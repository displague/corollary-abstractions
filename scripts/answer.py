#!/usr/bin/env python3
"""Compose an answer about a statement — by quotation, never by generation.

The v0.13 goal is arbitrary text in, and out an answer that is intelligible,
factual, logical and grammatical. Three of those four are settled by refusing
to write the sentences here:

- **Grammatical** — every sentence in an answer is lifted verbatim from the
  committed corpus (`title`, `semantic_interpretation.statement_meaning`).
  A human wrote those sentences and a schema validates them. This module
  contributes labels, never prose.
- **Factual** — the sentences are attributed to the statement id they came
  from, so any claim can be checked against `data/`. Nothing is paraphrased,
  because paraphrase is where a claim quietly changes.
- **Logical** — relations come from `inferential_links`, which are edges the
  corpus asserts and `validate_nodes.py` checks for reciprocity. Following an
  edge is deduction over committed data, not inference invented here.

**Intelligible** is the one this module actually works for: ordering the
material the way a reference entry does — what it is, what it says, how it is
written formally, what it is connected to, and how strongly it is held.

## The honesty this has to carry

12,514 of 12,777 nodes are ingested, and their `statement_meaning` is
machine-authored boilerplate ("The covered Lean-workbook claim stated by
problem X, emitted as a matcher template"). Quoting that is honest but it is
*provenance*, not mathematics. `Answer.prose_is_authored` records which kind
of node was quoted so a caller can tell the difference, and the rendered
answer says so in one line rather than letting a reader assume a person
wrote it.

Only 1.8% of nodes carry `inferential_links`. An answer about the other 98%
has no relations to show, and says nothing rather than implying isolation is
a finding.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

#: Corpora authored mechanically in bulk. Their prose is a provenance
#: sentence, not an explanation, and an answer must not pass it off as one.
#: Read from `decompose` so there is one registry, not two.
try:
    from decompose import INGESTED_CORPUS_PREFIXES
except ImportError:  # pragma: no cover - CLI import shim
    INGESTED_CORPUS_PREFIXES = ("lean_workbook", "ingested_arithmetic")

LINK_PHRASING = {
    "entails": "entails",
    "entailed_by": "is entailed by",
    "equivalent_to": "is equivalent to",
    "special_case_of": "is a special case of",
    "generalizes": "generalizes",
    "composed_with": "composes with",
}


@dataclass(frozen=True)
class Answer:
    statement_id: str
    corpus: str
    title: str
    meaning: str
    formal: str
    status: str
    disciplines: tuple[str, ...]
    links: tuple[tuple[str, str], ...]
    verified_by: tuple[str, ...]
    prose_is_authored: bool

    @property
    def sources(self) -> tuple[str, ...]:
        """Every id this answer quotes or cites. Nothing else is claimed."""
        return (self.statement_id,) + tuple(sid for _kind, sid in self.links)


@lru_cache(maxsize=1)
def _corpus_records(roots: tuple[str, ...]) -> dict[str, tuple[dict, str]]:
    """statement_id -> (node json, corpus_id). Read once, reused."""
    out: dict[str, tuple[dict, str]] = {}
    for root in roots:
        base = Path(root)
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*/nodes.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            corpus = doc.get("corpus_id", path.parent.name)
            for node in doc.get("statement_nodes", []):
                sid = node.get("statement_id")
                if isinstance(sid, str):
                    out[sid] = (node, corpus)
    return out


def records(roots: list[Path] | None = None) -> dict[str, tuple[dict, str]]:
    paths = roots or [REPO / "data", REPO / "data_holdout"]
    return _corpus_records(tuple(str(p) for p in paths))


def compose(statement_id: str, roots: list[Path] | None = None) -> Answer | None:
    """Assemble the answer for one statement from its committed fields."""
    found = records(roots).get(statement_id)
    if found is None:
        return None
    node, corpus = found
    semantic = node.get("semantic_interpretation") or {}
    theory = node.get("theory_context") or {}
    formal = node.get("formal_statement") or {}
    links: list[tuple[str, str]] = []
    for kind, targets in (node.get("inferential_links") or {}).items():
        for target in targets or []:
            if isinstance(target, str):
                links.append((kind, target))
            elif isinstance(target, dict) and isinstance(
                target.get("statement_id"), str
            ):
                links.append((kind, target["statement_id"]))
    verified = tuple(
        link.get("artifact", "")
        for link in (node.get("verified_by") or [])
        if isinstance(link, dict)
    )
    return Answer(
        statement_id=statement_id,
        corpus=corpus,
        title=str(node.get("title", "")),
        meaning=str(semantic.get("statement_meaning", "")),
        formal=str(formal.get("canonical_ascii", "")),
        status=str(node.get("epistemic_status", "")),
        disciplines=tuple(theory.get("disciplines") or ()),
        links=tuple(sorted(links)),
        verified_by=verified,
        prose_is_authored=not corpus.startswith(tuple(INGESTED_CORPUS_PREFIXES)),
    )


@lru_cache(maxsize=1)
def _realization_lexicon():
    """The committed realization table, read once per process, or None.

    Read once because `realization_lexicon.load` re-reads and re-gates the
    file on every call (~0.7 ms warm against the ~0.1 ms a realization
    costs), and this renderer runs per answer. The table is a committed
    artifact, so a process treats it as static for its lifetime — the same
    assumption every other committed-artifact read here makes.

    A table that will not load returns None rather than raising: an absent
    or invalid lexicon is an absent capability, and `in words` is then
    simply not emitted (R3). A reference entry that has always rendered must
    not start crashing because an optional surface lost its table.
    """

    try:
        from realization_lexicon import load  # noqa: PLC0415

        return load()
    except (ImportError, OSError, ValueError):
        return None


def _in_words(formal: str, statement_id: str) -> str | None:
    """The English surface for one canonical term, or None (R3).

    R3 is refusal *at the surface*: a term that does not parse, a term whose
    operator head has no lexicon row, and a sentence whose re-parse does not
    canonicalize back to the source skeleton all produce **no line at all** —
    not an error string, not a placeholder, not a hedge. Absence is the
    refusal. Anyone who wants the reason calls `realize_term.realize`
    directly and reads the receipt it returns; a reference entry is not the
    place to explain why a sentence the reader never saw was not written.

    The gate is `Realization.served`, which is `round_trip == "EXACT"` and
    nothing looser. `Refusal` exposes the same property as False, so this
    function branches on one attribute rather than on which type came back.
    """

    lexicon = _realization_lexicon()
    if not formal or lexicon is None:
        return None
    from realize_term import realize  # noqa: PLC0415

    # `realize` is documented never to raise on corpus input; it returns a
    # Refusal instead. Trusting that contract keeps the refusal path here a
    # single readable branch rather than an except block that would also
    # swallow a real bug.
    result = realize(formal, lexicon, statement_id)
    return result.surface if result.served else None


def render(answer: Answer, *, links: bool = True) -> list[str]:
    """A reference entry. Labels are mine; every sentence is the corpus's."""
    out: list[str] = []
    if answer.title:
        out.append(answer.title)
    if answer.meaning:
        out.append("")
        out.append(answer.meaning)
    if answer.formal:
        out.append("")
        out.append(f"formally   : {answer.formal}")
        # Immediately under the term it realizes, because that is what it
        # is: the same statement, read aloud. Emitted only behind the
        # round-trip gate (R3); see `_in_words`.
        surface = _in_words(answer.formal, answer.statement_id)
        if surface is not None:
            out.append(f"in words   : {surface}")
    if answer.status:
        out.append(f"held as    : {answer.status}")
    if answer.disciplines:
        out.append(f"discipline : {', '.join(answer.disciplines)}")
    out.append(f"source     : {answer.statement_id}  [{answer.corpus}]")
    if answer.verified_by:
        out.append(f"checked by : {', '.join(a for a in answer.verified_by if a)}")
    if not answer.prose_is_authored:
        # Said plainly rather than left for the reader to discover: the
        # sentence above describes where this node came from, not what the
        # mathematics means.
        out.append(
            "note       : this text is an ingestion record, not an "
            "explanation a person wrote"
        )
    if links and answer.links:
        out.append("")
        out.append("connected to:")
        for kind, target in answer.links:
            phrase = LINK_PHRASING.get(kind, kind)
            out.append(f"  {phrase} {target}")
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("statement_id")
    args = ap.parse_args(argv)
    answer = compose(args.statement_id)
    if answer is None:
        print(f"no such statement: {args.statement_id}", file=sys.stderr)
        return 1
    print("\n".join(render(answer)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
