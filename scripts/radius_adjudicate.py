#!/usr/bin/env python3
"""The R2 evaluator: does a computed closure explain the hand-audited list?

DESIGN-retraction-closure §6, verbatim:

    **R2 — the live drifts are explained, superset-exactly.** For each of
    the two stale-ledger roots, the computed closure must be a superset of
    the pre-committed hand-audited ground truth, with
    ``closure_size ≤ 3 × |ground truth|``. One missed claim voids the
    capability; no patch-and-rerun — a re-run after any graph edit is a new
    preregistration.

This module scores that clause and nothing else. It takes a certificate
written by ``scripts/retraction_radius.py``, the hand-audited list the
adjudication is against, and the graph the certificate names, and reports
how many audited claims the closure covers, which it misses, and whether
the ratio holds.

**Why this file may read the answer key and the assembler may not.** §4's
dated clarification says: "The citation scan must not read the ground
truth. R2 compares a mechanically derived closure against an independently
hand-audited list; an assembler that consumes [the hand-audited files]
would make the clause a tautology." That prohibition binds the two tools
that *produce* the thing being scored — ``scripts/provenance_graph.py``
and ``scripts/retraction_radius.py`` — and a test scans both of their
sources to enforce it. It cannot bind the evaluator: an R2 evaluator that
could not read the audited list would have nothing to compare against.
The asymmetry is the whole design. The producer must be blind; the judge
must not be. This module is therefore explicitly EXEMPT from that scan,
and the exemption is stated here rather than left as an omission, so that
nobody later "fixes" the scan by adding this file to it or, worse, moves a
lookup out of here and into the assembler because "the evaluator reads it
anyway".

**Anchor resolution.** A ground-truth entry names a ``file`` and an
``anchor`` (a heading string). The assembler mints one claim node per
markdown section and disambiguates repeated headings within a file with a
positional ``~2``, ``~3``, … suffix. The audit was done by a human reading
prose and does not carry that suffix, and it should not have to: the
auditor recorded *the claim*, and which of two identically-headed sections
carries it is a fact about the assembler's numbering, not about the audit.
So an anchor resolves to EVERY claim node for that file and heading, and
the pair counts as covered if ANY of them is in the closure. This is the
generous direction on purpose — R2's failure mode that matters is a missed
claim, and resolving generously means a reported miss is a real miss rather
than a suffix collision.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from retraction_radius import load_graph  # noqa: E402

#: §6's ratio, transcribed from the design and checkable against the schema
#: const ``$defs.gate.r2_closure_to_ground_truth_ratio``.
R2_RATIO = 3


def claim_node_prefix(file_rel: str, anchor: str) -> str:
    """The node id an anchor resolves to, before duplicate disambiguation."""

    return f"claim:{file_rel}#{anchor}"


def resolve_anchor(nodes: dict[str, dict], file_rel: str, anchor: str) -> list[str]:
    """Every claim node for one (file, heading) pair, ``~n`` suffixes included."""

    base = claim_node_prefix(file_rel, anchor)
    return sorted(
        node_id
        for node_id in nodes
        if node_id == base or node_id.startswith(base + "~")
    )


def score_closure(
    nodes: dict[str, dict], closure: set[str], audit: dict
) -> dict:
    """R2's arithmetic over an in-memory closure — the shared core.

    Split out from :func:`evaluate` so that the blind control scores its 100
    shuffled graphs with *this* function rather than a second copy of it. A
    control that scored itself by different arithmetic than the real run
    would compare two things, only one of which is R2.
    """

    covered: list[dict] = []
    misses: list[dict] = []
    for claim in audit["claims"]:
        candidates = resolve_anchor(nodes, claim["file"], claim["anchor"])
        inside = [node_id for node_id in candidates if node_id in closure]
        row = {
            "ground_truth_id": claim["id"],
            "class": claim["class"],
            "file": claim["file"],
            "anchor": claim["anchor"],
            "claim_nodes": candidates,
            "covered_by": inside,
            # A pair with no candidates at all is a different defect from a
            # pair whose node exists and sits outside the closure: the first
            # says the assembler never anchored the section, the second says
            # the citation scan saw no path from the root to it.
            "anchored": bool(candidates),
        }
        (covered if inside else misses).append(row)

    total = len(audit["claims"])
    size = len(closure)
    return {
        "covered": len(covered),
        "total": total,
        "misses": misses,
        "closure_size": size,
        "cap": R2_RATIO * total,
        "ratio_ok": size <= R2_RATIO * total,
        "superset_ok": not misses,
        "r2_ok": (not misses) and size <= R2_RATIO * total,
    }


def evaluate(
    cert_path: Path | str,
    ground_truth_path: Path | str,
    graph_path: Path | str,
) -> dict:
    """Score R2 for one root. Returns the verdict as plain data.

    ``superset_ok`` is the clause that voids the capability when false, and
    it is reported separately from ``ratio_ok`` because the two failures
    mean opposite things: a miss says the graph does not know about a real
    dependency, and an over-wide closure says it cannot tell dependency
    from vocabulary.
    """

    cert = json.loads(Path(cert_path).read_text(encoding="utf-8"))
    audit = json.loads(Path(ground_truth_path).read_text(encoding="utf-8"))
    nodes, _ = load_graph(Path(graph_path))

    verdict = score_closure(nodes, set(cert["closure"]), audit)
    # The certificate's own count is authoritative for the ratio clause —
    # R2 is read off the receipt, not recomputed from a list that could
    # have been edited after it was published.
    assert verdict["closure_size"] == cert["closure_size"], "cert closure_size"
    verdict.update(
        {
            "root_node": cert["root_node"],
            "cert_id": cert["cert_id"],
            "graph_sha256": cert["graph_sha256"],
        }
    )
    return verdict


def format_verdict(verdict: dict) -> str:
    lines = [
        f"root            {verdict['root_node']}",
        f"covered         {verdict['covered']}/{verdict['total']}",
        f"closure_size    {verdict['closure_size']} (cap {verdict['cap']})",
        f"superset_ok     {verdict['superset_ok']}",
        f"ratio_ok        {verdict['ratio_ok']}",
        f"R2              {'PASS' if verdict['r2_ok'] else 'FAIL'}",
    ]
    for miss in verdict["misses"]:
        where = miss["claim_nodes"][0] if miss["anchored"] else "(no claim node)"
        lines.append(f"  MISS {miss['ground_truth_id']} {miss['class']} {where}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Score design R2 for one root")
    ap.add_argument("certificate")
    ap.add_argument("ground_truth")
    ap.add_argument(
        "--graph", default=str(REPO_ROOT / "reports" / "provenance_graph.jsonl")
    )
    ap.add_argument("--out", default=None, help="write the verdict as JSON here")
    args = ap.parse_args(argv)

    verdict = evaluate(args.certificate, args.ground_truth, args.graph)
    print(format_verdict(verdict))
    if args.out:
        Path(args.out).write_bytes(
            (json.dumps(verdict, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        )
    return 0 if verdict["r2_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
