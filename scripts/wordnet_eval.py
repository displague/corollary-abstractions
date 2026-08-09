#!/usr/bin/env python3
"""Adjudicate P-CF6 on fixed held-out request terms.

The eight terms below are intentionally absent from the five committed stores'
exact/neighborhood surface at registration time. Each has an OEWN synonym that
is already a corpus alias. Success means lexical coverage, not semantic proof:
the expected corpus owner must appear in retrieved context, every WordNet item
must remain empirical, and the frame executor's UNKNOWN verdict must not move.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from controller import Verdict
from frames import FrameExecutor, FrameSpec, Literal
from retrieval import (
    RetrievalState,
    RetrievalVerifier,
    UnifiedKnowledgeStore,
    point_action,
    retrieval_action,
)


CASES = (
    # term, expected corpus owner in context, safely bindable without a sense cue
    ("euclidian", "geometry.metric_geometry.euclidean_distance_formula", True),
    ("perseverance", "narrative.frame.premise_persistence", False),
    ("quickening", "physics.frames.galilean_acceleration_invariance", True),
    ("geodetic", "diffgeo.curves.geodesic_energy_functional", True),
    ("earlier", "temporal.order.strict_precedence_asymmetry", True),
    ("solving", "narrative.structure.resolution_outcome", True),
    ("reverse", "logic.inference.contraposition", True),
    ("repeating", "logic.boolean_laws.idempotence", True),
)


def owner_ids(result) -> set[str]:
    return {
        item.source_ids[0]
        for item in result.items
        if item.source in {"corpus", "lexicon", "proof"}
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wordnet", type=Path)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    baseline = UnifiedKnowledgeStore.load(repo / "data", repo / "reports")
    enriched = UnifiedKnowledgeStore.load(
        repo / "data", repo / "reports", args.wordnet
    )

    executor = FrameExecutor()
    frame = executor.open_frame(
        FrameSpec(frame="runtime.frames.wordnet_eval", retrieval="open")
    )
    baseline_hits = 0
    enriched_hits = 0
    verdict_changes = 0
    binding_mismatches = 0
    safe_bindings = 0
    ambiguity_refusals = 0
    mutation_detections = 0
    for term, expected_owner, bindable in CASES:
        literal = Literal("request", "needs", term)
        before = executor.check(frame, literal)
        baseline_result = baseline.query(term, limit=200)
        enriched_result = enriched.query(term, limit=200)
        baseline_hit = expected_owner in owner_ids(baseline_result)
        enriched_hit = expected_owner in owner_ids(enriched_result)
        baseline_hits += baseline_hit
        enriched_hits += enriched_hit

        state = RetrievalState.from_unknown(
            executor, frame, "answer", term, literal
        )
        verifier = RetrievalVerifier(enriched, executor)
        retrieved = verifier.evaluate(state, retrieval_action(term))
        position = next(
            (
                material.position
                for material in (retrieved.next_state.context if retrieved.next_state else ())
                if material.item.source_ids[0] == expected_owner
            ),
            None,
        )
        pointed = (
            verifier.evaluate(retrieved.next_state, point_action(position))
            if retrieved.next_state is not None and position is not None
            else None
        )
        expected_verdict = Verdict.VERIFIED if bindable else Verdict.REFUSED
        if pointed is None or pointed.verdict is not expected_verdict:
            binding_mismatches += 1
        if pointed is not None and pointed.verdict is Verdict.VERIFIED:
            safe_bindings += 1
            after_frame = pointed.next_state.frame
        else:
            ambiguity_refusals += pointed is not None
            after_frame = (
                retrieved.next_state.frame
                if retrieved.next_state is not None
                else frame
            )
        after = executor.check(after_frame, literal)
        verdict_changes += (before.verdict, before.evidence) != (
            after.verdict,
            after.evidence,
        )

        # Capability-blind non-vacuity control: the same comparison must catch
        # an actual frame mutation that asserts the previously UNKNOWN literal.
        mutated = replace(
            frame,
            asserted=frame.asserted + ((f"blind:{term}", literal),),
        )
        changed = executor.check(mutated, literal)
        mutation_detections += (before.verdict, before.evidence) != (
            changed.verdict,
            changed.evidence,
        )

        lexical = tuple(
            material.item
            for material in (
                retrieved.next_state.context if retrieved.next_state else ()
            )
            if material.item.source == "wordnet"
        )
        if any(item.epistemic_status != "empirical" for item in lexical):
            raise AssertionError(f"status laundering for {term!r}")
        print(
            f"{term:14} baseline={baseline_result.mode:12} "
            f"wordnet={enriched_result.mode:8} "
            f"target={'hit' if enriched_hit else 'MISS'} "
            f"bind={'yes' if bindable else 'refused-polysemy'}"
        )

    total = len(CASES)
    print(f"coverage: baseline {baseline_hits}/{total}; wordnet {enriched_hits}/{total}")
    print(f"frame verdict changes: {verdict_changes}")
    print(f"safe bindings: {safe_bindings}/{total}")
    print(f"polysemy refusals: {ambiguity_refusals}/{total}")
    print(f"binding expectation mismatches: {binding_mismatches}")
    print(f"blind frame-mutation detections: {mutation_detections}/{total}")
    return (
        0
        if baseline_hits == 0
        and enriched_hits == total
        and not verdict_changes
        and not binding_mismatches
        and mutation_detections == total
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
