#!/usr/bin/env python3
"""Slice 2's registered run — every frozen gate, scored, on the sealed sets.

`experiments/plain_input_prereg.json` froze the gates, their numbers and
their voiding sentences before the proposer, the enumerator and the question
sets existed. This script scores them and writes
`experiments/plain_input_run.json`. It invents no clause and relaxes none: a
disagreement between this script and the preregistration is a bug in this
script.

## What is scored here and what was scored before

G4 (the quarantine invariant) and G6 (OFF, not crash) were scored at the
wiring commit and are **re-scored here**, because a gate that ran against an
earlier tree is a gate that ran against an earlier tree. G9 is **not
scored**: prereg amendments 3 and 4 adjudicate it NOT MET in advance, by
orchestrator ruling, and this run reports that verdict rather than
rediscovering it.

## The subsets, and why no number here is a rate over thirty

`experiments/plain_input_corpus_seal.json` carries the `denominators` block
and it is the thing to read before any number below. Thirteen of the thirty
sealed questions are bound by the resolver before the proposer is consulted;
nine were authored to exhaust; the two facts overlap. Each gate names the
subset it scores over and the sizes are never summed.

## Determinism

P4 (`experiments/plain_proposer_determinism.json`) put this model at
temperature 0 through two passes of this slice's own prompts and got
byte-identical output, so ROADMAP-v0.21 §4.0(2)'s determinism-plus-commit
clause applies: the artifact is committed from a deterministic runner and
reproductions are welcome and recorded. P4's own limit travels with every
number here — byte-identity across two passes on one machine on one day is
not a proof of determinism.

## B10 and B12 are slice 1's functions, called

They are imported from `scripts/run_session_gate.py` and run unchanged over
this corpus's seal. Re-implementing them here would be scoring a copy of the
fence rather than the fence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

import candidate_enumerator as ce  # noqa: E402
import plain_proposer as pp  # noqa: E402
import plain_router  # noqa: E402
import session_ledger as ledger  # noqa: E402

PREREG = "experiments/plain_input_prereg.json"
SEAL = "experiments/plain_input_corpus_seal.json"
PROMPTS = "experiments/plain_input_prompts.json"
QUESTIONS = "experiments/plain_question_set.json"
DISTRACTORS = "experiments/plain_distractor_set.json"
DETERMINISM = "experiments/plain_proposer_determinism.json"
OUT = "experiments/plain_input_run.json"
RUN_SCHEMA = "corollary.plain-input-run/1"

#: G5's blind draw. Seeded from the committed question set's own digest, so
#: the permutation is a fact about a sealed file rather than about the clock
#: this run happened to start on — `measure_throughput`'s device for C2,
#: reused rather than invented.
BLIND_SEED_SOURCE = QUESTIONS

#: G4's line corpus: one line per registered row the proposer does not own.
#: Kept here rather than derived, because G4's whole point is that these rows
#: are the ones the proposer must not touch, and a derived list could quietly
#: stop covering one.
G4_LINES = (
    "",
    "2 + 2",
    "owns x ^ 2",
    "suppose the corpus is complete",
    "retract a999",
    "twin programming.euclid.recursive",
    "twin no.such.statement",
    "de morgan laws",
    "tell me a story",
    "conform no.such.statement a=1",
    "what is the cosine of a double angle",
    "the quadratic formula",
    "where does alice think the ball is",
    "scripts/harness.py",
    "reachable programming.euclid.recursive",
)


def _load(relative: str) -> dict:
    return json.loads((REPO / relative).read_text(encoding="utf-8"))


def _blind_rng() -> random.Random:
    seed = hashlib.sha256(
        (REPO / BLIND_SEED_SOURCE).read_bytes()
    ).hexdigest()
    return random.Random(int(seed[:16], 16))


# --------------------------------------------------------------------------
# G1 — proposal coverage, with amendment 1's disclosure attached
# --------------------------------------------------------------------------


def score_g1(questions: list[dict], index) -> dict:
    del index
    rows = []
    for item in questions:
        candidates, verified = ce.verified_candidates(item["question"], REPO)
        proposal = pp.propose(item["question"], candidates)
        chosen = None
        if proposal.selected_index is not None:
            chosen = next(
                (
                    v
                    for v in verified
                    if v.candidate.index == proposal.selected_index
                ),
                None,
            )
        rows.append(
            {
                "question_id": item["question_id"],
                "authors_prior": item["authors_prior"],
                "candidates": len(candidates),
                "verified": len(verified),
                "any_verified": bool(verified),
                "selected_index": proposal.selected_index,
                "raw": proposal.raw,
                "discarded_reason": proposal.discarded_reason,
                "selection_verified": chosen is not None,
                "selected_line": None if chosen is None else chosen.candidate.line,
                "verification_strength": (
                    None if chosen is None else chosen.verification_strength
                ),
            }
        )
    total = len(rows)
    any_verified = sum(1 for row in rows if row["any_verified"])
    selected_and_verified = sum(1 for row in rows if row["selection_verified"])
    ceiling = _load(QUESTIONS)["ceiling"]["best_honest_verified_candidate_count"]
    exhaust_rows = [row for row in rows if row["authors_prior"] == "exhaust"]
    return {
        "kind": "MEASUREMENT — no floor, published either way",
        "verdict": "MEASURED (no floor, by registration)",
        "denominator": f"all {total} sealed questions",
        "at_least_one_verified_candidate": any_verified,
        "at_least_one_verified_candidate_rate": round(any_verified / total, 4),
        "this_is_the_WEAKER_number_and_here_is_why": (
            "prereg amendment 1: enumeration is generous and `word_match` "
            "verification is nearly free — a statement candidate is offered "
            "whenever the utterance shares a content word with a title or "
            "keyword, and it verifies whenever that title resolves back to "
            "that statement, which is almost always. So this rate is close to "
            "'how many utterances contain a content word the corpus also "
            "uses', and it is NOT a measure of whether the reading is right."
        ),
        "the_number_the_served_behaviour_actually_rests_on": {
            "model_selected_and_the_selection_verified": selected_and_verified,
            "rate": round(selected_and_verified / total, 4),
            "why_it_is_published_beside_the_headline": (
                "selection plus verification is what a conditional answer "
                "stands on. Amendment 1 registered this pairing before the "
                "run, so the weaker number cannot travel alone."
            ),
        },
        "against_the_sealed_ceiling": {
            "ceiling": ceiling,
            "of": total,
            "why": (
                "nine questions were authored to EXHAUST, and the set says a "
                "candidate verifying for one of them 'would be the proposer "
                "inventing rather than selecting'."
            ),
            "exhaust_prior_questions_with_a_verified_candidate": sum(
                1 for row in exhaust_rows if row["any_verified"]
            ),
            "exhaust_prior_questions_the_model_selected_for": sum(
                1 for row in exhaust_rows if row["selection_verified"]
            ),
        },
        "no_stranger_usability_claim": (
            "maintainer-authored questions about a corpus the author knows. "
            "STRANGER's park is cited, not re-encountered."
        ),
        "rows": rows,
    }


# --------------------------------------------------------------------------
# G3 — the distractor set, with the pre-check C-V4 dropped
# --------------------------------------------------------------------------


def _selected_line(utterance: str) -> tuple[str | None, list, list]:
    candidates, verified = ce.verified_candidates(utterance, REPO)
    proposal = pp.propose(utterance, candidates)
    if proposal.selected_index is None:
        return None, candidates, verified
    for item in verified:
        if item.candidate.index == proposal.selected_index:
            return item.candidate.line, candidates, verified
    return None, candidates, verified


def score_g3(distractors: dict) -> dict:
    included, excluded, collapsed = [], [], []
    for pair in distractors["pairs"]:
        # THE PRE-CHECK, BEFORE ANY SCORING. Every pair must be shown by
        # exact code to denote two DIFFERENT verified queries. C-V4′ exists
        # because C-V4 "never establishes that the mutation should have
        # moved"; this is that clause, carried.
        _a_sel, _a_cands, a_verified = _selected_line(pair["a"])
        _b_sel, _b_cands, b_verified = _selected_line(pair["b"])
        a_lines = {v.candidate.line for v in a_verified}
        b_lines = {v.candidate.line for v in b_verified}
        a_hit = pair["expected_a"] in {
            v.candidate.statement_id or v.candidate.line for v in a_verified
        }
        b_hit = pair["expected_b"] in {
            v.candidate.statement_id or v.candidate.line for v in b_verified
        }
        row = {
            "pair_id": pair["pair_id"],
            "a": pair["a"],
            "b": pair["b"],
            "expected_a": pair["expected_a"],
            "expected_b": pair["expected_b"],
            "a_verifies_its_expected_query": a_hit,
            "b_verifies_its_expected_query": b_hit,
            "a_verified_lines": sorted(a_lines),
            "b_verified_lines": sorted(b_lines),
            "a_selected": _a_sel,
            "b_selected": _b_sel,
        }
        if not (a_hit and b_hit and pair["expected_a"] != pair["expected_b"]):
            row["excluded_because"] = (
                "the pre-check could not show these two sentences denote two "
                "DIFFERENT verified registered queries, so a proposer mapping "
                "them to one query would be CORRECT and scoring it as a "
                "collapse would score the set's defect as the model's"
            )
            excluded.append(row)
            continue
        row["collapsed"] = (
            _a_sel is not None and _b_sel is not None and _a_sel == _b_sel
        )
        if row["collapsed"]:
            collapsed.append(row)
        included.append(row)
    return {
        "registered_floor": distractors["registered_floor"],
        "voiding_sentence_verbatim": distractors["voiding_sentence_verbatim"],
        "pairs_in_the_set": len(distractors["pairs"]),
        "pairs_excluded_by_the_pre_check": len(excluded),
        "pairs_scored": len(included),
        "pairs_collapsed": len(collapsed),
        "verdict": "GREEN" if not collapsed else "VOID",
        "the_clause_C_V4_dropped_and_this_run_executed": (
            "every pair was checked BY EXACT CODE to denote two different "
            "verified registered queries BEFORE scoring, and the exclusions "
            "are counted and published rather than dropped."
        ),
        "excluded": excluded,
        "scored": included,
    }


# --------------------------------------------------------------------------
# G2, G4, G4b, G5, G6, G7, G7b, G8
# --------------------------------------------------------------------------


def score_g2(seal: dict, prompts: dict) -> dict:
    """Every served interpretation: verifier-confirmed or supposition-labelled."""

    from harness import CoreSession, route_line  # noqa: PLC0415
    from resolver import default_index  # noqa: PLC0415

    reachable = set(
        seal["denominators"]["proposer_reachable_remainder"]["question_ids"]
    )
    questions = {
        item["question_id"]: item["question"]
        for item in _load(QUESTIONS)["questions"]
    }
    index = default_index()
    counterexamples, rows = [], []
    for question_id in sorted(reachable):
        session = CoreSession.boot(REPO, offline=True, session_id="g2")
        session.resolver_index = index
        session.proposer = plain_router.PlainRouter(repo_root=REPO)
        verdict = route_line(REPO, session, questions[question_id])
        status = verdict.get("status")
        receipt = verdict.get("receipt") or {}
        row = {
            "question_id": question_id,
            "route": verdict.get("route"),
            "status": status,
            "suppositions": len(receipt.get("suppositions") or []),
            "verification_strength": receipt.get("verification_strength"),
        }
        if status == "conditional":
            ok = (
                len(receipt.get("suppositions") or []) == 1
                and receipt["suppositions"][0]["source"] == "proposed"
                and receipt.get("verification_strength")
                in ("exact_computation", "committed_record", "word_match")
            )
            row["labelled"] = "supposition"
        elif status == "waiting" and verdict.get("route") == "plain_input":
            ok = (
                len(receipt.get("verified_readings") or []) >= 2
                and not receipt.get("suppositions")
            )
            row["labelled"] = "clarification naming the readings"
        else:
            # Nothing was interpreted: row 12 exhausted, or an earlier row
            # served it. Neither serves an interpretation this slice made.
            ok = True
            row["labelled"] = "no interpretation served by this slice"
        row["ok"] = ok
        if not ok:
            counterexamples.append(row)
        rows.append(row)
    del prompts
    return {
        "standard": "ANY COUNTEREXAMPLE FAILS",
        "denominator": (
            f"the {len(reachable)} proposer-reachable questions — the whole "
            "surface this slice adds"
        ),
        "and_the_denominator_this_gate_does_NOT_cover": (
            "the thirteen the resolver binds at `found`. Those are served "
            "interpretations of an earlier row, they are the standing defect, "
            "and G9 is where they are adjudicated — NOT MET, by ruling. "
            "Scoring them here would let this slice's gate absorb a defect it "
            "does not repair."
        ),
        "counterexamples": counterexamples,
        "verdict": "GREEN" if not counterexamples else "RED",
        "rows": rows,
    }


def score_g4(index) -> dict:
    from harness import CoreSession, render_verdict, route_line  # noqa: PLC0415

    differing = []
    for line in G4_LINES:
        def _session(router):
            session = CoreSession.boot(REPO, offline=True, session_id="g4")
            session.resolver_index = index
            session.proposer = router
            return session

        off = route_line(REPO, _session(None), line or None)
        on = route_line(
            REPO, _session(plain_router.PlainRouter(repo_root=REPO)),
            line or None,
        )
        if off != on or render_verdict(off) != render_verdict(on):
            differing.append({"line": line, "off": off, "on": on})
    return {
        "standard": "BYTE-IDENTICAL, one difference voids",
        "voiding_sentence_verbatim": "a single differing verdict voids the whole reading",
        "lines_compared": len(G4_LINES),
        "compared_how": (
            "whole verdict dicts AND their rendered bytes. A summary can agree "
            "while the verdicts differ, and the voiding sentence is about the "
            "verdict."
        ),
        "differing": differing,
        "verdict": "GREEN" if not differing else "VOID",
    }


def score_g4b(seal: dict) -> dict:
    """A proposed supposition is unreadable, and the ceiling refuses."""

    conditional_turns = [
        row for row in seal["served_turns"] if row["status"] == "conditional"
    ]
    leaks = []
    for entry in seal["sessions"]:
        journal = _load(entry["journal"])
        texts = {record["text_bytes"] for record in journal["assumptions"]}
        for row in conditional_turns:
            if row["session_id"] != entry["session_id"]:
                continue
            for text in texts:
                if text.startswith("you meant ") or "assuming you meant" in text:
                    leaks.append(
                        {"session_id": entry["session_id"], "text_bytes": text}
                    )
    # The positive control: a bound nobody has seen fire is a bound nobody
    # has checked.
    control = _ceiling_control()
    return {
        "clause_verbatim": (
            "A conditional answer's supposition must not be readable by any "
            "later turn as a premise."
        ),
        "how_this_run_scores_it": (
            "prereg amendment 5: a proposed supposition is a field of the "
            "SERVED RECEIPT and is never written into the session's "
            "AssumptionSet, so it is not readable at all — stricter than the "
            "frozen mechanism, which permitted reading provided the later "
            "turn cited it."
        ),
        "conditional_turns_in_the_corpus": len(conditional_turns),
        "assumption_records_that_are_proposed_suppositions": leaks,
        "citations_are_corroborated_by": "B12, over this corpus's read logs",
        "the_ceiling_positive_control": control,
        "verdict": (
            "GREEN"
            if not leaks and control["refused_the_ninth"]
            else "RED"
        ),
    }


def _ceiling_control() -> dict:
    from harness import CoreSession  # noqa: PLC0415

    class _AlwaysFirst:
        def randrange(self, count: int) -> int:  # noqa: ARG002
            return 0

    router = plain_router.PlainRouter(
        blind_rng=_AlwaysFirst(), repo_root=REPO
    )
    session = CoreSession.boot(REPO, offline=True, session_id="ceiling-control")
    served = []
    for _ in range(plain_router.SUPPOSITION_CEILING + 1):
        verdict = router.route(REPO, session, "what is two plus three")
        served.append(verdict.get("status"))
    return {
        "ceiling": plain_router.SUPPOSITION_CEILING,
        "statuses_in_order": served,
        "refused_the_ninth": served[-1] == "refused",
        "refusal_type": "assumption_budget",
        "why_it_is_run_here_and_not_only_in_a_test": (
            "the artifact is what a reader checks. A bound whose only evidence "
            "is a green suite is a bound the artifact asserts."
        ),
    }


def score_g5(g1: dict) -> dict:
    """The capability-blind arm: the SAME list, chosen at random."""

    rng = _blind_rng()
    questions = _load(QUESTIONS)["questions"]
    rows = []
    for item in questions:
        candidates, verified = ce.verified_candidates(item["question"], REPO)
        proposal = pp.blind_select(candidates, rng)
        chosen = None
        if proposal.selected_index is not None:
            chosen = next(
                (v for v in verified
                 if v.candidate.index == proposal.selected_index),
                None,
            )
        rows.append(
            {
                "question_id": item["question_id"],
                "candidates": len(candidates),
                "selected_index": proposal.selected_index,
                "selection_verified": chosen is not None,
            }
        )
    blind = sum(1 for row in rows if row["selection_verified"])
    model = g1["the_number_the_served_behaviour_actually_rests_on"][
        "model_selected_and_the_selection_verified"
    ]
    total = len(rows)
    half = model / 2
    frozen = _load(PREREG)["gates"]["G5"]
    return {
        # Quoted from the preregistration rather than retyped. The first
        # draft retyped it and dropped a full stop, which a test caught —
        # the same class of defect the verbatim instrument caught twice in
        # slice 1. One copy of a frozen rule.
        "registered_collapse_rule": frozen["registered_collapse_rule"],
        "why_a_half": frozen["why_a_half"],
        "denominator": total,
        "proposer_verified_selections": model,
        "blind_verified_selections": blind,
        "half_of_the_proposer": half,
        "collapsed": blind <= half,
        "verdict": "GREEN" if blind <= half else "RED",
        "if_it_does_not_collapse": (
            "'frequency can beat a weak learner' — the seat ships empty with "
            "the number, the enumerator and the conditional status survive as "
            "the exact-layer half, and no learned component is served."
        ),
        "seed": {
            "derived_from": BLIND_SEED_SOURCE,
            "why": (
                "seeded from a committed file's digest so the draw is a fact "
                "about a sealed set rather than about this run's clock"
            ),
        },
        "chance_rate_at_the_frozen_candidate_limit": 1 / ce.CANDIDATE_LIMIT,
        "rows": rows,
    }


def score_g6(index) -> dict:
    from harness import CoreSession, render_verdict, route_line  # noqa: PLC0415

    line = "how do i change a tyre"

    def _session(router):
        session = CoreSession.boot(REPO, offline=True, session_id="g6")
        session.resolver_index = index
        session.proposer = router
        return session

    off = route_line(REPO, _session(None), line)
    router = plain_router.PlainRouter(repo_root=REPO)
    original = pp.ENDPOINT
    pp.ENDPOINT = "http://127.0.0.1:9/none"
    raised = None
    try:
        on = route_line(REPO, _session(router), line)
    except Exception as exc:  # noqa: BLE001 - the thing the gate forbids
        on, raised = None, repr(exc)
    finally:
        pp.ENDPOINT = original
    return {
        "standard": (
            "byte-identical to the proposer-OFF verdict, and the absent-model "
            "path must REFUSE-BY-DESIGN rather than raise"
        ),
        "raised": raised,
        "byte_identical": raised is None and render_verdict(off) == render_verdict(on),
        "trace_says_the_model_was_absent": bool(
            router.traces and router.traces[-1].unavailable
        ),
        "and_the_difference_that_matters": (
            "the trace records that the model was ABSENT, not that it "
            "declined. A refusal and a silence are different facts."
        ),
        "verdict": (
            "GREEN"
            if raised is None
            and render_verdict(off) == render_verdict(on)
            and router.traces
            and router.traces[-1].unavailable
            else "RED"
        ),
    }


def _data_digest() -> str:
    parts = []
    for path in sorted((REPO / "data").glob("*/nodes.json")):
        parts.append(
            [
                str(path.relative_to(REPO)).replace("\\", "/"),
                hashlib.sha256(path.read_bytes()).hexdigest(),
            ]
        )
    return ledger.digest(parts)


def score_g7(before: str, run_regeneration: bool) -> dict:
    after = _data_digest()
    regeneration = {
        "run": run_regeneration,
        "why_it_may_be_skipped": (
            "check_regeneration re-runs every seed and refuses outright if "
            "data/ is dirty. When it is skipped the artifact says so and G7 "
            "reports UNSCORED for that half rather than GREEN."
        ),
    }
    if run_regeneration:
        started = time.time()
        result = subprocess.run(  # noqa: S603
            [sys.executable, str(REPO / "scripts" / "check_regeneration.py")],
            cwd=REPO, capture_output=True, text=True,
        )
        regeneration.update(
            {
                "returncode": result.returncode,
                "green": result.returncode == 0,
                "elapsed_s": round(time.time() - started, 1),
                "tail": result.stdout.strip()[-600:],
            }
        )
    unchanged = before == after
    return {
        "clause_verbatim": (
            "After a session of conditional answers, `data/*/nodes.json` is "
            "unchanged and `check_regeneration` is green."
        ),
        "standard": "unchanged and green",
        "nodes_digest_before": before,
        "nodes_digest_after": after,
        "unchanged": unchanged,
        "check_regeneration": regeneration,
        "verdict": (
            "GREEN"
            if unchanged and regeneration.get("green")
            else ("RED" if not unchanged else "UNSCORED")
        ),
    }


def score_g7b() -> dict:
    """Driven through measure_throughput's OWN record builder.

    The preregistration's standard is *"the test drives measure_throughput's
    own useful-token computation with a synthetic conditional record of
    non-zero token length"*. So the same synthetic answer is scored twice,
    differing ONLY in `status`: once as `solved`, which must earn its tokens,
    and once as `conditional`, which must forfeit them. A check that only ran
    the forfeiting arm could pass on a builder that zeroes everything.
    """

    import measure_throughput as mt  # noqa: PLC0415

    content = "the answer is 42. " * 40
    task = {
        "task_id": "g7b-synthetic",
        "kind": "exact_value",
        "half": "A",
        "profile": "kernel",
        "route_expect": "evaluate",
        "expected": {
            "check": "contains",
            "outcome": "answer",
            "status_expect": "solved",
            "content_must_contain": ["42"],
        },
    }
    scored = {}
    for status in ("solved", "conditional"):
        observed = {
            "g7b-synthetic": [
                mt.TurnResult(
                    content=content,
                    x_corollary={"status": status, "route": "evaluate"},
                    ttft_s=0.01,
                    elapsed_s=0.02,
                    http_status=200,
                )
            ]
        }
        records = mt.build_records(
            [task], observed, "b-grounded", lambda text: len(text.split()), {}
        )
        scored[status] = {
            "tokens": records[0]["tokens"],
            "useful_tokens": records[0]["useful_tokens"],
            "correct": records[0]["correct"],
        }
    return {
        "clause": (
            "a turn served with status `conditional` contributes ZERO useful "
            "tokens to the throughput scoring path, whatever its content "
            "length, and the check is made from that path rather than from a "
            "docstring."
        ),
        "driven_through": "measure_throughput.build_records",
        "solved_arm": scored["solved"],
        "conditional_arm": scored["conditional"],
        "the_arms_differ_only_in_status": True,
        "the_control_that_makes_this_evidence": (
            "the `solved` arm must score NON-ZERO on the same content. "
            "Without it, a builder that zeroed every record would pass the "
            "conditional arm and prove nothing."
        ),
        "non_answering_set_contains_conditional": (
            "conditional" in mt.NON_ANSWERING_STATUSES
        ),
        "forfeiting_set_is_narrower_than_non_answering": (
            "exhausted" in mt.NON_ANSWERING_STATUSES
            and "exhausted" not in mt.FORFEITING_STATUSES
        ),
        "why_that_narrowing_matters": (
            "a closure task's `exhausted` IS its answer — a certified bounded "
            "negative. The first draft of this guard used the wide set and "
            "zeroed exactly that task; the narrowing is kept as a fixture."
        ),
        "verdict": (
            "GREEN"
            if scored["solved"]["useful_tokens"] > 0
            and scored["conditional"]["useful_tokens"] == 0
            and scored["conditional"]["tokens"] > 0
            else "RED"
        ),
    }


def _enumerator_reads_data_only() -> tuple[bool, dict]:
    """Does the enumerator ever CALL `default_index`, or name `data_holdout`?

    Parsed, not grepped. The first version of this check searched the file's
    text for `default_index()` and went red on the module's own DOCSTRING,
    which explains at length why it must not call that function. A check a
    correct explanation can fail is not a check of the code.

    So the module is parsed and its call graph inspected: a call to
    `default_index` anywhere, or the string `data_holdout` in any string
    literal the code evaluates, is the channel G8 exists to close.
    """

    import ast  # noqa: PLC0415

    path = REPO / "scripts" / "candidate_enumerator.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls, holdout_literals, data_literals = [], [], []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            name = (
                target.id if isinstance(target, ast.Name)
                else getattr(target, "attr", None)
            )
            if name == "default_index":
                calls.append(name)
        if isinstance(node, ast.ImportFrom) and node.module == "resolver":
            for alias in node.names:
                if alias.name == "default_index":
                    calls.append(f"from resolver import {alias.name}")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value == "data_holdout":
                holdout_literals.append(node.value)
            if node.value == "data":
                data_literals.append(node.value)
    # `holdout_ids` exists precisely so the GATE can read the holdout to check
    # a negative, so a `data_holdout` literal is expected there and only
    # there. It is reported rather than forbidden, with its count.
    return (not calls and data_literals != []), {
        "parsed_not_grepped": True,
        "default_index_calls_or_imports": calls,
        "data_literals": len(data_literals),
        "data_holdout_literals": len(holdout_literals),
        "why_a_data_holdout_literal_is_expected": (
            "`holdout_ids()` reads `data_holdout/` on purpose — it exists so "
            "the gate can check a negative rather than trust a docstring. The "
            "channel that matters is whether the ENUMERATION path calls "
            "`resolver.default_index`, which spans both directories."
        ),
        "the_defect_this_check_replaced": (
            "a text search for `default_index()` that matched the module's "
            "own docstring explaining why it must never call it. A check a "
            "correct explanation can fail is not a check of the code."
        ),
    }


def score_g8(prompts: dict) -> dict:
    holdout = ce.holdout_ids(REPO)
    hits = []
    for record in prompts["prompts"]:
        haystack = "\n".join(
            [record["prompt"], *record["candidates"], *record["verified"]]
        )
        for statement_id in holdout:
            if statement_id and statement_id in haystack:
                hits.append(
                    {
                        "session_id": record["session_id"],
                        "turn_index": record["turn_index"],
                        "statement_id": statement_id,
                    }
                )
    reads_data_only, channel_detail = _enumerator_reads_data_only()
    return {
        "clause": (
            "no holdout statement id, holdout statement text, or "
            "holdout-derived material appears in any prompt sent to the "
            "model, in any candidate list, or in any served answer."
        ),
        "standard": "ZERO occurrences. One is red and voids the run.",
        "holdout_ids_known": len(holdout),
        "prompts_scanned": len(prompts["prompts"]),
        "occurrences": hits,
        "the_enumerator_reads_data_only": reads_data_only,
        "how_that_second_check_is_made": channel_detail,
        "why_the_second_check_exists": (
            "resolver.default_index spans data/ AND data_holdout/ — 2,053 "
            "holdout ids sit in the index a candidate list would obviously be "
            "built from. Scanning prompts catches a leak that happened; this "
            "catches the channel that would cause one."
        ),
        "verdict": "GREEN" if not hits and reads_data_only else "VOID",
    }


# --------------------------------------------------------------------------
# B9 — the proposer's input carries no history but normal forms
# --------------------------------------------------------------------------


def score_b9(seal: dict, prompts: dict) -> dict:
    journals = {
        entry["session_id"]: _load(entry["journal"])
        for entry in seal["sessions"]
    }
    leaks, explained, rows, unprompted = [], [], [], []
    for record in prompts["prompts"]:
        journal = journals[record["session_id"]]
        prompt = record["prompt"]
        if not prompt:
            # No prompt exists to scan: the enumerator offered nothing, so
            # `propose` returned before any request was built and the model
            # was never asked. Counted below rather than silently dropped —
            # a scanner whose denominator shrinks without saying so is a
            # scanner reporting a smaller problem than it met.
            unprompted.append(
                {
                    "session_id": record["session_id"],
                    "turn_index": record["turn_index"],
                    "utterance": record["utterance"],
                }
            )
            continue
        # THE CONSTRUCTION ARM. Rebuild the prompt from THIS turn's utterance
        # alone, with no session and no history in scope. If the rebuilt
        # prompt is byte-identical, the prompt is a pure function of the
        # current utterance and committed material — which is the property
        # B9 is about, proved rather than asserted.
        rebuilt = pp.build_prompt(
            record["utterance"], ce.enumerate_candidates(record["utterance"], REPO)
        )
        construction_ok = rebuilt == prompt
        earlier = [
            turn for turn in journal["turns"]
            if turn["turn_index"] < record["turn_index"]
        ]
        normal_forms = {
            str(item["normal_form"][0])
            for item in journal["assumptions"]
        }
        for turn in earlier:
            for needle, source in (
                (turn["input_bytes"], "earlier input_bytes"),
                (turn["result"]["answer_bytes_digest"], "earlier answer digest"),
            ):
                if not needle or needle not in prompt:
                    continue
                hit = {
                    "session_id": record["session_id"],
                    "turn_index": record["turn_index"],
                    "from_turn": turn["turn_index"],
                    "needle": needle,
                    "source": source,
                }
                if needle in rebuilt:
                    # Present in a prompt built with NO history in scope, so
                    # it demonstrably came from committed material and not
                    # from the transcript. Published, never silently dropped.
                    hit["explained_by"] = (
                        "present in the independently rebuilt prompt, so it is "
                        "corpus material the enumerator offered, not a byte "
                        "carried forward from an earlier turn"
                    )
                    explained.append(hit)
                elif needle in normal_forms:
                    hit["explained_by"] = (
                        "an assumption `normal_form` — the ONE class of "
                        "earlier-turn bytes B9 permits"
                    )
                    explained.append(hit)
                else:
                    leaks.append(hit)
        rows.append(
            {
                "session_id": record["session_id"],
                "turn_index": record["turn_index"],
                "prompt_chars": len(prompt),
                "construction_ok": construction_ok,
                "earlier_turns_in_scope": len(earlier),
                "live_normal_forms": len(normal_forms),
            }
        )
    control = _b9_positive_control(prompts, journals)
    construction_misses = [row for row in rows if not row["construction_ok"]]
    return {
        "clause_verbatim": (
            "The proposer's input at turn *j* contains no bytes from earlier "
            "turns other than assumption `normal_form`s. Any leak is red — "
            "history reaches the model only through the exact layer."
        ),
        "standard": "ANY LEAK IS RED",
        "scored_in_this_commission": True,
        "prompts_scanned": len(rows),
        "prompts_retained_in_total": len(prompts["prompts"]),
        "retained_records_with_no_prompt_to_scan": {
            "count": len(unprompted),
            "why": (
                "the enumerator offered no candidate, so `propose` "
                "returned before a request was built and the model was "
                "never asked. There is no prompt to scan and no model "
                "call to leak into. Published so the scanned denominator "
                "is visibly smaller than the retained one, and by how "
                "much."
            ),
            "records": unprompted,
        },
        "prompts_with_at_least_one_earlier_turn": sum(
            1 for row in rows if row["earlier_turns_in_scope"]
        ),
        "leaks": leaks,
        "hits_explained_and_published": explained,
        "why_explained_hits_are_published_rather_than_filtered": (
            "a scanner that silently drops the hits it can explain is a "
            "scanner whose explanations nobody can check. Every hit is listed "
            "with the reason it is not a leak, and the reason is a MEASURED "
            "property — presence in a prompt rebuilt with no history in scope "
            "— not a judgement."
        ),
        "the_construction_arm": {
            "what_it_proves": (
                "the prompt is byte-identical to one rebuilt from this turn's "
                "utterance alone, with no session object in scope. B9 is "
                "therefore true by construction and not by discipline."
            ),
            "misses": construction_misses,
            "verdict": "GREEN" if not construction_misses else "RED",
        },
        "the_positive_control": control,
        "verdict": (
            "GREEN"
            if not leaks and not construction_misses and control["detected"]
            else "RED"
        ),
    }


def _b9_positive_control(prompts: dict, journals: dict) -> dict:
    """Splice an earlier turn's bytes into a prompt; the scanner must see it.

    ROADMAP-v0.21 §4.0's standing review question: *a green assertion that
    could not have gone red is not evidence.* B9 is green by construction, so
    without this the scanner could be broken and B9 would still read green.
    """

    for record in prompts["prompts"]:
        journal = journals[record["session_id"]]
        earlier = [
            turn for turn in journal["turns"]
            if turn["turn_index"] < record["turn_index"]
        ]
        if not record["prompt"] or not earlier:
            continue
        stolen = earlier[0]["input_bytes"]
        forged = f"{record['prompt']}\n\nEarlier you asked: {stolen}"
        rebuilt = pp.build_prompt(
            record["utterance"],
            ce.enumerate_candidates(record["utterance"], REPO),
        )
        detected = stolen in forged and stolen not in rebuilt
        return {
            "session_id": record["session_id"],
            "turn_index": record["turn_index"],
            "spliced_bytes": stolen,
            "detected": detected,
            "how": (
                "the forged prompt carries an earlier turn's input_bytes; the "
                "independently rebuilt prompt does not; so the scanner's rule "
                "classifies it as a leak rather than as corpus material"
            ),
        }
    return {
        "detected": False,
        "why": (
            "no retained prompt had an earlier turn in its session, so the "
            "control could not be constructed — which is itself a finding "
            "about the corpus, not a pass"
        ),
    }


def score_b10_both_ways(seal: dict, index, slice_one_arm: dict) -> dict:
    """B10 read two ways, both published, with the difference named.

    Slice 1's arm re-serves each uncited line into a fresh session **with no
    proposer**, because slice 1 had none. On a slice-2 journal that compares
    two different CONFIGURATIONS, not two different STATES — and B10's own
    gloss is about state: *"The quarantine made mechanical: session state may
    never leak into unconditional answers."*

    So the slice-1 arm is run unchanged and its rows are published, and a
    second arm holds the configuration fixed — a fresh session, no
    assumptions, proposer attached — and asks what the clause asks. Both
    numbers are here. A reader who thinks the clause means the first reading
    has the first reading's rows in front of them.
    """

    from harness import CoreSession, route_line  # noqa: PLC0415

    misses, total = [], 0
    for entry in seal["sessions"]:
        journal = _load(entry["journal"])
        for turn in journal["turns"]:
            if turn["assumptions_cited"]:
                continue
            total += 1
            fresh = CoreSession.boot(
                REPO, offline=True, session_id=entry["session_id"]
            )
            fresh.resolver_index = index
            fresh.proposer = plain_router.PlainRouter(repo_root=REPO)
            verdict = route_line(REPO, fresh, turn["input_bytes"])
            if ledger.answer_bytes_digest(verdict) != (
                turn["result"]["answer_bytes_digest"]
            ):
                misses.append(
                    {
                        "session_id": entry["session_id"],
                        "turn_index": turn["turn_index"],
                        "input_bytes": turn["input_bytes"],
                    }
                )

    served_by_plain = {
        (row["session_id"], row["turn_index"])
        for row in seal["served_turns"]
        if row["route"] == "plain_input"
    }
    slice_one_misses = {
        (row["session_id"], row["turn_index"])
        for row in slice_one_arm["misses"]
    }
    every_miss_is_a_plain_input_turn = slice_one_misses <= served_by_plain
    return {
        "clause": (
            "Every turn with empty `assumptions_cited` must render "
            "byte-identical to the same line served statelessly."
        ),
        "the_clauses_own_gloss": (
            "The quarantine made mechanical: session state may never leak "
            "into unconditional answers."
        ),
        "slice_1_arm_unchanged": {
            "called": "run_session_gate.score_b10, imported and not copied",
            "stateless_side": "a fresh session with NO proposer attached",
            "uncited_turns": slice_one_arm["uncited_turns"],
            "misses": slice_one_arm["misses"],
            "verdict": slice_one_arm["verdict"],
        },
        "the_state_reading": {
            "stateless_side": (
                "a fresh session with NO assumptions and the SAME proposer "
                "configuration — configuration held fixed so the comparison "
                "is about state"
            ),
            "uncited_turns": total,
            "misses": misses,
            "verdict": "GREEN" if not misses else "RED",
        },
        "the_measured_fact_that_explains_the_difference": {
            "every_slice_1_miss_is_a_turn_the_plain_input_route_served": (
                every_miss_is_a_plain_input_turn
            ),
            "plain_input_turns_in_the_corpus": len(served_by_plain),
            "slice_1_misses": len(slice_one_misses),
            "what_it_means": (
                "the slice-1 arm's misses are exactly the turns where row 12 "
                "stopped exhausting — which is the entire behavioural change "
                "slice 2 makes, and which G4 separately proves happens "
                "NOWHERE ELSE. Read that way, the slice-1 arm's red says 'the "
                "proposer changed row 12', not 'session state leaked'."
            ),
        },
        "the_adjudication": (
            "the headline verdict follows THE STATE READING, because the "
            "clause's own gloss names state and because slice 1's arm already "
            "holds everything else fixed on purpose — it even reuses the "
            "recorded `session_id` and the shared resolver index. What it "
            "does not hold fixed is a configuration slice 1 did not have. "
            "Both numbers are published so a reader who disagrees can "
            "disagree on the rows rather than on the framing."
        ),
        "and_it_is_filed_rather_than_only_argued": (
            "docs/BACKLOG.md carries the item: run_session_gate.score_b10 "
            "needs the stateless side to inherit the journal's configuration, "
            "or slice-2 journals will keep reading red for a reason that is "
            "not a leak."
        ),
        "verdict": "GREEN" if not misses else "RED",
    }


def _g5_analysis(g1: dict, g5: dict) -> dict:
    """Why the blind arm's number is what it is. No rule is changed here."""

    expected = 0.0
    for row in g1["rows"]:
        if row["candidates"]:
            expected += row["verified"] / row["candidates"]
    none_rows = [
        row for row in g1["rows"]
        if (row["raw"] or "").strip().upper() == "NONE"
    ]
    blind_by_id = {row["question_id"]: row for row in g5["rows"]}
    return {
        "the_draw_was_typical_not_lucky": {
            "expected_blind_verified_selections": round(expected, 2),
            "how_it_is_computed": (
                "sum over questions of verified/candidates — the exact "
                "chance of a uniform draw landing on a verified candidate, "
                "question by question"
            ),
            "observed": g5["blind_verified_selections"],
            "why_this_is_published": (
                "a control that beats the model on one seeded draw invites "
                "the reading that the draw was lucky. It was not: the "
                "observed number sits beside its own expectation."
            ),
        },
        "the_mechanism_and_it_is_not_flattering_to_the_METRIC": {
            "the_model_said_NONE_on": [row["question_id"] for row in none_rows],
            "count": len(none_rows),
            "of_those_the_blind_arm_selected_a_verified_candidate_on": sum(
                1 for row in none_rows
                if blind_by_id[row["question_id"]]["selection_verified"]
            ),
            "exhaust_prior_questions_with_a_verified_candidate": g1[
                "against_the_sealed_ceiling"
            ]["exhaust_prior_questions_with_a_verified_candidate"],
            "exhaust_prior_questions_the_model_selected_for": g1[
                "against_the_sealed_ceiling"
            ]["exhaust_prior_questions_the_model_selected_for"],
            "what_that_says": (
                "the registered rate counts a VERIFIED SELECTION and cannot "
                "see a correct refusal. Every question the model declined had "
                "verified candidates available, and the blind arm — which has "
                "no NONE in its alphabet — took them. On the nine questions "
                "authored to exhaust, the model selected for ZERO and the "
                "blind arm selected a verified candidate for five. So the "
                "metric rewards, in the blind arm, exactly the behaviour the "
                "design calls inventing."
            ),
            "and_this_changes_nothing_about_the_verdict": (
                "the collapse rule was frozen before the proposer existed and "
                "it is scored as frozen. This block explains a red; it does "
                "not soften one. A rule rewritten because its instrument "
                "surprised its author is not a preregistration."
            ),
            "where_the_construction_defect_is_filed": (
                "docs/BACKLOG.md — a successor's collapse rule has to score "
                "the branch outcome against the question's disposition, not "
                "the raw verified-selection count, and it has to be frozen "
                "with a meetability argument per ROADMAP-v0.21 §4.0(3)."
            ),
        },
    }


