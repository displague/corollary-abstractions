"""Tests for the MDL-gated block-vocabulary induction (DESIGN §3c).

Four things are worth testing here and they are all cheap: the induction is
deterministic, the MDL gate really refuses a mint that does not pay, growth
is append-only, and the committed report is what the script produces today.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from measure_block_mdl import (  # noqa: E402
    RULE_NS,
    Grammar,
    Surface,
    ascii_tokens,
    code_width,
    entropy_bits,
    load_surfaces,
    to_template,
    total_bits,
)

REPORT = ROOT / "experiments" / "block_mdl.json"
SCRIPT = ROOT / "scripts" / "measure_block_mdl.py"


def surfaces(texts, corpus="t", kind="meaning"):
    return [
        Surface(corpus, f"{corpus}.{i}", kind, t, t.split())
        for i, t in enumerate(texts)
    ]


class BitModelTests(unittest.TestCase):
    def test_code_width_is_ceil_log2(self):
        self.assertEqual([code_width(v) for v in (1, 2, 3, 4, 5, 512, 513)],
                         [1, 1, 2, 2, 3, 9, 10])

    def test_total_bits_is_the_documented_sum(self):
        # lex + N*w + ceil(R*mult*2*w); T+R=8 -> w=3
        self.assertEqual(total_bits(100, 5, 3, 40, 1.0), 100 + 120 + 18)
        self.assertEqual(total_bits(100, 5, 3, 40, 2.0), 100 + 120 + 36)

    def test_entropy_bits_of_a_uniform_stream(self):
        # 8 symbols each occurring 4 times: 32 symbols * 3 bits
        self.assertEqual(entropy_bits(32, 8 * (4 * 2.0)), 32 * 3)


class InductionTests(unittest.TestCase):
    def test_repair_chain_from_the_design(self):
        """The maintainer's own example: "this is" -> "this is a test"."""
        s = surfaces(["this is a test"] * 60)
        g = Grammar()
        g.append_documents(s)
        g.induce(1.0)
        blocks = [" ".join(g.expand(RULE_NS | i)) for i in range(len(g.rules))]
        self.assertIn("this is", blocks)
        self.assertIn("this is a test", blocks)
        # composition: the long block is built from minted ids, not words
        top = blocks.index("this is a test")
        self.assertEqual(g.depth[RULE_NS | top], 2)

    def test_round_trip_is_byte_identical(self):
        s = surfaces(["alpha beta gamma delta"] * 12 + ["alpha beta zeta"] * 9)
        g = Grammar()
        g.append_documents(s)
        g.induce(1.0)
        for d, src in enumerate(s):
            out = []
            for sym in g.document_pattern(d):
                out.extend(g.expand(sym))
            self.assertEqual(out, src.words)

    def test_blocks_never_span_a_document_boundary(self):
        # "b a" only ever occurs across the join between documents
        s = [
            Surface("t", f"t.{i}", "meaning", txt, txt.split())
            for i, txt in enumerate(["x b", "a y"] * 20)
        ]
        g = Grammar()
        g.append_documents(s)
        g.induce(1.0)
        blocks = {" ".join(g.expand(RULE_NS | i)) for i in range(len(g.rules))}
        self.assertNotIn("b a", blocks)

    def test_determinism_two_runs_agree_exactly(self):
        s = surfaces(
            ["the quick brown fox jumps"] * 30
            + ["the quick red fox sleeps"] * 25
            + ["a quick brown dog jumps"] * 17
        )
        runs = []
        for _ in range(2):
            g = Grammar()
            g.append_documents(s)
            g.induce(1.0)
            runs.append((
                list(g.terminals),
                list(g.rules),
                json.dumps(g.stats(1.0), sort_keys=True),
            ))
        self.assertEqual(runs[0], runs[1])


class MdlGateTests(unittest.TestCase):
    """The gate must refuse, not merely prefer."""

    def test_gate_refuses_a_pair_that_does_not_pay(self):
        # Two words, each pair occurring exactly twice. Minting saves
        # 2 symbols * w bits and costs 2*w bits for the dictionary entry:
        # exactly break-even, and the gate demands a STRICT improvement.
        s = surfaces(["ab cd"] * 2)
        g = Grammar()
        g.append_documents(s)
        before = g.stats(1.0)["total_bits"]
        minted = g.induce(1.0)
        self.assertEqual(minted, 0)
        self.assertEqual(g.stats(1.0)["total_bits"], before)
        # ...and one more occurrence tips it: 3*w saved against 2*w spent.
        s3 = surfaces(["ab cd"] * 3)
        g3 = Grammar()
        g3.append_documents(s3)
        self.assertEqual(g3.induce(1.0), 1)
        self.assertLess(g3.stats(1.0)["total_bits"],
                        total_bits(g3.lexicon_bits(), len(g3.terminals), 0,
                                   g3.length + 3, 1.0))

    def test_doubling_dictionary_cost_refuses_marginal_mints(self):
        s = surfaces(["ab cd"] * 3)
        a = Grammar()
        a.append_documents(s)
        b = Grammar()
        b.append_documents(s)
        self.assertEqual(a.induce(1.0), 1)   # 3*w saved > 2*w spent
        self.assertEqual(b.induce(2.0), 0)   # 3*w saved < 4*w spent

    def test_every_mint_strictly_lowered_the_total(self):
        s = surfaces(
            ["one two three four five"] * 40 + ["one two three six"] * 31
        )
        g = Grammar()
        g.append_documents(s)
        totals = []
        trace: list = []
        # replay the induction one mint at a time, checking monotone descent
        probe = Grammar()
        probe.append_documents(s)
        probe.induce(1.0, trace=trace)
        step = Grammar()
        step.append_documents(s)
        totals.append(step.stats(1.0)["total_bits"])
        for _new_id, pair, _c in trace:
            step.mint(pair)
            totals.append(step.stats(1.0)["total_bits"])
        self.assertEqual(len(totals), len(trace) + 1)
        for earlier, later in zip(totals, totals[1:]):
            self.assertLess(later, earlier)

    def test_induction_is_a_fixed_point(self):
        s = surfaces(["alpha beta gamma"] * 50 + ["beta gamma delta"] * 40)
        g = Grammar()
        g.append_documents(s)
        n1 = g.induce(1.0)
        g.rebuild_heap()
        self.assertGreater(n1, 0)
        self.assertEqual(g.induce(1.0), 0)  # nothing left that pays


