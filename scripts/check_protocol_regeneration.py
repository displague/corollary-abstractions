#!/usr/bin/env python3
"""The protocol corpus and its fixture seal must equal what the builder emits.

``docs/DESIGN-protocol-uptake.md`` §3 puts the generated protocol corpus at
``protocol/protocols.json``, deliberately **outside** ``data/`` — so
``scripts/check_regeneration.py``, whose whole subject is the two corpus roots
and their ``seed_*.py`` owners, cannot and must not reach it. A generated file
no checker owns is a file that drifts, which is why §3 requires *this*
dedicated checker committed at U-P0 and §7's B1 makes it the source-truth gate.

What it does, in order, each with a named failure:

1. **Regeneration.** Runs ``scripts/build_protocol_corpus.py`` twice into a
   temporary directory — never into the repository, so a check can never be
   the thing that writes the artifact it checks — and byte-compares both
   outputs against the committed files. A direct edit of either generated file
   is DESIGN §10's stop condition and shows up here as a byte difference.
2. **Digests.** Every ``frozen`` row of ``experiments/protocol_uptake_prereg
   .json`` is checked against the live file with ``prereg_pins.sha256_lf``,
   the digest convention every prereg in this repository records.
3. **Recomputation.** ``c_surface``, ``c_position``, and the position-switch
   control's table-agreement are recomputed **from the sealed table committed
   in the fixtures file** — not from the corpus, and not from the builder's
   own report — and compared with the numbers frozen in the prereg. B1: "a
   mismatch is a construction bug, not a leak."
4. **Structural invariants.** The nine properties U-P0 seals, each recomputed
   from the committed artifacts.

Exit 0 clean, exit 1 with a named failure.

Usage
-----

    python scripts/check_protocol_regeneration.py

Joins the release skill's step-1 regeneration list in the release that commits
it (DESIGN §12).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from prereg_pins import sha256_lf  # noqa: E402

BUILDER = REPO / "scripts" / "build_protocol_corpus.py"
CORPUS = REPO / "protocol" / "protocols.json"
FIXTURES = REPO / "experiments" / "protocol_uptake_fixtures.json"
PREREG = REPO / "experiments" / "protocol_uptake_prereg.json"
UPRE = REPO / "experiments" / "protocol_uptake_upre.json"

REFUSED = "REFUSED"
STACK_EMPTY = "empty"


def deleted_at_upre() -> list[str]:
    """The input fields the audit deleted, read from the audit itself.

    Never spelled here. A checker that hardcoded the two names would carry
    them in its own bytes, and invariant (i) — "they appear nowhere" — would
    fire on the file enforcing it. The audit stays the one place they are
    written down.
    """

    audit = json.loads(UPRE.read_text(encoding="utf-8"))
    return [
        row["field"].split(".")[-1].replace("[]", "")
        for row in audit["audit"]
        if row["verdict"] == "DELETED"
    ]


def surviving_at_upre() -> dict[str, list[str]]:
    audit = json.loads(UPRE.read_text(encoding="utf-8"))
    return audit["survivors"]


class Failures(list):
    """Named failures, in the order they were found."""

    def add(self, name: str, detail: str) -> None:
        self.append((name, detail))
        print(f"  FAIL [{name}] {detail}")


# --------------------------------------------------------------------------
# 1. Regeneration into a tempdir.
# --------------------------------------------------------------------------


def check_regeneration(failures: Failures) -> None:
    before = len(failures)
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    with tempfile.TemporaryDirectory(prefix="protocol-regen-") as tmp:
        tmpdir = Path(tmp)
        pairs = (
            ("corpus", ["--out", str(tmpdir / "protocols.json")], tmpdir / "protocols.json", CORPUS),
            (
                "fixtures",
                ["--fixtures", str(tmpdir / "fixtures.json")],
                tmpdir / "fixtures.json",
                FIXTURES,
            ),
        )
        for role, args, produced, committed in pairs:
            run = subprocess.run(
                [sys.executable, str(BUILDER), *args],
                cwd=REPO,
                capture_output=True,
                text=True,
                env=env,
            )
            if run.returncode != 0:
                failures.add(
                    f"builder-{role}",
                    f"the builder exited {run.returncode}: "
                    f"{(run.stderr or run.stdout).strip()[-400:]}",
                )
                continue
            if not committed.exists():
                failures.add(f"missing-{role}", f"{committed.relative_to(REPO)} is not committed")
                continue
            fresh = produced.read_bytes()
            on_disk = committed.read_bytes()
            if fresh != on_disk:
                failures.add(
                    f"drift-{role}",
                    f"{committed.relative_to(REPO)} differs from a fresh regeneration "
                    f"({len(on_disk)} committed bytes vs {len(fresh)} regenerated); "
                    f"the seed in the builder is source truth",
                )
    if len(failures) == before:
        print("  regeneration OK: both generated artifacts are byte-identical")


# --------------------------------------------------------------------------
# 2. The prereg's frozen digests.
# --------------------------------------------------------------------------


def check_digests(prereg: dict[str, Any], failures: Failures) -> None:
    before = len(failures)
    for row in prereg.get("frozen", ()):
        path = REPO / row["path"]
        if not path.exists():
            failures.add("frozen-missing", f"{row['path']} is pinned but absent")
            continue
        observed = sha256_lf(path)
        if observed != row["sha256_lf"]:
            failures.add(
                "frozen-digest",
                f"{row['path']} ({row['role']}) is {observed}, prereg pins "
                f"{row['sha256_lf']}",
            )
    if len(failures) == before:
        print(f"  digests OK: {len(prereg.get('frozen', ()))} frozen rows agree with sha256_lf")


# --------------------------------------------------------------------------
# 3. Recompute the two ceilings and the position-switch agreement from the
#    sealed table committed in the fixtures file.
# --------------------------------------------------------------------------


def sealed_grid(fixtures: dict[str, Any]) -> list[list[str]]:
    return [[cell["label"] for cell in row["cells"]] for row in fixtures["sealed_table"]]


def recompute_c_surface(fixtures: dict[str, Any]) -> int:
    return sum(max(Counter(row).values()) for row in sealed_grid(fixtures))


def recompute_c_position(fixtures: dict[str, Any]) -> int:
    return sum(max(Counter(col).values()) for col in zip(*sealed_grid(fixtures)))


def recompute_position_switch_agreement(fixtures: dict[str, Any]) -> int:
    agree = 0
    for row in fixtures["sealed_table"]:
        for cell in row["cells"]:
            predicted = "greeting" if cell["position_id"] == "fresh_root" else REFUSED
            agree += int(predicted == cell["label"])
    return agree


def check_numbers(prereg: dict[str, Any], fixtures: dict[str, Any], failures: Failures) -> None:
    before = len(failures)
    frozen = prereg["frozen_numbers"]
    recomputed = {
        "c_surface": recompute_c_surface(fixtures),
        "c_position": recompute_c_position(fixtures),
        "position_switch_agreement": recompute_position_switch_agreement(fixtures),
    }
    for name, value in recomputed.items():
        if frozen.get(name) != value:
            failures.add(
                f"number-{name}",
                f"the sealed table recomputes {name} = {value}, prereg freezes "
                f"{frozen.get(name)!r}; B1 calls a mismatch a construction bug",
            )
    if fixtures["ceilings"]["c_surface"] != recomputed["c_surface"]:
        failures.add("number-c_surface-fixtures", "the fixtures file's own c_surface disagrees")
    if fixtures["ceilings"]["c_position"] != recomputed["c_position"]:
        failures.add("number-c_position-fixtures", "the fixtures file's own c_position disagrees")
    if (
        fixtures["position_switch_control"]["frozen_table_agreement"]
        != recomputed["position_switch_agreement"]
    ):
        failures.add(
            "number-position_switch-fixtures",
            "the fixtures file's own frozen_table_agreement disagrees",
        )
    if len(failures) == before:
        print(
            "  numbers OK: c_surface={c_surface} c_position={c_position} "
            "position_switch_agreement={position_switch_agreement}".format(**recomputed)
        )


# --------------------------------------------------------------------------
# 4. The structural invariants.
# --------------------------------------------------------------------------


def entry_witnesses(corpus: dict[str, Any], surface: str) -> list[dict[str, str]]:
    return [w for w in corpus["lookup"].get(surface, ()) if w["move_kind"] == "entry"]


def move_of(corpus: dict[str, Any], protocol_id: str, move_id: str) -> dict[str, Any]:
    node = next(n for n in corpus["nodes"] if n["protocol_id"] == protocol_id)
    return next(m for m in node["moves"] if m["move_id"] == move_id)


def predicate_holds(predicate, signals: dict[str, str]) -> bool:
    return all(
        row["signal_id"] in signals and signals[row["signal_id"]] == row["required_value"]
        for row in predicate
    )


def family_entry_predicate(corpus: dict[str, Any], family: str):
    for node in corpus["nodes"]:
        if node["family"] != family:
            continue
        for move in node["moves"]:
            if move["kind"] == "entry":
                return move["required_signal_predicates"]
    return None


def check_invariants(
    corpus: dict[str, Any], fixtures: dict[str, Any], failures: Failures
) -> None:
    before = len(failures)
    products = list(fixtures["product_surfaces"])
    positions = {p["position_id"]: p for p in fixtures["positions"]}

    # (a) each PRODUCT surface matches at most one node per family.
    for surface in products:
        per_family: dict[str, set[str]] = {}
        for witness in entry_witnesses(corpus, surface):
            per_family.setdefault(witness["relation"], set()).add(witness["protocol_node_id"])
        for family, node_ids in sorted(per_family.items()):
            if len(node_ids) > 1:
                failures.add(
                    "invariant-a",
                    f"product surface {surface!r} matches {len(node_ids)} nodes in "
                    f"family {family!r}; a 32 cell could become a two-next_state ASK",
                )

    # (b) ASK and equivalence keys are disjoint from the 8 product surfaces.
    extras = {row["surface"] for row in fixtures["ask_surfaces"]} | {
        row["surface"] for row in fixtures["equivalence_surfaces"]
    }
    overlap = sorted(extras & set(products))
    if overlap:
        failures.add("invariant-b", f"ASK/equivalence surfaces overlap the product surfaces: {overlap}")

    # (c) entry predicates are pairwise exclusive across families on the four positions.
    preds = {f: family_entry_predicate(corpus, f) for f in corpus["families"]}
    for position_id, position in positions.items():
        signals = dict(position["signals"])
        signals["protocol_stack"] = STACK_EMPTY
        holding = sorted(f for f, p in preds.items() if p and predicate_holds(p, signals))
        if len(holding) > 1:
            failures.add(
                "invariant-c",
                f"entry predicates of {holding} both hold at {position_id!r}",
            )

    # (d) at least two product surfaces take two different SELECTED moves.
    switching = []
    for row in fixtures["sealed_table"]:
        selected = {
            (cell["protocol_id"], cell["move_id"])
            for cell in row["cells"]
            if cell["label"] != REFUSED
        }
        if len(selected) >= 2:
            switching.append(row["surface"])
    if len(switching) < 2:
        failures.add(
            "invariant-d",
            f"only {len(switching)} surface(s) take two different selected moves across "
            f"positions; 'same utterance, different moves' is not constructed",
        )
    if switching != fixtures["surfaces_taking_two_different_selected_moves"]:
        failures.add(
            "invariant-d-recorded",
            f"the fixtures record {fixtures['surfaces_taking_two_different_selected_moves']} "
            f"as switching surfaces; recomputation says {switching}",
        )

    # (e) both ceilings < 24 and < 32 (DESIGN §6's two meetable degeneracy bounds).
    for name in ("c_surface", "c_position"):
        value = fixtures["ceilings"][name]
        if value >= 32:
            failures.add("invariant-e", f"{name} = {value}/32: that view is a sufficient statistic")
        elif value >= 24:
            failures.add(
                "invariant-e",
                f"{name} = {value}/32 >= 24: at least as separable as the exclusive-home shape",
            )

    # (f) at least 2 ASK fixtures, and all four expect WAITING.
    asks = [f for f in fixtures["fixtures"] if f["kind"] == "ask"]
    if len(asks) < 2:
        failures.add("invariant-f", f"{len(asks)} ASK fixtures sealed; B6 needs at least two")
    if len(asks) != 4:
        failures.add("invariant-f-count", f"{len(asks)} ASK fixtures sealed; the design seals four")
    not_waiting = [
        f["fixture_id"]
        for f in asks
        if f.get("expected_state") != "WAITING" or f.get("expected_disposition") != "ASK"
    ]
    if not_waiting:
        failures.add("invariant-f-waiting", f"ASK fixtures that do not stop WAITING: {not_waiting}")

    # (g) deepest nested-fixture depth is exactly two.
    nested = [f for f in fixtures["fixtures"] if f["kind"] == "nested"]
    if len(nested) != 8:
        failures.add("invariant-g-count", f"{len(nested)} nested fixtures; the design seals eight")
    depths = [
        max(turn["expected_depth_after"] for turn in f["turns"]) for f in nested
    ] or [0]
    if max(depths) != 2:
        failures.add(
            "invariant-g",
            f"the eight nested fixtures reach depth {max(depths)}; the cap of "
            f"{corpus['stack_depth_cap']} is four times a deepest of two",
        )

    # (h) the equivalence pair's four-field projections coincide.
    for fixture in fixtures["fixtures"]:
        if fixture["kind"] != "equivalence":
            continue
        digests = {c["next_state_sha256"] for c in fixture["turns"][0]["candidates"]}
        move_ids = sorted(c["move_id"] for c in fixture["turns"][0]["candidates"])
        if len(digests) != 1:
            failures.add(
                "invariant-h",
                f"{fixture['fixture_id']}: candidates {move_ids} group to {len(digests)} "
                f"next_state digests; the proceed-without-asking leg has no fixture",
            )
        if fixture["expected_move_id"] != min(move_ids):
            failures.add(
                "invariant-h-canonical",
                f"{fixture['fixture_id']} selects {fixture['expected_move_id']!r}, not the "
                f"canonical lowest {min(move_ids)!r}",
            )
        recomputed = {
            _digest(
                {
                    "protocol_id": c["protocol_id"],
                    "stack_after": c["next_state"]["stack_after"],
                    "pending_request_id": None,
                    "authority_delta": [],
                }
            )
            for c in fixture["turns"][0]["candidates"]
        }
        if recomputed != digests:
            failures.add(
                "invariant-h-digest",
                f"{fixture['fixture_id']}: the recorded next_state_sha256 is not the "
                f"sha256 of the canonical four-field projection",
            )

    # (i) the fields U-PRE deleted appear nowhere in what U-P0 commits. The
    #     audit that deleted them is the one file exempt: it is where they are
    #     named.
    deleted = deleted_at_upre()
    for label, path in (
        ("corpus", CORPUS),
        ("fixtures", FIXTURES),
        ("prereg", PREREG),
        ("builder", BUILDER),
        ("checker", Path(__file__).resolve()),
    ):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for name in deleted:
            if name in text:
                failures.add(
                    "invariant-i",
                    f"{label} names {name!r}, which U-PRE deleted; no schema U-P0 seals "
                    f"may carry it",
                )

    # The survivor lists U-P0 records are exactly the audit's.
    survivors = surviving_at_upre()
    if corpus["context_signal_ids"] != survivors["context_signals"]:
        failures.add(
            "invariant-i-survivors",
            f"the corpus records context signals {corpus['context_signal_ids']}, the "
            f"audit's survivors are {survivors['context_signals']}",
        )
    if corpus["protocol_witness_fields"] != survivors["protocol_witness_fields"]:
        failures.add(
            "invariant-i-survivors",
            f"the corpus records witness fields {corpus['protocol_witness_fields']}, the "
            f"audit's survivors are {survivors['protocol_witness_fields']}",
        )

    if len(failures) == before:
        print("  invariants OK: (a) through (i)")


def _digest(obj: Any) -> str:
    import hashlib

    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


# --------------------------------------------------------------------------


def main() -> int:
    failures = Failures()
    for path in (BUILDER, CORPUS, FIXTURES, PREREG):
        if not path.exists():
            failures.add("missing-artifact", f"{path.relative_to(REPO)} does not exist")
    if failures:
        print("protocol regeneration: FAILED")
        return 1

    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))

    print("protocol corpus regeneration check (DESIGN-protocol-uptake §7 B1)")
    check_regeneration(failures)
    check_digests(prereg, failures)
    check_numbers(prereg, fixtures, failures)
    check_invariants(corpus, fixtures, failures)

    if failures:
        print(f"protocol regeneration: FAILED ({len(failures)} named failure(s))")
        return 1
    print("protocol regeneration: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
