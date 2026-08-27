"""Tests for H-P0, the handles coverage census (`DESIGN-handles.md` §6).

The census is a measurement, so the only thing worth testing about it is
whether its numbers are the ones the tree actually holds. Five things,
each checked by recomputing rather than by re-reading:

1. **S-LEX's forward map is the resolver's index, transposed.** The
   census builds `statement -> glossary words`; `resolver.build_index`
   builds `glossary word -> statements`. Inverting one must give the
   other exactly, on the real corpus. If it does not, the census is
   measuring some other source and calling it S-LEX.
2. **S-SKEL's table agrees with a report nobody involved in this cycle
   wrote.** `reports/compression.json` carries a `family_reuse` count per
   statement and no skeleton string -- which is precisely why the census
   owes an id->skeleton table. Grouping the census's skeleton strings must
   reproduce that committed count for all 12,777 statements.
3. **No producer on this path reads `title` or `keywords`,** checked by
   AST over the census module and over `match_signatures`'s two producer
   functions -- and the auditor is itself shown to go red on a planted
   read, because an audit that cannot fail is the defect this cycle's
   reviews keep finding.
4. **The two S3 numbers are subset, never summed** -- `BACKLOG.md`
   1122-1133's anti-merge rule, asserted against the artifact's bytes.
5. **The headline's numbers are the artifact's numbers.** A published
   sentence that outran its own measurement is the other recurring defect;
   here the sentence is parsed and every integer in it must appear in a
   measured field.

And one fence, because this slice is measurement only: the census must
not have written a handle table, a partition, or an enumeration receipt.
"""

from __future__ import annotations

import ast
import collections
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import handles_census as census  # noqa: E402

CENSUS = ROOT / "experiments" / "handles_census.json"
SKELETONS = ROOT / "experiments" / "skeleton_index.json"
DATA = ROOT / "data"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# the AST auditor, and the proof that it can fail
# --------------------------------------------------------------------------

FORBIDDEN_FIELDS = {"title", "keywords"}


def field_reads(source: str) -> set[str]:
    """Every corpus field name this source reads positionally.

    A field is *read* when its name appears as the first argument of a
    `.get(...)` call or inside a subscript. Prose mentioning `title` in a
    docstring is not a read, and this auditor deliberately does not count
    it -- the question is what the code touches, not what it talks about.
    """

    found: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get"
                and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)):
            found.add(node.args[0].value)
        if (isinstance(node, ast.Subscript)
                and isinstance(node.slice, ast.Constant)
                and isinstance(node.slice.value, str)):
            found.add(node.slice.value)
    return found


class TheAuditorCanFail(unittest.TestCase):
    """Point 3's precondition. An audit that cannot go red is not an audit."""

    def test_a_planted_get_is_caught(self) -> None:
        planted = "def f(node):\n    return node.get('title', '')\n"
        self.assertIn("title", field_reads(planted))

    def test_a_planted_subscript_is_caught(self) -> None:
        planted = "def f(node):\n    return node['keywords']\n"
        self.assertIn("keywords", field_reads(planted))

    def test_prose_alone_is_not_a_read(self) -> None:
        prose = '"""this function does not read title or keywords."""\nx = 1\n'
        self.assertEqual(field_reads(prose) & FORBIDDEN_FIELDS, set())


class TheProducersAreTitleFree(unittest.TestCase):
    """B3's producer audit is the table's to run. This is the census's own.

    The census would be worthless if the sources it measured were
    title-derived, so the same shape of check runs here one slice early,
    over the census writer and over the committed producer
    `DESIGN-handles.md` §3 substituted for the draft's title-reading one
    (review N2).
    """

    def test_the_census_writer_reads_neither_title_nor_keywords(self) -> None:
        source = (ROOT / "scripts" / "handles_census.py").read_text(
            encoding="utf-8")
        self.assertEqual(field_reads(source) & FORBIDDEN_FIELDS, set())

    def test_the_s_inv_producer_reads_neither(self) -> None:
        """`template_call_heads` and the loader that reaches it.

        Sliced out of `match_signatures.py` rather than audited whole,
        because that module has other callers with other rights; what
        S-INV depends on is these two functions.
        """

        module = ast.parse(
            (ROOT / "scripts" / "match_signatures.py").read_text(
                encoding="utf-8"))
        wanted = {"template_call_heads", "load_nodes"}
        seen: set[str] = set()
        for node in module.body:
            if isinstance(node, ast.FunctionDef) and node.name in wanted:
                seen.add(node.name)
                self.assertEqual(
                    field_reads(ast.unparse(node)) & FORBIDDEN_FIELDS, set(),
                    node.name)
        self.assertEqual(seen, wanted)


