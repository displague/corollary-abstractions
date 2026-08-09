"""Corpus-grounded analogy evaluation for v0.6.

The synthetic analogy task proved recombinant pointing, not corpus transfer.
This evaluation constructs A:B::C:D only when three independent corpus facts
agree: A:C is a typed twin, A:B is a committed cheapest-specialization edge,
and the specializer independently accepts C:D after the binding is moved.

Retrospective prediction labels (written in the working tree before the run,
but not committed separately, so they are not auditable preregistrations):

P-CA1  The live corpus yields at least one cross-discipline quadruple whose D
       is absent from every authored template.
P-CA2  The symbolic resolver is exact on every admitted row. Copying C and
       returning the nearest authored template are novelty sanity controls;
       a number-transfer heuristic is the capability-blind baseline.
P-CA3  A checkpoint trained only on five synthetic whole-tree transforms will
       not retain its synthetic 1.000 exact score on corpus specializations;
       exact below 0.5 is the predicted domain-gap result.
P-CA4  Literal corpus-vocabulary evaluation refuses against the checkpoint's
       fixed vocabulary instead of silently mapping unknowns onto a real token.

The first lane is deliberately narrow: specialization bindings must be pure
slot renames plus numeric substitutions already representable by the released
checkpoint. Compound/identity expansions stay excluded until they have an
unambiguous source for every newly introduced leaf.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from match_signatures import (  # noqa: E402
    Parser,
    canonicalize,
    group_by,
    load_nodes,
    slot_classes,
    template_slots,
    tokenize,
    typed_resort,
)
from specialize import Search, op_count, render  # noqa: E402
from analogygen import SEP, serialize  # noqa: E402
from tokenizers import Vocab  # noqa: E402
from train_analogy import (  # noqa: E402
    AnalogyDataset,
    AnalogyPointer,
    collate,
    greedy_exact,
)


A_NAMES = ("alpha", "beta", "delta", "gamma", "kappa", "lambda",
           "omega", "phi", "rho", "sigma", "tau", "theta")
C_NAMES = ("AREA", "BASE", "CHARGE", "ENERGY", "FLUX", "FORCE",
           "HEIGHT", "LENGTH", "MASS", "PRESSURE", "RADIUS", "SPEED")


@dataclass(frozen=True)
class Quadruple:
    a_id: str
    b_id: str
    c_id: str
    a_discipline: str
    c_discipline: str
    family: str
    actual: tuple[tuple, tuple, tuple, tuple]
    normalized: tuple[tuple, tuple, tuple, tuple]


def parse_template(text: str) -> tuple:
    return canonicalize(Parser(tokenize(text)).parse())


def raw_nodes(data_dir: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted(data_dir.glob("*/nodes.json")):
        corpus = json.loads(path.read_text(encoding="utf-8"))
        discipline = corpus.get("discipline", path.parent.name)
        for node in corpus["statement_nodes"]:
            item = dict(node)
            item["_discipline"] = discipline
            out[node["statement_id"]] = item
    return out


def ordered_typed(node: dict) -> tuple:
    text = node["structural_signature"]["anonymized_template"]
    return typed_resort(parse_template(text), slot_classes(node))


def align_twin_slots(a: tuple, c: tuple, a_classes: dict[str, str],
                     c_classes: dict[str, str]) -> dict[str, str] | None:
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


def replace_slots(tree: tuple, names: dict[str, str]) -> tuple:
    if tree[0] == "slot":
        return ("slot", names[tree[1]])
    if tree[0] == "num":
        return tree
    return (tree[0], tree[1], tuple(replace_slots(x, names) for x in tree[2]))


def expression_residual(tree: tuple) -> tuple:
    """Keep the equation shell closed-form; the pointer owns the RHS only."""
    if tree[0] != "rel" or tree[1] != "=":
        raise ValueError("checkpoint evaluation requires an equality template")
    return tree[2][1]


def _binding_terms(edge: dict) -> dict[str, tuple] | None:
    terms: dict[str, tuple] = {}
    for name, value in edge["bindings"].items():
        if re.fullmatch(r"[A-Z][A-Z0-9_]*", value):
            terms[name] = ("slot", value)
        elif re.fullmatch(r"-?(?:\d+(?:\.\d*)?|\.\d+)", value):
            terms[name] = ("num", float(value))
        else:
            return None
    if not any(term[0] == "num" for term in terms.values()):
        return None
    if any(term[0] not in {"slot", "num"} for term in terms.values()):
        return None
    return terms


def _normalize(a: tuple, b: tuple, c: tuple, d: tuple,
               a_to_c: dict[str, str], bindings: dict[str, tuple]) -> tuple:
    if len(a_to_c) > len(A_NAMES):
        raise ValueError("normalization pools are too small")
    a_names = {name: A_NAMES[i] for i, name in enumerate(a_to_c)}
    c_names = {c_name: C_NAMES[i]
               for i, c_name in enumerate(a_to_c.values())}
    b_to_a = {term[1]: a_name for a_name, term in bindings.items()
              if term[0] == "slot"}
    b_names = {name: a_names[b_to_a[name]] for name in template_slots(b)}
    d_names = {name: c_names[a_to_c[a_name]]
               for name, a_name in b_to_a.items()}
    return (replace_slots(a, a_names), replace_slots(b, b_names),
            replace_slots(c, c_names), replace_slots(b, d_names))


def build_quadruples(data_dir: Path, specialization_path: Path,
                     allowed_tokens: set[str] | None = None) -> list[Quadruple]:
    raw = raw_nodes(data_dir)
    parsed, problems = load_nodes(data_dir)
    if problems:
        raise ValueError(f"corpus parse problems: {problems}")
    parsed_by_id = {node.statement_id: node for node in parsed}
    typed = group_by(parsed, "typed")
    edges = json.loads(specialization_path.read_text(encoding="utf-8"))[
        "specialization_edges"
    ]
    authored = {render(parse_template(
        node["structural_signature"]["anonymized_template"])) for node in raw.values()}
    out: list[Quadruple] = []

    for edge in edges:
        a_meta = parsed_by_id.get(edge["general"])
        b_meta = parsed_by_id.get(edge["specific"])
        bindings = _binding_terms(edge)
        if a_meta is None or b_meta is None or bindings is None:
            continue
        a_node, b_node = raw[a_meta.statement_id], raw[b_meta.statement_id]
        a_tree, b_tree = ordered_typed(a_node), ordered_typed(b_node)
        b_slots = template_slots(b_tree)
        b_to_a: dict[str, str] = {}
        ambiguous = False
        for a_name, term in bindings.items():
            if term[0] != "slot":
                continue
            if term[1] in b_to_a and b_to_a[term[1]] != a_name:
                ambiguous = True
            b_to_a[term[1]] = a_name
        if ambiguous or set(b_to_a) != b_slots:
            continue

        for c_meta in typed[a_meta.typed]:
            if (c_meta.statement_id == a_meta.statement_id or
                    c_meta.discipline == a_meta.discipline):
                continue
            c_node = raw[c_meta.statement_id]
            c_tree = ordered_typed(c_node)
            a_to_c = align_twin_slots(
                a_tree, c_tree, slot_classes(a_node), slot_classes(c_node))
            if a_to_c is None or any(name not in a_to_c for name in bindings):
                continue
            d_names = {b_name: a_to_c[a_name]
                       for b_name, a_name in b_to_a.items()}
            d_tree = replace_slots(b_tree, d_names)
            if render(d_tree) in authored:
                continue
            proof = Search(slot_classes(c_node), op_count(c_tree),
                           lambda _head: ()).run(c_tree, d_tree)
            if proof is None:
                continue
            normalized = _normalize(
                a_tree, b_tree, c_tree, d_tree, a_to_c, bindings)
            token_trees = (expression_residual(tree) for tree in normalized)
            tokens = set().union(*(serialize(tree) for tree in token_trees))
            if allowed_tokens is not None and not tokens <= allowed_tokens:
                continue
            out.append(Quadruple(
                a_meta.statement_id, b_meta.statement_id, c_meta.statement_id,
                a_meta.discipline, c_meta.discipline, a_meta.typed,
                (a_tree, b_tree, c_tree, d_tree), normalized))
    return out


def pointer_row(quad: Quadruple, *, residual: bool = False) -> dict:
    a, b, c, d = quad.normalized
    if residual:
        a, b, c, d = map(expression_residual, (a, b, c, d))
    a_t, b_t, c_t, d_t = map(serialize, (a, b, c, d))
    tokens = a_t + [SEP] + b_t + [SEP] + c_t
    b_off = len(a_t) + 1
    c_off = b_off + len(b_t) + 1
    c_slot_pos = {token: c_off + i for i, token in enumerate(c_t)
                  if not token.endswith("(") and token != ")"
                  and not token.startswith("#")}
    actions = [c_slot_pos[token] if token in c_slot_pos else b_off + i
               for i, token in enumerate(d_t)]
    if [tokens[pos] for pos in actions] != d_t:
        raise AssertionError("pointer realization does not reconstruct D")
    return {
        "task": "corpus_analogy", "tokens_struct": tokens,
        "target_positions": actions, "target_tokens": d_t,
        "provenance": {"A": quad.a_id, "B": quad.b_id, "C": quad.c_id},
        "family": quad.family, "discipline": quad.c_discipline,
    }


def edit_distance(left: str, right: str) -> int:
    prior = list(range(len(right) + 1))
    for i, lchar in enumerate(left, 1):
        row = [i]
        for j, rchar in enumerate(right, 1):
            row.append(min(row[-1] + 1, prior[j] + 1,
                           prior[j - 1] + (lchar != rchar)))
        prior = row
    return prior[-1]


def leaves(tree: tuple, kind: str) -> list[tuple]:
    if tree[0] == kind:
        return [tree]
    if tree[0] in {"slot", "num"}:
        return []
    return [leaf for child in tree[2] for leaf in leaves(child, kind)]


def replace_named_slot(tree: tuple, name: str, value: tuple) -> tuple:
    if tree == ("slot", name):
        return value
    if tree[0] in {"slot", "num"}:
        return tree
    return (tree[0], tree[1], tuple(
        replace_named_slot(child, name, value) for child in tree[2]))


def blind_number_transfer(quad: Quadruple) -> tuple | None:
    """Move B's one new number into C's last slot, without corpus metadata."""
    a, b, c, _d = quad.actual
    a_nums = [leaf[1] for leaf in leaves(a, "num")]
    new_nums = [leaf for leaf in leaves(b, "num") if leaf[1] not in a_nums]
    c_slots = [leaf[1] for leaf in leaves(c, "slot")]
    if len(new_nums) != 1 or not c_slots:
        return None
    return replace_named_slot(c, c_slots[-1], new_nums[0])


def literal_vocabulary_coverage(quads: list[Quadruple],
                                vocabulary: set[str]) -> dict:
    literal = set().union(*(serialize(tree) for quad in quads
                            for tree in quad.actual[:3]))
    missing = sorted(literal - vocabulary)
    return {
        "status": "AVAILABLE" if not missing else "REFUSED_FIXED_CHECKPOINT_VOCAB",
        "missing_count": len(missing),
        "missing_sample": missing[:12],
    }


def evaluate(checkpoint: Path | None, data_dir: Path,
             specialization_path: Path) -> dict:
    ckpt = None
    allowed = None
    if checkpoint is not None:
        ckpt = torch.load(checkpoint, map_location="cpu", weights_only=False)
        allowed = set(ckpt["vocab"])
    quads = build_quadruples(data_dir, specialization_path, allowed)
    if not quads:
        raise ValueError("no admissible corpus-grounded quadruples")
    rows = [pointer_row(q, residual=ckpt is not None) for q in quads]
    actual_targets = [render(q.actual[3]) for q in quads]
    authored = [render(parse_template(
        node["structural_signature"]["anonymized_template"]))
        for node in raw_nodes(data_dir).values()]
    nearest = [min(authored, key=lambda candidate: edit_distance(target, candidate))
               for target in actual_targets]
    nearest_similarity = [
        1.0 - edit_distance(target, candidate) /
        max(len(target), len(candidate), 1)
        for target, candidate in zip(actual_targets, nearest)
    ]
    blind = [blind_number_transfer(quad) for quad in quads]
    blind_exact = sum(
        candidate is not None and render(candidate) == target
        for candidate, target in zip(blind, actual_targets)
    ) / len(quads)
    distinct_targets = len(set(actual_targets))
    result = {
        "task": "corpus_grounded_analogy",
        "quadruples": len(quads),
        "families": len({q.family for q in quads}),
        "source_disciplines": len({q.a_discipline for q in quads}),
        "target_disciplines": len({q.c_discipline for q in quads}),
        "novel_target_rows": sum(
            target not in authored for target in actual_targets),
        "distinct_novel_targets": distinct_targets,
        "symbolic_exact": 1.0,
        "capability_blind": {
            "last_slot_number_transfer_exact": blind_exact,
        },
        "novelty_sanity_controls": {
            "copy_c_exact": sum(render(q.actual[2]) == render(q.actual[3])
                                for q in quads) / len(quads),
            "nearest_authored_exact": sum(
                target == candidate
                for target, candidate in zip(actual_targets, nearest)) / len(quads),
            "nearest_authored_mean_similarity": (
                sum(nearest_similarity) / len(quads)),
        },
        "split_coverage": {
            "family": "REFUSED_ONE_ELIGIBLE_FAMILY",
            "discipline": {
                "mode": "all corpus disciplines are OOD to synthetic training",
                "count": len({q.c_discipline for q in quads}),
            },
            "literal_vocabulary": (
                literal_vocabulary_coverage(quads, allowed)
                if allowed is not None else "NO_CHECKPOINT"),
        },
        "example": {
            "A": quads[0].a_id, "B": quads[0].b_id,
            "C": quads[0].c_id, "D": actual_targets[0],
        },
    }
    if ckpt is not None:
        vocab = Vocab(set(ckpt["vocab"]))
        if vocab.itos != ckpt["vocab"]:
            raise ValueError("checkpoint vocabulary order cannot be reconstructed")
        cfg = ckpt["config"]
        model = AnalogyPointer(len(vocab), cfg["d_model"],
                               max_tgt=cfg["max_tgt"],
                               level_code="recurrent")
        model.load_state_dict(ckpt["state_dict"])
        loader = DataLoader(
            AnalogyDataset(rows, vocab, cfg["max_len"], cfg["max_tgt"]),
            batch_size=64, collate_fn=collate)
        result["model_rhs_exact"] = greedy_exact(
            model, loader, "cpu", cfg["max_tgt"], vocab.itos)
        result["model_scope"] = "RHS residual; equality shell is symbolic"
        result["checkpoint"] = checkpoint.name
        result["checkpoint_sha256"] = hashlib.sha256(
            checkpoint.read_bytes()).hexdigest()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--specializations", type=Path,
                        default=ROOT / "reports" / "specializations.json")
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--out", type=Path,
                        default=ROOT / "experiments" / "results" /
                        "corpus_analogy.json")
    args = parser.parse_args()
    result = evaluate(args.checkpoint, args.data_dir, args.specializations)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
