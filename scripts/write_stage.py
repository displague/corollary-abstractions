#!/usr/bin/env python3
"""PROVEN-gated staging for model-initiated durable writes.

`RETRIEVE` is the UNKNOWN-triggered action: the system does not know something,
so it reads. `WRITE` is its PROVEN-gated dual: the system has a machine-checked
proof, so it PROPOSES that the durable corpus grow. The asymmetry is deliberate
and total -- reading is cheap and reversible, writing is neither -- so this
module stages proposals and never accepts one.

**No runtime action writes `data/*/nodes.json`.** That is the roadmap's flat
prohibition, and it is enforced three ways rather than promised once:

1. a WRITE candidate names a SEED, not a corpus file; a candidate whose edit
   target resolves anywhere under `data/` is REFUSED at the first gate, before
   any file is touched;
2. regeneration runs in a scratch copy OUTSIDE the repository, with the
   candidate's seed executed at that copy's root, so the byte-identity rule the
   project already enforces (`scripts/check_regeneration.py`) is exercised
   against the candidate instead of against the durable tree;
3. the durable tree is digested before and after every staging attempt --
   accepted, refused, or crashed -- and the two digests are written into the
   receipt. A refusal that changed a byte would be visible in its own receipt.

The gate matrix, which is the whole point of the module:

| claimed rung | correspondence | outcome |
|---|---|---|
| PROVEN | CORRESPONDS | `STAGED_CANDIDATE` -- full candidate, awaiting review |
| PROVEN | MISMATCH | `REFUSED` |
| PROVEN | UNTRANSLATABLE | `REFUSED` (fails closed; see below) |
| VERIFIED | not consulted | `STAGED_REVIEW_REQUEST` -- no candidate content |
| CONJECTURED | not consulted | `REFUSED` |
| any, frame-local | not consulted | `REFUSED` |

UNTRANSLATABLE refuses here while `scripts/proof_correspondence.py` merely
reports it. That is not an inconsistency, it is the difference between a lint and
a gate: a citation this rung cannot read is not thereby a wrong citation (so the
corpus is not failed for it), but it is also not a proof this rung can rely on
(so it cannot buy durable promotion). Fail open in the report, fail closed in the
gate.

Acceptance pipeline for a PROVEN candidate, in order, every step able to refuse:

  path containment -> rung -> artifact digest pin -> theorem closes to no goals
  -> declared transition trace is really in the artifact -> theorem is unowned
  -> scratch regeneration -> regeneration is CONFINED to the declared corpus and
  adds exactly the declared statement -> semantic correspondence -> STRUCTURAL
  UNAMBIGUITY -> schema and link validation of the merged scratch graph ->
  matcher delta measured and compared against the candidate's DECLARED delta ->
  durable byte-identity.

The structural-unambiguity gate is strictly stronger than what the committed
corpus is held to, and deliberately so. `scripts/proof_correspondence.py`
documents that skeleton correspondence cannot distinguish a statement from its
cross-discipline structural twin, and reports `ambiguous_with` rather than
failing -- the sixteen committed links are human-authored and each already owns
its theorem exclusively. A WRITE, by contrast, would MANUFACTURE a new instance
of that hole, so a candidate whose regenerated skeleton is also declared by some
committed statement is refused instead of staged with a caveat nobody is obliged
to read.

Nothing in that list accepts. A `STAGED_CANDIDATE` carries
`approval_required: ["human_or_prover_review"]` and `approval_granted: []`;
promotion is a human editing the seed and running the ordinary loop. The
system may prove a theorem and lay a candidate on the table; it may not put it
in the corpus.

**Declared limit: executing a candidate seed is not sandboxed.** Regeneration is
real -- the candidate's seed source is run -- and running code cannot be
contained by a static screen. The scratch copy lives outside the repository, the
subprocess is given no repository path in argv or environment, and two cheap
escapes a NON-adversarial mistake would produce (absolute path literals, `..`
literals) are screened out; but a determined candidate could still reach the
durable tree, which is why the before/after digest exists and why the receipt
records both. Read a candidate's seed source before staging it. Filed in
docs/BACKLOG.md.

Staging area (`staging/`): the DIRECTORY and its README are committed, the
RECORDS are not (`staging/.gitignore`). A staging record is runtime output, and
runtime output that lands in git by default is how policy output quietly becomes
trusted knowledge -- the exact failure this whole item exists to prevent. But
the path must be a declared part of the repository rather than an ambient temp
directory, or a receipt is not something a reviewer can be pointed at. Attaching
a specific receipt to a review is a deliberate `git add -f`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - CLI import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import match_signatures  # noqa: E402
from controller import (  # noqa: E402
    Action,
    ActionKind,
    Verdict,
    Verification,
)
from proof_artifacts import (  # noqa: E402
    REQUIRED_TRANSITION_FIELDS,
    resolve_contained_artifact,
    select_closing_transitions,
)
from proof_correspondence import (  # noqa: E402
    CORRESPONDS,
    check_link,
    declared_forms,
    load_corpus_nodes,
)


REPO_ROOT = Path(__file__).resolve().parents[1]

STAGED_CANDIDATE = "STAGED_CANDIDATE"
STAGED_REVIEW_REQUEST = "STAGED_REVIEW_REQUEST"
REFUSED = "REFUSED"

PROVEN = "PROVEN"
VERIFIED = "VERIFIED"
CONJECTURED = "CONJECTURED"
RUNGS = (PROVEN, VERIFIED, CONJECTURED)

# Directories a scratch checkout needs for the full acceptance pipeline: the
# seeds and validator, the corpora they regenerate, the proof artifacts
# `verified_by` resolves against, and the schema the validator reads.
SCRATCH_TREES = ("scripts", "data", "prover", "schema")

_SEED_NAME = re.compile(r"^seed_[a-z0-9_]+\.py$")
_MATCHER_DELTA_KEYS = frozenset(
    {
        "nodes_analyzed",
        "shape_groups",
        "typed_groups",
        "family_groups",
        "aliased_groups",
        "mirror_groups",
        "new_typed_twin_partners",
    }
)


class Refusal(Exception):
    """A gate said no. Carries the reason that goes into the receipt."""

    def __init__(self, check: str, detail: str):
        super().__init__(f"{check}: {detail}")
        self.check = check
        self.detail = detail


# --------------------------------------------------------------------------
# The candidate
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class WriteCandidate:
    """One proposed durable addition, with everything needed to judge it.

    `seed_source` is the FULL text the seed script should have after the edit,
    not a node payload: a candidate that could declare its node directly could
    declare a node its seed does not actually produce, and the regeneration
    check would be checking the candidate's own claim. The node judged here is
    the one the scratch regeneration EMITS.
    """

    statement_id: str
    corpus: str
    seed_script: str
    seed_source: str
    rung: str
    rationale: str = ""
    artifact: str = ""
    artifact_sha256: str = ""
    reference: str = ""
    transition_trace: tuple[dict, ...] = ()
    expected_matcher_delta: dict | None = None
    frame_local: bool = False

    def payload(self) -> dict:
        """Canonical, order-stable view used for the record id."""

        return {
            "statement_id": self.statement_id,
            "corpus": self.corpus,
            "seed_script": self.seed_script,
            "seed_source_sha256": hashlib.sha256(
                self.seed_source.encode("utf-8")
            ).hexdigest(),
            "rung": self.rung,
            "artifact": self.artifact,
            "artifact_sha256": self.artifact_sha256,
            "reference": self.reference,
            "transition_trace": [
                {key: row[key] for key in sorted(row)}
                for row in self.transition_trace
            ],
            "expected_matcher_delta": self.expected_matcher_delta,
            "frame_local": self.frame_local,
        }

    @property
    def record_id(self) -> str:
        canonical = json.dumps(
            self.payload(), sort_keys=True, ensure_ascii=False
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()[:16]


@dataclass
class StagingRecord:
    """The diffable receipt. Written for accepted AND refused candidates."""

    record_id: str
    statement_id: str
    outcome: str
    rung: str
    checks: list[dict] = field(default_factory=list)
    refusal: dict | None = None
    correspondence: dict | None = None
    matcher_delta: dict | None = None
    staged: dict | None = None
    durable_digest_before: str = ""
    durable_digest_after: str = ""
    approval_required: tuple[str, ...] = ()
    approval_granted: tuple[str, ...] = ()

    def passed(self, check: str, detail: str) -> None:
        self.checks.append({"check": check, "status": "PASS", "detail": detail})

    def as_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "statement_id": self.statement_id,
            "outcome": self.outcome,
            "claimed_rung": self.rung,
            "checks": self.checks,
            "refusal": self.refusal,
            "correspondence": self.correspondence,
            "matcher_delta": self.matcher_delta,
            "staged": self.staged,
            "durable_store": {
                "digest_before": self.durable_digest_before,
                "digest_after": self.durable_digest_after,
                "byte_identical": (
                    self.durable_digest_before == self.durable_digest_after
                ),
            },
            "approval_required": list(self.approval_required),
            "approval_granted": list(self.approval_granted),
        }

    def render(self) -> str:
        """Deterministic bytes: no clock, no temp paths, sorted keys."""

        return json.dumps(
            self.as_dict(), indent=2, sort_keys=True, ensure_ascii=False
        ) + "\n"


# --------------------------------------------------------------------------
# Durable-store integrity
# --------------------------------------------------------------------------


def durable_digest(data_dir: Path) -> str:
    """One digest over every committed corpus file, path-sensitive."""

    digest = hashlib.sha256()
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file():
            continue
        digest.update(path.relative_to(data_dir).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _resolve_seed_target(repo_root: Path, target: str) -> Path:
    """Refuse every edit target that is not a repository seed script.

    First gate, deliberately: `data/logic/nodes.json` must be refused as a
    NAME, before any pipeline stage has had the chance to touch a file.
    """

    if "\\" in target:
        raise Refusal(
            "path_containment",
            f"WRITE targets must use forward slashes: {target!r}",
        )
    candidate = Path(target)
    if candidate.is_absolute():
        raise Refusal(
            "path_containment",
            f"WRITE target must be repository-relative: {target!r}",
        )
    resolved = (repo_root.resolve() / candidate).resolve()
    try:
        relative = resolved.relative_to(repo_root.resolve())
    except ValueError:
        raise Refusal(
            "path_containment",
            f"WRITE target escapes the repository: {target!r}",
        ) from None
    parts = relative.as_posix().split("/")
    if parts[0] == "data":
        raise Refusal(
            "path_containment",
            "the durable store is never a WRITE target; a candidate edits a "
            f"seed and the corpus is regenerated: {target!r}",
        )
    if len(parts) != 2 or parts[0] != "scripts" or not _SEED_NAME.match(parts[1]):
        raise Refusal(
            "path_containment",
            f"WRITE target must be `scripts/seed_<name>.py`: {target!r}",
        )
    return resolved


def _resolve_contained_input(repo_root: Path, target: str) -> Path:
    """Resolve an existing repository file a proposal is allowed to name.

    Same containment discipline as `proof_artifacts.resolve_contained_artifact`
    (forward slashes only, relative only, no escape), plus the rule this module
    adds everywhere: `data/` is not an input either. A proposal that could read
    a corpus file could smuggle corpus bytes into a staged record and make them
    look like the candidate's own.
    """

    if "\\" in target:
        raise Refusal(
            "path_containment",
            f"proposal paths must use forward slashes: {target!r}",
        )
    if Path(target).is_absolute():
        raise Refusal(
            "path_containment",
            f"proposal path must be repository-relative: {target!r}",
        )
    resolved = (repo_root.resolve() / target).resolve()
    try:
        relative = resolved.relative_to(repo_root.resolve())
    except ValueError:
        raise Refusal(
            "path_containment",
            f"proposal path escapes the repository: {target!r}",
        ) from None
    if relative.as_posix().split("/")[0] == "data":
        raise Refusal(
            "path_containment",
            f"the durable store is not a proposal input: {target!r}",
        )
    if not resolved.is_file():
        raise Refusal("path_containment", f"proposal does not exist: {target!r}")
    return resolved


def _screen_seed_source(source: str) -> None:
    """Cheap screen for the two escapes a non-adversarial mistake produces.

    NOT a sandbox -- see the module docstring. It refuses a seed that names an
    absolute path or a parent-directory literal, both of which would leave the
    scratch checkout by accident rather than by design.
    """

    for pattern, detail in (
        (r"""['"][A-Za-z]:[\\/]""", "absolute Windows path literal"),
        (r"""['"]/[A-Za-z]""", "absolute POSIX path literal"),
        (r"\.\.[\\/]", "parent-directory path literal"),
    ):
        if re.search(pattern, source):
            raise Refusal(
                "seed_source_screen",
                f"candidate seed contains an {detail}; regeneration must stay "
                "inside the scratch checkout",
            )


