#!/usr/bin/env python3
"""Semantic correspondence between a Lean theorem and the statement citing it.

`scripts/validate_nodes.py`'s `verified_by_errors` is the PROVENANCE rung: it
proves the artifact is repository-contained, that every row is a complete
state-tactic-state transition, that the cited theorem exists and closes to
`no goals`, and that no two statements claim one theorem. It says nothing about
whether the theorem PROVES the statement citing it, and its own capability-blind
control demonstrates the hole: a real gravity statement citing
`BooleanLaws.modus_ponens` passes.

This module is the SEMANTIC rung. For one `verified_by` link it:

1. reads the theorem's INITIAL goal state out of the artifact (the transition
   state that no transition of that theorem produces, and that carries no
   `case` label -- an order-independent rule, so reordering artifact rows
   cannot choose a different "first" goal);
2. translates that goal from the declared Lean fragment into the corpus template
   grammar (MEET / JOIN / NEG / IMPLIES over slots, with TRUTH and FALSITY as
   constant slots);
3. skeletonizes it with `match_signatures`' own tokenizer, parser,
   canonicalizer and `skeleton` -- the same front end the twin matcher runs over
   `anonymized_template`, not a private re-implementation -- with ONE declared
   refinement, applied identically to both sides: the lattice poles TOP and BOT
   do not share a slot class (see `LATTICE_POLES`);
4. compares it against the citing statement's DECLARED FORM SET and reports
   CORRESPONDS / MISMATCH / UNTRANSLATABLE.

**What a CORRESPONDS verdict is not.** It is a statement about SHAPE. It says
the theorem's opening goal, translated and skeletonized, is one of the forms the
citing statement declares. It does NOT say the statement is true, it does not
say the theorem proves this statement rather than a structural twin, and it is
not semantic ownership. "Byte integrity alone is not semantic ownership" is a
FLOOR this rung clears, not a ceiling it reaches. Nothing here -- and nothing in
a `scripts/write_stage.py` receipt -- may be read as certifying the truth of the
statement; truth lives in the Lean theorem, and correspondence only says which
proposition the theorem is about.

Four design decisions are load-bearing and are argued rather than assumed.

**The declared fragment (fail closed on the rest).** A goal translates only if
every hypothesis line binds names at type `Prop` and the goal is built from `not`,
`and`, `or`, `implies`, `True`, `False`, parentheses, those bound propositional
names, and at most one TOP-LEVEL `iff`. Types, predicates, `forall`, `exists`,
arithmetic, nested `iff` and every other Lean term are UNTRANSLATABLE -- never
MISMATCH. Refusing to translate is not evidence of a wrong citation, and
collapsing the two would let this check manufacture false accusations exactly
where it is weakest. The corpus contains one such link today
(`BooleanLaws.not_forall_iff_exists_not`, a first-order theorem); its citing node
declares a matching first-order equivalent form, so the citation is honest and
merely outside this rung's reach.

**The target is the statement's DECLARED FORM SET, not `anonymized_template`
alone.** Six of the sixteen committed links cite the DUAL law: the De Morgan node
whose canonical template is `NEG(MEET(..)) = JOIN(NEG(..), NEG(..))` also cites
`de_morgan_not_or`, whose goal is the meet/join mirror image. Every one of these
nodes declares that dual in `equivalent_forms`, and several declare their
invariants as self-dual pairs. A check that compared against the canonical
template alone would report six honest citations as MISMATCH -- not a stricter
gate, a broken one. The form set is therefore

  * the canonical `anonymized_template`;
  * its BOOLEAN DUAL, under the declared involution MEET<->JOIN,
    TRUTH<->FALSITY, UNIVERSE<->EMPTYSET (NEG is self-dual), offered ONLY for
    templates whose call heads are a subset of {MEET, JOIN, NEG}. Order-sensitive
    heads (IMPLIES, LEQ, LT, ...) have a dual that also reverses the order, which
    this table does not represent, so they get no dual rather than a wrong one;
  * each `equivalent_forms` entry that the same fragment can translate.

Which route matched is RECORDED per link (`matched_route`), so a reviewer can see
when a link is carried by a declared variant rather than by the canonical form.
That visibility is the price of the widening, and it exposes a real corpus
finding: `logic.boolean_laws.double_negation` files the one-directional
`P implies not(not P)` under `equivalent_forms`, so this check would accept a
theorem proving only that half. See docs/DISCOVERIES.md.

**A lattice constant is an object, not a placeholder.** The twin matcher folds
every parameter-like slot into one class `P`, which is right for asking "same
shape?" and catastrophic for asking "does this theorem prove this?": under it,
`MEET(PROP1, TRUTH) = TRUTH` and `MEET(PROP1, FALSITY) = FALSITY` are the same
skeleton, and a proof of `P ∧ False ↔ False` certified the FALSE claim
`P and true = true` through every gate. Correspondence therefore splits the two
lattice POLES (TOP, BOT) into distinct classes -- on the Lean side and the
corpus side alike, and only inside this module. Spellings of ONE pole (TRUTH
and UNIVERSE) are still not distinguished, deliberately: that is the corpus's
own cross-discipline claim, and `ambiguous_with` is where this module admits it
cannot choose between them. See `LATTICE_POLES`.

**An asserted proposition is an equation.** A theorem `A` with no top-level `iff`
is, in the Lindenbaum-Tarski algebra the corpus already works in, the equation
`A = TOP`. The normalisation is applied UNIFORMLY to both sides -- to Lean goals
and to corpus templates alike -- so it never creates a match between a bare form
and an equational one unless that equation's other side is literally TRUTH. It is
what lets `modus_ponens` (a bare implication on both sides) and
`non_contradiction` (`not(P and not P)`) be compared at all.

**What this still cannot do.** Skeleton correspondence is STRUCTURAL, and
structure is exactly what the corpus's cross-discipline twins share: every
`logic.boolean_laws.*` statement has a `settheory.boolean_laws.*` twin with a
character-identical skeleton. This check therefore reports `ambiguous_with` --
the other statements whose declared form set also contains the theorem's
skeleton -- and relies on `verified_by_errors`' exclusive-ownership rule to keep
only one of them citing it. The two checks together prove "one statement owns
this theorem, and its structure matches"; they do NOT prove that the right one of
two structural twins owns it. Do not read a CORRESPONDS verdict as more than
that.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - CLI import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from match_signatures import (  # noqa: E402
    Parser,
    TemplateParseError,
    canonicalize,
    skeleton,
    slot_classes,
    template_call_heads,
    template_slots,
    tokenize,
)
from proof_artifacts import (  # noqa: E402
    resolve_contained_artifact,
    select_closing_transitions,
)


REPO_ROOT = Path(__file__).resolve().parents[1]

CORRESPONDS = "CORRESPONDS"
MISMATCH = "MISMATCH"
UNTRANSLATABLE = "UNTRANSLATABLE"


class Untranslatable(ValueError):
    """The input is outside the declared fragment. Never a MISMATCH."""


# --------------------------------------------------------------------------
# The declared fragment: one abstract syntax, two surface dialects
#
# Both dialects tokenize into the SAME connective vocabulary, so there is one
# parser and one precedence ladder for Lean goal states and for the corpus's
# ASCII `equivalent_forms`. Anything not in these tables raises Untranslatable.
# --------------------------------------------------------------------------

_CONNECTIVES = {
    # Lean surface
    "¬": "not", "∧": "and", "∨": "or", "→": "imp", "↔": "iff",
    "True": "TRUE", "False": "FALSE",
    # ASCII / corpus surface
    "not": "not", "and": "and", "or": "or", "implies": "imp",
    "=": "iff", "≡": "iff", "true": "TRUE", "false": "FALSE",
    # Unicode lattice constants as the corpora spell them
    "⊤": "TRUE", "⊥": "FALSE",
}

# Binding power, tightest first. Identical in both dialects, and identical to
# Lean's own (`¬` 40 > `∧` 35 > `∨` 30 > `→` 25 > `↔` 20), so
# `P ∨ Q ∧ R ↔ (P ∨ Q) ∧ (P ∨ R)` parses the way Lean printed it.
_BINARY_PRECEDENCE = {"and": 35, "or": 30, "imp": 25, "iff": 20}
_RIGHT_ASSOCIATIVE = {"and", "or", "imp"}

_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_']*")
_SURFACE = re.compile(
    "|".join(
        (
            r"[A-Za-z_][A-Za-z0-9_']*",  # words: names and word-connectives
            r"[¬∧∨→↔⊤⊥≡=()]",           # single-character connectives
        )
    )
)


def _lex(text: str) -> list[str]:
    """Split a fragment surface string, refusing any unrecognised character."""

    tokens: list[str] = []
    pos = 0
    while pos < len(text):
        if text[pos].isspace():
            pos += 1
            continue
        match = _SURFACE.match(text, pos)
        if not match:
            raise Untranslatable(
                f"unsupported character {text[pos]!r} in {text.strip()!r}"
            )
        tokens.append(match.group(0))
        pos = match.end()
    if not tokens:
        raise Untranslatable("empty proposition")
    return tokens


class _FragmentParser:
    """Precedence-climbing parser for the declared propositional fragment.

    Produces `("var", name)`, `("const", "TRUE"|"FALSE")`, `("not", a)` or
    `(op, a, b)` for op in {and, or, imp, iff}.
    """

    def __init__(self, tokens: list[str], names: frozenset[str]):
        self.tokens = tokens
        self.names = names
        self.i = 0

    def peek(self) -> str | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def next(self) -> str:
        token = self.peek()
        if token is None:
            raise Untranslatable("proposition ends early")
        self.i += 1
        return token

    def parse(self) -> tuple:
        tree = self.expression(0)
        if self.peek() is not None:
            raise Untranslatable(f"trailing token {self.peek()!r}")
        return tree

    def expression(self, minimum: int) -> tuple:
        left = self.atom()
        while True:
            token = self.peek()
            symbol = _CONNECTIVES.get(token) if token is not None else None
            if symbol not in _BINARY_PRECEDENCE:
                return left
            power = _BINARY_PRECEDENCE[symbol]
            if power < minimum:
                return left
            self.next()
            nxt = power if symbol in _RIGHT_ASSOCIATIVE else power + 1
            right = self.expression(nxt)
            if symbol == "iff" and self.i < len(self.tokens):
                # Only a TOP-LEVEL iff is in the fragment; a chained one would
                # need an equivalence head the template grammar does not have.
                raise Untranslatable("chained `iff` is outside the fragment")
            left = (symbol, left, right)

    def atom(self) -> tuple:
        token = self.next()
        if token == "(":
            inner = self.expression(0)
            if self.next() != ")":
                raise Untranslatable("expected `)`")
            return inner
        symbol = _CONNECTIVES.get(token)
        if symbol == "not":
            # `¬` binds tighter than every binary connective.
            return ("not", self.expression(40))
        if symbol in {"TRUE", "FALSE"}:
            return ("const", symbol)
        if symbol is not None:
            raise Untranslatable(f"connective {token!r} in operand position")
        if not _WORD.fullmatch(token):
            raise Untranslatable(f"unsupported token {token!r}")
        if token not in self.names:
            raise Untranslatable(
                f"{token!r} is not a declared propositional name"
            )
        return ("var", token)


def parse_fragment(text: str, names: frozenset[str]) -> tuple:
    return _FragmentParser(_lex(text), names).parse()


# --------------------------------------------------------------------------
# Lean goal states
# --------------------------------------------------------------------------

_GOAL_MARKER = "⊢"
_CASE_LABEL = re.compile(r"^case\s+\S+$")
_PROP_BINDER = re.compile(r"^(?P<names>[^:]+):\s*Prop$")


def initial_goal_state(transitions: tuple[dict, ...]) -> str:
    """The theorem's opening goal, chosen order-independently.

    A theorem's transitions form a forest whose roots are the states no
    transition produces; branching tactics leave several such roots, but Lean
    labels every state below the first branch with a `case` tag. The opening
    goal is the unique unlabelled root. Taking "the artifact's first row"
    instead would let an attacker who can reorder rows nominate a different
    proposition as the thing proved, so the rule is deliberately independent of
    row order; ambiguity fails closed.

    Order-independent is NOT tamper-proof, and the difference matters. Adding a
    row whose `stateAfter` is the real opening goal demotes it from root and
    promotes a decoy in its place. That cannot be detected structurally --
    unlabelled non-root states occur legitimately (`intro h` on
    `BooleanLaws.modus_ponens` produces one) -- so the defence is the artifact
    DIGEST PIN, not this function: `scripts/write_stage.py` refuses a candidate
    whose artifact bytes do not match the pin, and `scripts/retrieval.py` marks
    an unpinned artifact untrusted. Row insertion is byte-level tampering and
    is caught there.
    """

    produced = {row["stateAfter"] for row in transitions}
    roots = {
        row["stateBefore"]
        for row in transitions
        if row["stateBefore"] not in produced
    }
    unlabelled = sorted(
        state
        for state in roots
        if not _CASE_LABEL.match(state.replace("\r\n", "\n").split("\n", 1)[0].strip())
    )
    if len(unlabelled) != 1:
        raise Untranslatable(
            f"theorem has {len(unlabelled)} unlabelled root goal states; "
            "an opening goal cannot be identified"
        )
    return unlabelled[0]


def read_goal(state: str) -> tuple[str, frozenset[str]]:
    """Split a goal state into (goal text, declared propositional names).

    Windows-newline safe: the artifact is committed text and a CRLF checkout
    must not change which proposition a theorem is read to prove.
    """

    lines = [
        line.strip()
        for line in state.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        if line.strip()
    ]
    goals = [line for line in lines if line.startswith(_GOAL_MARKER)]
    if len(goals) != 1:
        raise Untranslatable(
            f"goal state carries {len(goals)} goals; exactly one is required"
        )
    goal = goals[0][len(_GOAL_MARKER):].strip()
    names: set[str] = set()
    for line in lines:
        if line.startswith(_GOAL_MARKER) or _CASE_LABEL.match(line):
            continue
        binder = _PROP_BINDER.match(line)
        if not binder:
            raise Untranslatable(
                f"hypothesis {line!r} does not bind names at type `Prop`"
            )
        for name in binder.group("names").split():
            if not _WORD.fullmatch(name):
                raise Untranslatable(f"unsupported binder name {name!r}")
            names.add(name)
    if not names:
        raise Untranslatable("goal state binds no propositional names")
    return goal, frozenset(names)


# --------------------------------------------------------------------------
# Fragment -> corpus template grammar
# --------------------------------------------------------------------------

_TEMPLATE_HEAD = {"and": "MEET", "or": "JOIN", "imp": "IMPLIES"}
_TEMPLATE_CONST = {"TRUE": "TRUTH", "FALSE": "FALSITY"}
# Slot categories the emitted template implies. `constant` is what the corpora
# declare for TRUTH / FALSITY / UNIVERSE / EMPTYSET, and PARAMETER_LIKE maps it
# to the typed skeleton's `P`; propositional names are variables (`V`).
#
# This is the COARSE category only, and it is deliberately the same coarse
# category the corpus side derives from `slot_schema` -- see
# `equation_classes`. The identity of a lattice constant is restored later, at
# skeleton time, by `correspondence_classes`, uniformly on both sides.
EMITTED_SLOT_CLASSES = {"TRUTH": "P", "FALSITY": "P"}


def emit_template(tree: tuple) -> tuple[str, dict[str, str]]:
    """Render a fragment tree as corpus template text plus its slot classes.

    A tree whose top level is not `iff` is emitted as `<expr> = TRUTH`: a
    theorem asserting `A` is the Boolean equation `A = TOP`.
    """

    order: dict[str, str] = {}
    classes: dict[str, str] = {}

    def render(node: tuple) -> str:
        kind = node[0]
        if kind == "var":
            slot = order.setdefault(node[1], f"PROP{len(order) + 1}")
            classes[slot] = "V"
            return slot
        if kind == "const":
            slot = _TEMPLATE_CONST[node[1]]
            classes[slot] = EMITTED_SLOT_CLASSES[slot]
            return slot
        if kind == "not":
            return f"NEG({render(node[1])})"
        head = _TEMPLATE_HEAD.get(kind)
        if head is None:  # pragma: no cover - guarded by the parser
            raise Untranslatable(f"no template head for {kind!r}")
        return f"{head}({render(node[1])}, {render(node[2])})"

    if tree[0] == "iff":
        text = f"{render(tree[1])} = {render(tree[2])}"
    else:
        text = f"{render(tree)} = TRUTH"
        classes["TRUTH"] = "P"
    return text, classes


def parse_template(text: str) -> tuple:
    """Parse corpus template text with the matcher's own front end."""

    try:
        return canonicalize(Parser(tokenize(text)).parse())
    except TemplateParseError as exc:
        raise Untranslatable(f"template does not parse: {text!r} ({exc})") from exc


