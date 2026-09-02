#!/usr/bin/env python3
"""H-P1's second program: re-derive the registered run from committed bytes.

`scripts/run_house_rules_gates.py` writes two artifacts and says a great many
things about them. This file is the other side of that: it reads the two
committed documents and asks, of everything in them that a second program can
recompute, whether it is true. A run artifact that could only be read is a
claim; one that a separate program can falsify is evidence, and DESIGN §7's
B2 makes "two sides, two programs" the standard the census is already held
to. B10 asks the same of the run itself.

What is re-derived here, never trusted
--------------------------------------

* **the pins** — every `frozen` row in the prereg re-digested against the
  tree, so a corpus edited after the freeze cannot be checked as sealed;
* **the ancestry** — `git merge-base --is-ancestor` run again, strictly, and
  the artifact's own `ancestry_proof` sentence reconstructed from it;
* **provenance** — the writer's digest and every declared input's digest
  recomputed;
* **the verdict table** — every gate's `verdict` must be GREEN exactly when
  its `misses` list is empty, `gate_greens`/`gate_reds` must agree with the
  table, and every gate's quoted `clause` must be the prereg's clause
  VERBATIM. A clause softened between the score and the artifact is the
  failure mode this check exists for;
* **the result gates** — R-H1 green exactly when every gate in the prereg's
  own requirement list is green AND the run was registered before it ran AND
  the voiding sentence did not fire; the licensed sentence present exactly
  when it is green; R-H3 licensed exactly when there is a red or a firing;
* **B9's arithmetic** — the fit/scored halves re-derived from the sealed
  fixture order by the prereg's own even/odd rule, the scored half's
  majority-class rate recomputed from the receipts, the threshold recomputed
  as anchor plus the declared margin, the REPORTED fitted rule re-evaluated
  on the committed fixture lines, and the firing recomputed as a STRICT
  exceedance;
* **the receipt set** — set equality against the sealed declaration fixtures,
  so a dropped receipt fails rather than passing quietly;
* **B5, by re-sweeping the committed bytes** — the admitted names are derived
  HERE from the sealed corpus (parsed out of the fixture lines the seal marks
  admitted, plus the B12 mutants' sealed resolved keys), not read from the
  run, and the two committed outputs are swept for them. This is the check
  the runner structurally cannot perform on itself: it sweeps the documents
  it is about to write, and this sweeps the documents it wrote;
* **the whole-repository count B5's scoping is disclosed against** — the
  runner publishes how many pre-existing files contain an admitted name so
  its output-tree scoping can be judged. That number is recomputed here by a
  separate implementation of the same sweep, so it is verified rather than
  asserted.

Names are derived in memory and never printed. This program's own stdout
would otherwise become one more durable artifact carrying what B5 forbids.

`--replay`
----------

Re-runs the gates runner into a temporary directory and compares the bytes.
Everything must be identical except a short, NAMED list of fields that are
facts about the tip and the tree rather than about the computation — the head
commit, the ancestry sentence quoting it, and the two working-tree digests
(which move because the run's own outputs now exist in the tree). Each of
those is independently recomputed here against the current tree, so the
carve-out is checked rather than granted.

The replay therefore wants a CLEAN tree, which means: run it after the two
outputs are committed, not between the run and the commit. On a dirty tree
the runner refuses, and `--replay-allow-dirty` is the pre-run testing hatch —
it widens the mask to the tree-state fields as well and says so in the
output, so a rehearsal cannot be mistaken for the real comparison.

Usage
-----

    python scripts/check_house_rules_receipts.py
    python scripts/check_house_rules_receipts.py --replay
    python scripts/check_house_rules_receipts.py \\
        --verdicts /tmp/v.json --receipts /tmp/r.json

Exit 0 clean, exit 1 with a named failure.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import run_house_rules_gates as gates  # noqa: E402
import symbol_ledger as SL  # noqa: E402
import write_stage  # noqa: E402
from prereg_pins import sha256_lf  # noqa: E402

PREREG = REPO / gates.PREREG
FIXTURES = REPO / gates.FIXTURES
VERDICTS = REPO / gates.RUN_OUT
RECEIPTS = REPO / gates.RECEIPTS_OUT
RUNNER = REPO / gates.THIS

#: DESIGN §8's R-H3 in its own words — "Any failed construction gate
#: B1-B8/B10/B11 or a fired B9". Written out here INDEPENDENTLY of the
#: runner's own constant, so a runner that widened its licence to every gate
#: it happens to score is caught rather than echoed.
R_H3_GATES = ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B10", "B11")

#: Fields a replay at a later tip may legitimately differ on, each one a fact
#: about WHERE the replay ran rather than about what it computed. Nothing else
#: may move.
TIP_DEPENDENT: tuple[tuple[str, ...], ...] = (
    ("scoring_tree", "head_commit"),
    ("construction_gate", "B10", "head_commit"),
    ("construction_gate", "B10", "ancestry_proof"),
    ("construction_gate", "B4", "working_tree_digest_before"),
    ("construction_gate", "B4", "working_tree_digest_after"),
)

#: Additionally masked under `--replay-allow-dirty`, which is a rehearsal and
#: licenses nothing. Every one of these is downstream of the dirty flag.
DIRTY_DEPENDENT: tuple[tuple[str, ...], ...] = (
    ("scoring_tree",),
    ("registered_before_the_run",),
    ("registration_commit",),
    ("construction_gate", "B10"),
    ("gate_greens",),
    ("gate_reds",),
    ("result_gates", "R-H1"),
    ("result_gates", "R-H3"),
)


class Failures(list):
    """Named failures, in the order they were found."""

    def add(self, name: str, detail: str) -> None:
        self.append((name, detail))
        print(f"  FAIL [{name}] {detail}")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    ).stdout.strip()


def _is_ancestor(earlier: str, later: str) -> bool:
    """Strict, exactly as the runner reads it: same-commit is not ancestry."""

    if not earlier or not later or earlier == later:
        return False
    return (
        subprocess.run(
            ["git", "-C", str(REPO), "merge-base", "--is-ancestor", earlier, later],
            capture_output=True,
            timeout=120,
        ).returncode
        == 0
    )


def _first_commit(path: str) -> str | None:
    lines = [
        line.strip()
        for line in _git(
            "log", "--format=%H", "--diff-filter=A", "--reverse", "--", path
        ).splitlines()
        if line.strip()
    ]
    return lines[0] if lines else None


def _rest(line: str) -> str:
    return line.partition(" ")[2]


def load_json(path: Path, name: str, failures: Failures) -> dict | None:
    if not path.exists():
        failures.add(f"missing-{name}", f"{path} does not exist")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.add(f"unreadable-{name}", f"{path} is not JSON: {exc}")
        return None


# --------------------------------------------------------------------------
# shape, clocks, prereg binding
# --------------------------------------------------------------------------


def check_shape(verdicts: dict, receipts: dict, prereg: dict, failures: Failures) -> None:
    """Schemas, stage, and the date that must be a committed constant."""

    before = len(failures)
    if verdicts.get("schema") != gates.RUN_SCHEMA:
        failures.add("verdicts-schema", f"schema is {verdicts.get('schema')!r}")
    if receipts.get("schema") != gates.RECEIPTS_SCHEMA:
        failures.add("receipts-schema", f"schema is {receipts.get('schema')!r}")
    for label, document in (("verdicts", verdicts), ("receipts", receipts)):
        if document.get("stage") != gates.STAGE:
            failures.add(f"{label}-stage", f"stage is {document.get('stage')!r}")
        if document.get("date") != gates.DATE:
            failures.add(
                f"{label}-date",
                f"date is {document.get('date')!r}; the runner's committed DATE "
                f"constant is {gates.DATE!r}. A date that is not the constant is "
                f"a wall-clock read, and a replay would not reproduce it",
            )
        if document.get("preregistration_id") != prereg["preregistration_id"]:
            failures.add(
                f"{label}-prereg-id",
                f"cites preregistration_id {document.get('preregistration_id')!r}",
            )
    if len(failures) == before:
        print(f"  shape OK: both artifacts carry {gates.STAGE} and date {gates.DATE}")


_CLOCK_KEYS = ("timestamp", "generated_at", "created_at", "run_at", "wall_clock", "now")


def check_no_clock(document: dict, label: str, failures: Failures) -> None:
    """A replayable artifact carries no clock field, at any depth."""

    found: list[str] = []

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if key.casefold() in _CLOCK_KEYS:
                    found.append(f"{path}.{key}")
                walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(document, label)
    if found:
        failures.add(
            "record-clock",
            f"{label} carries {len(found)} clock field(s): {found[:5]}",
        )
    else:
        print(f"  no clock in {label}")


def check_prereg_binding(
    verdicts: dict, receipts: dict, prereg: dict, prereg_path: Path, failures: Failures
) -> None:
    """Both artifacts pin the registration by digest, and cite its commit."""

    before = len(failures)
    expected = sha256_lf(prereg_path)
    registration_commit = _first_commit(gates.PREREG)
    for label, document in (("verdicts", verdicts), ("receipts", receipts)):
        if document.get("preregistration_sha256_lf") != expected:
            failures.add(
                f"{label}-prereg-digest",
                f"cites {document.get('preregistration_sha256_lf')} for "
                f"{prereg_path.name}; recomputed {expected}",
            )
        if registration_commit is not None and (
            document.get("registration_commit") != registration_commit
        ):
            failures.add(
                f"{label}-registration-commit",
                f"cites {document.get('registration_commit')} as the commit that "
                f"added the prereg; git says {registration_commit}",
            )
        if document.get("registered_before_the_run") and not document.get(
            "registration_commit"
        ):
            failures.add(
                f"{label}-registration-commit",
                "claims the run was registered before it ran while citing no "
                "commit that added the registration",
            )
    if len(failures) == before:
        print(f"  prereg binding OK: both cite {expected[:12]} added at "
              f"{(registration_commit or '?')[:12]}")


def check_frozen_pins(prereg: dict, failures: Failures) -> None:
    """Every `frozen` row re-digested against the tree, not trusted."""

    moved = []
    for row in prereg["frozen"]:
        path = REPO / row["path"]
        if not path.exists():
            moved.append((row["path"], "missing"))
            continue
        actual = sha256_lf(path)
        if actual != row["sha256_lf"]:
            moved.append((row["path"], actual[:12]))
    if moved:
        failures.add(
            "frozen-pin",
            f"{len(moved)} prereg `frozen` pin(s) no longer match the tree: {moved}",
        )
    else:
        print(f"  frozen pins OK: {len(prereg['frozen'])} re-digested and unmoved")


def check_provenance(document: dict, label: str, failures: Failures) -> None:
    """The writer and every declared input, re-digested."""

    provenance = document.get("provenance") or {}
    before = len(failures)
    writer = provenance.get("writer")
    if writer != gates.THIS:
        failures.add(f"{label}-writer", f"writer is {writer!r}, not {gates.THIS!r}")
    elif provenance.get("writer_sha256_lf") != sha256_lf(RUNNER):
        failures.add(
            f"{label}-writer-digest",
            f"cites {provenance.get('writer_sha256_lf')} for the writer; "
            f"recomputed {sha256_lf(RUNNER)}",
        )
    second = provenance.get("second_program") or {}
    if second.get("path") != gates.RECEIPT_CHECKER:
        failures.add(
            f"{label}-second-program",
            f"the artifact pins {second.get('path')!r} as the second program; "
            f"this is {gates.RECEIPT_CHECKER}",
        )
    elif second.get("sha256_lf") != sha256_lf(Path(__file__).resolve()):
        failures.add(
            f"{label}-second-program-digest",
            "the artifact pins a different build of this checker than the one "
            "reading it; the run was verified under other bytes",
        )
    if not provenance.get("inputs"):
        failures.add(
            f"{label}-provenance",
            "the artifact declares no inputs, so there is nothing to re-digest",
        )
    for row in provenance.get("inputs", []):
        path = REPO / row["path"]
        if not path.exists():
            failures.add(f"{label}-input-missing", f"{row['path']} does not exist")
            continue
        actual = sha256_lf(path)
        if actual != row["sha256_lf"]:
            failures.add(
                f"{label}-input-digest",
                f"{row['path']} is cited at {row['sha256_lf'][:12]}; recomputed "
                f"{actual[:12]}",
            )
    if len(failures) == before:
        print(
            f"  provenance OK ({label}): writer and "
            f"{len(provenance.get('inputs', []))} input digest(s) recomputed"
        )


def check_ancestry(verdicts: dict, prereg: dict, failures: Failures) -> None:
    """B10's ordering claim, proved again rather than read."""

    before = len(failures)
    sealed = verdicts.get("sealed_commit")
    if sealed != prereg["sealed_commit"]:
        failures.add(
            "sealed-commit",
            f"the artifact cites {sealed}; the prereg seals {prereg['sealed_commit']}",
        )
        sealed = prereg["sealed_commit"]
    tree = verdicts.get("scoring_tree") or {}
    head = tree.get("head_commit")
    if not head:
        # Without this the check is vacuous: a missing head makes the claim
        # False and the recomputation False, and two absences agree.
        failures.add(
            "ancestry-head",
            "the artifact records no head commit, so its ordering claim is not "
            "about any tip",
        )
    claimed = bool(tree.get("sealed_commit_is_strict_ancestor_of_head"))
    actual = _is_ancestor(sealed, head or "")
    if claimed != actual:
        failures.add(
            "ancestry",
            f"the artifact claims sealed_commit_is_strict_ancestor_of_head="
            f"{claimed}; git merge-base --is-ancestor says {actual}",
        )
    b10 = (verdicts.get("construction_gate") or {}).get("B10") or {}
    expected_proof = (
        "git merge-base --is-ancestor "
        f"{sealed[:12]} {(head or '')[:12]} -> "
        + ("true" if actual else "false")
    )
    if b10.get("ancestry_proof") != expected_proof:
        failures.add(
            "ancestry-proof",
            f"B10 records {b10.get('ancestry_proof')!r}; recomputed "
            f"{expected_proof!r}",
        )
    if b10.get("head_commit") != head:
        failures.add(
            "ancestry-head",
            f"B10 records head {b10.get('head_commit')} and the scoring tree "
            f"records {head}",
        )
    if len(failures) == before:
        print(f"  ancestry OK: {sealed[:12]} is a strict ancestor of {(head or '')[:12]}")


