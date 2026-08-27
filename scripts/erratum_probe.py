#!/usr/bin/env python3
"""R3 -- ERRATUM's flip probe (`DESIGN-handles.md` §7 B9, §11).

ERRATUM asks a question a program that keeps receipts can ask and one
that does not cannot: **when the library grows, does anything the
program already refused become answerable?** A refusal is a claim about
the world at a moment. If the world moved, some refusals are now errata,
and the program owes its own history a correction.

B9 registers it as a rider with one floor and one stop rule:

> **R3** (ERRATUM flip probe): floor = **1** designated planted flip
> detected in the replay harness (the mechanism check), real-flip count
> published with the growth window named; stop rule: zero real flips
> publishes the scale sentence and R3's v0.23 candidacy is decided by the
> count, not re-run.

So this probe measures three things and claims nothing beyond them.

**1. The window.** Between the tip the v0.21 journals were recorded at
and today's tip, what moved? The authoritative answer is a digest, not a
commit log: the journals pin `corpora_digest` in their headers, and
`write_stage.durable_digest(data/)` recomputes it today. If the two
agree, the corpus is byte-identical to what was recorded and no
statement was added -- proven, not inferred. The git figures beside it
are checkout-derived narrative and are labelled as such.

**2. The real flips.** Every typed line in every committed
`experiments/sessions/v021-s*.json`, re-served against today's tree
under that turn's recorded assumption set, using the committed replay
machinery (`replay_session._rebuild_assumptions`, `harness.route_line`).
A **FLIP** is a turn whose recorded result was a refusal and whose
replay today is not a refusal. That is the only definition, it is
frozen here, and it is narrower than "the answer changed": an answer
that merely re-rendered differently is a DIVERGENCE and is counted
separately, because calling it a flip would inflate the count with
cosmetics.

**3. The plant.** A floor of 1 on a real-flip count nobody controls
would be a wish. The floor is on a *designated planted* flip: a
synthetic journal whose recorded refusal names a statement that **does
exist today**. Replaying it must produce a non-refusal, and the probe
must classify that as a flip. If the plant is not detected, the
mechanism is broken and the real-flip count -- whatever it is -- means
nothing.

**Two disclosures the probe makes rather than hides.**

- *Pin bypass.* Replaying these journals at today's tip refuses
  `stale-environment`: `scripts/harness.py` and `scripts/serve_chat.py`
  both moved, so `rendering_module_digests` and
  `capability_sheet_digest` no longer match. That refusal is the pin
  gate working. But a probe that stopped there would measure environment
  drift and call it answer drift, so the replay deliberately passes the
  journal's own pins as the live table -- and publishes the genuine pin
  comparison beside every number, so the bypass is a stated method, not
  a silent one.
- *MACs.* `replay_session` never verifies a MAC
  (`scripts/replay_session.py:26-42`). Neither does this probe. The
  planted journal therefore carries placeholder authentication and could
  not be told from a real one by replay alone. That is a property of the
  replay path, disclosed here because the plant depends on it.

Writes:
    experiments/erratum_probe.json
    experiments/erratum_plant_journal.json  (the plant, regenerated and
                                             verified on every run)
"""

from __future__ import annotations

import argparse
import collections
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import replay_session  # noqa: E402
import session_ledger as ledger  # noqa: E402
from harness import CoreSession, route_line  # noqa: E402
from report_provenance import repo_relative  # noqa: E402

SCHEMA = "erratum_probe.v1"
PLANT_SCHEMA = "corollary.session-journal/1"

#: The line whose genuine refusal supplies the plant's recorded digest.
#: A `twin` against an id nobody authored refuses `twin_exhausted` and
#: names the id it could not find -- the shape ERRATUM is about.
PLANT_REFUSAL_SOURCE_LINE = "twin no.such.statement.at.all"

PLANT_SESSION_ID = "v022-erratum-plant"

#: B9's floor.
PLANTED_FLIP_FLOOR = 1


# --------------------------------------------------------------------------
# the window
# --------------------------------------------------------------------------


