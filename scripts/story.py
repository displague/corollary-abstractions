#!/usr/bin/env python3
"""A story, run through the verifier that checks it obeys its own rules.

`tell me a story about a chicken` abstained for the whole of v0.13, and the
reason given was that telling a story means authoring prose or generating
it. That was wrong, and the evidence was already committed: this repo has
had a golden-chicken story frame and a `StoryFrameVerifier` since v0.8, and
nothing had ever let a person reach them.

What runs here is not generation and not a template written for this module.
The beats come from committed frame data, rendered by the committed v0.8
program that rewords accepted content without moving facts, and every beat
is checked by the verifier against constraints the corpus states as ordinary
statements:

- `narrative.structure.story_sequence` — setup, complication, resolution, in
  that order.
- `narrative.constraint.chekhov_gun` — anything deliberately shown must do
  narrative work. The feather is planted in the setup and discharged in the
  resolution; a story that plants and never discharges does not verify.
- `narrative.constraint.no_deus_ex_machina` — anything used to resolve the
  plot must be present no later than the outcome that uses it.
- `narrative.frame.frame_consistency` — a story may not contradict its own
  premises.

So the honest claim is narrow and real: **the system does not invent
stories; it holds one and can prove it is well formed.** The constraints are
quoted from the corpus, so a reader can check the rules as easily as the
story.

## What is still not here

One committed story, not stories on demand about a subject you choose.
Asking for a story about a rabbit gets the chicken, clearly labelled, plus
the grammar — because inventing a rabbit story is the thing that would
require authoring or generating. Multi-turn beat-by-beat authoring, where a
person supplies each beat and the verifier accepts or refuses it, is the
natural next step and is blocked by P-LS6, not by design.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

#: The boot-matrix subsystem this is a capability of.
REQUIRES_SUBSYSTEM = "narrative.story"

#: The committed statements the verifier enforces. Quoted, not paraphrased,
#: so the rules are as checkable as the story.
CONSTRAINT_IDS = (
    "narrative.structure.story_sequence",
    "narrative.constraint.chekhov_gun",
    "narrative.constraint.no_deus_ex_machina",
    "narrative.frame.frame_consistency",
)

#: A request for a story. A registered question shape, like `owns`.
STORY_REQUEST = re.compile(
    r"(?:\btell\s+me\s+a\s+story|\btell\s+a\s+story|\ba\s+story\s+about|"
    r"\bwrite\s+me\s+a\s+story|^\s*story\s*$)",
    re.IGNORECASE,
)


def is_story_request(text: str) -> bool:
    return bool(STORY_REQUEST.search(text.strip()))


@dataclass(frozen=True)
class Told:
    solved: bool
    stop_reason: str
    desire: str | None
    beats: tuple[tuple[str, str], ...]
    accepted: int
    rejected: int


def tell() -> Told:
    """Run the committed story oracle and report what the verifier said."""
    from oracle_controller_demo import story_oracle_run  # noqa: PLC0415

    run = story_oracle_run()
    final = run.final_state
    return Told(
        solved=bool(run.solved),
        stop_reason=run.stop_reason.value,
        desire=getattr(final, "desire", None),
        beats=tuple((b.role, b.text) for b in getattr(final, "beats", ())),
        accepted=int(run.accepted_steps),
        rejected=int(run.rejected_steps),
    )


def constraint_prose() -> dict[str, tuple[str, str]]:
    """Title and meaning for each rule, quoted from the corpus."""
    from answer import compose  # noqa: PLC0415

    out: dict[str, tuple[str, str]] = {}
    for sid in CONSTRAINT_IDS:
        answer = compose(sid)
        if answer is not None:
            out[sid] = (answer.title, answer.meaning)
    return out


def render(told: Told, constraints: dict[str, tuple[str, str]]) -> list[str]:
    """The story, then the rules it was checked against — both quoted."""
    out: list[str] = []
    for _role, text in told.beats:
        out.append(f"  {text}")
    if not told.beats:
        out.append("  (the verifier produced no beats)")
    out.append("")
    out.append(
        f"verifier   : {told.stop_reason} "
        f"({told.accepted} beats accepted, {told.rejected} rejected)"
    )
    if told.desire:
        out.append(f"the desire : {told.desire}")
    out.append("")
    out.append("checked against the corpus's own story rules:")
    for sid, (title, meaning) in constraints.items():
        out.append(f"  {title}")
        out.append(f"    {meaning}")
        out.append(f"    [{sid}]")
    out.append("")
    out.append(
        "this story is committed data checked by the narrative verifier; it "
        "was not written for this answer, and no other story is invented on "
        "request"
    )
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.parse_args(argv)
    print("\n".join(render(tell(), constraint_prose())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
