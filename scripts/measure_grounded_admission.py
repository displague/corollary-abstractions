#!/usr/bin/env python3
"""Measure groundedness-at-all on paired one-head near-misses.

The threshold, seeds, foil concept, and G1--G4 bars were stated in prose at
commit 3fe54cf28bdbcf9870538daf888898c9b234ac21.  This executable and its first
ledger landed together at commit 943c87cd9ddc7f381c8b20c316c4871c2e89707d,
so the measurement is reproducible exploratory evidence, not a fully
auditable preregistered one-shot experiment.  See the design's audit
correction before interpreting the ledger's historical field names.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Iterable

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from decompose import (  # noqa: E402
    analyze_loaded,
    attach_extra,
    defined_head,
    load_trees,
    subterms,
)
from match_signatures import (  # noqa: E402
    Parser,
    TemplateParseError,
    canonicalize,
    tokenize,
)
from measure_self_grounding import render_template  # noqa: E402

PROSE_DESIGN_COMMIT = "3fe54cf28bdbcf9870538daf888898c9b234ac21"
EXECUTABLE_LEDGER_COMMIT = "943c87cd9ddc7f381c8b20c316c4871c2e89707d"
SCHEMA = "grounded_admission.v1"
SEEDS = (20260818, 20260819, 20260820)
SOURCES = ("minif2f", "goedel_pset")
SWAPS_PER_SOURCE = 32
PAIRS_PER_SOURCE = SWAPS_PER_SOURCE * 2
THRESHOLD = 0.50

DATA = REPO / "data"
HOLDOUT = REPO / "data_holdout"
DEFAULT_OUT = REPO / "experiments" / "grounded_admission.json"


def _canonical_bytes(path: Path) -> bytes:
    """Hash text artifacts independently of the checkout's newline policy."""

    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(_canonical_bytes(path)).hexdigest()


def _tree_digest(root: Path) -> dict:
    """Digest path names and bytes for every seed-generated corpus artifact."""
    paths = sorted(root.glob("*/nodes.json"))
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(_canonical_bytes(path))
        digest.update(b"\0")
    return {"files": len(paths), "sha256": digest.hexdigest()}


def head_blind(tree: tuple) -> tuple:
    """Tree visible to the capability-blind baseline."""
    kind = tree[0]
    if kind in {"slot", "num"}:
        return tree
    head = tree[1] if kind == "rel" else "<HEAD>"
    return (kind, head, tuple(head_blind(child) for child in tree[2]))


def leaves(tree: tuple) -> tuple[tuple, ...]:
    if tree[0] in {"slot", "num"}:
        return (tree,)
    return tuple(leaf for child in tree[2] for leaf in leaves(child))


def heads(tree: tuple) -> tuple[str, ...]:
    own = (tree[1],) if tree[0] in {"call", "op"} else ()
    if tree[0] in {"slot", "num"}:
        return own
    return own + tuple(head for child in tree[2] for head in heads(child))


def replace_head(tree: tuple, path: tuple[int, ...], new_head: str) -> tuple:
    """Return ``tree`` with the applied-node head at ``path`` replaced."""
    if not path:
        if tree[0] not in {"call", "op"}:
            raise ValueError("head replacement path does not name an applied node")
        return (tree[0], new_head, tree[2])
    if tree[0] not in {"rel", "call", "op"}:
        raise ValueError("head replacement path crosses a leaf")
    index = path[0]
    children = list(tree[2])
    children[index] = replace_head(children[index], path[1:], new_head)
    return (tree[0], tree[1], tuple(children))


def changed_head_positions(authentic: tuple, foil: tuple) -> list[tuple[int, ...]]:
    """Paths where applied-node labels differ; topology must already match."""
    changed: list[tuple[int, ...]] = []

    def visit(left: tuple, right: tuple, path: tuple[int, ...]) -> None:
        if left[0] != right[0] or len(left) != len(right):
            raise ValueError("trees do not share topology")
        if left[0] in {"call", "op"} and left[1] != right[1]:
            changed.append(path)
        if left[0] in {"slot", "num"}:
            if left != right:
                raise ValueError("trees do not share leaves")
            return
        if len(left[2]) != len(right[2]):
            raise ValueError("trees do not share arity")
        for i, (lchild, rchild) in enumerate(zip(left[2], right[2])):
            visit(lchild, rchild, path + (i,))

    visit(authentic, foil, ())
    return changed


def _parse(template: str) -> tuple:
    return canonicalize(Parser(tokenize(template)).parse())


