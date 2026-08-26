#!/usr/bin/env python3
"""The C-E3 supplementary run: the 25 sampled counterexamples, closed and decided.

`docs/ROADMAP-v0.21.md` §2's **named early rider**, permitted by §4.0(1)'s
bug-not-result clause. v0.20's C-E3 control **never executed** on the sampled
class: `scripts/measure_conformance.py:709-717` built its adjudication list
out of each record's raw `formal_statement.canonical_ascii` and `:464` handed
that raw text straight to `_lean_decide`, so a universally quantified
statement reached the checker with its free variables **unbound**. Lean failed
at elaboration with an unknown identifier long before `decide` was reached,
and all 25 sampled rows recorded `decide did not reduce in either direction` —
a label for `returncode != 0`, not a decision procedure meeting its boundary.
The dead `_lean_expression` at `:434-438` (guarded by a literal `if False`)
and the discarded `typed` at `:463` are the committed fossils of the dropped
substitution step, and they stay where they are: they are the evidence.

**This is a NEW writer and `measure_conformance.py` is byte-frozen.** The
registered run's writer is the record of what ran, and a supplementary run
that edited it would destroy the thing it is supplementing. Nothing here
reads, writes or re-scores `experiments/conformance_run.json`; it is opened
read-only and its digest is recorded.

**What this run can and cannot do**, stated before the first line of output.
It answers the question the gap withheld: *do the evaluator and the pinned
checker agree, at the exact point the record printed, on the exact
proposition the record claims fails there?* It **cannot un-void** v0.20's
conformance run, cannot restore `NO_COUNTEREXAMPLE_FOUND` to meaning anything
universal, and makes no claim about the 750 counterexamples outside C-E3's
committed 40-row limit. Agreement strengthens the credibility of the
provisional NONCONFORMANT labels **on the rows examined**; a refutation is an
evaluator-versus-checker disagreement and is **filed** — as the first
mechanically-confirmed candidate corpus-or-compiler error — **not fixed
here**.

**Substitution is structural, never textual.** The bindings are substituted
into the **parsed tree** at the `slot` nodes `conform.py` itself binds, so a
statement carrying both `x` and `x1` cannot have its `x1` corrupted by a
substitution for `x`. A textual rewrite is what a reader would assume from
the phrase "substitute the bindings", and it is wrong for exactly the class
of statement this corpus is full of.

**The rendering is the declared domain, not a translation of it.** Over the
`Nat` carrier with `division: truncating` and `subtraction: truncated-at-zero`
— the domain every one of these rows declares — Lean's own `Nat` operations
*are* the declared readings: `-` truncates at zero and `/` floors. The
rendered proposition is ascribed `: Nat` on both sides so nothing defaults,
and where a domain row's readings and the carrier's Lean semantics do NOT
coincide (`Int` under `truncating`: Python floors, `Int.div` truncates toward
zero; `Rat` at all, per the design's Correction 7) this writer **refuses to
present** rather than presenting a proposition the schema did not declare.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import conform  # noqa: E402
import conform_census as census  # noqa: E402
import external_verifier as verifier  # noqa: E402

RUN = "experiments/conformance_run.json"
PREREG = "experiments/conformance_prereg.json"
ARTIFACT = "experiments/conformance_ce3_supplement.json"
TOOLCHAIN_PIN = "prover/lean/normalizer/lean-toolchain"

CONFIRMED = "confirmed_counterexample"
REFUTED = "refuted_counterexample"
DID_NOT_REDUCE = "did_not_reduce"
NOT_PRESENTED = "not_presented"

#: The verdict's own closed table, keyed the way §3.4 keys `certifies`: the
#: sentence a reader sees is emitted by the code path that computed it.
MEANS = {
    CONFIRMED:
        "the pinned checker accepted the NEGATION of the substituted "
        "proposition: at this point the statement is false, and the run's "
        "counterexample is confirmed by an implementation that is not this "
        "repository's evaluator",
    REFUTED:
        "the pinned checker accepted the substituted proposition ITSELF: at "
        "this point the statement holds, and the evaluator and the checker "
        "disagree. This is filed as a candidate corpus-or-compiler error and "
        "is not repaired by this run",
    DID_NOT_REDUCE:
        "the checker accepted neither direction. This is a fact about the "
        "decision procedure on this term, not about the statement, and it "
        "adjudicates nothing either way",
    NOT_PRESENTED:
        "no closed proposition was built for this row, and the reason is "
        "printed. Nothing was handed to the checker, so nothing is claimed",
}

#: The honest non-claim, PER ROW, because DESIGN-statements-that-run's
#: Correction 7 requires it per counterexample rather than once per artifact:
#: *"A design that silently let the reachable half stand for the whole would
#: be doing the thing this control was added to prevent."* The registered
#: run's rows carry it for the rows the adjudicator could not reach; these
#: rows carry it for a different reason, and the difference is the point. An
#: adjudication that RAN still leaves the domain unadjudicated.
HONEST_NON_CLAIM = {
    CONFIRMED:
        "independent adjudication WAS available for this carrier and it "
        "agreed. What is still not claimed: the DOMAIN under which this point "
        "was drawn was declared by this repository, and the checker was "
        "handed that declaration rather than an independent reading of the "
        "Lean source statement. The standing correlated-interpretation label "
        "on this NONCONFORMANT verdict is untouched by this row",
    REFUTED:
        "independent adjudication WAS available for this carrier and it "
        "DISAGREED. This row is filed as a candidate corpus-or-compiler error "
        "and is not repaired here; no claim is made about which of the two "
        "implementations is wrong, and none about the domain either",
    DID_NOT_REDUCE:
        "no independent adjudication was available for this carrier; the "
        "verdict is this repository's arithmetic under this repository's "
        "schema",
    NOT_PRESENTED:
        "no independent adjudication was available for this carrier; the "
        "verdict is this repository's arithmetic under this repository's "
        "schema",
}


class Unpresentable(Exception):
    """No closed proposition can be built. Carries the reason, nothing else."""


# --------------------------------------------------------------------------
# Substitution — structural, at the slot nodes conform.py binds
# --------------------------------------------------------------------------


def substitute(tree, bindings: dict[str, str]):
    """Replace every `slot` with the record's binding. Refuses on a miss.

    `bindings` is the record's own `counterexample.bindings` map, whose keys
    are `Program.variables` — i.e. `Classified.sampled_variables`, the same
    names `conform_sampler` bound when the point was drawn. A slot outside
    that map is a slot the run never bound, and inventing a value for it
    would be manufacturing the point rather than reproducing it.
    """

    kind = tree[0]
    if kind == "num":
        return tree
    if kind == "slot":
        name = tree[1]
        if name not in bindings:
            raise Unpresentable(
                f"variable {name!r} has no binding in the record's "
                f"counterexample; the proposition would not be closed"
            )
        return ("num", str(bindings[name]))
    if kind in {"op", "rel", "call"}:
        return (kind, tree[1], tuple(substitute(a, bindings) for a in tree[2]))
    raise Unpresentable(f"unknown node kind {kind!r}")


def free_slots(tree) -> set[str]:
    kind = tree[0]
    if kind == "num":
        return set()
    if kind == "slot":
        return {tree[1]}
    out: set[str] = set()
    for arg in tree[2]:
        out |= free_slots(arg)
    return out


# --------------------------------------------------------------------------
# Rendering — the DECLARED domain, in the carrier's own Lean operations
# --------------------------------------------------------------------------

_RELATION_SYNTAX = {"=": "=", "<": "<", ">": ">", "<=": "<=", ">=": ">="}


def _check_domain(carrier: str, division: str, subtraction: str) -> None:
    """Where this writer will present, and where it refuses to.

    The refusals are the honest half of Correction 7 and are stated per
    domain rather than per row, because they are properties of the domain.
    """

    if carrier == "Nat":
        if division not in {"truncating", "exact"}:
            raise Unpresentable(f"undeclared division reading {division!r}")
        if subtraction not in {"truncated-at-zero", "signed"}:
            raise Unpresentable(f"undeclared subtraction reading {subtraction!r}")
        if division == "exact":
            raise Unpresentable(
                "an exact `/` over Nat has no Lean Nat counterpart; Lean's "
                "Nat division floors and would silently read a different "
                "operator than the schema declared"
            )
        if subtraction == "signed":
            raise Unpresentable(
                "a signed `-` over Nat has no Lean Nat counterpart; Lean's "
                "Nat subtraction truncates at zero"
            )
        return
    if carrier == "Int":
        if division == "truncating":
            raise Unpresentable(
                "Int under a truncating `/`: `conform.eval_under_domain` "
                "FLOORS (Python `//`) and Lean's `Int.div` truncates toward "
                "zero, so the two disagree on negative quotients. Presenting "
                "would be adjudicating a different statement"
            )
        if subtraction != "signed":
            raise Unpresentable(f"undeclared subtraction reading {subtraction!r}")
        return
    raise Unpresentable(
        f"carrier {carrier!r} is outside `decide`'s reach without Mathlib "
        f"(the design's Correction 7: core Lean's instDecidableEqRat gets "
        f"stuck without norm_num, and Mathlib is outside the hermetic budget)"
    )


def _literal(value) -> str:
    number = Fraction(str(value))
    if number.denominator != 1:
        raise Unpresentable(f"literal {number} is not in the carrier")
    if number < 0:
        raise Unpresentable(f"literal {number} is negative")
    return str(number.numerator)


def render(tree, carrier: str, division: str, subtraction: str) -> str:
    """A closed tree as a fully parenthesised Lean term over the carrier.

    The branch structure mirrors `conform.eval_under_domain` node for node,
    deliberately: the two are meant to compute the same value, and the way to
    keep them that way is to make the correspondence readable rather than
    argued. Every group is parenthesised, so Lean's precedence table never
    enters the reading.
    """

    kind = tree[0]
    if kind == "num":
        return _literal(tree[1])
    if kind == "slot":
        raise Unpresentable(f"slot {tree[1]!r} survived substitution")
    if kind == "call":
        raise Unpresentable(f"call head {tree[1]!r} is outside the evaluator")
    if kind != "op":
        raise Unpresentable(f"no rendering rule for {kind!r}")

    op = tree[1]
    if op == "+":
        # The parser spells `a - b` as `+(a, neg(b))`, so the split happens
        # here and not at a `-` node that does not exist. Over Nat this is
        # exactly Lean's truncated subtraction; over Int (signed) it is
        # exactly Lean's Int subtraction.
        positives, negatives = [], []
        for arg in tree[2]:
            if arg[0] == "op" and arg[1] == "neg":
                negatives.append(arg[2][0])
            else:
                positives.append(arg)
        head = " + ".join(
            render(a, carrier, division, subtraction) for a in positives
        ) or "0"
        if not negatives:
            return f"({head})"
        tail = " + ".join(
            render(a, carrier, division, subtraction) for a in negatives
        )
        return f"(({head}) - ({tail}))"
    if op == "*":
        numerators, denominators = conform._split_division(tree[2])
        product = " * ".join(
            render(a, carrier, division, subtraction) for a in numerators
        ) or "1"
        if not denominators:
            return f"({product})"
        divisor = " * ".join(
            render(a, carrier, division, subtraction) for a in denominators
        )
        return f"(({product}) / ({divisor}))"
    if op == "neg":
        inner = tree[2][0]
        if carrier == "Int":
            return f"(-({render(inner, carrier, division, subtraction)}))"
        # Over Nat, `eval_under_domain` REFUSES a unary negation of a positive
        # quantity rather than clamping it (the comment there records why:
        # clamping made a quarter of the ground class decide for a reason that
        # was not the statement's). A point that took that branch errored and
        # was never a counterexample, so this is unreachable from a recorded
        # row — and it refuses here rather than inventing `Nat`'s missing
        # negation.
        raise Unpresentable(
            "unary negation outside the carrier: Nat has no negation, and "
            "`conform.eval_under_domain` refuses this node rather than "
            "clamping it"
        )
    if op == "inv":
        inner = render(tree[2][0], carrier, division, subtraction)
        if division != "truncating":
            raise Unpresentable("a bare `inv` under an exact division is not "
                                "in the carrier")
        # DECLARED READING, quoted from `conform.py`: a bare `inv` under a
        # truncating division is `1 / inner` in the carrier's own division,
        # i.e. floor division, so `inv(4)` is 0.
        return f"(1 / {inner})"
    if op == "^":
        base = render(tree[2][0], carrier, division, subtraction)
        exponent = tree[2][1]
        if exponent[0] != "num":
            raise Unpresentable("only a literal exponent is rendered; a "
                                "computed exponent would need its own reading")
        return f"({base} ^ {_literal(exponent[1])})"
    raise Unpresentable(f"no rendering rule for operator {op!r}")


def render_proposition(tree, carrier: str, division: str,
                       subtraction: str) -> str:
    """The whole relation, with BOTH sides ascribed so nothing defaults.

    Without the ascription Lean's `OfNat` default instance would elaborate
    every literal at `Nat` whatever the schema declared — which is right for
    the `Nat` rows by accident and wrong for an `Int` row silently. An
    accident that happens to agree is not a reading.
    """

    _check_domain(carrier, division, subtraction)
    if tree[0] != "rel":
        raise Unpresentable("the conclusion is not a top-level relation")
    relation = tree[1]
    if relation not in _RELATION_SYNTAX:
        raise Unpresentable(f"relation {relation!r} has no rendering")
    left = render(tree[2][0], carrier, division, subtraction)
    right = render(tree[2][1], carrier, division, subtraction)
    return (f"(({left} : {carrier}) {_RELATION_SYNTAX[relation]} "
            f"({right} : {carrier}))")


# --------------------------------------------------------------------------
# The pinned checker, invoked by path
# --------------------------------------------------------------------------


def pinned_binary() -> Path:
    """The pinned toolchain's `lean`, or a refusal. NEVER downloads."""

    toolchain = (REPO / TOOLCHAIN_PIN).read_text(encoding="utf-8").strip()
    binary = verifier.toolchain_binary(toolchain)
    if binary is None:
        raise Unpresentable(
            f"toolchain {toolchain!r} is not installed; refusing to download "
            f"(the hermetic rule, docs/DESIGN-external-verifier.md)"
        )
    return binary