def as_equation(tree: tuple) -> tuple:
    """Normalise an asserted proposition into `proposition = TRUTH`."""

    if tree[0] == "rel":
        return tree
    return canonicalize(("rel", "=", (tree, ("slot", "TRUTH"))))


def equation_classes(tree: tuple, classes: dict[str, str]) -> dict[str, str]:
    """Slot classes for `as_equation(tree)`.

    The synthesized TRUTH is a lattice bound, so it must carry the SAME coarse
    category (`P`, parameter-like) that the corpora declare when they write it
    out -- `logic.boolean_laws.identity_laws` declares `TRUTH` as `constant`.
    Without this the typed skeleton of a bare template like
    `IMPLIES(MEET(IMPLIES(PROP1, PROP2), PROP1), PROP2)` classes its synthesized
    TRUTH as a variable while the Lean side classes it as a constant, and
    `modus_ponens` fails to match its own canonical form -- which is exactly what
    the first run of this module reported, caught only because `matched_route`
    records WHICH form carried a link (it had fallen through to the node's
    unicode `equivalent_forms` entry). A statement that declares the slot itself
    keeps its own declaration.
    """

    if tree[0] == "rel":
        return dict(classes)
    return {"TRUTH": "P", **classes}


# --------------------------------------------------------------------------
# Constant identity: a lattice bound is an OBJECT, not a placeholder
# --------------------------------------------------------------------------

