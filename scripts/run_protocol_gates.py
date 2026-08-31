#!/usr/bin/env python3
"""The registered run: B1-B6, B8-B10 scored, B7 reported PENDING_AMD3.

``docs/DESIGN-protocol-uptake.md`` §7 is the construction gate, §8 is the
blind control and the voiding sentence, §9 is R-U1. Every number this script
compares against was frozen in ``experiments/protocol_uptake_prereg.json``
before ``scripts/protocol_runtime.py`` existed; nothing here may adjust a
sealed fixture, and a disagreement with one is reported, never repaired.

Two artifacts, raw before compact
---------------------------------

§12: *"If implemented, raw uptake receipts land before compact metrics."* So
this writer emits ``experiments/protocol_uptake_receipts.json`` — every raw
``ProtocolUptake`` record the registered pass emitted — and only then
``experiments/protocol_uptake_run.json``, the gate verdicts computed over
them. B10 runs against the receipts file on disk, so the compact artifact
cannot claim a replay of records the raw artifact does not carry.

Both paths are refused if they already exist. A registered run that can
overwrite its own evidence is not registered.

The scoring tree
----------------

§6 step 4: *"The result writer refuses an existing output path and a dirty or
wrong-tip scoring tree."* Dirty is ``git status --porcelain``. **Wrong-tip**
is this slice's own construction order made checkable: the B10 receipt-replay
checker and the deliberately broken controls must have been committed
**before** the runtime they measure. A tree where the runtime landed first is
a tree where the instrument could have been shaped by the thing it measures,
and this writer refuses to score it.

``--allow-dirty`` exists for pre-run testing only. It never changes a verdict;
it records ``registered_before_the_run: false`` in the artifact, and every
sentence in §9 is gated on that flag being false.

B7 is not scored here
---------------------

B7 is the tool-wire round trip on the ``corollary/protocol`` profile, which
AMD-3 registers. AMD-3 is not implemented at this commit, so B7 is reported
``PENDING_AMD3``: not green, not red, and not fabricated from the text
fallback — §7 forbids reporting it green from the text WAITING path, and R-U2
is not licensed.

Usage
-----

    python scripts/run_protocol_gates.py
    python scripts/run_protocol_gates.py --out /tmp/run.json --receipts-out /tmp/receipts.json --allow-dirty
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

import protocol_controls as controls  # noqa: E402
import protocol_runtime as runtime  # noqa: E402
from prereg_pins import sha256_lf  # noqa: E402

RUN_SCHEMA = "corollary.protocol-uptake-run/1"
DESIGN = "docs/DESIGN-protocol-uptake.md"
PREREG = "experiments/protocol_uptake_prereg.json"
FIXTURES = "experiments/protocol_uptake_fixtures.json"
CORPUS = "protocol/protocols.json"
HOST_CAPTURE = "experiments/protocol_uptake_host_capture.json"
RECEIPTS_OUT = "experiments/protocol_uptake_receipts.json"
RUN_OUT = "experiments/protocol_uptake_run.json"

REGENERATION_CHECKER = "scripts/check_protocol_regeneration.py"
REPLAY_CHECKER = "scripts/check_protocol_receipts.py"
CONTROLS = "scripts/protocol_controls.py"
RUNTIME_MODULE = "scripts/protocol_runtime.py"
BUILDER = "scripts/build_protocol_corpus.py"
THIS = "scripts/run_protocol_gates.py"

# The gates this run scores. B7 is reported, not scored.
SCORED_GATES = ("B1", "B2", "B3", "B4", "B5", "B6", "B8", "B9", "B10")
PENDING_GATES = ("B7",)

REFUSED = "REFUSED"
ASK = "ASK"
DATA_TREES = ("data", "staging")


class RunRefusal(RuntimeError):
    """The run may not proceed. Never a gate verdict — a refusal to score."""


# --------------------------------------------------------------------------
# The scoring tree.
# --------------------------------------------------------------------------


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    ).stdout.strip()


def _first_commit(path: str) -> str | None:
    lines = [
        line.strip()
        for line in _git("log", "--format=%H", "--diff-filter=A", "--reverse", "--", path).splitlines()
        if line.strip()
    ]
    return lines[0] if lines else None


def _is_ancestor(earlier: str, later: str) -> bool:
    return (
        subprocess.run(
            ["git", "-C", str(REPO), "merge-base", "--is-ancestor", earlier, later],
            capture_output=True,
            timeout=120,
        ).returncode
        == 0
    )


def scoring_tree(allow_dirty: bool) -> dict[str, Any]:
    """Refuse a dirty or wrong-tip tree; record what was checked either way."""

    status = _git("status", "--porcelain", "--untracked-files=all")
    dirty = [line for line in status.splitlines() if line.strip()]

    registration_inputs = [
        PREREG,
        FIXTURES,
        CORPUS,
        BUILDER,
        REGENERATION_CHECKER,
        REPLAY_CHECKER,
        CONTROLS,
        RUNTIME_MODULE,
        THIS,
    ]
    commits = {path: _first_commit(path) for path in registration_inputs}
    uncommitted = sorted(path for path, commit in commits.items() if commit is None)

    # DESIGN §6 step 4's construction order, as a fact about the tree.
    instrument_first = None
    if commits[REPLAY_CHECKER] and commits[CONTROLS] and commits[RUNTIME_MODULE]:
        instrument_first = all(
            commits[instrument] == commits[RUNTIME_MODULE]
            or _is_ancestor(commits[instrument], commits[RUNTIME_MODULE])
            for instrument in (REPLAY_CHECKER, CONTROLS)
        )

    tree = {
        "head_commit": _git("rev-parse", "HEAD") or None,
        "dirty": bool(dirty),
        "dirty_entries": dirty[:40],
        "uncommitted_registration_inputs": uncommitted,
        "first_commit_of": commits,
        "instrument_committed_before_the_runtime": instrument_first,
        "wrong_tip": bool(uncommitted) or instrument_first is not True,
        "how_checked": (
            "git status --porcelain for dirty; the commits that INTRODUCED the "
            "B10 checker, the controls, and the runtime, compared with git "
            "merge-base --is-ancestor, for the construction order DESIGN §6 "
            "step 4 requires"
        ),
        "allow_dirty": allow_dirty,
    }
    # A rehearsal never counts as registered, even on a tree that happens to
    # be clean: the module docstring promises --allow-dirty "records
    # registered_before_the_run: false", and the v0.24 suite gate's run 1
    # caught this line computing it from tree state alone.
    tree["registered_before_the_run"] = (
        not tree["dirty"] and not tree["wrong_tip"] and not allow_dirty
    )
    if not tree["registered_before_the_run"] and not allow_dirty:
        if tree["dirty"]:
            raise RunRefusal(
                f"the registered run scores only a clean tree; {len(dirty)} entry(ies) "
                f"are dirty, first: {dirty[0]!r}"
            )
        if uncommitted:
            raise RunRefusal(
                f"registration inputs are not committed: {', '.join(uncommitted)}"
            )
        raise RunRefusal(
            "wrong-tip tree: DESIGN §6 step 4 commits the B10 checker and the "
            "broken controls BEFORE the runtime, and this tree does not"
        )
    return tree


def refuse_existing(path: Path, role: str) -> None:
    if path.exists():
        raise RunRefusal(f"registered {role} artifact already exists: {path}")


def write_once(path: Path, document: dict[str, Any]) -> None:
    """Create the artifact; an existing path is never replaced."""

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(document, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    except FileExistsError as exc:
        raise RunRefusal(f"registered artifact already exists: {path}") from exc


# --------------------------------------------------------------------------
# Process-start and data-tree instrumentation (B8).
# --------------------------------------------------------------------------


class ProcessWatch:
    """Counts process-creation audit events while armed.

    B8 requires *zero process starts*. Asserting that by reading the runtime's
    imports would be a claim about source; this counts the interpreter's own
    audit events, which is a claim about the run.
    """

    PREFIXES = ("subprocess.", "os.system", "os.exec", "os.fork", "os.spawn", "os.posix_spawn")

    def __init__(self) -> None:
        self.armed = False
        self.events: list[str] = []
        sys.addaudithook(self._hook)

    def _hook(self, event: str, args) -> None:  # pragma: no cover - hook path
        if self.armed and event.startswith(self.PREFIXES):
            self.events.append(event)

    def __enter__(self) -> "ProcessWatch":
        self.events = []
        self.armed = True
        return self

    def __exit__(self, *exc) -> None:
        self.armed = False


def tree_digest(root: Path) -> str:
    """One digest over a directory's bytes and names. Missing tree digests empty."""

    digest = hashlib.sha256()
    if root.exists():
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            digest.update(path.relative_to(root).as_posix().encode("utf-8"))
            digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


