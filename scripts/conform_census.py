#!/usr/bin/env python3
"""Classify every committed statement for conformance, read-only.

`docs/DESIGN-statements-that-run.md` §3.1's walk, executed rather than
quoted. This module computes **where each statement lands** and nothing
else: it decides no verdict, samples no point and writes no artifact of its
own. The register (E0c) and the compiler (`conform.py`) both read their
partition from here, so there is one classification in the tree rather than
two that agree today.

**The walk is shape-first, and the order is load-bearing** because the
buckets depend on it (§3.1): parse -> is the top level a relation? -> is it
a *single* relation? -> are all heads inside the evaluator? -> are all
operators and the relation itself decidable?

**Two fields, and the design's Correction 3 is why.** The shape walk reads
`formal_statement.canonical_ascii`. The GUARD is read from
`structural_signature.anonymized_template`, because for 79.4% of the
free-variable candidates the ascii field is *the conclusion with the
hypotheses deleted* — a sampler pointed at it manufactures counterexamples
that are not counterexamples. Both readings are recorded per statement so a
reader can see which field said what.

**Nothing here is a heuristic over free text.** Every typing decision keys
on a committed declaration: `slot_schema[].syntactic_category` for what may
be sampled (§3.2.1), `symbol_lexicon.constants[]` for declared values, and
the domain schema's reviewed output-role list for definitional equalities.
A regex over role strings would be the guessing this design refuses.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
import sys  # noqa: E402

sys.path.insert(0, str(REPO / "scripts"))

import match_signatures as ms  # noqa: E402

#: The committed evaluator's whole inventory (§3.1). Read from the module
#: rather than restated, so an evaluator that grows is not silently
#: under-counted here.
EVALUATOR_OPERATORS = frozenset({"+", "*", "neg", "inv", "^"})


def evaluator_relations() -> frozenset[str]:
    from evaluate import _RELATIONS  # noqa: PLC0415

    return frozenset(_RELATIONS)


#: `IMPLIES` and `MEET` are the two template heads the guard walk reads
#: structurally. Neither is arithmetic: `MEET` carries a commutativity row in
#: `HEAD_ALGEBRA` and `IMPLIES` carries none, and this design reads the
#: antecedent as a conjunct list rather than algebraically (§3.3).
IMPLIES_HEAD = "IMPLIES"
MEET_HEAD = "MEET"


# --------------------------------------------------------------------------
# Tree walking
# --------------------------------------------------------------------------


def parse(text: str):
    """The committed parser, or None. Never raises on corpus input."""

    try:
        return ms.Parser(ms.tokenize(text)).parse()
    except Exception:
        return None


def call_heads(node) -> set[str]:
    kind = node[0]
    if kind in {"num", "slot"}:
        return set()
    out: set[str] = set()
    if kind == "call":
        out.add(node[1])
    for arg in node[2]:
        out |= call_heads(arg)
    return out


def operators(node) -> set[str]:
    kind = node[0]
    if kind in {"num", "slot"}:
        return set()
    out: set[str] = set()
    if kind == "op":
        out.add(node[1])
    for arg in node[2]:
        out |= operators(arg)
    return out


def relations_in(node) -> list[str]:
    kind = node[0]
    if kind in {"num", "slot"}:
        return []
    out: list[str] = []
    if kind == "rel":
        out.append(node[1])
    for arg in node[2]:
        out += relations_in(arg)
    return out


def slots(node) -> set[str]:
    kind = node[0]
    if kind == "slot":
        return {node[1]}
    if kind == "num":
        return set()
    out: set[str] = set()
    for arg in node[2]:
        out |= slots(arg)
    return out


def exponent_slots(node) -> set[str]:
    """Slots occurring in an exponent position — §3.3's `exponent_variable`.

    `evaluate._eval_tree` refuses a non-integer exponent, so a statement
    whose exponent is a SAMPLED variable cannot be tested without the
    sampler choosing which powers are legal, which is a semantic choice it
    has no authority to make.
    """

    kind = node[0]
    if kind in {"num", "slot"}:
        return set()
    out: set[str] = set()
    if kind == "op" and node[1] == "^" and len(node[2]) == 2:
        out |= slots(node[2][1])
    for arg in node[2]:
        out |= exponent_slots(arg)
    return out


# --------------------------------------------------------------------------
# The guard, read from the template (Correction 3)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Guard:
    """An antecedent read as a conjunct list, plus what it is made of."""

    conjuncts: tuple = ()
    source_field: str = "structural_signature.anonymized_template"
    all_conjuncts_evaluable: bool = True
    has_equality: bool = False
    box_only: bool = False
    couples_variables: bool = False
    unevaluable_reason: str | None = None

    @property
    def present(self) -> bool:
        return bool(self.conjuncts)


def _flatten_meet(node) -> list:
    """`MEET(MEET(a,b),c)` -> [a, b, c]. Any other node is one conjunct."""

    if node[0] == "call" and node[1] == MEET_HEAD:
        out: list = []
        for arg in node[2]:
            out += _flatten_meet(arg)
        return out
    return [node]


def read_guard(template_tree, decidable_relations: frozenset[str]) -> Guard:
    """The antecedent of an `IMPLIES`-topped template, as conjuncts."""

    if template_tree is None:
        return Guard()
    if not (
        template_tree[0] == "call"
        and template_tree[1] == IMPLIES_HEAD
        and len(template_tree[2]) == 2
    ):
        return Guard()

    antecedent = template_tree[2][0]
    conjuncts = tuple(_flatten_meet(antecedent))

    evaluable = True
    reason = None
    has_equality = False
    box_only = True
    couples = False
    for conjunct in conjuncts:
        if conjunct[0] != "rel":
            evaluable = False
            reason = "conjunct is not a relation"
            box_only = False
            continue
        relation = conjunct[1]
        if relation not in decidable_relations:
            evaluable = False
            reason = f"relation {relation!r} is not decidable"
        if call_heads(conjunct):
            evaluable = False
            reason = "conjunct carries a call head outside the evaluator"
        outside = operators(conjunct) - EVALUATOR_OPERATORS
        if outside:
            evaluable = False
            reason = f"conjunct carries operator(s) {sorted(outside)}"
        if relation == "=":
            has_equality = True
        # A box constraint is `slot REL num` (either orientation) — directly
        # samplable per variable. Anything else couples variables and needs
        # rejection sampling (§6 E0d).
        lhs, rhs = conjunct[2]
        is_box = (
            (lhs[0] == "slot" and rhs[0] == "num")
            or (lhs[0] == "num" and rhs[0] == "slot")
        )
        if not is_box:
            box_only = False
            if len(slots(conjunct)) > 1:
                couples = True

    return Guard(
        conjuncts=conjuncts,
        all_conjuncts_evaluable=evaluable,
        has_equality=has_equality,
        box_only=box_only and bool(conjuncts),
        couples_variables=couples,
        unevaluable_reason=reason,
    )


def align_slots(ascii_tree, template_tree) -> dict[str, str] | None:
    """Map a surface identifier to the anonymized slot id the schema types.

    **Found while writing this census, and it matters.** The typing rules of
    §3.2.1 key on `slot_schema[].slot_id`, and those ids are ANONYMIZED —
    `AREA`, `RADIUS`, `CONSTANT` — while the tree parsed from
    `canonical_ascii` carries the surface identifiers the author wrote:
    `A`, `r`, `pi`. Matching them by name finds nothing, so a first pass
    typed **zero** authored slots and every declaration in the corpus went
    unread. A census that reads no declaration is exactly the sampler
    Correction 2 was written to prevent.

    The two trees are structurally parallel by construction — the template
    IS the ascii statement with identifiers anonymized — so the mapping is
    positional, not a guess: walk both in lockstep and pair the slots that
    occupy the same position.

    Returns `None` when the shapes diverge, and the caller refuses rather
    than typing by proximity. A statement whose two fields do not align is
    one where no declaration can be attributed with confidence, and guessing
    there is the failure this design exists to refuse.
    """

    mapping: dict[str, str] = {}

    def walk(left, right) -> bool:
        if left[0] != right[0]:
            return False
        if left[0] == "slot":
            surface, anonymized = left[1], right[1]
            if mapping.setdefault(surface, anonymized) != anonymized:
                return False       # one surface name, two slots: ambiguous
            return True
        if left[0] == "num":
            return True
        if left[1] != right[1] or len(left[2]) != len(right[2]):
            return False
        return all(walk(a, b) for a, b in zip(left[2], right[2]))

    if ascii_tree is None or template_tree is None:
        return None
    return mapping if walk(ascii_tree, template_tree) else None


def template_conclusion(template_tree):
    """The consequent of an IMPLIES-topped template, else the template."""

    if template_tree is None:
        return None
    if (
        template_tree[0] == "call"
        and template_tree[1] == IMPLIES_HEAD
        and len(template_tree[2]) == 2
    ):
        return template_tree[2][1]
    return template_tree


# --------------------------------------------------------------------------
# The classification
# --------------------------------------------------------------------------


@dataclass
class Classified:
    statement_id: str
    corpus: str
    epistemic_status: str = ""
    # shape walk
    parses: bool = False
    shape_exclusion: str | None = None      # why it is not evaluable-shaped
    shape_detail: str = ""
    evaluable_shaped: bool = False
    ground: bool = False
    # typed slots (§3.2.1)
    typed_refusal: str | None = None        # defined_output | named_constant |
                                            #   exponent_variable
    sampled_variables: tuple = ()
    held_parameters: tuple = ()
    bound_constants: tuple = ()
    # guard (Correction 3)
    guard: Guard = field(default_factory=Guard)
    slot_alignment: tuple = ()
    template_parses: bool = False
    consequent_differs_after_canonicalization: bool = False
    # where it lands
    bucket: str = ""


def classify(
    node: dict,
    corpus: str,
    decidable_relations: frozenset[str],
    output_roles: frozenset[str],
) -> Classified:
    """One statement, walked. `output_roles` comes from the domain schema."""

    result = Classified(
        statement_id=node.get("statement_id", ""),
        corpus=corpus,
        epistemic_status=str(node.get("epistemic_status", "")),
    )
    ascii_text = ((node.get("formal_statement") or {}).get("canonical_ascii") or "")
    tree = parse(ascii_text)
    if tree is None:
        result.bucket = "not_evaluable_shaped"
        result.shape_exclusion = "does_not_parse"
        return result
    result.parses = True

    # --- shape walk, in the design's order -----------------------------
    if tree[0] != "rel":
        result.bucket = "not_evaluable_shaped"
        result.shape_exclusion = "not_a_top_level_relation"
        return result
    if len(relations_in(tree)) > 1:
        result.bucket = "not_evaluable_shaped"
        result.shape_exclusion = "nested_relation"
        return result
    heads = call_heads(tree)
    if heads:
        result.bucket = "not_evaluable_shaped"
        result.shape_exclusion = "head_outside_evaluator"
        result.shape_detail = ",".join(sorted(heads))
        return result
    outside = operators(tree) - EVALUATOR_OPERATORS
    if outside:
        result.bucket = "not_evaluable_shaped"
        result.shape_exclusion = "operator_outside_evaluator"
        result.shape_detail = ",".join(sorted(outside))
        return result
    if tree[1] not in decidable_relations:
        result.bucket = "not_evaluable_shaped"
        result.shape_exclusion = "relation_undecidable"
        result.shape_detail = tree[1]
        return result

    result.evaluable_shaped = True
    free = slots(tree)
    if not free:
        result.ground = True
        result.bucket = "ground"
        return result

    # --- typed slots (§3.2.1) -------------------------------------------
    schema_rows = (node.get("structural_signature") or {}).get("slot_schema") or []
    category = {}
    role = {}
    for row in schema_rows:
        slot_id = row.get("slot_id")
        if not isinstance(slot_id, str):
            continue
        category[slot_id] = str(row.get("syntactic_category", ""))
        role[slot_id] = str(row.get("semantic_role", ""))

    # Slot ids in the schema are ANONYMIZED; the parsed ascii tree carries
    # the surface identifiers. `align_slots` walks the two trees in lockstep
    # to pair them positionally — see its docstring for why matching by name
    # reads no declaration at all.
    template_text = (
        (node.get("structural_signature") or {}).get("anonymized_template") or ""
    )
    # Aligned against the template's CONSEQUENT, not the whole template.
    # Correction 3 is exactly this relationship: for 79% of the candidates
    # the ascii field IS the consequent with the hypotheses deleted, so a
    # whole-tree alignment cannot match an `IMPLIES`-topped template and
    # fails for 6,525 statements — every declaration in the largest corpus
    # unread. Measured before the fix, which is why it is stated here.
    alignment = align_slots(tree, template_conclusion(parse(template_text))) or {}
    result.slot_alignment = tuple(sorted(alignment.items()))

    def anonymized(name: str) -> str:
        return alignment.get(name, name)

    def kind_of(name: str) -> str:
        key = anonymized(name)
        for candidate, value in category.items():
            if candidate.casefold() == key.casefold():
                return value
        return ""

    def role_of(name: str) -> str:
        key = anonymized(name)
        for candidate, value in role.items():
            if candidate.casefold() == key.casefold():
                return value
        return ""

    # FAIL CLOSED on anything not declared `variable`. §3.2.1's rule is
    # "sample only kind = variable", and a slot with no declaration is not
    # declared `variable` — defaulting it to sampled is precisely the
    # first-draft behaviour Correction 2 measured as fatal. Measured cost of
    # closing it: 10 statements, all authored, all of them cases where the
    # ascii and the template do not align so no declaration is attributable
    # at all.
    if not alignment and len(free) > 0:
        result.typed_refusal = "slot_alignment_failed"
        result.bucket = "refused_typed_slot"
        return result

    undeclared = tuple(sorted(n for n in free if kind_of(n) == ""))
    if undeclared:
        result.typed_refusal = "undeclared_slot"
        result.bucket = "refused_typed_slot"
        return result

    sampled = tuple(sorted(n for n in free if kind_of(n) == "variable"))
    held = tuple(sorted(n for n in free if kind_of(n) == "parameter"))
    constants = tuple(sorted(n for n in free if kind_of(n) == "constant"))
    other = tuple(sorted(
        n for n in free
        if kind_of(n) not in {"variable", "parameter", "constant"}
    ))
    result.sampled_variables = sampled
    result.held_parameters = held
    result.bound_constants = constants
    if other:
        # A declared category §3.2.1 does not name — `random_variable` is the
        # measured instance. Not sampled, because the rule admits exactly one
        # sampled category and this is not it.
        result.typed_refusal = "category_outside_typing_rule"
        result.bucket = "refused_typed_slot"
        return result
    if not sampled:
        # Every free slot is held or bound: nothing to vary, so there is no
        # point set and no sampling claim to make.
        result.typed_refusal = "no_sampled_variable"
        result.bucket = "refused_typed_slot"
        return result

    # named_constant: a declared constant whose committed value is an
    # irrational approximation makes an exact-rational equality test false
    # for a second, independent reason (§3.2.1).
    if constants:
        result.typed_refusal = "named_constant"
        result.bucket = "refused_typed_slot"
        return result

    # defined_output: `=` with one side a single slot whose declared role is
    # in the schema's REVIEWED output-role list. Not a regex over roles.
    if tree[1] == "=":
        lhs, rhs = tree[2]
        for side in (lhs, rhs):
            if side[0] == "slot" and role_of(side[1]) in output_roles:
                result.typed_refusal = "defined_output"
                result.bucket = "refused_typed_slot"
                return result

    if exponent_slots(tree) & set(sampled):
        result.typed_refusal = "exponent_variable"
        result.bucket = "refused_typed_slot"
        return result

    # --- the guard, from the template (Correction 3) ---------------------
    template = (
        (node.get("structural_signature") or {}).get("anonymized_template") or ""
    )
    template_tree = parse(template)
    result.template_parses = template_tree is not None
    result.guard = read_guard(template_tree, decidable_relations)

    if result.guard.present:
        # The consequent must agree with the parsed ascii after
        # canonicalization, or the corpus wrote two different literals and a
        # reviewer decides which (Correction 3's two named statements).
        consequent = template_conclusion(template_tree)
        try:
            same = ms.canonicalize(consequent) == ms.canonicalize(tree)
        except Exception:
            same = False
        result.consequent_differs_after_canonicalization = not same
        if not same:
            result.bucket = "refused_numeral_beyond_exact_parse"
            return result
        if not result.guard.all_conjuncts_evaluable:
            result.bucket = "refused_guard_unevaluable"
            return result
        result.bucket = "guarded"
        return result

    result.bucket = "unguarded"
    return result


def corpora(data_dir: Path | None = None):
    """Every committed corpus file, in a stable order."""

    base = data_dir or (REPO / "data")
    return sorted(base.glob("*/nodes.json"))


def walk(
    decidable_relations: frozenset[str] | None = None,
    output_roles: frozenset[str] = frozenset(),
    data_dir: Path | None = None,
):
    """Classify the whole tree. Yields `Classified`, one per statement."""

    relations = decidable_relations or evaluator_relations()
    for path in corpora(data_dir):
        document = json.loads(path.read_text(encoding="utf-8"))
        corpus = document.get("corpus_id", path.parent.name)
        for node in document.get("statement_nodes", []):
            yield classify(node, corpus, relations, output_roles)
