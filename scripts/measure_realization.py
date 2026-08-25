#!/usr/bin/env python3
"""The registered run: R0-R5 and C-R1..C-R3 into experiments/realization_rate.json.

DESIGN-sans-template-rendering §10, last item of the preregistration order:
*"then the one registered full-corpus run (`experiments/realization_rate.json`,
R0 table + R1 rate)."*  This is that run, plus the three blind controls §7
registers, in one deterministic writer.

**Why a separate script rather than a `--registered` mode in
`realize_term.py`.**  `realize_term.py` is digest-pinned in
`experiments/realization_prereg.json` as the *inverter*, and C-R3's whole
point is that the reading path does not move while the run is being written.
A `--registered` mode would have re-recorded the inverter's digest in the same
commit that produced the number the digest is supposed to certify.  So the
runner lives here, in the repo's own `measure_*.py` convention
(`measure_throughput`, `measure_ambiguity`, `measure_false_positive`, …), and
the pinned modules are byte-frozen through the run.  The runner is NOT itself
pinned; it is the instrument, and `provenance.writer_sha256_lf` records it.

**Byte-reproducibility.**  Nothing in the artifact varies between two runs on
one tree: no timestamp, no elapsed time, no absolute path, no environment.
Corpus iteration is sorted, the C-R1 derangement is seeded from the committed
lexicon's own digest, and C-R2's mutation choice is the first applicable node
in a fixed pre-order walk.  `tests/test_measure_realization.py` regenerates
the artifact into a temp path and compares bytes.

## What this writer is allowed to do, and what it refuses

It refuses to write at all if any digest in the prereg's `frozen` list
disagrees with the tree (C-R3).  That is the one hard stop: a run whose
reading path moved after the freeze is not a registered run, it is a
measurement of something else, and writing it would launder the change.

## The three controls, and the shape each has to have

- **C-R1 — the scrambled realizer, as a contrast, ONE-SIDED.**  The forward
  table is deranged; the surface is read back through the **committed** table.
  Two-sidedness was measured during implementation and pinned in
  `tests/test_realize_term.py`: a consistent relabelling is still a bijection
  and round-trips at 4 of 4, which would report a near-perfect control and
  void the reading under C-R1's own ≥1% clause for a reason that has nothing
  to do with whether the gate reads the words.  So the scramble is applied to
  the writer only, and this file says so in the artifact it emits.
  Scrambled failures are counted in TWO classes, because "the control failed"
  is uninformative otherwise: `unreadable` (the wrong tokens do not parse at
  all) versus `different_skeleton` (they parse fine and mean something else).
  A control that only ever produced the first would be exercising the
  tokenizer, exactly the hazard C-R2's own floor exists to catch.
- **C-R2 — near-misses, mechanically generated, verified BEFORE realizing.**
  Every mutation is applied to the canonical TREE and its skeleton is compared
  to the source's *before* any sentence is produced; a mutation that does not
  change the skeleton is discarded, never counted.  That is the design's rule
  and it is the only way the control can be aimed: `canonicalize` legitimately
  erases commutative-argument order and symmetric-relation sides, and a
  control built from those would void the gate for behaving correctly.
  Alias-class swaps are INCLUDED, per the design's 2026-08-23 correction —
  `canonicalize` does no aliasing, so `MOD` vs `CONCAT` is a real
  skeleton-changing near-miss and not an exclusion.
- **C-R3 — the tautology probe**, revalidated here rather than trusted.

## Where C-R2's tree-level realization comes from

The mutations are trees, and `realize_term.realize` takes a source string, so
this file re-realizes from a tree.  It does that with `realize_term`'s OWN
objects — `_Linearizer`, `_slot_order`, `reparse`, `LEVEL_RELATION` — so the
control exercises the same linearizer and the same two-stage gate the served
path uses.  Only the glue is local, and it is a transcription of `realize()`'s
own body.  The alternative was adding a tree entry point to `realize_term.py`,
which would have moved the pinned inverter's digest in the run's own commit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numeral_words as nw
import realization_lexicon as rlex
import realize_term as rt
from match_signatures import (
    COMMUTATIVE_CALL_HEADS,
    HEAD_ALIASES,
    SYMMETRIC_RELATIONS,
    Parser,
    TemplateParseError,
    canonicalize,
    skeleton,
    tokenize,
)
from report_provenance import provenance_block, sha256_lf_file

REPO_ROOT = Path(__file__).resolve().parent.parent
RUN_ID = "realization.registered.v1"
REGISTERED_ON = "2026-08-23"
PREREG_PATH = REPO_ROOT / "experiments" / "realization_prereg.json"

#: R1's floor, frozen in the design before any of this was written.
R1_FLOOR = 0.90
#: R1's per-corpus floor applies only above this parseable denominator.
THIN_DENOMINATOR = 50
#: C-R1's two voiding thresholds, both from design §7.
C_R1_CONTRAST_MULTIPLE = 20.0
C_R1_SCRAMBLED_CEILING = 0.01
#: "Near zero" for the true realizer, below which the contrast is untested.
C_R1_TRUE_FLOOR = 0.05
#: C-R2's floor: below this the mutation set exercises the tokenizer.
C_R2_REPARSE_FLOOR = 0.50
#: How many served surfaces are pinned verbatim in the artifact (M2).
SURFACE_SAMPLE_SIZE = 25


class PreregMismatch(RuntimeError):
    """C-R3 failed. The run does not get written."""


def closed_by_amendment(prereg_path: Path | None = None) -> str | None:
    """The reason this registered run may no longer WRITE, or None.

    Added 2026-08-24 by `realization.prereg.v1.amendment.transliteration-
    2026-08-24` (ROADMAP-v0.19 item 3a), and it closes a hazard the amendment
    would otherwise only have described.

    `revalidate_prereg` follows the retirement, which is right: the digest check
    must stay alive, and the mechanics stay testable. But following it also
    means this writer would happily re-measure under the SUCCESSOR parser and
    overwrite `experiments/realization_rate.json` with an R1 over 8,586 terms —
    2,172 adjudicated under v0.18's gate and 6,414 reached by a change that gate
    never saw. That blended figure is precisely what the amendment declined to
    produce, and a prohibition that lives only in prose is one command away from
    being violated by someone who never read it.

    So the CLI is closed while `revalidate_prereg` stays open. The two answer
    different questions: "does the tree still match a pin recorded somewhere"
    (bookkeeping, must keep working) versus "may this run be executed and its
    artifact rewritten" (authority, and the answer is no). `--no-write` still
    runs, because reading the numbers is not the thing being prevented.
    """
    prereg_path = Path(prereg_path) if prereg_path is not None else PREREG_PATH
    prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
    for row in prereg["frozen"]:
        marker = row.get("retired_for_future_comparisons")
        if marker is None:
            continue
        return (
            f"this registered run is CLOSED. {row['path']}'s pin was retired "
            f"for future comparisons by amendment {marker['amendment']} "
            f"({marker['dated']}), which declared "
            f"experiments/realization_rate.json a HISTORICAL ARTIFACT measured "
            f"under the pre-amendment parser and recorded, in writing, that the "
            f"v0.18 run would not be re-run. Re-running it now would blend two "
            f"cycles' denominators into one rate neither cycle's floor can be "
            f"checked against. The new parser's rates are in "
            f"experiments/transliteration_rate.json. Use --no-write to read the "
            f"numbers without overwriting the record."
        )
    return None


def _successor_row(prereg: dict, row: dict) -> tuple[dict, str]:
    """The live pin for a row retired by a dated amendment, and its file.

    A row carrying `retired_for_future_comparisons` is history: it records what
    the artifact that quoted it was measured under, and the tree has legitimately
    moved past it. Checking such a row against the working tree would be asking
    a closed question. Checking nothing would be worse — the freeze would have
    silently become optional.

    So the retirement is followed rather than skipped. The marker names the
    amendment; the amendment names the successor prereg; the successor's row of
    the same role is what the tree is checked against. Every hop is a fact
    written down in a committed file, so a reader can walk the chain by hand and
    a broken link raises instead of degrading to a pass.
    """
    marker = row["retired_for_future_comparisons"]
    wanted = marker["amendment"]
    for entry in prereg.get("amendments", ()):
        if entry["amendment_id"].endswith(wanted):
            successor_path = entry["successor_prereg"]["path"]
            break
    else:
        raise PreregMismatch(
            f"{row['path']} is marked retired by amendment {wanted!r}, but no "
            f"such amendment is recorded in this file. A retirement marker "
            f"without its amendment is a pin removed with no reason attached."
        )
    successor = json.loads(
        (REPO_ROOT / successor_path).read_text(encoding="utf-8"))
    for candidate in successor["frozen"]:
        if candidate["role"] == row["role"]:
            return candidate, successor_path
    raise PreregMismatch(
        f"{successor_path} is named as the successor pin for role "
        f"{row['role']!r} but records no row for it."
    )


# --------------------------------------------------------------------------
# C-R3 — revalidate the freeze before anything is measured
# --------------------------------------------------------------------------


def revalidate_prereg(prereg_path: Path | None = None) -> dict:
    """Re-compute every pinned digest. Raises `PreregMismatch` on any drift.

    Called FIRST, before a single term is realized, so a moved reading path
    stops the run rather than producing a number nobody can interpret.

    `prereg_path` defaults to the module global read at CALL time, not at
    definition time. A default argument would have frozen the real prereg into
    the signature, so a caller pointing this at a different file — the refusal
    test, or any future harness — would have been silently revalidated against
    the committed one and the run written anyway. The refusal path has to be
    reachable or it is decoration.
    """
    prereg_path = Path(prereg_path) if prereg_path is not None else PREREG_PATH
    prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
    rows = []
    drifted = []
    for row in prereg["frozen"]:
        path = REPO_ROOT / row["path"]
        actual = sha256_lf_file(path) if path.exists() else None
        entry = {
            "path": row["path"],
            "role": row["role"],
            "recorded_sha256_lf": row["sha256_lf"],
            "observed_sha256_lf": actual,
        }
        if "retired_for_future_comparisons" in row:
            # Follow the chain to its END, not one hop. ROADMAP-v0.20 §4b
            # retired the parser row of the very file this amendment named as
            # successor — two cycles touching one file — so a single hop now
            # stops at a digest the tree has legitimately moved past and
            # reports that as drift. `prereg_pins` is the shared walk; the
            # one-hop `_successor_row` is kept for the reporting fields it
            # still supplies.
            from prereg_pins import resolve_pin  # noqa: PLC0415

            successor, successor_path = _successor_row(prereg, row)
            resolved = resolve_pin(
                prereg, row, prereg_path=str(prereg_path))
            agrees = actual == resolved["sha256_lf"]
            entry["retired_for_future_comparisons"] = {
                "amendment": row["retired_for_future_comparisons"]["amendment"],
                "dated": row["retired_for_future_comparisons"]["dated"],
                "checked_against": resolved["source"],
                "retirement_hops": resolved["hops"],
                "first_hop_was": successor_path,
                "successor_sha256_lf": resolved["sha256_lf"],
                "read_this_as": (
                    "`recorded_sha256_lf` is the digest THIS file's artifact was "
                    "measured under and is not expected to match the tree. The "
                    "tree is checked against the successor pin named above, and "
                    "`agrees` reports that check."
                ),
            }
        else:
            agrees = actual == row["sha256_lf"]
        entry["agrees"] = agrees
        rows.append(entry)
        if not agrees:
            drifted.append(row["path"])
    if drifted:
        raise PreregMismatch(
            "C-R3 VOID: these preregistered artifacts no longer match the tree: "
            + ", ".join(drifted)
            + ". The independence claim needs its own review naming the reason; "
            "the registered run is NOT written."
        )
    return {
        "control": "C-R3 (the tautology probe)",
        "prereg": "experiments/realization_prereg.json",
        "prereg_sha256_lf": sha256_lf_file(prereg_path),
        "verdict": "HOLDS",
        "what_it_means": (
            "Every artifact frozen before the realizer was written is "
            "byte-identical to what the preregistration commit recorded, so "
            "stage 2 is the same reader that had never seen the realizer — "
            "EXCEPT for any row a dated amendment retired for future "
            "comparisons, which is checked against the successor pin the "
            "amendment names and says so in its own row. If any row disagreed "
            "this writer would refuse to emit the artifact."
        ),
        "revalidated": rows,
    }


# --------------------------------------------------------------------------
# Corpus walk
# --------------------------------------------------------------------------


def _iter_terms(data_dir: Path):
    """(corpus, statement_id, canonical_ascii) in a fully sorted order."""
    for path in sorted(data_dir.glob("*/nodes.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        corpus = doc.get("discipline", path.parent.name)
        for node in doc.get("statement_nodes", []):
            yield (
                corpus,
                node.get("statement_id", "<missing-id>"),
                ((node.get("formal_statement") or {}).get("canonical_ascii") or ""),
            )


def _parse_failure_class(detail: str) -> str:
    if not detail:
        return "empty"
    return detail.split(" at ")[0].split(" `")[0][:48]


def _rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


# --------------------------------------------------------------------------
# R0 / R1 / R2 — the registered measurement
# --------------------------------------------------------------------------


def measure(data_dir: Path, lex: rlex.Lexicon) -> dict:
    """One pass over every node. Returns the R0/R1/R2 block plus the served set."""
    per_corpus: dict[str, Counter] = {}
    corpus_order: list[str] = []
    parse_failures: dict[str, Counter] = {}
    refusals: list[dict] = []          # EXHAUSTIVE, post-parse only
    round_trip_failures: list[dict] = []   # EXHAUSTIVE
    r2_breaches: list[dict] = []           # EXHAUSTIVE
    served: list[tuple[str, str, str, str]] = []   # (sid, corpus, surface, skel)
    #: Exactly the terms in R1's denominator, so the controls run on the same
    #: set the rate was read on rather than on a set assembled separately.
    parseable: list[tuple[str, str]] = []

    for corpus, sid, source in _iter_terms(data_dir):
        if corpus not in per_corpus:
            per_corpus[corpus] = Counter()
            parse_failures[corpus] = Counter()
            corpus_order.append(corpus)
        row = per_corpus[corpus]
        row["nodes"] += 1

        result = rt.realize(source, lex, statement_id=sid)
        if isinstance(result, rt.Refusal):
            if result.reason in {"unparseable_term", "empty_term"}:
                # Not parseable: it never enters R1's denominator at all.
                parse_failures[corpus][_parse_failure_class(result.detail)] += 1
                continue
            # Parsed, then refused by the realizer: it IS in the denominator,
            # and it counts against R1 exactly as a round-trip failure would.
            row["parseable"] += 1
            parseable.append((sid, source))
            row["refused_after_parse"] += 1
            refusals.append({
                "statement_id": sid, "corpus": corpus,
                "reason": result.reason, "detail": result.detail,
                "source": source,
            })
            continue

        row["parseable"] += 1
        parseable.append((sid, source))
        if result.round_trip == "EXACT":
            row["round_trip_exact"] += 1
            served.append((sid, corpus, result.surface, result.term_skeleton))
            if not rt.surface_words_are_covered(result.surface, lex):
                row["r2_words_outside_sources"] += 1
                r2_breaches.append({"statement_id": sid, "corpus": corpus,
                                    "surface": result.surface})
        else:
            row["round_trip_failed"] += 1
            round_trip_failures.append({
                "statement_id": sid, "corpus": corpus, "source": source,
                "term_skeleton": result.term_skeleton,
                "reparse_skeleton": result.reparse_skeleton,
                "surface": result.surface,
            })

    corpora = []
    totals = Counter()
    for corpus in corpus_order:
        row = per_corpus[corpus]
        totals.update(row)
        thin = row["parseable"] < THIN_DENOMINATOR
        corpora.append({
            "corpus": corpus,
            "nodes": row["nodes"],
            "parseable": row["parseable"],
            "parse_rate": _rate(row["parseable"], row["nodes"]),
            "round_trip_exact": row["round_trip_exact"],
            "round_trip_failed": row["round_trip_failed"],
            "refused_after_parse": row["refused_after_parse"],
            "r2_words_outside_sources": row["r2_words_outside_sources"],
            "round_trip_rate_over_parseable": _rate(row["round_trip_exact"],
                                                    row["parseable"]),
            "thin_denominator": thin,
            "r1_per_corpus_floor_applies": not thin,
            "r1_per_corpus_verdict": (
                "n/a (thin denominator: reported individually, never averaged)"
                if thin else
                ("FIRES" if _rate(row["round_trip_exact"], row["parseable"])
                 >= R1_FLOOR else "MISSES")
            ),
            "parse_failure_classes": dict(sorted(
                parse_failures[corpus].items(), key=lambda kv: (-kv[1], kv[0]))),
        })
    corpora.sort(key=lambda r: (-r["parseable"], r["corpus"]))

    r1_rate = _rate(totals["round_trip_exact"], totals["parseable"])
    all_classes: Counter = Counter()
    for counter in parse_failures.values():
        all_classes.update(counter)

    return {
        "corpora": corpora,
        "totals": totals,
        "r1_rate": r1_rate,
        "parse_failure_classes": dict(sorted(all_classes.items(),
                                             key=lambda kv: (-kv[1], kv[0]))),
        "refusals": refusals,
        "round_trip_failures": round_trip_failures,
        "r2_breaches": r2_breaches,
        "served": served,
        "parseable_sources": sorted(parseable),
    }


def surface_sample(served: list[tuple[str, str, str, str]]) -> dict:
    """M2 at corpus scale: 25 surfaces verbatim, and a digest over all of them.

    The digest is what makes future rendering drift detectable without
    committing 2,170 sentences: any lexicon or grammar edit that changes one
    emitted surface changes this hex string, and the 25 pinned rows make the
    first such change readable rather than merely visible.
    """
    rows = sorted(served, key=lambda r: r[0])
    joined = "\n".join(f"{sid}\t{surface}" for sid, _c, surface, _s in rows)
    return {
        "what": (
            "The served surfaces, pinned. `digest_over_all` is sha256 over "
            "'<statement_id>\\t<surface>' for every served realization, sorted "
            "by statement_id and joined with newlines. It is R5 at corpus "
            "scale: same terms, same lexicon, same parameters, same bytes."
        ),
        "served_count": len(rows),
        "digest_algorithm": (
            "sha256 of '\\n'.join(f'{statement_id}\\t{surface}') over all "
            "served realizations sorted by statement_id, UTF-8"
        ),
        "digest_over_all": hashlib.sha256(joined.encode("utf-8")).hexdigest(),
        "first_n_by_statement_id": SURFACE_SAMPLE_SIZE,
        "sample": [
            {"statement_id": sid, "corpus": corpus, "surface": surface,
             "term_skeleton": skel}
            for sid, corpus, surface, skel in rows[:SURFACE_SAMPLE_SIZE]
        ],
    }


# --------------------------------------------------------------------------
# C-R1 — the scrambled realizer, one-sided
# --------------------------------------------------------------------------


def _derange(items: list[str], rng: random.Random) -> list[str]:
    """A permutation with no fixed point. Deterministic given `rng`."""
    if len(items) < 2:
        return list(items)
    shuffled = list(items)
    rng.shuffle(shuffled)
    for i, value in enumerate(shuffled):
        if value == items[i]:
            j = (i + 1) % len(shuffled)
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    # One more pass closes the wrap-around case for tiny lists.
    for i, value in enumerate(shuffled):
        if value == items[i]:
            j = i - 1
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    return shuffled


def scrambled_lexicon(raw: dict, seed_hex: str) -> tuple[rlex.Lexicon, dict]:
    """Derange head/operator/relation phrases. Structure words are left alone.

    Deranging WITHIN each section preserves the section's phrase multiset, so
    the table is still injective both ways, still prefix-free and still
    numeral-disjoint — it loads through the same R2b gate the committed table
    does, which is the point: the control is a wrong table, not a broken one.

    Grouping words are deliberately untouched.  A scramble that also broke
    parenthesization would fail at the tokenizer and prove nothing about
    whether stage 2 reads the WORDS.
    """
    rng = random.Random(int(seed_hex[:16], 16))
    doc = json.loads(json.dumps(raw))
    moved = {}
    for section in ("operators", "relations", "call_heads"):
        keys = sorted(doc[section])
        phrases = [doc[section][k] for k in keys]
        deranged = _derange(phrases, rng)
        for key, phrase in zip(keys, deranged):
            doc[section][key] = phrase
        moved[section] = sum(1 for a, b in zip(phrases, deranged) if a != b)
    return rlex.build(doc, "<scrambled>"), moved


class _ScrambledNumerals:
    """A scrambled digit map, installed around `numeral_words` for the control.

    Design §7 names it: *"numerals through a scrambled digit map"*.  The
    numeral pair is algorithmic rather than a table, so the scramble is a
    derangement of the ten digits applied to the literal's decimal spelling
    before it is put into words.  Every digit changes, so every numeral
    changes, and the committed pair reads the sentence back to a different
    number.
    """

    def __init__(self, rng: random.Random) -> None:
        digits = [str(d) for d in range(10)]
        self.map = dict(zip(digits, _derange(digits, rng)))
        self._real_number_to_words = nw.number_to_words

    def number_to_words(self, value):
        text = self._real_number_to_words(value)  # validates the domain first
        spelled = repr(float(value))
        if spelled.endswith(".0"):
            spelled = spelled[:-2]
        scrambled = "".join(self.map.get(ch, ch) for ch in spelled)
        try:
            return self._real_number_to_words(float(scrambled))
        except (nw.NumeralError, ValueError):
            return text

    def __enter__(self):
        nw.number_to_words = self.number_to_words
        return self

    def __exit__(self, *exc):
        nw.number_to_words = self._real_number_to_words
        return False


def control_c_r1(sources: list[tuple[str, str]], lex: rlex.Lexicon,
                 raw: dict, lexicon_digest: str, true_exact: int) -> dict:
    """Realize through the deranged table, read through the committed one."""
    scrambled, moved = scrambled_lexicon(raw, lexicon_digest)
    rng = random.Random(int(lexicon_digest[16:32], 16))

    passes = 0
    unreadable = 0
    different_skeleton = 0
    refused = 0
    examples: list[dict] = []

    with _ScrambledNumerals(rng) as numerals:
        digit_map = dict(numerals.map)
        for sid, source in sources:
            result = rt.realize(source, scrambled, statement_id=sid)
            if isinstance(result, rt.Refusal):
                refused += 1
                continue
            # ONE-SIDED: read the scrambled sentence with the COMMITTED table.
            recovered, _tokens = rt.reparse(result.surface, lex)
            if recovered is None:
                unreadable += 1
            elif recovered == result.term_skeleton:
                passes += 1
                if len(examples) < 10:
                    examples.append({
                        "statement_id": sid, "source": source,
                        "scrambled_surface": result.surface,
                        "recovered_skeleton": recovered,
                    })
            else:
                different_skeleton += 1

    total = len(sources)
    scrambled_rate = _rate(passes, total)
    true_rate = _rate(true_exact, total)
    if scrambled_rate == 0.0:
        contrast = None
        contrast_text = "unbounded (the scrambled realizer passed zero terms)"
    else:
        contrast = round(true_rate / scrambled_rate, 3)
        contrast_text = f"{contrast}x"

    if true_rate < C_R1_TRUE_FLOOR and scrambled_rate < C_R1_TRUE_FLOOR:
        verdict = "VOID (both near zero: the gate is untested)"
    elif scrambled_rate >= C_R1_SCRAMBLED_CEILING:
        verdict = "VOID (the scrambled realizer passed >= 1%: the gate is not reading the words)"
    elif contrast is None or contrast >= C_R1_CONTRAST_MULTIPLE:
        verdict = "INFORMATIVE"
    else:
        verdict = "VOID (contrast below 20x)"

    return {
        "control": "C-R1 (the scrambled realizer, as a contrast)",
        "one_sided": True,
        "why_one_sided": (
            "Emitted through the deranged table, read back through the "
            "COMMITTED one. A two-sided scramble — deranging the table and "
            "then reading through that same deranged table — is a consistent "
            "relabelling, still a bijection, and round-trips at 4 of 4 (pinned "
            "in tests/test_realize_term.py). It would report a near-perfect "
            "control and void this reading under the >= 1% clause for a reason "
            "with nothing to do with whether the gate reads the words."
        ),
        "scramble": {
            "seed": (
                "derived from the committed lexicon's own sha256_lf, so the "
                "derangement is a function of the table under test and not of "
                "a number someone chose"
            ),
            "seed_source_digest": lexicon_digest,
            "method": (
                "a fixed-point-free permutation of the phrases WITHIN each of "
                "operators, relations and call_heads; grouping words and the "
                "slot marker are untouched, because a scramble that broke "
                "parenthesization would fail at the tokenizer and prove "
                "nothing about whether stage 2 reads the words"
            ),
            "rows_moved": moved,
            "digit_map": digit_map,
            "slot_indices_deliberately_not_scrambled": (
                "skeleton() is invariant under slot RENAMING, so a bijective "
                "index scramble would pass 100% and measure nothing. Only a "
                "non-injective one would change a skeleton, and that is a "
                "different control than the one §7 registers."
            ),
        },
        "denominator": total,
        "true_realizer": {"passes": true_exact, "rate": true_rate},
        "scrambled_realizer": {
            "passes": passes,
            "rate": scrambled_rate,
            "failed_unreadable": unreadable,
            "failed_different_skeleton": different_skeleton,
            "refused_before_reading": refused,
            "failure_modes_note": (
                "Counted separately on purpose. `failed_unreadable` means the "
                "wrong tokens did not parse — that would be the tokenizer "
                "rejecting nonsense, not stage 2 reading words. "
                "`failed_different_skeleton` means the sentence parsed "
                "perfectly well and meant something else, which is the failure "
                "this control is supposed to produce."
            ),
        },
        "contrast_multiple": contrast,
        "contrast": contrast_text,
        "thresholds": {
            "informative_if_contrast_at_least": C_R1_CONTRAST_MULTIPLE,
            "void_if_scrambled_rate_at_least": C_R1_SCRAMBLED_CEILING,
            "void_if_both_below": C_R1_TRUE_FLOOR,
        },
        "verdict": verdict,
        "scrambled_passes_examples": examples,
    }


# --------------------------------------------------------------------------
# C-R2 — mechanical near-misses, verified before realizing
# --------------------------------------------------------------------------

_OP_SWAP = {"+": "*", "*": "+", "^": "*"}
_REL_SWAP = {"=": "<", "<": "=", ">": ">=", "<=": ">=", ">=": "<=",
             "approx": "=", "=>_d": "="}


def _alias_siblings() -> dict[str, str]:
    """MOD<->CONCAT, BEFORE<->LT, sum<->INTEGRAL, from the declared classes."""
    by_class: dict[str, list[str]] = {}
    for head, cls in sorted(HEAD_ALIASES.items()):
        by_class.setdefault(cls, []).append(head)
    out: dict[str, str] = {}
    for members in by_class.values():
        for i, head in enumerate(members):
            out[head] = members[(i + 1) % len(members)]
    return out


ALIAS_SIBLING = _alias_siblings()


def _replace_first(node: tuple, chooser) -> tuple | None:
    """Pre-order: replace the first node `chooser` accepts. Deterministic."""
    replacement = chooser(node)
    if replacement is not None:
        return replacement
    if node[0] in {"num", "slot"}:
        return None
    for i, arg in enumerate(node[2]):
        mutated = _replace_first(arg, chooser)
        if mutated is not None:
            args = list(node[2])
            args[i] = mutated
            return (node[0], node[1], tuple(args))
    return None


def _rule_swap_noncommutative_args(node: tuple) -> tuple | None:
    if node[0] == "rel" and node[1] not in SYMMETRIC_RELATIONS:
        return ("rel", node[1], (node[2][1], node[2][0]))
    if node[0] == "op" and node[1] == "^":
        return ("op", "^", (node[2][1], node[2][0]))
    if (node[0] == "call" and len(node[2]) == 2
            and node[1] not in COMMUTATIVE_CALL_HEADS):
        return ("call", node[1], (node[2][1], node[2][0]))
    return None


def _rule_operator_word_swap(node: tuple) -> tuple | None:
    if node[0] == "op" and node[1] in _OP_SWAP:
        return ("op", _OP_SWAP[node[1]], node[2])
    if node[0] == "rel" and node[1] in _REL_SWAP:
        return ("rel", _REL_SWAP[node[1]], node[2])
    return None


def _rule_alias_class_swap(node: tuple) -> tuple | None:
    if node[0] == "call" and node[1] in ALIAS_SIBLING:
        return ("call", ALIAS_SIBLING[node[1]], node[2])
    return None


def _make_head_swap_rule(heads: list[str]):
    """Replace the first call head with the next covered head in sorted order."""
    index = {head: i for i, head in enumerate(heads)}

    def rule(node: tuple) -> tuple | None:
        if node[0] == "call" and node[1] in index:
            return ("call", heads[(index[node[1]] + 1) % len(heads)], node[2])
        return None

    return rule


def _realize_tree(tree: tuple, lex: rlex.Lexicon) -> str | None:
    """Linearize an already-canonical tree with realize_term's OWN linearizer.

    A transcription of `realize()`'s body from the point the tree exists.
    Kept here rather than added to `realize_term.py` so the pinned inverter
    stays byte-frozen through the run it is being measured by.
    """
    names: list[str] = []
    rt._slot_order(tree, names)
    linearizer = rt._Linearizer(lex, {n: i for i, n in enumerate(names)})
    try:
        return " ".join(linearizer.emit(tree, rt.LEVEL_RELATION))
    except (rt.RefusalError, RecursionError):
        return None


def control_c_r2(sources: list[tuple[str, str]], lex: rlex.Lexicon) -> dict:
    """One mutation per applicable rule per served term, verified first."""
    heads = sorted(lex.call_heads)
    rules = [
        ("swap_noncommutative_args", _rule_swap_noncommutative_args),
        ("operator_word_swap", _rule_operator_word_swap),
        ("alias_class_swap", _rule_alias_class_swap),
        ("head_swap", _make_head_swap_rule(heads)),
    ]

    per_rule: dict[str, Counter] = {name: Counter() for name, _ in rules}
    round_tripped_to_source: list[dict] = []
    examples: dict[str, dict] = {}
    generated = 0
    reparsed_different = 0
    unreadable = 0

    for sid, source in sources:
        try:
            tree = canonicalize(Parser(tokenize(source)).parse())
        except (TemplateParseError, RecursionError):   # pragma: no cover
            continue
        source_skeleton = skeleton(tree)
        for name, rule in rules:
            counter = per_rule[name]
            mutated = _replace_first(tree, rule)
            if mutated is None:
                counter["not_applicable"] += 1
                continue
            mutated = canonicalize(mutated)
            mutated_skeleton = skeleton(mutated)
            if mutated_skeleton == source_skeleton:
                # VERIFIED BEFORE REALIZING, per the design: a swap that does
                # not change the canonical skeleton is discarded, never counted.
                counter["discarded_skeleton_unchanged"] += 1
                continue

            counter["generated"] += 1
            generated += 1
            surface = _realize_tree(mutated, lex)
            if surface is None:
                counter["refused"] += 1
                unreadable += 1
                continue
            recovered, _tokens = rt.reparse(surface, lex)
            if recovered is None:
                counter["failed_to_parse"] += 1
                unreadable += 1
            elif recovered == source_skeleton:
                counter["round_tripped_to_source"] += 1
                round_tripped_to_source.append({
                    "statement_id": sid, "rule": name, "source": source,
                    "source_skeleton": source_skeleton,
                    "mutated_skeleton": mutated_skeleton,
                    "surface": surface,
                })
            else:
                counter["reparsed_to_a_different_skeleton"] += 1
                reparsed_different += 1
                if name not in examples:
                    examples[name] = {
                        "statement_id": sid, "source": source,
                        "source_skeleton": source_skeleton,
                        "mutated_skeleton": mutated_skeleton,
                        "recovered_skeleton": recovered,
                        "mutated_surface": surface,
                    }

    reparse_rate = _rate(reparsed_different, generated)
    if round_tripped_to_source:
        verdict = ("VOID (a skeleton-changing near-miss round-tripped to the "
                   "SOURCE skeleton: canonicalization is collapsing a "
                   "distinction)")
    elif reparse_rate < C_R2_REPARSE_FLOOR:
        verdict = ("UNINFORMATIVE (under the 50% floor: the set is exercising "
                   "the tokenizer, not the canonicalizer)")
    else:
        verdict = "INFORMATIVE"

    return {
        "control": "C-R2 (the near-miss)",
        "construction": (
            "Mechanical, and verified BEFORE realizing: every mutation is "
            "applied to the canonical TREE and its skeleton compared to the "
            "source's before any sentence exists. A mutation that does not "
            "change the skeleton is DISCARDED and never counted, which is the "
            "design's rule — canonicalize legitimately erases "
            "commutative-argument order and symmetric-relation sides, and a "
            "control built from those would void the gate for behaving "
            "correctly."
        ),
        "alias_classes_included": (
            "Per the design's 2026-08-23 correction: canonicalize does NO head "
            "aliasing (alias_heads is a separate pass only the ALIASED match "
            "level runs), so MOD vs CONCAT is a real skeleton-changing "
            "near-miss and belongs IN the set rather than among its "
            "exclusions."
        ),
        "one_mutation_per_rule_per_served_term": True,
        "denominator_terms": len(sources),
        "mutations_generated": generated,
        "reparsed_to_a_different_skeleton": reparsed_different,
        "failed_to_parse_or_refused": unreadable,
        "round_tripped_to_source": len(round_tripped_to_source),
        "reparse_rate": reparse_rate,
        "thresholds": {
            "void_if_any_round_trips_to_source": 0,
            "uninformative_below_reparse_rate": C_R2_REPARSE_FLOOR,
        },
        "verdict": verdict,
        "per_rule_accounting": (
            "Every term gets exactly one disposition per rule: "
            "`not_applicable` (the rule found no node to mutate), "
            "`discarded_skeleton_unchanged` (it mutated something but the "
            "canonical skeleton did not move, so it is NOT a near-miss and is "
            "not counted as one), or one of the four outcomes `refused`, "
            "`failed_to_parse`, `round_tripped_to_source`, "
            "`reparsed_to_a_different_skeleton`. `generated` is the sum of "
            "those four. The discards matter: `a < b` and `b < a` are the "
            "same skeleton because render_skeleton erases slot identity and "
            "renumbers by first occurrence, so a set built on the assumption "
            "that swapping a non-symmetric relation always changes the "
            "skeleton would be full of non-mutations, every one of which "
            "would 'round-trip to the source' and void this control for "
            "behaving correctly."
        ),
        "per_rule": {name: dict(sorted(counter.items()))
                     for name, counter in sorted(per_rule.items())},
        "per_rule_examples": {k: examples[k] for k in sorted(examples)},
        "voiding_cases": round_tripped_to_source,
    }


# --------------------------------------------------------------------------
# The artifact
# --------------------------------------------------------------------------


def build_artifact(data_dir: Path, lexicon_path: Path | None = None,
                   prereg_path: Path | None = None) -> dict:
    """The whole registered run. Raises `PreregMismatch` before measuring."""
    c_r3 = revalidate_prereg(prereg_path)
    path = lexicon_path or rlex.DEFAULT_LEXICON_PATH
    lex = rlex.load(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    lexicon_digest = sha256_lf_file(path)

    body = measure(data_dir, lex)
    totals = body["totals"]
    r1_rate = body["r1_rate"]
    # Both controls run over exactly the set R1's rate was read on — R1's
    # denominator, not a set assembled separately, so the contrast in C-R1 is
    # a contrast on one population.
    parseable_sources = body["parseable_sources"]

    c_r1 = control_c_r1(parseable_sources, lex, raw, lexicon_digest,
                        totals["round_trip_exact"])
    c_r2 = control_c_r2(parseable_sources, lex)

    thick = [row for row in body["corpora"] if not row["thin_denominator"]]
    thin = [row for row in body["corpora"] if row["thin_denominator"]]

    return {
        "run_id": RUN_ID,
        "registered": REGISTERED_ON,
        "design": "docs/DESIGN-sans-template-rendering.md",
        "roadmap": "docs/ROADMAP-v0.18.md",
        "provenance": provenance_block(
            Path(__file__),
            sorted(data_dir.glob("*/nodes.json")) + [
                path,
                REPO_ROOT / "scripts" / "realize_term.py",
                REPO_ROOT / "scripts" / "realization_lexicon.py",
                REPO_ROOT / "scripts" / "numeral_words.py",
                REPO_ROOT / "scripts" / "match_signatures.py",
                prereg_path or PREREG_PATH,
            ],
        ),
        "what_this_is": [
            "The ONE registered full-corpus run named in "
            "DESIGN-sans-template-rendering §10. R0's parse table, R1's "
            "round-trip rate over the parseable denominator, R2's "
            "corpus-scale sweep, R5's surface digest, and the three blind "
            "controls C-R1..C-R3.",
            "It is byte-reproducible: no timestamp, no elapsed time, no "
            "absolute path. The C-R1 derangement is seeded from the committed "
            "lexicon's own digest and C-R2's mutation choice is the first "
            "applicable node in a fixed pre-order walk.",
            "It refuses to exist if C-R3 fails. The digest revalidation runs "
            "before a single term is realized.",
        ],
        "c_r3": c_r3,
        "r0": {
            "gate": "R0 — construction prerequisite, discharged before R1 is read",
            "source_field": "formal_statement.canonical_ascii",
            "parser": "scripts/match_signatures.py (byte-frozen, C-R3-pinned)",
            "nodes_total": totals["nodes"],
            "nodes_parseable": totals["parseable"],
            "parse_rate": _rate(totals["parseable"], totals["nodes"]),
            "failure_classes": body["parse_failure_classes"],
            "failure_classes_note": (
                "Named per corpus in the table below as well. A term that "
                "does not parse has no source skeleton to round-trip to, so "
                "it never enters R1's denominator."
            ),
            "stop_condition_check": {
                "rule": ("Stop and publish if R0 leaves NO corpus with >= 50 "
                         "parseable terms."),
                "corpora_at_or_above_50_parseable": [r["corpus"] for r in thick],
                "fired": not thick,
            },
            "table": body["corpora"],
        },
        "r1": {
            "gate": "R1 — round-trip floor",
            "floor": R1_FLOOR,
            "denominator": totals["parseable"],
            "numerator": totals["round_trip_exact"],
            "rate": r1_rate,
            "verdict": "FIRES" if r1_rate >= R1_FLOOR else "MISSES",
            "sentence": (
                f"{totals['round_trip_exact']} of {totals['parseable']} "
                f"parseable terms round-trip to the source skeleton "
                f"({r1_rate:.4f}); the floor is {R1_FLOOR:.2f} of the same "
                f"parseable denominator of {totals['parseable']}, out of "
                f"{totals['nodes']} corpus nodes."
            ),
            "per_corpus_floor_applies_to": [r["corpus"] for r in thick],
            "thin_corpora_reported_individually": [
                {
                    "corpus": r["corpus"],
                    "parseable": r["parseable"],
                    "round_trip_exact": r["round_trip_exact"],
                    "round_trip_failed": r["round_trip_failed"],
                    "refused_after_parse": r["refused_after_parse"],
                }
                for r in thin
            ],
            "stop_condition_check": {
                "rule": "Stop and publish the failure list if R1 lands under 50%.",
                "fired": r1_rate < 0.50,
            },
            "lost_is_zero": {
                "rule": ("Every term in the parseable denominator that did not "
                         "round-trip is listed here by statement id. Nothing "
                         "is summarized away."),
                "round_trip_failures": body["round_trip_failures"],
                "refused_after_parse": body["refusals"],
                "accounted": (totals["round_trip_exact"]
                              + len(body["round_trip_failures"])
                              + len(body["refusals"])),
                "denominator": totals["parseable"],
                "balances": (totals["round_trip_exact"]
                             + len(body["round_trip_failures"])
                             + len(body["refusals"])) == totals["parseable"],
            },
        },
        "r2": {
            "gate": "R2 — no invented surface",
            "swept": totals["round_trip_exact"],
            "words_outside_the_lexicon_or_numeral_pair":
                totals["r2_words_outside_sources"],
            "rate": _rate(totals["r2_words_outside_sources"],
                          totals["round_trip_exact"]),
            "verdict": "CLEAN" if not totals["r2_words_outside_sources"] else "BREACHED",
            "breaches": body["r2_breaches"],
            "what_counts_as_a_source": (
                "A lexicon phrase word, or a word the registered numeral pair "
                "(scripts/numeral_words) can emit. Nothing else."
            ),
        },
        "r5": surface_sample(body["served"]),
        "c_r1": c_r1,
        "c_r2": c_r2,
    }


def print_summary(artifact: dict) -> None:
    r0, r1, r2 = artifact["r0"], artifact["r1"], artifact["r2"]
    print(f"registered run {artifact['run_id']}  ({artifact['registered']})")
    print(f"C-R3: {artifact['c_r3']['verdict']} "
          f"({len(artifact['c_r3']['revalidated'])} pinned artifacts revalidated)")
    print()
    head = (f"{'corpus':30s} {'nodes':>7s} {'parse':>7s} {'parse%':>8s} "
            f"{'exact':>7s} {'fail':>6s} {'refus':>6s} {'rt%':>8s}")
    print(head)
    print("-" * len(head))
    for row in r0["table"]:
        mark = " *" if row["thin_denominator"] else "  "
        print(f"{row['corpus'][:30]:30s} {row['nodes']:7d} {row['parseable']:7d} "
              f"{row['parse_rate']:8.4f} {row['round_trip_exact']:7d} "
              f"{row['round_trip_failed']:6d} {row['refused_after_parse']:6d} "
              f"{row['round_trip_rate_over_parseable']:8.4f}{mark}")
    print("-" * len(head))
    print(f"{'TOTAL':30s} {r0['nodes_total']:7d} {r0['nodes_parseable']:7d} "
          f"{r0['parse_rate']:8.4f} {r1['numerator']:7d} "
          f"{len(r1['lost_is_zero']['round_trip_failures']):6d} "
          f"{len(r1['lost_is_zero']['refused_after_parse']):6d} "
          f"{r1['rate']:8.4f}")
    print("  * thin denominator (< 50 parseable): reported individually, "
          "never averaged")
    print()
    print("R0 failure classes: " + ", ".join(
        f"{v} {k}" for k, v in r0["failure_classes"].items()))
    print(f"R0 stop condition fired: {r0['stop_condition_check']['fired']}")
    print()
    print("R1: " + r1["sentence"])
    print(f"R1 verdict: {r1['verdict']} (floor {r1['floor']:.2f})   "
          f"LOST=0 balances: {r1['lost_is_zero']['balances']}")
    print(f"R2: {r2['words_outside_the_lexicon_or_numeral_pair']} of "
          f"{r2['swept']} served surfaces carry a word outside the two "
          f"sources — {r2['verdict']}")
    print(f"R5: surface digest over {artifact['r5']['served_count']} served "
          f"surfaces = {artifact['r5']['digest_over_all']}")
    print()
    c1, c2 = artifact["c_r1"], artifact["c_r2"]
    print(f"C-R1  true {c1['true_realizer']['passes']}/{c1['denominator']} "
          f"({c1['true_realizer']['rate']:.4f})  scrambled "
          f"{c1['scrambled_realizer']['passes']}/{c1['denominator']} "
          f"({c1['scrambled_realizer']['rate']:.4f})  contrast "
          f"{c1['contrast']}")
    print(f"      scrambled failures: "
          f"{c1['scrambled_realizer']['failed_different_skeleton']} parsed to a "
          f"different skeleton, "
          f"{c1['scrambled_realizer']['failed_unreadable']} did not parse")
    print(f"C-R1 verdict: {c1['verdict']}")
    print(f"C-R2  {c2['mutations_generated']} mutations generated, "
          f"{c2['reparsed_to_a_different_skeleton']} re-parsed to a different "
          f"skeleton ({c2['reparse_rate']:.4f}), "
          f"{c2['round_tripped_to_source']} round-tripped to the SOURCE")
    for name, counts in c2["per_rule"].items():
        print(f"      {name:28s} generated {counts.get('generated', 0):5d}  "
              f"discarded {counts.get('discarded_skeleton_unchanged', 0):5d}  "
              f"n/a {counts.get('not_applicable', 0):5d}")
    print(f"C-R2 verdict: {c2['verdict']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path,
                        default=Path("experiments/realization_rate.json"))
    parser.add_argument("--lexicon", type=Path, default=None)
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--prereg", type=Path, default=None)
    args = parser.parse_args(argv)

    closed = closed_by_amendment(args.prereg)
    if closed is not None and not args.no_write:
        print(f"REFUSING TO WRITE: {closed}", file=sys.stderr)
        return 4

    started = time.time()
    try:
        artifact = build_artifact(args.data_dir, args.lexicon, args.prereg)
    except PreregMismatch as exc:
        print(f"REFUSING TO WRITE: {exc}", file=sys.stderr)
        return 3
    print_summary(artifact)
    print(f"\nwall clock: {time.time() - started:.1f}s "
          f"(not recorded in the artifact — it must stay byte-reproducible)")

    if not args.no_write:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(
            (json.dumps(artifact, indent=2, ensure_ascii=False) + "\n")
            .encode("utf-8")
        )
        print(f"registered run written to {args.out}")

    voided = ("VOID" in artifact["c_r1"]["verdict"]
              or "VOID" in artifact["c_r2"]["verdict"])
    return 1 if voided else 0


if __name__ == "__main__":
    raise SystemExit(main())