# --------------------------------------------------------------------------
# Reading the pass.
# --------------------------------------------------------------------------


class Pass:
    """One registered pass over the sealed fixtures, plus its B9 mutant runs."""

    def __init__(self, fixtures: dict[str, Any], corpus: dict[str, Any]) -> None:
        self.fixtures = fixtures
        self.corpus = corpus
        self.by_id = {f["fixture_id"]: f for f in fixtures["fixtures"]}
        self.families = {node["protocol_id"]: node["family"] for node in corpus["nodes"]}
        self.sessions = {
            fixture["fixture_id"]: runtime.run_fixture(fixture, corpus)
            for fixture in fixtures["fixtures"]
        }

    def receipts(self, fixture_id: str) -> list[dict[str, Any]]:
        return self.sessions[fixture_id].receipts

    def first(self, fixture_id: str) -> dict[str, Any]:
        return self.sessions[fixture_id].receipts[0]

    def selected_candidate(self, receipt: dict[str, Any]) -> dict[str, Any] | None:
        if receipt["selected_move_id"] is None:
            return None
        rows = [c for c in receipt["candidates"] if c["move_id"] == receipt["selected_move_id"]]
        return rows[0] if len(rows) == 1 else None

    def selected_protocol_id(self, receipt: dict[str, Any]) -> str | None:
        row = self.selected_candidate(receipt)
        return row["protocol_id"] if row else None

    def label(self, receipt: dict[str, Any]) -> str:
        protocol_id = self.selected_protocol_id(receipt)
        return self.families[protocol_id] if protocol_id else REFUSED

    def product_grid(self) -> list[list[str]]:
        return [
            [self.label(self.first(f"ctx-{row['row']}-{cell['col']}")) for cell in row["cells"]]
            for row in self.fixtures["sealed_table"]
        ]


def _verdict(misses: list[str]) -> str:
    return "GREEN" if not misses else "RED"


# --------------------------------------------------------------------------
# B1 — source truth.
# --------------------------------------------------------------------------


def score_b1(prereg: dict[str, Any], fixtures: dict[str, Any]) -> dict[str, Any]:
    misses: list[str] = []
    completed = subprocess.run(
        [sys.executable, str(REPO / REGENERATION_CHECKER)],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=None,
    )
    if completed.returncode != 0:
        misses.append(
            f"{REGENERATION_CHECKER} exited {completed.returncode}: "
            f"{(completed.stdout or completed.stderr).strip().splitlines()[-1:]}"
        )

    sealed = controls.sealed_labels(fixtures)
    columns = controls.position_ids(fixtures)
    recomputed = {
        "c_surface": controls.fit_surface_only(sealed),
        "c_position": controls.fit_position_only(sealed),
        "position_switch_agreement": controls.position_switch_agreement(sealed, columns),
    }
    frozen = prereg["frozen_numbers"]
    for name, value in recomputed.items():
        if frozen.get(name) != value:
            misses.append(
                f"the sealed table recomputes {name}={value}, the prereg freezes "
                f"{frozen.get(name)!r}; B1 calls a mismatch a construction bug"
            )
    return {
        "verdict": _verdict(misses),
        "clause": prereg["gates"]["B1"],
        "regeneration_checker": REGENERATION_CHECKER,
        "regeneration_checker_exit": completed.returncode,
        "regeneration_checker_tail": completed.stdout.strip().splitlines()[-1:],
        "recomputed_from_the_sealed_table": recomputed,
        "frozen_in_the_prereg": frozen,
        "misses": misses,
    }


# --------------------------------------------------------------------------
# B2 — context and corpus change uptake.
# --------------------------------------------------------------------------


