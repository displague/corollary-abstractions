#!/usr/bin/env python3
"""Seed data/logic/nodes.json and data/set_theory/nodes.json together.

Two corpora, one script, on purpose. Propositional logic and the algebra of
sets are not analogous structures -- they are the *same* structure, a Boolean
lattice, presented over two different carriers. Every equational law below is
a theorem of the same axiom set; the propositional reading and the powerset
reading differ only in what the elements are called. Stone's representation
theorem is the exact statement of that identity, and the Lindenbaum-Tarski
construction is the map that carries one presentation to the other.

The corpus's design decision follows from that fact. `anonymized_template` is
*anonymized*: it abstracts away discipline-specific naming. Slot names are
already abstracted (`PROP1`, `SETA` -> `?0`), so operator families are
abstracted the same way:

    MEET(x, y)   conjunction `and`      /  intersection `∩`
    JOIN(x, y)   disjunction `or`       /  union `∪`
    NEG(x)       negation `not`         /  complement `(.)^c`
    LEQ(x, y)    entailment `|-`        /  inclusion `⊆`
    TOP / BOT    `true` / `false`       /  universe `U` / empty set `∅`

Discipline notation is *not* lost; it lives where it belongs, in
`formal_statement.canonical_ascii`, `canonical_latex` and `equivalent_forms`.
The consequence is that logic De Morgan and set De Morgan share one skeleton
character for character:

    JOIN⟨NEG⟨?0:V⟩, NEG⟨?1:V⟩⟩ = NEG⟨MEET⟨?0:V, ?1:V⟩⟩

and so do the other six shared laws. These are the cleanest cross-discipline
typed twins in the corpus, because for once the twinning is not an analogy
between unrelated subject matters (compounding money and decaying nuclei) but
literal identity of theorem.

Two authoring rules make that hold, and both are load-bearing:

1. The template strings are shared format strings (TPL_*), instantiated with
   a per-discipline vocabulary. A twin cannot drift because there is only one
   string.
2. Call arguments are matched in ORDER by scripts/match_signatures.py -- calls
   are not commutative there, unlike `+` and `*`. So `MEET(X, TOP)` and
   `MEET(TOP, X)` are different skeletons even though meet is commutative in
   every model. The convention adopted here, and required of anything added
   later: the distinguished/repeated element comes first, and the special
   element (TOP, BOT, or a NEG-ed copy) comes second.

Node classes track the axiom/theorem split of a Boolean algebra rather than
flattening everything to `identity`: distributivity, the identity laws and the
complement laws are Huntington's postulates (`axiom`/`formal`), while
idempotence, absorption, involution and De Morgan are consequences
(`identity`/`derived`) and carry `entailed_by` edges to say which postulates
they lean on. The same lineage is mirrored in both corpora, because it is the
same proof.

Prover alignment: these are precisely the statements the planned Lean
sub-project proves first (`and_or_distrib_left`, `not_not`, `absorb`,
`compl_inf`, `Set.compl_inter`...). Authoring them as one shared skeleton per
law means a proof obligation discharged for the lattice discharges both
readings at once, which is the whole point of hanging a prover off this graph.

Discipline-only nodes probe the edges of the shared structure: modus ponens
and contraposition on the logic side (inference, not equation), subset
transitivity and two-set inclusion-exclusion on the set side (order and
counting, which propositions have no analogue of).

Registered prediction (hypothetical syllogism)
----------------------------------------------

`settheory.order.subset_transitivity` was authored with the lattice-abstract
LEQ head rather than a SUBSET head, and its own commentary recorded why: so
that a future logic node for entailment transitivity "would twin with this one
exactly, without either corpus being rewritten". The node was left unwritten on
purpose, as a bet placed against the corpus and payable later.

`logic.inference.hypothetical_syllogism` is that node, and the reading it needs
is standard rather than convenient: in the Lindenbaum-Tarski algebra the
elements are formulas modulo interderivability and the partial order IS logical
consequence, so `LEQ(a, b)` is `a |- b` in the same sense that it is
`A subset B` over powersets. Both nodes are now generated from ONE format
string (TPL_ORDER_TRANSITIVITY), which is the file's standing guarantee that a
twin cannot drift.

PREDICTION: the node joins the LEQ-transitivity group and makes it FOUR
disciplines -- set inclusion, geospatial containment
(`geotop.predicates.containment_transitivity`), temporal precedence
(`temporal.order.precedence_transitivity`) and now propositional entailment.

VERDICT: **FIRED, at typed and at shape level.**

    IMPLIES⟨MEET⟨LEQ⟨?0:V, ?1:V⟩, LEQ⟨?1:V, ?2:V⟩⟩, LEQ⟨?0:V, ?2:V⟩⟩
      - geotop.predicates.containment_transitivity   (geospatial_topology)
      - logic.inference.hypothetical_syllogism       (logic)
      - settheory.order.subset_transitivity          (set_theory)
      - temporal.order.precedence_transitivity       (temporal_logic)

Worth distinguishing from the Boolean-law twins above. Those twin because logic
and set theory are literally one algebra, so the group is an identity of
theorem. This one spans four carriers -- propositions, sets, spatial regions,
instants -- that share nothing but *being ordered*, and it is the corpus's
clearest case of a form outliving its origin. It is also the cheapest result in
the graph: three of the four members were already present, and the fourth cost
one spec entry because the abstraction had been chosen correctly two corpora
earlier.

The pair also gets a reciprocal `equivalent_to` (CROSS_LAW_EQUIVALENT below).
Only the logic/set pair does: those two are one lattice statement over two
carriers, in exactly the sense the shared laws are, while containment and
precedence are analogies of order and stay in the matcher's report where
analogies belong.

Falsehood (docs/DESIGN-epistemic-ladder.md) is authored as a pair plus an
honest echo. BOT was already an algebraic constant here -- it is the right
side of the complement laws -- but nothing said what could be *done* with it.
Ex falso quodlibet `IMPLIES(BOT, PROP)` reads BOT forwards (from falsehood,
anything) and reductio ad absurdum `IMPLIES(IMPLIES(PROP, BOT), NEG(PROP))`
reads it backwards (what drives you to falsehood is refuted). Both are logic
nodes. The set side gets the order form `LEQ(BOT, ANYSET)` -- the empty set is
LEQ-minimal -- as a set-theory-only law, and that choice costs a twin on
purpose: transcribing the IMPLIES head into set theory would give
`∅^c ∪ A = U`, true in the powerset Boolean algebra but not a statement any
set theory is written in, so a same-template twin would have been manufactured
rather than found. `IMPLIES⟨?0:P, ?1:V⟩` and `LEQ⟨?0:P, ?1:V⟩` differ at the
head and the matcher reports no group -- correctly. The identity is real; it
lives one deduction-theorem step away from the templates, and that near miss
is recorded in both nodes' commentary instead of being engineered away.

Truth versus provability is made structural by `verified_by` (the schema's
optional bridge). VERIFIED_BY below maps a law name to the Lean 4 theorems in
`prover/sample_triples.json` that machine-check its propositional form, and
`build_node` injects the field on LOGIC nodes only: the extraction proves
`P Q : Prop` statements, so claiming the set readings on that evidence would
overstate what was checked (the Lindenbaum-Tarski/powerset transport is a
further theorem, not part of the artifact). Ten logic nodes carry a bridge,
covering all 16 extracted theorems (the quantifier De Morgan theorem
`not_forall_iff_exists_not` moved to `quantifier_negation_universal` when the
v0.10 quantifier slice authored the node that states exactly what it proves).
The falsehood pair and most quantifier laws carry none, which is the ladder's
VERIFIED-vs-PROVEN distinction showing up as a real gap rather than a slogan.

v0.10 adds a `quantification` topic to the logic corpus only: the classical
first-order laws that DEFINE the FORALL/EXISTS binder heads (instantiation,
generalization, the two quantifier De Morgan duals, the two valid
distribution laws, subalternation on an inhabited domain, and the ∃!
expansion). Binding is carried by slot recurrence — `FORALL⟨?0, PRED⟨?0⟩⟩` —
which the skeleton's first-occurrence numbering makes alpha-invariant, and
the schematic predicate slots are APPLIED slots in the calculus `F(ENDPOINT)`
sense. Logic-only on purpose: the set-theoretic reading of a quantifier is
comprehension/indexed union, a different statement family, so a set twin
would be manufactured rather than found.

Note on `statement_id`: the schema pattern `^[a-z0-9]+(\\.[a-z0-9_]+)+$`
forbids an underscore in the *first* segment, so set-theory ids are prefixed
`settheory.` even though the corpus directory and `discipline` field are
`set_theory`. Recorded in docs/BACKLOG.md.
"""

from __future__ import annotations

import json
import string
from pathlib import Path

# --------------------------------------------------------------------------
# Shared templates. One string per law, instantiated per discipline.
# --------------------------------------------------------------------------

TPL_DE_MORGAN = "NEG(MEET({a}, {b})) = JOIN(NEG({a}), NEG({b}))"
TPL_DISTRIBUTIVITY = "MEET({a}, JOIN({b}, {c})) = JOIN(MEET({a}, {b}), MEET({a}, {c}))"
TPL_INVOLUTION = "NEG(NEG({a})) = {a}"
TPL_ABSORPTION = "MEET({a}, JOIN({a}, {b})) = {a}"
TPL_IDENTITY = "MEET({a}, {top}) = {a}"
TPL_COMPLEMENT = "MEET({a}, NEG({a})) = {bot}"
TPL_IDEMPOTENCE = "MEET({a}, {a}) = {a}"

TPL_MODUS_PONENS = "IMPLIES(MEET(IMPLIES({a}, {b}), {a}), {b})"
TPL_CONTRAPOSITION = "IMPLIES({a}, {b}) = IMPLIES(NEG({b}), NEG({a}))"
# The falsehood pair. Stated bare, like modus ponens and unlike contraposition:
# these are valid schemas, not equations between two expressions, and the file's
# convention is that a rule keeps its IMPLIES root rather than being padded to
# `... = TOP`. (Padding would also render as `= UNIVERSE` on the set side, which
# is why the order form below is bare too.)
TPL_EX_FALSO = "IMPLIES({bot}, {a})"
TPL_REDUCTIO = "IMPLIES(IMPLIES({a}, {bot}), NEG({a}))"
TPL_BOTTOM_MINIMAL = "LEQ({bot}, {a})"
# One string, two carriers -- the same rule that makes De Morgan a twin. The
# set reading is inclusion transitivity and the logic reading is hypothetical
# syllogism over the Lindenbaum-Tarski order; they are one lattice statement,
# so they share one format string rather than two hand-kept copies.
TPL_ORDER_TRANSITIVITY = "IMPLIES(MEET(LEQ({a}, {b}), LEQ({b}, {c})), LEQ({a}, {c}))"
TPL_INCLUSION_EXCLUSION = (
    "CARD(JOIN({a}, {b})) = CARD({a}) + CARD({b}) - CARD(MEET({a}, {b}))"
)

# Quantifier templates (v0.10, logic-only). FORALL/EXISTS are ordinary call
# heads to the matcher: non-commutative, first argument the bound variable's
# slot, second the body. Binding structure is carried by slot RECURRENCE in
# the skeleton (`FORALL⟨?0, PRED⟨?0⟩⟩`), which the skeleton's first-occurrence
# placeholder numbering makes alpha-invariant with no new machinery. PRED and
# PREDB are slots APPLIED as call heads — the established `F(ENDPOINT)`
# pattern from calculus: schematic predicate letters, exactly as PROP1 is a
# schematic proposition letter in modus ponens, NOT first-class function
# values. Binder exchange (∀x∀y = ∀y∀x) is true in every model and
# deliberately NOT declared in the matcher's HEAD_ALGEBRA — the same honest
# under-declaration as associativity elsewhere: nothing in the corpus states
# it yet.
TPL_UNIVERSAL_INSTANTIATION = "IMPLIES(FORALL({x}, {p}({x})), {p}({t}))"
TPL_EXISTENTIAL_GENERALIZATION = "IMPLIES({p}({t}), EXISTS({x}, {p}({x})))"
TPL_NOT_FORALL = "NEG(FORALL({x}, {p}({x}))) = EXISTS({x}, NEG({p}({x})))"
TPL_NOT_EXISTS = "NEG(EXISTS({x}, {p}({x}))) = FORALL({x}, NEG({p}({x})))"
TPL_FORALL_MEET = ("FORALL({x}, MEET({p}({x}), {q}({x}))) = "
                   "MEET(FORALL({x}, {p}({x})), FORALL({x}, {q}({x})))")
TPL_EXISTS_JOIN = ("EXISTS({x}, JOIN({p}({x}), {q}({x}))) = "
                   "JOIN(EXISTS({x}, {p}({x})), EXISTS({x}, {q}({x})))")
TPL_FORALL_TO_EXISTS = "IMPLIES(FORALL({x}, {p}({x})), EXISTS({x}, {p}({x})))"
# The definiens of ∃!, stated bare like ex falso: unique existence has NO head
# of its own — the corpus expresses it only through this expansion, which is
# also Lean's own `ExistsUnique` definition and what licenses the coverage
# classifier's ∃!-desugar.
TPL_UNIQUE_EXISTENCE = ("EXISTS({x}, MEET({p}({x}), "
                        "FORALL({y}, IMPLIES({p}({y}), {y} = {x}))))")

# --------------------------------------------------------------------------
# Per-discipline vocabularies: slot names, categories, roles.
#
# Categories matter to the matcher: it collapses `syntactic_category` to
# P (parameter-like: parameter, constant) vs V (everything else). Propositions
# are `variable` and sets are `set`, both of which land in V, so the typed
# skeletons coincide. TOP/BOT are `constant` -> P in both corpora, which is
# right: they are fixed elements of the algebra, not free operands.
# --------------------------------------------------------------------------

LOGIC_VOCAB = {"a": "PROP1", "b": "PROP2", "c": "PROP3",
               "top": "TRUTH", "bot": "FALSITY",
               # quantifier vocabulary (logic-only templates): bound variables,
               # schematic predicate letters, and an instantiating term. All
               # `variable` category -> V in the matcher's typed skeletons.
               "x": "VAR1", "y": "VAR2", "p": "PRED", "q": "PREDB",
               "t": "TERM1"}
LOGIC_CATS = {"a": "variable", "b": "variable", "c": "variable",
              "top": "constant", "bot": "constant",
              "x": "variable", "y": "variable", "p": "variable",
              "q": "variable", "t": "variable"}
LOGIC_ROLES = {"a": "propositional_operand", "b": "propositional_operand",
               "c": "propositional_operand",
               "top": "top_element", "bot": "bottom_element",
               "x": "bound_individual_variable",
               "y": "bound_individual_variable",
               "p": "predicate_operand", "q": "predicate_operand",
               "t": "instantiating_term"}

SET_VOCAB = {"a": "SETA", "b": "SETB", "c": "SETC",
             "top": "UNIVERSE", "bot": "EMPTYSET"}
SET_CATS = {"a": "set", "b": "set", "c": "set",
            "top": "constant", "bot": "constant"}
SET_ROLES = {"a": "set_operand", "b": "set_operand", "c": "set_operand",
             "top": "top_element", "bot": "bottom_element"}

VOCAB = {"logic": (LOGIC_VOCAB, LOGIC_CATS, LOGIC_ROLES),
         "set_theory": (SET_VOCAB, SET_CATS, SET_ROLES)}

ID_PREFIX = {"logic": "logic", "set_theory": "settheory"}


def tpl_keys(tpl: str) -> list[str]:
    """Format keys of a template, first-appearance order, de-duplicated."""
    seen: list[str] = []
    for _, key, _, _ in string.Formatter().parse(tpl):
        if key and key not in seen:
            seen.append(key)
    return seen


def render(tpl: str, discipline: str) -> str:
    return tpl.format(**VOCAB[discipline][0])


def slots_for(tpl: str, discipline: str) -> list[dict]:
    vocab, cats, roles = VOCAB[discipline]
    return [{"slot_id": vocab[k], "syntactic_category": cats[k],
             "semantic_role": roles[k]} for k in tpl_keys(tpl)]


# --------------------------------------------------------------------------
# Lexicon fragments
# --------------------------------------------------------------------------


def sym(s, cat, role, desc, order=0):
    return {"symbol": s, "syntactic_category": cat, "semantic_role": role,
            "mathematical_order": order, "description": desc}


