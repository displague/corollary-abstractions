"""Adjudication of `verified_by` SEMANTIC correspondence.

`tests/test_verified_by.py` owns the provenance rung and keeps a capability-blind
control that deliberately PASSES a gravity statement citing a Boolean theorem.
This file is where that control must FAIL, plus the fail-closed boundary of the
declared fragment and the ownership ambiguity structural matching cannot resolve.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from proof_correspondence import (  # noqa: E402
    CORRESPONDS,
    MISMATCH,
    UNTRANSLATABLE,
    Untranslatable,
    boolean_dual,
    check_corpus,
    check_link,
    declared_forms,
    equation_classes,
    initial_goal_state,
    parse_template,
    read_goal,
    theorem_skeleton,
)
from match_signatures import slot_classes  # noqa: E402


ARTIFACT = "prover/sample_triples.json"

# Every committed link, with the route the delivered check reports. Pinned as a
# TABLE rather than a count so that a change of route -- a link silently falling
# through from `canonical` to some weaker declared variant -- fails the suite.
# The first run of the checker did exactly that for `modus_ponens`, and only the
# recorded route made it visible.
EXPECTED = {
    "BooleanLaws.de_morgan_not_and": (
        "logic.boolean_laws.de_morgan_laws", CORRESPONDS, "canonical"),
    "BooleanLaws.de_morgan_not_or": (
        "logic.boolean_laws.de_morgan_laws", CORRESPONDS, "dual_of_canonical"),
    "BooleanLaws.not_forall_iff_exists_not": (
        "logic.boolean_laws.de_morgan_laws", UNTRANSLATABLE, None),
    "BooleanLaws.distrib_and_or": (
        "logic.boolean_laws.distributivity_meet_over_join", CORRESPONDS,
        "canonical"),
    "BooleanLaws.distrib_or_and": (
        "logic.boolean_laws.distributivity_meet_over_join", CORRESPONDS,
        "dual_of_canonical"),
    "BooleanLaws.double_negation": (
        "logic.boolean_laws.double_negation", CORRESPONDS, "canonical"),
    "BooleanLaws.absorption_and_or": (
        "logic.boolean_laws.absorption", CORRESPONDS, "canonical"),
    "BooleanLaws.absorption_or_and": (
        "logic.boolean_laws.absorption", CORRESPONDS, "dual_of_canonical"),
    "BooleanLaws.identity_and_true": (
        "logic.boolean_laws.identity_laws", CORRESPONDS, "canonical"),
    "BooleanLaws.identity_or_false": (
        "logic.boolean_laws.identity_laws", CORRESPONDS, "dual_of_canonical"),
    "BooleanLaws.non_contradiction": (
        "logic.boolean_laws.complement_laws", CORRESPONDS,
        "equivalent_forms[non_contradiction]"),
    "BooleanLaws.excluded_middle": (
        "logic.boolean_laws.complement_laws", CORRESPONDS, "dual_of_canonical"),
    "BooleanLaws.idempotence_and": (
        "logic.boolean_laws.idempotence", CORRESPONDS, "canonical"),
    "BooleanLaws.idempotence_or": (
        "logic.boolean_laws.idempotence", CORRESPONDS, "dual_of_canonical"),
    "BooleanLaws.modus_ponens": (
        "logic.inference.modus_ponens", CORRESPONDS, "canonical"),
    "BooleanLaws.contraposition": (
        "logic.inference.contraposition", CORRESPONDS, "canonical"),
}


def corpus_nodes() -> dict[str, dict]:
    nodes = {}
    for path in sorted((REPO_ROOT / "data").glob("*/nodes.json")):
        corpus = json.loads(path.read_text(encoding="utf-8"))
        for node in corpus["statement_nodes"]:
            nodes[node["statement_id"]] = node
    return nodes


def link(reference: str, artifact: str = ARTIFACT) -> dict:
    return {"system": "lean4", "artifact": artifact, "reference": reference}


class CommittedCorpusCorrespondenceTests(unittest.TestCase):
    """P-PW1, P-PW2, P-PW4, P-PW5, P-PW6 adjudicated over the live corpus."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = check_corpus(REPO_ROOT / "data", REPO_ROOT)

    def test_every_committed_link_is_adjudicated_with_its_route(self) -> None:
        seen = {}
        for result in self.report.results:
            seen[result.reference] = (
                result.statement_id, result.verdict, result.matched_route
            )
        self.assertEqual(seen, EXPECTED)

    def test_no_committed_link_mismatches(self) -> None:
        self.assertEqual([r.reference for r in self.report.mismatches], [])

    def test_p_pw2_counts(self) -> None:
        """15 CORRESPONDS, 1 UNTRANSLATABLE, 0 MISMATCH over 16 links."""
        self.assertEqual(len(self.report.results), 16)
        self.assertEqual(self.report.count(CORRESPONDS), 15)
        self.assertEqual(self.report.count(UNTRANSLATABLE), 1)
        self.assertEqual(self.report.count(MISMATCH), 0)

    def test_p_pw5_six_links_are_carried_by_the_declared_dual(self) -> None:
        duals = sorted(
            r.reference
            for r in self.report.results
            if r.matched_route == "dual_of_canonical"
        )
        self.assertEqual(
            duals,
            [
                "BooleanLaws.absorption_or_and",
                "BooleanLaws.de_morgan_not_or",
                "BooleanLaws.distrib_or_and",
                "BooleanLaws.excluded_middle",
                "BooleanLaws.idempotence_or",
                "BooleanLaws.identity_or_false",
            ],
        )

    def test_p_pw5_canonical_template_alone_would_reject_seven(self) -> None:
        """The false-MISMATCH count a naive reading of the brief would produce.

        P-PW5 predicted six -- the six DUAL citations -- and that number is
        right for the dual route (test above). The naive count is SEVEN: the
        prediction did not notice that `non_contradiction`, which P-PW4 had
        already named as matching only a declared `equivalent_forms` entry, is a
        seventh link the canonical template alone would reject. Recorded as a
        correction rather than by editing P-PW5.
        """
        nodes = corpus_nodes()
        naive_failures = []
        for reference, (statement_id, verdict, _route) in EXPECTED.items():
            if verdict != CORRESPONDS:
                continue
            node = nodes[statement_id]
            _resolved, _text, target = theorem_skeleton(
                REPO_ROOT / ARTIFACT, reference
            )
            raw = parse_template(
                node["structural_signature"]["anonymized_template"]
            )
            from match_signatures import skeleton  # local: naive baseline only

            from proof_correspondence import as_equation

            canonical_only = skeleton(
                as_equation(raw), equation_classes(raw, slot_classes(node))
            )
            if canonical_only != target:
                naive_failures.append(reference)
        self.assertEqual(
            sorted(naive_failures),
            [
                "BooleanLaws.absorption_or_and",
                "BooleanLaws.de_morgan_not_or",
                "BooleanLaws.distrib_or_and",
                "BooleanLaws.excluded_middle",
                "BooleanLaws.idempotence_or",
                "BooleanLaws.identity_or_false",
                "BooleanLaws.non_contradiction",
            ],
        )

    def test_p_pw6_structural_twins_make_ownership_undecidable(self) -> None:
        ambiguous = {
            r.reference: r.ambiguous_with
            for r in self.report.results
            if r.verdict == CORRESPONDS
        }
        # Every boolean-law link carried by canonical/dual structure is claimed
        # by the set-theory twin as well.
        for reference, partners in ambiguous.items():
            statement_id = EXPECTED[reference][0]
            if statement_id.startswith("logic.inference."):
                self.assertEqual(partners, (), reference)
            elif EXPECTED[reference][2].startswith("equivalent_forms["):
                # The declared-variant route is what breaks the tie here: the
                # set-theory twin does not declare `not(A and not A)`.
                self.assertEqual(partners, (), reference)
            else:
                self.assertTrue(partners, reference)
                self.assertTrue(
                    any(p.startswith("settheory.") for p in partners), reference
                )

    def test_untranslatable_link_names_the_first_order_binder(self) -> None:
        result = next(
            r for r in self.report.results if r.verdict == UNTRANSLATABLE
        )
        self.assertEqual(result.reference, "BooleanLaws.not_forall_iff_exists_not")
        self.assertIn("Prop", result.reason)

    def test_cli_exit_code_is_zero_when_nothing_mismatches(self) -> None:
        import subprocess

        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "scripts" / "proof_correspondence.py"),
                ],
                cwd=temporary,
                capture_output=True,
                text=True,
                check=False,
                env={"PYTHONIOENCODING": "utf-8", **_min_env()},
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("15 CORRESPONDS", result.stdout)


