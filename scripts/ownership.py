#!/usr/bin/env python3
"""Exact ownership lookup: which statements host this subterm?

The project's wager is that anything with an exact answer lives outside the
weights. "Which statements contain this part, and who are they?" is exactly
that kind of question — a lookup over committed templates, decided by the
same canonicaliser and skeleton function the matcher already uses. No model,
no ranker, no scoring, no English understanding.

This module exists so a typed line can end **solved** for the first time.
Before it, every line the live session accepted ended `REFUSED` (write gate)
or `exhausted` (dispatcher): honest, and a dead end for the thesis. A person
who can ask who owns a part has a reason to care about the graph before
proposing a write against it.

## Why this is not a parser

The query grammar is a literal command word followed by a template
expression: `owns <expr>`. The expression is handed to
`match_signatures.tokenize` / `Parser` — the *same* front end that reads
every committed `anonymized_template` — and canonicalised the same way. If
it does not parse as a template, the lookup refuses and says so. Nothing
here interprets English, guesses intent, or fills a slot.

## What "owns" means here

A statement **hosts** a subterm when some non-leaf subtree of its template
has the same skeleton as the query, where `skeleton` is the matcher's own
slot-position abstraction. So `x^2` and `y^2` are the same part, and that is
the same equivalence the self-grounding measurement uses when it asks who
owns a constituent. This is deliberately *hosting*, not the measurement's
"most independent owner": hosting is the exact, total fact, and the owner
ranking is a further judgement the measurement makes for its own purpose.

The answer is grouped by corpus so a reader can see immediately whether a
part belongs to the hand-authored layer or to an ingested one — which, after
v0.12's holdout result, is the distinction that actually matters.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from decompose import load_trees, subterms  # noqa: E402
from match_signatures import (  # noqa: E402
    Parser,
    TemplateParseError,
    canonicalize,
    skeleton,
    template_slots,
    tokenize,
)

#: The boot-matrix subsystem this lookup is a capability of. It reads the
#: committed corpus graph and nothing else, so if that subsystem did not
#: register, the lookup must refuse rather than answer from somewhere else.
REQUIRES_SUBSYSTEM = "corpus.nodes"

#: The one command word. A line must begin with it to reach this route.
COMMAND = "owns"


class QueryError(ValueError):
    """The query text is not a template expression."""


@dataclass(frozen=True)
class Ownership:
    """The exact answer, as data."""

    query: str
    query_skeleton: str
    hosts: tuple[str, ...]
    by_corpus: tuple[tuple[str, int], ...]
    searched: int

    @property
    def found(self) -> bool:
        return bool(self.hosts)


def parse_query(text: str) -> tuple[tuple, str]:
    """`x^2` -> (tree, skeleton), using the matcher's own front end."""
    try:
        tree = canonicalize(Parser(tokenize(text)).parse())
    except TemplateParseError as exc:
        raise QueryError(f"not a template expression: {exc}") from None
    except (ValueError, IndexError) as exc:
        raise QueryError(f"not a template expression: {exc}") from None
    if tree[0] not in {"op", "call"}:
        # A bare slot or numeral is every statement's subterm and no
        # statement's part. Refusing is more useful than answering 12,777.
        raise QueryError(
            "query must be a compound term (an operator or a call), not a "
            "bare variable or numeral"
        )
    # A typed query carries no `slot_schema`, so every slot is read as the
    # variable class -- the class committed skeletons already print as `?0:V`.
    # This is a stated convention, not an inference: a query cannot ask about
    # a parameter-class slot, and `render` prints the skeleton it searched for
    # so the reader can see exactly what was matched.
    classes = {name: "V" for name in template_slots(tree)}
    return tree, skeleton(tree, classes)


def lookup(query: str, data_dir: Path | None = None) -> Ownership:
    """Every statement hosting `query` as a subterm. Exact, total, unranked."""
    root = data_dir or (REPO / "data")
    nodes, trees, classes, corpus_of, _disc = load_trees(root)
    _tree, want = parse_query(query)

    hosts: list[str] = []
    per_corpus: dict[str, int] = defaultdict(int)
    for node in nodes:
        tree = trees.get(node.statement_id)
        if tree is None:
            continue
        node_classes = classes[node.statement_id]
        for _path, sub in subterms(tree):
            if skeleton(sub, node_classes) == want:
                hosts.append(node.statement_id)
                per_corpus[corpus_of.get(node.statement_id, "?")] += 1
                break
    return Ownership(
        query=query,
        query_skeleton=want,
        hosts=tuple(sorted(hosts)),
        by_corpus=tuple(sorted(per_corpus.items(), key=lambda kv: (-kv[1], kv[0]))),
        searched=len(nodes),
    )


def render(answer: Ownership, *, sample: int = 5) -> list[str]:
    """The answer a person reads. Counts first, then named witnesses."""
    if not answer.found:
        return [
            f"no statement in the graph hosts {answer.query!r}",
            f"searched  : {answer.searched} statements",
            f"skeleton  : {answer.query_skeleton}",
        ]
    lines = [
        f"{len(answer.hosts)} of {answer.searched} statements host "
        f"{answer.query!r}",
        f"skeleton  : {answer.query_skeleton}",
    ]
    for corpus, count in answer.by_corpus[:8]:
        lines.append(f"  {count:>6}  {corpus}")
    if len(answer.by_corpus) > 8:
        lines.append(f"  ... {len(answer.by_corpus) - 8} more corpora")
    for sid in answer.hosts[:sample]:
        lines.append(f"  e.g. {sid}")
    return lines


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("query", help="a template expression, e.g. 'x ^ 2'")
    args = ap.parse_args(argv)
    try:
        answer = lookup(args.query)
    except QueryError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print("\n".join(render(answer)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
