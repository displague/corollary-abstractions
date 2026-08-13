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
2. the proposed seed must be one canonical envelope around literal JSON. The
   gate parses that envelope, rejects every extra statement, and trusted code
   materializes the corpus in a scratch copy OUTSIDE the repository. Candidate
   Python is never executed;
3. the WHOLE WORKING TREE is digested before and after every staging attempt --
   accepted, refused, or crashed -- and the two digests are written into the
   receipt. A refusal that changed a byte would be visible in its own receipt.
   The cover is the working tree and not `data/` alone because the seed's
   escape hatches are not corpus-shaped: a candidate that landed a file in
   `scripts/`, `prover/` or the repository root could own the next run, or
   poison the artifacts every digest pin resolves against, and a `data/`-only
   digest called such an attempt byte-identical. See `working_tree_digest`.

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

  path containment -> rung -> trusted-manifest and candidate digest pins -> theorem closes to no goals
  -> declared transition trace is really in the artifact -> theorem is unowned
  -> scratch regeneration -> regeneration is CONFINED to the declared corpus and
  adds exactly the declared statement -> semantic correspondence -> STRUCTURAL
  UNAMBIGUITY -> schema and link validation of the merged scratch graph ->
  matcher delta measured and compared against the candidate's DECLARED delta ->
  working-tree byte-identity.

**What a staged candidate is NOT evidence of.** `semantic_correspondence` passing
means the theorem's opening goal skeletonizes to a form the citing statement
DECLARES. It does not mean the statement is TRUE, and it does not mean this
statement rather than a structural twin is what the theorem proves -- which is
why the unambiguity gate exists and why nothing here accepts. Skeleton-level
correspondence is a floor above byte integrity, not semantic ownership. A
receipt is evidence that a proposal survived sixteen checks; a reviewer is what
turns that into knowledge.

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

**The executable-seed design was retracted after adversarial review.** A scratch
cwd and post-hoc digest do not sandbox Python: code can discover the repository,
damage it, and leave detection without recovery. The delivered boundary is now
declarative. The source retained in a receipt is reviewable seed text, but the
only accepted text has the exact AST of the gate's canonical literal-data
envelope. The model supplies data; trusted code performs every write.

