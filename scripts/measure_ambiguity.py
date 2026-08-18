#!/usr/bin/env python3
"""Adjudicate A1 over every registered in-corpus query.

`docs/DESIGN-ambiguity-and-context.md` registered A1 before this measurement:
at least 25% of the development and holdout queries whose registered
expectation is ``resolve`` end in ASK rather than BIND.  The denominator is
the complete registered in-corpus population.  PASS is therefore counted,
not silently removed: it is a coverage failure, but it is still one of the
questions A1 promised to measure.

The first implementation conditioned on BIND + ASK and reported 16 / 59 =
0.2712.  Review found three registered holdout-1 queries ending in PASS.  The
reviewed adjudication is 16 / 62 = 0.2581: still FIRED, but more narrowly.
Both numbers remain in the public ledgers rather than rewriting the first.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import sys
from pathlib import Path
from typing import Callable, Iterable

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from resolver import ASK, BIND, PASS, GraphIndex, Resolution  # noqa: E402
from resolver import default_index, resolve  # noqa: E402

DEFAULT_OUT = REPO / "experiments" / "ambiguity_rate.json"
THRESHOLD = 0.25
QUERY_SETS = (
    ("development", "text_resolution_queries.json"),
    ("holdout_1", "text_resolution_holdout.json"),
    ("holdout_2", "text_resolution_holdout2.json"),
)
RESOLVER_SOURCES = (
    "scripts/measure_ambiguity.py",
    "scripts/resolver.py",
    "scripts/decompose.py",
    "scripts/match_signatures.py",
)
REGISTERED_EXPECTATIONS = frozenset({"resolve", "refuse", "compute", "define"})


def _sha256_text(path: Path) -> str:
    """Hash canonical LF text so Git checkout policy cannot move the pin."""
    text = path.read_text(encoding="utf-8")
    canonical = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _manifest_digest(entries: dict[str, str]) -> str:
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_query_sets(
    query_root: Path,
    query_sets: Iterable[tuple[str, str]],
) -> tuple[dict[str, list[dict]], dict[str, str]]:
    loaded: dict[str, list[dict]] = {}
    digests: dict[str, str] = {}
    for name, filename in query_sets:
        path = query_root / filename
        if not path.is_file():
            raise FileNotFoundError(f"registered query set is missing: {path}")
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"cannot read registered query set {path}: {exc}") from exc
        if not isinstance(document, dict) or not isinstance(
            document.get("queries"), list
        ):
            raise ValueError(f"registered query set has no queries list: {path}")
        queries = document["queries"]
        for position, query in enumerate(queries):
            if not isinstance(query, dict):
                raise ValueError(f"{path}: query {position} is not an object")
            if not isinstance(query.get("text"), str) or not query["text"].strip():
                raise ValueError(f"{path}: query {position} has invalid text")
            if query.get("expect") not in REGISTERED_EXPECTATIONS:
                raise ValueError(f"{path}: query {position} has invalid expectation")
        if name in loaded:
            raise ValueError(f"duplicate registered query-set name: {name}")
        loaded[name] = queries
        digests[path.relative_to(REPO).as_posix() if path.is_relative_to(REPO)
                else filename] = _sha256_text(path)
    if not loaded:
        raise ValueError("no registered query sets were supplied")
    return loaded, digests


def _provenance(query_digests: dict[str, str]) -> dict:
    source_digests = {
        name: _sha256_text(REPO / name) for name in RESOLVER_SOURCES
    }
    corpus_paths = sorted((REPO / "data").glob("*/nodes.json"))
    corpus_paths += sorted((REPO / "data_holdout").glob("*/nodes.json"))
    if not corpus_paths:
        raise FileNotFoundError("no corpus nodes.json files found")
    corpus_digests = {
        path.relative_to(REPO).as_posix(): _sha256_text(path)
        for path in corpus_paths
    }
    complete_manifest = {
        **{f"query:{k}": v for k, v in query_digests.items()},
        **{f"source:{k}": v for k, v in source_digests.items()},
        **{f"corpus:{k}": v for k, v in corpus_digests.items()},
    }
    return {
        "algorithm": "sha256",
        "query_files": query_digests,
        "resolver_sources": source_digests,
        "corpus_nodes": {
            "files": len(corpus_digests),
            "manifest_sha256": _manifest_digest(corpus_digests),
        },
        "measurement_inputs_sha256": _manifest_digest(complete_manifest),
    }


def measure(
    index: GraphIndex,
    query_sets: dict[str, list[dict]],
    resolver: Callable[[str, GraphIndex], Resolution] = resolve,
) -> dict:
    per_set: dict[str, dict] = {}
    all_sizes: list[int] = []
    totals = {BIND: 0, ASK: 0, PASS: 0}

    for name, queries in query_sets.items():
        counts = {BIND: 0, ASK: 0, PASS: 0}
        sizes: list[int] = []
        ask_examples: list[dict] = []
        registered = 0
        for query in queries:
            if query["expect"] != "resolve":
                continue
            registered += 1
            outcome = resolver(query["text"], index)
            if outcome.kind not in counts:
                raise ValueError(
                    f"unexpected resolver outcome {outcome.kind!r} for "
                    f"{name}: {query['text']!r}"
                )
            counts[outcome.kind] += 1
            if outcome.kind == ASK:
                sizes.append(len(outcome.candidates))
                if len(ask_examples) < 8:
                    ask_examples.append({
                        "text": query["text"],
                        "candidates": len(outcome.candidates),
                        "resolver": outcome.resolver,
                    })
        if sum(counts.values()) != registered:
            raise AssertionError(f"outcome accounting drifted for {name}")
        per_set[name] = {
            "registered_resolve_queries": registered,
            "bind": counts[BIND],
            "ask": counts[ASK],
            "pass": counts[PASS],
            "ask_rate": round(counts[ASK] / registered, 4) if registered else None,
            "ask_candidates_median": statistics.median(sizes) if sizes else None,
            "ask_candidates_max": max(sizes) if sizes else None,
            "ask_examples": ask_examples,
        }
        all_sizes.extend(sizes)
        for kind in totals:
            totals[kind] += counts[kind]

    registered = sum(totals.values())
    if not registered:
        raise ValueError("registered query sets contain no expect=resolve queries")
    rate = totals[ASK] / registered
    return {
        "schema": "ambiguity_rate.v2",
        "design": "docs/DESIGN-ambiguity-and-context.md",
        "measure": "ASK / all registered expect=resolve queries",
        "graph_nodes": index.size,
        "pooled": {
            "registered_resolve_queries": registered,
            "bind": totals[BIND],
            "ask": totals[ASK],
            "pass": totals[PASS],
            "ask_rate": round(rate, 4),
        },
        "unregistered_probe": {
            "note": "A1 asks IF ambiguity happens; tractability is A2's",
            "ask_candidates_median": statistics.median(all_sizes)
            if all_sizes else None,
            "ask_candidates_max": max(all_sizes) if all_sizes else None,
            "ask_sets_of_two_or_three": sum(1 for size in all_sizes if size <= 3),
            "ask_sets_over_ten": sum(1 for size in all_sizes if size > 10),
        },
        "per_set": per_set,
        "adjudication": {
            "A1": {
                "fired": rate >= THRESHOLD,
                "ask_rate": round(rate, 4),
                "threshold": THRESHOLD,
                "ask": totals[ASK],
                "of": registered,
            }
        },
        "review_correction": {
            "initial_rate": 0.2712,
            "initial_denominator": "BIND + ASK only (16 / 59)",
            "correction": "include all registered expect=resolve queries",
        },
    }


def run(out_path: Path) -> dict:
    query_sets, query_digests = _load_query_sets(
        REPO / "experiments", QUERY_SETS
    )
    result = measure(default_index(), query_sets)
    result["provenance"] = _provenance(query_digests)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    result = run(args.out)
    print(json.dumps({
        "A1": result["adjudication"]["A1"],
        "pooled": result["pooled"],
        "candidate_sizes": result["unregistered_probe"],
        "per_set": {
            name: {
                "ask": values["ask"],
                "bind": values["bind"],
                "pass": values["pass"],
                "rate": values["ask_rate"],
            }
            for name, values in result["per_set"].items()
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
