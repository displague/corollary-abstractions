#!/usr/bin/env python3
"""Detect structurally isomorphic statement nodes across discipline corpora.

Parses each node's `structural_signature.anonymized_template` into an
expression tree, canonicalizes it (commutative flattening/sorting, subtraction
and division normalization), and abstracts slot names into position-indexed
placeholders to produce a *skeleton*. Nodes sharing a skeleton are structural
twins regardless of discipline or notation.

Which heads may be reordered is declared, not folklore: see `HEAD_ALGEBRA`
below. Before it, the canonicalizer knew only that `+` and `*` commute, and
the corpora compensated by fixing an argument order in their seed scripts —
so `MEET(X, TOP)` and `MEET(TOP, X)` were different skeletons, and a node
existed (`geotop.predicates.adjacency_symmetry`) purely to state a
commutativity the tooling could not represent.

Two match levels are reported:

- shape twins: identical skeletons with slot identity ignored
- typed twins: identical skeletons after annotating each slot with a coarse
  category (parameter-like vs variable-like) taken from `slot_schema`

Typed twins are strong cross-discipline analogy candidates; shape twins are
looser. The report also flags archetype-label drift (same skeleton, different
hand-assigned `archetype_id`, and vice versa) and template slots missing from
`slot_schema`.

Twin proposals are written to a report, never into the corpora: structural
isomorphism is an analogy relation, not the logical `equivalent_to` captured
by `inferential_links`.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------
# Expression trees
#
# Nodes are tuples:
#   ("num", value)                 numeric literal
#   ("slot", name)                 template slot (leaf)
#   ("call", fname, (args...))     function application, incl. E[X|Y] brackets
#   ("op", opname, (args...))      operator application
#   ("rel", relname, (lhs, rhs))   top-level relation (=, =>_d, approx, ~)
# --------------------------------------------------------------------------

RELATIONS = {"=", "=>_d", "approx", "~", "<=", ">=", "<", ">"}
SYMMETRIC_RELATIONS = {"="}
BIG_OP_PREFIXES = ("sum_", "prod_", "lim_", "max_", "min_")

# --------------------------------------------------------------------------
# Declared head algebra
#
# Until now the canonicalizer knew exactly one algebraic fact — that `+` and
# `*` are commutative — and every other head's algebra lived as folklore: in
# a seed script's fixed argument order (`scripts/seed_logic.py` always writes
# the distinguished operand first so the two `identity_laws` nodes twin), in
# a node authored solely to say out loud what the tooling cannot represent
# (`geotop.predicates.adjacency_symmetry`), or in a scope note. This table
# replaces the folklore with a declaration that the passes read.
#
# Fields:
#   kind          "op" (an arithmetic operator node) or "call" (a call head)
#   commutative   arguments may be reordered. Consumed by `canonicalize` /
#                 `typed_resort` (sort args by shape key) and by
#                 `specialize.py` (try both argument orders when matching).
#   associative   nested applications may be reparenthesized. DECLARED ONLY —
#                 no pass consumes it yet. Flattening a declared-associative
#                 call head is the separate BACKLOG item "Associativity and
#                 commutativity are one package in the canonicalizer"; the
#                 two `+`/`*` entries are the only ones the canonicalizer
#                 actually flattens, and it flattens them because they are
#                 commutative, not because of this field.
#   identity      a two-sided identity element. A float means the numeric
#                 literal; a tuple of strings means "the corpus writes this
#                 element as a constant slot under these names" (the same
#                 lattice top is `TRUTH` in data/logic and `UNIVERSE` in
#                 data/set_theory). Consumed by `specialize.py`.
#   annihilator   an absorbing element (x OP a = a). DECLARED ONLY — recorded
#                 because the corpus states it, not yet consumed by any pass.
#   provenance    ASSERTED (a node in data/ states the property), DERIVED (it
#                 follows from a property a node states), or CONVENTION (it is
#                 an authoring convention the corpus relies on silently).
#
# Deliberately ABSENT, with reasons:
#   `^`   The Wikisem lane (docs/BACKLOG.md, "Real-data lanes") asks for `^`
#         to be commutative because there `^` is logical conjunction. In THIS
#         grammar `^` is exponentiation (`Parser.parse_power`), and
#         `SIDE1^2` is not `2^SIDE1`. The Wikisem request needs a lane-local
#         algebra table, not an entry here.
#   CONCAT commutative — false of words: `re-do` is not `do-re`
#         (morphology.wordformation.affixation's own scope note).
#   CROSS, OUTER, MATRIXPOWER — anti-commutative / non-commutative; the table
#         has no vocabulary for antisymmetry and inventing one for a single
#         node would be declaring more than the corpus justifies.
HEAD_ALGEBRA: dict[str, dict] = {
    # ---- arithmetic operators (formerly the hardcoded COMMUTATIVE set) ----
    "+": {
        "kind": "op", "commutative": True, "associative": True,
        "identity": 0.0, "provenance": "CONVENTION",
        # Ordinary real addition; assumed by every numeric corpus. The
        # identity is the one `specialize.py` already used to cover
        # geometry.circle_formulas.circle_circumference_formula from the
        # affine family (SHIFT -> 0).
    },
    "*": {
        "kind": "op", "commutative": True, "associative": True,
        "identity": 1.0, "provenance": "CONVENTION",
        # Scalar multiplication. Known over-declaration: `*` is also the only
        # spelling available for non-commutative products, which is why
        # ml.recurrence.mlstm_matrix_memory_update had to introduce an
        # `OUTER(.,.)` head and geomodel.surfaces.surface_normal_cross_product
        # a `CROSS(.,.)` head rather than write them with `*`.
    },
    # ---- lattice heads ----
    "MEET": {
        "kind": "call", "commutative": True, "associative": True,
        "identity": ("TRUTH", "UNIVERSE"),
        "annihilator": ("FALSITY", "EMPTYSET", "INCONSISTENCY"),
        "provenance": "ASSERTED",
        # Commutativity: DERIVED, but from a statement rather than from
        # folklore — logic.boolean_laws.identity_laws states in its invariants
        # "TOP is a two-sided identity for MEET", and settheory.order.
        # empty_set_minimality states "equivalent to the domination law
        # MEET(BOT, x) = BOT" with the constant on the LEFT while
        # geotop.predicates.de9im_disjoint writes MEET(REGA, REGB) and
        # logic.boolean_laws.identity_laws writes MEET(PROP1, TRUTH) with it
        # on the right. Two-sidedness is asserted; argument order across the
        # corpora is already inconsistent, which is the case for declaring it.
        # Identity: logic.boolean_laws.identity_laws (`MEET(PROP1, TRUTH)`,
        # TRUTH a `constant` slot) and settheory.boolean_laws.identity_laws
        # (`MEET(SETA, UNIVERSE)`).
        # Annihilator: the same two nodes carry it in `equivalent_forms` —
        # "P and false = false" / "A inter 0 = 0", scope-noted "the companion
        # domination laws". INCONSISTENCY is narrative.frame.frame_consistency's
        # spelling of BOT.
    },
    "JOIN": {
        "kind": "call", "commutative": True, "associative": True,
        "identity": ("FALSITY", "EMPTYSET", "INCONSISTENCY"),
        "annihilator": ("TRUTH", "UNIVERSE"),
        "provenance": "ASSERTED",
        # Identity: logic.boolean_laws.identity_laws equivalent form
        # "P or false = P", scope-noted "Falsity is the identity for
        # disjunction"; settheory.boolean_laws.identity_laws equivalent form
        # "A union emptyset = A". Its invariants say "dually BOT is one for
        # JOIN". Annihilator: same nodes, "P or true = true" / "A union U = U".
        # Commutativity: same argument as MEET; additionally
        # geotop.point_set.interior_boundary_exterior_partition writes a
        # nested JOIN whose three operands are a partition, which is
        # order-independent.
    },
    # ---- geospatial predicate ----
    "TOUCHES": {
        "kind": "call", "commutative": True, "provenance": "ASSERTED",
        # geotop.predicates.adjacency_symmetry exists for no other reason:
        # `IMPLIES(TOUCHES(REGA, REGB), TOUCHES(REGB, REGA))`, whose own
        # invariant says "Recording symmetry this way is the corpus's only
        # current means of saying that a head is commutative". It is the one
        # node in data/ that ASSERTS a call head's commutativity rather than
        # assuming it. No identity element: adjacency has none.
    },
    # ---- morphological concatenation ----
    "CONCAT": {
        "kind": "call", "commutative": False, "associative": True,
        "identity": ("EMPTY",), "provenance": "ASSERTED",
        # Associativity: morphology.wordformation.concat_associativity states
        # `CONCAT(CONCAT(A,B),C) = CONCAT(A,CONCAT(B,C))` outright.
        # Identity: morphology.wordformation.zero_morpheme_identity states
        # `CONCAT(STEM, EMPTY) = STEM`, with an equivalent form
        # "concat(empty, s) = s = concat(s, empty)" making it two-sided, and
        # EMPTY declared `constant` in its slot_schema exactly as TRUTH and
        # UNIVERSE are. NOT commutative -- the same corpus notes `re-do` is
        # not `do-re`, which is why it needs its own entry rather than
        # joining MEET.
    },
    # ---- binary minimum ----
    "MINOF": {
        "kind": "call", "commutative": True, "associative": True,
        "provenance": "DERIVED",
        # ml.policy.ppo_clipped_surrogate is the only carrier;
        # docs/BACKLOG.md records "MINOF is commutative in every model and the
        # matcher cannot know it". Binary min on a totally ordered codomain is
        # symmetric. Declared for completeness; the node is a singleton, so
        # nothing in the current graph turns on it.
    },
}

# Operator heads the canonicalizer flattens AND sorts. `specialize.py` imports
# this name and treats it as "arithmetic commutative op with an identity that
# an argument may vanish into", so only `op`-kind entries belong here.
COMMUTATIVE = {
    name for name, alg in HEAD_ALGEBRA.items()
    if alg["kind"] == "op" and alg.get("commutative")
}

# Call heads whose arguments may be reordered. Sorted, never flattened: a
# nested `JOIN(a, JOIN(b, c))` keeps its nesting, because associativity is a
# separate declaration that no pass consumes yet.
COMMUTATIVE_CALL_HEADS = {
    name for name, alg in HEAD_ALGEBRA.items()
    if alg["kind"] == "call" and alg.get("commutative")
}


def identity_terms(head: str) -> tuple[tuple, ...]:
    """Expression-tree spellings of `head`'s declared identity element.

    A float identity yields the numeric literal; a tuple of names yields one
    `("slot", name)` per spelling the corpora use for that element, so a
    pattern slot can bind `TRUTH` under MEET in data/logic and `UNIVERSE`
    under MEET in data/set_theory without either corpus being privileged.
    Returns `()` for heads with no declared identity.
    """
    ident = HEAD_ALGEBRA.get(head, {}).get("identity")
    if ident is None:
        return ()
    if isinstance(ident, (int, float)):
        return (("num", float(ident)),)
    return tuple(("slot", name) for name in ident)

TOKEN_RE = re.compile(
    r"\s*(=>_d|<=|>=|[A-Za-z][A-Za-z0-9_]*|\d+(?:\.\d+)?|[=+\-*/^()\[\],|]|±)"
)


class TemplateParseError(ValueError):
    pass


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    pos = 0
    while pos < len(text):
        m = TOKEN_RE.match(text, pos)
        if not m:
            raise TemplateParseError(f"unexpected character at {text[pos:pos+10]!r}")
        tokens.append(m.group(1))
        pos = m.end()
    return tokens


class Parser:
    """Pratt-style parser for anonymized templates."""

    def __init__(self, tokens: list[str]):
        self.tokens = tokens
        self.i = 0

    def peek(self) -> str | None:
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def next(self) -> str:
        tok = self.peek()
        if tok is None:
            raise TemplateParseError("unexpected end of template")
        self.i += 1
        return tok

    def parse(self) -> tuple:
        expr = self.parse_relation()
        if self.peek() is not None:
            raise TemplateParseError(f"trailing tokens at {self.peek()!r}")
        return expr

    def parse_relation(self) -> tuple:
        lhs = self.parse_sum()
        tok = self.peek()
        if tok in RELATIONS or tok == "approx":
            self.next()
            rhs = self.parse_sum()
            return ("rel", tok, (lhs, rhs))
        return lhs

    def parse_sum(self) -> tuple:
        node = self.parse_product()
        while self.peek() in {"+", "-", "±"}:
            op = self.next()
            rhs = self.parse_product()
            if op == "-":
                rhs = ("op", "neg", (rhs,))
                op = "+"
            elif op == "±":
                rhs = ("op", "pm", (rhs,))
                op = "+"
            node = ("op", "+", (node, rhs))
        return node

    def parse_product(self) -> tuple:
        node = self.parse_power()
        while self.peek() in {"*", "/"}:
            op = self.next()
            rhs = self.parse_power()
            if op == "/":
                rhs = ("op", "inv", (rhs,))
            node = ("op", "*", (node, rhs))
        return node

    def parse_power(self) -> tuple:
        base = self.parse_atom()
        if self.peek() == "^":
            self.next()
            exponent = self.parse_power()  # right-associative
            return ("op", "^", (base, exponent))
        return base

    def parse_atom(self) -> tuple:
        tok = self.next()
        if tok == "(":
            node = self.parse_relation()
            if self.next() != ")":
                raise TemplateParseError("expected `)`")
            return node
        if tok == "-":
            return ("op", "neg", (self.parse_atom(),))
        if re.fullmatch(r"\d+(?:\.\d+)?", tok):
            return ("num", float(tok))
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", tok):
            raise TemplateParseError(f"unexpected token {tok!r}")

        # Big operators written as `sum_i EXPR` apply to the following product.
        if tok.lower().startswith(BIG_OP_PREFIXES):
            body = self.parse_product()
            return ("call", tok.lower().split("_", 1)[0], (body,))

        if self.peek() == "(":
            self.next()
            args = self.parse_args(")")
            return ("call", tok, tuple(args))
        if self.peek() == "[":
            # Functional application; `|` separates conditioned arguments.
            self.next()
            args = self.parse_args("]", allow_bar=True)
            return ("call", f"{tok}[]", tuple(args))
        return ("slot", tok)

    def parse_args(self, closing: str, allow_bar: bool = False) -> list[tuple]:
        args = [self.parse_relation()]
        while self.peek() in ({",", "|"} if allow_bar else {","}):
            self.next()
            args.append(self.parse_relation())
        if self.next() != closing:
            raise TemplateParseError(f"expected `{closing}`")
        return args


# --------------------------------------------------------------------------
# Canonicalization and skeletons
# --------------------------------------------------------------------------


def canonicalize(node: tuple) -> tuple:
    """Flatten and sort commutative operators; keep everything else ordered."""
    kind = node[0]
    if kind in {"num", "slot"}:
        return node
    if kind == "rel":
        rel, (lhs, rhs) = node[1], node[2]
        lhs, rhs = canonicalize(lhs), canonicalize(rhs)
        if rel in SYMMETRIC_RELATIONS and shape_key(lhs) > shape_key(rhs):
            lhs, rhs = rhs, lhs
        return ("rel", rel, (lhs, rhs))
    name = node[1]
    args = [canonicalize(a) for a in node[2]]
    if kind == "op" and name in COMMUTATIVE:
        flat: list[tuple] = []
        for a in args:
            if a[0] == "op" and a[1] == name:
                flat.extend(a[2])
            else:
                flat.append(a)
        flat.sort(key=shape_key)
        return ("op", name, tuple(flat))
    if kind == "call" and name in COMMUTATIVE_CALL_HEADS and len(args) > 1:
        # Sort only. Call heads are binary throughout data/, so ordering two
        # arguments by shape key is the whole of commutativity for them; and
        # flattening would need the separate `associative` declaration, which
        # nothing consumes (a nested `JOIN(a, JOIN(b, c))` stays nested).
        args.sort(key=shape_key)
    return (kind, name, tuple(args))


def shape_key(node: tuple) -> str:
    """Structure with slot identity erased — used for canonical ordering."""
    kind = node[0]
    if kind == "slot":
        return "?"
    if kind == "num":
        return f"#{node[1]:g}"
    head = node[1]
    return f"{kind}:{head}({','.join(shape_key(a) for a in node[2])})"


def typed_resort(node: tuple, slot_class: dict[str, str]) -> tuple:
    """Re-sort commutative args with slot categories visible, so typed
    skeletons are invariant to `P*V` vs `V*P` orderings that the
    category-blind canonical sort leaves arbitrary."""

    def typed_key(n: tuple) -> str:
        if n[0] == "slot":
            return f"?{slot_class.get(n[1], 'V')}"
        if n[0] == "num":
            return f"#{n[1]:g}"
        return f"{n[0]}:{n[1]}({','.join(typed_key(a) for a in n[2])})"

    kind = node[0]
    if kind in {"num", "slot"}:
        return node
    if kind == "rel":
        rel, (lhs, rhs) = node[1], node[2]
        lhs, rhs = typed_resort(lhs, slot_class), typed_resort(rhs, slot_class)
        if rel in SYMMETRIC_RELATIONS and typed_key(lhs) > typed_key(rhs):
            lhs, rhs = rhs, lhs
        return ("rel", rel, (lhs, rhs))
    args = [typed_resort(a, slot_class) for a in node[2]]
    if kind == "op" and node[1] in COMMUTATIVE:
        args.sort(key=typed_key)
    elif kind == "call" and node[1] in COMMUTATIVE_CALL_HEADS and len(args) > 1:
        args.sort(key=typed_key)
    return (kind, node[1], tuple(args))


def skeleton(node: tuple, slot_class: dict[str, str] | None = None) -> str:
    """Render canonicalized tree with slots as position-indexed placeholders.

    With `slot_class`, placeholders carry a coarse category (P: parameter-like,
    V: variable-like), so `CONSTANT * RADIUS` and `DIM1 * DIM2` diverge.
    """
    if slot_class is not None:
        node = typed_resort(node, slot_class)
    indices: dict[str, int] = {}

    def render(n: tuple) -> str:
        kind = n[0]
        if kind == "num":
            return f"{n[1]:g}"
        if kind == "slot":
            idx = indices.setdefault(n[1], len(indices))
            if slot_class is None:
                return f"?{idx}"
            return f"?{idx}:{slot_class.get(n[1], 'V')}"
        head = n[1]
        inner = ", ".join(render(a) for a in n[2])
        if kind == "rel":
            lhs, rhs = (render(a) for a in n[2])
            return f"{lhs} {head} {rhs}"
        if kind == "op":
            return f"{head}({inner})"
        return f"{head}⟨{inner}⟩"

    return render(node)


PARAMETER_LIKE = {"parameter", "constant"}

# Declared head-alias classes for the ALIASED match level. An alias is an
# assertion that two call heads name one operation family; entries must be
# argued, not convenient. Current classes:
# - ordered_compose: modifier application MOD(base, modifier) and
#   affixation CONCAT(stem, affix) -- the registered morphology prediction
#   that word-level and phrase-level recursion are one skeleton
#   (docs/DISCOVERIES.md); both are ordered binary composition of a head
#   with a dependent.
# - order_le: LEQ and BEFORE -- temporal precedence IS an order relation;
#   the temporal corpus already twins transitivity through the LEQ shape.
# - aggregate: `sum` (the prefix big-operator) and INTEGRAL -- both are
#   linear aggregation of a family over an index set, differing only in
#   whether that set is discrete or continuous (a Riemann sum IS the
#   integral's defining approximation, and counting measure makes the two
#   literally one operator). Registered against the pair docs/BACKLOG.md
#   nominates as the test case: difftop.vectorfields.poincare_hopf_index_theorem
#   versus diffgeo.surfaces.gauss_bonnet_theorem.
HEAD_ALIASES = {
    "MOD": "ordered_compose",
    "CONCAT": "ordered_compose",
    "BEFORE": "order_le",
    "LEQ": "order_le",
    "sum": "aggregate",
    "INTEGRAL": "aggregate",
}


def alias_heads(node: tuple) -> tuple:
    """Rewrite call heads into their declared alias classes."""
    kind = node[0]
    if kind in {"num", "slot"}:
        return node
    args = tuple(alias_heads(a) for a in node[2])
    head = node[1]
    if kind == "call" and head in HEAD_ALIASES:
        head = HEAD_ALIASES[head]
    return (kind, head, args)


def absorb_parameter_signs(node: tuple, slot_class: dict[str, str]) -> tuple:
    """Drop negations whose sign can be absorbed into a free parameter.

    `EXP(RATE*TIME)` (growth) and `EXP(-(RATECONST*TIME))` (decay) are the
    same one-parameter family under the reparameterization RATE = -RATECONST;
    the minus sign is a discipline's sign convention, not structure. A `neg`
    is absorbable exactly when its operand contains a parameter-like slot at
    multiplicative position, since that free coefficient can carry the sign.

    Applied only for the `family` match level -- typed twins stay sign-exact,
    because for a *fixed-value* constant the sign is real structure.
    """

    def has_param_factor(n: tuple) -> bool:
        if n[0] == "slot":
            return slot_class.get(n[1]) == "P"
        if n[0] == "op" and n[1] in {"*", "inv"}:
            return any(has_param_factor(a) for a in n[2])
        return False

    kind = node[0]
    if kind in {"num", "slot"}:
        return node
    args = tuple(absorb_parameter_signs(a, slot_class) for a in node[2])
    if kind == "op" and node[1] == "neg" and has_param_factor(args[0]):
        return args[0]
    return (kind, node[1], args)


def slot_classes(node_json: dict) -> dict[str, str]:
    classes: dict[str, str] = {}
    for slot in node_json.get("structural_signature", {}).get("slot_schema", []):
        category = slot.get("syntactic_category", "")
        classes[slot.get("slot_id", "")] = "P" if category in PARAMETER_LIKE else "V"
    return classes


def template_slots(tree: tuple) -> set[str]:
    if tree[0] == "slot":
        return {tree[1]}
    if tree[0] in {"num"}:
        return set()
    return set().union(*(template_slots(a) for a in tree[2])) if tree[2] else set()


# --------------------------------------------------------------------------
# Corpus loading and reporting
# --------------------------------------------------------------------------


@dataclass
class ParsedNode:
    statement_id: str
    discipline: str
    archetype: str
    template: str
    shape: str
    typed: str
    family: str
    aliased: str
    missing_slots: list[str]


def load_nodes(data_dir: Path) -> tuple[list[ParsedNode], list[str]]:
    parsed: list[ParsedNode] = []
    problems: list[str] = []
    for corpus_path in sorted(data_dir.glob("*/nodes.json")):
        corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
        discipline = corpus.get("discipline", corpus_path.parent.name)
        for node in corpus.get("statement_nodes", []):
            sid = node.get("statement_id", "<missing-id>")
            signature = node.get("structural_signature", {})
            template = signature.get("anonymized_template", "")
            if not template:
                problems.append(f"{sid}: no anonymized_template")
                continue
            try:
                tree = canonicalize(Parser(tokenize(template)).parse())
            except TemplateParseError as exc:
                problems.append(f"{sid}: cannot parse template `{template}`: {exc}")
                continue
            classes = slot_classes(node)
            missing = sorted(template_slots(tree) - set(classes))
            parsed.append(
                ParsedNode(
                    statement_id=sid,
                    discipline=discipline,
                    archetype=signature.get("archetype_id", "<none>"),
                    template=template,
                    shape=skeleton(tree),
                    typed=skeleton(tree, classes),
                    family=skeleton(
                        canonicalize(absorb_parameter_signs(tree, classes)), classes),
                    aliased=skeleton(canonicalize(alias_heads(tree)), classes),
                    missing_slots=missing,
                )
            )
    return parsed, problems


def group_by(nodes: list[ParsedNode], key: str) -> dict[str, list[ParsedNode]]:
    groups: dict[str, list[ParsedNode]] = defaultdict(list)
    for n in nodes:
        groups[getattr(n, key)].append(n)
    return groups


def build_report(nodes: list[ParsedNode], problems: list[str]) -> dict:
    shape_groups = group_by(nodes, "shape")
    typed_groups = group_by(nodes, "typed")
    family_groups = group_by(nodes, "family")
    aliased_groups = group_by(nodes, "aliased")

    def group_entries(groups: dict[str, list[ParsedNode]]) -> list[dict]:
        entries = []
        for skel, members in sorted(groups.items()):
            if len(members) < 2:
                continue
            entries.append(
                {
                    "skeleton": skel,
                    "disciplines": sorted({m.discipline for m in members}),
                    "archetypes": sorted({m.archetype for m in members}),
                    "members": [
                        {
                            "statement_id": m.statement_id,
                            "discipline": m.discipline,
                            "template": m.template,
                        }
                        for m in members
                    ],
                }
            )
        return entries

    archetype_groups = group_by(nodes, "archetype")
    label_drift = [
        {
            "archetype_id": arch,
            "distinct_shapes": sorted({m.shape for m in members}),
            "members": [m.statement_id for m in members],
        }
        for arch, members in sorted(archetype_groups.items())
        if len({m.shape for m in members}) > 1
    ]
    split_labels = [
        {
            "skeleton": skel,
            "archetype_ids": sorted({m.archetype for m in members}),
            "members": [m.statement_id for m in members],
        }
        for skel, members in sorted(shape_groups.items())
        if len(members) > 1 and len({m.archetype for m in members}) > 1
    ]
    slot_gaps = [
        {"statement_id": n.statement_id, "missing_from_slot_schema": n.missing_slots}
        for n in nodes
        if n.missing_slots
    ]

    # Family twins subsume typed twins by construction (sign absorption only
    # merges groups); report only groups that grew beyond every typed group,
    # since the rest would repeat the typed section verbatim.
    typed_member_sets = {
        frozenset(m.statement_id for m in members)
        for members in typed_groups.values()
    }
    family_new = {
        skel: members
        for skel, members in family_groups.items()
        if len(members) > 1
        and frozenset(m.statement_id for m in members) not in typed_member_sets
    }

    aliased_new = {
        skel: members
        for skel, members in aliased_groups.items()
        if len(members) > 1
        and frozenset(m.statement_id for m in members) not in typed_member_sets
    }

    return {
        "nodes_analyzed": len(nodes),
        "typed_twin_groups": group_entries(typed_groups),
        "family_twin_groups_beyond_typed": group_entries(family_new),
        "aliased_twin_groups_beyond_typed": group_entries(aliased_new),
        "shape_twin_groups": group_entries(shape_groups),
        "archetype_label_drift": label_drift,
        "skeletons_with_split_archetypes": split_labels,
        "slot_schema_gaps": slot_gaps,
        "parse_problems": problems,
    }


def print_report(report: dict) -> None:
    print(f"Analyzed {report['nodes_analyzed']} statement nodes.\n")

    def show_groups(title: str, entries: list[dict]) -> None:
        print(f"## {title} ({len(entries)} groups)")
        for e in entries:
            cross = " [CROSS-DISCIPLINE]" if len(e["disciplines"]) > 1 else ""
            print(f"\n  skeleton: {e['skeleton']}{cross}")
            for m in e["members"]:
                print(f"    - {m['statement_id']:55s} ({m['discipline']}) {m['template']}")
        print()

    show_groups("Typed structural twins", report["typed_twin_groups"])
    show_groups("Family twins (parameter signs absorbed, beyond typed)",
                report["family_twin_groups_beyond_typed"])
    show_groups("Aliased twins (declared head classes, beyond typed)",
                report["aliased_twin_groups_beyond_typed"])
    show_groups("Shape twins (slot categories ignored)", report["shape_twin_groups"])

    if report["archetype_label_drift"]:
        print("## Archetype ids spanning multiple structures")
        for d in report["archetype_label_drift"]:
            print(f"  - {d['archetype_id']}: {', '.join(d['members'])}")
        print()
    if report["skeletons_with_split_archetypes"]:
        print("## Identical structures with different archetype ids")
        for d in report["skeletons_with_split_archetypes"]:
            print(f"  - {d['skeleton']}")
            print(f"    labels: {', '.join(d['archetype_ids'])}")
        print()
    if report["slot_schema_gaps"]:
        print("## Template slots missing from slot_schema")
        for g in report["slot_schema_gaps"]:
            print(f"  - {g['statement_id']}: {', '.join(g['missing_from_slot_schema'])}")
        print()
    if report["parse_problems"]:
        print("## Templates that could not be analyzed")
        for p in report["parse_problems"]:
            print(f"  - {p}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument(
        "--write-report",
        type=Path,
        default=None,
        help="Also write the full report as JSON to this path.",
    )
    args = parser.parse_args()

    nodes, problems = load_nodes(args.data_dir)
    report = build_report(nodes, problems)
    print_report(report)

    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        print(f"Report written to {args.write_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
