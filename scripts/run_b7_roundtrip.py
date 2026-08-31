#!/usr/bin/env python3
"""B7's instrument: the tool-wire round trip, self-checked, then recorded.

`docs/DESIGN-protocol-uptake.md` §7 B7 is the one gate this repository cannot
score from its own code: *"an unmodified Codex CLI must complete: function-call
item -> host result -> function-call-output input -> exact request resume"*,
served on `corollary/protocol`. Only a live host can answer that. What this
script owns is everything around the live run — the wire shapes, the refusal
to write a verdict nothing measured, and the artifact the gates runner reads.

Two arms, and the difference between them is the whole point
--------------------------------------------------------------

**The self-check arm (default).** Starts `serve_chat` on ``--port`` and drives
ONE scripted HTTP round trip against it, asserting the wire shapes AMD-3
defines: a request advertising the registered prompt tool gets exactly one
`function_call` output item; its `call_id` is the pending `request_id`; its
arguments follow the capture's `mapping_to_need`; a `function_call_output`
carrying that `call_id` resumes the **exact** request and selects the named
move; and a stale `call_id` is refused with the session still WAITING. This
proves the server's half of B7 and **writes nothing**.

It has one honest limitation, stated here rather than buried: U-P1's capture
records the installed host's `request_user_input` **digest** and deliberately
keeps the raw request outside the repository, so nothing in this tree can
build a schema hashing to `23ee6f1a…`. The self-check therefore registers a
**stand-in** schema digest through `serve_chat.register_prompt_tool`, with a
provenance saying exactly that — and the served capability sheet publishes it,
so a reader can always tell a stand-in registration from the captured one.
A green self-check is a statement about this server, never about a host.

**The live arm (`--live-codex-log PATH --verdict …`).** The orchestrator runs
the unmodified `codex.cmd` against `corollary/protocol` and hands this script
the log. The script validates and records; it does not run Codex and it does
not invent a verdict. `--verdict GREEN` is **refused** unless the self-check
passed and the log actually mentions the registered tool name and a
`function_call_output`; `RED` and `UNTESTED` are recorded as given, with the
log's digest beside them. The artifact is written to
`experiments/protocol_uptake_b7.json`, which `scripts/run_protocol_gates.py`
reads in place of `PENDING_AMD3`; an existing output path is refused rather
than overwritten, following the gates runner's own write-once rule.

Usage
-----

    # the wire shapes, against a server this script starts and stops
    python scripts/run_b7_roundtrip.py --port 8378

    # the orchestrator, after its live codex.cmd run
    python scripts/run_b7_roundtrip.py --port 8378 \
        --live-codex-log reports/b7-codex-session.log --verdict GREEN

    # what the durable README command becomes for this gate: `-m` switched
    #   codex.cmd exec ... -m corollary/protocol ...

Exit status is 0 only when every requested arm passed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Sequence

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

import serve_chat  # noqa: E402

ARTIFACT = "experiments/protocol_uptake_b7.json"
HOST_CAPTURE = "experiments/protocol_uptake_host_capture.json"
DESIGN = "docs/DESIGN-protocol-uptake.md"
SPEC = "docs/SPEC-chat-completions-skin.md"
SCHEMA = "corollary.protocol-uptake-b7/1"

#: The ambiguous surface: two corpus-witnessed greeting protocols hold at a
#: fresh root and their next states differ, so the verifier opens one signed
#: request and stops WAITING. That is the ASK B7 needs, and it comes from the
#: sealed corpus rather than from a flag.
AMBIGUOUS_SURFACE = "hi"

#: The stand-in schema. Shaped after the capture's `shape` note so the wire
#: carries something plausible, but its DIGEST is what matters and its digest
#: is not the captured one — see the module docstring.
STAND_IN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["questions"],
    "properties": {
        "questions": {
            "type": "array",
            "minItems": 1,
            "maxItems": 3,
            "items": {
                "type": "object",
                "required": ["id", "header", "question", "options"],
                "properties": {
                    "id": {"type": "string"},
                    "header": {"type": "string"},
                    "question": {"type": "string"},
                    "options": {"type": "array"},
                },
            },
        }
    },
}

STAND_IN_PROVENANCE = (
    "scripts/run_b7_roundtrip.py self-check stand-in: U-P1's capture records "
    "the installed host's schema DIGEST and keeps the raw request outside "
    "this repository, so no in-tree schema can hash to it. This registration "
    "exercises the adapter's code path and attests nothing about a host."
)


class SelfCheckFailure(RuntimeError):
    """A wire shape this server got wrong. Never a host's verdict."""


# --------------------------------------------------------------------------
# HTTP, stdlib only — the server under test is stdlib only too.
# --------------------------------------------------------------------------


def post(base_url: str, path: str, payload: dict) -> tuple[int, dict]:
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SelfCheckFailure(message)


# --------------------------------------------------------------------------
# The scripted round trip.
# --------------------------------------------------------------------------


