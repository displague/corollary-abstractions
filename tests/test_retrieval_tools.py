"""Registered predictions for ROADMAP-v0.7 item 6 (retrieval becomes tool use).

Registered BEFORE the implementation ran, per AGENTS.md working method 2.
Each prediction names its own miss condition; fired and missed are both
reportable, and the adjudication is recorded in the delivering commit.

**P-RT1 — The typed-protocol migration is behaviour-preserving.**
Replacing ``RetrievalNeed.resolution_channel``'s validated string with a
``Channel`` Enum, and ``Controller``'s ``getattr(verifier, "commit_run")``
with a ``runtime_checkable`` ``RunCommitter`` protocol, changes no observable
behaviour. Prediction: every existing test in ``tests/test_retrieval.py``,
``tests/test_ask.py``, ``tests/test_conversation_runtime.py``,
``tests/test_controller.py`` and ``tests/test_wordnet_retrieval.py`` passes
**unmodified**, including the receipt, forgery, replay and supersession
cases. *Miss* if any existing test file needs an edit to stay green.

**P-RT2 — The miss chain's rung order is observable in the trace.**
For a key that misses exact and neighborhood but is reachable through a
committed specialization/decomposition edge, the controller trace shows one
entry per attempted rung, in the order ``exact → neighborhood → derivation``,
each carrying its own outcome verdict, and the accepted entry is the
derivation rung. *Miss* if a rung is skipped, reordered, or if the chain
resolves without recording the rungs it walked past.

**P-RT3 — Ranked neighborhood announces its score and its cap.**
Neighborhood results are ordered by a closed-form token-overlap score in
[0, 1] (mean of query coverage, alias coverage, and exact-token share; 1.0
iff the query and alias token sets are equal), ties broken by the existing
deterministic (source, item_id) order. Prediction: the top-ranked
neighborhood item for a truncated statement id is that statement's own
corpus record; a truncated neighborhood announces the drop count **and** the
lowest admitted score; and no existing POINT outcome changes because of the
reordering. *Miss* if ranking flips any existing binding verdict.

**P-RT4 — Sense ambiguity survives relation traversal.** *(Hardest case,
named in advance: ``quickening``.)* ``quickening`` has three senses; only
``00331283-n`` shares members with ``acceleration``. Its hypernym is
``00330000-n`` = "change" — a common word whose lemma would alias many
corpus records. A traversal that flattened senses would therefore bridge
``quickening → change → several corpus statements`` and offer a POINT.
Prediction: hypernym/antonym/entailment traversal returns **per-sense**
records that name their originating synset and hop count, every one of them
stays ``empirical``, and **none of them is ever bindable** — a relation
record is WordNet's claim about a sense, not an answer to the key. *Miss* if
any relation-derived record binds a slot, if two senses are merged into one
record, or if a traversal record's status exceeds ``empirical``.

**P-RT5 — A tool transaction proves what was fetched, not that it is true.**
The local-filesystem observation adapter retains, per observation, its
source id, its declared record timestamp, the fetch timestamp, the exact
query that fetched it, and its epistemic rung. Prediction: an observation
file declaring a rung above the external ceiling (anything other than
``conjectured``/``empirical``) is refused at load with the file named; an
admitted observation's rung is unchanged by ranking, by neighbouring formal
corpus material, or by the receipt that authorised it. *Miss* if any
adapter-sourced record reaches a rung above ``empirical``.

**P-RT6 — Session pruning evidence is reusable and cannot poison a retry.**
REFUTED and exhausted (UNKNOWN/ABSTAIN) branches from a *returned* run are
recorded on the verifier at session scope, keyed by
``(session_id, verifier state_key, action fingerprint)``. Prediction: a
second run in the same session re-proposing the identical triple is pruned
with the original reason cited; the same action in the same session from a
**different** state is re-evaluated normally; and a different session is
never pruned. *Miss* if pruning refuses a branch that would otherwise have
been VERIFIED, or if a speculative (uncommitted) evaluation writes evidence.

---

**RE-ADJUDICATION (P-RT6): MISSED, then repaired.** The prediction texts
above are kept exactly as registered; this note is appended, not edited in.

The delivering commit recorded P-RT6 as FIRED. That was wrong, and wrong
against the prediction's *own* stated miss condition — "pruning refuses a
branch that would otherwise have been VERIFIED" — which had already fired.
``RetrievalVerifier.state_key`` delegated its frame half to
``FrameAssertionVerifier.state_key``, which keys on the frame's **name** and
omits ``declarations``, ``suspends`` and ``owner``. Two same-named frames
with contradictory premises therefore shared a pruning key, and a REFUTED
dead end in one returned REFUSED for the other, whose branch was VERIFIED
when evaluated fresh. In belief frames that is Sally's dead end refusing
Anne's branch and citing Sally's premise as the reason.

What made the mis-adjudication possible is worth as much as the bug: the
three cases the commit *did* check (a second hop, another session, an
advanced state) are all cases where the state key is meant to differ or
match, and none of them constructs two states that must NOT share a key.
Confirming a cache's hits is not testing a cache; the miss condition was
about its collisions, and no probe went there.

Now MISSED-then-repaired: ``repr(state.frame.spec)`` joins the key (the same
frame scope receipts are signed against), and the two collision cases are
regressions below —
``SessionPruningTests::test_same_named_frames_with_contradictory_premises_do_not_share_a_prune``
and ``::test_same_named_belief_frames_of_different_owners_do_not_share_a_prune``.
The other three clauses of P-RT6 stand as originally adjudicated.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from zipfile import ZipFile


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from controller import (  # noqa: E402
    Action,
    ActionKind,
    Controller,
    RunCommitter,
    SequencePolicy,
    StopReason,
    Verdict,
    Verification,
)
from frames import (  # noqa: E402
    FrameAssertionVerifier,
    FrameExecutor,
    FrameSpec,
    Literal,
)
from observation_adapter import (  # noqa: E402
    EXTERNAL_RUNG_CEILING,
    LocalObservationAdapter,
    ObservationSource,
)
from retrieval import (  # noqa: E402
    MISS_CHAIN,
    Channel,
    QueryResult,
    RetrievalItem,
    RetrievalState,
    RetrievalVerifier,
    Rung,
    UnifiedKnowledgeStore,
    ask_action,
    item_match_mode,
    item_score,
    miss_chain_actions,
    point_action,
    retrieval_action,
    run_miss_chain,
)
from text_keys import overlap_score  # noqa: E402
from wordnet_store import WordNetIndex  # noqa: E402


#: A key with exactly one committed specialization edge and no exact or
#: neighborhood match anywhere on the query surface: the miss chain has to
#: walk to the derivation rung to answer it.
DERIVATION_KEY = "ALWAYS(IMPLIES(PLANTED(ELEMENT), EVENTUALLY(DISCHARGED(ELEMENT))))"
DERIVATION_ITEM = (
    "derivation:specialization:temporal.response.response_pattern"
    "->narrative.constraint.chekhov_gun"
)
FROZEN_CLOCK = "2026-08-09T12:00:00+00:00"


def corpus_item(
    item_id: str,
    aliases: tuple[str, ...],
    status: str = "derived",
    source: str = "corpus",
) -> RetrievalItem:
    return RetrievalItem(
        item_id=f"{source}:{item_id}",
        source=source,
        title=item_id,
        text=f"synthetic record {item_id}",
        epistemic_status=status,
        source_ids=(item_id,),
        aliases=aliases,
    )


def open_state(
    executor: FrameExecutor,
    key: str,
    *,
    slot: str = "answer",
    channel: Channel | str = Channel.STORE,
    retrieval: str = "open",
    frame_name: str = "runtime.frames.item6_tests",
) -> RetrievalState:
    frame = executor.open_frame(FrameSpec(frame=frame_name, retrieval=retrieval))
    return RetrievalState.from_unknown(
        executor,
        frame,
        slot,
        key,
        Literal("request", "needs", key),
        resolution_channel=channel,
    )


class ScoreDefinitionTests(unittest.TestCase):
    """P-RT3: the score is closed form, bounded, and recomputable."""

    def test_identical_token_sets_score_exactly_one(self) -> None:
        self.assertEqual(overlap_score("de morgan laws", "Laws, de Morgan!"), 1.0)
        self.assertEqual(overlap_score("a b", "b a"), 1.0)

    def test_tokenless_side_scores_zero_rather_than_dividing_by_zero(self) -> None:
        self.assertEqual(overlap_score("", "anything"), 0.0)
        self.assertEqual(overlap_score("¬", "negation"), 0.0)

    def test_score_is_bounded_and_monotone_in_alias_tightness(self) -> None:
        tight = overlap_score("boolean absorption", "boolean absorption")
        loose = overlap_score(
            "boolean absorption", "boolean absorption laws of lattice theory"
        )
        self.assertEqual(tight, 1.0)
        self.assertLess(loose, tight)
        self.assertGreater(loose, 0.0)

    def test_prefix_credit_scores_below_equality(self) -> None:
        exact = overlap_score("absorption", "absorption")
        prefix = overlap_score("absor", "absorption")
        self.assertGreater(exact, prefix)
        self.assertGreater(prefix, 0.0)

    def test_item_score_takes_the_best_alias(self) -> None:
        item = corpus_item("x.y", ("unrelated title", "boolean absorption"))
        self.assertEqual(item_score(item, "boolean absorption"), 1.0)


class RankedNeighborhoodTests(unittest.TestCase):
    """P-RT3: neighborhood results are ranked, capped, and both are announced."""

    def setUp(self) -> None:
        self.executor = FrameExecutor()

    def test_neighborhood_orders_by_score_then_by_store_order(self) -> None:
        tight = corpus_item("tight", ("boolean absorption",))
        loose = corpus_item("loose", ("boolean absorption laws of lattice theory",))
        store = UnifiedKnowledgeStore((tight, loose))
        result = store.attempt(Rung.NEIGHBORHOOD, "boolean absor")
        self.assertEqual(
            [item.item_id for item in result.items],
            ["corpus:tight", "corpus:loose"],
        )
        self.assertEqual(len(result.scores), 2)
        self.assertGreater(result.scores[0], result.scores[1])
        self.assertTrue(result.ranked)

    def test_equal_scores_keep_the_pre_ranking_source_order(self) -> None:
        items = (
            corpus_item("z.statement", ("boolean absorption",)),
            corpus_item("a.statement", ("boolean absorption",), source="lexicon"),
        )
        store = UnifiedKnowledgeStore(items)
        result = store.attempt(Rung.NEIGHBORHOOD, "boolean absor")
        self.assertEqual(len(set(result.scores)), 1)
        self.assertEqual(
            [item.item_id for item in result.items],
            ["corpus:z.statement", "lexicon:a.statement"],
        )

    def test_truncated_neighborhood_announces_count_cap_and_cut_score(self) -> None:
        items = tuple(
            corpus_item(f"s{index:03d}", (f"boolean absorption variant {index}",))
            for index in range(40)
        )
        store = UnifiedKnowledgeStore(items)
        state = open_state(self.executor, "boolean absorption")
        verifier = RetrievalVerifier(store, self.executor)
        outcome = verifier.evaluate(
            state, retrieval_action("boolean absorption", Rung.NEIGHBORHOOD)
        )
        self.assertIs(outcome.verdict, Verdict.VERIFIED)
        self.assertIn("ranked by", outcome.reason)
        self.assertIn("at cap 24", outcome.reason)
        self.assertIn("16 further matches", outcome.reason)
        self.assertIn("deterministically truncated", outcome.reason)
        self.assertIn("below score", outcome.reason)

    def test_exact_mode_declares_itself_unranked(self) -> None:
        store = UnifiedKnowledgeStore.load(REPO_ROOT / "data", REPO_ROOT / "reports")
        result = store.query("equality")
        self.assertEqual(result.mode, "exact")
        self.assertFalse(result.ranked)
        self.assertEqual(result.scores, ())
        self.assertGreater(result.truncated, 0)

    def test_ranking_moves_no_record_off_its_epistemic_rung(self) -> None:
        weak = corpus_item("weak", ("boolean absorption",), status="conjectured")
        strong = corpus_item(
            "strong",
            ("boolean absorption laws of lattice theory",),
            status="formal",
        )
        store = UnifiedKnowledgeStore((weak, strong))
        result = store.attempt(Rung.NEIGHBORHOOD, "boolean absor")
        statuses = {item.item_id: item.epistemic_status for item in result.items}
        # The top-ranked record is the WEAK one; ranking is relevance, and
        # relevance is not authority.
        self.assertEqual(result.items[0].item_id, "corpus:weak")
        self.assertEqual(statuses["corpus:weak"], "conjectured")
        self.assertEqual(statuses["corpus:strong"], "formal")


def write_polysemy_fixture(path: Path) -> None:
    """Two senses of one lemma, each with its own registered relations.

    ``quickening`` is P-RT4's named hard case. Sense ``a-n`` shares members
    with ``acceleration`` and hypernyms to the very common lemma ``change``;
    sense ``b-n`` is the obstetric sense and entails ``live``. Both senses
    hypernym to ``change``, so a traversal that flattened senses would merge
    two unrelated neighbourhoods into one bridge.
    """

    entries = {
        "quickening": {
            "n": {
                "sense": [
                    {"id": "quickening%1:04:00::", "synset": "a-n"},
                    {"id": "quickening%1:22:00::", "synset": "b-n"},
                ]
            }
        }
    }
    synsets = {
        "a-n": {
            "definition": ["the act of increasing speed"],
            "members": ["acceleration", "quickening"],
            "partOfSpeech": "n",
            "hypernym": ["change-n"],
            "antonym": ["deceleration-n"],
        },
        "b-n": {
            "definition": ["the first motion of a fetus"],
            "members": ["quickening"],
            "partOfSpeech": "n",
            "entailment": ["live-n"],
            "hypernym": ["change-n"],
        },
        "change-n": {
            "definition": ["an event that occurs when something passes"],
            "members": ["change"],
            "partOfSpeech": "n",
        },
        "deceleration-n": {
            "definition": ["a decrease in speed"],
            "members": ["deceleration"],
            "partOfSpeech": "n",
        },
        "live-n": {
            "definition": ["being alive"],
            "members": ["live"],
            "partOfSpeech": "n",
        },
        "dangling-n": {
            "definition": ["never referenced"],
            "members": ["dangling"],
            "partOfSpeech": "n",
        },
    }
    with ZipFile(path, "w") as archive:
        archive.writestr("entries-q.json", json.dumps(entries))
        archive.writestr("noun.act.json", json.dumps(synsets))


class WordNetRelationTests(unittest.TestCase):
    """P-RT4: relations are walkable without flattening sense ambiguity."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.archive = Path(self.temp.name) / "oewn.zip"
        write_polysemy_fixture(self.archive)
        self.index = WordNetIndex.load(self.archive)
        self.executor = FrameExecutor()

    def store(self, *items: RetrievalItem) -> UnifiedKnowledgeStore:
        return UnifiedKnowledgeStore(items, self.index)

    def test_every_sense_keeps_its_own_relation_records(self) -> None:
        records = self.store().relation_records("quickening")
        origins = {item.item_id.split(":")[1] for item in records}
        self.assertEqual(origins, {"a-n", "b-n"})
        relations = {item.item_id.split(":")[2] for item in records}
        self.assertEqual(relations, {"antonym", "entailment", "hypernym"})
        # The hard part of P-RT4: BOTH senses hypernym to "change", and the
        # two walks stay two records rather than collapsing into one.
        to_change = [item for item in records if item.item_id.endswith("change-n")]
        self.assertEqual(len(to_change), 2)
        self.assertEqual(
            {item.item_id.split(":")[1] for item in to_change}, {"a-n", "b-n"}
        )

    def test_relation_records_never_leave_empirical(self) -> None:
        formal = corpus_item("physics.change", ("change",), status="formal")
        records = self.store(formal).relation_records("quickening")
        self.assertTrue(records)
        for item in records:
            self.assertEqual(item.epistemic_status, "empirical", item.item_id)

    def test_no_relation_record_can_ever_bind_a_slot(self) -> None:
        """The named laundering path: quickening -> change -> a corpus answer."""

        formal = corpus_item("physics.change", ("change",), status="formal")
        store = self.store(formal)
        records = store.relation_records("quickening")
        hypernyms = [item for item in records if ":hypernym:" in item.item_id]
        self.assertTrue(hypernyms)
        for item in records:
            self.assertIsNone(
                store.binding_match_mode(item, "quickening"), item.item_id
            )

        state = open_state(self.executor, "quickening")
        verifier = RetrievalVerifier(store, self.executor)
        retrieved = verifier.evaluate(
            state, retrieval_action("quickening", Rung.TOOL)
        )
        self.assertIs(retrieved.verdict, Verdict.VERIFIED)
        assert retrieved.next_state is not None
        pointed_any = False
        for material in retrieved.next_state.context:
            if material.item.source != "wordnet_relation":
                continue
            pointed_any = True
            outcome = verifier.evaluate(
                retrieved.next_state, point_action(material.position)
            )
            self.assertIs(outcome.verdict, Verdict.REFUSED, material.item.item_id)
            self.assertIn("key constraint", outcome.reason)
        self.assertTrue(pointed_any)

    def test_unregistered_relation_names_are_refused_not_walked(self) -> None:
        with self.assertRaisesRegex(ValueError, "unregistered WordNet relations"):
            self.store().relation_records("quickening", ("meronym",))

    def test_forged_relation_edge_fails_containment(self) -> None:
        store = self.store()
        real = next(
            item
            for item in store.relation_records("quickening")
            if item.item_id == "wordnet_relation:b-n:entailment:live-n"
        )
        self.assertTrue(store.contains_item(real))
        # Both senses exist and the relation name is registered, but this edge
        # is not in the archive.
        forged = replace(real, item_id="wordnet_relation:b-n:antonym:deceleration-n")
        self.assertFalse(store.contains_item(forged))
        # Real edge, tampered payload.
        self.assertFalse(
            store.contains_item(replace(real, epistemic_status="formal"))
        )

    def test_dangling_targets_are_skipped_not_invented(self) -> None:
        records = self.store().relation_records("quickening")
        self.assertNotIn(
            "dangling-n", {item.item_id.split(":")[-1] for item in records}
        )

    def test_tool_rung_orders_project_material_before_outside_material(self) -> None:
        """The intra-transaction authority order, with real outside material.

        Rewritten after external review: the original registered **no**
        observation source, so "before outside material" asserted a property
        of an empty tail. A test whose subject is absent cannot fail, and
        this one was guarding the ordering claim that the POINT-time
        outranking rule is built on.
        """

        outside = Path(self.temp.name) / "observations"
        outside.mkdir()
        (outside / "note.json").write_text(
            json.dumps(
                {
                    "observation_id": "note.outside",
                    "title": "Somebody's note on quickening",
                    "text": "An outside remark.",
                    "keywords": ["quickening"],
                    "recorded_at": "2026-07-01T00:00:00+00:00",
                    "epistemic_rung": "conjectured",
                }
            ),
            encoding="utf-8",
        )
        adapter = LocalObservationAdapter(outside, clock=lambda: FROZEN_CLOCK)
        bridged = corpus_item(
            "physics.acceleration", ("acceleration",), status="proven"
        )
        store = UnifiedKnowledgeStore((bridged,), self.index, (), (adapter,))
        result = store.attempt(Rung.TOOL, "quickening")
        sources = [item.source for item in result.items]

        # Authority order, not score order: bridged project material, then
        # the senses that bridged it, then the walked edges, then outside.
        self.assertEqual(sources[0], "corpus")
        self.assertEqual(sources[1:3], ["wordnet", "wordnet"])
        self.assertEqual(sources[-1], "observation")
        self.assertTrue(
            all(source == "wordnet_relation" for source in sources[3:-1])
        )
        self.assertGreater(sources.count("wordnet_relation"), 0)
        # Every rung keeps the status it entered with; ordering is not
        # promotion and proximity is not authority.
        self.assertEqual(
            [item.epistemic_status for item in result.items],
            ["proven"] + ["empirical"] * (len(result.items) - 2) + ["conjectured"],
        )
        # And the order is an authority claim, enforced at POINT: the outside
        # record cannot answer the key its neighbours in this very
        # transaction already own.
        observation = result.items[-1]
        self.assertIsNone(store.binding_match_mode(observation, "quickening"))
        self.assertEqual(store.binding_match_mode(bridged, "quickening"), "synonym")


