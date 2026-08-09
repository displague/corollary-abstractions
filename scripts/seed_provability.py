#!/usr/bin/env python3
"""Seed data/provability/nodes.json — provability logic (GL) as corpus subject.

docs/DESIGN-cognitive-frames.md §4 orders this corpus: Willard's
self-verifying theories name the storage bet's boundary (trust roots stay
external; nothing self-attests), and GL — the modal logic whose box IS
"provable in T" — makes the mathematics of self-reference corpus subject
matter. ROADMAP-v0.5 item 10f. Six nodes: the K axiom, necessitation,
Löb's axiom, consistency as unprovability of falsum, the formalized second
incompleteness theorem (Löb at falsum), and Gödel's second incompleteness
theorem as the honest meta-level statement. Willard's boundary case is
deliberately an invariant, not a node — see "What was NOT authored" below.

Authoring stance: one head for the box, reused Boolean vocabulary
--------------------------------------------------------------------------

The provability modality is spelled `BOX(.)` everywhere, with the
provable-in-T reading carried by the lexicon (`functionals` descriptions),
not by a second head. PROVABLE was considered and rejected: two spellings
of one operator inside one corpus is exactly the head-vocabulary drift the
narrative structure trio measured (three same-shaped nodes, one hand, zero
twins). The Boolean fragments reuse scripts/seed_logic.py's IMPLIES and NEG
heads verbatim, for the same reason seed_temporal.py reused MEET/JOIN/NEG:
Boolean sub-structure inside a modal statement stays visible to the matcher.
The falsum constant slot is spelled FALSITY, the token
logic.boolean_laws.complement_laws already binds and HEAD_ALGEBRA already
lists as a MEET annihilator, so the arithmetized falsum and the Boolean
falsum land on one name.

What is deliberately ABSENT: a `BOX ~ ALWAYS` entry in HEAD_ALIASES. GL and
LTL share K and necessitation, so the temptation is real, but an alias is an
assertion that two heads name ONE operation family, and that assertion is
false here: LTL validates reflection (ALWAYS(p) -> p is valid), GL refuses
it (by Löb's theorem, T proves Bew(p) -> p only when T already proves p).
The two boxes differ in exactly the axiom that separates well-founded
induction from an interior operator. Per the HEAD_ALGEBRA discipline an
alias needs a justifying corpus citation, and the citable facts point the
other way — so the corpus accepts head-literal quarantine and REGISTERS the
price (PV2 below) instead of engineering it away.

Registered predictions BEFORE running scripts/match_signatures.py
------------------------------------------------------------------

P-CF4 (registered first in docs/DESIGN-cognitive-frames.md §4, before this
    file existed). **Löb vs temporal induction is an archetype-shared
    near-miss, NOT a typed twin.** Predicted skeletons:
      Löb        IMPLIES(BOX(IMPLIES(BOX(?0:V), ?0:V)), BOX(?0:V))
      induction  IMPLIES(ALWAYS(IMPLIES(?0:V, NEXT(?0:V))), IMPLIES(?0:V, ALWAYS(?0:V)))
    Two independent blockers, same two-blocker pattern seed_temporal.py's P1
    recorded for the modal De Morgan: (a) heads — BOX vs ALWAYS/NEXT, fatal
    at every level under head literalism; (b) shape — even under a
    hypothetical BOX~ALWAYS alias with NEXT erased the trees differ: Löb
    boxes its whole hypothesis and the hypothesis's own antecedent, while
    induction's conclusion is itself an implication. The shape difference IS
    the reflection difference: Löb's inner implication is reflection
    (BOX(p) -> p) guarded under a box, which GL grants only there; temporal
    induction lives in a logic where reflection holds outright. Channel
    prediction: `provability.modal.loeb_axiom` ADOPTS the existing
    `temporal_induction` archetype (justification in the node — Löb is
    induction along the converse well-founded accessibility relation;
    Segerberg completeness for finite transitive irreflexive frames), so
    the report's "Archetype ids spanning multiple structures" section gains
      temporal_induction: temporal.induction.temporal_induction_axiom,
                          provability.modal.loeb_axiom
    and NO twin group at shape/typed/family/aliased/mirror contains both
    nodes. The discipline-named label spanning a second discipline is
    itself evidence for docs/BACKLOG.md's drift-promotion proposal.
    VERDICT: see Adjudication below.

PV1. **The K axiom will be a singleton at every level, and the honest
    archetype is a mint, not an adoption.** Candidate neighbours:
    temporal.modality.next_distributes_over_meet
    (NEXT(MEET(?0,?1)) = MEET(NEXT(?0),NEXT(?1)), archetype
    modal_meet_homomorphism) and its PREV mirror. Two blockers again:
    heads (BOX vs NEXT/MEET), and root relation — K is an IMPLIES-rooted
    one-directional distribution, the temporal pair are equations. Adopting
    `modal_meet_homomorphism` would assert that a one-way distribution over
    implication is a two-way homomorphism onto meet — false, so the node
    mints `modal_distribution_axiom` and pays the singleton price. The LTL
    K-analog (ALWAYS distributing over implication) is ABSENT from the
    temporal corpus; the node records that corpus gap in its invariants,
    the same gap-shape temporal_induction recorded for missing arithmetic
    induction. VERDICT: see Adjudication below.

PV2. **The whole corpus buys zero twin groups: 215 -> 221 nodes with group
    counts unchanged at shape 30 / typed 31 / family 30 / aliased 32 /
    mirror 5, and zero ladder violations.** Every node introduces or
    depends on BOX, no alias is declared, BOX has no TIME_REVERSE entry,
    and no two of the six templates share a skeleton — so all six land as
    singletons at every level. This is the narrative-structure-trio
    quarantine price, predicted this time instead of discovered.
    Consistency-definition nearest miss registered explicitly: its skeleton
    `?0:P = NEG(BOX(?1:P))` is one BOX away from nothing in the graph — no
    other statement is rooted in a bare NEG equation or call over a single
    parameter-like slot. VERDICT: see Adjudication below.

PV3. **Groundedness splits on the box, with intra-corpus recurrence as the
    only channel for BOX-bearing constituents.** Extra-corpus grounding can
    flow only through BOX-free constituents — concretely K's inner
    IMPLIES(?0:V, ?1:V), which recurs graph-wide (modus ponens's detached
    implication among others). BOX-bearing constituents can ground only on
    THIS corpus's own recurrence (BOX(...) and NEG(BOX(...)) sub-forms
    recur across the consistency/incompleteness trio — in particular
    NEG(BOX(FALSITY)) is verbatim the expression side of
    provability.consistency.consistency_definition). Registered
    expectations: no provability node reaches 1.000; the corpus lands below
    the graph mean (0.764 at baseline); necessitation — whose only
    non-trivial constituent is BOX(PROP) — depends entirely on whether
    single-head box recurrence across sibling nodes counts, so it is the
    sharpest probe of whether "new discipline vocabulary is structurally
    quarantined" (docs/BACKLOG.md) applies within a corpus or only across
    corpora. VERDICT: see Adjudication below.

PV4. **specialize.py emits zero provability edges in either direction
    (655 stays 655), and the Löb -> formalized-Gödel-II edge exists only
    because it is hand-authored.** Three independent recorded filters each
    block the tool from finding that edge: (a) the non-`rel` root skip —
    five of the six templates are IMPLIES- or NEG-rooted calls, excluded
    from the general side outright (the 16-of-195 filter seed_temporal.py's
    P7 measured); (b) plain slot-to-subtree binding suppression — the
    instance is Löb with PROP := FALSITY; (c) a definitional rewrite no
    pass performs — NEG(x) := IMPLIES(x, FALSITY) turns the raw instance
    into the stated form. The one rel-rooted template
    (CONSISTENCY = NEG(BOX(FALSITY))) offers the arithmetic-noise mechanism
    nothing to bite on (no commutative op, no identity), consistent with
    temporal P10: call-head-only templates generate neither signal nor
    noise. VERDICT: see Adjudication below.

Adjudication (written after running the tools; skeletons quoted from the
matcher's own canonicalizer — singletons are not printed in the report body)
--------------------------------------------------------------------------

P-CF4  FIRED, both halves. No twin group at any level contains both nodes,
    and the report's drift section prints exactly the predicted entry:
      temporal_induction: provability.modal.loeb_axiom,
                          temporal.induction.temporal_induction_axiom
    Typed skeletons, computed with the matcher's canonicalize/skeleton:
      Löb        IMPLIES⟨BOX⟨IMPLIES⟨BOX⟨?0:V⟩, ?0:V⟩⟩, BOX⟨?0:V⟩⟩
      induction  IMPLIES⟨ALWAYS⟨IMPLIES⟨?0:V, NEXT⟨?0:V⟩⟩⟩, IMPLIES⟨?0:V, ALWAYS⟨?0:V⟩⟩⟩
    Both predicted blockers are real and independent: the heads differ at
    every modal position, and the trees differ below any renaming — Löb's
    conclusion is a bare boxed slot where induction's is an implication.
    The archetype channel now carries a discipline-named label across a
    second discipline, the strongest drift-promotion evidence the graph
    has: `temporal_induction` was named for its corpus and the name is now
    demonstrably too narrow for its extension (well-founded induction
    under a modality). Filed in docs/BACKLOG.md.

PV1  FIRED. k_distribution appears in no group at shape, typed, family,
    aliased or mirror level (report JSON checked; provability ids occur
    only in the drift entry and the slot/head-collision lint). Its typed
    skeleton
      IMPLIES⟨BOX⟨IMPLIES⟨?0:V, ?1:V⟩⟩, IMPLIES⟨BOX⟨?0:V⟩, BOX⟨?1:V⟩⟩⟩
    shares no group with
      NEXT⟨MEET⟨?0:V, ?1:V⟩⟩ = MEET⟨NEXT⟨?0:V⟩, NEXT⟨?1:V⟩⟩.
    The corpus gap stands: the graph still has no ALWAYS-distribution node
    for the LTL K axiom, so the cheapest future connectivity fix for this
    node is authoring temporal's K in the temporal corpus — recorded in
    the node's significance rather than forced from here (this seed must
    not edit seed_temporal.py).

PV2  FIRED exactly. 215 -> 221 nodes; shape 30 / typed 31 / family 30 /
    aliased 32 / mirror 5 unchanged; 0 ladder violations; parse_problems
    and slot_schema_gaps both empty; all six provability nodes absent
    from every group at every level. The quarantine price was paid
    knowingly and measured at zero group movement — the archetype channel
    (P-CF4) is the corpus's only cross-discipline connection, as designed.
    Unregistered finding from the same run: the slot/head name-collision
    lint gained an entry — `box: slot BOX vs head BOX⟨...⟩` — because
    narrative.world.marble_moved_box binds BOX as a constant slot (Sally-
    Anne's container) while this corpus uses BOX as its modal head. A
    lint, not a defect (slots and heads can never match each other), but
    the funniest possible witness that head vocabulary is global: Gödel's
    box and Sally's box now share a namespace. Left as-is deliberately —
    renaming the marble's container is seed_temporal.py's call, not ours.

PV3  MISSED on its headline expectations, and the miss is the seed's most
    useful result. Registered: no node reaches 1.000; corpus below the
    0.764 graph mean; extra-corpus grounding only through BOX-free
    constituents. Actual: **every provability node scores groundedness
    1.000**, the corpus decomposes 6/6 (graph: 187/215 -> 193/221), and
    the graph mean rose 0.764 -> 0.770 by dilution with perfect scores.
    Two mechanisms produced the inversion, both visible in the report:
    (a) Intra-corpus recurrence is unconditionally sufficient. BOX⟨?0:V⟩
        recurs across k/necessitation/Löb and BOX⟨?0:P⟩ across the falsum
        trio, so every box-rooted constituent grounds "exactly"; and
        NEG⟨BOX⟨?0:P⟩⟩ is verbatim the consistency definition's
        expression side (the one intra-corpus channel PV3 did predict).
    (b) The pattern channel absorbs the box entirely: Löb's reflection
        premise IMPLIES⟨BOX⟨?0:V⟩, ?0:V⟩ grounds as an instance of
        IMPLIES⟨?0:P, ?1:V⟩ "known from logic.inference.ex_falso_quodlibet"
        — a slot swallowing the boxed subtree, so a BOX-bearing
        constituent grounded extra-corpus after all, refuting the
        registered channel claim directly. (The one exact extra-corpus
        hit, K's inner IMPLIES⟨?0:V, ?1:V⟩, cites contraposition, not the
        modus-ponens premise the registration guessed.)
    The finding, stated for docs/BACKLOG.md: **groundedness has no notion
    of provenance, so a hermetic new corpus that reuses one new head
    densely self-grounds to 1.000.** Six mutually-referential nodes
    authored in one sitting now grade as perfectly grounded as three-
    corpus-old Boolean laws, while temporal's genuinely quarantined
    narrative heads sit at 0.000 — the score rewards vocabulary density,
    not vocabulary establishment. Together with the until_unfolding
    self-reference defect (correct axiom graded 0.000) the ladder's one
    graded rung has now been measured failing in BOTH directions.

PV4  FIRED. specialize.py: "Found 655 specialization edges
    (566 cross-discipline) among 221 nodes" — identical to the 215-node
    baseline; zero provability ids anywhere in its output. The
    hand-authored special_case_of/generalizes pair between loeb_axiom and
    formalized_second_incompleteness is therefore the corpus's only
    general->specific edge, and all three registered blockers stand.

What was NOT authored, and why
-------------------------------

- **Willard's self-verifying theories are an invariant, not a node.** Their
  honest content is existential — "there exist consistent r.e. theories
  proving their own consistency, obtained by weakening multiplication
  totality until the Hilbert-Bernays derivability conditions fail" — and
  the template grammar has no existential binder (the recorded quantifier
  gap). Any template would have had to assert BOX(CONSISTENCY) as a law,
  stripped of the side conditions that make it true, i.e. the corpus would
  state the negation of its own Gödel II node one line below it. The
  boundary case lives in second_incompleteness's invariants and failure
  modes, with Willard 2001 cited, which is what DESIGN-cognitive-frames §4
  asks the record to keep ("if you cannot author it honestly as a
  template, put it in an invariant note").
- **No LTL K axiom on temporal's behalf.** PV1's corpus gap is real, but
  this seed owns only data/provability; authoring temporal's K here would
  either edit seed_temporal.py (out of scope) or duplicate a statement
  into the wrong discipline.
- **No Lean `verified_by` yet.** prover/sample_triples.json carries no GL
  theorems; a false verified_by is worse than none. Löb is the discipline
  where a Lean anchor is most poetic (design §4), so the hook is left for
  the prover lane.

Authoring constraints observed (all from docs/BACKLOG.md / ADDING_FORMULAE)
---------------------------------------------------------------------------

- `statement_id` first segment forbids underscores: ids are
  `provability.*`, and here directory, discipline field and prefix agree.
- `constants` entries use {symbol, description} — never `name`.
- Every modal head lives in `functionals`; every node keeps at least one
  scalar `symbols` entry; `constantToken` keys are {symbol, description}.
- Call arguments are ORDERED; IMPLIES is antecedent-first everywhere, BOX
  is unary, and the corpus fixes no new binary head.
- All six inferential_links lists present; entails/entailed_by and
  special_case_of/generalizes pairs are reciprocal INSIDE this corpus.
  Cross-corpus relationships (temporal induction, modus ponens, complement
  laws, ex falso) use one-sided `composed_with` only — this seed does not
  edit other corpora's seeds.
- The meta/object double reading of IMPLIES (a rule vs a formula) is
  inherited from scripts/seed_logic.py and documented at every use;
  necessitation is the extreme case and says so in its invariants.
- Run the matcher with PYTHONIOENCODING=utf-8 on Windows.
"""

