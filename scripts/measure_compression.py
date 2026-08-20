#!/usr/bin/env python3
"""Milestone-2 measurement on the real corpus: what does the concept
vocabulary buy over character and parse-token encodings?

Encodings of each node's anonymized template (the corpus's canonical
structural surface, parseable by construction):

- char: characters of the template string (subword-free lower bound for a
  text tokenizer)
- struct: canonical parse-tree tokens (operators, heads, slots, brackets)
- concept: one token naming the node's FAMILY skeleton + one token per slot
  filler. Decoding needs the skeleton vocabulary (the extrinsic structure
  lexicon) -- exactly the design doc's bet, measured.

Also reports skeleton-vocabulary statistics: reuse is where compression
scales, because every node sharing a skeleton amortizes one vocab entry.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from match_signatures import load_nodes
from report_provenance import corpus_provenance


def struct_token_count(shape: str) -> int:
    # shape strings render tokens separated by spaces/commas/parens; count
    # atoms rather than characters
    out = 0
    token = ""
    for ch in shape:
        if ch in "(),⟨⟩ ":
            if token:
                out += 1
                token = ""
            if ch in "()⟨⟩":
                out += 1
        else:
            token += ch
    return out + (1 if token else 0)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--write-report", type=Path, default=None)
    args = ap.parse_args()

    nodes, problems = load_nodes(args.data_dir)
    fam_counts = Counter(n.family for n in nodes)

    rows = []
    for n in nodes:
        n_slots = len(set(
            tok for tok in n.family.replace("(", " ").replace(")", " ")
            .replace("⟨", " ").replace("⟩", " ").replace(",", " ").split()
            if tok.startswith("?")))
        rows.append({
            "statement_id": n.statement_id,
            "char_tokens": len(n.template),
            "struct_tokens": struct_token_count(n.shape),
            "concept_tokens": 1 + n_slots,
            "family_reuse": fam_counts[n.family],
        })

    def mean(key: str) -> float:
        return sum(r[key] for r in rows) / len(rows)

    n_skeletons = len(fam_counts)
    reused = sum(1 for c in fam_counts.values() if c > 1)
    print(f"Nodes analyzed: {len(rows)} (parse problems skipped: {len(problems)})")
    print(f"\nMean tokens per statement:")
    print(f"  char    {mean('char_tokens'):6.1f}")
    print(f"  struct  {mean('struct_tokens'):6.1f}  "
          f"({mean('char_tokens')/mean('struct_tokens'):.2f}x vs char)")
    print(f"  concept {mean('concept_tokens'):6.1f}  "
          f"({mean('char_tokens')/mean('concept_tokens'):.2f}x vs char, "
          f"{mean('struct_tokens')/mean('concept_tokens'):.2f}x vs struct)")
    print(f"\nSkeleton vocabulary: {n_skeletons} family skeletons for "
          f"{len(rows)} nodes ({len(rows)/n_skeletons:.2f} nodes/skeleton); "
          f"{reused} skeletons reused by >1 node")
    top = fam_counts.most_common(5)
    print("Most-reused skeletons:")
    for skel, c in top:
        print(f"  {c} nodes: {skel}")

    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        # Provenance leads the file (see match_signatures.main): additive
        # over the committed bytes, and read before the payload.
        args.write_report.write_text(json.dumps({
            "provenance": corpus_provenance(Path(__file__), args.data_dir),
            "nodes": rows,
            "mean_char": mean("char_tokens"),
            "mean_struct": mean("struct_tokens"),
            "mean_concept": mean("concept_tokens"),
            "n_family_skeletons": n_skeletons,
            "skeletons_reused": reused,
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"\nReport written to {args.write_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
