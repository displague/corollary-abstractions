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

ROADMAP-v0.7 item 6 makes that ladder executable and extends it outward. The
complete miss chain is ``exact -> neighborhood -> derivation -> tool -> ASK ->
abstention`` (:data:`MISS_CHAIN`), every rung is a real controller transition
with its own verdict in the trace, and no rung may raise a record above the
rung it honestly occupies. A successful tool transaction proves *what was
fetched*, not that its content is true.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass, field, replace
from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable

from controller import (
    Action,
    ActionKind,
    Controller,
    RunResult,
    SequencePolicy,
    TraceEntry,
    Verification,
    Verdict,
)
from observation_adapter import (
    EXTERNAL_RUNG_CEILING,
    LocalObservationAdapter,
    Observation,
    ObservationSource,
    SourceProbe,
)
from text_keys import (
    SCORE_DEFINITION,
    alias_covered,
    exact_key,
    overlap_score,
    query_tokens,
)
from frames import (
    FrameAssertionVerifier,
    FrameExecutor,
    FrameSpec,
    FrameState,
    Literal,
)
from lifetimes import Lifetime, declarable
from session_keys import (
    KEY_SCHEMA,
    KeyRingRefusal,
    RefusalReason,
    SessionKeyRing,
    owner_scope,
    session_scope,
)
from proof_artifacts import (
    resolve_contained_artifact,
    select_closing_transitions,
)
from wordnet_store import WordNetIndex, WordNetSynset, lemma_key


# Sort order of the unified surface. The first six values are frozen: they fix
# the deterministic order of every existing query result. Sources added by
# ROADMAP-v0.7 item 6 append (they never renumber), and neither of them is a
# member of ``UnifiedKnowledgeStore.items`` -- both are reached only through
# their own explicitly requested rung, so the five/six-store query surface is
# byte-for-byte what it was.
SOURCE_ORDER = {
    "corpus": 0,
    "lexicon": 1,
    "wordnet": 2,
    "twin_ledger": 3,
    "decomposition": 4,
    "proof": 5,
    "derivation": 6,
    "wordnet_relation": 7,
    "observation": 8,
}

#: Sources that may appear in :attr:`UnifiedKnowledgeStore.items`.
COMMITTED_SOURCES = ("corpus", "lexicon", "twin_ledger", "decomposition", "proof")

#: The closed set of WordNet relations this store will walk. Item 6 names
#: exactly these three. An unregistered relation name is not walked -- the
#: registration rule of docs/DESIGN-interactive-harness.md §3.2 applied to
#: lexical edges: the store does not invent a path it was not given.
WALKABLE_RELATIONS = ("antonym", "entailment", "hypernym")


class Channel(str, Enum):
    """Who owns the answer to a pending UNKNOWN.

    BACKLOG "resolution_channel string-not-Enum": this was a validated string
    where the house pattern (``Verdict``, ``StopReason``, ``ActionKind``) is an
    Enum. No laundering path existed and none is created; the Enum makes the
    closed set checkable by the type system instead of by a literal set
    comparison repeated at four call sites. It subclasses ``str`` exactly as
    ``Verdict`` does, so ``Channel.USER == "user"`` and every existing caller
    that passes ``"user"``/``"store"`` keeps working.
    """

    STORE = "store"
    USER = "user"


class Rung(str, Enum):
    """One step of ROADMAP-v0.7 item 6's miss chain.

    The chain is ordered by *decreasing project authority*, not by cost: an
    exact committed match outranks a token neighborhood, which outranks a
    precomputed structural relation, which outranks anything outside the
    repository, which outranks asking the interlocutor, which outranks
    inventing an answer (there is no rung for that; the chain ends in
    ABSTAIN).
    """

    EXACT = "exact"
    NEIGHBORHOOD = "neighborhood"
    DERIVATION = "derivation"
    TOOL = "tool"
    ASK = "ask"
    ABSTAIN = "abstain"


#: The store-side rungs, in order. ``ASK`` and ``ABSTAIN`` are not store
#: queries: ASK is a different action kind and abstention is the absence of
#: any accepted transition, which is why they are not in this tuple even
#: though they are in the chain.
MISS_CHAIN: tuple[Rung, ...] = (
    Rung.EXACT,
    Rung.NEIGHBORHOOD,
    Rung.DERIVATION,
    Rung.TOOL,
)


def _artifact_is_pinned(
    repo_root: Path, artifact: str, digest: str
) -> bool:
    """Does this artifact's digest match the manifest's pin for it?

    Trust used to be ONE hardcoded constant — the sha256 of
    `prover/sample_triples.json` — which was exactly right while the repo
    had exactly one proof artifact. v0.10 item 2 added a second (the traced
    `prover/ingested_triples.json`, itself backed by committed external
    verifier verdicts), and a hardcoded single digest answers `untrusted`
    for every artifact that is not the first one. The pin registry is
    `prover/proof-artifact-manifest.json`, which the validator's ledger rung
    already re-checks; this reads the same pin rather than keeping a second,
    silently narrower list. An artifact absent from the manifest, a manifest
    that will not parse, or a digest that does not match stays UNTRUSTED —
    the record is then `conjectured`, never dropped.
    """

    manifest_path = repo_root / "prover" / "proof-artifact-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entry = manifest["artifacts"][artifact]
    except (OSError, ValueError, KeyError, TypeError):
        return False
    return isinstance(entry, dict) and entry.get("sha256") == digest


def item_match_mode(item: "RetrievalItem", key: str) -> str | None:
    """Return the exact closed-form relation between a key and one item."""

    if any(exact_key(key) == exact_key(alias) for alias in item.aliases):
        return "exact"
    tokens = query_tokens(key)
    if not tokens:
        return None
    if any(alias_covered(tokens, query_tokens(alias)) for alias in item.aliases):
        return "neighborhood"
    return None


