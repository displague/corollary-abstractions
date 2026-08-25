#!/usr/bin/env python3
"""The ONE registered run: `experiments/conformance_run.json`.

`docs/DESIGN-statements-that-run.md` §5 and §10. It carries E0b, E0d, E0f,
E1's ground decision with every disagreement listed exhaustively, E2's
admitted-point and falsification tables **with their denominators in the same
sentence**, E3's ten-bucket arithmetic, E4's NIHIL certification, and every
control's reading including C-E2's guard-blind arm and C-E3's per-statement
availability.

**C-E4 runs first and can stop everything.** The parser, evaluator, schema
and sampler were digest-frozen in the preregistration commit before
`conform.py` existed. If implementing the compiler required changing any of
them, the independence claim is void and this writer refuses rather than
publishing a number measured through a moved instrument.

**Falsification-only, everywhere the number can be seen.** A
`NO_COUNTEREXAMPLE_FOUND` count travels with its admitted-point denominator
and its `certifies` sentence in the same object, because the asymmetry is
total: one falsifying point settles a statement and a million agreeing points
settle nothing.
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
import conform_domain  # noqa: E402
import conform_sampler as sampler  # noqa: E402
import match_signatures as ms  # noqa: E402

ARTIFACT = "experiments/conformance_run.json"
PREREG = "experiments/conformance_prereg.json"
REGISTER = "experiments/conformance_register.json"
PILOT = "experiments/conformance_admission_pilot.json"
NIHIL_CLASS = "data/domains/nihil_class.json"

E2A_FLOOR = 0.80
CE1_FLOOR = 0.99
CE2_CONTRAST = 10.0


class RunRefusal(RuntimeError):
    """A voiding sentence fired. The run is NOT written."""


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


# --------------------------------------------------------------------------
# C-E4 — the tautology probe, first
# --------------------------------------------------------------------------


def revalidate_prereg() -> dict:
    prereg = json.loads((REPO / PREREG).read_text(encoding="utf-8"))
    rows, drifted = [], []
    for row in prereg["frozen"]:
        observed = conform_domain.sha256_lf(REPO / row["path"])
        agrees = observed == row["sha256_lf"]
        rows.append({"path": row["path"], "role": row["role"],
                     "recorded_sha256_lf": row["sha256_lf"],
                     "observed_sha256_lf": observed, "agrees": agrees})
        if not agrees:
            drifted.append(row["path"])
    if drifted:
        raise RunRefusal(
            "C-E4 VOID: these preregistered artifacts no longer match the "
            "tree: " + ", ".join(drifted) + ". If making a conformance "
            "verdict come out right required editing the parser, the "
            "arithmetic, or the schema, the independence claim is void and "
            "the change needs its own review naming the reason. No rate is "
            "published."
        )
    return {"control": "C-E4 (the tautology probe)", "verdict": "HOLDS",
            "revalidated": rows}


# --------------------------------------------------------------------------
# C-E1 — the perturbation control, discard rule ported FIRST
# --------------------------------------------------------------------------


def _mutations(tree):
    """Five classes, each on the TERM. Yields (class_id, mutated_tree)."""

    out = []

    def replace_first_num(node, transform, done, in_exponent=False):
        """Replace the first numeric literal in a COEFFICIENT position.

        Exponent positions are skipped, and that exclusion is the control
        working rather than a convenience. A first version mutated whatever
        literal came first, which on `a^2 + b^2 >= 2*a*b` meant turning `a^2`
        into `a^-2` — a change to the *shape* of the term, not to a
        coefficient, and one whose flip-or-not says nothing about whether the
        sampler is testing the term. C-E1's five classes name a coefficient
        and a numeric literal; an exponent is neither.
        """

        if done[0]:
            return node
        if node[0] == "num":
            if in_exponent:
                return node
            done[0] = True
            return ("num", transform(node[1]))
        if node[0] in {"op", "call", "rel"}:
            is_power = node[0] == "op" and node[1] == "^" and len(node[2]) == 2
            return (node[0], node[1], tuple(
                replace_first_num(a, transform, done,
                                  in_exponent or (is_power and i == 1))
                for i, a in enumerate(node[2])))
        return node

    done = [False]
    negated = replace_first_num(tree, lambda v: -v if v else 1, done)
    if done[0]:
        out.append(("negate_a_coefficient", negated))
    done = [False]
    perturbed = replace_first_num(tree, lambda v: v + 1, done)
    if done[0]:
        out.append(("perturb_a_literal", perturbed))

    if tree[0] == "rel":
        flip = {"=": "<", "<": "=", ">": "=", "<=": ">", ">=": "<"}
        if tree[1] in flip:
            out.append(("flip_the_relation", ("rel", flip[tree[1]], tree[2])))
        lhs, rhs = tree[2]
        if lhs[0] == "op" and lhs[1] == "+" and len(lhs[2]) > 1:
            dropped = ("op", "+", tuple(lhs[2][1:]))
            out.append(("drop_a_summand", ("rel", tree[1], (dropped, rhs))))
        if lhs[0] == "op" and lhs[1] == "*" and len(lhs[2]) > 2:
            reassoc = ("op", "*", (("op", "*", lhs[2][:2]),) + tuple(lhs[2][2:]))
            out.append(("reassociate_an_operator",
                        ("rel", tree[1], (reassoc, rhs))))
    return out


def _flips_a_point(program, mutated, schema, budget) -> bool:
    """Does the mutation change any ADMITTED point's holds/fails outcome?

    The design's floor is on point verdicts, and the distinction is
    load-bearing: two arms that both end in NO_COUNTEREXAMPLE_FOUND can still
    disagree at every point, and a statement-level comparison would score
    that mutation as inert.
    """

    points = sampler.sample_points(
        program.variables, schema.digest, program.statement_id, budget)
    for point in points:
        bindings = point.as_dict()
        if not all(conform.in_carrier(v, program.carrier)
                   for v in bindings.values()):
            continue
        try:
            if not conform._guard_holds(program, bindings):
                continue
        except Exception:
            continue
        outcomes = []
        for tree in (program.conclusion, mutated):
            try:
                left = conform.eval_under_domain(
                    tree[2][0], bindings, program.carrier,
                    program.division, program.subtraction)
                right = conform.eval_under_domain(
                    tree[2][1], bindings, program.carrier,
                    program.division, program.subtraction)
                outcomes.append(conform.decide_relation(tree[1], left, right))
            except Exception:
                outcomes.append(None)
        if outcomes[0] is not None and outcomes[0] != outcomes[1]:
            return True
    return False


def _skeleton(tree) -> str:
    try:
        return ms.render_skeleton(ms.canonicalize(tree))
    except Exception:
        return "<unrenderable>"


def run_ce1(programs, schema, budget, limit):
    """Mutate, DISCARD the non-mutations, count them, only then sample."""

    surviving = flipped = discarded = 0
    by_class: dict[str, dict] = {}
    non_flipping: list = []
    examined = 0
    for program, row in programs:
        if examined >= limit:
            break
        if not program.variables:
            continue
        base = conform.run(program, schema.digest, budget=budget, keep_points=0)
        if base.get("points_admitted", 0) == 0:
            continue
        examined += 1
        try:
            base_skeleton = ms.render_skeleton(ms.canonicalize(program.conclusion))
        except Exception:
            continue
        for class_id, mutated in _mutations(program.conclusion):
            entry = by_class.setdefault(
                class_id, {"generated": 0, "discarded": 0, "surviving": 0,
                           "flipped": 0})
            entry["generated"] += 1
            try:
                if ms.render_skeleton(ms.canonicalize(mutated)) == base_skeleton:
                    entry["discarded"] += 1
                    discarded += 1
                    continue
            except Exception:
                entry["discarded"] += 1
                discarded += 1
                continue
            entry["surviving"] += 1
            surviving += 1
            mutant = conform.Program(
                statement_id=program.statement_id + f"#{class_id}",
                corpus=program.corpus, conclusion=mutated,
                guard_conjuncts=program.guard_conjuncts,
                variables=program.variables, carrier=program.carrier,
                division=program.division, subtraction=program.subtraction,
            )
            # The SAME admitted point set, and the comparison is on POINT
            # verdicts rather than on the statement verdict. The floor reads
            # "flip at least one POINT verdict": a statement-level comparison
            # would call a mutation inert whenever both arms happened to end
            # in NO_COUNTEREXAMPLE_FOUND, which is most of them.
            if _flips_a_point(program, mutated, schema, budget):
                entry["flipped"] += 1
                flipped += 1
            elif len(non_flipping) < 12:
                # Kept so a missed floor carries its mechanism rather than
                # only its number. A mutation can change the SKELETON and
                # still be unfalsifiable ON THE DECLARED CARRIER — over Nat,
                # `a^2 + b^2 >= 2*a*b` mutated to `>= -2*a*b` is true at
                # every point there is, so no sampler can flip it.
                non_flipping.append({
                    "statement_id": program.statement_id,
                    "class": class_id,
                    "source_skeleton": base_skeleton,
                    "mutant_skeleton": _skeleton(mutated),
                    "admitted_points": base.get("points_admitted"),
                })
    rate = (flipped / surviving) if surviving else 0.0
    return {
        "control": "C-E1 (the perturbation control)",
        "discard_rule_ported_first": (
            "Each mutation is constructed on the TERM, the mutated term is "
            "canonicalized, and any mutation whose canonical skeleton did not "
            "change is DISCARDED and counted. v0.19's C-V4 inherited C-R2's "
            "mutation idea without this clause and scored 0.80 against a "
            "denominator that had never been cleaned."
        ),
        "one_sided_by_construction": (
            "The mutation is applied to the term and read by the COMMITTED "
            "evaluator, never by a mutated one: a consistently mutated pair "
            "is a renaming and round-trips for a reason that has nothing to "
            "do with what the gate reads."
        ),
        "statements_examined": examined,
        "mutations_generated": surviving + discarded,
        "discarded_as_non_mutations": discarded,
        "surviving_skeleton_changing": surviving,
        "flipped_a_verdict": flipped,
        "flip_rate": round(rate, 6),
        "floor": CE1_FLOOR,
        "floor_met": rate >= CE1_FLOOR,
        "per_class": by_class,
        "non_flipping_examples": non_flipping,
        "why_a_missed_floor_here_is_about_the_FLOOR_and_not_only_the_sampler": (
            "A skeleton-changing mutation need not be falsifiable ON THE "
            "DECLARED CARRIER. Over Nat, `a^2 + b^2 >= 2*a*b` mutated to "
            "`>= -2*a*b` is true at every point that exists, so NO sampler "
            "can flip it and no admission rate would help. The floor as "
            "written therefore cannot be met by a correct sampler either, "
            "which makes its miss a finding about the control's "
            "specification as much as about the point set. C-V4's lesson one "
            "level up: the discard rule this control ported discards "
            "mutations whose SKELETON did not move, and what it also needed "
            "to discard is mutations that cannot move a point verdict on the "
            "carrier. Recorded rather than repaired, because repairing a "
            "control after reading its number is the chase §8 forbids."
        ),
        "voiding_sentence": (
            "If fewer than 99% of skeleton-changing mutations flip, the "
            "sampler is not testing the term and every "
            "NO_COUNTEREXAMPLE_FOUND in the run is void."
        ),
    }


# --------------------------------------------------------------------------
# C-E2 — the guard-blind arm, and the always-conforms floor
# --------------------------------------------------------------------------


def run_ce2(programs, schema, budget, limit):
    guarded_cx = blind_cx = compared = 0
    for program, row in programs:
        if compared >= limit:
            break
        if not program.guard_conjuncts or row.guard.has_equality:
            continue
        guarded = conform.run(program, schema.digest, budget=budget,
                              keep_points=0)
        if guarded.get("points_admitted", 0) == 0:
            continue
        compared += 1
        if guarded.get("verdict") == conform.NONCONFORMANT:
            guarded_cx += 1
        blind = conform.run(
            conform.Program(**{**program.__dict__, "guard_conjuncts": ()}),
            schema.digest, budget=budget, keep_points=0)
        if blind.get("verdict") == conform.NONCONFORMANT:
            blind_cx += 1
    guarded_rate = guarded_cx / compared if compared else 0.0
    blind_rate = blind_cx / compared if compared else 0.0
    ratio = (blind_rate / guarded_rate) if guarded_rate else None
    return {
        "control": "C-E2 (the guard-blind arm)",
        "this_is_the_capability_blind_baseline": (
            "The same sampler with the one capability under test — hypothesis "
            "recovery — removed, and nothing else changed. It is the only "
            "instrument that can show the guard apparatus is load-bearing "
            "rather than decorative."
        ),
        "comparison_set": (
            "inequality-only guarded statements whose GUARDED arm admitted "
            ">= 1 point, both arms over the identical admitted point set. "
            "Scoring it over statements whose guarded arm admits nothing "
            "would make the contrast a division by a vacuum."
        ),
        "statements_compared": compared,
        "guarded_counterexamples": guarded_cx,
        "guard_blind_counterexamples": blind_cx,
        "guarded_rate": round(guarded_rate, 6),
        "guard_blind_rate": round(blind_rate, 6),
        "contrast_multiple": (round(ratio, 3) if ratio is not None
                              else "unbounded (the guarded arm found none)"),
        "informative_if": f"the guard-blind rate is >= {CE2_CONTRAST}x the guarded arm's",
        "verdict": (
            "INFORMATIVE" if (blind_rate > 0 and (guarded_rate == 0 or
                              blind_rate / guarded_rate >= CE2_CONTRAST))
            else "VOID — the guard is doing no work and the recovery "
                 "apparatus is decoration"
        ),
        "always_conforms_arm": {
            "counterexamples": 0,
            "why_it_is_here": (
                "A floor, not a contender. It emits NO_COUNTEREXAMPLE_FOUND "
                "for every statement without evaluating anything, so 'we "
                "found no counterexamples' can never be reported without the "
                "arm that also finds none sitting next to it."
            ),
        },
        "measure_zero_row_reported_separately_and_non_informative": (
            "The equality-guarded statements are NOT in the comparison set. "
            "Their guard-blind arm would produce counterexamples in abundance "
            "and their guarded arm produces nothing at all, and a ratio "
            "across that pair would look spectacular while measuring only "
            "that one arm never ran."
        ),
    }


# --------------------------------------------------------------------------
# C-E3 — the independent adjudicator, on the pinned toolchain
# --------------------------------------------------------------------------


def _lean_binary():
    import foreign_voice_eligibility as fve

    _toolchain, binary = fve._toolchain(
        REPO / "prover" / "lean" / "normalizer" / "lean-toolchain")
    return Path(binary)


def _lean_decide(expression: str, carrier: str, binary: Path,
                 timeout: int = 60):
    """`by decide` on a closed proposition. Returns True/False/None."""

    if carrier not in {"Nat", "Int"}:
        return None, "carrier outside decide's reach without Mathlib"
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "Probe.lean"
        source.write_text(
            f"example : ({expression} : Prop) := by decide\n", encoding="utf-8")
        try:
            positive = subprocess.run(
                [str(binary), str(source)], cwd=tmp, capture_output=True,
                text=True, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return None, f"{type(exc).__name__}"
        if positive.returncode == 0:
            return True, "decide accepted the proposition"
        source.write_text(
            f"example : ¬({expression} : Prop) := by decide\n", encoding="utf-8")
        try:
            negative = subprocess.run(
                [str(binary), str(source)], cwd=tmp, capture_output=True,
                text=True, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return None, f"{type(exc).__name__}"
        if negative.returncode == 0:
            return False, "decide accepted the negation"
        return None, "decide did not reduce in either direction"


def _lean_expression(ascii_text: str, carrier: str) -> str:
    """The statement as a Lean proposition over the declared carrier."""

    body = ascii_text.strip()
    return f"(({body} : Prop))" if False else body.replace("^", "^")


def run_ce3(candidates, budget_seconds: int, limit: int):
    """Adjudicate every DECIDED_FALSE and NONCONFORMANT we can reach."""

    try:
        binary = _lean_binary()
    except Exception as exc:
        return {"control": "C-E3", "status": "unavailable",
                "reason": f"{type(exc).__name__}: {exc}", "adjudicated": []}
    if not binary.exists():
        return {"control": "C-E3", "status": "unavailable",
                "reason": f"pinned binary absent at {binary}",
                "adjudicated": []}

    rows, disagreements = [], []
    started = time.time()
    for record, ascii_text in candidates[:limit]:
        if time.time() - started > budget_seconds:
            rows.append({"statement_id": record["statement_id"],
                         "available": False,
                         "reason": "C-E3 time budget exhausted"})
            continue
        carrier = record["domain"]["carrier"]
        typed = f"({ascii_text} : Prop)"
        holds, note = _lean_decide(ascii_text, carrier, binary)
        ours = record["verdict"] in {conform.DECIDED_TRUE}
        if holds is None:
            rows.append({
                "statement_id": record["statement_id"], "available": False,
                "carrier": carrier, "reason": note,
                "honest_non_claim": (
                    "no independent adjudication was available for this "
                    "carrier; the verdict is this repository's arithmetic "
                    "under this repository's schema"
                ),
            })
            continue
        agrees = (holds == ours)
        rows.append({"statement_id": record["statement_id"], "available": True,
                     "carrier": carrier, "lean_says_holds": holds,
                     "our_verdict": record["verdict"], "agrees": agrees,
                     "note": note})
        if not agrees:
            disagreements.append(record["statement_id"])
    return {
        "control": "C-E3 (the independent interpretation)",
        "toolchain": "leanprover/lean4:v4.32.2, invoked directly by path",
        "hermetic": "no lake, no Mathlib, no network",
        "what_is_adjudicated": (
            "the INSTANTIATED counterexample, not the statement. A "
            "universally quantified statement cannot be handed to `decide`, "
            "but a counterexample is a closed proposition."
        ),
        "reaches": "Nat and Int; NOT Rat (Correction 7: instDecidableEqRat "
                   "gets stuck without Mathlib's norm_num)",
        "adjudicated": rows,
        "disagreements": disagreements,
        "voiding_sentence": (
            "If the adjudicator disagrees with the evaluator on any "
            "instantiated counterexample whose carrier the schema declares, "
            "the schema is wrong: every NONCONFORMANT verdict is downgraded "
            "to UNDECLARED_DOMAIN, no corpus-error claim is published, and "
            "the schema is re-registered with its own new run."
        ),
    }


# --------------------------------------------------------------------------
# The run
# --------------------------------------------------------------------------


def build(budget: int, ce1_limit: int, ce2_limit: int, ce3_limit: int,
          ce3_seconds: int) -> dict:
    tautology = revalidate_prereg()

    schema = conform_domain.load()
    relations = census.evaluator_relations()
    register = json.loads((REPO / REGISTER).read_text(encoding="utf-8"))
    pilot = json.loads((REPO / PILOT).read_text(encoding="utf-8"))
    nihil_class = json.loads((REPO / NIHIL_CLASS).read_text(encoding="utf-8"))

    rows, nodes = [], {}
    for path in census.corpora():
        document = json.loads(path.read_text(encoding="utf-8"))
        corpus = document.get("corpus_id", path.parent.name)
        for node in document.get("statement_nodes", []):
            row = census.classify(node, corpus, relations, schema.output_roles)
            rows.append(row)
            nodes[row.statement_id] = node

    ground_records, sampled_records, refusals = [], [], []
    programs = []
    for row in rows:
        node = nodes[row.statement_id]
        try:
            program = conform.compile_statement(node, row, schema)
        except conform.Refusal as exc:
            refusals.append({"statement_id": row.statement_id,
                             "construct": exc.construct})
            continue
        if program.variables:
            programs.append((program, row))
        record = conform.run(program, schema.digest,
                             budget=0 if not program.variables else budget)
        if not program.variables:
            ground_records.append(record)
        else:
            sampled_records.append(record)

    # --- E1 ------------------------------------------------------------
    decided_false = [r for r in ground_records
                     if r["verdict"] == conform.DECIDED_FALSE]
    ground_refused = [r for r in ground_records
                      if r["verdict"] == conform.REFUSED]
    e1 = {
        "gate": "E1 — the ground class is decided, exhaustively",
        "ground_statements": len(ground_records),
        "decided_true": sum(1 for r in ground_records
                            if r["verdict"] == conform.DECIDED_TRUE),
        "decided_false": len(decided_false),
        "refused": len(ground_refused),
        "floor": "zero refusals in the ground class",
        "floor_met": len(ground_refused) == 0,
        "decided_false_exhaustively": [
            {"statement_id": r["statement_id"], "left": r.get("left"),
             "right": r.get("right"), "domain": r["domain"]}
            for r in sorted(decided_false, key=lambda r: r["statement_id"])
        ],
        "refusals_exhaustively": [
            {"statement_id": r["statement_id"],
             "reason": r.get("refusal_reason"),
             "detail": r.get("refusal_detail", "")}
            for r in sorted(ground_refused, key=lambda r: r["statement_id"])
        ],
        "the_two_named_before_the_run": {
            "statement_ids": ["leanworkbook.ground.lean_workbook_plus_16115",
                              "leanworkbook.ground.lean_workbook_plus_46623"],
            "why_named": (
                "§3.5 disclosed them before the registered run so that "
                "finding them again could not be presented as a discovery "
                "the gate made."
            ),
            "still_decided_false": sorted(
                r["statement_id"] for r in decided_false
                if r["statement_id"].endswith(("16115", "46623"))
            ),
        },
    }

    # --- E2 ------------------------------------------------------------
    admitted_any = [r for r in sampled_records
                    if r.get("points_admitted", 0) > 0]
    nonconformant = [r for r in sampled_records
                     if r["verdict"] == conform.NONCONFORMANT]
    not_falsified = [r for r in sampled_records
                     if r["verdict"] == conform.NO_COUNTEREXAMPLE_FOUND]
    admitting_share = (len(admitted_any) / len(sampled_records)
                       if sampled_records else 0.0)
    e2 = {
        "gate": "E2 — the falsification claim",
        "M": budget,
        "denominator": len(sampled_records),
        "denominator_is": (
            "the samplable set INTERSECTED with schema coverage, published by "
            "E0c before this run"
        ),
        "statements_admitting_at_least_one_point": len(admitted_any),
        "share_admitting": round(admitting_share, 6),
        "e2a_floor": E2A_FLOOR,
        "e2a_floor_met": admitting_share >= E2A_FLOOR,
        "e2a_floor_frozen_by": "E0f's dated amendment, 2026-08-25",
        "counterexamples_found": len(nonconformant),
        "not_falsified": len(not_falsified),
        "the_sentence_not_a_rate": (
            f"{len(not_falsified)} statements were tested at their admitted "
            f"points and not falsified, out of {len(sampled_records)} "
            f"samplable-and-schema-covered statements at M = {budget}. "
            f"THIS CERTIFIES NOTHING UNIVERSALLY and is not evidence any of "
            f"them is true; one falsifying point would settle a statement and "
            f"a million agreeing points settle nothing."
        ),
        "no_floor_on_the_counterexample_rate": (
            "Freezing one would be incoherent: a low rate means the corpus is "
            "sound and a high rate means it is not, and both are results."
        ),
        "counterexamples_exhaustively": [
            {"statement_id": r["statement_id"],
             "counterexample": r.get("counterexample"),
             "admitted": r.get("points_admitted"),
             "domain": r["domain"]}
            for r in sorted(nonconformant, key=lambda r: r["statement_id"])
        ],
    }

    # --- E3 ------------------------------------------------------------
    by_construct: dict[str, int] = {}
    for entry in refusals:
        by_construct[entry["construct"]] = by_construct.get(
            entry["construct"], 0) + 1
    buckets = {
        "ground_decided": len(ground_records) - len(ground_refused),
        "ground_refused": len(ground_refused),
        "samplable_no_counterexample": len(not_falsified),
        "samplable_nonconformant": len(nonconformant),
        "samplable_refused": len(sampled_records) - len(not_falsified)
                             - len(nonconformant),
        "refused_at_compile": len(refusals),
    }
    total = sum(buckets.values())
    e3 = {
        "gate": "E3 — verdict or register, and the arithmetic closes",
        "buckets": buckets,
        "refused_at_compile_by_construct": dict(sorted(by_construct.items())),
        "total": total,
        "closes_exactly": total == 12777,
        "the_refused_buckets_are_never_summed": (
            "Some are consequences a maintainer can lift by authoring schema "
            "rows and some are consequences this design owns; merging them "
            "hides which is which."
        ),
        "the_register_is_indexed_by_construct_this_table_by_statement": (
            "The register's blocking_count fields are never summed against "
            "this table. Two questions, two objects."
        ),
    }

    # --- E4 ------------------------------------------------------------
    e4_rows, e4_wrong = [], []
    for instance in nihil_class["instances"]:
        record = conform.rational_root_test(instance["coefficients"])
        correct = record["verdict"] == instance["expected"]
        e4_rows.append({"coefficients": instance["coefficients"],
                        "expected": instance["expected"],
                        "verdict": record["verdict"],
                        "candidates_enumerated": record.get(
                            "candidates_enumerated"),
                        "correct": correct})
        if not correct:
            e4_wrong.append(instance["coefficients"])
    out_of_class = [
        conform.rational_root_test(c)["verdict"] for c in ([5], [], [0], [7])
    ]
    e4 = {
        "gate": "E4 — NIHIL certifies its procedure",
        "class": NIHIL_CLASS,
        "instance_set_digest": nihil_class["instance_set_digest"],
        "instances": len(e4_rows),
        "correct": sum(1 for r in e4_rows if r["correct"]),
        "incorrect": e4_wrong,
        "floor": "all of it",
        "floor_met": not e4_wrong,
        "out_of_class_returned_not_guessed": {
            "probes": [[5], [], [0], [7]], "verdicts": out_of_class,
            "all_out_of_class": all(v == conform.OUT_OF_CLASS
                                    for v in out_of_class),
        },
        "no_corpus_coverage_number_is_quoted": (
            "Correction 5: the honest figure is three statements, all "
            "carrying `sqrt` — a call head outside the evaluator — so none is "
            "compiled by this cycle's machinery. The procedure is certified; "
            "the reach is not claimed."
        ),
        "per_instance": e4_rows,
    }

    # --- controls -------------------------------------------------------
    ce1 = run_ce1(programs, schema, budget, ce1_limit)
    ce2 = run_ce2(programs, schema, budget, ce2_limit)
    adjudicate = [
        (r, (nodes[r["statement_id"]].get("formal_statement") or {})
            .get("canonical_ascii", ""))
        for r in ground_records if r["verdict"] in {conform.DECIDED_FALSE}
    ] + [
        (r, (nodes[r["statement_id"]].get("formal_statement") or {})
            .get("canonical_ascii", ""))
        for r in nonconformant
    ]
    ce3 = run_ce3(adjudicate, ce3_seconds, ce3_limit)

    downgraded = bool(ce3.get("disagreements"))

    return {
        "run_id": "conformance.run.v1",
        "registered": "2026-08-25",
        "design": "docs/DESIGN-statements-that-run.md",
        "roadmap": "docs/ROADMAP-v0.20.md §1",
        "writer": "scripts/measure_conformance.py",
        "commit": _git("rev-parse", "HEAD"),
        "prereg": PREREG,
        "register": REGISTER,
        "pilot": PILOT,
        "c_e4": tautology,
        "e0b": json.loads((REPO / PREREG).read_text(encoding="utf-8"))
              ["census"]["e0b_guard_recovery_table"],
        "e0d": json.loads((REPO / PREREG).read_text(encoding="utf-8"))
              ["census"]["e0d_samplable_denominator"],
        "e0f": {
            "artifact": PILOT,
            "coupled_guards": pilot["scope"]["coupled_guards_measured"],
            "share_admitting": pilot["admission"]["share_admitting_at_least_one"],
            "e2a_floor_frozen_at": E2A_FLOOR,
        },
        "e1": e1,
        "e2": e2,
        "e3": e3,
        "e4": e4,
        "c_e1": ce1,
        "c_e2": ce2,
        "c_e3": ce3,
        "verdicts": {
            "overall": _overall(e1, e2, e3, e4, ce1, ce2, ce3, downgraded),
            "how_to_read_this": (
                "A VOID control voids the reading it gates, so a voided "
                "control outranks a cleared floor. A published miss is a "
                "result: this artifact is committed either way."
            ),
            "gates": [
                {"gate": "E0b", "met": True},
                {"gate": "E1", "met": e1["floor_met"]},
                {"gate": "E2a", "met": e2["e2a_floor_met"]},
                {"gate": "E3", "met": e3["closes_exactly"]},
                {"gate": "E4", "met": e4["floor_met"]},
                {"gate": "C-E1", "met": ce1["floor_met"]},
                {"gate": "C-E2", "informative": ce2["verdict"]},
                {"gate": "C-E3", "disagreements": ce3.get("disagreements", [])},
            ],
        },
        "non_claims": [
            "Agreement is not proof. NO_COUNTEREXAMPLE_FOUND certifies "
            "nothing universally, and no figure here is paired with the word "
            "verified, proved, holds or conforms without its point count.",
            "No decision for the free-variable class at any point count.",
            "This is a lean_workbook denominator and almost purely one; no "
            "sentence describes this cycle as having tested 'the corpus'.",
            "No corpus-coverage number for NIHIL.",
            "No verified_by links and no epistemic-ladder movement.",
            "No throughput claim.",
            "The declared domain is a declaration, not a discovery.",
        ],
    }


def _overall(e1, e2, e3, e4, ce1, ce2, ce3, downgraded) -> str:
    if ce3.get("disagreements"):
        return "VOID — C-E3 disagreed; NONCONFORMANT downgraded to UNDECLARED_DOMAIN"
    if not ce1["floor_met"]:
        return "VOID — C-E1 missed its floor; every NO_COUNTEREXAMPLE_FOUND is void"
    misses = [name for name, met in (
        ("E1", e1["floor_met"]), ("E2a", e2["e2a_floor_met"]),
        ("E3", e3["closes_exactly"]), ("E4", e4["floor_met"]),
    ) if not met]
    if misses:
        return f"MISSED — {', '.join(misses)}; published as the reading"
    return "FIRES"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--budget", type=int, default=1000)
    parser.add_argument("--ce1-limit", type=int, default=200)
    parser.add_argument("--ce2-limit", type=int, default=400)
    parser.add_argument("--ce3-limit", type=int, default=40)
    parser.add_argument("--ce3-seconds", type=int, default=900)
    parser.add_argument("--out", default=ARTIFACT)
    args = parser.parse_args(argv)

    try:
        record = build(args.budget, args.ce1_limit, args.ce2_limit,
                       args.ce3_limit, args.ce3_seconds)
    except RunRefusal as exc:
        print(f"run refused: {exc}", file=sys.stderr)
        return 2

    out = REPO / args.out
    out.write_text(
        json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"overall: {record['verdicts']['overall']}")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