from __future__ import annotations

import json
from pathlib import Path


# --------------------------------------------------------------------------
# Builders (same shape as scripts/seed_temporal.py / seed_morphology.py)
# --------------------------------------------------------------------------


def sym(s, cat, role, desc, order=0):
    return {"symbol": s, "syntactic_category": cat, "semantic_role": role,
            "mathematical_order": order, "description": desc}


def op(symbol, name, arity=2, family="logical"):
    return {"symbol": symbol, "name": name, "arity": arity,
            "operator_family": family}


def slot(sid, cat, role):
    return {"slot_id": sid, "syntactic_category": cat, "semantic_role": role}


def links(entailed_by=None, entails=None, equivalent_to=None,
          special_case_of=None, generalizes=None, composed_with=None):
    return {"entailed_by": entailed_by or [], "entails": entails or [],
            "equivalent_to": equivalent_to or [],
            "special_case_of": special_case_of or [],
            "generalizes": generalizes or [],
            "composed_with": composed_with or []}


def node(sid, title, cls, status, subfield, topic, ascii_, latex, forms,
         archetype, template, slots, invariants, symbols, operators,
         meaning, significance, conditions, provenance, disciplines,
         functionals=None, constants=None, index_sets=None, failure_modes=None,
         inferential_links=None, keywords=None, canonical_objects=None):
    context = {"disciplines": disciplines, "subfield": subfield, "topic": topic}
    context["canonical_objects"] = CANONICAL_OBJECTS
    interpretation = {"statement_meaning": meaning,
                      "statistical_significance": significance,
                      "regularity_conditions": conditions}
    if failure_modes:
        interpretation["failure_modes"] = failure_modes
    out = {
        "statement_id": sid, "title": title, "statement_class": cls,
        "epistemic_status": status,
        "theory_context": context,
        "formal_statement": {"canonical_ascii": ascii_, "canonical_latex": latex,
                             "equivalent_forms": forms},
        "structural_signature": {"archetype_id": archetype,
                                 "anonymized_template": template,
                                 "slot_schema": slots, "invariants": invariants},
        "symbol_lexicon": {"symbols": symbols, "operators": operators,
                           "functionals": functionals or [],
                           "index_sets": index_sets or [],
                           "constants": constants or []},
        "semantic_interpretation": interpretation,
        "inferential_links": inferential_links or links(),
        "provenance": provenance,
    }
    if keywords:
        out["keywords"] = keywords
    return out