def self_check(base_url: str, tool_declaration: dict) -> dict[str, Any]:
    """One scripted round trip of exactly the wire shapes B7 names."""

    steps: list[dict[str, Any]] = []
    tools = [tool_declaration]

    status, ask = post(
        base_url,
        "/responses",
        {
            "model": serve_chat.PROTOCOL_MODEL,
            "input": AMBIGUOUS_SURFACE,
            "tools": tools,
            "tool_choice": "auto",
            "parallel_tool_calls": True,
            "store": False,
            "stream": False,
        },
    )
    require(status == 200, f"the ASK request returned {status}: {ask}")
    require(len(ask["output"]) == 1, "an ASK must emit exactly one output item")
    item = ask["output"][0]
    require(
        item["type"] == "function_call",
        f"the registered tool was advertised but the item is {item['type']!r}",
    )
    require(
        item["name"] == tool_declaration["name"],
        f"the emitted call names {item['name']!r}",
    )
    need = ask["x_corollary"]["need"]
    require(
        item["call_id"] == need["request_id"],
        "call_id must be the pending request_id",
    )
    arguments = json.loads(item["arguments"])
    question = arguments["questions"][0]
    require(len(arguments["questions"]) == 1, "the mapping is ONE question")
    require(question["id"] == need["slot"], "questions[0].id is the need's slot")
    require(question["header"] == "protocol", "questions[0].header is 'protocol'")
    require(
        question["question"] == need["prompt"],
        "questions[0].question is the minted prompt",
    )
    require(
        [option["label"] for option in question["options"]] == need["options"],
        "options are the unresolved candidate move ids, canonical order",
    )
    require(
        ask["parallel_tool_calls"] is False,
        "this profile emits at most one call and must publish so",
    )
    for handled in ("tools", "tool_choice"):
        require(
            handled not in ask["x_corollary"]["ignored"],
            f"{handled} is acted on here and must not be called ignored",
        )
    chosen = need["options"][0]
    steps.append(
        {
            "step": "function_call item",
            "call_id": item["call_id"],
            "options": need["options"],
            "ok": True,
        }
    )

    # A stale call_id binds nothing, and the session stays WAITING.
    status, stale = post(
        base_url,
        "/responses",
        {
            "model": serve_chat.PROTOCOL_MODEL,
            "previous_response_id": ask["id"],
            "input": [
                {
                    "type": "function_call_output",
                    "call_id": "not-a-request-id",
                    "output": chosen,
                }
            ],
            "tools": tools,
            "stream": False,
        },
    )
    require(status == 200, f"the stale-result request returned {status}: {stale}")
    require(
        stale["x_corollary"]["status"] == "refused",
        "a stale call_id must be refused",
    )
    require(
        stale["x_corollary"]["uptake"]["selected_move_id"] is None,
        "a refused result may select no move",
    )
    require(
        stale["x_corollary"]["uptake"]["stack_after"] == [],
        "a refused result may not mutate the stack",
    )
    steps.append({"step": "stale call_id refused", "ok": True})

    # The exact request resumes.
    status, resumed = post(
        base_url,
        "/responses",
        {
            "model": serve_chat.PROTOCOL_MODEL,
            "previous_response_id": ask["id"],
            "input": [
                {
                    "type": "function_call_output",
                    "call_id": item["call_id"],
                    "output": chosen,
                }
            ],
            "tools": tools,
            "stream": False,
        },
    )
    require(status == 200, f"the resume request returned {status}: {resumed}")
    uptake = resumed["x_corollary"]["uptake"]
    require(
        resumed["x_corollary"]["status"] == "found",
        f"the resume did not admit a transition: {resumed['x_corollary']}",
    )
    require(
        uptake["selected_move_id"] == chosen,
        f"the resume selected {uptake['selected_move_id']!r}, not {chosen!r}",
    )
    require(
        f"bound_request:{item['call_id']}" in uptake["verifier_evidence"],
        "the receipt must name the request it bound",
    )
    require(uptake["authority_delta"] == [], "no protocol move opens an authority")
    steps.append(
        {
            "step": "function_call_output resumed the exact request",
            "selected_move_id": uptake["selected_move_id"],
            "uptake_id": uptake["uptake_id"],
            "ok": True,
        }
    )
    return {
        "passed": True,
        "surface": AMBIGUOUS_SURFACE,
        "profile": serve_chat.PROTOCOL_MODEL,
        "steps": steps,
        "registration": dict(
            serve_chat.PROMPT_TOOL_ADAPTERS[tool_declaration["name"]]
        ),
        "attests": (
            "the server's half of B7: the AMD-3 wire shapes over loopback. It "
            "attests nothing about the installed host, because the schema "
            "digest registered here is a stand-in."
        ),
    }


# --------------------------------------------------------------------------
# The live arm: validate and record. It never runs Codex.
# --------------------------------------------------------------------------


