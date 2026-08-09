#!/usr/bin/env python3
"""UNKNOWN-triggered retrieval over the project's extrinsic knowledge stores.

The store is deliberately read-only and symbolic. It unifies five committed
sources into one query surface: corpus statements, their lexica, structural
twin/mirror groups, decomposition entries, and machine-proof links. Retrieval
may add Open English WordNet as a sixth, external source when the caller names
an archive; absence leaves the five-store behavior byte-for-byte unchanged.
RETRIEVE does not answer a slot by itself; it appends stable, indexed material
to the session context, and a later POINT action binds one item to the pending
slot.

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
from proof_artifacts import (
    resolve_contained_artifact,
    select_closing_transitions,
)
from oracle_controller_demo import TRUSTED_TRIPLES_SHA256
from wordnet_store import WordNetIndex, WordNetSynset, lemma_key


SOURCE_ORDER = {
    "corpus": 0,
    "lexicon": 1,
    "wordnet": 2,
    "twin_ledger": 3,
    "decomposition": 4,
    "proof": 5,
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
    # Structured provenance marker (review finding: trust lived only in a text
    # substring). For proofs it authenticates the expected artifact digest;
    # for external lexical data it means the source bytes were digested and
    # parsed, never that their semantics were formally verified.
    trusted: bool = True


@dataclass(frozen=True)
class QueryResult:
    mode: str
    query: str
    items: tuple[RetrievalItem, ...] = ()
    # Total matches before the deterministic limit; len(items) < total means
    # truncation happened and the caller must say so (no silent caps).
    total: int = 0


class UnifiedKnowledgeStore:
    """Read local corpus/report artifacts through one exact interface.

    Trust model, stated precisely (review findings F3/F8): the store reads
    the WORKING TREE, not git -- "committed" here means the files the repo
    tracks, trusted as-is; the only content-addressed pin is the Lean
    artifact digest, and that digest covers artifact BYTES, not the
    semantic correspondence between a statement and the theorem its
    `verified_by` cites. That correspondence is unchecked node metadata
    today (BACKLOG: verified_by semantic lint). Duplicate statement_ids
    across corpora resolve last-writer-wins here; validate_nodes.py names
    any such collision on the merged graph.
    """

    def __init__(
        self,
        items: tuple[RetrievalItem, ...] = (),
        wordnet: WordNetIndex | None = None,
    ):
        ids = [item.item_id for item in items]
        if len(ids) != len(set(ids)):
            raise ValueError("retrieval item ids must be unique")
        self.items = tuple(
            sorted(items, key=lambda item: (SOURCE_ORDER[item.source], item.item_id))
        )
        self.wordnet = wordnet

    @classmethod
    def load(
        cls,
        data_dir: Path,
        reports_dir: Path,
        wordnet_path: Path | None = None,
    ) -> "UnifiedKnowledgeStore":
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
                if not isinstance(verified_by, list) or not all(
                    isinstance(entry, dict)
                    and isinstance(entry.get("system"), str)
                    and isinstance(entry.get("artifact"), str)
                    for entry in verified_by
                ):
                    raise ValueError(
                        f"statement {statement_id!r} has a malformed "
                        "verified_by value; run scripts/validate_nodes.py"
                    )
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
                    # Shared containment boundary (review F1): the same
                    # helper the validator uses, so an out-of-root artifact
                    # can never mint a proof record here even if its bytes
                    # match the trusted digest.
                    artifact_path = resolve_contained_artifact(
                        repo_root, entry["artifact"]
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
                    transitions, resolved_reference = select_closing_transitions(
                        artifact_path, reference
                    )
                    if reference is None:
                        detail = (
                            f"{entry['system']}:{resolved_reference} "
                            f"({entry['artifact']})"
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
                            else "conjectured"
                        ),
                        source_ids=(statement_id, *artifacts),
                        aliases=(statement_id, title, *references, *artifacts),
                        trusted=all(proof_artifacts_trusted),
                    )
                )

        # Weakest-member inheritance for derivative records (review
        # finding F1: a hardcoded "verified" let an empirical statement be
        # answered by a stronger-labeled twin/decomposition record). Order is
        # the schema's epistemic_status enum from weakest to strongest.
        status_strength = {
            "conjectured": 0,
            "empirical": 1,
            "asymptotic": 2,
            "assumed": 3,
            "derived": 4,
            "formal": 5,
        }

        def weakest_status(statement_ids: tuple[str, ...]) -> str:
            statuses = [
                nodes[statement_id]["epistemic_status"]
                for statement_id in statement_ids
            ]
            return min(statuses, key=lambda s: status_strength.get(s, 0))

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
                        epistemic_status=weakest_status(member_ids),
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
                    epistemic_status=weakest_status((statement_id,)),
                    source_ids=(statement_id,),
                    aliases=(statement_id, nodes[statement_id]["title"], *constituents),
                )
            )
        if wordnet_path is not None and not wordnet_path.is_file():
            # Graceful absence covers the UNNAMED default only. A caller
            # who explicitly named an archive meant to use it; silently
            # degrading to five stores would hide a typo (review nit 2).
            raise FileNotFoundError(
                f"named WordNet archive does not exist: {wordnet_path}"
            )
        wordnet = (
            WordNetIndex.load(wordnet_path) if wordnet_path is not None
            else None
        )
        return cls(tuple(items), wordnet)

    def _wordnet_item(self, synset: WordNetSynset) -> RetrievalItem:
        if self.wordnet is None:
            raise ValueError("WordNet is not loaded")
        relation_text = "; ".join(
            f"{relation}={','.join(targets)}"
            for relation, targets in synset.relations
        )
        text = " | ".join(synset.definitions)
        if synset.examples:
            text += " Examples: " + " | ".join(synset.examples)
        if relation_text:
            text += " Relations: " + relation_text
        return RetrievalItem(
            item_id=f"wordnet:{synset.synset_id}",
            source="wordnet",
            title="WordNet: " + ", ".join(synset.members),
            text=text,
            epistemic_status="empirical",
            source_ids=(
                f"oewn:2025:{synset.synset_id}",
                f"sha256:{self.wordnet.archive_sha256}",
            ),
            aliases=synset.members,
            trusted=True,
        )

    def _wordnet_resolution(
        self, key: str
    ) -> tuple[tuple[RetrievalItem, ...], tuple[RetrievalItem, ...]]:
        if self.wordnet is None:
            return (), ()
        synsets = self.wordnet.lookup(key)
        lexical = tuple(self._wordnet_item(synset) for synset in synsets)
        synonyms = {
            lemma_key(member)
            for synset in synsets
            for member in synset.members
            if lemma_key(member) != lemma_key(key)
        }
        bridged = tuple(
            item
            for item in self.items
            if item.source in {"corpus", "lexicon", "proof"}
            and any(
                lemma_key(alias) in synonyms
                for alias in item.aliases
            )
        )
        return bridged, lexical

    def _wordnet_supporting_synsets(
        self, item: RetrievalItem, key: str
    ) -> tuple[str, ...]:
        """Name the exact senses that bridge one key to one project item."""

        if self.wordnet is None:
            return ()
        item_aliases = {lemma_key(alias) for alias in item.aliases}
        support = []
        for synset in self.wordnet.lookup(key):
            synonyms = {
                lemma_key(member)
                for member in synset.members
                if lemma_key(member) != lemma_key(key)
            }
            if item_aliases & synonyms:
                support.append(synset.synset_id)
        return tuple(support)

    def query(self, key: str, limit: int = 24) -> QueryResult:
        exact = tuple(
            item
            for item in self.items
            if item_match_mode(item, key) == "exact"
        )
        if exact:
            return QueryResult("exact", key, exact[:limit], total=len(exact))

        if not query_tokens(key):
            return QueryResult("miss", key)

        neighborhood = tuple(
            item
            for item in self.items
            if item_match_mode(item, key) == "neighborhood"
        )
        if neighborhood:
            return QueryResult(
                "neighborhood",
                key,
                neighborhood[:limit],
                total=len(neighborhood),
            )
        bridged, lexical = self._wordnet_resolution(key)
        if bridged:
            resolved = bridged + lexical
            return QueryResult(
                "synonym",
                key,
                resolved[:limit],
                total=len(resolved),
            )
        if lexical:
            return QueryResult(
                "lexical",
                key,
                lexical[:limit],
                total=len(lexical),
            )
        return QueryResult("miss", key)

    def contains_item(self, item: RetrievalItem) -> bool:
        """Authenticate a pointable record against this store's loaded items.

        Value equality against what load() read from the working tree --
        an integrity check within the local-files-trusted model, not a
        git-anchored proof of commit membership.
        """

        if item in self.items:
            return True
        if item.source != "wordnet" or self.wordnet is None:
            return False
        prefix = "wordnet:"
        if not item.item_id.startswith(prefix):
            return False
        synset = self.wordnet.synsets.get(item.item_id[len(prefix) :])
        return synset is not None and self._wordnet_item(synset) == item

    def binding_match_mode(self, item: RetrievalItem, key: str) -> str | None:
        """Return a match only when the key resolves to one corpus owner.

        A lexicon symbol such as ``a`` may be an exact alias of dozens of
        unrelated statements. Retrieval may expose that neighborhood, but it
        is not an answer certificate: POINT can bind only when the corpus,
        lexicon, and proof views that match the key identify one statement.
        """

        mode = item_match_mode(item, key)
        if item.source != "wordnet" and mode is not None:
            project_mode = self._project_binding_match_mode(item, key, mode)
            if project_mode is not None:
                return project_mode

        bridged, lexical = self._wordnet_resolution(key)
        if item in lexical:
            # A bare lexical binding needs one sense. Polysemous records remain
            # pointable context until another constraint disambiguates them.
            return "lexical" if len(lexical) == 1 else None
        if item in bridged:
            owners = {candidate.source_ids[0] for candidate in bridged}
            support = self._wordnet_supporting_synsets(item, key)
            if (
                len(owners) == 1
                and item.source_ids[0] in owners
                and len(support) == 1
            ):
                return "synonym"
        return None

    def _project_binding_match_mode(
        self, item: RetrievalItem, key: str, mode: str
    ) -> str | None:
        """Apply the pre-WordNet exact/neighborhood ownership contract."""

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
    resolution_channel: str = "store"


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
class ClarificationRequest:
    """Verifier-minted question for one frame-private UNKNOWN."""

    request_id: str
    slot: str
    prompt: str
    unresolved_literal: Literal
    suggested_key: str
    resolution_channel: str
    signature: str


@dataclass(frozen=True)
class UserBinding:
    """Channel-authenticated answer in the persistent user-owned frame."""

    request_id: str
    slot: str
    value: str
    signature: str
    lifetime: str = "session"


@dataclass(frozen=True)
class UserFrame:
    """Runtime-owned interlocutor state; never promoted to corpus truth.

    ``superseded_request_ids`` is auditable state, not authority. The verifier's
    private committed ledger prevents a caller from deleting this tuple to
    resurrect an earlier signed answer.
    """

    owner: str = "user"
    questions: tuple[ClarificationRequest, ...] = ()
    bindings: tuple[UserBinding, ...] = ()
    consumed_request_ids: tuple[str, ...] = ()
    superseded_request_ids: tuple[str, ...] = ()


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
    user_frame: UserFrame = field(default_factory=UserFrame)
    awaiting: ClarificationRequest | None = None

    @classmethod
    def from_unknown(
        cls,
        executor: FrameExecutor,
        frame: FrameState,
        slot: str,
        suggested_key: str,
        unresolved_literal: Literal,
        resolution_channel: str = "store",
        user_owner: str = "user",
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
        if resolution_channel not in {"store", "user"}:
            raise ValueError("resolution_channel must be 'store' or 'user'")
        if not user_owner.strip():
            raise ValueError("user_owner must be non-empty")
        return cls(
            frame=frame,
            pending=RetrievalNeed(
                slot,
                suggested_key,
                unresolved_literal,
                tuple(finding.evidence),
                resolution_channel,
            ),
            user_frame=UserFrame(owner=user_owner),
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
        self._ask_secret = secrets.token_bytes(32)
        self._consumed_ask_requests: set[tuple[str, str]] = set()
        self._superseded_ask_bindings: set[tuple[str, str]] = set()

    def _ask_signature(self, domain: str, *parts: object) -> str:
        payload = repr((domain, *parts)).encode("utf-8")
        return hmac.new(self._ask_secret, payload, hashlib.sha256).hexdigest()

    @staticmethod
    def _question_parts(
        state: RetrievalState, request: ClarificationRequest
    ) -> tuple[object, ...]:
        return (
            state.session_id,
            repr(state.frame.spec),
            state.user_frame.owner,
            request.request_id,
            request.slot,
            request.unresolved_literal,
            request.suggested_key,
            request.resolution_channel,
            request.prompt,
        )

    def _valid_question(
        self, state: RetrievalState, request: ClarificationRequest
    ) -> bool:
        expected = self._ask_signature(
            "question", *self._question_parts(state, request)
        )
        return hmac.compare_digest(request.signature, expected)

    def reply_action(self, state: RetrievalState, value: str) -> Action:
        """Trusted return-channel boundary: sign one actual user response."""
        request = state.awaiting
        if request is None or not self._valid_question(state, request):
            raise ValueError("cannot reply without a verifier-minted question")
        if not value.strip():
            raise ValueError("user reply must be non-empty")
        signature = self._ask_signature(
            "reply", *self._question_parts(state, request), value
        )
        return Action.build(
            ActionKind.ASK,
            "reply",
            {
                "request_id": request.request_id,
                "value": value,
                "signature": signature,
            },
        )

    def binding_value(self, state: RetrievalState, slot: str) -> str | None:
        """Return the latest authentic user binding for this exact session."""
        for binding in reversed(state.user_frame.bindings):
            if binding.slot != slot:
                continue
            if (state.session_id, binding.request_id) in (
                self._superseded_ask_bindings
            ):
                continue
            if self._valid_binding(state, binding):
                return binding.value
        return None

    def _valid_binding(
        self, state: RetrievalState, binding: UserBinding
    ) -> bool:
        expected = self._ask_signature(
            "binding",
            state.session_id,
            repr(state.frame.spec),
            state.user_frame.owner,
            binding.request_id,
            binding.slot,
            binding.value,
            binding.lifetime,
        )
        return hmac.compare_digest(binding.signature, expected)

    def commit_run(self, trace: tuple[object, ...]) -> None:
        """Atomically consume replies only when Controller returns the run."""
        consumed: set[tuple[str, str]] = set()
        superseded: set[tuple[str, str]] = set()
        for entry in trace:
            action = entry.action
            if (
                entry.accepted
                and action.kind is ActionKind.ASK
                and action.name == "reply"
            ):
                request_id = action.argument("request_id")
                if request_id is not None:
                    consumed.add((entry.state_after.session_id, request_id))
                    slot = next(
                        (
                            binding.slot
                            for binding in reversed(
                                entry.state_after.user_frame.bindings
                            )
                            if binding.request_id == request_id
                            and self._valid_binding(
                                entry.state_after, binding
                            )
                        ),
                        None,
                    )
                    if slot is not None:
                        superseded.update(
                            (entry.state_before.session_id, binding.request_id)
                            for binding in entry.state_before.user_frame.bindings
                            if binding.slot == slot
                            and self._valid_binding(
                                entry.state_before, binding
                            )
                        )
        self._consumed_ask_requests.update(consumed)
        self._superseded_ask_bindings.update(superseded)

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
                state.user_frame,
                state.awaiting,
            )
        )

    def evaluate(
        self, state: RetrievalState, action: Action
    ) -> Verification[RetrievalState]:
        if state.awaiting is not None and not (
            action.kind is ActionKind.ASK and action.name == "reply"
        ):
            return Verification(
                Verdict.REFUSED,
                "controller is waiting for the outstanding user reply; no "
                "other transition may advance this branch",
                evidence=(state.awaiting.request_id,),
            )
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
        if action.kind is ActionKind.ASK:
            if action.name == "clarify":
                return self._ask(state, action)
            if action.name == "reply":
                return self._reply(state, action)
            return Verification(
                Verdict.REFUSED,
                f"unknown ASK transition {action.name!r}",
                evidence=(self.name,),
            )

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
        if state.pending.resolution_channel == "user":
            return Verification(
                Verdict.REFUSED,
                "pending UNKNOWN is user-private; RETRIEVE cannot impersonate "
                f"the interlocutor, use ASK({state.pending.slot})",
                evidence=(state.user_frame.owner, f"ASK({state.pending.slot})"),
            )
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
                "exact, neighborhood, and lexical retrieval all missed; UNKNOWN stays "
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
        truncation = (
        ""
            if result.total <= len(result.items)
            else (
                f" ({result.total - len(result.items)} further matches "
                "deterministically truncated at the query limit)"
            )
        )
        return Verification(
            Verdict.VERIFIED,
            f"{result.mode} retrieval transaction added {len(added)} pointable "
            "items without changing their own epistemic statuses"
            + truncation,
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
        if state.frame.closed:
            return Verification(
                Verdict.REFUSED,
                "frame is closed; POINT cannot bind into it",
                evidence=(state.frame.spec.frame,),
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

    def _ask(
        self, state: RetrievalState, action: Action
    ) -> Verification[RetrievalState]:
        if state.frame.closed:
            return Verification(
                Verdict.REFUSED,
                "frame is closed; ASK cannot extend its user context",
                evidence=(state.frame.spec.frame,),
            )
        if state.pending is None:
            return Verification(
                Verdict.REFUSED,
                "ASK requires an unresolved UNKNOWN slot",
                evidence=(self.name,),
            )
        stale = self._pending_is_current_unknown(state)
        if stale is not None:
            return stale
        if state.awaiting is not None:
            return Verification(
                Verdict.REFUSED,
                "one clarification is already awaiting a user reply",
                evidence=(state.awaiting.request_id,),
            )
        if not state.user_frame.owner.strip():
            return Verification(
                Verdict.REFUSED,
                "ASK requires a non-empty user-frame owner",
                evidence=(self.name,),
            )
        if state.pending.resolution_channel not in {"store", "user"}:
            return Verification(
                Verdict.REFUSED,
                "pending UNKNOWN has an invalid resolution channel",
                evidence=(state.pending.slot,),
            )
        if (
            state.pending.resolution_channel != "user"
            and state.frame.spec.retrieval != "frame_local"
        ):
            return Verification(
                Verdict.REFUSED,
                "pending UNKNOWN is assigned to the durable store, not the "
                "interlocutor",
                evidence=(state.pending.slot, "RETRIEVE"),
            )
        if tuple(key for key, _ in action.arguments) != ("slot",):
            return Verification(
                Verdict.REFUSED,
                "ASK(clarify) requires exactly one slot argument",
                evidence=(self.name,),
            )
        if action.dependencies:
            return Verification(
                Verdict.REFUSED,
                "ASK(clarify) accepts no policy-supplied dependencies",
                evidence=(self.name,),
            )
        slot = action.argument("slot")
        if slot != state.pending.slot:
            return Verification(
                Verdict.REFUSED,
                "ASK slot must equal the pending UNKNOWN slot",
                evidence=(state.pending.slot, slot or ""),
            )
        request_id = secrets.token_hex(16)
        literal = state.pending.unresolved_literal
        prompt = (
            f"What value should fill {slot!r} for "
            f"{literal.subject} {literal.predicate}?"
        )
        unsigned = ClarificationRequest(
            request_id,
            slot,
            prompt,
            literal,
            state.pending.suggested_key,
            state.pending.resolution_channel,
            signature="",
        )
        request = replace(
            unsigned,
            signature=self._ask_signature(
                "question", *self._question_parts(state, unsigned)
            ),
        )
        return Verification(
            Verdict.VERIFIED,
            "clarification request recorded in the persistent user frame; "
            "controller must wait for interlocutor input",
            replace(
                state,
                awaiting=request,
                user_frame=replace(
                    state.user_frame,
                    questions=state.user_frame.questions + (request,),
                ),
            ),
            (state.user_frame.owner, f"ASK({slot})", request_id),
        )

    def _reply(
        self, state: RetrievalState, action: Action
    ) -> Verification[RetrievalState]:
        if state.frame.closed:
            return Verification(
                Verdict.REFUSED,
                "frame is closed; a user reply cannot bind into it",
                evidence=(state.frame.spec.frame,),
            )
        request = state.awaiting
        if state.pending is None or request is None:
            return Verification(
                Verdict.REFUSED,
                "ASK(reply) requires a pending verifier-minted question",
                evidence=(self.name,),
            )
        if not self._valid_question(state, request):
            return Verification(
                Verdict.REFUSED,
                "clarification request provenance is invalid for this "
                "session/frame/user",
                evidence=(state.user_frame.owner,),
            )
        consumed_key = (state.session_id, request.request_id)
        if (
            consumed_key in self._consumed_ask_requests
            or request.request_id in state.user_frame.consumed_request_ids
        ):
            return Verification(
                Verdict.REFUSED,
                "clarification request was already consumed; a later need "
                "requires fresh user input",
                evidence=(request.request_id,),
            )
        stale = self._pending_is_current_unknown(state)
        if stale is not None:
            return stale
        if (
            state.pending.slot != request.slot
            or state.pending.unresolved_literal != request.unresolved_literal
            or state.pending.suggested_key != request.suggested_key
            or state.pending.resolution_channel != request.resolution_channel
        ):
            return Verification(
                Verdict.REFUSED,
                "pending UNKNOWN differs from the signed clarification request",
                evidence=(request.request_id,),
            )
        if (
            state.pending.resolution_channel != "user"
            and state.frame.spec.retrieval != "frame_local"
        ):
            return Verification(
                Verdict.REFUSED,
                "signed clarification no longer targets a user-resolvable need",
                evidence=(request.request_id,),
            )
        expected_keys = ("request_id", "signature", "value")
        if tuple(key for key, _ in action.arguments) != expected_keys:
            return Verification(
                Verdict.REFUSED,
                "ASK(reply) requires exactly request_id, signature, and value",
                evidence=(request.request_id,),
            )
        if action.dependencies:
            return Verification(
                Verdict.REFUSED,
                "ASK(reply) accepts no policy-supplied dependencies",
                evidence=(request.request_id,),
            )
        request_id = action.argument("request_id")
        value = action.argument("value")
        signature = action.argument("signature")
        if request_id != request.request_id or value is None or not value.strip():
            return Verification(
                Verdict.REFUSED,
                "user reply has a missing/mismatched request id or empty value",
                evidence=(request.request_id,),
            )
        expected = self._ask_signature(
            "reply", *self._question_parts(state, request), value
        )
        if signature is None or not hmac.compare_digest(signature, expected):
            return Verification(
                Verdict.REFUSED,
                "user reply signature is invalid; policy output is not user "
                "input",
                evidence=(request.request_id,),
            )
        binding = UserBinding(
            request.request_id,
            request.slot,
            value,
            self._ask_signature(
                "binding",
                state.session_id,
                repr(state.frame.spec),
                state.user_frame.owner,
                request.request_id,
                request.slot,
                value,
                "session",
            ),
        )
        superseded = tuple(
            prior.request_id for prior in state.user_frame.bindings
            if prior.slot == request.slot
            and prior.request_id
                not in state.user_frame.superseded_request_ids
            and self._valid_binding(state, prior)
        )
        return Verification(
            Verdict.VERIFIED,
            "channel-authenticated reply binds the frame-private UNKNOWN without "
            "asserting it as world or corpus truth",
            replace(
                state,
                pending=None,
                awaiting=None,
                user_frame=replace(
                    state.user_frame,
                    bindings=state.user_frame.bindings + (binding,),
                    consumed_request_ids=(
                        state.user_frame.consumed_request_ids
                        + (request.request_id,)
                    ),
                    superseded_request_ids=(
                        state.user_frame.superseded_request_ids + superseded
                    ),
                ),
            ),
            (state.user_frame.owner, request.request_id, request.slot),
        )


def retrieval_action(key: str) -> Action:
    return Action.build(ActionKind.RETRIEVE, "lookup", {"key": key})


def ask_action(slot: str) -> Action:
    return Action.build(ActionKind.ASK, "clarify", {"slot": slot})


def point_action(position: int) -> Action:
    return Action.build(ActionKind.POINT, "bind", {"position": str(position)})


def demo(repo_root: Path, key: str, wordnet_path: Path | None = None) -> int:
    executor = FrameExecutor()
    frame = executor.open_frame(
        # Retrieval is open here; story-local frames keep their existing guard.
        FrameSpec(frame="runtime.frames.retrieval_demo", retrieval="open")
    )
    state = RetrievalState.from_unknown(
        executor,
        frame,
        "answer",
        key,
        Literal("request", "needs", key),
    )
    store = UnifiedKnowledgeStore.load(
        repo_root / "data", repo_root / "reports", wordnet_path
    )
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
    parser.add_argument(
        "--wordnet",
        type=Path,
        help="optional external Open English WordNet 2025 JSON zip",
    )
    args = parser.parse_args()
    return demo(Path(__file__).resolve().parent.parent, args.key, args.wordnet)


if __name__ == "__main__":
    raise SystemExit(main())
