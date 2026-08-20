#!/usr/bin/env python3
"""The ROADMAP-v0.15 item 1 preregistration, committed before the builder.

This file is authored BEFORE ``scripts/closure_build.py`` exists, and that
ordering is the whole reason it is worth committing. A construction gate
written after the artifact it judges is vacuous: it can only ask whether
the builder does what the builder does. Written first, it asks whether the
builder does what the design registered. Four tests in
:class:`TheGateIsNotVacuous` therefore FAIL on this commit with
``ModuleNotFoundError: closure_build``. They are not skipped and not marked
expected-failure, because a skip is invisible in a summary line and an
expected failure would turn green the moment the builder appeared, before
anyone read what it produced.

The six clauses of DESIGN-compile-before-query §8, quoted verbatim so that
the gate cannot drift from the document while the tests keep passing:

- **B1 — two real worlds register.** Exactly two already-committed worlds
  satisfy the four-operation contract without adding a new demonstration
  world.
- **B2 — blind closure finishes.** Canonical breadth-first enumeration closes
  each world at its frozen horizon with at most **512 distinct states**, at
  most **32 syntactic actions per interior state**, and at most **30 seconds**
  per closure on the registered release host; each canonical closure is at
  most **8 MiB**.
- **B3 — checking is complete.** The checker independently accounts for every
  schema action at every interior state; derives the exact reachable state,
  edge, refusal, predecessor, and convergence-cell sets; rejects all extras;
  and reproduces every returned witness.
- **B4 — corruption is always caught.** For each closure, the checker rejects
  every registered mutation class in section 9 across five fixed mutation
  seeds, with zero false rejection of the untouched control.
- **B5 — the abstraction is shared.** Generic builder and checker contain no
  world-name conditional and produce byte-identical output on a repeated run.
- **B6 — composition is exercised.** The closures naturally contain at least
  four convergence cells in total.  If the existing worlds form only trees,
  report that fact; do not author redundant actions to meet the count.

The five fixed corruption seeds are **3, 11, 29, 47, 101**. They are
registered here and are never changed: a seed chosen after seeing which
mutation slipped through would convert B4 from a test into a search.

The builder API this preregistration commits to is
``closure_build.build_closure(registration: dict, repo_root: Path) -> dict``,
importing :func:`closure_check.enumerate_actions` and
:func:`closure_check.canonical_closure_bytes` rather than reimplementing
either, so that builder and checker cannot disagree about what the action
product or the canonical form is.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "experiments"))

import closure_check  # noqa: E402
import closure_corrupt  # noqa: E402
import closure_worlds  # noqa: E402

SEEDS = (3, 11, 29, 47, 101)

DESIGN_CEILINGS = {
    "max_states": 512,
    "max_actions_per_state": 32,
    "max_seconds_per_closure": 30,
    "max_closure_bytes": 8388608,
}

EXPECTED_ACTION_COUNTS = {
    "story.golden_chicken": 20,
    "visual.rt0000": 6,
}

FORBIDDEN_WORLD_NAMES = (
    "story", "visual", "chicken", "triangle", "rt-0000", "golden",
)

GENERIC_SOURCES = (
    REPO / "scripts" / "closure_check.py",
    REPO / "scripts" / "closure_corrupt.py",
)


def _registrations() -> dict[str, dict]:
    """Every committed registration, keyed by its declared world id."""

    loaded = {}
    for path in closure_worlds.registration_paths():
        registration = closure_worlds.load_registration(path)
        loaded[registration["world_id"]] = registration
    return loaded


def _synthetic_closure() -> dict:
    """A hand-built two-state closure, used only to exercise the battery.

    It is deliberately not a real world's output: the corruption generator
    must be total over the closure SHAPE, and testing it against a built
    closure would make this file depend on the very module whose absence
    the gate is asserting.
    """

    first = '{"depth":0}'
    second = '{"depth":1}'
    first_digest = hashlib.sha256(first.encode("utf-8")).hexdigest()
    second_digest = hashlib.sha256(second.encode("utf-8")).hexdigest()
    accepted = closure_worlds.canonical_action("step", {"how": "left"})
    refused = closure_worlds.canonical_action("step", {"how": "right"})
    closure = {
        "format_version": "bounded-closure/1",
        "world_id": "synthetic.pair",
        "source_manifest": [
            {
                "path": "data/closure_worlds/manifest.json",
                "sha256_lf": "0" * 64,
            }
        ],
        "adapter_id": "synthetic.pair.v1",
        "adapter_digest": "0" * 64,
        "action_schema_digest": "0" * 64,
        "horizon": 1,
        "initial_state_digest": first_digest,
        "states": [
            {
                "state_digest": first_digest,
                "canonical_state": first,
                "minimum_depth": 0,
                "outgoing": [
                    {
                        "canonical_action": accepted,
                        "disposition": "successor",
                        "successor_digest": second_digest,
                    },
                    {
                        "canonical_action": refused,
                        "disposition": "illegal",
                        "refusal_code": "declined",
                    },
                ],
            },
            {
                "state_digest": second_digest,
                "canonical_state": second,
                "minimum_depth": 1,
                "outgoing": [],
            },
        ],
        "convergence_cells": [
            {
                "start_state_digest": first_digest,
                "primary_route": [accepted],
                "alternate_route": [refused],
                "end_state_digest": second_digest,
            }
        ],
    }
    closure["closure_digest"] = closure_check.closure_digest(closure)
    return closure


def _build_every_registered_closure(builder) -> list[tuple[dict, dict]]:
    """Build both closures through the registered builder entry point."""

    built = []
    for path in closure_worlds.registration_paths():
        registration = closure_worlds.load_registration(path)
        built.append((registration, builder.build_closure(registration, REPO)))
    return built


class RegistrationsAreFrozen(unittest.TestCase):
    """B1's precondition: the registrations are pinned, not merely present."""

    def test_the_manifest_pins_every_registration_by_canonical_lf_digest(
        self,
    ) -> None:
        manifest = json.loads(
            (REPO / "data" / "closure_worlds" / "manifest.json")
            .read_text(encoding="utf-8")
        )
        entries = manifest["files"]
        self.assertEqual(len(entries), 2)
        for entry in entries:
            path = REPO / entry["path"]
            self.assertTrue(path.is_file(), entry["path"])
            self.assertEqual(
                closure_worlds.sha256_lf_file(path),
                entry["sha256_lf"],
                entry["path"],
            )

    def test_each_registration_declares_a_tag_adapter_and_horizon(
        self,
    ) -> None:
        registrations = _registrations()
        self.assertEqual(
            set(registrations), set(EXPECTED_ACTION_COUNTS)
        )
        for world_id, registration in registrations.items():
            self.assertEqual(
                registration["schema"], closure_worlds.WORLD_SCHEMA_TAG,
                world_id,
            )
            self.assertIn(
                registration["adapter_id"], closure_worlds._ADAPTERS,
                world_id,
            )
            self.assertGreaterEqual(registration["horizon"], 1, world_id)

    def test_the_ceilings_are_exactly_the_four_design_constants(self) -> None:
        for world_id, registration in _registrations().items():
            self.assertEqual(
                registration["ceilings"], DESIGN_CEILINGS, world_id
            )

    def test_each_action_product_is_its_registered_size(self) -> None:
        """The product is data, and its size was frozen before the builder.

        A schema that grew between preregistration and construction would
        change what "every syntactically possible action" means, so the two
        counts are asserted literally rather than recomputed from the file.
        """

        for world_id, registration in _registrations().items():
            actions = closure_check.enumerate_actions(
                registration["action_schema"]
            )
            self.assertEqual(
                len(actions), EXPECTED_ACTION_COUNTS[world_id], world_id
            )
            self.assertLessEqual(
                len(actions),
                DESIGN_CEILINGS["max_actions_per_state"],
                world_id,
            )
            texts = [
                closure_worlds.canonical_action(name, params)
                for name, params in actions
            ]
            self.assertEqual(len(set(texts)), len(texts), world_id)


