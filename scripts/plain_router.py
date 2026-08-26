#!/usr/bin/env python3
"""Row 12's pre-router: propose, verify, and name the hidden variable.

`docs/DESIGN-plain-input.md` §1's served shape, built:

    *assuming you meant X* [supposition S, stated] *, the answer is Y*
    [receipt].

This module owns the BRANCH and nothing else. It enumerates (exact code),
asks the proposer for an index (the only learned step), verifies the
selection (exact code), and then decides — from the selection and the
verification, never from anything the model said in prose.

## The branch, as the preregistration's amendment 2 corrected it

* the proposer SELECTS a candidate and committed code VERIFIES it →
  **`conditional`**, served under one named supposition, with every other
  verified candidate named in `alternatives_not_taken`.
* the proposer selects nothing, or its selection fails verification, and
  **two or more** candidates verify → **ask**, naming the readings. The
  residue would need more than one supposition to serve, which is the
  frozen bound of one multiplying past itself — the design's own trigger
  for the clarifying-question loop.
* nothing verifies → **`None`**, and row 12 exhausts exactly as it does
  today.

The first version of that rule sent every case with rivals to the ask
branch. It was a misreading of the design and is corrected in prereg
amendment 2 against the design's own text — including §3b's
`alternatives_not_taken`, a field a conditional answer could never carry if
rivals forced a clarification.

## What the answer is, and what it is not

`answer_under` is **the verbatim engine answer, unchanged from what that
route would have emitted had the supposition been typed** (§3b). This module
composes no sentence of its own beyond the labels: it re-serves the selected
candidate's line through `route_line` on a fresh session and passes the
result through. DESIGN-plain-input §7: *"A conditional answer is a LABEL
WRAPPED AROUND AN EXISTING ANSWER, not a generated one."*

## Zero useful tokens

Status `conditional` is non-answering (SPEC ¶AMD-1), so this branch cannot
inflate the throughput metric however much it serves. That is the property
that makes the design's incentive argument sound, and G7b tests it from the
scoring path.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

import candidate_enumerator as ce  # noqa: E402
import plain_proposer as pp  # noqa: E402

#: The frozen bound: one proposed supposition per served answer.
SUPPOSITION_BUDGET = 1


@dataclass
class RouterTrace:
    """Everything the gate needs to audit one plain-input turn."""

    utterance: str
    candidates: list = field(default_factory=list)
    verified: list = field(default_factory=list)
    prompt: str = ""
    raw: str = ""
    selected_index: int | None = None
    discarded_reason: str | None = None
    branch: str = "exhaust"
    unavailable: bool = False


class PlainRouter:
    """Attached to a CoreSession by a recorder or a gate runner. Never by the
    skin, and never by `main()`."""

    def __init__(self, *, blind_rng=None, repo_root: Path | None = None) -> None:
        #: G5's capability-blind arm. When set, selection is a uniform draw
        #: over the SAME enumerated list — same path, same alphabet, no
        #: capability — so the comparison isolates selection and nothing
        #: else.
        self.blind_rng = blind_rng
        self.repo_root = repo_root or REPO
        self.traces: list[RouterTrace] = []

    # -- the branch -------------------------------------------------------

    def route(self, repo_root: Path, session, line: str) -> dict | None:
        trace = RouterTrace(utterance=line)
        self.traces.append(trace)

        candidates = ce.enumerate_candidates(line, repo_root)
        trace.candidates = candidates
        if not candidates:
            return None

        verified = [v for v in (ce.verify(c, repo_root) for c in candidates) if v]
        trace.verified = verified

        if self.blind_rng is not None:
            proposal = pp.blind_select(candidates, self.blind_rng)
        else:
            try:
                proposal = pp.propose(line, candidates)
            except pp.ProposerUnavailable:
                # G6 / bar clause 3: OFF, not crash. Row 12 exhausts exactly
                # as it does today, and the trace records that the model was
                # absent rather than that it declined.
                trace.unavailable = True
                return None
        trace.prompt = proposal.prompt
        trace.raw = proposal.raw
        trace.selected_index = proposal.selected_index
        trace.discarded_reason = proposal.discarded_reason

        chosen = None
        if proposal.selected_index is not None:
            for item in verified:
                if item.candidate.index == proposal.selected_index:
                    chosen = item
                    break

        if chosen is not None:
            trace.branch = "conditional"
            return self._conditional(repo_root, session, line, chosen, verified)
        if len(verified) >= 2:
            trace.branch = "ask"
            return self._ask(line, verified)
        return None

    # -- the two served shapes -------------------------------------------

    def _conditional(self, repo_root, session, line, chosen, verified) -> dict:
        served = self._reserve(repo_root, session, chosen.candidate.line)
        reading = chosen.candidate.line
        others = [
            v.candidate.line for v in verified if v.candidate.index
            != chosen.candidate.index
        ]
        return {
            "route": "plain_input",
            # SPEC ¶AMD-1's minted status. NOT `solved`, NOT `found`, NOT
            # `held` — a conditional answer asserts nothing unconditionally
            # and scores zero useful tokens.
            "status": "conditional",
            "detail": (
                f"assuming you meant {reading!r}; "
                f"verified by {chosen.verification_strength}"
            ),
            "answer": [
                f"assuming    : you meant {reading}",
                f"verified by : {chosen.verification_strength}",
                "",
                *(served.get("answer") or [f"({served.get('detail','')})"]),
                "",
                "this answer is conditional on the reading named above; it is "
                "not a claim that you meant it",
            ],
            "receipt": {
                "suppositions": [
                    {
                        "variable": "reading",
                        "value": reading,
                        "source": "proposed",
                        "why": chosen.candidate.why,
                    }
                ],
                "supposition_budget": SUPPOSITION_BUDGET,
                "verification_strength": chosen.verification_strength,
                "verification_detail": chosen.detail,
                "route_that_produced_the_answer": served.get("route"),
                "underlying_status": served.get("status"),
                "alternatives_not_taken": others,
            },
        }

    def _ask(self, line, verified) -> dict:
        readings = [v.candidate.line for v in verified]
        return {
            "route": "plain_input",
            # The kernel's own word for "a person owes the next move".
            "status": "waiting",
            "detail": (
                f"{len(readings)} readings verify and none was selected; "
                "no reading is chosen on your behalf"
            ),
            "answer": [
                "these readings all verify:",
                *(f"  {reading}" for reading in readings),
                "",
                "say which you meant; nothing was chosen for you",
            ],
            "receipt": {
                "suppositions": [],
                "verified_readings": readings,
                "why_not_conditional": (
                    "serving one would need a supposition the proposer did "
                    f"not supply, and the budget is {SUPPOSITION_BUDGET}"
                ),
            },
        }

    # -- re-serving the selected line ------------------------------------

    @staticmethod
    def _reserve(repo_root, session, candidate_line: str) -> dict:
        """The verbatim engine answer for the selected reading.

        Served on a FRESH session with no proposer attached, for two
        reasons. It cannot recurse — a fresh session's `proposer` is None,
        so `_route_proposed` returns immediately. And what comes back is
        exactly "what that route would have emitted had the supposition been
        typed" (§3b), because it IS that route serving that line.
        """

        from harness import CoreSession, route_line  # noqa: PLC0415

        fresh = CoreSession.boot(repo_root, offline=True)
        fresh.resolver_index = getattr(session, "resolver_index", None)
        return route_line(repo_root, fresh, candidate_line)