def score_b2(run: Pass) -> dict[str, Any]:
    misses: list[str] = []
    rows = []
    for row in run.fixtures["sealed_table"]:
        for cell in row["cells"]:
            fixture_id = f"ctx-{row['row']}-{cell['col']}"
            fixture = run.by_id[fixture_id]
            turn = fixture["turns"][0]
            receipts = run.receipts(fixture_id)
            if len(receipts) != 1:
                misses.append(f"{fixture_id}: {len(receipts)} receipts for one turn")
                continue
            receipt = receipts[0]
            protocol_id = run.selected_protocol_id(receipt)
            candidate = run.selected_candidate(receipt)
            observed = {
                "fixture_id": fixture_id,
                "surface": fixture["surface"],
                "position_id": fixture["position_id"],
                "sealed_label": cell["label"],
                "runtime_label": run.label(receipt),
                "disposition": receipt["disposition"],
                "selected_move_id": receipt["selected_move_id"],
                "selected_protocol_id": protocol_id,
                "stack_after": receipt["stack_after"],
                "witnesses": [w["protocol_node_id"] for w in receipt["protocol_witnesses"]],
            }
            rows.append(observed)
            if receipt["disposition"] != fixture["expected_disposition"]:
                misses.append(
                    f"{fixture_id}: disposition {receipt['disposition']} != sealed "
                    f"{fixture['expected_disposition']}"
                )
            if receipt["selected_move_id"] != fixture["expected_move_id"]:
                misses.append(
                    f"{fixture_id}: move {receipt['selected_move_id']!r} != sealed "
                    f"{fixture['expected_move_id']!r}"
                )
            if protocol_id != fixture["expected_protocol_id"]:
                misses.append(
                    f"{fixture_id}: protocol {protocol_id!r} != sealed "
                    f"{fixture['expected_protocol_id']!r}"
                )
            if run.label(receipt) != cell["label"]:
                misses.append(
                    f"{fixture_id}: family {run.label(receipt)!r} != sealed table "
                    f"{cell['label']!r}"
                )
            if receipt["stack_after"] != turn["expected_stack_after"]:
                misses.append(
                    f"{fixture_id}: stack_after {receipt['stack_after']} != sealed "
                    f"{turn['expected_stack_after']}"
                )
            digest = candidate["next_state_sha256"] if candidate else None
            if digest != fixture["expected_next_state_sha256"]:
                misses.append(
                    f"{fixture_id}: next_state_sha256 {digest} != sealed "
                    f"{fixture['expected_next_state_sha256']}"
                )
            if receipt["protocol_witnesses"] != turn["protocol_witnesses"]:
                misses.append(f"{fixture_id}: protocol_witnesses differ from the seal")
            if receipt["selected_move_id"] is not None and not receipt["protocol_witnesses"]:
                misses.append(f"{fixture_id}: a selected move cites no protocol witness")
            if receipt["authority_delta"] != []:
                misses.append(f"{fixture_id}: authority_delta is not empty")

    # The construction check §7 folds into this gate: the same bytes take two
    # different selected moves, in the runtime's own labels.
    switching = []
    for row in run.fixtures["sealed_table"]:
        selected = {
            (
                run.selected_protocol_id(run.first(f"ctx-{row['row']}-{cell['col']}")),
                run.first(f"ctx-{row['row']}-{cell['col']}")["selected_move_id"],
            )
            for cell in row["cells"]
        } - {(None, None)}
        if len(selected) >= 2:
            switching.append(row["surface"])
    if len(switching) < 2:
        misses.append(
            f"only {len(switching)} surface(s) take two different selected moves in the "
            f"runtime's labels; 'same utterance, different moves' is not shown"
        )
    if switching != run.fixtures["surfaces_taking_two_different_selected_moves"]:
        misses.append(
            f"the runtime's switching surfaces {switching} differ from the sealed "
            f"{run.fixtures['surfaces_taking_two_different_selected_moves']}"
        )

    return {
        "verdict": _verdict(misses),
        "clause": run.fixtures.get("table_generation_rule"),
        "cells": len(rows),
        "cells_matching_the_sealed_table": sum(
            1 for row in rows if row["runtime_label"] == row["sealed_label"]
        ),
        "of": 32,
        "surfaces_taking_two_different_selected_moves": switching,
        "table": rows,
        "misses": misses,
    }


# --------------------------------------------------------------------------
# B3 — ambiguity never guesses.
# --------------------------------------------------------------------------


def score_b3(run: Pass) -> dict[str, Any]:
    misses: list[str] = []
    refusals, asks = [], []
    for fixture in run.fixtures["fixtures"]:
        if fixture["kind"] not in ("refusal", "ask"):
            continue
        fixture_id = fixture["fixture_id"]
        receipt = run.first(fixture_id)
        session = run.sessions[fixture_id]
        row = {
            "fixture_id": fixture_id,
            "corruption": fixture.get("corruption"),
            "disposition": receipt["disposition"],
            "selected_move_id": receipt["selected_move_id"],
            "stack_before": receipt["stack_before"],
            "stack_after": receipt["stack_after"],
            "authority_delta_present": "authority_delta" in receipt,
            "authority_delta": receipt["authority_delta"],
            "verifier_verdict": receipt["verifier_verdict"],
        }
        if receipt["disposition"] != fixture["expected_disposition"]:
            misses.append(
                f"{fixture_id}: disposition {receipt['disposition']} != sealed "
                f"{fixture['expected_disposition']}"
            )
        if receipt["selected_move_id"] is not None:
            misses.append(f"{fixture_id}: a selected move on an {fixture['kind']} path")
        if receipt["stack_after"] != receipt["stack_before"]:
            misses.append(f"{fixture_id}: the stack mutated on an {fixture['kind']} path")
        # §7 B3: emptiness is a plaintext field, not inferred from a digest.
        if "authority_delta" not in receipt or receipt["authority_delta"] != []:
            misses.append(f"{fixture_id}: authority_delta is not present-and-empty")
        if fixture["kind"] == "ask":
            row["need"] = receipt["need"]
            row["waiting"] = session.waiting
            if not session.waiting:
                misses.append(f"{fixture_id}: the session did not stop WAITING")
            if not receipt["need"] or receipt["need"]["slot"] != runtime.NEED_SLOT:
                misses.append(f"{fixture_id}: no need minted on the {runtime.NEED_SLOT} slot")
            elif not receipt["need"]["request_id"]:
                misses.append(f"{fixture_id}: the minted need carries no request_id")
            if receipt["unresolved_move_ids"] != fixture["expected_unresolved_move_ids"]:
                misses.append(
                    f"{fixture_id}: unresolved {receipt['unresolved_move_ids']} != sealed "
                    f"{fixture['expected_unresolved_move_ids']}"
                )
            asks.append(row)
        else:
            if receipt["need"] is not None:
                misses.append(f"{fixture_id}: a refusal minted a need")
            refusals.append(row)

    if len(refusals) != 8:
        misses.append(f"{len(refusals)} refusal fixtures scored; the seal has 8")
    if len(asks) != 4:
        misses.append(f"{len(asks)} ASK fixtures scored; the seal has 4")
    return {
        "verdict": _verdict(misses),
        "refusals": f"{sum(1 for r in refusals if r['disposition'] == REFUSED)}/{len(refusals)}",
        "asks": f"{sum(1 for r in asks if r['disposition'] == ASK)}/{len(asks)}",
        "authority_delta_is_a_plaintext_field": all(
            row["authority_delta_present"] and row["authority_delta"] == []
            for row in refusals + asks
        ),
        "refusal_rows": refusals,
        "ask_rows": asks,
        "misses": misses,
    }


