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
import subprocess
import sys
import tempfile
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

    #: The tree the audit quoted: the rebased preregistration commit
    #: ("Preregister the retraction closure before any assembler can
    #: exist"). Quotes are anchors into the documents AS AUDITED. After
    #: the adjudication, documents legitimately rotate — the v0.16
    #: release pruned the BACKLOG entry claim a10 quotes, exactly as
    #: that entry's own prune condition required — so demanding
    #: liveness against the working tree forever would force either
    #: frozen docs or edited ground truth, both wrong. Liveness against
    #: the audited tree is the invariant that can and must hold.
    AUDIT_TIP = "20581cc"

    def _audited_text(self, rel_path: str) -> str:
        blob = subprocess.run(
            ["git", "show", f"{self.AUDIT_TIP}:{rel_path}"],
            cwd=REPO, check=True, capture_output=True,
        ).stdout.decode("utf-8")
        return self._collapse(blob)

    def test_every_quote_is_a_substring_of_its_file_as_audited(self) -> None:
        texts: dict[str, str] = {}
        for key, path in GROUND_TRUTH_PATHS.items():
            for claim in _load(path)["claims"]:
                self.assertIsNotNone(claim["quote"], claim["id"])
                self.assertNotIn("discrepancy", claim, claim["id"])
                if claim["file"] not in texts:
                    texts[claim["file"]] = self._audited_text(claim["file"])
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
    """The assembler exists, and what it writes is what §4 registered.

    Every build here goes to a TEMP path, never the committed one: the
    committed graph is the adjudicated run's sealed input — certificates
    pin its hash and the recheck refuses on mismatch — and a suite that
    rebuilt it over a later tree would silently break every published
    certificate. That is not hypothetical; it happened once, at the
    v0.16 release gate, and this class is the fix.
    """

    _tmp: tempfile.TemporaryDirectory | None = None
    _built: Path | None = None

    @classmethod
    def _fresh_build(cls) -> Path:
        import provenance_graph  # noqa: PLC0415

        if cls._built is None:
            cls._tmp = tempfile.TemporaryDirectory(prefix="graph-dev-")
            cls._built = provenance_graph.build_graph(
                REPO, Path(cls._tmp.name) / "provenance_graph.jsonl"
            )
        return cls._built

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._tmp is not None:
            cls._tmp.cleanup()

    def test_the_assembler_emits_records_that_validate(self) -> None:
        # R1's emitted-edge fraction and R5's two-build reproduction are
        # asserted here now that the assembler exists. R3's coverage floor
        # is not: it is scored over the current release's claims against a
        # certificate, not over the graph, and asserting a floor here would
        # move that judgement into a unit test.
        built = self._fresh_build()
        schema = _load(GRAPH_SCHEMA_PATH)
        validator = jsonschema.Draft202012Validator(schema)
        lines = built.read_text(encoding="utf-8").splitlines()
        self.assertGreater(len(lines), 0)
        for line in lines:
            validator.validate(json.loads(line))

    def test_every_registered_kind_is_populated_except_ledger_section(
        self,
    ) -> None:
        """Six kinds carry nodes; the seventh is empty, and says so.

        ``ledger_section`` is zero *by decision*, not by oversight: no
        published claim in this repository addresses a ledger's internal
        section, so v1 mints no such nodes and R1's denominator is edges
        into ``report_ledger`` nodes alone. Asserting the zero keeps that
        decision visible — when this assertion starts failing, someone
        added the kind and R1's denominator changed underneath the gate.
        """

        built = self._fresh_build()
        counts = {kind: 0 for kind in NODE_KINDS}
        for line in built.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if record["record"] == "node":
                counts[record["kind"]] += 1
        self.assertEqual(counts["ledger_section"], 0)
        for kind in sorted(NODE_KINDS - {"ledger_section"}):
            self.assertGreater(counts[kind], 0, kind)
        print(f"\nnode counts by kind: {dict(sorted(counts.items()))}")

    def test_r1_the_writers_emit_their_own_edges(self) -> None:
        """≥95% of edges into ledger nodes carry ``inferred: false``."""

        import provenance_graph  # noqa: PLC0415

        report = provenance_graph.summarize(self._fresh_build())
        print(
            f"\nR1 = {report['edges_into_ledgers_emitted']}"
            f"/{report['edges_into_ledgers']} = {report['r1_fraction']:.4f}"
            f"\nedges by relation: {report['relations']}"
            f"\nedges by emitter:  {report['emitted_by']}"
        )
        self.assertGreater(report["edges_into_ledgers"], 0)
        self.assertGreaterEqual(
            report["r1_fraction"], DESIGN_GATE["r1_emitted_edge_fraction"]
        )

    def test_r5_two_builds_reproduce_the_graph_byte_identically(self) -> None:
        """The in-test half of R5: same tree in, same bytes out.

        Not the whole clause — R5 says *clean* builds, and a second checkout
        is the release step's job — but a builder that cannot reproduce
        itself within one process will never reproduce itself across two
        machines, and this catches that failure in seconds instead of at
        publication.
        """

        import provenance_graph  # noqa: PLC0415

        with tempfile.TemporaryDirectory(prefix="graph-r5-") as tmp:
            first = provenance_graph.build_graph(
                REPO, Path(tmp) / "a.jsonl"
            ).read_bytes()
            second = provenance_graph.build_graph(
                REPO, Path(tmp) / "b.jsonl"
            ).read_bytes()
        self.assertEqual(first, second)
        self.assertNotIn(b"\r\n", first)


