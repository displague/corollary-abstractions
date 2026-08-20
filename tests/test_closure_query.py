#!/usr/bin/env python3
"""What a query receipt is allowed to claim, tested against sealed closures.

Every test here runs against the two closures already committed under
``reports/closures/`` — the ones §7 requires be built, checked, and sealed
*before* any person names a target. That ordering is the reason these tests
are worth running: the targets below are extracted from the closure files
themselves at test time, so no target could have steered what was compiled.

The four properties under test are the four §3 asks a query to have:

* a present target answers with a route the WORLD replays, not merely one
  the file asserts (:class:`AReachableTargetReplays`,
  :class:`ReplayIsLoadBearing`);
* an absent target answers with a negative that carries its horizon
  (:class:`AnAbsentTargetKeepsItsBound`);
* a digest match with unequal canonical bytes is refused as corruption
  rather than answered either way
  (:class:`ADigestMatchWithWrongBytesIsRefused`);
* a closure that is not the closure it names answers nothing at all
  (:class:`ATamperedClosureAnswersNothing`).

Two of these need a closure that lies. Both build one by mutating an
in-memory copy **and re-sealing its** ``closure_digest``, which is the only
adversary worth testing: an unsealed forgery is caught by the digest recompute
before the query looks at a single target byte, so testing against one would
prove nothing about the branches below it. A re-sealed forgery is exactly what
:mod:`closure_check` exists to reject and what a query, which cannot rebuild
the world, must survive without emitting a confident receipt.
"""

from __future__ import annotations

import copy
import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "experiments"))

import closure_check  # noqa: E402
import closure_query  # noqa: E402
import closure_worlds  # noqa: E402

CLOSURE_DIR = REPO / "reports" / "closures"
FRAME_CLOSURE = CLOSURE_DIR / "story.golden_chicken.closure.json"
DIAGRAM_CLOSURE = CLOSURE_DIR / "visual.rt0000.closure.json"

RECEIPT_SCHEMA = json.loads(
    (REPO / "schema" / "closure-receipt.schema.json").read_text(
        encoding="utf-8"
    )
)
HEX64 = re.compile(r"^[0-9a-f]{64}$")

try:  # optional: the structural assertions below stand without it
    import jsonschema  # noqa: E402
except ImportError:  # pragma: no cover - exercised only on a bare host
    jsonschema = None


def _load(path: Path) -> dict:
    return closure_check.load_closure(path)


def _registration(closure: dict) -> dict:
    return closure_query.find_registration(closure["world_id"])


def _state_at_depth(closure: dict, depth: int) -> dict:
    """The lexicographically first state record at ``depth``, from the file.

    Chosen by digest order rather than by hand so that the target is a
    function of the sealed closure alone. A maintainer cannot make this test
    easier by picking a friendlier endpoint.
    """

    candidates = sorted(
        (state for state in closure["states"]
         if state["minimum_depth"] == depth),
        key=lambda state: state["state_digest"],
    )
    if not candidates:
        raise AssertionError(f"no committed state at minimum_depth {depth}")
    return candidates[0]


def _reseal(closure: dict) -> dict:
    """Re-stamp a mutated copy's ``closure_digest`` so it looks intact."""

    closure[closure_check.DIGEST_KEY] = closure_check.closure_digest(closure)
    return closure


class ReceiptStructure(unittest.TestCase):
    """Shared structural assertions against the committed receipt schema."""

    def assert_receipt_is_well_formed(self, receipt: dict) -> None:
        properties = RECEIPT_SCHEMA["properties"]
        self.assertEqual(
            set(receipt) - set(properties), set(),
            "the schema declares additionalProperties: false",
        )
        for field in RECEIPT_SCHEMA["required"]:
            self.assertIn(field, receipt)
        self.assertEqual(receipt["schema"], properties["schema"]["const"])
        self.assertIn(receipt["outcome"], properties["outcome"]["enum"])
        for field in ("closure_digest", "target_digest"):
            self.assertRegex(receipt[field], HEX64, field)
        self.assertRegex(
            receipt["world_id"], properties["world_id"]["pattern"]
        )
        self.assertRegex(
            receipt["adapter_id"], properties["adapter_id"]["pattern"]
        )
        self.assertIsInstance(receipt["horizon"], int)
        self.assertGreaterEqual(receipt["horizon"], 1)
        self.assertIsInstance(receipt["visited_states"], int)
        self.assertGreaterEqual(receipt["visited_states"], 1)
        if receipt["outcome"] == closure_query.REACHABLE:
            self.assertIn("shortest_route", receipt)
            self.assertIsInstance(receipt["shortest_route"], list)
            for action_text in receipt["shortest_route"]:
                self.assertIsInstance(action_text, str)
        else:
            self.assertNotIn(
                "shortest_route", receipt,
                "a route may only accompany REACHABLE",
            )
        if jsonschema is not None:
            jsonschema.validate(receipt, RECEIPT_SCHEMA)
        # The receipt must survive the round trip it will be quoted through.
        self.assertEqual(
            json.loads(closure_query.serialize_receipt(receipt)), receipt
        )


