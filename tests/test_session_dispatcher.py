"""Adjudication of the Phase-2 need dispatcher (v0.8 item 1, slice 2).

Registered predictions. These entries are quoted VERBATIM from
``docs/DESIGN-interactive-harness.md`` §10, where they were registered on
2026-08-09 *before* any dispatcher implementation. They are restated here beside
the tests that decide them, per the house rule that a prediction is registered
before it is adjudicated and its text is never silently narrowed. A miss is
recorded MISSED with a correction appended, never edited away.

P-IH4 — Registered paths only. *(prediction)* Given a goal that no registered
    subsystem claims, the session abstains or ASKs rather than free-generating an
    answer. Miss if fluent unregistered content is emitted as VERIFIED.
    Adjudicated by: a dispatcher test that submits a goal outside every
    registered path and asserts the terminal stop is REFUSED/abstain with a
    reason, extending the refusal patterns of tests/test_retrieval.py
    (test_point_before_retrieval_is_refused).

P-IH7 — Session-level loop detection. *(prediction — newly registered,
    2026-08-09 review.)* The kernel's rejected sets, seen_states, and budgets are
    run-local (scripts/controller.py:271), so a multi-run dispatcher session has
    no cycle protection today. Prediction: once §9 Phase 1's session-scoped
    pruning record and Phase 2's session budget land, a session whose need cycles
    between two registered paths terminates in bounded hops with REFUSED or an
    explicit abstention/BUDGET stop, and never loops.
    Adjudicated by: a new tests/test_session_dispatcher.py case in which two
    registered subsystems each re-open the need the other just failed, with a
    stated session budget (proposed: 8 dispatcher hops). The session must reach a
    terminal stop within that budget, the stop must be REFUSED/abstain/BUDGET
    with the cycle named in the trace, and the trace must show the second visit
    to a (need, state_key) pair being pruned rather than re-expanded. Miss if the
    session exceeds the hop ceiling, or if it terminates only because a
    wall-clock or step cap fired without identifying the cycle. Adjudication is
    required before any Phase-3 tool plugin registers, since tools multiply the
    hop graph (§3.5, §8).

Adjudications (recorded after implementation):
  P-IH4: FIRED — a need routed to an unregistered path (an OFF optional
         subsystem, and an id absent from the registry) abstains with the
         missing capability named; no run emits VERIFIED and no material is
         materialized (``PIH4RegisteredPathsOnly``).
  P-IH7: FIRED — two registered subsystems each re-open the other's dead need;
         the dispatcher terminates by naming the (need, state_key) cycle at hop 2
         of a budget of 8 (and identically under a budget of 50, so the ceiling
         did not cause it), pruning the second visit rather than re-expanding it.
         Cross-hop non-vacuity: with loop detection disabled the SAME topology
         runs to the hop ceiling with BUDGET, proving the cycle is real and that
         detection — not a step cap — is what stops it. Adversarial: two
         genuinely different needs sharing a frame NAME but differing in owner
         (spec) are NOT conflated as a loop, and a genuinely live need sharing a
         dead need's frame name still materializes (``PIH7SessionLoopDetection``).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from controller import StopReason, Verdict  # noqa: E402
from dispatcher import (  # noqa: E402
    DEFAULT_HOP_BUDGET,
    DispatchOutcome,
    NeedDispatcher,
    RegisteredPath,
    need_identity,
)
from frames import FrameExecutor, FrameSpec, Literal  # noqa: E402
from harness import CoreSession  # noqa: E402
from retrieval import Channel, RetrievalState, UnifiedKnowledgeStore  # noqa: E402


# A key no committed source can answer: every rung of the miss chain misses, so
# a run over it abstains (EXHAUSTED, empty context) and commits pruning
# evidence. This is the same shape the retrieval substrate test uses.
DEAD_KEY_A = "zzqx nonexistent alpha 998877"
DEAD_KEY_B = "zzqx nonexistent beta 665544"


def _live_corpus_key() -> str:
    """A committed statement id that the exact rung answers.

    Read at test time rather than pinned, like the Phase-1 twin-member helper,
    so a live-need assertion survives seed regeneration.
    """

    for path in sorted((REPO_ROOT / "data").glob("*/nodes.json")):
        corpus = json.loads(path.read_text(encoding="utf-8"))
        for node in corpus.get("statement_nodes", []):
            return node["statement_id"]
    raise unittest.SkipTest("no committed corpus statement to point at")


def _open_need(
    executor: FrameExecutor,
    key: str,
    *,
    frame_name: str,
    owner: str | None = None,
) -> RetrievalState:
    """Open a store-channel retrieval need over a named (optionally owned) frame.

    ``owner`` lets two needs share a frame *name* while differing in *spec* —
    the P-RT6 shape the dispatcher's frame-spec-qualified key must keep apart.
    Retrieval stays open on the frame so the miss chain may walk it.
    """

    frame = executor.open_frame(
        FrameSpec(frame=frame_name, owner=owner, retrieval="open")
    )
    return RetrievalState.from_unknown(
        executor,
        frame,
        "answer",
        key,
        Literal("request", "needs", key),
        resolution_channel=Channel.STORE,
    )


class PIH4RegisteredPathsOnly(unittest.TestCase):
    """P-IH4: a goal no registered subsystem claims abstains, never fabricates."""

    def setUp(self) -> None:
        self.session = CoreSession.boot(REPO_ROOT, offline=True)

    def test_route_to_off_optional_subsystem_abstains_with_reason(self) -> None:
        # retrieve.wordnet is OFF in an offline boot, so a path standing in for
        # it is present-but-unregistered. Routing a need there must abstain with
        # the capability named — not free-generate, not improvise another path.
        self.assertFalse(self.session.matrix.get("retrieve.wordnet").registered)
        executor = self.session.executor
        registry = {
            "retrieve.wordnet": RegisteredPath(
                "retrieve.wordnet",
                registered=False,  # mirrors the OFF probe
                build_state=lambda sid: _open_need(
                    executor, DEAD_KEY_A, frame_name="runtime.frames.disp_p_ih4"
                ),
            ),
        }
        dispatcher = NeedDispatcher.for_session(self.session, registry)
        result = dispatcher.dispatch(self.session.session_id, "retrieve.wordnet")

        self.assertIs(result.stop_reason, StopReason.EXHAUSTED)
        self.assertIsNone(result.cycle)
        self.assertEqual(len(result.events), 1)
        self.assertIs(result.events[0].outcome, DispatchOutcome.UNREGISTERED)
        self.assertIn("did not register", result.reason)
        self.assertIn("retrieve.wordnet", result.reason)
        # Nothing was materialized and no run was produced: abstention is not a
        # transition, so there is no VERIFIED content to leak (P-IH4 miss cond).
        self.assertFalse(result.materialized)
        self.assertIsNone(result.final_run)

    def test_route_to_unknown_subsystem_id_abstains(self) -> None:
        # An id absent from the registry entirely is the "command not found"
        # case: still abstain, never guess a path.
        dispatcher = NeedDispatcher.for_session(self.session, {})
        result = dispatcher.dispatch(self.session.session_id, "tool.no_such_thing")
        self.assertIs(result.stop_reason, StopReason.EXHAUSTED)
        self.assertIs(result.events[0].outcome, DispatchOutcome.UNREGISTERED)
        self.assertFalse(result.materialized)

    def test_registered_path_is_actually_walked(self) -> None:
        # The negative test is only meaningful if a REGISTERED path does get
        # dispatched. A registered path over a live corpus key materializes.
        executor = self.session.executor
        key = _live_corpus_key()
        registry = {
            "retrieve.five_store": RegisteredPath(
                "retrieve.five_store",
                registered=True,
                build_state=lambda sid: _open_need(
                    executor, key, frame_name="runtime.frames.disp_live"
                ),
            ),
        }
        dispatcher = NeedDispatcher.for_session(self.session, registry)
        result = dispatcher.dispatch(self.session.session_id, "retrieve.five_store")
        self.assertIs(result.stop_reason, StopReason.SOLVED)
        self.assertTrue(result.materialized)
        self.assertIs(result.events[-1].outcome, DispatchOutcome.MATERIALIZED)


class PIH7SessionLoopDetection(unittest.TestCase):
    """P-IH7: a need cycling between two registered paths refuses, never spins."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.store = UnifiedKnowledgeStore.load(
            REPO_ROOT / "data", REPO_ROOT / "reports"
        )

    def setUp(self) -> None:
        self.session = CoreSession.boot(REPO_ROOT, offline=True)
        # Reuse the session's executor; swap in the full store so a live key can
        # actually materialize in the adversarial case. One verifier, so pruning
        # accumulates across hops — the property under test.
        self.executor = self.session.executor
        self.verifier = self.session.verifier
        self.verifier.store = self.store

    def _cycle_registry(self) -> dict[str, RegisteredPath]:
        """Two registered subsystems, each re-opening the other's dead need.

        subsystem.alpha's need is DEAD_KEY_A over one frame; subsystem.beta's is
        DEAD_KEY_B over a different frame. alpha.reopens = beta and
        beta.reopens = alpha, so with both needs unanswerable the dispatcher is
        pushed A -> B -> A ... — a genuine cross-subsystem cycle whose two legs
        have DIFFERENT verifier state keys (so the verifier's own single-state
        pruning cannot see the loop; only the dispatcher record can).
        """

        return {
            "subsystem.alpha": RegisteredPath(
                "subsystem.alpha",
                registered=True,
                build_state=lambda sid: _open_need(
                    self.executor, DEAD_KEY_A, frame_name="runtime.frames.disp_alpha"
                ),
                reopens="subsystem.beta",
            ),
            "subsystem.beta": RegisteredPath(
                "subsystem.beta",
                registered=True,
                build_state=lambda sid: _open_need(
                    self.executor, DEAD_KEY_B, frame_name="runtime.frames.disp_beta"
                ),
                reopens="subsystem.alpha",
            ),
        }

    def test_two_subsystem_cycle_terminates_by_naming_the_cycle(self) -> None:
        dispatcher = NeedDispatcher.for_session(
            self.session, self._cycle_registry(), hop_budget=DEFAULT_HOP_BUDGET
        )
        result = dispatcher.dispatch(self.session.session_id, "subsystem.alpha")

        # Terminates within budget, and NOT by hitting the ceiling.
        self.assertIs(result.stop_reason, StopReason.EXHAUSTED)
        self.assertIsNot(result.stop_reason, StopReason.BUDGET)
        self.assertLess(len(result.events), DEFAULT_HOP_BUDGET)

        # The cycle is named in the trace as a (need, state_key) pair.
        self.assertIsNotNone(result.cycle)
        cycle_events = [
            e for e in result.events if e.outcome is DispatchOutcome.CYCLE
        ]
        self.assertEqual(len(cycle_events), 1)
        cycle_event = cycle_events[0]
        # The second visit was PRUNED, not re-expanded: the cycle hop produced
        # no run (run_miss_chain was never called for it).
        self.assertIsNone(cycle_event.run)
        self.assertIn("loop detection", cycle_event.detail)
        self.assertIn("pruned", cycle_event.detail)

        # It fired at hop 2 (index 2): hop0 alpha DEAD, hop1 beta DEAD, hop2 the
        # revisit of alpha's pair. This is the "second visit" P-IH7 names.
        self.assertEqual(cycle_event.hop, 2)
        outcomes = [e.outcome for e in result.events]
        self.assertEqual(
            outcomes,
            [
                DispatchOutcome.DEAD,
                DispatchOutcome.DEAD,
                DispatchOutcome.CYCLE,
            ],
        )
        # The pruned pair is exactly alpha's first-visit (need, state_key).
        self.assertEqual(result.cycle[0], result.events[0].need_key)
        self.assertEqual(result.cycle[1], result.events[0].state_key)

    def test_pruning_evidence_genuinely_spans_hops(self) -> None:
        # The verifier's _pruning is NOT reset per hop: each distinct dead need
        # adds committed evidence, and the total is strictly greater after the
        # second subsystem than after the first. If a hop reset pruning, these
        # counts would not accumulate.
        dispatcher = NeedDispatcher.for_session(
            self.session, self._cycle_registry()
        )
        result = dispatcher.dispatch(self.session.session_id, "subsystem.alpha")
        alpha_dead, beta_dead, cycle = result.events
        self.assertGreater(alpha_dead.pruning_count, 0)
        self.assertGreater(beta_dead.pruning_count, alpha_dead.pruning_count)
        # The refusal cites the accumulated cross-hop evidence, not an empty set.
        self.assertEqual(cycle.pruning_count, beta_dead.pruning_count)
        self.assertGreater(cycle.pruning_count, 0)
        evidence = self.verifier.session_pruning_evidence(self.session.session_id)
        self.assertEqual(len(evidence), cycle.pruning_count)

    def test_a_high_budget_still_stops_at_the_cycle_not_the_ceiling(self) -> None:
        # Non-vacuity: prove termination is caused by cycle DETECTION, not by a
        # step cap. Raising the ceiling to 50 must not change where it stops.
        dispatcher = NeedDispatcher.for_session(
            self.session, self._cycle_registry(), hop_budget=50
        )
        result = dispatcher.dispatch(self.session.session_id, "subsystem.alpha")
        self.assertIs(result.stop_reason, StopReason.EXHAUSTED)
        self.assertIsNotNone(result.cycle)
        self.assertEqual(len(result.events), 3)  # unchanged by the larger budget

    def test_without_detection_the_same_topology_spins_to_the_ceiling(self) -> None:
        # The control that makes the loop test non-vacuous: "confirming a
        # cache's hits is not testing a cache". With detection OFF, the SAME
        # cycling registry does NOT terminate on its own — it runs to the hop
        # ceiling and stops with BUDGET. That proves the topology genuinely
        # cycles and that the visited-dead record is what stops it.
        dispatcher = NeedDispatcher.for_session(
            self.session,
            self._cycle_registry(),
            hop_budget=6,
            loop_detection=False,
        )
        result = dispatcher.dispatch(self.session.session_id, "subsystem.alpha")
        self.assertIs(result.stop_reason, StopReason.BUDGET)
        self.assertIsNone(result.cycle)
        self.assertEqual(len(result.events), 6)  # spun for the whole budget
        self.assertTrue(
            all(e.outcome is DispatchOutcome.DEAD for e in result.events)
        )

    def test_two_different_needs_are_not_conflated_as_a_loop(self) -> None:
        # Adversarial: two genuinely DIFFERENT needs that share a frame NAME but
        # differ in owner (spec). A name-only key (the P-RT6 bug) would treat the
        # second as a revisit of the first and refuse it as a loop. The
        # spec-qualified key must not: both are processed as independent dead
        # ends, and the stop is a plain abstention, not a named cycle.
        executor = self.executor
        registry = {
            "subsystem.sally": RegisteredPath(
                "subsystem.sally",
                registered=True,
                build_state=lambda sid: _open_need(
                    executor,
                    DEAD_KEY_A,
                    frame_name="runtime.frames.disp_shared",
                    owner="sally",
                ),
                reopens="subsystem.anne",
            ),
            "subsystem.anne": RegisteredPath(
                "subsystem.anne",
                registered=True,
                build_state=lambda sid: _open_need(
                    executor,
                    DEAD_KEY_A,  # SAME key AND same frame name; only owner differs
                    frame_name="runtime.frames.disp_shared",
                    owner="anne",
                ),
                reopens=None,  # leaf: honest abstention if reached
            ),
        }
        dispatcher = NeedDispatcher.for_session(self.session, registry)
        result = dispatcher.dispatch(self.session.session_id, "subsystem.sally")

        # Both were processed as DEAD; the second was NOT flagged as a cycle.
        self.assertIs(result.stop_reason, StopReason.EXHAUSTED)
        self.assertIsNone(result.cycle)
        self.assertEqual(
            [e.outcome for e in result.events],
            [DispatchOutcome.DEAD, DispatchOutcome.DEAD],
        )

        # Prove the collision a name-only key WOULD have caused: the two needs
        # share slot, suggested key AND frame name, so a name-only identity is
        # identical — yet the spec-qualified identities differ, which is exactly
        # why the second is not conflated.
        sally = _open_need(
            executor, DEAD_KEY_A,
            frame_name="runtime.frames.disp_shared", owner="sally",
        )
        anne = _open_need(
            executor, DEAD_KEY_A,
            frame_name="runtime.frames.disp_shared", owner="anne",
        )
        def name_only(s: RetrievalState) -> tuple[str, str, str]:
            return (s.pending.slot, s.pending.suggested_key, s.frame.spec.frame)

        self.assertEqual(name_only(sally), name_only(anne))  # would collide
        self.assertNotEqual(need_identity(sally), need_identity(anne))  # does not
        self.assertNotEqual(
            self.verifier.state_key(sally), self.verifier.state_key(anne)
        )

    def test_a_live_need_sharing_a_dead_needs_frame_name_still_answers(self) -> None:
        # The wrong-answer this guards against, made concrete: if a dead need
        # poisoned a same-named live need, the live need would be REFUSED as a
        # loop instead of materializing. It must materialize.
        executor = self.executor
        live_key = _live_corpus_key()
        registry = {
            "subsystem.dead": RegisteredPath(
                "subsystem.dead",
                registered=True,
                build_state=lambda sid: _open_need(
                    executor,
                    DEAD_KEY_A,
                    frame_name="runtime.frames.disp_shared_live",
                    owner="dead",
                ),
                reopens="subsystem.live",
            ),
            "subsystem.live": RegisteredPath(
                "subsystem.live",
                registered=True,
                build_state=lambda sid: _open_need(
                    executor,
                    live_key,
                    frame_name="runtime.frames.disp_shared_live",
                    owner="live",
                ),
                reopens=None,
            ),
        }
        dispatcher = NeedDispatcher.for_session(self.session, registry)
        result = dispatcher.dispatch(self.session.session_id, "subsystem.dead")
        self.assertIs(result.stop_reason, StopReason.SOLVED)
        self.assertTrue(result.materialized)
        self.assertEqual(
            [e.outcome for e in result.events],
            [DispatchOutcome.DEAD, DispatchOutcome.MATERIALIZED],
        )


if __name__ == "__main__":
    unittest.main()
