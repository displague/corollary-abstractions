#!/usr/bin/env python3
"""G1 and G1b: the canonicalizer against the pinned parser, and the census of blindness.

Two pre-run prerequisites of DESIGN-voice-completion §6, both adjudicated
against the **pinned binary** — the authority this repository did not write and
which has never seen `grouping.json`, `rule_r.json` or the lexicon.

**G1 — the canonicalizer agrees with the pinned parser.** For every covered
statement the binary elaborates `R(s)` and `canon(R(s))` to **byte-identical
serializations**.  *Floor: 2,313 of 2,313 — no allowance.*  One disagreement
means `grouping.json` states a precedence the toolchain does not use, and one
wrong level is wrong everywhere, so a single miss stops the cycle.

**G1b — no redundant grouping bracket survives.** For **every** grouping pair
in **every** canonical surface, deleting that pair must change the elaborated
term or fail to elaborate.  *Floor: 5,228 of 5,228*, with the 215 ascription
and 16 binder-group pairs excluded by `pair_kind`.

G1b is the structural claim stated **exhaustively rather than sampled**, and
it is what **demotes C-V4′'s `drop_group` to a confirmation**: a 50-statement
sample cannot establish what a 5,228-pair census establishes.  The design says
in advance which governs — *"if the two disagree the census governs and the
disagreement is the finding"* — which is why this runs before the registered
run rather than inside it.

## The deletion is by matched pair, by index

§3.3 records a defect in the inherited control: v0.19's `drop_group` deleted
the **first opening and the first closing** independently, two `str.replace`
calls, which coincide only when the first bracket contains no nested bracket —
and 3 of its sampled 50 nest.  Here the pair is deleted **by index** from the
emission the rule already computed, so a grouping-pair deletion is always a
grouping-pair deletion.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - CLI import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import foreign_voice_oracle as fvo  # noqa: E402
import grouping_canonical_probe as gp  # noqa: E402
import measure_foreign_voice as mfv  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / "experiments" / "grouping_agreement.json"

G1_FLOOR_IS_EVERY_STATEMENT = True
G1B_FLOOR_IS_EVERY_PAIR = True


class AgreementError(RuntimeError):
    """A prerequisite could not be measured. Never a rate."""


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def measure(batch_size: int = 300) -> dict:
    rule = gp.Rule.load()
    oracle = fvo.load()
    data = REPO_ROOT / "data" / "foreign_voice"
    preview = json.loads((data / "eligibility_preview.json").read_text(encoding="utf-8"))
    register = json.loads((data / "register.json").read_text(encoding="utf-8"))
    rows = mfv.covered_rows(preview, register)

    # ---- parse and canonicalize once ---------------------------------
    canonical: dict[str, list[str]] = {}
    spans: dict[str, list[tuple[int, int]]] = {}
    parse_failures: list[dict] = []
    for row in rows:
        sid = row["statement_id"]
        try:
            node = gp.parse(row["interpreted"], rule)
            emission = gp.emit(node, rule)
        except gp.GroupingError as exc:
            parse_failures.append({"statement_id": sid, "error": str(exc)})
            continue
        canonical[sid] = emission.tokens
        spans[sid] = gp.grouping_pair_spans(emission.tokens, emission.pair_kinds)
    if parse_failures:
        raise AgreementError(
            f"G-P cannot be discharged: {len(parse_failures)} statements do not "
            f"parse under the rule; the first is {parse_failures[0]}")

    # ---- G1: R(s) and canon(R(s)) elaborate identically ---------------
    terms: list[tuple[str, str]] = []
    order = [row["statement_id"] for row in rows]
    by_id = {row["statement_id"]: row for row in rows}
    for index, sid in enumerate(order):
        terms.append((f"o{index}", by_id[sid]["interpreted"]))
        terms.append((f"c{index}", " ".join(canonical[sid])))
    answers = oracle.serialize(terms, batch_size=batch_size)

    agree = 0
    disagreements: list[dict] = []
    canonical_digest: dict[str, str] = {}
    for index, sid in enumerate(order):
        original, canon_answer = answers[f"o{index}"], answers[f"c{index}"]
        canonical_digest[sid] = canon_answer.digest
        if original.ok and canon_answer.ok and original.digest == canon_answer.digest:
            agree += 1
        else:
            disagreements.append({
                "statement_id": sid,
                "interpreted": by_id[sid]["interpreted"],
                "canonical": " ".join(canonical[sid]),
                "original_ok": original.ok, "canonical_ok": canon_answer.ok,
                "original_error": original.error, "canonical_error": canon_answer.error,
            })

    # ---- G1b: every canonical grouping pair, deleted --------------------
    mutants: list[tuple[str, str]] = []
    index_of: list[tuple[str, int]] = []
    for sid in order:
        for which, span in enumerate(spans[sid]):
            tag = f"m{len(index_of)}"
            index_of.append((sid, which))
            mutants.append((tag, " ".join(gp.delete_pair(canonical[sid], span))))
    mutant_answers = oracle.serialize(mutants, batch_size=batch_size) if mutants else {}

    detected = blind = 0
    by_digest = by_failure = 0
    blind_cases: list[dict] = []
    for position, (sid, which) in enumerate(index_of):
        answer = mutant_answers[f"m{position}"]
        if not answer.ok:
            detected += 1
            by_failure += 1
        elif answer.digest != canonical_digest[sid]:
            detected += 1
            by_digest += 1
        else:
            blind += 1
            blind_cases.append({
                "statement_id": sid, "pair_index": which,
                "canonical": " ".join(canonical[sid]),
                "mutant": answer.term,
            })

    return {
        "measure_id": "foreign_voice.grouping_agreement.v1",
        "measured": "2026-08-24",
        "design": "docs/DESIGN-voice-completion.md",
        "toolchain": oracle.toolchain,
        "inputs": {
            "grouping_rule": "data/foreign_voice/grouping.json",
            "grouping_rule_sha256_lf": _sha256_lf(data / "grouping.json"),
            "probe": "scripts/grouping_canonical_probe.py",
            "probe_sha256_lf": _sha256_lf(
                REPO_ROOT / "scripts" / "grouping_canonical_probe.py"),
        },
        "g1": {
            "gate": "G1 — the canonicalizer agrees with the pinned parser",
            "statements": len(order),
            "agree": agree,
            "floor": len(order),
            "floor_met": agree == len(order),
            "disagreements": disagreements,
            "why_no_allowance": (
                "one disagreement means grouping.json states a precedence the "
                "toolchain does not use, and one wrong level is wrong "
                "everywhere"
            ),
        },
        "g1b": {
            "gate": "G1b — no redundant grouping bracket survives, over the whole set",
            "pairs_tested": len(index_of),
            "detected": detected,
            "detected_by_digest_change": by_digest,
            "detected_by_failing_to_elaborate": by_failure,
            "blind": blind,
            "floor": len(index_of),
            "floor_met": blind == 0,
            "blind_cases": blind_cases,
            "excluded_by_pair_kind": {
                "ascription": 215,
                "binder_group": 16,
                "why": (
                    "an ascription bracket is syntax and a binder-group bracket "
                    "is stripped by the rule; neither is a grouping pair, and a "
                    "census about grouping that counted them would be counting "
                    "the wrong thing"
                ),
            },
            "deletion_is_by_matched_pair": (
                "deleted by INDEX from the emission the rule computed, not by "
                "two independent str.replace calls. v0.19's drop_group deleted "
                "the first opening and the first closing, which coincide only "
                "when the first bracket contains no nested bracket — 3 of its "
                "sampled 50 nest"
            ),
            "it_demotes_the_sample": (
                "a 50-statement sample cannot establish what a "
                f"{len(index_of)}-pair census establishes. If C-V4′'s "
                "drop_group and this census disagree, THE CENSUS GOVERNS and "
                "the disagreement is the finding"
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--batch-size", type=int, default=300)
    args = parser.parse_args(argv)
    try:
        report = measure(args.batch_size)
    except (AgreementError, fvo.OracleRefusal) as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    g1, g1b = report["g1"], report["g1b"]
    print(f"G1  {g1['agree']} of {g1['statements']} agree   floor_met {g1['floor_met']}")
    print(f"G1b {g1b['detected']} of {g1b['pairs_tested']} detected "
          f"({g1b['detected_by_digest_change']} by digest, "
          f"{g1b['detected_by_failing_to_elaborate']} by failing to elaborate); "
          f"blind {g1b['blind']}   floor_met {g1b['floor_met']}")
    print(f"written to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
