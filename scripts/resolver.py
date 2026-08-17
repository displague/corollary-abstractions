#!/usr/bin/env python3
"""Free text -> graph node, by resolution rather than generation.

The lineage is A.L.I.C.E./AIML, minus the part that does not fit here. AIML
contributed three ideas worth keeping and one worth refusing:

- **Graphmaster** — patterns in a trie, matched in priority order. Here the
  index is over the *statement graph* rather than over authored patterns,
  and it is built from committed data, not hand-written.
- **`<srai>`** (symbolic reduction) — many surface forms collapse to one
  canonical form. Kept, and pointed somewhere new: reduction produces a
  canonical **query**, not a canned reply.
- **`<that>` / `<topic>`** — context narrows ambiguity. Kept in shape; the
  multi-turn half is deliberately absent while P-LS6 is parked.
- **`<template>`** — canned response text. **Refused.** Every answer here is
  rendered from graph data (ids, counts, corpora). Nothing is authored
  prose, so nothing can claim more than the graph knows.

## Resolve, do not generate

A resolver is a total function from text to one of three outcomes:

- **BIND** — exactly one candidate. The answer is exact.
- **ASK** — several candidates, and it *names them*. Ambiguity becomes a
  question containing the real alternatives, never a guess.
- **PASS** — this resolver has nothing to say; try the next.

Nothing infers, completes, or invents. Where a ranker would go — choosing
among candidates when the query cannot — the system asks instead. That seat
is left explicitly empty; it is the first honestly-graded leftover this
project has produced, and it is not filled by guessing.

## Cost, because this is meant to run on small hardware

Measured on the 12,777-node graph: `load_trees` 1.47 s, index build 2.51 s,
**lookup 0.04 us (~24M/sec)**. All the cost is cold start, which is why the
index is built once and cached rather than recomputed per query. There is no
model to load and no token loop to run: answering is a dict lookup and a
render, so the working set is the index, not a weight matrix.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from decompose import load_trees, subterms  # noqa: E402
from match_signatures import (  # noqa: E402
    Parser,
    TemplateParseError,
    canonicalize,
    skeleton,
    template_slots,
    tokenize,
)

BIND, ASK, PASS = "bind", "ask", "pass"

#: A keyword on more than this share of nodes carries no discriminating
#: information. `ingested` sits on 12,525 of 12,777 nodes; matching it would
#: "resolve" a query to the whole corpus. Document-frequency reasoning,
#: computed from the corpus rather than tuned against an answer key.
KEYWORD_DF_CEILING = 0.20

#: A match must account for at least this share of the query's content
#: words. Below it, most of what the person typed went unexplained, and the
#: part that matched is coincidence. Set at "most of the query", not tuned
#: to a score.
COVERAGE_FLOOR = 0.60

#: At most this many content words still counts as a TERM query, where
#: matching every word is enough on its own. Above it the text is a
#: sentence, and a sentence has to corroborate rather than lean on one
#: surviving word.
TERM_QUERY_WORDS = 2

#: How many content words the corpus has NEVER SEEN, anywhere, before the
#: query is judged to be about something else entirely.
#:
#: This is a different signal from coverage, and it uses information the
#: coverage rule discards. A word can go unmatched for two very different
#: reasons: it is too common to discriminate (`value`, `sum`), or the corpus
#: has no record of it at all (`war`, `piano`, `lisbon`). The second is
#: evidence about DOMAIN, not about phrasing.
#:
#: Measured across every query available: in-corpus questions carry zero or
#: one unknown word — one being a morphology or synonym gap, like
#: `derivatives` against a corpus that writes `derivative`. Out-of-corpus
#: questions carry two or more, because their subject matter is simply
#: absent. Two independent unknown content words is the corpus saying it
#: does not cover this, and that outweighs any number of ordinary words
#: that happen to overlap.
UNKNOWN_WORD_LIMIT = 2

#: Dropped before keyword matching. Deliberately tiny and closed: this is not
#: language understanding, it is removing tokens that match everything.
STOPWORDS = frozenset("""
a an the is are was were be been being of in on at to for from by with
what which who whom whose that this these those and or not do does did
how why where when whether

show tell find give me my we our you your it its
into onto over under about above below between through during before after
as if then than so but nor yet also very much many some any each every
have has had will would can could should may might must shall
""".split())

_WORD = re.compile(r"[a-z0-9_]+")


@dataclass(frozen=True)
class Resolution:
    """One resolver's disposition. `kind` is BIND, ASK, or PASS."""

    kind: str
    resolver: str
    candidates: tuple[str, ...] = ()
    detail: str = ""
    evidence: tuple[str, ...] = ()

    @property
    def bound(self) -> str | None:
        return self.candidates[0] if self.kind == BIND else None


