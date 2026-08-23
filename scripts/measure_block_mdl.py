#!/usr/bin/env python3
"""MDL-gated grammar induction over the corpus surfaces: the census's successor.

`docs/DESIGN-block-vocabulary.md` §3c closes with a demand this script
answers: "the census script's successor must *induce* the dictionary under
MDL and report what the data chose." §2's five templates are a snapshot of
one generator's output; the number of blocks, the number of templates and
the composition depth are here *chosen by the data* under a stated bit
model, not by a threshold anybody picked.

What runs
---------
Re-Pair (Larsson-Moffat) at word granularity over the slotted prose
surfaces, with one change: the classic algorithm mints the most frequent
adjacent pair unconditionally until no pair repeats. Here every mint must
first pass an **MDL gate** -- `total_bits` must strictly fall -- which is
§3 item 5's promotion rule and §3c's criterion made executable. Minting
over already-minted ids is composition, and each id's composition depth is
tracked, so the "composition bits" question gets a measured histogram
instead of a guess.

The bit model (Model A, primary)
--------------------------------
One simple, defensible, fully stated model. No entropy coder, no arithmetic
coding, no adaptive context: those would compress better and make the
comparison unreproducible by hand.

    total_bits = terminal_lexicon_bits + encoded_bits + dictionary_bits

    T  = number of terminal symbols (distinct slotted words, plus one
         end-of-document terminal)
    R  = number of minted rule ids
    V  = T + R                       (logical symbol count)
    w  = ceil(log2(V))               (fixed-width code, one width for all)
    N  = symbols remaining in the encoded stream

    terminal_lexicon_bits = sum over terminals of (len(utf8) + 1) * 8
                            -- the spelling table; identical in every arm,
                               carried so no arm gets its alphabet free
    encoded_bits          = N * w
    dictionary_bits       = ceil(R * mult * 2 * w)
                            -- each rule is stored as its two constituent
                               ids at the same width; `mult` = 1.0

A candidate pair with `c` non-overlapping occurrences is admitted iff

    total_bits(T, R+1, N-c) < total_bits(T, R, N)

strictly. Because savings grow monotonically with `c` and the cost term is
independent of `c`, the highest-count pair is the best candidate, and once
a pair fails the gate it can never pass it later (its count only falls, the
cost only rises). That makes "stop when no candidate improves MDL" exact
rather than heuristic.

Model B (sensitivity) is the same model with `mult = 2.0`: every dictionary
entry costs twice as much, so any conclusion that survives both is not an
artifact of how generously the dictionary was priced. Both are reported.

Model C (sensitivity, added after the first run) exists because Models A and
B share a defect the first run exposed: a fixed-width code has a
**power-of-two cliff**. When `V` sits at `2^k`, one more id widens every
symbol in the stream, so the gate demands savings of `N` bits and refuses
everything -- the dictionary size that gets reported is then chosen by the
code width, not by the data. The `canonical_ascii` stream stopped dead at
`V = 512` for exactly that reason. Model C prices the stream with an
order-0 entropy estimate instead,

    encoded_bits = ceil(N * log2(N) - sum over symbols of f * log2(f))

which has no cliff, keeps the dictionary term at `R * 2 * ceil(log2(V))`,
and is maintained exactly (not sampled) as the induction runs. Where A and C
agree the number is the data's; where they disagree the fixed-width model is
the thing that spoke, and the report says so.

Structured ids (§3, §3b)
------------------------
Symbols are namespaced the way the design asks: terminals are
`TERMINAL_NS | index`, rules are `RULE_NS | index`, with `RULE_NS = 1 << 24`.
The bit model prices the *logical* symbol count `V`, not the id space; the
cost of the design's fixed-width 2^24 ids is reported separately as its own
arm so §4's "fixed-width vs variable-length" question has both numbers.
Append-only growth (§3b) is then structural: an increment mints new indices
inside each namespace and can never renumber an existing one. The probe in
`append_only_probe` asserts it anyway.

Determinism
-----------
No randomness, no timestamps, no wall-clock, no dict/set iteration order in
any output. Corpora in sorted path order, nodes in file order, ties broken
on the symbol pair. Two runs are byte-identical; `tests/test_block_mdl.py`
checks that and checks the committed report regenerates.

Usage
-----
    python scripts/measure_block_mdl.py --write-report experiments/block_mdl.json
"""

from __future__ import annotations

import argparse
import heapq
import json
import math
import re
import sys
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

#: Namespace bits, as directed by DESIGN-block-vocabulary.md §3 item 1.
TERMINAL_NS = 0
RULE_NS = 1 << 24