# --------------------------------------------------------------------------
# B4 — lexical control loses.
# --------------------------------------------------------------------------


def score_b4(run: Pass, prereg: dict[str, Any]) -> dict[str, Any]:
    grid = run.product_grid()
    columns = controls.position_ids(run.fixtures)
    frozen = prereg["frozen_numbers"]
    evaluation = controls.voiding_sentence_evaluation(
        grid,
        c_surface=frozen["c_surface"],
        c_position=frozen["c_position"],
        frozen_position_switch_agreement=frozen["position_switch_agreement"],
        positions=columns,
    )
    misses = []
    if evaluation["fired"]:
        misses.append(
            f"the voiding sentence fired on {evaluation['fired_arms']}: the runtime's "
            f"labels are more a function of that view than the sealed table is"
        )
    return {
        "verdict": _verdict(misses),
        "clause": prereg["gates"]["B4"],
        "refit_on_the_runtimes_selected_moves": evaluation,
        "equality_is_not_a_firing": True,
        "runtime_labels": grid,
        "misses": misses,
    }


# --------------------------------------------------------------------------
# B5 — exact nesting.
# --------------------------------------------------------------------------


def score_b5(run: Pass) -> dict[str, Any]:
    misses: list[str] = []
    rows = []
    for fixture in run.fixtures["fixtures"]:
        if fixture["kind"] != "nested":
            continue
        fixture_id = fixture["fixture_id"]
        session = run.sessions[fixture_id]
        receipts = session.receipts
        dispositions = [receipt["disposition"] for receipt in receipts]
        stacks = [receipt["stack_after"] for receipt in receipts]
        if dispositions != fixture["expected_disposition_sequence"]:
            misses.append(
                f"{fixture_id}: dispositions {dispositions} != sealed "
                f"{fixture['expected_disposition_sequence']}"
            )
        if stacks != fixture["expected_stack_after_sequence"]:
            misses.append(
                f"{fixture_id}: stack_after sequence != sealed "
                f"{fixture['expected_stack_after_sequence']}"
            )
        # The active/suspended marks — "resume the exact parent episode" — are
        # session state, compared against the sealed snapshots turn by turn.
        marks_ok = [
            snapshot == turn["expected_stack_after"]
            for snapshot, turn in zip(session.stack_history, fixture["turns"])
        ]
        if not all(marks_ok):
            misses.append(
                f"{fixture_id}: an episode's active/suspended mark differs from the seal"
            )

        # Three arrival-order replays produce byte-identical uptake order.
        canonical = [runtime.canonical_record(receipt) for receipt in receipts]
        replays = []
        for _ in range(fixture.get("arrival_order_replays_required", 3)):
            replay = runtime.run_fixture(fixture, run.corpus)
            replays.append([runtime.canonical_record(r) for r in replay.receipts])
        identical = all(replay == canonical for replay in replays)
        if not identical:
            misses.append(f"{fixture_id}: an arrival-order replay differed byte-wise")

        rows.append(
            {
                "fixture_id": fixture_id,
                "dispositions": dispositions,
                "stack_after_sequence": stacks,
                "deepest_depth": max(len(stack) for stack in stacks),
                "arrival_order_replays": len(replays),
                "replays_byte_identical": identical,
                "episode_marks_reproduced": all(marks_ok),
            }
        )

    if len(rows) != 8:
        misses.append(f"{len(rows)} nested trajectories scored; the seal has 8")

    # A reply for the suspended child may not bind in its parent: the stale
    # replay of an already-consumed request is refused, and nothing moves.
    stale = None
    for fixture in run.fixtures["fixtures"]:
        for turn in fixture["turns"]:
            if turn.get("stale_replay_of_turn") is None:
                continue
            receipt = run.receipts(fixture["fixture_id"])[turn["turn_index"] - 1]
            stale = {
                "fixture_id": fixture["fixture_id"],
                "turn_index": turn["turn_index"],
                "disposition": receipt["disposition"],
                "verifier_verdict": receipt["verifier_verdict"],
                "stack_unchanged": receipt["stack_after"] == receipt["stack_before"],
                "sealed_refusal_reason": turn.get("refusal_reason"),
            }
            if receipt["disposition"] != REFUSED:
                misses.append(
                    f"{fixture['fixture_id']} turn {turn['turn_index']}: a stale reply "
                    f"was admitted as {receipt['disposition']}"
                )
            if receipt["verifier_verdict"] != runtime.CONSUMED_REQUEST:
                misses.append(
                    f"{fixture['fixture_id']} turn {turn['turn_index']}: refused as "
                    f"{receipt['verifier_verdict']}, not against the consumed request"
                )
            if receipt["stack_after"] != receipt["stack_before"]:
                misses.append(
                    f"{fixture['fixture_id']} turn {turn['turn_index']}: the stale reply "
                    f"mutated the stack"
                )
    if stale is None:
        misses.append("no stale-reply turn found in the seal; B5's binding clause is unscored")

    # The depth-nine plant.
    plant = run.by_id["depth9-plant"]
    plant_receipts = run.receipts("depth9-plant")
    final = plant_receipts[-1]
    plant_row = {
        "fixture_id": "depth9-plant",
        "stack_depth_cap": plant["stack_depth_cap"],
        "final_disposition": final["disposition"],
        "verifier_verdict": final["verifier_verdict"],
        "stack_unchanged": final["stack_after"] == final["stack_before"],
        "episodes_at_refusal": len(final["stack_before"]),
    }
    if final["disposition"] != REFUSED:
        misses.append(f"the ninth push was admitted as {final['disposition']}")
    if final["verifier_verdict"] != runtime.DEPTH_CAP:
        misses.append(
            f"the ninth push was refused as {final['verifier_verdict']}, not the depth cap"
        )
    if final["stack_after"] != final["stack_before"]:
        misses.append("the depth-nine refusal mutated the stack")
    if len(final["stack_before"]) != plant["stack_depth_cap"]:
        misses.append(
            f"the plant refused at depth {len(final['stack_before'])}, not at the "
            f"declared cap of {plant['stack_depth_cap']}"
        )

    return {
        "verdict": _verdict(misses),
        "trajectories": f"{len(rows)}/8",
        "rows": rows,
        "stale_reply": stale,
        "depth_nine_plant": plant_row,
        "misses": misses,
    }


