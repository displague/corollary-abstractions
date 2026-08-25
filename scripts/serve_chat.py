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
from session_keys import SessionKeyRing  # noqa: E402

# --------------------------------------------------------------------------
# Constants the spec freezes
# --------------------------------------------------------------------------

#: §2. Loopback only. Not a flag: a multi-tenant bind would be a scope this
#: cycle has not paid for.
HOST = "127.0.0.1"
DEFAULT_PORT = 8377

CHAT_SCHEMA = "corollary.chat/1"
CAPABILITIES_SCHEMA = "corollary.capabilities/1"

KERNEL_MODEL = "corollary/kernel"
CONVERSATION_MODEL = "corollary/conversation"

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
)
WRITE_GATE_STATUSES = ("PROVEN", "VERIFIED", "REFUSED")
SKIN_ASSIGNED_STATUSES = ("abstained",)

#: §6.1's answered? axis. Every other status in the frozen alphabet is
#: non-answering and carries no grounding claim — with the two named `closure`
#: exceptions, which :func:`_receipt` handles before this set is consulted.
ANSWERING_STATUSES = frozenset({"solved", "found", "held", "PROVEN", "VERIFIED"})

#: The pinned-baseline manifest the tokenizer digest is READ from (never
#: hardcoded here: a second copy of a digest is a second thing to rot).
BASELINE_MANIFEST = "experiments/throughput_baseline.json"

#: The ONE registered realization run (DESIGN-sans-template-rendering §10).
#: The capability sheet quotes R1 from THIS file rather than from a number
#: pasted into this module: a rate that can go stale in a docstring is a rate
#: that will, and the sheet is generated from live artifacts by §7's rule.
REALIZATION_RUN = "experiments/realization_rate.json"

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
#: (`harness.py:1393-1437`). `requires` is what makes `served` a *live* flag
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
        "statuses": ["refused"],
        "requires": ("tool.conform",),
        "note": (
            "DESIGN-statements-that-run §5's wiring step, landed with "
            "ROADMAP-v0.20 §4's retirement so item 1's slice need not retouch "
            "harness.py. The compiler (scripts/conform.py) is not built, so "
            "the route refuses by name — published `served: false` on §7's "
            "rule rather than hidden, because a registered line that is not "
            "yet answerable is a different fact from an unregistered one"
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
}

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


def prefix_hash(prefix: list[tuple[str, str]]) -> str:
    """§4.1. sha256 over canonical-JSON/compact of ``[[role, content], …]``."""

    return hashlib.sha256(
        canonical_bytes([[role, content] for role, content in prefix])
    ).hexdigest()


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
    lines (`harness.py:1219-1228`), so the skin must too; adding, dropping,
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

    def __init__(self, body: dict) -> None:
        if not isinstance(body, dict):
            raise ApiError(400, "request body must be a JSON object", "invalid_body")

        model = body.get("model")
        if not isinstance(model, str) or not model:
            raise ApiError(
                400, "'model' is required and must be a string", "missing_model",
                param="model",
            )
        if model not in (KERNEL_MODEL, CONVERSATION_MODEL):
            raise ApiError(
                404,
                f"model {model!r} does not exist; this server serves "
                f"{KERNEL_MODEL!r} and {CONVERSATION_MODEL!r}",
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
        self.messages: list[tuple[str, str]] = []
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
        self.final_user_index = user_indices[-1]
        self.final_user_content = self.messages[self.final_user_index][1]

        # §4: sampling parameters (and anything else this skin does not act
        # on) are accepted, ignored, and listed. Keys this server *enforces*
        # are excluded: see :data:`ENFORCED_BODY_KEYS`.
        ignored.extend(
            sorted(
                key
                for key in body
                if key not in HANDLED_BODY_KEYS and key not in ENFORCED_BODY_KEYS
            )
        )
        self.ignored = ignored

        self.prefix = self.messages[: self.final_user_index]
        self.prefix_hash = prefix_hash(self.prefix)
        self.tail = self.messages[self.final_user_index + 1 :]

        self.stream = bool(body.get("stream"))
        options = body.get("stream_options")
        self.include_usage = bool(
            isinstance(options, dict) and options.get("include_usage")
        )
        self.prompt_text = "\n".join(content for _role, content in self.messages)

    def next_prefix_hash(self, content: str) -> str:
        """The prefix hash of the transcript a client continuing from here sends."""

        return prefix_hash(
            [
                *self.prefix,
                ("user", self.final_user_content),
                ("assistant", content),
            ]
        )


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
        self._lock = threading.Lock()
        self._cache: "OrderedDict[str, _CacheEntry]" = OrderedDict()
        self._cache_size = cache_size
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

    def _fresh(self, model: str, request: ChatRequest):
        if model == KERNEL_MODEL:
            return self._kernel_session(request.prefix_hash)
        return self._conversation_session(request.prefix_hash)

    def _render(
        self, model: str, session, line: str, *, with_receipt: bool = True
    ) -> Rendered:
        if model == KERNEL_MODEL:
            return render_kernel_turn(
                self.repo_root, session, line, with_receipt=with_receipt
            )
        try:
            return render_conversation_turn(session, line)
        except ValueError as exc:
            # §10: the engine's own message, under a code distinct from
            # transcript_divergence so a client can tell them apart.
            raise ApiError(409, str(exc), "slot_conflict", param="messages") from None

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

        rendered = self._render(request.model, session, request.final_user_content)

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
            if role == "user":
                last_produced = self._render(
                    request.model, session, content, with_receipt=False
                ).content
            elif role == "assistant":
                _check_divergence(content, last_produced)

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
            "realization": realization_row(str(self.repo_root)),
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

    def model_list(self) -> dict:
        models = {
            "object": "list",
            "data": [
                {
                    "id": model,
                    "object": "model",
                    "created": self.created,
                    "owned_by": "corollary",
                    "description": PROFILE_DESCRIPTIONS[model],
                }
                for model in (KERNEL_MODEL, CONVERSATION_MODEL)
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
                "/v1/chat/completions, /v1/models and /v1/capabilities",
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
        if path != "/v1/chat/completions":
            self._not_found(self.path)
            return
        try:
            body = self._read_body()
            request = ChatRequest(body)
            rendered = self.engine.serve(request)
        except ApiError as error:
            self._send_error_object(error)
            return
        usage = self.engine.tokens.usage(request.prompt_text, rendered.content)
        if request.stream:
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
