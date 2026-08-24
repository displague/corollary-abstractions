#!/usr/bin/env python3
"""The registered run: B0a–B0d, B1–B5, and every control's reading.

DESIGN-foreign-voice §10 orders one run at the end of the chain, and this is
the module that performs it.  It writes `experiments/foreign_voice_rate.json`
and **nothing is written unless every digest in
`experiments/foreign_voice_prereg.json` revalidates against the tree first**.
That is B7 with teeth: *"If making the oracle agree requires editing the
lexicon, the interpretation, or the parser, the independence claim is void."*
A run that had to move a frozen artifact does not get to publish a rate.

## What it measures, in the order the design registers

* **B0a** — the transliterable/foreign split under the byte-frozen parser.
  Floor: the residue must be ≥ 2,000 statements.
* **B0b+B0c** — the oracle's reach, **as one measurement**, eligibility by
  outcome.  Floor: ≥ 1,000 accepted.
* **B0d** — the sealed hundred, compared **byte-identically** against
  `data/foreign_voice/b0d_sealed_renderings.json`, then inverted and
  elaborated.  Floor: ≥ 90 of 100 elaborate at all.  Every divergence from the
  seal is **reported, never repaired**, and is classified rather than counted:
  a grammar disagreement and an authoring slip are different findings.
* **B1** — identity over the covered set, ≥ 99.5%, with the composition
  sentence the design and the review both require: *n of N*, the
  `lean_workbook.ground.v1` share, **and the number of distinct elaborated
  terms**, because a rate over 2,313 statements that hold 2,176 distinct terms
  does not cover 2,313 independent facts.
* **B2** — three outcomes, no silent drop.  A FAIL counts against B1; a
  REFUSAL aborts and publishes zero rates.
* **B3** — the five-bucket census closing at 10,605 exactly, with the two
  `registered_blocked_*` buckets **never summed**.
* **B5** — determinism: the whole artifact is produced twice and the bytes
  compared.
* **C-V1** — the skeleton renderer, **one-sided by construction**.
* **C-V2** — the transliteration null, a positive control, plus its rate on
  the transliterable 6,414 reported beside the renderer's on the residue.
* **C-V4** — per the `c_v4` block of the prereg, which replaced §7's pooled
  95% floor with four per-class floors before this file existed.
* **C-V3** — recorded **ABSENT**, with the sentence that gates the claim.

## The one control that cannot run, said out loud

C-V3 is a determinacy sheet marked blind by a **non-maintainer**, and no
adjudicator has been recruited.  There is no way to run it from inside this
process, and a control that quietly does not run is worse than one that
loudly does not.  So the artifact carries `c_v3.status = "absent"` with the
reason, and the claim it alone can license — *that a reader can determinately
recover the mathematics from the English* — is **not made anywhere**, in the
artifact or in the release.  §7's voiding sentence for C-V3 governs a sheet
that ran; this is the case where it did not.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - CLI import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import foreign_voice as fv  # noqa: E402
import foreign_voice_eligibility as fve  # noqa: E402
import foreign_voice_lexicon as fvl  # noqa: E402
import foreign_voice_oracle as fvo  # noqa: E402
import foreign_voice_rule_r as fvr  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
PREREG_PATH = REPO_ROOT / "experiments" / "foreign_voice_prereg.json"
PREVIEW_PATH = REPO_ROOT / "data" / "foreign_voice" / "eligibility_preview.json"
REGISTER_PATH = REPO_ROOT / "data" / "foreign_voice" / "register.json"
SEALED_PATH = REPO_ROOT / "data" / "foreign_voice" / "b0d_sealed_renderings.json"
LEXICON_PATH = REPO_ROOT / "data" / "foreign_voice" / "lexicon.json"
DEFAULT_OUT = REPO_ROOT / "experiments" / "foreign_voice_rate.json"

RUN_ID = "foreign_voice.rate.v1"

B0A_FLOOR = 2000
B0BC_FLOOR = 1000
B0D_FLOOR = 90
B1_FLOOR = 0.995
C_V1_RATIO = 20.0
C_V1_CEILING = 0.01
C_V2_FLOOR = 0.99


class RunRefusal(RuntimeError):
    """The run cannot publish. B2: a refusal is not a data point."""


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


# --------------------------------------------------------------------------
# B7: nothing is written unless every frozen digest still holds
# --------------------------------------------------------------------------


def revalidate(prereg_path: Path = PREREG_PATH) -> dict:
    """Recompute every frozen digest. Raises `RunRefusal` on the first mismatch."""
    prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
    if prereg.get("pending"):
        raise RunRefusal(
            f"the preregistration still lists {len(prereg['pending'])} pending "
            f"artifacts; the run may not precede the things it is gated on")
    checked: dict[str, str] = {}
    for row in prereg["frozen"]:
        path = REPO_ROOT / row["path"]
        if not path.is_file():
            raise RunRefusal(f"B7 VOID: {row['path']} is not in the tree")
        digest = _sha256_lf(path)
        if digest != row["sha256_lf"]:
            raise RunRefusal(
                f"B7 VOID: {row['path']} is {digest[:16]}… and the "
                f"preregistration recorded {row['sha256_lf'][:16]}…. If the "
                f"change was needed to make the oracle agree, the independence "
                f"claim is void and the change needs its own review naming the "
                f"reason. No rate is published.")
        checked[row["path"]] = digest
    return {"prereg_id": prereg["prereg_id"], "revalidated": checked,
            "c_v4": prereg["c_v4"],
            "b1_composition_requirements": prereg["b1_composition_requirements"]}


# --------------------------------------------------------------------------
# The covered set
# --------------------------------------------------------------------------


def covered_rows(preview: dict, register: dict) -> list[dict]:
    """Eligible, minus everything the frozen register already accounts for."""
    blocked = {sid for entry in register["entries"]
               for sid in entry["statement_ids"]}
    return [row for row in preview["statements"]
            if row["accepted"] and row["statement_id"] not in blocked]


# --------------------------------------------------------------------------
# C-V1: the skeleton renderer, one-sided by construction
# --------------------------------------------------------------------------


def _derange(items: list[str], rng: random.Random) -> list[str]:
    """A permutation with no fixed point. v0.18's `_derange`, imported."""
    if len(items) < 2:
        return list(items)
    shuffled = list(items)
    rng.shuffle(shuffled)
    for i, value in enumerate(shuffled):
        if value == items[i]:
            j = (i + 1) % len(shuffled)
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    for i, value in enumerate(shuffled):
        if value == items[i]:
            j = i - 1
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    return shuffled


