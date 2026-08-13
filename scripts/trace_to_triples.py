"""Turn one `ExtractData` AST dump into committed transition rows.

`prover/ExtractData.win.lean` (the patched LeanDojo tracer, provenance in
`prover/PHASE1_NOTES.md`) writes `.lake/build/ir/<Module>.ast.json`, which
records tactics as **byte offsets into the source, not text**, and does not
record which theorem a tactic belongs to. Both gaps have to be closed the
same way every time, and until now the closing was a snippet pasted out of
the notes for each trace — so the two committed artifacts in the repo were
produced by code that no longer existed anywhere. This is that code, kept.

What it does NOT do, deliberately: invent, reorder, or normalise anything.
Every row's `tactic` is a byte slice of the pinned source, and `stateBefore`
/ `stateAfter` are the tracer's own strings. The output is the artifact a
`verified_by` link resolves against, so a "helpful" transformation here would
be a transformation nothing downstream could see.

Usage:
    python scripts/trace_to_triples.py \
        --ast   prover/lean/session/.lake/build/ir/Session22080.ast.json \
        --source prover/lean/session/Session22080.lean \
        --out   prover/session_triples.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# The notes' guard: no state in the committed corpora has come close, but a
# runaway state would bloat an artifact every consumer reads eagerly.
MAX_STATE = 4000

_DECL = re.compile(r"^(?:theorem|lemma)\s+([A-Za-z_][\w']*)", re.M)


def declarations(source_text: str) -> list[tuple[int, str]]:
    """(byte offset, name) for every theorem/lemma, in source order."""

    return sorted(
        (len(source_text[: match.start()].encode("utf-8")), match.group(1))
        for match in _DECL.finditer(source_text)
    )


def owning_declaration(decls: list[tuple[int, str]], offset: int) -> str:
    """The declaration a tactic at `offset` belongs to.

    Attribution is positional because the AST does not carry it: the owner is
    the LAST declaration that starts at or before the tactic. A tactic before
    any declaration is a tracer bug, not something to guess about.
    """

    owner = None
    for start, name in decls:
        if start <= offset:
            owner = name
        else:
            break
    if owner is None:
        raise ValueError(f"tactic at byte {offset} precedes every declaration")
    return owner


def triples(ast: dict, source_bytes: bytes, source_text: str) -> list[dict]:
    decls = declarations(source_text)
    if not decls:
        raise ValueError("no theorem/lemma declarations in the pinned source")
    rows: list[dict] = []
    for tactic in ast.get("tactics", []):
        start = tactic["pos"]["byteIdx"]
        end = tactic["endPos"]["byteIdx"]
        before = tactic["stateBefore"]
        after = tactic["stateAfter"]
        for label, state in (("stateBefore", before), ("stateAfter", after)):
            if len(state) > MAX_STATE:
                raise ValueError(
                    f"{label} at byte {start} is {len(state)} chars, over the "
                    f"{MAX_STATE} guard; widen it deliberately or split the proof"
                )
        rows.append(
            {
                "theorem": owning_declaration(decls, start),
                "tactic": source_bytes[start:end].decode("utf-8"),
                "stateBefore": before,
                "stateAfter": after,
            }
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ast", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)

    ast = json.loads(args.ast.read_text(encoding="utf-8"))
    source_bytes = args.source.read_bytes()
    rows = triples(ast, source_bytes, source_bytes.decode("utf-8"))
    if not rows:
        print("no tactics extracted — refusing to write an empty artifact",
              file=sys.stderr)
        return 1
    # LF, and the same indent the existing artifacts use, so the digest a
    # manifest pins is stable across platforms (.gitattributes pins eol=lf).
    payload = json.dumps(rows, ensure_ascii=False, indent=1) + "\n"
    args.out.write_bytes(payload.encode("utf-8"))
    print(f"{len(rows)} transition rows -> {args.out}")
    for row in rows:
        print(f"  {row['theorem']}: {row['tactic']!r} -> {row['stateAfter']!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
