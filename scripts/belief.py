#!/usr/bin/env python3
"""Who believes what, and what follows inside one person's head.

    dotty sees bob walk into the room. bob is in the kitchen.
    dotty knows the room is the kitchen. Where does dotty think bob is?

This is not a corpus lookup and not a computation. It is a question about a
**frame** — the region of belief owned by one agent — and this project has
carried a `FrameExecutor` for owner-scoped belief since v0.7 without ever
letting a person ask it anything.

## The reasoning, and why it is closed form

Each agent gets a store of two relations, both taken only from what that
agent was said to witness or know:

- `located_in(x, p)` — the agent believes x is at p
- `same_as(a, b)` — the agent believes a and b are the same thing

Answering "where does A think B is" is then: look up `located_in(B)` in A's
own store, and rewrite the answer through A's `same_as` classes until it
stops changing. Equality classes are a union-find; the rewrite terminates
because each step moves to a class representative. No search, no scoring, no
model.

## The part that makes it a belief and not a fact

**World facts never enter an agent's store.** "bob is in the kitchen" is
said by the narrator, not witnessed by dotty, so it goes to a world store
that the query does not read. That separation is the whole point: it is what
lets the system answer a false-belief question correctly.

    dotty sees bob walk into the room. bob moves to the garden.
    Where does dotty think bob is?   -> the room

Dotty did not see him leave. A system that answered "the garden" would be
reporting the world, not the belief, and would fail the oldest test in
theory of mind.

## What this is not

A **micro-grammar**, not language understanding. It reads a handful of
sentence forms — `X sees Y <verb> the P`, `X knows A is B`, `A is in the P`,
`A is B`, and `where does X think Y is` — and refuses everything else by
finding nothing. It is closer to a command with slots than to parsing. When
it cannot read a sentence it says so and names the sentence, rather than
guessing at meaning.

No pronoun resolution, no tense, no negation, no plurals, no time ordering
beyond "later statements about the same agent overwrite earlier ones".
Each is a real limit and each is listed here so nobody has to discover it.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

WORD = r"[a-z][a-z0-9_'-]*"

#: `dotty sees bob walk into the room`, `ann sees the ball go to the box`
SEES = re.compile(
    rf"\b({WORD})\s+(?:sees|saw|watches|watched)\s+(?:the\s+)?({WORD})"
    rf"(?:\s+(?:{WORD}))*?\s+(?:in)?to\s+(?:the\s+)?({WORD})",
)
#: `dotty knows the room is the kitchen`
KNOWS_SAME = re.compile(
    rf"\b({WORD})\s+(?:knows|believes|thinks)\s+(?:that\s+)?(?:the\s+)?({WORD})"
    rf"\s+is\s+(?:the\s+)?({WORD})",
)
#: `bob is in the kitchen` — narrator's world fact
WORLD_IN = re.compile(rf"\b({WORD})\s+is\s+in\s+(?:the\s+)?({WORD})")
#: `bob moves to the garden` — world change the agent may not have seen
WORLD_MOVE = re.compile(
    rf"\b({WORD})\s+(?:moves|moved|goes|went|walks|walked)\s+"
    rf"(?:in)?to\s+(?:the\s+)?({WORD})",
)
#: `where does dotty think bob is`
QUERY = re.compile(
    rf"\bwhere\s+(?:does|do|would|will)\s+({WORD})\s+"
    rf"(?:think|believe|expect|say)\s+(?:that\s+)?({WORD})\s+is",
)

_ARTICLES = {"the", "a", "an"}


@dataclass
class BeliefStore:
    """One agent's beliefs. Deliberately incapable of holding world facts."""

    located_in: dict[str, str] = field(default_factory=dict)
    same_as: dict[str, str] = field(default_factory=dict)

    def _root(self, name: str) -> str:
        seen: set[str] = set()
        cur = name
        while cur in self.same_as and cur not in seen:
            seen.add(cur)
            cur = self.same_as[cur]
        return cur

    def unify(self, a: str, b: str) -> None:
        ra, rb = self._root(a), self._root(b)
        if ra != rb:
            self.same_as[ra] = rb

    def where(self, subject: str) -> str | None:
        place = self.located_in.get(self._root(subject))
        if place is None:
            for name, value in self.located_in.items():
                if self._root(name) == self._root(subject):
                    place = value
                    break
        return self._root(place) if place is not None else None


