"""Tests for R3, ERRATUM's flip probe (`DESIGN-handles.md` §7 B9).

A probe that reports zero of something is the easiest kind of probe to
be wrong about, because "found nothing" and "cannot find anything" print
the same number. So the tests are aimed at exactly that:

1. **the flip predicate can fire** -- exercised directly on synthetic
   turn records, both ways, including the two near-misses that must NOT
   count (a refusal that is still a refusal, an answer that merely
   re-rendered);
2. **the plant is a real plant** -- the committed synthetic journal
   records a refusal, names a statement that exists in the corpus today,
   and the probe classified it as a flip. B9's floor is on this and not
   on the yield, and if this is green with a zero yield the zero means
   something;
3. **the zero is a measured zero** -- 410 turns replayed over 60
   journals, every one accounted for in exactly one outcome bucket, and
   the denominators published rather than implied;
4. **the window is stated from a digest, not from a commit log** -- the
   corpus-identity claim is the recorded `corpora_digest` against the
   recomputed one, and the git figures are labelled as narrative;
5. **the bypass is disclosed** -- replay passes the journals' own pins,
   and the genuine pin mismatch (which is non-empty at this tip) is
   published beside it.

The probe itself takes several minutes over 60 journals, so it is not
re-run here. Point 2 re-serves the plant's single line, which is the one
piece of live evidence that costs nothing.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import erratum_probe as probe  # noqa: E402
import session_ledger as ledger  # noqa: E402

ARTIFACT = ROOT / "experiments" / "erratum_probe.json"
PLANT = ROOT / "experiments" / "erratum_plant_journal.json"
SESSIONS = ROOT / "experiments" / "sessions"


def turn(kind: str, refusal_type: str | None) -> dict:
    return {"result": {"kind": kind, "refusal_type": refusal_type,
                       "answer_bytes_digest": "x"}}


class TheFlipPredicateCanFire(unittest.TestCase):
    """Point 1. Both directions, and the two near-misses."""

    def test_a_recorded_refusal_is_recognised(self) -> None:
        self.assertTrue(probe.recorded_is_refusal(turn("refused", "twin_exhausted")))
        self.assertTrue(probe.recorded_is_refusal(turn("exhausted", None)))

    def test_a_recorded_answer_is_not_a_refusal(self) -> None:
        self.assertFalse(probe.recorded_is_refusal(turn("solved", None)))
        self.assertFalse(probe.recorded_is_refusal(turn("found", None)))

    def test_the_refusal_statuses_are_the_ledgers_own(self) -> None:
        """The predicate must not carry a private idea of what a refusal is."""

        artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(
            artifact["flip_definition"]["refusal_statuses"],
            sorted(ledger.REFUSAL_STATUSES))

    def test_a_refusal_that_is_still_a_refusal_is_not_a_flip(self) -> None:
        """Near-miss one. The classifier's own branch, restated as a rule."""

        artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        for row in artifact["real_flips"]["divergences"]["rows"]:
            self.assertFalse(row["recorded_was_refusal"]
                             and not row["replayed_is_refusal"],
                             "a divergence matching the flip shape was not "
                             "classified as a flip")

    def test_a_rerendered_answer_is_a_divergence_not_a_flip(self) -> None:
        """Near-miss two, asserted on the published definition."""

        artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        self.assertIn("DIVERGENCE",
                      artifact["flip_definition"]["a_flip_is_not"])
        for row in artifact["real_flips"]["flips"]:
            self.assertTrue(row["recorded_was_refusal"])
            self.assertFalse(row["replayed_is_refusal"])