def scrambled_lexicon(raw: dict, seed_hex: str) -> tuple[fvl.ForeignLexicon, dict]:
    """A WRONG table that is still a legal one, for the one-sided control.

    Deranging *within* each section preserves the section's phrase multiset, so
    the scrambled table is still injective both ways, still prefix-free and
    still numeral-disjoint — it loads through the same F1–F8 gate the committed
    table does. The control is a wrong table, not a broken one.

    Grouping words are deliberately untouched. A scramble that also broke
    parenthesisation would fail in the pinned binary's parser and prove nothing
    about whether the gate reads the WORDS.

    **One-sided by construction**: the surface is produced with this table and
    read back through the COMMITTED one. v0.18 measured why — a two-sided
    scramble is a consistent renaming, still a bijection, and round-trips
    near-perfectly, so it would void the reading for a reason that has nothing
    to do with whether the gate reads the words.
    """
    rng = random.Random(int(seed_hex[:16], 16))
    doc = json.loads(json.dumps(raw))
    moved: dict[str, int] = {}
    for section in ("binders", "connectives", "relations", "operators", "types"):
        keys = sorted(doc[section])
        phrases = [doc[section][key] for key in keys]
        deranged = _derange(phrases, rng)
        for key, phrase in zip(keys, deranged):
            doc[section][key] = phrase
        moved[section] = sum(1 for a, b in zip(phrases, deranged) if a != b)
    return fvl.build(doc, "<scrambled>"), moved


# --------------------------------------------------------------------------
# C-V4: the mutations, per the preregistered block
# --------------------------------------------------------------------------


def _admits(surface: str, mutation: str, lexicon: fvl.ForeignLexicon) -> bool:
    words = surface.split()
    slots = [i for i, w in enumerate(words) if w == lexicon.slot_word]
    if mutation == "drop_binder":
        return len(slots) >= 2 and words[0:2] == lexicon.words_for("∀").split()
    if mutation == "swap_binder":
        return _preamble_slots(words, lexicon) >= 2
    if mutation == "drop_ascription":
        return lexicon.words_for(":") in surface
    if mutation in {"drop_group", "shift_group"}:
        return lexicon.words_for("(") in surface
    raise ValueError(mutation)


def _preamble_slots(words: list[str], lexicon: fvl.ForeignLexicon) -> int:
    """How many `variable <n>` pairs stand before the `of type` phrase."""
    ascription = lexicon.words_for(":").split()
    stop = len(words)
    for i in range(len(words) - len(ascription) + 1):
        if words[i:i + len(ascription)] == ascription:
            stop = i
            break
    return sum(1 for w in words[:stop] if w == lexicon.slot_word)


def mutate(surface: str, mutation: str, lexicon: fvl.ForeignLexicon) -> str:
    """Exactly ONE mechanical mutation to the rendered English.

    Never to R(s) and never to the inverse output: the question C-V4 asks is
    whether the SENTENCE determines the term.
    """
    words = surface.split()
    if mutation == "drop_binder":
        index = next(i for i, w in enumerate(words) if w == lexicon.slot_word)
        return " ".join(words[:index] + words[index + 2:])
    if mutation == "swap_binder":
        ascription = lexicon.words_for(":").split()
        stop = next(i for i in range(len(words) - len(ascription) + 1)
                    if words[i:i + len(ascription)] == ascription)
        positions = [i for i, w in enumerate(words[:stop])
                     if w == lexicon.slot_word]
        first, second = positions[0], positions[1]
        out = list(words)
        out[first + 1], out[second + 1] = out[second + 1], out[first + 1]
        return " ".join(out)
    if mutation == "drop_ascription":
        phrase = lexicon.words_for(":").split()
        index = next(i for i in range(len(words) - len(phrase) + 1)
                     if words[i:i + len(phrase)] == phrase)
        # the phrase plus the type word it introduces
        return " ".join(words[:index] + words[index + len(phrase) + 1:])
    if mutation == "drop_group":
        opening = lexicon.words_for("(").split()
        closing = lexicon.words_for(")").split()
        text = " ".join(words)
        text = text.replace(" ".join(opening) + " ", "", 1)
        text = text.replace(" " + " ".join(closing), "", 1)
        return " ".join(text.split())
    if mutation == "shift_group":
        closing = " ".join(lexicon.words_for(")").split())
        index = surface.find(closing)
        if index == -1:
            raise ValueError("no grouping word to shift")
        head = surface[:index].rstrip()
        tail = surface[index + len(closing):].strip()
        following = tail.split()
        if not following:
            raise ValueError("nothing after the grouping word to shift past")
        return " ".join([head, following[0], closing, *following[1:]])
    raise ValueError(mutation)


# --------------------------------------------------------------------------
# The run
# --------------------------------------------------------------------------


def _plan(seed_hex: str, rows: list[dict], lexicon: fvl.ForeignLexicon,
          sample_size: int, mutations: list[dict]) -> dict[str, list[dict]]:
    """C-V4's samples, drawn by the preregistered seeded rule."""
    rendered: dict[str, str] = {}
    for row in rows:
        got = fv.render_interpreted(row["interpreted"], lexicon)
        if isinstance(got, fv.Rendering):
            rendered[row["statement_id"]] = got.surface
    plan: dict[str, list[dict]] = {}
    for mutation in mutations:
        name = mutation["name"]
        pool = sorted(row["statement_id"] for row in rows
                      if row["statement_id"] in rendered
                      and _admits(rendered[row["statement_id"]], name, lexicon))
        shuffled = list(pool)
        random.Random(int(seed_hex[:16], 16)).shuffle(shuffled)
        plan[name] = [{"statement_id": sid, "admitting": len(pool)}
                      for sid in sorted(shuffled[:sample_size])]
    return plan


