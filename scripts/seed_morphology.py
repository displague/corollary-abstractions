#!/usr/bin/env python3
"""Seed data/morphology/nodes.json.

The thesis this corpus is built to test: *word formation is compositional
structure, so the laws of word formation should twin the algebraic structure
the rest of the corpus already records.* Concatenative morphology is, taken
literally, the free monoid on a set of morphemes -- an associative binary
operation with an identity element, plus homomorphisms out of it (morpheme
count into the naturals, meaning into a space of composed functions). Those
are the same objects the logic and set-theory corpora state as lattice laws
and the calculus corpus states as composition rules.

Where this sits in the repo. `docs/DESIGN-linguistic-twins.md` argued that
grammar is another discipline corpus and worked at the *sentence* level
(modifiers, comparisons, questions). This corpus extends that claim one
level down, inside the word. `experiments/realsyn.py` is the empirical face
of the same object: same-lemma detection over real Spanish word/lemma/PoS
data, where the informal `WORD = STEM + AFFIX` is what the char arm has to
rediscover from surface strings. Node `morphology.wordformation.affixation`
is that equation made formal, and `morphology.inflection.paradigm_realization`
is realsyn's (lemma, form) pair typed as a function.

Authoring decisions, all of them things the matcher can see:

1. `CONCAT(...)` is a *call*, not an `op`. The matcher flattens and sorts
   only the heads in `COMMUTATIVE = {+, *}`; a call keeps its argument order
   (docs/BACKLOG.md). That is the correct encoding here and not a workaround:
   concatenation is non-commutative -- `re-do` is not `do-re` -- so the
   ordered-call semantics is exactly the semantics wanted. It is the first
   place in the corpus where the ordered-call behaviour is a feature rather
   than a hazard.
2. Argument order for `CONCAT` is fixed as (left piece, right piece), i.e.
   surface order. Every node here depends on that convention: the whole
   difference between `morphology.inflection.category_preservation` and
   `morphology.derivation.category_from_affix` is *which argument index* the
   category is projected from, and that difference is only meaningful because
   the order is fixed.
3. `EMPTY` is declared `constant`, matching how `scripts/seed_logic.py`
   declares `TRUTH` for logic and `UNIVERSE` for set theory (it generates both
   corpora from one format string). It is
   the monoid identity, and the typed skeleton comes out
   `?0:V = CONCAT⟨?0:V, ?1:P⟩` -- character for character the logic/set
   identity law `?0:V = MEET⟨?0:V, ?1:P⟩` except for the head string.

What fired, and what did not (verified with scripts/match_signatures.py):

- **No cross-discipline twin fires. That is the finding.** Every near miss in
  this corpus is a *head-only* difference, and there are four of them:

      zero_morpheme_identity   ?0:V = CONCAT⟨?0:V, ?1:P⟩
      logic/set identity_laws  ?0:V = MEET⟨?0:V, ?1:P⟩

      iterated_affixation      ?0:V = CONCAT⟨CONCAT⟨?1:V, ?2:V⟩, ?3:V⟩
      intensifier nesting      ?0:V = MOD⟨MOD⟨?1:V, ?2:V⟩, ?3:V⟩
        (the `MOD(MOD(x,i),i)` of docs/DESIGN-linguistic-twins.md, not yet a
         node -- so this one is a prediction, not a report)

      derivation.category_from_affix  CATEGORY⟨?0:V⟩ = CATEGORY⟨CONCAT⟨?1:V, ?0:V⟩⟩
      agreement.feature_percolation   FEAT⟨?0:V⟩     = FEAT⟨CONCAT⟨?1:V, ?0:V⟩⟩

      morpheme_count_additivity  LENGTH⟨CONCAT⟨?0:V, ?1:V⟩⟩ = +(LENGTH⟨?0:V⟩, LENGTH⟨?1:V⟩)
      logarithm law              LOG⟨*(?0:V, ?1:V)⟩         = +(LOG⟨?0:V⟩, LOG⟨?1:V⟩)

  The matcher renders call heads literally at every match level (shape, typed,
  family), so a corpus that introduces its own vocabulary is structurally
  quarantined however faithful its templates are. `seed_infotheory.py` already
  paid this price and paid it by *adopting* the CARD/MEET/JOIN heads. Here that
  escape is not available: adopting `MEET` for concatenation would assert
  commutativity and idempotence, which are false of words. The honest options
  are a head-alias table or a head-blind match level; filed in docs/BACKLOG.md.

  The last pair above is the interesting one, because the difference is not
  only the head. `LOG(X*Y) = LOG(X) + LOG(Y)` is *not* authored as a node here
  (this is a morphology corpus, and the archetype comparison belongs in an
  `equivalent_forms` note, which is where it is). Had it been authored, the two
  would still not twin, because `*` is a commutative `op` that the
  canonicalizer flattens and sorts while `CONCAT` is an ordered call. That
  divergence is *correct*: the free monoid of morph strings and the
  multiplicative monoid of positive reals are different monoids, and the
  matcher is right to say so. The shared thing is the archetype -- a
  homomorphism out of a monoid -- not the skeleton.

- Within the corpus, `category_preservation` and `category_from_affix` differ
  in exactly one argument index (`CONCAT⟨?0, ?1⟩` vs `CONCAT⟨?1, ?0⟩`). That
  is the whole derivation/inflection distinction as far as head placement goes,
  and it is the same kind of one-position difference that separates Shannon
  entropy from cross-entropy in the information-theory corpus. Recording it
  this way means the matcher can be *asked* whether a proposed morphological
  rule is inflection-shaped or derivation-shaped.

- `category_from_affix` and `feature_percolation` deliberately share the
  archetype id `right_hand_head_projection`, so the report's
  "archetype ids spanning multiple structures" section records them. They are
  one theorem (Williams's Righthand Head Rule) that the skeletons cannot
  merge, and the drift section is the only channel in the report that can say
  so. The label is not a mistake; it is the finding, written where the tool
  will print it.

Schema constraints observed (docs/BACKLOG.md):

- `statement_id` may not contain `_` in its first segment -- `morphology` is
  clean, unlike `set_theory`, so prefix and directory agree here.
- `symbolToken.syntactic_category` has no `functional` member, so CONCAT,
  LENGTH, MEANING, COMPOSE, REALIZE, CATEGORY and FEAT live in `functionals`
  and every node still carries at least one scalar `symbols` entry.
- No slot name may begin `sum_ prod_ lim_ max_ min_`; none here does.
- Cross-corpus `entails`/`special_case_of` need a reciprocal edge in the other
  corpus's file, so links out of this corpus use `composed_with` only.
"""

from __future__ import annotations

import json
from pathlib import Path


def sym(s, cat, role, desc, order=0):
    return {"symbol": s, "syntactic_category": cat, "semantic_role": role,
            "mathematical_order": order, "description": desc}


def op(symbol, name, arity=2, family="arithmetic"):
    return {"symbol": symbol, "name": name, "arity": arity, "operator_family": family}


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
         meaning, significance, conditions, provenance, disciplines=None,
         functionals=None, constants=None, index_sets=None, failure_modes=None,
         inferential_links=None, keywords=None, canonical_objects=None):
    context = {"disciplines": disciplines or ["morphology"],
               "subfield": subfield, "topic": topic}
    if canonical_objects:
        context["canonical_objects"] = canonical_objects
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

EQ = op("=", "equality", 2, "relational")
ADD = op("+", "addition", 2, "arithmetic")

CONCAT_FN = {
    "notation": "CONCAT(left, right)", "name": "concatenation", "input_arity": 2,
    "codomain": "morph strings",
    "description": "Concatenation of two morph strings, written as a call "
                   "because the matcher keeps call arguments ORDERED and "
                   "concatenation is non-commutative (`re-do` is not `do-re`). "
                   "Argument order is surface order: left piece first, right "
                   "piece second. Every projection statement in this corpus "
                   "depends on that convention."}

LENGTH_FN = {
    "notation": "LENGTH(.)", "name": "morph count", "input_arity": 1,
    "codomain": "non-negative integers",
    "description": "Number of morphs in a form. The canonical monoid "
                   "homomorphism from the free monoid of morph strings onto "
                   "(N, +, 0): it sends CONCAT to +, and EMPTY to 0."}

