#!/usr/bin/env python3
"""B4 — the untranslatable register, built from the tree and frozen before render.

DESIGN-foreign-voice §3.3 makes this the **headline artifact**, not a
limitations paragraph:

    The register is not a limitations paragraph. It is the artifact a reader
    consults to learn what the graph is silent about, it carries a digest so
    that widening it later is a visible diff, and **B4 makes freezing it a
    precondition of rendering anything**.

and §8: *"Coverage percent is not the headline. The register is. No release
sentence leads with a coverage number. If the register is thin and the
coverage is high, the cycle under-delivered on its actual product."*

## Every class is decided by outcome, not by an author's guess

The design retired an authored blocklist once already — *"a hand-written
eligibility filter measures the filter"* — and the same discipline applies to
the register or the inventory of silence becomes an inventory of expectations.
So:

* **the Mathlib head vocabulary is read out of the oracle's own diagnostics.**
  Every name the pinned binary reported as `Unknown identifier` or `Unknown
  constant` across the whole residue is collected, committed as
  `oracle_unknown_heads`, and a statement carrying one is
  `mathlib_head_vocabulary`.  Nobody wrote that list; the toolchain did.  It
  is why `Nat.Prime` is in it and why nothing is in it that the oracle never
  complained about.
* **`√` is added to that test by rule and the rule is stated**: it is
  Mathlib's notation for a head core Lean does not have, so it fails at the
  *parser* and never reaches the diagnostic that would name it.  A class that
  counted it as pseudo-mathematics would be filing a Mathlib budget
  consequence under a design consequence, and B3 exists precisely to keep
  those two apart.
* **`interpretation_absent` is exactly the set the design's B0b+B0c branch
  clause names** — the Prop-valued and relational corpora — because branch
  (ii) was taken and the clause says those statements carry that reason.
* the remaining classes fall out of the diagnostic: a parse-level rejection is
  `ascii_pseudo_math`, anything else is `typeclass_instance_absent`.

Three further classes cover statements the oracle ACCEPTED and the lexicon
still cannot say: `coercion`, `unsupported_numeral`, `noncanonical_numeral`.
They are the honest cost of a frozen table and a registered numeral pair, and
they are in the register rather than in a footnote for the same reason
everything else is.

## B3's arithmetic, and the two buckets that are never summed

    transliterable + covered + registered_blocked_mathlib_head
                             + registered_blocked_no_row  =  10,605  exactly

*"The two `registered_blocked_*` buckets are reported separately, never summed
into one number: the first is a budget consequence the maintainer can lift and
the second is a design consequence this cycle owns, and merging them would
hide which is which."*  This module keeps them in different fields and the
builder refuses if the total does not close.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - CLI import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import numeral_words as nw  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
PREVIEW_PATH = REPO_ROOT / "data" / "foreign_voice" / "eligibility_preview.json"
LEXICON_PATH = REPO_ROOT / "data" / "foreign_voice" / "lexicon.json"
RULE_PATH = REPO_ROOT / "data" / "foreign_voice" / "rule_r.json"
DEFAULT_OUT = REPO_ROOT / "data" / "foreign_voice" / "register.json"

#: B3's two blocked buckets. Kept as constants because the one thing that must
#: never happen to them is being added together.
MATHLIB_BUCKET = "registered_blocked_mathlib_head"
NO_ROW_BUCKET = "registered_blocked_no_row"

#: The seven corpora the B0b+B0c branch clause names. Under branch (ii) every
#: one of their residue statements is `registered_blocked_no_row` with reason
#: `interpretation_absent`.
PROP_CORPORA = ("graph_theory", "logic", "narrative", "programming",
                "provability", "set_theory", "temporal_logic")

#: Mathlib's notation for a head core Lean does not have. It fails at the
#: parser, so the oracle never gets to name it — see the module docstring.
NOTATION_HEADS = ("√",)

_UNKNOWN_RE = re.compile(r"Unknown (?:identifier|constant) .(.+?).$")
_PARSE_ERROR = ("unexpected token", "expected token", "Function expected")
_NUMERAL_RE = re.compile(r"\d+(?:\.\d+)?")


class RegisterError(ValueError):
    """The census does not close, or a class was authored rather than measured."""


def _digest_ids(ids: list[str]) -> str:
    """Digest of a blocked set: sorted, LF-joined, so it is order-independent."""
    return hashlib.sha256(
        ("\n".join(sorted(ids)) + "\n").encode("utf-8")).hexdigest()


def oracle_unknown_heads(rejected: list[dict]) -> list[str]:
    """Every head the PINNED BINARY named. Nobody authored this list."""
    heads: set[str] = set()
    for row in rejected:
        match = _UNKNOWN_RE.match(row["error"])
        if match:
            heads.add(match.group(1))
    return sorted(heads)


def _carries_head(text: str, heads: list[str]) -> bool:
    for head in heads:
        if re.search(rf"(?<![A-Za-z0-9_.]){re.escape(head)}(?![A-Za-z0-9_'])", text):
            return True
    return any(glyph in text for glyph in NOTATION_HEADS)


def _numeral_problem(text: str) -> str:
    """`unsupported_numeral`, `noncanonical_numeral`, or the empty string."""
    for match in _NUMERAL_RE.finditer(text):
        literal = match.group(0)
        if "." in literal:
            value = float(literal)
            if repr(value) != literal:
                return "noncanonical_numeral"
            try:
                nw.number_to_words(value)
            except nw.NumeralError:
                return "unsupported_numeral"
            continue
        try:
            nw.int_to_words(int(literal))
        except nw.NumeralError:
            return "unsupported_numeral"
    return ""


def classify(preview: dict, refusal_glyphs: list[str]) -> dict[str, list[dict]]:
    """Every residue statement into exactly one class. Raises if one lands in two."""
    statements = preview["statements"]
    rejected = [row for row in statements if not row["accepted"]]
    accepted = [row for row in statements if row["accepted"]]
    heads = oracle_unknown_heads(rejected)

    classes: dict[str, list[dict]] = {}

    def put(name: str, row: dict) -> None:
        classes.setdefault(name, []).append(row)

    for row in rejected:
        if _carries_head(row["interpreted"], heads):
            put("mathlib_head_vocabulary", row)
        elif row["corpus"] in PROP_CORPORA:
            put("interpretation_absent", row)
        elif row["error"].startswith(_PARSE_ERROR):
            put("ascii_pseudo_math", row)
        else:
            put("typeclass_instance_absent", row)

    for row in accepted:
        glyph = next((g for g in refusal_glyphs if g in row["interpreted"]), "")
        if glyph:
            put("coercion", row)
            continue
        problem = _numeral_problem(row["interpreted"])
        if problem:
            put(problem, row)

    return classes


#: register_id -> the fixed prose the entry carries. Written once, here, so a
#: reader of the register meets the reason and not a code name.
_ENTRY_PROSE: dict[str, dict] = {
    "mathlib_head_vocabulary": {
        "dialect_construct": "namespaced and bare Mathlib heads, and the √ notation",
        "bucket": MATHLIB_BUCKET,
        "reason": "oracle_rejected",
        "why": [
            "No row can be authored because there is nothing to author a row TO.",
            "DESIGN-external-verifier:40 states it as design law — 'Core Lean",
            "only: Mathlib is not installable within the hermetic budget' — and",
            "the pinned toolchain confirms it: `#check Real.sqrt` returns Unknown",
            "identifier. Correction 2(b) narrowed this from the first draft's 'no",
            "ℝ': the TYPE glyphs are carried by rule R, the HEAD vocabulary is",
            "not.",
            "This is a BUDGET consequence, not a design consequence. The",
            "maintainer can lift it by deciding the Mathlib question; this cycle",
            "cannot and does not."
        ],
        "revisit_trigger": (
            "a decision on the Mathlib budget. Until then this entry is the "
            "single largest thing the graph cannot say, and every sentence "
            "quoting a coverage number owes it."
        ),
    },
    "interpretation_absent": {
        "dialect_construct": "propositional, modal, provability and set-theoretic statements",
        "bucket": NO_ROW_BUCKET,
        "reason": "interpretation_absent",
        "why": [
            "B0b+B0c's branch (ii), taken at B0 time and recorded in rule_r.json",
            "before any render. Rule R binds free identifiers at Rat and these",
            "statements are propositions, so none of them elaborates.",
            "The branch was chosen on a measurement, not a preference. A",
            "deliberately generous second interpretation — rewriting the ASCII",
            "connective vocabulary into core Lean's and binding every remaining",
            "free identifier at Prop — reaches 13 of these 75: 12 logic rows and",
            "one narrative row. Thirteen moves the covered set from 99.87% one",
            "corpus to 99.31% one corpus, which is not the outcome the design",
            "gives as the honest reason to prefer branch (i).",
            "The other 62 are not out for want of table rows. temporal_logic",
            "needs always/eventually/until/next/since/once/historically,",
            "provability needs provable/falsum/Con and a turnstile, set_theory",
            "needs inter/union/complement/emptyset/subset/CARD, narrative and",
            "programming carry English prose and Python-shaped conditionals, and",
            "the remaining logic rows need a genuine dependent binder. Reaching",
            "them means axiomatising those constants inside the preamble, and",
            "then the oracle is adjudicating a theory this repository wrote."
        ],
        "revisit_trigger": (
            "a design that says what licenses axiomatising a modal, "
            "provability or set-theoretic signature inside the preamble "
            "without the oracle grading this repository's own theory."
        ),
    },
    "ascii_pseudo_math": {
        "dialect_construct": "house ASCII notation that is not Lean in any alphabet",
        "bucket": NO_ROW_BUCKET,
        "reason": "interpretation_absent",
        "why": [
            "These statements are not a foreign dialect of the same grammar;",
            "they are a different notation entirely — subscripted sums written",
            "`sum_(i=0)^(n)`, cardinality bars, `iso`, `whenever`, `o` for",
            "composition, and in places English prose. The pinned binary rejects",
            "them at the PARSER, before any interpretation could apply.",
            "A row cannot be authored because a row maps a constructor to a",
            "phrase, and these carry no constructor the oracle can name."
        ],
        "revisit_trigger": (
            "a design for reading this repository's own ASCII mathematical "
            "notation, which is a parser question and not a lexicon question."
        ),
    },
    "typeclass_instance_absent": {
        "dialect_construct": "variable exponents and other terms core Lean cannot instantiate",
        "bucket": NO_ROW_BUCKET,
        "reason": "oracle_rejected",
        "why": [
            "These parse and then fail to elaborate: `(1 : Rat) ^ m` with `m` a",
            "rational needs an `HPow Rat Rat Rat` instance core Lean does not",
            "have, `Nat.Prime` is not a core constant, and a handful hit a type",
            "mismatch or a stuck instance problem.",
            "It is a DESIGN consequence rather than a budget one only in the",
            "narrow sense that rule R chose to bind every regenerated binder at",
            "one type. A per-identifier type decision would reach some of these",
            "and would also be the preamble doing semantic work, which is the",
            "thing rule R exists to avoid."
        ],
        "revisit_trigger": (
            "a rule R successor that assigns preamble types per identifier, "
            "with its own digest and its own re-run — and with an argument for "
            "why that is not the preamble deciding what the statement means."
        ),
    },
    "coercion": {
        "dialect_construct": "the coercion arrow ↑",
        "bucket": NO_ROW_BUCKET,
        "reason": "no_lexicon_row",
        "why": [
            "The oracle ACCEPTS these; the lexicon refuses them. An up-arrow is",
            "a request to insert a coercion whose target type the elaborator",
            "chooses, so a phrase for it would mean something a reader cannot see",
            "and the inverse would name a coercion this table cannot commit to.",
            "The refusal row is in data/foreign_voice/lexicon.json, which is why",
            "the renderer refuses at the surface rather than improvising."
        ],
        "revisit_trigger": (
            "a lexicon row that names the coercion's target type explicitly, "
            "which requires the renderer to see the elaborated term and would "
            "make the forward direction depend on the oracle."
        ),
    },
    "unsupported_numeral": {
        "dialect_construct": "an integer literal outside the registered numeral pair's domain",
        "bucket": NO_ROW_BUCKET,
        "reason": "unsupported_numeral",
        "why": [
            "scripts/numeral_words registers integers with abs < 10^15. One",
            "eligible statement carries a 433-digit literal. The pair refuses it",
            "rather than approximating, which is the same refusal v0.18 already",
            "ships for its own two long literals."
        ],
        "revisit_trigger": (
            "extending numeral_words' SCALES table, which is a reviewed diff "
            "with tests and moves a digest the prereg freezes."
        ),
    },
    "noncanonical_numeral": {
        "dialect_construct": "a decimal literal whose spelling the numeral pair cannot reproduce",
        "bucket": NO_ROW_BUCKET,
        "reason": "noncanonical_numeral",
        "why": [
            "One eligible statement carries `23.50` and `39.50`. The registered",
            "pair is exact rather than approximately exact — it renders the",
            "canonical `23.5` — and `23.50` and `23.5` are DIFFERENT",
            "`OfScientific` terms to the elaborator, so a round trip through the",
            "pair would produce a term the corpus did not write and B1 would",
            "score it as a failure of the renderer.",
            "Refusing is the honest reading: the sentence would have been right",
            "about the number and wrong about the term."
        ],
        "revisit_trigger": (
            "a numeral pair that carries trailing-zero precision, which would "
            "widen the accepted word language beyond the emitted one unless the "
            "canonicality check is widened with it."
        ),
    },
}


def build(preview_path: Path = PREVIEW_PATH,
          lexicon_path: Path = LEXICON_PATH,
          rule_path: Path = RULE_PATH) -> dict:
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    lexicon = json.loads(lexicon_path.read_text(encoding="utf-8"))
    rule = json.loads(rule_path.read_text(encoding="utf-8"))
    refusal_glyphs = sorted(lexicon.get("refusals", {}))

    rejected = [row for row in preview["statements"] if not row["accepted"]]
    classes = classify(preview, refusal_glyphs)

    unknown = set(classes) - set(_ENTRY_PROSE)
    if unknown:
        raise RegisterError(
            f"{sorted(unknown)} have no committed entry prose; a class with no "
            f"reason written down is a code name, not an inventory of silence"
        )

    entries = []
    for register_id in sorted(classes):
        rows = classes[register_id]
        prose = _ENTRY_PROSE[register_id]
        ids = sorted(row["statement_id"] for row in rows)
        witness = min(rows, key=lambda r: r["statement_id"])
        entries.append({
            "register_id": register_id,
            "dialect_construct": prose["dialect_construct"],
            "construct_class": register_id,
            "bucket": prose["bucket"],
            "reason": prose["reason"],
            "blocking_count": len(ids),
            "blocked_statement_set_digest": _digest_ids(ids),
            "surface_witness": {
                "statement_id": witness["statement_id"],
                "corpus": witness["corpus"],
                "source": witness["source"],
                "interpreted": witness["interpreted"],
                "oracle_said": witness["error"] or "(accepted; the lexicon refuses it)",
            },
            "per_corpus": dict(sorted(Counter(row["corpus"] for row in rows).items())),
            "decided_at": "2026-08-24",
            "frozen_before_render": True,
            "why": prose["why"],
            "revisit_trigger": prose["revisit_trigger"],
            "statement_ids": ids,
        })

    mathlib = sum(e["blocking_count"] for e in entries if e["bucket"] == MATHLIB_BUCKET)
    no_row = sum(e["blocking_count"] for e in entries if e["bucket"] == NO_ROW_BUCKET)
    totals = preview["b0a"]["totals"]
    transliterable = totals["transliterable"]
    residue = totals["residue"]
    accepted = preview["b0bc"]["accepted"]
    covered = accepted - sum(
        e["blocking_count"] for e in entries
        if e["register_id"] in {"coercion", "unsupported_numeral",
                                "noncanonical_numeral"})
    census = transliterable + covered + mathlib + no_row
    if census != totals["mute"]:
        raise RegisterError(
            f"B3 does not close: {transliterable} + {covered} + {mathlib} + "
            f"{no_row} = {census}, not {totals['mute']}. A statement in none of "
            f"those buckets is a bug in the census, not a rounding difference."
        )
    if mathlib + no_row != residue - covered:
        raise RegisterError("the blocked buckets do not account for the residue")

    all_ids = [sid for entry in entries for sid in entry["statement_ids"]]
    if len(set(all_ids)) != len(all_ids):
        raise RegisterError("a statement is registered under two classes")

    return {
        "register_id": "foreign_voice.register.v1",
        "frozen_at": "2026-08-24",
        "design": "docs/DESIGN-foreign-voice.md",
        "gate": "B4 — the register is frozen first",
        "what_this_is": [
            "The inventory of what this cycle's graph cannot say, with the",
            "blocking construct named and counted, frozen and digested BEFORE",
            "anything is rendered. §3.3: 'The register is not a limitations",
            "paragraph.' §8: 'Coverage percent is not the headline. The register",
            "is.'",
            "B4: a post-freeze entry is permitted only as a DATED AMENDMENT",
            "COMMIT THAT RE-RUNS B1 FROM SCRATCH. An amendment chased after",
            "reading B1 is §8's stop condition."
        ],
        "how_the_classes_were_decided": [
            "By outcome, not by an author's guess. The Mathlib head vocabulary",
            "below is every name the PINNED BINARY reported as an unknown",
            "identifier or constant across the whole residue — nobody wrote that",
            "list, which is why Nat.Prime is in it and why nothing is in it that",
            "the oracle never complained about.",
            "√ is added to that test by a stated rule: it is Mathlib's notation",
            "for a head core Lean does not have, so it fails at the PARSER and",
            "never reaches the diagnostic that would name it. Counting it as",
            "pseudo-mathematics would file a budget consequence under a design",
            "consequence, and B3 exists to keep those apart.",
            "interpretation_absent is exactly the set B0b+B0c's branch clause",
            "names, because branch (ii) was taken."
        ],
        "lexicon_digest_at_freeze": _sha256_lf(lexicon_path),
        "interpretation_digest_at_freeze": _sha256_lf(rule_path),
        "eligibility_preview_digest_at_freeze": _sha256_lf(preview_path),
        "lexicon_id": lexicon["lexicon_id"],
        "rule_id": rule["rule_id"],
        "prop_branch": rule["prop_branch"]["decision"],
        "oracle_unknown_heads": oracle_unknown_heads(rejected),
        "oracle_unknown_heads_note": (
            "Read out of the pinned binary's own diagnostics over the 4,191 "
            "residue statements. This is the list, and it is measured."
        ),
        "notation_heads": list(NOTATION_HEADS),
        "b3_census": {
            "note": [
                "The two registered_blocked_* buckets are reported separately and",
                "NEVER summed: the first is a budget consequence the maintainer",
                "can lift, the second is a design consequence this cycle owns,",
                "and merging them would hide which is which.",
                "These are PREVIEW figures. `covered` is the renderable set",
                "before anything has been rendered; the registered run splits it",
                "into covered_served and covered_failed and the census closes",
                "again at 10,605."
            ],
            "transliterable": transliterable,
            "covered": covered,
            MATHLIB_BUCKET: mathlib,
            NO_ROW_BUCKET: no_row,
            "total": census,
            "must_equal": totals["mute"],
            "closes_exactly": True,
        },
        "blocked_set_digest": _digest_ids(all_ids),
        "blocked_total": len(all_ids),
        "entries": entries,
    }


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    try:
        register = build()
    except RegisterError as exc:
        print(f"register refused: {exc}", file=sys.stderr)
        return 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(register, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    census = register["b3_census"]
    for entry in register["entries"]:
        print(f"  {entry['blocking_count']:6d}  {entry['bucket']:33s} "
              f"{entry['register_id']}")
    print(f"\nB3  transliterable {census['transliterable']}  "
          f"covered {census['covered']}  "
          f"mathlib_head {census[MATHLIB_BUCKET]}  "
          f"no_row {census[NO_ROW_BUCKET]}  = {census['total']}")
    print(f"written to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
