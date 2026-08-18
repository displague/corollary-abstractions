#!/usr/bin/env python3
"""Construction check: does the ambiguity a row claims actually exist?

v0.14 authored twenty rows predicted to ASK and the resolver bound eight of
them straight to the intended id.  Those rows were not wrong about the
resolver; they were wrong about the graph.  Their ambiguity was asserted in
an author's rationale -- "several quadrilateral readings remain" -- and never
checked against the corpus, so Q2 spent its one-shot measuring clarification
on candidate sets that were already singletons.

This module makes the claim checkable before a row is committed, and it has
one hard constraint: it may not ask a resolver.  A row verified by running
the resolver would be a row authored to match the implementation, which is
the oracle the whole preregistration discipline exists to prevent.  So the
criterion here is capability-blind and reads only committed corpus text --
the same title-token arm v0.14 published as its control, reused rather than
restated so there is exactly one definition of "blind".

An ASK row must therefore NAME its competitors instead of asserting them:

    retained_ids   readings that must survive the follow-up
    competing_ids  readings the corpus really offers and the follow-up
                   must eliminate

and this module checks that the corpus agrees on all counts.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from answer import records  # noqa: E402
from decompose import INGESTED_CORPUS_PREFIXES  # noqa: E402
from measure_when_to_ask import (  # noqa: E402
    BLIND_LIMIT,
    _narrow_matched,
    jaccard,
    parse_followup,
    title_tokens,
)
from resolver import GraphIndex  # noqa: E402


@dataclass(frozen=True)
class BlindView:
    """One query's ranking under the published capability-blind criterion."""

    scores: dict[str, float]
    ranked: tuple[str, ...]

    def score(self, statement_id: str) -> float:
        return self.scores.get(statement_id, 0.0)

    def top(self, limit: int = BLIND_LIMIT) -> tuple[str, ...]:
        return self.ranked[:limit]


class TitleIndex:
    """Committed titles, tokenized once.

    `blind_initial` re-tokenizes every title on every call, which is right
    for a scorer that runs 48 times and wrong for a checker an author runs
    while writing rows.  The ranking produced here is identical; only the
    arithmetic is shared.
    """

    def __init__(self, corpus: dict[str, tuple[dict, str]]) -> None:
        self.tokens = {
            sid: title_tokens(str(node.get("title", "")))
            for sid, (node, _corpus) in corpus.items()
        }

    def view(self, text: str) -> BlindView:
        asked = title_tokens(text)
        scores = {sid: jaccard(asked, toks) for sid, toks in self.tokens.items()}
        ranked = tuple(
            sid for sid in sorted(scores, key=lambda s: (-scores[s], s))
        )
        return BlindView(scores, ranked)


def eligible(statement_id: str, corpus: dict[str, tuple[dict, str]]) -> str | None:
    """Why this id may not carry credit, or None if it may."""
    found = corpus.get(statement_id)
    if found is None:
        return "absent from data/"
    if found[1].startswith(tuple(INGESTED_CORPUS_PREFIXES)):
        return f"belongs to ingested corpus {found[1]}"
    return None


def check_row(
    row: dict,
    corpus: dict[str, tuple[dict, str]],
    titles: TitleIndex,
    index: GraphIndex,
    *,
    blind_limit: int = BLIND_LIMIT,
) -> list[str]:
    """Every reason this row's claimed ambiguity is not visible in the graph."""
    problems: list[str] = []
    if row.get("expected_route") != "ASK":
        return problems

    primary = row.get("primary_id")
    retained = list(row.get("retained_ids") or [])
    competing = list(row.get("competing_ids") or [])

    if not isinstance(primary, str) or primary not in retained:
        problems.append("retained_ids must contain primary_id")
        return problems
    if len(set(retained)) != len(retained) or len(set(competing)) != len(competing):
        problems.append("retained_ids and competing_ids must each be unique")
    overlap = set(retained) & set(competing)
    if overlap:
        problems.append(f"ids are both retained and competing: {sorted(overlap)}")

    # 1. The competitors have to be named. An ASK with nothing to eliminate
    #    is a BIND that has not admitted it.
    if not competing:
        problems.append(
            "ASK declares no competing_ids; a row that names no alternative "
            "reading is claiming ambiguity without exhibiting it"
        )

    for sid in [*retained, *competing]:
        why = eligible(sid, corpus)
        if why is not None:
            problems.append(f"{sid}: {why}")
    if problems:
        return problems

    view = titles.view(str(row.get("query", "")))

    # 2. The corpus's own words must not settle it. If the intended reading
    #    is the unique best title match, the graph DOES discriminate and the
    #    honest prediction is BIND -- this is exactly the shape of the eight
    #    v0.14 rows that bound straight to their intended id.
    best_rival = max(
        (view.score(sid) for sid in competing), default=0.0
    )
    if view.score(primary) > best_rival:
        problems.append(
            f"blind title match already prefers {primary} "
            f"({view.score(primary):.4f}) over every declared competitor "
            f"({best_rival:.4f}); the corpus is not ambiguous here"
        )

    # 3. Every named reading must be findable at all. A competitor the blind
    #    arm cannot see is a competitor only the author can see.
    horizon = set(view.top(blind_limit))
    unseen = [sid for sid in [*retained, *competing] if sid not in horizon]
    if unseen:
        problems.append(
            f"not within the blind top {blind_limit} for this query: {sorted(unseen)}"
        )

    # 4. The follow-up has to do work: keep everything intended, remove at
    #    least one thing that was really there. v0.14 checked only the first
    #    half, so a follow-up that changed nothing scored as a success.
    follow = row.get("follow_up")
    if not isinstance(follow, dict):
        problems.append("ASK needs a follow_up")
        return problems
    try:
        kind, value = parse_followup(str(follow.get("line", "")))
    except Exception as exc:  # noqa: BLE001 - surfaced as a construction problem
        problems.append(f"follow-up does not parse: {exc}")
        return problems
    declared = tuple([*retained, *competing])
    survivors = set(_narrow_matched(index, declared, kind, value))
    dropped_intended = [sid for sid in retained if sid not in survivors]
    if dropped_intended:
        problems.append(f"follow-up drops intended readings: {sorted(dropped_intended)}")
    if not [sid for sid in competing if sid not in survivors]:
        problems.append(
            "follow-up eliminates no declared competitor; it narrows nothing"
        )
    return problems


def audit(
    rows: Iterable[dict],
    corpus: dict[str, tuple[dict, str]] | None = None,
    index: GraphIndex | None = None,
) -> dict:
    """Check every ASK row and report, without resolving anything."""
    from resolver import default_index  # noqa: PLC0415

    corpus = corpus if corpus is not None else records([REPO / "data"])
    index = index if index is not None else default_index()
    titles = TitleIndex(corpus)
    findings: list[dict] = []
    checked = 0
    for row in rows:
        if row.get("expected_route") != "ASK":
            continue
        checked += 1
        problems = check_row(row, corpus, titles, index)
        if problems:
            findings.append({"row_id": row.get("row_id"), "problems": problems})
    return {
        "schema": "verified_ambiguity.v1",
        "ask_rows_checked": checked,
        "rows_refused": len(findings),
        "findings": findings,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="holdout JSON with a `rows` list")
    args = parser.parse_args(argv)
    doc = json.loads(args.spec.read_text(encoding="utf-8"))
    report = audit(doc["rows"])
    print(json.dumps(report, indent=2))
    return 1 if report["rows_refused"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