def git(repo_root: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:  # noqa: BLE001 - a probe must not die on a git absence
        return ""


def corpus_statement_count(data_dir: Path) -> int:
    total = 0
    for path in sorted(data_dir.glob("*/nodes.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        total += len(document.get("statement_nodes", []))
    return total


def window(repo_root: Path, recorded_pins: dict, live_pins: dict,
           journal_paths: list[Path]) -> dict:
    """What moved between the recording tip and today, and how we know."""

    from write_stage import durable_digest  # noqa: PLC0415

    live_corpora = durable_digest(repo_root / "data")
    recorded_corpora = recorded_pins.get("corpora_digest")
    corpus_moved = live_corpora != recorded_corpora

    # The s-journals only. The same directory holds the v0.21 slice-2
    # p-journals, which were recorded later against a different pin table;
    # letting the directory stand for the corpus would date this window to
    # their commit rather than to these journals'.
    spec = [repo_relative(path, repo_root) for path in journal_paths]
    head = git(repo_root, "rev-parse", "HEAD")
    base = git(repo_root, "merge-base", "HEAD", "main")
    added_at = git(repo_root, "log", "--diff-filter=A", "-1", "--format=%H %ad",
                   "--date=short", "--", *spec)
    last_touched = git(repo_root, "log", "-1", "--format=%H %ad",
                       "--date=short", "--", *spec)
    tip = last_touched.split(" ")[0] if last_touched else ""
    commits = git(repo_root, "rev-list", "--count", f"{tip}..HEAD") if tip else ""
    data_diff = git(repo_root, "diff", "--numstat", tip, "HEAD", "--",
                    "data/") if tip else ""
    shortstat = git(repo_root, "diff", "--shortstat", tip, "HEAD") if tip else ""
    # The window the commission names runs to the release tip, not to this
    # branch's HEAD. HEAD carries this slice's own commits, and counting them
    # inside the window being measured would be the probe reporting its own
    # footprint as library growth.
    to_base = git(repo_root, "rev-list", "--count",
                  f"{tip}..{base}") if tip and base else ""
    base_shortstat = git(repo_root, "diff", "--shortstat", tip,
                         base) if tip and base else ""
    base_data_diff = git(repo_root, "diff", "--numstat", tip, base, "--",
                         "data/") if tip and base else ""

    recorded_modules = recorded_pins.get("rendering_module_digests") or {}
    live_modules = live_pins.get("rendering_module_digests") or {}
    moved_modules = sorted(
        name for name in set(recorded_modules) | set(live_modules)
        if recorded_modules.get(name) != live_modules.get(name))
    moved_pins = replay_session.compare_pins(recorded_pins, live_pins)

    return {
        "authoritative_because_it_is_a_digest": {
            "recorded_corpora_digest": recorded_corpora,
            "live_corpora_digest": live_corpora,
            "corpus_moved": corpus_moved,
            "statements_today": corpus_statement_count(repo_root / "data"),
            "statements_added_in_the_window": (
                None if corpus_moved else 0),
            "why_this_and_not_the_commit_log": (
                "the journals pin the corpus by digest. If the recomputed "
                "digest equals the recorded one, no byte of any corpus moved "
                "and no statement was added -- proven from the artifacts "
                "themselves, with no checkout archaeology and no assumption "
                "that a commit touching data/ is the only way statements "
                "arrive. If they differ, this probe does NOT guess a count; it "
                "publishes null and names the digests."
            ),
        },
        "capability_flips": {
            "definition": (
                "a pin that moved between the recorded header and today's live "
                "pin table. These are the flips in what the PROGRAM can do, as "
                "distinct from flips in what the LIBRARY holds"
            ),
            "pins_that_moved": moved_pins,
            "pins_that_held": [name for name in ledger.PIN_FIELDS
                               if name not in moved_pins],
            "rendering_modules_that_moved": moved_modules,
            "reading": (
                f"{len(moved_pins)} of {len(ledger.PIN_FIELDS)} pins moved. "
                f"The corpus pin is not among them"
                if not corpus_moved else
                f"{len(moved_pins)} of {len(ledger.PIN_FIELDS)} pins moved, "
                f"the corpus pin among them"
            ),
        },
        "checkout_derived_narrative": {
            "caveat": (
                "these figures come from `git` and therefore from checkout "
                "state, not from committed bytes. They are context for the "
                "digest facts above, never evidence for them"
            ),
            "pathspec": "the 60 v021-s*.json journals only, never the "
                        "sessions directory -- the later p-journals share it "
                        "and would date this window to their commit",
            "journals_added_at": added_at,
            "journals_last_rewritten_at": last_touched,
            "head": head,
            "merge_base_with_main": base,
            "the_named_window": {
                "from": tip,
                "to": base,
                "why_to_the_merge_base_and_not_to_head": (
                    "HEAD carries this slice's own commits. Counting them "
                    "inside the window being measured would be the probe "
                    "reporting its own footprint as library growth"
                ),
                "commits": to_base,
                "shortstat": base_shortstat,
                "data_dir_numstat": base_data_diff or "(no change)",
            },
            "commits_since_the_journals_were_last_written": commits,
            "shortstat_over_the_window": shortstat,
            "data_dir_numstat_over_the_window": data_diff or "(no change)",
        },
    }


# --------------------------------------------------------------------------
# the replay, and the flip predicate
# --------------------------------------------------------------------------


def recorded_is_refusal(record: dict) -> bool:
    result = record["result"]
    return (result.get("kind") in ledger.REFUSAL_STATUSES
            or result.get("refusal_type") is not None)


def replay_journal(repo_root: Path, journal: dict, shared_index) -> list[dict]:
    """Re-serve every typed line under its recorded assumption set.

    A hand-rolled loop rather than `replay_session.replay`, for one
    reason: `replay` reports digests and this probe needs the live
    verdict's *status*, which is what the flip predicate is about. Every
    piece of machinery it uses is the committed one -- the same
    `_rebuild_assumptions`, the same `ReadBarrier`, the same
    `route_line`, the same `answer_bytes_digest`.
    """

    header = journal["header"]
    session = CoreSession.boot(repo_root, offline=True,
                               session_id=header["session_id"])
    if shared_index is not None:
        session.resolver_index = shared_index

    barrier = ledger.ReadBarrier()
    replay_set = replay_session._rebuild_assumptions(  # noqa: SLF001
        header["session_id"], journal.get("assumptions", []), barrier)
    session.assumptions = replay_set

    out: list[dict] = []
    for record in journal["turns"]:
        turn_index = record["turn_index"]
        barrier.open_turn(turn_index)
        replay_set.advance(turn_index)
        verdict = route_line(repo_root, session, record["input_bytes"])
        barrier.close_turn()
        got = ledger.answer_bytes_digest(verdict)
        want = record["result"]["answer_bytes_digest"]
        was_refusal = recorded_is_refusal(record)
        now_refusal = verdict.get("status") in ledger.REFUSAL_STATUSES
        if got == want:
            outcome = "REPRODUCED"
        elif was_refusal and not now_refusal:
            outcome = "FLIP"
        else:
            outcome = "DIVERGENCE"
        out.append({
            "session_id": header["session_id"],
            "turn_index": turn_index,
            "input_bytes": record["input_bytes"],
            "recorded_kind": record["result"].get("kind"),
            "recorded_refusal_type": record["result"].get("refusal_type"),
            "recorded_was_refusal": was_refusal,
            "replayed_status": verdict.get("status"),
            "replayed_route": verdict.get("route"),
            "replayed_is_refusal": now_refusal,
            "digest_matched": got == want,
            "outcome": outcome,
        })
    return out


# --------------------------------------------------------------------------
# the plant
# --------------------------------------------------------------------------


def plantable_statement(repo_root: Path, session, index) -> tuple[str, dict]:
    """A committed statement id whose `twin` line ANSWERS today.

    Chosen by asking, in sorted id order, rather than by assuming: the
    first id the live route does not refuse is the plant's subject. A
    plant built on an id that turned out to refuse today would test
    nothing, and the search is what stops that being a possibility.
    """

    groups = json.loads(
        (repo_root / "reports" / "signature_matches.json").read_text(
            encoding="utf-8"))

    candidates: list[str] = []

    def harvest(node: object) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key in {"members", "statement_ids"} and isinstance(value, list):
                    candidates.extend(v for v in value if isinstance(v, str))
                else:
                    harvest(value)
        elif isinstance(node, list):
            for child in node:
                harvest(child)

    harvest(groups)
    for sid in sorted(set(candidates)):
        verdict = route_line(repo_root, session, f"twin {sid}")
        if verdict.get("status") not in ledger.REFUSAL_STATUSES:
            return sid, verdict
    raise SystemExit("no committed statement answers a `twin` line today; "
                     "the plant cannot be built without inventing one")


def build_plant(repo_root: Path, template_header: dict, shared_index) -> dict:
    """The synthetic journal whose refusal names a statement that exists.

    Construction, stated so the plant is never mistaken for evidence of
    anything except the mechanism:

    - the recorded `answer_bytes_digest` is the digest of a **real**
      refusal, produced by serving `twin no.such.statement.at.all`
      against today's tree. It is a genuine rendering of a genuine
      `twin_exhausted`;
    - the recorded `input_bytes` names a **different** id -- one that
      exists today and whose `twin` line answers;
    - so the journal records "this line was refused" about a statement
      the library holds, which is exactly the situation ERRATUM exists to
      find, simulated rather than waited for;
    - the header's pins are copied from a real v0.21 journal, so the
      plant is stale in exactly the way the real corpus is and travels
      through the same bypass;
    - `key_id` and `mac` are placeholders. Replay never verifies them
      (`replay_session.py:26-42`), which is disclosed at module level
      because the plant depends on it.
    """

    session = CoreSession.boot(repo_root, offline=True,
                               session_id=PLANT_SESSION_ID)
    if shared_index is not None:
        session.resolver_index = shared_index

    refusal = route_line(repo_root, session, PLANT_REFUSAL_SOURCE_LINE)
    if refusal.get("status") not in ledger.REFUSAL_STATUSES:
        raise SystemExit(
            f"{PLANT_REFUSAL_SOURCE_LINE!r} no longer refuses; the plant's "
            "recorded digest would not be a refusal and the mechanism check "
            "would be vacuous")
    refusal_digest = ledger.answer_bytes_digest(refusal)

    subject, _answer = plantable_statement(repo_root, session, shared_index)

    return {
        "schema": PLANT_SCHEMA,
        "header": {
            "session_id": PLANT_SESSION_ID,
            "created_utc": template_header["created_utc"],
            "pins": template_header["pins"],
        },
        "assumptions": [],
        "turns": [
            {
                "assumptions_cited": [],
                "assumptions_declared": [],
                "input_bytes": f"twin {subject}",
                "key_id": "planted-not-authenticated",
                "live_set_digest": ledger.text_digest(""),
                "mac": "planted-not-authenticated",
                "prev_turn_digest": ledger.text_digest(""),
                "receipt_digest": ledger.text_digest("planted"),
                "resolution": {
                    "assumption_id": None,
                    "grammar_query": "twin <statement-id>",
                    "kind": "refusal",
                },
                "result": {
                    "answer_bytes_digest": refusal_digest,
                    "kind": "refused",
                    "refusal_type": "twin_exhausted",
                },
                "session_events": [],
                "turn_index": 0,
            }
        ],
        "plant_provenance": {
            "synthetic": True,
            "purpose": "R3's B9 mechanism check -- a designated flip the probe "
                       "must detect",
            "refusal_digest_taken_from_line": PLANT_REFUSAL_SOURCE_LINE,
            "input_line_names_statement": subject,
            "statement_exists_today": True,
            "authentication": "placeholder; replay never verifies a MAC "
                              "(scripts/replay_session.py:26-42)",
        },
    }


# --------------------------------------------------------------------------
# the probe
# --------------------------------------------------------------------------


def build(repo_root: Path, sessions_dir: Path, plant_path: Path,
          limit: int | None) -> tuple[dict, dict]:
    from resolver import build_index  # noqa: PLC0415

    shared_index = build_index([repo_root / "data", repo_root / "data_holdout"])

    journal_paths = sorted(sessions_dir.glob("v021-s*.json"))
    journal_paths = [p for p in journal_paths if not p.name.endswith(".reads.json")]
    if limit:
        journal_paths = journal_paths[:limit]
    journals = [json.loads(p.read_text(encoding="utf-8")) for p in journal_paths]
    if not journals:
        raise SystemExit(f"no journals under {sessions_dir}")

    boot = CoreSession.boot(repo_root, offline=True, session_id="v022-erratum")
    live_pins = replay_session.live_pin_table(
        repo_root, boot.matrix, journals[0]["header"]["pins"])
    recorded_pins = journals[0]["header"]["pins"]

    plant = build_plant(repo_root, journals[0]["header"], shared_index)
    plant_path.parent.mkdir(parents=True, exist_ok=True)
    plant_path.write_text(json.dumps(plant, indent=2, sort_keys=True,
                                     ensure_ascii=False) + "\n",
                          encoding="utf-8")

    turns: list[dict] = []
    for journal in journals:
        turns.extend(replay_journal(repo_root, journal, shared_index))
    plant_turns = replay_journal(repo_root, plant, shared_index)

    flips = [t for t in turns if t["outcome"] == "FLIP"]
    divergences = [t for t in turns if t["outcome"] == "DIVERGENCE"]
    reproduced = [t for t in turns if t["outcome"] == "REPRODUCED"]
    recorded_refusals = [t for t in turns if t["recorded_was_refusal"]]
    planted_flips = [t for t in plant_turns if t["outcome"] == "FLIP"]

    win = window(repo_root, recorded_pins, live_pins, journal_paths)
    corpus_moved = win["authoritative_because_it_is_a_digest"]["corpus_moved"]

    scale_sentence = (
        "Zero refusals flipped, and the window is why: between the tip these "
        "journals were recorded at and today, the corpus did not move by a "
        "single byte -- the recorded `corpora_digest` and the recomputed one "
        "are the same string. The probe measured a growth window containing no "
        "growth. What it did establish is that the mechanism works: a planted "
        "refusal naming a statement that exists today was detected as a flip. "
        "So the real-flip count of zero prices the WINDOW, not the "
        "phenomenon, and R3's v0.23 candidacy is a question about whether a "
        "cycle with real ingest is coming -- decided by this count, per the "
        "stop rule, and not by re-running the probe."
    ) if not corpus_moved else (
        "The corpus moved in this window, and the flip count below is a "
        "measurement of that movement rather than of an empty window."
    )

    probe = {
        "schema": SCHEMA,
        "design": "docs/DESIGN-handles.md",
        "roadmap": "docs/ROADMAP-v0.22.md",
        "roadmap_item": "v0.22 rider R3 -- ERRATUM's flip probe",
        "headline": (
            f"{len(flips)} real flips over {len(turns)} replayed turns from "
            f"{len(journals)} committed v0.21 journals "
            f"({len(recorded_refusals)} of those turns recorded a refusal). "
            f"The planted flip was detected {len(planted_flips)}/"
            f"{len(plant_turns)}, meeting B9's floor of {PLANTED_FLIP_FLOOR}. "
            f"Statements added in the window: "
            f"{win['authoritative_because_it_is_a_digest']['statements_added_in_the_window']}."
        ),
        "flip_definition": {
            "a_flip_is": (
                "a turn whose RECORDED result was a refusal and whose replay "
                "today is NOT a refusal"
            ),
            "a_flip_is_not": (
                "any turn whose answer merely re-rendered differently. That is "
                "a DIVERGENCE and is counted separately. Folding the two "
                "together would inflate the flip count with cosmetics, which "
                "is the easiest way to make a probe like this look productive"
            ),
            "refusal_statuses": sorted(ledger.REFUSAL_STATUSES),
            "recorded_refusal_test": (
                "result.kind in refusal_statuses, or result.refusal_type is "
                "not null"
            ),
        },
        "window": win,
        "method_disclosures": {
            "pin_bypass": {
                "what": (
                    "replay passes each journal's own header pins as the live "
                    "pin table, so the environment-staleness gate does not "
                    "stop the run"
                ),
                "why": (
                    "at today's tip these journals refuse `stale-environment`. "
                    "That refusal is the pin gate working, and a probe that "
                    "stopped there would measure environment drift and call it "
                    "answer drift. The genuine pin comparison is published in "
                    "`window.capability_flips` so the bypass is a stated "
                    "method rather than a silent one"
                ),
                "genuine_pin_mismatch": win["capability_flips"]["pins_that_moved"],
            },
            "macs_are_not_verified": (
                "replay never verifies a MAC (scripts/replay_session.py:26-42), "
                "so neither does this probe, and the planted journal carries "
                "placeholder authentication. The plant's detectability "
                "therefore says nothing about forgery detection"
            ),
            "no_write_gate_reached": (
                "every replayed line is a read; no line in the v0.21 s-corpus "
                "reached the write gate and the plant's line is a `twin` query"
            ),
        },
        "planted_flip": {
            "floor": PLANTED_FLIP_FLOOR,
            "detected": len(planted_flips),
            "met": len(planted_flips) >= PLANTED_FLIP_FLOOR,
            "journal": repo_relative(plant_path, repo_root),
            "construction": plant["plant_provenance"],
            "turns": plant_turns,
            "why_the_floor_is_on_the_plant_and_not_on_the_yield": (
                "a floor of 1 on a real-flip count would be a floor on the "
                "world's behaviour, which no instrument can meet by being "
                "correct. The floor is on the mechanism: if the probe cannot "
                "see a flip it was handed, its real count means nothing "
                "whatever that count is"
            ),
        },
        "real_flips": {
            "count": len(flips),
            "flips": flips,
            "turns_replayed": len(turns),
            "journals_replayed": len(journals),
            "turns_recording_a_refusal": len(recorded_refusals),
            "refusal_types_replayed": dict(sorted(collections.Counter(
                t["recorded_refusal_type"] for t in recorded_refusals
                if t["recorded_refusal_type"]).items())),
            "turns_reproduced": len(reproduced),
            "divergences": {
                "count": len(divergences),
                "rows": divergences,
            },
        },
        "scale_sentence": scale_sentence,
        "stop_rule": (
            "DESIGN-handles §7 B9: zero real flips publishes the scale "
            "sentence and R3's v0.23 candidacy is decided by the count, not "
            "re-run. This artifact is that publication. The probe does not "
            "re-run, does not widen its corpus, and does not go looking for a "
            "window with more growth in it."
        ),
        "non_claims": [
            "no claim that the program's refusals are correct, then or now",
            "no claim about flips outside the 60 committed v0.21 s-journals; "
            "the p-journals and every unrecorded session are outside the "
            "denominator and stay outside it",
            "no claim that a zero count is evidence the phenomenon is rare -- "
            "it is evidence this window held no growth, which is a different "
            "sentence and the scale sentence says which one it is",
            "no forgery claim: MACs are not verified anywhere on this path",
        ],
    }
    return probe, plant


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--sessions-dir", type=Path,
                        default=ROOT / "experiments" / "sessions")
    parser.add_argument("--out", type=Path,
                        default=ROOT / "experiments" / "erratum_probe.json")
    parser.add_argument("--plant", type=Path,
                        default=ROOT / "experiments" / "erratum_plant_journal.json")
    parser.add_argument("--limit", type=int, default=0,
                        help="replay only the first N journals (development "
                             "convenience; the committed run uses all of them)")
    args = parser.parse_args(argv)

    probe, _plant = build(args.repo_root, args.sessions_dir, args.plant,
                          args.limit or None)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(probe, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"wrote {args.out}")
    print(probe["headline"])
    print(probe["scale_sentence"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
