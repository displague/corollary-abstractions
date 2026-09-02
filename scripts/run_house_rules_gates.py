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

## What the H-P1 adversarial review changed here (2026-09-02)

Run 1 (`2ac8c9f`) scored twelve green and is retained under
`experiments/superseded/`. An independent review returned MERGE AFTER FIXES:
every number reproduced, and the findings were about checks that could not
fail, scope that was not disclosed, and one real leak. What moved:

* **B3 does not execute mutants and now says so.** The 32 mutants are prose;
  the id-to-detector map is authored here; each row publishes its sealed
  `stopper_mechanism` beside the detector, and a mechanical class check
  reports every id whose detector belongs to no class the seal names.
* **Two B3 detectors could not fail and were repaired or retired.**
  `name_sweep` planted a name in a temporary directory and found it; it now
  runs the live B5 sweep over the real tree and the run's own pending output.
  `checker_inputs_exclude_the_runs_outputs` asserted an absence that is true
  of every module; it is retired and its mutant re-pointed.
* **b3-m08's vector was in the tree while run 1 scored it STOPPED.** The
  served `declare` grammar example carried an ADMITTED fixture symbol. The
  example is now a placeholder that appears nowhere in the corpus, and
  `grammar_example_names` is the detector that sees such a leak.
* **B9 discloses that its registered family could not fire.** The family
  ceiling on the scored half, the fitted rule's degeneracy, and a richer
  family fitted on the fit half with a pre-declared tie-break are all
  reported. The gate stays computed from the REGISTERED family.
* **B6 gained the populated-ledger arm**, B12's mutant arm compares against
  the live ledger key, B2's counts are relabelled, and three hardcoded
  booleans are computed.

Usage::

    python scripts/run_house_rules_gates.py
    python scripts/run_house_rules_gates.py --allow-dirty \\
        --out /tmp/v.json --receipts-out /tmp/r.json   # rehearsal, licenses nothing
"""

from __future__ import annotations

import argparse
import ast
import copy
import hashlib
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
COMMAND_BOUND = "experiments/session_p1_command_bound.json"
SERVE_CHAT = "scripts/serve_chat.py"

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


def _last_commit(path: str) -> str | None:
    """The commit whose bytes the tree carries for `path` today."""

    line = _git("log", "-1", "--format=%H", "--", path).strip()
    return line or None


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
                (
                    _rest(" ".join(tokens[:index] + tokens[index + 1 :])),
                    fixture_id,
                    context,
                    index,
                )
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
                        index,
                    )
                )
    seen: set[tuple[str, str]] = set()
    ordered: list[tuple] = []
    for text, fixture_id, context, index in sweep:
        key = (text, fixture_id)
        if key in seen:
            continue
        seen.add(key)
        ordered.append((text, fixture_id, context, index))
    ordered.sort(key=lambda item: (item[0], item[1]))

    # F13's repair. These three fields were hardcoded booleans in run 1 — a
    # runner asserting a property of its own output. They are computed here
    # from the sweep that was actually built, and B7 reads the second one
    # rather than a constant.
    alphabet_set = set(alphabet)
    outside = sorted(
        {
            token
            for text, _fixture, _context, _index in ordered
            for token in text.split()
            if token not in alphabet_set
        }
    )
    from_the_command_word = sum(1 for item in ordered if item[3] == 0)
    alphabet_sha256 = hashlib.sha256(
        json.dumps(alphabet, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
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
        "mutation_covers_the_command_word": from_the_command_word > 0,
        "mutants_whose_mutated_token_index_is_zero": from_the_command_word,
        "mutation_covers_the_command_word_how": (
            "COMPUTED, not asserted: the mutated token index is carried on "
            "every sweep row and this is the count of rows whose index is 0 — "
            "the command word's own position"
        ),
        "evaluated_in_context": True,
        "evaluated_in_context_note": (
            "each mutant is decided in the session context its SOURCE FIXTURE "
            "occupied — the symbols admitted in that session before that turn, "
            "and the three-source session-name union as it stood. Three of the "
            "eight codes are clauses about session state and are unreachable "
            "by any stateless input, so a context-free sweep would report a "
            "property of the harness as a property of the checker."
        ),
        "authored_toward_a_code": bool(outside),
        "authored_toward_a_code_how": (
            "COMPUTED, not asserted: every token of every scored mutant is "
            "checked for membership in the fixture alphabet, which is itself "
            "enumerated from the sealed corpus. A sweep containing a token no "
            "fixture line carries could only have been authored, and the "
            "tokens that failed are listed below. The alphabet is pinned by "
            "digest so a later reader can recompute the set this was checked "
            "against"
        ),
        "tokens_outside_the_fixture_alphabet": outside,
        "alphabet_sha256": alphabet_sha256,
        "alphabet_sha256_rule": (
            "sha256 of json.dumps(sorted_alphabet, ensure_ascii=False) encoded "
            "utf-8"
        ),
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
    for text, _source, (ctx_admitted, ctx_names), _mutated_index in sweep:
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
    if meta["authored_toward_a_code"]:
        misses7.append(
            "the sweep carries tokens outside the fixture alphabet, so it was "
            f"not enumerated from the seal: {meta['tokens_outside_the_fixture_alphabet'][:8]}"
        )

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
        "no_sweep_input_authored_toward_a_code": not meta["authored_toward_a_code"],
        "no_sweep_input_authored_toward_a_code_how": meta["authored_toward_a_code_how"],
        "sweep_alphabet_sha256": meta["alphabet_sha256"],
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

    live = sorted(set(replay.admitted_key_by_fixture.values()))
    sealed_b12 = sorted(
        {
            mutant["expected_resolved_key"]
            for mutant in document["b12_round_trip"]["mutants"]
            if mutant["expected_resolved_key"]
        }
    )
    return {
        "verdict": _verdict(misses),
        "clause": prereg["gates"]["B2"],
        # F12's relabel. Run 1 reported `admissions: 17` beside a corpus whose
        # sealed `counts.admitted` is 13, and the two numbers are not the same
        # thing: 17 is the UNION of the 13 keys this run's replay admitted and
        # the 7 reserved-prefix-adjacent keys B12's mutants seal, three of
        # which appear in both. The union is what B2 sweeps, because a name
        # sealed as admissible is a name the census must not already hold
        # whichever arm admits it.
        "admitted_names_swept": len(admitted),
        "live_admissions": len(live),
        "sealed_b12_mutant_keys": len(sealed_b12),
        "names_in_both": len(set(live) & set(sealed_b12)),
        "union_note": (
            "admitted_names_swept = |live_admissions U sealed_b12_mutant_keys|; "
            "live_admissions is the corpus count the seal carries as "
            "counts.admitted"
        ),
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


def _prereg_frozen() -> list[dict]:
    """The prereg's `frozen` rows, read from the committed registration."""

    return json.loads((REPO / PREREG).read_text(encoding="utf-8"))["frozen"]


