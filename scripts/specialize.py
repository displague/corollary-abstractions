#!/usr/bin/env python3
"""Specialization matcher (v3): find general->specific edges between nodes,
returning the CHEAPEST derivation rather than the first one found.

The exact-skeleton matcher (match_signatures.py) groups only isomorphic
templates, which misses relationships the corpus keeps recording as near
misses: the ideal gas law is the quantity theory of money with an explicit
dimensional constant; Cobb-Douglas is a power-law rate law with one more
factor; circle circumference is the affine archetype with SHIFT = 0.

This tool matches a *general* node's canonical tree as a pattern against a
*specific* node's tree, where:

- a pattern slot may bind any subtree (consistently across repeats);
- in commutative ops (+, *), a slot may ABSORB several arguments (binding to
  their sub-product/sum) -- how QT's 2x2 covers the gas law's 2x3;
- a parameter-like pattern slot may bind the op's identity element (0 for +,
  1 for *) when arguments run out -- how affine covers circumference
  (SHIFT -> 0). Variable-like slots may not vanish there: a law does not
  lose its variables, only its conventions;
- a declared-commutative CALL head (`MEET`, `JOIN`, `TOUCHES`) may have its
  two arguments matched in either order;
- a call head with a declared identity may COLLAPSE: `HEAD(a, e)` is `a`, so
  a pattern's slot argument may bind the identity and the call reduces to its
  other argument -- how iterated affixation covers plain affixation
  (SUFFIX -> EMPTY) and how absorption covers idempotence (the join operand
  goes to BOT). Here a variable-like slot MAY vanish, because the element it
  binds is one the corpus declares as a `constant` slot rather than a number
  the matcher invented.

Identities and commutativity both come from `match_signatures.HEAD_ALGEBRA`;
nothing about which heads have which algebra is decided in this file.

CHEAPEST-DERIVATION SEARCH
--------------------------
Five mechanisms can each explain the same pair, and the v2 matcher kept
whichever the recursion reached first. That let a weak reading pre-empt a
strong one (BACKLOG: `de9im_disjoint >= next_distributes_over_meet` was
matched by plain binding until the head-identity rule found `REGB -> TRUTH`
first and deleted the edge), and it was patched by running the whole matcher
twice with head identities disabled on the first pass -- a fix that does not
generalise to a third and fourth mechanism.

Here every mechanism carries a price, and the search returns the minimum-cost
ACCEPTABLE derivation over the whole space:

  slot -> slot rename            0   the pattern says exactly what the
                                     specific statement says
  slot -> structure          1 + op_count(bound)   one per node of the
                                     specific statement the pattern did not
                                     look at (a bare literal costs 1)
  absorption                     1   per EXTRA argument swallowed, on top of
                                     the structure cost of the sub-op built
                                     -- absorption invents a grouping the
                                     specific statement does not write
  arithmetic identity            2   per use; the pattern claims a degree of
                                     freedom (`SHIFT`) the specific lacks.
                                     Priced like swallowing a one-op subtree
  head-identity collapse         4   per use; the only mechanism that REMOVES
                                     a node from the pattern rather than
                                     filling one in, so it is the dearest

The structure component is `looseness` (which counts parenthesis depth of the
bindings) plus one per compound binding, so cost is a refinement of the old
ranking rather than a replacement for it; the algebra component is the
"how much algebra did this need" axis the BACKLOG asked for.

The search is exhaustive with branch-and-bound: every mechanism is tried in
cheap-first order, the first acceptable derivation becomes the incumbent, and
any partial derivation whose cost has already reached the incumbent's is
abandoned (cost is monotone along a derivation, so this is exact, not a
heuristic). Acceptability -- the non-triviality bar and the collapse guard --
is part of the search, not a post-filter, which is what makes the two-pass
workaround unnecessary: a derivation that would fail the collapse guard can
no longer pre-empt one that passes it, at ANY depth, whereas the pass
ordering only protected the root.

Only matches beyond pure slot-to-slot renaming are reported (a renaming is
an exact twin, already in the skeleton report): absorption, identity
binding, or a slot binding structure (a compound subtree or a literal).
Patterns must be rel- or call-rooted with at least two operator/call nodes,
else near-trivial templates (X = A*B) would subsume half the corpus.

IDENTITY SPELLING
-----------------
One lattice bottom is spelled `FALSITY` in data/logic, `EMPTYSET` in
data/set_theory and `INCONSISTENCY` in data/narrative. The spellings are
tried in the SPECIFIC statement's own vocabulary first (its `slot_schema`,
then its discipline's), so a set-theory edge prints `SETB -> EMPTYSET` where
v2 printed `SETB -> FALSITY` from table order. Edges that fall back to table
order say so in the report.
"""