def item_score(item: "RetrievalItem", key: str) -> float:
    """Best closed-form alias relevance of one item to one key.

    See :func:`text_keys.overlap_score` for the definition. This is an
    ordering over already-admitted matches; it decides *sequence*, never
    admission and never epistemic status.
    """

    if not item.aliases:
        return 0.0
    return max(overlap_score(key, alias) for alias in item.aliases)


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
    # Announced ranking (item 6, "ranked neighborhood search with announced
    # scores and caps"). Parallel to ``items`` and populated only for modes
    # that are actually *ordered by score*; an empty tuple means "this mode's
    # order is the store's deterministic source order, not a ranking", which
    # is a claim the caller can check rather than a silence it must guess at.
    scores: tuple[float, ...] = ()
    # The cap that was applied to produce ``items``, announced even when it
    # did not bite, so a reader never has to infer the limit from a count.
    cap: int = 0

    @property
    def truncated(self) -> int:
        return max(0, self.total - len(self.items))

    @property
    def ranked(self) -> bool:
        return bool(self.scores)

    @property
    def lowest_admitted_score(self) -> float | None:
        return min(self.scores) if self.scores else None


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
        derivations: tuple[RetrievalItem, ...] = (),
        observation_sources: tuple[ObservationSource, ...] = (),
    ):
        ids = [item.item_id for item in items]
        if len(ids) != len(set(ids)):
            raise ValueError("retrieval item ids must be unique")
        if any(item.source not in COMMITTED_SOURCES for item in items):
            raise ValueError(
                "the unified query surface holds committed sources only; "
                "derivation, wordnet_relation and observation records are "
                "reachable through their own rung"
            )
        self.items = tuple(
            sorted(items, key=lambda item: (SOURCE_ORDER[item.source], item.item_id))
        )
        self.wordnet = wordnet
        # Kept OUT of ``items`` on purpose: adding them would silently change
        # every existing exact/neighborhood result. The derivation rung is the
        # only way in, so the five/six-store surface is unchanged.
        derivation_ids = [item.item_id for item in derivations]
        if len(derivation_ids) != len(set(derivation_ids)):
            raise ValueError("derivation item ids must be unique")
        self.derivations = tuple(
            sorted(derivations, key=lambda item: item.item_id)
        )
        self.observation_sources = tuple(observation_sources)
        # Process-local minting evidence for records this store issued from an
        # external source. Observations carry a fetch timestamp, so they
        # cannot be re-derived by value the way a committed record can; what
        # ``contains_item`` can honestly certify is "this store minted exactly
        # this record in this process", which is precisely the authority a
        # tool transaction has. Every mint is kept, not just the latest: two
        # fetches of the same observation are two transactions with two
        # timestamps, and both of them really happened.
        self._minted_observations: dict[str, tuple[RetrievalItem, ...]] = {}

    def probe_sources(self) -> tuple[SourceProbe, ...]:
        """Liveness of every registered external source. Never a rung claim."""

        return tuple(source.probe() for source in self.observation_sources)

    @classmethod
    def load(
        cls,
        data_dir: Path,
        reports_dir: Path,
        wordnet_path: Path | None = None,
        observation_sources: tuple[ObservationSource, ...] = (),
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
                    trusted_artifact = _artifact_is_pinned(
                        repo_root, entry["artifact"], artifact_digest
                    )
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
        derivations: list[RetrievalItem] = []
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
            # Derivation rung, half one: the constituent EDGE, one pointable
            # record per (statement, part). The decomposition record above
            # answers "what is this statement made of" as a single blob; an
            # edge record answers it part-by-part and, read backwards, lets a
            # key that names only a part reach every statement built from it.
            for index, constituent in enumerate(constituents):
                derivations.append(
                    RetrievalItem(
                        item_id=f"derivation:constituent:{statement_id}#{index}",
                        source="derivation",
                        title=(
                            f"{nodes[statement_id]['title']} decomposes to "
                            f"constituent {index}"
                        ),
                        text=(
                            f"{statement_id} has constituent {constituent} "
                            f"(groundedness={entry['groundedness']:.3f})"
                        ),
                        epistemic_status=weakest_status((statement_id,)),
                        source_ids=(statement_id,),
                        aliases=(
                            statement_id,
                            nodes[statement_id]["title"],
                            constituent,
                        ),
                    )
                )

        # Derivation rung, half two: committed specialization edges, which have
        # never been on the query surface before. The report is optional -- an
        # absent specializations.json leaves the rung empty and the rung says
        # so in its miss reason rather than pretending it looked.
        specialization_path = reports_dir / "specializations.json"
        if specialization_path.is_file():
            specialization_report = json.loads(
                specialization_path.read_text(encoding="utf-8")
            )
            for edge in specialization_report.get("specialization_edges", []):
                general = edge["general"]
                specific = edge["specific"]
                if general not in nodes or specific not in nodes:
                    # A report row naming a statement this store did not load
                    # is a stale report, not a new fact. Skipping keeps every
                    # derivation record's owner authenticatable against nodes.
                    continue
                bindings = "; ".join(
                    f"{name}->{value}"
                    for name, value in sorted(edge.get("bindings", {}).items())
                )
                derivations.append(
                    RetrievalItem(
                        item_id=f"derivation:specialization:{general}->{specific}",
                        source="derivation",
                        title=(
                            f"{nodes[general]['title']} specializes to "
                            f"{nodes[specific]['title']}"
                        ),
                        text=(
                            f"{edge['general_template']} => "
                            f"{edge['specific_template']} via {edge['via']} "
                            f"(cost={edge['cost']}, looseness="
                            f"{edge.get('looseness', 0)}); {bindings}"
                        ),
                        epistemic_status=weakest_status((general, specific)),
                        source_ids=(general, specific),
                        aliases=(
                            general,
                            specific,
                            nodes[general]["title"],
                            nodes[specific]["title"],
                            edge["general_template"],
                            edge["specific_template"],
                        ),
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
        return cls(tuple(items), wordnet, tuple(derivations), observation_sources)

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

    def _relation_item(
        self,
        origin: WordNetSynset,
        relation: str,
        target: WordNetSynset,
    ) -> RetrievalItem:
        """One walked lexical edge, kept attached to the sense that owns it.

        The item id names the ORIGIN sense as well as the target, so two
        senses of the same lemma that reach the same target produce two
        distinct records. That is the whole anti-flattening rule in one
        identifier: there is no representation of "the lemma's hypernym",
        only "this sense's hypernym".
        """

        if self.wordnet is None:
            raise ValueError("WordNet is not loaded")
        return RetrievalItem(
            item_id=(
                f"wordnet_relation:{origin.synset_id}:{relation}:"
                f"{target.synset_id}"
            ),
            source="wordnet_relation",
            title=(
                f"WordNet {relation}: "
                + ", ".join(origin.members)
                + " -> "
                + ", ".join(target.members)
            ),
            text=(
                f"sense {origin.synset_id} ({' | '.join(origin.definitions)}) "
                f"--{relation}--> {target.synset_id} "
                f"({' | '.join(target.definitions)})"
            ),
            # Lexical evidence never rises above empirical, and a walked edge
            # is weaker evidence than the sense it started from, not stronger.
            epistemic_status="empirical",
            source_ids=(
                f"oewn:2025:{origin.synset_id}",
                f"relation:{relation}",
                f"oewn:2025:{target.synset_id}",
                f"sha256:{self.wordnet.archive_sha256}",
            ),
            aliases=target.members,
            trusted=True,
        )

    def relation_records(
        self, key: str, relations: tuple[str, ...] = WALKABLE_RELATIONS
    ) -> tuple[RetrievalItem, ...]:
        """Walk one hop of the registered relations, per sense, never merged.

        Only the relation names in :data:`WALKABLE_RELATIONS` are walked, and
        only one hop: a one-hop edge is checkable directly against the archive
        (``target in origin.relations[relation]``), which is what lets
        :meth:`contains_item` authenticate a relation record without keeping
        process state. Multi-hop traversal is deliberately deferred rather
        than approximated (BACKLOG).
        """

        if self.wordnet is None:
            return ()
        unregistered = tuple(r for r in relations if r not in WALKABLE_RELATIONS)
        if unregistered:
            raise ValueError(
                f"unregistered WordNet relations {unregistered!r}; the "
                f"walkable set is {WALKABLE_RELATIONS!r}"
            )
        records: list[RetrievalItem] = []
        for origin in self.wordnet.lookup(key):
            edges = dict(origin.relations)
            for relation in relations:
                for target_id in edges.get(relation, ()):
                    target = self.wordnet.synsets.get(target_id)
                    if target is None:
                        # A dangling edge is the archive's problem, not a
                        # licence to invent the missing sense.
                        continue
                    records.append(self._relation_item(origin, relation, target))
        return tuple(
            sorted(records, key=lambda item: item.item_id)
        )

    def _observation_item(self, observation: Observation) -> RetrievalItem:
        if observation.rung not in EXTERNAL_RUNG_CEILING:
            raise ValueError(
                f"observation {observation.observation_id!r} reported rung "
                f"{observation.rung!r} above the external ceiling"
            )
        item = RetrievalItem(
            item_id=f"observation:{observation.source}:{observation.observation_id}",
            source="observation",
            title=f"{observation.title} [{observation.source}]",
            text=(
                f"{observation.text} (recorded {observation.recorded_at}; "
                f"fetched {observation.fetched_at} for query "
                f"{observation.query!r})"
            ),
            # The rung the SOURCE declared, capped by the adapter. Nothing
            # downstream may raise it: not the ranker, not a formal neighbour
            # in the same result, not the receipt that admitted it.
            epistemic_status=observation.rung,
            source_ids=observation.provenance,
            aliases=(
                observation.observation_id,
                observation.title,
                *observation.keywords,
            ),
            # A tool transaction proves what was fetched, not that it is true:
            # the bytes were digested and parsed, and that is the entire claim.
            trusted=True,
        )
        self._minted_observations[item.item_id] = (
            self._minted_observations.get(item.item_id, ()) + (item,)
        )
        return item

    def observation_records(self, key: str) -> tuple[RetrievalItem, ...]:
        records: list[RetrievalItem] = []
        for source in self.observation_sources:
            for observation in source.fetch(key):
                records.append(self._observation_item(observation))
        return tuple(records)

    def attempt(self, rung: Rung, key: str, limit: int = 24) -> QueryResult:
        """Execute exactly one rung of the miss chain, and nothing else.

        This is the executable form of ROADMAP-v0.7 item 6's ladder: the
        caller (or a controller policy) walks the rungs in order and each
        attempt is separately verdicted, so the trace shows what was tried and
        what it returned rather than a single opaque "retrieval". The composed
        :meth:`query` remains the legacy one-shot surface and is unchanged.
        """

        if rung is Rung.EXACT:
            exact = tuple(
                item for item in self.items if item_match_mode(item, key) == "exact"
            )
            return QueryResult(
                "exact", key, exact[:limit], total=len(exact), cap=limit
            )
        if rung is Rung.NEIGHBORHOOD:
            return self._ranked_neighborhood(key, limit)
        if rung is Rung.DERIVATION:
            matches = tuple(
                item
                for item in self.derivations
                if item_match_mode(item, key) is not None
            )
            ranked = self._rank(matches, key)
            admitted = ranked[:limit]
            return QueryResult(
                "derivation",
                key,
                tuple(item for item, _ in admitted),
                total=len(ranked),
                scores=tuple(score for _, score in admitted),
                cap=limit,
            )
        if rung is Rung.TOOL:
            bridged, lexical = self._wordnet_resolution(key)
            relations = self.relation_records(key)
            observations = self.observation_records(key)
            # Order is authority order, not score order: project material the
            # lexicon bridged to, then the senses themselves, then the walked
            # edges, then anything from outside the repository.
            resolved = bridged + lexical + relations + observations
            return QueryResult(
                "tool", key, resolved[:limit], total=len(resolved), cap=limit
            )
        raise ValueError(f"{rung!r} is not a store rung; see MISS_CHAIN")

    def _rank(
        self, matches: tuple[RetrievalItem, ...], key: str
    ) -> tuple[tuple[RetrievalItem, float], ...]:
        """Order matches by announced relevance, deterministically.

        Ties fall back to the store's existing ``(source, item_id)`` order, so
        ranking is a refinement of the previous order rather than a
        replacement for it: equally relevant material comes out exactly where
        it used to.
        """

        scored = [(item, item_score(item, key)) for item in matches]
        scored.sort(
            key=lambda pair: (
                -pair[1],
                SOURCE_ORDER[pair[0].source],
                pair[0].item_id,
            )
        )
        return tuple(scored)

    def _ranked_neighborhood(self, key: str, limit: int) -> QueryResult:
        matches = tuple(
            item
            for item in self.items
            if item_match_mode(item, key) == "neighborhood"
        )
        ranked = self._rank(matches, key)
        admitted = ranked[:limit]
        return QueryResult(
            "neighborhood",
            key,
            tuple(item for item, _ in admitted),
            total=len(ranked),
            scores=tuple(score for _, score in admitted),
            cap=limit,
        )

    def query(self, key: str, limit: int = 24) -> QueryResult:
        """Composed exact -> neighborhood -> synonym -> lexical lookup.

        Preserved verbatim in behaviour (modes, membership, and order) so the
        pre-item-6 callers and their receipts are unaffected; the only change
        is that the neighborhood branch now carries its announced ranking.
        The derivation and tool rungs are deliberately NOT reachable here --
        adding them would silently change what every existing key returns.
        Walk :data:`MISS_CHAIN` with :meth:`attempt` to reach them.
        """

        exact = self.attempt(Rung.EXACT, key, limit)
        if exact.items:
            return exact

        if not query_tokens(key):
            return QueryResult("miss", key)

        neighborhood = self._ranked_neighborhood(key, limit)
        if neighborhood.items:
            return neighborhood
        bridged, lexical = self._wordnet_resolution(key)
        if bridged:
            resolved = bridged + lexical
            return QueryResult(
                "synonym",
                key,
                resolved[:limit],
                total=len(resolved),
                cap=limit,
            )
        if lexical:
            return QueryResult(
                "lexical",
                key,
                lexical[:limit],
                total=len(lexical),
                cap=limit,
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
        if item.source == "derivation":
            return item in self.derivations
        if item.source == "wordnet_relation":
            return self._contains_relation_item(item)
        if item.source == "observation":
            # Re-derivation by value is impossible for an external record (its
            # fetch timestamp is part of it), so the honest check is minting
            # evidence: this process issued exactly this record. Forged text,
            # a forged rung, or a rung copied from a stronger neighbour all
            # fail the equality, which is what the check is for.
            return item in self._minted_observations.get(item.item_id, ())
        if item.source != "wordnet" or self.wordnet is None:
            return False
        prefix = "wordnet:"
        if not item.item_id.startswith(prefix):
            return False
        synset = self.wordnet.synsets.get(item.item_id[len(prefix) :])
        return synset is not None and self._wordnet_item(synset) == item

    def _contains_relation_item(self, item: RetrievalItem) -> bool:
        """Re-derive a walked edge from the archive, stateless.

        The item id carries origin/relation/target, so the edge is checked
        against the loaded index rather than trusted from the caller: a
        fabricated hypernym between two real senses fails here.
        """

        if self.wordnet is None:
            return False
        parts = item.item_id.split(":")
        if len(parts) != 4 or parts[0] != "wordnet_relation":
            return False
        _, origin_id, relation, target_id = parts
        if relation not in WALKABLE_RELATIONS:
            return False
        origin = self.wordnet.synsets.get(origin_id)
        target = self.wordnet.synsets.get(target_id)
        if origin is None or target is None:
            return False
        if target_id not in dict(origin.relations).get(relation, ()):
            return False
        return self._relation_item(origin, relation, target) == item

    def binding_match_mode(self, item: RetrievalItem, key: str) -> str | None:
        """Return a match only when the key resolves to one corpus owner.

        A lexicon symbol such as ``a`` may be an exact alias of dozens of
        unrelated statements. Retrieval may expose that neighborhood, but it
        is not an answer certificate: POINT can bind only when the corpus,
        lexicon, and proof views that match the key identify one statement.

        Item 6's three new sources each get their own rule, stated here rather
        than inherited by accident:

        * ``derivation`` records bind under the same one-owner contract as the
          committed views, because a specialization/decomposition edge names
          statements this repository already committed to;
        * ``wordnet_relation`` records **never** bind. A hypernym is WordNet's
          claim about a sense, not an answer to the key, and letting one bind
          is exactly how a polysemous lemma would launder a common
          superordinate ("change") into a corpus answer;
        * ``observation`` records bind only when the external source that
          returned them is unambiguous for this key, and they bind at their
          own declared rung -- binding never promotes them.
        """

        if item.source == "derivation":
            return self._derivation_binding_match_mode(item, key)
        if item.source == "wordnet_relation":
            return None
        if item.source == "observation":
            return self._observation_binding_match_mode(item, key)

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

    def _derivation_binding_match_mode(
        self, item: RetrievalItem, key: str
    ) -> str | None:
        """One-owner contract for the derivation rung.

        A derivation edge names committed statements, so it binds under the
        same shape of contract as the committed views, in two admitted cases:

        * the key reaches **exactly one** derivation record -- the same rule
          the twin_ledger already uses, where the answer is the *relation*
          itself rather than a statement; or
        * every derivation record the key reaches agrees on a **single owner**
          statement, and that owner is one of this record's ``source_ids``.

        A specialization edge carries two owners by construction, so the
        second case admits only constituent edges; the first is what lets a
        template that names one edge bind that edge. An exact committed match
        anywhere on the query surface outranks the whole rung: derivation is
        consulted only *after* exact and neighborhood miss, so binding it
        while an exact owner exists would be the chain running backwards.
        """

        mode = item_match_mode(item, key)
        if mode is None:
            return None
        exact_owners = {
            candidate.source_ids[0]
            for candidate in self.items
            if item_match_mode(candidate, key) == "exact"
        }
        if exact_owners:
            return None
        matches = tuple(
            candidate
            for candidate in self.derivations
            if item_match_mode(candidate, key) is not None
        )
        if len(matches) == 1 and matches[0].item_id == item.item_id:
            return "derivation"
        owners = {
            owner for candidate in matches for owner in candidate.source_ids
        }
        if len(owners) != 1 or next(iter(owners)) not in item.source_ids:
            return None
        return "derivation"

    def _observation_binding_match_mode(
        self, item: RetrievalItem, key: str
    ) -> str | None:
        """One-source contract for external observations.

        Binding requires (a) this store minted the record, (b) the record was
        fetched for this very key -- the query is part of its provenance, so a
        record fetched for a different question cannot be re-aimed -- (c) no
        higher rung already owns the key, and (d) exactly one observation id
        answers the key across every registered source. The returned mode is
        ``observation``; nothing here inspects or alters
        ``epistemic_status``, which stays whatever the source declared under
        the adapter's ceiling.

        Condition (c) is the fix for a self-review finding. Keeping the rung
        label honest is NOT sufficient: an observation file whose
        ``observation_id`` impersonates a committed statement id bound that
        statement's slot when a caller invoked the tool rung directly, because
        the record's own status ("empirical") was never the thing at issue --
        the *authority to answer* was. The miss chain would have stopped at
        the exact rung, but a verifier may not rely on a policy walking the
        ladder in order. The outranking test is therefore enforced here,
        where POINT is adjudicated.

        **That first fix covered one door.** External review found the other:
        ``item_match_mode`` only sees the key's *literal* reach into
        ``items``/``derivations``, and the WordNet synonym bridge reaches
        committed records through shared synset members, which no alias
        comparison can see. With an archive loaded, one TOOL transaction
        emits ``[corpus:proven, wordnet:empirical, observation:conjectured]``
        for a single key and POINT bound any of the three: a conjectured
        outside note answered the slot a proven statement answers. The
        outranking test now also consults :meth:`_wordnet_resolution`.

        Two ordering decisions are stated rather than inherited:

        * **Bridged committed records and the senses themselves outrank
          observations.** This is exactly the order :meth:`attempt` already
          emits at the TOOL rung (``bridged + lexical + relations +
          observations``); enforcing it at POINT is what makes the emission
          order an authority claim instead of a presentation detail.
        * **Reachability outranks, not bindability.** A polysemous lemma
          reaches two senses and binds neither; the honest reading is that
          the key's answer is *unresolved*, not that it is available to
          outside material. The pre-existing ``items``/``derivations`` test
          already worked this way, and splitting the two would mean an
          ambiguous corpus neighbourhood was easier for an external record
          to usurp than an unambiguous one.

        Walked ``wordnet_relation`` records deliberately do NOT outrank: they
        can never bind at all (see :meth:`binding_match_mode`), so treating
        them as an owner would leave the key answerable by nothing while
        claiming somebody owned it.

        The last clause refuses an ``observation_id`` that names a loaded
        synset. A synset id is not an alias, so the bridge above cannot see
        that impersonation either -- ``a-n`` reaches no lemma and therefore
        looked like a key nothing owned.
        """

        if item not in self._minted_observations.get(item.item_id, ()):
            return None
        if f"query:{exact_key(key)}" not in item.source_ids:
            return None
        if self._impersonates_a_synset(item):
            return None
        outranked = any(
            item_match_mode(candidate, key) is not None
            for candidate in self.items + self.derivations
        )
        if not outranked:
            bridged, lexical = self._wordnet_resolution(key)
            outranked = bool(bridged or lexical)
        if outranked:
            return None
        # Ask the sources directly rather than through observation_records():
        # checking a binding must not mint a new transaction record.
        ids = {
            f"observation:{source.source_id}:{observation.observation_id}"
            for source in self.observation_sources
            for observation in source.fetch(key)
        }
        if len(ids) != 1 or item.item_id not in ids:
            return None
        return "observation"

    def _impersonates_a_synset(self, item: RetrievalItem) -> bool:
        """True when an external record's own id names a loaded sense.

        Refused rather than raised: minting happens inside a RETRIEVE the
        verifier must be able to *answer*, and the record is still honest
        pointable context. What it may not do is own the key.
        """

        if self.wordnet is None:
            return False
        declared = tuple(
            part.split(":", 1)[1]
            for part in item.source_ids
            if part.startswith("observation:")
        )
        return any(name in self.wordnet.synsets for name in declared)

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
    resolution_channel: Channel = Channel.STORE


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
    """Verifier-minted evidence that RETRIEVE admitted these item ids.

    ``key_id`` names the root-key generation this signature descends from, so
    a ring holding several generations can verify a receipt minted before a
    rotation. It is covered by the signature: relabelling a receipt with
    another generation's id changes the payload and invalidates it. An empty
    ``key_id`` means "the verifier's own current generation" and is what every
    pre-item-2 caller produces, which keeps the ephemeral path byte-compatible.
    """

    session_id: str
    frame_scope: str
    key: str
    mode: str
    item_ids: tuple[str, ...]
    signature: str
    key_id: str = ""


@dataclass(frozen=True)
class ClarificationRequest:
    """Verifier-minted question for one frame-private UNKNOWN."""

    request_id: str
    slot: str
    prompt: str
    unresolved_literal: Literal
    suggested_key: str
    resolution_channel: Channel
    signature: str
    key_id: str = ""


@dataclass(frozen=True)
class UserBinding:
    """Channel-authenticated answer in the persistent user-owned frame.

    ``lifetime`` is the **declared** lifetime (``lifetimes.Lifetime``), chosen
    by the trusted return channel and covered by ``signature``; it is not the
    binding's current status. The effective lifetime — which may be
    ``superseded`` or ``expired`` — is computed on every read by
    :meth:`RetrievalVerifier.binding_status` from the private ledgers and the
    current goal, and is never stored anywhere a caller could edit it.
    """

    request_id: str
    slot: str
    value: str
    signature: str
    lifetime: str = Lifetime.SESSION.value
    key_id: str = ""


@dataclass(frozen=True)
class LedgerSnapshot:
    """The verifier's private anti-replay state, signed for transport.

    This is the record that makes a restart honest. Its two tuples are the
    consumed-request and supersession ledgers that
    ``docs/DESIGN-interactive-harness.md`` §3.3 named as the *second* blocker
    on durability (after keys): a process that reloaded keys but re-minted
    empty ledgers would silently re-admit every consumed request.

    It is signed, unlike the session file that carries it, because it is
    verifier-*private* state travelling through public space. ``sequence`` is
    stamped from the private keyring's monotone counter, and that — not the
    signature — is what refuses a rollback: an earlier snapshot is a genuinely
    signed message replayed out of order.

    ``PruningEvidence`` is deliberately **absent**. Carrying it would let a
    stale refusal outlive the process, and BACKLOG ("session pruning assumes a
    static rung store") already establishes that the TOOL rung can make a
    pruned branch answerable again. Losing pruning at a restart costs one
    re-query; carrying it can cost a wrong REFUSED that no longer has a cause.
    """

    schema: str
    key_id: str
    session_id: str
    owner: str
    sequence: int
    consumed: tuple[tuple[str, str], ...]
    superseded: tuple[tuple[str, str], ...]
    signature: str


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
        resolution_channel: Channel | str = Channel.STORE,
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
        try:
            # Callers keep passing "store"/"user"; the Enum is the internal
            # representation, and an unknown string still fails here with the
            # message it always had.
            channel = Channel(resolution_channel)
        except ValueError as exc:
            raise ValueError(
                "resolution_channel must be 'store' or 'user'"
            ) from exc
        if not user_owner.strip():
            raise ValueError("user_owner must be non-empty")
        return cls(
            frame=frame,
            pending=RetrievalNeed(
                slot,
                suggested_key,
                unresolved_literal,
                tuple(finding.evidence),
                channel,
            ),
            user_frame=UserFrame(owner=user_owner),
        )


class QueryStore(Protocol):
    """The verifier's view of a store. Unchanged for pre-item-6 stores.

    ``attempt`` is deliberately absent: a store that predates the miss chain
    (the frame-local guard's ``StoreMustNotRun``, for instance) still
    satisfies this protocol, and a rung-scoped RETRIEVE against such a store
    is REFUSED with the missing capability named rather than crashing. That
    is the registration rule again -- an unregistered path is refused, never
    improvised.
    """

    def query(self, key: str, limit: int = 24) -> QueryResult: ...

    def binding_match_mode(self, item: RetrievalItem, key: str) -> str | None: ...

    def contains_item(self, item: RetrievalItem) -> bool: ...


@runtime_checkable
class RungStore(QueryStore, Protocol):
    """A store that can execute one named rung of :data:`MISS_CHAIN`."""

    def attempt(self, rung: Rung, key: str, limit: int = 24) -> QueryResult: ...


@dataclass(frozen=True)
class PruningEvidence:
    """One closed branch, reusable for the rest of the session.

    ROADMAP-v0.7 item 6 asks that REFUTED and exhausted branches be stored as
    reusable pruning evidence; ``docs/DESIGN-interactive-harness.md`` §3.1/§6.2
    names the same record as the session-scoped substrate its dispatcher needs
    (adjudicated by **P-IH7**), because ``Controller.run``'s ``rejected`` set
    and ``SearchController``'s ``seen_states`` are run-local and reset at
    every dispatcher hop.

    The key is ``(session_id, verifier state_key, action fingerprint)``. All
    three parts are load-bearing: the session id keeps one conversation's dead
    ends out of another's, the state key means a branch is pruned only when
    the state key *matches* (so progress anywhere re-opens it), and the
    fingerprint pins the exact action including its arguments.

    "Matches" is deliberately weaker than "is identical", and the difference
    is the whole safety argument. See :meth:`RetrievalVerifier.state_key` for
    exactly what the key distinguishes and what it does not: two states this
    key cannot tell apart share a verdict whether or not that is sound, so a
    key that omits an authority-relevant field is a wrong-answer bug, not a
    cache-efficiency one. It was one, once (P-RT6, re-adjudicated).
    """

    session_id: str
    state_key: str
    action_fingerprint: tuple[object, ...]
    verdict: Verdict
    reason: str

    @property
    def key(self) -> tuple[str, str, tuple[object, ...]]:
        return (self.session_id, self.state_key, self.action_fingerprint)


class RetrievalVerifier:
    """Layer RETRIEVE/POINT over the existing frame verifier adapter."""

    name = "retrieval-harness"

    def __init__(
        self,
        store: QueryStore,
        frame_executor: FrameExecutor,
        keyring: SessionKeyRing | None = None,
        key_id: str | None = None,
    ):
        self.store = store
        self.frame_executor = frame_executor
        self.frame_verifier = FrameAssertionVerifier(frame_executor)
        # ROADMAP-v0.7 item 2. The default is an **ephemeral, per-instance**
        # ring: one random root, no file, dead at exit. That reproduces the
        # pre-item-2 contract exactly -- two default verifiers cannot read each
        # other's material, which is the claim
        # test_second_verifier_cannot_accept_first_verifiers_question makes --
        # and it is why the default is not a process-global ring. Durability is
        # opt-in: pass a SessionKeyRing.open(keyfile) and the same authority
        # comes back in the next process.
        self.keyring = keyring if keyring is not None else SessionKeyRing.ephemeral()
        self.key_id = key_id if key_id is not None else self.keyring.active_key_id
        self._consumed_ask_requests: set[tuple[str, str]] = set()
        self._superseded_ask_bindings: set[tuple[str, str]] = set()
        # Session-scoped pruning evidence (item 6 / P-IH7 substrate). Lives on
        # the verifier instance beside the anti-replay ledgers, for the same
        # reason: it is authority-adjacent state that must not be reachable by
        # public-tuple surgery. Written only by commit_run. Unlike the two
        # ledgers above it is NOT exported by :meth:`export_ledgers`; see
        # :class:`LedgerSnapshot` for why a stale refusal must not outlive the
        # process that earned it.
        self._pruning: dict[tuple[str, str, tuple[object, ...]], PruningEvidence] = {}

    # -- signing -----------------------------------------------------------

    def _signature(
        self, domain: str, scope: str, key_id: str, *parts: object
    ) -> str:
        """One MAC, purpose-bound twice over.

        The key is derived per ``(key_id, scope, domain)``, and ``key_id``,
        ``scope`` and ``domain`` are *also* written into the signed payload.
        The belt is the KDF: material signed for one session, owner, or domain
        produces an unrelated key elsewhere. The braces are the payload: even
        a caller who derived the wrong key cannot make a relabelled record
        verify, because the label is inside the message.
        """

        key = self.keyring.derive(key_id, scope, domain)
        payload = repr((KEY_SCHEMA, key_id, domain, scope, *parts)).encode("utf-8")
        return hmac.new(key, payload, hashlib.sha256).hexdigest()

    def _check(
        self,
        presented: str | None,
        domain: str,
        scope: str,
        key_id: str,
        *parts: object,
    ) -> RefusalReason | None:
        """``None`` when the signature authenticates, else the named reason.

        A record naming a key id this ring never had, or one that has been
        revoked, is refused *by name* before any comparison: "we cannot check
        this" and "we checked this and it is forged" are different facts and a
        boolean would merge them.
        """

        stated = key_id or self.key_id
        try:
            expected = self._signature(domain, scope, stated, *parts)
        except KeyRingRefusal as exc:
            return exc.reason
        if presented is None or not hmac.compare_digest(presented, expected):
            return RefusalReason.SIGNATURE_MISMATCH
        return None

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
        return (
            self._check(
                request.signature,
                "question",
                session_scope(state.session_id),
                request.key_id,
                *self._question_parts(state, request),
            )
            is None
        )

    def reply_action(
        self,
        state: RetrievalState,
        value: str,
        lifetime: Lifetime | str = Lifetime.SESSION,
    ) -> Action:
        """Trusted return-channel boundary: sign one actual user response.

        ``lifetime`` is declared *here*, at the channel, and signed into the
        reply. A policy cannot upgrade an answer to ``durable`` after the fact
        because the lifetime is inside the MAC, and it cannot declare
        ``superseded``/``expired`` at all because :func:`lifetimes.declarable`
        refuses the effective-only states.

        The default reply is byte-identical to the pre-item-2 one: the
        ``lifetime`` argument is omitted from the action's arguments when it is
        ``session``, so every existing action shape, fingerprint, and
        strict-argument test is untouched. The signature still covers the
        resolved lifetime, so an omitted argument is not an unsigned one.
        """

        request = state.awaiting
        if request is None or not self._valid_question(state, request):
            raise ValueError("cannot reply without a verifier-minted question")
        if not value.strip():
            raise ValueError("user reply must be non-empty")
        declared = declarable(lifetime)
        # Signed under the *question's* generation, not the ring's current
        # one. A rotation between the question and its answer must not orphan
        # an outstanding WAITING branch: the pair belongs together, and the
        # new binding minted from it is what gets the fresh generation.
        signature = self._signature(
            "reply",
            session_scope(state.session_id),
            request.key_id or self.key_id,
            *self._question_parts(state, request),
            value,
            declared.value,
        )
        arguments = {
            "request_id": request.request_id,
            "value": value,
            "signature": signature,
        }
        if declared is not Lifetime.SESSION:
            arguments["lifetime"] = declared.value
        return Action.build(ActionKind.ASK, "reply", arguments)

    def binding_scope(self, state: RetrievalState, lifetime: Lifetime) -> str:
        """Which key a binding of this lifetime is signed under.

        ``durable`` is owner-scoped; everything else is session-scoped. This
        one line is what makes ``durable`` mean something operationally rather
        than being a label: an owner-scoped key produces a MAC that a *new*
        session id can still verify, and a session-scoped one cannot. It is
        also the honest cost — a durable binding is not frame-isolated, and
        :mod:`lifetimes` says so in the protocol table.
        """

        if lifetime.crosses_sessions:
            return owner_scope(state.user_frame.owner)
        return session_scope(state.session_id)

    def _binding_parts(
        self,
        state: RetrievalState,
        lifetime: Lifetime,
        binding: UserBinding,
    ) -> tuple[object, ...]:
        if lifetime.crosses_sessions:
            # No session id and no frame spec: a durable answer must survive
            # both. The owner is already in the scope, hence in the key.
            return (
                state.user_frame.owner,
                binding.request_id,
                binding.slot,
                binding.value,
                lifetime.value,
            )
        return (
            state.session_id,
            repr(state.frame.spec),
            state.user_frame.owner,
            binding.request_id,
            binding.slot,
            binding.value,
            lifetime.value,
        )

    def binding_status(
        self, state: RetrievalState, binding: UserBinding
    ) -> Lifetime | RefusalReason:
        """The binding's *effective* lifetime, or the named reason it has none.

        Computed, never stored (see :mod:`lifetimes`). The order of the checks
        is the safety argument:

        1. an undeclarable lifetime is refused before any key is derived, so a
           binding claiming ``superseded`` cannot pick its own scope;
        2. the signature is checked next, under the scope its *declared*
           lifetime implies -- so relabelling a session binding ``durable`` to
           smuggle it into another session fails, because the durable payload
           and key are different objects entirely;
        3. supersession is consulted from the **private ledger first** and the
           public tuple second. Either one is sufficient to kill a binding;
           only the private one cannot be edited away, which is the whole
           reason it exists;
        4. goal-local expiry is last, because it is the only check that
           depends on the current conversation rather than on the record.
        """

        try:
            declared = declarable(binding.lifetime)
        except ValueError:
            return RefusalReason.UNDECLARABLE_LIFETIME
        scope = self.binding_scope(state, declared)
        reason = self._check(
            binding.signature,
            "binding",
            scope,
            binding.key_id,
            *self._binding_parts(state, declared, binding),
        )
        if reason is not None:
            return reason
        if (scope, binding.request_id) in self._superseded_ask_bindings:
            return RefusalReason.SUPERSEDED_BINDING
        if self.keyring.is_superseded(scope, binding.request_id):
            return RefusalReason.SUPERSEDED_BINDING
        if binding.request_id in state.user_frame.superseded_request_ids:
            return RefusalReason.SUPERSEDED_BINDING
        if declared is Lifetime.GOAL_LOCAL and self._goal_reopened(state, binding):
            return RefusalReason.EXPIRED_BINDING
        return declared

    @staticmethod
    def _goal_reopened(state: RetrievalState, binding: UserBinding) -> bool:
        """Has a newer question been minted for this binding's slot?

        A goal-local answer is scoped to the goal that asked for it, so the
        test is not "was it replaced by another answer" (that is supersession)
        but "was the question asked again". An unanswered reopening is enough:
        that is precisely the difference between the two lifetimes.
        """

        asked = [
            question.request_id
            for question in state.user_frame.questions
            if question.slot == binding.slot
        ]
        return bool(asked) and asked[-1] != binding.request_id

    def binding_value(self, state: RetrievalState, slot: str) -> str | None:
        """Return the latest authoritative user binding for this slot."""

        for binding in reversed(state.user_frame.bindings):
            if binding.slot != slot:
                continue
            status = self.binding_status(state, binding)
            if isinstance(status, Lifetime) and status.authoritative:
                return binding.value
        return None

    def binding_refusal(
        self, state: RetrievalState, binding: UserBinding
    ) -> RefusalReason | None:
        """The named reason this binding is not authoritative, if it is not."""

        status = self.binding_status(state, binding)
        return None if isinstance(status, Lifetime) else status

    def _valid_binding(
        self, state: RetrievalState, binding: UserBinding
    ) -> bool:
        """Signature-only authenticity, with no ledger or goal consultation.

        Kept distinct from :meth:`binding_status` on purpose: ``commit_run``
        and ``_reply`` need to enumerate the bindings a new answer *replaces*,
        and those are by definition about to become superseded. Asking the
        full status there would filter out the very records the supersession
        ledger has to be told about.
        """

        try:
            declared = declarable(binding.lifetime)
        except ValueError:
            return False
        return (
            self._check(
                binding.signature,
                "binding",
                self.binding_scope(state, declared),
                binding.key_id,
                *self._binding_parts(state, declared, binding),
            )
            is None
        )

    def session_pruning_evidence(
        self, session_id: str
    ) -> tuple[PruningEvidence, ...]:
        """Every closed branch this session has already paid for."""

        return tuple(
            sorted(
                (
                    evidence
                    for evidence in self._pruning.values()
                    if evidence.session_id == session_id
                ),
                key=lambda evidence: (evidence.state_key, repr(evidence.action_fingerprint)),
            )
        )

    def _pruned(
        self, state: RetrievalState, action: Action
    ) -> PruningEvidence | None:
        return self._pruning.get(
            (state.session_id, self.state_key(state), action.fingerprint)
        )

    def commit_run(self, trace: tuple[TraceEntry[RetrievalState], ...]) -> None:
        """Commit verifier-private effects only when Controller returns a run.

        Two ledgers are written here. Consuming ASK replies was always
        commit-gated; item 6's session pruning evidence joins it for exactly
        the same reason. A branch is recorded as closed only if it was closed
        inside a run the controller actually handed back, so a speculative
        ``evaluate`` -- a policy probing options, a test calling the verifier
        directly -- can never poison the session with a dead end it merely
        considered.
        """
        consumed: set[tuple[str, str]] = set()
        superseded: set[tuple[str, str]] = set()
        for entry in trace:
            action = entry.action
            verdict = entry.verification.verdict
            closed = verdict is Verdict.REFUTED or (
                verdict is Verdict.UNKNOWN
                and "ABSTAIN" in entry.verification.evidence
            )
            if closed:
                # REFUTED: the frame settled this literal against us.
                # UNKNOWN+ABSTAIN: the store is exhausted for this key.
                # REFUSED is deliberately NOT recorded -- it is an authority
                # or well-formedness answer, and re-proposing it costs one
                # cheap re-check rather than a re-query.
                evidence = PruningEvidence(
                    entry.state_before.session_id,
                    self.state_key(entry.state_before),
                    action.fingerprint,
                    verdict,
                    entry.verification.reason,
                )
                self._pruning.setdefault(evidence.key, evidence)
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
                            (
                                self._recorded_scope(entry.state_before, binding),
                                binding.request_id,
                            )
                            for binding in entry.state_before.user_frame.bindings
                            if binding.slot == slot
                            and self._valid_binding(
                                entry.state_before, binding
                            )
                        )
        self._consumed_ask_requests.update(consumed)
        self._superseded_ask_bindings.update(superseded)
        for scope, request_id in superseded:
            if scope.startswith("owner:"):
                # Owner-scoped (durable) retirements outlive every session, so
                # they belong in the ring, not on this instance. See
                # SessionKeyRing.record_superseded for the bug that proved it.
                self.keyring.record_superseded(scope, request_id)

    def _recorded_scope(
        self, state: RetrievalState, binding: UserBinding
    ) -> str:
        """The ledger scope a binding is filed under.

        Supersession is keyed by the binding's own signing scope, not by the
        session it happened to be replaced in. Otherwise a durable answer
        superseded during session A would come back to life in session B: the
        record would be filed under ``session:A`` and nothing in B would look
        there. The scope is derived from the *declared* lifetime, which is
        signed, so a caller cannot move a record between ledgers by editing it.
        """

        try:
            declared = declarable(binding.lifetime)
        except ValueError:
            return session_scope(state.session_id)
        return self.binding_scope(state, declared)

    # -- durable ledgers ---------------------------------------------------

    def export_ledgers(
        self, session_id: str, owner: str
    ) -> "LedgerSnapshot":
        """Sign this session's anti-replay state for transport across a restart.

        Two scopes are collected, not one: the session's own records, and the
        owner-scoped records that belong to ``durable`` bindings. Exporting
        only the session scope would carry a restart forward while quietly
        forgetting that a durable answer had been replaced.

        The sequence number is issued from the private keyring and is bumped
        *before* the signature is computed, so every export is strictly newer
        than the last. A snapshot is therefore not merely authentic; it has a
        place in an order that the public file cannot argue with.
        """

        scope = session_scope(session_id)
        mine = owner_scope(owner)
        consumed = tuple(
            sorted(
                entry
                for entry in self._consumed_ask_requests
                if entry[0] == session_id
            )
        )
        superseded = tuple(
            sorted(
                entry
                for entry in self._superseded_ask_bindings
                if entry[0] in (scope, mine)
            )
        )
        sequence = self.keyring.issue_sequence(scope)
        signature = self._signature(
            "ledger",
            scope,
            self.key_id,
            session_id,
            owner,
            sequence,
            consumed,
            superseded,
        )
        return LedgerSnapshot(
            schema=KEY_SCHEMA,
            key_id=self.key_id,
            session_id=session_id,
            owner=owner,
            sequence=sequence,
            consumed=consumed,
            superseded=superseded,
            signature=signature,
        )

    def import_ledgers(
        self, snapshot: "LedgerSnapshot", session_id: str, owner: str
    ) -> None:
        """Re-admit a signed ledger, or refuse it by name.

        Raises :class:`session_keys.KeyRingRefusal`. The check order is
        load-bearing and each step exists because skipping it is an attack:

        * **schema** first, so a future format cannot be read as this one;
        * **binding to the session and owner** next -- a snapshot is authority
          for exactly one conversation, and moving it is not a signature
          question;
        * **signature** before the counter, so a snapshot that never came from
          this ring cannot advance the high-water mark and lock out the real
          one (a denial-of-service that a naive "check freshness first"
          ordering would hand over free);
        * **sequence** last, refusing anything behind the high-water mark as
          ``ledger-rollback``. This is the only check that catches a
          *genuinely signed* older snapshot, and it works only because the
          counter lives in the private keyfile.

        Ledgers are merged, never replaced. A restore may only ever add
        refusals; there is no code path in which importing removes a consumed
        request or an existing supersession.
        """

        if snapshot.schema != KEY_SCHEMA:
            raise KeyRingRefusal(
                RefusalReason.SCHEMA_MISMATCH,
                f"snapshot declares {snapshot.schema!r}",
            )
        if snapshot.session_id != session_id or snapshot.owner != owner:
            raise KeyRingRefusal(
                RefusalReason.SESSION_MISMATCH,
                f"snapshot is for {snapshot.owner}/{snapshot.session_id}",
            )
        scope = session_scope(session_id)
        reason = self._check(
            snapshot.signature,
            "ledger",
            scope,
            snapshot.key_id,
            snapshot.session_id,
            snapshot.owner,
            snapshot.sequence,
            snapshot.consumed,
            snapshot.superseded,
        )
        if reason is not None:
            raise KeyRingRefusal(reason, f"ledger for {session_id}")
        self.keyring.admit_sequence(scope, snapshot.sequence)
        self._consumed_ask_requests.update(
            (entry[0], entry[1]) for entry in snapshot.consumed
        )
        self._superseded_ask_bindings.update(
            (entry[0], entry[1]) for entry in snapshot.superseded
        )

    def _receipt_signature(
        self,
        session_id: str,
        frame_scope: str,
        key: str,
        mode: str,
        item_ids: tuple[str, ...],
        key_id: str = "",
    ) -> str:
        return self._signature(
            "receipt",
            session_scope(session_id),
            key_id or self.key_id,
            session_id,
            frame_scope,
            exact_key(key),
            mode,
            item_ids,
        )

    def _valid_receipt(
        self, receipt: RetrievalReceipt, session_id: str, frame_scope: str
    ) -> bool:
        if (
            receipt.session_id != session_id
            or receipt.frame_scope != frame_scope
        ):
            return False
        return (
            self._check(
                receipt.signature,
                "receipt",
                session_scope(receipt.session_id),
                receipt.key_id,
                receipt.session_id,
                receipt.frame_scope,
                exact_key(receipt.key),
                receipt.mode,
                receipt.item_ids,
            )
            is None
        )

    def state_key(self, state: RetrievalState) -> str:
        """Distinguish two states that must not share a pruning verdict.

        ``repr(state.frame.spec)`` is here because of a review finding, and
        the reason it was missing is worth keeping: this key delegated the
        frame half to :meth:`FrameAssertionVerifier.state_key`, which keys on
        the frame's **name** plus its asserted claim ids, obligations and
        closed flag -- and omits ``declarations``, ``suspends`` and ``owner``.
        That is fine where it lives (``Controller.run``'s ``rejected`` set is
        run-local, and one run holds one frame), and it is NOT changed there.
        It is wrong here, because pruning evidence outlives the run: two
        same-named frames with contradictory premises produced the *same*
        key, so a REFUTED dead end in one returned REFUSED for the other,
        whose branch would have been VERIFIED. With belief frames that reads
        as Sally's dead end refusing Anne's branch and citing Sally's premise.
        The frame **scope** -- the spec, exactly the scope receipts are signed
        against in :meth:`_retrieve` -- is what separates them.

        What this key therefore distinguishes: the session, the frame scope
        (name, owner, declarations, suspends, governance, exit tier, retrieval
        policy), the frame's accepted claim ids / obligations / closed flag,
        the pending need, the retrieved context, bindings, resolutions,
        receipts, the user frame, and any outstanding question.

        What it does NOT distinguish, stated rather than implied: the frame's
        event history, its superseded declarations, its nested belief models,
        and -- the one that is a live assumption rather than an omission --
        the *contents of the store*. Pruning assumes the rung stores are
        static for a session, which the TOOL rung violates by design: a source
        that goes live mid-session leaves an earlier branch REFUSED. Filed as
        a v0.7 item 2/6 follow-up (BACKLOG, "session pruning assumes a static
        rung store"); it is a stale-refusal bug, not a wrong-binding one, and
        the honest fix is a re-consult policy rather than a wider key.
        """

        pending = None if state.pending is None else (
            state.pending.slot,
            state.pending.suggested_key,
            state.pending.unresolved_literal,
        )
        return repr(
            (
                self.frame_verifier.state_key(state.frame),
                repr(state.frame.spec),
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
        pruned = self._pruned(state, action)
        if pruned is not None:
            # Reusing evidence, not inventing a new judgment: this exact
            # action, in this session, from a state this verifier's state_key
            # cannot tell apart from the closed one, was already walked to a
            # close. The strength of that claim is exactly the strength of
            # state_key -- read its docstring for what it separates and for
            # the one assumption it still makes (a static rung store). It is
            # not, and should not be described as, "everything the answer
            # depends on": that phrasing is what let a state key missing the
            # frame scope look sound (P-RT6, re-adjudicated).
            return Verification(
                Verdict.REFUSED,
                "branch already closed in this session as "
                f"{pruned.verdict.value}; pruned by stored evidence",
                evidence=(self.name, pruned.verdict.value, pruned.reason),
            )
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
        if state.pending.resolution_channel == Channel.USER:
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

        rung = self._requested_rung(action)
        if isinstance(rung, Verification):
            return rung
        if rung is None:
            result = self.store.query(key)
        else:
            if not isinstance(self.store, RungStore):
                return Verification(
                    Verdict.REFUSED,
                    f"this store registers no {rung.value!r} rung; the miss "
                    "chain may not improvise one",
                    evidence=(key, rung.value),
                )
            result = self.store.attempt(rung, key)
        if not result.items:
            if rung is None:
                return Verification(
                    Verdict.UNKNOWN,
                    "exact, neighborhood, and lexical retrieval all missed; "
                    "UNKNOWN stays open and the controller must abstain rather "
                    "than confabulate",
                    evidence=(key, "ABSTAIN"),
                )
            return Verification(
                Verdict.UNKNOWN,
                f"miss-chain rung {rung.value!r} missed; UNKNOWN stays open "
                "and the next rung (or abstention) owns this need",
                evidence=(key, rung.value, "ABSTAIN"),
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
                self.key_id,
            ),
            self.key_id,
        )
        return Verification(
            Verdict.VERIFIED,
            f"{result.mode} retrieval transaction added {len(added)} pointable "
            "items without changing their own epistemic statuses"
            + self._announce_ranking(result),
            replace(
                state,
                context=state.context + added,
                retrieval_receipts=state.retrieval_receipts + (receipt,),
            ),
            (key, result.mode, *sources)
            if rung is None
            else (key, rung.value, result.mode, *sources),
        )

    @staticmethod
    def _requested_rung(
        action: Action,
    ) -> "Rung | None | Verification[RetrievalState]":
        """Read the optional rung argument, refusing anything not a STORE rung.

        Review finding: parsing with ``Rung(raw)`` alone accepted ``"ask"`` and
        ``"abstain"`` -- real members of the chain, but not store queries -- and
        the store then raised out of ``evaluate`` instead of returning a
        verdict. A verifier must answer a crafted action, never crash on one,
        so the admitted set is :data:`MISS_CHAIN`, not the whole Enum.
        """

        raw = action.argument("rung")
        if raw is None:
            return None
        rung = next(
            (member for member in MISS_CHAIN if member.value == raw), None
        )
        if rung is None:
            return Verification(
                Verdict.REFUSED,
                f"unregistered miss-chain rung {raw!r}; ASK is a different "
                "action kind and abstention is the absence of one",
                evidence=tuple(member.value for member in MISS_CHAIN),
            )
        return rung

    @staticmethod
    def _announce_ranking(result: QueryResult) -> str:
        """State the cap and the ranking, never leave a cut silent.

        The pre-item-6 rule was "announce what the limit dropped"; item 6 adds
        "announce what ordered the ones you kept, and what score the cut fell
        at", so a reader can tell a full answer from the top slice of a long
        one without re-running the query.
        """

        parts: list[str] = []
        if result.ranked:
            lowest = result.lowest_admitted_score
            assert lowest is not None
            parts.append(
                f" ranked by {SCORE_DEFINITION}; admitted scores "
                f"{max(result.scores):.6f}..{lowest:.6f} at cap {result.cap}"
            )
        if result.truncated:
            cut = (
                ""
                if not result.ranked
                else f", below score {result.lowest_admitted_score:.6f}"
            )
            parts.append(
                f" ({result.truncated} further matches "
                f"deterministically truncated at the query limit{cut})"
            )
        return "".join(parts)

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
        if state.pending.resolution_channel not in tuple(Channel):
            return Verification(
                Verdict.REFUSED,
                "pending UNKNOWN has an invalid resolution channel",
                evidence=(state.pending.slot,),
            )
        if (
            state.pending.resolution_channel != Channel.USER
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
            key_id=self.key_id,
        )
        request = replace(
            unsigned,
            signature=self._signature(
                "question",
                session_scope(state.session_id),
                self.key_id,
                *self._question_parts(state, unsigned),
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
            state.pending.resolution_channel != Channel.USER
            and state.frame.spec.retrieval != "frame_local"
        ):
            return Verification(
                Verdict.REFUSED,
                "signed clarification no longer targets a user-resolvable need",
                evidence=(request.request_id,),
            )
        # Two admitted shapes, both exact. The three-argument form is the
        # pre-item-2 reply and declares ``session`` by omission; the
        # four-argument form adds the explicit lifetime. Anything else is
        # still refused, so this stays a whitelist and not a relaxation --
        # ``lifetime`` is the only new key any caller may present, and its
        # value is checked against the signature two steps below.
        presented_keys = tuple(key for key, _ in action.arguments)
        if presented_keys not in (
            ("request_id", "signature", "value"),
            ("lifetime", "request_id", "signature", "value"),
        ):
            return Verification(
                Verdict.REFUSED,
                "ASK(reply) requires exactly request_id, signature, and value "
                "(optionally lifetime)",
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
        try:
            declared = declarable(action.argument("lifetime") or Lifetime.SESSION)
        except ValueError:
            return Verification(
                Verdict.REFUSED,
                "user reply declares an unregistered or effective-only "
                f"lifetime {action.argument('lifetime')!r}",
                evidence=(request.request_id, RefusalReason.UNDECLARABLE_LIFETIME),
            )
        reason = self._check(
            signature,
            "reply",
            session_scope(state.session_id),
            request.key_id,
            *self._question_parts(state, request),
            value,
            declared.value,
        )
        if reason is not None:
            return Verification(
                Verdict.REFUSED,
                "user reply signature is invalid; policy output is not user "
                "input",
                evidence=(request.request_id, reason),
            )
        unsigned = UserBinding(
            request.request_id,
            request.slot,
            value,
            signature="",
            lifetime=declared.value,
            key_id=self.key_id,
        )
        binding = replace(
            unsigned,
            signature=self._signature(
                "binding",
                self.binding_scope(state, declared),
                self.key_id,
                *self._binding_parts(state, declared, unsigned),
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


def retrieval_action(key: str, rung: Rung | None = None) -> Action:
    """One RETRIEVE, optionally scoped to a single miss-chain rung.

    Omitting ``rung`` keeps the pre-item-6 action byte-identical (arguments
    are ``{"key": ...}`` only), so every existing receipt, fingerprint, and
    replay test is unaffected. Naming a rung makes the ladder step visible in
    the controller trace instead of hidden inside one composed query.
    """

    arguments = {"key": key}
    if rung is not None:
        arguments["rung"] = rung.value
    return Action.build(ActionKind.RETRIEVE, "lookup", arguments)


def ask_action(slot: str) -> Action:
    return Action.build(ActionKind.ASK, "clarify", {"slot": slot})


def point_action(position: int) -> Action:
    return Action.build(ActionKind.POINT, "bind", {"position": str(position)})


def miss_chain_actions(
    key: str, slot: str, rungs: tuple[Rung, ...] = MISS_CHAIN
) -> tuple[Action, ...]:
    """ROADMAP-v0.7 item 6's chain as a proposable action sequence.

    ``exact -> neighborhood -> derivation -> tool -> ASK``. Abstention is not
    an action: it is what a run *is* when none of these was accepted, which is
    why the chain has no ABSTAIN proposal to forge. ASK is proposed
    unconditionally so the trace records its outcome either way -- VERIFIED
    (and WAITING) for a frame-private need, REFUSED with "assigned to the
    durable store" for a public one. Reading the chain's verdicts top to
    bottom tells you which rungs were tried, what each returned, and which
    authority owned the answer.
    """

    return tuple(retrieval_action(key, rung) for rung in rungs) + (
        ask_action(slot),
    )


def run_miss_chain(
    verifier: "RetrievalVerifier",
    state: RetrievalState,
    rungs: tuple[Rung, ...] = MISS_CHAIN,
) -> RunResult[RetrievalState]:
    """Walk the chain until a rung admits material, the user is asked, or it ends.

    Stops at the FIRST rung that returns pointable material: the chain is
    ordered by authority, so a lower rung is consulted only because every
    higher one missed. A run that ends with empty context and no outstanding
    question is the explicit abstention -- and its trace carries one UNKNOWN
    per rung saying exactly where the need went unanswered.
    """

    if state.pending is None:
        raise ValueError("the miss chain requires a pending UNKNOWN")
    actions = miss_chain_actions(
        state.pending.suggested_key, state.pending.slot, rungs
    )
    # One step beyond the ladder so an unanswered need stops as EXHAUSTED --
    # "every registered rung was tried and none answered" -- rather than as
    # BUDGET, which would wrongly suggest an untried rung remained.
    return Controller[RetrievalState](max_steps=len(actions) + 1).run(
        state,
        SequencePolicy(actions),
        verifier,
        is_complete=lambda current: bool(current.context),
        is_waiting=lambda current: current.awaiting is not None,
    )


def demo(
    repo_root: Path,
    key: str,
    wordnet_path: Path | None = None,
    observations_dir: Path | None = None,
    chain: bool = False,
) -> int:
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
    sources: tuple[ObservationSource, ...] = ()
    if observations_dir is not None:
        sources = (LocalObservationAdapter(observations_dir),)
    store = UnifiedKnowledgeStore.load(
        repo_root / "data", repo_root / "reports", wordnet_path, sources
    )
    verifier = RetrievalVerifier(store, executor)
    for probe in store.probe_sources():
        # Liveness chrome, never a verdict: see DESIGN-interactive-harness §3.2.
        status = "OK " if probe.available else "OFF"
        print(f"[{status}] {probe.source_id}: {probe.detail}")
    if chain:
        run = run_miss_chain(verifier, state)
    else:
        run = Controller[RetrievalState](max_steps=2).run(
            state,
            SequencePolicy((retrieval_action(key), point_action(0))),
            verifier,
            lambda current: current.pending is None,
        )
    for entry in run.trace:
        rung = entry.action.argument("rung")
        label = entry.action.kind.value + (f"({rung})" if rung else "")
        print(
            f"{label}: {entry.verification.verdict.value} — "
            f"{entry.verification.reason}"
        )
    for material in run.final_state.context:
        print(
            f"[{material.position}] {material.item.source}: "
            f"{material.item.title} ({material.item.epistemic_status})"
        )
    print(f"bindings: {run.final_state.bindings}")
    if chain:
        if run.final_state.context:
            return 0
        print(f"ABSTAIN: no registered rung answered {key!r}")
        return 1
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
    parser.add_argument(
        "--observations",
        type=Path,
        help="optional directory of external JSON observation files",
    )
    parser.add_argument(
        "--chain",
        action="store_true",
        help="walk the full miss chain instead of the composed lookup",
    )
    args = parser.parse_args()
    return demo(
        Path(__file__).resolve().parent.parent,
        args.key,
        args.wordnet,
        args.observations,
        args.chain,
    )


if __name__ == "__main__":
    raise SystemExit(main())
