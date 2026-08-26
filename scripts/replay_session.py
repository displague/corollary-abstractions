#!/usr/bin/env python3
"""Replay a recorded session, or refuse because the world moved.

`docs/DESIGN-session-ledger.md` §3: *"Tool: `scripts/replay_session.py` →
`replay_report` {`turns_total`, `turns_reproduced`, `first_divergence_turn`,
`pin_mismatch[]`}. Any pin mismatch yields a typed `stale-environment`
refusal, never a guess."*

## What replay is, and what it is not

Replay re-serves each recorded line, in order, into a session rebuilt from
the journal's Assumption records, and compares `answer_bytes_digest`. It
re-verifies **the record**. It does not verify that any answer was *right*:
§10 says it plainly and this file repeats it because it is the sentence a
reader most wants to skip — *sessions are reproducible, not correct, and a
wrong answer replays as faithfully as a right one.*

This is P5's corrected guarantee. `DESIGN-v010-harness-session.md` P5 asked
for byte-exact session re-run and was adjudicated **MISSED IN KIND**,
because *"a session that mutates the corpus cannot re-run byte-identically,
because the second run meets a different world"*
(`session_run.py:22-30`). What makes it askable now is scope plus pins: no
recorded turn may reach the write gate (§6 P3's no-write-gate-turn rule),
and every environment fact that moved bytes since v0.10 is digest-pinned.

## Stale environment is a refusal, not a lower score

Every pin is compared before a single line is replayed, and any mismatch
ends the run with `refusal: "stale-environment"` and the mismatching fields
named. Replaying anyway and reporting a low reproduction rate would be the
instrument reporting the environment as a defect in the record.

## The capability-blind baseline lives here too

`--stateless` is §8's vacuity control: a replayer that re-serves each line
ignoring Assumption records entirely. It must pass on assumption-free
sessions and must score 0 on B4's mutations — *"by construction, not by
hope"*, because B4 mutates only the Assumption record and never the
declaring line's `input_bytes`, which is all the stateless arm ever reads.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

import session_ledger as ledger  # noqa: E402
from harness import CoreSession, route_line  # noqa: E402

STALE = "stale-environment"


@dataclass
class ReplayReport:
    """§3's `replay_report`, field names included."""

    turns_total: int = 0
    turns_reproduced: int = 0
    first_divergence_turn: int | None = None
    pin_mismatch: list[str] = field(default_factory=list)
    refusal: str | None = None
    session_id: str = ""
    stateless: bool = False
    divergences: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "turns_total": self.turns_total,
            "turns_reproduced": self.turns_reproduced,
            "first_divergence_turn": self.first_divergence_turn,
            "pin_mismatch": list(self.pin_mismatch),
            "refusal": self.refusal,
            "stateless": self.stateless,
            "divergences": list(self.divergences),
        }

    @property
    def reproduced_everything(self) -> bool:
        return (
            self.refusal is None
            and self.turns_total > 0
            and self.turns_reproduced == self.turns_total
        )


def compare_pins(recorded: dict, live: dict) -> list[str]:
    """Which pin fields disagree. Every pin, no sampling (B3)."""

    mismatched = []
    for name in ledger.PIN_FIELDS:
        if recorded.get(name) != live.get(name):
            mismatched.append(name)
    for name in sorted(set(recorded) - set(ledger.PIN_FIELDS)):
        # A pin the journal carries and this build does not know about is a
        # mismatch too. Silently ignoring an unknown pin would make the pin
        # table's own growth invisible to B3.
        mismatched.append(name)
    return mismatched


def _rebuild_assumptions(
    session_id: str, records: list[dict], barrier: ledger.ReadBarrier
) -> ledger.AssumptionSet:
    """Rebuild the live set from the journal's Assumption records.

    Rebuilt from the RECORDS, never re-derived from the declaring lines:
    that is what makes B4 possible at all. A mutated Assumption record must
    reach the replayed answer without the declaring turn's `input_bytes`
    changing, and a replayer that re-parsed the line would be reading the
    transcript instead of the assumption — the exact confusion §8's voiding
    sentence exists to catch.

    Status is applied as the record carries it, and status is a function of
    turn order: a record `retracted` at the end of the session must be LIVE
    while the turns before the retraction replay. So the set is rebuilt
    incrementally by the replay loop through :meth:`_ReplaySet.advance`
    rather than restored whole at the start.
    """

    return _ReplaySet(session_id, barrier, records)