# --------------------------------------------------------------------------
# Lexicon fragments
# --------------------------------------------------------------------------

EQ = op("=", "definitional equality of arithmetic sentences", 2, "relational")
IMPL = op("implies", "material implication / meta-level inference", 2,
          "logical")
NOT = op("not", "negation", 1, "logical")
BOX_OP = op("[]", "provability modality (arithmetized Bew_T)", 1, "logical")
TSTILE = op("|-", "derivability in the theory T", 2, "logical")

BOX_FN = {
    "notation": "BOX(.)", "name": "provability modality", "input_arity": 1,
    "codomain": "arithmetic sentences",
    "description": "Goedel's arithmetized provability predicate read as a "
                   "modal operator: BOX(p) is the sentence Bew_T([p]) saying "
                   "'the theory T proves p'. The ONE spelling of the box in "
                   "this corpus; PROVABLE was rejected as a second name for "
                   "the same head. Deliberately NOT spelled ALWAYS, and no "
                   "HEAD_ALIASES entry relates the two: GL and LTL share K "
                   "and necessitation, but LTL validates reflection "
                   "(ALWAYS(p) -> p) while Loeb's theorem makes reflection "
                   "provable in GL only for theorems. An alias asserts one "
                   "operation family, and that assertion would be false in "
                   "exactly the axiom that matters. The head-literal "
                   "quarantine this costs is registered (PV2) and measured."}
IMPLIES_FN = {
    "notation": "IMPLIES(.,.)", "name": "implication", "input_arity": 2,
    "description": "Material implication where the statement is an "
                   "object-language formula under the box, and the "
                   "meta-level 'if ... then' where the statement is a rule "
                   "or a metatheorem. Same head and same documented double "
                   "reading as scripts/seed_logic.py and seed_temporal.py; "
                   "the necessitation node is the extreme case of the "
                   "ambiguity and records it in its invariants."}
NEG_FN = {
    "notation": "NEG(.)", "name": "negation", "input_arity": 1,
    "description": "Boolean negation, reused verbatim from "
                   "scripts/seed_logic.py. Definitionally NEG(x) = "
                   "IMPLIES(x, FALSITY), the rewrite that turns Loeb's "
                   "axiom at falsum into the formalized second "
                   "incompleteness theorem — a rewrite no matcher pass "
                   "performs, which is one of the three recorded reasons "
                   "the Loeb->Goedel-II edge must be hand-authored."}