def _eligible_records(
    source_ids: list[str], trees: dict[str, tuple], seed: int
) -> list[dict]:
    records: list[dict] = []
    for sid in sorted(source_ids):
        tree = trees[sid]
        for path, sub in subterms(tree):
            if sub[0] not in {"call", "op"}:
                continue
            records.append(
                {
                    "sid": sid,
                    "path": tuple(path),
                    "kind": sub[0],
                    "head": sub[1],
                    "arity": len(sub[2]),
                }
            )
    random.Random(seed).shuffle(records)
    return records


def construct_pairs(
    source: str,
    seed: int,
    source_ids: list[str],
    trees: dict[str, tuple],
    classes: dict[str, dict[str, str]],
    corpus_of: dict[str, str],
    disciplines_of: dict[str, frozenset],
) -> list[dict]:
    """Construct the first 32 disjoint valid swaps under the prose design."""
    records = _eligible_records(source_ids, trees, seed)
    buckets: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for record in records:
        buckets[(record["kind"], record["arity"])].append(record)
    used: set[str] = set()
    swaps: list[tuple[dict, dict, tuple, tuple]] = []
    mutation_cache: dict[tuple[str, tuple[int, ...], str], tuple | None] = {}

    def mutate(record: dict, new_head: str) -> tuple | None:
        key = (record["sid"], record["path"], new_head)
        if key in mutation_cache:
            return mutation_cache[key]
        authentic = trees[record["sid"]]
        raw = replace_head(authentic, record["path"], new_head)
        if defined_head(authentic) != defined_head(raw):
            mutation_cache[key] = None
            return None
        try:
            foil = _parse(render_template(raw))
            valid = (
                head_blind(authentic) == head_blind(foil)
                and leaves(authentic) == leaves(foil)
                and changed_head_positions(authentic, foil) == [record["path"]]
                and defined_head(authentic) == defined_head(foil)
            )
        except (TemplateParseError, ValueError, ZeroDivisionError):
            valid = False
            foil = None
        mutation_cache[key] = foil if valid else None
        return mutation_cache[key]

    for left in records:
        if left["sid"] in used:
            continue
        for right in buckets[(left["kind"], left["arity"])]:
            if right["sid"] in used or right["sid"] == left["sid"]:
                continue
            if left["head"] == right["head"]:
                continue

            left_foil = mutate(left, right["head"])
            right_foil = mutate(right, left["head"])
            if left_foil is None or right_foil is None:
                continue

            swaps.append((left, right, left_foil, right_foil))
            used.update((left["sid"], right["sid"]))
            break
        if len(swaps) == SWAPS_PER_SOURCE:
            break

    if len(swaps) != SWAPS_PER_SOURCE:
        raise RuntimeError(
            f"{source} seed {seed}: constructed {len(swaps)}/{SWAPS_PER_SOURCE} "
            "required disjoint swaps"
        )

    out: list[dict] = []
    for swap_index, (left, right, left_foil, right_foil) in enumerate(swaps):
        for side, record, foil_tree, donor in (
            ("a", left, left_foil, right),
            ("b", right, right_foil, left),
        ):
            sid = record["sid"]
            out.append(
                {
                    "pair_id": f"{source}.{seed}.{swap_index:02d}.{side}",
                    "source": source,
                    "source_id": sid,
                    "foil_id": f"grounded_admission.foil.{source}.{seed}.{swap_index:02d}.{side}",
                    "path": list(record["path"]),
                    "authentic_head": record["head"],
                    "foil_head": donor["head"],
                    "authentic_tree": trees[sid],
                    "foil_tree": foil_tree,
                    "authentic_template": render_template(trees[sid]),
                    "foil_template": render_template(foil_tree),
                    "classes": dict(classes[sid]),
                    "corpus_id": corpus_of[sid],
                    "disciplines": sorted(disciplines_of[sid]),
                }
            )
    return out


def construction_checks(pairs: list[dict]) -> dict:
    authentic_heads = Counter(
        head for pair in pairs for head in heads(pair["authentic_tree"])
    )
    foil_heads = Counter(head for pair in pairs for head in heads(pair["foil_tree"]))
    pair_checks = []
    for pair in pairs:
        authentic = pair["authentic_tree"]
        foil = pair["foil_tree"]
        changed = changed_head_positions(authentic, foil)
        pair_checks.append(
            head_blind(authentic) == head_blind(foil)
            and leaves(authentic) == leaves(foil)
            and changed == [tuple(pair["path"])]
            and defined_head(authentic) == defined_head(foil)
        )
    checks = {
        # Historical ledger key retained byte-for-byte. It means that the
        # prose-stated count was met, not that this executable was registered.
        "registered_pair_count": len(pairs) == PAIRS_PER_SOURCE,
        "all_pairs_head_blind_identical": all(pair_checks),
        "batch_head_multiset_identical": authentic_heads == foil_heads,
        "blind_paired_accuracy": 0.5 if pair_checks else None,
    }
    checks["valid"] = all(
        (
            checks["registered_pair_count"],
            checks["all_pairs_head_blind_identical"],
            checks["batch_head_multiset_identical"],
            checks["blind_paired_accuracy"] == 0.5,
        )
    )
    return checks


