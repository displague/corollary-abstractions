#!/usr/bin/env python3
"""Slice 2's corpus — the sealed thirty questions, served and written down.

`docs/DESIGN-session-ledger.md` §5 slice 2: *"plain input lands inside the
object. DESIGN-plain-input's proposer, unchanged in trust shape, writes its
resolutions and suppositions into the same journal."* This is the recording
that produces those journals, and its seal is
`experiments/plain_input_corpus_seal.json`.

## Slice 1's protocol, obeyed rather than restated

Slice 1's recording protocol is frozen in
`experiments/session_ledger_prereg.json` and this script reads its numbers
from that file: the session-count cap, the turn cap, the live-assumption
cap, the no-write-gate-turn rule and the A/B split rule. The recorder itself
is **unmodified** — `recorder_code_digest` is checked against the digest
slice 1 froze before slice 1 recorded, and a mismatch stops this script. A
slice that quietly edits the recorder and records under the old protocol's
name is the exact thing that digest exists to prevent.

Slice 1's own seal is **closed**. Nothing here touches `v021-s*`; this
corpus lives under `v021-p*` and gets its own dated seal.

## What is authored, and why the authoring is a counter rather than a choice

**Part 1 — the sealed questions, in sealed order, six sessions of five.**
`experiments/plain_question_set.json` was committed before the proposer, the
enumerator and any model call. Chunking it by a counter means no question
was placed to make a session read well, and every question appears exactly
once. Part 1 is the denominator for every served-behaviour count.

**Part 2 — two assumption-bearing sessions.** B9's clause permits one class
of earlier-turn bytes to reach the proposer — assumption `normal_form`s —
and a corpus with no live assumptions could not tell a permitted carve-out
from an empty one. So two sessions interleave `suppose` declarations, a
retraction and computation turns with plain questions drawn from the same
sealed set by a stated rule (every sixth question from index 0, and every
sixth from index 5). **Those questions are REPEATS** and are excluded from
the served-behaviour denominator; they count only toward B9, B10 and B12.

## The header pin slice 1 left empty

§3's SessionHeader lists `proposer_model_digest` as *"slice 2 only, key
omitted until then, omission meaning 'no proposer served'"*. Slice 1's
headers omit it. These carry it, and its value is the weights blob's
**measured** sha256 — `plain_proposer.verify_pin` calls
`machine_reader.verify_weights`, which hashes the blob's bytes and refuses on
absence or mismatch rather than trusting the filename ollama gave it.

## Determinism

`created_utc` comes from this module, not the clock; session ids come from a
counter; the resolver index is built once and shared, for the reason
`serve_chat.ChatEngine.prewarm` states. The proposer arm earned
**determinism-plus-commit** in P4 (`experiments/plain_proposer_determinism.json`:
two passes, byte-identical), so ROADMAP-v0.21 §4.0(2) applies and
reproductions are welcome and recorded. The honest limit P4 states travels
with it: byte-identity across two passes on one machine on one day is not a
proof of determinism.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

import session_ledger as ledger  # noqa: E402
from session_recorder import SessionRecorder, recorder_code_digest  # noqa: E402

LEDGER_PREREG = "experiments/session_ledger_prereg.json"
PLAIN_PREREG = "experiments/plain_input_prereg.json"
QUESTION_SET = "experiments/plain_question_set.json"
SEAL = "experiments/plain_input_corpus_seal.json"
PROMPTS = "experiments/plain_input_prompts.json"
SEAL_SCHEMA = "corollary.plain-input-corpus-seal/1"
PROMPTS_SCHEMA = "corollary.plain-input-prompts/1"

#: From the protocol, not the clock. A distinct date from slice 1's
#: 2026-08-25 because this is a distinct corpus, not a re-recording.
CREATED_UTC = "2026-08-26T00:00:00Z"

#: Part 1: six sessions of five, in the sealed order.
PART_ONE_SESSIONS = 6
PART_ONE_TURNS = 5


def part_two_lines(questions: list[dict]) -> dict[str, tuple[str, ...]]:
    """The two assumption-bearing sessions, from a stated rule.

    Every plain line here is a question the sealed set already carries, taken
    at a stride rather than picked: session 7 takes indices 0, 6, 12, 18, 24
    and session 8 takes 5, 11, 17, 23, 29. The `suppose`, `retract` and
    arithmetic lines around them exist so the corpus contains turns that CITE
    an assumption, turns that do not, and a lifecycle — which is what B9's
    carve-out, B10's fence and B12's corroboration each need to have anything
    to bite on.
    """

    text = [item["question"] for item in questions]
    return {
        "v021-p07": (
            "suppose x = 5",
            text[0],
            "x ^ 2",
            text[6],
            "suppose y = 3",
            text[12],
            "x + y",
            text[18],
            text[24],
        ),
        "v021-p08": (
            "suppose n = 7",
            text[5],
            "n ^ 2",
            text[11],
            "retract a001",
            "n ^ 2",
            text[17],
            text[23],
            text[29],
        ),
    }


def session_plan(questions: list[dict]) -> list[dict]:
    """Every session's id, part and lines. Deterministic, counter-driven."""

    plan: list[dict] = []
    for position in range(PART_ONE_SESSIONS):
        chunk = questions[
            position * PART_ONE_TURNS : (position + 1) * PART_ONE_TURNS
        ]
        plan.append(
            {
                "session_id": f"v021-p{position + 1:02d}",
                "part": 1,
                "lines": tuple(item["question"] for item in chunk),
                "question_ids": tuple(item["question_id"] for item in chunk),
            }
        )
    by_id = {item["question"]: item["question_id"] for item in questions}
    for session_id, lines in part_two_lines(questions).items():
        plan.append(
            {
                "session_id": session_id,
                "part": 2,
                "lines": lines,
                "question_ids": tuple(
                    by_id[line] for line in lines if line in by_id
                ),
            }
        )
    return plan