def dry_run(out: Path = DEFAULT_OUT) -> dict:
    """Everything except the corpus-scale oracle calls. Safe to run any time.

    It revalidates the freeze list, loads every artifact, builds the covered
    set, constructs the C-V1 scrambled table through the real F1–F8 gate, draws
    every C-V4 sample, and confirms the oracle resolves — then stops. A runner
    whose readiness can only be established by running it is a runner nobody
    can check before the one run they get.
    """
    validated = revalidate()
    preview = json.loads(PREVIEW_PATH.read_text(encoding="utf-8"))
    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    sealed = json.loads(SEALED_PATH.read_text(encoding="utf-8"))
    raw = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
    lexicon = fvl.load()
    rows = covered_rows(preview, register)

    seed_hex = _sha256_lf(LEXICON_PATH)
    scrambled, moved = scrambled_lexicon(raw, seed_hex)
    c_v4 = validated["c_v4"]
    plan = _plan(seed_hex, rows, lexicon, c_v4["sample_size"], c_v4["mutations"])

    # The renderer over the whole covered set, without the oracle: this is what
    # B1's denominator will actually be, and a dry run that did not compute it
    # would be reporting a plan for a set it had not looked at.
    refusals: Counter = Counter()
    surfaces = 0
    for row in rows:
        got = fv.render_interpreted(row["interpreted"], lexicon)
        if isinstance(got, fv.Refusal):
            refusals[got.reason] += 1
        else:
            surfaces += 1

    oracle_ready = True
    oracle_reason = ""
    try:
        fvo.load()
    except fvo.OracleRefusal as exc:
        oracle_ready = False
        oracle_reason = str(exc)

    return {
        "dry_run": True,
        "prereg_revalidated": len(validated["revalidated"]),
        "out_path_exists": out.exists(),
        "covered_statements": len(rows),
        "renderable_now": surfaces,
        "renderer_refusals": dict(refusals),
        "sealed_hundred": len(sealed["renderings"]),
        "c_v1_scramble_moved": moved,
        "c_v1_scrambled_table_loads": scrambled.lexicon_id == "<unnamed>"
                                      or bool(scrambled.key_to_phrase),
        "c_v4_samples": {name: {"drawn": len(sample),
                                "admitting": sample[0]["admitting"] if sample else 0}
                         for name, sample in plan.items()},
        "oracle_ready": oracle_ready,
        "oracle_reason": oracle_reason,
        "would_write": out.relative_to(REPO_ROOT).as_posix(),
    }


# --------------------------------------------------------------------------
# B0d: the sealed hundred, compared byte-identically
# --------------------------------------------------------------------------


def b0d(oracle: fvo.Oracle, lexicon: fvl.ForeignLexicon, rule: fvr.RuleR,
        sealed: dict, batch_size: int) -> dict:
    """The real probe. Divergences from the seal are REPORTED, never repaired.

    A divergence is CLASSIFIED rather than counted, because the seal's own
    file says what it did and did not check: every word was swept against the
    lexicon and the numeral pair, the token SEQUENCE was not. So a divergence
    is either a grammar disagreement — the implementation and the author read
    the table differently — or an authoring slip, and those are different
    findings about different things.
    """
    rendered: list[tuple[str, str, str]] = []
    divergences: list[dict] = []
    refused: list[dict] = []
    for row in sealed["renderings"]:
        got = fv.render_interpreted(row["interpreted"], lexicon,
                                    source=row["source"],
                                    statement_id=row["statement_id"])
        if isinstance(got, fv.Refusal):
            refused.append({"statement_id": row["statement_id"],
                            "reason": got.reason, "detail": got.detail,
                            "sealed_predicted": row["predicted"]})
            continue
        if got.surface != row["surface"]:
            divergences.append({
                "statement_id": row["statement_id"],
                "sealed": row["surface"],
                "rendered": got.surface,
                "classification": _classify_divergence(
                    row["surface"], got.surface, lexicon),
            })
        rendered.append((row["statement_id"], got.surface, row["interpreted"]))

    terms: list[tuple[str, str]] = []
    inverses: dict[str, str] = {}
    for index, (statement_id, surface, _interpreted) in enumerate(rendered):
        try:
            inverse = fv.delexicalize(surface, lexicon)
        except fv.ForeignVoiceError as exc:
            inverses[statement_id] = ""
            divergences.append({"statement_id": statement_id,
                                "classification": "inverse_refused",
                                "detail": str(exc)})
            continue
        inverses[statement_id] = rule.apply(inverse).text
        terms.append((f"d{index}", inverses[statement_id]))

    answers = oracle.serialize(terms, batch_size=batch_size) if terms else {}
    elaborated = sum(1 for row in answers.values() if row.ok)
    failures = [{"statement_id": rendered[int(tag[1:])][0], "error": row.error}
                for tag, row in sorted(answers.items()) if not row.ok]

    return {
        "gate": "B0d — the inverse direction, unpreviewed and the real probe",
        "sealed": len(sealed["renderings"]),
        "reproduced_byte_identically": len(rendered) - len(
            [d for d in divergences if "rendered" in d]),
        "divergences": divergences,
        "divergence_count": len(divergences),
        "refused_though_sealed_as_rendered": refused,
        "inverted_and_elaborated": elaborated,
        "elaboration_failures": failures,
        "floor": B0D_FLOOR,
        "floor_met": elaborated >= B0D_FLOOR,
        "divergences_are_reported_never_repaired": (
            "the seal is a prediction; a divergence is a finding about the "
            "grammar or about the authoring, and editing the seal to agree "
            "would delete the finding"
        ),
    }


def _classify_divergence(sealed: str, rendered: str,
                         lexicon: fvl.ForeignLexicon) -> str:
    """Grammar disagreement, or authoring slip? Different findings."""
    a, b = sealed.split(), rendered.split()
    if len(a) == len(b):
        differing = [(x, y) for x, y in zip(a, b) if x != y]
        if all(x in {w for p in lexicon.phrase_to_token for w in p}
               and y in {w for p in lexicon.phrase_to_token for w in p}
               for x, y in differing):
            return "grammar_disagreement_same_length"
        return "same_length_different_words"
    return "different_length"


# --------------------------------------------------------------------------
# B1 / B2 / B3
# --------------------------------------------------------------------------


