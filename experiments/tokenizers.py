"""Three encodings of expression pairs at increasing symbolic-front-end depth.

- char: raw ASCII characters of the surface strings (baseline LLM-style)
- struct: parse-tree tokens in surface order (lexing+parsing done by front-end,
  commutativity/sugar NOT normalized -- the model must learn algebra)
- canon: fully canonicalized concept tokens (front-end does commutative
  sort, sugar removal, slot abstraction; model learns what remains)

All three share one vocabulary object interface: encode(example) -> list[int].
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from match_signatures import canonicalize  # noqa: E402

PAD, CLS, SEP = "<pad>", "<cls>", "<sep>"


def tree_from_json(t) -> tuple:
    """JSONL round-trips tuples as lists; restore tuples."""
    if isinstance(t, list):
        if t[0] in {"num", "slot"}:
            return (t[0], t[1])
        return (t[0], t[1], tuple(tree_from_json(a) for a in t[2]))
    return t


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------


def char_tokens(example: dict) -> list[str]:
    return list(example["expr1"]) + [SEP] + list(example["expr2"])


def precomputed(example: dict, arm: str) -> list[str] | None:
    """Language-world examples carry pregenerated token streams (their
    serialization needs per-language lexica unavailable here)."""
    return example.get(f"tokens_{arm}")


def _struct_serialize(t: tuple, slot_idx: dict[str, int]) -> list[str]:
    kind = t[0]
    if kind == "num":
        return [f"#{t[1]:g}"]
    if kind == "slot":
        idx = slot_idx.setdefault(t[1], len(slot_idx))
        return [f"?{idx}"]
    head = t[1]
    out = [f"{head}(" if kind == "op" else f"{head}⟨"]
    for a in t[2]:
        out.extend(_struct_serialize(a, slot_idx))
    out.append(")")
    return out


def struct_tokens(example: dict) -> list[str]:
    pre = precomputed(example, "struct")
    if pre is not None:
        return pre
    t1 = tree_from_json(example["tree1"])
    t2 = tree_from_json(example["tree2"])
    return _struct_serialize(t1, {}) + [SEP] + _struct_serialize(t2, {})


def canon_tokens(example: dict) -> list[str]:
    pre = precomputed(example, "canon")
    if pre is not None:
        return pre
    t1 = canonicalize(tree_from_json(example["tree1"]))
    t2 = canonicalize(tree_from_json(example["tree2"]))
    return _struct_serialize(t1, {}) + [SEP] + _struct_serialize(t2, {})


def _shape_unify(a: tuple, b: tuple) -> bool:
    """Structural unification with leaf identity erased: WH matches any
    subtree; any leaf matches any leaf; commutative + args match as a
    multiset (small backtracking). Computable WITHOUT the lexicon — exactly
    the symbolic front-end's honest contribution on the syn task."""
    if b == ("slot", "WH") or a == ("slot", "WH"):
        return True
    a_leaf = a[0] in {"slot", "num"}
    b_leaf = b[0] in {"slot", "num"}
    if a_leaf or b_leaf:
        return a_leaf and b_leaf
    if a[0] != b[0] or a[1] != b[1]:
        return False
    if len(a[2]) != len(b[2]):
        return False
    if a[0] == "op" and a[1] == "+":
        remaining = list(b[2])

        def assign(i: int) -> bool:
            if i == len(a[2]):
                return True
            for j, cand in enumerate(remaining):
                if cand is not None and _shape_unify(a[2][i], cand):
                    remaining[j] = None
                    if assign(i + 1):
                        return True
                    remaining[j] = cand
            return False

        return assign(0)
    return all(_shape_unify(x, y) for x, y in zip(a[2], b[2]))


def hybrid_tokens(example: dict) -> list[str]:
    """Symbolic feature tokens + the struct stream. Features: does the
    statement structurally unify with the question pattern (lexicon-blind),
    and which role the unknown occupies."""
    t1 = tree_from_json(example["tree1"])
    t2 = tree_from_json(example["tree2"])
    evt1, evt2 = t1[2][0], t2[2][0]
    unify_bit = "FSHAPE1" if _shape_unify(evt1, evt2) else "FSHAPE0"
    wh_role = "FWHA" if evt2[2][1] == ("slot", "WH") else "FWHP"
    base = precomputed(example, "struct") or struct_tokens(example)
    return [unify_bit, wh_role] + base


SERIALIZERS = {"char": char_tokens, "struct": struct_tokens,
               "canon": canon_tokens, "hybrid": hybrid_tokens}


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------


class Vocab:
    def __init__(self, tokens: set[str]):
        self.itos = [PAD, CLS, SEP] + sorted(tokens - {PAD, CLS, SEP})
        self.stoi = {t: i for i, t in enumerate(self.itos)}

    def __len__(self) -> int:
        return len(self.itos)

    def encode(self, tokens: list[str]) -> list[int]:
        unk = self.stoi.get("?9", 3)
        return [self.stoi[CLS]] + [self.stoi.get(t, unk) for t in tokens]


def build_vocab(examples: list[dict], arm: str) -> Vocab:
    serialize = SERIALIZERS[arm]
    seen: set[str] = set()
    for ex in examples:
        seen.update(serialize(ex))
    return Vocab(seen)
