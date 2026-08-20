#!/usr/bin/env python3
"""DESIGN-retraction-closure §6 gate R4 made executable: the outside recheck.

R4, verbatim from the design's frozen construction gate:

    **R4 — independent recheck.** A recheck script re-derives every
    published closure from `(graph, root)` in ≤10 minutes on the declared
    host, hashes matching.

This module is the *independent* side of that gate, and its independence is
structural rather than promised. It was written against three documents
only — DESIGN-retraction-closure §4 (including the dated Clarification on
who counts as a writer) and §6 R4, ``schema/provenance-graph.schema.json``,
and ``schema/radius-certificate.schema.json`` — and it never imports, reads,
or executes the graph assembler or the radius tool that produced the
artifacts it judges. It re-derives the closure from the graph file and the
certificate's own declared fields, exactly as ``scripts/closure_check.py``
rebuilds a bounded closure without importing ``closure_build``. A checker
that called the builder would only re-ask the builder what the builder
thinks, which §9 of the incumbent design names vacuous; the same objection
applies here, so the same remedy is applied.

**The traversal, stated so a reader can check it against design §4.** The
graph's ``derived_from`` edges point from a downstream artifact to the input
it was derived from: an edge ``{from_node: X, to_node: Y, relation:
"derived_from"}`` says X consumed Y. A retraction runs the other way — if Y
is wrong, X is exposed — so the closure of a root R is built forward over
those edges reversed: start with ``{R}``, and repeatedly add any node X for
which some edge ``{from_node: X, to_node: Y, relation: "derived_from",
inferred: false}`` has Y already in the set, until nothing new joins. Only
``derived_from`` is traversed; ``pinned_from``, ``asserted_by``, and
``published_in`` record other facts and add nothing to a blast radius. Only
``inferred: false`` edges are traversed, per §4's Clarification: "Scored
closures (R2, and the blind control's shuffled closures) traverse
``inferred: false`` edges only." Depth is the minimum number of such edges
between the root and the node, so the root sits at depth 0.

The gate's own ceiling is not written here. ``r4_recheck_seconds`` is read
out of ``schema/radius-certificate.schema.json`` at run time, so that the
600 in the design, the const in the schema, and the limit this script
enforces cannot fork into three numbers that drift apart quietly.

Output is deterministic: one ``ok:`` or ``MISMATCH:`` line per check, no
timestamps beyond the measured duration, and no absolute paths — a recheck
transcript from another host must be diffable against this one.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import jsonschema

REPO = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO / "schema"
GRAPH_SCHEMA_PATH = SCHEMA_DIR / "provenance-graph.schema.json"
CERTIFICATE_SCHEMA_PATH = SCHEMA_DIR / "radius-certificate.schema.json"

GRAPH_RELATIVE_PATH = Path("reports") / "provenance_graph.jsonl"

TRAVERSED_RELATION = "derived_from"


@dataclass(frozen=True)
class Check:
    """One clause of R4, with the sentence that names its break.

    ``detail`` is a single sentence naming ONE offending node or edge, not a
    list of every downstream consequence of one corruption: a report that
    grew with the size of the damage would let a reader mistake noise for
    severity.
    """

    ok: bool
    what: str
    detail: str | None = None

    def render(self) -> str:
        if self.ok:
            return f"ok: {self.what}"
        return f"MISMATCH: {self.what} {self.detail}"


@dataclass(frozen=True)
class RecheckReport:
    """The verdict on one published certificate."""

    ok: bool
    first_mismatch: str | None
    checks: tuple[Check, ...]
    derived_closure: tuple[str, ...]
    closure_size: int
    duration_seconds: float
    limit_seconds: int

    def render(self) -> str:
        return "\n".join(check.render() for check in self.checks)


def sha256_lf_file(path: Path) -> str:
    """SHA-256 of the file's bytes with CRLF normalized to LF.

    The graph is a text artifact that crosses hosts; a checkout that
    materialized it with Windows line endings must still hash equal, or R4
    would fail for a reason that has nothing to do with provenance.
    """

    return hashlib.sha256(
        path.read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()


def _load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def recheck_seconds_limit(
    schema_path: Path = CERTIFICATE_SCHEMA_PATH,
) -> int:
    """R4's ceiling, read from the schema rather than restated here.

    The number lives in exactly one machine-readable place —
    ``$defs.gate.properties.r4_recheck_seconds.const`` — because a limit
    duplicated between the gate document, the schema, and the enforcing
    script is a limit that can be moved in one of the three without anyone
    noticing.
    """

    schema = _load_schema(schema_path)
    gate = schema["$defs"]["gate"]["properties"]
    return int(gate["r4_recheck_seconds"]["const"])


def default_graph_path(cert_path: Path) -> Path:
    """``reports/provenance_graph.jsonl`` of the tree the certificate is in.

    A certificate lives at ``reports/radius/<cert_id>.cert.json``, so the
    graph is normally two directories up and over. The search walks the
    ancestors instead of assuming that depth, so a certificate copied into a
    scratch tree still finds the graph committed beside it.
    """

    resolved = cert_path.resolve()
    for parent in resolved.parents:
        candidate = parent / GRAPH_RELATIVE_PATH
        if candidate.is_file():
            return candidate
    return resolved.parents[min(2, len(resolved.parents) - 1)] / (
        GRAPH_RELATIVE_PATH
    )


@dataclass(frozen=True)
class GraphRecords:
    """A parsed provenance graph: node ids, and edges as plain tuples."""

    node_ids: frozenset[str]
    edges: tuple[dict, ...]


def parse_graph(path: Path, validator: jsonschema.Validator) -> GraphRecords:
    """Read the JSONL graph, validating every line against §4's schema.

    Raises ``ValueError`` naming the first offending line. Line numbers are
    1-based and count blank lines, so the message points at what an editor
    would show.
    """

    node_ids: set[str] = set()
    edges: list[dict] = []
    text = path.read_bytes().decode("utf-8")
    for number, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(
                f"line {number} is not valid JSON ({error.msg})"
            ) from error
        errors = sorted(validator.iter_errors(record), key=str)
        if errors:
            raise ValueError(
                f"line {number} does not validate against the provenance "
                f"graph schema ({errors[0].message})"
            )
        if record["record"] == "node":
            node_ids.add(record["node_id"])
        else:
            edges.append(record)
    return GraphRecords(frozenset(node_ids), tuple(edges))


def derive_closure(
    graph: GraphRecords, root: str
) -> tuple[dict[str, int], dict[str, int]]:
    """The closure of ``root``, and its depth histogram.

    Breadth-first over emitted ``derived_from`` edges reversed (see the
    module docstring). Adjacency is sorted before traversal so that the
    derived depths are a function of the graph's content alone and not of
    the order the file happened to list its edges in.

    Returns ``(depth_by_node, histogram)`` where the histogram's keys are
    decimal depths as strings, matching the certificate schema's
    ``depth_histogram``.
    """

    consumers: dict[str, list[str]] = {}
    for edge in graph.edges:
        if edge["relation"] != TRAVERSED_RELATION or edge["inferred"]:
            continue
        consumers.setdefault(edge["to_node"], []).append(edge["from_node"])
    for inputs in consumers.values():
        inputs.sort()

    depth_by_node = {root: 0}
    frontier = [root]
    depth = 0
    while frontier:
        depth += 1
        successors: list[str] = []
        for node in sorted(frontier):
            for consumer in consumers.get(node, []):
                if consumer in depth_by_node:
                    continue
                depth_by_node[consumer] = depth
                successors.append(consumer)
        frontier = successors

    histogram: dict[str, int] = {}
    for value in depth_by_node.values():
        key = str(value)
        histogram[key] = histogram.get(key, 0) + 1
    return depth_by_node, histogram


def _first_closure_offender(
    derived: set[str], claimed: set[str]
) -> str | None:
    """The lowest-sorting node the two sets disagree about."""

    disagreements = sorted(derived ^ claimed)
    return disagreements[0] if disagreements else None


def recheck(
    cert_path: Path | str, graph_path: Path | str | None = None
) -> RecheckReport:
    """Re-derive one published certificate's closure and demand it match.

    The steps run in the order R4 implies and stop at the first break that
    makes the rest meaningless: a graph whose bytes are not the certificate's
    graph is refused before any traversal, because re-deriving from the
    wrong file and reporting a difference would blame the closure for a
    substitution.
    """

    started = time.monotonic()
    cert_path = Path(cert_path)
    limit = recheck_seconds_limit()
    checks: list[Check] = []
    derived_order: tuple[str, ...] = ()

    def finish() -> RecheckReport:
        duration = time.monotonic() - started
        checks.append(
            Check(
                duration <= limit,
                f"recheck_seconds {duration:.3f} of {limit} allowed",
                None
                if duration <= limit
                else (
                    f"expected at most {limit} seconds, took "
                    f"{duration:.3f}"
                ),
            )
        )
        failures = [check for check in checks if not check.ok]
        return RecheckReport(
            ok=not failures,
            first_mismatch=failures[0].render() if failures else None,
            checks=tuple(checks),
            derived_closure=derived_order,
            closure_size=len(derived_order),
            duration_seconds=duration,
            limit_seconds=limit,
        )

    certificate = json.loads(cert_path.read_text(encoding="utf-8"))
    cert_schema = _load_schema(CERTIFICATE_SCHEMA_PATH)
    cert_errors = sorted(
        jsonschema.Draft202012Validator(cert_schema).iter_errors(certificate),
        key=str,
    )
    if cert_errors:
        checks.append(
            Check(
                False,
                "certificate_schema",
                f"expected a certificate valid against the radius "
                f"certificate schema, found {cert_errors[0].message}",
            )
        )
        return finish()
    checks.append(Check(True, "certificate_schema"))

    graph_path = (
        Path(graph_path)
        if graph_path is not None
        else default_graph_path(cert_path)
    )
    if not graph_path.is_file():
        checks.append(
            Check(
                False,
                "graph_sha256",
                "expected a readable provenance graph at "
                f"{GRAPH_RELATIVE_PATH.as_posix()}, found no such file",
            )
        )
        return finish()
    found_graph_sha = sha256_lf_file(graph_path)
    if found_graph_sha != certificate["graph_sha256"]:
        checks.append(
            Check(
                False,
                "graph_sha256",
                f"expected {certificate['graph_sha256']}, found "
                f"{found_graph_sha}; refusing to re-derive from a graph "
                f"this certificate was not computed against",
            )
        )
        return finish()
    checks.append(Check(True, "graph_sha256"))

    graph_schema = _load_schema(GRAPH_SCHEMA_PATH)
    validator = jsonschema.Draft202012Validator(graph_schema)
    try:
        graph = parse_graph(graph_path, validator)
    except ValueError as error:
        checks.append(Check(False, "graph_schema", str(error)))
        return finish()
    checks.append(Check(True, "graph_schema"))

    root = certificate["root_node"]
    if root not in graph.node_ids:
        checks.append(
            Check(
                False,
                "root_node",
                f"expected node {root} to exist in the pinned graph, found "
                f"no node record for it",
            )
        )
        return finish()
    checks.append(Check(True, "root_node"))

    depth_by_node, histogram = derive_closure(graph, root)
    derived_order = tuple(sorted(depth_by_node))
    derived_set = set(depth_by_node)
    claimed_list = list(certificate["closure"])
    claimed_set = set(claimed_list)

    offender = _first_closure_offender(derived_set, claimed_set)
    if offender is not None:
        if offender in derived_set:
            detail = (
                f"expected node {offender} at depth "
                f"{depth_by_node[offender]}, which is reachable from "
                f"{root} over emitted derived_from edges; the certificate "
                f"does not list it"
            )
        else:
            detail = (
                f"expected no such member, found node {offender}, which is "
                f"not reachable from {root} over emitted derived_from edges"
            )
        checks.append(Check(False, "closure", detail))
        return finish()
    checks.append(Check(True, "closure"))

    if claimed_list != list(derived_order):
        checks.append(
            Check(
                False,
                "closure_order",
                "expected the closure listed once each in sorted order, "
                f"found {len(claimed_list)} entries whose first departure "
                f"from that order is "
                f"{_first_order_departure(claimed_list, derived_order)}",
            )
        )
        return finish()
    checks.append(Check(True, "closure_order"))

    if certificate["closure_size"] != len(derived_order):
        checks.append(
            Check(
                False,
                "closure_size",
                f"expected {len(derived_order)}, found "
                f"{certificate['closure_size']}",
            )
        )
        return finish()
    checks.append(Check(True, "closure_size"))

    claimed_histogram = dict(certificate["depth_histogram"])
    if claimed_histogram != histogram:
        depths = sorted(
            set(claimed_histogram) ^ set(histogram)
            | {
                key
                for key in set(claimed_histogram) & set(histogram)
                if claimed_histogram[key] != histogram[key]
            },
            key=int,
        )
        key = depths[0]
        checks.append(
            Check(
                False,
                "depth_histogram",
                f"expected depth {key} to hold {histogram.get(key, 0)} "
                f"nodes, found {claimed_histogram.get(key, 0)}",
            )
        )
        return finish()
    checks.append(Check(True, "depth_histogram"))

    edges_by_id = {edge["edge_id"]: edge for edge in graph.edges}
    for edge_id in sorted(certificate["inferred_edges_excluded"]):
        edge = edges_by_id.get(edge_id)
        if edge is None:
            detail = (
                f"expected edge {edge_id} to exist in the pinned graph, "
                f"found no edge record for it"
            )
        elif not edge["inferred"]:
            detail = (
                f"expected edge {edge_id} to be inferred, found an emitted "
                f"edge, which the closure traverses rather than excludes"
            )
        elif edge["relation"] != TRAVERSED_RELATION:
            detail = (
                f"expected edge {edge_id} to be a {TRAVERSED_RELATION} "
                f"edge, found relation {edge['relation']}, which no closure "
                f"traverses"
            )
        elif edge["to_node"] not in derived_set:
            detail = (
                f"expected edge {edge_id} to land on a closure member, "
                f"found to_node {edge['to_node']} outside the closure; it "
                f"would not have joined this closure had it been scored"
            )
        elif edge["from_node"] in derived_set:
            detail = (
                f"expected edge {edge_id} to add a node, found from_node "
                f"{edge['from_node']} already in the closure by an emitted "
                f"route; excluding it changes nothing"
            )
        else:
            continue
        checks.append(Check(False, "inferred_edges_excluded", detail))
        return finish()
    checks.append(Check(True, "inferred_edges_excluded"))

    return finish()


def _first_order_departure(
    claimed: list[str], derived: tuple[str, ...]
) -> str:
    """Name the first position where the listed order breaks sorted order."""

    for index, (found, expected) in enumerate(zip(claimed, derived)):
        if found != expected:
            return f"position {index}: expected {expected}, found {found}"
    return f"position {min(len(claimed), len(derived))}: a truncated list"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Re-derive a published radius certificate's closure from the "
            "pinned provenance graph and report the first mismatch "
            "(DESIGN-retraction-closure section 6, gate R4)."
        )
    )
    parser.add_argument("certificate", type=Path)
    parser.add_argument("--graph", type=Path, default=None)
    arguments = parser.parse_args(argv)

    report = recheck(arguments.certificate, arguments.graph)
    print(report.render())
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
