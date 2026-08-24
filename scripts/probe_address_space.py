#!/usr/bin/env python3
"""The address-space probe: is the unified dictionary a real object?

`docs/ROADMAP-v0.19.md` item 2 adopts `docs/DESIGN-block-vocabulary.md`
bounded, and scopes it to a single question its own census raised:

    is the unified dictionary a real object, or two existing objects
    wearing one id space?

This script answers it against three baselines that were **pre-registered
before any measurement**, in `experiments/address_space_probe_prereg.json`,
committed in its own commit with nothing else in it. That file is the
contract; this one only executes it. Its sha256 is carried in the result so
the prereg a verdict was adjudicated against is pinned rather than cited.

What runs
---------
1. **The one consumer** -- a resolver BLOCK CHANNEL prototype. The MDL
   dictionary's multi-word blocks (`scripts/measure_block_mdl.py`, rebuilt
   deterministically) become exact retrieval keys: block id -> posting list
   of statement ids. Scored on the SAME committed populations, by the SAME
   rules, as the keyword channel whose floors it must beat.
2. **The addressability measurement** -- bytes touched to answer "which
   statements contain block/subterm X", for the unified id space against
   grep, zstd-decompress-then-scan, and the two existing indexes used
   separately. This is what decides "one id space IS the contribution", so
   it carries its own registered win condition.
3. **The term layer** -- the same MDL induction over the anonymized
   templates, against the canon token encoding.
4. **The verdict** -- BEATEN or NOT BEATEN against each baseline, with the
   number. No third word. Beat none and the design parks with the numbers.

The comparison arm, declared
----------------------------
This is an instrument, not the task-book builder, so it MAY import engine
machinery -- but only what the prereg declares, and only for the arm the
prereg declares it for. The registered retrieval baseline IS the resolver's
own channel, so re-running it in this process on these rows is what makes
the comparison same-run instead of quoted-from-memory.

Imported for the comparison arm, from `scripts/resolver.py`:
`BIND`, `ASK`, `PASS`, `COVERAGE_FLOOR`, `KEYWORD_DF_CEILING`,
`TERM_QUERY_WORDS`, `GraphIndex`, `build_index`, `default_index`,
`reduce_text`, `resolve`.

Imported as the probe's dependency, from `scripts/measure_block_mdl.py`:
`Grammar`, `RULE_NS`, `Surface`, `code_width`, `load_surfaces`,
`to_template`.

Nothing else from this repository is imported, and
`tests/test_address_space_probe.py` parses this file's AST and fails on any
repo import outside those two lists. There is no learned component, no
network, and no wall-clock reading anywhere in the output.

One arm added during construction, before any adjudication
----------------------------------------------------------
The prereg registered one dictionary. Building the channel surfaced a fact
about casing that would have decided the retrieval verdict on an artifact
rather than on the design: block_mdl's induction runs over CASED surfaces
(`The derivative of a`), while the keyword channel lowercases every query
before matching. A cased dictionary therefore loses matches it should win.
So the channel is run over four dictionaries -- cased and case-folded, each
under Model A (fixed-width) and Model C (entropy) -- and adjudicated on
whichever is best, which is what the prereg already directs for its two
channel arms ("the verdict is adjudicated on whichever arm is BETTER, so the
design gets its best case"). This note is dated 2026-08-24 and stated here
rather than absorbed, because an arm added after a prereg has to be visible.

The case-folded fixed-width dictionary reproduces DESIGN section 3d
correction 1 independently and by accident: folding merges terminals until
`terminals + rules` lands on exactly 2048 = 2^11, the fixed-width code
refuses every further mint, and the rule count is chosen by the code width
rather than by the corpus. The arm is kept, with `at_power_of_two_cliff`
true beside it, because deleting an arm that reproduces a known defect would
delete the evidence for the defect.

Usage
-----
    python scripts/probe_address_space.py --write-report \\
        experiments/address_space_probe.json
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from measure_block_mdl import (  # noqa: E402
    Grammar,
    RULE_NS,
    Surface,
    code_width,
    load_surfaces,
    to_template,
)
from resolver import (  # noqa: E402  -- declared comparison arm
    ASK,
    BIND,
    COVERAGE_FLOOR,
    KEYWORD_DF_CEILING,
    PASS,
    TERM_QUERY_WORDS,
    GraphIndex,
    build_index,
    default_index,
    reduce_text,
    resolve,
)

PREREG = REPO / "experiments" / "address_space_probe_prereg.json"
DEFAULT_OUT = REPO / "experiments" / "address_space_probe.json"

#: The two corpora the committed retrieval floors were measured over.
#: `docs/DESIGN-holdout-quarantine.md` section 2 allows a measurement to merge
#: the holdout explicitly; this is that explicit merge, and its only reason is
#: that the baseline lives on the merged graph.
GRAPH_DIRS = (REPO / "data", REPO / "data_holdout")
#: The population `experiments/block_mdl.json` measured. Kept separate so no
#: figure comparable to that artifact is quietly computed over a wider set.
MDL_DIRS = (REPO / "data",)

#: Term-layer tokenizer. Deliberately local rather than imported: the prereg
#: declares six names from measure_block_mdl and this is not one of them.
#: Same shape as that module's `ascii_tokens` -- identifiers, numbers folded
#: to {N}, every other character its own atom.
TEMPLATE_TOKEN = re.compile(r"[A-Za-z_?][A-Za-z_0-9]*|[0-9]+(?:\.[0-9]+)?|\S")

#: Random access touches a page, not a byte. 4096 is the ordinary page.
PAGE_BYTES = 4096
#: One directory entry: 8-byte namespaced key id, 4-byte offset, 4-byte
#: length. Fixed width so a binary search is arithmetic, which is the whole
#: point of ids that are addresses.
DIRECTORY_ENTRY_BYTES = 16
#: One posting: a 4-byte statement ordinal.
POSTING_BYTES = 4


# --------------------------------------------------------------------------
# the dictionary, rebuilt
# --------------------------------------------------------------------------

def load_prose(dirs: tuple[Path, ...], fold: bool) -> list[Surface]:
    """Prose surfaces in deterministic order, optionally case-folded."""
    out: list[Surface] = []
    for data_dir in dirs:
        prose, _formal = load_surfaces(data_dir)
        out.extend(prose)
    if not fold:
        return out
    return [
        Surface(s.corpus, s.statement_id, s.kind, s.raw,
                [w.lower() for w in s.words])
        for s in out
    ]


def induce(surfaces: list[Surface], mult: float, mode: str) -> Grammar:
    g = Grammar()
    g.append_documents(surfaces)
    g.induce(mult, mode)
    return g


def rule_closure(g: Grammar) -> dict[int, frozenset[int]]:
    """symbol -> every rule id inside its expansion, itself included.

    A block occurs in a document when the grammar's own parse of that
    document contains it, at any composition depth. Taking the closure is
    what makes a composed id and its parts both usable as retrieval keys,
    which is the addressing the design asks for.
    """
    closed: dict[int, frozenset[int]] = {}
    for index in range(len(g.terminals)):
        closed[index] = frozenset()
    for index in range(len(g.rules)):
        rid = RULE_NS | index
        a, b = g.rules[index]
        closed[rid] = frozenset({rid}) | closed[a] | closed[b]
    return closed


def block_postings(
    g: Grammar, closed: dict[int, frozenset[int]]
) -> dict[int, tuple[str, ...]]:
    """block id -> the statement ids whose surfaces contain it, sorted."""
    acc: dict[int, set[str]] = {}
    for doc in range(len(g.doc_start)):
        _corpus, sid, _kind = g.doc_meta[doc]
        present: set[int] = set()
        for sym in g.document_pattern(doc):
            present |= closed[sym]
        for rid in present:
            acc.setdefault(rid, set()).add(sid)
    return {k: tuple(sorted(v)) for k, v in sorted(acc.items())}


def encode_query(g: Grammar, text: str, fold: bool) -> tuple[list[str], list[int]]:
    """Slot the query, then replay the dictionary's rules over it in mint
    order -- exactly `Grammar.replay_rules`' semantics on a growth increment,
    which is the encoder that re-uses existing ids instead of re-deriving
    them. Words the dictionary has never seen get a sentinel that no rule
    can match, so an unknown word blocks a block rather than joining one."""
    words = to_template(text).split()
    if fold:
        words = [w.lower() for w in words]
    seq = [g.term_index.get(w, -1) for w in words]
    for index in range(len(g.rules)):
        a, b = g.rules[index]
        new_id = RULE_NS | index
        out: list[int] = []
        i = 0
        while i < len(seq):
            if i + 1 < len(seq) and seq[i] == a and seq[i + 1] == b:
                out.append(new_id)
                i += 2
            else:
                out.append(seq[i])
                i += 1
        seq = out
    return words, seq


# --------------------------------------------------------------------------
# the block channel
# --------------------------------------------------------------------------

class BlockChannel:
    """Blocks as exact retrieval keys, scored by the keyword channel's rules.

    The design's claim (section 3 item 3) is that "multi-word exact blocks are
    radically higher-precision retrieval keys than the single keywords the
    resolver fights its 0.030 false-positive floor with today". This is that
    sentence built and pointed at the populations the 0.030 was measured on.
    """

    def __init__(self, g: Grammar, fold: bool, graph_size: int):
        self.g = g
        self.fold = fold
        self.closed = rule_closure(g)
        self.postings = block_postings(g, self.closed)
        self.graph_size = graph_size
        #: The same document-frequency reasoning the keyword channel uses. A
        #: block on most of the corpus discriminates nothing; `of a` sits on
        #: 14,570 of 14,830 nodes and matching it would "resolve" a query to
        #: the whole graph. Same constant, same corpus-derived rule.
        self.ceiling = max(1, int(graph_size * KEYWORD_DF_CEILING))
        self.words_of = {
            RULE_NS | i: g.expansion[RULE_NS | i] for i in range(len(g.rules))
        }
        self.single_word_blocks = sum(
            1 for i in range(len(g.rules)) if g.expansion[RULE_NS | i] < 2
        )

    # -- one query -------------------------------------------------------
    def keys(self, text: str) -> tuple[list[str], list[int], list[int]]:
        """(slotted words, live symbols, matched block ids below the ceiling)"""
        words, seq = encode_query(self.g, text, self.fold)
        found: set[int] = set()
        for sym in seq:
            found |= self.closed.get(sym, frozenset())
        usable = sorted(
            rid for rid in found
            if len(self.postings.get(rid, ())) <= self.ceiling
        )
        return words, seq, usable

    def resolve(self, text: str, arm: str, corpus_of: dict[str, str]) -> dict:
        """arm is "strict", "permissive", or "no_ceiling" (a diagnostic)."""
        words, seq, usable = self.keys(text)
        if arm == "no_ceiling":
            found: set[int] = set()
            for sym in seq:
                found |= self.closed.get(sym, frozenset())
            usable = sorted(found)
        row = {
            "words": len(words),
            "blocks_matched": len(usable),
            "kind": PASS,
            "candidates": 0,
            "top": None,
        }
        if not usable:
            row["detail"] = "no block below the ceiling matched"
            return row

        hits: dict[str, int] = {}
        for rid in usable:
            for sid in self.postings.get(rid, ()):
                hits[sid] = hits.get(sid, 0) + 1
        if not hits:
            row["detail"] = "matched blocks have empty posting lists"
            return row

        # Coverage, the block analogue of the keyword channel's rule: how
        # much of what was typed did the matched blocks account for. Counted
        # in query word POSITIONS, because a block is a span, not a token.
        covered_words = 0
        for sym in seq:
            if sym & RULE_NS and any(
                rid in usable for rid in self.closed.get(sym, frozenset())
            ):
                covered_words += self.words_of.get(sym, 1)
        covered = covered_words / max(len(words), 1)
        best = max(hits.values())
        row["coverage_of_query"] = round(covered, 4)
        row["best_score"] = best

        if arm == "strict":
            absorbed = covered_words == len(words) and len(words) <= TERM_QUERY_WORDS
            if not ((best >= 2 and covered >= COVERAGE_FLOOR) or absorbed):
                row["detail"] = (
                    f"{len(usable)} block(s) matched, accounting for "
                    f"{covered:.0%} of the query; a partial match is not a "
                    "resolution"
                )
                return row

        top = tuple(sorted(s for s, n in hits.items() if n == best))

        if arm == "strict" and len(usable) >= 2:
            # Convergence, the rule that bought the keyword channel its
            # 0.030 floor. Excluding it would measure the block channel
            # against a baseline the baseline does not have to clear.
            winner_corpora = {corpus_of.get(s, "?") for s in top}
            supporting = 0
            for rid in usable:
                if any(
                    corpus_of.get(sid, "?") in winner_corpora
                    for sid in self.postings.get(rid, ())
                ):
                    supporting += 1
            row["supporting_blocks"] = supporting
            if supporting < 2:
                row["detail"] = (
                    "only one matched block points at the winning corpus; a "
                    "single supporting key is a coincidence, not a subject"
                )
                return row

        row["kind"] = BIND if len(top) == 1 else ASK
        row["candidates"] = len(top)
        row["top"] = top[0]
        row["candidate_ids"] = list(top[:8])
        row["detail"] = f"{len(top)} statements match {len(usable)} block(s)"
        return row


# --------------------------------------------------------------------------
# populations
# --------------------------------------------------------------------------

def load_query_sets() -> dict[str, dict]:
    """The committed query sets, with the rows each arm is scored over."""
    out: dict[str, dict] = {}
    for key, name in (
        ("P-RET-DEV", "text_resolution_queries.json"),
        ("P-RET-H1", "text_resolution_holdout.json"),
        ("P-RET-H2", "text_resolution_holdout2.json"),
    ):
        spec = json.loads(
            (REPO / "experiments" / name).read_text(encoding="utf-8")
        )
        rows = spec["queries"]
        out[key] = {
            "source": f"experiments/{name}",
            "resolve": [r["text"] for r in rows if r.get("expect") == "resolve"],
            "refuse": [r["text"] for r in rows if r.get("expect") == "refuse"],
            "excluded_rows": sum(
                1 for r in rows if r.get("expect") in {"compute", "define"}
            ),
        }
    spec = json.loads(
        (REPO / "experiments" / "text_resolution_holdout3.json").read_text(
            encoding="utf-8"
        )
    )
    out["P-RET-H3"] = {
        "source": "experiments/text_resolution_holdout3.json",
        "resolve": [r["text"] for r in spec["queries"]],
        "refuse": [],
        "targets": {r["text"]: r["target"] for r in spec["queries"]},
        "excluded_rows": 0,
    }
    f3 = json.loads(
        (REPO / "experiments" / "false_positive_rate_f3.json").read_text(
            encoding="utf-8"
        )
    )
    out["P-FP-CLAIMED"] = {
        "source": "experiments/false_positive_rate_f3.json claimed_samples",
        "resolve": [],
        "refuse": [r["text"] for r in f3.get("claimed_samples", [])],
        "excluded_rows": 0,
        "one_sided": (
            "these 25 rows are the keyword channel's OWN false positives; a "
            "count over them is not a false-positive rate, and the 1,000 "
            "sentences that would make it one were never committed"
        ),
    }
    return out


def wordnet_archive_state() -> dict:
    """Whether F3's population can be reproduced here. It cannot, and the
    probe says so rather than substituting a different sample quietly."""
    import os
    env = os.environ.get("COROLLARY_WORDNET")
    pinned = REPO / "data_sources" / "derived"
    return {
        "COROLLARY_WORDNET_set": bool(env),
        "reproducible": False,
        "why": (
            "gloss.archive_path() returns None in this environment and the "
            "1,000 sampled sentences of F3 were never committed -- only 25 of "
            "the 30 claimed ones are. The 0.030 denominator cannot be "
            "regenerated, so no false-positive RATE is computed here."
        ),
        "checked": [str(pinned.relative_to(REPO))],
    }


# --------------------------------------------------------------------------
# arm A: retrieval
# --------------------------------------------------------------------------

def score_rows(
    rows: list[str], scorer, targets: dict[str, str] | None
) -> dict:
    reached = 0
    recalled = 0
    detail: list[dict] = []
    for text in rows:
        row = scorer(text)
        hit = row["kind"] in {BIND, ASK}
        reached += 1 if hit else 0
        if targets is not None:
            got = row.get("candidate_ids") or ([row["top"]] if row["top"] else [])
            if targets.get(text) in got:
                recalled += 1
        detail.append({"text": text, **row})
    out = {
        "rows": len(rows),
        "reached": reached,
        "rate": round(reached / len(rows), 4) if rows else None,
    }
    if targets is not None:
        out["target_recall"] = (
            round(recalled / len(rows), 4) if rows else None
        )
        out["recalled"] = recalled
    out["detail"] = detail
    return out


def retrieval_arm(
    channels: dict[str, BlockChannel],
    index: GraphIndex,
    sets: dict[str, dict],
) -> dict:
    corpus_of = index.corpus_of
    arms: dict[str, dict] = {}

    def keyword_scorer(text: str) -> dict:
        outcome = resolve(text, index)
        return {
            "kind": outcome.kind,
            "candidates": len(outcome.candidates),
            "top": outcome.candidates[0] if outcome.candidates else None,
            "candidate_ids": list(outcome.candidates[:8]),
            "resolver": outcome.resolver,
            "detail": outcome.detail[:120],
        }

    def run(scorer) -> dict:
        per: dict[str, dict] = {}
        pooled_resolve = [0, 0]
        pooled_refuse = [0, 0]
        for key, spec in sets.items():
            entry: dict = {"source": spec["source"]}
            if spec["resolve"]:
                entry["resolve"] = score_rows(
                    spec["resolve"], scorer, spec.get("targets")
                )
                pooled_resolve[0] += entry["resolve"]["reached"]
                pooled_resolve[1] += entry["resolve"]["rows"]
            if spec["refuse"]:
                entry["refuse"] = score_rows(spec["refuse"], scorer, None)
                if key != "P-FP-CLAIMED":
                    pooled_refuse[0] += entry["refuse"]["reached"]
                    pooled_refuse[1] += entry["refuse"]["rows"]
                else:
                    entry["refuse"]["not_a_rate"] = spec["one_sided"]
            per[key] = entry
        return {
            "per_population": per,
            "pooled_coverage": {
                "reached": pooled_resolve[0],
                "of": pooled_resolve[1],
                "rate": round(pooled_resolve[0] / pooled_resolve[1], 4)
                if pooled_resolve[1] else None,
                "populations": "P-RET-DEV + P-RET-H1 + P-RET-H2 + P-RET-H3",
            },
            "pooled_claim_on_refuse_rows": {
                "claimed": pooled_refuse[0],
                "of": pooled_refuse[1],
                "rate": round(pooled_refuse[0] / pooled_refuse[1], 4)
                if pooled_refuse[1] else None,
                "populations": "P-RET-DEV + P-RET-H1 + P-RET-H2",
                "note": (
                    "34 authored refuse rows. This is the only refusal "
                    "denominator this environment can reproduce; it is not "
                    "F3's 1,000-sentence population and is not quoted as the "
                    "0.030 figure's replacement."
                ),
            },
        }

    arms["keyword_channel_same_run"] = run(keyword_scorer)
    arms["keyword_channel_same_run"]["what_this_is"] = (
        "scripts/resolver.py resolve() -- the full committed chain, which is "
        "what experiments/text_resolution.json and "
        "experiments/false_positive_rate_f3.json both measured, so it is the "
        "baseline as it was actually floored"
    )

    for label, channel in channels.items():
        for mode in ("strict", "permissive", "no_ceiling"):
            arms[f"block_channel_{label}_{mode}"] = run(
                lambda t, c=channel, m=mode: c.resolve(t, m, corpus_of)
            )

    # Does the block channel ADD anything to the committed chain?
    best_label = max(
        channels,
        key=lambda k: arms[f"block_channel_{k}_permissive"][
            "pooled_coverage"]["reached"],
    )
    best = channels[best_label]

    def combined(text: str) -> dict:
        row = best.resolve(text, "strict", corpus_of)
        if row["kind"] != PASS:
            row["via"] = "block"
            return row
        out = keyword_scorer(text)
        out["via"] = "keyword"
        return out

    arms["block_first_then_keyword"] = run(combined)
    arms["block_first_then_keyword"]["dictionary"] = best_label
    arms["block_first_then_keyword"]["what_this_is"] = (
        "the block channel offered first, the committed chain behind it. If "
        "the unified dictionary is a retrieval contribution, this is where it "
        "shows: coverage above the chain's own, or refusals the chain misses."
    )
    return arms


# --------------------------------------------------------------------------
# arm B: addressability
# --------------------------------------------------------------------------

def _binary_search_cost(entries: int) -> dict:
    """Bytes and pages touched by a binary search over a sorted directory.

    Exact-bytes counts one directory entry per probe. The page model counts
    distinct 4 KiB pages: the last probes fall inside one page, so a search
    over N entries touches ceil(log2 N) - floor(log2 entries_per_page) pages,
    floored at one. Both are reported because they disagree about whether a
    second directory probe is a real cost, and that disagreement is exactly
    what the unification question turns on.
    """
    if entries <= 0:
        return {"probes": 0, "bytes": 0, "pages": 0}
    probes = max(1, math.ceil(math.log2(entries)))
    per_page = PAGE_BYTES // DIRECTORY_ENTRY_BYTES
    pages = max(1, probes - int(math.floor(math.log2(per_page))))
    return {
        "probes": probes,
        "bytes": probes * DIRECTORY_ENTRY_BYTES,
        "pages": pages,
    }


def _posting_cost(postings: int) -> dict:
    payload = postings * POSTING_BYTES
    return {
        "bytes": payload,
        "pages": max(1, math.ceil(payload / PAGE_BYTES)),
    }


def addressability_arm(
    channel: BlockChannel, index: GraphIndex, surfaces: list[Surface]
) -> dict:
    block_keys = {
        rid: len(post) for rid, post in channel.postings.items()
    }
    skeleton_keys = {
        key: len(sids) for key, sids in sorted(index.by_skeleton.items())
    }
    n_block = len(block_keys)
    n_skel = len(skeleton_keys)
    n_all = n_block + n_skel
    workload = sorted(block_keys.values()) + sorted(skeleton_keys.values())

    raw_bytes = 0
    for data_dir in GRAPH_DIRS:
        for path in sorted(data_dir.glob("*/nodes.json")):
            raw_bytes += len(path.read_bytes())
    surface_text = "\n".join(" ".join(s.words) for s in surfaces)
    surface_bytes = len(surface_text.encode("utf-8"))

    try:
        import zstandard as zstd  # type: ignore
        compressor = zstd.ZstdCompressor(level=19)
        zstd_bytes = len(compressor.compress(surface_text.encode("utf-8")))
        zstd_note = "zstd -19 over the same prose surfaces"
    except ImportError:  # pragma: no cover - binding-dependent
        import zlib
        zstd_bytes = len(zlib.compress(surface_text.encode("utf-8"), 9))
        zstd_note = "zstandard unavailable; zlib level 9 reported instead"

    unified_dir = _binary_search_cost(n_all)
    block_dir = _binary_search_cost(n_block)
    skel_dir = _binary_search_cost(n_skel)

    unified_bytes = 0
    unified_pages = 0
    separate_bytes = 0
    separate_pages = 0
    tagged_bytes = 0
    tagged_pages = 0
    grep_bytes = 0
    zstd_scan_bytes = 0
    for i, postings in enumerate(workload):
        own = block_dir if i < n_block else skel_dir
        cost = _posting_cost(postings)
        unified_bytes += unified_dir["bytes"] + cost["bytes"]
        unified_pages += unified_dir["pages"] + cost["pages"]
        # Two indexes, no namespace bits: the caller does not know which one
        # owns the key, so both directories are probed.
        separate_bytes += block_dir["bytes"] + skel_dir["bytes"] + cost["bytes"]
        separate_pages += block_dir["pages"] + skel_dir["pages"] + cost["pages"]
        # Two indexes, ONE TAG BIT saying which. Not a unified address space
        # -- a label. This is the arm that isolates what unification adds.
        tagged_bytes += own["bytes"] + cost["bytes"]
        tagged_pages += own["pages"] + cost["pages"]
        grep_bytes += raw_bytes
        zstd_scan_bytes += zstd_bytes + surface_bytes

    queries = len(workload)

    def per(total: int) -> int:
        return total // max(queries, 1)

    return {
        "the_query": "which statements contain block/subterm X",
        "workload": {
            "queries": queries,
            "block_keys": n_block,
            "subterm_skeleton_keys": n_skel,
            "note": (
                "every key in the unified space, asked once. Block keys come "
                "from the MDL induction; subterm skeleton keys are the ones "
                "the committed ownership/decompose machinery already builds "
                "(resolver.GraphIndex.by_skeleton, from decompose.subterms "
                "and match_signatures.skeleton)."
            ),
        },
        "sizes": {
            "raw_nodes_json_bytes": raw_bytes,
            "prose_surface_bytes": surface_bytes,
            "zstd19_archive_bytes": zstd_bytes,
            "zstd_note": zstd_note,
            "unified_directory_entries": n_all,
            "directory_entry_bytes": DIRECTORY_ENTRY_BYTES,
            "posting_bytes": POSTING_BYTES,
            "page_bytes": PAGE_BYTES,
        },
        "bytes_touched_total": {
            "i_unified_id_space": unified_bytes,
            "ii_grep_raw_prose": grep_bytes,
            "iii_zstd_decompress_then_scan": zstd_scan_bytes,
            "iv_two_separate_indexes_probed_both": separate_bytes,
            "iv_b_two_separate_indexes_with_one_tag_bit": tagged_bytes,
        },
        "bytes_touched_mean_per_query": {
            "i_unified_id_space": per(unified_bytes),
            "ii_grep_raw_prose": per(grep_bytes),
            "iii_zstd_decompress_then_scan": per(zstd_scan_bytes),
            "iv_two_separate_indexes_probed_both": per(separate_bytes),
            "iv_b_two_separate_indexes_with_one_tag_bit": per(tagged_bytes),
        },
        "pages_touched_total": {
            "i_unified_id_space": unified_pages,
            "ii_grep_raw_prose": queries * math.ceil(raw_bytes / PAGE_BYTES),
            "iii_zstd_decompress_then_scan": queries * (
                math.ceil(zstd_bytes / PAGE_BYTES)
                + math.ceil(surface_bytes / PAGE_BYTES)
            ),
            "iv_two_separate_indexes_probed_both": separate_pages,
            "iv_b_two_separate_indexes_with_one_tag_bit": tagged_pages,
        },
        "ratios": {
            "unified_vs_grep": round(grep_bytes / max(unified_bytes, 1), 2),
            "unified_vs_zstd_scan": round(
                zstd_scan_bytes / max(unified_bytes, 1), 2
            ),
            "unified_vs_two_separate_indexes": round(
                separate_bytes / max(unified_bytes, 1), 4
            ),
            "unified_vs_two_indexes_with_a_tag_bit": round(
                tagged_bytes / max(unified_bytes, 1), 4
            ),
        },
        "registered_win_condition": (
            "the unified id space is a REAL OBJECT iff its bytes-touched is "
            "strictly lower than arm (iv), the two existing indexes used "
            "separately. Beating (ii) and (iii) proves only that an index "
            "beats a scan, which both existing indexes already did "
            "separately, and the prereg registers that as NOT evidence for "
            "unification."
        ),
    }


# --------------------------------------------------------------------------
# arm C: the term layer
# --------------------------------------------------------------------------

def term_layer_arm() -> dict:
    """The MDL induction over anonymized templates, against 8.44x."""
    committed = json.loads(
        (REPO / "reports" / "compression.json").read_text(encoding="utf-8")
    )
    concept_of = {
        r["statement_id"]: r for r in committed["nodes"]
    }

    surfaces: list[Surface] = []
    char_tokens: dict[str, int] = {}
    for data_dir in MDL_DIRS:
        for path in sorted(data_dir.glob("*/nodes.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            corpus = path.parent.name
            for rec in doc.get("statement_nodes", []):
                sid = rec.get("statement_id")
                template = (rec.get("structural_signature") or {}).get(
                    "anonymized_template", ""
                )
                if not isinstance(sid, str) or not template:
                    continue
                if sid not in concept_of:
                    continue
                tokens = [
                    "{N}" if t[0].isdigit() else t
                    for t in TEMPLATE_TOKEN.findall(template)
                ]
                if not tokens:
                    continue
                char_tokens[sid] = len(template)
                surfaces.append(
                    Surface(corpus, sid, "anonymized_template", template, tokens)
                )

    arms: dict[str, dict] = {}
    for label, mult, mode in (
        ("model_a", 1.0, "fixed"),
        ("model_b_2x_dictionary", 2.0, "fixed"),
        ("model_c_entropy", 1.0, "entropy"),
    ):
        g = induce(surfaces, mult, mode)
        symbols = 0
        for doc in range(len(g.doc_start)):
            symbols += len(g.document_pattern(doc))
        stats = g.stats(mult, mode)
        mean_char = sum(char_tokens[s.statement_id] for s in surfaces) / len(surfaces)
        mean_block = symbols / len(surfaces)
        arms[label] = {
            "rules": stats["rules"],
            "terminals": stats["terminals"],
            "at_power_of_two_cliff": stats["at_power_of_two_cliff"],
            "mean_char_tokens": round(mean_char, 4),
            "mean_block_symbols": round(mean_block, 4),
            "ratio_vs_char": round(mean_char / max(mean_block, 1e-9), 4),
            "total_bits": stats["total_bits"],
        }

    mean_char = sum(char_tokens.values()) / len(char_tokens)
    mean_concept = sum(
        concept_of[s.statement_id]["concept_tokens"] for s in surfaces
    ) / len(surfaces)
    return {
        "population": "P-TERM",
        "surfaces": len(surfaces),
        "note": (
            "the anonymized_template of every node reports/compression.json "
            "scores, tokenized into identifier/number/symbol atoms, then run "
            "through the same MDL-gated Re-Pair induction the prose layer uses"
        ),
        "canon_token_baseline_same_population": {
            "mean_char_tokens": round(mean_char, 4),
            "mean_concept_tokens": round(mean_concept, 4),
            "ratio_vs_char": round(mean_char / max(mean_concept, 1e-9), 4),
            "source": "reports/compression.json, recomputed over the same rows",
        },
        "canon_token_baseline_as_the_roadmap_names_it": {
            "ratio_vs_char": 8.44,
            "source": (
                "experiments/ANALYSIS.md milestone-2 table, 67 nodes, 7 "
                "disciplines; that node list is not committed"
            ),
        },
        "block_arms": arms,
    }


# --------------------------------------------------------------------------
# arm D: compression, against the registered zstd numbers
# --------------------------------------------------------------------------

def compression_arm() -> dict:
    committed = json.loads(
        (REPO / "experiments" / "block_mdl.json").read_text(encoding="utf-8")
    )
    prose = committed["streams"]["prose"]
    base = prose["compression_baselines"]
    model_a = prose["mdl_arms"]["model_a"]
    model_b = prose["mdl_arms"]["model_b_2x_dictionary"]

    surfaces = load_prose(MDL_DIRS, fold=False)
    rebuilt = induce(surfaces, 1.0, "fixed")
    rebuilt_stats = rebuilt.stats(1.0, "fixed")

    return {
        "population": "P-MDL",
        "rebuild_check": {
            "why": (
                "the probe rebuilds the dictionary rather than reading it, so "
                "the first thing it owes is proof that the rebuild is the "
                "same object experiments/block_mdl.json measured"
            ),
            "committed_rules": model_a["rules"],
            "rebuilt_rules": rebuilt_stats["rules"],
            "committed_total_bits": model_a["total_bits"],
            "rebuilt_total_bits": rebuilt_stats["total_bits"],
            "identical": (
                rebuilt_stats["rules"] == model_a["rules"]
                and rebuilt_stats["total_bits"] == model_a["total_bits"]
            ),
        },
        "grammar_total_bits_model_a": model_a["total_bits"],
        "grammar_total_bits_model_b_2x_dictionary": model_b["total_bits"],
        "zstd19_archive_bits": base["zstd19_slotted_bits"],
        "zstd19_separately_addressable_no_dictionary_bits": base[
            "zstd19_per_document_bits"
        ],
        "zstd19_separately_addressable_with_shared_dictionary_bits": base[
            "zstd19_dict_plus_payload_bits"
        ],
        "flat_word_baseline_bits": prose["flat_word_baseline"]["flat_word_bits"],
        "archive_reading": {
            "comparison": (
                f"{model_a['total_bits']} against {base['zstd19_slotted_bits']}"
            ),
            "factor": round(
                model_a["total_bits"] / max(base["zstd19_slotted_bits"], 1), 2
            ),
        },
        "addressable_reading": {
            "comparison": (
                f"{model_a['total_bits']} against "
                f"{base['zstd19_dict_plus_payload_bits']}"
            ),
            "factor": round(
                base["zstd19_dict_plus_payload_bits"]
                / max(model_a["total_bits"], 1), 2
            ),
        },
    }


# --------------------------------------------------------------------------
# the report
# --------------------------------------------------------------------------

def sha256_of(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()


def build_report() -> dict:
    prereg = json.loads(PREREG.read_text(encoding="utf-8"))
    index = default_index()

    dictionaries: dict[str, dict] = {}
    channels: dict[str, BlockChannel] = {}
    for label, fold, mult, mode in (
        ("cased_model_a", False, 1.0, "fixed"),
        ("cased_model_c", False, 1.0, "entropy"),
        ("folded_model_a", True, 1.0, "fixed"),
        ("folded_model_c", True, 1.0, "entropy"),
    ):
        surfaces = load_prose(GRAPH_DIRS, fold)
        g = induce(surfaces, mult, mode)
        stats = g.stats(mult, mode)
        channel = BlockChannel(g, fold, index.size)
        channels[label] = channel
        posting_sizes = sorted(len(p) for p in channel.postings.values())
        dictionaries[label] = {
            "case_folded": fold,
            "bit_model": mode,
            "dictionary_multiplier": mult,
            "surfaces": len(surfaces),
            "terminals": stats["terminals"],
            "rules": stats["rules"],
            "blocks_that_are_one_word": channel.single_word_blocks,
            "at_power_of_two_cliff": stats["at_power_of_two_cliff"],
            "code_width_bits": stats["code_width_bits"],
            "words_per_stream_symbol": round(
                sum(len(s.words) for s in surfaces) / max(g.word_symbols, 1), 3
            ),
            "max_composition_depth": max(
                [g.depth[RULE_NS | i] for i in range(len(g.rules))] or [0]
            ),
            "keys_above_the_df_ceiling": sum(
                1 for n in posting_sizes if n > channel.ceiling
            ),
            "df_ceiling": channel.ceiling,
            "posting_list_sizes": {
                "min": posting_sizes[0] if posting_sizes else 0,
                "median": posting_sizes[len(posting_sizes) // 2]
                if posting_sizes else 0,
                "max": posting_sizes[-1] if posting_sizes else 0,
            },
            "sample_blocks": [
                " ".join(g.expand(RULE_NS | i))
                for i in range(min(8, len(g.rules)))
            ],
        }

    sets = load_query_sets()
    retrieval = retrieval_arm(channels, index, sets)
    compression = compression_arm()
    term = term_layer_arm()
    address = addressability_arm(
        channels["cased_model_a"], index, load_prose(GRAPH_DIRS, False)
    )

    report: dict = {
        "schema": "address_space_probe.v1",
        "design": "docs/DESIGN-block-vocabulary.md",
        "roadmap": "docs/ROADMAP-v0.19.md",
        "roadmap_item": "2 - the address-space probe",
        "prereg": {
            "path": "experiments/address_space_probe_prereg.json",
            "sha256_lf": sha256_of(PREREG),
            "single_question": prereg["single_question"]["question"],
            "verdict_rule": prereg["the_verdict_rule"]["verbatim_from_roadmap"],
        },
        "graph": {
            "nodes": index.size,
            "population": "P-GRAPH (data/ + data_holdout/, explicit merge)",
            "denominator_input_from_item_1": prereg["populations"][
                "denominator_input_from_item_1"
            ],
        },
        "wordnet_archive": wordnet_archive_state(),
        "dictionaries": dictionaries,
        "arm_A_retrieval": retrieval,
        "arm_B_compression": compression,
        "arm_C_term_layer": term,
        "arm_D_addressability": address,
    }
    report["verdict"] = verdict(report, prereg)
    report["registered_expectations"] = adjudicate_expectations(report, prereg)
    return report


def verdict(report: dict, prereg: dict) -> dict:
    baselines = prereg["the_three_pre_registered_baselines"]

    # --- A, retrieval ----------------------------------------------------
    arms = report["arm_A_retrieval"]
    best_label, best_cov = None, -1.0
    for key, arm in arms.items():
        if not key.startswith("block_channel_"):
            continue
        if key.endswith("_no_ceiling"):
            continue  # a declared diagnostic, not an adjudicated arm
        rate = arm["pooled_coverage"]["rate"] or 0.0
        if rate > best_cov:
            best_label, best_cov = key, rate
    best = arms[best_label]
    strict_label, strict_cov = None, -1.0
    for key, arm in arms.items():
        if not key.startswith("block_channel_") or not key.endswith("_strict"):
            continue
        rate = arm["pooled_coverage"]["rate"] or 0.0
        if rate > strict_cov:
            strict_label, strict_cov = key, rate
    claim_rate = best["pooled_claim_on_refuse_rows"]["rate"]
    keyword = arms["keyword_channel_same_run"]
    coverage_leg = best_cov >= 0.833
    fp_leg = (claim_rate is not None) and claim_rate <= 0.030
    a_beaten = coverage_leg and fp_leg

    # --- B, compression --------------------------------------------------
    comp = report["arm_B_compression"]
    archive_beaten = comp["grammar_total_bits_model_a"] < comp["zstd19_archive_bits"]
    addressable_beaten = (
        comp["grammar_total_bits_model_a"]
        < comp["zstd19_separately_addressable_with_shared_dictionary_bits"]
    )

    # --- C, term layer ---------------------------------------------------
    term = report["arm_C_term_layer"]
    best_term_label = max(
        term["block_arms"], key=lambda k: term["block_arms"][k]["ratio_vs_char"]
    )
    best_term = term["block_arms"][best_term_label]["ratio_vs_char"]
    c_beaten_roadmap = best_term > 8.44
    same_pop = term["canon_token_baseline_same_population"]["ratio_vs_char"]
    c_beaten_same_population = best_term > same_pop

    # --- the addressability question ------------------------------------
    addr = report["arm_D_addressability"]
    unified = addr["bytes_touched_total"]["i_unified_id_space"]
    separate = addr["bytes_touched_total"]["iv_two_separate_indexes_probed_both"]
    tagged = addr["bytes_touched_total"][
        "iv_b_two_separate_indexes_with_one_tag_bit"
    ]
    unified_beats_separate = unified < separate
    unified_beats_tagged = unified < tagged

    beaten_count = sum(
        [a_beaten, archive_beaten or addressable_beaten, c_beaten_roadmap]
    )

    return {
        "rule": prereg["the_verdict_rule"]["verbatim_from_roadmap"],
        "A_retrieval": {
            "baseline": baselines["A_retrieval"]["baseline"],
            "floors": baselines["A_retrieval"]["floors"],
            "best_block_arm": best_label,
            "coverage": best_cov,
            "coverage_leg": "MET" if coverage_leg else "MISSED",
            "claim_rate_on_authored_refuse_rows": claim_rate,
            "fp_leg": "MET" if fp_leg else "MISSED",
            "verdict": "BEATEN" if a_beaten else "NOT BEATEN",
            "the_number": (
                f"pooled coverage {best_cov} against the 0.833 floor; "
                f"{best['pooled_coverage']['reached']} of "
                f"{best['pooled_coverage']['of']} rows reached"
            ),
            "keyword_channel_on_the_same_rows": {
                "coverage": keyword["pooled_coverage"]["rate"],
                "reached": keyword["pooled_coverage"]["reached"],
                "of": keyword["pooled_coverage"]["of"],
                "claim_rate_on_refuse_rows":
                    keyword["pooled_claim_on_refuse_rows"]["rate"],
            },
            "best_strict_arm": {
                "arm": strict_label,
                "coverage": strict_cov,
                "note": (
                    "the arm scored by the keyword channel's own "
                    "corroboration, coverage and convergence rules. The "
                    "permissive arm above drops all three and is the design's "
                    "best case; both are published because the prereg forbids "
                    "dropping either."
                ),
            },
            "both_legs_rule": baselines["A_retrieval"][
                "the_leg_that_cannot_be_dropped"
            ],
        },
        "B_compression": {
            "baseline": baselines["B_compression"]["baseline"],
            "archive_reading": {
                "comparison": comp["archive_reading"]["comparison"],
                "verdict": "BEATEN" if archive_beaten else "NOT BEATEN",
                "the_number": (
                    f"the grammar costs {comp['archive_reading']['factor']}x "
                    "the zstd archive; conceded in advance by DESIGN 3d "
                    "correction 4"
                ),
            },
            "addressable_reading": {
                "comparison": comp["addressable_reading"]["comparison"],
                "verdict": "BEATEN" if addressable_beaten else "NOT BEATEN",
                "the_number": (
                    "separately addressable zstd with a trained shared "
                    f"dictionary costs {comp['addressable_reading']['factor']}x "
                    "the grammar"
                ),
            },
            "verdict": "BEATEN" if (archive_beaten or addressable_beaten)
                       else "NOT BEATEN",
            "the_number": (
                f"{comp['grammar_total_bits_model_a']} grammar bits against "
                f"{comp['zstd19_archive_bits']} as an archive (NOT BEATEN, "
                f"{comp['archive_reading']['factor']}x worse) and against "
                f"{comp['zstd19_separately_addressable_with_shared_dictionary_bits']}"
                f" as separately addressable units (BEATEN, "
                f"{comp['addressable_reading']['factor']}x better)"
            ),
            "what_this_verdict_is_worth": (
                "an arithmetic restatement of experiments/block_mdl.json, not "
                "a new finding. The prereg registered it as such (E2) so it "
                "could not be read as one afterwards."
            ),
        },
        "C_term_layer": {
            "baseline": baselines["C_term_layer"]["baseline"],
            "floor": 8.44,
            "best_block_arm": best_term_label,
            "ratio_vs_char": best_term,
            "verdict": "BEATEN" if c_beaten_roadmap else "NOT BEATEN",
            "the_number": f"{best_term}x against the roadmap's 8.44x",
            "same_population_reading": {
                "canon_token_ratio_on_P-TERM": same_pop,
                "verdict": "BEATEN" if c_beaten_same_population
                           else "NOT BEATEN",
                "the_number": f"{best_term}x against {same_pop}x",
            },
            "the_two_readings_disagree": c_beaten_roadmap != c_beaten_same_population,
            "if_they_disagree": (
                "the roadmap's 8.44x and the same-population 32.10x are the "
                "same encoding on two different node sets; a probe that quoted "
                "only the one it beat would be choosing its denominator"
            ),
        },
        "baselines_beaten": beaten_count,
        "baselines_beaten_detail": {
            "A_retrieval": "BEATEN" if a_beaten else "NOT BEATEN",
            "B_compression": "BEATEN"
                             if (archive_beaten or addressable_beaten)
                             else "NOT BEATEN",
            "C_term_layer": "BEATEN" if c_beaten_roadmap else "NOT BEATEN",
        },
        "disposition": (
            "PARK WITH THE NUMBERS" if beaten_count == 0
            else "at least one registered baseline beaten; see each verdict"
        ),
        "disposition_read_honestly": (
            "The only baseline this probe beats is B's addressable reading, "
            "and B was registered in advance (E2) as an arithmetic "
            "restatement of experiments/block_mdl.json rather than a new "
            "finding: the probe recomputed a comparison the MDL run had "
            "already published. The two baselines that required this probe to "
            "produce anything new -- retrieval and the term layer -- are both "
            "NOT BEATEN, and the retrieval arm is not close: the block "
            "channel is worse than the keyword channel it must beat on BOTH "
            "legs at once, "
            f"coverage {best_cov} against {keyword['pooled_coverage']['rate']} "
            f"and claim rate {claim_rate} against "
            f"{keyword['pooled_claim_on_refuse_rows']['rate']} on the same "
            "rows in the same run. Read as the roadmap's rule intends -- "
            "did the probe's own consumer beat its blind baseline -- the "
            "answer is no, and the recommended disposition is PARK WITH THE "
            "NUMBERS."
        ),
        "the_single_question": {
            "question": prereg["single_question"]["question"],
            "unified_beats_two_separate_indexes":
                "YES" if unified_beats_separate else "NO",
            "unified_beats_two_indexes_with_one_tag_bit":
                "YES" if unified_beats_tagged else "NO",
            "ratio_vs_two_separate_indexes":
                addr["ratios"]["unified_vs_two_separate_indexes"],
            "ratio_vs_two_indexes_with_a_tag_bit":
                addr["ratios"]["unified_vs_two_indexes_with_a_tag_bit"],
            "ratio_vs_grep": addr["ratios"]["unified_vs_grep"],
            "ratio_vs_zstd_scan": addr["ratios"]["unified_vs_zstd_scan"],
            "answer": (
                "TWO EXISTING OBJECTS WEARING ONE ID SPACE"
                if not unified_beats_tagged else
                "ONE OBJECT: the unified space is cheaper than the same two "
                "indexes with a namespace tag"
            ),
            "why": (
                "The unified space beats grep and zstd-scan by orders of "
                "magnitude, and the prereg registered in advance that this is "
                "NOT evidence for unification: it is evidence that an index "
                "beats a scan, and both existing indexes already had it "
                "separately. What unification adds over the same two indexes "
                "carrying one tag bit is the number that answers the question."
            ),
        },
    }


def adjudicate_expectations(report: dict, prereg: dict) -> dict:
    exp = prereg["registered_expectations"]
    verd = report["verdict"]
    addr = report["arm_D_addressability"]
    cov = verd["A_retrieval"]["coverage"]
    strict = report["arm_A_retrieval"]
    best_strict = max(
        (v["pooled_coverage"]["rate"] or 0.0)
        for k, v in strict.items()
        if k.startswith("block_channel_") and k.endswith("_strict")
    )
    return {
        "E1": {
            "registered": exp["E1"],
            "predicted": "pooled coverage under BC-strict below 0.20",
            "measured": best_strict,
            "fired": best_strict < 0.20,
        },
        "E2": {
            "registered": exp["E2"],
            "measured": {
                "archive": verd["B_compression"]["archive_reading"]["verdict"],
                "addressable":
                    verd["B_compression"]["addressable_reading"]["verdict"],
            },
            "fired": (
                verd["B_compression"]["archive_reading"]["verdict"]
                == "NOT BEATEN"
                and verd["B_compression"]["addressable_reading"]["verdict"]
                == "BEATEN"
            ),
        },
        "E3": {
            "registered": exp["E3"],
            "measured": verd["C_term_layer"]["ratio_vs_char"],
            "fired": verd["C_term_layer"]["verdict"] == "NOT BEATEN",
        },
        "E4": {
            "registered": exp["E4"],
            "measured": {
                "vs_grep": addr["ratios"]["unified_vs_grep"],
                "vs_zstd_scan": addr["ratios"]["unified_vs_zstd_scan"],
                "vs_two_indexes_with_a_tag_bit":
                    addr["ratios"]["unified_vs_two_indexes_with_a_tag_bit"],
            },
            "fired": (
                addr["ratios"]["unified_vs_grep"] > 100
                and addr["ratios"]["unified_vs_two_indexes_with_a_tag_bit"] <= 1.0
            ),
        },
        "coverage_note": (
            f"the best BC-strict arm reached {best_strict} pooled coverage "
            f"and the best arm of any kind reached {cov}"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="the address-space probe")
    ap.add_argument("--write-report", type=Path, default=None)
    args = ap.parse_args(argv)

    report = build_report()
    text = json.dumps(report, indent=2, sort_keys=False, ensure_ascii=False) + "\n"
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(text, encoding="utf-8", newline="\n")

    out = io.StringIO()
    verd = report["verdict"]
    print(f"question : {verd['the_single_question']['question']}", file=out)
    print(f"answer   : {verd['the_single_question']['answer']}", file=out)
    for key in ("A_retrieval", "B_compression", "C_term_layer"):
        entry = verd[key]
        print(f"{key:14s} {entry['verdict']:11s} "
              f"{entry.get('the_number', '')}", file=out)
    print(f"baselines beaten: {verd['baselines_beaten']} of 3 -> "
          f"{verd['disposition']}", file=out)
    for name, row in report["registered_expectations"].items():
        if isinstance(row, dict):
            print(f"  {name}: {'FIRED' if row['fired'] else 'MISSED'} "
                  f"{json.dumps(row['measured'])}", file=out)
    sys.stdout.write(out.getvalue())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
