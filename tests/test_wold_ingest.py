"""WOLD lexicon ingestion: manifest pin integrity, load-bearing attribution,
derived-artifact shape, and byte-for-byte regeneration of both committed
artifacts.

The citation strings are REQUIRED (CC BY 4.0 attribution) and therefore
load-bearing: tests assert them verbatim in the manifest entry, the derived
NOTICE, and the extract itself. Archive-dependent regeneration tests use the
skip-if-archive-missing pattern (the zips are gitignored; CI regenerates what
it can from committed inputs and skips the rest loudly rather than passing
vacuously).
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import ingest_wold as ing  # noqa: E402

MANIFEST = json.loads(
    (REPO_ROOT / "data_sources" / "manifest.json").read_text(encoding="utf-8")
)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")

CITATION_WOLD = (
    "Haspelmath, Martin & Tadmor, Uri (eds.) 2009. World Loanword Database. "
    "Leipzig: Max Planck Institute for Evolutionary Anthropology. "
    "https://wold.clld.org (CLDF dataset lexibank/wold v4.2)"
)
CITATION_CLDF = (
    "CLDF: Forkel et al. 2018, Cross-Linguistic Data Formats, "
    "Scientific Data 5:180205."
)

DERIVED_DIR = REPO_ROOT / "data_sources" / "derived" / "wold"
WOLD_ARCHIVE = REPO_ROOT / "data_sources" / "archives" / "wold-4.2.zip"
WORDNET_ARCHIVE = (
    REPO_ROOT / "data_sources" / "archives" / "english-wordnet-2025-json.zip"
)


def _wold_source() -> dict:
    return next(s for s in MANIFEST["sources"] if s["id"] == "git-lexibank-wold")


def _lexicon() -> dict:
    return json.loads((DERIVED_DIR / "lexicon.json").read_text(encoding="utf-8"))


def _reach() -> dict:
    return json.loads(
        (REPO_ROOT / "experiments" / "wold_reach.json").read_text(encoding="utf-8")
    )


class ManifestPin(unittest.TestCase):
    """The source must be release-pinned with a real SHA so the transform is
    reproducible from exact bytes, and the license claim must be the one
    actually found in the archive."""

    def test_entry_is_fully_pinned(self) -> None:
        src = _wold_source()
        self.assertEqual(src["access"], "direct")
        self.assertEqual(src["release_tag"], "v4.2")
        self.assertIn("/archive/refs/tags/v4.2.zip", src["url"], "tagged release, not a moving branch")
        self.assertEqual(src["filename"], "wold-4.2.zip")
        self.assertTrue(_HEX64.match(src["sha256"]), "sha256 not 64-hex")
        self.assertIsInstance(src["size_bytes"], int)
        self.assertGreater(src["size_bytes"], 0)

    def test_license_records_what_the_archive_says(self) -> None:
        # CC BY 4.0 as found: LICENSE text + metadata.json declaration.
        lic = _wold_source()["license"]
        self.assertIn("CC BY 4.0", lic)
        self.assertIn("Creative Commons Attribution 4.0 International", lic)
        self.assertIn("CC-BY-4.0", lic)

    def test_purpose_pins_the_empirical_tier(self) -> None:
        purpose = _wold_source()["purpose"]
        self.assertIn("empirical", purpose.lower())
        self.assertIn("verified_by", purpose)
        self.assertIn("never grounds a frame verdict", purpose)


class RequiredCitations(unittest.TestCase):
    """CC BY 4.0 makes attribution a license condition; the citations are
    load-bearing and must appear verbatim everywhere the data does."""

    def test_manifest_attribution_verbatim(self) -> None:
        attribution = _wold_source()["attribution"]
        self.assertIn(CITATION_WOLD, attribution)
        self.assertIn(CITATION_CLDF, attribution)

    def test_notice_carries_both_citations(self) -> None:
        notice = (DERIVED_DIR / "NOTICE.md").read_text(encoding="utf-8")
        # NOTICE renders the citations as a wrapped blockquote; compare
        # whitespace-normalized so a reflow cannot silently drop words.
        flat = " ".join(notice.replace(">", " ").split())
        self.assertIn(CITATION_WOLD, flat)
        self.assertIn(CITATION_CLDF, flat)
        self.assertIn("CC BY 4.0", notice)

    def test_license_file_is_cc_by_40(self) -> None:
        text = (DERIVED_DIR / "LICENSE").read_text(encoding="utf-8")
        self.assertTrue(
            text.lstrip().startswith("Attribution 4.0 International"),
            "vendored LICENSE must be the CC BY 4.0 text found in the archive",
        )

    def test_extract_embeds_the_attribution(self) -> None:
        src_block = _lexicon()["source"]
        self.assertIn(CITATION_WOLD, src_block["attribution"])
        self.assertIn(CITATION_CLDF, src_block["attribution"])
        self.assertEqual(src_block["attribution"], _wold_source()["attribution"])


class CommittedExtractShape(unittest.TestCase):
    def test_meaning_count_is_the_full_core_list(self) -> None:
        doc = _lexicon()
        self.assertEqual(doc["meaning_count"], 1460, "LWT core list is 1,460 meanings")
        self.assertEqual(len(doc["meanings"]), 1460)

    def test_language_subset_is_declared_and_closed(self) -> None:
        doc = _lexicon()
        self.assertEqual(doc["language_subset"], list(ing.LANGUAGES))
        self.assertTrue(doc["language_subset_rationale"])
        self.assertIn("Spanish", doc["language_subset_rationale"], "the Spanish gap is disclosed, not silent")
        for meaning in doc["meanings"]:
            self.assertLessEqual(
                set(meaning["forms"]), set(ing.LANGUAGES), meaning["id"]
            )

    def test_meanings_have_concepticon_identity_and_nonempty_cells(self) -> None:
        doc = _lexicon()
        for meaning in doc["meanings"]:
            for key in ("id", "name", "concepticon_gloss", "semantic_field", "forms"):
                self.assertIn(key, meaning, meaning.get("id"))
            for lang, forms in meaning["forms"].items():
                self.assertTrue(forms, f"{meaning['id']}/{lang}: empty cell must be an absent key")
                self.assertEqual(len(forms), len(set(forms)), f"{meaning['id']}/{lang}: duplicate form")
        self.assertEqual(doc["meanings"][0]["id"], "1-1")
        self.assertEqual(doc["meanings"][0]["concepticon_gloss"], "WORLD")

    def test_language_records_match_the_meanings_table(self) -> None:
        doc = _lexicon()
        for lang, rec in doc["languages"].items():
            attested = [m for m in doc["meanings"] if lang in m["forms"]]
            self.assertEqual(rec["meanings_attested"], len(attested), lang)
            self.assertEqual(
                rec["form_count"],
                sum(len(m["forms"][lang]) for m in attested),
                lang,
            )
        # the subset-selection claim that Dutch attests the full core list
        self.assertEqual(doc["languages"]["Dutch"]["meanings_attested"], 1460)

    def test_tier_is_empirical_in_the_artifact_itself(self) -> None:
        doc = _lexicon()
        self.assertIn("empirical", doc["tier"])
        self.assertIn("verified_by", doc["tier"])


class CandidateExtraction(unittest.TestCase):
    """The reach number is only as honest as the English-candidate rule."""

    def _mk(self, name: str, english: list[str] | None = None) -> dict:
        forms = {"English": english} if english else {}
        return {"name": name, "forms": forms}

    def test_article_and_alternation_normalization(self) -> None:
        c = ing.english_candidates(self._mk("the mountain or hill"))
        self.assertIn("mountain", c)
        self.assertIn("hill", c)

    def test_sense_index_and_infinitive_are_stripped(self) -> None:
        self.assertIn("burn", ing.english_candidates(self._mk("to burn(1)")))
        self.assertIn("rough", ing.english_candidates(self._mk("rough(2)")))

    def test_english_forms_come_first_and_are_deduped(self) -> None:
        c = ing.english_candidates(self._mk("the world", ["world"]))
        self.assertEqual(c, ["world"])

    def test_multiword_phrases_survive_for_wordnet(self) -> None:
        c = ing.english_candidates(self._mk("the mother-in-law (of a man)"))
        self.assertEqual(c, ["mother-in-law"])


class CommittedReach(unittest.TestCase):
    def test_totals_partition_the_meanings(self) -> None:
        reach = _reach()
        total = reach["totals"]["meanings"]
        self.assertEqual(total, 1460)
        mapped = reach["totals"]["mapped_any"]["count"]
        unmapped = reach["totals"]["unmapped"]["count"]
        self.assertEqual(mapped + unmapped, total)
        self.assertEqual(len(reach["unmapped_meaning_ids"]), unmapped)
        self.assertEqual(len(reach["per_meaning"]), total)
        # mapped_any dominates every single target
        for name, rec in reach["targets"].items():
            self.assertGreaterEqual(mapped, rec["mapped"], name)

    def test_per_meaning_agrees_with_the_headline_numbers(self) -> None:
        reach = _reach()
        empty = [r["id"] for r in reach["per_meaning"] if not r["mapped"]]
        self.assertEqual(empty, reach["unmapped_meaning_ids"])
        for name, rec in reach["targets"].items():
            n = sum(1 for r in reach["per_meaning"] if name in r["mapped"])
            self.assertEqual(n, rec["mapped"], name)

    def test_repo_local_targets_recount_from_committed_lexicon(self) -> None:
        """langgen + data/ tokens need no archive: recount them fresh so the
        committed reach cannot drift from the repo it describes."""
        lexicon = _lexicon()
        from wordnet_store import lemma_key

        targets = {
            "langgen_vocab": ing.langgen_vocab(),
            "corpus_node_tokens": ing.corpus_node_tokens(),
        }
        reach = _reach()
        for name, vocab in targets.items():
            self.assertEqual(len(vocab), reach["targets"][name]["vocab_size"], name)
            n = sum(
                1
                for m in lexicon["meanings"]
                if any(lemma_key(c) in vocab for c in ing.english_candidates(m))
            )
            self.assertEqual(n, reach["targets"][name]["mapped"], name)


class Regeneration(unittest.TestCase):
    """Byte-for-byte: the committed artifacts are pure functions of pinned
    bytes (extract) and of committed inputs + the pinned WordNet archive
    (reach). Skips loudly when a gitignored archive is absent."""

    @unittest.skipUnless(WOLD_ARCHIVE.exists(), "pinned wold-4.2.zip not fetched")
    def test_extract_regenerates_byte_for_byte(self) -> None:
        rebuilt = ing.build_extract(WOLD_ARCHIVE, _wold_source())
        self.assertEqual(
            ing.serialize(rebuilt),
            (DERIVED_DIR / "lexicon.json").read_bytes(),
            "committed lexicon.json is stale; re-run `ingest_wold.py extract`",
        )

    @unittest.skipUnless(
        WORDNET_ARCHIVE.exists(), "pinned OEWN archive not fetched"
    )
    def test_reach_regenerates_byte_for_byte(self) -> None:
        lexicon = _lexicon()
        targets = {
            "langgen_vocab": ing.langgen_vocab(),
            "corpus_node_tokens": ing.corpus_node_tokens(),
            "wordnet_lemmas": ing.wordnet_lemma_keys(WORDNET_ARCHIVE),
        }
        rebuilt = ing.build_reach(lexicon, targets)
        self.assertEqual(
            ing.serialize(rebuilt),
            (REPO_ROOT / "experiments" / "wold_reach.json").read_bytes(),
            "committed wold_reach.json is stale; re-run `ingest_wold.py reach`",
        )


if __name__ == "__main__":
    unittest.main()
