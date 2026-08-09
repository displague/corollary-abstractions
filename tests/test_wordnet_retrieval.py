"""P-CF6 controls for the optional Open English WordNet retrieval store.

Registered before the external archive is adjudicated:

* a held-out synonym that the five committed stores miss reaches a corpus
  alias through WordNet;
* every lexical record remains empirical even beside formal corpus material;
* retrieval changes pointable context, never the frame executor's verdict;
* absent external bytes reproduce the five-store baseline exactly.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from zipfile import ZipFile


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from controller import Verdict  # noqa: E402
from frames import FrameExecutor, FrameSpec, Literal  # noqa: E402
from retrieval import (  # noqa: E402
    RetrievalItem,
    RetrievalState,
    RetrievalVerifier,
    UnifiedKnowledgeStore,
    point_action,
    retrieval_action,
)
from wordnet_store import WordNetIndex, WordNetSynset  # noqa: E402


def write_fixture(path: Path) -> None:
    entries = {
        "acceleration": {
            "n": {
                "sense": [
                    {"id": "acceleration%1:04:00::", "synset": "00331283-n"}
                ]
            }
        },
        "quickening": {
            "n": {
                "sense": [
                    {"id": "quickening%1:04:00::", "synset": "00331283-n"},
                    {"id": "quickening%1:22:00::", "synset": "13565986-n"},
                    {"id": "quickening%1:26:00::", "synset": "14071616-n"},
                ]
            }
        },
    }
    synsets = {
        "00331283-n": {
            "definition": ["the act of increasing speed"],
            "example": ["a quickening of the pulse"],
            "hypernym": ["00330000-n"],
            "ili": "i32000",
            "members": ["acceleration", "quickening"],
            "partOfSpeech": "n",
        },
        "00330000-n": {
            "definition": ["a change"],
            "members": ["change"],
            "partOfSpeech": "n",
        },
        "13565986-n": {
            "definition": ["the first motion of a fetus"],
            "members": ["quickening"],
            "partOfSpeech": "n",
        },
        "14071616-n": {
            "definition": ["the process of becoming alive"],
            "members": ["quickening"],
            "partOfSpeech": "n",
        },
    }
    with ZipFile(path, "w") as archive:
        archive.writestr("entries-a.json", json.dumps(entries))
        archive.writestr("noun.act.json", json.dumps(synsets))


def corpus_item(item_id: str = "corpus:physics.acceleration") -> RetrievalItem:
    return RetrievalItem(
        item_id=item_id,
        source="corpus",
        title="Constant acceleration",
        text="Acceleration is change in velocity per unit time.",
        epistemic_status="formal",
        source_ids=(item_id.removeprefix("corpus:"),),
        aliases=("acceleration",),
    )


class WordNetRetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.archive = Path(self.temp.name) / "oewn-2025.zip"
        write_fixture(self.archive)
        self.index = WordNetIndex.load(self.archive)
        self.target = corpus_item()
        self.store = UnifiedKnowledgeStore((self.target,), self.index)
        self.executor = FrameExecutor()
        self.frame = self.executor.open_frame(
            FrameSpec(frame="runtime.frames.wordnet_test", retrieval="open")
        )
        self.literal = Literal("request", "needs", "quickening")

    def state(self) -> RetrievalState:
        return RetrievalState.from_unknown(
            self.executor,
            self.frame,
            "answer",
            "quickening",
            self.literal,
        )

    def test_synonym_bridge_reaches_unique_corpus_owner(self) -> None:
        baseline = UnifiedKnowledgeStore((self.target,)).query("quickening")
        self.assertEqual(baseline.mode, "miss")

        result = self.store.query("quickening")
        self.assertEqual(result.mode, "synonym")
        self.assertIn(self.target, result.items)
        lexical = next(item for item in result.items if item.source == "wordnet")
        self.assertEqual(lexical.epistemic_status, "empirical")
        self.assertTrue(lexical.trusted)
        self.assertTrue(any(part.startswith("sha256:") for part in lexical.source_ids))
        self.assertEqual(
            self.store.binding_match_mode(self.target, "quickening"), "synonym"
        )

    def test_retrieve_then_point_binds_without_changing_frame_verdict(self) -> None:
        before = self.executor.check(self.frame, self.literal)
        verifier = RetrievalVerifier(self.store, self.executor)
        retrieved = verifier.evaluate(self.state(), retrieval_action("quickening"))
        self.assertIs(retrieved.verdict, Verdict.VERIFIED)
        self.assertEqual(retrieved.next_state.frame, self.frame)
        after = self.executor.check(retrieved.next_state.frame, self.literal)
        self.assertEqual((before.verdict, before.evidence), (after.verdict, after.evidence))

        pointed = verifier.evaluate(retrieved.next_state, point_action(0))
        self.assertIs(pointed.verdict, Verdict.VERIFIED)
        self.assertEqual(pointed.next_state.bindings, (("answer", self.target.item_id),))
        self.assertEqual(pointed.next_state.frame, self.frame)

    def test_wordnet_status_cannot_launder_from_formal_neighbor(self) -> None:
        result = self.store.query("quickening")
        statuses = {item.source: item.epistemic_status for item in result.items}
        self.assertEqual(statuses["corpus"], "formal")
        self.assertEqual(statuses["wordnet"], "empirical")
        self.assertTrue(
            all(
                item.epistemic_status == "empirical"
                for item in result.items
                if item.source == "wordnet"
            )
        )
        lexical = next(item for item in result.items if item.source == "wordnet")
        self.assertFalse(
            self.store.contains_item(replace(lexical, epistemic_status="formal"))
        )

    def test_ambiguous_synonym_bridge_cannot_bind(self) -> None:
        second = corpus_item("corpus:biology.acceleration")
        store = UnifiedKnowledgeStore((self.target, second), self.index)
        verifier = RetrievalVerifier(store, self.executor)
        retrieved = verifier.evaluate(self.state(), retrieval_action("quickening"))
        self.assertIs(retrieved.verdict, Verdict.VERIFIED)
        pointed = verifier.evaluate(retrieved.next_state, point_action(0))
        self.assertIs(pointed.verdict, Verdict.REFUSED)

    def test_polysemous_lexical_item_and_multi_sense_bridge_cannot_bind(self) -> None:
        result = self.store.query("quickening")
        lexical = next(item for item in result.items if item.source == "wordnet")
        self.assertIsNone(self.store.binding_match_mode(lexical, "quickening"))

        first = WordNetSynset(
            "one-n", ("quickening", "acceleration"), ("first sense",), (), (), "n"
        )
        second = WordNetSynset(
            "two-n", ("quickening", "acceleration"), ("second sense",), (), (), "n"
        )
        ambiguous_index = WordNetIndex(
            self.archive,
            self.index.archive_sha256,
            {first.synset_id: first, second.synset_id: second},
            {"quickening": (first.synset_id, second.synset_id)},
        )
        store = UnifiedKnowledgeStore((self.target,), ambiguous_index)
        self.assertIsNone(store.binding_match_mode(self.target, "quickening"))

    def test_exact_committed_alias_precedes_lexical_bridge(self) -> None:
        exact = RetrievalItem(
            item_id="corpus:exact.quickening",
            source="corpus",
            title="Quickening",
            text="An exact corpus record.",
            epistemic_status="derived",
            source_ids=("exact.quickening",),
            # Also a WordNet-bridged alias: exact project matching must still
            # win even when lexical ambiguity sees this same item.
            aliases=("quickening", "acceleration"),
        )
        result = UnifiedKnowledgeStore((exact, self.target), self.index).query(
            "quickening"
        )
        self.assertEqual(result.mode, "exact")
        self.assertEqual(result.items, (exact,))

    def test_eval_reports_valid_archive_misses_without_crashing(self) -> None:
        run = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "wordnet_eval.py"), str(self.archive)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(run.returncode, 1)
        self.assertNotIn("Traceback", run.stderr)
        self.assertIn("binding expectation mismatches", run.stdout)

    def test_missing_archive_preserves_five_store_baseline(self) -> None:
        baseline = UnifiedKnowledgeStore.load(
            REPO_ROOT / "data", REPO_ROOT / "reports"
        )
        absent = UnifiedKnowledgeStore.load(
            REPO_ROOT / "data",
            REPO_ROOT / "reports",
            Path(self.temp.name) / "absent.zip",
        )
        self.assertIsNone(absent.wordnet)
        self.assertEqual(absent.items, baseline.items)
        self.assertEqual(absent.query("quickening"), baseline.query("quickening"))

    def test_existing_malformed_archive_fails_closed(self) -> None:
        malformed = Path(self.temp.name) / "malformed.zip"
        malformed.write_bytes(b"not a zip")
        with self.assertRaisesRegex(ValueError, "not a valid zip"):
            WordNetIndex.load(malformed)

    def test_authoritative_index_maps_are_immutable(self) -> None:
        with self.assertRaises(TypeError):
            self.index.synsets["forged-n"] = next(iter(self.index.synsets.values()))
        with self.assertRaises(TypeError):
            self.index.lemma_synsets["forged"] = ("00331283-n",)


if __name__ == "__main__":
    unittest.main()