def _protocol(repo_root: Path) -> dict:
    prereg = json.loads(
        (repo_root / LEDGER_PREREG).read_text(encoding="utf-8")
    )
    protocol = prereg["recording_protocol"]
    amendment = prereg["amendments"][0]
    return {
        "inherited_from": LEDGER_PREREG,
        "session_count_cap": protocol["session_count_cap"],
        "turn_cap_per_session": protocol["turn_cap_per_session"],
        "live_assumption_cap": protocol["live_assumption_cap"],
        "ab_split_rule": protocol["ab_split_rule"],
        "session_id_rule": (
            "`v021-p{NN}`, in order from a counter. A distinct namespace from "
            "slice 1's `v021-s{NN}`, whose seal is CLOSED and whose journals "
            "this recording never touches."
        ),
        "no_write_gate_turn_rule": protocol.get(
            "no_write_gate_turn_rule",
            "a recorded session contains no corpus-mutating line; a session "
            "that acquires one is excluded whole, the exclusion counted and "
            "published",
        ),
        "recorder_code_digest": amendment["adds"]["recorder_code_digest"],
    }


def record(repo_root: Path) -> tuple[dict, dict]:
    """Record the corpus. Returns (seal, prompts_artifact)."""

    import plain_proposer as pp  # noqa: PLC0415
    import plain_router  # noqa: PLC0415
    from resolver import default_index  # noqa: PLC0415
    from session_keys import SessionKeyRing  # noqa: PLC0415

    protocol = _protocol(repo_root)
    measured_digest = recorder_code_digest(repo_root)
    if measured_digest != protocol["recorder_code_digest"]:
        raise RuntimeError(
            "the recorder's bytes do not match the digest slice 1's protocol "
            "froze before slice 1 recorded. Slice 2 records under the SAME "
            "recorder or it is not recording under the same protocol"
        )

    # The weights are hashed before any question is asked, and absence or
    # mismatch REFUSES rather than downloads. `machine_reader`'s own
    # discipline, called rather than copied.
    weights = pp.verify_pin()

    questions = json.loads(
        (repo_root / QUESTION_SET).read_text(encoding="utf-8")
    )["questions"]
    plan = session_plan(questions)

    index = default_index()
    keyring = SessionKeyRing.open(repo_root / ".runtime" / "session-keys.json")
    pin_table = None

    sessions: list[dict] = []
    excluded: list[dict] = []
    prompt_records: list[dict] = []
    served: list[dict] = []
    started = time.time()

    for entry in plan:
        session_id = entry["session_id"]
        recorder = SessionRecorder(
            repo_root,
            session_id,
            CREATED_UTC,
            keyring,
            shared_index=index,
            pin_table=pin_table,
        )
        if pin_table is None:
            # §3's slice-2-only pin, added ONCE and then carried, and added
            # BEFORE the first turn because turn 0's `prev_turn_digest` is
            # the header digest.
            recorder.pin_table = {
                **recorder.pin_table,
                "proposer_model_digest": weights["sha256"],
            }
        pin_table = recorder.pin_table

        router = plain_router.PlainRouter(repo_root=repo_root)
        recorder.session.proposer = router

        if len(entry["lines"]) > protocol["turn_cap_per_session"]:
            raise RuntimeError(
                f"{session_id} authors {len(entry['lines'])} turns against a "
                f"frozen cap of {protocol['turn_cap_per_session']}"
            )
        trace_mark = 0
        for turn_index, line in enumerate(entry["lines"]):
            outcome = recorder.turn(line)
            fresh = router.traces[trace_mark:]
            trace_mark = len(router.traces)
            for trace in fresh:
                prompt_records.append(
                    {
                        "session_id": session_id,
                        "turn_index": turn_index,
                        "utterance": trace.utterance,
                        "candidates": [c.line for c in trace.candidates],
                        "verified": [v.candidate.line for v in trace.verified],
                        "prompt": trace.prompt,
                        "raw": trace.raw,
                        "selected_index": trace.selected_index,
                        "discarded_reason": trace.discarded_reason,
                        "branch": trace.branch,
                        "model_unavailable": trace.unavailable,
                    }
                )
            served.append(
                {
                    "session_id": session_id,
                    "part": entry["part"],
                    "turn_index": turn_index,
                    "line": line,
                    "route": outcome.verdict.get("route"),
                    "status": outcome.verdict.get("status"),
                    "proposer_consulted": bool(fresh),
                    "branch": fresh[-1].branch if fresh else None,
                }
            )

        document = recorder.document()
        journal_digest, read_digest = recorder.write(repo_root)
        turns = document["turns"]
        record_entry = {
            "session_id": session_id,
            "part": entry["part"],
            "half": ledger.half_of(session_id),
            "question_ids": list(entry["question_ids"]),
            "journal": f"{ledger.JOURNAL_DIR}/{session_id}.json",
            "journal_digest": journal_digest,
            "read_log": f"{ledger.JOURNAL_DIR}/{session_id}.reads.json",
            "read_log_digest": read_digest,
            "turns": len(turns),
            "assumptions": len(document["assumptions"]),
            "binding_dependent_turns": sum(
                1 for turn in turns if ledger.is_binding_dependent(turn)
            ),
            "citing_turns": sum(1 for turn in turns if turn["assumptions_cited"]),
            "refusal_turns": sum(
                1
                for turn in turns
                if turn["result"]["kind"] in ledger.REFUSAL_STATUSES
            ),
            "proposer_turns": sum(
                1 for row in served
                if row["session_id"] == session_id and row["proposer_consulted"]
            ),
            "excluded": recorder.excluded_reason,
        }
        if recorder.excluded_reason:
            excluded.append(record_entry)
        sessions.append(record_entry)
    elapsed = round(time.time() - started, 1)

    admitted = [entry for entry in sessions if not entry["excluded"]]
    part_one = [row for row in served if row["part"] == 1]

    prompts_artifact = {
        "schema": PROMPTS_SCHEMA,
        "design": "docs/DESIGN-plain-input.md",
        "prereg": PLAIN_PREREG,
        "what_this_is": (
            "every prompt sent to the proposer during this recording, "
            "retained verbatim. B9 requires that every prompt be RETAINED and "
            "scanned — a construction argument nobody checks is a "
            "construction argument that stops being true quietly."
        ),
        "and_what_it_is_not": (
            "not a transcript of the model's reasoning. The model's whole "
            "output is `raw`, and the only part of it this system reads is "
            "`selected_index`, an integer."
        ),
        "created_utc": CREATED_UTC,
        "prompts": prompt_records,
    }

    counts = {
        "sessions_recorded": len(sessions),
        "sessions_excluded_by_the_no_write_gate_rule": len(excluded),
        "sessions_admitted": len(admitted),
        "turns_admitted": sum(entry["turns"] for entry in admitted),
        "assumptions_declared": sum(entry["assumptions"] for entry in admitted),
        "binding_dependent_turns_admitted": sum(
            entry["binding_dependent_turns"] for entry in admitted
        ),
        "citing_turns_admitted": sum(
            entry["citing_turns"] for entry in admitted
        ),
        "refusal_turns_admitted": sum(
            entry["refusal_turns"] for entry in admitted
        ),
        "turns_the_proposer_was_consulted_on": sum(
            1 for row in served if row["proposer_consulted"]
        ),
        "prompts_retained": len(prompt_records),
        "recording_seconds": elapsed,
        "by_half": {
            half: {
                "sessions": sum(1 for e in admitted if e["half"] == half),
                "turns": sum(e["turns"] for e in admitted if e["half"] == half),
            }
            for half in ("A", "B")
        },
    }

    return (
        {
            "schema": SEAL_SCHEMA,
            "slice": 2,
            "design": "docs/DESIGN-session-ledger.md",
            "design_clause": "§5 slice 2, recorded under §6 P3's protocol",
            "completes": "docs/DESIGN-plain-input.md",
            "prereg": PLAIN_PREREG,
            "built_by": "scripts/record_plain_corpus.py",
            "created_utc": CREATED_UTC,
            "recorder_code_digest": measured_digest,
            "the_recorder_is_slice_1s_unmodified": (
                "checked against the digest experiments/session_ledger_prereg.json "
                "froze before slice 1 recorded. Slice 2 records under the same "
                "recorder or it is not recording under the same protocol."
            ),
            "slice_1s_seal_is_closed_and_untouched": (
                "experiments/session_corpus_seal.json covers `v021-s*` and is "
                "not read, re-scored or re-recorded here. This corpus is "
                "`v021-p*` and is its own denominator."
            ),
            "protocol": protocol,
            "the_proposer_model_pin": {
                "why_the_header_carries_it_now": (
                    "DESIGN-session-ledger §3 lists `proposer_model_digest` as "
                    "'slice 2 only, key omitted until then, omission meaning "
                    "\"no proposer served\"'. Slice 1's headers omit it; these "
                    "carry it, so the omission keeps meaning what it meant."
                ),
                "provider_tag": "ollama:qwen3:4b-instruct",
                "weights_blob_sha256": weights["sha256"],
                "bytes": weights["bytes"],
                "verified_before_any_question_was_asked": weights["verified"],
                "the_refusal_discipline": (
                    "machine_reader.verify_weights hashes the blob's BYTES and "
                    "refuses on absence or mismatch. It never downloads. The "
                    "filename ollama gives a blob is its digest, so trusting "
                    "the name would be checking the copy against itself."
                ),
            },
            "determinism": (
                "artifact committed from a deterministic runner; reproductions "
                "welcome and recorded (ROADMAP-v0.21 §4.0(2)). The proposer arm "
                "earned that in P4 — experiments/plain_proposer_determinism.json, "
                "two passes, byte-identical — and P4's honest limit travels with "
                "it: byte-identity across two passes on one machine on one day "
                "is not a proof of determinism."
            ),
            "digest_algorithm": "sha256 over the journal file's bytes as written",
            "where_the_digests_live": (
                "here, out of band. §3 puts a journal's whole-file digest in "
                "the seal and never inside the journal it covers."
            ),
            "what_a_stranger_can_and_cannot_check": (
                "every journal against the digests below: yes, offline, with no "
                "key. Any per-record MAC: no — the key descends from a root "
                "secret under .runtime/, which .gitignore excludes, because "
                "B8's threat model is that the tamperer holds no key."
            ),
            "no_ab_split_is_used_and_here_is_why": (
                "slice 1's A/B rule is applied to these ids and PUBLISHED per "
                "session, because the rule is committed and a reader may want "
                "it. It is not used as a denominator: slice 2's "
                "preregistration registered no half-B rule, and minting one "
                "now — after the corpus exists — would be choosing a "
                "denominator with the results in view. Every gate below scores "
                "over a named subset instead."
            ),
            "prompts_artifact": PROMPTS,
            "counts": counts,
            "sessions": sessions,
            "excluded_sessions": excluded,
            "served_turns": served,
            "non_claims": [
                "maintainer-authored: no stranger-usability claim, here or "
                "anywhere in this cycle (DESIGN-plain-input §5 G1's STRANGER "
                "park is cited, not re-encountered)",
                "reproducible, not correct — a wrong answer replays as "
                "faithfully as a right one",
                "no throughput claim: `conditional` is non-answering and this "
                "corpus appears in no sentence containing a K number",
                "no completeness over readings: the candidate list is what "
                "exact code could enumerate",
                "slice 2 does not repair the silent binding P2 measured — see "
                "the denominators block and prereg amendment 4",
            ],
        },
        prompts_artifact,
    )


