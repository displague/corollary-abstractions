#!/usr/bin/env python3
"""R1 -- ONE STEP's depth-1 census (`DESIGN-handles.md` §7 B9, §11).

ONE STEP is the fold of CHAIN and BRIDGE: *answer-or-frontier*, where a
correct refusal scores. Before any of that can be built, one number has
to exist -- how many committed statements admit a **one-step consumer
shape** at all. B9 makes that number a lane opener:

> **R1** (depth-1 census): ONE STEP's build opens at >=200 one-step-
> consumable statements AND >=5/60 questions landing there -- *the floor
> is a lane opener, not an instrument verdict; a miss closes the lane and
> the census publishes regardless; meetability is deliberately not argued
> because the census exists to measure it.*

This file publishes the **statement side** of that conjunction. The
question side is a cross-tab against Q60, and **Q60 is not sealed** --
H-P2 has not run, and this slice is forbidden to seal it. So the
question-side half is recorded as deferred with the prerequisite named,
and the lane's adjudication belongs to the roadmap, not to this artifact.

**No search. No Lean. No proof attempt.** Everything here is a predicate
over the canonical parse of each node's `anonymized_template`, produced
by committed code (`match_signatures.canonicalize(Parser(tokenize(...)))`
-- the same pipeline `load_nodes` runs at `:1010-1011`). Whether a
statement *can* actually be consumed in one step is a proof question;
whether it *has the shape of* a one-step consumer is a parse question,
and only the parse question is asked here.

## The shape classes, defined mechanically

Let `core(t)` strip leading universal quantifiers: while `t` is
`FORALL(binder, body)`, take `body`. Universals are stripped because a
universally quantified rule is the same rule; existentials are not,
because an existential body is not something a consumer discharges.

Let `conjuncts(t)` flatten nested `MEET` into a list.

Then exactly one class per statement, in this order:

- **IMPLICATION** -- `core` is `IMPLIES(A, C)` and `core(C)` is not a
  relational bound. One consumer step: discharge `A`, obtain `C`.
- **CONDITIONAL_INEQUALITY** -- `core` is `IMPLIES(A, C)`, `core(C)` is a
  relational bound (`<`, `<=`, `>`, `>=`), and `A` is a single
  obligation. One consumer step: discharge one condition, obtain a bound.
- **SIDE_CONDITIONED_BOUND** -- as above, but `A` has two or more
  conjuncts. One consumer step, several side conditions: discharge the
  conjunction, obtain a bound. The split from CONDITIONAL_INEQUALITY is
  the antecedent's conjunct count and nothing else, so both are countable
  without a judgement call.

Those three are **one-step-consumable**. The rest are not, and each is
named rather than swept into a remainder:

- **HOSTED_IMPLICATIONS** -- `core` is a `MEET` whose every conjunct is
  an implication. Reported as a **sensitivity band, not as consumable**:
  reaching the rule inside needs a projection first, which is a second
  step. The band is published so the floor can be read both ways instead
  of resting on one debatable call.
- **MIXED_CONJUNCTION** -- a `MEET` with some implication conjuncts and
  some not. Same band, same reason.
- **CONJUNCTION_OF_FACTS** -- a `MEET` with no implication conjunct.
- **EXISTENTIAL** -- `core` is `EXISTS(...)`.
- **UNCONDITIONAL_FACT** -- `core` is a bare relation. A fact, not a
  rule: consuming it is depth 0, and counting it would make the floor
  meaningless.
- **PREDICATE_ATOM** -- `core` is any other call (`NEG`, `EVEN`,
  `PRIME`, a modality...).
- **OTHER** -- anything the eight above do not cover. Published with its
  members so the partition is complete rather than tidy.

Writes: `experiments/onestep_census.json`
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from match_signatures import (Parser, TemplateParseError, canonicalize,  # noqa: E402
                              tokenize)
from report_provenance import corpus_provenance  # noqa: E402

SCHEMA = "onestep_census.v1"

#: The relational heads that make a consequent a *bound* rather than an
#: identity. `=` is deliberately excluded: an equation obtained under a
#: hypothesis is a rewrite, not a bound, and ONE STEP's frontier reading
#: is about bounds.
BOUND_RELS = frozenset({"<", "<=", ">", ">="})

CONSUMABLE = ("IMPLICATION", "CONDITIONAL_INEQUALITY", "SIDE_CONDITIONED_BOUND")
SENSITIVITY_BAND = ("HOSTED_IMPLICATIONS", "MIXED_CONJUNCTION")
ALL_CLASSES = CONSUMABLE + SENSITIVITY_BAND + (
    "CONJUNCTION_OF_FACTS", "EXISTENTIAL", "UNCONDITIONAL_FACT",
    "PREDICATE_ATOM", "OTHER")

#: `DESIGN-handles.md` §7 B9.
STATEMENT_FLOOR = 200
QUESTION_FLOOR = 5
QUESTION_DENOMINATOR = 60


# --------------------------------------------------------------------------
# tree predicates
# --------------------------------------------------------------------------


def is_call(node: tuple, head: str) -> bool:
    return node[0] == "call" and node[1] == head


def core(node: tuple) -> tuple:
    """Strip leading universal quantifiers. `FORALL(x, body)` -> `body`."""

    while is_call(node, "FORALL") and node[2]:
        node = node[2][-1]
    return node


def conjuncts(node: tuple) -> list[tuple]:
    """Flatten nested `MEET`. A non-MEET is a one-element conjunction."""

    if not is_call(node, "MEET"):
        return [node]
    out: list[tuple] = []
    for arg in node[2]:
        out.extend(conjuncts(arg))
    return out


def classify(tree: tuple) -> tuple[str, int]:
    """`(class, antecedent_obligations)`. Exactly one class per statement."""

    head = core(tree)
    if is_call(head, "IMPLIES") and len(head[2]) >= 2:
        antecedent, consequent = head[2][0], head[2][-1]
        obligations = len(conjuncts(core(antecedent)))
        target = core(consequent)
        if target[0] == "rel" and target[1] in BOUND_RELS:
            if obligations >= 2:
                return "SIDE_CONDITIONED_BOUND", obligations
            return "CONDITIONAL_INEQUALITY", obligations
        return "IMPLICATION", obligations
    if is_call(head, "MEET"):
        parts = [core(part) for part in conjuncts(head)]
        implications = sum(1 for part in parts if is_call(part, "IMPLIES"))
        if implications == len(parts):
            return "HOSTED_IMPLICATIONS", 0
        if implications:
            return "MIXED_CONJUNCTION", 0
        return "CONJUNCTION_OF_FACTS", 0
    if is_call(head, "EXISTS"):
        return "EXISTENTIAL", 0
    if head[0] == "rel":
        return "UNCONDITIONAL_FACT", 0
    if head[0] == "call":
        return "PREDICATE_ATOM", 0
    return "OTHER", 0


# --------------------------------------------------------------------------
# the reading the two censuses only have together
# --------------------------------------------------------------------------


def cross_census(consumable: list[dict], data_dir: Path) -> dict:
    """How much of the consumable mass H-P0 says a person can reach.

    Both halves are recomputed here from the same committed producers
    H-P0 used, rather than read out of `handles_census.json`, so this
    block does not depend on that artifact being current.
    """

    import handles_census as hp0  # noqa: PLC0415

    rows = hp0.corpus_rows(data_dir)
    parsed, _problems = hp0.parsed_by_id(data_dir)
    slex = {sid: hp0.slex_handles(node) for _c, sid, node in rows}
    sinv = {sid: set(parsed[sid].call_heads) if sid in parsed else set()
            for _c, sid, _n in rows}
    slex_counts = hp0.resolves_to(slex)
    sinv_counts = hp0.resolves_to(sinv)
    k = hp0.DEFAULT_K
    typable = {sid for sid in slex
               if any(slex_counts[h] <= k for h in slex[sid])
               or any(sinv_counts[h] <= k for h in sinv[sid])}

    ids = {row["statement_id"] for row in consumable}
    both = ids & typable
    return {
        "question": (
            "of the statements that admit a one-step consumer shape, how many "
            "can a question reach at all? H-P0 answers the second half"
        ),
        "specificity_K": k,
        "one_step_consumable_strict": len(ids),
        "with_a_specific_typable_handle": len(both),
        "without_any_specific_typable_handle": len(ids - typable),
        "reading": (
            f"{len(both)} of {len(ids)} one-step-consumable statements carry a "
            f"specific S-LEX or S-INV handle. The statement-side floor is met "
            f"many times over, and it is met almost entirely by statements "
            f"H-P0 shows are nameless -- the consumable mass and the "
            f"unreachable mass are largely the same statements. That is an "
            f"observation about two committed censuses, not a verdict on "
            f"either lane."
        ),
        "non_claim": (
            "this does not open or close R1's lane and does not fire "
            "DESIGN-handles §9's stop clause. Both are adjudications the "
            "roadmap makes, and R1's needs a question side that does not exist "
            "yet"
        ),
    }


# --------------------------------------------------------------------------
# the census
# --------------------------------------------------------------------------


def build(data_dir: Path, repo_root: Path) -> dict:
    rows: list[dict] = []
    unparsed: list[dict] = []
    for path in sorted(data_dir.glob("*/nodes.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        for node in document.get("statement_nodes", []):
            sid = node.get("statement_id")
            template = (node.get("structural_signature") or {}).get(
                "anonymized_template", "")
            if not isinstance(sid, str):
                continue
            if not template:
                unparsed.append({"statement_id": sid, "reason": "no template"})
                continue
            try:
                tree = canonicalize(Parser(tokenize(template)).parse())
            except TemplateParseError as exc:
                unparsed.append({"statement_id": sid, "reason": str(exc)})
                continue
            shape_class, obligations = classify(tree)
            rows.append({
                "statement_id": sid,
                "corpus": path.parent.name,
                "class": shape_class,
                "antecedent_obligations": obligations,
                "consumable": shape_class in CONSUMABLE,
            })

    by_class = collections.Counter(row["class"] for row in rows)
    consumable = [row for row in rows if row["consumable"]]
    band = [row for row in rows if row["class"] in SENSITIVITY_BAND]
    obligations = collections.Counter(
        row["antecedent_obligations"] for row in consumable)

    strict = len(consumable)
    widest = strict + len(band)

    return {
        "schema": SCHEMA,
        "design": "docs/DESIGN-handles.md",
        "roadmap": "docs/ROADMAP-v0.22.md",
        "roadmap_item": "v0.22 rider R1 -- ONE STEP's depth-1 census",
        "headline": (
            f"{strict} of {len(rows)} committed statements admit a one-step "
            f"consumer shape under the strict reading "
            f"({100.0 * strict / len(rows):.1f}%), and {widest} under the "
            f"widest reading that also counts conjunctions hosting "
            f"implications. B9's statement-side floor is {STATEMENT_FLOOR}. "
            f"The question-side half of the same conjunction is NOT measured "
            f"here: Q60 is unsealed and H-P2 has not run."
        ),
        "what_this_is_not": (
            "no search, no Lean, no proof attempt, and no claim that a "
            "statement in a consumable class CAN be consumed -- only that its "
            "committed canonical form has the shape of a one-step consumer. "
            "Shape is a parse question; consumability is a proof question, and "
            "only the parse question is asked here."
        ),
        "provenance": corpus_provenance(Path(__file__), data_dir, repo_root),
        "definitions": {
            "core": "strip leading FORALL binders; a universally quantified "
                    "rule is the same rule. EXISTS is NOT stripped -- an "
                    "existential body is not something a consumer discharges",
            "conjuncts": "flatten nested MEET; a non-MEET is a one-element "
                         "conjunction",
            "bound_relations": sorted(BOUND_RELS),
            "why_equality_is_not_a_bound": (
                "an equation obtained under a hypothesis is a rewrite, not a "
                "bound. ONE STEP's frontier reading is about bounds, so `=` "
                "consequents fall in IMPLICATION rather than in the two bound "
                "classes"
            ),
            "classes": {
                "IMPLICATION":
                    "core is IMPLIES(A, C), core(C) is not a bound. Discharge "
                    "A, obtain C",
                "CONDITIONAL_INEQUALITY":
                    "core is IMPLIES(A, C), core(C) is a bound, A is one "
                    "conjunct. Discharge one condition, obtain a bound",
                "SIDE_CONDITIONED_BOUND":
                    "core is IMPLIES(A, C), core(C) is a bound, A has >= 2 "
                    "conjuncts. Discharge the side conditions, obtain a bound. "
                    "The split from CONDITIONAL_INEQUALITY is the antecedent's "
                    "conjunct count and nothing else",
                "HOSTED_IMPLICATIONS":
                    "core is a MEET whose every conjunct is an implication. "
                    "NOT consumable under the strict reading: reaching the "
                    "rule inside needs a projection first, which is a second "
                    "step",
                "MIXED_CONJUNCTION":
                    "a MEET with some implication conjuncts and some not. Same "
                    "band, same reason",
                "CONJUNCTION_OF_FACTS":
                    "a MEET with no implication conjunct",
                "EXISTENTIAL": "core is EXISTS(...)",
                "UNCONDITIONAL_FACT":
                    "core is a bare relation -- a fact, not a rule. Consuming "
                    "it is depth 0, and counting it would make the floor "
                    "meaningless",
                "PREDICATE_ATOM":
                    "core is any other call: NEG, EVEN, PRIME, a modality",
                "OTHER":
                    "anything the eight above do not cover, published with its "
                    "members so the partition is complete rather than tidy",
            },
        },
        "totals": {
            "statements_parsed": len(rows),
            "statements_unparsed": len(unparsed),
            "unparsed": unparsed,
            "by_class": {name: by_class.get(name, 0) for name in ALL_CLASSES},
            "partition_check": sum(by_class.values()) == len(rows),
        },
        "one_step_consumable": {
            "strict": {
                "classes": list(CONSUMABLE),
                "statements": strict,
                "share_of_corpus": round(100.0 * strict / len(rows), 4),
                "by_corpus": dict(sorted(collections.Counter(
                    row["corpus"] for row in consumable).items())),
                "by_class": {name: by_class.get(name, 0)
                             for name in CONSUMABLE},
            },
            "widest": {
                "classes": list(CONSUMABLE) + list(SENSITIVITY_BAND),
                "statements": widest,
                "share_of_corpus": round(100.0 * widest / len(rows), 4),
                "why_published": (
                    "the strict/widest gap is the whole judgement call in this "
                    "census. Publishing both means the floor is not resting on "
                    "which side of it I landed on"
                ),
            },
            "antecedent_obligations": {
                "definition": "how many conjuncts a consumer must discharge to "
                              "apply the rule once. One rule application is "
                              "one step whatever this number is; it is "
                              "published so a later lane can tighten the "
                              "definition without re-running the census",
                "histogram": dict(sorted(obligations.items())),
                "max": max(obligations) if obligations else 0,
            },
        },
        "b9_floor_readout": {
            "clause": (
                "ONE STEP's build opens at >=200 one-step-consumable "
                "statements AND >=5/60 questions landing there"
            ),
            "statement_side": {
                "floor": STATEMENT_FLOOR,
                "measured_strict": strict,
                "measured_widest": widest,
                "met_strict": strict >= STATEMENT_FLOOR,
                "met_widest": widest >= STATEMENT_FLOOR,
            },
            "question_side": {
                "floor": f"{QUESTION_FLOOR}/{QUESTION_DENOMINATOR}",
                "measured": None,
                "status": "DEFERRED",
                "blocked_on": "H-P2 -- Q60 is not sealed, and this slice is "
                              "forbidden to seal it",
                "why_it_cannot_be_estimated": (
                    "the cross-tab needs the sealed questions and their sealed "
                    "candidate-reading sets. Producing a number from unsealed "
                    "drafts would be the sealed-after-the-fact defect the "
                    "whole prereg discipline exists to prevent"
                ),
            },
            "verdict": "INCOMPLETE -- one limb measured, one limb deferred",
            "adjudication": (
                "B9's floor is a conjunction and only one limb is measured, so "
                "this census does not open or close the lane. DESIGN-handles "
                "§7 B9's stop rule -- census committed, lane opens or closes, "
                "nothing else runs -- is discharged by committing this "
                "artifact; the opening or closing is the roadmap's at H-P2, "
                "and nothing else in R1 runs either way."
            ),
        },
        "cross_census_reading": cross_census(consumable, data_dir),
        "non_claims": [
            "no claim that a consumable statement can actually be consumed -- "
            "that is a proof question and no prover ran",
            "no claim about the three parked lanes R1 was said to be able to "
            "close; closing them needs the question side",
            "no ranking, no selection, no search over the classes",
            "the strict/widest split is a definitional choice, published as "
            "two numbers rather than resolved by preference",
        ],
        "rows": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path,
                        default=ROOT / "experiments" / "onestep_census.json")
    args = parser.parse_args(argv)

    census = build(args.data_dir, args.repo_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(census, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"wrote {args.out}")
    print(census["headline"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
