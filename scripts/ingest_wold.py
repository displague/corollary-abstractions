#!/usr/bin/env python3
"""Deterministic WOLD lexicon ingestion + vocabulary-reach measurement.

WOLD (World Loanword Database, CLDF dataset lexibank/wold) is the first
EMPIRICAL-TIER multilingual lexicon for the language-as-structure lane: the
1,460 core LWT meanings (concept list Haspelmath-2009-1460), each with word
forms in a declared subset of the 41 WOLD recipient vocabularies. Per the
house rule for lexical sources (data_sources/manifest.json), it enters the
ontology at `empirical` only -- it never grounds a frame verdict and never
appears in `verified_by`.

Two stages, mirroring ingest_minif2f.py:

  extract  pinned release zip (SHA-256 verified against
           data_sources/manifest.json; gitignored under data_sources/archives/)
           -> committed data_sources/derived/wold/lexicon.json
  reach    committed lexicon.json + the repo's CURRENT vocabularies
           -> committed experiments/wold_reach.json

The reach stage is the measure-before-claiming number: of the 1,460 meanings,
how many connect to vocabulary the repo already has TODAY -- the langgen toy
lexicon (experiments/langgen.py), English content tokens in data/*/nodes.json
metadata, and Open English WordNet lemmas (the manifest-pinned OEWN archive,
required for this stage so the committed number is never a silent partial).
This is honesty about a lexicon's usefulness, not a wiring step: nothing in
any runtime path consumes these artifacts yet.

Language subset (declared, disclosed in the extract): English, Dutch,
Romanian, Japanese, Vietnamese, MandarinChinese. Why: English is the repo's
realization language (the reach targets are all English-keyed); Dutch is the
only vocabulary attesting all 1,460 core meanings; Romanian is the
highest-coverage Romance vocabulary -- Spanish, the natural pick next to the
repo's corpusdata-span source, is only a DONOR language in WOLD, not one of
the 41 recipient vocabularies; Japanese, Vietnamese and Mandarin Chinese are
the three highest-coverage non-Indo-European vocabularies and span three
distinct families. Six keeps the committed artifact small (~11k forms).

Determinism: rows keep parameters.csv/forms.csv source order, no timestamps,
LF-only bytes via write_bytes, so regeneration is byte-identical and testable.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
from pathlib import Path
from zipfile import ZipFile

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

MANIFEST = REPO_ROOT / "data_sources" / "manifest.json"
ARCHIVE_DIR = REPO_ROOT / "data_sources" / "archives"
EXTRACT_PATH = REPO_ROOT / "data_sources" / "derived" / "wold" / "lexicon.json"
REACH_PATH = REPO_ROOT / "experiments" / "wold_reach.json"

MANIFEST_SOURCE_ID = "git-lexibank-wold"
WORDNET_SOURCE_ID = "wordnet-2025-json"
CLDF_PREFIX = "wold-4.2/cldf/"

#: The declared vocabulary subset (rationale in the module docstring).
LANGUAGES = (
    "English",
    "Dutch",
    "Romanian",
    "Japanese",
    "Vietnamese",
    "MandarinChinese",
)

LANGUAGE_SUBSET_RATIONALE = (
    "English: the repo's realization language -- every reach target is "
    "English-keyed. Dutch: the only WOLD vocabulary attesting all 1,460 core "
    "meanings. Romanian: highest-coverage Romance vocabulary (Spanish is only "
    "a donor language in WOLD, not one of the 41 recipient vocabularies). "
    "Japanese, Vietnamese, MandarinChinese: the three highest-coverage "
    "non-Indo-European vocabularies, spanning three distinct families. Six "
    "vocabularies keep the committed extract small."
)


# --------------------------------------------------------------------------
# Shared plumbing (mirrors grammar_coverage.write_json without importing the
# head-algebra machinery this lexicon slice does not use)
# --------------------------------------------------------------------------

def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def serialize(doc: dict) -> bytes:
    return (
        json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    ).encode("utf-8")


def write_json(path: Path, doc: dict) -> None:
    # write_bytes, not write_text: on Windows write_text translates \n -> \r\n,
    # which breaks byte-for-byte regeneration. .gitattributes pins these LF.
    path.write_bytes(serialize(doc))


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def pct(num: int, den: int) -> float:
    return round(100.0 * num / den, 1) if den else 0.0


def _load_manifest_source(source_id: str) -> dict:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for src in manifest["sources"]:
        if src["id"] == source_id:
            return src
    raise KeyError(f"manifest source `{source_id}` not found")


def _verified_archive(source_id: str) -> tuple[Path, dict] | None:
    """Locate + SHA-verify a pinned archive; None (with stderr note) if absent."""
    src = _load_manifest_source(source_id)
    path = ARCHIVE_DIR / src["filename"]
    if not path.exists():
        print(
            f"MISSING: {path} not present. Fetch the pinned source first:\n"
            f"  python scripts/fetch_sources.py --fetch {source_id}",
            file=sys.stderr,
        )
        return None
    digest = _sha256_bytes(path.read_bytes())
    if digest != src["sha256"]:
        raise SystemExit(
            f"SHA MISMATCH for {src['filename']}:\n"
            f"  expected {src['sha256']}\n  got      {digest}\n"
            "Refusing to work from unpinned bytes."
        )
    return path, src


# --------------------------------------------------------------------------
# Stage 1: extract  (CLDF tables -> meaning_id -> per-language forms)
# --------------------------------------------------------------------------

def _cldf_rows(zipped: ZipFile, table: str) -> list[dict]:
    with zipped.open(CLDF_PREFIX + table) as fh:
        return list(csv.DictReader(io.TextIOWrapper(fh, encoding="utf-8")))


def build_extract(archive: Path, src: dict) -> dict:
    """Pure function of the verified archive bytes -> extract doc."""
    with ZipFile(archive) as zipped:
        params = _cldf_rows(zipped, "parameters.csv")
        langs = {row["ID"]: row for row in _cldf_rows(zipped, "languages.csv")}
        forms = _cldf_rows(zipped, "forms.csv")

    subset = set(LANGUAGES)
    core = [p for p in params if p["Core_list"] == "yes"]

    # forms.csv source order is preserved; duplicates within one
    # (meaning, language) cell are dropped on first-wins.
    by_meaning: dict[str, dict[str, list[str]]] = {p["ID"]: {} for p in core}
    for f in forms:
        if f["Language_ID"] not in subset:
            continue
        cell = by_meaning.get(f["Parameter_ID"])
        if cell is None:  # non-core meaning
            continue
        bucket = cell.setdefault(f["Language_ID"], [])
        form = f["Form"]
        if form and form not in bucket:
            bucket.append(form)

    meanings = []
    for p in core:  # parameters.csv order == canonical LWT meaning order
        cell = by_meaning[p["ID"]]
        meanings.append(
            {
                "id": p["ID"],
                "name": p["Name"],
                "concepticon_id": p["Concepticon_ID"],
                "concepticon_gloss": p["Concepticon_Gloss"],
                "semantic_field": p["Semantic_field"],
                "semantic_category": p["Semantic_category"],
                # absent key = vocabulary does not attest the meaning; never
                # an empty list, so coverage gaps are visible not padded.
                "forms": {lang: cell[lang] for lang in LANGUAGES if lang in cell},
            }
        )

    language_records = {}
    for lang in LANGUAGES:
        row = langs[lang]
        attested = [m for m in meanings if lang in m["forms"]]
        language_records[lang] = {
            "name": row["Name"],
            "glottocode": row["Glottocode"],
            "family": row["Family"],
            "wold_vocabulary_id": row["WOLD_ID"],
            "meanings_attested": len(attested),
            "form_count": sum(len(m["forms"][lang]) for m in attested),
        }

    return {
        "generated_by": "scripts/ingest_wold.py extract",
        "source": {
            "id": src["id"],
            "url": src["url"],
            "release_tag": src["release_tag"],
            "sha256": src["sha256"],
            "license": "CC BY 4.0",
            "attribution": src["attribution"],
            "concept_list": "Haspelmath-2009-1460 (Core_list=yes rows of cldf/parameters.csv)",
        },
        "tier": "empirical -- never grounds a frame verdict or verified_by (house rule)",
        "language_subset": list(LANGUAGES),
        "language_subset_rationale": LANGUAGE_SUBSET_RATIONALE,
        "languages": language_records,
        "meaning_count": len(meanings),
        "meanings": meanings,
    }


def run_extract() -> int:
    located = _verified_archive(MANIFEST_SOURCE_ID)
    if located is None:
        return 2
    archive, src = located
    doc = build_extract(archive, src)
    if doc["meaning_count"] != 1460:
        print(
            f"COUNT MISMATCH: extracted {doc['meaning_count']} core meanings, "
            "the LWT list pins 1460. Parser drift; refusing.",
            file=sys.stderr,
        )
        return 4
    EXTRACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_json(EXTRACT_PATH, doc)
    forms_total = sum(rec["form_count"] for rec in doc["languages"].values())
    print(
        f"extract OK: {doc['meaning_count']} meanings x {len(LANGUAGES)} "
        f"vocabularies ({forms_total} forms) -> {rel(EXTRACT_PATH)}"
    )
    return 0


# --------------------------------------------------------------------------
# Stage 2: reach  (lexicon.json + current repo vocabularies -> honest number)
# --------------------------------------------------------------------------

_ARTICLE_RE = re.compile(r"^(?:the|a|an|to|be)\s+", re.IGNORECASE)
_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$|\(\d\)$")
_TOKEN_RE = re.compile(r"[a-z][a-z-]{2,}")

#: Function words excluded from the data/ metadata token vocabulary -- they
#: would connect meanings like "and", "in", "or" vacuously.
_STOPWORDS = frozenset(
    "the and for with from into over under between are was were has have not "
    "its this that when where which whose one two all any than then also".split()
)


def english_candidates(meaning: dict) -> list[str]:
    """English match keys for one meaning: its English WOLD forms plus the
    normalized LWT meaning name ('the mountain or hill' -> 'mountain', 'hill').
    Lowercased; multi-word phrases kept (WordNet has multi-word lemmas)."""
    out: list[str] = []

    def add(s: str) -> None:
        s = " ".join(s.strip().lower().split())
        if s and s not in out:
            out.append(s)

    for form in meaning["forms"].get("English", ()):
        add(_PAREN_RE.sub("", form))
    name = _PAREN_RE.sub("", meaning["name"])
    name = _ARTICLE_RE.sub("", name.strip())
    for alt in name.split(" or "):
        add(_ARTICLE_RE.sub("", alt))
    return out


def langgen_vocab() -> frozenset[str]:
    """The toy bilingual grammar's English lexicon (experiments/langgen.py)."""
    sys.path.insert(0, str(REPO_ROOT / "experiments"))
    import langgen  # noqa: PLC0415

    return frozenset(
        w.lower()
        for w in (
            langgen.NOUNS + langgen.ADJS + langgen.VERBS + langgen.DIMS + langgen.INTENS
        )
    )