# --------------------------------------------------------------------------
# the verdict table and the result gates
# --------------------------------------------------------------------------


def check_verdict_table(verdicts: dict, prereg: dict, failures: Failures) -> None:
    """GREEN iff no misses; the roll-ups agree; the clauses are verbatim."""

    before = len(failures)
    table = verdicts.get("construction_gate") or {}
    missing = [name for name in gates.SCORED_GATES if name not in table]
    if missing:
        failures.add("gate-missing", f"the table has no row for {missing}")
    greens = verdicts.get("gate_greens") or {}
    for name in gates.SCORED_GATES:
        row = table.get(name)
        if not isinstance(row, dict):
            failures.add(
                "gate-shape",
                f"{name}'s row is {type(row).__name__}, not an object, so its "
                f"verdict, roll-up and clause could not be checked",
            )
            continue
        misses = row.get("misses")
        if not isinstance(misses, list):
            failures.add("gate-misses", f"{name} carries no `misses` list")
            continue
        expected = "GREEN" if not misses else "RED"
        if row.get("verdict") != expected:
            failures.add(
                "gate-verdict",
                f"{name} records verdict {row.get('verdict')!r} with "
                f"{len(misses)} miss(es); GREEN means exactly an empty misses list",
            )
        if greens.get(name) != (row.get("verdict") == "GREEN"):
            failures.add(
                "gate-greens",
                f"gate_greens[{name}]={greens.get(name)!r} disagrees with the "
                f"table's {row.get('verdict')!r}",
            )
        clause = prereg["gates"].get(name)
        if row.get("clause") != clause:
            failures.add(
                "gate-clause",
                f"{name} quotes a clause that is not the registered one; a "
                f"clause may not move between the score and the artifact",
            )
    expected_reds = sorted(
        name
        for name in gates.SCORED_GATES
        if not (isinstance(table.get(name), dict) and table[name].get("verdict") == "GREEN")
    )
    if sorted(verdicts.get("gate_reds") or []) != expected_reds:
        failures.add(
            "gate-reds",
            f"gate_reds is {verdicts.get('gate_reds')!r}; the table's reds are "
            f"{expected_reds}",
        )
    if len(failures) == before:
        print(
            f"  verdict table OK: {len(gates.SCORED_GATES)} gates, "
            f"reds {expected_reds or 'none'}, every clause verbatim from the prereg"
        )


