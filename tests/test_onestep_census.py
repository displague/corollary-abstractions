"""Tests for R1, ONE STEP's depth-1 census (`DESIGN-handles.md` §7 B9).

The census is a partition of 12,777 statements by a shape predicate, so
there are exactly three ways it can be wrong and all three are checked:

1. **the predicate does not mean what the artifact says it means** --
   every clause of the published definitions is exercised against a
   hand-built tree, including the two boundaries that carry the whole
   split (one antecedent conjunct versus two; `=` consequent versus `<=`
   consequent);
2. **the partition leaks** -- every statement lands in exactly one of
   the nine classes, the class counts sum to the row count, and every
   class assignment is cross-checked against a *different* committed
   producer (`match_signatures.load_nodes`'s call-head list), which knows
   nothing about this file's classifier;
3. **the floor readout claims a limb it did not measure** -- B9's floor
   is a conjunction, Q60 is unsealed, and the artifact must say so
   rather than produce a question-side number from unsealed drafts.

The last one is the reason this file exists at all. A census that
published "floor met" off one limb of a two-limb clause would be the
v0.21 G5 defect in a new lane.
"""

from __future__ import annotations

import collections
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import onestep_census as onestep  # noqa: E402

ARTIFACT = ROOT / "experiments" / "onestep_census.json"
DATA = ROOT / "data"


def call(head: str, *args: tuple) -> tuple:
    return ("call", head, tuple(args))


def rel(name: str, left: tuple, right: tuple) -> tuple:
    return ("rel", name, (left, right))


X = ("slot", "X")
Y = ("slot", "Y")
ZERO = ("num", 0, ())


class TheDefinitionsAreWhatTheArtifactSays(unittest.TestCase):
    """Point 1. Every published clause, against a tree built to test it."""

    def test_universals_are_stripped_and_existentials_are_not(self) -> None:
        body = rel("<=", X, Y)
        self.assertEqual(onestep.core(call("FORALL", X, call("FORALL", Y, body))),
                         body)
        existential = call("EXISTS", X, body)
        self.assertEqual(onestep.core(existential), existential)

    def test_meet_flattens(self) -> None:
        a, b, c = rel(">", X, ZERO), rel(">", Y, ZERO), rel("=", X, Y)
        nested = call("MEET", call("MEET", a, b), c)
        self.assertEqual(onestep.conjuncts(nested), [a, b, c])
        self.assertEqual(onestep.conjuncts(a), [a])

    def test_one_obligation_with_a_bound_is_a_conditional_inequality(self) -> None:
        tree = call("IMPLIES", rel(">", X, ZERO), rel("<=", X, Y))
        self.assertEqual(onestep.classify(tree), ("CONDITIONAL_INEQUALITY", 1))

    def test_two_obligations_with_a_bound_is_a_side_conditioned_bound(self) -> None:
        antecedent = call("MEET", rel(">", X, ZERO), rel(">", Y, ZERO))
        tree = call("IMPLIES", antecedent, rel("<=", X, Y))
        self.assertEqual(onestep.classify(tree), ("SIDE_CONDITIONED_BOUND", 2))

    def test_the_boundary_is_the_conjunct_count_and_nothing_else(self) -> None:
        """The one judgement the split rests on, isolated."""

        consequent = rel(">=", X, Y)
        one = call("IMPLIES", rel(">", X, ZERO), consequent)
        two = call("IMPLIES", call("MEET", rel(">", X, ZERO), rel(">", Y, ZERO)),
                   consequent)
        self.assertNotEqual(onestep.classify(one)[0], onestep.classify(two)[0])

    def test_an_equality_consequent_is_an_implication_not_a_bound(self) -> None:
        tree = call("IMPLIES", rel(">", X, ZERO), rel("=", X, Y))
        self.assertEqual(onestep.classify(tree), ("IMPLICATION", 1))

    def test_a_bare_relation_is_an_unconditional_fact(self) -> None:
        self.assertEqual(onestep.classify(rel("=", X, Y)),
                         ("UNCONDITIONAL_FACT", 0))

    def test_a_conjunction_of_implications_is_the_sensitivity_band(self) -> None:
        rule = call("IMPLIES", rel(">", X, ZERO), rel(">=", X, Y))
        self.assertEqual(onestep.classify(call("MEET", rule, rule))[0],
                         "HOSTED_IMPLICATIONS")
        mixed = call("MEET", rule, rel("=", X, Y))
        self.assertEqual(onestep.classify(mixed)[0], "MIXED_CONJUNCTION")
        facts = call("MEET", rel("=", X, Y), rel(">", X, ZERO))
        self.assertEqual(onestep.classify(facts)[0], "CONJUNCTION_OF_FACTS")

    def test_the_band_is_not_counted_as_consumable(self) -> None:
        for name in onestep.SENSITIVITY_BAND:
            self.assertNotIn(name, onestep.CONSUMABLE)

    def test_a_predicate_atom_is_not_consumable(self) -> None:
        self.assertEqual(onestep.classify(call("PRIME", X))[0], "PREDICATE_ATOM")

    def test_quantified_rules_classify_as_the_rule_they_are(self) -> None:
        inner = call("IMPLIES", rel(">", X, ZERO), rel(">=", X, Y))
        self.assertEqual(onestep.classify(call("FORALL", X, inner)),
                         onestep.classify(inner))


