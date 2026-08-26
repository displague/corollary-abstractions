#!/usr/bin/env python3
"""P4 — is this proposer's output byte-identical across two passes?

`experiments/plain_input_prereg.json` leaves determinism OPEN at freeze time
and settles it here, before any gate is scored. The two outcomes license
different things and the preregistration says which:

* **identical** — the proposer arm registers as ROADMAP-v0.21 §4.0(2)'s
  determinism-plus-commit, and reproductions are welcome and recorded.
* **different** — the arm is NON-DETERMINISTIC and is executed ONCE with
  the run pre-announced, which is §4.0(2)'s KEPT clause: anything touching a
  model stays execute-once.

The artifact SAYS which of the two it earned rather than assuming either.

## Why this is run again when C-V3′ already ran it

`experiments/c_v3_prime_pilot.json` put this exact model at temperature 0
through two passes and got byte-identical output. That is evidence and it is
not sufficient: different prompts, a different `max_tokens`, a different
system line, and **ollama guarantees nothing** — there is no seed field
anywhere in this tree, which is the fact C-V3′ itself recorded before
testing rather than assuming. A determinism result belongs to the prompt set
that produced it.

## The honest limit, stated whichever way it reads

Byte-identity across two passes on one machine on one day is not a proof of
determinism. It is the strongest check this repository has ever run on a
model call, and the artifact reports it as exactly that.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

import candidate_enumerator as ce  # noqa: E402
import plain_proposer as pp  # noqa: E402

ARTIFACT = "experiments/plain_proposer_determinism.json"
QUESTIONS = "experiments/plain_question_set.json"


def run(repo_root: Path) -> dict:
    questions = json.loads(
        (repo_root / QUESTIONS).read_text(encoding="utf-8")
    )["questions"]

    pin = pp.verify_pin()

    passes: list[list[dict]] = []
    for attempt in (1, 2):
        rows = []
        started = time.time()
        for question in questions:
            candidates = ce.enumerate_candidates(question["question"], repo_root)
            proposal = pp.propose(question["question"], candidates)
            rows.append(
                {
                    "question_id": question["question_id"],
                    "candidates": len(candidates),
                    "raw": proposal.raw,
                    "selected_index": proposal.selected_index,
                    "discarded_reason": proposal.discarded_reason,
                }
            )
        passes.append(rows)
        print(f"  pass {attempt}: {round(time.time() - started, 1)} s")

    differing = [
        {
            "question_id": one["question_id"],
            "pass_one_raw": one["raw"],
            "pass_two_raw": two["raw"],
        }
        for one, two in zip(passes[0], passes[1])
        if one["raw"] != two["raw"] or one["selected_index"] != two["selected_index"]
    ]
    identical = not differing

    return {
        "schema": "corollary.plain-proposer-determinism/1",
        "prerequisite": "P4",
        "design": "docs/DESIGN-plain-input.md",
        "prereg": "experiments/plain_input_prereg.json",
        "measured": "2026-08-26",
        "model": {
            "provider_tag": f"ollama:{pp.MODEL_TAG}",
            "temperature": pp.TEMPERATURE,
            "max_tokens": pp.MAX_TOKENS,
            "weights_blob_sha256": pin["sha256"],
            "weights_verified_before_any_question": pin["verified"],
        },
        "sampling_requested_not_settings_that_took_effect": (
            "ollama's /v1 layer ignores some sampling fields, so this block "
            "records what was REQUESTED and never claims what took effect — "
            "the wording measure_throughput and machine_reader both use"
        ),
        "prompts": len(questions),
        "two_passes_byte_identical": identical,
        "differing": differing,
        "what_this_licenses": (
            "the proposer arm registers as determinism-plus-commit "
            "(ROADMAP-v0.21 §4.0(2)); reproductions are welcome and recorded"
            if identical
            else "NOTHING about reproduction. The arm is non-deterministic "
            "and is executed ONCE with the run pre-announced, which is "
            "§4.0(2)'s KEPT clause for anything touching a model."
        ),
        "the_honest_limit": (
            "byte-identity across two passes on one machine on one day is "
            "not a proof of determinism. It is the strongest check this "
            "repository has ever run on a model call, and it is reported as "
            "that and nothing more."
        ),
        "why_c_v3_primes_result_was_not_inherited": (
            "experiments/c_v3_prime_pilot.json got byte-identical output "
            "from this same model at temperature 0 — with different prompts, "
            "a different max_tokens and a different system line. ollama "
            "guarantees nothing and no seed field exists anywhere in this "
            "tree, so a determinism result belongs to the prompt set that "
            "produced it."
        ),
        "pass_one": passes[0],
        "pass_two": passes[1],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=ARTIFACT)
    args = ap.parse_args(argv)

    try:
        payload = run(REPO)
    except pp.ProposerUnavailable as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except mr_refusal() as exc:  # pragma: no cover - pin failure path
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    out = REPO / args.out
    out.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {args.out}")
    print(f"  two passes byte-identical: {payload['two_passes_byte_identical']}")
    print(f"  {payload['what_this_licenses']}")
    return 0


def mr_refusal():
    import machine_reader  # noqa: PLC0415

    return machine_reader.ReaderRefusal


if __name__ == "__main__":
    raise SystemExit(main())