def check_result_gates(verdicts: dict, prereg: dict, failures: Failures) -> None:
    """R-H1's sentence, R-H2's no-threshold arm, R-H3's licence."""

    before = len(failures)
    table = verdicts.get("construction_gate") or {}
    result = verdicts.get("result_gates") or {}
    r_h1 = result.get("R-H1") or {}
    if list(r_h1.get("requires") or []) != list(prereg["r_h1_requires"]):
        failures.add(
            "r-h1-requires",
            f"R-H1 requires {r_h1.get('requires')}; the prereg registers "
            f"{prereg['r_h1_requires']}",
        )
    required = list(prereg["r_h1_requires"])
    fired = bool((verdicts.get("voiding_sentence") or {}).get("fired"))
    registered = bool(verdicts.get("registered_before_the_run"))
    expected_green = (
        all(
            isinstance(table.get(name), dict) and table[name].get("verdict") == "GREEN"
            for name in required
        )
        and not fired
        and registered
    )
    if bool(r_h1.get("green")) != expected_green:
        failures.add(
            "r-h1-green",
            f"R-H1 records green={r_h1.get('green')!r}; recomputed {expected_green} "
            f"from the required gates, the voiding flag and "
            f"registered_before_the_run={registered}",
        )
    sentence = r_h1.get("licensed_sentence")
    if expected_green and sentence != prereg["r_h1_sentence"]:
        failures.add(
            "r-h1-sentence",
            "R-H1 is green but the licensed sentence is not the registered one",
        )
    if not expected_green and sentence is not None:
        failures.add(
            "r-h1-sentence",
            "R-H1 is not green and a sentence is licensed anyway",
        )
    r_h2 = result.get("R-H2") or {}
    if r_h2.get("threshold") is not None or not r_h2.get("gates_nothing"):
        failures.add("r-h2-threshold", "the R-H2 arm carries a threshold")
    if r_h2.get("population_size") != prereg["r_h2"]["population_size"]:
        failures.add(
            "r-h2-population",
            f"R-H2 counted over {r_h2.get('population_size')} hypotheses; the "
            f"prereg seals {prereg['r_h2']['population_size']}",
        )
    parsed = r_h2.get("parse_as_declarations")
    if not isinstance(parsed, int) or not 0 <= parsed <= (r_h2.get("population_size") or 0):
        failures.add("r-h2-count", f"R-H2's count is {parsed!r}")
    r_h3 = result.get("R-H3") or {}
    if list(r_h3.get("gates_in_scope") or []) != list(R_H3_GATES):
        failures.add(
            "r-h3-scope",
            f"R-H3 scopes itself to {r_h3.get('gates_in_scope')}; the clause "
            f"names B1-B8/B10/B11 ({list(R_H3_GATES)}), with B9 entering "
            f"through the firing clause and B12 reported beside it",
        )
    in_scope = sorted(
        name for name in (verdicts.get("gate_reds") or []) if name in R_H3_GATES
    )
    expected_licence = bool(in_scope) or fired
    if bool(r_h3.get("licensed")) != expected_licence:
        failures.add(
            "r-h3",
            f"R-H3 records licensed={r_h3.get('licensed')!r}; the clause "
            f"licenses on an in-scope red or a firing, and this run has "
            f"in-scope reds={in_scope}, fired={fired}",
        )
    if sorted(r_h3.get("reds_in_scope") or []) != in_scope:
        failures.add(
            "r-h3-scope",
            f"R-H3 lists {r_h3.get('reds_in_scope')} as its in-scope reds; "
            f"recomputed {in_scope}",
        )
    if len(failures) == before:
        print(
            f"  result gates OK: R-H1 green={expected_green}, R-H2 reports "
            f"{parsed} with no threshold, R-H3 licensed={expected_licence}"
        )


