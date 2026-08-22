#!/usr/bin/env python3
"""The stopwatch, checked against a stub server that is not the engine.

`docs/DESIGN-grounded-throughput.md` §3 says the stopwatch "speaks only the
public API (no imports from the serving process)". This suite holds it to
that and to the scoring rules the sealed task book carries -- without ever
letting a real system answer a real task.

**The seal, stated as what this file may do.** It READS
`experiments/throughput_tasks.json` (paddings, expectations, digests) and it
EXECUTES nothing against a real system: every response here is canned by a
stub in this process, or produced by `scripts/dump_server.py`, which is the
C1 control and answers no question. Half B is never selected; the two
end-to-end runs below pass `--half A`, which is the half the book's `seal`
opens to "implementation and debugging". A test that booted the kernel to
check the clock would be the system under test timing itself.

Like the stopwatch and the task-book builder, this file imports no engine
module, and asserts that the stopwatch does not either -- once by reading its
source with `ast`, and once by reading the clean-imports line the stopwatch
prints from the process that actually did the timing.
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import measure_throughput as mt  # noqa: E402
import dump_server as ds  # noqa: E402

PY = sys.executable
STOPWATCH = REPO / "scripts" / "measure_throughput.py"
BOOK_PATH = REPO / "experiments" / "throughput_tasks.json"
BASELINE_PATH = REPO / "experiments" / "throughput_baseline.json"

BOOK = json.loads(BOOK_PATH.read_text(encoding="utf-8"))
BASELINE = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
HALF_A = [t for t in BOOK["tasks"] if t["half"] == "A"]

#: The engine modules the stopwatch may never import. Quoted here rather than
#: imported from the stopwatch, so an implementer who shortens the list there
#: has to shorten it twice.
ENGINE_MODULES = frozenset(
    {
        "answer", "belief", "closure_build", "closure_check", "closure_query",
        "closure_worlds", "controller", "conversation", "decompose", "deixis",
        "discourse", "dispatcher", "entailment", "evaluate", "frames",
        "gloss", "harness", "lifetimes", "match_signatures", "ownership",
        "preference", "request_grammar", "resolver", "retrieval",
        "serve_chat", "session_keys", "session_run", "session_state",
        "specialize", "story", "supposition", "theory_of_mind", "write_stage",
    }
)

#: The kernel's frozen label padding, as the committed book actually spells
#: it. Pinned here so the B-side rule cannot quietly widen: if the engine's
#: rendering grows a new label shape, this list goes red before any baseline
#: gets credit for a string it never produced.
BOOK_LABEL_PADDINGS = [
    "adapter_id: ",
    "agent      : ",
    "believes   : ",
    "closure: ",
    "closure_digest: ",
    "divergence : ",
    "exact      : ",
    "expression : ",
    "given      : ",
    "holds      : ",
    "horizon: ",
    "outcome: ",
    "relation   : ",
    "shortest_route: ",
    "subject    : ",
    "target_digest: ",
    "visited_states: ",
    "world says : ",
    "world_id: ",
]


# ---------------------------------------------------------------------------
# a stub server: canned SSE, no engine anywhere near it
# ---------------------------------------------------------------------------


def sse_chunk(delta: dict, finish: str | None = None, extension: dict | None = None):
    chunk = {
        "id": "chatcmpl-stub",
        "object": "chat.completion.chunk",
        "created": 0,
        "model": "stub",
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
    }
    if extension is not None:
        chunk["x_corollary"] = extension
    return chunk


class StubHandler(BaseHTTPRequestHandler):
    """Answers from a table keyed by the request's last user message."""

    protocol_version = "HTTP/1.1"
    table: dict[str, dict] = {}
    default: dict = {"content": "", "x_corollary": {"status": "exhausted"}}
    first_delta_delay_s: float = 0.0
    seen: list[dict] = []
    #: C-1(b). What `/api/ps` reports as the served context. `None` makes the
    #: stub answer with an empty model list, which is the not-loaded case the
    #: `/api/show` fallback exists for.
    ps_context_length: int | None = 32768
    show_context_length: int | None = 262144
    probes: list[str] = []

    def log_message(self, *args) -> None:  # noqa: D102
        pass

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.rstrip("/")
        if path == "/api/ps":
            type(self).probes.append("/api/ps")
            models = (
                [
                    {
                        "name": "qwen3:4b-instruct",
                        "model": "qwen3:4b-instruct",
                        "context_length": self.ps_context_length,
                    }
                ]
                if self.ps_context_length is not None
                else []
            )
            self._json(200, {"models": models})
            return
        self._json(200, {"object": "list", "data": [{"id": "stub"}]})

    def _json(self, status: int, body: dict) -> None:
        blob = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(blob)))
        self.end_headers()
        self.wfile.write(blob)

    def _sse(self, chunk: dict) -> None:
        self.wfile.write(b"data: ")
        self.wfile.write(json.dumps(chunk, ensure_ascii=False).encode("utf-8"))
        self.wfile.write(b"\n\n")

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        request = json.loads(self.rfile.read(length).decode("utf-8"))
        if self.path.rstrip("/") == "/api/show":
            type(self).probes.append("/api/show")
            info = (
                {"qwen3.context_length": self.show_context_length}
                if self.show_context_length is not None
                else {}
            )
            self._json(200, {"model_info": info})
            return
        type(self).seen.append(request)
        users = [m for m in request["messages"] if m["role"] == "user"]
        key = users[-1]["content"] if users else ""
        canned = self.table.get(key, self.default)

        content = canned.get("content", "")
        extension = canned.get("x_corollary")

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        self._sse(sse_chunk({"role": "assistant", "content": ""}))
        if self.first_delta_delay_s:
            time.sleep(self.first_delta_delay_s)
        # SPEC §8: chunk boundaries are rendered lines, and "every chunk after
        # the first carries its leading `\n`, so concatenating all deltas
        # reproduces `content` byte-for-byte".
        lines = content.split("\n") if content else []
        for index, line in enumerate(lines):
            self._sse(sse_chunk({"content": line if index == 0 else "\n" + line}))
        self._sse(sse_chunk({}, finish="stop", extension=extension))
        self.wfile.write(b"data: [DONE]\n\n")
        self.close_connection = True


class ServerFixture:
    def __init__(self, handler) -> None:
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self) -> str:
        self.thread.start()
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}"

    def __exit__(self, *exc) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def oracle_extension(task: dict) -> dict:
    """A perfect kernel response, synthesized from the book's own record.

    The receipt carries one key the book does NOT pin, so a run that scores
    correct has exercised the subset assertion rather than an equality.
    """

    expected = task["expected"]
    receipt = dict(expected.get("receipt_expect") or {})
    receipt["unpinned_extra"] = "the wire may carry more than a task pins"
    extension = {
        "schema": "corollary.chat/1",
        "profile": task["profile"],
        "route": task.get("route_expect") or "resolver",
        "status": expected["status_expect"],
        "detail": "stub",
        "evidence": [],
        "receipt": receipt,
        "session": {"profile_session_id": "stub"},
    }
    if expected.get("need_expect"):
        need = dict(expected["need_expect"])
        need.setdefault("prompt", "stub prompt")
        extension["need"] = need
    return extension


def oracle_table(tasks) -> dict[str, dict]:
    """Canned perfect answers for half A, keyed by the turn that draws them."""

    table: dict[str, dict] = {}
    for task in tasks:
        final = task["turns"][-1]["content"]
        table[final] = {
            "content": "\n".join(task["expected"]["content_must_contain"]),
            "x_corollary": oracle_extension(task),
        }
    for task in tasks:
        for index, turn in enumerate(task["turns"]):
            if turn.get("expected_status") != "waiting":
                continue
            if index == len(task["turns"]) - 1 or turn["content"] in table:
                continue
            table[turn["content"]] = {
                "content": "stub clarification question",
                "x_corollary": {
                    "schema": "corollary.chat/1",
                    "profile": task["profile"],
                    "status": "waiting",
                    "need": {"slot": "egg_color", "prompt": "stub prompt"},
                    "receipt": {},
                },
            }
    return table


def _real_tokenizers():
    """Import the installed `tokenizers` package, not a repo shadow.

    Several test modules prepend `experiments/` to sys.path for their own
    imports, and `experiments/tokenizers.py` (the 2026-08 pair-encoding
    experiment) then shadows the installed package for every module that
    runs after them in the same suite process. The v0.17.0 gate's first
    full run went red on exactly this — five setUpClass ImportErrors that
    no standalone run of this file could reproduce. Import by site-packages
    priority so this file's tests mean the same thing in both processes.
    """

    import importlib
    import sysconfig

    shadow = sys.modules.get("tokenizers")
    if shadow is not None and "site-packages" not in str(
        getattr(shadow, "__file__", "") or ""
    ):
        for name in [m for m in sys.modules if m.split(".")[0] == "tokenizers"]:
            del sys.modules[name]
    purelib = sysconfig.get_paths()["purelib"]
    saved = list(sys.path)
    sys.path.insert(0, purelib)
    try:
        return importlib.import_module("tokenizers")
    finally:
        sys.path[:] = saved