# --------------------------------------------------------------------------
# recomputation
# --------------------------------------------------------------------------


class SLexIsTheResolversIndexTransposed(unittest.TestCase):
    """Point 1. The expensive test, and the one that would catch a wrong source."""

    @classmethod
    def setUpClass(cls) -> None:
        from resolver import build_index  # noqa: PLC0415

        cls.index = build_index([DATA])
        cls.rows = census.corpus_rows(DATA)

    def test_inverting_the_forward_map_reproduces_by_lexicon(self) -> None:
        inverted: dict[str, set[str]] = collections.defaultdict(set)
        for _corpus, sid, node in self.rows:
            for word in census.slex_handles(node):
                inverted[word].add(sid)
        self.assertEqual(set(inverted), set(self.index.by_lexicon))
        for word, ids in self.index.by_lexicon.items():
            self.assertEqual(inverted[word], set(ids), word)

    def test_resolves_to_count_is_the_resolvers_document_frequency(self) -> None:
        forward = {sid: census.slex_handles(node)
                   for _c, sid, node in self.rows}
        counts = census.resolves_to(forward)
        self.assertEqual(dict(counts), self.index.lexicon_df)

    def test_the_committed_coverage_is_what_the_index_says(self) -> None:
        """The artifact's S-LEX count, recomputed from `by_lexicon` alone."""

        artifact = load(CENSUS)
        k = artifact["specificity_K"]
        specific_words = {w for w, ids in self.index.by_lexicon.items()
                          if len(ids) <= k}
        reachable: set[str] = set()
        for word in specific_words:
            reachable.update(self.index.by_lexicon[word])
        self.assertEqual(
            len(reachable),
            artifact["sources"]["S-LEX"]["coverage"][
                "statements_with_specific_handle"])


class SkeletonIndexAgreesWithTheCompressionReport(unittest.TestCase):
    """Point 2. An independent committed source for the same grouping."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.skeletons = load(SKELETONS)
        cls.compression = json.loads(
            (ROOT / "reports" / "compression.json").read_text(encoding="utf-8"))

    def test_every_statement_has_a_skeleton(self) -> None:
        ids = {row["statement_id"] for row in self.skeletons["rows"]}
        self.assertEqual(len(ids), len(self.skeletons["rows"]))
        self.assertEqual(len(ids), self.skeletons["totals"]["statements"])
        self.assertEqual(
            ids, {row["statement_id"] for row in self.compression["nodes"]})

    def test_grouping_the_strings_reproduces_the_committed_reuse_counts(self) -> None:
        sizes = collections.Counter(
            row["family_skeleton"] for row in self.skeletons["rows"])
        committed = {row["statement_id"]: row["family_reuse"]
                     for row in self.compression["nodes"]}
        for row in self.skeletons["rows"]:
            self.assertEqual(sizes[row["family_skeleton"]],
                             committed[row["statement_id"]],
                             row["statement_id"])
            self.assertEqual(row["family_reuse"], committed[row["statement_id"]])

    def test_the_skeleton_vocabulary_size_matches(self) -> None:
        self.assertEqual(self.skeletons["totals"]["distinct_family_skeletons"],
                         self.compression["n_family_skeletons"])

    def test_k_never_binds_on_skeletons_and_the_artifact_says_so(self) -> None:
        """B2's own argument, checked rather than quoted."""

        k = self.skeletons["specificity_K"]
        self.assertEqual(self.skeletons["totals"]["skeletons_over_K"], 0)
        self.assertLessEqual(self.skeletons["totals"]["max_family_reuse"], k)


