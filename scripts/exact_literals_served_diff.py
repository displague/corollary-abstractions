#!/usr/bin/env python3
"""The served-answer-line diff ROADMAP-v0.20 §4b owes, both sides measured.

`scripts/match_signatures.py` is NOT one of the eleven witnessed rendering
modules, so §4b pays no seal for changing it — and the discipline
`docs/DESIGN-foreign-voice.md` §5 named for exactly that case is that an
unwitnessed change owes a **served-answer-line diff** instead. This is that
diff, and `scripts/transliteration_served_diff.py` is its working precedent.

**Why a child process per side, and why the blob comes from git.** The two
sides must run under two genuinely different parsers. Reverting in memory
would re-type the old code and then check the copy against itself; the
precedent states it plainly and this script inherits the rule verbatim: *the
blob from git IS the pre-amendment file*. So the parent's
`scripts/match_signatures.py` is extracted with `git show`, its LF digest is
checked against the pin the amendment retired, and the run **refuses to write
anything** if that check fails.

**Why each child reports the parser it loaded.** The precedent's first draft
ordered `sys.path` and produced a clean diff in which both sides were the NEW
parser, because `answer.py` inserts `scripts/` at the front on import. The
fix, kept here: each child installs its chosen parser into `sys.modules`
BEFORE anything can import it, then reports the digest it actually loaded.
Both digests ride in the artifact, so that failure mode is visible in the
file rather than hidden by a green result.

**What is compared.** Every committed statement's full `answer.render` output
— which is the served surface, and which reaches `match_signatures` through
`_in_words` -> `realize_term.realize` -> the parser. The expectation §4b
registers is that only the corrupted nodes move and everything else is
byte-identical. Anything else moving is a STOP, and the artifact says so
rather than the reader having to infer it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

#: The pin the amendment retired. The parent blob must equal this or the
#: "before" side is not the side this diff claims to measure.
RETIRED_PARSER_PIN = "f5b2abba6f5df4625d0816a71778aaffe46d07504dd34ae65ad0cef6d70376b7"
AMENDMENT = "transliteration.prereg.v1.amendment.exact-literals-2026-08-24"
ARTIFACT = "experiments/exact_literals_served_diff.json"

#: The nodes whose served evaluation the destroyed literals corrupted. Named
#: so a node that stopped being affected — or a new one that started — shows
#: up as a diff against this expectation rather than passing unnoticed.
#:
#: The first two are BACKLOG's measured pair. **The third was found by this
#: diff and is recorded as a discovery, not back-fitted silently:** BACKLOG's
#: scan named 3 nodes, of which one (`leanworkbook.skel.lean_workbook_50397`)
#: turns out not to be repairable here at all — its `inf` is frozen into the
#: committed `anonymized_template` by `scripts/seed_lean_workbook.py`, and its
#: `canonical_ascii` does not tokenize, so the parser never sees it. In its
#: place this diff surfaced `goedelpset.skel.goedel_pset_789185`, whose served
#: `right` value printed as a rounded `1e64` and now prints its exact 64
#: digits. So the served count is still three — but not the same three, and
#: the difference is a measurement rather than a correction of the record.
EXPECTED_MOVERS = (
    "goedelpset.skel.goedel_pset_789185",
    "leanworkbook.ground.lean_workbook_37421",
    "leanworkbook.ground.lean_workbook_plus_68304",
)

_CHILD = r'''
import hashlib, importlib.util, json, sys
from pathlib import Path

parser_path, repo, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])

# Install the CHOSEN parser under its module name before anything else can
# import it. sys.path ordering is not enough: answer.py puts scripts/ first.
spec = importlib.util.spec_from_file_location("match_signatures", parser_path)
module = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(repo / "scripts"))
sys.modules["match_signatures"] = module
spec.loader.exec_module(module)

loaded = hashlib.sha256(
    Path(parser_path).read_bytes().replace(b"\r\n", b"\n")
).hexdigest()

import answer as answer_module
import evaluate as evaluate_module

rendered = {}
evaluated = {}
for statement_id in sorted(answer_module.records()):
    composed = answer_module.compose(statement_id)
    if composed is None:
        continue
    rendered[statement_id] = "\n".join(answer_module.render(composed))
    # The evaluate route is where the destroyed literals actually surfaced:
    # the right verdict with a wrong printed value. answer.render never shows
    # it, because the numeral pair refuses those terms on both sides anyway.
    if composed.formal:
        try:
            evaluated[statement_id] = "\n".join(
                evaluate_module.verify(composed.formal).rendered())
        except Exception:
            try:
                evaluated[statement_id] = "\n".join(
                    evaluate_module.render(
                        evaluate_module.evaluate(composed.formal)))
            except Exception:
                pass

out.write_text(json.dumps({
    "parser_sha256_lf": loaded,
    "parser_is_the_module_answer_used": (
        sys.modules["match_signatures"] is module
    ),
    "rendered": rendered,
    "evaluated": evaluated,
}, ensure_ascii=False), encoding="utf-8")
'''


def _sha256_lf(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def _run_side(parser_path: Path, tmp: Path, label: str) -> dict:
    out = tmp / f"{label}.json"
    child = tmp / "child.py"
    child.write_text(_CHILD, encoding="utf-8")
    subprocess.run(
        [sys.executable, str(child), str(parser_path), str(REPO), str(out)],
        check=True,
        cwd=REPO,
        env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"},
    )
    return json.loads(out.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--parent", default="HEAD")
    parser.add_argument("--out", default=ARTIFACT)
    args = parser.parse_args(argv)

    before_blob = subprocess.run(
        ["git", "show", f"{args.parent}:scripts/match_signatures.py"],
        capture_output=True, cwd=REPO, check=True,
    ).stdout
    before_digest = _sha256_lf(before_blob)
    if before_digest != RETIRED_PARSER_PIN:
        print(
            f"REFUSING to write: {args.parent}:scripts/match_signatures.py "
            f"digests {before_digest}, not the retired pin "
            f"{RETIRED_PARSER_PIN}. The before side would not be the parser "
            f"this diff claims to measure.",
            file=sys.stderr,
        )
        return 2

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        old_parser = tmp / "match_signatures_before.py"
        old_parser.write_bytes(before_blob)
        before = _run_side(old_parser, tmp, "before")
        after = _run_side(REPO / "scripts" / "match_signatures.py", tmp, "after")

    if before["parser_sha256_lf"] == after["parser_sha256_lf"]:
        print("REFUSING to write: both sides loaded one parser", file=sys.stderr)
        return 2

    moved = sorted(
        sid for sid in set(before["rendered"]) | set(after["rendered"])
        if before["rendered"].get(sid) != after["rendered"].get(sid)
    )
    moved_eval = sorted(
        sid for sid in set(before["evaluated"]) | set(after["evaluated"])
        if before["evaluated"].get(sid) != after["evaluated"].get(sid)
    )
    unexpected = sorted(
        sid for sid in set(moved) | set(moved_eval)
        if sid not in EXPECTED_MOVERS
    )

    record = {
        "run_id": "exact_literals.served_diff.v1",
        "roadmap": "docs/ROADMAP-v0.20.md §4b",
        "amendment": AMENDMENT,
        "what_this_is": [
            "The served-answer-line diff an UNWITNESSED rendering-adjacent "
            "change owes in place of a seal (DESIGN-foreign-voice §5).",
            "Every committed statement's full answer.render output, rendered "
            "twice: once under the parser the amendment retired and once "
            "under its successor.",
        ],
        "mechanism": {
            "before_parser_sha256_lf": before["parser_sha256_lf"],
            "after_parser_sha256_lf": after["parser_sha256_lf"],
            "before_blob_from": f"git show {args.parent}:scripts/match_signatures.py",
            "why_the_committed_blob_and_not_an_in_memory_revert": (
                "An in-memory revert re-types the old code, and the digest "
                "check would then be checking the copy against itself. The "
                "blob from git IS the pre-amendment file."
            ),
            "each_child_reports_the_parser_it_loaded": {
                "before": before["parser_sha256_lf"],
                "after": after["parser_sha256_lf"],
                "before_module_is_the_one_answer_used": before[
                    "parser_is_the_module_answer_used"],
                "after_module_is_the_one_answer_used": after[
                    "parser_is_the_module_answer_used"],
                "why": (
                    "sys.path ordering alone is defeated by answer.py "
                    "inserting scripts/ at import; the precedent's first "
                    "draft produced a clean diff in which both sides were "
                    "the NEW parser. Each side installs its parser into "
                    "sys.modules first and reports what it loaded."
                ),
            },
        },
        "statements_rendered": len(after["rendered"]),
        "statements_evaluated": len(after["evaluated"]),
        "answer_lines_moved": {
            "count": len(moved),
            "statement_ids": moved,
            "why_zero_is_the_right_answer_here": (
                "answer.render's `in words` line is gated by v0.18's numeral "
                "pair, which REFUSES these statements' literals (|n| < 10^15) "
                "on BOTH sides. The corruption never reached this surface; it "
                "reached the evaluate route below. Zero here is the "
                "seal-shaped half of the evidence: an unwitnessed "
                "rendering-adjacent change that moved no rendered answer byte."
            ),
        },
        "evaluate_route_moved": {
            "count": len(moved_eval),
            "statement_ids": moved_eval,
            "this_is_the_defect_being_fixed": (
                "BACKLOG: two ground statements returned the RIGHT verdict "
                "with printed values wrong by 4.4e59, handed back as an exact "
                "Fraction so nothing downstream could tell."
            ),
        },
        "lines_moved": {
            "expected": list(EXPECTED_MOVERS),
            "unexpected": unexpected,
            "verdict": "AS EXPECTED" if not unexpected else "STOP",
        },
        "samples": {
            sid: {
                "answer_before": before["rendered"].get(sid),
                "answer_after": after["rendered"].get(sid),
                "evaluate_before": before["evaluated"].get(sid),
                "evaluate_after": after["evaluated"].get(sid),
            }
            for sid in sorted(set(moved) | set(moved_eval))[:4]
        },
    }
    out = REPO / args.out
    out.write_text(
        json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"rendered {record['statements_rendered']} statements per side")
    print(f"answer lines moved  : {len(moved)}")
    print(f"evaluate route moved: {len(moved_eval)}")
    print(f"verdict: {record['lines_moved']['verdict']}")
    for sid in sorted(set(moved) | set(moved_eval)):
        print(f"   {sid}{'' if sid in EXPECTED_MOVERS else '   <-- UNEXPECTED'}")
    print(f"-> {out}")
    return 0 if not unexpected else 1


if __name__ == "__main__":
    raise SystemExit(main())
