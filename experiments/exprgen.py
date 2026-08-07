"""Synthetic expression world for concept-token experiments.

Generates random expression trees in the same tuple AST format as
scripts/match_signatures.py, renders them to disguised ASCII surface forms,
applies semantics-preserving rewrites, and verifies labels by random numeric
evaluation.

AST nodes:
    ("num", float)
    ("slot", name)
    ("op", opname, (args...))     opname in {+, *, ^, neg, inv}
    ("call", fname, (args...))
"""

from __future__ import annotations

import json
import math
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from match_signatures import canonicalize  # noqa: E402

CALLS_1 = ["SQRT", "ABS", "LOG", "EXP"]

NAME_POOLS = [
    ["AREA", "VOLUME", "FORCE", "MASS", "ENERGY", "RADIUS", "HEIGHT", "BASE",
     "WIDTH", "LENGTH", "SPEED", "TIME", "CHARGE", "FLUX", "PRESSURE"],
    ["alpha", "beta", "gamma", "delta", "sigma", "theta", "lambda", "omega",
     "phi", "kappa", "rho", "tau"],
    ["x", "y", "z", "u", "v", "w", "p", "q", "r", "s", "a", "b", "c", "m", "n"],
    ["X_1", "X_2", "Y_i", "Z_n", "W_k", "V_0", "U_t", "T_j"],
]


# ---------------------------------------------------------------------------
# Random tree generation
# ---------------------------------------------------------------------------


def random_tree(rng: random.Random, depth: int, n_slots: int) -> tuple:
    """Random expression tree using slot ids s0..s{n_slots-1} (with reuse)."""
    if depth <= 0 or (depth <= 1 and rng.random() < 0.35):
        if rng.random() < 0.12:
            return ("num", float(rng.choice([2, 3, 4, 5])))
        return ("slot", f"s{rng.randrange(n_slots)}")
    kind = rng.random()
    if kind < 0.34:
        n_args = rng.choice([2, 2, 3])
        return ("op", "+", tuple(random_tree(rng, depth - 1, n_slots) for _ in range(n_args)))
    if kind < 0.68:
        n_args = rng.choice([2, 2, 3])
        return ("op", "*", tuple(random_tree(rng, depth - 1, n_slots) for _ in range(n_args)))
    if kind < 0.78:
        base = random_tree(rng, depth - 1, n_slots)
        return ("op", "^", (base, ("num", float(rng.choice([2, 3])))))
    if kind < 0.86:
        return ("op", "neg", (random_tree(rng, depth - 1, n_slots),))
    if kind < 0.94:
        return ("op", "inv", (random_tree(rng, depth - 1, n_slots),))
    return ("call", rng.choice(CALLS_1), (random_tree(rng, depth - 1, n_slots),))


def tree_slots(t: tuple) -> set[str]:
    if t[0] == "slot":
        return {t[1]}
    if t[0] == "num":
        return set()
    out: set[str] = set()
    for a in t[2]:
        out |= tree_slots(a)
    return out


def tree_size(t: tuple) -> int:
    if t[0] in {"slot", "num"}:
        return 1
    return 1 + sum(tree_size(a) for a in t[2])


# ---------------------------------------------------------------------------
# Surface rendering (the "disguise"): random slot names, commutative order,
# sugar for neg/inv, redundant parentheses.
# ---------------------------------------------------------------------------


def random_skin(rng: random.Random, slots: set[str]) -> dict[str, str]:
    pool = list(rng.choice(NAME_POOLS))
    rng.shuffle(pool)
    while len(pool) < len(slots):
        pool += [f"{p}{rng.randrange(10)}" for p in pool]
    return {s: pool[i] for i, s in enumerate(sorted(slots))}


