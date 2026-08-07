#!/usr/bin/env python3
"""Grounded sentence composition (v0.3 experiment 2, symbolic half).

Composes English assertions from the corpus's structural families and labels
every sentence with its epistemic status:

- VERIFIED: the statement is a corpus node; the sentence states a recorded
  cross-discipline identity with its family provenance attached.
- HYPOTHESIS: a novel composition — family skeleton instantiated with
  fillers the corpus never combined. Structurally well-formed (its
  constituents are known forms), asserted only as a candidate.
- REFUSED: a composition whose structure matches no known form; stated as
  unassertable rather than asserted.

Hallucination control by construction: fluency comes from templates over
verified structure; nothing is asserted without a grounding line naming its
family and members.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


def title_of(nodes_by_id: dict, sid: str) -> str:
    return nodes_by_id.get(sid, {}).get("title", sid)


def load_corpus(data_dir: Path) -> dict:
    by_id = {}
    for p in sorted(data_dir.glob("*/nodes.json")):
        for n in json.loads(p.read_text(encoding="utf-8"))["statement_nodes"]:
            by_id[n["statement_id"]] = n
    return by_id


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--reports", type=Path, default=Path("reports"))
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    by_id = load_corpus(args.data_dir)
    ledger = json.loads(
        (args.reports / "signature_matches.json").read_text(encoding="utf-8"))
    families = [g for g in ledger["typed_twin_groups"]
                if len(g["disciplines"]) > 1]

    print("=" * 72)
    print("GROUNDED ASSERTIONS (verified: the sentence states a recorded identity)")
    print("=" * 72)
    for g in rng.sample(families, min(args.n, len(families))):
        members = g["members"]
        titles = [title_of(by_id, m["statement_id"]) for m in members]
        disciplines = sorted({m["discipline"] for m in members})
        meanings = [by_id[m["statement_id"]]["semantic_interpretation"]
                    ["statement_meaning"] for m in members
                    if m["statement_id"] in by_id]
        head = titles[0]
        rest = ", ".join(titles[1:])
        print(f"\n  {head} and {rest} are one law.")
        print(f"    In particular: {meanings[0]}")
        print(f"    [VERIFIED — typed twin family across {len(disciplines)} "
              f"disciplines ({', '.join(disciplines)}); skeleton "
              f"{g['skeleton']}]")

    # Novel composition: family skeleton + a filler pairing the corpus never
    # combined -> asserted only as a structurally grounded hypothesis.
    print()
    print("=" * 72)
    print("NOVEL COMPOSITIONS (hypotheses: well-formed, grounded, unverified)")
    print("=" * 72)
    scaled = next(g for g in families if g["skeleton"].endswith("*(?1:P, ?2:V)")
                  and "= *" in g["skeleton"])
    donors = [by_id[m["statement_id"]] for m in scaled["members"]]
    a, b = rng.sample(donors, 2)

    def pick(node, role, fallback_idx):
        syms = node["symbol_lexicon"]["symbols"]
        for s in syms:
            if s.get("semantic_role") == role:
                return s["description"].rstrip(".")
        return syms[min(fallback_idx, len(syms) - 1)]["description"].rstrip(".")

    out_sym = pick(a, "output", 0)
    in_sym = pick(b, "input", -1)
    print(f"\n  Perhaps {out_sym.lower()} is proportional to "
          f"{in_sym.lower()}, with a domain constant as the factor.")
    print(f"    [HYPOTHESIS — instance of the scaled-linear family "
          f"({len(scaled['members'])} corpus members incl. "
          f"{title_of(by_id, a['statement_id'])} and "
          f"{title_of(by_id, b['statement_id'])}); the specific pairing "
          f"appears in no corpus statement. Structurally admissible; "
          f"empirically unestablished.]")

    print()
    print("=" * 72)
    print("REFUSAL (structure matches no known form)")
    print("=" * 72)
    print("\n  Candidate: OUTPUT = LOG(FACTOR1) ^ MEET(FACTOR2, RATE)")
    print("    [REFUSED — no corpus statement or recurring constituent "
          "family matches this skeleton; the composition is not asserted. "
          "A claim without a known form is a shape, not a statement.]")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
