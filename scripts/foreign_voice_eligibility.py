#!/usr/bin/env python3
"""B0a's split and B0b+B0c's eligibility, computed against the pinned binary.

Two measurements, both prerequisites of everything else in
DESIGN-foreign-voice, and both computed here so the preview numbers the
lexicon and the register were authored against are **reproducible rather than
remembered**:

* **B0a — the transliterable/foreign split.**  The mute set — every corpus node
  whose `formal_statement.canonical_ascii` the byte-frozen parser
  `scripts/match_signatures.py` cannot read — partitioned by whether it parses
  *after substituting exactly two glyphs*, `≥`→`>=` and `≤`→`<=`.  The half
  that then parses is **transliterable** and is **excluded from this cycle's
  claim** (design Correction 1); the half that does not is the **foreign
  residue**, which is the design's actual territory.
* **B0b+B0c — the oracle's reach, stated as one measurement.**  A residue
  statement is **oracle-eligible iff, after rule R, the pinned binary accepts
  it** with `autoImplicit false`.  Eligibility is defined **by outcome**.
  There is no blocklist: the design's first draft used an authored regex naming
  what its writer guessed Lean would reject, and the review was right that a
  hand-written eligibility filter measures the filter.

## Hermetic rule, imported unchanged

The pinned toolchain's `lean` binary is invoked **directly by path** through
`external_verifier.toolchain_binary`, never through the elan proxy, so an
absent toolchain is a **refusal** and can never become a network download
(`scripts/external_verifier.py:14–17`).  No lake, no Mathlib, no network.  The
toolchain name is read from a committed `lean-toolchain` file, so the pin is a
digestible artifact and not an argument.

## The measurement bug this module refuses rather than tolerates

The pinned frontend stops reporting diagnostics after 100 errors:

    maximum number of errors (100; from option `maxErrors`) reached, exiting

A batch prober that infers acceptance from the **absence** of an error then
reads every statement after the hundredth error as accepted.  Measured on this
tree during authoring, that bug alone reported **2,982 eligible where the truth
is 2,319** — and it reported the five wholly-mute Prop-valued corpora as fully
eligible, which would have sent the B0b+B0c branch decision the wrong way on a
number that was an artefact of a diagnostic limit.  `rule_r.json` freezes
`-DmaxErrors` so the cutoff cannot fire, and this module **refuses the batch**
if the line appears anyway.  A silent truncation that reads as a pass is
exactly the failure mode B2 exists to forbid, arriving through the harness
instead of through the oracle.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - CLI import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import foreign_voice_rule_r as rule_r  # noqa: E402
from external_verifier import toolchain_binary  # noqa: E402
from match_signatures import (  # noqa: E402
    Parser,
    TemplateParseError,
    canonicalize,
    tokenize,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA_DIR = REPO_ROOT / "data"
DEFAULT_TOOLCHAIN_FILE = REPO_ROOT / "prover" / "lean" / "normalizer" / "lean-toolchain"
DEFAULT_OUT = REPO_ROOT / "data" / "foreign_voice" / "eligibility_preview.json"

#: Correction 1's two glyphs, and nothing else. The whole point of B0a is that
#: this list is TWO ROWS LONG — a third would make "transliterable" mean
#: something the design did not measure.
TRANSLITERATION = (("≥", ">="), ("≤", "<="))

_ERROR_RE = re.compile(r"^.*?:(\d+):(\d+): error(?:\([^)]*\))?: (.*)$", re.M)
_CUTOFF = "maximum number of errors"

#: Return codes the pinned frontend produces in normal operation: 0 when it
#: logged nothing, 1 when it logged a diagnostic. Anything else is a crash, a
#: rejected flag, or a binary that is not the one this file thinks it is — and
#: none of those is a measurement. Without this, a frontend that died halfway
#: through a batch would leave every statement after the death looking accepted,
#: which is the maxErrors bug wearing a different hat.
_EXPECTED_RETURNCODES = (0, 1)

#: Appended to the end of every batch. The first must NOT error, proving the
#: file elaborated all the way down; the second MUST error with a known
#: diagnostic, proving the frontend is still reporting at all. A run that has
#: stopped reporting looks exactly like a run with nothing to report, and this
#: probe reads acceptance from the absence of a diagnostic.
_SENTINEL_OK = "example : (0 : Nat) = 0 := rfl"
_SENTINEL_ERR = "example : fv_sentinel_no_such_identifier := sorry"
_SENTINEL_ERR_EXPECT = "fv_sentinel_no_such_identifier"


class EligibilityError(RuntimeError):
    """The probe could not run, or ran and cannot be trusted. Never a rate."""


# --------------------------------------------------------------------------
# B0a — the split, under the byte-frozen parser
# --------------------------------------------------------------------------


def parses(source: str) -> bool:
    """Exactly what `realize_term.realize` calls a parseable term, and nothing more."""
    if not source or not source.strip():
        return False
    try:
        canonicalize(Parser(tokenize(source)).parse())
    except (TemplateParseError, RecursionError):
        return False
    return True


def transliterate(source: str) -> str:
    """Correction 1's two-glyph swap."""
    for glyph, ascii_form in TRANSLITERATION:
        source = source.replace(glyph, ascii_form)
    return source