# `match_signatures.slot_classes` folds every `parameter` and `constant` slot
# into ONE coarse class `P`, and the typed skeleton renders a slot as
# `?<index>:<class>`. That is right for the twin MATCHER, whose question is "do
# these two statements have the same shape?": `CONSTANT * RADIUS` and
# `MASS * RADIUS` should group, and the matcher is not asserting either is true.
#
# It is wrong for a PROOF gate, whose question is "does this theorem prove this
# statement?", because a lattice bound is not a placeholder -- TRUTH denotes TOP
# and nothing else. Under the coarse class alone, `MEET(PROP1, TRUTH) = TRUTH`
# and `MEET(PROP1, FALSITY) = FALSITY` both skeletonize to
# `?0:P = MEET⟨?0:P, ?1:V⟩`, so a Lean proof of `P ∧ False ↔ False` -- a TRUE
# theorem -- certified the canonical claim `P and true = true` -- a FALSE one --
# as CORRESPONDS, and carried it through all fourteen gates of
# `scripts/write_stage.py` into a STAGED_CANDIDATE. Found by adversarial review
# of this branch; it is the headline defect of the item.
#
# The refinement is LOCAL TO CORRESPONDENCE. `match_signatures` is untouched, so
# the matcher's own typed skeletons -- and the matcher-delta prediction the
# WRITE gate measures against them -- are exactly what they were.
#
# Constants are separated by what they DENOTE, not by how they are spelled, and
# that choice is load-bearing in both directions:
#
# * separating the POLES is the fix: TOP and BOT are different objects, so
#   TRUTH and FALSITY (and UNIVERSE and EMPTYSET) can never unify again;
# * NOT separating spellings of one pole is equally deliberate. The corpus's
#   whole cross-discipline thesis is that TRUTH over propositions and UNIVERSE
#   over subsets are one object read twice, and this module's `ambiguous_with`
#   reporting exists to say out loud that structure cannot choose between those
#   two readings. Keying constants by spelling would make
#   `logic.boolean_laws.identity_laws` and `settheory.boolean_laws.identity_laws`
#   structurally distinct and silently delete that admission -- a check claiming
#   more discriminating power than it has, which is the failure mode this whole
#   module is written against.
#
# A parameter-like slot the table does not name keeps the coarse `P` and so
# matches no Lean-emitted constant at all: `narrative.frame.frame_consistency`
# writes BOT as `INCONSISTENCY`, and fail-closed is the right answer for an
# undeclared spelling (the declared-dual code refuses it on the same grounds).
LATTICE_POLES = {
    "TRUTH": "TOP",
    "UNIVERSE": "TOP",
    "FALSITY": "BOT",
    "EMPTYSET": "BOT",
}


