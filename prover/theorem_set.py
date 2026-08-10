#!/usr/bin/env python3
"""Loader for the versioned held-out theorem set (ROADMAP-v0.7 item 1).

The set is data, not code: ``theorems_v1.json`` names every theorem, its
family, its backend, its provenance, and a witness tactic sequence.  This
module only reads and validates it.

**The versioning rule.** A published curve names the set file *and* its
sha256.  Adding, removing, or correcting a theorem produces
``theorems_v2.json``; the v1 file is never edited afterwards.  That is what
makes an older solved-rate still mean what it meant when it was published --
the same discipline the corpus seeds follow, applied to an evaluation set.
:func:`digest` is the value a result file must record.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


PROVER_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PROVER_ROOT.parent
DEFAULT_SET = PROVER_ROOT / "theorems_v1.json"
TRAINING_EXTRACTION = PROVER_ROOT / "sample_triples.json"


@dataclass(frozen=True)
class Backend:
    name: str
    imports: tuple[str, ...]
    project: Path | None
    lean_path: Path | None

    @property
    def needs_project(self) -> bool:
        return self.project is not None

    def project_provenance(self) -> dict[str, object] | None:
        """Digest the source, toolchain, and exact compiled module in use."""
        if self.project is None or self.lean_path is None:
            return None
        source = self.project / "ProofCurve.lean"
        toolchain = self.project / "lean-toolchain"
        lakefile = self.project / "lakefile.toml"
        olean = self.lean_path / "ProofCurve.olean"
        return {
            "project": self.project.relative_to(REPO_ROOT).as_posix(),
            "source_sha256": digest(source),
            "toolchain_sha256": digest(toolchain),
            "lakefile_sha256": digest(lakefile),
            "olean_sha256": hashlib.sha256(olean.read_bytes()).hexdigest(),
        }


@dataclass(frozen=True)
class Theorem:
    id: str
    family: str
    backend: str
    held_out: bool
    source: str
    proposition: str
    witness: tuple[str, ...]


@dataclass(frozen=True)
class TheoremSet:
    set_id: str
    version: int
    path: Path
    sha256: str
    backends: dict[str, Backend]
    families: dict[str, str]
    theorems: tuple[Theorem, ...]

    @property
    def label(self) -> str:
        return f"{self.set_id}@v{self.version}"

    def by_family(self, family: str) -> tuple[Theorem, ...]:
        return tuple(item for item in self.theorems if item.family == family)

    def backend_of(self, theorem: Theorem) -> Backend:
        return self.backends[theorem.backend]

    def provenance(self) -> dict[str, object]:
        return {
            "set_id": self.set_id,
            "version": self.version,
            "file": self.path.name,
            "sha256": self.sha256,
            "theorems": len(self.theorems),
            "families": {
                family: len(self.by_family(family)) for family in self.families
            },
        }


def digest(path: Path = DEFAULT_SET) -> str:
    """Content digest stable across Git's LF/CRLF checkout conversion."""
    normalized = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def load(path: Path = DEFAULT_SET) -> TheoremSet:
    payload = json.loads(path.read_text(encoding="utf-8"))
    backends = {
        name: Backend(
            name=name,
            imports=tuple(spec["imports"]),
            project=(
                REPO_ROOT / spec["project"] if spec.get("project") else None
            ),
            lean_path=(
                REPO_ROOT / spec["project"] / spec["lean_path"]
                if spec.get("project") and spec.get("lean_path")
                else None
            ),
        )
        for name, spec in payload["backends"].items()
    }
    families = dict(payload["families"])
    theorems = tuple(
        Theorem(
            id=row["id"],
            family=row["family"],
            backend=row["backend"],
            held_out=bool(row["held_out"]),
            source=row["source"],
            proposition=row["proposition"],
            witness=tuple(row["witness"]),
        )
        for row in payload["theorems"]
    )
    seen: set[str] = set()
    for theorem in theorems:
        if theorem.id in seen:
            raise ValueError(f"duplicate theorem id {theorem.id!r}")
        seen.add(theorem.id)
        if theorem.family not in families:
            raise ValueError(
                f"{theorem.id!r} claims undeclared family {theorem.family!r}"
            )
        if theorem.backend not in backends:
            raise ValueError(
                f"{theorem.id!r} claims undeclared backend {theorem.backend!r}"
            )
        if not theorem.witness:
            raise ValueError(f"{theorem.id!r} has no witness sequence")
    return TheoremSet(
        set_id=payload["set_id"],
        version=int(payload["version"]),
        path=path,
        sha256=digest(path),
        backends=backends,
        families=families,
        theorems=theorems,
    )


def training_theorem_ids(
    path: Path = TRAINING_EXTRACTION,
) -> frozenset[str]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return frozenset(row["theorem"] for row in rows)


def training_states(path: Path = TRAINING_EXTRACTION) -> frozenset[str]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return frozenset(row["stateBefore"] for row in rows) | frozenset(
        row["stateAfter"] for row in rows
    )