def split(data_dir: Path) -> dict:
    """B0a: parseable / transliterable / foreign residue, per corpus."""
    if not data_dir.is_dir():
        raise EligibilityError(f"no such data directory: {data_dir}")
    paths = sorted(data_dir.glob("*/nodes.json"))
    if not paths:
        # A split over nothing reports 0/0/0 and reads as a run. That is the
        # shape of a mis-pointed --data-dir, so it refuses (v0.18's census
        # lesson, imported: `realize_term.CensusError`).
        raise EligibilityError(f"{data_dir} contains no */nodes.json corpora")

    rows: list[dict] = []
    per_corpus: dict[str, Counter] = {}
    #: Every bucket starts at zero and stays in the dict. A totals map whose
    #: KEYS depend on the data cannot report an EMPTY bucket — and when
    #: `b1c9440` widened the tokenizer so the two glyphs read natively, the
    #: transliterable bucket emptied and this function silently dropped the key
    #: while the CLI crashed on it. A zero is a measurement; a missing key is a
    #: guess about what the reader will assume.
    BUCKETS = ("nodes", "parseable", "mute", "transliterable", "residue")
    for path in paths:
        doc = json.loads(path.read_text(encoding="utf-8"))
        corpus = doc.get("discipline", path.parent.name)
        counts = per_corpus.setdefault(corpus, Counter({b: 0 for b in BUCKETS}))
        for node in doc.get("statement_nodes", []):
            sid = node.get("statement_id", "<missing-id>")
            source = ((node.get("formal_statement") or {})
                      .get("canonical_ascii") or "")
            counts["nodes"] += 1
            if parses(source):
                counts["parseable"] += 1
                continue
            counts["mute"] += 1
            if parses(transliterate(source)):
                counts["transliterable"] += 1
                continue
            counts["residue"] += 1
            rows.append({"statement_id": sid, "corpus": corpus, "source": source})

    totals = Counter({bucket: 0 for bucket in BUCKETS})
    for counts in per_corpus.values():
        totals.update(counts)
    return {
        "per_corpus": {name: dict(counts) for name, counts in sorted(per_corpus.items())},
        "totals": dict(totals),
        "residue": rows,
    }


# --------------------------------------------------------------------------
# B0b+B0c — eligibility by outcome
# --------------------------------------------------------------------------


def _toolchain(toolchain_file: Path) -> tuple[str, Path]:
    if not toolchain_file.is_file():
        raise EligibilityError(f"no pinned toolchain file at {toolchain_file}")
    name = toolchain_file.read_text(encoding="utf-8").strip()
    binary = toolchain_binary(name)
    if binary is None:
        raise EligibilityError(
            f"toolchain {name!r} is not installed; refusing to download "
            f"(hermetic rule). B2: a refusal aborts the run and publishes no rate."
        )
    return name, binary