def read_log(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    capture, _error = serve_chat._read_json(REPO / HOST_CAPTURE)
    tool_name = (capture or {}).get("prompt_tool", {}).get("name", "")
    return {
        "path": str(path),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "mentions_prompt_tool": bool(tool_name) and tool_name in text,
        "mentions_function_call_output": "function_call_output" in text,
        "mentions_protocol_profile": serve_chat.PROTOCOL_MODEL in text,
        "scan_note": (
            "a mechanical scan of the operator-supplied log, not a parse of a "
            "format this repository controls. It can refuse a GREEN verdict; "
            "it cannot license one on its own."
        ),
    }


def artifact(
    verdict: str, check: dict[str, Any], log: dict[str, Any] | None, why: str
) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "gate": "B7",
        "design": DESIGN,
        "design_clause": (
            "§7 B7 — tool-wire round trip: function-call item -> host result "
            "-> function-call-output input -> exact request resume, served on "
            "corollary/protocol"
        ),
        "spec": SPEC,
        "spec_clause": "¶AMD-3 (§4.2, §8)",
        "instrument": "scripts/run_b7_roundtrip.py",
        "profile": serve_chat.PROTOCOL_MODEL,
        "verdict": verdict,
        "green": verdict == "GREEN",
        "why": why,
        "self_check": check,
        "live_codex_log": log,
        "host_capture": HOST_CAPTURE,
        "non_claims": [
            "a green self-check is not B7: §7 forbids reporting B7 green from "
            "anything but a live host round trip",
            "the text WAITING fallback cannot license B7 or R-U2",
        ],
    }


def write_once(path: Path, payload: dict[str, Any]) -> None:
    if path.exists():
        raise RuntimeError(
            f"{path} already exists; this writer refuses an existing output "
            "path so a recorded verdict cannot be quietly replaced"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


# --------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help="loopback port for the server this script starts (0 = ephemeral)",
    )
    parser.add_argument(
        "--live-codex-log",
        type=Path,
        help="the unmodified codex.cmd session log the orchestrator captured",
    )
    parser.add_argument(
        "--verdict",
        choices=("GREEN", "RED", "UNTESTED"),
        help="the live arm's verdict; required with --live-codex-log",
    )
    parser.add_argument("--out", type=Path, default=REPO / ARTIFACT)
    args = parser.parse_args(argv)

    if args.live_codex_log and not args.verdict:
        parser.error("--live-codex-log requires --verdict")
    if args.verdict and not args.live_codex_log:
        parser.error("--verdict requires --live-codex-log; nothing else measures B7")

    declaration = {
        "type": "function",
        "name": "request_user_input",
        "description": "ask the person a structured question",
        "parameters": STAND_IN_SCHEMA,
    }

    server, engine = serve_chat.build_server(REPO, args.port, pool_size=0)
    # AFTER the engine, deliberately: building one registers the adapter U-P1
    # captured, under the captured tool's own name. The stand-in replaces it
    # for this process only, and the served capability sheet publishes the
    # substituted provenance so the swap is visible rather than silent.
    serve_chat.register_prompt_tool(
        "request_user_input",
        serve_chat.tool_schema_digest(STAND_IN_SCHEMA),
        STAND_IN_PROVENANCE,
    )
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base_url = f"http://{serve_chat.HOST}:{server.server_port}/v1"
    print(f"self-check server on {base_url}")
    try:
        check = self_check(base_url, declaration)
        print("self-check: PASSED")
        for step in check["steps"]:
            print(f"  - {step['step']}")
    except SelfCheckFailure as failure:
        print(f"self-check: FAILED — {failure}", file=sys.stderr)
        check = {"passed": False, "failure": str(failure)}
    finally:
        server.shutdown()
        server.server_close()
        del engine

    if not args.live_codex_log:
        print(
            "\nno --live-codex-log: nothing written. B7 stays PENDING_AMD3 in "
            "the gates run until the orchestrator's live Codex round trip "
            "supplies its log."
        )
        return 0 if check["passed"] else 1

    log = read_log(args.live_codex_log)
    verdict, why = args.verdict, ""
    if not check["passed"]:
        verdict = "RED"
        why = (
            "the server's own wire shapes failed the self-check, so no host "
            f"result could be attributed: {check.get('failure')}"
        )
    elif args.verdict == "GREEN" and not (
        log["mentions_prompt_tool"] and log["mentions_function_call_output"]
    ):
        verdict = "RED"
        why = (
            "GREEN was refused: the supplied log mentions neither the "
            "registered prompt tool nor a function_call_output, so nothing in "
            "it evidences the round trip B7 scores"
        )
    elif args.verdict == "GREEN":
        why = (
            "the unmodified Codex host presented the verifier-approved need as "
            "a structured prompt tool, returned its result, and resumed the "
            "exact pending request; the server's wire shapes are self-checked "
            "and the operator's log evidences the host's half"
        )
    else:
        why = (
            f"recorded as {args.verdict} by the operator who ran the live "
            "round trip; the self-check passed, so the server's half is not "
            "the cause"
        )

    payload = artifact(verdict, check, log, why)
    write_once(args.out, payload)
    print(f"\n{args.out}: B7 {verdict}")
    print(f"  {why}")
    return 0 if verdict == "GREEN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