def _min_env() -> dict:
    import os

    return {
        name: os.environ[name]
        for name in ("SystemRoot", "SYSTEMROOT", "COMSPEC", "PATH", "TEMP", "TMP")
        if name in os.environ
    }


class CapabilityBlindControlTests(unittest.TestCase):
    """P-PW3: the control the provenance lint passes must fail here."""

    def test_gravity_statement_citing_modus_ponens_is_a_mismatch(self) -> None:
        node = corpus_nodes()["physics.gravitation.newton_universal_gravitation"]
        result = check_link(node, link("BooleanLaws.modus_ponens"), REPO_ROOT)
        self.assertEqual(result.verdict, MISMATCH)
        self.assertIsNone(result.matched_route)

    def test_the_provenance_lint_still_passes_the_same_pair(self) -> None:
        """The two rungs must disagree; if the lint failed it too, the
        capability-blind control would no longer be blind."""
        from validate_nodes import verified_by_errors

        node = dict(corpus_nodes()[
            "physics.gravitation.newton_universal_gravitation"
        ])
        node["verified_by"] = [link("BooleanLaws.modus_ponens")]
        self.assertEqual(verified_by_errors([node], REPO_ROOT), [])


class ConstructedMismatchTests(unittest.TestCase):
    def artifact(self, root: Path, rows: list[dict], name: str = "proof.json") -> str:
        (root / name).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        return name

    def row(self, theorem: str, before: str, after: str = "no goals") -> dict:
        return {
            "theorem": theorem,
            "tactic": "simp",
            "stateBefore": before,
            "stateAfter": after,
        }

    def test_commutativity_theorem_cited_by_idempotence_is_a_mismatch(self) -> None:
        """A true, closing, well-formed Boolean theorem that proves the wrong law."""
        node = corpus_nodes()["logic.boolean_laws.idempotence"]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            name = self.artifact(
                root,
                [self.row("BooleanLaws.and_comm", "P Q : Prop\n⊢ P ∧ Q ↔ Q ∧ P")],
            )
            result = check_link(node, link("BooleanLaws.and_comm", name), root)
        self.assertEqual(result.verdict, MISMATCH)
        self.assertIn("matches no form", result.reason)

    def test_two_theorem_artifact_adjudicates_the_cited_one(self) -> None:
        """Attack: pack a corresponding theorem beside a non-corresponding one."""
        node = corpus_nodes()["logic.boolean_laws.idempotence"]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            name = self.artifact(
                root,
                [
                    self.row("BooleanLaws.right", "P : Prop\n⊢ P ∧ P ↔ P"),
                    self.row("BooleanLaws.wrong", "P Q : Prop\n⊢ P ∧ Q ↔ Q ∧ P"),
                ],
            )
            good = check_link(node, link("BooleanLaws.right", name), root)
            bad = check_link(node, link("BooleanLaws.wrong", name), root)
        self.assertEqual(good.verdict, CORRESPONDS)
        self.assertEqual(bad.verdict, MISMATCH)

    def test_reordering_artifact_rows_cannot_choose_the_opening_goal(self) -> None:
        """The opening goal is the unlabelled root, not the first row."""
        branch = "case mp\nP : Prop\n⊢ P ∧ P → P"
        opening = "P : Prop\n⊢ P ∧ P ↔ P"
        # Deliberately artifact-first-row-hostile: the branch state is row 0, so
        # "take the first row" would read the theorem as proving `P ∧ P → P`.
        rows = [self.row("T", branch), self.row("T", opening, branch)]
        forward = initial_goal_state(tuple(rows))
        backward = initial_goal_state(tuple(reversed(rows)))
        self.assertEqual(forward, backward)
        self.assertEqual(forward, opening)
        self.assertNotEqual(rows[0]["stateBefore"], forward)

    def test_windows_newlines_do_not_change_the_proposition_read(self) -> None:
        goal, names = read_goal("P Q : Prop\r\n⊢ P ∧ Q ↔ Q ∧ P")
        self.assertEqual(goal, "P ∧ Q ↔ Q ∧ P")
        self.assertEqual(names, frozenset({"P", "Q"}))