def b1(oracle: fvo.Oracle, lexicon: fvl.ForeignLexicon, rule: fvr.RuleR,
       rows: list[dict], batch_size: int) -> dict:
    """Identity over the covered set, with the composition sentence's three parts."""
    renderings: list[fv.Rendering] = []
    refusals: Counter = Counter()
    for row in rows:
        got = fv.render_interpreted(row["interpreted"], lexicon,
                                    source=row["source"],
                                    statement_id=row["statement_id"])
        if isinstance(got, fv.Refusal):
            refusals[got.reason] += 1
        else:
            renderings.append(got)

    receipts = fv.gate(renderings, oracle, rule, lexicon, batch_size=batch_size)
    outcomes = Counter(receipt.outcome for receipt in receipts)
    served = outcomes["identity"]
    corpus_of = {row["statement_id"]: row["corpus"] for row in rows}
    served_corpora = Counter(
        corpus_of[receipt.rendering.statement_id] for receipt in receipts
        if receipt.outcome == "identity")
    distinct = len({receipt.orig_elab_digest for receipt in receipts
                    if receipt.orig_elab_digest})
    lean_workbook = served_corpora.get("lean_workbook", 0)

    per_corpus = {}
    for corpus, count in sorted(served_corpora.items()):
        per_corpus[corpus] = {
            "served": count,
            "thin_denominator": count < 50,
            "note": ("fewer than 50 covered statements: reported individually "
                     "with every failure named, never averaged"
                     if count < 50 else ""),
        }

    return {
        "gate": "B1 — identity floor",
        "covered": len(rows),
        "rendered": len(renderings),
        "renderer_refusals": dict(refusals),
        "served": served,
        "rate_over_covered": _rate(served, len(rows)),
        "rate_over_rendered": _rate(served, len(renderings)),
        "floor": B1_FLOOR,
        "floor_met": _rate(served, len(renderings)) >= B1_FLOOR,
        "outcomes": dict(outcomes),
        "failures": [
            {"statement_id": receipt.rendering.statement_id,
             "outcome": receipt.outcome,
             "orig_error": receipt.orig_error, "rt_error": receipt.rt_error,
             "surface": receipt.rendering.surface,
             "roundtrip_text": receipt.roundtrip_text}
            for receipt in receipts if receipt.outcome != "identity"
        ],
        "composition": {
            "statements": len(renderings),
            "distinct_elaborated_terms": distinct,
            "lean_workbook_served": lean_workbook,
            "lean_workbook_share": _rate(lean_workbook, served),
            "per_corpus": per_corpus,
            "required_sentence": (
                f"{served} of {len(rows)} covered statements, holding "
                f"{distinct} distinct elaborated terms, of which "
                f"{_rate(lean_workbook, served) * 100:.1f}% is "
                f"lean_workbook.ground.v1"
            ),
            "why_all_three": (
                "the design requires n-of-N and the corpus share; the review "
                "added the distinct-term count, because a rate over statements "
                "that share terms does not cover as many independent facts as "
                "its denominator suggests"
            ),
        },
        "identity_is_bounded": (
            "up to what elaboration erases and what rule R's preamble "
            "regenerates; C-V4 below is the measured bound and no sentence "
            "quoting this rate may omit it"
        ),
        "receipts": [receipt.as_dict() for receipt in receipts],
    }


def b3(preview: dict, register: dict, b1_result: dict) -> dict:
    """The five buckets, closing exactly, with the two blocked ones kept apart."""
    totals = preview["b0a"]["totals"]
    census = register["b3_census"]
    served = b1_result["served"]
    failed = b1_result["covered"] - served
    total = (totals["transliterable"] + served + failed
             + census[_MATHLIB] + census[_NO_ROW])
    return {
        "gate": "B3 — rendered or registered, and the arithmetic closes",
        "transliterable": totals["transliterable"],
        "covered_served": served,
        "covered_failed": failed,
        _MATHLIB: census[_MATHLIB],
        _NO_ROW: census[_NO_ROW],
        "total": total,
        "must_equal": totals["mute"],
        "closes_exactly": total == totals["mute"],
        "never_summed": (
            "the two registered_blocked_* buckets are reported separately: the "
            "first is a budget consequence the maintainer can lift and the "
            "second is a design consequence this cycle owns"
        ),
    }


_MATHLIB = "registered_blocked_mathlib_head"
_NO_ROW = "registered_blocked_no_row"


# --------------------------------------------------------------------------
# The controls
# --------------------------------------------------------------------------


