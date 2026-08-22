#!/usr/bin/env python3
"""C1, the dump server: raw bandwidth incarnate, wearing the right protocol.

`docs/DESIGN-grounded-throughput.md` §7 defines the control and its voiding
sentence:

> **C1 -- the dump server.** A server that streams corpus text at maximum
> rate, ignoring the query: raw bandwidth incarnate, and under a correct
> metric it scores approximately zero. *If C1's perceived throughput exceeds
> 1% of the kernel's, the metric as implemented is crediting bandwidth, and
> the metric is void.* (The clause guards the implementation of the
> denominator, which is where a metric quietly rots; a C1 score of zero is
> the expected reading, not a vacuous one, because the same scoring code
> produced it.)

"the same scoring code produced it" is the whole design constraint on this
file: the stopwatch must consume it **without special-casing**, so the
responses have to be protocol-valid in the shape SPEC §8 fixes -- SSE chunks
in the OpenAI chunk shape, every chunk after the first carrying its leading
newline, `finish_reason: "stop"` on the last, `x_corollary` riding on it.

The one judgment this file makes, recorded rather than hidden: the dump
claims `x_corollary.status = "found"`. It could claim nothing and be rejected
on a missing status field, which would make C1 a test of the status check and
nothing else. Claiming the most common answering status makes the control
tighter: it forces the **content and receipt** assertions to be what drives
C1's score to zero. The dump does not fake a receipt -- that is C2's job,
where the receipts are real and attached to the wrong question -- and it
names itself in `profile` and `route`, because a control that lies about
what it is measures the reader, not the metric.

Nothing here imports an engine module; like the stopwatch, this process is a
stranger to the serving path. It reads one committed corpus file as data.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterator

REPO = Path(__file__).resolve().parents[1]

MODEL_ID = "control/dump"
DEFAULT_CORPUS = "data/logic/nodes.json"
DEFAULT_PORT = 8123

#: Bytes per SSE chunk. Chunk boundaries in the real skin are rendered lines
#: (SPEC §8); the dump has no lines, so it slices, which is the fastest thing
#: a streamer can do and exactly the behaviour C1 is meant to represent.
CHUNK_CHARS = 512


def prose_of(value: object) -> Iterator[str]:
    """Every string leaf of a committed corpus record, in document order.

    "streams corpus text" (§7). Titles, meanings, scope notes, expressions:
    the person-authored prose the kernel copies from is exactly this text,
    which is what makes the control adversarial rather than a noise generator
    -- the dump is emitting the very sentences a correct answer would.
    """

    if isinstance(value, dict):
        for key in value:
            yield from prose_of(value[key])
    elif isinstance(value, list):
        for item in value:
            yield from prose_of(item)
    elif isinstance(value, str):
        yield value


def load_payload(corpus: Path) -> str:
    document = json.loads(corpus.read_text(encoding="utf-8"))
    return "\n".join(prose_of(document))


def chunk_shape(created: int, delta: dict, finish: str | None = None) -> dict:
    return {
        "id": "chatcmpl-control-dump",
        "object": "chat.completion.chunk",
        "created": created,
        "model": MODEL_ID,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
    }


class DumpHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    payload = ""
    corpus_name = DEFAULT_CORPUS
    quiet = True

    def log_message(self, fmt: str, *args) -> None:  # noqa: D102
        if not self.quiet:
            super().log_message(fmt, *args)

    # -- helpers ---------------------------------------------------------

    def _json(self, status: int, body: dict) -> None:
        blob = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(blob)))
        self.end_headers()
        self.wfile.write(blob)

    def _error(self, status: int, message: str, code: str) -> None:
        self._json(
            status,
            {"error": {"message": message, "type": "invalid_request_error",
                       "code": code}},
        )

    def _sse(self, chunk: dict) -> None:
        self.wfile.write(b"data: ")
        self.wfile.write(json.dumps(chunk, ensure_ascii=False).encode("utf-8"))
        self.wfile.write(b"\n\n")

    # -- routes ----------------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/v1/models":
            self._json(
                200,
                {
                    "object": "list",
                    "data": [
                        {
                            "id": MODEL_ID,
                            "object": "model",
                            "owned_by": "corollary-abstractions",
                            "description": (
                                "C1 blind control: streams committed corpus "
                                "text at maximum rate and ignores the query"
                            ),
                        }
                    ],
                },
            )
            return
        self._error(404, f"no such path: {self.path}", "not_found")

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/v1/chat/completions":
            self._error(404, f"no such path: {self.path}", "not_found")
            return

        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            request = json.loads(raw.decode("utf-8") or "{}")
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._error(400, "body is not JSON", "invalid_body")
            return
        # The query is read only far enough to answer the stream question,
        # and then discarded: "ignoring the query" is the control.
        streaming = bool(request.get("stream"))

        created = int(time.time())
        text = self.payload
        extension = {
            "schema": "corollary.chat/1",
            "profile": MODEL_ID,
            "route": "control/dump",
            "status": "found",
            "detail": (
                f"C1 blind control: {self.corpus_name} streamed at maximum "
                "rate; the query was not read"
            ),
            "evidence": [],
            "receipt": {},
            "ignored": ["messages", "temperature", "top_p", "top_k"],
            "session": {"profile_session_id": "control-dump"},
        }

        if not streaming:
            self._json(
                200,
                {
                    "id": "chatcmpl-control-dump",
                    "object": "chat.completion",
                    "created": created,
                    "model": MODEL_ID,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": text},
                            "finish_reason": "stop",
                        }
                    ],
                    "x_corollary": extension,
                },
            )
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()

        self._sse(chunk_shape(created, {"role": "assistant", "content": ""}))
        for start in range(0, len(text), CHUNK_CHARS):
            self._sse(
                chunk_shape(created, {"content": text[start:start + CHUNK_CHARS]})
            )
        final = chunk_shape(created, {}, finish="stop")
        final["x_corollary"] = extension
        self._sse(final)
        self.wfile.write(b"data: [DONE]\n\n")
        self.close_connection = True


def serve(corpus: Path, host: str, port: int, quiet: bool) -> None:
    DumpHandler.payload = load_payload(corpus)
    try:
        DumpHandler.corpus_name = str(corpus.relative_to(REPO))
    except ValueError:
        DumpHandler.corpus_name = str(corpus)
    DumpHandler.quiet = quiet
    server = ThreadingHTTPServer((host, port), DumpHandler)
    print(
        f"C1 dump server on http://{host}:{port} "
        f"({DumpHandler.corpus_name}, {len(DumpHandler.payload)} chars)",
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="dump_server.py",
        description=(
            "DESIGN-grounded-throughput §7's C1 control: an OpenAI-compatible "
            "endpoint that streams committed corpus text at maximum rate and "
            "ignores the query."
        ),
    )
    parser.add_argument("--corpus", default=DEFAULT_CORPUS)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    corpus = Path(args.corpus)
    corpus = corpus if corpus.is_absolute() else REPO / corpus
    if not corpus.is_file():
        print(f"no such corpus file: {corpus}", file=sys.stderr)
        return 2
    if args.host != "127.0.0.1":
        # The substrate's shipped contract is one owner, no auth (SPEC §2);
        # a control server that binds a public interface would be a new
        # surface nobody registered.
        print(
            "refused: the control binds 127.0.0.1 only (SPEC §2, no auth)",
            file=sys.stderr,
        )
        return 2
    serve(corpus, args.host, args.port, quiet=not args.verbose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
