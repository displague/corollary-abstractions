#!/usr/bin/env python3
"""Verdict-backed ingestion as a RULE (v0.12 item 4).

The rule refuses a case that does not exist in the corpus yet: no ingested
node cites `verified_by` today. So it is proved against synthetic nodes —
the only honest way to test a preventive rule, and the reason this file
exists rather than a grep over `data/`.

The named dependant is held-out B. Goedel-Pset's proofs are all `sorry`, so
a Goedel-Pset node carrying a `verified_by` link would assert a
machine-checked bridge that provably is not there upstream.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from decompose import INGESTED_CORPUS_PREFIXES  # noqa: E402
from validate_nodes import ingested_verdict_rule_errors  # noqa: E402


def node(sid: str, links: list | None = None) -> dict:
    out: dict = {"statement_id": sid}
    if links is not None:
        out["verified_by"] = links
    return out


LEAN_LINK = [{
    "system": "lean4",
    "artifact": "prover/proofs/not-a-real-artifact.json",
    "reference": "some_theorem",
}]


class TheRuleFires(unittest.TestCase):
    def test_goedel_pset_node_citing_verified_by_is_refused(self) -> None:
        """The case item 4 exists for."""
        errors = ingested_verdict_rule_errors(
            [node("goedelpset.skel.goedel_pset_1", LEAN_LINK)],
            {"goedelpset.skel.goedel_pset_1": "goedel_pset.skel.v1"},
            REPO,
        )
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("not pinned", errors[0])

    def test_the_rule_is_not_limited_to_python_tests(self) -> None:
        """v0.11 covered `python-tests` only; this is the widening."""
        errors = ingested_verdict_rule_errors(
            [node("leanworkbook.skel.x", LEAN_LINK)],
            {"leanworkbook.skel.x": "lean_workbook.ground.v1"},
            REPO,
        )
        self.assertTrue(errors)
        self.assertNotIn("python-tests", errors[0])

    def test_every_registered_ingested_corpus_is_covered(self) -> None:
        """Whatever `decompose` calls ingested, this rule binds."""
        for prefix in INGESTED_CORPUS_PREFIXES:
            with self.subTest(prefix=prefix):
                errors = ingested_verdict_rule_errors(
                    [node("some.node", LEAN_LINK)],
                    {"some.node": f"{prefix}.v1"},
                    REPO,
                )
                self.assertTrue(errors, f"{prefix} not covered")

    def test_a_link_with_no_artifact_is_refused(self) -> None:
        errors = ingested_verdict_rule_errors(
            [node("goedelpset.skel.x", [{"system": "lean4"}])],
            {"goedelpset.skel.x": "goedel_pset.skel.v1"},
            REPO,
        )
        self.assertTrue(errors)
        self.assertIn("names no artifact", errors[0])


class TheRuleIsNotVacuous(unittest.TestCase):
    """A rule that refuses everything is not a rule."""

    def test_curated_nodes_are_untouched(self) -> None:
        """Hand-authored citations are reviewed; the rule binds ingestion."""
        errors = ingested_verdict_rule_errors(
            [node("programming.gcd.euclid", LEAN_LINK)],
            {"programming.gcd.euclid": "programming.core.v1"},
            REPO,
        )
        self.assertEqual(errors, [])

    def test_ingested_nodes_without_citations_are_untouched(self) -> None:
        """The overwhelming majority: 12k formal-without-bridge nodes."""
        errors = ingested_verdict_rule_errors(
            [node("goedelpset.skel.x"), node("minif2f.skel.y", [])],
            {"goedelpset.skel.x": "goedel_pset.skel.v1",
             "minif2f.skel.y": "minif2f.skel.v1"},
            REPO,
        )
        self.assertEqual(errors, [])

    def test_a_pinned_artifact_with_a_verdict_passes(self) -> None:
        """The rule admits what it is supposed to admit.

        Uses a real manifest entry that carries verdicts, so this asserts
        the accept path against committed data rather than a mock.
        """
        manifest = json.loads(
            (REPO / "prover" / "proof-artifact-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        with_verdicts = [
            name for name, entry in (manifest.get("artifacts") or {}).items()
            if isinstance(entry, dict) and entry.get("verdicts")
        ]
        if not with_verdicts:
            self.skipTest("no manifest artifact carries verdicts")
        errors = ingested_verdict_rule_errors(
            [node("goedelpset.skel.x", [{
                "system": "lean4",
                "artifact": with_verdicts[0],
                "reference": "t",
            }])],
            {"goedelpset.skel.x": "goedel_pset.skel.v1"},
            REPO,
        )
        self.assertEqual(errors, [])


class TheLiveCorpusObeysIt(unittest.TestCase):
    def test_no_committed_ingested_node_violates_the_rule(self) -> None:
        """Both corpus roots, so the holdouts are checked too."""
        nodes: list[dict] = []
        corpus_of: dict[str, str] = {}
        roots = [REPO / "data", REPO / "data_holdout"]
        for root in roots:
            if not root.is_dir():
                continue
            for path in sorted(root.glob("*/nodes.json")):
                doc = json.loads(path.read_text(encoding="utf-8"))
                cid = doc.get("corpus_id", path.parent.name)
                for n in doc["statement_nodes"]:
                    nodes.append(n)
                    corpus_of[n["statement_id"]] = cid
        self.assertEqual(ingested_verdict_rule_errors(nodes, corpus_of, REPO), [])


if __name__ == "__main__":
    unittest.main()
