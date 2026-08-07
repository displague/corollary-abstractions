#!/usr/bin/env python3
"""Specialization matcher (v2): find general->specific edges between nodes.

The exact-skeleton matcher (match_signatures.py) groups only isomorphic
templates, which misses relationships the corpus keeps recording as near
misses: the ideal gas law is the quantity theory of money with an explicit
dimensional constant; Cobb-Douglas is a power-law rate law with one more
factor; circle circumference is the affine archetype with SHIFT = 0.

This tool matches a *general* node's canonical tree as a pattern against a
*specific* node's tree, where:

- a pattern slot may bind any subtree (consistently across repeats);
- in commutative ops (+, *), a slot may ABSORB several arguments (binding to
  their sub-product/sum) -- how QT's 2x2 covers the gas law's 2x3;
- a parameter-like pattern slot may bind the op's IDENTITY element (0 for +,
  1 for *) when arguments run out -- how affine covers circumference
  (SHIFT -> 0). Variable-like slots may not vanish: a law does not lose its
  variables, only its conventions.

Only matches that USE absorption or identity binding are reported: anything
matchable without them is an exact twin and already in the skeleton report.
Patterns must be relations with at least two operator/call nodes, else
near-trivial templates (X = A*B) would subsume half the corpus.
"""

from __future__ import annotations

import argparse
import json
from itertools import permutations
from pathlib import Path

from match_signatures import (
    COMMUTATIVE, ParsedNode, Parser, TemplateParseError, canonicalize,
    load_nodes, slot_classes, tokenize,
)

IDENTITY = {"+": ("num", 0.0), "*": ("num", 1.0)}


def op_count(t: tuple) -> int:
    if t[0] in {"slot", "num"}:
        return 0
    return 1 + sum(op_count(a) for a in t[2])


class MatchState:
    def __init__(self, slot_class: dict[str, str]):
        self.binds: dict[str, tuple] = {}
        self.slot_class = slot_class
        self.used_absorption = False
        self.used_identity = False


def match(pat: tuple, term: tuple, st: MatchState) -> bool:
    kind = pat[0]
    if kind == "slot":
        name = pat[1]
        if name in st.binds:
            return st.binds[name] == term
        st.binds[name] = term
        return True
    if kind == "num":
        return term[0] == "num" and term[1] == pat[1]
    if term[0] != kind or term[1] != pat[1]:
        return False
    if kind == "rel":
        (pl, pr), (tl, tr) = pat[2], term[2]
        saved = dict(st.binds), st.used_absorption, st.used_identity
        if match(pl, tl, st) and match(pr, tr, st):
            return True
        st.binds, st.used_absorption, st.used_identity = dict(saved[0]), saved[1], saved[2]
        if pat[1] == "=":
            if match(pl, tr, st) and match(pr, tl, st):
                return True
            st.binds, st.used_absorption, st.used_identity = saved[0], saved[1], saved[2]
        return False
    if kind == "op" and pat[1] in COMMUTATIVE:
        return match_commutative(pat[1], list(pat[2]), list(term[2]), st)
    if len(pat[2]) != len(term[2]):
        return False
    saved = dict(st.binds), st.used_absorption, st.used_identity
    for p, t in zip(pat[2], term[2]):
        if not match(p, t, st):
            st.binds, st.used_absorption, st.used_identity = dict(saved[0]), saved[1], saved[2]
            return False
    return True


def match_commutative(opname: str, pats: list[tuple], terms: list[tuple],
                      st: MatchState) -> bool:
    """Assign term args to pattern args. Non-slot pattern args take exactly
    one term arg; slot args take >=1 (absorbing extras as a sub-op) or, for
    parameter-like slots, the identity element (taking none)."""
    if not pats:
        return not terms
    pat = pats[0]
    saved = dict(st.binds), st.used_absorption, st.used_identity

    def restore():
        st.binds, st.used_absorption, st.used_identity = dict(saved[0]), saved[1], saved[2]

    if pat[0] != "slot":
        for i, t in enumerate(terms):
            if match(pat, t, st):
                if match_commutative(opname, pats[1:], terms[:i] + terms[i + 1:], st):
                    return True
            restore()
        return False

    name = pat[1]
    # identity binding for parameter-like slots
    if st.slot_class.get(name) == "P":
        ident = IDENTITY[opname]
        if st.binds.get(name, ident) == ident:
            prev = name in st.binds
            st.binds[name] = ident
            was_ident = st.used_identity
            st.used_identity = True
            if match_commutative(opname, pats[1:], terms, st):
                return True
            if not prev:
                st.binds.pop(name, None)
            st.used_identity = was_ident
    # bind to each possible non-empty subset (subsets beyond singletons only
    # explored when the remaining pattern can still be satisfied)
    n = len(terms)
    remaining_needed = sum(1 for p in pats[1:] if p[0] != "slot"
                           or st.slot_class.get(p[1]) != "P")
    max_take = n - remaining_needed if n - remaining_needed >= 1 else 0
    for size in range(1, max_take + 1):
        for combo in _combinations(range(n), size):
            taken = [terms[i] for i in combo]
            bound = taken[0] if size == 1 else canonicalize((
                "op", opname, tuple(taken)))
            if name in st.binds:
                if st.binds[name] != bound:
                    continue
                prev = True
            else:
                st.binds[name] = bound
                prev = False
            was_abs = st.used_absorption
            if size > 1:
                st.used_absorption = True
            rest = [terms[i] for i in range(n) if i not in combo]
            if match_commutative(opname, pats[1:], rest, st):
                return True
            if not prev:
                st.binds.pop(name, None)
            st.used_absorption = was_abs
    return False


