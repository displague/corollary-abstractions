#!/usr/bin/env python3
"""Self-grounding curve: ISG_real(N) against a distribution-matched null.

docs/DESIGN-self-grounding-ingestion.md, ROADMAP-v0.11 item 1. Predictions
S1–S4 were registered in that design *before* the 12k ingested corpus
existed. This module is the committed generator; it does not invent a
second question.

ROUTE 1 (decided in design §8, before this file existed): ISG is the
fraction of *considered* subterms in ingested nodes whose most-independent
owner is another ingested node. Owner identity comes from the `owners`
field `decompose.analyze` now emits. Route 2 (shared-skeleton proxy) is
a labelled control, not the headline.

What this script runs
---------------------
Decomposition only. It never calls specialize.py (design §7). Pattern
membership is off: ingested statements already skip `pattern_cover`, and
ISG/XSG are exact-owner questions. Each curve point recomputes `analyze`
over (hand-authored corpora held fixed) ∪ (ingested subsample or a
matched synthetic overlay). Subsamples are drawn from a committed seed.

Registered predictions (frozen in the design; restated, not rewritten)
--------------------------------------------------------------------
S1  ISG_real(N) > ISG_null(N) at the largest N, by more than the
    seed-to-seed spread of the null.
S2  The gap ISG_real − ISG_null widens with N (compounding), rather than
    being a constant offset.
S3  XSG does not fall by as much as ISG rises: the ingested layer gains
    owners without losing its connection to the hand-authored corpus.
S4  The S1 effect survives removing the single most common subterm. A
    curve carried by one popular term is a fact about that term.

P-R1 (design §8, the owners-field prediction): adding `owners` changes
no channel, no count, and no aggregate. Guarded in
tests/test_decompose_channels.py, not here.

Null model (design §4)
----------------------
For each N, generate N synthetic statements whose operator/call heads,
arities, numerals, slot names, relations, sizes, and discipline labels
are sampled from the *observed* ingested layer (not uniform), then
skeletonized through the same matcher front end. Trees are structurally
random. Three seeds; the spread is max − min of ISG_null at that N.

Adjudication is written into the result JSON by this script (closed-form
predicates over the numbers). Prose in ANALYSIS.md / DISCOVERIES.md is
appended after the run, not edited into this docstring.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from decompose import (  # noqa: E402
    _ingested_sid,
    analyze_loaded,
    attach_extra,
    load_trees,
    owner_channel,
    tree_size,
)
from match_signatures import (  # noqa: E402
    Parser,
    TemplateParseError,
    canonicalize,
    tokenize,
)

DEFAULT_OUT = REPO / "experiments" / "self_grounding_curve.json"
SELECTION_SEED = 20260814
NULL_SEEDS = (0, 1, 2)
SIZE_POINTS = (8, 32, 128, 512)
IDENT_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
SCHEMA = "self_grounding_curve.v1"


# --------------------------------------------------------------------------
# Empirical inventory and structurally-random printer
# --------------------------------------------------------------------------


def _walk_heads(tree: tuple, ops: list, calls: list, leaves: list, rels: list) -> None:
    kind = tree[0]
    if kind == "num":
        leaves.append(("num", tree[1]))
        return
    if kind == "slot":
        leaves.append(("slot", tree[1]))
        return
    if kind == "rel":
        rels.append(tree[1])
        for a in tree[2]:
            _walk_heads(a, ops, calls, leaves, rels)
        return
    arity = len(tree[2])
    if kind == "op":
        ops.append((tree[1], arity))
    elif kind == "call" and IDENT_RE.match(tree[1] or ""):
        calls.append((tree[1], arity))
    for a in tree[2]:
        _walk_heads(a, ops, calls, leaves, rels)


def observed_inventory(
    ingested: list[str],
    trees: dict[str, tuple],
    disciplines_of: dict[str, frozenset],
    corpus_of: dict[str, str],
) -> dict:
    ops: list[tuple[str, int]] = []
    calls: list[tuple[str, int]] = []
    leaves: list[tuple] = []
    rels: list[str] = []
    sizes: list[int] = []
    disc_sets: list[tuple[str, ...]] = []
    disciplines_by_sid: dict[str, tuple[str, ...]] = {}
    for sid in ingested:
        tree = trees.get(sid)
        if tree is None:
            continue
        sizes.append(tree_size(tree))
        _walk_heads(tree, ops, calls, leaves, rels)
        labels = tuple(sorted(disciplines_of.get(sid, frozenset())))
        disc_sets.append(labels)
        disciplines_by_sid[sid] = labels
    if not sizes:
        raise ValueError("ingested layer has no parseable trees")
    # Fallbacks so a degenerate fixture still prints a parseable statement.
    if not leaves:
        leaves = [("num", 2.0), ("slot", "x")]
    if not ops and not calls:
        ops = [("+", 2), ("*", 2)]
    if not rels:
        rels = ["="]
    if not disc_sets:
        disc_sets = [("number_theory",)]
    return {
        "ops": ops,
        "calls": calls,
        "leaves": leaves,
        "rels": rels,
        "sizes": sizes,
        "disc_sets": disc_sets,
        "disciplines_by_sid": disciplines_by_sid,
        "n_observed": len(sizes),
    }


def render_template(tree: tuple) -> str:
    """Infix / call-form printer whose output `tokenize`/`Parser` accept."""
    kind = tree[0]
    if kind == "num":
        value = tree[1]
        if isinstance(value, float) and value == int(value) and abs(value) < 1e15:
            return str(int(value))
        return f"{value:g}"
    if kind == "slot":
        return str(tree[1])
    if kind == "rel":
        lhs, rhs = tree[2]
        return f"{render_template(lhs)} {tree[1]} {render_template(rhs)}"
    if kind == "op":
        op, args = tree[1], tree[2]
        if op == "neg" and len(args) == 1:
            return f"-({render_template(args[0])})"
        if op == "inv" and len(args) == 1:
            return f"(1 / ({render_template(args[0])}))"
        if op == "pm" and len(args) == 1:
            return f"(0 + -({render_template(args[0])}))"
        if op in {"+", "*"} and args:
            return "(" + f" {op} ".join(render_template(a) for a in args) + ")"
        if op == "^" and len(args) == 2:
            return f"({render_template(args[0])} ^ {render_template(args[1])})"
        if op in {"-", "/"} and len(args) == 2:
            return f"({render_template(args[0])} {op} {render_template(args[1])})"
        inner = ", ".join(render_template(a) for a in args)
        return f"{op}({inner})"
    if kind == "call":
        inner = ", ".join(render_template(a) for a in tree[2])
        return f"{tree[1]}({inner})"
    raise ValueError(f"unknown tree kind {kind!r}")


def _random_leaf(rng: random.Random, inv: dict) -> tuple:
    kind, payload = rng.choice(inv["leaves"])
    if kind == "num":
        return ("num", payload)
    name = payload if IDENT_RE.match(str(payload) or "") else "x"
    return ("slot", name)


def _random_expr(rng: random.Random, inv: dict, budget: int) -> tuple:
    if budget <= 1 or rng.random() < 0.35:
        return _random_leaf(rng, inv)
    use_call = bool(inv["calls"]) and (
        not inv["ops"] or rng.random() < len(inv["calls"]) / (
            len(inv["calls"]) + len(inv["ops"])))
    if use_call:
        head, arity = rng.choice(inv["calls"])
        arity = max(1, min(arity, 4))
        child_budget = max(1, (budget - 1) // arity)
        return ("call", head, tuple(
            _random_expr(rng, inv, child_budget) for _ in range(arity)))
    head, arity = rng.choice(inv["ops"])
    arity = max(1, min(arity, 4))
    child_budget = max(1, (budget - 1) // arity)
    return ("op", head, tuple(
        _random_expr(rng, inv, child_budget) for _ in range(arity)))


def random_statement_tree(rng: random.Random, inv: dict) -> tuple:
    size = rng.choice(inv["sizes"])
    rel = rng.choice(inv["rels"])
    half = max(1, size // 2)
    return ("rel", rel, (_random_expr(rng, inv, half), _random_expr(rng, inv, half)))


def generate_synthetic(
    n: int,
    inv: dict,
    seed: int,
    *,
    max_attempts_per: int = 20,
) -> list[dict]:
    """N structurally-random statements; each template parses or we retry."""
    rng = random.Random(seed)
    out: list[dict] = []
    attempts = 0
    target_attempts = n * max_attempts_per
    while len(out) < n and attempts < target_attempts:
        attempts += 1
        tree = random_statement_tree(rng, inv)
        try:
            template = render_template(tree)
            canonicalize(Parser(tokenize(template)).parse())
        except (TemplateParseError, ValueError, ZeroDivisionError):
            continue
        disc = list(rng.choice(inv["disc_sets"]) or ("number_theory",))
        idx = len(out)
        out.append({
            "statement_id": f"null.synth.{seed}.{idx}",
            "template": template,
            "corpus_id": "lean_workbook.null.v1",
            "discipline": "lean_workbook",
            "disciplines": disc,
        })
    if len(out) < n:
        raise RuntimeError(
            f"null seed {seed}: only {len(out)}/{n} synthetic templates parsed "
            f"after {attempts} attempts")
    return out


# --------------------------------------------------------------------------
# ISG / XSG / proxy over an analyze result
# --------------------------------------------------------------------------


def classify_constituent(
    sid: str,
    constituent: dict,
    ingested: set[str],
    corpus_of: dict[str, str],
    disciplines_of: dict[str, frozenset],
) -> str:
    """Route-1 label of one exact constituent.

    `isg` — every owner in the winning channel is ingested.
    `xsg` — every owner in the winning channel is hand-authored.
    `mixed` — the winning channel has both (reported, not folded in).
    `recursive` / `pattern` — not owner-attributed.
    """
    if constituent.get("grounded_via") != "exact":
        return "pattern"
    owners = list(constituent.get("owners") or [])
    if not owners:
        return "recursive"
    winning = [
        owner for owner in owners
        if owner_channel(sid, owner, corpus_of, disciplines_of)
        == constituent["channel"]
    ]
    if not winning:
        winning = owners
    flags = [owner in ingested for owner in winning]
    if all(flags):
        return "isg"
    if not any(flags):
        return "xsg"
    return "mixed"


def score_entries(
    entries: list[dict],
    ingested: set[str],
    corpus_of: dict[str, str],
    disciplines_of: dict[str, frozenset],
    *,
    drop_skeleton: str | None = None,
) -> dict:
    """Counts and rates over ingested statements. Raw counts always travel."""
    considered = 0
    n_isg = n_xsg = n_mixed = n_exact = n_proxy = 0
    dropped = 0
    skel_hosts: dict[str, set[str]] = defaultdict(set)
    skel_occ: Counter[str] = Counter()
    for entry in entries:
        sid = entry["statement_id"]
        if sid not in ingested:
            continue
        exact = [c for c in entry["constituents"] if c.get("grounded_via") == "exact"]
        kept = [c for c in exact if c.get("skeleton") != drop_skeleton]
        n_drop = len(exact) - len(kept)
        dropped += n_drop
        # `considered` includes ungrounded subterms. Dropping a skeleton
        # removes it from the denominator as well as the numerator, or S4
        # would punish the rate for a term it was told to ignore.
        considered += entry["considered"] - n_drop
        n_exact += len(kept)
        for constituent in kept:
            label = classify_constituent(
                sid, constituent, ingested, corpus_of, disciplines_of)
            if label == "isg":
                n_isg += 1
            elif label == "xsg":
                n_xsg += 1
            elif label == "mixed":
                n_mixed += 1
            owners = constituent.get("owners") or []
            if any(owner in ingested for owner in owners):
                n_proxy += 1
            skel = constituent.get("skeleton")
            if skel:
                skel_hosts[skel].add(sid)
                skel_occ[skel] += 1
    def rate(num: int, den: int) -> float | None:
        return (num / den) if den else None

    top = None
    if skel_occ:
        # Most common = most host statements, then most occurrences, then name.
        top_skel = max(
            skel_occ,
            key=lambda s: (len(skel_hosts[s]), skel_occ[s], s),
        )
        top = {
            "skeleton": top_skel,
            "host_statements": len(skel_hosts[top_skel]),
            "occurrences": skel_occ[top_skel],
        }
    return {
        "ingested_statements": len(ingested),
        "considered": considered,
        "exact": n_exact,
        "isg": n_isg,
        "xsg": n_xsg,
        "mixed": n_mixed,
        "proxy": n_proxy,
        "dropped": dropped,
        "isg_rate": rate(n_isg, considered),
        "xsg_rate": rate(n_xsg, considered),
        "mixed_rate": rate(n_mixed, considered),
        "isg_of_grounded": rate(n_isg, n_exact),
        "xsg_of_grounded": rate(n_xsg, n_exact),
        "proxy_rate": rate(n_proxy, n_exact),
        "proxy_minus_isg_of_grounded": (
            None if n_exact == 0 else (n_proxy - n_isg) / n_exact),
        "most_common_subterm": top,
    }


def subsample(ids: list[str], n: int, seed: int) -> list[str]:
    """Committed selection: sort, then shuffle with a fixed seed, then prefix."""
    ordered = sorted(ids)
    rng = random.Random(seed)
    rng.shuffle(ordered)
    return ordered[:n]


# --------------------------------------------------------------------------
# Curve + adjudication
# --------------------------------------------------------------------------


def _spread(values: list[float]) -> float:
    return max(values) - min(values) if values else 0.0


def adjudicate(points: list[dict]) -> dict:
    """Closed-form S1–S4 over the computed rows. Fired and missed both land."""
    if not points:
        return {"S1": {"fired": False, "reason": "no points"},
                "S2": {"fired": False, "reason": "no points"},
                "S3": {"fired": False, "reason": "no points"},
                "S4": {"fired": False, "reason": "no points"}}

    def real_isg(p: dict) -> float:
        return float(p["real"]["isg_rate"])

    def null_mean(p: dict) -> float:
        return sum(float(n["isg_rate"]) for n in p["null"]) / len(p["null"])

    def null_rates(p: dict) -> list[float]:
        return [float(n["isg_rate"]) for n in p["null"]]

    largest = points[-1]
    smallest = points[0]
    real_big = real_isg(largest)
    nulls_big = null_rates(largest)
    null_mean_big = sum(nulls_big) / len(nulls_big)
    spread_big = _spread(nulls_big)
    gap_big = real_big - null_mean_big
    s1 = {
        "fired": real_big > null_mean_big and gap_big > spread_big,
        "isg_real": real_big,
        "isg_null_mean": null_mean_big,
        "isg_null_spread": spread_big,
        "gap": gap_big,
        "n": largest["n"],
    }

    gaps = []
    for point in points:
        if point["real"]["isg_rate"] is None:
            continue
        gaps.append({
            "n": point["n"],
            "gap": real_isg(point) - null_mean(point),
        })
    # Widens: last gap > first gap, and Spearman of (n, gap) is positive.
    s2_fired = False
    spearman = None
    if len(gaps) >= 2:
        s2_fired = gaps[-1]["gap"] > gaps[0]["gap"]
        xs = [g["n"] for g in gaps]
        ys = [g["gap"] for g in gaps]
        rx = _rank(xs)
        ry = _rank(ys)
        spearman = _pearson(rx, ry)
        s2_fired = s2_fired and spearman is not None and spearman > 0
    s2 = {
        "fired": s2_fired,
        "gaps": gaps,
        "spearman_n_gap": spearman,
    }

    # S3 compares the ingested layer at the smallest N to the largest N.
    isg_rise = real_isg(largest) - real_isg(smallest)
    xsg_small = float(smallest["real"]["xsg_rate"])
    xsg_big = float(largest["real"]["xsg_rate"])
    xsg_fall = xsg_small - xsg_big  # positive if XSG dropped
    s3 = {
        "fired": xsg_fall <= isg_rise,
        "isg_rise": isg_rise,
        "xsg_fall": xsg_fall,
        "xsg_at_smallest": xsg_small,
        "xsg_at_largest": xsg_big,
        "smallest_n": smallest["n"],
        "largest_n": largest["n"],
    }

    s4_real = largest["s4"]["real"]["isg_rate"]
    s4_nulls = [float(n["isg_rate"]) for n in largest["s4"]["null"]]
    s4_null_mean = sum(s4_nulls) / len(s4_nulls)
    s4_spread = _spread(s4_nulls)
    s4_gap = float(s4_real) - s4_null_mean
    s4 = {
        "fired": float(s4_real) > s4_null_mean and s4_gap > s4_spread,
        "isg_real": s4_real,
        "isg_null_mean": s4_null_mean,
        "isg_null_spread": s4_spread,
        "gap": s4_gap,
        "dropped_skeleton": largest["s4"]["dropped_skeleton"],
        "n": largest["n"],
    }
    return {"S1": s1, "S2": s2, "S3": s3, "S4": s4}


def _rank(values: list[float]) -> list[float]:
    """Average ranks, 1-based, ties share the mean rank."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    n = len(xs)
    if n < 2:
        return None
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = sum((x - mx) ** 2 for x in xs) ** 0.5
    dy = sum((y - my) ** 2 for y in ys) ** 0.5
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def measure(
    data_dir: Path,
    *,
    sizes: tuple[int, ...] = SIZE_POINTS,
    selection_seed: int = SELECTION_SEED,
    null_seeds: tuple[int, ...] = NULL_SEEDS,
    include_all: bool = True,
    min_family: int = 2,
) -> dict:
    """Build the curve. Loads the graph once; each point is an in-memory overlay."""
    all_nodes, all_trees, all_classes, all_corpus, all_disc = load_trees(data_dir)
    ingested_ids = [
        n.statement_id for n in all_nodes
        if _ingested_sid(n.statement_id, all_corpus)
    ]
    curated_nodes = [
        n for n in all_nodes
        if not _ingested_sid(n.statement_id, all_corpus)
    ]
    curated_ids = {n.statement_id for n in curated_nodes}
    curated_trees = {sid: all_trees[sid] for sid in curated_ids if sid in all_trees}
    curated_classes = {sid: all_classes[sid] for sid in curated_ids if sid in all_classes}
    curated_corpus = {sid: all_corpus[sid] for sid in curated_ids}
    curated_disc = {sid: all_disc[sid] for sid in curated_ids}

    inventory = observed_inventory(ingested_ids, all_trees, all_disc, all_corpus)
    n_all = len(ingested_ids)
    ns: list[int] = [n for n in sizes if n < n_all]
    if include_all:
        ns.append(n_all)

    by_id = {n.statement_id: n for n in all_nodes}

    def analyze_subset(sids: list[str]) -> tuple[dict, dict, dict]:
        keep_nodes = list(curated_nodes) + [by_id[s] for s in sids]
        keep_ids = {n.statement_id for n in keep_nodes}
        trees = {sid: all_trees[sid] for sid in keep_ids}
        classes = {sid: all_classes[sid] for sid in keep_ids}
        corpus_of = {sid: all_corpus[sid] for sid in keep_ids}
        disciplines_of = {sid: all_disc[sid] for sid in keep_ids}
        result = analyze_loaded(
            keep_nodes, trees, classes, corpus_of, disciplines_of,
            min_family=min_family, pattern_membership=False,
        )
        return result, corpus_of, disciplines_of

    def analyze_null(synths: list[dict]) -> tuple[dict, dict, dict]:
        nodes = list(curated_nodes)
        trees = dict(curated_trees)
        classes = {k: dict(v) for k, v in curated_classes.items()}
        corpus_of = dict(curated_corpus)
        disciplines_of = dict(curated_disc)
        attach_extra(nodes, trees, classes, corpus_of, disciplines_of, synths)
        result = analyze_loaded(
            nodes, trees, classes, corpus_of, disciplines_of,
            min_family=min_family, pattern_membership=False,
        )
        return result, corpus_of, disciplines_of

    points = []
    for n in ns:
        chosen = subsample(ingested_ids, n, selection_seed)
        chosen_set = set(chosen)
        real_result, real_corpus, real_disc = analyze_subset(chosen)
        real_score = score_entries(
            real_result["decompositions"], chosen_set, real_corpus, real_disc)
        top = real_score["most_common_subterm"]
        drop = top["skeleton"] if top else None

        null_rows = []
        s4_null_rows = []
        for seed in null_seeds:
            synths = generate_synthetic(n, inventory, seed)
            synth_ids = {s["statement_id"] for s in synths}
            null_result, null_corpus, null_disc = analyze_null(synths)
            null_score = score_entries(
                null_result["decompositions"], synth_ids, null_corpus, null_disc)
            null_rows.append({"seed": seed, **null_score})
            s4_null_rows.append({
                "seed": seed,
                **score_entries(
                    null_result["decompositions"], synth_ids, null_corpus, null_disc,
                    drop_skeleton=drop,
                ),
            })

        s4_real = score_entries(
            real_result["decompositions"], chosen_set, real_corpus, real_disc,
            drop_skeleton=drop,
        )
        points.append({
            "n": n,
            "selection_seed": selection_seed,
            "real": real_score,
            "null": null_rows,
            "s4": {
                "dropped_skeleton": drop,
                "real": s4_real,
                "null": s4_null_rows,
            },
        })

    verdicts = adjudicate(points)
    return {
        "schema": SCHEMA,
        "route": 1,
        "proxy_is": "control",
        "selection_seed": selection_seed,
        "null_seeds": list(null_seeds),
        "min_family": min_family,
        "pattern_membership": False,
        "passes": ["decompose.analyze_loaded"],
        "not_run": ["specialize.py"],
        "ingested_layer": n_all,
        "curated_layer": len(curated_nodes),
        "inventory": {
            "n_observed": inventory["n_observed"],
            "n_ops": len(inventory["ops"]),
            "n_calls": len(inventory["calls"]),
            "n_leaves": len(inventory["leaves"]),
            "n_rels": len(inventory["rels"]),
            "unique_ops": sorted({h for h, _ in inventory["ops"]}),
            "unique_calls": sorted({h for h, _ in inventory["calls"]}),
            "unique_rels": sorted(set(inventory["rels"])),
        },
        "points": points,
        "adjudication": verdicts,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=REPO / "data")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--sizes", type=int, nargs="*", default=list(SIZE_POINTS),
        help="subsample sizes; `all` is always appended unless --no-all")
    ap.add_argument("--no-all", action="store_true",
                    help="do not add the full ingested layer as a point")
    ap.add_argument("--selection-seed", type=int, default=SELECTION_SEED)
    ap.add_argument("--null-seeds", type=int, nargs="*", default=list(NULL_SEEDS))
    args = ap.parse_args()
    result = measure(
        args.data_dir,
        sizes=tuple(args.sizes),
        selection_seed=args.selection_seed,
        null_seeds=tuple(args.null_seeds),
        include_all=not args.no_all,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    adj = result["adjudication"]
    print(json.dumps({
        "wrote": str(args.out),
        "ingested_layer": result["ingested_layer"],
        "points": [p["n"] for p in result["points"]],
        "adjudication": {
            name: {"fired": block["fired"], **{
                k: block[k] for k in block
                if k in {"gap", "isg_real", "isg_null_mean", "isg_rise", "xsg_fall"}
            }}
            for name, block in adj.items()
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
