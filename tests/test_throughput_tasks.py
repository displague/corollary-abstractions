#!/usr/bin/env python3
"""The committed task book, re-validated against the tree it was built from.

`docs/DESIGN-grounded-throughput.md` §6 T3 says the book precedes the
answers, and SPEC §6 says any change to engine rendering after the book
seals **voids the run**. Neither promise is worth anything unless something
goes red when it is broken, so this file is the something:

- the **seal witness** — `rendering_module_digests` recomputed from the
  working tree. Edit any of the eleven rendering modules SPEC §6 names and
  this test fails, which is the void condition made checkable instead of
  honour-system;
- the **half rule**, recomputed here from the task ids rather than trusted,
  so half B cannot be quietly re-drawn once someone has seen the scores;
- the **grounding** — every artifact ref resolves, and every string the book
  says an answer must contain is checked to be *in the artifact it cites*,
  which is what makes "the receipt exists before the question does" a fact
  about this file rather than a sentence about it;
- the **arithmetic** — `exact_value` expectations are recomputed from the
  stored operand tree with this module's own `Fraction` evaluator. The book
  and the test would have to be wrong in the same way to agree wrongly;
- **rebuild idempotency** — the builder, run into a temporary path, must
  reproduce the committed bytes.

Like the builder, this file runs **no engine code**: it imports no module
from the serving path and asserts that the builder does not either. A test
that booted the kernel to check the answer key would be the answer key
grading itself.
"""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
BOOK_PATH = REPO / "experiments" / "throughput_tasks.json"
BUILDER = REPO / "scripts" / "build_throughput_tasks.py"
PY = sys.executable

SCHEMA = "corollary.throughput-tasks/1"
BUILT_BY = "scripts/build_throughput_tasks.py"

#: SPEC §6's seal-witness clause, quoted independently of the builder.
SEAL_WITNESS_MODULES = frozenset(
    {
        "scripts/answer.py",
        "scripts/belief.py",
        "scripts/closure_query.py",
        "scripts/evaluate.py",
        "scripts/gloss.py",
        "scripts/harness.py",
        "scripts/ownership.py",
        "scripts/resolver.py",
        "scripts/retrieval.py",
        "scripts/story.py",
        "scripts/supposition.py",
    }
)

KINDS = frozenset(
    {
        "corpus_definition",
        "exact_value",
        "twin_lookup",
        "closure_reachability",
        "belief_query",
        "refusal_due",
        "clarification_due",
    }
)

ANSWERABLE_KINDS = (
    "belief_query",
    "closure_reachability",
    "corpus_definition",
    "exact_value",
    "twin_lookup",
)
CONDITIONAL_KINDS = ("closure_reachability", "twin_lookup")

#: Kinds whose population is the committed artifact supply, exhausted, and
#: which therefore keep whatever half-B count that supply yields.
#: `closure_reachability` holds exactly the targets
#: `data/closure_targets/manifest.json` registers, and W2 answers about no
#: other file; padding it would be one target asked twice.
POPULATION_CAPPED_KINDS = ("closure_reachability",)

#: Raised from 3 before the seal: with three half-B tasks, T5's per-kind 80%
#: floor turns on a single answer.
HALF_B_FLOOR = 5

#: Anything in the serving path. Neither this test nor the builder may touch
#: one: the book is the answer key, and a key computed by the system under
#: test measures the system's agreement with itself.
ENGINE_MODULES = frozenset(
    {
        "answer", "belief", "closure_check", "closure_query", "closure_worlds",
        "controller", "conversation", "decompose", "dispatcher", "evaluate",
        "frames", "gloss", "harness", "match_signatures", "ownership",
        "request_grammar", "resolver", "retrieval", "story", "supposition",
        "write_stage",
    }
)

TWIN_LEDGER_FIELDS = {
    "typed": "typed_twin_groups",
    "family": "family_twin_groups_beyond_typed",
    "aliased": "aliased_twin_groups_beyond_typed",
    "mirror": "mirror_twin_groups",
    "shape": "shape_twin_groups",
}


def counts_kinds(tasks: list[dict]) -> set[str]:
    return {task["kind"] for task in tasks}


def load_book() -> dict:
    return json.loads(BOOK_PATH.read_text(encoding="utf-8"))


def expected_half(task_id: str) -> str:
    """The frozen rule, written out here so the book cannot define it."""

    digest = hashlib.sha256(task_id.encode()).hexdigest()
    return "B" if int(digest[:2], 16) % 2 else "A"


def canonical_lf_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def canonical_json(value) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def corpus_nodes(rel: str) -> list[dict]:
    doc = json.loads((REPO / rel).read_text(encoding="utf-8"))
    return doc.get("statement_nodes", [])