#: The end-of-document terminal. It is a real symbol -- it occupies a slot
#: in the stream and is priced at the same width as everything else, so
#: document boundaries are paid for rather than assumed free -- but it is
#: never eligible to be part of a minted pair, which is what keeps blocks
#: from straddling two statements.
EOD_WORD = "␞"  # RECORD SEPARATOR glyph; not present in any surface


# --------------------------------------------------------------------------
# Stream A: prose surfaces, slotted
# --------------------------------------------------------------------------

#: Carried over verbatim from `scripts/block_census.py` so the induction runs
#: on exactly the alphabet the census measured: numerals become {N}, and runs
#: of formula-ish tokens collapse to a single {F}. Slotting is lossy, so every
#: compression baseline below is computed on the *slotted* text as well as the
#: raw text; the slotted figure is the apples-to-apples one.
NUMISH = re.compile(r"[0-9]+(\.[0-9]+)?")


def to_template(text: str) -> str:
    """Pre-slot a surface: backtick spans -> {S}, numerals -> {N}, runs of
    formula-ish tokens -> a single {F}. Identical to the census's function."""
    t = re.sub(r"`[^`]*`", "{S}", text)
    t = NUMISH.sub("{N}", t)
    words = t.split()
    out = []
    run = False
    for w in words:
        if any(ch in w for ch in "=^\\+*/<>|") or w in ("{N}", "{S}"):
            if not run:
                out.append("{F}")
                run = True
        else:
            out.append(w)
            run = False
    return " ".join(out)


#: Stream B tokenizer: operator/identifier atoms of `canonical_ascii`.
ASCII_TOKEN = re.compile(r"[A-Za-z_][A-Za-z_0-9]*|[0-9]+(?:\.[0-9]+)?|\S")


def ascii_tokens(text: str) -> list[str]:
    return ["{N}" if t[0].isdigit() else t for t in ASCII_TOKEN.findall(text)]


class Surface:
    """One document in an induction stream."""

    __slots__ = ("corpus", "statement_id", "kind", "raw", "words")

    def __init__(self, corpus: str, statement_id: str, kind: str, raw: str,
                 words: list[str]):
        self.corpus = corpus
        self.statement_id = statement_id
        self.kind = kind
        self.raw = raw
        self.words = words


def load_surfaces(data_dir: Path) -> tuple[list[Surface], list[Surface]]:
    """Return (prose surfaces, canonical_ascii surfaces) in deterministic order."""
    prose: list[Surface] = []
    formal: list[Surface] = []
    for nodes_path in sorted(data_dir.glob("*/nodes.json")):
        doc = json.loads(nodes_path.read_text(encoding="utf-8"))
        records = doc["statement_nodes"] if isinstance(doc, dict) else doc
        corpus = nodes_path.parent.name
        for rec in records:
            sid = rec.get("statement_id", "")
            meaning = (rec.get("semantic_interpretation") or {}).get(
                "statement_meaning", ""
            )
            title = rec.get("title", "")
            if meaning:
                w = to_template(meaning).split()
                if w:
                    prose.append(Surface(corpus, sid, "meaning", meaning, w))
            if title:
                w = to_template(title).split()
                if w:
                    prose.append(Surface(corpus, sid, "title", title, w))
            ascii_form = (rec.get("formal_statement") or {}).get(
                "canonical_ascii", ""
            )
            if ascii_form:
                w = ascii_tokens(ascii_form)
                if w:
                    formal.append(
                        Surface(corpus, sid, "canonical_ascii", ascii_form, w)
                    )
    return prose, formal


# --------------------------------------------------------------------------
# The bit model
# --------------------------------------------------------------------------

def code_width(v: int) -> int:
    """ceil(log2(v)), at least 1 bit."""
    return max(1, (max(v, 1) - 1).bit_length())


def total_bits(lexicon_bits: int, terminals: int, rules: int, stream: int,
               mult: float) -> int:
    w = code_width(terminals + rules)
    return lexicon_bits + stream * w + math.ceil(rules * mult * 2 * w)


def _flog(x: int) -> float:
    return x * math.log2(x) if x > 0 else 0.0


def entropy_bits(stream: int, flog_sum: float) -> int:
    """Order-0 entropy estimate of a stream, given sum(f*log2 f) over symbols."""
    if stream <= 0:
        return 0
    return math.ceil(stream * math.log2(stream) - flog_sum)


# --------------------------------------------------------------------------
# The Re-Pair engine, MDL-gated
# --------------------------------------------------------------------------

