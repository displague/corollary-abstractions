#!/usr/bin/env python3
"""The client-side stopwatch: perceived useful-token throughput, over HTTP only.

`docs/DESIGN-grounded-throughput.md` §3 names this file and pins what it may
know:

> **The stopwatch** -- `scripts/measure_throughput.py` plus
> `experiments/throughput_result.json`: a client-side harness that speaks
> only the public API (no imports from the serving process) ...

That parenthesis is the load-bearing sentence of this module. A stopwatch
that imported the engine would be the system under test grading its own
clock, so the rule is **enforced rather than promised**, exactly the way
`scripts/build_throughput_tasks.py` enforces it for the answer key:

- a `sys.modules` assertion at the end of every run (`assert_clean_imports`),
  which prints `CLEAN_IMPORTS_LINE` so a parent process can read that the
  guard actually ran rather than infer it from a zero exit code;
- an AST guard in `tests/test_measure_throughput.py`, which reads this
  source and refuses any import from the serving path.

Committed artifacts are read as **data** -- the task book, the baseline
manifest, `data/*.json`, `reports/*` -- because that is what a client with a
copy of the repository has. Nothing here calls a function the server calls.

What is measured, and where each rule comes from
------------------------------------------------

*Useful tokens* (DESIGN §3): "the tokens of the assistant message `content`
field only -- the rendered answer text -- under the pinned baseline
tokenizer (one tokenizer counting both contenders); vendor extension
payloads, receipt structures, ids, and digests never count."

*Perceived throughput* (DESIGN §3): "useful tokens / client wall-clock,
where the numerator counts only correctly-and-receipted answers, the
denominator counts every task's elapsed time, and an answerable task the
system REFUSES contributes zero tokens plus a frozen time charge equal to
that system's slowest correct answer -- so a refusal is never a cheap way to
shed a hard task's clock."

*Token counting refuses rather than approximates* (baseline manifest,
`tokenizer.policy`): "token counting REFUSES (exit 2) when the file is
absent or its digest mismatches - cannot-verify, never skip (the
WordNet-archive rule)."

*The server's own `usage` block is never read* (SPEC §6): "the stopwatch
counts `content` itself, client-side, with the pinned baseline tokenizer --
it never reads the server's `usage` block."

Gates are **reported, not enforced**. The stopwatch measures; adjudication
reads the file it writes. The one thing this module refuses to do is run at
all when the run would already be void: half B without `--registered`, an
output file it would silently overwrite, a rendering module that changed
after the task book sealed (SPEC §6: "any change to engine rendering after
the task book seals **voids the run**"), or an unverifiable tokenizer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
import time
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.client import HTTPConnection, HTTPSConnection
from pathlib import Path
from typing import Any, Callable, Sequence

REPO = Path(__file__).resolve().parents[1]

SCHEMA = "corollary.throughput-result/1"
BOOK_SCHEMA = "corollary.throughput-tasks/1"
BASELINE_SCHEMA = "corollary.throughput-baseline/1"

DEFAULT_BOOK = "experiments/throughput_tasks.json"
DEFAULT_BASELINE = "experiments/throughput_baseline.json"

#: DESIGN §3's five all-answer kinds, which are exactly the kinds the book's
#: `counts.answerable_by_kind` enumerates and exactly the kinds the book's
#: `scoring_rules.per_kind_floor` binds to T5's >=80% floor: "T5's per-kind
#: >=80% correctness-with-receipts floor applies to the five all-answer kinds
#: (belief_query, closure_reachability, corpus_definition, exact_value,
#: twin_lookup), which are the kinds counted in answerable_total."
ANSWERABLE_KINDS = (
    "belief_query",
    "closure_reachability",
    "corpus_definition",
    "exact_value",
    "twin_lookup",
)

#: SPEC §5's frozen status alphabet, split by whether the turn is *answering*.
#: SPEC §6.1: "any non-answering status -- `exhausted`, `refused`, `waiting`,
#: `canceled`, `cycle`, `hop_ceiling`, `abstained`, uppercase `REFUSED` --
#: carries no grounding claim". Used only for the anti-shirking time charge:
#: whether a turn was *correct* is decided by the book's expected record, not
#: by this set, because the book's `bounded_negative_is_an_answer` rule makes
#: a closure `exhausted` a correct ANSWER.
NON_ANSWERING_STATUSES = frozenset(
    {
        "exhausted",
        "refused",
        "waiting",
        "canceled",
        "cycle",
        "hop_ceiling",
        "abstained",
        "REFUSED",
    }
)

#: Never importable from here, for the reason the module docstring gives.
#: Copied from `scripts/build_throughput_tasks.py:FORBIDDEN_MODULES` and
#: extended with the modules the substrate added since (`session_state`,
#: `session_keys`, `theory_of_mind`, `deixis`, `discourse`, `lifetimes`,
#: `preference`, `specialize`, `entailment`, `ambiguity`) -- a list rather
#: than a convention, because a convention is what an implementer under time
#: pressure edits.
FORBIDDEN_MODULES = (
    "ambiguity", "answer", "belief", "closure_build", "closure_check",
    "closure_query", "closure_worlds", "controller", "conversation",
    "decompose", "deixis", "discourse", "dispatcher", "entailment",
    "evaluate", "frames", "gloss", "harness", "lifetimes",
    "match_signatures", "ownership", "preference", "request_grammar",
    "resolver", "retrieval", "serve_chat", "session_keys", "session_run",
    "session_state", "specialize", "story", "supposition", "theory_of_mind",
    "write_stage",
)

CLEAN_IMPORTS_LINE = "engine-clean imports: verified in this process"

#: The manifest's `tokenizer.policy`, spoken as the refusal itself.
CANNOT_VERIFY = (
    "cannot-verify: the pinned baseline tokenizer is absent or its digest "
    "does not match experiments/throughput_baseline.json. Token counting "
    "REFUSES rather than approximates (the WordNet-archive rule); no number "
    "in this run would mean anything without the one tokenizer that counts "
    "both contenders."
)

#: The kernel's frozen label padding, as it appears in every rendered answer
#: line the book pins ("exact      : 94", "world_id: story.golden_chicken").
LABEL_PADDING = re.compile(r"^[a-z_][a-z_ ]*: *")

#: Committed HERE, before any run, and copied into every result file that
#: scores a baseline arm. DESIGN §6 T4 compares "correctness >= B-grounded's"
#: and speed; a model is never asked for a receipt, so `receipted` is false
#: on the B side by construction and is recorded as such.
B_SIDE_CORRECTNESS_RULE = (
    "A baseline answer is correct iff every content_must_contain string, "
    "after stripping any leading label of the form ^[a-z_][a-z_ ]*: * (the "
    "kernel's frozen label padding), is a substring of the baseline's "
    "content -- e.g. the kernel line 'exact      : 449' requires '449'; "
    "unlabeled strings (titles, meanings, member ids) are unchanged. "
    "Receipts are not required of a model: receipted is false on this arm "
    "and is recorded, and T4 compares correctness and speed only "
    "(DESIGN-grounded-throughput 6 T4). Baseline arms never see "
    "receipt_expect, need_expect or x_corollary. Baseline arms run "
    "ANSWERABLE tasks only; refusal_due and clarification_due tasks gate the "
    "kernel and are recorded 'not-applicable' here. This rule was committed "
    "with the stopwatch, before any timed run."
)

#: H-4. What actually governs the baseline's sampling, established by live
#: probe rather than by reading the OpenAI field list.
SAMPLING_SOURCE = (
    "applied by the ollama model manifest; /v1 ignores top_k and "
    "repeat_penalty (verified 2026-08-22)"
)

#: The two design sentences the throughput number has to reconcile, quoted so
#: the result file argues with itself in the open rather than picking one and
#: hoping nobody reads the other.
DESIGN_SENTENCE_T4 = (
    "T4 -- the baseline is pinned before K. ... then K = 5 freezes: the "
    "kernel's median perceived throughput over half-B answerable tasks must "
    "be >= 5x B-grounded's, at correctness >= B-grounded's, with median "
    "time-to-first-useful-token also lower "
    "(DESIGN-grounded-throughput 6 T4)"
)
DESIGN_SENTENCE_SECTION_3 = (
    "Perceived throughput for a system = useful tokens / client wall-clock, "
    "where the numerator counts only correctly-and-receipted answers, the "
    "denominator counts every task's elapsed time, and an answerable task "
    "the system REFUSES contributes zero tokens plus a frozen time charge "
    "equal to that system's slowest correct answer "
    "(DESIGN-grounded-throughput 3)"
)

#: DESIGN §7 C1 and C2, quoted so the result file carries its own voiding
#: sentences. The comparisons themselves are the adjudication's, not this
#: module's: the stopwatch measures, the adjudication reads.
VOIDING_SENTENCES = {
    "C1": (
        "If C1's perceived throughput exceeds 1% of the kernel's, the metric "
        "as implemented is crediting bandwidth, and the metric is void."
    ),
    "C2": (
        "If C2's perceived throughput exceeds 1% of the kernel's, either the "
        "scoring or the task book's expected records fail to separate right "
        "from wrong answers, and the run is void."
    ),
}

WARMUP_LINE_KERNEL = ""  # SPEC §5 row 0: the registered empty line, served.
WARMUP_LINE_MODEL = "hello"


class Refused(Exception):
    """A condition under which running would produce a void number."""


# --------------------------------------------------------------------------
# digests and small helpers
# --------------------------------------------------------------------------


def canonical_json(value: Any) -> str:
    """SPEC §4.1's canonical-JSON/compact."""

    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def canonical_lf_sha256(path: Path) -> str:
    """SPEC §6's canonical-LF digest: file bytes with CRLF folded to LF."""

    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def raw_sha256(path: Path) -> str:
    """Byte-exact digest, for the downloaded tokenizer the manifest pins."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def median_or_none(values: Sequence[float]) -> float | None:
    return statistics.median(values) if values else None


def strip_label(text: str) -> str:
    """Drop the kernel's leading label padding; see B_SIDE_CORRECTNESS_RULE."""

    match = LABEL_PADDING.match(text)
    return text[match.end():] if match else text


