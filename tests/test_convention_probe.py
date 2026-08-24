#!/usr/bin/env python3
"""The TWO RIGHTS B0 probe, held to what §3b promised.

Three things this file checks, and each corresponds to a sentence in
ROADMAP-v0.19 §3b that would otherwise be unfalsifiable:

- **Determinism and byte-identity.** "Its result is committed either way"
  only means something if the committed bytes are what a re-run produces.
  The probe is regenerated into a temporary location and diffed against
  `experiments/convention_pairs_probe.json` byte for byte, and the report
  is built twice in one process to catch order-dependent construction that
  a single build would hide.
- **The census re-verifies against the ledgers.** Every row's two statement
  ids must resolve to committed statements whose `canonical_ascii` is
  exactly what the row quotes, and every row's discriminator must be the
  one the rule produces from those two strings. A census that cannot be
  re-derived from the corpus is a claim, not a record.
- **The classifier means what its labels say.** Each class has a property
  a reader would expect it to have; those are asserted directly, including
  the guard that a declared head spelling is not eligible to be called a
  renamed variable (the bug that hid `Odd` vs `odd` in the first run).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import probe_convention_pairs as probe  # noqa: E402

ARTIFACT = REPO / "experiments" / "convention_pairs_probe.json"


class ArtifactShape(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw = ARTIFACT.read_bytes()
        cls.report = json.loads(cls.raw.decode("utf-8"))

    def test_committed_artifact_is_lf_only(self) -> None:
        self.assertNotIn(b"\r\n", self.raw)
        self.assertTrue(self.raw.endswith(b"\n"))

    def test_branch_is_one_of_the_two_registered_branches(self) -> None:
        self.assertIn(self.report["branch"], ("census", "registered_negative"))

    def test_both_branches_carry_their_evidence(self) -> None:
        """Whichever branch landed, the artifact must carry what that branch
        owes: a census owes rows, a negative owes the sweep's parameters."""

        params = self.report["parameters"]
        for key in ("tokenizer_regex", "max_discriminator_tokens",
                    "discriminator_rule", "pool_passes", "notation_classes",
                    "clash_shapes_swept"):
            self.assertIn(key, params, key)
        if self.report["branch"] == "census":
            self.assertTrue(self.report["census"]["rows"])
        self.assertIn("registered_negative", self.report["famous_clash_sweep"])

    def test_counts_agree_with_the_rows(self) -> None:
        rows = self.report["census"]["rows"]
        self.assertEqual(len(rows), self.report["census"]["pairs"])
        by_class: dict[str, int] = {}
        by_verdict: dict[str, int] = {}
        for row in rows:
            by_class[row["classification"]] = by_class.get(row["classification"], 0) + 1
            by_verdict[row["verdict"]] = by_verdict.get(row["verdict"], 0) + 1
        self.assertEqual(by_class, self.report["census"]["counts_by_classification"])
        self.assertEqual(by_verdict, self.report["census"]["counts_by_verdict"])

    def test_every_row_carries_the_full_disclosure_section_3b_asks_for(self) -> None:
        for row in self.report["census"]["rows"]:
            self.assertEqual(len(row["statement_ids"]), 2)
            self.assertEqual(len(row["subterms"]), 2)
            self.assertNotEqual(row["subterms"][0], row["subterms"][1])
            self.assertIsInstance(row["discriminator_position"], int)
            self.assertTrue(row["note"])
            self.assertIn(row["verdict"],
                          ("convention_pair_candidate", "near_duplicate",
                           "different_statement", "unclassified"))

    def test_rows_are_not_sealed_convention_pair_objects(self) -> None:
        """§3b reserves sealing for the full direction. A row that claimed a
        seal would be this probe overreaching its charter."""

        for row in self.report["census"]["rows"]:
            self.assertNotIn("seal", row)
            self.assertNotIn("sealed_digest", row)
        self.assertTrue(any("not sealed ConventionPair" in line.replace("NOT", "not")
                            for line in self.report["not_claimed"]))