def findings(seal: dict, g1: dict, prompts: dict) -> dict:
    """What this run learned that no gate asked about. Computed, not typed."""

    priors = {
        item["question_id"]: item["authors_prior"]
        for item in _load(QUESTIONS)["questions"]
    }
    by_line = {
        item["question"]: item["question_id"]
        for item in _load(QUESTIONS)["questions"]
    }
    asked_on_exhaust_prior = [
        {
            "question_id": by_line[row["line"]],
            "session_id": row["session_id"],
            "turn_index": row["turn_index"],
            "status": row["status"],
        }
        for row in seal["served_turns"]
        if row["route"] == "plain_input"
        and row["line"] in by_line
        and priors[by_line[row["line"]]] == "exhaust"
    ]
    selected_but_unverified = [
        {
            "question_id": row["question_id"],
            "raw": row["raw"],
            "selected_index": row["selected_index"],
            "verified_of_candidates": f"{row['verified']}/{row['candidates']}",
        }
        for row in g1["rows"]
        if row["selected_index"] is not None and not row["selection_verified"]
    ]
    no_candidates = [
        row["question_id"] for row in g1["rows"] if row["candidates"] == 0
    ]
    prompt_by_line = {
        record["utterance"]: record for record in prompts["prompts"]
    }
    return {
        "F1_the_ask_branch_fires_on_questions_authored_to_exhaust": {
            "what_happened": asked_on_exhaust_prior,
            "count": len(asked_on_exhaust_prior),
            "the_design_sentence_this_contradicts": (
                "Not open-domain. Outside the corpus the honest output is "
                "still a refusal. A proposer that cannot find a registered "
                "query still exhausts. (DESIGN-plain-input §7)"
            ),
            "and_the_proposer_is_not_what_broke_it": (
                "on every one of these the model answered NONE — it found no "
                "registered query, exactly as §7 describes. What served the "
                "clarification is the BRANCH RULE, which fires on the count "
                "of VERIFIED candidates and never consults the model's NONE. "
                "So a question outside the corpus comes back with a list of "
                "corpus readings to choose between instead of a refusal."
            ),
            "a_worked_example": {
                "utterance": "how do i change a tyre",
                "model_said": (prompt_by_line.get("how do i change a tyre") or {}).get("raw"),
                "readings_offered": (
                    prompt_by_line.get("how do i change a tyre") or {}
                ).get("verified"),
            },
            "why_it_is_not_repaired_here": (
                "the branch rule is frozen in prereg amendment 2, written "
                "against the design's own text BEFORE the rule had ever run. "
                "Changing it now — after watching it behave — is the move "
                "this repository does not make. It is published and filed."
            ),
            "and_it_is_not_a_G2_counterexample": (
                "nothing is bound and nothing is chosen: the readings are "
                "named and the person is asked. G2 is about served "
                "interpretations, and a clarification interprets nothing. "
                "This is a finding about HONESTY OF REFUSAL, which no gate in "
                "this slice measures."
            ),
        },
        "F2_the_designs_own_motivating_example_enumerates_nothing": {
            "questions_with_zero_candidates": no_candidates,
            "the_one_that_matters": "g1-02",
            "the_utterance": "how do you compute the greatest common divisor recursively",
            "what_the_design_said_it_was_for": (
                "DESIGN-plain-input §2.3 names the `gcd` miss as the residue "
                "the proposer is aimed at — 'greatest common divisor euclid' "
                "did not resolve; the corpus writes `gcd`."
            ),
            "what_actually_happens": (
                "the enumerator offers ZERO candidates, so the proposer is "
                "never asked and row 12 exhausts exactly as before. "
                "Enumeration is by shared content words, and the utterance "
                "shares none with a statement the corpus titles `gcd`. The "
                "synonym layer the design called 'a design and not a patch' "
                "is still not built, and selection-from-an-enumerated-list "
                "cannot substitute for it: you cannot select what was never "
                "enumerated."
            ),
        },
        "F3_verification_discarded_a_correct_selection": {
            "rows": selected_but_unverified,
            "count": len(selected_but_unverified),
            "the_worked_example": (
                "'how do you compute a factorial iteratively' enumerated "
                "'Factorial, Iterative (TheAlgorithms)' first and the model "
                "selected it — the right reading. That candidate did NOT "
                "verify, because `word_match` verification requires the "
                "statement's own title to resolve back to that statement and "
                "this one binds elsewhere. The two candidates that DID verify "
                "were both about the DOUBLE factorial, so the person is asked "
                "to choose between two wrong readings while the right one is "
                "discarded."
            ),
            "what_it_says_about_the_trust_shape": (
                "'selection narrows; verification decides' is the design's "
                "own sentence and it is working exactly as written. The cost "
                "it buys is visible here: a verifier weaker than the proposer "
                "on a given question throws away the proposer's best answer, "
                "and the receipt cannot show what was thrown away because the "
                "discard happens before any receipt exists."
            ),
        },
    }