from __future__ import annotations

import argparse
import json
import time
from functools import lru_cache
from itertools import combinations
from pathlib import Path

from match_signatures import (
    COMMUTATIVE, COMMUTATIVE_CALL_HEADS, ParsedNode, Parser,
    TemplateParseError, canonicalize, identity_terms, load_nodes, slot_classes,
    template_slots, tokenize,
)

# ---------------------------------------------------------------------------
# Cost model. See the module docstring for the reasoning; the numbers are
# tuned so that (a) cost restricted to plain bindings is monotone in the old
# `looseness`, and (b) the mechanisms rank in the order the corpus reads them:
# renaming < swallowing structure < inventing a grouping < spending a numeric
# identity < erasing a node from the pattern.
# ---------------------------------------------------------------------------
COST_BIND_NODE = 1        # per node of specific-statement structure swallowed
COST_ABSORB_ARG = 1       # per EXTRA argument absorbed into a sub-op
COST_IDENTITY = 2         # per arithmetic (+ / *) identity binding
COST_HEAD_COLLAPSE = 4    # per call node erased by a declared head identity

MIN_PATTERN_OPS = 2       # non-triviality bar, checked on the pattern AS USED

# Disciplines whose statements are ingested instances, not curated laws.
# They twin and they decompose by exact lookup; they do not specialize
# (docs/DESIGN-skeleton-emitter.md P-E4).
INGESTED_DISCIPLINES = frozenset({"lean_workbook", "ingested_arithmetic"})


def _ingested_discipline(discipline: str) -> bool:
    return discipline in INGESTED_DISCIPLINES


@lru_cache(maxsize=None)
def op_count(t: tuple) -> int:
    if t[0] in {"slot", "num"}:
        return 0
    return 1 + sum(op_count(a) for a in t[2])


class Deriv:
    """One (partial) derivation: the bindings so far plus what they cost.

    Immutable by discipline -- every step returns a new `Deriv` -- because the
    search is a generator pipeline and the save/restore mutation the v2
    matcher used cannot survive a suspended frame.
    """

    __slots__ = ("binds", "structure_cost", "algebra_cost", "absorbed",
                 "identity_uses", "head_collapses", "compound",
                 "ident_choices")

    def __init__(self, binds, structure_cost=0, algebra_cost=0, absorbed=0,
                 identity_uses=0, head_collapses=0, compound=0,
                 ident_choices=()):
        self.binds = binds
        self.structure_cost = structure_cost
        self.algebra_cost = algebra_cost
        self.absorbed = absorbed
        self.identity_uses = identity_uses
        self.head_collapses = head_collapses
        self.compound = compound
        self.ident_choices = ident_choices

    @property
    def cost(self) -> int:
        return self.structure_cost + self.algebra_cost

    def bind(self, name, term, structure=0, absorbed=0, compound=0):
        b = dict(self.binds)
        b[name] = term
        return Deriv(b, self.structure_cost + structure,
                     self.algebra_cost + absorbed * COST_ABSORB_ARG,
                     self.absorbed + absorbed, self.identity_uses,
                     self.head_collapses, self.compound + compound,
                     self.ident_choices)

    def bind_identity(self, name, term):
        """Arithmetic identity: a parameter slot vanishes into 0 or 1.

        Deliberately does NOT set `compound`, matching v2: the bound term is a
        bare number the matcher supplied, not structure it read off the
        specific statement, and `looseness` scores it 0 for the same reason.
        """
        b = dict(self.binds)
        b[name] = term
        return Deriv(b, self.structure_cost, self.algebra_cost + COST_IDENTITY,
                     self.absorbed, self.identity_uses + 1, self.head_collapses,
                     self.compound, self.ident_choices)

    def collapse(self, name, term, head, basis):
        """Head-identity collapse: `HEAD(keep, name)` reduces to `keep`."""
        b = dict(self.binds)
        b[name] = term
        return Deriv(b, self.structure_cost,
                     self.algebra_cost + COST_HEAD_COLLAPSE, self.absorbed,
                     self.identity_uses + 1, self.head_collapses + 1,
                     self.compound,
                     self.ident_choices + ((name, term[1], head, basis),))