class Determinism(unittest.TestCase):
    def test_report_is_stable_across_two_builds(self) -> None:
        first = probe.build_report(REPO)
        second = probe.build_report(REPO)
        self.assertEqual(json.dumps(first, ensure_ascii=False, sort_keys=False),
                         json.dumps(second, ensure_ascii=False, sort_keys=False))

    def test_regenerates_byte_identically(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "regen.json"
            probe.write_report(probe.build_report(REPO), out)
            self.assertEqual(out.read_bytes(), ARTIFACT.read_bytes())


class CensusReVerifies(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        cls.statements, _ = probe.load_statements(REPO)
        cls.ledger = json.loads(
            (REPO / "reports" / "signature_matches.json").read_text(encoding="utf-8"))

    def test_provenance_digests_match_the_committed_inputs(self) -> None:
        from report_provenance import sha256_lf_file

        for entry in self.report["provenance"]["inputs"]:
            path = REPO / entry["path"]
            self.assertTrue(path.exists(), entry["path"])
            self.assertEqual(sha256_lf_file(path), entry["sha256_lf"], entry["path"])

    def test_every_row_quotes_the_committed_canonical_forms(self) -> None:
        for row in self.report["census"]["rows"]:
            for sid, quoted in zip(row["statement_ids"], row["canonical_ascii"]):
                self.assertIn(sid, self.statements, sid)
                self.assertEqual(self.statements[sid]["canonical_ascii"], quoted, sid)

    def test_every_row_is_co_present_and_pool_derived(self) -> None:
        """`pool_origin` must be a family the twin ledger really groups these
        two ids under, or the anonymized-template pass."""

        for row in self.report["census"]["rows"]:
            a, b = row["statement_ids"]
            origin = row["pool_origin"]
            if origin == "anonymized_template":
                self.assertEqual(self.statements[a]["anonymized_template"],
                                 self.statements[b]["anonymized_template"])
                continue
            self.assertIn(origin, probe.TWIN_FAMILIES)
            grouped = any(
                {a, b} <= {m["statement_id"] for m in group.get("members", [])}
                for group in self.ledger.get(origin, [])
            )
            self.assertTrue(grouped, f"{a}/{b} not grouped under {origin}")

    def test_every_discriminator_re_derives_from_the_rule(self) -> None:
        for row in self.report["census"]["rows"]:
            left = probe.tokens(row["canonical_ascii"][0])
            right = probe.tokens(row["canonical_ascii"][1])
            fork = probe.discriminator(left, right)
            self.assertIsNotNone(fork)
            self.assertTrue(probe.qualifies(fork))
            self.assertEqual(fork["position"], row["discriminator_position"])
            self.assertEqual([" ".join(fork["left_tokens"]),
                              " ".join(fork["right_tokens"])], row["subterms"])
            klass, _note = probe.classify(left, right, fork)
            self.assertEqual(klass, row["classification"])

    def test_notation_candidates_really_collapse_under_the_declared_table(self) -> None:
        rows = [r for r in self.report["census"]["rows"]
                if r["classification"] == "notation_convention"]
        self.assertTrue(rows, "the census claims notation forks; check one")
        for row in rows:
            left = probe._normalize_notation(probe.tokens(row["canonical_ascii"][0]))
            right = probe._normalize_notation(probe.tokens(row["canonical_ascii"][1]))
            self.assertEqual(probe._strip_parens(left), probe._strip_parens(right),
                             row["statement_ids"])

    def test_alpha_variants_really_are_renamings(self) -> None:
        for row in self.report["census"]["rows"]:
            if row["classification"] != "alpha_variant":
                continue
            left = probe.tokens(row["canonical_ascii"][0])
            right = probe.tokens(row["canonical_ascii"][1])
            fork = probe.discriminator(left, right)
            mapping = probe._alpha_rename(left, right, fork)
            self.assertIsNotNone(mapping, row["statement_ids"])
            self.assertEqual([mapping.get(t, t) for t in left], right)

    def test_declared_heads_are_not_renameable_variables(self) -> None:
        """The guard that stopped `Odd` vs `odd` being filed as a renaming."""

        for head in ("Odd", "odd", "Real.sqrt", "sin", "ℝ"):
            self.assertFalse(probe._is_identifier(head), head)
        for variable in ("a", "x_1", "θ", "n"):
            self.assertTrue(probe._is_identifier(variable), variable)

    def test_famous_clash_sweep_hits_are_real_or_absent(self) -> None:
        sweep = self.report["famous_clash_sweep"]
        self.assertEqual(sweep["registered_negative"], not sweep["hits"])
        for hit in sweep["hits"]:
            left = probe.tokens(hit["canonical_ascii"][0])
            right = probe.tokens(hit["canonical_ascii"][1])
            self.assertEqual(sorted(probe.clash_shapes(left, right)),
                             sorted(hit["shapes"]))

    def test_clash_detectors_fire_on_constructed_clashes(self) -> None:
        """The negative is only worth committing if the detectors can fire.

        Injected, not accidental: three synthetic pairs in exactly the shapes
        §3b names, so `sign_convention=0` reports an absence in the corpus
        rather than a detector that never worked.
        """

        cases = [
            ("F = k * x", "F = -k * x", "sign_convention"),
            ("∀ n : ℕ, 0 < n", "∀ n : ℕ, 1 ≤ n", "nat_zero_boundary"),
            ("C = 2 * π * r", "C = τ * r", "two_pi_placement"),
        ]
        for left_src, right_src, shape in cases:
            shapes = probe.clash_shapes(probe.tokens(left_src), probe.tokens(right_src))
            self.assertIn(shape, shapes, f"{left_src} vs {right_src}")


if __name__ == "__main__":
    unittest.main()