def _under_home(path: Path) -> str:
    """`~/...`, with forward slashes, or the plain path if it is elsewhere."""

    try:
        return "~/" + path.relative_to(Path.home()).as_posix()
    except (ValueError, RuntimeError):
        return path.as_posix()


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_lf(path: Path) -> str:
    return _sha256(path.read_bytes().replace(b"\r\n", b"\n"))


def _probe(source_text: str, binary: Path, timeout: int) -> dict:
    """One `lean` invocation on one file. Returns the receipt, never raises."""

    started = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "Probe.lean"
        source.write_text(source_text, encoding="utf-8")
        try:
            # BYTES, decoded as UTF-8 here rather than by the locale. Lean
            # writes `≥` and `¬` into its diagnostics; Python's `text=True`
            # decodes a subprocess pipe with the console codepage, which on
            # this machine turned `≥` into `â‰¥` inside a receipt whose whole
            # job is to be quotable.
            completed = subprocess.run(
                [str(binary), str(source)], cwd=tmp, capture_output=True,
                timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"accepted": False, "returncode": None,
                    "failure": type(exc).__name__,
                    "source_sha256": _sha256(source_text.encode("utf-8")),
                    "seconds": round(time.time() - started, 3)}
        raw = (completed.stdout + completed.stderr).decode("utf-8", "replace")
        # The temporary directory's name is random, and a random string in a
        # field a reader is told is deterministic is a reproduction that
        # cannot be checked. The probe's path is replaced by a stable name.
        output = raw.replace(str(source), "<probe>.lean").replace(
            str(source).replace("\\", "/"), "<probe>.lean").replace(
            str(tmp), "<probe-dir>").strip()
    return {
        "accepted": completed.returncode == 0,
        "returncode": completed.returncode,
        "source_sha256": _sha256(source_text.encode("utf-8")),
        "checker_output_head": output[:400],
        "seconds": round(time.time() - started, 3),
    }


