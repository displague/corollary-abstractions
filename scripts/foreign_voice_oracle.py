#!/usr/bin/env python3
"""B-P's driver: submit dialect text to the pinned binary, get a digest back.

DESIGN-foreign-voice §6 B-P — *"the construction prerequisite, discharged
before B0 freezes"*.  The design's §3.2 spends a whole correction establishing
that this did not exist: `check_lean4` adjudicates exit code, warnings and an
axiom footprint and **produces no term**; `prover/ExtractData.win.lean` emits
command `Syntax` and **pretty-printed** goal states, which are binder-name and
width dependent.  *"Elaborated-term emission is a construction prerequisite
with its own registered step (B-P), not an assumption."*  This module and
`prover/lean/normalizer/Serialize.lean` are that step.

## What a digest from here means, and what it does not

`digest(text)` is `sha256(serialize(elaborate(text)))` under rule R's
committed settings.  The identity relation of §3.2 compares two such digests:
one for `R(s)` and one for `R(literal_inverse(render(s)))`, **both recomputed
in the same run and never carried from ingest**.

It is not a verdict.  `scripts/external_verifier.py:6–7` governs unweakened —
*"a passing check certifies what it checks, not correctness in general"* — and
`:35–40` means a digest alone never mints a `verified_by` link.  Nothing here
proves anything: the serialized terms are propositions, not proofs, and no
`sorry` and no `#print axioms` appear anywhere in this path.

## Hermetic rule, imported rather than re-decided

The toolchain name is read from a committed `lean-toolchain` file and resolved
through `external_verifier.toolchain_binary`, which returns `None` rather than
downloading.  An absent toolchain **refuses and aborts** — B2: *"REFUSED — the
toolchain is absent or an input escapes containment — aborts the run; it is
not a data point, and a run with any refusal publishes zero rates."*  No lake,
no Mathlib, no network.  `Serialize.lean` is never compiled to an `.olean`; it
is concatenated with the `#ser` commands into one temporary source file, so
there is no build artifact that can go stale against its digest.

## Why every term carries its own tag

The B0 eligibility probe attributes diagnostics to statements **by line
number**, and that is exactly the shape that let the frontend's 100-error
cutoff report 2,982 eligible against a truth of 2,319.  Here nothing is
attributed by position: `#ser "tag" => term` prints one `FVSER <tag>` line or
one `FVERR <tag>` line, and a tag with no line at all is a *parse* failure —
the one thing no elaborator can catch.

A parse error can still swallow the commands that follow it, so a missing tag
is **re-probed in a batch of its own** before it is called a failure.  A tag
that is still missing when it is the only command in the file is genuinely
unparseable; one that reappears was a bystander.  Silence is never read as
success.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - CLI import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import foreign_voice_rule_r as rule_r  # noqa: E402
from external_verifier import toolchain_binary  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
NORMALIZER_DIR = REPO_ROOT / "prover" / "lean" / "normalizer"
DEFAULT_SERIALIZER = NORMALIZER_DIR / "Serialize.lean"
DEFAULT_TOOLCHAIN_FILE = NORMALIZER_DIR / "lean-toolchain"

_TAG_RE = re.compile(r"[A-Za-z0-9._-]+")
_LINE_RE = re.compile(r"FV(SER|ERR) (\S+) (.*)$")
_CUTOFF = "maximum number of errors"


class OracleRefusal(RuntimeError):
    """The oracle could not run. B2: a refusal aborts, it is not a data point."""


@dataclass(frozen=True)
class Serialization:
    """One term's answer. Either a serialization or the reason there is none."""

    tag: str
    term: str
    ok: bool
    serialization: str
    digest: str
    error: str

    @property
    def refused(self) -> bool:
        return not self.ok


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Oracle:
    """A resolved, pinned oracle. Constructing one proves the toolchain is there."""

    binary: Path
    toolchain: str
    serializer: Path
    serializer_text: str
    rule: rule_r.RuleR

    def preamble(self) -> str:
        """The bytes every batch carries: the serializer, then rule R's settings.

        The settings are re-emitted here even though `Serialize.lean` already
        sets two of them, because B5 asserts them as *committed settings of the
        run* and a setting inherited from another file is not one this run's
        bytes record.
        """
        return (self.serializer_text.rstrip("\n") + "\n\n"
                + "\n".join(self.rule.set_option_lines()) + "\n")

    def serialize(self, terms: list[tuple[str, str]],
                  batch_size: int = 100) -> dict[str, Serialization]:
        """Serialize every `(tag, term)`. Raises `OracleRefusal`, never guesses."""
        seen: set[str] = set()
        for tag, term in terms:
            if not _TAG_RE.fullmatch(tag):
                raise OracleRefusal(
                    f"tag {tag!r} is not [A-Za-z0-9._-]+; a tag goes into a Lean "
                    f"string literal and this module will not escape one for you"
                )
            if tag in seen:
                raise OracleRefusal(f"tag {tag!r} appears twice; tags are the identity")
            seen.add(tag)
            if "\n" in term or "\r" in term:
                raise OracleRefusal(f"{tag}: the term spans more than one line")

        out: dict[str, Serialization] = {}
        for start in range(0, len(terms), batch_size):
            out.update(self._run_with_reprobe(terms[start:start + batch_size]))
        return out

    def digest_of(self, term: str) -> Serialization:
        """One term, one answer. The shape §3.2's identity relation calls twice."""
        return self.serialize([("t", term)])["t"]

    # -- internals ---------------------------------------------------------

    def _run_with_reprobe(self, chunk: list[tuple[str, str]]) -> dict[str, Serialization]:
        answered = self._run(chunk)
        missing = [(tag, term) for tag, term in chunk if tag not in answered]
        if missing and len(missing) < len(chunk):
            # A parse error swallows the commands after it. Re-probe the
            # bystanders without the offender before calling them failures.
            answered.update(self._run_with_reprobe(missing))
            missing = [(tag, term) for tag, term in chunk if tag not in answered]
        for tag, term in missing:
            answered[tag] = Serialization(
                tag=tag, term=term, ok=False, serialization="", digest="",
                error="parse_error: the pinned binary produced no line for this "
                      "tag even when it was the only command in the file",
            )
        return answered

    def _run(self, chunk: list[tuple[str, str]]) -> dict[str, Serialization]:
        lines = [self.preamble()]
        for tag, term in chunk:
            lines.append(f'#ser "{tag}" => ({term})')
        source = "\n".join(lines) + "\n"

        with tempfile.TemporaryDirectory() as scratch:
            path = Path(scratch) / "Batch.lean"
            path.write_text(source, encoding="utf-8", newline="\n")
            completed = subprocess.run(
                [str(self.binary), *self.rule.command_line_options(), str(path)],
                cwd=scratch,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        output = ((completed.stdout or "") + (completed.stderr or "")).replace(
            "\r\n", "\n")
        if _CUTOFF in output:
            raise OracleRefusal(
                "the frontend's error cutoff fired; diagnostics are truncated and "
                "a truncated stream cannot be told from a clean one"
            )

        by_term = dict(chunk)
        answered: dict[str, Serialization] = {}
        for line in output.split("\n"):
            match = _LINE_RE.search(line)
            if not match:
                continue
            kind, tag, payload = match.groups()
            if tag not in by_term or tag in answered:
                # A tag we did not ask for, or asked for once and heard twice.
                # Either means the output is not the output of this batch.
                raise OracleRefusal(
                    f"the pinned binary answered for {tag!r} unexpectedly; the "
                    f"batch's answers cannot be trusted"
                )
            ok = kind == "SER"
            answered[tag] = Serialization(
                tag=tag,
                term=by_term[tag],
                ok=ok,
                serialization=payload if ok else "",
                digest=_digest(payload) if ok else "",
                error="" if ok else payload,
            )
        return answered


def load(serializer: Path | None = None,
         toolchain_file: Path | None = None,
         rule: rule_r.RuleR | None = None) -> Oracle:
    """Resolve the pinned oracle, or refuse. NEVER downloads."""
    serializer = serializer or DEFAULT_SERIALIZER
    toolchain_file = toolchain_file or DEFAULT_TOOLCHAIN_FILE
    if not serializer.is_file():
        raise OracleRefusal(f"no serializer at {serializer}")
    if not toolchain_file.is_file():
        raise OracleRefusal(f"no pinned toolchain file at {toolchain_file}")
    name = toolchain_file.read_text(encoding="utf-8").strip()
    binary = toolchain_binary(name)
    if binary is None:
        raise OracleRefusal(
            f"toolchain {name!r} is not installed; refusing to download "
            f"(hermetic rule). B2: a refusal aborts the run and publishes no rate."
        )
    return Oracle(
        binary=binary,
        toolchain=name,
        serializer=serializer,
        serializer_text=serializer.read_text(encoding="utf-8"),
        rule=rule or rule_r.load(),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--term", action="append", default=[],
                        help="a dialect term to serialize; repeatable")
    parser.add_argument("--json", action="store_true",
                        help="emit the full record rather than tag/digest lines")
    args = parser.parse_args(argv)
    if not args.term:
        parser.error("nothing to do: pass at least one --term")

    try:
        oracle = load()
        answers = oracle.serialize([(f"t{i}", term)
                                    for i, term in enumerate(args.term)])
    except OracleRefusal as exc:
        print(f"oracle refused: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(
            {tag: {"ok": row.ok, "digest": row.digest, "error": row.error,
                   "serialization": row.serialization}
             for tag, row in sorted(answers.items())},
            ensure_ascii=False, indent=1, sort_keys=True))
        return 0
    for tag, row in sorted(answers.items()):
        print(f"{tag}\t{'ok ' if row.ok else 'ERR'}\t"
              f"{row.digest or row.error[:80]}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