def evaluate_tree(node: dict, bindings: dict[str, Fraction]) -> Fraction:
    """An independent exact evaluator. Not the engine's, and not the builder's."""

    if "num" in node:
        return Fraction(node["num"])
    if "var" in node:
        return bindings[node["var"]]
    symbol, args = node["op"], [
        evaluate_tree(arg, bindings) for arg in node["args"]
    ]
    if symbol == "+":
        total = Fraction(0)
        for arg in args:
            total += arg
        return total
    if symbol == "*":
        product = Fraction(1)
        for arg in args:
            product *= arg
        return product
    if symbol == "neg":
        return -args[0]
    if symbol == "inv":
        return Fraction(1) / args[0]
    if symbol == "^":
        return args[0] ** int(args[1])
    raise AssertionError(f"unknown operator {symbol!r}")


def format_exact(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


COMPARE = {
    "=": lambda a, b: a == b,
    "<": lambda a, b: a < b,
    ">": lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    ">=": lambda a, b: a >= b,
}


class BookShape(unittest.TestCase):
    """The record types the design named, present and typed."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.book = load_book()

    def test_the_top_level_fields_are_all_there(self) -> None:
        for field in (
            "schema",
            "built_by",
            "seal",
            "scoring_rules",
            "rendering_module_digests",
            "counts",
            "tasks",
        ):
            with self.subTest(field=field):
                self.assertIn(field, self.book)
        self.assertEqual(self.book["schema"], SCHEMA)
        self.assertEqual(self.book["built_by"], BUILT_BY)

    def test_the_scoring_rules_are_stated_in_the_book(self) -> None:
        """A rule the stopwatch's implementer has to guess is a rule two
        implementers will guess differently."""

        rules = self.book["scoring_rules"]
        for key in (
            "receipt_subset",
            "clarification_leg",
            "per_kind_floor",
            "bounded_negative_is_an_answer",
            "zero_token_turns",
        ):
            with self.subTest(rule=key):
                self.assertIn(key, rules)
                self.assertIsInstance(rules[key], str)
        self.assertIn("subset assertions", rules["receipt_subset"])
        self.assertIn("absent keys are unconstrained", rules["receipt_subset"])
        self.assertIn(
            "per marked WAITING turn, not per task", rules["clarification_leg"]
        )
        self.assertIn("need_expect", rules["clarification_leg"])
        for kind in ANSWERABLE_KINDS:
            self.assertIn(kind, rules["per_kind_floor"])
        self.assertIn("clarification_due", rules["per_kind_floor"])
        self.assertIn("refusal_due", rules["per_kind_floor"])

    def test_the_seal_states_the_frozen_half_rule(self) -> None:
        seal = self.book["seal"]
        self.assertIn("sealed until the registered run", seal)
        self.assertIn("sha256", seal)
        self.assertIn("% 2", seal)

    def test_every_task_carries_the_typed_record(self) -> None:
        for task in self.book["tasks"]:
            with self.subTest(task=task["task_id"]):
                self.assertIn(task["kind"], KINDS)
                self.assertIn(
                    task["profile"], {"corollary/kernel", "corollary/conversation"}
                )
                self.assertIn(task["half"], {"A", "B"})
                self.assertTrue(task["turns"])
                for turn in task["turns"]:
                    self.assertEqual(turn["role"], "user")
                    self.assertIsInstance(turn["content"], str)
                expected = task["expected"]
                self.assertIn(expected["outcome"], {"answer", "refuse", "ask"})
                self.assertIn(expected["check"], {"exact", "receipt", "verdict"})
                self.assertIsInstance(expected["status_expect"], str)
                self.assertIsInstance(expected["content_must_contain"], list)
                self.assertIsInstance(expected["artifact_refs"], list)
                self.assertIsInstance(expected["receipt_expect"], dict)

    def test_the_status_alphabet_stays_the_frozen_closed_set(self) -> None:
        """SPEC §5 froze it, inconsistencies included. The book may not add."""

        allowed = {
            "waiting", "solved", "refused", "exhausted", "found", "held",
            "canceled", "cycle", "hop_ceiling", "abstained",
            "PROVEN", "VERIFIED", "REFUSED",
        }
        for task in self.book["tasks"]:
            with self.subTest(task=task["task_id"]):
                self.assertIn(task["expected"]["status_expect"], allowed)
                for turn in task["turns"]:
                    if "expected_status" in turn:
                        self.assertIn(turn["expected_status"], allowed)


class TheHalfRuleIsRecomputed(unittest.TestCase):
    """Half B is sealed, so its membership may not be taken on the book's word."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.book = load_book()

    def test_every_task_half_recomputes_from_its_id(self) -> None:
        for task in self.book["tasks"]:
            with self.subTest(task=task["task_id"]):
                self.assertEqual(task["half"], expected_half(task["task_id"]))

    def test_task_ids_are_unique(self) -> None:
        ids = [task["task_id"] for task in self.book["tasks"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_no_half_b_task_repeats_half_a_content(self) -> None:
        """A sealed task whose turns also sit in half A is not sealed."""

        seen: dict[str, str] = {}
        for task in self.book["tasks"]:
            signature = canonical_json(
                [[turn["role"], turn["content"]] for turn in task["turns"]]
            )
            self.assertNotIn(
                signature,
                seen,
                f"{task['task_id']} repeats the turns of {seen.get(signature)}",
            )
            seen[signature] = task["task_id"]


class CountsAndFloors(unittest.TestCase):
    """T3's floors, recomputed rather than read."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.book = load_book()
        cls.tasks = cls.book["tasks"]

    def test_the_counts_block_matches_the_tasks(self) -> None:
        counts = self.book["counts"]
        self.assertEqual(counts["total"], len(self.tasks))
        for kind, number in counts["by_kind"].items():
            with self.subTest(kind=kind):
                self.assertEqual(
                    number, sum(1 for t in self.tasks if t["kind"] == kind)
                )
        for half in ("A", "B"):
            self.assertEqual(
                counts["by_half"][half],
                sum(1 for t in self.tasks if t["half"] == half),
            )
        for kind, halves in counts["by_kind_half"].items():
            for half, number in halves.items():
                with self.subTest(kind=kind, half=half):
                    self.assertEqual(
                        number,
                        sum(
                            1
                            for t in self.tasks
                            if t["kind"] == kind and t["half"] == half
                        ),
                    )
        answerable = [
            t
            for t in self.tasks
            if t["expected"]["outcome"] == "answer"
            and t["kind"] in ANSWERABLE_KINDS
        ]
        self.assertEqual(counts["answerable_total"], len(answerable))
        self.assertEqual(
            counts["answerable_without_conditional_kinds"],
            sum(1 for t in answerable if t["kind"] not in CONDITIONAL_KINDS),
        )
        self.assertEqual(
            counts["clarification_answer_tasks"],
            sum(
                1
                for t in self.tasks
                if t["kind"] == "clarification_due"
                and t["expected"]["outcome"] == "answer"
            ),
        )
        self.assertEqual(
            counts["waiting_marked_turns"],
            sum(
                1
                for t in self.tasks
                for turn in t["turns"]
                if turn.get("expected_status") == "waiting"
            ),
        )

    def test_the_answerable_population_excludes_clarification_tasks(
        self,
    ) -> None:
        """A resume task ends in an answer but its kind is graded by the
        WAITING leg. Counting it as answerable would let it pad the per-kind
        floor of a population it is not scored in."""

        counts = self.book["counts"]
        self.assertNotIn("clarification_due", counts["answerable_by_kind"])
        self.assertGreaterEqual(counts["clarification_answer_tasks"], 1)
        self.assertEqual(
            counts["answerable_total"],
            sum(counts["answerable_by_kind"].values()),
        )
        self.assertEqual(set(counts["answerable_by_kind"]), set(ANSWERABLE_KINDS))

    def test_every_kind_declares_where_its_ids_came_from(self) -> None:
        provenance = self.book["counts"]["id_provenance"]
        self.assertEqual(set(provenance), set(counts_kinds(self.tasks)))
        for kind, source in provenance.items():
            with self.subTest(kind=kind):
                self.assertIn(source, {"artifact-derived", "author-authored"})
        for kind in ("corpus_definition", "twin_lookup", "closure_reachability"):
            self.assertEqual(provenance[kind], "artifact-derived")

    def test_the_book_clears_the_hundred_task_floor(self) -> None:
        self.assertGreaterEqual(len(self.tasks), 100)

    def test_the_book_clears_the_fifty_answerable_floor(self) -> None:
        answerable = sum(
            1
            for t in self.tasks
            if t["expected"]["outcome"] == "answer"
            and t["kind"] in ANSWERABLE_KINDS
        )
        self.assertGreaterEqual(answerable, 50)

    def test_dropping_both_conditional_kinds_still_clears_fifty(self) -> None:
        """SPEC §9 ¶DEV-2: T3's floor is unaffected by a wiring-step drop."""

        surviving = sum(
            1
            for t in self.tasks
            if t["expected"]["outcome"] == "answer"
            and t["kind"] in ANSWERABLE_KINDS
            and t["kind"] not in CONDITIONAL_KINDS
        )
        self.assertGreaterEqual(surviving, 50)

    def test_every_answerable_kind_clears_the_half_b_floor(self) -> None:
        """T5 grades within every kind, so no kind may be unmeasurable in B.

        The floor is five rather than three: at three, one wrong answer is
        67% and the per-kind 80% gate turns on a coin toss instead of on the
        kind. A population-capped kind is the one exception (below).
        """

        for kind in ANSWERABLE_KINDS:
            if kind in POPULATION_CAPPED_KINDS:
                continue
            with self.subTest(kind=kind):
                self.assertGreaterEqual(
                    sum(
                        1
                        for t in self.tasks
                        if t["kind"] == kind and t["half"] == "B"
                    ),
                    HALF_B_FLOOR,
                )

    def test_a_population_capped_kind_is_declared_and_still_scorable(
        self,
    ) -> None:
        """The exception, held to its own bar: a capped kind keeps whatever
        half B its committed supply yields, but a kind with nothing in B is
        dropped rather than capped, and the cap is recorded in the book."""

        declared = self.book["counts"]["population_capped"]
        self.assertEqual(set(declared), set(POPULATION_CAPPED_KINDS))
        for kind, capped in declared.items():
            with self.subTest(kind=kind):
                self.assertTrue(capped)
                self.assertGreaterEqual(
                    sum(
                        1
                        for t in self.tasks
                        if t["kind"] == kind and t["half"] == "B"
                    ),
                    1,
                )

    def test_the_capped_kind_holds_the_whole_committed_supply(self) -> None:
        """A cap is only honest if the population really is exhausted: every
        registered target is in the book, and none is in it twice."""

        manifest = json.loads(
            (REPO / "data" / "closure_targets" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        registered = {entry["path"] for entry in manifest["files"]}
        used = [
            t["expected"]["artifact_refs"][0]
            for t in self.tasks
            if t["kind"] == "closure_reachability"
        ]
        self.assertEqual(sorted(used), sorted(registered))

    def test_the_book_records_the_floor_it_was_built_to(self) -> None:
        self.assertEqual(
            self.book["counts"]["half_b_floor_per_answerable_kind"],
            HALF_B_FLOOR,
        )

    def test_the_refusal_and_clarification_sets_are_not_empty(self) -> None:
        """T5 grades both at 100%, which needs something to grade."""

        self.assertTrue(
            [t for t in self.tasks if t["expected"]["outcome"] == "refuse"]
        )
        self.assertTrue(
            [t for t in self.tasks if t["expected"]["outcome"] == "ask"]
        )

    def test_the_belief_set_carries_real_false_belief_cases(self) -> None:
        """A visibility question the world never contradicts tests nothing."""

        false_belief = [t for t in self.tasks if t.get("false_belief")]
        self.assertGreaterEqual(len(false_belief), 3)

    def test_the_belief_set_uses_both_narrator_forms(self) -> None:
        """`belief.read` has two world-fact forms — `WORLD_MOVE` and
        `WORLD_IN`. A set that only ever narrated one would leave half the
        channel that must NOT reach the agent's store unmeasured."""

        forms = {
            t.get("world_fact_form")
            for t in self.tasks
            if t["kind"] == "belief_query"
        }
        self.assertEqual(forms, {None, "moves", "in"})


class TheSealWitness(unittest.TestCase):
    """SPEC §6: engine rendering changed after the seal => the run is void."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.book = load_book()

    def test_the_witness_covers_exactly_the_modules_the_spec_names(self) -> None:
        self.assertEqual(
            set(self.book["rendering_module_digests"]), set(SEAL_WITNESS_MODULES)
        )

    def test_every_digest_matches_the_current_tree(self) -> None:
        """The void condition, made checkable. If this goes red, the rendering
        the book was built against is not the rendering in the tree, and the
        answer is to rebuild the book — not to update the digest."""

        for rel, digest in sorted(self.book["rendering_module_digests"].items()):
            with self.subTest(module=rel):
                path = REPO / rel
                self.assertTrue(path.is_file(), f"{rel} is gone")
                self.assertEqual(canonical_lf_sha256(path), digest)


class GroundingResolves(unittest.TestCase):
    """Every citation points at something committed, and says something true."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.book = load_book()

    def test_every_artifact_ref_resolves(self) -> None:
        for task in self.book["tasks"]:
            for ref in task["expected"]["artifact_refs"]:
                path, _, fragment = ref.partition("#")
                with self.subTest(task=task["task_id"], ref=ref):
                    self.assertTrue(
                        (REPO / path).exists(), f"{path} does not exist"
                    )
                    if fragment:
                        ids = {
                            node.get("statement_id") for node in corpus_nodes(path)
                        }
                        self.assertIn(fragment, ids)

    def test_answerable_tasks_cite_something_or_say_why_not(self) -> None:
        """A receipt never claims an artifact the answer did not rest on, and a
        route with no artifact says `computed` / `session` instead (§6.1)."""

        for task in self.book["tasks"]:
            if task["expected"]["outcome"] != "answer":
                continue
            expected = task["expected"]
            with self.subTest(task=task["task_id"]):
                if expected["artifact_refs"]:
                    continue
                self.assertIn(
                    expected["receipt_expect"].get("grounding")
                    or expected["receipt_expect"].get("derivation"),
                    {"computed", "session"},
                )

    def test_corpus_quotes_are_the_cited_nodes_own_sentences(self) -> None:
        """The definition tasks quote the corpus; here is the check that they
        quote *the node they cite*, verbatim, field for field."""

        checked = 0
        for task in self.book["tasks"]:
            refs = [r for r in task["expected"]["artifact_refs"] if "#" in r]
            if not refs:
                continue
            path, _, fragment = refs[0].partition("#")
            node = next(
                n for n in corpus_nodes(path) if n.get("statement_id") == fragment
            )
            quotable = {
                str(node.get("title", "")),
                str(
                    (node.get("semantic_interpretation") or {}).get(
                        "statement_meaning", ""
                    )
                ),
            }
            for text in task["expected"]["content_must_contain"]:
                with self.subTest(task=task["task_id"], text=text[:40]):
                    self.assertIn(text, quotable)
            checked += 1
        self.assertGreaterEqual(checked, 30)

    def test_definition_receipts_carry_the_nodes_canonical_digest(self) -> None:
        """T7 revalidates receipts client-side; the digest has to be real."""

        for task in self.book["tasks"]:
            if task["kind"] != "corpus_definition":
                continue
            receipt = task["expected"]["receipt_expect"]
            node = next(
                n
                for n in corpus_nodes(receipt["corpus_path"])
                if n.get("statement_id") == receipt["statement_id"]
            )
            with self.subTest(task=task["task_id"]):
                self.assertEqual(
                    receipt["node_sha256"],
                    hashlib.sha256(
                        canonical_json(node).encode("utf-8")
                    ).hexdigest(),
                )

    def test_twin_quotes_are_the_cited_ledger_groups_members(self) -> None:
        ledger = json.loads(
            (REPO / "reports" / "signature_matches.json").read_text(
                encoding="utf-8"
            )
        )
        checked = 0
        for task in self.book["tasks"]:
            if task["kind"] != "twin_lookup":
                continue
            group = task["ledger_group"]
            self.assertEqual(
                group["field"], TWIN_LEDGER_FIELDS[group["level"]]
            )
            members = [
                member["statement_id"]
                for member in ledger[group["field"]][group["group_index"]][
                    "members"
                ]
            ]
            receipt = task["expected"]["receipt_expect"]
            with self.subTest(task=task["task_id"]):
                self.assertEqual(receipt["member_ids"], members)
                self.assertEqual(
                    receipt["ledger_path"], "reports/signature_matches.json"
                )
                queried = task["turns"][0]["content"].split(" ", 1)[1]
                self.assertIn(queried, members)
                for text in task["expected"]["content_must_contain"]:
                    self.assertIn(text, members)
                    self.assertNotEqual(text, queried)
            checked += 1
        self.assertGreaterEqual(checked, 3)

    def test_the_twin_set_covers_every_level_the_ledger_holds(self) -> None:
        """A book of `typed` pairs would leave the four weaker levels — the
        ones whose membership a reader has most reason to doubt — untested."""

        levels = {
            task["ledger_group"]["level"]
            for task in load_book()["tasks"]
            if task["kind"] == "twin_lookup"
        }
        self.assertEqual(levels, set(TWIN_LEDGER_FIELDS))

    def test_no_twin_task_claims_a_level_a_stronger_group_outranks(
        self,
    ) -> None:
        """`_route_twin` reports the STRONGEST level listing the queried id,
        so a task expecting `shape` is only correct if no typed, family,
        aliased or mirror group lists that id. Recomputed from the ledger."""

        order = ["typed", "family", "aliased", "mirror", "shape"]
        ledger = json.loads(
            (REPO / "reports" / "signature_matches.json").read_text(
                encoding="utf-8"
            )
        )
        listing: dict[str, set[str]] = {}
        for level, field in TWIN_LEDGER_FIELDS.items():
            for group in ledger[field]:
                for member in group["members"]:
                    listing.setdefault(member["statement_id"], set()).add(level)
        for task in load_book()["tasks"]:
            if task["kind"] != "twin_lookup":
                continue
            queried = task["turns"][0]["content"].split(" ", 1)[1]
            claimed = task["ledger_group"]["level"]
            with self.subTest(task=task["task_id"]):
                self.assertEqual(listing[queried], set(task["ledger_group"]["levels_listing_id"]))
                strongest = min(listing[queried], key=order.index)
                self.assertEqual(claimed, strongest)

    def test_closure_receipts_match_the_committed_closure_and_target(self) -> None:
        manifest = json.loads(
            (REPO / "data" / "closure_targets" / "manifest.json").read_text(
                encoding="utf-8"
            )
        )
        by_path = {entry["path"]: entry for entry in manifest["files"]}
        for task in self.book["tasks"]:
            if task["kind"] != "closure_reachability":
                continue
            target, closure_rel = task["expected"]["artifact_refs"]
            receipt = task["expected"]["receipt_expect"]
            closure = json.loads(
                (REPO / closure_rel).read_text(encoding="utf-8")
            )
            with self.subTest(task=task["task_id"]):
                self.assertEqual(receipt["schema"], "closure-receipt/1")
                self.assertEqual(receipt["world_id"], closure["world_id"])
                self.assertEqual(
                    receipt["closure_digest"], closure["closure_digest"]
                )
                self.assertEqual(receipt["adapter_id"], closure["adapter_id"])
                self.assertEqual(receipt["horizon"], closure["horizon"])
                self.assertEqual(
                    receipt["visited_states"], len(closure["states"])
                )
                self.assertEqual(
                    receipt["target_digest"],
                    hashlib.sha256((REPO / target).read_bytes()).hexdigest(),
                )
                self.assertEqual(
                    receipt["target_digest"], by_path[target]["sha256"]
                )
                arm = by_path[target]["arm"]
                self.assertEqual(
                    receipt["outcome"],
                    "REACHABLE" if arm == "reachable" else
                    "NOT_REACHABLE_WITHIN_HORIZON",
                )
                # SPEC §6.1: the bounded negative is an ANSWER, not a refusal.
                self.assertEqual(task["expected"]["outcome"], "answer")
                self.assertEqual(
                    task["expected"]["status_expect"],
                    "found" if arm == "reachable" else "exhausted",
                )

    def test_verified_absences_are_still_absences(self) -> None:
        """A refusal built on "the corpus does not contain this" rots the day
        somebody seeds a statement that does. Re-checked, not remembered."""

        corpora = [
            path.read_text(encoding="utf-8").casefold()
            for path in sorted((REPO / "data").glob("*/nodes.json"))
        ]
        self.assertTrue(corpora)
        checked = 0
        for task in self.book["tasks"]:
            absence = task.get("verified_absence")
            if not absence:
                continue
            for token in absence["tokens"]:
                with self.subTest(task=task["task_id"], token=token):
                    needle = token.casefold()
                    self.assertFalse(
                        any(needle in text for text in corpora),
                        f"{token!r} now occurs in a committed corpus",
                    )
            checked += 1
        self.assertGreaterEqual(checked, 3)


class ExactValuesRecompute(unittest.TestCase):
    """The arithmetic, redone here from the operand tree the book stores."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.book = load_book()
        cls.tasks = [
            t for t in cls.book["tasks"] if t["kind"] == "exact_value"
        ]

    def test_there_are_exact_value_tasks_to_recompute(self) -> None:
        self.assertGreaterEqual(len(self.tasks), 10)

    def test_every_evaluation_recomputes_to_its_stated_value(self) -> None:
        seen = 0
        for task in self.tasks:
            spec = task["expr_spec"]
            if spec["form"] != "evaluate":
                continue
            bindings = {k: Fraction(v) for k, v in spec["bindings"].items()}
            value = format_exact(evaluate_tree(spec["tree"], bindings))
            with self.subTest(task=task["task_id"]):
                self.assertEqual(value, spec["expected_exact"])
                self.assertEqual(
                    task["expected"]["receipt_expect"]["exact"], value
                )
                self.assertIn(
                    f"exact      : {value}",
                    task["expected"]["content_must_contain"],
                )
            seen += 1
        self.assertGreaterEqual(seen, 5)

    def test_every_relation_recomputes_to_its_stated_verdict(self) -> None:
        seen = 0
        for task in self.tasks:
            spec = task["expr_spec"]
            if spec["form"] != "relation":
                continue
            bindings = {k: Fraction(v) for k, v in spec["bindings"].items()}
            holds = COMPARE[spec["relation"]](
                evaluate_tree(spec["left"], bindings),
                evaluate_tree(spec["right"], bindings),
            )
            with self.subTest(task=task["task_id"]):
                self.assertEqual(holds, spec["expected_holds"])
                self.assertIn(
                    f"holds      : {'yes' if holds else 'no'}",
                    task["expected"]["content_must_contain"],
                )
            seen += 1
        self.assertGreaterEqual(seen, 5)

    def test_the_kind_asks_for_more_than_positive_integers(self) -> None:
        """`exact` is the whole point of the module this kind measures. A set
        that only ever expected a positive integer would never once exercise
        the exactness, and a float engine would pass it."""

        exacts = [
            t["expr_spec"]["expected_exact"]
            for t in self.tasks
            if t["expr_spec"]["form"] == "evaluate"
        ]
        self.assertGreaterEqual(
            len([v for v in exacts if "/" in v]), 2, "no non-integer answers"
        )
        self.assertGreaterEqual(
            len([v for v in exacts if v.startswith("-")]), 2,
            "no negative answers",
        )

    def test_relation_truth_does_not_correlate_with_the_glyph(self) -> None:
        """If every `>` were true and every `<` false, a system could score
        the kind by reading the operator and never doing the arithmetic."""

        by_glyph: dict[str, set[bool]] = {}
        for task in self.tasks:
            spec = task["expr_spec"]
            if spec["form"] != "relation":
                continue
            by_glyph.setdefault(spec["relation"], set()).add(
                spec["expected_holds"]
            )
        for glyph in ("<", ">", "="):
            with self.subTest(glyph=glyph):
                self.assertEqual(
                    by_glyph.get(glyph),
                    {True, False},
                    f"{glyph} never appears both true and false",
                )

    def test_every_false_relation_is_off_by_exactly_one(self) -> None:
        """A false relation that misses by a mile is passed by any system
        that is roughly right. Off-by-one is what separates computing from
        approximating."""

        for task in self.tasks:
            spec = task["expr_spec"]
            if spec["form"] != "relation" or spec["expected_holds"]:
                continue
            bindings = {k: Fraction(v) for k, v in spec["bindings"].items()}
            left = evaluate_tree(spec["left"], bindings)
            right = evaluate_tree(spec["right"], bindings)
            with self.subTest(task=task["task_id"]):
                self.assertEqual(abs(left - right), 1)

    def test_a_false_relation_is_still_an_answer(self) -> None:
        """`holds: no` is a correct answer, not a refusal. If the book scored
        it as one, the metric would reward declining the hard direction."""

        false_ones = [
            t for t in self.tasks if t["expr_spec"].get("expected_holds") is False
        ]
        self.assertGreaterEqual(len(false_ones), 2)
        for task in false_ones:
            with self.subTest(task=task["task_id"]):
                self.assertEqual(task["expected"]["outcome"], "answer")
                self.assertEqual(task["expected"]["status_expect"], "solved")

    def test_the_english_line_carries_the_expression_it_claims(self) -> None:
        """The stored expression must be the substring the front end selects,
        so a reader can see the line and the operand tree describe one thing."""

        for task in self.tasks:
            spec = task["expr_spec"]
            with self.subTest(task=task["task_id"]):
                self.assertIn(spec["expression"], spec["line"])
                self.assertEqual(
                    spec["line"], task["turns"][0]["content"]
                )
                for name, value in spec["bindings"].items():
                    self.assertIn(f"{name} = {value}", spec["line"])

    def test_computed_answers_claim_no_artifact(self) -> None:
        for task in self.tasks:
            with self.subTest(task=task["task_id"]):
                self.assertEqual(task["expected"]["artifact_refs"], [])
                self.assertEqual(
                    task["expected"]["receipt_expect"]["grounding"], "computed"
                )


class ClarificationSetIsRenderable(unittest.TestCase):
    """T5 grades the clarification set at 100%, so it has to be a real set."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tasks = [
            t
            for t in load_book()["tasks"]
            if t["kind"] == "clarification_due"
        ]

    def test_every_clarification_task_marks_a_waiting_turn(self) -> None:
        """The book's own scoring rule says the leg is graded per marked
        WAITING turn. If a task carried no such turn the leg would skip it
        and score 100% of a set it never looked at."""

        for task in self.tasks:
            with self.subTest(task=task["task_id"]):
                self.assertTrue(
                    [
                        turn
                        for turn in task["turns"]
                        if turn.get("expected_status") == "waiting"
                    ],
                    "no turn marked WAITING",
                )

    def test_a_waiting_conversation_turn_names_its_need_or_resumes(
        self,
    ) -> None:
        """SPEC §6.2: on the conversation profile a WAITING turn carries a
        need record. On the kernel profile it does not, and the leg says so
        rather than demanding one."""

        for task in self.tasks:
            if task["profile"] != "corollary/conversation":
                continue
            with self.subTest(task=task["task_id"]):
                if task["expected"]["outcome"] == "ask":
                    self.assertIn("need_expect", task["expected"])
        for task in self.tasks:
            if task["profile"] != "corollary/kernel":
                continue
            with self.subTest(task=task["task_id"]):
                self.assertNotIn("need_expect", task["expected"])

    def test_the_ask_tasks_expect_a_waiting_need(self) -> None:
        asks = [t for t in self.tasks if t["expected"]["outcome"] == "ask"]
        self.assertGreaterEqual(len(asks), 5)
        for task in asks:
            with self.subTest(task=task["task_id"]):
                self.assertEqual(task["expected"]["status_expect"], "waiting")
                self.assertEqual(task["profile"], "corollary/conversation")
                self.assertTrue(task["expected"]["need_expect"]["slot"])
                self.assertEqual(len(task["turns"]), 1)

    def test_the_ask_values_are_outside_the_closed_vocabulary(self) -> None:
        """An ask task whose value is registered would be answered, not asked.
        The vocabulary is lifted from the grammar's source with `ast` — read as
        a literal, never imported."""

        tree = ast.parse(
            (REPO / "scripts" / "request_grammar.py").read_text(encoding="utf-8")
        )
        values = None
        for statement in tree.body:
            targets = (
                statement.targets
                if isinstance(statement, ast.Assign)
                else [statement.target]
                if isinstance(statement, ast.AnnAssign)
                else []
            )
            for target in targets:
                if isinstance(target, ast.Name) and target.id == "SLOT_VALUES":
                    values = ast.literal_eval(statement.value)
        self.assertIsNotNone(values)
        registered = set(values["egg_color"])
        for task in self.tasks:
            if task["expected"]["outcome"] != "ask":
                continue
            utterance = task["turns"][0]["content"]
            with self.subTest(task=task["task_id"]):
                self.assertFalse(
                    [v for v in registered if f" {v}" in f" {utterance}"],
                    f"{utterance!r} names a registered value",
                )

    def test_the_resume_tasks_end_where_the_ask_left_off(self) -> None:
        resumes = [t for t in self.tasks if t.get("phase") == "resume"]
        self.assertGreaterEqual(len(resumes), 2)
        ask_ids = {
            t["task_id"] for t in self.tasks if t["expected"]["outcome"] == "ask"
        }
        for task in resumes:
            with self.subTest(task=task["task_id"]):
                self.assertEqual(len(task["turns"]), 2)
                self.assertEqual(task["turns"][0]["expected_status"], "waiting")
                self.assertEqual(task["expected"]["outcome"], "answer")
                if "resume_of" in task:
                    self.assertIn(task["resume_of"], ask_ids)


class RefusalSetIsVerifiedAbsence(unittest.TestCase):
    """T2 keeps every refusal refused, so the set may not contain a soft one."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tasks = [
            t for t in load_book()["tasks"] if t["kind"] == "refusal_due"
        ]

    def test_refusals_require_no_content(self) -> None:
        """Refusal turns score zero useful tokens whatever they say (§6), so a
        required substring here would grade prose the metric ignores."""

        for task in self.tasks:
            with self.subTest(task=task["task_id"]):
                self.assertEqual(task["expected"]["outcome"], "refuse")
                self.assertEqual(task["expected"]["content_must_contain"], [])

    def test_every_refusal_names_the_route_it_must_die_on(self) -> None:
        routes = {
            "ownership", "dispatcher", "twin", "closure", "write_gate",
            "resolver", "evaluate", "story", "belief", "gloss",
        }
        for task in self.tasks:
            with self.subTest(task=task["task_id"]):
                self.assertIn(task["route_expect"], routes)

    def test_the_set_spans_more_than_one_route(self) -> None:
        self.assertGreaterEqual(
            len({t["route_expect"] for t in self.tasks}), 3
        )


class BuiltWithoutTheEngine(unittest.TestCase):
    """The construction rule, checked rather than trusted."""

    def test_the_builder_imports_no_engine_module(self) -> None:
        tree = ast.parse(BUILDER.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        offenders = sorted(imported & ENGINE_MODULES)
        self.assertEqual(
            offenders,
            [],
            "the answer key may not be computed by the system under test",
        )

    def test_the_builder_stays_engine_clean_in_its_own_process(self) -> None:
        """The runtime half of the guard, run where it means something.

        An in-process `sys.modules` assertion inside this suite would be a
        statement about whichever test module imported first, not about the
        builder: run the whole suite in one interpreter and `harness` is
        already loaded before this file is reached. So the builder asserts
        its OWN interpreter, in the child process that does the building,
        and prints a line saying it did. This test reads the exit code and
        that line.
        """

        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "throughput_tasks.json"
            proc = subprocess.run(
                [PY, str(BUILDER), "--out", str(out), "--assert-clean-imports"],
                capture_output=True,
                text=True,
                cwd=REPO,
                timeout=900,
            )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn(
            "engine-clean imports: verified in this process", proc.stdout
        )


class RebuildIsIdempotent(unittest.TestCase):
    """Run the builder again; the committed bytes must come back."""

    def test_a_fresh_build_reproduces_the_committed_book(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / "throughput_tasks.json"
            proc = subprocess.run(
                [PY, str(BUILDER), "--out", str(out), "--assert-clean-imports"],
                capture_output=True,
                text=True,
                cwd=REPO,
                timeout=900,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            rebuilt = out.read_bytes()
        self.assertEqual(
            rebuilt,
            BOOK_PATH.read_bytes(),
            "the builder is not a function of the committed tree, or the "
            "committed book is stale",
        )

    def test_the_committed_book_is_written_with_lf_newlines(self) -> None:
        self.assertNotIn(b"\r\n", BOOK_PATH.read_bytes())


if __name__ == "__main__":
    unittest.main()