EMPTY_DERIV = Deriv({})


class Search:
    """Branch-and-bound minimum-cost matcher for one (general, specific) pair.

    `run` consumes the generator pipeline eagerly; because the incumbent is
    read by `_pruned` on every recursive entry, improvements found early cut
    the remaining space while the generators are still suspended.
    """

    def __init__(self, slot_class: dict[str, str], pattern_ops: int,
                 idents_for_head, accept_all: bool = False):
        self.slot_class = slot_class
        self.pattern_ops = pattern_ops
        self.idents_for_head = idents_for_head
        # `accept_all` drops the two REPORTING bars (non-triviality, collapse
        # guard) and leaves a pure "cheapest derivation that matches at all"
        # search -- what the decompose.py facade at the bottom of the file
        # wants. Edge reporting always leaves it False.
        self.accept_all = accept_all
        self.best: Deriv | None = None
        self.best_cost: int | None = None
        self.steps = 0

    # -- acceptability ------------------------------------------------------

    def acceptable(self, d: Deriv) -> bool:
        if self.accept_all:
            return True
        # Head-identity collapse removes a call node from the pattern, so the
        # non-triviality bar (op_count >= 2, so that templates like `X = A*B`
        # cannot subsume half the corpus) has to be re-checked against the
        # pattern as *used*, not as written. Without this,
        # `MEET(REGA, REGB) = EMPTYSET` collapses to `REGA = EMPTYSET` and
        # matches every two-slot equation in the graph: measured, it was 507
        # extra edges, 500 of them from three such templates.
        if self.pattern_ops - d.head_collapses < MIN_PATTERN_OPS:
            return False
        # Informative = anything beyond pure slot-to-slot renaming (renamings
        # are exact twins, already in the skeleton report).
        return bool(d.absorbed or d.identity_uses or d.compound)

    def _pruned(self, d: Deriv) -> bool:
        self.steps += 1
        return self.best_cost is not None and d.cost >= self.best_cost

    def run(self, pat: tuple, term: tuple) -> Deriv | None:
        for d in self.gen(pat, term, EMPTY_DERIV):
            if not self.acceptable(d):
                continue
            if self.best_cost is None or d.cost < self.best_cost:
                self.best, self.best_cost = d, d.cost
        return self.best

    # -- the generator pipeline --------------------------------------------

    def gen(self, pat, term, d):
        if self._pruned(d):
            return
        yield from self.gen_direct(pat, term, d)
        # A declared identity lets a call collapse: for a head with a two-sided
        # identity e, HEAD(a, e) IS a, so a pattern whose vanishing argument is
        # a slot may bind that slot to e and match its other argument against
        # the whole term. This is the per-head generalization of the arithmetic
        # "argument runs out, bind 0 or 1" rule, and it is what makes CONCAT's
        # zero morph usable. Tried last and priced highest: it is the only
        # rewrite that shrinks the pattern.
        if pat[0] == "call" and self.idents_for_head(pat[1]):
            yield from self.gen_head_identity(pat, term, d)

    def gen_direct(self, pat, term, d):
        kind = pat[0]
        if kind == "slot":
            name = pat[1]
            if name in d.binds:
                if d.binds[name] == term:
                    yield d
                return
            if term[0] == "slot":
                yield d.bind(name, term)                      # free rename
            else:
                yield d.bind(name, term,
                             structure=COST_BIND_NODE * (1 + op_count(term)),
                             compound=1)
            return
        if kind == "num":
            if term[0] == "num" and term[1] == pat[1]:
                yield d
            return
        if term[0] != kind or term[1] != pat[1]:
            return
        if kind == "rel":
            (pl, pr), (tl, tr) = pat[2], term[2]
            yield from self.gen_seq((pl, pr), (tl, tr), d)
            if pat[1] == "=":
                yield from self.gen_seq((pl, pr), (tr, tl), d)
            return
        if kind == "op" and pat[1] in COMMUTATIVE:
            yield from self.gen_commutative(pat[1], list(pat[2]),
                                            list(term[2]), d)
            return
        if len(pat[2]) != len(term[2]):
            return
        if kind == "call" and pat[1] in COMMUTATIVE_CALL_HEADS and len(pat[2]) == 2:
            # Declared-commutative call head: try both argument orders. Both
            # trees are already canonically sorted, but the sort key erases
            # slot identity, so a pattern and a term can still disagree.
            for order in ((0, 1), (1, 0)):
                yield from self.gen_seq(
                    pat[2], (term[2][order[0]], term[2][order[1]]), d)
            return
        yield from self.gen_seq(pat[2], term[2], d)

    def gen_seq(self, pats, terms, d, i=0):
        if i == len(pats):
            yield d
            return
        for d2 in self.gen(pats[i], terms[i], d):
            yield from self.gen_seq(pats, terms, d2, i + 1)

    def gen_head_identity(self, pat, term, d):
        """Collapse `HEAD(keep, vanish)` to `keep` by binding `vanish` to
        HEAD's declared identity element.

        Unlike the arithmetic identity rule, this permits a VARIABLE-like slot
        to vanish. The justification is in the corpus: a zero morph *is* a
        morph (`morphology.wordformation.zero_morpheme_identity`,
        `CONCAT(STEM, EMPTY) = STEM`), and the element it binds is a slot the
        corpus declares `constant`, not a value invented by the matcher. The
        blanket rule ("a law does not lose its variables") is right for `+`
        and `*`, where the identity is a bare number, and wrong here.
        """
        args = pat[2]
        if len(args) != 2:
            return
        idents = self.idents_for_head(pat[1])
        for i in (1, 0):  # right identity first: the corpora write it that way
            vanish, keep = args[i], args[1 - i]
            if vanish[0] != "slot":
                continue
            name = vanish[1]
            for ident, basis in idents:
                if d.binds.get(name, ident) != ident:
                    continue
                yield from self.gen(
                    keep, term, d.collapse(name, ident, pat[1], basis))

    def gen_commutative(self, opname, pats, terms, d):
        """Assign term args to pattern args. Non-slot pattern args take
        exactly one term arg; slot args take >=1 (absorbing extras as a
        sub-op) or, for parameter-like slots, the identity element (none)."""
        if self._pruned(d):
            return
        if not pats:
            if not terms:
                yield d
            return
        pat = pats[0]
        if pat[0] != "slot":
            for i, t in enumerate(terms):
                for d2 in self.gen(pat, t, d):
                    yield from self.gen_commutative(
                        opname, pats[1:], terms[:i] + terms[i + 1:], d2)
            return

        name = pat[1]
        n = len(terms)
        remaining_needed = sum(1 for p in pats[1:] if p[0] != "slot"
                               or self.slot_class.get(p[1]) != "P")
        max_take = n - remaining_needed if n - remaining_needed >= 1 else 0
        # Cheap-first: a plain single-argument binding before absorption
        # before the identity rule. The order is only an efficiency hint --
        # the search is exhaustive and the minimum does not depend on it --
        # but it gets a tight incumbent in place before the dear branches run.
        for size in range(1, max_take + 1):
            for combo in combinations(range(n), size):
                taken = [terms[i] for i in combo]
                bound = taken[0] if size == 1 else canonicalize(
                    ("op", opname, tuple(taken)))
                if name in d.binds:
                    if d.binds[name] != bound:
                        continue
                    # Repeat binding: the structure was paid for the first
                    # time (as `looseness` also counts it once), but the
                    # absorption is a second invented grouping and is charged.
                    d2 = d.bind(name, bound, absorbed=max(0, size - 1))
                else:
                    struct = 0 if bound[0] == "slot" else (
                        COST_BIND_NODE * (1 + op_count(bound)))
                    # NOTE: deliberately no `compound=1` here, mirroring v2 --
                    # the commutative path never set `used_compound`, so an
                    # edge whose ONLY novelty is a commutative slot swallowing
                    # a subtree is still filtered as non-informative. Recorded
                    # in docs/BACKLOG.md; changing it is an edge-count change
                    # that does not belong in the cost-search commit.
                    d2 = d.bind(name, bound, structure=struct,
                                absorbed=max(0, size - 1))
                rest = [terms[i] for i in range(n) if i not in combo]
                yield from self.gen_commutative(opname, pats[1:], rest, d2)

        # Identity binding for parameter-like slots. The identity comes from
        # the declared HEAD_ALGEBRA table; for `+` and `*` it is a bare number,
        # so the parameter-only restriction stays (see gen_head_identity for
        # why declared constant slots are different).
        if self.slot_class.get(name) == "P":
            for ident, _basis in self.idents_for_head(opname):
                if d.binds.get(name, ident) != ident:
                    continue
                yield from self.gen_commutative(
                    opname, pats[1:], terms, d.bind_identity(name, ident))


