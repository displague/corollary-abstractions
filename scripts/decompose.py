#!/usr/bin/env python3
"""Derivational composition: read each statement as a construct of known forms.

The matchers relate WHOLE statements; this tool walks every statement's
canonical tree and asks, for each constituent subterm, "which known form is
this an instance of?" — where the form inventory is (a) the expression-side
skeletons of every corpus statement and (b) recurring subterm families
across statements. Output: per-statement decompositions ("the SSM update's
right side is two scaled-linear constituents joined by +"), i.e. statements
as constructs of other forms — commitment #1 of docs/DESIGN-concept-tokens.md
made mechanical, and the substrate for composing new mathematically grounded
statements from named parts.

Constituents are matched at the typed level (parameter/variable categories
respected). Trivial subterms (single leaves) are excluded; a constituent
reports every statement whose expression side shares its skeleton, plus how
many corpus statements contain it as a subterm.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from match_signatures import (
    Parser, TemplateParseError, canonicalize, load_nodes, skeleton,
    slot_classes, tokenize,
)


def subterms(t: tuple, path: tuple = ()):
    """Yield (path, subtree) for every non-leaf subtree, including relation
    sides but not the relation itself."""
    if t[0] == "rel":
        for i, side in enumerate(t[2]):
            yield from subterms(side, path + (i,))
        return
    if t[0] in {"op", "call"}:
        yield path, t
        for i, a in enumerate(t[2]):
            yield from subterms(a, path + (i,))


def tree_size(t: tuple) -> int:
    if t[0] in {"slot", "num"}:
        return 1
    if t[0] == "rel":
        return sum(tree_size(a) for a in t[2])
    return 1 + sum(tree_size(a) for a in t[2])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--min-family", type=int, default=2,
                    help="a subterm family counts if it recurs in >= this many statements")
    ap.add_argument("--write-report", type=Path, default=None)
    args = ap.parse_args()

    nodes, _ = load_nodes(args.data_dir)

    # Rebuild trees + slot classes (load_nodes keeps only skeleton strings).
    trees: dict[str, tuple] = {}
    classes: dict[str, dict[str, str]] = {}
    for corpus_path in sorted(args.data_dir.glob("*/nodes.json")):
        corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
        for nj in corpus.get("statement_nodes", []):
            sid = nj.get("statement_id")
            tmpl = nj.get("structural_signature", {}).get("anonymized_template", "")
            try:
                trees[sid] = canonicalize(Parser(tokenize(tmpl)).parse())
            except TemplateParseError:
                continue
            classes[sid] = slot_classes(nj)

    # Form inventory 1: expression-side skeletons of whole statements.
    side_forms: dict[str, list[str]] = defaultdict(list)
    for n in nodes:
        t = trees.get(n.statement_id)
        if t is None:
            continue
        sides = t[2] if t[0] == "rel" else (t,)
        for side in sides:
            if side[0] in {"op", "call"}:
                side_forms[skeleton(side, classes[n.statement_id])].append(
                    n.statement_id)

    # Form inventory 2: recurring subterm families across statements.
    subterm_hosts: dict[str, set] = defaultdict(set)
    for n in nodes:
        t = trees.get(n.statement_id)
        if t is None:
            continue
        for _, sub in subterms(t):
            if tree_size(sub) < 2:
                continue
            subterm_hosts[skeleton(sub, classes[n.statement_id])].add(
                n.statement_id)

    decompositions = []
    for n in nodes:
        t = trees.get(n.statement_id)
        if t is None:
            continue
        cls = classes[n.statement_id]
        constituents = []
        n_considered = 0
        n_grounded = 0
        for path, sub in subterms(t):
            if not path:  # the whole side; skip self-description
                continue
            skel = skeleton(sub, cls)
            named = sorted(set(side_forms.get(skel, [])) - {n.statement_id})
            hosts = subterm_hosts.get(skel, set())
            n_considered += 1
            grounded = bool(named) or len(hosts) >= args.min_family
            if grounded:
                n_grounded += 1
            if not grounded:
                continue
            constituents.append({
                "path": list(path),
                "skeleton": skel,
                "instance_of_statements": named[:8],
                "recurs_in_n_statements": len(hosts),
            })
        # Groundedness: the epistemic-ladder grade for "disorder" — fraction
        # of non-trivial constituents matching known forms. 1.0 = every
        # piece is a named/recurring form; low values shade toward gibberish.
        score = round(n_grounded / n_considered, 3) if n_considered else 1.0
        if constituents or n_considered:
            decompositions.append({
                "statement_id": n.statement_id,
                "template": n.template,
                "groundedness": score,
                "constituents": constituents,
            })

    n_with = sum(1 for d in decompositions if d["constituents"])
    n_named = sum(1 for d in decompositions
                  if any(c["instance_of_statements"] for c in d["constituents"]))
    scores = [d["groundedness"] for d in decompositions]
    mean_score = sum(scores) / len(scores) if scores else 0.0
    lowest = sorted(decompositions, key=lambda d: d["groundedness"])[:3]
    print(f"{n_with} of {len(nodes)} statements decompose into known forms; "
          f"{n_named} contain a constituent that IS another statement's "
          f"expression side.")
    print("Corpus mean groundedness: "
          f"{mean_score:.3f}; least grounded: "
          + ", ".join(f"{d['statement_id']} ({d['groundedness']})"
                      for d in lowest) + "\n")

    # Show the ones whose constituents are named statements — the
    # 'built from lemmas' readout.
    shown = 0
    for d in decompositions:
        named_cs = [c for c in d["constituents"] if c["instance_of_statements"]]
        if not named_cs or shown >= 20:
            continue
        shown += 1
        print(f"  {d['statement_id']}")
        print(f"    template: {d['template']}")
        for c in named_cs:
            others = ", ".join(c["instance_of_statements"][:3])
            more = ("..." if len(c["instance_of_statements"]) > 3 else "")
            print(f"    constituent at {c['path']}: {c['skeleton']}")
            print(f"      = expression side of: {others}{more} "
                  f"(recurs in {c['recurs_in_n_statements']} statements)")
        print()

    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(json.dumps(
            {"decompositions": decompositions}, indent=2, ensure_ascii=False)
            + "\n", encoding="utf-8")
        print(f"Report written to {args.write_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
