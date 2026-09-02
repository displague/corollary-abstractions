#!/usr/bin/env python3
"""H-P1: the registered run. Replay the sealed corpus and score B1-B12.

`docs/DESIGN-house-rules.md` §6.3 is the order, §7 is the scoring, §8 is what
a score licenses. This is the third and last construction step: H-PRE sealed
the fixtures before a checker existed, H-P0 built the census, the checker and
the `declare` row, and this runs the one against the other.

## What makes this REGISTERED rather than a script that prints numbers

Every threshold this file compares against is READ from
`experiments/house_rules_prereg.json`, which is committed with this runner and
before the run. None of them is written here. A runner that carried its own
numbers could be edited into agreement with a result; a runner that reads them
can only be caught disagreeing.

Four refusals, all before any scoring:

* an **existing output path** refuses, twice — eagerly, and again structurally
  through `open(..., "x")`. The run may not overwrite its own evidence.
* a **dirty tree** refuses. `--allow-dirty` is for rehearsal only and forces
  `registered_before_the_run: false`, on which every licensed sentence gates.
  A rehearsal can print a table and can license nothing.
* a **wrong tip** refuses: the sealed H-PRE commit must be a strict ancestor of
  the scoring tip, proved with `git merge-base --is-ancestor` and recorded.
* a **moved seal** refuses: every `frozen` pin in the prereg is re-digested
  here, so a corpus edited between freeze and run cannot be scored as sealed.

## What the gates compare against, and why not against themselves

Two of the checks here would be tautologies if they read the shipped module
for both sides. B1's exclusivity check compares each verdict's deciding
clause against the clause the **sealed** `clause_order` maps its refusal code
to — the copy H-PRE committed before this checker existed — because comparing
`symbol_ledger._CLAUSE_BY_CODE[code]` against the clause the module built
from that same dict compares a value to itself. And the fixtures where MORE
THAN ONE clause holds are the only rows an order can be wrong about, so their
computed ground sets are compared against the seal exactly rather than by
containment.

## Determinism

No wall clock and no random source anywhere in the scored content; `DATE` is a
committed constant, every enumeration is sorted or file-ordered, and a replay
on the same tip reproduces the bytes. `scripts/check_house_rules_receipts.py`
is the second program that proves it.

## Why the outputs name no admitted symbol

The two declared output paths carry **fixture ids, never admitted symbol
names**, and the prereg registers that rule before the run. It is what lets
B5 be scored over the run's FULL output tree with no carve-out: a verdict
table that echoed those names would be a durable artifact from the run
containing exactly what B5 forbids, and the gate would have to be read down to
"except my own evidence" before it could pass. The names stay where H-PRE
already committed them. Refused names are not admitted names and are quoted
freely.

Usage::

    python scripts/run_house_rules_gates.py
    python scripts/run_house_rules_gates.py --allow-dirty \\
        --out /tmp/v.json --receipts-out /tmp/r.json   # rehearsal, licenses nothing
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import check_symbol_census  # noqa: E402
import harness  # noqa: E402
import session_ledger as ledger  # noqa: E402
import session_state  # noqa: E402
import symbol_ledger as SL  # noqa: E402
import write_stage  # noqa: E402
from prereg_pins import sha256_lf  # noqa: E402

RUN_SCHEMA = "corollary.house-rules-run/1"
RECEIPTS_SCHEMA = "corollary.house-rules-receipts/1"
STAGE = "H-P1"
DATE = "2026-09-02"
DESIGN = "docs/DESIGN-house-rules.md"

PREREG = "experiments/house_rules_prereg.json"
FIXTURES = "experiments/house_rules_fixtures.json"
CENSUS = "experiments/symbol_census.json"
SCHEMA = "schema/equation-node.schema.json"
HYPOTHESES = "experiments/guest_hypotheses.json"

LEDGER_MODULE = "scripts/symbol_ledger.py"
CENSUS_CHECKER = "scripts/check_symbol_census.py"
RECEIPT_CHECKER = "scripts/check_house_rules_receipts.py"
THIS = "scripts/run_house_rules_gates.py"

RUN_OUT = "experiments/house_rules_verdicts.json"
RECEIPTS_OUT = "experiments/house_rules_receipts.json"

SCORED_GATES = tuple(f"B{n}" for n in range(1, 13))

#: DESIGN §8's R-H3, and the prereg's `r_h3`, in their own words: "Any failed
#: construction gate B1-B8/B10/B11 or a fired B9 licenses the bounded
#: negative". B9 enters through the firing clause; B12 postdates the sentence
#: and is reported beside it. Spelled out here so the licence is the clause's
#: and not "every gate the runner happens to score".
R_H3_GATES = ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B10", "B11")


class RunRefusal(RuntimeError):
    """The run may not proceed. Never a gate verdict — a refusal to score."""


def _verdict(misses: list[str]) -> str:
    return "GREEN" if not misses else "RED"


# --------------------------------------------------------------------------
# git, and the tree the run is allowed to score
# --------------------------------------------------------------------------


def _git(*args: str) -> str:
    """A failing git command refuses the run; it never reads as a clean tree.

    Discarding the return code would let a broken `git status` come back empty
    and be scored as "nothing is dirty", which is the one misreading a
    registered run cannot afford.
    """

    completed = subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    if completed.returncode != 0:
        raise RunRefusal(
            f"git {' '.join(args)} exited {completed.returncode}: "
            f"{(completed.stderr or '').strip()[:200]}"
        )
    return completed.stdout.strip()


def _first_commit(path: str) -> str | None:
    lines = [
        line.strip()
        for line in _git(
            "log", "--format=%H", "--diff-filter=A", "--reverse", "--", path
        ).splitlines()
        if line.strip()
    ]
    return lines[0] if lines else None


def _is_ancestor(earlier: str, later: str) -> bool:
    if not earlier or not later or earlier == later:
        # Strict: two artifacts added in the same commit are not ordered by
        # the history, and an ordering claim a single squashed commit would
        # satisfy is not an ordering claim (tests/git_ordering.py's rule).
        return False
    return (
        subprocess.run(
            ["git", "-C", str(REPO), "merge-base", "--is-ancestor", earlier, later],
            capture_output=True,
            timeout=120,
        ).returncode
        == 0
    )


def refuse_existing(path: Path, role: str) -> None:
    if path.exists():
        raise RunRefusal(f"registered {role} artifact already exists: {path}")


def write_once(path: Path, document: dict) -> None:
    """Create the artifact; an existing path is never replaced."""

    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(document, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
    except FileExistsError as exc:
        raise RunRefusal(f"registered artifact already exists: {path}") from exc


def scoring_tree(prereg: dict, allow_dirty: bool) -> dict:
    """Refuse a dirty, wrong-tip or moved-seal tree; record what was checked."""

    status = _git("status", "--porcelain", "--untracked-files=all")
    dirty = [line for line in status.splitlines() if line.strip()]

    head = _git("rev-parse", "HEAD") or None
    sealed = prereg["sealed_commit"]
    sealed_is_ancestor = _is_ancestor(sealed, head) if head else False

    registration_inputs = [
        PREREG,
        FIXTURES,
        CENSUS,
        LEDGER_MODULE,
        CENSUS_CHECKER,
        RECEIPT_CHECKER,
        THIS,
    ]
    commits = {path: _first_commit(path) for path in registration_inputs}
    uncommitted = sorted(path for path, commit in commits.items() if commit is None)

    # The seal has not moved since it was pinned: every `frozen` row is
    # re-digested here rather than trusted.
    moved = [
        row["path"]
        for row in prereg["frozen"]
        if sha256_lf(REPO / row["path"]) != row["sha256_lf"]
    ]

    tree = {
        "head_commit": head,
        "sealed_commit": sealed,
        "sealed_commit_is_strict_ancestor_of_head": sealed_is_ancestor,
        "dirty": bool(dirty),
        "dirty_entries": dirty[:40],
        "uncommitted_registration_inputs": uncommitted,
        "first_commit_of": commits,
        "frozen_pins_that_moved": moved,
        "wrong_tip": bool(uncommitted) or not sealed_is_ancestor or bool(moved),
        "how_checked": (
            "git status --porcelain --untracked-files=all for dirty; "
            "git merge-base --is-ancestor (STRICT: same-commit is not an "
            "ancestor) for the sealed commit against HEAD; and every prereg "
            "`frozen` pin re-digested with sha256_lf"
        ),
        "allow_dirty": allow_dirty,
    }
    # A rehearsal never counts as registered, even on a tree that happens to be
    # clean: --allow-dirty is a hatch for testing the runner, and a hatch that
    # could still license a sentence would not be one.
    tree["registered_before_the_run"] = (
        not tree["dirty"] and not tree["wrong_tip"] and not allow_dirty
    )
    if not tree["registered_before_the_run"] and not allow_dirty:
        if tree["dirty"]:
            raise RunRefusal(
                f"the registered run scores only a clean tree; {len(dirty)} "
                f"entry(ies) are dirty, first: {dirty[0]!r}"
            )
        if uncommitted:
            raise RunRefusal(
                f"registration inputs are not committed: {', '.join(uncommitted)}"
            )
        if moved:
            raise RunRefusal(
                "the seal moved after it was pinned; these prereg `frozen` rows "
                f"no longer match the tree: {', '.join(moved)}"
            )
        raise RunRefusal(
            f"wrong-tip tree: the sealed commit {sealed[:12]} is not a strict "
            f"ancestor of HEAD {head[:12] if head else '(none)'}"
        )
    return tree


# --------------------------------------------------------------------------
# replay
# --------------------------------------------------------------------------


def _rest(line: str) -> str:
    return line.partition(" ")[2]


def _sessions(document: dict) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in document["fixtures"]:
        grouped.setdefault(row["session_id"], []).append(row)
    for rows in grouped.values():
        rows.sort(key=lambda r: r["turn_index"])
    return grouped


def _live_session(session_id: str, inputs: SL.CommittedInputs):
    session = harness.CoreSession.boot(REPO, offline=True, session_id=session_id)
    session.assumptions = ledger.AssumptionSet(
        session_id=session_id, barrier=ledger.ReadBarrier()
    )
    session.symbols = SL.SymbolLedger(
        session_id=session_id, inputs=inputs, assumptions=session.assumptions
    )
    return session


class Replay:
    """Every declaration fixture, decided session by session in turn order."""

    def __init__(self, document: dict, inputs: SL.CommittedInputs) -> None:
        self.document = document
        self.inputs = inputs
        self.rows: dict[str, dict] = {}
        self.admitted_by_session: dict[str, list[str]] = {}
        #: fixture_id -> the LIVE ledger key that fixture's admission created.
        #: Held in memory only; it never reaches either declared output, which
        #: is what lets B5 sweep the full output tree with no carve-out.
        self.admitted_key_by_fixture: dict[str, str] = {}
        #: fixture_id -> (admitted tuple, SessionNames) as they stood WHEN
        #: that fixture was decided. The sweep replays mutants in place.
        self.contexts: dict[str, tuple] = {}
        self._run()

    def _run(self) -> None:
        for session_id, rows in _sessions(self.document).items():
            admitted: list[str] = []
            binding: set[str] = set()
            heads: set[str] = set()
            for row in rows:
                if row["kind"] == "use":
                    self.contexts[row["fixture_id"]] = (
                        tuple(admitted),
                        SL.SessionNames(
                            admitted_symbols=frozenset(admitted),
                            binding_subjects=frozenset(binding),
                            applied_heads=frozenset(heads),
                        ),
                    )
                    if row.get("binds_subject"):
                        binding.add(SL.normalize(row["binds_subject"]))
                    elif row.get("read_applied_head"):
                        heads.add(SL.normalize(row["read_applied_head"]))
                    continue
                names = SL.SessionNames(
                    admitted_symbols=frozenset(admitted),
                    binding_subjects=frozenset(binding),
                    applied_heads=frozenset(heads),
                )
                self.contexts[row["fixture_id"]] = (tuple(admitted), names)
                decision = SL.decide(
                    _rest(row["line"]),
                    self.inputs,
                    session_id=session_id,
                    turn_index=row["turn_index"],
                    admitted=tuple(admitted),
                    session_names=names,
                )
                self.rows[row["fixture_id"]] = {
                    "fixture_id": row["fixture_id"],
                    "session_id": session_id,
                    "turn_index": row["turn_index"],
                    "verdict": decision.verdict.verdict,
                    "refusal_code": decision.verdict.refusal_code,
                    "deciding_clause": decision.verdict.deciding_clause,
                    "grounds_count": len(decision.grounds),
                    "also_grounds_for": sorted(
                        set(decision.grounds) - {decision.verdict.refusal_code}
                    ),
                    "session_name_subcase": decision.session_name_subcase,
                    "matches_sealed_expectation": (
                        decision.verdict.verdict == row["expected_verdict"]
                        and decision.verdict.refusal_code == row["expected_refusal_code"]
                        and decision.verdict.deciding_clause
                        == row["expected_deciding_clause"]
                    ),
                    "verdict_id": decision.verdict.verdict_id,
                    "decl_id": decision.verdict.decl_id,
                }
                if decision.admitted:
                    admitted.append(decision.declaration.symbol_name)
                    self.admitted_key_by_fixture[row["fixture_id"]] = (
                        decision.declaration.symbol_name
                    )
            self.admitted_by_session[session_id] = admitted

    def admitted_names(self) -> list[str]:
        """The names B5 sweeps for. Held in memory; never written out."""

        names: set[str] = set()
        for admitted in self.admitted_by_session.values():
            names.update(admitted)
        for mutant in self.document["b12_round_trip"]["mutants"]:
            if mutant["expected_resolved_key"]:
                names.add(mutant["expected_resolved_key"])
        return sorted(names)


# --------------------------------------------------------------------------
# the enumerated sweep (B1's input set, B7's population)
# --------------------------------------------------------------------------


def build_sweep(document: dict, replay: Replay) -> tuple[list[tuple], dict]:
    """Every fixture line, mutated in PLACE, with its session context.

    "Every fixture line mutated by single-token deletion/substitution" means
    the line where it sits, not the line in a vacuum. That distinction is
    load-bearing and rehearsal is how it was found: scored statelessly, in a
    fresh session with nothing admitted, the sweep can reach only five of the
    eight codes, because `REDEFINITION_ATTEMPT`, `COLLIDES_WITH_SESSION_NAME`
    and `SYMBOL_BUDGET` are clauses ABOUT SESSION STATE and no stateless input
    can fire them. A stateless sweep would therefore have reported 5-of-8 as a
    fact about the checker when it was a fact about the harness.

    So each mutant is decided in the context its source fixture occupied: the
    symbols admitted in that session before that turn, and the three-source
    session-name union as it stood. Both numbers are reported — the stateless
    count as well — so the choice is visible rather than buried.
    """

    contexts = replay.contexts
    # THE WHOLE LINE, command word included. The clause says "every fixture
    # LINE mutated by single-token deletion/substitution from the fixture
    # alphabet". Mutating only the declaration argument would leave `declare`
    # and `suppose` untouched and absent from the alphabet, which is a
    # narrower population than the one registered — so the mutation is
    # applied to the full line and the ROUTE's own convention (everything
    # after the first token reaches the checker) is applied afterwards,
    # exactly as a person typing that line would experience it.
    surfaces = [(row["fixture_id"], row["line"]) for row in document["fixtures"]]
    alphabet = sorted({token for _, text in surfaces for token in text.split()})
    sweep: list[tuple] = []
    for fixture_id, text in surfaces:
        context = contexts.get(fixture_id, ((), SL.SessionNames()))
        tokens = text.split()
        for index in range(len(tokens)):
            sweep.append(
                (_rest(" ".join(tokens[:index] + tokens[index + 1 :])), fixture_id, context)
            )
            for replacement in alphabet:
                sweep.append(
                    (
                        _rest(
                            " ".join(
                                tokens[:index] + [replacement] + tokens[index + 1 :]
                            )
                        ),
                        fixture_id,
                        context,
                    )
                )
    seen: set[tuple[str, str]] = set()
    ordered: list[tuple] = []
    for text, fixture_id, context in sweep:
        key = (text, fixture_id)
        if key in seen:
            continue
        seen.add(key)
        ordered.append((text, fixture_id, context))
    ordered.sort(key=lambda item: (item[0], item[1]))
    return ordered, {
        "source_lines": len(surfaces),
        "alphabet_size": len(alphabet),
        "generated": len(sweep),
        "distinct_scored": len(ordered),
        "rule": (
            "for every fixture line — the command word included — delete each "
            "token once, and substitute each token once with every member of "
            "the fixture alphabet; the route's convention (everything after "
            "the first token reaches the checker) is then applied to the "
            "mutant, and the results are de-duplicated on (surface, source "
            "fixture) and sorted"
        ),
        "alphabet_rule": (
            "every whitespace token occurring in any fixture LINE — command "
            "words included — enumerated from the sealed corpus, not chosen"
        ),
        "mutation_covers_the_command_word": True,
        "evaluated_in_context": True,
        "evaluated_in_context_note": (
            "each mutant is decided in the session context its SOURCE FIXTURE "
            "occupied — the symbols admitted in that session before that turn, "
            "and the three-source session-name union as it stood. Three of the "
            "eight codes are clauses about session state and are unreachable "
            "by any stateless input, so a context-free sweep would report a "
            "property of the harness as a property of the checker."
        ),
        "authored_toward_a_code": False,
    }


def score_b1_b7(prereg: dict, document: dict, inputs, replay: Replay) -> tuple:
    sweep, meta = build_sweep(document, replay)
    clauses = set(SL.CLAUSE_IDS) | {SL.CLAUSE_ADMIT}

    # THE DISCRIMINATOR IS THE SEALED ONE, not the shipped module's own map.
    # Comparing `symbol_ledger._CLAUSE_BY_CODE[code]` against the clause the
    # module built from that same dict one call earlier compares a value to
    # itself: it cannot fail, and B1 would report 13k inputs' worth of
    # exclusivity evidence it never gathered. H-PRE sealed `clause_order` in
    # the fixtures — before the checker existed — precisely so a second copy
    # exists, and this is what reads it.
    sealed_rows = sorted(document["clause_order"], key=lambda row: row["rank"])
    sealed_clause_by_code = {row["refusal_code"]: row["clause"] for row in sealed_rows}
    sealed_order = tuple((row["clause"], row["refusal_code"]) for row in sealed_rows)

    misses1: list[str] = []
    if sealed_order != SL.CLAUSE_ORDER:
        misses1.append(
            "the shipped CLAUSE_ORDER is not the order sealed at H-PRE"
        )
    codes: dict[str, int] = {}
    stateless_codes: dict[str, int] = {}
    admitted_on_sweep = 0
    fall_throughs = 0
    unknown_clauses = 0
    for text, _source, (ctx_admitted, ctx_names) in sweep:
        stateless = SL.decide(text, inputs, session_id="b1-sweep", turn_index=1)
        if not stateless.admitted:
            stateless_codes[stateless.verdict.refusal_code] = (
                stateless_codes.get(stateless.verdict.refusal_code, 0) + 1
            )
        decision = SL.decide(
            text,
            inputs,
            session_id="b1-sweep",
            turn_index=1,
            admitted=ctx_admitted,
            session_names=ctx_names,
        )
        verdict = decision.verdict
        if verdict.verdict not in {SL.VERDICT_ADMITTED, SL.VERDICT_REFUSED}:
            fall_throughs += 1
            misses1.append(f"fall-through verdict {verdict.verdict!r}")
            continue
        if verdict.deciding_clause not in clauses:
            unknown_clauses += 1
            misses1.append(f"unknown deciding_clause {verdict.deciding_clause!r}")
            continue
        if verdict.admitted:
            admitted_on_sweep += 1
            if verdict.refusal_code != SL.REFUSAL_NONE:
                misses1.append("an admission carried a refusal code")
            if verdict.deciding_clause != SL.CLAUSE_ADMIT:
                misses1.append("an admission did not decide on the admit clause")
            continue
        if sealed_clause_by_code.get(verdict.refusal_code) != verdict.deciding_clause:
            misses1.append(
                f"code {verdict.refusal_code} decided on {verdict.deciding_clause}, "
                f"which is not the clause the SEALED order maps it to"
            )
            continue
        codes[verdict.refusal_code] = codes.get(verdict.refusal_code, 0) + 1

    fixture_rows = list(replay.rows.values())
    mismatched = sorted(
        row["fixture_id"] for row in fixture_rows if not row["matches_sealed_expectation"]
    )
    for fixture_id in mismatched:
        misses1.append(f"{fixture_id}: verdict differs from the sealed expectation")
    sealed_by_id = {row["fixture_id"]: row for row in document["fixtures"]}
    grounds_off_the_seal: list[str] = []
    for row in fixture_rows:
        if row["verdict"] not in {SL.VERDICT_ADMITTED, SL.VERDICT_REFUSED}:
            fall_throughs += 1
            misses1.append(f"{row['fixture_id']}: fall-through verdict")
        if row["deciding_clause"] not in clauses:
            unknown_clauses += 1
            misses1.append(f"{row['fixture_id']}: unknown deciding_clause")
        # The ONLY rows that prove the order decided anything are the ones
        # where more than one clause held. The seal records those in
        # `also_grounds_for`; comparing the computed set against it EXACTLY
        # (not by containment) is what catches a fixture that omitted an
        # earlier ground.
        sealed = sealed_by_id[row["fixture_id"]]
        if sorted(sealed.get("also_grounds_for") or []) != sorted(row["also_grounds_for"]):
            grounds_off_the_seal.append(row["fixture_id"])
            misses1.append(
                f"{row['fixture_id']}: the grounds that also held differ from the seal"
            )

    b1 = {
        "verdict": _verdict(misses1),
        "clause": prereg["gates"]["B1"],
        "sweep": meta,
        "sweep_inputs_scored": len(sweep),
        "sweep_admissions": admitted_on_sweep,
        "fixture_declarations_scored": len(fixture_rows),
        "fixtures_matching_the_seal": f"{len(fixture_rows) - len(mismatched)}/{len(fixture_rows)}",
        "inputs_scored_total": len(sweep) + len(fixture_rows),
        "fall_throughs": fall_throughs,
        "deciding_clauses_outside_the_committed_order": unknown_clauses,
        "multi_ground_fixtures": sorted(
            row["fixture_id"]
            for row in document["fixtures"]
            if row.get("also_grounds_for")
        ),
        "multi_ground_fixtures_off_the_seal": sorted(grounds_off_the_seal),
        "shipped_clause_order_equals_the_sealed_order": sealed_order == SL.CLAUSE_ORDER,
        "how_exclusivity_was_checked": (
            "for every input the deciding_clause was compared against the "
            "clause the SEALED clause_order maps its refusal code to — the "
            "copy H-PRE committed before the checker existed — per input "
            "rather than once for the set, and the shipped CLAUSE_ORDER was "
            "compared against that seal as a whole. Comparing the module's "
            "own code-to-clause map against the clause the module built from "
            "it would compare a value to itself"
        ),
        "how_the_order_was_shown_to_decide": (
            "the fixtures where MORE THAN ONE clause holds are the only ones "
            "an order can be wrong about; their computed ground sets are "
            "compared against the seal EXACTLY rather than by containment, so "
            "a fixture that omitted an earlier ground fails"
        ),
        "admission_clause_note": (
            "the admit clause has no sealed row — `clause_order` seals the "
            "eight REFUSAL clauses — so an admission's deciding clause is "
            "checked against the module's constant. Disclosed rather than "
            "counted as sealed evidence"
        ),
        "misses": misses1,
    }

    all_codes = set(SL.REFUSAL_CODES)
    hit = set(codes)
    hand_only = sorted(all_codes - hit)
    floor = prereg["frozen_numbers"]["b7_codes_floor"]
    all_admitted = admitted_on_sweep == len(sweep)
    all_unparsed = hit == {"UNPARSED"} and admitted_on_sweep == 0
    misses7: list[str] = []
    if len(hit) < floor:
        misses7.append(f"the sweep hit {len(hit)} of 8 refusal codes, floor {floor}")
    if all_admitted:
        misses7.append("BLOCKED CONSTRUCTION: the sweep is all-admitted")
    if all_unparsed:
        misses7.append("BLOCKED CONSTRUCTION: the sweep is all-UNPARSED")

    b7 = {
        "verdict": _verdict(misses7),
        "clause": prereg["gates"]["B7"],
        "codes_hit_on_the_sweep": f"{len(hit)}/{prereg['frozen_numbers']['b7_codes_of']}",
        "floor": floor,
        "per_code_counts": dict(sorted(codes.items())),
        "codes_hit_stateless": (
            f"{len(stateless_codes)}/{prereg['frozen_numbers']['b7_codes_of']}"
        ),
        "per_code_counts_stateless": dict(sorted(stateless_codes.items())),
        "stateless_note": (
            "reported beside the scored figure so the contextual choice is "
            "visible: decided in a fresh session with nothing admitted, the "
            "same sweep reaches only the codes that do not depend on session "
            "state. The difference is the three session-state clauses."
        ),
        "hand_only_codes": hand_only,
        "hand_only_note": (
            "codes reachable only by hand-crafted fixtures, reported by name "
            "as the clause requires"
        ),
        "sweep_admissions": admitted_on_sweep,
        "all_admitted": all_admitted,
        "all_unparsed": all_unparsed,
        "no_sweep_input_authored_toward_a_code": True,
        "misses": misses7,
    }
    return b1, b7, meta


# --------------------------------------------------------------------------
# B2
# --------------------------------------------------------------------------


def score_b2(prereg: dict, document: dict, inputs, replay: Replay) -> dict:
    misses: list[str] = []
    admitted = replay.admitted_names()
    collisions = [n for n in admitted if n in inputs.equality_members]
    prefixed = [n for n in admitted if n.startswith(tuple(inputs.reserved_prefixes))]
    if collisions:
        misses.append(f"{len(collisions)} admission(s) collide with the census")
    if prefixed:
        misses.append(f"{len(prefixed)} admission(s) match a reserved prefix")

    completed = subprocess.run(
        [sys.executable, str(REPO / CENSUS_CHECKER)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(REPO),
    )
    if completed.returncode != 0:
        misses.append("the census checker did not reproduce the committed artifact")

    prefix_rows = []
    library_rows = []
    for row in document["fixtures"]:
        if row["kind"] != "declaration":
            continue
        scored = replay.rows[row["fixture_id"]]
        if row["expected_refusal_code"] == "RESERVED_PREFIX":
            prefix_rows.append(
                {"fixture_id": row["fixture_id"], "refusal_code": scored["refusal_code"]}
            )
            if scored["refusal_code"] != "RESERVED_PREFIX":
                misses.append(f"{row['fixture_id']}: did not refuse RESERVED_PREFIX")
        if row["expected_refusal_code"] == "COLLIDES_WITH_LIBRARY_SYMBOL":
            library_rows.append(
                {"fixture_id": row["fixture_id"], "refusal_code": scored["refusal_code"]}
            )
            if scored["refusal_code"] != "COLLIDES_WITH_LIBRARY_SYMBOL":
                misses.append(
                    f"{row['fixture_id']}: did not refuse COLLIDES_WITH_LIBRARY_SYMBOL"
                )
    if not prefix_rows:
        misses.append("no fixture exercised the reserved-prefix named case")
    if not library_rows:
        misses.append("no fixture exercised the library-collision named case")

    return {
        "verdict": _verdict(misses),
        "clause": prereg["gates"]["B2"],
        "admissions": len(admitted),
        "admissions_colliding_with_the_census": len(collisions),
        "admissions_matching_a_reserved_prefix": len(prefixed),
        "census_checker": CENSUS_CHECKER,
        "census_checker_exit": completed.returncode,
        "census_checker_output": completed.stdout.strip().splitlines()[-2:],
        "census_ref": inputs.census_ref,
        "named_case_reserved_prefix": prefix_rows,
        "named_case_library_collision": library_rows,
        "two_programs_note": (
            "the checker compares against the COMMITTED artifact at the digest "
            "every verdict cites; the census checker is a separate invocation "
            "of a separate program that recomputes from source"
        ),
        "misses": misses,
    }


# --------------------------------------------------------------------------
# B3 — each mutant stopped by the shipped detector its seal names
# --------------------------------------------------------------------------


def _covered_paths(root: Path) -> list[str]:
    """Exactly the paths `write_stage.working_tree_digest` folds.

    Re-deriving the exclusion rule here got it wrong in a way that matters:
    `INTEGRITY_EXCLUDED_RUNTIME`'s entries are path PREFIXES
    (`experiments/data`, `experiments/visual/out`), and a per-component
    membership test never matches one. A file under a directory the digest
    deliberately ignores would then be reported by B4 as having appeared
    while `working_tree_digest_byte_identical` stayed true, and the two
    programs' sweeps could disagree about which files exist. So both the path
    list and both sweeps read the shipped, public definition instead.
    """

    return sorted(write_stage.working_tree_file_digests(root))


def _sweep_tree_for_names(
    root: Path, names: list[str], skip: tuple[str, ...] = ()
) -> tuple[list[dict], list[str]]:
    """Hits, and the paths that could not be read — never silently dropped."""

    hits: list[dict] = []
    unreadable: list[str] = []
    folded = [name.casefold() for name in names]
    for relative in _covered_paths(root):
        if relative in skip:
            continue
        try:
            text = (root / relative).read_text(encoding="utf-8", errors="ignore").casefold()
        except OSError:  # pragma: no cover — a locked or vanished file
            unreadable.append(relative)
            continue
        if any(name in text for name in folded):
            hits.append({"path": relative})
    return hits, unreadable


def _detectors(document: dict, inputs) -> dict[str, dict]:
    out: dict[str, dict] = {}

    decision = SL.decide(
        "probe_of/2 (variable, variable)", inputs, session_id="b3", turn_index=1
    )
    observed = []
    for record in (decision.declaration, decision.verdict):
        try:
            session_state.encode(record)
            observed.append("ENCODED")
        except session_state.SessionFormatError as exc:
            observed.append(f"refused: {type(exc).__name__}")
    out["encode_type_registry"] = {
        "fires": all(item.startswith("refused") for item in observed),
        "observed": observed,
    }

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "planted.json").write_text('{"x": "a_planted_name"}', encoding="utf-8")
        found, _ = _sweep_tree_for_names(root, ["a_planted_name"])
        clean, _ = _sweep_tree_for_names(root, ["a_name_that_is_absent"])
    out["name_sweep"] = {
        "fires": bool(found) and not clean,
        "kind": "sensitivity probe",
        "observed": {"planted_found": len(found), "absent_found": len(clean)},
    }

    # TWO HALVES, because a sensitivity probe on its own cannot be false. The
    # first half shows the digest MOVES when a file is planted — that is the
    # detector working. The second half is the vector: a declaration and a use
    # are routed through a live session against the real repository, and the
    # repository's own digest must NOT have moved. Without the second half
    # this detector answered "does a digest change when you change a tree",
    # which is a question about hashlib.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "seed.txt").write_text("one", encoding="utf-8")
        before = write_stage.working_tree_digest(root)
        (root / "escape.py").write_text("print('escaped')\n", encoding="utf-8")
        after = write_stage.working_tree_digest(root)
    sensitive = before != after
    repo_before = write_stage.working_tree_digest(REPO)
    live = _live_session("b3-write", inputs)
    live.assumptions.barrier.open_turn(1)
    harness.route_line(REPO, live, "declare probe_three/2 (variable, variable)")
    live.assumptions.barrier.close_turn()
    live.assumptions.barrier.open_turn(2)
    harness.route_line(REPO, live, "suppose probe_three(a, b)")
    live.assumptions.barrier.close_turn()
    repo_after = write_stage.working_tree_digest(REPO)
    out["working_tree_digest"] = {
        "fires": sensitive and repo_before == repo_after,
        "kind": "sensitivity probe AND a live observation of the vector",
        "observed": {
            "moved_on_a_planted_file": sensitive,
            "repository_digest_unmoved_by_a_declaration_and_a_use": (
                repo_before == repo_after
            ),
        },
    }

    from dataclasses import fields as dc_fields  # noqa: PLC0415

    read_event = {f.name for f in dc_fields(ledger.ReadEvent)}
    out["record_shape_has_no_symbol_slot"] = {
        "fires": "symbol_name" not in read_event,
        "observed": {"ReadEvent_fields": sorted(read_event)},
    }

    ids: set[str] = set()
    for path in sorted((REPO / "data").glob("*/nodes.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for node in payload.get("statement_nodes", []):
            ids.add(node.get("statement_id"))
    out["id_resolution_against_the_merged_graph"] = {
        "fires": decision.declaration.decl_id not in ids,
        "observed": {
            "corpus_statement_ids": len(ids),
            "decl_id_resolves_to_a_node": decision.declaration.decl_id in ids,
        },
    }

    session = _live_session("b3-status", inputs)
    session.assumptions.barrier.open_turn(1)
    harness.route_line(REPO, session, "declare probe_two/2 (variable, variable)")
    session.assumptions.barrier.close_turn()
    session.assumptions.barrier.open_turn(2)
    used = harness.route_line(REPO, session, "suppose probe_two(a, b)")
    session.assumptions.barrier.close_turn()
    out["a_checked_use_is_still_a_supposition"] = {
        "fires": used["route"] == "supposition" and used["status"] != "solved",
        "observed": {"route": used["route"], "status": used["status"]},
    }

    import prereg_pins  # noqa: PLC0415

    # Narrow on purpose, and the narrowing found a real defect during
    # construction: the earlier probe passed a malformed row and caught
    # `Exception`, so a KeyError from the row's own missing field scored as
    # "the pin chain refused". It never exercised the chain at all. The probe
    # below is a WELL-FORMED row retired to an amendment the prereg does not
    # record — the case `PinChainError` exists for — and the second half
    # confirms an unretired row still resolves, so the detector is not just
    # "this function raises".
    retired = {
        "path": "<probe>",
        "role": "<probe>",
        "sha256_lf": "0" * 64,
        "retired_for_future_comparisons": {"amendment": "an-amendment-not-recorded"},
    }
    try:
        prereg_pins.resolve_pin({"amendments": []}, retired, prereg_path="<probe>")
        pin_fires, pin_observed = False, "resolve_pin accepted an unrecorded retirement"
    except prereg_pins.PinChainError as exc:
        pin_fires, pin_observed = True, type(exc).__name__
    plain = prereg_pins.resolve_pin(
        {"amendments": []},
        {"path": "<probe>", "role": "<probe>", "sha256_lf": "0" * 64},
        prereg_path="<probe>",
    )
    out["prereg_pin_chain"] = {
        "fires": pin_fires and plain["sha256_lf"] == "0" * 64,
        "kind": "sensitivity probe, both directions",
        "observed": {
            "unrecorded_retirement": pin_observed,
            "unretired_row_resolves_to_itself": plain["sha256_lf"] == "0" * 64,
        },
        "refusal_type_required": "prereg_pins.PinChainError",
    }

    committed = json.loads((REPO / CENSUS).read_text(encoding="utf-8"))
    fresh = check_symbol_census.recompute(REPO)
    clean_problems = check_symbol_census.compare(copy.deepcopy(committed), fresh)
    tampered = copy.deepcopy(committed)
    tampered["equality_members"] = sorted(
        set(tampered["equality_members"]) | {"an_inserted_member"}
    )
    dirty_problems = check_symbol_census.compare(tampered, fresh)
    out["census_regeneration"] = {
        "fires": not clean_problems and bool(dirty_problems),
        "observed": {
            "committed_problems": len(clean_problems),
            "problems_after_inserting_a_member": len(dirty_problems),
        },
    }

    fresh_session = _live_session("b3-fresh", inputs)
    row = next(
        r
        for r in document["fixtures"]
        if r["session_id"] == "hr-fx-s4" and r["kind"] == "use"
    )
    fresh_session.assumptions.barrier.open_turn(1)
    fresh_verdict = harness.route_line(REPO, fresh_session, row["line"])
    fresh_session.assumptions.barrier.close_turn()
    out["fresh_session_has_no_ledger_entry"] = {
        "fires": (
            fresh_session.symbols.admitted_names() == ()
            and fresh_session.symbols.check_use(_rest(row["line"])) is None
            and fresh_verdict["status"] != "refused"
        ),
        "observed": {
            "admitted_in_a_fresh_session": len(fresh_session.symbols.admitted_names()),
            "use_check_returned_none": (
                fresh_session.symbols.check_use(_rest(row["line"])) is None
            ),
            "fixture_id": row["fixture_id"],
        },
    }

    source = (REPO / LEDGER_MODULE).read_text(encoding="utf-8")
    constants = {
        node.value
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    named = [path for path in (RUN_OUT, RECEIPTS_OUT) if path in constants]
    out["checker_inputs_exclude_the_runs_outputs"] = {
        "fires": not named,
        "observed": {
            "declared_outputs_named_in_the_checker": named,
            "checker_inputs": [CENSUS, SCHEMA, "the declaration line"],
        },
    }
    return out


B3_DETECTORS = {
    "b3-m01": "id_resolution_against_the_merged_graph",
    "b3-m02": "a_checked_use_is_still_a_supposition",
    "b3-m03": "id_resolution_against_the_merged_graph",
    "b3-m04": "record_shape_has_no_symbol_slot",
    "b3-m05": "name_sweep",
    "b3-m06": "record_shape_has_no_symbol_slot",
    "b3-m07": "name_sweep",
    "b3-m08": "working_tree_digest",
    "b3-m09": "encode_type_registry",
    "b3-m10": "encode_type_registry",
    "b3-m11": "name_sweep",
    "b3-m12": "encode_type_registry",
    "b3-m13": "name_sweep",
    "b3-m14": "record_shape_has_no_symbol_slot",
    "b3-m15": "name_sweep",
    "b3-m16": "name_sweep",
    "b3-m17": "working_tree_digest",
    "b3-m18": "prereg_pin_chain",
    "b3-m19": "working_tree_digest",
    "b3-m20": "name_sweep",
    "b3-m21": "fresh_session_has_no_ledger_entry",
    "b3-m22": "working_tree_digest",
    "b3-m23": "census_regeneration",
    "b3-m24": "checker_inputs_exclude_the_runs_outputs",
    "b3-m25": "working_tree_digest",
    "b3-m26": "census_regeneration",
    "b3-m27": "working_tree_digest",
    "b3-m28": "working_tree_digest",
    "b3-m29": "working_tree_digest",
    "b3-m30": "working_tree_digest",
    "b3-m31": "census_regeneration",
    "b3-m32": "working_tree_digest",
}


def score_b3(prereg: dict, document: dict, detectors: dict) -> dict:
    misses: list[str] = []
    rows = []
    for mutant in document["b3_containment"]["mutants"]:
        name = B3_DETECTORS.get(mutant["mutant_id"])
        detector = detectors.get(name)
        stopped = bool(detector and detector["fires"])
        if not stopped:
            misses.append(f"{mutant['mutant_id']} survived: detector {name!r} did not fire")
        rows.append(
            {
                "mutant_id": mutant["mutant_id"],
                "vector": mutant["vector"],
                "outcome": "STOPPED" if stopped else "SURVIVED",
                "stopped_by": name,
            }
        )
    floor = prereg["frozen_numbers"]["b3_mutant_floor"]
    if len(rows) < floor:
        misses.append(f"{len(rows)} mutants, floor {floor}")
    sealed_ids = {mutant["mutant_id"] for mutant in document["b3_containment"]["mutants"]}
    unmapped = sorted(sealed_ids - set(B3_DETECTORS))
    invented = sorted(set(B3_DETECTORS) - sealed_ids)
    if unmapped:
        misses.append(f"sealed mutants with no detector mapped: {unmapped}")
    if invented:
        misses.append(f"detector map carries ids absent from the seal: {invented}")
    stopped = sum(1 for row in rows if row["outcome"] == "STOPPED")
    return {
        "verdict": _verdict(misses),
        "clause": prereg["gates"]["B3"],
        "mutants": f"{stopped}/{len(rows)} stopped",
        "floor": floor,
        "survivors": [r["mutant_id"] for r in rows if r["outcome"] == "SURVIVED"],
        "detectors_exercised": {name: detectors[name] for name in sorted(detectors)},
        "detector_map": f"{THIS}:B3_DETECTORS",
        "detector_map_covers_the_seal_exactly": not unmapped and not invented,
        "detector_map_note": (
            "DISCLOSED rather than glossed: the sealed corpus names each "
            "mutant's stopper in PROSE (`stopper_mechanism`), not as a "
            "machine-readable detector id, so the id-to-detector association "
            "is AUTHORED in the runner — committed with the prereg and before "
            "the run, and required here to cover the sealed mutant set exactly "
            "in both directions. What is not authored is whether the named "
            "detector fires: every one is exercised on a planted case in this "
            "run, and a detector that did not fire fails its mutants."
        ),
        "how_stopping_was_established": (
            "each mutant is stopped by the SHIPPED detector the runner maps it "
            "to from its sealed stopper_mechanism, and the runner EXERCISES "
            "that detector on a planted case rather than asserting the "
            "mutant's name is absent from an output — which is what the clause "
            "forbids"
        ),
        "rows": rows,
        "misses": misses,
    }


# --------------------------------------------------------------------------
# B6, B12, B5, B8, B9, B10, B11
# --------------------------------------------------------------------------


def score_b6(prereg: dict, document: dict, inputs) -> dict:
    misses: list[str] = []
    mismatch_rows = []
    fence_rows = []
    for session_id, rows in _sessions(document).items():
        live = _live_session(f"b6-{session_id}", inputs)
        for row in rows:
            live.assumptions.barrier.open_turn(row["turn_index"])
            verdict = harness.route_line(REPO, live, row["line"])
            live.assumptions.barrier.close_turn()
            if row["kind"] != "use":
                continue
            if row["expected_disposition"] == "USE_ARITY_MISMATCH":
                ok = (
                    verdict["route"] == "supposition"
                    and verdict["status"] == "refused"
                    and verdict.get("refusal_type") == SL.REFUSAL_USE_ARITY_MISMATCH
                    and row["cites_declaration_symbol"] in verdict["detail"]
                )
                if not ok:
                    misses.append(f"{row['fixture_id']}: USE_ARITY_MISMATCH not as sealed")
                mismatch_rows.append(
                    {
                        "fixture_id": row["fixture_id"],
                        "refusal_type": verdict.get("refusal_type"),
                        "names_the_declaration": row["cites_declaration_symbol"]
                        in verdict["detail"],
                        "refused_as_sealed": ok,
                    }
                )

    for row in document["fixtures"]:
        if row["kind"] != "use":
            continue
        if row["expected_disposition"] not in {"OPAQUE_ATOM", "BINDING_SUPPOSITION_UNCHANGED"}:
            continue
        with_slice = _live_session("b6-fence-with", inputs)
        without = harness.CoreSession.boot(
            REPO, offline=True, session_id="b6-fence-without"
        )
        without.assumptions = ledger.AssumptionSet(
            session_id="b6-fence-without", barrier=ledger.ReadBarrier()
        )
        with_slice.assumptions.barrier.open_turn(1)
        without.assumptions.barrier.open_turn(1)
        left = harness.route_line(REPO, with_slice, row["line"])
        right = harness.route_line(REPO, without, row["line"])
        with_slice.assumptions.barrier.close_turn()
        without.assumptions.barrier.close_turn()
        identical = left == right
        if not identical:
            misses.append(f"{row['fixture_id']}: the regression fence moved")
        fence_rows.append(
            {"fixture_id": row["fixture_id"], "byte_identical_to_the_pre_slice_path": identical}
        )

    # NON-EMPTINESS FLOORS, read from the seal. Without them both legs are
    # `if expected_disposition == ...` filters, and a corpus that produced no
    # matching row at all would report "0/0" and score GREEN — a gate about
    # "every fixture use" passing because there were none.
    sealed_mismatches = document["counts"]["use_arity_mismatch"]
    sealed_fenced = (
        document["counts"]["use_opaque_atom"] + document["counts"]["use_binding_unchanged"]
    )
    if len(mismatch_rows) != sealed_mismatches:
        misses.append(
            f"{len(mismatch_rows)} wrong-arity use(s) scored, the seal counts "
            f"{sealed_mismatches}"
        )
    if len(fence_rows) != sealed_fenced:
        misses.append(
            f"{len(fence_rows)} fenced use(s) scored, the seal counts {sealed_fenced}"
        )

    return {
        "verdict": _verdict(misses),
        "clause": prereg["gates"]["B6"],
        "sealed_wrong_arity_uses": sealed_mismatches,
        "sealed_fenced_uses": sealed_fenced,
        "wrong_arity_uses": (
            f"{sum(1 for r in mismatch_rows if r['refused_as_sealed'])}/"
            f"{len(mismatch_rows)}"
        ),
        "undeclared_atoms_fenced": f"{sum(1 for r in fence_rows if r['byte_identical_to_the_pre_slice_path'])}/{len(fence_rows)}",
        "how_the_fence_was_checked": (
            "the same line routed twice — once through a session with a symbol "
            "ledger attached and once through a session with none, which IS "
            "the pre-slice code path because the new block is guarded on that "
            "field — and the two verdict dicts compared for equality"
        ),
        "refusal_rows": mismatch_rows,
        "fence_rows": fence_rows,
        "misses": misses,
    }


def score_b12(prereg: dict, document: dict, inputs, replay: Replay) -> dict:
    """The ledger key is the LIVE one, not the seal's expectation of it.

    "Byte-identical to the ledger key" is a claim about the key the running
    ledger holds, so the key set here is `Replay.admitted_key_by_fixture` — what
    the checker actually admitted this run — rather than the symbol names the
    seal expected to be admitted. Reading both sides off the seal would let
    B12 stay green while the live checker admitted something else entirely.
    """

    misses: list[str] = []
    pairs = []
    for session_id, rows in _sessions(document).items():
        keys: set[str] = set()
        for row in rows:
            if row["kind"] == "declaration":
                key = replay.admitted_key_by_fixture.get(row["fixture_id"])
                if key is not None:
                    keys.add(key)
                continue
            target = row.get("round_trip_for")
            if not target:
                continue
            head = SL.applied_head(_rest(row["line"]))
            ok = bool(head) and head[0] == target and head[0] in keys
            if not ok:
                misses.append(f"{row['fixture_id']}: the use did not resolve to the ledger key")
            pairs.append({"fixture_id": row["fixture_id"], "resolves_to_the_ledger_key": ok})

    mutant_rows = []
    for mutant in document["b12_round_trip"]["mutants"]:
        decision = SL.decide(_rest(mutant["line"]), inputs, session_id="b12", turn_index=1)
        expected = (
            decision.verdict.verdict == mutant["expected_verdict"]
            and decision.verdict.refusal_code == mutant["expected_refusal_code"]
            and decision.verdict.deciding_clause == mutant["expected_deciding_clause"]
        )
        resolved = True
        if mutant["expected_resolved_key"]:
            head = SL.applied_head(_rest(mutant["use_line"]))
            resolved = bool(head) and head[0] == mutant["expected_resolved_key"]
        if not expected:
            misses.append(f"{mutant['mutant_id']}: verdict differs from the seal")
        if not resolved:
            misses.append(f"{mutant['mutant_id']}: the admitted name did not round-trip")
        mutant_rows.append(
            {
                "mutant_id": mutant["mutant_id"],
                "adjacency": mutant["adjacency"],
                "verdict_matches_the_seal": expected,
                "round_trips": resolved,
            }
        )

    expected_pairs = prereg["frozen_numbers"]["b12_round_trip_pairs"]
    if len(pairs) != expected_pairs:
        misses.append(f"{len(pairs)} round-trip pairs, sealed {expected_pairs}")
    return {
        "verdict": _verdict(misses),
        "clause": prereg["gates"]["B12"],
        "round_trip_pairs": f"{sum(1 for p in pairs if p['resolves_to_the_ledger_key'])}/{len(pairs)}",
        "mutants": f"{sum(1 for m in mutant_rows if m['verdict_matches_the_seal'] and m['round_trips'])}/{len(mutant_rows)}",
        "byte_identity_note": (
            "the surface the use-side checker resolves is compared against the "
            "LEDGER KEY, not against the bytes the person typed; session "
            "hr-fx-s5 is where those two come apart under casefold expansion"
        ),
        "ledger_key_source": (
            "the keys this run's replay actually admitted, accumulated in turn "
            "order, so a use may only resolve to a symbol declared before it"
        ),
        "pairs": pairs,
        "mutant_rows": mutant_rows,
        "misses": misses,
    }


def score_b8(prereg: dict, document: dict, inputs, replay: Replay) -> dict:
    misses: list[str] = []
    targets = prereg["b8_named_targets"]

    member = targets["census_member_removed"]
    target_fixture = targets["census_member_target_fixture"]
    row = next(r for r in document["fixtures"] if r["fixture_id"] == target_fixture)
    before = replay.rows[target_fixture]["refusal_code"]
    corrupted = SL.CommittedInputs(
        census_path=inputs.census_path,
        census_sha256_lf=inputs.census_sha256_lf,
        equality_members=inputs.equality_members - {member},
        reserved_prefixes=inputs.reserved_prefixes,
        schema_path=inputs.schema_path,
        schema_sha256_lf=inputs.schema_sha256_lf,
        categories=inputs.categories,
    )
    flipped = SL.decide(_rest(row["line"]), corrupted, session_id="b8", turn_index=1)
    arm_one = (
        before == "COLLIDES_WITH_LIBRARY_SYMBOL"
        and flipped.verdict.verdict == SL.VERDICT_ADMITTED
    )
    if not arm_one:
        misses.append("removing the named census member did not flip its fixture to admitted")

    category = targets["schema_category_removed"]
    corrupted_schema = SL.CommittedInputs(
        census_path=inputs.census_path,
        census_sha256_lf=inputs.census_sha256_lf,
        equality_members=inputs.equality_members,
        reserved_prefixes=inputs.reserved_prefixes,
        schema_path=inputs.schema_path,
        schema_sha256_lf=inputs.schema_sha256_lf,
        categories=inputs.categories - {category},
    )
    citing_rows = []
    for fixture_id in targets["schema_category_target_fixtures"]:
        row = next(r for r in document["fixtures"] if r["fixture_id"] == fixture_id)
        moved = SL.decide(_rest(row["line"]), corrupted_schema, session_id="b8", turn_index=1)
        ok = moved.verdict.refusal_code == "CATEGORY_NOT_IN_SCHEMA"
        if not ok:
            misses.append(f"{fixture_id}: did not flip to CATEGORY_NOT_IN_SCHEMA")
        citing_rows.append(
            {
                "fixture_id": fixture_id,
                "before": replay.rows[fixture_id]["verdict"],
                "after": moved.verdict.refusal_code,
            }
        )
    every_citing = [
        r["fixture_id"]
        for r in document["fixtures"]
        if r["kind"] == "declaration"
        and r["expected_verdict"] == SL.VERDICT_ADMITTED
        and category in (r["read_argument_categories"] or [])
    ]
    if sorted(every_citing) != sorted(targets["schema_category_target_fixtures"]):
        misses.append(
            "the prereg's named target fixtures are not every admitted fixture citing "
            f"{category!r}: {sorted(every_citing)}"
        )

    return {
        "verdict": _verdict(misses),
        "clause": prereg["gates"]["B8"],
        "census_arm": {
            "member_removed": member,
            "target_fixture": target_fixture,
            "before": before,
            "after": flipped.verdict.verdict,
            "flipped": arm_one,
        },
        "schema_arm": {
            "category_removed": category,
            "target_fixtures": targets["schema_category_target_fixtures"],
            "rows": citing_rows,
        },
        "mutations_applied_to": "in-memory COPIES; the committed census and schema are never written",
        "misses": misses,
    }


def _surface_features(line: str) -> dict:
    tokens = line.split()
    return {
        "token_count": len(tokens),
        "line_length": len(line),
        "has_command_word": 1 if tokens and tokens[0].casefold() == "declare" else 0,
    }


def score_b9(prereg: dict, document: dict, replay: Replay) -> dict:
    """A surface-only admitter, fitted on the fit half and scored on the other.

    The hypothesis space is every threshold rule over the three ALLOWED
    features plus the two constant predictors, enumerated and scored on the
    fit half; the best is carried to the scored half. Ties break on the
    lexicographically smallest rule id, so the control is deterministic and
    has no seed.
    """

    control = prereg["b9_control"]
    by_id = {row["fixture_id"]: row for row in document["fixtures"]}
    truth = {
        fixture_id: replay.rows[fixture_id]["verdict"]
        for fixture_id in control["fit_half_fixture_ids"] + control["scored_half_fixture_ids"]
    }

    candidates: list[tuple[str, Any]] = []
    for feature in ("token_count", "line_length", "has_command_word"):
        values = sorted(
            {_surface_features(by_id[f]["line"])[feature] for f in truth}
        )
        for value in values:
            for op in ("le", "ge", "eq"):
                rule_id = f"{feature}:{op}:{value}"
                candidates.append((rule_id, (feature, op, value)))
    candidates.append(("const:ADMITTED_DECLARED_SYMBOL", ("const", "", SL.VERDICT_ADMITTED)))
    candidates.append(("const:REFUSED", ("const", "", SL.VERDICT_REFUSED)))
    candidates.sort(key=lambda item: item[0])

    def predict(rule, line: str) -> str:
        feature, op, value = rule
        if feature == "const":
            return value
        actual = _surface_features(line)[feature]
        hit = (
            actual <= value
            if op == "le"
            else actual >= value
            if op == "ge"
            else actual == value
        )
        return SL.VERDICT_ADMITTED if hit else SL.VERDICT_REFUSED

    def accuracy(rule, ids) -> float:
        correct = sum(1 for f in ids if predict(rule, by_id[f]["line"]) == truth[f])
        return correct / len(ids)

    fit_ids = control["fit_half_fixture_ids"]
    scored_ids = control["scored_half_fixture_ids"]
    # Deterministic tie-break: highest fit accuracy, then smallest rule id.
    top = max(accuracy(rule, fit_ids) for _, rule in candidates)
    best_id, best_rule = min(
        ((rid, rule) for rid, rule in candidates if accuracy(rule, fit_ids) == top),
        key=lambda item: item[0],
    )

    # ROUNDED BEFORE THE COMPARISON, and reported at the same precision the
    # comparison used. The prereg insists the strict-vs-loose reading not be
    # left to be read off code; two programs comparing at two precisions on
    # either side of that sentence would put it straight back there.
    agreement = round(accuracy(best_rule, scored_ids), 6)
    fit_accuracy = round(accuracy(best_rule, fit_ids), 6)
    threshold = prereg["frozen_numbers"]["b9_void_threshold"]
    anchor = prereg["frozen_numbers"]["b9_scored_half_majority_class_rate"]
    fired = agreement > threshold

    misses: list[str] = []
    if fired:
        misses.append(
            "the voiding sentence fired: the surface-only admitter's out-of-half "
            f"agreement {agreement:.6f} exceeds the threshold {threshold}"
        )
    return {
        "verdict": _verdict(misses),
        "clause": prereg["gates"]["B9"],
        "fitted_rule": best_id,
        "fit_half_accuracy": fit_accuracy,
        "out_of_half_agreement": agreement,
        "compared_at_precision": 6,
        "scored_half_majority_class_rate": anchor,
        "declared_margin_points": prereg["frozen_numbers"]["b9_declared_margin_points"],
        "void_threshold": threshold,
        "fired": fired,
        "comparison": "strict >: the agreement must EXCEED the threshold to fire",
        "agreement_equals_the_threshold": agreement == threshold,
        "equality_is_not_a_firing": control["equality_is_not_a_firing"],
        "equality_note": prereg["b9_control"]["equality_note"],
        "sealed_class_balance": document["b9_class_balance"]["scored_half_balance"],
        "hypothesis_space": len(candidates),
        "inputs_used": control["admitter_inputs_allowed"],
        "inputs_refused": control["admitter_inputs_forbidden"],
        "candidate_values_enumerated_over": "both halves",
        "candidate_values_note": (
            "DELIBERATE and disclosed: the threshold VALUES a rule may test "
            "are enumerated over the whole declaration corpus, not the fit "
            "half alone. That is leakage in the control's favour — it can "
            "only raise the surface-only admitter's agreement and therefore "
            "makes the voiding sentence EASIER to fire. Restricting the "
            "enumeration to the fit half would hand the control less power, "
            "which is the wrong direction for a check whose job is to void "
            "the capability if it can"
        ),
        "degenerate_features": [
            feature
            for feature in ("token_count", "line_length", "has_command_word")
            if len({_surface_features(by_id[f]["line"])[feature] for f in truth}) == 1
        ],
        "degenerate_features_note": (
            "an allowed feature that takes ONE value across the whole "
            "declaration corpus carries no signal and its threshold rules "
            "collapse to the two constant predictors; reported rather than "
            "left to be inferred from the fitted rule"
        ),
        "voiding_sentence": control["voiding_sentence"],
        "misses": misses,
    }


def score_b4_b5(
    prereg: dict,
    document: dict,
    inputs,
    replay: Replay,
    digest_before: dict,
    digest_after: dict,
    pending_outputs: dict,
) -> tuple[dict, dict]:
    misses4: list[str] = []
    if digest_before["working_tree_digest"] != digest_after["working_tree_digest"]:
        misses4.append("write_stage.working_tree_digest moved across the run")
    if digest_before["durable_digest"] != digest_after["durable_digest"]:
        misses4.append("durable_digest over data/ moved across the run")
    appeared = sorted(set(digest_after["paths"]) - set(digest_before["paths"]))
    vanished = sorted(set(digest_before["paths"]) - set(digest_after["paths"]))
    if appeared:
        misses4.append(f"paths appeared during the run: {appeared[:8]}")
    if vanished:
        misses4.append(f"paths vanished during the run: {vanished[:8]}")
    staging = REPO / "staging"
    stage_records = (
        sorted(p.name for p in staging.glob("*.json")) if staging.is_dir() else []
    )
    if stage_records:
        misses4.append(f"{len(stage_records)} stage record(s) exist")

    b4 = {
        "verdict": _verdict(misses4),
        "clause": prereg["gates"]["B4"],
        "working_tree_digest_before": digest_before["working_tree_digest"],
        "working_tree_digest_after": digest_after["working_tree_digest"],
        "working_tree_digest_byte_identical": (
            digest_before["working_tree_digest"] == digest_after["working_tree_digest"]
        ),
        "durable_digest_before": digest_before["durable_digest"],
        "durable_digest_after": digest_after["durable_digest"],
        "durable_digest_byte_identical": (
            digest_before["durable_digest"] == digest_after["durable_digest"]
        ),
        "narrow_control_note": (
            "durable_digest covers data/ only and is the NARROW named control; "
            "the gate is the wider working_tree_digest, because durable_digest's "
            "own docstring names the scripts/ escape it cannot see"
        ),
        "declared_output_paths": list(prereg["declared_output_paths"]),
        "declared_output_paths_note": (
            "both digests are taken BEFORE either output is written, so the two "
            "declared paths are absent from both sides of the comparison rather "
            "than subtracted from one — the exclusion is structural"
        ),
        "paths_that_appeared": appeared,
        "paths_that_vanished": vanished,
        "stage_records": len(stage_records),
        "misses": misses4,
    }

    misses5: list[str] = []
    admitted = replay.admitted_names()

    # THE RUN'S OUTPUT TREE, and only that. Rehearsal is how the scope was
    # settled: swept over the whole repository the sweep finds 21 files, every
    # one of them a PRE-EXISTING committed file — the sealed corpus that names
    # the fixtures, its builder, and the H-P0 tests. None is a document this
    # run wrote, and a gate about what a run persists cannot be scored against
    # files that predate it. So the sweep covers exactly what the run
    # produced: the two declared outputs, plus every path B4 observed
    # appearing or changing while the run executed (B4 observed none), plus
    # the directories a session write would land in, checked for new files.
    written = {
        RUN_OUT: json.dumps(pending_outputs["verdicts"], ensure_ascii=False),
        RECEIPTS_OUT: json.dumps(pending_outputs["receipts"], ensure_ascii=False),
    }
    hits = []
    folded = [name.casefold() for name in admitted]
    for path, text in written.items():
        lowered = text.casefold()
        if any(name in lowered for name in folded):
            hits.append({"path": path})
    appeared_during_the_run = sorted(
        set(digest_after["paths"]) - set(digest_before["paths"])
    )
    for relative in appeared_during_the_run:
        try:
            text = (REPO / relative).read_text(encoding="utf-8", errors="ignore").casefold()
        except OSError:  # pragma: no cover
            continue
        if any(name in text for name in folded):
            hits.append({"path": relative})
    journal_dirs = ["experiments/sessions", "reports", "staging"]
    new_journal_files = sorted(
        relative
        for relative in appeared_during_the_run
        if any(relative.startswith(f"{d}/") for d in journal_dirs)
    )
    # DISCLOSURE, measured rather than asserted. The clause scopes the sweep
    # to the run's output tree ("swept over the run's full output tree",
    # DESIGN §7 B5), so the whole repository is NOT what B5 asks for — but the
    # size of the difference is exactly what a reader needs to judge the
    # scoping, so the runner sweeps the whole tree too and publishes the
    # number and the paths. Every hit must have existed BEFORE the run: that
    # is checked against the pre-run path list, so "they all predate the run"
    # is a finding here and not a claim. The two declared outputs are skipped
    # so the figure is the same before they exist and after they are
    # committed, which is what lets `check_house_rules_receipts.py` recompute
    # it from the committed bytes.
    repo_rows, unreadable = _sweep_tree_for_names(
        REPO, admitted, skip=(RUN_OUT, RECEIPTS_OUT)
    )
    repo_hits = [row["path"] for row in repo_rows]
    if unreadable:
        misses5.append(
            f"{len(unreadable)} file(s) could not be read by the sweep, so the "
            f"gate covers less than it claims: {unreadable[:8]}"
        )
    before_paths = set(digest_before["paths"])
    not_pre_existing = sorted(path for path in repo_hits if path not in before_paths)
    if not_pre_existing:
        misses5.append(
            f"{len(not_pre_existing)} file(s) containing an admitted name did not "
            f"exist before the run: {not_pre_existing[:8]}"
        )
    if hits:
        misses5.append(
            f"{len(hits)} document(s) the run produced contain an admitted name"
        )
    if new_journal_files:
        misses5.append(
            f"the run wrote {len(new_journal_files)} session document(s) or journal(s)"
        )
    encode_refusals = []
    decision = SL.decide(
        "probe_of/2 (variable, variable)", inputs, session_id="b5", turn_index=1
    )
    for record in (decision.declaration, decision.verdict):
        try:
            session_state.encode(record)
            encode_refusals.append("ENCODED")
            misses5.append(f"session_state.encode accepted {type(record).__name__}")
        except session_state.SessionFormatError:
            encode_refusals.append(f"refused {type(record).__name__}")
    fresh = _live_session("b5-fresh", inputs)
    s4 = next(
        r for r in document["fixtures"] if r["session_id"] == "hr-fx-s4" and r["kind"] == "use"
    )
    fresh.assumptions.barrier.open_turn(1)
    fresh_verdict = harness.route_line(REPO, fresh, s4["line"])
    fresh.assumptions.barrier.close_turn()
    opaque = fresh.symbols.check_use(_rest(s4["line"])) is None
    if not opaque:
        misses5.append("a fresh session did not take the opaque-atom path")

    b5 = {
        "verdict": _verdict(misses5),
        "clause": prereg["gates"]["B5"],
        "admitted_symbol_names_swept_for": len(admitted),
        "admitted_names_are_not_listed_here": (
            "the count is reported and the names are not, because this artifact "
            "is itself inside the swept tree; they are in the sealed corpus"
        ),
        "documents_the_run_produced": sorted(written),
        "documents_containing_an_admitted_name": len(hits),
        "paths_that_appeared_during_the_run": appeared_during_the_run,
        "session_documents_or_journals_written": new_journal_files,
        "journal_directories_checked": journal_dirs,
        "sweep_scope": (
            "the run's OUTPUT tree: the two declared outputs — the verdicts "
            "document in FULL, with only the B4 and B5 rows held out because "
            "they are what this sweep produces — plus every path that "
            "appeared or changed while the run executed. Pre-existing "
            "committed files are outside it: the sealed corpus names the "
            "fixture symbols by construction and predates this run, and the "
            "count of those files is disclosed below"
        ),
        "held_out_of_the_swept_document": ["construction_gate.B4", "construction_gate.B5"],
        "held_out_note": (
            "those two rows carry digests, counts and paths and no symbol "
            "name; the re-sweep in check_house_rules_receipts.py covers the "
            "committed bytes including them, which is the falsifiable side"
        ),
        "sweep_scope_note": prereg["outputs_name_no_admitted_symbol_note"],
        "no_carve_out_for_the_declared_outputs": True,
        "whole_repository_sweep_disclosure": {
            "is_the_gate": False,
            "why_reported": (
                "the clause scopes the sweep to the run's output tree, so this "
                "wider number scores nothing — it is published so the scoping "
                "can be judged against a measurement instead of a description"
            ),
            "scope": (
                "every file in the repository under the write_stage integrity "
                "exclusions, minus the two declared output paths — skipped so "
                "the figure is identical before they exist and after they are "
                "committed, and so a replay reproduces it"
            ),
            "hits": len(repo_hits),
            "paths": repo_hits,
            "files_that_could_not_be_read": unreadable,
            "all_hits_existed_before_the_run": not not_pre_existing,
            "hits_that_did_not_exist_before_the_run": not_pre_existing,
            "how_pre_existence_was_established": (
                "membership in the path list taken before any gate was scored, "
                "not an author's claim about which files are old"
            ),
            "recomputable_by": RECEIPT_CHECKER,
        },
        "encode": encode_refusals,
        "fresh_session_takes_the_opaque_path": opaque,
        "fresh_session_fixture": s4["fixture_id"],
        "fresh_session_status": fresh_verdict["status"],
        "scope_sentence": prereg["b5_scope_sentence"],
        "misses": misses5,
    }
    return b4, b5


def score_b10(prereg: dict, tree: dict) -> dict:
    misses: list[str] = []
    if not tree["sealed_commit_is_strict_ancestor_of_head"]:
        misses.append("the sealed commit is not a strict ancestor of the scoring tip")
    if tree["frozen_pins_that_moved"]:
        misses.append(f"frozen pins moved: {tree['frozen_pins_that_moved']}")
    if tree["dirty"]:
        misses.append("the scoring tree is dirty")
    if not tree["registered_before_the_run"]:
        misses.append("registered_before_the_run is false")
    return {
        "verdict": _verdict(misses),
        "clause": prereg["gates"]["B10"],
        "sealed_commit": prereg["sealed_commit"],
        "head_commit": tree["head_commit"],
        "ancestry_proof": (
            "git merge-base --is-ancestor "
            f"{prereg['sealed_commit'][:12]} {(tree['head_commit'] or '')[:12]} "
            "-> " + ("true" if tree["sealed_commit_is_strict_ancestor_of_head"] else "false")
        ),
        "ancestry_is_strict": True,
        "frozen_pins_verified": len(prereg["frozen"]),
        "frozen_pins_that_moved": tree["frozen_pins_that_moved"],
        "first_commit_of": tree["first_commit_of"],
        "registered_before_the_run": tree["registered_before_the_run"],
        "misses": misses,
    }


def score_b11(prereg: dict) -> dict:
    from echo_population_audit import import_closure  # noqa: PLC0415

    forbidden = (
        "torch", "numpy", "scipy", "sklearn", "transformers", "sentence_transformers",
        "tensorflow", "jax", "openai", "anthropic", "plain_router", "proposer",
        "wordnet", "nltk", "retrieve",
    )
    misses: list[str] = []
    closures = {}
    for module in (LEDGER_MODULE, CENSUS_CHECKER, "scripts/build_symbol_census.py"):
        closure = import_closure(module)
        closures[module] = closure
        for member in closure:
            tree = ast.parse((REPO / member).read_text(encoding="utf-8"))
            names: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names.add(node.module.split(".")[0])
            for name in forbidden:
                if name in names:
                    misses.append(f"{member} imports {name!r}")
    return {
        "verdict": _verdict(misses),
        "clause": prereg["gates"]["B11"],
        "closures": closures,
        "closure_size": {module: len(c) for module, c in closures.items()},
        "forbidden_modules": list(forbidden),
        "two_checks_note": (
            "import_closure resolves REPOSITORY-LOCAL files only, so a "
            "third-party import is invisible to it; the source scan over every "
            "closure member is what covers the third-party names, and it parses "
            "with ast so a name in a docstring is not mistaken for an import"
        ),
        "misses": misses,
    }


# --------------------------------------------------------------------------
# R-H2
# --------------------------------------------------------------------------


def score_r_h2(prereg: dict) -> dict:
    hypotheses = json.loads((REPO / HYPOTHESES).read_text(encoding="utf-8"))
    rows = hypotheses["hypotheses"]
    parsed_rows = []
    for row in rows:
        text = row[prereg["r_h2"]["population_field"]]
        parsed = SL.parse_declaration(text)
        if parsed is not None:
            parsed_rows.append(
                {"hypothesis_id": row["hypothesis_id"], "verbatim": text}
            )
        # A declaration line would still carry the command word; the arm also
        # tries the text with the command word stripped, which is the more
        # generous reading and can only raise the count.
        stripped = SL.parse_declaration(_rest(text))
        if stripped is not None and not any(
            r["hypothesis_id"] == row["hypothesis_id"] for r in parsed_rows
        ):
            parsed_rows.append(
                {"hypothesis_id": row["hypothesis_id"], "verbatim": text}
            )
    return {
        "population": prereg["r_h2"]["population"],
        "population_size": len(rows),
        "population_size_sealed": prereg["r_h2"]["population_size"],
        "parse_as_declarations": len(parsed_rows),
        "rows": parsed_rows,
        "threshold": None,
        "gates_nothing": True,
        "how_counted": (
            "each hypothesis_text is offered to symbol_ledger.parse_declaration "
            "whole AND with its first token stripped; the more generous reading "
            "is taken, so the number can only be too high"
        ),
        "precommitted_reading": prereg["r_h2"]["precommitted_reading"],
    }


# --------------------------------------------------------------------------
# the run
# --------------------------------------------------------------------------


def _digests() -> dict:
    return {
        "working_tree_digest": write_stage.working_tree_digest(REPO),
        "durable_digest": write_stage.durable_digest(REPO / "data"),
        "paths": _covered_paths(REPO),
    }


def provenance() -> dict:
    inputs = [PREREG, FIXTURES, CENSUS, SCHEMA, LEDGER_MODULE, CENSUS_CHECKER, HYPOTHESES]
    return {
        "writer": THIS,
        "writer_sha256_lf": sha256_lf(REPO / THIS),
        "inputs": [
            {"path": path, "sha256_lf": sha256_lf(REPO / path)}
            for path in sorted(inputs)
            if (REPO / path).is_file()
        ],
        # Not an input — the program that reads this artifact back and tries to
        # falsify it. Pinned here so which checker was frozen beside the run is
        # a fact in the artifact rather than a fact about the commit log.
        "second_program": {
            "path": RECEIPT_CHECKER,
            "sha256_lf": (
                sha256_lf(REPO / RECEIPT_CHECKER)
                if (REPO / RECEIPT_CHECKER).is_file()
                else None
            ),
        },
        "emitted_at_generation": True,
    }


def _receipts_document(prereg: dict, tree: dict, replay: "Replay") -> dict:
    """The per-fixture verdict table. Fixture ids only; no admitted names."""

    return {
        "schema": RECEIPTS_SCHEMA,
        "design": DESIGN,
        "stage": STAGE,
        "date": DATE,
        "preregistration": PREREG,
        "preregistration_id": prereg["preregistration_id"],
        "preregistration_sha256_lf": sha256_lf(REPO / PREREG),
        "registration_commit": tree["first_commit_of"][PREREG],
        "registered_before_the_run": tree["registered_before_the_run"],
        "emitted_by": THIS,
        "replay_definition": (
            "every declaration fixture in the sealed corpus, replayed session "
            "by session in turn index order, with the three-source session-name "
            "union carried turn to turn exactly as a live session carries it"
        ),
        "receipt_count": len(replay.rows),
        "carries_no_admitted_symbol_name": True,
        "receipts": [replay.rows[key] for key in sorted(replay.rows)],
        "provenance": provenance(),
    }



def run(out_path: Path, receipts_path: Path, allow_dirty: bool = False) -> tuple[dict, dict]:
    refuse_existing(out_path, "verdicts")
    refuse_existing(receipts_path, "receipts")

    prereg = json.loads((REPO / PREREG).read_text(encoding="utf-8"))
    tree = scoring_tree(prereg, allow_dirty)
    document = json.loads((REPO / FIXTURES).read_text(encoding="utf-8"))
    inputs = SL.load_inputs(REPO)

    digest_before = _digests()

    replay = Replay(document, inputs)
    detectors = _detectors(document, inputs)
    b1, b7, sweep_meta = score_b1_b7(prereg, document, inputs, replay)
    b2 = score_b2(prereg, document, inputs, replay)
    b3 = score_b3(prereg, document, detectors)
    b6 = score_b6(prereg, document, inputs)
    b8 = score_b8(prereg, document, inputs, replay)
    b9 = score_b9(prereg, document, replay)
    b10 = score_b10(prereg, tree)
    b11 = score_b11(prereg)
    b12 = score_b12(prereg, document, inputs, replay)

    digest_after = _digests()

    receipts = _receipts_document(prereg, tree, replay)
    r_h2 = score_r_h2(prereg)

    # B4 and B5 are scored LAST, against the documents this run is about to
    # write — and the document B5 sweeps is now the WHOLE verdicts document
    # with those two rows held out, not the gate table alone. The earlier
    # shape swept a fragment and therefore never looked at `counts`,
    # `scoring_tree`, `result_gates` (R-H2 quotes hypothesis text verbatim),
    # `non_claims` or `provenance`. The only difference between what is swept
    # and what is written is the B4 and B5 rows themselves, which carry
    # digests, counts and paths and no symbol name — and
    # `check_house_rules_receipts.py` re-sweeps the COMMITTED bytes, which is
    # the side of this a second program can falsify.
    scored = {
        "B1": b1, "B2": b2, "B3": b3, "B4": None, "B5": None, "B6": b6,
        "B7": b7, "B8": b8, "B9": b9, "B10": b10, "B11": b11, "B12": b12,
    }
    provisional = _verdicts_document(
        prereg, document, tree, replay, sweep_meta, scored, r_h2
    )
    b4, b5 = score_b4_b5(
        prereg,
        document,
        inputs,
        replay,
        digest_before,
        digest_after,
        {"receipts": receipts, "verdicts": provisional},
    )
    scored["B4"], scored["B5"] = b4, b5
    verdicts = _verdicts_document(
        prereg, document, tree, replay, sweep_meta, scored, r_h2
    )
    return verdicts, receipts


def _verdicts_document(
    prereg: dict,
    document: dict,
    tree: dict,
    replay: "Replay",
    sweep_meta: dict,
    gate: dict,
    r_h2: dict,
) -> dict:
    """The run artifact. Called twice: once with B4/B5 held out for B5's own
    sweep, once with them in place. Everything else is identical between the
    two, which is what makes the sweep a sweep of what gets written."""

    b9 = gate["B9"]
    greens = {
        name: bool(row) and row["verdict"] == "GREEN" for name, row in gate.items()
    }
    reds = sorted(name for name in SCORED_GATES if not greens[name])
    r_h1_requires = prereg["r_h1_requires"]
    r_h1_green = (
        all(greens[name] for name in r_h1_requires)
        and not b9["fired"]
        and tree["registered_before_the_run"]
    )
    r_h3_reds = sorted(name for name in R_H3_GATES if name in reds)
    return {
        "schema": RUN_SCHEMA,
        "design": DESIGN,
        "design_clause": prereg["design_clause"],
        "stage": STAGE,
        "date": DATE,
        "preregistration": PREREG,
        "preregistration_id": prereg["preregistration_id"],
        "preregistration_sha256_lf": sha256_lf(REPO / PREREG),
        "registration_commit": tree["first_commit_of"][PREREG],
        "registered_before_the_run": tree["registered_before_the_run"],
        "scoring_tree": tree,
        "sealed_commit": prereg["sealed_commit"],
        "receipts_artifact": {
            "path": RECEIPTS_OUT,
            "receipt_count": len(replay.rows),
            "note": "the per-fixture verdict table; gate scoring lives here",
        },
        "counts": {
            "fixtures_total": document["counts"]["fixtures_total"],
            "declaration_fixtures": document["counts"]["declaration_fixtures"],
            "use_fixtures": document["counts"]["use_fixtures"],
            "admitted": document["counts"]["admitted"],
            "refused": document["counts"]["refused"],
            "b3_mutants": document["counts"]["b3_mutants"],
            "b12_mutants": document["counts"]["b12_mutants"],
            "sweep_inputs": sweep_meta["distinct_scored"],
        },
        "construction_gate": gate,
        "gate_greens": greens,
        "gate_reds": reds,
        "voiding_sentence": {
            "text": prereg["b9_control"]["voiding_sentence"],
            "fired": b9["fired"],
            "agreement": b9["out_of_half_agreement"],
            "threshold": b9["void_threshold"],
        },
        "result_gates": {
            "R-H1": {
                "requires": r_h1_requires,
                "requires_note": prereg["r_h1_requires_note"],
                "green": r_h1_green,
                "licensed_sentence": prereg["r_h1_sentence"] if r_h1_green else None,
                "why_not": None
                if r_h1_green
                else (
                    f"reds: {reds}; voiding fired: {b9['fired']}; "
                    f"registered_before_the_run: {tree['registered_before_the_run']}"
                ),
                "b12_reported_beside": {
                    "green": greens["B12"],
                    "note": (
                        "B12 postdates §8's R-H1 sentence and is not in its "
                        "requirement list; it is scored and reported, never "
                        "folded in"
                    ),
                },
            },
            "R-H2": r_h2,
            "R-H3": {
                "clause": prereg["r_h3"],
                "gates_in_scope": list(R_H3_GATES),
                "gates_in_scope_source": (
                    "the clause names 'any failed construction gate "
                    "B1-B8/B10/B11 or a fired B9'. B9 enters through the "
                    "firing clause rather than through its verdict, and B12 "
                    "postdates the sentence: a red B12 alone is REPORTED and "
                    "does not by itself license the bounded negative. Read "
                    "off the clause here rather than widened to every scored "
                    "gate, which is what `bool(reds)` would have done"
                ),
                "licensed": bool(r_h3_reds) or b9["fired"],
                "reds_in_scope": r_h3_reds,
                "reds_outside_the_scope": [n for n in reds if n not in R_H3_GATES],
                "reds": reds,
            },
        },
        "non_claims": list(prereg["non_claims"]),
        "provenance": provenance(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=REPO / RUN_OUT)
    parser.add_argument("--receipts-out", type=Path, default=REPO / RECEIPTS_OUT)
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help=(
            "score a dirty or wrong-tip tree for PRE-RUN TESTING ONLY. Recorded "
            "in the artifact as registered_before_the_run: false, which "
            "withholds every §8 sentence."
        ),
    )
    args = parser.parse_args(argv)

    try:
        verdicts, receipts = run(
            out_path=args.out,
            receipts_path=args.receipts_out,
            allow_dirty=args.allow_dirty,
        )
    except RunRefusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    write_once(args.receipts_out, receipts)
    write_once(args.out, verdicts)
    print(f"wrote {args.receipts_out}")
    print(f"wrote {args.out}")
    for name, row in verdicts["construction_gate"].items():
        detail = row.get("misses") or []
        print(
            f"  {name}: {row['verdict']}"
            + (f"  ({len(detail)} miss(es))" if detail else "")
        )
    print(f"voiding sentence fired: {verdicts['voiding_sentence']['fired']}")
    print(f"R-H2 parses as declarations: {verdicts['result_gates']['R-H2']['parse_as_declarations']}/30")
    print(f"R-H1 green: {verdicts['result_gates']['R-H1']['green']}")
    return 0 if not verdicts["gate_reds"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