def correspondence_classes(
    tree: tuple, classes: dict[str, str]
) -> dict[str, str]:
    """Refine slot classes so the two lattice poles can never unify.

    Applied to BOTH sides of every comparison -- Lean-emitted templates and
    corpus-declared ones -- so it can only ever split a match, never create one.
    """

    refined = dict(classes)
    for name in template_slots(tree):
        if classes.get(name, "V") != "P":
            continue
        pole = LATTICE_POLES.get(name)
        if pole is not None:
            refined[name] = f"P.{pole}"
    return refined


def correspondence_skeleton(tree: tuple, classes: dict[str, str]) -> str:
    """`match_signatures.skeleton` with lattice-constant identity restored."""

    return skeleton(tree, correspondence_classes(tree, classes))


def template_skeleton(text: str, classes: dict[str, str]) -> str:
    raw = parse_template(text)
    return correspondence_skeleton(as_equation(raw), equation_classes(raw, classes))


# --------------------------------------------------------------------------
# The declared Boolean dual
# --------------------------------------------------------------------------

# One global involution, in the style of `match_signatures.TIME_REVERSE_HEADS`:
# a declaration the passes read, not folklore. Boolean duality swaps the lattice
# operations and the lattice bounds; NEG is self-dual, which is precisely what
# De Morgan's laws say.
DUAL_HEADS = {"MEET": "JOIN", "JOIN": "MEET"}
DUAL_SLOTS = {
    "TRUTH": "FALSITY", "FALSITY": "TRUTH",
    "UNIVERSE": "EMPTYSET", "EMPTYSET": "UNIVERSE",
}
# Heads whose dual is order-independent. Anything else -- IMPLIES, LEQ, LT --
# dualizes only with an order reversal this table cannot express, so a template
# containing one is offered NO dual rather than a wrong one.
DUALIZABLE_HEADS = frozenset({"MEET", "JOIN", "NEG"})