class Grammar:
    """An append-only Re-Pair grammar over a doubly-linked symbol stream.

    `terminals` and `rules` are index-ordered and only ever grow at the end;
    that is the whole of §3b's id-stability requirement, enforced by the data
    structure rather than by discipline.
    """

    def __init__(self) -> None:
        self.terminals: list[str] = []
        self.term_index: dict[str, int] = {}
        self.rules: list[tuple[int, int]] = []
        self.depth: dict[int, int] = {}
        self.expansion: dict[int, int] = {}  # rule id -> words it expands to

        self.sym: list[int | None] = []
        self.nxt: list[int] = []
        self.prv: list[int] = []
        self.doc_start: list[int] = []
        self.doc_meta: list[tuple[str, str, str]] = []
        self.pairpos: dict[tuple[int, int], set[int]] = {}
        self.freq: dict[int, int] = {}   # symbol -> occurrences in live stream
        self.length = 0          # live symbols, EOD included
        self.word_symbols = 0    # live symbols, EOD excluded
        self.heap: list[tuple[int, int, int]] = []
        self.eod = self._terminal(EOD_WORD)

    # -- terminals ---------------------------------------------------------
    def _terminal(self, word: str) -> int:
        got = self.term_index.get(word)
        if got is None:
            got = TERMINAL_NS | len(self.terminals)
            self.term_index[word] = got
            self.terminals.append(word)
            self.depth[got] = 0
            self.expansion[got] = 1
        return got

    def lexicon_bits(self) -> int:
        return sum((len(w.encode("utf-8")) + 1) * 8 for w in self.terminals)

    # -- pair bookkeeping --------------------------------------------------
    def _pair_at(self, i: int) -> tuple[int, int] | None:
        j = self.nxt[i]
        if j < 0:
            return None
        a, b = self.sym[i], self.sym[j]
        if a is None or b is None or a == self.eod or b == self.eod:
            return None
        return (a, b)

    def _register(self, i: int) -> None:
        p = self._pair_at(i)
        if p is None:
            return
        s = self.pairpos.get(p)
        if s is None:
            s = self.pairpos[p] = set()
        s.add(i)
        if len(s) >= 2:
            heapq.heappush(self.heap, (-len(s), p[0], p[1]))

    def _unregister(self, i: int) -> None:
        p = self._pair_at(i)
        if p is None:
            return
        s = self.pairpos.get(p)
        if not s:
            return
        s.discard(i)
        if not s:
            del self.pairpos[p]
        elif len(s) >= 2:
            heapq.heappush(self.heap, (-len(s), p[0], p[1]))

    # -- stream construction ----------------------------------------------
    def append_documents(self, surfaces: list[Surface]) -> None:
        """Append surfaces to the stream, minting terminal ids for unseen
        words. Existing terminal ids are untouched, by construction."""
        base = len(self.sym)
        f = self.freq
        for s in surfaces:
            self.doc_start.append(len(self.sym))
            self.doc_meta.append((s.corpus, s.statement_id, s.kind))
            for word in s.words:
                t = self._terminal(word)
                self.sym.append(t)
                f[t] = f.get(t, 0) + 1
            self.sym.append(self.eod)
            f[self.eod] = f.get(self.eod, 0) + 1
        n = len(self.sym)
        self.nxt.extend(range(base + 1, n + 1))
        self.prv.extend(range(base - 1, n - 1))
        self.nxt[n - 1] = -1
        if base:
            # stitch the increment onto the existing stream; the joint sits
            # between an EOD and a document head, so no pair spans it
            self.nxt[base - 1] = base
        self.length = sum(1 for x in self.sym if x is not None)
        self.word_symbols = sum(
            1 for x in self.sym if x is not None and x != self.eod
        )
        for i in range(base, n):
            self._register(i)

    # -- rule application --------------------------------------------------
    def actual_count(self, pair: tuple[int, int]) -> int:
        """Non-overlapping left-to-right occurrence count of `pair`.

        `len(self.pairpos[pair])` over-counts inside runs such as `a a a`,
        where two registered positions yield only one replacement. The MDL
        gate must be fed the number of replacements that will really happen.
        """
        slots = self.pairpos.get(pair)
        if not slots:
            return 0
        a, b = pair
        n = 0
        consumed = -1
        for i in sorted(slots):
            if i == consumed or self.sym[i] != a:
                continue
            j = self.nxt[i]
            if j < 0 or self.sym[j] != b:
                continue
            n += 1
            consumed = j
        return n

    def apply_rule(self, pair: tuple[int, int], new_id: int) -> int:
        """Replace every non-overlapping occurrence of `pair` with `new_id`."""
        slots = self.pairpos.pop(pair, None)
        if not slots:
            return 0
        a, b = pair
        replaced = 0
        for i in sorted(slots):
            if self.sym[i] != a:
                continue
            j = self.nxt[i]
            if j < 0 or self.sym[j] != b:
                continue
            p = self.prv[i]
            k = self.nxt[j]
            if p >= 0:
                self._unregister(p)
            self._unregister(j)
            self.sym[i] = new_id
            self.nxt[i] = k
            if k >= 0:
                self.prv[k] = i
            self.sym[j] = None
            self.nxt[j] = -1
            self.prv[j] = -1
            self.length -= 1
            self.word_symbols -= 1
            if p >= 0:
                self._register(p)
            self._register(i)
            replaced += 1
        if replaced:
            f = self.freq
            f[a] = f.get(a, 0) - replaced
            f[b] = f.get(b, 0) - replaced
            f[new_id] = f.get(new_id, 0) + replaced
        return replaced

    def mint(self, pair: tuple[int, int]) -> int:
        a, b = pair
        new_id = RULE_NS | len(self.rules)
        self.rules.append(pair)
        self.depth[new_id] = 1 + max(self.depth[a], self.depth[b])
        self.expansion[new_id] = self.expansion[a] + self.expansion[b]
        self.apply_rule(pair, new_id)
        return new_id

    def replay_rules(self, upto: int) -> int:
        """Apply rules 0..upto-1, in mint order, to whatever occurrences are
        currently live. On a stream that has already been reduced this is a
        no-op; on a freshly appended increment it is exactly the encoder that
        re-uses existing ids instead of re-deriving them."""
        used = 0
        for idx in range(upto):
            if self.apply_rule(self.rules[idx], RULE_NS | idx):
                used += 1
        return used

    def rebuild_heap(self) -> None:
        self.heap = [
            (-len(s), p[0], p[1]) for p, s in self.pairpos.items() if len(s) >= 2
        ]
        heapq.heapify(self.heap)

    # -- cost models -------------------------------------------------------
    def flog_sum(self) -> float:
        return sum(_flog(v) for v in self.freq.values() if v > 0)

    def _flog_after(self, pair: tuple[int, int], c: int, flog: float) -> float:
        """sum(f*log2 f) after minting `pair` with `c` replacements."""
        a, b = pair
        fa, fb = self.freq.get(a, 0), self.freq.get(b, 0)
        if a == b:
            return flog - _flog(fa) + _flog(fa - 2 * c) + _flog(c)
        return (flog - _flog(fa) - _flog(fb)
                + _flog(fa - c) + _flog(fb - c) + _flog(c))

    def _entropy_after(self, pair: tuple[int, int], c: int, flog: float,
                       mult: float) -> int:
        """Exact Model-C total after minting `pair` with `c` replacements."""
        flog2 = self._flog_after(pair, c, flog)
        w = code_width(len(self.terminals) + len(self.rules) + 1)
        return (self.lexicon_bits() + entropy_bits(self.length - c, flog2)
                + math.ceil((len(self.rules) + 1) * mult * 2 * w))

    # -- the MDL-gated induction loop --------------------------------------
    def induce(self, mult: float, mode: str = "fixed",
               trace: list | None = None) -> int:
        """Mint pairs while the MDL total strictly falls. Returns rules minted.

        Under `mode="fixed"` the stop is exact: savings rise monotonically
        with the occurrence count and the cost term does not depend on it, so
        the highest-count pair bounds every remaining candidate and "no
        candidate improves MDL" is proved rather than guessed.

        Under `mode="entropy"` occurrence count does NOT bound savings -- a
        rarer pair of rarer constituents can pay more per occurrence -- so
        stopping at the highest-count pair's failure is a heuristic. Model C's
        rule count is therefore a **lower bound** on what an exhaustive
        entropy-MDL search would mint, and it is a sensitivity arm precisely
        because its stop is weaker than Model A's.
        """
        lex = self.lexicon_bits()
        minted = 0
        flog = self.flog_sum() if mode == "entropy" else 0.0
        while self.heap:
            negc, a, b = heapq.heappop(self.heap)
            est = -negc
            pair = (a, b)
            slots = self.pairpos.get(pair)
            if slots is None or len(slots) != est:
                continue  # stale heap entry; a current one exists
            t = len(self.terminals)
            r = len(self.rules)
            if mode == "fixed":
                before = total_bits(lex, t, r, self.length, mult)

                def after(c: int) -> int:
                    return total_bits(lex, t, r + 1, self.length - c, mult)
            else:
                w = code_width(t + r)
                before = (lex + entropy_bits(self.length, flog)
                          + math.ceil(r * mult * 2 * w))

                def after(c: int) -> int:
                    return self._entropy_after(pair, c, flog, mult)

            # Fixed-width: `est` upper-bounds the savings of every remaining
            # candidate, so if the best case cannot pay, nothing can -- an
            # exact stop. Entropy: a heuristic stop, see the docstring.
            if after(est) >= before:
                break
            act = self.actual_count(pair)
            if act < 2:
                continue
            if after(act) >= before:
                continue  # dead forever: counts only fall, costs only rise
            if mode == "entropy":
                flog = self._flog_after(pair, act, flog)
            new_id = self.mint(pair)
            minted += 1
            if trace is not None:
                trace.append((new_id, pair, act))
        return minted

    # -- readout -----------------------------------------------------------
    def stats(self, mult: float, mode: str = "fixed") -> dict:
        lex = self.lexicon_bits()
        t = len(self.terminals)
        r = len(self.rules)
        w = code_width(t + r)
        enc = (self.length * w if mode == "fixed"
               else entropy_bits(self.length, self.flog_sum()))
        return {
            "bit_model_mode": mode,
            "terminals": t,
            "rules": r,
            "symbol_count": t + r,
            "code_width_bits": w,
            # A fixed-width code refuses every mint once V hits a power of
            # two, because the next id widens the whole stream. When this is
            # 0 the reported dictionary size was chosen by the code width,
            # not by the data -- read Model C instead.
            "symbols_below_next_width": (1 << w) - (t + r),
            "at_power_of_two_cliff": (t + r) == (1 << w),
            "encoded_stream_symbols": self.length,
            "terminal_lexicon_bits": lex,
            "encoded_bits": enc,
            "dictionary_bits": math.ceil(r * mult * 2 * w),
            "total_bits": lex + enc + math.ceil(r * mult * 2 * w),
        }

    def document_pattern(self, d: int) -> tuple[int, ...]:
        out = []
        i = self.doc_start[d]
        while i >= 0 and self.sym[i] is not None and self.sym[i] != self.eod:
            out.append(self.sym[i])
            i = self.nxt[i]
        return tuple(out)

    def expand(self, sym: int) -> list[str]:
        """Decode one symbol back to its words (round-trip check)."""
        out: list[str] = []
        stack = [sym]
        while stack:
            s = stack.pop()
            if s & RULE_NS:
                a, b = self.rules[s & ~RULE_NS]
                stack.append(b)
                stack.append(a)
            else:
                out.append(self.terminals[s])
        return out