def c_v1(oracle: fvo.Oracle, lexicon: fvl.ForeignLexicon,
         scrambled: fvl.ForeignLexicon, moved: dict, rule: fvr.RuleR,
         rows: list[dict], b1_identity: dict[str, bool],
         batch_size: int) -> dict:
    """Rendered with a WRONG table, read back through the COMMITTED one.

    The **failure-mode split** is what makes this control readable rather than
    merely low. A skeleton rate of zero has two entirely different meanings and
    §7's voiding sentence turns on which one it is:

    * zero because every scrambled sentence **elaborated to a different term** —
      the gate is reading the words and the control has done its job;
    * zero because every scrambled sentence **failed to elaborate at all** —
      the pinned binary never got to compare two terms, and *"both are near
      zero, the gate is untested and the reading is void"*.

    So the non-identity outcomes are split four ways: the scrambled table
    refused to render, the literal inverse refused to read it back, the binary
    refused to elaborate it, or it elaborated to a different digest.

    The contrast is computed **on the same statement set**, because §7 says
    *"the true renderer's identity rate on the same statement set"* and a ratio
    between two different denominators is not a ratio.
    """
    terms: list[tuple[str, str]] = []
    attempted: list[str] = []
    renderer_refused: Counter = Counter()
    inverse_refused = 0
    for index, row in enumerate(rows):
        got = fv.render_interpreted(row["interpreted"], scrambled)
        if isinstance(got, fv.Refusal):
            renderer_refused[got.reason] += 1
            continue
        try:
            inverse = fv.delexicalize(got.surface, lexicon)
        except fv.ForeignVoiceError:
            inverse_refused += 1
            continue
        attempted.append(row["statement_id"])
        terms.append((f"o{index}", row["interpreted"]))
        terms.append((f"s{index}", rule.apply(inverse).text))
    answers = oracle.serialize(terms, batch_size=batch_size) if terms else {}

    identical = differed = elaboration_failed = orig_failed = 0
    for index, row in enumerate(rows):
        orig, scram = answers.get(f"o{index}"), answers.get(f"s{index}")
        if orig is None or scram is None:
            continue
        if not orig.ok:
            orig_failed += 1
        elif not scram.ok:
            elaboration_failed += 1
        elif orig.digest == scram.digest:
            identical += 1
        else:
            differed += 1

    rate = _rate(identical, len(attempted))
    true_identity = sum(1 for sid in attempted if b1_identity.get(sid))
    true_rate = _rate(true_identity, len(attempted))
    ratio = round(true_rate / rate, 3) if rate else None
    both_near_zero = rate <= C_V1_CEILING and true_rate <= C_V1_CEILING
    ratio_short = ratio is not None and ratio < C_V1_RATIO
    voided = rate > C_V1_CEILING or both_near_zero or ratio_short
    if rate > C_V1_CEILING:
        void_reason = ("the skeleton renderer cleared the ceiling: the gate is "
                       "not reading the words")
    elif both_near_zero:
        void_reason = "both rates are near zero: the gate is untested"
    elif ratio_short:
        void_reason = "the ratio is below the required multiple"
    else:
        void_reason = ""
    return {
        "control": "C-V1 — the skeleton renderer, one-sided by construction",
        "one_sided": (
            "produced with the scrambled table, read back through the "
            "committed one. v0.18 measured why: a two-sided scramble is a "
            "consistent renaming, still a bijection, and round-trips "
            "near-perfectly, so it would void the reading for a reason that "
            "has nothing to do with whether the gate reads the words"
        ),
        "scramble_seed_source": "data/foreign_voice/lexicon.json",
        "phrases_moved": moved,
        "covered_offered": len(rows),
        "attempted": len(attempted),
        "identity": identical,
        "rate": rate,
        "failure_modes": {
            "scrambled_renderer_refused": dict(renderer_refused),
            "scrambled_renderer_refused_total": sum(renderer_refused.values()),
            "inverse_refused": inverse_refused,
            "original_failed_to_elaborate": orig_failed,
            "scrambled_failed_to_elaborate": elaboration_failed,
            "elaborated_to_a_different_digest": differed,
            "reading": (
                "a skeleton rate of zero means the control worked ONLY if the "
                "misses are `elaborated_to_a_different_digest`. If they are "
                "`scrambled_failed_to_elaborate`, the pinned binary never got "
                "to compare two terms and the gate is untested"
            ),
        },
        "contrast_on_the_same_statement_set": {
            "statements": len(attempted),
            "true_renderer_identity": true_identity,
            "true_renderer_identity_rate": true_rate,
            "skeleton_identity": identical,
            "skeleton_identity_rate": rate,
            "ratio": ratio,
            "ratio_required": C_V1_RATIO,
            "note": ("§7 compares against the true renderer's rate ON THE SAME "
                     "STATEMENT SET, so this is not B1's headline denominator"),
        },
        "voiding": (
            f"informative only if the true renderer's rate is >= {C_V1_RATIO}x "
            f"this one; if this clears {C_V1_CEILING}, the gate is not reading "
            f"the words and the reading is void; if both are near zero the gate "
            f"is untested and the reading is void"
        ),
        "voided": voided,
        "void_reason": void_reason,
    }


def c_v2(oracle: fvo.Oracle, rule: fvr.RuleR, covered: list[dict],
         transliterable: list[dict], batch_size: int) -> dict:
    """The transliteration null: no English in it at all, and it must pass.

    Its second job is to keep Correction 1 honest in public — the null's rate
    on the TRANSLITERABLE half is reported beside the renderer's rate on the
    residue, so a reader can see that the easy half was declined rather than
    counted.
    """
    def _null(rows: list[dict], prefix: str, interpret: bool) -> dict:
        terms: list[tuple[str, str]] = []
        for index, row in enumerate(rows):
            text = (rule.apply(fve.transliterate(row["source"])).text
                    if interpret else row["interpreted"])
            terms.append((f"{prefix}a{index}", text))
            terms.append((f"{prefix}b{index}", text))
        answers = oracle.serialize(terms, batch_size=batch_size) if terms else {}
        elaborated = sum(1 for index in range(len(rows))
                         if answers[f"{prefix}a{index}"].ok)
        identical = sum(
            1 for index in range(len(rows))
            if answers[f"{prefix}a{index}"].ok
            and answers[f"{prefix}a{index}"].digest
            == answers[f"{prefix}b{index}"].digest)
        return {"statements": len(rows), "elaborated": elaborated,
                "identity": identical,
                "elaboration_rate": _rate(elaborated, len(rows)),
                "identity_rate_over_elaborated": _rate(identical, elaborated)}

    over_covered = _null(covered, "c", False)
    over_transliterable = _null(transliterable, "t", True)
    rate = over_covered["identity_rate_over_elaborated"]
    return {
        "control": "C-V2 — the transliteration null, a positive control",
        "over_covered": over_covered,
        "over_transliterable": over_transliterable,
        "floor": C_V2_FLOOR,
        "voided": rate < C_V2_FLOOR,
        "voiding": (
            f"if the null does not reach {C_V2_FLOOR} identity, the harness — "
            f"not the renderer — is what the run measured, and every other "
            f"reading in this artifact is void"
        ),
        "the_easy_half_was_not_counted": (
            "the transliterable statements are reported here and NOWHERE in "
            "B1. If they are ever counted inside a foreign-voice rate, that "
            "rate is wrong"
        ),
    }