def render(t: tuple, skin: dict[str, str], rng: random.Random) -> str:
    """Render tree to ASCII with randomized presentation choices."""

    def paren(s: str) -> str:
        return f"({s})"

    def maybe_paren(s: str, prob: float = 0.15) -> str:
        return paren(s) if rng.random() < prob else s

    def rec(n: tuple, parent: str) -> str:
        kind = n[0]
        if kind == "num":
            return f"{n[1]:g}"
        if kind == "slot":
            return skin[n[1]]
        if kind == "call":
            return f"{n[1]}({rec(n[2][0], 'call')})"
        opname = n[1]
        if opname == "neg":
            inner = rec(n[2][0], "neg")
            if n[2][0][0] in {"op", "call"} and n[2][0][1] not in {"neg", "inv"}:
                inner = paren(inner)
            return f"-{inner}"
        if opname == "inv":
            inner = rec(n[2][0], "inv")
            if n[2][0][0] == "op":
                inner = paren(inner)
            return f"1/{inner}"
        if opname == "^":
            base = rec(n[2][0], "^")
            if n[2][0][0] == "op":
                base = paren(base)
            return f"{base}^{rec(n[2][1], '^')}"
        args = list(n[2])
        rng.shuffle(args)  # commutative presentation order
        if opname == "+":
            parts: list[str] = []
            for i, a in enumerate(args):
                if a[0] == "op" and a[1] == "neg" and i > 0 and rng.random() < 0.7:
                    parts.append(f"- {rec(a[2][0], '+')}"
                                 if a[2][0][0] != "op" or a[2][0][1] in {"^", "neg", "inv"}
                                 else f"- {paren(rec(a[2][0], '+'))}")
                else:
                    rendered = rec(a, "+")
                    parts.append(rendered if i == 0 else f"+ {rendered}")
            s = " ".join(parts)
            return maybe_paren(s) if parent in {"*", "^", "call"} else (
                paren(s) if parent in {"*", "^"} else s)
        if opname == "*":
            parts = []
            for i, a in enumerate(args):
                if a[0] == "op" and a[1] == "inv" and i > 0 and rng.random() < 0.7:
                    inner = rec(a[2][0], "*")
                    if a[2][0][0] == "op":
                        inner = paren(inner)
                    parts.append(f"/ {inner}")
                else:
                    rendered = rec(a, "*")
                    if a[0] == "op" and a[1] in {"+"}:
                        rendered = paren(rendered)
                    parts.append(rendered if i == 0 else f"* {rendered}")
            s = " ".join(parts)
            return paren(s) if parent == "^" else maybe_paren(s, 0.1)
        raise ValueError(opname)

    return rec(t, "top")


# ---------------------------------------------------------------------------
# Numeric evaluation (label verification)
# ---------------------------------------------------------------------------


def evaluate(t: tuple, env: dict[str, float]) -> float:
    kind = t[0]
    if kind == "num":
        return t[1]
    if kind == "slot":
        return env[t[1]]
    if kind == "call":
        x = evaluate(t[2][0], env)
        f = t[1]
        if f == "SQRT":
            return math.sqrt(abs(x))
        if f == "ABS":
            return abs(x)
        if f == "LOG":
            return math.log(abs(x) + 1e-9)
        if f == "EXP":
            return math.exp(max(min(x, 30.0), -30.0))
        raise ValueError(f)
    opname = t[1]
    args = [evaluate(a, env) for a in t[2]]
    if opname == "+":
        return sum(args)
    if opname == "*":
        out = 1.0
        for a in args:
            out *= a
        return out
    if opname == "^":
        return math.copysign(abs(args[0]) ** args[1], args[0] if args[1] % 2 else 1.0)
    if opname == "neg":
        return -args[0]
    if opname == "inv":
        return args[0] / (args[0] * args[0] + 1e-12) if abs(args[0]) < 1e-6 else 1.0 / args[0]
    raise ValueError(opname)


def numerically_equal(t1: tuple, t2: tuple, rng: random.Random, trials: int = 12) -> bool:
    slots = tree_slots(t1) | tree_slots(t2)
    agree = 0
    for _ in range(trials):
        env = {s: rng.uniform(0.2, 3.0) * rng.choice([1.0, -1.0]) for s in slots}
        try:
            v1, v2 = evaluate(t1, env), evaluate(t2, env)
        except (OverflowError, ValueError):
            continue
        if not (math.isfinite(v1) and math.isfinite(v2)):
            continue
        scale = max(abs(v1), abs(v2), 1.0)
        if abs(v1 - v2) / scale < 1e-6:
            agree += 1
        else:
            return False
    return agree >= trials // 2


# ---------------------------------------------------------------------------
# Semantics-preserving rewrites (for the equivalence task)
# ---------------------------------------------------------------------------


