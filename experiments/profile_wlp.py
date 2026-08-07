"""Profile word/lemma/PoS corpus samples: the real extrinsic-lexicon shape.

Reports, per corpus: token count, distinct surface forms, distinct lemmas,
surface-forms-per-lemma distribution (the empirical 'thesaurical twin'
fan-out), and PoS-ambiguous surface forms (same word, multiple lemmas) --
the real-world rate of the ambiguity the syn task simulated.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def profile(path: Path, word_col: int, lemma_col: int, pos_col: int) -> dict:
    lemma_forms: dict[str, set] = defaultdict(set)
    word_lemmas: dict[str, set] = defaultdict(set)
    n_tokens = 0
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) <= max(word_col, lemma_col, pos_col):
                continue
            word = parts[word_col].strip().lower()
            lemma = parts[lemma_col].strip().lower()
            if not word or not lemma or word.startswith("@@") or word == "-----":
                continue
            if not any(ch.isalpha() for ch in word):
                continue
            n_tokens += 1
            lemma_forms[lemma].add(word)
            word_lemmas[word].add(lemma)
    fanout = Counter(len(v) for v in lemma_forms.values())
    ambiguous = sum(1 for v in word_lemmas.values() if len(v) > 1)
    return {
        "file": str(path),
        "alpha_tokens": n_tokens,
        "distinct_words": len(word_lemmas),
        "distinct_lemmas": len(lemma_forms),
        "mean_forms_per_lemma": round(
            sum(len(v) for v in lemma_forms.values()) / max(len(lemma_forms), 1), 3),
        "lemmas_with_multiple_forms": sum(
            c for k, c in fanout.items() if k > 1),
        "max_forms_one_lemma": max(fanout) if fanout else 0,
        "ambiguous_words": ambiguous,
        "ambiguous_word_rate": round(ambiguous / max(len(word_lemmas), 1), 4),
    }


def main() -> None:
    base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data_real")
    jobs = [
        (base / "wiki-en-wlp" / "wordLemPoS.txt", 2, 3, 4, "wiki-en"),
        (base / "wiki-es-wlp" / "wordLemPoS.txt", 2, 3, 4, "wiki-es"),
    ]
    out = {}
    for path, w, l, p, name in jobs:
        if path.exists():
            out[name] = profile(path, w, l, p)
            print(f"{name}: {json.dumps(out[name], indent=1)}", flush=True)
    Path("results").mkdir(exist_ok=True)
    Path("results/wlp_profile.json").write_text(
        json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("-> results/wlp_profile.json")


if __name__ == "__main__":
    main()
