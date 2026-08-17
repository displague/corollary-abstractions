#!/usr/bin/env python3
"""Validate Mathematical Statement Node corpora."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from proof_artifacts import (
    resolve_contained_artifact,
    select_closing_transitions,
)


# Mirrors $defs.frameScope in schema/equation-node.schema.json. The syntax is
# retained for compatibility; scope_errors additionally requires the value to
# resolve to the declaration node that owns the frame.
FRAME_ID_RE = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)+\Z")
FRAME_ROLES = {"declaration", "assertion"}
# Frame-level properties every member of a frame must agree on: they describe
# the FRAME, not the member node, so disagreement means two nodes are talking
# about different frames under one identifier.
FRAME_AGREEMENT_PROPS = (
    "frame_title",
    "owner",
    "suspends",
    "governed_by",
    "retrieval",
    "on_exit",
)
REPO_ROOT = Path(__file__).resolve().parents[1]


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
    checks jsonschema cannot express: suspends/governed_by must resolve
    against the merged graph, the frame id must identify its declaration
    node, and nodes sharing a frame must agree on frame properties.
    """
    errors: list[str] = []
    node_by_id = {
        n.get("statement_id"): n for n in nodes if n.get("statement_id")
    }
    resolvable = set(node_by_id) | (known_ids or set())
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
        owner = scope.get("owner")
        if "owner" in scope and (
            not isinstance(owner, str) or not owner.strip()
        ):
            errors.append(f"{node_id}: scope.owner must be a non-empty string")
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
        declaration = node_by_id.get(frame)
        declaration_scope = (
            declaration.get("scope") if isinstance(declaration, dict) else None
        )
        if declaration is None:
            errors.append(
                f"frame `{frame}` must resolve to its declaration node"
            )
        elif not (
            isinstance(declaration_scope, dict)
            and declaration_scope.get("frame") == frame
            and declaration_scope.get("role") == "declaration"
        ):
            errors.append(
                f"frame `{frame}` must identify a scoped declaration node"
            )
        else:
            declaration_owner = declaration_scope.get("owner")
            for member_id, member_scope in members:
                if member_id == frame or "owner" not in member_scope:
                    continue
                if declaration_owner is None:
                    errors.append(
                        f"{member_id}: scope.owner must originate on frame "
                        f"declaration `{frame}`"
                    )
                elif member_scope["owner"] != declaration_owner:
                    errors.append(
                        f"{member_id}: scope.owner disagrees with frame "
                        f"declaration `{frame}`"
                    )
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


def ingested_verdict_rule_errors(
    nodes: list[dict], corpus_of: dict[str, str], repo_root: Path
) -> list[str]:
    """Verdict-backed ingestion as a RULE (v0.12 item 4).

    v0.11 made this real for programming nodes only: a `python-tests`
    citation must name a digest-pinned artifact carrying a PASS. That left
    the Lean half open, and v0.12 authored the corpus that makes the hole
    concrete — Goedel-Pset, whose proofs are all `sorry`. A Goedel-Pset node
    that cited `verified_by` would be claiming a machine-checked bridge that
    provably does not exist upstream. That is the case this rule refuses.

    The rule, stated once: **an ingested node may cite `verified_by` only
    when the cited artifact is pinned in the proof manifest AND carries a
    PASS verdict claiming that node.** Any system, not just `python-tests`.

    Why ingested corpora specifically. A curated node is written by hand and
    reviewed; its citation is a claim a person made and can be asked about.
    An ingested node is authored mechanically in bulk from an external
    extract, so a citation on one is a claim nobody inspected. Bulk
    authorship is exactly the regime where an unbacked link would enter
    unnoticed, which is why the rule binds there first and hardest.

    Keyed on **corpus identity**, not on statement-id shape, so a corpus
    cannot dodge it by renaming its nodes. `decompose` owns the registry of
    which corpora are ingested; importing it here keeps one list rather than
    a second that can drift.

    This is preventive: at the time it was written **no ingested node cited
    `verified_by` at all**, so it refuses a case that does not yet exist.
    That is the point — the rule has to be in place before the first
    Goedel-Pset node tries it, not after. `tests/test_verdict_rule.py`
    proves it fires, using a synthetic node, because there is no violator in
    the corpus to point at.
    """

    try:
        from decompose import INGESTED_CORPUS_PREFIXES
    except ImportError:  # pragma: no cover - CLI import shim
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from decompose import INGESTED_CORPUS_PREFIXES

    manifest_path = repo_root / "prover" / "proof-artifact-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = manifest.get("artifacts") or {}
    except (OSError, ValueError):
        entries = {}

    errors: list[str] = []
    for index, node in enumerate(nodes):
        node_id = node.get("statement_id", f"<node-{index}>")
        links = node.get("verified_by") or []
        if not links or not isinstance(links, list):
            continue
        corpus = corpus_of.get(node_id, "")
        if not corpus.startswith(tuple(INGESTED_CORPUS_PREFIXES)):
            continue
        for link_index, link in enumerate(links):
            if not isinstance(link, dict):
                continue
            artifact = link.get("artifact")
            where = f"{node_id}: verified_by[{link_index}]"
            if not isinstance(artifact, str) or not artifact:
                errors.append(
                    f"{where} on ingested corpus {corpus!r} names no artifact; "
                    "an ingested citation requires a digest-pinned artifact "
                    "with a PASS verdict"
                )
                continue
            entry = entries.get(artifact)
            if not isinstance(entry, dict):
                errors.append(
                    f"{where} on ingested corpus {corpus!r} cites {artifact!r}, "
                    "which is not pinned in prover/proof-artifact-manifest.json; "
                    "an ingested corpus may not mint a verified_by link from an "
                    "unpinned artifact"
                )
                continue
            claimed = entry.get("verdicts") or []
            if not claimed:
                errors.append(
                    f"{where} on ingested corpus {corpus!r} cites {artifact!r}, "
                    "which carries no verdict; an ingested citation requires a "
                    "PASS verdict claiming this statement (Goedel-Pset proofs "
                    "are `sorry` — there is no proof to bridge to)"
                )
    return errors


