#!/usr/bin/env python3
"""The chat-completions skin: one session engine, a second renderer.

This is `docs/SPEC-chat-completions-skin.md` made executable, and the spec is
normative: every clause below cites the section it implements. What this file
is NOT is the part worth stating first — it is not a second engine. Every
token it serves is a *pass-through* of what `harness.route_line` or
`conversation.ConversationSession.say` already rendered for the TTY and the
tests (A-IH6, spec §1). The skin owns exactly one authored string in the whole
serving path, named in §6 and quoted at :data:`ABSTENTION_ACKNOWLEDGEMENT`.

Stdlib only (`http.server`), bound to 127.0.0.1, one owner, no auth — the
substrate's shipped single-session scope (§2). The single exception to
"stdlib only" is the *informational* `usage` block, which is counted with the
digest-pinned baseline tokenizer through the `tokenizers` package when that
package imports AND the pinned file is present with the pinned digest, and is
**omitted entirely** otherwise (§6: informational only, never approximated).
The stopwatch counts `content` client-side and never reads `usage`.

Three properties are the contract, each one visible in the code rather than
promised in a docstring:

**Replay, not resumption (¶DEV-1).** Every request is served by replaying the
message array's user turns into a *fresh* session object (§4). No ledger
snapshot is imported, `save`/`restore` are not in the serving path, and no
stored authority is asserted. The session cache below is an optimization whose
key is the canonical hash of the exact message prefix, so a cache hit is
replay-equivalence by construction, not by hope (see :class:`_Cache`).

**No slot is ever filled with a value the user did not send.** The skin never
calls `reply_action` itself; `ConversationSession.say` does, from the bytes of
the utterance. An unparseable reply degrades to another question (P-IH6's
wire-falsifiable negative (a)); a reply naming a different slot while one is
awaiting raises out of the engine and is served as `409 slot_conflict`,
never reinterpreted (negative (b), §10).

**The status alphabet is transported, not edited.** §5 freezes the closed set,
inconsistent casing included. The one skin-assigned status is `abstained`,
conversation profile only, for the branch that runs no turn.

**¶AMD-3 (2026-08-31) registers a third profile**, `corollary/protocol`, whose
request surface is the protocol runtime (`scripts/protocol_runtime.py`) over a
fresh session type — DESIGN-protocol-uptake §4. Three things in this file
change shape for it and nowhere else: `_fresh`/`_render` become explicit
three-way dispatches (the old else-branch handed every non-kernel model to the
slot-filling session, so an allowlist edit alone would have served the new
profile as the demo); §4.1's prefix hash gains an additive typed serialization
for admitted tool-result items; and one `function_call` output item may be
emitted on the Responses path, for an already-approved need, when the request
advertises a tool whose name AND parameters-schema digest are the pair U-P1
captured. Everything the two shipped profiles serve is byte-unchanged, which
the suite asserts rather than assumes.

Two places where this file makes a judgement the spec left to the
implementation, recorded here rather than left for a reader to discover:

* §7's `line_grammar` row for `suppose <claim>` names two routes ("evaluate or
  supposition"). The sheet keeps `route` a single real route name
  (`supposition`) and carries the fall-through in the row's `note`, because a
  route name that is not a route name would be the sheet rotting in its first
  field.
* The demo-name lint (P-IH3, §3/§7) is enforced where the spec scopes it — the
  model list, the capability sheet, and every served *description* — and it is
  enforced **at build time**, in :func:`assert_no_demo_name`, not only in the
  suite: a name reaching either endpoint fails the server at start-up rather
  than shipping until a test notices. It is deliberately NOT enforced over the
  conversation profile's `content`: the verifier mints its clarification
  prompt from the slot's own unresolved literal (`retrieval.py:2592`), which
  quotes the demo name, and §6 makes `content` a verbatim pass-through of that
  minted prompt. Scrubbing it would be the renderer rewriting the record,
  which A-IH6 forbids. Raised at implementation review and settled in §3 of
  the spec (2026-08-22): the minted prompt is the engine's record crossing the
  wire, not a listing or a description, so P-IH3 is not breached; a
  demo-neutral literal would be an engine change, out of this cycle's scope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import queue
import sys
import threading
import time
import uuid
from collections import OrderedDict
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

# The server IS the engine's renderer, so it imports engine modules freely.
# (The anti-import rules elsewhere in this repository bind the task-book
# builder and the stopwatch — the two programs that must not be able to see
# the answers — not this one.)
import request_grammar  # noqa: E402
import story as story_module  # noqa: E402
from conversation import golden_chicken_revision_session  # noqa: E402
from harness import (  # noqa: E402
    CLOSURE_OUTCOME_STATUS,
    CoreSession,
    OWNS_COMMAND,
    SUPPOSE_COMMAND,
    pending_need,
    route_line,
)
from protocol_runtime import (  # noqa: E402
    ASK as PROTOCOL_ASK,
    NEED_SLOT as PROTOCOL_NEED_SLOT,
    ProtocolSession,
    load_corpus as read_protocol_corpus,
)
from session_keys import SessionKeyRing  # noqa: E402

# --------------------------------------------------------------------------
# Constants the spec freezes
# --------------------------------------------------------------------------

#: §2. Loopback only. Not a flag: a multi-tenant bind would be a scope this
#: cycle has not paid for.
HOST = "127.0.0.1"
DEFAULT_PORT = 8377

CHAT_SCHEMA = "corollary.chat/1"

#: Bumped to /2 on 2026-08-26, when `conditional` entered the frozen status
#: alphabet (DESIGN-plain-input §3b, slice 2). The SHEET is what publishes
#: the alphabet, so widening the alphabet is a change to the sheet's
#: contract and a client that enumerated it needs to know.
#:
#: `CHAT_SCHEMA` deliberately stays at /1, and the reason is not thrift.
#: No status REACHABLE ON THAT WIRE changed: the proposer is attached to a
#: CoreSession the way slice 1 attached `assumptions` — opt-in, `None` by
#: default, set only by a recorder or a replayer — and ¶DEV-1 replays every
#: HTTP request into a fresh session that has neither. So this skin cannot
#: emit `conditional` today, and bumping the wire schema would rewrite 732
#: references including slice 1's CLOSED corpus seal and all 119 task
#: records in `experiments/throughput_tasks.json` — moving a sealed
#: denominator for a status that cannot appear in it.
#:
#: The trigger is recorded so the debt cannot be forgotten: **the day the
#: proposer is attached to a session this skin serves, `corollary.chat/2`
#: is owed**, and the spec's §5 amendment says so too.
#:
#: **¶AMD-3 read this trigger and did NOT bump it (2026-08-31), in writing.**
#: The recorded trigger above is *widening the published status alphabet*:
#: the sheet is what publishes the alphabet, so a new status changes the
#: sheet's contract. AMD-3 registers a third profile and publishes no new
#: status — `corollary/protocol` transports `found`, `waiting` and `refused`,
#: all already in §5's frozen closed set (see
#: :data:`PROTOCOL_DISPOSITION_STATUS`). Its additions to the sheet are new
#: keys (`profiles["corollary/protocol"]`, `protocol_grammar`,
#: `prompt_tool_adapters`), which is the additive shape the /2 contract has
#: already carried three times without a bump — `realization`, `conformance`
#: and `foreign_voice` all entered that way — and no byte of the kernel's
#: `line_grammar`, the conversation's `request_grammar`, or the `honesty`
#: line moves. A client that enumerated the alphabet learns nothing new; a
#: client that enumerates `profiles` reads one more key. Bumping on an
#: additive key would spend the version number on the case the trigger was
#: written to exclude, and would leave nothing to say the day the alphabet
#: really does widen.
CAPABILITIES_SCHEMA = "corollary.capabilities/2"

KERNEL_MODEL = "corollary/kernel"
CONVERSATION_MODEL = "corollary/conversation"

#: SPEC ¶AMD-3 (2026-08-31), DESIGN-protocol-uptake §4. The third profile: the
#: protocol runtime over a **fresh session type**. Neither shipped profile can
#: host it honestly — the kernel's registered line grammar and the
#: conversation's two-slot request grammar are both sheet-published claims —
#: so the uptake path gets its own model name rather than widening either.
PROTOCOL_MODEL = "corollary/protocol"

#: The three profiles, in listing order. `/v1/models`, the sheet, the
#: unknown-model 404 and `ChatEngine._fresh`'s dispatch all read THIS tuple, so
#: a fourth profile cannot be half-registered: an entry here with no `_fresh`
#: branch raises rather than falling through to a demo session, which is
#: exactly the bug ¶AMD-3 repairs (every non-kernel model used to construct the
#: two-slot session).
PROFILES = (KERNEL_MODEL, CONVERSATION_MODEL, PROTOCOL_MODEL)

#: §6, the single skin-authored string in the serving path. A ``Turn`` with
#: ``abstained=True`` carries no text at all (``conversation.py:278-281``), so
#: there is nothing to pass through; this is named as the one exception to
#: §10's no-skin-authored-tokens rule, and the stopwatch scores the turn as
#: zero useful tokens through ``status == "abstained"``.
ABSTENTION_ACKNOWLEDGEMENT = "noted; {slot} stays unknown"

#: §5's frozen closed alphabet, inconsistencies included. The skin transports
#: this vocabulary; normalizing it would be the renderer rewriting the record.
ENGINE_STATUSES = (
    "waiting",
    "solved",
    "refused",
    "exhausted",
    "found",
    "held",
    "canceled",
    "cycle",
    "hop_ceiling",
    # Added 2026-08-26 by DESIGN-plain-input §3b (slice 2). An answer served
    # under a stated supposition is a DIFFERENT SPEECH ACT from an answer,
    # and the design's whole honesty argument rests on it having its own
    # status rather than borrowing one. `held` was the tempting reuse and is
    # refused for a measured reason: `held` is already in
    # ANSWERING_STATUSES below, so reusing it would make every conditional
    # answer score as an answer in the throughput metric — "precisely the
    # accounting this design must not have".
    "conditional",
)
WRITE_GATE_STATUSES = ("PROVEN", "VERIFIED", "REFUSED")
SKIN_ASSIGNED_STATUSES = ("abstained",)

#: §6.1's answered? axis. Every other status in the frozen alphabet is
#: non-answering and carries no grounding claim — with the two named `closure`
#: exceptions, which :func:`_receipt` handles before this set is consulted.
#: `conditional` is deliberately ABSENT, and that absence is the whole
#: mechanism DESIGN-plain-input §3b's honesty argument rests on: with it
#: non-answering, this design "cannot inflate K by converting exhaustions
#: into conditionals" — the incentive that would corrupt it is removed by
#: the metric that already exists rather than by anyone's intent.
#: `measure_throughput` carries the other half, and G7b tests it from the
#: scoring path rather than from this comment.
ANSWERING_STATUSES = frozenset({"solved", "found", "held", "PROVEN", "VERIFIED"})

#: The pinned-baseline manifest the tokenizer digest is READ from (never
#: hardcoded here: a second copy of a digest is a second thing to rot).
BASELINE_MANIFEST = "experiments/throughput_baseline.json"

#: The ONE registered realization run (DESIGN-sans-template-rendering §10).
#: The capability sheet quotes R1 from THIS file rather than from a number
#: pasted into this module: a rate that can go stale in a docstring is a rate
#: that will, and the sheet is generated from live artifacts by §7's rule.
REALIZATION_RUN = "experiments/realization_rate.json"

#: The ONE registered conformance run (DESIGN-statements-that-run §10). The
#: sheet reads it live rather than restating any of it here: the run's own
#: overall verdict is VOID and its controls are published beside it, and a
#: verdict restated in a docstring is a verdict that goes stale — which is
#: worse for a miss than for a rate.
CONFORMANCE_RUN = "experiments/conformance_run.json"

#: The ONE registered foreign-voice run, and the register frozen before it.
#: The sheet quotes BOTH: the run says why the surface is withheld, and the
#: register says what shipped instead. Read at sheet-build time for the same
#: reason `REALIZATION_RUN` is — a number restated in code is a number that
#: goes stale, and this one states a miss, which is worse to get wrong.
FOREIGN_VOICE_RUN = "experiments/foreign_voice_rate.json"
FOREIGN_VOICE_REGISTER = "data/foreign_voice/register.json"

#: A11, second half. `CoreSession.boot(offline=True)` costs ~415 ms on the
#: reference host, of which ~405 ms is `UnifiedKnowledgeStore.load` re-parsing
#: every committed `data/*/nodes.json` (the boot probes together are ~5 ms —
#: the store, not the probes, is the cost). On a single-turn task that boot is
#: most of the wall clock, so it is moved off the request path: a background
#: thread keeps this many freshly booted sessions ready. Four is a balance
#: against the measured ~27 MB a pooled session holds.
#:
#: The pool is an OPTIMIZATION ONLY. A request that finds it empty boots on
#: demand and is served identically; correctness never depends on a pool hit,
#: and `tests/test_serve_chat.py` asserts pooled and pool-disabled bodies are
#: byte-identical.
DEFAULT_POOL_SIZE = 4

#: A11. One throwaway free-text line at startup so the resolver's graph index
#: is built before the first request rather than inside it. Deliberately not a
#: line any registered route claims, and deliberately carrying no demo name.
WARMUP_LINE = "kernel skin warm start line"

#: §3/§7, P-IH3. These names stay in selftests and docs. Enforced over the
#: model list, the capability sheet, and every served description (see the
#: module docstring for the one place it provably cannot reach).
DEMO_NAMES = (
    "golden-chicken",
    "golden chicken",
    "golden_chicken",
    "sally-anne",
    "sally anne",
    "sally_anne",
)

#: The request body keys this skin actually acts on. Everything else the
#: client sends is accepted, ignored, and *listed* in ``x_corollary.ignored``
#: (§4): sampling parameters have nothing to sample here, and an ignored input
#: the response does not name is the silent failure this repository exists to
#: catch.
HANDLED_BODY_KEYS = frozenset({"model", "messages", "stream", "stream_options"})

#: Keys this skin ENFORCES rather than ignores. `n` is the whole set: §4 both
#: lists it among the ignored sampling parameters and makes `n != 1` a 400,
#: and those cannot both be true of one key. The 400 wins — a request this
#: server rejects was not ignored — so `n` never appears in
#: ``x_corollary.ignored``, and calling it ignored while refusing it would be
#: the response describing itself wrongly.
ENFORCED_BODY_KEYS = frozenset({"n"})

#: A loopback server with one owner still refuses to buffer an arbitrary body:
#: a 10 MB message array is not a conversation, and reading it before saying
#: so would be the refusal arriving after the cost.
MAX_BODY_BYTES = 10 * 1024 * 1024

#: §7's line-grammar rows, mirroring `harness.route_line`'s chain in order
#: (`harness.py:2485-2550`; this comment read `:1393-1437` until 2026-09-01,
#: stale since v0.21 under DESIGN-plain-input §2.2's standing instruction to
#: correct it whenever a design next touches this file — DESIGN-house-rules'
#: `declare` row is that design). `requires` is what makes `served` a *live* flag
#: rather than a copied one: it is resolved against the booted matrix at
#: request time, which is why the gloss row publishes `served: false` under the
#: offline boot instead of disappearing.
LINE_GRAMMAR: tuple[dict, ...] = (
    {
        "form": "(empty line)",
        "route": "none",
        "example": "",
        "statuses": ["waiting"],
        "requires": (),
    },
    {
        "form": "narrow <corpus|discipline|word|id> <value> | cancel",
        "route": "resolver_context",
        "example": "narrow corpus logic",
        "statuses": ["found", "waiting", "canceled", "cycle", "hop_ceiling"],
        "requires": ("corpus.nodes",),
        "note": "reachable only while a resolver candidate set is pending",
    },
    {
        "form": "owns <template-expr>",
        "route": "ownership",
        "example": "owns x ^ 2",
        "statuses": ["solved", "exhausted", "refused"],
        "requires": ("corpus.nodes",),
    },
    {
        "form": "suppose <claim>",
        "route": "supposition",
        "example": "suppose the corpus is complete",
        "statuses": ["solved", "held", "waiting", "refused"],
        "requires": (),
        "note": (
            "a suppose line that binds and computes is routed to evaluate "
            "first (harness.route_line), which is where its solved status "
            "comes from"
        ),
    },
    {
        "form": "retract <assumption-id>",
        "route": "retraction",
        "example": "retract a001",
        "statuses": ["canceled", "refused"],
        "requires": (),
        "note": (
            "DESIGN-session-ledger §3's lifecycle surface: the Assumption "
            "record's status alphabet registers `retracted`, and supersession "
            "happens on its own when a person re-supposes the same subject, "
            "so withdrawal is the one transition that needed a word. Refuses "
            "with `unknown_assumption` in a session that keeps no ledger, "
            "which is every session this skin serves — ¶DEV-1 replays "
            "requests into fresh sessions and attaches no assumption set"
        ),
    },
    {
        "form": "declare <name>/<arity> (<category>, ...)",
        "route": "declaration",
        "example": "declare parent_of/2 (variable, variable)",
        "statuses": ["held", "refused"],
        "requires": (),
        "note": (
            "DESIGN-house-rules §6.2's row: the person names a fresh relation "
            "symbol and the system admits it into a session-scoped symbol "
            "ledger or refuses with exactly one deciding clause, totally and "
            "by default toward refusal. Disclosed against prior art rather "
            "than presented as new ground: the `what is X | define X` row "
            "below is a WordNet gloss lookup — the WORD, not the act — and "
            "`suppose` above is the discipline precedent (the cap, the "
            "supersession, the refusal names), not the object. Categories are "
            "the committed schema's nine symbolToken slot roles, so the check "
            "they buy is exact role agreement between declaration and use and "
            "nothing more. An admitted declaration is well-formed and fresh; "
            "it is never true or useful, and nothing declared reaches a "
            "generated library file. Refuses `no_symbol_ledger` in a session "
            "that keeps no symbol ledger, which is every session this skin "
            "serves — ¶DEV-1 replays requests into fresh sessions and "
            "attaches none, so declared vocabulary cannot cross an HTTP turn "
            "here, exactly as the `retract` row above publishes its own "
            "¶DEV-1 limitation"
        ),
    },
    {
        "form": "twin <statement-id>",
        "route": "twin",
        "example": "twin programming.dfactorial.recursive",
        "statuses": ["found", "exhausted", "refused"],
        "requires": ("corpus.nodes",),
        "note": "wiring step W1",
    },
    {
        "form": "reachable <world-id> <target-path>",
        "route": "closure",
        "example": (
            "reachable visual.rt0000 "
            "data/closure_targets/visual.rt0000.reachable.0.state.json"
        ),
        "statuses": ["found", "exhausted", "refused"],
        "requires": ("closure.worlds",),
        "note": "wiring step W2; targets must be listed in the committed manifest",
    },
    {
        "form": "conform <statement-id> <bindings>",
        "route": "conform",
        "example": "conform algebra.polynomial_equations.quadratic_formula a=1 b=-3 c=2",
        "statuses": ["found", "refused"],
        "requires": ("tool.conform",),
        "note": (
            "DESIGN-statements-that-run §5's route, live since the registered "
            "run. `found` carries a conformance record whose `certifies` "
            "sentence says exactly what the verdict is worth; `refused` names "
            "the register construct that blocked it. Never `solved` — a "
            "conformance verdict is not an exact lookup"
        ),
    },
    {
        "form": "<story request>",
        "route": "story",
        "example": "tell me a story",
        "statuses": ["found", "waiting", "exhausted"],
        "requires": ("narrative.story",),
    },
    {
        "form": "<belief narration> / where does A think B is",
        "route": "belief",
        "example": "where does the observer think the marble is",
        "statuses": ["found", "waiting", "exhausted"],
        "requires": ("belief.ownership",),
    },
    {
        "form": "<computable relation or expression>",
        "route": "evaluate",
        "example": "x = 5, x ^ 2",
        "statuses": ["solved", "refused"],
        "requires": (),
        "note": (
            "refused only by a registered resource bound (E0e): a power wider "
            "than evaluate.MAX_RESULT_DIGITS is declined by name rather than "
            "computed into something that cannot be rendered"
        ),
    },
    {
        "form": "<repo-relative path>",
        "route": "write_gate",
        "example": "staging/proposal.json",
        "statuses": list(WRITE_GATE_STATUSES),
        "requires": (),
        "note": "uppercase Verdict pass-through",
    },
    {
        "form": "<free text the graph claims>",
        "route": "resolver",
        "example": "de morgan laws",
        "statuses": ["found", "waiting"],
        "requires": ("corpus.nodes",),
    },
    {
        "form": "what is X | define X",
        "route": "gloss",
        "example": "what is a lemma",
        "statuses": ["found"],
        "requires": ("retrieve.wordnet",),
        "note": (
            "the offline boot forces retrieve.wordnet OFF and _route_gloss "
            "then declines; the row is published off rather than hidden"
        ),
    },
    {
        "form": "<everything else>",
        "route": "dispatcher",
        "example": "tell me about tomorrow's weather",
        "statuses": ["exhausted"],
        "requires": (),
    },
)

PROFILE_DESCRIPTIONS = {
    KERNEL_MODEL: (
        "corpus answers, exact evaluation, ownership, belief, story, refusals"
    ),
    CONVERSATION_MODEL: (
        "signed slot-filling with minted clarification questions"
    ),
    PROTOCOL_MODEL: (
        "an ordinary turn taken as a registered interaction move, licensed "
        "together by declared context signals and sealed corpus witnesses; "
        "materially different transitions pause instead of guessing"
    ),
}

# --------------------------------------------------------------------------
# ¶AMD-3: the protocol profile's constants
# --------------------------------------------------------------------------

#: The generated protocol corpus, deliberately outside `data/` (DESIGN §3) so
#: it joins no boot corpus count and no merged resolver graph.
PROTOCOL_CORPUS = "protocol/protocols.json"

#: U-P1's committed host capture. The prompt adapter is registered from THIS
#: file and from nowhere else: the design forbids a guessed adapter, and a
#: digest pasted into this module would be a second copy of a number that can
#: rot away from the capture it claims to quote.
HOST_CAPTURE = "experiments/protocol_uptake_host_capture.json"

#: §6's `route` for this profile. One route, because the profile has one
#: request surface: the protocol runtime.
PROTOCOL_ROUTE = "protocol"

#: Dispositions to §5's frozen status alphabet. ¶AMD-3 widens NOTHING here:
#: every value on the right is already in the closed set, which is why the
#: capability schema does not bump (see :data:`CAPABILITIES_SCHEMA`).
#: An admitted transition is `found` rather than `solved` because what
#: licensed it is a corpus witness plus a position, the same shape as the
#: resolver route's `found`, not a computation.
PROTOCOL_DISPOSITION_STATUS = {
    "ENTER": "found",
    "SUSPEND": "found",
    "CONTINUE": "found",
    "RESUME": "found",
    "EXIT": "found",
    "ASK": "waiting",
    "REFUSED": "refused",
}

#: DESIGN §3's absence sentinel. Absence is a VALUE, not a missing key.
PROTOCOL_ABSENT = "ABSENT"

#: Where each served context signal comes from on this profile. Two are
#: derived from real session state; three have **no HTTP source event in this
#: slice** and are honestly `ABSENT` rather than quietly invented. The receipt
#: carries the source-event id, so a reader can see which is which without
#: consulting this table.
PROTOCOL_SIGNAL_SOURCES = {
    "pending_need": "evt-http-session-root",
    "quote_boundary": "evt-http-no-source",
    "expected_output_slot": "evt-http-no-source",
    "active_task": "evt-http-no-source",
}
PROTOCOL_PENDING_NEED_EVENT = "evt-http-pending-need"
PROTOCOL_STACK_EVENT = "evt-http-protocol-stack"
PROTOCOL_SIGNALS_WITHOUT_AN_HTTP_SOURCE = (
    "quote_boundary",
    "expected_output_slot",
    "active_task",
)

#: Responses body keys this profile ACTS on, so §4's ignored list must not
#: name them (¶AMD-3). `tools` decides whether the registered prompt adapter
#: fires; `tool_choice: "none"` suppresses the call. `parallel_tool_calls` is
#: deliberately NOT here: the client's value changes nothing, because this
#: profile emits at most one call whatever it says — and the body publishes
#: `false`, which is what the catalog publishes too.
PROTOCOL_HANDLED_RESPONSES_KEYS = frozenset({"tools", "tool_choice"})

#: The one name §8 permits in an output item on this profile, filled from the
#: capture at boot. `{}` means no adapter is registered and every ASK takes
#: the text WAITING fallback.
PROMPT_TOOL_ADAPTERS: dict[str, dict] = {}

CODEX_REASONING_LEVELS = [
    {
        "effort": "medium",
        "description": "The deterministic harness ignores reasoning effort",
    }
]

HONESTY_LINE = (
    "offline boot; unregistered paths abstain (P-IH4); no generative path"
)


def _read_json(path: Path):
    """One committed artifact, or (None, reason). Never raises at a caller."""

    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), None
    except (OSError, ValueError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def assert_no_demo_name(payload: dict, where: str) -> str:
    """P-IH3, enforced where the bytes are built rather than only in a test.

    A lint that lives only in the suite is a lint a green run can lose: this
    raises at build time, so a demo name reaching `/v1/models` or the sheet
    stops the server instead of shipping. It reads the *serialized* payload
    because a name that only appears after serialization is still a name the
    client reads. Returns the serialized text so the caller does not pay for
    a second `json.dumps`.
    """

    text = json.dumps(payload, ensure_ascii=False)
    lowered = text.lower()
    for name in DEMO_NAMES:
        if name in lowered:
            raise RuntimeError(
                f"P-IH3 violation: {where} would serve the demo name "
                f"{name!r}; those names stay in selftests and docs"
            )
    return text


@lru_cache(maxsize=8)
def realization_row(repo_root_str: str) -> dict:
    """The sheet's `realization` row, read from the registered run (§5).

    `served: true` describes the *surface*, not any particular term: the
    `in words` line exists and reaches both skins. Which terms get one is
    what `rate` and `denominator` say, and they are quoted from the run
    rather than restated here — R1's own sentence insists the parseable
    denominator travel with the rate, so the row carries both and the
    corpus total beside them.

    A missing or unreadable run file publishes `served: false` with the
    reason. That is the honest row for a checkout without the artifact, and
    it is not a refusal to serve: `answer.render` gates itself on its own
    round trip and needs nothing from this file.
    """

    path = Path(repo_root_str) / REALIZATION_RUN
    row = {
        "surface": "in words",
        "rendered_in": "answer lines, under `formally`",
        "description": (
            "canonical terms realized as English sentences, emitted only "
            "when the sentence re-parses to the source skeleton"
        ),
        "refusal": (
            "a term that does not parse, an uncovered operator head, or a "
            "failed re-parse emits no line at all (R3)"
        ),
        "run": REALIZATION_RUN,
    }
    try:
        run = json.loads(path.read_text(encoding="utf-8"))
        r0, r1 = run["r0"], run["r1"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        row["served"] = False
        row["detail"] = f"no readable registered run at {REALIZATION_RUN}: {exc}"
        return row
    row["served"] = True
    row["realizer_id"] = run.get("run_id")
    row["round_trip_rate"] = r1["rate"]
    row["round_trip_floor"] = r1["floor"]
    row["parseable_denominator"] = r1["denominator"]
    row["corpus_nodes"] = r0["nodes_total"]
    row["sentence"] = r1["sentence"]
    return row


@lru_cache(maxsize=8)
def foreign_voice_row(repo_root_str: str) -> dict:
    """The sheet's `foreign_voice` row — armed or dark, and never a lie.

    §7's rule: "Rows the profile cannot serve (gloss under offline boot)
    appear with `served: false` rather than disappearing." A withheld surface
    absent from the sheet is indistinguishable, to a client, from one this
    repository never attempted, and that difference is what this cycle's
    artifacts exist to record.

    **Rewritten by ROADMAP-v0.20 §4d, which inherited three defects from the
    v0.19 version of this function** (DESIGN-voice-completion Correction 7,
    all three confirmed in the tree before rewriting):

    (a) *There was no code path that set `served: true` at all.* `served` was
    assigned once, to `False`. Flipping the row was never a matter of
    removing a guard — the true branch did not exist, and 4d writes it.

    (b) *The empty-list read was caught, so the failure was a plausible lie.*
    It indexed `c_v4["voided_classes"][0]` on a list that is EMPTY when
    nothing voided, and the `except` tuple named `IndexError` — so an
    all-clear run returned early with `served: false` and the words "its
    record could not be read", on exactly the branch the voice design exists
    to produce. A clean run would have been published as a corrupt file.

    (c) *The guard keyed off the wrong field.* `c_v4["voided_classes"]` is
    one control's internal detail; the run's own verdict is
    `verdicts["voided"]`. They agree in the shipped artifact and would both
    be empty on an all-clear run — but only the wrong one was consulted, so
    the row's behaviour was decided by a field that is not the verdict.

    All three are gone: the arming decision now comes from
    `foreign_voice_arming.arming_state`, the SAME read `answer.render` uses,
    so the row and the line cannot disagree about whether a surface exists.
    The C-V4 detail is still quoted when a run carries it, but as
    description rather than as the gate.

    Two things the row still refuses to say, unchanged from v0.19 and
    restated because they are easy to lose in a rewrite: it does not quote
    B1's identity rate (a VOID control outranks a cleared floor, and printing
    1.0 beside VOID would re-publish a withdrawn reading), and it does not
    present one summed blocked figure without its split (the run says those
    buckets are reported separately; the total is the register's own field,
    read rather than computed).
    """

    from foreign_voice_arming import arming_state  # noqa: PLC0415

    root = Path(repo_root_str)
    state = arming_state(root)
    row = {
        "surface": "foreign voice",
        "served": bool(state["armed"]),
        "description": (
            "statements rendered as invertible English sentences in a "
            "non-notational register"
        ),
        "run": state["run"],
        "register": FOREIGN_VOICE_REGISTER,
        "arming_rule": state["arming_rule"],
        "reason": state["reason"],
    }
    for field in (
        "verdict", "voided", "summary", "prior_run",
        "blocking_checks", "non_blocking_voids",
    ):
        if field in state:
            row[field] = state[field]

    # C-V3' is published as a VOID and never as a number. The design spends
    # §8 refusing the claim that control would license — that a reader can
    # recover the mathematics determinately from the English — so a row that
    # showed a rate beside it would make exactly the claim the void withdrew.
    # The absent C-V3 stays absent for the same reason: an un-run control is
    # not a passed one.
    run, _run_error = _read_json(root / state["run"])
    if isinstance(run, dict):
        for key, label in (("c_v3", "C-V3"), ("c_v3_prime", "C-V3'")):
            block = run.get(key)
            if not isinstance(block, dict):
                continue
            row.setdefault("reader_claim", {})[label] = {
                "status": block.get("status"),
                "verdict": block.get("verdict"),
                "claims": None,
                "read_this_as": (
                    "published as a void or an absence, never as a rate. The "
                    "claim this control alone could license — that a reader "
                    "recovers the mathematics determinately from the English "
                    "— is NOT made here or anywhere this cycle."
                ),
            }

    # The register ships whether or not the voice does: it is the inventory
    # of what this cycle's graph cannot say, and it is a result either way.
    register, _error = _read_json(root / FOREIGN_VOICE_REGISTER)
    if isinstance(register, dict):
        census = register.get("b3_census") or {}
        row["register_id"] = register.get("register_id")
        row["blocked_total"] = register.get("blocked_total")
        row["blocked_split"] = {
            "registered_blocked_mathlib_head": census.get(
                "registered_blocked_mathlib_head"),
            "registered_blocked_no_row": census.get(
                "registered_blocked_no_row"),
            "reported_separately_because": (
                "the two registered_blocked_* buckets are reported "
                "separately: the first is a budget consequence the maintainer "
                "can lift and the second is a design consequence this cycle "
                "owns"
            ),
        }
    return row


@lru_cache(maxsize=8)
def conformance_row(repo_root_str: str) -> dict:
    """The sheet's `conformance` row — the vocabulary and the sentence, NEVER a rate.

    DESIGN-statements-that-run §5 is unusually explicit about this, and the
    reason is worth keeping in front of the code: *"A sheet row reading
    `conformance: 0.98` would be the single most misleading object this
    design could ship, because the number it invites a reader to form is the
    universal claim §3.4 spends its whole length refusing."*

    So the row carries the verdict VOCABULARY, the denominators, and the
    `certifies` sentences — and no rate, no percentage, no ratio. The habit
    the `realization` row set (quote the registered run's headline number) is
    deliberately suspended here, and §8.1 records that suspension.

    A missing artifact publishes `served: false` with the reason, on the
    existing precedent.
    """

    run, error = _read_json(Path(repo_root_str) / CONFORMANCE_RUN)
    row = {
        "surface": "conform <statement-id> <bindings>",
        "run": CONFORMANCE_RUN,
        "description": (
            "a committed statement compiled to an exact evaluator over the "
            "asker's own numbers, answering with a conformance record"
        ),
        "no_rate_is_published_here": (
            "by design, not by omission. A conformance figure invites a "
            "universal reading that no verdict in this lane supports; the "
            "sheet quotes the certifies sentence instead."
        ),
    }
    if not isinstance(run, dict):
        row["served"] = False
        row["reason"] = f"no readable registered run at {CONFORMANCE_RUN}: {error}"
        return row

    try:
        from conform import CERTIFIES, NIHIL_CERTIFIES  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover
        row["served"] = False
        row["reason"] = f"the compiler is not importable: {exc}"
        return row

    verdicts = run.get("verdicts") or {}
    row["served"] = True
    row["verdict_vocabulary"] = {
        verdict: sentence for verdict, sentence in sorted(CERTIFIES.items())
    }
    row["nihil_vocabulary"] = {
        verdict: sentence for verdict, sentence in sorted(NIHIL_CERTIFIES.items())
    }
    row["denominators"] = {
        "ground_decided": run.get("e1", {}).get("ground_statements"),
        "samplable_and_schema_covered": run.get("e2", {}).get("denominator"),
        "M_points_per_statement": run.get("e2", {}).get("M"),
        "corpus_statements": 12777,
        "never_summed_into_one_supported_number": (
            "The refused buckets are reported separately: some are "
            "consequences a maintainer can lift by authoring schema rows and "
            "some are consequences this design owns."
        ),
    }
    row["registered_run_verdict"] = verdicts.get("overall")

    # A CONTROL AND A GATE ARE NOT THE SAME OBJECT, and this row used to
    # publish them as one (fixed 2026-08-25, after review). The old filter was
    # `gate.get("met") is False` over every row in `verdicts.gates`, which got
    # BOTH halves wrong on the live artifact: it named E1 — a MISSED GATE, a
    # finding about the corpus under the declared domain — as a voided
    # control, and it silently dropped C-E2, whose row carries the key
    # `informative` rather than `met` and so never matched. It published
    # `['E1', 'C-E1']` where the truth is two voided controls, `C-E1` and
    # `C-E2`, and one missed gate, `E1`.
    #
    # The distinction is the whole reason both are published: a voided control
    # withdraws a reading (C-E1's own sentence voids every
    # NO_COUNTEREXAMPLE_FOUND in the run), while a missed gate IS a reading —
    # E1's 25 refusals are what the floor existed to surface. Merging them
    # tells a reader that a result was retracted when it was published, and
    # that a retraction did not happen when it did.
    controls, missed_gates = [], []
    for gate in verdicts.get("gates", []):
        name = gate.get("gate")
        if not name:
            continue
        is_control = str(name).startswith("C-")
        if "informative" in gate:
            # C-E2's shape: the verdict is a sentence, not a boolean.
            voided = "VOID" in str(gate["informative"]).upper()
        elif "disagreements" in gate:
            # C-E3's shape: it voids by DISAGREEING, so an empty list is the
            # cleared reading and not a missing one.
            voided = bool(gate["disagreements"])
        else:
            voided = gate.get("met") is False
        if not voided:
            continue
        (controls if is_control else missed_gates).append(name)
    row["voided_controls"] = controls
    row["missed_gates"] = missed_gates
    row["a_missed_gate_is_not_a_voided_control"] = (
        "A voided control WITHDRAWS a reading this run would otherwise have "
        "published. A missed gate IS a reading: the floor existed to surface "
        "exactly what it surfaced. They are listed separately because a "
        "reader who sees them merged learns the wrong thing about both."
    )
    row["read_the_run_before_reading_a_verdict"] = (
        "The registered run's own overall verdict is published above. Where "
        "it reads VOID, a served NO_COUNTEREXAMPLE_FOUND carries that void "
        "in its own answer lines rather than only here."
    )
    return row


def conversation_owner(session_prefix_hash: str) -> str:
    """§4: the conversation profile's owner, derived from the prefix hash.

    Named rather than inlined because of an invariant the cache depends on:
    a cached session's owner was derived from a SHORTER prefix than the
    request being served, and unlike the kernel's `session_id` it cannot be
    realigned — the owner is baked into `state.user_frame`, into every
    binding the verifier has already signed, and into the ephemeral ring's
    scopes. Realigning it would mean re-signing another owner's bindings,
    which is the forgery the signed channel exists to prevent.

    What makes that harmless is that **the owner never reaches the wire**.
    §6 defines no field carrying it: `content` is the reply, the minted
    prompt, or the abstention line; `detail` is a rule id or a failure
    reason; the binding receipt carries slot, value and lifetime; and
    `profile_session_id` is the request's own prefix hash, recomputed per
    request and never read off the session. So a cached turn and a cold
    replay differ in a value neither can express — which is what keeps §4's
    "identical bodies modulo id and created" true rather than lucky.
    `tests/test_serve_chat.py` asserts the owner appears in no served byte.
    """

    return f"chat-{session_prefix_hash[:16]}"


# --------------------------------------------------------------------------
# §4.1 canonical-JSON/compact, and the canonical prefix hash
# --------------------------------------------------------------------------


def canonical(value) -> str:
    """§4.1's one serialization discipline, used everywhere "canonical" appears."""

    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def canonical_bytes(value) -> bytes:
    return canonical(value).encode("utf-8")


def prefix_item(role: str, content) -> list:
    """§4.1's per-item serialization — ¶AMD-3's extension, and it is ADDITIVE.

    A message item serializes to ``[role, content]``, exactly as it always
    has, so a prefix of only role/content pairs hashes to the byte it hashed
    to before this function existed and every kernel and conversation replay
    test stays green.

    An admitted tool-result item serializes to its **type token and its typed
    payload** — ``["function_call_output", {"call_id": …, "output": …}]`` —
    rather than to some flattened string. Two transcripts differing only in a
    tool result's payload therefore hash differently, which is what makes the
    divergence check of §4 able to see a tampered tool result at all. That
    property is tested, not assumed.
    """

    if role == "tool":
        return [
            "function_call_output",
            {"call_id": content["call_id"], "output": content["output"]},
        ]
    return [role, content]


def prefix_hash(prefix) -> str:
    """§4.1. sha256 over canonical-JSON/compact of the serialized prefix."""

    return hashlib.sha256(
        canonical_bytes([prefix_item(role, content) for role, content in prefix])
    ).hexdigest()


# --------------------------------------------------------------------------
# ¶AMD-3: the registered prompt adapter (DESIGN §4, U-P1)
# --------------------------------------------------------------------------


def tool_schema_digest(parameters) -> str:
    """The capture's own `digest_rule`, implemented verbatim.

    ``sha256`` of ``json.dumps(obj, sort_keys=True, separators=(',',':'))``
    encoded UTF-8. Deliberately NOT :func:`canonical`, which passes
    ``ensure_ascii=False``: the two agree on every ASCII schema, and the
    registration rule is the capture's, not this module's.
    """

    return hashlib.sha256(
        json.dumps(parameters, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def register_prompt_tool(name: str, parameters_sha256: str, provenance: str) -> None:
    """Register one prompt adapter for exactly one (name, schema digest) pair.

    ``provenance`` is required and is **published in the capability sheet**.
    The capture's registration rule allows no guessed adapter, so a reader has
    to be able to see where each registered digest came from — and a
    stand-in registered by an instrument (`scripts/run_b7_roundtrip.py`'s
    self-check arm) has to be distinguishable, on the wire, from the digest
    U-P1 actually captured from the installed host.
    """

    if not name or not parameters_sha256 or not provenance:
        raise ValueError("a prompt adapter needs a name, a digest and a provenance")
    PROMPT_TOOL_ADAPTERS[name] = {
        "name": name,
        "parameters_sha256": parameters_sha256,
        "provenance": provenance,
    }


def load_captured_prompt_tools(repo_root: Path) -> None:
    """Register the adapter U-P1 captured, if the capture names one.

    No capture, an unreadable one, or `host_prompt_status` other than
    `captured` registers nothing at all: the design's rule is that no suitable
    tool means the Codex-prompt result is UNTESTED, never a guessed adapter.
    """

    capture, _error = _read_json(Path(repo_root) / HOST_CAPTURE)
    if not isinstance(capture, dict):
        return
    tool = capture.get("prompt_tool")
    if not isinstance(tool, dict):
        return
    if tool.get("host_prompt_status") != "captured":
        return
    name, digest = tool.get("name"), tool.get("parameters_sha256")
    if not isinstance(name, str) or not isinstance(digest, str):
        return
    register_prompt_tool(
        name,
        digest,
        f"{HOST_CAPTURE} (U-P1, {capture.get('captured_date')})",
    )


def match_prompt_tool(tools) -> dict | None:
    """The advertised declaration this server is registered to answer, or None.

    Exactly the capture's `adapter_registration_rule`: the pair
    ``(name, parameters_sha256)``. A request advertising `request_user_input`
    with any other parameters digest matches nothing and takes the text
    WAITING fallback — it does not get a guessed adapter.
    """

    if not isinstance(tools, list):
        return None
    for declaration in tools:
        if not isinstance(declaration, dict):
            continue
        registered = PROMPT_TOOL_ADAPTERS.get(declaration.get("name"))
        if registered is None:
            continue
        if "parameters" not in declaration:
            continue
        if tool_schema_digest(declaration["parameters"]) != registered[
            "parameters_sha256"
        ]:
            continue
        return {**registered, "declaration": declaration}
    return None


# --------------------------------------------------------------------------
# ¶AMD-3: the protocol profile's session type
# --------------------------------------------------------------------------


@lru_cache(maxsize=4)
def protocol_corpus(corpus_path_str: str) -> dict:
    """The sealed corpus, read once. Never mutated by the serving path."""

    return read_protocol_corpus(corpus_path_str)


class ProtocolProfileSession:
    """A fresh :class:`protocol_runtime.ProtocolSession`, plus its HTTP context.

    This is the **fresh session type** ¶AMD-3 registers. It is not
    `golden_chicken_revision_session` and it is not kernel line routing: the
    two shipped profiles' request surfaces are untouched by this file's
    changes, and this class is the whole of the third one.

    The context signals it supplies are derived from real session state or
    are honestly absent, and nothing in between:

    * ``pending_need`` — the session's own pending need: its slot while one is
      open, the absence sentinel when none is. **A reply reports the need it
      binds as no longer outstanding**, which is not a special case bolted on
      but the signal's own meaning — the need this result answers is not a
      need outstanding *for* this result — and it is what the sealed
      reply-turn fixtures record too;
    * ``protocol_stack`` — the session's own stack, through the runtime's top
      summary (the runtime refuses a supplied summary contradicting its own
      derivation, so this can only ever agree);
    * ``quote_boundary``, ``expected_output_slot``, ``active_task`` — **no
      HTTP source event exists for these in this slice**, so they carry the
      absence sentinel under the `evt-http-no-source` event id. Inventing a
      quote boundary from, say, a quoted-looking user line would be the
      lexical trigger this whole design abolishes.

    A rendered phrase never enters the admission predicate: the only things
    this class hands the runtime are the user's surface bytes (which reach the
    corpus through the exact-lookup channel and nowhere else), the tool
    result's `call_id`/`output`, and the signal rows above.
    """

    __slots__ = ("session",)

    def __init__(self, repo_root: Path, session_id: str) -> None:
        self.session = ProtocolSession(
            session_id, protocol_corpus(str(Path(repo_root) / PROTOCOL_CORPUS))
        )

    def context_rows(self, binding: str | None = None) -> list[dict]:
        pending = self.session.pending
        if pending is not None and binding is not None and pending["request_id"] == binding:
            pending = None
        rows = [
            {
                "signal_id": signal_id,
                "value": PROTOCOL_ABSENT,
                "source_event_id": source,
            }
            for signal_id, source in PROTOCOL_SIGNAL_SOURCES.items()
        ]
        if pending is not None:
            rows[0] = {
                "signal_id": "pending_need",
                # The pending need's identity: the slot the verifier minted
                # it for. It is deliberately NOT the fixtures' `probe` value —
                # this profile opens no probe, and borrowing that value would
                # make a clarification look like one.
                "value": PROTOCOL_NEED_SLOT,
                "source_event_id": PROTOCOL_PENDING_NEED_EVENT,
            }
        rows.append(
            {
                "signal_id": "protocol_stack",
                "value": self.session.top_summary(),
                "source_event_id": PROTOCOL_STACK_EVENT,
            }
        )
        return rows

    def submit(self, line: str, source: str) -> dict:
        return self.session.submit_utterance(
            line, self.context_rows(), source=source
        )

    def resume(self, call_id: str, output: str, source: str) -> dict:
        return self.session.submit_reply(
            call_id,
            protocol_tool_answer(output, self.session.pending),
            self.context_rows(binding=call_id),
            source=source,
        )


def protocol_tool_answer(output: str, pending: dict | None) -> dict:
    """Map a host's `function_call_output` payload onto the need's answer schema.

    The wording of what a host sends back is outside the scored claim; what is
    inside it is that **nothing is invented**. This function only ever returns
    a `{protocol_id, move_id}` pair drawn from the *pending* candidate set, or
    an empty dict — and an empty dict is refused by the runtime as
    `UNBOUND_ANSWER` with the session still WAITING. A cancelled prompt, an
    empty string, a free-form "Other", and a move name that was never a
    candidate all land there together, which is the correct place for them:
    no value is invented for a slot the person did not fill.
    """

    if pending is None:
        return {}
    token = output.strip() if isinstance(output, str) else ""
    named_protocol: str | None = None
    if token.startswith("{") or token.startswith("["):
        try:
            parsed = json.loads(token)
        except ValueError:
            parsed = None
        if isinstance(parsed, dict):
            answers = parsed.get("answers")
            if isinstance(answers, list) and answers and isinstance(answers[0], dict):
                parsed = answers[0]
            if isinstance(parsed.get("protocol_id"), str):
                named_protocol = parsed["protocol_id"]
            for key in ("move_id", "value", "answer", "label", "text", "option"):
                candidate = parsed.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    token = candidate.strip()
                    break
            else:
                token = ""
    if "/" in token:
        head, _, tail = token.partition("/")
        named_protocol, token = head.strip(), tail.strip()
    for candidate in pending["candidates"]:
        if candidate["move_id"] != token:
            continue
        if named_protocol is not None and candidate["protocol_id"] != named_protocol:
            continue
        return dict(candidate)
    return {}


# --------------------------------------------------------------------------
# ¶AMD-3: rendering one protocol turn
# --------------------------------------------------------------------------


def protocol_selection(receipt: dict) -> tuple[str, str, str] | None:
    """``(protocol_id, move_id, family)`` of the selected move, or None.

    Read off the receipt's own `candidates[]` and `protocol_witnesses[]`
    rather than parsed out of `verifier_evidence` prose: a renderer that
    scraped an evidence string would break the moment the runtime reworded
    one, and the record already carries the facts.
    """

    move_id = receipt["selected_move_id"]
    if move_id is None:
        return None
    protocol_ids = sorted(
        candidate["protocol_id"]
        for candidate in receipt["candidates"]
        if candidate["move_id"] == move_id
    )
    if not protocol_ids:
        return None
    protocol_id = protocol_ids[0]
    family = next(
        (
            witness["relation"]
            for witness in receipt["protocol_witnesses"]
            if witness["protocol_node_id"] == protocol_id
        ),
        "",
    )
    return protocol_id, move_id, family


def protocol_content(receipt: dict) -> str:
    """§6 for this profile: the minted question, or a mechanical receipt summary.

    An ASK renders the verifier's own minted prompt, exactly as the
    conversation profile does — a WAITING turn is a complete assistant turn
    that asks a question.

    Every other disposition renders four (or two) label-aligned fields read
    straight out of the uptake receipt. This is an **inspectable rendering,
    not conversational prose**: there is no sentence bank, no template store,
    and no phrase whose wording could carry information the record does not.
    And the direction matters — a rendered phrase never travels back into the
    admission predicate. The engine's replay reads user turns and admitted
    tool results; the assistant text it produced is compared for divergence
    and is never an input to a transition.
    """

    if receipt["disposition"] == PROTOCOL_ASK:
        return receipt["need"]["prompt"]
    lines = [f"disposition: {receipt['disposition']}"]
    selection = protocol_selection(receipt)
    if selection is None:
        lines.append(f"verdict    : {receipt['verifier_verdict']}")
        return "\n".join(lines)
    protocol_id, move_id, family = selection
    lines.append(f"family     : {family}")
    lines.append(f"protocol   : {protocol_id}")
    lines.append(f"move       : {move_id}")
    return "\n".join(lines)


def protocol_receipt(receipt: dict) -> dict:
    """§6.1's `protocol` row, keyed on (route, answered?) like every other.

    An answering turn cites the committed corpus and the witnesses the
    selected move rested on, so a client can recheck the claim against
    `protocol/protocols.json`. A non-answering turn — `waiting` or `refused` —
    claims no grounding and carries `{}`, exactly as §6.1 requires. The uptake
    record itself is NOT this receipt: it rides in `x_corollary.uptake` on
    every turn including those two, because DESIGN §3's `authority_delta` must
    be a present, plaintext, empty field on the ASK and REFUSED paths.
    """

    if PROTOCOL_DISPOSITION_STATUS[receipt["disposition"]] not in ANSWERING_STATUSES:
        return {}
    return {
        "uptake_id": receipt["uptake_id"],
        "corpus_path": PROTOCOL_CORPUS,
        "protocol_witnesses": [
            witness["protocol_node_id"] for witness in receipt["protocol_witnesses"]
        ],
        "grounding": "protocol-corpus",
    }


def render_protocol_turn(
    profile_session: ProtocolProfileSession,
    role: str,
    content,
    *,
    source: str,
    with_receipt: bool = True,
) -> Rendered:
    """One protocol-profile input item, admitted and rendered (¶AMD-3)."""

    if role == "tool":
        receipt = profile_session.resume(
            content["call_id"], content["output"], source
        )
    else:
        receipt = profile_session.submit(content, source)

    extension = {
        "schema": CHAT_SCHEMA,
        "profile": PROTOCOL_MODEL,
        "route": PROTOCOL_ROUTE,
        "status": PROTOCOL_DISPOSITION_STATUS[receipt["disposition"]],
        # Engine vocabulary, verbatim: the verifier names WHICH rule admitted
        # or refused, which is what makes a refusal readable at all.
        "detail": receipt["verifier_verdict"],
        "receipt": protocol_receipt(receipt) if with_receipt else {},
        # The ProtocolUptake record, verbatim (A-IH6: the skin renders the
        # engine's record, it does not rewrite it).
        "uptake": receipt,
    }
    if receipt["disposition"] == PROTOCOL_ASK:
        need = receipt["need"]
        extension["need"] = {
            "slot": need["slot"],
            "prompt": need["prompt"],
            # The two fields §6.2's conversation shape has no use for and this
            # profile cannot work without: the id a `call_id` binds to, and
            # the unresolved candidates the question is between.
            "request_id": need["request_id"],
            "options": list(receipt["unresolved_move_ids"]),
        }
    return Rendered(protocol_content(receipt), extension)


# --------------------------------------------------------------------------
# §6: usage, informational only, never approximated
# --------------------------------------------------------------------------


class TokenCounter:
    """The pinned baseline tokenizer, or nothing at all.

    The digest is read from the committed baseline manifest rather than
    written here twice; a mismatch or a missing file means *no usage block*,
    following the manifest's own cannot-verify-never-skip policy rather than
    inventing an approximate count that a reader would mistake for the pinned
    one.
    """

    def __init__(self, repo_root: Path) -> None:
        self._tokenizer = None
        self.reason = "not attempted"
        self._load(repo_root)

    @property
    def available(self) -> bool:
        return self._tokenizer is not None

    def _load(self, repo_root: Path) -> None:
        manifest_path = repo_root / BASELINE_MANIFEST
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            pin = manifest["tokenizer"]
            relative, expected = pin["file"], pin["sha256"]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            self.reason = f"no readable tokenizer pin in {BASELINE_MANIFEST}: {exc}"
            return
        path = repo_root / relative
        if not path.is_file():
            self.reason = f"pinned tokenizer file absent: {relative}"
            return
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            self.reason = (
                f"pinned tokenizer digest mismatch for {relative}: "
                f"{digest} != {expected}"
            )
            return
        try:
            # Import by site-packages priority: experiments/tokenizers.py (the
            # 2026-08 pair-encoding experiment) shadows the installed package
            # in any process where a caller has prepended experiments/ to
            # sys.path -- the v0.17.0 gate's suite process was one, and usage
            # silently vanished there while every standalone run stayed green.
            # Production serving is unaffected (its process never carries that
            # path entry); this keeps the optional usage block meaning the
            # same thing in both.
            import importlib  # noqa: PLC0415
            import sysconfig  # noqa: PLC0415

            shadow = sys.modules.get("tokenizers")
            if shadow is not None and "site-packages" not in str(
                getattr(shadow, "__file__", "") or ""
            ):
                for name in [
                    m for m in sys.modules if m.split(".")[0] == "tokenizers"
                ]:
                    del sys.modules[name]
            saved = list(sys.path)
            sys.path.insert(0, sysconfig.get_paths()["purelib"])
            try:
                Tokenizer = importlib.import_module("tokenizers").Tokenizer
            finally:
                sys.path[:] = saved
        except (ImportError, AttributeError) as exc:
            self.reason = f"tokenizers package unavailable: {exc}"
            return
        try:
            self._tokenizer = Tokenizer.from_file(str(path))
        except Exception as exc:  # pragma: no cover - corrupt pinned file
            self.reason = f"pinned tokenizer would not load: {exc}"
            return
        self.reason = f"pinned tokenizer {relative}"

    def count(self, text: str) -> int | None:
        if self._tokenizer is None:
            return None
        return len(self._tokenizer.encode(text, add_special_tokens=False).ids)

    def usage(self, prompt_text: str, completion_text: str) -> dict | None:
        prompt = self.count(prompt_text)
        completion = self.count(completion_text)
        if prompt is None or completion is None:
            return None
        return {
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total_tokens": prompt + completion,
        }


# --------------------------------------------------------------------------
# Errors (§10), in the OpenAI error shape
# --------------------------------------------------------------------------


class ApiError(Exception):
    """One refusal, already shaped the way a stock client expects to read it."""

    def __init__(
        self,
        status: int,
        message: str,
        code: str,
        *,
        error_type: str = "invalid_request_error",
        param: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.code = code
        self.error_type = error_type
        self.param = param

    def body(self) -> dict:
        return {
            "error": {
                "message": self.message,
                "type": self.error_type,
                "param": self.param,
                "code": self.code,
            }
        }


# --------------------------------------------------------------------------
# §6 content rules
# --------------------------------------------------------------------------


def kernel_content(verdict: dict) -> str:
    """§6, verbatim: reading+answer, else answer, else detail.

    No selector lives here. The TTY renders both a `reading` and the answer
    lines (`harness.py:1232-1241`), so the skin must too; adding, dropping,
    reordering or re-parameterizing a line would be the verbosity-inflation
    hole the seal exists to close.
    """

    reading = tuple(verdict.get("reading") or ())
    answer = tuple(verdict.get("answer") or ())
    if reading:
        return "\n".join((*reading, *answer))
    if answer:
        return "\n".join(answer)
    return str(verdict["detail"])


def _normalize_transcript(content: str) -> list[str]:
    """§4's divergence normalization, and nothing beyond it.

    Split on ``"\\n"``, ``rstrip()`` each line, drop trailing empty lines.
    Whitespace *inside* a line's body participates; ``x_corollary`` does not.
    """

    lines = [line.rstrip() for line in content.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return lines


# --------------------------------------------------------------------------
# §6.1 receipts
# --------------------------------------------------------------------------


def _bound_statement_id(answer_lines) -> str | None:
    """The statement id a resolution rested on, read out of its own answer.

    Two committed shapes carry it: ``answer.render``'s ``source     : ID  [c]``
    (`scripts/answer.py:161`) and ``resolver.render``'s ``bound    : ID``
    (`scripts/resolver.py:809`); `_route_pending_context` emits the first
    without the corpus bracket. Read rather than re-derived so the receipt
    cites what the served answer actually said.
    """

    for line in answer_lines or ():
        head, sep, rest = str(line).partition(":")
        if not sep:
            continue
        label = head.strip()
        if label not in {"source", "bound"}:
            continue
        candidate = rest.strip()
        if "  [" in candidate:
            candidate = candidate.split("  [", 1)[0]
        candidate = candidate.strip()
        if candidate:
            return candidate
    return None


_CORPUS_PATHS: dict[str, str] | None = None
_CORPUS_PATHS_LOCK = threading.Lock()


def _corpus_paths(repo_root: Path) -> dict[str, str]:
    """corpus_id -> the committed `data/*/nodes.json` that declares it.

    Built once and by reading the files rather than by guessing: a corpus's
    declared ``corpus_id`` is not its directory name
    (``logic/nodes.json`` declares ``logic.boolean_foundations.v1``), so a
    receipt that composed the path from the id would cite a file that does
    not exist.
    """

    global _CORPUS_PATHS
    with _CORPUS_PATHS_LOCK:
        if _CORPUS_PATHS is None:
            found: dict[str, str] = {}
            for root in ("data", "data_holdout"):
                base = repo_root / root
                if not base.is_dir():
                    continue
                for path in sorted(base.glob("*/nodes.json")):
                    try:
                        doc = json.loads(path.read_text(encoding="utf-8"))
                    except (OSError, ValueError):  # pragma: no cover
                        continue
                    corpus = doc.get("corpus_id", path.parent.name)
                    found.setdefault(
                        str(corpus), f"{root}/{path.parent.name}/nodes.json"
                    )
            _CORPUS_PATHS = found
        return _CORPUS_PATHS


def _corpus_path(repo_root: Path, corpus: str) -> str | None:
    return _corpus_paths(repo_root).get(corpus)


def _resolution_receipt(repo_root: Path, verdict: dict) -> dict:
    """§6.1's `resolver` / `resolver_context` row, recheckable against `data/`."""

    from answer import records  # noqa: PLC0415

    statement_id = _bound_statement_id(verdict.get("answer"))
    if statement_id is None:
        return {}
    found = records().get(statement_id)
    if found is None:
        # A statement id the committed corpus does not hold is not a receipt
        # with one field missing; it is no grounding claim at all. Shipping
        # the bare id would name an artifact the answer did not rest on.
        return {}
    node, corpus = found
    receipt = {
        "statement_id": statement_id,
        "node_sha256": hashlib.sha256(canonical_bytes(node)).hexdigest(),
    }
    path = _corpus_path(repo_root, corpus)
    if path is not None:
        receipt["corpus_path"] = path
    return receipt


def _ownership_receipt(verdict: dict) -> dict:
    """§6.1's `ownership` row, taken from the verdict the engine already built.

    Until v0.20 this ran `ownership.lookup` a SECOND time, because
    `_route_ownership` rendered five witness hosts and dropped the object
    that knew the rest — the one route not following the convention
    `_route_twin` and `_route_reachable` set. The skin mitigated with a
    memo on the pure function rather than monkeypatching the engine, which
    would have been the renderer editing the record. ROADMAP-v0.20 §4a
    aligned the route instead, so the receipt is now a read.

    `hosts` is still the WHOLE host set, not the five witnesses the answer
    names: §6.1's "(top entries)" qualifies `by_corpus`, and a receipt
    listing five of 6884 hosts without saying so would misrepresent what the
    answer rests on.
    """

    receipt = verdict.get("receipt")
    if not isinstance(receipt, dict):  # pragma: no cover - the route always carries it
        return {}
    return dict(receipt)


def _evaluate_receipt(text: str) -> dict:
    """§6.1's `evaluate` row.

    A relation check has no single value, so it carries `expression` and
    `grounding` alone; an evaluation carries the exact value beside them. The
    engine's own honesty line ("no corpus statement was consulted") is already
    in `content` and is not repeated here.
    """

    from evaluate import EvalError, evaluate, verify  # noqa: PLC0415

    try:
        checked = verify(text)
    except EvalError:
        pass
    else:
        return {"expression": checked.relation, "grounding": "computed"}
    try:
        result = evaluate(text)
    except EvalError:  # pragma: no cover - an answering turn already evaluated
        return {"grounding": "computed"}
    return {
        "expression": result.expression,
        "exact": result.formatted(),
        "grounding": "computed",
    }


#: §6.1's `story` row names this path literally: the story's four constraints
#: are committed corpus statements and the receipt says where they live.
STORY_CORPUS_PATH = "data/narrative/nodes.json"


def _story_receipt(repo_root: Path) -> dict:
    del repo_root
    return {
        "constraint_ids": list(story_module.CONSTRAINT_IDS),
        "corpus_path": STORY_CORPUS_PATH,
    }


def kernel_receipt(repo_root: Path, verdict: dict, eval_text: str) -> dict:
    """§6.1, keyed on (route, answered?) — never on route alone."""

    route = verdict["route"]
    status = verdict["status"]

    # The two named exceptions, both on `closure`: a certified bounded
    # negative IS an answer, and a CORRUPT_TARGET refusal IS an answer about
    # the target's bytes. Both stay scored as what they are; the wire does
    # not strip the certificate.
    #
    # Keyed on the receipt's own `outcome` being one of `closure_query`'s
    # three, not on a `receipt` key merely being present: a future route that
    # attached some other object under that name would otherwise inherit the
    # exception and ship a grounding claim §6.1 never granted it.
    if route == "closure":
        certificate = verdict.get("receipt")
        if (
            isinstance(certificate, dict)
            and certificate.get("outcome") in CLOSURE_OUTCOME_STATUS
        ):
            return dict(certificate)

    if status not in ANSWERING_STATUSES:
        capability = verdict.get("missing_capability")
        return {"missing_capability": capability} if capability else {}

    if route in {"resolver", "resolver_context"}:
        return _resolution_receipt(repo_root, verdict)
    if route == "ownership":
        return _ownership_receipt(verdict)
    if route == "twin":
        return dict(verdict.get("receipt") or {})
    if route == "evaluate":
        return _evaluate_receipt(eval_text)
    if route == "story":
        return _story_receipt(repo_root)
    if route in {"belief", "supposition"}:
        return {"derivation": "session"}
    if route == "write_gate":
        return {"grounding": "working-tree"}
    # `gloss` is the only answering route §6.1's table does not name, and it
    # is unreachable under the offline boot. An empty receipt claims nothing,
    # which is the honest shape for a route with no committed artifact row.
    return {}


# --------------------------------------------------------------------------
# The rendered turn (content + its vendor extension)
# --------------------------------------------------------------------------


class Rendered:
    """One served assistant turn: `content`, and everything riding beside it."""

    __slots__ = ("content", "x_corollary")

    def __init__(self, content: str, x_corollary: dict) -> None:
        self.content = content
        self.x_corollary = x_corollary


def _kernel_eval_text(line: str) -> str:
    """The text a route actually consumed, for a receipt that re-derives it.

    `route_line` hands `owns`/`suppose` only the tail of the line, so a
    receipt built from the whole line would cite an expression the engine
    never evaluated.
    """

    head, _, rest = line.partition(" ")
    if head.lower() in {OWNS_COMMAND, SUPPOSE_COMMAND}:
        return rest.strip()
    return line


def render_kernel_turn(
    repo_root: Path,
    session: CoreSession,
    line: str,
    *,
    with_receipt: bool = True,
) -> Rendered:
    """One kernel-profile line, routed and rendered (§5, §6).

    ``with_receipt=False`` is used for the turns of a replayed prefix, whose
    `content` the divergence check reads and whose `x_corollary` nobody ever
    sees. Building a receipt for a turn that is not served is work the
    stopwatch would time and no client would receive; on the ownership route
    that is a whole second corpus scan per replayed turn.
    """

    verdict = route_line(repo_root, session, line)
    content = kernel_content(verdict)
    extension = {
        "schema": CHAT_SCHEMA,
        "profile": KERNEL_MODEL,
        "route": verdict["route"],
        "status": verdict["status"],
        "detail": str(verdict["detail"]),
        "receipt": (
            kernel_receipt(repo_root, verdict, _kernel_eval_text(line))
            if with_receipt
            else {}
        ),
    }
    evidence = list(verdict.get("evidence") or ())
    if evidence:
        extension["evidence"] = evidence
    return Rendered(content, extension)


def render_conversation_turn(session, utterance: str) -> Rendered:
    """One conversation-profile utterance (§6, §6.2).

    `ValueError` out of `say` is *not* caught here: §10 maps the cross-slot
    refusal to `409 slot_conflict` with the engine's own message, and
    swallowing it would be the skin reinterpreting a refusal.
    """

    turn = session.say(utterance)

    if turn.reply is not None:
        content = turn.reply
    elif turn.asked is not None:
        content = turn.asked
    else:
        # The only branch with no engine text to pass through (§6).
        slot = getattr(turn.parsed, "slot", None) or session.active_slot
        content = ABSTENTION_ACKNOWLEDGEMENT.format(slot=slot)

    if turn.abstained:
        status = "abstained"
    elif session.turns:
        status = session.turns[-1].stop_reason.value
    else:  # pragma: no cover - every non-abstain branch runs or holds a turn
        status = "waiting"

    parsed = turn.parsed
    if turn.understood:
        detail = parsed.rule_id
    else:
        detail = parsed.reason.value

    extension = {
        "schema": CHAT_SCHEMA,
        "profile": CONVERSATION_MODEL,
        "route": "conversation",
        "status": status,
        "detail": detail,
        "receipt": {},
    }

    if status == "waiting":
        # §6.2: the exact two fields the `Need` protocol exposes, and no
        # third. The client resumes by sending the next user message; the
        # binding is minted server-side by the verifier from the bytes that
        # message carried.
        need = pending_need(session.state)
        if need is not None:
            extension["need"] = {"slot": need.slot, "prompt": need.prompt}
    elif status == "solved" and turn.reply is not None:
        extension["receipt"] = {
            "binding": {
                "slot": parsed.slot,
                "value": turn.reply,
                "lifetime": parsed.lifetime.value,
            },
            "derivation": "user-frame",
        }
    return Rendered(content, extension)


# --------------------------------------------------------------------------
# §4: request mapping
# --------------------------------------------------------------------------


class ChatRequest:
    """One validated request: the turns, the prefix, and what was ignored."""

    def __init__(self, body: dict, *, handled_extra=frozenset()) -> None:
        if not isinstance(body, dict):
            raise ApiError(400, "request body must be a JSON object", "invalid_body")

        model = body.get("model")
        if not isinstance(model, str) or not model:
            raise ApiError(
                400, "'model' is required and must be a string", "missing_model",
                param="model",
            )
        if model not in PROFILES:
            raise ApiError(
                404,
                f"model {model!r} does not exist; this server serves "
                + ", ".join(repr(name) for name in PROFILES[:-1])
                + f" and {PROFILES[-1]!r}",
                "model_not_found",
                param="model",
            )
        self.model = model

        messages = body.get("messages")
        if not isinstance(messages, list) or not messages:
            raise ApiError(
                400,
                "'messages' must be a non-empty array",
                "missing_messages",
                param="messages",
            )

        # §4: `n != 1` is a 400. There is nothing to sample, so asking for two
        # samples is asking for something this server cannot honestly produce.
        count = body.get("n")
        if count is not None and count != 1:
            raise ApiError(
                400,
                "n must be 1: no token in the serving path is drawn from a "
                "generative model, so there is nothing to sample twice",
                "unsupported_n",
                param="n",
            )

        # Every message, in order, role and content — §4.1's prefix is "every
        # message strictly before the final user turn", which includes the
        # ignored ones: a system turn changes the canonical prefix and so the
        # conversation's identity, even though it changes no served token.
        self.messages: list[tuple[str, object]] = []
        ignored: list[str] = []
        for index, message in enumerate(messages):
            if not isinstance(message, dict):
                raise ApiError(
                    400,
                    f"messages[{index}] must be an object",
                    "invalid_message",
                    param="messages",
                )
            role = message.get("role")
            content = message.get("content")
            if not isinstance(role, str):
                raise ApiError(
                    400,
                    f"messages[{index}].role must be a string",
                    "invalid_message",
                    param="messages",
                )
            if role == "tool":
                # ¶AMD-3: the one admitted non-message item, and only on the
                # profile that has a pending request for it to bind to. On
                # every other profile this is the same 400 it always was.
                self.messages.append(("tool", self._tool_result(message, index, model)))
                continue
            if not isinstance(content, str):
                raise ApiError(
                    400,
                    f"messages[{index}].content must be a string; this server "
                    "has no multimodal channel and will not guess one",
                    "invalid_message",
                    param="messages",
                )
            self.messages.append((role, content))
            if role not in {"user", "assistant"}:
                # §4: accepted and ignored, and the response says so. The
                # engine has no system-prompt channel; inventing one would be
                # a new answerable surface, which this cycle forbids.
                ignored.append(f"{role}[{index}]")

        user_indices = [
            i for i, (role, _) in enumerate(self.messages) if role == "user"
        ]
        if not user_indices:
            raise ApiError(
                400,
                "no user turn: the message array's user turns are the "
                "session's input lines and there were none",
                "missing_user_turn",
                param="messages",
            )
        # The served turn is the last **input item**, which is a user turn on
        # every profile and may also be an admitted tool result on
        # `corollary/protocol` (¶AMD-3). Before AMD-3 the two were the same
        # index by construction, and on the two shipped profiles they still
        # are: `role == "tool"` cannot reach `self.messages` there.
        input_indices = [
            i for i, (role, _) in enumerate(self.messages) if role in ("user", "tool")
        ]
        self.final_input_index = input_indices[-1]
        self.final_input = self.messages[self.final_input_index]
        self.final_user_index = self.final_input_index

        # §4: sampling parameters (and anything else this skin does not act
        # on) are accepted, ignored, and listed. Keys this server *enforces*
        # are excluded: see :data:`ENFORCED_BODY_KEYS`. `handled_extra` is
        # ¶AMD-3's addition: the Responses path on `corollary/protocol` ACTS
        # on `tools` and `tool_choice`, and a response that called a field it
        # acted on "ignored" would be describing itself wrongly.
        handled = HANDLED_BODY_KEYS | frozenset(handled_extra)
        ignored.extend(
            sorted(
                key
                for key in body
                if key not in handled and key not in ENFORCED_BODY_KEYS
            )
        )
        self.ignored = ignored

        self.prefix = self.messages[: self.final_input_index]
        self.prefix_hash = prefix_hash(self.prefix)
        self.tail = self.messages[self.final_input_index + 1 :]
        # ¶AMD-3. The protocol runtime derives its `request_id` from its own
        # session id, so a `call_id` can only survive ¶DEV-1's replay if that
        # id is the SAME on every request of one conversation. The §4.1 prefix
        # hash is not: it grows with the transcript. The canonical hash of the
        # conversation's FIRST item is — it is the one part of a transcript
        # replay cannot change — so that is this profile's session identity.
        # The wire field `session.profile_session_id` is unchanged on all
        # three profiles: it stays the §4.1 prefix hash.
        self.protocol_session_id = prefix_hash(self.messages[:1])

        self.stream = bool(body.get("stream"))
        options = body.get("stream_options")
        self.include_usage = bool(
            isinstance(options, dict) and options.get("include_usage")
        )
        self.prompt_text = "\n".join(
            content if isinstance(content, str) else canonical(content)
            for _role, content in self.messages
        )

    @staticmethod
    def _tool_result(message: dict, index: int, model: str) -> dict:
        """§4.2's one admitted non-message item, validated rather than guessed."""

        if model != PROTOCOL_MODEL:
            raise ApiError(
                400,
                f"messages[{index}] is a tool result, which only "
                f"{PROTOCOL_MODEL!r} admits; no other profile has a pending "
                "request for one to bind to",
                "invalid_message",
                param="messages",
            )
        call_id = message.get("call_id")
        output = message.get("output")
        if not isinstance(call_id, str) or not call_id:
            raise ApiError(
                400,
                f"messages[{index}].call_id must be a non-empty string",
                "invalid_message",
                param="messages",
            )
        if not isinstance(output, str):
            raise ApiError(
                400,
                f"messages[{index}].output must be a string",
                "invalid_message",
                param="messages",
            )
        return {"call_id": call_id, "output": output}

    def next_prefix_hash(self, content: str) -> str:
        """The prefix hash of the transcript a client continuing from here sends."""

        return prefix_hash(
            [*self.prefix, self.final_input, ("assistant", content)]
        )


class ResponsesRequest:
    """Validated Responses text subset mapped onto :class:`ChatRequest`."""

    _MAPPED_KEYS = frozenset(
        {"model", "input", "previous_response_id", "stream"}
    )

    def __init__(self, body: dict, engine: "ChatEngine") -> None:
        if not isinstance(body, dict):
            raise ApiError(400, "request body must be a JSON object", "invalid_body")

        previous = body.get("previous_response_id")
        if previous is not None and (not isinstance(previous, str) or not previous):
            raise ApiError(
                400,
                "'previous_response_id' must be a non-empty string",
                "invalid_previous_response_id",
                param="previous_response_id",
            )
        model = body.get("model")
        # ¶AMD-3. The adapter registers for exactly one (name, schema digest)
        # pair, on exactly one profile. `tool_choice: "none"` suppresses the
        # call the way the Responses contract says it should — the need is
        # still opened, it is simply presented as text.
        self.tool_choice = body.get("tool_choice")
        self.prompt_tool = (
            match_prompt_tool(body.get("tools"))
            if model == PROTOCOL_MODEL and self.tool_choice != "none"
            else None
        )

        prior = engine.response_transcript(previous) if previous else []
        incoming = self._messages(body.get("input"), model)
        has_user_text = any(
            role == "user" and content for role, content in incoming
        )
        has_tool_result = any(role == "tool" for role, _ in incoming)
        if not has_user_text and not has_tool_result:
            raise ApiError(
                400,
                "Responses input must contribute new, non-empty user text; "
                "a stored transcript cannot supply the current turn",
                "missing_user_text",
                param="input",
            )

        chat_body = {
            key: value for key, value in body.items() if key not in self._MAPPED_KEYS
        }
        chat_body.update(
            {
                "model": model,
                "messages": [
                    self._chat_message(role, content)
                    for role, content in (*prior, *incoming)
                ],
                "stream": bool(body.get("stream")),
            }
        )
        self.chat = ChatRequest(
            chat_body,
            handled_extra=(
                PROTOCOL_HANDLED_RESPONSES_KEYS
                if model == PROTOCOL_MODEL
                else frozenset()
            ),
        )
        self.stream = self.chat.stream

    @property
    def admitted_tools(self) -> list:
        """Exactly the declarations this profile took up — never a blanket echo."""

        return [self.prompt_tool["declaration"]] if self.prompt_tool else []

    @staticmethod
    def _chat_message(role: str, content) -> dict:
        if role == "tool":
            return {
                "role": "tool",
                "call_id": content["call_id"],
                "output": content["output"],
            }
        return {"role": role, "content": content}

    @classmethod
    def _messages(cls, value, model=None) -> list[tuple[str, object]]:
        if isinstance(value, str):
            return [("user", value)]
        if not isinstance(value, list) or not value:
            raise ApiError(
                400,
                "'input' must be a string or a non-empty array of message items",
                "missing_input",
                param="input",
            )

        messages: list[tuple[str, object]] = []
        for index, item in enumerate(value):
            item_type = item.get("type", "message") if isinstance(item, dict) else None
            if (
                item_type == "function_call_output"
                and isinstance(item, dict)
                and model == PROTOCOL_MODEL
            ):
                # ¶AMD-3 amends §4.2's non-message refusal for EXACTLY this
                # item type, on exactly this profile. Every other non-message
                # item — a reasoning item, a `function_call` echo, a
                # multimodal part — still refuses below rather than being
                # guessed at.
                messages.append(("tool", cls._function_call_output(item, index)))
                continue
            if not isinstance(item, dict) or item_type != "message":
                raise ApiError(
                    400,
                    f"input[{index}] must be a message item; this server does "
                    "not invent meanings for tool, reasoning, or multimodal items",
                    "invalid_input_item",
                    param="input",
                )
            role = item.get("role")
            if not isinstance(role, str):
                raise ApiError(
                    400,
                    f"input[{index}].role must be a string",
                    "invalid_input_item",
                    param="input",
                )
            messages.append((role, cls._content(item.get("content"), index)))
        return messages

    @staticmethod
    def _function_call_output(item: dict, index: int) -> dict:
        call_id = item.get("call_id")
        output = item.get("output")
        if not isinstance(call_id, str) or not call_id:
            raise ApiError(
                400,
                f"input[{index}].call_id must be a non-empty string: a tool "
                "result with no call id binds to no pending request",
                "invalid_input_item",
                param="input",
            )
        if not isinstance(output, str):
            raise ApiError(
                400,
                f"input[{index}].output must be a string",
                "invalid_input_item",
                param="input",
            )
        return {"call_id": call_id, "output": output}

    @staticmethod
    def _content(value, index: int) -> str:
        if isinstance(value, str):
            return value
        if not isinstance(value, list) or not value:
            raise ApiError(
                400,
                f"input[{index}].content must be text or a non-empty text-part array",
                "invalid_input_item",
                param="input",
            )
        chunks = []
        for part_index, part in enumerate(value):
            if (
                not isinstance(part, dict)
                or part.get("type") not in {"input_text", "output_text"}
                or not isinstance(part.get("text"), str)
            ):
                raise ApiError(
                    400,
                    f"input[{index}].content[{part_index}] must be an "
                    "input_text or output_text part",
                    "invalid_input_item",
                    param="input",
                )
            chunks.append(part["text"])
        return "".join(chunks)


def _check_divergence(claimed: str, produced: str | None) -> None:
    """§4's divergence check, exactly as defined there and no wider."""

    if produced is None:
        raise ApiError(
            409,
            "the transcript claims an assistant turn this session never "
            "produced",
            "transcript_divergence",
            param="messages",
        )
    if _normalize_transcript(claimed) != _normalize_transcript(produced):
        raise ApiError(
            409,
            "assistant transcript diverges from the replayed session: this "
            "server replays your user turns and renders the engine's own "
            "output, so a claimed turn it did not produce cannot be continued",
            "transcript_divergence",
            param="messages",
        )


# --------------------------------------------------------------------------
# The engine: replay, the replay-equivalent cache, and the sheet
# --------------------------------------------------------------------------


class _CacheEntry:
    __slots__ = ("model", "session")

    def __init__(self, model: str, session) -> None:
        self.model = model
        self.session = session


class KernelSessionPool:
    """Freshly booted kernel sessions, kept ready off the request path.

    A pooled session is **indistinguishable from a cold boot**, and that is a
    claim with a proof rather than a hope. `CoreSession.boot` takes an optional
    `session_id` and otherwise mints a random one; nothing else in `boot`
    reads it (the boot event it appends names only the registered and
    optional-off subsystems). A fresh session's `state` is `None`, and no
    field carried between turns — the pending candidate set, the hop counters,
    the graph index — is derived from the id. So booting without an id and
    assigning the prefix hash on the way out is the same object a cold boot
    with `session_id=` would have produced. It is also the exact realignment
    the cache-hit path already performs and documents (`_serve_locked`).

    The pool never decides an answer. `take()` returns `None` when empty and
    the caller boots on demand, so a slow refill costs latency and nothing
    else. `hits`/`misses` are exposed so a test can prove the pool was
    actually exercised rather than silently bypassed — an equivalence test
    against a pool that never fired would be a test of nothing.
    """

    #: How long the server must stay idle before the refill thread starts a
    #: boot. Booting holds the GIL for ~415 ms, so a refill that overlaps a
    #: request makes BOTH slower — measured: with an always-on refill thread,
    #: a pool miss cost ~1800 ms against the ~580 ms it costs with no pool at
    #: all. Yielding to in-flight work bounds the miss at the no-pool cost,
    #: which is the floor a pool must never push a request below.
    QUIET_PERIOD_SECONDS = 0.05

    def __init__(self, boot, size: int, idle: threading.Event | None = None) -> None:
        self._boot = boot
        self._idle = idle if idle is not None else threading.Event()
        if idle is None:
            self._idle.set()
        self._size = max(0, int(size))
        self._ready: "queue.Queue" = queue.Queue(maxsize=max(1, self._size))
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._counts = threading.Lock()
        self.hits = 0
        self.misses = 0
        self.boot_failures = 0

    @property
    def size(self) -> int:
        return self._size

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self._size <= 0 or self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._refill, name="corollary-skin-session-pool", daemon=True
        )
        self._thread.start()

    def take(self):
        """One ready session, or `None` — never a blocking wait.

        Blocking here would trade the boot this pool exists to remove for a
        wait of the same length, and would make a request's latency depend on
        a background thread's progress. An empty pool is a miss the caller
        handles by booting, which is exactly what happened before the pool.
        """

        if self._size <= 0:
            with self._counts:
                self.misses += 1
            return None
        try:
            session = self._ready.get_nowait()
        except queue.Empty:
            with self._counts:
                self.misses += 1
            return None
        with self._counts:
            self.hits += 1
        return session

    def stop(self) -> None:
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.join(timeout=10.0)
        while True:
            try:
                self._ready.get_nowait()
            except queue.Empty:
                return

    def _wait_for_quiet(self) -> bool:
        """True when the server has been idle long enough to spend a boot.

        Under a tight sequential load this returns False forever and the pool
        simply stops refilling — which is the right answer, not a failure: a
        session booted into a queue that is drained the instant it lands has
        bought nothing, and the boot it cost would have been stolen from the
        request being served. The load then degrades to exactly the on-demand
        behaviour that existed before this pool.
        """

        if not self._idle.wait(timeout=0.5):
            return False
        # The idle flag must HOLD, not merely have been observed: back-to-back
        # requests leave sub-millisecond gaps, and starting a 415 ms boot in
        # one of them is the contention this guard exists to avoid.
        self._stop.wait(self.QUIET_PERIOD_SECONDS)
        return self._idle.is_set() and not self._stop.is_set()

    def _refill(self) -> None:
        while not self._stop.is_set():
            if not self._wait_for_quiet():
                continue
            try:
                session = self._boot()
            except Exception:  # pragma: no cover - a boot the probes refused
                # The pool is not the place to decide a boot failure means
                # anything: the on-demand path will raise it where a client
                # can be told. Back off so a permanently broken tree does not
                # spin a core.
                with self._counts:
                    self.boot_failures += 1
                self._stop.wait(1.0)
                continue
            while not self._stop.is_set():
                try:
                    self._ready.put(session, timeout=0.25)
                    break
                except queue.Full:
                    continue


class ChatEngine:
    """One session engine behind the HTTP renderer (A-IH6).

    The whole serving path runs under one lock. That is not a throughput
    concession made carelessly: the engine's session objects are mutable and
    single-owner by contract (§2), and serving two requests into one of them
    concurrently would be the second engine A-IH6 forbids, wearing a race
    condition instead of a second file.
    """

    def __init__(
        self,
        repo_root: Path,
        *,
        cache_size: int = 32,
        pool_size: int = DEFAULT_POOL_SIZE,
    ) -> None:
        self.repo_root = repo_root
        self.tokens = TokenCounter(repo_root)
        # ¶AMD-3: the adapter U-P1 captured, registered from the capture and
        # from nowhere else. Idempotent, so a second engine re-reads rather
        # than duplicating.
        load_captured_prompt_tools(repo_root)
        self._lock = threading.Lock()
        self._cache: "OrderedDict[str, _CacheEntry]" = OrderedDict()
        self._cache_size = cache_size
        self._response_lock = threading.Lock()
        self._response_transcripts: "OrderedDict[str, list[tuple[str, str]]]" = (
            OrderedDict()
        )
        self._warm_index = None
        self._matrix = None
        self.created = int(time.time())
        #: Clear while a request is being served. The pool's refill thread
        #: waits on it so a background boot never competes with a live turn.
        self._idle = threading.Event()
        self._idle.set()
        # The pool boots through this engine's own boot path, so it reads
        # `_warm_index` at call time and inherits it as soon as prewarm has
        # one. It is started at the END of prewarm, not here: a pool filled
        # before the index existed would hand out sessions that pay for it.
        self.pool = KernelSessionPool(self._boot_kernel, pool_size, self._idle)

    # -- A11 --------------------------------------------------------------

    def prewarm(self) -> None:
        """Boot one kernel session and run one throwaway free-text line (A11).

        The line reaches `_route_resolver`, which builds the graph index, so
        the *first* request pays a routing cost instead of an indexing one.
        The index is immutable and `resolver.default_index()` is deterministic,
        so handing the same object to every later session is replay-equivalent
        by construction — which is what makes this a warm-up rather than a
        cache with opinions.
        """

        session = CoreSession.boot(self.repo_root, offline=True, session_id="warmup")
        route_line(self.repo_root, session, WARMUP_LINE)
        self._warm_index = session.resolver_index
        self._matrix = session.matrix
        # The corpus_id -> path map a resolution receipt needs. Measured at
        # ~300 ms on first use, which is a cost the first request should not
        # pay and the stopwatch should not see.
        _corpus_paths(self.repo_root)
        # P-IH3 fails the server at startup rather than at the first GET.
        assert_no_demo_name(self.capability_sheet(), "GET /v1/capabilities")
        assert_no_demo_name(self.model_list(), "GET /v1/models")
        # Last, so every pooled session inherits the warm index above.
        self.pool.start()

    def shutdown(self) -> None:
        """Stop the refill thread. Idempotent; safe on a pool never started."""

        self.pool.stop()

    @property
    def matrix(self):
        if self._matrix is None:
            self.prewarm()
        return self._matrix

    # -- session construction --------------------------------------------

    def _boot_kernel(self) -> CoreSession:
        """One offline boot with the shared graph index, id not yet assigned.

        The id is deliberately left as `boot`'s random default here: this is
        the pool's boot too, and a pooled session does not know which
        conversation will claim it. :meth:`_kernel_session` assigns it.
        """

        session = CoreSession.boot(self.repo_root, offline=True)
        if self._warm_index is not None:
            session.resolver_index = self._warm_index
        return session

    def _kernel_session(self, session_id: str) -> CoreSession:
        """§3/§4: the offline boot, threaded on the canonical prefix hash.

        Served from the pool when one is ready and booted on demand when not.
        Both arms end at the same object: see :class:`KernelSessionPool` for
        why assigning the id after the boot is the same session a cold
        `boot(session_id=…)` produces.
        """

        session = self.pool.take()
        if session is None:
            session = self._boot_kernel()
        elif session.resolver_index is None and self._warm_index is not None:
            # Booted before prewarm finished; give it the index a cold boot
            # would now get, so a pooled turn never pays to rebuild it.
            session.resolver_index = self._warm_index
        session.session_id = session_id
        return session

    def _conversation_session(self, owner_hash: str):
        """§3/§4: the slot-filling session, owner derived from the same hash.

        The key ring is ephemeral and per-conversation: one owner, one ring,
        gone when the process is. No durable authority is asserted (¶DEV-1).
        """

        return golden_chicken_revision_session(
            owner=conversation_owner(owner_hash),
            keyring=SessionKeyRing.ephemeral(),
        )

    def _protocol_session(self, session_id: str) -> ProtocolProfileSession:
        """¶AMD-3: the fresh session type, mounted over the protocol runtime.

        Not `golden_chicken_revision_session` and not kernel line routing —
        which is the whole point of replacing the else-branch below.
        """

        return ProtocolProfileSession(self.repo_root, session_id)

    def _fresh(self, model: str, request: ChatRequest):
        """¶AMD-3: an explicit three-way dispatch, with no fall-through.

        Until AMD-3 this read `if kernel: … else: conversation`, so every
        non-kernel model — including one the model list had not registered —
        constructed the two-slot demo session. An allowlist edit alone would
        therefore have served `corollary/protocol` as the conversation
        profile. The dispatch is now exhaustive over :data:`PROFILES` and
        raises on anything else, so a fourth profile cannot be half-added.
        """

        if model == KERNEL_MODEL:
            return self._kernel_session(request.prefix_hash)
        if model == CONVERSATION_MODEL:
            return self._conversation_session(request.prefix_hash)
        if model == PROTOCOL_MODEL:
            return self._protocol_session(request.protocol_session_id)
        raise ApiError(  # pragma: no cover - ChatRequest 404s first
            404,
            f"model {model!r} has no registered session object",
            "model_not_found",
            param="model",
        )

    def _render(
        self, model: str, session, role: str, content, *, with_receipt: bool = True
    ) -> Rendered:
        if model == KERNEL_MODEL:
            return render_kernel_turn(
                self.repo_root, session, content, with_receipt=with_receipt
            )
        if model == PROTOCOL_MODEL:
            return render_protocol_turn(
                session,
                role,
                content,
                source=f"http:{PROTOCOL_MODEL}",
                with_receipt=with_receipt,
            )
        if model == CONVERSATION_MODEL:
            try:
                return render_conversation_turn(session, content)
            except ValueError as exc:
                # §10: the engine's own message, under a code distinct from
                # transcript_divergence so a client can tell them apart.
                raise ApiError(
                    409, str(exc), "slot_conflict", param="messages"
                ) from None
        raise ApiError(  # pragma: no cover - ChatRequest 404s first
            404,
            f"model {model!r} has no registered renderer",
            "model_not_found",
            param="model",
        )

    # -- §4 replay --------------------------------------------------------

    def serve(self, request: ChatRequest) -> Rendered:
        # The idle flag brackets the WHOLE served turn, lock acquisition
        # included: a request queued behind another is still in flight, and
        # the refill thread must yield to it too.
        self._idle.clear()
        try:
            with self._lock:
                return self._serve_locked(request)
        finally:
            self._idle.set()

    def _serve_locked(self, request: ChatRequest) -> Rendered:
        entry = self._cache.pop(request.prefix_hash, None)
        if entry is not None and entry.model == request.model:
            # A cache hit means the incoming prefix is byte-identical, under
            # §4.1's canonical hash, to a transcript THIS server produced and
            # already checked — so the divergence check on the prefix is
            # satisfied by construction rather than skipped. Any tampering,
            # whitespace included, changes the hash and falls to the cold
            # replay below, where the normalized comparison decides.
            session = entry.session
            if request.model == KERNEL_MODEL:
                # What a cold replay of this prefix would have booted with.
                # Nothing carried across turns is derived from it (the pending
                # resolver set, the hop counters and the graph index are not),
                # so this assignment is the whole of the difference.
                session.session_id = request.prefix_hash
        else:
            session = self._fresh(request.model, request)
            self._replay_prefix(request, session)

        rendered = self._render(request.model, session, *request.final_input)

        for role, content in request.tail:
            if role == "assistant":
                _check_divergence(content, rendered.content)

        rendered.x_corollary["ignored"] = list(request.ignored)
        rendered.x_corollary["session"] = {
            "profile_session_id": request.prefix_hash
        }

        self._cache[request.next_prefix_hash(rendered.content)] = _CacheEntry(
            request.model, session
        )
        while len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)
        return rendered

    def _replay_prefix(self, request: ChatRequest, session) -> None:
        """Replay the prefix's user turns; check its assistant claims (§4).

        An assistant claim is compared to the MOST RECENT turn the replay
        produced, which is the only pairing §4 describes: "the claimed
        ``content`` string is compared to the replayed turn's ``content``".
        A first-in-first-out queue was wrong and provably so — with
        ``[u1, u2, a, u3]`` it paired ``a`` with ``u1``, so the truthful
        claim (what ``u2`` actually rendered) was refused as a divergence
        while a stale rendering of ``u1`` was accepted. It also disagreed
        with the tail check below, which was always most-recent; one rule
        now governs both.

        ``last_produced`` is overwritten, never cleared, so two identical
        consecutive assistant claims both pass. That is deliberate: §4's
        comparison is a statement about content, and a client that repeats
        the same true assistant turn has told no lie for the check to catch.
        """

        last_produced: str | None = None
        for role, content in request.prefix:
            if role in ("user", "tool"):
                last_produced = self._render(
                    request.model, session, role, content, with_receipt=False
                ).content
            elif role == "assistant":
                _check_divergence(content, last_produced)

    # -- §4.2 Responses replay handles ----------------------------------

    def response_transcript(self, response_id: str) -> list[tuple[str, str]]:
        """Return the in-process transcript named by ``previous_response_id``."""

        with self._response_lock:
            transcript = self._response_transcripts.get(response_id)
            if transcript is None:
                raise ApiError(
                    404,
                    f"previous response {response_id!r} is not available in "
                    "this process",
                    "previous_response_not_found",
                    param="previous_response_id",
                )
            return list(transcript)

    def remember_response(
        self, response_id: str, request: ChatRequest, rendered: Rendered
    ) -> None:
        """Keep only replay material; no engine authority or durable state."""

        transcript = [
            *request.messages[: request.final_input_index + 1],
            ("assistant", rendered.content),
        ]
        with self._response_lock:
            self._response_transcripts[response_id] = transcript
            self._response_transcripts.move_to_end(response_id)
            while len(self._response_transcripts) > self._cache_size:
                self._response_transcripts.popitem(last=False)

    # -- §7 the capability sheet -----------------------------------------

    def capability_sheet(self) -> dict:
        """Generated from the live objects, never a hand-maintained copy.

        Linted for demo names before it can be returned (P-IH3, §7).
        """

        matrix = self._matrix if self._matrix is not None else self.matrix
        registered = set(matrix.registered_ids())
        rows = []
        for row in LINE_GRAMMAR:
            served = all(need in registered for need in row["requires"])
            entry = {
                "form": row["form"],
                "route": row["route"],
                "example": row["example"],
                "statuses": list(row["statuses"]),
                "served": served,
                "requires": list(row["requires"]),
            }
            if "note" in row:
                entry["note"] = row["note"]
            rows.append(entry)

        sheet = {
            "schema": CAPABILITIES_SCHEMA,
            "profiles": {
                KERNEL_MODEL: {
                    "session_object": "harness.CoreSession",
                    "boot": "offline",
                    "grammar": "registered line grammar",
                    "description": PROFILE_DESCRIPTIONS[KERNEL_MODEL],
                    "resume": "narrow <kind> <value> / cancel",
                },
                CONVERSATION_MODEL: {
                    "session_object": "conversation.ConversationSession",
                    "boot": "ephemeral key ring, one owner per conversation",
                    "grammar": "request_grammar.parse_request",
                    "description": PROFILE_DESCRIPTIONS[CONVERSATION_MODEL],
                    "resume": "the next user message is the reply",
                },
                # ¶AMD-3. A block of its own; neither shipped block above
                # moves by a byte.
                PROTOCOL_MODEL: {
                    "session_object": "protocol_runtime.ProtocolSession",
                    "boot": (
                        "a fresh protocol session over the sealed protocol "
                        "corpus; an episode stack, one pending need, no "
                        "durable state"
                    ),
                    "grammar": (
                        "no line grammar and no request grammar: the request "
                        "surface is the protocol runtime, which takes the "
                        "utterance as an exact lookup key into the sealed "
                        "corpus and admits a transition only from witnesses "
                        "and declared context signals"
                    ),
                    "description": PROFILE_DESCRIPTIONS[PROTOCOL_MODEL],
                    "resume": (
                        "a registered function_call_output whose call_id is "
                        "the pending request_id, or the next user message "
                        "under the text WAITING fallback"
                    ),
                    "honesty": (
                        "uptake is this system's own, not a claim about "
                        "private human intent; exact conformance to the "
                        "sealed transition table does not establish that the "
                        "table describes human convention"
                    ),
                    "tool_capability": (
                        "this profile emits at most ONE function call per "
                        "turn, so the catalog's supports_parallel_tool_calls "
                        "and the Responses body's parallel_tool_calls both "
                        "read false and agree"
                    ),
                },
            },
            "line_grammar": rows,
            "request_grammar": {
                "slot_phrases": dict(request_grammar.SLOT_PHRASES),
                "slot_values": {
                    slot: list(values)
                    for slot, values in request_grammar.SLOT_VALUES.items()
                },
                "rules": [
                    {"rule_id": rule_id, "description": description}
                    for rule_id, description in request_grammar.coverage()
                ],
            },
            "boot_matrix": [
                {
                    "subsystem": record.subsystem_id,
                    "liveness": record.liveness.value,
                    "optional": record.optional,
                    "detail": record.detail,
                }
                for record in matrix.records
            ],
            "statuses": {
                "engine": list(ENGINE_STATUSES),
                "write_gate": list(WRITE_GATE_STATUSES),
                "skin_assigned": list(SKIN_ASSIGNED_STATUSES),
            },
            "protocol_grammar": self.protocol_grammar_block(),
            "prompt_tool_adapters": [
                dict(adapter)
                for _name, adapter in sorted(PROMPT_TOOL_ADAPTERS.items())
            ],
            "realization": realization_row(str(self.repo_root)),
            "conformance": conformance_row(str(self.repo_root)),
            "foreign_voice": foreign_voice_row(str(self.repo_root)),
            "honesty": HONESTY_LINE,
            "replay": (
                "every request replays its user turns into a fresh session; "
                "no durable session is resumed over HTTP"
            ),
            "usage": (
                "informational only, omitted when the pinned baseline "
                f"tokenizer is unavailable ({self.tokens.reason})"
            ),
        }
        assert_no_demo_name(sheet, "GET /v1/capabilities")
        return sheet

    def protocol_grammar_block(self) -> dict:
        """¶AMD-3's generated sheet block, read from the live sealed corpus.

        Generated, never copied — §7's rule for every other block. A row here
        that disagreed with `protocol/protocols.json` would be the sheet
        rotting in its first field, and the moves are enumerated from the
        corpus's own nodes so a regenerated corpus republishes itself.

        A row this profile cannot reach is published rather than hidden, the
        way the gloss row is: the three context signals with no HTTP source
        event are named here with the reason, so a client can see that a
        `quoted_datum` move is unreachable over HTTP in this slice instead of
        discovering it from an unexplained refusal.
        """

        corpus, error = _read_json(self.repo_root / PROTOCOL_CORPUS)
        if not isinstance(corpus, dict):
            return {
                "served": False,
                "corpus_path": PROTOCOL_CORPUS,
                "reason": f"no readable protocol corpus at {PROTOCOL_CORPUS}: {error}",
            }
        moves = [
            {
                "protocol_id": node["protocol_id"],
                "family": node["family"],
                "move_id": move["move_id"],
                "kind": move["kind"],
                "requires": {
                    predicate["signal_id"]: predicate["required_value"]
                    for predicate in move["required_signal_predicates"]
                },
            }
            for node in corpus["nodes"]
            for move in node["moves"]
        ]
        return {
            "served": True,
            "corpus_path": PROTOCOL_CORPUS,
            "corpus_schema": corpus["schema"],
            "generator": corpus["generator"],
            "runtime_module": corpus["runtime_module"],
            "normalization": corpus["normalization"],
            "predicate_language": corpus["predicate_language"],
            "absence_sentinel": corpus["absence_sentinel"],
            "families": list(corpus["families"]),
            "move_kinds": list(corpus["move_kinds"]),
            "context_signal_ids": list(corpus["context_signal_ids"]),
            "stack_depth_cap": corpus["stack_depth_cap"],
            "moves": moves,
            "statuses": sorted(set(PROTOCOL_DISPOSITION_STATUS.values())),
            "dispositions": dict(PROTOCOL_DISPOSITION_STATUS),
            "served_context_signals": {
                "pending_need": (
                    "derived from this session's own pending need: the slot "
                    "the verifier minted it for, or the absence sentinel"
                ),
                "protocol_stack": (
                    "derived from this session's own episode stack, through "
                    "the runtime's top summary"
                ),
                **{
                    signal: (
                        "no HTTP source event exists for this signal in this "
                        "slice, so it carries the absence sentinel; it is "
                        "published rather than hidden"
                    )
                    for signal in PROTOCOL_SIGNALS_WITHOUT_AN_HTTP_SOURCE
                },
            },
            "no_authority": (
                "no protocol move may authorize WRITE, process creation, "
                "filesystem, shell, or network access; authority_delta is a "
                "present, plaintext, empty field on every served receipt"
            ),
        }

    def model_list(self) -> dict:
        standard_models = [
            {
                "id": model,
                "object": "model",
                "created": self.created,
                "owned_by": "corollary",
                "description": PROFILE_DESCRIPTIONS[model],
            }
            for model in PROFILES
        ]
        models = {
            "object": "list",
            "data": standard_models,
            # Codex CLI probes the provider's /models route for its richer
            # local catalog.  Keeping both keys makes the same endpoint useful
            # to stock OpenAI clients and Codex without user-agent branching.
            "models": [
                {
                    "slug": model,
                    "display_name": model,
                    "description": PROFILE_DESCRIPTIONS[model],
                    "default_reasoning_level": "medium",
                    "supported_reasoning_levels": CODEX_REASONING_LEVELS,
                    "shell_type": "disabled",
                    "visibility": "list",
                    "supported_in_api": True,
                    "priority": priority,
                    "model_messages": {
                        "instructions_template": "",
                        "instructions_variables": None,
                    },
                    "include_skills_usage_instructions": False,
                    "include_plugin_usage_instructions": False,
                    "include_apps_usage_instructions": False,
                    "support_verbosity": False,
                    "truncation_policy": {"mode": "tokens", "limit": 10000},
                    # ¶AMD-3 reconciles this key with the Responses body on
                    # the protocol profile: false here, false there, because
                    # the profile emits at most one call. The two shipped
                    # profiles keep the values (and the pre-existing
                    # body/catalog disagreement) they shipped with; that
                    # contradiction is out of this slice's scope and is
                    # deliberately not copied onto the new row.
                    "supports_parallel_tool_calls": False,
                    "context_window": 32768,
                    # Exactly the captured supported tool, on exactly the
                    # profile that answers it (DESIGN §12). The KEY SET stays
                    # identical across all three rows on purpose: Codex
                    # deserializes this catalog, and a key present on one row
                    # only is a compatibility risk taken for nothing. The
                    # reconciliation note lives in the capability sheet's
                    # profile block instead.
                    "experimental_supported_tools": (
                        sorted(PROMPT_TOOL_ADAPTERS)
                        if model == PROTOCOL_MODEL
                        else []
                    ),
                    "input_modalities": ["text"],
                }
                for priority, model in enumerate(PROFILES, start=1)
            ],
        }
        assert_no_demo_name(models, "GET /v1/models")
        return models


# --------------------------------------------------------------------------
# Response shapes (§6, §8)
# --------------------------------------------------------------------------


def _completion_id() -> str:
    return "chatcmpl-" + uuid.uuid4().hex


def completion_body(
    request: ChatRequest, rendered: Rendered, usage: dict | None
) -> dict:
    body = {
        "id": _completion_id(),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": rendered.content},
                # §6: a WAITING turn is a *complete* assistant turn that asks
                # a question, not a truncation.
                "finish_reason": "stop",
            }
        ],
        "x_corollary": rendered.x_corollary,
    }
    if usage is not None:
        body["usage"] = usage
    return body


def stream_chunks(
    request: ChatRequest, rendered: Rendered, usage: dict | None
) -> list[dict]:
    """§8. Chunk boundaries are rendered lines; deltas concatenate exactly.

    Every chunk after the first carries its own leading ``"\\n"``, so a client
    that reassembles the stream and sends the turn back reproduces `content`
    byte-for-byte — which is what keeps §4's divergence comparison stable.
    """

    completion = _completion_id()
    created = int(time.time())

    def envelope(choices, extra=None) -> dict:
        chunk = {
            "id": completion,
            "object": "chat.completion.chunk",
            "created": created,
            "model": request.model,
            "choices": choices,
        }
        if extra:
            chunk.update(extra)
        return chunk

    lines = rendered.content.split("\n")
    chunks = [
        envelope(
            [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": lines[0]},
                    "finish_reason": None,
                }
            ]
        )
    ]
    for line in lines[1:]:
        chunks.append(
            envelope(
                [
                    {
                        "index": 0,
                        "delta": {"content": "\n" + line},
                        "finish_reason": None,
                    }
                ]
            )
        )
    chunks.append(
        envelope(
            [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            {"x_corollary": rendered.x_corollary},
        )
    )
    if usage is not None and request.include_usage:
        # Only when the client asks, matching the OpenAI contract.
        chunks.append(envelope([], {"usage": usage}))
    return chunks


def _response_id() -> str:
    return "resp_" + uuid.uuid4().hex


def _response_usage(usage: dict | None) -> dict | None:
    if usage is None:
        return None
    prompt = usage["prompt_tokens"]
    completion = usage["completion_tokens"]
    return {
        "input_tokens": prompt,
        "input_tokens_details": {"cached_tokens": 0},
        "output_tokens": completion,
        "output_tokens_details": {"reasoning_tokens": 0},
        "total_tokens": prompt + completion,
    }


def prompt_call_item(rendered: Rendered, tool: dict) -> dict | None:
    """§8/¶AMD-3: ONE `function_call` output item for an approved need.

    Returns None unless this turn actually opened a need — the adapter
    represents an **already-approved** need and never manufactures one, so a
    turn that selected a move or refused emits the ordinary message item.

    The arguments are the capture's own `mapping_to_need`, followed literally:
    one question, `id` = the need's slot, `header` = the fixed literal
    `protocol`, `question` = the verifier-minted prompt, and one
    `{label, description}` option per unresolved candidate move id in
    canonical order. Question wording is outside the scored claim (DESIGN §4);
    the typed need and its exact binding are what count.

    One recorded caveat: the captured tool's description says `id` should be
    snake_case, and the mapping says `id` is the slot, which is
    `protocol_uptake.candidate_move` — snake_case but for the dotted
    namespace. The mapping is the committed registration record, so it is
    followed literally rather than sanitized into something the capture does
    not say; whether the installed host accepts it is exactly what B7
    measures.
    """

    need = rendered.x_corollary.get("need")
    if not need:
        return None
    arguments = {
        "questions": [
            {
                "id": need["slot"],
                "header": "protocol",
                "question": need["prompt"],
                "options": [
                    {
                        "label": move_id,
                        "description": (
                            f"take the registered move {move_id!r}; nothing "
                            "else in the session changes"
                        ),
                    }
                    for move_id in need["options"]
                ],
            }
        ]
    }
    return {
        "id": "fc_" + uuid.uuid4().hex,
        "type": "function_call",
        "status": "completed",
        "name": tool["name"],
        # The binding: the host's result must come back on this exact id, and
        # the runtime resumes only the request that minted it.
        "call_id": need["request_id"],
        "arguments": json.dumps(arguments, ensure_ascii=False),
    }


def response_body(
    request: ChatRequest,
    rendered: Rendered,
    usage: dict | None,
    *,
    response_id: str | None = None,
    function_call: dict | None = None,
    admitted_tools: list | None = None,
    tool_choice: str | None = None,
) -> dict:
    """§6 Responses representation of the same completed engine turn."""

    part = {
        "type": "output_text",
        "text": rendered.content,
        "annotations": [],
        "logprobs": [],
    }
    item = {
        "id": "msg_" + uuid.uuid4().hex,
        "type": "message",
        "status": "completed",
        "role": "assistant",
        "content": [part],
    }
    protocol = request.model == PROTOCOL_MODEL
    body = {
        "id": response_id or _response_id(),
        "object": "response",
        "created_at": int(time.time()),
        "status": "completed",
        "error": None,
        "incomplete_details": None,
        "model": request.model,
        "output": [function_call] if function_call is not None else [item],
        # ¶AMD-3: false on the protocol profile, where it AGREES with the
        # catalog's `supports_parallel_tool_calls: false` because the profile
        # emits at most one call. The two shipped profiles keep the value
        # they shipped with, contradiction and all — repairing that is out of
        # this slice's scope, and copying it onto the new profile was the
        # thing the design forbade.
        "parallel_tool_calls": not protocol,
        "tool_choice": (
            tool_choice
            if protocol and isinstance(tool_choice, str) and tool_choice
            else "auto"
        ),
        "tools": list(admitted_tools or []),
        "x_corollary": rendered.x_corollary,
    }
    mapped_usage = _response_usage(usage)
    if mapped_usage is not None:
        body["usage"] = mapped_usage
    return body


def response_events(body: dict) -> list[tuple[str, dict]]:
    """§8 named Responses SSE lifecycle, with one exact text delta.

    ¶AMD-3 adds the second shape: when the one output item is the protocol
    profile's `function_call`, the lifecycle is the function-call one —
    created, output-item added (empty arguments), one arguments delta,
    arguments done, output-item done, completed. There are no content-part
    events, because a function-call item has no content parts; inventing a
    text part around it would be exactly the synthetic item §8 refuses.
    """

    completed_item = body["output"][0]
    created = {**body, "status": "in_progress", "output": []}
    created.pop("usage", None)
    if completed_item["type"] == "function_call":
        return _sequenced(_function_call_events(body, created, completed_item))
    completed_part = completed_item["content"][0]
    in_progress_item = {**completed_item, "status": "in_progress", "content": []}
    empty_part = {**completed_part, "text": ""}
    raw = [
        ("response.created", {"response": created}),
        (
            "response.output_item.added",
            {"output_index": 0, "item": in_progress_item},
        ),
        (
            "response.content_part.added",
            {"output_index": 0, "content_index": 0, "part": empty_part},
        ),
        (
            "response.output_text.delta",
            {
                "output_index": 0,
                "content_index": 0,
                "item_id": completed_item["id"],
                "delta": completed_part["text"],
                "logprobs": [],
            },
        ),
        (
            "response.output_text.done",
            {
                "output_index": 0,
                "content_index": 0,
                "item_id": completed_item["id"],
                "text": completed_part["text"],
                "logprobs": [],
            },
        ),
        (
            "response.content_part.done",
            {"output_index": 0, "content_index": 0, "part": completed_part},
        ),
        ("response.output_item.done", {"output_index": 0, "item": completed_item}),
        ("response.completed", {"response": body}),
    ]
    return _sequenced(raw)


def _sequenced(raw: list[tuple[str, dict]]) -> list[tuple[str, dict]]:
    return [
        (name, {"type": name, "sequence_number": sequence, **payload})
        for sequence, (name, payload) in enumerate(raw)
    ]


def _function_call_events(
    body: dict, created: dict, completed_item: dict
) -> list[tuple[str, dict]]:
    """¶AMD-3's §8 lifecycle for the one function-call item this skin emits."""

    in_progress_item = {**completed_item, "status": "in_progress", "arguments": ""}
    return [
        ("response.created", {"response": created}),
        (
            "response.output_item.added",
            {"output_index": 0, "item": in_progress_item},
        ),
        (
            "response.function_call_arguments.delta",
            {
                "output_index": 0,
                "item_id": completed_item["id"],
                "delta": completed_item["arguments"],
            },
        ),
        (
            "response.function_call_arguments.done",
            {
                "output_index": 0,
                "item_id": completed_item["id"],
                "arguments": completed_item["arguments"],
            },
        ),
        ("response.output_item.done", {"output_index": 0, "item": completed_item}),
        ("response.completed", {"response": body}),
    ]


# --------------------------------------------------------------------------
# The HTTP surface (§2)
# --------------------------------------------------------------------------


class ChatHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "corollary-skin/1"
    sys_version = ""

    #: Set by :func:`build_server`.
    engine: ChatEngine = None  # type: ignore[assignment]
    verbose: bool = False

    def log_message(self, fmt, *args) -> None:  # noqa: A003
        if self.verbose:
            super().log_message(fmt, *args)

    # -- plumbing ---------------------------------------------------------

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_object(self, error: ApiError) -> None:
        self._send_json(error.status, error.body())

    def _not_found(self, path: str) -> None:
        self._send_error_object(
            ApiError(
                404,
                f"unknown path {path!r}; this server serves "
                "/v1/chat/completions, /v1/responses, /v1/models and "
                "/v1/capabilities",
                "not_found",
            )
        )

    def _read_body(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise ApiError(
                400, "invalid Content-Length", "invalid_body"
            ) from None
        if length < 0:
            # A negative length is not a short read; `rfile.read(-1)` would
            # block on the socket until the client hung up, so it is refused
            # by name rather than waited on.
            raise ApiError(
                400, f"negative Content-Length: {length}", "invalid_body"
            )
        if length > MAX_BODY_BYTES:
            raise ApiError(
                400,
                f"request body of {length} bytes exceeds the "
                f"{MAX_BODY_BYTES}-byte limit",
                "body_too_large",
            )
        raw = self.rfile.read(length) if length else b""
        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise ApiError(400, f"malformed JSON body: {exc}", "invalid_body") from None

    # -- routes -----------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        try:
            if path == "/v1/models":
                self._send_json(200, self.engine.model_list())
            elif path == "/v1/capabilities":
                self._send_json(200, self.engine.capability_sheet())
            else:
                self._not_found(self.path)
        except RuntimeError as exc:
            # A build-time P-IH3 refusal. It is served as a refusal rather
            # than as a traceback, and it is a 500 because the fault is this
            # server's, not the client's — the sheet it was asked for is one
            # this repository will not publish.
            self._send_error_object(
                ApiError(
                    500,
                    str(exc),
                    "capability_sheet_refused",
                    error_type="server_error",
                )
            )

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path not in {"/v1/chat/completions", "/v1/responses"}:
            self._not_found(self.path)
            return
        try:
            body = self._read_body()
            if path == "/v1/chat/completions":
                request = ChatRequest(body)
            else:
                responses_request = ResponsesRequest(body, self.engine)
                request = responses_request.chat
            rendered = self.engine.serve(request)
        except ApiError as error:
            self._send_error_object(error)
            return
        usage = self.engine.tokens.usage(request.prompt_text, rendered.content)
        if path == "/v1/responses":
            response_id = _response_id()
            # ¶AMD-3. Only a digest-exact registered tool, only on the
            # protocol profile, and only for a need this turn actually
            # opened; every other combination is the text WAITING fallback
            # with `x_corollary.need`, unchanged.
            tool = responses_request.prompt_tool
            call = prompt_call_item(rendered, tool) if tool is not None else None
            response = response_body(
                request,
                rendered,
                usage,
                response_id=response_id,
                function_call=call,
                admitted_tools=responses_request.admitted_tools,
                tool_choice=responses_request.tool_choice,
            )
            self.engine.remember_response(response_id, request, rendered)
            if responses_request.stream:
                self._send_response_stream(response_events(response))
            else:
                self._send_json(200, response)
        elif request.stream:
            self._send_stream(stream_chunks(request, rendered, usage))
        else:
            self._send_json(200, completion_body(request, rendered, usage))

    def _send_stream(self, chunks: list[dict]) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        try:
            for chunk in chunks:
                self._write_chunk(
                    f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n".encode(
                        "utf-8"
                    )
                )
            self._write_chunk(b"data: [DONE]\n\n")
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionError, OSError):
            # A stock client that has read `[DONE]` may hang up before the
            # terminating zero-length chunk arrives. The turn is already
            # delivered in full, so this is a closed socket, not a failure to
            # answer; keeping the connection is what would be wrong.
            self.close_connection = True

    def _send_response_stream(self, events: list[tuple[str, dict]]) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Transfer-Encoding", "chunked")
        self.end_headers()
        try:
            for name, event in events:
                payload = (
                    f"event: {name}\n"
                    f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                ).encode("utf-8")
                self._write_chunk(payload)
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionError, OSError):
            self.close_connection = True

    def _write_chunk(self, payload: bytes) -> None:
        self.wfile.write(f"{len(payload):X}\r\n".encode("ascii"))
        self.wfile.write(payload)
        self.wfile.write(b"\r\n")