def c_v4(oracle: fvo.Oracle, lexicon: fvl.ForeignLexicon, rule: fvr.RuleR,
         rows: list[dict], block: dict, plan: dict[str, list[dict]],
         batch_size: int) -> dict:
    """Per the preregistered block: per-class floors, FVERR counts as differing."""
    by_id = {row["statement_id"]: row for row in rows}
    results: dict[str, dict] = {}
    voided: list[str] = []
    for mutation in block["mutations"]:
        name = mutation["name"]
        sample = plan[name]
        terms: list[tuple[str, str]] = []
        keep: list[str] = []
        inverse_refused = 0
        no_op = 0
        for index, entry in enumerate(sample):
            row = by_id[entry["statement_id"]]
            base = fv.render_interpreted(row["interpreted"], lexicon)
            if isinstance(base, fv.Refusal):
                continue
            try:
                mutated = mutate(base.surface, name, lexicon)
            except (ValueError, StopIteration):
                continue
            if mutated == base.surface:
                # A no-op mutation would score as "did not detect" and flatter
                # the control by shrinking its rate for a reason that is not
                # about blindness. Dropped from the denominator, and COUNTED,
                # because a control whose sample quietly shrinks is a control
                # nobody can read.
                no_op += 1
                continue
            try:
                inverse = rule.apply(fv.delexicalize(mutated, lexicon)).text
            except fv.ForeignVoiceError:
                # The inverse refused: the mutant is DETECTED, and by the
                # TRUSTED half rather than by the oracle. It never reaches a
                # digest, so it is counted here and not sent.
                inverse_refused += 1
                keep.append(entry["statement_id"])
                continue
            keep.append(entry["statement_id"])
            terms.append((f"{name[:4]}m{index}", inverse))
            terms.append((f"{name[:4]}o{index}", row["interpreted"]))
        answers = oracle.serialize(terms, batch_size=batch_size) if terms else {}

        differed = fverr = same = 0
        for index in range(len(sample)):
            mutant = answers.get(f"{name[:4]}m{index}")
            original = answers.get(f"{name[:4]}o{index}")
            if mutant is None or original is None:
                continue
            if not mutant.ok:
                fverr += 1
                differed += 1
            elif mutant.digest != original.digest:
                differed += 1
            else:
                same += 1
        differed += inverse_refused
        denominator = differed + same
        rate = _rate(differed, denominator)
        row_out = {
            "sample_size": denominator,
            "no_op_mutations_dropped": no_op,
            "of_which_the_inverse_refused": inverse_refused,
            "admitting": sample[0]["admitting"] if sample else 0,
            "differed": differed,
            "of_which_fverr": fverr,
            "of_which_digest_moved": differed - fverr,
            "did_not_differ": same,
            "rate": rate,
            "threshold": mutation["threshold"],
            "in_voiding_pool": mutation["in_voiding_pool"],
        }
        if mutation.get("blind_by_construction"):
            row_out["blind_by_construction"] = True
            row_out["reading"] = (
                "the preamble rule regenerates what this mutation deletes, so "
                "B1 cannot see it. This number IS the measured boundary of "
                "what B1 cannot see — the §8 non-claim made quantitative — and "
                "it is excluded from the voiding pool by preregistration"
            )
            row_out["expectation_from_the_review_audit"] = (
                block["drop_binder_is_blind_by_construction"]
                ["expectation_carried_from_the_review_audit"])
        elif mutation["threshold"] is not None and rate < mutation["threshold"]:
            voided.append(name)
        results[name] = row_out

    return {
        "control": "C-V4 — the near-miss null",
        "preregistered_in": "experiments/foreign_voice_prereg.json (`c_v4`)",
        "an_fverr_counts_as_differing": True,
        "why": (
            "a mutation that breaks elaboration IS DETECTED; counting it as "
            "'no difference' would score the control against itself. The two "
            "sub-counts are reported separately anyway"
        ),
        "per_class": results,
        "voided_classes": voided,
        "voided": bool(voided),
        "voiding": (
            "any class in the voiding pool below its 0.90 floor voids the C-V4 "
            "reading and, through it, the sentence B1 is allowed to make. The "
            "design's pooled 95% floor was replaced by these four per-class "
            "floors before this file existed"
        ),
    }


def c_v3_absent() -> dict:
    """The control that could not run, recorded loudly."""
    return {
        "control": "C-V3 — the determinacy sheet",
        "status": "absent",
        "reason": (
            "C-V3 requires thirty rendered statements on a pre-registered "
            "sheet marked blind by a NON-MAINTAINER, with fifteen C-V1 "
            "skeleton outputs interleaved unlabelled. No adjudicator was "
            "recruited, and nothing inside this process can stand in for one"
        ),
        "consequence": (
            "the claim C-V3 alone can license — that a reader can recover the "
            "mathematics DETERMINATELY from the English — is NOT MADE, here or "
            "in the release. This artifact claims only that the English "
            "determines the term to the pinned elaborator, which is a claim "
            "about a machine and not about a reader"
        ),
        "also_not_claimed": (
            "readability, fluency, or translation quality. §8: 'Not fluency, "
            "and not translation quality. The sentences are invertible; their "
            "style is whatever the lexicon produces'"
        ),
        "unpark_trigger": (
            "a non-maintainer adjudicator and a sheet pre-registered before "
            "the statements are drawn. The 15-item control arm is flagged in "
            "the design as sub-threshold and advisory: at n=15 it can only "
            "ever VOID, never confirm"
        ),
    }


# --------------------------------------------------------------------------
# The run
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# The verdicts: every gate adjudicated against the design's own sentence
# --------------------------------------------------------------------------