# ---------------------------------------------------------------------------
# Compatibility facade for scripts/decompose.py
# ---------------------------------------------------------------------------
# `decompose.py` uses this module as a plain "does this pattern cover that
# subterm, and did it need any algebra to do it" predicate:
#
#     st = MatchState(cls)
#     if match(tree, sub, st) and not (st.used_absorption or st.used_identity)
#            and any(v[0] == "call" for v in st.binds.values()): ...
#
# The names are kept so that pass stays untouched. The semantics are the
# cost search's, with acceptability relaxed to "any successful derivation"
# (the non-triviality bar and the collapse guard belong to edge REPORTING,
# not to the predicate) -- which is the reading decompose.py was asking for
# all along: it wants the derivation that used the least algebra, and that is
# what minimising cost returns.
#
# This is NOT a no-op for decompose.py, and the difference is the branch's own
# thesis showing up in a second tool. `*(?0:P, ?1:V)` against
# `*(?0:P, LOG(?1:V))`: v2's first success bound `?0 -> 1` and absorbed the
# rest, which decompose.py rejects as algebra, so the honest category-correct
# grounding was never found and the coarser `*(?0:V, ?1:V)` was cited instead
# -- exactly the P-vs-V mismatch `pattern_cover`'s own docstring warns about.
# Measured: 10 of 198 nodes change constituents, corpus mean groundedness
# 0.7634 -> 0.7660, two calculus nodes gain a rung. `reports/decompositions.json`
# and `reports/compression.json` are deliberately NOT refreshed on this branch
# (see docs/BACKLOG.md -- both are already stale against committed data on
# `main`, so refreshing them here would smuggle an unrelated drift into a
# matcher commit).