class ThePartitionDoesNotLeak(unittest.TestCase):
    """Point 2, including a cross-check by a producer that knows nothing."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        cls.rows = cls.artifact["rows"]

    def test_every_statement_appears_once_in_exactly_one_class(self) -> None:
        ids = [row["statement_id"] for row in self.rows]
        self.assertEqual(len(ids), len(set(ids)))
        for row in self.rows:
            self.assertIn(row["class"], onestep.ALL_CLASSES)

    def test_the_class_counts_are_the_rows(self) -> None:
        counted = collections.Counter(row["class"] for row in self.rows)
        published = self.artifact["totals"]["by_class"]
        for name in onestep.ALL_CLASSES:
            self.assertEqual(counted.get(name, 0), published[name], name)
        self.assertEqual(sum(published.values()), len(self.rows))
        self.assertTrue(self.artifact["totals"]["partition_check"])

    def test_the_consumable_count_is_the_consumable_rows(self) -> None:
        strict = [row for row in self.rows if row["consumable"]]
        self.assertEqual(
            {row["class"] for row in strict}, set(onestep.CONSUMABLE))
        self.assertEqual(
            len(strict),
            self.artifact["one_step_consumable"]["strict"]["statements"])

    def test_every_class_agrees_with_the_call_head_inventory(self) -> None:
        """A different producer, asked the same question sideways.

        `load_nodes` computes each node's call heads without ever looking
        at this file's classifier. Anything classified as an implication
        shape must carry `IMPLIES`; anything existential must carry
        `EXISTS`; anything in the sensitivity band must carry both
        `MEET` and `IMPLIES`. A classifier reading the wrong field could
        not satisfy all three.
        """

        from match_signatures import load_nodes  # noqa: PLC0415

        nodes, problems = load_nodes(DATA)
        self.assertEqual(problems, [])
        heads = {node.statement_id: set(node.call_heads) for node in nodes}
        checked = 0
        for row in self.rows:
            own = heads[row["statement_id"]]
            if row["class"] in onestep.CONSUMABLE:
                self.assertIn("IMPLIES", own, row["statement_id"])
                checked += 1
            elif row["class"] == "EXISTENTIAL":
                self.assertIn("EXISTS", own, row["statement_id"])
                checked += 1
            elif row["class"] in onestep.SENSITIVITY_BAND:
                self.assertIn("MEET", own, row["statement_id"])
                self.assertIn("IMPLIES", own, row["statement_id"])
                checked += 1
        self.assertGreater(checked, 0)

    def test_obligation_counts_are_positive_exactly_on_implication_shapes(self) -> None:
        for row in self.rows:
            if row["class"] in onestep.CONSUMABLE:
                self.assertGreaterEqual(row["antecedent_obligations"], 1)
            else:
                self.assertEqual(row["antecedent_obligations"], 0, row["class"])

    def test_the_side_condition_split_holds_row_by_row(self) -> None:
        for row in self.rows:
            if row["class"] == "SIDE_CONDITIONED_BOUND":
                self.assertGreaterEqual(row["antecedent_obligations"], 2)
            if row["class"] == "CONDITIONAL_INEQUALITY":
                self.assertEqual(row["antecedent_obligations"], 1)

    def test_nothing_was_dropped(self) -> None:
        committed = 0
        for path in sorted(DATA.glob("*/nodes.json")):
            document = json.loads(path.read_text(encoding="utf-8"))
            committed += len(document.get("statement_nodes", []))
        self.assertEqual(
            len(self.rows) + self.artifact["totals"]["statements_unparsed"],
            committed)


class TheFloorReadoutClaimsOnlyWhatItMeasured(unittest.TestCase):
    """Point 3. B9's floor is a conjunction and one limb does not exist yet."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    def test_the_question_side_is_deferred_with_its_prerequisite_named(self) -> None:
        question = self.artifact["b9_floor_readout"]["question_side"]
        self.assertEqual(question["status"], "DEFERRED")
        self.assertIsNone(question["measured"])
        self.assertIn("H-P2", question["blocked_on"])

    def test_the_verdict_is_incomplete_not_met(self) -> None:
        readout = self.artifact["b9_floor_readout"]
        self.assertEqual(readout["verdict"],
                         "INCOMPLETE -- one limb measured, one limb deferred")
        self.assertNotIn("MET", readout["verdict"].upper().split())

    def test_the_statement_side_number_is_the_measured_one(self) -> None:
        readout = self.artifact["b9_floor_readout"]["statement_side"]
        strict = self.artifact["one_step_consumable"]["strict"]["statements"]
        widest = self.artifact["one_step_consumable"]["widest"]["statements"]
        self.assertEqual(readout["measured_strict"], strict)
        self.assertEqual(readout["measured_widest"], widest)
        self.assertEqual(readout["met_strict"], strict >= readout["floor"])
        self.assertEqual(readout["met_widest"], widest >= readout["floor"])

    def test_the_slice_did_not_seal_q60(self) -> None:
        """The fence. Nothing in this lane may produce a sealed question set.

        Checked structurally rather than by grepping for the word `seal`
        -- the module says "forbidden to seal it" in its own prose, and a
        substring test would have gone red on the sentence stating the
        rule it was meant to enforce.
        """

        # A rule, not three literal filenames: a fence naming the three
        # files someone might have written is a fence that any fourth
        # name walks through.
        allowed = {"plain_question_set.json"}  # v0.21's, committed
        offenders = sorted(
            path.name for path in (ROOT / "experiments").glob("*.json")
            if path.name not in allowed
            and ("q60" in path.name.lower() or "question" in path.name.lower()))
        self.assertEqual(offenders, [], "a question-set artifact appeared in "
                                        "a slice forbidden to seal one")
        source = (ROOT / "scripts" / "onestep_census.py").read_text(
            encoding="utf-8")
        self.assertEqual(source.count("write_text"), 1)
        self.assertIn("onestep_census.json", source)
        for key in ("questions", "question_set", "q60"):
            self.assertNotIn(key, self.artifact)

    def test_the_cross_census_reading_recomputes(self) -> None:
        """The consumable/reachable intersection, recomputed from producers."""

        block = self.artifact["cross_census_reading"]
        consumable = [row for row in self.artifact["rows"] if row["consumable"]]
        fresh = onestep.cross_census(consumable, DATA)
        self.assertEqual(fresh["with_a_specific_typable_handle"],
                         block["with_a_specific_typable_handle"])
        self.assertEqual(
            block["with_a_specific_typable_handle"]
            + block["without_any_specific_typable_handle"],
            block["one_step_consumable_strict"])

    def test_the_artifact_attests_the_committed_writer(self) -> None:
        """The H1 guard, locally. See test_handles_census for what it cost."""

        import hashlib  # noqa: PLC0415

        block = self.artifact["provenance"]
        writer = ROOT / "scripts" / "onestep_census.py"
        self.assertEqual(block["writer"], "scripts/onestep_census.py")
        self.assertEqual(
            block["writer_sha256_lf"],
            hashlib.sha256(
                writer.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            "the artifact attests a writer that is not the committed one -- "
            "regenerate it")

    def test_no_budget_or_pilot_artifact_exists(self) -> None:
        """H-P1 is not this slice's to author, and B is not frozen anywhere."""

        for name in ("handles_budget.json", "budget_pilot.json",
                     "handles_budget_pilot.json", "hp1_budget.json"):
            self.assertFalse((ROOT / "experiments" / name).exists(), name)
        for source in ("onestep_census.py", "handles_census.py",
                       "erratum_probe.py"):
            text = (ROOT / "scripts" / source).read_text(encoding="utf-8")
            self.assertNotIn("B = 40", text, source)
            self.assertNotIn("budget_used", text, source)

    def test_no_proof_or_search_claim_is_made(self) -> None:
        blob = json.dumps(self.artifact).lower()
        self.assertIn("no search, no lean", blob)
        self.assertTrue(any("proof question" in claim
                            for claim in self.artifact["non_claims"]))


if __name__ == "__main__":
    unittest.main()