def strict_equal(expect: Any, actual: Any) -> bool:
    """Equality with a **strict type match**, decided and documented here.

    Python's `==` is looser than a receipt check should be: `True == 1`,
    `1 == 1.0`, and `1 == True` are all true, so a wire that answered
    `visited_states: true` or `horizon: 5.0` would satisfy a book that pinned
    `75` and `5`. A receipt is a claim about a value the client will
    re-validate against a committed artifact (T7), so the rule taken here is
    the strict one: **`type(expect) is type(actual)` and then `==`**, with no
    numeric-tower coercion of any kind -- an int never matches a float, a
    bool never matches an int. Lists and nested dicts recurse elementwise so
    the strictness cannot be laundered through a container.

    Everything the committed book pins is a str, an int, or a list of str,
    and JSON round-trips all three without changing type, so the strict rule
    costs the honest kernel nothing and is only ever felt by a wire that
    answered with the wrong kind of value.
    """

    if type(expect) is not type(actual):
        return False
    if isinstance(expect, list):
        return len(expect) == len(actual) and all(
            strict_equal(a, b) for a, b in zip(expect, actual)
        )
    if isinstance(expect, dict):
        return set(expect) == set(actual) and all(
            strict_equal(value, actual[key]) for key, value in expect.items()
        )
    return expect == actual


def subset_ok(expect: Any, actual: Any) -> bool:
    """The book's `receipt_subset` rule, recursively.

    Book, `scoring_rules.receipt_subset`: "receipt_expect and need_expect are
    subset assertions: every key present must match; absent keys are
    unconstrained." Nested dicts (the conversation route's
    `binding: {slot, value, lifetime}`) recurse with subset semantics; every
    leaf comparison goes through `strict_equal`, and a pinned list
    (`member_ids`) must match whole, because the book pins it whole.
    """

    if isinstance(expect, dict):
        if not isinstance(actual, dict):
            return False
        return all(
            key in actual and subset_ok(value, actual[key])
            for key, value in expect.items()
        )
    return strict_equal(expect, actual)


def is_answerable(task: dict) -> bool:
    """The book's own definition, not a new one.

    `counts.answerable_by_kind` enumerates exactly ANSWERABLE_KINDS and
    `counts.answerable_total` is their sum (94); the book's `per_kind_floor`
    rule says clarification_due and refusal_due "may not be counted toward
    it in either direction". A `phase: resume` clarification task therefore
    ends in a correct answer and still contributes zero useful tokens.
    """

    return task["kind"] in ANSWERABLE_KINDS


# --------------------------------------------------------------------------
# the clean-imports guard
# --------------------------------------------------------------------------


def assert_clean_imports() -> None:
    """No engine module may be in this interpreter. Checked, not promised.

    Same shape as the task-book builder's guard and for the same reason: the
    check is only meaningful in the process that did the work, so it lives
    here, runs at the end of a run, and prints a line a parent can read.
    """

    leaked = sorted(set(FORBIDDEN_MODULES) & set(sys.modules))
    if leaked:
        raise Refused(
            "an engine module was imported while timing the engine: "
            f"{leaked}. The stopwatch speaks only the public HTTP API; a "
            "client that can call the server's own functions is not a client."
        )


# --------------------------------------------------------------------------
# the tokenizer pin
# --------------------------------------------------------------------------


def load_token_counter(baseline: dict, repo: Path) -> Callable[[str], int]:
    """Load the pinned tokenizer or refuse with exit 2.

    Manifest `tokenizer.policy`: "gitignored local file, digest-pinned here;
    token counting REFUSES (exit 2) when the file is absent or its digest
    mismatches - cannot-verify, never skip (the WordNet-archive rule)."
    """

    pin = baseline["tokenizer"]
    named = Path(pin["file"])
    path = named if named.is_absolute() else repo / named

    if not path.is_file():
        print(CANNOT_VERIFY, file=sys.stderr)
        print(f"missing tokenizer file: {path}", file=sys.stderr)
        print(f"source_url: {pin.get('source_url', '(none recorded)')}",
              file=sys.stderr)
        raise SystemExit(2)

    digest = raw_sha256(path)
    if digest != pin["sha256"]:
        print(CANNOT_VERIFY, file=sys.stderr)
        print(f"tokenizer file: {path}", file=sys.stderr)
        print(f"expected sha256: {pin['sha256']}", file=sys.stderr)
        print(f"actual   sha256: {digest}", file=sys.stderr)
        raise SystemExit(2)

    from tokenizers import Tokenizer  # third-party, not an engine module

    tokenizer = Tokenizer.from_file(str(path))

    def count(text: str) -> int:
        if not text:
            return 0
        return len(tokenizer.encode(text, add_special_tokens=False).ids)

    return count


# --------------------------------------------------------------------------
# the transport: stdlib http.client, SSE in, deltas concatenated
# --------------------------------------------------------------------------


@dataclass
class TurnResult:
    """One request/response round trip, timed by the client's own clock."""

    content: str = ""
    x_corollary: dict | None = None
    ttft_s: float | None = None
    elapsed_s: float = 0.0
    chunk_count: int = 0
    finish_reason: str | None = None
    http_status: int = 0
    error: str | None = None


def split_base_url(url: str) -> tuple[str, str, int, str]:
    """Return (scheme, host, port, path-prefix) for a base URL."""

    parsed = urllib.parse.urlsplit(url if "://" in url else "http://" + url)
    scheme = parsed.scheme or "http"
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if scheme == "https" else 80)
    prefix = parsed.path.rstrip("/")
    for tail in ("/v1/chat/completions", "/chat/completions"):
        if prefix.endswith(tail):
            prefix = prefix[: -len(tail)]
    if prefix.endswith("/v1"):
        prefix = prefix[:-3]
    return scheme, host, port, prefix


def post_stream(base_url: str, body: dict, timeout: float) -> TurnResult:
    """POST a streamed chat completion and time it from the client side.

    SPEC §8: "Chunk boundaries are rendered lines of `content` ... and every
    chunk after the first carries its leading `"\\n"`, so concatenating all
    deltas reproduces `content` byte-for-byte." So reassembly is a plain
    concatenation -- this function never inserts a separator of its own.

    SPEC §8 also fixes where the extension rides: "The final chunk carries
    `finish_reason: "stop"`; `x_corollary` rides on the final chunk." We take
    the last `x_corollary` seen, which is that one.
    """

    scheme, host, port, prefix = split_base_url(base_url)
    path = f"{prefix}/v1/chat/completions"
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "Connection": "close",
    }

    opener = HTTPSConnection if scheme == "https" else HTTPConnection
    conn = opener(host, port, timeout=timeout)
    result = TurnResult()
    started = time.perf_counter()
    try:
        conn.request("POST", path, body=payload, headers=headers)
        response = conn.getresponse()
        result.http_status = response.status
        if response.status != 200:
            result.error = (
                f"HTTP {response.status}: "
                f"{response.read()[:800].decode('utf-8', 'replace')}"
            )
            result.elapsed_s = time.perf_counter() - started
            return result

        pieces: list[str] = []
        while True:
            line = response.readline()
            if not line:
                break
            line = line.rstrip(b"\r\n")
            if not line or not line.startswith(b"data:"):
                continue
            raw = line[len(b"data:"):].strip()
            if raw == b"[DONE]":
                break
            try:
                chunk = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                result.error = f"unparseable SSE chunk: {exc}"
                break
            result.chunk_count += 1
            choices = chunk.get("choices") or []
            if choices:
                delta = choices[0].get("delta") or {}
                piece = delta.get("content")
                if piece:
                    if result.ttft_s is None:
                        result.ttft_s = time.perf_counter() - started
                    pieces.append(piece)
                if choices[0].get("finish_reason"):
                    result.finish_reason = choices[0]["finish_reason"]
            if isinstance(chunk.get("x_corollary"), dict):
                result.x_corollary = chunk["x_corollary"]
        result.content = "".join(pieces)
    except OSError as exc:  # socket timeouts, refused connections
        result.error = f"{type(exc).__name__}: {exc}"
    finally:
        result.elapsed_s = time.perf_counter() - started
        conn.close()
    return result


# --------------------------------------------------------------------------
# B-grounded materials: the manifest's context_rule, ref by ref
# --------------------------------------------------------------------------


