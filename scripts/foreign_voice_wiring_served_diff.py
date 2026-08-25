#!/usr/bin/env python3
"""Write `experiments/foreign_voice_wiring_served_diff.json` — 4d's evidence.

DESIGN-voice-completion §5.1 states 4d's obligation precisely because it is
unusual: the foreign `in words` line shown **absent on both sides at batch
time**, because no run has armed it yet, and present only after a clean run
lands. The absent/absent half is not a null result — it is the proof that a
witnessed-module change moved no served byte, which is exactly what the seal
discipline asks a witnessed change to demonstrate.

This is that artifact's writer, committed on the precedent 4a and 4b set
(adversarial review, M3: the artifact existed with no `writer` field and no
program behind it, which makes it a number nobody can reproduce).

Both sides render every committed statement's full `answer.render` output in
a CHILD interpreter rooted at its own git worktree, so "before" is the
committed renderer rather than this one with the wiring disabled.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ARTIFACT = "experiments/foreign_voice_wiring_served_diff.json"

_CHILD = r'''
import json, sys
from pathlib import Path

repo, out = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(repo / "scripts"))
import answer as a

rendered = {}
for statement_id in sorted(a.records()):
    composed = a.compose(statement_id)
    if composed is None:
        continue
    rendered[statement_id] = "\n".join(a.render(composed))

try:
    from foreign_voice_arming import arming_state

    armed = bool(arming_state(repo)["armed"])
    reason = arming_state(repo)["reason"]
except Exception as exc:
    armed, reason = False, f"no arming module on this side ({type(exc).__name__})"

out.write_text(json.dumps({
    "rendered": rendered,
    "armed": armed,
    "arming_reason": reason,
}, ensure_ascii=False), encoding="utf-8")
'''


def _side(tree: Path, tmp: Path, label: str) -> dict:
    child = tmp / f"child_{label}.py"
    child.write_text(_CHILD, encoding="utf-8")
    out = tmp / f"{label}.json"
    subprocess.run(
        [sys.executable, str(child), str(tree), str(out)],
        check=True,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    return json.loads(out.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--before", default="main",
        help="the commit whose renderer is the BEFORE side (default: main)",
    )
    parser.add_argument("--out", default=ARTIFACT)
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        before_tree = tmp / "before-tree"
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(before_tree), args.before],
            cwd=REPO, check=True, capture_output=True,
        )
        try:
            before = _side(before_tree, tmp, "before")
            after = _side(REPO, tmp, "after")
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(before_tree)],
                cwd=REPO, check=True, capture_output=True,
            )

    moved = sorted(
        sid for sid in set(before["rendered"]) | set(after["rendered"])
        if before["rendered"].get(sid) != after["rendered"].get(sid)
    )
    in_words_before = sum(
        1 for v in before["rendered"].values() if "in words" in v)
    in_words_after = sum(
        1 for v in after["rendered"].values() if "in words" in v)

    record = {
        "run_id": "foreign_voice_wiring.served_diff.v2",
        "roadmap": "docs/ROADMAP-v0.20.md §4d",
        "design": "docs/DESIGN-voice-completion.md §5.1",
        "writer": "scripts/foreign_voice_wiring_served_diff.py",
        "regenerate_with": (
            f"python scripts/foreign_voice_wiring_served_diff.py "
            f"--before {args.before}"
        ),
        "what_this_is": [
            "The absent/absent half of 4d's evidence obligation, stated "
            "precisely by the design because it is unusual: the foreign "
            "`in words` line shown ABSENT ON BOTH SIDES at batch time, "
            "because no run has armed it yet.",
            "NOT a null result. It is the proof that a witnessed-module "
            "change moved no served byte — exactly what the seal discipline "
            "asks a witnessed change to demonstrate. The present-after-a-"
            "clean-run half lands with the run, or never.",
        ],
        "sides": {
            "before": {
                "commit": args.before,
                "armed": before["armed"],
                "arming_reason": before["arming_reason"],
            },
            "after": {
                "commit": "working tree",
                "armed": after["armed"],
                "arming_reason": after["arming_reason"],
            },
        },
        "statements_rendered": len(after["rendered"]),
        "answer_lines_moved": len(moved),
        "moved_statement_ids": moved,
        "verdict": (
            "AS EXPECTED (no served byte moved)" if not moved else "STOP"
        ),
        "in_words_lines_present": {
            "before": in_words_before,
            "after": in_words_after,
            "note": (
                "v0.18's realizer line. 4d adds a SECOND voice under the same "
                "label, tried only where the committed realizer produced "
                "nothing, so while the surface is dark this count is "
                "unchanged by construction."
            ),
        },
        "why_absent": (
            after["arming_reason"] if not after["armed"]
            else "the surface is ARMED on this tree; re-read the verdict above"
        ),
    }
    out = REPO / args.out
    out.write_text(
        json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"statements rendered : {len(after['rendered'])}")
    print(f"answer lines moved  : {len(moved)} -> {record['verdict']}")
    print(f"`in words` lines    : before {in_words_before}, after {in_words_after}")
    print(f"armed               : before {before['armed']}, after {after['armed']}")
    print(f"-> {out}")
    return 0 if not moved else 1


if __name__ == "__main__":
    raise SystemExit(main())
