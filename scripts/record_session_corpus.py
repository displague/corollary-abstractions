#!/usr/bin/env python3
"""P3 — record the session corpus under the frozen protocol, then seal it.

`docs/DESIGN-session-ledger.md` §6 P3, steps (2) and (3). Step (1), the
recording protocol, is frozen in `experiments/session_ledger_prereg.json`
and this script obeys it rather than restating it: the session count cap
(60), the turn cap (64), the live-assumption cap (8), the
no-write-gate-turn rule, the session-id rule (`v021-s{NN}`, in order) and
the A/B split rule all come from that file, and a disagreement between this
script and the prereg is a bug in this script.

## What the sessions are, said plainly

**Maintainer-authored.** Every line below was written by the maintainer, in
advance, to exercise the object — not sampled from anything, and not what
any other person would type. DESIGN-plain-input §5 G1's STRANGER caveat is
inherited whole: the claim is scoped to these sessions and no
stranger-usability claim is made anywhere in this cycle.

That is also what makes P3's floor meetable, and the prereg says so beside
the non-claim: a binding-dependent turn is one whose served evaluation read
a live assumption, so authoring `suppose x = 5` followed by turns that
compute with `x` produces them deterministically. Meetability by
construction is honest exactly as long as the construction is disclosed.

## The six shapes, assigned by counter and not by half

Each session's shape is `index % 6`. The shapes are assigned from the
session's POSITION, and the position determines the id, and the id
determines the half — so nothing about the authoring consulted which half a
session would land in. The split is a consequence of a counter, twice over.

0. assumption-free — arithmetic, corpus lookups, a refusal. These are the
   sessions B10's fence has the most to say about: every turn cites nothing.
1. one assumption, then turns that compute under it.
2. two assumptions, then turns using each and both.
3. supersession — declare, cite, re-declare the same subject, cite again.
4. retraction — declare, cite, retract, then the SAME line again, which now
   cites nothing and answers differently.
5. a negated assumption and its typed conflict refusal, beside a working
   assumption in the same session.

Every shape ends on a line that reaches no answer, because a corpus with no
refusal turns would leave B7 with an empty denominator.

## No write-gate line, and the rule is enforced not remembered

`SessionRecorder` marks a session excluded whole if any turn's served
verdict reaches the write gate. Nothing authored here does; the check runs
anyway, and the seal publishes the count either way — an exclusion nobody
counted is an exclusion nobody can check.

## Determinism

`created_utc` comes from the protocol, not the clock. Session ids come from
the counter. The resolver's graph index is built once and shared across
sessions, for the reason `serve_chat.ChatEngine.prewarm` already states.
Per ROADMAP-v0.21 §4.0(2): artifact committed from a deterministic runner;
reproductions welcome and recorded.

The MAC key ring is the one thing that is NOT reproducible off this
workstation, and that is the design's own choice rather than an oversight:
the keyfile lives under `.runtime/`, which `.gitignore` excludes, because
B8's threat model is that the tamperer holds no key. A stranger can check
every journal against the seal's out-of-band digests and cannot check a
MAC, and the seal says so.
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

PREREG = "experiments/session_ledger_prereg.json"
SEAL = "experiments/session_corpus_seal.json"
SEAL_SCHEMA = "corollary.session-corpus-seal/1"

#: The pre-repair seal, retained byte for byte when the corpus is recorded
#: again at a fixed tree (prereg amendment 3). A re-recording that erased
#: what it superseded would make its own delta uncheckable.
PRIOR_SEAL = "experiments/session_corpus_seal_pre_repair.json"

#: From the protocol, not the clock.
CREATED_UTC = "2026-08-25T00:00:00Z"

#: Corpus material these sessions lean on, named once so a reader can see
#: that the lines are about committed statements rather than about nothing.
_RESOLVER_LINES = (
    "de morgan laws",
    "quadratic formula",
    "binary exponentiation",
    "double angle cosine identity",
    "pythagorean identity",
    "euclidean distance formula",
)
_TWIN_LINES = (
    "twin programming.euclid.recursive",
    "twin trigonometry.identities.double_angle_cosine",
    "twin algebra.polynomial_equations.quadratic_formula",
    "twin programming.factorial.recursive",
    "twin logic.boolean_laws.de_morgan_laws",
    "twin programming.binexp.recursive",
)
_REFUSAL_LINES = (
    "twin no.such.statement.at.all",
    "owns",
    "retract a999",
    "suppose",
    "twin two words",
    "conform no.such.statement a=1",
)
_VARIABLES = ("x", "y", "n", "k", "m", "t")


def session_lines(index: int) -> tuple[str, ...]:
    """The authored lines for session `index`, by shape. Deterministic."""

    shape = index % 6
    pick = lambda seq: seq[index % len(seq)]  # noqa: E731
    other = lambda seq: seq[(index + 3) % len(seq)]  # noqa: E731
    var = pick(_VARIABLES)
    var2 = other(_VARIABLES)
    base = 2 + (index % 7)
    second = 3 + (index % 5)

    if shape == 0:
        return (
            f"{base} + {second}",
            f"{base} ^ 3",
            pick(_TWIN_LINES),
            pick(_RESOLVER_LINES),
            f"{base} * {second} = {base * second}",
            pick(_REFUSAL_LINES),
        )
    if shape == 1:
        return (
            pick(_RESOLVER_LINES),
            f"suppose {var} = {base}",
            f"{var} ^ 2",
            f"{var} + {second}",
            f"{var} * {var}",
            pick(_TWIN_LINES),
            pick(_REFUSAL_LINES),
        )
    if shape == 2:
        return (
            f"suppose {var} = {base}",
            f"suppose {var2} = {second}",
            f"{var} ^ 2",
            f"{var2} ^ 2",
            f"{var} + {var2}",
            f"{var} * {var2} = {base * second}",
            pick(_REFUSAL_LINES),
        )
    if shape == 3:
        return (
            f"suppose {var} = {base}",
            f"{var} ^ 2",
            pick(_TWIN_LINES),
            f"suppose {var} = {base + 4}",
            f"{var} ^ 2",
            f"{var} + 1",
            pick(_REFUSAL_LINES),
        )
    if shape == 4:
        return (
            f"suppose {var} = {base}",
            f"{var} ^ 2",
            f"{var} + {second}",
            "retract a001",
            f"{var} ^ 2",
            pick(_RESOLVER_LINES),
            pick(_REFUSAL_LINES),
        )
    return (
        f"suppose not {var} = {base}",
        f"{var} ^ 2",
        f"suppose {var2} = {second}",
        f"{var2} ^ 2",
        f"{var2} + {second}",
        pick(_TWIN_LINES),
        pick(_REFUSAL_LINES),
    )


def _delta_finding(
    changed: int, lines: list[str], pin_moves: dict[str, int]
) -> str:
    """What THIS recording moved, written from the numbers.

    Assembled rather than asserted for the reason P1's finding is: the
    expectation registered for the B10 repair's recording was TEN changed
    turns, a hand-typed sentence saying so would still have said so at zero,
    and zero is what it was. That historical delta lives in its own block;
    this sentence describes only the transition this run made.
    """

    pins = ", ".join(f"{name} ({count} headers)" for name, count in sorted(pin_moves.items()))
    head = (
        f"{changed} turn answer-digest(s) moved"
        + (f" across lines {lines}" if lines else "")
        + f"; header pins that moved: {pins or 'none'}."
    )
    if changed == 10 and lines == ["retract a999"]:
        return head + (
            " This is the registered expectation exactly: the repair reached "
            "the defect and nothing else."
        )
    if changed == 0 and pin_moves:
        return head + (
            " No SERVED BYTE moved; only the pin did. Re-recording was "
            "mandatory anyway: a journal carrying the old pin would be "
            "refused `stale-environment` by B3's own machinery on every "
            "replay, so any edit to a module in RENDERING_MODULES — however "
            "cosmetic — obliges a re-recording. That is the pin working, not "
            "a failure. Which transition this was is named exactly by "
            "`pin_values_that_moved`; the B10 repair's own delta, and the "
            "registered expectation it missed, are in "
            "`the_b10_repair_delta` beside this block."
        )
    if changed == 0:
        return head + (
            " Nothing moved at all — same journals, same pins. This "
            "recording is a reproduction of the one before it, which is what "
            "ROADMAP-v0.21 §4.0(2)'s determinism-plus-commit clause asks a "
            "re-run to be. The B10 repair's delta is in "
            "`the_b10_repair_delta` beside this block; it is not this one."
        )
    return head + (
        " Turn answer-digests moved. Every one is listed in `changed_turns` "
        "and the distinct lines in `distinct_lines_changed`, so a reader can "
        "check whether the change reached only what it was meant to reach."
    )


def _protocol() -> dict:
    prereg = json.loads((REPO / PREREG).read_text(encoding="utf-8"))
    protocol = prereg["recording_protocol"]
    amendment = prereg["amendments"][0]
    return {
        "session_count_cap": protocol["session_count_cap"],
        "turn_cap_per_session": protocol["turn_cap_per_session"],
        "live_assumption_cap": protocol["live_assumption_cap"],
        "ab_split_rule": protocol["ab_split_rule"],
        "session_id_rule": protocol["session_id_rule"],
        "recorder_code_digest": amendment["adds"]["recorder_code_digest"],
        "floor": prereg["floors_and_their_meetability"]["P3_corpus_floor"],
    }


def record(repo_root: Path) -> dict:
    from resolver import default_index  # noqa: PLC0415
    from session_keys import SessionKeyRing  # noqa: PLC0415

    protocol = _protocol()
    if recorder_code_digest(repo_root) != protocol["recorder_code_digest"]:
        raise RuntimeError(
            "the recorder's bytes do not match the digest the protocol froze "
            "before recording; recording under an unpinned recorder is the "
            "one thing the C3 fix exists to prevent"
        )

    index = default_index()
    keyring = SessionKeyRing.open(repo_root / ".runtime" / "session-keys.json")
    pin_table = None

    sessions: list[dict] = []
    excluded: list[dict] = []
    # Per-turn answer digests as they stand BEFORE this recording overwrites
    # them. A re-recording at a fixed tree owes a checkable claim about what
    # it changed, and the claim is only checkable if the old numbers are read
    # before they are replaced (prereg amendment 3).
    prior_digests: dict[str, dict[int, str]] = {}
    started = time.time()
    for position in range(1, protocol["session_count_cap"] + 1):
        session_id = f"v021-s{position:02d}"
        existing = ledger.journal_path(repo_root, session_id)
        if existing.exists():
            old = json.loads(existing.read_text(encoding="utf-8"))
            prior_digests[session_id] = {
                "turns": {
                    turn["turn_index"]: turn["result"]["answer_bytes_digest"]
                    for turn in old["turns"]
                },
                "pins": old["header"]["pins"],
            }
        recorder = SessionRecorder(
            repo_root,
            session_id,
            CREATED_UTC,
            keyring,
            shared_index=index,
            pin_table=pin_table,
        )
        pin_table = recorder.pin_table
        lines = session_lines(position - 1)
        if len(lines) > protocol["turn_cap_per_session"]:
            raise RuntimeError(
                f"{session_id} authors {len(lines)} turns against a frozen "
                f"cap of {protocol['turn_cap_per_session']}"
            )
        for line in lines:
            recorder.turn(line)
        document = recorder.document()
        journal_digest, read_digest = recorder.write(repo_root)
        turns = document["turns"]
        entry = {
            "session_id": session_id,
            "half": ledger.half_of(session_id),
            "shape": (position - 1) % 6,
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
            "excluded": recorder.excluded_reason,
        }
        if recorder.excluded_reason:
            excluded.append(entry)
        sessions.append(entry)
    elapsed = round(time.time() - started, 1)

    admitted = [entry for entry in sessions if not entry["excluded"]]
    by_half = {"A": [], "B": []}
    for entry in admitted:
        by_half[entry["half"]].append(entry)

    counts = {
        "sessions_recorded": len(sessions),
        "sessions_excluded_by_the_no_write_gate_rule": len(excluded),
        "sessions_admitted": len(admitted),
        "turns_admitted": sum(entry["turns"] for entry in admitted),
        "binding_dependent_turns_admitted": sum(
            entry["binding_dependent_turns"] for entry in admitted
        ),
        "refusal_turns_admitted": sum(
            entry["refusal_turns"] for entry in admitted
        ),
        "assumption_free_sessions": sum(
            1 for entry in admitted if entry["assumptions"] == 0
        ),
        "by_half": {
            half: {
                "sessions": len(entries),
                "turns": sum(entry["turns"] for entry in entries),
                "binding_dependent_turns": sum(
                    entry["binding_dependent_turns"] for entry in entries
                ),
                "refusal_turns": sum(
                    entry["refusal_turns"] for entry in entries
                ),
            }
            for half, entries in by_half.items()
        },
        "recording_seconds": elapsed,
    }

    floor = {
        "sessions_required_corpus_wide": 30,
        "turns_required_corpus_wide": 120,
        "binding_dependent_turns_required_in_half_b": 36,
        "sessions_met": counts["sessions_admitted"] >= 30,
        "turns_met": counts["turns_admitted"] >= 120,
        "binding_dependent_in_half_b_met": (
            counts["by_half"]["B"]["binding_dependent_turns"] >= 36
        ),
    }
    floor["all_met"] = all(
        floor[key] for key in
        ("sessions_met", "turns_met", "binding_dependent_in_half_b_met")
    )
    floor["reading_frozen_before_recording"] = (
        "30 sessions and 120 turns over the RECORDED CORPUS; 36 "
        "binding-dependent turns in HALF B's share alone. Frozen in the "
        "prereg, with its reasons, before this script existed."
    )
    # Published, not buried: the roadmap's one-line compression of the same
    # floor attaches "in half B's share alone" to all three clauses, and
    # under THAT reading this corpus would miss on sessions. The prereg
    # chose the design's reading before recording and wrote down why —
    # among the reasons, that 30 sessions in half B against a 60-session cap
    # is a coin flip on a hash-derived split, which is the
    # unmeetable-by-construction shape §4.0(3) exists to forbid. Reporting
    # the number the other reading would have produced is what makes that
    # choice checkable rather than convenient.
    floor["under_the_roadmaps_compressed_reading"] = {
        "what_it_would_require": (
            "≥30 sessions, ≥120 turns AND ≥36 binding-dependent turns, all "
            "in half B's share alone (ROADMAP-v0.21 §1.1)"
        ),
        "sessions_in_half_b": counts["by_half"]["B"]["sessions"],
        "turns_in_half_b": counts["by_half"]["B"]["turns"],
        "binding_dependent_in_half_b": (
            counts["by_half"]["B"]["binding_dependent_turns"]
        ),
        "sessions_met": counts["by_half"]["B"]["sessions"] >= 30,
        "turns_met": counts["by_half"]["B"]["turns"] >= 120,
        "binding_dependent_met": (
            counts["by_half"]["B"]["binding_dependent_turns"] >= 36
        ),
        "why_it_is_published_rather_than_omitted": (
            "the prereg resolved the discrepancy in writing BEFORE recording "
            "and gave its reasons. Publishing the number the other reading "
            "would have produced is what turns that resolution from a "
            "convenient choice into a checkable one — and it is the number a "
            "reader who prefers the roadmap's wording needs in order to "
            "disagree with the prereg on the evidence."
        ),
    }

    prior_seal_path = repo_root / PRIOR_SEAL
    delta = None
    # Two blocks, deliberately separate. `recording_delta` always describes
    # THIS recording's transition and may be empty. `the_b10_repair_delta` is
    # a fixed historical record of one particular transition and never
    # changes. An earlier version had one block trying to be both, kept
    # alive by carrying itself forward whenever a re-recording had nothing
    # to say — and the result was a block that described the B10 repair
    # while measuring an unrelated citation edit. A record that could
    # describe either transition and names neither is a record a reader
    # cannot use.
    if prior_digests:
        changed = []
        pin_moves: dict[str, int] = {}
        pin_values: dict[str, dict] = {}
        for entry in sessions:
            old = prior_digests.get(entry["session_id"], {})
            journal = json.loads(
                (repo_root / entry["journal"]).read_text(encoding="utf-8")
            )
            for name, value in journal["header"]["pins"].items():
                was = old.get("pins", {}).get(name)
                if was != value:
                    pin_moves[name] = pin_moves.get(name, 0) + 1
                    # WHICH values moved, not only that some did. A delta
                    # that says "rendering_module_digests moved on 60
                    # headers" is true of every re-recording after any
                    # rendering module changes, so it cannot tell a reader
                    # WHICH transition it measured.
                    if isinstance(value, dict) and isinstance(was, dict):
                        for leaf in sorted(set(value) | set(was)):
                            if value.get(leaf) != was.get(leaf):
                                pin_values.setdefault(
                                    f"{name}.{leaf}",
                                    {"was": was.get(leaf), "now": value.get(leaf)},
                                )
                    else:
                        pin_values.setdefault(name, {"was": was, "now": value})
            for turn in journal["turns"]:
                was = old.get("turns", {}).get(turn["turn_index"])
                now = turn["result"]["answer_bytes_digest"]
                if was is not None and was != now:
                    changed.append(
                        {
                            "session_id": entry["session_id"],
                            "turn_index": turn["turn_index"],
                            "input_bytes": turn["input_bytes"],
                            "answer_bytes_digest_was": was,
                            "answer_bytes_digest_now": now,
                        }
                    )
        prior_seal = (
            json.loads(prior_seal_path.read_text(encoding="utf-8"))
            if prior_seal_path.exists()
            else None
        )
        lines_changed = sorted({row["input_bytes"] for row in changed})
        delta = {
            "why_the_corpus_was_recorded_again": (
                "the B10 repair touches scripts/harness.py, which is in "
                "build_throughput_tasks.RENDERING_MODULES, so the "
                "rendering_module_digests pin moves. A journal recorded "
                "before the serving path changed MUST NOT replay against the "
                "code after it — every replay would refuse "
                "`stale-environment`, which is B3's mechanism working, not a "
                "failure. So the same authored corpus is recorded again at "
                "the fixed tree, exactly as a suite gate re-runs at a fixed "
                "tree (prereg amendment 3)."
            ),
            "the_corpus_itself_did_not_move": (
                "the same 60 authored sessions, the same lines, the same ids "
                "from the same counter, the same protocol, the same caps and "
                "the same A/B split. scripts/record_session_corpus.py's "
                "authoring is unedited."
            ),
            "prior_seal_retained_at": PRIOR_SEAL,
            "prior_seal_digest": (
                ledger.text_digest(
                    prior_seal_path.read_text(encoding="utf-8")
                )
                if prior_seal_path.exists()
                else None
            ),
            "registered_expectation": (
                "EXACTLY the ten turns B10 named, and no others. More than "
                "ten means the repair reached further than the defect; fewer "
                "means it did not reach the defect. Either is a finding and "
                "is published as one. Frozen in prereg amendment 3 before "
                "this recording ran."
            ),
            "turns_whose_answer_digest_changed": len(changed),
            "distinct_lines_changed": lines_changed,
            "expectation_met": (
                len(changed) == 10 and lines_changed == ["retract a999"]
            ),
            "changed_turns": changed,
            "header_pins_that_moved": pin_moves,
            "pin_values_that_moved": pin_values,
            "which_transition_this_measures": (
                "the transition from the journals that were on disk when this "
                "recording ran to the ones it wrote — named exactly by "
                "`pin_values_that_moved` above. It is NOT necessarily the B10 "
                "repair transition: any change to a rendering module moves "
                "the same pin on all 60 headers and produces a "
                "same-shaped delta. `the_b10_repair_delta` below records that "
                "one separately, because a block that could describe either "
                "and names neither is a block a reader cannot use."
            ),
            "finding": _delta_finding(len(changed), lines_changed, pin_moves),
            "counts_unchanged": (
                prior_seal is not None
                and prior_seal["counts"]["sessions_admitted"]
                == counts["sessions_admitted"]
                and prior_seal["counts"]["turns_admitted"]
                == counts["turns_admitted"]
                and prior_seal["counts"]["binding_dependent_turns_admitted"]
                == counts["binding_dependent_turns_admitted"]
                and prior_seal["counts"]["by_half"] == counts["by_half"]
            ),
            "prior_counts": prior_seal["counts"] if prior_seal else None,
        }

    return {
        "schema": SEAL_SCHEMA,
        "prerequisite": "P3",
        **({"recording_delta": delta} if delta else {}),
        "the_b10_repair_delta": {
            "what_it_was": (
            "the recording made at the tree repaired by prereg "
            "amendment 3's fix (a), committed as [GATE3-V21]."
            ),
            "registered_expectation": (
            "EXACTLY the ten turns B10 named would change."
            ),
            "what_it_measured": (
            "ZERO turn answer-digests changed; "
            "rendering_module_digests moved on all 60 headers."
            ),
            "expectation_met": False,
            "why_it_missed": (
            "a recorded session always has a ledger attached, so "
            "`retract a999` always took the unknown-id arm and always "
            "rendered the string fix (a) chose to KEEP. What moved was "
            "the STATELESS side of B10's comparison — the fresh "
            "ledgerless session B10 compares against — which appears "
            "in no journal. Wrong about which side would move, right "
            "that the sides would meet."
            ),
            },
        "design": "docs/DESIGN-session-ledger.md",
        "design_clause": "§6 P3 step (3) — the seal",
        "prereg": PREREG,
        "built_by": "scripts/record_session_corpus.py",
        "recorder_code_digest": protocol["recorder_code_digest"],
        "created_utc": CREATED_UTC,
        "protocol": protocol,
        "determinism": (
            "artifact committed from a deterministic runner; reproductions "
            "welcome and recorded (ROADMAP-v0.21 §4.0(2))"
        ),
        "digest_algorithm": "sha256 over the journal file's bytes as written",
        "where_the_digests_live": (
            "here, out of band. §3 puts a journal's whole-file digest in the "
            "seal and never inside the journal it covers, because a digest "
            "that lives inside the thing it covers is a digest an editor "
            "updates."
        ),
        "what_a_stranger_can_and_cannot_check": (
            "every journal against the digests below: yes, offline, with no "
            "key. Any per-record MAC: no. The MAC key descends from a root "
            "secret under .runtime/, which .gitignore excludes, because B8's "
            "threat model is that the tamperer holds no key — and the price "
            "of that is that a reader who is not the maintainer holds no key "
            "either. Said here rather than discovered later."
        ),
        "and_note_that_replay_verifies_no_macs_at_all": (
            "scripts/replay_session.py compares pins and re-serves lines. It "
            "never derives a key and never calls verify_turn_mac or "
            "verify_assumption_mac, so a journal whose every signature was "
            "forged would replay exactly as well as an authentic one. That is "
            "a division of labour rather than a gap: replay asks whether "
            "recorded lines still produce recorded answers, a question with "
            "no key in it. Integrity lives in §7 B8 (keyed-MAC tamper "
            "detection against an adversary who repairs the digest chain) and "
            "in the out-of-band whole-file digests below. Replay plus these "
            "digests is what a stranger gets; replay plus these digests plus "
            "B8 is what the maintainer gets."
        ),
        "half_b_discipline": (
            "implementation and debugging may exercise half A only; half B's "
            "first execution is the registered run"
        ),
        "counts": counts,
        "floor": floor,
        "sessions": sessions,
        "excluded_sessions": excluded,
        "non_claims": [
            "maintainer-authored: no stranger-usability claim, here or "
            "anywhere in this cycle (DESIGN-plain-input §5 G1's STRANGER park "
            "is cited, not re-encountered)",
            "reproducible, not correct — a wrong answer replays as "
            "faithfully as a right one (§10)",
            "no cross-session memory: every journal is one session and the "
            "live set never leaves it",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=SEAL)
    args = ap.parse_args(argv)

    seal = record(REPO)
    out = REPO / args.out
    out.write_text(
        json.dumps(seal, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {args.out}")
    print(json.dumps(seal["counts"], indent=2, sort_keys=True))
    print(json.dumps(seal["floor"], indent=2, sort_keys=True))
    if not seal["floor"]["all_met"]:
        print(
            "\nSTOP: the capped protocol did not reach the floor. Per §6 P3 "
            "the cycle publishes 'multi-turn binding is rare in practice' as "
            "its finding and builds nothing further.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