def tiny_tokenizer(path: Path) -> str:
    """A real `tokenizers` file, so the digest gate is exercised for real."""

    tokenizers_pkg = _real_tokenizers()
    Tokenizer = tokenizers_pkg.Tokenizer
    WordLevel = tokenizers_pkg.models.WordLevel
    Whitespace = tokenizers_pkg.pre_tokenizers.Whitespace

    tokenizer = Tokenizer(WordLevel(vocab={"[UNK]": 0}, unk_token="[UNK]"))
    tokenizer.pre_tokenizer = Whitespace()
    tokenizer.save(str(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def baseline_with_tokenizer(directory: Path, tokenizer_path: Path, digest: str) -> Path:
    manifest = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    manifest["tokenizer"]["file"] = str(tokenizer_path)
    manifest["tokenizer"]["sha256"] = digest
    out = directory / "baseline.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out


def turn(content: str = "", status: str | None = None, **extension) -> mt.TurnResult:
    payload = dict(extension)
    if status is not None:
        payload["status"] = status
    return mt.TurnResult(
        content=content,
        x_corollary=payload or None,
        ttft_s=0.01,
        elapsed_s=0.02,
        chunk_count=1,
        finish_reason="stop",
        http_status=200,
    )


# ---------------------------------------------------------------------------
# transport
# ---------------------------------------------------------------------------


class TheTransportReassemblesWhatTheSpecPromised(unittest.TestCase):
    def test_deltas_concatenate_byte_for_byte(self) -> None:
        content = "level      : typed\nmember     : a.b.c\nledger     : reports/x.json"
        StubHandler.table = {"ask": {"content": content, "x_corollary": {"status": "found"}}}
        StubHandler.first_delta_delay_s = 0.0
        with ServerFixture(StubHandler) as url:
            result = mt.post_stream(
                url,
                {"model": "corollary/kernel",
                 "messages": [{"role": "user", "content": "ask"}],
                 "stream": True},
                timeout=10,
            )
        self.assertIsNone(result.error)
        self.assertEqual(result.content, content)
        self.assertEqual(result.finish_reason, "stop")
        self.assertEqual(result.x_corollary, {"status": "found"})

    def test_an_empty_answer_reassembles_to_the_empty_string(self) -> None:
        """Refusals render nothing; the reader must not invent a newline."""

        StubHandler.table = {"ask": {"content": "", "x_corollary": {"status": "exhausted"}}}
        with ServerFixture(StubHandler) as url:
            result = mt.post_stream(
                url,
                {"model": "corollary/kernel",
                 "messages": [{"role": "user", "content": "ask"}],
                 "stream": True},
                timeout=10,
            )
        self.assertEqual(result.content, "")
        self.assertIsNone(result.ttft_s)

    def test_ttft_is_the_first_content_delta_not_the_first_chunk(self) -> None:
        StubHandler.table = {"ask": {"content": "one\ntwo", "x_corollary": {"status": "found"}}}
        StubHandler.first_delta_delay_s = 0.30
        try:
            with ServerFixture(StubHandler) as url:
                result = mt.post_stream(
                    url,
                    {"model": "corollary/kernel",
                     "messages": [{"role": "user", "content": "ask"}],
                     "stream": True},
                    timeout=10,
                )
        finally:
            StubHandler.first_delta_delay_s = 0.0
        self.assertIsNotNone(result.ttft_s)
        # The role chunk arrives immediately; the first *content* delta does
        # not. A stopwatch that timed the first chunk would read ~0 here.
        self.assertGreaterEqual(result.ttft_s, 0.25)
        self.assertGreaterEqual(result.elapsed_s, result.ttft_s)

    def test_the_client_sends_user_turns_in_order_one_request_per_turn(self) -> None:
        task = {"turns": [{"role": "user", "content": "a"},
                          {"role": "user", "content": "b"}]}
        self.assertEqual(
            mt.kernel_requests(task),
            [
                [{"role": "user", "content": "a"}],
                [{"role": "user", "content": "a"}, {"role": "user", "content": "b"}],
            ],
        )


# ---------------------------------------------------------------------------
# scoring mechanics
# ---------------------------------------------------------------------------


class SubsetAssertionsAreSubsets(unittest.TestCase):
    """Book, `scoring_rules.receipt_subset`."""

    def test_absent_keys_are_unconstrained(self) -> None:
        self.assertTrue(mt.subset_ok({"a": 1}, {"a": 1, "b": 2}))

    def test_every_named_key_must_match(self) -> None:
        self.assertFalse(mt.subset_ok({"a": 1}, {"a": 2, "b": 1}))
        self.assertFalse(mt.subset_ok({"a": 1}, {"b": 1}))

    def test_nested_receipt_dicts_recurse(self) -> None:
        expect = {"binding": {"slot": "egg_color", "value": "silver"}}
        actual = {
            "binding": {"slot": "egg_color", "value": "silver", "lifetime": "turn"},
            "derivation": "user-frame",
        }
        self.assertTrue(mt.subset_ok(expect, actual))
        actual["binding"]["value"] = "copper"
        self.assertFalse(mt.subset_ok(expect, actual))

    def test_pinned_lists_compare_whole(self) -> None:
        expect = {"member_ids": ["a", "b"]}
        self.assertTrue(mt.subset_ok(expect, {"member_ids": ["a", "b"]}))
        self.assertFalse(mt.subset_ok(expect, {"member_ids": ["a", "b", "c"]}))

    def test_a_receipt_the_wire_omitted_fails_rather_than_passing_empty(self) -> None:
        self.assertFalse(mt.subset_ok({"derivation": "session"}, {}))
        self.assertTrue(mt.subset_ok({}, {}))

    def test_a_real_book_task_scores_against_its_own_expected_record(self) -> None:
        task = next(t for t in HALF_A if t["kind"] == "corpus_definition")
        good = mt.score_kernel(
            task,
            [turn("\n".join(task["expected"]["content_must_contain"]),
                  **oracle_extension(task))],
        )
        self.assertTrue(good.correct)
        self.assertTrue(good.receipted)

        bad = mt.score_kernel(task, [turn("nothing useful", status="found")])
        self.assertFalse(bad.correct)
        self.assertFalse(bad.receipted)
        self.assertEqual(
            bad.missing_strings, task["expected"]["content_must_contain"]
        )


class TheClarificationLegIsGradedPerMarkedTurn(unittest.TestCase):
    """Book, `scoring_rules.clarification_leg`."""

    def _resume_task(self) -> dict:
        return next(
            t for t in HALF_A
            if t["kind"] == "clarification_due"
            and t.get("phase") == "resume"
            and t["profile"] == "corollary/conversation"
        )

    def test_a_resume_task_that_never_waited_fails_the_leg(self) -> None:
        task = self._resume_task()
        legs = mt.waiting_legs(
            task,
            [
                turn("silver", status="solved"),          # turn 1 did not wait
                turn("silver", status="solved",
                     receipt={"derivation": "user-frame"}),
            ],
        )
        self.assertEqual(len(legs), 1)
        self.assertEqual(legs[0]["turn_index"], 0)
        self.assertFalse(legs[0]["ok"])

    def test_a_waiting_turn_on_the_conversation_profile_needs_a_need(self) -> None:
        task = self._resume_task()
        without = mt.waiting_legs(
            task, [turn("a question?", status="waiting"), turn("silver", status="solved")]
        )
        self.assertFalse(without[0]["ok"])
        with_need = mt.waiting_legs(
            task,
            [
                turn("a question?", status="waiting",
                     need={"slot": "egg_color", "prompt": "which colour?"}),
                turn("silver", status="solved"),
            ],
        )
        self.assertTrue(with_need[0]["ok"])

    def test_an_ask_task_subset_asserts_the_books_need_expect(self) -> None:
        task = next(
            t for t in HALF_A
            if t["kind"] == "clarification_due" and t.get("phase") == "ask"
        )
        expect = task["expected"]["need_expect"]
        good = mt.waiting_legs(
            task,
            [turn(task["expected"]["content_must_contain"][0], status="waiting",
                  need={**expect, "prompt": "extra keys are unconstrained"})],
        )
        self.assertTrue(good[0]["ok"])
        wrong = mt.waiting_legs(
            task,
            [turn("q", status="waiting", need={"slot": "some_other_slot"})],
        )
        self.assertFalse(wrong[0]["ok"])

    def test_a_kernel_waiting_turn_is_satisfied_by_candidate_lines(self) -> None:
        """SPEC §6.2 emits no need record on the kernel profile."""

        task = {
            "profile": "corollary/kernel",
            "expected": {},
            "turns": [
                {"role": "user", "content": "double factorial",
                 "expected_status": "waiting"},
                {"role": "user", "content": "narrow word recursive"},
            ],
        }
        legs = mt.waiting_legs(
            task, [turn("candidate: a\ncandidate: b", status="waiting"), turn("x", status="found")]
        )
        self.assertTrue(legs[0]["ok"])
        empty = mt.waiting_legs(task, [turn("", status="waiting"), turn("x", status="found")])
        self.assertFalse(empty[0]["ok"])


class TheRefusalTimeChargeIsAPostPass(unittest.TestCase):
    """DESIGN §3's frozen anti-shirking rule."""

    def _records(self) -> list[dict]:
        return [
            {"task_id": "slow-correct", "answerable": True, "correct": True,
             "elapsed_s": 2.0, "tokens": 40, "useful_tokens": 40,
             "status": "found"},
            {"task_id": "fast-refusal", "answerable": True, "correct": False,
             "elapsed_s": 0.01, "tokens": 0, "useful_tokens": 0,
             "status": "exhausted"},
            {"task_id": "fast-wrong-answer", "answerable": True, "correct": False,
             "elapsed_s": 0.02, "tokens": 30, "useful_tokens": 0,
             "status": "found"},
            {"task_id": "a-refusal-task", "answerable": False, "correct": True,
             "elapsed_s": 0.01, "tokens": 0, "useful_tokens": 0,
             "status": "exhausted"},
        ]

    def test_a_refused_answerable_task_is_charged_the_slowest_correct_answer(self) -> None:
        records = self._records()
        charge = mt.charge_refusals(records, "kernel")
        by_id = {r["task_id"]: r for r in records}
        self.assertEqual(charge["slowest_correct_answer_s"], 2.0)
        self.assertEqual(by_id["fast-refusal"]["charged_elapsed_s"], 2.0)
        self.assertTrue(by_id["fast-refusal"]["refusal_charge_applied"])
        self.assertEqual(by_id["fast-refusal"]["perceived_tps"], 0.0)

    def test_speed_at_being_wrong_keeps_its_own_clock_and_scores_zero(self) -> None:
        records = self._records()
        mt.charge_refusals(records, "kernel")
        wrong = next(r for r in records if r["task_id"] == "fast-wrong-answer")
        self.assertFalse(wrong["refusal_charge_applied"])
        self.assertEqual(wrong["charged_elapsed_s"], 0.02)
        self.assertEqual(wrong["perceived_tps"], 0.0)

    def test_a_refusal_task_is_never_charged_because_it_is_not_answerable(self) -> None:
        records = self._records()
        mt.charge_refusals(records, "kernel")
        row = next(r for r in records if r["task_id"] == "a-refusal-task")
        self.assertFalse(row["refusal_charge_applied"])
        self.assertEqual(row["charged_elapsed_s"], 0.01)

    def test_a_certified_bounded_negative_is_an_answer_and_is_not_charged(self) -> None:
        """Book, `scoring_rules.bounded_negative_is_an_answer`."""

        records = [
            {"task_id": "slow-correct", "answerable": True, "correct": True,
             "elapsed_s": 3.0, "tokens": 40, "useful_tokens": 40, "status": "found"},
            {"task_id": "unreachable", "answerable": True, "correct": True,
             "elapsed_s": 0.05, "tokens": 25, "useful_tokens": 25,
             "status": "exhausted"},
        ]
        mt.charge_refusals(records, "kernel")
        row = next(r for r in records if r["task_id"] == "unreachable")
        self.assertFalse(row["refusal_charge_applied"])
        self.assertEqual(row["charged_elapsed_s"], 0.05)
        self.assertEqual(row["perceived_tps"], 500.0)

    def test_on_a_baseline_arm_only_an_empty_answer_counts_as_a_refusal(self) -> None:
        records = [
            {"task_id": "slow-correct", "answerable": True, "correct": True,
             "elapsed_s": 5.0, "tokens": 40, "useful_tokens": 40, "status": None},
            {"task_id": "said-nothing", "answerable": True, "correct": False,
             "elapsed_s": 0.4, "tokens": 0, "useful_tokens": 0, "status": None},
            {"task_id": "said-something-wrong", "answerable": True, "correct": False,
             "elapsed_s": 0.4, "tokens": 90, "useful_tokens": 0, "status": None},
        ]
        mt.charge_refusals(records, "b-grounded")
        by_id = {r["task_id"]: r for r in records}
        self.assertTrue(by_id["said-nothing"]["refusal_charge_applied"])
        self.assertEqual(by_id["said-nothing"]["charged_elapsed_s"], 5.0)
        self.assertFalse(by_id["said-something-wrong"]["refusal_charge_applied"])


def synthetic_record(task_id: str, **overrides) -> dict:
    """A per-task record with every key `summarize` and the reconciler read."""

    record = {
        "task_id": task_id,
        "kind": "corpus_definition",
        "answerable": True,
        "applicable": True,
        "correct": True,
        "receipted": True,
        "useful_tokens": 100,
        "tokens": 100,
        "elapsed_s": 1.0,
        "charged_elapsed_s": 1.0,
        "perceived_tps": 100.0,
        "ttft_s": 0.1,
        "status": "found",
        "refusal_gate_ok": None,
        "waiting_legs": [],
    }
    record.update(overrides)
    return record


class TheTwoReadingsOfPerceivedThroughputAreBothReported(unittest.TestCase):
    """H-1, H-2 and M-3, on records this test controls end to end."""

    def _records(self) -> list[dict]:
        return [
            synthetic_record("fast", useful_tokens=100, elapsed_s=1.0,
                             charged_elapsed_s=1.0, perceived_tps=100.0,
                             ttft_s=0.10),
            synthetic_record("slow", useful_tokens=100, elapsed_s=4.0,
                             charged_elapsed_s=4.0, perceived_tps=25.0,
                             ttft_s=0.40),
            synthetic_record("refused", correct=False, receipted=False,
                             useful_tokens=0, tokens=0, elapsed_s=0.01,
                             charged_elapsed_s=4.0, perceived_tps=0.0,
                             ttft_s=0.001, status="exhausted"),
            synthetic_record("a-refusal-task", kind="refusal_due",
                             answerable=False, useful_tokens=0, tokens=0,
                             elapsed_s=0.02, charged_elapsed_s=0.02,
                             perceived_tps=0.0, ttft_s=0.002,
                             status="exhausted", refusal_gate_ok=True),
        ]

    def test_the_gate_statistic_is_the_median_of_per_task_ratios(self) -> None:
        summary = mt.summarize(self._records(), BOOK, "kernel")
        # 100, 25, 0 -> median 25
        self.assertEqual(summary["median_perceived_throughput_tps"], 25.0)

    def test_the_aggregate_is_the_section_3_ratio_of_sums(self) -> None:
        records = self._records()
        charge = {"tasks_charged": ["refused"], "slowest_correct_answer_s": 4.0}
        summary = mt.summarize(records, BOOK, "kernel")
        summary["median_perceived_throughput_tps_materials_fit"] = None
        block = mt.reconcile_metrics(records, summary, charge)
        # 200 useful tokens over 1 + 4 + 4 charged seconds.
        self.assertEqual(block["aggregate_useful_tokens"], 200)
        self.assertEqual(block["aggregate_charged_elapsed_s"], 9.0)
        self.assertEqual(block["aggregate_perceived_tps"], round(200 / 9, 6))

    def test_the_block_says_the_charge_is_inert_under_the_median(self) -> None:
        records = self._records()
        charge = {"tasks_charged": ["refused"], "slowest_correct_answer_s": 4.0}
        summary = mt.summarize(records, BOOK, "kernel")
        summary["median_perceived_throughput_tps_materials_fit"] = None
        block = mt.reconcile_metrics(records, summary, charge)
        self.assertTrue(block["under_the_median"]["refusal_time_charge_inert"])
        self.assertTrue(
            block["under_the_median"]["non_answerable_elapsed_excluded"]
        )
        self.assertEqual(block["under_the_median"]["non_answerable_tasks"], 1)
        self.assertEqual(block["under_the_median"]["tasks_charged"], ["refused"])
        # and the charge really is inert: move it and the median does not budge
        for record in records:
            if record["task_id"] == "refused":
                record["charged_elapsed_s"] = 40.0
        moved = mt.summarize(records, BOOK, "kernel")
        self.assertEqual(
            moved["median_perceived_throughput_tps"],
            summary["median_perceived_throughput_tps"],
        )

    def test_both_design_sentences_are_quoted_in_the_block(self) -> None:
        records = self._records()
        summary = mt.summarize(records, BOOK, "kernel")
        summary["median_perceived_throughput_tps_materials_fit"] = None
        block = mt.reconcile_metrics(records, summary, {"tasks_charged": []})
        self.assertIn("median perceived throughput", block["design_sentence_t4"])
        self.assertIn("frozen time charge", block["design_sentence_section_3"])
        self.assertIn("DESIGN-grounded-throughput 6 T4", block["design_sentence_t4"])
        self.assertIn(
            "DESIGN-grounded-throughput 3", block["design_sentence_section_3"]
        )

    def test_ttft_is_time_to_first_USEFUL_token_and_ttfa_is_not(self) -> None:
        """H-2. A refusal's first byte is not a useful token."""

        summary = mt.summarize(self._records(), BOOK, "kernel")
        # useful-bearing tasks: 0.10 and 0.40 -> median 0.25
        self.assertEqual(summary["median_ttft_s"], 0.25)
        # every answerable task, including the 0.001 s refusal -> median 0.10
        self.assertEqual(summary["median_ttfa_s"], 0.10)
        self.assertIn("useful_tokens > 0", summary["median_ttft_task_set"])
        self.assertIn("any-token", summary["median_ttfa_task_set"])

    def test_elapsed_totals_name_their_task_sets(self) -> None:
        """M-3."""

        summary = mt.summarize(self._records(), BOOK, "kernel")
        self.assertEqual(summary["elapsed_total_s"], 9.02)
        self.assertEqual(summary["elapsed_total_answerable_s"], 9.0)
        self.assertIn("non-answerable", summary["elapsed_total_task_set"])

    def test_the_secondary_median_is_restricted_to_materials_that_fit(self) -> None:
        """C-1(c)."""

        records = self._records()
        for record in records:
            record["materials_tokens"] = 10
        records[1]["materials_tokens"] = 10_000_000  # the slow one cannot fit
        mt.apply_context_fit(records, 32768)
        summary = mt.summarize(records, BOOK, "kernel")
        self.assertEqual(summary["median_perceived_throughput_tps"], 25.0)
        # with the un-holdable task dropped: 100 and 0 -> median 50
        self.assertEqual(
            summary["median_perceived_throughput_tps_materials_fit"], 50.0
        )
        self.assertEqual(summary["materials_fit_tasks"], 2)
        self.assertNotIn("slow", summary["materials_fit_task_ids"])

    def test_an_unprobed_context_reads_as_unknown_not_as_fitting(self) -> None:
        records = self._records()
        for record in records:
            record["materials_tokens"] = 10
        mt.apply_context_fit(records, None)
        for record in records:
            if record["answerable"]:
                self.assertIsNone(record["materials_truncated"])
        summary = mt.summarize(records, BOOK, "kernel")
        self.assertEqual(summary["materials_fit_tasks"], 0)
        self.assertEqual(summary["materials_fit_known_for"], 0)
        self.assertIsNone(
            summary["median_perceived_throughput_tps_materials_fit"]
        )


class TheContextBoundPrefersWhatTheServerActuallySaid(unittest.TestCase):
    """C-1(b), and the fallback that keeps both arms on one task set."""

    def test_an_observed_length_wins_and_is_labelled_observed(self) -> None:
        bound, source = mt.context_bound_for(
            BASELINE, {"observed_context_length": 8192, "source": "/api/ps (x)"}
        )
        self.assertEqual(bound, 8192)
        self.assertTrue(source.startswith("observed:"))

    def test_the_manifest_configured_value_is_the_fallback(self) -> None:
        bound, source = mt.context_bound_for(
            BASELINE, {"observed_context_length": None}
        )
        self.assertEqual(
            bound, BASELINE["runtime"]["context"]["configured_tokens"]
        )
        self.assertEqual(bound, 32768)
        self.assertIn("configured_tokens", source)

    def test_the_probe_reads_api_ps_when_the_model_is_loaded(self) -> None:
        StubHandler.probes = []
        StubHandler.ps_context_length = 32768
        with ServerFixture(StubHandler) as url:
            report = mt.probe_context_length(url, "qwen3:4b-instruct", 10)
        self.assertEqual(report["observed_context_length"], 32768)
        self.assertIn("/api/ps", report["source"])
        self.assertEqual(report["matched_model"], "qwen3:4b-instruct")
        self.assertEqual(report["errors"], [])

    def test_it_falls_back_to_api_show_and_says_that_is_weaker(self) -> None:
        StubHandler.probes = []
        StubHandler.ps_context_length = None
        try:
            with ServerFixture(StubHandler) as url:
                report = mt.probe_context_length(url, "qwen3:4b-instruct", 10)
        finally:
            StubHandler.ps_context_length = 32768
        self.assertEqual(report["observed_context_length"], 262144)
        self.assertIn("NOT the served context", report["source"])
        self.assertTrue(report["errors"])
        self.assertEqual(StubHandler.probes, ["/api/ps", "/api/show"])

    def test_an_unreachable_server_records_the_failure_and_no_number(self) -> None:
        report = mt.probe_context_length("http://127.0.0.1:1", "m", 0.25)
        self.assertIsNone(report["observed_context_length"])
        self.assertEqual(len(report["errors"]), 2)


class TheSamplingBlockSaysWhatActuallyApplies(unittest.TestCase):
    """H-4 and C-1(d)."""

    def test_the_source_sentence_is_the_probed_one(self) -> None:
        self.assertEqual(
            mt.SAMPLING_SOURCE,
            "applied by the ollama model manifest; /v1 ignores top_k and "
            "repeat_penalty (verified 2026-08-22)",
        )

    def test_the_false_extra_body_field_claim_is_gone(self) -> None:
        """C-1(d). The comment that said /v1 accepts top_k was wrong."""

        source = STOPWATCH.read_text(encoding="utf-8")
        self.assertNotIn("ollama accepts it as an extra body field", source)
        self.assertIn("ignores", mt.sampling_body.__doc__)
        self.assertIn("Requested, not necessarily applied", mt.sampling_body.__doc__)


class TheBSideRuleStripsOnlyTheKernelsLabelPadding(unittest.TestCase):
    """B_SIDE_CORRECTNESS_RULE, against the paddings the book really uses."""

    def test_the_books_paddings_are_exactly_the_pinned_set(self) -> None:
        found = set()
        for task in BOOK["tasks"]:
            for string in task["expected"]["content_must_contain"]:
                match = mt.LABEL_PADDING.match(string)
                if match:
                    found.add(match.group(0))
        self.assertEqual(sorted(found), BOOK_LABEL_PADDINGS)

    def test_every_padding_strips_to_something_shorter_and_nonempty(self) -> None:
        for padding in BOOK_LABEL_PADDINGS:
            with self.subTest(padding=padding):
                self.assertEqual(mt.strip_label(padding + "VALUE"), "VALUE")

    def test_the_worked_example_from_the_rule(self) -> None:
        self.assertEqual(mt.strip_label("exact      : 449"), "449")

    def test_unlabeled_strings_are_untouched(self) -> None:
        for string in (
            "Quadratic Formula",
            "physics.frames.galilean_velocity_addition",
            "(the target IS the initial state)",
            "no corpus statement was consulted",
            "ann observed  located_in(ball) = box",
        ):
            with self.subTest(string=string):
                self.assertEqual(mt.strip_label(string), string)

    def test_a_baseline_that_says_the_number_is_correct(self) -> None:
        task = next(t for t in HALF_A if t["kind"] == "exact_value")
        value = mt.strip_label(
            next(s for s in task["expected"]["content_must_contain"]
                 if s.startswith("exact"))
        )
        expression = mt.strip_label(
            next(s for s in task["expected"]["content_must_contain"]
                 if s.startswith("expression"))
        )
        prose = f"The expression {expression} evaluates to {value}."
        self.assertTrue(mt.score_baseline(task, prose).correct)
        self.assertFalse(mt.score_baseline(task, "I am not sure.").correct)

    def test_a_baseline_is_never_credited_with_a_receipt(self) -> None:
        task = next(t for t in HALF_A if t["kind"] == "corpus_definition")
        scored = mt.score_baseline(
            task, "\n".join(task["expected"]["content_must_contain"])
        )
        self.assertTrue(scored.correct)
        self.assertFalse(scored.receipted)


class TheDerangementIsDeterministicAndHasNoFixedPoints(unittest.TestCase):
    """DESIGN §7 C2."""

    def test_no_element_maps_to_itself(self) -> None:
        for count in (2, 3, 7, 45, 94):
            with self.subTest(count=count):
                order = mt.derangement(count, seed=0xC0FFEE)
                self.assertEqual(sorted(order), list(range(count)))
                self.assertEqual([i for i, v in enumerate(order) if v == i], [])

    def test_the_same_seed_gives_the_same_permutation(self) -> None:
        self.assertEqual(
            mt.derangement(45, seed=12345), mt.derangement(45, seed=12345)
        )
        self.assertNotEqual(
            mt.derangement(45, seed=12345), mt.derangement(45, seed=54321)
        )

    def test_one_task_cannot_be_deranged_and_says_so(self) -> None:
        with self.assertRaises(mt.Refused):
            mt.derangement(1, seed=1)

    def test_the_shuffle_keeps_the_clock_and_moves_the_answer(self) -> None:
        tasks = [t for t in HALF_A if t["kind"] == "corpus_definition"][:4]
        observed = {
            task["task_id"]: [
                mt.TurnResult(
                    content=task["task_id"],
                    x_corollary={"status": "found"},
                    ttft_s=index / 100,
                    elapsed_s=(index + 1) / 10,
                )
            ]
            for index, task in enumerate(tasks)
        }
        clocks = {k: v[0].elapsed_s for k, v in observed.items()}
        control = mt.apply_shuffle(tasks, observed, "a" * 64)
        self.assertEqual(control["fixed_points"], [])
        self.assertEqual(control["answerable_tasks_permuted"], 4)
        self.assertEqual(len(control["mapping_digest"]), 64)
        for task in tasks:
            key = task["task_id"]
            self.assertEqual(observed[key][0].elapsed_s, clocks[key])
            self.assertNotEqual(observed[key][0].content, key)


# ---------------------------------------------------------------------------
# B-grounded materials
# ---------------------------------------------------------------------------


class MaterialsComeFromTheArtifactRefsAndNowhereElse(unittest.TestCase):
    """Manifest, `arms.B-grounded.context_rule`."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.materials = mt.Materials(REPO)

    def test_a_corpus_definition_injects_the_node_record(self) -> None:
        task = next(t for t in HALF_A if t["kind"] == "corpus_definition")
        text, skipped = self.materials.for_task(task)
        self.assertEqual(skipped, [])
        record = json.loads(text)
        ref = task["expected"]["artifact_refs"][0]
        self.assertEqual(record["statement_id"], ref.split("#", 1)[1])
        for string in task["expected"]["content_must_contain"]:
            self.assertIn(string, text)

    def test_a_computed_task_gets_no_materials_rather_than_invented_ones(self) -> None:
        task = next(t for t in HALF_A if t["kind"] == "exact_value")
        text, _ = self.materials.for_task(task)
        self.assertEqual(text, "none")

    def test_a_session_derived_task_gets_no_materials(self) -> None:
        task = next(t for t in HALF_A if t["kind"] == "belief_query")
        text, _ = self.materials.for_task(task)
        self.assertEqual(text, "none")

    def test_a_twin_task_injects_the_group_entry_not_the_whole_ledger(self) -> None:
        task = next(t for t in HALF_A if t["kind"] == "twin_lookup")
        text, _ = self.materials.for_task(task)
        block = json.loads(text)
        self.assertEqual(block["group_index"], task["ledger_group"]["group_index"])
        self.assertEqual(block["level"], task["ledger_group"]["level"])
        members = {m["statement_id"] for m in block["group"]["members"]}
        self.assertEqual(
            members, set(task["expected"]["receipt_expect"]["member_ids"])
        )
        # "not whole ledger files": reports/signature_matches.json is 4.8 MB.
        self.assertLess(len(text), 20000)

    def test_the_prompt_template_is_filled_verbatim(self) -> None:
        task = next(t for t in HALF_A if t["kind"] == "exact_value")
        messages = mt.grounded_messages(task, BASELINE, "none")
        template = BASELINE["arms"]["B-grounded"]["prompt_template"]
        self.assertEqual(messages[0]["content"], template["system"])
        self.assertTrue(messages[1]["content"].startswith("MATERIALS:\nnone"))
        self.assertIn(task["turns"][0]["content"], messages[1]["content"])

    def test_the_ungrounded_arm_sends_the_turns_verbatim(self) -> None:
        task = next(t for t in HALF_A if t["kind"] == "corpus_definition")
        self.assertEqual(
            mt.ungrounded_messages(task),
            [{"role": t["role"], "content": t["content"]} for t in task["turns"]],
        )

    def test_the_sampling_body_is_the_manifests_and_carries_top_k(self) -> None:
        body = mt.sampling_body(BASELINE)
        self.assertEqual(body["temperature"], BASELINE["sampling"]["temperature"])
        self.assertEqual(body["top_k"], BASELINE["sampling"]["top_k"])
        self.assertEqual(mt.baseline_model_name(BASELINE), "qwen3:4b-instruct")


class TheClosureMaterialsNameTheirDeviation(unittest.TestCase):
    def test_a_closure_task_injects_registration_routes_and_states(self) -> None:
        task = next(t for t in HALF_A if t["kind"] == "closure_reachability")
        text, skipped = mt.Materials(REPO).for_task(task)
        self.assertEqual(skipped, [])
        self.assertIn('"world_id"', text)
        self.assertIn('"routes"', text)
        self.assertIn('"states"', text)
        self.assertIn(task["expected"]["receipt_expect"]["closure_digest"], text)

    def test_the_committed_closure_report_carries_no_canonical_routes_key(self) -> None:
        """The contradiction this implementation had to resolve, pinned.

        The parent instruction and the manifest speak of the closure's
        "routes"; the committed reports have no `canonical_routes` field.
        What they hold are `convergence_cells`' primary/alternate routes, and
        that is what the grounded arm injects. If a future closure report
        grows a real `canonical_routes` array, this test goes red and the
        materials rule should be revisited rather than silently widened.
        """

        report = json.loads(
            (REPO / "reports" / "closures" / "story.golden_chicken.closure.json")
            .read_text(encoding="utf-8")
        )
        self.assertNotIn("canonical_routes", report)
        self.assertIn("convergence_cells", report)
        self.assertIn("states", report)


# ---------------------------------------------------------------------------
# the tokenizer pin, and the refusals that precede any timing
# ---------------------------------------------------------------------------


class TheTokenizerPinRefusesRatherThanApproximates(unittest.TestCase):
    """Manifest, `tokenizer.policy`: REFUSES (exit 2), cannot-verify."""

    def _run(self, baseline: Path, out: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [PY, str(STOPWATCH), "--book", str(BOOK_PATH),
             "--baseline", str(baseline), "--system", "kernel",
             "--url", "http://127.0.0.1:1", "--half", "A", "--out", str(out)],
            capture_output=True, text=True, cwd=REPO, timeout=300,
        )

    def test_a_wrong_digest_exits_2_with_the_cannot_verify_sentence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tokenizer = root / "tokenizer.json"
            tiny_tokenizer(tokenizer)
            baseline = baseline_with_tokenizer(root, tokenizer, "0" * 64)
            proc = self._run(baseline, root / "result.json")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("cannot-verify", proc.stderr)
        self.assertIn("0" * 64, proc.stderr)
        self.assertFalse((Path(tempfile.gettempdir()) / "result.json").exists())

    def test_an_absent_tokenizer_exits_2_and_never_approximates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = baseline_with_tokenizer(root, root / "absent.json", "0" * 64)
            proc = self._run(baseline, root / "result.json")
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("cannot-verify", proc.stderr)
        self.assertIn("missing tokenizer file", proc.stderr)


class TheRunRefusesBeforeItCanProduceAVoidNumber(unittest.TestCase):
    """Every refusal here happens before a socket is opened.

    H-3. The earlier version of this class leaned on the pinned tokenizer
    being absent from the developer's `.runtime/` -- a fact about one
    checkout, which would flip the moment somebody downloaded the file and
    turn a seal test green for the wrong reason. It now supplies its OWN
    baseline manifest whose tokenizer digest is deliberately wrong, so the
    refusal is caused by something this file controls. `--url` names a dead
    loopback port that is never dialed: every refusal below fires earlier
    than the warmup request.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.directory = tempfile.TemporaryDirectory()
        root = Path(cls.directory.name)
        tokenizer = root / "tokenizer.json"
        tiny_tokenizer(tokenizer)
        cls.wrong_digest = "0" * 64
        cls.baseline = baseline_with_tokenizer(root, tokenizer, cls.wrong_digest)
        cls.root = root

    @classmethod
    def tearDownClass(cls) -> None:
        cls.directory.cleanup()

    def _run(self, extra: list[str], out: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [PY, str(STOPWATCH), "--book", str(BOOK_PATH),
             "--baseline", str(self.baseline), "--system", "kernel",
             "--url", "http://127.0.0.1:1", "--out", str(out)] + extra,
            capture_output=True, text=True, cwd=REPO, timeout=300,
        )

    def test_half_b_without_registered_is_refused(self) -> None:
        out = self.root / "half-b-unregistered.json"
        proc = self._run(["--half", "B"], out)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("half B is sealed", proc.stderr)
        self.assertNotIn("REGISTERED RUN", proc.stdout)
        self.assertFalse(out.exists())

    def test_half_b_with_registered_announces_then_still_refuses(self) -> None:
        """H-3. The loud line fires; the tokenizer pin stops the run anyway.

        The refusal is caused by a digest this test wrote, not by an absent
        file: the tokenizer exists and is a real `tokenizers` file, and the
        manifest pins the wrong sha256 for it. Nothing is timed, no socket is
        opened, and no half-B task is spent.
        """

        out = self.root / "half-b-registered.json"
        proc = self._run(["--half", "B", "--registered"], out)
        self.assertIn("REGISTERED RUN", proc.stdout)
        self.assertIn("half B's first and only execution", proc.stdout)
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn("cannot-verify", proc.stderr)
        self.assertIn(self.wrong_digest, proc.stderr)
        self.assertFalse(out.exists())

    def test_an_existing_out_file_is_not_overwritten(self) -> None:
        out = self.root / "occupied.json"
        out.write_text('{"already": "here"}', encoding="utf-8")
        proc = self._run([], out)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("refusing to overwrite", proc.stderr)
        self.assertIn("--overwrite", proc.stderr)
        self.assertEqual(json.loads(out.read_text(encoding="utf-8")),
                         {"already": "here"})

    def test_from_without_control_shuffle_is_refused(self) -> None:
        """M-5. `--from` derives C2; on its own it means nothing."""

        proc = self._run(
            ["--from", str(self.root / "nothing.json")], self.root / "o1.json"
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--control-shuffle", proc.stderr)

    def test_rendering_digest_drift_refuses_and_names_the_void(self) -> None:
        """SPEC §6: a rendering change after the seal voids the run."""

        book = json.loads(BOOK_PATH.read_text(encoding="utf-8"))
        book["rendering_module_digests"]["scripts/answer.py"] = "f" * 64
        drifted = self.root / "book.json"
        drifted.write_text(json.dumps(book), encoding="utf-8")
        proc = subprocess.run(
            [PY, str(STOPWATCH), "--book", str(drifted),
             "--baseline", str(self.baseline), "--system", "kernel",
             "--url", "http://127.0.0.1:1", "--half", "A",
             "--out", str(self.root / "drift.json")],
            capture_output=True, text=True, cwd=REPO, timeout=300,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("VOID WARNING", proc.stderr)
        self.assertIn("scripts/answer.py", proc.stderr)
        self.assertIn("--force-void", proc.stderr)

    def test_the_committed_book_revalidates_against_the_committed_tree(self) -> None:
        ok, drift = mt.revalidate_rendering_digests(BOOK, REPO)
        self.assertTrue(ok, drift)

    def test_control_shuffle_is_refused_on_any_arm_but_the_kernel(self) -> None:
        args = mt.build_parser().parse_args(
            ["--system", "b-grounded", "--out", "x", "--control-shuffle"]
        )
        with self.assertRaises(mt.Refused):
            mt.run(args)

    def test_a_short_task_set_refuses_rather_than_reporting_a_median(self) -> None:
        """M-4. The book's own arithmetic, quoted back at the run."""

        book = json.loads(BOOK_PATH.read_text(encoding="utf-8"))
        dropped = next(t for t in book["tasks"] if t["half"] == "A")
        book["tasks"] = [t for t in book["tasks"] if t is not dropped]
        short = self.root / "short-book.json"
        short.write_text(json.dumps(book), encoding="utf-8")
        proc = subprocess.run(
            [PY, str(STOPWATCH), "--book", str(short),
             "--baseline", str(self.baseline), "--system", "kernel",
             "--url", "http://127.0.0.1:1", "--half", "A",
             "--out", str(self.root / "short.json")],
            capture_output=True, text=True, cwd=REPO, timeout=300,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("does not match the book's own arithmetic", proc.stderr)
        self.assertIn("57", proc.stderr)
        self.assertIn("58", proc.stderr)

    def test_the_expected_counts_come_from_the_book_not_from_a_constant(self) -> None:
        for half in ("A", "B"):
            for system in ("kernel", "dump"):
                with self.subTest(half=half, system=system):
                    self.assertEqual(
                        mt.expected_task_count(BOOK, half, system),
                        BOOK["counts"]["by_half"][half],
                    )
            for system in ("b-grounded", "b-ungrounded"):
                with self.subTest(half=half, system=system):
                    self.assertEqual(
                        mt.expected_task_count(BOOK, half, system),
                        BOOK["counts"]["answerable_by_half"][half],
                    )

    def test_help_runs(self) -> None:
        proc = subprocess.run(
            [PY, str(STOPWATCH), "--help"],
            capture_output=True, text=True, cwd=REPO, timeout=120,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("--control-shuffle", proc.stdout)
        self.assertIn("--registered", proc.stdout)
        self.assertIn("--overwrite", proc.stdout)
        self.assertIn("--force-void", proc.stdout)
        self.assertIn("--from", proc.stdout)


class TheLoadGuardsRefuseAnUnpinnedAnswerKey(unittest.TestCase):
    """L-1, and the strict-type decision behind L-2."""

    def test_the_committed_book_pins_every_answerable_task(self) -> None:
        mt.validate_book_pins(BOOK)  # raises if not

    def test_an_answerable_task_pinning_nothing_is_refused(self) -> None:
        book = {
            "tasks": [
                {
                    "task_id": "corpus_definition/unpinned",
                    "kind": "corpus_definition",
                    "expected": {
                        "content_must_contain": [],
                        "receipt_expect": {},
                        "status_expect": "found",
                    },
                }
            ]
        }
        with self.assertRaises(mt.Refused) as caught:
            mt.validate_book_pins(book)
        self.assertIn("corpus_definition/unpinned", str(caught.exception))

    def test_a_refusal_task_pinning_no_prose_is_allowed(self) -> None:
        """`zero_token_turns`: refusal tasks carry an empty must-contain."""

        book = {
            "tasks": [
                {
                    "task_id": "refusal_due/x",
                    "kind": "refusal_due",
                    "expected": {"content_must_contain": [], "receipt_expect": {}},
                }
            ]
        }
        mt.validate_book_pins(book)

    def test_a_bool_never_satisfies_an_int_and_an_int_never_a_float(self) -> None:
        self.assertFalse(mt.subset_ok({"visited_states": 75}, {"visited_states": True}))
        self.assertFalse(mt.subset_ok({"horizon": 5}, {"horizon": 5.0}))
        self.assertFalse(mt.subset_ok({"flag": True}, {"flag": 1}))
        self.assertTrue(mt.subset_ok({"horizon": 5}, {"horizon": 5}))

    def test_strictness_cannot_be_laundered_through_a_container(self) -> None:
        self.assertFalse(mt.subset_ok({"ids": [1, 2]}, {"ids": [1, True]}))
        self.assertFalse(
            mt.subset_ok({"b": {"n": 1}}, {"b": {"n": 1.0}})
        )
        self.assertTrue(mt.subset_ok({"ids": ["a"]}, {"ids": ["a"]}))

    def test_the_committed_book_still_scores_under_the_strict_rule(self) -> None:
        for task in BOOK["tasks"]:
            expect = task["expected"].get("receipt_expect") or {}
            with self.subTest(task=task["task_id"]):
                self.assertTrue(mt.subset_ok(expect, json.loads(json.dumps(expect))))


# ---------------------------------------------------------------------------
# end to end, against the stub -- never against a real system
# ---------------------------------------------------------------------------


class TheStopwatchScoresAWholeHalfAgainstAStub(unittest.TestCase):
    """Half A only; every answer here is canned in this process."""

    @classmethod
    def setUpClass(cls) -> None:
        StubHandler.table = oracle_table(HALF_A)
        StubHandler.first_delta_delay_s = 0.0
        StubHandler.seen = []
        cls.fixture = ServerFixture(StubHandler)
        cls.url = cls.fixture.__enter__()
        cls.directory = tempfile.TemporaryDirectory()
        root = Path(cls.directory.name)
        tokenizer = root / "tokenizer.json"
        digest = tiny_tokenizer(tokenizer)
        cls.baseline = baseline_with_tokenizer(root, tokenizer, digest)
        cls.root = root

        cls.proc = subprocess.run(
            [PY, str(STOPWATCH), "--book", str(BOOK_PATH),
             "--baseline", str(cls.baseline), "--system", "kernel",
             "--url", cls.url, "--half", "A",
             "--out", str(root / "kernel.json")],
            capture_output=True, text=True, cwd=REPO, timeout=900,
        )
        path = root / "kernel.json"
        cls.result = (
            json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.fixture.__exit__(None, None, None)
        cls.directory.cleanup()

    def test_the_run_completed(self) -> None:
        self.assertEqual(self.proc.returncode, 0, self.proc.stdout + self.proc.stderr)
        self.assertIsNotNone(self.result)

    def test_the_stopwatch_asserts_its_own_process_stayed_engine_clean(self) -> None:
        """The runtime half of the boundary rule, read where it means something.

        An in-process `sys.modules` assertion inside this suite would be a
        statement about whichever test module imported first. So the
        stopwatch asserts its OWN interpreter and prints a line saying it
        did; this test reads the exit code and that line -- the same shape
        `tests/test_throughput_tasks.py` uses for the task-book builder.
        """

        self.assertIn(mt.CLEAN_IMPORTS_LINE, self.proc.stdout)

    def test_the_result_carries_the_schema_and_the_digests(self) -> None:
        self.assertEqual(self.result["schema"], "corollary.throughput-result/1")
        self.assertEqual(
            self.result["book_digest"], mt.canonical_lf_sha256(BOOK_PATH)
        )
        self.assertTrue(self.result["rendering_digests_revalidated"])
        self.assertEqual(
            self.result["scoring_rules_applied"], BOOK["scoring_rules"]
        )
        self.assertTrue(self.result["run"]["warmup"])
        self.assertFalse(self.result["run"]["registered"])
        self.assertEqual(self.result["run"]["half"], "A")

    def test_a_perfect_oracle_reads_as_perfect_on_every_gate(self) -> None:
        summary = self.result["summary"]
        self.assertEqual(summary["correctness_overall"]["rate"], 1.0)
        self.assertEqual(summary["refusal_gate"]["rate"], 1.0)
        self.assertEqual(summary["clarification_gate"]["rate"], 1.0)
        for kind, row in summary["correctness_by_kind"].items():
            with self.subTest(kind=kind):
                self.assertEqual(row["rate"], 1.0)

    def test_the_half_and_its_counts_match_the_books_own_arithmetic(self) -> None:
        measured = [r for r in self.result["per_task"] if r.get("applicable")]
        self.assertEqual(len(measured), BOOK["counts"]["by_half"]["A"])
        self.assertEqual(
            self.result["summary"]["answerable_tasks"],
            BOOK["counts"]["answerable_by_half"]["A"],
        )

    def test_refusal_and_clarification_tasks_earn_no_useful_tokens(self) -> None:
        """Book, `scoring_rules.zero_token_turns` and `per_kind_floor`."""

        for record in self.result["per_task"]:
            if record["kind"] in ("refusal_due", "clarification_due"):
                with self.subTest(task=record["task_id"]):
                    self.assertFalse(record["answerable"])
                    self.assertEqual(record["useful_tokens"], 0)

    def test_a_clarification_resume_answers_correctly_and_still_scores_zero(self) -> None:
        record = next(
            r for r in self.result["per_task"]
            if r["task_id"] == "clarification_due/resume/imperative_purple"
        )
        self.assertTrue(record["correct"])
        self.assertEqual(record["useful_tokens"], 0)
        self.assertEqual(len(record["turns"]), 2)
        self.assertEqual(record["waiting_legs"][0]["turn_index"], 0)

    def test_every_answerable_task_has_a_throughput_and_a_ttft(self) -> None:
        for record in self.result["per_task"]:
            if record.get("answerable"):
                with self.subTest(task=record["task_id"]):
                    self.assertGreater(record["useful_tokens"], 0)
                    self.assertIsNotNone(record["perceived_tps"])
                    self.assertIsNotNone(record["ttft_s"])
        self.assertGreater(
            self.result["summary"]["median_perceived_throughput_tps"], 0
        )

    def test_the_control_block_is_empty_on_an_uncontrolled_run(self) -> None:
        self.assertEqual(self.result["control"], {})

    def test_no_b_side_rule_is_recorded_on_a_kernel_run(self) -> None:
        self.assertNotIn("b_side_correctness_rule", self.result)

    def test_the_metric_reconciliation_block_carries_both_readings(self) -> None:
        """H-1."""

        block = self.result["metric_reconciliation"]
        summary = self.result["summary"]
        self.assertEqual(
            block["t4_gate_value_tps"],
            summary["median_perceived_throughput_tps"],
        )
        self.assertIn("median of the per-task ratio", block["t4_gate_statistic"])
        self.assertIn("DESIGN-grounded-throughput 6 T4", block["design_sentence_t4"])
        self.assertIn(
            "DESIGN-grounded-throughput 3", block["design_sentence_section_3"]
        )
        self.assertTrue(block["under_the_median"]["non_answerable_elapsed_excluded"])
        self.assertTrue(block["under_the_median"]["refusal_time_charge_inert"])
        self.assertGreater(block["under_the_median"]["non_answerable_elapsed_s"], 0)
        self.assertEqual(
            block["aggregate_useful_tokens"], summary["useful_tokens_total"]
        )
        self.assertEqual(
            block["aggregate_charged_elapsed_s"],
            summary["elapsed_total_answerable_s"],
        )
        self.assertAlmostEqual(
            block["aggregate_perceived_tps"],
            block["aggregate_useful_tokens"]
            / block["aggregate_charged_elapsed_s"],
            places=4,
        )

    def test_the_ttft_split_is_recorded_on_a_real_run(self) -> None:
        """H-2."""

        summary = self.result["summary"]
        self.assertIsNotNone(summary["median_ttft_s"])
        self.assertIsNotNone(summary["median_ttfa_s"])
        self.assertIn("useful", summary["median_ttft_task_set"])
        # a perfect oracle answers every answerable task, so the two series
        # are the same set here -- the names still have to be distinct
        self.assertIn("median_ttfa_s", summary)

    def test_the_secondary_median_is_labelled_exactly_as_the_manifest_declares(self) -> None:
        """C-1(c)."""

        summary = self.result["summary"]
        self.assertEqual(
            summary["pre_declared_secondary_label"],
            BASELINE["runtime"]["context"]["pre_declared_secondary"],
        )
        self.assertEqual(summary["materials_fit_bound_tokens"], 32768)
        self.assertIn("configured_tokens", summary["materials_fit_bound_source"])
        self.assertIsNotNone(
            summary["median_perceived_throughput_tps_materials_fit"]
        )

    def test_the_kernel_arm_carries_its_content_at_the_top_level_too(self) -> None:
        """The same recording guarantee, on the arm the bug did not show on."""

        for record in self.result["per_task"]:
            if not record.get("applicable"):
                continue
            with self.subTest(task=record["task_id"]):
                self.assertIn("content", record)
                self.assertEqual(
                    record["content"], record["turns"][-1]["content"]
                )
                self.assertEqual(
                    record["content_chars"], len(record["content"])
                )
                self.assertEqual(
                    record["x_corollary"], record["turns"][-1]["x_corollary"]
                )
                if record["answerable"]:
                    self.assertNotEqual(record["content"], "")

    def test_materials_tokens_are_recorded_for_every_answerable_task(self) -> None:
        """C-1(a). Counted with the pinned tokenizer, on every arm."""

        answerable = [r for r in self.result["per_task"] if r.get("answerable")]
        self.assertTrue(answerable)
        for record in answerable:
            with self.subTest(task=record["task_id"]):
                self.assertIn("materials_chars", record)
                self.assertIn("materials_tokens", record)
                self.assertIsInstance(record["materials_tokens"], int)
                self.assertIn(record["materials_truncated"], (True, False))

    def test_the_closure_tasks_are_the_ones_that_do_not_fit(self) -> None:
        """The truncation disclosure, as a fact about this half."""

        truncated = [
            r for r in self.result["per_task"] if r.get("materials_truncated")
        ]
        self.assertTrue(truncated, "half A has closure tasks; none was oversized")
        self.assertTrue(
            all(r["kind"] == "closure_reachability" for r in truncated),
            [r["task_id"] for r in truncated],
        )

    def test_the_context_probe_says_it_had_nothing_to_probe(self) -> None:
        probe = self.result["context_probe"]
        self.assertIsNone(probe["observed_context_length"])
        self.assertIn("serves no model", probe["errors"][0])
        self.assertEqual(
            self.result["context_pin"], BASELINE["runtime"]["context"]
        )

    def test_the_force_flags_are_recorded_separately(self) -> None:
        """M-2."""

        self.assertFalse(self.result["run"]["overwrote_existing_out"])
        self.assertFalse(self.result["run"]["forced_over_void"])
        self.assertIsNone(self.result["run"]["derived_offline_from"])

    def test_overwrite_replaces_the_file_and_records_that_it_did(self) -> None:
        """M-2, the positive leg."""

        out = self.root / "overwritten.json"
        out.write_text('{"stale": true}', encoding="utf-8")
        proc = subprocess.run(
            [PY, str(STOPWATCH), "--book", str(BOOK_PATH),
             "--baseline", str(self.baseline), "--system", "kernel",
             "--url", self.url, "--half", "A", "--overwrite", "--out", str(out)],
            capture_output=True, text=True, cwd=REPO, timeout=900,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        written = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(written["schema"], "corollary.throughput-result/1")
        self.assertTrue(written["run"]["overwrote_existing_out"])
        self.assertFalse(written["run"]["forced_over_void"])

    def test_force_void_records_the_void_instead_of_hiding_it(self) -> None:
        """M-2, the other positive leg: consent is recorded, not assumed."""

        book = json.loads(BOOK_PATH.read_text(encoding="utf-8"))
        book["rendering_module_digests"]["scripts/answer.py"] = "f" * 64
        drifted = self.root / "drifted-book.json"
        drifted.write_text(json.dumps(book), encoding="utf-8")
        out = self.root / "voided.json"
        proc = subprocess.run(
            [PY, str(STOPWATCH), "--book", str(drifted),
             "--baseline", str(self.baseline), "--system", "kernel",
             "--url", self.url, "--half", "A", "--force-void", "--out", str(out)],
            capture_output=True, text=True, cwd=REPO, timeout=900,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("VOID WARNING", proc.stderr)
        written = json.loads(out.read_text(encoding="utf-8"))
        self.assertTrue(written["run"]["forced_over_void"])
        self.assertFalse(written["rendering_digests_revalidated"])
        self.assertEqual(
            [row["module"] for row in written["rendering_digest_drift"]],
            ["scripts/answer.py"],
        )

    def test_c2_is_derived_offline_from_the_recorded_result(self) -> None:
        """M-5. The sealed half is asked once; C2 re-scores what it said."""

        out = self.root / "offline-c2.json"
        proc = subprocess.run(
            [PY, str(STOPWATCH), "--book", str(BOOK_PATH),
             "--baseline", str(self.baseline), "--system", "kernel",
             "--half", "A", "--control-shuffle",
             "--from", str(self.root / "kernel.json"), "--out", str(out)],
            capture_output=True, text=True, cwd=REPO, timeout=900,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        derived = json.loads(out.read_text(encoding="utf-8"))
        control = derived["control"]
        self.assertEqual(control["control"], "C2")
        self.assertTrue(control["derived_offline"])
        self.assertEqual(control["derived_from"], str(self.root / "kernel.json"))
        self.assertEqual(control["fixed_points"], [])
        self.assertIn("not asked a second time", control["no_re_execution"])
        self.assertEqual(derived["run"]["derived_offline_from"],
                         str(self.root / "kernel.json"))
        self.assertEqual(derived["summary"]["useful_tokens_total"], 0)
        self.assertEqual(
            derived["summary"]["median_perceived_throughput_tps"], 0.0
        )
        # The clocks are the ones the live run measured, task by task. They
        # can differ in the last microsecond on a multi-turn task, because
        # the live run sums unrounded seconds and the offline derivation sums
        # the per-turn values the file rounded to six places -- a rounding
        # artifact of the record, not a re-measurement.
        live = {r["task_id"]: r for r in self.result["per_task"]}
        for record in derived["per_task"]:
            if record.get("applicable"):
                with self.subTest(task=record["task_id"]):
                    self.assertAlmostEqual(
                        record["elapsed_s"],
                        live[record["task_id"]]["elapsed_s"],
                        places=5,
                    )

    def test_the_offline_derivation_and_the_live_shuffle_agree(self) -> None:
        """One derangement rule, seeded from the book, either way round."""

        live_out = self.root / "shuffled-again.json"
        subprocess.run(
            [PY, str(STOPWATCH), "--book", str(BOOK_PATH),
             "--baseline", str(self.baseline), "--system", "kernel",
             "--url", self.url, "--half", "A", "--control-shuffle",
             "--out", str(live_out)],
            capture_output=True, text=True, cwd=REPO, timeout=900, check=True,
        )
        live = json.loads(live_out.read_text(encoding="utf-8"))
        offline_out = self.root / "offline-c2-again.json"
        subprocess.run(
            [PY, str(STOPWATCH), "--book", str(BOOK_PATH),
             "--baseline", str(self.baseline), "--system", "kernel",
             "--half", "A", "--control-shuffle",
             "--from", str(self.root / "kernel.json"), "--out", str(offline_out)],
            capture_output=True, text=True, cwd=REPO, timeout=900, check=True,
        )
        offline = json.loads(offline_out.read_text(encoding="utf-8"))
        self.assertEqual(
            live["control"]["mapping_digest"], offline["control"]["mapping_digest"]
        )
        self.assertEqual(
            live["control"]["derangement_seed"],
            offline["control"]["derangement_seed"],
        )

    def test_the_offline_derivation_refuses_a_mismatched_source(self) -> None:
        offline = self.root / "offline-c2.json"
        if not offline.exists():
            self.skipTest("depends on the offline derivation having run")
        proc = subprocess.run(
            [PY, str(STOPWATCH), "--book", str(BOOK_PATH),
             "--baseline", str(self.baseline), "--system", "kernel",
             "--half", "A", "--control-shuffle", "--from", str(offline),
             "--out", str(self.root / "double.json")],
            capture_output=True, text=True, cwd=REPO, timeout=900,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("already a shuffled control", proc.stderr)

    def test_the_offline_derivation_refuses_the_wrong_half(self) -> None:
        args = mt.build_parser().parse_args(
            ["--system", "kernel", "--half", "B", "--registered",
             "--control-shuffle", "--from", str(self.root / "kernel.json"),
             "--baseline", str(self.baseline), "--out", str(self.root / "x.json")]
        )
        with self.assertRaises(mt.Refused) as caught:
            mt.run(args)
        self.assertIn("half-A run", str(caught.exception))

    def test_the_clean_imports_guard_runs_before_the_file_is_written(self) -> None:
        """L-5. A refused run leaves no result behind to be read anyway."""

        out = self.root / "never-written.json"
        original = dict(sys.modules)
        try:
            sys.modules["harness"] = object()  # type: ignore[assignment]
            with contextlib.redirect_stdout(io.StringIO()), \
                    contextlib.redirect_stderr(io.StringIO()) as err:
                code = mt.main(
                    ["--book", str(BOOK_PATH), "--baseline", str(self.baseline),
                     "--system", "kernel", "--url", self.url, "--half", "A",
                     "--out", str(out)]
                )
        finally:
            sys.modules.clear()
            sys.modules.update(original)
        self.assertEqual(code, 2)
        self.assertIn("an engine module was imported", err.getvalue())
        self.assertFalse(
            out.exists(),
            "a result written before the guard ran would be read anyway",
        )

    def test_the_shuffled_kernel_scores_approximately_zero(self) -> None:
        """DESIGN §7 C2, through the CLI, with the clocks left in place."""

        out = self.root / "shuffled.json"
        proc = subprocess.run(
            [PY, str(STOPWATCH), "--book", str(BOOK_PATH),
             "--baseline", str(self.baseline), "--system", "kernel",
             "--url", self.url, "--half", "A", "--control-shuffle",
             "--out", str(out)],
            capture_output=True, text=True, cwd=REPO, timeout=900,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        shuffled = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(shuffled["control"]["control"], "C2")
        self.assertEqual(shuffled["control"]["fixed_points"], [])
        self.assertEqual(len(shuffled["control"]["mapping_digest"]), 64)
        self.assertIn("1%", shuffled["control"]["voiding_sentence"])
        self.assertEqual(
            shuffled["summary"]["median_perceived_throughput_tps"], 0.0
        )
        self.assertEqual(shuffled["summary"]["useful_tokens_total"], 0)

    def test_the_baseline_arm_records_its_rule_and_its_not_applicables(self) -> None:
        """The B side, still against the stub: no model is ever contacted."""

        StubHandler.table = {
            t["turns"][-1]["content"]: {
                "content": "\n".join(
                    mt.strip_label(s)
                    for s in t["expected"]["content_must_contain"]
                ),
                "x_corollary": None,
            }
            for t in HALF_A
        }
        try:
            out = self.root / "ungrounded.json"
            proc = subprocess.run(
                [PY, str(STOPWATCH), "--book", str(BOOK_PATH),
                 "--baseline", str(self.baseline), "--system", "b-ungrounded",
                 "--url", self.url, "--half", "A", "--out", str(out)],
                capture_output=True, text=True, cwd=REPO, timeout=900,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            result = json.loads(out.read_text(encoding="utf-8"))
        finally:
            StubHandler.table = oracle_table(HALF_A)

        self.assertEqual(
            result["b_side_correctness_rule"], mt.B_SIDE_CORRECTNESS_RULE
        )
        measured = [r for r in result["per_task"] if r.get("applicable")]
        self.assertEqual(len(measured), BOOK["counts"]["answerable_by_half"]["A"])
        self.assertTrue(all(r["answerable"] for r in measured))
        self.assertTrue(all(not r["receipted"] for r in measured))
        skipped = [r for r in result["per_task"] if not r.get("applicable")]
        self.assertTrue(skipped)
        self.assertTrue(
            all("not-applicable" in r["reason"] for r in skipped)
        )
        self.assertEqual(result["summary"]["correctness_overall"]["rate"], 1.0)

        # H-4: what was asked for, and what actually governs it.
        arm = result["baseline_arm"]
        self.assertNotIn("sampling", arm)
        self.assertEqual(
            arm["sampling_requested"]["temperature"],
            BASELINE["sampling"]["temperature"],
        )
        self.assertEqual(arm["sampling_source"], mt.SAMPLING_SOURCE)

        # C-1(b): the arm probed the server it was about to time.
        self.assertEqual(result["context_probe"]["observed_context_length"], 32768)
        self.assertIn("/api/ps", result["context_probe"]["source"])
        self.assertEqual(result["summary"]["materials_fit_bound_tokens"], 32768)
        self.assertTrue(
            result["summary"]["materials_fit_bound_source"].startswith("observed:")
        )

        # M-1: the residuals the rule actually searched for.
        with_labels = [
            r for r in measured
            if any(entry["stripped"] for entry in r["b_residuals"])
        ]
        self.assertTrue(with_labels, "no task in half A pins a labelled line")
        for record in measured:
            with self.subTest(task=record["task_id"]):
                self.assertEqual(
                    [entry["pinned"] for entry in record["b_residuals"]],
                    next(
                        t["expected"]["content_must_contain"]
                        for t in HALF_A if t["task_id"] == record["task_id"]
                    ),
                )
                self.assertTrue(all(e["found"] for e in record["b_residuals"]))

        # An ungrounded arm holds no materials, so nothing can be truncated.
        self.assertTrue(all(r["materials_tokens"] == 0 for r in measured))
        self.assertTrue(all(r["materials_truncated"] is False for r in measured))


def unique_answer(task: dict) -> str:
    """A per-task string no scorer could produce by accident.

    Deliberately mixed: a line the book's rule WILL find, a line it will not,
    a non-ASCII character, and the task id, so a record that carries the
    wrong task's text, a truncated copy, or a re-encoded copy all read as
    failures rather than as passes.
    """

    pinned = task["expected"]["content_must_contain"]
    echo = mt.strip_label(pinned[0]) if pinned else "(nothing pinned)"
    return (
        f"answer for {task['task_id']}\n"
        f"{echo}\n"
        f"trailing prose the book never pinned — ünicode, 94\n"
    )


class ABaselineResultCarriesTheContentItScored(unittest.TestCase):
    """The 2026-08-22 recording bug, pinned so it cannot come back.

    A live half-A b-grounded trial produced per-task records whose `content`
    was the empty string while the scorer had plainly seen real text -- five
    `exact_value` tasks scored correct against it. The text was being written
    only inside `turns[]`, never at the top level of the record where a
    reader looks, so the arm's whole evidentiary surface read as blank.

    The regression this file asserts is the strong one: **every applicable
    record on a baseline arm carries the scored content verbatim**, including
    the records that scored WRONG -- because recording must not depend on
    scoring, which is exactly the coupling that let an empty string look
    plausible.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.answers = {t["task_id"]: unique_answer(t) for t in HALF_A}
        StubHandler.table = {
            t["turns"][-1]["content"]: {
                "content": cls.answers[t["task_id"]],
                "x_corollary": None,
            }
            for t in HALF_A
        }
        StubHandler.ps_context_length = 32768
        cls.fixture = ServerFixture(StubHandler)
        cls.url = cls.fixture.__enter__()
        cls.directory = tempfile.TemporaryDirectory()
        root = Path(cls.directory.name)
        tokenizer = root / "tokenizer.json"
        digest = tiny_tokenizer(tokenizer)
        cls.baseline = baseline_with_tokenizer(root, tokenizer, digest)
        out = root / "ungrounded.json"
        cls.proc = subprocess.run(
            [PY, str(STOPWATCH), "--book", str(BOOK_PATH),
             "--baseline", str(cls.baseline), "--system", "b-ungrounded",
             "--url", cls.url, "--half", "A", "--out", str(out)],
            capture_output=True, text=True, cwd=REPO, timeout=900,
        )
        cls.result = (
            json.loads(out.read_text(encoding="utf-8")) if out.exists() else None
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.fixture.__exit__(None, None, None)
        cls.directory.cleanup()
        StubHandler.table = oracle_table(HALF_A)

    def test_the_run_completed(self) -> None:
        self.assertEqual(self.proc.returncode, 0, self.proc.stdout + self.proc.stderr)

    def test_every_baseline_record_carries_its_content_verbatim(self) -> None:
        measured = [r for r in self.result["per_task"] if r.get("applicable")]
        self.assertEqual(len(measured), BOOK["counts"]["answerable_by_half"]["A"])
        for record in measured:
            with self.subTest(task=record["task_id"]):
                expected = self.answers[record["task_id"]]
                self.assertIn("content", record)
                self.assertEqual(record["content"], expected)
                self.assertEqual(record["content_chars"], len(expected))
                self.assertGreater(record["tokens"], 0)

    def test_the_content_is_recorded_even_where_the_task_scored_wrong(self) -> None:
        """Recording must not depend on scoring; that coupling was the bug."""

        measured = [r for r in self.result["per_task"] if r.get("applicable")]
        wrong = [r for r in measured if not r["correct"]]
        self.assertTrue(wrong, "this stub was supposed to miss some tasks")
        for record in wrong:
            with self.subTest(task=record["task_id"]):
                self.assertEqual(
                    record["content"], self.answers[record["task_id"]]
                )
                self.assertNotEqual(record["content"], "")

    def test_no_record_carries_another_task_s_answer(self) -> None:
        for record in self.result["per_task"]:
            if record.get("applicable"):
                with self.subTest(task=record["task_id"]):
                    self.assertIn(record["task_id"], record["content"])

    def test_the_turn_records_carry_it_too_for_the_offline_derivation(self) -> None:
        """M-5 reads `turns[]`; the top-level copy did not replace it."""

        for record in self.result["per_task"]:
            if record.get("applicable"):
                with self.subTest(task=record["task_id"]):
                    self.assertEqual(len(record["turns"]), 1)
                    self.assertEqual(
                        record["turns"][-1]["content"], record["content"]
                    )
                    self.assertIn("x_corollary", record["turns"][-1])

    def test_the_residuals_agree_with_the_recorded_content(self) -> None:
        """The number and the text behind it now have to tell one story."""

        for record in self.result["per_task"]:
            if not record.get("applicable"):
                continue
            for entry in record["b_residuals"]:
                with self.subTest(task=record["task_id"], pinned=entry["pinned"]):
                    self.assertEqual(
                        entry["found"], entry["residual"] in record["content"]
                    )

    def test_a_task_context_key_cannot_empty_the_response(self) -> None:
        """The bug class, not the bug: the merge happens before the content.

        `build_records` merges per-task context (materials sizes, prompt
        tokens) into the record. If that merge ran last, any key added to it
        later could silently blank the response -- so the response is written
        after it, and a context dict that tries to carry a `content` key
        loses.
        """

        task = next(t for t in HALF_A if t["kind"] == "exact_value")
        observed = {task["task_id"]: [turn("real text 94", status=None)]}
        records = mt.build_records(
            [task], observed, "b-ungrounded", len, {
                task["task_id"]: {"materials_tokens": 0, "content": ""}
            },
        )
        self.assertEqual(records[0]["content"], "real text 94")


class TheGroundedArmMeasuresWhatItCouldNotHold(unittest.TestCase):
    """C-1(a)-(c) on the arm the manifest's context block was written for.

    Still a stub: the canned answers are built from the book, and no model is
    contacted. What is real here is the MATERIALS extraction, its token count
    under the pinned tokenizer, and the truncation arithmetic against the
    context the stub reports from `/api/ps`.
    """

    @classmethod
    def setUpClass(cls) -> None:
        StubHandler.table = {
            t["turns"][-1]["content"]: {
                "content": "\n".join(
                    mt.strip_label(s)
                    for s in t["expected"]["content_must_contain"]
                ),
                "x_corollary": None,
            }
            for t in HALF_A
        }
        StubHandler.ps_context_length = 32768
        cls.fixture = ServerFixture(StubHandler)
        cls.url = cls.fixture.__enter__()
        cls.directory = tempfile.TemporaryDirectory()
        root = Path(cls.directory.name)
        tokenizer = root / "tokenizer.json"
        digest = tiny_tokenizer(tokenizer)
        cls.baseline = baseline_with_tokenizer(root, tokenizer, digest)
        out = root / "grounded.json"
        cls.proc = subprocess.run(
            [PY, str(STOPWATCH), "--book", str(BOOK_PATH),
             "--baseline", str(cls.baseline), "--system", "b-grounded",
             "--url", cls.url, "--half", "A", "--out", str(out)],
            capture_output=True, text=True, cwd=REPO, timeout=1800,
        )
        cls.result = (
            json.loads(out.read_text(encoding="utf-8")) if out.exists() else None
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.fixture.__exit__(None, None, None)
        cls.directory.cleanup()
        StubHandler.table = oracle_table(HALF_A)

    def test_the_run_completed(self) -> None:
        self.assertEqual(self.proc.returncode, 0, self.proc.stdout + self.proc.stderr)

    def test_the_grounded_prompt_template_was_used_verbatim(self) -> None:
        arm = self.result["baseline_arm"]
        self.assertEqual(
            arm["prompt_template"],
            BASELINE["arms"]["B-grounded"]["prompt_template"],
        )
        self.assertIn("canonical_routes", arm["materials_deviation"])

    def test_materials_tokens_track_materials_chars(self) -> None:
        """C-1(a). Both are recorded; the token count is the pinned one."""

        measured = [r for r in self.result["per_task"] if r.get("applicable")]
        self.assertEqual(len(measured), BOOK["counts"]["answerable_by_half"]["A"])
        for record in measured:
            with self.subTest(task=record["task_id"]):
                self.assertIn("materials_chars", record)
                self.assertIn("materials_tokens", record)
                self.assertIn("prompt_tokens", record)
                if record["materials_none"]:
                    self.assertEqual(record["materials_chars"], 0)
                    self.assertEqual(record["materials_tokens"], 0)
                else:
                    self.assertGreater(record["materials_tokens"], 0)
                    self.assertLessEqual(
                        record["materials_tokens"], record["materials_chars"]
                    )

    def test_the_closure_materials_do_not_fit_and_the_file_says_so(self) -> None:
        """C-1(b), against the manifest's truncation_disclosure."""

        truncated = [
            r for r in self.result["per_task"] if r.get("materials_truncated")
        ]
        self.assertTrue(truncated)
        self.assertTrue(
            all(r["kind"] == "closure_reachability" for r in truncated),
            [r["task_id"] for r in truncated],
        )
        for record in truncated:
            self.assertGreater(record["materials_tokens"], 32768)

    def test_the_secondary_median_excludes_exactly_the_oversized_tasks(self) -> None:
        """C-1(c)."""

        summary = self.result["summary"]
        self.assertEqual(
            summary["pre_declared_secondary_label"],
            BASELINE["runtime"]["context"]["pre_declared_secondary"],
        )
        oversized = {
            r["task_id"] for r in self.result["per_task"]
            if r.get("materials_truncated")
        }
        self.assertEqual(
            set(summary["materials_fit_task_ids"]),
            {
                r["task_id"] for r in self.result["per_task"]
                if r.get("applicable") and r["task_id"] not in oversized
            },
        )
        self.assertEqual(
            summary["materials_fit_tasks"],
            summary["answerable_tasks"] - len(oversized),
        )
        self.assertIsNotNone(
            summary["median_perceived_throughput_tps_materials_fit"]
        )

    def test_the_reconciliation_block_also_restricts_its_aggregate(self) -> None:
        block = self.result["metric_reconciliation"]
        self.assertIsNotNone(block["aggregate_perceived_tps"])
        self.assertIsNotNone(block["aggregate_perceived_tps_materials_fit"])
        self.assertEqual(
            block["median_perceived_tps_materials_fit"],
            self.result["summary"]["median_perceived_throughput_tps_materials_fit"],
        )


# ---------------------------------------------------------------------------
# C1, the dump server
# ---------------------------------------------------------------------------


class TheDumpServerIsConsumedWithoutSpecialCasing(unittest.TestCase):
    """DESIGN §7 C1."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.directory = tempfile.TemporaryDirectory()
        root = Path(cls.directory.name)
        corpus = root / "nodes.json"
        corpus.write_text(
            json.dumps(
                {
                    "statement_nodes": [
                        {"title": "A Title", "statement_meaning": "Some prose."},
                        {"title": "Another", "nested": {"note": "More prose."}},
                    ]
                }
            ),
            encoding="utf-8",
        )
        ds.DumpHandler.payload = ds.load_payload(corpus)
        ds.DumpHandler.corpus_name = "stub/nodes.json"
        cls.fixture = ServerFixture(ds.DumpHandler)
        cls.url = cls.fixture.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.fixture.__exit__(None, None, None)
        cls.directory.cleanup()

    def test_prose_extraction_takes_every_string_leaf_in_order(self) -> None:
        self.assertEqual(
            ds.DumpHandler.payload,
            "A Title\nSome prose.\nAnother\nMore prose.",
        )

    def test_the_default_corpus_is_a_committed_file_that_loads(self) -> None:
        payload = ds.load_payload(REPO / ds.DEFAULT_CORPUS)
        self.assertGreater(len(payload), 10000)

    def test_v1_models_lists_the_control(self) -> None:
        import urllib.request

        with urllib.request.urlopen(self.url + "/v1/models", timeout=10) as response:
            body = json.loads(response.read().decode("utf-8"))
        self.assertEqual([m["id"] for m in body["data"]], ["control/dump"])

    def test_the_stopwatchs_own_transport_reads_it_with_no_special_case(self) -> None:
        result = mt.post_stream(
            self.url,
            {"model": "control/dump",
             "messages": [{"role": "user", "content": "anything at all"}],
             "stream": True},
            timeout=30,
        )
        self.assertIsNone(result.error)
        self.assertEqual(result.content, ds.DumpHandler.payload)
        self.assertEqual(result.finish_reason, "stop")
        self.assertEqual(result.x_corollary["profile"], "control/dump")
        self.assertEqual(result.x_corollary["status"], "found")

    def test_the_dump_ignores_the_query(self) -> None:
        first = mt.post_stream(
            self.url,
            {"model": "control/dump",
             "messages": [{"role": "user", "content": "logic.boolean_laws"}],
             "stream": True},
            timeout=30,
        )
        second = mt.post_stream(
            self.url,
            {"model": "control/dump",
             "messages": [{"role": "user", "content": "something else entirely"}],
             "stream": True},
            timeout=30,
        )
        self.assertEqual(first.content, second.content)

    def test_the_same_scoring_code_gives_the_dump_zero_useful_tokens(self) -> None:
        """"a C1 score of zero is the expected reading, not a vacuous one,
        because the same scoring code produced it" (DESIGN §7)."""

        counts = 0
        for task in [t for t in HALF_A if mt.is_answerable(t)][:8]:
            result = mt.post_stream(
                self.url,
                {"model": "control/dump",
                 "messages": [{"role": "user", "content": task["turns"][0]["content"]}],
                 "stream": True},
                timeout=30,
            )
            scored = mt.score_kernel(task, [result])
            with self.subTest(task=task["task_id"]):
                self.assertFalse(scored.correct)
                self.assertFalse(scored.receipted)
            counts += 1
        self.assertEqual(counts, 8)

    def test_the_dump_binds_loopback_only(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()) as noise:
            code = ds.main(["--host", "0.0.0.0", "--port", "1"])
        self.assertEqual(code, 2)
        self.assertIn("127.0.0.1 only", noise.getvalue())


# ---------------------------------------------------------------------------
# the boundary rule
# ---------------------------------------------------------------------------


class TheStopwatchNeverImportsTheEngine(unittest.TestCase):
    def test_the_stopwatch_imports_no_engine_module(self) -> None:
        tree = ast.parse(STOPWATCH.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertEqual(
            sorted(imported & ENGINE_MODULES),
            [],
            "the stopwatch speaks only the public HTTP API",
        )

    def test_the_control_server_imports_no_engine_module_either(self) -> None:
        tree = ast.parse((REPO / "scripts" / "dump_server.py").read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertEqual(sorted(imported & ENGINE_MODULES), [])

    def test_this_suite_imports_no_engine_module(self) -> None:
        tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertEqual(sorted(imported & ENGINE_MODULES), [])

    def test_the_forbidden_list_covers_every_module_the_task_prompt_named(self) -> None:
        named = {
            "harness", "conversation", "retrieval", "evaluate", "answer",
            "resolver", "belief", "ownership", "closure_query",
            "closure_worlds", "request_grammar", "dispatcher", "controller",
            "story", "gloss", "decompose", "match_signatures", "serve_chat",
        }
        self.assertTrue(named <= set(mt.FORBIDDEN_MODULES))

    def test_the_guard_is_a_real_assertion_not_a_comment(self) -> None:
        original = dict(sys.modules)
        try:
            sys.modules["harness"] = object()  # type: ignore[assignment]
            with self.assertRaises(mt.Refused):
                mt.assert_clean_imports()
        finally:
            sys.modules.clear()
            sys.modules.update(original)

    def test_no_task_is_ever_executed_against_a_real_system_here(self) -> None:
        """The seal, as a property of this file's own source.

        The suite may read the book; it may not point the stopwatch at
        anything but a stub in this process. Every `--url` in this file is a
        loopback address bound here, and every `--half` is A.
        """

        # Everything above this method: the patterns below are literals, and
        # a scanner that read itself would only ever find its own quotes.
        source = Path(__file__).read_text(encoding="utf-8").split(
            "def test_no_task_is_ever_executed"
        )[0]
        for match in re.finditer(r'"--url",\s*([^\n,]+)', source):
            value = match.group(1).strip()
            with self.subTest(url=value):
                self.assertIn(
                    value,
                    {'"http://127.0.0.1:1"', "cls.url", "self.url"},
                    f"a --url this suite passes is not a stub: {value}",
                )
        # Half B may be NAMED only where the surrounding test proves the run
        # is refused: never in the same invocation as a live stub URL.
        for match in re.finditer(r'"--half", "B"', source):
            window = source[max(0, match.start() - 400): match.end() + 400]
            with self.subTest(offset=match.start()):
                self.assertNotIn(
                    "cls.url", window, "half B was pointed at a live server"
                )
                self.assertNotIn(
                    "self.url", window, "half B was pointed at a live server"
                )
                self.assertIn(
                    "returncode, 2", window,
                    "a half-B invocation that does not assert a refusal",
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