class MatchState:
    """v2-shaped result holder; see the facade note above."""

    def __init__(self, slot_class: dict[str, str]):
        self.slot_class = slot_class
        self.binds: dict[str, tuple] = {}
        self.used_absorption = False
        self.used_identity = False
        self.used_compound = False
        self.head_collapses = 0


def match(pat: tuple, term: tuple, st: MatchState) -> bool:
    """True if `pat` covers `term`; fills `st` from the cheapest derivation."""
    search = Search(st.slot_class, op_count(pat), _bare_idents, accept_all=True)
    best = search.run(pat, term)
    if best is None:
        return False
    st.binds = dict(best.binds)
    st.used_absorption = bool(best.absorbed)
    st.used_identity = bool(best.identity_uses)
    st.used_compound = bool(best.compound)
    st.head_collapses = best.head_collapses
    return True


@lru_cache(maxsize=None)
def _bare_idents(head: str) -> tuple:
    """Identity spellings in HEAD_ALGEBRA table order, for callers with no
    specific-statement context to prefer a discipline's vocabulary from."""
    terms = identity_terms(head)
    sole = len(terms) < 2
    return tuple((t, "sole" if sole or t[0] != "slot" else "table-order")
                 for t in terms)


# ---------------------------------------------------------------------------
# Identity spelling: one abstract element, several corpus vocabularies
# ---------------------------------------------------------------------------