# --------------------------------------------------------------------------
# B9's arithmetic
# --------------------------------------------------------------------------


def _surface_features(line: str) -> dict:
    """Re-implemented here rather than imported: two programs, two readings."""

    tokens = line.split()
    return {
        "token_count": len(tokens),
        "line_length": len(line),
        "has_command_word": 1 if tokens and tokens[0].casefold() == "declare" else 0,
    }


def check_b9(
    verdicts: dict, receipts: dict, prereg: dict, fixtures: dict, failures: Failures
) -> None:
    """The split, the anchor, the threshold, the rule, and the strict compare."""

    before = len(failures)
    control = prereg["b9_control"]
    declarations = [row for row in fixtures["fixtures"] if row["kind"] == "declaration"]
    derived_fit = [row["fixture_id"] for index, row in enumerate(declarations) if index % 2 == 0]
    derived_scored = [row["fixture_id"] for index, row in enumerate(declarations) if index % 2 == 1]
    if derived_fit != list(control["fit_half_fixture_ids"]):
        failures.add(
            "b9-split",
            "the prereg's FIT half is not what the registered even/odd rule "
            "yields over the sealed fixture order",
        )
    if derived_scored != list(control["scored_half_fixture_ids"]):
        failures.add(
            "b9-split",
            "the prereg's SCORED half is not what the registered even/odd rule "
            "yields over the sealed fixture order",
        )

    truth = {row["fixture_id"]: row["verdict"] for row in receipts.get("receipts", [])}
    lines = {row["fixture_id"]: row["line"] for row in fixtures["fixtures"]}
    scored_ids = list(control["scored_half_fixture_ids"])
    fit_ids = list(control["fit_half_fixture_ids"])
    if not all(fixture_id in truth for fixture_id in scored_ids + fit_ids):
        # Named as UNVERIFIED rather than returned on: five further checks
        # below depend on the receipts covering both halves, and a silent
        # return would report "no failures" for checks that never ran.
        failures.add(
            "b9-truth",
            "the receipts do not cover both halves, so the anchor, threshold, "
            "rule, agreement and firing could not be recomputed",
        )
        return

    counts: dict[str, int] = {}
    for fixture_id in scored_ids:
        counts[truth[fixture_id]] = counts.get(truth[fixture_id], 0) + 1
    anchor = round(max(counts.values()) / len(scored_ids), 6)
    if anchor != prereg["frozen_numbers"]["b9_scored_half_majority_class_rate"]:
        failures.add(
            "b9-anchor",
            f"the scored half's majority-class rate recomputes to {anchor}; the "
            f"prereg freezes "
            f"{prereg['frozen_numbers']['b9_scored_half_majority_class_rate']}",
        )
    margin = prereg["frozen_numbers"]["b9_declared_margin_points"] / 100
    threshold = round(anchor + margin, 6)
    if threshold != prereg["frozen_numbers"]["b9_void_threshold"]:
        failures.add(
            "b9-threshold",
            f"anchor {anchor} plus the declared {margin} margin is {threshold}; "
            f"the prereg freezes {prereg['frozen_numbers']['b9_void_threshold']}",
        )

    b9 = (verdicts.get("construction_gate") or {}).get("B9") or {}
    rule_id = b9.get("fitted_rule") or ""
    if rule_id.startswith("const:"):
        # The two constant predictors carry no operator; the hypothesis space
        # includes them, so the checker must be able to re-evaluate one.
        parts = ["const", "", rule_id.partition(":")[2]]
    else:
        parts = rule_id.split(":")
    if len(parts) != 3:
        failures.add("b9-rule", f"the fitted rule id {rule_id!r} is unreadable")
        return

    def predict(line: str) -> str:
        feature, op, value = parts
        if feature == "const":
            return value
        actual = _surface_features(line)[feature]
        target = int(value)
        hit = (
            actual <= target
            if op == "le"
            else actual >= target
            if op == "ge"
            else actual == target
        )
        return SL.VERDICT_ADMITTED if hit else SL.VERDICT_REFUSED

    def accuracy(ids: list[str]) -> float:
        return sum(1 for f in ids if predict(lines[f]) == truth[f]) / len(ids)

    fit_accuracy = round(accuracy(fit_ids), 6)
    agreement = round(accuracy(scored_ids), 6)
    if b9.get("fit_half_accuracy") != fit_accuracy:
        failures.add(
            "b9-fit-accuracy",
            f"B9 reports fit accuracy {b9.get('fit_half_accuracy')}; the reported "
            f"rule {rule_id} scores {fit_accuracy} on the fit half",
        )
    if b9.get("out_of_half_agreement") != agreement:
        failures.add(
            "b9-agreement",
            f"B9 reports out-of-half agreement {b9.get('out_of_half_agreement')}; "
            f"the reported rule {rule_id} scores {agreement} on the scored half",
        )
    if b9.get("void_threshold") != threshold:
        failures.add(
            "b9-reported-threshold",
            f"B9 carries threshold {b9.get('void_threshold')}; recomputed {threshold}",
        )
    fired = agreement > threshold
    if bool(b9.get("fired")) != fired:
        failures.add(
            "b9-fired",
            f"B9 records fired={b9.get('fired')!r}; the sentence fires only on a "
            f"STRICT exceedance, and {agreement} > {threshold} is {fired}",
        )
    if bool(b9.get("agreement_equals_the_threshold")) != (agreement == threshold):
        failures.add(
            "b9-equality",
            "B9's equality flag disagrees with the recomputed comparison",
        )
    voiding = verdicts.get("voiding_sentence") or {}
    if bool(voiding.get("fired")) != fired or voiding.get("agreement") != agreement:
        failures.add(
            "b9-voiding-block",
            "the artifact's voiding_sentence block disagrees with B9's own row",
        )
    if voiding.get("text") != control["voiding_sentence"]:
        failures.add("b9-voiding-text", "the voiding sentence is not the registered one")
    if len(failures) == before:
        print(
            f"  B9 OK: split re-derived, anchor {anchor}, threshold {threshold}, "
            f"rule {rule_id} agrees {agreement} out of half, fired={fired} (strict)"
        )