class AppendOnlyTests(unittest.TestCase):
    def test_increment_only_appends_ids_and_reuses_old_ones(self):
        base = surfaces(["red green blue"] * 30 + ["red green yellow"] * 20)
        incr = surfaces(["red green blue"] * 12 + ["red green violet"] * 12,
                        corpus="incr")
        g = Grammar()
        g.append_documents(base)
        g.induce(1.0)
        terms0, rules0 = list(g.terminals), list(g.rules)

        g.append_documents(incr)
        reused = g.replay_rules(len(rules0))
        g.rebuild_heap()
        g.induce(1.0)

        # existing ids are an untouched prefix -- the §3b invariant
        self.assertEqual(g.terminals[: len(terms0)], terms0)
        self.assertEqual(g.rules[: len(rules0)], rules0)
        self.assertGreater(reused, 0, "the increment must re-use old blocks")
        self.assertIn("violet", g.terminals[len(terms0):])
        # and the increment still decodes exactly
        start = len(g.doc_start) - len(incr)
        for k, src in enumerate(incr):
            out: list[str] = []
            for sym in g.document_pattern(start + k):
                out.extend(g.expand(sym))
            self.assertEqual(out, src.words)

    def test_existing_block_meanings_survive_the_increment(self):
        base = surfaces(["one two three"] * 40)
        incr = surfaces(["two three one"] * 40, corpus="incr")
        g = Grammar()
        g.append_documents(base)
        g.induce(1.0)
        meanings0 = {
            i: " ".join(g.expand(RULE_NS | i)) for i in range(len(g.rules))
        }
        g.append_documents(incr)
        g.replay_rules(len(meanings0))
        g.rebuild_heap()
        g.induce(1.0)
        for i, was in meanings0.items():
            self.assertEqual(" ".join(g.expand(RULE_NS | i)), was)


class SlottingTests(unittest.TestCase):
    def test_slotting_matches_the_census(self):
        # A formula-ish RUN collapses to one {F}; a plain word breaks the run,
        # which is why "y" survives between two {F}s. Bug-compatible with
        # scripts/block_census.py on purpose: the induction must run on the
        # alphabet the census measured, not a tidied-up one.
        self.assertEqual(
            to_template("Problem lean_workbook_12 says x^2 + y = 3 here."),
            "Problem lean_workbook_{N} says {F} y {F} here.",
        )
        self.assertEqual(to_template("value `foo` is 7"), "value {F} is {F}")

    def test_ascii_tokens_slot_numerals(self):
        self.assertEqual(ascii_tokens("f(x) = 2*x + 10"),
                         ["f", "(", "x", ")", "=", "{N}", "*", "x", "+", "{N}"])


class ReportTests(unittest.TestCase):
    def test_committed_report_regenerates_byte_identically(self):
        self.assertTrue(REPORT.exists(), f"missing {REPORT}")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "block_mdl.json"
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "--write-report", str(out)],
                cwd=str(ROOT), capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr[-2000:])
            self.assertEqual(
                out.read_bytes(), REPORT.read_bytes(),
                "experiments/block_mdl.json is stale; regenerate it with "
                "scripts/measure_block_mdl.py --write-report",
            )

    def test_report_carries_the_claims_the_design_asked_for(self):
        d = json.loads(REPORT.read_text(encoding="utf-8"))
        prose = d["streams"]["prose"]
        for arm in prose["mdl_arms"].values():
            self.assertTrue(arm["round_trip_ok"])
            self.assertIn("composition_depth_histogram", arm)
            self.assertIn("at_power_of_two_cliff", arm)
        self.assertIn("template_readout", prose)
        probe = d["append_only_probe"]
        self.assertTrue(probe["existing_ids_unchanged"])
        self.assertTrue(probe["increment_round_trips"])

    def test_no_timestamps_or_absolute_paths_in_the_report(self):
        text = REPORT.read_text(encoding="utf-8")
        for banned in ("C:\\", "/Users/", "20:", "T00:", "Z\""):
            self.assertNotIn(banned, text)


class CorpusSmokeTests(unittest.TestCase):
    def test_surfaces_load_from_the_committed_tree(self):
        prose, formal = load_surfaces(ROOT / "data")
        self.assertGreater(len(prose), 20000)
        self.assertGreater(len(formal), 10000)
        self.assertTrue(all(s.words for s in prose))


if __name__ == "__main__":
    unittest.main()
