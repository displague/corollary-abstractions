#!/usr/bin/env python3
"""The finite candidate list a proposer selects from. Exact code, no model.

`experiments/plain_input_prereg.json` answers DESIGN-plain-input §4's
Phase-2 question by registering a trust shape stronger than the one the
design argued for: **the proposer never emits a query string.** This module
is the half that makes that possible — it enumerates a finite list of
registered-grammar lines from committed material, and the model's entire
output alphabet is an index into that list plus the token NONE.

## Why the design's own argument needed replacing

§4 defends Phase 2 by saying the bound is on the output alphabet, because
"A candidate is a string that route_line already accepts". Slice 1's P1
measured that alphabet: **nine of fifteen template classes admit countably
infinite languages**, and two of those nine are where plain prose lands.
"route_line accepts it" is a parse check, not membership in a finite set. So
a proposer free to emit accepted strings has an unbounded output alphabet
and Phase 2 would be false. Selection from an enumerated list makes it true
by construction — and it is the doctrine's own words read literally: the
residual "ranks labels of candidates, it does not invent candidates from
ℝ^d prose space" (DESIGN-language-as-structure:465-466).

## The holdout rule, and why it is a rule rather than a habit

**This module reads `data/` and never `data_holdout/`.** Slice 1's review
measured why that has to be explicit: `resolver.default_index` builds over
BOTH directories, so **2,053 holdout statement ids sit inside the resolver's
index**. A candidate list built the obvious way — from the resolver's own
default index — would put holdout material in front of a learned model,
silently. G8 scores it: one holdout occurrence in any prompt is red and
voids the run.

The index here is therefore built explicitly over `[repo_root / "data"]`,
and :func:`holdout_ids` exists so the gate can check the negative rather
than trust this docstring.

## What a candidate is

A `Candidate` carries a LINE the registered grammar accepts, the route
expected to claim it, and its provenance. Two sources, both exact:

* **arithmetic** — a deliberately tiny number-word lexicon over a closed
  operator vocabulary. `"what is two to the tenth"` enumerates `2 ^ 10`.
  Tiny in the same way `supposition._atom` is tiny, and for the same
  reason: this is not English comprehension, it is the handful of forms a
  person actually types.
* **committed statements** — statements whose `title` and `keywords` share
  content words with the utterance, offered as their own title text. The
  line is the statement's words, so the resolver can bind it back.

## What verification is, and how strong it is

:func:`verify` runs committed code and records `verification_strength` from
the closed vocabulary the preregistration froze, because §4 warns that "a
candidate verified by the resolver is weaker evidence than one verified by
evaluation, and the receipt must say which — otherwise the design launders a
weak match through a strong-sounding word".

* `exact_computation` — `evaluate.evaluate` returned a value.
* `word_match` — the resolver BOUND the candidate's own title back to the
  candidate's own statement. The weakest, and it says so in the field.

A statement candidate that binds to a DIFFERENT statement is not verified.
That is the check that keeps enumeration honest: offering a line and
accepting whatever comes back would verify the verifier, not the candidate.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

#: The frozen candidate-list ceiling. Load-bearing for G5: the blind arm's
#: chance rate is 1/N, so N must be frozen before either arm runs or the
#: control's own baseline could move afterwards. Registered in the
#: preregistration's dated amendment 1.
CANDIDATE_LIMIT = 8

#: Deliberately tiny, exactly as `supposition._atom` is: this is not English
#: comprehension, it is the handful of number words a person types.
_NUMBERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "twenty": 20, "hundred": 100,
}
_ORDINALS = {
    "second": 2, "third": 3, "fourth": 4, "fifth": 5, "sixth": 6,
    "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
}
#: Closed operator vocabulary. A phrase not here is not an operator.
_OPERATORS = [
    (re.compile(r"\bto the\b"), "^"),
    (re.compile(r"\bplus\b|\badded to\b"), "+"),
    (re.compile(r"\btimes\b|\bmultiplied by\b"), "*"),
    (re.compile(r"\bminus\b|\bless\b"), "-"),
]

_WORD = re.compile(r"[a-z0-9]+")
#: Words carrying no discrimination. Kept short on purpose: a long stop list
#: is a tuning knob, and a tuning knob in an enumerator is a place for the
#: enumerator to start having opinions.
_STOP = frozenset(
    "what is are the a an of do does you your how i me tell say about "
    "corpus it that this to in for on and or with please can could".split()
)


@dataclass(frozen=True)
class Candidate:
    """One registered-grammar line the model may select. Never model-made."""

    index: int
    line: str
    route_expect: str
    source: str
    statement_id: str | None = None
    why: str = ""


@dataclass
class Verified:
    """A candidate that committed code confirmed, with its strength."""

    candidate: Candidate
    verification_strength: str
    detail: str
    evidence: dict = field(default_factory=dict)


def holdout_ids(repo_root: Path | None = None) -> frozenset[str]:
    """Statement ids under `data_holdout/`. For the gate to check a negative."""

    root = (repo_root or REPO) / "data_holdout"
    ids: set[str] = set()
    for path in sorted(root.glob("*/nodes.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        for node in document.get("statement_nodes", []):
            ids.add(node["statement_id"])
    return frozenset(ids)


@lru_cache(maxsize=4)
def _committed_statements(repo_root_str: str) -> tuple[dict, ...]:
    """Every statement under `data/`, with the words it can be found by.

    `data/` ONLY. The one line in this module that the holdout rule is
    about, and it is a glob over one directory rather than a filter over
    two — a filter can be relaxed by someone who does not know why it is
    there.
    """

    root = Path(repo_root_str) / "data"
    out: list[dict] = []
    for path in sorted(root.glob("*/nodes.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        for node in document.get("statement_nodes", []):
            title = node.get("title") or ""
            keywords = [str(word) for word in node.get("keywords") or []]
            haystack = " ".join([title, *keywords]).lower()
            out.append(
                {
                    "statement_id": node["statement_id"],
                    "title": title,
                    "words": frozenset(_WORD.findall(haystack)) - _STOP,
                }
            )
    return tuple(out)


@lru_cache(maxsize=4)
def _data_only_index(repo_root_str: str):
    """The resolver's index, built over `data/` alone.

    NOT `resolver.default_index()`, which spans `data/` AND `data_holdout/`
    — the exact mechanism slice 1's review measured (2,053 holdout ids in
    the default index). Verification here must not consult the holdout
    either, or a candidate could be confirmed by material the model is
    forbidden to see.
    """

    from resolver import build_index  # noqa: PLC0415

    return build_index([Path(repo_root_str) / "data"])


def _content_words(utterance: str) -> frozenset[str]:
    return frozenset(_WORD.findall(utterance.lower())) - _STOP


def _arithmetic_candidates(utterance: str) -> list[tuple[str, str]]:
    """`(line, why)` for arithmetic the utterance's words name."""

    lowered = utterance.lower()
    operator = None
    for pattern, symbol in _OPERATORS:
        if pattern.search(lowered):
            operator = symbol
            break
    if operator is None:
        return []
    numbers: list[int] = []
    for token in _WORD.findall(lowered):
        if token.isdigit():
            numbers.append(int(token))
        elif token in _NUMBERS:
            numbers.append(_NUMBERS[token])
        elif token in _ORDINALS:
            numbers.append(_ORDINALS[token])
    if len(numbers) < 2:
        return []
    left, right = numbers[0], numbers[1]
    return [
        (
            f"{left} {operator} {right}",
            f"the closed number lexicon read {left} and {right} and the "
            f"closed operator vocabulary read {operator!r}",
        )
    ]


