#!/usr/bin/env python3
"""The v0.16 preregistration, committed before the graph, tool, or check.

This file is authored BEFORE ``scripts/provenance_graph.py``,
``scripts/retraction_radius.py``, and ``scripts/check_report_regeneration.py``
exist, and that ordering is the whole reason it is worth committing. A
construction gate written after the artifact it judges can only ask whether
the tool does what the tool does. Written first, it asks whether the tool does
what DESIGN-retraction-closure registered. Three tests therefore FAIL on this
commit with ``ModuleNotFoundError``. They are not skipped and not marked
expected-failure, because a skip is invisible in a summary line and an
expected failure would turn green the moment the module appeared, before
anyone read what it produced.

The six clauses of DESIGN-retraction-closure §6, quoted verbatim so that the
gate cannot drift from the document while the tests keep passing:

- **R1 — writers emit their own edges.** ≥95% of edges into
  `report_ledger` and `ledger_section` nodes carry `inferred: false`.
  Mid-cycle checkpoint: if the writers cannot be made to emit without
  rewriting a frozen instrument, fold the direction and publish the fold.
- **R2 — the live drifts are explained, superset-exactly.** For each of
  the two stale-ledger roots, the computed closure must be a superset of
  the pre-committed hand-audited ground truth, with
  `closure_size ≤ 3 × |ground truth|`. One missed claim voids the
  capability; no patch-and-rerun — a re-run after any graph edit is a new
  preregistration.
- **R3 — coverage floor.** ≥90% of the current release's claims resolve
  to anchored nodes with complete inbound edges; the remainder are listed
  as unprovenanced on every certificate that touches them.
- **R4 — independent recheck.** A recheck script re-derives every
  published closure from `(graph, root)` in ≤10 minutes on the declared
  host, hashes matching.
- **R5 — byte reproducibility.** Two clean builds reproduce
  `graph_sha256` byte-identically, or every certificate in the cycle is
  void.
- **R6 — historical replays reported, not scored.** Both retraction
  replays are published with their actual (small) closures and the
  sentence that they are interpretation-shaped and therefore calibrate
  the graph's *floor*, not its adequacy.

**Blind control.** 100 degree-preserving, kind-preserving edge shuffles of
the real graph, seeds committed in advance, each run against both live
drift roots. *If one or more of the 100 shuffled graphs satisfies R2 on
both roots, the real edges carry no consequence-relevant information and
this capability is void.* A perfect-looking control kills the capability,
not the control.

The 100 control seeds are frozen in ``data/retraction_closure/shuffle_seeds.json``
and are derived, not drawn: seeds chosen after a shuffle was seen to behave
would convert the control from a test into a search. The derivation is
recomputed here from the rule stated in the file itself, so the committed
integers are checked rather than trusted.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

import jsonschema

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "experiments"))

SEEDS_PATH = REPO / "data" / "retraction_closure" / "shuffle_seeds.json"
GROUND_TRUTH_PATHS = {
    "a": REPO / "data" / "retraction_closure" / "ground_truth_root_a.json",
    "b": REPO / "data" / "retraction_closure" / "ground_truth_root_b.json",
}
GRAPH_SCHEMA_PATH = REPO / "schema" / "provenance-graph.schema.json"
CERT_SCHEMA_PATH = REPO / "schema" / "radius-certificate.schema.json"
GRAPH_PATH = REPO / "reports" / "provenance_graph.jsonl"

SHUFFLE_COUNT = 100
SEED_PREFIX = b"retraction-closure-shuffle-"

GROUND_TRUTH_SCHEMA = "retraction-ground-truth/1"

#: R2's two roots and the size of each hand-audited list, frozen here so the
#: lists cannot grow a claim after the radius tool has been seen to miss one.
#: The ratio clause is ``closure_size <= 3 x |ground truth|``; a denominator
#: that can move on the day of the run is not a denominator.
GROUND_TRUTH_COUNTS = {"a": 11, "b": 16}
GROUND_TRUTH_ROOTS = {
    "a": "reports/compression.json",
    "b": "reports/decompositions.json",
}

#: §3's correction names the healed window by commit; root A's block carries
#: all four so the window is auditable from git without re-reading the design.
ROOT_A_WINDOW_KEYS = {"last_true_write", "staleness_begins", "healed", "note"}
ROOT_A_WINDOW_COMMITS = {
    "last_true_write": "e6d24cf",
    "staleness_begins": "3e6356c",
    "healed": "1090aa5",
}

CLAIM_CLASSES = {"assumes_fresh", "declared_snapshot"}

#: §6's numbers, transcribed from the design and asserted against the schema's
#: own copy. Two independent transcriptions of the same frozen constants: if
#: either moves, this file fails rather than the gate quietly moving.
DESIGN_GATE = {
    "r1_emitted_edge_fraction": 0.95,
    "r2_closure_to_ground_truth_ratio": 3,
    "r3_anchored_claims_floor": 0.9,
    "r4_recheck_seconds": 600,
    "r5_identical_builds": 2,
    "blind_shuffle_count": 100,
}

STANDING_LIMITATION = (
    "This graph records data lineage, not conceptual dependency; a "
    "convention shared by many artifacts and an input to none is outside "
    "it. See DESIGN-retraction-closure section 7."
)

NODE_KINDS = {
    "seed_script",
    "corpus_file",
    "external_source",
    "report_ledger",
    "ledger_section",
    "analysis_claim",
    "release_claim",
}

EDGE_RELATIONS = {
    "derived_from",
    "pinned_from",
    "asserted_by",
    "published_in",
}


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _object_schemas(node, trail="$"):
    """Every subschema that constrains an object's members, with its path.

    Walks values rather than keys: a subschema can sit under ``properties``,
    ``$defs``, ``items``, ``oneOf``, or ``patternProperties``, and a closure
    test that only knew about ``properties`` would miss exactly the branch an
    author forgot to close.
    """

    if isinstance(node, dict):
        if "properties" in node or "patternProperties" in node:
            yield trail, node
        for key, value in node.items():
            yield from _object_schemas(value, f"{trail}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _object_schemas(value, f"{trail}[{index}]")


class PreregistrationIsFrozen(unittest.TestCase):
    """The committed numbers, seeds, and schema shapes, before any builder."""

    def test_the_hundred_control_seeds_match_their_stated_derivation(
        self,
    ) -> None:
        seeds_file = _load(SEEDS_PATH)
        self.assertEqual(seeds_file["schema"], "retraction-shuffle-seeds/1")
        seeds = seeds_file["seeds"]
        self.assertEqual(len(seeds), SHUFFLE_COUNT)
        self.assertEqual(len(set(seeds)), SHUFFLE_COUNT)
        for value in seeds:
            self.assertIsInstance(value, int)
            self.assertGreaterEqual(value, 0)
            self.assertLess(value, 2 ** 32)
        recomputed = [
            int.from_bytes(
                hashlib.sha256(
                    SEED_PREFIX + str(index).encode("ascii")
                ).digest()[:4],
                "big",
            )
            for index in range(SHUFFLE_COUNT)
        ]
        self.assertEqual(seeds, recomputed)

    def test_the_seeds_file_states_the_rule_it_was_derived_from(self) -> None:
        """The rule travels with the integers or the integers are opaque."""

        rule = _load(SEEDS_PATH)["rule"]
        self.assertIn("sha256", rule)
        self.assertIn("retraction-closure-shuffle-", rule)
        self.assertIn("[:4]", rule)
        self.assertIn("0..99", rule)

    def test_both_schemas_parse_and_declare_draft_2020_12(self) -> None:
        for path in (GRAPH_SCHEMA_PATH, CERT_SCHEMA_PATH):
            schema = _load(path)
            self.assertEqual(
                schema["$schema"],
                "https://json-schema.org/draft/2020-12/schema",
                path.name,
            )
            jsonschema.Draft202012Validator.check_schema(schema)

    def test_every_object_subschema_is_closed(self) -> None:
        for path in (GRAPH_SCHEMA_PATH, CERT_SCHEMA_PATH):
            for trail, subschema in _object_schemas(_load(path)):
                self.assertIs(
                    subschema.get("additionalProperties"),
                    False,
                    f"{path.name}: {trail}",
                )

    def test_the_graph_schema_freezes_the_node_kinds_and_relations(
        self,
    ) -> None:
        defs = _load(GRAPH_SCHEMA_PATH)["$defs"]
        node = defs["nodeRecord"]["properties"]
        edge = defs["edgeRecord"]["properties"]
        self.assertEqual(node["record"]["const"], "node")
        self.assertEqual(edge["record"]["const"], "edge")
        self.assertEqual(set(node["kind"]["enum"]), NODE_KINDS)
        self.assertEqual(set(edge["relation"]["enum"]), EDGE_RELATIONS)
        self.assertEqual(
            edge["inferred"]["$comment"],
            "an edge reconstructed after the fact; excluded from every "
            "scored clause (design §4)",
        )

    def test_the_certificate_schema_carries_the_standing_limitation(
        self,
    ) -> None:
        """§7's limitation is a const, not prose the tool may reword."""

        schema = _load(CERT_SCHEMA_PATH)
        self.assertEqual(
            schema["properties"]["standing_limitation"]["const"],
            STANDING_LIMITATION,
        )
        self.assertIn("standing_limitation", schema["required"])

    def test_the_certificate_schema_requires_the_inconvenient_fields(
        self,
    ) -> None:
        """A certificate that could omit its remainder would under-report."""

        schema = _load(CERT_SCHEMA_PATH)
        for field in (
            "cert_id",
            "root_node",
            "root_falsification_kind",
            "closure",
            "closure_size",
            "depth_histogram",
            "unprovenanced_nodes",
            "inferred_edges_excluded",
            "graph_sha256",
            "tool_version",
            "recheck_command",
            "standing_limitation",
        ):
            self.assertIn(field, schema["required"], field)
            self.assertIn(field, schema["properties"], field)
        self.assertEqual(
            set(schema["properties"]["root_falsification_kind"]["enum"]),
            {
                "witness_invalid",
                "source_unpinned",
                "standing_demoted",
                "script_defect",
                "ledger_stale",
            },
        )

    def test_the_frozen_gate_numbers_are_consts_in_the_schema(self) -> None:
        gate = _load(CERT_SCHEMA_PATH)["$defs"]["gate"]["properties"]
        self.assertEqual(set(gate), set(DESIGN_GATE))
        for name, expected in DESIGN_GATE.items():
            self.assertEqual(gate[name]["const"], expected, name)

    def test_the_shuffle_count_is_the_same_number_in_both_places(self) -> None:
        """The seeds file and the schema's control clause cannot disagree."""

        gate = _load(CERT_SCHEMA_PATH)["$defs"]["gate"]["properties"]
        self.assertEqual(
            gate["blind_shuffle_count"]["const"],
            len(_load(SEEDS_PATH)["seeds"]),
        )