# --------------------------------------------------------------------------
# Readouts
# --------------------------------------------------------------------------

def depth_histogram(g: Grammar) -> dict[str, int]:
    hist: dict[int, int] = {}
    for idx in range(len(g.rules)):
        d = g.depth[RULE_NS | idx]
        hist[d] = hist.get(d, 0) + 1
    return {str(k): hist[k] for k in sorted(hist)}


def live_depth_histogram(g: Grammar) -> dict[str, int]:
    """Depth of the symbols actually left in the encoded stream."""
    hist: dict[int, int] = {}
    for s in g.sym:
        if s is None or s == g.eod:
            continue
        d = g.depth[s]
        hist[d] = hist.get(d, 0) + 1
    return {str(k): hist[k] for k in sorted(hist)}


def pattern_readout(g: Grammar, kind: str, corpora: set[str] | None = None
                    ) -> dict:
    """§3c's count question at the sentence level: how many distinct top-level
    patterns survive when every surface is written in the induced vocabulary."""
    counts: dict[tuple[int, ...], int] = {}
    total = 0
    for d, (corpus, _sid, k) in enumerate(g.doc_meta):
        if k != kind:
            continue
        if corpora is not None and corpus not in corpora:
            continue
        pat = g.document_pattern(d)
        counts[pat] = counts.get(pat, 0) + 1
        total += 1
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    curve = {}
    for K in (1, 5, 10, 50, 100):
        curve[f"top{K}"] = round(
            sum(v for _, v in ordered[:K]) / max(total, 1), 4
        )
    single_symbol = sum(1 for p, _ in ordered if len(p) == 1)
    return {
        "surfaces": total,
        "distinct_patterns": len(counts),
        "patterns_that_are_one_symbol": single_symbol,
        "coverage_curve": curve,
        "top_patterns": [
            {
                "count": v,
                "symbols": len(p),
                "rendered": " ".join(
                    " ".join(g.expand(s)) for s in p
                )[:160],
            }
            for p, v in ordered[:5]
        ],
    }