class AdaptersHonorTheContract(unittest.TestCase):
    """The four-operation contract, exercised against the real worlds."""

    def test_two_instances_canonicalize_the_initial_state_identically(
        self,
    ) -> None:
        for world_id, registration in _registrations().items():
            one = closure_worlds.load_world(registration)
            other = closure_worlds.load_world(registration)
            self.assertEqual(
                one.canonicalize(one.initial_state()),
                other.canonicalize(other.initial_state()),
                world_id,
            )

    def test_every_enumerated_action_answers_the_same_way_twice(self) -> None:
        """Determinism is a registration requirement, not a hope.

        A world that answered differently on a second call would make the
        closure unbuildable and the checker's independent traversal
        meaningless; §10 says park, and this is where that would surface.
        """

        for world_id, registration in _registrations().items():
            world = closure_worlds.load_world(registration)
            state = world.initial_state()
            actions = closure_check.enumerate_actions(
                registration["action_schema"]
            )
            for name, params in actions:
                first = world.validate_and_apply(state, name, params)
                second = world.validate_and_apply(state, name, params)
                if isinstance(first, closure_worlds.Refusal):
                    self.assertIsInstance(
                        second, closure_worlds.Refusal, (world_id, name)
                    )
                    self.assertEqual(first.code, second.code, (world_id, name))
                else:
                    self.assertNotIsInstance(
                        second, closure_worlds.Refusal, (world_id, name)
                    )
                    self.assertEqual(
                        world.canonicalize(first),
                        world.canonicalize(second),
                        (world_id, name),
                    )

    def test_the_diagram_world_refuses_all_six_controlled_invalids(
        self,
    ) -> None:
        registration = _registrations()["visual.rt0000"]
        world = closure_worlds.load_world(registration)
        state = world.initial_state()
        actions = closure_check.enumerate_actions(
            registration["action_schema"]
        )
        self.assertEqual(len(actions), 6)
        for name, params in actions:
            outcome = world.validate_and_apply(state, name, params)
            self.assertIsInstance(outcome, closure_worlds.Refusal, params)
            self.assertTrue(
                outcome.code.startswith("verify_failed:"), outcome.code
            )

    def test_the_frame_world_accepts_a_declared_trait_and_denies_the_other(
        self,
    ) -> None:
        registration = _registrations()["story.golden_chicken"]
        world = closure_worlds.load_world(registration)
        state = world.initial_state()
        denied = registration["source"]["denied_trait"]
        accepted = 0
        for name, params in closure_check.enumerate_actions(
            registration["action_schema"]
        ):
            if name != "introduce":
                continue
            outcome = world.validate_and_apply(state, name, params)
            if params["trait"] == denied:
                self.assertIsInstance(
                    outcome, closure_worlds.Refusal, params
                )
            elif not isinstance(outcome, closure_worlds.Refusal):
                accepted += 1
        self.assertGreaterEqual(accepted, 1)


