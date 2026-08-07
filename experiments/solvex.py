"""Solve-for-X: generative QA as span extraction (emergence battery, task 1).

A WH-question is an equation; answering means producing the binding. Here the
binding is a pointer: the answer NP is a contiguous span of the statement's
token stream, so the model answers by emitting (start, end) — the
pointer-into-extrinsic-content mechanism, measured.

Splits are SYSTEMATIC RECOMBINATION, not random: 15% of (verb, answer-noun)
pairs are held out entirely from training; test uses only held-out combos
(seen parts, unseen combination — the signature of compositional
generalization); ood additionally deepens modifier recursion.

Only positive (answerable) pairs exist here; the label is the span.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from langgen import (  # noqa: E402
    LEX_A, LEX_B, NOUNS, SEP, VERBS, gen_np, render, struct_tokens_lang,
)


def np_noun(np: tuple) -> str:
    return np[1] if np[0] == "slot" else np[2][0][1]


def make_example(rng: random.Random, depth: int,
                 combos: set[tuple[str, str]], want_heldout: bool) -> dict | None:
    verb = ("slot", f"v{rng.randrange(len(VERBS))}")
    agent, patient = gen_np(rng, depth), gen_np(rng, depth)
    wh_agent = rng.random() < 0.5
    answer_np = agent if wh_agent else patient
    combo = (verb[1], np_noun(answer_np))
    if (combo in combos) != want_heldout:
        return None

    stmt = ("call", "STMT", (("call", "EVT", (verb, agent, patient)),))
    q_fixed = patient if wh_agent else agent
    q_agent = ("slot", "WH") if wh_agent else q_fixed
    q_patient = q_fixed if wh_agent else ("slot", "WH")
    ques = ("call", "ASK", (("call", "EVT", (verb, q_agent, q_patient)),))

    ques_toks = struct_tokens_lang(ques, LEX_B)
    stmt_toks = struct_tokens_lang(stmt, LEX_A)
    # statement serialization: ["STMT(", "EVT(", verb, agent..., patient..., ")", ")"]
    agent_len = len(struct_tokens_lang(agent, LEX_A))
    if wh_agent:
        span_lo, span_hi = 3, 3 + agent_len - 1
    else:
        span_lo = 3 + agent_len
        span_hi = span_lo + len(struct_tokens_lang(patient, LEX_A)) - 1
    tokens = ques_toks + [SEP] + stmt_toks
    offset = len(ques_toks) + 1
    return {
        "task": "solvex",
        "expr1": render(ques, "B", rng),
        "expr2": render(stmt, "A", rng),
        "tree1": ques,
        "tree2": stmt,
        "tokens_struct": tokens,
        "ans_start": offset + span_lo,
        "ans_end": offset + span_hi,
        "answer": " ".join(stmt_toks[span_lo:span_hi + 1]),
        "combo": list(combo),
        "depth": depth,
        "label": 1,
    }


def build_split(n: int, rng: random.Random, depths: list[int],
                combos: set, want_heldout: bool) -> list[dict]:
    out = []
    attempts = 0
    while len(out) < n and attempts < n * 80:
        attempts += 1
        ex = make_example(rng, rng.choice(depths), combos, want_heldout)
        if ex is not None:
            out.append(ex)
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
    ap.add_argument("--heldout-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=41)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    all_combos = [(f"v{v}", f"n{n}") for v in range(len(VERBS))
                  for n in range(len(NOUNS))]
    rng.shuffle(all_combos)
    n_held = int(len(all_combos) * args.heldout_frac)
    heldout = set(all_combos[:n_held])
    print(f"combos: {len(all_combos)} total, {n_held} held out of training")

    splits = {
        "train": build_split(args.train, rng, [1, 1, 2], heldout, False),
        "val": build_split(args.val, rng, [1, 1, 2], heldout, False),
        "test": build_split(args.test, rng, [1, 1, 2], heldout, True),
        "ood": build_split(args.ood, rng, [3, 4], heldout, True),
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for split, rows in splits.items():
        path = args.out_dir / f"solvex_{split}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        print(f"solvex/{split}: {len(rows)} -> {path}")


if __name__ == "__main__":
    main()
