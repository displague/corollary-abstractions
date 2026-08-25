#!/usr/bin/env python3
"""Write `experiments/conformance_prereg.json` — E7's freeze and E0's adjudication.

`docs/DESIGN-statements-that-run.md` E7: *"Recorded in the preregistration
commit, BEFORE `conform.py` is written: the digests of
`scripts/match_signatures.py`, `scripts/evaluate.py`, the domain schema, and
the sampler. If making a conformance verdict come out right requires editing
the parser, the arithmetic, or the schema, the independence claim is void and
the change needs its own review naming the reason."*

C-E4 (the tautology probe) revalidates these four at run time, the way
`measure_throughput.revalidate_rendering_digests` does. This writer is what
freezes them, and it refuses to write if `scripts/conform.py` already exists
— a freeze recorded after the thing it constrains is not a freeze, and the
transliteration lane's pending-row rule is the precedent.

It also records the **E0-series adjudication** the lane owes in writing: which
prerequisites ROADMAP-v0.20 §4 discharged, with the evidence, and which
remain this slice's to measure. Adjudicating them in prose and then measuring
them again would be the re-doing the brief forbids.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

ARTIFACT = "experiments/conformance_prereg.json"
COMPILER = "scripts/conform.py"

#: E7's four. The sampler is a separate module for exactly this reason: a
#: digest cannot be frozen before the file it names exists.
FROZEN = (
    ("parser", "scripts/match_signatures.py"),
    ("evaluator", "scripts/evaluate.py"),
    ("domain_schema", "data/domains/domain_schema.json"),
    ("sampler", "scripts/conform_sampler.py"),
    ("census", "scripts/conform_census.py"),
    ("schema_loader", "scripts/conform_domain.py"),
)


def sha256_lf(path: Path) -> str:
    return hashlib.sha256(
        Path(path).read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def build() -> dict:
    import conform_census as census
    import conform_domain

    schema = conform_domain.load()
    rows = list(census.walk(output_roles=schema.output_roles))

    buckets: dict[str, int] = {}
    for row in rows:
        buckets[row.bucket] = buckets.get(row.bucket, 0) + 1

    guarded = [r for r in rows if r.bucket == "guarded"]
    unguarded = [r for r in rows if r.bucket == "unguarded"]
    equality = [r for r in guarded if r.guard.has_equality]
    inequality = [r for r in guarded if not r.guard.has_equality]
    box_only = [r for r in inequality if r.guard.box_only]
    coupled = [r for r in inequality if not r.guard.box_only]
    ground = [r for r in rows if r.ground]

    typed: dict[str, int] = {}
    for row in rows:
        if row.typed_refusal:
            typed[row.typed_refusal] = typed.get(row.typed_refusal, 0) + 1

    shape: dict[str, int] = {}
    for row in rows:
        if row.shape_exclusion:
            shape[row.shape_exclusion] = shape.get(row.shape_exclusion, 0) + 1

    return {
        "prereg_id": "conformance.prereg.v1",
        "registered": "2026-08-25",
        "design": "docs/DESIGN-statements-that-run.md",
        "roadmap": "docs/ROADMAP-v0.20.md §1",
        "writer": "scripts/write_conformance_prereg.py",
        "commit_at_freeze": _git("rev-parse", "HEAD"),
        "digest_algorithm": "sha256 over the file's bytes with CRLF normalised to LF",
        "what_this_records": [
            "E7's freeze: the digests of the parser, the evaluator, the domain schema and the sampler, recorded BEFORE scripts/conform.py exists.",
            "The E0-series adjudication this lane owes in writing: which prerequisites ROADMAP-v0.20 §4 discharged and with what evidence, and which remain this slice's to measure.",
            "The census as measured on this tree. The design's own figures are the reviewer's preview; these are the run's, and where they differ the difference is reconciled rather than rounded.",
        ],
        "frozen": [
            {
                "role": role,
                "path": path,
                "sha256_lf": sha256_lf(REPO / path),
                "recorded": "2026-08-25",
            }
            for role, path in FROZEN
        ],
        "e7_voiding_sentence": (
            "If making a conformance verdict come out right requires editing "
            "the parser, the arithmetic, or the schema, the independence claim "
            "is void and the change needs its own review naming the reason."
        ),
        "e0_series_adjudication": {
            "how_to_read_this": (
                "Four E0-series clauses are construction prerequisites rather "
                "than frozen floors, and two of them are discharged by "
                "ROADMAP-v0.20 §4's batched witness item rather than by this "
                "slice. Adjudicated here, in writing, before the slice — "
                "re-doing a discharged prerequisite would be work the batch "
                "already paid for."
            ),
            "E0": {
                "clause": "exact numerals",
                "owner": "ROADMAP-v0.20 §4b (batched witness item)",
                "status": "DISCHARGED",
                "evidence": [
                    "scripts/match_signatures.exact_literal stores an integer surface as int; verified present on this tree.",
                    "experiments/exact_literals_served_diff.json: 0 answer lines moved of 14,830, 3 evaluate-route renderings moved, 0 skeletons moved of 25,554 terms.",
                    "The three named nodes: leanworkbook.ground.lean_workbook_37421 and lean_workbook_plus_68304 now print exact digits; goedelpset.skel.goedel_pset_789185 was found by that lane's served diff.",
                ],
                "what_remains_true_and_is_carried_here": (
                    "leanworkbook.skel.lean_workbook_50397's `inf` is frozen "
                    "into its committed anonymized_template by the seed script "
                    "and its canonical_ascii does not tokenize, so no parser "
                    "change reaches it. It is BACKLOG-filed as a seed "
                    "regeneration and lands in this lane's register rather "
                    "than being silently absent."
                ),
                "this_lanes_obligation": (
                    "No conformance record prints a `left` or `right` value "
                    "where the exact path did not reach; such a point is "
                    "`evaluation_error`, the third outcome, never a silent "
                    "rounding."
                ),
            },
            "E0e": {
                "clause": "the resource bound, refusing by name",
                "owner": "ROADMAP-v0.20 §4c (batched witness item)",
                "status": "DISCHARGED",
                "evidence": [
                    "evaluate.MAX_RESULT_DIGITS = 4300 and evaluate.ResourceBound exist on this tree.",
                    "The bound sits at the result-formatting boundary after the review found a per-node bound escapable by `(10^4000)*(10^4000)`.",
                    "experiments/exponent_bound.json: 3 of 6 cases crashed while printing before, 0 after.",
                ],
                "this_lanes_obligation": (
                    "The refusal VOCABULARY is this design's: a bound the "
                    "compiler hits emits REFUSED with "
                    "`evaluation_budget_exceeded`, never a truncated answer. "
                    "The domain schema declares it as a branch cut so the "
                    "mapping from ResourceBound to the register construct is "
                    "recorded rather than improvised in the compiler."
                ),
            },
            "E0b": {
                "clause": "the guard-recovery table, floor >= 5,000 compiling",
                "owner": "this slice",
                "status": "MEASURED — see census below",
            },
            "E0c": {
                "clause": "the domain schema, frozen before any verdict",
                "owner": "this slice",
                "status": "FROZEN by this commit",
            },
            "E0d": {
                "clause": "the samplable denominator",
                "owner": "this slice",
                "status": "MEASURED — see census below",
            },
            "E0f": {
                "clause": "the admission pilot over the coupled guards",
                "owner": "this slice",
                "status": "PENDING — runs after conform.py, freezes E2a by dated amendment",
            },
        },
        "census": {
            "measured_on": _git("rev-parse", "HEAD"),
            "statement_nodes": len(rows),
            "buckets": dict(sorted(buckets.items())),
            "shape_exclusions": dict(sorted(shape.items())),
            "typed_refusals": dict(sorted(typed.items())),
            "e0b_guard_recovery_table": {
                "ground": len(ground),
                "guarded_and_recoverable": len(guarded),
                "guarded_but_unevaluable": buckets.get(
                    "refused_guard_unevaluable", 0),
                "unguarded": len(unguarded),
                "total_compiling": len(ground) + len(guarded) + len(unguarded),
                "floor": 5000,
                "floor_met": (len(ground) + len(guarded) + len(unguarded)) >= 5000,
                "floor_is_a_disclosed_formality": (
                    "The design labels it one: the preview sat 39% above the "
                    "floor. It is kept because a floor the run could in "
                    "principle miss is worth more than no floor."
                ),
            },
            "e0d_samplable_denominator": {
                "equality_guarded_measure_zero": len(equality),
                "inequality_only": len(inequality),
                "of_which_box_constraints_only": len(box_only),
                "of_which_couple_variables": len(coupled),
                "unguarded": len(unguarded),
                "samplable": len(unguarded) + len(inequality),
                "ground_is_not_in_it": (
                    "The 297 ground statements are decided by E1 and carry no "
                    "free variable to sample; adding them would inflate the "
                    "sampling denominator with statements no sampler touches."
                ),
            },
            "reconciliation_with_the_designs_preview": {
                "why_the_numbers_differ": (
                    "The design's preview predates its own Correction 2, whose "
                    "typing rule this census applies BEFORE reading the guard. "
                    "Statements refused for a typed slot therefore never reach "
                    "the guard partition, which is where the difference comes "
                    "from. The shape walk — 12,777 / 4,191 / 8,586 / 8,476 / "
                    "297 / 8,179 — reproduces the design exactly."
                ),
                "design_preview": {
                    "guarded": 6490, "unguarded": 1689, "equality_guarded": 3476,
                    "inequality_only": 2781, "box_only": 2061, "coupled": 720,
                    "samplable": 4470, "total_compiling": 8243,
                },
            },
            "two_corrections_this_census_made_to_itself": [
                {
                    "correction": "slot ids are anonymized; the ascii tree carries surface identifiers",
                    "found": "while writing the census",
                    "effect_before_fix": "zero authored slots typed — every declaration in the corpus unread, which is the sampler Correction 2 was written to prevent",
                    "fix": "positional alignment between the ascii tree and the template's consequent, refusing when the shapes diverge rather than typing by proximity",
                },
                {
                    "correction": "alignment must target the template's CONSEQUENT, not the whole template",
                    "found": "measured: 6,535 alignment failures, 6,525 of them lean_workbook",
                    "effect_before_fix": "an IMPLIES-topped template cannot align with a bare conclusion, so the largest corpus went untyped",
                    "fix": "align against template_conclusion(); failures fell to 128, all of which now refuse rather than defaulting to sampled",
                },
            ],
        },
        "non_claims": [
            "This artifact computes no verdict and samples no point. It freezes digests and publishes a census.",
            "The census is a classification, not a result. Which statements CONFORM is E1/E2's business and is not knowable from this file.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=ARTIFACT)
    parser.add_argument(
        "--allow-compiler-present",
        action="store_true",
        help="write even though scripts/conform.py exists (re-freeze only)",
    )
    args = parser.parse_args(argv)

    if (REPO / COMPILER).exists() and not args.allow_compiler_present:
        print(
            f"REFUSING to write: {COMPILER} already exists. E7 freezes these "
            f"digests BEFORE the compiler is written, and a freeze recorded "
            f"after the thing it constrains is not a freeze.",
            file=sys.stderr,
        )
        return 2

    record = build()
    out = REPO / args.out
    out.write_text(
        json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    census = record["census"]
    print(f"frozen: {len(record['frozen'])} artifacts")
    for row in record["frozen"]:
        print(f"   {row['role']:16s} {row['sha256_lf'][:16]}  {row['path']}")
    print()
    print(f"statements      : {census['statement_nodes']}")
    for name, count in census["buckets"].items():
        print(f"   {name:36s} {count}")
    table = census["e0b_guard_recovery_table"]
    print(f"E0b compiling   : {table['total_compiling']} "
          f"(floor {table['floor']}, met={table['floor_met']})")
    denom = census["e0d_samplable_denominator"]
    print(f"E0d samplable   : {denom['samplable']} "
          f"= {denom['unguarded']} unguarded + {denom['inequality_only']} inequality-only")
    print(f"   coupled guards (E0f's pilot set): {denom['of_which_couple_variables']}")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
