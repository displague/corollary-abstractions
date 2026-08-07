"""Graded-residual task (syn): QA-as-unification with a synonymous lexicon.

Language B gives every concept 2-3 interchangeable surface words
("thesaurical twins"), sampled independently per sentence. Surface-token
unification is now undecidable without knowing the synonym clusters, and the
clusters are nowhere in the input — the model must induce the thesaurus from
co-occurrence. That induction is the graded residual: no closed form exists
over the tokens the struct arm sees.

Arms reuse the standard three with shifted meaning:
- char: raw text, synonymous B lexicon (parsing + thesaurus induction)
- struct: parse trees, sampled B surface words (thesaurus induction only)
- canon: concept ids = gold thesaurus applied (the symbolic ceiling — what a
  learned lexicon would recover at 100%)

Labels remain exact (computed on trees), so accuracy gaps between struct and
canon measure precisely how much of the thesaurus the model learned.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from langgen import (  # noqa: E402
    LEX_A, SEP, SYLL, VERBS, gen_np, mutate_np, render,
    struct_tokens_lang, canon_tokens_lang,
)
from qagen import unifies  # noqa: E402


def synonyms_b(concept: str, k: int) -> list[str]:
    """k deterministic pseudo-words per concept, disjoint across concepts."""
    out = []
    for j in range(k):
        h = j * 7919
        for ch in concept + LEX_A[concept]:
            h = (h * 31 + ord(ch)) % (1 << 20)
        out.append(SYLL[h % 16] + SYLL[(h // 16) % 16] + SYLL[(h // 256) % 16]
                   + str(j))
    return out


SYNS_B = {c: synonyms_b(c, 3 if c[0] in "nav" else 2) for c in LEX_A}
SYNS_B["WH"] = ["wo"]


def sample_lex_b(rng: random.Random) -> dict[str, str]:
    return {c: rng.choice(ws) for c, ws in SYNS_B.items()}


def make_pair(rng: random.Random, depth: int, positive: bool) -> dict | None:
    verb = ("slot", f"v{rng.randrange(len(VERBS))}")
    agent, patient = gen_np(rng, depth), gen_np(rng, depth)
    stmt = ("call", "STMT", (("call", "EVT", (verb, agent, patient)),))

    wh_agent = rng.random() < 0.5
    q_fixed = patient if wh_agent else agent
    verb_for_q = verb

    if not positive:
        r = rng.random()
        if r < 0.3:
            new_v = ("slot", f"v{rng.randrange(len(VERBS))}")
            if new_v == verb:
                return None
            verb_for_q = new_v
        elif r < 0.65:
            mutated = mutate_np(q_fixed, rng)
            if mutated is None:
                return None
            q_fixed = mutated
        else:
            other = agent if wh_agent else patient
            if other == q_fixed:
                return None
            q_fixed = other

    q_agent = ("slot", "WH") if wh_agent else q_fixed
    q_patient = q_fixed if wh_agent else ("slot", "WH")
    ques = ("call", "ASK", (("call", "EVT", (verb_for_q, q_agent, q_patient)),))

    label = int(unifies(stmt, ques))
    if label != int(positive):
        return None
    lex_b = sample_lex_b(rng)
    return {
        "task": "syn",
        "expr1": render(stmt, "A", rng),
        "expr2": render(ques, "B", rng, lex=lex_b),
        "tree1": stmt,
        "tree2": ques,
        "label": label,
        "depth": depth,
        "tokens_struct": (struct_tokens_lang(stmt, LEX_A) + [SEP]
                          + struct_tokens_lang(ques, lex_b)),
        "tokens_canon": (canon_tokens_lang(stmt) + [SEP]
                         + canon_tokens_lang(ques)),
    }


def build_split(n: int, rng: random.Random, depths: list[int]) -> list[dict]:
    out: list[dict] = []
    n_pos = 0
    attempts = 0
    want_pos = n // 2
    while len(out) < n and attempts < n * 50:
        attempts += 1
        n_neg = len(out) - n_pos
        if n_pos >= want_pos:
            positive = False
        elif n_neg >= n - want_pos:
            positive = True
        else:
            positive = rng.random() < 0.5
        ex = make_pair(rng, rng.choice(depths), positive)
        if ex is None:
            continue
        out.append(ex)
        n_pos += ex["label"]
    rng.shuffle(out)
    return out


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("data"))
    ap.add_argument("--train", type=int, default=50000)
    ap.add_argument("--val", type=int, default=5000)
    ap.add_argument("--test", type=int, default=5000)
    ap.add_argument("--ood", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=31)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    splits = {
        "train": build_split(args.train, rng, [1, 1, 2]),
        "val": build_split(args.val, rng, [1, 1, 2]),
        "test": build_split(args.test, rng, [1, 1, 2]),
        "ood": build_split(args.ood, rng, [3, 4]),
    }
    for split, rows in splits.items():
        path = args.out_dir / f"syn_{split}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        n_pos = sum(r["label"] for r in rows)
        print(f"syn/{split}: {len(rows)} ({n_pos} pos) -> {path}")


if __name__ == "__main__":
    main()