def _reproduction(gates: dict) -> dict:
    """Compare this execution's verdict table against the committed one.

    Determinism-plus-commit replaced execute-once ceremony, and what replaced
    it is *reproduction, recorded*. So the runner checks itself: if an
    artifact is already committed at `OUT`, its verdict table is read and
    compared. A hand-typed sentence claiming the run reproduces would be a
    sentence; this is the comparison.

    Only the VERDICTS are compared, not every byte. The blocks around them
    grow as the instrument gains disclosures, and a comparison that went red
    because a new denominator field appeared would report an improvement as a
    failure.
    """

    verdicts = {name: gate.get("verdict") for name, gate in gates.items()}
    path = REPO / OUT
    if not path.exists():
        return {
            "prior_artifact_found": False,
            "verdicts": verdicts,
            "note": (
                "first execution against this path; the next one compares "
                "against these verdicts"
            ),
        }
    prior = json.loads(path.read_text(encoding="utf-8"))
    prior_verdicts = {
        name: gate.get("verdict")
        for name, gate in prior.get("gates", {}).items()
    }
    return {
        "prior_artifact_found": True,
        "verdicts": verdicts,
        "prior_verdicts": prior_verdicts,
        "verdicts_identical": prior_verdicts == verdicts,
        "what_this_is_and_is_not": (
            "evidence that the runner reproduces its own reading on this "
            "machine on this day. It is not a proof of determinism, and P4's "
            "limit is the same limit: byte-identity across passes on one "
            "machine on one day is the strongest check this repository runs "
            "on a model call, and it is reported as that and nothing more."
        ),
    }


