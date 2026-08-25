#!/usr/bin/env python3
"""Freeze `experiments/conformance_register.json` — E0c, before any verdict.

`docs/DESIGN-statements-that-run.md` §3.3: *"So the register is not an
appendix; it is where most of the territory lands this cycle."* One row per
blocking construct, frozen and digested **before the first verdict**, on
v0.19's register schema.

**Two objects, two questions, and the artifact says which is which.** E3's
arithmetic partitions STATEMENTS — every statement lands in exactly one
bucket. The register is indexed by CONSTRUCT, and one statement can carry
two blocking constructs. So the register's `blocking_count` fields are never
summed and never reconciled against E3's table; the first draft of the design
implied they could be, and that would have double-counted.

**Why domain coverage is applied here and not in the census.** The census
(`conform_census.py`) is frozen by E7 and classifies shape and typing — what
the statement IS. Whether a domain row covers it is the schema's business,
and applying it here keeps the frozen classifier from needing to know about
a table that can grow by review. `domain_absent` is therefore computed at
this step, over statements the census found otherwise testable.

**The register ships its zeros.** `operator_pm` is real — the parser emits a
`pm` node the evaluator has no rule for — and measures zero on this tree. It
ships with `blocking_count: 0` rather than being quietly omitted, because a
register that lists only its populated rows is a register that cannot show
you a zero.
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

ARTIFACT = "experiments/conformance_register.json"
COMPILER = "scripts/conform.py"


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


#: The closed construct vocabulary. The first twelve are the design's own
#: (§3.3); the rest carry a dated reason because this lane measured them and
#: the design could not have — a vocabulary extended silently is not closed.
CONSTRUCTS = {
    "domain_absent": (
        "no domain row covers this statement, and a verdict computed without "
        "a declared carrier has undefined meaning (Correction 4)"
    ),
    "division_semantics_undeclared": (
        "the statement divides and no row declares whether `/` truncates"
    ),
    "guard_unevaluable": (
        "the recovered antecedent carries a relation, head or operator the "
        "committed evaluator cannot decide"
    ),
    "guard_measure_zero": (
        "the guard carries an equality conjunct, which naive rejection "
        "sampling satisfies essentially never (E0d)"
    ),
    "head_outside_evaluator": (
        "a call head outside the evaluator's inventory — sin, exp, sqrt and "
        "their kin"
    ),
    "relation_undecidable": (
        "the top-level relation is not one the evaluator decides (`approx`)"
    ),
    "numeral_beyond_exact_parse": (
        "the template's consequent and the parsed ascii disagree after "
        "canonicalization, so the corpus wrote two different literals and a "
        "reviewer decides which it meant"
    ),
    "operator_pm": (
        "the parser emits a `pm` node for ± and the evaluator has no rule "
        "for it"
    ),
    "defined_output": (
        "an `=` whose one side is a slot declared with a reviewed output "
        "role: a definition, not a claim to sample (§3.2.1)"
    ),
    "named_constant": (
        "a declared constant whose committed value is a decimal "
        "approximation, so an exact-rational test against it is false for a "
        "second, independent reason (§3.2.1)"
    ),
    "exponent_variable": (
        "a sampled variable in an exponent position; testing it would make "
        "the sampler choose which powers are legal, which it has no "
        "authority to do"
    ),
    "evaluation_budget_exceeded": (
        "the result exceeds the registered rendering bound (E0e, discharged "
        "by ROADMAP-v0.20 §4c); a bound the compiler hits refuses by name "
        "rather than truncating"
    ),
    # --- added 2026-08-25, measured by this lane -----------------------
    "slot_alignment_failed": (
        "added 2026-08-25: canonical_ascii and the template's consequent do "
        "not align positionally, so no declaration can be attributed to any "
        "slot and typing by proximity would be a guess"
    ),
    "undeclared_slot": (
        "added 2026-08-25: a free slot with no declared syntactic_category. "
        "§3.2.1 admits exactly one sampled category, and a slot that is not "
        "declared `variable` is not one"
    ),
    "category_outside_typing_rule": (
        "added 2026-08-25: a declared category §3.2.1 does not name — "
        "`random_variable` is the measured instance"
    ),
    "no_sampled_variable": (
        "added 2026-08-25: every free slot is held or bound, so there is no "
        "point set and no sampling claim to make"
    ),
    "does_not_parse": (
        "added 2026-08-25 for completeness over the excluded territory: "
        "v0.19's foreign residue, whose own register is "
        "data/foreign_voice/register.json"
    ),
    "not_a_top_level_relation": (
        "added 2026-08-25: the term parses but its top level is not a "
        "relation, so there is nothing to decide"
    ),
    "nested_relation": (
        "added 2026-08-25: a relation inside a relation's argument"
    ),
}


def build() -> dict:
    import conform_census as census
    import conform_domain

    schema = conform_domain.load()
    rows = list(census.walk(output_roles=schema.output_roles))

    blocked: dict[str, list[str]] = {name: [] for name in CONSTRUCTS}
    witness: dict[str, str] = {}

    def block(construct: str, row, surface: str) -> None:
        blocked[construct].append(row.statement_id)
        witness.setdefault(construct, surface)

    testable: list = []
    for row in rows:
        if row.shape_exclusion == "does_not_parse":
            block("does_not_parse", row, row.statement_id)
            continue
        if row.shape_exclusion == "not_a_top_level_relation":
            block("not_a_top_level_relation", row, row.statement_id)
            continue
        if row.shape_exclusion == "nested_relation":
            block("nested_relation", row, row.statement_id)
            continue
        if row.shape_exclusion == "head_outside_evaluator":
            block("head_outside_evaluator", row, row.shape_detail)
            continue
        if row.shape_exclusion == "relation_undecidable":
            block("relation_undecidable", row, row.shape_detail)
            continue
        if row.shape_exclusion == "operator_outside_evaluator":
            block("operator_pm", row, row.shape_detail)
            continue
        if row.typed_refusal:
            block(row.typed_refusal, row, row.statement_id)
            continue
        if row.bucket == "refused_numeral_beyond_exact_parse":
            block("numeral_beyond_exact_parse", row, row.statement_id)
            continue
        if row.bucket == "refused_guard_unevaluable":
            block("guard_unevaluable", row,
                  row.guard.unevaluable_reason or row.statement_id)
            continue
        # Everything from here is shape-and-typing testable. Domain coverage
        # is applied at this step, not in the frozen census.
        if schema.carrier_for(row.statement_id, row.corpus) is None:
            block("domain_absent", row, row.statement_id)
            continue
        if row.bucket == "guarded" and row.guard.has_equality:
            block("guard_measure_zero", row, row.statement_id)
            continue
        testable.append(row)

    ground = [r for r in testable if r.ground]
    samplable = [r for r in testable if not r.ground]
    coupled = [
        r for r in samplable
        if r.bucket == "guarded" and not r.guard.box_only
    ]

    entries = []
    for construct, reason in CONSTRUCTS.items():
        ids = sorted(blocked[construct])
        entries.append({
            "construct_id": construct,
            "reason": reason,
            "surface_witness": witness.get(construct, ""),
            "blocking_count": len(ids),
            "statement_ids": ids,
        })

    blob = json.dumps(
        {e["construct_id"]: e["statement_ids"] for e in entries},
        sort_keys=True, ensure_ascii=False,
    ).encode("utf-8")

    return {
        "register_id": "conformance.register.v1",
        "frozen_at": "2026-08-25",
        "design": "docs/DESIGN-statements-that-run.md",
        "writer": "scripts/write_conformance_register.py",
        "commit_at_freeze": _git("rev-parse", "HEAD"),
        "what_this_is": [
            "E0c's register, frozen and digested BEFORE the first verdict. "
            "One row per blocking construct, exhaustive statement ids, no "
            "silent drops.",
            "It is where most of this cycle's territory lands, and the design "
            "says so: the register is not an appendix.",
        ],
        "blocking_counts_are_never_summed": (
            "This object is indexed by CONSTRUCT and a statement can carry "
            "two. E3's arithmetic partitions STATEMENTS and every statement "
            "lands in exactly one bucket. Two questions, two objects — "
            "summing these rows would double-count, which the design's first "
            "draft implied could be done."
        ),
        "the_register_ships_its_zeros": (
            "`operator_pm` is a real construct — the parser emits the node "
            "and the evaluator has no rule for it — and measures zero here. "
            "A register that lists only its populated rows cannot show you a "
            "zero."
        ),
        "entries": entries,
        "blocked_set_digest": hashlib.sha256(blob).hexdigest(),
        "schema_digest_at_freeze": schema.digest,
        "parser_digest_at_freeze": conform_domain.sha256_lf(
            REPO / "scripts" / "match_signatures.py"),
        "evaluator_digest_at_freeze": conform_domain.sha256_lf(
            REPO / "scripts" / "evaluate.py"),
        "sampler_digest_at_freeze": conform_domain.sha256_lf(
            REPO / "scripts" / "conform_sampler.py"),
        "census_digest_at_freeze": conform_domain.sha256_lf(
            REPO / "scripts" / "conform_census.py"),
        "e2_denominator": {
            "what_this_is": (
                "E0c publishes E2's denominator before E2 is read, so a rate "
                "can never be quoted against a denominator the schema had not "
                "actually reached. It is the samplable set INTERSECTED WITH "
                "schema coverage, not the whole samplable set."
            ),
            "samplable_and_schema_covered": len(samplable),
            "of_which_couple_variables": len(coupled),
            "ground_and_schema_covered": len(ground),
            "ground_is_not_in_the_sampling_denominator": (
                "The ground statements are decided by E1 and carry no free "
                "variable to sample; adding them would inflate the sampling "
                "denominator with statements no sampler ever touches."
            ),
        },
        "non_claims": [
            "No verdict is computed here and no point is sampled.",
            "A register entry is not a negative result about a statement. It "
            "says nothing was computed and names why.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=ARTIFACT)
    parser.add_argument("--allow-compiler-present", action="store_true")
    args = parser.parse_args(argv)

    if (REPO / COMPILER).exists() and not args.allow_compiler_present:
        print(
            f"REFUSING to write: {COMPILER} exists. E0c freezes the register "
            f"before the first verdict, and a register frozen after the "
            f"compiler can be shaped by what the compiler found.",
            file=sys.stderr,
        )
        return 2

    record = build()
    out = REPO / args.out
    out.write_text(
        json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    total = 0
    for entry in record["entries"]:
        if entry["blocking_count"]:
            print(f"   {entry['construct_id']:32s} {entry['blocking_count']:6d}")
            total += entry["blocking_count"]
        else:
            print(f"   {entry['construct_id']:32s} {0:6d}   (declared, measures zero)")
    print(f"   {'-' * 32} {'-' * 6}")
    print(f"   {'construct-indexed total':32s} {total:6d}   (NEVER summed against E3)")
    denominator = record["e2_denominator"]
    print()
    print(f"E2 denominator (samplable AND schema-covered): "
          f"{denominator['samplable_and_schema_covered']}")
    print(f"   of which coupled guards: {denominator['of_which_couple_variables']}")
    print(f"ground AND schema-covered : {denominator['ground_and_schema_covered']}")
    print(f"blocked_set_digest        : {record['blocked_set_digest'][:16]}")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