def denominators(repo_root: Path) -> dict:
    """Which gate scores over which subset — published, never summed.

    The one block a reader should read before any rate in this cycle. The
    thirty sealed questions do not form one population: thirteen are bound by
    the resolver before the proposer is consulted, nine were authored to
    exhaust, and the two facts overlap. A single number over thirty would
    average a gate's result with a subset that gate cannot reach.
    """

    from harness import CoreSession, route_line  # noqa: PLC0415
    from resolver import default_index  # noqa: PLC0415

    questions = json.loads(
        (repo_root / QUESTION_SET).read_text(encoding="utf-8")
    )["questions"]
    index = default_index()
    routed: dict[str, dict] = {}
    for item in questions:
        session = CoreSession.boot(repo_root, offline=True)
        session.resolver_index = index
        verdict = route_line(repo_root, session, item["question"])
        routed[item["question_id"]] = {
            "route": verdict.get("route"),
            "status": verdict.get("status"),
            "authors_prior": item["authors_prior"],
        }

    # The key says `resolver_found`, so the filter checks the ROUTE as well
    # as the status — a correction dated 2026-08-26 after review. It read
    # `status == "found"` alone, which would have counted a `found` served by
    # `twin`, `closure` or `conform` as a resolver bind. It changes nothing
    # here (all thirteen are route `resolver`, measured before and after) and
    # a key that asserts more than its filter checks is the defect class this
    # cycle's review found four times.
    resolver_found = sorted(
        qid
        for qid, row in routed.items()
        if row["status"] == "found" and row["route"] == "resolver"
    )
    resolver_waiting = sorted(
        qid for qid, row in routed.items()
        if row["status"] == "waiting" and row["route"] == "resolver"
    )
    reachable = sorted(
        qid for qid, row in routed.items()
        if qid not in resolver_found and qid not in resolver_waiting
    )
    exhaust_authored = sorted(
        item["question_id"] for item in questions
        if item["authors_prior"] == "exhaust"
    )
    return {
        "why_this_block_exists": (
            "the thirty sealed questions are not one population, and a rate "
            "over all thirty would average a gate's result with a subset that "
            "gate cannot reach. Every subset below is named with its members "
            "and its size, and the sizes are NEVER SUMMED into a headline."
        ),
        "measured_how": (
            "each sealed question served once through a fresh offline "
            "CoreSession against the committed tree; the subsets are read off "
            "the route and status of the verdict, not asserted."
        ),
        "resolver_found_before_the_proposer_is_consulted": {
            "size": len(resolver_found),
            "question_ids": resolver_found,
            "what_it_means": (
                "the resolver bound these to a statement and served `found` "
                "with nothing in the verdict recording that a reading was "
                "chosen. The proposer never sees them: DESIGN-plain-input "
                "§2.2 confines it to row 12 and G4 protects the resolver row "
                "by name."
            ),
            "which_gates_score_over_it": [
                "NONE of this slice's gates. It is the STANDING DEFECT, ruled "
                "NOT MET at G9 by prereg amendment 4 and filed in "
                "docs/BACKLOG.md with these thirteen as its fixtures."
            ],
        },
        "resolver_waiting_pre_empted_but_not_silently": {
            "size": len(resolver_waiting),
            "question_ids": resolver_waiting,
            "what_it_means": (
                "the resolver's own ASK subloop claimed these and NAMED its "
                "alternatives. Pre-empted from the proposer, but not silently "
                "bound — which is why they are a separate subset and not "
                "folded into the thirteen."
            ),
            "which_gates_score_over_it": ["none"],
        },
        "proposer_reachable_remainder": {
            "size": len(reachable),
            "question_ids": reachable,
            "what_it_means": (
                "every registered route declined, so row 12's pre-router runs. "
                "This is the whole surface slice 2 adds, and the only subset "
                "on which the served behaviour can differ from the committed "
                "tree's."
            ),
            "which_gates_score_over_it": [
                "G2 (zero silent binds, over what THIS SLICE serves)",
                "the served-behaviour counts in the run's readout",
            ],
        },
        "exhaust_authored": {
            "size": len(exhaust_authored),
            "question_ids": exhaust_authored,
            "what_it_means": (
                "authored to EXHAUST — outside the corpus, or not questions "
                "with an exact answer at all. The question set's own words: "
                "'a candidate that verified for one of them would be the "
                "proposer inventing rather than selecting'. The sealed ceiling "
                "of 21/30 is what this subset costs."
            ),
            "which_gates_score_over_it": [
                "G1, as part of its thirty — and G1's rate is published "
                "against the sealed 21/30 ceiling rather than against 30"
            ],
        },
        "the_overlap_is_real_and_is_not_hidden": {
            "exhaust_authored_that_the_resolver_pre_empted": sorted(
                set(exhaust_authored) & set(resolver_waiting + resolver_found)
            ),
            "why_it_matters": (
                "the subsets INTERSECT, so their sizes cannot be added. A "
                "question authored to exhaust that the resolver claimed at "
                "`waiting` belongs to two of the blocks above and to neither "
                "exclusively."
            ),
        },
        "gate_denominators": {
            "G1": (
                "all thirty sealed questions. G1 asks what fraction yield at "
                "least one VERIFIED candidate, which the enumerator answers "
                "for every question regardless of which route serves it. "
                "Amendment 1's disclosure applies: enumeration is generous and "
                "`word_match` verification is nearly free, so the "
                "selection-plus-verification number is published beside it and "
                "G1's own rate is labelled the weaker one."
            ),
            "G2": (
                "the served turns of this corpus's part 1, on the "
                "proposer-reachable remainder. Stated as a subset because G2 "
                "is a property of what THIS SLICE serves; the resolver's "
                "thirteen are adjudicated at G9, not here."
            ),
            "G3": (
                "the distractor pairs that SURVIVE the pre-check. Pairs whose "
                "two sentences do not denote two different verified queries "
                "are excluded from the denominator and the exclusion is "
                "counted and published — the clause C-V4 dropped."
            ),
            "G5": (
                "the same thirty, both arms, drawing from the same enumerated "
                "list. The comparison isolates selection."
            ),
            "B9": (
                "every prompt retained by this recording — part 1 and part 2 "
                "together, because a prompt is a prompt whether or not the "
                "question was a repeat."
            ),
            "B10": (
                "every turn of this corpus with an empty `assumptions_cited`, "
                "part 1 and part 2 together."
            ),
            "B12": "every turn of this corpus.",
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=SEAL)
    ap.add_argument("--prompts-out", default=PROMPTS)
    args = ap.parse_args(argv)

    seal, prompts = record(REPO)
    seal["denominators"] = denominators(REPO)

    (REPO / args.prompts_out).write_text(
        json.dumps(prompts, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    seal["prompts_artifact_digest"] = ledger.text_digest(
        (REPO / args.prompts_out).read_text(encoding="utf-8")
    )
    (REPO / args.out).write_text(
        json.dumps(seal, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {args.out} and {args.prompts_out}")
    print(json.dumps(seal["counts"], indent=2, sort_keys=True))
    for name, block in seal["denominators"].items():
        if isinstance(block, dict) and "size" in block:
            print(f"{name}: {block['size']} {block['question_ids']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