def op(symbol, name, arity, family):
    return {"symbol": symbol, "name": name, "arity": arity,
            "operator_family": family}


EQ = op("=", "equality of algebra elements", 2, "relational")
LOG_EQUIV = op("=", "logical equivalence (interderivability)", 2, "relational")
AND = op("and", "conjunction", 2, "logical")
OR = op("or", "disjunction", 2, "logical")
NOT = op("not", "negation", 1, "logical")
IMPL = op("implies", "material implication", 2, "logical")
TURNSTILE = op("|-", "derivability", 2, "logical")

INTER = op("inter", "set intersection", 2, "set_theoretic")
UNION = op("union", "set union", 2, "set_theoretic")
COMPL = op("^c", "set complement relative to the universe", 1, "set_theoretic")
SUBSET = op("subset", "subset inclusion", 2, "set_theoretic")
PLUS = op("+", "addition of cardinals", 2, "arithmetic")
MINUS = op("-", "subtraction of cardinals", 2, "arithmetic")

# Propositions and sets: the two carriers of the same lattice.
P_SYMS = [sym("P", "variable", "propositional_operand",
              "An arbitrary proposition (well-formed formula) of the object language."),
          sym("Q", "variable", "propositional_operand",
              "A second arbitrary proposition, independent of P."),
          sym("R", "variable", "propositional_operand",
              "A third arbitrary proposition.")]

# Quantifier-node symbols: schematic predicate letters, bound variables, and
# an instantiating term. F and G are schematic in exactly the sense P and Q
# are — metavariables of the schema, not first-class function values.
PRED_SYM = sym("F", "variable", "predicate_operand",
               "An arbitrary unary predicate over the domain of discourse — a "
               "schematic letter like modus ponens' P, not a first-class "
               "function value.")
PREDB_SYM = sym("G", "variable", "predicate_operand",
                "A second arbitrary unary predicate, independent of F.")
VAR_SYM = sym("x", "variable", "bound_individual_variable",
              "The bound individual variable, ranging over the domain of "
              "discourse; it has no free occurrence in the whole statement.")
VAR2_SYM = sym("y", "variable", "bound_individual_variable",
               "A second bound individual variable, for the inner binder.")
TERM_SYM = sym("t", "variable", "instantiating_term",
               "An arbitrary term of the domain, free for x in F (no variable "
               "of t may be captured by a binder of F).")

FORALL_OP = op("forall", "universal quantifier (binder)", 2, "logical")
EXISTS_OP = op("exists", "existential quantifier (binder)", 2, "logical")
EXISTS_UNIQUE_OP = op("exists!", "unique existence (defined binder)", 2, "logical")
A_SYMS = [sym("A", "set", "set_operand",
              "An arbitrary subset of the ambient universe U."),
          sym("B", "set", "set_operand",
              "A second arbitrary subset of U."),
          sym("C", "set", "set_operand",
              "A third arbitrary subset of U.")]

TRUE_CONST = {"symbol": "true", "value": True,
              "description": "The verum: the greatest element of the "
                             "propositional lattice, entailed by every formula."}
FALSE_CONST = {"symbol": "false", "value": False,
               "description": "The falsum: the least element of the "
                              "propositional lattice, entailing every formula."}
UNIVERSE_CONST = {"symbol": "U",
                  "description": "The universe of discourse: the greatest element "
                                 "of the powerset lattice, containing every set "
                                 "under consideration."}
EMPTY_CONST = {"symbol": "emptyset",
               "description": "The empty set: the least element of the powerset "
                              "lattice, contained in every set."}

# Template-level lattice heads. These are deliberately recorded as
# `functionals` rather than `operators`: they are not notation any textbook
# writes, they are the abstraction the template uses so that both disciplines
# land on one skeleton. Their descriptions carry the translation table.
LATTICE_FN = {
    "MEET": {"notation": "MEET(.,.)", "name": "lattice meet", "input_arity": 2,
             "description": "Greatest lower bound in the Boolean lattice. "
                            "Realized as conjunction in data/logic and as "
                            "intersection in data/set_theory."},
    "JOIN": {"notation": "JOIN(.,.)", "name": "lattice join", "input_arity": 2,
             "description": "Least upper bound in the Boolean lattice. Realized "
                            "as disjunction in data/logic and as union in "
                            "data/set_theory."},
    "NEG": {"notation": "NEG(.)", "name": "lattice complement", "input_arity": 1,
            "description": "Boolean complement. Realized as negation in "
                           "data/logic and as relative complement in "
                           "data/set_theory."},
    "LEQ": {"notation": "LEQ(.,.)", "name": "lattice order", "input_arity": 2,
            "description": "The partial order x <= y, equivalently MEET(x, y) = x. "
                           "Realized as entailment in data/logic and as subset "
                           "inclusion in data/set_theory."},
    "IMPLIES": {"notation": "IMPLIES(.,.)", "name": "implication",
                "input_arity": 2,
                "description": "Material implication where the statement is an "
                               "object-language formula, and the meta-level "
                               "'if ... then' where the statement is a rule."},
    "CARD": {"notation": "CARD(.)", "name": "cardinality", "input_arity": 1,
             "codomain": "non-negative integers",
             "description": "Number of elements of a finite set; the measure "
                            "that turns lattice statements into counting ones."},
    "FORALL": {"notation": "FORALL(.,.)", "name": "universal quantification",
               "input_arity": 2,
               "description": "The universal binder: FORALL(x, B) holds when "
                              "the body B holds of every element of the domain "
                              "of discourse substituted for the bound variable "
                              "x. First argument the bound variable's slot, "
                              "second the body; binding is carried by slot "
                              "recurrence. Semantically the infinitary MEET of "
                              "the body's instances, which is why it "
                              "distributes over MEET and dualizes to EXISTS "
                              "under NEG. The head does NOT carry the binder's "
                              "domain — the slot_schema does, as for every "
                              "other slot."},
    "EXISTS": {"notation": "EXISTS(.,.)", "name": "existential quantification",
               "input_arity": 2,
               "description": "The existential binder: EXISTS(x, B) holds when "
                              "some element of the domain of discourse "
                              "satisfies the body B. Same argument convention "
                              "as FORALL. Semantically the infinitary JOIN of "
                              "the body's instances, which is why it "
                              "distributes over JOIN and dualizes to FORALL "
                              "under NEG. Unique existence has no head of its "
                              "own; it is expressed only through the "
                              "unique_existence_expansion definiens."},
}


def fns(*names, codomain_override=None):
    out = []
    for n in names:
        entry = dict(LATTICE_FN[n])
        if (n in {"MEET", "JOIN", "NEG", "LEQ", "IMPLIES", "FORALL", "EXISTS"}
                and codomain_override):
            entry["codomain"] = codomain_override
        out.append(entry)
    return out


LOGIC_CODOMAIN = "propositions modulo logical equivalence"
SET_CODOMAIN = "subsets of the universe U"

# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------

BOOLE = {"citation_key": "boole1854",
         "bibliographic_entry": "Boole, G. (1854). An Investigation of the Laws of Thought, on Which Are Founded the Mathematical Theories of Logic and Probabilities. London: Walton and Maberly."}
DE_MORGAN = {"citation_key": "demorgan1847",
             "bibliographic_entry": "De Morgan, A. (1847). Formal Logic: or, The Calculus of Inference, Necessary and Probable. London: Taylor and Walton."}
HUNTINGTON = {"citation_key": "huntington1904",
              "bibliographic_entry": "Huntington, E. V. (1904). Sets of Independent Postulates for the Algebra of Logic. Transactions of the American Mathematical Society, 5(3), 288-309."}
BIRKHOFF = {"citation_key": "birkhoff1967",
            "bibliographic_entry": "Birkhoff, G. (1967). Lattice Theory (3rd ed.). AMS Colloquium Publications 25. Providence: American Mathematical Society."}
DAVEY_PRIESTLEY = {"citation_key": "davey2002",
                   "bibliographic_entry": "Davey, B. A., Priestley, H. A. (2002). Introduction to Lattices and Order (2nd ed.). Cambridge: Cambridge University Press."}
STONE = {"citation_key": "stone1936",
         "bibliographic_entry": "Stone, M. H. (1936). The Theory of Representations for Boolean Algebras. Transactions of the American Mathematical Society, 40(1), 37-111."}
ENDERTON_LOGIC = {"citation_key": "enderton2001",
                  "bibliographic_entry": "Enderton, H. B. (2001). A Mathematical Introduction to Logic (2nd ed.). San Diego: Academic Press."}
MENDELSON = {"citation_key": "mendelson2015",
             "bibliographic_entry": "Mendelson, E. (2015). Introduction to Mathematical Logic (6th ed.). Boca Raton: CRC Press."}
ARISTOTLE = {"citation_key": "aristotle_priora",
             "bibliographic_entry": "Aristotle (c. 350 BCE). Prior Analytics. Translated by A. J. Jenkinson, in The Complete Works of Aristotle (J. Barnes, ed., 1984). Princeton: Princeton University Press."}
FREGE = {"citation_key": "frege1879",
         "bibliographic_entry": "Frege, G. (1879). Begriffsschrift, eine der arithmetischen nachgebildete Formelsprache des reinen Denkens. Halle: Louis Nebert."}
PRINCIPIA = {"citation_key": "whitehead1910",
             "bibliographic_entry": "Whitehead, A. N., Russell, B. (1910). Principia Mathematica, Volume I. Cambridge: Cambridge University Press."}
GENTZEN = {"citation_key": "gentzen1935",
           "bibliographic_entry": "Gentzen, G. (1935). Untersuchungen ueber das logische Schliessen I. Mathematische Zeitschrift, 39(1), 176-210."}
HEYTING = {"citation_key": "heyting1930",
           "bibliographic_entry": "Heyting, A. (1930). Die formalen Regeln der intuitionistischen Logik. Sitzungsberichte der Preussischen Akademie der Wissenschaften, Physikalisch-mathematische Klasse, 42-56."}
HALMOS = {"citation_key": "halmos1960",
          "bibliographic_entry": "Halmos, P. R. (1960). Naive Set Theory. Princeton: D. Van Nostrand."}
ENDERTON_SETS = {"citation_key": "enderton1977",
                 "bibliographic_entry": "Enderton, H. B. (1977). Elements of Set Theory. New York: Academic Press."}
JECH = {"citation_key": "jech2003",
        "bibliographic_entry": "Jech, T. (2003). Set Theory (3rd millennium ed.). Berlin: Springer."}
KUNEN = {"citation_key": "kunen1980",
         "bibliographic_entry": "Kunen, K. (1980). Set Theory: An Introduction to Independence Proofs. Amsterdam: North-Holland."}
STANLEY = {"citation_key": "stanley2011",
           "bibliographic_entry": "Stanley, R. P. (2011). Enumerative Combinatorics, Volume 1 (2nd ed.). Cambridge: Cambridge University Press."}
ROTA = {"citation_key": "rota1964",
        "bibliographic_entry": "Rota, G.-C. (1964). On the Foundations of Combinatorial Theory I: Theory of Moebius Functions. Zeitschrift fuer Wahrscheinlichkeitstheorie und Verwandte Gebiete, 2(4), 340-368."}
KOLMOGOROV = {"citation_key": "kolmogorov1933",
              "bibliographic_entry": "Kolmogorov, A. N. (1933). Grundbegriffe der Wahrscheinlichkeitsrechnung. Ergebnisse der Mathematik 2(3). Berlin: Springer."}
MATHLIB = {"citation_key": "mathlib2020",
           "bibliographic_entry": "The mathlib Community (2020). The Lean Mathematical Library. Proceedings of the 9th ACM SIGPLAN International Conference on Certified Programs and Proofs (CPP 2020), 367-381.",
           "url": "https://doi.org/10.1145/3372885.3373824"}
PRIEST = {"citation_key": "priest1979",
          "bibliographic_entry": "Priest, G. (1979). The Logic of Paradox. Journal of Philosophical Logic, 8(1), 219-241."}

# --------------------------------------------------------------------------
# The prover bridge: truth (a corpus node) versus provability (a machine-
# checked artifact), made structural.
#
# `prover/sample_triples.json` holds 155 tactic steps extracted from 16 Lean 4
# theorems over `P Q R : Prop` (prover/PHASE1_NOTES.md records the extraction
# and the theorem -> node mapping). Several theorems land on one law, because
# a law here states a self-dual pair while Lean proves each half separately.
# The quantifier form `not_forall_iff_exists_not` belongs to
# quantifier_negation_universal since the v0.10 quantifier slice.
#
# Injected on LOGIC nodes only. The Lean statements quantify over `Prop`; the
# powerset reading follows by Stone/Lindenbaum-Tarski transport, which is a
# further theorem and is *not* in the artifact. Claiming it on the set nodes
# would be asserting more verification than was performed.
# --------------------------------------------------------------------------

LEAN_ARTIFACT = "prover/sample_triples.json"


def lean(*theorems: str) -> list[dict]:
    return [{"system": "lean4", "artifact": LEAN_ARTIFACT,
             "reference": f"BooleanLaws.{t}"} for t in theorems]


VERIFIED_BY = {
    # `not_forall_iff_exists_not` moved from de_morgan_laws to the
    # quantifier_negation_universal node the moment a node existed stating
    # exactly what the theorem proves (v0.10 quantifier slice). The merged
    # graph requires each reference to resolve to exactly one node.
    "de_morgan_laws": lean("de_morgan_not_and", "de_morgan_not_or"),
    "quantifier_negation_universal": lean("not_forall_iff_exists_not"),
    "distributivity_meet_over_join": lean("distrib_and_or", "distrib_or_and"),
    "double_negation": lean("double_negation"),
    "absorption": lean("absorption_and_or", "absorption_or_and"),
    "identity_laws": lean("identity_and_true", "identity_or_false"),
    "complement_laws": lean("non_contradiction", "excluded_middle"),
    "idempotence": lean("idempotence_and", "idempotence_or"),
    "modus_ponens": lean("modus_ponens"),
    "contraposition": lean("contraposition"),
}


def check_verified_by() -> str:
    """Fail regeneration if the bridge and the artifact have drifted apart."""
    referenced = {e["reference"] for entries in VERIFIED_BY.values()
                  for e in entries}
    path = Path(LEAN_ARTIFACT)
    if not path.exists():
        return f"{len(referenced)} references (artifact not present; unchecked)"
    proved = {t["theorem"] for t in json.loads(path.read_text(encoding="utf-8"))}
    dangling = sorted(referenced - proved)
    unclaimed = sorted(proved - referenced)
    if dangling:
        raise SystemExit(f"verified_by references no such Lean theorem: {dangling}")
    if unclaimed:
        raise SystemExit(f"Lean theorems no corpus node claims: {unclaimed}")
    return f"{len(referenced)} of {len(proved)} extracted Lean theorems claimed"


# --------------------------------------------------------------------------
# Law specifications. `logic` and `set_theory` sub-dicts differ only in
# notation and commentary; template, archetype, class and lineage are shared,
# which is what guarantees the twins.
# --------------------------------------------------------------------------

