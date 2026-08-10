"""Regression pins for the v0.7 corpus-analogy split (roadmap item 5).

The v0.6 lane's failure was not a bug; it was an unchecked claim. These tests
turn each of the six roadmap bullets into something that breaks loudly:
pointability, family non-isomorphism, holdout disjointness, target dedup,
control scores, and specializer verification.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
sys.path.insert(0, str(ROOT / "scripts"))

import corpus_analogy_split as cas  # noqa: E402
from match_signatures import canonicalize  # noqa: E402
from specialize import Search, op_count, render, spelling_ranker  # noqa: E402


class Fixture(unittest.TestCase):
    corpus: cas.Corpus
    raw: list
    quads: list
    splits: dict

    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus = cas.load_corpus(cas.DATA_DIR)
        cls.ledger = Counter()
        cls.raw = cas.build_quadruples(ledger=cls.ledger)
        cls.quads = cas.dedup_by_target(cls.raw)
        cls.splits = cas.build_splits(cls.quads)


# ---------------------------------------------------------------------------
# bullet 1: pointable source leaves, never invented vocabulary
# ---------------------------------------------------------------------------

class PointabilityTests(Fixture):
    def test_every_target_token_is_pointed_at_in_the_input(self) -> None:
        for quad in self.quads:
            row = cas.pointer_row(quad)
            self.assertEqual(
                [row["tokens_struct"][i] for i in row["target_positions"]],
                row["target_tokens"],
                msg=quad.target,
            )

    def test_no_target_introduces_a_token_the_input_lacks(self) -> None:
        for quad in self.quads:
            self.assertLessEqual(set(cas.serialize(quad.d_tree)),
                                 set(cas.input_tokens(quad)), msg=quad.target)

    def test_compound_expansion_leaves_are_the_point_of_the_lane(self) -> None:
        """v0.6 excluded compound expansions entirely; most rows now carry one."""
        with_expansion = [q for q in self.quads if q.expansion_leaves]
        self.assertGreater(len(with_expansion), len(self.quads) // 2)
        for quad in with_expansion:
            b_tokens = set(cas.serialize(quad.b_tree))
            for leaf in quad.expansion_leaves:
                self.assertIn(leaf, b_tokens)
                # An expansion leaf is B's own vocabulary: if it were also
                # reachable through the twin alignment the row would be
                # ambiguous, and the builder refuses those.
                self.assertNotIn(leaf, quad.renamed_leaves)

    def test_head_kind_table_matches_every_authored_template(self) -> None:
        """The declared operator table, not a spelling heuristic.

        The first version of `head_kind` guessed that call heads are UPPERCASE
        identifiers. `sum`, `lim` and `AGGREGATE_n` falsified it against the
        live corpus; this test is what caught it and what keeps a future
        grammar addition from silently mis-typing a target.
        """
        seen: dict[str, str] = {}

        def walk(tree: tuple) -> None:
            if tree[0] in {"slot", "num"}:
                return
            seen[tree[1]] = tree[0]
            for child in tree[2]:
                walk(child)

        for tree in self.corpus.trees.values():
            walk(tree)
        self.assertTrue(seen)
        for head, kind in sorted(seen.items()):
            self.assertEqual(cas.head_kind(head), kind, msg=head)

    def test_serialization_round_trips_on_every_authored_statement(self) -> None:
        for sid, tree in self.corpus.trees.items():
            self.assertEqual(cas.deserialize(cas.serialize(tree)), tree, msg=sid)


# ---------------------------------------------------------------------------
# bullet 2: at least three non-isomorphic structural families
# ---------------------------------------------------------------------------

class FamilyTests(Fixture):
    def test_at_least_three_families_exist_before_a_family_split_is_named(self) -> None:
        self.assertGreaterEqual(len({q.family for q in self.quads}), 3)

    def test_families_are_non_isomorphic_under_the_stricter_untyped_quotient(
            self) -> None:
        """Answering our own adversarial question honestly.

        Family = the matcher's `typed` skeleton, so "distinct families are
        non-isomorphic" is true by definition and therefore worthless as
        evidence. The real question is whether the families survive a COARSER
        quotient that ignores slot classes entirely -- otherwise two of them
        could be one shape wearing a P where the other wears a V, which is
        exactly what `*(?1:P, ?2:V)` and `*(?1:V, ?2:V)` are.

        They are distinct to the matcher (the class governs the identity rule
        and absorption eligibility) but they are NOT distinct shapes, so the
        roadmap's "at least three non-isomorphic structural families" is
        checked against the head/arity witness, where the count is what makes
        the family split meaningful.
        """
        families = sorted({q.family for q in self.quads})
        self.assertEqual(len(families), len(set(families)))
        shapes = set()
        for family in families:
            sample = next(q for q in self.quads if q.family == family)
            shapes.add(tuple(sorted(cas._op_multiset(sample.c_tree).items())))
        self.assertGreaterEqual(
            len(shapes), 3,
            msg=f"{len(families)} typed families collapse to {len(shapes)} shapes")

    def test_the_family_holdout_removes_whole_untyped_shapes_too(self) -> None:
        """A family holdout that only moved a P to a V would be vacuous."""
        assignment = self.splits["family"]

        def shapes(side: str) -> set:
            return {tuple(sorted(cas._op_multiset(q.c_tree).items()))
                    for q in self.quads if assignment[q.target] == side}

        self.assertTrue(shapes("holdout") - shapes("train"))

    def test_every_family_has_a_cross_discipline_witness(self) -> None:
        for quad in self.quads:
            self.assertNotEqual(quad.a_discipline, quad.c_discipline)


# ---------------------------------------------------------------------------
# bullet 3: three holdouts with disjoint leakage surfaces
# ---------------------------------------------------------------------------

class HoldoutTests(Fixture):
    def test_three_splits_exist_and_all_are_two_sided(self) -> None:
        self.assertEqual(set(self.splits), set(cas.SPLIT_NAMES))
        for name, assignment in self.splits.items():
            counts = Counter(assignment.values())
            self.assertGreater(counts["train"], 0, msg=name)
            self.assertGreater(counts["holdout"], 0, msg=name)

    def test_each_split_covers_every_deduplicated_target_exactly_once(self) -> None:
        targets = {q.target for q in self.quads}
        for name, assignment in self.splits.items():
            self.assertEqual(set(assignment), targets, msg=name)

    def test_the_three_holdouts_are_not_one_partition_renamed(self) -> None:
        """Three files must be three partitions, not three names for one.

        The pairwise Jaccard of the holdout sets is the measurement that makes
        "separate holdouts" mean something; 0.26 is the worst pair.
        """
        surfaces = cas.leakage_surfaces(self.quads, self.splits)
        for name, entry in surfaces.items():
            for other, jaccard in entry["jaccard_with"].items():
                self.assertLess(jaccard, 0.30, msg=f"{name} vs {other}")

    def test_axis_entanglement_is_pinned_not_assumed(self) -> None:
        """Full orthogonality is NOT achieved, and the shortfall is the pin.

        Holding out complete families also empties five disciplines out of
        training, because at this corpus size some disciplines occur in only
        one skeleton. The honest report is the number, not an assertion that
        the axes are independent; this test fails if the number drifts, in
        either direction.
        """
        surfaces = cas.leakage_surfaces(self.quads, self.splits)
        self.assertEqual(
            surfaces["family"]["discipline_values_in_holdout_also_in_train"],
            (5, 10))
        self.assertEqual(
            surfaces["discipline"]["family_values_in_holdout_also_in_train"],
            (7, 8))
        self.assertEqual(
            surfaces["vocabulary"]["family_values_in_holdout_also_in_train"],
            (6, 10))
        self.assertEqual(
            surfaces["vocabulary"]["discipline_values_in_holdout_also_in_train"],
            (11, 15))

    def test_family_holdout_actually_removes_skeletons(self) -> None:
        assignment = self.splits["family"]
        held = {q.family for q in self.quads if assignment[q.target] == "holdout"}
        train = {q.family for q in self.quads if assignment[q.target] == "train"}
        self.assertTrue(held)
        self.assertTrue(train)
        self.assertFalse(held & train)

    def test_discipline_holdout_actually_removes_disciplines(self) -> None:
        assignment = self.splits["discipline"]
        held = {q.c_discipline for q in self.quads
                if assignment[q.target] == "holdout"}
        train = {q.c_discipline for q in self.quads
                 if assignment[q.target] == "train"}
        self.assertFalse(held & train)

    def test_vocabulary_holdout_removes_tokens_from_training_targets(self) -> None:
        assignment = self.splits["vocabulary"]
        held = [q for q in self.quads if assignment[q.target] == "holdout"]
        train = [q for q in self.quads if assignment[q.target] == "train"]
        unseen = cas._vocab(held) - cas._vocab(train)
        self.assertTrue(unseen, "the vocabulary holdout held nothing back")
        for quad in train:
            self.assertFalse(unseen & set(cas.serialize(quad.d_tree)))

    def test_splits_are_not_seeded_and_cannot_be_re_rolled(self) -> None:
        """The split rule takes no seed, so there is nothing to search over."""
        again = cas.build_splits(cas.dedup_by_target(self.raw))
        self.assertEqual(again, self.splits)


# ---------------------------------------------------------------------------
# bullet 4: dedup before counting
# ---------------------------------------------------------------------------

class DedupTests(Fixture):
    def test_dedup_leaves_one_row_per_distinct_target(self) -> None:
        targets = [q.target for q in self.quads]
        self.assertEqual(len(targets), len(set(targets)))

    def test_dedup_actually_removes_rows(self) -> None:
        self.assertLess(len(self.quads), len(self.raw))

    def test_dedup_is_order_independent(self) -> None:
        forward = [q.key for q in cas.dedup_by_target(self.raw)]
        backward = [q.key for q in cas.dedup_by_target(list(reversed(self.raw)))]
        self.assertEqual(forward, backward)

    def test_the_task_is_a_function_of_its_input(self) -> None:
        """No two distinct targets may share one `A <sep> B <sep> C`.

        Dedup is by TARGET, so nothing in it forbids two rows with different
        Ds from carrying byte-identical inputs -- and if any did, the lane
        would be ill-posed (no reader of the input could choose between them)
        and a retrieval baseline could score by exact-input lookup while
        looking like structure transfer. 398 targets over 398 distinct inputs;
        this is the assertion that keeps it that way.
        """
        inputs = [tuple(cas.input_tokens(q)) for q in self.quads]
        self.assertEqual(len(inputs), len(set(inputs)))

    def test_dedup_holds_across_every_split(self) -> None:
        """A target may not appear on both sides of any holdout."""
        for name, assignment in self.splits.items():
            sides: dict[str, set] = {}
            for quad in self.quads:
                sides.setdefault(quad.target, set()).add(assignment[quad.target])
            for target, side in sides.items():
                self.assertEqual(len(side), 1, msg=f"{name}: {target}")


# ---------------------------------------------------------------------------
# bullet 6: verified through the tools, and absent from the input
# ---------------------------------------------------------------------------

class VerificationTests(Fixture):
    def test_specializer_independently_accepts_c_to_d(self) -> None:
        for quad in self.quads:
            ranker = spelling_ranker(self.corpus.node_slots[quad.c_id],
                                     self.corpus.disc_slots[quad.c_discipline])
            proof = Search(self.corpus.classes[quad.c_id],
                           op_count(quad.c_tree), ranker).run(quad.c_tree,
                                                              quad.d_tree)
            self.assertIsNotNone(proof, msg=quad.target)

    def test_no_target_is_an_authored_statement(self) -> None:
        for quad in self.quads:
            self.assertNotIn(quad.target, self.corpus.authored, msg=quad.target)

    def test_target_never_occurs_verbatim_in_the_input(self) -> None:
        for quad in self.quads:
            self.assertFalse(
                cas.contiguous_slice(cas.input_tokens(quad),
                                     cas.serialize(quad.d_tree)),
                msg=quad.target)

    def test_both_constructions_agree_on_every_admitted_row(self) -> None:
        """subst-into-C and translate-B are checked at build time; re-check it
        here so that relaxing the builder cannot quietly drop the cross-check.
        """
        for quad in self.quads:
            self.assertEqual(canonicalize(quad.d_tree), quad.d_tree)

    def test_specialization_ledger_is_load_bearing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "specializations.json"
            empty.write_text('{"specialization_edges": []}\n', encoding="utf-8")
            self.assertEqual(cas.build_quadruples(cas.DATA_DIR, empty), [])

    def test_head_identity_collapses_are_refused_as_unpointable(self) -> None:
        self.assertGreater(self.ledger["head_identity_collapse_not_pointable"], 0)


# ---------------------------------------------------------------------------
# determinism
# ---------------------------------------------------------------------------

class DeterminismTests(Fixture):
    def test_generator_is_deterministic(self) -> None:
        again = cas.dedup_by_target(cas.build_quadruples())
        self.assertEqual([q.key for q in again], [q.key for q in self.quads])

    def test_pointer_rows_are_deterministic(self) -> None:
        first = [json.dumps(cas.pointer_row(q), sort_keys=True) for q in self.quads]
        second = [json.dumps(cas.pointer_row(q), sort_keys=True) for q in self.quads]
        self.assertEqual(first, second)

    def test_split_files_regenerate_byte_identically(self) -> None:
        """The three split files are generated, not committed.

        `experiments/data/` is gitignored by repo policy, so the splits are
        reproduced from this generator rather than stored. That is only safe
        because the split rule takes no seed, and this test is what makes
        "regenerates exactly" a checked claim instead of a hope -- so it must
        not be skippable. An earlier version skipped when the CLI had not been
        run yet, which meant the one guarantee standing in for a committed
        dataset was unchecked on a fresh clone, exactly where it matters most.
        Two independent writes into scratch directories are compared byte for
        byte; the checkout's own files, when present, are compared as well.
        """
        with tempfile.TemporaryDirectory() as one, tempfile.TemporaryDirectory() as two:
            first = cas.write_split_files(self.quads, self.splits, Path(one))
            second = cas.write_split_files(
                cas.dedup_by_target(cas.build_quadruples()), self.splits, Path(two))
            for a, b in zip(first, second):
                self.assertEqual(a.read_bytes(), b.read_bytes(), msg=a.name)
            for path in first:
                live = cas.SPLIT_DIR / path.name
                if live.exists():  # the checkout's copy, if the CLI has run
                    self.assertEqual(live.read_bytes(), path.read_bytes(),
                                     msg=path.name)

    def test_written_rows_carry_the_split_assignment(self) -> None:
        """The file body is the pointer rows plus exactly two split columns."""
        for name, assignment in self.splits.items():
            lines = cas.split_lines(self.quads, assignment, name)
            self.assertEqual(len(lines), len(self.quads), msg=name)
            for quad, line in zip(self.quads, lines):
                row = json.loads(line)
                self.assertEqual(row["holdout_axis"], name)
                self.assertEqual(row["split"], assignment[quad.target])
                self.assertEqual(row["target_tokens"],
                                 list(cas.serialize(quad.d_tree)))


# ---------------------------------------------------------------------------
# bullet 5: the controls, pinned
# ---------------------------------------------------------------------------

class ControlTests(unittest.TestCase):
    """Regression pins for every number in the committed ceiling table.

    These are the tests that would have caught v0.6 a cycle earlier. A split
    can rot silently -- a corpus edit adds one statement, a family stops being
    held out, and a blind rule quietly starts solving the task again -- and the
    only defence is pinning the control scores themselves, not just the shapes.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus = cas.load_corpus(cas.DATA_DIR)
        cls.quads = cas.dedup_by_target(cas.build_quadruples())
        cls.splits = cas.build_splits(cls.quads)
        cls.table = cas.ceiling_table(cls.quads, cls.splits, cls.corpus)

    def test_the_v06_killer_fails_on_every_holdout(self) -> None:
        """P-CS1. The rule that scored 1.000 on the v0.6 lane.

        This is the single assertion that says the replacement worked. If it
        ever rises, the lane has regressed to a positional trick and must be
        reported as such rather than repaired in place.
        """
        for name, entry in self.table.items():
            self.assertLessEqual(entry["blind"]["last_slot_number_transfer"],
                                 0.05, msg=name)

    def test_blind_ceiling_is_below_one_on_every_holdout(self) -> None:
        """P-CS7 and the roadmap's acceptance condition."""
        for name, entry in self.table.items():
            self.assertLess(entry["blind_ceiling"], 1.0, msg=name)

    def test_ceilings_match_the_committed_numbers(self) -> None:
        expected = {
            "family": (0.4000, "nearest_template_transfer"),
            "discipline": (0.9318, "nearest_template_transfer"),
            "vocabulary": (0.3976, "nearest_template_transfer"),
        }
        for name, (value, control) in expected.items():
            self.assertAlmostEqual(self.table[name]["blind_ceiling"], value,
                                   places=3, msg=name)
            self.assertEqual(self.table[name]["blind_ceiling_control"], control)

    def test_the_symbolic_roof_is_exactly_the_declared_slot_classes(self) -> None:
        """P-CS2 adjudicated. The residual is metadata, not difficulty.

        `symbolic_typed_input` differs from `symbolic_input_only` in exactly
        two corpus declarations -- the parameter/variable class of each slot
        and the identity table -- and reaching 1.000 with them while falling
        to 0.46-0.65 without them locates the whole gap there.
        """
        for name, entry in self.table.items():
            self.assertEqual(entry["sighted"]["symbolic_oracle"], 1.0, msg=name)
            self.assertEqual(entry["sighted"]["symbolic_typed_input"], 1.0,
                             msg=name)
            self.assertLess(entry["sighted"]["symbolic_input_only"], 0.70,
                            msg=name)
            self.assertGreater(entry["sighted"]["symbolic_input_only"], 0.40,
                               msg=name)

    def test_shuffling_c_collapses_every_control(self) -> None:
        """P-CS5. A control that survives the shuffle was not reading C."""
        for name, entry in self.table.items():
            for control, value in entry["shuffled_c_leaves"].items():
                self.assertLessEqual(value, 0.05, msg=f"{name}/{control}")

    def test_novelty_sanity_controls_are_pinned_at_zero(self) -> None:
        """They CANNOT exceed zero: admission forbids it.

        v0.6 reported these as capability baselines and review corrected it.
        They are kept, at zero, as vacuity checks, and excluded from the
        ceiling so the correction cannot be un-made by accident.
        """
        for name, entry in self.table.items():
            for control in sorted(cas.NOVELTY_SANITY):
                self.assertEqual(entry["blind"][control], 0.0,
                                 msg=f"{name}/{control}")

    def test_no_blind_control_can_see_the_answer(self) -> None:
        """The capability-blind claim, executed rather than asserted.

        Every control is handed the whole `Quadruple`, and a `Quadruple` owns
        `d_tree` -- so "blind" was, structurally, a promise about what the eight
        functions happen to read. Reading them is not proof. This poisons the
        answer on every HELD row (D replaced by another row's D, which also
        poisons the derived `target`, plus both leaf-provenance tuples) and
        requires the guesses to be unchanged token for token. A control that
        peeked at the label -- directly, or through `pointer_row`, which is how
        a training-pattern control could leak if it were ever pointed at the
        query row -- returns something different here and fails.

        Training rows are left intact: replaying a training row's realization
        is the baseline's whole point, and those labels are legitimately theirs.
        """
        for name, assignment in self.splits.items():
            train = [q for q in self.quads if assignment[q.target] == "train"]
            held = [q for q in self.quads if assignment[q.target] == "holdout"]
            blind_ctx, _ = cas.build_context(train, self.corpus)
            poisoned = [
                cas.Quadruple(**{**q.__dict__,
                                 "d_tree": held[(i + 1) % len(held)].d_tree,
                                 "expansion_leaves": (),
                                 "renamed_leaves": ()})
                for i, q in enumerate(held)]
            for clean_q, dirty_q in zip(held, poisoned):
                # EVERY row must be poisoned, not merely the list as a whole:
                # one unpoisoned row is one row where the check is vacuous.
                self.assertNotEqual(clean_q.target, dirty_q.target, msg=name)
            for ctl_name, control in cas.BLIND_CONTROLS.items():
                clean = [control(q, blind_ctx) for q in held]
                dirty = [control(q, blind_ctx) for q in poisoned]
                self.assertEqual(clean, dirty, msg=f"{name}/{ctl_name}")

    def test_the_blind_context_does_not_carry_corpus_metadata(self) -> None:
        """The blind context is a different object, not the same one trusted."""
        train = [q for q in self.quads
                 if self.splits["family"][q.target] == "train"]
        blind_ctx, sighted_ctx = cas.build_context(train, self.corpus)
        self.assertNotIn("corpus", blind_ctx)
        self.assertIs(sighted_ctx["corpus"], self.corpus)

    def test_the_blind_ceiling_is_untyped_shape_leakage(self) -> None:
        """The finding that explains all three ceilings.

        Families are TYPED skeletons, so `*(?1:P, ?2:V)` and `*(?1:V, ?2:V)`
        are two families and one shape. Nearest-template replay scores 1.000
        exactly where a holdout row's untyped shape is still in training and
        ~0.10 where it is not -- so the ceiling is measuring a hole in the
        split, not a capability. The strict ceiling is the unseen-shape column.
        """
        for name, entry in self.table.items():
            leak = entry["shape_leak"]
            self.assertGreater(leak["nearest_template_on_leaky_shapes"],
                               leak["nearest_template_on_unseen_shapes"],
                               msg=name)
            self.assertLessEqual(leak["nearest_template_on_unseen_shapes"],
                                 0.15, msg=name)

    def test_committed_ceiling_report_is_not_stale(self) -> None:
        path = (ROOT / "experiments" / "results" /
                "corpus_analogy_v07_ceilings.json")
        if not path.exists():
            self.skipTest("ceiling report not built yet")
        committed = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(committed["distinct_targets"], len(self.quads))
        self.assertEqual(committed["rows_before_dedup"], 914)
        self.assertEqual(committed["families"], 11)
        self.assertEqual(committed["untyped_shapes"], 10)
        for name, entry in self.table.items():
            self.assertAlmostEqual(committed["ceilings"][name]["blind_ceiling"],
                                   entry["blind_ceiling"], places=9, msg=name)


if __name__ == "__main__":
    unittest.main()