def decide_both_directions(proposition: str, binary: Path,
                           timeout: int = 120) -> tuple[str, dict]:
    """`by decide` on the proposition and on its negation. Verdict + receipt.

    Both directions are run **always**, even when the first accepts, so the
    receipt records what the checker said about each and a reader can see that
    exactly one direction was accepted. A procedure that accepted both would
    be an inconsistent checker, and this writer would rather record that than
    short-circuit past it.
    """

    positive_source = f"example : ({proposition} : Prop) := by decide\n"
    negative_source = f"example : (¬({proposition}) : Prop) := by decide\n"
    positive = _probe(positive_source, binary, timeout)
    negative = _probe(negative_source, binary, timeout)
    receipt = {"positive_probe": positive, "negative_probe": negative,
               "pattern": "example : (<prop> : Prop) := by decide"}
    if positive["accepted"] and negative["accepted"]:
        receipt["both_accepted"] = (
            "THE CHECKER ACCEPTED A PROPOSITION AND ITS NEGATION. That is a "
            "statement about the checker, not the corpus, and this row "
            "adjudicates nothing."
        )
        return DID_NOT_REDUCE, receipt
    if positive["accepted"]:
        return REFUTED, receipt
    if negative["accepted"]:
        return CONFIRMED, receipt
    return DID_NOT_REDUCE, receipt