SHARED_LAWS = [
    {
        "name": "de_morgan_laws",
        "topic_id": "boolean_laws",
        "archetype": "de_morgan_duality",
        "cls": "identity",
        "status": "derived",
        "template": TPL_DE_MORGAN,
        "entailed_by": ["distributivity_meet_over_join", "identity_laws",
                        "complement_laws"],
        "invariants": [
            "Self-dual as a pair: swapping MEET with JOIN and TOP with BOT maps "
            "the stated form onto its dual, so one line of the pair proves the "
            "other for free.",
            "NEG is an order-reversing bijection (an antitone involution), which "
            "is the single fact the law encodes.",
            "Both sides are symmetric under exchanging the two operands.",
            "Generalizes verbatim to arbitrary arities and, in a complete "
            "Boolean algebra, to infinite meets and joins.",
        ],
        "logic": {
            "title": "De Morgan's Laws (Propositional Form)",
            "ascii": "not(P and Q) = (not P) or (not Q)",
            "latex": "\\lnot(P \\land Q) \\equiv \\lnot P \\lor \\lnot Q",
            "forms": [
                {"form_id": "dual", "notation_system": "ascii",
                 "expression": "not(P or Q) = (not P) and (not Q)",
                 "scope_note": "The dual law; the two are interderivable by double negation"},
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "¬(P ∧ Q) ≡ ¬P ∨ ¬Q",
                 "scope_note": "Standard connective notation"},
                {"form_id": "quantifier", "notation_system": "ascii",
                 "expression": "not(forall x. F(x)) = exists x. not F(x)",
                 "scope_note": "First-order form; the quantifiers are the infinitary meet and join"},
                {"form_id": "nand_basis", "notation_system": "ascii",
                 "expression": "P nand Q = (not P) or (not Q)",
                 "scope_note": "Reading that makes NAND functionally complete"},
            ],
            "meaning": "Denying that two things hold together is exactly asserting that "
                       "at least one of them fails; negation trades conjunction for "
                       "disjunction and back.",
            "significance": "The corpus's flagship cross-discipline twin. Its skeleton "
                            "`JOIN⟨NEG⟨?0:V⟩, NEG⟨?1:V⟩⟩ = NEG⟨MEET⟨?0:V, ?1:V⟩⟩` is "
                            "shared character for character with "
                            "settheory.boolean_laws.de_morgan_laws, and unlike the "
                            "exponential twins that span finance, calculus and "
                            "chemistry, this one is not an analogy between unrelated "
                            "subject matters: both nodes state one theorem of one "
                            "Boolean algebra, read once over propositions and once over "
                            "subsets. The `equivalent_to` edge between them is therefore "
                            "literal, not aspirational.",
            "conditions": ["Classical two-valued semantics",
                           "Negation is an involution (see double_negation)",
                           "Connectives are truth-functional"],
            "failure_modes": [
                "Only one direction survives intuitionistically: not(P or Q) -> "
                "(not P) and (not Q) is constructive, while not(P and Q) -> "
                "(not P) or (not Q) is not, since it would decide which conjunct fails.",
                "Fails in quantum logic, where the lattice of propositions is "
                "orthomodular but not distributive.",
                "In natural language the scope of 'not' is ambiguous, so the law is "
                "routinely misapplied to sentences whose parse is not the intended one.",
            ],
            "provenance": [DE_MORGAN, BOOLE, ENDERTON_LOGIC, MENDELSON],
            "keywords": ["De Morgan", "duality", "negation", "Boolean lattice",
                         "propositional logic"],
            "ops": [LOG_EQUIV, AND, OR, NOT],
        },
        "set_theory": {
            "title": "De Morgan's Laws (Set Form)",
            "ascii": "complement(A inter B) = complement(A) union complement(B)",
            "latex": "(A \\cap B)^{c} = A^{c} \\cup B^{c}",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "(A ∩ B)^c = A^c ∪ B^c",
                 "scope_note": "Standard set notation, complement taken in U"},
                {"form_id": "dual", "notation_system": "ascii",
                 "expression": "(A ∪ B)^c = A^c ∩ B^c",
                 "scope_note": "The dual law"},
                {"form_id": "relative", "notation_system": "ascii",
                 "expression": "X \\ (A inter B) = (X \\ A) union (X \\ B)",
                 "scope_note": "Relative-difference form, valid without a fixed universe"},
                {"form_id": "sigma_algebra", "notation_system": "measure_theoretic",
                 "expression": "(union_i A_i)^c = inter_i A_i^c",
                 "scope_note": "Countable form; why a sigma-algebra closed under complement and countable union is closed under countable intersection"},
            ],
            "meaning": "The complement of an intersection is the union of the "
                       "complements: a point misses the overlap exactly when it misses "
                       "at least one of the sets.",
            "significance": "Exact typed twin of logic.boolean_laws.de_morgan_laws. The "
                            "two templates are generated from one shared format string "
                            "in scripts/seed_logic.py, so the skeleton "
                            "`JOIN⟨NEG⟨?0:V⟩, NEG⟨?1:V⟩⟩ = NEG⟨MEET⟨?0:V, ?1:V⟩⟩` is "
                            "identical by construction rather than by luck. The set "
                            "form is also the workhorse of measure theory: closure of a "
                            "sigma-algebra under countable intersection is this law plus "
                            "closure under complement, which is why the probability "
                            "corpus can assume it silently.",
            "conditions": ["A fixed ambient universe U relative to which complements are taken",
                           "A and B are subsets of that same U"],
            "failure_modes": [
                "Absolute complements do not exist in ZFC: {x : x not-in A} is a proper "
                "class, so the law must be stated relative to a set U or as a difference.",
                "Changing the universe changes both sides; comparing complements taken "
                "in different universes is the commonest error in practice.",
            ],
            "provenance": [DE_MORGAN, HALMOS, ENDERTON_SETS, KOLMOGOROV],
            "keywords": ["De Morgan", "complement", "intersection", "union",
                         "sigma-algebra", "Boolean lattice"],
            "ops": [EQ, INTER, UNION, COMPL],
        },
    },
    {
        "name": "distributivity_meet_over_join",
        "topic_id": "boolean_laws",
        "archetype": "meet_distributes_over_join",
        "cls": "axiom",
        "status": "formal",
        "template": TPL_DISTRIBUTIVITY,
        "entails": ["de_morgan_laws", "absorption", "double_negation", "idempotence"],
        "invariants": [
            "One operand is repeated on the right, so the law is not a rearrangement "
            "but a duplication: it is what separates distributive lattices from "
            "general ones.",
            "Self-dual: the same statement with MEET and JOIN exchanged also holds, and "
            "in a lattice each of the two implies the other.",
            "Fails in the smallest non-distributive lattices M3 and N5; a lattice is "
            "distributive exactly when neither embeds in it.",
            "Symmetric in the two distributed operands but not in the distributing one.",
        ],
        "logic": {
            "title": "Distributivity of Conjunction over Disjunction",
            "ascii": "P and (Q or R) = (P and Q) or (P and R)",
            "latex": "P \\land (Q \\lor R) \\equiv (P \\land Q) \\lor (P \\land R)",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "P ∧ (Q ∨ R) ≡ (P ∧ Q) ∨ (P ∧ R)"},
                {"form_id": "dual", "notation_system": "ascii",
                 "expression": "P or (Q and R) = (P or Q) and (P or R)",
                 "scope_note": "Disjunction over conjunction; equivalent in any lattice"},
                {"form_id": "normal_form", "notation_system": "ascii",
                 "expression": "any formula = or_i (and_j literal_ij)",
                 "scope_note": "Repeated application is exactly the conversion to disjunctive normal form"},
            ],
            "meaning": "A conjunction with an alternative inside it can be pushed out "
                       "into an alternative of conjunctions, and back.",
            "significance": "One of Huntington's postulates, and the reason normal forms "
                            "exist: DNF/CNF conversion is nothing but this law applied "
                            "until it stops. Its typed twin in the set corpus is "
                            "intersection over union; the exponential blow-up that makes "
                            "CNF conversion expensive in SAT solving is the same "
                            "duplication that makes the set form grow the number of "
                            "intersection terms.",
            "conditions": ["Classical propositional semantics",
                           "The lattice of propositions is distributive"],
            "failure_modes": [
                "Quantum logic drops exactly this law: the lattice of closed subspaces "
                "of a Hilbert space is orthomodular, not distributive, which is Birkhoff "
                "and von Neumann's formalization of complementarity.",
                "Naive repeated application is exponential in formula size, which is why "
                "practical CNF conversion introduces fresh variables (Tseitin) instead.",
            ],
            "provenance": [HUNTINGTON, BOOLE, BIRKHOFF, ENDERTON_LOGIC],
            "keywords": ["distributivity", "normal form", "Huntington postulate",
                         "distributive lattice"],
            "ops": [LOG_EQUIV, AND, OR],
        },
        "set_theory": {
            "title": "Distributivity of Intersection over Union",
            "ascii": "A inter (B union C) = (A inter B) union (A inter C)",
            "latex": "A \\cap (B \\cup C) = (A \\cap B) \\cup (A \\cap C)",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)"},
                {"form_id": "dual", "notation_system": "ascii",
                 "expression": "A ∪ (B ∩ C) = (A ∪ B) ∩ (A ∪ C)"},
                {"form_id": "indexed", "notation_system": "ascii",
                 "expression": "A inter (union_i B_i) = union_i (A inter B_i)",
                 "scope_note": "Arbitrary-index form; holds for any family, not just finite ones"},
            ],
            "meaning": "Intersecting with a union distributes across that union: a point "
                       "is in A and in one of B, C exactly when it is in A-and-B or in A-and-C.",
            "significance": "The powerset reading of the same Huntington postulate, and "
                            "an exact typed twin of the propositional form. Worth noting "
                            "what the twin buys: the *proof* is one proof. Membership "
                            "unfolds `x ∈ A ∩ (B ∪ C)` into `x ∈ A and (x ∈ B or x ∈ C)`, "
                            "at which point the set law is the propositional law applied "
                            "pointwise. The Lindenbaum-Tarski/powerset correspondence is "
                            "not decoration on this pair; it is the derivation.",
            "conditions": ["A, B, C are sets (no universe needed: no complement appears)"],
            "failure_modes": [
                "The unrestricted-index dual A ∪ (∩_i B_i) = ∩_i (A ∪ B_i) needs the "
                "family to be non-empty; over an empty family the intersection is not a set.",
                "Analogous distributivity fails for cartesian product over difference in "
                "the way beginners expect, so the law should not be transplanted to other "
                "set operations by pattern-matching.",
            ],
            "provenance": [HUNTINGTON, HALMOS, ENDERTON_SETS, DAVEY_PRIESTLEY],
            "keywords": ["distributivity", "intersection", "union",
                         "distributive lattice", "algebra of sets"],
            "ops": [EQ, INTER, UNION],
        },
    },
    {
        "name": "double_negation",
        "topic_id": "boolean_laws",
        "archetype": "complement_involution",
        "cls": "identity",
        "status": "derived",
        "template": TPL_INVOLUTION,
        "entailed_by": ["complement_laws", "distributivity_meet_over_join",
                        "identity_laws"],
        "invariants": [
            "NEG is an involution: applying it twice is the identity map, so it is its "
            "own inverse and a bijection of the algebra onto itself.",
            "Order-reversing, hence an anti-automorphism: it exchanges TOP with BOT and "
            "MEET with JOIN, which is the source of every duality in this corpus.",
            "The complement of an element is unique in a distributive lattice, which is "
            "what makes the two-sided statement well posed.",
            "Only one free element appears, twice: the law is about the operator, not "
            "about any relation between operands.",
        ],
        "logic": {
            "title": "Double Negation Elimination",
            "ascii": "not(not P) = P",
            "latex": "\\lnot\\lnot P \\equiv P",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "¬¬P ≡ P"},
                {"form_id": "introduction_only", "notation_system": "ascii",
                 "expression": "P implies not(not P)",
                 "scope_note": "The half that is intuitionistically valid"},
                {"form_id": "elimination_only", "notation_system": "ascii",
                 "expression": "not(not P) implies P",
                 "scope_note": "The classical half; equivalent to excluded middle and to reductio"},
            ],
            "meaning": "Denying a denial returns the original assertion; negation is its "
                       "own inverse.",
            "significance": "The smallest node in either corpus and one of the sharpest "
                            "twins: `?0:V = NEG⟨NEG⟨?0:V⟩⟩` in logic and in set theory "
                            "alike. It is also the corpus's cleanest example of a law "
                            "whose *status* is discipline-dependent while its *form* is "
                            "not: intuitionistically the propositional reading is exactly "
                            "what fails, while the set reading survives untouched because "
                            "the powerset of a set is a Boolean algebra regardless of the "
                            "metatheory's logic. Same skeleton, different frontier.",
            "conditions": ["Classical (Boolean) semantics",
                           "Negation defined by the complement laws"],
            "failure_modes": [
                "Intuitionistic and constructive logics reject the elimination direction; "
                "assuming it is equivalent to assuming excluded middle, which is why "
                "proof assistants make `Classical.byContradiction` an explicit axiom.",
                "In many-valued and fuzzy logics the negation need not be involutive at all.",
            ],
            "provenance": [BOOLE, PRINCIPIA, HEYTING, ENDERTON_LOGIC, MATHLIB],
            "keywords": ["double negation", "involution", "classical logic",
                         "intuitionism"],
            "ops": [LOG_EQUIV, NOT],
        },
        "set_theory": {
            "title": "Double Complement (Involution of Complement)",
            "ascii": "complement(complement(A)) = A",
            "latex": "(A^{c})^{c} = A",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "(A^c)^c = A"},
                {"form_id": "relative", "notation_system": "ascii",
                 "expression": "U \\ (U \\ A) = A",
                 "scope_note": "Complement as relative difference, requires A subset U"},
            ],
            "meaning": "Taking the complement of a complement returns the original set: "
                       "the points not outside A are exactly the points in A.",
            "significance": "Exact typed twin of double negation elimination, and the "
                            "reason De Morgan's two dual forms are interderivable in "
                            "either corpus: complement each side and apply this law. "
                            "Where the propositional version is the contested boundary "
                            "between classical and constructive logic, the set version is "
                            "uncontroversial as long as U is fixed, which is a useful "
                            "reminder that structural identity of statements does not "
                            "imply identity of their epistemic risk.",
            "conditions": ["A is a subset of the fixed universe U",
                           "Complement taken relative to that same U on both applications"],
            "failure_modes": [
                "Silently switching universes between the two complements breaks it; the "
                "expression is only well formed with U fixed.",
                "In a constructive/topos setting the subobject lattice is a Heyting "
                "algebra, and double complement is a closure operator rather than the "
                "identity (it lands on the regular subobjects only).",
            ],
            "provenance": [HALMOS, ENDERTON_SETS, DAVEY_PRIESTLEY, JECH],
            "keywords": ["complement", "involution", "algebra of sets", "duality"],
            "ops": [EQ, COMPL],
        },
    },
    {
        "name": "absorption",
        "topic_id": "boolean_laws",
        "archetype": "lattice_absorption",
        "cls": "identity",
        "status": "derived",
        "template": TPL_ABSORPTION,
        "entailed_by": ["distributivity_meet_over_join", "identity_laws"],
        "invariants": [
            "The second operand vanishes from the result entirely, so the law is a "
            "genuine simplification, not a rearrangement.",
            "Equivalent to the order statement MEET(x, y) = x iff JOIN(x, y) = y; "
            "absorption is what ties the two operations to one partial order.",
            "Holds in every lattice, distributive or not, and together with "
            "commutativity, associativity and idempotence it *characterizes* lattices "
            "algebraically -- the order can be recovered from the equations.",
            "Self-dual: JOIN(x, MEET(x, y)) = x is the same law with the operations "
            "exchanged.",
        ],
        "logic": {
            "title": "Absorption Law (Conjunction over Disjunction)",
            "ascii": "P and (P or Q) = P",
            "latex": "P \\land (P \\lor Q) \\equiv P",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "P ∧ (P ∨ Q) ≡ P"},
                {"form_id": "dual", "notation_system": "ascii",
                 "expression": "P or (P and Q) = P",
                 "scope_note": "Dual absorption"},
                {"form_id": "order_form", "notation_system": "ascii",
                 "expression": "P entails (P or Q)",
                 "scope_note": "The order fact absorption is an equational restatement of"},
            ],
            "meaning": "Adding an alternative that is already implied by P, and then "
                       "requiring P as well, tells you nothing beyond P.",
            "significance": "The law that makes the two connectives describe a single "
                            "order rather than two unrelated operations, and the reason "
                            "Q may be discarded outright when simplifying formulas. Its "
                            "set twin `A ∩ (A ∪ B) = A` is the same equation; the "
                            "skeleton `?0:V = MEET⟨?0:V, JOIN⟨?0:V, ?1:V⟩⟩` has one slot "
                            "appearing three times, which is why nothing else in the "
                            "corpus comes close to it structurally.",
            "conditions": ["Lattice semantics for `and`/`or`; distributivity not required"],
            "failure_modes": [
                "The natural-language reading invites the mistake that Q is irrelevant to "
                "the *argument*, when it is only irrelevant to the truth value.",
                "Fails for non-idempotent 'conjunctions' such as those in linear logic or "
                "in resource-sensitive/substructural systems, where multiplicities matter.",
            ],
            "provenance": [BIRKHOFF, DAVEY_PRIESTLEY, HUNTINGTON, MENDELSON],
            "keywords": ["absorption", "lattice", "simplification", "order"],
            "ops": [LOG_EQUIV, AND, OR],
        },
        "set_theory": {
            "title": "Absorption Law (Intersection over Union)",
            "ascii": "A inter (A union B) = A",
            "latex": "A \\cap (A \\cup B) = A",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "A ∩ (A ∪ B) = A"},
                {"form_id": "dual", "notation_system": "ascii",
                 "expression": "A ∪ (A ∩ B) = A"},
                {"form_id": "order_form", "notation_system": "ascii",
                 "expression": "A subset (A union B)",
                 "scope_note": "The inclusion the equation encodes"},
            ],
            "meaning": "Enlarging A by B and then intersecting back with A recovers A "
                       "exactly: the detour through B adds nothing.",
            "significance": "Exact typed twin of propositional absorption. It is also the "
                            "reason the powerset order can be *defined* from either "
                            "operation -- A ⊆ B iff A ∩ B = A iff A ∪ B = B -- which is "
                            "the set-theoretic content of the LEQ head this corpus uses in "
                            "settheory.order.subset_transitivity.",
            "conditions": ["A and B are sets; no universe or complement needed"],
            "failure_modes": [
                "Multisets and bags break it: with multiplicities, absorption fails "
                "because union and intersection stop being idempotent.",
                "Fuzzy sets under min/max keep absorption, but under other t-norm/t-conorm "
                "pairs (product, Lukasiewicz) it fails, so 'set-like' is not enough.",
            ],
            "provenance": [BIRKHOFF, DAVEY_PRIESTLEY, HALMOS, ENDERTON_SETS],
            "keywords": ["absorption", "lattice", "subset order", "algebra of sets"],
            "ops": [EQ, INTER, UNION],
        },
    },
    {
        "name": "identity_laws",
        "topic_id": "boolean_laws",
        "archetype": "identity_element_law",
        "cls": "axiom",
        "status": "formal",
        "template": TPL_IDENTITY,
        "entails": ["de_morgan_laws", "absorption", "double_negation", "idempotence"],
        "invariants": [
            "TOP is a two-sided identity for MEET, and dually BOT is one for JOIN; being "
            "an identity is what *defines* these two constants.",
            "The only law here in which a constant slot (P-category) appears, which is "
            "why the typed skeleton `?0:V = MEET⟨?0:V, ?1:P⟩` differs in kind from the "
            "all-variable laws.",
            "Identities are unique: any two elements both acting as identities for MEET "
            "are equal, so TOP is determined by the law rather than posited alongside it.",
            "Combined with the complement laws it makes the lattice bounded and "
            "complemented, i.e. Boolean.",
        ],
        "logic": {
            "title": "Identity Laws (Conjunction with Truth, Disjunction with Falsity)",
            "ascii": "P and true = P",
            "latex": "P \\land \\top \\equiv P",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "P ∧ ⊤ ≡ P"},
                {"form_id": "dual", "notation_system": "ascii",
                 "expression": "P or false = P",
                 "scope_note": "Falsity is the identity for disjunction"},
                {"form_id": "annihilators", "notation_system": "ascii",
                 "expression": "P and false = false, P or true = true",
                 "scope_note": "The companion domination laws, where the constants annihilate instead"},
            ],
            "meaning": "Conjoining a tautology changes nothing, and neither does "
                       "disjoining a contradiction: the constants are neutral for their "
                       "own operation.",
            "significance": "A Huntington postulate and the point where a *constant* slot "
                            "first enters this corpus. That matters to the matcher: TRUTH "
                            "and UNIVERSE are declared `constant`, hence parameter-like "
                            "(P), so the typed skeleton `?0:V = MEET⟨?0:V, ?1:P⟩` records "
                            "that the second argument is a fixed element of the algebra "
                            "rather than a second free proposition. The set twin is `A ∩ U "
                            "= A`, with U in the same P slot.",
            "conditions": ["The language contains the constants true and false, or "
                           "definable stand-ins such as (P or not P)"],
            "failure_modes": [
                "In systems without truth constants the law must be stated schematically "
                "with a chosen tautology, and the choice can matter in weak metatheories.",
                "Confusing the identity laws with the domination laws (P and false = "
                "false) is the standard slip; they are duals of each other, not the same "
                "law.",
            ],
            "provenance": [HUNTINGTON, BOOLE, ENDERTON_LOGIC, DAVEY_PRIESTLEY],
            "keywords": ["identity element", "tautology", "neutral element",
                         "bounded lattice"],
            "ops": [LOG_EQUIV, AND, OR],
            "constants": [TRUE_CONST, FALSE_CONST],
        },
        "set_theory": {
            "title": "Identity Laws (Intersection with the Universe, Union with the Empty Set)",
            "ascii": "A inter U = A",
            "latex": "A \\cap U = A",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "A ∩ U = A"},
                {"form_id": "dual", "notation_system": "ascii",
                 "expression": "A ∪ emptyset = A",
                 "scope_note": "The empty set is the identity for union"},
                {"form_id": "annihilators", "notation_system": "ascii",
                 "expression": "A ∩ ∅ = ∅, A ∪ U = U",
                 "scope_note": "Companion domination laws"},
            ],
            "meaning": "Intersecting with everything, or uniting with nothing, leaves a "
                       "set unchanged.",
            "significance": "Exact typed twin of the propositional identity laws, "
                            "including the P/V split: UNIVERSE sits in the same "
                            "parameter-like slot as TRUTH. This is the node where the "
                            "abstraction pays for itself most visibly -- U and `true` look "
                            "nothing alike and belong to different subjects, but both are "
                            "the top element of a bounded lattice, and the template says "
                            "so.",
            "conditions": ["A is a subset of U",
                           "U is fixed for the duration of the argument"],
            "failure_modes": [
                "There is no universal set in ZFC, so U must be a set chosen in advance; "
                "treating it as 'the set of everything' reintroduces Russell's paradox.",
                "A ∩ U = A silently asserts A ⊆ U; if A escapes the chosen universe the "
                "left side is a proper subset of A.",
            ],
            "provenance": [HALMOS, ENDERTON_SETS, KUNEN, DAVEY_PRIESTLEY],
            "keywords": ["identity element", "universe", "empty set",
                         "bounded lattice", "algebra of sets"],
            "ops": [EQ, INTER, UNION],
            "constants": [UNIVERSE_CONST, EMPTY_CONST],
        },
    },
    {
        "name": "complement_laws",
        "topic_id": "boolean_laws",
        "archetype": "complement_annihilation",
        "cls": "axiom",
        "status": "formal",
        "template": TPL_COMPLEMENT,
        "entails": ["de_morgan_laws", "double_negation", "idempotence"],
        "invariants": [
            "An element and its complement meet in BOT and join in TOP; the pair of "
            "statements is what makes the bounded lattice complemented.",
            "In a distributive lattice the complement satisfying both halves is unique, "
            "so NEG is a well-defined function rather than a relation.",
            "The stated half fixes a constant on the right, so the typed skeleton "
            "`?0:P = MEET⟨?1:V, NEG⟨?1:V⟩⟩` puts the P slot on the *result* side, unlike "
            "the identity laws where it is an argument.",
            "Self-dual as a pair under exchanging MEET/JOIN and TOP/BOT.",
        ],
        "logic": {
            "title": "Complement Laws (Non-Contradiction and Excluded Middle)",
            "ascii": "P and (not P) = false",
            "latex": "P \\land \\lnot P \\equiv \\bot",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "P ∧ ¬P ≡ ⊥"},
                {"form_id": "dual", "notation_system": "ascii",
                 "expression": "P or (not P) = true",
                 "scope_note": "Law of the excluded middle, the dual half"},
                {"form_id": "non_contradiction", "notation_system": "ascii",
                 "expression": "not(P and not P)",
                 "scope_note": "Law of non-contradiction as a theorem rather than an equation"},
            ],
            "meaning": "A proposition and its negation cannot both hold, and one of them "
                       "must: negation partitions the space of cases exactly.",
            "significance": "The postulate that makes the lattice Boolean rather than "
                            "merely distributive, and the one whose two halves have very "
                            "different histories: non-contradiction is accepted almost "
                            "everywhere, excluded middle is the classic casualty of "
                            "constructive mathematics. Structurally the two halves are one "
                            "self-dual law, and its set twin `A ∩ A^c = ∅` is an exact "
                            "typed match -- with the notable asymmetry that the set half "
                            "corresponding to excluded middle, `A ∪ A^c = U`, is not "
                            "controversial at all.",
            "conditions": ["Classical two-valued semantics",
                           "Truth constants available"],
            "failure_modes": [
                "Excluded middle fails intuitionistically and in topos logic; assuming it "
                "is exactly assuming double negation elimination.",
                "Non-contradiction is dropped in paraconsistent logics, precisely so that "
                "an inconsistent theory does not entail everything.",
                "Neither half holds in fuzzy logic under the usual min/max connectives, "
                "where P ∧ ¬P can take the value 1/2.",
            ],
            "provenance": [HUNTINGTON, BOOLE, HEYTING, ENDERTON_LOGIC, MATHLIB],
            "keywords": ["excluded middle", "non-contradiction", "complement",
                         "Boolean algebra"],
            "ops": [LOG_EQUIV, AND, OR, NOT],
            "constants": [TRUE_CONST, FALSE_CONST],
        },
        "set_theory": {
            "title": "Complement Laws (Disjointness and Exhaustiveness)",
            "ascii": "A inter complement(A) = emptyset",
            "latex": "A \\cap A^{c} = \\emptyset",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "A ∩ A^c = ∅"},
                {"form_id": "dual", "notation_system": "ascii",
                 "expression": "A ∪ A^c = U",
                 "scope_note": "A set and its complement exhaust the universe"},
                {"form_id": "partition", "notation_system": "ascii",
                 "expression": "{A, A^c} is a partition of U whenever A is neither empty nor U"},
                {"form_id": "probability", "notation_system": "event_probability",
                 "expression": "Pr(A) + Pr(A^c) = 1",
                 "scope_note": "The measure-theoretic consequence: disjointness gives additivity, exhaustiveness gives the total"},
            ],
            "meaning": "A set and its complement share no points and together cover the "
                       "universe: complementation cuts U in two.",
            "significance": "Exact typed twin of non-contradiction. The set reading is "
                            "also the hinge between this corpus and the probability one: "
                            "the two-block partition {A, A^c} is the smallest instance of "
                            "the partition that "
                            "probstat.probability.total_probability_partition sums over, "
                            "and Pr(A^c) = 1 - Pr(A) is that sum with two terms. The "
                            "structural bridge is the CARD/measure functional, not the "
                            "lattice itself.",
            "conditions": ["A is a subset of the fixed universe U",
                           "Complement taken relative to U"],
            "failure_modes": [
                "Without a fixed universe there is no complement to speak of, so the law "
                "is vacuous rather than false in unrestricted set talk.",
                "In a Heyting algebra (open sets of a topological space, subobjects in a "
                "topos) the join half fails: A ∪ A^c is generally a proper subset of U, "
                "which is the topological face of intuitionism.",
            ],
            "provenance": [HALMOS, ENDERTON_SETS, KOLMOGOROV, DAVEY_PRIESTLEY],
            "keywords": ["complement", "disjoint", "partition", "universe",
                         "Boolean algebra"],
            "ops": [EQ, INTER, UNION, COMPL],
            "constants": [UNIVERSE_CONST, EMPTY_CONST],
        },
    },
    {
        "name": "idempotence",
        "topic_id": "boolean_laws",
        "archetype": "idempotent_operation",
        "cls": "identity",
        "status": "derived",
        "template": TPL_IDEMPOTENCE,
        "entailed_by": ["complement_laws", "distributivity_meet_over_join",
                        "identity_laws"],
        "invariants": [
            "A single free element occupies every position, so the law says something "
            "about the operation alone: repetition carries no information.",
            "Self-dual: JOIN(x, x) = x is the same statement with operations exchanged.",
            "Forced in any lattice by absorption, and derivable in a Boolean algebra "
            "from the identity, complement and distributive postulates without assuming "
            "it.",
            "Idempotence is what makes these operations *logical* rather than arithmetic: "
            "multiplication and addition are not idempotent, which is why counting "
            "arguments need inclusion-exclusion corrections.",
        ],
        "logic": {
            "title": "Idempotence of Conjunction and Disjunction",
            "ascii": "P and P = P",
            "latex": "P \\land P \\equiv P",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "P ∧ P ≡ P"},
                {"form_id": "dual", "notation_system": "ascii",
                 "expression": "P or P = P",
                 "scope_note": "Idempotence of disjunction"},
                {"form_id": "contraction", "notation_system": "ascii",
                 "expression": "from P, P infer P",
                 "scope_note": "The structural rule of contraction, which idempotence is the equational shadow of"},
            ],
            "meaning": "Asserting the same thing twice is asserting it once; repetition "
                       "adds no content.",
            "significance": "The smallest law with a free operand, and the corpus's "
                            "clearest illustration of what the twin thesis does *not* "
                            "claim: `?0:V = MEET⟨?0:V, ?0:V⟩` matches its set twin exactly, "
                            "yet the analogous arithmetic statement x*x = x is false for "
                            "all but two numbers. Structural twinning is a claim about "
                            "which operations share a form, and idempotence is precisely "
                            "the form that separates the lattice operations from the "
                            "arithmetic ones elsewhere in data/.",
            "conditions": ["Classical propositional semantics; no distributivity needed "
                           "once absorption is available"],
            "failure_modes": [
                "Substructural logics (linear, relevance) reject contraction, so the "
                "multiplicative conjunction there is not idempotent and this law does not "
                "hold of it.",
                "Probabilistic readings mislead: Pr(A and A) = Pr(A) holds, but the "
                "corresponding intuition Pr(A and B) ≈ Pr(A)Pr(B) does not degrade "
                "gracefully to the repeated case.",
            ],
            "provenance": [BOOLE, HUNTINGTON, BIRKHOFF, GENTZEN],
            "keywords": ["idempotence", "contraction", "lattice operation",
                         "repetition"],
            "ops": [LOG_EQUIV, AND, OR],
        },
        "set_theory": {
            "title": "Idempotence of Intersection and Union",
            "ascii": "A inter A = A",
            "latex": "A \\cap A = A",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "A ∩ A = A"},
                {"form_id": "dual", "notation_system": "ascii",
                 "expression": "A ∪ A = A"},
                {"form_id": "extensional", "notation_system": "ascii",
                 "expression": "{x : x in A and x in A} = {x : x in A}",
                 "scope_note": "Extensionality reduces the set law to the propositional one pointwise"},
            ],
            "meaning": "A set intersected or united with itself is itself: sets record "
                       "membership, not multiplicity.",
            "significance": "Exact typed twin of propositional idempotence, and the "
                            "property that distinguishes sets from multisets and from "
                            "cardinalities. The contrast with "
                            "settheory.cardinality.inclusion_exclusion_two_sets in this "
                            "same corpus is the point: CARD is not idempotent, so once a "
                            "counting functional is applied to the lattice the "
                            "overlap-correction term appears. Idempotence upstairs, "
                            "inclusion-exclusion downstairs.",
            "conditions": ["A is a set; extensionality holds"],
            "failure_modes": [
                "Multisets, bags and lists are not idempotent under their union analogues; "
                "SQL's UNION ALL is the everyday counterexample.",
                "Idempotence at the set level does not survive the passage to counts or "
                "measures, which is exactly why inclusion-exclusion exists.",
            ],
            "provenance": [BOOLE, HALMOS, ENDERTON_SETS, BIRKHOFF],
            "keywords": ["idempotence", "intersection", "union", "extensionality",
                         "multiset"],
            "ops": [EQ, INTER, UNION],
        },
    },
]