FALSUM_CONST = {
    "symbol": "bottom",
    "description": "The refutable sentence 0=1 (falsum). Spelled FALSITY in "
                   "slot schemas — the same token "
                   "logic.boolean_laws.complement_laws binds and "
                   "HEAD_ALGEBRA lists as a MEET annihilator — so the "
                   "Boolean falsum and the arithmetized falsum land on one "
                   "name."}
CON_CONST = {
    "symbol": "Con(T)",
    "description": "The arithmetized consistency statement of T: the "
                   "sentence NEG(BOX(FALSITY)). A constant of the corpus "
                   "because T is fixed throughout; intensionality (which "
                   "proof predicate arithmetizes 'proves') is recorded in "
                   "the defining node's invariants, after Feferman 1960."}

SENT_SYMS = [
    sym("p", "variable", "arithmetic_sentence",
        "An arbitrary sentence of the language of T, closed under the "
        "arithmetization that gives every sentence a numeral name."),
    sym("q", "variable", "arithmetic_sentence",
        "A second arbitrary sentence, independent of p."),
]

CANONICAL_OBJECTS = ["recursively enumerable theory", "arithmetized proof "
                     "predicate", "arithmetic sentence", "GL Kripke frame "
                     "(finite, transitive, irreflexive)"]

# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------

GODEL1931 = {"citation_key": "goedel1931",
             "bibliographic_entry": "Goedel, K. (1931). Ueber formal unentscheidbare Saetze der Principia Mathematica und verwandter Systeme I. Monatshefte fuer Mathematik und Physik, 38, 173-198."}
LOEB1955 = {"citation_key": "loeb1955",
            "bibliographic_entry": "Loeb, M. H. (1955). Solution of a Problem of Leon Henkin. Journal of Symbolic Logic, 20(2), 115-118."}
HENKIN1952 = {"citation_key": "henkin1952",
              "bibliographic_entry": "Henkin, L. (1952). A Problem Concerning Provability (problem 3). Journal of Symbolic Logic, 17(2), 160."}
HILBERTBERNAYS1939 = {"citation_key": "hilbert_bernays1939",
                      "bibliographic_entry": "Hilbert, D., Bernays, P. (1939). Grundlagen der Mathematik, Band II. Berlin: Springer."}
SEGERBERG1971 = {"citation_key": "segerberg1971",
                 "bibliographic_entry": "Segerberg, K. (1971). An Essay in Classical Modal Logic. Filosofiska Studier 13. Uppsala: University of Uppsala."}
SOLOVAY1976 = {"citation_key": "solovay1976",
               "bibliographic_entry": "Solovay, R. M. (1976). Provability Interpretations of Modal Logic. Israel Journal of Mathematics, 25, 287-304."}
BOOLOS1993 = {"citation_key": "boolos1993",
              "bibliographic_entry": "Boolos, G. (1993). The Logic of Provability. Cambridge: Cambridge University Press."}
SMORYNSKI1985 = {"citation_key": "smorynski1985",
                 "bibliographic_entry": "Smorynski, C. (1985). Self-Reference and Modal Logic. New York: Springer."}
FEFERMAN1960 = {"citation_key": "feferman1960",
                "bibliographic_entry": "Feferman, S. (1960). Arithmetization of Metamathematics in a General Setting. Fundamenta Mathematicae, 49, 35-92."}
ROSSER1936 = {"citation_key": "rosser1936",
              "bibliographic_entry": "Rosser, J. B. (1936). Extensions of Some Theorems of Goedel and Church. Journal of Symbolic Logic, 1(3), 87-91."}
WILLARD2001 = {"citation_key": "willard2001",
               "bibliographic_entry": "Willard, D. E. (2001). Self-Verifying Axiom Systems, the Incompleteness Theorem and Related Reflection Principles. Journal of Symbolic Logic, 66(2), 536-596."}


# --------------------------------------------------------------------------
# Provability corpus
# --------------------------------------------------------------------------

