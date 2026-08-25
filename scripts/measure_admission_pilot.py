#!/usr/bin/env python3
"""E0f: measure admission over the coupled guards, THEN freeze E2a's floor.

`docs/DESIGN-statements-that-run.md` E0f. The design's first draft froze an
admission floor at 90%, and the adversarial review removed it because **the
number had nothing under it** — the sampler did not exist, and most of the
inequality-only guards are box constraints that admit trivially while a
minority couple their variables and are the only ones whose admission rate
is in genuine doubt. *"A floor set at 90% over a set that is 74% trivial is
a floor calibrated by the easy majority."*

So this measures first. It runs the committed sampler at M = 1,000 over the
coupled guards alone, publishes the admission distribution, and the dated
amendment that follows freezes E2a's floor with this as its justification.
**Both branches yield an artifact**: a high rate sets E2a over the whole
samplable set, a low rate narrows E2's denominator to what the sampler
actually reaches — *"which is a finding about these guards, not a failure of
the cycle."*

**Two admission gates, reported separately.** A candidate can fail because it
is not in the declared carrier (`Nat` admits no negatives and no fractions)
or because the guard rejects it. Summing them would hide which gate did the
work, and the carrier gate is the schema's while the guard gate is the
statement's.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

ARTIFACT = "experiments/conformance_admission_pilot.json"


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def build(budget: int) -> dict:
    import conform
    import conform_census as census
    import conform_domain

    schema = conform_domain.load()
    relations = census.evaluator_relations()

    coupled = []
    for path in census.corpora():
        document = json.loads(path.read_text(encoding="utf-8"))
        corpus = document.get("corpus_id", path.parent.name)
        for node in document.get("statement_nodes", []):
            row = census.classify(node, corpus, relations, schema.output_roles)
            if row.bucket != "guarded" or row.guard.has_equality:
                continue
            if row.guard.box_only:
                continue
            if schema.carrier_for(row.statement_id, row.corpus) is None:
                continue
            coupled.append((node, row))

    rows = []
    for node, row in coupled:
        try:
            program = conform.compile_statement(node, row, schema)
        except conform.Refusal as exc:
            rows.append({
                "statement_id": row.statement_id,
                "refused": exc.construct,
                "admitted": 0,
            })
            continue
        record = conform.run(program, schema.digest, budget=budget,
                             keep_points=0)
        rows.append({
            "statement_id": row.statement_id,
            "admitted": record.get("points_admitted", 0),
            "guard_rejected": record.get("points_rejected", 0),
            "domain_rejected": record.get("points_domain_rejected", 0),
            "errored": record.get("points_errored", 0),
            "verdict": record.get("verdict"),
        })

    measured = [r for r in rows if "refused" not in r]
    admitted_counts = [r["admitted"] for r in measured]
    admitted_any = [r for r in measured if r["admitted"] > 0]
    rates = [r["admitted"] / budget for r in measured] or [0.0]

    return {
        "run_id": "conformance.admission_pilot.v1",
        "registered": "2026-08-25",
        "gate": "E0f — the admission pilot, measured before E2a freezes",
        "design": "docs/DESIGN-statements-that-run.md",
        "writer": "scripts/measure_admission_pilot.py",
        "commit": _git("rev-parse", "HEAD"),
        "why_this_runs_before_a_floor_is_frozen": (
            "The design's first draft froze 90% and the review removed it: "
            "the number had nothing under it, and a floor set over a set that "
            "is mostly box constraints is calibrated by the easy majority. "
            "E0f measures the hard minority first."
        ),
        "budget_M": budget,
        "scope": {
            "coupled_guards_measured": len(measured),
            "coupled_guards_refused_at_compile": len(rows) - len(measured),
            "why_coupled_only": (
                "Box constraints (`slot REL num`) are directly samplable per "
                "variable and admit trivially. The guards that couple their "
                "variables are the only ones whose admission rate is in "
                "genuine doubt, so they are what a floor should be calibrated "
                "on."
            ),
        },
        "admission": {
            "statements_admitting_at_least_one": len(admitted_any),
            "statements_admitting_none": len(measured) - len(admitted_any),
            "share_admitting_at_least_one": (
                round(len(admitted_any) / len(measured), 6) if measured else 0.0
            ),
            "mean_admission_rate": round(statistics.mean(rates), 6),
            "median_admission_rate": round(statistics.median(rates), 6),
            "max_admitted_points": max(admitted_counts) if admitted_counts else 0,
            "distribution_by_decile": _deciles(rates),
        },
        "two_gates_reported_separately": {
            "domain_rejected_total": sum(
                r.get("domain_rejected", 0) for r in measured),
            "guard_rejected_total": sum(
                r.get("guard_rejected", 0) for r in measured),
            "why": (
                "A candidate can fail the declared carrier (Nat admits no "
                "negatives and no fractions) or fail the guard. Summing them "
                "would hide which gate did the work; the carrier gate is the "
                "schema's and the guard gate is the statement's."
            ),
        },
        "per_statement": rows,
    }


def _deciles(rates) -> dict:
    buckets = {f"{i/10:.1f}-{(i+1)/10:.1f}": 0 for i in range(10)}
    for rate in rates:
        index = min(int(rate * 10), 9)
        buckets[f"{index/10:.1f}-{(index+1)/10:.1f}"] += 1
    return buckets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--budget", type=int, default=1000)
    parser.add_argument("--out", default=ARTIFACT)
    args = parser.parse_args(argv)

    record = build(args.budget)
    out = REPO / args.out
    out.write_text(
        json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    scope, admission = record["scope"], record["admission"]
    print(f"coupled guards measured : {scope['coupled_guards_measured']}")
    print(f"   refused at compile   : {scope['coupled_guards_refused_at_compile']}")
    print(f"admitting >= 1 point    : {admission['statements_admitting_at_least_one']}"
          f"  ({admission['share_admitting_at_least_one']:.1%})")
    print(f"admitting none          : {admission['statements_admitting_none']}")
    print(f"mean admission rate     : {admission['mean_admission_rate']:.4f}")
    print(f"median admission rate   : {admission['median_admission_rate']:.4f}")
    print(f"max admitted points     : {admission['max_admitted_points']} of {args.budget}")
    gates = record["two_gates_reported_separately"]
    print(f"rejected by carrier     : {gates['domain_rejected_total']}")
    print(f"rejected by guard       : {gates['guard_rejected_total']}")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
