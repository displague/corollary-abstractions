#!/usr/bin/env python3
"""W0 — the WITNESS fragment census, committed before any manifest exists.

`docs/DESIGN-witnessed-conformance.md` §4. The course receipt's draft named
the fragment as *"quantified linear arithmetic over Z and Q (decidable)"* and
proposed a **60-name manifest**. The design's own indicative walk said that
fragment is close to empty against this repository's committed compiler, and
turned the walk into a construction prerequisite rather than a footnote:

> **If the census admits fewer than 70 candidates the 60-name manifest is
> withdrawn and the number is set from the census.** A manifest that consumes
> its population is the construction defect §4.0(3) exists to catch.

**This writer is the executable predicate, and its digest is the seal.** B1
requires the manifest to be sealed first, and a manifest is only as sealed as
the rule that chose its names. `selection_predicate_hash` is the sha256 of
THIS FILE, so a predicate edited after the census is a predicate a reader can
catch.

**What linear means here, decided before the count was read.** A term is
linear when every variable occurs at degree at most one, no two variables are
multiplied, no variable sits under `inv` (division BY a variable is not
linear), and no variable sits in an exponent. Guards are held to the same
standard: a linear conclusion under a quadratic guard is not a statement of
linear arithmetic. Each rejection records the FIRST reason it tripped on,
and `docs/ROADMAP-v0.21.md` §3.4's first-blocker-bias note applies to that
column exactly as it applies to ATLAS: a statement rejected for one reason
may well have carried three.

**The census decides no verdict and seals no manifest.** It counts, it
partitions by carrier, and it publishes what the draft's numbers do against
what the tree actually holds. What follows from the count is a **dated
amendment**, written before anything is sealed — never a quiet reread.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import conform  # noqa: E402
import conform_census as census  # noqa: E402
import conform_domain  # noqa: E402
import witness_obligation  # noqa: E402

ARTIFACT = "experiments/witness_fragment_census.json"

#: The draft's proposals, quoted so the census reads against them rather than
#: replacing them silently.
DRAFT_TARGETS = 60
DRAFT_DECOYS = 10
DRAFT_FRAGMENT = "quantified linear arithmetic over Z and Q (decidable)"

#: §4's withdraw-and-reset threshold, frozen in the design before this ran.
WITHDRAW_BELOW = 70


class NotLinear(Exception):
    """Carries the FIRST reason a term left the fragment, and a detail."""

    def __init__(self, reason: str, detail: str = "") -> None:
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


def has_slot(node) -> bool:
    if node[0] == "slot":
        return True
    if node[0] == "num":
        return False
    return any(has_slot(a) for a in node[2])


def check_linear(node) -> None:
    """Raise `NotLinear` with the first reason, or return.

    Mirrors the shape of `conform.eval_under_domain`'s walk so the two read
    the same term the same way — the parser spells `a - b` as `+(a, neg(b))`
    and `a / b` as `*(a, inv(b))`, and a predicate that forgot that would
    admit `a / b` as linear because it never saw a division node.
    """

    kind = node[0]
    if kind == "slot":
        return
    if kind == "num":
        # ADDED 2026-08-26, after the first walk: a literal that is not a
        # non-negative integer cannot appear in a `Nat` obligation, and the
        # first version of this predicate admitted three statements the
        # obligation builder then could not render (`literal 5/2 is not a
        # Nat`). A predicate that admits what the builder refuses is a
        # predicate that has not been executed, so the clause is here and
        # the correction is disclosed in the artifact rather than folded in.
        #
        # Worth saying plainly, because it is a fact about the evaluator and
        # not only about this fragment: `conform.in_carrier` tests sampled
        # VALUES against the carrier and says nothing about LITERALS, so the
        # committed evaluator does compute `2.5 * x` over a `Nat`-declared
        # row, as an exact rational. That is outside what a Nat obligation
        # can state, and it is outside this slice.
        value = Fraction(str(node[1]))
        if value.denominator != 1 or value < 0:
            raise NotLinear(
                "a literal outside the declared Nat carrier",
                f"literal={value}")
        return
    if kind == "call":
        raise NotLinear(f"call head {node[1]!r} is outside the evaluator")
    if kind != "op":
        raise NotLinear(f"node kind {kind!r} is outside the fragment")

    op = node[1]
    if op in {"+", "neg"}:
        for arg in node[2]:
            check_linear(arg)
        return
    if op == "*":
        numerators, denominators = conform._split_division(node[2])
        for arg in denominators:
            if has_slot(arg):
                raise NotLinear("division BY a variable is not linear")
            check_linear(arg)
        with_slots = [a for a in numerators if has_slot(a)]
        if len(with_slots) > 1:
            raise NotLinear("two variables multiplied together")
        for arg in numerators:
            check_linear(arg)
        return
    if op == "inv":
        if has_slot(node[2][0]):
            raise NotLinear("a variable under `inv` is not linear")
        return
    if op == "^":
        base, exponent = node[2]
        if has_slot(exponent):
            raise NotLinear("a variable in an exponent is not linear")
        if exponent[0] != "num":
            raise NotLinear("a computed exponent is outside the fragment")
        power = str(exponent[1])
        if has_slot(base) and power not in {"1", "1.0"}:
            # ONE bucket, not one bucket per exponent. A first version wrote
            # the power into the reason string and produced a rejection table
            # with a separate row for `power 1006`, which is a histogram of
            # the corpus's exponents wearing a diagnosis's clothes. The
            # exponents are tallied separately, where they are a fact about
            # the corpus rather than a reason.
            raise NotLinear("a variable raised to a power > 1",
                            f"power={power}")
        check_linear(base)
        return
    raise NotLinear(f"operator {op!r} is outside the fragment")


def classify_statement(node: dict, row, schema) -> dict:
    """One statement against the fragment predicate. Never raises."""

    statement_id = row.statement_id
    out = {"statement_id": statement_id, "corpus": row.corpus}
    try:
        program = conform.compile_statement(node, row, schema)
    except conform.Refusal as exc:
        out.update(in_fragment=False, reason=f"does not compile: {exc.construct}")
        return out
    out["carrier"] = program.carrier
    out["division"] = program.division
    out["subtraction"] = program.subtraction
    if not program.variables:
        out.update(in_fragment=False,
                   reason="ground: no quantifier, decided by E1 not by a lemma")
        return out
    out["variables"] = list(program.variables)
    try:
        check_linear(program.conclusion[2][0])
        check_linear(program.conclusion[2][1])
        for conjunct in program.guard_conjuncts:
            check_linear(conjunct[2][0])
            check_linear(conjunct[2][1])
    except NotLinear as exc:
        out.update(in_fragment=False, reason=exc.reason)
        if exc.detail:
            out["reason_detail"] = exc.detail
        return out
    # THE PREDICATE ASKS THE BUILDER, and this is not belt-and-braces.
    # Two earlier versions of this walk admitted statements the obligation
    # builder then refused — a non-Nat literal, and a unary negation outside
    # a `+` node — and each was found by running the builder over the
    # admitted set rather than by reading the predicate. A selection
    # predicate that has never been executed against the thing it selects
    # FOR is a rule, not a predicate. So membership is now: the linearity
    # walk passes AND both readings render. The digest below covers both
    # files for the same reason.
    try:
        witness_obligation.build(program)
    except witness_obligation.Unbuildable as exc:
        out.update(in_fragment=False,
                   reason=f"the obligation builder refuses: {exc}")
        return out
    out.update(in_fragment=True, relation=program.conclusion[1],
               guard_conjuncts=len(program.guard_conjuncts))
    return out


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def walk() -> list[dict]:
    schema = conform_domain.load()
    relations = census.evaluator_relations()
    rows = []
    for path in census.corpora():
        document = json.loads(path.read_text(encoding="utf-8"))
        corpus = document.get("corpus_id", path.parent.name)
        for node in document.get("statement_nodes", []):
            classified = census.classify(
                node, corpus, relations, schema.output_roles)
            rows.append(classify_statement(node, classified, schema))
    return rows


def build() -> dict:
    rows = walk()
    admitted = [r for r in rows if r["in_fragment"]]
    by_carrier: dict[str, int] = {}
    for row in admitted:
        by_carrier[row["carrier"]] = by_carrier.get(row["carrier"], 0) + 1
    rejection_reasons: dict[str, int] = {}
    exponents: dict[str, int] = {}
    for row in rows:
        if row["in_fragment"]:
            continue
        rejection_reasons[row["reason"]] = rejection_reasons.get(
            row["reason"], 0) + 1
        detail = row.get("reason_detail", "")
        if detail.startswith("power="):
            key = detail.split("=", 1)[1]
            exponents[key] = exponents.get(key, 0) + 1

    # DECOYS: compiled, quantified, and OUT of the fragment. Drawn by a
    # committed rule — sorted by statement_id, first ten — rather than chosen,
    # so a reader can recompute the list from this file.
    decoy_pool = sorted(
        r["statement_id"] for r in rows
        if not r["in_fragment"] and r.get("variables")
    )

    population = len(admitted)
    withdraw = population < WITHDRAW_BELOW
    carriers = sorted(by_carrier)
    fragment_is_nat_only = carriers == ["Nat"]

    return {
        "census_id": "witness.fragment.census.v1",
        "registered": "2026-08-26",
        "design": "docs/DESIGN-witnessed-conformance.md §4 (W0)",
        "roadmap": "docs/ROADMAP-v0.21.md §2",
        "writer": "scripts/witness_fragment_census.py",
        "selection_predicate": (
            "compiles under conform.compile_statement AND has at least one "
            "free variable AND every literal is a non-negative integer AND "
            "both sides of the conclusion are linear AND every guard "
            "conjunct is linear AND witness_obligation.build renders both "
            "readings, where linear means: no variable at degree > 1, no two "
            "variables multiplied, no variable under `inv`, no variable in "
            "an exponent."
        ),
        "selection_predicate_hash": _sha256_lf(Path(__file__)),
        "obligation_builder_hash": _sha256_lf(
            REPO / "scripts" / "witness_obligation.py"),
        "selection_predicate_hash_is": (
            "the sha256 of scripts/witness_fragment_census.py, LF-normalised, "
            "and `obligation_builder_hash` is the same for "
            "scripts/witness_obligation.py — BOTH, because the predicate's "
            "last clause is a call into the builder. B1 seals the manifest "
            "first, and a manifest is only as sealed as the rule that chose "
            "its names."
        ),
        "commit": _git("rev-parse", "HEAD"),
        "statements_walked": len(rows),
        "candidate_population": population,
        "candidates": sorted(r["statement_id"] for r in admitted),
        "by_carrier": dict(sorted(by_carrier.items())),
        "rejection_reasons_first_blocker_only": dict(
            sorted(rejection_reasons.items(), key=lambda kv: -kv[1])),
        "exponents_that_kept_a_statement_out": dict(
            sorted(exponents.items(),
                   key=lambda kv: (-kv[1], kv[0]))),
        "the_predicate_was_corrected_three_times_before_it_was_sealed": (
            "DISCLOSED rather than folded in, and the shape of the mistake "
            "is worth more than the numbers. (1) 2026-08-25: the first walk "
            "admitted 45 and the obligation builder then refused three of "
            "them (`literal 5/2 is not a Nat`); a literal clause was added. "
            "(2) The next walk admitted 42 and the builder refused more "
            "(`unary negation has no value in Nat`, from a `-3 * x` shape), "
            "so the final clause became a CALL INTO THE BUILDER and the "
            "mismatch class was closed rather than patched twice — 38. "
            "(3) 2026-08-25, from delta review: the builder was itself "
            "wrong. It rendered GUARD conjuncts without checking that their "
            "slots are bound by the binder, and `lean_workbook_10679`'s "
            "guard names `c` while the sampler binds only `a` and `b`. Lean "
            "auto-bound the free `c` as an implicit and accepted a "
            "STRICTLY STRONGER proposition than the row it was filed under, "
            "with exit 0 and no diagnostic. The builder now refuses an "
            "unbound slot as a typed refusal, every probe runs under "
            "`set_option autoImplicit false`, and the population is 37. "
            "Every correction landed BEFORE any manifest was sealed and "
            "before any obligation was discharged. Worth stating plainly, "
            "because it is a fact about the evaluator and not only about "
            "this fragment: `conform.in_carrier` tests sampled VALUES "
            "against the carrier and says nothing about LITERALS, so the "
            "committed evaluator does compute `2.5 * x` over a Nat-declared "
            "row, as an exact rational."
        ),
        "exponents_are_a_fact_about_the_corpus_not_a_reason": (
            "Tallied apart from the rejection table on purpose: `power=2` "
            "and `power=1006` are the same rejection and a table that split "
            "them would report the corpus's exponent distribution as if it "
            "were a diagnosis."
        ),
        "first_blocker_bias": (
            "Each rejected statement records the FIRST reason it tripped on, "
            "so a statement rejected for one reason may well have carried "
            "three. ROADMAP-v0.21 §3.4 files this as ATLAS's carried "
            "residual; the same caveat governs this column and no reason's "
            "count is a measure of how much work that reason does."
        ),
        "decoy_pool_size": len(decoy_pool),
        "decoys_drawn": decoy_pool[:DRAFT_DECOYS],
        "decoy_rule": (
            "compiled, quantified, and OUT of the fragment; sorted by "
            "statement_id, first ten. A rule a reader can recompute rather "
            "than a list a writer chose."
        ),
        "against_the_draft": {
            "draft_fragment": DRAFT_FRAGMENT,
            "draft_targets": DRAFT_TARGETS,
            "draft_decoys": DRAFT_DECOYS,
            "carriers_actually_declared": carriers,
            "the_fragment_names_Z_and_Q_and_the_tree_declares_neither": (
                fragment_is_nat_only
            ),
            "what_that_means": (
                "The draft's fragment is quantified linear arithmetic over Z "
                "and Q. Every admitted statement declares carrier `Nat` with "
                "`truncating` division and `truncated-at-zero` subtraction, "
                "which are not the integers' operations. An obligation "
                "quantified over Z and discharged about a Nat-declared "
                "statement adjudicates a different statement, so the "
                "fragment's WORDING is amended rather than reread: WITNESS's "
                "fragment is quantified linear arithmetic over the DECLARED "
                "Nat domain."
                if fragment_is_nat_only else
                "The tree declares more than one carrier; the fragment "
                "wording stands and the per-carrier split is above."
            ),
        },
        "the_withdraw_and_reset_rule": {
            "rule_as_frozen_in_the_design": (
                "If the census admits fewer than 70 candidates the 60-name "
                "manifest is withdrawn and the number is set from the census."
            ),
            "threshold": WITHDRAW_BELOW,
            "population": population,
            "fires": withdraw,
            "verdict": (
                f"WITHDRAWN — {population} candidates is below {WITHDRAW_BELOW}"
                if withdraw else
                f"STANDS — {population} candidates is at or above "
                f"{WITHDRAW_BELOW}"
            ),
            "what_happens_next": (
                "The manifest size is reset by a DATED AMENDMENT written "
                "BEFORE anything is sealed. This artifact does not seal a "
                "manifest and does not choose a number; it publishes the "
                "population that any number has to answer to."
            ),
        },
        "non_claims": [
            "This artifact seals no manifest, builds no obligation and "
            "discharges no lemma. It counts.",
            "The predicate is this repository's reading of `linear`, frozen "
            "before the count was read and digested above. It is not a claim "
            "that the wider literature would draw the boundary here.",
            "A statement being IN the fragment says nothing about whether its "
            "obligation will discharge. That is W1's question.",
            "No conformance rate, and nothing here touches "
            "experiments/conformance_run.json, which stays void.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=ARTIFACT)
    args = parser.parse_args(argv)

    record = build()
    out = REPO / args.out
    out.write_text(
        json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"candidates: {record['candidate_population']} "
          f"({record['by_carrier']})")
    print(f"withdraw rule: {record['the_withdraw_and_reset_rule']['verdict']}")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