class Materials:
    """Extract the committed records a task's answer rests on.

    Manifest, `arms.B-grounded.context_rule`: "receives, injected into its
    context before the question, the same committed artifact records the
    kernel's answer rests on - scoped to the referenced record(s) named by
    the task's artifact_refs (the node record, the twin group entry, the
    closure's registration plus the routes and states for the queried world),
    extracted verbatim, not whole ledger files."

    Extraction is therefore driven by `artifact_refs`, one clause of the rule
    per ref shape. Refs to source or test files (`scripts/request_grammar.py`,
    `tests/test_harness_line.py`) appear only on clarification and refusal
    tasks, which no baseline arm runs, so they are skipped with a note rather
    than pasted as materials.
    """

    def __init__(self, repo: Path) -> None:
        self.repo = repo
        self._cache: dict[str, Any] = {}

    def _json(self, rel: str) -> Any:
        if rel not in self._cache:
            self._cache[rel] = read_json(self.repo / rel)
        return self._cache[rel]

    def _pretty(self, value: Any) -> str:
        return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)

    def _node(self, rel: str, statement_id: str) -> str:
        for node in self._json(rel).get("statement_nodes", []):
            if node.get("statement_id") == statement_id:
                return self._pretty(node)
        raise Refused(f"artifact ref does not resolve: {rel}#{statement_id}")

    def _twin_group(self, task: dict, rel: str) -> str:
        group = task.get("ledger_group")
        if not group:
            raise Refused(
                f"{task['task_id']} cites {rel} but records no ledger_group"
            )
        entry = self._json(rel)[group["field"]][group["group_index"]]
        return self._pretty(
            {
                "ledger_path": rel,
                "field": group["field"],
                "group_index": group["group_index"],
                "level": group["level"],
                "group": entry,
            }
        )

    def _world_registration(self, world_id: str) -> str | None:
        manifest = self._json("data/closure_worlds/manifest.json")
        for entry in manifest.get("files", []):
            world = self._json(entry["path"])
            if world.get("world_id") == world_id:
                return self._pretty({"path": entry["path"], "world": world})
        return None

    def _closure(self, rel: str) -> list[str]:
        report = self._json(rel)
        blocks = []
        registration = self._world_registration(report["world_id"])
        if registration is not None:
            blocks.append(registration)
        head = {k: v for k, v in report.items()
                if k not in ("states", "convergence_cells")}
        head["path"] = rel
        blocks.append(self._pretty(head))
        # The report carries no key literally named `canonical_routes`; the
        # routes it holds are `convergence_cells`' `primary_route` /
        # `alternate_route` pairs, and those are what the manifest's "routes"
        # clause can mean here. Recorded as a deviation in the result file.
        blocks.append(self._pretty({"routes": report.get("convergence_cells", [])}))
        blocks.append(self._pretty({"states": report.get("states", [])}))
        return blocks

    def for_task(self, task: dict) -> tuple[str, list[str]]:
        """Return (materials text, skipped refs)."""

        blocks: list[str] = []
        skipped: list[str] = []
        for ref in task["expected"]["artifact_refs"]:
            if "#" in ref:
                rel, statement_id = ref.split("#", 1)
                blocks.append(self._node(rel, statement_id))
            elif ref.endswith(".closure.json"):
                blocks.extend(self._closure(ref))
            elif ref == "reports/signature_matches.json":
                blocks.append(self._twin_group(task, ref))
            elif ref.endswith(".json"):
                blocks.append(self._pretty(self._json(ref)))
            else:
                skipped.append(ref)
        if not blocks:
            # DESIGN §3: computed and session-derived answers rest on no
            # external artifact; the receipt says `computed` / `session`
            # (SPEC §6.1). There is nothing to inject and nothing is invented.
            return "none", skipped
        return "\n\n".join(blocks), skipped


# --------------------------------------------------------------------------
# request construction
# --------------------------------------------------------------------------


def user_turns(task: dict) -> list[dict]:
    return [t for t in task["turns"] if t["role"] == "user"]


def kernel_requests(task: dict) -> list[list[dict]]:
    """One request per user turn, prefixes replayed.

    SPEC §4: "The `messages` array's **user turns, in order**, are the
    session's input lines. Turn *n*'s response is computed by replaying user
    turns 1...*n* into a fresh session object and rendering the last result."

    The client sends user turns only. SPEC §4 makes assistant turns "the
    client's transcript claim, not an input channel", checked for divergence
    and answered with `409` on mismatch; a stopwatch has no reason to risk a
    409 on a whitespace question, so it omits them. The engine's answer is
    identical either way -- the replay is over user turns.
    """

    turns = user_turns(task)
    return [
        [{"role": t["role"], "content": t["content"]} for t in turns[: n + 1]]
        for n in range(len(turns))
    ]


def grounded_messages(task: dict, baseline: dict, materials: str) -> list[dict]:
    """The manifest's frozen prompt_template, filled and not improvised."""

    template = baseline["arms"]["B-grounded"]["prompt_template"]
    question = "\n".join(t["content"] for t in user_turns(task))
    return [
        {"role": "system", "content": template["system"]},
        {
            "role": "user",
            "content": template["user"].format(
                artifacts=materials, question=question
            ),
        },
    ]


def ungrounded_messages(task: dict) -> list[dict]:
    """`context_rule: none - the same model answering cold`."""

    return [{"role": t["role"], "content": t["content"]} for t in task["turns"]]


def sampling_body(baseline: dict) -> dict:
    """Manifest `sampling`, **requested** through the OpenAI-compatible body.

    Requested, not necessarily applied, and the earlier draft of this
    docstring claimed otherwise. Live probing on 2026-08-22 established that
    ollama's `/v1` compatibility layer **ignores** `top_k` and
    `repeat_penalty`; what governs them is the ollama model manifest, which
    is exactly where the baseline manifest says the values come from
    ("vendor defaults as shipped in the ollama model manifest; not tuned by
    this repository"). The fields are still sent, so the request on the wire
    matches the pin and a future runtime that honours them needs no change
    here -- but the result file records them as `sampling_requested` beside
    `sampling_source`, never as settings that took effect.

    DESIGN §8: "the baseline is not strawmanned -- it runs with the GPU,
    warm, at its vendor-recommended settings", so these are copied, never
    tuned here.
    """

    sampling = baseline["sampling"]
    body = {
        "temperature": sampling["temperature"],
        "top_p": sampling["top_p"],
        "top_k": sampling["top_k"],
    }
    if "repeat_penalty" in sampling:
        body["repeat_penalty"] = sampling["repeat_penalty"]
    return body


def baseline_model_name(baseline: dict) -> str:
    tag = baseline["model"]["provider_tag"]
    engine = baseline["runtime"]["engine"]
    prefix = engine + ":"
    return tag[len(prefix):] if tag.startswith(prefix) else tag


# --------------------------------------------------------------------------
# scoring
# --------------------------------------------------------------------------


@dataclass
class Scored:
    correct: bool = False
    receipted: bool = False
    status_ok: bool = False
    content_ok: bool = False
    receipt_ok: bool = False
    need_ok: bool = True
    route_ok: bool = True
    refusal_gate_ok: bool | None = None
    waiting_legs: list[dict] = field(default_factory=list)
    missing_strings: list[str] = field(default_factory=list)


def score_kernel(task: dict, turns: list[TurnResult]) -> Scored:
    """One mechanic for check=exact / receipt / verdict.

    The book carries three `check` values but no three sets of mechanics: an
    `exact_value` task pins its computed line in `content_must_contain` and
    its value in `receipt_expect`; a `corpus_definition` task pins the
    person-authored sentences and the node digest; a `verdict` task pins the
    rendered verdict lines and whatever receipt the route mints. All three
    reduce to the same four assertions below, which is why `check` is
    recorded and not branched on.
    """

    expected = task["expected"]
    final = turns[-1]
    extension = final.x_corollary or {}
    scored = Scored()

    scored.status_ok = extension.get("status") == expected["status_expect"]

    scored.missing_strings = [
        s for s in expected["content_must_contain"] if s not in final.content
    ]
    scored.content_ok = not scored.missing_strings

    receipt = extension.get("receipt")
    receipt_expect = expected.get("receipt_expect") or {}
    scored.receipt_ok = subset_ok(receipt_expect, receipt if receipt else {})

    need_expect = expected.get("need_expect")
    if need_expect:
        scored.need_ok = subset_ok(need_expect, extension.get("need") or {})

    route_expect = task.get("route_expect")
    if route_expect is not None:
        scored.route_ok = extension.get("route") == route_expect

    scored.correct = (
        scored.status_ok
        and scored.content_ok
        and scored.receipt_ok
        and scored.need_ok
        and scored.route_ok
    )
    # "correctly-and-receipted" (DESIGN §3): the wire carried a receipt and
    # every key the book pinned matched it. A task that pins nothing still
    # has to carry one -- SPEC §6.1: the receipt is "always present".
    scored.receipted = bool(receipt) and scored.receipt_ok

    if task["kind"] == "refusal_due":
        # T5's refusal leg, per the parent gate: status matches, and route
        # matches route_expect when the book records one.
        scored.refusal_gate_ok = scored.status_ok and scored.route_ok

    if task["kind"] == "clarification_due":
        scored.waiting_legs = waiting_legs(task, turns)

    return scored


def waiting_legs(task: dict, turns: list[TurnResult]) -> list[dict]:
    """The book's `clarification_leg` rule, graded per marked WAITING turn.

    Book, `scoring_rules.clarification_leg`: "T5's clarification leg is
    graded per marked WAITING turn, not per task. Every clarification_due
    task carries at least one turn with expected_status 'waiting'; the leg
    passes only if the skin returns a WAITING status at 100% of those turns.
    On corollary/conversation that turn must additionally carry
    x_corollary.need matching need_expect; on corollary/kernel a WAITING
    status with its candidate answer lines satisfies the leg (SPEC §6.2
    emits no need record on that profile). A phase:'resume' task that never
    waited fails the leg even if its final answer is correct."

    Two readings this implementation had to fix, both recorded here:

    - "matching need_expect" is only checkable where the book records a
      `need_expect`, which it does on the `phase: ask` tasks whose marked
      turn IS the final turn. On a `phase: resume` conversation task the
      marked turn is turn 1 and the book pins the resumed answer's receipt
      instead. So: subset-assert `need_expect` when it exists and the marked
      turn is the one it describes; otherwise require the profile to have
      emitted a non-empty `need` record at all, which is the same sentence's
      minimum claim.
    - "with its candidate answer lines" is read as non-empty `content` on the
      kernel profile: SPEC §6.2 says a kernel WAITING carries "only `detail`
      (and sometimes `answer` lines listing candidates)", so a wholly empty
      rendering is the failure the clause guards against.
    """

    marked = [
        (index, turn)
        for index, turn in enumerate(task["turns"])
        if turn.get("expected_status") == "waiting"
    ]
    legs: list[dict] = []
    conversation = task["profile"] == "corollary/conversation"
    need_expect = task["expected"].get("need_expect")
    final_index = len(task["turns"]) - 1

    for index, spec in marked:
        observed = turns[index] if index < len(turns) else TurnResult()
        extension = observed.x_corollary or {}
        status = extension.get("status")
        leg = {
            "turn_index": index,
            "expected_status": "waiting",
            "status": status,
            "status_ok": status == "waiting",
            "need": extension.get("need"),
        }
        if conversation:
            need = extension.get("need") or {}
            if need_expect and index == final_index:
                leg["need_ok"] = subset_ok(need_expect, need)
            else:
                leg["need_ok"] = bool(need)
        else:
            leg["need_ok"] = bool(observed.content)
            leg["kernel_candidate_lines"] = bool(observed.content)
        leg["ok"] = bool(leg["status_ok"] and leg["need_ok"])
        legs.append(leg)
    return legs