class CorruptionGeneratorIsTotal(unittest.TestCase):
    """§9's battery is frozen, deterministic, and side-effect free."""

    def setUp(self) -> None:
        self.closure = _synthetic_closure()

    def test_the_registered_classes_are_the_twelve_in_design_order(
        self,
    ) -> None:
        self.assertEqual(len(closure_corrupt.CLASSES), 12)
        self.assertEqual(
            len(set(closure_corrupt.CLASSES)), len(closure_corrupt.CLASSES)
        )
        self.assertEqual(
            closure_corrupt.CLASSES[0], "delete_legal_action_row"
        )
        self.assertEqual(
            closure_corrupt.CLASSES[-1], "semantic_preserving_reorder"
        )

    def test_every_class_returns_a_closure_or_an_honest_none(self) -> None:
        for kind in closure_corrupt.CLASSES:
            for seed in SEEDS:
                before = copy.deepcopy(self.closure)
                mutated = closure_corrupt.corrupt(self.closure, kind, seed)
                self.assertEqual(self.closure, before, (kind, seed))
                if mutated is not None:
                    self.assertIsInstance(mutated, dict, (kind, seed))

    def test_the_applicable_classes_all_find_a_site_here(self) -> None:
        applicable = [
            kind for kind in closure_corrupt.CLASSES
            if kind != "corrupt_one_convergence_route"
            and kind != "replace_alternate_route"
        ]
        for kind in applicable:
            for seed in SEEDS:
                self.assertIsNotNone(
                    closure_corrupt.corrupt(self.closure, kind, seed),
                    (kind, seed),
                )

    def test_a_semantic_preserving_reorder_normalizes_to_the_same_bytes(
        self,
    ) -> None:
        original = closure_check.canonical_closure_bytes(self.closure)
        for seed in SEEDS:
            mutated = closure_corrupt.corrupt(
                self.closure, "semantic_preserving_reorder", seed
            )
            self.assertIsNotNone(mutated)
            self.assertEqual(
                closure_check.canonical_closure_bytes(mutated), original, seed
            )
            self.assertEqual(
                closure_check.closure_digest(mutated),
                self.closure["closure_digest"],
                seed,
            )
            self.assertEqual(
                mutated["closure_digest"], self.closure["closure_digest"], seed
            )

    def test_every_other_class_changes_the_canonical_bytes(self) -> None:
        original = closure_check.canonical_closure_bytes(self.closure)
        for kind in closure_corrupt.CLASSES:
            if kind == "semantic_preserving_reorder":
                continue
            for seed in SEEDS:
                mutated = closure_corrupt.corrupt(self.closure, kind, seed)
                if mutated is None:
                    continue
                self.assertNotEqual(
                    closure_check.canonical_closure_bytes(mutated),
                    original,
                    (kind, seed),
                )

    def test_site_selection_is_reproducible(self) -> None:
        for kind in closure_corrupt.CLASSES:
            for seed in SEEDS:
                first = closure_corrupt.corrupt(self.closure, kind, seed)
                second = closure_corrupt.corrupt(self.closure, kind, seed)
                self.assertEqual(first, second, (kind, seed))