MEANING_FN = {
    "notation": "MEANING(.)", "name": "semantic value", "input_arity": 1,
    "codomain": "semantic values (typed functions and their arguments)",
    "description": "Interpretation function from a form to its semantic value. "
                   "Montague's claim is that this map is a homomorphism from "
                   "the syntactic algebra to the semantic one; stating it with "
                   "an explicit head makes that claim checkable rather than "
                   "programmatic."}

COMPOSE_FN = {
    "notation": "COMPOSE(outer, inner)", "name": "function composition",
    "input_arity": 2, "codomain": "semantic values",
    "description": "Application of a semantic operation to a semantic argument, "
                   "outer first. The same head scripts/seed_calculus.py "
                   "introduced for the chain rule -- there because the parser "
                   "has no call juxtaposition (docs/BACKLOG.md), here because "
                   "affix meanings really are functions over stem meanings. The "
                   "head is shared and the reading is the same; only the "
                   "skeletons differ."}

REALIZE_FN = {
    "notation": "REALIZE(lemma, features)", "name": "paradigm realization",
    "input_arity": 2, "codomain": "surface word forms",
    "description": "The realization rule of a paradigm: it maps a lexeme "
                   "together with a bundle of morphosyntactic feature values "
                   "onto the surface form that expresses them. Argument order "
                   "is fixed: lexeme first, feature bundle second."}

CATEGORY_FN = {
    "notation": "CATEGORY(.)", "name": "word class", "input_arity": 1,
    "codomain": "lexical categories (N, V, A, ...)",
    "description": "The lexical category (part of speech) of a form. Written as "
                   "a projection so that 'inflection preserves category' and "
                   "'derivation takes its category from the affix' become two "
                   "statements that differ only in which CONCAT argument the "
                   "projection reads."}

FEAT_FN = {
    "notation": "FEAT(.)", "name": "morphosyntactic feature bundle",
    "input_arity": 1, "codomain": "feature-value bundles",
    "description": "The morphosyntactic feature values (number, case, tense, "
                   "person, ...) carried by a form. Distinct from CATEGORY: an "
                   "inflected word keeps the stem's category but takes its "
                   "feature values from the affix."}

EMPTY_CONST = {
    "symbol": "epsilon",
    "description": "The empty string: the identity element of concatenation, and "
                   "the exponent of the zero morpheme (the linguists' null "
                   "sign). Written `EMPTY` in templates."}


# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------

ARONOFF1976 = {"citation_key": "aronoff1976",
               "bibliographic_entry": "Aronoff, M. (1976). Word Formation in Generative Grammar. Linguistic Inquiry Monograph 1. Cambridge, MA: MIT Press."}
ARONOFF2011 = {"citation_key": "aronoff2011",
               "bibliographic_entry": "Aronoff, M., Fudeman, K. (2011). What Is Morphology? (2nd ed.). Chichester: Wiley-Blackwell."}
HASPELMATH2010 = {"citation_key": "haspelmath2010",
                  "bibliographic_entry": "Haspelmath, M., Sims, A. D. (2010). Understanding Morphology (2nd ed.). London: Hodder Education."}
JURAFSKY = {"citation_key": "jurafsky2025",
            "bibliographic_entry": "Jurafsky, D., Martin, J. H. (2025). Speech and Language Processing (3rd ed. draft). Chapters on words, morphology and subword tokenization.",
            "url": "https://web.stanford.edu/~jurafsky/slp3/"}
WILLIAMS1981 = {"citation_key": "williams1981",
                "bibliographic_entry": "Williams, E. (1981). On the Notions 'Lexically Related' and 'Head of a Word'. Linguistic Inquiry, 12(2), 245-274."}
STUMP2001 = {"citation_key": "stump2001",
             "bibliographic_entry": "Stump, G. T. (2001). Inflectional Morphology: A Theory of Paradigm Structure. Cambridge: Cambridge University Press."}
MATTHEWS1991 = {"citation_key": "matthews1991",
                "bibliographic_entry": "Matthews, P. H. (1991). Morphology (2nd ed.). Cambridge: Cambridge University Press."}
HOCKETT1954 = {"citation_key": "hockett1954",
               "bibliographic_entry": "Hockett, C. F. (1954). Two Models of Grammatical Description. Word, 10(2-3), 210-234."}
MONTAGUE1970 = {"citation_key": "montague1970",
                "bibliographic_entry": "Montague, R. (1970). Universal Grammar. Theoria, 36(3), 373-398."}
PARTEE2004 = {"citation_key": "partee2004",
              "bibliographic_entry": "Partee, B. H. (2004). Compositionality in Formal Semantics: Selected Papers. Oxford: Blackwell."}
CORBETT2006 = {"citation_key": "corbett2006",
               "bibliographic_entry": "Corbett, G. G. (2006). Agreement. Cambridge: Cambridge University Press."}
MCCARTHY1981 = {"citation_key": "mccarthy1981",
                "bibliographic_entry": "McCarthy, J. J. (1981). A Prosodic Theory of Nonconcatenative Morphology. Linguistic Inquiry, 12(3), 373-418."}
HAUSER2002 = {"citation_key": "hauser2002",
              "bibliographic_entry": "Hauser, M. D., Chomsky, N., Fitch, W. T. (2002). The Faculty of Language: What Is It, Who Has It, and How Did It Evolve? Science, 298(5598), 1569-1579."}
HOPCROFT2006 = {"citation_key": "hopcroft2006",
                "bibliographic_entry": "Hopcroft, J. E., Motwani, R., Ullman, J. D. (2006). Introduction to Automata Theory, Languages, and Computation (3rd ed.). Boston: Addison-Wesley."}
BOOIJ2012 = {"citation_key": "booij2012",
             "bibliographic_entry": "Booij, G. (2012). The Grammar of Words: An Introduction to Linguistic Morphology (3rd ed.). Oxford: Oxford University Press."}
BAUER1983 = {"citation_key": "bauer1983",
             "bibliographic_entry": "Bauer, L. (1983). English Word-Formation. Cambridge: Cambridge University Press."}


# --------------------------------------------------------------------------
# Nodes
# --------------------------------------------------------------------------

