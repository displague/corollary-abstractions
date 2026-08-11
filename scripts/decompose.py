#!/usr/bin/env python3
"""Derivational composition: read each statement as a construct of known forms.

The matchers relate WHOLE statements; this tool walks every statement's
canonical tree and asks, for each constituent subterm, "which known form is
this an instance of?" — where the form inventory is (a) the expression-side
skeletons of every corpus statement and (b) recurring subterm families
across statements. Output: per-statement decompositions ("the SSM update's
right side is two scaled-linear constituents joined by +"), i.e. statements
as constructs of other forms — commitment #1 of docs/DESIGN-concept-tokens.md
made mechanical, and the substrate for composing new mathematically grounded
statements from named parts.

Constituents are matched at the typed level (parameter/variable categories
respected). Trivial subterms (single leaves) are excluded; a constituent
reports every statement whose expression side shares its skeleton, plus how
many corpus statements contain it as a subterm.

Groundedness v2 repairs two MEASURED pathologies of the v1 score (both in
docs/BACKLOG.md):

1. *An instance graded less grounded than its pattern.*
   `narrative.constraint.chekhov_gun` scored 0.000 while the abstraction it
   instantiates, `temporal.response.response_pattern`, scored 0.500 — because
   exact skeleton lookup sees `EVENTUALLY⟨DISCHARGED⟨?0⟩⟩` and
   `EVENTUALLY⟨?0⟩` as unrelated strings. A constituent that fails exact
   lookup is now re-tried with the specialize.py matcher, every known form
   used AS PATTERN against it, so a pattern slot may bind the constituent's
   instantiated call subtree. Counted separately as `grounded_via_pattern`.

2. *Recursive definitions graded 0.000, i.e. as gibberish.*
   `temporal.recurrence.until_unfolding` defines UNTIL in terms of itself, so
   every constituent carried the head being defined and none could be found in
   an inventory built from *other* statements. A statement whose definiendum
   head recurs in the other side of the relation is marked `recursive`, and
   its self-headed constituents leave the denominator: they are definitional,
   not ungrounded.

Groundedness v3 splits the score by PROVENANCE CHANNEL (ROADMAP-v0.7 item 10).
The aggregate is unchanged; what changes is that it is no longer reported
alone, because the aggregate hid *where* the credit came from. The recorded
counterexample (docs/BACKLOG.md, docs/DISCOVERIES.md): all six
`data/provability` nodes ground at 1.000 on arrival though BOX occurs nowhere
else in the graph — intra-corpus BOX recurrence counts unconditionally, and
the pattern channel grounds Loeb's boxed premise on ex falso's
`IMPLIES⟨?0:P, ?1:V⟩` by a slot swallowing the boxed subtree. One number
cannot distinguish that from a statement built out of the rest of the graph.

Every grounded constituent is therefore attributed to exactly one channel:

- `external` — its supporting statements live in another corpus that shares
  no discipline label with this statement. The only channel that is evidence
  of grounding in knowledge the statement's authoring act did not bring with
  it.
- `prior_corpus` — another corpus, but the two statements share a discipline
  label (`theory_context.disciplines`; 57 nodes carry more than one and six
  labels span corpora). Same discipline, separately authored. MEASURED, and
  smaller than the first draft of this docstring claimed: 4 of 440 exact
  constituents, graph mean 0.008, and all four share the umbrella label
  `mathematics`. The *mechanism* is necessary — without it those four would
  be counted as external evidence, which is exactly the umbrella laundering
  `shared_disciplines` exists to expose — but the channel is not today a
  substantive source of credit, and "a real channel rather than a formality"
  overstated what was measured.
- `same_corpus` — the supporting statements are siblings in this statement's
  own `nodes.json`, i.e. authored in the same act. This is the channel that
  lets a hermetic corpus self-certify.
- `recursive` — self/definitional, and STRUCTURALLY EMPTY at the shipped
  defaults. The only path that produces recursive credit is `best_channel`'s
  empty-tally fallback: a constituent that passes the grounding test with no
  *other* statement supporting it. `analyze` subtracts the statement from
  both owner sets before classifying (`named` at the exact-lookup site, and
  `hosts` via `- {n.statement_id}`), so at `min_family >= 2` a constituent
  can only pass by recurring in some other statement and the fallback is
  unreachable. The channel's emptiness across all 22 corpora is therefore a
  consequence of the design, not a fact about the data; an earlier draft of
  this docstring and of docs/DISCOVERIES.md attributed it to the data and was
  wrong. It is reachable, and large, at `--min-family 1`: 200 constituents
  over 105 statements, graph mean 0.316, because a subterm family of size one
  (the statement itself) then passes the test with an empty owner set. The v2
  self-headed exclusion can also route a whole statement here by emptying its
  denominator; measured, none does — all four recursive definitions keep two
  or three surviving constituents.
- `pattern_absorption` — the v2 slot-swallows-structure channel. Credit here
  is quarantined regardless of who owns the pattern: a slot binding a call
  subtree says the constituent is an *instance* of a known shape, not that
  its own vocabulary is known. `absorbed_from_channel` on each constituent
  records the provenance the credit would have claimed under the aggregate,
  which for Loeb's premise is `external` — exactly the credit the aggregate
  hid.

Precedence for exact matches is the most independent owner present
(external > prior_corpus > same_corpus > recursive): attribution is generous
to the statement, so a near-zero `external` channel is a strong reading. That
generosity is the FLATTERING direction and it is load-bearing, not a
tie-break detail: 190 of the graph's 440 exact constituents have owners in
more than one channel, and all 190 are credited `external`. **Every reported
`external` share, and every `independent_mean`, is therefore an UPPER BOUND.**
`channel_summary` reports the least-independent counterpart beside it
(`channel_means_lower`, `external_lower`, `independent_lower`,
`self_certifying_lower`, `same_corpus_dominant_lower`) rather than replacing
it, so both readings stay on the record. Under the conservative rule graph
external falls 0.535 -> 0.246 (352 -> 162 constituents), with per-corpus
swings as large as `logic.boolean_foundations.v1` 0.812 -> 0.442 and
`algebra.foundations.v1` 0.143 -> 0.000; eight constituents are credited
`external` while their same-corpus owners outnumber their external ones (all
eight the `D⟨?0:V⟩` of `calculus`, two external owners against four
siblings). The headline is robust to the choice: `data/provability`'s
external share is 0.033 under both rules, because none of its exact
constituents is multi-owner.

Per statement the channel counts partition the grounded numerator over the
unchanged denominator, so the unrounded shares (`channel_shares`) sum to
`groundedness` exactly *before rounding*. The report's `channel_scores` are
those shares rounded to three places and may differ from `groundedness` in
the last digit: 3 of the 219 shipped rows do, by 0.001. Consumers that need
the identity must use `channel_shares`, and the shipped fields are asserted
only to within 0.002.

REGISTERED PREDICTIONS (2026-08-09, written before the first channel run;
adjudication appended below, per AGENTS.md working method 2):

- GC1: `data/provability`'s `external` channel mean lands at or below 0.15
  (point estimate 0.10), with at least three of its six nodes at exactly
  0.000 external. Non-zero at all only because bare `IMPLIES⟨?0:V, ?1:V⟩`
  subterms should match `logic`'s contraposition exactly.
- GC2: provability's `same_corpus` + `pattern_absorption` means together
  carry at least 0.80 of its 1.000 aggregate, with `same_corpus` the largest
  single channel.
- GC3: at least two non-provability corpora are also same-corpus-dominant
  (`same_corpus` mean > `external` + `prior_corpus` means). Named guess:
  `morphology` (a call-only corpus whose CONCAT/STEM/AFFIX vocabulary no
  other corpus uses); runner-up `narrative`.
- GC4: aggregates are untouched — every per-statement `groundedness` equals
  the pre-split value, the graph mean stays 0.770, and the totals stay 440
  exact / 75 via pattern.
- GC5: the partition identity holds for all 221 statements: the five channel
  counts sum to `grounded_exact + grounded_via_pattern`.

ADJUDICATION (2026-08-09, first channel run over all 22 corpora):

- GC1 **FIRED**, mechanism included. provability's `external` mean is 0.033,
  inside the predicted 0.15 and near the 0.10 point estimate, and five of six
  nodes are at exactly 0.000. The single external constituent is the one the
  prediction named: `k_distribution`'s inner `IMPLIES⟨?0:V, ?1:V⟩`, credited
  to `logic.inference.contraposition`. One constituent out of 17 is the whole
  extra-disciplinary content of a corpus that grades 1.000.
- GC2 **FIRED.** `same_corpus` 0.775 + `pattern_absorption` 0.192 = 0.967 of
  the 1.000 aggregate, `same_corpus` the largest channel, `prior_corpus` and
  `recursive` both 0.000.
- GC3 **FIRED, named guess included.** Four non-provability corpora are
  same-corpus-dominant (predicted at least two): `morphology` 0.498 vs 0.000
  — the named guess, and the cleanest case as guessed — `narrative` 0.308 vs
  0.077 (the runner-up guess), `temporal_logic` 0.255 vs 0.159, and
  `differential_topology` 0.567 vs 0.367, which was not anticipated and is
  the one corpus besides provability that grades 1.000. **Four is a LOWER
  BOUND**, because the owner precedence is generous to `external`: under the
  conservative rule the same test names 12 corpora, 11 of them
  non-provability. Generosity suppresses same-corpus dominance; it cannot
  manufacture it, so the direction of GC3's result is safe under both rules.
- GC4 **FIRED.** All 219 emitted entries are field-for-field identical to the
  pre-split report on `groundedness`, `considered`, `grounded_exact`,
  `grounded_via_pattern` and every pre-existing constituent key; graph mean
  0.770; totals 440 exact / 75 via pattern.
- GC5 **FIRED**, and is now a test
  (`tests/test_decompose_channels.py`): the five channel counts sum to the
  grounded numerator for every one of the 219 emitted entries. (The
  prediction said 221, the node count; two nodes have no non-trivial
  constituent at all and emit no entry, as before the split.)

Two unpredicted results were recorded because they were not predicted. BOTH
were CORRECTED under review on 2026-08-09; the original wording is kept in
docs/DISCOVERIES.md with the correction attached, per the retraction
discipline (AGENTS.md working method 2).

- The `recursive` channel is empty across the whole graph (0.000 everywhere).
  ORIGINALLY recorded as an observation about the corpus — "the four
  self-referential definitions kept non-empty denominators after the v2
  exclusion, so nothing lands in it." That sentence is true of those four
  definitions but it is not the reason, and stating it as the reason
  concealed the real one: at `min_family >= 2` the channel is structurally
  unreachable (see the `recursive` bullet above), so no corpus of any shape
  could have landed in it. **The emptiness is a design consequence, not a
  data observation**, and it is sensitive to one flag: at `--min-family 1`
  the channel carries 200 constituents and a graph mean of 0.316.
  `temporal.recurrence.until_unfolding` grading 1.000 with all three
  surviving constituents in `pattern_absorption` stands exactly as measured:
  v2 moved it off 0.000 entirely by slot absorption, a fact the aggregate
  could not show.
- 62 of the graph's 75 pattern-absorption constituents absorb a pattern whose
  MOST INDEPENDENT owner is outside the absorbing statement's discipline
  (82.7%). Under the all-owners reading it is 36 of 75 (48.0%); the other 26
  also have a same-corpus owner (25) or a prior-corpus one (1). The
  *inference* originally drawn — "absorption is where external-looking credit
  concentrates graph-wide, not a provability quirk" — **is RETRACTED: it
  failed the capability-blind baseline it never ran** (AGENTS.md working
  method 3). The exact channel, measured the same two ways, is 352 of 440
  best-owner external (80.0%) and 162 of 440 all-owner external (36.8%) — a
  wash against absorption by rate under either reading, and 5.7:1 in
  absorption's disfavour by absolute count (352 constituents against 62).
  Absorption is not where cross-discipline-looking credit concentrates; it is
  where such credit is *quarantined*, which was the design intent all along.
  What survives is the narrow fact and nothing more: most absorbed patterns
  have an out-of-discipline owner, and the aggregate silently claimed that
  provenance for them.

REGISTERED PREDICTION GC6 (2026-08-09, written before the conservative
rollup was implemented, in response to the channel-split review's finding
that owner precedence is the flattering direction):

- GC6: `data/provability` is flagged `self_certifying` under BOTH owner rules
  — the generous most-independent one and the conservative least-independent
  one — and remains the only corpus so flagged under either. This is a weak
  prediction and is registered as one: the review had already reported that
  provability's `external` is rule-invariant at 0.033. The live risk is the
  other leg of `independent_mean`, since the conservative rule moves credit
  toward `prior_corpus` as well as `same_corpus`, and a corpus can lose the
  flag by gaining prior-corpus credit.

ADJUDICATION (2026-08-09): GC6 **FIRED.** Under the conservative rule
provability's `external` stays 0.033 and its `prior_corpus` stays 0.000, so
`independent_lower` is 0.033 and it is the only corpus flagged under either
rule. The rule change is not cosmetic elsewhere: graph `external` falls
0.535 -> 0.246 and the same-corpus-dominant list grows from 5 corpora to 12.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from match_signatures import (
    Parser, TemplateParseError, canonicalize, load_nodes, skeleton,
    slot_classes, tokenize,
)
from specialize import MatchState, match, op_count


def subterms(t: tuple, path: tuple = ()):
    """Yield (path, subtree) for every non-leaf subtree, including relation
    sides but not the relation itself."""
    if t[0] == "rel":
        for i, side in enumerate(t[2]):
            yield from subterms(side, path + (i,))
        return
    if t[0] in {"op", "call"}:
        yield path, t
        for i, a in enumerate(t[2]):
            yield from subterms(a, path + (i,))


def tree_size(t: tuple) -> int:
    if t[0] in {"slot", "num"}:
        return 1
    if t[0] == "rel":
        return sum(tree_size(a) for a in t[2])
    return 1 + sum(tree_size(a) for a in t[2])


def head_of(t: tuple) -> tuple | None:
    """(kind, name) for an applied node; None for leaves and relations."""
    return (t[0], t[1]) if t[0] in {"op", "call"} else None


def contains_head(t: tuple, head: tuple) -> bool:
    if t[0] in {"slot", "num"}:
        return False
    if head_of(t) == head:
        return True
    return any(contains_head(a, head) for a in t[2])


def defined_head(t: tuple) -> tuple | None:
    """The head a statement recursively defines, or None.

    A recursive definition has a *definiendum* side — a bare application of one
    named head to leaves, `UNTIL(PROPA, PROPB)` — whose head occurs again on
    the other side, under a different head. Both sides are tested because
    `canonicalize` sorts the operands of `=` by shape, so the definiendum is
    not reliably the left one.

    Three guards keep this to actual recursion; each was measured firing on the
    corpus when absent:

    - `call` heads only. `HYP^2 = LEG1^2 + LEG2^2` otherwise "defines" `^`, and
      the ideal gas law "defines" `*`. Arithmetic operators are shared
      vocabulary, never a definiendum.
    - the other side's root head must differ. Otherwise `ALWAYS(ALWAYS(P)) =
      ALWAYS(P)` (idempotence), `CATEGORY(CONCAT(STEM, AFFIX)) =
      CATEGORY(STEM)` (preservation) and contraposition read as definitions of
      their own head and empty their denominators.
    - the head must occur *below* the other side's root, which the previous
      guard implies but `EULERCHAR(M) = EULERCHAR(N)` (invariance under
      diffeomorphism) makes worth stating: same head both sides, no recursion.
    """
    if t[0] != "rel":
        return None
    for i, side in enumerate(t[2]):
        other = t[2][1 - i]
        if side[0] != "call" or not side[2]:
            continue
        if any(a[0] not in {"slot", "num"} for a in side[2]):
            continue
        head = head_of(side)
        if head_of(other) == head or other[0] not in {"op", "call"}:
            continue
        if any(contains_head(a, head) for a in other[2]):
            return head
    return None


# The provenance channels, in attribution precedence order: a constituent
# supported by several statements is credited to the most independent owner
# it has, so a low `external` share cannot be an artifact of a strict tie-break.
OWNER_CHANNELS = ("external", "prior_corpus", "same_corpus", "recursive")
CHANNELS = OWNER_CHANNELS + ("pattern_absorption",)

# The opposite tie-break, reported beside the shipped one so that every
# `external` share is bracketed rather than asserted. 190 of 440 exact
# constituents are multi-owner and all 190 are credited `external` under
# OWNER_CHANNELS; under this order the graph's external constituents fall
# 352 -> 162. Neither order is "the truth" — the pair is.
CONSERVATIVE_OWNER_CHANNELS = tuple(reversed(OWNER_CHANNELS))

# Thresholds for the `self_certifying` readout: a corpus that grades near the
# top of the scale while nearly none of the credit comes from outside its own
# authoring act. Chosen to bracket the recorded regression case (provability,
# aggregate 1.000 / independent 0.033) without catching the two other corpora
# at aggregate >= 0.9, whose credit is external; the discrimination is
# asserted in tests/test_decompose_channels.py rather than assumed.
SELF_CERTIFYING_AGGREGATE = 0.9
SELF_CERTIFYING_INDEPENDENT = 0.1


def owner_channel(sid: str, owner: str, corpus_of: dict[str, str],
                  disciplines_of: dict[str, frozenset]) -> str:
    """Which channel does `owner`'s support of `sid` belong to?

    Corpus identity, not directory name, is the authoring unit: a corpus is
    seeded in one act, so sibling nodes are "added together" by construction.
    Discipline membership is read per node (`theory_context.disciplines`), not
    per corpus, because nodes claim more disciplines than their corpus header
    does and an umbrella label like `mathematics` is exactly the kind of shared
    ground that must not be counted as external evidence.

    PRECONDITION: `owner != sid`. `analyze` subtracts the statement from every
    owner set before classifying, so a statement is never its own owner here.
    This function used to answer `"recursive"` for the self case; review
    measured that branch taking zero calls at every `--min-family`, while the
    docstring cited it as the source of recursive credit — a dead branch
    standing in for the real mechanism (`best_channel`'s empty-tally
    fallback). It is now an enforced invariant rather than a silent one, so
    that a future caller which stops subtracting the statement fails loudly
    instead of quietly minting self-grounding.
    """
    if owner == sid:
        raise ValueError(
            f"owner_channel called with owner == sid ({sid!r}); owner sets "
            "must have the statement subtracted before attribution")
    if corpus_of.get(owner) == corpus_of.get(sid):
        return "same_corpus"
    if disciplines_of.get(owner, frozenset()) & disciplines_of.get(sid, frozenset()):
        return "prior_corpus"
    return "external"


def best_channel(channels) -> str:
    """Most independent owner channel present; `recursive` if there is none.

    The final `return` is not a defensive default — it is the ONLY path by
    which the `recursive` channel is ever populated. An empty tally means a
    constituent passed the grounding test with no supporting statement other
    than its own, which at `min_family >= 2` cannot happen (see the module
    docstring's `recursive` bullet) and at `--min-family 1` happens 200 times.
    """
    for ch in OWNER_CHANNELS:
        if ch in channels:
            return ch
    return "recursive"


def least_independent_channel(channels) -> str:
    """`best_channel`'s conservative counterpart: the least independent owner.

    Used only by the `*_lower` rollup, never to score a constituent. It exists
    so that the shipped `external` share is published as an upper bound with
    its lower bound beside it, rather than as a point estimate whose value
    depends on an undisclosed tie-break.
    """
    for ch in CONSERVATIVE_OWNER_CHANNELS:
        if ch in channels:
            return ch
    return "recursive"


def load_trees(data_dir: Path):
    """Rebuild trees + slot classes + provenance index.

    `load_nodes` keeps only skeleton strings and the corpus-level discipline,
    so the corpus files are re-read here for the canonical trees and for the
    per-node provenance the channel split needs.
    """
    trees: dict[str, tuple] = {}
    classes: dict[str, dict[str, str]] = {}
    corpus_of: dict[str, str] = {}
    disciplines_of: dict[str, frozenset] = {}
    for corpus_path in sorted(data_dir.glob("*/nodes.json")):
        corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
        corpus_id = corpus.get("corpus_id", corpus_path.parent.name)
        corpus_discipline = corpus.get("discipline", corpus_path.parent.name)
        for nj in corpus.get("statement_nodes", []):
            sid = nj.get("statement_id")
            corpus_of[sid] = corpus_id
            declared = nj.get("theory_context", {}).get("disciplines", [])
            disciplines_of[sid] = frozenset(declared or [corpus_discipline])
            tmpl = nj.get("structural_signature", {}).get("anonymized_template", "")
            try:
                trees[sid] = canonicalize(Parser(tokenize(tmpl)).parse())
            except TemplateParseError:
                continue
            classes[sid] = slot_classes(nj)
    return trees, classes, corpus_of, disciplines_of


def analyze(data_dir: Path, min_family: int = 2, max_pattern_attempts: int = 250,
            pattern_membership: bool = True) -> dict:
    """Decompose every statement and attribute its grounding to channels."""
    nodes, _ = load_nodes(data_dir)
    trees, classes, corpus_of, disciplines_of = load_trees(data_dir)

    # Form inventory 1: expression-side skeletons of whole statements.
    # `form_rep` keeps one concrete (tree, slot_class) witness per skeleton so
    # the form can later be used as a *pattern* by specialize.py's matcher.
    side_forms: dict[str, list[str]] = defaultdict(list)
    form_rep: dict[str, tuple[tuple, dict[str, str]]] = {}
    for n in nodes:
        t = trees.get(n.statement_id)
        if t is None:
            continue
        sides = t[2] if t[0] == "rel" else (t,)
        for side in sides:
            if side[0] in {"op", "call"}:
                skel = skeleton(side, classes[n.statement_id])
                side_forms[skel].append(n.statement_id)
                form_rep.setdefault(skel, (side, classes[n.statement_id]))

    # Form inventory 2: recurring subterm families across statements.
    subterm_hosts: dict[str, set] = defaultdict(set)
    for n in nodes:
        t = trees.get(n.statement_id)
        if t is None:
            continue
        for _, sub in subterms(t):
            if tree_size(sub) < 2:
                continue
            skel = skeleton(sub, classes[n.statement_id])
            subterm_hosts[skel].add(n.statement_id)
            form_rep.setdefault(skel, (sub, classes[n.statement_id]))

    # Pattern index for v2 grounding: known forms bucketed by root head, so a
    # constituent only ever tries the forms that could possibly match it.
    forms_by_head: dict[tuple, list[tuple]] = defaultdict(list)
    for skel, (tree, cls) in form_rep.items():
        owners = set(side_forms.get(skel, ())) | subterm_hosts.get(skel, set())
        forms_by_head[head_of(tree)].append(
            (op_count(tree), skel, tree, cls, owners))
    for bucket in forms_by_head.values():
        bucket.sort(key=lambda f: (-f[0], f[1]))  # most specific pattern first

    def known_form(skel: str, exclude: str) -> bool:
        """The v1 grounding test, reused to keep patterns to *known* forms."""
        if set(side_forms.get(skel, ())) - {exclude}:
            return True
        return len(subterm_hosts.get(skel, set())) >= min_family

    def pattern_cover(sub: tuple, own_skel: str, sid: str) -> tuple | None:
        """Find a known form that covers `sub` when read as a pattern.

        This is the fix for "an instance grades less grounded than its
        pattern": `EVENTUALLY⟨?0⟩` is a known form and Chekhov's gun's
        `EVENTUALLY⟨DISCHARGED⟨?0⟩⟩` is that form with the slot instantiated,
        which exact skeleton lookup cannot see.

        The accepted evidence is exactly the recorded pathology: some slot of
        the known form binds a *named-head application*. Weaker matches are
        refused on purpose —

        - slot-to-slot renaming is a twin, not a membership, and accepting it
          would silently grade P-vs-V category mismatches as grounding;
        - absorbing extra commutative arguments or vanishing a parameter into
          an identity element is *specialization*, which `specialize.py`
          already reports and where its recorded noise lives. Allowing it
          moves the corpus mean by +0.003 and is therefore not worth the
          justifications it prints: Beer-Lambert's `?0:P * ?1:V * ?2:V` was
          credited with grounding `?0:P * D⟨?1:V⟩` by letting a factor
          disappear, where the honest citation is the plain product form.
        """
        budget = max_pattern_attempts
        limit = op_count(sub)
        for pop, skel, tree, cls, owners in forms_by_head.get(head_of(sub), ()):
            if budget <= 0:
                break
            if pop > limit or skel == own_skel or not owners - {sid}:
                continue
            if not known_form(skel, sid):
                continue
            budget -= 1
            st = MatchState(cls)
            if (match(tree, sub, st)
                    and not (st.used_absorption or st.used_identity)
                    and any(v[0] == "call" for v in st.binds.values())):
                return skel, sorted(owners - {sid})
        return None

    def channel_of(sid: str, owners) -> tuple[str, dict[str, int]]:
        """Attribute a grounded constituent to one channel, generously."""
        tally: dict[str, int] = {}
        for owner in owners:
            ch = owner_channel(sid, owner, corpus_of, disciplines_of)
            tally[ch] = tally.get(ch, 0) + 1
        return best_channel(tally), tally

    decompositions = []
    for n in nodes:
        t = trees.get(n.statement_id)
        if t is None:
            continue
        cls = classes[n.statement_id]
        constituents = []
        n_considered = 0
        n_exact = 0
        n_pattern = 0
        n_self = 0
        channels = dict.fromkeys(CHANNELS, 0)
        self_head = defined_head(t)
        atomic = not any(path for path, _ in subterms(t))
        for path, sub in subterms(t):
            # Atomic statements (single call over leaves) are graded by their
            # root -- otherwise they fall off the ladder entirely (falsum
            # agent's finding: ex falso had no groundedness rung at all).
            if not path and not atomic:
                continue
            # A recursive definition's own head is definitional, not
            # ungrounded: the inventory is built from *other* statements, so
            # UNTIL cannot appear in it while UNTIL is being defined. Such
            # constituents leave the denominator instead of failing it.
            if self_head is not None and head_of(sub) == self_head:
                n_self += 1
                continue
            skel = skeleton(sub, cls)
            named = sorted(set(side_forms.get(skel, [])) - {n.statement_id})
            hosts = subterm_hosts.get(skel, set())
            n_considered += 1
            if named or len(hosts) >= min_family:
                n_exact += 1
                owners = (set(named) | hosts) - {n.statement_id}
                ch, tally = channel_of(n.statement_id, owners)
                channels[ch] += 1
                entry_c = {
                    "path": list(path),
                    "skeleton": skel,
                    "grounded_via": "exact",
                    "channel": ch,
                    "owner_channels": {k: tally[k] for k in CHANNELS if k in tally},
                    "instance_of_statements": named[:8],
                    "recurs_in_n_statements": len(hosts),
                }
                if ch == "prior_corpus":
                    # Name the label that made it prior rather than external, so
                    # an umbrella discipline cannot launder cross-corpus credit
                    # invisibly.
                    shared = set()
                    for owner in owners:
                        if owner_channel(n.statement_id, owner, corpus_of,
                                         disciplines_of) == "prior_corpus":
                            shared |= (disciplines_of[owner]
                                       & disciplines_of[n.statement_id])
                    entry_c["shared_disciplines"] = sorted(shared)
                constituents.append(entry_c)
                continue
            cover = None if not pattern_membership else pattern_cover(
                sub, skel, n.statement_id)
            if cover is None:
                continue
            n_pattern += 1
            pat_skel, pat_owners = cover
            channels["pattern_absorption"] += 1
            # The channel this credit would have claimed if slot absorption
            # were counted as ordinary grounding — the provenance the aggregate
            # hid. Reported, never added to an owner channel.
            absorbed_ch, absorbed_tally = channel_of(n.statement_id, pat_owners)
            constituents.append({
                "path": list(path),
                "skeleton": skel,
                "grounded_via": "pattern",
                "channel": "pattern_absorption",
                "absorbed_from_channel": absorbed_ch,
                "absorbed_owner_channels": {k: absorbed_tally[k]
                                            for k in CHANNELS
                                            if k in absorbed_tally},
                "instance_of_pattern": pat_skel,
                "pattern_known_from": pat_owners[:8],
                "pattern_recurs_in_n_statements": len(pat_owners),
            })
        # Groundedness: the epistemic-ladder grade for "disorder" — fraction
        # of non-trivial constituents matching known forms, exactly or as
        # instances of a known pattern. 1.0 = every piece is a named/recurring
        # form; low values shade toward gibberish.
        n_grounded = n_exact + n_pattern
        score = round(n_grounded / n_considered, 3) if n_considered else 1.0
        if constituents or n_considered or n_self:
            # Channel shares partition the score over the unchanged
            # denominator. A statement with an empty denominator scored 1.0
            # only because every constituent was definitional (v2's self-headed
            # exclusion), so the whole share is recursive — the aggregate said
            # "perfectly grounded" where the channel says "grounded in itself".
            if n_considered:
                shares = {ch: channels[ch] / n_considered for ch in CHANNELS}
            else:
                shares = dict.fromkeys(CHANNELS, 0.0)
                shares["recursive"] = 1.0
            entry = {
                "statement_id": n.statement_id,
                "corpus_id": corpus_of.get(n.statement_id, "<unknown>"),
                "discipline": n.discipline,
                "template": n.template,
                "groundedness": score,
                "considered": n_considered,
                "grounded_exact": n_exact,
                "grounded_via_pattern": n_pattern,
                "channels": dict(channels),
                "channel_scores": {ch: round(shares[ch], 3) for ch in CHANNELS},
                "constituents": constituents,
            }
            if self_head is not None:
                entry["recursive"] = True
                entry["defines_head"] = self_head[1]
                entry["self_headed_constituents_excluded"] = n_self
            decompositions.append(entry)

    return {
        "decompositions": decompositions,
        "channel_summary": channel_summary(decompositions),
        "n_nodes": len(nodes),
    }


def channel_shares(entry: dict) -> dict[str, float]:
    """Unrounded channel shares of one statement's groundedness.

    Sums to `groundedness` exactly (the rounded `channel_scores` in the report
    need not, which is why the rollup and the partition test use this).
    """
    considered = entry["considered"]
    if not considered:
        return {ch: (1.0 if ch == "recursive" else 0.0) for ch in CHANNELS}
    return {ch: entry["channels"][ch] / considered for ch in CHANNELS}


def conservative_channel_shares(entry: dict) -> dict[str, float]:
    """The same statement re-attributed under the least-independent owner rule.

    Recomputed from each constituent's recorded `owner_channels` tally, so it
    needs no second pass over the corpus and cannot drift from the shipped
    attribution. `pattern_absorption` is unaffected: absorbed credit is
    quarantined by the channel it lands in, not by who owns the pattern.
    """
    considered = entry["considered"]
    if not considered:
        return {ch: (1.0 if ch == "recursive" else 0.0) for ch in CHANNELS}
    counts = dict.fromkeys(CHANNELS, 0)
    for c in entry["constituents"]:
        if c["grounded_via"] == "pattern":
            counts["pattern_absorption"] += 1
        else:
            counts[least_independent_channel(c["owner_channels"])] += 1
    return {ch: counts[ch] / considered for ch in CHANNELS}


def channel_summary(decompositions: list[dict]) -> dict:
    """Per-corpus and whole-graph channel means.

    `self_certifying` flags the shape ROADMAP-v0.7 item 10 exists to expose:
    a corpus that grades near-perfect while almost none of the credit comes
    from outside its own authoring act. It is a reporting flag, not a gate —
    nothing consumes it yet, and the provability corpus is its regression case.

    Every `external`/`independent` figure here is an UPPER bound: exact
    constituents take their most independent owner, and 190 of 440 are
    multi-owner. The `*_lower` keys carry the least-independent counterpart so
    both bounds are published together; the flag survives under both, which is
    GC6 in the module docstring.
    """
    by_corpus: dict[str, list[dict]] = defaultdict(list)
    for d in decompositions:
        by_corpus[d["corpus_id"]].append(d)

    def block(entries: list[dict], discipline: str | None = None) -> dict:
        n = len(entries)
        shares = [channel_shares(e) for e in entries]
        means = {ch: (sum(s[ch] for s in shares) / n if n else 0.0)
                 for ch in CHANNELS}
        counts = {ch: sum(e["channels"][ch] for e in entries) for ch in CHANNELS}
        mean_g = sum(e["groundedness"] for e in entries) / n if n else 0.0
        independent = means["external"] + means["prior_corpus"]
        lower_shares = [conservative_channel_shares(e) for e in entries]
        lower = {ch: (sum(s[ch] for s in lower_shares) / n if n else 0.0)
                 for ch in CHANNELS}
        independent_lower = lower["external"] + lower["prior_corpus"]
        blk = {
            "statements": n,
            "mean_groundedness": round(mean_g, 3),
            "channel_means": {ch: round(means[ch], 3) for ch in CHANNELS},
            "channel_constituents": counts,
            "independent_mean": round(independent, 3),
            "same_corpus_dominant": means["same_corpus"] > independent,
            "self_certifying": (mean_g >= SELF_CERTIFYING_AGGREGATE
                                and independent <= SELF_CERTIFYING_INDEPENDENT),
            # Conservative counterpart: same constituents, least independent
            # owner. Reported beside the shipped figures, never replacing
            # them, so that `external` is read as a bracket and not a point.
            "channel_means_lower": {ch: round(lower[ch], 3) for ch in CHANNELS},
            "external_lower": round(lower["external"], 3),
            "independent_lower": round(independent_lower, 3),
            "same_corpus_dominant_lower": lower["same_corpus"] > independent_lower,
            "self_certifying_lower": (
                mean_g >= SELF_CERTIFYING_AGGREGATE
                and independent_lower <= SELF_CERTIFYING_INDEPENDENT),
        }
        if discipline is not None:
            blk["discipline"] = discipline
        return blk

    corpora = {cid: block(entries, entries[0]["discipline"])
               for cid, entries in sorted(by_corpus.items())}
    return {"graph": block(decompositions), "corpora": corpora}


def report(result: dict, write_report: Path | None = None) -> None:
    decompositions = result["decompositions"]
    summary = result["channel_summary"]
    n_with = sum(1 for d in decompositions if d["constituents"])
    n_named = sum(1 for d in decompositions
                  if any(c.get("instance_of_statements")
                         for c in d["constituents"]))
    scores = [d["groundedness"] for d in decompositions]
    mean_score = sum(scores) / len(scores) if scores else 0.0
    lowest = sorted(decompositions, key=lambda d: d["groundedness"])[:3]
    print(f"{n_with} of {result['n_nodes']} statements decompose into known forms; "
          f"{n_named} contain a constituent that IS another statement's "
          f"expression side.")
    print("Corpus mean groundedness: "
          f"{mean_score:.3f}; least grounded: "
          + ", ".join(f"{d['statement_id']} ({d['groundedness']})"
                      for d in lowest))
    n_exact_total = sum(d["grounded_exact"] for d in decompositions)
    n_pattern_total = sum(d["grounded_via_pattern"] for d in decompositions)
    print(f"Grounded constituents: {n_exact_total} exact, {n_pattern_total} "
          f"via pattern membership (a known form with a slot instantiated).")
    recursives = [d for d in decompositions if d.get("recursive")]
    if recursives:
        print("Recursive definitions (self-headed constituents excluded from "
              "the denominator): "
              + ", ".join(f"{d['statement_id']} defines {d['defines_head']}, "
                          f"{d['groundedness']}" for d in recursives))
    print()

    # Show the ones whose constituents are named statements — the
    # 'built from lemmas' readout.
    shown = 0
    for d in decompositions:
        named_cs = [c for c in d["constituents"]
                    if c.get("instance_of_statements")]
        if not named_cs or shown >= 20:
            continue
        shown += 1
        print(f"  {d['statement_id']}")
        print(f"    template: {d['template']}")
        for c in named_cs:
            others = ", ".join(c["instance_of_statements"][:3])
            more = ("..." if len(c["instance_of_statements"]) > 3 else "")
            print(f"    constituent at {c['path']}: {c['skeleton']}")
            print(f"      = expression side of: {others}{more} "
                  f"(recurs in {c['recurs_in_n_statements']} statements)")
        print()

    # The v2 readout: constituents that are a known form with a slot
    # instantiated — the membership exact skeleton lookup could not see.
    pattern_rows = [(d, c) for d in decompositions for c in d["constituents"]
                    if c["grounded_via"] == "pattern"]
    if pattern_rows:
        print(f"## Pattern membership ({len(pattern_rows)} constituents; "
              f"first 20)")
        for d, c in pattern_rows[:20]:
            print(f"  {d['statement_id']} at {c['path']}: {c['skeleton']}")
            known = ", ".join(c["pattern_known_from"][:3])
            n_from = c["pattern_recurs_in_n_statements"]
            print(f"    instantiates {c['instance_of_pattern']} "
                  f"(known from {n_from} statement{'' if n_from == 1 else 's'}"
                  f": {known})")
        print()

    # The v3 readout: where the score came from. The aggregate answers "how
    # much of this statement is made of known forms"; the channels answer
    # "known to whom" — and a corpus can only certify itself in the
    # same_corpus, recursive and pattern_absorption columns.
    print("## Groundedness by channel (mean share of each statement's score)")
    header = (f"  {'corpus':46s} {'n':>3s} {'aggr':>6s} {'extern':>7s} "
              f"{'prior':>7s} {'same':>7s} {'recurs':>7s} {'pattern':>7s}")
    print(header)
    print("  " + "-" * (len(header) - 2))
    rows = sorted(summary["corpora"].items(),
                  key=lambda kv: (kv[1]["independent_mean"], kv[0]))
    for cid, blk in rows:
        m = blk["channel_means"]
        flag = "  <- self-certifying" if blk["self_certifying"] else ""
        print(f"  {cid:46s} {blk['statements']:3d} "
              f"{blk['mean_groundedness']:6.3f} {m['external']:7.3f} "
              f"{m['prior_corpus']:7.3f} {m['same_corpus']:7.3f} "
              f"{m['recursive']:7.3f} {m['pattern_absorption']:7.3f}{flag}")
    g = summary["graph"]
    gm = g["channel_means"]
    print(f"  {'GRAPH':46s} {g['statements']:3d} {g['mean_groundedness']:6.3f} "
          f"{gm['external']:7.3f} {gm['prior_corpus']:7.3f} "
          f"{gm['same_corpus']:7.3f} {gm['recursive']:7.3f} "
          f"{gm['pattern_absorption']:7.3f}")
    flagged = [cid for cid, blk in summary["corpora"].items()
               if blk["self_certifying"]]
    print(f"  Self-certifying corpora (aggregate >= 0.9 while external + "
          f"prior_corpus <= 0.1): {', '.join(flagged) if flagged else 'none'}")
    dominant = [cid for cid, blk in summary["corpora"].items()
                if blk["same_corpus_dominant"]]
    print(f"  Same-corpus-dominant corpora (same_corpus mean above external + "
          f"prior_corpus): {', '.join(dominant) if dominant else 'none'}")

    # Every external figure above is an upper bound (exact constituents take
    # their most independent owner). Publish the bracket, not the point.
    flagged_lo = [cid for cid, blk in summary["corpora"].items()
                  if blk["self_certifying_lower"]]
    dominant_lo = [cid for cid, blk in summary["corpora"].items()
                   if blk["same_corpus_dominant_lower"]]
    print(f"  Conservative (least-independent owner) counterpart — every "
          f"`extern` above is an UPPER BOUND:")
    print(f"    graph external {gm['external']:.3f} -> "
          f"{g['channel_means_lower']['external']:.3f}, independent "
          f"{g['independent_mean']:.3f} -> {g['independent_lower']:.3f}")
    print(f"    self-certifying under both rules: "
          f"{', '.join(sorted(set(flagged) & set(flagged_lo))) or 'none'}"
          f"; same-corpus-dominant grows {len(dominant)} -> "
          f"{len(dominant_lo)} corpora (the shipped count is a lower bound)")

    # Absorption's cross-discipline share, stated both ways and beside the
    # capability-blind baseline it has to beat. It does not beat it: the
    # original "absorption is where such credit concentrates" reading is
    # retracted in the module docstring and docs/DISCOVERIES.md.
    def _ext(rows, key, tally_key):
        best = sum(1 for c in rows if c[key] == "external")
        allx = sum(1 for c in rows if set(c[tally_key]) == {"external"})
        return best, allx

    absorbed = [c for d in decompositions for c in d["constituents"]
                if c["channel"] == "pattern_absorption"]
    exact = [c for d in decompositions for c in d["constituents"]
             if c["grounded_via"] == "exact"]
    a_best, a_all = _ext(absorbed, "absorbed_from_channel",
                         "absorbed_owner_channels")
    e_best, e_all = _ext(exact, "channel", "owner_channels")
    n_abs, n_ex = len(absorbed) or 1, len(exact) or 1
    print(f"  Out-of-discipline ownership, absorption vs the exact-channel "
          f"baseline (best owner / all owners):")
    print(f"    pattern_absorption {a_best}/{len(absorbed)} "
          f"({a_best / n_abs:.1%}) / {a_all}/{len(absorbed)} "
          f"({a_all / n_abs:.1%})")
    print(f"    exact              {e_best}/{len(exact)} "
          f"({e_best / n_ex:.1%}) / {e_all}/{len(exact)} "
          f"({e_all / n_ex:.1%})")
    # The sentence must describe the data, not repeat the v0.7 adjudication:
    # the rate reading stopped being a wash at the v0.10 quantifier slice
    # (self-grounding corpus growth lowered exact's external rate), while the
    # count baseline still refuses the retracted inference outright.
    rate_gap = a_best / n_abs - e_best / n_ex
    rate_note = (
        "A wash by rate" if abs(rate_gap) < 0.12
        else f"Absorption leads by rate ({rate_gap:+.1%})" if rate_gap > 0
        else f"The exact channel leads by rate ({-rate_gap:+.1%})"
    )
    print(f"    {rate_note}; the exact channel dominates by absolute count "
          f"({e_best / (a_best or 1):.1f}:1). Absorption is where such credit "
          f"is quarantined, not where it concentrates.")
    print()

    if write_report:
        write_report.parent.mkdir(parents=True, exist_ok=True)
        write_report.write_text(json.dumps(
            {"decompositions": decompositions,
             "channel_summary": summary}, indent=2, ensure_ascii=False)
            + "\n", encoding="utf-8")
        print(f"Report written to {write_report}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--min-family", type=int, default=2,
                    help="a subterm family counts if it recurs in >= this many statements")
    ap.add_argument("--max-pattern-attempts", type=int, default=250,
                    help="cap on known forms tried as patterns per constituent")
    ap.add_argument("--no-pattern-membership", action="store_true",
                    help="disable v2 pattern matching (exact skeleton lookup only)")
    ap.add_argument("--write-report", type=Path, default=None)
    args = ap.parse_args()
    result = analyze(args.data_dir, min_family=args.min_family,
                     max_pattern_attempts=args.max_pattern_attempts,
                     pattern_membership=not args.no_pattern_membership)
    report(result, args.write_report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
