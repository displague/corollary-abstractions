#!/usr/bin/env python3
"""Trusted merger for seed-append documents.

An append is JSON, parsed as data, never executed
(docs/DESIGN-write-append.md). Seeds emit the nodes they own; files under
``data/<corpus>/appends/*.json`` add nodes the seed does not emit. The same
function is used by ``check_regeneration``, WRITE scratch regeneration, and
``accept_write``.
"""

from __future__ import annotations

import json
from pathlib import Path

APPEND_KIND = "append_nodes"
APPENDS_DIRNAME = "appends"


class AppendError(ValueError):
    """An append document is malformed or collides with an existing node."""


def append_dir(corpus_dir: Path) -> Path:
    return corpus_dir / APPENDS_DIRNAME


def append_paths(corpus_dir: Path) -> list[Path]:
    directory = append_dir(corpus_dir)
    if not directory.is_dir():
        return []
    return sorted(
        path for path in directory.glob("*.json") if path.is_file()
    )


def load_append_document(path: Path) -> dict:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AppendError(f"{path.as_posix()}: {exc}") from exc
    if not isinstance(doc, dict) or doc.get("kind") != APPEND_KIND:
        raise AppendError(
            f"{path.as_posix()}: append must be a JSON object with "
            f"kind={APPEND_KIND!r}"
        )
    nodes = doc.get("statement_nodes")
    if not isinstance(nodes, list) or not nodes:
        raise AppendError(
            f"{path.as_posix()}: statement_nodes must be a non-empty list"
        )
    for node in nodes:
        if not isinstance(node, dict) or not node.get("statement_id"):
            raise AppendError(
                f"{path.as_posix()}: every appended node needs a statement_id"
            )
    return doc


def apply_appends(data_dir: Path) -> None:
    """Merge every corpus's appends into its nodes.json, in filename order.

    Refuses (raises AppendError) if an append id is already present — that
    is a replace, not an append.
    """

    if not data_dir.is_dir():
        return
    for corpus_dir in sorted(path for path in data_dir.iterdir() if path.is_dir()):
        nodes_path = corpus_dir / "nodes.json"
        paths = append_paths(corpus_dir)
        if not nodes_path.is_file() or not paths:
            continue
        corpus = json.loads(nodes_path.read_text(encoding="utf-8"))
        nodes = corpus.get("statement_nodes")
        if not isinstance(nodes, list):
            raise AppendError(
                f"{nodes_path.as_posix()}: statement_nodes must be a list"
            )
        existing = {node.get("statement_id") for node in nodes}
        for path in paths:
            doc = load_append_document(path)
            for node in doc["statement_nodes"]:
                sid = node["statement_id"]
                if sid in existing:
                    raise AppendError(
                        f"append_collision: {sid} already present when "
                        f"applying {path.as_posix()}"
                    )
                nodes.append(node)
                existing.add(sid)
        nodes_path.write_text(
            json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
