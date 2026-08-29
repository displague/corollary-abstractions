#!/usr/bin/env python3
"""Execute the sealed G-P0 drawing rule. Nothing here is an elaboration.

`experiments/guest_axiom_draw_rule.json` is the source of truth and was
committed before this writer. The recast is exact membership of statement
ids the sealed `why` already named, against the same 2,313 covered set
the voice already measured. The resolver is not consulted.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from measure_foreign_voice import covered_rows  # noqa: E402
from report_provenance import provenance_block, sha256_lf_file  # noqa: E402
from supposition import _atom  # noqa: E402

RULE_PATH = ROOT / "experiments" / "guest_axiom_draw_rule.json"
QUESTIONS_PATH = ROOT / "experiments" / "plain_question_set.json"
PREVIEW_PATH = ROOT / "data" / "foreign_voice" / "eligibility_preview.json"
REGISTER_PATH = ROOT / "data" / "foreign_voice" / "register.json"
CORRECTIONS_PATH = ROOT / "experiments" / "crossing_corrections.json"
DEFAULT_OUT = ROOT / "experiments" / "guest_hypotheses.json"

# Tokens that can be statement ids: the corpus alphabet plus dots.
_ID_TOKEN = re.compile(r"[a-z0-9]+(?:\.[a-z0-9_]+)+")


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def covered_ids() -> set[str]:
    preview = load_json(PREVIEW_PATH)
    register = load_json(REGISTER_PATH)
    return {row["statement_id"] for row in covered_rows(preview, register)}


def named_covered_ids(why: str, covered: set[str]) -> list[str]:
    """Exact covered-set members appearing as tokens in `why`.

    Order is first-appearance order. A longer id is one token, not a
    prefix match on a shorter sibling.
    """
    seen: list[str] = []
    found: set[str] = set()
    for token in _ID_TOKEN.findall(why):
        if token in covered and token not in found:
            found.add(token)
            seen.append(token)
    return seen


def recast_question(question: dict, covered: set[str], pilot_ids: set[str]) -> dict:
    why = question.get("why") or ""
    named = named_covered_ids(why, covered)
    exhaust = question.get("authors_prior") == "exhaust"
    if exhaust or len(named) != 1:
        stratum = "nameless_probe"
        target = None
    else:
        stratum = "recorded_question"
        target = named[0]
    text = question["question"]
    normal, _polarity = _atom(text)
    return {
        "hypothesis_id": f"gp0-rq-{question['question_id']}",
        "source_stratum": stratum,
        "hypothesis_text": text,
        "hypothesis_normal_form": normal,
        "target_statement_id": target,
        "question_id": question["question_id"],
        "authors_prior": question["authors_prior"],
        "pilot": question["question_id"] in pilot_ids,
        "named_covered_ids_in_why": named,
    }


def draw_corrections(covered: set[str]) -> dict:
    if not CORRECTIONS_PATH.is_file():
        return {
            "correction_arm": "BLOCKED_NO_LOG",
            "pool_size": 0,
            "drawn": [],
            "reason": (
                "experiments/crossing_corrections.json is absent; the sealed "
                "rule predicted BLOCKED_NO_LOG and forbids inventing the pool."
            ),
        }
    raw = load_json(CORRECTIONS_PATH)
    if not isinstance(raw, list):
        raw = raw.get("corrections") or raw.get("records") or []
    eligible = [
        row
        for row in raw
        if isinstance(row, dict) and row.get("target_statement_id") in covered
    ]
    eligible.sort(key=lambda row: row["correction_id"])
    drawn = eligible[:20]
    if not eligible:
        arm = "BLOCKED_NO_LOG"
    elif len(drawn) < 20:
        arm = "UNDERFILLED"
    else:
        arm = "DRAWN"
    records = []
    for row in drawn:
        text = row["hypothesis_text"]
        normal, _ = _atom(text)
        records.append(
            {
                "hypothesis_id": f"gp0-mc-{row['correction_id']}",
                "source_stratum": "maintainer_correction",
                "hypothesis_text": text,
                "hypothesis_normal_form": normal,
                "target_statement_id": row["target_statement_id"],
                "question_id": None,
                "authors_prior": None,
                "pilot": False,
                "correction_id": row["correction_id"],
                "served_answer_ref": row.get("served_answer_ref"),
            }
        )
    return {
        "correction_arm": arm,
        "pool_size": len(eligible),
        "drawn": records,
        "reason": None if arm == "DRAWN" else (
            "named source present but eligible pool smaller than 20"
            if arm == "UNDERFILLED"
            else "named source present but no covered targets"
        ),
    }


def build() -> dict:
    rule = load_json(RULE_PATH)
    questions = load_json(QUESTIONS_PATH)["questions"]
    covered = covered_ids()
    pilot_ids = set(rule["recorded_question_recast"]["pilot_reservation"]["question_ids"])
    recast = [recast_question(q, covered, pilot_ids) for q in questions]
    corrections = draw_corrections(covered)
    hypotheses = recast + corrections["drawn"]
    recast_only = [h for h in recast]
    recast_yield = {
        "non_exhaust_questions": sum(
            1 for h in recast_only if h["authors_prior"] != "exhaust"
        ),
        "exhaust_questions": sum(
            1 for h in recast_only if h["authors_prior"] == "exhaust"
        ),
        "landed_in_covered_set": sum(
            1 for h in recast_only if h["source_stratum"] == "recorded_question"
        ),
        "nameless_because_exhaust": sum(
            1
            for h in recast_only
            if h["authors_prior"] == "exhaust" and h["source_stratum"] == "nameless_probe"
        ),
        "nameless_because_no_unique_covered_id": sum(
            1
            for h in recast_only
            if h["authors_prior"] != "exhaust" and h["source_stratum"] == "nameless_probe"
        ),
        "why_the_yield_can_be_zero": (
            "the sealed questions name curated-library ids; the 2,313 "
            "covered set is the voice's oracle-accepted minus register-"
            "blocked ids, 99.87% lean_workbook. Membership in that set "
            "is the design's target rule, not a resolver bind."
        ),
    }
    counts = {
        "total": len(hypotheses),
        "recorded_question": sum(
            1 for h in hypotheses if h["source_stratum"] == "recorded_question"
        ),
        "maintainer_correction": sum(
            1 for h in hypotheses if h["source_stratum"] == "maintainer_correction"
        ),
        "nameless_probe": sum(
            1 for h in hypotheses if h["source_stratum"] == "nameless_probe"
        ),
        "pilot": sum(1 for h in hypotheses if h["pilot"]),
        "non_nameless_in_covered_set": sum(
            1
            for h in hypotheses
            if h["source_stratum"] != "nameless_probe"
            and h["target_statement_id"] in covered
        ),
        "covered_set_size": len(covered),
        "recast_yield": recast_yield,
    }
    return {
        "schema": "corollary.guest-hypotheses/1",
        "design": "docs/DESIGN-guest-axiom.md",
        "draw_rule": "experiments/guest_axiom_draw_rule.json",
        "draw_rule_sha256_lf": sha256_lf_file(RULE_PATH),
        "correction_arm": corrections["correction_arm"],
        "correction_arm_reason": corrections["reason"],
        "correction_pool_size": corrections["pool_size"],
        "hypotheses": hypotheses,
        "counts": counts,
        "counts_note": (
            "computed from hypotheses[], not typed beside them. "
            "correction_arm BLOCKED_NO_LOG means the 50-set is the 30 recasts "
            "only; person-wrong is unfilled, not faked."
        ),
        "provenance": provenance_block(
            Path(__file__),
            [RULE_PATH, QUESTIONS_PATH, PREVIEW_PATH, REGISTER_PATH],
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    payload = build()
    args.out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
