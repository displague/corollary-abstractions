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
further theorem, not part of the artifact). Nine of the eleven logic nodes
carry a bridge, covering all 16 extracted theorems. The two that do not are
the falsehood pair, which is the ladder's VERIFIED-vs-PROVEN distinction
showing up as a real gap rather than a slogan.

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
TPL_SUBSET_TRANSITIVITY = "IMPLIES(MEET(LEQ({a}, {b}), LEQ({b}, {c})), LEQ({a}, {c}))"
TPL_INCLUSION_EXCLUSION = (
    "CARD(JOIN({a}, {b})) = CARD({a}) + CARD({b}) - CARD(MEET({a}, {b}))"
)

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
               "top": "TRUTH", "bot": "FALSITY"}
LOGIC_CATS = {"a": "variable", "b": "variable", "c": "variable",
              "top": "constant", "bot": "constant"}
LOGIC_ROLES = {"a": "propositional_operand", "b": "propositional_operand",
               "c": "propositional_operand",
               "top": "top_element", "bot": "bottom_element"}

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
}


def fns(*names, codomain_override=None):
    out = []
    for n in names:
        entry = dict(LATTICE_FN[n])
        if n in {"MEET", "JOIN", "NEG", "LEQ", "IMPLIES"} and codomain_override:
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
# a law here states a self-dual pair while Lean proves each half separately,
# and because De Morgan additionally gets its quantifier form.
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
    "de_morgan_laws": lean("de_morgan_not_and", "de_morgan_not_or",
                           "not_forall_iff_exists_not"),
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
        "name": "subset_transitivity",
        "topic_id": "order",
        "archetype": "order_transitivity",
        "cls": "theorem",
        "status": "derived",
        "template": TPL_SUBSET_TRANSITIVITY,
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
                            "without either corpus being rewritten.",
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

ALL_LAWS = SHARED_LAWS + DISCIPLINE_ONLY_LAWS

TOPIC_META = {
    ("logic", "boolean_laws"): ("propositional_logic", "boolean_laws"),
    ("logic", "inference"): ("propositional_logic", "inference_rules"),
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

    heads = [h for h in ("MEET", "JOIN", "NEG", "LEQ", "IMPLIES", "CARD")
             if f"{h}(" in template]
    functionals = fns(*heads, codomain_override=codomain)

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
