#!/usr/bin/env python3
"""B10: every uptake receipt regenerates from the sealed input, byte for byte.

``docs/DESIGN-protocol-uptake.md`` §7's B10:

    The checker regenerates every receipt from the sealed input and obtains
    byte-identical records. Missing and extra uptake records fail set
    equality; the checker may not validate only records the runtime chose to
    emit.

and §6 step 4 requires this file **committed before the runtime exists**. That
ordering is the whole point of the instrument: a replay checker written after
the runtime is a checker shaped by what the runtime happened to emit. So this
file imports ``scripts/protocol_runtime.py`` at call time and reports a
missing runtime as one named failure — at the commit that introduces this
checker, that named failure is the correct and expected output.

It is distinct from ``scripts/check_protocol_regeneration.py``, which is
U-P0's *corpus* regeneration checker (B1). That one asks whether the sealed
artifacts still equal what the builder emits; this one asks whether a
receipts artifact still equals what the runtime emits.

Set equality, not spot-checking
-------------------------------

The comparison is over the **multiset** of canonical records:

* a record in the artifact that the replay does not produce is an **extra**;
* a record the replay produces that the artifact does not carry is
  **missing** — including a record the runtime emitted and the writer dropped;
* a record present twice in one and once in the other is a count mismatch.

DESIGN §10 stops the slice on "a checker that cannot detect an omitted
receipt", so the missing arm is checked first and reported by uptake id.

The replay is not a re-derivation of what the artifact contains: it calls
``protocol_runtime.replay_registered_pass`` on the sealed fixtures, which is
the same function the gates runner calls to produce the artifact. There is one
definition of what a registered pass emits, and both sides read it.

Usage
-----

    python scripts/check_protocol_receipts.py
    python scripts/check_protocol_receipts.py --receipts experiments/protocol_uptake_receipts.json

Exit 0 clean, exit 1 with a named failure.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]

FIXTURES = REPO / "experiments" / "protocol_uptake_fixtures.json"
RECEIPTS = REPO / "experiments" / "protocol_uptake_receipts.json"
RUNTIME_MODULE = "scripts/protocol_runtime.py"
RECEIPT_SCHEMA = "corollary.protocol-uptake/1"


class Failures(list):
    """Named failures, in the order they were found."""

    def add(self, name: str, detail: str) -> None:
        self.append((name, detail))
        print(f"  FAIL [{name}] {detail}")


def load_runtime(failures: Failures):
    """Import the runtime at call time; a missing module is a named failure."""

    if str(REPO / "scripts") not in sys.path:
        sys.path.insert(0, str(REPO / "scripts"))
    try:
        import protocol_runtime  # noqa: PLC0415
    except ImportError as exc:
        failures.add(
            "missing-runtime",
            f"{RUNTIME_MODULE} could not be imported ({exc}). This checker is "
            f"committed before the runtime by DESIGN §6 step 4, so this is the "
            f"expected failure until the runtime lands.",
        )
        return None
    for name in ("replay_registered_pass", "canonical_record", "recompute_uptake_id"):
        if not hasattr(protocol_runtime, name):
            failures.add(
                "runtime-interface",
                f"{RUNTIME_MODULE} does not expose {name}(); B10 replays through "
                f"that interface and cannot substitute its own",
            )
            return None
    return protocol_runtime


def load_artifact(path: Path, failures: Failures) -> list[dict[str, Any]] | None:
    """A receipts artifact: a JSON list of records, or an object carrying one."""

    if not path.exists():
        failures.add("missing-receipts", f"{path} does not exist")
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.add("unreadable-receipts", f"{path} is not JSON: {exc}")
        return None
    if isinstance(document, list):
        return document
    if isinstance(document, dict) and isinstance(document.get("receipts"), list):
        return document["receipts"]
    failures.add(
        "unreadable-receipts",
        f"{path} is neither a list of ProtocolUptake records nor an object with a "
        f"'receipts' list",
    )
    return None


def check_wellformed(records: list[dict[str, Any]], runtime, failures: Failures) -> None:
    """Every record carries the schema and its own digest rule."""

    before = len(failures)
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            failures.add("record-shape", f"record {index} is not an object")
            continue
        if record.get("schema") != RECEIPT_SCHEMA:
            failures.add(
                "record-schema",
                f"record {index} carries schema {record.get('schema')!r}, not "
                f"{RECEIPT_SCHEMA!r}",
            )
            continue
        recomputed = runtime.recompute_uptake_id(record)
        if record.get("uptake_id") != recomputed:
            failures.add(
                "uptake-id",
                f"record {index} ({record.get('session_id')}/{record.get('turn_id')}) "
                f"carries uptake_id {record.get('uptake_id')}, the canonical digest "
                f"of the record with uptake_id empty is {recomputed}",
            )
        if "timestamp" in record or "generated_at" in record:
            failures.add(
                "record-clock",
                f"record {index} carries a clock field; a replayable receipt has none",
            )
    if len(failures) == before:
        print(f"  well-formed OK: {len(records)} records carry {RECEIPT_SCHEMA} and their own digest")


def check_set_equality(
    artifact: list[dict[str, Any]], replayed: list[dict[str, Any]], runtime, failures: Failures
) -> None:
    """Multiset equality over canonical records. Missing fails; extra fails."""

    def index(records: list[dict[str, Any]]) -> tuple[Counter, dict[str, dict[str, Any]]]:
        counter: Counter = Counter()
        by_canonical: dict[str, dict[str, Any]] = {}
        for record in records:
            canonical = runtime.canonical_record(record)
            counter[canonical] += 1
            by_canonical.setdefault(canonical, record)
        return counter, by_canonical

    have, have_rows = index(artifact)
    want, want_rows = index(replayed)

    def name(record: dict[str, Any]) -> str:
        return (
            f"{record.get('session_id')}/{record.get('turn_id')} "
            f"[{record.get('disposition')}] {record.get('uptake_id', '')[:12]}"
        )

    missing = sorted(
        (canonical for canonical in want if want[canonical] > have.get(canonical, 0)),
        key=lambda canonical: name(want_rows[canonical]),
    )
    extra = sorted(
        (canonical for canonical in have if have[canonical] > want.get(canonical, 0)),
        key=lambda canonical: name(have_rows[canonical]),
    )
    for canonical in missing:
        failures.add(
            "missing-record",
            f"the runtime regenerates {name(want_rows[canonical])} "
            f"({want[canonical]}x) but the artifact carries it "
            f"{have.get(canonical, 0)}x",
        )
    for canonical in extra:
        failures.add(
            "extra-record",
            f"the artifact carries {name(have_rows[canonical])} "
            f"({have[canonical]}x) but the runtime regenerates it "
            f"{want.get(canonical, 0)}x",
        )
    if not missing and not extra:
        print(
            f"  set equality OK: {len(artifact)} artifact records and "
            f"{len(replayed)} regenerated records are the same multiset of "
            f"canonical bytes"
        )


def check_order(
    artifact: list[dict[str, Any]], replayed: list[dict[str, Any]], runtime, failures: Failures
) -> None:
    """Emission order is a fact about the pass, so it is reported, not assumed.

    Order is *not* part of B10's set-equality clause; a run that emitted the
    same records in another order still replays. It is reported because a
    reordering is worth seeing when the sets agree.
    """

    if len(artifact) != len(replayed):
        return
    same = all(
        runtime.canonical_record(left) == runtime.canonical_record(right)
        for left, right in zip(artifact, replayed)
    )
    print(f"  emission order {'matches' if same else 'DIFFERS (set equality still holds)'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fixtures", type=Path, default=FIXTURES)
    parser.add_argument("--receipts", type=Path, default=RECEIPTS)
    args = parser.parse_args(argv)

    print("protocol receipt replay check (DESIGN-protocol-uptake §7 B10)")
    failures = Failures()

    runtime = load_runtime(failures)
    if runtime is None:
        print(f"protocol receipt replay: FAILED ({len(failures)} named failure(s))")
        return 1

    if not args.fixtures.exists():
        failures.add("missing-fixtures", f"{args.fixtures} does not exist")
        print(f"protocol receipt replay: FAILED ({len(failures)} named failure(s))")
        return 1

    artifact = load_artifact(args.receipts, failures)
    if artifact is None:
        print(f"protocol receipt replay: FAILED ({len(failures)} named failure(s))")
        return 1

    fixtures = json.loads(args.fixtures.read_text(encoding="utf-8"))
    replayed = runtime.replay_registered_pass(fixtures)

    check_wellformed(artifact, runtime, failures)
    check_set_equality(artifact, replayed, runtime, failures)
    check_order(artifact, replayed, runtime, failures)

    if failures:
        print(f"protocol receipt replay: FAILED ({len(failures)} named failure(s))")
        return 1
    print("protocol receipt replay: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