DISCIPLINE_ONLY_LAWS = [
    {
        "name": "modus_ponens",
        "topic_id": "inference",
        "archetype": "detachment_rule",
        "cls": "axiom",
        "status": "formal",
        "template": TPL_MODUS_PONENS,
        "invariants": [
            "The only inferential archetype in either corpus: the top-level node is an "
            "IMPLIES, not an equality, so the statement is a rule that licenses a move "
            "rather than an identity between two expressions.",
            "The antecedent slot occurs twice (once inside the conditional, once "
            "alone) and the consequent slot occurs twice, so the rule is entirely "
            "determined by the reuse pattern of two operands.",
            "Truth-preserving but not information-preserving: the conclusion is weaker "
            "than the premises, unlike every equational law here, which is reversible.",
            "Together with a suitable axiom schema it is complete for classical "
            "propositional logic, which is why it is stated as an axiom node.",
        ],
        "logic": {
            "title": "Modus Ponens (Rule of Detachment)",
            "ascii": "((P implies Q) and P) implies Q",
            "latex": "\\bigl((P \\to Q) \\land P\\bigr) \\to Q",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "((P → Q) ∧ P) → Q"},
                {"form_id": "rule", "notation_system": "ascii",
                 "expression": "P implies Q ; P |- Q",
                 "scope_note": "Presented as an inference rule with premises above the line"},
                {"form_id": "sequent", "notation_system": "ascii",
                 "expression": "Gamma |- P implies Q, Gamma |- P => Gamma |- Q",
                 "scope_note": "Sequent-calculus form; the elimination rule for implication"},
                {"form_id": "lattice_order", "notation_system": "ascii",
                 "expression": "if LEQ(top, implies(P,Q)) and LEQ(top, P) then LEQ(top, Q)",
                 "scope_note": "Order-theoretic reading in the Lindenbaum-Tarski algebra"},
            ],
            "meaning": "Given a conditional and its antecedent, the consequent may be "
                       "asserted; this is what makes a conditional usable rather than "
                       "merely true.",
            "significance": "Deliberately the odd node out. Everything else in these two "
                            "corpora is an equation between lattice expressions, which "
                            "means the matcher sees a symmetric `=` at the root and can "
                            "sort the two sides; modus ponens has an IMPLIES at the root "
                            "and is irreversible. Its nearest structural neighbour is "
                            "settheory.order.subset_transitivity, which shares the outer "
                            "`IMPLIES⟨MEET⟨_, _⟩, _⟩` shell but differs inside "
                            "(`IMPLIES⟨?0,?1⟩, ?0` against `LEQ⟨?0,?1⟩, LEQ⟨?1,?2⟩`), so "
                            "the two do not twin. That near miss is the honest result: "
                            "both are two-premise detachment rules, but only a matcher "
                            "that abstracted over the premise *heads* would see it.",
            "conditions": ["A consequence relation closed under the rule",
                           "Material implication with its classical truth table, or any "
                           "implication satisfying the deduction theorem"],
            "failure_modes": [
                "Fails for indicative conditionals in natural language under "
                "probabilistic readings (McGee's counterexamples to modus ponens for "
                "nested conditionals).",
                "In fuzzy and many-valued logics the rule needs a graded form; chaining "
                "it degrades the truth value of the conclusion.",
                "Affirming the consequent is the standing confusion: the rule is not "
                "symmetric and the template's asymmetric IMPLIES root records that.",
            ],
            "provenance": [FREGE, PRINCIPIA, GENTZEN, ENDERTON_LOGIC, MENDELSON],
            "keywords": ["modus ponens", "detachment", "inference rule",
                         "implication elimination"],
            "ops": [IMPL, AND, TURNSTILE],
        },
    },
    {
        "name": "contraposition",
        "topic_id": "inference",
        "archetype": "contrapositive_equivalence",
        "cls": "identity",
        "status": "derived",
        "template": TPL_CONTRAPOSITION,
        "entailed_by": ["double_negation"],
        "invariants": [
            "Both operands appear on each side but in exchanged positions and under a "
            "negation, so the law is an order-reversal statement about IMPLIES.",
            "An involution: applying contraposition twice returns the original "
            "conditional, which requires double negation to see.",
            "Preserves truth in both directions, unlike the converse and the inverse, "
            "which it is routinely confused with.",
            "Equational, hence reversible, which is why it is classed as an identity "
            "rather than a rule alongside modus ponens.",
        ],
        "logic": {
            "title": "Contraposition (Transposition)",
            "ascii": "(P implies Q) = ((not Q) implies (not P))",
            "latex": "(P \\to Q) \\equiv (\\lnot Q \\to \\lnot P)",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "(P → Q) ≡ (¬Q → ¬P)"},
                {"form_id": "disjunctive", "notation_system": "ascii",
                 "expression": "(P implies Q) = (not P) or Q",
                 "scope_note": "Material implication rewritten as a disjunction; contraposition is then commutativity of `or` plus double negation, which is the one-line proof"},
                {"form_id": "half", "notation_system": "ascii",
                 "expression": "(P implies Q) implies ((not Q) implies (not P))",
                 "scope_note": "The intuitionistically valid direction"},
            ],
            "meaning": "A conditional and its contrapositive say the same thing: ruling "
                       "out the consequent rules out the antecedent.",
            "significance": "The equational sibling of modus ponens, and the node that "
                            "shows why NEG had to be a call head rather than the parser's "
                            "arithmetic `-`. Written as `IMPLIES(NEG(PROP2), NEG(PROP1))` "
                            "the negations stay visible as structure; written with a minus "
                            "sign the matcher's family level would try to absorb them into "
                            "a parameter, which is meaningful for a rate constant and "
                            "nonsense for a truth value. The law has no set-theoretic twin "
                            "here because inclusion contraposes into complements "
                            "(A ⊆ B iff B^c ⊆ A^c) rather than into a conditional, a "
                            "genuinely different skeleton.",
            "conditions": ["Classical semantics for implication and negation",
                           "Double negation available for the reverse direction"],
            "failure_modes": [
                "Only one direction is intuitionistically valid; recovering the other "
                "needs double negation elimination.",
                "Confusion with the converse (Q implies P) and the inverse "
                "((not P) implies (not Q)), neither of which is equivalent to the "
                "original.",
                "Under probabilistic or default reasoning contraposition fails outright: "
                "'birds fly' does not contrapose to 'non-flyers are non-birds'.",
            ],
            "provenance": [BOOLE, PRINCIPIA, ENDERTON_LOGIC, MENDELSON],
            "keywords": ["contraposition", "transposition", "implication",
                         "converse", "inverse"],
            "ops": [LOG_EQUIV, IMPL, NOT],
        },
    },
    {
        "name": "ex_falso_quodlibet",
        "topic_id": "inference",
        "archetype": "explosion_from_falsehood",
        "cls": "theorem",
        "status": "derived",
        "template": TPL_EX_FALSO,
        "entailed_by": ["complement_laws", "identity_laws"],
        "invariants": [
            "The antecedent is a constant rather than a free operand, so the "
            "typed skeleton `IMPLIES⟨?0:P, ?1:V⟩` carries the P/V split at the "
            "root: the law is about BOT itself, not about a relation between two "
            "operands. Only its set-side echo, "
            "settheory.order.empty_set_minimality, makes a claim of that shape.",
            "The consequent slot occurs once and is never inspected -- that is "
            "the entire content, and it is also the relevantist's objection: a "
            "conclusion with no subject-matter connection to the premise.",
            "Order-theoretic restatement: LEQ(BOT, x) holds for every x, i.e. BOT "
            "is the least element of the bounded lattice. The two readings are "
            "the deduction theorem apart.",
            "Dual in position to reductio_ad_absurdum: BOT sits in the antecedent "
            "here and in the consequent there, so the pair exhausts what an "
            "object-language falsum can be attached to.",
            "Intuitionistically valid. It is minimal logic (which keeps BOT as an "
            "ordinary unprovable atom) and the paraconsistent logics that reject "
            "it, not constructivism.",
        ],
        "logic": {
            "title": "Ex Falso Quodlibet (Explosion)",
            "ascii": "false implies P",
            "latex": "\\bot \\to P",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "⊥ → P"},
                {"form_id": "entailment", "notation_system": "ascii",
                 "expression": "false |- P",
                 "scope_note": "Entailment form: from a contradiction every formula is derivable. Its skeleton LEQ(BOT, PROP) is the one that would twin exactly with settheory.order.empty_set_minimality; the deduction theorem is the step between the two forms"},
                {"form_id": "disjunctive", "notation_system": "ascii",
                 "expression": "(not false) or P = true",
                 "scope_note": "Unfolding material implication: the antecedent's complement is TOP, and TOP dominates every join"},
                {"form_id": "two_premise_rule", "notation_system": "ascii",
                 "expression": "P ; not P |- Q",
                 "scope_note": "The everyday explosion rule: a contradiction is assembled first, then anything at all is detached from it"},
            ],
            "meaning": "From falsehood, anything follows: a false antecedent places no "
                       "constraint on the consequent, so the conditional holds whatever "
                       "the consequent happens to say.",
            "significance": "The forward half of the epistemic ladder's falsehood rung "
                            "(docs/DESIGN-epistemic-ladder.md) made corpus-real. BOT was "
                            "already present algebraically -- it is the right-hand side of "
                            "logic.boolean_laws.complement_laws -- but until now nothing "
                            "said what could be *done* with it; this node says it forwards "
                            "and logic.inference.reductio_ad_absurdum says it backwards. "
                            "It twins with nothing, and the near miss is the informative "
                            "part: written in the entailment form the skeleton would be "
                            "`LEQ⟨?0:P, ?1:V⟩`, matching settheory.order.empty_set_minimality "
                            "character for character, because 'falsity entails everything' "
                            "and 'the empty set is contained in everything' are one "
                            "statement about the least element of a bounded lattice. The "
                            "object-language IMPLIES form was authored instead because it "
                            "is what the prover lane proves and what reductio inverts, and "
                            "the honest consequence -- two heads, no group -- is recorded "
                            "rather than dissolved by rewriting one side.",
            "conditions": ["A consequence relation in which BOT is the least element",
                           "An implication satisfying the deduction theorem, or an "
                           "explicit BOT-elimination rule"],
            "failure_modes": [
                "Rejected by paraconsistent logics (LP, relevance logics) precisely so "
                "that a single inconsistency does not trivialize a theory; this is the "
                "law that makes an inconsistent knowledge base useless rather than merely "
                "wrong, which is why a corpus that reasons over its own contents has a "
                "practical stake in it.",
                "Minimal logic keeps intuitionistic implication but drops BOT-elimination, "
                "so explosion fails while the rest of the constructive apparatus survives; "
                "'constructive' is therefore not the axis on which this law is contested.",
                "The natural-language gloss 'a false premise proves anything' invites the "
                "slide from validity to soundness: the schema says nothing about whether "
                "the antecedent is ever satisfied, and in practice it never is.",
            ],
            "provenance": [PRINCIPIA, GENTZEN, HEYTING, ENDERTON_LOGIC, PRIEST],
            "keywords": ["ex falso quodlibet", "explosion", "falsum", "bottom element",
                         "paraconsistency"],
            "ops": [IMPL, TURNSTILE, OR, NOT],
            "constants": [FALSE_CONST, TRUE_CONST],
        },
    },
    {
        "name": "reductio_ad_absurdum",
        "topic_id": "inference",
        "archetype": "refutation_by_contradiction",
        "cls": "theorem",
        "status": "derived",
        "template": TPL_REDUCTIO,
        "entailed_by": ["complement_laws", "identity_laws"],
        "invariants": [
            "The only statement in either corpus with an implication as its own "
            "antecedent, which is what makes this negation *introduction*: the "
            "premise being consumed is itself a derivation.",
            "The operand slot occurs twice, once inside the refuted conditional "
            "and once under NEG, so the rule is fixed entirely by that reuse; "
            "nothing else about the operand is used.",
            "BOT appears in consequent position here and in antecedent position "
            "in ex_falso_quodlibet, so the two nodes are one constant read in the "
            "two available directions.",
            "Intuitionistically valid as stated. The mirror image "
            "IMPLIES(IMPLIES(NEG(a), BOT), a) is not: that is double negation "
            "elimination in disguise, recorded on "
            "logic.boolean_laws.double_negation rather than duplicated here.",
            "Definitional where NEG(x) abbreviates IMPLIES(x, BOT), a theorem "
            "where NEG is the primitive lattice complement -- as it is in this "
            "corpus. Same line, two statuses, decided by which head is basic.",
        ],
        "logic": {
            "title": "Reductio ad Absurdum (Negation Introduction)",
            "ascii": "(P implies false) implies (not P)",
            "latex": "(P \\to \\bot) \\to \\lnot P",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "(P → ⊥) → ¬P"},
                {"form_id": "rule", "notation_system": "ascii",
                 "expression": "P |- false ; therefore |- not P",
                 "scope_note": "Natural-deduction negation introduction: the assumption P is discharged once it has yielded a contradiction"},
                {"form_id": "definitional", "notation_system": "ascii",
                 "expression": "not P = (P implies false)",
                 "scope_note": "Intuitionistic presentations define NEG this way, which turns the law into an identity rather than a derivation"},
                {"form_id": "classical", "notation_system": "ascii",
                 "expression": "((not P) implies false) implies P",
                 "scope_note": "The classical form, equivalent to double negation elimination and to excluded middle; NOT intuitionistically valid, and supplied in Lean by the explicit axiom Classical.byContradiction"},
                {"form_id": "contradiction_pair", "notation_system": "ascii",
                 "expression": "((P implies Q) and (P implies not Q)) implies not P",
                 "scope_note": "The everyday two-premise form, where the contradiction is exhibited as a pair instead of as BOT"},
            ],
            "meaning": "If assuming a proposition drives you to falsehood, the "
                       "proposition is refuted: a hypothesis that entails a contradiction "
                       "is discharged as its own negation.",
            "significance": "The backward half of the falsehood rung, and the corpus's "
                            "point of maximum care about intuitionistic honesty. The "
                            "direction stated here is constructively valid and is a "
                            "primitive rule of intuitionistic natural deduction; the "
                            "classical mirror image is the contested one, and the "
                            "extraction in prover/sample_triples.json shows exactly that "
                            "boundary being crossed by name -- `Classical.byContradiction` "
                            "appears twice inside `not_forall_iff_exists_not`, which is why "
                            "that theorem verifies logic.boolean_laws.de_morgan_laws and "
                            "not this node. Structurally its nearest neighbour is "
                            "logic.inference.modus_ponens: both have an IMPLIES root over "
                            "an IMPLIES-headed antecedent, but modus ponens conjoins the "
                            "antecedent where this drives it to BOT, so the skeletons "
                            "differ and no group is reported. Operationally this is the "
                            "closed form behind the ladder's REFUTED rung: deriving BOT "
                            "along a branch is search, and this node is what licenses the "
                            "discharge once the search succeeds.",
            "conditions": ["An implication satisfying the deduction theorem, so the "
                           "assumption can be discharged",
                           "BOT available as an object-language proposition, not merely "
                           "as a metatheoretic marker"],
            "failure_modes": [
                "Routinely conflated with the classical reductio ((not P) implies false) "
                "implies P; only the stated direction is intuitionistically valid, which "
                "is why proof assistants make the other an explicit axiom rather than a "
                "tactic.",
                "In paraconsistent settings deriving BOT no longer refutes the assumption, "
                "since contradictions are tolerated: reductio and explosion stand or fall "
                "together, and rejecting one to save inconsistent theories costs the other.",
                "Informally, 'that leads to absurdity' is used for conclusions that are "
                "merely implausible; the rule requires an actual contradiction, and the "
                "slippage is where rhetorical reductio arguments fail.",
            ],
            "provenance": [GENTZEN, HEYTING, PRINCIPIA, ENDERTON_LOGIC, MATHLIB],
            "keywords": ["reductio ad absurdum", "negation introduction",
                         "proof by contradiction", "falsum", "intuitionistic logic"],
            "ops": [IMPL, NOT, TURNSTILE],
            "constants": [FALSE_CONST],
        },
    },
    {
        "name": "hypothetical_syllogism",
        "topic_id": "inference",
        "archetype": "order_transitivity",
        "cls": "theorem",
        "status": "derived",
        "template": TPL_ORDER_TRANSITIVITY,
        "invariants": [
            "The middle proposition appears twice, once as the conclusion of the "
            "first entailment and once as the premise of the second: transitivity "
            "is the chaining pattern, and the repeated slot is the whole content.",
            "LEQ is the entailment order, not a defined connective. In the "
            "Lindenbaum-Tarski algebra the elements are formulas modulo "
            "interderivability and the partial order IS logical consequence, so "
            "`LEQ(a, b)` reads `a |- b` in exactly the sense in which it reads "
            "`A subset B` on the set side. Together with reflexivity (`a |- a`) "
            "and antisymmetry-modulo-equivalence, this law is what makes that "
            "quotient a poset at all -- the construction the corpus's whole "
            "logic/set_theory identity rests on.",
            "Order-theoretic restatement of absorption: LEQ(x, y) holds exactly "
            "when MEET(x, y) = x, so transitivity is a consequence of the lattice "
            "equations rather than an extra postulate.",
            "Not an equation and not reversible, which puts it in the same "
            "structural family as modus ponens rather than with the Boolean laws.",
            "Distinct from the object-language deduction "
            "`((a -> b) and (b -> c)) -> (a -> c)`, which is the same fact one "
            "deduction-theorem step away and would carry IMPLIES where this "
            "carries LEQ. The order form is authored because it is the form the "
            "graph can compare -- and, unusually for this corpus, that choice "
            "costs nothing: both readings are standard textbook statements of "
            "hypothetical syllogism, and the object-language one is recorded in "
            "equivalent_forms.",
        ],
        "logic": {
            "title": "Hypothetical Syllogism (Transitivity of Entailment)",
            "ascii": "if (P entails Q) and (Q entails R) then (P entails R)",
            "latex": "P \\vdash Q \\ \\land\\ Q \\vdash R \\implies P \\vdash R",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "(P ⊢ Q) ∧ (Q ⊢ R) → (P ⊢ R)"},
                {"form_id": "object_language", "notation_system": "ascii",
                 "expression": "((P implies Q) and (Q implies R)) implies (P implies R)",
                 "scope_note": "The conditional-chaining form, which is what most textbooks name hypothetical syllogism. Equivalent to the order form by the deduction theorem; it would carry IMPLIES in the two premise positions and so would NOT twin the inclusion family"},
                {"form_id": "rule", "notation_system": "ascii",
                 "expression": "P |- Q ; Q |- R |- P |- R",
                 "scope_note": "Presented as an inference rule with premises above the line"},
                {"form_id": "cut", "notation_system": "ascii",
                 "expression": "Gamma |- P, P |- Delta => Gamma |- Delta",
                 "scope_note": "Gentzen's cut rule: hypothetical syllogism is the propositional shadow of cut, and cut-elimination is the theorem that it is admissible rather than primitive"},
                {"form_id": "lattice", "notation_system": "ascii",
                 "expression": "(P and Q = P) and (Q and R = Q) implies (P and R = P)",
                 "scope_note": "Entailment expressed through meet, which is how LEQ is defined in the template"},
                {"form_id": "composition", "notation_system": "ascii",
                 "expression": "f : P -> Q, g : Q -> R  gives  g . f : P -> R",
                 "scope_note": "Under Curry-Howard the rule is composition of proof terms; a preorder read as a category has hypothetical syllogism as its composition law"},
            ],
            "meaning": "Entailment chains: if P is enough for Q and Q is enough "
                       "for R, then P is enough for R. Reasoning can be assembled "
                       "from steps, which is what makes proof possible at all.",
            "significance": "Authored to cash a prediction the corpus registered "
                            "against itself. `settheory.order.subset_transitivity` "
                            "was deliberately written with the lattice-abstract LEQ "
                            "head rather than a SUBSET head, and its commentary "
                            "recorded the reason out loud: so that a future logic "
                            "node for entailment transitivity 'would twin with this "
                            "one exactly, without either corpus being rewritten'. "
                            "That is now testable, and the answer is yes -- the two "
                            "templates are generated from one shared format string "
                            "(TPL_ORDER_TRANSITIVITY), and the skeleton "
                            "`IMPLIES⟨MEET⟨LEQ⟨?0:V, ?1:V⟩, LEQ⟨?1:V, ?2:V⟩⟩, "
                            "LEQ⟨?0:V, ?2:V⟩⟩` now carries FOUR statements in four "
                            "disciplines: this node, subset inclusion, "
                            "geotop.predicates.containment_transitivity and "
                            "temporal.order.precedence_transitivity. The result is "
                            "worth separating from the file's other twins. De "
                            "Morgan twins because logic and set theory are one "
                            "Boolean algebra; this group twins across four subject "
                            "matters that share no carrier -- propositions, sets, "
                            "spatial regions, instants of time -- and what they "
                            "share is only that each carries a partial order. It is "
                            "the corpus's clearest instance of structure "
                            "generalizing past its origin, and the cheapest one to "
                            "have obtained, since three quarters of it was already "
                            "in the graph waiting. Against its own corpus the "
                            "contrast is with logic.inference.modus_ponens, which "
                            "shares the outer two-premise detachment shell "
                            "`IMPLIES⟨MEET⟨_, _⟩, _⟩` and differs inside; that shell "
                            "now carries six nodes and forms exactly one group, "
                            "which is the measurement docs/BACKLOG.md asked for.",
            "conditions": ["A consequence relation that is reflexive and "
                           "transitive, i.e. a preorder on formulas",
                           "Formulas taken modulo interderivability, so the "
                           "preorder becomes the partial order of the "
                           "Lindenbaum-Tarski algebra"],
            "failure_modes": [
                "Fails for non-transitive consequence relations, which are not "
                "exotic: probabilistic support, default and defeasible reasoning, "
                "and 'is evidence for' all chain badly, and the sorites paradox is "
                "what happens when a tolerant relation is chained anyway.",
                "Substructural logics that reject cut as primitive still validate "
                "it as admissible; a logic in which cut is genuinely unavailable is "
                "one in which proofs cannot be composed, which is a very strong "
                "restriction and rarely what is wanted.",
                "Conflated with the invalid chain of *converses* and with the "
                "material-conditional paradoxes: from vacuously true conditionals "
                "the rule still fires and yields a vacuously true conclusion, which "
                "is valid and routinely misread as informative.",
            ],
            "provenance": [ARISTOTLE, FREGE, GENTZEN, ENDERTON_LOGIC,
                           DAVEY_PRIESTLEY],
            "keywords": ["hypothetical syllogism", "transitivity", "entailment",
                         "cut rule", "Lindenbaum-Tarski algebra", "partial order"],
            "ops": [TURNSTILE, AND, IMPL],
        },
    },
    {
        "name": "subset_transitivity",
        "topic_id": "order",
        "archetype": "order_transitivity",
        "cls": "theorem",
        "status": "derived",
        "template": TPL_ORDER_TRANSITIVITY,
        "invariants": [
            "The middle element appears twice, once as the consequent of the first "
            "premise and once as the antecedent of the second: transitivity is the "
            "chaining pattern, and the repeated slot is the whole content.",
            "Together with reflexivity and antisymmetry it makes inclusion a partial "
            "order, which is the order underlying every MEET/JOIN statement in this "
            "corpus.",
            "Order-theoretic restatement of absorption: LEQ(x, y) holds exactly when "
            "MEET(x, y) = x, so transitivity is a consequence of the lattice equations.",
            "Not an equation and not reversible, which puts it in the same structural "
            "family as modus ponens rather than with the Boolean laws.",
        ],
        "set_theory": {
            "title": "Transitivity of Subset Inclusion",
            "ascii": "if (A subset B) and (B subset C) then (A subset C)",
            "latex": "A \\subseteq B \\ \\land\\ B \\subseteq C \\implies A \\subseteq C",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "(A ⊆ B) ∧ (B ⊆ C) → (A ⊆ C)"},
                {"form_id": "membership", "notation_system": "ascii",
                 "expression": "(forall x. x in A implies x in B) and (forall x. x in B implies x in C) implies (forall x. x in A implies x in C)",
                 "scope_note": "Unfolded to membership; the proof is hypothetical syllogism applied pointwise"},
                {"form_id": "lattice", "notation_system": "ascii",
                 "expression": "(A inter B = A) and (B inter C = B) implies (A inter C = A)",
                 "scope_note": "Inclusion expressed through meet, which is how LEQ is defined in the template"},
            ],
            "meaning": "Containment chains: if every element of A lies in B and every "
                       "element of B lies in C, then every element of A lies in C.",
            "significance": "The set corpus's inferential node, chosen to mirror "
                            "logic.inference.modus_ponens rather than to twin with it. "
                            "Both are two-premise detachment shells "
                            "`IMPLIES⟨MEET⟨_, _⟩, _⟩`, but the premises differ in head, so "
                            "the matcher reports no group -- correctly. The template uses "
                            "the lattice-abstract LEQ head rather than a SUBSET head "
                            "precisely so that a future logic node for entailment "
                            "transitivity (hypothetical syllogism, stated over the "
                            "Lindenbaum-Tarski order) would twin with this one exactly, "
                            "without either corpus being rewritten. That bet has now been "
                            "settled, and it paid three times over. "
                            "logic.inference.hypothetical_syllogism was authored from the "
                            "same shared format string and joined the group, but two "
                            "corpora had already found it first without being asked to: "
                            "geotop.predicates.containment_transitivity and "
                            "temporal.order.precedence_transitivity adopted the same LEQ "
                            "shape for spatial containment and temporal precedence. The "
                            "skeleton now carries four statements in four disciplines "
                            "whose carriers have nothing in common but a partial order. "
                            "The `equivalent_to` edge to the logic node is literal in the "
                            "same sense as the Boolean-law twins; the other two are "
                            "analogies of order and are left to the matcher's report, "
                            "where analogies belong.",
            "conditions": ["A, B, C are sets",
                           "Inclusion defined extensionally by universally quantified "
                           "membership"],
            "failure_modes": [
                "Membership `in` is emphatically not transitive; conflating ⊆ with ∈ is "
                "the standard beginner error and the reason transitive *sets* are a named "
                "special class.",
                "Proper inclusion ⊂ is transitive but not reflexive, so results stated for "
                "⊆ do not transfer verbatim.",
            ],
            "provenance": [HALMOS, ENDERTON_SETS, KUNEN, DAVEY_PRIESTLEY],
            "keywords": ["transitivity", "subset", "partial order", "inclusion",
                         "lattice order"],
            "ops": [SUBSET, AND, IMPL],
        },
    },
    {
        "name": "empty_set_minimality",
        "topic_id": "order",
        "archetype": "least_element_minimality",
        "cls": "theorem",
        "status": "derived",
        "template": TPL_BOTTOM_MINIMAL,
        "entailed_by": ["identity_laws"],
        "invariants": [
            "One constant and one free operand, and the operand is never "
            "inspected: BOT is below everything unconditionally, which is what "
            "'least' means.",
            "Equivalent to the domination law MEET(BOT, x) = BOT, so the content "
            "is purely lattice-algebraic; the order form is merely the readable "
            "one.",
            "The order-theoretic transcription of ex falso quodlibet. LEQ is "
            "realized as entailment in data/logic and as inclusion here, so "
            "'falsity entails everything' and 'the empty set is contained in "
            "everything' are one statement over two carriers.",
            "Vacuous truth is the entire proof: the universally quantified "
            "membership condition ranges over an empty domain, so it holds with "
            "nothing to check.",
            "Not an equation and not reversible, which places it structurally "
            "with subset_transitivity rather than with the Boolean laws.",
        ],
        "set_theory": {
            "title": "Minimality of the Empty Set",
            "ascii": "emptyset subset A",
            "latex": "\\emptyset \\subseteq A",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "∅ ⊆ A"},
                {"form_id": "membership", "notation_system": "ascii",
                 "expression": "forall x. (x in emptyset implies x in A)",
                 "scope_note": "Unfolded to membership; vacuously true, because the antecedent is never satisfied"},
                {"form_id": "lattice", "notation_system": "ascii",
                 "expression": "emptyset inter A = emptyset",
                 "scope_note": "Inclusion expressed through meet, which is how LEQ is defined in the template; this is the domination law"},
                {"form_id": "bounded", "notation_system": "ascii",
                 "expression": "emptyset subset A subset U",
                 "scope_note": "Paired with the universe from the identity laws: the two bounds that make the powerset lattice bounded"},
            ],
            "meaning": "Every set contains the empty set: there is no element of the "
                       "empty set that could fail to lie in A, so the inclusion holds "
                       "with nothing to verify.",
            "significance": "The set corpus's half of the epistemic ladder's falsehood "
                            "rung, and deliberately the *order* form rather than a copy of "
                            "logic.inference.ex_falso_quodlibet's template. Transcribing "
                            "the object-language head IMPLIES into set theory would read "
                            "`∅^c ∪ A = U` -- true in the powerset Boolean algebra, and no "
                            "set theory is written that way; authoring it would have "
                            "manufactured a twin rather than found one. The cost is stated "
                            "instead of hidden: `LEQ⟨?0:P, ?1:V⟩` and `IMPLIES⟨?0:P, ?1:V⟩` "
                            "differ at the head, so the matcher reports no group even "
                            "though the two nodes are the same fact about the least element "
                            "of a bounded lattice, one deduction theorem apart. Against its "
                            "own corpus the contrast is with "
                            "settheory.order.subset_transitivity: same LEQ head, but there "
                            "every operand is free, while here the lower one is the fixed "
                            "bottom element -- the P/V split, not the shape, is what "
                            "separates them.",
            "conditions": ["A is a set",
                           "Inclusion defined extensionally by universally quantified "
                           "membership"],
            "failure_modes": [
                "The vacuous-truth argument reads as a trick rather than a proof to most "
                "beginners, and is the commonest place where quantification over an empty "
                "domain gets rejected on intuitive grounds.",
                "Inclusion is not membership: ∅ ⊆ A always, while ∅ ∈ A only if A was "
                "built to contain it. Conflating the two is the standard error and the "
                "reason {∅} ≠ ∅.",
                "Proper inclusion fails at the single point A = ∅, since ∅ ⊂ ∅ is false, "
                "so the statement does not transfer verbatim from ⊆ to ⊂.",
            ],
            "provenance": [HALMOS, ENDERTON_SETS, KUNEN, DAVEY_PRIESTLEY],
            "keywords": ["empty set", "subset", "vacuous truth", "least element",
                         "bounded lattice"],
            "ops": [SUBSET, INTER, EQ],
            "constants": [EMPTY_CONST],
        },
    },
    {
        "name": "inclusion_exclusion_two_sets",
        "topic_id": "cardinality",
        "archetype": "inclusion_exclusion_correction",
        "cls": "theorem",
        "status": "derived",
        "template": TPL_INCLUSION_EXCLUSION,
        "invariants": [
            "Additive with a single correction term: the overlap is counted twice by the "
            "naive sum and subtracted once, so the identity is exact rather than a bound.",
            "Reduces to plain additivity CARD(JOIN(x, y)) = CARD(x) + CARD(y) exactly "
            "when MEET(x, y) = BOT, which is the complement law's hypothesis.",
            "Symmetric in the two sets, since both MEET and JOIN are.",
            "CARD is a valuation on the lattice: monotone, and modular in the sense this "
            "identity states. Any valuation -- counting measure, probability, Lebesgue "
            "measure, dimension of a vector-space sum -- satisfies the same equation.",
            "Extends to n sets with alternating signs over all non-empty subsets, the "
            "Moebius function of the Boolean lattice.",
        ],
        "set_theory": {
            "title": "Inclusion-Exclusion for Two Sets",
            "ascii": "CARD(A union B) = CARD(A) + CARD(B) - CARD(A inter B)",
            "latex": "|A \\cup B| = |A| + |B| - |A \\cap B|",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "|A ∪ B| = |A| + |B| - |A ∩ B|"},
                {"form_id": "disjoint_case", "notation_system": "ascii",
                 "expression": "|A ∪ B| = |A| + |B| when A ∩ B = ∅",
                 "scope_note": "Finite additivity as the degenerate case"},
                {"form_id": "probability", "notation_system": "event_probability",
                 "expression": "Pr(A ∪ B) = Pr(A) + Pr(B) - Pr(A ∩ B)",
                 "scope_note": "The addition rule; same identity with probability as the valuation"},
                {"form_id": "n_sets", "notation_system": "ascii",
                 "expression": "CARD(union_i A_i) = sum over non-empty S of (-1)^(CARD(S)+1) * CARD(inter_{i in S} A_i)",
                 "scope_note": "General form; the signs are the Moebius function of the Boolean lattice"},
            ],
            "meaning": "Counting the union by adding the parts double-counts whatever "
                       "lies in both, so the overlap is subtracted once to make the count "
                       "exact.",
            "significance": "Included to test the shape relation the corpus predicted "
                            "with probstat.probability.total_probability_partition, and "
                            "the honest answer is that it does not twin: total probability "
                            "is `MARGINAL = sum_i CONDITIONAL_i*WEIGHT_i`, a weighted sum "
                            "over an index, while this is a three-term signed sum with a "
                            "nested MEET inside the correction. What they share is the "
                            "*idea* of a valuation on a Boolean lattice, and the two do "
                            "meet on the `probability` equivalent form recorded above, "
                            "which is literally the probability addition rule. The "
                            "structural moral is worth keeping: applying a non-idempotent "
                            "functional (CARD) to idempotent lattice operations is exactly "
                            "what manufactures the correction term, so this node is the "
                            "counterweight to settheory.boolean_laws.idempotence.",
            "conditions": ["A and B are finite (or CARD is replaced by a finite measure)",
                           "Counting measure, or any modular valuation on the lattice"],
            "failure_modes": [
                "Meaningless as stated for infinite sets: |A ∪ B| = |A| for infinite A and "
                "countable B, so cardinal arithmetic absorbs rather than corrects.",
                "The n-set expansion has 2^n - 1 terms and is numerically unstable in "
                "floating point when the alternating terms are of comparable size.",
                "Transplanting it to a non-modular valuation (e.g. a submodular set "
                "function) turns the identity into an inequality.",
            ],
            "provenance": [STANLEY, ROTA, KOLMOGOROV, HALMOS],
            "keywords": ["inclusion-exclusion", "cardinality", "counting", "valuation",
                         "addition rule", "modularity"],
            "ops": [EQ, INTER, UNION, PLUS, MINUS],
        },
    },
]

