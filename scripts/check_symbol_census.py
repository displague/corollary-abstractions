#!/usr/bin/env python3
"""Check `experiments/symbol_census.json` against a fresh recomputation.

B2's structure, in the design's own words: *"the census **checker**, a
separate invocation, proves the artifact matches a fresh recomputation — two
sides, two programs, so a mismatch can actually go red."*

## Why this is a second program and not `--check` on the builder

A `--check` mode inside the builder compares the artifact against the
builder's own idea of the corpus. That catches a hand-edited artifact and a
moved corpus, which is most of the value — but it cannot catch a **builder**
that started extracting the wrong thing, because the thing it compares
against is the builder. This file therefore re-derives every member from the
committed sources **without importing the builder**, and the test suite
asserts the two agree. A divergence between the two extractions is a red,
not a silently shared bug.

The independence is real but it is bounded, and the bound is stated rather
than implied: both programs read the same corpus with the same loader
convention and both consume `match_signatures`' own constants, because those
ARE the ground truth — a "second opinion" that guessed at `BIG_OP_PREFIXES`
would be checking a copy instead of the parser. What is genuinely
independent is the extraction: the builder walks the parsed trees with an
explicit stack and this side walks them by recursive descent, and each
derives the leading identifiers with its own matcher and assembles the union
in its own order. A traversal bug in one shape is not a traversal bug in the
other, which is the specific thing two programs buy here.

## What a red means

Exactly one of four things, and the report says which: the artifact was
hand-edited (a DESIGN §9 stop condition), the corpus moved, the shipped
parser's constants moved, or the two extractions disagree. The first is a
stop; the middle two are a re-generate; the last is a defect in one of two
named files.

Usage::

    python scripts/check_symbol_census.py
    python scripts/check_symbol_census.py experiments/symbol_census.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

from match_signatures import (
    BIG_OP_PREFIXES,
    COMMUTATIVE_CALL_HEADS,
    HEAD_ALIASES,
    Parser,
    tokenize,
)

REPO = Path(__file__).resolve().parents[1]

ARTIFACT = "experiments/symbol_census.json"
BUILDER = "scripts/build_symbol_census.py"
SCHEMA = "corollary.symbol-census/1"

_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
_LEAD = re.compile(r"^[a-z][a-z0-9_]*")

_LEXICON = (
    ("symbols", "symbol"),
    ("operators", "symbol"),
    ("functionals", "notation"),
    ("constants", "symbol"),
    ("index_sets", "notation"),
)


class CensusMismatch(RuntimeError):
    """The committed census is not what the sources say it should be."""


def _normalize(raw: str) -> str:
    return unicodedata.normalize("NFC", raw).casefold()


def _walk_heads(node, out: set[str]) -> None:
    """Recursive descent — deliberately a different traversal from the
    builder's explicit stack, so a bug in one shape is not a bug in both."""

    if not isinstance(node, tuple):
        return
    if node and node[0] == "call" and len(node) == 3:
        out.add(node[1])
    for item in node:
        if isinstance(item, tuple):
            _walk_heads(item, out)
        elif isinstance(item, (list, set)):
            for child in item:
                _walk_heads(child, out)


def recompute(repo: Path) -> dict:
    """Every census member, re-derived from the committed sources."""

    lexicon: dict[str, set[str]] = {f"symbol_lexicon.{c}": set() for c, _ in _LEXICON}
    heads: set[str] = set()
    templates = 0
    corpus = sorted((repo / "data").glob("*/nodes.json"))

    for path in corpus:
        document = json.loads(path.read_text(encoding="utf-8"))
        for node in document.get("statement_nodes", []):
            entries = node.get("symbol_lexicon") or {}
            for category, key in _LEXICON:
                bucket = lexicon[f"symbol_lexicon.{category}"]
                for entry in entries.get(category) or []:
                    value = entry.get(key)
                    if isinstance(value, str) and value:
                        bucket.add(value)
            template = (node.get("structural_signature") or {}).get(
                "anonymized_template"
            )
            if template:
                templates += 1
                _walk_heads(Parser(tokenize(template)).parse(), heads)

    leading = set()
    for notation in lexicon["symbol_lexicon.functionals"]:
        found = _LEAD.match(_normalize(notation))
        if found:
            leading.add(found.group(0))

    raw = dict(lexicon)
    raw["functional_leading_identifiers"] = leading
    raw["anonymized_template_call_heads"] = heads
    raw["head_aliases_keys"] = set(HEAD_ALIASES)
    raw["head_aliases_targets"] = set(HEAD_ALIASES.values())
    raw["commutative_call_heads"] = set(COMMUTATIVE_CALL_HEADS)

    shaped = {
        source: sorted(
            {n for member in members if _NAME.match(n := _normalize(member))}
        )
        for source, members in raw.items()
    }
    equality = sorted(set().union(*shaped.values()))

    return {
        "equality_members": equality,
        "members_by_source": shaped,
        "raw_members_by_source": {
            source: sorted(members) for source, members in raw.items()
        },
        "prefixes": sorted(BIG_OP_PREFIXES),
        "templates_parsed": templates,
        "corpus_files": len(corpus),
    }