def boolean_dual(tree: tuple, classes: dict[str, str]) -> tuple | None:
    """The declared Boolean dual of a template tree, or None if undeclared.

    Refused in three cases, each because dualizing anyway would ADD a form the
    statement does not declare:

    * a call head outside {MEET, JOIN, NEG} -- IMPLIES and the order heads
      dualize with an order reversal this table cannot express;
    * a numeric literal -- duality acts on the lattice, not on arithmetic;
    * a parameter-like (constant) slot with no declared dual spelling. Found by
      adversarial reading of this module's own first output:
      `narrative.frame.frame_consistency` writes BOT as `INCONSISTENCY`, for
      which no corpus declares a TOP spelling, so leaving the constant in place
      produced the FALSE form `JOIN(P, NEG(P)) = INCONSISTENCY` and made that
      node a spurious structural claimant of `BooleanLaws.excluded_middle`.
    """

    if not template_call_heads(tree) <= DUALIZABLE_HEADS:
        return None

    def undualizable(node: tuple) -> bool:
        if node[0] == "num":
            return True
        if node[0] == "slot":
            return (
                classes.get(node[1], "V") == "P" and node[1] not in DUAL_SLOTS
            )
        return any(undualizable(a) for a in node[2])

    if undualizable(tree):
        return None

    def swap(node: tuple) -> tuple:
        kind = node[0]
        if kind == "num":
            return node
        if kind == "slot":
            return ("slot", DUAL_SLOTS.get(node[1], node[1]))
        args = tuple(swap(a) for a in node[2])
        head = node[1]
        if kind == "call":
            head = DUAL_HEADS.get(head, head)
        return (kind, head, args)

    return canonicalize(swap(tree))