# --------------------------------------------------------------------------
# the receipt set
# --------------------------------------------------------------------------


def check_receipts(
    verdicts: dict, receipts: dict, fixtures: dict, failures: Failures
) -> None:
    """Set equality against the sealed declaration fixtures. Missing fails."""

    before = len(failures)
    sealed = {
        row["fixture_id"] for row in fixtures["fixtures"] if row["kind"] == "declaration"
    }
    rows = receipts.get("receipts") or []
    have = [row.get("fixture_id") for row in rows]
    missing = sorted(sealed - set(have))
    extra = sorted(set(have) - sealed)
    duplicated = sorted({f for f in have if have.count(f) > 1})
    if missing:
        failures.add(
            "missing-receipt",
            f"{len(missing)} sealed declaration fixture(s) have no receipt: "
            f"{missing[:8]}",
        )
    if extra:
        failures.add("extra-receipt", f"receipts for unsealed ids: {extra[:8]}")
    if duplicated:
        failures.add("duplicate-receipt", f"repeated fixture ids: {duplicated[:8]}")
    if receipts.get("receipt_count") != len(rows):
        failures.add(
            "receipt-count",
            f"receipt_count is {receipts.get('receipt_count')} over {len(rows)} rows",
        )
    cited = (verdicts.get("receipts_artifact") or {}).get("receipt_count")
    if cited != len(rows):
        failures.add(
            "receipt-count-cited",
            f"the verdicts artifact cites {cited} receipts; the receipts artifact "
            f"carries {len(rows)}",
        )

    expected = {
        row["fixture_id"]: (
            row["expected_verdict"],
            row["expected_refusal_code"],
            row["expected_deciding_clause"],
        )
        for row in fixtures["fixtures"]
        if row["kind"] == "declaration"
    }
    off_seal = sorted(
        row["fixture_id"]
        for row in rows
        if row.get("fixture_id") in expected
        and (
            row.get("verdict"),
            row.get("refusal_code"),
            row.get("deciding_clause"),
        )
        != expected[row["fixture_id"]]
    )
    claimed = sorted(
        row["fixture_id"] for row in rows if not row.get("matches_sealed_expectation")
    )
    if off_seal != claimed:
        failures.add(
            "receipt-expectation",
            f"{len(off_seal)} receipt(s) differ from the seal but "
            f"{len(claimed)} carry matches_sealed_expectation=false: "
            f"{sorted(set(off_seal) ^ set(claimed))[:8]}",
        )
    b1 = (verdicts.get("construction_gate") or {}).get("B1") or {}
    if off_seal and b1.get("verdict") == "GREEN":
        failures.add(
            "receipt-expectation",
            f"{len(off_seal)} receipt(s) differ from the seal and B1 is GREEN",
        )
    counts = verdicts.get("counts") or {}
    for key in ("fixtures_total", "declaration_fixtures", "use_fixtures", "admitted",
                "refused", "b3_mutants", "b12_mutants"):
        if counts.get(key) != fixtures["counts"].get(key):
            failures.add(
                "counts",
                f"counts.{key} is {counts.get(key)}; the seal says "
                f"{fixtures['counts'].get(key)}",
            )
    if len(failures) == before:
        print(f"  receipts OK: {len(rows)} receipts, set-equal to the sealed "
              f"declaration fixtures, every row on the seal")