class AReachableTargetReplays(ReceiptStructure):
    """§3's positive answer: a shortest route the world itself walks."""

    def test_a_depth_three_target_answers_with_a_three_action_route(
        self,
    ) -> None:
        closure = _load(FRAME_CLOSURE)
        target = _state_at_depth(closure, 3)
        target_bytes = target["canonical_state"].encode("utf-8")

        receipt = closure_query.query(
            closure, _registration(closure), target_bytes, REPO
        )

        self.assert_receipt_is_well_formed(receipt)
        self.assertEqual(receipt["outcome"], closure_query.REACHABLE)
        self.assertEqual(
            len(receipt["shortest_route"]), 3,
            "the route must be as short as the recorded minimum depth",
        )
        self.assertEqual(
            receipt["target_digest"], target["state_digest"],
            "the receipt names the digest of the supplied bytes",
        )
        self.assertEqual(receipt["closure_digest"],
                         closure[closure_check.DIGEST_KEY])
        self.assertEqual(receipt["visited_states"], len(closure["states"]))
        self.assertEqual(receipt["horizon"], closure["horizon"])

    def test_every_route_action_is_an_accepted_edge_of_the_closure(
        self,
    ) -> None:
        """The route is derived from the file, not invented beside it."""

        closure = _load(FRAME_CLOSURE)
        target = _state_at_depth(closure, 3)
        receipt = closure_query.query(
            closure, _registration(closure),
            target["canonical_state"].encode("utf-8"), REPO,
        )

        edges = closure_query.accepted_edges(closure)
        digest = closure["initial_state_digest"]
        for action_text in receipt["shortest_route"]:
            successors = dict(edges[digest])
            self.assertIn(action_text, successors)
            digest = successors[action_text]
        self.assertEqual(digest, target["state_digest"])

    def test_the_route_is_canonical_across_repeated_queries(self) -> None:
        closure = _load(FRAME_CLOSURE)
        registration = _registration(closure)
        target_bytes = _state_at_depth(closure, 3)[
            "canonical_state"
        ].encode("utf-8")
        first = closure_query.query(
            closure, registration, target_bytes, REPO
        )
        second = closure_query.query(
            _load(FRAME_CLOSURE), registration, target_bytes, REPO
        )
        self.assertEqual(first, second)


class AnAbsentTargetKeepsItsBound(ReceiptStructure):
    """§3's only negative, and §7's refusal to let it be quoted bare."""

    def _fabricated_target(self, closure: dict) -> bytes:
        initial = next(
            state for state in closure["states"]
            if state["state_digest"] == closure["initial_state_digest"]
        )
        return initial["canonical_state"].encode("utf-8") + b"\n<fabricated>"

    def test_a_fabricated_target_is_bounded_not_denied(self) -> None:
        closure = _load(FRAME_CLOSURE)
        target_bytes = self._fabricated_target(closure)

        receipt = closure_query.query(
            closure, _registration(closure), target_bytes, REPO
        )

        self.assert_receipt_is_well_formed(receipt)
        self.assertEqual(receipt["outcome"], closure_query.NOT_REACHABLE)
        self.assertNotIn("shortest_route", receipt)
        self.assertEqual(
            receipt["target_digest"],
            closure_worlds.sha256_hex(target_bytes),
        )

    def test_the_display_names_the_horizon_and_never_the_bare_negative(
        self,
    ) -> None:
        closure = _load(FRAME_CLOSURE)
        receipt = closure_query.query(
            closure, _registration(closure),
            self._fabricated_target(closure), REPO,
        )
        text = "\n".join(
            closure_query.display_lines(receipt, closure, Path("q.json"))
        )
        self.assertIn(
            f"not reachable within horizon {closure['horizon']}", text
        )
        self.assertNotIn("impossible", text.lower())
        for expected in (
            closure[closure_check.DIGEST_KEY],
            closure["adapter_id"],
            str(len(closure["states"])),
            closure["source_manifest"][0]["path"],
        ):
            self.assertIn(expected, text)