PROVABILITY_NODES = [

    node("provability.modal.k_distribution",
         "Distribution Axiom (K) for Provability",
         "axiom", "formal", "provability_logic", "modal_distribution",
         "provable(p implies q) implies (provable(p) implies provable(q))",
         "\\Box(p \\to q) \\to (\\Box p \\to \\Box q)",
         [{"form_id": "unicode", "notation_system": "ascii",
           "expression": "□(p→q) → (□p→□q)",
           "scope_note": "Modal-logic notation; K is what makes a modality normal"},
          {"form_id": "derivability_condition", "notation_system": "ascii",
           "expression": "Bew([p implies q]) implies (Bew([p]) implies Bew([q]))",
           "scope_note": "The second Hilbert-Bernays-Loeb derivability condition D2: T's theorems are provably closed under modus ponens"},
          {"form_id": "rule", "notation_system": "ascii",
           "expression": "from |- box(p implies q) and |- box(p), infer |- box(q)",
           "scope_note": "The detached reading; K internalizes modus ponens one box down"}],
         "modal_distribution_axiom",
         "IMPLIES(BOX(IMPLIES(PROPP, PROPQ)), IMPLIES(BOX(PROPP), BOX(PROPQ)))",
         [slot("PROPP", "variable", "arithmetic_sentence"),
          slot("PROPQ", "variable", "arithmetic_sentence")],
         ["K is the axiom that makes BOX a normal modality; every normal "
          "modal logic — including LTL under its ALWAYS reading — carries "
          "it verbatim. The temporal corpus has no ALWAYS-distribution "
          "node, so the obvious cross-discipline twin for this statement "
          "is a corpus gap, not a matcher miss: the same gap-shape "
          "temporal.induction.temporal_induction_axiom records for the "
          "absent arithmetic-induction node.",
          "One-directional: K distributes the box over an implication and "
          "never collects it back. That is why the archetype is a minted "
          "`modal_distribution_axiom` rather than an adoption of "
          "temporal's `modal_meet_homomorphism`, which asserts a two-sided "
          "equation onto MEET (PV1's honesty boundary).",
          "Under the arithmetic reading this is derivability condition D2, "
          "one of the three conditions Goedel II needs; D1 is the "
          "necessitation node and D3 the formalized-necessitation form on "
          "that node. The corpus therefore carries the Hilbert-Bernays "
          "conditions as statements, not as prose.",
          "Head literalism quarantines BOX from ALWAYS at every match "
          "level by design; the refused alias is argued in the BOX "
          "functional's description and its price is registered as PV2."],
         SENT_SYMS, [IMPL, BOX_OP, TSTILE],
         "If the theory proves an implication, then provability of the "
         "antecedent yields provability of the consequent: proof search "
         "composes across modus ponens, and the box records that fact "
         "inside the object language.",
         "The distribution axiom is half of what 'provable' shares with "
         "every other necessity-like operator; the corpus states it so "
         "that the SHARED half of GL and LTL is a statement in the graph "
         "rather than folklore, while the UNSHARED half (Loeb vs "
         "reflection) is carried by the adjacent axiom. Registered "
         "prediction PV1: singleton at every level, with the LTL K-analog "
         "recorded as the graph's missing counterpart — the cheapest "
         "future connectivity fix is authoring ALWAYS-distribution in the "
         "temporal corpus, not respelling this node.",
         ["T is recursively enumerable and interprets enough arithmetic "
          "to arithmetize its own proof relation",
          "BOX is the standard Goedel proof predicate for T (Feferman "
          "intensionality: a deviant predicate can break the conditions)",
          "Classical object logic"],
         [HILBERTBERNAYS1939, LOEB1955, SEGERBERG1971, BOOLOS1993],
         ["provability"],
         functionals=[BOX_FN, IMPLIES_FN],
         failure_modes=[
             "Fails for Rosser-style provability predicates: Rosser's "
             "ordered proof search is not provably closed under modus "
             "ponens, so D2 breaks — which is exactly why Rosser "
             "consistency escapes Goedel II and why 'which predicate' is "
             "part of the theorem's hypotheses.",
             "Fails for resource-bounded provability ('provable in at "
             "most n steps'): combining two short proofs can exceed the "
             "bound, so the boxed closure is lost.",
             "Fails for Willard's self-verifying systems at the "
             "arithmetization stage: without total multiplication the "
             "standard coding of proof sequences is unavailable, and K "
             "for the standard predicate is not internally derivable."],
         inferential_links=links(
             composed_with=["provability.modal.necessitation",
                            "provability.modal.loeb_axiom",
                            "logic.inference.modus_ponens",
                            "temporal.modality.next_distributes_over_meet"]),
         keywords=["distribution axiom", "normal modal logic", "K axiom",
                   "derivability conditions", "provability logic"]),

    node("provability.modal.necessitation",
         "Necessitation for Provability",
         "axiom", "formal", "provability_logic", "necessitation",
         "from |- p, infer |- provable(p)",
         "\\dfrac{\\vdash p}{\\vdash \\Box p}",
         [{"form_id": "derivability_condition", "notation_system": "ascii",
           "expression": "if T |- p then T |- Bew([p])",
           "scope_note": "The first Hilbert-Bernays-Loeb derivability condition D1: every theorem is provably a theorem"},
          {"form_id": "formalized", "notation_system": "ascii",
           "expression": "provable(p) implies provable(provable(p))",
           "scope_note": "Derivability condition D3 / modal axiom 4, the FORMALIZED necessitation; in GL it is derivable from K and Loeb rather than postulated, so this corpus carries it as a form of the rule it internalizes, not as a seventh node"}],
         "theoremhood_internalization",
         "IMPLIES(PROP, BOX(PROP))",
         [slot("PROP", "variable", "arithmetic_sentence")],
         ["The root IMPLIES is META-LEVEL: the template is a rule (from a "
          "proof of p, a proof of box p), the same double reading "
          "scripts/seed_logic.py documents for modus ponens and "
          "seed_temporal.py for temporal induction. This node is the "
          "extreme case of that inherited ambiguity, because the "
          "OBJECT-level reading of the same template — truth implies "
          "provability, the converse of reflection — is FALSE for every "
          "consistent T (there are true unprovable sentences; that is "
          "Goedel I). The matcher cannot tell the two readings apart and "
          "would group this rule with a formula of the same shape; no "
          "such formula exists in the graph today, and this invariant is "
          "the tripwire for the day one arrives.",
          "Necessitation applies to THEOREMS only, never under open "
          "assumptions: the deduction theorem does not commute with the "
          "box, which is the standard error the rule form guards against.",
          "With K, necessitation is what 'normal modal logic' means; GL "
          "is K + Loeb + necessitation, and both shared components are "
          "now graph statements."],
         SENT_SYMS[:1], [IMPL, BOX_OP, TSTILE],
         "Whatever the theory actually proves, it also proves that it "
         "proves: theoremhood is verifiable by exhibiting the proof, and "
         "the proof predicate is strong enough to check exhibited proofs.",
         "D1 of the derivability conditions, and the second half of the "
         "GL/LTL shared core. Structurally a predicted singleton: "
         "IMPLIES(?0:V, BOX(?0:V)) has no counterpart shape in the graph "
         "(PV2). Its decompose behaviour was PV3's sharpest probe: the "
         "node's only non-trivial constituent is BOX(PROP) itself, so its "
         "groundedness measures whether sibling-node box recurrence "
         "counts as a known form. Adjudicated: it does, unconditionally — "
         "the node scores 1.000 on box recurrence alone, the cleanest "
         "single exhibit of the self-grounding finding in the docstring.",
         ["p ranges over sentences actually derivable in T (the rule has "
          "a proof of p as its premise, not the truth of p)",
          "The proof predicate is Sigma-1: exhibited proofs are provably "
          "proofs, which is what makes D1 hold",
          "T recursively enumerable"],
         [HILBERTBERNAYS1939, LOEB1955, BOOLOS1993, SMORYNSKI1985],
         ["provability"],
         functionals=[BOX_FN, IMPLIES_FN],
         failure_modes=[
             "Read object-level it is false outright: truth does not "
             "imply provability in any consistent T extending arithmetic "
             "(Goedel I); the meta reading is load-bearing, not a "
             "nicety.",
             "Fails under open assumptions: from p |- q one may NOT "
             "infer p |- box(q); necessitation and the deduction theorem "
             "do not commute.",
             "Fails for provability-in-a-weaker-theory read into a "
             "stronger box or vice versa: D1 is a property of ONE fixed "
             "predicate for ONE fixed T."],
         inferential_links=links(
             composed_with=["provability.modal.k_distribution",
                            "provability.modal.loeb_axiom",
                            "logic.inference.modus_ponens"]),
         keywords=["necessitation", "derivability condition", "D1",
                   "normal modal logic", "rule vs formula"]),

    node("provability.modal.loeb_axiom",
         "Loeb's Axiom (GL)",
         "axiom", "formal", "provability_logic", "loeb_induction",
         "provable(provable(p) implies p) implies provable(p)",
         "\\Box(\\Box p \\to p) \\to \\Box p",
         [{"form_id": "unicode", "notation_system": "ascii",
           "expression": "□(□p→p) → □p",
           "scope_note": "The axiom that turns K4 into GL"},
          {"form_id": "rule", "notation_system": "ascii",
           "expression": "from |- provable(p) implies p, infer |- p",
           "scope_note": "Loeb's theorem as a rule over T: reflection is provable only for theorems. Loeb 1955's answer to Henkin's 1952 question about the sentence asserting its own provability"},
          {"form_id": "wellfounded_induction", "notation_system": "ascii",
           "expression": "valid on a transitive frame iff the accessibility relation is converse well-founded",
           "scope_note": "Segerberg completeness: GL is the logic of finite, transitive, irreflexive frames, so Loeb IS induction along the accessibility relation"},
          {"form_id": "arithmetic_completeness", "notation_system": "ascii",
           "expression": "GL proves exactly the schemata PA proves under every arithmetic realization of the box",
           "scope_note": "Solovay 1976; the reason this modal axiom is a fact about arithmetic rather than a stipulation"}],
         "temporal_induction",
         "IMPLIES(BOX(IMPLIES(BOX(PROP), PROP)), BOX(PROP))",
         [slot("PROP", "variable", "arithmetic_sentence")],
         ["The archetype_id `temporal_induction` is ADOPTED from "
          "temporal.induction.temporal_induction_axiom on purpose, and the "
          "adoption is a claim, not a convenience: Loeb's axiom is "
          "well-founded induction along the accessibility relation "
          "(Segerberg: valid on transitive frames exactly when no infinite "
          "ascending chain exists), and temporal induction is the same "
          "principle along NEXT/successor. Nested implication under a "
          "modality internalizing induction — one archetype, two "
          "disciplines. The label being named for ONE of them is recorded "
          "drift evidence for docs/BACKLOG.md's rename/promotion proposal, "
          "exactly as `de_morgan_duality` spanning three skeletons was.",
          "What the archetype shares, the skeletons refuse: Loeb boxes its "
          "whole hypothesis AND the hypothesis's own antecedent, and its "
          "conclusion is a bare boxed slot; temporal induction's "
          "conclusion is itself an implication and its step is unboxed on "
          "the antecedent side. The difference is reflection. LTL "
          "validates ALWAYS(p) -> p; in GL, reflection appears exactly "
          "once, INSIDE the box, as the hypothesis being discharged — "
          "P-CF4's registered near-miss, adjudicated in this file's "
          "docstring.",
          "One free operand occurring three times at three depths, the "
          "same recurrence-is-the-content pattern the induction and "
          "transitivity families carry.",
          "Adding reflection to GL as an axiom collapses it: "
          "box(p) -> p for all p plus Loeb yields |- p for all p by "
          "modus ponens inside the box. The axiom and reflection are "
          "not merely different, they are incompatible company.",
          "With p := FALSITY and the definitional rewrite NEG(x) = "
          "IMPLIES(x, FALSITY), this axiom yields the formalized second "
          "incompleteness theorem — the hand-authored "
          "generalizes/special_case_of pair, blocked from mechanical "
          "discovery by three independent recorded filters (PV4)."],
         SENT_SYMS[:1], [IMPL, BOX_OP, TSTILE],
         "If the theory proves that provability of p would already settle "
         "p, then the theory proves p outright: provability admits no "
         "useful self-trust below actual proof. Soundness-about-itself is "
         "purchasable only at the price of the theorem itself.",
         "The axiom that separates provability from every reflection-"
         "validating necessity, and the corpus's cross-discipline hinge: "
         "P-CF4 predicts (and this file adjudicates) that it shares an "
         "archetype with temporal induction while twinning nothing at any "
         "structural level. GL's completeness for PA (Solovay) makes it "
         "the discipline where a future Lean verified_by anchor is most "
         "wanted; none is claimed yet because prover/ carries no GL "
         "artifact.",
         ["T recursively enumerable, interpreting enough arithmetic for "
          "the diagonal lemma (the proof of Loeb's theorem runs through "
          "the fixed point of 'if this sentence is provable then p')",
          "BOX satisfies the Hilbert-Bernays-Loeb conditions D1-D3",
          "Classical object logic"],
         [LOEB1955, HENKIN1952, SEGERBERG1971, SOLOVAY1976, BOOLOS1993],
         ["provability"],
         functionals=[BOX_FN, IMPLIES_FN],
         failure_modes=[
             "Fails read as truth: if the box were a truth predicate, "
             "Loeb plus the tautology box(p) -> p would prove every p — "
             "the modal shadow of the liar/Curry collapse, and the "
             "sharpest reason box-as-provable and box-as-true must never "
             "alias.",
             "Fails for Rosser provability: the diagonal argument needs "
             "D1-D3, and Rosser's predicate breaks D2, so Loeb's theorem "
             "does not transfer.",
             "Fails on non-transitive or non-well-founded frames: over "
             "reflexive frames (S4, where reflection holds) the axiom is "
             "simply false; well-foundedness of the frame is not a "
             "convenience but the semantic content of the axiom."],
         inferential_links=links(
             generalizes=[
                 "provability.incompleteness.formalized_second_incompleteness"],
             composed_with=["provability.modal.k_distribution",
                            "provability.modal.necessitation",
                            "provability.consistency.consistency_definition",
                            "temporal.induction.temporal_induction_axiom"]),
         keywords=["Loeb's axiom", "GL", "well-founded induction",
                   "reflection", "Henkin's problem", "provability logic"]),

    node("provability.consistency.consistency_definition",
         "Consistency as Unprovability of Falsum",
         "definition", "formal", "arithmetization", "consistency",
         "Con(T) := not(provable(falsum))",
         "\\mathrm{Con}(T) :\\equiv \\lnot\\,\\Box\\bot",
         [{"form_id": "no_contradiction", "notation_system": "ascii",
           "expression": "Con(T) iff for no p are both p and not(p) provable",
           "scope_note": "Equivalent under D2 plus ex falso quodlibet: from a contradiction the falsum is provable, and from falsum everything"},
          {"form_id": "something_unprovable", "notation_system": "ascii",
           "expression": "Con(T) iff there exists a sentence T does not prove",
           "scope_note": "The Post-consistency reading; equivalent classically because an inconsistent theory proves everything. Existential, hence prose: the grammar has no binder"},
          {"form_id": "arithmetized", "notation_system": "ascii",
           "expression": "Con(T) is itself a sentence of T's language, via Goedel numbering",
           "scope_note": "The move that makes Goedel II expressible at all: consistency becomes a statement the theory can be asked about"}],
         "unprovability_of_falsum",
         "CONSISTENCY = NEG(BOX(FALSITY))",
         [slot("CONSISTENCY", "constant", "consistency_statement"),
          slot("FALSITY", "constant", "refutable_sentence")],
         ["FALSITY is deliberately the SAME constant token "
          "logic.boolean_laws.complement_laws binds as its result and "
          "HEAD_ALGEBRA lists as a MEET annihilator; the arithmetized "
          "falsum and the Boolean falsum are one name in the graph. The "
          "node is nevertheless a predicted singleton (PV2): shared "
          "constants feed specialize.py's identity machinery, not the twin "
          "ladder, so one NEG and one BOX around a shared token buy no "
          "group membership — the registered nearest-miss measurement.",
          "Intensionality (Feferman 1960): Con(T) depends on WHICH proof "
          "predicate is arithmetized, not only on the set of theorems. A "
          "Rosser-style predicate yields a different Con(T) that T CAN "
          "prove; every downstream node in this corpus inherits this "
          "hypothesis from here, where the definition lives.",
          "Definitional equality, not a discovered identity: the `=` is "
          "the corpus's one rel-rooted provability template, and PV4 "
          "predicts (correctly) that specialize.py finds nothing in it — "
          "no commutative arithmetic op, nothing for the noise mechanism "
          "to bite."],
         [sym("Con(T)", "constant", "consistency_statement",
              "The arithmetized consistency sentence being defined."),
          sym("bottom", "constant", "refutable_sentence",
              "Falsum: the canonical refutable sentence 0=1.")],
         [EQ, NOT, BOX_OP],
         "A theory is consistent exactly when it cannot prove the absurd "
         "sentence; arithmetization turns that meta-level property into a "
         "single sentence of the theory's own language.",
         "The definitional hinge of the corpus: both incompleteness nodes "
         "consume this constant, and the formalized one contains this "
         "node's entire expression side as a subterm — the one "
         "intra-corpus grounding channel PV3 predicted correctly, inside "
         "an adjudication PV3 otherwise missed (the corpus self-grounds "
         "to 1.000 throughout; see the docstring).",
         ["Goedel numbering fixed; Con(T) is standard, built from the "
          "standard proof predicate",
          "Classical logic (ex falso quodlibet), so falsum-unprovability "
          "and no-contradiction coincide",
          "T recursively enumerable"],
         [GODEL1931, HILBERTBERNAYS1939, FEFERMAN1960, BOOLOS1993],
         ["provability"],
         functionals=[BOX_FN, NEG_FN],
         constants=[CON_CONST, FALSUM_CONST],
         failure_modes=[
             "Intensional failure: Feferman's deviant consistency "
             "predicates are provable or refutable at will while the "
             "theorem set stays fixed; 'Con(T)' without naming the "
             "predicate is not yet a sentence.",
             "In paraconsistent logics unprovability-of-falsum and "
             "absence-of-contradiction come apart; the definition is "
             "classical.",
             "For theories too weak to arithmetize syntax (or Willard's "
             "self-verifying systems, which weaken multiplication "
             "totality precisely to dodge the standard coding), the "
             "definition's premise — that Con(T) is a sentence OF T — "
             "needs a different, weaker coding, and the downstream "
             "incompleteness machinery changes with it."],
         inferential_links=links(
             composed_with=[
                 "provability.incompleteness.formalized_second_incompleteness",
                 "provability.incompleteness.second_incompleteness",
                 "logic.boolean_laws.complement_laws",
                 "logic.inference.ex_falso_quodlibet"]),
         keywords=["consistency", "Con(T)", "arithmetization", "falsum",
                   "intensionality"]),

    node("provability.incompleteness.formalized_second_incompleteness",
         "Formalized Second Incompleteness (Loeb at Falsum)",
         "theorem", "derived", "incompleteness", "second_incompleteness",
         "provable(not(provable(falsum))) implies provable(falsum)",
         "\\Box\\lnot\\Box\\bot \\to \\Box\\bot",
         [{"form_id": "con_spelling", "notation_system": "ascii",
           "expression": "provable(Con(T)) implies provable(falsum)",
           "scope_note": "The same statement through the consistency definition: if T proves its own consistency, T is inconsistent"},
          {"form_id": "loeb_instance", "notation_system": "ascii",
           "expression": "provable(provable(falsum) implies falsum) implies provable(falsum)",
           "scope_note": "Loeb's axiom with p := falsum, before the definitional rewrite NEG(x) = IMPLIES(x, FALSITY); the substitution plus that one rewrite is the whole derivation"},
          {"form_id": "contrapositive", "notation_system": "ascii",
           "expression": "not(provable(falsum)) implies not(provable(not(provable(falsum))))",
           "scope_note": "Con(T) implies not provable(Con(T)) — the shape Goedel II takes one node later, still entirely inside GL"}],
         "formalized_incompleteness",
         "IMPLIES(BOX(NEG(BOX(FALSITY))), BOX(FALSITY))",
         [slot("FALSITY", "constant", "refutable_sentence")],
         ["Derived, in one visible step, from Loeb's axiom: substitute "
          "FALSITY for the free slot and rewrite IMPLIES(x, FALSITY) as "
          "NEG(x). The special_case_of edge to the Loeb node is "
          "hand-authored because each of three recorded tool filters "
          "blocks mechanical discovery: specialize.py skips non-rel-rooted "
          "generals (both templates are IMPLIES calls), suppresses plain "
          "slot bindings (PROP -> FALSITY is one), and performs no "
          "definitional NEG rewrite at all. PV4 registers this and the "
          "matcher run confirms zero mechanical provability edges.",
          "The node's antecedent BOX(NEG(BOX(FALSITY))) contains, "
          "verbatim, the consistency definition's entire expression side "
          "NEG(BOX(FALSITY)) — definitional compression is recorded via "
          "composed_with rather than inline expansion, so the graph keeps "
          "one spelling of Con(T).",
          "Entirely object-level: unlike Goedel II one node later, no "
          "connective here is meta — both boxes and the implication are "
          "sentences of T, which is why this form is derivable inside GL "
          "with no consistency hypothesis at all.",
          "Read positively rather than as a limitation: self-certified "
          "consistency is worthless, because producing the certificate "
          "is the one act that would refute it. This is the corpus-level "
          "statement of the external-trust-roots rule, and "
          "DESIGN-cognitive-frames §4 records the architectural "
          "principle it grounds."],
         [sym("bottom", "constant", "refutable_sentence",
              "Falsum, the instantiated slot: the entire theorem is "
              "Loeb's axiom pinned to the worst-case sentence.")],
         [IMPL, NOT, BOX_OP],
         "If the theory proves its own consistency sentence, then the "
         "theory proves falsum: a consistency certificate issued by the "
         "certified party is self-defeating.",
         "The GL-internal form of Goedel II and the corpus's one "
         "general->specific edge, deliberately hand-authored (PV4). Its "
         "decompose readout carries PV3's one correct channel — the "
         "NEG(BOX(FALSITY)) constituent grounds verbatim on the "
         "consistency definition's expression side — inside PV3's "
         "headline miss: the whole corpus self-grounds to 1.000, because "
         "groundedness counts recurrence without provenance. A new "
         "head's vocabulary can certify itself within one authoring act; "
         "the docstring adjudication and docs/BACKLOG.md carry the "
         "finding.",
         ["Derivable in GL from K, necessitation and Loeb alone; no "
          "assumption about T's actual consistency is used",
          "Transfers to T through Solovay's arithmetic completeness: "
          "every arithmetic realization of the schema is a theorem of PA",
          "Standard proof predicate throughout (intensionality inherited "
          "from the consistency definition)"],
         [LOEB1955, GODEL1931, SOLOVAY1976, BOOLOS1993, SMORYNSKI1985],
         ["provability"],
         functionals=[BOX_FN, IMPLIES_FN, NEG_FN],
         constants=[FALSUM_CONST],
         failure_modes=[
             "Everything the Loeb node lists, instantiated: Rosser "
             "predicates, truth-reading of the box, non-well-founded "
             "frames.",
             "The con_spelling form silently assumes the STANDARD Con(T); "
             "for a deviant consistency sentence the implication can fail "
             "while this node's falsum spelling still holds for the "
             "standard predicate."],
         inferential_links=links(
             special_case_of=["provability.modal.loeb_axiom"],
             entails=["provability.incompleteness.second_incompleteness"],
             composed_with=[
                 "provability.consistency.consistency_definition"]),
         keywords=["second incompleteness", "formalized", "Loeb's theorem",
                   "self-certification", "GL theorem"]),

    node("provability.incompleteness.second_incompleteness",
         "Goedel's Second Incompleteness Theorem",
         "theorem", "derived", "incompleteness", "second_incompleteness",
         "assuming Con(T): not(provable(Con(T)))",
         "\\mathrm{Con}(T) \\;\\Longrightarrow\\; T \\nvdash \\mathrm{Con}(T)",
         [{"form_id": "expanded", "notation_system": "ascii",
           "expression": "not(provable(not(provable(falsum))))",
           "scope_note": "Con(T) expanded per the consistency definition; the template keeps the defined constant instead"},
          {"form_id": "original", "notation_system": "ascii",
           "expression": "in any consistent formal system containing enough arithmetic, the consistency of the system is not provable in the system",
           "scope_note": "Goedel 1931, Theorem XI, modern hypotheses (r.e., derivability conditions)"},
          {"form_id": "hilbert_program", "notation_system": "ascii",
           "expression": "no finitary fragment of mathematics can certify the whole",
           "scope_note": "The reading that ended Hilbert's program in its original form: the certifying theory always needs strictly more than the certified one"}],
         "unprovable_self_consistency",
         "NEG(BOX(CONSISTENCY))",
         [slot("CONSISTENCY", "constant", "consistency_statement")],
         ["TEMPLATE CHOICE, documented as required: the honest statement "
          "is meta-level — the outer NEG is the METATHEORY's 'T does not "
          "prove', while BOX and everything under it is object-level. Two "
          "authorings were considered. (a) "
          "IMPLIES(CONSISTENCY, NEG(BOX(CONSISTENCY))) puts the "
          "consistency hypothesis into the template, but stacks a second "
          "meta-level connective and manufactures an implication shape "
          "whose antecedent is not an object sentence of the graph's "
          "grammar in the same sense as its consequent. (b) The bare "
          "NEG(BOX(CONSISTENCY)) with the hypothesis in "
          "regularity_conditions — CHOSEN, following the two standing "
          "precedents: narrative.frame.frame_consistency keeps 'within a "
          "frame' in prose because the grammar has no scope construct, "
          "and temporal induction's root IMPLIES carries a documented "
          "meta reading. Exactly one operator here is meta (the outer "
          "NEG), and this invariant is the record of where the "
          "object/meta seam runs.",
          "The unprovable sentence is the consistency definition's "
          "definiendum: expanding CONSISTENCY would give "
          "NEG(BOX(NEG(BOX(FALSITY)))) — one NEG away from the "
          "formalized node's antecedent. The template keeps the defined "
          "constant so the graph carries one spelling of Con(T) and the "
          "compression stays visible in composed_with.",
          "WILLARD BOUNDARY (deliberately an invariant, not a node): "
          "self-verifying theories (Willard 2001) prove their own "
          "consistency by weakening multiplication totality until the "
          "Hilbert-Bernays derivability conditions fail for the standard "
          "coding; 'contains enough arithmetic' is load-bearing, not "
          "decorative. Not authored as a template because its honest "
          "content is existential over a family of theories and the "
          "grammar has no existential binder (the recorded quantifier "
          "gap); a forced template would assert BOX(CONSISTENCY) as a "
          "law, stripped of the side conditions — the negation of this "
          "very node, one line below it.",
          "The consistency HYPOTHESIS is not removable: an inconsistent "
          "T proves everything, including Con(T). What survives without "
          "the hypothesis is the formalized node, which is why the "
          "entailed_by edge points there and why the two are distinct "
          "statements rather than spellings of one."],
         [sym("Con(T)", "constant", "consistency_statement",
              "The standard arithmetized consistency sentence, defined "
              "one node earlier.")],
         [NOT, BOX_OP, TSTILE],
         "A consistent theory that can talk about its own proofs can "
         "never prove its own consistency sentence: the certificate of "
         "freedom from contradiction is always issued by a strictly "
         "stronger authority, or not at all.",
         "The statement DESIGN-cognitive-frames §4 built this corpus to "
         "hold, and the mathematical warrant for the repository's "
         "architectural rule that trust roots stay external (receipts "
         "prove freshness, never correctness; no slice may gate on "
         "self-attestation). Epistemic status `derived`, and the choice "
         "is argued: within this corpus its warrant flows from the "
         "formalized node by one metatheoretic step (if T proved Con(T), "
         "the formalized theorem would make T inconsistent, contradicting "
         "the hypothesis), matching the graph-wide convention that "
         "axioms are `formal` and theorems with in-graph derivations are "
         "`derived` — the same status subset_transitivity and "
         "ex_falso_quodlibet carry.",
         ["Con(T) holds (the metatheoretic hypothesis; without it the "
          "statement is false, since an inconsistent T proves "
          "everything)",
          "T is recursively enumerable and interprets enough arithmetic "
          "for the derivability conditions D1-D3",
          "Standard proof predicate and standard Con(T) (Feferman "
          "intensionality, inherited from the consistency definition)"],
         [GODEL1931, HILBERTBERNAYS1939, FEFERMAN1960, WILLARD2001,
          BOOLOS1993],
         ["provability"],
         functionals=[BOX_FN, NEG_FN],
         constants=[CON_CONST],
         failure_modes=[
             "Fails for self-verifying theories: Willard 2001 constructs "
             "consistent r.e. theories proving their own consistency by "
             "weakening multiplication totality; the boundary case that "
             "DESIGN-cognitive-frames §4 keeps as an architectural "
             "warning against reading Goedel II as unconditional.",
             "Fails for deviant consistency predicates: Rosser-style "
             "consistency IS provable (Rosser 1936 via Feferman 1960's "
             "analysis); the theorem is about the standard predicate.",
             "Fails for theories without enough arithmetic: Presburger "
             "arithmetic is consistent, complete and decidable — it "
             "cannot even express Con, so the theorem says nothing "
             "about it.",
             "Does not say consistency is unknowable: PA's consistency "
             "is provable in ZFC and in PA + epsilon_0-induction "
             "(Gentzen); the bar is 'in T itself', not 'anywhere'."],
         inferential_links=links(
             entailed_by=[
                 "provability.incompleteness.formalized_second_incompleteness"],
             composed_with=[
                 "provability.consistency.consistency_definition"]),
         keywords=["Goedel's second incompleteness theorem", "consistency",
                   "self-verification boundary", "Willard", "Hilbert's "
                   "program", "external trust roots"]),
]


CORPORA = [
    ("provability", "provability.goedel_loeb.v1", PROVABILITY_NODES),
]


def main() -> None:
    for directory, corpus_id, nodes in CORPORA:
        corpus = {
            "schema": "../../schema/equation-node.schema.json",
            "corpus_id": corpus_id,
            "discipline": directory,
            "version": "1.0.0-alpha",
            "statement_nodes": nodes,
        }
        out = Path("data") / directory / "nodes.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        print(f"wrote {len(nodes)} {directory} nodes -> {out}")


if __name__ == "__main__":
    main()
