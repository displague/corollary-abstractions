"""Bilingual toy-grammar world: cross-language twin detection (xlang task).

One semantic tree (interlingua), two surface languages with different word
order and disjoint lexica. A pair is a twin iff both sentences express the
same proposition (canonical tree equality: modifier sets commutative,
argument roles and intensifier nesting fixed).

Tree schema (same tuple AST as the formula world, so the canonicalizer and
serializers are reused unchanged):
    ("call","STMT",(evt,))                declarative  ~ proof/assertion
    ("call","ASK",(evt,))                 WH-question  ~ equation (WH = unknown)
    ("call","CMP",(dim, np1, np2))        comparison   ~ inequality np1 > np2
    ("call","EVT",(verb, np_agent, np_patient))
    NP  = noun-slot | ("op","+",(noun, adjp...))      + = intersective set
    ADJP= adj-slot  | ("call","MOD",(adjp, intensifier))  recursive nesting
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from match_signatures import canonicalize  # noqa: E402

SEP = "<sep>"

NOUNS = ["dog", "cat", "wolf", "bird", "child", "teacher", "robot", "farmer",
         "queen", "fox", "horse", "student", "doctor", "thief", "poet", "crab"]
ADJS = ["big", "red", "old", "fast", "loud", "clever", "small", "green",
        "brave", "tired", "hungry", "quiet"]
VERBS = ["chases", "sees", "likes", "follows", "helps", "fears", "carries",
         "greets", "avoids", "teaches"]
DIMS = ["big", "fast", "old", "loud", "brave", "small"]
INTENS = ["very", "quite", "truly"]

SYLL = ["ka", "to", "mi", "su", "ren", "bo", "cha", "lu", "ne", "gi",
        "za", "po", "ver", "dul", "shi", "mon"]


def word_b(concept: str) -> str:
    """Deterministic disjoint pseudo-lexicon for Language B."""
    h = 0
    for ch in concept:
        h = (h * 31 + ord(ch)) % (1 << 16)
    return SYLL[h % 16] + SYLL[(h // 16) % 16] + SYLL[(h // 256) % 16][0]


LEX_A = {f"n{i}": w for i, w in enumerate(NOUNS)}
LEX_A |= {f"a{i}": w for i, w in enumerate(ADJS)}
LEX_A |= {f"v{i}": w for i, w in enumerate(VERBS)}
LEX_A |= {f"d{i}": w for i, w in enumerate(DIMS)}
LEX_A |= {f"i{i}": w for i, w in enumerate(INTENS)}
LEX_A["WH"] = "wh"
LEX_B = {c: word_b(c + LEX_A[c]) for c in LEX_A}
LEX_B["WH"] = "wo"


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def gen_adjp(rng: random.Random, depth: int) -> tuple:
    adj = ("slot", f"a{rng.randrange(len(ADJS))}")
    node = adj
    for _ in range(rng.choices([0, 1, 2], weights=[70, 22, 8])[0] if depth <= 1
                   else rng.choice([1, 2, depth])):
        node = ("call", "MOD", (node, ("slot", f"i{rng.randrange(len(INTENS))}")))
    return node


def gen_np(rng: random.Random, depth: int) -> tuple:
    noun = ("slot", f"n{rng.randrange(len(NOUNS))}")
    n_adj = rng.choices([0, 1, 2, 3], weights=[35, 35, 20, 10])[0] if depth <= 1 \
        else rng.choice([2, 3, depth + 1])
    if n_adj == 0:
        return noun
    seen: set[str] = set()
    adjps = []
    while len(adjps) < n_adj:
        ap = gen_adjp(rng, depth)
        base = ap
        while base[0] == "call":
            base = base[2][0]
        if base[1] in seen:
            continue
        seen.add(base[1])
        adjps.append(ap)
    return ("op", "+", (noun, *adjps))


def gen_tree(rng: random.Random, depth: int) -> tuple:
    kind = rng.random()
    if kind < 0.5:
        evt = ("call", "EVT", (("slot", f"v{rng.randrange(len(VERBS))}"),
                               gen_np(rng, depth), gen_np(rng, depth)))
        return ("call", "STMT", (evt,))
    if kind < 0.8:
        wh_agent = rng.random() < 0.5
        agent = ("slot", "WH") if wh_agent else gen_np(rng, depth)
        patient = gen_np(rng, depth) if wh_agent else ("slot", "WH")
        evt = ("call", "EVT", (("slot", f"v{rng.randrange(len(VERBS))}"),
                               agent, patient))
        return ("call", "ASK", (evt,))
    return ("call", "CMP", (("slot", f"d{rng.randrange(len(DIMS))}"),
                            gen_np(rng, depth), gen_np(rng, depth)))


# ---------------------------------------------------------------------------
# Surface rendering
# ---------------------------------------------------------------------------


def render_adjp(t: tuple, lex: dict[str, str], lang: str) -> list[str]:
    if t[0] == "slot":
        return [lex[t[1]]]
    inner = render_adjp(t[2][0], lex, lang)
    intens = lex[t[2][1][1]]
    return [intens] + inner if lang == "A" else inner + [intens]


def render_np(t: tuple, lex: dict[str, str], lang: str,
              rng: random.Random) -> list[str]:
    if t[0] == "slot":
        return ["the", lex[t[1]]] if lang == "A" else [lex[t[1]]]
    noun, *adjps = t[2]
    adjps = list(adjps)
    rng.shuffle(adjps)  # surface order of intersective modifiers is free
    words: list[str] = []
    for ap in adjps:
        words.extend(render_adjp(ap, lex, lang))
    if lang == "A":
        return ["the"] + words + [lex[noun[1]]]
    return [lex[noun[1]]] + words


def render(t: tuple, lang: str, rng: random.Random,
           lex: dict[str, str] | None = None) -> str:
    if lex is None:
        lex = LEX_A if lang == "A" else LEX_B

    def np_or_wh(n: tuple) -> list[str]:
        if n == ("slot", "WH"):
            return [lex["WH"]]
        return render_np(n, lex, lang, rng)

    head = t[1]
    if head in {"STMT", "ASK"}:
        verb, agent, patient = t[2][0][2]
        v = [lex[verb[1]]]
        if lang == "A":
            words = np_or_wh(agent) + v + np_or_wh(patient)
        else:
            words = np_or_wh(agent) + np_or_wh(patient) + v
        if head == "ASK":
            words = words + ["?"] if lang == "A" else words + ["ka"]
        return " ".join(words)
    dim, np1, np2 = t[2]
    if lang == "A":
        return " ".join(np_or_wh(np1) + ["is", lex[dim[1]] + "er", "than"]
                        + np_or_wh(np2))
    return " ".join(np_or_wh(np1) + np_or_wh(np2) + [lex[dim[1]], "mas"])


# ---------------------------------------------------------------------------
# Serialization per arm
# ---------------------------------------------------------------------------


def struct_tokens_lang(t: tuple, lex: dict[str, str]) -> list[str]:
    """Parse-tree tokens with language-native words at the leaves."""
    if t[0] == "slot":
        return [lex[t[1]]]
    head = t[1]
    out = [f"{head}("]
    for a in t[2]:
        out.extend(struct_tokens_lang(a, lex))
    out.append(")")
    return out


def canon_tokens_lang(t: tuple) -> list[str]:
    """Canonical interlingua tokens: concept ids, modifier sets sorted."""
    t = canonicalize(t)

    def ser(n: tuple) -> list[str]:
        if n[0] == "slot":
            return [n[1]]
        out = [f"{n[1]}("]
        for a in n[2]:
            out.extend(ser(a))
        out.append(")")
        return out

    return ser(t)


# ---------------------------------------------------------------------------
# Mutations (negatives)
# ---------------------------------------------------------------------------


def mutate(t: tuple, rng: random.Random) -> tuple | None:
    choice = rng.random()
    head = t[1]
    if head in {"STMT", "ASK"}:
        verb, agent, patient = t[2][0][2]
        if choice < 0.3 and agent != patient:
            evt = ("call", "EVT", (verb, patient, agent))  # role swap
            return ("call", head, (evt,))
        if choice < 0.5:
            new_v = ("slot", f"v{rng.randrange(len(VERBS))}")
            if new_v == verb:
                return None
            return ("call", head, (("call", "EVT", (new_v, agent, patient)),))
        # concept swap inside an NP / adjective move / type flip
        if choice < 0.7 and head == "STMT":
            wh_agent = rng.random() < 0.5
            evt = ("call", "EVT", (verb, ("slot", "WH") if wh_agent else agent,
                                   patient if wh_agent else ("slot", "WH")))
            return ("call", "ASK", (evt,))
        target_agent = rng.random() < 0.5
        np_new = mutate_np(agent if target_agent else patient, rng)
        if np_new is None:
            return None
        evt = ("call", "EVT", (verb, np_new if target_agent else agent,
                               patient if target_agent else np_new))
        return ("call", head, (evt,))
    dim, np1, np2 = t[2]
    if choice < 0.35 and np1 != np2:
        return ("call", "CMP", (dim, np2, np1))  # comparison direction
    if choice < 0.6:
        new_d = ("slot", f"d{rng.randrange(len(DIMS))}")
        if new_d == dim:
            return None
        return ("call", "CMP", (new_d, np1, np2))
    np_new = mutate_np(np1 if rng.random() < 0.5 else np2, rng)
    if np_new is None:
        return None
    return ("call", "CMP", (dim, np_new, np2) if rng.random() < 0.5
            else (dim, np1, np_new))


def mutate_np(np: tuple, rng: random.Random) -> tuple | None:
    if np[0] == "slot":
        if np[1] == "WH":
            return None
        new = f"n{rng.randrange(len(NOUNS))}"
        return None if new == np[1] else ("slot", new)
    noun, *adjps = np[2]
    r = rng.random()
    if r < 0.4:  # change the noun
        new = f"n{rng.randrange(len(NOUNS))}"
        return None if new == noun[1] else ("op", "+", (("slot", new), *adjps))
    if r < 0.7 and adjps:  # drop an adjective
        keep = list(adjps)
        keep.pop(rng.randrange(len(keep)))
        return ("op", "+", (noun, *keep)) if keep else noun
    ap = gen_adjp(rng, 1)  # add an adjective
    return ("op", "+", (noun, *adjps, ap))


# ---------------------------------------------------------------------------
# Dataset build
# ---------------------------------------------------------------------------


def make_pair(rng: random.Random, depth: int, positive: bool) -> dict | None:
    t1 = gen_tree(rng, depth)
    if positive:
        t2 = t1
    else:
        t2 = mutate(t1, rng)
        if t2 is None or canonicalize(t2) == canonicalize(t1):
            return None
    return {
        "task": "xlang",
        "expr1": render(t1, "A", rng),
        "expr2": render(t2, "B", rng),
        "tree1": t1,
        "tree2": t2,
        "label": int(canonicalize(t1) == canonicalize(t2)),
        "depth": depth,
        "tokens_struct": (struct_tokens_lang(t1, LEX_A) + [SEP]
                          + struct_tokens_lang(t2, LEX_B)),
        "tokens_canon": (canon_tokens_lang(t1) + [SEP]
                         + canon_tokens_lang(t2)),
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
        if ex is None or ex["label"] != int(positive):
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
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    splits = {
        "train": build_split(args.train, rng, [1, 1, 2]),
        "val": build_split(args.val, rng, [1, 1, 2]),
        "test": build_split(args.test, rng, [1, 1, 2]),
        "ood": build_split(args.ood, rng, [3, 4]),  # deeper modifier recursion
    }
    for split, rows in splits.items():
        path = args.out_dir / f"xlang_{split}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r) + "\n")
        n_pos = sum(r["label"] for r in rows)
        print(f"xlang/{split}: {len(rows)} ({n_pos} pos) -> {path}")


if __name__ == "__main__":
    main()
