#!/usr/bin/env python3
"""The radius tool: one root, one closure, one receipt.

DESIGN-retraction-closure §1 asks the question reproducibility cannot
answer — *if this input is wrong, what exactly falls?* — and §4 fixes the
answer's shape as ``reports/radius/<cert_id>.cert.json``. This module
computes that answer from a pinned ``reports/provenance_graph.jsonl`` and a
single root node, and refuses to write a certificate that does not validate
against ``schema/radius-certificate.schema.json``.

**The closure runs downstream.** The graph's ``derived_from`` edges point
from a consumer to what it consumed. Consequence runs the other way, so the
closure is the reverse-``derived_from`` reachable set: start at the root,
and repeatedly admit any node ``X`` with an edge ``X derived_from Y`` for a
``Y`` already inside. Depth is BFS distance from the root, and depth 0 is
the root itself, which is always a member of its own closure.

**Only emitted edges are traversed** (§4's clarification, and R2's scored
clause). An ``inferred: true`` edge is one a writer should have emitted and
did not; counting it would let a reconstruction decide what a retraction
costs. What such edges *would* have added is not hidden either — every one
that would have joined this closure is listed by id in
``inferred_edges_excluded``, so the reader can see the size of what the
gate refuses to count.

**``pinned_from`` is not traversed in v1, deliberately.** Revoking an
external pin — a source relicensed, a dataset withdrawn, an archive whose
bytes no longer match the manifest — is a different falsification with a
different blast radius, and it belongs to its own root kind
(``source_unpinned``). Folding it into ``ledger_stale`` traversal would
price two failures with one number and would make the corpora that happen
to share an upstream archive look like each other's consequences. It is
priced later, as its own root, with its own ground truth.

**What a certificate does not claim** (§7): not that the closure is
*sufficient* — repairing every node in it is not certified to restore
correctness; not that absence from it is a negative certificate; and not
that it captures conceptual dependency. That last one is carried on the
certificate itself as ``standing_limitation``, read out of the schema at
write time so the sentence in the receipt and the sentence in the schema
cannot drift apart.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import deque
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parent.parent

GRAPH_RELATIVE_PATH = "reports/provenance_graph.jsonl"
CERT_SCHEMA_RELATIVE = "schema/radius-certificate.schema.json"
CERT_DIR_RELATIVE = "reports/radius"
RECHECK_SCRIPT = "scripts/radius_recheck.py"

CLAIM_KINDS = {"analysis_claim", "release_claim"}

FALSIFICATION_KINDS = (
    "witness_invalid",
    "source_unpinned",
    "standing_demoted",
    "script_defect",
    "ledger_stale",
)


def sha256_lf_file(path: Path) -> str:
    """Canonical-LF SHA-256: the identity the whole repo hashes files by."""

    return hashlib.sha256(
        Path(path).read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()


def load_graph(graph_path: Path) -> tuple[dict[str, dict], list[dict]]:
    """``({node_id: node}, [edge])`` from a JSONL graph file."""

    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    text = Path(graph_path).read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
    for line in text.splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record["record"] == "node":
            nodes[record["node_id"]] = record
        else:
            edges.append(record)
    return nodes, edges


def _reverse_index(edges: list[dict], include_inferred: bool) -> dict[str, list[dict]]:
    """``to_node -> [derived_from edges]``, i.e. consumers of each node."""

    index: dict[str, list[dict]] = {}
    for edge in edges:
        if edge["relation"] != "derived_from":
            continue
        if edge["inferred"] and not include_inferred:
            continue
        index.setdefault(edge["to_node"], []).append(edge)
    return index


def closure_from(
    edges: list[dict], root: str, include_inferred: bool = False
) -> dict[str, int]:
    """``{node_id: bfs_depth}`` for everything downstream of ``root``."""

    index = _reverse_index(edges, include_inferred)
    depth = {root: 0}
    queue = deque([root])
    while queue:
        current = queue.popleft()
        for edge in index.get(current, []):
            consumer = edge["from_node"]
            if consumer not in depth:
                depth[consumer] = depth[current] + 1
                queue.append(consumer)
    return depth


def unprovenanced_claims(nodes: dict[str, dict], edges: list[dict]) -> list[str]:
    """Claim nodes with no outbound ``derived_from`` edge at all.

    R3's remainder, listed on EVERY certificate rather than only on the ones
    it embarrasses. A claim the citation scan could not anchor to any
    artifact is not evidence that the claim depends on nothing; it is
    evidence that this graph cannot say what it depends on, and a
    certificate that omitted the distinction would read like a clean
    closure.
    """

    anchored = {
        edge["from_node"] for edge in edges if edge["relation"] == "derived_from"
    }
    return sorted(
        node_id
        for node_id, node in nodes.items()
        if node["kind"] in CLAIM_KINDS and node_id not in anchored
    )


def certify(
    graph_path: Path | str,
    root_node_id: str,
    falsification_kind: str,
    cert_id: str,
    out_dir: Path | str | None = None,
) -> Path:
    """Compute one root's closure and write its certificate.

    Returns the certificate path. Raises before writing if the root is not
    in the graph, if the falsification kind is not one of the five frozen
    kinds, or if the assembled certificate fails schema validation — an
    invalid receipt is worse than no receipt, because it looks like one.
    """

    graph_path = Path(graph_path).resolve()
    repo_root = graph_path.parent.parent
    if falsification_kind not in FALSIFICATION_KINDS:
        raise ValueError(f"unknown falsification kind: {falsification_kind}")

    nodes, edges = load_graph(graph_path)
    if root_node_id not in nodes:
        raise KeyError(f"root not in graph: {root_node_id}")

    scored = closure_from(edges, root_node_id, include_inferred=False)
    # What the gate refuses to count, measured rather than asserted: re-run
    # the same walk with inferred edges admitted, and report every inferred
    # edge whose target ended up reachable. These are exactly the edges that
    # would have grown this closure had a writer emitted them.
    permissive = closure_from(edges, root_node_id, include_inferred=True)
    excluded = sorted(
        edge["edge_id"]
        for edge in edges
        if edge["inferred"]
        and edge["relation"] == "derived_from"
        and edge["to_node"] in permissive
    )

    histogram: dict[str, int] = {}
    for value in scored.values():
        histogram[str(value)] = histogram.get(str(value), 0) + 1

    out_dir = Path(out_dir) if out_dir is not None else repo_root / CERT_DIR_RELATIVE
    out_dir.mkdir(parents=True, exist_ok=True)
    cert_path = out_dir / f"{cert_id}.cert.json"

    # A recheck command must name a path the rechecker can open. A cert
    # written inside the repo names itself; one written to a scratch
    # directory (a dev run, a test) names the published location it would
    # occupy, since a temp path is meaningless to any reader.
    try:
        cert_rel = cert_path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        cert_rel = f"{CERT_DIR_RELATIVE}/{cert_id}.cert.json"

    schema = json.loads(
        (repo_root / CERT_SCHEMA_RELATIVE).read_text(encoding="utf-8")
    )
    certificate = {
        "cert_id": cert_id,
        "root_node": root_node_id,
        "root_falsification_kind": falsification_kind,
        "closure": sorted(scored),
        "closure_size": len(scored),
        "depth_histogram": dict(
            sorted(histogram.items(), key=lambda kv: int(kv[0]))
        ),
        "unprovenanced_nodes": unprovenanced_claims(nodes, edges),
        "inferred_edges_excluded": excluded,
        "graph_sha256": sha256_lf_file(graph_path),
        "tool_version": sha256_lf_file(Path(__file__).resolve()),
        "recheck_command": f"python {RECHECK_SCRIPT} {cert_rel}",
        # Read from the schema, never retyped: §7's limitation is a const
        # precisely so a tool cannot soften its own caveat.
        "standing_limitation": schema["properties"]["standing_limitation"]["const"],
    }

    jsonschema.Draft202012Validator(schema).validate(certificate)
    cert_path.write_bytes(
        (json.dumps(certificate, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    )
    return cert_path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Certify one retraction radius")
    ap.add_argument("root", help="root node_id, e.g. ledger:reports/compression.json")
    ap.add_argument("cert_id", help="certificate id; also its filename stem")
    ap.add_argument(
        "--kind",
        default="ledger_stale",
        choices=FALSIFICATION_KINDS,
        help="why the root is being treated as wrong",
    )
    ap.add_argument("--graph", default=str(REPO_ROOT / GRAPH_RELATIVE_PATH))
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args(argv)

    path = certify(args.graph, args.root, args.kind, args.cert_id, args.out_dir)
    cert = json.loads(path.read_text(encoding="utf-8"))
    print(f"wrote {path}")
    print(f"root            {cert['root_node']} ({cert['root_falsification_kind']})")
    print(f"closure_size    {cert['closure_size']}")
    print(f"depth_histogram {cert['depth_histogram']}")
    print(f"unprovenanced   {len(cert['unprovenanced_nodes'])}")
    print(f"inferred excl.  {len(cert['inferred_edges_excluded'])}")
    print(f"recheck         {cert['recheck_command']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
