#!/usr/bin/env python3
"""C-V3′: a pinned local model reads the English blind and picks the term.

*Maintainer directive, 2026-08-24.*  DESIGN-voice-completion §7 and
`docs/DESIGN-plain-input.md` §6, which is the shared cross-design definition
this control ratifies.

C-V3, the human determinacy sheet, requires thirty statements *"marked blind
by a **non-maintainer**"*.  A single-maintainer repository has no
non-maintainer, so C-V3 has never run: **ABSENT**, with the claim it alone
could license not made.  C-V3′ buys an instrument that *can* run — and buys a
strictly weaker claim with it.

**What it licenses, exactly:** *the English determines the term to an
independent machine reader that never saw the term.*  That is a fact about a
model.  It is **not** a readability claim, it is **not** a human-reader claim,
and C-V3 stays ABSENT beside it.  Every number this module produces is
labelled MACHINE-reader, here and in every sentence that quotes it.

**It grades only.**  No output reaches a served answer, gates a rendering,
ranks anything or mints a receipt.  B6's no-learned-component rule is
untouched because nothing learned sits in the render path, the inverse, rule
R, the grouping rule or the register.

## Two arms, and the second is what makes the first mean anything

* **the served arm** — the reader sees a rendered English sentence and picks
  the formal term from four candidates.  Three are **mutation-class
  distractors** built from the same classes C-V4′ mutates: a deleted grouping
  pair, a swapped binder, a shifted group.  *A reader that cannot tell a
  served sentence from its near-miss is not reading it.*
* **the skeleton arm, interleaved and unlabelled** — the same question, but
  the sentence is rendered through C-V1's **scrambled** table.  The words are
  wrong; the structure and the numerals are not.  A reader that still picks
  the truth is supplying the mathematics itself, which is the exact failure
  C-V3 was built to catch.

C-V3's voiding sentence is inherited **unchanged**: *if the skeleton arm is
marked determinate at ≥ half the served arm's rate, the voice claim is void —
the sheet is measuring the reader's mathematical guesswork, not the
rendering.*

## The refusal is BUILT here, not inherited

> **Correction 9.**  The quotable refusal policy — *"digest-pinned here; token
> counting REFUSES (exit 2) when the file is absent or its digest mismatches —
> cannot-verify, never skip"* — is the **tokenizer's**.
> `weights_blob_sha256` appears exactly once in the whole tree and **nothing
> reads it at run time**.

So this module hashes the weights blob itself before any question is asked,
and refuses on absence or mismatch.  It never downloads.  The filename ollama
gives a blob is its digest, and trusting that would be checking the copy
against itself — the same reasoning the git-blob precedent states — so the
bytes are read and hashed.

## Its floor is a construction prerequisite, not a number picked now

**There is no `seed` field in any manifest or request body anywhere in this
tree**, so temperature-0 determinism is an assumption this repository has
never tested.  The pilot settles it before any floor is frozen: same inputs,
same model, temperature 0, **byte-identical output across two passes**.  *If
reproducibility fails, C-V3′ publishes that failure as its result and reverts
to ABSENT* — an instrument that cannot repeat itself can only void, never
confirm.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - CLI import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import foreign_voice as fv  # noqa: E402
import foreign_voice_lexicon as fvl  # noqa: E402
import grouping_canonical_probe as gp  # noqa: E402
import measure_foreign_voice as mfv  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA = REPO_ROOT / "data" / "foreign_voice"
DEFAULT_PILOT_OUT = REPO_ROOT / "experiments" / "c_v3_prime_pilot.json"
DEFAULT_ARM_OUT = REPO_ROOT / "experiments" / "c_v3_prime_arm.json"

#: Pinned to the byte, the fields `experiments/throughput_baseline.json`
#: already pins. C-V3′ pins the same ones in its own manifest rather than
#: reading that file, because a control that shares a manifest with a
#: throughput benchmark inherits its sampling too — and this one must not.
MANIFEST = {
    "control": "C-V3′ — the machine blind reader",
    "labelled": "MACHINE-reader, never human",
    "model": {
        "name": "Qwen3-4B-Instruct-2507",
        "provider_tag": "ollama:qwen3:4b-instruct",
        "quantization": "Q4_K_M",
        "weights_blob_sha256":
            "85e4a5b7b8ef0e48af0e8658f5aaab9c2324c76c1641493f4d1e25fce54b18b9",
    },
    "runtime": {"engine": "ollama", "version": "0.32.15",
                "endpoint": "http://127.0.0.1:11434/v1/chat/completions",
                "loopback_only": True},
    "sampling": {
        "temperature": 0,
        "sampling_requested": {"temperature": 0},
        "sampling_source": (
            "declared by this control, NOT inherited from the throughput "
            "baseline, which runs at temperature 0.7 with vendor defaults"
        ),
        "not_settings_that_took_effect": (
            "ollama's /v1 layer ignores top_k and repeat_penalty (verified live "
            "2026-08-22), so this block records what was REQUESTED and never "
            "claims what took effect — the wording "
            "scripts/measure_throughput.py:669-677 already uses"
        ),
        "no_seed_field_exists_anywhere_in_this_tree": (
            "so temperature-0 determinism is an assumption this repository has "
            "never tested, and the pilot is what settles it"
        ),
    },
    "it_grades_only": (
        "no output reaches a served answer, gates a rendering, ranks anything "
        "or mints a receipt"
    ),
}

_BLOB_DIR = Path.home() / ".ollama" / "models" / "blobs"
_LETTERS = "ABCD"


class ReaderRefusal(RuntimeError):
    """Cannot verify. Never skip, never download, never publish a number."""


# --------------------------------------------------------------------------
# The refusal Correction 9 says must be built
# --------------------------------------------------------------------------


def verify_weights(blob_dir: Path | None = None) -> dict:
    """Hash the pinned weights blob. REFUSES on absence or mismatch.

    The bytes are read rather than the filename trusted. ollama names a blob
    by its digest, so believing the name would be checking the copy against
    itself — the reasoning `transliteration_served_diff.py` states for taking
    a blob from git rather than reverting in memory.
    """
    pinned = MANIFEST["model"]["weights_blob_sha256"]
    directory = blob_dir or _BLOB_DIR
    path = directory / f"sha256-{pinned}"
    if not path.is_file():
        raise ReaderRefusal(
            f"the pinned weights blob is not present at {path}. REFUSING, and "
            f"not downloading: C-V3′ publishes no number it cannot pin. "
            f"(cannot-verify, never skip — the rule the tokenizer already lives "
            f"by, built here because nothing in this tree reads "
            f"weights_blob_sha256 at run time)")
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 22), b""):
            digest.update(chunk)
            size += len(chunk)
    measured = digest.hexdigest()
    if measured != pinned:
        raise ReaderRefusal(
            f"the weights blob at {path} hashes to {measured[:16]}… and the "
            f"manifest pins {pinned[:16]}…. REFUSING: a number from unpinned "
            f"weights is not reproducible and is not a measurement.")
    return {"path_relative_to_home": str(path.relative_to(Path.home())).replace("\\", "/"),
            "bytes": size, "sha256": measured, "verified": True}


# --------------------------------------------------------------------------
# The sheet
# --------------------------------------------------------------------------


@dataclass
class Item:
    statement_id: str
    arm: str                      # "served" | "skeleton"
    sentence: str
    candidates: list[str]
    correct: int
    distractor_classes: list[str] = field(default_factory=list)

    def prompt(self) -> str:
        options = "\n".join(f"{_LETTERS[i]}) {c}"
                            for i, c in enumerate(self.candidates))
        return (
            "Below is an English sentence that describes exactly one formal "
            "mathematical statement, and four candidate statements written in "
            "Lean.\n\nEnglish sentence:\n"
            f"{self.sentence}\n\nCandidates:\n{options}\n\n"
            "Which candidate does the English sentence describe? "
            "Reply with a single capital letter and nothing else."
        )


def _mutations(tokens: list[str], kinds: list[str], rng: random.Random,
               rule: gp.Rule) -> list[tuple[str, str]]:
    """Distractor terms from the C-V4′ mutation classes. Never the truth."""
    out: list[tuple[str, str]] = []
    spans = gp.grouping_pair_spans(tokens, kinds)
    if spans:
        span = spans[rng.randrange(len(spans))]
        out.append(("drop_group", " ".join(gp.delete_pair(tokens, span))))
        start, end = span
        if end + 1 < len(tokens):
            shifted = list(tokens)
            shifted.insert(end + 2, shifted.pop(end))
            out.append(("shift_group", " ".join(shifted)))
    # swap two binder names in the preamble, leaving their occurrences alone
    if tokens and tokens[0] in rule.binders:
        names = []
        i = 1
        while i < len(tokens) and tokens[i] not in (":", ","):
            names.append(i)
            i += 1
        if len(names) >= 2:
            swapped = list(tokens)
            a, b = names[0], names[1]
            swapped[a], swapped[b] = swapped[b], swapped[a]
            out.append(("swap_binder", " ".join(swapped)))
    return out


def build_items(rows: list[dict], lexicon: fvl.ForeignLexicon,
                scrambled: fvl.ForeignLexicon, rule: gp.Rule,
                n_served: int, n_skeleton: int, seed_hex: str) -> list[Item]:
    """A preregistered sheet: served items with skeleton items interleaved."""
    rng = random.Random(int(seed_hex[:16], 16))
    pool = sorted(rows, key=lambda r: r["statement_id"])
    rng.shuffle(pool)

    items: list[Item] = []
    for row in pool:
        if len(items) >= n_served + n_skeleton:
            break
        rendered = fv.render_interpreted(row["interpreted"], lexicon)
        if isinstance(rendered, fv.Refusal):
            continue
        emission = gp.emit(gp.parse(row["interpreted"], rule), rule)
        truth = " ".join(emission.tokens)
        pairs = _mutations(emission.tokens, emission.pair_kinds, rng, rule)
        pairs = [(name, text) for name, text in pairs if text != truth]
        if len(pairs) < 3:
            continue
        chosen = pairs[:3]
        arm = "served" if sum(1 for i in items if i.arm == "served") < n_served \
            else "skeleton"
        if arm == "skeleton":
            skeleton = fv.render_interpreted(row["interpreted"], scrambled)
            if isinstance(skeleton, fv.Refusal):
                continue
            sentence = skeleton.surface
        else:
            sentence = rendered.surface
        candidates = [truth] + [text for _n, text in chosen]
        order = list(range(4))
        rng.shuffle(order)
        items.append(Item(
            statement_id=row["statement_id"], arm=arm,
            sentence=sentence,
            candidates=[candidates[i] for i in order],
            correct=order.index(0),
            distractor_classes=[name for name, _t in chosen],
        ))
    rng.shuffle(items)          # interleaved and unlabelled
    return items


# --------------------------------------------------------------------------
# Asking
# --------------------------------------------------------------------------


def ask(item: Item, timeout: float = 180.0) -> tuple[str, float]:
    body = {
        "model": MANIFEST["model"]["provider_tag"].split("ollama:")[-1],
        "temperature": MANIFEST["sampling"]["temperature"],
        "max_tokens": 4,
        "messages": [
            {"role": "system",
             "content": "You answer with a single capital letter and nothing else."},
            {"role": "user", "content": item.prompt()},
        ],
    }
    request = urllib.request.Request(
        MANIFEST["runtime"]["endpoint"],
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ReaderRefusal(
            f"the pinned endpoint did not answer: {exc}. REFUSING rather than "
            f"scoring a missing answer as wrong.") from None
    text = payload["choices"][0]["message"]["content"].strip()
    return text, time.time() - started


def _letter_of(raw: str) -> str | None:
    """The answer, or None. Prose is NOT an answer.

    The first version scanned for the first A-D character anywhere in the
    reply, so "I am not sure" graded as A — the model's refusal counted as a
    guess, and against a four-way sheet a quarter of those would have scored.
    A reply is an answer only if it IS a letter, optionally with a trailing
    `)` or `.`; anything else is counted as unparsed and reported.
    """
    text = raw.strip().rstrip(").:").strip()
    return text.upper() if len(text) == 1 and text.upper() in _LETTERS else None


def grade(items: list[Item], answers: list[str]) -> dict:
    """Mechanical scoring. A letter, compared. No judgement anywhere."""
    per_arm: dict[str, dict] = {}
    rows = []
    for item, raw in zip(items, answers):
        letter = _letter_of(raw)
        correct = letter is not None and _LETTERS.index(letter) == item.correct
        bucket = per_arm.setdefault(item.arm, {"n": 0, "correct": 0, "unparsed": 0})
        bucket["n"] += 1
        bucket["correct"] += bool(correct)
        bucket["unparsed"] += letter is None
        rows.append({"statement_id": item.statement_id, "arm": item.arm,
                     "raw": raw, "letter": letter, "correct": bool(correct),
                     "expected": _LETTERS[item.correct],
                     "distractor_classes": item.distractor_classes})
    for bucket in per_arm.values():
        bucket["rate"] = round(bucket["correct"] / bucket["n"], 4) if bucket["n"] else 0.0
    return {"per_arm": per_arm, "answers": rows}


def load_rows() -> list[dict]:
    preview = json.loads((DATA / "eligibility_preview.json").read_text(encoding="utf-8"))
    register = json.loads((DATA / "register.json").read_text(encoding="utf-8"))
    return mfv.covered_rows(preview, register)


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def pilot(n_served: int = 35, n_skeleton: int = 15) -> dict:
    """Reproducibility first. A floor is frozen from this, never before it."""
    weights = verify_weights()
    lexicon = fvl.load()
    rule = gp.Rule.load()
    raw = json.loads((DATA / "lexicon.json").read_text(encoding="utf-8"))
    seed_hex = _sha256_lf(DATA / "lexicon.json")
    scrambled, _moved = mfv.scrambled_lexicon(raw, seed_hex)
    items = build_items(load_rows(), lexicon, scrambled, rule,
                        n_served, n_skeleton, seed_hex)

    passes = []
    for _ in range(2):
        answers, elapsed = [], 0.0
        for item in items:
            text, took = ask(item)
            answers.append(text)
            elapsed += took
        passes.append({"answers": answers, "seconds": round(elapsed, 1)})

    identical = passes[0]["answers"] == passes[1]["answers"]
    first = grade(items, passes[0]["answers"])
    served = first["per_arm"].get("served", {})
    skeleton = first["per_arm"].get("skeleton", {})
    return {
        "pilot_id": "foreign_voice.c_v3_prime_pilot.v1",
        "measured": "2026-08-25",
        "control": "C-V3′ — the machine blind reader (PILOT, not the arm)",
        "labelled": "MACHINE-reader throughout. Never a human-reader number.",
        "manifest": MANIFEST,
        "weights": weights,
        "items": len(items),
        "reproducibility": {
            "question": (
                "same inputs, same model, temperature 0 — are two passes "
                "byte-identical? ollama does not guarantee it and this "
                "repository has never tested it, because no seed field exists "
                "anywhere in the tree"
            ),
            "two_passes_byte_identical": identical,
            "disagreements": [
                {"index": i, "first": a, "second": b}
                for i, (a, b) in enumerate(zip(passes[0]["answers"],
                                               passes[1]["answers"])) if a != b
            ],
            "consequence_if_false": (
                "C-V3′ publishes the failure as its result and reverts to "
                "ABSENT — an instrument that cannot repeat itself can only "
                "void, never confirm"
            ),
            "seconds_pass_one": passes[0]["seconds"],
            "seconds_pass_two": passes[1]["seconds"],
        },
        "reading": first["per_arm"],
        "answers": first["answers"],
        "chance_rate": 0.25,
        "arms": {
            "served": "the rendered English sentence, with three mutation-class distractors",
            "skeleton": "the SAME question with the sentence rendered through C-V1's scrambled table, interleaved and unlabelled",
        },
        "inherited_voiding_sentence": (
            "if the skeleton arm is marked determinate at >= half the served "
            "arm's rate, the voice claim is void — the sheet is measuring the "
            "reader's mathematical guesswork, not the rendering"
        ),
        "skeleton_over_served": (
            round(skeleton.get("rate", 0.0) / served["rate"], 4)
            if served.get("rate") else None
        ),
        "floor_is_not_frozen_here": (
            "This is the pilot. A floor derived from it is frozen by a DATED "
            "PREREG ENTRY before the full arm runs, and the full arm is what "
            "the registered run carries."
        ),
        "c_v3_human_is_still_absent": (
            "a machine reader measures whether the sentence determines the "
            "term TO THAT MACHINE, which is a fact about a model and not about "
            "a reader. The human-reader claim stays not-made."
        ),
    }


def arm(n_served: int, n_skeleton: int) -> dict:
    """The full arm, one pass. Reproducibility was settled by the pilot.

    Its floor and its inherited voiding sentence were both frozen in
    `experiments/foreign_voice_prereg2.json` BEFORE this ran, and the pilot's
    reading — which already fires the voiding sentence — is recorded there too,
    so nothing here can be mistaken for a sheet redesigned after seeing a
    number.
    """
    weights = verify_weights()
    lexicon = fvl.load()
    rule = gp.Rule.load()
    raw = json.loads((DATA / "lexicon.json").read_text(encoding="utf-8"))
    seed_hex = _sha256_lf(DATA / "lexicon.json")
    scrambled, _moved = mfv.scrambled_lexicon(raw, seed_hex)
    items = build_items(load_rows(), lexicon, scrambled, rule,
                        n_served, n_skeleton, seed_hex)
    answers, elapsed = [], 0.0
    for item in items:
        text, took = ask(item)
        answers.append(text)
        elapsed += took
    result = grade(items, answers)
    served = result["per_arm"].get("served", {})
    skeleton = result["per_arm"].get("skeleton", {})
    ratio = (round(skeleton.get("rate", 0.0) / served["rate"], 4)
             if served.get("rate") else None)
    prereg = json.loads(
        (REPO_ROOT / "experiments" / "foreign_voice_prereg2.json").read_text(
            encoding="utf-8"))["c_v3_prime"]
    floor = prereg["served_arm_floor"]
    threshold = prereg["inherited_voiding_sentence"]["threshold_ratio"]
    voided = ratio is not None and ratio >= threshold
    return {
        "arm_id": "foreign_voice.c_v3_prime_arm.v1",
        "measured": "2026-08-25",
        "control": "C-V3′ — the machine blind reader (THE ARM)",
        "labelled": "MACHINE-reader throughout. Never a human-reader number.",
        "manifest": MANIFEST,
        "weights": weights,
        "items": len(items),
        "seconds": round(elapsed, 1),
        "reading": result["per_arm"],
        "answers": result["answers"],
        "chance_rate": 0.25,
        "served_arm_floor": floor,
        "served_arm_floor_met": served.get("rate", 0.0) >= floor,
        "skeleton_over_served": ratio,
        "inherited_voiding_sentence": prereg["inherited_voiding_sentence"]["text"],
        "voiding_threshold_ratio": threshold,
        "voided": voided,
        "verdict": "VOID" if voided else "HOLDS",
        "what_a_void_means_here": (
            "the machine-reader claim is NOT MADE. It does not stop the cycle: "
            "C-V3′ is an instrument this cycle bought, not a gate the voice "
            "hangs on, and the voice's fate rests on C-G1 and C-V4′."
        ),
        "c_v3_human_is_still_absent": (
            "and the human-reader claim stays not-made regardless of anything "
            "measured here"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--verify-weights-only", action="store_true")
    parser.add_argument("--served", type=int, default=35)
    parser.add_argument("--skeleton", type=int, default=15)
    parser.add_argument("--out", type=Path, default=DEFAULT_PILOT_OUT)
    args = parser.parse_args(argv)
    try:
        if args.verify_weights_only:
            print(json.dumps(verify_weights(), indent=1))
            return 0
        if args.full:
            prereg = json.loads(
                (REPO_ROOT / "experiments" / "foreign_voice_prereg2.json")
                .read_text(encoding="utf-8"))["c_v3_prime"]["full_arm"]
            report = arm(prereg["served"], prereg["skeleton"])
            args.out = DEFAULT_ARM_OUT if args.out == DEFAULT_PILOT_OUT else args.out
        elif args.pilot:
            report = pilot(args.served, args.skeleton)
        else:
            parser.error("nothing to do: pass --pilot, --full or --verify-weights-only")
    except ReaderRefusal as exc:
        print(f"machine reader refused: {exc}", file=sys.stderr)
        return 2
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    repro = report.get("reproducibility")
    print(f"MACHINE-reader {'pilot' if repro else 'ARM'}: {report['items']} items")
    if repro:
        print(f"  two passes byte-identical: {repro['two_passes_byte_identical']} "
              f"({len(repro['disagreements'])} disagreements)")
    for arm_name, row in sorted(report["reading"].items()):
        print(f"  {arm_name:9} {row['correct']}/{row['n']} = {row['rate']} "
              f"(chance 0.25, unparsed {row['unparsed']})")
    print(f"  skeleton/served ratio: {report['skeleton_over_served']}")
    if "verdict" in report:
        print(f"  served floor {report['served_arm_floor']} met: "
              f"{report['served_arm_floor_met']}")
        print(f"  VERDICT: {report['verdict']} "
              f"(voiding threshold ratio {report['voiding_threshold_ratio']})")
    print(f"written to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