def compression_baselines(surfaces: list[Surface]) -> dict:
    slotted = "\n".join(" ".join(s.words) for s in surfaces)
    raw = "\n".join(s.raw for s in surfaces)
    slotted_b = slotted.encode("utf-8")
    raw_b = raw.encode("utf-8")

    out = {
        "slotted_text_chars": len(slotted),
        "slotted_text_bytes": len(slotted_b),
        "raw_text_bytes": len(raw_b),
        "distinct_chars_slotted": len(set(slotted)),
        "char_encoding_bits": len(slotted) * code_width(len(set(slotted))),
        "utf8_byte_bits": len(slotted_b) * 8,
    }

    try:
        import zstandard as zstd  # type: ignore
        out["zstd_available"] = True
        c = zstd.ZstdCompressor(level=19)
        out["zstd19_slotted_bits"] = len(c.compress(slotted_b)) * 8
        out["zstd19_raw_bits"] = len(c.compress(raw_b)) * 8
        # Per-document, with and without a trained shared dictionary: the
        # design's §4 falsifier is "zstd-with-shared-dictionary over the same
        # bytes", and a shared dictionary only means anything when the units
        # are compressed separately (which is what addressability requires).
        samples = [" ".join(s.words).encode("utf-8") for s in surfaces]
        plain = sum(len(c.compress(x)) for x in samples)
        out["zstd19_per_document_bits"] = plain * 8
        try:
            zdict = zstd.train_dictionary(110 * 1024, samples, level=19)
            cd = zstd.ZstdCompressor(level=19, dict_data=zdict)
            trained = sum(len(cd.compress(x)) for x in samples)
            out["zstd19_dict_bits"] = trained * 8
            out["zstd19_dict_size_bits"] = len(zdict.as_bytes()) * 8
            out["zstd19_dict_plus_payload_bits"] = (
                trained + len(zdict.as_bytes())
            ) * 8
        except Exception as exc:  # pragma: no cover - binding-dependent
            out["zstd_dict_error"] = type(exc).__name__
    except ImportError:  # pragma: no cover - fallback path
        out["zstd_available"] = False
        out["zstd_fallback_note"] = (
            "zstandard package unavailable; zlib level 9 reported instead"
        )
        out["zlib9_slotted_bits"] = len(zlib.compress(slotted_b, 9)) * 8
        out["zlib9_raw_bits"] = len(zlib.compress(raw_b, 9)) * 8
    return out