def spelling_ranker(spec_slots: frozenset, disc_slots: frozenset):
    """Order a head's identity spellings by the SPECIFIC statement's own
    vocabulary: names it declares itself first, then names its discipline
    uses anywhere, then the declaration order in HEAD_ALGEBRA.

    `HEAD_ALGEBRA["JOIN"]["identity"]` is `("FALSITY", "EMPTYSET",
    "INCONSISTENCY")` because the same lattice bottom is spelled three ways.
    v2 tried them in table order and so reported
    `settheory.boolean_laws.absorption >= settheory.boolean_laws.idempotence`
    as `SETB -> FALSITY` -- correct, but in the wrong corpus's vocabulary.
    Ties in cost keep the first spelling tried, so ranking here is what
    decides the printed spelling.
    """

    @lru_cache(maxsize=None)
    def ranked(head: str) -> tuple:
        terms = identity_terms(head)
        if not terms:
            return ()
        if len(terms) == 1:
            # A numeric identity, or a head the corpus spells one way only.
            return ((terms[0], "sole"),)
        out = []
        for t in terms:
            if t[0] != "slot":
                out.append((1, t, "sole"))
            elif t[1] in spec_slots:
                out.append((0, t, "specific-node"))
            elif t[1] in disc_slots:
                out.append((1, t, "specific-discipline"))
            else:
                out.append((2, t, "table-order"))
        out.sort(key=lambda r: r[0])  # stable: table order breaks rank ties
        return tuple((t, b) for _, t, b in out)

    return ranked


# ---------------------------------------------------------------------------


def find_specializations(nodes: list[ParsedNode], trees: dict[str, tuple],
                         classes: dict[str, dict[str, str]],
                         node_slots: dict[str, frozenset],
                         disc_slots: dict[str, frozenset]) -> tuple[list[dict], dict]:
    edges = []
    # The search is exhaustive, so it is bounded only by the shape of the
    # trees. `max_pair_steps` is reported so that the bound stays visible: if
    # a future corpus grows a wide commutative op (the subset enumeration is
    # the only super-linear part), it shows up here long before the wall time
    # does. v2 had exactly the same exposure -- a FAILING first-success match
    # already explores the whole space -- but no way to see it.
    stats = {"steps": 0, "max_pair_steps": 0, "max_pair": None}
    rankers = {n.statement_id: spelling_ranker(
        node_slots.get(n.statement_id, frozenset()),
        disc_slots.get(n.discipline, frozenset())) for n in nodes}
    for gen in nodes:
        gtree = trees[gen.statement_id]
        # rel-rooted equations AND call-rooted statements (inference rules,
        # relational predicates) may serve as patterns; the old rel-only
        # guard excluded all 16 inference-rule nodes (probed, BACKLOG).
        if gtree[0] not in {"rel", "call", "op"} or op_count(gtree) < MIN_PATTERN_OPS:
            continue
        # Fully-ground trees have nothing to bind. Using them as patterns
        # is algebra-swallowing noise and is already minutes-scale at
        # 508 nodes (docs/DESIGN-item4-authoring.md P6).
        if not template_slots(gtree):
            continue
        # Ingested statements are not specialize endpoints
        # (docs/DESIGN-skeleton-emitter.md P-E4). The remainder has slots,
        # so the ground skip above would let 8k inequalities become
        # generals; the curve does not need this ledger.
        if _ingested_discipline(gen.discipline):
            continue
        for spec in nodes:
            if spec.statement_id == gen.statement_id:
                continue
            if gen.shape == spec.shape:
                continue  # exact twins already reported
            # Fully-ground specifics do not participate either (P7).
            if not template_slots(trees[spec.statement_id]):
                continue
            if _ingested_discipline(spec.discipline):
                continue
            search = Search(classes[gen.statement_id], op_count(gtree),
                            rankers[spec.statement_id])
            best = search.run(gtree, trees[spec.statement_id])
            stats["steps"] += search.steps
            if search.steps > stats["max_pair_steps"]:
                stats["max_pair_steps"] = search.steps
                stats["max_pair"] = (gen.statement_id, spec.statement_id)
            if best is None:
                continue
            edge = {
                "general": gen.statement_id,
                "specific": spec.statement_id,
                "general_template": gen.template,
                "specific_template": spec.template,
                "via": "+".join(v for v, on in [
                    ("absorption", best.absorbed),
                    ("identity", best.identity_uses),
                    ("compound", best.compound)] if on),
                "cost": best.cost,
                "structure_cost": best.structure_cost,
                "algebra_cost": best.algebra_cost,
                "head_collapses": best.head_collapses,
                "bindings": {k: render(v) for k, v in sorted(best.binds.items())},
            }
            if best.ident_choices:
                edge["identity_spellings"] = [
                    {"slot": s, "spelling": sp, "head": h, "basis": b}
                    for s, sp, h, b in best.ident_choices]
                if any(b == "table-order" for _, _, _, b in best.ident_choices):
                    edge["identity_spelling_note"] = (
                        "no spelling of this identity occurs in the specific "
                        "statement's discipline; fell back to HEAD_ALGEBRA "
                        "table order")
            edges.append(edge)
    return edges, stats