def enumerate_candidates(
    utterance: str, repo_root: Path | None = None, limit: int = CANDIDATE_LIMIT
) -> list[Candidate]:
    """The finite list. Deterministic, model-free, `data/`-only."""

    root = repo_root or REPO
    out: list[Candidate] = []

    for line, why in _arithmetic_candidates(utterance):
        out.append(
            Candidate(
                index=len(out),
                line=line,
                route_expect="evaluate",
                source="arithmetic",
                why=why,
            )
        )

    asked = _content_words(utterance)
    if asked:
        scored = []
        for record in _committed_statements(str(root)):
            shared = asked & record["words"]
            if not shared:
                continue
            # Overlap, then the shorter title, then the id: a total order,
            # so the list is the same list on every run and on every
            # machine. A list whose ORDER moved would move the blind arm's
            # baseline without moving the model's.
            scored.append(
                (-len(shared), len(record["title"]), record["statement_id"], record)
            )
        scored.sort()
        for _neg, _length, _sid, record in scored[: max(0, limit - len(out))]:
            out.append(
                Candidate(
                    index=len(out),
                    line=record["title"],
                    route_expect="resolver",
                    source="committed_statement",
                    statement_id=record["statement_id"],
                    why=(
                        "the statement's title and keywords share "
                        f"{sorted(asked & record['words'])} with the utterance"
                    ),
                )
            )
    return out[:limit]


def verify(candidate: Candidate, repo_root: Path | None = None) -> Verified | None:
    """Run committed code. `None` when the candidate does not confirm."""

    root = repo_root or REPO
    if candidate.source == "arithmetic":
        from evaluate import EvalError, ResourceBound, evaluate  # noqa: PLC0415

        try:
            result = evaluate(candidate.line)
        except (EvalError, ResourceBound):
            return None
        return Verified(
            candidate=candidate,
            verification_strength="exact_computation",
            detail=f"{result.expression} = {result.formatted()}",
            evidence={"value": result.formatted()},
        )

    from resolver import BIND, resolve  # noqa: PLC0415

    outcome = resolve(candidate.line, _data_only_index(str(root)))
    if outcome.kind != BIND or outcome.bound != candidate.statement_id:
        # Binding to a DIFFERENT statement is not verification. Accepting
        # whatever came back would verify the verifier, not the candidate.
        return None
    return Verified(
        candidate=candidate,
        verification_strength="word_match",
        detail=f"{outcome.resolver}: {outcome.detail}",
        evidence={"statement_id": outcome.bound},
    )


def verified_candidates(
    utterance: str, repo_root: Path | None = None, limit: int = CANDIDATE_LIMIT
) -> tuple[list[Candidate], list[Verified]]:
    """The list the model sees, and the subset committed code confirms."""

    candidates = enumerate_candidates(utterance, repo_root, limit)
    confirmed = [v for v in (verify(c, repo_root) for c in candidates) if v]
    return candidates, confirmed