class ADigestMatchWithWrongBytesIsRefused(ReceiptStructure):
    """§3: "A digest match with unequal canonical bytes is refused as
    corruption." Neither present nor absent — a third, named outcome."""

    def _forged(self, closure: dict) -> tuple[dict, bytes]:
        """A re-sealed closure whose record disagrees with its own digest.

        The record keeps its ``state_digest`` and loses its bytes, so the
        query's lookup succeeds on digest and fails on bytes — precisely the
        branch under test. Re-sealing is required: without it the digest
        recompute refuses first and this branch is never reached, which is
        itself asserted below so the construction cannot rot into a no-op.
        """

        forged = copy.deepcopy(closure)
        target = _state_at_depth(forged, 2)
        original_bytes = target["canonical_state"].encode("utf-8")
        for record in forged["states"]:
            if record["state_digest"] == target["state_digest"]:
                record["canonical_state"] = (
                    record["canonical_state"] + " "
                )
        return _reseal(forged), original_bytes

    def test_the_forged_record_still_carries_the_targets_digest(self) -> None:
        """Guard on the construction: it must exercise the branch it claims."""

        forged, original_bytes = self._forged(_load(FRAME_CLOSURE))
        digest = closure_worlds.sha256_hex(original_bytes)
        record = next(
            state for state in forged["states"]
            if state["state_digest"] == digest
        )
        self.assertNotEqual(
            record["canonical_state"].encode("utf-8"), original_bytes
        )
        self.assertEqual(
            forged[closure_check.DIGEST_KEY],
            closure_check.closure_digest(forged),
            "an unsealed forgery would be refused before this branch",
        )

    def test_the_query_answers_corrupt_target_and_offers_no_route(
        self,
    ) -> None:
        forged, original_bytes = self._forged(_load(FRAME_CLOSURE))

        receipt = closure_query.query(
            forged, _registration(forged), original_bytes, REPO
        )

        self.assert_receipt_is_well_formed(receipt)
        self.assertEqual(receipt["outcome"], closure_query.CORRUPT_TARGET)
        self.assertNotIn("shortest_route", receipt)

    def test_the_independent_checker_rejects_the_same_forgery(self) -> None:
        """The query refuses locally; §5's checker names the break globally."""

        forged, _bytes = self._forged(_load(FRAME_CLOSURE))
        report = closure_check.check_closure(
            forged, _registration(forged), REPO
        )
        self.assertFalse(report.ok)
        self.assertIsNotNone(report.first_disagreement)


class ReplayIsLoadBearing(unittest.TestCase):
    """A route the file asserts but the world will not walk is no answer."""

    def _closure_with_a_forged_shortcut(self) -> tuple[dict, bytes]:
        """Repoint the initial state's first accepted edge at the target.

        This makes the closure claim a one-action route to a state whose
        recorded minimum depth is three. Breadth-first search over the
        forged edges therefore returns that single action, and applying it
        through the world's own verifier lands somewhere else — so replay,
        and only replay, can catch it.
        """

        closure = _load(FRAME_CLOSURE)
        target = _state_at_depth(closure, 3)
        target_bytes = target["canonical_state"].encode("utf-8")
        initial = next(
            state for state in closure["states"]
            if state["state_digest"] == closure["initial_state_digest"]
        )
        accepted = sorted(
            (row for row in initial["outgoing"]
             if row["disposition"] == "successor"),
            key=lambda row: row["canonical_action"],
        )
        self.assertTrue(accepted, "the initial state accepts something")
        self.assertNotEqual(
            accepted[0]["successor_digest"], target["state_digest"]
        )
        accepted[0]["successor_digest"] = target["state_digest"]
        return _reseal(closure), target_bytes

    def test_a_forged_shortcut_raises_instead_of_claiming_reachable(
        self,
    ) -> None:
        forged, target_bytes = self._closure_with_a_forged_shortcut()

        routes = closure_query.canonical_routes(forged)
        self.assertEqual(
            len(routes[closure_worlds.sha256_hex(target_bytes)]), 1,
            "the forgery must actually shorten the derived route",
        )
        with self.assertRaises(closure_query.ReplayDisagreement):
            closure_query.query(
                forged, _registration(forged), target_bytes, REPO
            )

    def test_the_honest_closure_replays_the_same_route_it_records(
        self,
    ) -> None:
        closure = _load(FRAME_CLOSURE)
        target = _state_at_depth(closure, 3)
        route = closure_query.canonical_routes(closure)[
            target["state_digest"]
        ]
        closure_query.replay(
            _registration(closure), route,
            target["canonical_state"].encode("utf-8"),
        )