# --------------------------------------------------------------------------
# Quantifier laws (v0.10, logic-only): the classical first-order core that
# DEFINES the FORALL/EXISTS heads. Authored corpus-first, because the coverage
# classifier may only accept a quantified ingested statement once a corpus
# node carries the binder heads. Logic-only on purpose: the set-theoretic
# reading of a quantifier is comprehension/indexed union, a genuinely
# different statement family, so a set twin would be manufactured, not found.
# --------------------------------------------------------------------------

QUANTIFIER_LAWS = [
    {
        "name": "universal_instantiation",
        "topic_id": "quantification",
        "archetype": "binder_elimination_rule",
        "cls": "axiom",
        "status": "formal",
        "template": TPL_UNIVERSAL_INSTANTIATION,
        "invariants": [
            "The FORALL head's generating exemplar: the bound slot VAR1 occurs "
            "only inside the binder's body, and the recurrence pattern IS the "
            "binding — the skeleton's first-occurrence numbering makes the "
            "statement alpha-invariant with no dedicated machinery.",
            "An elimination rule with an IMPLIES root, structurally beside "
            "modus ponens rather than the equational laws: it licenses a move "
            "from the general to the particular and is not reversible.",
            "The predicate letter PRED is applied to two DIFFERENT arguments "
            "(the bound variable, then the free term), which is what "
            "distinguishes instantiation from the vacuous IMPLIES(P, P).",
            "With existential_generalization it composes into "
            "universal_implies_existential — the inhabited-domain bridge "
            "between the two binders.",
        ],
        "logic": {
            "title": "Universal Instantiation (∀-Elimination)",
            "ascii": "(forall x. F(x)) implies F(t)",
            "latex": "(\\forall x\\, F(x)) \\to F(t)",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "(∀ x, F x) → F t"},
                {"form_id": "rule", "notation_system": "ascii",
                 "expression": "forall x. F(x) |- F(t)",
                 "scope_note": "Natural-deduction ∀-elimination; premise above the line"},
                {"form_id": "dictum", "notation_system": "ascii",
                 "expression": "what is affirmed of all is affirmed of any",
                 "scope_note": "The scholastic dictum de omni, the rule's pre-formal ancestor"},
            ],
            "symbols": [PRED_SYM, VAR_SYM, TERM_SYM],
            "meaning": "What holds of everything holds of any particular thing "
                       "you can name: a universal claim may be applied to any "
                       "term of the domain.",
            "significance": "The rule that makes a universal statement USABLE "
                            "rather than merely true — every application of a "
                            "general theorem to a concrete case passes through "
                            "it. For this corpus it is the load-bearing "
                            "exemplar: the coverage classifier accepts an "
                            "ingested `∀ x : ℝ, x^2 ≥ 0` only because this "
                            "node carries the FORALL head it reduces to.",
            "conditions": ["t is free for x in F: no variable of t is captured "
                           "by a binder inside F",
                           "Valid classically and intuitionistically"],
            "failure_modes": [
                "Variable capture: instantiating ∀x ∃y (x ≠ y) with t := y "
                "yields the falsehood ∃y (y ≠ y); the freeness side condition "
                "is not decorative.",
                "Free logic rejects the rule for non-denoting terms: from 'all "
                "unicorns are horned' one may not instantiate to a unicorn.",
                "Sorted/typed domains: t must belong to the sort x ranges "
                "over, which is exactly the carrier-honesty the coverage "
                "classifier enforces on ingested binders.",
            ],
            "provenance": [FREGE, PRINCIPIA, GENTZEN, ENDERTON_LOGIC, MENDELSON],
            "keywords": ["universal instantiation", "forall elimination",
                         "specialization", "dictum de omni", "binder"],
            "ops": [IMPL, FORALL_OP],
        },
    },
    {
        "name": "existential_generalization",
        "topic_id": "quantification",
        "archetype": "binder_introduction_rule",
        "cls": "axiom",
        "status": "formal",
        "template": TPL_EXISTENTIAL_GENERALIZATION,
        "invariants": [
            "The EXISTS head's generating exemplar, and universal "
            "instantiation's mirror: the same two predicate applications in "
            "the opposite order around the IMPLIES root.",
            "An introduction rule: the witness t is forgotten, not produced — "
            "the conclusion is strictly weaker than the premise, which is why "
            "the root is IMPLIES and not an equality.",
            "The bound slot VAR1 again occurs only inside the binder's body; "
            "EXISTS binds by recurrence exactly as FORALL does.",
        ],
        "logic": {
            "title": "Existential Generalization (∃-Introduction)",
            "ascii": "F(t) implies (exists x. F(x))",
            "latex": "F(t) \\to (\\exists x\\, F(x))",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "F t → (∃ x, F x)"},
                {"form_id": "rule", "notation_system": "ascii",
                 "expression": "F(t) |- exists x. F(x)",
                 "scope_note": "Natural-deduction ∃-introduction; the witness is discharged into the binder"},
            ],
            "symbols": [PRED_SYM, VAR_SYM, TERM_SYM],
            "meaning": "A named example establishes existence: if the property "
                       "holds of some particular term, then something has the "
                       "property.",
            "significance": "The rule every witness argument ends with, and "
                            "the shape of every ingested `∃ x, x = e` goal "
                            "read backwards: exhibiting e IS the proof. "
                            "data/number_theory's parity witness definitions "
                            "(evenness as the existence of a doubling witness) "
                            "instantiate this head over the integers.",
            "conditions": ["t is free for x in F",
                           "t denotes an element of the domain (existential "
                           "import of terms)"],
            "failure_modes": [
                "Free logic again: from F(Pegasus) one may not conclude "
                "∃x F(x) unless Pegasus denotes.",
                "Constructively the rule is valid but its converse reading is "
                "the error: knowing ∃x F(x) does not recover WHICH t worked.",
            ],
            "provenance": [FREGE, PRINCIPIA, GENTZEN, ENDERTON_LOGIC, MENDELSON],
            "keywords": ["existential generalization", "exists introduction",
                         "witness", "binder"],
            "ops": [IMPL, EXISTS_OP],
        },
    },
    {
        "name": "quantifier_negation_universal",
        "topic_id": "quantification",
        "archetype": "universal_negation_duality",
        "cls": "identity",
        "status": "derived",
        "template": TPL_NOT_FORALL,
        "entailed_by": ["quantifier_negation_existential", "double_negation"],
        "invariants": [
            "The quantifier De Morgan law: NEG passes through the binder and "
            "flips it, exactly as it flips MEET to JOIN in the propositional "
            "law — the infinitary reading (FORALL as the big MEET of the "
            "body's instances) makes the analogy an identity.",
            "Equational, hence reversible; but only the ∃¬-to-¬∀ direction "
            "survives intuitionistically — the equation as stated is classical. "
            "(Review-corrected: an earlier wording named ¬∃¬-to-¬∀, a direction "
            "valid in no logic; the failure_modes entry always had it right.)",
            "This is the law that licenses reading a ¬-prefixed quantifier "
            "chain as NEG-composition of the binder heads: a `¬∃ x, P` goal "
            "is NEG(EXISTS(x, P)), and this node with its dual says the "
            "composition is well-defined either way.",
            "One predicate letter, one bound variable: the smallest statement "
            "in which both binder heads appear.",
        ],
        "logic": {
            "title": "Negation of a Universal (Quantifier De Morgan, ∀-Form)",
            "ascii": "not (forall x. F(x)) = (exists x. not F(x))",
            "latex": "\\lnot(\\forall x\\, F(x)) \\equiv \\exists x\\, \\lnot F(x)",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "¬(∀ x, F x) ↔ (∃ x, ¬F x)"},
                {"form_id": "counterexample", "notation_system": "ascii",
                 "expression": "a universal fails iff it has a counterexample",
                 "scope_note": "The reading every refutation-by-counterexample argument uses"},
                {"form_id": "infinitary", "notation_system": "ascii",
                 "expression": "not (F(a1) and F(a2) and ...) = (not F(a1)) or (not F(a2)) or ...",
                 "scope_note": "Over a fixed domain: propositional De Morgan applied to the big meet"},
            ],
            "symbols": [PRED_SYM, VAR_SYM],
            "meaning": "A universal claim fails exactly when some instance "
                       "fails: denying 'all' asserts a counterexample.",
            "significance": "The refutation rule of quantified mathematics — "
                            "every disproof-by-counterexample is this equation "
                            "read left to right. Its Lean form "
                            "(not_forall_iff_exists_not) is machine-checked in "
                            "the committed prover artifact, and the "
                            "verified_by bridge moved HERE from the "
                            "propositional De Morgan node the moment a node "
                            "existed that states exactly what the theorem "
                            "proves.",
            "conditions": ["Classical semantics: the left-to-right direction "
                           "requires excluded middle (Markov-style reasoning "
                           "is not intuitionistically available)"],
            "failure_modes": [
                "Intuitionistically only ∃x ¬F(x) → ¬∀x F(x) holds; the "
                "converse is equivalent to a choice-of-counterexample "
                "principle and fails in Heyting semantics.",
                "Over an empty domain both sides are decided (¬∀ is false, "
                "∃¬ is false), so the law holds — but vacuously, which "
                "beginners routinely misread.",
            ],
            "provenance": [FREGE, PRINCIPIA, HEYTING, ENDERTON_LOGIC, MENDELSON],
            "keywords": ["quantifier negation", "De Morgan", "counterexample",
                         "duality", "classical logic"],
            "ops": [LOG_EQUIV, NOT, FORALL_OP, EXISTS_OP],
        },
    },
    {
        "name": "quantifier_negation_existential",
        "topic_id": "quantification",
        "archetype": "existential_negation_duality",
        "cls": "identity",
        "status": "derived",
        "template": TPL_NOT_EXISTS,
        "invariants": [
            "The dual De Morgan law, and the intuitionistically innocent one: "
            "both directions hold in Heyting semantics, unlike its ∀-form "
            "sibling, which needs classical logic — the asymmetry between the "
            "two nodes is real logical content, not authoring drift.",
            "NEG flips EXISTS to FORALL: the infinitary reading of "
            "propositional De Morgan over the big join.",
            "With double negation it ENTAILS the ∀-form law, which is the "
            "recorded lineage edge: ¬∀F = ¬∀¬¬F = ¬¬∃¬F = ∃¬F, classically.",
            "The shape of every ingested no-solutions statement: "
            "`¬∃ x y : ℕ, 7^x - 3^y = 4` is NEG over this node's left-hand "
            "head.",
        ],
        "logic": {
            "title": "Negation of an Existential (Quantifier De Morgan, ∃-Form)",
            "ascii": "not (exists x. F(x)) = (forall x. not F(x))",
            "latex": "\\lnot(\\exists x\\, F(x)) \\equiv \\forall x\\, \\lnot F(x)",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "¬(∃ x, F x) ↔ (∀ x, ¬F x)"},
                {"form_id": "no_solutions", "notation_system": "ascii",
                 "expression": "an equation has no solution iff every candidate fails it",
                 "scope_note": "The reading every non-existence proof in number theory uses"},
                {"form_id": "infinitary", "notation_system": "ascii",
                 "expression": "not (F(a1) or F(a2) or ...) = (not F(a1)) and (not F(a2)) and ...",
                 "scope_note": "Over a fixed domain: propositional De Morgan applied to the big join"},
            ],
            "symbols": [PRED_SYM, VAR_SYM],
            "meaning": "Nothing has the property exactly when everything lacks "
                       "it: denying existence is a universal claim.",
            "significance": "The logical form of every impossibility theorem — "
                            "'there is no rational square root of two' IS a "
                            "universally quantified negation, and this node is "
                            "the bridge between the two shapes. Constructively "
                            "the cleanest of the four quantifier-negation "
                            "directions: refuting an existential never needs "
                            "excluded middle.",
            "conditions": ["None beyond first-order semantics: valid "
                           "classically and intuitionistically, both "
                           "directions"],
            "failure_modes": [
                "The three-way confusion with ¬∀ shapes: ¬∃¬F (equivalent to "
                "∀F classically but strictly weaker intuitionistically) is "
                "routinely conflated with ¬∃F.",
                "Substructural logics without weakening or with existential "
                "import distinctions restrict the equivalence.",
            ],
            "provenance": [FREGE, PRINCIPIA, HEYTING, ENDERTON_LOGIC, MENDELSON],
            "keywords": ["quantifier negation", "De Morgan", "non-existence",
                         "impossibility", "duality"],
            "ops": [LOG_EQUIV, NOT, FORALL_OP, EXISTS_OP],
        },
    },
    {
        "name": "universal_conjunction_distribution",
        "topic_id": "quantification",
        "archetype": "binder_meet_distribution",
        "cls": "identity",
        "status": "derived",
        "template": TPL_FORALL_MEET,
        "invariants": [
            "FORALL distributes over MEET in both directions — the equational "
            "face of 'the universal quantifier is an infinitary meet': a big "
            "meet of pairwise meets regroups freely.",
            "Two schematic predicates over ONE bound variable; the bound slot "
            "recurs in four positions, the densest recurrence pattern in the "
            "corpus's logic nodes.",
            "The dual distribution (FORALL over JOIN) is deliberately ABSENT: "
            "only one direction of it is valid, so authoring it as an "
            "equation would state a falsehood — the gap is the honest shape "
            "of the law, recorded in the failure modes instead.",
            "Valid intuitionistically in both directions, unlike the "
            "quantifier De Morgan pair.",
        ],
        "logic": {
            "title": "Universal Quantifier Distributes over Conjunction",
            "ascii": "(forall x. F(x) and G(x)) = (forall x. F(x)) and (forall x. G(x))",
            "latex": "\\forall x\\,(F(x) \\land G(x)) \\equiv (\\forall x\\, F(x)) \\land (\\forall x\\, G(x))",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "(∀ x, F x ∧ G x) ↔ (∀ x, F x) ∧ (∀ x, G x)"},
                {"form_id": "big_meet", "notation_system": "ascii",
                 "expression": "meet_x (F(x) and G(x)) = (meet_x F(x)) and (meet_x G(x))",
                 "scope_note": "The infinitary-lattice reading: regrouping a big meet of meets"},
            ],
            "symbols": [PRED_SYM, PREDB_SYM, VAR_SYM],
            "meaning": "Everything satisfies both properties exactly when "
                       "everything satisfies each: a joint universal claim "
                       "splits into separate ones.",
            "significance": "The regrouping law behind proving conjunctive "
                            "goals componentwise — `∀ x, P x ∧ Q x` and the "
                            "pair of separate universals are one statement, "
                            "which is also why the coverage classifier may "
                            "check a quantified body's conjuncts under one "
                            "binder context.",
            "conditions": ["None beyond first-order semantics: valid "
                           "classically and intuitionistically"],
            "failure_modes": [
                "The JOIN analogue fails: (∀x Fx) ∨ (∀x Gx) implies "
                "∀x (Fx ∨ Gx) but not conversely — every integer is even or "
                "odd, yet neither 'all are even' nor 'all are odd' holds. "
                "Distributing ∀ over ∨ is the classic quantifier error.",
                "Over distinct bound variables the regrouping is a different "
                "(valid) law; conflating the two hides a change of scope.",
            ],
            "provenance": [FREGE, PRINCIPIA, ENDERTON_LOGIC, MENDELSON,
                           DAVEY_PRIESTLEY],
            "keywords": ["distribution", "universal quantifier", "conjunction",
                         "infinitary meet", "scope"],
            "ops": [LOG_EQUIV, AND, FORALL_OP],
        },
    },
    {
        "name": "existential_disjunction_distribution",
        "topic_id": "quantification",
        "archetype": "binder_join_distribution",
        "cls": "identity",
        "status": "derived",
        "template": TPL_EXISTS_JOIN,
        "invariants": [
            "EXISTS distributes over JOIN in both directions — the dual "
            "regrouping law, with the big join in place of the big meet.",
            "Mirror-symmetric to universal_conjunction_distribution under the "
            "NEG duality of the quantifier De Morgan pair: negate both sides "
            "and both laws exchange, which is how one is classically derived "
            "from the other.",
            "The MEET analogue is deliberately ABSENT for the dual reason: "
            "∃x (Fx ∧ Gx) implies (∃x Fx) ∧ (∃x Gx) but not conversely — the "
            "two witnesses need not coincide.",
            "Valid intuitionistically in both directions.",
        ],
        "logic": {
            "title": "Existential Quantifier Distributes over Disjunction",
            "ascii": "(exists x. F(x) or G(x)) = (exists x. F(x)) or (exists x. G(x))",
            "latex": "\\exists x\\,(F(x) \\lor G(x)) \\equiv (\\exists x\\, F(x)) \\lor (\\exists x\\, G(x))",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "(∃ x, F x ∨ G x) ↔ (∃ x, F x) ∨ (∃ x, G x)"},
                {"form_id": "big_join", "notation_system": "ascii",
                 "expression": "join_x (F(x) or G(x)) = (join_x F(x)) or (join_x G(x))",
                 "scope_note": "The infinitary-lattice reading: regrouping a big join of joins"},
            ],
            "symbols": [PRED_SYM, PREDB_SYM, VAR_SYM],
            "meaning": "Something satisfies one property or the other exactly "
                       "when something satisfies the first or something "
                       "satisfies the second.",
            "significance": "The case-split law for existence proofs: a "
                            "witness for a disjunctive property is a witness "
                            "for one of its disjuncts, and conversely either "
                            "separate witness serves. With its ∀/∧ mirror it "
                            "completes the pair of valid distribution "
                            "equations — the two invalid mixtures are recorded "
                            "as failure modes on both nodes, which is the "
                            "corpus's way of stating a non-law without "
                            "authoring a false node.",
            "conditions": ["None beyond first-order semantics: valid "
                           "classically and intuitionistically"],
            "failure_modes": [
                "The MEET analogue fails: some integer is even and some is "
                "odd, but none is both — (∃x Fx) ∧ (∃x Gx) does not produce a "
                "single witness for ∃x (Fx ∧ Gx).",
                "In free logics the empty domain trivializes both sides to "
                "false; the equivalence survives but carries no content.",
            ],
            "provenance": [FREGE, PRINCIPIA, ENDERTON_LOGIC, MENDELSON,
                           DAVEY_PRIESTLEY],
            "keywords": ["distribution", "existential quantifier",
                         "disjunction", "infinitary join", "witness"],
            "ops": [LOG_EQUIV, OR, EXISTS_OP],
        },
    },
    {
        "name": "universal_implies_existential",
        "topic_id": "quantification",
        "archetype": "domain_inhabitation_entailment",
        "cls": "theorem",
        "status": "derived",
        "template": TPL_FORALL_TO_EXISTS,
        "entailed_by": ["universal_instantiation", "existential_generalization"],
        "invariants": [
            "The only node in the corpus whose truth depends on the DOMAIN "
            "rather than on the connectives: over an empty domain the "
            "universal is vacuously true and the existential false, so the "
            "inhabitation condition is the entire content.",
            "Composes the two rule nodes it is entailed by: instantiate the "
            "universal at any inhabitant, then generalize the instance "
            "existentially.",
            "Same body under both binders — the recurrence pattern "
            "distinguishes it from instantiation and generalization, whose "
            "second predicate application takes a free term.",
        ],
        "logic": {
            "title": "A Universal Entails an Existential (Inhabited Domain)",
            "ascii": "(forall x. F(x)) implies (exists x. F(x))",
            "latex": "(\\forall x\\, F(x)) \\to (\\exists x\\, F(x))",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "(∀ x, F x) → (∃ x, F x)"},
                {"form_id": "square_of_opposition", "notation_system": "ascii",
                 "expression": "the A proposition entails the I proposition",
                 "scope_note": "Subalternation on the traditional square of opposition, valid only with existential import"},
            ],
            "symbols": [PRED_SYM, VAR_SYM],
            "meaning": "If everything has the property and there is anything "
                       "at all, then something has the property.",
            "significance": "The hinge between the two binder heads, and the "
                            "corpus's record of the inhabitation subtlety that "
                            "modern logic extracted from the medieval square "
                            "of opposition: subalternation is not free — it is "
                            "purchased by the assumption that the domain is "
                            "nonempty, which mathlib encodes as the "
                            "`Nonempty` instance this statement's Lean form "
                            "requires.",
            "conditions": ["The domain of quantification is inhabited "
                           "(nonempty) — the load-bearing hypothesis"],
            "failure_modes": [
                "Empty domain: ∀x F(x) holds vacuously while ∃x F(x) fails — "
                "the inclusive-logic counterexample that dismantled the "
                "traditional square of opposition.",
                "Sortal slippage: inhabitation must hold for the SORT x "
                "ranges over, not for some ambient superset.",
            ],
            "provenance": [ARISTOTLE, FREGE, ENDERTON_LOGIC, MENDELSON],
            "keywords": ["subalternation", "existential import",
                         "inhabited domain", "square of opposition"],
            "ops": [IMPL, FORALL_OP, EXISTS_OP],
        },
    },
    {
        "name": "unique_existence_expansion",
        "topic_id": "quantification",
        "archetype": "unique_existence_definiens",
        "cls": "definition",
        "status": "formal",
        "template": TPL_UNIQUE_EXISTENCE,
        "invariants": [
            "The definiendum ∃! deliberately has NO head of its own: the "
            "corpus expresses unique existence only through this expansion, "
            "so the template is the bare definiens, stated the way ex falso "
            "states its bare schema.",
            "Nested binders of both kinds with the inner body an EQUATION "
            "between the two bound slots — the recurrence pattern (x free in "
            "the uniqueness clause, y bound inside it) is the whole content "
            "of 'at most one'.",
            "Existence and uniqueness are the MEET's two conjuncts, and each "
            "is strictly weaker than the whole: dropping either conjunct is "
            "the standard misreading.",
            "Lean's `ExistsUnique` unfolds to exactly this shape, which is "
            "what licenses the coverage classifier's ∃!-desugar: an ingested "
            "`∃! x, P x` is expressible if and only if this expansion is.",
        ],
        "logic": {
            "title": "Unique Existence, Expanded",
            "ascii": "exists! x. F(x) = exists x. (F(x) and forall y. (F(y) implies y = x))",
            "latex": "\\exists! x\\, F(x) \\;\\equiv\\; \\exists x\\,\\bigl(F(x) \\land \\forall y\\,(F(y) \\to y = x)\\bigr)",
            "forms": [
                {"form_id": "unicode", "notation_system": "ascii",
                 "expression": "(∃! x, F x) ↔ (∃ x, F x ∧ ∀ y, F y → y = x)"},
                {"form_id": "split", "notation_system": "ascii",
                 "expression": "(exists x. F(x)) and (forall y z. F(y) and F(z) implies y = z)",
                 "scope_note": "The equivalent existence-plus-at-most-one split, with uniqueness stated symmetrically"},
            ],
            "symbols": [PRED_SYM, VAR_SYM, VAR2_SYM],
            "meaning": "Exactly one thing has the property: something has it, "
                       "and anything that has it is that very thing.",
            "significance": "The definition that turns 'the' into a "
                            "well-formed operator — every definite description "
                            "and every well-definedness proof of a function "
                            "value rests on this expansion (Russell's theory "
                            "of descriptions is its use). For the coverage "
                            "instrument it is load-bearing: 7,099 Goedel-Pset "
                            "goals are ∃!-statements, and each is classified "
                            "by expanding to this definiens of carried heads "
                            "rather than by inventing an EXISTSUNIQUE head "
                            "the corpus does not state laws for.",
            "conditions": ["Equality is available in the object language "
                           "(first-order logic with equality)"],
            "failure_modes": [
                "Dropping the uniqueness clause silently weakens 'the "
                "solution' to 'a solution'; dropping existence turns a "
                "definite description into a vacuous one.",
                "Uniqueness up to WHICH equivalence matters: unique up to "
                "equality, isomorphism, or permutation are different claims, "
                "and only the first is this definition.",
            ],
            "provenance": [FREGE, PRINCIPIA, ENDERTON_LOGIC, MENDELSON, MATHLIB],
            "keywords": ["unique existence", "definite description",
                         "uniqueness", "well-definedness", "ExistsUnique"],
            "ops": [EXISTS_UNIQUE_OP, AND, IMPL, EQ, FORALL_OP, EXISTS_OP],
        },
    },
]