# --------------------------------------------------------------------------
# B6 — ask only for material ambiguity.
# --------------------------------------------------------------------------


def score_b6(run: Pass) -> dict[str, Any]:
    misses: list[str] = []
    multi, single, bindings = 0, 0, 0

    def bound_request(receipt: dict[str, Any]) -> str | None:
        for line in receipt["verifier_evidence"]:
            if line.startswith("bound_request:"):
                return line.split(":", 1)[1]
        return None

    for fixture in run.fixtures["fixtures"]:
        session = run.sessions[fixture["fixture_id"]]
        minted = {
            receipt["need"]["request_id"]: receipt
            for receipt in session.receipts
            if receipt["need"] is not None
        }
        for receipt in session.receipts:
            digests = {c["next_state_sha256"] for c in receipt["candidates"]}
            request_id = bound_request(receipt)
            if request_id is not None:
                # A turn that binds a pending need is the *completion* of a
                # pause, not a fresh ambiguity: it carries the deferred
                # candidate set, and the pause it answers was scored on the ASK
                # turn that minted the request. What B6 owes here is that the
                # transition really did go through that pause.
                bindings += 1
                paused = minted.get(request_id)
                if paused is None:
                    misses.append(
                        f"{fixture['fixture_id']}/{receipt['turn_id']}: bound a request "
                        f"this session never minted from an ASK"
                    )
                elif paused["disposition"] != ASK:
                    misses.append(
                        f"{fixture['fixture_id']}/{receipt['turn_id']}: the request it "
                        f"binds was not minted by an ASK"
                    )
                elif {
                    (c["protocol_id"], c["move_id"]) for c in paused["candidates"]
                } != {(c["protocol_id"], c["move_id"]) for c in receipt["candidates"]}:
                    misses.append(
                        f"{fixture['fixture_id']}/{receipt['turn_id']}: the deferred "
                        f"candidate set is not the one that paused"
                    )
                continue
            if len(digests) > 1:
                multi += 1
                if receipt["disposition"] != ASK:
                    misses.append(
                        f"{fixture['fixture_id']}/{receipt['turn_id']}: "
                        f"{len(digests)} distinct next states but disposition "
                        f"{receipt['disposition']}"
                    )
            elif len(digests) == 1:
                single += 1
                if receipt["disposition"] == ASK:
                    misses.append(
                        f"{fixture['fixture_id']}/{receipt['turn_id']}: one next state "
                        f"but the run asked"
                    )

    asks = [f for f in run.fixtures["fixtures"] if f["kind"] == "ask"]
    for fixture in asks:
        receipt = run.first(fixture["fixture_id"])
        digests = sorted({c["next_state_sha256"] for c in receipt["candidates"]})
        if not run.sessions[fixture["fixture_id"]].waiting:
            misses.append(f"{fixture['fixture_id']}: did not stop WAITING")
        if digests != fixture["expected_distinct_next_state_sha256"]:
            # A disagreement with the seal is reported, never repaired.
            misses.append(
                f"{fixture['fixture_id']}: the runtime computes distinct next states "
                f"{digests}, the seal records "
                f"{fixture['expected_distinct_next_state_sha256']}"
            )
    if len(asks) < 2:
        misses.append("fewer than two sealed ASK fixtures; the WAITING arm is empty")

    equivalences = []
    for fixture in run.fixtures["fixtures"]:
        if fixture["kind"] != "equivalence":
            continue
        receipt = run.first(fixture["fixture_id"])
        digests = {c["next_state_sha256"] for c in receipt["candidates"]}
        partition = sorted(
            sorted(c["move_id"] for c in receipt["candidates"] if c["next_state_sha256"] == digest)
            for digest in sorted(digests)
        )
        row = {
            "fixture_id": fixture["fixture_id"],
            "disposition": receipt["disposition"],
            "selected_move_id": receipt["selected_move_id"],
            "candidate_move_ids": sorted(c["move_id"] for c in receipt["candidates"]),
            "unresolved_move_ids": receipt["unresolved_move_ids"],
            "derived_equivalence_partition": partition,
            "shared_next_state_sha256": sorted(digests)[0] if len(digests) == 1 else None,
            "grouping_recorded_in_the_receipt": any(
                line.startswith("grouped_to_one_next_state:") for line in receipt["verifier_evidence"]
            ),
        }
        equivalences.append(row)
        if receipt["disposition"] == ASK:
            misses.append(f"{fixture['fixture_id']}: asked although the candidates agree")
        if receipt["selected_move_id"] != fixture["expected_move_id"]:
            misses.append(
                f"{fixture['fixture_id']}: selected {receipt['selected_move_id']!r}, the "
                f"canonical lowest is {fixture['expected_move_id']!r}"
            )
        if receipt["selected_move_id"] != min(row["candidate_move_ids"]):
            misses.append(f"{fixture['fixture_id']}: not the canonical lowest identifier")
        if partition != fixture["expected_equivalence_partition"]:
            misses.append(
                f"{fixture['fixture_id']}: derived partition {partition} != sealed "
                f"{fixture['expected_equivalence_partition']}"
            )
        if row["shared_next_state_sha256"] != fixture["expected_shared_next_state_sha256"]:
            misses.append(f"{fixture['fixture_id']}: the shared next state differs from the seal")
        if not row["grouping_recorded_in_the_receipt"]:
            misses.append(f"{fixture['fixture_id']}: the receipt does not record the grouping")
        if receipt["unresolved_move_ids"] != sorted(
            set(row["candidate_move_ids"]) - {receipt["selected_move_id"]}
        ):
            misses.append(f"{fixture['fixture_id']}: the equivalent name was not named")
    if len(equivalences) != 2:
        misses.append(f"{len(equivalences)} equivalence fixtures scored; the seal has 2")

    return {
        "verdict": _verdict(misses),
        "turns_with_more_than_one_next_state": multi,
        "turns_with_exactly_one_next_state": single,
        "turns_binding_a_pending_need": bindings,
        "binding_turns_note": (
            "a turn that binds a pending need carries the deferred candidate "
            "set, so it can hold more than one next state without being a fresh "
            "ambiguity. It is scored on the stronger clause instead: the request "
            "it binds must have been minted by an ASK in the same session, with "
            "that exact candidate set. The set is compared by "
            "(protocol_id, move_id), not by next_state_sha256: an episode id is "
            "ep-<turn_index>-<protocol_id>, so a transition deferred at turn n "
            "and completed at turn m mints its episode at m and its next-state "
            "digest legitimately differs from the one that paused"
        ),
        "ask_fixtures_waiting": sum(
            1 for f in asks if run.sessions[f["fixture_id"]].waiting
        ),
        "of_ask_fixtures": len(asks),
        "equivalence_rows": equivalences,
        "partition_note": (
            "the equivalence partition is derived here at check time from "
            "candidates[]; B9 forbids adding a schema field after U-P0"
        ),
        "misses": misses,
    }