def dual_classes(classes: dict[str, str]) -> dict[str, str]:
    swapped = {DUAL_SLOTS.get(name, name): cls for name, cls in classes.items()}
    for name, dual in DUAL_SLOTS.items():
        if name in classes:
            swapped.setdefault(dual, classes[name])
    return swapped


# --------------------------------------------------------------------------
# A statement's declared form set
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class DeclaredForm:
    route: str
    template: str
    skeleton: str


@dataclass(frozen=True)
class FormSet:
    statement_id: str
    forms: tuple[DeclaredForm, ...]
    refused: tuple[str, ...]

    def match(self, target: str) -> DeclaredForm | None:
        for form in self.forms:
            if form.skeleton == target:
                return form
        return None

    @property
    def skeletons(self) -> frozenset[str]:
        return frozenset(form.skeleton for form in self.forms)


def declared_forms(node: dict) -> FormSet:
    """Every form the statement declares AS ITSELF, skeletonized.

    Canonical template, its declared Boolean dual, and each translatable
    `equivalent_forms` entry. Forms outside the fragment are recorded in
    `refused` rather than dropped, so the record shows what was not considered.
    """

    statement_id = node.get("statement_id", "<unknown>")
    forms: list[DeclaredForm] = []
    refused: list[str] = []
    seen: set[str] = set()

    def add(route: str, template: str, skeleton_text: str) -> None:
        if skeleton_text in seen:
            return
        seen.add(skeleton_text)
        forms.append(DeclaredForm(route, template, skeleton_text))

    signature = node.get("structural_signature", {})
    canonical = signature.get("anonymized_template", "")
    classes = slot_classes(node)
    if canonical:
        try:
            raw = parse_template(canonical)
        except Untranslatable as exc:
            refused.append(f"canonical: {exc}")
        else:
            tree = as_equation(raw)
            classes = equation_classes(raw, classes)
            add("canonical", canonical, correspondence_skeleton(tree, classes))
            dual = boolean_dual(tree, classes)
            if dual is not None:
                add(
                    "dual_of_canonical",
                    canonical,
                    correspondence_skeleton(dual, dual_classes(classes)),
                )
    else:
        refused.append("canonical: statement declares no anonymized_template")

    formal = node.get("formal_statement", {})
    ascii_names = _statement_names(node)
    for entry in formal.get("equivalent_forms", []):
        form_id = entry.get("form_id", "<unnamed>")
        expression = entry.get("expression", "")
        try:
            tree = parse_fragment(expression, ascii_names)
            text, emitted = emit_template(tree)
            add(f"equivalent_forms[{form_id}]", expression,
                template_skeleton(text, emitted))
        except Untranslatable as exc:
            refused.append(f"equivalent_forms[{form_id}]: {exc}")

    return FormSet(statement_id, tuple(forms), tuple(refused))