class SInvIsTheCallHeadInventory(unittest.TestCase):
    """S-INV recomputed from the producer, not from the artifact."""

    def test_committed_coverage_matches_a_fresh_load_nodes(self) -> None:
        from match_signatures import load_nodes  # noqa: PLC0415

        artifact = load(CENSUS)
        k = artifact["specificity_K"]
        nodes, problems = load_nodes(DATA)
        self.assertEqual(problems, [])
        df: collections.Counter = collections.Counter()
        for node in nodes:
            for head in set(node.call_heads):
                df[head] += 1
        specific = sum(1 for node in nodes
                       if any(df[h] <= k for h in set(node.call_heads)))
        block = artifact["sources"]["S-INV"]
        self.assertEqual(specific,
                         block["coverage"]["statements_with_specific_handle"])
        self.assertEqual(dict(df), block["full_head_index"])


# --------------------------------------------------------------------------
# the artifact's own discipline
# --------------------------------------------------------------------------


class TheArtifactSaysWhatItMeasured(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = load(CENSUS)

    def test_the_two_s3_numbers_are_subset_never_summed(self) -> None:
        counts = self.artifact["s3_price"]["counts"]
        self.assertLessEqual(counts["covered"], counts["oracle_eligible"])
        self.assertIn("SUBSET", counts["anti_merge_note"])
        forbidden = counts["covered"] + counts["oracle_eligible"]
        blob = json.dumps(self.artifact)
        self.assertNotIn(str(forbidden), blob,
                         "the sum of the two S3 numbers appears in the artifact")

    def test_the_oracle_measurement_proved_it_really_ran(self) -> None:
        estimate = self.artifact["s3_price"]["runtime_estimate"]
        self.assertTrue(estimate["measured"])
        self.assertEqual(estimate["liveness"]["digests_reproduced"],
                         estimate["liveness"]["of"])
        self.assertGreaterEqual(estimate["calls"], 20)
        self.assertGreater(estimate["payload_chars"]["min"], 0)

    def test_every_integer_in_the_headline_is_a_measured_field(self) -> None:
        """The published sentence cannot outrun the measurement.

        Percentages are excluded (they are derived and rounded); the bare
        integers must each appear as a value somewhere in the artifact's
        measured blocks.
        """

        headline = self.artifact["headline"]
        # drop the decimal percentages before scanning for integers
        stripped = re.sub(r"\d+\.\d+%", "", headline)
        integers = {int(m) for m in re.findall(r"\d+", stripped)}
        values: set[int] = set()

        def collect(node: object) -> None:
            if isinstance(node, bool):
                return
            if isinstance(node, int):
                values.add(node)
            elif isinstance(node, dict):
                for child in node.values():
                    collect(child)
            elif isinstance(node, list):
                for child in node:
                    collect(child)

        for key in ("corpus", "sources", "union", "per_corpus_split",
                    "boilerplate_finding"):
            collect(self.artifact[key])
        self.assertTrue(integers)
        self.assertEqual(integers - values, set())

    def test_the_stop_clause_reading_names_both_source_numbers(self) -> None:
        sentence = self.artifact["headline_is_the_stop_clause"]
        for source in ("S-LEX", "S-INV"):
            count = self.artifact["sources"][source]["coverage"][
                "statements_with_specific_handle"]
            self.assertIn(str(count), sentence, source)

    def test_the_curated_bulk_split_partitions_the_corpus(self) -> None:
        split = self.artifact["per_corpus_split"]
        self.assertEqual(
            split["curated"]["statements"] + split["lean_workbook_bulk"]["statements"],
            self.artifact["corpus"]["statements"])
        for source in ("S-LEX", "S-INV"):
            key = f"specific_{source}"
            self.assertEqual(
                split["curated"][key] + split["lean_workbook_bulk"][key],
                self.artifact["sources"][source]["coverage"][
                    "statements_with_specific_handle"])

    def test_the_boilerplate_finding_is_quantified(self) -> None:
        finding = self.artifact["boilerplate_finding"]
        self.assertEqual(finding["bulk_statements"],
                         self.artifact["corpus"]["bulk_lean_workbook"])
        self.assertEqual(len(finding["the_tokens"]),
                         finding["distinct_glossary_tokens_over_the_bulk"])
        self.assertEqual(len(finding["the_raw_strings"]),
                         finding["distinct_raw_glossary_strings_over_the_bulk"])

    def test_the_typable_union_excludes_the_skeleton_source(self) -> None:
        union = self.artifact["union"]
        self.assertEqual(union["typable_sources"], ["S-LEX", "S-INV"])
        self.assertEqual(union["specific_handle_union_all_sources"],
                         self.artifact["corpus"]["statements"])
        self.assertLess(union["specific_handle_union_typable"],
                        union["specific_handle_union_all_sources"])
        self.assertEqual(
            union["slex_only"] + union["sinv_only"] + union["both"],
            union["specific_handle_union_typable"])

    def test_no_reachability_rate_is_claimed(self) -> None:
        for claim in self.artifact["non_claims"]:
            self.assertIsInstance(claim, str)
        self.assertTrue(any("reachability rate" in c
                            for c in self.artifact["non_claims"]))


class TheArtifactsAttestTheWriterThatMadeThem(unittest.TestCase):
    """The guard this slice shipped without, and paid for.

    Both artifacts were generated, the writer was then edited, and
    neither was regenerated -- so both carried a `writer_sha256_lf` that
    no committed file hashed to. Every surrounding test stayed green,
    because a provenance block nothing scores is a block nothing scores.
    `test_retraction_closure.PROVENANCED_LEDGERS` now covers these two as
    the house guard; this is the local one, so the failure is legible
    from the module that owns the artifacts.
    """

    @staticmethod
    def sha256_lf(path: Path) -> str:
        import hashlib  # noqa: PLC0415

        return hashlib.sha256(
            path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()

    def test_both_artifacts_name_the_committed_writer(self) -> None:
        writer = ROOT / "scripts" / "handles_census.py"
        for path in (CENSUS, SKELETONS):
            block = load(path)["provenance"]
            self.assertEqual(block["writer"], "scripts/handles_census.py")
            self.assertEqual(block["writer_sha256_lf"], self.sha256_lf(writer),
                             f"{path.name} attests a writer that is not the "
                             f"committed one -- regenerate it")

    def test_every_declared_input_digest_is_the_committed_file(self) -> None:
        for path in (CENSUS, SKELETONS):
            for row in load(path)["provenance"]["inputs"]:
                target = ROOT / row["path"]
                self.assertTrue(target.is_file(), row)
                self.assertEqual(row["sha256_lf"], self.sha256_lf(target), row)


class TheDeterministicHalfIsDeterministic(unittest.TestCase):
    """The artifact claims everything but the clock recomputes identically.

    That claim was false when it was first written. `resolves_to`
    accumulates over per-statement SETS, so the counter's insertion order
    -- and with it `Counter.most_common`'s tie order -- followed
    PYTHONHASHSEED. Across three seeds, entries of `most_resolving` moved
    and at one seed a tied handle dropped off the twenty-fifth slot
    entirely. Ties now break on the handle's own bytes.

    This test is the reason the claim is allowed to stay in the artifact:
    it runs the writer twice under different hash seeds and compares
    every byte except the wall-clock block the artifact names.
    """

    @staticmethod
    def build_under(seed: str, out: Path) -> dict:
        import os  # noqa: PLC0415
        import subprocess  # noqa: PLC0415

        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONIOENCODING="utf-8")
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "handles_census.py"),
             "--oracle-calls", "0", "--out", str(out),
             "--skeleton-index", str(out.with_name(out.stem + "-skel.json"))],
            check=True, capture_output=True, env=env, cwd=str(ROOT))
        return json.loads(out.read_text(encoding="utf-8"))

    def test_two_hash_seeds_produce_the_same_census(self) -> None:
        import tempfile  # noqa: PLC0415

        with tempfile.TemporaryDirectory() as tmp:
            first = self.build_under("1", Path(tmp) / "a.json")
            second = self.build_under("7", Path(tmp) / "b.json")
        for payload in (first, second):
            # the clock block is the artifact's own declared exception,
            # and with --oracle-calls 0 it is not measured at all
            payload["s3_price"].pop("runtime_estimate", None)
        self.assertEqual(json.dumps(first, sort_keys=True),
                         json.dumps(second, sort_keys=True))

    def test_the_most_resolving_lists_are_in_the_frozen_order(self) -> None:
        """Descending count, ties on the handle's bytes -- §4's rule."""

        artifact = load(CENSUS)
        for name, block in artifact["sources"].items():
            rows = block["distribution"]["most_resolving"]
            keys = [(-row["resolves_to_count"], row["handle"]) for row in rows]
            self.assertEqual(keys, sorted(keys), name)