class GateRadiusToolAnswers(unittest.TestCase):
    """The tool answers one root, and the receipt validates."""

    def test_the_radius_tool_certifies_a_root(self) -> None:
        # R2 (superset-exact against the pre-committed hand-audited list,
        # ratio ≤ 3) is deliberately NOT asserted here. R2 is adjudicated
        # once, against a certificate written by the adjudicated run; a unit
        # test that scored it would turn "no patch-and-rerun" into "rerun
        # until green", which is the one thing §6 forbids by name.
        import provenance_graph  # noqa: PLC0415
        import retraction_radius  # noqa: PLC0415

        self.assertTrue(hasattr(retraction_radius, "certify"))
        self.assertTrue(
            GRAPH_PATH.is_file(),
            "the committed adjudicated graph is missing; it is an artifact, "
            "never rebuilt by the suite",
        )

        root = f"ledger:{GROUND_TRUTH_ROOTS['a']}"
        # A temp directory, not reports/radius/: the published certificate
        # belongs to the adjudicated run, and a suite that wrote one every
        # time it ran would make "one root, one certificate" meaningless.
        with tempfile.TemporaryDirectory(prefix="radius-dev-") as tmp:
            cert_path = retraction_radius.certify(
                GRAPH_PATH, root, "ledger_stale", "root-a-dev", Path(tmp)
            )
            cert = _load(cert_path)

        jsonschema.Draft202012Validator(_load(CERT_SCHEMA_PATH)).validate(cert)
        self.assertEqual(cert["root_node"], root)
        self.assertEqual(cert["root_falsification_kind"], "ledger_stale")
        self.assertIn(root, cert["closure"])
        self.assertGreater(cert["closure_size"], 0)
        self.assertEqual(cert["closure_size"], len(cert["closure"]))
        self.assertEqual(cert["closure"], sorted(set(cert["closure"])))
        # The histogram is the closure re-counted by depth: it must account
        # for every member exactly once, and depth 0 is the root alone.
        self.assertEqual(
            sum(cert["depth_histogram"].values()), cert["closure_size"]
        )
        self.assertEqual(cert["depth_histogram"]["0"], 1)
        self.assertEqual(cert["standing_limitation"], STANDING_LIMITATION)
        self.assertEqual(
            cert["standing_limitation"],
            _load(CERT_SCHEMA_PATH)["properties"]["standing_limitation"][
                "const"
            ],
        )
        print(
            f"\nroot A dev closure_size = {cert['closure_size']}, "
            f"depths {cert['depth_histogram']}, "
            f"unprovenanced {len(cert['unprovenanced_nodes'])}, "
            f"inferred excluded {len(cert['inferred_edges_excluded'])}"
        )