def score_baseline(task: dict, content: str) -> Scored:
    """B_SIDE_CORRECTNESS_RULE, and nothing else."""

    scored = Scored()
    scored.missing_strings = [
        s
        for s in task["expected"]["content_must_contain"]
        if strip_label(s) not in content
    ]
    scored.content_ok = not scored.missing_strings
    scored.correct = scored.content_ok
    scored.receipted = False
    scored.status_ok = True  # not asserted on this arm; recorded as such
    scored.receipt_ok = True
    return scored


# --------------------------------------------------------------------------
# the shuffled-kernel control (C2)
# --------------------------------------------------------------------------


def derangement(count: int, seed: int) -> list[int]:
    """A deterministic permutation with no fixed points (Sattolo's algorithm).

    DESIGN §7 C2: "the kernel with answers permuted across tasks: fast,
    receipt-shaped, wrong." Sattolo's algorithm yields a single cycle, so no
    element maps to itself for count >= 2 -- the property the control needs,
    obtained without rejection sampling and therefore reproducible from the
    seed alone. The seed is derived from the task book's own digest so the
    permutation is a fact about the sealed book, not about the run's clock.
    """

    if count < 2:
        raise Refused(
            "a derangement needs at least two answerable tasks; C2 cannot be "
            f"applied to {count}."
        )
    import random  # stdlib

    order = list(range(count))
    rng = random.Random(seed)
    for i in range(count - 1, 0, -1):
        j = rng.randrange(i)
        order[i], order[j] = order[j], order[i]
    return order


def apply_shuffle(
    tasks: Sequence[dict], observed: dict[str, list[TurnResult]], book_digest: str
) -> dict:
    """Permute (content, x_corollary) across answerable tasks; keep the clocks.

    Timing stays with the original task, because C2 asks what the metric says
    about a system that is exactly as fast and reliably wrong.
    """

    answerable = [t for t in tasks if is_answerable(t)]
    seed = int(book_digest[:16], 16)
    order = derangement(len(answerable), seed)
    mapping = []
    donors = {}
    for position, source in enumerate(order):
        target_id = answerable[position]["task_id"]
        donor_id = answerable[source]["task_id"]
        mapping.append([donor_id, target_id])
        donors[target_id] = donor_id

    swapped: dict[str, list[TurnResult]] = {}
    for target_id, donor_id in donors.items():
        donor_turns = observed[donor_id]
        target_turns = observed[target_id]
        rebuilt = []
        for index, turn in enumerate(target_turns):
            source = donor_turns[min(index, len(donor_turns) - 1)]
            rebuilt.append(
                TurnResult(
                    content=source.content,
                    x_corollary=source.x_corollary,
                    ttft_s=turn.ttft_s,
                    elapsed_s=turn.elapsed_s,
                    chunk_count=turn.chunk_count,
                    finish_reason=source.finish_reason,
                    http_status=turn.http_status,
                    error=turn.error,
                )
            )
        swapped[target_id] = rebuilt
    for task in tasks:
        observed[task["task_id"]] = swapped.get(
            task["task_id"], observed[task["task_id"]]
        )

    return {
        "control": "C2",
        "voiding_sentence": VOIDING_SENTENCES["C2"],
        "derangement_seed": seed,
        "derangement_seed_source": "int(book_digest[:16], 16)",
        "algorithm": "Sattolo (single cycle; no fixed points by construction)",
        "answerable_tasks_permuted": len(answerable),
        "mapping_digest": hashlib.sha256(
            canonical_json(mapping).encode("utf-8")
        ).hexdigest(),
        "fixed_points": [d for d, t in mapping if d == t],
    }


# --------------------------------------------------------------------------
# the run
# --------------------------------------------------------------------------


def validate_book_pins(book: dict) -> None:
    """L-1. An answerable task that pins nothing would score itself correct.

    `score_kernel` reduces to four assertions, and two of them -- the
    content containment and the receipt subset -- are vacuously true against
    an empty `content_must_contain` and an empty `receipt_expect`. A task
    like that would be graded on `status_expect` alone, which the dump
    server (C1) can satisfy by claiming a status. The committed book has no
    such task; this is a guard so a later edit cannot introduce one
    silently, not a change to anything the book says.

    Refusal and clarification tasks are exempt by design: the book's
    `zero_token_turns` rule says refusal tasks "carry an empty
    content_must_contain: there is no prose there for a score to reward",
    and they are gated on status and route instead.
    """

    unpinned = [
        task["task_id"]
        for task in book["tasks"]
        if is_answerable(task)
        and not task["expected"].get("content_must_contain")
        and not task["expected"].get("receipt_expect")
    ]
    if unpinned:
        raise Refused(
            "answerable tasks that pin neither content_must_contain nor "
            f"receipt_expect would grade themselves on status alone: {unpinned}"
        )


def probe_context_length(base_url: str, model: str, timeout: float) -> dict:
    """C-1(b). Read the context the server is ACTUALLY serving, and record it.

    Baseline manifest, `runtime.context.mechanism`: "the OpenAI-compat /v1
    layer ignores a num_ctx body field (verified live 2026-08-22), so the
    setting must be server-side and the run must record the observed
    context_length from /api/ps."

    `/api/ps` reports the loaded model's served context, which is the number
    that matters -- it reflects `OLLAMA_CONTEXT_LENGTH` as the process
    actually took it. `/api/show` is the fallback the coordinator named for
    the not-loaded case, and it is a **weaker** reading: it reports the
    model's trained capability, not the served window, so the result records
    which source answered and never lets the reader confuse them.
    """

    scheme, host, port, prefix = split_base_url(base_url)
    opener = HTTPSConnection if scheme == "https" else HTTPConnection
    report: dict[str, Any] = {
        "observed_context_length": None,
        "source": None,
        "matched_model": None,
        "errors": [],
        "probed": [f"{prefix}/api/ps", f"{prefix}/api/show"],
    }

    def fetch(method: str, path: str, body: dict | None) -> Any:
        conn = opener(host, port, timeout=timeout)
        try:
            payload = json.dumps(body).encode("utf-8") if body else None
            headers = {"Content-Type": "application/json"} if body else {}
            conn.request(method, path, body=payload, headers=headers)
            response = conn.getresponse()
            raw = response.read()
            if response.status != 200:
                raise OSError(f"HTTP {response.status}")
            return json.loads(raw.decode("utf-8"))
        finally:
            conn.close()

    try:
        listing = fetch("GET", f"{prefix}/api/ps", None)
        entries = listing.get("models") or []
        chosen = next(
            (
                entry
                for entry in entries
                if model in (entry.get("model"), entry.get("name"))
            ),
            None,
        )
        if chosen is None and entries:
            chosen = entries[0]
        if chosen is not None:
            length = chosen.get("context_length")
            if isinstance(length, int):
                report["observed_context_length"] = length
                report["source"] = "/api/ps (served context of the loaded model)"
                report["matched_model"] = chosen.get("model") or chosen.get("name")
                return report
        report["errors"].append("/api/ps: no loaded model reported a context_length")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report["errors"].append(f"/api/ps: {type(exc).__name__}: {exc}")

    try:
        shown = fetch("POST", f"{prefix}/api/show", {"model": model})
        info = shown.get("model_info") or {}
        candidates = [
            value
            for key, value in info.items()
            if key.endswith(".context_length") and isinstance(value, int)
        ]
        if isinstance(shown.get("context_length"), int):
            candidates.append(shown["context_length"])
        if candidates:
            report["observed_context_length"] = max(candidates)
            report["source"] = (
                "/api/show (model capability, NOT the served context: the "
                "model was not loaded when the run started)"
            )
            report["matched_model"] = model
            return report
        report["errors"].append("/api/show: no context_length in model_info")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report["errors"].append(f"/api/show: {type(exc).__name__}: {exc}")

    return report


def revalidate_rendering_digests(book: dict, repo: Path) -> tuple[bool, list[dict]]:
    """SPEC §6's seal witness, recomputed before anything is timed.

    SPEC §6: "any change to engine rendering after the task book seals
    **voids the run**" -- and: "the registered run revalidates them before
    timing anything."
    """

    drift = []
    for rel, pinned in sorted(book["rendering_module_digests"].items()):
        path = repo / rel
        actual = canonical_lf_sha256(path) if path.is_file() else None
        if actual != pinned:
            drift.append({"module": rel, "pinned": pinned, "actual": actual})
    return (not drift), drift