# --------------------------------------------------------------------------
# B5, re-swept over the committed bytes
# --------------------------------------------------------------------------


def check_clause_order(
    verdicts: dict, receipts: dict, fixtures: dict, failures: Failures
) -> None:
    """B1's exclusivity claim, re-derived against the sealed clause order.

    The seal carries `clause_order` — committed at H-PRE before any checker
    existed. Every receipt's deciding clause must be the clause that seal maps
    its refusal code to, and the shipped `CLAUSE_ORDER` must be that seal in
    that order. Checking the module's map against itself proves nothing, so
    the sealed copy is the one used on both sides.
    """

    before = len(failures)
    sealed_rows = sorted(fixtures["clause_order"], key=lambda row: row["rank"])
    sealed_order = tuple((row["clause"], row["refusal_code"]) for row in sealed_rows)
    sealed_clause_by_code = {row["refusal_code"]: row["clause"] for row in sealed_rows}
    b1 = (verdicts.get("construction_gate") or {}).get("B1") or {}

    if sealed_order != SL.CLAUSE_ORDER:
        failures.add(
            "clause-order",
            "the shipped symbol_ledger.CLAUSE_ORDER is not the order sealed in "
            "the fixtures",
        )
    if b1.get("shipped_clause_order_equals_the_sealed_order") is not (
        sealed_order == SL.CLAUSE_ORDER
    ):
        failures.add(
            "clause-order",
            f"B1 records shipped_clause_order_equals_the_sealed_order="
            f"{b1.get('shipped_clause_order_equals_the_sealed_order')!r}; "
            f"recomputed {sealed_order == SL.CLAUSE_ORDER}",
        )

    off = []
    for row in receipts.get("receipts") or []:
        code = row.get("refusal_code")
        if code == SL.REFUSAL_NONE:
            if row.get("deciding_clause") != SL.CLAUSE_ADMIT:
                off.append(row.get("fixture_id"))
            continue
        if sealed_clause_by_code.get(code) != row.get("deciding_clause"):
            off.append(row.get("fixture_id"))
    if off:
        failures.add(
            "clause-exclusivity",
            f"{len(off)} receipt(s) decided on a clause the SEALED order does "
            f"not map their refusal code to: {off[:8]}",
        )

    expected_multi = sorted(
        row["fixture_id"] for row in fixtures["fixtures"] if row.get("also_grounds_for")
    )
    if sorted(b1.get("multi_ground_fixtures") or []) != expected_multi:
        failures.add(
            "clause-multi-ground",
            f"B1 names {b1.get('multi_ground_fixtures')} as the fixtures where "
            f"more than one clause held; the seal names {expected_multi}",
        )
    by_id = {row["fixture_id"]: row for row in fixtures["fixtures"]}
    drifted = sorted(
        row["fixture_id"]
        for row in receipts.get("receipts") or []
        if row.get("fixture_id") in by_id
        and sorted(row.get("also_grounds_for") or [])
        != sorted(by_id[row["fixture_id"]].get("also_grounds_for") or [])
    )
    if drifted:
        failures.add(
            "clause-multi-ground",
            f"{len(drifted)} receipt(s) record a different set of also-holding "
            f"grounds than the seal: {drifted[:8]}",
        )
    if len(failures) == before:
        print(
            f"  clause order OK: the shipped order is the sealed one, every "
            f"receipt decided on the clause the seal maps its code to, and the "
            f"{len(expected_multi)} multi-ground fixtures match"
        )


def admitted_names_from_the_seal(fixtures: dict) -> list[str]:
    """Derive the names B5 forbids from the SEAL, never from the run.

    The runner sweeps for the keys its live replay admitted. Deriving the same
    set here from the sealed corpus — the declaration lines the seal marks
    admitted, parsed to their normalized ledger key, plus the B12 mutants'
    sealed resolved keys — is what makes the re-sweep a second opinion rather
    than an echo. A disagreement in the COUNT is reported; the names are not.
    """

    names: set[str] = set()
    for row in fixtures["fixtures"]:
        if row["kind"] != "declaration":
            continue
        if row["expected_verdict"] != SL.VERDICT_ADMITTED:
            continue
        parsed = SL.parse_declaration(_rest(row["line"]))
        if parsed is not None:
            names.add(parsed.symbol_name)
    for mutant in fixtures["b12_round_trip"]["mutants"]:
        if mutant.get("expected_resolved_key"):
            names.add(mutant["expected_resolved_key"])
    return sorted(names)