class TheB2TriggerWasAdjudicatedNotJustMeasured(unittest.TestCase):
    """M1. The census measured B2's re-freeze condition and owed a verdict.

    lean_workbook's specific-S-LEX coverage is 0 of 12,514, which is
    arguably "a corpus stranded with no specific handle" -- B2's trigger
    in its own words. A census that measured the trigger and left it
    lying there would be the cycle's recurring defect in its purest
    form: a clause that could have gone red, never adjudicated.

    Every number in the adjudication is checked against the measurement
    it cites, and the sweep is recomputed from the producers.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = load(CENSUS)
        cls.block = cls.artifact["k_sensitivity"]

    def test_the_sweep_recomputes_from_the_producers(self) -> None:
        from match_signatures import load_nodes  # noqa: PLC0415

        rows = census.corpus_rows(DATA)
        parsed = {n.statement_id: n for n in load_nodes(DATA)[0]}
        slex = {sid: census.slex_handles(node) for _c, sid, node in rows}
        sinv = {sid: set(parsed[sid].call_heads) if sid in parsed else set()
                for _c, sid, _n in rows}
        slex_counts = census.resolves_to(slex)
        sinv_counts = census.resolves_to(sinv)
        corpus_of = {sid: corpus for corpus, sid, _ in rows}
        for row in self.block["sweep"]:
            k = row["K"]
            a = {s for s in slex if any(slex_counts[h] <= k for h in slex[s])}
            b = {s for s in sinv if any(sinv_counts[h] <= k for h in sinv[s])}
            self.assertEqual(len(a), row["S-LEX"], k)
            self.assertEqual(len(b), row["S-INV"], k)
            self.assertEqual(len(a | b), row["typable_union"], k)
            self.assertEqual(
                sum(1 for s in a if corpus_of[s] == "lean_workbook"),
                row["lean_workbook_specific_S-LEX"], k)

    def test_the_committed_K_is_interior_to_its_plateau(self) -> None:
        k = self.artifact["specificity_K"]
        for name, entry in self.block["plateaus"].items():
            low, high = entry["invariant_for_K_in"]
            self.assertLess(low, k, name)
            self.assertLess(k, high, name)
            self.assertTrue(entry["K_is_interior"], name)

    def test_the_plateau_endpoints_are_real_endpoints(self) -> None:
        """Inside the range the number holds; one step outside it moves."""

        sweep = {row["K"]: row for row in self.block["sweep"]}
        union = self.block["plateaus"]["typable union"]
        low, high = union["invariant_for_K_in"]
        self.assertIn(high, sweep)
        self.assertIn(high + 1, sweep)
        self.assertEqual(sweep[high]["typable_union"], union["coverage_at_K"])
        self.assertNotEqual(sweep[high + 1]["typable_union"],
                            union["coverage_at_K"])

    def test_reason_a_cites_the_measured_bulk_coverage(self) -> None:
        measured = self.artifact["per_corpus_split"]["lean_workbook_bulk"][
            "specific_S-INV"]
        self.assertGreater(measured, 0)
        self.assertIn(str(measured), self.block["adjudication"]["reasons"][0])

    def test_reason_b_cites_the_measured_plateaus(self) -> None:
        reason = self.block["adjudication"]["reasons"][1]
        for name in ("S-LEX", "typable union"):
            low, high = self.block["plateaus"][name]["invariant_for_K_in"]
            self.assertIn(f"[{low}, {high}]", reason, name)

    def test_reason_c_cites_the_measured_ceiling_and_the_token(self) -> None:
        buy = self.block["what_a_refreeze_would_buy_the_bulk"]
        reason = self.block["adjudication"]["reasons"][2]
        rescue = buy[
            "smallest_K_giving_any_lean_workbook_statement_a_specific_S-LEX_handle"]
        self.assertIn(str(rescue), reason)
        self.assertIn(str(buy["ceiling_on_bulk_S-LEX_coverage_at_any_K"]), reason)
        self.assertIn(buy["the_token_that_K_admits"], reason)

    def test_the_ceiling_really_is_a_ceiling(self) -> None:
        """Checked at the largest K in the sweep, not asserted in prose."""

        buy = self.block["what_a_refreeze_would_buy_the_bulk"]
        largest = max(self.block["sweep"], key=lambda row: row["K"])
        self.assertEqual(largest["lean_workbook_specific_S-LEX"],
                         buy["ceiling_on_bulk_S-LEX_coverage_at_any_K"])
        self.assertLess(buy["ceiling_as_share_of_the_bulk"], 5.0)

    def test_the_verdict_is_recorded_and_dated(self) -> None:
        adjudication = self.block["adjudication"]
        self.assertEqual(adjudication["verdict"], "NOT FIRED")
        self.assertEqual(adjudication["dated"], "2026-08-27")
        self.assertIn("K stays 128", adjudication["consequence"])
        self.assertEqual(self.artifact["specificity_K"], 128)

    def test_the_token_the_refreeze_admits_is_a_real_bulk_token(self) -> None:
        """The adjudication names a token; it must be one the bulk carries."""

        token = self.block["what_a_refreeze_would_buy_the_bulk"][
            "the_token_that_K_admits"]
        self.assertIn(token, self.artifact["boilerplate_finding"]["the_tokens"])


class ThePLDenominatorIsRecomputable(unittest.TestCase):
    """L3. Three numbers nobody could check without knowing the walk."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.block = load(CENSUS)["P-L"]

    def test_the_denominator_names_the_sections_and_the_file(self) -> None:
        text = self.block["denominator"]
        self.assertIn("data/realization/lexicon.json", text)
        for section in census.REALIZATION_SECTIONS:
            self.assertIn(section, text)
        self.assertIn("STOPWORDS", text)

    def test_the_three_numbers_recompute_from_that_definition(self) -> None:
        english = census.realization_english(
            ROOT / "data" / "realization" / "lexicon.json")
        self.assertEqual(len(english),
                         self.block["realization_english_content_words"])
        rows = census.corpus_rows(DATA)
        slex = {sid: census.slex_handles(node) for _c, sid, node in rows}
        counts = census.resolves_to(slex)
        handles = set(counts)
        specific = {h for h, c in counts.items() if c <= census.DEFAULT_K}
        self.assertEqual(len(handles & english),
                         self.block["slex_handles_in_realization_english"])
        self.assertEqual(
            len(specific & english),
            self.block["slex_specific_handles_in_realization_english"])


class TheSliceBuiltNothing(unittest.TestCase):
    """Measurement only. H-P0 lands before the table, and only H-P0."""

    def test_no_table_partition_or_receipt_artifact_exists(self) -> None:
        for name in ("handles_table.json", "handles_partition.json",
                     "handles_enum_receipts.json"):
            self.assertFalse((ROOT / "experiments" / name).exists(), name)

    def test_the_census_writes_exactly_two_artifacts(self) -> None:
        source = (ROOT / "scripts" / "handles_census.py").read_text(
            encoding="utf-8")
        self.assertEqual(source.count("write_text"), 1)
        self.assertIn("handles_census.json", source)
        self.assertIn("skeleton_index.json", source)
        self.assertNotIn("handles_table.json", source)


if __name__ == "__main__":
    unittest.main()