def select_tasks(book: dict, half: str, system: str) -> list[dict]:
    tasks = [t for t in book["tasks"] if t["half"] == half]
    if system in ("b-grounded", "b-ungrounded"):
        # Baseline arms run ANSWERABLE tasks only; the refusal and
        # clarification kinds gate the kernel (T5), not the model.
        return [t for t in tasks if is_answerable(t)]
    return tasks


def expected_task_count(book: dict, half: str, system: str) -> int:
    """M-4. The book's own arithmetic, for the arm's task set.

    The counts are recomputed by `tests/test_throughput_tasks.py` against the
    tasks themselves, so quoting them here makes a silently short run
    impossible: a network failure that dropped tasks, or a filter that
    over-matched, changes this number and the run refuses instead of
    reporting a median over a set nobody chose.
    """

    if system in ("b-grounded", "b-ungrounded"):
        return book["counts"]["answerable_by_half"][half]
    return book["counts"]["by_half"][half]


def context_bound_for(
    baseline: dict, probe: dict
) -> tuple[int | None, str | None]:
    """The token budget the pre-declared secondary median is taken against.

    Preference order, and why: the **observed** context wins, because the
    manifest's `runtime.context.mechanism` says "the run must record the
    observed context_length from /api/ps" and an observed number is a fact
    about the server that answered. The manifest's `configured_tokens`
    (32768, set via `OLLAMA_CONTEXT_LENGTH`) is the fallback so the kernel
    and dump arms -- which serve no model and have nothing to probe -- can
    still carry the same restricted median over the same task set, which is
    the only way the secondary K can be recomputed from two files. The source
    is recorded either way; a reader is never left guessing which one applied.
    """

    observed = probe.get("observed_context_length")
    if isinstance(observed, int):
        return observed, f"observed: {probe.get('source')}"
    configured = baseline["runtime"].get("context", {}).get("configured_tokens")
    if isinstance(configured, int):
        return configured, (
            "manifest runtime.context.configured_tokens (no live server to "
            "probe on this arm, or the probe failed)"
        )
    return None, None


def load_observed_from_result(
    path: Path, book_digest: str, half: str, system: str
) -> tuple[dict, dict[str, list[TurnResult]]]:
    """M-5. Rebuild a run's responses and clocks from its result file.

    The point of the offline mode is that half B is spent once. Everything
    needed to re-score is in the file the registered run wrote -- each turn's
    `content`, its `x_corollary`, and its measured seconds -- so C2 is a
    re-scoring of that record, not a second interrogation of the sealed half.
    The three refusals below are the ones that would make the derivation a
    statement about some other run.
    """

    source = read_json(path)
    if source.get("schema") != SCHEMA:
        raise Refused(f"not a throughput result file: {path}")
    if source["book_digest"] != book_digest:
        raise Refused(
            f"{path} was measured against a different task book "
            f"({source['book_digest'][:12]}... vs {book_digest[:12]}...)"
        )
    if source["run"]["half"] != half:
        raise Refused(
            f"{path} is a half-{source['run']['half']} run; --half {half} asked"
        )
    if source["run"]["system"] != system:
        raise Refused(
            f"{path} measured {source['run']['system']}; --system {system} asked"
        )
    if source.get("control", {}).get("control") == "C2":
        raise Refused(f"{path} is already a shuffled control; deranging it twice")

    observed: dict[str, list[TurnResult]] = {}
    for record in source["per_task"]:
        if not record.get("applicable"):
            continue
        turns = []
        for entry in record["turns"]:
            if "content" not in entry:
                raise Refused(
                    f"{path} records no turn content for {record['task_id']}; "
                    "it was written before the result file carried responses "
                    "and cannot be re-scored offline"
                )
            turns.append(
                TurnResult(
                    content=entry["content"],
                    x_corollary=entry.get("x_corollary"),
                    ttft_s=entry.get("ttft_s"),
                    elapsed_s=entry.get("elapsed_s") or 0.0,
                    chunk_count=entry.get("chunks") or 0,
                    finish_reason=entry.get("finish_reason"),
                    http_status=entry.get("http_status") or 0,
                    error=entry.get("error"),
                )
            )
        observed[record["task_id"]] = turns
    return source, observed


def run_kernel_like(
    tasks: Sequence[dict],
    url: str,
    system: str,
    timeout: float,
    verbose: bool,
) -> dict[str, list[TurnResult]]:
    observed: dict[str, list[TurnResult]] = {}
    for position, task in enumerate(tasks, start=1):
        model = "control/dump" if system == "dump" else task["profile"]
        turns: list[TurnResult] = []
        for messages in kernel_requests(task):
            turns.append(
                post_stream(
                    url,
                    {"model": model, "messages": messages, "stream": True},
                    timeout,
                )
            )
        observed[task["task_id"]] = turns
        if verbose:
            print(
                f"[{position}/{len(tasks)}] {task['task_id']} "
                f"{sum(t.elapsed_s for t in turns):.3f}s",
                file=sys.stderr,
            )
    return observed


def materials_sizing(
    task: dict, materials: Materials, count_tokens: Callable[[str], int]
) -> tuple[str, dict]:
    """The size of a task's B-grounded MATERIALS block, in chars and tokens.

    C-1(a): `materials_tokens` is counted with the **pinned** tokenizer --
    the same one that counts useful tokens on both contenders -- because the
    number it is compared against (the observed context window) is a token
    budget, and a character count cannot be compared to a token budget
    without inventing a ratio.

    This is a property of the task and the tokenizer, not of any run, so it
    is computed identically on every arm and never inside a timed region.
    """

    text, skipped = materials.for_task(task)
    empty = text == "none"
    return text, {
        "materials_chars": 0 if empty else len(text),
        "materials_tokens": 0 if empty else count_tokens(text),
        "materials_none": empty,
        "refs_skipped": skipped,
    }


def run_baseline(
    tasks: Sequence[dict],
    url: str,
    system: str,
    baseline: dict,
    materials: Materials,
    count_tokens: Callable[[str], int],
    timeout: float,
    verbose: bool,
) -> tuple[dict[str, list[TurnResult]], dict[str, dict]]:
    observed: dict[str, list[TurnResult]] = {}
    context: dict[str, dict] = {}
    model = baseline_model_name(baseline)
    extra = sampling_body(baseline)
    template = baseline["arms"]["B-grounded"]["prompt_template"]
    for position, task in enumerate(tasks, start=1):
        if system == "b-grounded":
            text, sizing = materials_sizing(task, materials, count_tokens)
            messages = grounded_messages(task, baseline, text)
            sizing["prompt_tokens"] = count_tokens(
                template["system"] + "\n" + messages[1]["content"]
            )
            context[task["task_id"]] = sizing
        else:
            messages = ungrounded_messages(task)
            context[task["task_id"]] = {
                "materials_chars": 0,
                "materials_tokens": 0,
                "materials_none": True,
                "refs_skipped": [],
                "prompt_tokens": count_tokens(
                    "\n".join(m["content"] for m in messages)
                ),
            }
        body = {"model": model, "messages": messages, "stream": True, **extra}
        observed[task["task_id"]] = [post_stream(url, body, timeout)]
        if verbose:
            print(
                f"[{position}/{len(tasks)}] {task['task_id']} "
                f"{observed[task['task_id']][0].elapsed_s:.3f}s",
                file=sys.stderr,
            )
    return observed, context


def warm_up(url: str, system: str, baseline: dict, timeout: float) -> dict:
    """One unmeasured request per system, per the manifest's `warmup` rule.

    Manifest: "both contenders warm: one unmeasured warmup request per system
    before the run; the baseline model is loaded and resident before timing
    starts."
    """

    if system in ("b-grounded", "b-ungrounded"):
        body = {
            "model": baseline_model_name(baseline),
            "messages": [{"role": "user", "content": WARMUP_LINE_MODEL}],
            "stream": True,
            **sampling_body(baseline),
        }
    else:
        model = "control/dump" if system == "dump" else "corollary/kernel"
        body = {
            "model": model,
            # SPEC §5 row 0: "An empty-string user turn is **served**, not
            # rejected: it is the engine's registered empty line."
            "messages": [{"role": "user", "content": WARMUP_LINE_KERNEL}],
            "stream": True,
        }
    result = post_stream(url, body, timeout)
    return {
        "sent": True,
        "measured": False,
        "http_status": result.http_status,
        "elapsed_s": round(result.elapsed_s, 6),
        "error": result.error,
    }