NODES = [
    node("morphology.wordformation.affixation",
         "Affixation (Concatenative Word Formation)",
         "definition", "empirical", "word_formation", "concatenation",
         "word = concat(stem, suffix)",
         "w = \\mathrm{stem} \\cdot \\mathrm{suffix}",
         [{"form_id": "informal", "notation_system": "ascii",
           "expression": "WORD = STEM + AFFIX",
           "scope_note": "The informal equation used in experiments/realsyn.py; `+` there is string concatenation, which is why this corpus writes it as an ordered call instead"},
          {"form_id": "example", "notation_system": "ascii",
           "expression": "walked = concat(walk, ed)",
           "scope_note": "English past tense; the same shape as Spanish habl- + -o in the realsyn data"},
          {"form_id": "free_monoid", "notation_system": "ascii",
           "expression": "w in M*, where M is the morph inventory and * is the free monoid over it",
           "scope_note": "The algebraic reading: words are elements of the free monoid on the morph inventory"}],
         "binary_composition_definition", "WORD = CONCAT(STEM, SUFFIX)",
         [slot("WORD", "variable", "output_form"),
          slot("STEM", "variable", "base"),
          slot("SUFFIX", "variable", "affix")],
         ["The head is a call, not an operator, and that is load-bearing: the "
          "matcher flattens and sorts only `+` and `*`, so a call keeps its "
          "argument order. Concatenation is non-commutative -- `re-do` is not "
          "`do-re`, `un-lock-able` is not `able-lock-un` -- so ordered "
          "arguments are the correct semantics here rather than a workaround.",
          "Argument order is surface order: left piece first. Prefixation is "
          "the same statement with the affix in the first argument, which is "
          "why this node is named for affixation generally and slot-named for "
          "the suffixing case that the Indo-European data in "
          "experiments/realsyn.py exhibits.",
          "Both arguments are variable-like. Neither the stem nor the affix is "
          "a fixed constant of the language: paradigms range over both.",
          "The statement is closed on words: its output is the same kind of "
          "object as its inputs, which is what allows "
          "morphology.wordformation.iterated_affixation to apply it to its own "
          "output."],
         [sym("w", "variable", "output_form",
              "A surface word form, e.g. Spanish `hablaba`."),
          sym("s", "variable", "base",
              "A stem: the form an affix attaches to, itself possibly complex."),
          sym("a", "variable", "affix",
              "An affix: a bound morph with no independent distribution.")],
         [EQ],
         "A complex word is its stem followed by its affix; word formation, in "
         "the concatenative case, is nothing but ordered composition of morphs.",
         "The formal counterpart of the informal `WORD = STEM + AFFIX` that "
         "experiments/realsyn.py leaves to the character arm to rediscover from "
         "Spanish Wikipedia forms. Structurally it is the corpus's first "
         "non-commutative binary composition: everything else with two operands "
         "and one output is either arithmetic (`+`, `*`, both flattened and "
         "sorted) or a lattice head (MEET/JOIN, commutative in every model even "
         "though the matcher keeps their order). Recording an operation whose "
         "asymmetry is real, and stating that asymmetry as a convention other "
         "nodes then depend on, is what lets "
         "morphology.inflection.category_preservation and "
         "morphology.derivation.category_from_affix differ meaningfully by an "
         "argument index. No twin fires for this skeleton "
         "(`?0:V = CONCAT⟨?1:V, ?2:V⟩`); the nearest neighbours in the corpus, "
         "`?0:V = CAPMAX⟨?1:V, ?2:V⟩` and `?0:V = REALIZE⟨?1:V, ?2:V⟩`, are "
         "identical except for the head string, which the matcher renders "
         "literally.",
         ["A concatenative language, or a concatenative subpart of one",
          "A segmentation of the form into morphs is available and unique",
          "Allomorphy is resolved before the statement applies: `ed` here stands "
          "for the morpheme, not for any one of its phonological realizations"],
         [ARONOFF1976, ARONOFF2011, HASPELMATH2010, JURAFSKY, HOCKETT1954],
         functionals=[CONCAT_FN],
         failure_modes=[
             "Non-concatenative morphology breaks the statement outright: "
             "Arabic k-t-b interdigitated with a vocalic pattern (kataba, "
             "kutiba, kitaab) is not the concatenation of two substrings, and "
             "neither are ablaut (sing/sang/sung), reduplication or subtractive "
             "morphology. This node is a model specification for one family of "
             "languages, not a universal.",
             "Morph boundaries are not always recoverable: cranberry morphemes "
             "and fusional endings (Latin -o expressing person, number, tense "
             "and mood at once) resist the one-morph-one-meaning segmentation "
             "the statement presupposes. That failure is exactly what "
             "morphology.inflection.paradigm_realization is authored to absorb.",
             "Read as a *procedure* it predicts that any stem plus any affix is "
             "a word, which is false: *arrivation, *stealable are blocked by "
             "existing lexemes and by affix selection restrictions."],
         inferential_links=links(
             special_case_of=["morphology.wordformation.iterated_affixation"],
             composed_with=["morphology.wordformation.concat_associativity",
                            "morphology.wordformation.zero_morpheme_identity",
                            "morphology.quantity.morpheme_count_additivity",
                            "morphology.semantics.compositionality"]),
         keywords=["affixation", "concatenation", "morph", "stem", "free monoid",
                   "realsyn"],
         canonical_objects=["morph string", "stem", "affix"]),

    node("morphology.wordformation.iterated_affixation",
         "Iterated Affixation (Recursion in the Word)",
         "model_specification", "empirical", "word_formation", "recursion",
         "word = concat(concat(stem, suffix1), suffix2)",
         "w = ((\\mathrm{stem} \\cdot \\mathrm{suffix}_1) \\cdot \\mathrm{suffix}_2)",
         [{"form_id": "example", "notation_system": "ascii",
           "expression": "nationalization = concat(concat(concat(nation, al), ize), ation)",
           "scope_note": "Four morphs, three applications; the depth is limited by usage, not by grammar"},
          {"form_id": "closure", "notation_system": "ascii",
           "expression": "if w is a word and a is an affix then concat(w, a) may be a word",
           "scope_note": "The closure statement: the output of affixation is an input to affixation"},
          {"form_id": "intensifier_analogue", "notation_system": "ascii",
           "expression": "MOD(MOD(BASE, INT1), INT2)",
           "scope_note": "The intensifier nesting of docs/DESIGN-linguistic-twins.md ('very very big'): the same skeleton one level up, with MOD in place of CONCAT. Not authored as a node anywhere yet"}],
         "left_nested_binary_composition",
         "WORD = CONCAT(CONCAT(STEM, SUFFIX1), SUFFIX2)",
         [slot("WORD", "variable", "output_form"),
          slot("STEM", "variable", "base"),
          slot("SUFFIX1", "variable", "inner_affix"),
          slot("SUFFIX2", "variable", "outer_affix")],
         ["Left-nested, and the nesting is real: the inner CONCAT's output is "
          "the outer CONCAT's first argument. This is discrete infinity at the "
          "word level -- a finite morph inventory and an operation closed on "
          "its own output give an unbounded set of possible words.",
          "The bracketing is semantically contentful even though "
          "morphology.wordformation.concat_associativity says the *string* does "
          "not depend on it: `un-[lock-able]` (not able to be locked) and "
          "`[un-lock]-able` (able to be unlocked) are the same string with "
          "different derivations. The template records the bracketing the "
          "matcher can see; the ambiguity is that two different trees flatten "
          "to one form.",
          "Affix ORDER is constrained, not free: -al-ize-ation is possible and "
          "*-ation-ize-al is not. The template says nothing about which orders "
          "are licit; it says only that the operation composes.",
          "Reduces to morphology.wordformation.affixation when SUFFIX2 is the "
          "zero morpheme -- which is a real linguistic case, not a degenerate "
          "one, and which scripts/specialize.py cannot currently derive (see "
          "morphology.wordformation.zero_morpheme_identity)."],
         [sym("w", "variable", "output_form",
              "A multiply affixed word form."),
          sym("s", "variable", "base", "The innermost stem."),
          sym("a", "variable", "affix", "An affix; two of them here, ordered.")],
         [EQ],
         "Affixation applies to its own output, so words nest: a stem takes an "
         "affix, and the result takes another.",
         "The word-internal face of discrete infinity, and a direct echo of "
         "docs/DESIGN-linguistic-twins.md. That design note gives intensifier "
         "nesting as `MOD(MOD(x, i), i)` -- non-commutative modifier "
         "application, unbounded recursion -- and the skeleton here is "
         "`?0:V = CONCAT⟨CONCAT⟨?1:V, ?2:V⟩, ?3:V⟩` against that note's "
         "`?0:V = MOD⟨MOD⟨?1:V, ?2:V⟩, ?3:V⟩`. They are the same structure "
         "modulo one head string, which is the strongest evidence this corpus "
         "produces for the design's claim that word-internal and phrasal "
         "recursion are one phenomenon at two scales. It is a *prediction* "
         "rather than a report: the phrasal node does not exist yet, and when "
         "someone authors it the twin will fire only if the heads are unified "
         "or the matcher grows a head-blind level. Either way the check is now "
         "mechanical instead of rhetorical.",
         ["Each application produces a well-formed word of the language",
          "Affix ordering restrictions are satisfied (level-ordering, selection)",
          "The recursion is grammatically unbounded but usage-bounded; no claim "
          "is made about how deep attested words go"],
         [ARONOFF1976, HASPELMATH2010, HAUSER2002, BAUER1983, BOOIJ2012],
         functionals=[CONCAT_FN],
         failure_modes=[
             "Unbounded in the grammar does not mean unbounded in the lexicon: "
             "productivity is graded, and each affixation step can be blocked "
             "by an existing lexeme.",
             "Two different derivations can produce one string, so the template "
             "under-determines the structure of an observed word. Recovering "
             "the bracketing from the surface form is the hard part of "
             "morphological parsing, and nothing here helps with it.",
             "Templatic and infixing morphology do not nest this way at all; "
             "the failure inherited from "
             "morphology.wordformation.affixation compounds with depth."],
         inferential_links=links(
             generalizes=["morphology.wordformation.affixation"],
             composed_with=["morphology.wordformation.concat_associativity",
                            "morphology.wordformation.zero_morpheme_identity"]),
         keywords=["recursion", "discrete infinity", "affix ordering",
                   "bracketing paradox", "productivity"],
         canonical_objects=["morph string", "derivational tree"]),

    node("morphology.wordformation.concat_associativity",
         "Associativity of Concatenation",
         "axiom", "formal", "word_formation", "monoid_structure",
         "concat(concat(a, b), c) = concat(a, concat(b, c))",
         "(a \\cdot b) \\cdot c = a \\cdot (b \\cdot c)",
         [{"form_id": "flat", "notation_system": "ascii",
           "expression": "concat(a, b, c) is well defined without brackets",
           "scope_note": "The practical consequence: n-ary concatenation needs no bracketing convention"},
          {"form_id": "monoid", "notation_system": "ascii",
           "expression": "(M*, concat, empty) is a monoid, free on the morph inventory M",
           "scope_note": "With morphology.wordformation.zero_morpheme_identity, this is the whole monoid axiom set; commutativity is deliberately absent"}],
         "associativity_law",
         "CONCAT(CONCAT(FIRST, SECOND), THIRD) = CONCAT(FIRST, CONCAT(SECOND, THIRD))",
         [slot("FIRST", "variable", "left_operand"),
          slot("SECOND", "variable", "middle_operand"),
          slot("THIRD", "variable", "right_operand")],
         ["Associativity without commutativity. The corpus's other binary "
          "structures are either arithmetic (associative AND commutative, and "
          "the canonicalizer bakes both in by flattening and sorting) or "
          "lattice meets and joins (likewise commutative). This is the first "
          "node stating the weaker structure on purpose.",
          "Slot order is preserved on both sides: FIRST, SECOND, THIRD appear "
          "in that order in both trees. That is the content of the law -- only "
          "the bracketing moves -- and the matcher can see it because CONCAT is "
          "a call whose arguments are not sorted.",
          "It is the associativity of the *string*, not of the derivation. "
          "morphology.wordformation.iterated_affixation records a bracketing "
          "that this law flattens; the two are consistent because they are "
          "about different objects (surface form vs derivational history).",
          "Together with morphology.wordformation.zero_morpheme_identity this "
          "makes the set of morph strings a free monoid, which is what licenses "
          "calling LENGTH and MEANING homomorphisms rather than merely "
          "additive-looking functions."],
         [sym("a", "variable", "left_operand", "A morph string."),
          sym("b", "variable", "middle_operand", "A morph string."),
          sym("c", "variable", "right_operand", "A morph string.")],
         [EQ],
         "Concatenating three pieces gives the same string however you bracket "
         "the two concatenations.",
         "The axiom that makes the algebra of this corpus an algebra. It is "
         "also the corpus's cleanest example of a structure that is *deliberately "
         "weaker* than the ones already present: every other associative "
         "operation the corpus records is also commutative, and the "
         "canonicalizer's `COMMUTATIVE = {+, *}` flattening treats "
         "associativity and commutativity as one package. Concatenation "
         "separates them. If the matcher ever grows declared-associative call "
         "heads, this is the node that says which heads qualify and, just as "
         "importantly, that CONCAT must not be added to the commutative set.",
         ["Strings over a fixed morph inventory",
          "No claim of commutativity: concat(a, b) and concat(b, a) are "
          "distinct in general",
          "Concatenation is total: any two strings compose"],
         [HOPCROFT2006, MATTHEWS1991, HASPELMATH2010],
         functionals=[CONCAT_FN],
         failure_modes=[
             "Associativity of strings hides derivational ambiguity rather than "
             "resolving it: bracketing paradoxes such as `unlockable` are real "
             "even though the string is bracketing-independent.",
             "Phonology is not associative in the same way. Sandhi, resyllabi"
             "fication and stress assignment apply to the whole output, so the "
             "phonological form of a compound is not always recoverable from "
             "the concatenation of its parts' phonological forms."],
         inferential_links=links(
             composed_with=["morphology.wordformation.affixation",
                            "morphology.wordformation.iterated_affixation",
                            "morphology.wordformation.zero_morpheme_identity",
                            "morphology.quantity.morpheme_count_additivity"]),
         keywords=["associativity", "free monoid", "non-commutative",
                   "bracketing", "algebraic structure"],
         canonical_objects=["morph string", "free monoid"]),

    node("morphology.wordformation.zero_morpheme_identity",
         "Zero Morpheme (Identity Element of Concatenation)",
         "axiom", "formal", "word_formation", "monoid_structure",
         "concat(stem, empty) = stem",
         "\\mathrm{stem} \\cdot \\varepsilon = \\mathrm{stem}",
         [{"form_id": "two_sided", "notation_system": "ascii",
           "expression": "concat(empty, s) = s = concat(s, empty)",
           "scope_note": "The identity is two-sided; only the right-hand law is templated, following the argument-order convention of scripts/seed_logic.py"},
          {"form_id": "zero_exponent", "notation_system": "ascii",
           "expression": "sheep-PL = concat(sheep, 0)",
           "scope_note": "The linguists' zero morph: an inflectional slot filled by nothing, posited so the paradigm stays a total function"},
          {"form_id": "lattice_analogue", "notation_system": "ascii",
           "expression": "MEET(X, TOP) = X",
           "scope_note": "The identity law of logic.boolean_laws.identity_laws and settheory.boolean_laws.identity_laws; the same skeleton with a different head string"}],
         "identity_element_law", "CONCAT(STEM, EMPTY) = STEM",
         [slot("STEM", "variable", "distinguished_operand"),
          slot("EMPTY", "constant", "identity_element")],
         ["The identity element is declared `constant`, exactly as `TRUTH` is "
          "in logic.boolean_laws.identity_laws and `UNIVERSE` is in "
          "settheory.boolean_laws.identity_laws, so the typed skeleton comes "
          "out `?0:V = CONCAT⟨?0:V, ?1:P⟩` against their "
          "`?0:V = MEET⟨?0:V, ?1:P⟩`. Same structure, different head string, no "
          "twin: the whole difference is four characters.",
          "The distinguished operand occurs twice in the statement -- once "
          "inside the call, once as the other side of the equation -- and that "
          "repetition is what makes it an identity law rather than a definition.",
          "Argument order follows the convention scripts/seed_logic.py fixed "
          "for commutative call heads: distinguished operand first, special "
          "element second. Here the convention is not merely a tidiness "
          "measure, because CONCAT really is non-commutative; the two-sided law "
          "needs both orders and only one of them is templated.",
          "The zero morph is a *variable* slot's value, not a parameter's. A "
          "language that expresses plural by adding nothing is filling an "
          "affix slot with the identity element, which is why English `sheep` "
          "is analysed as sheep + zero rather than as an unaffixed form."],
         [sym("s", "variable", "distinguished_operand",
              "An arbitrary morph string."),
          sym("e", "constant", "identity_element",
              "The empty string; the zero morph when it fills an affix slot.")],
         [EQ],
         "Attaching nothing to a stem leaves the stem unchanged: the empty "
         "string is the identity of concatenation, and the zero morpheme is that "
         "identity doing inflectional work.",
         "This node exists to make an existing gap concrete. "
         "scripts/specialize.py can bind a parameter-like slot to an operator's "
         "identity element -- that is how circle circumference is recovered "
         "from the affine family with SHIFT = 0 -- but its `IDENTITY` table is "
         "hardcoded as `{+: 0, *: 1}`, so identity binding works for arithmetic "
         "and nowhere else. docs/BACKLOG.md already records that the logic and "
         "set-theory corpora state their own identity elements and get zero "
         "specialization edges for it. Morphology is now the third head making "
         "the same offer, and it adds a wrinkle the Boolean corpora do not: the "
         "slot that should take the identity value here is *variable-like*, not "
         "parameter-like, because a zero morph is a morph. So the fix needs two "
         "parts -- a per-head identity table sourced from nodes like this one, "
         "and permission for a variable slot to bind an identity element when "
         "the corpus has declared that element for that head. With both, "
         "morphology.wordformation.iterated_affixation would specialize to "
         "morphology.wordformation.affixation by binding SUFFIX2 to EMPTY, "
         "which is the correct and currently unfindable edge.",
         ["A monoid structure on morph strings (see "
          "morphology.wordformation.concat_associativity)",
          "The identity is two-sided and unique",
          "Positing a zero morph requires an independently motivated paradigm "
          "cell for it to fill"],
         [HOCKETT1954, MATTHEWS1991, HASPELMATH2010, HOPCROFT2006],
         functionals=[CONCAT_FN],
         constants=[EMPTY_CONST],
         failure_modes=[
             "Zero morphs are cheap and therefore dangerous: any missing "
             "exponent can be described as a zero, so the analysis has content "
             "only when a paradigm cell independently demands an exponent. "
             "Unconstrained, it makes the theory unfalsifiable.",
             "Formally the identity element is unique; linguistically, "
             "'zero plural', 'zero past' and 'zero derivation' (conversion: "
             "the noun `hammer` to the verb `hammer`) are different phenomena "
             "sharing one notation, and the algebra cannot tell them apart."],
         inferential_links=links(
             composed_with=["morphology.wordformation.affixation",
                            "morphology.wordformation.iterated_affixation",
                            "morphology.wordformation.concat_associativity",
                            "logic.boolean_laws.identity_laws",
                            "settheory.boolean_laws.identity_laws"]),
         keywords=["zero morpheme", "identity element", "monoid", "null exponent",
                   "conversion", "specialization gap"],
         canonical_objects=["empty string", "paradigm cell"]),

    node("morphology.quantity.morpheme_count_additivity",
         "Additivity of Morpheme Count",
         "theorem", "derived", "word_formation", "homomorphism",
         "length(concat(a, b)) = length(a) + length(b)",
         "|a \\cdot b| = |a| + |b|",
         [{"form_id": "homomorphism", "notation_system": "ascii",
           "expression": "LENGTH: (M*, concat, empty) -> (N, +, 0) is a monoid homomorphism",
           "scope_note": "With length(empty) = 0, the two conditions defining a monoid homomorphism are exactly this node and morphology.wordformation.zero_morpheme_identity"},
          {"form_id": "example", "notation_system": "ascii",
           "expression": "length(un + lock + able) = 1 + 1 + 1 = 3",
           "scope_note": "Extended to three pieces by associativity"},
          {"form_id": "logarithm_archetype", "notation_system": "ascii",
           "expression": "LOG(X*Y) = LOG(X) + LOG(Y)",
           "scope_note": "The archetype comparison, recorded here rather than authored as a node: the logarithm is the same homomorphism out of a DIFFERENT monoid (positive reals under multiplication, commutative). The skeletons diverge because `*` is a commutative op the canonicalizer flattens and sorts while CONCAT is an ordered call -- a difference that is correct, not a matcher defect"}],
         "monoid_homomorphism_to_addition",
         "LENGTH(CONCAT(FIRST, SECOND)) = LENGTH(FIRST) + LENGTH(SECOND)",
         [slot("FIRST", "variable", "left_operand"),
          slot("SECOND", "variable", "right_operand")],
         ["A homomorphism statement: one head (LENGTH) applied to a composition "
          "on the left, and the same head applied to the pieces, combined by a "
          "different operation, on the right. Structure carries across a change "
          "of operation -- CONCAT becomes `+` -- which is the general shape "
          "shared with the logarithm law and with "
          "morphology.semantics.compositionality.",
          "The right-hand side is a commutative `+`, so the canonicalizer "
          "flattens and sorts it, while the left-hand side's CONCAT stays "
          "ordered. The asymmetry is faithful: morph *count* forgets order, "
          "morph *concatenation* does not. Forgetting is precisely what makes "
          "the map a homomorphism onto a smaller structure rather than an "
          "isomorphism.",
          "The map is not injective: infinitely many words have length 3. A "
          "homomorphism to (N, +) is the coarsest useful invariant of a morph "
          "string, and every property it can express is a property of counts.",
          "Zero morphs must count as zero for the homomorphism to hold, which "
          "ties this node to morphology.wordformation.zero_morpheme_identity: "
          "the unit condition length(empty) = 0 is the other half of the "
          "definition."],
         [sym("n", "variable", "output_count",
              "The number of morphs in a form; a non-negative integer."),
          sym("a", "variable", "left_operand", "A morph string."),
          sym("b", "variable", "right_operand", "A morph string.")],
         [EQ, ADD],
         "The morph count of a concatenation is the sum of the morph counts: "
         "counting morphemes distributes over building words.",
         "The corpus's clearest statement of a homomorphism, and a deliberate "
         "test of how far the matcher can see one. The intended comparison is "
         "the logarithm law, `LOG(X*Y) = LOG(X) + LOG(Y)` -- the archetypal "
         "structure-preserving map that turns a product into a sum. That law is "
         "*not* authored here (this is a morphology corpus, and the observation "
         "belongs in an equivalent-forms note), but the comparison was checked: "
         "even if it existed, the two would not twin, and for two independent "
         "reasons. The head strings differ, LENGTH against LOG, which the "
         "matcher renders literally at every level. And the inner operation "
         "differs in kind -- `*` is a commutative op that the canonicalizer "
         "flattens and sorts, CONCAT is an ordered call -- so the trees are not "
         "isomorphic even with the heads unified. The second reason is "
         "*correct*: the free monoid of morph strings and the multiplicative "
         "monoid of positive reals are genuinely different monoids, and a "
         "matcher that merged them would be lying. What the two share is an "
         "archetype, not a skeleton, and the corpus currently has no level at "
         "which archetype-sharing without skeleton-sharing can be asserted and "
         "checked. The geospatial-style additivity elsewhere in the corpus "
         "(inclusion-exclusion, `CARD(JOIN(A,B)) = CARD(A) + CARD(B) - "
         "CARD(MEET(A,B))`) is nearer in spirit but further in structure: it "
         "carries an overlap correction, and concatenation has no overlap to "
         "correct for, because the pieces of a word do not share material.",
         ["A unique morph segmentation of each form",
          "Zero morphs count as zero, i.e. length(empty) = 0",
          "Counting morphs, not characters or syllables: the statement is false "
          "for orthographic length under any process that deletes or fuses "
          "material at the boundary"],
         [HASPELMATH2010, MATTHEWS1991, HOPCROFT2006, JURAFSKY],
         functionals=[LENGTH_FN, CONCAT_FN],
         failure_modes=[
             "Fusional exponence defeats the count: Latin `-o` in `amo` "
             "realizes person, number, tense, voice and mood together, so 'how "
             "many morphemes' has no determinate answer and the additivity is "
             "vacuous rather than false.",
             "Under haplology and boundary deletion the surface string loses "
             "material (`humbly` from humble + ly), so character length is not "
             "additive even where morph count is.",
             "Subword tokenizers count pieces additively but their pieces are "
             "not morphs; borrowing this statement to justify a BPE token count "
             "as a morphological measure is a category error."],
         inferential_links=links(
             composed_with=["morphology.wordformation.affixation",
                            "morphology.wordformation.concat_associativity",
                            "morphology.wordformation.zero_morpheme_identity"]),
         keywords=["homomorphism", "additivity", "morpheme count", "logarithm",
                   "structure-preserving map"],
         canonical_objects=["morph string", "natural numbers under addition"]),

    node("morphology.semantics.compositionality",
         "Compositionality of Word Meaning",
         "model_specification", "empirical", "semantics", "homomorphism",
         "meaning(concat(a, b)) = compose(meaning(a), meaning(b))",
         "[\\![a \\cdot b]\\!] = [\\![a]\\!] \\circ [\\![b]\\!]",
         [{"form_id": "frege", "notation_system": "ascii",
           "expression": "the meaning of a complex form is a function of the meanings of its parts and of the way they are combined",
           "scope_note": "The principle in words; the template is the same claim with 'is a function of' spelled as an explicit head"},
          {"form_id": "montague", "notation_system": "ascii",
           "expression": "MEANING is a homomorphism from the syntactic algebra to the semantic algebra",
           "scope_note": "Montague's Universal Grammar formulation, which is what makes this node's shape a homomorphism rather than an analogy"},
          {"form_id": "example", "notation_system": "ascii",
           "expression": "meaning(read + able) = compose(ABLE, READ) = 'able to be read'",
           "scope_note": "The affix contributes the function, the stem the argument; the argument order of COMPOSE is outer-first"}],
         "meaning_homomorphism",
         "MEANING(CONCAT(FIRST, SECOND)) = COMPOSE(MEANING(FIRST), MEANING(SECOND))",
         [slot("FIRST", "variable", "left_operand"),
          slot("SECOND", "variable", "right_operand")],
         ["The same homomorphism shape as "
          "morphology.quantity.morpheme_count_additivity, with COMPOSE where "
          "that node has `+`: one head applied to a composition on the left, "
          "the same head applied to the parts and recombined on the right. The "
          "two do not twin, because the recombining operation differs in head "
          "and in kind, but the archetype is one.",
          "COMPOSE is ordered and non-commutative, matching CONCAT. This is the "
          "one place in the corpus where the syntactic and semantic operations "
          "are *both* non-commutative, so the homomorphism preserves order "
          "rather than discarding it -- unlike the count homomorphism, which "
          "throws order away.",
          "Argument order is outer-first, the convention "
          "scripts/seed_calculus.py fixed for COMPOSE in the chain rule. Here "
          "it means the affix's meaning is the function and the stem's meaning "
          "the argument in suffixed derivation; for prefixes the same order "
          "holds with the operands swapped in CONCAT, which the template does "
          "not distinguish.",
          "Read as a constraint on possible grammars rather than as a fact: "
          "compositionality is a methodological commitment, and its empirical "
          "bite comes from what it forbids (unpredictable idiomatic meaning for "
          "productively formed words)."],
         [sym("m", "variable", "output_meaning",
              "The semantic value of the complex form."),
          sym("a", "variable", "left_operand", "A morph string (typically the stem)."),
          sym("b", "variable", "right_operand", "A morph string (typically the affix).")],
         [EQ],
         "The meaning of a complex word is built from the meanings of its parts "
         "by an operation that mirrors the way the parts were combined.",
         "The node authored to test a shape kinship with the chain rule, and "
         "the honest answer is that the kinship is partial. "
         "calculus.differentiation.chain_rule is "
         "`D(COMPOSE(OUTER, INNER)) = COMPOSE(D(OUTER), INNER) * D(INNER)`; "
         "this node is "
         "`MEANING(CONCAT(A, B)) = COMPOSE(MEANING(A), MEANING(B))`. Both push "
         "an operator through a composition, and both use the COMPOSE head that "
         "docs/BACKLOG.md records as a workaround for the parser's missing call "
         "juxtaposition -- so the vocabulary is genuinely shared across two "
         "disciplines with the same reading. But the skeletons are not close: "
         "the chain rule's right-hand side is a *product* of two terms and "
         "leaves INNER undifferentiated inside the composition, because "
         "differentiation is not a homomorphism for composition -- it is a "
         "homomorphism only up to that correction factor. Compositionality "
         "claims no correction factor at all. So the correct report is a shared "
         "head and a shared intuition ('the operator distributes over the "
         "composition') with a structurally different law underneath, and "
         "claiming a twin here would be exactly the kind of surface analogy the "
         "matcher exists to refuse.",
         ["A syntactic algebra with a determinate part-whole structure",
          "A semantic algebra with an operation matching each syntactic one",
          "The word is formed productively; stored idiomatic forms are outside "
          "the statement's scope"],
         [MONTAGUE1970, PARTEE2004, ARONOFF1976, JURAFSKY],
         functionals=[MEANING_FN, CONCAT_FN, COMPOSE_FN],
         failure_modes=[
             "Lexicalization is the standard counterexample: `business` is not "
             "busy + ness, `transmission` (car part) is not transmit + ion. "
             "Derived words drift, and a stored meaning overrides the composed "
             "one, so the statement holds for the productive process and not "
             "for the resulting lexeme.",
             "The principle is near-vacuous without constraints on the "
             "semantic algebra: allow arbitrary operations and any meaning "
             "assignment becomes compositional. Its content lives entirely in "
             "how restricted COMPOSE is.",
             "Bracketing paradoxes make MEANING and CONCAT disagree about "
             "structure: `unhappier` is phonologically [[un happy] er] and "
             "semantically un[happier], so no single tree satisfies both."],
         inferential_links=links(
             composed_with=["morphology.wordformation.affixation",
                            "morphology.wordformation.iterated_affixation",
                            "calculus.differentiation.chain_rule"]),
         keywords=["compositionality", "Frege", "Montague", "homomorphism",
                   "lexicalization", "chain rule"],
         canonical_objects=["semantic value", "syntactic algebra"]),

    node("morphology.inflection.paradigm_realization",
         "Paradigm Realization (Inflection as a Function)",
         "model_specification", "empirical", "inflection", "paradigm",
         "surface = realize(lemma, features)",
         "\\mathrm{surface} = R(\\ell, \\sigma)",
         [{"form_id": "example", "notation_system": "ascii",
           "expression": "hablaba = realize(hablar, {1sg or 3sg, imperfect, indicative})",
           "scope_note": "A cell of the Spanish paradigm, exactly the (form, lemma) pairing experiments/realsyn.py reads out of the wlp data"},
          {"form_id": "same_lemma_test", "notation_system": "ascii",
           "expression": "same_lemma(w1, w2) iff there exist f1, f2 with w1 = realize(l, f1) and w2 = realize(l, f2)",
           "scope_note": "The realsyn task statement: two forms are related iff they are two cells of one paradigm"},
          {"form_id": "concatenative_case", "notation_system": "ascii",
           "expression": "realize(l, f) = concat(stem(l), exponent(f))",
           "scope_note": "The special case where realization is affixation; morphology.wordformation.affixation is this node with the function opened up"}],
         "two_argument_realization", "SURFACE = REALIZE(LEMMA, FEATURES)",
         [slot("SURFACE", "variable", "output_form"),
          slot("LEMMA", "variable", "lexeme"),
          slot("FEATURES", "set", "feature_bundle")],
         ["Realizational, not concatenative: REALIZE is opaque on purpose, so "
          "that the statement covers suppletion (`go`/`went`), stem alternation "
          "and fusional exponence, none of which "
          "morphology.wordformation.affixation can express. The price is that "
          "the matcher sees no internal structure -- the same trade "
          "infotheory.channel.channel_capacity makes with its CAPMAX head.",
          "The feature slot is declared `set`, because a feature bundle is a "
          "set of feature-value pairs and not a scalar. It still classes as "
          "variable-like for the typed matcher, so the skeleton is "
          "`?0:V = REALIZE⟨?1:V, ?2:V⟩`.",
          "Argument order is fixed: lexeme first, feature bundle second. The "
          "asymmetry is real -- the lexeme selects which paradigm applies, the "
          "features select which cell of it -- so an ordered call is the right "
          "encoding.",
          "The function is total on its paradigm: every cell has a realization, "
          "which is what forces zero exponents "
          "(morphology.wordformation.zero_morpheme_identity) and defective "
          "paradigms into view as the two ways totality can fail."],
         [sym("w", "variable", "output_form", "A surface word form."),
          sym("l", "variable", "lexeme",
              "A lexeme, cited by its lemma (the conventional citation form)."),
          sym("f", "set", "feature_bundle",
              "A bundle of morphosyntactic feature values: person, number, "
              "tense, case, and so on.")],
         [EQ],
         "A surface form is what you get by realizing a lexeme with a particular "
         "bundle of morphosyntactic features; a paradigm is that function "
         "tabulated over all the bundles.",
         "The bridge between this corpus and experiments/realsyn.py. That "
         "experiment's data is exactly this function sampled: word / lemma / PoS "
         "triples from Spanish Wikipedia, with the task being to decide whether "
         "two surface forms come from one lexeme. Written as "
         "`SURFACE = REALIZE(LEMMA, FEATURES)`, the same-lemma question becomes "
         "an existential over the second argument -- the two forms are related "
         "iff the first argument can be held fixed -- which is the "
         "questions-are-equations reading of docs/DESIGN-linguistic-twins.md "
         "applied to morphology. Structurally the node is a near-neighbour of "
         "everything else in the corpus and a twin of nothing: its skeleton "
         "`?0:V = REALIZE⟨?1:V, ?2:V⟩` differs from "
         "morphology.wordformation.affixation's "
         "`?0:V = CONCAT⟨?1:V, ?2:V⟩` only in the head string, which is "
         "appropriate, since Hockett's two models of grammatical description "
         "(item-and-arrangement versus item-and-process) really are the same "
         "shape disagreeing about what the pieces are.",
         ["A lexeme with an established paradigm",
          "Feature bundles drawn from the language's morphosyntactic feature "
          "inventory",
          "One form per cell; overabundance (two licit forms for one cell) makes "
          "the relation non-functional and is out of scope"],
         [STUMP2001, MATTHEWS1991, HOCKETT1954, HASPELMATH2010, JURAFSKY],
         functionals=[REALIZE_FN, CONCAT_FN],
         failure_modes=[
             "Defective paradigms break totality: some lexemes simply lack "
             "cells (Spanish `abolir` in several present-tense forms), so "
             "REALIZE is a partial function in practice.",
             "Syncretism breaks injectivity: one form can realize several "
             "distinct bundles (Spanish `hablaba` is both 1sg and 3sg), so the "
             "features are not recoverable from the surface form, which is the "
             "principal difficulty the realsyn task poses to a model working "
             "from characters.",
             "Lemma choice is a lexicographic convention, not a linguistic "
             "fact; treating the lemma as the underlying form imports an "
             "arbitrary choice into the statement."],
         inferential_links=links(
             composed_with=["morphology.wordformation.affixation",
                            "morphology.inflection.category_preservation",
                            "morphology.agreement.feature_percolation"]),
         keywords=["paradigm", "realization", "lemma", "inflection", "syncretism",
                   "realsyn"],
         canonical_objects=["lexeme", "feature bundle", "paradigm cell"]),

    node("morphology.inflection.category_preservation",
         "Inflection Preserves Word Class",
         "proposition", "empirical", "inflection", "headedness",
         "category(concat(stem, inflection)) = category(stem)",
         "\\mathrm{cat}(\\mathrm{stem} \\cdot \\mathrm{infl}) = \\mathrm{cat}(\\mathrm{stem})",
         [{"form_id": "example", "notation_system": "ascii",
           "expression": "category(walk + ed) = category(walk) = V",
           "scope_note": "Tense inflection leaves a verb a verb"},
          {"form_id": "criterion", "notation_system": "ascii",
           "expression": "an affix is inflectional only if it leaves the category fixed",
           "scope_note": "One of the standard diagnostics separating inflection from derivation; necessary, not sufficient"}],
         "projection_from_first_component",
         "CATEGORY(CONCAT(STEM, INFLECTION)) = CATEGORY(STEM)",
         [slot("STEM", "variable", "base"),
          slot("INFLECTION", "variable", "affix")],
         ["The projection reads the FIRST argument of CONCAT. That is the "
          "entire structural difference from "
          "morphology.derivation.category_from_affix, whose projection reads "
          "the second -- one argument index, exactly as one repeated slot "
          "position separates Shannon entropy from cross-entropy in the "
          "information-theory corpus.",
          "The affix slot appears on the left-hand side and nowhere on the "
          "right: the statement says the inflectional affix is invisible to "
          "category, which is a strong claim recorded as an absence.",
          "Category is preserved but features are not: the inflectional "
          "features come from the affix, which is "
          "morphology.agreement.feature_percolation. The two nodes together are "
          "the reason CATEGORY and FEAT are separate heads rather than one.",
          "Only meaningful because CONCAT's argument order is fixed by "
          "convention; under a commutative head the two projection nodes would "
          "collapse into one and the inflection/derivation contrast would be "
          "unstateable."],
         [sym("c", "variable", "output_category",
              "A lexical category: N, V, A, and so on."),
          sym("s", "variable", "base", "The stem being inflected."),
          sym("i", "variable", "affix", "An inflectional affix.")],
         [EQ],
         "Inflecting a word does not change what kind of word it is: the "
         "category of an inflected form is the category of its stem.",
         "Half of the derivation/inflection distinction, written so that the "
         "matcher can check which half a proposed rule belongs to. The pair "
         "with morphology.derivation.category_from_affix is the corpus's "
         "tightest near miss: `CATEGORY⟨?0:V⟩ = CATEGORY⟨CONCAT⟨?0:V, ?1:V⟩⟩` "
         "against `CATEGORY⟨?0:V⟩ = CATEGORY⟨CONCAT⟨?1:V, ?0:V⟩⟩`, differing in "
         "one argument index and in nothing else. That the two do not twin is "
         "the right answer, and it is a *useful* right answer: it means the "
         "distinction between changing a word's class and merely marking it "
         "survives anonymization of every symbol involved. A classification "
         "that survives having its labels stripped is the strongest evidence "
         "this corpus can offer that a linguistic distinction is structural "
         "rather than terminological.",
         ["A concatenative inflectional system",
          "A determinate lexical category for the stem",
          "Category-preserving derivation exists (`friend` to `friendship` is "
          "N to N), so this criterion is necessary for inflection, not "
          "sufficient"],
         [HASPELMATH2010, WILLIAMS1981, BOOIJ2012, ARONOFF2011],
         functionals=[CATEGORY_FN, CONCAT_FN],
         failure_modes=[
             "The inflection/derivation boundary is a cline, not a partition: "
             "participles and gerunds are inflectional by paradigm and "
             "category-changing in distribution, so the statement's crispness "
             "overstates the data.",
             "Transposition (deverbal nominalization by inflection-like means) "
             "is a standing counterexample in languages with rich derivational "
             "inflection.",
             "Conversion changes category with no affix at all, so the "
             "statement has nothing to apply to there while the phenomenon it "
             "describes is exactly what conversion violates."],
         inferential_links=links(
             composed_with=["morphology.wordformation.affixation",
                            "morphology.derivation.category_from_affix",
                            "morphology.agreement.feature_percolation",
                            "morphology.inflection.paradigm_realization"]),
         keywords=["inflection", "word class", "part of speech", "headedness",
                   "derivation contrast"],
         canonical_objects=["lexical category", "inflected form"]),

    node("morphology.derivation.category_from_affix",
         "Derivation Takes Its Category from the Affix (Righthand Head Rule)",
         "proposition", "empirical", "derivation", "headedness",
         "category(concat(stem, derivation)) = category(derivation)",
         "\\mathrm{cat}(\\mathrm{stem} \\cdot \\mathrm{deriv}) = \\mathrm{cat}(\\mathrm{deriv})",
         [{"form_id": "example", "notation_system": "ascii",
           "expression": "category(happy + ness) = category(ness) = N",
           "scope_note": "An adjective plus a nominalizing suffix is a noun: the suffix wins"},
          {"form_id": "righthand_head_rule", "notation_system": "ascii",
           "expression": "the head of a morphologically complex word is its rightmost member",
           "scope_note": "Williams (1981); the template is that rule restricted to category projection"},
          {"form_id": "compounds", "notation_system": "ascii",
           "expression": "category(dog + house) = category(house) = N",
           "scope_note": "Endocentric compounds project from the right member too, in the Germanic languages the rule was stated for"}],
         "right_hand_head_projection",
         "CATEGORY(CONCAT(STEM, DERIVATION)) = CATEGORY(DERIVATION)",
         [slot("STEM", "variable", "base"),
          slot("DERIVATION", "variable", "affix")],
         ["The projection reads the SECOND argument of CONCAT -- the mirror of "
          "morphology.inflection.category_preservation, and the whole "
          "difference between the two skeletons.",
          "The base slot appears only inside the concatenation: the statement "
          "says the stem's category is discarded, which is why derivation can "
          "move a form across word classes while inflection cannot.",
          "This node shares the archetype id `right_hand_head_projection` with "
          "morphology.agreement.feature_percolation, deliberately. The two are "
          "one theorem -- Williams's Righthand Head Rule, projecting category "
          "in one case and features in the other -- and their skeletons differ "
          "only in the head string (CATEGORY against FEAT). Sharing the label "
          "makes scripts/match_signatures.py print them in its "
          "archetype-label-drift section, which is the only channel in the "
          "report that can record a head-only difference.",
          "Stated for suffixation. Prefixes in English are mostly "
          "category-neutral (`re-`, `un-`), which is consistent with the "
          "righthand head rule and is why the rule is stated for the right "
          "member rather than for 'the affix'."],
         [sym("c", "variable", "output_category", "A lexical category."),
          sym("s", "variable", "base", "The stem being derived from."),
          sym("d", "variable", "affix", "A derivational affix.")],
         [EQ],
         "A derived word belongs to the class its affix specifies, not the class "
         "of the stem it was built from: the rightmost element is the head.",
         "The other half of the derivation/inflection contrast, and the node "
         "that turns headedness into something the matcher can check. Against "
         "morphology.inflection.category_preservation it differs in exactly one "
         "argument index; against morphology.agreement.feature_percolation it "
         "differs in exactly one head string. Those two near misses are "
         "different in kind and the difference matters. The first is a genuine "
         "structural distinction that the matcher *should* keep apart, and "
         "keeping it apart is a success. The second is one theorem the matcher "
         "*cannot* recognize as one, because call heads are rendered literally "
         "at every match level, and no amount of faithful authoring can fix it "
         "from inside a corpus. That asymmetry is the clearest statement this "
         "corpus can make about where the tooling stands: it discriminates "
         "well and it generalizes only where vocabulary was shared in advance.",
         ["A concatenative derivational system with a rightmost head",
          "The affix carries a category specification of its own",
          "Endocentric formations only: exocentric compounds (`pickpocket`, "
          "`redhead`) have no member whose category the whole inherits"],
         [WILLIAMS1981, ARONOFF1976, BAUER1983, BOOIJ2012, HASPELMATH2010],
         functionals=[CATEGORY_FN, CONCAT_FN],
         failure_modes=[
             "The Righthand Head Rule is a generalization about Germanic and "
             "not a universal: left-headed compounding is normal in Romance "
             "(`capostazione`) and in Vietnamese, so the argument index in the "
             "template is language-particular.",
             "Exocentric compounds have no head at all, so the projection is "
             "undefined rather than wrong.",
             "Category-preserving derivation (`friend` to `friendship`, N to N) "
             "satisfies both this node and "
             "morphology.inflection.category_preservation, so the pair does not "
             "partition the affixes even where both hold."],
         inferential_links=links(
             composed_with=["morphology.wordformation.affixation",
                            "morphology.inflection.category_preservation",
                            "morphology.agreement.feature_percolation"]),
         keywords=["derivation", "righthand head rule", "headedness",
                   "category change", "compounding"],
         canonical_objects=["lexical category", "derived word", "head"]),

    node("morphology.agreement.feature_percolation",
         "Feature Percolation from the Affix",
         "proposition", "empirical", "inflection", "headedness",
         "feat(concat(stem, inflection)) = feat(inflection)",
         "F(\\mathrm{stem} \\cdot \\mathrm{infl}) = F(\\mathrm{infl})",
         [{"form_id": "example", "notation_system": "ascii",
           "expression": "feat(gat + as) = feat(as) = {feminine, plural}",
           "scope_note": "Spanish: the noun's gender and number values are those the suffix spells out"},
          {"form_id": "agreement", "notation_system": "ascii",
           "expression": "feat(target) = feat(controller)",
           "scope_note": "The syntactic consequence: agreement copies the percolated bundle onto a target elsewhere in the phrase, as in `las gatas negras`"},
          {"form_id": "percolation", "notation_system": "ascii",
           "expression": "head features of a complex word are the head features of its head",
           "scope_note": "The general percolation convention; this template is its inflectional case"}],
         "right_hand_head_projection",
         "FEAT(CONCAT(STEM, INFLECTION)) = FEAT(INFLECTION)",
         [slot("STEM", "variable", "base"),
          slot("INFLECTION", "variable", "affix")],
         ["Same structure as morphology.derivation.category_from_affix with a "
          "different projection head: FEAT rather than CATEGORY. The two share "
          "an archetype id on purpose so the report records the collision.",
          "Together with morphology.inflection.category_preservation this says "
          "an inflected word is a split inheritance: category from the stem, "
          "feature values from the affix. Neither statement alone characterizes "
          "inflection; the pair does.",
          "The feature bundle percolates up to the whole word, which is what "
          "makes it visible to syntax. Agreement is that bundle being matched "
          "against another word's, so agreement is a consequence of percolation "
          "and not an independent mechanism.",
          "Stated as an equation, not an inclusion, which is an idealization: "
          "in reality the word's bundle is the unification of the stem's "
          "inherent features (lexical gender) with the affix's, and the "
          "template flattens that into equality."],
         [sym("f", "set", "output_bundle",
              "The morphosyntactic feature values of the whole form."),
          sym("s", "variable", "base", "The stem."),
          sym("i", "variable", "affix", "An inflectional affix bearing feature values.")],
         [EQ],
         "The morphosyntactic features of an inflected word are those its "
         "inflectional affix spells out; they percolate up to the whole word, "
         "where syntax can see them and agreement can copy them.",
         "The node that makes agreement a corollary rather than a primitive, and "
         "the second member of this corpus's head-only near miss. Its skeleton "
         "`FEAT⟨?0:V⟩ = FEAT⟨CONCAT⟨?1:V, ?0:V⟩⟩` is character-for-character "
         "morphology.derivation.category_from_affix's with CATEGORY swapped for "
         "FEAT, and the two really are one theorem: Williams's Righthand Head "
         "Rule says the rightmost member is the head and that the head's "
         "properties project, without caring whether the property in question "
         "is a category label or a feature bundle. The corpus cannot make the "
         "matcher say so. Merging the heads would be false -- an inflected verb "
         "keeps its stem's category while taking the affix's features, so "
         "CATEGORY and FEAT project from different arguments in the "
         "inflectional case and would contradict each other under one head. The "
         "shared archetype id is therefore the honest record: same theorem, two "
         "structures, filed where the tool will print the collision.",
         ["An inflectional affix that carries feature values",
          "Head features only: idiosyncratic stem-level features do not "
          "percolate",
          "Concatenative exponence; fusional and cumulative exponents realize "
          "several features at once but still percolate as a bundle"],
         [WILLIAMS1981, CORBETT2006, STUMP2001, HASPELMATH2010],
         functionals=[FEAT_FN, CONCAT_FN],
         failure_modes=[
             "Inherent features do not percolate from the affix: Spanish lexical "
             "gender is a property of the stem (`el problema` is masculine "
             "despite the -a), so the equation holds for contextual features "
             "and overstates the case for inherent ones.",
             "Agreement can be semantic rather than morphological (`the "
             "committee have decided`), in which case the target's features "
             "match the referent and not the controller's percolated bundle.",
             "Zero exponents percolate nothing, so a form inflected by a zero "
             "morph gets its features from the paradigm cell rather than from "
             "the affix -- the statement is vacuous exactly where "
             "morphology.wordformation.zero_morpheme_identity applies."],
         inferential_links=links(
             composed_with=["morphology.wordformation.affixation",
                            "morphology.derivation.category_from_affix",
                            "morphology.inflection.category_preservation",
                            "morphology.inflection.paradigm_realization"]),
         keywords=["percolation", "agreement", "features", "headedness",
                   "gender", "number"],
         canonical_objects=["feature bundle", "head", "agreement target"]),
]


def main() -> None:
    corpus = {
        "schema": "../../schema/equation-node.schema.json",
        "corpus_id": "morphology.concatenative.v1",
        "discipline": "morphology",
        "version": "1.0.0-alpha",
        "statement_nodes": NODES,
    }
    out = Path("data/morphology/nodes.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"wrote {len(NODES)} morphology nodes -> {out}")


if __name__ == "__main__":
    main()