def render(t: tuple) -> str:
    if t[0] == "slot":
        return t[1]
    if t[0] == "num":
        return f"{t[1]:g}"
    if t[0] == "rel":
        return f"{render(t[2][0])} {t[1]} {render(t[2][1])}"
    inner = ", ".join(render(a) for a in t[2])
    return f"{t[1]}({inner})"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--write-report", type=Path, default=None)
    args = ap.parse_args()

    nodes, problems = load_nodes(args.data_dir)
    trees: dict[str, tuple] = {}
    classes: dict[str, dict[str, str]] = {}
    node_slots: dict[str, frozenset] = {}
    disc_slots: dict[str, set] = {}
    for corpus_path in sorted(args.data_dir.glob("*/nodes.json")):
        corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
        discipline = corpus.get("discipline", corpus_path.parent.name)
        vocab = disc_slots.setdefault(discipline, set())
        for nj in corpus.get("statement_nodes", []):
            sid = nj.get("statement_id")
            sig = nj.get("structural_signature", {})
            tmpl = sig.get("anonymized_template", "")
            slots = slot_classes(nj)
            # The discipline's vocabulary is collected from EVERY node,
            # including ones whose template fails to parse: a corpus's
            # spelling of the lattice bottom is a fact about the corpus, not
            # about which of its statements the matcher can read.
            vocab.update(slots)
            try:
                trees[sid] = canonicalize(Parser(tokenize(tmpl)).parse())
            except TemplateParseError:
                continue
            classes[sid] = slots
            node_slots[sid] = frozenset(slots)
    kept = [n for n in nodes if n.statement_id in trees]
    frozen_disc = {k: frozenset(v) for k, v in disc_slots.items()}

    t0 = time.perf_counter()
    edges, stats = find_specializations(kept, trees, classes, node_slots,
                                        frozen_disc)
    elapsed = time.perf_counter() - t0
    # Tightness: how much structure the bindings had to swallow. Small =
    # near-exact relationship; large = loose structural analogy. `cost` is the
    # companion axis -- looseness plus what the algebra was charged for.
    for e in edges:
        e["looseness"] = sum(max(0, b.count("(")) for b in e["bindings"].values())
    edges.sort(key=lambda e: (e["cost"], e["looseness"], e["general"],
                              e["specific"]))
    cross = [e for e in edges
             if e["general"].split(".")[0] != e["specific"].split(".")[0]]
    print(f"Found {len(edges)} specialization edges "
          f"({len(cross)} cross-discipline) among {len(kept)} nodes.")
    summary = (f"Cheapest-derivation search: {stats['steps']} search steps in "
               f"{elapsed:.2f}s")
    if edges:
        costs = sorted(e["cost"] for e in edges)
        summary += (f"; cost range {costs[0]}-{costs[-1]} "
                    f"(median {costs[len(costs) // 2]})")
    print(summary + ".")
    if stats["max_pair"]:
        print(f"  worst single pair: {stats['max_pair_steps']} steps, "
              f"{stats['max_pair'][0]} vs {stats['max_pair'][1]}.")
    print()
    cross_ids = {(e["general"], e["specific"]) for e in cross}
    shown = edges[:40]
    for e in shown:
        tag = (" [CROSS-DISCIPLINE]"
               if (e["general"], e["specific"]) in cross_ids else "")
        print(f"  {e['general']}  >=  {e['specific']}  via {e['via']} "
              f"(cost {e['cost']} = {e['structure_cost']} structure + "
              f"{e['algebra_cost']} algebra, looseness {e['looseness']}){tag}")
        print(f"    general : {e['general_template']}")
        print(f"    specific: {e['specific_template']}")
        binds = ", ".join(f"{k}->{v}" for k, v in e["bindings"].items())
        print(f"    bindings: {binds}")
        if e.get("identity_spelling_note"):
            print(f"    note: {e['identity_spelling_note']}")
        print()
    if len(edges) > len(shown):
        print(f"  ... {len(edges) - len(shown)} costlier edges omitted from "
              f"stdout (all are in the JSON report).")

    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(
            json.dumps({"specialization_edges": edges}, indent=2,
                       ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Report written to {args.write_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