def build_records(
    tasks: Sequence[dict],
    observed: dict[str, list[TurnResult]],
    system: str,
    count_tokens: Callable[[str], int],
    context: dict[str, dict],
) -> list[dict]:
    records = []
    for task in tasks:
        turns = observed[task["task_id"]]
        final = turns[-1]
        scored = (
            score_baseline(task, final.content)
            if system in ("b-grounded", "b-ungrounded")
            else score_kernel(task, turns)
        )
        elapsed = sum(t.elapsed_s for t in turns)
        # Time to first useful token, from the task's own start: the clock
        # runs from the first request, and the token that could be useful is
        # in the final turn. Every answerable task in the book is single-turn,
        # so this equals the final turn's TTFT there; the cumulative form is
        # what makes a multi-turn record honest.
        prior = sum(t.elapsed_s for t in turns[:-1])
        ttft = None if final.ttft_s is None else prior + final.ttft_s

        answerable = is_answerable(task)
        tokens = count_tokens(final.content)
        # DESIGN §3: the numerator "counts only correctly-and-receipted
        # answers". On the B arm receipts are not asked for (see
        # B_SIDE_CORRECTNESS_RULE), so correctness alone carries it there.
        useful = 0
        if answerable and scored.correct:
            useful = tokens if system in ("b-grounded", "b-ungrounded") else (
                tokens if scored.receipted else 0
            )

        status = (final.x_corollary or {}).get("status")
        record = {
            "task_id": task["task_id"],
            "kind": task["kind"],
            "half": task["half"],
            "profile": task["profile"],
            "check": task["expected"]["check"],
            "outcome_expect": task["expected"]["outcome"],
            "status_expect": task["expected"]["status_expect"],
            "route_expect": task.get("route_expect"),
            "answerable": answerable,
            "applicable": True,
            "elapsed_s": round(elapsed, 6),
            "ttft_s": None if ttft is None else round(ttft, 6),
            "tokens": tokens,
            "useful_tokens": useful,
            "correct": scored.correct,
            "receipted": scored.receipted,
            "status": status,
            "route": (final.x_corollary or {}).get("route"),
            "status_ok": scored.status_ok,
            "content_ok": scored.content_ok,
            "receipt_ok": scored.receipt_ok,
            "need_ok": scored.need_ok,
            "route_ok": scored.route_ok,
            "missing_strings": scored.missing_strings,
            "refusal_gate_ok": scored.refusal_gate_ok,
            "waiting_legs": scored.waiting_legs,
            "http_status": final.http_status,
            "error": final.error,
            # The response itself rides in the record. Three reasons, all
            # named: T7 re-validates receipt fields client-side against the
            # committed artifacts they cite, M-5's offline C2 derives the
            # shuffled control from a finished result file rather than
            # re-executing the sealed half, and a scored number nobody can
            # see the text behind is not evidence. A result file that dropped
            # the answers could support none of the three without spending
            # half B twice.
            "turns": [
                {
                    "index": index,
                    "elapsed_s": round(t.elapsed_s, 6),
                    "ttft_s": None if t.ttft_s is None else round(t.ttft_s, 6),
                    "chunks": t.chunk_count,
                    "content_chars": len(t.content),
                    "content": t.content,
                    "x_corollary": t.x_corollary,
                    "status": (t.x_corollary or {}).get("status"),
                    "finish_reason": t.finish_reason,
                    "http_status": t.http_status,
                    "error": t.error,
                }
                for index, t in enumerate(turns)
            ],
        }
        if system in ("b-grounded", "b-ungrounded"):
            # M-1. The residuals are what the B-side rule actually searched
            # for; printing them is what lets a reader check the rule rather
            # than trust it.
            record["b_residuals"] = [
                {
                    "pinned": pinned,
                    "residual": strip_label(pinned),
                    "stripped": strip_label(pinned) != pinned,
                    "found": strip_label(pinned) in final.content,
                }
                for pinned in task["expected"]["content_must_contain"]
            ]
        if task["task_id"] in context:
            record.update(context[task["task_id"]])

        # The scored response, at the TOP level of the record, on EVERY arm.
        #
        # This is where a reader looks, and until 2026-08-22 it was not here:
        # the text lived only inside `turns[]`, so a live b-grounded trial
        # read `record["content"]` and got the empty string on every task
        # while the scorer had plainly seen real text. The number and the
        # text behind it now sit in one place, and the assignment happens
        # AFTER the per-task context merge above so that no key added to that
        # dict later can ever silently empty the response again -- the bug
        # class, not just the bug.
        #
        # `content` is exactly the string the scorer was handed: the FINAL
        # turn's, which is the one `score_kernel`/`score_baseline` read. The
        # per-turn copies stay, because a multi-turn task's earlier turns are
        # what M-5's offline derivation and the clarification leg need.
        record["content"] = final.content
        record["content_chars"] = len(final.content)
        record["x_corollary"] = final.x_corollary
        record["scored_content_is"] = (
            "the final turn's content, byte for byte, as handed to the scorer"
        )
        records.append(record)
    return records


def charge_refusals(records: list[dict], system: str) -> dict:
    """DESIGN §3's frozen anti-shirking rule, as a post-pass.

    DESIGN §3: "an answerable task the system REFUSES contributes zero tokens
    plus a frozen time charge equal to that system's slowest correct answer
    -- so a refusal is never a cheap way to shed a hard task's clock."

    It has to be a post-pass because "that system's slowest correct answer"
    is not known until every task has been timed.

    Judgment recorded: on the kernel and dump systems "refuses" is read
    mechanically off the wire -- a non-answering status from SPEC §6.1's list
    -- and a task the book scored CORRECT is never charged, which is what
    keeps a closure task's certified bounded negative (`exhausted`, and an
    answer per the book's `bounded_negative_is_an_answer`) out of the charge.
    On the baseline arms there is no status field to read, so only an empty
    answer counts as a refusal; a model that answers wrongly keeps its own
    clock, which is the harsher reading for the kernel and therefore the one
    to take.
    """

    correct_times = [
        r["elapsed_s"] for r in records if r["answerable"] and r["correct"]
    ]
    slowest = max(correct_times) if correct_times else 0.0
    charged = []
    for record in records:
        record["charged_elapsed_s"] = record["elapsed_s"]
        record["refusal_charge_applied"] = False
        if not record["answerable"] or record["correct"]:
            continue
        if system in ("b-grounded", "b-ungrounded"):
            refused = record["tokens"] == 0
        else:
            refused = (
                record["status"] in NON_ANSWERING_STATUSES
                or record["status"] is None
                or record["tokens"] == 0
            )
        if refused and slowest > record["elapsed_s"]:
            record["charged_elapsed_s"] = round(slowest, 6)
            record["refusal_charge_applied"] = True
            charged.append(record["task_id"])
        elif refused:
            record["refusal_charge_applied"] = True
    for record in records:
        elapsed = record["charged_elapsed_s"]
        record["perceived_tps"] = (
            round(record["useful_tokens"] / elapsed, 6) if elapsed > 0 else None
        )
    return {
        "rule": (
            "an answerable task the system REFUSES contributes zero tokens "
            "plus a frozen time charge equal to that system's slowest correct "
            "answer (DESIGN-grounded-throughput 3)"
        ),
        "slowest_correct_answer_s": round(slowest, 6),
        "tasks_charged": charged,
    }


def apply_context_fit(records: list[dict], bound: int | None) -> None:
    """C-1(b). Mark every task whose grounded materials cannot be held.

    Baseline manifest, `runtime.context.truncation_disclosure`: "The
    stopwatch records materials_chars and materials_tokens per task; any task
    whose materials exceed the observed context is reported
    materials-truncated in the result."

    `None` means *unknown*, not *fine*: an unprobed server and a fitting task
    must not read the same in the file.
    """

    for record in records:
        if not record.get("answerable"):
            continue
        tokens = record.get("materials_tokens")
        if bound is None or tokens is None:
            record["materials_truncated"] = None
        else:
            record["materials_truncated"] = tokens > bound


def summarize(records: list[dict], book: dict, system: str) -> dict:
    answerable = [r for r in records if r["answerable"] and r["applicable"]]
    by_kind = {}
    for kind in ANSWERABLE_KINDS:
        rows = [r for r in answerable if r["kind"] == kind]
        correct = [r for r in rows if r["correct"] and (
            r["receipted"] or system in ("b-grounded", "b-ungrounded")
        )]
        by_kind[kind] = {
            "tasks": len(rows),
            "correct_with_receipt": len(correct),
            "rate": round(len(correct) / len(rows), 6) if rows else None,
            "floor": 0.80,
            "meets_floor": (len(correct) / len(rows) >= 0.80) if rows else None,
        }

    overall_correct = [
        r
        for r in answerable
        if r["correct"] and (
            r["receipted"] or system in ("b-grounded", "b-ungrounded")
        )
    ]
    overall_rate = (
        round(len(overall_correct) / len(answerable), 6) if answerable else None
    )

    refusals = [r for r in records if r["kind"] == "refusal_due" and r["applicable"]]
    refusal_ok = [r for r in refusals if r["refusal_gate_ok"]]

    legs = [
        leg
        for r in records
        if r["kind"] == "clarification_due" and r["applicable"]
        for leg in r["waiting_legs"]
    ]
    legs_ok = [leg for leg in legs if leg["ok"]]

    tps = [r["perceived_tps"] for r in answerable if r["perceived_tps"] is not None]
    # H-2. T4's leg is "median time-to-first-**useful**-token", and a token
    # is useful only on a task the system answered correctly-and-receipted
    # (DESIGN §3). A refusal's first byte is not a useful token, so it is not
    # in this series; the all-answerable series is kept beside it, under a
    # name that says what it actually measures.
    ttft_useful = [
        r["ttft_s"]
        for r in answerable
        if r["ttft_s"] is not None and r["useful_tokens"] > 0
    ]
    ttfa_any = [r["ttft_s"] for r in answerable if r["ttft_s"] is not None]

    fitting = [r for r in answerable if r.get("materials_truncated") is False]
    fit_known = [r for r in answerable if r.get("materials_truncated") is not None]
    secondary_tps = [
        r["perceived_tps"] for r in fitting if r["perceived_tps"] is not None
    ]

    return {
        "tasks_measured": len(records),
        "answerable_tasks": len(answerable),
        "correctness_by_kind": by_kind,
        "correctness_overall": {
            "tasks": len(answerable),
            "correct_with_receipt": len(overall_correct),
            "rate": overall_rate,
            "floor": 0.90,
            "meets_floor": (overall_rate >= 0.90) if overall_rate is not None else None,
        },
        "refusal_gate": {
            "tasks": len(refusals),
            "refused": len(refusal_ok),
            "rate": round(len(refusal_ok) / len(refusals), 6) if refusals else None,
            "floor": 1.0,
            "meets_floor": (len(refusal_ok) == len(refusals)) if refusals else None,
        },
        "clarification_gate": {
            "marked_waiting_turns": len(legs),
            "waiting_returned": len(legs_ok),
            "rate": round(len(legs_ok) / len(legs), 6) if legs else None,
            "floor": 1.0,
            "meets_floor": (len(legs_ok) == len(legs)) if legs else None,
            "graded": "per marked WAITING turn (book scoring_rules.clarification_leg)",
        },
        "median_perceived_throughput_tps": median_or_none(tps),
        "median_ttft_s": median_or_none(ttft_useful),
        "median_ttft_task_set": (
            "answerable tasks with useful_tokens > 0 -- T4's "
            "time-to-first-USEFUL-token leg"
        ),
        "median_ttfa_s": median_or_none(ttfa_any),
        "median_ttfa_task_set": (
            "every answerable task that produced any content delta -- "
            "time to first any-token, reported beside the gate statistic and "
            "not the gate statistic"
        ),
        "median_perceived_throughput_tps_materials_fit": median_or_none(
            secondary_tps
        ),
        "materials_fit_tasks": len(fitting),
        "materials_fit_known_for": len(fit_known),
        "materials_fit_task_ids": sorted(r["task_id"] for r in fitting),
        "pre_declared_secondary_label": None,  # filled by run() from the manifest
        "useful_tokens_total": sum(r["useful_tokens"] for r in answerable),
        "elapsed_total_s": round(sum(r["charged_elapsed_s"] for r in records), 6),
        "elapsed_total_task_set": (
            "every task measured on this arm, charged elapsed -- answerable "
            "and non-answerable alike"
        ),
        "elapsed_total_answerable_s": round(
            sum(r["charged_elapsed_s"] for r in answerable), 6
        ),
        "gates_are_reported_not_enforced": (
            "the stopwatch measures; adjudication reads this file "
            "(DESIGN-grounded-throughput 6, 7)"
        ),
        "book_expected_counts": book["counts"]["by_kind_half"],
    }


