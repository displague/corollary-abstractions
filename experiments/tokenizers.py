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
    t1 = tree_from_json(example["tree1"])
    t2 = tree_from_json(example["tree2"])
    return _struct_serialize(t1, {}) + [SEP] + _struct_serialize(t2, {})


def canon_tokens(example: dict) -> list[str]:
    t1 = canonicalize(tree_from_json(example["tree1"]))
    t2 = canonicalize(tree_from_json(example["tree2"]))
    return _struct_serialize(t1, {}) + [SEP] + _struct_serialize(t2, {})


SERIALIZERS = {"char": char_tokens, "struct": struct_tokens, "canon": canon_tokens}


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