ALL_LAWS = SHARED_LAWS + DISCIPLINE_ONLY_LAWS + QUANTIFIER_LAWS

TOPIC_META = {
    ("logic", "boolean_laws"): ("propositional_logic", "boolean_laws"),
    ("logic", "inference"): ("propositional_logic", "inference_rules"),
    ("logic", "quantification"): ("predicate_logic", "quantifier_laws"),
    ("set_theory", "boolean_laws"): ("algebra_of_sets", "boolean_laws"),
    ("set_theory", "order"): ("algebra_of_sets", "inclusion_order"),
    ("set_theory", "cardinality"): ("combinatorial_set_theory", "finite_cardinality"),
}

CANONICAL_OBJECTS = {
    "logic": ["proposition", "truth value", "Lindenbaum-Tarski algebra",
              "Boolean lattice"],
    "set_theory": ["set", "universe of discourse", "powerset algebra",
                   "Boolean lattice"],
}

# One-sided `composed_with` edges into other corpora. Only `composed_with` is
# safe across corpora without writing the reciprocal edge (docs/BACKLOG.md).
# `equivalent_to` between two *differently named* laws in this file, as opposed
# to the two readings of one shared law (which build_links derives from the
# spec having both discipline keys). Only one pair needs it: hypothetical
# syllogism and subset transitivity are one lattice statement, but they sit in
# different topics (`inference` / `order`) under names their own disciplines
# use, so they could not be folded into a single shared law without renaming an
# existing node. Reciprocity is checked over the merged graph and both ends are
# generated here, so the pair closes without touching another corpus.
CROSS_LAW_EQUIVALENT = {
    ("logic", "hypothetical_syllogism"): ["settheory.order.subset_transitivity"],
    ("set_theory", "subset_transitivity"): ["logic.inference.hypothetical_syllogism"],
}

