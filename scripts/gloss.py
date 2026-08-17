#!/usr/bin/env python3
"""Plain human-readable definitions, quoted from Open English WordNet.

The corpus can answer "what is the cosine of a double angle" in a sentence a
person wrote, because a person wrote that sentence and a schema checks it.
It cannot answer "what is a chicken", and until now nothing could: the
options were a template I author (refused) or a model that generates
(refused).

WordNet is the third option, and it is the same option as the corpus —
**quotation**. Open English WordNet ships roughly 120,000 lemmas with
human-written glosses and examples. Reading one out is not generation and not
a template; it is a dictionary lookup with attribution, which is exactly the
"accuracy of a dictionary and reference systems" this project is aiming at.

## What this does and does not license

- Every sentence printed is a WordNet gloss or example, verbatim, with the
  synset id and archive digest available as provenance. Nothing is
  paraphrased, because paraphrase is where a claim changes.
- A definition is **not** a corpus statement. It is not `formal`, it is not
  `derived`, and it never enters the graph. `answer.py` speaks for the graph;
  this module speaks for the dictionary, and the two are printed under
  different labels on purpose.
- Ambiguity is not resolved. `spring` has many senses and the honest output
  is all of them, labelled by part of speech, not a guess at which one was
  meant.

## Why it is gated on the boot matrix

The archive is gitignored and located by `COROLLARY_WORDNET`. On a machine
without it the route must be OFF rather than silently empty — the same rule
every optional subsystem follows, and the trap v0.11's WOLD ledger fell into
when a missing archive produced a quiet wrong answer instead of a refusal.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from wordnet_store import WordNetIndex, lemma_key  # noqa: E402

#: The boot-matrix subsystem this is a capability of.
REQUIRES_SUBSYSTEM = "retrieve.wordnet"

#: How many senses to print before saying how many were left.
SENSE_CAP = 4

#: The question forms a dictionary can answer, and the word each one asks
#: about. This is a registered question shape, like `owns` and `suppose` --
#: not comprehension. It exists because the first version fired on any line
#: containing a dictionary word, which is nearly every line: "tell me a
#: story about a chicken" was answered by DEFINING chicken. A definition is
#: only an answer when a definition was asked for; otherwise abstaining is
#: the more useful reply.
DEFINITIONAL = re.compile(
    r"\b(?:what\s+(?:is|are|was|were)|what's|define|definition\s+of|"
    r"meaning\s+of|what\s+does)\s+"
    r"(?:an?|the)?\s*([a-zA-Z][a-zA-Z0-9_'-]*)",
    re.IGNORECASE,
)

#: The inverted form: "explain what an egg is", "tell me what a proof is".
#: English puts the subject before the verb here, and a pattern written only
#: for "what is X" silently misses it.
DEFINITIONAL_INVERTED = re.compile(
    r"\bwhat\s+(?:an?|the)\s+([a-zA-Z][a-zA-Z0-9_'-]*)\s+(?:is|are|was|were)\b",
    re.IGNORECASE,
)


#: Words that may trail a definition request without making it a question
#: about something else. Anything outside this set means the person asked
#: about a compound thing, not about a word.
_TRAILING_OK = frozenset(
    "a an the is are was were of in on to for from by with and or "
    "please then really actually exactly mean means".split()
)

_TOKEN = re.compile(r"[a-zA-Z][a-zA-Z0-9_'-]*")


def definitional_target(text: str) -> str | None:
    """The word a definitional question asks about, or `None`.

    Returns the word from the QUESTION rather than the longest word in the
    line: "explain what an egg is from the perspective of a bird" is asking
    about the egg, not the perspective.

    The forward form additionally requires the question to END at that word.
    "what is a telescope" asks what a word means; "what is the capital city
    of australia" asks a fact about a compound noun phrase, and answering it
    with the dictionary sense of `capital` is a non-answer that the holdout
    caught. The inverted form needs no such check because `is` already
    bounds the target on the right.
    """
    inverted = DEFINITIONAL_INVERTED.search(text)
    if inverted:
        return inverted.group(1).lower()
    forward = DEFINITIONAL.search(text)
    if not forward:
        return None
    rest = text[forward.end():]
    if any(
        token.lower() not in _TRAILING_OK for token in _TOKEN.findall(rest)
    ):
        return None
    return forward.group(1).lower()


@dataclass(frozen=True)
class Sense:
    synset_id: str
    part_of_speech: str
    definitions: tuple[str, ...]
    examples: tuple[str, ...]
    members: tuple[str, ...]


@dataclass(frozen=True)
class Gloss:
    word: str
    senses: tuple[Sense, ...]
    archive: str
    archive_sha256: str

    @property
    def found(self) -> bool:
        return bool(self.senses)


def archive_path() -> Path | None:
    raw = os.environ.get("COROLLARY_WORDNET")
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_file() else None


@lru_cache(maxsize=2)
def _index(archive: str) -> WordNetIndex:
    return WordNetIndex.load(Path(archive))


def look_up(word: str, archive: Path | None = None) -> Gloss | None:
    """Every sense WordNet records for `word`. `None` if no archive."""
    located = archive or archive_path()
    if located is None:
        return None
    index = _index(str(located))
    key = lemma_key(word)
    senses: list[Sense] = []
    for synset_id in index.lemma_synsets.get(key, ()):  # type: ignore[union-attr]
        synset = index.synsets.get(synset_id)
        if synset is None:
            continue
        senses.append(
            Sense(
                synset_id=synset.synset_id,
                part_of_speech=synset.part_of_speech,
                definitions=synset.definitions,
                examples=synset.examples,
                members=synset.members,
            )
        )
    return Gloss(
        word=word,
        senses=tuple(senses),
        archive=located.name,
        archive_sha256=index.archive_sha256,
    )


def render(gloss: Gloss) -> list[str]:
    """The senses, quoted. Labels are mine; every sentence is WordNet's."""
    if not gloss.found:
        return [f"no dictionary entry for {gloss.word!r}"]
    out = [f"{gloss.word} — {len(gloss.senses)} sense(s) in {gloss.archive}"]
    for sense in gloss.senses[:SENSE_CAP]:
        out.append("")
        out.append(f"  ({sense.part_of_speech}) {sense.synset_id}")
        for definition in sense.definitions:
            out.append(f"    {definition}")
        for example in sense.examples[:1]:
            out.append(f"    e.g. {example}")
        others = [m for m in sense.members if lemma_key(m) != lemma_key(gloss.word)]
        if others:
            out.append(f"    also: {', '.join(others[:6])}")
    if len(gloss.senses) > SENSE_CAP:
        out.append("")
        out.append(f"  ... {len(gloss.senses) - SENSE_CAP} more senses")
    out.append("")
    out.append(
        "quoted from Open English WordNet; a dictionary sense, not a "
        "statement in this corpus"
    )
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("word")
    args = ap.parse_args(argv)
    gloss = look_up(args.word)
    if gloss is None:
        print(
            "no WordNet archive; set COROLLARY_WORDNET to the pinned zip",
            file=sys.stderr,
        )
        return 2
    print("\n".join(render(gloss)))
    return 0 if gloss.found else 1


if __name__ == "__main__":
    raise SystemExit(main())