def _extra_rows(pairs: list[dict]) -> list[dict]:
    out = []
    for pair in pairs:
        common = {
            "classes": pair["classes"],
            "discipline": pair["source"],
            "disciplines": pair["disciplines"],
        }
        out.append(
            {
                **common,
                "statement_id": pair["source_id"],
                "template": pair["authentic_template"],
                "corpus_id": pair["corpus_id"],
            }
        )
        out.append(
            {
                **common,
                "statement_id": pair["foil_id"],
                "template": pair["foil_template"],
                "corpus_id": f"grounded_admission.foil.{pair['source']}",
            }
        )
    return out


def fixed_owned_score(entry: dict, fixed_ids: set[str]) -> dict:
    """Exact grounding by any owner in the pre-candidate graph."""
    considered = int(entry["considered"])
    fixed_owned = 0
    nonfixed_only = 0
    for constituent in entry["constituents"]:
        if constituent.get("grounded_via") != "exact":
            continue
        owners = set(constituent.get("owners") or ())
        if owners & fixed_ids:
            fixed_owned += 1
        elif owners:
            nonfixed_only += 1
    score = fixed_owned / considered if considered else 0.0
    return {
        "considered": considered,
        "fixed_owned_exact": fixed_owned,
        "nonfixed_only_exact": nonfixed_only,
        "grounded_at_all": score,
        "admitted": considered > 0 and score >= THRESHOLD,
    }


def _metrics(rows: list[dict]) -> dict:
    authentic_acceptance = mean(float(row["authentic"]["admitted"]) for row in rows)
    foil_rejection = mean(float(not row["foil"]["admitted"]) for row in rows)
    pair_credit = []
    margins = []
    for row in rows:
        margin = row["authentic"]["grounded_at_all"] - row["foil"]["grounded_at_all"]
        margins.append(margin)
        pair_credit.append(1.0 if margin > 0 else 0.5 if margin == 0 else 0.0)
    return {
        "pairs": len(rows),
        "authentic_acceptance": authentic_acceptance,
        "foil_rejection": foil_rejection,
        "balanced_accuracy": (authentic_acceptance + foil_rejection) / 2,
        "paired_accuracy": mean(pair_credit),
        "mean_margin": mean(margins),
    }


def measure_seed(
    seed: int,
    fixed: tuple,
    holdout: tuple,
) -> dict:
    fixed_nodes, fixed_trees, fixed_classes, fixed_corpus, fixed_disc = fixed
    h_nodes, h_trees, h_classes, h_corpus, h_disc = holdout
    fixed_ids = set(fixed_trees)
    by_source: dict[str, list[str]] = {
        source: sorted(
            n.statement_id
            for n in h_nodes
            if h_corpus.get(n.statement_id, "").startswith(source)
        )
        for source in SOURCES
    }

    source_pairs = {
        source: construct_pairs(
            source,
            seed,
            by_source[source],
            h_trees,
            h_classes,
            h_corpus,
            h_disc,
        )
        for source in SOURCES
    }
    all_pairs = [pair for source in SOURCES for pair in source_pairs[source]]
    extras = _extra_rows(all_pairs)

    nodes = list(fixed_nodes)
    trees = dict(fixed_trees)
    classes = {sid: dict(value) for sid, value in fixed_classes.items()}
    corpus_of = dict(fixed_corpus)
    disciplines_of = dict(fixed_disc)
    if any(item["statement_id"] in fixed_ids for item in extras):
        raise RuntimeError("candidate id collides with the fixed graph")
    attach_extra(nodes, trees, classes, corpus_of, disciplines_of, extras)
    result = analyze_loaded(
        nodes,
        trees,
        classes,
        corpus_of,
        disciplines_of,
        min_family=2,
        pattern_membership=False,
    )
    entries = {row["statement_id"]: row for row in result["decompositions"]}

    out_sources = {}
    for source in SOURCES:
        rows = []
        for pair in source_pairs[source]:
            authentic = fixed_owned_score(entries[pair["source_id"]], fixed_ids)
            foil = fixed_owned_score(entries[pair["foil_id"]], fixed_ids)
            rows.append(
                {
                    "pair_id": pair["pair_id"],
                    "source_id": pair["source_id"],
                    "foil_id": pair["foil_id"],
                    "path": pair["path"],
                    "authentic_head": pair["authentic_head"],
                    "foil_head": pair["foil_head"],
                    "authentic": authentic,
                    "foil": foil,
                    "considered_topology_identical": (
                        authentic["considered"] == foil["considered"]
                    ),
                }
            )
        checks = construction_checks(source_pairs[source])
        checks["considered_topology_identical"] = all(
            row["considered_topology_identical"] for row in rows
        )
        checks["valid"] = checks["valid"] and checks["considered_topology_identical"]
        out_sources[source] = {
            "construction": checks,
            "metrics": _metrics(rows),
            "rows": rows,
        }
    return {"seed": seed, "sources": out_sources}


