"""Closed-form parsing for native state--tactic--state proof artifacts."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path


REQUIRED_TRANSITION_FIELDS = ("theorem", "tactic", "stateBefore", "stateAfter")


def resolve_contained_artifact(repo_root: Path, artifact: str) -> Path:
    """Resolve an artifact path, refusing anything outside the repository.

    Shared by the validator and the retrieval loader so the containment
    boundary cannot drift between them (post-merge review of c3c144f,
    finding F1: containment lived only in the validator, and an
    out-of-root artifact whose bytes matched the trusted digest minted a
    trusted proof record in retrieval). Forward slashes only: a backslash
    separator would name a different file on POSIX than on Windows, so it
    is refused rather than normalized.
    """
    if "\\" in artifact:
        raise ValueError(
            "verified_by artifact paths must use forward slashes: "
            f"`{artifact}`"
        )
    artifact_path = Path(artifact)
    if artifact_path.is_absolute():
        raise ValueError(
            f"verified_by artifact must be repository-relative: `{artifact}`"
        )
    root = repo_root.resolve()
    resolved = (root / artifact_path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise ValueError(
            f"verified_by artifact escapes repository root: `{artifact}`"
        ) from None
    if not resolved.is_file():
        raise ValueError(
            f"verified_by artifact does not exist: `{artifact}`"
        )
    return resolved


def read_regular_file_once(path: Path) -> bytes:
    """Read one immutable snapshot, refusing links and non-regular files."""

    if path.is_symlink():
        raise ValueError(f"proof artifact may not be a symbolic link: {path}")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode) or not before.st_size:
                raise ValueError(f"proof artifact is not a non-empty regular file: {path}")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(descriptor, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            after = os.fstat(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise ValueError(f"proof artifact cannot be snapshotted: {path} ({exc})") from exc
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
    ):
        raise ValueError(f"proof artifact changed while it was being read: {path}")
    return b"".join(chunks)


def load_complete_transitions_bytes(payload_bytes: bytes, label: str = "<snapshot>") -> tuple[dict, ...]:
    """Parse complete transitions from bytes already captured once."""
    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"verified_by artifact is not valid JSON: {label} ({exc})") from exc
    complete = (
        isinstance(payload, list)
        and bool(payload)
        and all(
            isinstance(row, dict)
            and all(isinstance(row.get(field), str) for field in REQUIRED_TRANSITION_FIELDS)
            and all(row[field].strip() for field in REQUIRED_TRANSITION_FIELDS)
            for row in payload
        )
    )
    if not complete:
        raise ValueError(
            "verified_by JSON artifact has malformed or no complete theorem "
            f"transitions: {label}"
        )
    return tuple(payload)


def load_complete_transitions(artifact_path: Path) -> tuple[dict, ...]:
    """Load a non-empty JSON artifact whose every row is a complete transition."""
    if artifact_path.suffix.casefold() != ".json":
        raise ValueError(
            f"cannot authenticate non-JSON proof artifact: {artifact_path}"
        )
    return load_complete_transitions_bytes(read_regular_file_once(artifact_path), str(artifact_path))


def select_closing_transitions_bytes(
    payload_bytes: bytes, reference: str | None, label: str = "<snapshot>"
) -> tuple[tuple[dict, ...], str]:
    """Resolve a closing theorem from an immutable artifact snapshot."""
    rows = load_complete_transitions_bytes(payload_bytes, label)
    theorem_names = {row["theorem"] for row in rows}
    if reference is None:
        if len(theorem_names) != 1:
            raise ValueError(
                "artifact-only verified_by link is ambiguous across theorems "
                f"{sorted(theorem_names)!r}: {label}"
            )
        reference = next(iter(theorem_names))
    transitions = tuple(row for row in rows if row["theorem"] == reference)
    if not transitions:
        raise ValueError(f"verified_by reference {reference!r} is absent from {label}")
    if not any(row["stateAfter"].strip().casefold() == "no goals" for row in transitions):
        raise ValueError(f"verified_by {reference!r} does not close to no goals in {label}")
    return transitions, reference


def select_closing_transitions(
    artifact_path: Path, reference: str | None
) -> tuple[tuple[dict, ...], str]:
    """Resolve one theorem identity and require at least one closing transition."""
    if artifact_path.suffix.casefold() != ".json":
        raise ValueError(
            f"cannot authenticate non-JSON proof artifact: {artifact_path}"
        )
    return select_closing_transitions_bytes(
        read_regular_file_once(artifact_path), reference, str(artifact_path)
    )
