#!/usr/bin/env python3
"""P2 — can one admitted command tell a prompt's rival readings apart?

DESIGN-session-ledger §6 P2: *"For ten hand-sealed ambiguous prompts: does
any single admitted command distinguish the rival readings under exact
evaluation? If no separator exists for most, the clarifying-question arm has
nothing to ask and the conditional-answer arm wins by measurement. Committed
either way."*

**This is a measurement, not a gate.** Nothing here can go red, nothing here
licenses a capability, and both answers were publishable before the first
line ran. What it decides is which arm of DESIGN-plain-input's open question
— serve a conditional answer under a named supposition, or ask a clarifying
question — has anything to work with.

## The order, and how a reader checks it

The prompts and their candidate readings were frozen in
``experiments/session_p2_prompt_seal.json`` in its own commit, before this
file existed. This script **reads** that file; it never authors a reading.
The seal's digest travels into the artifact, and
``tests/test_session_prereqs.py`` recomputes it, so the ordering is checkable
rather than asserted.

## What a separator is, operationally

A reading is an admitted command. Serving it produces a verdict — the
structured stop `route_line` returns and `render_verdict` prints. Two
readings are **separated** when the bytes a person is served differ; they
**collapse** when those bytes are identical, and a collapse is the finding
that matters, because two readings the exact layer cannot tell apart are two
readings a clarifying question has no way to be about.

The echoed input line is excluded from the comparison. Every reading is a
different string by construction, so digesting the echo would separate all
ten prompts trivially and measure nothing. What is digested is what the
person is TOLD: route, status, detail, evidence, answer lines, missing
capability, receipt.

Two digests are published per reading because they answer different
questions:

* ``served_digest`` — the whole served verdict minus the echo. Separation on
  this digest means *the person reads different words.*
* ``act_digest`` — route and status only. Separation on this digest means
  *the system did a different thing.* Two readings can differ in words while
  performing the same act (two `twin` lookups that both report `found`), and
  that is a weaker separation than a different act, so the artifact carries
  both and never collapses them into one number.

## The boot, stated rather than assumed

Every reading is served on a **fresh** session (¶DEV-1's replay discipline:
no state crosses a line), booted ``offline=True`` — the forced-absent boot
P-IH1 uses, so the measurement does not depend on which optional archives
this workstation happens to hold. One sealed reading (p02's gloss row) needs
``retrieve.wordnet``, which an offline boot forces OFF; the artifact records
that per reading as ``row_served_on_this_boot: false`` rather than dropping
the reading, which is the capability sheet's own discipline
(`serve_chat.py:339-342`).

Per ROADMAP-v0.21 §4.0(2): artifact committed from a deterministic runner;
reproductions welcome and recorded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

SEAL = "experiments/session_p2_prompt_seal.json"
ARTIFACT = "experiments/session_p2_separator_probe.json"
SCHEMA = "corollary.session-p2-separator-probe/1"

#: The verdict keys a person is served. `line` is deliberately absent: it is
#: the echo of the input, every reading has a different one by construction,
#: and digesting it would separate everything and measure nothing.
SERVED_KEYS = (
    "route",
    "status",
    "detail",
    "evidence",
    "answer",
    "missing_capability",
    "receipt",
    "reading",
    "materialized",
)

#: The two fields that say what the system DID, as opposed to what it said.
ACT_KEYS = ("route", "status")


def file_digest(path: Path) -> str:
    """sha256 over the file's bytes with CRLF normalised to LF.

    The normalisation is the committed convention
    (`experiments/conformance_prereg.json` `digest_algorithm`), and it is
    what keeps a seal digest stable across a checkout that rewrites line
    endings — which this repository's own `.gitattributes` handling does.
    """

    raw = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def _canonical(verdict: dict, keys: tuple[str, ...]) -> str:
    payload = {
        key: verdict[key] for key in keys if verdict.get(key) not in (None, (), [])
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, default=list)


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


_SHARED_INDEX: object | None = None


def _serve(repo_root: Path, line: str) -> dict:
    """One line, one fresh offline session. Never a reused session.

    The resolver's graph index is the one object shared across those fresh
    sessions, and sharing it is a cost decision with no semantic content:
    ``CoreSession`` already builds exactly this object lazily and caches it
    for the session's whole life (`harness.py:1152-1159`), it is immutable
    committed-graph data, and building it costs ~6 s against a ~0.4 s boot —
    so rebuilding it thirty-five times would have made this probe a
    two-minute run for no change in any digest. Every piece of *session*
    state (pending candidates, hops, frames, story) is still fresh per line,
    which is the property ¶DEV-1 is about.
    """

    global _SHARED_INDEX
    from harness import CoreSession, route_line  # noqa: PLC0415

    if _SHARED_INDEX is None:
        from resolver import default_index  # noqa: PLC0415

        _SHARED_INDEX = default_index()
    session = CoreSession.boot(repo_root, offline=True)
    session.resolver_index = _SHARED_INDEX
    return route_line(repo_root, session, line)


def _registered(repo_root: Path) -> tuple[str, ...]:
    from harness import CoreSession  # noqa: PLC0415

    session = CoreSession.boot(repo_root, offline=True)
    return tuple(sorted(session.matrix.registered_ids()))


def _row_requires(route: str) -> tuple[str, ...]:
    """A reading's grammar row, resolved by ROUTE NAME rather than index.

    The seal carries both. It carried only the index at first, and v0.21's
    session ledger then inserted a `retract` row and shifted twenty-one of
    the twenty-five readings' indices — silently, because an index that is
    wrong is still an index. Route names are stable where positions are not,
    and the KeyError below is the loud version of the same event.
    """

    from serve_chat import LINE_GRAMMAR  # noqa: PLC0415

    for row in LINE_GRAMMAR:
        if row["route"] == route:
            return tuple(row["requires"])
    raise KeyError(f"no LINE_GRAMMAR row serves route {route!r}")


def _first_difference(left: dict, right: dict) -> list[str]:
    return [
        key
        for key in SERVED_KEYS
        if left.get(key) != right.get(key)
    ]


def probe(repo_root: Path) -> dict:
    seal_path = repo_root / SEAL
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    registered = _registered(repo_root)

    verdicts: list[dict] = []
    for prompt in seal["prompts"]:
        results: list[dict] = []
        served_verdicts: list[dict] = []
        by_served: dict[str, list[str]] = defaultdict(list)
        by_act: dict[str, list[str]] = defaultdict(list)
        for reading in prompt["candidate_readings"]:
            served = _serve(repo_root, reading["command"])
            served_verdicts.append(served)
            served_text = _canonical(served, SERVED_KEYS)
            act_text = _canonical(served, ACT_KEYS)
            served_digest = _digest(served_text)
            act_digest = _digest(act_text)
            requires = _row_requires(reading["route"])
            results.append(
                {
                    "reading_id": reading["reading_id"],
                    "command": reading["command"],
                    "grammar_row": reading["grammar_row"],
                    "route_sealed": reading["route"],
                    "route_taken": served.get("route"),
                    "status": served.get("status"),
                    "detail": served.get("detail"),
                    "answer_lines": len(served.get("answer") or ()),
                    "served_digest": served_digest,
                    "act_digest": act_digest,
                    "row_requires": list(requires),
                    "row_served_on_this_boot": all(
                        need in registered for need in requires
                    ),
                    "routed_where_it_was_sealed": (
                        served.get("route") == reading["route"]
                    ),
                }
            )
            by_served[served_digest].append(reading["reading_id"])
            by_act[act_digest].append(reading["reading_id"])

        collapsed = [ids for ids in by_served.values() if len(ids) > 1]
        collapsed_by_act = [ids for ids in by_act.values() if len(ids) > 1]
        separated = len(by_served) > 1
        separated_by_act = len(by_act) > 1

        differing_fields: list[str] = []
        if len(served_verdicts) >= 2:
            differing_fields = _first_difference(
                served_verdicts[0], served_verdicts[1]
            )

        raw = _serve(repo_root, prompt["prompt"])
        verdicts.append(
            {
                "prompt_id": prompt["prompt_id"],
                "prompt": prompt["prompt"],
                "readings_probed": [
                    reading["reading_id"]
                    for reading in prompt["candidate_readings"]
                ],
                "reading_results": results,
                "separated": separated,
                "separated_by_act": separated_by_act,
                "distinct_served_digests": len(by_served),
                "distinct_act_digests": len(by_act),
                "collapsed_readings": collapsed,
                "collapsed_readings_by_act": collapsed_by_act,
                "fields_separating_the_first_two_readings": differing_fields,
                "separator": (
                    {
                        "exists": True,
                        "kind": "the readings themselves",
                        "why": (
                            "the readings are admitted commands and their "
                            "served verdicts differ, so serving each one is "
                            "itself the distinguishing evaluation"
                        ),
                    }
                    if separated
                    else {
                        "exists": False,
                        "why": (
                            "every sealed reading of this prompt serves the "
                            "same bytes; no admitted command can be about the "
                            "difference, because on this boot there is none"
                        ),
                    }
                ),
                "raw_prompt_today": {
                    "route": raw.get("route"),
                    "status": raw.get("status"),
                    "detail": raw.get("detail"),
                    "silently_bound": raw.get("route") not in {
                        "dispatcher",
                        "none",
                    }
                    and raw.get("status") not in {"exhausted", "waiting"},
                },
            }
        )

    return {"verdicts": verdicts, "registered": list(registered)}


def _aggregate(verdicts: list[dict]) -> dict:
    total = len(verdicts)
    with_separator = sum(1 for v in verdicts if v["separated"])
    with_act_separator = sum(1 for v in verdicts if v["separated_by_act"])
    collapsed_any = sum(1 for v in verdicts if v["collapsed_readings"])
    fully_collapsed = sum(1 for v in verdicts if not v["separated"])
    raw_exhausts = sum(
        1
        for v in verdicts
        if v["raw_prompt_today"]["status"] in {"exhausted", "waiting"}
    )
    raw_silently_bound = sum(
        1 for v in verdicts if v["raw_prompt_today"]["silently_bound"]
    )
    routed_as_sealed = sum(
        1
        for v in verdicts
        for r in v["reading_results"]
        if r["routed_where_it_was_sealed"]
    )
    readings = sum(len(v["reading_results"]) for v in verdicts)
    return {
        "prompts_total": total,
        "prompts_with_a_separator": with_separator,
        "prompts_with_a_separator_at_the_act_level": with_act_separator,
        "prompts_with_at_least_one_collapsed_pair": collapsed_any,
        "prompts_whose_readings_all_collapsed": fully_collapsed,
        "readings_total": readings,
        "readings_that_routed_where_the_seal_said": routed_as_sealed,
        "raw_prompts_that_exhaust_or_wait_today": raw_exhausts,
        "raw_prompts_silently_bound_today": raw_silently_bound,
    }


def _answer(aggregate: dict, verdicts: list[dict]) -> str:
    """P2's answer to the incumbent's conditional-versus-clarify question.

    Generated from the counts. The design frames the decision rule and this
    function applies it: *"If no separator exists for most, the
    clarifying-question arm has nothing to ask and the conditional-answer arm
    wins by measurement."*
    """

    total = aggregate["prompts_total"]
    separated = aggregate["prompts_with_a_separator"]
    act = aggregate["prompts_with_a_separator_at_the_act_level"]
    silent = aggregate["raw_prompts_silently_bound_today"]
    majority = separated * 2 > total
    lead = (
        f"A separator exists for {separated} of {total} sealed prompts "
        f"({act} of {total} separate at the act level — a different route or "
        "status, not merely different words)."
    )
    if majority:
        verdict = (
            "So the design's stop condition — 'if no separator exists for "
            "most' — is NOT met, and the clarifying-question arm is "
            "expressible: for most of these prompts there is an admitted "
            "command whose exact evaluation is about the difference, which is "
            "what a clarifying question would have to be about. P2 therefore "
            "does NOT decide the conditional-versus-clarify question by "
            "measurement, and DESIGN-plain-input's open question stays open "
            "for slice 2 to settle on other grounds."
        )
    else:
        verdict = (
            "So the design's stop condition IS met: for most sealed prompts "
            "no admitted command distinguishes the rival readings, the "
            "clarifying-question arm has nothing to ask, and the "
            "conditional-answer arm wins by measurement rather than by "
            "preference."
        )
    caveat = (
        f" The separation that exists is cheap, and the artifact says so: a "
        "reading is an admitted command, so serving it IS the distinguishing "
        "evaluation, and separation mostly reports that two different "
        "commands do two different things. The expensive question — whether "
        "a person could ANSWER the clarifying question the separator "
        "licenses — is not measured here and is not claimed."
    )
    today = (
        f" Second reading, from the same run: handed the raw prose, today's "
        f"system silently bound {silent} of {total} prompts to one reading "
        "without saying it had chosen. Those are the prompts where a named "
        "supposition would change what the person is told, whichever arm "
        "wins."
    )
    return lead + " " + verdict + caveat + today


def build(repo_root: Path) -> dict:
    seal_path = repo_root / SEAL
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    result = probe(repo_root)
    verdicts = result["verdicts"]
    aggregate = _aggregate(verdicts)
    return {
        "schema": SCHEMA,
        "prerequisite": "P2",
        "design": "docs/DESIGN-session-ledger.md",
        "design_clause": seal["design_clause"],
        "built_by": "scripts/probe_separator_expressibility.py",
        "builder_digest": file_digest(Path(__file__)),
        "determinism": (
            "artifact committed from a deterministic runner; reproductions "
            "welcome and recorded (ROADMAP-v0.21 §4.0(2))"
        ),
        "seal": {
            "source_file": SEAL,
            "file_digest": file_digest(seal_path),
            "digest_algorithm": (
                "sha256 over the file's bytes with CRLF normalised to LF"
            ),
            "frozen_at": seal["frozen_at"],
            "prompt_count": len(seal["prompts"]),
            "reading_count": sum(
                len(prompt["candidate_readings"]) for prompt in seal["prompts"]
            ),
            "sealed_before_the_probe_existed": True,
            "how_a_reader_checks_that": (
                "the seal is its own commit, earlier than this artifact's; "
                "tests/test_session_prereqs.py recomputes file_digest over "
                "the committed seal and compares"
            ),
            "prompts": seal["prompts"],
        },
        "method": {
            "served_digest": (
                "sha256 over the served verdict's "
                + ", ".join(SERVED_KEYS)
                + " — the echoed input `line` is EXCLUDED, because every "
                "reading is a different string by construction and digesting "
                "the echo would separate everything and measure nothing"
            ),
            "act_digest": (
                "sha256 over route and status only: whether the system did a "
                "different thing, as opposed to said different words"
            ),
            "boot": (
                "one fresh CoreSession per line, offline=True (P-IH1's "
                "forced-absent boot), so no optional archive on this "
                "workstation can move a number"
            ),
            "gated_rows_are_kept": (
                "a reading whose grammar row needs an unregistered subsystem "
                "is served anyway and marked row_served_on_this_boot: false, "
                "rather than dropped"
            ),
        },
        "boot_registered_subsystems": result["registered"],
        "verdicts": verdicts,
        "aggregate": aggregate,
        "answer_to_the_incumbents_question": _answer(aggregate, verdicts),
        "not_a_gate": (
            "P2 is a measurement with no floor and no failing side. Both "
            "answers were publishable before the first line ran, and the "
            "artifact is committed either way (DESIGN-session-ledger §6 P2)."
        ),
        "what_this_does_not_claim": [
            "no completeness over readings — the candidate sets are one "
            "author's, and DESIGN-session-ledger §11 forbids the claim",
            "no stranger-usability claim: the prompts are "
            "maintainer-authored and STRANGER's park is cited, not "
            "re-encountered",
            "no claim that a person could answer the clarifying question a "
            "separator licenses; expressibility is not answerability",
            "no claim about slice 2's proposer, which does not exist",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=ARTIFACT)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    payload = build(REPO)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    out = REPO / args.out
    if args.check:
        try:
            existing = out.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"MISSING: {out}: {exc}")
            return 1
        if existing != text:
            print(f"DRIFT: recomputed {args.out} differs from the committed file")
            return 1
        print(f"P2 OK: {args.out} reproduces byte-identically")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(f"wrote {args.out}")
    for key, value in payload["aggregate"].items():
        print(f"  {key}: {value}")
    print()
    print(payload["answer_to_the_incumbents_question"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
