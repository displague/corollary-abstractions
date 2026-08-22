#!/usr/bin/env python3
"""The two wiring steps of `docs/SPEC-chat-completions-skin.md` §9.

Both steps surface a capability the engine already had and no typed line
could reach: the twin ledger (W1) and a sealed bounded closure (W2). So the
tests below are written to catch the failure mode a *wiring* step actually
has — a route that answers from somewhere other than the committed artifact,
or that answers where the artifact is silent.

Every fixture is read out of the committed artifacts at test time rather
than pasted in: the twin ids come from `reports/signature_matches.json`, the
targets from `data/closure_targets/manifest.json`. A hardcoded id that
quietly stopped being a twin would turn a real regression into a green run.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from harness import (  # noqa: E402
    CLOSURE_SUBSYSTEM,
    COMMITTED_ARTIFACT_SUBSYSTEMS,
    OPTIONAL_SUBSYSTEMS,
    CoreSession,
    Liveness,
    probe_closure_worlds,
    route_line,
)

PY = sys.executable
LEDGER = REPO / "reports" / "signature_matches.json"
TARGET_DIR = REPO / "data" / "closure_targets"
TARGET_MANIFEST = TARGET_DIR / "manifest.json"
SEED_SCRIPT = REPO / "scripts" / "seed_closure_targets.py"

GROUP_FIELDS = (
    "typed_twin_groups",
    "family_twin_groups_beyond_typed",
    "aliased_twin_groups_beyond_typed",
    "mirror_twin_groups",
    "shape_twin_groups",
)


def ledger() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def twinned_ids(report: dict) -> set[str]:
    return {
        member["statement_id"]
        for field in GROUP_FIELDS
        for group in report.get(field, [])
        for member in group["members"]
    }


def targets(arm: str, world_id: str) -> list[str]:
    manifest = json.loads(TARGET_MANIFEST.read_text(encoding="utf-8"))
    return [
        entry["path"]
        for entry in manifest["files"]
        if entry["arm"] == arm and entry["world_id"] == world_id
    ]


def answer_field(verdict: dict, label: str) -> list[str]:
    prefix = f"{label}"
    return [
        line.split(":", 1)[1].strip()
        for line in verdict.get("answer", ())
        if line.startswith(prefix)
    ]


class WiringSession(unittest.TestCase):
    """One offline session, reused: neither route mutates the resolver state."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.session = CoreSession.boot(REPO, offline=True)


