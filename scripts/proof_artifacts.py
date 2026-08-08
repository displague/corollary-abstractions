"""Closed-form parsing for native state--tactic--state proof artifacts."""

from __future__ import annotations

import json
from pathlib import Path


REQUIRED_TRANSITION_FIELDS = ("theorem", "tactic", "stateBefore", "stateAfter")


def load_complete_transitions(artifact_path: Path) -> tuple[dict, ...]:
    """Load a non-empty JSON artifact whose every row is a complete transition."""
    if artifact_path.suffix.casefold() != ".json":
        raise ValueError(
            f"cannot authenticate non-JSON proof artifact: {artifact_path}"
        )
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"verified_by artifact is not valid JSON: {artifact_path} ({exc})"
        ) from exc
    complete = (
        isinstance(payload, list)
        and bool(payload)
        and all(
            isinstance(row, dict)
            and all(
                isinstance(row.get(field), str)
                for field in REQUIRED_TRANSITION_FIELDS
            )
            and all(row[field].strip() for field in REQUIRED_TRANSITION_FIELDS)
            for row in payload
        )
    )
    if not complete:
        raise ValueError(
            "verified_by JSON artifact has malformed or no complete theorem "
            f"transitions: {artifact_path}"
        )
    return tuple(payload)


def select_closing_transitions(
    artifact_path: Path, reference: str | None
) -> tuple[tuple[dict, ...], str]:
    """Resolve one theorem identity and require at least one closing transition."""
    rows = load_complete_transitions(artifact_path)
    theorem_names = {row["theorem"] for row in rows}
    if reference is None:
        if len(theorem_names) != 1:
            raise ValueError(
                "artifact-only verified_by link is ambiguous across theorems "
                f"{sorted(theorem_names)!r}: {artifact_path}"
            )
        reference = next(iter(theorem_names))
    transitions = tuple(row for row in rows if row["theorem"] == reference)
    if not transitions:
        raise ValueError(
            f"verified_by reference {reference!r} is absent from {artifact_path}"
        )
    if not any(
        row["stateAfter"].strip().casefold() == "no goals" for row in transitions
    ):
        raise ValueError(
            f"verified_by {reference!r} does not close to no goals in "
            f"{artifact_path}"
        )
    return transitions, reference
