#!/usr/bin/env python3
"""Load and gate `data/domains/domain_schema.json`.

`docs/DESIGN-statements-that-run.md` §3.3: the domain schema is a frozen,
hand-authored, reviewed table carrying its own digest, on the rules v0.19's
lexicon lives by — **a table that fails its load gate raises rather than
degrading** (`scripts/realization_lexicon.py:30-38`).

Why the gate raises rather than returning a partial table: Correction 4
measured that a conformance engine without a domain does not produce wrong
answers occasionally, it produces a verdict whose meaning is undefined. A
half-loaded schema is exactly that, and §8 makes a schema that will not load
a stop condition — *"a schema that will not load is not a thing to work
around"*.

**Domain absence is a refusal, never a default.** `carrier_for` returns
`None` for a statement no row covers, and the caller refuses with
`domain_absent`. There is no fallback carrier, because a fallback is a
declaration nobody reviewed.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA_PATH = REPO / "data" / "domains" / "domain_schema.json"


class DomainSchemaError(ValueError):
    """The table is unreadable, incomplete, or contradicts itself."""


@dataclass(frozen=True)
class ClassRow:
    class_id: str
    applies_to: str
    carrier: str
    division: str
    subtraction: str


@dataclass(frozen=True)
class DomainSchema:
    schema_id: str
    frozen_at: str
    carriers: tuple[str, ...]
    class_rows: tuple[ClassRow, ...]
    statement_rows: tuple[dict, ...]
    branch_cuts: tuple[str, ...]
    output_roles: frozenset[str]
    digest: str
    path: str

    def carrier_for(self, statement_id: str, corpus_id: str):
        """The declared reading for one statement, or None.

        None is `domain_absent` — a refusal with a register entry, never a
        default. §3.3: *"Domain is therefore a required input, and its
        absence is a refusal with a register entry, never a default."*
        """

        for row in self.statement_rows:
            if row.get("statement_id") == statement_id:
                return row
        for row in self.class_rows:
            if row.applies_to == "corpus_id" and row.class_id == corpus_id:
                return {
                    "class_id": row.class_id,
                    "carrier": row.carrier,
                    "division": row.division,
                    "subtraction": row.subtraction,
                }
        return None


def sha256_lf(path: Path) -> str:
    return hashlib.sha256(
        Path(path).read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()


def load(path: Path | str | None = None) -> DomainSchema:
    """Read, gate and return the table. Raises `DomainSchemaError` on any failure."""

    schema_path = Path(path) if path is not None else DEFAULT_SCHEMA_PATH
    try:
        raw = json.loads(schema_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise DomainSchemaError(f"domain schema unreadable: {exc}") from None
    except ValueError as exc:
        raise DomainSchemaError(f"domain schema is not JSON: {exc}") from None
    if not isinstance(raw, dict):
        raise DomainSchemaError("domain schema is not an object")

    return build(raw, schema_path)


def build(raw: dict, path: Path | str = "<memory>") -> DomainSchema:
    """Gate an already-parsed table. Split from `load` so tests can inject."""

    schema_id = raw.get("schema_id")
    if not isinstance(schema_id, str) or not schema_id:
        raise DomainSchemaError("schema_id is required")

    carriers = tuple(raw.get("carriers") or ())
    if not carriers or not all(isinstance(c, str) for c in carriers):
        raise DomainSchemaError("carriers must be a non-empty list of strings")

    rows: list[ClassRow] = []
    for entry in raw.get("class_rows") or ():
        if not isinstance(entry, dict):
            raise DomainSchemaError("every class row must be an object")
        missing = [
            key for key in ("class_id", "applies_to", "carrier", "division",
                            "subtraction")
            if not isinstance(entry.get(key), str) or not entry.get(key)
        ]
        if missing:
            raise DomainSchemaError(
                f"class row {entry.get('class_id')!r} is missing {missing}"
            )
        if entry["carrier"] not in carriers:
            raise DomainSchemaError(
                f"class row {entry['class_id']!r} declares carrier "
                f"{entry['carrier']!r}, which is not in `carriers`"
            )
        if entry["applies_to"] != "corpus_id":
            raise DomainSchemaError(
                f"class row {entry['class_id']!r} applies_to "
                f"{entry['applies_to']!r}; this repository indexes class rows "
                f"by corpus_id only"
            )
        rows.append(ClassRow(
            class_id=entry["class_id"], applies_to=entry["applies_to"],
            carrier=entry["carrier"], division=entry["division"],
            subtraction=entry["subtraction"],
        ))

    statement_rows = tuple(raw.get("statement_rows") or ())
    seen: set[str] = set()
    for entry in statement_rows:
        if not isinstance(entry, dict) or not isinstance(
            entry.get("statement_id"), str
        ):
            raise DomainSchemaError("every statement row needs a statement_id")
        statement_id = entry["statement_id"]
        if statement_id in seen:
            raise DomainSchemaError(
                f"{statement_id!r} appears in more than one row; a statement "
                f"with two declared domains has none"
            )
        seen.add(statement_id)
        if entry.get("carrier") not in carriers:
            raise DomainSchemaError(
                f"statement row {statement_id!r} declares an unknown carrier"
            )

    cuts = tuple(
        entry.get("cut_id", "") for entry in raw.get("branch_cuts") or ()
    )
    if not all(cuts):
        raise DomainSchemaError("every branch cut needs a cut_id")

    reviewed = raw.get("reviewed_output_roles") or {}
    role_rows = reviewed.get("roles") or []
    roles: set[str] = set()
    for entry in role_rows:
        if not isinstance(entry, dict):
            raise DomainSchemaError("every output-role row must be an object")
        role = entry.get("role")
        witness = entry.get("witness")
        if not isinstance(role, str) or not role:
            raise DomainSchemaError("every output-role row needs a role")
        if not isinstance(witness, str) or not witness:
            raise DomainSchemaError(
                f"output role {role!r} carries no witness; the design requires "
                f"a reviewed artifact, and a row nobody can check against a "
                f"corpus occurrence is not reviewed"
            )
        roles.add(role)

    digest = (
        sha256_lf(Path(path)) if Path(str(path)).is_file() else "<memory>"
    )
    return DomainSchema(
        schema_id=schema_id,
        frozen_at=str(raw.get("frozen_at", "")),
        carriers=carriers,
        class_rows=tuple(rows),
        statement_rows=statement_rows,
        branch_cuts=cuts,
        output_roles=frozenset(roles),
        digest=digest,
        path=str(path),
    )