class W1TwinLine(WiringSession):
    """`twin <statement-id>` reports the committed ledger, or says it cannot."""

    def test_a_ledger_member_is_found_with_its_group_and_the_ledger_path(
        self,
    ) -> None:
        report = ledger()
        group = report["typed_twin_groups"][0]
        statement_id = group["members"][0]["statement_id"]

        verdict = route_line(REPO, self.session, f"twin {statement_id}")

        self.assertEqual(verdict["route"], "twin")
        self.assertEqual(verdict["status"], "found")
        members = answer_field(verdict, "member")
        self.assertGreaterEqual(len(members), 2)
        self.assertIn(statement_id, members)
        self.assertIn(
            "ledger     : reports/signature_matches.json",
            verdict["answer"],
        )

    def test_the_reported_members_are_the_ledger_group_verbatim(self) -> None:
        report = ledger()
        group = report["typed_twin_groups"][0]
        statement_id = group["members"][0]["statement_id"]
        expected = [member["statement_id"] for member in group["members"]]

        verdict = route_line(REPO, self.session, f"twin {statement_id}")

        self.assertEqual(answer_field(verdict, "member"), expected)
        self.assertEqual(answer_field(verdict, "level"), ["typed"])
        self.assertEqual(verdict["receipt"]["member_ids"], expected)
        self.assertEqual(
            verdict["receipt"]["ledger_path"], "reports/signature_matches.json"
        )

    def test_the_answer_carries_nothing_beyond_the_frozen_three(self) -> None:
        """§9 froze the answer at level, members, ledger path — nothing more."""
        report = ledger()
        statement_id = report["typed_twin_groups"][0]["members"][0][
            "statement_id"
        ]
        verdict = route_line(REPO, self.session, f"twin {statement_id}")
        labels = {line.split(":", 1)[0].strip() for line in verdict["answer"]}
        self.assertEqual(labels, {"level", "member", "ledger"})

    def test_a_statement_in_several_groups_reports_the_strongest_level(
        self,
    ) -> None:
        """The miss chain returns a statement's shape group and its typed
        group both. Reporting whichever arrived first would make the level in
        the answer a coin toss, so the ledger's own order decides and the
        detail says how many groups were in the running."""
        report = ledger()
        statement_id = "programming.dfactorial.recursive"
        levels = {
            level
            for level, field in zip(("typed", "shape"),
                                    ("typed_twin_groups", "shape_twin_groups"))
            for group in report[field]
            if statement_id in {m["statement_id"] for m in group["members"]}
        }
        if levels != {"typed", "shape"}:
            self.skipTest(f"{statement_id} is no longer in both group levels")

        verdict = route_line(REPO, self.session, f"twin {statement_id}")

        self.assertEqual(verdict["status"], "found")
        self.assertEqual(answer_field(verdict, "level"), ["typed"])
        self.assertEqual(verdict["receipt"]["level"], "typed")
        self.assertIn("2 groups list this statement", verdict["detail"])
        self.assertIn("strongest level is reported", verdict["detail"])

    def test_an_id_the_corpus_does_not_hold_is_the_same_bounded_negative(
        self,
    ) -> None:
        """`exhausted` is a claim about the ledger, so a statement id that
        names nothing at all gets the ledger's answer, not a second one."""
        verdict = route_line(REPO, self.session, "twin no.such.statement.anywhere")

        self.assertEqual(verdict["route"], "twin")
        self.assertEqual(verdict["status"], "exhausted")
        self.assertIn("reports/signature_matches.json", verdict["detail"])
        self.assertIn("no.such.statement.anywhere", verdict["detail"])
        self.assertNotIn("answer", verdict)
        self.assertNotIn("receipt", verdict)

    def test_a_statement_no_group_lists_is_a_bounded_negative(self) -> None:
        statement_id = "calculus.differentiation.chain_rule"
        report = ledger()
        if statement_id in twinned_ids(report):
            self.skipTest(f"{statement_id} has gained a twin group")

        verdict = route_line(REPO, self.session, f"twin {statement_id}")

        self.assertEqual(verdict["route"], "twin")
        self.assertEqual(verdict["status"], "exhausted")
        # The negative is about the ledger, and says so; an unbounded "this
        # statement has no twin" is the sentence this route must not emit.
        self.assertIn("reports/signature_matches.json", verdict["detail"])
        self.assertNotIn("answer", verdict)

    def test_the_statement_still_resolves_when_the_ledger_is_silent(self) -> None:
        """The exhausted arm is a ledger absence, not a missing statement."""
        run = self.session.retrieve("calculus.differentiation.chain_rule")
        self.assertTrue(run.final_state.context)

    def test_the_bare_command_is_refused(self) -> None:
        verdict = route_line(REPO, self.session, "twin")
        self.assertEqual(verdict["route"], "twin")
        self.assertEqual(verdict["status"], "refused")
        self.assertNotIn("answer", verdict)

    def test_two_arguments_are_refused_rather_than_guessed(self) -> None:
        verdict = route_line(REPO, self.session, "twin logic.a logic.b")
        self.assertEqual(verdict["route"], "twin")
        self.assertEqual(verdict["status"], "refused")
        self.assertIn("whitespace", verdict["detail"])