CROSS_CORPUS = {
    ("set_theory", "inclusion_exclusion_two_sets"): [
        "probstat.probability.total_probability_partition",
        "probstat.probability.bayes_rule",
    ],
    ("set_theory", "complement_laws"): [
        "probstat.probability.total_probability_partition",
    ],
}


def qid(discipline: str, spec: dict) -> str:
    return f"{ID_PREFIX[discipline]}.{spec['topic_id']}.{spec['name']}"


def build_links(discipline: str, spec: dict) -> dict:
    by_name = {s["name"]: s for s in ALL_LAWS}

    def local(name: str) -> str:
        return qid(discipline, by_name[name])

    entailed_by = [local(n) for n in spec.get("entailed_by", [])]
    entails = [local(n) for n in spec.get("entails", [])]

    # Reciprocals implied by other specs' declarations, so each corpus's
    # lineage graph closes without hand-maintaining both directions.
    for other in ALL_LAWS:
        if discipline not in other:
            continue
        if spec["name"] in other.get("entails", []):
            ref = local(other["name"])
            if ref not in entailed_by:
                entailed_by.append(ref)
        if spec["name"] in other.get("entailed_by", []):
            ref = local(other["name"])
            if ref not in entails:
                entails.append(ref)

    # The cross-discipline twin edge. `equivalent_to` rather than a weaker
    # relation because the two nodes are the same theorem of the same Boolean
    # algebra read over two carriers, not merely isomorphic in shape; both
    # directions are written here, which is what the merged-graph reciprocity
    # check requires.
    equivalent_to = []
    twin = "set_theory" if discipline == "logic" else "logic"
    if twin in spec:
        equivalent_to.append(qid(twin, spec))
    equivalent_to.extend(CROSS_LAW_EQUIVALENT.get((discipline, spec["name"]), []))

    composed_with = list(CROSS_CORPUS.get((discipline, spec["name"]), []))
    # Every node in a corpus composes with the postulates it is stated over.
    if spec["name"] not in {"identity_laws", "complement_laws",
                            "distributivity_meet_over_join"}:
        for post in ("identity_laws", "complement_laws"):
            ref = local(post)
            if ref not in entailed_by and ref not in entails and ref not in composed_with:
                composed_with.append(ref)

    return {"entailed_by": sorted(set(entailed_by)), "entails": sorted(set(entails)),
            "equivalent_to": sorted(set(equivalent_to)),
            "special_case_of": [], "generalizes": [],
            "composed_with": sorted(set(composed_with))}


