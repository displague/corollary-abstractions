#!/usr/bin/env python3
"""Validate Mathematical Statement Node corpora."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


# Mirrors $defs.frameScope in schema/equation-node.schema.json. Underscores
# are allowed in the first segment on purpose (statement_id forbids them;
# BACKLOG records that asymmetry as a defect, not a convention to copy).
FRAME_ID_RE = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)+\Z")
FRAME_ROLES = {"declaration", "assertion"}
# Frame-level properties every member of a frame must agree on: they describe
# the FRAME, not the member node, so disagreement means two nodes are talking
# about different frames under one identifier.
FRAME_AGREEMENT_PROPS = (
    "frame_title",
    "suspends",
    "governed_by",
    "retrieval",
    "on_exit",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def minimal_schema_errors(schema: dict, nodes: list[dict]) -> list[str]:
    errors: list[str] = []
    required = schema.get("required", [])
    classes = set(
        schema.get("properties", {})
        .get("statement_class", {})
        .get("enum", [])
    )
    statuses = set(
        schema.get("properties", {})
        .get("epistemic_status", {})
        .get("enum", [])
    )

    for i, node in enumerate(nodes):
        node_id = node.get("statement_id", f"<node-{i}>")
        for field in required:
            if field not in node:
                errors.append(f"{node_id}: missing required field `{field}`")
        if node.get("statement_class") not in classes:
            errors.append(
                f"{node_id}: invalid statement_class `{node.get('statement_class')}`"
            )
        if node.get("epistemic_status") not in statuses:
            errors.append(
                f"{node_id}: invalid epistemic_status `{node.get('epistemic_status')}`"
            )
    return errors


def inferential_link_errors(
    schema: dict, nodes: list[dict], known_ids: set[str] | None = None
) -> list[str]:
    errors: list[str] = []
    ids = [n.get("statement_id") for n in nodes]
    id_set = set(ids)
    if None in id_set:
        errors.append("At least one node is missing `statement_id`.")
        id_set.discard(None)

    if len(ids) != len(id_set):
        seen: set[str] = set()
        duplicates = sorted({i for i in ids if i in seen or seen.add(i)})
        # Runs over the MERGED graph, so this also names cross-corpus
        # collisions -- which matter to every consumer that keys by
        # statement_id (retrieval's store loader is last-writer-wins).
        errors.append(
            "Duplicate statement_id values found: " + ", ".join(duplicates)
        )

    # Links may resolve to nodes in other corpora when a global id set is given.
    resolvable = id_set | (known_ids or set())

    link_fields = (
        schema.get("properties", {})
        .get("inferential_links", {})
        .get("required", [])
    )
    by_id = {n.get("statement_id"): n for n in nodes if n.get("statement_id")}

    for i, node in enumerate(nodes):
        node_id = node.get("statement_id", f"<node-{i}>")
        links = node.get("inferential_links", {})
        if not isinstance(links, dict):
            errors.append(f"{node_id}: `inferential_links` must be an object")
            continue

        for field in link_fields:
            if field not in links:
                errors.append(f"{node_id}: missing inferential link list `{field}`")
            elif not isinstance(links[field], list):
                errors.append(f"{node_id}: inferential link `{field}` is not a list")

        for field, refs in links.items():
            if not isinstance(refs, list):
                continue
            for ref in refs:
                if ref not in resolvable:
                    errors.append(
                        f"{node_id}: inferential link `{field}` references missing node `{ref}`"
                    )
                if ref == node_id and field != "equivalent_to":
                    errors.append(
                        f"{node_id}: inferential link `{field}` should not self-reference"
                    )

    # Reciprocity checks for directed/symmetric relations. Targets outside
    # this node list (cross-corpus refs in single-file mode) are skipped here;
    # the default all-corpora run checks reciprocity over the merged graph.
    def _links_of(target: str) -> dict | None:
        return by_id[target]["inferential_links"] if target in by_id else None

    for node_id, node in by_id.items():
        links = node.get("inferential_links", {})
        for target in links.get("entails", []):
            t = _links_of(target)
            if t is not None and node_id not in t.get("entailed_by", []):
                errors.append(
                    f"{node_id}: `entails` -> `{target}` lacks reciprocal `entailed_by`"
                )
        for target in links.get("entailed_by", []):
            t = _links_of(target)
            if t is not None and node_id not in t.get("entails", []):
                errors.append(
                    f"{node_id}: `entailed_by` -> `{target}` lacks reciprocal `entails`"
                )
        for target in links.get("equivalent_to", []):
            t = _links_of(target)
            if t is not None and node_id not in t.get("equivalent_to", []):
                errors.append(
                    f"{node_id}: `equivalent_to` -> `{target}` lacks reciprocal equivalence"
                )
        for target in links.get("special_case_of", []):
            t = _links_of(target)
            if t is not None and node_id not in t.get("generalizes", []):
                errors.append(
                    f"{node_id}: `special_case_of` -> `{target}` lacks reciprocal `generalizes`"
                )
        for target in links.get("generalizes", []):
            t = _links_of(target)
            if t is not None and node_id not in t.get("special_case_of", []):
                errors.append(
                    f"{node_id}: `generalizes` -> `{target}` lacks reciprocal `special_case_of`"
                )

    return errors


def scope_errors(
    nodes: list[dict], known_ids: set[str] | None = None
) -> list[str]:
    """Closed-form checks for the optional `scope` object.

    Runs even when jsonschema is absent (pattern/role fallback), and adds
    the two checks jsonschema cannot express: suspends/governed_by must
    resolve against the merged graph, and nodes sharing a frame identifier
    must agree on the frame's properties.
    """
    errors: list[str] = []
    resolvable = {
        n.get("statement_id") for n in nodes if n.get("statement_id")
    } | (known_ids or set())
    frames: dict[str, list[tuple[str, dict]]] = {}

    for i, node in enumerate(nodes):
        node_id = node.get("statement_id", f"<node-{i}>")
        if "scope" not in node:
            continue
        scope = node["scope"]
        if not isinstance(scope, dict):
            # Catches an explicit `"scope": null` too, which jsonschema would
            # flag but this fallback must not silently wave through.
            errors.append(f"{node_id}: `scope` must be an object")
            continue
        frame = scope.get("frame")
        if not isinstance(frame, str) or not FRAME_ID_RE.match(frame):
            errors.append(
                f"{node_id}: scope.frame `{frame}` does not match the "
                "frame-id pattern"
            )
        if scope.get("role") not in FRAME_ROLES:
            errors.append(
                f"{node_id}: scope.role `{scope.get('role')}` must be one of "
                f"{sorted(FRAME_ROLES)}"
            )
        for field in ("suspends", "governed_by"):
            refs = scope.get(field, [])
            if not isinstance(refs, list):
                errors.append(f"{node_id}: scope.{field} must be a list")
                continue
            for ref in refs:
                if ref == node_id:
                    errors.append(
                        f"{node_id}: scope.{field} must not self-reference"
                    )
                elif ref not in resolvable:
                    errors.append(
                        f"{node_id}: scope.{field} references missing node "
                        f"`{ref}`"
                    )
        if isinstance(frame, str):
            frames.setdefault(frame, []).append((node_id, scope))

    for frame, members in sorted(frames.items()):
        for prop in FRAME_AGREEMENT_PROPS:
            stated: dict[str, list[str]] = {}
            for node_id, scope in members:
                if prop in scope:
                    value = scope[prop]
                    if isinstance(value, list):
                        # suspends/governed_by are set-valued: element order
                        # must not manufacture a disagreement.
                        value = sorted(value, key=json.dumps)
                    key = json.dumps(value, sort_keys=True)
                    stated.setdefault(key, []).append(node_id)
            if len(stated) > 1:
                groups = "; ".join(
                    f"{value} in {ids}" for value, ids in sorted(stated.items())
                )
                errors.append(
                    f"frame `{frame}`: members disagree on `{prop}`: {groups}"
                )
        premise_owner: dict[str, tuple[str, str]] = {}
        for node_id, scope in members:
            premises = scope.get("premises", [])
            if not isinstance(premises, list):
                errors.append(
                    f"{node_id}: scope.premises must be a list of premise "
                    "objects"
                )
                continue
            for premise in premises:
                if not isinstance(premise, dict):
                    errors.append(
                        f"{node_id}: scope.premises entries must be objects"
                    )
                    continue
                premise_id = premise.get("premise_id")
                expression = premise.get("expression")
                if premise_id is None:
                    continue
                prior = premise_owner.get(premise_id)
                if prior is not None and prior[0] != expression:
                    errors.append(
                        f"frame `{frame}`: premise `{premise_id}` has "
                        f"conflicting expressions in {prior[1]} and {node_id}"
                    )
                premise_owner.setdefault(premise_id, (expression, node_id))

    return errors


def jsonschema_errors(schema: dict, nodes: list[dict]) -> list[str]:
    try:
        import jsonschema
    except Exception:
        return []

    validator = jsonschema.Draft202012Validator(schema)
    errors: list[str] = []
    for i, node in enumerate(nodes):
        node_id = node.get("statement_id", f"<node-{i}>")
        for err in sorted(validator.iter_errors(node), key=lambda e: list(e.path)):
            errors.append(f"{node_id}: {err.message}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--schema",
        default="schema/equation-node.schema.json",
        help="Path to Mathematical Statement Node schema.",
    )
    parser.add_argument(
        "--nodes",
        default=None,
        help=(
            "Path to a single corpus JSON file containing `statement_nodes`. "
            "Default: validate every data/*/nodes.json as one merged graph."
        ),
    )
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Base data directory scanned when --nodes is not given.",
    )
    args = parser.parse_args()

    schema = load_json(Path(args.schema))

    if args.nodes:
        corpus_paths = [Path(args.nodes)]
    else:
        corpus_paths = sorted(Path(args.data_dir).glob("*/nodes.json"))
        if not corpus_paths:
            print(f"Validation failed:\n- No */nodes.json files under `{args.data_dir}`.")
            return 1

    all_nodes: list[dict] = []
    errors: list[str] = []
    for path in corpus_paths:
        data = load_json(path)
        nodes = data.get("statement_nodes")
        if not isinstance(nodes, list):
            errors.append(f"{path}: corpus must contain `statement_nodes` as a list.")
            continue
        errors.extend(minimal_schema_errors(schema, nodes))
        errors.extend(jsonschema_errors(schema, nodes))
        all_nodes.extend(nodes)

    # Link integrity and reciprocity over the merged cross-discipline graph.
    errors.extend(inferential_link_errors(schema, all_nodes))
    # Scope integrity: frame ids, frame agreement, suspends/governed_by
    # resolution -- also over the merged graph, since a frame may suspend
    # or be governed by nodes in another corpus.
    errors.extend(scope_errors(all_nodes))

    if errors:
        print("Validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    corpus_word = "corpus" if len(corpus_paths) == 1 else "corpora"
    print(
        f"Validation passed for {len(all_nodes)} statement nodes "
        f"across {len(corpus_paths)} {corpus_word}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