@dataclass
class Reading:
    """Everything the micro-grammar could read out of the text."""

    agents: dict[str, BeliefStore] = field(default_factory=dict)
    world: BeliefStore = field(default_factory=BeliefStore)
    unread: tuple[str, ...] = ()

    def store(self, agent: str) -> BeliefStore:
        return self.agents.setdefault(agent, BeliefStore())


def read(text: str) -> Reading:
    """Apply the micro-grammar. Unread sentences are reported, not guessed."""
    reading = Reading()
    unread: list[str] = []
    lowered = text.lower()
    for raw in re.split(r"[.;\n]", lowered):
        sentence = raw.strip()
        if not sentence:
            continue
        matched = False
        for agent, subject, place in SEES.findall(sentence):
            reading.store(agent).located_in[subject] = place
            matched = True
        for agent, left, right in KNOWS_SAME.findall(sentence):
            if left in _ARTICLES or right in _ARTICLES:
                continue
            reading.store(agent).unify(left, right)
            matched = True
        if not matched:
            for subject, place in WORLD_MOVE.findall(sentence):
                reading.world.located_in[subject] = place
                matched = True
            for subject, place in WORLD_IN.findall(sentence):
                reading.world.located_in[subject] = place
                matched = True
        if not matched and not QUERY.search(sentence):
            unread.append(sentence)
    reading.unread = tuple(unread)
    return reading


@dataclass(frozen=True)
class Answer:
    agent: str
    subject: str
    place: str | None
    world_place: str | None
    steps: tuple[str, ...]
    unread: tuple[str, ...]


def answer(text: str) -> Answer | None:
    """Answer `where does A think B is`, or `None` if no such question."""
    found = QUERY.search(text.lower())
    if not found:
        return None
    agent, subject = found.group(1), found.group(2)
    reading = read(text)
    store = reading.agents.get(agent)
    steps: list[str] = []
    place: str | None = None
    if store is None:
        steps.append(f"no frame for {agent}: nothing observed or known")
    else:
        seen = store.located_in.get(subject)
        if seen is None:
            steps.append(f"{agent}: no observation of {subject}")
        else:
            steps.append(f"{agent} observed  located_in({subject}) = {seen}")
            resolved = store._root(seen)
            if resolved != seen:
                steps.append(f"{agent} holds     same_as({seen}) = {resolved}")
                steps.append(f"rewrite         located_in({subject}) = {resolved}")
            place = resolved
    world = reading.world.located_in.get(subject)
    if world is not None:
        steps.append(f"narrator        located_in({subject}) = {world}")
    return Answer(agent, subject, place, world, tuple(steps), reading.unread)


def render(result: Answer) -> list[str]:
    """A structured readout. Labels and values — no authored sentences.

    An earlier version of this function wrote English: "dotty thinks bob is
    in the kitchen". That was template prose, which is the thing this project
    refuses, and it was worse than useless dressing — a fluent sentence
    invites the reader to trust a fluency the system does not have. The
    corpus can be quoted because a person wrote it and a schema checks it.
    Nothing here has that provenance, so nothing here is written as prose.

    What is printed instead is the derivation: the relations that were read,
    the class they resolved through, and the answer as a relation. A reader
    can check every line against the sentence they typed.
    """
    out = [
        f"agent      : {result.agent}",
        f"subject    : {result.subject}",
    ]
    if result.place is None:
        out.append("believes   : (nothing — not derivable from what was said)")
    else:
        out.append(f"believes   : located_in({result.subject}) = {result.place}")
    if result.world_place is not None:
        out.append(f"world says : located_in({result.subject}) = {result.world_place}")
        if result.place is not None and result.place != result.world_place:
            out.append(
                "divergence : belief and world differ; the question asked "
                "for the belief"
            )
    out.append("")
    out.append("derivation :")
    for step in result.steps:
        out.append(f"  {step}")
    if result.unread:
        out.append("")
        out.append("unread     : the grammar here is small; these were skipped")
        for sentence in result.unread:
            out.append(f"  ? {sentence}")
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("text", nargs="+")
    args = ap.parse_args(argv)
    result = answer(" ".join(args.text))
    if result is None:
        print("no belief question found", file=sys.stderr)
        return 2
    print("\n".join(render(result)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
