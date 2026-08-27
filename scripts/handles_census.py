#!/usr/bin/env python3
"""H-P0 -- the coverage census `DESIGN-handles.md` §6 orders before anything.

This is a **measurement only**. It builds no handle table, freezes no
budget, seals no question set. It answers one question per source, from
committed producers and committed corpora:

    exactly which statements does this source yield a handle for, and how
    many statements does each of those handles resolve to?

The three sources are the three `DESIGN-handles.md` §3 kept after review
deleted S4 and S5 and demoted S3:

- **S-LEX** -- the per-node `symbol_lexicon` glossary that
  `resolver.by_lexicon` is built from (`scripts/resolver.py:264-277`).
  A handle is a content word of a glossary entry's `name`, `description`
  or `semantic_role`, lowercased, `resolver.STOPWORDS` removed. That is
  the resolver's own field set and its own reduction, restated here rather
  than imported through `build_index`, because `build_index` returns the
  inverted index and this census needs the per-statement forward map that
  produced it. The two are cross-checked in
  `tests/test_handles_census.py`.
- **S-INV** -- `match_signatures.template_call_heads`
  (`scripts/match_signatures.py:952`, reached through `load_nodes` at
  `:1038`) over each node's `anonymized_template`. Title-free by
  construction: it reads `structural_signature.anonymized_template` and
  nothing else. This is the producer review N2 substituted for the
  draft's `resolver._inventory_strings`, which reads `title` and
  `keywords` and could not pass B3's audit.
- **S-SKEL** -- the family skeleton `measure_compression.py` computes
  (via the same `load_nodes`, field `family`). The strings are not
  persisted anywhere in the tree -- `reports/compression.json` carries
  `family_reuse` counts and no skeleton -- so this census writes the
  id->skeleton table the design says it owes, to
  `experiments/skeleton_index.json`.

Neither this writer nor either of its two producers reads `title` or
`keywords`. S-LEX reads `symbol_lexicon`; S-INV and S-SKEL read
`structural_signature`. B3's producer audit is not this artifact's job --
the table does not exist yet -- but the census would be worthless if its
own inputs were title-derived, so `tests/test_handles_census.py` asserts
the absence by AST over this module.

**Specificity.** K = 128 per `DESIGN-handles.md` §7 B2: a handle is
*specific* when it resolves to at most K statements. K is not re-frozen
here. B2 says the distribution this census publishes is what a re-freeze
would be argued from, and that is all this file does with it.

**S3 is priced, not built.** `foreign_voice.py` drops every serialized
term it computes (`Receipt` has no field for it;
`foreign_voice.py:486-498` lets `answers` fall out of scope), so a term
layer would have to persist them. This census counts the statements whose
terms would need persisting, and measures the pinned checker's per-call
cost over 20 real calls so the runtime is a measured number rather than a
guess. The 20 calls double as a check that the pinned toolchain still
reproduces the committed digests.

Writes:
    experiments/handles_census.json
    experiments/skeleton_index.json
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from match_signatures import load_nodes  # noqa: E402
from report_provenance import provenance_block  # noqa: E402
from resolver import STOPWORDS  # noqa: E402

SCHEMA = "handles_census.v1"
SKELETON_SCHEMA = "skeleton_index.v1"

#: `DESIGN-handles.md` §7 B2. Not re-frozen here; published against.
DEFAULT_K = 128

#: The exact word rule `resolver.build_index` applies to glossary strings
#: (`scripts/resolver.py:117`, `:273-275`).
_WORD = re.compile(r"[a-z0-9_]+")

#: The five glossary groups `resolver.build_index:266-267` walks.
LEXICON_GROUPS = ("symbols", "operators", "functionals", "constants", "index_sets")

#: The three entry keys it reads (`scripts/resolver.py:271`).
LEXICON_KEYS = ("name", "description", "semantic_role")

#: Histogram edges for a resolves-to-count distribution. Closed upper
#: bounds; K = 128 is an edge so the specific/overbroad cut is readable
#: off the histogram without recomputing it.
BUCKET_EDGES = (1, 2, 4, 8, 16, 32, 64, 128, 256, 1024, 4096, 16384)


# --------------------------------------------------------------------------
# producers
# --------------------------------------------------------------------------


def corpus_rows(data_dir: Path) -> list[tuple[str, str, dict]]:
    """`(corpus, statement_id, raw node)` for every committed statement.

    Sorted by corpus directory then by file order, which is the order
    every other reader in the tree uses (`sorted(glob("*/nodes.json"))`).
    """

    rows: list[tuple[str, str, dict]] = []
    for path in sorted(data_dir.glob("*/nodes.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        for node in document.get("statement_nodes", []):
            sid = node.get("statement_id")
            if isinstance(sid, str):
                rows.append((path.parent.name, sid, node))
    return rows


def slex_handles(node: dict) -> set[str]:
    """S-LEX: the glossary words `resolver.by_lexicon` is keyed on.

    Deliberately a forward map. `build_index` yields word -> ids; this
    yields id -> words, from the same fields under the same reduction, so
    a per-statement coverage question can be asked at all.
    """

    lexicon = node.get("symbol_lexicon") or {}
    words: set[str] = set()
    for group in LEXICON_GROUPS:
        for entry in lexicon.get(group) or []:
            if not isinstance(entry, dict):
                continue
            for key in LEXICON_KEYS:
                value = entry.get(key)
                if isinstance(value, str):
                    words.update(_WORD.findall(value.lower()))
    return words - STOPWORDS


def slex_name_handles(node: dict) -> set[str]:
    """S-LEX restricted to `name`, the sensitivity reading.

    §3's table calls the source "`symbol_lexicon` **names**" while the
    producer it cites (`resolver.by_lexicon`) reads three keys. Both
    readings are published; neither is quietly chosen.
    """

    lexicon = node.get("symbol_lexicon") or {}
    words: set[str] = set()
    for group in LEXICON_GROUPS:
        for entry in lexicon.get(group) or []:
            if isinstance(entry, dict) and isinstance(entry.get("name"), str):
                words.update(_WORD.findall(entry["name"].lower()))
    return words - STOPWORDS


def parsed_by_id(data_dir: Path):
    """`match_signatures.load_nodes` keyed by id. S-INV and S-SKEL both."""

    nodes, problems = load_nodes(data_dir)
    return {n.statement_id: n for n in nodes}, problems


# --------------------------------------------------------------------------
# distribution
# --------------------------------------------------------------------------


def resolves_to(forward: dict[str, set[str]]) -> collections.Counter:
    """handle -> how many statements it resolves to."""

    counts: collections.Counter = collections.Counter()
    for handles in forward.values():
        for handle in handles:
            counts[handle] += 1
    return counts


def distribution(counts: collections.Counter, k: int) -> dict:
    """The resolves-to-count distribution B2 says a K re-freeze argues from."""

    values = sorted(counts.values())
    if not values:
        return {"distinct_handles": 0, "histogram": {}, "specific_handles": 0,
                "overbroad_handles": 0, "quantiles": {}, "max": 0,
                "most_resolving": []}
    buckets: dict[str, int] = {}
    lo = 0
    for edge in BUCKET_EDGES:
        label = f"{lo + 1}" if edge == lo + 1 else f"{lo + 1}-{edge}"
        buckets[label] = sum(1 for v in values if lo < v <= edge)
        lo = edge
    buckets[f">{BUCKET_EDGES[-1]}"] = sum(1 for v in values if v > BUCKET_EDGES[-1])

    def quantile(q: float) -> int:
        return values[min(len(values) - 1, int(q * len(values)))]

    return {
        "distinct_handles": len(values),
        "specific_handles": sum(1 for v in values if v <= k),
        "overbroad_handles": sum(1 for v in values if v > k),
        "min": values[0],
        "max": values[-1],
        "mean": round(statistics.fmean(values), 4),
        "median": statistics.median(values),
        "quantiles": {"p50": quantile(0.50), "p90": quantile(0.90),
                      "p99": quantile(0.99)},
        "histogram": buckets,
        # NOT `counts.most_common(25)`. `resolves_to` accumulates over
        # per-statement SETS, so the counter's insertion order — and
        # therefore `most_common`'s tie order — follows PYTHONHASHSEED.
        # Measured across three seeds: five leaves of this list moved,
        # and at one seed the twenty-fifth entry was a different handle
        # entirely, because two handles tied on the cut. Ties break on
        # the handle's own bytes, which is the rule `full_head_index`
        # already used and the rule DESIGN-handles §4 freezes one layer
        # up for candidate truncation.
        "most_resolving": [
            {"handle": handle, "resolves_to_count": count}
            for handle, count in sorted(counts.items(),
                                        key=lambda kv: (-kv[1], kv[0]))[:25]
        ],
    }


def coverage(forward: dict[str, set[str]], counts: collections.Counter,
             corpus_of: dict[str, str], k: int) -> dict:
    """Which statements this source yields a handle for -- and a specific one."""

    any_handle = {sid for sid, hs in forward.items() if hs}
    specific = {sid for sid, hs in forward.items()
                if any(counts[h] <= k for h in hs)}
    return {
        "statements_with_any_handle": len(any_handle),
        "statements_with_specific_handle": len(specific),
        "statements_with_no_handle": len(forward) - len(any_handle),
        "statements_with_only_overbroad_handles":
            len(any_handle) - len(specific),
        "specific_by_corpus": dict(sorted(
            collections.Counter(corpus_of[s] for s in specific).items())),
        "any_by_corpus": dict(sorted(
            collections.Counter(corpus_of[s] for s in any_handle).items())),
        "_specific_ids": specific,
        "_any_ids": any_handle,
    }


def strip_private(block: dict) -> dict:
    return {k: v for k, v in block.items() if not k.startswith("_")}


# --------------------------------------------------------------------------
# K sensitivity -- what B2's re-freeze would and would not buy
# --------------------------------------------------------------------------


def cheapest_handle(forward: dict[str, set[str]],
                    counts: collections.Counter) -> dict[str, int]:
    """Each statement's most specific handle, as a resolves-to-count.

    A statement has a specific handle at K exactly when this number is
    <= K, so the whole K sweep reduces to comparisons against one integer
    per statement instead of a rescan per K. Equivalent by construction:
    `any(counts[h] <= K)` is `min(counts[h]) <= K`.
    """

    out: dict[str, int] = {}
    for sid, handles in forward.items():
        out[sid] = min((counts[h] for h in handles), default=1 << 30)
    return out


def k_sensitivity(slex_min: dict[str, int], sinv_min: dict[str, int],
                  corpus_of: dict[str, str], k: int) -> dict:
    """B2's re-freeze argument, measured rather than asserted.

    B2 says that if K strands whole corpora with no specific handle, K is
    re-frozen from this census's distribution by dated amendment before
    the table run. That trigger was measured by this census
    (lean_workbook's specific-S-LEX coverage is 0 of 12,514) and has to
    be adjudicated, not merely reported -- so this block publishes the
    two things an adjudication needs: how wide the plateau around K is,
    and what a re-freeze would actually buy.
    """

    total = len(slex_min)
    union_min = {sid: min(slex_min[sid], sinv_min[sid]) for sid in slex_min}
    bulk = [sid for sid in slex_min if corpus_of[sid] == "lean_workbook"]

    def at(series: dict[str, int], threshold: int,
           members: list[str] | None = None) -> int:
        pool = members if members is not None else list(series)
        return sum(1 for sid in pool if series[sid] <= threshold)

    def plateau(series: dict[str, int]) -> tuple[int, int, int]:
        base = at(series, k)
        low = k
        while low > 1 and at(series, low - 1) == base:
            low -= 1
        high = k
        while high < total and at(series, high + 1) == base:
            high += 1
        return base, low, high

    plateaus = {}
    for name, series in (("S-LEX", slex_min), ("S-INV", sinv_min),
                         ("typable union", union_min)):
        base, low, high = plateau(series)
        plateaus[name] = {"coverage_at_K": base, "invariant_for_K_in": [low, high],
                          "plateau_width": high - low + 1,
                          "K_is_interior": low < k < high}

    sweep = []
    for threshold in (16, 32, 64, k, 218, 219, 256, 301, 302, 305, 1024, 4096):
        sweep.append({
            "K": threshold,
            "S-LEX": at(slex_min, threshold),
            "S-INV": at(sinv_min, threshold),
            "typable_union": at(union_min, threshold),
            "union_pct": round(100.0 * at(union_min, threshold) / total, 4),
            "lean_workbook_specific_S-LEX": at(slex_min, threshold, bulk),
        })

    bulk_ceiling = max(row["lean_workbook_specific_S-LEX"] for row in sweep)
    first_rescue = next((row["K"] for row in sweep
                         if row["lean_workbook_specific_S-LEX"] > 0), None)

    return {
        "why_this_block_exists": (
            "B2's re-freeze trigger fires on K stranding whole corpora with "
            "no specific handle. This census measured exactly that condition "
            "-- lean_workbook's specific-S-LEX coverage is 0 of 12,514 -- so "
            "the trigger has to be adjudicated rather than reported and left."
        ),
        "plateaus": plateaus,
        "sweep": sweep,
        "what_a_refreeze_would_buy_the_bulk": {
            "smallest_K_giving_any_lean_workbook_statement_a_specific_S-LEX_handle":
                first_rescue,
            "the_token_that_K_admits": "ground_numeral",
            "what_that_token_is": (
                "a `semantic_role` value on the ingest template -- "
                "boilerplate, not a name a mathematician uses and not a "
                "phrase anybody types"
            ),
            "ceiling_on_bulk_S-LEX_coverage_at_any_K": bulk_ceiling,
            "ceiling_as_share_of_the_bulk": round(
                100.0 * bulk_ceiling / len(bulk), 4),
            "why_there_is_a_ceiling": (
                "the bulk carries nine distinct glossary tokens in total and "
                "six of them are held by more than 12,200 statements each. No "
                "threshold below the corpus size admits those six without "
                "admitting the whole corpus, so S-LEX coverage of the bulk "
                "cannot exceed the holders of the three rare ones however far "
                "K is raised."
            ),
        },
        "adjudication": {
            "dated": "2026-08-27",
            "trigger": (
                "DESIGN-handles.md §7 B2: if K = 128 strands whole corpora "
                "with no specific handle, K is re-frozen from H-P0's "
                "distribution by dated amendment BEFORE the table run"
            ),
            "verdict": "NOT FIRED",
            "reasons": [
                "(a) lean_workbook is not WHOLLY stranded. S-INV gives "
                f"{at(sinv_min, k, bulk)} of its 12,514 statements a specific "
                "handle at K = 128. The trigger's condition is a corpus with "
                "no specific handle, and this corpus has one source that "
                "reaches it.",
                "(b) the headline is not a knife-edge artifact of K's value. "
                f"S-LEX's coverage is invariant across K in "
                f"{plateaus['S-LEX']['invariant_for_K_in']}, and S-INV's and "
                f"the union's across "
                f"{plateaus['typable union']['invariant_for_K_in']} -- so K = "
                "128 sits INSIDE the plateau rather than on its edge, and any "
                "re-freeze within that range returns the identical numbers.",
                "(c) and the decisive one: no re-freeze rescues the bulk. The "
                f"smallest K at which S-LEX reaches a single lean_workbook "
                f"statement is {first_rescue}, and it does so by admitting one "
                "token -- `ground_numeral`, a boilerplate semantic_role -- "
                f"which is exactly what K exists to exclude. Even then it caps "
                f"at {bulk_ceiling} statements, "
                f"{round(100.0 * bulk_ceiling / len(bulk), 2)}% of the bulk, "
                "at every larger K forever. A re-freeze cannot turn the "
                "finding around; it can only buy 2% of the bulk by admitting "
                "the boilerplate the finding is about.",
            ],
            "consequence": (
                "K stays 128. No dated amendment to B2's number is owed, and "
                "this block is the record of the trigger being adjudicated "
                "rather than silently left measured."
            ),
            "what_would_change_this": (
                "a source that gives the bulk names. That is the census's "
                "headline -- the naming layer must be built, not indexed -- "
                "and it is a v0.23 rotation question, not a K question."
            ),
        },
    }


# --------------------------------------------------------------------------
# S3 -- the priced question
# --------------------------------------------------------------------------


def s3_price(repo_root: Path, oracle_calls: int) -> dict:
    """What term-serialization would cost, counted and timed.

    The two coverage numbers are **subset, never summed**
    (`docs/BACKLOG.md:1122-1133`'s anti-merge rule): 2,319 oracle-eligible
    statements, of which 2,313 are covered after the register's blocked
    ids are removed. Both are recomputed here from the committed rows
    rather than read off the summary keys that assert them.
    """

    preview_path = repo_root / "data" / "foreign_voice" / "eligibility_preview.json"
    register_path = repo_root / "data" / "foreign_voice" / "register.json"
    rate_path = repo_root / "experiments" / "foreign_voice_rate.json"
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    register = json.loads(register_path.read_text(encoding="utf-8"))
    rate = json.loads(rate_path.read_text(encoding="utf-8"))

    accepted = [row for row in preview["statements"] if row.get("accepted")]
    blocked = {sid for entry in register["entries"] for sid in entry["statement_ids"]}
    covered = [row for row in accepted if row["statement_id"] not in blocked]
    receipts = rate["b1"]["receipts"]

    block = {
        "question": (
            "what would S3 term-serialization cost, if a later slice took it"
        ),
        "why_it_is_a_price_and_not_a_source": (
            "the pinned oracle computes a serialization for every term and "
            "keeps only its sha256: `Receipt` (scripts/foreign_voice.py:182-191) "
            "has no field for the payload, and `gate` "
            "(scripts/foreign_voice.py:486-498) lets `answers` fall out of "
            "scope. A term layer would have to persist what that path throws "
            "away, so its cost is a storage cost plus a re-elaboration cost."
        ),
        "counts": {
            "oracle_eligible": len(accepted),
            "covered": len(covered),
            "register_blocked_ids": len(blocked),
            "anti_merge_note": (
                "covered is a SUBSET of oracle_eligible. The two are never "
                "summed (docs/BACKLOG.md:1122-1133). The difference, "
                f"{len(accepted) - len(covered)}, is eligible statements the "
                "register blocks."
            ),
            "eligible_by_corpus": dict(sorted(collections.Counter(
                row["corpus"] for row in accepted).items())),
            "covered_by_corpus": dict(sorted(collections.Counter(
                row["corpus"] for row in covered).items())),
        },
        "terms_that_would_need_persisting": {
            "one_per_covered_statement": len(covered),
            "two_per_covered_statement_identity_relation": 2 * len(covered),
            "definition": (
                "the identity relation serializes each covered statement "
                "twice -- the interpreted original and the delexicalized "
                "round-trip (scripts/foreign_voice.py:483-484). Persisting "
                "only the original is one term per statement; persisting what "
                "the relation actually elaborates is two. Both are published; "
                "they are alternative scopes, not addends."
            ),
            "receipts_committed": len(receipts),
        },
    }

    if oracle_calls <= 0:
        block["runtime_estimate"] = {
            "measured": False,
            "note": "run with --oracle-calls N to measure; nothing is estimated "
                    "from an unmeasured constant",
        }
        return block

    block["runtime_estimate"] = measure_oracle(repo_root, receipts, oracle_calls)
    est = block["runtime_estimate"]
    if est.get("measured"):
        per = est["per_call_seconds"]["median"]
        per_batched = est["batched_seconds_for_all"] / est["calls"]
        est["projected_seconds"] = {
            "basis": (
                "warm median per-call seconds x term count. Unbatched is one "
                "Lean process per term -- the ceiling. Batched is the same "
                "twenty terms in one process divided by twenty -- the floor. "
                "The real cost of a term-store build sits between them and "
                "depends on a batch size nobody has chosen yet."
            ),
            "one_term_per_covered_statement_unbatched":
                round(per * len(covered), 1),
            "two_terms_per_covered_statement_unbatched":
                round(per * 2 * len(covered), 1),
            "one_term_per_covered_statement_batched":
                round(per_batched * len(covered), 1),
            "two_terms_per_covered_statement_batched":
                round(per_batched * 2 * len(covered), 1),
        }
        chars = est["payload_chars"]["mean"]
        est["projected_store_bytes"] = {
            "basis": (
                "mean measured serialization length (UTF-8 chars, the "
                "serializations are ASCII S-expressions) x term count. Storage "
                "only: no index, no framing, no compression."
            ),
            "one_term_per_covered_statement": int(chars * len(covered)),
            "two_terms_per_covered_statement": int(chars * 2 * len(covered)),
        }
    return block


def measure_oracle(repo_root: Path, receipts: list[dict], n: int) -> dict:
    """`n` real calls to the pinned checker, timed one process per term.

    The terms are the first `n` committed `interpreted` terms in
    statement-id order, so the sample is on-distribution and the same
    every run. Each answer's digest is compared with the digest the
    committed receipt recorded: a timing run that did not really invoke
    the binary cannot reproduce a sha256 it never computed, so the
    measurement carries its own liveness proof.
    """

    try:
        import foreign_voice_oracle as fvo  # noqa: PLC0415
    except Exception as exc:  # pragma: no cover - import shape
        return {"measured": False, "reason": f"oracle module unavailable: {exc}"}

    try:
        oracle = fvo.load()
    except Exception as exc:
        return {"measured": False,
                "reason": f"pinned toolchain not resolvable: {exc}"}

    sample = sorted(receipts, key=lambda r: r["statement_id"])[:n]
    per_call: list[float] = []
    digest_matches = 0
    refusals = 0
    payload_chars: list[int] = []
    for index, receipt in enumerate(sample):
        start = time.perf_counter()
        answer = oracle.serialize([(f"h{index}", receipt["interpreted"])],
                                  batch_size=1)[f"h{index}"]
        per_call.append(time.perf_counter() - start)
        if answer.ok:
            payload_chars.append(len(answer.serialization))
            if answer.digest == receipt["orig_elab_digest"]:
                digest_matches += 1
        else:
            refusals += 1

    start = time.perf_counter()
    batched = oracle.serialize(
        [(f"b{i}", r["interpreted"]) for i, r in enumerate(sample)],
        batch_size=len(sample))
    batched_seconds = time.perf_counter() - start
    batched_ok = sum(1 for a in batched.values() if a.ok)

    warm = per_call[1:] or per_call
    return {
        "measured": True,
        "note": (
            "wall-clock, so this block is the only non-deterministic bytes in "
            "this artifact. Everything else recomputes byte-identical."
        ),
        "toolchain": oracle.toolchain,
        "calls": len(per_call),
        "sample": "first N committed receipts by statement_id, term = `interpreted`",
        "cold_first_call_seconds": round(per_call[0], 4),
        "cold_start_note": (
            "the first call is reported separately and excluded from "
            "`per_call_seconds` because it may pay for the OS bringing the "
            "toolchain and `import Lean` into cache, and on a cold box that "
            "cost can be large enough to move a mean of twenty. Whether it did "
            "on THIS run is readable from the two numbers: compare "
            "`cold_first_call_seconds` with `per_call_seconds.median`. The "
            "exclusion is a rule fixed before the run, not a reaction to what "
            "the run produced."
        ),
        "per_call_seconds": {
            "basis": "calls 2..N, one Lean process per term (batch_size=1)",
            "mean": round(statistics.fmean(warm), 4),
            "median": round(statistics.median(warm), 4),
            "min": round(min(warm), 4),
            "max": round(max(warm), 4),
        },
        "batched_seconds_for_all": round(batched_seconds, 4),
        "batched_ok": batched_ok,
        "liveness": {
            "digests_reproduced": digest_matches,
            "of": len(per_call),
            "refusals": refusals,
            "why": (
                "each call's sha256 is compared with the digest the committed "
                "receipt recorded. A no-op cannot reproduce these."
            ),
        },
        "payload_chars": {
            "n": len(payload_chars),
            "mean": round(statistics.fmean(payload_chars), 1) if payload_chars else 0,
            "min": min(payload_chars) if payload_chars else 0,
            "max": max(payload_chars) if payload_chars else 0,
        },
    }


# --------------------------------------------------------------------------
# P-L -- the one census line the parked lexicon-backwards question gets
# --------------------------------------------------------------------------


#: The sections of `data/realization/lexicon.json` that hold renderings
#: the lexicon EMITS. The file's other keys (`design`, `purpose`,
#: `lexicon_id`, `head_coverage`, `registered`, `reading_rules`) are prose
#: about the lexicon and are not part of P-L's denominator.
REALIZATION_SECTIONS = ("call_heads", "operators", "relations", "structural",
                        "slot_marker", "operator_tokens", "naming_conventions")


def realization_english(path: Path) -> set[str]:
    """Content words of every English rendering string in the lexicon."""

    document = json.loads(path.read_text(encoding="utf-8"))
    words: set[str] = set()

    def walk(value: object) -> None:
        if isinstance(value, str):
            words.update(_WORD.findall(value.lower()))
        elif isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    for section in REALIZATION_SECTIONS:
        walk(document.get(section))
    return words - STOPWORDS


# --------------------------------------------------------------------------
# the census
# --------------------------------------------------------------------------


def build(data_dir: Path, repo_root: Path, k: int, oracle_calls: int) -> tuple[dict, dict]:
    rows = corpus_rows(data_dir)
    corpus_of = {sid: corpus for corpus, sid, _ in rows}
    parsed, problems = parsed_by_id(data_dir)

    slex = {sid: slex_handles(node) for _c, sid, node in rows}
    slex_names = {sid: slex_name_handles(node) for _c, sid, node in rows}
    sinv = {sid: set(parsed[sid].call_heads) if sid in parsed else set()
            for _c, sid, _n in rows}
    skel_of = {sid: parsed[sid].family for _c, sid, _n in rows if sid in parsed}
    sskel = {sid: ({skel_of[sid]} if sid in skel_of else set())
             for _c, sid, _n in rows}

    slex_counts = resolves_to(slex)
    slex_name_counts = resolves_to(slex_names)
    sinv_counts = resolves_to(sinv)
    sskel_counts = resolves_to(sskel)

    slex_cov = coverage(slex, slex_counts, corpus_of, k)
    slex_name_cov = coverage(slex_names, slex_name_counts, corpus_of, k)
    sinv_cov = coverage(sinv, sinv_counts, corpus_of, k)
    sskel_cov = coverage(sskel, sskel_counts, corpus_of, k)

    total = len(rows)
    bulk = [sid for _c, sid, _n in rows if corpus_of[sid] == "lean_workbook"]
    curated = [sid for _c, sid, _n in rows if corpus_of[sid] != "lean_workbook"]

    typable = slex_cov["_specific_ids"] | sinv_cov["_specific_ids"]
    all_union = typable | sskel_cov["_specific_ids"]

    # The boilerplate finding, quantified exactly.
    bulk_tokens: set[str] = set()
    bulk_name_tokens: set[str] = set()
    bulk_raw_strings: collections.Counter = collections.Counter()
    for _corpus, sid, node in rows:
        if corpus_of[sid] != "lean_workbook":
            continue
        bulk_tokens |= slex[sid]
        bulk_name_tokens |= slex_names[sid]
        lexicon = node.get("symbol_lexicon") or {}
        for group in LEXICON_GROUPS:
            for entry in lexicon.get(group) or []:
                if not isinstance(entry, dict):
                    continue
                for key in LEXICON_KEYS:
                    value = entry.get(key)
                    if isinstance(value, str):
                        bulk_raw_strings[f"{group}.{key}={value}"] += 1

    english = realization_english(repo_root / "data" / "realization" / "lexicon.json")
    slex_all_tokens = set(slex_counts)
    slex_specific_tokens = {h for h, c in slex_counts.items() if c <= k}

    pct = 100.0 * len(typable) / total

    census = {
        "schema": SCHEMA,
        "design": "docs/DESIGN-handles.md",
        "roadmap": "docs/ROADMAP-v0.22.md",
        "roadmap_item": "v0.22 item 1 -- H-P0, the construction prerequisite",
        "measurement_only": (
            "No handle table is built here, no budget is frozen, no question "
            "set is sealed. DESIGN-handles.md §6 orders this census before all "
            "three, and B10 makes a handle from outside its coverage red."
        ),
        "headline": (
            f"The ingested library is effectively nameless. Of {total} "
            f"statements, S-LEX gives a specific handle to "
            f"{len(slex_cov['_specific_ids'])} "
            f"({100.0 * len(slex_cov['_specific_ids']) / total:.2f}%) and "
            f"S-INV to {len(sinv_cov['_specific_ids'])} "
            f"({100.0 * len(sinv_cov['_specific_ids']) / total:.2f}%); their "
            f"union -- everything a person could plausibly type -- is "
            f"{len(typable)} ({pct:.2f}%), leaving {total - len(typable)} "
            f"statements with no specific handle at all. S-LEX's "
            f"{len(slex_cov['_specific_ids'])} are exactly the "
            f"{len(curated)} curated statements minus "
            f"{len(curated) - sum(1 for s in curated if s in slex_cov['_specific_ids'])}: "
            f"the {len(bulk)} lean_workbook statements carry "
            f"{len(bulk_tokens)} distinct glossary tokens and "
            f"{len(bulk_raw_strings)} distinct glossary strings between all of "
            f"them, and not one of them has a specific S-LEX handle. The "
            f"naming layer must be built, not indexed."
        ),
        "headline_is_the_stop_clause": (
            "DESIGN-handles.md §9's stop clause fires on specific-handle "
            "coverage near the review's indicative ~2%. The review's two "
            "indicative numbers are reproduced here exactly -- "
            f"{len(slex_cov['_specific_ids'])} via S-LEX (review said ~263) "
            f"and {len(sinv_cov['_specific_ids'])} via S-INV (review said "
            f"~306) -- so the ~2% figure is confirmed per source, at "
            f"{100.0 * len(slex_cov['_specific_ids']) / total:.2f}% and "
            f"{100.0 * len(sinv_cov['_specific_ids']) / total:.2f}%. The "
            f"typable union is {pct:.2f}%, which is the wider reading and is "
            "published beside them rather than instead of them. The clause is "
            "the design's to adjudicate and the roadmap's to seal; this "
            "census's job is to make sure the adjudication has numbers."
        ),
        "specificity_K": k,
        "specificity_definition": (
            "a handle is specific iff resolves_to_count <= K "
            "(DESIGN-handles.md §7 B2). K is NOT re-frozen here; B2 says a "
            "re-freeze is argued from the distribution this census publishes, "
            "by dated amendment before the table run."
        ),
        "provenance": provenance_block(
            Path(__file__),
            [*sorted(data_dir.glob("*/nodes.json")),
             repo_root / "data" / "realization" / "lexicon.json",
             repo_root / "data" / "foreign_voice" / "eligibility_preview.json",
             repo_root / "data" / "foreign_voice" / "register.json",
             repo_root / "experiments" / "foreign_voice_rate.json"],
            repo_root,
        ),
        "corpus": {
            "statements": total,
            "curated": len(curated),
            "bulk_lean_workbook": len(bulk),
            "template_parse_problems": len(problems),
            "per_corpus": dict(sorted(
                collections.Counter(corpus_of.values()).items())),
        },
        "sources": {
            "S-LEX": {
                "producer": "scripts/resolver.py:264-277 (the per-node "
                            "symbol_lexicon glossary resolver.by_lexicon is "
                            "built from)",
                "definition": (
                    "handle = a content word of a glossary entry's name, "
                    "description or semantic_role, over the five groups "
                    f"{list(LEXICON_GROUPS)}, lowercased on "
                    "[a-z0-9_]+ with resolver.STOPWORDS removed -- the "
                    "resolver's own field set and its own reduction"
                ),
                "reads_title_or_keywords": False,
                "coverage": strip_private(slex_cov),
                "distribution": distribution(slex_counts, k),
            },
            "S-LEX-names-only": {
                "producer": "same glossary, `name` key alone",
                "definition": (
                    "the sensitivity reading: §3's table calls the source "
                    "\"symbol_lexicon names\" while the producer it cites "
                    "reads three keys. Published so neither reading is "
                    "quietly chosen."
                ),
                "reads_title_or_keywords": False,
                "coverage": strip_private(slex_name_cov),
                "distribution": distribution(slex_name_counts, k),
            },
            "S-INV": {
                "producer": "scripts/match_signatures.py:952 "
                            "(template_call_heads), reached at :1038 via "
                            "load_nodes",
                "definition": (
                    "handle = a call head occurring anywhere in the canonical "
                    "parse of structural_signature.anonymized_template. "
                    "Title-free by construction"
                ),
                "reads_title_or_keywords": False,
                "coverage": strip_private(sinv_cov),
                "distribution": distribution(sinv_counts, k),
                "full_head_index": dict(sorted(sinv_counts.items(),
                                               key=lambda kv: (-kv[1], kv[0]))),
            },
            "S-SKEL": {
                "producer": "scripts/measure_compression.py (field `family` "
                            "from the same load_nodes)",
                "definition": (
                    "handle = the node's family skeleton string. K never "
                    "binds here, which is B2's own argument: the largest "
                    "bucket holds "
                    f"{max(sskel_counts.values()) if sskel_counts else 0} "
                    "statements"
                ),
                "reads_title_or_keywords": False,
                "coverage": strip_private(sskel_cov),
                "distribution": distribution(sskel_counts, k),
                "non_claim": (
                    "a skeleton string is nothing a person types. S-SKEL's "
                    "coverage is total and carries no human-question match; "
                    "it is excluded from the typable union below and the "
                    "design claims nothing for it."
                ),
                "table": "experiments/skeleton_index.json",
            },
        },
        "union": {
            "typable_sources": ["S-LEX", "S-INV"],
            "specific_handle_union_typable": len(typable),
            "specific_handle_union_typable_pct": round(pct, 4),
            "specific_handle_union_all_sources": len(all_union),
            "why_two_unions": (
                "S-SKEL reaches every statement, so a union including it is "
                "12,777 by construction and answers no question a person "
                "could ask. The typable union is the number the stop clause "
                "is about."
            ),
            "typable_union_by_corpus": dict(sorted(
                collections.Counter(corpus_of[s] for s in typable).items())),
            "slex_only": len(slex_cov["_specific_ids"] - sinv_cov["_specific_ids"]),
            "sinv_only": len(sinv_cov["_specific_ids"] - slex_cov["_specific_ids"]),
            "both": len(slex_cov["_specific_ids"] & sinv_cov["_specific_ids"]),
            "neither": total - len(typable),
        },
        "per_corpus_split": {
            "curated": {
                "statements": len(curated),
                "specific_S-LEX": sum(
                    1 for s in curated if s in slex_cov["_specific_ids"]),
                "specific_S-INV": sum(
                    1 for s in curated if s in sinv_cov["_specific_ids"]),
                "specific_typable_union": sum(1 for s in curated if s in typable),
            },
            "lean_workbook_bulk": {
                "statements": len(bulk),
                "specific_S-LEX": sum(
                    1 for s in bulk if s in slex_cov["_specific_ids"]),
                "specific_S-INV": sum(
                    1 for s in bulk if s in sinv_cov["_specific_ids"]),
                "specific_typable_union": sum(1 for s in bulk if s in typable),
            },
        },
        "boilerplate_finding": {
            "claim_under_test": (
                "review N7: 93% of the 27,182 by_lexicon entries are "
                "bulk-ingest boilerplate. DESIGN-handles.md §3 says the "
                "12,514 lean_workbook nodes share three boilerplate name "
                "pairs (equality / template / standing)."
            ),
            "bulk_statements": len(bulk),
            "distinct_glossary_tokens_over_the_bulk": len(bulk_tokens),
            "the_tokens": sorted(bulk_tokens),
            "distinct_name_tokens_over_the_bulk": len(bulk_name_tokens),
            "the_name_tokens": sorted(bulk_name_tokens),
            "distinct_raw_glossary_strings_over_the_bulk": len(bulk_raw_strings),
            "the_raw_strings": [
                {"string": text, "statements": count}
                for text, count in sorted(bulk_raw_strings.items(),
                                          key=lambda kv: (-kv[1], kv[0]))
            ],
            "reading": (
                f"{len(bulk)} statements, {len(bulk_tokens)} distinct glossary "
                f"tokens, {len(bulk_raw_strings)} distinct raw glossary "
                "strings. Every one of those tokens resolves to more than K "
                f"statements, so the bulk's specific-S-LEX coverage is "
                f"{sum(1 for s in bulk if s in slex_cov['_specific_ids'])}."
            ),
        },
        "k_sensitivity": k_sensitivity(
            cheapest_handle(slex, slex_counts),
            cheapest_handle(sinv, sinv_counts), corpus_of, k),
        "s3_price": s3_price(repo_root, oracle_calls),
        "P-L": {
            "park": "the lexicon-backwards question (docs/BACKLOG.md; "
                    "ROADMAP-v0.22.md §4.3 'Open-English input')",
            "the_one_line": (
                "which S-LEX names also appear in the realization lexicon's "
                "English -- recorded for that park's future unpark case, and "
                "nothing else"
            ),
            "denominator": (
                "\"the realization lexicon's English\" is defined here so the "
                "three numbers below are recomputable from this artifact "
                "alone: every string reachable by walking the seven sections "
                f"{list(REALIZATION_SECTIONS)} of "
                "data/realization/lexicon.json (recursively, values only), "
                "lowercased on [a-z0-9_]+ with resolver.STOPWORDS removed -- "
                "the same reduction S-LEX uses, so the two sides are compared "
                "in one vocabulary rather than across two. Sections of that "
                "file outside the seven (design, purpose, lexicon_id, "
                "head_coverage, registered, reading_rules) are prose ABOUT the "
                "lexicon rather than renderings it emits, and are excluded."
            ),
            "realization_english_content_words": len(english),
            "slex_handles_total": len(slex_all_tokens),
            "slex_handles_in_realization_english": len(slex_all_tokens & english),
            "slex_specific_handles_total": len(slex_specific_tokens),
            "slex_specific_handles_in_realization_english":
                len(slex_specific_tokens & english),
            "overlap_sample": sorted(slex_specific_tokens & english)[:40],
            "non_claim": (
                "an overlap is not an inversion. This line records how much "
                "vocabulary the two sides share; it says nothing about "
                "whether the lexicon runs backwards."
            ),
        },
        "non_claims": [
            "no reachability rate is published -- the deliverable this census "
            "serves is a partition, and the partition does not exist yet",
            "no handle table is built, no budget frozen, no question sealed",
            "no claim that a statement with a specific handle is CORRECTLY "
            "reachable, only that a specific handle exists for it",
            "no stranger-usability claim: no population of askers is involved "
            "in this census at all",
            "the S3 runtime projection is a per-call cost times a term count. "
            "It prices elaboration, not the design of a term store",
        ],
    }

    skeleton_index = {
        "schema": SKELETON_SCHEMA,
        "design": "docs/DESIGN-handles.md",
        "why_this_file_exists": (
            "DESIGN-handles.md §3: S-SKEL's strings are NOT persisted "
            "anywhere in the tree. reports/compression.json carries "
            "family_reuse counts per statement and no skeleton string, so "
            "S-SKEL had no committed table to be censused against. This is "
            "that table, recomputed from committed code "
            "(match_signatures.load_nodes, field `family`) over committed "
            "corpora."
        ),
        "producer": "scripts/match_signatures.py load_nodes -> ParsedNode.family, "
                    "the field scripts/measure_compression.py groups on",
        "specificity_K": k,
        "provenance": provenance_block(
            Path(__file__), sorted(data_dir.glob("*/nodes.json")), repo_root),
        "totals": {
            "statements": len(skel_of),
            "distinct_family_skeletons": len(sskel_counts),
            "max_family_reuse": max(sskel_counts.values()) if sskel_counts else 0,
            "mean_statements_per_skeleton": round(
                len(skel_of) / len(sskel_counts), 4) if sskel_counts else 0,
            "skeletons_over_K": sum(1 for v in sskel_counts.values() if v > k),
        },
        "rows": [
            {"statement_id": sid,
             "corpus": corpus_of[sid],
             "family_skeleton": skel_of[sid],
             "family_reuse": sskel_counts[skel_of[sid]]}
            for _c, sid, _n in rows if sid in skel_of
        ],
    }
    return census, skeleton_index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path,
                        default=ROOT / "experiments" / "handles_census.json")
    parser.add_argument("--skeleton-index", type=Path,
                        default=ROOT / "experiments" / "skeleton_index.json")
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--oracle-calls", type=int, default=0,
                        help="real pinned-checker calls to time for the S3 "
                             "price. 0 leaves the runtime unmeasured and says "
                             "so; the design asks for 20")
    args = parser.parse_args(argv)

    census, skeleton_index = build(args.data_dir, args.repo_root, args.k,
                                   args.oracle_calls)
    for path, payload in ((args.out, census),
                          (args.skeleton_index, skeleton_index)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        print(f"wrote {path}")
    print(census["headline"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