# --------------------------------------------------------------------------
# B7 — reported, not scored.
# --------------------------------------------------------------------------


#: The artifact `scripts/run_b7_roundtrip.py` writes after the orchestrator's
#: live Codex round trip. It does not exist until that run happens, and this
#: runner never writes it: B7 is the one gate this repository cannot score
#: from its own code, so the verdict is READ from the instrument that measured
#: it rather than computed here from something that did not.
B7_ARTIFACT = "experiments/protocol_uptake_b7.json"


def report_b7(prereg: dict[str, Any]) -> dict[str, Any]:
    capture_path = REPO / HOST_CAPTURE
    capture = json.loads(capture_path.read_text(encoding="utf-8")) if capture_path.exists() else {}
    tool = capture.get("prompt_tool", {})

    recorded_path = REPO / B7_ARTIFACT
    if recorded_path.exists():
        recorded = json.loads(recorded_path.read_text(encoding="utf-8"))
        verdict = recorded["verdict"]
        return {
            "verdict": verdict,
            "green": verdict == "GREEN",
            "clause": prereg["gates"]["B7"],
            "why": recorded.get("why", ""),
            "recorded_by": recorded.get("instrument"),
            "recorded_in": B7_ARTIFACT,
            "recorded_sha256": sha256_lf(recorded_path),
            "self_check_passed": bool(recorded.get("self_check", {}).get("passed")),
            "live_codex_log": recorded.get("live_codex_log"),
            "u_p1_host_prompt_status": tool.get("host_prompt_status"),
            "u_p1_prompt_tool": tool.get("name"),
            "u_p1_parameters_sha256": tool.get("parameters_sha256"),
            "blocks": "R-U2",
            "does_not_block": "R-U1, which §9 gates on B1-B6 and B8-B10",
            "misses": list(recorded.get("misses", [])),
        }

    return {
        "verdict": "PENDING_AMD3",
        "green": False,
        "clause": prereg["gates"]["B7"],
        "why": (
            "B7 is the tool-wire round trip served on corollary/protocol, the "
            "profile AMD-3 registers. AMD-3 is not implemented at this commit, "
            "so there is no profile to run it against. This is not UNTESTED in "
            "U-P1's sense — U-P1 did capture a compatible prompt tool — and it "
            "is not green: §7 forbids reporting B7 green from the text WAITING "
            "fallback, and no round trip was attempted."
        ),
        "u_p1_host_prompt_status": tool.get("host_prompt_status"),
        "u_p1_prompt_tool": tool.get("name"),
        "u_p1_parameters_sha256": tool.get("parameters_sha256"),
        "blocks": "R-U2",
        "does_not_block": "R-U1, which §9 gates on B1-B6 and B8-B10",
        "misses": [],
    }


# --------------------------------------------------------------------------
# B8 — phrases carry no authority.
# --------------------------------------------------------------------------


def score_b8(run: Pass, watch: ProcessWatch) -> dict[str, Any]:
    fixture = run.by_id["b8-authority-plant"]
    before = {name: tree_digest(REPO / name) for name in DATA_TREES}
    with watch:
        session = runtime.run_fixture(fixture, run.corpus)
    after = {name: tree_digest(REPO / name) for name in DATA_TREES}
    receipt = session.receipts[0]

    misses: list[str] = []
    if receipt["disposition"] != REFUSED:
        misses.append(f"the planted phrase was admitted as {receipt['disposition']}")
    if receipt["selected_move_id"] is not None:
        misses.append("the planted phrase selected a move")
    if receipt["authority_delta"] != []:
        misses.append(f"the planted phrase opened {receipt['authority_delta']}")
    if receipt["candidates"]:
        misses.append("the planted phrase produced candidates")
    if receipt["stack_after"] != receipt["stack_before"]:
        misses.append("the planted phrase mutated the stack")
    changed = sorted(name for name in DATA_TREES if before[name] != after[name])
    if changed:
        misses.append(f"tree bytes changed under {changed}")
    if watch.events:
        misses.append(f"{len(watch.events)} process-creation event(s): {sorted(set(watch.events))}")

    return {
        "verdict": _verdict(misses),
        "planted_surface": fixture["surface"],
        "disposition": receipt["disposition"],
        "verifier_verdict": receipt["verifier_verdict"],
        "authority_delta": receipt["authority_delta"],
        "process_starts": len(watch.events),
        "process_start_events": sorted(set(watch.events)),
        "how_process_starts_were_counted": (
            "sys.addaudithook, counting subprocess./os.exec/os.system/os.fork/"
            "os.spawn events while the planted turn ran — a fact about the run, "
            "not a reading of the runtime's imports"
        ),
        "tree_digests_before": before,
        "tree_digests_after": after,
        "zero_data_tree_byte_changes": not changed,
        "stage_records": 0,
        "how_stage_records_were_counted": (
            "the protocol runtime has no stage-record channel: it opens no "
            "capability and writes no file, and the staging/ tree is digested "
            "before and after the planted turn to show it"
        ),
        "misses": misses,
    }


