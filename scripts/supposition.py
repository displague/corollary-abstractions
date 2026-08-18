#!/usr/bin/env python3
"""`suppose ...` — a place where fabrication is legal and marked as such.

Arbitrary text wants conjecture, hypotheticals, opinions and deliberate
fiction. A system that answers only corpus facts refuses all four, which is
honest and useless. A system that answers them *as facts* is dishonest. The
third option is the one this project already had and was not using: hold the
claim inside a **frame**, where the check is consistency with the frame's own
premises rather than truth in the world.

The corpus already declares such frames as first-class content —
`narrative.frames.cartoon_gravity` is a committed Frame Declaration, and the
narrative corpus carries story structure, Chekhov's Gun and the
no-deus-ex-machina condition as statements. So a story is not an exception to
the graph; it is a region of it with different rules.

## What a supposition is, exactly

- It opens a frame **owned by the person who typed it**, never the corpus.
- The claim is held as a frame-local literal.
- `FrameSpec.on_exit` is `conjectured`: whatever leaves this frame leaves as
  conjecture. Nothing typed here can become a corpus fact, and no later
  answer can quote it as one.
- `FrameExecutor.open_frame` refuses a frame that declares a contradiction,
  and `assert_literal` refuses a claim that contradicts one already held. So
  "consistent" is enforced by the executor, not by care.

## What it is not

Not truth evaluation — a supposition is not checked against the world, and
saying "the chicken crossed the road" is neither true nor false here.

Not a multi-turn supposition editor.  P-LS6 now keeps resolver ASK state, but
one `suppose` line still holds one claim; a later line is a new route, not an
implicit continuation of that frame.  Contradiction *between* two typed
claims is therefore not reachable yet; the executor supports it, the surface
does not, and that gap is named rather than papered over.

Not generation. The system does not continue the story. It records the
supposition, marks its status, and — if the words also match committed
statements — names them, so a fiction can be anchored to the graph without
being confused for it.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from frames import FrameExecutor, FrameSpec, Literal  # noqa: E402

#: The command word. Same discipline as `owns`: a registered command, not a
#: phrase the system claims to understand.
COMMAND = "suppose"

#: A leading negation the atom-level check can actually see. Deliberately
#: tiny: this is not negation parsing, it is the one form a person types
#: when they mean the opposite of something they just said.
_NEGATIONS = ("not ", "no ", "never ")


@dataclass(frozen=True)
class Supposition:
    frame: str
    claim: str
    polarity: bool
    status: str
    accepted: bool
    detail: str
    related: tuple[str, ...] = ()


def _atom(text: str) -> tuple[str, bool]:
    """Claim text -> (normalised atom, polarity)."""
    lowered = " ".join(text.lower().split())
    polarity = True
    for marker in _NEGATIONS:
        if lowered.startswith(marker):
            lowered = lowered[len(marker):].strip()
            polarity = False
            break
    return lowered, polarity


def suppose(text: str, *, owner: str = "user") -> Supposition:
    """Hold `text` as a frame-local claim. Never as a fact."""
    claim, polarity = _atom(text)
    # `frames` reserves a namespace for frames with no corpus node behind
    # them, and refuses anything else. A supposition typed at a prompt is
    # exactly that: runtime-only, owned by a person, backed by nothing.
    frame_name = "runtime.frames.supposition"
    executor = FrameExecutor()
    spec = FrameSpec(
        frame=frame_name,
        owner=owner,
        title="A supposition typed by the person at the prompt",
        # on_exit is the honesty guarantee: anything leaving this frame is
        # conjecture. It is the executor's default and is named here so a
        # future edit has to argue with the word rather than delete it.
        on_exit="conjectured",
        retrieval="open",
    )
    state = executor.open_frame(spec)
    literal = Literal("supposed", "holds" if polarity else "fails", claim)
    result = executor.assert_literal(state, "typed.supposition", literal)
    accepted = bool(getattr(result.verdict, "accepts", False))
    return Supposition(
        frame=frame_name,
        claim=claim,
        polarity=polarity,
        status=spec.on_exit,
        accepted=accepted,
        detail=result.reason,
    )


def render(supposition: Supposition) -> list[str]:
    """What the person sees. No continuation, no evaluation of truth."""
    out = [
        f"frame      : {supposition.frame} (owner: you)",
        f"supposed   : {'not ' if not supposition.polarity else ''}"
        f"{supposition.claim}",
        f"held as    : {supposition.status}",
        f"executor   : {supposition.detail}",
    ]
    if supposition.related:
        out.append("")
        out.append("committed statements sharing these words:")
        for sid in supposition.related:
            out.append(f"  {sid}")
        out.append(
            "  (named so the supposition can be anchored to the graph; "
            "they do not make it true)"
        )
    out.append("")
    out.append(
        "this is conjecture held inside a frame you own; it is not a corpus "
        "fact and nothing later will quote it as one"
    )
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("claim", nargs="+")
    args = ap.parse_args(argv)
    print("\n".join(render(suppose(" ".join(args.claim)))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