# --------------------------------------------------------------------------
# Scratch regeneration
# --------------------------------------------------------------------------


def _subprocess_env() -> dict[str, str]:
    """A minimal environment: no repository path reaches the child process.

    `SystemRoot`/`COMSPEC`/`PATHEXT` are Windows requirements for starting a
    Python interpreter at all, and the temp variables keep the child's own
    scratch needs off the repository; nothing else is inherited.
    """

    import os

    env = {"PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
    for name in ("SystemRoot", "SYSTEMROOT", "COMSPEC", "PATHEXT", "TEMP", "TMP"):
        value = os.environ.get(name)
        if value:
            env[name] = value
    return env


def _scratch_checkout(repo_root: Path, destination: Path) -> None:
    for tree in SCRATCH_TREES:
        source = repo_root / tree
        if source.is_dir():
            shutil.copytree(
                source,
                destination / tree,
                ignore=shutil.ignore_patterns("__pycache__"),
            )


def _corpus_snapshot(data_dir: Path) -> dict[str, bytes]:
    return {
        path.relative_to(data_dir).as_posix(): path.read_bytes()
        for path in sorted(data_dir.rglob("*"))
        if path.is_file()
    }


def _statement_ids(payload: bytes) -> list[str]:
    corpus = json.loads(payload.decode("utf-8"))
    return [node.get("statement_id", "") for node in corpus.get("statement_nodes", [])]


def _regenerate(
    candidate: WriteCandidate, repo_root: Path, scratch: Path
) -> tuple[dict, str]:
    """Run the candidate seed in the scratch checkout; return (node, detail).

    Refuses unless the regeneration is CONFINED: every corpus other than the
    candidate's is byte-identical to the durable tree, and the candidate's
    corpus differs only by gaining exactly the declared statement id.
    """

    _scratch_checkout(repo_root, scratch)
    seed_path = scratch / candidate.seed_script
    seed_path.parent.mkdir(parents=True, exist_ok=True)
    seed_path.write_text(candidate.seed_source, encoding="utf-8")

    # cwd is the scratch ROOT because that is where a seed writes: every
    # `scripts/seed_*.py` in this repository emits `Path("data") / discipline /
    # "nodes.json"` relative to the working directory. The argv path is
    # relative for the same reason the environment is minimal -- the subprocess
    # is handed no route back to the repository.
    result = subprocess.run(
        [sys.executable, str(Path(candidate.seed_script))],
        cwd=str(scratch),
        capture_output=True,
        text=True,
        env=_subprocess_env(),
    )
    if result.returncode != 0:
        raise Refusal(
            "scratch_regeneration",
            "candidate seed failed: "
            + _scrub(result.stderr.strip()[-400:], scratch),
        )

    before = _corpus_snapshot(repo_root / "data")
    after = _corpus_snapshot(scratch / "data")
    target = f"{candidate.corpus}/nodes.json"

    for name in sorted(set(before) | set(after)):
        if name == target:
            continue
        if before.get(name) != after.get(name):
            raise Refusal(
                "regeneration_confinement",
                f"candidate seed changed `data/{name}`, which it does not "
                "declare; a WRITE may only extend its own corpus",
            )
    if target not in after:
        raise Refusal(
            "regeneration_confinement",
            f"candidate seed produced no `data/{target}`",
        )

    old_ids = _statement_ids(before[target]) if target in before else []
    new_corpus = json.loads(after[target].decode("utf-8"))
    new_ids = [node.get("statement_id", "") for node in new_corpus.get("statement_nodes", [])]
    added = [sid for sid in new_ids if sid not in set(old_ids)]
    removed = [sid for sid in old_ids if sid not in set(new_ids)]
    if removed:
        raise Refusal(
            "regeneration_confinement",
            f"candidate seed removes existing statements: {', '.join(removed)}",
        )
    if added != [candidate.statement_id]:
        raise Refusal(
            "regeneration_confinement",
            f"candidate seed adds {added or 'nothing'}, but the candidate "
            f"declares `{candidate.statement_id}`",
        )
    if len(new_ids) != len(set(new_ids)):
        raise Refusal(
            "regeneration_confinement", "candidate corpus has duplicate ids"
        )

    node = next(
        node
        for node in new_corpus["statement_nodes"]
        if node.get("statement_id") == candidate.statement_id
    )
    detail = (
        f"seed regenerated `data/{target}`; every other corpus byte-identical; "
        f"exactly one statement added"
    )
    return node, detail


def _scrub(text: str, scratch: Path) -> str:
    """Keep receipts diffable: a temp path differs on every run."""

    return text.replace(str(scratch), "<scratch>").replace(
        str(scratch).replace("\\", "/"), "<scratch>"
    )


def _validate(scratch: Path) -> str:
    result = subprocess.run(
        [
            sys.executable,
            str(scratch / "scripts" / "validate_nodes.py"),
            "--data-dir",
            str(scratch / "data"),
            "--schema",
            str(scratch / "schema" / "equation-node.schema.json"),
        ],
        cwd=str(scratch),
        capture_output=True,
        text=True,
        env=_subprocess_env(),
    )
    if result.returncode != 0:
        raise Refusal(
            "schema_and_link_validation",
            _scrub((result.stdout + result.stderr).strip()[-800:], scratch),
        )
    return _scrub(result.stdout.strip().splitlines()[-1], scratch)


# --------------------------------------------------------------------------
# Matcher delta
# --------------------------------------------------------------------------


def _matcher_summary(data_dir: Path) -> tuple[dict, dict[str, str]]:
    nodes, problems = match_signatures.load_nodes(data_dir)
    report = match_signatures.build_report(nodes, problems)
    counts = report["group_counts"]
    summary = {
        "nodes_analyzed": report["nodes_analyzed"],
        "shape_groups": counts["shape"],
        "typed_groups": counts["typed"],
        "family_groups": counts["family"],
        "aliased_groups": counts["aliased"],
        "mirror_groups": counts["mirror"],
        "ladder_violations": len(report["ladder_violations"]),
        "parse_problems": len(report["parse_problems"]),
        "slot_schema_gaps": len(report["slot_schema_gaps"]),
    }
    typed_of = {n.statement_id: n.typed for n in nodes}
    return summary, typed_of


def _measure_matcher_delta(
    repo_data: Path, scratch_data: Path, statement_id: str
) -> dict:
    before, _ = _matcher_summary(repo_data)
    after, typed_after = _matcher_summary(scratch_data)
    typed = typed_after.get(statement_id)
    partners = sorted(
        other
        for other, key in typed_after.items()
        if other != statement_id and key == typed
    )
    delta = {
        key: after[key] - before[key]
        for key in sorted(set(before) & set(after))
    }
    delta["new_typed_twin_partners"] = partners
    return {
        "before": before,
        "after": after,
        "delta": delta,
        "candidate_typed_skeleton": typed,
    }


def _compare_declared_delta(candidate: WriteCandidate, measured: dict) -> str:
    declared = candidate.expected_matcher_delta
    if not isinstance(declared, dict):
        raise Refusal(
            "matcher_delta_prediction",
            "a PROVEN candidate must DECLARE its matcher delta before it is "
            "measured; an undeclared delta is an unregistered prediction",
        )
    extras = sorted(set(declared) - _MATCHER_DELTA_KEYS)
    if extras:
        raise Refusal(
            "matcher_delta_prediction",
            f"unknown declared delta keys: {', '.join(extras)}",
        )
    missing = sorted(_MATCHER_DELTA_KEYS - set(declared))
    if missing:
        raise Refusal(
            "matcher_delta_prediction",
            f"declared delta omits: {', '.join(missing)}",
        )
    # Types are checked before values because Python's `True == 1` would let a
    # declaration of `true` satisfy a measured delta of 1, and a JSON proposal
    # is exactly where that spelling arrives. `bool` is excluded explicitly:
    # `isinstance(True, int)` is also true.
    for key in sorted(_MATCHER_DELTA_KEYS - {"new_typed_twin_partners"}):
        value = declared[key]
        if isinstance(value, bool) or not isinstance(value, int):
            raise Refusal(
                "matcher_delta_prediction",
                f"declared delta `{key}` must be an integer, got "
                f"{type(value).__name__}",
            )
    partners = declared["new_typed_twin_partners"]
    if not isinstance(partners, (list, tuple)) or not all(
        isinstance(item, str) for item in partners
    ):
        raise Refusal(
            "matcher_delta_prediction",
            "declared `new_typed_twin_partners` must be a list of statement ids",
        )
    actual = {key: measured["delta"][key] for key in _MATCHER_DELTA_KEYS}
    normalized = {
        key: (
            sorted(value)
            if key == "new_typed_twin_partners"
            else value
        )
        for key, value in declared.items()
    }
    if normalized != actual:
        differing = sorted(
            key for key in _MATCHER_DELTA_KEYS if normalized[key] != actual[key]
        )
        raise Refusal(
            "matcher_delta_prediction",
            "declared matcher delta does not match the measured one for "
            + ", ".join(
                f"{key} (declared {normalized[key]!r}, measured {actual[key]!r})"
                for key in differing
            ),
        )
    return "declared matcher delta matches the delta measured in the scratch checkout"


# --------------------------------------------------------------------------
# Proof gating
# --------------------------------------------------------------------------


def _is_subsequence(trace: tuple[dict, ...], rows: tuple[dict, ...]) -> bool:
    index = 0
    for row in rows:
        if index < len(trace) and all(
            row.get(key) == value for key, value in trace[index].items()
        ):
            index += 1
    return index == len(trace)


def _check_proof(candidate: WriteCandidate, repo_root: Path) -> list[tuple[str, str]]:
    """Digest pin, closure, and trace membership. Returns passed checks."""

    if not candidate.artifact or not candidate.reference:
        raise Refusal(
            "proof_artifact",
            "a PROVEN candidate must name both an artifact and a theorem",
        )
    try:
        artifact_path = resolve_contained_artifact(repo_root, candidate.artifact)
    except ValueError as exc:
        raise Refusal("proof_artifact", str(exc)) from None
    digest = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    if not candidate.artifact_sha256:
        raise Refusal(
            "artifact_digest_pin",
            "a PROVEN candidate must pin the artifact digest it proved against",
        )
    if digest != candidate.artifact_sha256:
        raise Refusal(
            "artifact_digest_pin",
            f"artifact digest is {digest}, candidate pinned "
            f"{candidate.artifact_sha256}",
        )
    try:
        transitions, resolved = select_closing_transitions(
            artifact_path, candidate.reference
        )
    except ValueError as exc:
        raise Refusal("theorem_closure", str(exc)) from None
    if not candidate.transition_trace:
        raise Refusal(
            "transition_trace",
            "a PROVEN candidate must carry the transition trace it claims",
        )
    # Self-review: `_is_subsequence` matches a declared row when every key it
    # states agrees, so a row stating NOTHING would match anything and an empty
    # trace of empty rows would sail through. Completeness is required.
    for row in candidate.transition_trace:
        missing = [
            field
            for field in REQUIRED_TRANSITION_FIELDS
            if not isinstance(row.get(field), str) or not row[field].strip()
        ]
        if missing:
            raise Refusal(
                "transition_trace",
                "declared transitions must be complete; missing "
                + ", ".join(missing),
            )
    if not _is_subsequence(candidate.transition_trace, transitions):
        raise Refusal(
            "transition_trace",
            "the declared transition trace is not a subsequence of the "
            f"artifact's transitions for {resolved}",
        )
    return [
        ("artifact_digest_pin", f"artifact bytes pin to {digest}"),
        (
            "theorem_closure",
            f"{resolved} resolves to {len(transitions)} transitions closing to "
            "no goals",
        ),
        (
            "transition_trace",
            f"{len(candidate.transition_trace)} declared transitions are an "
            "in-order subsequence of the artifact's",
        ),
    ]


def _check_unowned(candidate: WriteCandidate, repo_root: Path) -> str:
    owners = [
        node["statement_id"]
        for node in load_corpus_nodes(repo_root / "data")
        for link in node.get("verified_by", []) or []
        if isinstance(link, dict) and link.get("reference") == candidate.reference
    ]
    if owners:
        raise Refusal(
            "exclusive_theorem_ownership",
            f"{candidate.reference} is already cited by {', '.join(sorted(owners))}",
        )
    return f"{candidate.reference} is cited by no committed statement"


def _check_correspondence(
    node: dict,
    candidate: WriteCandidate,
    repo_root: Path,
    record: "StagingRecord",
) -> dict:
    links = [
        link for link in node.get("verified_by", []) or [] if isinstance(link, dict)
    ]
    if len(links) != 1:
        raise Refusal(
            "semantic_correspondence",
            f"a staged candidate must carry exactly one verified_by link, "
            f"found {len(links)}",
        )
    link = links[0]
    if link.get("artifact") != candidate.artifact or link.get(
        "reference"
    ) != candidate.reference:
        raise Refusal(
            "semantic_correspondence",
            "the regenerated node cites a different theorem than the candidate "
            f"declares: {link.get('artifact')}:{link.get('reference')}",
        )
    corpus_forms = {
        other["statement_id"]: declared_forms(other)
        for other in load_corpus_nodes(repo_root / "data")
        if other.get("statement_id")
    }
    result = check_link(node, link, repo_root, corpus_forms)
    # Recorded BEFORE any refusal: "a diffable receipt explaining why" is worth
    # little if the MISMATCH receipt omits the skeletons that mismatched.
    record.correspondence = result.as_dict()
    if result.verdict != CORRESPONDS:
        raise Refusal(
            "semantic_correspondence",
            f"{result.verdict}: {result.reason}",
        )
    if result.ambiguous_with:
        # Self-review, the forgery attack: correspondence is STRUCTURAL, and the
        # corpus's cross-discipline twins share structure exactly. For the
        # sixteen committed links this is a documented limit -- they are
        # human-authored and each already owns its theorem exclusively -- but a
        # WRITE must not MANUFACTURE new instances of it. A candidate whose
        # regenerated skeleton is also declared by an existing statement cannot
        # be certified to be the statement the theorem proves, so it is refused
        # rather than staged with a caveat nobody is obliged to read.
        raise Refusal(
            "structural_unambiguity",
            "the theorem's skeleton is also declared by "
            + ", ".join(result.ambiguous_with)
            + "; structural correspondence cannot say which statement it "
            "proves, so a new durable claim on it is refused",
        )
    return result.as_dict()


# --------------------------------------------------------------------------
# The gate
# --------------------------------------------------------------------------


def stage_write(
    candidate: WriteCandidate,
    repo_root: Path = REPO_ROOT,
    staging_dir: Path | None = None,
) -> StagingRecord:
    """Judge one WRITE candidate and write its receipt. Never accepts."""

    repo_root = repo_root.resolve()
    data_dir = repo_root / "data"
    if staging_dir is not None:
        # Self-review: every candidate-controlled path is contained, but the
        # CALLER-supplied receipt directory was not, and a receipt written into
        # `data/` would be this module writing to the durable store by its own
        # hand. A misconfigured caller is a programmer error, not a candidate
        # to be judged, so it raises rather than producing a REFUSED record.
        resolved_staging = staging_dir.resolve()
        if resolved_staging == data_dir or data_dir in resolved_staging.parents:
            raise ValueError(
                f"staging directory may not live under the durable store: "
                f"{staging_dir}"
            )
    record = StagingRecord(
        record_id=candidate.record_id,
        statement_id=candidate.statement_id,
        outcome=REFUSED,
        rung=candidate.rung,
        durable_digest_before=durable_digest(data_dir),
    )
    try:
        _gate(candidate, repo_root, record)
    except Refusal as refusal:
        record.outcome = REFUSED
        record.refusal = {"check": refusal.check, "detail": refusal.detail}
        record.checks.append(
            {"check": refusal.check, "status": "REFUSED", "detail": refusal.detail}
        )
    record.durable_digest_after = durable_digest(data_dir)
    if record.durable_digest_after != record.durable_digest_before:
        # Belt and braces: nothing above writes to data/, so this can only fire
        # if a candidate seed escaped the scratch checkout. It is a refusal even
        # for an otherwise perfect candidate, and the receipt says why.
        record.outcome = REFUSED
        record.staged = None
        record.refusal = {
            "check": "durable_store_byte_identity",
            "detail": "the durable store changed during staging; the candidate "
            "seed escaped the scratch checkout",
        }
        record.checks.append(
            {
                "check": "durable_store_byte_identity",
                "status": "REFUSED",
                "detail": record.refusal["detail"],
            }
        )
    else:
        record.passed(
            "durable_store_byte_identity",
            "data/ is byte-identical before and after this attempt",
        )
    if staging_dir is not None:
        staging_dir.mkdir(parents=True, exist_ok=True)
        (staging_dir / f"{record.record_id}.json").write_text(
            record.render(), encoding="utf-8"
        )
    return record


def _gate(
    candidate: WriteCandidate, repo_root: Path, record: StagingRecord
) -> None:
    if candidate.rung not in RUNGS:
        raise Refusal(
            "epistemic_rung", f"unknown epistemic rung {candidate.rung!r}"
        )
    if candidate.frame_local:
        raise Refusal(
            "epistemic_rung",
            "frame-local content is session-scoped and may not request durable "
            "promotion; prove it separately first",
        )
    if candidate.rung == CONJECTURED:
        raise Refusal(
            "epistemic_rung",
            "CONJECTURED material stays in the proposal queue; a conjecture "
            "cannot request durable promotion",
        )

    _resolve_seed_target(repo_root, candidate.seed_script)
    record.passed(
        "path_containment",
        f"edit target `{candidate.seed_script}` is a repository seed script, "
        "not a corpus file",
    )

    if candidate.rung == VERIFIED:
        # Review only: the record deliberately carries NO candidate content --
        # no seed source, no node, no artifact -- because a VERIFIED claim has
        # not earned a staged edit, only a human's attention.
        record.outcome = STAGED_REVIEW_REQUEST
        record.approval_required = ("human_review",)
        record.staged = {
            "kind": "review_request",
            "statement_id": candidate.statement_id,
            "corpus": candidate.corpus,
            "seed_script": candidate.seed_script,
            "rationale": candidate.rationale,
        }
        record.passed(
            "epistemic_rung",
            "VERIFIED stages a review request only; no candidate content is "
            "staged and no seed is executed",
        )
        return

    record.passed("epistemic_rung", "PROVEN may stage a full candidate")
    for check, detail in _check_proof(candidate, repo_root):
        record.passed(check, detail)
    record.passed(
        "exclusive_theorem_ownership", _check_unowned(candidate, repo_root)
    )
    _screen_seed_source(candidate.seed_source)
    record.passed(
        "seed_source_screen",
        "no absolute or parent-directory path literal in the candidate seed "
        "(a screen, not a sandbox)",
    )

    with tempfile.TemporaryDirectory(prefix="write-stage-") as temporary:
        scratch = Path(temporary) / "scratch"
        node, detail = _regenerate(candidate, repo_root, scratch)
        record.passed("scratch_regeneration", detail)
        record.passed("regeneration_confinement", detail)
        _check_correspondence(node, candidate, repo_root, record)
        record.passed(
            "semantic_correspondence",
            f"CORRESPONDS via the candidate's "
            f"{record.correspondence['matched_route']} form",
        )
        record.passed(
            "structural_unambiguity",
            "no committed statement declares the theorem's skeleton",
        )
        record.passed("schema_and_link_validation", _validate(scratch))
        measured = _measure_matcher_delta(
            repo_root / "data", scratch / "data", candidate.statement_id
        )
        record.matcher_delta = measured
        record.passed(
            "matcher_delta_prediction", _compare_declared_delta(candidate, measured)
        )
        record.staged = {
            "kind": "seed_candidate",
            "statement_id": candidate.statement_id,
            "corpus": candidate.corpus,
            "seed_script": candidate.seed_script,
            "seed_source_sha256": candidate.payload()["seed_source_sha256"],
            "seed_source": candidate.seed_source,
            "node": node,
            "proof": {
                "system": "lean4",
                "artifact": candidate.artifact,
                "artifact_sha256": candidate.artifact_sha256,
                "reference": candidate.reference,
                "transition_trace": candidate.payload()["transition_trace"],
            },
            "rationale": candidate.rationale,
        }
    record.outcome = STAGED_CANDIDATE
    record.approval_required = ("human_or_prover_review",)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


# --------------------------------------------------------------------------
# The controller adapter
#
# `ActionKind.WRITE` has been vocabulary since v0.5 with nothing behind it,
# because the obvious adapter is a category error: a verifier that returned
# PROVEN with a next state for "add this to the corpus" would make a PROPOSAL
# look like an accepted step, which is the one thing this item exists to
# prevent.
#
# The way out is to be exact about what the action is. `WRITE(proposal)` does
# not mean "add this knowledge"; it means "put this proposal on the table". So
# the state the controller advances is a RECEIPT LEDGER -- record ids and
# outcomes, no corpus content, no node, no seed source -- and accepting a WRITE
# means a receipt now exists, not that anything was learned. A refused
# candidate leaves the ledger untouched, exactly like every other refused
# branch in `controller.py`.
#
# The rung mapping follows the same discipline: a staged CANDIDATE is PROVEN
# (a machine-checked proof carried it through every gate), a staged REVIEW
# REQUEST is VERIFIED (a corpus-level assertion earned a human's attention, no
# more), and everything else is REFUSED. What advances is the ledger; the
# corpus is asserted byte-identical by the same digest the receipt carries.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class WriteStagingState:
    """A ledger of receipts. Deliberately incapable of holding knowledge."""

    receipts: tuple[tuple[str, str], ...] = ()

    def with_receipt(self, record_id: str, outcome: str) -> "WriteStagingState":
        return WriteStagingState(self.receipts + ((record_id, outcome),))


def write_action(proposal: str) -> Action:
    """`WRITE(proposal)` -- stage the proposal at this repository-relative path."""

    return Action.build(ActionKind.WRITE, "stage", {"proposal": proposal})


class WriteStagingVerifier:
    """Controller adapter for `ActionKind.WRITE`. Stages; never promotes."""

    name = "write-staging"

    def __init__(self, repo_root: Path = REPO_ROOT, staging_dir: Path | None = None):
        self.repo_root = repo_root.resolve()
        self.staging_dir = staging_dir

    def state_key(self, state: WriteStagingState) -> str:
        return repr(state.receipts)

    def evaluate(
        self, state: WriteStagingState, action: Action
    ) -> Verification[WriteStagingState]:
        if action.kind is not ActionKind.WRITE:
            return Verification(
                Verdict.REFUSED,
                f"{self.name} evaluates WRITE only, got {action.kind.value}",
            )
        proposal = action.argument("proposal")
        if not proposal:
            return Verification(
                Verdict.REFUSED, "WRITE requires a `proposal` argument"
            )
        try:
            path = _resolve_contained_input(self.repo_root, proposal)
            payload = json.loads(path.read_text(encoding="utf-8"))
            candidate = candidate_from_json(payload, self.repo_root)
        except Refusal as refusal:
            return Verification(Verdict.REFUSED, str(refusal))
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError) as exc:
            return Verification(
                Verdict.REFUSED, f"proposal is unreadable: {exc}"
            )

        record = stage_write(candidate, self.repo_root, self.staging_dir)
        evidence = (
            f"record_id={record.record_id}",
            f"outcome={record.outcome}",
            f"durable_byte_identical="
            f"{record.durable_digest_before == record.durable_digest_after}",
        )
        if record.outcome == REFUSED:
            detail = record.refusal["check"] if record.refusal else "refused"
            return Verification(
                Verdict.REFUSED,
                f"candidate refused at {detail}",
                evidence=evidence,
            )
        verdict = (
            Verdict.PROVEN
            if record.outcome == STAGED_CANDIDATE
            else Verdict.VERIFIED
        )
        return Verification(
            verdict,
            f"{record.outcome}: a receipt exists; nothing is promoted",
            next_state=state.with_receipt(record.record_id, record.outcome),
            evidence=evidence,
        )