def corpus_node_tokens() -> frozenset[str]:
    """English content tokens in data/*/nodes.json metadata (title, topic,
    subfield, disciplines, canonical_objects) -- the corpus's own concept
    naming vocabulary."""
    tokens: set[str] = set()
    for path in sorted(REPO_ROOT.glob("data/*/nodes.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for node in doc.get("statement_nodes", []):
            ctx = node.get("theory_context", {})
            texts = [
                node.get("title", ""),
                ctx.get("subfield", ""),
                ctx.get("topic", ""),
                *ctx.get("disciplines", []),
                *ctx.get("canonical_objects", []),
            ]
            for text in texts:
                tokens.update(_TOKEN_RE.findall(text.lower().replace("_", " ")))
    return frozenset(tokens - _STOPWORDS)


def wordnet_lemma_keys(archive: Path) -> frozenset[str]:
    """All entry lemma keys of the pinned OEWN archive, via the same
    normalization wordnet_store uses for lookup."""
    from wordnet_store import WordNetIndex, lemma_key  # noqa: PLC0415

    index = WordNetIndex.load(archive)
    return frozenset(lemma_key(k) for k in index.lemma_synsets)


def build_reach(lexicon: dict, targets: dict[str, frozenset[str]]) -> dict:
    """Pure function: extract doc + named vocab sets -> reach doc."""
    from wordnet_store import lemma_key  # noqa: PLC0415

    target_names = list(targets)
    per_meaning = []
    mapped_counts = {name: 0 for name in target_names}
    unmapped_ids = []
    for meaning in lexicon["meanings"]:
        candidates = english_candidates(meaning)
        hits = []
        for name in target_names:
            vocab = targets[name]
            if any(lemma_key(c) in vocab for c in candidates):
                hits.append(name)
                mapped_counts[name] += 1
        if not hits:
            unmapped_ids.append(meaning["id"])
        per_meaning.append(
            {"id": meaning["id"], "gloss": meaning["concepticon_gloss"], "mapped": hits}
        )

    total = lexicon["meaning_count"]
    mapped_any = total - len(unmapped_ids)
    return {
        "generated_by": "scripts/ingest_wold.py reach",
        "question": "Of the 1,460 core LWT meanings, how many connect to "
        "vocabulary the repo already has today? Measured, not asserted; "
        "nothing consumes this at runtime yet.",
        "source_lexicon": {
            "path": rel(EXTRACT_PATH),
            "release_tag": lexicon["source"]["release_tag"],
            "meaning_count": total,
        },
        "match_rule": "a meaning maps to a target iff any of its English "
        "candidates (English WOLD forms + normalized LWT name, lowercased, "
        "wordnet_store.lemma_key-normalized) is in the target vocabulary; "
        "exact match only, no stemming.",
        "targets": {
            name: {
                "vocab_size": len(targets[name]),
                "mapped": mapped_counts[name],
                "pct": pct(mapped_counts[name], total),
            }
            for name in target_names
        },
        "totals": {
            "meanings": total,
            "mapped_any": {"count": mapped_any, "pct": pct(mapped_any, total)},
            "unmapped": {"count": len(unmapped_ids), "pct": pct(len(unmapped_ids), total)},
        },
        "unmapped_meaning_ids": unmapped_ids,
        "per_meaning": per_meaning,
    }


def run_reach() -> int:
    if not EXTRACT_PATH.exists():
        print(
            f"MISSING extract: {rel(EXTRACT_PATH)}. Run `extract` first.",
            file=sys.stderr,
        )
        return 2
    located = _verified_archive(WORDNET_SOURCE_ID)
    if located is None:
        # Required, not optional: a reach number computed without WordNet
        # would silently undercount and still look committed.
        return 2
    wordnet_archive, _ = located
    lexicon = json.loads(EXTRACT_PATH.read_text(encoding="utf-8"))
    targets = {
        "langgen_vocab": langgen_vocab(),
        "corpus_node_tokens": corpus_node_tokens(),
        "wordnet_lemmas": wordnet_lemma_keys(wordnet_archive),
    }
    doc = build_reach(lexicon, targets)
    write_json(REACH_PATH, doc)
    t = doc["totals"]
    lines = [f"reach OK -> {rel(REACH_PATH)}"]
    for name, rec in doc["targets"].items():
        lines.append(
            f"  {name:<20} {rec['mapped']}/{t['meanings']} ({rec['pct']}%) "
            f"[vocab {rec['vocab_size']}]"
        )
    lines.append(
        f"  mapped-any:          {t['mapped_any']['count']}/{t['meanings']} "
        f"({t['mapped_any']['pct']}%); unmapped {t['unmapped']['count']}"
    )
    print("\n".join(lines))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "stage",
        choices=["extract", "reach", "all"],
        help="extract: CLDF zip -> lexicon.json (needs pinned wold archive); "
        "reach: lexicon.json -> wold_reach.json (needs pinned WordNet archive); "
        "all: both.",
    )
    args = ap.parse_args(argv)
    if args.stage in ("extract", "all"):
        rc = run_extract()
        if rc != 0:
            return rc
    if args.stage in ("reach", "all"):
        rc = run_reach()
        if rc != 0:
            return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
