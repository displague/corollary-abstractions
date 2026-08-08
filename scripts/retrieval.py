#!/usr/bin/env python3
"""UNKNOWN-triggered retrieval over the project's extrinsic knowledge stores.

The store is deliberately read-only and symbolic. It unifies five committed
sources into one query surface: corpus statements, their lexica, structural
twin/mirror groups, decomposition entries, and machine-proof links. Retrieval
does not answer a slot by itself; it appends stable, indexed material to the
session context, and a later POINT action binds one item to the pending slot.

Exact lookup is attempted first. A miss falls back to deterministic token
neighborhood search. A durable miss remains UNKNOWN and records ABSTAIN rather
than inventing material. Frames declaring ``retrieval: frame_local`` refuse
before touching the store and expose ``ASK(slot)`` as the permitted escalation.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import re
import secrets
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Protocol

from controller import (
    Action,
    ActionKind,
    Controller,
    SequencePolicy,
    Verification,
    Verdict,
)
from frames import (
    FrameAssertionVerifier,
    FrameExecutor,
    FrameSpec,
    FrameState,
    Literal,
)
from oracle_controller_demo import TRUSTED_TRIPLES_SHA256


SOURCE_ORDER = {
    "corpus": 0,
    "lexicon": 1,
    "twin_ledger": 2,
    "decomposition": 3,
    "proof": 4,
}
_TOKEN = re.compile(r"[a-z0-9]+")
_WHITESPACE = re.compile(r"\s+")


def exact_key(value: str) -> str:
    """Canonical equality key that preserves closed-form operators."""

    return _WHITESPACE.sub(" ", value.strip().casefold())


def query_tokens(value: str) -> tuple[str, ...]:
    """Canonical closed-form query tokens."""

    return tuple(_TOKEN.findall(value.casefold()))


def item_match_mode(item: "RetrievalItem", key: str) -> str | None:
    """Return the exact closed-form relation between a key and one item."""

    if any(exact_key(key) == exact_key(alias) for alias in item.aliases):
        return "exact"
    tokens = query_tokens(key)
    if not tokens:
        return None
    aliases = tuple(query_tokens(alias) for alias in item.aliases)

    def covers(alias: tuple[str, ...]) -> bool:
        return all(
            any(
                query_token == candidate
                or (
                    len(query_token) >= 3
                    and candidate.startswith(query_token)
                )
                or (
                    len(candidate) >= 3
                    and query_token.startswith(candidate)
                )
                for candidate in alias
            )
            for query_token in tokens
        )

    if any(covers(alias) for alias in aliases):
        return "neighborhood"
    return None


@dataclass(frozen=True)
class RetrievalItem:
    """One attributable piece of material from one extrinsic source."""

    item_id: str
    source: str
    title: str
    text: str
    epistemic_status: str
    source_ids: tuple[str, ...]
    aliases: tuple[str, ...]


@dataclass(frozen=True)
class QueryResult:
    mode: str
    query: str
    items: tuple[RetrievalItem, ...] = ()


class UnifiedKnowledgeStore:
    """Read committed corpus/report artifacts through one exact interface."""

    def __init__(self, items: tuple[RetrievalItem, ...] = ()):
        ids = [item.item_id for item in items]
        if len(ids) != len(set(ids)):
            raise ValueError("retrieval item ids must be unique")
        self.items = tuple(
            sorted(items, key=lambda item: (SOURCE_ORDER[item.source], item.item_id))
        )

    @classmethod
    def load(cls, data_dir: Path, reports_dir: Path) -> "UnifiedKnowledgeStore":
        repo_root = data_dir.parent
        nodes: dict[str, dict] = {}
        for path in sorted(data_dir.glob("*/nodes.json")):
            corpus = json.loads(path.read_text(encoding="utf-8"))
            for node in corpus.get("statement_nodes", []):
                nodes[node["statement_id"]] = node

        items: list[RetrievalItem] = []
        for statement_id, node in sorted(nodes.items()):
            title = node["title"]
            meaning = node["semantic_interpretation"]["statement_meaning"]
            template = node["structural_signature"]["anonymized_template"]
            common_aliases = (
                statement_id,
                title,
                *node.get("keywords", []),
                node["structural_signature"]["archetype_id"],
            )
            items.append(
                RetrievalItem(
                    item_id=f"corpus:{statement_id}",
                    source="corpus",
                    title=title,
                    text=f"{meaning} Template: {template}",
                    epistemic_status=node["epistemic_status"],
                    source_ids=(statement_id,),
                    aliases=common_aliases,
                )
            )

            lexicon = node["symbol_lexicon"]
            symbol_names = [entry["symbol"] for entry in lexicon["symbols"]]
            operator_names = [entry["name"] for entry in lexicon["operators"]]
            functional_names = [
                entry["name"] for entry in lexicon.get("functionals", [])
            ]
            lexicon_terms = tuple(symbol_names + operator_names + functional_names)
            items.append(
                RetrievalItem(
                    item_id=f"lexicon:{statement_id}",
                    source="lexicon",
                    title=f"{title} lexicon",
                    text="; ".join(lexicon_terms),
                    epistemic_status=node["epistemic_status"],
                    source_ids=(statement_id,),
                    aliases=(statement_id, title, *lexicon_terms),
                )
            )

            verified_by = node.get("verified_by", [])
            if verified_by:
                references = tuple(
                    entry["reference"]
                    for entry in verified_by
                    if entry.get("reference")
                )
                artifacts = tuple(entry["artifact"] for entry in verified_by)
                proof_details: list[str] = []
                proof_artifacts_trusted: list[bool] = []
                for entry in verified_by:
                    if entry["system"] != "lean4":
                        raise ValueError(
                            "retrieval can authenticate only verified_by system "
                            f"'lean4', got {entry['system']!r}"
                        )
                    reference = entry.get("reference")
                    artifact_path = repo_root / entry["artifact"]
                    if not artifact_path.is_file():
                        raise FileNotFoundError(
                            f"verified_by artifact does not exist: {artifact_path}"
                        )
                    artifact_digest = hashlib.sha256(
                        artifact_path.read_bytes()
                    ).hexdigest()
                    trusted_artifact = artifact_digest == TRUSTED_TRIPLES_SHA256
                    proof_artifacts_trusted.append(trusted_artifact)
                    detail = entry["system"]
                    if reference:
                        detail += f":{reference}"
                    detail += f" ({entry['artifact']})"
                    if artifact_path.suffix != ".json":
                        raise ValueError(
                            "retrieval cannot authenticate non-JSON proof "
                            f"artifact: {artifact_path}"
                        )
                    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
                    required_transition_fields = (
                        "theorem",
                        "tactic",
                        "stateBefore",
                        "stateAfter",
                    )
                    theorem_rows = (
                        [
                            row
                            for row in payload
                            if isinstance(row, dict)
                            and all(
                                isinstance(row.get(field), str)
                                for field in required_transition_fields
                            )
                            and bool(row["theorem"])
                            and bool(row["tactic"])
                        ]
                        if isinstance(payload, list)
                        else []
                    )
                    if not theorem_rows:
                        raise ValueError(
                            "verified_by JSON artifact has no complete theorem "
                            f"transitions: {artifact_path}"
                        )
                    theorem_names = {row["theorem"] for row in theorem_rows}
                    if reference is None and len(theorem_names) != 1:
                        raise ValueError(
                            "artifact-only verified_by link is ambiguous across "
                            f"theorems {sorted(theorem_names)!r}: {artifact_path}"
                        )
                    transitions = theorem_rows
                    if reference:
                        transitions = [
                            row
                            for row in theorem_rows
                            if row.get("theorem") == reference
                        ]
                    if reference and not transitions:
                        raise ValueError(
                            f"verified_by reference {reference!r} "
                            f"is absent from {artifact_path}"
                        )
                    if not any(
                        row["stateAfter"].strip().casefold() == "no goals"
                        for row in transitions
                    ):
                        label = reference or "artifact"
                        raise ValueError(
                            f"verified_by {label!r} does not close to no goals "
                            f"in {artifact_path}"
                        )
                    detail += f" — {len(transitions)} extracted transitions"
                    detail += (
                        " — trusted extraction"
                        if trusted_artifact
                        else " — untrusted extraction"
                    )
                    proof_details.append(detail)
                items.append(
                    RetrievalItem(
                        item_id=f"proof:{statement_id}",
                        source="proof",
                        title=f"{title} proof artifacts",
                        text="; ".join(proof_details),
                        epistemic_status=(
                            "proven"
                            if all(proof_artifacts_trusted)
                            else "verified"
                        ),
                        source_ids=(statement_id, *artifacts),
                        aliases=(statement_id, title, *references, *artifacts),
                    )
                )

        signature_report = json.loads(
            (reports_dir / "signature_matches.json").read_text(encoding="utf-8")
        )
        group_fields = (
            ("typed", "typed_twin_groups"),
            ("family", "family_twin_groups_beyond_typed"),
            ("aliased", "aliased_twin_groups_beyond_typed"),
            ("mirror", "mirror_twin_groups"),
            ("shape", "shape_twin_groups"),
        )
        for level, field in group_fields:
            for index, group in enumerate(signature_report[field]):
                member_ids = tuple(
                    member["statement_id"] for member in group["members"]
                )
                member_titles = tuple(
                    nodes[statement_id]["title"] for statement_id in member_ids
                )
                items.append(
                    RetrievalItem(
                        item_id=f"twin_ledger:{level}:{index}",
                        source="twin_ledger",
                        title=f"{level} structural group",
                        text=(
                            f"{group['skeleton']} :: " + " | ".join(member_titles)
                        ),
                        epistemic_status="verified",
                        source_ids=member_ids,
                        aliases=(*member_ids, *member_titles, group["skeleton"]),
                    )
                )

        decomposition_report = json.loads(
            (reports_dir / "decompositions.json").read_text(encoding="utf-8")
        )
        for entry in decomposition_report["decompositions"]:
            statement_id = entry["statement_id"]
            constituents = tuple(
                constituent["skeleton"] for constituent in entry["constituents"]
            )
            items.append(
                RetrievalItem(
                    item_id=f"decomposition:{statement_id}",
                    source="decomposition",
                    title=f"{nodes[statement_id]['title']} decomposition",
                    text=(
                        f"groundedness={entry['groundedness']:.3f}; "
                        + "; ".join(constituents)
                    ),
                    epistemic_status="verified",
                    source_ids=(statement_id,),
                    aliases=(statement_id, nodes[statement_id]["title"], *constituents),
                )
            )
        return cls(tuple(items))

    def query(self, key: str, limit: int = 24) -> QueryResult:
        exact = tuple(
            item
            for item in self.items
            if item_match_mode(item, key) == "exact"
        )
        if exact:
            return QueryResult("exact", key, exact[:limit])

        if not query_tokens(key):
            return QueryResult("miss", key)

        neighborhood = tuple(
            item
            for item in self.items
            if item_match_mode(item, key) == "neighborhood"
        )
        if neighborhood:
            return QueryResult("neighborhood", key, neighborhood[:limit])
        return QueryResult("miss", key)

    def contains_item(self, item: RetrievalItem) -> bool:
        """Authenticate a pointable record against the committed snapshot."""

        return item in self.items

    def binding_match_mode(self, item: RetrievalItem, key: str) -> str | None:
        """Return a match only when the key resolves to one corpus owner.

        A lexicon symbol such as ``a`` may be an exact alias of dozens of
        unrelated statements. Retrieval may expose that neighborhood, but it
        is not an answer certificate: POINT can bind only when the corpus,
        lexicon, and proof views that match the key identify one statement.
        """

        mode = item_match_mode(item, key)
        if mode is None:
            return None
        exact_owners = {
            candidate.source_ids[0]
            for candidate in self.items
            if candidate.source in {"corpus", "lexicon", "proof"}
            and item_match_mode(candidate, key) == "exact"
        }
        if mode == "neighborhood" and exact_owners:
            return None
        canonical_matches = tuple(
            candidate
            for candidate in self.items
            if candidate.source in {"corpus", "lexicon", "proof"}
            and item_match_mode(candidate, key) == mode
        )
        if canonical_matches:
            owners = {candidate.source_ids[0] for candidate in canonical_matches}
            if len(owners) != 1 or next(iter(owners)) not in item.source_ids:
                return None
            return mode

        decomposition_matches = tuple(
            candidate
            for candidate in self.items
            if candidate.source == "decomposition"
            and item_match_mode(candidate, key) == mode
        )
        if decomposition_matches:
            owners = {
                candidate.source_ids[0] for candidate in decomposition_matches
            }
            if len(owners) != 1 or next(iter(owners)) not in item.source_ids:
                return None
            return mode

        group_matches = tuple(
            candidate
            for candidate in self.items
            if candidate.source == "twin_ledger"
            and item_match_mode(candidate, key) == mode
        )
        if len(group_matches) == 1 and item.item_id == group_matches[0].item_id:
            return mode
        return None


@dataclass(frozen=True)
class RetrievalNeed:
    slot: str
    suggested_key: str
    unresolved_literal: Literal
    unknown_evidence: tuple[str, ...]


@dataclass(frozen=True)
class PointableMaterial:
    position: int
    item: RetrievalItem


@dataclass(frozen=True)
class RetrievalResolution:
    """A pending UNKNOWN resolved by a non-retrieval frame transition."""

    slot: str
    verdict: Verdict
    reason: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class RetrievalReceipt:
    """Verifier-minted evidence that RETRIEVE admitted these item ids."""

    session_id: str
    frame_scope: str
    key: str
    mode: str
    item_ids: tuple[str, ...]
    signature: str


@dataclass(frozen=True)
class RetrievalState:
    """Frame state plus one unresolved slot and its retrieved context."""

    frame: FrameState
    session_id: str = field(default_factory=lambda: secrets.token_hex(16))
    pending: RetrievalNeed | None = None
    context: tuple[PointableMaterial, ...] = ()
    bindings: tuple[tuple[str, str], ...] = ()
    resolutions: tuple[RetrievalResolution, ...] = ()
    retrieval_receipts: tuple[RetrievalReceipt, ...] = ()

    @classmethod
    def from_unknown(
        cls,
        executor: FrameExecutor,
        frame: FrameState,
        slot: str,
        suggested_key: str,
        unresolved_literal: Literal,
    ) -> "RetrievalState":
        finding = executor.check(frame, unresolved_literal)
        if finding.verdict is not Verdict.UNKNOWN:
            raise ValueError(
                "retrieval may be initiated only from an UNKNOWN adjudication"
            )
        if not slot or not suggested_key:
            raise ValueError("retrieval slot and suggested key must be non-empty")
        if exact_key(suggested_key) != exact_key(unresolved_literal.value):
            raise ValueError(
                "retrieval key must be the unresolved literal's value; request "
                "parsing owns that key constraint"
            )
        return cls(
            frame=frame,
            pending=RetrievalNeed(
                slot, suggested_key, unresolved_literal, tuple(finding.evidence)
            ),
        )


class QueryStore(Protocol):
    def query(self, key: str, limit: int = 24) -> QueryResult: ...

    def binding_match_mode(self, item: RetrievalItem, key: str) -> str | None: ...

    def contains_item(self, item: RetrievalItem) -> bool: ...


class RetrievalVerifier:
    """Layer RETRIEVE/POINT over the existing frame verifier adapter."""

    name = "retrieval-harness"

    def __init__(self, store: QueryStore, frame_executor: FrameExecutor):
        self.store = store
        self.frame_executor = frame_executor
        self.frame_verifier = FrameAssertionVerifier(frame_executor)
        self._receipt_secret = secrets.token_bytes(32)

    def _receipt_signature(
        self,
        session_id: str,
        frame_scope: str,
        key: str,
        mode: str,
        item_ids: tuple[str, ...],
    ) -> str:
        payload = repr(
            (session_id, frame_scope, exact_key(key), mode, item_ids)
        ).encode("utf-8")
        return hmac.new(self._receipt_secret, payload, hashlib.sha256).hexdigest()

    def _valid_receipt(
        self, receipt: RetrievalReceipt, session_id: str, frame_scope: str
    ) -> bool:
        if (
            receipt.session_id != session_id
            or receipt.frame_scope != frame_scope
        ):
            return False
        expected = self._receipt_signature(
            receipt.session_id,
            receipt.frame_scope,
            receipt.key,
            receipt.mode,
            receipt.item_ids,
        )
        return hmac.compare_digest(receipt.signature, expected)

    def state_key(self, state: RetrievalState) -> str:
        pending = None if state.pending is None else (
            state.pending.slot,
            state.pending.suggested_key,
            state.pending.unresolved_literal,
        )
        return repr(
            (
                self.frame_verifier.state_key(state.frame),
                state.session_id,
                pending,
                tuple(material.item.item_id for material in state.context),
                state.bindings,
                state.resolutions,
                state.retrieval_receipts,
            )
        )

    def evaluate(
        self, state: RetrievalState, action: Action
    ) -> Verification[RetrievalState]:
        if action.kind is ActionKind.RETRIEVE:
            if action.name != "lookup":
                return Verification(
                    Verdict.REFUSED,
                    f"unknown retrieval transition {action.name!r}",
                    evidence=(self.name,),
                )
            return self._retrieve(state, action)
        if action.kind is ActionKind.POINT:
            if action.name != "bind":
                return Verification(
                    Verdict.REFUSED,
                    f"unknown point transition {action.name!r}",
                    evidence=(self.name,),
                )
            return self._point(state, action)

        delegated = self.frame_verifier.evaluate(state.frame, action)
        if not delegated.verdict.accepts:
            return Verification(
                delegated.verdict, delegated.reason, evidence=delegated.evidence
            )
        assert delegated.next_state is not None
        pending = state.pending
        if pending is not None:
            current = self.frame_executor.check(
                delegated.next_state, pending.unresolved_literal
            )
            if current.verdict is Verdict.UNKNOWN:
                pending = replace(
                    pending, unknown_evidence=tuple(current.evidence)
                )
            else:
                resolution = RetrievalResolution(
                    pending.slot,
                    current.verdict,
                    current.reason,
                    tuple(current.evidence),
                )
                return Verification(
                    delegated.verdict,
                    delegated.reason,
                    replace(
                        state,
                        frame=delegated.next_state,
                        pending=None,
                        resolutions=state.resolutions + (resolution,),
                    ),
                    delegated.evidence,
                )
        return Verification(
            delegated.verdict,
            delegated.reason,
            replace(state, frame=delegated.next_state, pending=pending),
            delegated.evidence,
        )

    def _pending_is_current_unknown(
        self, state: RetrievalState
    ) -> Verification[RetrievalState] | None:
        assert state.pending is not None
        if exact_key(state.pending.suggested_key) != exact_key(
            state.pending.unresolved_literal.value
        ):
            return Verification(
                Verdict.REFUSED,
                "pending retrieval need is malformed: its key differs from "
                "the unresolved literal's value",
                evidence=(state.pending.slot,),
            )
        finding = self.frame_executor.check(
            state.frame, state.pending.unresolved_literal
        )
        if finding.verdict is Verdict.UNKNOWN:
            return None
        return Verification(
            Verdict.REFUSED,
            "pending retrieval need is stale because its literal is no longer "
            f"UNKNOWN ({finding.verdict.value})",
            evidence=(state.pending.slot, *finding.evidence),
        )

    def _retrieve(
        self, state: RetrievalState, action: Action
    ) -> Verification[RetrievalState]:
        if state.frame.closed:
            return Verification(
                Verdict.REFUSED,
                "frame is closed; retrieval cannot extend its context",
                evidence=(state.frame.spec.frame,),
            )
        if state.pending is None:
            return Verification(
                Verdict.REFUSED,
                "RETRIEVE requires an unresolved UNKNOWN slot",
                evidence=(self.name,),
            )
        stale = self._pending_is_current_unknown(state)
        if stale is not None:
            return stale
        if state.frame.spec.retrieval == "frame_local":
            return Verification(
                Verdict.REFUSED,
                "frame declares this UNKNOWN unresolvable-by-retrieval; "
                f"escalate as ASK({state.pending.slot})",
                evidence=(state.frame.spec.frame, f"ASK({state.pending.slot})"),
            )
        key = action.argument("key")
        if not key:
            return Verification(
                Verdict.REFUSED,
                "RETRIEVE requires a non-empty key",
                evidence=(self.name,),
            )
        if exact_key(key) != exact_key(state.pending.suggested_key):
            return Verification(
                Verdict.REFUSED,
                "RETRIEVE key must equal the pending UNKNOWN literal's "
                "canonical key",
                evidence=(state.pending.suggested_key, key),
            )

        result = self.store.query(key)
        if not result.items:
            return Verification(
                Verdict.UNKNOWN,
                "exact and neighborhood retrieval both missed; UNKNOWN stays "
                "open and the controller must abstain rather than confabulate",
                evidence=(key, "ABSTAIN"),
            )

        existing = {material.item.item_id for material in state.context}
        new_items = tuple(item for item in result.items if item.item_id not in existing)
        if not new_items:
            return Verification(
                Verdict.REFUSED,
                "retrieval returned only material already present in context",
                evidence=(key, result.mode),
            )
        start = len(state.context)
        added = tuple(
            PointableMaterial(start + offset, item)
            for offset, item in enumerate(new_items)
        )
        sources = tuple(sorted({item.source for item in new_items}))
        item_ids = tuple(item.item_id for item in new_items)
        receipt = RetrievalReceipt(
            state.session_id,
            repr(state.frame.spec),
            key,
            result.mode,
            item_ids,
            self._receipt_signature(
                state.session_id,
                repr(state.frame.spec),
                key,
                result.mode,
                item_ids,
            ),
        )
        return Verification(
            Verdict.VERIFIED,
            f"{result.mode} retrieval transaction added {len(added)} pointable "
            "items without changing their own epistemic statuses",
            replace(
                state,
                context=state.context + added,
                retrieval_receipts=state.retrieval_receipts + (receipt,),
            ),
            (key, result.mode, *sources),
        )

    def _point(
        self, state: RetrievalState, action: Action
    ) -> Verification[RetrievalState]:
        if state.pending is None:
            return Verification(
                Verdict.REFUSED,
                "POINT requires an unresolved slot",
                evidence=(self.name,),
            )
        stale = self._pending_is_current_unknown(state)
        if stale is not None:
            return stale
        raw_position = action.argument("position")
        try:
            position = int(raw_position) if raw_position is not None else -1
        except ValueError:
            position = -1
        by_position = {material.position: material for material in state.context}
        if position not in by_position:
            return Verification(
                Verdict.REFUSED,
                f"POINT position {raw_position!r} is absent from retrieved context",
                evidence=(state.pending.slot,),
            )
        material = by_position[position]
        if not self.store.contains_item(material.item):
            return Verification(
                Verdict.REFUSED,
                "pointed material is absent from the authoritative retrieval "
                "store",
                evidence=(state.pending.slot, material.item.item_id),
            )
        authorized = any(
            self._valid_receipt(
                receipt, state.session_id, repr(state.frame.spec)
            )
            and exact_key(receipt.key) == exact_key(state.pending.suggested_key)
            and material.item.item_id in receipt.item_ids
            for receipt in state.retrieval_receipts
        )
        if not authorized:
            return Verification(
                Verdict.REFUSED,
                "pointed material has no valid RETRIEVE receipt for this "
                "pending key",
                evidence=(state.pending.slot, material.item.item_id),
            )
        match_mode = self.store.binding_match_mode(
            material.item, state.pending.suggested_key
        )
        if match_mode is None:
            return Verification(
                Verdict.REFUSED,
                "pointed material does not satisfy the pending slot's "
                "closed-form key constraint",
                evidence=(
                    state.pending.slot,
                    state.pending.suggested_key,
                    material.item.item_id,
                ),
            )
        return Verification(
            Verdict.VERIFIED,
            f"{match_mode}-matched material binds UNKNOWN slot "
            f"{state.pending.slot!r}",
            replace(
                state,
                pending=None,
                bindings=state.bindings
                + ((state.pending.slot, material.item.item_id),),
            ),
            (material.item.item_id, *material.item.source_ids),
        )


def retrieval_action(key: str) -> Action:
    return Action.build(ActionKind.RETRIEVE, "lookup", {"key": key})


def point_action(position: int) -> Action:
    return Action.build(ActionKind.POINT, "bind", {"position": str(position)})


def demo(repo_root: Path, key: str) -> int:
    executor = FrameExecutor()
    frame = executor.open_frame(
        # Retrieval is open here; story-local frames keep their existing guard.
        FrameSpec(frame="retrieval.demo", retrieval="open")
    )
    state = RetrievalState.from_unknown(
        executor,
        frame,
        "answer",
        key,
        Literal("request", "needs", key),
    )
    store = UnifiedKnowledgeStore.load(repo_root / "data", repo_root / "reports")
    verifier = RetrievalVerifier(store, executor)
    run = Controller[RetrievalState](max_steps=2).run(
        state,
        SequencePolicy((retrieval_action(key), point_action(0))),
        verifier,
        lambda current: current.pending is None,
    )
    for entry in run.trace:
        print(
            f"{entry.action.kind.value}: {entry.verification.verdict.value} — "
            f"{entry.verification.reason}"
        )
    for material in run.final_state.context:
        print(
            f"[{material.position}] {material.item.source}: "
            f"{material.item.title} ({material.item.epistemic_status})"
        )
    print(f"bindings: {run.final_state.bindings}")
    return 0 if run.solved else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "key", nargs="?", default="logic.boolean_laws.de_morgan_laws"
    )
    args = parser.parse_args()
    return demo(Path(__file__).resolve().parent.parent, args.key)


if __name__ == "__main__":
    raise SystemExit(main())