class TheScanNeverReadsTheAnswerKey(unittest.TestCase):
    """§4's anti-tautology clause, made mechanical.

    R2 compares a mechanically derived closure against an independently
    hand-audited list. A citation scan that consumed that list would be
    grading its own homework, and the clause would certify nothing. The
    design registered a source scan as the enforcement — the same way
    ``tests/test_bounded_closure.py::TheGenericLayerIsShared`` forbids
    world-name literals in the generic closure layer — so the prohibition is
    checked by arithmetic rather than by the author's memory.

    The forbidden strings are the filename stem and the directory-qualified
    prefix, not just an open() call: a module that merely *names* the
    answer key has already made it available to the next person who edits
    it, and a scan that only caught reads would pass the commit before the
    one that matters.
    """

    SCANNED = ("provenance_graph.py", "retraction_radius.py")
    FORBIDDEN = ("ground_truth", "retraction_closure/ground")

    def test_neither_tool_names_the_hand_audited_lists(self) -> None:
        for name in self.SCANNED:
            path = REPO / "scripts" / name
            self.assertTrue(path.is_file(), name)
            source = path.read_text(encoding="utf-8").lower()
            for forbidden in self.FORBIDDEN:
                self.assertNotIn(forbidden, source, f"{name}: {forbidden}")


class GateRegenerationCheckRuns(unittest.TestCase):
    """Green as of the wave-1 builder: the check exists and runs.

    This test really re-runs three corpus writers into a tempdir, so it
    costs minutes, not milliseconds — the honest price of asserting
    regeneration rather than asserting that a regeneration script parses.
    """

    def test_the_regeneration_check_reports_the_live_drifts(self) -> None:
        # R2's roots per the design's §3 correction: a HEALED silent drift
        # (compression.json, repaired at 1090aa5 with no radius computed)
        # and a DECLARED divergence (decompositions.json, the pre-scale
        # ledger by decision). The check must tell those two shapes apart —
        # a declared snapshot is not a drift — and that distinction's
        # assertion lands with the check.
        import check_report_regeneration  # noqa: PLC0415

        self.assertTrue(hasattr(check_report_regeneration, "main"))

        # The registry is the mapping design §3 complained lived only in a
        # comment in verify_slice.py. Pinning it here means a ledger cannot
        # be added to reports/ and left unchecked without this test noticing.
        self.assertEqual(
            set(check_report_regeneration.REGISTRY),
            {
                "reports/signature_matches.json",
                "reports/specializations.json",
                "reports/compression.json",
                "reports/decompositions.json",
            },
        )
        self.assertEqual(
            set(check_report_regeneration.DECLARED_SNAPSHOTS),
            {GROUND_TRUTH_ROOTS["b"]},
        )
        self.assertIn(
            "TRIAGE-v0.11",
            check_report_regeneration.DECLARED_SNAPSHOTS[GROUND_TRUTH_ROOTS["b"]],
        )

        self.assertEqual(check_report_regeneration.main([]), 0)