def _statement_names(node: dict) -> frozenset[str]:
    """Symbol names an `equivalent_forms` expression may use as operands."""

    lexicon = node.get("symbol_lexicon", {})
    names = {
        entry.get("symbol", "")
        for entry in lexicon.get("symbols", [])
        if _WORD.fullmatch(entry.get("symbol", ""))
    }
    for slot in node.get("structural_signature", {}).get("slot_schema", []):
        slot_id = slot.get("slot_id", "")
        if _WORD.fullmatch(slot_id):
            names.add(slot_id)
    return frozenset(names)


# --------------------------------------------------------------------------
# Per-link correspondence
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class CorrespondenceResult:
    statement_id: str
    system: str
    artifact: str
    reference: str
    verdict: str
    reason: str
    theorem_skeleton: str | None = None
    theorem_template: str | None = None
    matched_route: str | None = None
    ambiguous_with: tuple[str, ...] = ()
    considered: tuple[str, ...] = ()
    refused_forms: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "statement_id": self.statement_id,
            "system": self.system,
            "artifact": self.artifact,
            "reference": self.reference,
            "verdict": self.verdict,
            "reason": self.reason,
            "theorem_template": self.theorem_template,
            "theorem_skeleton": self.theorem_skeleton,
            "matched_route": self.matched_route,
            "ambiguous_with": list(self.ambiguous_with),
            "considered_forms": list(self.considered),
            "refused_forms": list(self.refused_forms),
        }


def theorem_skeleton(
    artifact_path: Path, reference: str | None
) -> tuple[str, str, str]:
    """Regenerate a formal skeleton from a Lean theorem's opening goal.

    Returns (resolved reference, emitted template text, typed skeleton).
    """

    transitions, resolved = select_closing_transitions(artifact_path, reference)
    goal, names = read_goal(initial_goal_state(transitions))
    tree = parse_fragment(goal, names)
    text, classes = emit_template(tree)
    return resolved, text, template_skeleton(text, classes)


def check_link(
    node: dict,
    link: dict,
    repo_root: Path,
    corpus_forms: dict[str, FormSet] | None = None,
) -> CorrespondenceResult:
    """Adjudicate one `verified_by` link."""

    statement_id = node.get("statement_id", "<unknown>")
    system = link.get("system", "")
    artifact = link.get("artifact", "")
    reference = link.get("reference")

    def fail(verdict: str, reason: str, **extra) -> CorrespondenceResult:
        return CorrespondenceResult(
            statement_id=statement_id,
            system=system,
            artifact=artifact,
            reference=reference or "<unresolved>",
            verdict=verdict,
            reason=reason,
            **extra,
        )

    if system != "lean4":
        return fail(UNTRANSLATABLE, f"unsupported proof system {system!r}")
    try:
        artifact_path = resolve_contained_artifact(repo_root, artifact)
        resolved, text, target = theorem_skeleton(artifact_path, reference)
    except Untranslatable as exc:
        return fail(UNTRANSLATABLE, f"theorem is outside the fragment: {exc}")
    except ValueError as exc:
        # Provenance failures belong to validate_nodes; here they simply mean
        # no skeleton can be regenerated, and the link stays unadjudicated.
        return fail(UNTRANSLATABLE, f"artifact is unreadable: {exc}")

    forms = declared_forms(node)
    if not forms.forms:
        return CorrespondenceResult(
            statement_id=statement_id, system=system, artifact=artifact,
            reference=resolved, verdict=UNTRANSLATABLE,
            reason="statement declares no translatable form",
            theorem_template=text, theorem_skeleton=target,
            refused_forms=forms.refused,
        )

    matched = forms.match(target)
    considered = tuple(f"{f.route}: {f.skeleton}" for f in forms.forms)
    if matched is None:
        return CorrespondenceResult(
            statement_id=statement_id, system=system, artifact=artifact,
            reference=resolved, verdict=MISMATCH,
            reason=(
                "the theorem's skeleton matches no form the statement declares"
            ),
            theorem_template=text, theorem_skeleton=target,
            considered=considered, refused_forms=forms.refused,
        )

    ambiguous: tuple[str, ...] = ()
    if corpus_forms is not None:
        ambiguous = tuple(
            sorted(
                other
                for other, other_forms in corpus_forms.items()
                if other != statement_id and target in other_forms.skeletons
            )
        )
    return CorrespondenceResult(
        statement_id=statement_id, system=system, artifact=artifact,
        reference=resolved, verdict=CORRESPONDS,
        reason=f"matched the statement's {matched.route} form",
        theorem_template=text, theorem_skeleton=target,
        matched_route=matched.route, ambiguous_with=ambiguous,
        considered=considered, refused_forms=forms.refused,
    )


