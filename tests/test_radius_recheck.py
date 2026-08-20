#!/usr/bin/env python3
"""The R4 recheck, tested against a graph and a certificate written by hand.

Every fixture in this file is authored here, in literals, and computed by
hand in the comments beside them. Nothing in this suite runs the graph
assembler or the radius tool, and nothing reads their output: R4 asks
whether an *independent* re-derivation agrees with a published closure, and
a test that fed the recheck the builder's own artifacts would be asking the
builder to grade itself. The synthetic graph is small enough that the
expected closure can be read off the edge list without running anything,
which is the property that makes the corruption cases meaningful — each one
is a difference between what a reader can see and what the certificate
claims.

The certificate fixture is validated against
``schema/radius-certificate.schema.json`` before it is used, so a corruption
case can never pass for the trivial reason that its certificate was
malformed in some second, unintended way.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import radius_recheck  # noqa: E402

CERTIFICATE_SCHEMA_PATH = REPO / "schema" / "radius-certificate.schema.json"
GRAPH_SCHEMA_PATH = REPO / "schema" / "provenance-graph.schema.json"

BUILD = "test-build-0001"


def _node(node_id: str, kind: str, produced_by: str) -> dict:
    """A node record, with its content hash derived from its own id.

    The hash only has to be a well-formed sha256 that differs per node; this
    suite tests traversal, not content identity, and inventing digests by
    hand would add sixty-four characters of noise per line.
    """

    return {
        "record": "node",
        "node_id": node_id,
        "kind": kind,
        "content_sha256": hashlib.sha256(node_id.encode("utf-8")).hexdigest(),
        "produced_by": produced_by,
        "first_seen_build": BUILD,
    }


def _edge(
    edge_id: str,
    from_node: str,
    to_node: str,
    relation: str,
    emitted_by: str,
    inferred: bool,
) -> dict:
    return {
        "record": "edge",
        "edge_id": edge_id,
        "from_node": from_node,
        "to_node": to_node,
        "relation": relation,
        "emitted_by": emitted_by,
        "inferred": inferred,
    }


# Eleven nodes: one seed script, three corpus files, one pinned external
# source, two report ledgers, one ledger section, two analysis claims, one
# release claim. The shape mirrors design section 4's chain (seed -> corpus
# -> ledger -> section -> analysis claim -> release claim) with two side
# branches that exist to be NOT traversed.
NODES = [
    _node("seed.compression", "seed_script", "scripts/seed_compression.py"),
    _node("corpus.alpha", "corpus_file", "scripts/seed_compression.py"),
    _node("corpus.beta", "corpus_file", "scripts/seed_compression.py"),
    _node("corpus.gamma", "corpus_file", "scripts/ingest_gamma.py"),
    _node("source.wals", "external_source", ""),
    _node("ledger.compression", "report_ledger",
          "scripts/measure_compression.py"),
    _node("ledger.decompositions", "report_ledger", "scripts/decompose.py"),
    _node("section.compression.table", "ledger_section",
          "scripts/assemble_graph.py"),
    _node("claim.analysis.rate", "analysis_claim",
          "scripts/assemble_graph.py"),
    _node("claim.analysis.blind", "analysis_claim",
          "scripts/assemble_graph.py"),
    _node("claim.release.v015", "release_claim",
          "scripts/assemble_graph.py"),
]

# Edges read "from_node was derived from to_node", so a closure runs them
# backwards. Emitted (inferred: false) derived_from edges are the only ones
# a scored closure traverses (design section 4, Clarification).
EDGES = [
    _edge("e01", "corpus.alpha", "seed.compression", "derived_from",
          "scripts/seed_compression.py", False),
    _edge("e02", "corpus.beta", "seed.compression", "derived_from",
          "scripts/seed_compression.py", False),
    _edge("e03", "ledger.compression", "corpus.alpha", "derived_from",
          "scripts/measure_compression.py", False),
    _edge("e04", "section.compression.table", "ledger.compression",
          "derived_from", "scripts/assemble_graph.py", False),
    _edge("e05", "claim.analysis.rate", "section.compression.table",
          "derived_from", "scripts/assemble_graph.py", False),
    _edge("e06", "claim.release.v015", "claim.analysis.rate", "derived_from",
          "scripts/assemble_graph.py", False),
    # Hand-recovered: excluded from the closure, and published as excluded.
    _edge("e07", "claim.analysis.blind", "ledger.compression", "derived_from",
          "hand", True),
    _edge("e08", "claim.analysis.blind", "ledger.decompositions",
          "derived_from", "scripts/assemble_graph.py", False),
    _edge("e09", "ledger.decompositions", "corpus.beta", "derived_from",
          "scripts/decompose.py", False),
    # pinned_from / asserted_by / published_in are never traversed. Each of
    # these would pull an extra node in if a recheck traversed its relation,
    # so the passing case below is evidence that none of them is traversed.
    _edge("e10", "corpus.gamma", "ledger.compression", "pinned_from",
          "scripts/ingest_gamma.py", False),
    _edge("e11", "corpus.gamma", "source.wals", "pinned_from",
          "scripts/ingest_gamma.py", False),
    _edge("e12", "claim.analysis.rate", "section.compression.table",
          "asserted_by", "scripts/assemble_graph.py", False),
    _edge("e13", "claim.release.v015", "ledger.compression", "published_in",
          "scripts/assemble_graph.py", False),
    # Inferred, and its to_node is outside the closure: it would NOT have
    # joined the closure even if inferred edges were scored. Corruption (c)
    # publishes it as excluded anyway.
    _edge("e14", "claim.analysis.blind", "corpus.beta", "derived_from",
          "hand", True),
]

# Closure of ledger.compression, computed by hand from EDGES:
#   depth 0: ledger.compression                     (the root)
#   depth 1: section.compression.table              (e04, emitted)
#            - e07 also lands on the root but is inferred: excluded
#            - e10 (pinned_from) and e13 (published_in) are not traversed
#   depth 2: claim.analysis.rate                    (e05, from depth 1)
#   depth 3: claim.release.v015                     (e06, from depth 2)
#   nothing else: e03's from_node IS the root; e01/e02/e09 land on nodes
#   outside the set; e08 lands on ledger.decompositions, never reached.
ROOT = "ledger.compression"
EXPECTED_CLOSURE = [
    "claim.analysis.rate",
    "claim.release.v015",
    "ledger.compression",
    "section.compression.table",
]
EXPECTED_HISTOGRAM = {"0": 1, "1": 1, "2": 1, "3": 1}
EXPECTED_EXCLUDED = ["e07"]

STANDING_LIMITATION = json.loads(
    CERTIFICATE_SCHEMA_PATH.read_text(encoding="utf-8")
)["properties"]["standing_limitation"]["const"]

_TEMPORARY: tempfile.TemporaryDirectory | None = None
FIXTURE: dict = {}


def setUpModule() -> None:
    """Write the graph once; every case reuses those exact bytes."""

    global _TEMPORARY
    _TEMPORARY = tempfile.TemporaryDirectory()
    root = Path(_TEMPORARY.name)
    reports = root / "reports" / "radius"
    reports.mkdir(parents=True)
    graph_path = root / "reports" / "provenance_graph.jsonl"
    lines = [
        json.dumps(record, sort_keys=True, separators=(",", ":"))
        for record in NODES + EDGES
    ]
    graph_path.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))

    certificate = {
        "cert_id": "fixture-ledger-compression-0001",
        "root_node": ROOT,
        "root_falsification_kind": "ledger_stale",
        "closure": list(EXPECTED_CLOSURE),
        "closure_size": len(EXPECTED_CLOSURE),
        "depth_histogram": dict(EXPECTED_HISTOGRAM),
        "unprovenanced_nodes": ["claim.analysis.blind"],
        "inferred_edges_excluded": list(EXPECTED_EXCLUDED),
        "graph_sha256": radius_recheck.sha256_lf_file(graph_path),
        "tool_version": "radius-fixture/1",
        "recheck_command": (
            "python scripts/radius_recheck.py "
            "reports/radius/fixture-ledger-compression-0001.cert.json"
        ),
        "standing_limitation": STANDING_LIMITATION,
    }
    FIXTURE.update(
        {
            "root": root,
            "graph_path": graph_path,
            "certificate": certificate,
            "reports": reports,
        }
    )


def tearDownModule() -> None:
    if _TEMPORARY is not None:
        _TEMPORARY.cleanup()


def _write_certificate(name: str, certificate: dict) -> Path:
    path = FIXTURE["reports"] / f"{name}.cert.json"
    path.write_bytes(
        (json.dumps(certificate, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
    )
    return path


def _corrupted(**changes) -> dict:
    certificate = copy.deepcopy(FIXTURE["certificate"])
    certificate.update(changes)
    return certificate


class TheFixtureIsWellFormed(unittest.TestCase):
    """Nothing below means anything if the fixtures are not schema-legal."""

    def test_certificate_validates_against_the_schema(self) -> None:
        schema = json.loads(
            CERTIFICATE_SCHEMA_PATH.read_text(encoding="utf-8")
        )
        jsonschema.Draft202012Validator(schema).validate(
            FIXTURE["certificate"]
        )

    def test_every_graph_line_validates_against_the_schema(self) -> None:
        schema = json.loads(GRAPH_SCHEMA_PATH.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        text = FIXTURE["graph_path"].read_text(encoding="utf-8")
        records = [
            json.loads(line) for line in text.splitlines() if line.strip()
        ]
        self.assertEqual(len(records), len(NODES) + len(EDGES))
        for record in records:
            validator.validate(record)


class TheRecheckAcceptsACorrectCertificate(unittest.TestCase):

    def test_hand_computed_closure_is_re_derived(self) -> None:
        path = _write_certificate("correct", FIXTURE["certificate"])
        report = radius_recheck.recheck(path, FIXTURE["graph_path"])
        self.assertIsNone(report.first_mismatch)
        self.assertTrue(report.ok)
        self.assertEqual(list(report.derived_closure), EXPECTED_CLOSURE)
        self.assertEqual(report.closure_size, 4)
        self.assertTrue(all(check.ok for check in report.checks))

    def test_the_graph_defaults_to_the_tree_the_certificate_lives_in(
        self,
    ) -> None:
        path = _write_certificate("correct-default", FIXTURE["certificate"])
        report = radius_recheck.recheck(path)
        self.assertTrue(report.ok, report.first_mismatch)

    def test_main_exits_zero_and_prints_only_ok_lines(self) -> None:
        path = _write_certificate("correct-main", FIXTURE["certificate"])
        self.assertEqual(
            radius_recheck.main([str(path), "--graph",
                                 str(FIXTURE["graph_path"])]),
            0,
        )

    def test_unscored_relations_and_inferred_edges_are_not_traversed(
        self,
    ) -> None:
        """corpus.gamma and claim.analysis.blind stay out, by construction.

        e10 (pinned_from) and e13 (published_in) both point at the root, and
        e07 (inferred derived_from) does too. A recheck that traversed any
        of the three would return a larger closure than the hand count.
        """

        path = _write_certificate("correct-relations", FIXTURE["certificate"])
        report = radius_recheck.recheck(path, FIXTURE["graph_path"])
        self.assertTrue(report.ok, report.first_mismatch)
        self.assertNotIn("corpus.gamma", report.derived_closure)
        self.assertNotIn("claim.analysis.blind", report.derived_closure)


class TheRecheckNamesTheFirstBreak(unittest.TestCase):

    def test_a_closure_missing_one_node_is_named(self) -> None:
        # Drop the deepest member, and adjust size and histogram with it, so
        # that membership is the ONLY thing left to disagree about.
        certificate = _corrupted(
            closure=[
                node
                for node in EXPECTED_CLOSURE
                if node != "claim.release.v015"
            ],
            closure_size=3,
            depth_histogram={"0": 1, "1": 1, "2": 1},
        )
        path = _write_certificate("missing-node", certificate)
        report = radius_recheck.recheck(path, FIXTURE["graph_path"])
        self.assertFalse(report.ok)
        self.assertIn("MISMATCH: closure", report.first_mismatch)
        self.assertIn("claim.release.v015", report.first_mismatch)
        self.assertEqual(
            radius_recheck.main([str(path), "--graph",
                                 str(FIXTURE["graph_path"])]),
            1,
        )

    def test_a_wrong_graph_hash_refuses_before_re_deriving(self) -> None:
        wrong = hashlib.sha256(b"not the pinned graph").hexdigest()
        certificate = _corrupted(graph_sha256=wrong)
        path = _write_certificate("wrong-graph-hash", certificate)
        report = radius_recheck.recheck(path, FIXTURE["graph_path"])
        self.assertFalse(report.ok)
        self.assertIn("MISMATCH: graph_sha256", report.first_mismatch)
        self.assertIn(wrong, report.first_mismatch)
        self.assertIn("refusing to re-derive", report.first_mismatch)
        # Refusal means refusal: no closure was derived at all.
        self.assertEqual(report.closure_size, 0)
        self.assertEqual(
            [check.what for check in report.checks if "closure" in check.what],
            [],
        )
        self.assertEqual(
            radius_recheck.main([str(path), "--graph",
                                 str(FIXTURE["graph_path"])]),
            1,
        )

    def test_an_excluded_edge_that_would_never_have_joined_is_named(
        self,
    ) -> None:
        # e14 is inferred, but it lands on corpus.beta, which is outside the
        # closure; scoring it would still not have added claim.analysis.blind
        # to THIS closure, so publishing it as excluded overstates what the
        # gate refused to count.
        certificate = _corrupted(inferred_edges_excluded=["e07", "e14"])
        path = _write_certificate("phantom-excluded-edge", certificate)
        report = radius_recheck.recheck(path, FIXTURE["graph_path"])
        self.assertFalse(report.ok)
        self.assertIn(
            "MISMATCH: inferred_edges_excluded", report.first_mismatch
        )
        self.assertIn("e14", report.first_mismatch)
        self.assertNotIn("e07", report.first_mismatch)
        self.assertEqual(
            radius_recheck.main([str(path), "--graph",
                                 str(FIXTURE["graph_path"])]),
            1,
        )


class TheGateNumberIsNotRestated(unittest.TestCase):

    def test_the_limit_comes_from_the_schema_const(self) -> None:
        schema = json.loads(
            CERTIFICATE_SCHEMA_PATH.read_text(encoding="utf-8")
        )
        const = schema["$defs"]["gate"]["properties"]["r4_recheck_seconds"][
            "const"
        ]
        self.assertEqual(radius_recheck.recheck_seconds_limit(), const)
        path = _write_certificate("limit", FIXTURE["certificate"])
        report = radius_recheck.recheck(path, FIXTURE["graph_path"])
        self.assertEqual(report.limit_seconds, const)
        self.assertLessEqual(report.duration_seconds, const)
        self.assertIn(
            f"recheck_seconds {report.duration_seconds:.3f} of {const} "
            f"allowed",
            report.render(),
        )


if __name__ == "__main__":
    unittest.main()