def reconcile_metrics(records: list[dict], summary: dict, charge: dict) -> dict:
    """H-1. The two readings of "perceived throughput", side by side.

    DESIGN §6 T4 states the gate as a **median**: "the kernel's median
    perceived throughput over half-B answerable tasks must be >= 5x
    B-grounded's". DESIGN §3 states the metric as a **ratio of totals**:
    "useful tokens / client wall-clock, where the numerator counts only
    correctly-and-receipted answers, the denominator counts every task's
    elapsed time". Those are not the same statistic, and the difference is
    not cosmetic:

    - Under the median of per-task ratios, **non-answerable elapsed never
      enters** -- the refusal and clarification tasks are not in the series
      at all -- and the §3 refusal time-charge is **inert**, because a
      refused answerable task contributes `0 / anything = 0` whether it is
      charged one second or twenty. The charge changes a zero into a zero.
    - Under the §3-literal aggregate it bites, because the charged seconds
      land in a shared denominator and drag the whole ratio down.

    The gate statistic is the median, because T4 says median and T4 is what
    freezes at K = 5. The aggregate is computed here over **the same task
    set** (the half's answerable tasks, with charges applied) so the two can
    be read against each other on both arms rather than one arm quoting the
    flattering one. Neither is adjudicated here; both are recorded.
    """

    answerable = [r for r in records if r.get("answerable") and r.get("applicable")]
    useful = sum(r["useful_tokens"] for r in answerable)
    charged = sum(r["charged_elapsed_s"] for r in answerable)
    uncharged = sum(r["elapsed_s"] for r in answerable)
    non_answerable = [
        r for r in records if r.get("applicable") and not r.get("answerable")
    ]
    fitting = [r for r in answerable if r.get("materials_truncated") is False]
    fit_useful = sum(r["useful_tokens"] for r in fitting)
    fit_charged = sum(r["charged_elapsed_s"] for r in fitting)

    return {
        "t4_gate_statistic": (
            "median of the per-task ratio useful_tokens / charged_elapsed_s, "
            "taken over the half's answerable tasks"
        ),
        "t4_gate_value_tps": summary["median_perceived_throughput_tps"],
        "design_sentence_t4": DESIGN_SENTENCE_T4,
        "design_sentence_section_3": DESIGN_SENTENCE_SECTION_3,
        "under_the_median": {
            "non_answerable_elapsed_excluded": True,
            "non_answerable_tasks": len(non_answerable),
            "non_answerable_elapsed_s": round(
                sum(r["charged_elapsed_s"] for r in non_answerable), 6
            ),
            "refusal_time_charge_inert": True,
            "why_inert": (
                "a refused answerable task scores 0 useful tokens, so its "
                "ratio is zero at any denominator; the charge moves a zero "
                "to a zero and only bites in the aggregate below"
            ),
            "tasks_charged": charge["tasks_charged"],
        },
        "aggregate_perceived_tps": (
            round(useful / charged, 6) if charged > 0 else None
        ),
        "aggregate_task_set": (
            "the half's answerable tasks, charged elapsed (the same set the "
            "median is taken over) -- the DESIGN section-3 literal reading, "
            "where the refusal time charge does bite"
        ),
        "aggregate_useful_tokens": useful,
        "aggregate_charged_elapsed_s": round(charged, 6),
        "aggregate_uncharged_elapsed_s": round(uncharged, 6),
        "aggregate_charge_penalty_s": round(charged - uncharged, 6),
        "aggregate_perceived_tps_materials_fit": (
            round(fit_useful / fit_charged, 6) if fit_charged > 0 else None
        ),
        "median_perceived_tps_materials_fit": summary[
            "median_perceived_throughput_tps_materials_fit"
        ],
        "adjudication": (
            "K = 5 freezes on the median (T4). The aggregate is reported so a "
            "reader can see what the section-3 wording would have said over "
            "the same tasks; neither number is gated here"
        ),
    }


