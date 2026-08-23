"""Read-only recurrence census over the committed corpus prose.

Grounds the maintainer's block-vocabulary idea before any design is
written: how much of the corpus's surface is recurrent blocks, how far
a greedy block dictionary compresses it, and how templated the
ingested prose really is. Reads data/*/nodes.json only; writes nothing
inside the repository.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(r"C:\Users\displ\Documents\corollary-abstractions")
OUT = Path(__file__).with_name("block_census_report.json")

meanings = []          # (corpus, statement_id, meaning)
titles = []
templates_src = []     # ingested meanings for template mining
anon_templates = Counter()

for nodes_path in sorted(REPO.glob("data/*/nodes.json")):
    doc = json.loads(nodes_path.read_text(encoding="utf-8"))
    records = doc["statement_nodes"] if isinstance(doc, dict) else doc
    corpus = nodes_path.parent.name
    for rec in records:
        sid = rec.get("statement_id", "")
        meaning = (rec.get("semantic_interpretation") or {}).get(
            "statement_meaning", ""
        )
        title = rec.get("title", "")
        if meaning:
            meanings.append((corpus, sid, meaning))
            if corpus in ("lean_workbook", "ingested_arithmetic"):
                templates_src.append(meaning)
        if title:
            titles.append(title)
        tmpl = (rec.get("structural_signature") or {}).get(
            "anonymized_template", ""
        )
        if tmpl:
            anon_templates[tmpl] += 1

WORD = re.compile(r"\S+")
all_texts = [m for _, _, m in meanings] + titles
docs_words = [WORD.findall(t) for t in all_texts]
total_words = sum(len(w) for w in docs_words)

# --- A) word n-gram census ------------------------------------------------
ngram_counts = {}
for n in range(2, 9):
    c = Counter()
    for words in docs_words:
        for i in range(len(words) - n + 1):
            c[tuple(words[i:i + n])] += 1
    ngram_counts[n] = c

census = {}
for n, c in ngram_counts.items():
    for floor in (32, 100, 500):
        census[f"n{n}_freq_ge_{floor}"] = sum(
            1 for v in c.values() if v >= floor
        )

# --- B) greedy block encoding --------------------------------------------
# Dictionary: every n-gram (2..8 words) with freq >= 32, plus all single
# words. Greedy longest-match left to right.
block_dict = set()
for n in range(8, 1, -1):
    for gram, v in ngram_counts[n].items():
        if v >= 32:
            block_dict.add(gram)

emitted = 0
covered_words_by_blocks = 0
for words in docs_words:
    i = 0
    L = len(words)
    while i < L:
        matched = False
        for n in range(min(8, L - i), 1, -1):
            if tuple(words[i:i + n]) in block_dict:
                emitted += 1
                covered_words_by_blocks += n
                i += n
                matched = True
                break
        if not matched:
            emitted += 1
            i += 1

# --- C) template mining over ingested prose -------------------------------
SLOT = re.compile(
    r"`[^`]*`|\$[^$]*\$|[A-Za-z0-9_^{}\\()+\-*/=<>,.! ]*[=<>^][^.;:]*"
)
NUMISH = re.compile(r"[0-9]+(\.[0-9]+)?")


def to_template(text: str) -> str:
    t = re.sub(r"`[^`]*`", "{S}", text)
    t = NUMISH.sub("{N}", t)
    # collapse formula-ish token runs: tokens containing =, ^, \, /, +
    words = t.split()
    out = []
    run = False
    for w in words:
        if any(ch in w for ch in "=^\\+*/<>|") or w in ("{N}", "{S}"):
            if not run:
                out.append("{F}")
                run = True
        else:
            out.append(w)
            run = False
    return " ".join(out)


tmpl_counter = Counter(to_template(m) for m in templates_src)
top_templates = tmpl_counter.most_common(12)
ingested_total = len(templates_src)
top10_cover = sum(v for _, v in tmpl_counter.most_common(10))

report = {
    "corpus": {
        "nodes_with_meaning": len(meanings),
        "titles": len(titles),
        "total_surface_words": total_words,
    },
    "ngram_census": census,
    "greedy_block_encoding": {
        "dictionary_blocks_freq_ge_32": len(block_dict),
        "tokens_emitted": emitted,
        "words_per_emitted_token": round(total_words / emitted, 3),
        "fraction_of_words_inside_multiword_blocks": round(
            covered_words_by_blocks / total_words, 4
        ),
    },
    "ingested_prose_templates": {
        "ingested_meanings": ingested_total,
        "distinct_templates": len(tmpl_counter),
        "top10_coverage": round(top10_cover / max(ingested_total, 1), 4),
        "top_templates": [
            {"count": v, "template": t[:160]} for t, v in top_templates
        ],
    },
    "formal_side_reuse": {
        "nodes_with_anonymized_template": sum(anon_templates.values()),
        "distinct_anonymized_templates": len(anon_templates),
        "top5_template_hosts": anon_templates.most_common(5)
        and [
            {"count": v, "template": t[:100]}
            for t, v in anon_templates.most_common(5)
        ],
    },
}

OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report["corpus"], indent=1))
print(json.dumps(report["greedy_block_encoding"], indent=1))
print(json.dumps({k: v for k, v in report["ingested_prose_templates"].items()
                  if k != "top_templates"}, indent=1))
print("top templates:")
for row in report["ingested_prose_templates"]["top_templates"][:6]:
    print(f"  {row['count']:>6}  {row['template'][:110]}")
print(json.dumps({k: v for k, v in report["formal_side_reuse"].items()
                  if k != "top5_template_hosts"}, indent=1))
print("census (blocks recurring >=100x):",
      {k: v for k, v in census.items() if "ge_100" in k})
