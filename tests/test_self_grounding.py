"""Self-grounding curve: metric, null, adjudication. No 12k analyze.

S1–S4 live in docs/DESIGN-self-grounding-ingestion.md and are restated in
scripts/measure_self_grounding.py. This file checks the closed forms on
fixtures so a full-graph run cannot silently redefine them.

Vacuity (AGENTS.md working method 3): a capability-blind "any shared
owner" baseline — route 2, the rejected proxy — scores a fixture as
self-grounding when route 1 does not. If that baseline were the test,
S1 would fire on co-occurrence alone. The fixture exists to keep that
distinction load-bearing.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from match_signatures import Parser, canonicalize, tokenize  # noqa: E402
from measure_self_grounding import (  # noqa: E402
    SCHEMA,
    adjudicate,
    classify_constituent,
    generate_synthetic,
    observed_inventory,
    render_template,
    score_entries,
    subsample,
)


def _entry(sid: str, considered: int, constituents: list[dict]) -> dict:
    return {
        "statement_id": sid,
        "considered": considered,
        "constituents": constituents,
    }


def _exact(skel: str, channel: str, owners: list[str]) -> dict:
    return {
        "skeleton": skel,
        "grounded_via": "exact",
        "channel": channel,
        "owners": owners,
        "owner_channels": {channel: len(owners)},
    }


class ClassifyAndScore(unittest.TestCase):
    def setUp(self):
        # Two ingested siblings, one curated owner. Shared discipline so a
        # prior_corpus owner can be curated.
        self.ingested = {"ing.a", "ing.b"}
        self.corpus_of = {
            "ing.a": "lean_workbook.ground.v1",
            "ing.b": "lean_workbook.ground.v1",
            "curated.law": "algebra.foundations.v1",
        }
        self.disc = {
            "ing.a": frozenset({"number_theory"}),
            "ing.b": frozenset({"number_theory"}),
            "curated.law": frozenset({"number_theory"}),
        }

    def test_winning_channel_all_ingested_is_isg(self):
        c = _exact("+(2, 30)", "same_corpus", ["ing.b"])
        self.assertEqual(
            classify_constituent(
                "ing.a", c, self.ingested, self.corpus_of, self.disc),
            "isg")

    def test_winning_channel_curated_is_xsg_even_if_a_sibling_also_hosts(self):
        """Route 1 vs route 2. External/prior wins; the sibling is ignored."""
        # prior_corpus beats same_corpus. curated.law shares number_theory
        # and is a different corpus, so it is prior_corpus.
        c = _exact("^(2, 30)", "prior_corpus", ["curated.law", "ing.b"])
        self.assertEqual(
            classify_constituent(
                "ing.a", c, self.ingested, self.corpus_of, self.disc),
            "xsg")

    def test_proxy_fires_on_the_same_fixture_route1_calls_xsg(self):
        """Vacuity check: the rejected proxy cannot be the test."""
        c = _exact("^(2, 30)", "prior_corpus", ["curated.law", "ing.b"])
        entries = [_entry("ing.a", 1, [c])]
        scored = score_entries(
            entries, self.ingested, self.corpus_of, self.disc)
        self.assertEqual(scored["isg"], 0)
        self.assertEqual(scored["xsg"], 1)
        self.assertEqual(scored["proxy"], 1)
        self.assertEqual(scored["isg_rate"], 0.0)
        self.assertEqual(scored["proxy_rate"], 1.0)

    def test_raw_counts_travel_with_rates(self):
        c = _exact("+(1, 1)", "same_corpus", ["ing.b"])
        scored = score_entries(
            [_entry("ing.a", 4, [c])], self.ingested, self.corpus_of, self.disc)
        self.assertEqual(scored["considered"], 4)
        self.assertEqual(scored["isg"], 1)
        self.assertEqual(scored["isg_rate"], 0.25)
        self.assertEqual(scored["isg_of_grounded"], 1.0)

    def test_s4_drop_removes_the_skeleton_from_both_sides(self):
        kept = _exact("+(1, 2)", "same_corpus", ["ing.b"])
        drop = _exact("^(2, 30)", "same_corpus", ["ing.b"])
        scored = score_entries(
            [_entry("ing.a", 2, [kept, drop])],
            self.ingested, self.corpus_of, self.disc,
            drop_skeleton="^(2, 30)",
        )
        self.assertEqual(scored["considered"], 1)
        self.assertEqual(scored["isg"], 1)
        self.assertEqual(scored["dropped"], 1)
        self.assertEqual(scored["most_common_subterm"]["skeleton"], "+(1, 2)")


class NullGenerator(unittest.TestCase):
    def test_synthetic_templates_parse(self):
        inv = {
            "ops": [("+", 2), ("*", 2), ("^", 2), ("neg", 1)],
            "calls": [("SIN", 1), ("SQRT", 1)],
            "leaves": [("num", 2.0), ("num", 30.0), ("slot", "theta"), ("slot", "x")],
            "rels": ["=", ">="],
            "sizes": [3, 5, 8],
            "disc_sets": [("number_theory",)],
        }
        synths = generate_synthetic(20, inv, seed=0)
        self.assertEqual(len(synths), 20)
        for item in synths:
            tree = canonicalize(Parser(tokenize(item["template"])).parse())
            self.assertTrue(tree)
            self.assertTrue(item["statement_id"].startswith("null.synth.0."))
            self.assertEqual(item["corpus_id"], "lean_workbook.null.v1")

    def test_render_round_trips_the_heads_the_null_uses(self):
        trees = [
            ("rel", "=", (("op", "+", (("num", 2.0), ("num", 3.0))),
                          ("num", 5.0))),
            ("rel", ">=", (("call", "SIN", (("slot", "theta"),)),
                           ("op", "^", (("slot", "x"), ("num", 2.0))))),
            ("rel", "=", (("op", "neg", (("slot", "a"),)),
                          ("op", "inv", (("num", 2.0),)))),
        ]
        for tree in trees:
            text = render_template(tree)
            canonicalize(Parser(tokenize(text)).parse())

    def test_inventory_samples_observed_not_uniform(self):
        trees = {
            "i1": ("rel", "=", (("op", "+", (("num", 2.0), ("num", 2.0))),
                                ("num", 4.0))),
            "i2": ("rel", "=", (("op", "+", (("num", 2.0), ("num", 3.0))),
                                ("num", 5.0))),
        }
        inv = observed_inventory(
            ["i1", "i2"], trees,
            {"i1": frozenset({"number_theory"}),
             "i2": frozenset({"number_theory"})},
            {"i1": "lean_workbook.ground.v1",
             "i2": "lean_workbook.ground.v1"},
        )
        nums = [leaf[1] for leaf in inv["leaves"] if leaf[0] == "num"]
        self.assertEqual(nums.count(2.0), 3)
        self.assertEqual(nums.count(3.0), 1)


class AdjudicationPredicates(unittest.TestCase):
    def _point(self, n, real_isg, real_xsg, nulls, s4_real=None, s4_nulls=None,
               considered=100):
        def block(rate, xsg=0.0):
            return {
                "isg_rate": rate,
                "xsg_rate": xsg,
                "considered": considered,
                "isg": int(rate * considered),
                "xsg": int(xsg * considered),
            }
        if s4_real is None:
            s4_real = real_isg
        if s4_nulls is None:
            s4_nulls = nulls
        return {
            "n": n,
            "real": block(real_isg, real_xsg),
            "null": [{"seed": i, **block(r)} for i, r in enumerate(nulls)],
            "s4": {
                "dropped_skeleton": "^(2, 30)",
                "real": block(s4_real, real_xsg),
                "null": [{"seed": i, **block(r)} for i, r in enumerate(s4_nulls)],
            },
        }

    def test_s1_fires_when_the_gap_beats_the_null_spread(self):
        points = [
            self._point(8, 0.20, 0.40, [0.18, 0.19, 0.20]),
            self._point(32, 0.50, 0.35, [0.20, 0.21, 0.22]),
        ]
        v = adjudicate(points)
        self.assertTrue(v["S1"]["fired"])
        self.assertTrue(v["S2"]["fired"])
        self.assertTrue(v["S3"]["fired"])
        self.assertTrue(v["S4"]["fired"])

    def test_s1_misses_when_real_tracks_the_null(self):
        points = [
            self._point(8, 0.20, 0.40, [0.19, 0.20, 0.21]),
            self._point(32, 0.21, 0.39, [0.20, 0.21, 0.22]),
        ]
        v = adjudicate(points)
        self.assertFalse(v["S1"]["fired"])
        self.assertFalse(v["S2"]["fired"])

    def test_s3_misses_when_xsg_falls_more_than_isg_rises(self):
        points = [
            self._point(8, 0.10, 0.80, [0.05, 0.05, 0.05]),
            self._point(32, 0.20, 0.20, [0.05, 0.05, 0.05]),
        ]
        v = adjudicate(points)
        self.assertTrue(v["S1"]["fired"])
        self.assertFalse(v["S3"]["fired"])
        self.assertAlmostEqual(v["S3"]["isg_rise"], 0.10)
        self.assertAlmostEqual(v["S3"]["xsg_fall"], 0.60)

    def test_s4_misses_when_dropping_the_popular_term_kills_the_gap(self):
        points = [
            self._point(8, 0.40, 0.40, [0.10, 0.10, 0.10],
                        s4_real=0.11, s4_nulls=[0.10, 0.10, 0.10]),
            self._point(32, 0.50, 0.35, [0.10, 0.11, 0.12],
                        s4_real=0.11, s4_nulls=[0.10, 0.10, 0.11]),
        ]
        v = adjudicate(points)
        self.assertTrue(v["S1"]["fired"])
        self.assertFalse(v["S4"]["fired"])


class SelectionAndSchema(unittest.TestCase):
    def test_subsample_is_seeded_and_prefix_stable(self):
        ids = [f"s{i:03d}" for i in range(50)]
        a = subsample(ids, 8, seed=20260814)
        b = subsample(ids, 8, seed=20260814)
        c = subsample(ids, 8, seed=1)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 8)
        self.assertNotEqual(a, c)
        # Larger prefix at the same seed extends the smaller one.
        bigger = subsample(ids, 16, seed=20260814)
        self.assertEqual(bigger[:8], a)

    def test_committed_curve_schema_when_present(self):
        path = REPO / "experiments" / "self_grounding_curve.json"
        if not path.exists():
            self.skipTest("curve not yet generated")
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], SCHEMA)
        self.assertEqual(payload["route"], 1)
        self.assertEqual(payload["proxy_is"], "control")
        self.assertIn("specialize.py", payload["not_run"])
        self.assertGreaterEqual(len(payload["points"]), 2)
        for name in ("S1", "S2", "S3", "S4"):
            self.assertIn("fired", payload["adjudication"][name])
            self.assertIsInstance(payload["adjudication"][name]["fired"], bool)
            self.assertTrue(
                payload["adjudication"][name]["fired"],
                f"{name} was registered to fire and the committed curve must "
                f"keep that adjudication or rewrite it in the design",
            )
        for point in payload["points"]:
            real = point["real"]
            for key in ("considered", "isg", "xsg", "isg_rate", "xsg_rate",
                        "proxy", "proxy_rate"):
                self.assertIn(key, real)
            self.assertIsInstance(real["considered"], int)
            self.assertGreater(real["considered"], 0)


class TinyGraphSmoke(unittest.TestCase):
    """End-to-end on a temp corpus. Must not touch data/lean_workbook."""

    def test_measure_on_a_handful_of_nodes(self):
        from measure_self_grounding import measure  # noqa: E402

        curated = {
            "schema": "../../schema/equation-node.schema.json",
            "corpus_id": "algebra.foundations.v1",
            "discipline": "algebra",
            "statement_nodes": [
                {
                    "statement_id": "algebra.fixture.sum",
                    "theory_context": {"disciplines": ["algebra"]},
                    "structural_signature": {
                        "anonymized_template": "a + b = b + a",
                        "slot_schema": [
                            {"slot_id": "a", "syntactic_category": "variable"},
                            {"slot_id": "b", "syntactic_category": "variable"},
                        ],
                    },
                }
            ],
        }
        ingested = {
            "schema": "../../schema/equation-node.schema.json",
            "corpus_id": "lean_workbook.ground.v1",
            "discipline": "lean_workbook",
            "statement_nodes": [],
        }
        for i, tmpl in enumerate(
            ["2 + 3 = 5", "2 + 4 = 6", "2 * 3 = 6", "3 + 3 = 6",
             "2 ^ 3 = 8", "4 + 2 = 6", "2 + 2 = 4", "3 * 3 = 9",
             "2 * 2 = 4", "5 + 1 = 6"]
        ):
            ingested["statement_nodes"].append({
                "statement_id": f"leanworkbook.ground.n{i}",
                "theory_context": {"disciplines": ["number_theory"]},
                "structural_signature": {
                    "anonymized_template": tmpl,
                    "slot_schema": [{
                        "slot_id": "GROUND",
                        "syntactic_category": "constant",
                    }],
                },
            })
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "algebra").mkdir()
            (root / "lean_workbook").mkdir()
            (root / "algebra" / "nodes.json").write_text(
                json.dumps(curated), encoding="utf-8")
            (root / "lean_workbook" / "nodes.json").write_text(
                json.dumps(ingested), encoding="utf-8")
            result = measure(
                root,
                sizes=(4,),
                selection_seed=0,
                null_seeds=(0, 1),
                include_all=True,
            )
        self.assertEqual(result["schema"], SCHEMA)
        self.assertEqual(result["ingested_layer"], 10)
        self.assertEqual([p["n"] for p in result["points"]], [4, 10])
        for point in result["points"]:
            self.assertEqual(len(point["null"]), 2)
            self.assertIsInstance(point["real"]["isg_rate"], float)
            self.assertGreater(point["real"]["considered"], 0)
        for name in ("S1", "S2", "S3", "S4"):
            self.assertIn(name, result["adjudication"])


if __name__ == "__main__":
    unittest.main()
