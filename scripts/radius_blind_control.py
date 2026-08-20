#!/usr/bin/env python3
"""The blind control: 100 shuffled graphs, asked the same question.

DESIGN-retraction-closure §6, verbatim:

    **Blind control.** 100 degree-preserving, kind-preserving edge shuffles
    of the real graph, seeds committed in advance, each run against both
    live drift roots. *If one or more of the 100 shuffled graphs satisfies
    R2 on both roots, the real edges carry no consequence-relevant
    information and this capability is void.* A perfect-looking control
    kills the capability, not the control.

Read that clause twice. It has no pass line for the tool and no failure
line for the control: the control is a way for the capability to die. If a
graph whose edges have been scrambled explains the two hand-audited lists
as well as the real one does, then what R2 measured was the *shape* of the
graph — how many claims, how many ledgers, how densely connected — and not
which claim depends on which ledger. Reporting a satisfying shuffle is
therefore the most valuable thing this script can do, and it is written so
that finding one is easy to see and impossible to explain away: the
satisfying seeds are printed by number, and the summary line counts them
whether the count is zero or not.

**The shuffle, stated precisely.**

- Only ``inferred: false`` ``derived_from`` edges are shuffled. Those are
  the edges R2's closures traverse; scrambling edges the traversal ignores
  would produce a control that differs from the real graph in no way the
  gate can see, which is a control in name only. ``pinned_from`` edges and
  the reconstructed (``inferred: true``) edges ride along untouched.
- Edges are partitioned into classes keyed by ``(kind(from_node),
  kind(to_node))``, and swaps happen only within a class. This is the
  "kind-preserving" clause: a claim→ledger edge is replaced by another
  claim→ledger edge, never by a corpus→seed edge, so the shuffled graph
  remains a graph of the same *type* and the control cannot be satisfied
  by an obviously malformed structure.
- Within a class, double-edge swaps: ``(a→b), (c→d)`` become ``(a→d),
  (c→b)``. Every node keeps its exact out-degree and in-degree, which is
  the "degree-preserving" clause — the shuffled graph has the same number
  of claims citing something and the same number of citations per ledger,
  so a closure that comes out the right size does so by luck rather than
  by construction.
- ``10 × |class|`` swaps are attempted per class, a fixed budget rather
  than a mixing criterion: a stopping rule that looked at the result would
  let the shuffle be tuned. Swaps that would create a self-loop or
  duplicate an existing edge are skipped and consume their attempt.
- Randomness comes from ``random.Random(seed)`` with the seeds committed
  in advance at ``data/retraction_closure/shuffle_seeds.json`` and derived,
  not drawn (the derivation is re-checked in the suite). Same seed, same
  shuffle, byte for byte — asserted in the suite, because a control that
  could not be reproduced could not be audited.

**This module reads the hand-audited lists, and that is correct.** §4's
anti-tautology rule binds the *producers* — ``scripts/provenance_graph.py``
and ``scripts/retraction_radius.py``, whose sources a test scans — because
an assembler that saw the answer key would make R2 vacuous. The control is
on the judging side with ``scripts/radius_adjudicate.py``: it must score
the same clause against the same lists, or it is not a control on R2. It
scores them with :func:`radius_adjudicate.score_closure`, the same function
the real adjudication uses, rather than a second copy of the arithmetic.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from radius_adjudicate import score_closure  # noqa: E402
from retraction_radius import closure_from, load_graph  # noqa: E402

SEEDS_RELATIVE = "data/retraction_closure/shuffle_seeds.json"
GRAPH_RELATIVE = "reports/provenance_graph.jsonl"

#: The two live drift roots of §3's correction, with the hand-audited list
#: each is scored against. The control asks R2 of both, per seed, and a
#: seed only counts if it satisfies BOTH — the clause says "on both roots".
ROOTS: tuple[tuple[str, str, str], ...] = (
    (
        "a",
        "ledger:reports/compression.json",
        "data/retraction_closure/ground_truth_root_a.json",
    ),
    (
        "b",
        "ledger:reports/decompositions.json",
        "data/retraction_closure/ground_truth_root_b.json",
    ),
)

#: Swap attempts per edge in a class. Fixed in advance; see the module
#: docstring on why this is a budget and not a mixing criterion.
SWAPS_PER_EDGE = 10

REPORT_SCHEMA = "retraction-blind-control/1"


def shuffle_edges(
    edges: list[dict], kinds: dict[str, str], seed: int
) -> list[dict]:
    """One seeded, degree- and kind-preserving shuffle of the scored edges.

    Returns the FULL edge list with the scored ``derived_from`` edges
    rewired in place; unscored edges are returned untouched and in their
    original positions, so the only difference between this graph and the
    real one is the thing the gate actually traverses.
    """

    rng = random.Random(seed)
    scored_positions: list[int] = []
    classes: dict[tuple[str, str], list[int]] = {}
    present: set[tuple[str, str]] = set()
    endpoints: dict[int, tuple[str, str]] = {}

    for index, edge in enumerate(edges):
        if edge["relation"] != "derived_from" or edge["inferred"]:
            continue
        scored_positions.append(index)
        pair = (edge["from_node"], edge["to_node"])
        endpoints[index] = pair
        present.add(pair)
        key = (kinds[pair[0]], kinds[pair[1]])
        classes.setdefault(key, []).append(index)

    # Classes in sorted order and members in graph order: the shuffle must
    # be a function of (seed, graph bytes) alone, never of dict iteration.
    for key in sorted(classes):
        members = classes[key]
        if len(members) < 2:
            continue
        for _ in range(SWAPS_PER_EDGE * len(members)):
            i = members[rng.randrange(len(members))]
            j = members[rng.randrange(len(members))]
            if i == j:
                continue
            a, b = endpoints[i]
            c, d = endpoints[j]
            if a == d or c == b:            # self-loop
                continue
            if (a, d) in present or (c, b) in present:   # duplicate
                continue
            present.discard((a, b))
            present.discard((c, d))
            present.add((a, d))
            present.add((c, b))
            endpoints[i] = (a, d)
            endpoints[j] = (c, b)

    shuffled = [dict(edge) for edge in edges]
    for index in scored_positions:
        from_node, to_node = endpoints[index]
        shuffled[index]["from_node"] = from_node
        shuffled[index]["to_node"] = to_node
        # The id is derived from the endpoints, so a rewired slot must be
        # re-identified or two different edges would share an id.
        shuffled[index]["edge_id"] = f"e:{from_node}->{to_node}:derived_from"
    return shuffled


def shuffle_digest(edges: list[dict]) -> str:
    """A stable fingerprint of one shuffle, for the determinism assertion."""

    payload = "\n".join(
        sorted(
            f"{edge['from_node']}\t{edge['to_node']}\t{edge['relation']}"
            f"\t{int(edge['inferred'])}"
            for edge in edges
        )
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def run_control(
    graph_path: Path | str,
    seeds: list[int],
    repo_root: Path | str = REPO_ROOT,
) -> dict:
    """Score R2 on both roots for every seed. Returns the whole report."""

    repo_root = Path(repo_root)
    nodes, edges = load_graph(Path(graph_path))
    kinds = {node_id: node["kind"] for node_id, node in nodes.items()}
    audits = {
        key: json.loads((repo_root / rel).read_text(encoding="utf-8"))
        for key, _, rel in ROOTS
    }

    rows: list[dict] = []
    satisfying: list[int] = []
    for seed in seeds:
        shuffled = shuffle_edges(edges, kinds, seed)
        per_root = {}
        for key, root, _ in ROOTS:
            closure = set(closure_from(shuffled, root))
            verdict = score_closure(nodes, closure, audits[key])
            per_root[key] = {
                "root_node": root,
                "covered": verdict["covered"],
                "total": verdict["total"],
                "closure_size": verdict["closure_size"],
                "cap": verdict["cap"],
                "superset_ok": verdict["superset_ok"],
                "ratio_ok": verdict["ratio_ok"],
                "r2_ok": verdict["r2_ok"],
            }
        both = all(entry["r2_ok"] for entry in per_root.values())
        if both:
            satisfying.append(seed)
        rows.append(
            {
                "seed": seed,
                "shuffle_digest": shuffle_digest(shuffled),
                "roots": per_root,
                "satisfies_r2_on_both_roots": both,
            }
        )

    return {
        "schema": REPORT_SCHEMA,
        "graph_sha256": hashlib.sha256(
            Path(graph_path).read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest(),
        "seeds_run": len(seeds),
        "swaps_per_edge": SWAPS_PER_EDGE,
        "satisfying_seeds": satisfying,
        "satisfying_shuffles": len(satisfying),
        "results": rows,
    }


def load_seeds(repo_root: Path = REPO_ROOT) -> list[int]:
    return json.loads(
        (repo_root / SEEDS_RELATIVE).read_text(encoding="utf-8")
    )["seeds"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run design section 6's blind control")
    ap.add_argument("--graph", default=str(REPO_ROOT / GRAPH_RELATIVE))
    ap.add_argument(
        "--limit",
        type=int,
        default=None,
        help="run only the first N committed seeds (a smoke run, never the "
             "registered one: the clause says 100)",
    )
    ap.add_argument("--out", default=None, help="write the JSON report here")
    args = ap.parse_args(argv)

    seeds = load_seeds()
    if args.limit is not None:
        seeds = seeds[: args.limit]
    report = run_control(args.graph, seeds)

    for row in report["results"]:
        if row["satisfies_r2_on_both_roots"]:
            print(f"SATISFYING SHUFFLE seed={row['seed']} {row['roots']}")
    print(f"satisfying_shuffles: {report['satisfying_shuffles']} / {len(seeds)}")
    if args.out:
        Path(args.out).write_bytes(
            (json.dumps(report, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