def _sweep_repository(names: list[str], skip: tuple[str, ...]) -> tuple[list[str], list[str]]:
    """A second implementation of the SWEEP — not of what counts as the tree.

    The sweep logic and the name derivation are written independently here,
    which is the part a second opinion is worth having. What is deliberately
    NOT re-derived is which paths the repository consists of: both programs
    ask `write_stage` (the shipped, public definition the B4 digest itself
    uses), because two hand-rolled copies of an exclusion rule disagreeing
    would produce a red about the checkers rather than about the run.
    """

    folded = [name.casefold() for name in names]
    hits: list[str] = []
    unreadable: list[str] = []
    for relative in sorted(write_stage.working_tree_file_digests(REPO)):
        if relative in skip:
            continue
        try:
            text = (REPO / relative).read_text(encoding="utf-8", errors="ignore").casefold()
        except OSError:  # pragma: no cover
            unreadable.append(relative)
            continue
        if any(name in text for name in folded):
            hits.append(relative)
    return hits, unreadable


def check_b5_resweep(
    verdicts: dict,
    receipts: dict,
    fixtures: dict,
    verdicts_path: Path,
    receipts_path: Path,
    failures: Failures,
    whole_repository: bool = True,
) -> None:
    """The committed outputs, swept for admitted names by a second program."""

    before = len(failures)
    names = admitted_names_from_the_seal(fixtures)
    folded = [name.casefold() for name in names]
    b5 = (verdicts.get("construction_gate") or {}).get("B5") or {}
    if b5.get("admitted_symbol_names_swept_for") != len(names):
        failures.add(
            "b5-name-count",
            f"B5 swept for {b5.get('admitted_symbol_names_swept_for')} admitted "
            f"names; the sealed corpus yields {len(names)}",
        )
    leaked = []
    for path in (verdicts_path, receipts_path):
        text = path.read_text(encoding="utf-8", errors="ignore").casefold()
        if any(name in text for name in folded):
            leaked.append(path.name)
    if leaked:
        failures.add(
            "b5-leak",
            f"{len(leaked)} committed output(s) contain an admitted symbol name: "
            f"{leaked}. The gate's own evidence is inside the swept tree",
        )
    # Only the UNDER-reporting direction is a failure. A run that honestly
    # records more hits than the two committed outputs carry is reporting hits
    # in paths that appeared during it, which is a red B5 truthfully told; a
    # run that records fewer than the bytes show is the artifact lying about
    # its own evidence, and that is what this catches.
    reported = b5.get("documents_containing_an_admitted_name")
    if not isinstance(reported, int) or reported < len(leaked):
        failures.add(
            "b5-underreported",
            f"B5 records {reported!r} document(s) containing an admitted name "
            f"and the committed bytes carry at least {len(leaked)}",
        )
    if not whole_repository:
        if len(failures) == before:
            print(f"  B5 re-sweep OK: {len(names)} names derived from the seal, "
                  f"0 hits in the two committed outputs (repository sweep skipped)")
        return

    disclosure = b5.get("whole_repository_sweep_disclosure") or {}
    recomputed, unreadable = _sweep_repository(
        names, skip=(gates.RUN_OUT, gates.RECEIPTS_OUT)
    )
    if unreadable:
        failures.add(
            "b5-unreadable",
            f"{len(unreadable)} file(s) could not be read on the re-sweep, so "
            f"this check covers less than it claims: {unreadable[:5]}",
        )
    if sorted(disclosure.get("files_that_could_not_be_read") or []) != sorted(unreadable):
        failures.add(
            "b5-unreadable",
            "the artifact and the re-sweep disagree about which files could "
            "not be read",
        )
    if disclosure.get("hits") != len(recomputed):
        failures.add(
            "b5-disclosure-count",
            f"the artifact discloses {disclosure.get('hits')} pre-existing "
            f"file(s) containing an admitted name; a second sweep finds "
            f"{len(recomputed)}",
        )
    if sorted(disclosure.get("paths") or []) != sorted(recomputed):
        only_artifact = sorted(set(disclosure.get("paths") or []) - set(recomputed))
        only_here = sorted(set(recomputed) - set(disclosure.get("paths") or []))
        failures.add(
            "b5-disclosure-paths",
            f"the disclosed path list differs from a second sweep: "
            f"artifact-only {only_artifact[:5]}, sweep-only {only_here[:5]}",
        )
    if not disclosure.get("all_hits_existed_before_the_run"):
        failures.add(
            "b5-disclosure-pre-existing",
            f"the artifact reports files containing an admitted name that did "
            f"not exist before the run: "
            f"{disclosure.get('hits_that_did_not_exist_before_the_run')}",
        )
    if len(failures) == before:
        print(
            f"  B5 re-sweep OK: {len(names)} names derived from the seal, 0 hits "
            f"in the two committed outputs, {len(recomputed)} pre-existing "
            f"repository file(s) as disclosed"
        )


# --------------------------------------------------------------------------
# the replay
# --------------------------------------------------------------------------


def json_diff(left: Any, right: Any, path: tuple = ()) -> list[tuple]:
    """Every leaf path at which two documents differ."""

    if isinstance(left, dict) and isinstance(right, dict):
        out: list[tuple] = []
        for key in sorted(set(left) | set(right)):
            if key not in left or key not in right:
                out.append(path + (key,))
            else:
                out.extend(json_diff(left[key], right[key], path + (key,)))
        return out
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return [path]
        out = []
        for index, (a, b) in enumerate(zip(left, right)):
            out.extend(json_diff(a, b, path + (index,)))
        return out
    return [] if left == right else [path]