#: The ledgers whose writers adopted the provenance convention, with the
#: writer each must name. `decompositions.json` is absent on purpose — see
#: the assertion at the end of the class.
#:
#: Wave 1 was the three `reports/` ledgers. **Wave 2 (2026-08-27) adds the
#: four v0.22 item-1 measurement artifacts**, and they are here because
#: this guard would have caught a defect they shipped with:
#: `handles_census.json` and `skeleton_index.json` were generated, their
#: writer was then edited, and neither was regenerated — so both attested
#: a writer digest no committed file had. Nothing in the suite could see
#: it, because the convention was adopted without the guard that scores
#: it. An artifact carrying a provenance block belongs on this list or the
#: block is decoration.
PROVENANCED_LEDGERS = {
    "reports/signature_matches.json": "scripts/match_signatures.py",
    "reports/specializations.json": "scripts/specialize.py",
    "reports/compression.json": "scripts/measure_compression.py",
    "experiments/handles_census.json": "scripts/handles_census.py",
    "experiments/skeleton_index.json": "scripts/handles_census.py",
    "experiments/onestep_census.json": "scripts/onestep_census.py",
    "experiments/erratum_probe.json": "scripts/erratum_probe.py",
}

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _sha256_lf(path: Path) -> str:
    """Canonical-LF digest, recomputed here rather than imported.

    A test that hashed with the writer's own helper would agree with the
    writer even if the helper were wrong; §6's R5 wants an independent
    arithmetic.
    """

    return hashlib.sha256(
        path.read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()


class WritersEmitTheirOwnProvenance(unittest.TestCase):
    """§5 step 1 / gate R1: the ledgers name their writer and their inputs.

    R1 scores edges into `report_ledger` nodes as `inferred: false` only
    when a deterministic writer emitted them at generation time. These
    blocks are those edges in ledger form, so their shape is checked here
    before the assembler that reads them exists.
    """

    def test_each_regenerated_ledger_carries_its_writers_block(self) -> None:
        for report_path, writer in sorted(PROVENANCED_LEDGERS.items()):
            with self.subTest(report=report_path):
                block = _load(REPO / report_path)["provenance"]
                self.assertEqual(block["writer"], writer)
                self.assertTrue(HEX64.match(block["writer_sha256_lf"]))
                self.assertTrue(block["emitted_at_generation"])
                self.assertTrue(block["inputs"])
                paths = [row["path"] for row in block["inputs"]]
                self.assertEqual(paths, sorted(paths))
                for row in block["inputs"]:
                    self.assertTrue(HEX64.match(row["sha256_lf"]), row)
                    # Repo-relative, forward slashes, no drive letters: R5
                    # forbids anything that differs between two checkouts
                    # of the same bytes.
                    self.assertNotIn("\\", row["path"])
                    self.assertFalse(Path(row["path"]).is_absolute(), row)
                    self.assertFalse(row["path"].startswith(".."), row)
                    self.assertTrue((REPO / row["path"]).is_file(), row)

    def test_the_writer_digest_matches_the_committed_writer(self) -> None:
        for report_path, writer in sorted(PROVENANCED_LEDGERS.items()):
            with self.subTest(report=report_path):
                block = _load(REPO / report_path)["provenance"]
                self.assertEqual(
                    block["writer_sha256_lf"], _sha256_lf(REPO / writer)
                )

    def test_two_input_digests_per_ledger_match_the_committed_data(
        self,
    ) -> None:
        # A spot-check, not a sweep: hashing all ~40 corpora three times
        # over would put a multi-second cost on every suite run to re-prove
        # the same arithmetic. The regeneration check is what catches a
        # stale block wholesale; this proves the digests are real hashes of
        # the named files rather than plausible-looking strings.
        for report_path in sorted(PROVENANCED_LEDGERS):
            with self.subTest(report=report_path):
                rows = _load(REPO / report_path)["provenance"]["inputs"]
                for row in (rows[0], rows[-1]):
                    self.assertEqual(
                        row["sha256_lf"], _sha256_lf(REPO / row["path"]), row
                    )

    def test_the_declared_snapshot_predates_the_convention(self) -> None:
        # NOT an oversight, and not a TODO. reports/decompositions.json is
        # the declared pre-scale ledger (TRIAGE-v0.11 gate table row 6);
        # regenerating it at 12k scale to gain a provenance block would
        # destroy the snapshot the decision preserved. Its missing block is
        # therefore data — design §4's standing example of an edge that a
        # writer should have emitted and did not, and so is `inferred:
        # true` and excluded from every scored clause. When this assertion
        # starts failing, someone regenerated the snapshot.
        self.assertNotIn("provenance", _load(REPO / GROUND_TRUTH_ROOTS["b"]))


class R2EvaluatorScoresTheAuditedList(unittest.TestCase):
    """The adjudication evaluator, checked for internal consistency only.

    Not for a verdict: R2 is adjudicated once, against the certificate of
    the adjudicated run, and a suite that asserted PASS or FAIL here would
    turn §6's "no patch-and-rerun" into "rerun until green". What is
    asserted is that the evaluator counts what it says it counts — the
    denominator is the frozen 11, every audited pair lands in exactly one
    of covered/missed, and the cap it publishes is 3x that denominator.
    """

    def _dev_verdict(self, tmp: str) -> dict:
        import provenance_graph  # noqa: PLC0415
        import radius_adjudicate  # noqa: PLC0415
        import retraction_radius  # noqa: PLC0415

        self.assertTrue(
            GRAPH_PATH.is_file(),
            "the committed adjudicated graph is missing; it is an artifact, "
            "never rebuilt by the suite",
        )
        cert_path = retraction_radius.certify(
            GRAPH_PATH,
            f"ledger:{GROUND_TRUTH_ROOTS['a']}",
            "ledger_stale",
            "root-a-dev",
            Path(tmp),
        )
        return radius_adjudicate.evaluate(
            cert_path, GROUND_TRUTH_PATHS["a"], GRAPH_PATH
        )

    def test_the_evaluator_is_internally_consistent_on_root_a(self) -> None:
        with tempfile.TemporaryDirectory(prefix="radius-adj-") as tmp:
            verdict = self._dev_verdict(tmp)

        self.assertEqual(verdict["total"], GROUND_TRUTH_COUNTS["a"])
        self.assertEqual(
            verdict["covered"] + len(verdict["misses"]), verdict["total"]
        )
        self.assertEqual(
            verdict["cap"],
            DESIGN_GATE["r2_closure_to_ground_truth_ratio"] * verdict["total"],
        )
        self.assertEqual(
            verdict["ratio_ok"], verdict["closure_size"] <= verdict["cap"]
        )
        self.assertEqual(verdict["superset_ok"], not verdict["misses"])
        self.assertEqual(
            verdict["r2_ok"], verdict["superset_ok"] and verdict["ratio_ok"]
        )
        for miss in verdict["misses"]:
            # A miss carries the reason it is a miss: either the anchor
            # resolved to no claim node at all, or it resolved and the
            # closure did not reach it. Those are different defects and the
            # adjudication needs to tell them apart.
            self.assertEqual(miss["covered_by"], [])
            self.assertEqual(miss["anchored"], bool(miss["claim_nodes"]))
        print(
            f"\nroot A dev R2: covered {verdict['covered']}/{verdict['total']}, "
            f"closure {verdict['closure_size']} (cap {verdict['cap']}), "
            f"superset_ok={verdict['superset_ok']} ratio_ok={verdict['ratio_ok']}"
        )

    def test_the_producers_stay_blind_and_the_judge_is_exempt(self) -> None:
        """The asymmetry §4 requires, asserted in both directions.

        The two tools that PRODUCE the scored artifact must not name the
        hand-audited lists — that is TheScanNeverReadsTheAnswerKey's job and
        this re-states its scope. The tool that JUDGES must read them, so it
        is exempt; the exemption is asserted here so that adding the
        evaluator to the scanned set fails loudly rather than looking like
        a tightening.
        """

        scanned = set(TheScanNeverReadsTheAnswerKey.SCANNED)
        self.assertEqual(scanned, {"provenance_graph.py", "retraction_radius.py"})
        self.assertNotIn("radius_adjudicate.py", scanned)
        for name in sorted(scanned):
            source = (REPO / "scripts" / name).read_text(encoding="utf-8").lower()
            for forbidden in TheScanNeverReadsTheAnswerKey.FORBIDDEN:
                self.assertNotIn(forbidden, source, f"{name}: {forbidden}")
        judge = (REPO / "scripts" / "radius_adjudicate.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("EXEMPT", judge)


class BlindControlShufflesReproducibly(unittest.TestCase):
    """A smoke run of §6's control: three seeds, not the registered hundred.

    The registered control is 100 seeds against both roots and is run once,
    as its own adjudication. What a suite can usefully assert is the
    property that makes that run auditable at all — same committed seed,
    same shuffle, every time — plus the stability of the report's shape, so
    that a later reader parsing a published control report is not parsing a
    format that moved.
    """

    SMOKE_SEEDS = 3

    def test_the_same_seed_reproduces_the_same_shuffle(self) -> None:
        import provenance_graph  # noqa: PLC0415
        import radius_blind_control as control  # noqa: PLC0415

        self.assertTrue(
            GRAPH_PATH.is_file(),
            "the committed adjudicated graph is missing; it is an artifact, "
            "never rebuilt by the suite",
        )
        seeds = control.load_seeds(REPO)[: self.SMOKE_SEEDS]
        self.assertEqual(len(seeds), self.SMOKE_SEEDS)

        first = control.run_control(GRAPH_PATH, seeds, REPO)
        second = control.run_control(GRAPH_PATH, seeds, REPO)
        self.assertEqual(
            [row["shuffle_digest"] for row in first["results"]],
            [row["shuffle_digest"] for row in second["results"]],
        )
        # Distinct seeds must actually produce distinct graphs, or the
        # "100 shuffles" would be one shuffle counted a hundred times.
        self.assertEqual(
            len({row["shuffle_digest"] for row in first["results"]}),
            self.SMOKE_SEEDS,
        )
        print(
            f"\nblind-control smoke ({self.SMOKE_SEEDS} seeds): "
            f"satisfying_shuffles {first['satisfying_shuffles']}"
            f"/{first['seeds_run']}"
        )

    def test_the_control_report_shape_is_stable(self) -> None:
        import radius_blind_control as control  # noqa: PLC0415

        seeds = control.load_seeds(REPO)[: self.SMOKE_SEEDS]
        report = control.run_control(GRAPH_PATH, seeds, REPO)
        self.assertEqual(report["schema"], "retraction-blind-control/1")
        self.assertEqual(
            set(report),
            {
                "schema",
                "graph_sha256",
                "seeds_run",
                "swaps_per_edge",
                "satisfying_seeds",
                "satisfying_shuffles",
                "results",
            },
        )
        self.assertEqual(
            report["satisfying_shuffles"], len(report["satisfying_seeds"])
        )
        for row in report["results"]:
            self.assertEqual(
                set(row),
                {"seed", "shuffle_digest", "roots", "satisfies_r2_on_both_roots"},
            )
            self.assertEqual(set(row["roots"]), {"a", "b"})
            self.assertEqual(
                row["satisfies_r2_on_both_roots"],
                all(entry["r2_ok"] for entry in row["roots"].values()),
            )
            for key, entry in row["roots"].items():
                self.assertEqual(entry["total"], GROUND_TRUTH_COUNTS[key])
                self.assertEqual(
                    entry["cap"],
                    DESIGN_GATE["r2_closure_to_ground_truth_ratio"]
                    * entry["total"],
                )

    def test_the_shuffle_preserves_degrees_and_kinds(self) -> None:
        """The two adjectives §6 attaches to "shuffle", made arithmetic.

        A shuffle that changed a node's degree would be comparing the real
        graph against a differently-shaped one, and a shuffle that crossed
        kinds would be comparing it against something that is not a
        provenance graph at all. Either would make a clean control
        meaningless in the direction that matters — it would let the real
        edges look informative for a reason that has nothing to do with
        consequence.
        """

        import radius_blind_control as control  # noqa: PLC0415
        import retraction_radius  # noqa: PLC0415

        nodes, edges = retraction_radius.load_graph(GRAPH_PATH)
        kinds = {node_id: node["kind"] for node_id, node in nodes.items()}
        shuffled = control.shuffle_edges(
            edges, kinds, control.load_seeds(REPO)[0]
        )
        self.assertEqual(len(shuffled), len(edges))

        def profile(rows: list[dict]) -> tuple[dict, dict, dict]:
            out: dict[str, int] = {}
            into: dict[str, int] = {}
            classes: dict[tuple[str, str], int] = {}
            for edge in rows:
                if edge["relation"] != "derived_from" or edge["inferred"]:
                    continue
                out[edge["from_node"]] = out.get(edge["from_node"], 0) + 1
                into[edge["to_node"]] = into.get(edge["to_node"], 0) + 1
                key = (kinds[edge["from_node"]], kinds[edge["to_node"]])
                classes[key] = classes.get(key, 0) + 1
            return out, into, classes

        self.assertEqual(profile(edges), profile(shuffled))
        # Degree-preserving is not the same as unchanged: if the shuffle
        # rewired nothing, this control would certify by doing nothing.
        self.assertNotEqual(
            control.shuffle_digest(edges), control.shuffle_digest(shuffled)
        )


if __name__ == "__main__":
    unittest.main()