# --------------------------------------------------------------------------
# The run
# --------------------------------------------------------------------------


def sampled_rows(run: dict) -> list[dict]:
    """The C-E3 rows that belong to the SAMPLED class, with their bindings.

    Derived rather than indexed. `c_e3.adjudicated` is the ground class
    followed by the sampled class, and the committed run's sampled rows sit
    at indices 15-39 — but hard-coding 15 would make this writer depend on a
    count it does not compute. A row is sampled exactly when the run's own E2
    table carries a counterexample for it, and that table is where the
    bindings live.
    """

    counterexamples = {
        row["statement_id"]: row
        for row in run["e2"]["counterexamples_exhaustively"]
    }
    out = []
    for index, row in enumerate(run["c_e3"]["adjudicated"]):
        found = counterexamples.get(row["statement_id"])
        if found is None:
            continue
        out.append({"adjudicated_index": index,
                    "c_e3_row": row, "e2_row": found})
    return out


def corpus_nodes(statement_ids: set[str]) -> dict[str, dict]:
    nodes = {}
    for path in census.corpora():
        document = json.loads(path.read_text(encoding="utf-8"))
        for node in document.get("statement_nodes", []):
            if node.get("statement_id") in statement_ids:
                nodes[node["statement_id"]] = node
    return nodes