def _combinations(idx, size):
    from itertools import combinations
    return combinations(idx, size)


def find_specializations(nodes: list[ParsedNode], trees: dict[str, tuple],
                         classes: dict[str, dict[str, str]]) -> list[dict]:
    edges = []
    for gen in nodes:
        gtree = trees[gen.statement_id]
        if gtree[0] != "rel" or op_count(gtree) < 2:
            continue
        for spec in nodes:
            if spec.statement_id == gen.statement_id:
                continue
            if gen.shape == spec.shape:
                continue  # exact twins already reported
            st = MatchState(classes[gen.statement_id])
            if match(gtree, trees[spec.statement_id], st) and (
                    st.used_absorption or st.used_identity):
                edges.append({
                    "general": gen.statement_id,
                    "specific": spec.statement_id,
                    "general_template": gen.template,
                    "specific_template": spec.template,
                    "via": ("absorption" if st.used_absorption else "")
                           + ("+" if st.used_absorption and st.used_identity else "")
                           + ("identity" if st.used_identity else ""),
                    "bindings": {k: render(v) for k, v in sorted(st.binds.items())},
                })
    return edges


def render(t: tuple) -> str:
    if t[0] == "slot":
        return t[1]
    if t[0] == "num":
        return f"{t[1]:g}"
    if t[0] == "rel":
        return f"{render(t[2][0])} {t[1]} {render(t[2][1])}"
    inner = ", ".join(render(a) for a in t[2])
    return f"{t[1]}({inner})"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--write-report", type=Path, default=None)
    args = ap.parse_args()

    nodes, problems = load_nodes(args.data_dir)
    trees: dict[str, tuple] = {}
    classes: dict[str, dict[str, str]] = {}
    kept: list[ParsedNode] = []
    for corpus_path in sorted(args.data_dir.glob("*/nodes.json")):
        corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
        for nj in corpus.get("statement_nodes", []):
            sid = nj.get("statement_id")
            sig = nj.get("structural_signature", {})
            tmpl = sig.get("anonymized_template", "")
            try:
                trees[sid] = canonicalize(Parser(tokenize(tmpl)).parse())
            except TemplateParseError:
                continue
            classes[sid] = slot_classes(nj)
    kept = [n for n in nodes if n.statement_id in trees]

    edges = find_specializations(kept, trees, classes)
    # Tightness: how much structure the bindings had to swallow. Small =
    # near-exact relationship; large = loose structural analogy.
    for e in edges:
        e["looseness"] = sum(max(0, b.count("(")) for b in e["bindings"].values())
    edges.sort(key=lambda e: (e["looseness"], e["general"]))
    cross = [e for e in edges
             if e["general"].split(".")[0] != e["specific"].split(".")[0]]
    print(f"Found {len(edges)} specialization edges "
          f"({len(cross)} cross-discipline) among {len(kept)} nodes.\n")
    shown = edges[:40]
    for e in shown:
        tag = " [CROSS-DISCIPLINE]" if e in cross else ""
        print(f"  {e['general']}  >=  {e['specific']}  via {e['via']} "
              f"(looseness {e['looseness']}){tag}")
        print(f"    general : {e['general_template']}")
        print(f"    specific: {e['specific_template']}")
        binds = ", ".join(f"{k}->{v}" for k, v in e["bindings"].items())
        print(f"    bindings: {binds}\n")
    if len(edges) > len(shown):
        print(f"  ... {len(edges) - len(shown)} looser edges omitted from "
              f"stdout (all are in the JSON report).")

    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(
            json.dumps({"specialization_edges": edges}, indent=2,
                       ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Report written to {args.write_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
