#!/usr/bin/env python3
"""The proposer: a pinned local model that SELECTS a candidate, or none.

`docs/DESIGN-plain-input.md` is the governing spec and
`experiments/plain_input_prereg.json` froze the trust shape. The whole of
what this module lets a learned component do is written in one sentence:

    it returns an integer.

Not a query, not an answer, not a rendering, not a ranking of anything it
made up. `candidate_enumerator` builds a finite list from committed
material; this module asks a pinned model which entry the person probably
meant; committed code then verifies the selection before anything is
served. Selection narrows. Verification decides.

## The refusal is inherited, not re-invented

`scripts/machine_reader.py` built the discipline this repository uses for a
pinned local model, and this module CALLS it rather than copying it —
`verify_weights` hashes the blob's BYTES before any question is asked and
refuses on absence or mismatch, never downloading. Importing the function
also means there is one copy of the digest: a second copy is a second thing
to rot, which is the rule `serve_chat` states about the tokenizer pin.

## What the model is shown, and what it is not (B9)

The prompt is the utterance, and the numbered candidate list. That is all.
It carries **no bytes from any earlier turn** — not the previous question,
not the previous answer, not the session id. DESIGN-session-ledger §7 B9
permits one exception, assumption `normal_form`s, and this module does not
even use that: the exception exists so history CAN reach the model through
the exact layer, and here nothing needs to.

That makes B9 true by construction rather than by discipline, and the gate
still scans every prompt for it — a construction argument that nobody
checks is a construction argument that stops being true quietly.

## OFF, not crash

With no model reachable the module raises :class:`ProposerUnavailable`,
which the caller turns into today's exhaustion. Bar clause 3
(DESIGN-interactive-harness:712) is "missing checkpoint → OFF, not crash",
and G6 is where that is scored.

## Determinism

temperature 0, and the request records what it ASKED for rather than
claiming what took effect — ollama's `/v1` layer silently ignores some
sampling fields, which `measure_throughput` already documents. Whether
temperature 0 buys byte-identical output is not assumed here: P4
(`scripts/check_proposer_determinism.py`) measures it over this slice's own
prompts and the preregistration says what each outcome licenses.
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

import machine_reader as mr  # noqa: E402
from candidate_enumerator import Candidate  # noqa: E402

ENDPOINT = "http://127.0.0.1:11434/v1/chat/completions"
MODEL_TAG = "qwen3:4b-instruct"
TEMPERATURE = 0
MAX_TOKENS = 6

#: The system line. It names the ONLY two shapes of legal output, because a
#: model that answers in prose has emitted nothing this module can use and
#: its output is discarded rather than repaired (DESIGN-plain-input §3.1:
#: "anything else it emits is discarded before verification, not repaired").
SYSTEM = (
    "You are given a question and a numbered list of candidate readings. "
    "Reply with the single number of the reading the question most likely "
    "means, or the word NONE if no reading fits. Reply with a number or "
    "NONE and nothing else."
)

_SELECTION = re.compile(r"\b(\d{1,2}|NONE)\b", re.IGNORECASE)


class ProposerUnavailable(RuntimeError):
    """No reachable pinned model. The caller must serve today's exhaustion."""


@dataclass(frozen=True)
class Proposal:
    """What the model returned, and everything needed to audit it."""

    selected_index: int | None
    raw: str
    prompt: str
    elapsed_s: float
    discarded_reason: str | None = None


def build_prompt(utterance: str, candidates: list[Candidate]) -> str:
    """The whole of what the model sees. No history, by construction."""

    listed = "\n".join(
        f"{c.index + 1}. {c.line}" for c in candidates
    )
    return f"Question: {utterance}\n\nCandidate readings:\n{listed}"


def verify_pin(blob_dir: Path | None = None) -> dict:
    """machine_reader's own weights check. One copy of the digest."""

    return mr.verify_weights(blob_dir)


def propose(
    utterance: str,
    candidates: list[Candidate],
    *,
    timeout: float = 120.0,
) -> Proposal:
    """Ask which candidate. Returns a Proposal whose selection may be None.

    A reply this module cannot read as a number or NONE is DISCARDED, with
    the reason recorded. It is never repaired, never re-prompted, and never
    read as content.
    """

    if not candidates:
        return Proposal(None, "", "", 0.0, "no candidates to select from")
    prompt = build_prompt(utterance, candidates)
    body = {
        "model": MODEL_TAG,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise ProposerUnavailable(
            f"no reachable pinned model at {ENDPOINT}: {exc}. The caller "
            "serves today's exhaustion; nothing is guessed and nothing is "
            "downloaded."
        ) from None
    elapsed = time.time() - started
    raw = (payload["choices"][0]["message"]["content"] or "").strip()

    found = _SELECTION.search(raw)
    if not found:
        return Proposal(None, raw, prompt, elapsed, "reply was not a number or NONE")
    token = found.group(1)
    if token.upper() == "NONE":
        return Proposal(None, raw, prompt, elapsed, None)
    position = int(token)
    if not 1 <= position <= len(candidates):
        return Proposal(
            None, raw, prompt, elapsed,
            f"selected {position}, which is outside 1..{len(candidates)}",
        )
    return Proposal(position - 1, raw, prompt, elapsed, None)


def blind_select(candidates: list[Candidate], rng) -> Proposal:
    """G5's capability-blind arm: the SAME list, chosen at random.

    Same path, same alphabet, no capability — which is what makes the
    comparison isolate SELECTION. A blind arm that generated its own strings
    could blame its failures on generation instead.
    """

    if not candidates:
        return Proposal(None, "", "", 0.0, "no candidates to select from")
    position = rng.randrange(len(candidates))
    return Proposal(position, str(position + 1), "", 0.0, None)