class ObservationAdapterTests(unittest.TestCase):
    """P-RT5: a tool transaction proves what was fetched, not that it is true."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "observations"
        self.root.mkdir()
        self.executor = FrameExecutor()

    def write(self, name: str, **payload: object) -> Path:
        record: dict[str, object] = {
            "observation_id": "note.tide_gauge",
            "title": "Tide gauge reading",
            "text": "Mean sea level rose 3 mm.",
            "keywords": ["tide", "gauge"],
            "recorded_at": "2026-07-01T00:00:00+00:00",
            "epistemic_rung": "empirical",
        }
        record.update(payload)
        path = self.root / name
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def adapter(self) -> LocalObservationAdapter:
        return LocalObservationAdapter(self.root, clock=lambda: FROZEN_CLOCK)

    def test_adapter_satisfies_the_typed_source_protocol(self) -> None:
        self.write("a.json")
        self.assertIsInstance(self.adapter(), ObservationSource)

    def test_observation_retains_source_timestamps_query_and_rung(self) -> None:
        self.write("a.json")
        store = UnifiedKnowledgeStore((), None, (), (self.adapter(),))
        records = store.observation_records("note.tide_gauge")
        self.assertEqual(len(records), 1)
        item = records[0]
        self.assertEqual(item.source, "observation")
        self.assertEqual(item.epistemic_status, "empirical")
        provenance = set(item.source_ids)
        self.assertIn("source:local.observations:observations", provenance)
        self.assertIn("recorded_at:2026-07-01T00:00:00+00:00", provenance)
        self.assertIn(f"fetched_at:{FROZEN_CLOCK}", provenance)
        self.assertIn("query:note.tide_gauge", provenance)
        self.assertIn("rung:empirical", provenance)
        self.assertTrue(any(part.startswith("sha256:") for part in provenance))

    def test_rung_above_the_external_ceiling_is_refused_at_load(self) -> None:
        self.write("a.json", epistemic_rung="formal")
        with self.assertRaisesRegex(ValueError, "may not exceed 'empirical'"):
            self.adapter()
        self.assertEqual(EXTERNAL_RUNG_CEILING, ("conjectured", "empirical"))

    def test_malformed_observation_names_its_file(self) -> None:
        (self.root / "broken.json").write_text("{not json", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid observation JSON"):
            self.adapter()

    def test_non_iso_timestamp_is_refused(self) -> None:
        self.write("a.json", recorded_at="last tuesday")
        with self.assertRaisesRegex(ValueError, "non-ISO-8601 recorded_at"):
            self.adapter()

    def test_recorded_at_in_the_future_is_refused_with_the_file_named(self) -> None:
        """A claim about the future is not a provenance this adapter witnessed."""

        path = self.write("a.json", recorded_at="2026-08-09T13:00:00+00:00")
        with self.assertRaisesRegex(ValueError, "in the future") as caught:
            self.adapter()
        self.assertIn(path.name, str(caught.exception))

    def test_small_clock_skew_is_tolerated_rather_than_refused(self) -> None:
        """Two honest machines disagree by seconds; that is not a forgery."""

        self.write("a.json", recorded_at="2026-08-09T12:00:30+00:00")
        self.assertEqual(self.adapter().probe().record_count, 1)

    def test_a_naive_timestamp_is_read_as_utc_not_as_local(self) -> None:
        self.write("a.json", recorded_at="2026-08-09T13:00:00")
        with self.assertRaisesRegex(ValueError, "in the future"):
            self.adapter()

    def test_uppercase_json_suffix_is_read_and_refused_not_ignored(self) -> None:
        """``root.glob("*.json")`` was case-sensitive on Linux only.

        The module's own rule is that a source silently dropping records is
        worse than an absent one, and a rule that means different things per
        platform is not a rule. A ``.JSON`` forgery must be refused loudly
        everywhere, so the suffix comparison replaces the glob.

        Stated so nobody mistakes it for stronger evidence than it is: on a
        case-INsensitive filesystem (Windows, default macOS) the old glob
        already matched this file, so the test is green either way there. It
        can only *fail* where the bug lived, which is the platform this fix
        is for. Running the suite on Linux is what actually adjudicates it.
        """

        (self.root / "forgery.JSON").write_text("{not json", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid observation JSON"):
            self.adapter()

    def test_a_wellformed_uppercase_file_is_admitted_on_every_platform(self) -> None:
        self.write("a.JSON")
        self.assertEqual(self.adapter().probe().record_count, 1)
        (record,) = self.adapter().fetch("note.tide_gauge")
        self.assertEqual(record.location, "a.JSON")

    def test_absent_root_probes_off_and_fetches_nothing(self) -> None:
        adapter = LocalObservationAdapter(self.root / "missing")
        probe = adapter.probe()
        self.assertFalse(probe.available)
        self.assertIn("not a directory", probe.detail)
        self.assertEqual(adapter.fetch("note.tide_gauge"), ())

    def test_probe_is_liveness_and_carries_no_rung(self) -> None:
        self.write("a.json")
        store = UnifiedKnowledgeStore((), None, (), (self.adapter(),))
        (probe,) = store.probe_sources()
        self.assertTrue(probe.available)
        self.assertEqual(probe.record_count, 1)
        self.assertFalse(hasattr(probe, "epistemic_status"))

    def test_observation_cannot_launder_beside_formal_corpus_material(self) -> None:
        self.write("a.json", keywords=["tide", "gauge", "quadratic"])
        formal = corpus_item("algebra.quadratic", ("quadratic",), status="formal")
        store = UnifiedKnowledgeStore((formal,), None, (), (self.adapter(),))
        result = store.attempt(Rung.TOOL, "quadratic")
        statuses = {item.source: item.epistemic_status for item in result.items}
        self.assertEqual(statuses["observation"], "empirical")
        observation = next(
            item for item in result.items if item.source == "observation"
        )
        self.assertFalse(
            store.contains_item(replace(observation, epistemic_status="formal"))
        )

    def test_observation_binds_only_for_the_query_that_fetched_it(self) -> None:
        self.write("a.json")
        store = UnifiedKnowledgeStore((), None, (), (self.adapter(),))
        (item,) = store.observation_records("note.tide_gauge")
        self.assertEqual(
            store.binding_match_mode(item, "note.tide_gauge"), "observation"
        )
        # The same record re-aimed at a question it was never asked.
        self.assertIsNone(store.binding_match_mode(item, "tide gauge"))

    def test_outside_record_cannot_answer_a_slot_a_committed_record_owns(self) -> None:
        """Self-review finding: an honest rung label is not enough.

        An observation file whose ``observation_id`` impersonates a committed
        statement id used to bind that statement's slot when the tool rung was
        invoked directly. The record never claimed a rung above ``empirical``
        -- what it usurped was the *authority to answer*. The chain would have
        stopped at the exact rung, but the verifier may not assume the policy
        walked the ladder in order, so the outranking test lives at POINT.
        """

        self.write("a.json", observation_id="logic.owned", keywords=["owned"])
        owned = corpus_item("logic.owned", ("logic.owned",), status="derived")
        store = UnifiedKnowledgeStore((owned,), None, (), (self.adapter(),))
        (outside,) = store.observation_records("logic.owned")
        self.assertEqual(outside.epistemic_status, "empirical")
        self.assertIsNone(store.binding_match_mode(outside, "logic.owned"))

        state = open_state(self.executor, "logic.owned")
        verifier = RetrievalVerifier(store, self.executor)
        retrieved = verifier.evaluate(
            state, retrieval_action("logic.owned", Rung.TOOL)
        )
        self.assertIs(retrieved.verdict, Verdict.VERIFIED)
        assert retrieved.next_state is not None
        pointed = verifier.evaluate(retrieved.next_state, point_action(0))
        self.assertIs(pointed.verdict, Verdict.REFUSED)
        self.assertIn("key constraint", pointed.reason)

    def test_outside_record_still_binds_a_key_nothing_committed_owns(self) -> None:
        self.write("a.json", observation_id="note.unowned", keywords=["unowned"])
        owned = corpus_item("logic.other", ("logic.other",))
        store = UnifiedKnowledgeStore((owned,), None, (), (self.adapter(),))
        (outside,) = store.observation_records("note.unowned")
        self.assertEqual(
            store.binding_match_mode(outside, "note.unowned"), "observation"
        )

    def test_ambiguous_external_answer_cannot_bind(self) -> None:
        self.write("a.json", observation_id="note.one", keywords=["tide"])
        self.write("b.json", observation_id="note.two", keywords=["tide"])
        store = UnifiedKnowledgeStore((), None, (), (self.adapter(),))
        records = store.observation_records("tide")
        self.assertEqual(len(records), 2)
        for item in records:
            self.assertIsNone(store.binding_match_mode(item, "tide"))

    def test_unminted_observation_is_not_in_the_store(self) -> None:
        self.write("a.json")
        store = UnifiedKnowledgeStore((), None, (), (self.adapter(),))
        (item,) = store.observation_records("note.tide_gauge")
        fresh = UnifiedKnowledgeStore((), None, (), (self.adapter(),))
        self.assertTrue(store.contains_item(item))
        self.assertFalse(fresh.contains_item(item))

    def test_tool_rung_admits_an_observation_and_point_binds_it(self) -> None:
        self.write("a.json")
        store = UnifiedKnowledgeStore((), None, (), (self.adapter(),))
        state = open_state(self.executor, "note.tide_gauge")
        verifier = RetrievalVerifier(store, self.executor)
        retrieved = verifier.evaluate(
            state, retrieval_action("note.tide_gauge", Rung.TOOL)
        )
        self.assertIs(retrieved.verdict, Verdict.VERIFIED)
        assert retrieved.next_state is not None
        item = retrieved.next_state.context[0].item
        self.assertEqual(item.epistemic_status, "empirical")
        pointed = verifier.evaluate(retrieved.next_state, point_action(0))
        self.assertIs(pointed.verdict, Verdict.VERIFIED)
        assert pointed.next_state is not None
        self.assertTrue(pointed.next_state.bindings[-1][1].startswith("observation:"))


class ObservationAuthorityDoorTests(unittest.TestCase):
    """One test per door into the slot an outside record may not answer.

    External review's second blocking finding: the first authority fix
    covered one door. ``_observation_binding_match_mode``'s outranking test
    consulted ``item_match_mode`` over ``items + derivations`` only, which
    sees a key's *literal* reach. The WordNet synonym bridge reaches
    committed records through shared synset members, which no alias
    comparison can see, so with an archive loaded a single TOOL transaction
    emitted ``[corpus:proven, wordnet:empirical, observation:conjectured]``
    for one key and POINT bound **any** of the three.

    The lesson is that the author's own fix was the unprobed boundary, so
    the doors are now enumerated and each has its own regression:

    1. ``observation_id`` impersonating a committed statement id —
       ``ObservationAdapterTests::
       test_outside_record_cannot_answer_a_slot_a_committed_record_owns``
       (the original finding; kept where it was written).
    2. an **alias** of a committed record — below.
    3. a **twin_ledger** group record — below.
    4. the **WordNet synonym bridge** — below; this is the one that was open.
    5. an ``observation_id`` impersonating a loaded **synset id** — below;
       also open, because a synset id is not a lemma and so the bridge in
       (4) cannot see it either.
    """

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "observations"
        self.root.mkdir()
        self.executor = FrameExecutor()

    def write(self, name: str, **payload: object) -> None:
        record: dict[str, object] = {
            "observation_id": "note.outside",
            "title": "Somebody's note",
            "text": "An outside remark.",
            "keywords": [],
            "recorded_at": "2026-07-01T00:00:00+00:00",
            "epistemic_rung": "conjectured",
        }
        record.update(payload)
        (self.root / name).write_text(json.dumps(record), encoding="utf-8")

    def adapter(self) -> LocalObservationAdapter:
        return LocalObservationAdapter(self.root, clock=lambda: FROZEN_CLOCK)

    def wordnet(self) -> WordNetIndex:
        archive = Path(self.temp.name) / "oewn.zip"
        write_polysemy_fixture(archive)
        return WordNetIndex.load(archive)

    def assert_refused_and_pointing_refused(
        self, store: UnifiedKnowledgeStore, key: str
    ) -> RetrievalItem:
        """The record is admitted as context and refused as an answer."""

        (outside,) = store.observation_records(key)
        self.assertIn(outside.epistemic_status, EXTERNAL_RUNG_CEILING)
        self.assertIsNone(store.binding_match_mode(outside, key))

        state = open_state(self.executor, key)
        verifier = RetrievalVerifier(store, self.executor)
        retrieved = verifier.evaluate(state, retrieval_action(key, Rung.TOOL))
        self.assertIs(retrieved.verdict, Verdict.VERIFIED)
        assert retrieved.next_state is not None
        position = next(
            material.position
            for material in retrieved.next_state.context
            if material.item.item_id == outside.item_id
        )
        pointed = verifier.evaluate(retrieved.next_state, point_action(position))
        self.assertIs(pointed.verdict, Verdict.REFUSED)
        self.assertIn("key constraint", pointed.reason)
        return outside

    def test_alias_door_an_outside_note_cannot_answer_a_committed_alias(self) -> None:
        """Door 2: the key reaches a committed record by ALIAS, not by id."""

        self.write("a.json", keywords=["harmonic mean"])
        owned = corpus_item("stats.central_tendency", ("harmonic mean",))
        store = UnifiedKnowledgeStore((owned,), None, (), (self.adapter(),))
        self.assertEqual(
            store.binding_match_mode(owned, "harmonic mean"), "exact"
        )
        self.assert_refused_and_pointing_refused(store, "harmonic mean")

    def test_twin_ledger_door_an_outside_note_cannot_answer_a_group(self) -> None:
        """Door 3: the owner of the key is a structural twin group."""

        self.write("a.json", keywords=["absorption pair"])
        group = corpus_item(
            "twin.absorption", ("absorption pair",), source="twin_ledger"
        )
        store = UnifiedKnowledgeStore((group,), None, (), (self.adapter(),))
        self.assertEqual(
            store.binding_match_mode(group, "absorption pair"), "exact"
        )
        self.assert_refused_and_pointing_refused(store, "absorption pair")

    def test_wordnet_bridge_door_is_the_one_the_first_fix_left_open(self) -> None:
        """Door 4: reached through shared synset members, invisible to aliases.

        ``quickening`` shares sense ``a-n`` with ``acceleration``, so the
        committed statement aliased ``acceleration`` answers the key through
        the bridge — while ``item_match_mode(owned, "quickening")`` is
        ``None``, which is exactly why the alias-only outranking test let the
        outside note through. The transaction really does emit a proven
        statement and a conjectured note under one key.
        """

        self.write("a.json", keywords=["quickening"])
        owned = corpus_item("physics.acceleration", ("acceleration",), status="proven")
        store = UnifiedKnowledgeStore(
            (owned,), self.wordnet(), (), (self.adapter(),)
        )
        # The door: no literal alias reach, but a real bridged owner.
        self.assertIsNone(item_match_mode(owned, "quickening"))
        self.assertEqual(store.binding_match_mode(owned, "quickening"), "synonym")

        result = store.attempt(Rung.TOOL, "quickening")
        statuses = [
            (item.source, item.epistemic_status)
            for item in result.items
            if item.source in {"corpus", "observation"}
        ]
        self.assertEqual(
            statuses, [("corpus", "proven"), ("observation", "conjectured")]
        )
        self.assert_refused_and_pointing_refused(store, "quickening")

    def test_lexical_only_reach_still_outranks_an_outside_note(self) -> None:
        """Door 4, no committed owner: the senses themselves still outrank.

        Reachability outranks, not bindability. ``quickening`` reaches two
        senses and binds neither; the honest reading is that the key's answer
        is unresolved, not that it is available to outside material.
        """

        self.write("a.json", keywords=["quickening"])
        store = UnifiedKnowledgeStore((), self.wordnet(), (), (self.adapter(),))
        bridged, lexical = store._wordnet_resolution("quickening")
        self.assertEqual(bridged, ())
        self.assertEqual(len(lexical), 2)
        self.assert_refused_and_pointing_refused(store, "quickening")

    def test_synset_id_impersonation_door(self) -> None:
        """Door 5: the record's own id names a loaded sense.

        A synset id is not a lemma, so ``a-n`` reaches nothing through the
        bridge and looked like a key nobody owned. Refused at the binding
        boundary rather than raised at mint time: the RETRIEVE that mints it
        is an action the verifier must be able to *answer*.
        """

        self.write("a.json", observation_id="a-n", keywords=[])
        store = UnifiedKnowledgeStore((), self.wordnet(), (), (self.adapter(),))
        (impostor,) = store.observation_records("a-n")
        self.assertEqual(store._wordnet_resolution("a-n"), ((), ()))
        self.assert_refused_and_pointing_refused(store, "a-n")
        # And the honest form of the same record, under a name it may own,
        # still binds — the refusal is about impersonation, not about the file.
        self.write("a.json", observation_id="note.a_n", keywords=[])
        honest = UnifiedKnowledgeStore((), self.wordnet(), (), (self.adapter(),))
        (record,) = honest.observation_records("note.a_n")
        self.assertEqual(
            honest.binding_match_mode(record, "note.a_n"), "observation"
        )
        self.assertNotEqual(impostor.item_id, record.item_id)


class MissChainTests(unittest.TestCase):
    """P-RT2: every rung's attempt and outcome is in the trace, in order."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.store = UnifiedKnowledgeStore.load(
            REPO_ROOT / "data", REPO_ROOT / "reports"
        )

    def setUp(self) -> None:
        self.executor = FrameExecutor()
        self.verifier = RetrievalVerifier(self.store, self.executor)

    def test_chain_order_is_exact_neighborhood_derivation_tool_ask(self) -> None:
        self.assertEqual(
            [rung.value for rung in MISS_CHAIN],
            ["exact", "neighborhood", "derivation", "tool"],
        )
        actions = miss_chain_actions("k", "slot")
        self.assertEqual(
            [action.argument("rung") for action in actions],
            ["exact", "neighborhood", "derivation", "tool", None],
        )
        self.assertIs(actions[-1].kind, ActionKind.ASK)

    def test_derivation_rung_answers_only_after_the_higher_rungs_miss(self) -> None:
        state = open_state(self.executor, DERIVATION_KEY)
        run = run_miss_chain(self.verifier, state)
        walked = [
            (entry.action.argument("rung"), entry.verification.verdict)
            for entry in run.trace
        ]
        self.assertEqual(
            walked,
            [
                ("exact", Verdict.UNKNOWN),
                ("neighborhood", Verdict.UNKNOWN),
                ("derivation", Verdict.VERIFIED),
            ],
        )
        self.assertIs(run.stop_reason, StopReason.SOLVED)
        self.assertEqual(
            [material.item.item_id for material in run.final_state.context],
            [DERIVATION_ITEM],
        )
        for entry in run.trace[:2]:
            self.assertIn("ABSTAIN", entry.verification.evidence)

    def test_derivation_material_binds_at_its_inherited_status(self) -> None:
        state = open_state(self.executor, DERIVATION_KEY)
        run = run_miss_chain(self.verifier, state)
        item = run.final_state.context[0].item
        self.assertEqual(item.source, "derivation")
        # Weakest-member inheritance, unchanged by the new rung.
        self.assertEqual(item.epistemic_status, "assumed")
        pointed = self.verifier.evaluate(run.final_state, point_action(0))
        self.assertIs(pointed.verdict, Verdict.VERIFIED)
        self.assertIn("derivation-matched", pointed.reason)

    def test_composed_query_still_misses_what_only_derivation_answers(self) -> None:
        """The derivation rung must not leak into the legacy query surface."""

        self.assertEqual(self.store.query(DERIVATION_KEY).mode, "miss")

    def test_exhausted_chain_ends_in_explicit_abstention(self) -> None:
        key = "zzqx nonexistent 998877"
        state = open_state(self.executor, key)
        run = run_miss_chain(self.verifier, state)
        self.assertEqual(
            [entry.action.argument("rung") for entry in run.trace],
            ["exact", "neighborhood", "derivation", "tool", None],
        )
        self.assertEqual(
            [entry.verification.verdict for entry in run.trace],
            [Verdict.UNKNOWN] * 4 + [Verdict.REFUSED],
        )
        self.assertIn(
            "assigned to the durable store", run.trace[-1].verification.reason
        )
        self.assertIs(run.stop_reason, StopReason.EXHAUSTED)
        self.assertEqual(run.final_state.context, ())
        self.assertIsNotNone(run.final_state.pending)

    def test_frame_private_need_walks_the_chain_to_ask(self) -> None:
        state = open_state(
            self.executor,
            "user preferred tone",
            slot="tone",
            channel=Channel.USER,
            frame_name="runtime.frames.item6_private",
        )
        run = run_miss_chain(self.verifier, state)
        self.assertEqual(
            [entry.verification.verdict for entry in run.trace],
            [Verdict.REFUSED] * 4 + [Verdict.VERIFIED],
        )
        for entry in run.trace[:4]:
            self.assertIn("user-private", entry.verification.reason)
            self.assertIn("ASK(tone)", entry.verification.evidence)
        self.assertIs(run.stop_reason, StopReason.WAITING)
        self.assertIsNotNone(run.final_state.awaiting)

    def test_unregistered_rung_name_is_refused(self) -> None:
        state = open_state(self.executor, DERIVATION_KEY)
        forged = Action.build(
            ActionKind.RETRIEVE,
            "lookup",
            {"key": DERIVATION_KEY, "rung": "vibes"},
        )
        outcome = self.verifier.evaluate(state, forged)
        self.assertIs(outcome.verdict, Verdict.REFUSED)
        self.assertIn("unregistered miss-chain rung", outcome.reason)

    def test_non_store_rung_names_are_refused_not_raised(self) -> None:
        """Review finding: ``Rung(raw)`` alone admitted ASK and ABSTAIN.

        Both are real chain members but neither is a store query, so the
        store raised out of ``evaluate`` instead of returning a verdict. A
        verifier must answer a crafted action, never crash on one.
        """

        state = open_state(self.executor, DERIVATION_KEY)
        for name in ("ask", "abstain"):
            with self.subTest(rung=name):
                forged = Action.build(
                    ActionKind.RETRIEVE,
                    "lookup",
                    {"key": DERIVATION_KEY, "rung": name},
                )
                outcome = self.verifier.evaluate(state, forged)
                self.assertIs(outcome.verdict, Verdict.REFUSED)
                self.assertIn("unregistered miss-chain rung", outcome.reason)
                self.assertIsNone(outcome.next_state)

    def test_store_without_a_rung_capability_refuses_not_improvises(self) -> None:
        class LegacyStore:
            def query(self, key: str, limit: int = 24) -> QueryResult:
                return QueryResult("miss", key)

            def binding_match_mode(self, item, key):
                return None

            def contains_item(self, item) -> bool:
                return False

        state = open_state(self.executor, DERIVATION_KEY)
        verifier = RetrievalVerifier(LegacyStore(), self.executor)
        outcome = verifier.evaluate(
            state, retrieval_action(DERIVATION_KEY, Rung.DERIVATION)
        )
        self.assertIs(outcome.verdict, Verdict.REFUSED)
        self.assertIn("registers no 'derivation' rung", outcome.reason)

    def test_legacy_retrieval_action_is_byte_identical(self) -> None:
        self.assertEqual(retrieval_action("k").arguments, (("key", "k"),))
        self.assertEqual(
            retrieval_action("k", Rung.EXACT).arguments,
            (("key", "k"), ("rung", "exact")),
        )


