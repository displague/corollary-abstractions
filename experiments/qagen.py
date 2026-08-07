"""QA-as-unification task (qa): does a Language-A statement answer a
Language-B question?

A WH-question is an equation: EVT(verb, WH, patient) with WH the unknown.
A statement answers it iff the statement unifies with the question pattern --
all fixed parts (verb, the non-WH role, its full modifier structure) equal
after canonicalization; WH binds to anything. No closed-form string equality
exists between the two sides even in the canon arm, so this measures the
graded residual that weights are actually for (per ANALYSIS.md).

Negatives are near-misses: wrong verb, wrong fixed-role noun, one adjective
changed/dropped on the fixed role, roles crossed (statement's agent matches
but question asks about patient position).
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from match_signatures import canonicalize  # noqa: E402

from langgen import (  # noqa: E402
    LEX_A, LEX_B, SEP, VERBS, gen_np, mutate_np, render,
    struct_tokens_lang, canon_tokens_lang,
)


def unifies(stmt: tuple, ques: tuple) -> bool:
    """stmt: STMT(EVT(v, agent, patient)); ques: ASK(EVT(v', a', p')) with
    exactly one of a'/p' == WH. Unification = all fixed parts canonically
    equal; WH matches anything."""
    sv, sa, sp = stmt[2][0][2]
    qv, qa, qp = ques[2][0][2]
    if canonicalize(sv) != canonicalize(qv):
        return False
    if qa == ("slot", "WH"):
        return canonicalize(sp) == canonicalize(qp)
    return canonicalize(sa) == canonicalize(qa)


def make_pair(rng: random.Random, depth: int, positive: bool) -> dict | None:
    verb = ("slot", f"v{rng.randrange(len(VERBS))}")
    agent, patient = gen_np(rng, depth), gen_np(rng, depth)
    stmt = ("call", "STMT", (("call", "EVT", (verb, agent, patient)),))

    wh_agent = rng.random() < 0.5
    q_fixed = patient if wh_agent else agent

    if not positive:
        r = rng.random()
        if r < 0.3:  # wrong verb
            new_v = ("slot", f"v{rng.randrange(len(VERBS))}")
            if new_v == verb:
                return None
            verb_q, q_fixed_q = new_v, q_fixed
        elif r < 0.65:  # fixed role mutated (noun/adjective near-miss)
            mutated = mutate_np(q_fixed, rng)
            if mutated is None:
                return None
            verb_q, q_fixed_q = verb, mutated
        else:  # roles crossed: ask about the role the statement fills differently
            other = agent if wh_agent else patient
            if canonicalize(other) == canonicalize(q_fixed):
                return None
            verb_q, q_fixed_q = verb, other
        q_fixed = q_fixed_q
        verb_for_q = verb_q
    else:
        verb_for_q = verb

    q_agent = ("slot", "WH") if wh_agent else q_fixed
    q_patient = q_fixed if wh_agent else ("slot", "WH")
    ques = ("call", "ASK", (("call", "EVT", (verb_for_q, q_agent, q_patient)),))

    label = int(unifies(stmt, ques))
    if label != int(positive):
        return None
    return {
        "task": "qa",
        "expr1": render(stmt, "A", rng),
        "expr2": render(ques, "B", rng),
        "tree1": stmt,
        "tree2": ques,
        "label": label,
        "depth": depth,
        "tokens_struct": (struct_tokens_lang(stmt, LEX_A) + [SEP]
                          + struct_tokens_lang(ques, LEX_B)),
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
    ap.add_argument("--seed", type=int, default=23)
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
        path = args.out_dir / f"qa_{split}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        n_pos = sum(r["label"] for r in rows)
        print(f"qa/{split}: {len(rows)} ({n_pos} pos) -> {path}")


if __name__ == "__main__":
    main()