@dataclass
class GraphIndex:
    """Everything the resolvers read. Built once, cached, then reused."""

    statement_ids: tuple[str, ...] = ()
    corpus_of: dict[str, str] = field(default_factory=dict)
    by_skeleton: dict[str, tuple[str, ...]] = field(default_factory=dict)
    by_keyword: dict[str, tuple[str, ...]] = field(default_factory=dict)
    keyword_df: dict[str, int] = field(default_factory=dict)
    #: Inverted index over each node's AUTHORED PROSE -- its title and its
    #: `statement_meaning`. This is what lets arbitrary text find a node at
    #: all: keywords are a curator's short list, prose is what a person
    #: actually types. Saturating words are excluded by the same
    #: document-frequency ceiling, which matters more here than for keywords
    #: because 12,514 ingested nodes share a formulaic meaning sentence.
    by_prose: dict[str, tuple[str, ...]] = field(default_factory=dict)
    prose_df: dict[str, int] = field(default_factory=dict)
    #: Inverted index over `symbol_lexicon` names and descriptions -- the
    #: corpus's own glossary. This is where a node says that `GCD(a, b)` is
    #: called "greatest common divisor", so it is the synonym layer the
    #: corpus already carried and nobody was reading. Every node has one.
    by_lexicon: dict[str, tuple[str, ...]] = field(default_factory=dict)
    lexicon_df: dict[str, int] = field(default_factory=dict)
    #: Whole-statement skeletons. `by_skeleton` indexes SUBTERMS, because
    #: `decompose.subterms` yields a relation's sides and never the relation
    #: itself -- so typing a complete statement (`12 * 3 + 4 * 5 = 56`)
    #: matched nothing at all. That is how 2,728 ground arithmetic nodes came
    #: out unreachable: not because they lack a name, but because the only
    #: query that fits them was the one shape the resolver refused.
    by_statement: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @property
    def size(self) -> int:
        return len(self.statement_ids)


