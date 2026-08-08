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
- a parameter-like pattern slot may bind the op's identity element (0 for +,
  1 for *) when arguments run out -- how affine covers circumference
  (SHIFT -> 0). Variable-like slots may not vanish there: a law does not
  lose its variables, only its conventions;
- a declared-commutative CALL head (`MEET`, `JOIN`, `TOUCHES`) may have its
  two arguments matched in either order;
- a call head with a declared identity may COLLAPSE: `HEAD(a, e)` is `a`, so
  a pattern's slot argument may bind the identity and the call reduces to its
  other argument -- how iterated affixation covers plain affixation
  (SUFFIX -> EMPTY) and how absorption covers idempotence (the join operand
  goes to BOT). Here a variable-like slot MAY vanish, because the element it
  binds is one the corpus declares as a `constant` slot rather than a number
  the matcher invented.

Identities and commutativity both come from `match_signatures.HEAD_ALGEBRA`;
nothing about which heads have which algebra is decided in this file.

Only matches beyond pure slot-to-slot renaming are reported (a renaming is
an exact twin, already in the skeleton report): absorption, identity
binding, or a slot binding structure (a compound subtree or a literal).
Patterns must be rel- or call-rooted with at least two operator/call nodes,
else near-trivial templates (X = A*B) would subsume half the corpus.
"""

from __future__ import annotations

import argparse
import json
from itertools import permutations
from pathlib import Path

from match_signatures import (
    COMMUTATIVE, COMMUTATIVE_CALL_HEADS, ParsedNode, Parser,
    TemplateParseError, canonicalize, identity_terms, load_nodes, slot_classes,
    tokenize,
)


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
        self.used_compound = False  # a slot bound a non-leaf or a literal
        self.head_collapses = 0  # call nodes eliminated via a declared identity
        # Head-identity collapse is a fallback, enabled only on a second pass
        # (see find_specializations): a match that needs no algebra at all is
        # always the better reading, and the first-success-wins search would
        # otherwise let a collapse pre-empt one. Measured on
        # `de9im_disjoint >= next_distributes_over_meet`, which the one-pass
        # version replaced with a degenerate `REGB -> TRUTH` reading.
        self.allow_head_identity = True


def _save(st: MatchState) -> tuple:
    # used_compound is part of the checkpoint: a branch that binds structure
    # and then fails must not leave the flag set, or the edge filter reports
    # "compound" for a match that never used it.
    return (dict(st.binds), st.used_absorption, st.used_identity,
            st.used_compound, st.head_collapses)


def _restore(st: MatchState, saved: tuple) -> None:
    st.binds = dict(saved[0])
    (st.used_absorption, st.used_identity, st.used_compound,
     st.head_collapses) = saved[1:]


def match(pat: tuple, term: tuple, st: MatchState) -> bool:
    saved = _save(st)
    if match_direct(pat, term, st):
        return True
    _restore(st, saved)
    # A declared identity lets a call collapse: for a head with a two-sided
    # identity e, HEAD(a, e) IS a, so a pattern whose vanishing argument is a
    # slot may bind that slot to e and match its other argument against the
    # whole term. This is the per-head generalization of the arithmetic
    # "argument runs out, bind 0 or 1" rule below, and it is what makes
    # CONCAT's zero morph usable (docs/BACKLOG.md, per-head identities).
    if st.allow_head_identity and pat[0] == "call" and identity_terms(pat[1]):
        if match_via_head_identity(pat, term, st):
            return True
        _restore(st, saved)
    return False


def match_direct(pat: tuple, term: tuple, st: MatchState) -> bool:
    kind = pat[0]
    if kind == "slot":
        name = pat[1]
        if name in st.binds:
            return st.binds[name] == term
        st.binds[name] = term
        if term[0] != "slot":
            st.used_compound = True  # binding structure, not renaming
        return True
    if kind == "num":
        return term[0] == "num" and term[1] == pat[1]
    if term[0] != kind or term[1] != pat[1]:
        return False
    if kind == "rel":
        (pl, pr), (tl, tr) = pat[2], term[2]
        saved = _save(st)
        if match(pl, tl, st) and match(pr, tr, st):
            return True
        _restore(st, saved)
        if pat[1] == "=":
            if match(pl, tr, st) and match(pr, tl, st):
                return True
            _restore(st, saved)
        return False
    if kind == "op" and pat[1] in COMMUTATIVE:
        return match_commutative(pat[1], list(pat[2]), list(term[2]), st)
    if len(pat[2]) != len(term[2]):
        return False
    saved = _save(st)
    if kind == "call" and pat[1] in COMMUTATIVE_CALL_HEADS and len(pat[2]) == 2:
        # Declared-commutative call head: try both argument orders. Both trees
        # are already canonically sorted, but the sort key erases slot
        # identity, so a pattern and a term can still disagree on order.
        for order in ((0, 1), (1, 0)):
            if (match(pat[2][0], term[2][order[0]], st)
                    and match(pat[2][1], term[2][order[1]], st)):
                return True
            _restore(st, saved)
        return False
    for p, t in zip(pat[2], term[2]):
        if not match(p, t, st):
            _restore(st, saved)
            return False
    return True


def match_via_head_identity(pat: tuple, term: tuple, st: MatchState) -> bool:
    """Collapse `HEAD(keep, vanish)` to `keep` by binding `vanish` to HEAD's
    declared identity element.

    Unlike the arithmetic identity rule in `match_commutative`, this permits a
    VARIABLE-like slot to vanish. The justification is in the corpus: a zero
    morph *is* a morph (`morphology.wordformation.zero_morpheme_identity`,
    `CONCAT(STEM, EMPTY) = STEM`), and the element it binds is a slot the
    corpus declares `constant`, not a value invented by the matcher. The old
    blanket rule ("a law does not lose its variables") is right for `+` and
    `*`, where the identity is a bare number, and wrong here.
    """
    args = pat[2]
    if len(args) != 2:
        return False
    idents = identity_terms(pat[1])
    for i in (1, 0):  # right identity first: the corpora write it that way
        vanish, keep = args[i], args[1 - i]
        if vanish[0] != "slot":
            continue
        name = vanish[1]
        for ident in idents:
            if st.binds.get(name, ident) != ident:
                continue
            saved = _save(st)
            st.binds[name] = ident
            st.used_identity = True
            st.head_collapses += 1
            if match(keep, term, st):
                return True
            _restore(st, saved)
    return False


def match_commutative(opname: str, pats: list[tuple], terms: list[tuple],
                      st: MatchState) -> bool:
    """Assign term args to pattern args. Non-slot pattern args take exactly
    one term arg; slot args take >=1 (absorbing extras as a sub-op) or, for
    parameter-like slots, the identity element (taking none)."""
    if not pats:
        return not terms
    pat = pats[0]
    saved = _save(st)

    def restore():
        _restore(st, saved)

    if pat[0] != "slot":
        for i, t in enumerate(terms):
            if match(pat, t, st):
                if match_commutative(opname, pats[1:], terms[:i] + terms[i + 1:], st):
                    return True
            restore()
        return False

    name = pat[1]
    # Identity binding for parameter-like slots. The identity now comes from
    # the declared HEAD_ALGEBRA table rather than a local dict; for `+` and
    # `*` it is a bare number, so the parameter-only restriction stays (see
    # match_via_head_identity for why declared constant slots are different).
    if st.slot_class.get(name) == "P":
        for ident in identity_terms(opname):
            if st.binds.get(name, ident) != ident:
                continue
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
        # rel-rooted equations AND call-rooted statements (inference rules,
        # relational predicates) may serve as patterns; the old rel-only
        # guard excluded all 16 inference-rule nodes (probed, BACKLOG).
        if gtree[0] not in {"rel", "call", "op"} or op_count(gtree) < 2:
            continue
        for spec in nodes:
            if spec.statement_id == gen.statement_id:
                continue
            if gen.shape == spec.shape:
                continue  # exact twins already reported
            # Pass 1 uses no declared head identity; pass 2 allows it. A
            # reading that needs no algebra is always preferred.
            st = MatchState(classes[gen.statement_id])
            st.allow_head_identity = False
            if not match(gtree, trees[spec.statement_id], st):
                st = MatchState(classes[gen.statement_id])
                if not match(gtree, trees[spec.statement_id], st):
                    continue
            # informative = anything beyond pure slot-to-slot renaming
            # (renamings are exact twins, already in the skeleton report);
            # the old absorption/identity-only filter provably suppressed
            # the plainest specializations (5 probed instances in BACKLOG).
            # Head-identity collapse removes a call node from the pattern, so
            # the non-triviality bar (`op_count >= 2`, so that templates like
            # `X = A*B` cannot subsume half the corpus) has to be re-checked
            # against the pattern as *used*, not as written. Without this,
            # `MEET(REGA, REGB) = EMPTYSET` collapses to `REGA = EMPTYSET`
            # and matches every two-slot equation in the graph: measured, it
            # was 507 extra edges, 500 of them from three such templates.
            if (op_count(gtree) - st.head_collapses >= 2
                    and (st.used_absorption or st.used_identity
                         or st.used_compound)):
                edges.append({
                    "general": gen.statement_id,
                    "specific": spec.statement_id,
                    "general_template": gen.template,
                    "specific_template": spec.template,
                    "via": "+".join(v for v, on in [
                        ("absorption", st.used_absorption),
                        ("identity", st.used_identity),
                        ("compound", st.used_compound)] if on),
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