class SkinServer(ThreadingHTTPServer):
    """`ThreadingHTTPServer`, minus the traceback for a client that hung up.

    A stock client that has read `[DONE]` closes its socket without waiting
    for the terminating chunk, and a reset connection is not a server error.
    Everything else still surfaces: swallowing a real handler exception would
    turn a broken route into a silent one.
    """

    daemon_threads = True

    #: Set by :func:`build_server` so `server_close` can stop the refill thread.
    engine: ChatEngine | None = None

    def handle_error(self, request, client_address) -> None:
        if isinstance(sys.exc_info()[1], (ConnectionError, BrokenPipeError)):
            return
        super().handle_error(request, client_address)

    def server_close(self) -> None:
        if self.engine is not None:
            self.engine.shutdown()
        super().server_close()


def build_server(
    repo_root: Path | None = None,
    port: int = DEFAULT_PORT,
    *,
    verbose: bool = False,
    prewarm: bool = True,
    pool_size: int = DEFAULT_POOL_SIZE,
) -> tuple[SkinServer, ChatEngine]:
    """A bound, warmed server plus its engine. Caller owns `serve_forever`.

    `pool_size=0` disables the pre-booted session pool, which is what the
    equivalence test's cold arm runs; the served bytes must not change.
    """

    engine = ChatEngine(repo_root or REPO, pool_size=pool_size)
    if prewarm:
        engine.prewarm()

    class _Handler(ChatHandler):
        pass

    _Handler.engine = engine
    _Handler.verbose = verbose
    server = SkinServer((HOST, port), _Handler)
    server.engine = engine
    return server, engine


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Serve the corollary session engine as an OpenAI-compatible "
            "chat-completions subset (docs/SPEC-chat-completions-skin.md)."
        ),
        epilog=(
            "Startup pre-warms (spec A11): one kernel session is booted and "
            "one throwaway free-text line is routed so the resolver's graph "
            "index is built before the first request, and a background "
            "thread then keeps --pool-size sessions booted so no request "
            "pays the ~415 ms boot. Both contenders are "
            "warm before a registered run - the baseline manifest "
            f"({BASELINE_MANIFEST}) requires one unmeasured warmup request "
            "per system, so start this server and let it warm before timing "
            "anything. Replay only: no durable session is resumed over HTTP."
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"loopback port to bind (default {DEFAULT_PORT}); the bind "
        f"address is always {HOST}",
    )
    parser.add_argument(
        "--no-prewarm",
        action="store_true",
        help="skip the A11 warm-up (the first request then pays for it)",
    )
    parser.add_argument(
        "--pool-size",
        type=int,
        default=DEFAULT_POOL_SIZE,
        help=f"pre-booted kernel sessions kept ready off the request path "
        f"(default {DEFAULT_POOL_SIZE}, ~27 MB each); 0 boots every request "
        f"on demand",
    )
    parser.add_argument(
        "--no-pool",
        action="store_true",
        help="equivalent to --pool-size 0; the served bytes are identical "
        "either way, only the wall clock differs",
    )
    parser.add_argument("--verbose", action="store_true", help="log every request")
    args = parser.parse_args(argv)

    server, engine = build_server(
        REPO,
        args.port,
        verbose=args.verbose,
        prewarm=not args.no_prewarm,
        pool_size=0 if args.no_pool else args.pool_size,
    )
    matrix = engine.matrix
    print(f"corollary chat skin on http://{HOST}:{server.server_port}/v1")
    for line in matrix.render():
        print(line)
    print(f"usage block: {engine.tokens.reason}")
    print(
        f"session pool: {engine.pool.size} pre-booted"
        if engine.pool.running
        else "session pool: off (every request boots on demand)"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