# --------------------------------------------------------------------------
# B9 — corruption fires.
# --------------------------------------------------------------------------


def score_b9(run: Pass, prereg: dict[str, Any]) -> dict[str, Any]:
    misses: list[str] = []
    rows = []
    sealed = {row["mutant_id"]: row for row in prereg["b9_mutants"]}
    for mutant in run.fixtures["b9_mutants"]:
        mutant_id = mutant["mutant_id"]
        if mutant_id not in sealed:
            misses.append(f"{mutant_id} is not in the prereg's sealed mutant set")
            continue
        for key in ("field", "field_class", "target_fixture", "transformation"):
            if sealed[mutant_id].get(key) != mutant.get(key):
                misses.append(
                    f"{mutant_id}: the fixtures' {key} differs from the prereg's"
                )
        plan = runtime.parse_mutant(mutant)
        fixture = run.by_id[mutant["target_fixture"]]
        baseline = run.receipts(fixture["fixture_id"])
        mutated = runtime.run_fixture(fixture, run.corpus, mutation=plan).receipts
        index = plan.turn_index - 1
        before, after = baseline[index], mutated[index]
        changed_move = before["selected_move_id"] != after["selected_move_id"]
        moved_to_ask_or_refused = after["disposition"] in (ASK, REFUSED) and before[
            "disposition"
        ] not in (ASK, REFUSED)
        validation_failure = after["verifier_verdict"] == runtime.INVALID_INPUT
        fired = changed_move or moved_to_ask_or_refused or validation_failure
        rows.append(
            {
                "mutant_id": mutant_id,
                "field": mutant["field"],
                "target_fixture": mutant["target_fixture"],
                "target_turn_index": plan.turn_index,
                "transformation": mutant["transformation"],
                "sealed_expected_effect": mutant["expected_effect"],
                "baseline": {
                    "disposition": before["disposition"],
                    "selected_move_id": before["selected_move_id"],
                },
                "mutated": {
                    "disposition": after["disposition"],
                    "selected_move_id": after["selected_move_id"],
                    "verifier_verdict": after["verifier_verdict"],
                    "verifier_evidence": after["verifier_evidence"][:2],
                },
                "fired_by": sorted(
                    name
                    for name, value in (
                        ("selected_move_changed", changed_move),
                        ("moved_to_ask_or_refused", moved_to_ask_or_refused),
                        ("validation_failure", validation_failure),
                    )
                    if value
                ),
                "fired": fired,
            }
        )
        if not fired:
            misses.append(
                f"{mutant_id}: the mutation changed nothing — a mutant that cannot "
                f"fire is not a mutant"
            )
    if len(rows) != prereg["fixture_counts"]["b9_mutants"]:
        misses.append(
            f"{len(rows)} mutants scored; the prereg seals "
            f"{prereg['fixture_counts']['b9_mutants']}"
        )
    return {
        "verdict": _verdict(misses),
        "mutants": f"{sum(1 for row in rows if row['fired'])}/{len(rows)} fired",
        "rows": rows,
        "misses": misses,
    }


# --------------------------------------------------------------------------
# B10 — replay.
# --------------------------------------------------------------------------