class W2ReachableLine(WiringSession):
    """`reachable <world-id> <target-path>` answers from a sealed closure."""

    def test_the_probe_registers_in_this_checkout(self) -> None:
        record = probe_closure_worlds(REPO)
        self.assertIs(record.liveness, Liveness.OK)
        self.assertIn("worlds registered", record.detail)
        self.assertIn(CLOSURE_SUBSYSTEM, self.session.matrix.registered_ids())

    def test_the_probe_is_a_committed_artifact_probe_not_a_dependency(
        self,
    ) -> None:
        """Spec §9 classifies this as a committed-artifact probe with
        `optional=False`, explicitly not a member of `OPTIONAL_SUBSYSTEMS`:
        that flag names an optional dependency *family* the offline boot
        forces OFF, P-IH1 asserts an offline session registers none of them,
        and the kernel profile's offline boot must still serve W2."""
        self.assertIn(CLOSURE_SUBSYSTEM, COMMITTED_ARTIFACT_SUBSYSTEMS)
        self.assertNotIn(CLOSURE_SUBSYSTEM, OPTIONAL_SUBSYSTEMS)
        record = self.session.matrix.get(CLOSURE_SUBSYSTEM)
        self.assertFalse(record.optional)
        self.assertEqual(self.session.matrix.registered_optional_ids(), ())

    def test_the_probe_is_off_without_a_committed_world_set(self) -> None:
        # OFF and never FAIL: an absent artifact must not block boot.
        record = probe_closure_worlds(REPO / "scripts")
        self.assertIs(record.liveness, Liveness.OFF)

    def test_a_reachable_target_is_found_with_a_replayed_route(self) -> None:
        target = targets("reachable", "story.golden_chicken")[2]

        verdict = route_line(
            REPO, self.session, f"reachable story.golden_chicken {target}"
        )

        self.assertEqual(verdict["route"], "closure")
        self.assertEqual(verdict["status"], "found")
        self.assertEqual(verdict["receipt"]["outcome"], "REACHABLE")
        self.assertIn("shortest_route", verdict["receipt"])
        self.assertTrue(verdict["receipt"]["shortest_route"])
        self.assertIn("outcome: REACHABLE", verdict["answer"])

    def test_the_answer_is_the_committed_display_verbatim(self) -> None:
        """§6 leaves the skin no rendering freedom, so the route must have
        none either: the answer is `closure_query`'s own §7 display, not a
        second spelling of the same receipt."""
        import closure_check  # noqa: PLC0415
        import closure_query  # noqa: PLC0415

        target = targets("reachable", "story.golden_chicken")[3]
        verdict = route_line(
            REPO, self.session, f"reachable story.golden_chicken {target}"
        )

        closure_path = Path("reports/closures/story.golden_chicken.closure.json")
        closure = closure_check.load_closure(REPO / closure_path)
        self.assertEqual(
            list(verdict["answer"]),
            closure_query.display_lines(
                verdict["receipt"], closure, closure_path
            ),
        )

    def test_an_unreachable_target_is_exhausted_with_its_horizon_named(
        self,
    ) -> None:
        target = targets("unreachable", "story.golden_chicken")[0]
        horizon = json.loads(
            (REPO / "reports" / "closures"
             / "story.golden_chicken.closure.json").read_text(encoding="utf-8")
        )["horizon"]

        verdict = route_line(
            REPO, self.session, f"reachable story.golden_chicken {target}"
        )

        self.assertEqual(verdict["status"], "exhausted")
        self.assertEqual(
            verdict["receipt"]["outcome"], "NOT_REACHABLE_WITHIN_HORIZON"
        )
        self.assertIn(f"horizon: {horizon}", verdict["answer"])
        self.assertTrue(
            any(
                f"not reachable within horizon {horizon}" in line
                for line in verdict["answer"]
            ),
            verdict["answer"],
        )

    def test_a_missing_target_is_refused_here_not_staged_by_the_write_gate(
        self,
    ) -> None:
        verdict = route_line(
            REPO,
            self.session,
            "reachable story.golden_chicken data/closure_targets/no_such.json",
        )
        self.assertEqual(verdict["route"], "closure")
        self.assertEqual(verdict["status"], "refused")

    def test_wrong_arity_is_refused(self) -> None:
        for line in (
            "reachable",
            "reachable story.golden_chicken",
            "reachable story.golden_chicken a b",
        ):
            with self.subTest(line=line):
                verdict = route_line(REPO, self.session, line)
                self.assertEqual(verdict["route"], "closure")
                self.assertEqual(verdict["status"], "refused")

    def test_an_unregistered_world_is_refused_by_name(self) -> None:
        target = targets("reachable", "story.golden_chicken")[0]

        verdict = route_line(REPO, self.session, f"reachable nonsense.world {target}")

        self.assertEqual(verdict["status"], "refused")
        self.assertTrue(verdict["detail"].startswith("WrongWorld:"), verdict["detail"])
        self.assertNotIn("receipt", verdict)


STORY_CLOSURE = Path("reports/closures/story.golden_chicken.closure.json")


def mirror_repo_root(root: Path) -> Path:
    """A repo root a query can run against: the frozen sources its
    ``source_manifest`` names, the sealed closures, and the target set."""

    shutil.copytree(
        REPO / "data" / "closure_worlds", root / "data" / "closure_worlds"
    )
    shutil.copytree(
        REPO / "data" / "closure_targets", root / "data" / "closure_targets"
    )
    shutil.copytree(REPO / "reports" / "closures", root / "reports" / "closures")
    return root


