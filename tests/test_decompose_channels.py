"""Regression tests for the v0.7 groundedness channel split (ROADMAP item 10).

The registered predictions GC1-GC5 live in `scripts/decompose.py`'s module
docstring together with their adjudication; this file is where the two that
are machine-checkable stay checked:

- GC4 (aggregates unchanged) is pinned as the pre-split numbers: graph mean
  0.770, 440 exact + 75 pattern-membership constituents, 193 statements with
  at least one grounded constituent. A channel change that moves any of them
  is a scoring change and needs its own registered prediction.
- GC5 (partition identity) is checked per statement: the five channel counts
  sum to the grounded numerator, so channel shares sum to `groundedness`.

The provability corpus is the regression case the item names. Its 1.000 must
keep resolving into same-corpus + pattern-absorption with a near-zero external
channel; if a future change lets that corpus claim external grounding, this
file fails and the claim has to be argued rather than absorbed.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from decompose import (  # noqa: E402
    CHANNELS,
    analyze,
    best_channel,
    channel_shares,
    owner_channel,
)


PROVABILITY = "provability.goedel_loeb.v1"


class ChannelClassification(unittest.TestCase):
    """The channel rule itself, on synthetic provenance."""

    corpus_of = {"a": "c1", "b": "c1", "c": "c2", "d": "c3"}
    disciplines_of = {
        "a": frozenset({"alpha"}),
        "b": frozenset({"alpha"}),
        "c": frozenset({"alpha", "beta"}),   # other corpus, shared discipline
        "d": frozenset({"gamma"}),           # other corpus, nothing shared
    }

    def channel(self, sid: str, owner: str) -> str:
        return owner_channel(sid, owner, self.corpus_of, self.disciplines_of)

    def test_sibling_is_same_corpus(self):
        self.assertEqual(self.channel("a", "b"), "same_corpus")

    def test_shared_discipline_other_corpus_is_prior(self):
        self.assertEqual(self.channel("a", "c"), "prior_corpus")

    def test_disjoint_discipline_is_external(self):
        self.assertEqual(self.channel("a", "d"), "external")

    def test_self_support_is_recursive(self):
        self.assertEqual(self.channel("a", "a"), "recursive")

    def test_precedence_prefers_the_most_independent_owner(self):
        # Attribution is generous on purpose: a low external share must not be
        # an artifact of the tie-break.
        self.assertEqual(
            best_channel({"same_corpus": 9, "external": 1}), "external")
        self.assertEqual(
            best_channel({"same_corpus": 9, "prior_corpus": 1}), "prior_corpus")
        self.assertEqual(best_channel({"recursive": 1}), "recursive")
        self.assertEqual(best_channel({}), "recursive")


class ChannelSplitOverCorpus(unittest.TestCase):
    """The split as run over `data/` — one analysis shared by every test."""

    @classmethod
    def setUpClass(cls):
        cls.result = analyze(REPO_ROOT / "data")
        cls.decompositions = cls.result["decompositions"]
        cls.summary = cls.result["channel_summary"]
        cls.by_id = {d["statement_id"]: d for d in cls.decompositions}

    # -- GC4: the split is a reporting change, not a scoring change ---------

    def test_aggregate_totals_unchanged(self):
        graph = self.summary["graph"]
        self.assertEqual(graph["mean_groundedness"], 0.770)
        self.assertEqual(
            sum(d["grounded_exact"] for d in self.decompositions), 440)
        self.assertEqual(
            sum(d["grounded_via_pattern"] for d in self.decompositions), 75)
        self.assertEqual(
            sum(1 for d in self.decompositions if d["constituents"]), 193)

    def test_groundedness_is_still_grounded_over_considered(self):
        for d in self.decompositions:
            expected = (round((d["grounded_exact"] + d["grounded_via_pattern"])
                              / d["considered"], 3) if d["considered"] else 1.0)
            self.assertEqual(d["groundedness"], expected, d["statement_id"])

    # -- GC5: the channels partition the numerator -------------------------

    def test_channel_counts_partition_the_numerator(self):
        for d in self.decompositions:
            self.assertEqual(
                sum(d["channels"].values()),
                d["grounded_exact"] + d["grounded_via_pattern"],
                d["statement_id"])

    def test_channel_shares_sum_to_groundedness(self):
        for d in self.decompositions:
            self.assertAlmostEqual(
                sum(channel_shares(d).values()), d["groundedness"], places=3,
                msg=d["statement_id"])

    def test_every_constituent_carries_a_known_channel(self):
        for d in self.decompositions:
            for c in d["constituents"]:
                self.assertIn(c["channel"], CHANNELS, d["statement_id"])
                if c["grounded_via"] == "pattern":
                    self.assertEqual(c["channel"], "pattern_absorption")
                    self.assertIn(c["absorbed_from_channel"], CHANNELS)

    # -- The regression case named by ROADMAP-v0.7 item 10 -----------------

    def test_provability_still_aggregates_to_one(self):
        prov = [d for d in self.decompositions
                if d["corpus_id"] == PROVABILITY]
        self.assertEqual(len(prov), 6)
        self.assertTrue(all(d["groundedness"] == 1.0 for d in prov))

    def test_provability_external_channel_is_near_zero(self):
        block = self.summary["corpora"][PROVABILITY]
        self.assertLessEqual(block["channel_means"]["external"], 0.05)
        self.assertEqual(block["channel_means"]["prior_corpus"], 0.0)
        prov = [d for d in self.decompositions
                if d["corpus_id"] == PROVABILITY]
        zero_external = [d for d in prov if d["channels"]["external"] == 0]
        self.assertGreaterEqual(len(zero_external), 5)

    def test_provability_score_is_carried_by_self_and_absorption(self):
        means = self.summary["corpora"][PROVABILITY]["channel_means"]
        self.assertGreaterEqual(
            means["same_corpus"] + means["pattern_absorption"], 0.9)
        self.assertEqual(max(means, key=means.get), "same_corpus")

    def test_loeb_boxed_premise_is_absorption_of_external_credit(self):
        """The recorded mechanism, now attributed instead of hidden.

        Loeb's reflection premise grounds on ex falso's `IMPLIES(?0:P, ?1:V)`
        by a slot swallowing the boxed subtree. Under the aggregate that credit
        was indistinguishable from grounding in `data/logic`; the channel now
        says absorption, and records what it would have claimed.
        """
        loeb = self.by_id["provability.modal.loeb_axiom"]
        premise = [c for c in loeb["constituents"]
                   if c["skeleton"] == "IMPLIES⟨BOX⟨?0:V⟩, ?0:V⟩"]
        self.assertEqual(len(premise), 1)
        c = premise[0]
        self.assertEqual(c["channel"], "pattern_absorption")
        self.assertEqual(c["absorbed_from_channel"], "external")
        self.assertIn("logic.inference.ex_falso_quodlibet",
                      c["pattern_known_from"])

    def test_provability_box_recurrence_is_same_corpus(self):
        """BOX exists nowhere else in the graph, so no BOX credit is external.

        A bare `BOX(slot)` grounds on its siblings (same_corpus); a boxed
        application such as `BOX(IMPLIES(?0:V, ?1:V))` grounds by instantiating
        the bare form, which is absorption. Neither may be attributed outside
        the corpus, and that is the assertion: the head is corpus-private.
        """
        seen_bare = 0
        for d in self.decompositions:
            if d["corpus_id"] != PROVABILITY:
                continue
            for c in d["constituents"]:
                if not c["skeleton"].startswith("BOX⟨"):
                    continue
                self.assertNotIn(c["channel"], ("external", "prior_corpus"),
                                 f"{d['statement_id']} {c['skeleton']}")
                if c["skeleton"] in ("BOX⟨?0:V⟩", "BOX⟨?0:P⟩"):
                    seen_bare += 1
                    self.assertEqual(c["channel"], "same_corpus",
                                     f"{d['statement_id']} {c['skeleton']}")
        self.assertGreaterEqual(seen_bare, 3)

    # -- the flag must discriminate, not just restate the aggregate --------

    def test_self_certifying_flag_is_not_vacuous(self):
        flagged = [cid for cid, blk in self.summary["corpora"].items()
                   if blk["self_certifying"]]
        self.assertEqual(flagged, [PROVABILITY])
        high = [cid for cid, blk in self.summary["corpora"].items()
                if blk["mean_groundedness"] >= 0.9]
        # Capability-blind baseline for the flag: "aggregate >= 0.9" alone
        # would flag more corpora than the channel test does.
        self.assertGreater(len(high), len(flagged))


if __name__ == "__main__":
    unittest.main()
