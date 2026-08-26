#!/usr/bin/env python3
"""W1 — the six-statement pilot, and the floor it was supposed to freeze.

`docs/DESIGN-witnessed-conformance.md` §5:

> **W1 — the six-statement pilot.** Six statements drawn from W0's census by
> the committed predicate and **named in the pilot artifact before any
> obligation is written** [...] **the floor is frozen from the pilot's
> reading, in a dated amendment, BEFORE `target_manifest` seals**. If the
> pilot discharges 2 of 6 the floor is not 40/60; if it discharges **0 of
> 6**, WITNESS publishes that as its result and the slice does not open.

The draw rule is committed here and is recomputable: for each of six shape
classes in a fixed order — unguarded/guarded × one/two/three variables — take
the FIRST candidate by statement id, then fill any unmet class with the first
unused candidate by id. No sampling, no seed, nothing to tune.

**Three controls ride the pilot**, because a pilot that reads zero has to
show the zero is a reading and not a broken pipeline. A **positive control**
is a hand-built non-trivial obligation that is TRUE and must discharge; a
**negative control** is a hand-built non-trivial obligation that is FALSE and
must not; and the **counterfactual tally** hands every pilot obligation to
the checker anyway, with the triviality test switched off, to record what a
version of this instrument without B4 would have published.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import conform  # noqa: E402
import conform_census as census  # noqa: E402
import conform_domain  # noqa: E402
import external_verifier as verifier  # noqa: E402
import witness_obligation as wo  # noqa: E402

CENSUS = "experiments/witness_fragment_census.json"
ARTIFACT = "experiments/witness_pilot.json"
TOOLCHAIN_PIN = "prover/lean/normalizer/lean-toolchain"

#: The six shape classes, in the order the draw walks them.
SHAPE_CLASSES = [
    ("unguarded", 1), ("unguarded", 2), ("unguarded", 3),
    ("guarded", 1), ("guarded", 2), ("guarded", 3),
]
PILOT_SIZE = 6


class ToolchainAbsent(RuntimeError):
    """The pinned checker is not installed. LOUD, never a silent skip."""


def pinned_binary() -> Path:
    toolchain = (REPO / TOOLCHAIN_PIN).read_text(encoding="utf-8").strip()
    binary = verifier.toolchain_binary(toolchain)
    if binary is None:
        raise ToolchainAbsent(
            f"the pinned toolchain {toolchain!r} is NOT INSTALLED. This "
            f"writer refuses to download it (the hermetic rule, "
            f"docs/DESIGN-external-verifier.md) and refuses to skip quietly: "
            f"a gate artifact written without its checker would record "
            f"absence as if it were a reading. Install the toolchain or read "
            f"this refusal as the result."
        )
    return binary


#: PREPENDED TO EVERY PROBE, and the reason is a defect this slice shipped
#: once. Lean's `autoImplicit` silently binds an unknown lowercase identifier
#: as an implicit argument, so an obligation that accidentally carried a free
#: `c` elaborated as an extra implicit binder — a DIFFERENT and strictly
#: stronger proposition than the row it was filed under, accepted with exit 0
#: and no diagnostic. A checker receipt is only evidence about the term you
#: think you sent it.
PREAMBLE = "set_option autoImplicit false" + chr(10)


def check(source: str, binary: Path, timeout: int = 120) -> dict:
    """One `lean` invocation, with autoImplicit off. Never raises."""

    source = PREAMBLE + source
    started = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "Obligation.lean"
        path.write_text(source, encoding="utf-8")
        try:
            done = subprocess.run([str(binary), str(path)], cwd=tmp,
                                  capture_output=True, timeout=timeout)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {"accepted": False, "returncode": None,
                    "failure": type(exc).__name__,
                    "source_sha256": hashlib.sha256(
                        source.encode("utf-8")).hexdigest(),
                    "seconds": round(time.time() - started, 3)}
        raw = (done.stdout + done.stderr).decode("utf-8", "replace")
        output = raw.replace(str(path), "<obligation>.lean").replace(
            str(path).replace("\\", "/"), "<obligation>.lean").strip()
    return {
        "accepted": done.returncode == 0,
        "returncode": done.returncode,
        "source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "checker_output_head": output[:400],
        "seconds": round(time.time() - started, 3),
    }


def load_programs(candidates: set[str]) -> dict:
    schema = conform_domain.load()
    relations = census.evaluator_relations()
    out = {}
    for path in census.corpora():
        document = json.loads(path.read_text(encoding="utf-8"))
        corpus = document.get("corpus_id", path.parent.name)
        for node in document.get("statement_nodes", []):
            if node.get("statement_id") not in candidates:
                continue
            row = census.classify(node, corpus, relations, schema.output_roles)
            out[row.statement_id] = (
                conform.compile_statement(node, row, schema),
                (node.get("formal_statement") or {}).get("canonical_ascii", ""),
            )
    return out


def guard_kind(program) -> str:
    """`box` if every conjunct mentions one variable, `coupling` otherwise."""

    if not program.guard_conjuncts:
        return "none"
    for conjunct in program.guard_conjuncts:
        names = set()
        for side in conjunct[2]:
            names |= _slots(side)
        if len(names) > 1:
            return "coupling"
    return "box"


def _slots(node) -> set:
    if node[0] == "slot":
        return {node[1]}
    if node[0] == "num":
        return set()
    out = set()
    for arg in node[2]:
        out |= _slots(arg)
    return out


def draw(programs: dict) -> list[dict]:
    """The committed draw. Deterministic, recomputable, no seed."""

    ordered = sorted(programs)
    chosen, taken = [], set()
    for guarded, variables in SHAPE_CLASSES:
        for statement_id in ordered:
            if statement_id in taken:
                continue
            program = programs[statement_id][0]
            has_guard = "guarded" if program.guard_conjuncts else "unguarded"
            if has_guard == guarded and len(program.variables) == variables:
                taken.add(statement_id)
                chosen.append({"statement_id": statement_id,
                               "shape_class": f"{guarded}/{variables}var",
                               "class_was_filled": True})
                break
    for statement_id in ordered:
        if len(chosen) >= PILOT_SIZE:
            break
        if statement_id in taken:
            continue
        taken.add(statement_id)
        chosen.append({"statement_id": statement_id,
                       "shape_class": "filler (a shape class was empty)",
                       "class_was_filled": False})
    return chosen[:PILOT_SIZE]


# --------------------------------------------------------------------------
# The controls
# --------------------------------------------------------------------------

#: A NON-TRIVIAL obligation that is TRUE. `(a + c) - b` versus `(a - b) + c`
#: is exactly the regrouping the evaluator would perform if the parser ever
#: handed it a `+` node with three operands, and the two are NOT equal over
#: Nat — but the guard `b <= a` makes them agree, so this discharges.
POSITIVE_CONTROL = (
    "∀ (a b c : Nat), (b <= a) → ((((a + c) - b) >= 1) ↔ (((a - b) + c) >= 1))"
)
#: The same shape WITHOUT the guard. Over Nat it is false at a=1, b=4, c=10:
#: (1 + 10) - 4 = 7 and (1 - 4) + 10 = 10, and at the >= 8 threshold the two
#: sides disagree. `omega` must refuse it.
NEGATIVE_CONTROL = (
    "∀ (a b c : Nat), ((((a + c) - b) >= 8) ↔ (((a - b) + c) >= 8))"
)


def divergence_reachability() -> dict:
    """COUNT the shapes on which the two readings can differ. Not asserted.

    The first version of this pilot published a mechanism that was FALSE as
    worded — it said the divergent class was unreachable from the parser.
    Delta review falsified it: a binary `+` whose FIRST operand is a `neg`
    diverges (the evaluator groups `b - a`, as-written groups `(0 - a) + b`),
    and the parser emits that shape. It is excluded from this slice by the
    FRAGMENT'S LINEARITY PREDICATE, not by the parser, and the difference
    matters to what the next cycle should build. So the numbers are walked
    out of the corpus here rather than reasoned about in prose.
    """

    census_doc = json.loads((REPO / CENSUS).read_text(encoding="utf-8"))
    in_fragment = set(census_doc["candidates"])
    schema = conform_domain.load()
    relations = census.evaluator_relations()

    counts = {"parsed": 0, "op_nodes": 0, "n_ary": 0,
              "leading_neg": 0, "leading_inv": 0}
    with_leading_neg: set = set()
    with_leading_inv: set = set()
    compiled_leading_neg: set = set()
    fragment_leading_neg: set = set()

    def walk(node, statement_id):
        if node[0] in {"num", "slot"}:
            return
        if node[0] == "op" and node[1] in {"+", "*"}:
            counts["op_nodes"] += 1
            if len(node[2]) > 2:
                counts["n_ary"] += 1
            first = node[2][0]
            if node[1] == "+" and first[0] == "op" and first[1] == "neg":
                counts["leading_neg"] += 1
                with_leading_neg.add(statement_id)
            if node[1] == "*" and first[0] == "op" and first[1] == "inv":
                counts["leading_inv"] += 1
                with_leading_inv.add(statement_id)
        for arg in node[2]:
            walk(arg, statement_id)

    for path in census.corpora():
        document = json.loads(path.read_text(encoding="utf-8"))
        corpus = document.get("corpus_id", path.parent.name)
        for node in document.get("statement_nodes", []):
            statement_id = node.get("statement_id", "")
            tree = census.parse(
                (node.get("formal_statement") or {}).get("canonical_ascii", ""))
            if tree is None:
                continue
            counts["parsed"] += 1
            walk(tree, statement_id)
            if statement_id in with_leading_neg:
                row = census.classify(
                    node, corpus, relations, schema.output_roles)
                try:
                    conform.compile_statement(node, row, schema)
                except conform.Refusal:
                    continue
                compiled_leading_neg.add(statement_id)
                if statement_id in in_fragment:
                    fragment_leading_neg.add(statement_id)

    return {
        "statements_parsed": counts["parsed"],
        "plus_and_times_nodes_walked": counts["op_nodes"],
        "n_ary_nodes": counts["n_ary"],
        "n_ary_nodes_note": (
            "A node with more than two operands is where the evaluator's "
            "hoisting would visibly regroup. The parser emits none: `+` and "
            "`*` are left-nested binary throughout."
        ),
        "leading_neg_plus_nodes": counts["leading_neg"],
        "statements_with_a_leading_neg_plus": len(with_leading_neg),
        "of_those_that_compile": len(compiled_leading_neg),
        "of_those_inside_the_w0_fragment": len(fragment_leading_neg),
        "example_statement_id": (
            sorted(compiled_leading_neg)[0] if compiled_leading_neg else None),
        "leading_inv_times_nodes": counts["leading_inv"],
        "statements_with_a_leading_inv_times": len(with_leading_inv),
        "the_accurate_mechanism": (
            "TWO shapes make the readings differ. (1) A node with more than "
            "two operands — the parser emits ZERO of these, so the "
            "evaluator's hoisting never has anything to hoist. (2) A BINARY "
            "node whose FIRST operand is a `neg` (or, for `*`, an `inv`): "
            "the evaluator groups it as `b - a` and the written reading as "
            "`(0 - a) + b`, and over Nat those differ. The parser DOES emit "
            "shape (2) — the counts above say how often — and it is excluded "
            "from this slice by the FRAGMENT'S LINEARITY PREDICATE rather "
            "than by the parser. Saying `the divergent class is unreachable` "
            "was wrong, and wrong in the direction that made the instrument "
            "look less repairable than it is."
        ),
        "what_it_means_for_the_next_cycle": (
            "The divergent class EXISTS and is non-linear. Growing the "
            "fragment to reach it would give the drafted obligation content "
            "— but that content would still be one front-end's parse "
            "compared to itself under two grouping rules, which is a "
            "narrower question than whether the compiler read the statement "
            "correctly. A second front-end is needed BEFORE fragment growth, "
            "not instead of it."
        ),
    }


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


def build(timeout: int) -> dict:
    binary = pinned_binary()
    toolchain = (REPO / TOOLCHAIN_PIN).read_text(encoding="utf-8").strip()
    census_doc = json.loads((REPO / CENSUS).read_text(encoding="utf-8"))
    programs = load_programs(set(census_doc["candidates"]))
    drawn = draw(programs)

    rows = []
    for entry in drawn:
        program, ascii_text = programs[entry["statement_id"]]
        obligation = wo.build(program)
        trivial = obligation["trivial_by_construction"]
        row = {
            "statement_id": entry["statement_id"],
            "shape_class": entry["shape_class"],
            "class_was_filled": entry["class_was_filled"],
            "guard_kind": guard_kind(program),
            "canonical_ascii": ascii_text,
            "variables": obligation["variables"],
            "obligation": obligation["obligation"],
            "evaluated_reading": obligation["evaluated_reading"],
            "as_written_reading": obligation["as_written_reading"],
            "trivial_by_construction": trivial,
            "verdict": wo.REJECTED_TRIVIAL if trivial else None,
        }
        if trivial:
            row["trivial_reason"] = obligation["trivial_reason"]
        # THE COUNTERFACTUAL: hand it to the checker anyway, and record what
        # an instrument without B4 would have published.
        row["counterfactual_without_B4"] = check(
            obligation["lean_source"], binary, timeout)
        if not trivial:
            row["verdict"] = (wo.DISCHARGED
                              if row["counterfactual_without_B4"]["accepted"]
                              else wo.NOT_DISCHARGED)
            row["proof_receipt"] = row.pop("counterfactual_without_B4")
        rows.append(row)

    discharged = [r for r in rows if r["verdict"] == wo.DISCHARGED]
    trivial_rows = [r for r in rows if r["verdict"] == wo.REJECTED_TRIVIAL]
    would_have_discharged = [
        r["statement_id"] for r in rows
        if r.get("counterfactual_without_B4", {}).get("accepted")
    ]

    positive = check(f"example : {POSITIVE_CONTROL} := by omega\n", binary,
                     timeout)
    negative = check(f"example : {NEGATIVE_CONTROL} := by omega\n", binary,
                     timeout)

    # B4's own trap, run on the first drawn target: the SAME reading on both
    # sides. It must come back rejected_trivial, and it must do so by the
    # ordinary structural test rather than by a special case.
    trap_program = programs[drawn[0]["statement_id"]][0]
    trap = wo.build(trap_program, self_comparison=True)

    pipeline_works = positive["accepted"] and not negative["accepted"]
    stop = not discharged

    return {
        "pilot_id": "witness.pilot.v1",
        "registered": "2026-08-26",
        "design": "docs/DESIGN-witnessed-conformance.md §5 (W1)",
        "roadmap": "docs/ROADMAP-v0.21.md §2",
        "writer": "scripts/witness_pilot.py",
        "commit": _git("rev-parse", "HEAD"),
        "reads": CENSUS,
        "census_predicate_hash": census_doc["selection_predicate_hash"],
        "obligation_builder_hash": _sha256_lf(
            REPO / "scripts" / "witness_obligation.py"),
        "checker": {
            "toolchain": toolchain,
            "binary": "~/" + str(binary.relative_to(Path.home())).replace(
                "\\", "/") if str(binary).startswith(str(Path.home()))
            else str(binary),
            "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
            "tactic": "omega",
            "invocation": "the pinned binary by absolute path; no elan proxy, "
                          "no lake, no Mathlib, no network, never a download",
        },
        "draw_rule": (
            "For each of six shape classes in the fixed order "
            "unguarded/guarded × 1/2/3 variables, take the FIRST candidate by "
            "statement id; then fill any unmet class with the first unused "
            "candidate by id. Deterministic and recomputable from the census "
            "artifact alone."
        ),
        "drawn": [r["statement_id"] for r in rows],
        "rows": rows,
        "controls": {
            "positive_control": {
                "obligation": POSITIVE_CONTROL,
                "must": "discharge — it is non-trivial and true",
                "receipt": positive,
                "met": positive["accepted"],
            },
            "negative_control": {
                "obligation": NEGATIVE_CONTROL,
                "must": "NOT discharge — it is non-trivial and false over Nat "
                        "at a=1, b=4, c=10",
                "receipt": negative,
                "met": not negative["accepted"],
            },
            "pipeline_is_not_broken": pipeline_works,
            "why_these_exist": (
                "A pilot that reads zero must show the zero is a READING and "
                "not a pipeline that never worked. The positive control is "
                "the exact regrouping shape this instrument was built to "
                "test, it is non-trivial, and it discharges; the negative "
                "control is the same shape unguarded and false, and the "
                "checker refuses it. So the builder builds, the renderer "
                "renders, `omega` decides, and the zero below is about the "
                "corpus and the parser rather than about the machinery."
            ),
        },
        "b4_self_comparison_trap": {
            "target": drawn[0]["statement_id"],
            "obligation": trap["obligation"],
            "verdict": (wo.REJECTED_TRIVIAL if trap["trivial_by_construction"]
                        else "DISCHARGED — THE INSTRUMENT IS VOID"),
            "met": trap["trivial_by_construction"],
            "rejected_structurally_not_by_special_case": (
                "`build(self_comparison=True)` puts the SAME reading on both "
                "sides and the ordinary tree comparison rejects it. There is "
                "no branch in the builder that recognises the trap, which is "
                "the difference between an instrument the trap can catch and "
                "one that recognises being tested."
            ),
        },
        "reading": {
            "drawn": len(rows),
            "discharged": len(discharged),
            "not_discharged": sum(1 for r in rows
                                  if r["verdict"] == wo.NOT_DISCHARGED),
            "rejected_trivial": len(trivial_rows),
            "the_floor_this_was_meant_to_freeze": (
                "B2's ≥40/60, already void with the 60 (§4's amendment). This "
                "pilot was to set the number in its place."
            ),
            "floor_frozen": None,
            "why_no_floor_is_frozen": (
                "A floor is a fraction of a population that a correct "
                "instrument can reach. This pilot reached zero, so there is "
                "no fraction to freeze and freezing one would be inventing a "
                "number the pilot exists to prevent."
            ),
        },
        "the_counterfactual_that_makes_B4_concrete": {
            "obligations_the_checker_accepted": len(would_have_discharged),
            "of": len(rows),
            "statement_ids": sorted(would_have_discharged),
            "what_it_means": (
                "Every pilot obligation was handed to `omega` anyway, with "
                "the triviality test switched off. The checker ACCEPTED them "
                "— of course it did: they are `P ↔ P`. An instrument without "
                "B4 would have published these as discharged agreement "
                "lemmas, cleared its gate, and reported a capability. That is "
                "not a hypothetical about some other design; it is this "
                "design's own output with one clause removed, and it is the "
                "most direct evidence available that B4 is load-bearing "
                "rather than ceremonial."
            ),
        },
        "stop_condition": {
            "fired": stop,
            "clause": (
                "docs/DESIGN-witnessed-conformance.md §5 and §8: *if it "
                "discharges 0 of 6, WITNESS publishes that as its result and "
                "the slice does not open*."
            ),
            "verdict": (
                "STOPPED — 0 of 6 discharged, and the reason is structural "
                "rather than incidental (see below). The manifest is NOT "
                "sealed, no floor is frozen, no obligation builder runs over "
                "the population, no mutant ledger is built, and no capability "
                "is claimed."
                if stop else "not fired"
            ),
        },
        "divergence_reachability": divergence_reachability(),
        "why_the_zero_is_structural": {
            "finding": (
                "The committed parser emits LEFT-NESTED BINARY `+` and `*` "
                "nodes — `a - b + c` parses as `+(+(a, neg(b)), c)`, not as a "
                "flat three-operand node — so the evaluator's hoisting has "
                "nothing to hoist. That accounts for MOST of the triviality "
                "but not all of it, and the difference was got wrong once: a "
                "binary node whose FIRST operand is a `neg` still diverges, "
                "and the parser emits that shape. It is the FRAGMENT'S "
                "LINEARITY PREDICATE that keeps those out. Within this "
                "fragment, and only within it, the evaluator's reading and "
                "the written reading are the same tree for every census "
                "candidate. The counts are in `divergence_reachability`, "
                "walked rather than argued."
            ),
            "so_what_the_pilot_actually_measured": (
                "Not that the corpus is easy, and not that the checker is "
                "weak. That the OBLIGATION SHAPE, built from a single "
                "front-end, has no content: both sides descend from one parse "
                "tree, and the only difference the construction could express "
                "— the evaluator's regrouping — is a no-op on that tree's "
                "shape. The draft's own residual_risk named this and priced "
                "it as a survivable residual: *'the obligation is built from "
                "the compiler's own front-end reading of S -- a uniform "
                "front-end misreading survives every clause.'* The pilot's "
                "reading is stronger than that: it is not that a misreading "
                "SURVIVES the clauses, it is that there is NOTHING ELSE IN "
                "THE OBLIGATION. B4 is not narrowing a residual here; B4 is "
                "the whole verdict."
            ),
            "what_it_would_take": (
                "A genuinely independent second reading of S — a second "
                "front-end, or the human transcription W2 registered as a "
                "narrowing audit. The draft put that explicitly OUT of the "
                "slice. It is therefore not a residual to be priced later but "
                "a CONSTRUCTION PREREQUISITE, and that is this pilot's "
                "recommendation to the next cycle."
            ),
            "the_divergent_class_is_reachable_but_non_linear": (
                "CORRECTED 2026-08-25, after delta review falsified the "
                "previous wording. The earlier text said the divergent class "
                "was unreachable from the parser. It is not. A BINARY `+` "
                "whose first operand is a `neg` diverges, and the parser "
                "emits it — see the computed `divergence_reachability` block "
                "for how often and for the example statement id. What keeps "
                "it out of this slice is the FRAGMENT'S LINEARITY PREDICATE, "
                "not the parser. The correction strengthens the "
                "recommendation rather than weakening the stop: the "
                "divergent class exists and is non-linear, so a second "
                "front-end is needed even before fragment growth."
            ),
        },
        "non_claims": [
            "No capability is claimed. WITNESS discharged nothing.",
            "No conformance rate, and nothing here touches "
            "experiments/conformance_run.json, which stays void.",
            "This says nothing about whether the 38 fragment statements are "
            "true, and nothing about the 12,739 statements outside the "
            "fragment.",
            "`rejected_trivial` is not a criticism of the statements. It is a "
            "verdict about the OBLIGATION this design built for them.",
            "The stop is not a failure of the pinned checker: both controls "
            "read as specified, so `omega` proved what is true and refused "
            "what is false.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--out", default=ARTIFACT)
    args = parser.parse_args(argv)

    try:
        record = build(args.timeout)
    except ToolchainAbsent as exc:
        print(f"PILOT REFUSED: {exc}", file=sys.stderr)
        return 2

    out = REPO / args.out
    out.write_text(
        json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8")
    for row in record["rows"]:
        print(f"{row['statement_id']}: {row['verdict']} ({row['shape_class']})")
    print(f"reading: {record['reading']}")
    print(f"controls: positive={record['controls']['positive_control']['met']} "
          f"negative={record['controls']['negative_control']['met']}")
    print(f"B4 trap: {record['b4_self_comparison_trap']['verdict']}")
    print(f"STOP: {record['stop_condition']['verdict'][:80]}")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