class SeedsRegenerate(unittest.TestCase):
    """The seeds file is output, not input: the seeder reproduces it."""

    def test_the_seeder_reproduces_the_committed_bytes(self) -> None:
        # Imported, not subprocessed: a subprocess would rewrite the working
        # tree, and the point here is that the committed text already equals
        # what the seeder builds.
        import seed_retraction_closure  # noqa: PLC0415

        self.assertEqual(
            seed_retraction_closure.render(seed_retraction_closure.build()),
            SEEDS_PATH.read_text(encoding="utf-8"),
        )

    def test_the_seeder_owns_the_committed_path_and_count(self) -> None:
        import seed_retraction_closure  # noqa: PLC0415

        self.assertEqual(seed_retraction_closure.OUT_PATH, SEEDS_PATH)
        self.assertEqual(seed_retraction_closure.SHUFFLE_COUNT, SHUFFLE_COUNT)


class GroundTruthIsCommitted(unittest.TestCase):
    """The two hand-audited R2 lists, verified against the working tree.

    §5 step 4 requires the ground truth committed BEFORE the radius tool runs
    on either root, and §6's R2 makes ``|ground truth|`` the denominator of
    the ratio clause. Both properties are worthless if the quotes are
    approximate: a claim recorded with prose that no longer appears in its
    file is a node the assembler can never anchor, and it would fail R2 as a
    tool defect rather than as the transcription error it is. So every quote
    is checked here as a real substring of the file it names, and every
    anchor as a real heading string in that file, on every run.

    Whitespace is collapsed on both sides before comparing. Markdown wraps
    prose at the author's column and rewraps it whenever a word changes
    length; a ground-truth list that broke on rewrapping would train its
    maintainer to loosen the check.

    These two files are INPUT, not output: they are hand-audited and
    adjudicated by a human reading, and ``scripts/seed_retraction_closure.py``
    deliberately does not own them. A seeder that could regenerate this list
    would be a program deciding what the program's published claims are.
    """

    @staticmethod
    def _collapse(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    def test_both_files_parse_and_declare_the_schema_and_root(self) -> None:
        for key, path in GROUND_TRUTH_PATHS.items():
            doc = _load(path)
            self.assertEqual(doc["schema"], GROUND_TRUTH_SCHEMA, key)
            self.assertEqual(doc["root"]["artifact"], GROUND_TRUTH_ROOTS[key])
            self.assertEqual(
                doc["root"]["falsification_kind"], "ledger_stale", key
            )
            self.assertTrue(doc["root"]["story"].strip(), key)

    def test_the_claim_counts_are_the_adjudicated_ones(self) -> None:
        """R2's denominator, frozen: 11 and 16, neither more nor fewer."""

        for key, path in GROUND_TRUTH_PATHS.items():
            claims = _load(path)["claims"]
            self.assertEqual(len(claims), GROUND_TRUTH_COUNTS[key], key)
            ids = [claim["id"] for claim in claims]
            self.assertEqual(len(set(ids)), len(ids), key)

    def test_every_claim_is_classed_as_fresh_or_snapshot(self) -> None:
        """The whole point of root B is telling those two apart."""

        for key, path in GROUND_TRUTH_PATHS.items():
            for claim in _load(path)["claims"]:
                self.assertIn(claim["class"], CLAIM_CLASSES, claim["id"])
                self.assertTrue(claim["derives_from"], claim["id"])
                self.assertTrue(claim["note"].strip(), claim["id"])

    def test_every_quote_is_a_live_substring_of_its_file(self) -> None:
        texts: dict[str, str] = {}
        for key, path in GROUND_TRUTH_PATHS.items():
            for claim in _load(path)["claims"]:
                self.assertIsNotNone(claim["quote"], claim["id"])
                self.assertNotIn("discrepancy", claim, claim["id"])
                target = REPO / claim["file"]
                self.assertTrue(target.is_file(), claim["file"])
                if claim["file"] not in texts:
                    texts[claim["file"]] = self._collapse(
                        target.read_text(encoding="utf-8")
                    )
                haystack = texts[claim["file"]]
                quote = self._collapse(claim["quote"])
                self.assertGreaterEqual(len(quote.split()), 5, claim["id"])
                self.assertLessEqual(len(quote.split()), 30, claim["id"])
                self.assertIn(quote, haystack, f"{key}/{claim['id']} quote")
                self.assertIn(
                    self._collapse(claim["anchor"]),
                    haystack,
                    f"{key}/{claim['id']} anchor",
                )

    def test_the_excluded_lists_carry_their_reasons(self) -> None:
        """Design §4: nothing is silently omitted; exclusions are stated."""

        for key, path in GROUND_TRUTH_PATHS.items():
            excluded = _load(path)["excluded"]
            self.assertTrue(excluded, key)
            for entry in excluded:
                self.assertEqual(set(entry), {"what", "reason"}, key)
                self.assertTrue(entry["what"].strip(), key)
                self.assertTrue(entry["reason"].strip(), key)

    def test_both_lists_were_audited_on_the_same_date(self) -> None:
        """One adjudication pass, or the two roots are not comparable."""

        dates = {
            key: _load(path)["audit"]["date"]
            for key, path in GROUND_TRUTH_PATHS.items()
        }
        self.assertEqual(dates["a"], dates["b"])
        for key, path in GROUND_TRUTH_PATHS.items():
            method = _load(path)["audit"]["method"]
            self.assertIn("adjudication", method, key)
            self.assertIn(Path(__file__).name, method, key)

    def test_root_a_names_the_four_commits_of_its_stale_window(self) -> None:
        window = _load(GROUND_TRUTH_PATHS["a"])["window"]
        self.assertEqual(set(window), ROOT_A_WINDOW_KEYS)
        for field, prefix in ROOT_A_WINDOW_COMMITS.items():
            self.assertEqual(window[field], prefix, field)
        self.assertIn("c1c8202", window["note"])

    def test_root_b_declares_no_window_because_it_never_went_stale(
        self,
    ) -> None:
        """A declared snapshot has no staleness window to reconstruct."""

        self.assertNotIn("window", _load(GROUND_TRUTH_PATHS["b"]))

    def test_the_seeder_does_not_own_the_hand_audited_files(self) -> None:
        """These are inputs. A generator for them would defeat the audit."""

        import seed_retraction_closure  # noqa: PLC0415

        source = Path(seed_retraction_closure.__file__).read_text(
            encoding="utf-8"
        )
        for path in GROUND_TRUTH_PATHS.values():
            self.assertNotIn(path.name, source, path.name)
            self.assertNotEqual(seed_retraction_closure.OUT_PATH, path)


class GateAssemblerBuildsTheGraph(unittest.TestCase):
    """Red by construction until the builder lands — that is the
    preregistration working."""

    def test_the_assembler_emits_records_that_validate(self) -> None:
        # R1's emitted-edge fraction, R3's coverage floor, and R5's two-build
        # reproduction are asserted here once the assembler exists; today the
        # import is the assertion, and it fails.
        import provenance_graph  # noqa: PLC0415

        provenance_graph.build_graph(REPO)
        schema = _load(GRAPH_SCHEMA_PATH)
        validator = jsonschema.Draft202012Validator(schema)
        lines = GRAPH_PATH.read_text(encoding="utf-8").splitlines()
        self.assertGreater(len(lines), 0)
        for line in lines:
            validator.validate(json.loads(line))


class GateRadiusToolAnswers(unittest.TestCase):
    """Red by construction until the builder lands — that is the
    preregistration working."""

    def test_the_radius_tool_certifies_a_root(self) -> None:
        # R2 (superset-exact against the pre-committed ground truth, ratio
        # ≤ 3) and R4 (recheck ≤ 600s, hashes matching) attach here when the
        # tool and the two hand-audited drift lists both exist.
        import retraction_radius  # noqa: PLC0415

        self.assertTrue(hasattr(retraction_radius, "certify"))


class GateRegenerationCheckRuns(unittest.TestCase):
    """Red by construction until the builder lands — that is the
    preregistration working."""

    def test_the_regeneration_check_reports_the_live_drifts(self) -> None:
        # R2's roots per the design's §3 correction: a HEALED silent drift
        # (compression.json, repaired at 1090aa5 with no radius computed)
        # and a DECLARED divergence (decompositions.json, the pre-scale
        # ledger by decision). The check must tell those two shapes apart —
        # a declared snapshot is not a drift — and that distinction's
        # assertion lands with the check.
        import check_report_regeneration  # noqa: PLC0415

        self.assertTrue(hasattr(check_report_regeneration, "main"))


if __name__ == "__main__":
    unittest.main()