class FragmentBoundaryTests(unittest.TestCase):
    """Everything outside the declared fragment must be UNTRANSLATABLE."""

    def assertRefused(self, state: str, needle: str) -> None:
        with self.assertRaises(Untranslatable) as caught:
            read_goal(state)
        self.assertIn(needle, str(caught.exception))

    def test_non_prop_binder(self) -> None:
        self.assertRefused("n : Nat\n⊢ P", "does not bind names at type `Prop`")

    def test_predicate_binder(self) -> None:
        self.assertRefused(
            "α : Type\nF : α → Prop\n⊢ F x", "does not bind names at type `Prop`"
        )

    def test_multiple_goals_in_one_state(self) -> None:
        self.assertRefused("P : Prop\n⊢ P\n⊢ P", "carries 2 goals")

    def test_quantifier_body_is_refused(self) -> None:
        goal, names = read_goal("P : Prop\n⊢ ∀ x, P")
        from proof_correspondence import parse_fragment

        with self.assertRaises(Untranslatable):
            parse_fragment(goal, names)

    def test_arithmetic_is_refused(self) -> None:
        from proof_correspondence import parse_fragment

        with self.assertRaises(Untranslatable):
            parse_fragment("n + 1 > n", frozenset({"n"}))

    def test_undeclared_name_is_refused(self) -> None:
        from proof_correspondence import parse_fragment

        with self.assertRaises(Untranslatable):
            parse_fragment("P ∧ R", frozenset({"P"}))

    def test_chained_iff_is_refused(self) -> None:
        from proof_correspondence import parse_fragment

        with self.assertRaises(Untranslatable):
            parse_fragment("P ↔ Q ↔ P", frozenset({"P", "Q"}))

    def test_lean_precedence_matches_lean(self) -> None:
        """`P ∨ Q ∧ R ↔ (P ∨ Q) ∧ (P ∨ R)` must parse as Lean printed it."""
        from proof_correspondence import emit_template, parse_fragment

        tree = parse_fragment(
            "P ∨ Q ∧ R ↔ (P ∨ Q) ∧ (P ∨ R)", frozenset({"P", "Q", "R"})
        )
        text, _classes = emit_template(tree)
        self.assertEqual(
            text,
            "JOIN(PROP1, MEET(PROP2, PROP3)) = "
            "MEET(JOIN(PROP1, PROP2), JOIN(PROP1, PROP3))",
        )

    def test_asserted_proposition_becomes_an_equation(self) -> None:
        from proof_correspondence import emit_template, parse_fragment

        text, classes = emit_template(parse_fragment("P ∨ ¬P", frozenset({"P"})))
        self.assertEqual(text, "JOIN(PROP1, NEG(PROP1)) = TRUTH")
        self.assertEqual(classes["TRUTH"], "P")