class ThePlantIsARealPlant(unittest.TestCase):
    """Point 2. The floor B9 actually set."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.plant = json.loads(PLANT.read_text(encoding="utf-8"))
        cls.artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))

    def test_the_plant_records_a_refusal(self) -> None:
        record = self.plant["turns"][0]
        self.assertTrue(probe.recorded_is_refusal(record))
        self.assertEqual(record["result"]["refusal_type"], "twin_exhausted")

    def test_the_planted_line_names_a_statement_that_exists_today(self) -> None:
        """The whole point of the plant, checked against the corpus."""

        line = self.plant["turns"][0]["input_bytes"]
        self.assertTrue(line.startswith("twin "))
        named = line.split(" ", 1)[1]
        committed: set[str] = set()
        for path in sorted((ROOT / "data").glob("*/nodes.json")):
            document = json.loads(path.read_text(encoding="utf-8"))
            committed.update(node["statement_id"]
                             for node in document.get("statement_nodes", []))
        self.assertIn(named, committed)

    def test_the_planted_digest_is_a_real_refusal_from_a_different_line(self) -> None:
        provenance = self.plant["plant_provenance"]
        self.assertTrue(provenance["synthetic"])
        self.assertEqual(provenance["refusal_digest_taken_from_line"],
                         probe.PLANT_REFUSAL_SOURCE_LINE)
        self.assertNotEqual(provenance["input_line_names_statement"],
                            probe.PLANT_REFUSAL_SOURCE_LINE.split(" ", 1)[1])

    def test_the_probe_detected_it_and_the_floor_is_met(self) -> None:
        planted = self.artifact["planted_flip"]
        self.assertGreaterEqual(planted["detected"], probe.PLANTED_FLIP_FLOOR)
        self.assertTrue(planted["met"])
        self.assertEqual([t["outcome"] for t in planted["turns"]], ["FLIP"])

    def test_the_planted_line_still_answers_when_served_live(self) -> None:
        """The one live check, because the plant decays if the tree moves.

        If this line ever starts refusing again, the plant stops being a
        flip and the floor stops being met -- so it is asserted rather
        than assumed.
        """

        from harness import CoreSession, route_line  # noqa: PLC0415

        session = CoreSession.boot(ROOT, offline=True,
                                   session_id="test-erratum-plant")
        verdict = route_line(ROOT, session, self.plant["turns"][0]["input_bytes"])
        self.assertNotIn(verdict.get("status"), ledger.REFUSAL_STATUSES)

    def test_the_floor_is_argued_on_the_mechanism_not_the_yield(self) -> None:
        reason = self.artifact["planted_flip"][
            "why_the_floor_is_on_the_plant_and_not_on_the_yield"]
        self.assertIn("mechanism", reason)


class TheZeroIsAMeasuredZero(unittest.TestCase):
    """Point 3. Every turn accounted for, every denominator published."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        cls.real = cls.artifact["real_flips"]

    def test_every_committed_s_journal_was_replayed(self) -> None:
        journals = [p for p in sorted(SESSIONS.glob("v021-s*.json"))
                    if not p.name.endswith(".reads.json")]
        self.assertEqual(self.real["journals_replayed"], len(journals))
        turns = sum(len(json.loads(p.read_text(encoding="utf-8"))["turns"])
                    for p in journals)
        self.assertEqual(self.real["turns_replayed"], turns)

    def test_the_outcome_buckets_partition_the_turns(self) -> None:
        total = (self.real["turns_reproduced"]
                 + self.real["divergences"]["count"]
                 + self.real["count"])
        self.assertEqual(total, self.real["turns_replayed"])

    def test_the_refusal_denominator_is_published_and_non_zero(self) -> None:
        """A flip count over zero refusals would be vacuous."""

        self.assertGreater(self.real["turns_recording_a_refusal"], 0)
        self.assertEqual(
            sum(self.real["refusal_types_replayed"].values()),
            self.real["turns_recording_a_refusal"])

    def test_the_scale_sentence_is_published_when_the_count_is_zero(self) -> None:
        if self.real["count"] == 0:
            self.assertIn("prices the WINDOW", self.artifact["scale_sentence"])
            self.assertIn("B9", self.artifact["stop_rule"])
            self.assertIn("not re-run", self.artifact["stop_rule"])


