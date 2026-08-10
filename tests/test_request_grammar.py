"""The bounded request grammar: every registered rule, every named failure.

Two claims are under test and they pull against each other, which is why both
get exhaustive coverage rather than a sample:

* the grammar **covers** the registered forms -- fills, corrections, pronouns,
  owner references, lifetime declarations, abstentions;
* the grammar **refuses** everything else, by name, and a refusal degrades to
  ASK rather than to a guess.

A grammar test that only proved the first claim would be satisfied by a parser
that returned the nearest registered value for any input, which is exactly the
unbounded guesser this module exists not to be.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from conversation import golden_chicken_revision_session  # noqa: E402
from lifetimes import Lifetime  # noqa: E402
from request_grammar import (  # noqa: E402
    RULES,
    SLOT_VALUES,
    FailureReason,
    Intent,
    ParseFailure,
    ParsedRequest,
    normalize,
    parse_request,
)


class GrammarCoverageTests(unittest.TestCase):
    """One case per registered rule id, asserted against the rule table."""

    CASES = (
        ("R0-abstain", "I don't know", Intent.ABSTAIN, None),
        ("R1-bare-value", "silver", Intent.FILL, "silver"),
        ("R2-correction", "no, copper", Intent.CORRECT, "copper"),
        ("R3-imperative", "make the eggs silver", Intent.FILL, "silver"),
        ("R4-owner", "in my version, make the eggs blue", Intent.FILL, "blue"),
        ("R6-pronoun", "make it gold", Intent.FILL, "gold"),
        ("R7-lifetime", "always make the eggs copper", Intent.FILL, "copper"),
    )

    def test_every_registered_rule_fires(self) -> None:
        fired = set()
        for rule_id, utterance, intent, value in self.CASES:
            with self.subTest(rule=rule_id):
                parsed = parse_request(utterance, "egg_color", "alice")
                self.assertIsInstance(parsed, ParsedRequest)
                self.assertEqual(parsed.rule_id, rule_id)
                self.assertIs(parsed.intent, intent)
                self.assertEqual(parsed.value, value)
                self.assertEqual(parsed.slot, "egg_color")
                fired.add(rule_id)
        # R5 is the refusal rule; it is covered in the failure suite below.
        self.assertEqual(
            fired | {"R5-foreign-owner"}, {rule for rule, _ in RULES}
        )

    def test_rule_table_ids_are_unique_and_described(self) -> None:
        ids = [rule for rule, _ in RULES]
        self.assertEqual(len(ids), len(set(ids)))
        for _rule, description in RULES:
            self.assertTrue(description.strip())

    def test_corrections_are_recognised_by_marker_and_by_history(self) -> None:
        by_marker = parse_request("actually copper", "egg_color", "alice")
        self.assertIs(by_marker.intent, Intent.CORRECT)
        by_history = parse_request(
            "silver", "egg_color", "alice", answered_slots=("egg_color",)
        )
        self.assertIs(by_history.intent, Intent.CORRECT)
        first_time = parse_request("silver", "egg_color", "alice")
        self.assertIs(first_time.intent, Intent.FILL)

    def test_trailing_instead_marks_a_correction(self) -> None:
        parsed = parse_request("make the eggs copper instead", "egg_color", "alice")
        self.assertIs(parsed.intent, Intent.CORRECT)
        self.assertEqual(parsed.value, "copper")

    def test_owner_pronouns_resolve_to_the_speaker(self) -> None:
        for utterance in ("make mine copper", "mine copper", "my version: copper"):
            with self.subTest(utterance=utterance):
                parsed = parse_request(utterance, "egg_color", "bob")
                self.assertIsInstance(parsed, ParsedRequest)
                self.assertEqual(parsed.owner, "bob")
                self.assertEqual(parsed.value, "copper")

    def test_slot_pronouns_resolve_against_the_open_goal(self) -> None:
        parsed = parse_request("make them whimsical", "tone", "alice")
        self.assertEqual(parsed.slot, "tone")
        self.assertEqual(parsed.value, "whimsical")

    def test_value_may_repeat_its_own_slot_noun(self) -> None:
        parsed = parse_request("make the eggs silver eggs", "egg_color", "alice")
        self.assertEqual(parsed.value, "silver")
        # ...but only when the repeated noun belongs to the same slot.
        stray = parse_request("make the eggs silver tone", "egg_color", "alice")
        self.assertIsInstance(stray, ParseFailure)

    def test_lifetime_markers_declare_only_declarable_lifetimes(self) -> None:
        durable = parse_request("always make the eggs copper", "egg_color", "a")
        self.assertIs(durable.lifetime, Lifetime.DURABLE)
        goal_local = parse_request("for now, make the eggs blue", "egg_color", "a")
        self.assertIs(goal_local.lifetime, Lifetime.GOAL_LOCAL)
        default = parse_request("make the eggs blue", "egg_color", "a")
        self.assertIs(default.lifetime, Lifetime.SESSION)
        self.assertTrue(default.lifetime.declarable)

    def test_a_correction_may_carry_its_own_lifetime(self) -> None:
        parsed = parse_request("no, always make the eggs gold", "egg_color", "a")
        self.assertIs(parsed.intent, Intent.CORRECT)
        self.assertIs(parsed.lifetime, Lifetime.DURABLE)
        self.assertEqual(parsed.value, "gold")

    def test_normalization_is_case_and_punctuation_only(self) -> None:
        self.assertEqual(normalize("  No,   COPPER!! "), "no copper")
        # No stemming: a value that is not in the table stays out of it.
        self.assertIsInstance(
            parse_request("coppery", "egg_color", "a"), ParseFailure
        )


class GrammarRefusalTests(unittest.TestCase):
    """Every named failure reason, and the guarantee that none of them guesses."""

    def test_unregistered_value_is_named(self) -> None:
        failure = parse_request("make the eggs chartreuse", "egg_color", "a")
        self.assertIsInstance(failure, ParseFailure)
        self.assertIs(failure.reason, FailureReason.UNREGISTERED_VALUE)
        self.assertEqual(failure.ask_slot, "egg_color")

    def test_unregistered_slot_phrase_is_named(self) -> None:
        failure = parse_request("make the wallpaper blue", "egg_color", "a")
        self.assertIsInstance(failure, ParseFailure)
        self.assertIs(failure.reason, FailureReason.UNREGISTERED_VALUE)

    def test_unresolved_pronoun_without_an_open_slot_is_named(self) -> None:
        failure = parse_request("make it gold", None, "a")
        self.assertIsInstance(failure, ParseFailure)
        self.assertIs(failure.reason, FailureReason.UNRESOLVED_PRONOUN)

    def test_foreign_owner_reference_is_refused_not_ignored(self) -> None:
        for utterance in ("make hers blue", "his version: blue", "make theirs blue"):
            with self.subTest(utterance=utterance):
                failure = parse_request(utterance, "egg_color", "alice")
                self.assertIsInstance(failure, ParseFailure)
                self.assertIs(failure.reason, FailureReason.FOREIGN_OWNER)

    def test_empty_and_unmatched_utterances_are_named(self) -> None:
        self.assertIs(
            parse_request("", "egg_color", "a").reason, FailureReason.NO_RULE
        )
        self.assertIs(
            parse_request("   ", "egg_color", "a").reason, FailureReason.NO_RULE
        )
        self.assertIs(
            parse_request("tell me a story about dragons", "egg_color", "a").reason,
            FailureReason.UNREGISTERED_VALUE,
        )

    def test_a_marker_with_no_value_never_reuses_the_old_one(self) -> None:
        failure = parse_request("no,", "egg_color", "a")
        self.assertIsInstance(failure, ParseFailure)
        self.assertIs(failure.reason, FailureReason.UNREGISTERED_VALUE)

    def test_no_utterance_produces_a_value_outside_the_slot_vocabulary(self) -> None:
        """The bound, asserted directly rather than inferred from examples."""

        probes = (
            "make the eggs chartreuse",
            "make the eggs 12",
            "silver-ish",
            "make the eggs whimsical",
            "make the tone silver",
            "make the eggs the eggs",
            "please make the eggs mauve for me",
        )
        for utterance in probes:
            with self.subTest(utterance=utterance):
                parsed = parse_request(utterance, "egg_color", "a")
                if isinstance(parsed, ParsedRequest):
                    self.assertIn(parsed.value, SLOT_VALUES[parsed.slot])

    def test_cross_slot_value_is_refused_rather_than_coerced(self) -> None:
        failure = parse_request("make the eggs whimsical", "egg_color", "a")
        self.assertIsInstance(failure, ParseFailure)
        self.assertIs(failure.reason, FailureReason.UNREGISTERED_VALUE)


class DegradeToAskTests(unittest.TestCase):
    """P-DS6's second half, exercised through the real session, not a stub."""

    def test_parse_failure_asks_a_signed_question_and_binds_nothing(self) -> None:
        session = golden_chicken_revision_session("alice")
        turn = session.say("make the eggs chartreuse")
        self.assertFalse(turn.understood)
        self.assertIs(turn.parsed.reason, FailureReason.UNREGISTERED_VALUE)
        self.assertIsNotNone(session.state.awaiting)
        self.assertIn("egg_color", turn.asked)
        self.assertEqual(session.state.user_frame.bindings, ())
        self.assertIsNone(
            session.verifier.binding_value(session.state, "egg_color")
        )

    def test_the_asked_question_can_then_be_answered(self) -> None:
        session = golden_chicken_revision_session("alice")
        session.say("make the eggs chartreuse")
        session.say("copper")
        self.assertEqual(
            session.verifier.binding_value(session.state, "egg_color"), "copper"
        )

    def test_a_second_failure_reuses_the_outstanding_question(self) -> None:
        session = golden_chicken_revision_session("alice")
        first = session.say("make the eggs chartreuse")
        second = session.say("make the eggs mauve")
        self.assertEqual(first.asked, second.asked)
        self.assertEqual(len(session.state.user_frame.questions), 1)

    def test_abstention_leaves_the_slot_unknown(self) -> None:
        session = golden_chicken_revision_session("alice")
        turn = session.say("I don't know")
        self.assertTrue(turn.abstained)
        self.assertIs(turn.parsed.intent, Intent.ABSTAIN)
        self.assertEqual(session.state.user_frame.bindings, ())
        self.assertIsNone(
            session.verifier.binding_value(session.state, "egg_color")
        )

    def test_a_foreign_owner_cannot_revise_another_session(self) -> None:
        alice = golden_chicken_revision_session("alice")
        alice.say("make the eggs silver")
        bob = golden_chicken_revision_session("bob")
        turn = bob.say("make hers blue")
        self.assertFalse(turn.understood)
        self.assertIs(turn.parsed.reason, FailureReason.FOREIGN_OWNER)
        self.assertEqual(
            alice.verifier.binding_value(alice.state, "egg_color"), "silver"
        )


if __name__ == "__main__":
    unittest.main()