def flat_baselines(g0_terminals: int, lexicon_bits: int, stream: int,
                   words: int) -> dict:
    w = code_width(g0_terminals)
    return {
        "distinct_words": g0_terminals,
        "stream_symbols": stream,
        "word_code_width_bits": w,
        "terminal_lexicon_bits": lexicon_bits,
        "flat_word_bits": lexicon_bits + stream * w,
        "words": words,
    }


def round_trip_ok(g: Grammar, surfaces: list[Surface], samples: int = 1500
                  ) -> bool:
    """Decode a sample of documents and compare to the slotted input.

    Strided, not a prefix: corpora are laid out in sorted-path order, so a
    prefix would only ever exercise `data/algebra` and never reach the
    12,514 lean_workbook surfaces where every deep block actually lives.
    """
    n = len(g.doc_start)
    stride = max(1, n // max(samples, 1))
    for d in range(0, n, stride):
        got: list[str] = []
        for s in g.document_pattern(d):
            got.extend(g.expand(s))
        if got != surfaces[d].words:
            return False
    return True


# --------------------------------------------------------------------------
# §3b append-only probe
# --------------------------------------------------------------------------

def append_only_probe(surfaces: list[Surface], holdout: str, mult: float
                      ) -> dict:
    """Induce on the corpus MINUS `holdout`, then feed the holdout's surfaces
    and count what the increment mints under the same gate.

    The invariant the design needs -- "no existing id ever changes meaning" --
    is asserted, not assumed: terminal spellings and rule right-hand sides
    must both be unchanged prefixes after the increment.
    """
    base = [s for s in surfaces if s.corpus != holdout]
    incr = [s for s in surfaces if s.corpus == holdout]
    if not incr:
        raise SystemExit(f"holdout corpus {holdout!r} contributes no surfaces")

    g = Grammar()
    g.append_documents(base)
    g.induce(mult)
    before = g.stats(mult)
    terminals_before = list(g.terminals)
    rules_before = list(g.rules)

    g.append_documents(incr)
    reused = g.replay_rules(len(rules_before))
    g.rebuild_heap()
    minted = g.induce(mult)
    after = g.stats(mult)

    assert g.terminals[: len(terminals_before)] == terminals_before, (
        "terminal ids were renumbered by the increment"
    )
    assert g.rules[: len(rules_before)] == rules_before, (
        "rule ids were renumbered by the increment"
    )
    assert len(g.rules) - len(rules_before) == minted

    incr_words = sum(len(s.words) for s in incr)
    incr_syms = 0
    for d in range(len(g.doc_start) - len(incr), len(g.doc_start)):
        incr_syms += len(g.document_pattern(d))

    # Path independence: is the grown dictionary the same OBJECT the one-shot
    # induction would have produced, or merely a compatible one? §3b needs
    # append-only ids; this asks the stronger question the design does not.
    mono = Grammar()
    mono.append_documents(surfaces)
    mono.induce(mult)
    grown_blocks = {
        " ".join(g.expand(RULE_NS | i)) for i in range(len(g.rules))
    }
    mono_blocks = {
        " ".join(mono.expand(RULE_NS | i)) for i in range(len(mono.rules))
    }

    return {
        "path_independence": {
            "note": (
                "blocks are compared by the words they expand to, since "
                "mint order differs between the two paths"
            ),
            "monolithic_rules": len(mono.rules),
            "grown_rules": len(g.rules),
            "blocks_in_both": len(grown_blocks & mono_blocks),
            "blocks_only_when_grown": sorted(grown_blocks - mono_blocks),
            "blocks_only_when_monolithic": sorted(mono_blocks - grown_blocks),
            "identical_dictionary": grown_blocks == mono_blocks,
            "monolithic_total_bits": mono.stats(mult)["total_bits"],
        },
        "holdout_corpus": holdout,
        "base_surfaces": len(base),
        "increment_surfaces": len(incr),
        "increment_words": incr_words,
        "rules_before": len(rules_before),
        "rules_after": len(g.rules),
        "new_rules_minted_by_increment": minted,
        "existing_rules_reapplied_to_increment": reused,
        "terminals_before": len(terminals_before),
        "terminals_after": len(g.terminals),
        "new_terminals_minted_by_increment": (
            len(g.terminals) - len(terminals_before)
        ),
        "existing_ids_unchanged": True,
        "increment_symbols_after_encoding": incr_syms,
        "increment_words_per_symbol": round(
            incr_words / max(incr_syms, 1), 3
        ),
        "increment_round_trips": _incr_round_trip(g, incr),
        "total_bits_before": before["total_bits"],
        "total_bits_after": after["total_bits"],
    }


def _incr_round_trip(g: Grammar, incr: list[Surface]) -> bool:
    start = len(g.doc_start) - len(incr)
    for k, s in enumerate(incr):
        got: list[str] = []
        for sym in g.document_pattern(start + k):
            got.extend(g.expand(sym))
        if got != s.words:
            return False
    return True


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def stream_report(surfaces: list[Surface], name: str, do_patterns: bool,
                  ingested: set[str] | None) -> dict:
    words = sum(len(s.words) for s in surfaces)

    g0 = Grammar()
    g0.append_documents(surfaces)
    flat = flat_baselines(len(g0.terminals), g0.lexicon_bits(), g0.length, words)
    start_stream = g0.length

    arms: dict[str, dict] = {}
    grammars: dict[str, Grammar] = {}
    for label, mult, mode in (
        ("model_a", 1.0, "fixed"),
        ("model_b_2x_dictionary", 2.0, "fixed"),
        ("model_c_entropy", 1.0, "entropy"),
    ):
        g = Grammar()
        g.append_documents(surfaces)
        g.induce(mult, mode)
        st = g.stats(mult, mode)
        st["words_per_stream_symbol"] = round(
            words / max(g.word_symbols, 1), 3
        )
        st["mean_words_per_rule"] = round(
            sum(g.expansion[RULE_NS | i] for i in range(len(g.rules)))
            / max(len(g.rules), 1),
            3,
        )
        st["max_rule_expansion_words"] = max(
            [g.expansion[RULE_NS | i] for i in range(len(g.rules))] or [0]
        )
        st["max_composition_depth"] = max(
            [g.depth[RULE_NS | i] for i in range(len(g.rules))] or [0]
        )
        st["composition_depth_histogram"] = depth_histogram(g)
        st["live_symbol_depth_histogram"] = live_depth_histogram(g)
        st["dictionary_cost_multiplier"] = mult
        st["ratio_vs_flat_word_bits"] = round(
            flat["flat_word_bits"] / max(st["total_bits"], 1), 3
        )
        st["round_trip_ok"] = round_trip_ok(g, surfaces)
        st["fixed_width_id_arm"] = {
            "note": (
                "DESIGN §4: 2^24 structured ids are fixed-width by design. "
                "This arm prices the same encoded stream at the design's own "
                "id width instead of the MDL-minimal width."
            ),
            "id_width_bits": 25,
            "encoded_bits_at_25": g.length * 25,
            "dictionary_bits_at_25": math.ceil(len(g.rules) * mult * 2 * 25),
            "total_bits_at_25": (
                st["terminal_lexicon_bits"]
                + g.length * 25
                + math.ceil(len(g.rules) * mult * 2 * 25)
            ),
        }
        arms[label] = st
        grammars[label] = g

    report: dict = {
        "stream": name,
        "surfaces": len(surfaces),
        "slotted_words": words,
        "initial_stream_symbols": start_stream,
        "flat_word_baseline": flat,
        "compression_baselines": compression_baselines(surfaces),
        "mdl_arms": arms,
    }

    if do_patterns:
        g = grammars["model_a"]
        report["template_readout"] = {
            "note": (
                "DESIGN §2 recorded 5 distinct templates over ingested prose "
                "after hand-chosen slotting. These are the patterns the MDL "
                "induction chose, over the same slotting, with no threshold."
            ),
            "all_meanings": pattern_readout(g, "meaning"),
            "titles": pattern_readout(g, "title"),
        }
        if ingested:
            report["template_readout"]["ingested_prose_only"] = pattern_readout(
                g, "meaning", ingested
            )
    return report


def build_report(data_dir: Path, holdout: str, formal_stream: bool) -> dict:
    prose, formal = load_surfaces(data_dir)
    report: dict = {
        "design": "docs/DESIGN-block-vocabulary.md",
        "section": "3c",
        "bit_model": {
            "total_bits": "terminal_lexicon_bits + encoded_bits + dictionary_bits",
            "code_width": "w = ceil(log2(terminals + rules)), one width for all",
            "encoded_bits": "stream_symbols * w",
            "dictionary_bits": "ceil(rules * multiplier * 2 * w)",
            "terminal_lexicon_bits": "sum over terminals of (utf8_len + 1) * 8",
            "gate": "mint iff total_bits strictly falls",
            "model_a_multiplier": 1.0,
            "model_b_multiplier": 2.0,
            "model_c": (
                "order-0 entropy stream cost, no fixed-width cliff; its stop "
                "is heuristic, so its rule count is a LOWER bound"
            ),
            "known_defect": (
                "Models A and B use a fixed-width code, which refuses every "
                "mint once terminals+rules reaches a power of two. Arms carry "
                "at_power_of_two_cliff; where it is true the dictionary size "
                "was chosen by the code width, not by the data."
            ),
        },
        "streams": {},
    }
    ingested = {"lean_workbook", "ingested_arithmetic"}
    report["streams"]["prose"] = stream_report(prose, "prose", True, ingested)
    if formal_stream and formal:
        report["streams"]["canonical_ascii"] = stream_report(
            formal, "canonical_ascii", False, None
        )
    report["append_only_probe"] = append_only_probe(prose, holdout, 1.0)
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="MDL-gated block-vocabulary induction")
    ap.add_argument("--data-dir", type=Path, default=REPO / "data")
    ap.add_argument("--holdout", default="logic",
                    help="corpus withheld for the append-only probe")
    ap.add_argument("--no-formal-stream", action="store_true")
    ap.add_argument("--write-report", type=Path, default=None)
    args = ap.parse_args(argv)

    report = build_report(args.data_dir, args.holdout,
                          not args.no_formal_stream)
    text = json.dumps(report, indent=2, sort_keys=False) + "\n"
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(text, encoding="utf-8")

    for name, p in report["streams"].items():
        print(f"[{name}] surfaces={p['surfaces']} words={p['slotted_words']}")
        for label, a in p["mdl_arms"].items():
            print(f"  {label:22s} rules={a['rules']:5d} "
                  f"depth<={a['max_composition_depth']} "
                  f"words/sym={a['words_per_stream_symbol']:7.3f} "
                  f"total_bits={a['total_bits']:9d} "
                  f"cliff={a['at_power_of_two_cliff']}")
        cb = p["compression_baselines"]
        print(f"  flat_word_bits={p['flat_word_baseline']['flat_word_bits']} "
              f"char_bits={cb['char_encoding_bits']}")
        for k in ("zstd19_slotted_bits", "zstd19_per_document_bits",
                  "zstd19_dict_plus_payload_bits", "zlib9_slotted_bits"):
            if k in cb:
                print(f"  {k}={cb[k]}")

    p = report["streams"]["prose"]
    cb = p["compression_baselines"]
    tr = p.get("template_readout", {})
    if tr:
        print(f"  meaning patterns={tr['all_meanings']['distinct_patterns']} "
              f"top10={tr['all_meanings']['coverage_curve']['top10']}")
        if "ingested_prose_only" in tr:
            io = tr["ingested_prose_only"]
            print(f"  ingested-only patterns={io['distinct_patterns']} "
                  f"(census snapshot said 5)")
    pr = report["append_only_probe"]
    print(f"  append-only: +{pr['new_rules_minted_by_increment']} rules, "
          f"+{pr['new_terminals_minted_by_increment']} terminals, "
          f"reused={pr['existing_rules_reapplied_to_increment']}, "
          f"round_trip={pr['increment_round_trips']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