class OnlyRegisteredTargetsAreAnswerable(WiringSession):
    """`query` certifies a bounded negative for whatever bytes it is handed.

    Ungated, that makes every file in the repository a mintable sealed
    "not reachable within horizon N" receipt naming a real closure — the
    self-fulfilling arm reopened from the other side. The manifest is the
    gate, and these are the ways past it that must not exist.
    """

    def test_an_arbitrary_repository_file_is_refused_not_certified(self) -> None:
        verdict = route_line(
            REPO, self.session, "reachable story.golden_chicken README.md"
        )
        self.assertEqual(verdict["route"], "closure")
        self.assertEqual(verdict["status"], "refused")
        self.assertIn("data/closure_targets/manifest.json", verdict["detail"])
        # The point of the gate: no receipt, so nothing was certified.
        self.assertNotIn("receipt", verdict)
        self.assertNotIn("answer", verdict)

    def test_a_committed_closure_file_is_not_a_target_either(self) -> None:
        verdict = route_line(
            REPO,
            self.session,
            f"reachable story.golden_chicken {STORY_CLOSURE.as_posix()}",
        )
        self.assertEqual(verdict["status"], "refused")
        self.assertNotIn("receipt", verdict)

    def test_another_worlds_target_is_refused_by_name(self) -> None:
        target = targets("reachable", "visual.rt0000")[0]

        verdict = route_line(
            REPO, self.session, f"reachable story.golden_chicken {target}"
        )

        self.assertEqual(verdict["status"], "refused")
        self.assertIn("visual.rt0000", verdict["detail"])
        self.assertNotIn("receipt", verdict)

    def test_the_same_path_spelled_with_backslashes_still_matches(self) -> None:
        """The manifest is posix; a Windows person types the other separator.
        Refusing them would be the gate rejecting the registered target."""
        windows_spelling = targets("reachable", "story.golden_chicken")[1].replace(
            "/", "\\"
        )

        verdict = route_line(
            REPO, self.session, f"reachable story.golden_chicken {windows_spelling}"
        )

        self.assertEqual(verdict["status"], "found")

    def test_an_absent_target_manifest_refuses_everything(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = mirror_repo_root(Path(temporary))
            (root / "data" / "closure_targets" / "manifest.json").unlink()
            target = targets("reachable", "story.golden_chicken")[0]

            verdict = route_line(
                root, self.session, f"reachable story.golden_chicken {target}"
            )

        self.assertEqual(verdict["status"], "refused")
        self.assertIn("no readable target set", verdict["detail"])
        self.assertNotIn("receipt", verdict)

    def test_an_unparseable_target_manifest_refuses_rather_than_raises(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = mirror_repo_root(Path(temporary))
            (root / "data" / "closure_targets" / "manifest.json").write_text(
                '{"files": tru', encoding="utf-8"
            )
            target = targets("reachable", "story.golden_chicken")[0]

            verdict = route_line(
                root, self.session, f"reachable story.golden_chicken {target}"
            )

        self.assertEqual(verdict["status"], "refused")
        self.assertIn("JSONDecodeError", verdict["detail"])


class BrokenArtifactsRefuseRatherThanRaise(WiringSession):
    """A committed file that has gone bad ends the turn, not the session."""

    def test_a_truncated_closure_is_a_named_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = mirror_repo_root(Path(temporary))
            (root / STORY_CLOSURE).write_text('{"world_id": trunc', encoding="utf-8")
            target = targets("reachable", "story.golden_chicken")[0]

            verdict = route_line(
                root, self.session, f"reachable story.golden_chicken {target}"
            )

        self.assertEqual(verdict["route"], "closure")
        self.assertEqual(verdict["status"], "refused")
        self.assertIn("JSONDecodeError", verdict["detail"])
        self.assertNotIn("receipt", verdict)

    def test_a_corrupt_target_is_refused_and_keeps_its_receipt(self) -> None:
        """`CORRUPT_TARGET` is an answer — a state record carrying this digest
        with different canonical bytes — but not a grounding claim, so it maps
        to `refused` while keeping the receipt the skin passes through.

        The only adversary worth building is a RE-SEALED forgery: an unsealed
        one is caught by the digest recompute before a target byte is read.
        """
        import closure_check  # noqa: PLC0415

        target = targets("reachable", "story.golden_chicken")[2]
        payload = (REPO / target).read_bytes()
        digest = hashlib.sha256(payload).hexdigest()

        with tempfile.TemporaryDirectory() as temporary:
            root = mirror_repo_root(Path(temporary))
            closure = closure_check.load_closure(REPO / STORY_CLOSURE)
            record = next(
                state
                for state in closure["states"]
                if state["state_digest"] == digest
            )
            record["canonical_state"] = record["canonical_state"] + " "
            closure["closure_digest"] = closure_check.closure_digest(closure)
            (root / STORY_CLOSURE).write_text(
                json.dumps(closure), encoding="utf-8"
            )

            verdict = route_line(
                root, self.session, f"reachable story.golden_chicken {target}"
            )

        self.assertEqual(verdict["route"], "closure")
        self.assertEqual(verdict["status"], "refused")
        self.assertEqual(verdict["receipt"]["outcome"], "CORRUPT_TARGET")
        self.assertEqual(verdict["receipt"]["target_digest"], digest)
        self.assertIn("outcome: CORRUPT_TARGET", verdict["answer"])


class RoutingTableIsUnchangedAbove(WiringSession):
    """The two new rows sit below the rows §5 already ordered above them."""

    def setUp(self) -> None:
        self.session.pending_candidates = ()
        self.session.pending_query = None
        self.session.pending_resolver = None
        self.session.context_hops = 0
        self.session.context_seen.clear()

    def test_ownership_still_wins_its_line(self) -> None:
        verdict = route_line(REPO, self.session, "owns x ^ 2")
        self.assertEqual(verdict["route"], "ownership")
        self.assertEqual(verdict["status"], "solved")

    def test_suppose_still_wins_its_line(self) -> None:
        verdict = route_line(REPO, self.session, "suppose x=5, what is x^2")
        self.assertEqual(verdict["route"], "evaluate")
        self.assertEqual(verdict["status"], "solved")

    def test_twin_escapes_a_pending_resolver_ask_the_way_owns_does(self) -> None:
        report = ledger()
        statement_id = report["typed_twin_groups"][0]["members"][0][
            "statement_id"
        ]
        route_line(REPO, self.session, "area of a circle")
        before = self.session.pending_candidates
        self.assertTrue(before)

        verdict = route_line(REPO, self.session, f"twin {statement_id}")

        self.assertEqual(verdict["route"], "twin")
        self.assertEqual(verdict["status"], "found")
        self.assertEqual(self.session.pending_candidates, before)

    def test_reachable_escapes_a_pending_resolver_ask_too(self) -> None:
        target = targets("reachable", "story.golden_chicken")[1]
        route_line(REPO, self.session, "area of a circle")
        before = self.session.pending_candidates
        self.assertTrue(before)

        verdict = route_line(
            REPO, self.session, f"reachable story.golden_chicken {target}"
        )

        self.assertEqual(verdict["route"], "closure")
        self.assertEqual(verdict["status"], "found")
        self.assertEqual(self.session.pending_candidates, before)


class SeededTargetsAreReproducible(unittest.TestCase):
    """The targets are generated, so the generator must be a function."""

    def test_the_committed_bytes_match_the_committed_digests(self) -> None:
        manifest = json.loads(TARGET_MANIFEST.read_text(encoding="utf-8"))
        self.assertTrue(manifest["files"])
        for entry in manifest["files"]:
            with self.subTest(path=entry["path"]):
                payload = (REPO / entry["path"]).read_bytes()
                self.assertEqual(
                    hashlib.sha256(payload).hexdigest(), entry["sha256"]
                )

    def test_every_registered_world_has_at_least_one_target(self) -> None:
        manifest = json.loads(TARGET_MANIFEST.read_text(encoding="utf-8"))
        for summary in manifest["worlds"]:
            with self.subTest(world=summary["world_id"]):
                self.assertGreaterEqual(summary["reachable_targets"], 1)
                # A world that cannot fill the §9 floor records why, in the
                # manifest, rather than having targets manufactured for it.
                if (
                    summary["reachable_targets"] < 3
                    or summary["unreachable_targets"] < 2
                ):
                    self.assertIn("shortfall", summary)

    def test_rerunning_the_seed_writes_identical_bytes(self) -> None:
        before = {
            path.name: path.read_bytes() for path in sorted(TARGET_DIR.iterdir())
        }
        after: dict[str, bytes] = {}
        try:
            proc = subprocess.run(
                [PY, str(SEED_SCRIPT)],
                capture_output=True,
                text=True,
                cwd=REPO,
                timeout=600,
            )
            after = {
                path.name: path.read_bytes()
                for path in sorted(TARGET_DIR.iterdir())
            }
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(after, before)
        finally:
            # Restore whatever was committed even on a failure — including a
            # seed run that exited non-zero partway through writing — so a
            # drifting generator cannot leave the checkout rewritten behind it.
            for name, payload in before.items():
                (TARGET_DIR / name).write_bytes(payload)
            for name in set(after) - set(before):
                (TARGET_DIR / name).unlink()


if __name__ == "__main__":
    unittest.main()
