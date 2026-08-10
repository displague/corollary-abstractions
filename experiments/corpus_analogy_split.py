#!/usr/bin/env python3
"""Corpus-grounded analogy, v0.7: a real split with pointable compound leaves.

WHY THIS EXISTS
---------------
`experiments/corpus_analogy.py` (v0.6) is kept as the superseded record. Its
lane admitted only bindings that were pure slot renames plus numeric
substitutions, which produced 40 rows carrying **five** distinct targets in
**one** ratio family, and a capability-blind rule -- "take the one number newly
visible in B and overwrite C's last slot" -- scored **1.000**. v0.7 item 5
replaces it. Every roadmap bullet is a hard admission rule here:

1. *Pointable source leaves, never invented vocabulary.* Compound expansions
   are admitted, but only if EVERY token of the target D already occurs in the
   input `A <sep> B <sep> C`. That single gate is what excludes the two ways
   the specializer can conjure vocabulary out of a table rather than read it
   off a statement: an arithmetic identity binding (`CONSTANT -> 1` when no
   `1` is written anywhere) and a head-identity collapse (`PROP2 -> FALSITY`,
   where the collapse means B does not contain the element at all).
2. *At least three non-isomorphic structural families before a family split is
   named.* Family = the matcher's own typed skeleton of A, so "non-isomorphic"
   is the skeleton quotient's verdict, not ours.
3. *Separate family, discipline, and literal-vocabulary holdouts*, in three
   files, with the leakage surface of each documented and cross-checked to be
   still fully available in the other two.
4. *Deduplicate targets before counting examples.* The headline N is the count
   of DISTINCT rendered targets; the pre-dedup row count is reported beside it
   so that inflation stays visible.
5. *Capability-blind controls before any training.* No model is trained here;
   the split and the ceiling table ARE this slice.
6. *Verify every D through the matcher/specializer, and keep it out of the
   input.* C >= D is re-derived by `specialize.Search` under the same
   acceptability bar edge reporting uses, and D's token sequence must not occur
   as a contiguous slice of the input.

HOW D IS BUILT
--------------
A is a general statement; B is the specific statement the committed
specialization ledger says A covers, with binding sigma: A-slot -> B-subtree.
C is a typed twin of A in a different discipline, with alignment
rho: A-slot -> C-slot. Write tau for the partial inverse of sigma restricted to
its bare-slot bindings (B-slot -> A-slot).

    D = C with each slot rho(alpha) replaced by translate(sigma(alpha))

where `translate` rewrites a B-slot leaf `s` to `rho(tau(s))` when tau knows
it, and leaves it alone otherwise. The leaves left alone are exactly the
compound-expansion leaves: they are B's own vocabulary, and the pointer
realization points at them IN B. Leaves that came through rho are C's
vocabulary and are pointed at IN C. Nothing else may appear.

Equivalently D = translate(B); the builder asserts both constructions agree,
which is a real check rather than a restatement, because the two disagree the
moment a head-identity collapse removed a node from B (those rows are refused
by the pointability gate for an independent reason).

REGISTERED PREDICTIONS (written and committed BEFORE the controls were run)
--------------------------------------------------------------------------
P-CS1  The v0.6 killer, `last_slot_number_transfer`, scores <= 0.05 exact on
       EVERY holdout of this split. Rationale: it can only fire when B
       introduces exactly one new number and the target differs from C in
       exactly that one last position; compound expansions break both clauses.
       If it scores above 0.05 anywhere, this split has reproduced v0.6's
       failure and must be reported as such rather than patched.

P-CS2  The symbolic ceiling is 1.000, and it is 1.000 from the INPUT ALONE --
       no corpus metadata needed. The task is closed-form solvable: parse
       A, B, C; run the specializer A >= B; run the twin alignment A ~ C;
       substitute. Per the v0.4 creation thesis this is the honest reading of
       the lane -- it measures the POINTING MECHANISM (can a model realize a
       target every atom of which is present but whose arrangement is not),
       not a residual that only weights could supply. Stated up front so that
       no later result can be sold as reasoning.

P-CS3  `nearest_template_transfer` -- copy the pointer-action pattern of the
       nearest training input and replay it -- is the strongest capability-
       blind control, and the family most vulnerable to it is the largest one,
       the ratio skeleton `?0:V = *(?1:V, inv(?2:V))`: it has the most rows,
       the shortest targets, and therefore the most near-duplicate inputs for
       edit distance to land on.

P-CS4  The family holdout has the LOWEST blind ceiling of the three, because
       it is the only split that removes the target's skeleton from training;
       the literal-vocabulary holdout has the highest, because the action
       pattern that produces a target is independent of which words fill it.

P-CS5  Shuffling C's leaf tokens collapses both the input-only symbolic
       solver and the strongest blind control by at least 0.5 absolute. A
       control that survives the shuffle was not reading C.

P-CS7  Acceptance holds: the blind ceiling is strictly below 1.000 on at least
       one holdout. If it is 1.000 everywhere, this branch reports that the
       corpus cannot support a non-vacuous split and says which structure is
       missing, rather than shopping for a partition that hides it.

REGISTERED PREDICTION FOR THE v0.8 UNTYPED-SHAPE HOLDOUT (P-CS8)
----------------------------------------------------------------
Written and committed BEFORE the shape holdout's controls were run, as the
v0.8 item-2 slice that adds the split the family holdout should have been. The
family holdout's 0.400 decomposes (see `_shape_leak`) as
`51/155 x 1.000 + 104/155 x 0.106`: nearest-template replay scores 1.000 on
exactly the held rows whose UNTYPED shape is still in training, and ~0.106 on
the rest. Cutting the holdout on the untyped shape removes those leaky rows by
construction, so:

P-CS8  The untyped-shape holdout's blind ceiling is STRICTLY BELOW the family
       holdout's 0.400, and lands in or near the disclosed strict band
       ~0.10-0.14 (widened only to ~[0.08, 0.16] because the ceiling is the max
       over ALL blind controls, not nearest-template alone). Four sub-claims:
       (a) blind_ceiling(shape) < 0.400;
       (b) blind_ceiling(shape) is approximately in [0.08, 0.16];
       (c) the split removes WHOLE shapes -- its `shape_leak` reports zero
           holdout rows whose shape is in training (a structural guarantee of
           the cut, not a measured control), so its ceiling IS the unseen-shape
           regime rather than a leaky/clean mixture;
       (d) P-CS1 extends: `last_slot_number_transfer` stays <= 0.05 here too.
       A miss on (a) or (b) is recorded as MISSED with a correction appended;
       the split is NOT re-rolled against the result (that is laundering). The
       shape holdout is cut on shape, full stop, and whatever ceiling results
       is reported.

ADJUDICATION OF P-CS8 (appended after the single run; the registration above is
unchanged, and the split was not re-rolled)
------------------------------------------------------------------------------
P-CS8 FIRED on all four sub-claims. The shape holdout is 131 held rows over 267
train; its blind ceiling is 0.1069 (`nearest_template_transfer`).
  (a) CONFIRMED: 0.1069 < 0.400.
  (b) CONFIRMED: 0.1069 is inside [0.08, 0.16] and inside the disclosed strict
      ~0.10-0.14 band -- essentially equal to the family holdout's OWN
      clean-shape figure 0.106, which is the point: with the leak removed, the
      whole holdout scores what the family holdout's unseen-shape rows scored.
  (c) CONFIRMED structurally: `shape_leak` reports 0 holdout rows whose shape is
      in training and 131 with an unseen shape, so the ceiling IS the
      unseen-shape regime rather than a leaky/clean mixture.
  (d) CONFIRMED: `last_slot_number_transfer` = 0.0382 <= 0.05.
Two honest observations recorded rather than smoothed: the shape holdout's
holdout set is a structural sibling of the family holdout (target Jaccard 0.437,
and 0 of its 5 held shapes' families survive in training), which is expected --
it is the split the family holdout should have been -- and its
`symbolic_input_only` is 0.290, BELOW the 0.40-0.70 the other three sit in,
while `symbolic_typed_input` is still 1.000. The declared-classes residual (the
P-CS2 finding) is therefore WIDER on unseen shapes, not narrower: the token
stream alone gets less far when the shape is genuinely novel, and the two corpus
declarations still close the whole gap.

NOT A PREDICTION -- reported because it was already observed
-----------------------------------------------------------
The builder was run while the admission rules were still being settled, so the
construction counts below were seen before the controls existed. They are
recorded as facts, not registered as predictions, and the ledger must not read
them as a fired forecast: 914 admitted rows collapse to 398 distinct targets
(2.30x, against v0.6's 8.0x), over 11 families, 376 of them carrying at least
one compound-expansion leaf. Everything P-CS1..P-CS7 speaks about -- control
scores -- was unmeasured when they were committed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "experiments"))

from match_signatures import (  # noqa: E402
    RELATIONS,
    SYMMETRIC_RELATIONS,
    Parser,
    canonicalize,
    group_by,
    load_nodes,
    slot_classes,
    tokenize,
    typed_resort,
)
from match_signatures import identity_terms  # noqa: E402
from specialize import Search, op_count, render, spelling_ranker  # noqa: E402
from analogygen import SEP, is_leaf_token, serialize  # noqa: E402

DATA_DIR = ROOT / "data"
SPEC_REPORT = ROOT / "reports" / "specializations.json"
SPLIT_DIR = ROOT / "experiments" / "data"
SPLIT_PREFIX = "corpus_analogy_v07"
SPLIT_NAMES = ("family", "discipline", "vocabulary", "shape")

# The literal-vocabulary holdout grows from the rarest target token upward
# until it reaches this share of examples. Declared before the run; it is the
# split's only tunable and it is not tuned.
VOCAB_HOLDOUT_TARGET_SHARE = 0.20


# ---------------------------------------------------------------------------
# tree helpers
# ---------------------------------------------------------------------------

def parse_template(text: str) -> tuple:
    return canonicalize(Parser(tokenize(text)).parse())


# Every operator node `match_signatures.Parser` can build, cited by line:
# `neg` (332, 366), `pm` (335), `+` (337), `inv` (346), `*` (347), `^` (355).
# Everything else with arguments is a call head. This is a DECLARED table, not
# a spelling heuristic: the first attempt keyed on "call heads are UPPERCASE",
# and the corpus immediately falsified it with `sum`, `lim` and `AGGREGATE_n`.
# `test_corpus_analogy_split` re-derives the partition from every authored
# template, so a new operator in the grammar breaks the test rather than
# silently mis-typing a target.
OPERATOR_HEADS = frozenset({"+", "*", "^", "neg", "inv", "pm"})


def head_kind(head: str) -> str:
    """Recover a serialized node's kind from its head alone.

    The token stream written by `analogygen.serialize` keeps the head but not
    the kind, and the input-only symbolic control may not consult the corpus to
    get it back.
    """
    if head in RELATIONS:
        return "rel"
    if head in OPERATOR_HEADS:
        return "op"
    return "call"


def deserialize(tokens: list[str]) -> tuple:
    tree, pos = _deserialize(tokens, 0)
    if pos != len(tokens):
        raise ValueError("trailing tokens in serialized tree")
    return tree


def _deserialize(tokens: list[str], pos: int) -> tuple[tuple, int]:
    tok = tokens[pos]
    if tok.startswith("#"):
        return ("num", float(tok[1:])), pos + 1
    if tok.endswith("("):
        head = tok[:-1]
        args: list[tuple] = []
        pos += 1
        while tokens[pos] != ")":
            arg, pos = _deserialize(tokens, pos)
            args.append(arg)
        return (head_kind(head), head, tuple(args)), pos + 1
    return ("slot", tok), pos + 1


def tree_slots(tree: tuple) -> set[str]:
    if tree[0] == "slot":
        return {tree[1]}
    if tree[0] == "num":
        return set()
    return set().union(*(tree_slots(child) for child in tree[2])) if tree[2] else set()


def slot_order(tree: tuple) -> list[str]:
    """Distinct slot names in serialization order."""
    out: list[str] = []
    for token in serialize(tree):
        if is_leaf_token(token) and token not in out:
            out.append(token)
    return out


def rename(tree: tuple, names: dict[str, str]) -> tuple:
    if tree[0] == "slot":
        return ("slot", names.get(tree[1], tree[1]))
    if tree[0] == "num":
        return tree
    return (tree[0], tree[1], tuple(rename(child, names) for child in tree[2]))


def substitute(tree: tuple, terms: dict[str, tuple]) -> tuple:
    if tree[0] == "slot":
        return terms.get(tree[1], tree)
    if tree[0] == "num":
        return tree
    return (tree[0], tree[1], tuple(substitute(child, terms) for child in tree[2]))


def align_twin_slots(a: tuple, c: tuple, a_classes: dict[str, str],
                     c_classes: dict[str, str]) -> dict[str, str] | None:
    """Slot bijection witnessing that A and C are the SAME typed skeleton.

    Ported unchanged from the v0.6 lane; it is the only place the two
    statements' vocabularies are ever put in correspondence, and it refuses on
    any class mismatch or non-injective assignment.
    """
    mapping: dict[str, str] = {}
    reverse: dict[str, str] = {}

    def walk(left: tuple, right: tuple) -> bool:
        if left[0] == "slot" and right[0] == "slot":
            if a_classes.get(left[1], "V") != c_classes.get(right[1], "V"):
                return False
            old = mapping.setdefault(left[1], right[1])
            prior = reverse.setdefault(right[1], left[1])
            return old == right[1] and prior == left[1]
        if left[0] != right[0] or left[1] != right[1]:
            return False
        if left[0] == "num":
            return True
        if len(left[2]) != len(right[2]):
            return False
        return all(walk(x, y) for x, y in zip(left[2], right[2]))

    return mapping if walk(a, c) else None


IDENTITY_OF = {"*": 1.0, "+": 0.0}


def drop_arithmetic_identities(tree: tuple) -> tuple:
    """Delete `*(1, ...)` and `+(0, ...)` arguments, as the corpus writes it.

    `specialize.Search` binds a parameter-like slot to an identity element
    precisely when the specific statement ran out of arguments -- the factor is
    not written. Re-substituting the pattern into a twin puts it back, so this
    is the inverse of that step, not a simplifier with opinions.
    """
    if tree[0] in {"slot", "num"}:
        return tree
    args = tuple(drop_arithmetic_identities(child) for child in tree[2])
    ident = IDENTITY_OF.get(tree[1]) if tree[0] == "op" else None
    if ident is not None:
        kept = tuple(a for a in args if not (a[0] == "num" and a[1] == ident))
        if len(kept) == 1:
            return kept[0]
        if kept:
            args = kept
    return (tree[0], tree[1], args)


def eq_modulo_symmetry(left: tuple, right: tuple) -> bool:
    """Tree equality that ignores the side order of a symmetric relation.

    `canonicalize` sorts commutative OPERATOR arguments but leaves a relation's
    two sides where the parser put them, and `Search.gen_direct` explicitly
    tries `=` in both orders. So two derivations of the same statement can
    differ by a swap and by nothing else.
    """
    if left == right:
        return True
    if (left[0] == "rel" and right[0] == "rel" and left[1] == right[1]
            and left[1] in SYMMETRIC_RELATIONS):
        return (left[2][0] == right[2][1]) and (left[2][1] == right[2][0])
    return False


def contiguous_slice(haystack: list[str], needle: list[str]) -> bool:
    n = len(needle)
    if not n or n > len(haystack):
        return False
    return any(haystack[i:i + n] == needle for i in range(len(haystack) - n + 1))


# ---------------------------------------------------------------------------
# corpus loading
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Corpus:
    raw: dict[str, dict]
    parsed_by_id: dict
    typed_groups: dict
    trees: dict[str, tuple]          # plain-canonical, as specialize.main uses
    ordered: dict[str, tuple]        # typed_resort, so twins line up
    classes: dict[str, dict[str, str]]
    node_slots: dict[str, frozenset]
    disc_slots: dict[str, frozenset]
    authored: frozenset


def load_corpus(data_dir: Path) -> Corpus:
    parsed, problems = load_nodes(data_dir)
    if problems:
        raise ValueError(f"corpus parse problems: {problems}")
    raw: dict[str, dict] = {}
    trees: dict[str, tuple] = {}
    ordered: dict[str, tuple] = {}
    classes: dict[str, dict[str, str]] = {}
    node_slots: dict[str, frozenset] = {}
    disc: dict[str, set] = {}
    for path in sorted(data_dir.glob("*/nodes.json")):
        corpus = json.loads(path.read_text(encoding="utf-8"))
        discipline = corpus.get("discipline", path.parent.name)
        vocab = disc.setdefault(discipline, set())
        for node in corpus["statement_nodes"]:
            sid = node["statement_id"]
            item = dict(node)
            item["_discipline"] = discipline
            raw[sid] = item
            cls = slot_classes(node)
            vocab.update(cls)
            tree = parse_template(node["structural_signature"]["anonymized_template"])
            trees[sid] = tree
            ordered[sid] = typed_resort(tree, cls)
            classes[sid] = cls
            node_slots[sid] = frozenset(cls)
    return Corpus(
        raw=raw,
        parsed_by_id={n.statement_id: n for n in parsed},
        typed_groups=group_by(parsed, "typed"),
        trees=trees,
        ordered=ordered,
        classes=classes,
        node_slots=node_slots,
        disc_slots={k: frozenset(v) for k, v in disc.items()},
        authored=frozenset(render(t) for t in trees.values()),
    )


# ---------------------------------------------------------------------------
# quadruple construction
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Quadruple:
    a_id: str
    b_id: str
    c_id: str
    a_discipline: str
    b_discipline: str
    c_discipline: str
    family: str                       # A's typed skeleton = the matcher's own quotient
    via: str                          # specializer mechanism mix for A >= B
    a_tree: tuple
    b_tree: tuple
    c_tree: tuple
    d_tree: tuple
    expansion_leaves: tuple           # B leaves carried into D verbatim
    renamed_leaves: tuple             # C leaves D reaches through the twin alignment

    @property
    def target(self) -> str:
        return render(self.d_tree)

    @property
    def key(self) -> tuple:
        return (render(self.a_tree), render(self.b_tree),
                render(self.c_tree), self.target)


def build_quadruples(data_dir: Path = DATA_DIR,
                     specialization_path: Path = SPEC_REPORT,
                     ledger: Counter | None = None) -> list[Quadruple]:
    """Every admitted A:B::C:D, with a rejection ledger for the refused ones."""
    corpus = load_corpus(data_dir)
    ledger = Counter() if ledger is None else ledger
    edges = json.loads(specialization_path.read_text(encoding="utf-8"))[
        "specialization_edges"]
    out: list[Quadruple] = []

    for edge in edges:
        a_meta = corpus.parsed_by_id.get(edge["general"])
        b_meta = corpus.parsed_by_id.get(edge["specific"])
        if a_meta is None or b_meta is None:
            ledger["edge_endpoint_unparsed"] += 1
            continue
        twins = [c for c in corpus.typed_groups.get(a_meta.typed, [])
                 if c.statement_id != a_meta.statement_id
                 and c.discipline != a_meta.discipline]
        if not twins:
            ledger["no_cross_discipline_twin"] += 1
            continue

        # Re-derive the edge through the specializer rather than trusting the
        # rendered strings in the report: the report prints bindings, and the
        # builder needs the TREES. Agreement with the committed report is
        # asserted, so the ledger stays load-bearing instead of decorative.
        ranker = spelling_ranker(corpus.node_slots[b_meta.statement_id],
                                 corpus.disc_slots[b_meta.discipline])
        a_plain = corpus.trees[a_meta.statement_id]
        best = Search(corpus.classes[a_meta.statement_id], op_count(a_plain),
                      ranker).run(a_plain, corpus.trees[b_meta.statement_id])
        if best is None:
            ledger["specializer_rederive_failed"] += 1
            continue
        if {k: render(v) for k, v in sorted(best.binds.items())} != edge["bindings"]:
            ledger["specializer_disagrees_with_report"] += 1
            continue
        if best.head_collapses:
            # The collapse REMOVED a node from B, so the element it binds
            # (FALSITY / EMPTYSET / ...) is nowhere in the input. Admitting it
            # would be inventing vocabulary; refusing it is bullet 1.
            ledger["head_identity_collapse_not_pointable"] += 1
            continue

        sigma = dict(best.binds)
        tau: dict[str, str] = {}
        ambiguous = False
        for a_slot, term in sigma.items():
            if term[0] != "slot":
                continue
            if term[1] in tau and tau[term[1]] != a_slot:
                ambiguous = True
            tau[term[1]] = a_slot
        if ambiguous:
            ledger["ambiguous_rename_inverse"] += 1
            continue

        a_node = corpus.raw[a_meta.statement_id]
        a_tree = corpus.ordered[a_meta.statement_id]
        b_tree = corpus.ordered[b_meta.statement_id]
        a_classes = corpus.classes[a_meta.statement_id]

        for c_meta in twins:
            c_node = corpus.raw[c_meta.statement_id]
            c_tree = corpus.ordered[c_meta.statement_id]
            rho = align_twin_slots(a_tree, c_tree, a_classes,
                                   corpus.classes[c_meta.statement_id])
            if rho is None:
                ledger["twin_alignment_refused"] += 1
                continue
            if any(name not in rho for name in sigma):
                ledger["bound_slot_outside_alignment"] += 1
                continue

            translate = {b_slot: rho[a_slot] for b_slot, a_slot in tau.items()}
            # Accidental capture: an expansion leaf that happens to spell a
            # slot the alignment also produces would fuse two distinct origins
            # into one token, and the target would stop being derivable.
            produced = set(translate.values())
            carried = {s for s in tree_slots(b_tree) if s not in translate}
            if produced & carried:
                ledger["expansion_leaf_collides_with_alignment"] += 1
                continue

            d_tree = canonicalize(rename(b_tree, translate))
            # Cross-check: specializing C directly must give the same target,
            # so D is not an artefact of which construction we happened to
            # write down. Two normalizations are needed and both are forced by
            # the specializer's own mechanisms rather than chosen for
            # convenience:
            #   * symmetric orientation, because `Search.gen_direct` matches
            #     `=` in both directions and D keeps B's side order;
            #   * arithmetic identities, because the identity rule fires
            #     exactly when the specific statement DOES NOT WRITE the
            #     factor. Substituting into C re-inserts `*(1, ...)`; B is the
            #     corpus-faithful form, and it is also the only pointable one,
            #     since a `1` the matcher supplied appears nowhere in the
            #     input. That is bullet 1 deciding a representation question.
            terms = {rho[a_slot]: rename(term, translate)
                     for a_slot, term in sigma.items()}
            direct = canonicalize(drop_arithmetic_identities(
                substitute(c_tree, terms)))
            if not eq_modulo_symmetry(direct, d_tree):
                ledger["two_constructions_disagree"] += 1
                continue

            quad = _finish(corpus, a_meta, b_meta, c_meta, edge, a_tree,
                           b_tree, c_tree, d_tree, translate, ledger)
            if quad is not None:
                out.append(quad)
    return out


def _finish(corpus: Corpus, a_meta, b_meta, c_meta, edge: dict, a_tree: tuple,
            b_tree: tuple, c_tree: tuple, d_tree: tuple,
            translate: dict[str, str], ledger: Counter) -> Quadruple | None:
    target = render(d_tree)
    if target in corpus.authored:
        ledger["target_is_an_authored_statement"] += 1
        return None
    if d_tree in (a_tree, b_tree, c_tree):
        ledger["target_equals_an_input_statement"] += 1
        return None

    tokens = (serialize(a_tree) + [SEP] + serialize(b_tree) + [SEP]
              + serialize(c_tree))
    d_tokens = serialize(d_tree)
    # Bullet 1, enforced rather than argued: every token of D must already be
    # readable somewhere in the input.
    unpointable = sorted(set(d_tokens) - set(tokens))
    if unpointable:
        ledger["target_token_not_pointable"] += 1
        return None
    # Bullet 6, second clause: D absent from the input, as a sequence.
    if contiguous_slice(tokens, d_tokens):
        ledger["target_occurs_verbatim_in_input"] += 1
        return None

    # Bullet 6, first clause: the specializer must independently accept C >= D
    # under the SAME acceptability bar that edge reporting uses.
    c_ranker = spelling_ranker(corpus.node_slots[c_meta.statement_id],
                               corpus.disc_slots[c_meta.discipline])
    proof = Search(corpus.classes[c_meta.statement_id], op_count(c_tree),
                   c_ranker).run(c_tree, d_tree)
    if proof is None:
        ledger["specializer_refuses_c_to_d"] += 1
        return None
    # The target has to survive a full round trip through the representation
    # the task actually ships, or it is not a target a pointer could realize.
    # (`specialize.render` prints ops in prefix form, which the infix template
    # Parser cannot read back -- an asymmetry inherited from v0.6 -- so the
    # round trip that matters here is serialize/deserialize, which is also the
    # only reader the input-only symbolic control is allowed to use.)
    if canonicalize(deserialize(d_tokens)) != d_tree:
        ledger["target_does_not_round_trip"] += 1
        return None

    expansion = tuple(sorted(t for t in set(d_tokens) if is_leaf_token(t)
                             and t in set(serialize(b_tree))
                             and t not in translate.values()))
    renamed = tuple(sorted(set(translate.values()) & set(d_tokens)))
    if not renamed:
        ledger["no_leaf_reaches_c"] += 1
        return None
    ledger["ADMITTED"] += 1
    return Quadruple(
        a_id=a_meta.statement_id, b_id=b_meta.statement_id,
        c_id=c_meta.statement_id, a_discipline=a_meta.discipline,
        b_discipline=b_meta.discipline, c_discipline=c_meta.discipline,
        family=a_meta.typed, via=edge["via"], a_tree=a_tree, b_tree=b_tree,
        c_tree=c_tree, d_tree=d_tree, expansion_leaves=expansion,
        renamed_leaves=renamed)


# ---------------------------------------------------------------------------
# pointer realization
# ---------------------------------------------------------------------------

def blocks(quad: Quadruple) -> tuple[list[str], list[str], list[str]]:
    return (serialize(quad.a_tree), serialize(quad.b_tree),
            serialize(quad.c_tree))


def input_tokens(quad: Quadruple) -> list[str]:
    a, b, c = blocks(quad)
    return a + [SEP] + b + [SEP] + c


def pointer_row(quad: Quadruple) -> dict:
    """Serialize one example, with every target token an explicit pointer.

    Provenance is deliberate rather than incidental: a leaf the twin alignment
    produced points into C, and everything else points into B first (its
    structure and its expansion leaves both live there), falling back to C then
    A. v0.6 resolved by token identity alone, which silently attributed a
    B-vocabulary leaf to C whenever the two corpora spelled a slot the same.
    """
    a_tok, b_tok, c_tok = blocks(quad)
    tokens = a_tok + [SEP] + b_tok + [SEP] + c_tok
    b_off = len(a_tok) + 1
    c_off = b_off + len(b_tok) + 1
    first_in = {}
    for name, off, block in (("C", c_off, c_tok), ("B", b_off, b_tok),
                             ("A", 0, a_tok)):
        for i, token in enumerate(block):
            first_in.setdefault((name, token), off + i)

    d_tokens = serialize(quad.d_tree)
    from_c = set(quad.renamed_leaves)
    actions, sources = [], []
    for token in d_tokens:
        order = ("C", "B", "A") if token in from_c else ("B", "C", "A")
        for name in order:
            pos = first_in.get((name, token))
            if pos is not None:
                actions.append(pos)
                sources.append(name)
                break
        else:  # pragma: no cover - the pointability gate forbids this
            raise AssertionError(f"unpointable target token {token!r}")
    if [tokens[p] for p in actions] != d_tokens:
        raise AssertionError("pointer realization does not reconstruct D")
    return {
        "task": "corpus_analogy_v07",
        "tokens_struct": tokens,
        "target_positions": actions,
        "target_tokens": d_tokens,
        "target_render": quad.target,
        "pointer_sources": "".join(sources),
        "provenance": {"A": quad.a_id, "B": quad.b_id, "C": quad.c_id},
        "family": quad.family,
        "via": quad.via,
        "source_discipline": quad.a_discipline,
        "discipline": quad.c_discipline,
        "expansion_leaves": list(quad.expansion_leaves),
        "renamed_leaves": list(quad.renamed_leaves),
    }


# ---------------------------------------------------------------------------
# dedup
# ---------------------------------------------------------------------------

def dedup_by_target(quads: list[Quadruple]) -> list[Quadruple]:
    """One example per DISTINCT rendered target (bullet 4).

    v0.6 counted 40 rows over 5 targets; every control it reported was really
    a five-point measurement wearing a forty-point coat. The canonical row for
    a target is the lexicographically smallest full key, so the choice does not
    depend on ledger order.
    """
    best: dict[str, Quadruple] = {}
    for quad in quads:
        prior = best.get(quad.target)
        if prior is None or quad.key < prior.key:
            best[quad.target] = quad
    return sorted(best.values(), key=lambda q: q.key)


# ---------------------------------------------------------------------------
# holdouts
# ---------------------------------------------------------------------------

def _alternating(keys_by_size: list[str]) -> set[str]:
    """Hold out every second key in descending-size order.

    Deterministic, salt-free and un-tunable: there is no seed to search over
    and no threshold to move, so a split cannot be quietly re-rolled until the
    ceiling looks good. It also guarantees the holdout is not simply the tail
    of the distribution.
    """
    return {key for i, key in enumerate(keys_by_size) if i % 2 == 1}


def _by_size(counts: Counter) -> list[str]:
    return [k for k, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def untyped_shape(quad: Quadruple) -> tuple:
    """The twin's head/arity multiset -- slot classes DROPPED.

    The coarser quotient `_shape_leak` and the `untyped_shapes` count already
    use: `*(?1:P, ?2:V)` and `*(?1:V, ?2:V)` are two TYPED families and ONE
    shape. A and C share a typed skeleton (twins are grouped by it, then the
    alignment re-checks head/arity), so this is A's shape as much as C's.
    """
    return tuple(sorted(_op_multiset(quad.c_tree).items()))


def family_split(quads: list[Quadruple]) -> dict[str, str]:
    held = _alternating(_by_size(Counter(q.family for q in quads)))
    return {q.target: ("holdout" if q.family in held else "train") for q in quads}


def shape_split(quads: list[Quadruple]) -> dict[str, str]:
    """Hold out whole UNTYPED shapes -- the split the family holdout should have
    been (v0.8 item 2, ROADMAP-v0.7 item 5's disclosed defect).

    Family = A's TYPED skeleton, so two families can be one shape, and a
    nearest-template replay scores ~1.000 on any held row whose shape survives
    in training -- the leak `_shape_leak` measures and the family holdout's
    0.400 is inflated by. Cutting on the shape instead makes a held row's shape
    GENUINELY absent from training, so that leak is closed by construction, not
    by tuning. Same deterministic, seedless, alternating-by-size rule as the
    other three; there is nothing here to re-roll.
    """
    held = _alternating(_by_size(Counter(untyped_shape(q) for q in quads)))
    return {q.target: ("holdout" if untyped_shape(q) in held else "train")
            for q in quads}


def discipline_split(quads: list[Quadruple]) -> dict[str, str]:
    held = _alternating(_by_size(Counter(q.c_discipline for q in quads)))
    return {q.target: ("holdout" if q.c_discipline in held else "train")
            for q in quads}


def vocabulary_split(quads: list[Quadruple],
                     share: float = VOCAB_HOLDOUT_TARGET_SHARE) -> dict[str, str]:
    """Hold out the RAREST target-side literal tokens until `share` is met.

    The held tokens never appear in a training TARGET. They may still appear in
    a training INPUT, and that is the point: this lane is a pointing task, so a
    token has to stay pointable to be producible at all. The leakage the split
    removes is "this word has been emitted before", which is the only
    vocabulary leakage a pointer network can exploit.
    """
    target_tokens = {q.target: sorted({t for t in serialize(q.d_tree)
                                       if is_leaf_token(t)}) for q in quads}
    freq = Counter(t for tokens in target_tokens.values() for t in tokens)
    order = [k for k, _ in sorted(freq.items(), key=lambda kv: (kv[1], kv[0]))]
    held_tokens: set[str] = set()
    assignment = {q.target: "train" for q in quads}
    want = int(round(share * len(quads)))
    for token in order:
        if sum(1 for v in assignment.values() if v == "holdout") >= want:
            break
        held_tokens.add(token)
        assignment = {
            target: ("holdout" if held_tokens & set(tokens) else "train")
            for target, tokens in target_tokens.items()}
    return assignment


SPLIT_BUILDERS = {"family": family_split, "discipline": discipline_split,
                  "vocabulary": vocabulary_split, "shape": shape_split}


def build_splits(quads: list[Quadruple]) -> dict[str, dict[str, str]]:
    return {name: builder(quads) for name, builder in SPLIT_BUILDERS.items()}


def leakage_surfaces(quads: list[Quadruple],
                     splits: dict[str, dict[str, str]]) -> dict:
    """Each split's holdout must leave the OTHER two axes fully covered.

    That is the operational reading of "disjoint leakage surfaces": whatever a
    split removes, the other splits' axes are still present on both sides, so
    the three are not three names for one partition.
    """
    axes = {"family": lambda q: q.family,
            "discipline": lambda q: q.c_discipline,
            "shape": untyped_shape}
    out: dict[str, dict] = {}
    for name, assignment in splits.items():
        train = [q for q in quads if assignment[q.target] == "train"]
        held = [q for q in quads if assignment[q.target] == "holdout"]
        if name == "vocabulary":
            held_keys = sorted(_vocab(held) - _vocab(train))
        elif name == "shape":
            # shape keys are head/arity multisets; render them for the report
            held_keys = sorted({str(untyped_shape(q)) for q in held})
        else:
            held_keys = sorted({axes[name](q) for q in held})
        entry: dict = {"train": len(train), "holdout": len(held),
                       "held_keys": held_keys}
        for other in ("family", "discipline"):
            if other == name:
                continue
            key = axes[other]
            held_vals = {key(q) for q in held}
            train_vals = {key(q) for q in train}
            entry[f"{other}_values_in_holdout_also_in_train"] = (
                len(held_vals & train_vals), len(held_vals))
        if name != "vocabulary":
            entry["holdout_target_tokens_unseen_in_train_targets"] = len(
                _vocab(held) - _vocab(train))
        entry["jaccard_with"] = {
            other: _jaccard({q.target for q in quads if assignment[q.target] == "holdout"},
                            {q.target for q in quads
                             if splits[other][q.target] == "holdout"})
            for other in splits if other != name}
        out[name] = entry
    return out


def _vocab(quads: list[Quadruple]) -> set[str]:
    return {t for q in quads for t in serialize(q.d_tree) if is_leaf_token(t)}


def _jaccard(left: set, right: set) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


# ---------------------------------------------------------------------------
# capability-blind controls
# ---------------------------------------------------------------------------

def _leaves(tree: tuple, kind: str) -> list[tuple]:
    if tree[0] == kind:
        return [tree]
    if tree[0] in {"slot", "num"}:
        return []
    return [leaf for child in tree[2] for leaf in _leaves(child, kind)]


def _replace_named(tree: tuple, name: str, value: tuple) -> tuple:
    if tree == ("slot", name):
        return value
    if tree[0] in {"slot", "num"}:
        return tree
    return (tree[0], tree[1],
            tuple(_replace_named(child, name, value) for child in tree[2]))


def ctl_copy_c(quad: Quadruple, ctx: dict) -> tuple | None:
    return quad.c_tree


def ctl_copy_b(quad: Quadruple, ctx: dict) -> tuple | None:
    return quad.b_tree


def ctl_last_slot_number_transfer(quad: Quadruple, ctx: dict) -> tuple | None:
    """v0.6's killer, ported verbatim. It scored 1.000 on the old lane."""
    a_nums = [leaf[1] for leaf in _leaves(quad.a_tree, "num")]
    new = [leaf for leaf in _leaves(quad.b_tree, "num") if leaf[1] not in a_nums]
    c_slots = [leaf[1] for leaf in _leaves(quad.c_tree, "slot")]
    if len(new) != 1 or not c_slots:
        return None
    return canonicalize(_replace_named(quad.c_tree, c_slots[-1], new[0]))


def ctl_first_slot_number_transfer(quad: Quadruple, ctx: dict) -> tuple | None:
    a_nums = [leaf[1] for leaf in _leaves(quad.a_tree, "num")]
    new = [leaf for leaf in _leaves(quad.b_tree, "num") if leaf[1] not in a_nums]
    c_slots = [leaf[1] for leaf in _leaves(quad.c_tree, "slot")]
    if len(new) != 1 or not c_slots:
        return None
    return canonicalize(_replace_named(quad.c_tree, c_slots[0], new[0]))


def ctl_positional_rename(quad: Quadruple, ctx: dict) -> tuple | None:
    """B with its k-th distinct slot renamed to C's k-th distinct slot.

    Pure position; no alignment, no bindings, no corpus metadata. This is the
    heuristic that the v0.6 lane would also have fallen to, generalized off the
    single number to the whole leaf sequence.
    """
    b_names, c_names = slot_order(quad.b_tree), slot_order(quad.c_tree)
    if not c_names:
        return None
    mapping = {b: c_names[i] for i, b in enumerate(b_names) if i < len(c_names)}
    return canonicalize(rename(quad.b_tree, mapping))


def ctl_nearest_authored(quad: Quadruple, ctx: dict) -> tuple | None:
    query = render(quad.c_tree)
    best = min(ctx["authored_pairs"],
               key=lambda kv: (_edit(query, kv[0]), kv[0]))
    return best[1]


def _action_pattern(quad: Quadruple) -> tuple | None:
    """(block, offset) for every target token -- the row's realization recipe."""
    row = pointer_row(quad)
    a_tok, b_tok, _c = blocks(quad)
    b_off, c_off = len(a_tok) + 1, len(a_tok) + len(b_tok) + 2
    pattern = []
    for pos in row["target_positions"]:
        if pos < len(a_tok):
            pattern.append(("A", pos))
        elif pos < c_off - 1:
            pattern.append(("B", pos - b_off))
        else:
            pattern.append(("C", pos - c_off))
    return tuple(pattern)


def _apply_pattern(quad: Quadruple, pattern: tuple) -> tuple | None:
    a_tok, b_tok, c_tok = blocks(quad)
    lookup = {"A": a_tok, "B": b_tok, "C": c_tok}
    out = []
    for block, offset in pattern:
        seq = lookup[block]
        if offset >= len(seq):
            return None
        out.append(seq[offset])
    try:
        return canonicalize(deserialize(out))
    except (ValueError, IndexError, KeyError):
        return None


def ctl_nearest_template_transfer(quad: Quadruple, ctx: dict) -> tuple | None:
    """Replay the pointer-action pattern of the nearest TRAINING input.

    This is the strong blind baseline. Retrieving a training TARGET can only
    ever score 0 here (dedup makes holdout targets unseen by construction), and
    reporting that as a baseline is exactly the mistake v0.6 review caught. A
    pattern replay can emit a novel target, so it is a capability claim.
    """
    train = ctx.get("train_patterns")
    if not train:
        return None
    query = tuple(input_tokens(quad))
    _, pattern = min(train, key=lambda kv: (_edit(query, kv[0]), kv[0]))
    return _apply_pattern(quad, pattern)


def ctl_modal_pattern(quad: Quadruple, ctx: dict) -> tuple | None:
    """The single most frequent training action pattern, replayed blind."""
    pattern = ctx.get("modal_pattern")
    return _apply_pattern(quad, pattern) if pattern else None


def ctl_symbolic_input_only(quad: Quadruple, ctx: dict) -> tuple | None:
    """Solve from `A <sep> B <sep> C` alone -- no corpus metadata at all.

    Slot classes are unavailable to a reader of the token stream, so every slot
    is treated as a variable. If this scores 1.000 the task is closed-form
    solvable from its own input, and the lane measures the pointing mechanism
    rather than a residual only weights could supply (P-CS2).
    """
    tokens = ctx.get("tokens", input_tokens(quad))
    first = tokens.index(SEP)
    second = tokens.index(SEP, first + 1)
    try:
        a = deserialize(tokens[:first])
        b = deserialize(tokens[first + 1:second])
        c = deserialize(tokens[second + 1:])
    except (ValueError, IndexError):
        return None
    flat = {name: "V" for name in tree_slots(a) | tree_slots(b) | tree_slots(c)}
    rho = align_twin_slots(a, c, flat, flat)
    if rho is None:
        return None
    best = Search(flat, op_count(a), lambda _h: ()).run(a, b)
    if best is None:
        return None
    sigma = dict(best.binds)
    if any(name not in rho for name in sigma):
        return None
    tau: dict[str, str] = {}
    for a_slot, term in sigma.items():
        if term[0] == "slot":
            if term[1] in tau and tau[term[1]] != a_slot:
                return None
            tau[term[1]] = a_slot
    translate = {b_slot: rho[a_slot] for b_slot, a_slot in tau.items()}
    terms = {rho[a_slot]: rename(term, translate)
             for a_slot, term in sigma.items()}
    return canonicalize(substitute(c, terms))


def _declared_idents(head: str) -> tuple:
    return tuple((term, "sole") for term in identity_terms(head))


def ctl_symbolic_typed_input(quad: Quadruple, ctx: dict) -> tuple | None:
    """The same solver, plus the corpus's DECLARED slot classes and identities.

    This exists to attribute `symbolic_input_only`'s shortfall rather than
    merely report it. The two solvers differ in two DECISIVE inputs: the
    parameter/variable class of each slot, and the identity table. (There is
    a third, causally-inert implementation difference — this control renames
    B while the input-only solver substitutes into C — verified to change no
    ceiling: untyped scores 0.458/0.545/0.651 under either spelling.) Both
    decisive inputs are
    corpus declarations, not facts a reader of the token stream could recover,
    and `Search` gates its arithmetic-identity rule on the class being `P`. If
    this control reaches 1.000 while the input-only one does not, the residual
    the lane leaves to something other than the token stream IS that
    declaration -- which is a far more specific claim than "the task is hard".
    """
    corpus: Corpus = ctx["corpus"]
    tokens = ctx.get("tokens", input_tokens(quad))
    first = tokens.index(SEP)
    second = tokens.index(SEP, first + 1)
    try:
        a = deserialize(tokens[:first])
        b = deserialize(tokens[first + 1:second])
        c = deserialize(tokens[second + 1:])
    except (ValueError, IndexError):
        return None
    a_cls = corpus.classes[quad.a_id]
    rho = align_twin_slots(a, c, a_cls, corpus.classes[quad.c_id])
    if rho is None:
        return None
    best = Search(a_cls, op_count(a), _declared_idents).run(a, b)
    if best is None or best.head_collapses:
        return None
    sigma = dict(best.binds)
    if any(name not in rho for name in sigma):
        return None
    tau: dict[str, str] = {}
    for a_slot, term in sigma.items():
        if term[0] == "slot":
            if term[1] in tau and tau[term[1]] != a_slot:
                return None
            tau[term[1]] = a_slot
    translate = {b_slot: rho[a_slot] for b_slot, a_slot in tau.items()}
    return canonicalize(rename(b, translate))


def ctl_symbolic_oracle(quad: Quadruple, ctx: dict) -> tuple | None:
    """The construction itself: full corpus metadata, 1.000 by definition."""
    return quad.d_tree


BLIND_CONTROLS = {
    "copy_c": ctl_copy_c,
    "copy_b": ctl_copy_b,
    "last_slot_number_transfer": ctl_last_slot_number_transfer,
    "first_slot_number_transfer": ctl_first_slot_number_transfer,
    "positional_rename": ctl_positional_rename,
    "modal_action_pattern": ctl_modal_pattern,
    "nearest_template_transfer": ctl_nearest_template_transfer,
    "nearest_authored_template": ctl_nearest_authored,
}
# Not blind: they are the capability, reported so the ceiling has a roof.
SIGHTED_CONTROLS = {
    "symbolic_input_only": ctl_symbolic_input_only,
    "symbolic_typed_input": ctl_symbolic_typed_input,
    "symbolic_oracle": ctl_symbolic_oracle,
}
# Sanity controls forced by admission: they CANNOT score above zero, so they
# are reported as vacuity checks and excluded from the blind ceiling.
NOVELTY_SANITY = {"copy_c", "copy_b", "nearest_authored_template"}


def _edit(left: str, right: str) -> int:
    prior = list(range(len(right) + 1))
    for i, lchar in enumerate(left, 1):
        row = [i]
        for j, rchar in enumerate(right, 1):
            row.append(min(row[-1] + 1, prior[j] + 1,
                           prior[j - 1] + (lchar != rchar)))
        prior = row
    return prior[-1]


def shuffle_c_leaves(quad: Quadruple) -> list[str]:
    """Deterministically permute C's leaf tokens, structure untouched.

    A control that survives this was never reading C, and any score it keeps is
    coming from A and B alone.
    """
    tokens = input_tokens(quad)
    second = tokens.index(SEP, tokens.index(SEP) + 1)
    leaves = [i for i in range(second + 1, len(tokens))
              if is_leaf_token(tokens[i])]
    if len(leaves) < 2:
        return tokens
    names = [tokens[i] for i in leaves]
    digest = hashlib.md5(" ".join(names).encode("utf-8")).digest()
    rotated = names[digest[0] % len(names) or 1:] + names[:digest[0] % len(names) or 1]
    out = list(tokens)
    for i, name in zip(leaves, rotated):
        out[i] = name
    return out


def score(control, quads: list[Quadruple], ctx: dict) -> float:
    if not quads:
        return float("nan")
    hits = 0
    for quad in quads:
        try:
            guess = control(quad, ctx)
        except (ValueError, IndexError, KeyError, RecursionError):
            guess = None
        if guess is not None and render(guess) == quad.target:
            hits += 1
    return hits / len(quads)


def build_context(train: list[Quadruple], corpus: Corpus) -> tuple[dict, dict]:
    """Build the blind context and the sighted one, as two separate objects.

    A blind control must not be able to reach corpus metadata, and "we checked
    that none of them do" is the kind of assurance this project does not
    accept. Review of this file found the `Corpus` handle sitting in the single
    shared context, one attribute access away from every capability-blind
    scorer -- inert, but only by convention. The blind dict now physically does
    not contain it, so a control that wanted the answer would have to change
    this function to get it.

    `authored_pairs` stays on the blind side because
    `nearest_authored_template` needs it and is a NOVELTY SANITY control: it is
    pinned at zero by admission and excluded from the ceiling.
    """
    # Token-level, not character-level: the neighbourhood a template baseline
    # should search is "same shape, different words", and character distance
    # would let a long slot name outvote a whole missing subtree.
    patterns = [(tuple(input_tokens(q)), _action_pattern(q)) for q in train]
    modal = Counter(p for _, p in patterns).most_common(1)
    blind = {
        "train_patterns": patterns,
        "modal_pattern": modal[0][0] if modal else None,
        "authored_pairs": [(render(t), t) for t in
                           sorted(set(corpus.trees.values()), key=render)],
    }
    return blind, {**blind, "corpus": corpus}


def ceiling_table(quads: list[Quadruple], splits: dict[str, dict[str, str]],
                  corpus: Corpus) -> dict:
    table: dict[str, dict] = {}
    for name, assignment in splits.items():
        train = [q for q in quads if assignment[q.target] == "train"]
        held = [q for q in quads if assignment[q.target] == "holdout"]
        blind_ctx, sighted_ctx = build_context(train, corpus)
        entry: dict[str, object] = {"train_n": len(train), "holdout_n": len(held)}
        blind: dict[str, float] = {}
        for ctl_name, control in BLIND_CONTROLS.items():
            blind[ctl_name] = score(control, held, blind_ctx)
        entry["blind"] = blind
        entry["sighted"] = {n: score(c, held, sighted_ctx)
                            for n, c in SIGHTED_CONTROLS.items()}
        # Shuffled-input controls: same scorers, C's leaves permuted.
        shuffled = {}
        for ctl_name in ("symbolic_input_only", "positional_rename",
                         "nearest_template_transfer"):
            control = {**BLIND_CONTROLS, **SIGHTED_CONTROLS}[ctl_name]
            base = (sighted_ctx if ctl_name in SIGHTED_CONTROLS else blind_ctx)
            hits = 0
            for quad in held:
                sctx = dict(base)
                sctx["tokens"] = shuffle_c_leaves(quad)
                try:
                    guess = control(_shuffled_quad(quad), sctx)
                except (ValueError, IndexError, KeyError, RecursionError):
                    guess = None
                hits += guess is not None and render(guess) == quad.target
            shuffled[ctl_name] = hits / len(held) if held else float("nan")
        entry["shuffled_c_leaves"] = shuffled
        candidates = {k: v for k, v in blind.items() if k not in NOVELTY_SANITY}
        best = max(candidates.items(), key=lambda kv: (kv[1], kv[0]))
        entry["blind_ceiling"] = best[1]
        entry["blind_ceiling_control"] = best[0]
        entry["per_family_nearest_template"] = {
            family: score(ctl_nearest_template_transfer,
                          [q for q in held if q.family == family], blind_ctx)
            for family in sorted({q.family for q in held})}
        entry["shape_leak"] = _shape_leak(train, held, blind_ctx)
        table[name] = entry
    return table


def _shape_leak(train: list[Quadruple], held: list[Quadruple],
                ctx: dict) -> dict:
    """Does a holdout leak through the UNTYPED shape?

    Families are TYPED skeletons, so two of them can share a head/arity shape
    and differ only in a slot class. If the strongest blind control scores
    where that happens and not where it does not, then the family holdout is
    holding out a NAME while leaving the structure in training -- a weaker
    holdout than the file's title claims. Splitting the same control on that
    one bit is the cheapest way to find out.
    """
    def shape(quad: Quadruple) -> tuple:
        return tuple(sorted(_op_multiset(quad.c_tree).items()))

    train_shapes = {shape(q) for q in train}
    leaky = [q for q in held if shape(q) in train_shapes]
    clean = [q for q in held if shape(q) not in train_shapes]
    return {
        "holdout_rows_whose_shape_is_in_train": len(leaky),
        "holdout_rows_with_an_unseen_shape": len(clean),
        "nearest_template_on_leaky_shapes": score(
            ctl_nearest_template_transfer, leaky, ctx),
        "nearest_template_on_unseen_shapes": score(
            ctl_nearest_template_transfer, clean, ctx),
    }


def _shuffled_quad(quad: Quadruple) -> Quadruple:
    """C with its leaves rotated, as a Quadruple, for the non-token controls."""
    tokens = shuffle_c_leaves(quad)
    second = tokens.index(SEP, tokens.index(SEP) + 1)
    try:
        c_tree = deserialize(tokens[second + 1:])
    except (ValueError, IndexError):
        return quad
    return Quadruple(**{**quad.__dict__, "c_tree": c_tree})


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def family_inventory(quads: list[Quadruple], corpus: Corpus) -> list[dict]:
    counts = Counter(q.family for q in quads)
    out = []
    for family, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        rows = [q for q in quads if q.family == family]
        sample = rows[0]
        out.append({
            "skeleton": family,
            "examples": n,
            "disciplines": sorted({q.c_discipline for q in rows}),
            "via": sorted({q.via for q in rows}),
            "op_multiset": _op_multiset(sample.c_tree),
            "example": {"A": render(sample.a_tree), "B": render(sample.b_tree),
                        "C": render(sample.c_tree), "D": sample.target},
        })
    return out


def _op_multiset(tree: tuple) -> dict[str, int]:
    """Head/arity multiset -- an isomorphism witness independent of `typed`.

    Arity is not decoration. `*` is n-ary after canonicalization, so
    `*(?1:P, ?2:V)` and `*(?1:P, ?2:V, ?3:V)` have the SAME head multiset while
    being different skeletons; keying on the head alone reported two live
    families as one, and the family test caught it.
    """
    counter: Counter = Counter()

    def walk(node: tuple) -> None:
        if node[0] in {"slot", "num"}:
            return
        counter[f"{node[1]}/{len(node[2])}"] += 1
        for child in node[2]:
            walk(child)

    walk(tree)
    return dict(sorted(counter.items()))


def split_lines(quads: list[Quadruple], assignment: dict[str, str],
                name: str) -> list[str]:
    """The exact JSONL body of one split file, as lines.

    Factored out of `run` so the determinism test can assert "regenerates
    exactly" against the SAME code path the CLI writes with, rather than
    against a reimplementation of it that could drift into agreement.
    """
    lines = []
    for quad in quads:
        row = pointer_row(quad)
        row["split"] = assignment[quad.target]
        row["holdout_axis"] = name
        lines.append(json.dumps(row, sort_keys=True))
    return lines


def write_split_files(quads: list[Quadruple],
                      splits: dict[str, dict[str, str]],
                      split_dir: Path) -> list[Path]:
    """Write the three holdout files. `experiments/data/` is gitignored.

    Repo policy: generated datasets are regenerated from committed generators,
    not stored in git. These files qualify only because the split rule takes no
    seed and no threshold to search over -- see `build_splits` -- so there is
    nothing a re-run could re-roll. The committed artifact is the ceiling table
    at `experiments/results/corpus_analogy_v07_ceilings.json`.
    """
    split_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, assignment in splits.items():
        path = split_dir / f"{SPLIT_PREFIX}_{name}.jsonl"
        body = "".join(line + "\n" for line in split_lines(quads, assignment, name))
        path.write_text(body, encoding="utf-8", newline="\n")
        written.append(path)
    return written


def run(data_dir: Path, specialization_path: Path, split_dir: Path,
        out: Path | None, write_splits: bool) -> dict:
    ledger: Counter = Counter()
    corpus = load_corpus(data_dir)
    raw_quads = build_quadruples(data_dir, specialization_path, ledger)
    quads = dedup_by_target(raw_quads)
    splits = build_splits(quads)
    result = {
        "task": "corpus_analogy_v07",
        "rows_before_dedup": len(raw_quads),
        "distinct_targets": len(quads),
        "dedup_compression": (len(raw_quads) / len(quads)) if quads else 0.0,
        "families": len({q.family for q in quads}),
        # The stricter count: how many families survive dropping slot classes.
        # `*(?1:P, ?2:V)` and `*(?1:V, ?2:V)` are two families to the matcher
        # and one shape here, and the roadmap's bullet is checked against this
        # number rather than the flattering one.
        "untyped_shapes": len({
            tuple(sorted(_op_multiset(q.c_tree).items())) for q in quads}),
        "source_disciplines": sorted({q.a_discipline for q in quads}),
        "target_disciplines": sorted({q.c_discipline for q in quads}),
        "rows_with_compound_expansion": sum(1 for q in quads if q.expansion_leaves),
        "admission_ledger": dict(sorted(ledger.items())),
        "family_inventory": family_inventory(quads, corpus),
        "leakage_surfaces": leakage_surfaces(quads, splits),
        "ceilings": ceiling_table(quads, splits, corpus),
    }
    if write_splits:
        write_split_files(quads, splits, split_dir)
        result["split_files"] = [f"{SPLIT_PREFIX}_{n}.jsonl" for n in SPLIT_NAMES]
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=DATA_DIR)
    ap.add_argument("--specializations", type=Path, default=SPEC_REPORT)
    ap.add_argument("--split-dir", type=Path, default=SPLIT_DIR)
    ap.add_argument("--no-write-splits", action="store_true")
    ap.add_argument("--out", type=Path,
                    default=ROOT / "experiments" / "results" /
                    "corpus_analogy_v07_ceilings.json")
    args = ap.parse_args()
    result = run(args.data_dir, args.specializations, args.split_dir,
                 args.out, not args.no_write_splits)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
