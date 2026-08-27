#!/usr/bin/env python3
"""CR-P1 — the reconstruction rule for the one worked raw-invocation kind.

`docs/DESIGN-cold-receipt.md` §12 orders this *before* the general harness, on
the WITNESS W1 precedent, and states its job precisely:

    Its job is not to assert that the C-E3 rows are re-checkable but to
    **derive and publish the exact rule** by which a bundle reconstructs a
    probe from the artifact: proposition → source text → `source_sha256` →
    invocation.

    If the rule cannot be published as a rule, B2's floor of one is not
    meetable and the slice publishes that instead of opening.

This script publishes it, and publishes the **gap** in it. §12 records the
finding that strengthens B2 rather than softening it: the artifact carries
only the *positive* template, in its own ``pattern`` field. The **negative**
probe's template and the trailing newline are recorded nowhere in the
artifact — the negation glyph appears zero times in it — so a reconstructor
must supply half the rule from outside the receipt. That half is published
here, with its source named, and the count of the glyph in the artifact is
**computed** by this script rather than asserted, so the gap is a measurement.

THE RULE
--------

Given one row of ``experiments/conformance_ce3_supplement.json``:

1. **proposition** — take ``row["substituted_proposition"]`` verbatim. It is
   already fully parenthesised and carrier-ascribed by the writer's
   ``render_proposition``; a reconstructor neither re-renders nor re-binds.
2. **source text** — substitute into the two templates:

       positive:  ``example : (<prop> : Prop) := by decide\\n``
       negative:  ``example : (¬(<prop>) : Prop) := by decide\\n``

   The negation is U+00AC NOT SIGN and it introduces **one extra paren pair**
   inside the ``: Prop`` ascription. Both texts end with exactly one LF and
   carry no import, no header, no BOM.
3. **digest** — ``sha256(source_text.encode("utf-8"))``, over the **LF** form.
   This is a digest of the in-memory string, not of the file the writer put on
   disk: ``Path.write_text`` translates ``\\n`` to ``os.linesep``, so on this
   Windows workstation the bytes the checker parsed ended ``\\r\\n`` while the
   recorded digest covers the LF form. A reconstructor that hashed the file it
   wrote would not reach the recorded digest, and this step is where that is
   said out loud.
4. **invocation** — write the source to ``<tmp>/Probe.lean`` and run
   ``[<lean binary>, <that path>]`` with ``cwd=<tmp>``. No flags. The
   environment is inherited; nothing is scrubbed. ``accepted`` is
   ``returncode == 0`` and nothing else — the checker's output is evidence, never
   the adjudication.
5. **verdict** — the pair maps as the writer's table does:
   (accepted, ¬accepted) → ``refuted_counterexample``;
   (¬accepted, accepted) → ``confirmed_counterexample``; otherwise
   ``did_not_reduce``.

Steps 1–3 need **no program and no checker** and are what this script executes
and verifies against every committed row. Step 4 needs the pinned third-party
binary and nothing of this repository. Step 5 is arithmetic on two integers.

Usage
-----

    python scripts/cold_reconstruct_ce3.py --out cold/reconstruction_rule.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from report_provenance import provenance_block  # noqa: E402

SCHEMA_TAG = "cold-reconstruction-rule/1"
ARTIFACT = "experiments/conformance_ce3_supplement.json"

POSITIVE_TEMPLATE = "example : ({prop} : Prop) := by decide\n"
NEGATIVE_TEMPLATE = "example : (¬({prop}) : Prop) := by decide\n"

#: How many rows get their full reconstructed text published, as the draft's
#: "one worked stranger-path transcript" grown to three. Every row is
#: *verified*; three are *transcribed*.
TRANSCRIBED = 3


def reconstruct(proposition: str) -> dict[str, str]:
    """Step 2 of the rule, for one proposition."""

    return {
        "positive": POSITIVE_TEMPLATE.format(prop=proposition),
        "negative": NEGATIVE_TEMPLATE.format(prop=proposition),
    }


def digest(source_text: str) -> str:
    """Step 3 of the rule: over the LF form, encoded UTF-8."""

    return hashlib.sha256(source_text.encode("utf-8")).hexdigest()


def _rows(artifact: dict) -> list[dict]:
    return [row for row in artifact["rows"] if "checker_receipt" in row]


def verify(artifact: dict) -> dict[str, Any]:
    """Run steps 1–3 against every committed row and score the agreement."""

    results = []
    for index, row in enumerate(_rows(artifact)):
        receipt = row["checker_receipt"]
        texts = reconstruct(row["substituted_proposition"])
        results.append(
            {
                "row_index": index,
                "statement_id": row["statement_id"],
                "positive": {
                    "recomputed": digest(texts["positive"]),
                    "recorded": receipt["positive_probe"]["source_sha256"],
                },
                "negative": {
                    "recomputed": digest(texts["negative"]),
                    "recorded": receipt["negative_probe"]["source_sha256"],
                },
            }
        )
    matched = [
        row
        for row in results
        if row["positive"]["recomputed"] == row["positive"]["recorded"]
        and row["negative"]["recomputed"] == row["negative"]["recorded"]
    ]
    return {
        "rows_with_a_receipt": len(results),
        "rows_whose_both_digests_reconstruct": len(matched),
        "mismatches": [
            row
            for row in results
            if row["positive"]["recomputed"] != row["positive"]["recorded"]
            or row["negative"]["recomputed"] != row["negative"]["recorded"]
        ],
    }


def measure_the_gap(artifact_path: Path, artifact: dict) -> dict[str, Any]:
    """The half of the rule the receipt does not carry, counted.

    §12 calls publishing this gap a strengthening of B2. It is measured here —
    the glyph is counted in the artifact's bytes and in its decoded text, and
    the recorded ``pattern`` field is compared against the template this rule
    derives — so the finding is a number rather than a recollection.
    """

    raw = artifact_path.read_bytes()
    text = artifact_path.read_text(encoding="utf-8")
    patterns = sorted(
        {
            row["checker_receipt"]["pattern"]
            for row in _rows(artifact)
            if "pattern" in row["checker_receipt"]
        }
    )
    derived_positive = POSITIVE_TEMPLATE.replace("{prop}", "<prop>").rstrip("\n")
    derived_negative = NEGATIVE_TEMPLATE.replace("{prop}", "<prop>").rstrip("\n")
    return {
        "negation_glyph": "U+00AC NOT SIGN",
        "occurrences_in_artifact_bytes": raw.count("¬".encode("utf-8")),
        "occurrences_in_artifact_text": text.count("¬"),
        "patterns_recorded_in_the_artifact": patterns,
        "recorded_pattern_matches_the_derived_positive_template": (
            patterns == [derived_positive]
        ),
        "derived_positive_template": derived_positive,
        "derived_negative_template": derived_negative,
        "trailing_newline_recorded_anywhere_in_the_artifact": False,
        "unrecorded_half": [
            "the negative template, including the U+00AC glyph and the extra "
            "paren pair it introduces",
            "the single trailing LF both templates append",
            "that the digest is over the LF form rather than over the CRLF "
            "bytes Path.write_text put on disk",
        ],
        "where_the_unrecorded_half_lives": (
            "scripts/conformance_ce3_supplement.py, in the two f-strings that "
            "build positive_source and negative_source"
        ),
        "what_this_means_for_B2": (
            "a reconstructor handed only the artifact can rebuild the POSITIVE "
            "probe from the artifact's own pattern field, and must infer the "
            "NEGATIVE one. The rule is publishable — it is published here — but "
            "it is not self-describing from the receipt, and DESIGN-cold-receipt "
            "§12 records that publishing the gap strengthens B2 rather than "
            "softening it: the floor is met by a rule a reader can execute, not "
            "by a receipt that carries it."
        ),
    }


def transcripts(artifact: dict, count: int) -> list[dict[str, Any]]:
    """The worked transcript, for the first `count` rows.

    The draft's artifact list asks for *one worked stranger-path transcript*.
    The name is the draft's; §12 and §14's first non-claim govern what it may
    be called. What is transcribed here is a **program-absent reconstruction**
    of a probe on this workstation — no person outside this repository is in
    it.
    """

    out = []
    for row in _rows(artifact)[:count]:
        receipt = row["checker_receipt"]
        texts = reconstruct(row["substituted_proposition"])
        out.append(
            {
                "statement_id": row["statement_id"],
                "substituted_proposition": row["substituted_proposition"],
                "positive": {
                    "source_text": texts["positive"],
                    "source_bytes_len": len(texts["positive"].encode("utf-8")),
                    "recomputed_sha256": digest(texts["positive"]),
                    "recorded_sha256": receipt["positive_probe"]["source_sha256"],
                    "recorded_returncode": receipt["positive_probe"]["returncode"],
                },
                "negative": {
                    "source_text": texts["negative"],
                    "source_bytes_len": len(texts["negative"].encode("utf-8")),
                    "recomputed_sha256": digest(texts["negative"]),
                    "recorded_sha256": receipt["negative_probe"]["source_sha256"],
                    "recorded_returncode": receipt["negative_probe"]["returncode"],
                },
                "recorded_verdict": row["decide_verdict"],
            }
        )
    return out


def build_rule(repo: Path) -> dict[str, Any]:
    artifact_path = repo / ARTIFACT
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    checker = artifact.get("checker", {})
    verification = verify(artifact)
    gap = measure_the_gap(artifact_path, artifact)

    meetable = (
        verification["rows_with_a_receipt"] > 0
        and verification["rows_whose_both_digests_reconstruct"]
        == verification["rows_with_a_receipt"]
    )

    rule = {
        "schema": SCHEMA_TAG,
        "design": "docs/DESIGN-cold-receipt.md",
        "prerequisite": "CR-P1",
        "kind_id": "conformance_ce3_supplement:decide_both_directions",
        "source_artifact": ARTIFACT,
        "status_note": (
            "Published BEFORE the general harness, on the WITNESS W1 precedent "
            "(DESIGN-cold-receipt.md §12). This is the rule, not an assertion "
            "that the rows are re-checkable."
        ),
        "steps": [
            {
                "step": 1,
                "name": "proposition",
                "rule": (
                    "take row['substituted_proposition'] verbatim; it is "
                    "already parenthesised and carrier-ascribed, and a "
                    "reconstructor neither re-renders nor re-binds"
                ),
                "needs": [],
            },
            {
                "step": 2,
                "name": "source text",
                "rule": "substitute the proposition into the two templates",
                "positive_template": POSITIVE_TEMPLATE,
                "negative_template": NEGATIVE_TEMPLATE,
                "notes": [
                    "the negation is U+00AC NOT SIGN",
                    "the negative form introduces one extra paren pair inside "
                    "the ': Prop' ascription",
                    "exactly one trailing LF; no import, no header, no BOM",
                ],
                "needs": ["the negative template, which the artifact does not carry"],
            },
            {
                "step": 3,
                "name": "digest",
                "rule": "sha256(source_text.encode('utf-8')) over the LF form",
                "notes": [
                    "the recorded digest covers the in-memory LF string, not "
                    "the file the writer put on disk: Path.write_text "
                    "translated the newline, so the bytes the checker parsed "
                    "on this Windows workstation ended CRLF"
                ],
                "needs": [],
            },
            {
                "step": 4,
                "name": "invocation",
                "rule": (
                    "write the source to <tmp>/Probe.lean and run "
                    "[<lean binary>, <that path>] with cwd=<tmp>"
                ),
                "argv_shape": ["<lean binary>", "<tmp>/Probe.lean"],
                "flags": [],
                "cwd": "<tmp>",
                "environment": "inherited; nothing scrubbed",
                "verdict_from": "returncode == 0, and nothing else",
                "needs": ["the pinned third-party checker binary"],
            },
            {
                "step": 5,
                "name": "verdict",
                "rule": (
                    "(accepted, not accepted) -> refuted_counterexample; "
                    "(not accepted, accepted) -> confirmed_counterexample; "
                    "otherwise did_not_reduce"
                ),
                "needs": [],
            },
        ],
        "what_each_step_needs": {
            "steps_1_to_3": "no program and no checker",
            "step_4": (
                "the pinned third-party binary and nothing of this repository"
            ),
            "step_5": "arithmetic on two integers",
        },
        "checker_pin": {
            "toolchain": checker.get("toolchain"),
            "binary": checker.get("binary"),
            "binary_sha256": checker.get("binary_sha256"),
            "timeout_seconds": checker.get("timeout_seconds"),
        },
        "verification": verification,
        "unrecorded_half_of_the_rule": gap,
        "transcripts": transcripts(artifact, TRANSCRIBED),
        "b2_meetability": {
            "clause": (
                "DESIGN-cold-receipt.md §12: if the rule cannot be published as "
                "a rule, B2's floor of one is not meetable and the slice "
                "publishes that instead of opening"
            ),
            "rule_published_as_a_rule": True,
            "every_committed_row_reconstructs": meetable,
            "b2_floor_meetable": meetable,
        },
        "non_claims": [
            "no stranger-success claim: what is demonstrated is a "
            "program-absent reconstruction on this workstation, and no person "
            "outside this repository is in the instrument",
            "reconstructing a digest is not running the checker; step 4 is "
            "published as a rule here and executed by the harness, not by this "
            "script",
            "nothing here upgrades the C-E3 supplement's own non-claims, which "
            "stand unaltered",
        ],
    }
    rule["provenance"] = provenance_block(Path(__file__), [artifact_path], repo)
    return rule


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    rule = build_rule(REPO)
    text = json.dumps(rule, indent=2, ensure_ascii=False) + "\n"
    if args.out is None:
        sys.stdout.write(text)
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    verification = rule["verification"]
    gap = rule["unrecorded_half_of_the_rule"]
    print(
        f"rows {verification['rows_with_a_receipt']}  "
        f"reconstructed {verification['rows_whose_both_digests_reconstruct']}  "
        f"negation-glyph-in-artifact {gap['occurrences_in_artifact_text']}  "
        f"b2_meetable {rule['b2_meetability']['b2_floor_meetable']}"
    )
    return 0 if rule["b2_meetability"]["b2_floor_meetable"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