def probe(items: list[tuple[str, str]], rule: rule_r.RuleR, binary: Path,
          batch_size: int = 150) -> dict[str, dict]:
    """Accept/reject every `(key, R(s))` pair. Raises rather than guessing."""
    verdicts: dict[str, dict] = {}
    for start in range(0, len(items), batch_size):
        chunk = items[start:start + batch_size]
        lines = list(rule.set_option_lines())
        spans: dict[int, str] = {}
        for offset, (key, text) in enumerate(chunk):
            if "\n" in text or "\r" in text:
                # One statement per line is what makes the line number an
                # identity. A multi-line statement would silently shift every
                # later line's attribution, which is the same class of bug as
                # the maxErrors cutoff: wrong answers that look like answers.
                raise EligibilityError(
                    f"{key}: R(s) spans more than one line; the batch harness "
                    f"attributes diagnostics by line number"
                )
            lines.append(f"theorem fv_{start + offset} : {text} := sorry")
            spans[len(lines)] = key
        lines.append(_SENTINEL_OK)
        sentinel_ok_line = len(lines)
        lines.append(_SENTINEL_ERR)
        sentinel_err_line = len(lines)
        source = "\n".join(lines) + "\n"

        with tempfile.TemporaryDirectory() as scratch:
            probe_file = Path(scratch) / "Probe.lean"
            probe_file.write_text(source, encoding="utf-8", newline="\n")
            completed = subprocess.run(
                [str(binary), *rule.command_line_options(), str(probe_file)],
                cwd=scratch,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        output = ((completed.stdout or "") + (completed.stderr or "")).replace("\r\n", "\n")
        if completed.returncode not in _EXPECTED_RETURNCODES:
            raise EligibilityError(
                f"the pinned binary exited {completed.returncode}; the frontend "
                f"exits 0 or 1 in normal operation, and this probe reads "
                f"acceptance from the ABSENCE of a diagnostic — so a frontend "
                f"that died is a frontend that accepted everything after it"
            )
        if _CUTOFF in output:
            raise EligibilityError(
                "the frontend's error cutoff fired; every statement after it "
                "would read as ACCEPTED because no diagnostic was printed. "
                "Batch results discarded rather than published."
            )

        errors_by_line: dict[int, str] = {}
        for match in _ERROR_RE.finditer(output):
            errors_by_line.setdefault(int(match.group(1)), match.group(3))
        if sentinel_ok_line in errors_by_line:
            raise EligibilityError(
                f"the batch's passing sentinel failed "
                f"({errors_by_line[sentinel_ok_line][:120]}); the file did not "
                f"elaborate cleanly to its end, so nothing above it is a reading"
            )
        if _SENTINEL_ERR_EXPECT not in errors_by_line.get(sentinel_err_line, ""):
            raise EligibilityError(
                "the batch's failing sentinel did not report its known "
                "diagnostic; a frontend that has stopped reporting looks exactly "
                "like a batch with nothing to report, and this probe cannot tell "
                "those apart without a sentinel"
            )

        failed: dict[str, str] = {}
        boundaries = sorted(spans)
        for line, message in errors_by_line.items():
            if line >= sentinel_ok_line:
                # The sentinels live past the last statement and are adjudicated
                # above. Attributing their diagnostics to the final statement of
                # the batch would make the last row of every batch a failure.
                continue
            owners = [b for b in boundaries if b <= line]
            if not owners:
                continue
            failed.setdefault(spans[owners[-1]], message[:240])
        for key, text in chunk:
            verdicts[key] = {
                "accepted": key not in failed,
                "error": failed.get(key, ""),
                "interpreted": text,
            }
    return verdicts


def preview(data_dir: Path, toolchain_file: Path,
            rule: rule_r.RuleR | None = None,
            batch_size: int = 150) -> dict:
    """B0a + B0b+B0c as one artifact. This is a PREVIEW, not the registered run."""
    rule = rule or rule_r.load()
    name, binary = _toolchain(toolchain_file)
    tables = split(data_dir)
    interpretations = {row["statement_id"]: rule.apply(row["source"])
                       for row in tables["residue"]}
    items = [(row["statement_id"], interpretations[row["statement_id"]].text)
             for row in tables["residue"]]
    verdicts = probe(items, rule, binary, batch_size=batch_size)

    statements = []
    for row in tables["residue"]:
        sid = row["statement_id"]
        verdict = verdicts[sid]
        interpretation = interpretations[sid]
        statements.append({
            "statement_id": sid,
            "corpus": row["corpus"],
            "source": row["source"],
            "interpreted": interpretation.text,
            "interpretation_shift": list(interpretation.interpretation_shift),
            "preamble_binders": list(interpretation.preamble_binders),
            "accepted": verdict["accepted"],
            "error": verdict["error"],
        })
    statements.sort(key=lambda row: row["statement_id"])

    accepted = [row for row in statements if row["accepted"]]
    return {
        "preview_id": "foreign_voice.eligibility_preview.v1",
        "measured": "2026-08-24",
        "design": "docs/DESIGN-foreign-voice.md",
        "what_this_is": [
            "The B0a and B0b+B0c PREVIEW, recorded in the preregistration commit "
            "so the lexicon and the register were authored against numbers a "
            "reader can recompute. B0a and B0b+B0c remain the registered probes; "
            "this file is not the registered run and mints nothing.",
        ],
        "rule_id": rule.rule_id,
        "toolchain": name,
        "elaboration_settings": {
            "autoImplicit": rule.auto_implicit,
            "relaxedAutoImplicit": rule.relaxed_auto_implicit,
            "maxHeartbeats": rule.max_heartbeats,
            "maxErrors": rule.max_errors,
        },
        "b0a": {
            "totals": tables["totals"],
            "per_corpus": tables["per_corpus"],
            "transliteration": [list(pair) for pair in TRANSLITERATION],
            "floor": "the foreign residue must be >= 2,000 statements",
            "floor_met": tables["totals"].get("residue", 0) >= 2000,
        },
        "b0bc": {
            "residue": len(statements),
            "accepted": len(accepted),
            "rejected": len(statements) - len(accepted),
            "accepted_by_corpus": dict(sorted(Counter(
                row["corpus"] for row in accepted).items())),
            "floor": "at least 1,000 accepted",
            "floor_met": len(accepted) >= 1000,
        },
        "statements": statements,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--toolchain-file", type=Path, default=DEFAULT_TOOLCHAIN_FILE)
    parser.add_argument("--batch-size", type=int, default=150)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    try:
        report = preview(args.data_dir, args.toolchain_file,
                         batch_size=args.batch_size)
    except EligibilityError as exc:
        print(f"eligibility preview refused: {exc}", file=sys.stderr)
        return 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n",
    )
    totals = report["b0a"]["totals"]
    print(f"B0a  nodes {totals['nodes']}  parseable {totals['parseable']}  "
          f"mute {totals['mute']}  transliterable {totals['transliterable']}  "
          f"residue {totals['residue']}")
    print(f"B0bc accepted {report['b0bc']['accepted']} of {report['b0bc']['residue']}")
    print(f"written to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