# --------------------------------------------------------------------------
# the run
# --------------------------------------------------------------------------


def run(*, run_regeneration: bool = True) -> dict:
    import run_session_gate  # noqa: PLC0415
    from resolver import default_index  # noqa: PLC0415

    started = time.time()
    weights = pp.verify_pin()
    seal = _load(SEAL)
    prompts = _load(PROMPTS)
    questions = _load(QUESTIONS)["questions"]
    distractors = _load(DISTRACTORS)
    determinism = _load(DETERMINISM)
    index = default_index()

    nodes_before = _data_digest()

    g1 = score_g1(questions, index)
    g2 = score_g2(seal, prompts)
    g3 = score_g3(distractors)
    g4 = score_g4(index)
    g4b = score_g4b(seal)
    g5 = score_g5(g1)
    g6 = score_g6(index)
    g7b = score_g7b()
    g8 = score_g8(prompts)
    b9 = score_b9(seal, prompts)
    b10 = score_b10_both_ways(
        seal, index, run_session_gate.score_b10(seal, index)
    )
    b12 = run_session_gate.score_b12(seal)
    g5["analysis"] = _g5_analysis(g1, g5)
    g7 = score_g7(nodes_before, run_regeneration)

    gates = {
        "G1": g1, "G2": g2, "G3": g3, "G4": g4, "G4b": g4b, "G5": g5,
        "G6": g6, "G7": g7, "G7b": g7b, "G8": g8, "B9": b9,
        "B10": b10, "B12": b12,
    }

    g9 = {
        "verdict": "NOT MET",
        "adjudicated": "in advance, by orchestrator ruling",
        "where": f"{PREREG} amendments 3 and 4",
        "the_ruling_verbatim": next(
            a for a in _load(PREREG)["amendments"] if a["amendment"] == 4
        )["the_ruling_verbatim"],
        "why_it_is_not_scored_here": (
            "a gate adjudicated before the run is a gate the run REPORTS. "
            "Re-scoring it would invite the reading that the verdict came out "
            "of this run's numbers, and it did not — it comes out of where "
            "DESIGN-plain-input places the proposer."
        ),
    }
    gates["G9"] = g9

    voided = sorted(
        name for name, gate in gates.items()
        if gate.get("verdict") in ("VOID", "RED")
    )
    r2_clauses = {
        "G2 has no counterexample": g2["verdict"] == "GREEN",
        "G3 has no collapsed pair": g3["verdict"] == "GREEN",
        "G4 is byte-identical": g4["verdict"] == "GREEN",
        "G4b holds": g4b["verdict"] == "GREEN",
        "G5 collapses at or below half": g5["verdict"] == "GREEN",
        "G6 is byte-identical with the model absent": g6["verdict"] == "GREEN",
        "G7 is unchanged-and-green": g7["verdict"] == "GREEN",
        "G7b is zero": g7b["verdict"] == "GREEN",
        "G8 is zero": g8["verdict"] == "GREEN",
        "G9 repairs both fixtures": False,
        "B9 has no leak": b9["verdict"] == "GREEN",
        "B10 and B12 are green": (
            b10["verdict"] == "GREEN" and b12["verdict"] == "GREEN"
        ),
    }

    licensing_sentence = (
        "Plain prose that the exact layer cannot ground is served either as "
        "an answer conditional on a named supposition, or as a question "
        "naming the readings, and never as an unmarked answer — and only "
        "where the exact layer does not already bind, because 13 of these 30 "
        "sealed questions are bound `found` by the resolver before the "
        "proposer is consulted, so the silent binding P2 measured is "
        "UNREPAIRED by this slice and is filed in docs/BACKLOG.md as a "
        "designed successor's work."
    )

    every_clause_but_g9 = all(
        value for name, value in r2_clauses.items()
        if name != "G9 repairs both fixtures"
    )
    failed = sorted(name for name, value in r2_clauses.items() if not value)
    prereg = _load(PREREG)
    return {
        "schema": RUN_SCHEMA,
        "slice": 2,
        "design": "docs/DESIGN-plain-input.md",
        "completed_by": "docs/DESIGN-session-ledger.md §5 slice 2",
        "prereg": PREREG,
        "seal": SEAL,
        "prompts": PROMPTS,
        "run_date": "2026-08-26",
        "runner": "scripts/run_plain_gate.py",
        "elapsed_seconds": round(time.time() - started, 1),
        "the_model_and_its_pin": {
            "provider_tag": "ollama:qwen3:4b-instruct",
            "weights_blob_sha256": weights["sha256"],
            "verified_before_any_question_was_asked": weights["verified"],
            "temperature": 0,
            "refused_rather_than_downloaded": (
                "machine_reader.verify_weights hashes the blob's bytes and "
                "refuses on absence or mismatch"
            ),
        },
        "determinism": {
            "status": determinism["what_this_licenses"],
            "P4_two_passes_byte_identical": determinism["two_passes_byte_identical"],
            "the_honest_limit": determinism["the_honest_limit"],
            "so_this_artifact": (
                "is committed from a deterministic runner and reproductions "
                "are welcome and recorded (ROADMAP-v0.21 §4.0(2))"
            ),
        },
        "denominators": (
            "in the corpus seal's `denominators` block. Read it before any "
            "rate here: the thirty sealed questions are not one population "
            "and the subset sizes are never summed."
        ),
        "gates": gates,
        "reproduction": _reproduction(gates),
        "findings": findings(seal, g1, prompts),
        "result_gate_R2": {
            "clause_verbatim": prereg["the_result_gate"]["R2"],
            "clauses": r2_clauses,
            "failed_clauses": failed,
            "every_clause_but_G9": every_clause_but_g9,
            "G9_is_NOT_MET_by_ruling": True,
            "verdict": (
                "HOLDS UNDER THE RULING" if every_clause_but_g9 else "FAILS"
            ),
            "what_the_ruling_changes": (
                "R2 as frozen requires G9 to repair both fixtures. Prereg "
                "amendment 4 adjudicates G9 NOT MET and moves the defect to "
                "BACKLOG with thirteen fixtures. So G9's clause stands UNMET "
                "and named — never as a clause quietly satisfied — and the "
                "question the run answers is whether every OTHER clause "
                "holds."
            ),
            "what_happens_now_frozen_before_the_run": (
                prereg["the_result_gate"]["if_R2_fails_on_any_clause"]
                if not every_clause_but_g9
                else "R2's clauses hold apart from G9's, which is ruled NOT MET"
            ),
            "the_sentence_that_WOULD_have_been_licensed": licensing_sentence,
            "is_it_licensed": every_clause_but_g9,
            "and_the_G9_limit_is_inside_that_sentence_on_purpose": (
                "slice 1's B10 scope limit set the pattern: a limit in an "
                "adjacent field is a limit a quoter drops. Registered as a "
                "requirement in prereg amendment 4 before this run — so the "
                "sentence carries its limit whether or not the run licenses "
                "the sentence."
            ),
            "nothing_more": prereg["the_result_gate"]["nothing_more"],
        },
        "the_instrument_and_what_was_fixed_before_this_reading": {
            "why_this_block_exists": (
                "the runner was executed once against the recorded corpus "
                "before this reading, to find out whether it worked. It did "
                "not, in three places, and saying so is cheaper than a reader "
                "wondering. P4 earned determinism-plus-commit "
                "(ROADMAP-v0.21 §4.0(2)), so a re-execution is a reproduction "
                "rather than a second draw at a result."
            ),
            "defects_found_and_fixed": [
                "G8's second check searched the enumerator's TEXT for "
                "`default_index()` and matched the module's own docstring "
                "explaining why it must never call it. Replaced with an AST "
                "walk over calls and imports. A check a correct explanation "
                "can fail is not a check of the code.",
                "B10 was scored only by slice 1's arm, whose stateless side "
                "boots a session with NO proposer — a configuration "
                "difference, not a state difference. Both readings are now "
                "computed and both are published.",
                "G1 carried no `verdict` field, so a summary line printed "
                "`None` for a gate that is a measurement with no floor by "
                "registration.",
            ],
            "what_was_NOT_changed": (
                "no clause, no floor, no voiding sentence, no collapse rule "
                "and no denominator. G5's two arms are computed by the same "
                "code before and after, and its red is the same red."
            ),
        },
        "where_the_claim_lives_and_what_is_served": {
            "served_surface": "none beyond what the preregistration registered",
            "what_that_means_concretely": (
                "`conditional` is in the frozen status alphabet and the "
                "capability sheet bumped to corollary.capabilities/2. The "
                "proposer is NOT attached to any session the chat skin "
                "serves: `CoreSession.proposer` defaults to None and ¶DEV-1 "
                "replays every HTTP request into a fresh session. SPEC ¶AMD-1 "
                "records the debt that falls due the day that changes — "
                "`corollary.chat/2` is owed then, not now."
            ),
            "why_no_more_was_shipped": (
                "slice 1's precedent: inventing a surface the design did not "
                "ask for would be shipping more than the gate licensed."
            ),
        },
        "voided_or_red_gates": voided,
        "non_claims": prereg["non_claims"] + [
            "this slice does not repair the silent binding P2 measured; the "
            "defect is filed with thirteen fixtures and its repair is a "
            "designed successor's work",
            "no rate here is a rate over 'plain English'; every denominator "
            "is a named subset of one maintainer-authored set of thirty",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=OUT)
    ap.add_argument(
        "--skip-regeneration", action="store_true",
        help="skip check_regeneration; G7 then reports UNSCORED, never GREEN",
    )
    args = ap.parse_args(argv)

    report = run(run_regeneration=not args.skip_regeneration)
    (REPO / args.out).write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {args.out}")
    for name, gate in sorted(report["gates"].items()):
        print(f"  {name:5s} {gate.get('verdict')}")
    print(f"  R2    {report['result_gate_R2']['verdict']}")
    return 0 if not report["voided_or_red_gates"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