class _ReplaySet(ledger.AssumptionSet):
    """An AssumptionSet driven by a journal instead of by typed lines."""

    def __init__(
        self, session_id: str, barrier: ledger.ReadBarrier, records: list[dict]
    ) -> None:
        super().__init__(session_id, barrier)
        self._records = list(records)

    def advance(self, turn_index: int) -> None:
        """Admit every assumption declared at or before `turn_index`.

        A declaration becomes live on the turn that declared it and stays
        live until a later turn supersedes or retracts it. Supersession is
        replayed from `superseded_by`, and retraction is replayed by the
        `retract` line itself when it comes round — so the only thing this
        method does is bring declarations into scope on time.
        """

        for record in self._records:
            if record["declared_at_turn"] > turn_index:
                continue
            if record["assumption_id"] in self._by_id:
                continue
            self._by_id[record["assumption_id"]] = ledger.Assumption(
                assumption_id=record["assumption_id"],
                declared_at_turn=record["declared_at_turn"],
                text_bytes=record["text_bytes"],
                normal_form=tuple(record["normal_form"]),
                status="live",
                superseded_by=None,
                key_id=record.get("key_id", ""),
                mac=record.get("mac", ""),
            )
            self._order.append(record["assumption_id"])

    def declare(self, text: str, turn_index: int):
        """A declaring line, replayed against the record it produced.

        The recorder's `declare` MINTS an assumption; replay must ADMIT the
        one the journal already holds, or a mutated record would be shadowed
        by a fresh one re-derived from the declaring line — and re-deriving
        from the line is precisely the transcript-reading confusion §8's
        voiding sentence exists to catch. `advance` has already brought this
        turn's record into scope, so all that is left is supersession.

        Matched on `declared_at_turn` alone, never on `text_bytes`: B4
        mutates `text_bytes`, and a match that consulted it would make the
        mutated record unfindable, which would look like insensitivity when
        it was really a lookup failure.
        """

        from dataclasses import replace  # noqa: PLC0415

        for record in self._records:
            if record["declared_at_turn"] != turn_index:
                continue
            item = self._by_id.get(record["assumption_id"])
            if item is None:
                continue
            for key in self._order:
                other = self._by_id[key]
                if (
                    key != item.assumption_id
                    and other.status == "live"
                    and other.subject == item.subject
                ):
                    self._by_id[key] = replace(
                        other,
                        status="superseded",
                        superseded_by=item.assumption_id,
                    )
            return item
        # No record for this turn: the journal and the lines disagree. Fall
        # back to the recorder's own behaviour rather than inventing one, so
        # the divergence shows up as a divergence instead of as a crash.
        return super().declare(text, turn_index)


def replay(
    repo_root: Path,
    journal: dict,
    *,
    stateless: bool = False,
    shared_index=None,
    live_pins: dict | None = None,
) -> ReplayReport:
    header = journal["header"]
    session_id = header["session_id"]
    report = ReplayReport(session_id=session_id, stateless=stateless)

    session = CoreSession.boot(repo_root, offline=True, session_id=session_id)
    if shared_index is not None:
        session.resolver_index = shared_index

    pins_now = (
        live_pins
        if live_pins is not None
        else ledger.pins(repo_root, session.matrix)
    )
    report.pin_mismatch = compare_pins(header["pins"], pins_now)
    if report.pin_mismatch:
        report.refusal = STALE
        report.turns_total = len(journal["turns"])
        return report

    barrier = ledger.ReadBarrier()
    replay_set = None
    if not stateless:
        replay_set = _rebuild_assumptions(
            session_id, journal["assumptions"], barrier
        )
        session.assumptions = replay_set

    for record in journal["turns"]:
        turn_index = record["turn_index"]
        report.turns_total += 1
        barrier.open_turn(turn_index)
        if replay_set is not None:
            replay_set.advance(turn_index)
        verdict = route_line(repo_root, session, record["input_bytes"])
        barrier.close_turn()
        got = ledger.answer_bytes_digest(verdict)
        want = record["result"]["answer_bytes_digest"]
        if got == want:
            report.turns_reproduced += 1
            continue
        if report.first_divergence_turn is None:
            report.first_divergence_turn = turn_index
        report.divergences.append(
            {
                "turn_index": turn_index,
                "input_bytes": record["input_bytes"],
                "recorded_digest": want,
                "replayed_digest": got,
                "replayed_status": verdict.get("status"),
                "replayed_route": verdict.get("route"),
            }
        )
    return report


def load_journal(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("journal", help="path to a journal under experiments/sessions/")
    ap.add_argument(
        "--stateless",
        action="store_true",
        help="§8's capability-blind baseline: ignore Assumption records",
    )
    args = ap.parse_args(argv)

    report = replay(
        REPO, load_journal(Path(args.journal)), stateless=args.stateless
    )
    print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    if report.refusal == STALE:
        print(
            f"REFUSED: {STALE} — "
            + ", ".join(report.pin_mismatch)
            + "; nothing was replayed and nothing is claimed",
            file=sys.stderr,
        )
        return 2
    return 0 if report.reproduced_everything else 1


if __name__ == "__main__":
    raise SystemExit(main())
