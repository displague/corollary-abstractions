#!/usr/bin/env python3
"""Report<->writer coherence check: a committed ledger must equal what its
writer regenerates, or say out loud why it does not.

This absorbs the BACKLOG item "reports/ has no regeneration check" per
DESIGN-retraction-closure §4, which takes that proposed chore as the
retraction slice's substrate rather than a separate errand. It is the
sibling of `scripts/check_regeneration.py` (seeds -> data) one link
further down the artifact chain (data -> reports), and belongs beside it
in the release skill's refresh step.

**A drift is a `ledger_stale` root.** When this check reports `drift`, the
ledger's node is the root of a radius certificate whose
`root_falsification_kind` is `ledger_stale`, and every published claim in
its closure was computed against bytes the writer no longer produces.
That is the tool's first real work (§4), which is why the check lands with
the graph rather than after it.

**A declared snapshot is not a drift.** This distinction is the whole
point of the design's §3 correction: the paragraph that called two ledgers
"already stale" conflated a silent drift (`compression.json`, healed at
`1090aa5` with nobody computing what had consumed the stale bytes) with a
documented decision (`decompositions.json` stays the pre-scale ledger; live
analysis is the pin source). They are different epistemic objects and a
check that flattened them would reproduce the error the design exists to
end. Declared snapshots therefore report `declared_divergence` *with their
citation*, and are never regenerated here — regenerating one would destroy
the snapshot the decision preserved.

Output is one plain line per ledger, machine-parseable:

    <path> <status> [<n> diff lines]

Exit 0 when every ledger is `clean` or `declared_divergence`; exit 1 on any
`drift`.
"""

from __future__ import annotations

import argparse
import difflib
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

#: report path (repo-relative) -> the writer that produces it, and the
#: `--write-report` invocation that regenerates it into an arbitrary path.
#: The mapping used to exist only as a comment in `scripts/verify_slice.py`
#: (design §3: "which script produces which ledger is knowable only from a
#: comment"); this is that knowledge promoted to something executable.
REGISTRY: dict[str, dict] = {
    "reports/signature_matches.json": {
        "writer": "scripts/match_signatures.py",
        "argv": ["--write-report"],
    },
    "reports/specializations.json": {
        "writer": "scripts/specialize.py",
        "argv": ["--write-report"],
    },
    "reports/compression.json": {
        "writer": "scripts/measure_compression.py",
        "argv": ["--write-report"],
    },
    "reports/decompositions.json": {
        "writer": "scripts/decompose.py",
        "argv": ["--write-report"],
    },
}

#: Ledgers whose committed bytes are a declared snapshot, with the citation
#: that declares them. Regenerating one is not merely wasteful (181k
#: constituents at 12k scale) — it would overwrite the artifact the
#: decision exists to keep.
DECLARED_SNAPSHOTS: dict[str, str] = {
    "reports/decompositions.json": (
        "declared pre-scale snapshot; TRIAGE-v0.11 gate table row 6 and "
        "section 5 — live analysis is the pin source"
    ),
}

CLEAN = "clean"
DRIFT = "drift"
DECLARED = "declared_divergence"


def regenerate(report_path: str, out_path: Path, repo: Path = REPO) -> None:
    """Run the registered writer for `report_path` into `out_path`.

    Never into the repo: a check that writes the artifact it is judging
    cannot report drift, it can only erase it. Callers pass a tempdir.
    """

    entry = REGISTRY[report_path]
    cmd = [PYTHON, str(repo / entry["writer"]), *entry["argv"], str(out_path)]
    proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"{entry['writer']} exit {proc.returncode}: {proc.stderr[-400:]}"
        )


def diff_line_count(committed: Path, regenerated: Path) -> int:
    """Unified-diff line count between two ledgers, for the drift report.

    Text-mode with LF folding, so a CRLF checkout does not report every
    line of a clean ledger as changed (same reason `sha256_lf_file` folds).
    """

    def lines(path: Path) -> list[str]:
        return path.read_bytes().replace(b"\r\n", b"\n").decode(
            "utf-8", "replace"
        ).splitlines(keepends=True)

    return sum(
        1
        for _ in difflib.unified_diff(
            lines(committed), lines(regenerated), n=0
        )
    )


def check(report_path: str, repo: Path = REPO) -> tuple[str, int, str]:
    """Return `(status, diff_lines, note)` for one registered ledger."""

    if report_path in DECLARED_SNAPSHOTS:
        return DECLARED, 0, DECLARED_SNAPSHOTS[report_path]
    committed = repo / report_path
    if not committed.is_file():
        return DRIFT, 0, "committed ledger missing"
    with tempfile.TemporaryDirectory(prefix="report-regen-") as tmp:
        out = Path(tmp) / Path(report_path).name
        regenerate(report_path, out, repo)
        if committed.read_bytes() == out.read_bytes():
            return CLEAN, 0, ""
        return DRIFT, diff_line_count(committed, out), ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--only",
        action="append",
        default=None,
        help="check only this repo-relative report path (repeatable)",
    )
    args = ap.parse_args(argv)

    selected = [p for p in REGISTRY if args.only is None or p in args.only]
    failed = False
    for report_path in selected:
        status, n_diff, note = check(report_path)
        line = f"{report_path} {status}"
        if status == DRIFT:
            failed = True
            line += f" {n_diff} diff lines" if n_diff else f" ({note})"
        elif note:
            line += f" ({note})"
        print(line)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
