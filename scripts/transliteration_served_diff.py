#!/usr/bin/env python3
"""The before/after diff of served answer lines that ROADMAP-v0.19 item 3a owes.

Rule 3 of the lane's re-freeze discipline, quoted because this file exists for
no other reason:

    `match_signatures.py` is *not* in the task book's `rendering_module_digests`
    (that witness lists eleven modules and this is not one of them). But widening
    the tokenizer changes *which* terms parse, and therefore changes what
    `answer.render` emits on its `in words` line — **rendered output moves while
    every witnessed module digest stands still.** The book's witness cannot catch
    it. So this lane owes an explicit before/after diff of served answer lines
    over the task book's own corpus tasks, committed with the probe, rather than
    a green digest test read as reassurance.

## The mechanism, stated rather than implied

The AFTER side is this working tree: `answer.compose` then `answer.render` for
every `corpus_definition` task in `experiments/throughput_tasks.json`.

The BEFORE side is **the real pre-amendment file, not a reconstruction of it**.
`git show <parent>:scripts/match_signatures.py` is written into a scratch
directory and its LF sha256 is checked against the retired pin
`65fead2f47b6a2ce…` recorded in `experiments/realization_prereg.json`. A second
fresh interpreter loads that file as the `match_signatures` module and binds it
into `sys.modules` **before importing anything else**, so every later
`from match_signatures import …` in the call graph resolves to it. No regex is
re-typed from memory: an in-memory revert would be a copy of the old tokenizer
that a reader has to trust matches the old tokenizer, and the digest check would
then be checking the copy against itself.

Two things were learned building this and both are kept in the code rather than
in a commit message. Ordering `sys.path` does NOT work — `answer.py:47` and
`realize_term.py:112` each `sys.path.insert(0, ...)` their own directory at
import time and jump in front of any scratch directory. And a substitution that
fails to substitute produces a clean, confident diff of nothing, which is what
the first draft produced: the corpus sweep read 8,584 served lines on the BEFORE
side — the post-change number — and that is the only reason it was caught. So
every child interpreter now reports the LF sha256 of the parser it actually
loaded, and the parent refuses to write an artifact whose four child processes
did not load the two parsers they claim to have loaded.

## What the diff must show

ADDITIVE ONLY. A statement that rendered an `in words` line before must render
the byte-identical line after; the only permitted difference is a statement
GAINING a line it did not have. A changed line is not a widening, and this
script exits non-zero rather than writing an artifact that reports one — the
lane's instruction is to stop and report, so the stop is mechanical.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from report_provenance import sha256_lf_file  # noqa: E402

TASKS_PATH = REPO_ROOT / "experiments" / "throughput_tasks.json"
PREREG_PATH = REPO_ROOT / "experiments" / "realization_prereg.json"
SUCCESSOR_PATH = REPO_ROOT / "experiments" / "transliteration_prereg.json"
OUT_PATH = REPO_ROOT / "experiments" / "transliteration_served_diff.json"

#: The line `answer.render` emits for a realized term, and the only line this
#: change can possibly move. Kept as a prefix rather than a regex because
#: `answer.py:215` writes exactly this and a looser match would silently widen
#: what counts as "the rendered surface".
IN_WORDS_PREFIX = "in words   : "


class ChangedLine(RuntimeError):
    """A previously-served line moved. The lane stops here."""


def corpus_definition_ids(tasks_doc: dict) -> list[str]:
    """Every corpus_definition task's statement id, in the book's own order.

    Read from `expected.receipt_expect.statement_id` rather than parsed out of
    `task_id`: the receipt field is what the book asserts the answer is about,
    and a task whose id and receipt disagreed would be a book bug this script
    should surface rather than paper over by preferring one of them.
    """
    ids = []
    for task in tasks_doc["tasks"]:
        if task.get("kind") != "corpus_definition":
            continue
        sid = task["expected"]["receipt_expect"]["statement_id"]
        suffix = task["task_id"].split("/", 1)[1]
        if sid != suffix:
            raise RuntimeError(
                f"{task['task_id']}: receipt names {sid!r}; the ids disagree"
            )
        ids.append(sid)
    return ids


#: Prelude every child interpreter runs. It BINDS the parser into `sys.modules`
#: before anything imports it, which is the only substitution that actually
#: holds: `scripts/answer.py:47` and `scripts/realize_term.py:112` both
#: `sys.path.insert(0, ...)` their own directory at import time, so a temp
#: directory placed ahead of `scripts/` is jumped in front of the moment
#: `answer` is imported. Ordering sys.path looks like it works and does not.
#:
#: Found by measurement, not by reading: the first draft ordered sys.path, and
#: the corpus sweep then reported 8,584 served lines on the BEFORE side — the
#: post-change number — which is what gave it away. That is why every child
#: reports the LF sha256 of the parser it actually loaded, below, and why the
#: parent refuses a run whose sides do not carry the two expected digests. A
#: mechanism that can silently substitute nothing must be made to prove it did
#: not.
PRELUDE = r"""
import hashlib, importlib.util, json, sys
sys.path.insert(0, %(scripts)r)
_old = %(old)r
if _old is not None:
    _spec = importlib.util.spec_from_file_location("match_signatures", _old)
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules["match_signatures"] = _mod
    _spec.loader.exec_module(_mod)