def adjudicate(seed_rows: list[dict]) -> dict:
    by_source = {
        source: [row["sources"][source] for row in seed_rows] for source in SOURCES
    }
    g3_fired = all(
        source_row["construction"]["valid"]
        and source_row["construction"]["blind_paired_accuracy"] == 0.5
        for rows in by_source.values()
        for source_row in rows
    )
    summary = {}
    for source, rows in by_source.items():
        summary[source] = {
            key: mean(row["metrics"][key] for row in rows)
            for key in (
                "authentic_acceptance",
                "foil_rejection",
                "balanced_accuracy",
                "paired_accuracy",
                "mean_margin",
            )
        }

    def outcome(fired: bool, *, refused: bool = False) -> dict:
        return {
            "status": "REFUSED" if refused else "FIRED" if fired else "MISSED",
            "fired": fired if not refused else None,
        }

    g1 = all(
        values["balanced_accuracy"] >= 0.70
        and values["authentic_acceptance"] > 0.50
        and values["foil_rejection"] > 0.50
        for values in summary.values()
    )
    g2 = all(values["paired_accuracy"] >= 0.75 for values in summary.values())
    g4 = all(values["mean_margin"] > 0 for values in summary.values())
    return {
        "source_means": summary,
        "G1": {
            **outcome(g1, refused=not g3_fired),
            "predicate": (
                "mean balanced_accuracy >= 0.70 and authentic acceptance > 0.50 "
                "and foil rejection > 0.50 on each source"
            ),
        },
        "G2": {
            **outcome(g2, refused=not g3_fired),
            "predicate": "mean paired_accuracy >= 0.75 on each source",
        },
        "G3": {
            **outcome(g3_fired),
            "predicate": "all construction invariants and blind baseline == 0.50",
        },
        "G4": {
            **outcome(g4, refused=not g3_fired),
            "predicate": "mean authentic-minus-foil margin > 0 on both sources",
        },
    }


def generate() -> dict:
    fixed = load_trees(DATA)
    holdout = load_trees(HOLDOUT)
    seeds = []
    for seed in SEEDS:
        print(f"[grounded-admission] seed {seed}", flush=True)
        seeds.append(measure_seed(seed, fixed, holdout))
    result = {
        "schema": SCHEMA,
        "design": "docs/DESIGN-grounded-admission.md",
        # Historical schema name: this points to the prose-only design, not
        # to a commit containing the executable protocol.
        "design_commit": PROSE_DESIGN_COMMIT,
        "threshold": THRESHOLD,
        "seeds": list(SEEDS),
        "pairs_per_source_per_seed": PAIRS_PER_SOURCE,
        "fixed_owner_scope": "data/*/nodes.json before candidates are attached",
        "pattern_membership": False,
        "source_digest_algorithm": "sha256-canonical-lf",
        "source_digests": {
            "fixed_data": _tree_digest(DATA),
            **{
                source: {
                    "path": f"data_holdout/{source}/nodes.json",
                    "sha256": _sha256(HOLDOUT / source / "nodes.json"),
                }
                for source in SOURCES
            },
        },
        "runs": seeds,
    }
    result["adjudication"] = adjudicate(seeds)
    return result


def render(result: dict) -> bytes:
    return (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def _summary(result: dict) -> dict:
    adj = result["adjudication"]
    return {
        "outcomes": {key: adj[key]["status"] for key in ("G1", "G2", "G3", "G4")},
        "source_means": adj["source_means"],
    }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="regenerate in memory and require byte identity with --out",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)
    result = generate()
    payload = render(result)
    if args.check:
        if not args.out.exists() or args.out.read_bytes() != payload:
            print(f"drift: {args.out}", file=sys.stderr)
            return 1
        print(f"byte-identical: {args.out}")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(payload)
        print(f"wrote: {args.out}")
    print(json.dumps(_summary(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