class SessionPruningTests(unittest.TestCase):
    """P-RT6: closed branches are reusable evidence, scoped to one session."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.store = UnifiedKnowledgeStore.load(
            REPO_ROOT / "data", REPO_ROOT / "reports"
        )

    def setUp(self) -> None:
        self.executor = FrameExecutor()
        self.verifier = RetrievalVerifier(self.store, self.executor)
        self.key = "zzqx nonexistent 998877"
        self.state = open_state(self.executor, self.key)

    def run_once(self, state: RetrievalState):
        return Controller[RetrievalState](max_steps=1).run(
            state,
            SequencePolicy((retrieval_action(self.key),)),
            self.verifier,
            lambda current: bool(current.context),
        )

    def test_exhausted_branch_is_pruned_on_a_later_run_in_the_session(self) -> None:
        first = self.run_once(self.state)
        self.assertIs(first.trace[0].verification.verdict, Verdict.UNKNOWN)
        evidence = self.verifier.session_pruning_evidence(self.state.session_id)
        self.assertEqual(len(evidence), 1)
        self.assertIs(evidence[0].verdict, Verdict.UNKNOWN)

        second = self.run_once(self.state)
        outcome = second.trace[0].verification
        self.assertIs(outcome.verdict, Verdict.REFUSED)
        self.assertIn("already closed in this session", outcome.reason)
        self.assertIn(Verdict.UNKNOWN.value, outcome.evidence)

    def test_a_second_dispatcher_hop_costs_no_store_queries(self) -> None:
        """The P-IH7 substrate, exercised across runs.

        ``docs/DESIGN-interactive-harness.md`` §3.1/§6.2: ``Controller.run``'s
        ``rejected`` set is run-local, so a multi-run dispatcher re-walked
        every dead rung at every hop. With session-scoped evidence the second
        hop refuses all four rungs from the ledger. This is the retrieval-side
        substrate only -- the session BUDGET and the ``(need, state_key)``
        cycle report that P-IH7 adjudicates are Phase-1/2 dispatcher work and
        are not claimed here.
        """

        state = open_state(self.executor, self.key)
        first = run_miss_chain(self.verifier, state)
        self.assertEqual(
            [entry.verification.verdict for entry in first.trace],
            [Verdict.UNKNOWN] * 4 + [Verdict.REFUSED],
        )
        second = run_miss_chain(self.verifier, first.final_state)
        self.assertEqual(
            [entry.verification.verdict for entry in second.trace],
            [Verdict.REFUSED] * 5,
        )
        for entry in second.trace[:4]:
            self.assertIn("already closed in this session", entry.verification.reason)
        self.assertIs(second.stop_reason, StopReason.EXHAUSTED)
        self.assertEqual(
            len(self.verifier.session_pruning_evidence(state.session_id)), 4
        )

    def test_speculative_evaluation_writes_no_evidence(self) -> None:
        outcome = self.verifier.evaluate(self.state, retrieval_action(self.key))
        self.assertIs(outcome.verdict, Verdict.UNKNOWN)
        self.assertEqual(
            self.verifier.session_pruning_evidence(self.state.session_id), ()
        )
        # And the branch stays open for a real run.
        run = self.run_once(self.state)
        self.assertIs(run.trace[0].verification.verdict, Verdict.UNKNOWN)

    def test_another_session_is_never_pruned_by_this_ones_dead_end(self) -> None:
        self.run_once(self.state)
        other = open_state(self.executor, self.key)
        self.assertNotEqual(other.session_id, self.state.session_id)
        run = self.run_once(other)
        self.assertIs(run.trace[0].verification.verdict, Verdict.UNKNOWN)

    def test_progress_in_the_same_session_reopens_the_branch(self) -> None:
        """Pruning must not poison a retry whose state has actually changed."""

        key = "logic.boolean_laws.de_morgan_laws"
        state = open_state(self.executor, key)
        run = Controller[RetrievalState](max_steps=2).run(
            state,
            SequencePolicy(
                (
                    # No WordNet archive and no observation source are
                    # registered, so the tool rung is a guaranteed miss.
                    retrieval_action(key, Rung.TOOL),
                    retrieval_action(key),
                )
            ),
            self.verifier,
            lambda current: False,
        )
        self.assertIs(run.trace[0].verification.verdict, Verdict.UNKNOWN)
        self.assertIs(run.trace[1].verification.verdict, Verdict.VERIFIED)
        evidence = self.verifier.session_pruning_evidence(state.session_id)
        self.assertEqual(len(evidence), 1)
        # Re-proposing the closed action from the ADVANCED state is a different
        # state key, so it is evaluated afresh rather than refused from the
        # ledger.
        outcome = self.verifier.evaluate(
            run.final_state, retrieval_action(key, Rung.TOOL)
        )
        self.assertIs(outcome.verdict, Verdict.UNKNOWN)
        self.assertNotIn("already closed", outcome.reason)

    def test_verified_branches_are_never_recorded_as_pruning_evidence(self) -> None:
        key = "logic.boolean_laws.de_morgan_laws"
        state = open_state(self.executor, key)
        run = Controller[RetrievalState](max_steps=1).run(
            state,
            SequencePolicy((retrieval_action(key),)),
            self.verifier,
            lambda current: bool(current.context),
        )
        self.assertIs(run.trace[0].verification.verdict, Verdict.VERIFIED)
        self.assertEqual(
            self.verifier.session_pruning_evidence(state.session_id), ()
        )

    def assert_frames_are_separated(
        self,
        spec_refuted: FrameSpec,
        spec_verified: FrameSpec,
        action: Action,
    ) -> None:
        """One session, two frames: the dead end must not close the live one.

        The shape is the same for both collision cases. ``spec_refuted``
        REFUTES ``action`` and ``spec_verified`` accepts it, and the two
        states share a session id because a dispatcher carrying one
        conversation across frames is exactly the situation session-scoped
        evidence exists for.
        """

        executor = FrameExecutor()
        verifier = RetrievalVerifier(UnifiedKnowledgeStore(()), executor)

        def state_for(spec: FrameSpec) -> RetrievalState:
            return RetrievalState.from_unknown(
                executor,
                executor.open_frame(spec),
                "answer",
                self.key,
                Literal("request", "needs", self.key),
            )

        dead_end = state_for(spec_refuted)
        live = replace(state_for(spec_verified), session_id=dead_end.session_id)

        # The frame-local key does NOT separate them, and is not asked to:
        # it is run-local by design and frames.py keeps it. The retrieval
        # verifier's key must, because pruning evidence outlives the run.
        frame_keys = FrameAssertionVerifier(executor)
        self.assertEqual(
            frame_keys.state_key(dead_end.frame),
            frame_keys.state_key(live.frame),
        )
        self.assertNotEqual(verifier.state_key(dead_end), verifier.state_key(live))

        def run(state: RetrievalState):
            return Controller[RetrievalState](max_steps=1).run(
                state, SequencePolicy((action,)), verifier, lambda current: False
            )

        self.assertIs(
            verifier.evaluate(live, action).verdict, Verdict.VERIFIED
        )
        self.assertIs(run(dead_end).trace[0].verification.verdict, Verdict.REFUTED)
        outcome = run(live).trace[0].verification
        self.assertIs(outcome.verdict, Verdict.VERIFIED)
        self.assertNotIn("already closed", outcome.reason)
        self.assertEqual(
            len(verifier.session_pruning_evidence(dead_end.session_id)), 1
        )

    def test_same_named_frames_with_contradictory_premises_do_not_share_a_prune(
        self,
    ) -> None:
        """P-RT6 re-adjudicated: MISSED here, then repaired.

        The prediction's own miss condition was "pruning refuses a branch
        that would otherwise have been VERIFIED". It had fired and the commit
        called P-RT6 FIRED anyway. ``RetrievalVerifier.state_key`` delegated
        the frame half to ``FrameAssertionVerifier.state_key``, which keys on
        the frame NAME and omits ``declarations``/``suspends``/``owner``, so
        two frames named alike but premised oppositely shared a pruning key:
        the REFUTED branch under ``NOT wet`` closed the VERIFIED branch under
        ``wet``, citing the other frame's premise as its reason.
        """

        wet = Literal("ground", "state", "wet")
        name = "runtime.frames.item6_collision"
        self.assert_frames_are_separated(
            FrameSpec(frame=name, declarations=(("p.ground", replace(wet, polarity=False)),)),
            FrameSpec(frame=name, declarations=(("p.ground", wet),)),
            Action.build(
                ActionKind.GEN,
                "assert_fact",
                {
                    "claim_id": "c.ground",
                    "subject": "ground",
                    "predicate": "state",
                    "value": "wet",
                },
            ),
        )

    def test_same_named_belief_frames_of_different_owners_do_not_share_a_prune(
        self,
    ) -> None:
        """The same collision as false-belief attribution, which is worse.

        Sally and Anne hold the same-named frame with opposite beliefs about
        the marble. Under the old key Sally's dead end refused Anne's branch
        and reported Sally's premise as the reason — one agent's model
        answering for another's is the precise failure the nested-frame work
        exists to prevent, arriving through the pruning cache instead of
        through the frame ladder.
        """

        marble = Literal("marble", "in", "basket")
        name = "runtime.frames.item6_belief_collision"
        self.assert_frames_are_separated(
            FrameSpec(
                frame=name,
                owner="sally",
                declarations=(("p.marble", replace(marble, polarity=False)),),
            ),
            FrameSpec(frame=name, owner="anne", declarations=(("p.marble", marble),)),
            Action.build(
                ActionKind.GEN,
                "assert_fact",
                {
                    "claim_id": "c.marble",
                    "subject": "marble",
                    "predicate": "in",
                    "value": "basket",
                },
            ),
        )

    def test_refused_branches_are_not_recorded(self) -> None:
        """REFUSED is an authority answer; re-checking it costs one predicate."""

        run = Controller[RetrievalState](max_steps=1).run(
            self.state,
            SequencePolicy((point_action(0),)),
            self.verifier,
            lambda current: False,
        )
        self.assertIs(run.trace[0].verification.verdict, Verdict.REFUSED)
        self.assertEqual(
            self.verifier.session_pruning_evidence(self.state.session_id), ()
        )


class TypedProtocolTests(unittest.TestCase):
    """P-RT1: the migration is typed and behaviour-preserving."""

    def setUp(self) -> None:
        self.executor = FrameExecutor()
        self.store = UnifiedKnowledgeStore((corpus_item("logic.x", ("logic.x",)),))

    def test_channel_accepts_and_normalises_the_legacy_strings(self) -> None:
        for raw in ("store", "user"):
            state = open_state(self.executor, "logic.x", channel=raw)
            assert state.pending is not None
            self.assertIsInstance(state.pending.resolution_channel, Channel)
            self.assertEqual(state.pending.resolution_channel.value, raw)
            self.assertEqual(state.pending.resolution_channel, raw)

    def test_unknown_channel_still_raises_the_original_message(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be 'store' or 'user'"):
            open_state(self.executor, "logic.x", channel="telepathy")

    def test_forged_raw_channel_string_is_refused_by_ask(self) -> None:
        state = open_state(
            self.executor,
            "logic.x",
            channel=Channel.USER,
            retrieval="frame_local",
        )
        forged = replace(
            state, pending=replace(state.pending, resolution_channel="invalid")
        )
        verifier = RetrievalVerifier(self.store, self.executor)
        outcome = verifier.evaluate(forged, ask_action("answer"))
        self.assertIs(outcome.verdict, Verdict.REFUSED)
        self.assertIn("invalid resolution channel", outcome.reason)

    def test_retrieval_verifier_satisfies_the_run_committer_protocol(self) -> None:
        verifier = RetrievalVerifier(self.store, self.executor)
        self.assertIsInstance(verifier, RunCommitter)

    def test_commit_run_stays_optional(self) -> None:
        """A verifier with no private ledgers implements nothing and still runs."""

        class Plain:
            name = "plain"

            def state_key(self, state) -> str:
                return repr(state)

            def evaluate(self, state, action):
                return Verification(Verdict.VERIFIED, "ok", state + 1)

        plain = Plain()
        self.assertNotIsInstance(plain, RunCommitter)
        run = Controller[int](max_steps=1).run(
            0,
            SequencePolicy((Action.build(ActionKind.GEN, "step"),)),
            plain,
            lambda state: state >= 1,
        )
        self.assertTrue(run.solved)

    def test_a_failing_commit_is_not_swallowed(self) -> None:
        """Documented duty: a committer must not raise, and is not covered for it.

        Swallowing would hand back a RunResult claiming a commit that did not
        happen, which is a worse failure than losing the result.
        """

        class Exploding:
            name = "exploding"

            def state_key(self, state) -> str:
                return repr(state)

            def evaluate(self, state, action):
                return Verification(Verdict.VERIFIED, "ok", state + 1)

            def commit_run(self, trace) -> None:
                raise RuntimeError("ledger unavailable")

        self.assertIsInstance(Exploding(), RunCommitter)
        with self.assertRaisesRegex(RuntimeError, "ledger unavailable"):
            Controller[int](max_steps=1).run(
                0,
                SequencePolicy((Action.build(ActionKind.GEN, "step"),)),
                Exploding(),
                lambda state: state >= 1,
            )

    def test_committed_sources_only_on_the_unified_surface(self) -> None:
        outsider = RetrievalItem(
            item_id="observation:forged",
            source="observation",
            title="forged",
            text="forged",
            epistemic_status="formal",
            source_ids=("forged",),
            aliases=("forged",),
        )
        with self.assertRaisesRegex(ValueError, "committed sources only"):
            UnifiedKnowledgeStore((outsider,))


if __name__ == "__main__":
    unittest.main()