def score_b10(receipts_path: Path, fixtures_path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            sys.executable,
            str(REPO / REPLAY_CHECKER),
            "--fixtures",
            str(fixtures_path),
            "--receipts",
            str(receipts_path),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    misses = []
    if completed.returncode != 0:
        misses.append(
            f"{REPLAY_CHECKER} exited {completed.returncode}: "
            + " | ".join(
                line.strip()
                for line in completed.stdout.splitlines()
                if line.strip().startswith("FAIL")
            )[:800]
        )
    return {
        "verdict": _verdict(misses),
        "checker": REPLAY_CHECKER,
        "checker_exit": completed.returncode,
        "receipts_artifact": receipts_path.name,
        "checker_output": completed.stdout.strip().splitlines()[-4:],
        "set_equality_note": (
            "the checker replays through protocol_runtime.replay_registered_pass "
            "and compares the multiset of canonical records: a missing record "
            "fails and an extra record fails"
        ),
        "misses": misses,
    }


# --------------------------------------------------------------------------
# The run.
# --------------------------------------------------------------------------


def provenance() -> dict[str, Any]:
    inputs = [
        PREREG,
        FIXTURES,
        CORPUS,
        BUILDER,
        REGENERATION_CHECKER,
        REPLAY_CHECKER,
        CONTROLS,
        RUNTIME_MODULE,
    ]
    return {
        "writer": THIS,
        "writer_sha256_lf": sha256_lf(REPO / THIS),
        "inputs": [
            {"path": path, "sha256_lf": sha256_lf(REPO / path)}
            for path in sorted(inputs)
            if (REPO / path).is_file()
        ],
        "emitted_at_generation": True,
    }


def run(
    *,
    out_path: Path,
    receipts_path: Path,
    fixtures_path: Path,
    allow_dirty: bool,
) -> dict[str, Any]:
    refuse_existing(out_path, "run")
    refuse_existing(receipts_path, "receipts")
    tree = scoring_tree(allow_dirty)

    prereg = json.loads((REPO / PREREG).read_text(encoding="utf-8"))
    fixtures = json.loads(fixtures_path.read_text(encoding="utf-8"))
    corpus = runtime.load_corpus()
    watch = ProcessWatch()

    # Raw receipts land before compact metrics (DESIGN §12).
    records = runtime.replay_registered_pass(fixtures, corpus)
    receipts_document = {
        "schema": "corollary.protocol-uptake-receipts/1",
        "design": DESIGN,
        "preregistration": PREREG,
        "preregistration_sha256": sha256_lf(REPO / PREREG),
        "registration_commit": tree["first_commit_of"][PREREG],
        "registered_before_the_run": tree["registered_before_the_run"],
        "emitted_by": THIS,
        "runtime_module": RUNTIME_MODULE,
        "pass_definition": (
            "protocol_runtime.replay_registered_pass: every sealed fixture in "
            "file order, one session each, then every sealed B9 mutant applied "
            "to the fixture the seal names. B5's arrival-order replays are "
            "identity checks over these same sessions and add no records."
        ),
        "receipt_count": len(records),
        "receipts": records,
    }
    write_once(receipts_path, receipts_document)

    scored = Pass(fixtures, corpus)
    gate = {
        "B1": score_b1(prereg, fixtures),
        "B2": score_b2(scored),
        "B3": score_b3(scored),
        "B4": score_b4(scored, prereg),
        "B5": score_b5(scored),
        "B6": score_b6(scored),
        "B7": report_b7(prereg),
        "B8": score_b8(scored, watch),
        "B9": score_b9(scored, prereg),
        "B10": score_b10(receipts_path, fixtures_path),
    }

    greens = {name: row.get("verdict") == "GREEN" for name, row in gate.items()}
    reds = sorted(name for name in SCORED_GATES if not greens[name])
    voiding = gate["B4"]["refit_on_the_runtimes_selected_moves"]
    r_u1_green = not reds and not voiding["fired"] and tree["registered_before_the_run"]

    return {
        "schema": RUN_SCHEMA,
        "design": DESIGN,
        "design_clause": "§7 construction gates, §8 blind controls, §9 result gates",
        "stage": "U-R1",
        "preregistration": PREREG,
        "preregistration_id": prereg["preregistration_id"],
        "preregistration_sha256": sha256_lf(REPO / PREREG),
        "registration_commit": tree["first_commit_of"][PREREG],
        "registered_before_the_run": tree["registered_before_the_run"],
        "scoring_tree": tree,
        "runtime_module": RUNTIME_MODULE,
        "receipts_artifact": {
            "path": receipts_path.name
            if receipts_path.parent != REPO / "experiments"
            else RECEIPTS_OUT,
            "receipt_count": len(records),
            "sha256_lf": sha256_lf(receipts_path),
            "note": "raw uptake receipts land before compact metrics (DESIGN §12)",
        },
        "counts": {
            **prereg["fixture_counts"],
            "receipts_emitted": len(records),
            "sessions": len(scored.sessions) + len(fixtures["b9_mutants"]),
        },
        "construction_gate": gate,
        "gate_greens": greens,
        "gate_reds": reds,
        "gates_pending": [
            name
            for name in PENDING_GATES
            if gate[name].get("verdict") == "PENDING_AMD3"
        ],
        "voiding_sentence": {
            "text": prereg["control_labels"]["voiding_sentence"],
            "evaluation": voiding,
            "fired": voiding["fired"],
        },
        "result_gates": {
            "R-U1": {
                "requires": "B1-B6 and B8-B10 pass, and no blind control fires",
                "green": r_u1_green,
                "licensed_sentence": (
                    "On the sealed protocol corpus and honest context product, the "
                    "same short utterance takes different verified interaction moves "
                    "from context and corpus evidence, and material ambiguity pauses "
                    "instead of guessing."
                )
                if r_u1_green
                else None,
                "why_not": None
                if r_u1_green
                else (
                    f"reds: {reds}; voiding fired: {voiding['fired']}; "
                    f"registered_before_the_run: {tree['registered_before_the_run']}"
                ),
            },
            "R-U2": {
                "requires": "B7 runs and passes",
                "green": gate["B7"].get("verdict") == "GREEN",
                "licensed_sentence": (
                    "The installed Codex host presented a verifier-approved need "
                    "as a structured prompt tool, returned its result, and "
                    "resumed the exact pending request."
                )
                if gate["B7"].get("verdict") == "GREEN"
                else None,
                "why_not": None
                if gate["B7"].get("verdict") == "GREEN"
                else (
                    f"B7 is {gate['B7'].get('verdict')}; text WAITING cannot "
                    "license R-U2"
                ),
            },
            "R-U3": {
                "requires": "a failed B2/B3 or a fired blind control",
                "green": False,
                "note": (
                    "the bounded negative is not licensed either: nothing failed and "
                    "no control fired"
                )
                if r_u1_green
                else "adjudicate against the confusion table in B2/B3",
            },
        },
        "non_claims": list(prereg["non_claims"]),
        "provenance": provenance(),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=REPO / RUN_OUT)
    parser.add_argument("--receipts-out", type=Path, default=REPO / RECEIPTS_OUT)
    parser.add_argument("--fixtures", type=Path, default=REPO / FIXTURES)
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help=(
            "score a dirty or wrong-tip tree for PRE-RUN TESTING ONLY. Recorded "
            "in the artifact as registered_before_the_run: false, which withholds "
            "every §9 sentence."
        ),
    )
    args = parser.parse_args(argv)

    try:
        payload = run(
            out_path=args.out,
            receipts_path=args.receipts_out,
            fixtures_path=args.fixtures,
            allow_dirty=args.allow_dirty,
        )
    except RunRefusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    write_once(args.out, payload)
    print(f"wrote {args.receipts_out}")
    print(f"wrote {args.out}")
    for name, row in payload["construction_gate"].items():
        detail = row.get("misses") or []
        print(f"  {name}: {row['verdict']}" + (f"  ({len(detail)} miss(es))" if detail else ""))
    print(f"voiding sentence fired: {payload['voiding_sentence']['fired']}")
    print(f"R-U1 green: {payload['result_gates']['R-U1']['green']}")
    return 0 if not payload["gate_reds"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
