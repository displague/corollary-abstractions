"""solvex-v2: solve-for-X against a distractor KB — content load-bearing.

v1's flaw (caught by user audit): with one statement, the answer span is
computable from structure alone. v2 presents K statements sharing the same
verb and near-identical structure; exactly ONE unifies with the question.
Selecting it requires matching the question's fixed-role NP (language B
words) against each statement's NP (language A words) — the cross-language
dictionary is now on the critical path, so held-out (verb, answer-noun)
combos genuinely stress recombination.

The smoke audit enforces the new design standard: a structure-only rule
must score ~1/K here, not 1.0.
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
    LEX_A, LEX_B, NOUNS, SEP, VERBS, canon_tokens_lang, gen_np, mutate_np,
    render, struct_tokens_lang,
)
from solvex import np_noun  # noqa: E402


def make_example(rng: random.Random, depth: int, n_stmts: int,
                 combos: set, want_heldout: bool) -> dict | None:
    verb = ("slot", f"v{rng.randrange(len(VERBS))}")
    agent, patient = gen_np(rng, depth), gen_np(rng, depth)
    wh_agent = rng.random() < 0.5
    answer_np = agent if wh_agent else patient
    q_fixed = patient if wh_agent else agent
    combo = (verb[1], np_noun(answer_np))
    if (combo in combos) != want_heldout:
        return None

    correct = ("call", "STMT", (("call", "EVT", (verb, agent, patient)),))

    # distractors: same verb, same structure family, DIFFERENT fixed-role NP
    distractors = []
    tries = 0
    while len(distractors) < n_stmts - 1 and tries < 40:
        tries += 1
        alt_fixed = mutate_np(q_fixed, rng)
        if alt_fixed is None or canonicalize(alt_fixed) == canonicalize(q_fixed):
            continue
        alt_other = gen_np(rng, depth)
        if wh_agent:
            d = ("call", "STMT", (("call", "EVT", (verb, alt_other, alt_fixed)),))
        else:
            d = ("call", "STMT", (("call", "EVT", (verb, alt_fixed, alt_other)),))
        distractors.append(d)
    if len(distractors) < n_stmts - 1:
        return None

    stmts = distractors + [correct]
    rng.shuffle(stmts)
    correct_idx = stmts.index(correct)

    q_agent = ("slot", "WH") if wh_agent else q_fixed
    q_patient = q_fixed if wh_agent else ("slot", "WH")
    ques = ("call", "ASK", (("call", "EVT", (verb, q_agent, q_patient)),))

    ques_toks = struct_tokens_lang(ques, LEX_B)
    stmt_tok_lists = [struct_tokens_lang(s, LEX_A) for s in stmts]

    # span of the WH-role NP inside the correct statement's block
    agent_len = len(struct_tokens_lang(stmts[correct_idx][2][0][2][1], LEX_A))
    if wh_agent:
        lo, hi = 3, 3 + agent_len - 1
    else:
        lo = 3 + agent_len
        patient_len = len(struct_tokens_lang(stmts[correct_idx][2][0][2][2], LEX_A))
        hi = lo + patient_len - 1
    block_off = len(ques_toks) + 1 + sum(len(t) for t in stmt_tok_lists[:correct_idx])
    tokens = ques_toks + [SEP] + [t for lst in stmt_tok_lists for t in lst]
    return {
        "task": "solvex2",
        "expr1": render(ques, "B", rng),
        "expr2": " | ".join(render(s, "A", rng) for s in stmts),
        "tokens_struct": tokens,
        "ans_start": block_off + lo,
        "ans_end": block_off + hi,
        "answer": " ".join(stmt_tok_lists[correct_idx][lo:hi + 1]),
        "answer_canon": canon_tokens_lang(answer_np),
        "correct_idx": correct_idx,
        "n_stmts": n_stmts,
        "combo": list(combo),
        "depth": depth,
        "label": 1,
    }


def build_split(n: int, rng: random.Random, depths: list[int],
                combos: set, want_heldout: bool, n_stmts: int) -> list[dict]:
    out = []
    attempts = 0
    while len(out) < n and attempts < n * 120:
        attempts += 1
        ex = make_example(rng, rng.choice(depths), n_stmts, combos, want_heldout)
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
    ap.add_argument("--n-stmts", type=int, default=3)
    ap.add_argument("--heldout-frac", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=47)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    all_combos = [(f"v{v}", f"n{n}") for v in range(len(VERBS))
                  for n in range(len(NOUNS))]
    rng.shuffle(all_combos)
    heldout = set(all_combos[:int(len(all_combos) * args.heldout_frac)])
    print(f"combos: {len(all_combos)}, held out: {len(heldout)}; "
          f"K={args.n_stmts} statements per example")

    splits = {
        "train": build_split(args.train, rng, [1, 1, 2], heldout, False, args.n_stmts),
        "val": build_split(args.val, rng, [1, 1, 2], heldout, False, args.n_stmts),
        "test": build_split(args.test, rng, [1, 1, 2], heldout, True, args.n_stmts),
        "ood": build_split(args.ood, rng, [3, 4], heldout, True, args.n_stmts),
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for split, rows in splits.items():
        path = args.out_dir / f"solvex2_{split}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        print(f"solvex2/{split}: {len(rows)} -> {path}")


if __name__ == "__main__":
    main()