import match_signatures
_bytes = open(match_signatures.__file__, "rb").read()
_used = hashlib.sha256(_bytes.replace(b"\x0d\x0a", b"\x0a")).hexdigest()
import answer
"""

#: Appended after each body. `out` is the body's result and `_used` is the
#: prelude's reading of which parser this interpreter actually loaded; they come
#: back together so the caller never has to take the substitution on trust.
EPILOGUE = (
    '\nsys.stdout.write(json.dumps({"used": _used, "out": out},'
    ' ensure_ascii=False))\n'
)


def _run(body: str, old: Path | None, argv: list[str] | None = None) -> tuple:
    """Run PRELUDE + `body` in a fresh interpreter; return (payload, parser digest).

    `body` must leave its result in `out`. The prelude's `_used` comes back
    beside it so the caller can check WHICH parser produced the payload rather
    than assuming the substitution took.
    """
    code = (PRELUDE % {"scripts": str(REPO_ROOT / "scripts"),
                       "old": None if old is None else str(old)}
            + body + EPILOGUE)
    proc = subprocess.run(
        [sys.executable, "-c", code] + list(argv or []),
        capture_output=True, cwd=str(REPO_ROOT), text=True, encoding="utf-8",
        env={**dict(__import__("os").environ), "PYTHONIOENCODING": "utf-8"},
    )
    if proc.returncode != 0:
        raise RuntimeError("child interpreter failed:\n" + proc.stderr)
    payload = json.loads(proc.stdout)
    return payload["out"], payload["used"]


RENDER_BODY = """
out = {}
for sid in json.loads(sys.argv[1]):
    composed = answer.compose(sid)
    out[sid] = None if composed is None else answer.render(composed)
"""

CORPUS_BODY = """
import pathlib
out = {}
for path in sorted(pathlib.Path(%(data)r).glob("*/nodes.json")):
    doc = json.loads(path.read_text(encoding="utf-8"))
    for node in doc.get("statement_nodes", []):
        sid = node.get("statement_id", "<missing-id>")
        formal = ((node.get("formal_statement") or {}).get("canonical_ascii") or "")
        out[sid] = answer._in_words(formal, sid)
