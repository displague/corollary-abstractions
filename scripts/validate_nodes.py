#!/usr/bin/env python3
"""Validate Mathematical Statement Node corpora."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


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
        errors.append("Duplicate statement_id values found.")

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
