"""ROADMAP-v0.10 item 3: programming as a first-class discipline.

Predictions P1-P10 are registered in docs/DESIGN-programming-discipline.md
§8; this file is where the machine-checkable ones stay checked.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from match_signatures import build_report, load_nodes  # noqa: E402
from validate_nodes import verified_by_errors  # noqa: E402
import seed_programming as seed  # noqa: E402
import external_verifier as ev  # noqa: E402

PROGRAMMING = REPO_ROOT / "data" / "programming" / "nodes.json"
VERDICTS = REPO_ROOT / "prover" / "verifier-verdicts"


def _nodes() -> list[dict]:
    return json.loads(PROGRAMMING.read_text(encoding="utf-8"))["statement_nodes"]


def _by_id() -> dict[str, dict]:
    return {n["statement_id"]: n for n in _nodes()}


class Vocabulary(unittest.TestCase):
    """P1: python-tests may ground verified_by; PROVEN stays lean4."""

    def test_programming_nodes_cite_python_tests(self) -> None:
        for node in _nodes():
            links = node["verified_by"]
            self.assertEqual(len(links), 1)
            self.assertEqual(links[0]["system"], "python-tests")
            self.assertEqual(node["epistemic_status"], "formal")

    def test_python_tests_against_lean_triples_is_refused(self) -> None:
        node = {
            "statement_id": "programming.example.cross_system",
            "verified_by": [{
                "system": "python-tests",
                "artifact": "prover/ingested_triples.json",
                "reference": "greatest_common_divisor",
            }],
        }
        errors = verified_by_errors([node], REPO_ROOT)
        self.assertTrue(any("JSON artifact" in e for e in errors), errors)

    def test_unmanifested_py_file_cannot_ground_a_link(self) -> None:
        """Review finding: a contained .py is not a verdict."""
        node = {
            "statement_id": "programming.example.unmanifested",
            "verified_by": [{
                "system": "python-tests",
                "artifact": "prover/pychecks/gcd_euclid_drop_abs.py",
                "reference": "greatest_common_divisor",
            }],
        }
        errors = verified_by_errors([node], REPO_ROOT)
        self.assertTrue(
            any("not a key in" in e and "proof-artifact-manifest" in e
                for e in errors),
            errors,
        )

    def test_lean4_against_py_candidate_is_refused(self) -> None:
        node = {
            "statement_id": "programming.example.lean_on_py",
            "verified_by": [{
                "system": "lean4",
                "artifact": "prover/pychecks/gcd_euclid_recursive.py",
                "reference": "greatest_common_divisor",
            }],
        }
        errors = verified_by_errors([node], REPO_ROOT)
        self.assertTrue(errors)

    def test_honesty_boundary_is_written_at_node_level(self) -> None:
        needle = "does not certify the candidate correct"
        for node in _nodes():
            self.assertIn(
                needle,
                node["semantic_interpretation"]["statistical_significance"],
            )


class EndToEnd(unittest.TestCase):
    """P3: each node has a rechecking PASS; P6: drop-abs is a recorded FAIL."""

    def test_nine_pass_verdicts_recheck(self) -> None:
        for name in (
            "programming_euclid_recursive.python-tests.json",
            "programming_euclid_iterative.python-tests.json",
            "programming_stein_binary.python-tests.json",
            "programming_factorial_recursive.python-tests.json",
            "programming_factorial_iterative.python-tests.json",
            "programming_dfactorial_recursive.python-tests.json",
            "programming_dfactorial_iterative.python-tests.json",
            "programming_binexp_recursive.python-tests.json",
            "programming_binexp_iterative.python-tests.json",
        ):
            ok, detail = ev.recheck(REPO_ROOT, f"prover/verifier-verdicts/{name}")
            self.assertTrue(ok, detail)

    def test_drop_abs_is_a_committed_fail_cited_by_nothing(self) -> None:
        path = VERDICTS / "programming_euclid_drop_abs.python-tests.json"
        verdict = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(verdict["verdict"], "fail")
        self.assertEqual(verdict["backend"], "python-tests")
        manifest = json.loads(
            (REPO_ROOT / "prover" / "proof-artifact-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        cited = [
            v
            for entry in manifest["artifacts"].values()
            for v in entry.get("verdicts") or []
        ]
        self.assertNotIn(
            "prover/verifier-verdicts/programming_euclid_drop_abs.python-tests.json",
            cited,
        )
        self.assertNotIn(
            "prover/verifier-verdicts/programming_factorial_n_minus_2.python-tests.json",
            cited,
        )
        for node in _nodes():
            self.assertNotIn(
                node["statement_id"],
                {"programming.euclid.drop_abs",
                 "programming.factorial.n_minus_2"},
            )
        ok, detail = ev.recheck(
            REPO_ROOT,
            "prover/verifier-verdicts/programming_euclid_drop_abs.python-tests.json",
        )
        self.assertTrue(ok, detail)

    def test_n_minus_2_is_a_committed_fail_cited_by_nothing(self) -> None:
        path = VERDICTS / "programming_factorial_n_minus_2.python-tests.json"
        verdict = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(verdict["verdict"], "fail")
        self.assertEqual(verdict["backend"], "python-tests")
        ok, detail = ev.recheck(
            REPO_ROOT,
            "prover/verifier-verdicts/programming_factorial_n_minus_2.python-tests.json",
        )
        self.assertTrue(ok, detail)

    def test_merged_validator_accepts_the_graph(self) -> None:
        all_nodes = []
        for path in sorted((REPO_ROOT / "data").glob("*/nodes.json")):
            all_nodes.extend(
                json.loads(path.read_text(encoding="utf-8"))["statement_nodes"]
            )
        self.assertEqual(verified_by_errors(all_nodes, REPO_ROOT), [])


class TwinsAndBaseline(unittest.TestCase):
    """P4 / P5: Euclid pair twins; Stein is the name-similar non-twin."""

    @classmethod
    def setUpClass(cls) -> None:
        nodes, problems = load_nodes(REPO_ROOT / "data")
        cls.report = build_report(nodes, problems)
        cls.problems = problems

    def test_zero_parse_problems_and_slot_gaps(self) -> None:
        self.assertEqual(self.report["parse_problems"], [])
        self.assertEqual(self.report["slot_schema_gaps"], [])

    def test_euclid_pair_is_a_typed_twin_stein_is_not(self) -> None:
        expected = {
            "programming.euclid.recursive",
            "programming.euclid.iterative",
        }
        groups = [
            {m["statement_id"] for m in g["members"]}
            for g in self.report["typed_twin_groups"]
        ]
        self.assertIn(expected, groups)
        for group in groups:
            self.assertNotIn("programming.stein.binary", group)

    def test_second_wave_pairs_are_typed_twins_and_do_not_cross(self) -> None:
        """P-W4: three new groups of size 2; no FACT/DFACT or BEXP/STEIN cross."""
        expected = [
            {"programming.factorial.recursive", "programming.factorial.iterative"},
            {"programming.dfactorial.recursive", "programming.dfactorial.iterative"},
            {"programming.binexp.recursive", "programming.binexp.iterative"},
        ]
        groups = [
            {m["statement_id"] for m in g["members"]}
            for g in self.report["typed_twin_groups"]
        ]
        for pair in expected:
            self.assertIn(pair, groups)
        for group in groups:
            heads = {sid.split(".")[1] for sid in group if sid.startswith("programming.")}
            if "factorial" in heads:
                self.assertNotIn("dfactorial", heads)
            if "binexp" in heads:
                self.assertNotIn("stein", heads)
            self.assertNotIn("programming.stein.binary", group)

    def test_token_gcd_baseline_loses_on_precision(self) -> None:
        # P5 registered "token gcd in statement_id". The ids are
        # programming.euclid.* / programming.stein.* — the gcd token
        # lives in keywords (and the function names), not the id prefix.
        # The baseline is therefore keywords, which is what the
        # capability-blind name check actually has to work with.
        by_id = _by_id()
        ids = [
            "programming.euclid.recursive",
            "programming.euclid.iterative",
            "programming.stein.binary",
        ]
        def has_gcd(sid: str) -> bool:
            return "gcd" in by_id[sid].get("keywords", [])
        baseline = [
            (a, b)
            for i, a in enumerate(ids)
            for b in ids[i + 1 :]
            if has_gcd(a) and has_gcd(b)
        ]
        self.assertEqual(len(baseline), 3)
        matcher = [
            {m["statement_id"] for m in g["members"]}
            for g in self.report["typed_twin_groups"]
            if {m["statement_id"] for m in g["members"]} <= set(ids)
        ]
        self.assertEqual(len(matcher), 1)
        self.assertEqual(matcher[0], {ids[0], ids[1]})

    def test_token_factorial_baseline_loses_on_precision(self) -> None:
        """P-W5: keyword factorial forms 6 pairs; matcher forms 2."""
        by_id = _by_id()
        ids = [
            "programming.factorial.recursive",
            "programming.factorial.iterative",
            "programming.dfactorial.recursive",
            "programming.dfactorial.iterative",
        ]
        def has_factorial(sid: str) -> bool:
            return "factorial" in by_id[sid].get("keywords", [])
        baseline = [
            (a, b)
            for i, a in enumerate(ids)
            for b in ids[i + 1 :]
            if has_factorial(a) and has_factorial(b)
        ]
        self.assertEqual(len(baseline), 6)
        matcher = [
            {m["statement_id"] for m in g["members"]}
            for g in self.report["typed_twin_groups"]
            if {m["statement_id"] for m in g["members"]} <= set(ids)
        ]
        self.assertEqual(len(matcher), 2)
        self.assertEqual(
            set(map(frozenset, matcher)),
            {
                frozenset(ids[:2]),
                frozenset(ids[2:]),
            },
        )

    def test_combined_programming_keyword_baseline_is_point_four(self) -> None:
        """P-W5 combined: 10 keyword pairs vs 4 matcher pairs (precision 0.4)."""
        by_id = _by_id()
        ids = [n["statement_id"] for n in _nodes()]
        tokens = ("gcd", "factorial", "exponentiation")
        def toks(sid: str) -> set[str]:
            kws = by_id[sid].get("keywords", [])
            return {t for t in tokens if t in kws}
        baseline = [
            (a, b)
            for i, a in enumerate(ids)
            for b in ids[i + 1 :]
            if toks(a) & toks(b)
        ]
        self.assertEqual(len(baseline), 10)
        matcher = [
            {m["statement_id"] for m in g["members"]}
            for g in self.report["typed_twin_groups"]
            if any(m["statement_id"].startswith("programming.") for m in g["members"])
        ]
        self.assertEqual(len(matcher), 4)

    def test_volume_loops_are_real(self) -> None:
        """P-W11: FACT/DFACT tests contain a range(20) library comparison."""
        needles = {
            "test_factorial_recursive.py": "range(20)",
            "test_factorial_iterative.py": "range(20)",
            "test_dfactorial_recursive.py": "range(20)",
            "test_dfactorial_iterative.py": "range(20)",
        }
        for name, needle in needles.items():
            text = (REPO_ROOT / "prover" / "pychecks" / name).read_text(
                encoding="utf-8"
            )
            self.assertIn(needle, text)
            self.assertTrue(
                "math.factorial" in text or "math.prod" in text, name
            )


class RetrievalDoesNotTreatTestsAsProofs(unittest.TestCase):
    """python-tests citations must not crash the store or mint proven."""

    def test_store_loads_and_programming_nodes_are_not_proven(self) -> None:
        from retrieval import UnifiedKnowledgeStore

        store = UnifiedKnowledgeStore.load(
            REPO_ROOT / "data", REPO_ROOT / "reports"
        )
        proof_ids = {
            item.item_id
            for item in store.items
            if item.item_id.startswith("proof:programming.")
        }
        self.assertEqual(proof_ids, set())
        programming = [
            item
            for item in store.items
            if any(
                sid.startswith("programming.")
                for sid in item.source_ids
            )
        ]
        self.assertTrue(programming)
        self.assertFalse(any(item.epistemic_status == "proven" for item in programming))


class VerdictBackedRule(unittest.TestCase):
    """P7: the seed refuses a verified_by without a PASS."""

    def test_unknown_statement_cannot_be_emitted(self) -> None:
        with self.assertRaises(SystemExit) as caught:
            seed.require_python_tests_pass("programming.example.no_verdict")
        self.assertIn("no committed python-tests PASS", str(caught.exception))

    def test_drop_abs_fail_does_not_satisfy_the_rule(self) -> None:
        with self.assertRaises(SystemExit):
            seed.require_python_tests_pass("programming.euclid.drop_abs")

    def test_n_minus_2_fail_does_not_satisfy_the_rule(self) -> None:
        with self.assertRaises(SystemExit):
            seed.require_python_tests_pass("programming.factorial.n_minus_2")


if __name__ == "__main__":
    unittest.main()