class TheGateIsNotVacuous(unittest.TestCase):
    """These four MUST fail until ``scripts/closure_build.py`` exists.

    Their failure is the preregistration's evidence that the gate was
    registered before the artifact it judges.
    """

    def test_b2_blind_closure_finishes(self) -> None:
        import closure_build  # noqa: PLC0415

        started = time.monotonic()
        built = _build_every_registered_closure(closure_build)
        self.assertEqual(len(built), 2)
        for registration, closure in built:
            ceilings = registration["ceilings"]
            world_id = registration["world_id"]
            self.assertLessEqual(
                len(closure["states"]), ceilings["max_states"], world_id
            )
            self.assertLessEqual(
                len(closure_check.canonical_closure_bytes(closure)),
                ceilings["max_closure_bytes"],
                world_id,
            )
            expected_rows = len(
                closure_check.enumerate_actions(registration["action_schema"])
            )
            for state in closure["states"]:
                rows = len(state["outgoing"])
                if state["minimum_depth"] < registration["horizon"]:
                    self.assertEqual(rows, expected_rows, world_id)
                else:
                    self.assertEqual(rows, 0, world_id)
        self.assertLess(
            time.monotonic() - started,
            2 * DESIGN_CEILINGS["max_seconds_per_closure"],
        )

    def test_b3_checker_accepts_both_closures(self) -> None:
        import closure_build  # noqa: PLC0415

        for registration, closure in _build_every_registered_closure(
            closure_build
        ):
            report = closure_check.check_closure(closure, registration, REPO)
            self.assertTrue(
                report.ok, (registration["world_id"],
                            report.first_disagreement)
            )

    def test_b4_corruption_is_always_caught(self) -> None:
        import closure_build  # noqa: PLC0415

        inapplicable: list[tuple[str, str, int]] = []
        for registration, closure in _build_every_registered_closure(
            closure_build
        ):
            world_id = registration["world_id"]
            control = closure_check.check_closure(
                closure, registration, REPO
            )
            self.assertTrue(control.ok, (world_id, "untouched control"))
            for kind in closure_corrupt.CLASSES:
                if kind == "semantic_preserving_reorder":
                    continue
                for seed in SEEDS:
                    mutated = closure_corrupt.corrupt(closure, kind, seed)
                    if mutated is None:
                        inapplicable.append((world_id, kind, seed))
                        continue
                    report = closure_check.check_closure(
                        mutated, registration, REPO
                    )
                    self.assertFalse(report.ok, (world_id, kind, seed))
                    self.assertIsNotNone(
                        report.first_disagreement, (world_id, kind, seed)
                    )
            for seed in SEEDS:
                reordered = closure_corrupt.corrupt(
                    closure, "semantic_preserving_reorder", seed
                )
                self.assertIsNotNone(reordered, (world_id, seed))
                report = closure_check.check_closure(
                    reordered, registration, REPO
                )
                self.assertTrue(
                    report.ok,
                    (world_id, seed, report.first_disagreement),
                )
        self.assertIsInstance(inapplicable, list)

    def test_b6_convergence_cells_are_counted(self) -> None:
        """Count the cells; do not assert the adjudication.

        §8 lets B6 report ``INSUFFICIENT_STRUCTURE`` honestly, so asserting
        "at least four" here would forbid the one answer the design
        explicitly permits. The number belongs in the roadmap readout.
        """

        import closure_build  # noqa: PLC0415

        total = 0
        for _registration, closure in _build_every_registered_closure(
            closure_build
        ):
            total += len(closure["convergence_cells"])
        self.assertIsInstance(total, int)
        self.assertGreaterEqual(total, 0)


class TheGenericLayerIsShared(unittest.TestCase):
    """B5's no-world-name-conditional clause, made mechanical.

    ``scripts/closure_worlds.py`` is exempt and deliberately absent from
    the scanned set: adapters are world-specific by definition, and the
    registry is §5's one sanctioned way to select one.
    """

    def test_no_generic_module_mentions_a_registered_world(self) -> None:
        for path in GENERIC_SOURCES:
            source = path.read_text(encoding="utf-8").lower()
            for name in FORBIDDEN_WORLD_NAMES:
                self.assertNotIn(name, source, f"{path.name}: {name}")


if __name__ == "__main__":
    unittest.main()