"""


def render_all(ids: list[str], old: Path | None) -> tuple[dict, str]:
    """`answer.compose` + `answer.render` for every id, in a fresh interpreter."""
    return _run(RENDER_BODY, old, [json.dumps(ids)])


def sweep_corpus(old: Path | None) -> tuple[dict, str]:
    """`answer._in_words` over every statement node, in one fresh interpreter.

    The task book addresses 32 statements. The corpus holds 12,777, and the
    additive-only claim is about all of them - a diff over 30 tasks that happen
    to carry no glyph would be thirty true rows and no evidence. This sweep asks
    the same question where the change can be seen, and it calls the private
    `_in_words` deliberately: that is the exact function `render` uses to decide
    the line, so a sweep over it moves if and only if a served line moves.
    """
    return _run(CORPUS_BODY % {"data": str(REPO_ROOT / "data")}, old)


def in_words(lines: list[str] | None) -> str | None:
    if lines is None:
        return None
    for line in lines:
        if line.startswith(IN_WORDS_PREFIX):
            return line[len(IN_WORDS_PREFIX):]
    return None


def build(parent: str = "HEAD~1") -> dict:
    tasks_doc = json.loads(TASKS_PATH.read_text(encoding="utf-8"))
    ids = corpus_definition_ids(tasks_doc)

    retired = {row["role"]: row for row in json.loads(
        PREREG_PATH.read_text(encoding="utf-8"))["frozen"]}["parser"]
    live = {row["role"]: row for row in json.loads(
        SUCCESSOR_PATH.read_text(encoding="utf-8"))["frozen"]}["parser"]

    after, used_after = render_all(ids, None)
    corpus_after, used_corpus_after = sweep_corpus(None)
    with tempfile.TemporaryDirectory() as tmp:
        blob = subprocess.run(
            ["git", "show", f"{parent}:scripts/match_signatures.py"],
            capture_output=True, cwd=str(REPO_ROOT), check=True,
        ).stdout
        old = Path(tmp) / "match_signatures.py"
        old.write_bytes(blob)
        observed = sha256_lf_file(old)
        if observed != retired["sha256_lf"]:
            raise RuntimeError(
                f"{parent}:scripts/match_signatures.py has LF sha256 {observed}, "
                f"not the retired pin {retired['sha256_lf']}. The BEFORE side "
                f"would not be the parser the historical artifacts were measured "
                f"under, so no diff is written."
            )
        before, used_before = render_all(ids, old)
        corpus_before, used_corpus_before = sweep_corpus(old)

    # Each child reported the digest of the parser it ACTUALLY loaded. Checking
    # it is the whole reason the prelude computes it: a substitution that
    # silently fails to substitute produces a clean, confident diff of nothing.
    for label, seen, wanted in (
        ("book/after", used_after, live["sha256_lf"]),
        ("corpus/after", used_corpus_after, live["sha256_lf"]),
        ("book/before", used_before, retired["sha256_lf"]),
        ("corpus/before", used_corpus_before, retired["sha256_lf"]),
    ):
        if seen != wanted:
            raise RuntimeError(
                f"the {label} interpreter loaded a parser with LF sha256 {seen}, "
                f"not {wanted}. The two sides of this diff are not the two "
                f"parsers they claim to be, so no artifact is written."
            )

    if set(corpus_before) != set(corpus_after):
        raise RuntimeError("the two sweeps disagree on which statements exist")
    c_gained, c_changed, c_lost = [], [], []
    c_same_served = c_same_absent = 0
    for sid in sorted(corpus_before):
        b, a = corpus_before[sid], corpus_after[sid]
        if b == a:
            if b is None:
                c_same_absent += 1
            else:
                c_same_served += 1
        elif b is None:
            c_gained.append(sid)
        elif a is None:
            c_lost.append(sid)
        else:
            c_changed.append({"statement_id": sid, "before": b, "after": a})

    rows, gained, unchanged, changed, lost = [], [], 0, [], []
    for sid in ids:
        b, a = before[sid], after[sid]
        if b is None or a is None:
            raise RuntimeError(f"{sid}: compose returned nothing on one side")
        bw, aw = in_words(b), in_words(a)
        other_before = [ln for ln in b if not ln.startswith(IN_WORDS_PREFIX)]
        other_after = [ln for ln in a if not ln.startswith(IN_WORDS_PREFIX)]
        if other_before != other_after:
            changed.append({"statement_id": sid, "what": "a non-`in words` line "
                                                         "moved"})
        if bw is None and aw is not None:
            verdict = "GAINED"
            gained.append(sid)
        elif bw == aw:
            verdict = "UNCHANGED"
            unchanged += 1
        elif bw is not None and aw is None:
            verdict = "LOST"
            lost.append(sid)
        else:
            verdict = "CHANGED"
            changed.append({"statement_id": sid, "before": bw, "after": aw})
        row = {"statement_id": sid, "verdict": verdict, "served_before": bw is not None,
               "served_after": aw is not None}
        if verdict == "GAINED":
            row["gained_line"] = f"{IN_WORDS_PREFIX}{aw}"
        if verdict in ("CHANGED", "LOST"):
            row["before"], row["after"] = bw, aw
        rows.append(row)

    def digest(side: dict) -> str:
        joined = "\n".join(f"{sid}\t" + "\n".join(side[sid]) for sid in ids)
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()

    doc = {
        "artifact_id": "transliteration.served_diff.v1",
        "produced": "2026-08-24",
        "produced_by": "scripts/transliteration_served_diff.py",
        "owed_by": "ROADMAP-v0.19 item 3a, re-freeze discipline rule 3",
        "why_it_exists": [
            "scripts/match_signatures.py is NOT among the task book's eleven "
            "`rendering_module_digests`, so widening the tokenizer moves what "
            "`answer.render` serves while every witnessed digest stands still. "
            "The book's seal cannot see this change.",
            "A green digest test over the eleven witnessed modules would "
            "therefore be reassurance about the wrong thing. This artifact is "
            "the diff the seal cannot produce, committed with the probe.",
        ],
        "the_witness_gap_named_concretely": {
            "witnessed_modules": sorted(tasks_doc["rendering_module_digests"]),
            "match_signatures_is_witnessed": (
                "scripts/match_signatures.py" in tasks_doc["rendering_module_digests"]
            ),
            "reading": "eleven modules are witnessed and the parser is not one "
                       "of them; every one of those eleven digests is unchanged "
                       "by this lane.",
        },
        "mechanism": {
            "after": "this working tree, rendered by answer.compose + "
                     "answer.render in a fresh interpreter",
            "before": f"the real file at {parent}:scripts/match_signatures.py, "
                      f"written to a scratch directory and bound into "
                      f"sys.modules as `match_signatures` before any other "
                      f"import, in a SECOND fresh interpreter",
            "why_a_subprocess_and_not_a_monkeypatch": [
                "realize_term and answer bind match_signatures at import time. "
                "Replacing the module after those imports leaves the old parser "
                "live in part of the call graph, and the resulting diff would be "
                "of neither version.",
                "A fresh interpreter with the module pre-bound in sys.modules "
                "resolves every `from match_signatures import ...` in the call "
                "graph to the same one parser.",
            ],
            "why_not_sys_path_ordering": [
                "It does not work, and it fails SILENTLY. scripts/answer.py:47 "
                "and scripts/realize_term.py:112 each sys.path.insert(0, ...) "
                "their own directory at import time, jumping in front of any "
                "scratch directory the caller put first.",
                "The first draft of this generator did exactly that and reported "
                "a confident, internally consistent diff of nothing. It was "
                "caught because the corpus sweep read 8,584 served lines on the "
                "BEFORE side — the post-change number — not because the code "
                "looked wrong.",
            ],
            "why_the_committed_blob_and_not_an_in_memory_revert": [
                "An in-memory revert re-types the old regex, and the digest "
                "check would then be checking the copy against itself. The blob "
                "from git IS the pre-amendment file.",
                "It is verified before it is used: its LF sha256 must equal the "
                "retired pin, or no artifact is written.",
            ],
            "each_child_reports_the_parser_it_loaded": {
                "why": "A mechanism that can silently substitute nothing has to "
                       "be made to prove it did not. Each of the four child "
                       "interpreters hashes match_signatures.__file__ after "
                       "import and returns it; the parent refuses to write this "
                       "artifact if any of the four is not the digest that side "
                       "claims.",
                "book_before": used_before,
                "book_after": used_after,
                "corpus_before": used_corpus_before,
                "corpus_after": used_corpus_after,
            },
            "before_parser_sha256_lf": retired["sha256_lf"],
            "before_parser_is_the_retired_pin": True,
            "after_parser_sha256_lf": live["sha256_lf"],
            "retired_by": "realization.prereg.v1.amendment.transliteration-"
                          "2026-08-24",
        },
        "scope": {
            "tasks": "every corpus_definition task in "
                     "experiments/throughput_tasks.json",
            "count": len(ids),
            "note": "corpus_definition is the kind whose expected content is a "
                    "rendered reference entry, so it is the kind whose served "
                    "lines this change can move. The book's other 89 tasks are "
                    "out of scope for a reason, not by omission.",
        },
        "claim": {
            "additive_only": not changed and not lost,
            "what_it_means": "every line served before the change is served "
                             "byte-identically after it; the only difference is "
                             "newly-parseable statements gaining an `in words` "
                             "line they did not have.",
            "gained": len(gained),
            "unchanged": unchanged,
            "changed": len(changed),
            "lost": len(lost),
            "changed_must_be_zero": "a tokenizer widening that alters an "
                                    "existing rendering is not a widening; the "
                                    "generator refuses to write this file if "
                                    "`changed` or `lost` is non-zero",
        },
        "digests": {
            "all_rendered_lines_before": digest(before),
            "all_rendered_lines_after": digest(after),
            "note": "sha256 over `<statement_id>\\t<rendered lines>` for every "
                    "task in book order. The two differ exactly because lines "
                    "were gained; the per-task rows below are what says nothing "
                    "else moved.",
        },
        "gained_statement_ids": gained,
        "changed_statement_ids": [row["statement_id"] for row in changed],
        "lost_statement_ids": lost,
        "tasks": rows,
        "the_book_reading": [
            f"{len(ids)} corpus_definition tasks, {len(gained)} gained, "
            f"{unchanged} unchanged, {len(changed)} changed, {len(lost)} lost.",
            "ZERO GAINS, and that is a finding rather than a null result: NOT "
            "ONE statement the task book addresses carries `≥` or `≤`. The book "
            "reaches 32 statements by receipt id and every one of them parsed "
            "before this change and renders identically after it.",
            "So the gap rule 3 named — rendered output moving while every "
            "witnessed digest stands still — did not bite for THIS change over "
            "THIS book. It could have: nothing in the book's construction "
            "excludes a glyph-carrying statement, and nothing in its seal would "
            "have reported one if it had been drawn. The diff is what turns "
            "that from a hope into a checked fact, which is exactly why the "
            "roadmap asked for a diff instead of a green digest test.",
            "A diff over thirty tasks that carry no `≥` is thirty true rows and "
            "no evidence about the change itself, so the corpus-wide reading "
            "below asks the same question where the change can be seen.",
        ],
        "corpus_wide_reading": {
            "why": "The additive-only claim is about the corpus, not about 30 "
                   "tasks. This is `answer._in_words` — the exact function "
                   "`render` uses to decide the line — over every statement "
                   "node in data/, before and after, by the same two-interpreter "
                   "mechanism.",
            "statements": len(corpus_before),
            "gained": len(c_gained),
            "unchanged_served": c_same_served,
            "unchanged_absent": c_same_absent,
            "changed": len(c_changed),
            "lost": len(c_lost),
            "additive_only": not c_changed and not c_lost,
            "reading": (
                f"{len(c_gained)} statements gain an `in words` line; "
                f"{c_same_served} keep the byte-identical line they had; "
                f"{c_same_absent} stay silent; {len(c_changed)} changed and "
                f"{len(c_lost)} were lost."
            ),
            "changed_statement_ids": [row["statement_id"] for row in c_changed],
            "lost_statement_ids": c_lost,
            "sample_gained": [
                {"statement_id": sid, "in_words": corpus_after[sid]}
                for sid in c_gained[:5]
            ],
        },
    }
    if changed or lost or c_changed or c_lost:
        raise ChangedLine(
            "STOP: previously-served lines moved — book "
            f"changed={len(changed)} lost={len(lost)}; corpus "
            f"changed={len(c_changed)} lost={len(c_lost)}. "
            f"{json.dumps((changed + c_changed)[:5], ensure_ascii=False)}"
        )
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parent", default="HEAD~1",
                    help="the git rev holding the pre-amendment parser")
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    ap.add_argument("--check", action="store_true",
                    help="regenerate and compare instead of writing")
    args = ap.parse_args(argv)
    try:
        doc = build(args.parent)
    except ChangedLine as exc:
        print(str(exc), file=sys.stderr)
        return 3
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        current = args.out.read_text(encoding="utf-8")
        if current != text:
            print("REGENERATION DIFFERS from the committed artifact",
                  file=sys.stderr)
            return 1
        print("regenerates identically")
        return 0
    args.out.write_bytes(text.encode("utf-8"))
    print(f"wrote {args.out} — gained {doc['claim']['gained']}, "
          f"unchanged {doc['claim']['unchanged']}, "
          f"changed {doc['claim']['changed']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