def all_subtree_paths(t: tuple, path: tuple = ()) -> list[tuple]:
    paths = [path]
    if t[0] in {"op", "call"}:
        for i, a in enumerate(t[2]):
            paths.extend(all_subtree_paths(a, path + (i,)))
    return paths


def get_at(t: tuple, path: tuple) -> tuple:
    for i in path:
        t = t[2][i]
    return t


def replace_at(t: tuple, path: tuple, new: tuple) -> tuple:
    if not path:
        return new
    args = list(t[2])
    args[path[0]] = replace_at(args[path[0]], path[1:], new)
    return (t[0], t[1], tuple(args))


def rewrite_once(t: tuple, rng: random.Random) -> tuple | None:
    """Apply one random semantics-preserving rewrite somewhere in the tree."""
    paths = all_subtree_paths(t)
    rng.shuffle(paths)
    for path in paths:
        sub = get_at(t, path)
        candidates = []
        # distribute: a*(b+c) -> a*b + a*c
        if sub[0] == "op" and sub[1] == "*":
            plus_positions = [i for i, a in enumerate(sub[2]) if a[0] == "op" and a[1] == "+"]
            if plus_positions:
                i = rng.choice(plus_positions)
                plus = sub[2][i]
                rest = sub[2][:i] + sub[2][i + 1:]
                terms = tuple(
                    ("op", "*", rest + (term,)) if len(rest) else term
                    for term in plus[2]
                )
                candidates.append(("op", "+", terms))
        # identity padding: x -> x*1, x -> x+0 (kept rare), x -> --x
        if rng.random() < 0.3:
            candidates.append(("op", "*", (sub, ("num", 1.0))))
        if rng.random() < 0.2:
            candidates.append(("op", "+", (sub, ("num", 0.0))))
        if rng.random() < 0.2:
            candidates.append(("op", "neg", (("op", "neg", (sub,)),)))
        # power expansion: x^2 -> x*x, x^3 -> x*x*x
        if sub[0] == "op" and sub[1] == "^" and sub[2][1][0] == "num":
            k = int(sub[2][1][1])
            if k in (2, 3):
                candidates.append(("op", "*", tuple(sub[2][0] for _ in range(k))))
        # factor-out reverse of distribute: (a*b + a*c) -> a*(b+c)
        if sub[0] == "op" and sub[1] == "+" and len(sub[2]) == 2:
            l, r = sub[2]
            if (l[0] == "op" and l[1] == "*" and r[0] == "op" and r[1] == "*"):
                common = [a for a in l[2] if a in r[2]]
                if common:
                    f = common[0]
                    lrest = list(l[2]); lrest.remove(f)
                    rrest = list(r[2]); rrest.remove(f)
                    lterm = lrest[0] if len(lrest) == 1 else ("op", "*", tuple(lrest)) if lrest else ("num", 1.0)
                    rterm = rrest[0] if len(rrest) == 1 else ("op", "*", tuple(rrest)) if rrest else ("num", 1.0)
                    candidates.append(("op", "*", (f, ("op", "+", (lterm, rterm)))))
        if candidates:
            return replace_at(t, path, rng.choice(candidates))
    return None


def rewrite_k(t: tuple, rng: random.Random, k: int) -> tuple:
    out = t
    for _ in range(k):
        nxt = rewrite_once(out, rng)
        if nxt is None:
            break
        out = nxt
    return out


# ---------------------------------------------------------------------------
# Structural mutations (negatives): change meaning, keep surface plausible
# ---------------------------------------------------------------------------


def mutate(t: tuple, rng: random.Random) -> tuple | None:
    paths = all_subtree_paths(t)
    rng.shuffle(paths)
    for path in paths:
        sub = get_at(t, path)
        options = []
        if sub[0] == "op":
            if sub[1] == "+":
                options.append(("op", "*", sub[2]))
            elif sub[1] == "*":
                options.append(("op", "+", sub[2]))
            elif sub[1] == "^":
                k = sub[2][1]
                other = ("num", 3.0) if k == ("num", 2.0) else ("num", 2.0)
                options.append(("op", "^", (sub[2][0], other)))
            elif sub[1] == "neg":
                options.append(sub[2][0])
            elif sub[1] == "inv":
                options.append(sub[2][0])
        elif sub[0] == "call":
            others = [c for c in CALLS_1 if c != sub[1]]
            options.append(("call", rng.choice(others), sub[2]))
        elif sub[0] == "slot":
            # re-route a slot to another slot id (changes repetition structure)
            options.append(("slot", f"s{rng.randrange(6)}"))
        if options:
            return replace_at(t, path, rng.choice(options))
    return None


