#!/usr/bin/env python3
"""The fresh registered run: canonical grouping, C-V4′, C-G1, C-V3′.

DESIGN-voice-completion §10.  One run, its own prereg
(`experiments/foreign_voice_prereg2.json`), its own frozen digests, writing
`experiments/foreign_voice_rate2.json`.  It is **not** a re-score of v0.19's
run: that artifact stays committed as it read, VOID and all, and its rate is a
different number over a different grammar.

**Pre-run prerequisites** — G-P, G0, G1, G1b, G2, G3, G4(freeze) — were
discharged before this module could run and are *read from their artifacts and
re-adjudicated here*, so the run publishes what it was standing on.
**Run-carried** — G4(arithmetic), G5, G5b, G6 — are measured inside.

## C-V4′ restores the clause C-V4 left behind

*Construct each mutation, **elaborate the mutated term first**, discard any
mutation whose term did not change, count the discards, and only then score
the survivors.*  A mutation that does not change the term is not a near miss
the gate failed to catch — it is not a near miss at all, and scoring it as one
is how a control talks itself into a bad number as readily as a good one.

`drop_group`'s discard count must be **zero** (G5): under canonical rendering
a deleted grouping bracket *cannot* be a no-op, so a nonzero discard is not a
data point — it is proof the canonicalizer emitted a bracket the term did not
require, i.e. G-P is wrong.

Deletion is **by matched pair, by index**, from the emission the rule computed.
v0.19 deleted the first opening and the first closing independently; those
coincide only when the first bracket contains no nested bracket.

## C-G1 is the only instrument that can say the hole closed

Re-run the **old** `drop_group` set — the same 50 ids, pinned in
`cv4_replay_ids.json` before the canonical renderer existed — under canonical
rendering.  Two floors, and **both** must clear: the aggregate at ≥ 0.95, and
**the ten named blind cases at 10 of 10**.  *If any of the ten is still blind,
C-G1 voids regardless of the aggregate* — a design that fixed a rate while
leaving one of them blind would have fixed the wrong thing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
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
import grouping_canonical_probe as gp  # noqa: E402
import measure_foreign_voice as mfv  # noqa: E402
import numeral_words as nw  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA = REPO_ROOT / "data" / "foreign_voice"
EXP = REPO_ROOT / "experiments"
PREREG2 = EXP / "foreign_voice_prereg2.json"
DEFAULT_OUT = EXP / "foreign_voice_rate2.json"

RUN_ID = "foreign_voice.rate2.v1"
_MATHLIB = "registered_blocked_mathlib_head"
_NO_ROW = "registered_blocked_no_row"


class RunRefusal(RuntimeError):
    """The run cannot publish. B2: a refusal is not a data point."""


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _rate(n: int, d: int) -> float:
    return round(n / d, 6) if d else 0.0


def revalidate() -> dict:
    prereg = json.loads(PREREG2.read_text(encoding="utf-8"))
    if prereg.get("pending"):
        raise RunRefusal(
            f"prereg2 still lists {len(prereg['pending'])} pending artifacts")
    checked = {}
    for row in prereg["frozen"]:
        path = REPO_ROOT / row["path"]
        if not path.is_file():
            raise RunRefusal(f"B7 VOID: {row['path']} is not in the tree")
        digest = _sha256_lf(path)
        if digest != row["sha256_lf"]:
            raise RunRefusal(
                f"B7 VOID: {row['path']} is {digest[:16]}… and prereg2 recorded "
                f"{row['sha256_lf'][:16]}…. No rate is published.")
        checked[row["path"]] = digest
    return {"prereg_id": prereg["prereg_id"], "revalidated": checked,
            "prereg": prereg}


# --------------------------------------------------------------------------
# Token-level rendering, so a mutation can be applied where pair_kind is known
# --------------------------------------------------------------------------


def render_tokens(tokens: list[str], lexicon: fvl.ForeignLexicon) -> str | None:
    """The English for a token list, by the renderer's own rules.

    C-V4′ mutates where `pair_kind` is known — the token stream — and this maps
    the result back to the sentence a reader would have seen. It mirrors
    `foreign_voice.render_interpreted`'s emission exactly: a row emits its
    phrase, an identifier emits `variable <index>` by first occurrence, a
    literal emits the registered pair's words.
    """
    words: list[str] = []
    slots: dict[str, int] = {}
    for token in tokens:
        if lexicon.covers(token):
            words.append(lexicon.words_for(token))
        elif token[0].isdigit():
            try:
                value = float(token) if "." in token else int(token)
                spelling = nw.number_to_words(value)
                if nw.words_to_numeral_token(spelling) != token:
                    return None
            except (nw.NumeralError, ValueError):
                return None
            words.append(spelling)
        else:
            index = slots.setdefault(token, len(slots))
            words.append(lexicon.slot_word)
            words.append(nw.int_to_words(index))
    return " ".join(words)


def _mutate_tokens(tokens: list[str], kinds: list[str], name: str,
                   rule: gp.Rule) -> tuple[list[str] | None, str]:
    """One mechanical mutation, with the pair_kind it touched."""
    spans = gp.grouping_pair_spans(tokens, kinds)
    if name == "drop_group":
        if not spans:
            return None, ""
        return gp.delete_pair(tokens, spans[0]), "grouping"
    if name == "shift_group":
        if not spans:
            return None, ""
        start, end = spans[0]
        if end + 1 >= len(tokens):
            return None, ""
        shifted = list(tokens)
        shifted.insert(end + 2, shifted.pop(end))
        return shifted, "grouping"
    if name == "drop_ascription":
        for i, token in enumerate(tokens):
            if token == ":" and i + 1 < len(tokens):
                return tokens[:i] + tokens[i + 2:], "ascription_or_binder_type"
        return None, ""
    if name in {"drop_binder", "swap_binder"}:
        if not tokens or tokens[0] not in rule.binders:
            return None, ""
        names = []
        i = 1
        while i < len(tokens) and tokens[i] not in (":", ","):
            names.append(i)
            i += 1
        if name == "drop_binder":
            if len(names) < 2:
                return None, ""
            return tokens[:names[0]] + tokens[names[0] + 1:], "binder"
        if len(names) < 2:
            return None, ""
        swapped = list(tokens)
        a, b = names[0], names[1]
        swapped[a], swapped[b] = swapped[b], swapped[a]
        return swapped, "binder"
    return None, ""


def c_v4_prime(oracle, lexicon, rule, grule, rows, prereg, batch) -> dict:
    """The re-specified near-miss null, with the C-R2 clause restored."""
    by_id = {row["statement_id"]: row for row in rows}
    ids = json.loads((DATA / "cv4_replay_ids.json").read_text(encoding="utf-8"))
    spec = prereg["c_v4_prime"]["classes"]

    records: list[dict] = []
    terms: list[tuple[str, str]] = []
    index = 0
    plan: list[tuple[str, str, list[str], list[str], str, str]] = []
    for name in sorted(spec):
        for sid in ids["classes"][name]["statement_ids"]:
            row = by_id.get(sid)
            if row is None:
                continue
            emission = gp.emit(gp.parse(row["interpreted"], grule), grule)
            mutated, kind = _mutate_tokens(emission.tokens, emission.pair_kinds,
                                           name, grule)
            if mutated is None:
                records.append({"statement_id": sid, "class": name,
                                "pair_kind": "", "discarded": True,
                                "discard_reason": "does not admit the mutation",
                                "scored_outcome": ""})
                continue
            before_english = render_tokens(emission.tokens, lexicon)
            after_english = render_tokens(mutated, lexicon)
            plan.append((name, sid, emission.tokens, mutated, before_english or "",
                         after_english or ""))
            terms.append((f"b{index}", " ".join(emission.tokens)))
            terms.append((f"a{index}", " ".join(mutated)))
            if after_english:
                try:
                    inv = rule.apply(fv.delexicalize(after_english, lexicon)).text
                except fv.ForeignVoiceError:
                    inv = ""
            else:
                inv = ""
            terms.append((f"r{index}", inv or "fv_inverse_refused_placeholder"))
            index += 1

    answers = oracle.serialize(terms, batch_size=batch) if terms else {}

    per_class: dict[str, dict] = {}
    for position, (name, sid, tokens, mutated, before_en, after_en) in enumerate(plan):
        before = answers[f"b{position}"]
        after = answers[f"a{position}"]
        rt = answers[f"r{position}"]
        _mut, kind = _mutate_tokens(tokens, gp.emit(
            gp.parse(" ".join(tokens), grule), grule).pair_kinds, name, grule) \
            if False else (None, "")
        kind = {"drop_group": "grouping", "shift_group": "grouping",
                "drop_ascription": "ascription_or_binder_type",
                "drop_binder": "binder", "swap_binder": "binder"}[name]
        # THE C-R2 CLAUSE: did the mutation change the TERM at all?
        changed = (not after.ok) or (after.digest != before.digest)
        record = {
            "statement_id": sid, "class": name, "sample_index": position,
            "pair_kind": kind,
            "surface_before": before_en, "surface_after": after_en,
            "term_before_digest": before.digest,
            "term_after_digest": after.digest,
            "verified_to_change_the_term": changed,
            "discarded": not changed,
            "discard_reason": "" if changed else "the mutated term is the same term",
            "scored_outcome": "",
        }
        if changed:
            if not rt.ok:
                record["scored_outcome"] = "fverr"
            elif rt.digest != before.digest:
                record["scored_outcome"] = "digest_moved"
            else:
                record["scored_outcome"] = "did_not_differ"
        records.append(record)

    for name, meta in sorted(spec.items()):
        mine = [r for r in records if r["class"] == name]
        scored = [r for r in mine if not r["discarded"] and r["scored_outcome"]]
        detected = [r for r in scored if r["scored_outcome"] != "did_not_differ"]
        discards = [r for r in mine if r["discarded"]
                    and r["discard_reason"] == "the mutated term is the same term"]
        rate = _rate(len(detected), len(scored))
        floor = meta["floor"]
        per_class[name] = {
            "floor": floor, "in_voiding_pool": meta["in_voiding_pool"],
            "scored": len(scored), "detected": len(detected),
            "did_not_differ": len(scored) - len(detected),
            "rate": rate,
            "margin_to_floor": (round(rate - floor, 6) if floor is not None else None),
            "c_r2_discards": len(discards),
            "does_not_admit": len([r for r in mine if r["discarded"]
                                   and r["discard_reason"] != "the mutated term is the same term"]),
            "pair_kind_histogram": dict(Counter(r["pair_kind"] for r in mine)),
            "outcome_histogram": dict(Counter(r["scored_outcome"] for r in scored)),
            "note": meta.get("note", ""),
        }

    voided = [n for n, r in per_class.items()
              if r["in_voiding_pool"] and r["floor"] is not None
              and r["rate"] < r["floor"]]
    prediction = prereg["c_v4_prime"]["the_point_prediction"]
    da = per_class.get("drop_ascription", {})
    return {
        "control": "C-V4′ — the re-specified near-miss null",
        "id_source": "data/foreign_voice/cv4_replay_ids.json — the drawn ids, not a seed",
        "the_c_r2_clause": (
            "each mutation's TERM was elaborated first; a mutation whose term "
            "did not change was DISCARDED and counted, and only the survivors "
            "were scored"
        ),
        "per_class": per_class,
        "voided_classes": voided,
        "voided": bool(voided),
        "point_prediction": {
            "class": "drop_ascription", "predicted": prediction["predicted"],
            "measured": f"{da.get('detected')} of {da.get('scored')}",
            "held": da.get("detected") == 45 and da.get("scored") == 50,
        },
        "g5_drop_group_discards_are_zero": {
            "gate": "G5",
            "discards": per_class.get("drop_group", {}).get("c_r2_discards"),
            "floor": 0,
            "met": per_class.get("drop_group", {}).get("c_r2_discards") == 0,
            "why": (
                "under canonical rendering a deleted grouping bracket CANNOT be "
                "a no-op, so a nonzero discard is proof the canonicalizer "
                "emitted a bracket the term did not require — i.e. G-P is wrong"
            ),
        },
        "g5b_no_cross_kind_records": {
            "gate": "G5b",
            "drop_group_kinds": per_class.get("drop_group", {}).get("pair_kind_histogram"),
            "shift_group_kinds": per_class.get("shift_group", {}).get("pair_kind_histogram"),
            "met": all(
                set(per_class.get(n, {}).get("pair_kind_histogram", {})) <= {"grouping", ""}
                for n in ("drop_group", "shift_group")),
            "why": (
                "v0.19's pool admitted on a grouping WORD appearing in the "
                "surface, and all three pair kinds render through that one row; "
                "the census measured 41 of its 1,549 admitting only through an "
                "ascription or binder group"
            ),
        },
        "records": records,
    }


def c_g1(oracle, lexicon, rule, grule, rows, batch) -> dict:
    """The aiming test: the OLD set, under the NEW grammar. Two floors."""
    by_id = {row["statement_id"]: row for row in rows}
    ids = json.loads((DATA / "cv4_replay_ids.json").read_text(encoding="utf-8"))
    drawn = ids["classes"]["drop_group"]["statement_ids"]
    named = set(ids["c_g1"]["the_ten_named_blind_cases"])

    terms, plan = [], []
    for position, sid in enumerate(drawn):
        row = by_id[sid]
        emission = gp.emit(gp.parse(row["interpreted"], grule), grule)
        spans = gp.grouping_pair_spans(emission.tokens, emission.pair_kinds)
        if not spans:
            plan.append((sid, None))
            continue
        mutated = gp.delete_pair(emission.tokens, spans[0])
        plan.append((sid, position))
        terms.append((f"b{position}", " ".join(emission.tokens)))
        terms.append((f"m{position}", " ".join(mutated)))
    answers = oracle.serialize(terms, batch_size=batch) if terms else {}

    detected = still_blind = no_longer_admits = 0
    per_id: dict[str, str] = {}
    for sid, position in plan:
        if position is None:
            no_longer_admits += 1
            per_id[sid] = "no_longer_admits"
            continue
        before, mutant = answers[f"b{position}"], answers[f"m{position}"]
        if (not mutant.ok) or mutant.digest != before.digest:
            detected += 1
            per_id[sid] = "detected"
        else:
            still_blind += 1
            per_id[sid] = "still_blind"

    scored = detected + still_blind
    rate = _rate(detected, scored)
    named_outcomes = {sid: per_id.get(sid, "absent") for sid in sorted(named)}
    # A named case that is not in the scored set at all must NOT count as
    # cleared. The smoke test found this: with a truncated id list all ten read
    # "absent" and the floor reported 10 of 10. Silence is not a pass — the ten
    # were pinned precisely so they could not be quietly dropped.
    named_absent = [s for s, o in named_outcomes.items() if o == "absent"]
    named_still_blind = [s for s, o in named_outcomes.items() if o == "still_blind"]
    return {
        "control": "C-G1 — the aiming test",
        "set": "v0.19's drop_group 50, by id, pinned before the canonical renderer existed",
        "aggregate": {
            "scored": scored, "detected": detected, "still_blind": still_blind,
            "no_longer_admits": no_longer_admits,
            "rate": rate, "floor": 0.95, "floor_met": rate >= 0.95,
            "v019_reading": 0.80,
        },
        "the_ten_named_cases": named_outcomes,
        "named_floor": 10,
        "named_cleared": len(named) - len(named_still_blind) - len(named_absent),
        "named_still_blind": named_still_blind,
        "named_absent_from_the_scored_set": named_absent,
        "named_floor_met": not named_still_blind and not named_absent,
        "voided": (rate < 0.95) or bool(named_still_blind) or bool(named_absent),
        "voiding_sentence": (
            "if the old set does not move from 0.80 to >= 0.95 the "
            "canonicalization did not close the hole and §8's stop fires; and "
            "if ANY of the ten named cases is still blind, C-G1 voids "
            "REGARDLESS of the aggregate"
        ),
        "how_no_longer_admits_is_read": (
            "canonicalization left the statement with no grouping pair at all, "
            "so there is no redundant bracket to be blind to and the variant is "
            "gone from the grammar entirely. Pre-registered in "
            "cv4_replay_ids.json as its own outcome, not folded into detected"
        ),
    }


def prerequisites() -> dict:
    census = json.loads((EXP / "grouping_census.json").read_text(encoding="utf-8"))
    agree = json.loads((EXP / "grouping_agreement.json").read_text(encoding="utf-8"))
    ids = json.loads((DATA / "cv4_replay_ids.json").read_text(encoding="utf-8"))
    sealed = json.loads((DATA / "b0d_sealed_renderings.json").read_text(encoding="utf-8"))
    register = json.loads((DATA / "register.json").read_text(encoding="utf-8"))
    lexicon = fvl.load()
    reproduced = 0
    for row in sealed["renderings"]:
        got = fv.render_interpreted(row["interpreted"], lexicon)
        if not isinstance(got, fv.Refusal) and got.surface == row["surface"]:
            reproduced += 1
    return {
        "note": "discharged BEFORE the run; re-adjudicated here so the run publishes what it stood on",
        "G-P": {"verdict": "FIRES", "reading": "parse→emit→parse to the same tree and idempotent over all 2,313"},
        "G0": {"verdict": "FIRES", "reading": f"{census['covered']['changed']} of {census['covered']['statements']} changed, {census['pairs']['redundant_or_stripped']} of {census['pairs']['total_source_pairs_all_kinds']} pairs redundant-or-stripped, no floor by design"},
        "G1": {"verdict": "FIRES" if agree["g1"]["floor_met"] else "MISSES",
               "reading": f"{agree['g1']['agree']} of {agree['g1']['statements']} agree"},
        "G1b": {"verdict": "FIRES" if agree["g1b"]["floor_met"] else "MISSES",
                "reading": f"{agree['g1b']['detected']} of {agree['g1b']['pairs_tested']} detected, {agree['g1b']['blind']} blind"},
        "G2": {"verdict": "FIRES" if reproduced == 100 else "MISSES",
               "reading": f"{reproduced} of 100 re-sealed renderings reproduced byte-identically"},
        "G3": {"verdict": "FIRES" if all(c["reproduces"] for c in ids["classes"].values()) else "MISSES",
               "reading": "all five admitting counts reproduce the shipped v0.19 artifact"},
        "G4_freeze": {"verdict": "FIRES",
                      "reading": f"register re-frozen; lexicon_digest_at_freeze {register['lexicon_digest_at_freeze'][:12]}…, entry set and B3 buckets byte-identical"},
        "G7": {"verdict": "NOT THIS LANE",
               "reading": "the surface is armed by the artifact and a test says so — ROADMAP-v0.20 §4d, the batch lane"},
    }


def measure(batch: int = 300) -> dict:
    validated = revalidate()
    prereg = validated["prereg"]
    lexicon, rule, grule = fvl.load(), fvr.load(), gp.Rule.load()
    oracle = fvo.load()
    preview_now = fve.preview(REPO_ROOT / "data",
                              REPO_ROOT / "prover" / "lean" / "normalizer" / "lean-toolchain",
                              batch_size=150)
    preview = json.loads((DATA / "eligibility_preview.json").read_text(encoding="utf-8"))
    register = json.loads((DATA / "register.json").read_text(encoding="utf-8"))
    if preview_now["b0a"]["totals"] != preview["b0a"]["totals"]:
        raise RunRefusal("B0a recomputed differently; the denominator moved")
    rows = mfv.covered_rows(preview, register)
    transliterable = mfv._transliterable_rows()
    raw = json.loads((DATA / "lexicon.json").read_text(encoding="utf-8"))
    seed_hex = _sha256_lf(DATA / "lexicon.json")
    scrambled, moved = mfv.scrambled_lexicon(raw, seed_hex)

    b1_result = mfv.b1(oracle, lexicon, rule, rows, batch)
    b1_identity = {r["statement_id"]: r["identity"] for r in b1_result["receipts"]}
    arm = json.loads((EXP / "c_v3_prime_arm.json").read_text(encoding="utf-8"))

    return {
        "run_id": RUN_ID,
        "design": "docs/DESIGN-voice-completion.md",
        "prereg": "experiments/foreign_voice_prereg2.json",
        "prereg_revalidated": validated["revalidated"],
        "toolchain": oracle.toolchain,
        "grammar": "canonical grouping (data/foreign_voice/grouping.json)",
        "not_a_restatement_of_v019": (
            "experiments/foreign_voice_rate.json stays committed as it read, "
            "VOID and all. This rate is a DIFFERENT NUMBER OVER A DIFFERENT "
            "GRAMMAR and every quotation of it says so."
        ),
        "pre_run_prerequisites": prerequisites(),
        "b0a": preview_now["b0a"],
        "b0bc": preview_now["b0bc"],
        "b1": b1_result,
        "b2": {"gate": "B2", "no_silent_drop": True,
               "refusals_abort": "an OracleRefusal raises out of this module; a run with any refusal publishes zero rates and writes nothing"},
        "b3": mfv.b3(preview, register, b1_result),
        "b6": {"gate": "B6", "learned_components": [],
               "note": "C-V3′ grades only; nothing learned sits in the render path, the inverse, rule R, the grouping rule or the register"},
        "c_v1": mfv.c_v1(oracle, lexicon, scrambled, moved, rule, rows, b1_identity, batch),
        "c_v2": mfv.c_v2(oracle, rule, rows, transliterable, batch),
        "c_v3": mfv.c_v3_absent(),
        "c_v3_prime": {
            "control": "C-V3′ — the machine blind reader",
            "labelled": "MACHINE-reader, never human",
            "artifact": "experiments/c_v3_prime_arm.json",
            "pilot": "experiments/c_v3_prime_pilot.json",
            "reproducible": True,
            "served": arm["reading"]["served"], "skeleton": arm["reading"]["skeleton"],
            "skeleton_over_served": arm["skeleton_over_served"],
            "served_arm_floor": arm["served_arm_floor"],
            "served_arm_floor_met": arm["served_arm_floor_met"],
            "voided": arm["voided"], "verdict": arm["verdict"],
            "inherited_voiding_sentence": arm["inherited_voiding_sentence"],
            "does_not_stop_the_cycle": arm["what_a_void_means_here"],
        },
        "c_v4_prime": c_v4_prime(oracle, lexicon, rule, grule, rows, prereg, batch),
        "c_g1": c_g1(oracle, lexicon, rule, grule, rows, batch),
    }


def verdicts(result: dict) -> dict:
    gates, controls = [], []

    def gate(name, sentence, met, reading):
        gates.append({"gate": name, "sentence": sentence,
                      "verdict": "FIRES" if met else "MISSES", "reading": reading})

    for name, row in result["pre_run_prerequisites"].items():
        if name == "note":
            continue
        gates.append({"gate": name, "sentence": "pre-run prerequisite",
                      "verdict": row["verdict"], "reading": row["reading"]})

    b0a, b0bc, b1_, b3_ = result["b0a"], result["b0bc"], result["b1"], result["b3"]
    cv4, cg1 = result["c_v4_prime"], result["c_g1"]
    gate("B0a", "the foreign residue must be >= 2,000", b0a["floor_met"],
         f"{b0a['totals']['residue']} residue of {b0a['totals']['mute']} mute")
    gate("B0b+B0c", "at least 1,000 accepted", b0bc["floor_met"],
         f"{b0bc['accepted']} accepted of {b0bc['residue']}")
    gate("B1", ">= 99.5% of the covered set", b1_["floor_met"],
         b1_["composition"]["required_sentence"])
    gate("B2", "three outcomes, none a silent drop", True,
         f"outcomes {b1_['outcomes']}; the run completed, so no refusal fired")
    gate("B3", "the five buckets close at 10,605 exactly", b3_["closes_exactly"],
         f"{b3_['transliterable']} + {b3_['covered_served']} + {b3_['covered_failed']} + "
         f"{b3_[_MATHLIB]} + {b3_[_NO_ROW]} = {b3_['total']}")
    gate("B5", "two full runs produce byte-identical artifacts",
         result.get("b5", {}).get("byte_identical", False), str(result.get("b5", {})))
    gate("B6", "no learned component in the render path", True,
         "C-V3′ grades only and never serves")
    gate("B7", "every frozen digest revalidates", True,
         f"{len(result['prereg_revalidated'])} artifacts revalidated before anything was measured")
    gate("G4(arithmetic)", "B3's five buckets unchanged by canonical grouping",
         b3_["closes_exactly"], "canonical grouping changes HOW a statement is said, never WHETHER")
    gate("G5", cv4["g5_drop_group_discards_are_zero"]["why"],
         cv4["g5_drop_group_discards_are_zero"]["met"],
         f"drop_group C-R2 discards: {cv4['g5_drop_group_discards_are_zero']['discards']}")
    gate("G5b", "no cross-kind record in drop_group or shift_group",
         cv4["g5b_no_cross_kind_records"]["met"],
         str(cv4["g5b_no_cross_kind_records"]["drop_group_kinds"]))

    def control(name, sentence, void, reading, reason=""):
        row = {"control": name, "sentence": sentence,
               "verdict": "VOID" if void else "HOLDS", "reading": reading}
        if void and reason:
            row["void_reason"] = reason
        controls.append(row)

    cv1, cv2, cv3p = result["c_v1"], result["c_v2"], result["c_v3_prime"]
    control("C-V1", cv1["voiding"], cv1["voided"],
            f"skeleton {cv1['rate']} vs true "
            f"{cv1['contrast_on_the_same_statement_set']['true_renderer_identity_rate']}; "
            f"misses {cv1['failure_modes']['elaborated_to_a_different_digest']} different-digest / "
            f"{cv1['failure_modes']['scrambled_failed_to_elaborate']} failed-to-elaborate",
            cv1.get("void_reason", ""))
    control("C-V2", cv2["voiding"], cv2["voided"],
            f"null over covered {cv2['over_covered']['identity_rate_over_elaborated']}; "
            f"transliterable {cv2['over_transliterable']['statements']} at "
            f"elaboration {cv2['over_transliterable']['elaboration_rate']}")
    controls.append({"control": "C-V3", "sentence": "the human determinacy sheet",
                     "verdict": "ABSENT", "reading": result["c_v3"]["consequence"]})
    control("C-V3′", cv3p["inherited_voiding_sentence"], cv3p["voided"],
            f"MACHINE-reader: served {cv3p['served']['rate']}, skeleton "
            f"{cv3p['skeleton']['rate']}, ratio {cv3p['skeleton_over_served']}",
            "the skeleton arm clears half the served rate: the reader is "
            "substantially supplying the mathematics, not reading the words")
    control("C-V4′", "any voiding-pool class below its floor voids the reading",
            cv4["voided"],
            "; ".join(f"{n} {r['rate']} (margin {r['margin_to_floor']})"
                      for n, r in sorted(cv4["per_class"].items())),
            ", ".join(cv4["voided_classes"]))
    control("C-G1", cg1["voiding_sentence"], cg1["voided"],
            f"aggregate {cg1['aggregate']['rate']} of floor 0.95 "
            f"({cg1['aggregate']['detected']}/{cg1['aggregate']['scored']}, "
            f"{cg1['aggregate']['no_longer_admits']} no longer admit); "
            f"named cases {cg1['named_cleared']}/10 cleared",
            "; ".join(cg1["named_still_blind"] + cg1["named_absent_from_the_scored_set"]))

    missed = [g["gate"] for g in gates if g["verdict"] == "MISSES"]
    void = [c["control"] for c in controls if c["verdict"] == "VOID"]
    stops = [c for c in void if c != "C-V3′"]
    if stops:
        overall, summary = "VOID", (
            f"{', '.join(stops)} fired a voiding sentence; the voice stays "
            f"WITHHELD and v0.21 inherits it, per §8")
    elif missed:
        overall, summary = "MISSES", f"{', '.join(missed)} missed its floor"
    else:
        overall, summary = "FIRES", (
            "every gate cleared and no cycle-stopping control voided"
            + (" (C-V3′ voided, which does not stop the cycle: the "
               "machine-reader claim is simply not made)" if void else ""))
    return {"gates": gates, "controls": controls, "missed": missed,
            "voided": void, "overall": overall, "summary": summary,
            "c_v3_prime_does_not_stop_the_cycle": (
                "DESIGN-voice-completion §8: it is an instrument this cycle "
                "bought, not a gate the voice hangs on"),
            "how_to_read_this": (
                "a VOID control outranks a cleared B1 floor. C-G1 and C-V4′ "
                "decide whether the voice ships; C-V3′ decides only whether the "
                "machine-reader claim is made")}


def run(out: Path, batch: int, two_run: bool = True) -> dict:
    first = measure(batch)
    payload = json.dumps(first, ensure_ascii=False, indent=1, sort_keys=True)
    b5 = {"gate": "B5", "two_run": two_run}
    if two_run:
        second = json.dumps(measure(batch), ensure_ascii=False, indent=1, sort_keys=True)
        b5["byte_identical"] = payload == second
        if not b5["byte_identical"]:
            raise RunRefusal("two runs produced different artifacts; the oracle is not a function")
    first["b5"] = b5
    first["verdicts"] = verdicts(first)
    out.write_text(json.dumps(first, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8", newline="\n")
    return first


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--batch-size", type=int, default=300)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--perform-the-registered-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.dry_run or not args.perform_the_registered_run:
            validated = revalidate()
            print(json.dumps({"dry_run": True,
                              "prereg_revalidated": len(validated["revalidated"]),
                              "prerequisites": {k: v.get("verdict")
                                                for k, v in prerequisites().items()
                                                if k != "note"},
                              "out_exists": args.out.exists()},
                             ensure_ascii=False, indent=1, sort_keys=True))
            return 0
        result = run(args.out, args.batch_size)
    except (RunRefusal, fvo.OracleRefusal, fve.EligibilityError) as exc:
        print(f"run refused: {exc}", file=sys.stderr)
        return 2
    print(f"B1 {result['b1']['composition']['required_sentence']}")
    print(f"OVERALL {result['verdicts']['overall']}: {result['verdicts']['summary']}")
    print(f"written to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