Proof trust is independent for the same reason. A candidate-provided digest can
detect accidental drift but cannot authenticate evidence the candidate also
supplied. `prover/proof-artifact-manifest.json` is the local-files trust root;
the candidate pin, manifest pin, and one immutable artifact snapshot must all
agree before closure, trace, or correspondence is evaluated.

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
import ast
import contextlib
import ctypes
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
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
from seed_appends import (  # noqa: E402
    APPEND_KIND,
    APPENDS_DIRNAME,
    AppendError,
    append_dir,
    apply_appends,
)
from proof_artifacts import (  # noqa: E402
    REQUIRED_TRANSITION_FIELDS,
    read_regular_file_once,
    resolve_contained_artifact,
    select_closing_transitions_bytes,
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
ACCEPTED = "ACCEPTED"

PROVEN = "PROVEN"
VERIFIED = "VERIFIED"
CONJECTURED = "CONJECTURED"
RUNGS = (PROVEN, VERIFIED, CONJECTURED)

# Directories a scratch checkout needs for the full acceptance pipeline: the
# seeds and validator, the corpora they regenerate, the proof artifacts
# `verified_by` resolves against, and the schema the validator reads.
SCRATCH_TREES = ("scripts", "data", "prover", "schema")

# What the integrity digest covers, and what it deliberately does not. Argued in
# `working_tree_digest`; the trees are the scratch trees because those are
# exactly the ones a candidate seed is handed a copy of.
INTEGRITY_TREES = SCRATCH_TREES

# Build byproducts of this repository's OWN sources, excluded from the
# scratch copy and from the integrity digest alike. `.lake` is Lean's build
# directory: running `lake` once inside `prover/lean/<project>` materialises
# a ~3 GB, ~15k-file copy of the toolchain INSIDE a scratch tree, at which
# point every WRITE test copies it per test and every class-level digest
# hashes it twice (measured: 13 tests went from 26s to 1394s, and a lean run
# touching it mid-class tripped the working-tree guard). Nothing here is a
# seed target or an input to a staging decision, and the external verifier
# never reads it — it invokes the pinned toolchain's binary by path.
SCRATCH_IGNORED = ("__pycache__", ".lake")
INTEGRITY_EXCLUDED = frozenset({".git", "staging", *SCRATCH_IGNORED})
INTEGRITY_EXCLUDED_RUNTIME = (
    ".runtime",
    ".venv",
    ".worktrees",
    "experiments/data",
    "experiments/data_real",
    "experiments/data_smoke",
    "experiments/visual/out",
    # Fetched, SHA-pinned external archives (gitignored, ~1 GB once the
    # Lean corpora are present). Same lane as experiments/data: a large
    # generated/downloaded input, never a WRITE target, and already
    # authenticated where it is used -- every ingest script verifies its
    # archive against the manifest's sha256 before reading a byte, so this
    # digest re-hashing a gigabyte adds no integrity the manifest does not
    # already provide. It DOES cost minutes per call: with archives fetched,
    # the WRITE suite's per-class tree digest was hashing ~0.8 GB twice a
    # class. `data_sources/manifest.json` and the committed
    # `data_sources/derived/` extracts stay covered.
    "data_sources/archives",
)
PROOF_MANIFEST = "prover/proof-artifact-manifest.json"

_SEED_NAME = re.compile(r"^seed_[a-z0-9_]+\.py$")
_CORPUS_NAME = re.compile(r"^[a-z0-9_]+$")
# EVERY counter `_matcher_summary` emits, plus the twin-partner list. Seven of
# the nine counters were gated at first, which left `ladder_violations`,
# `parse_problems` and `slot_schema_gaps` outside the registered prediction: a
# candidate could introduce a slot-schema gap and stage without ever having
# declared it. `test_every_matcher_summary_key_is_gated` pins the two lists
# together so a future counter cannot be added to the summary and silently
# escape the prediction.
_MATCHER_DELTA_KEYS = frozenset(
    {
        "nodes_analyzed",
        "shape_groups",
        "typed_groups",
        "family_groups",
        "aliased_groups",
        "mirror_groups",
        "ladder_violations",
        "parse_problems",
        "slot_schema_gaps",
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
    seed_source_path: str = ""

    def payload(self) -> dict:
        """Canonical, order-stable view used for the record id.

        `rationale` is digested in rather than omitted: the record id names the
        receipt FILE, so two candidates it cannot tell apart overwrite each
        other. Rationale is the one field a reviewer reads and no gate checks,
        which makes "same proof, different justification" exactly the pair a
        reviewer must be able to see both of. Digested rather than inlined so
        the id stays a function of a fixed-size payload.
        """

        return {
            "statement_id": self.statement_id,
            "corpus": self.corpus,
            "seed_script": self.seed_script,
            "seed_source_sha256": hashlib.sha256(
                self.seed_source.encode("utf-8")
            ).hexdigest(),
            "rationale_sha256": hashlib.sha256(
                self.rationale.encode("utf-8")
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
            "seed_source_path": self.seed_source_path,
        }

    @property
    def record_id(self) -> str:
        canonical = json.dumps(
            self.payload(), sort_keys=True, ensure_ascii=False
        ).encode("utf-8")
        return hashlib.sha256(canonical).hexdigest()


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
    # The integrity digest covers the whole working tree, not `data/` alone --
    # the field is named for what it measures so a receipt cannot be read as a
    # narrower promise than it makes (or a wider one).
    working_tree_digest_before: str = ""
    working_tree_digest_after: str = ""
    approval_required: tuple[str, ...] = ()
    approval_granted: tuple[str, ...] = ()

    def passed(self, check: str, detail: str) -> None:
        self.checks.append({"check": check, "status": "PASS", "detail": detail})

    def refused(self, check: str, detail: str) -> None:
        self.outcome = REFUSED
        self.refusal = {"check": check, "detail": detail}
        self.checks.append(
            {"check": check, "status": "REFUSED", "detail": detail}
        )

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
            "working_tree_integrity": {
                "covers": [
                    "<repository recursively>",
                ],
                "excludes": sorted(
                    INTEGRITY_EXCLUDED
                    | set(INTEGRITY_EXCLUDED_RUNTIME)
                    | {
                        "*.session-keys.json",
                        "experiments/*.log",
                        "experiments/results/**/*.log",
                        "experiments/results/**/*.pt",
                        "experiments/results/**/*.pt.tmp",
                        "experiments/results/**/*.json.tmp",
                    }
                ),
                "digest_before": self.working_tree_digest_before,
                "digest_after": self.working_tree_digest_after,
                "byte_identical": (
                    self.working_tree_digest_before
                    == self.working_tree_digest_after
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


def _digest_tree(
    digest: "hashlib._Hash",
    root: Path,
    base: Path,
    excluded: frozenset[str] = frozenset(),
) -> None:
    """Fold every file under `root` into `digest`, keyed by path from `base`.

    `excluded` is matched against path COMPONENTS relative to `base`, and is
    passed explicitly rather than read from the module constant so that the
    narrow corpus digest cannot inherit the wide digest's exemptions: a corpus
    directory that happened to be named `staging` must still be digested.
    """

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(base)
        if any(part in excluded for part in relative.parts):
            continue
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())


def durable_digest(data_dir: Path) -> str:
    """One digest over every committed corpus file, path-sensitive.

    Kept as the narrow `data/`-only reading, because "did the DURABLE STORE
    change?" is a question a reviewer asks on its own -- and because it is the
    control that shows the wide digest earning its keep (a `scripts/` escape
    moves one and not the other). It is NOT what the gate enforces; see
    `working_tree_digest`.
    """

    digest = hashlib.sha256()
    _digest_tree(digest, data_dir, data_dir)
    return digest.hexdigest()


def working_tree_digest(repo_root: Path) -> str:
    """One digest over repository state the staging decision trusts.

    The integrity digest used to cover `data/` alone, while the scratch checkout
    copies FOUR trees (`SCRATCH_TREES`) and the seed's escape hatches are not
    corpus-shaped. A candidate that landed a file in `scripts/`, `prover/`,
    `schema/` or the repository root therefore wrote it AND collected a receipt
    reading `byte_identical: true` -- it could have overwritten this very module
    for the next run, or poisoned the `prover/` artifacts that every digest pin
    in the corpus resolves against, and the gate would have called the attempt
    clean. Found by adversarial review of this branch.

    The cover is now recursive so a new trusted directory cannot silently fall
    outside a hand-maintained list. Exclusions are explicit:

    * `.git` -- git's own bookkeeping churns for reasons that are not a
      candidate's doing;
    * `__pycache__` -- a byproduct of importing this repository's own modules
      (the scratch checkout ignores it for the same reason);
    * `.venv`, `.worktrees`, and `.runtime` -- environment, sibling-checkout,
      and private session state, not inputs to this staging decision;
    * ignored experiment inputs/outputs -- generated datasets, licensed local
      samples, checkpoints, and run logs can be large or change while a WRITE
      is checked. Committed experiment source and result JSON remain covered;
    * `staging` -- this gate's OWN output. Receipts are written here by design,
      so digesting them would make every second run of the same candidate look
      like tampering. Receipt writes are separately confined and atomic.
    """

    repo_root = repo_root.resolve()
    digest = hashlib.sha256()
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(repo_root)
        if _working_tree_path_excluded(relative):
            continue
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def working_tree_file_digests(repo_root: Path) -> dict[str, str]:
    """Per-file digest map over exactly the paths `working_tree_digest` folds.

    Same traversal and the same `_working_tree_path_excluded` exclusions, so a
    file the aggregate digest counts is a file this map counts -- but keyed by
    path, so a caller can ask WHICH files changed, not only WHETHER any did. The
    accept path uses it to assert its whole-tree delta is exactly the two files
    it declares it will write.
    """

    repo_root = repo_root.resolve()
    digests: dict[str, str] = {}
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(repo_root)
        if _working_tree_path_excluded(relative):
            continue
        digests[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def _working_tree_path_excluded(relative: Path) -> bool:
    """Mirror only the runtime-heavy `.gitignore` lanes relevant to WRITE.

    This is deliberately narrower than "all ignored files": an untracked
    proposed seed under `scripts/` is a trusted input to this run and therefore
    remains covered. The exact experiment suffixes below are generated model
    artifacts; committed source, fixtures, and result JSON are still hashed.
    """

    parts = relative.parts
    if any(part in INTEGRITY_EXCLUDED for part in parts):
        return True
    posix = relative.as_posix()
    if any(
        posix == prefix or posix.startswith(prefix + "/")
        for prefix in INTEGRITY_EXCLUDED_RUNTIME
    ):
        return True
    if relative.name.endswith(".session-keys.json"):
        return True
    if len(parts) == 2 and parts[0] == "experiments" and relative.suffix == ".log":
        return True
    if len(parts) >= 3 and parts[:2] == ("experiments", "results"):
        return (
            relative.suffix in {".pt", ".log"}
            or relative.name.endswith(".pt.tmp")
            or relative.name.endswith(".json.tmp")
        )
    return False


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


def _git_tracked(repo_root: Path, relative: str) -> bool:
    """Closed-form ownership check for a proposed source file."""
    if not (repo_root / ".git").exists():
        return False
    result = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "--error-unmatch", "--", relative],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def _canonical_seed_source(payload: dict, corpus: str) -> str:
    """The only executable-looking form accepted from an untrusted proposer.

    It is parsed as data and never executed. Requiring this exact AST keeps the
    staged seed reviewable while preventing imports, callbacks, or extra code
    from hiding beside the corpus literal.
    """
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    return (
        "import json\n"
        "from pathlib import Path\n\n"
        f"CORPUS = json.loads({rendered!r})\n\n"
        "def main() -> None:\n"
        f"    out = Path('data') / {corpus!r} / 'nodes.json'\n"
        "    out.parent.mkdir(parents=True, exist_ok=True)\n"
        "    out.write_text(\n"
        "        json.dumps(CORPUS, indent=2, ensure_ascii=False) + '\\n',\n"
        "        encoding='utf-8',\n"
        "    )\n\n"
        "main()\n"
    )


def _declarative_corpus(source: str, corpus: str) -> dict:
    """Extract a literal corpus from the canonical seed envelope, without exec."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise Refusal("declarative_seed", f"seed is not valid Python: {exc}") from None
    payload_text: str | None = None
    for statement in tree.body:
        if not isinstance(statement, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "CORPUS"
                   for target in statement.targets):
            continue
        call = statement.value
        if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id == "json" and call.func.attr == "loads"
                and len(call.args) == 1 and isinstance(call.args[0], ast.Constant)
                and isinstance(call.args[0].value, str)):
            payload_text = call.args[0].value
    if payload_text is None:
        raise Refusal("declarative_seed", "seed must declare CORPUS as json.loads(<literal>)")
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        raise Refusal("declarative_seed", f"CORPUS literal is invalid JSON: {exc}") from None
    expected_keys = {"schema", "corpus_id", "discipline", "version", "statement_nodes"}
    if not isinstance(payload, dict) or set(payload) != expected_keys:
        raise Refusal(
            "declarative_seed",
            "CORPUS envelope must contain exactly schema, corpus_id, discipline, "
            "version, and statement_nodes",
        )
    if payload["schema"] != "../../schema/equation-node.schema.json":
        raise Refusal("declarative_seed", "CORPUS schema path must target ../../schema")
    if payload["discipline"] != corpus:
        raise Refusal(
            "declarative_seed",
            f"CORPUS discipline must equal target directory {corpus!r}",
        )
    if not isinstance(payload["corpus_id"], str) or not re.fullmatch(
        r"[a-z0-9_]+(?:\.[a-z0-9_]+)+", payload["corpus_id"]
    ):
        raise Refusal("declarative_seed", "CORPUS corpus_id has invalid syntax")
    if not isinstance(payload["version"], str) or not re.fullmatch(
        r"\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?", payload["version"]
    ):
        raise Refusal("declarative_seed", "CORPUS version must be semantic-version text")
    if not isinstance(payload["statement_nodes"], list):
        raise Refusal("declarative_seed", "CORPUS statement_nodes must be a list")
    canonical = _canonical_seed_source(payload, corpus)
    if ast.dump(tree, include_attributes=False) != ast.dump(
        ast.parse(canonical), include_attributes=False
    ):
        raise Refusal(
            "declarative_seed",
            "untrusted seed source may contain only the canonical literal-data envelope",
        )
    return payload


def _parse_append_document(
    source: str, corpus: str, seed_script: str
) -> dict:
    """Parse an append_nodes document. Data only; never executed."""

    try:
        doc = json.loads(source)
    except json.JSONDecodeError as exc:
        raise Refusal(
            "declarative_seed", f"append document is not valid JSON: {exc}"
        ) from None
    if not isinstance(doc, dict):
        raise Refusal("declarative_seed", "append document must be a JSON object")
    if doc.get("kind") != APPEND_KIND:
        raise Refusal(
            "declarative_seed",
            f"append document kind must be {APPEND_KIND!r}",
        )
    if doc.get("schema_version") != 1:
        raise Refusal("declarative_seed", "append schema_version must be 1")
    extra = sorted(
        set(doc) - {"kind", "schema_version", "seed_script", "corpus",
                    "statement_nodes"}
    )
    if extra:
        raise Refusal(
            "declarative_seed",
            f"append document has unexpected keys: {', '.join(extra)}",
        )
    if doc.get("corpus") != corpus:
        raise Refusal(
            "declarative_seed",
            f"append corpus {doc.get('corpus')!r} does not match "
            f"candidate corpus {corpus!r}",
        )
    if doc.get("seed_script") != seed_script:
        raise Refusal(
            "declarative_seed",
            f"append seed_script {doc.get('seed_script')!r} does not match "
            f"candidate seed_script {seed_script!r}",
        )
    nodes = doc.get("statement_nodes")
    if not isinstance(nodes, list) or not nodes:
        raise Refusal(
            "declarative_seed",
            "append statement_nodes must be a non-empty list",
        )
    ids: list[str] = []
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(
            node.get("statement_id"), str
        ) or not node["statement_id"].strip():
            raise Refusal(
                "declarative_seed",
                "every appended node must be an object with a statement_id",
            )
        ids.append(node["statement_id"])
    if len(ids) != len(set(ids)):
        raise Refusal("declarative_seed", "append document has duplicate ids")
    return doc


def _candidate_lane(
    candidate: WriteCandidate,
) -> tuple[str, dict]:
    """Classify seed_source as new_corpus or append. Refuses anything else."""

    stripped = candidate.seed_source.lstrip()
    if stripped.startswith("{"):
        return "append", _parse_append_document(
            candidate.seed_source, candidate.corpus, candidate.seed_script
        )
    return "new_corpus", _declarative_corpus(
        candidate.seed_source, candidate.corpus
    )


def _seed_owns_corpus(seed_path: Path, corpus: str) -> bool:
    """The same ownership heuristic check_regeneration uses."""

    text = seed_path.read_text(encoding="utf-8", errors="replace")
    return (
        f'"{corpus}"' in text
        or f"'{corpus}'" in text
        or f"/{corpus}/" in text
        or f'"data/{corpus}' in text
    )


def _append_filename(statement_id: str) -> str:
    return f"{statement_id}.json"


# --------------------------------------------------------------------------
# Scratch regeneration
# --------------------------------------------------------------------------


def _subprocess_env() -> dict[str, str]:
    """Minimal environment for the trusted validator subprocess."""

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
                ignore=shutil.ignore_patterns(*SCRATCH_IGNORED),
            )


def _corpus_snapshot(data_dir: Path) -> dict[str, bytes]:
    return {
        path.relative_to(data_dir).as_posix(): path.read_bytes()
        for path in sorted(data_dir.rglob("*"))
        if path.is_file()
    }


def _atomic_write_text(path: Path, text: str) -> None:
    """Write `text` to `path` atomically, with `Path.write_text` byte semantics.

    The stream is opened in text mode with the default (`None`) newline, so a
    `\\n` is translated to `os.linesep` exactly as `Path.write_text` would --
    which is why the accepted corpus stays byte-for-byte what running the
    committed seed produces (proved by test) even though the write is now a
    temp-file/fsync/`os.replace` rather than a plain overwrite. A crash mid-write
    leaves the pre-existing bytes (or nothing) intact, never a torn file: the
    same discipline the receipt writer already uses.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", closefd=True) as stream:
            descriptor = -1
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        temporary.unlink(missing_ok=True)


def _materialize_corpus(path: Path, payload: dict) -> None:
    """The committed generator: trusted code that writes a corpus from its
    already-audited declarative payload.

    Byte-for-byte identical to the canonical seed's own `main()`
    (`out.write_text(json.dumps(CORPUS, indent=2, ensure_ascii=False) + '\\n')`),
    so running the committed seed reproduces exactly these bytes -- but this is
    trusted code parameterized by data the gate parsed, NOT the candidate seed
    being executed. Every write of `data/*/nodes.json` this module performs, in
    scratch and on the accept path alike, goes through here, and every such
    write is atomic.
    """

    _atomic_write_text(
        path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    )


def _restore_snapshot(snapshot: dict[str, bytes], data_dir: Path) -> None:
    """Write a `_corpus_snapshot` back out, e.g. to reconstruct a before-state."""

    for relative, content in snapshot.items():
        destination = data_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)


def _statement_ids(payload: bytes) -> list[str]:
    corpus = json.loads(payload.decode("utf-8"))
    return [node.get("statement_id", "") for node in corpus.get("statement_nodes", [])]


def _regenerate(
    candidate: WriteCandidate, repo_root: Path, scratch: Path
) -> tuple[dict, str]:
    """Materialize a declarative seed in scratch; return (node, detail).

    Refuses unless the regeneration is CONFINED: every corpus other than the
    candidate's is byte-identical, every existing target node and corpus field
    is unchanged, and exactly the declared statement is appended. Candidate
    Python is never executed.
    """

    if not _CORPUS_NAME.fullmatch(candidate.corpus):
        raise Refusal(
            "path_containment",
            f"corpus must be a lowercase directory identifier: {candidate.corpus!r}",
        )
    _scratch_checkout(repo_root, scratch)
    lane, parsed = _candidate_lane(candidate)
    before = _corpus_snapshot(repo_root / "data")
    target = f"{candidate.corpus}/nodes.json"
    target_path = (scratch / "data" / target).resolve()
    try:
        target_path.relative_to((scratch / "data").resolve())
    except ValueError:
        raise Refusal(
            "path_containment", f"corpus target escapes scratch data: {candidate.corpus!r}"
        ) from None

    append_rel = None
    if lane == "append":
        append_rel = (
            f"{candidate.corpus}/{APPENDS_DIRNAME}/"
            f"{_append_filename(candidate.statement_id)}"
        )
        append_path = scratch / "data" / append_rel
        append_path.parent.mkdir(parents=True, exist_ok=True)
        append_path.write_bytes(
            (json.dumps(parsed, ensure_ascii=False, indent=2) + "\n").encode(
                "utf-8"
            )
        )
        # The committed nodes.json is already seed+prior-appends
        # (check_regeneration). Merge only the NEW nodes as data; do not
        # re-exec the existing seed.
        existing = json.loads(target_path.read_text(encoding="utf-8"))
        existing_ids = {
            node.get("statement_id")
            for node in existing.get("statement_nodes", [])
        }
        for node in parsed["statement_nodes"]:
            sid = node["statement_id"]
            if sid in existing_ids:
                raise Refusal(
                    "append_collision",
                    f"{sid} is already in data/{target}",
                )
            existing["statement_nodes"].append(node)
            existing_ids.add(sid)
        new_corpus = existing
        _materialize_corpus(target_path, new_corpus)
    else:
        new_corpus = parsed
        seed_path = scratch / candidate.seed_script
        seed_path.parent.mkdir(parents=True, exist_ok=True)
        seed_path.write_text(candidate.seed_source, encoding="utf-8")
        _materialize_corpus(target_path, new_corpus)
    after = _corpus_snapshot(scratch / "data")

    allowed = {target}
    if append_rel is not None:
        allowed.add(append_rel)
    for name in sorted(set(before) | set(after)):
        if name in allowed:
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

    old_corpus: dict | None = None
    old_ids: list[str] = []
    if target in before:
        old_corpus = json.loads(before[target].decode("utf-8"))
        old_ids = _statement_ids(before[target])
    try:
        new_ids = [
            node.get("statement_id", "")
            for node in new_corpus["statement_nodes"]
        ]
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, KeyError) as exc:
        raise Refusal(
            "regeneration_confinement",
            f"candidate seed wrote a `data/{target}` that is not a corpus "
            f"document: {type(exc).__name__}: {str(exc)[:200]}",
        ) from None
    added = [sid for sid in new_ids if sid not in set(old_ids)]
    removed = [sid for sid in old_ids if sid not in set(new_ids)]
    if removed:
        raise Refusal(
            "regeneration_confinement",
            f"candidate seed removes existing statements: {', '.join(removed)}",
        )
    declared_ids = (
        [node["statement_id"] for node in parsed["statement_nodes"]]
        if lane == "append"
        else [candidate.statement_id]
    )
    if set(added) != set(declared_ids) or (
        lane != "append" and added != [candidate.statement_id]
    ):
        raise Refusal(
            "regeneration_confinement",
            f"candidate seed adds {added or 'nothing'}, but the candidate "
            f"declares {declared_ids}",
        )
    if lane == "append" and candidate.statement_id not in declared_ids:
        raise Refusal(
            "regeneration_confinement",
            "candidate.statement_id is not among the appended ids",
        )
    if len(new_ids) != len(set(new_ids)):
        raise Refusal(
            "regeneration_confinement", "candidate corpus has duplicate ids"
        )
    if old_corpus is not None:
        old_nodes = old_corpus.get("statement_nodes", [])
        new_nodes = new_corpus.get("statement_nodes", [])
        old_header = {k: v for k, v in old_corpus.items() if k != "statement_nodes"}
        new_header = {k: v for k, v in new_corpus.items() if k != "statement_nodes"}
        if old_header != new_header:
            raise Refusal(
                "regeneration_confinement",
                "candidate changes existing target-corpus metadata",
            )
        if new_nodes[:len(old_nodes)] != old_nodes:
            raise Refusal(
                "regeneration_confinement",
                "candidate changes or reorders existing target-corpus statements",
            )
        if len(new_nodes) != len(old_nodes) + len(declared_ids):
            raise Refusal(
                "regeneration_confinement",
                f"candidate must append exactly {len(declared_ids)} "
                "target-corpus statement(s)",
            )

    node = next(
        node
        for node in new_corpus["statement_nodes"]
        if node.get("statement_id") == candidate.statement_id
    )
    detail = (
        f"trusted staging code materialized declarative `data/{target}`; every "
        "other corpus and existing target node byte-equivalent; exactly one "
        "statement appended; candidate code was not executed"
    )
    return node, detail


def _scrub(text: str, *paths: Path, token: str = "<scratch>") -> str:
    """Keep receipts diffable: a temp path differs on every run.

    `token` is a parameter because the two things worth hiding are not the same
    thing: a scratch path is noise, a repository path is a location, and a
    receipt that labelled the second `<scratch>` would be wrong rather than
    merely terse.
    """

    for path in paths:
        native = str(path)
        text = text.replace(native, token).replace(
            native.replace("\\", "/"), token
        )
    return text


def _validate_data(data_dir: Path, repo_root: Path, cwd: Path, scrub: Path) -> str:
    """Validate a data tree with the validator and schema from the trusted tree.

    `data_dir` is what is checked, `repo_root` supplies the trusted validator and
    schema, `cwd` is the process working directory (so relative link targets
    resolve), and `scrub` is the path removed from the receipt so it stays
    diffable. Used for both the scratch checkout and, on the accept path, the
    real `data/` after the transition has been applied.
    """

    result = subprocess.run(
        [
            sys.executable,
            str(repo_root / "scripts" / "validate_nodes.py"),
            "--data-dir",
            str(data_dir),
            "--schema",
            str(repo_root / "schema" / "equation-node.schema.json"),
        ],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        env=_subprocess_env(),
    )
    if result.returncode != 0:
        raise Refusal(
            "schema_and_link_validation",
            _scrub((result.stdout + result.stderr).strip()[-800:], scrub),
        )
    return _scrub(result.stdout.strip().splitlines()[-1], scrub)


def _validate(scratch: Path, repo_root: Path) -> str:
    """Validate scratch data with validator and schema from the trusted tree."""
    return _validate_data(scratch / "data", repo_root, scratch, scratch)


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
    # A list, not "a list or a tuple": a declaration arrives as JSON, where a
    # tuple cannot occur, so accepting one only widened what an in-process
    # caller could pass without widening what a proposal file could say.
    partners = declared["new_typed_twin_partners"]
    if not isinstance(partners, list) or not all(
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


def _trusted_proof_digest(repo_root: Path, artifact: str) -> str:
    """Return the independently committed digest for one proof artifact."""
    manifest_path = repo_root / PROOF_MANIFEST
    try:
        manifest = json.loads(read_regular_file_once(manifest_path).decode("utf-8"))
        entry = manifest["artifacts"][artifact]
        digest = entry["sha256"]
    except (KeyError, TypeError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise Refusal(
            "proof_trust_manifest",
            f"artifact {artifact!r} is absent from a valid trusted manifest: {exc}",
        ) from None
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise Refusal(
            "proof_trust_manifest", f"manifest digest for {artifact!r} is malformed"
        )
    return digest


def _check_proof(
    candidate: WriteCandidate, repo_root: Path
) -> tuple[list[tuple[str, str]], bytes]:
    """Authenticate one immutable snapshot, then check closure and trace."""

    if not candidate.artifact or not candidate.reference:
        raise Refusal(
            "proof_artifact",
            "a PROVEN candidate must name both an artifact and a theorem",
        )
    try:
        artifact_path = resolve_contained_artifact(repo_root, candidate.artifact)
    except ValueError as exc:
        raise Refusal("proof_artifact", str(exc)) from None
    try:
        artifact_bytes = read_regular_file_once(artifact_path)
    except ValueError as exc:
        raise Refusal("proof_artifact", str(exc)) from None
    digest = hashlib.sha256(artifact_bytes).hexdigest()
    trusted_digest = _trusted_proof_digest(repo_root, candidate.artifact)
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
    if Path(candidate.artifact).suffix.casefold() != ".json":
        raise Refusal(
            "proof_artifact",
            f"cannot authenticate non-JSON proof artifact: {candidate.artifact}",
        )
    if digest != trusted_digest:
        raise Refusal(
            "proof_trust_manifest",
            f"artifact digest is {digest}, trusted manifest pins {trusted_digest}",
        )
    try:
        transitions, resolved = select_closing_transitions_bytes(
            artifact_bytes, candidate.reference, candidate.artifact
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
        (
            "proof_trust_manifest",
            f"trusted manifest independently pins {candidate.artifact} to {digest}",
        ),
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
    ], artifact_bytes


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
    artifact_bytes: bytes,
) -> dict:
    links = [
        link for link in node.get("verified_by", []) or [] if isinstance(link, dict)
    ]
    # These two refusals are about the SHAPE of the regenerated node's citation,
    # not about what a theorem proves: no correspondence has been computed yet,
    # so calling them `semantic_correspondence` put a check name in the receipt
    # beside a null `correspondence` field and invited the reader to think a
    # comparison had been made and failed. They get their own name.
    if len(links) != 1:
        raise Refusal(
            "candidate_link_shape",
            f"a staged candidate must carry exactly one verified_by link, "
            f"found {len(links)}",
        )
    link = links[0]
    if link.get("artifact") != candidate.artifact or link.get(
        "reference"
    ) != candidate.reference:
        raise Refusal(
            "candidate_link_shape",
            "the regenerated node cites a different theorem than the candidate "
            f"declares: {link.get('artifact')}:{link.get('reference')}",
        )
    corpus_forms = {
        other["statement_id"]: declared_forms(other)
        for other in load_corpus_nodes(repo_root / "data")
        if other.get("statement_id")
    }
    result = check_link(
        node, link, repo_root, corpus_forms, artifact_bytes=artifact_bytes
    )
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


def _linklike(path: Path) -> bool:
    return path.is_symlink() or (
        hasattr(path, "is_junction") and path.is_junction()
    )


def _write_all(descriptor: int, payload: bytes) -> None:
    """Write a complete buffer even when the OS reports partial progress."""
    view = memoryview(payload)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise OSError("receipt write made no progress")
        view = view[written:]


@contextlib.contextmanager
def _held_staging_directory(staging_dir: Path, expected: Path):
    """Hold the validated directory against replacement for the whole write.

    POSIX callers receive a directory fd and use only dir-relative operations.
    Windows lacks Python dir_fd support, so the committed `.gitignore` marker is
    opened without FILE_SHARE_DELETE; its resolved target is checked and the
    open child prevents the directory from being swapped during the write.
    """
    if _linklike(staging_dir) or staging_dir.resolve() != expected.resolve():
        raise ValueError("staging directory must be the repository's non-link `staging/`")
    if os.name != "nt":
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(staging_dir, flags)
        try:
            yield descriptor
        finally:
            os.close(descriptor)
        return

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
    ]
    create_file.restype = ctypes.c_void_p
    marker = staging_dir / ".gitignore"
    if _linklike(marker) or not marker.is_file():
        raise ValueError("staging directory lacks its trusted `.gitignore` marker")
    handle = create_file(
        str(marker), 0x80000000, 0x1 | 0x2, None, 3, 0x00200000, None
    )
    invalid = ctypes.c_void_p(-1).value
    if handle == invalid:
        raise OSError(ctypes.get_last_error(), "cannot hold staging directory")
    try:
        get_name = kernel32.GetFinalPathNameByHandleW
        get_name.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32]
        get_name.restype = ctypes.c_uint32
        buffer = ctypes.create_unicode_buffer(32768)
        length = get_name(handle, buffer, len(buffer), 0)
        if not length or length >= len(buffer):
            raise OSError(ctypes.get_last_error(), "cannot resolve held staging directory")
        held = buffer.value.removeprefix("\\\\?\\")
        lexical = str((expected / ".gitignore").absolute())
        if os.path.normcase(held) != os.path.normcase(lexical):
            raise ValueError("held staging directory resolves outside repository")
        yield None
    finally:
        kernel32.CloseHandle(ctypes.c_void_p(handle))


def _write_receipt_atomic(staging_dir: Path, expected: Path, name: str, payload: bytes) -> None:
    """Create and replace a receipt relative to one held directory identity."""
    with _held_staging_directory(staging_dir, expected) as directory_fd:
        temporary_name = f".{name}.{secrets.token_hex(12)}.tmp"
        if directory_fd is not None:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(temporary_name, flags, 0o600, dir_fd=directory_fd)
            try:
                _write_all(descriptor, payload)
                os.fsync(descriptor)
                info = os.fstat(descriptor)
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise RuntimeError("receipt temporary is not a private regular file")
            finally:
                os.close(descriptor)
            try:
                os.replace(
                    temporary_name, name,
                    src_dir_fd=directory_fd, dst_dir_fd=directory_fd,
                )
            finally:
                try:
                    os.unlink(temporary_name, dir_fd=directory_fd)
                except FileNotFoundError:
                    pass
            return

        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{name}.", suffix=".tmp", dir=staging_dir
        )
        temporary = Path(temporary_name)
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise RuntimeError("receipt temporary is not a private regular file")
            with os.fdopen(descriptor, "wb", closefd=True) as stream:
                descriptor = -1
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            info = temporary.stat(follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise RuntimeError("receipt temporary changed identity")
            os.replace(temporary, staging_dir / name)
        finally:
            if descriptor >= 0:
                os.close(descriptor)
            temporary.unlink(missing_ok=True)


def stage_write(
    candidate: WriteCandidate,
    repo_root: Path = REPO_ROOT,
    staging_dir: Path | None = None,
) -> StagingRecord:
    """Judge one WRITE candidate and write its receipt. Never accepts."""

    repo_root = repo_root.resolve()
    expected_staging = repo_root / "staging"
    if staging_dir is not None:
        if _linklike(staging_dir) or staging_dir.resolve() != expected_staging.resolve():
            raise ValueError(
                "staging directory must be the repository's non-symlink "
                f"`staging/`: {staging_dir}"
            )
    record = StagingRecord(
        record_id=candidate.record_id,
        statement_id=candidate.statement_id,
        outcome=REFUSED,
        rung=candidate.rung,
        working_tree_digest_before=working_tree_digest(repo_root),
    )
    try:
        _gate(candidate, repo_root, record)
    except Refusal as refusal:
        record.refused(refusal.check, refusal.detail)
    except Exception as exc:  # noqa: BLE001 - see below
        # A gate that only catches its OWN refusal is a gate that stops being a
        # gate the moment a candidate finds an unforeseen crash: `stage_write`
        # would raise, no after-digest would be taken, no receipt would be
        # written, and (through the controller adapter) the exception would
        # escape `Controller().run` entirely. A candidate seed emitting
        # malformed JSON did exactly that. Every unexpected failure is therefore
        # a REFUSAL WITH A RECEIPT: the attempt is judged rather than lost, and
        # the digest below still runs.
        record.refused(
            "staging_crashed",
            _scrub(
                _scrub(
                    f"{type(exc).__name__}: {str(exc).strip()[:400]}",
                    Path(tempfile.gettempdir()),
                ),
                repo_root,
                token="<repo>",
            ),
        )
    record.working_tree_digest_after = working_tree_digest(repo_root)
    if record.working_tree_digest_after != record.working_tree_digest_before:
        # Belt and braces: nothing above writes into the repository, so this can
        # only fire if trusted state changed concurrently or staging code has a
        # defect. Candidate code is never executed.
        record.staged = None
        record.refused(
            "working_tree_byte_identity",
            "trusted repository state changed during staging",
        )
    else:
        record.passed(
            "working_tree_byte_identity",
            "the trusted repository tree is byte-identical before and after "
            "this attempt",
        )
    if staging_dir is not None:
        staging_dir.mkdir(parents=False, exist_ok=True)
        receipt = staging_dir / f"{record.record_id}.json"
        _write_receipt_atomic(
            staging_dir,
            expected_staging,
            receipt.name,
            record.render().encode("utf-8"),
        )
        # `staging/` is intentionally excluded, so this catches mutation of
        # every trusted path during the atomic receipt write without flagging
        # the receipt itself.
        if working_tree_digest(repo_root) != record.working_tree_digest_after:
            receipt.unlink(missing_ok=True)
            raise RuntimeError("repository changed during atomic receipt write")
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

    seed_target = _resolve_seed_target(repo_root, candidate.seed_script)
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
    lane, parsed = _candidate_lane(candidate)
    corpus_target = repo_root / "data" / candidate.corpus / "nodes.json"
    proposed_untracked_seed = (
        seed_target.exists()
        and candidate.seed_source_path == candidate.seed_script
        and not _git_tracked(repo_root, candidate.seed_script)
    )
    if lane == "append":
        if not seed_target.is_file():
            raise Refusal(
                "seed_ownership",
                "an append names a committed seed that already owns the "
                "corpus; that seed is missing",
            )
        if (repo_root / ".git").exists() and not _git_tracked(
            repo_root, candidate.seed_script
        ):
            raise Refusal(
                "seed_ownership",
                "an append names a committed seed that already owns the "
                "corpus; that seed is untracked",
            )
        if not corpus_target.is_file():
            raise Refusal(
                "seed_ownership",
                "an append requires an existing corpus; a new corpus uses "
                "the literal-envelope lane",
            )
        if not _seed_owns_corpus(seed_target, candidate.corpus):
            raise Refusal(
                "seed_ownership",
                f"`{candidate.seed_script}` does not own corpus "
                f"`{candidate.corpus}`",
            )
        existing_ids = {
            node.get("statement_id")
            for node in json.loads(
                corpus_target.read_text(encoding="utf-8")
            ).get("statement_nodes", [])
        }
        incoming = [
            node["statement_id"] for node in parsed["statement_nodes"]
        ]
        collision = [sid for sid in incoming if sid in existing_ids]
        if collision:
            raise Refusal(
                "append_collision",
                "an append that would replace an existing node is a "
                "different operation: " + ", ".join(collision),
            )
        if candidate.statement_id not in incoming:
            raise Refusal(
                "declarative_seed",
                "candidate.statement_id must be one of the appended ids",
            )
        record.passed(
            "seed_ownership",
            "append to a corpus this committed seed already owns; the seed "
            "file is not rewritten",
        )
        record.passed(
            "append_collision",
            "no appended id is already in the corpus",
        )
    else:
        if (seed_target.exists() and not proposed_untracked_seed) or corpus_target.exists():
            raise Refusal(
                "seed_ownership",
                "the declarative WRITE lane stages new seed/new corpus pairs only; "
                "replacing an existing seed could orphan another corpus it owns, "
                "and appending to an existing corpus needs a trusted patch format",
            )
        record.passed(
            "seed_ownership",
            "both the proposed seed and corpus are new; no existing seed outputs "
            "can be orphaned",
        )
    proof_checks, artifact_bytes = _check_proof(candidate, repo_root)
    for check, detail in proof_checks:
        record.passed(check, detail)
    record.passed(
        "exclusive_theorem_ownership", _check_unowned(candidate, repo_root)
    )
    with tempfile.TemporaryDirectory(prefix="write-stage-") as temporary:
        scratch = Path(temporary) / "scratch"
        node, detail = _regenerate(candidate, repo_root, scratch)
        record.passed(
            "declarative_seed",
            "candidate is the canonical literal-data envelope; no candidate "
            "Python was executed",
        )
        record.passed("scratch_regeneration", detail)
        record.passed("regeneration_confinement", detail)
        _check_correspondence(
            node, candidate, repo_root, record, artifact_bytes
        )
        record.passed(
            "semantic_correspondence",
            f"CORRESPONDS via the candidate's "
            f"{record.correspondence['matched_route']} form",
        )
        record.passed(
            "structural_unambiguity",
            "no committed statement declares the theorem's skeleton",
        )
        record.passed(
            "schema_and_link_validation", _validate(scratch, repo_root)
        )
        measured = _measure_matcher_delta(
            repo_root / "data", scratch / "data", candidate.statement_id
        )
        # The candidate's PREDICTION belongs beside the measurement. It survived
        # only as free text in the pass detail, so a receipt could not be
        # audited for predicted-versus-measured without re-reading the proposal
        # file -- and staging/README.md already claimed this field carried it.
        measured["declared"] = candidate.expected_matcher_delta
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
# The acceptance path
#
# Staging never accepts, and it must not: a machine may not put its own proposal
# in the corpus, and `stage_write` above ends with `approval_granted: []` on
# purpose. `accept_write` is the SEPARATE, explicit act that applies a candidate
# that already cleared every gate. It is not reachable from the controller loop
# (that would let the machine promote itself); it is invoked deliberately, the
# same shape as a human running the ordinary seed loop, and it carries the same
# honesty boundary the receipt does: acceptance means "the audited seed was
# written and its corpus regenerated by trusted code so the declared delta was
# applied", NOT "the statement is true".
#
# The safety argument is by construction, and every clause is load-bearing:
#
#   * it runs the FULL `stage_write` audit first and applies NOTHING unless the
#     outcome is `STAGED_CANDIDATE`. A refused candidate is returned with its
#     diffable receipt and the working tree is byte-identical -- the accept path
#     cannot apply anything the gate would refuse, including a seed that would
#     orphan a co-owned corpus (refused at `seed_ownership`);
#   * it re-derives the corpus from the SAME `candidate.seed_source` the gate
#     audited, parsed as data by `_declarative_corpus` -- candidate Python is
#     never executed, here or anywhere;
#   * every byte of `data/*/nodes.json` it writes goes through
#     `_materialize_corpus`, the one trusted generator, byte-identical to what
#     running the committed seed would produce. The candidate never hands over
#     corpus bytes;
#   * after applying, it re-verifies IN THE REAL TREE: exactly the declared node
#     is present and nothing else, every OTHER corpus is byte-identical, schema
#     and links validate, and the declared matcher delta matches the one now
#     measured against the applied data. Any failure rolls the tree back to
#     byte-identical and refuses -- an application that cannot be verified is not
#     an application.
# --------------------------------------------------------------------------


@dataclass
class AcceptanceRecord:
    """The diffable receipt for an APPLIED write. Records the exact transition.

    Unlike a staging receipt, the working tree is NOT byte-identical across an
    acceptance -- applying the seed and regenerating the corpus is the whole
    point. The receipt therefore records the before/after digests so the applied
    transition is visible and reproducible: the same seed source, materialized
    by the same generator, yields the recorded after-digest.
    """

    record_id: str
    statement_id: str
    corpus: str
    seed_script: str
    outcome: str = ACCEPTED
    staging_record_id: str = ""
    seed_source_sha256: str = ""
    node_id: str = ""
    verifications: list[dict] = field(default_factory=list)
    matcher_delta: dict | None = None
    corpus_digest_before: str = ""
    corpus_digest_after: str = ""
    working_tree_digest_before: str = ""
    working_tree_digest_after: str = ""
    # Acceptance grants exactly one thing: the seed was written and the corpus
    # regenerated by trusted code. It never grants that the statement is true.
    applied: tuple[str, ...] = ()

    def verified(self, check: str, detail: str) -> None:
        self.verifications.append(
            {"check": check, "status": "PASS", "detail": detail}
        )

    def as_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "outcome": self.outcome,
            "staging_record_id": self.staging_record_id,
            "statement_id": self.statement_id,
            "corpus": self.corpus,
            "seed_script": self.seed_script,
            "seed_source_sha256": self.seed_source_sha256,
            "node_id": self.node_id,
            "verifications": self.verifications,
            "matcher_delta": self.matcher_delta,
            "transition": {
                "corpus_digest_before": self.corpus_digest_before,
                "corpus_digest_after": self.corpus_digest_after,
                "working_tree_digest_before": self.working_tree_digest_before,
                "working_tree_digest_after": self.working_tree_digest_after,
            },
            "applied": list(self.applied),
            "means": (
                "a receipt exists AND the audited seed was written and its "
                "corpus regenerated by trusted code so the declared delta was "
                "applied; this does NOT certify the statement is true, and "
                "correspondence certifies STRUCTURE only"
            ),
        }

    def render(self) -> str:
        return json.dumps(
            self.as_dict(), indent=2, sort_keys=True, ensure_ascii=False
        ) + "\n"


class AcceptanceError(Exception):
    """A post-application verification failed. Carries the reason; the tree is
    rolled back to byte-identical before this is raised."""


def accept_write(
    candidate: WriteCandidate,
    repo_root: Path = REPO_ROOT,
    staging_dir: Path | None = None,
) -> tuple[StagingRecord, AcceptanceRecord | None]:
    """Audit a candidate and, only if it stages, APPLY it. Never applies a
    candidate the gate would refuse.

    Returns `(staging_record, acceptance_record)`. On refusal (or a VERIFIED
    review request) the acceptance record is `None` and the working tree is
    byte-identical, exactly as for `stage_write`. On acceptance the seed is
    written, the corpus is regenerated by trusted code, and the acceptance
    receipt is written beside the staging receipt in `staging/`.
    """

    repo_root = repo_root.resolve()

    # 1. Full audit first. Applies nothing that the gate would not stage; a
    #    refused candidate leaves the tree byte-identical and returns here.
    staging_record = stage_write(candidate, repo_root, staging_dir)
    if staging_record.outcome != STAGED_CANDIDATE:
        return staging_record, None

    working_before = staging_record.working_tree_digest_after
    before_snapshot = _corpus_snapshot(repo_root / "data")
    corpus_before = durable_digest(repo_root / "data")

    # 2. Re-derive the corpus from the audited source. Trusted parse; the
    #    candidate is never executed.
    lane, parsed = _candidate_lane(candidate)

    seed_path = _resolve_seed_target(repo_root, candidate.seed_script)
    # Re-derive the corpus target under the same containment discipline the
    # scratch regeneration uses, rather than trust `candidate.corpus` across a
    # function boundary: the gate's `_CORPUS_NAME` check already ran, but this
    # is where bytes land in the REAL tree, so a traversal must be impossible
    # here on its own terms, not by inheritance.
    if not _CORPUS_NAME.fullmatch(candidate.corpus):
        raise AcceptanceError(
            f"corpus must be a lowercase directory identifier: {candidate.corpus!r}"
        )
    data_dir = (repo_root / "data").resolve()
    corpus_path = (data_dir / candidate.corpus / "nodes.json").resolve()
    try:
        corpus_path.relative_to(data_dir)
    except ValueError:
        raise AcceptanceError(
            f"corpus target escapes data/: {candidate.corpus!r}"
        ) from None
    target_rel = f"{candidate.corpus}/nodes.json"

    # 3. Belt-and-braces. new_corpus never overwrites an existing corpus.
    #    append never overwrites an existing seed; it may rewrite the
    #    corpus file it is extending, via the trusted merger.
    if lane != "append" and corpus_path.exists():
        raise AcceptanceError(
            f"data/{target_rel} already exists; acceptance never overwrites a "
            "corpus"
        )
    # Everything the accept path is about to touch, RECORDED BEFORE it is
    # touched, so rollback cleans up regardless of how far a write got:
    #   * an untracked proposed seed may pre-exist (the gate allows it) -- keep
    #     its bytes so rollback restores them exactly rather than leaving our
    #     overwrite; if it did not exist, rollback removes what we created;
    #   * the corpus directory is new for a new corpus, so rollback must remove
    #     it even if the (atomic) corpus write never completed and left an empty
    #     dir behind -- which the file-only `working_tree_digest` would miss.
    seed_before = seed_path.read_bytes() if seed_path.is_file() else None
    corpus_dir = corpus_path.parent
    corpus_dir_existed = corpus_dir.exists()
    # The strong guarantee, established by construction at the point bytes land:
    # a per-file map of the whole tree BEFORE, so AFTER we can assert the only
    # paths whose bytes changed are exactly the seed and the target corpus.
    files_before = working_tree_file_digests(repo_root)
    if lane == "append":
        append_path = (
            append_dir(corpus_dir) / _append_filename(candidate.statement_id)
        )
        expected_changes = {
            append_path.resolve().relative_to(repo_root).as_posix(),
            corpus_path.relative_to(repo_root).as_posix(),
        }
    else:
        append_path = None
        expected_changes = {
            seed_path.resolve().relative_to(repo_root).as_posix(),
            corpus_path.relative_to(repo_root).as_posix(),
        }

    def _rollback() -> None:
        # Idempotent, intention-based: does not depend on how far the try got.
        if lane == "append":
            if append_path is not None:
                append_path.unlink(missing_ok=True)
            _restore_snapshot(before_snapshot, repo_root / "data")
            return
        corpus_path.unlink(missing_ok=True)
        if not corpus_dir_existed:
            with contextlib.suppress(OSError):
                corpus_dir.rmdir()
        if seed_before is not None:
            seed_path.write_bytes(seed_before)
        else:
            seed_path.unlink(missing_ok=True)
        _restore_snapshot(before_snapshot, repo_root / "data")

    try:
        # 4. Apply through trusted code only. Candidate Python is never
        #    executed. new_corpus writes a seed + materializes the envelope;
        #    append writes the JSON patch and merges it onto the existing
        #    corpus.
        if lane == "append":
            append_path.parent.mkdir(parents=True, exist_ok=True)
            _atomic_write_text(
                append_path,
                json.dumps(parsed, ensure_ascii=False, indent=2) + "\n",
            )
            composed = json.loads(corpus_path.read_text(encoding="utf-8"))
            for node in parsed["statement_nodes"]:
                composed["statement_nodes"].append(node)
            _materialize_corpus(corpus_path, composed)
            verify_payload = composed
        else:
            _atomic_write_text(seed_path, candidate.seed_source)
            _materialize_corpus(corpus_path, parsed)
            verify_payload = parsed

        acceptance = _verify_application(
            candidate,
            repo_root,
            verify_payload,
            before_snapshot,
            target_rel,
            staging_record,
            lane=lane,
            append_rel=(
                f"{candidate.corpus}/{APPENDS_DIRNAME}/"
                f"{_append_filename(candidate.statement_id)}"
                if lane == "append"
                else None
            ),
            declared_ids=(
                [n["statement_id"] for n in parsed["statement_nodes"]]
                if lane == "append"
                else [candidate.statement_id]
            ),
        )

        # F4: the whole-tree delta must be EXACTLY the two declared files. If a
        # validator, matcher, or anything else touched `scripts/`, `prover/`,
        # `schema/`, another corpus, or the root, this catches it and the tree
        # is rolled back. `staging/` is excluded from the map by construction.
        files_after = working_tree_file_digests(repo_root)
        changed = {
            name
            for name in set(files_before) | set(files_after)
            if files_before.get(name) != files_after.get(name)
        }
        stray = sorted(changed - expected_changes)
        if stray:
            raise AcceptanceError(
                "acceptance changed files it did not declare: "
                + ", ".join(stray)
            )

        acceptance.corpus_digest_before = corpus_before
        acceptance.corpus_digest_after = durable_digest(repo_root / "data")
        acceptance.working_tree_digest_before = working_before
        acceptance.working_tree_digest_after = working_tree_digest(repo_root)

        # F3: receipt-or-nothing. The receipt is written INSIDE the guarded
        # region, so a receipt failure rolls the application back rather than
        # leaving a durable change with no diffable receipt. `staging/` is
        # excluded from the delta above, so writing it does not disturb F4.
        if staging_dir is not None:
            expected_staging = repo_root / "staging"
            receipt = staging_dir / f"{acceptance.record_id}.accepted.json"
            _write_receipt_atomic(
                staging_dir,
                expected_staging,
                receipt.name,
                acceptance.render().encode("utf-8"),
            )
    except Exception as exc:  # noqa: BLE001 - roll back, then re-raise
        # An application that cannot be verified -- or cannot be receipted -- is
        # not an application. Restore byte-identity before surfacing the failure.
        _rollback()
        if working_tree_digest(repo_root) != working_before:
            raise AcceptanceError(
                "acceptance failed AND rollback could not restore byte-identity; "
                f"manual review required: {type(exc).__name__}: {exc}"
            ) from exc
        raise

    return staging_record, acceptance


def _verify_application(
    candidate: WriteCandidate,
    repo_root: Path,
    payload: dict,
    before_snapshot: dict[str, bytes],
    target_rel: str,
    staging_record: StagingRecord,
    lane: str = "new_corpus",
    append_rel: str | None = None,
    declared_ids: list[str] | None = None,
) -> AcceptanceRecord:
    """Re-check the applied tree. Raises `AcceptanceError` on any discrepancy."""

    declared_ids = declared_ids or [candidate.statement_id]
    if lane == "append":
        applied = (
            f"wrote data/{append_rel}",
            f"merged append into data/{target_rel} via the trusted merger",
        )
    else:
        applied = (
            f"wrote {candidate.seed_script}",
            f"regenerated data/{target_rel} via the committed generator",
        )
    acceptance = AcceptanceRecord(
        record_id=candidate.record_id,
        statement_id=candidate.statement_id,
        corpus=candidate.corpus,
        seed_script=candidate.seed_script,
        staging_record_id=staging_record.record_id,
        seed_source_sha256=candidate.payload()["seed_source_sha256"],
        node_id=candidate.statement_id,
        applied=applied,
    )

    after_snapshot = _corpus_snapshot(repo_root / "data")

    # Every OTHER corpus byte-identical: acceptance extends its own corpus only.
    allowed = {target_rel}
    if append_rel:
        allowed.add(append_rel)
    for name in sorted(set(before_snapshot) | set(after_snapshot)):
        if name in allowed:
            continue
        if before_snapshot.get(name) != after_snapshot.get(name):
            raise AcceptanceError(
                f"applying the candidate changed data/{name}, which it does not "
                "declare"
            )
    acceptance.verified(
        "other_corpora_byte_identical",
        "every corpus other than the target is byte-identical to before the "
        "transition",
    )

    if target_rel not in after_snapshot:
        raise AcceptanceError(f"data/{target_rel} was not written")
    applied_corpus = json.loads(after_snapshot[target_rel].decode("utf-8"))
    if applied_corpus != payload:
        raise AcceptanceError(
            f"data/{target_rel} does not equal the audited declarative payload"
        )
    ids = [
        node.get("statement_id", "")
        for node in applied_corpus.get("statement_nodes", [])
    ]
    if lane == "append":
        before_ids = _statement_ids(before_snapshot[target_rel])
        added = [sid for sid in ids if sid not in set(before_ids)]
        if set(added) != set(declared_ids):
            raise AcceptanceError(
                f"the applied corpus added {added or 'nothing'}, but the "
                f"candidate declares {declared_ids}"
            )
        if ids[:len(before_ids)] != before_ids:
            raise AcceptanceError(
                "append changed or reordered existing target-corpus statements"
            )
        acceptance.verified(
            "declared_node_present_and_only_it",
            f"the regenerated corpus appended exactly {declared_ids}",
        )
    else:
        if ids != [candidate.statement_id]:
            raise AcceptanceError(
                f"the applied corpus contains {ids or 'nothing'}, but the "
                f"candidate declares exactly {candidate.statement_id}"
            )
        acceptance.verified(
            "declared_node_present_and_only_it",
            f"the regenerated corpus contains exactly {candidate.statement_id}",
        )

    detail = _validate_data(
        repo_root / "data", repo_root, repo_root, repo_root
    )
    acceptance.verified("schema_and_link_validation", detail)

    with tempfile.TemporaryDirectory(prefix="write-accept-") as temporary:
        before_data = Path(temporary) / "data"
        _restore_snapshot(before_snapshot, before_data)
        measured = _measure_matcher_delta(
            before_data, repo_root / "data", candidate.statement_id
        )
    measured["declared"] = candidate.expected_matcher_delta
    acceptance.matcher_delta = measured
    acceptance.verified(
        "matcher_delta_applied", _compare_declared_delta(candidate, measured)
    )
    return acceptance


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
        # `stage_write` is INSIDE the try. It was outside, so any exception it
        # raised propagated out of `Controller().run` and took the whole loop
        # with it -- a WRITE that crashed was not a refused step, it was an
        # aborted run. `stage_write` now refuses-with-a-receipt instead of
        # raising, and this is the second line of that defence.
        try:
            path = _resolve_contained_input(self.repo_root, proposal)
            payload = json.loads(read_regular_file_once(path).decode("utf-8"))
            candidate = candidate_from_json(payload, self.repo_root)
            record = stage_write(candidate, self.repo_root, self.staging_dir)
        except Refusal as refusal:
            return Verification(Verdict.REFUSED, str(refusal))
        except (
            OSError,
            UnicodeError,
            json.JSONDecodeError,
            KeyError,
            TypeError,
            ValueError,
        ) as exc:
            return Verification(
                Verdict.REFUSED, f"proposal is unreadable: {exc}"
            )

        evidence = (
            f"record_id={record.record_id}",
            f"outcome={record.outcome}",
            f"working_tree_byte_identical="
            f"{record.working_tree_digest_before == record.working_tree_digest_after}",
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

    if not isinstance(payload, dict):
        # A proposal file is untrusted bytes: valid JSON is not a proposal.
        # Without this an array-shaped file raised AttributeError straight out
        # of the adapter, which is the shape of bug this whole round fixed.
        raise Refusal(
            "proposal_shape",
            f"a WRITE proposal must be a JSON object, got {type(payload).__name__}",
        )

    source_path = payload.get("seed_source_path")
    source = payload.get("seed_source", "")
    if source_path:
        # Self-review: a proposal file is untrusted input, and an uncontained
        # read here would let it pull arbitrary bytes into a staged record.
        resolved = _resolve_seed_target(repo_root, source_path)
        if not resolved.is_file():
            # Refusal, not FileNotFoundError: every other bad path in a
            # proposal is a judged refusal with a receipt, and a typo should
            # not be the one that raises out of the CLI.
            raise Refusal(
                "path_containment",
                f"proposal seed source does not exist: {source_path!r}",
            )
        try:
            source = read_regular_file_once(resolved).decode("utf-8")
            source = source.replace("\r\n", "\n")
            if "\r" in source:
                raise UnicodeError("seed source contains a lone carriage return")
        except (ValueError, UnicodeError) as exc:
            raise Refusal("path_containment", str(exc)) from None
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
        seed_source_path=source_path or "",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage a PROVEN-gated WRITE")
    parser.add_argument("proposal", type=Path, help="JSON WRITE proposal")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--staging-dir", type=Path)
    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "APPLY a candidate that clears every gate: write its seed and "
            "regenerate its corpus. Refusal stays byte-identical. Deliberate "
            "and separate from staging; never reachable from the controller."
        ),
    )
    args = parser.parse_args()
    staging_dir = args.staging_dir or args.repo_root / "staging"

    payload = json.loads(read_regular_file_once(args.proposal).decode("utf-8"))
    candidate = candidate_from_json(payload, args.repo_root)
    if args.apply:
        record, acceptance = accept_write(candidate, args.repo_root, staging_dir)
        if acceptance is None:
            print(record.render())
            print(f"Refused; nothing applied. Receipt: "
                  f"{staging_dir / (record.record_id + '.json')}")
            return 1
        print(acceptance.render())
        print(f"Applied. Seed: {args.repo_root / candidate.seed_script}")
        print(f"Corpus: {args.repo_root / 'data' / candidate.corpus / 'nodes.json'}")
        print(f"Receipt: {staging_dir / (acceptance.record_id + '.accepted.json')}")
        return 0
    record = stage_write(candidate, args.repo_root, staging_dir)
    print(record.render())
    print(f"Receipt: {staging_dir / (record.record_id + '.json')}")
    return 0 if record.outcome != REFUSED else 1


if __name__ == "__main__":
    raise SystemExit(main())