def adjudicate(entry: dict, node: dict, binary: Path, timeout: int) -> dict:
    """One row: substitute, render, decide, and recompute as a cross-check."""

    e2_row = entry["e2_row"]
    counterexample = e2_row["counterexample"]
    domain = e2_row["domain"]
    bindings = dict(counterexample["bindings"])
    ascii_text = (node.get("formal_statement") or {}).get("canonical_ascii", "")

    record = {
        "statement_id": e2_row["statement_id"],
        "adjudicated_index": entry["adjudicated_index"],
        "domain": domain,
        "bindings": bindings,
        "canonical_ascii": ascii_text,
        "run_recorded": {
            "verdict_in_the_run": "NONCONFORMANT",
            "left": counterexample.get("left"),
            "right": counterexample.get("right"),
            "relation": counterexample.get("relation"),
            "c_e3_said": entry["c_e3_row"].get("reason")
                         or entry["c_e3_row"].get("note"),
        },
    }

    tree = census.parse(ascii_text)
    if tree is None:
        record.update(decide_verdict=NOT_PRESENTED, means=MEANS[NOT_PRESENTED],
                      not_presented_because="the committed parser returns None")
        return record

    try:
        closed = substitute(tree, bindings)
        remaining = free_slots(closed)
        if remaining:
            raise Unpresentable(
                f"unbound after substitution: {sorted(remaining)}")
        proposition = render_proposition(
            closed, domain["carrier"], domain["division"],
            domain["subtraction"])
    except Unpresentable as exc:
        record.update(decide_verdict=NOT_PRESENTED, means=MEANS[NOT_PRESENTED],
                      honest_non_claim=HONEST_NON_CLAIM[NOT_PRESENTED],
                      not_presented_because=str(exc))
        return record

    record["substituted_proposition"] = proposition

    # The cross-check: does the SUBSTITUTED TREE reproduce the numbers the
    # run printed? If it does not, the substitution is wrong and the checker's
    # answer would be about a different point. This is checked before the
    # verdict is read and travels with it.
    try:
        left = conform.eval_under_domain(
            closed[2][0], {}, domain["carrier"], domain["division"],
            domain["subtraction"])
        right = conform.eval_under_domain(
            closed[2][1], {}, domain["carrier"], domain["division"],
            domain["subtraction"])
        holds = conform.decide_relation(closed[1], left, right)
        record["evaluator_recomputation"] = {
            "left": str(left), "right": str(right), "holds": holds,
            "reproduces_the_runs_numbers": (
                str(left) == str(counterexample.get("left"))
                and str(right) == str(counterexample.get("right"))
            ),
            "still_a_counterexample_under_the_evaluator": not holds,
        }
    except Exception as exc:  # noqa: BLE001 - recorded, never raised
        record["evaluator_recomputation"] = {
            "failed": f"{type(exc).__name__}: {str(exc)[:160]}"}

    # THE SAME POINT, READ OVER EXACT RATIONALS. Computed, never asserted.
    # The declared domain's `truncating` division and `truncated-at-zero`
    # subtraction are what make these points counterexamples; asking what the
    # same statement does at the same point under exact `/` and signed `-` is
    # the cheapest available separation of ARITHMETIC-implementation risk
    # from DOMAIN risk, and it costs one more evaluation per row.
    try:
        exact_left = conform.eval_under_domain(
            closed[2][0], {}, "Rat", "exact", "signed")
        exact_right = conform.eval_under_domain(
            closed[2][1], {}, "Rat", "exact", "signed")
        record["over_exact_rationals"] = {
            "left": str(exact_left), "right": str(exact_right),
            "holds": conform.decide_relation(closed[1], exact_left,
                                             exact_right),
            "this_is_not_the_declared_domain": (
                "carrier Rat, division exact, subtraction signed — NOT the "
                "domain the schema declared for this row and NOT what any "
                "verdict here is measured under. It is reported so a reader "
                "can see which risk the checker's agreement priced."
            ),
        }
    except Exception as exc:  # noqa: BLE001 - recorded, never raised
        record["over_exact_rationals"] = {
            "failed": f"{type(exc).__name__}: {str(exc)[:160]}"}

    verdict, receipt = decide_both_directions(proposition, binary, timeout)
    record["decide_verdict"] = verdict
    record["means"] = MEANS[verdict]
    record["honest_non_claim"] = HONEST_NON_CLAIM[verdict]
    record["checker_receipt"] = receipt
    return record


