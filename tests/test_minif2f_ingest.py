"""miniF2F ingestion + grammar-coverage: parser soundness, classifier honesty,
and byte-for-byte regeneration of the committed measurement.

The coverage number is a load-bearing v0.9 claim, so these tests guard both
directions of error: a classifier that over-counts (marking an unexpressible
statement COVERED) and one that under-counts (rejecting an expressible one).
No network, no toolchain; the parser is pure and the committed extract is the
fixture for the coverage regeneration.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ingest_minif2f as ing  # noqa: E402
import grammar_coverage as gc  # noqa: E402

MANIFEST = json.loads(
    (REPO_ROOT / "data_sources" / "manifest.json").read_text(encoding="utf-8")
)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _minif2f_source() -> dict:
    return next(s for s in MANIFEST["sources"] if s["id"] == "git-openai-minif2f")


class ManifestPin(unittest.TestCase):
    """The source must be digest-pinned so the transform is reproducible."""

    def test_commit_and_files_are_pinned(self) -> None:
        src = _minif2f_source()
        self.assertEqual(len(src["git_commit"]), 40, "commit must be a full SHA-1")
        self.assertRegex(src["git_commit"], r"^[0-9a-f]{40}$")
        self.assertTrue(src["files"], "must pin the statement files")
        total = 0
        for f in src["files"]:
            self.assertTrue(_HEX64.match(f["sha256"]), f"{f['filename']} sha not 64-hex")
            self.assertIsInstance(f["size_bytes"], int)
            self.assertIn(f["split"], {"valid", "test"})
            total += f["theorem_count"]
        self.assertEqual(total, 488, "miniF2F is 244 valid + 244 test")


class ParserSoundness(unittest.TestCase):
    def test_top_level_scanners(self) -> None:
        s = "(a : ℝ) (h : f (x) = 1) : a = 2 := proof"
        self.assertEqual(gc.take_until_top_level(s, ":="), s[: s.index(":=")])
        sig = gc.take_until_top_level(s, ":=")
        ci = gc.first_top_level_colon(sig)
        # the first depth-0 colon is the goal separator, not the ':' inside binders
        self.assertEqual(sig[:ci].strip(), "(a : ℝ) (h : f (x) = 1)")
        self.assertEqual(sig[ci + 1 :].strip(), "a = 2")

    def test_parse_extracts_vars_hyps_goal(self) -> None:
        block = (
            "theorem demo\n  (b h v : ℝ)\n  (h0 : 0 < b ∧ 0 < h)\n"
            "  (h1 : v = b * h) :\n  v = 65 :=\nbegin\n norm_num,\nend"
        )
        p = ing.parse_theorem_block(block)
        self.assertEqual(p["name"], "demo")
        self.assertEqual(p["value_vars"], ["b", "h", "v"])
        self.assertEqual(p["goal"], "v = 65")
        self.assertIn("0 < b ∧ 0 < h", p["hyps"])
        self.assertIn("v = b * h", p["hyps"])
        self.assertFalse(p["fn_unknown"])

    def test_nnreal_and_pnat_are_numeric_slots(self) -> None:
        for typ in ("nnreal", "ℕ+"):
            names, hyp, is_fn, dom = gc.classify_binder(f"x y : {typ}")
            self.assertEqual(names, ["x", "y"], typ)
            self.assertIsNone(hyp)
            self.assertFalse(is_fn)
            self.assertEqual(dom, [])

    def test_function_and_domain_binders(self) -> None:
        _, _, is_fn, _ = gc.classify_binder("f : ℝ → ℝ")
        self.assertTrue(is_fn)
        _, _, is_fn2, _ = gc.classify_binder("g : ℂ → ℂ")
        self.assertTrue(is_fn2)
        _, _, _, dom = gc.classify_binder("a : ℂ")
        self.assertEqual(dom, [("a", "complex_number")])
        _, _, _, domz = gc.classify_binder("n : zmod 1399")
        self.assertEqual(domz, [("n", "modular_type_zmod")])

    def test_prop_binder_is_a_hypothesis_not_a_function(self) -> None:
        # `a → b` here is a Prop implication, not a function type.
        names, hyp, is_fn, _ = gc.classify_binder("h : a = 0 → b = 0")
        self.assertEqual(names, [])
        self.assertFalse(is_fn)
        self.assertEqual(hyp, "a = 0 → b = 0")


class ClassifierHonesty(unittest.TestCase):
    def _mk(self, goal, vars=(), hyps=(), fn=False, domain=None):
        return {
            "name": "t",
            "split": "valid",
            "goal": goal,
            "value_vars": list(vars),
            "hyps": list(hyps),
            "fn_unknown": fn,
            "domain_vars": domain or {},
        }

    def test_covered_conditional_identity(self) -> None:
        r = gc.classify(self._mk("v = 65", vars=("v", "b", "h"),
                                  hyps=("v = b * h", "0 < b ∧ 0 < h")))
        self.assertTrue(r["goal_ok"])
        self.assertTrue(r["full_ok"])
        self.assertIsNone(r["full_reason"])

    def test_covered_with_supported_transcendentals(self) -> None:
        r = gc.classify(self._mk("real.log w / real.log z = 60",
                                  vars=("w", "z"), hyps=("real.log w = 3",)))
        self.assertTrue(r["full_ok"])

    def test_big_operator_blocked(self) -> None:
        r = gc.classify(self._mk("∑ i in finset.range n, i = 1", vars=("n",)))
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "big_operator")

    def test_function_unknown_blocks_full_but_maybe_not_goal(self) -> None:
        # goal mentions f (an unknown function) -> unsupported at goal level
        r = gc.classify(self._mk("f 5 = 11", fn=True))
        self.assertFalse(r["goal_ok"])
        self.assertTrue(r["goal_reason"].startswith("unsupported_symbol"))

    def test_complex_domain_var_in_goal(self) -> None:
        r = gc.classify(self._mk("(a - 10) * (a + 11) = a^2 + a - 110",
                                  domain={"a": "complex_number"}))
        self.assertEqual(r["goal_reason"], "complex_number")

    def test_hypothesis_carries_the_blocker(self) -> None:
        r = gc.classify(self._mk("x = 6", vars=("x", "y"), hyps=("abs x = 6",)))
        self.assertTrue(r["goal_ok"], "goal alone is fine")
        self.assertFalse(r["full_ok"], "hypothesis has a blocker")
        self.assertEqual(r["full_reason"], "hyp:absolute_value")

    def test_bare_predicate_goal_now_covered(self) -> None:
        # v0.10 item 1 (cont.): PRIME is a corpus head (data/number_theory), so
        # the bare application `nat.prime p` is proposition-shaped and covered.
        # (This test asserted rejection while primality had no head.)
        r = gc.classify(self._mk("nat.prime p", vars=("p",)))
        self.assertTrue(r["goal_ok"])
        self.assertTrue(r["full_ok"])

    def test_bare_prop_variable_still_no_relation(self) -> None:
        # a goal that is a lone proposition variable has no shape to reduce
        r = gc.classify(self._mk("p", vars=("p",)))
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "no_relation_in_goal")

    def test_modulo_and_divides_are_gaps_not_supported(self) -> None:
        # Regression: an adversarial review found % and ∣ have no head in the
        # corpus (the only MOD node is morphology's linguistic modifier). They
        # must be rejected, not silently counted.
        r = gc.classify(self._mk("(2^2010) % 10 = 4"))
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "modulo_no_head")
        r2 = gc.classify(self._mk("12 ∣ 4^(n+1) + 20", vars=("n",)))
        self.assertFalse(r2["goal_ok"])
        self.assertEqual(r2["goal_reason"], "divides_no_head")

    def test_mathlib_norm_bars_are_blocked(self) -> None:
        # Regression: ∥·∥ (U+2225) escaped an ASCII-only `|` blocker.
        r = gc.classify(self._mk("a * b + ∥a - b∥ ≤ 1", vars=("a", "b")))
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "absolute_value")

    def test_tuple_constructor_equality_blocked(self) -> None:
        # Regression: (p,q,r)=(2,4,8) has a pairing constructor with no head.
        r = gc.classify(self._mk("(p, q, r) = (2, 4, 8)", vars=("p", "q", "r")))
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "tuple_or_structure")

    def test_quantifier_prefix_now_covers_and_embedded_beats_comma(self) -> None:
        # v0.10 quantifier slice: a prefix chain is extracted (its comma is
        # binder syntax, not a tuple constructor), so this simple witness goal
        # now reduces under the EXISTS head...
        r = gc.classify(self._mk("∃ m, m > n", vars=("n",)))
        self.assertTrue(r["goal_ok"], r["goal_reason"])
        # ...while a NON-prefix quantifier keeps its precise label — and the
        # original concern stands: the comma/tuple blocker must not steal it.
        r = gc.classify(self._mk("(∃ m, m > n) ∧ n > 0", vars=("n",)))
        self.assertFalse(r["goal_ok"])
        self.assertEqual(r["goal_reason"], "quantifier_embedded")

    def test_every_supported_head_char_maps_to_a_corpus_node(self) -> None:
        # The supported set may only contain heads that actually appear in the
        # corpus. % and ∣ must NOT be reachable as covered.
        for glyph in ("%", "∣"):
            r = gc.classify(self._mk(f"a {glyph} b = 1", vars=("a", "b")))
            self.assertFalse(r["goal_ok"], f"{glyph} must be a gap")


class CorpusHeadProvenance(unittest.TestCase):
    """The supported-head claim is verified against data/, not asserted. This is
    the direct response to the review that caught % and ∣ being claimed as
    corpus heads when the corpus has none."""

    def _all_templates(self) -> str:
        blob = []
        import glob
        for f in glob.glob(str(REPO_ROOT / "data" / "*" / "nodes.json")):
            d = json.loads(Path(f).read_text(encoding="utf-8"))
            for n in d.get("statement_nodes", []):
                blob.append(
                    n.get("structural_signature", {}).get("anonymized_template", "")
                )
        return "\n".join(blob)

    def test_transcendental_heads_actually_appear(self) -> None:
        templates = self._all_templates()
        # SIN/COS/TAN were added in v0.10 (data/trigonometry) — a supported head is
        # legitimate only once a corpus node carries it.
        for head in ("LOG(", "EXP(", "SQRT(", "SIN(", "COS(", "TAN("):
            self.assertIn(head, templates, f"claimed head {head} absent from data/")

    def test_predicate_heads_actually_appear(self) -> None:
        # v0.10 item 1 (cont.): the relational/predicate heads were added with
        # data/number_theory — same rule, verified node-by-node against data/.
        templates = self._all_templates()
        for head in ("EVEN(", "ODD(", "PRIME(", "IRRATIONAL("):
            self.assertIn(head, templates, f"claimed head {head} absent from data/")
        # the prop constants the classifier accepts as bare goals are carried by
        # data/logic (identity laws, non-contradiction, ex falso)
        for const in ("TRUTH", "FALSITY"):
            self.assertIn(const, templates, f"claimed constant {const} absent from data/")

    def test_binder_heads_actually_appear(self) -> None:
        # v0.10: the quantifier slice — FORALL/EXISTS are carried by
        # data/logic's quantification laws and data/number_theory's witness
        # definitions. Same rule, verified node-by-node against data/.
        templates = self._all_templates()
        for head in ("FORALL(", "EXISTS("):
            self.assertIn(head, templates, f"claimed head {head} absent from data/")
        # the ∃!-desugar is grounded by the authored expansion node, and the
        # witness definitions tie EXISTS to the predicate heads:
        for tpl in (
            "EXISTS(VAR1, MEET(PRED(VAR1), FORALL(VAR2, IMPLIES(PRED(VAR2), VAR2 = VAR1))))",
            "EVEN(INT1) = EXISTS(INT2, INT1 = 2 * INT2)",
            "ODD(INT1) = EXISTS(INT2, INT1 = 2 * INT2 + 1)",
        ):
            self.assertIn(tpl, templates, f"grounding template missing: {tpl}")

    def test_no_covered_statement_relies_on_an_unverified_head(self) -> None:
        # % and ∣ are gaps: no covered statement may contain them.
        ext = json.loads(ing.EXTRACT_PATH.read_text(encoding="utf-8"))
        byname = {s["name"]: s for s in ext["statements"]}
        cov = json.loads(ing.COVERAGE_PATH.read_text(encoding="utf-8"))
        for name in cov["covered_full_statement_names"]:
            s = byname[name]
            for txt in [s["goal"]] + s["hyps"]:
                self.assertNotIn("%", txt, name)
                self.assertNotIn("∣", txt, name)


class CommittedArtifacts(unittest.TestCase):
    def test_extract_is_complete_and_pinned(self) -> None:
        doc = json.loads(
            (REPO_ROOT / "data_sources" / "derived" / "minif2f"
             / "statements.json").read_text(encoding="utf-8")
        )
        self.assertEqual(doc["statement_count"], 488)
        self.assertEqual(len(doc["statements"]), 488)
        self.assertEqual(doc["source"]["git_commit"], _minif2f_source()["git_commit"])
        splits = {s["split"] for s in doc["statements"]}
        self.assertEqual(splits, {"valid", "test"})

    def test_coverage_regenerates_byte_for_byte(self) -> None:
        """coverage = pure fn of the committed extract; guard the exact bytes."""
        extract = json.loads(ing.EXTRACT_PATH.read_text(encoding="utf-8"))
        rebuilt = ing.build_coverage(extract)
        rebuilt_bytes = (
            json.dumps(rebuilt, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
        ).encode("utf-8")
        committed = ing.COVERAGE_PATH.read_bytes()
        self.assertEqual(
            hashlib.sha256(rebuilt_bytes).hexdigest(),
            hashlib.sha256(committed).hexdigest(),
            "committed coverage.json is stale; re-run `ingest_minif2f.py coverage`",
        )

    def test_covered_set_has_no_out_of_grammar_glyphs(self) -> None:
        """The false-positive guard the review demanded: every covered goal and
        hypothesis contains only whitelisted characters — no stray operator glyph
        (∥, %, ∣, ∑, ∈, …) or constructor survives in a COVERED statement."""
        ext = json.loads(ing.EXTRACT_PATH.read_text(encoding="utf-8"))
        byname = {s["name"]: s for s in ext["statements"]}
        cov = json.loads(ing.COVERAGE_PATH.read_text(encoding="utf-8"))
        # v0.10 quantifier slice: ∀ ∃ and the binder comma are grammar glyphs;
        # `∃!` is pre-stripped as a token so a bare factorial `!` still trips.
        allowed = set(
            "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "+-*/^=<>≤≥≠∧∨¬→↔() .:↑ℝℕℤℚπ⁻¹²³⁰⁴⁵⁶⁷⁸⁹∀∃,"
        ) | {chr(c) for c in range(0x2080, 0x208A)}  # subscripts ₀-₉
        offenders = []
        for name in cov["covered_full_statement_names"]:
            s = byname[name]
            for txt in [s["goal"]] + s["hyps"]:
                norm = re.sub(r"([∀∃]\s*)\{([^{}|]*)\}", r"\1(\2)",
                              txt.replace("∃!", "∃"))
                bad = set(norm) - allowed
                if bad:
                    offenders.append((name, "".join(sorted(bad))))
        self.assertEqual(offenders, [], f"covered statements with foreign glyphs: {offenders[:5]}")

    def test_totals_partition_the_statements(self) -> None:
        cov = json.loads(ing.COVERAGE_PATH.read_text(encoding="utf-8"))
        total = cov["totals"]["statements"]
        # covered + every untranslatable reason accounts for all statements
        untl = sum(cov["full_statement_untranslatable_reasons"].values())
        self.assertEqual(untl + cov["totals"]["full_statement"]["covered"], total)
        # goal-only coverage is an upper bound on full-statement coverage
        self.assertGreaterEqual(
            cov["totals"]["goal_only"]["covered"],
            cov["totals"]["full_statement"]["covered"],
        )
        # every statement listed as covered indeed has no full_reason
        covered_names = set(cov["covered_full_statement_names"])
        for r in cov["per_statement"]:
            if r["name"] in covered_names:
                self.assertIsNone(r["full_reason"], r["name"])


if __name__ == "__main__":
    unittest.main()