def check_replay(
    verdicts: dict,
    receipts: dict,
    failures: Failures,
    allow_dirty: bool = False,
) -> None:
    """Re-run the runner and compare bytes, masking only tip-dependent fields."""

    masked = list(TIP_DEPENDENT) + (list(DIRTY_DEPENDENT) if allow_dirty else [])
    with tempfile.TemporaryDirectory(prefix="house-rules-replay-") as tmp:
        out = Path(tmp) / "verdicts.json"
        receipts_out = Path(tmp) / "receipts.json"
        argv = [
            sys.executable,
            str(RUNNER),
            "--out",
            str(out),
            "--receipts-out",
            str(receipts_out),
        ]
        if allow_dirty:
            argv.append("--allow-dirty")
        completed = subprocess.run(
            argv, capture_output=True, text=True, encoding="utf-8", cwd=str(REPO)
        )
        if not out.exists() or not receipts_out.exists():
            failures.add(
                "replay-refused",
                f"the runner exited {completed.returncode} without writing: "
                f"{(completed.stderr or '').strip()[:300]}. A replay wants a CLEAN "
                f"tree at the same tip; --replay-allow-dirty is the rehearsal hatch",
            )
            return
        replayed_verdicts = json.loads(out.read_text(encoding="utf-8"))
        replayed_receipts = json.loads(receipts_out.read_text(encoding="utf-8"))

    receipt_diffs = json_diff(receipts, replayed_receipts)
    if receipt_diffs:
        failures.add(
            "replay-receipts",
            f"the replayed receipts differ from the committed ones at "
            f"{len(receipt_diffs)} path(s): {[list(p) for p in receipt_diffs[:5]]}",
        )
    else:
        print("  replay OK: the receipts artifact is byte-identical")

    diffs = json_diff(verdicts, replayed_verdicts)
    unexpected = [
        path
        for path in diffs
        if not any(path[: len(mask)] == mask for mask in masked)
    ]
    if unexpected:
        failures.add(
            "replay-bytes",
            f"the replayed verdicts differ outside the declared tip-dependent "
            f"fields at {len(unexpected)} path(s): "
            f"{[list(p) for p in unexpected[:8]]}",
        )

    # Every masked difference is checked against the tree rather than waved
    # through: the head the replay saw and the digest it took must be the ones
    # this checker computes for the tree it is standing in.
    moved = [path for path in diffs if path not in unexpected]
    head = _git("rev-parse", "HEAD")
    replay_head = (replayed_verdicts.get("scoring_tree") or {}).get("head_commit")
    if replay_head != head:
        failures.add(
            "replay-head",
            f"the replay recorded head {replay_head}; git rev-parse HEAD is {head}",
        )
    digest = write_stage.working_tree_digest(REPO)
    b4 = (replayed_verdicts.get("construction_gate") or {}).get("B4") or {}
    if b4.get("working_tree_digest_before") != digest:
        failures.add(
            "replay-digest",
            "the replay's pre-run working-tree digest is not the digest this "
            "checker computes for the same tree",
        )
    if not unexpected:
        print(
            f"  replay OK: the verdicts artifact is byte-identical outside "
            f"{len(moved)} declared tip-dependent field(s), each re-derived from "
            f"the current tree"
            + (" (REHEARSAL: --replay-allow-dirty widened the mask)" if allow_dirty else "")
        )


# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verdicts", type=Path, default=VERDICTS)
    parser.add_argument("--receipts", type=Path, default=RECEIPTS)
    parser.add_argument("--prereg", type=Path, default=PREREG)
    parser.add_argument("--fixtures", type=Path, default=FIXTURES)
    parser.add_argument(
        "--replay",
        action="store_true",
        help="re-run the gates runner and compare bytes (wants a clean tree)",
    )
    parser.add_argument(
        "--replay-allow-dirty",
        action="store_true",
        help="rehearsal only: replay on a dirty tree, masking the tree-state fields",
    )
    parser.add_argument(
        "--no-repository-sweep",
        action="store_true",
        help="skip B5's whole-repository disclosure re-sweep (the slow leg)",
    )
    args = parser.parse_args(argv)

    print("house rules receipt check (DESIGN-house-rules §7 B10, §6.3)")
    failures = Failures()

    prereg = load_json(args.prereg, "prereg", failures)
    fixtures = load_json(args.fixtures, "fixtures", failures)
    verdicts = load_json(args.verdicts, "verdicts", failures)
    receipts = load_json(args.receipts, "receipts", failures)
    if prereg is None or fixtures is None or verdicts is None or receipts is None:
        print(f"house rules receipt check: FAILED ({len(failures)} named failure(s))")
        return 1

    check_shape(verdicts, receipts, prereg, failures)
    check_no_clock(verdicts, "verdicts", failures)
    check_no_clock(receipts, "receipts", failures)
    check_prereg_binding(verdicts, receipts, prereg, args.prereg, failures)
    check_frozen_pins(prereg, failures)
    check_provenance(verdicts, "verdicts", failures)
    check_provenance(receipts, "receipts", failures)
    check_ancestry(verdicts, prereg, failures)
    check_verdict_table(verdicts, prereg, failures)
    check_result_gates(verdicts, prereg, failures)
    check_b9(verdicts, receipts, prereg, fixtures, failures)
    check_receipts(verdicts, receipts, fixtures, failures)
    check_clause_order(verdicts, receipts, fixtures, failures)
    check_b5_resweep(
        verdicts,
        receipts,
        fixtures,
        args.verdicts,
        args.receipts,
        failures,
        whole_repository=not args.no_repository_sweep,
    )
    if args.replay or args.replay_allow_dirty:
        check_replay(verdicts, receipts, failures, allow_dirty=args.replay_allow_dirty)

    if failures:
        print(f"house rules receipt check: FAILED ({len(failures)} named failure(s))")
        return 1
    print("house rules receipt check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