def build(timeout: int, limit: int | None = None) -> dict:
    run_path = REPO / RUN
    run = json.loads(run_path.read_text(encoding="utf-8"))
    entries = sampled_rows(run)
    if limit is not None:
        entries = entries[:limit]
    nodes = corpus_nodes({e["e2_row"]["statement_id"] for e in entries})

    binary = pinned_binary()
    toolchain = (REPO / TOOLCHAIN_PIN).read_text(encoding="utf-8").strip()

    rows = []
    for entry in entries:
        node = nodes.get(entry["e2_row"]["statement_id"], {})
        rows.append(adjudicate(entry, node, binary, timeout))

    tally: dict[str, int] = {}
    for row in rows:
        tally[row["decide_verdict"]] = tally.get(row["decide_verdict"], 0) + 1
    refuted = [r["statement_id"] for r in rows
               if r["decide_verdict"] == REFUTED]
    unreproduced = [
        r["statement_id"] for r in rows
        if not r.get("evaluator_recomputation", {}).get(
            "reproduces_the_runs_numbers", True)
    ]
    confirmed_rows = [r for r in rows if r["decide_verdict"] == CONFIRMED]
    exact_hold = [r["statement_id"] for r in confirmed_rows
                  if r.get("over_exact_rationals", {}).get("holds") is True]
    exact_fail = [r["statement_id"] for r in confirmed_rows
                  if r.get("over_exact_rationals", {}).get("holds") is False]
    exact_errored = [r["statement_id"] for r in confirmed_rows
                     if "holds" not in r.get("over_exact_rationals", {})]

    return {
        "supplement_id": "conformance.ce3.supplement.v1",
        "registered": "2026-08-26",
        "ordering": "RETROSPECTIVE",
        "ordering_disclosed": (
            "The gap this run closes was found by REVIEW AFTER the registered "
            "run was read, not before it. The prereg amendment naming this "
            "rider is dated 2026-08-26 and the run it supplements is dated "
            "2026-08-25. Nothing about that ordering is hidden by calling the "
            "amendment a preregistration: what is preregistered is the "
            "PROCEDURE and the reading rule — whatever the checker says is "
            "the answer — and both were fixed before this writer was run."
        ),
        "authority": (
            "docs/ROADMAP-v0.21.md §4.0(1), the bug-not-result clause: the "
            "no-chase rule governs controls that RAN and read unfavourably; "
            "C-E3 provably never executed on the sampled class, which is a "
            "bug. The precedent for the shape is foreign_voice_rate.json -> "
            "foreign_voice_rate2.json: own dated amendment, NEW artifact, "
            "original never edited or re-scored."
        ),
        "amends": f"{PREREG} -> amendments[] (the dated entry naming this rider)",
        "design": "docs/DESIGN-statements-that-run.md §7 (C-E3), Correction 7",
        "roadmap": "docs/ROADMAP-v0.21.md §2",
        "writer": "scripts/conformance_ce3_supplement.py",
        "measure_conformance_is_byte_frozen": (
            "scripts/measure_conformance.py is NOT edited by this rider. It "
            "is the record of what ran, including the dead `_lean_expression` "
            "at :434-438 and the discarded `typed` at :463 that are the "
            "evidence for the correction. A supplementary run that edited the "
            "writer it supplements would destroy its own subject."
        ),
        "commit": _git("rev-parse", "HEAD"),
        "checker": {
            "toolchain": toolchain,
            # HOME-RELATIVE, not absolute. The absolute path is a fact about
            # this machine's user account, and a reader on another machine
            # cannot reproduce it — which would put an irreproducible string
            # inside an artifact that tells them the rest reproduces. The
            # binary's IDENTITY is its digest, and that does reproduce.
            "binary": _under_home(binary),
            "binary_sha256": _sha256(binary.read_bytes()),
            "invocation": "the pinned binary by absolute path; no elan proxy, "
                          "no lake, no Mathlib, no network",
            "decision_procedure": "by decide, both directions, always both",
            "timeout_seconds": timeout,
        },
        "source": {
            "run_artifact": RUN,
            "run_artifact_sha256_lf": _sha256_lf(run_path),
            "run_artifact_is_read_only_here": True,
            "selection": (
                "every c_e3.adjudicated row whose statement_id carries a "
                "counterexample in e2.counterexamples_exhaustively — i.e. the "
                "SAMPLED class, derived rather than indexed. In the committed "
                "run these are indices 15-39."
            ),
            "rows_selected": len(rows),
            "of_the_runs_counterexamples": len(
                run["e2"]["counterexamples_exhaustively"]),
            "why_not_all_of_them": (
                "C-E3 ran under a committed 40-row limit and adjudicated the "
                "40 rows it reached. This supplement adjudicates exactly "
                "those rows again, correctly. The remaining counterexamples "
                "were never presented to any checker and this run does not "
                "present them: extending the sample would be a new "
                "measurement, not the repair of a gap."
            ),
        },
        "rows": rows,
        "aggregate": {
            "adjudicated": len(rows),
            "by_verdict": dict(sorted(tally.items())),
            "refuted_counterexamples": sorted(refuted),
            "rows_whose_substitution_did_not_reproduce_the_run": sorted(
                unreproduced),
            "rows_that_hold_over_exact_rationals": len(exact_hold),
            "rows_that_fail_over_exact_rationals": len(exact_fail),
            "rows_whose_exact_rational_reading_errored": len(exact_errored),
            "of_confirmed_rows": len(confirmed_rows),
            "what_the_agreement_therefore_PRICES": (
                f"{len(exact_hold)} of the {len(confirmed_rows)} confirmed "
                f"rows HOLD at the very same point when the same statement is "
                f"read over exact rationals with signed subtraction. So these "
                f"counterexamples are products of the DECLARED DOMAIN — "
                f"truncating `/`, truncated-at-zero `-` over Nat — and not of "
                f"the source statements. What the checker's agreement prices "
                f"is therefore ARITHMETIC-IMPLEMENTATION risk: two "
                f"independent implementations of the SAME declared arithmetic "
                f"(this repository's evaluator and Lean's Nat operations) "
                f"compute the same values and the same failures. It prices "
                f"NOTHING about whether that declared arithmetic is the right "
                f"reading of the Lean source statement. DOMAIN risk — the "
                f"standing correlated-interpretation label on every "
                f"NONCONFORMANT verdict — is untouched, and a reader who "
                f"takes 25/25 as evidence the corpus is wrong has read this "
                f"artifact backwards."
            ),
            "how_this_number_was_obtained": (
                "COMPUTED per row by conform.eval_under_domain under carrier "
                "Rat with exact division and signed subtraction, at the same "
                "bindings, and tallied here — not asserted, and not a floor. "
                "Either reading was publishable; this one is what the tree "
                "returned."
            ),
            "substitution_cross_check": (
                "Every presented row's substituted tree is re-evaluated by "
                "conform.eval_under_domain under the row's own declared "
                "domain and compared to the left/right values the registered "
                "run printed. A row that did not reproduce them would mean "
                "this writer substituted a different point, and its checker "
                "verdict would be about a statement nobody measured."
            ),
        },
        "could_this_have_gone_red": {
            "the_standing_review_question": (
                "ROADMAP-v0.21 §4's recurring catch of the cycle: a green "
                "assertion that could not have gone red is not evidence. This "
                "run read 25 of 25 confirmed — a clean sweep — and a clean "
                "sweep is exactly the shape that question exists to "
                "interrogate."
            ),
            "why_a_sweep_is_the_EXPECTED_reading_here": (
                "Unlike a gate, this rider has no floor and no voiding "
                "sentence: it asks whether two independent implementations of "
                "the SAME declared arithmetic agree at 25 specific points. If "
                "both are correct they agree, so agreement is the null result "
                "and disagreement would have been the finding. The content is "
                "not that the number is high; it is that Lean's Nat "
                "subtraction, Nat floor division and Nat comparison "
                "re-derive, from a term this repository never gave it before, "
                "the same 25 failures the evaluator printed."
            ),
            "the_refuted_path_is_demonstrably_reachable": (
                "tests/test_conform_ce3_supplement.py::"
                "TheRenderingMeansToLeanWhatItMeansToTheEvaluator drives this "
                "same `decide_both_directions` over seven fixtures, four of "
                "which HOLD at their point and therefore come back "
                "`refuted_counterexample`. The verdict this run did not "
                "produce is produced mechanically by the suite, on the same "
                "code path, against the same pinned binary. That is the "
                "difference between an instrument that did not go red and one "
                "that could not."
            ),
            "what_a_sweep_still_does_not_license": (
                "Nothing about the other 750 counterexamples, nothing about "
                "the declared domain's fidelity to the Lean source statement, "
                "and nothing that moves a voided control."
            ),
        },
        "corrections_to_this_writer_after_its_first_execution": {
            "disclosed_because_the_ordering_matters": (
                "The first execution read 25/25 confirmed. THREE DEFECTS IN "
                "THE RECEIPT — not in any verdict — were found by reading "
                "that output, fixed, and the run re-executed. All three are "
                "recorded here rather than quietly folded in."
            ),
            "the_probe_output_was_decoded_by_the_console_codepage": (
                "`subprocess.run(text=True)` decoded Lean's diagnostics with "
                "the locale encoding, so `≥` reached the receipt as `â‰¥`. The "
                "probe now captures bytes and decodes UTF-8 explicitly."
            ),
            "the_temporary_directorys_random_name_reached_the_artifact": (
                "Lean prefixes its diagnostics with the source path, and the "
                "source lived in a fresh `TemporaryDirectory`, so a random "
                "string sat inside a field this artifact tells a reader is "
                "deterministic. The path is now normalised to `<probe>.lean` "
                "and the artifact reproduces byte-for-byte apart from the "
                "wall-clock `seconds` fields."
            ),
            "the_checkers_absolute_path_named_this_machines_home_directory": (
                "`checker.binary` recorded `C:\\Users\\<user>\\.elan\\...`, a "
                "fact about one account, inside an artifact that tells a "
                "reader the rest of it reproduces. It is now recorded "
                "home-relative as `~/.elan/...`, with `binary_sha256` as the "
                "binary's actual identity."
            ),
            "no_verdict_moved": (
                "None of the three fixes touches substitution, rendering or "
                "the decision procedure. All 25 verdicts and both probe "
                "`source_sha256` values per row are identical before and "
                "after."
            ),
            "and_a_second_regeneration_after_adversarial_review": (
                "DATED 2026-08-26. Adversarial review found two things this "
                "artifact owed and one it could cheaply add: "
                "DESIGN-statements-that-run's Correction 7 requires the "
                "honest non-claim PER COUNTEREXAMPLE and these rows carried "
                "none (`honest_non_claim` is now on every row, keyed to the "
                "verdict by a closed table); and the exact-rational reading of "
                "each point was one evaluation away and separates "
                "arithmetic-implementation risk from domain risk (see the "
                "aggregate). The artifact was REGENERATED THROUGH THE WRITER "
                "rather than edited — this run is deterministic and §4.0(2) "
                "welcomes reproductions — and the regeneration moved exactly "
                "the intended fields plus `commit` and the wall-clock "
                "`seconds`. Every decide verdict and every probe digest is "
                "unchanged. This artifact never had a byte-reproduction proof "
                "at stake, which is what made regeneration the right repair "
                "here and the wrong one for foreign_voice_rate2."
            ),
        },
        "what_this_answers": {
            "the_question_the_gap_withheld": (
                "For each sampled counterexample: does the pinned checker, "
                "given the CLOSED proposition the record's own bindings "
                "produce, agree with the evaluator that the statement fails "
                "at that point?"
            ),
            "agreement": (
                "A confirmed_counterexample strengthens the credibility of "
                "that row's PROVISIONAL NONCONFORMANT label: the failure is "
                "reproduced by an implementation that is not this "
                "repository's evaluator. It does NOT make the label "
                "unconditional — the DOMAIN under which the point was drawn "
                "is still this repository's declaration, and the checker was "
                "handed that declaration rather than an independent reading "
                "of the source statement."
            ),
            "disagreement": (
                "A refuted_counterexample is an evaluator-versus-checker "
                "disagreement on a closed ground proposition, which is the "
                "first mechanically-confirmed candidate corpus-or-compiler "
                "error this project has produced. It is FILED here with its "
                "receipt and is NOT fixed by this run: repairing the "
                "evaluator or the corpus on the strength of a reading is the "
                "chase this project's rules exist to prevent."
            ),
            "did_not_reduce": (
                "The decision procedure did not settle the term. That is a "
                "fact about `decide` on this term — and, unlike the "
                "registered run's 25 identical rows, it is now a fact "
                "measured on a CLOSED proposition rather than an elaboration "
                "failure on an open one. Correction 7's carrier prediction "
                "becomes testable here for the first time."
            ),
        },
        "non_claims": [
            "This run does not un-void experiments/conformance_run.json. "
            "C-E1 missed its floor and C-E2 voided; both stand, and every "
            "NO_COUNTEREXAMPLE_FOUND in that run remains void.",
            "This run publishes no conformance rate, and agreement here is "
            "not evidence any statement is true — a counterexample decides "
            "and agreement at a point decides nothing.",
            "This run adjudicates the 25 rows C-E3 reached and says nothing "
            "about the other counterexamples in the registered run.",
            "The domain under which each point was drawn is this "
            "repository's declaration. An independent adjudication of the "
            "DOMAIN is not what this run is; that is WITNESS's problem.",
            "No verified_by link is created and nothing enters "
            "prover/verifier-verdicts/. A decided ground proposition at a "
            "sampled point is not a proof artifact.",
        ],
        "reproduction": {
            "how": "python scripts/conformance_ce3_supplement.py",
            "determinism": (
                "Deterministic given the pinned checker and the committed "
                "run artifact: the rows, the bindings and the rendered "
                "propositions are all functions of committed bytes, and "
                "`decide` is a decision procedure. Per ROADMAP-v0.21 §4.0(2) "
                "this artifact is committed from a deterministic runner and "
                "reproductions are welcome and recorded."
            ),
            "what_is_not_byte_identical": (
                "Two fields, named so a reader diffing two runs knows what to "
                "expect: the per-probe `seconds`, which are wall-clock and "
                "differ by construction, and `commit`, which records the HEAD "
                "the run happened on and cannot reproduce from a different "
                "one. Every other field is a function of the inputs."
            ),
        },
    }


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--out", default=ARTIFACT)
    args = parser.parse_args(argv)

    try:
        record = build(args.timeout, args.limit)
    except Unpresentable as exc:
        print(f"supplement refused: {exc}", file=sys.stderr)
        return 2

    out = REPO / args.out
    out.write_text(
        json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for row in record["rows"]:
        print(f"{row['statement_id']}: {row['decide_verdict']}")
    print(f"aggregate: {record['aggregate']['by_verdict']}")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