def build_index(data_dirs: list[Path]) -> GraphIndex:
    """One pass over the committed corpora. No network, no model, no state."""
    ids: list[str] = []
    corpus_of: dict[str, str] = {}
    by_skeleton: dict[str, list[str]] = defaultdict(list)
    by_keyword: dict[str, list[str]] = defaultdict(list)
    df: Counter = Counter()
    by_prose: dict[str, list[str]] = defaultdict(list)
    prose_df: Counter = Counter()
    by_lexicon: dict[str, list[str]] = defaultdict(list)
    lexicon_df: Counter = Counter()
    by_statement: dict[str, list[str]] = defaultdict(list)

    for data_dir in data_dirs:
        if not data_dir.is_dir():
            continue
        nodes, trees, classes, corpus_map, _disc = load_trees(data_dir)
        for node in nodes:
            sid = node.statement_id
            ids.append(sid)
            corpus_of[sid] = corpus_map.get(sid, "?")
            tree = trees.get(sid)
            if tree is not None:
                seen: set[str] = set()
                for _path, sub in subterms(tree):
                    key = skeleton(sub, classes[sid])
                    if key not in seen:
                        seen.add(key)
                        by_skeleton[key].append(sid)
                try:
                    by_statement[skeleton(tree, classes[sid])].append(sid)
                except (KeyError, TypeError, ValueError):
                    pass
        # Keywords live on the corpus JSON, which `load_trees` does not carry.
        for path in sorted(data_dir.glob("*/nodes.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            for raw in doc.get("statement_nodes", []):
                sid = raw.get("statement_id")
                if not isinstance(sid, str):
                    continue
                words: set[str] = set()
                for kw in raw.get("keywords") or []:
                    if isinstance(kw, str):
                        words.update(_WORD.findall(kw.lower()))
                for word in words - STOPWORDS:
                    by_keyword[word].append(sid)
                    df[word] += 1
                prose_words: set[str] = set()
                for text in (
                    raw.get("title"),
                    (raw.get("semantic_interpretation") or {}).get(
                        "statement_meaning"
                    ),
                ):
                    if isinstance(text, str):
                        prose_words.update(_WORD.findall(text.lower()))
                for word in prose_words - STOPWORDS:
                    by_prose[word].append(sid)
                    prose_df[word] += 1
                lex = raw.get("symbol_lexicon") or {}
                lex_words: set[str] = set()
                for group in ("symbols", "operators", "functionals",
                              "constants", "index_sets"):
                    for entry in lex.get(group) or []:
                        if not isinstance(entry, dict):
                            continue
                        for key in ("name", "description", "semantic_role"):
                            value = entry.get(key)
                            if isinstance(value, str):
                                lex_words.update(_WORD.findall(value.lower()))
                for word in lex_words - STOPWORDS:
                    by_lexicon[word].append(sid)
                    lexicon_df[word] += 1

    return GraphIndex(
        statement_ids=tuple(ids),
        corpus_of=corpus_of,
        by_skeleton={k: tuple(v) for k, v in by_skeleton.items()},
        by_keyword={k: tuple(v) for k, v in by_keyword.items()},
        keyword_df=dict(df),
        by_prose={k: tuple(v) for k, v in by_prose.items()},
        prose_df=dict(prose_df),
        by_lexicon={k: tuple(v) for k, v in by_lexicon.items()},
        lexicon_df=dict(lexicon_df),
        by_statement={k: tuple(v) for k, v in by_statement.items()},
    )


# --------------------------------------------------------------------------
# reduction (the `<srai>` idea, pointed at a query instead of a reply)
# --------------------------------------------------------------------------


def reduce_text(text: str) -> list[str]:
    """Surface form -> content words. Lowercase, split, drop match-alls.

    Bare numerals are dropped. `prove that 2 + 2 = 4` reduced to
    ['prove','2','2','4'] and the digits matched prose all over the corpus,
    binding a proof request to the quadratic formula. Numbers carry
    structure, not topic, and the expression resolver already reads them
    structurally — which is the right place for them.
    """
    return [
        w for w in _WORD.findall(text.lower())
        if w not in STOPWORDS and not w.isdigit()
    ]


# --------------------------------------------------------------------------
# resolvers
# --------------------------------------------------------------------------


def resolve_expression(text: str, index: GraphIndex) -> Resolution:
    """R1 — the text parses as a template expression: exact subterm lookup."""
    try:
        tree = canonicalize(Parser(tokenize(text)).parse())
    except (TemplateParseError, ValueError, IndexError):
        return Resolution(PASS, "expression", detail="not a template expression")
    classes = {n: "V" for n in template_slots(tree)}
    if tree[0] == "rel":
        # A whole typed statement. Match it against whole-statement
        # skeletons, which is the same equivalence the matcher calls a twin:
        # `12 * 3 + 4 * 5 = 56` should find that statement, and anything
        # structurally identical to it.
        key = skeleton(tree, classes)
        hosts = index.by_statement.get(key, ())
        if not hosts:
            return Resolution(
                PASS, "statement", detail=f"no statement has the skeleton {key}"
            )
        return Resolution(
            BIND if len(hosts) == 1 else ASK,
            "statement",
            candidates=hosts,
            detail=f"{len(hosts)} statements have this exact structure",
            evidence=(f"skeleton={key}",),
        )
    if tree[0] not in {"op", "call"}:
        return Resolution(PASS, "expression", detail="not a compound term")
    key = skeleton(tree, classes)
    hosts = index.by_skeleton.get(key, ())
    if not hosts:
        return Resolution(PASS, "expression", detail=f"no statement hosts {key}")
    return Resolution(
        BIND if len(hosts) == 1 else ASK,
        "expression",
        candidates=hosts,
        detail=f"{len(hosts)} statements host {key}",
        evidence=(f"skeleton={key}",),
    )


def resolve_statement_id(text: str, index: GraphIndex) -> Resolution:
    """R2 — the text names a statement id, whole or by unique suffix."""
    probe = text.strip()
    if probe in index.corpus_of:
        return Resolution(BIND, "statement_id", (probe,), "exact statement id")
    if "." not in probe or " " in probe:
        return Resolution(PASS, "statement_id", detail="not an id")
    hits = tuple(s for s in index.statement_ids if s.endswith(probe))
    if not hits:
        return Resolution(PASS, "statement_id", detail="no id ends with that")
    return Resolution(
        BIND if len(hits) == 1 else ASK,
        "statement_id",
        hits,
        f"{len(hits)} ids end with {probe!r}",
    )


def resolve_keywords(text: str, index: GraphIndex) -> Resolution:
    """R3 — content words intersected against the corpus keyword index.

    Only keywords below the document-frequency ceiling participate: a word on
    most nodes cannot discriminate, and matching it would "resolve" a query to
    the entire corpus. Candidates are scored by how many query words they
    match, and ties are NOT broken -- a tie is an ASK.
    """
    return _postings_resolver(
        text, index, index.by_keyword, index.keyword_df, "keywords"
    )


def _postings_resolver(
    text: str,
    index: GraphIndex,
    postings: dict[str, tuple[str, ...]],
    doc_freq: dict[str, int],
    name: str,
) -> Resolution:
    """Shared body for the two inverted-index resolvers.

    Factored so the corroboration rule exists once. It is the rule that
    stops fluent nonsense from being claimed, and a second copy of it would
    be a second place for it to rot.
    """
    words = reduce_text(text)
    if not words:
        return Resolution(PASS, name, detail="no content words")
    ceiling = max(1, int(index.size * KEYWORD_DF_CEILING))
    hits: Counter = Counter()
    used: list[str] = []
    for word in words:
        found = postings.get(word)
        if not found or doc_freq.get(word, 0) > ceiling:
            continue
        used.append(word)
        for sid in found:
            hits[sid] += 1
    if not hits:
        return Resolution(
            PASS, name, detail=f"no discriminating word matched {words}"
        )
    best = max(hits.values())
    # Corroboration, not enthusiasm. One stray word out of many is not a
    # resolution: "airspeed velocity of an unladen swallow" hits `velocity`
    # and would otherwise "resolve" to unrelated statements, which is
    # precisely the fluent-nonsense failure the dispatcher exists to refuse.
    # Two conditions, and the second was earned. Corroboration alone let
    # "translate this sentence into portuguese" bind to a logic node on
    # ['into', 'sentence'] -- two words agreeing, both weak, covering half
    # the query. So a match must also ACCOUNT FOR most of what was asked:
    # if half the query is unexplained, the half that matched is a
    # coincidence, not a resolution.
    covered = len(used) / len(words)
    if not ((best >= 2 and covered >= COVERAGE_FLOOR) or len(used) == len(words)):
        return Resolution(
            PASS, name,
            detail=(
                f"{used} matched but that is only {covered:.0%} of {words}; "
                "a partial match is not a resolution"
            ),
        )
    top = tuple(sorted(s for s, n in hits.items() if n == best))
    return Resolution(
        BIND if len(top) == 1 else ASK,
        name,
        top,
        f"{len(top)} statements match {used} ({best} of {len(used)})",
        evidence=(f"matched_words={used}",),
    )


def resolve_lexicon(text: str, index: GraphIndex) -> Resolution:
    """R4 — the corpus's own glossary of symbol and operator names.

    This is the synonym layer, and it was already committed: a node that
    writes `GCD(a, b)` records in `symbol_lexicon.functionals` that the
    functional is called "greatest common divisor". A person types the name;
    the corpus supplies the mapping. No synonym table is authored here,
    because authoring one would be guessing at what the corpus means.
    """
    return _postings_resolver(
        text, index, index.by_lexicon, index.lexicon_df, "lexicon"
    )


def resolve_prose(text: str, index: GraphIndex) -> Resolution:
    """R4 — the node's own authored title and meaning, word-indexed.

    This is what makes *arbitrary* text resolvable rather than only curated
    keywords: a person types the words a mathematician would write, and the
    corpus already contains those words in prose a human authored.
    """
    return _postings_resolver(
        text, index, index.by_prose, index.prose_df, "prose"
    )


def resolve_words(text: str, index: GraphIndex) -> Resolution:
    """R3-5 pooled: keywords, glossary and prose scored TOGETHER.

    These were three resolvers in a priority chain, and the corpus-scale
    sweep showed the ordering was an assumption that cost accuracy. A node's
    own title is not in the keyword index -- keywords are a curator's
    separate short list -- so `Pythagorean Theorem` matched another node's
    keywords before reaching the prose index where its own title lives, and
    bound confidently to the wrong statement.

    First-resolver-wins discards evidence. Pooling asks the better question:
    which statement does the MOST of what was typed point at, counting every
    place the corpus records a name for something. A node matching in two
    indexes outranks one matching in a single index, which is corroboration
    applied across sources rather than only across words.

    Exact resolvers still run first and are never pooled: a parsed
    expression or a literal id is a different kind of evidence, not more of
    the same kind.
    """
    words = reduce_text(text)
    if not words:
        return Resolution(PASS, "words", detail="no content words")
    sources = (
        (index.by_keyword, index.keyword_df, "keywords"),
        (index.by_lexicon, index.lexicon_df, "lexicon"),
        (index.by_prose, index.prose_df, "prose"),
    )
    ceiling = max(1, int(index.size * KEYWORD_DF_CEILING))
    hits: Counter = Counter()
    matched_words: set[str] = set()
    seen_anywhere: set[str] = set()
    where: set[str] = set()
    for postings, doc_freq, label in sources:
        for word in words:
            found = postings.get(word)
            if not found:
                continue
            # Present in the corpus, even if too common to discriminate.
            # That distinction is the whole point of the domain check below.
            seen_anywhere.add(word)
            if doc_freq.get(word, 0) > ceiling:
                continue
            matched_words.add(word)
            where.add(label)
            for sid in found:
                hits[sid] += 1

    # The domain check, before any scoring. Words the corpus has never
    # recorded are evidence about SUBJECT MATTER, and enough of them means
    # the question is about something this graph does not contain -- however
    # many ordinary words happen to overlap. "what were the main causes of
    # the second world war" matches three words and is still a history
    # question, because `war` and `main` appear nowhere in the corpus.
    unknown = sorted(set(words) - seen_anywhere)
    if len(unknown) >= UNKNOWN_WORD_LIMIT:
        return Resolution(
            PASS, "words",
            detail=(
                f"{unknown} appear nowhere in the corpus; this question is "
                "about something the graph does not cover"
            ),
            evidence=(f"unknown_words={unknown}",),
        )
    if not hits:
        return Resolution(
            PASS, "words", detail=f"no discriminating word matched {words}"
        )
    used = sorted(matched_words)
    covered = len(used) / len(words)
    best = max(hits.values())
    # The "absorbed whole" shortcut is for TERM queries -- someone typing
    # `parity` means the term. It is not for sentences: `prove that 2 + 2 = 4`
    # reduces to one weak content word, and letting one word stand for a whole
    # sentence is how a proof request became an answer about the quadratic
    # formula. A sentence must corroborate.
    absorbed = len(used) == len(words) and len(words) <= TERM_QUERY_WORDS
    if not ((best >= 2 and covered >= COVERAGE_FLOOR) or absorbed):
        return Resolution(
            PASS, "words",
            detail=(
                f"{used} matched but that is only {covered:.0%} of {words}; "
                "a partial match is not a resolution"
            ),
        )
    top = tuple(sorted(s for s, n in hits.items() if n == best))
    return Resolution(
        BIND if len(top) == 1 else ASK,
        "words",
        top,
        f"{len(top)} statements match {used} (score {best}, via {sorted(where)})",
        evidence=(f"matched_words={used}", f"indexes={sorted(where)}"),
    )


#: Exact evidence first, then pooled word evidence. An expression that parses
#: or an id that resolves is never second-guessed by word overlap.
CHAIN = (
    resolve_expression,
    resolve_statement_id,
    resolve_words,
)


def resolve(text: str, index: GraphIndex, *, chain=CHAIN) -> Resolution:
    """Run the chain. First resolver to BIND or ASK wins; PASS falls through."""
    tried: list[str] = []
    for resolver in chain:
        outcome = resolver(text, index)
        tried.append(f"{outcome.resolver}:{outcome.kind}")
        if outcome.kind != PASS:
            return Resolution(
                outcome.kind, outcome.resolver, outcome.candidates,
                outcome.detail, outcome.evidence + (f"tried={tried}",),
            )
    return Resolution(
        PASS, "chain", detail="no resolver claimed this text",
        evidence=(f"tried={tried}",),
    )


def render(outcome: Resolution, index: GraphIndex, *, sample: int = 6) -> list[str]:
    """The answer, assembled from graph facts. No authored prose."""
    if outcome.kind == PASS:
        return [f"unresolved: {outcome.detail}"]
    lines = [f"resolver : {outcome.resolver}", f"detail   : {outcome.detail}"]
    if outcome.kind == BIND:
        sid = outcome.candidates[0]
        lines.append(f"bound    : {sid}")
        lines.append(f"corpus   : {index.corpus_of.get(sid, '?')}")
        return lines
    lines.append(f"ambiguous: {len(outcome.candidates)} candidates")
    for sid in outcome.candidates[:sample]:
        lines.append(f"  ? {sid}  [{index.corpus_of.get(sid, '?')}]")
    if len(outcome.candidates) > sample:
        lines.append(f"  ... {len(outcome.candidates) - sample} more")
    lines.append("name one of them, or narrow the query")
    return lines


def default_index() -> GraphIndex:
    return build_index([REPO / "data", REPO / "data_holdout"])


def main(argv: list[str] | None = None) -> int:
    import argparse
    import time

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("text", nargs="+", help="text to resolve")
    ap.add_argument("--timing", action="store_true")
    args = ap.parse_args(argv)

    t0 = time.perf_counter()
    index = default_index()
    t1 = time.perf_counter()
    outcome = resolve(" ".join(args.text), index)
    t2 = time.perf_counter()
    print("\n".join(render(outcome, index)))
    if args.timing:
        print(f"\nindex {t1 - t0:.2f}s over {index.size} nodes; "
              f"resolve {(t2 - t1) * 1e6:.0f}us")
    return 0 if outcome.kind != PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