class ATamperedClosureAnswersNothing(unittest.TestCase):
    """A closure that is not the closure it names is not asked anything."""

    def test_a_tampered_closure_digest_refuses_before_any_lookup(self) -> None:
        closure = _load(FRAME_CLOSURE)
        target_bytes = _state_at_depth(closure, 3)[
            "canonical_state"
        ].encode("utf-8")
        closure[closure_check.DIGEST_KEY] = "0" * 64

        with self.assertRaises(closure_query.CorruptClosure):
            closure_query.query(
                closure, _registration(closure), target_bytes, REPO
            )

    def test_a_closure_queried_against_another_world_refuses(self) -> None:
        closure = _load(FRAME_CLOSURE)
        other = _load(DIAGRAM_CLOSURE)
        target_bytes = _state_at_depth(closure, 3)[
            "canonical_state"
        ].encode("utf-8")

        with self.assertRaises(closure_query.WrongWorld):
            closure_query.query(
                closure, _registration(other), target_bytes, REPO
            )


class TheInitialStateIsReachableByTheEmptyRoute(ReceiptStructure):
    """The one-state closure, and the route length its answer must have.

    Its only state IS the initial state, so the honest shortest route is the
    empty one. The receipt schema's ``shortest_route`` is a plain array with
    no ``minItems`` — deliberately not a ``$ref`` to the action-route
    definition used elsewhere, which does require at least one element — so
    ``[]`` is legal here and is what an empty walk should serialize to.
    Omitting the key instead would make the positive answer indistinguishable
    in shape from the negative one.
    """

    def test_its_only_state_is_reachable_with_an_empty_route(self) -> None:
        closure = _load(DIAGRAM_CLOSURE)
        self.assertEqual(len(closure["states"]), 1)
        initial = closure["states"][0]
        self.assertEqual(initial["minimum_depth"], 0)

        receipt = closure_query.query(
            closure, _registration(closure),
            initial["canonical_state"].encode("utf-8"), REPO,
        )

        self.assert_receipt_is_well_formed(receipt)
        self.assertEqual(receipt["outcome"], closure_query.REACHABLE)
        self.assertEqual(receipt["shortest_route"], [])
        self.assertEqual(receipt["visited_states"], 1)

    def test_a_fabricated_target_there_is_still_bounded(self) -> None:
        closure = _load(DIAGRAM_CLOSURE)
        target_bytes = (
            closure["states"][0]["canonical_state"].encode("utf-8")
            + b"\n<fabricated>"
        )
        receipt = closure_query.query(
            closure, _registration(closure), target_bytes, REPO
        )
        self.assert_receipt_is_well_formed(receipt)
        self.assertEqual(receipt["outcome"], closure_query.NOT_REACHABLE)
        text = "\n".join(closure_query.display_lines(receipt, closure))
        self.assertIn(
            f"not reachable within horizon {closure['horizon']}", text
        )
        self.assertNotIn("impossible", text.lower())


class TheCommandLineDisplayCarriesTheBound(unittest.TestCase):
    """§7's display, exercised through the entry point a person would run."""

    def test_the_cli_prints_the_snapshot_horizon_digest_and_route(
        self,
    ) -> None:
        closure = _load(FRAME_CLOSURE)
        target = _state_at_depth(closure, 3)

        # Written outside the repository: a query is a demonstration, and a
        # demonstration must not leave artifacts that look like committed
        # evidence next to the sealed closures.
        scratch = Path(
            self.enterContext(tempfile.TemporaryDirectory())
        )
        target_path = scratch / "target.bin"
        target_path.write_bytes(target["canonical_state"].encode("utf-8"))
        receipt_path = target_path.with_name("receipt.json")

        stream = io.StringIO()
        with redirect_stdout(stream):
            code = closure_query.main(
                [str(FRAME_CLOSURE), str(target_path), str(receipt_path)]
            )
        text = stream.getvalue()

        self.assertEqual(code, 0)
        self.assertIn("outcome: REACHABLE", text)
        self.assertIn(f"horizon: {closure['horizon']}", text)
        self.assertIn(
            f"closure_digest: {closure[closure_check.DIGEST_KEY]}", text
        )
        self.assertIn(f"adapter_id: {closure['adapter_id']}", text)
        for entry in closure["source_manifest"]:
            self.assertIn(entry["path"], text)
            self.assertIn(entry["sha256_lf"], text)
        written = json.loads(receipt_path.read_text(encoding="utf-8"))
        self.assertEqual(written["outcome"], closure_query.REACHABLE)
        self.assertEqual(len(written["shortest_route"]), 3)


if __name__ == "__main__":
    unittest.main()