def candidate_from_json(payload: dict, repo_root: Path) -> WriteCandidate:
    """Build a candidate from a proposal file; seed source read from disk."""

    source_path = payload.get("seed_source_path")
    source = payload.get("seed_source", "")
    if source_path:
        # Self-review: a proposal file is untrusted input, and an uncontained
        # read here would let it pull arbitrary bytes into a staged record.
        source = _resolve_seed_target(repo_root, source_path).read_text(
            encoding="utf-8"
        )
    return WriteCandidate(
        statement_id=payload["statement_id"],
        corpus=payload["corpus"],
        seed_script=payload["seed_script"],
        seed_source=source,
        rung=payload["rung"],
        rationale=payload.get("rationale", ""),
        artifact=payload.get("artifact", ""),
        artifact_sha256=payload.get("artifact_sha256", ""),
        reference=payload.get("reference", ""),
        transition_trace=tuple(payload.get("transition_trace", ())),
        expected_matcher_delta=payload.get("expected_matcher_delta"),
        frame_local=bool(payload.get("frame_local", False)),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage a PROVEN-gated WRITE")
    parser.add_argument("proposal", type=Path, help="JSON WRITE proposal")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument(
        "--staging-dir", type=Path, default=REPO_ROOT / "staging"
    )
    args = parser.parse_args()

    payload = json.loads(args.proposal.read_text(encoding="utf-8"))
    candidate = candidate_from_json(payload, args.repo_root)
    record = stage_write(candidate, args.repo_root, args.staging_dir)
    print(record.render())
    print(f"Receipt: {args.staging_dir / (record.record_id + '.json')}")
    return 0 if record.outcome != REFUSED else 1


if __name__ == "__main__":
    raise SystemExit(main())