def _detectors(
    document: dict, inputs, replay: Replay, pending_receipts: dict
) -> dict[str, dict]:
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

    # F2's repair, and the reason this detector is now able to fail. Until the
    # H-P1 review it planted a name in a `TemporaryDirectory` and found it
    # again — a property of `str.__contains__`, true of any tree — and it
    # carried seven mutants. It now runs the sweep B5 runs, against the LIVE
    # repository tree and against the bytes this run is about to write:
    #
    #  * POSITIVE CONTROL, ON THE REAL TREE. The sealed corpus is a committed
    #    file that carries every admitted fixture name by construction, so a
    #    sweep that finds nothing in the repository is a broken sweep and not
    #    a clean tree. The hit list is the one B5 discloses.
    #  * NEGATIVE CONTROL, ON THE REAL TREE. A name no committed file carries
    #    must find nothing, so the sweep is not matching everything.
    #  * PLANTED CONTROL, on an IN-MEMORY COPY of the pending output bytes: an
    #    admitted name appended to the receipts document is found, which shows
    #    the sweep would catch a plant in the REAL output.
    #  * THE VECTOR, and the half that can actually go red: the pending
    #    receipts document, unplanted, carries no admitted name.
    admitted_names = replay.admitted_names()
    # The negative control's probe name is DERIVED rather than written down.
    # A string literal for it would live in this file, this file is inside the
    # tree the sweep covers, and the control would then find its own source
    # and report that the sweep matches everything. Deterministic, no clock,
    # no random source, and absent from the tree by construction.
    absent_probe = "absent_" + hashlib.sha256(
        b"house-rules/b3/name_sweep/negative-control"
    ).hexdigest()[:24]
    tree_hits, tree_unreadable = _sweep_tree_for_names(
        REPO, admitted_names, skip=(RUN_OUT, RECEIPTS_OUT)
    )
    tree_clean, _ = _sweep_tree_for_names(
        REPO, [absent_probe], skip=(RUN_OUT, RECEIPTS_OUT)
    )
    pending_text = json.dumps(pending_receipts, ensure_ascii=False).casefold()
    pending_hits = sum(1 for name in admitted_names if name.casefold() in pending_text)
    planted_text = pending_text + admitted_names[0].casefold()
    planted_caught = any(name.casefold() in planted_text for name in admitted_names)
    out["name_sweep"] = {
        "fires": (
            not tree_unreadable
            and bool(tree_hits)
            and not tree_clean
            and pending_hits == 0
            and planted_caught
        ),
        "kind": (
            "the live B5 sweep: positive and negative controls on the REAL "
            "repository tree, a planted control on an in-memory copy of the "
            "bytes this run is about to write, and the vector itself — the "
            "unplanted pending output — as the arm that can go red"
        ),
        "observed": {
            "repository_files_carrying_an_admitted_name": len(tree_hits),
            "repository_files_carrying_an_absent_probe_name": len(tree_clean),
            "repository_files_the_sweep_could_not_read": len(tree_unreadable),
            "pending_receipts_carrying_an_admitted_name": pending_hits,
            "a_plant_in_a_copy_of_the_pending_receipts_was_caught": planted_caught,
        },
        "scope_note": (
            "the pending VERDICTS document does not exist when B3 is scored — "
            "it carries B3's own row — so the pending document swept here is "
            "the receipts. The verdicts document is swept by B5 itself before "
            "it is written, and re-swept from the COMMITTED bytes by "
            "scripts/check_house_rules_receipts.py, which is the falsifiable "
            "side of that half"
        ),
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

    # F4's detector, and the one that would have caught the leak the H-P1
    # review found. `serve_chat.LINE_GRAMMAR`'s `declare` row shipped
    # hr-fx-s1-t01's ADMITTED fixture symbol as its example, from H-P0 through
    # H-P1's FIRST registered run. (The name is not repeated here: this file
    # is inside the tree the sweep covers, and writing it would put it back.)
    # That is b3-m08's vector verbatim — an admitted name inside a committed
    # generated artifact — sitting in the tree while B3 scored b3-m08 STOPPED
    # on a detector that never looked at a grammar row. So the grammar's own
    # example strings, and the generated artifact that echoes them, are swept
    # here on every run.
    from serve_chat import LINE_GRAMMAR  # noqa: PLC0415

    grammar_texts = {
        f"serve_chat.LINE_GRAMMAR[{index}]": json.dumps(
            row, sort_keys=True, default=list, ensure_ascii=False
        )
        for index, row in enumerate(LINE_GRAMMAR)
    }
    echo = json.loads((REPO / COMMAND_BOUND).read_text(encoding="utf-8"))
    for index, row in enumerate(echo.get("classes", [])):
        grammar_texts[f"{COMMAND_BOUND}#classes[{index}]"] = json.dumps(
            row, sort_keys=True, ensure_ascii=False
        )
    grammar_hits = sorted(
        key
        for key, text in grammar_texts.items()
        if any(name.casefold() in text.casefold() for name in admitted_names)
    )
    grammar_planted_caught = all(
        any(
            name.casefold() in (text + admitted_names[0]).casefold()
            for name in admitted_names
        )
        for text in grammar_texts.values()
    )
    out["grammar_example_names"] = {
        "fires": not grammar_hits and grammar_planted_caught,
        "kind": (
            "the vector itself, live over the committed tree: the served "
            "grammar rows and the generated artifact that echoes them, swept "
            "for admitted fixture symbol names, with a planted control on an "
            "in-memory copy of each row"
        ),
        "observed": {
            "grammar_rows_swept": len(LINE_GRAMMAR),
            "generated_echo_rows_swept": len(echo.get("classes", [])),
            "rows_carrying_an_admitted_name": len(grammar_hits),
            "rows_carrying_an_admitted_name_keyed": grammar_hits,
            "a_plant_in_every_row_copy_was_caught": grammar_planted_caught,
        },
        "sources_swept": [SERVE_CHAT + " LINE_GRAMMAR", COMMAND_BOUND],
        "found_by_review_note": (
            "run 1 scored b3-m08 STOPPED while this vector was present in the "
            "committed tree; the H-P1 adversarial review found it, not the "
            "run. This detector is what sees it, and the run-1 record is "
            "reported rather than glossed because it is what makes the repair "
            "checkable"
        ),
    }

    # b3-m29's sealed mechanism names the SCHEMA DIGEST COMPARISON first —
    # "the schema's sha256_lf is a sealed field of this artifact and of every
    # AdmissibilityVerdict, so the digest comparison fails" — and run 1 mapped
    # it to the working-tree digest, which is only the second half of that
    # sentence. This exercises the first half: the digest a verdict carries is
    # the live schema's and the prereg's pin, and a verdict built over a
    # tampered digest is visibly not the committed schema's.
    from dataclasses import replace as dc_replace  # noqa: PLC0415

    live_schema_digest = sha256_lf(REPO / SCHEMA)
    pinned = {row["path"]: row["sha256_lf"] for row in _prereg_frozen()}
    agrees = (
        decision.verdict.schema_digest
        == live_schema_digest
        == inputs.schema_sha256_lf
        == pinned.get(SCHEMA)
    )
    tampered_decision = SL.decide(
        "probe_of/2 (variable, variable)",
        dc_replace(inputs, schema_sha256_lf="0" * 64),
        session_id="b3",
        turn_index=1,
    )
    detects = tampered_decision.verdict.schema_digest != live_schema_digest
    out["schema_digest_comparison"] = {
        "fires": agrees and detects,
        "kind": "a live comparison, both directions",
        "observed": {
            "verdict_digest_equals_the_live_schema_and_the_prereg_pin": agrees,
            "a_tampered_digest_is_visible_in_the_verdict": detects,
        },
    }
    return out


#: THE MECHANISM CLASS EACH DETECTOR BELONGS TO, and the lowercase phrases
#: that identify that class inside a mutant's SEALED `stopper_mechanism`
#: sentence. Both halves are AUTHORED HERE and both are published in the run
#: artifact, because the H-P1 review's first finding was that an authored
#: id-to-detector map was never checked against the seal at all: b3-m29's seal
#: names a schema-digest comparison and the map pointed it at the working-tree
#: digest; b3-m07's names B5's receipt sweep and the map pointed it at a
#: temporary-directory probe.
#:
#: WHAT THIS CHECK CAN AND CANNOT ESTABLISH, stated before its result is read.
#: It can establish that the detector a mutant is mapped to belongs to a
#: mechanism class the mutant's own seal NAMES. It cannot establish that the
#: detector reproduces the mutant: the 32 mutants are PROSE DESCRIPTIONS of
#: attempts, nothing here executes one, and a keyword match over a sentence is
#: a coarse instrument by construction. It is published so the coarseness is
#: inspectable rather than asserted, and a mismatch is REPORTED BY ID rather
#: than folded into a pass.
MECHANISM_CLASS_KEYWORDS: dict[str, tuple[str, ...]] = {
    "name_sweep_over_written_bytes": (
        "name sweep",
        "sweep",
        "finds the name",
        "found string",
    ),
    "codec_type_registry": (
        "session_state.encode",
        "encode",
        "_types",
        "codec",
        "sessionformaterror",
    ),
    "working_tree_digest": (
        "working_tree_digest",
        "durable_digest",
        "tree digest",
        "both digests",
        "digest moves",
        "digest comparison",
        "digest difference",
        "b4",
    ),
    "record_shape": (
        "record shape",
        "symbol-name field",
        "cannot represent",
        "no row can be built",
        "framespec",
        "literals",
        "provenance rows",
    ),
    "graph_id_resolution": (
        "node id",
        "merged graph",
        "resolves to nothing",
        "corpus nodes",
    ),
    "supposition_status": ("still a supposition", "evidence status"),
    "pin_chain": ("pinchainerror", "resolve_pin", "prereg_pins"),
    "census_regeneration": (
        "recomputes",
        "recomputation",
        "regeneration",
        "census drift",
        "re-derives",
    ),
    "fresh_session": ("fresh session", "replay_session", "ledger is empty"),
    "schema_digest_pin": ("sha256_lf", "schema's sha256"),
}

#: Which class each shipped detector belongs to. Two detectors share
#: `name_sweep_over_written_bytes` because they are the same mechanism pointed
#: at two bodies of bytes.
DETECTOR_MECHANISM_CLASS: dict[str, str] = {
    "encode_type_registry": "codec_type_registry",
    "name_sweep": "name_sweep_over_written_bytes",
    "grammar_example_names": "name_sweep_over_written_bytes",
    "working_tree_digest": "working_tree_digest",
    "record_shape_has_no_symbol_slot": "record_shape",
    "id_resolution_against_the_merged_graph": "graph_id_resolution",
    "a_checked_use_is_still_a_supposition": "supposition_status",
    "prereg_pin_chain": "pin_chain",
    "census_regeneration": "census_regeneration",
    "fresh_session_has_no_ledger_entry": "fresh_session",
    "schema_digest_comparison": "schema_digest_pin",
}

#: The three mutants whose detector MOVED between run 1 and run 2, and why.
#: Published so the map's change is a disclosed decision rather than a silent
#: difference between two artifacts a reader might compare.
B3_REPOINTED_SINCE_RUN_1: dict[str, str] = {
    "b3-m08": (
        "was `working_tree_digest`, now `grammar_example_names`. Its seal "
        "names a committed GENERATED ARTIFACT carrying the name, and the "
        "digest detector cannot see a name that is already committed — which "
        "is exactly how the served grammar example carried an admitted symbol "
        "through run 1 while this mutant scored STOPPED"
    ),
    "b3-m24": (
        "was `checker_inputs_exclude_the_runs_outputs`, now `name_sweep`. The "
        "retired detector could not fail; the sealed sentence's own first "
        "clause — 'B4 excludes those paths from the DIGEST, not from B5's "
        "name sweep' — is what `name_sweep` now runs against the run's real "
        "pending output"
    ),
    "b3-m29": (
        "was `working_tree_digest`, now `schema_digest_comparison`. Its seal "
        "names the schema sha256 comparison FIRST and the tree digest second; "
        "run 1 mapped it to the second half only"
    ),
}

#: Detectors the H-P1 review retired, kept by name so the artifact can say
#: which mutants moved and why rather than showing a map that silently
#: changed shape between two runs.
RETIRED_DETECTORS: dict[str, str] = {
    "checker_inputs_exclude_the_runs_outputs": (
        "RETIRED at H-P1-FIX. It asserted that scripts/symbol_ledger.py holds "
        "no string constant equal to either declared output path — true of "
        "every module that never mentions them, and so a check that could not "
        "fail. Its one mutant, b3-m24, is re-pointed at `name_sweep`, which "
        "now sweeps the run's real pending output for admitted names and is "
        "the half of b3-m24's own sealed sentence that can go red: 'B4 "
        "excludes those paths from the DIGEST, not from B5's name sweep'"
    ),
}


def sealed_mechanism_classes(mechanism: str) -> list[str]:
    """Every class whose keywords occur in a sealed stopper sentence."""

    folded = (mechanism or "").casefold()
    return sorted(
        name
        for name, keywords in MECHANISM_CLASS_KEYWORDS.items()
        if any(keyword in folded for keyword in keywords)
    )


B3_DETECTORS = {
    "b3-m01": "id_resolution_against_the_merged_graph",
    "b3-m02": "a_checked_use_is_still_a_supposition",
    "b3-m03": "id_resolution_against_the_merged_graph",
    "b3-m04": "record_shape_has_no_symbol_slot",
    "b3-m05": "name_sweep",
    "b3-m06": "record_shape_has_no_symbol_slot",
    "b3-m07": "name_sweep",
    "b3-m08": "grammar_example_names",
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
    "b3-m24": "name_sweep",
    "b3-m25": "working_tree_digest",
    "b3-m26": "census_regeneration",
    "b3-m27": "working_tree_digest",
    "b3-m28": "working_tree_digest",
    "b3-m29": "schema_digest_comparison",
    "b3-m30": "working_tree_digest",
    "b3-m31": "census_regeneration",
    "b3-m32": "working_tree_digest",
}


def score_b3(prereg: dict, document: dict, detectors: dict) -> dict:
    """Score the sealed mutant set against the LIVE detectors mapped to it.

    Read the three disclosure fields at the top of the returned row before any
    number below them. Nothing here executes a mutant; the mutants are prose,
    the map from mutant id to detector is authored in this file, and what the
    run establishes is that each mapped detector FIRES on live material this
    run touched. The class check added at H-P1-FIX is the third leg: it asks,
    mechanically, whether the detector a mutant is mapped to belongs to a
    mechanism class the mutant's own seal names, and reports every id where it
    does not.
    """

    misses: list[str] = []
    rows = []
    uncovered: list[str] = []
    class_mismatches: list[str] = []
    coverage: dict[str, int] = {}
    for mutant in document["b3_containment"]["mutants"]:
        name = B3_DETECTORS.get(mutant["mutant_id"])
        detector = detectors.get(name)
        mechanism = mutant.get("stopper_mechanism") or ""
        classes = sealed_mechanism_classes(mechanism)
        detector_class = DETECTOR_MECHANISM_CLASS.get(name)
        class_named_in_the_seal = bool(detector_class) and detector_class in classes
        if detector is None:
            uncovered.append(mutant["mutant_id"])
            outcome = "NOT COVERED BY A LIVE DETECTOR"
        elif detector["fires"]:
            outcome = "STOPPED"
        else:
            outcome = "SURVIVED"
            misses.append(
                f"{mutant['mutant_id']} survived: detector {name!r} did not fire"
            )
        if detector is not None:
            coverage[name] = coverage.get(name, 0) + 1
        if not class_named_in_the_seal:
            class_mismatches.append(mutant["mutant_id"])
        rows.append(
            {
                "mutant_id": mutant["mutant_id"],
                "vector": mutant["vector"],
                "outcome": outcome,
                "stopped_by": name,
                "sealed_stopper_mechanism": mechanism,
                "detector_mechanism_class": detector_class,
                "mechanism_classes_named_in_the_seal": classes,
                "detector_class_is_named_in_the_seal": class_named_in_the_seal,
            }
        )
    floor = prereg["frozen_numbers"]["b3_mutant_floor"]
    stopped = sum(1 for row in rows if row["outcome"] == "STOPPED")
    if stopped < floor:
        misses.append(
            f"{stopped} mutant(s) stopped by a live detector, floor {floor}"
        )
    sealed_ids = {mutant["mutant_id"] for mutant in document["b3_containment"]["mutants"]}
    unmapped = sorted(sealed_ids - set(B3_DETECTORS))
    invented = sorted(set(B3_DETECTORS) - sealed_ids)
    if unmapped:
        misses.append(f"sealed mutants with no detector mapped: {unmapped}")
    if invented:
        misses.append(f"detector map carries ids absent from the seal: {invented}")
    # A mutant explicitly mapped to nothing is reported as uncovered above,
    # not as an unexercised detector; only a NAMED detector that the run never
    # exercised is a defect in the runner.
    unexercised = sorted(
        name
        for name in set(B3_DETECTORS.values())
        if name is not None and name not in detectors
    )
    if unexercised:
        misses.append(f"detectors mapped but never exercised: {unexercised}")
    return {
        "verdict": _verdict(misses),
        "clause": prereg["gates"]["B3"],
        # ---- read these three first -------------------------------------
        "mutants_are_descriptions_not_executions": True,
        "mutants_are_descriptions_not_executions_note": (
            "THE 32 MUTANTS ARE PROSE DESCRIPTIONS SEALED AT H-PRE AND NO "
            "MUTANT IS EXECUTED BY THIS RUN OR BY ANY OTHER PROGRAM IN THIS "
            "REPOSITORY. What the run establishes is narrower and is the whole "
            "of what B3's numbers mean: for each sealed mutant, the detector "
            "the runner maps it to was exercised on live material during this "
            "run and fired. The word 'stopped' in the rows below is that "
            "observation and nothing more — no attempt was made and none was "
            "repelled. A successor that wants containment MEASURED needs "
            "executable mutants, which is the standing item this run leaves "
            "behind."
        ),
        "detector_map_is_authored": True,
        "detector_map_is_authored_note": (
            "the sealed corpus names each mutant's stopper in PROSE "
            "(`stopper_mechanism`), never as a machine-readable detector id, "
            "so the id-to-detector association is AUTHORED in "
            f"{THIS}:B3_DETECTORS. It is committed before the run and required "
            "to cover the sealed mutant set exactly in both directions, and "
            "every row below carries the sealed sentence beside the detector "
            "that was mapped to it so the association can be read rather than "
            "taken."
        ),
        "detector_class_check": {
            "what_it_establishes": (
                "that the detector a mutant is mapped to belongs to a "
                "MECHANISM CLASS the mutant's own sealed sentence names, "
                "matched by the published keyword table"
            ),
            "what_it_does_not_establish": (
                "that the detector reproduces the mutant. A keyword match over "
                "a sentence is coarse by construction, and several sealed "
                "sentences name two or three classes at once — every one they "
                "name is listed per row"
            ),
            "keyword_table": {
                name: list(keywords)
                for name, keywords in sorted(MECHANISM_CLASS_KEYWORDS.items())
            },
            "detector_classes": dict(sorted(DETECTOR_MECHANISM_CLASS.items())),
            "mutants_whose_detector_class_is_not_named_in_the_seal": class_mismatches,
            "mismatches_are_reported_not_scored": True,
            "mismatches_are_reported_not_scored_note": (
                "a mismatch does not fail B3 here: the check is new, the "
                "instrument is coarse, and turning a coarse instrument into a "
                "gate after a score would be exactly the move this "
                "registration forbids. It is published by id so a reader can "
                "judge each one"
            ),
        },
        # ---- the numbers -------------------------------------------------
        "mutants": f"{stopped}/{len(rows)} stopped by a live detector",
        "floor": floor,
        "survivors": [r["mutant_id"] for r in rows if r["outcome"] == "SURVIVED"],
        "not_covered_by_a_live_detector": uncovered,
        "detector_coverage_counts": dict(sorted(coverage.items())),
        "detector_coverage_counts_note": (
            "published so no prose number can drift: run 1's own report said "
            "`working_tree_digest` covered 15 of 32 mutants and the map "
            "carried 10. The counts are computed from the map that scored "
            "this run"
        ),
        "detectors_exercised": {name: detectors[name] for name in sorted(detectors)},
        "detectors_retired_at_this_stage": dict(sorted(RETIRED_DETECTORS.items())),
        "mutants_repointed_since_run_1": dict(sorted(B3_REPOINTED_SINCE_RUN_1.items())),
        "detector_map": f"{THIS}:B3_DETECTORS",
        "detector_map_covers_the_seal_exactly": not unmapped and not invented,
        "how_stopping_was_established": (
            "each mutant is associated with a SHIPPED detector by the authored "
            "map, the detector is exercised on live material in this run — the "
            "real repository tree, the bytes this run is about to write, the "
            "committed census and schema, a live session — and a detector that "
            "did not fire fails every mutant mapped to it. No test assertion "
            "reads a mutant's name out of an output, which is what the clause "
            "forbids; and no mutant is executed, which is what the clause "
            "never provided for"
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

    # F8's repair. The fence arm below compares a session carrying a symbol
    # ledger against a session carrying none. Run 1 ran only the arm where the
    # attached ledger was EMPTY — and `SymbolLedger.check_use` returns None
    # whenever `_by_name` is empty, so the two code paths provably agree and
    # the comparison could not fail. The empty arm is kept and labelled as the
    # trivial one; the arm that can fail is the POPULATED one, where the
    # session has actually admitted symbols and the undeclared applied atom
    # still has to come back untouched.
    #
    # Only the SYMBOL ledger is populated: `SymbolLedger.declare` mutates
    # nothing but itself, so the assumption ledger stays empty in both arms
    # and the one variable that moves is the one the fence is about.
    admitting_lines = [
        _rest(row["line"])
        for row in document["fixtures"]
        if row["kind"] == "declaration"
        and row["expected_verdict"] == SL.VERDICT_ADMITTED
    ]
    populated_rows = []
    populated_admitted = 0
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

        populated = _live_session("b6-fence-populated", inputs)
        for line in admitting_lines:
            if len(populated.symbols.admitted_names()) >= populated.symbols.cap:
                break
            populated.symbols.declare(line, len(populated.symbols.verdicts()) + 1)
        populated_admitted = len(populated.symbols.admitted_names())
        populated.assumptions.barrier.open_turn(1)
        populated_verdict = harness.route_line(REPO, populated, row["line"])
        populated.assumptions.barrier.close_turn()
        populated_identical = populated_verdict == right
        if not populated_identical:
            misses.append(
                f"{row['fixture_id']}: the regression fence moved with a "
                f"POPULATED symbol ledger"
            )
        populated_rows.append(
            {
                "fixture_id": row["fixture_id"],
                "byte_identical_to_the_pre_slice_path": populated_identical,
            }
        )
    if not populated_admitted:
        misses.append(
            "the populated fence arm admitted no symbol, so it is the empty "
            "arm again"
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
        "undeclared_atoms_fenced_populated_arm": (
            f"{sum(1 for r in populated_rows if r['byte_identical_to_the_pre_slice_path'])}/"
            f"{len(populated_rows)}"
        ),
        "symbols_admitted_in_the_populated_arm": populated_admitted,
        "how_the_fence_was_checked": (
            "the same line routed twice — once through a session with a symbol "
            "ledger attached and once through a session with none, which IS "
            "the pre-slice code path because the new block is guarded on that "
            "field — and the two verdict dicts compared for equality. TWO ARMS "
            "since H-P1-FIX: the EMPTY-LEDGER arm and the POPULATED one"
        ),
        "empty_ledger_arm_is_the_trivial_one": True,
        "empty_ledger_arm_note": (
            "`SymbolLedger.check_use` returns None whenever its name table is "
            "empty, so with an EMPTY ledger attached the two code paths are "
            "provably the same path and the comparison cannot fail. Run 1 ran "
            "only that arm. It is kept because it is the exact statement of "
            "the guard, and it is labelled trivial rather than counted as "
            "evidence"
        ),
        "populated_arm_note": (
            "the arm that can fail: the session has actually admitted symbols "
            "before the fence turn, so `check_use` runs its lookup on a "
            "non-empty table and an undeclared applied atom must still come "
            "back untouched. Only the SYMBOL ledger differs between the two "
            "sides — declaring mutates nothing else — so the assumption "
            "ledger is empty in both and the fence tests one variable"
        ),
        "refusal_rows": mismatch_rows,
        "fence_rows": fence_rows,
        "populated_fence_rows": populated_rows,
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
        # F14's repair. Run 1 compared the head the use line resolves to
        # against the SEAL's `expected_resolved_key` — seal to seal, with the
        # live ledger key never entering the comparison, which is the check
        # B12's own docstring says the pairs arm exists to avoid. The live key
        # is `decision.declaration.symbol_name`: what the checker admitted for
        # this mutant, this run. The seal comparison is kept beside it as a
        # separate reported field rather than dropped.
        resolved = True
        seal_agrees = True
        live_key = (
            decision.declaration.symbol_name
            if decision.admitted and decision.declaration is not None
            else None
        )
        if mutant["expected_resolved_key"]:
            head = SL.applied_head(_rest(mutant["use_line"]))
            resolved = bool(head) and live_key is not None and head[0] == live_key
            seal_agrees = live_key == mutant["expected_resolved_key"]
            if not seal_agrees:
                misses.append(
                    f"{mutant['mutant_id']}: the LIVE ledger key is not the "
                    f"key the seal expected"
                )
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
                "live_ledger_key_matches_the_seal": seal_agrees,
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
        "mutant_arm_compares_against_the_live_key": True,
        "mutant_arm_note": (
            "the mutant arm resolves each use line against the key THIS RUN "
            "admitted for that mutant — `decision.declaration.symbol_name` — "
            "exactly as the pairs arm does. Run 1 compared the resolved head "
            "against the seal's own `expected_resolved_key`, which is seal to "
            "seal and could not see a checker that admitted something else. "
            "Agreement between the live key and the seal is reported "
            "separately as `live_ledger_key_matches_the_seal`"
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


#: F3's richer surface family, declared here and in the prereg amendment
#: `amd-2026-09-02-b9-families` before it is fitted. Features are the same
#: three the prereg ALLOWS; what changes is the shape of the rules over them:
#: closed intervals on one feature, and conjunctions of two such intervals on
#: two DIFFERENT features. The registered family — three comparison operators
#: over single thresholds — is a strict subset of this one in expressive power
#: and is what the prereg names, so it and it alone decides the gate.
RICHER_FAMILY_FEATURES = ("has_command_word", "line_length", "token_count")

#: The pre-declared, deterministic tie-break for the richer family: highest
#: FIT-HALF accuracy, then the NARROWEST rule (the summed width of its
#: intervals), then the lexicographically smallest rule id. Declared before
#: the fit so no tie is resolved by looking at the scored half — which is the
#: exact failure the review named when it observed that `44 <= line_length <=
#: 57` ties on the fit half at 0.700 and reaches 0.789474 out of half.
RICHER_FAMILY_TIE_BREAK = (
    "highest fit-half accuracy; then the narrowest rule, measured as the sum "
    "of (hi - lo) over its interval clauses; then the lexicographically "
    "smallest rule id. Declared before the fit, in the runner and in the "
    "prereg amendment, so a fit-half tie is never resolved by a scored-half "
    "number"
)


def _interval_family(values: dict[str, list[int]]) -> list[tuple[str, int, tuple]]:
    """Every one- and two-feature closed-interval rule, with its width.

    Returns ``(rule_id, width, clauses)`` triples, sorted by rule id, where a
    clause is ``(feature, lo, hi)`` and a row predicts ADMITTED exactly when
    every clause holds.
    """

    singles: dict[str, list[tuple[str, int, tuple]]] = {}
    for feature in RICHER_FAMILY_FEATURES:
        rows = []
        seen = sorted(values[feature])
        for i, lo in enumerate(seen):
            for hi in seen[i:]:
                rows.append(
                    (f"{feature}:in:{lo}..{hi}", hi - lo, ((feature, lo, hi),))
                )
        singles[feature] = rows
    family: list[tuple[str, int, tuple]] = []
    for rows in singles.values():
        family.extend(rows)
    names = list(RICHER_FAMILY_FEATURES)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            for lid, lwidth, lclauses in singles[left]:
                for rid, rwidth, rclauses in singles[right]:
                    family.append(
                        (f"{lid}&{rid}", lwidth + rwidth, lclauses + rclauses)
                    )
    family.sort(key=lambda row: row[0])
    return family


def score_b9(prereg: dict, document: dict, replay: Replay) -> dict:
    """A surface-only admitter, fitted on the fit half and scored on the other.

    THE GATE IS THE REGISTERED FAMILY AND ONLY THE REGISTERED FAMILY: every
    threshold rule over the three allowed features plus the two constant
    predictors, enumerated and scored on the fit half, best carried to the
    scored half, ties broken on the lexicographically smallest rule id. That
    is what the prereg names, and moving the gate to a family invented after
    run 1's score would be choosing the control after seeing the result.

    THREE DISCLOSURES THE H-P1 REVIEW REQUIRED, all reported and none of them
    scoring:

    1. `family_ceiling_on_scored_half` — the best any member of the REGISTERED
       family achieves on the scored half. Run 1 reported an agreement of
       0.684211 against a 0.784211 threshold without saying that the family's
       own ceiling is below the threshold, which means no member could have
       fired and the control was structurally unable to void anything.
    2. `fitted_rule_degenerates_on_scored_half` — the fitted rule predicted
       one class for every scored row, which is why its agreement equalled the
       majority rate exactly. A degenerate rule is a majority-class predictor
       wearing a feature's name.
    3. the RICHER family above: fitted on the fit half with a pre-declared
       tie-break, scored out of half, and reported whatever it says —
       including if it exceeds the threshold. Its ceiling on the scored half
       is reported too and is labelled for what it is: selection on the scored
       half, not a legitimate control score.
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

    # ---- disclosure 1: the registered family's own ceiling on the scored
    # half. If it is at or below the threshold, no member of the family the
    # prereg registers could have fired, whatever the fit half chose.
    # Same tie-break both families use for their fit: highest score, then the
    # lexicographically SMALLEST rule id. Written the same way in both places
    # so the two ceilings are comparable and neither is an accident of `max`.
    family_ceiling = max(
        round(accuracy(rule, scored_ids), 6) for _rid, rule in candidates
    )
    ceiling_id = min(
        rid
        for rid, rule in candidates
        if round(accuracy(rule, scored_ids), 6) == family_ceiling
    )

    # ---- disclosure 2: does the fitted rule predict one class on the scored
    # half? A rule that does is a majority-class predictor with a feature's
    # name on it, and its agreement equals the majority rate by arithmetic.
    scored_predictions: dict[str, int] = {}
    for fixture_id in scored_ids:
        prediction = predict(best_rule, by_id[fixture_id]["line"])
        scored_predictions[prediction] = scored_predictions.get(prediction, 0) + 1
    degenerate = len(scored_predictions) == 1

    # ---- disclosure 3: the richer family, fitted on the FIT HALF ONLY with
    # the tie-break declared above before any of it was run.
    fit_values = {
        feature: sorted(
            {_surface_features(by_id[f]["line"])[feature] for f in fit_ids}
        )
        for feature in RICHER_FAMILY_FEATURES
    }
    family = _interval_family(fit_values)

    def interval_predict(clauses, line: str) -> str:
        features = _surface_features(line)
        hit = all(lo <= features[name] <= hi for name, lo, hi in clauses)
        return SL.VERDICT_ADMITTED if hit else SL.VERDICT_REFUSED

    def interval_accuracy(clauses, ids) -> float:
        correct = sum(
            1 for f in ids if interval_predict(clauses, by_id[f]["line"]) == truth[f]
        )
        return correct / len(ids)

    richer_fit = [
        (round(interval_accuracy(clauses, fit_ids), 6), width, rid, clauses)
        for rid, width, clauses in family
    ]
    best_fit_accuracy = max(row[0] for row in richer_fit)
    tied = [row for row in richer_fit if row[0] == best_fit_accuracy]
    chosen = min(tied, key=lambda row: (row[1], row[2]))
    richer_agreement = round(interval_accuracy(chosen[3], scored_ids), 6)
    richer_fired = richer_agreement > threshold
    richer_ceiling_rows = [
        (round(interval_accuracy(clauses, scored_ids), 6), rid)
        for rid, _width, clauses in family
    ]
    richer_ceiling = max(row[0] for row in richer_ceiling_rows)
    richer_ceiling_id = min(
        rid for score, rid in richer_ceiling_rows if score == richer_ceiling
    )

    # ---- F5's arithmetic: the pre-run re-anchoring did not rescue B9. The
    # superseded threshold is read from the sealed corpus's own amendments
    # block, never restated here.
    superseded = None
    for amendment in document.get("amendments") or ():
        if amendment.get("superseded_b9"):
            superseded = amendment["superseded_b9"]
    superseded_threshold = (superseded or {}).get("void_threshold")

    misses: list[str] = []
    if fired:
        misses.append(
            "the voiding sentence fired: the surface-only admitter's out-of-half "
            f"agreement {agreement:.6f} exceeds the threshold {threshold}"
        )
    return {
        "family_ceiling_on_scored_half": family_ceiling,
        "family_ceiling_rule": ceiling_id,
        "no_member_of_the_registered_family_could_have_fired": (
            family_ceiling <= threshold
        ),
        "family_ceiling_sentence": (
            "The best agreement ANY member of the registered family reaches on "
            f"the scored half is {family_ceiling:.6f}, against a void threshold "
            f"of {threshold}. "
            + (
                "No member of the family the prereg registers could have fired "
                "the voiding sentence on this corpus, whatever the fit half "
                "selected. The control as registered was structurally unable "
                "to void the capability, and that is a fact about the family "
                "and the 19-row scored half, not a result about the checker."
                if family_ceiling <= threshold
                else "At least one member could have fired, so the family was "
                "not structurally inert on this corpus."
            )
        ),
        "fitted_rule_degenerates_on_scored_half": degenerate,
        "fitted_rule_scored_half_predictions": dict(sorted(scored_predictions.items())),
        "fitted_rule_degeneracy_note": (
            "the fitted rule's predictions on the scored half, counted. One "
            "class for every row means the rule is a majority-class predictor "
            "with a feature's name on it, and its agreement equals the "
            "majority-class rate by arithmetic rather than by any signal the "
            "surface carries. Run 1 reported the equality without reporting "
            "the reason for it"
        ),
        "superseded_anchor_arm": {
            "superseded_void_threshold": superseded_threshold,
            "would_have_fired_under_the_superseded_threshold": (
                None if superseded_threshold is None else agreement > superseded_threshold
            ),
            "note": (
                "the corpus was re-anchored PRE-RUN by the sealed corpus's own "
                "amendment 1 (38 -> 39 declarations). Reported so the "
                "re-anchoring can be seen not to have rescued the control: the "
                "fitted rule is unfired against the superseded threshold as "
                "well as against the registered one"
            ),
        },
        "richer_family": {
            "is_the_gate": False,
            "why_not_the_gate": (
                "the prereg registers the threshold family and the gate is "
                "what the prereg names. This family was authored on "
                "2026-09-02, AFTER run 1's score, in response to the H-P1 "
                "review; scoring the capability against a control chosen after "
                "a result is the move the registration exists to prevent. It "
                "is reported in full, including if it exceeds the threshold"
            ),
            "shape": (
                "closed intervals lo <= feature <= hi on one of the three "
                "allowed features, and conjunctions of two such intervals on "
                "two DIFFERENT features"
            ),
            "features": list(RICHER_FAMILY_FEATURES),
            "size": len(family),
            "values_enumerated_over": "the FIT half only",
            "tie_break": RICHER_FAMILY_TIE_BREAK,
            "fit_half_selected": {
                "rule": chosen[2],
                "width": chosen[1],
                "fit_half_accuracy": chosen[0],
                "out_of_half_agreement": richer_agreement,
                "exceeds_the_void_threshold": richer_fired,
                "rules_tied_on_the_fit_half": len(tied),
                "selected_rule_is_a_point_interval": chosen[1] == 0,
                "tie_break_finding": (
                    "REPORTED AGAINST THE TIE-BREAK'S OWN AUTHOR: 'narrowest "
                    "first' resolves a large fit-half tie toward a ZERO-WIDTH "
                    "interval, which is a single-value equality test and "
                    "therefore the same degenerate shape the registered "
                    "family's fitted rule already had. The tie-break was "
                    "declared before the fit and is not changed after it. What "
                    "the finding says is that a successor's family needs a "
                    "tie-break that prefers a rule which SPLITS the half — "
                    "widest non-degenerate, or a complexity penalty — and a "
                    "held-out half larger than nineteen rows for either to "
                    "mean anything"
                ),
            },
            "ceiling_on_scored_half": {
                "agreement": richer_ceiling,
                "rule": richer_ceiling_id,
                "this_is_selection_on_the_scored_half": True,
                "note": (
                    "the maximum over the whole richer family evaluated ON THE "
                    "SCORED HALF. It is NOT a control score and may not be "
                    "read as one: choosing a rule by the half it is scored on "
                    "is the leak a held-out half exists to prevent. It is "
                    "published because it bounds what any surface-only "
                    "admitter of this shape could reach on this corpus, and "
                    "that bound is what a successor needs"
                ),
            },
        },
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


#: F6's replacement for a prose gloss the H-P1 review falsified. Every path
#: the whole-repository disclosure reports is classified by this rule and the
#: rule is published beside the result, because the alternative — naming which
#: admitted symbol each path carries — would put admitted names inside a
#: declared output and make B5 red by the act of disclosing.
DISCLOSURE_CLASSIFICATION_RULE = (
    "applied in order, first match wins: (1) the path IS the sealed corpus -> "
    "sealed_corpus; (2) the path IS the corpus builder -> corpus_builder; (3) "
    "the path IS the checker module -> checker_module; (4) the path IS "
    "scripts/serve_chat.py -> grammar_example; (5) the path IS the generated "
    "command-bound artifact -> generated_from_grammar; (6) the path is under "
    "tests/ AND its name contains 'symbol_ledger' or 'house_rules' -> "
    "h_p0_tests; (7) the commit that ADDED the path is an ancestor of, or is, "
    "the sealed H-PRE commit -> pre_existing_unrelated_use_of_a_common_word, "
    "which is to say the file was in the tree before this slice's corpus was "
    "sealed and uses the name as its own word; (8) anything else -> "
    "added_after_the_seal_and_unclassified, which is a finding and not a "
    "category"
)


def _classify_disclosure_path(relative: str, sealed_commit: str) -> str:
    """The mechanical rule DISCLOSURE_CLASSIFICATION_RULE states, run."""

    if relative == FIXTURES:
        return "sealed_corpus"
    if relative == "scripts/build_house_rules_fixtures.py":
        return "corpus_builder"
    if relative == LEDGER_MODULE:
        return "checker_module"
    if relative == SERVE_CHAT:
        return "grammar_example"
    if relative == COMMAND_BOUND:
        return "generated_from_grammar"
    if relative.startswith("tests/") and (
        "symbol_ledger" in relative or "house_rules" in relative
    ):
        return "h_p0_tests"
    added = _first_commit(relative)
    if added and (added == sealed_commit or _is_ancestor(added, sealed_commit)):
        return "pre_existing_unrelated_use_of_a_common_word"
    return "added_after_the_seal_and_unclassified"


def _classification_counts(paths: list[str], sealed_commit: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in paths:
        name = _classify_disclosure_path(path, sealed_commit)
        counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))


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
    sealed_commit = prereg["sealed_commit"]

    # THE RUN'S OUTPUT TREE, and only that. Swept over the whole repository
    # the sweep finds a set of PRE-EXISTING committed files. Run 1's comment
    # here called them "the sealed corpus that names the fixtures, its
    # builder, and the H-P0 tests" and the H-P1 review falsified that gloss:
    # at least ten of the twenty-one were none of those three — a corpus data
    # file, an old roadmap, a seeding script, gate logs, and four tests
    # belonging to other slices, all of them carrying an admitted fixture name
    # as an ordinary English word they used first. So the gloss is replaced by
    # a MECHANICAL CLASSIFICATION published beside the path list
    # (`_classify_disclosure_path`), and no sentence here summarises the set
    # any more.
    #
    # What has not changed is the scoping argument: none of them is a document
    # this run wrote, and a gate about what a run persists cannot be scored
    # against files that predate it. So the sweep covers exactly what the run
    # produced: the two declared outputs, plus every path B4 observed
    # appearing or changing while the run executed, plus the directories a
    # session write would land in, checked for new files.
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
            "committed files are outside it, because a gate about what a run "
            "persists cannot be scored against files that predate it; their "
            "count, their paths and a mechanical classification of each are "
            "disclosed below, and no prose here characterises them"
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
            "path_classification": {
                path: _classify_disclosure_path(path, sealed_commit)
                for path in repo_hits
            },
            "classification_counts": _classification_counts(repo_hits, sealed_commit),
            "classification_rule": DISCLOSURE_CLASSIFICATION_RULE,
            "why_the_names_are_not_published_per_path": (
                "the honest table would say WHICH admitted name each path "
                "carries, and this artifact is inside the swept tree: writing "
                "that table would put admitted names in a declared output and "
                "make B5 red by the act of disclosing. The classification is "
                "what can be published without echoing a name"
            ),
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


#: F7's scope note, stated rather than left to be inferred. The second
#: program (`check_house_rules_receipts.py`) re-derives these from committed
#: bytes; anything not on this list is scored ONCE, by this runner, and a
#: reader should weigh it accordingly.
SECOND_PROGRAM_COVERS = (
    "B5 — the admitted-name set re-derived from the seal and both committed "
    "outputs re-swept, plus the whole-repository disclosure recomputed by a "
    "separate implementation of the sweep",
    "B9 — the halves re-derived from the sealed fixture order, the anchor "
    "recomputed from the receipts, the threshold recomputed as anchor plus "
    "margin, the reported fitted rule re-evaluated on the committed lines, "
    "the firing recomputed as a strict exceedance, and the REGISTERED "
    "family's size, its ceiling on the scored half and the fitted rule's "
    "per-row predictions re-enumerated by a second implementation",
    "B10 — the ancestry re-run strictly, its proof sentence reconstructed, and "
    "every prereg `frozen` pin re-digested",
    "B12 — the sealed round-trip pair count re-derived from the corpus and "
    "compared against the reported denominator and the prereg's frozen number",
    "B8 — the prereg's named target fixtures re-derived from the corpus as "
    "every admitted declaration citing the removed category",
    "the clause order — every receipt's deciding clause re-checked against the "
    "sealed clause_order, and the multi-ground fixtures re-derived",
    "the verdict table's internal consistency, the result gates, the receipt "
    "set, provenance digests and the absence of a wall clock",
    "byte-for-byte determinism, through --replay",
)

#: The other side of the same sentence.
SECOND_PROGRAM_DOES_NOT_COVER = (
    "B1's sweep is not re-enumerated: no second program re-runs the ~13k "
    "mutants or re-decides them",
    "B2's census comparison is not recomputed here (the census checker is its "
    "own second program, invoked by B2 itself, but nothing re-derives B2's "
    "own admission set)",
    "B3's detectors are not re-exercised, and no program executes a mutant",
    "B4's digests are not retaken by a second implementation",
    "B6's replays are not re-run",
    "B7's per-code counts are not recomputed",
    "B11's import closure is not recomputed",
    "B12's mutant arm is not re-decided",
)


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
            "covers": list(SECOND_PROGRAM_COVERS),
            "does_not_cover": list(SECOND_PROGRAM_DOES_NOT_COVER),
            "scope_note": (
                "SEVEN OF THE TWELVE GATES ARE SCORED ONCE. The second program "
                "re-derives what a reader can recompute from committed bytes "
                "and the sealed corpus; it does not re-run the sweep, the "
                "detectors, the replays or the closures. That is a real limit "
                "on how much of this run is independently checked, and it is "
                "published here rather than implied by the list of things the "
                "checker does do"
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
    # The receipts document is assembled BEFORE the detectors, because B3's
    # `name_sweep` detector sweeps the bytes this run is about to write and a
    # detector that swept nothing was the review's second finding. The
    # verdicts document cannot be swept here — it carries B3's own row — and
    # its sweep is B5's, plus the second program's re-sweep of the COMMITTED
    # bytes.
    receipts = _receipts_document(prereg, tree, replay)
    detectors = _detectors(document, inputs, replay, receipts)
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


def _corpus_provenance(prereg: dict, document: dict, tree: dict) -> dict:
    """F5's disclosure: what moved in the sealed corpus, and when.

    The prereg's `sealed_commit_note` says the corpus was sealed at the H-PRE
    commit "before scripts/symbol_ledger.py existed". That is true of the FILE
    and false of the PINNED BYTES: the fixtures were amended twice after
    H-PRE — both times before any registered run, both times disclosed in the
    corpus's own `amendments` block — and the digest the prereg freezes is the
    later one. The H-P1 review found that the run artifact never said so. It
    says so here, without editing the frozen note, and the prereg carries the
    correction as amendment `amd-2026-09-02-corpus-provenance`.
    """

    amendments = [
        {
            "amendment": row.get("amendment"),
            "amendment_id": row.get("amendment_id"),
            "dated": row.get("dated"),
            "stage": row.get("stage"),
            "adds": list(row.get("adds") or ()),
            "edits": list(row.get("edits") or ()),
            "removes": list(row.get("removes") or ()),
            "finding": row.get("finding"),
            "b9_reanchored": row.get("b9_reanchored"),
            "superseded_b9": row.get("superseded_b9"),
        }
        for row in (document.get("amendments") or ())
    ]
    return {
        "fixtures": FIXTURES,
        "fixtures_first_committed_at": tree["first_commit_of"].get(FIXTURES),
        "fixtures_pinned_bytes_committed_at": _last_commit(FIXTURES),
        "census_first_committed_at": tree["first_commit_of"].get(CENSUS),
        "census_pinned_bytes_committed_at": _last_commit(CENSUS),
        "sealed_commit": prereg["sealed_commit"],
        "sealed_commit_note_as_registered": prereg["sealed_commit_note"],
        "correction": (
            "The sealed commit is where the corpus FILE was first committed, "
            "before scripts/symbol_ledger.py existed, and B10's ancestry proof "
            "is about that commit. The BYTES the prereg pins are later: the "
            "corpus was amended after H-PRE and the amendments are listed "
            "above. Every amendment is PRE-RUN — no checker had scored a "
            "verdict against this corpus when they were made, which is the "
            "window the corpus's own amendment note says is the only one in "
            "which it may move — but 'sealed before the checker existed' is "
            "true of the file and not of the digest, and the two were not "
            "distinguished in run 1's artifact"
        ),
        "amendments": amendments,
        "amendments_are_pre_run": True,
        "what_moved": (
            "amendment 1 added one declaration fixture (hr-fx-s1-t14) to "
            "discriminate a clause transposition the sealed corpus could not "
            "discriminate, which moved the declaration population 38 -> 39 and "
            "forced B9's split, class balance and void threshold to be "
            "recomputed and re-sealed. B9's `superseded_anchor_arm` reports "
            "whether the re-anchoring changed the control's outcome"
        ),
    }


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
    richer = b9["richer_family"]
    r_h1_caveat = None
    if richer["fit_half_selected"]["exceeds_the_void_threshold"]:
        r_h1_caveat = (
            "R-H1's `green` is computed from the REGISTERED B9 family, which "
            "is what the preregistration names. A RICHER surface family — "
            "single-feature closed intervals and two-feature conjunctions over "
            "the same three allowed inputs — authored on 2026-09-02 after run "
            "1's score and registered by prereg amendment "
            "amd-2026-09-02-b9-families, selects "
            f"{richer['fit_half_selected']['rule']} on the fit half and reaches "
            f"{richer['fit_half_selected']['out_of_half_agreement']} out of "
            f"half, which EXCEEDS the void threshold "
            f"{b9['void_threshold']}. The sentence below therefore stands on a "
            "control whose registered family could not separate the verdict, "
            "and whose richer sibling can. A successor must fix the family "
            "before its run and score it on a larger held-out half than "
            "nineteen rows."
        )
    if b9["no_member_of_the_registered_family_could_have_fired"]:
        inert = (
            "The registered B9 family's ceiling on the scored half is "
            f"{b9['family_ceiling_on_scored_half']} against a threshold of "
            f"{b9['void_threshold']}: NO MEMBER of the registered family could "
            "have fired the voiding sentence on this corpus. B9's green is "
            "therefore evidence that the registered control did not separate "
            "the verdict, and not evidence that no surface-only rule can."
        )
        r_h1_caveat = inert if r_h1_caveat is None else inert + " " + r_h1_caveat
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
        "corpus_provenance": _corpus_provenance(prereg, document, tree),
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
            "fired_under_richer_family": richer["fit_half_selected"][
                "exceeds_the_void_threshold"
            ],
            "fired_under_richer_family_note": (
                "the richer surface family was authored on 2026-09-02, after "
                "run 1's score and in response to the H-P1 review, and is "
                "registered by prereg amendment amd-2026-09-02-b9-families. "
                "The sentence's own `fired` above is computed from the "
                "REGISTERED family, because the registered control is what the "
                "prereg names and a control chosen after a result is not a "
                "control. This field reports the other reading rather than "
                "hiding it"
            ),
        },
        "result_gates": {
            "R-H1": {
                "requires": r_h1_requires,
                "requires_note": prereg["r_h1_requires_note"],
                "green": r_h1_green,
                "green_is_computed_from_the_registered_b9_family": True,
                "caveat": r_h1_caveat,
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