def verdicts(result: dict) -> dict:
    """FIRES / MISSES / VOID per gate, decided in the artifact rather than in prose.

    A run that reports numbers and leaves the adjudication to whoever writes
    the release is a run whose verdict can drift from its data. So the artifact
    carries the design's §6 and §7 sentences beside each reading and says which
    way each one went.

    The ordering matters and is the design's: a VOID control voids the reading
    it gates, so C-V1, C-V2 and C-V4 going void makes B1's rate unquotable even
    if B1's own floor was cleared. `overall` says so.
    """
    def gate(name: str, sentence: str, met: bool, reading: str) -> dict:
        return {"gate": name, "sentence": sentence,
                "verdict": "FIRES" if met else "MISSES", "reading": reading}

    def control(name: str, sentence: str, void: bool, reading: str,
                reason: str = "") -> dict:
        out = {"control": name, "sentence": sentence,
               "verdict": "VOID" if void else "HOLDS", "reading": reading}
        if void and reason:
            out["void_reason"] = reason
        return out

    b0a, b0bc, b0d_ = result["b0a"], result["b0bc"], result["b0d"]
    b1_, b3_ = result["b1"], result["b3"]
    cv1, cv2, cv4 = result["c_v1"], result["c_v2"], result["c_v4"]

    rows = [
        gate("B-P", "the Lean-side serializer exists, runs under the hermetic "
                    "rule, and its tests assert binder-name independence and "
                    "byte-identical output across two runs",
             True,
             "discharged before B0 froze; the prototype's two retained pairs "
             "reproduce at 475 and 2,627 characters"),
        gate("B0a", "the foreign residue must be >= 2,000 statements, or the "
                    "claim has no territory and the cycle stops",
             b0a["floor_met"],
             f"{b0a['totals']['residue']} residue of {b0a['totals']['mute']} "
             f"mute ({b0a['totals']['transliterable']} transliterable)"),
        gate("B0b+B0c", "at least 1,000 accepted, or the oracle cannot reach "
                        "enough of the residue to gate anything",
             b0bc["floor_met"],
             f"{b0bc['accepted']} accepted of {b0bc['residue']}"),
        gate("B0d", ">= 90 of 100 must elaborate at all — identity is B1's "
                    "business; B0d only asks whether the inverse produces Lean",
             b0d_["floor_met"],
             f"{b0d_['inverted_and_elaborated']} of {b0d_['sealed']} elaborated; "
             f"{b0d_['divergence_count']} divergences from the seal"),
        gate("B1", ">= 99.5% of the covered set, both digests recomputed in the run",
             b1_["floor_met"],
             b1_["composition"]["required_sentence"]),
        gate("B2", "the oracle's three outcomes are distinguished and none is a "
                   "silent drop; a REFUSAL aborts and publishes zero rates",
             True,
             f"outcomes {b1_['outcomes']}; the run completed, so no refusal fired"),
        gate("B3", "the five buckets must close at 10,605 exactly; any statement "
                   "in none of them is a bug in the census",
             b3_["closes_exactly"],
             f"{b3_['transliterable']} + {b3_['covered_served']} + "
             f"{b3_['covered_failed']} + {b3_[_MATHLIB]} + {b3_[_NO_ROW]} = "
             f"{b3_['total']}"),
        gate("B4", "the register is committed with its blocked_set_digest "
                   "BEFORE anything is rendered",
             True,
             "frozen in commit 297d1ea, before scripts/foreign_voice.py existed; "
             "checked against the git history by tests/git_ordering.py"),
        gate("B5", "two full runs on one tree produce byte-identical artifacts",
             result.get("b5", {}).get("byte_identical", False),
             str(result.get("b5", {}))),
        gate("B6", "nothing in the render path, the inverse, rule R or the "
                   "register is learned",
             not result["b6"]["learned_components"],
             "no learned component; §9 closes the seat in writing"),
        gate("B7", "every frozen digest revalidates, or the independence claim "
                   "is void and no rate is published",
             len(result["prereg_revalidated"]) > 0,
             f"{len(result['prereg_revalidated'])} artifacts revalidated "
             f"before anything was measured"),
    ]

    controls = [
        control("C-V1",
                "informative only if the true renderer's identity rate on the "
                "same statement set is >= 20x the skeleton renderer's; if the "
                "skeleton renderer clears 1%, the gate is not reading the words "
                "and is void; if both are near zero, the gate is untested and "
                "the reading is void",
                cv1["voided"],
                f"skeleton {cv1['rate']} vs true "
                f"{cv1['contrast_on_the_same_statement_set']['true_renderer_identity_rate']} "
                f"over {cv1['attempted']} statements, ratio "
                f"{cv1['contrast_on_the_same_statement_set']['ratio']}; misses split "
                f"{cv1['failure_modes']['elaborated_to_a_different_digest']} "
                f"different-digest / "
                f"{cv1['failure_modes']['scrambled_failed_to_elaborate']} "
                f"failed-to-elaborate",
                cv1["void_reason"]),
        control("C-V2",
                "if the null does not reach >= 99% identity, the harness — not "
                "the renderer — is what the run measured, and every other "
                "reading in the artifact is void",
                cv2["voided"],
                f"null over covered "
                f"{cv2['over_covered']['identity_rate_over_elaborated']} "
                f"({cv2['over_covered']['identity']} of "
                f"{cv2['over_covered']['elaborated']} elaborated); over the "
                f"transliterable {cv2['over_transliterable']['statements']}: "
                f"elaboration {cv2['over_transliterable']['elaboration_rate']}, "
                f"identity "
                f"{cv2['over_transliterable']['identity_rate_over_elaborated']}"),
        {
            "control": "C-V3",
            "sentence": "if the skeleton control is marked determinate at >= "
                        "half the true renderer's rate, the voice claim is void",
            "verdict": "ABSENT",
            "reading": result["c_v3"]["consequence"],
        },
        control("C-V4",
                "per-class floors at 0.90, registered before this instrument "
                "existed, replacing §7's pooled 95%; drop_binder is blind by "
                "construction and excluded from the voiding pool",
                cv4["voided"],
                "; ".join(
                    f"{name} {row['rate']} ({row['differed']}/{row['sample_size']})"
                    for name, row in sorted(cv4["per_class"].items())),
                ", ".join(cv4["voided_classes"])),
    ]

    missed = [row["gate"] for row in rows if row["verdict"] == "MISSES"]
    void = [row["control"] for row in controls if row["verdict"] == "VOID"]
    if void:
        overall = "VOID"
        summary = (f"{', '.join(void)} fired a voiding sentence, so B1's rate "
                   f"is not quotable regardless of its own floor")
    elif missed:
        overall = "MISSES"
        summary = f"{', '.join(missed)} missed its floor"
    else:
        overall = "FIRES"
        summary = ("every gate cleared its floor and no control fired a voiding "
                   "sentence; C-V3 is ABSENT and the claim it alone licenses "
                   "is not made")
    return {"gates": rows, "controls": controls, "missed": missed,
            "voided": void, "overall": overall, "summary": summary,
            "how_to_read_this": (
                "a VOID control voids the reading it gates, so a voided control "
                "outranks a cleared B1 floor. A published miss is a result: the "
                "artifact is committed either way and nothing is re-run or tuned"
            )}