def verified_by_errors(nodes: list[dict], repo_root: Path) -> list[str]:
    """Check that proof links name real, exclusively-owned artifact theorems.

    This is intentionally the cheap provenance-integrity rung, not a proof of
    semantic correspondence.  A valid theorem cited by the wrong statement is
    structurally indistinguishable here; prover phase 2 must compare their
    regenerated formal skeletons.
    """
    errors: list[str] = []
    # Cache holds (resolved_reference, error_message): failures are cached
    # WITH their message so every citing node gets its own attributed error
    # instead of the first citer absorbing them all.
    artifact_cache: dict[
        tuple[Path, str | None], tuple[str | None, str | None]
    ] = {}
    owners: dict[tuple[str, str], set[str]] = {}

    def resolve_reference(
        artifact: str, reference: str | None, node_id: str
    ) -> str | None:
        try:
            resolved = resolve_contained_artifact(repo_root, artifact)
        except ValueError as exc:
            errors.append(f"{node_id}: {exc}")
            return None
        key = (resolved, reference)
        if key in artifact_cache:
            cached_reference, cached_error = artifact_cache[key]
            if cached_error is not None:
                errors.append(f"{node_id}: {cached_error}")
            return cached_reference
        try:
            _, resolved_reference = select_closing_transitions(resolved, reference)
        except ValueError as exc:
            errors.append(f"{node_id}: {exc}")
            artifact_cache[key] = (None, str(exc))
            return None
        artifact_cache[key] = (resolved_reference, None)
        return resolved_reference

    for i, node in enumerate(nodes):
        node_id = node.get("statement_id", f"<node-{i}>")
        if "verified_by" not in node:
            continue
        links = node["verified_by"]
        if not isinstance(links, list):
            errors.append(f"{node_id}: `verified_by` must be a list")
            continue
        for link_index, link in enumerate(links):
            if not isinstance(link, dict):
                errors.append(
                    f"{node_id}: verified_by[{link_index}] must be an object"
                )
                continue
            extras = sorted(set(link) - {"system", "artifact", "reference"})
            if extras:
                errors.append(
                    f"{node_id}: verified_by[{link_index}] has unexpected "
                    f"fields: {', '.join(extras)}"
                )
            artifact = link.get("artifact")
            system = link.get("system")
            if not isinstance(system, str) or not system.strip():
                errors.append(
                    f"{node_id}: verified_by[{link_index}].system must be a "
                    "non-empty string"
                )
                continue
            if system not in {"lean4", "python-tests"}:
                errors.append(
                    f"{node_id}: verified_by[{link_index}].system `{system}` "
                    "is unsupported; supported systems are `lean4` and "
                    "`python-tests`"
                )
                continue
            if not isinstance(artifact, str) or not artifact.strip():
                errors.append(
                    f"{node_id}: verified_by[{link_index}].artifact must be a "
                    "non-empty string"
                )
                continue
            reference = link.get("reference")
            if reference is not None and (
                not isinstance(reference, str) or not reference.strip()
            ):
                errors.append(
                    f"{node_id}: verified_by reference must be a non-empty "
                    "theorem identity"
                )
                continue
            if system == "python-tests":
                # A python-tests citation is a digest-pinned candidate, not
                # a Lean transition-row artifact. Cross-system attach is
                # refused: a .json triples file is lean4's shape.
                if Path(artifact).suffix.casefold() == ".json":
                    errors.append(
                        f"{node_id}: verified_by[{link_index}] is "
                        "`python-tests` but cites a JSON artifact "
                        f"`{artifact}`; python-tests citations name the "
                        "pinned candidate module, not a Lean triples file"
                    )
                    continue
                try:
                    resolve_contained_artifact(repo_root, artifact)
                except ValueError as exc:
                    errors.append(f"{node_id}: {exc}")
                    continue
                if not isinstance(reference, str) or not reference.strip():
                    errors.append(
                        f"{node_id}: verified_by[{link_index}].reference "
                        "must name the checked function"
                    )
                    continue
                # Review finding: existence of a .py file is not a verdict.
                # A python-tests link must name a manifest-keyed artifact so
                # verdict_ledger_errors can require a PASS claiming this
                # statement. An unmanifested candidate would otherwise
                # launder an unchecked file into verified_by.
                manifest_path = repo_root / "prover" / "proof-artifact-manifest.json"
                try:
                    manifest = json.loads(
                        manifest_path.read_text(encoding="utf-8")
                    )
                    entries = manifest.get("artifacts") or {}
                except (OSError, ValueError):
                    entries = {}
                if artifact not in entries:
                    errors.append(
                        f"{node_id}: verified_by[{link_index}] is "
                        "`python-tests` but `{artifact}` is not a key in "
                        "prover/proof-artifact-manifest.json; a test-backed "
                        "citation requires a digest-pinned artifact with a "
                        "PASS verdict"
                    )
                    continue
                owners.setdefault((system, reference), set()).add(node_id)
                continue
            reference = resolve_reference(artifact, reference, node_id)
            if reference is None:
                continue
            owners.setdefault((system, reference), set()).add(node_id)

    for (system, reference), node_ids in sorted(owners.items()):
        if len(node_ids) > 1:
            errors.append(
                f"verified_by theorem `{system}:{reference}` is claimed by "
                f"multiple statements: {', '.join(sorted(node_ids))}"
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
        default=str(REPO_ROOT / "schema" / "equation-node.schema.json"),
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
        default=str(REPO_ROOT / "data"),
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
    corpus_of: dict[str, str] = {}
    errors: list[str] = []
    for path in corpus_paths:
        data = load_json(path)
        nodes = data.get("statement_nodes")
        if not isinstance(nodes, list):
            errors.append(f"{path}: corpus must contain `statement_nodes` as a list.")
            continue
        errors.extend(minimal_schema_errors(schema, nodes))
        errors.extend(jsonschema_errors(schema, nodes))
        corpus_id = data.get("corpus_id", path.parent.name)
        for node in nodes:
            sid = node.get("statement_id")
            if isinstance(sid, str):
                corpus_of[sid] = corpus_id
        all_nodes.extend(nodes)

    # v0.12 item 4: verdict-backed ingestion as a RULE, widened past
    # `python-tests` to every ingested corpus.
    errors.extend(ingested_verdict_rule_errors(all_nodes, corpus_of, REPO_ROOT))

    # Link integrity and reciprocity over the merged cross-discipline graph.
    errors.extend(inferential_link_errors(schema, all_nodes))
    # Scope integrity: frame ids, frame agreement, suspends/governed_by
    # resolution -- also over the merged graph, since a frame may suspend
    # or be governed by nodes in another corpus.
    errors.extend(scope_errors(all_nodes))
    # Proof-link integrity over the merged graph. This checks artifact and
    # theorem identity plus exclusive statement ownership, but deliberately
    # does not claim the theorem semantically corresponds to the statement.
    errors.extend(
        verified_by_errors(all_nodes, REPO_ROOT)
    )
    # External-verifier ledger integrity (v0.10 item 2): every committed
    # verdict re-hashes its pinned inputs, every manifest pin matches its
    # committed bytes, and a PASS verdict attaches only to the statement it
    # names. Fail closed; certifies ledger integrity, not correctness.
    try:
        from external_verifier import verdict_ledger_errors
    except ImportError:  # pragma: no cover - CLI import shim
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from external_verifier import verdict_ledger_errors
    errors.extend(verdict_ledger_errors(REPO_ROOT, all_nodes))

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