# ---------------------------------------------------------------------------
# Dataset builders
# ---------------------------------------------------------------------------


def canonical_of(t: tuple) -> tuple:
    return canonicalize(t)


def make_pair_twins(rng: random.Random, depth: int, positive: bool) -> dict | None:
    n_slots = rng.choice([2, 3, 3, 4])
    t1 = random_tree(rng, depth, n_slots)
    if tree_size(t1) < 5 or not tree_slots(t1):
        return None
    if positive:
        t2 = t1
    else:
        t2 = mutate(t1, rng)
        if t2 is None:
            return None
        if canonical_of(t2) == canonical_of(t1):
            return None
    skin1 = random_skin(rng, tree_slots(t1))
    skin2 = random_skin(rng, tree_slots(t2))
    label = int(canonical_of(t1) == canonical_of(t2))
    if positive and not label:
        return None
    return {
        "task": "twins",
        "expr1": render(t1, skin1, rng),
        "expr2": render(t2, skin2, rng),
        "tree1": t1,
        "tree2": t2,
        "label": label,
        "depth": depth,
    }


def make_pair_equiv(rng: random.Random, depth: int, positive: bool) -> dict | None:
    n_slots = rng.choice([2, 3, 3, 4])
    t1 = random_tree(rng, depth, n_slots)
    if tree_size(t1) < 5 or not tree_slots(t1):
        return None
    if positive:
        t2 = rewrite_k(t1, rng, rng.choice([1, 2, 2, 3]))
        if t2 == t1:
            return None
        if not numerically_equal(t1, t2, rng):
            return None
        label = 1
    else:
        base = rewrite_k(t1, rng, rng.choice([0, 1, 2]))
        t2 = mutate(base, rng)
        if t2 is None:
            return None
        if numerically_equal(t1, t2, rng):
            return None
        label = 0
    skin = random_skin(rng, tree_slots(t1) | tree_slots(t2))
    return {
        "task": "equiv",
        "expr1": render(t1, skin, rng),
        "expr2": render(t2, skin, rng),
        "tree1": t1,
        "tree2": t2,
        "label": label,
        "depth": depth,
    }


def build_split(task: str, n: int, rng: random.Random, depths: list[int]) -> list[dict]:
    out: list[dict] = []
    make = make_pair_twins if task == "twins" else make_pair_equiv
    want_pos = n // 2
    n_pos = n_neg = 0
    attempts = 0
    while len(out) < n and attempts < n * 60:
        attempts += 1
        positive = n_pos < want_pos if n_neg >= n - want_pos else (
            rng.random() < 0.5 if n_pos < want_pos else False)
        d = rng.choice(depths)
        ex = make(rng, d, positive)
        if ex is None or ex["label"] != int(positive):
            continue
        out.append(ex)
        n_pos += ex["label"]
        n_neg += 1 - ex["label"]
    rng.shuffle(out)
    return out


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", type=Path, default=Path("data"))
    ap.add_argument("--train", type=int, default=50000)
    ap.add_argument("--val", type=int, default=5000)
    ap.add_argument("--test", type=int, default=5000)
    ap.add_argument("--ood", type=int, default=3000, help="deeper-tree OOD test size")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for task in ["twins", "equiv"]:
        splits = {
            "train": build_split(task, args.train, rng, [2, 3, 4]),
            "val": build_split(task, args.val, rng, [2, 3, 4]),
            "test": build_split(task, args.test, rng, [2, 3, 4]),
            "ood": build_split(task, args.ood, rng, [5, 6]),
        }
        for split, rows in splits.items():
            path = args.out_dir / f"{task}_{split}.jsonl"
            with path.open("w", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r) + "\n")
            n_pos = sum(r["label"] for r in rows)
            print(f"{task}/{split}: {len(rows)} examples ({n_pos} pos / {len(rows)-n_pos} neg) -> {path}")


if __name__ == "__main__":
    main()