# --------------------------------------------------------------------------
# Corpus sweep and CLI
# --------------------------------------------------------------------------


@dataclass
class CorrespondenceReport:
    results: list[CorrespondenceResult] = field(default_factory=list)

    def count(self, verdict: str) -> int:
        return sum(1 for r in self.results if r.verdict == verdict)

    @property
    def mismatches(self) -> list[CorrespondenceResult]:
        return [r for r in self.results if r.verdict == MISMATCH]

    def as_dict(self) -> dict:
        return {
            "links": len(self.results),
            "corresponds": self.count(CORRESPONDS),
            "mismatch": self.count(MISMATCH),
            "untranslatable": self.count(UNTRANSLATABLE),
            "results": [r.as_dict() for r in self.results],
        }


def load_corpus_nodes(data_dir: Path) -> list[dict]:
    nodes: list[dict] = []
    for path in sorted(data_dir.glob("*/nodes.json")):
        corpus = json.loads(path.read_text(encoding="utf-8"))
        nodes.extend(corpus.get("statement_nodes", []))
    return nodes


def check_corpus(data_dir: Path, repo_root: Path) -> CorrespondenceReport:
    nodes = load_corpus_nodes(data_dir)
    corpus_forms = {
        node["statement_id"]: declared_forms(node)
        for node in nodes
        if node.get("statement_id")
    }
    report = CorrespondenceReport()
    for node in nodes:
        for link in node.get("verified_by", []) or []:
            if not isinstance(link, dict):
                continue
            report.results.append(
                check_link(node, link, repo_root, corpus_forms)
            )
    return report


def print_report(report: CorrespondenceReport) -> None:
    print(
        f"{len(report.results)} verified_by links: "
        f"{report.count(CORRESPONDS)} CORRESPONDS, "
        f"{report.count(MISMATCH)} MISMATCH, "
        f"{report.count(UNTRANSLATABLE)} UNTRANSLATABLE"
    )
    print()
    for result in report.results:
        print(f"  {result.verdict:15s} {result.statement_id}")
        print(f"    theorem   {result.reference}")
        if result.theorem_skeleton:
            print(f"    skeleton  {result.theorem_skeleton}")
        print(f"    route     {result.matched_route or '-'}   ({result.reason})")
        if result.ambiguous_with:
            print(
                "    AMBIGUOUS structural twins also declaring this skeleton: "
                + ", ".join(result.ambiguous_with)
            )
    print()
    if report.mismatches:
        print("MISMATCH links (a theorem that does not prove its citer):")
        for result in report.mismatches:
            print(f"  - {result.statement_id} -> {result.reference}")
    else:
        print("No MISMATCH links.")
    if report.count(UNTRANSLATABLE):
        print(
            "UNTRANSLATABLE links are reported, not failed: refusing to "
            "translate is not evidence of a wrong citation. A WRITE gate must "
            "still treat them as unproven (scripts/write_stage.py)."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="verified_by correspondence")
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT / "data")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--write-report", type=Path, default=None)
    args = parser.parse_args()

    report = check_corpus(args.data_dir, args.repo_root)
    print_report(report)
    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(
            json.dumps(report.as_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Report written to {args.write_report}")
    # MISMATCH is a failure; UNTRANSLATABLE is a limit of this rung.
    return 1 if report.mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