def run(args: argparse.Namespace) -> dict:
    if args.control_shuffle and args.system != "kernel":
        raise Refused("--control-shuffle applies to the kernel arm only")

    repo = REPO
    book_path = Path(args.book)
    book_path = book_path if book_path.is_absolute() else repo / book_path
    baseline_path = Path(args.baseline)
    baseline_path = (
        baseline_path if baseline_path.is_absolute() else repo / baseline_path
    )

    book = read_json(book_path)
    baseline = read_json(baseline_path)
    if book.get("schema") != BOOK_SCHEMA:
        raise Refused(f"not a task book: {book_path}")
    if baseline.get("schema") != BASELINE_SCHEMA:
        raise Refused(f"not a baseline manifest: {baseline_path}")

    book_digest = canonical_lf_sha256(book_path)
    baseline_digest = canonical_lf_sha256(baseline_path)

    revalidated, drift = revalidate_rendering_digests(book, repo)
    if not revalidated:
        print(
            "VOID WARNING: the engine's rendering changed after the task book "
            "sealed; SPEC-chat-completions-skin §6 says that voids the run.",
            file=sys.stderr,
        )
        for row in drift:
            print(
                f"  {row['module']}: pinned {row['pinned']} actual {row['actual']}",
                file=sys.stderr,
            )
        if not args.force_void:
            raise Refused(
                "refusing to time a run the seal already voids; pass "
                "--force-void only to record the void deliberately."
            )

    # The book's own claims are checked before the tokenizer pin, so a
    # miscounted or unpinned book reports the fault a reader can act on
    # rather than the tokenizer's (which would be true of any book).
    validate_book_pins(book)
    tasks = select_tasks(book, args.half, args.system)
    if not tasks:
        raise Refused(f"no tasks selected for half {args.half}")
    expected_count = expected_task_count(book, args.half, args.system)
    if len(tasks) != expected_count:
        raise Refused(
            f"the half's task set does not match the book's own arithmetic: "
            f"selected {len(tasks)}, book says {expected_count} for "
            f"half {args.half} on {args.system}"
        )

    count_tokens = load_token_counter(baseline, repo)

    materials = Materials(repo)
    context: dict[str, dict] = {}
    control: dict[str, Any] = {}
    context_probe: dict[str, Any] = {
        "observed_context_length": None,
        "source": None,
        "errors": ["not probed: this arm serves no model"],
    }

    if args.from_result:
        # M-5. C2 derived from a finished result file. The registered half is
        # spent exactly once; the shuffled control re-scores the answers that
        # run already produced, with their clocks, rather than asking the
        # sealed half a second time.
        source_path = Path(args.from_result)
        source_path = source_path if source_path.is_absolute() else repo / source_path
        source, observed = load_observed_from_result(
            source_path, book_digest, args.half, args.system
        )
        missing = [t["task_id"] for t in tasks if t["task_id"] not in observed]
        if missing:
            raise Refused(
                f"{source_path} carries no response for {len(missing)} of the "
                f"half's tasks, e.g. {missing[:3]}"
            )
        url = source["run"].get("url")
        started = now_iso()
        warmup = dict(source["run"].get("warmup_detail") or {})
        warmup["inherited_from"] = str(source_path)
        context_probe = dict(source.get("context_probe") or context_probe)
        for record in source["per_task"]:
            if record.get("applicable"):
                context[record["task_id"]] = {
                    key: record[key]
                    for key in (
                        "materials_chars", "materials_tokens",
                        "materials_none", "refs_skipped", "prompt_tokens",
                    )
                    if key in record
                }
        control = apply_shuffle(tasks, observed, book_digest)
        control["derived_offline"] = True
        control["derived_from"] = str(source_path)
        control["derived_from_run"] = {
            "system": source["run"]["system"],
            "half": source["run"]["half"],
            "registered": source["run"]["registered"],
            "started": source["run"]["started"],
        }
        control["no_re_execution"] = (
            "the sealed half was not asked a second time: the responses and "
            "their clocks come from the recorded run named above"
        )
    else:
        url = args.url or (
            baseline["runtime"]["endpoint"]
            if args.system in ("b-grounded", "b-ungrounded")
            else None
        )
        if not url:
            raise Refused("--url is required for this system")

        started = now_iso()
        if args.system in ("b-grounded", "b-ungrounded"):
            # Probed BEFORE the warmup so the number in the file describes the
            # server the run is about to time, and recorded whatever it says.
            context_probe = probe_context_length(
                url, baseline_model_name(baseline), args.timeout
            )
        warmup = warm_up(url, args.system, baseline, args.timeout)

        if args.system in ("b-grounded", "b-ungrounded"):
            observed, context = run_baseline(
                tasks, url, args.system, baseline, materials, count_tokens,
                args.timeout, args.verbose,
            )
        else:
            observed = run_kernel_like(
                tasks, url, args.system, args.timeout, args.verbose
            )

        if args.system == "dump":
            control = {
                "control": "C1",
                "voiding_sentence": VOIDING_SENTENCES["C1"],
                "comparison_is_the_adjudication's": (
                    "this file carries the numbers; the >1%-of-the-kernel "
                    "check is computed by the adjudication, not by the "
                    "stopwatch"
                ),
            }
        if args.control_shuffle:
            control = apply_shuffle(tasks, observed, book_digest)
            control["derived_offline"] = False

        if args.system not in ("b-grounded", "b-ungrounded"):
            # The same task-level materials sizing the grounded arm computes
            # inline, computed here AFTER every clock has stopped, so the two
            # arms' files carry the same `materials_tokens` for the same tasks
            # and the pre-declared secondary median is taken over one set on
            # both sides. Nothing here can touch a measured interval.
            for task in tasks:
                if is_answerable(task):
                    context[task["task_id"]] = materials_sizing(
                        task, materials, count_tokens
                    )[1]

    records = build_records(tasks, observed, args.system, count_tokens, context)
    if len(records) != expected_count:
        raise Refused(
            f"measured {len(records)} tasks but the book says {expected_count} "
            f"for half {args.half} on {args.system}"
        )

    context_bound, bound_source = context_bound_for(baseline, context_probe)
    apply_context_fit(records, context_bound)

    skipped_kinds = []
    if args.system in ("b-grounded", "b-ungrounded"):
        for task in book["tasks"]:
            if task["half"] != args.half or is_answerable(task):
                continue
            skipped_kinds.append(
                {
                    "task_id": task["task_id"],
                    "kind": task["kind"],
                    "applicable": False,
                    "reason": (
                        "not-applicable: refusal_due and clarification_due "
                        "gate the kernel (T5), not the baseline model"
                    ),
                }
            )

    charge = charge_refusals(records, args.system)
    summary = summarize(records, book, args.system)
    summary["pre_declared_secondary_label"] = (
        baseline["runtime"].get("context", {}).get("pre_declared_secondary")
    )
    summary["materials_fit_bound_tokens"] = context_bound
    summary["materials_fit_bound_source"] = bound_source
    reconciliation = reconcile_metrics(records, summary, charge)

    result = {
        "schema": SCHEMA,
        "run": {
            "system": args.system,
            "half": args.half,
            "registered": bool(args.registered),
            "url": url,
            "started": started,
            "finished": now_iso(),
            "warmup": True,
            "warmup_detail": warmup,
            "overwrote_existing_out": bool(args.overwrite),
            "forced_over_void": bool(args.force_void),
            "derived_offline_from": args.from_result,
            "measured_by": "scripts/measure_throughput.py",
            "boundary": (
                "public HTTP API only; no engine module imported (checked in "
                "this process, see the clean-imports line on stdout)"
            ),
        },
        "book": str(book_path.relative_to(repo)) if book_path.is_relative_to(repo)
        else str(book_path),
        "book_digest": book_digest,
        "baseline_digest": baseline_digest,
        "rendering_digests_revalidated": revalidated,
        "rendering_digest_drift": drift,
        "scoring_rules_applied": book["scoring_rules"],
        "useful_token_rule": (
            "useful tokens = the tokens of the assistant message content "
            "field only, under the pinned baseline tokenizer; vendor "
            "extension payloads, receipt structures, ids and digests never "
            "count, and the server's usage block is never read "
            "(DESIGN-grounded-throughput 3; SPEC-chat-completions-skin 6)"
        ),
        "refusal_time_charge": charge,
        "tokenizer": {
            "file": baseline["tokenizer"]["file"],
            "sha256": baseline["tokenizer"]["sha256"],
            "verified": True,
        },
        "control": control,
        "context_probe": context_probe,
        "context_pin": baseline["runtime"].get("context", {}),
        "metric_reconciliation": reconciliation,
        "per_task": records + skipped_kinds,
        "summary": summary,
    }
    if args.system in ("b-grounded", "b-ungrounded"):
        result["b_side_correctness_rule"] = B_SIDE_CORRECTNESS_RULE
        result["baseline_arm"] = {
            "arm": args.system,
            "model": baseline_model_name(baseline),
            "sampling_requested": sampling_body(baseline),
            "sampling_source": SAMPLING_SOURCE,
            "prompt_template": baseline["arms"]
            .get("B-grounded", {})
            .get("prompt_template")
            if args.system == "b-grounded"
            else None,
            "context_rule": baseline["arms"][
                "B-grounded" if args.system == "b-grounded" else "B-ungrounded"
            ]["context_rule"],
            "materials_deviation": (
                "the closure reports carry no key named canonical_routes; "
                "the routes they hold are convergence_cells' primary_route / "
                "alternate_route pairs, and those are what this arm injected "
                "beside the world registration and the states array"
            )
            if args.system == "b-grounded"
            else None,
        }
    return result


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="measure_throughput.py",
        description=(
            "Client-side stopwatch for DESIGN-grounded-throughput's perceived "
            "useful-token throughput. Speaks the public HTTP API only."
        ),
    )
    parser.add_argument("--book", default=DEFAULT_BOOK)
    parser.add_argument("--baseline", default=DEFAULT_BASELINE)
    parser.add_argument(
        "--system",
        required=True,
        choices=("kernel", "b-grounded", "b-ungrounded", "dump"),
    )
    parser.add_argument(
        "--url",
        default=None,
        help="base URL of the server; defaults to the manifest endpoint on "
             "the baseline arms",
    )
    parser.add_argument(
        "--half",
        default="A",
        choices=("A", "B"),
        help="half A is the development half; half B is sealed and requires "
             "--registered",
    )
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--control-shuffle",
        action="store_true",
        help="C2: derange the answers across the half's answerable tasks, "
             "keeping every clock where it was measured (kernel arm only)",
    )
    parser.add_argument(
        "--from",
        dest="from_result",
        default=None,
        metavar="RESULT.JSON",
        help="derive --control-shuffle offline from an existing result file "
             "instead of re-executing; this is how C2 runs against the "
             "registered half-B result, which is spent exactly once",
    )
    parser.add_argument("--registered", action="store_true")
    # M-2. Two different things were sharing one flag: overwriting a file is a
    # bookkeeping decision, recording a run the seal already voids is an
    # evidentiary one. They now need separate consent and are recorded
    # separately in the result.
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="permit writing over an existing --out file",
    )
    parser.add_argument(
        "--force-void",
        action="store_true",
        help="permit timing a run whose rendering-module digests no longer "
             "match the sealed task book (SPEC 6: that voids the run)",
    )
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        # Ordered so that a refusal names the reason a reader can act on,
        # before the tokenizer pin (which refuses for its own reason) can
        # mask it.
        if args.half == "B" and not args.registered:
            raise Refused(
                "half B is sealed: the book's seal says 'implementation and "
                "debugging may exercise half A only; half B's first execution "
                "is the registered run'. Pass --registered to spend it."
            )
        if args.half == "B":
            print("=" * 72)
            print("REGISTERED RUN: this is half B's first and only execution.")
            print("The book seals half B until now; a second run does not")
            print("replace this one, it invalidates the seal.")
            print("=" * 72)

        if args.from_result and not args.control_shuffle:
            raise Refused(
                "--from derives the C2 control offline and means nothing on "
                "its own; pass --control-shuffle with it."
            )

        out = Path(args.out)
        out = out if out.is_absolute() else Path.cwd() / out
        if out.exists() and not args.overwrite:
            raise Refused(
                f"refusing to overwrite an existing result file: {out}. A "
                "registered run is written once; pass --overwrite only to "
                "discard a run you meant to discard."
            )

        result = run(args)
        # L-5. The guard runs BEFORE the file exists. A result written first
        # and then found to have been produced by a process that imported the
        # engine is a result someone will read anyway; a refusal that leaves
        # no file behind is the only version of this check that cannot be
        # ignored after the fact.
        assert_clean_imports()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2

    print(CLEAN_IMPORTS_LINE)
    summary = result["summary"]
    print(f"wrote {out}")
    print(
        f"  answerable tasks: {summary['answerable_tasks']}  "
        f"overall correct-with-receipt: "
        f"{summary['correctness_overall']['rate']}"
    )
    print(
        f"  median perceived throughput: "
        f"{summary['median_perceived_throughput_tps']} tok/s  "
        f"(aggregate "
        f"{result['metric_reconciliation']['aggregate_perceived_tps']} tok/s)"
    )
    print(
        f"  median TTFT (useful): {summary['median_ttft_s']} s  "
        f"median TTFA (any token): {summary['median_ttfa_s']} s"
    )
    print(
        f"  secondary median over materials that fit "
        f"({summary['materials_fit_tasks']}/{summary['answerable_tasks']} "
        f"tasks, bound {summary['materials_fit_bound_tokens']}): "
        f"{summary['median_perceived_throughput_tps_materials_fit']} tok/s"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