def compare(committed: dict, fresh: dict) -> list[str]:
    """Every disagreement, named. An empty list is the green."""

    problems: list[str] = []

    if committed.get("schema") != SCHEMA:
        problems.append(
            f"schema is {committed.get('schema')!r}, expected {SCHEMA!r}"
        )

    for key in ("equality_members",):
        left = list(committed.get(key) or [])
        right = fresh[key]
        if left != right:
            missing = sorted(set(right) - set(left))
            extra = sorted(set(left) - set(right))
            problems.append(
                f"{key}: committed has {len(left)}, fresh has {len(right)}"
                + (f"; absent from the artifact: {missing[:12]}" if missing else "")
                + (f"; in the artifact but not the sources: {extra[:12]}" if extra else "")
            )

    for key in ("members_by_source", "raw_members_by_source"):
        left = committed.get(key) or {}
        right = fresh[key]
        if set(left) != set(right):
            problems.append(
                f"{key}: sources differ — committed {sorted(set(left))}, "
                f"fresh {sorted(set(right))}"
            )
            continue
        for source in sorted(right):
            if list(left.get(source) or []) != right[source]:
                problems.append(
                    f"{key}.{source}: committed "
                    f"{len(left.get(source) or [])} members, fresh "
                    f"{len(right[source])}"
                )

    guard = committed.get("prefix_guard") or {}
    if list(guard.get("prefixes") or []) != fresh["prefixes"]:
        problems.append(
            f"prefix_guard.prefixes: committed {guard.get('prefixes')!r}, "
            f"fresh {fresh['prefixes']!r} (the shipped parser's BIG_OP_PREFIXES)"
        )
    overlap = [p for p in fresh["prefixes"] if p in set(fresh["equality_members"])]
    if list(guard.get("prefixes_that_are_also_equality_members") or []) != overlap:
        problems.append(
            "prefix_guard.prefixes_that_are_also_equality_members is stale"
        )

    counts = committed.get("counts") or {}
    for key, value in (
        ("equality_members", len(fresh["equality_members"])),
        ("prefix_guard_entries", len(fresh["prefixes"])),
        ("templates_parsed", fresh["templates_parsed"]),
        ("corpus_files", fresh["corpus_files"]),
    ):
        if counts.get(key) != value:
            problems.append(
                f"counts.{key}: committed {counts.get(key)!r}, fresh {value!r}"
            )

    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", nargs="?", default=ARTIFACT)
    args = parser.parse_args()

    path = REPO / args.artifact
    if not path.is_file():
        print(f"MISSING: {args.artifact} does not exist", file=sys.stderr)
        return 1

    committed = json.loads(path.read_text(encoding="utf-8"))
    fresh = recompute(REPO)
    problems = compare(committed, fresh)

    if problems:
        print(f"DRIFT: {args.artifact} disagrees with a fresh recomputation")
        for problem in problems:
            print(f"  - {problem}")
        print(
            "\nExactly one of four things happened: the artifact was "
            "hand-edited (a DESIGN-house-rules §9 stop condition), the corpus "
            f"moved, the parser's constants moved, or {BUILDER} and this "
            "checker disagree. Re-generate with the builder only after "
            "deciding which."
        )
        return 1

    print(
        f"CENSUS OK: {args.artifact} reproduces from source — "
        f"{len(fresh['equality_members'])} equality members over "
        f"{fresh['templates_parsed']} templates, "
        f"{len(fresh['prefixes'])} prefix-guard entries"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