class TheWindowIsStatedFromADigest(unittest.TestCase):
    """Point 4, and point 5's disclosure."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        cls.window = cls.artifact["window"]

    def test_the_corpus_claim_is_two_digests_compared(self) -> None:
        block = self.window["authoritative_because_it_is_a_digest"]
        journal = json.loads(
            (SESSIONS / "v021-s01.json").read_text(encoding="utf-8"))
        self.assertEqual(block["recorded_corpora_digest"],
                         journal["header"]["pins"]["corpora_digest"])
        self.assertEqual(block["corpus_moved"],
                         block["recorded_corpora_digest"]
                         != block["live_corpora_digest"])

    def test_the_live_digest_recomputes_today(self) -> None:
        from write_stage import durable_digest  # noqa: PLC0415

        block = self.window["authoritative_because_it_is_a_digest"]
        self.assertEqual(durable_digest(ROOT / "data"),
                         block["live_corpora_digest"])

    def test_a_zero_statement_delta_is_only_claimed_when_the_digest_holds(self) -> None:
        block = self.window["authoritative_because_it_is_a_digest"]
        if block["corpus_moved"]:
            self.assertIsNone(block["statements_added_in_the_window"])
        else:
            self.assertEqual(block["statements_added_in_the_window"], 0)

    def test_the_git_figures_are_labelled_as_narrative(self) -> None:
        narrative = self.window["checkout_derived_narrative"]
        self.assertIn("never evidence", narrative["caveat"])
        self.assertIn("v021-s", narrative["pathspec"])

    def test_the_pin_bypass_is_disclosed_with_the_real_mismatch(self) -> None:
        bypass = self.artifact["method_disclosures"]["pin_bypass"]
        self.assertEqual(bypass["genuine_pin_mismatch"],
                         self.window["capability_flips"]["pins_that_moved"])
        self.assertTrue(bypass["genuine_pin_mismatch"],
                        "the bypass disclosure claims a mismatch that is empty; "
                        "either the pins now match, in which case the bypass is "
                        "unnecessary and should be removed, or the comparison "
                        "is broken")

    def test_the_capability_flips_partition_the_pins(self) -> None:
        flips = self.window["capability_flips"]
        self.assertEqual(
            sorted(flips["pins_that_moved"] + flips["pins_that_held"]),
            sorted(ledger.PIN_FIELDS))

    def test_the_artifact_attests_the_committed_writer(self) -> None:
        """L2's answer: a provenance block, not a plea that the live guards
        substitute for one."""

        import hashlib  # noqa: PLC0415

        block = self.artifact["provenance"]
        writer = ROOT / "scripts" / "erratum_probe.py"
        self.assertEqual(block["writer"], "scripts/erratum_probe.py")
        self.assertEqual(
            block["writer_sha256_lf"],
            hashlib.sha256(
                writer.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            "the artifact attests a writer that is not the committed one -- "
            "regenerate it")
        self.assertTrue(block["inputs"])
        self.assertIn("does NOT cover", self.artifact["provenance_scope"])

    def test_every_replayed_journal_is_a_declared_input(self) -> None:
        """The provenance block must name what the probe actually read."""

        declared = {row["path"] for row in self.artifact["provenance"]["inputs"]}
        journals = [p for p in sorted(SESSIONS.glob("v021-s*.json"))
                    if not p.name.endswith(".reads.json")]
        for path in journals:
            self.assertIn(f"experiments/sessions/{path.name}", declared)

    def test_the_probe_wrote_only_its_two_artifacts(self) -> None:
        """The containment fence its siblings carry."""

        source = (ROOT / "scripts" / "erratum_probe.py").read_text(
            encoding="utf-8")
        self.assertEqual(source.count("write_text"), 2)
        self.assertIn("erratum_probe.json", source)
        self.assertIn("erratum_plant_journal.json", source)

    def test_the_slice_built_no_table_budget_or_question_set(self) -> None:
        for name in ("handles_table.json", "handles_partition.json",
                     "handles_enum_receipts.json", "handles_budget.json",
                     "budget_pilot.json"):
            self.assertFalse((ROOT / "experiments" / name).exists(), name)

    def test_the_plant_did_not_enter_the_sealed_journal_corpus(self) -> None:
        """A synthetic journal must never sit where the sealed ones live."""

        self.assertFalse((SESSIONS / PLANT.name).exists())
        self.assertEqual(PLANT.parent, ROOT / "experiments")
        seal = ROOT / "experiments" / "session_corpus_seal.json"
        if seal.exists():
            sealed = {entry["journal"] for entry in
                      json.loads(seal.read_text(encoding="utf-8"))["sessions"]}
            self.assertNotIn("experiments/erratum_plant_journal.json", sealed)

    def test_no_forgery_or_correctness_claim_is_made(self) -> None:
        claims = self.artifact["non_claims"]
        self.assertTrue(any("forgery" in c for c in claims))
        self.assertTrue(any("refusals are correct" in c for c in claims))


if __name__ == "__main__":
    unittest.main()