class DeclaredDualTests(unittest.TestCase):
    def dual_of(self, statement_id: str):
        node = corpus_nodes()[statement_id]
        raw = parse_template(
            node["structural_signature"]["anonymized_template"]
        )
        from proof_correspondence import as_equation

        classes = equation_classes(raw, slot_classes(node))
        return boolean_dual(as_equation(raw), classes)

    def test_order_sensitive_heads_get_no_dual(self) -> None:
        """IMPLIES dualizes with an order reversal this table cannot express."""
        self.assertIsNone(self.dual_of("logic.inference.contraposition"))
        routes = {
            form.route
            for form in declared_forms(
                corpus_nodes()["logic.inference.modus_ponens"]
            ).forms
        }
        self.assertNotIn("dual_of_canonical", routes)

    def test_undeclared_lattice_bound_gets_no_dual(self) -> None:
        """Adversarial finding: INCONSISTENCY has no declared TOP spelling, so
        dualizing in place produced the FALSE form `JOIN(P, NEG(P)) =
        INCONSISTENCY` and made a narrative node a spurious claimant of
        `BooleanLaws.excluded_middle`."""
        self.assertIsNone(self.dual_of("narrative.frame.frame_consistency"))
        report = check_corpus(REPO_ROOT / "data", REPO_ROOT)
        excluded = next(
            r for r in report.results
            if r.reference == "BooleanLaws.excluded_middle"
        )
        self.assertEqual(
            excluded.ambiguous_with, ("settheory.boolean_laws.complement_laws",)
        )

    def test_declared_dual_is_an_involution_on_the_lattice_fragment(self) -> None:
        node = corpus_nodes()["logic.boolean_laws.de_morgan_laws"]
        raw = parse_template(
            node["structural_signature"]["anonymized_template"]
        )
        from match_signatures import skeleton
        from proof_correspondence import as_equation, dual_classes

        classes = equation_classes(raw, slot_classes(node))
        once = boolean_dual(as_equation(raw), classes)
        twice = boolean_dual(once, dual_classes(classes))
        self.assertEqual(
            skeleton(twice, classes), skeleton(as_equation(raw), classes)
        )


class DeclaredFormSetTests(unittest.TestCase):
    def test_untranslatable_equivalent_forms_are_recorded_not_dropped(self) -> None:
        forms = declared_forms(corpus_nodes()["logic.boolean_laws.de_morgan_laws"])
        self.assertTrue(any("quantifier" in r for r in forms.refused))
        self.assertTrue(any("nand" in r for r in forms.refused))

    def test_a_statement_with_no_translatable_form_is_untranslatable(self) -> None:
        node = {
            "statement_id": "logic.example.opaque",
            "structural_signature": {"anonymized_template": "", "slot_schema": []},
            "formal_statement": {"equivalent_forms": []},
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "proof.json").write_text(
                json.dumps(
                    [
                        {
                            "theorem": "T",
                            "tactic": "simp",
                            "stateBefore": "P : Prop\n⊢ P ∧ P ↔ P",
                            "stateAfter": "no goals",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            result = check_link(node, link("T", "proof.json"), root)
        self.assertEqual(result.verdict, UNTRANSLATABLE)
        self.assertIn("no translatable form", result.reason)


if __name__ == "__main__":
    unittest.main()