def build_node(discipline: str, spec: dict) -> dict:
    content = spec[discipline]
    subfield, topic = TOPIC_META[(discipline, spec["topic_id"])]
    template = render(spec["template"], discipline)
    codomain = LOGIC_CODOMAIN if discipline == "logic" else SET_CODOMAIN

    heads = [h for h in ("MEET", "JOIN", "NEG", "LEQ", "IMPLIES", "CARD",
                         "FORALL", "EXISTS")
             if f"{h}(" in template]
    functionals = fns(*heads, codomain_override=codomain)

    # Quantifier nodes carry their own symbol set (schematic predicates, bound
    # variables, instantiating terms); everything else keeps the shared
    # proposition/set letters sized to the operand count.
    if "symbols" in content:
        symbols = content["symbols"]
    else:
        symbols = P_SYMS if discipline == "logic" else A_SYMS
        used = tpl_keys(spec["template"])
        n_operands = sum(1 for k in used if k in {"a", "b", "c"})
        symbols = symbols[:max(1, n_operands)]

    node = {
        "statement_id": qid(discipline, spec),
        "title": content["title"],
        "statement_class": spec["cls"],
        "epistemic_status": spec["status"],
        "theory_context": {
            "disciplines": [discipline],
            "subfield": subfield,
            "topic": topic,
            "canonical_objects": CANONICAL_OBJECTS[discipline],
        },
        "formal_statement": {
            "canonical_ascii": content["ascii"],
            "canonical_latex": content["latex"],
            "equivalent_forms": content["forms"],
        },
        "structural_signature": {
            "archetype_id": spec["archetype"],
            "anonymized_template": template,
            "slot_schema": slots_for(spec["template"], discipline),
            "invariants": spec["invariants"],
        },
        "symbol_lexicon": {
            "symbols": symbols,
            "operators": content["ops"],
            "functionals": functionals,
            "index_sets": [],
            "constants": content.get("constants", []),
        },
        "semantic_interpretation": {
            "statement_meaning": content["meaning"],
            "statistical_significance": content["significance"],
            "regularity_conditions": content["conditions"],
            "failure_modes": content["failure_modes"],
        },
        "inferential_links": build_links(discipline, spec),
        "provenance": content["provenance"],
        "keywords": content["keywords"],
    }
    # The truth/provability bridge. Logic corpus only -- see VERIFIED_BY above.
    if discipline == "logic" and spec["name"] in VERIFIED_BY:
        node["verified_by"] = VERIFIED_BY[spec["name"]]
    return node


CORPUS_META = {
    "logic": ("logic.boolean_foundations.v1", "logic"),
    "set_theory": ("set_theory.boolean_foundations.v1", "set_theory"),
}


def main() -> None:
    artifact_note = check_verified_by()
    for discipline, (corpus_id, disc_field) in CORPUS_META.items():
        nodes = [build_node(discipline, spec) for spec in ALL_LAWS
                 if discipline in spec]
        corpus = {
            "schema": "../../schema/equation-node.schema.json",
            "corpus_id": corpus_id,
            "discipline": disc_field,
            "version": "1.0.0-alpha",
            "statement_nodes": nodes,
        }
        out = Path("data") / discipline / "nodes.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        bridged = sum(1 for n in nodes if "verified_by" in n)
        print(f"wrote {len(nodes)} {discipline} nodes -> {out}"
              + (f" ({bridged} carry verified_by)" if bridged else ""))
    print(f"verified_by: {artifact_note}")


if __name__ == "__main__":
    main()