def measure(batch_size: int = 300) -> dict:
    """Every gate and every control, as one deterministic dict.

    Deterministic by construction: no timestamps, no wall-clock, no absolute
    paths, corpus iteration sorted, and every sample seeded from a committed
    digest. B5 runs this twice and compares the bytes.
    """
    validated = revalidate()
    preview_now = fve.preview(REPO_ROOT / "data",
                              REPO_ROOT / "prover" / "lean" / "normalizer" /
                              "lean-toolchain", batch_size=150)
    preview = json.loads(PREVIEW_PATH.read_text(encoding="utf-8"))
    register = json.loads(REGISTER_PATH.read_text(encoding="utf-8"))
    sealed = json.loads(SEALED_PATH.read_text(encoding="utf-8"))
    raw = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
    lexicon = fvl.load()
    rule = fvr.load()
    oracle = fvo.load()

    if preview_now["b0a"]["totals"] != preview["b0a"]["totals"]:
        raise RunRefusal(
            "B0a recomputed differently than the committed preview; the "
            "denominator moved under the claim and no rate is published")

    rows = covered_rows(preview, register)
    transliterable = _transliterable_rows()
    seed_hex = _sha256_lf(LEXICON_PATH)
    scrambled, moved = scrambled_lexicon(raw, seed_hex)
    block = validated["c_v4"]
    plan = _plan(seed_hex, rows, lexicon, block["sample_size"],
                 block["mutations"])

    b1_result = b1(oracle, lexicon, rule, rows, batch_size)
    b1_identity = {receipt["statement_id"]: receipt["identity"]
                   for receipt in b1_result["receipts"]}
    return {
        "run_id": RUN_ID,
        "design": "docs/DESIGN-foreign-voice.md",
        "prereg": "experiments/foreign_voice_prereg.json",
        "prereg_revalidated": validated["revalidated"],
        "toolchain": oracle.toolchain,
        "b0a": preview_now["b0a"],
        "b0bc": preview_now["b0bc"],
        "b0d": b0d(oracle, lexicon, rule, sealed, batch_size),
        "b1": b1_result,
        "b2": {
            "gate": "B2 — rejection is failure, not a skip",
            "outcomes_are_three": ["identity", "digest_differed",
                                   "orig_failed / roundtrip_failed"],
            "no_silent_drop": True,
            "refusals_abort": (
                "an OracleRefusal raises out of this module; a run with any "
                "refusal publishes zero rates and writes nothing"
            ),
        },
        "b3": b3(preview, register, b1_result),
        "c_v1": c_v1(oracle, lexicon, scrambled, moved, rule, rows,
                     b1_identity, batch_size),
        "c_v2": c_v2(oracle, rule, rows, transliterable, batch_size),
        "c_v3": c_v3_absent(),
        "c_v4": c_v4(oracle, lexicon, rule, rows, block, plan, batch_size),
        "b6": {
            "gate": "B6 — no learned component",
            "learned_components": [],
            "note": ("nothing in the render path, the inverse, rule R or the "
                     "register is learned; §9 closes the seat in writing"),
        },
        "non_claims": [
            "Identity is bounded, and C-V4 is how far.",
            "This is a lean_workbook rate; the composition sentence says so.",
            "Not fluency, and not translation quality.",
            "Coverage percent is not the headline. The register is.",
            "No internal-grammar reading capability is gained.",
            "No truth claim, and no verified_by links.",
            "No Mathlib heads.",
            "The declared interpretation is an interpretation, not a discovery.",
            "The transliterable half is not this cycle's result.",
        ],
    }


def _transliterable_rows() -> list[dict]:
    """B0a's easy half, recomputed under the byte-frozen parser."""
    tables = fve.split(REPO_ROOT / "data")
    out: list[dict] = []
    for path in sorted((REPO_ROOT / "data").glob("*/nodes.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        corpus = doc.get("discipline", path.parent.name)
        for node in doc.get("statement_nodes", []):
            source = ((node.get("formal_statement") or {})
                      .get("canonical_ascii") or "")
            if fve.parses(source) or not fve.parses(fve.transliterate(source)):
                continue
            out.append({"statement_id": node.get("statement_id", "<missing-id>"),
                        "corpus": corpus, "source": source})
    assert len(out) == tables["totals"]["transliterable"]
    return out


def run(out: Path = DEFAULT_OUT, batch_size: int = 300,
        two_run: bool = True) -> dict:
    """B5: produce the artifact twice and compare the bytes before writing."""
    first = measure(batch_size)
    payload = json.dumps(first, ensure_ascii=False, indent=1, sort_keys=True)
    b5 = {"gate": "B5 — determinism and hermeticity", "two_run": two_run}
    if two_run:
        second = json.dumps(measure(batch_size), ensure_ascii=False, indent=1,
                            sort_keys=True)
        b5["byte_identical"] = payload == second
        if not b5["byte_identical"]:
            raise RunRefusal(
                "two runs on one tree produced different artifacts; the oracle "
                "is not a function and no digest identity means anything")
    first["b5"] = b5
    first["verdicts"] = verdicts(first)
    out.write_text(json.dumps(first, ensure_ascii=False, indent=1,
                              sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    return first


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--dry-run", action="store_true",
                        help="revalidate, plan and report readiness; do not run "
                             "the oracle over the corpus and write nothing")
    parser.add_argument("--batch-size", type=int, default=300)
    parser.add_argument(
        "--perform-the-registered-run", action="store_true",
        help="actually run it. The flag is long and explicit on purpose: the "
             "registered run is a once-only act, its result is the cycle's "
             "headline, and a runner that can be executed by typing its name "
             "is a runner that can spend the one run on a rehearsal")
    args = parser.parse_args(argv)

    try:
        if args.dry_run or not args.perform_the_registered_run:
            report = dry_run(args.out)
            if not args.dry_run:
                report["note"] = (
                    "readiness only. Pass --perform-the-registered-run to "
                    "execute; §10 puts the run last and it has not run yet")
            print(json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True))
            return 0
        result = run(args.out, args.batch_size)
    except (RunRefusal, fvo.OracleRefusal, fve.EligibilityError) as exc:
        print(f"run refused: {exc}", file=sys.stderr)
        return 2

    print(f"B1 {result['b1']['composition']['required_sentence']}")
    print(f"B3 closes: {result['b3']['closes_exactly']}")
    print(f"OVERALL {result['verdicts']['overall']}: {result['verdicts']['summary']}")
    print(f"written to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
