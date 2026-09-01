#!/usr/bin/env python3
"""HOUSE RULES — H-PRE, the fixture seal. Bytes and expectations, no checker.

Design pointer: ``docs/DESIGN-house-rules.md`` — §3 (the two record shapes and
the committed clause order), §6 step 1 (**H-PRE**: this artifact, its floors,
and the U-PRE-style deletion rule), §7 (B3's ≥30 containment mutants, B9's
sealed class balance and split rule, B12's reserved-prefix-adjacent mutants),
§9 (the stop conditions this seal is later adjudicated against). Roadmap:
``docs/ROADMAP-v0.25.md#1``. Precedent for the shape: U-PRE,
``experiments/protocol_uptake_upre.json`` — candidate rows survive with a
reason or are deleted with a reason, sealed *before* any checker exists.

**There is no parser here and there must not be one.** H-PRE seals the
authored surface bytes of `declare` and `suppose` lines together with the
verdict each one is expected to receive. The checker that consumes them is
H-P0's (`scripts/symbol_ledger.py`), and §9's stop condition — "the
declaration form cannot express the sealed fixtures inside the registered
grammar without parser exceptions" — is adjudicated at H-P0 *against these
bytes*. A seal that also parsed would be scoring its own homework.

What this script does compute, rather than assert:

* the nine argument categories are **read out of**
  ``schema/equation-node.schema.json`` (`$defs.symbolToken.syntactic_category`),
  never transcribed, so a schema edit moves this artifact and reddens the
  regeneration test instead of silently drifting from it;
* every count, every session's admitted/refused arithmetic, the arity and
  category coverage, the B9 class balance and its two halves — all derived
  from the authored turn list below;
* the construction floors are **checked**, and a violated floor raises
  `ConstructionRefusal` rather than writing a file that claims a floor it
  does not meet.

The floors themselves (≥8 admitted, ≥3 arities, ≥4 categories, ≥30 B3
mutants) are **declared construction bounds, not measurements**, and the
artifact says so in its own bytes. These fixtures license no population claim
about what people will declare.

Determinism: no wall clock, no randomness, no environment reads. The date is a
committed constant; the only file read is the committed schema. Re-running
reproduces the committed JSON byte for byte, which
``tests/test_house_rules_fixtures.py`` scores.

Usage
-----

    python scripts/build_house_rules_fixtures.py
    python scripts/build_house_rules_fixtures.py --out /tmp/fixtures.json
    python scripts/build_house_rules_fixtures.py --check
    python scripts/build_house_rules_fixtures.py --summary
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any, Sequence

REPO = Path(__file__).resolve().parents[1]

SCHEMA = "corollary.house-rules-fixtures/1"
STAGE = "H-PRE"
DATE = "2026-09-01"
DESIGN = "docs/DESIGN-house-rules.md"
DESIGN_CLAUSE = "§6 step 1 — H-PRE, the fixture seal; floors from §6.1, gates from §7 B3/B9/B12."
ROADMAP = "docs/ROADMAP-v0.25.md#1"
GENERATOR = "scripts/build_house_rules_fixtures.py"
PRECEDENT = "experiments/protocol_uptake_upre.json"

#: WHERE THIS BUILDER LIVES, and why it moved at H-P0.
#:
#: `scripts/**/*.py` is the COLD program tree — the exact glob
#: `cold_registry_census.PROGRAM_TREE_GLOB` seals and the cold attestation
#: attests. At H-PRE this file sat in `experiments/` for a measured reason:
#: adding one file to that glob moves `program_tree_files_scanned`, which
#: `tests.test_cold_receipt` recomputes, so a fixture seal placed there would
#: have landed RED — and the repair was worse, because re-sealing the census
#: breaks `cold/census_run2.json`'s provenance and forces a re-run of a
#: registered cold attestation as a side effect of committing fixtures.
#:
#: H-P0 pays that bill for its own reasons: it adds `scripts/symbol_ledger.py`,
#: `scripts/build_symbol_census.py` and `scripts/check_symbol_census.py` to the
#: program tree, so the census MUST be re-sealed and the cold reading MUST
#: re-attest whatever else this file does. H-PRE said the move would then cost
#: nothing, and that turned out to be exactly right: it rides a re-seal that
#: was already owed. So the builder now sits in the program tree with the rest
#: of this repository's generators, and the artifact's `generator` field moves
#: with it — written by the builder, never edited into the artifact by hand.
#:
#: What did NOT change: this builder still ships no runtime and still sits on
#: no admission path. DESIGN §5's "trusted, exact code — new" names the H-P0
#: census builder and checker, never this one.
PLACEMENT_NOTE = (
    "Moved into scripts/**/*.py at H-P0, as H-PRE said it could be. The COLD "
    "program tree's file count moves when a file is added to it, so H-PRE kept "
    "this builder outside it rather than redden tests.test_cold_receipt for a "
    "fixture seal; H-P0 adds three runtime modules to that tree for its own "
    "reasons, so the CR-P0 re-seal and the cold re-attestation were owed "
    "anyway and this move rides them at no additional cost. The builder ships "
    "no runtime and sits on no admission path either way."
)

SOURCE_COMMIT = "249f4630fa57c6c42f5f89deebb1bce53b53657c"

SCHEMA_PATH = "schema/equation-node.schema.json"

DEFAULT_OUT = "experiments/house_rules_fixtures.json"

#: The module H-P0 will own. It does not exist at this commit and H-PRE
#: registers that it must not: a fixture seal written after its checker is a
#: seal fitted to a checker.
CHECKER_MODULE = "scripts/symbol_ledger.py"

#: DESIGN §3, quoted in order. First hit decides — which is what makes
#: "exactly one deciding clause" true rather than asserted.
CLAUSE_ORDER: tuple[tuple[str, str], ...] = (
    ("c1_unparsed", "UNPARSED"),
    ("c2_arity_category_mismatch", "ARITY_CATEGORY_MISMATCH"),
    ("c3_category_not_in_schema", "CATEGORY_NOT_IN_SCHEMA"),
    ("c4_reserved_prefix", "RESERVED_PREFIX"),
    ("c5_collides_with_library_symbol", "COLLIDES_WITH_LIBRARY_SYMBOL"),
    ("c6_redefinition_attempt", "REDEFINITION_ATTEMPT"),
    ("c7_collides_with_session_name", "COLLIDES_WITH_SESSION_NAME"),
    ("c8_symbol_budget", "SYMBOL_BUDGET"),
)

#: Admission is the committed order's *only* fall-through, and it is named so
#: that B1's "exactly one deciding_clause, zero fall-throughs" is checkable on
#: admissions too rather than only on refusals.
ADMIT_CLAUSE = "c9_admit"
ADMIT_VERDICT = "ADMITTED_DECLARED_SYMBOL"
REFUSED = "REFUSED"

CLAUSE_BY_CODE = {code: clause for clause, code in CLAUSE_ORDER}
CLAUSE_RANK = {code: index for index, (_, code) in enumerate(CLAUSE_ORDER)}

#: DESIGN §3: at most four admitted symbols per session. Declared, not
#: measured. The fifth is SYMBOL_BUDGET, refused before any ledger mutation.
SESSION_ADMITTED_CAP = 4

#: DESIGN §6.1 floors. Declared construction bounds, not measurements.
FLOOR_ADMITTED = 8
FLOOR_ARITIES = 3
FLOOR_CATEGORIES = 4
FLOOR_B3_MUTANTS = 30

#: Use-side dispositions (DESIGN §3, B6). `USE_ARITY_MISMATCH` is a refusal
#: name in the *supposition ledger's* vocabulary beside `assumption_budget` /
#: `unknown_assumption` (`scripts/session_ledger.py:120-122`). It is not an
#: `AdmissibilityVerdict.refusal_code` and is deliberately absent from
#: CLAUSE_ORDER above.
USE_CHECKED = "CHECKED_SUPPOSITION"
USE_ARITY_MISMATCH = "USE_ARITY_MISMATCH"
USE_OPAQUE = "OPAQUE_ATOM"

#: A binding supposition (`suppose x = 5`) is not a use of a declared symbol at
#: all. It predates this slice and this slice does not touch it. Giving it the
#: slice's positive disposition would apply a verdict to a turn the capability
#: never sees, so it gets its own name and is excluded from B6's counts.
USE_BINDING_UNCHANGED = "BINDING_SUPPOSITION_UNCHANGED"

USE_DISPOSITIONS = (USE_CHECKED, USE_ARITY_MISMATCH, USE_OPAQUE, USE_BINDING_UNCHANGED)

#: Normalization, applied by this generator rather than described by it. The
#: design's rule is "NFC, casefold, [a-z][a-z0-9_]*" — an ORDER, not a set of
#: three independent facts, and the order is load-bearing: `SUM_TOTAL` parses
#: DESPITE not matching the production while `2parent` is refused BECAUSE it
#: does not, and only normalize-then-match makes both true at once. H-PRE seals
#: that order with fixtures whose verdicts differ under any other reading.
NORMALIZATION_ORDER = (
    "NFC, then casefold, then match [a-z][a-z0-9_]* against the RESULT. The order is "
    "sealed because fixtures disagree under any other one: `SUM_TOTAL` is admitted as "
    "`sum_total` though the raw bytes match no production, and a casefold expansion "
    "(U+FB01 -> `fi`, U+00DF -> `ss`) can carry a surface INTO the production that the "
    "raw bytes are outside of."
)


def normalize_name(raw: str) -> str:
    """The one normalization both sides of every comparison run (DESIGN §4)."""

    return unicodedata.normalize("NFC", raw).casefold()

#: The parser prefixes the census carries as a *prefix guard* (DESIGN §4,
#: `scripts/match_signatures.py` `BIG_OP_PREFIXES`). Recorded here as the
#: authored fixtures' target, not as a census: H-P0's census builder is the
#: authority and this seal is one of the things it will be checked against.
RESERVED_PREFIXES = ("sum_", "prod_", "lim_", "max_", "min_")


class ConstructionRefusal(RuntimeError):
    """A floor this seal cannot meet honestly. DESIGN §9 — stop, do not write."""


# --------------------------------------------------------------------------
# The collision targets that have to be real.
# --------------------------------------------------------------------------

#: DESIGN §7 B2: "a fixture head equal to a casefolded corpus call head must
#: refuse COLLIDES_WITH_LIBRARY_SYMBOL". A fixture naming an invented head
#: would score nothing, so each target below was verified present in the
#: committed graph *today* and carries the source that H-P0's census will
#: reach it through. If H-P0's census does not contain one of these, the
#: expectation here is falsified — and that is a finding about the census
#: builder, not a licence to edit this file.
LIBRARY_COLLISION_TARGETS: tuple[dict[str, str], ...] = (
    {
        "name": "gcd",
        "reached_by": "symbol_lexicon.functionals leading identifier; anonymized_template call head; COMMUTATIVE_CALL_HEADS",
        "provenance": (
            "Member of symbol_lexicon.functionals as `GCD(.,.)` (\"greatest common "
            "divisor\", 2 occurrences) in data/programming/nodes.json, node "
            "`programming.euclid.recursive`; leading identifier `gcd`. Independently a "
            "call head `GCD` in 2 committed anonymized_templates (4 applications). "
            "Independently a member of COMMUTATIVE_CALL_HEADS = {GCD, JOIN, MEET, MINOF, "
            "TOUCHES} (scripts/match_signatures.py:276-279). All three casefold to `gcd`."
        ),
        "why_the_census_must_contain_it": (
            "Three of §4's census bullets reach it independently, so the expectation "
            "survives even if one bullet is implemented differently than assumed."
        ),
    },
    {
        "name": "meet",
        "reached_by": "symbol_lexicon.functionals leading identifier; anonymized_template call head; COMMUTATIVE_CALL_HEADS",
        "provenance": (
            "Member of symbol_lexicon.functionals as `MEET(.,.)` (\"lattice meet\", 37 "
            "occurrences across 9 corpus files), e.g. data/algebraic_topology/nodes.json, "
            "node `algtop.invariants.euler_characteristic_valuation`. Independently the "
            "most frequent call head in the corpus: `MEET` in 8,160 of 12,777 committed "
            "anonymized_templates (22,653 applications). Independently in "
            "COMMUTATIVE_CALL_HEADS."
        ),
        "why_the_census_must_contain_it": (
            "The highest-frequency head in the corpus. A census that missed `meet` would "
            "have missed two thirds of the committed trees."
        ),
    },
    {
        "name": "implies",
        "reached_by": "symbol_lexicon.operators (bare, already name-shaped); symbol_lexicon.functionals leading identifier; anonymized_template call head",
        "provenance": (
            "Member of symbol_lexicon.operators as the bare token `implies` — name-shaped "
            "with no extraction needed, and the only one of these three targets reachable "
            "through a NON-functional route — and of symbol_lexicon.functionals as "
            "`IMPLIES(.,.)` (35 occurrences across 8 corpus files, e.g. "
            "data/logic/nodes.json). Independently the call head `IMPLIES` in 9,403 of "
            "12,777 committed anonymized_templates."
        ),
        "why_the_census_must_contain_it": (
            "It exercises the operators category, which the design notes is carried mostly "
            "as un-collidable glyphs; `implies` is one of the 23 name-shaped operators and "
            "proves that category is not inert."
        ),
    },
    {
        "name": "sum_i",
        "reached_by": "symbol_lexicon.functionals (whole member string is name-shaped); and BIG_OP_PREFIXES as a prefix guard",
        "provenance": (
            "One of exactly two name-shaped members of symbol_lexicon.functionals (`lim` "
            "and `sum_i`; every other functional notation carries parens or dots). It is "
            "also the literal token behind sixteen of the corpus's seventeen big-op "
            "captures — `EULERCHAR = sum_i COEFF_i*BETTI_i` in "
            "`algtop.homology.betti_alternating_sum` and fifteen siblings."
        ),
        "why_the_census_must_contain_it": (
            "It is the ONE verified name that is simultaneously a census member and a "
            "reserved-prefix match, which is what makes the RESERVED_PREFIX-before-"
            "COLLIDES_WITH_LIBRARY_SYMBOL order-sensitivity fixture real rather than "
            "hypothetical."
        ),
    },
    {
        "name": "sum",
        "reached_by": "anonymized_template call head; HEAD_ALIASES key",
        "provenance": (
            "A lowercase call head in 16 committed anonymized_templates — synthetic, "
            "produced by the big-op branch itself (`head = tok.lower().split(\"_\", 1)[0]`, "
            "scripts/match_signatures.py:551), so every `sum` head in the corpus comes from "
            "a literal `sum_i` token. Independently the one lowercase key of HEAD_ALIASES, "
            "aliased to `aggregate` (scripts/match_signatures.py:870-877). The corpus also "
            "carries an ordinary uppercase head `SUM`, which casefolds onto the same name."
        ),
        "why_the_census_must_contain_it": (
            "`sum` is the prefix minus its underscore, so the prefix guard does NOT reach "
            "it — the census must, or the hazard's own root name would be admitted."
        ),
    },
)

#: Verifying the targets above against the committed graph and parser turned up
#: three things the design's prose does not say, and one it says slightly wrong.
#: They are recorded here because H-P0's census builder is the consumer, and a
#: seal that quietly worked around a stale citation would hand H-P0 the same
#: surprise. None of them changes a fixture expectation.
CENSUS_SOURCE_FINDINGS: tuple[dict[str, str], ...] = (
    {
        "finding": "the design's `parse_sum` citation names the wrong method",
        "detail": (
            "DESIGN §4 places the big-op branch in `parse_sum` around "
            "match_signatures.py:541-563. The LINE RANGE is exact; the method is "
            "`Parser.parse_atom` (line 527). `parse_sum` is at line 495 and is the "
            "additive-precedence production. H-P0's census builder should read parse_atom."
        ),
        "affects_a_fixture_expectation": "no",
    },
    {
        "finding": "the design's `rank(·)` / `closure(·)` spelling is not the committed spelling",
        "detail": (
            "The committed functional notations are `RANK(.)` and `CLOSURE(.)` — uppercase "
            "head, ASCII full stop. Only `E[·]` and `sqrt(·)` use U+00B7 anywhere in the "
            "corpus. The design's ILLUSTRATION is off; its claim is not: the casefolded "
            "leading identifiers `rank` and `closure` are correct, and both were verified "
            "reachable through no other census bullet, which is that bullet's whole "
            "justification."
        ),
        "affects_a_fixture_expectation": "no",
    },
    {
        "finding": "the census will contain a collision with itself",
        "detail": (
            "The corpus carries uppercase call heads `SUM` and `LIM` as ordinary heads AND "
            "the synthetic lowercase heads `sum` and `lim` the big-op branch produces. "
            "After NFC + casefold these are one member each. That is a census-internal "
            "merge, not a defect, but a census builder that asserts distinctness before "
            "normalizing will trip on it."
        ),
        "affects_a_fixture_expectation": "no",
    },
    {
        "finding": "the functional leading-identifier rule is under-specified for `sum_i`",
        "detail": (
            "Of 95 functional notations, all 95 yield a name-shaped leading identifier and "
            "89 are distinct. Under `^[a-z][a-z0-9_]*` the extraction swallows the "
            "underscore and yields `sum_i`, not `sum`. H-PRE seals BOTH names as census "
            "members with independent provenance — `sum_i` as the functional, `sum` as the "
            "call head and HEAD_ALIASES key — so the fixture expectations hold under either "
            "reading of the extraction rule. H-P0 still owes the rule in writing."
        ),
        "affects_a_fixture_expectation": "no",
    },
)


# --------------------------------------------------------------------------
# The schema's category enum, read rather than transcribed.
# --------------------------------------------------------------------------


def sha256_lf(path: Path) -> str:
    """The digest every prereg in this repository records."""

    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def schema_categories(repo: Path) -> tuple[str, ...]:
    document = json.loads((repo / SCHEMA_PATH).read_text(encoding="utf-8"))
    enum = document["$defs"]["symbolToken"]["properties"]["syntactic_category"]["enum"]
    if len(enum) != 9:
        raise ConstructionRefusal(
            f"{SCHEMA_PATH} syntactic_category holds {len(enum)} members; the design "
            "cites a nine-member enum and every fixture category is drawn from it"
        )
    return tuple(enum)


# --------------------------------------------------------------------------
# Authored turns. Surface bytes exactly as DESIGN §6.2 registers the row:
#     declare <name>/<arity> (<category>, ...)
# Nothing below is parsed here; `name` / `arity` / `categories` are the
# author's *reading* of the line, sealed beside it so H-P0's parser can be
# scored against a reading it did not produce.
# --------------------------------------------------------------------------


def _decl(
    line: str,
    *,
    name: str | None,
    arity: int | None,
    categories: Sequence[str] | None,
    code: str,
    also: Sequence[str] = (),
    why: str,
    subcase: str | None = None,
    raw_name: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": "declaration",
        "line": line,
        # The surface identifier before normalization, where it differs from the
        # normalized name. This is what makes the NFC/casefold order checkable.
        "raw_symbol_name": raw_name,
        "read_symbol_name": name,
        "read_arity": arity,
        "read_argument_categories": list(categories) if categories is not None else None,
        "expected_refusal_code": code,
        "also_grounds_for": list(also),
        # Which member of DESIGN §4's three-source session-name union this line
        # reaches, where it reaches one. Named per fixture so the three cannot
        # be collapsed into "two codes are present".
        "session_name_subcase": subcase,
        "rationale": why,
    }


def _admit(
    line: str,
    name: str,
    arity: int,
    categories: Sequence[str],
    why: str,
    raw_name: str | None = None,
) -> dict[str, Any]:
    return _decl(
        line, name=name, arity=arity, categories=categories, code="NONE", why=why,
        raw_name=raw_name,
    )


def _use(
    line: str,
    *,
    head: str | None,
    argument_count: int | None,
    disposition: str,
    declares: str | None,
    why: str,
    binds: str | None = None,
    round_trip_for: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": "use",
        "line": line,
        "read_applied_head": head,
        "read_argument_count": argument_count,
        "expected_disposition": disposition,
        "expected_refusal_name": USE_ARITY_MISMATCH if disposition == USE_ARITY_MISMATCH else None,
        "cites_declaration_symbol": declares,
        "binds_subject": binds,
        # B12: when set, this use is the round-trip partner of an admitted
        # declaration and the surface the checker resolves must be these bytes.
        "round_trip_for": round_trip_for,
        "rationale": why,
    }


def authored_sessions() -> tuple[dict[str, Any], ...]:
    """The four sessions, in order. Turn indices are derived from position."""

    return (
        {
            "session_id": "hr-fx-s1",
            "gloss": (
                "A full session: four admissions across three arities, then the "
                "budget. The two fifth-declaration turns are siblings — neither "
                "mutates the ledger, so both are honest fifth attempts."
            ),
            "turns": (
                _admit(
                    "declare parent_of/2 (variable, variable)",
                    "parent_of", 2, ("variable", "variable"),
                    "The design's own worked example, in the registered surface form.",
                ),
                _admit(
                    "declare tallies/1 (statistic)",
                    "tallies", 1, ("statistic",),
                    "Arity 1, and the statistic category's first appearance.",
                ),
                _admit(
                    "declare between_bounds/3 (variable, parameter, parameter)",
                    "between_bounds", 3, ("variable", "parameter", "parameter"),
                    "Arity 3 with a repeated category — the arity floor's third member.",
                ),
                _admit(
                    "declare draws_from/2 (random_variable, distribution)",
                    "draws_from", 2, ("random_variable", "distribution"),
                    "Two categories that appear nowhere else in this session.",
                ),
                _decl(
                    "declare fifth_wheel/1 (variable)",
                    name="fifth_wheel", arity=1, categories=("variable",),
                    code="SYMBOL_BUDGET",
                    why=(
                        "A well-formed, fresh, non-colliding declaration whose only "
                        "defect is being the fifth in a session that already admitted "
                        "four. Every earlier clause passes, so SYMBOL_BUDGET is reached "
                        "as the last clause rather than as a shortcut."
                    ),
                ),
                _decl(
                    "declare sixth_wheel/2 (variable, hedgehog)",
                    name="sixth_wheel", arity=2, categories=("variable", "hedgehog"),
                    code="CATEGORY_NOT_IN_SCHEMA",
                    also=("SYMBOL_BUDGET",),
                    why=(
                        "Order-sensitivity, and the one that proves SYMBOL_BUDGET is "
                        "LAST: this session is already full, so a checker that tested "
                        "the budget early would refuse SYMBOL_BUDGET here. The committed "
                        "order refuses the category."
                    ),
                ),
                _use(
                    "suppose parent_of(alice, bob)",
                    head="parent_of", argument_count=2,
                    disposition=USE_CHECKED, declares="parent_of", round_trip_for="parent_of",
                    why="B6's positive leg: correct arity, so the use passes through as a checked supposition.",
                ),
                _use(
                    "suppose tallies(votes)",
                    head="tallies", argument_count=1,
                    disposition=USE_CHECKED, declares="tallies", round_trip_for="tallies",
                    why="Arity 1 round trip. B12 owes a declare-then-use pair for EVERY admitted symbol, not a sample.",
                ),
                _use(
                    "suppose between_bounds(t, lo, hi)",
                    head="between_bounds", argument_count=3,
                    disposition=USE_CHECKED, declares="between_bounds", round_trip_for="between_bounds",
                    why="Arity 3 checked against its declaration; the arity that a 2-place-only checker would miss.",
                ),
                _use(
                    "suppose draws_from(score, normal)",
                    head="draws_from", argument_count=2,
                    disposition=USE_CHECKED, declares="draws_from", round_trip_for="draws_from",
                    why="Completes session one's round-trip set.",
                ),
                _use(
                    "suppose parent_of(alice)",
                    head="parent_of", argument_count=1,
                    disposition=USE_ARITY_MISMATCH, declares="parent_of",
                    why="Too few arguments. The refusal must name the declaration it was checked against.",
                ),
                _use(
                    "suppose tallies(a, b)",
                    head="tallies", argument_count=2,
                    disposition=USE_ARITY_MISMATCH, declares="tallies",
                    why="Too many arguments against an arity-1 declaration.",
                ),
                _use(
                    "suppose neighbour_of(alice, bob)",
                    head="neighbour_of", argument_count=2,
                    disposition=USE_OPAQUE, declares=None,
                    why=(
                        "The regression fence (B6): an applied atom whose head is not "
                        "declared must behave byte-identically to the same line on a tip "
                        "without this slice. No new refusal, no new record."
                    ),
                ),
            ),
        },
        {
            "session_id": "hr-fx-s2",
            "gloss": (
                "A second full session, carrying REDEFINITION_ATTEMPT — §4's first "
                "session-name sub-case, which the committed order decides under a "
                "different name than the union it belongs to."
            ),
            "turns": (
                _admit(
                    "declare cohort_of/2 (set, index)",
                    "cohort_of", 2, ("set", "index"),
                    "The set and index categories; the redefinition fixture's target.",
                ),
                _admit(
                    "declare ranks_above/2 (statistic, statistic)",
                    "ranks_above", 2, ("statistic", "statistic"),
                    "A second arity-2 admission in a second session.",
                ),
                _admit(
                    "declare stage_seq/1 (sequence)",
                    "stage_seq", 1, ("sequence",),
                    "The sequence category.",
                ),
                _admit(
                    "declare pins_to/2 (constant, parameter)",
                    "pins_to", 2, ("constant", "parameter"),
                    "The constant category; with this turn all nine schema categories are exercised.",
                ),
                _decl(
                    "declare cohort_of/3 (set, index, index)",
                    name="cohort_of", arity=3, categories=("set", "index", "index"),
                    code="REDEFINITION_ATTEMPT",
                    also=("COLLIDES_WITH_SESSION_NAME", "SYMBOL_BUDGET"),
                    subcase="already_admitted_symbol",
                    why=(
                        "§4's session-name union names three members; its FIRST — the "
                        "session's already-admitted symbols — is reached by a clause that "
                        "runs earlier, so this line's deciding clause is "
                        "REDEFINITION_ATTEMPT and not COLLIDES_WITH_SESSION_NAME. Sealing "
                        "that here is the point: the sub-case is exercised, the union "
                        "member is real, and the committed order decides which name the "
                        "person is given. Triple order-sensitivity, since the session is "
                        "also full."
                    ),
                ),
                _use(
                    "suppose ranks_above(median, mode)",
                    head="ranks_above", argument_count=2,
                    disposition=USE_CHECKED, declares="ranks_above", round_trip_for="ranks_above",
                    why="Round-trip partner for the second session's arity-2 admission.",
                ),
                _use(
                    "suppose stage_seq(phases)",
                    head="stage_seq", argument_count=1,
                    disposition=USE_CHECKED, declares="stage_seq", round_trip_for="stage_seq",
                    why="Round-trip partner for the sequence-category admission.",
                ),
                _use(
                    "suppose pins_to(anchor, offset)",
                    head="pins_to", argument_count=2,
                    disposition=USE_CHECKED, declares="pins_to", round_trip_for="pins_to",
                    why="Round-trip partner for the constant-category admission.",
                ),
                _use(
                    "suppose cohort_of(third_years, k)",
                    head="cohort_of", argument_count=2,
                    disposition=USE_CHECKED, declares="cohort_of", round_trip_for="cohort_of",
                    why=(
                        "The use checks against the ADMITTED arity-2 declaration, not "
                        "against the refused arity-3 line above it — a refusal mutates no "
                        "ledger."
                    ),
                ),
                _use(
                    "suppose cohort_of(third_years, k, j)",
                    head="cohort_of", argument_count=3,
                    disposition=USE_ARITY_MISMATCH, declares="cohort_of",
                    why=(
                        "The arity the refused redefinition asked for. If a refused "
                        "declaration had leaked into the ledger this line would pass, "
                        "which makes it the redefinition refusal's own detector."
                    ),
                ),
            ),
        },
        {
            "session_id": "hr-fx-s3",
            "gloss": (
                "A deliberately NOT-full session (three admissions), so every refusal "
                "below is reached on its own clause with the budget clause provably "
                "inert. The three admissions are the reserved-prefix-adjacent names "
                "B12 rides."
            ),
            "turns": (
                # -- two suppositions seeded first: they populate §4's second and
                #    third session-name union members before the collisions below.
                _use(
                    "suppose headcount = 12",
                    head=None, argument_count=None,
                    disposition=USE_BINDING_UNCHANGED, declares=None, binds="headcount",
                    why=(
                        "A binding supposition, and NOT a use of a declared symbol — this "
                        "slice does not touch it, so it carries its own disposition rather "
                        "than the slice's positive verdict, and it is outside B6's counts. "
                        "Its subject `headcount` enters "
                        "`AssumptionSet.bound_names()` — §4's SECOND session-name union "
                        "member — and is the target of the collision fixture below."
                    ),
                ),
                _use(
                    "suppose parent_link(alice, bob)",
                    head="parent_link", argument_count=2,
                    disposition=USE_OPAQUE, declares=None,
                    why=(
                        "A live NON-binding supposition held as an opaque atom today. Its "
                        "applied-term head `parent_link` is §4's THIRD union member — the "
                        "whole atom can never equal a declared name, so the head is what "
                        "enters the comparison. Sealed as OPAQUE_ATOM because at this turn "
                        "no declaration for it exists."
                    ),
                ),
                _admit(
                    "declare sun_total/1 (variable)",
                    "sun_total", 1, ("variable",),
                    "B12: one character from the reserved prefix `sum_`. Must ADMIT and must round-trip unmangled.",
                ),
                _admit(
                    "declare presum_total/2 (variable, parameter)",
                    "presum_total", 2, ("variable", "parameter"),
                    "B12: CONTAINS `sum_` but does not start with it. The prefix guard is a prefix guard, not a substring guard.",
                ),
                _admit(
                    "declare maximal_of/2 (set, variable)",
                    "maximal_of", 2, ("set", "variable"),
                    "B12: starts with `max` — the prefix minus its underscore — but not with `max_`.",
                ),
                # -- B12's round trips, at the prefix-adjacent names -----------
                _use(
                    "suppose sun_total(9)",
                    head="sun_total", argument_count=1,
                    disposition=USE_CHECKED, declares="sun_total", round_trip_for="sun_total",
                    why=(
                        "B12's load-bearing case: a name one character from `sum_` must "
                        "resolve to the ledger key `sun_total` byte for byte. A parser that "
                        "reached for the near-miss would resolve `sum` and this line would "
                        "take the opaque path instead."
                    ),
                ),
                _use(
                    "suppose presum_total(x, y)",
                    head="presum_total", argument_count=2,
                    disposition=USE_CHECKED, declares="presum_total", round_trip_for="presum_total",
                    why="A substring guard would refuse the declaration; a prefix guard admits it and must resolve it whole.",
                ),
                _use(
                    "suppose maximal_of(chain, top)",
                    head="maximal_of", argument_count=2,
                    disposition=USE_CHECKED, declares="maximal_of", round_trip_for="maximal_of",
                    why="Must not be clipped to `max` on the way back in.",
                ),
                # -- UNPARSED family ------------------------------------------
                _decl(
                    "declare",
                    name=None, arity=None, categories=None, code="UNPARSED",
                    why="The command word with no tail. The emptiest input the row can receive.",
                ),
                _decl(
                    "declare parent_of/2",
                    name=None, arity=None, categories=None, code="UNPARSED",
                    why="No category list. Arity without categories cannot produce an arity/category agreement check.",
                ),
                _decl(
                    "declare parent_of/two (variable, variable)",
                    name=None, arity=None, categories=None, code="UNPARSED",
                    why="A spelled arity. `<arity>` is an integer in the registered form; a word is outside the grammar, not a mismatch inside it.",
                ),
                _decl(
                    "declare 2parent/2 (variable, variable)",
                    name=None, arity=None, categories=None, code="UNPARSED",
                    why="A leading digit. The name production is `[a-z][a-z0-9_]*` (DESIGN §3).",
                ),
                _decl(
                    "declare parent-of/2 (variable, variable)",
                    name=None, arity=None, categories=None, code="UNPARSED",
                    why="A hyphen: outside the name production, and the nearest-miss a person actually types.",
                ),
                _decl(
                    "declare zero_ary/0 ()",
                    name=None, arity=None, categories=None, code="UNPARSED",
                    why=(
                        "Arity is an integer >= 1 (DESIGN §3), so /0 is outside the form. "
                        "Sealed as UNPARSED rather than ARITY_CATEGORY_MISMATCH: zero "
                        "categories agreeing with zero arity would otherwise ADMIT a "
                        "propositional constant, which is not the symbol kind §9's "
                        "suspended habit licenses."
                    ),
                ),
                _decl(
                    "declare grandparent_of/3 (variable, variable, variable) if parent_of(x, y) and parent_of(y, z)",
                    name=None, arity=None, categories=None, code="UNPARSED",
                    why=(
                        "An AXIOM attempt. DESIGN §6.1 deletes REQUIRES_CONSERVATIVITY_VERDICT "
                        "at design time on the ground that connectives and binders are "
                        "refused by the grammar rather than by a dead code — this line is "
                        "that ground made checkable. It is also the fixture that would "
                        "fire the roadmap's first construction refusal if it were ever "
                        "admitted."
                    ),
                ),
                _decl(
                    "declare conservative parent_of/2 (variable, variable)",
                    name=None, arity=None, categories=None, code="UNPARSED",
                    why=(
                        "A conservativity REQUEST. Same deletion, second face: the person "
                        "asking for the verdict gets UNPARSED, not a verdict code that "
                        "would have to be honoured."
                    ),
                ),
                # -- ARITY_CATEGORY_MISMATCH ---------------------------------
                _decl(
                    "declare pairs_with/2 (variable)",
                    name="pairs_with", arity=2, categories=("variable",),
                    code="ARITY_CATEGORY_MISMATCH",
                    why="One category for arity 2. `argument_categories` has length == arity or it does not.",
                ),
                _decl(
                    "declare triple_of/3 (variable, variable, variable, variable)",
                    name="triple_of", arity=3, categories=("variable", "variable", "variable", "variable"),
                    code="ARITY_CATEGORY_MISMATCH",
                    why="Four categories for arity 3 — the mismatch in the other direction.",
                ),
                _decl(
                    "declare owns_pet/2 (hedgehog)",
                    name="owns_pet", arity=2, categories=("hedgehog",),
                    code="ARITY_CATEGORY_MISMATCH",
                    also=("CATEGORY_NOT_IN_SCHEMA",),
                    why=(
                        "Order-sensitivity: both the count and the member are wrong. The "
                        "committed order counts first, so a person who typed one bad "
                        "category in the wrong number of slots is told about the number."
                    ),
                ),
                # -- CATEGORY_NOT_IN_SCHEMA -----------------------------------
                _decl(
                    "declare owns_pet/2 (variable, hedgehog)",
                    name="owns_pet", arity=2, categories=("variable", "hedgehog"),
                    code="CATEGORY_NOT_IN_SCHEMA",
                    why=(
                        "Right count, one member outside the nine-member enum. B8's second "
                        "mutation names this fixture: delete a category from a copy of the "
                        "schema and every declaration citing it must flip here."
                    ),
                ),
                # -- RESERVED_PREFIX ------------------------------------------
                _decl(
                    "declare sum_total/1 (variable)",
                    name="sum_total", arity=1, categories=("variable",),
                    code="RESERVED_PREFIX",
                    why=(
                        "B2's mandated fixture, and the design's named live hazard: the "
                        "shipped template parser rewrites any `sum_`-leading identifier "
                        "into the corpus aggregate head, so equality against a census "
                        "cannot see a rewrite that happens at tokenization. The guard is a "
                        "PREFIX guard for exactly that reason."
                    ),
                ),
                _decl(
                    "declare SUM_TOTAL/1 (variable)",
                    name="sum_total", arity=1, categories=("variable",),
                    code="RESERVED_PREFIX",
                    why=(
                        "Normalization ordering, sealed as a fixture: NFC + casefold runs "
                        "BEFORE the prefix comparison, so an uppercased hazard is the same "
                        "hazard. A checker that compared raw bytes would admit this line."
                    ),
                ),
                _decl(
                    "declare sum_total/1 (hedgehog)",
                    name="sum_total", arity=1, categories=("hedgehog",),
                    code="CATEGORY_NOT_IN_SCHEMA",
                    also=("RESERVED_PREFIX",),
                    why=(
                        "Order-sensitivity across the schema/census boundary: the same "
                        "reserved name that refuses RESERVED_PREFIX above refuses the "
                        "CATEGORY clause here, because c3 precedes c4."
                    ),
                ),
                # -- COLLIDES_WITH_LIBRARY_SYMBOL -----------------------------
                _decl(
                    "declare gcd/2 (variable, variable)",
                    name="gcd", arity=2, categories=("variable", "variable"),
                    code="COLLIDES_WITH_LIBRARY_SYMBOL",
                    why=(
                        "B2's second mandated fixture: a head equal to a casefolded corpus "
                        "call head. Corpus heads are uppercase — `GCD` — and a declared "
                        "`gcd` colliding with it is the point, not an accident. Reached by "
                        "three independent census bullets."
                    ),
                ),
                _decl(
                    "declare meet/2 (set, set)",
                    name="meet", arity=2, categories=("set", "set"),
                    code="COLLIDES_WITH_LIBRARY_SYMBOL",
                    why=(
                        "The corpus's most frequent call head. A census that admitted `meet` "
                        "would have missed two thirds of the committed trees."
                    ),
                ),
                _decl(
                    "declare implies/2 (variable, variable)",
                    name="implies", arity=2, categories=("variable", "variable"),
                    code="COLLIDES_WITH_LIBRARY_SYMBOL",
                    why=(
                        "The only one of the three targets reachable through a NON-functional "
                        "route: `implies` is a bare, already name-shaped member of "
                        "symbol_lexicon.operators. It proves the operators category is not "
                        "inert just because most of its members are un-collidable glyphs."
                    ),
                ),
                _decl(
                    "declare sum_i/1 (index)",
                    name="sum_i", arity=1, categories=("index",),
                    code="RESERVED_PREFIX",
                    also=("COLLIDES_WITH_LIBRARY_SYMBOL",),
                    why=(
                        "The order-sensitivity the design's clause order exists for, and the "
                        "only VERIFIED name that is both a census member and a reserved-prefix "
                        "match: `sum_i` is one of exactly two name-shaped members of "
                        "symbol_lexicon.functionals and the literal token behind sixteen of "
                        "the corpus's seventeen big-op captures. Both clauses would fire; c4 "
                        "runs before c5, so the person is told about the prefix. A checker "
                        "that reported the collision here would be reporting the shallower "
                        "of two true things."
                    ),
                ),
                # -- COLLIDES_WITH_SESSION_NAME -------------------------------
                _decl(
                    "declare headcount/1 (statistic)",
                    name="headcount", arity=1, categories=("statistic",),
                    code="COLLIDES_WITH_SESSION_NAME",
                    subcase="supposition_binding_subject",
                    why=(
                        "§4 sub-case TWO: the name equals a live supposition's binding "
                        "subject (`suppose headcount = 12`, seeded at turn 1 of this "
                        "session). Nothing about the declaration itself is malformed."
                    ),
                ),
                _decl(
                    "declare parent_link/2 (variable, variable)",
                    name="parent_link", arity=2, categories=("variable", "variable"),
                    code="COLLIDES_WITH_SESSION_NAME",
                    subcase="live_non_binding_supposition_head",
                    why=(
                        "§4 sub-case THREE: the name equals the applied-term HEAD of a "
                        "live non-binding supposition (`suppose parent_link(alice, bob)`, "
                        "seeded at turn 2). The whole atom could never equal a declared "
                        "name; the head can, and does."
                    ),
                ),
            ),
        },
        {
            "session_id": "hr-fx-s5",
            "gloss": (
                "Normalization, which the rest of the corpus only exercises through "
                "`SUM_TOTAL`. The design's rule is an ORDER — NFC, then casefold, then "
                "match the production against the RESULT — and these fixtures disagree "
                "under any other reading, so H-P0 cannot pass them with `.lower()`."
            ),
            "turns": (
                _admit(
                    "declare ﬁrst_of/1 (variable)",
                    "first_of", 1, ("variable",),
                    (
                        "U+FB01 LATIN SMALL LIGATURE FI. Casefold EXPANDS it to `fi`, so the "
                        "raw surface matches no production and the normalized name matches "
                        "it exactly. A checker that tested the production before normalizing "
                        "refuses this line; a checker that used `.lower()` — which leaves "
                        "U+FB01 alone — also refuses it. Only the sealed order admits it, "
                        "and the ledger key is `first_of`."
                    ),
                    raw_name="ﬁrst_of",
                ),
                _admit(
                    "declare straße_of/1 (variable)",
                    "strasse_of", 1, ("variable",),
                    (
                        "U+00DF casefolds to `ss`, so the normalized name is two characters "
                        "LONGER than the surface. `.lower()` leaves it unchanged and refuses. "
                        "This is also why the ledger key cannot be a slice of the source line."
                    ),
                    raw_name="straße_of",
                ),
                _decl(
                    "declare café_of/1 (variable)",
                    name=None, arity=None, categories=None, code="UNPARSED",
                    raw_name="café_of",
                    why=(
                        "The NFC half, and deliberately a REFUSAL: `e` + U+0301 composes to "
                        "`é`, which casefolds to itself and is outside `[a-z]`. "
                        "Normalization is not a repair mechanism — it makes the comparison "
                        "well-defined and then the production still decides. Sealing an "
                        "NFC case that refuses is what stops the rule being read as "
                        "'normalize until it fits'."
                    ),
                ),
                _use(
                    "suppose ﬁrst_of(page)",
                    head="first_of", argument_count=1,
                    disposition=USE_CHECKED, declares="first_of", round_trip_for="first_of",
                    why=(
                        "The round trip across a normalization that CHANGES LENGTH. The "
                        "surface the checker resolves must be the ledger key `first_of`, "
                        "which is not a substring of the line the person typed — the case "
                        "where 'byte-identical to the ledger key' and 'byte-identical to the "
                        "typed surface' come apart, and B12 means the former."
                    ),
                ),
                _use(
                    "suppose straße_of(sign)",
                    head="strasse_of", argument_count=1,
                    disposition=USE_CHECKED, declares="strasse_of", round_trip_for="strasse_of",
                    why="The same, with a two-character expansion.",
                ),
            ),
        },
        {
            "session_id": "hr-fx-s4",
            "gloss": (
                "A fresh session that declares nothing. B5's third leg: an admitted "
                "symbol from an earlier session is gone, so its use takes the "
                "opaque-atom path again."
            ),
            "turns": (
                _use(
                    "suppose parent_of(alice, bob)",
                    head="parent_of", argument_count=2,
                    disposition=USE_OPAQUE, declares=None,
                    why=(
                        "Byte-identical to hr-fx-s1's CHECKED_SUPPOSITION line and expected "
                        "to behave differently, because the ledger is session-scoped. Same "
                        "bytes, no declaration, opaque atom — non-persistence as a fixture "
                        "rather than as a promise."
                    ),
                ),
                _use(
                    "suppose sun_total(9)",
                    head="sun_total", argument_count=1,
                    disposition=USE_OPAQUE, declares=None,
                    why=(
                        "The same for hr-fx-s3's B12 admission: a prefix-adjacent name that "
                        "was admitted in another session is not declared here."
                    ),
                ),
            ),
        },
    )


# --------------------------------------------------------------------------
# B3 — containment mutants. Descriptions of attempts, not machinery.
# --------------------------------------------------------------------------

#: DESIGN §7 B3: "≥30 seeded mutants attempt to move an admitted symbol into a
#: rendered answer's evidence, a written session document, a journal, or a
#: library path. 100% are stopped by the shipped machinery or the checker —
#: not by test assertions reading the mutant's name."
#:
#: Each row names its VECTOR and its TARGET. The machinery that stops them
#: ships at H-P0/H-P1; H-PRE only fixes what must be attempted, so that the
#: later run cannot choose an easier set.
B3_VECTORS = (
    "answer_evidence",
    "session_document",
    "journal",
    "library_path",
)

STOPPER_KINDS = ("shipped_machinery", "checker")

B3_MUTANTS: tuple[tuple[str, str, str, str, str], ...] = (
    # (vector, target, attempt, stopper_kind, stopper_mechanism)
    #
    # EVERY row names a MECHANISM: a code path that raises, a digest that
    # moves, or a sweep that finds a string. B3's wording is "stopped by the
    # shipped machinery or the checker — not by test assertions reading the
    # mutant's name", and a row whose stopper is a design argument ("the slice
    # sheds frames", "this slice mints no questions") is a row H-P1 could only
    # score by agreeing with the author. Those are not stoppers. The generator
    # now refuses them: `stopper_kind` is a closed vocabulary and
    # `stopper_mechanism` must name a module, a digest, or a sweep.
    (
        "answer_evidence",
        "the rendered answer's evidence list (scripts/answer.py)",
        "A declared symbol's name is offered as an evidence line on a rendered answer, as if the declaration were a citation.",
        "shipped_machinery",
        "The evidence path renders resolved corpus nodes by node id; an admitted symbol has no node id, so there is no evidence row to construct.",
    ),
    (
        "answer_evidence",
        "the rendered answer's evidence list (scripts/answer.py)",
        "A supposition applying a declared symbol is offered as evidence for the answer it appears beside.",
        "shipped_machinery",
        "The supposition ledger's evidence status travels with the assumption record and the renderer reads that status; a checked use is still a supposition.",
    ),
    (
        "answer_evidence",
        "the served answer payload's citation slots",
        "The declaration's decl_id is written into a citation slot so a reader would resolve it as a source.",
        "shipped_machinery",
        "Citation resolution looks the id up in the merged graph; decl_id is a session-record digest and resolves to nothing, so the slot cannot be filled.",
    ),
    (
        "answer_evidence",
        "the read-barrier citation carried on a turn",
        "The admitted symbol is cited through the read barrier as though it were a read corpus fact.",
        "shipped_machinery",
        "The read barrier records assumption ids through barrier.record(assumption_id); its record shape has no symbol-name field to carry one.",
    ),
    (
        "answer_evidence",
        "the rendered answer's gloss text",
        "The declared symbol name is interpolated into the rendered gloss so it appears in prose the reader takes as the program's own vocabulary.",
        "shipped_machinery",
        "B5's name sweep over the run's full output tree reads rendered text; an admitted fixture symbol in a gloss is a found string and a B5 instance.",
    ),
    (
        "answer_evidence",
        "the answer's provenance / attribution block",
        "The session's symbol ledger is attached as a provenance source of the answer.",
        "shipped_machinery",
        "Provenance rows carry a path plus sha256_lf; the symbol ledger is runtime state with no committed path, so no row can be built for it.",
    ),
    (
        "answer_evidence",
        "an exhausted turn's refusal receipt",
        "A refusal receipt quotes the admitted symbol as the reason the turn exhausted, moving the name into a durable receipt.",
        "shipped_machinery",
        "B5's name sweep covers receipts as part of the run's output tree, and B4's working_tree_digest moves for a receipt written outside the two declared output paths.",
    ),
    (
        "answer_evidence",
        "the capability sheet's generated example row",
        "The `declare` row's generated example is filled with a real admitted fixture symbol rather than a placeholder.",
        "shipped_machinery",
        "The capability sheet is a committed generated artifact inside write_stage.working_tree_digest, so B4 goes red on the write and B5's sweep finds the name.",
    ),
    (
        "session_document",
        "session_state.session_document's `ledgers` payload",
        "The symbol ledger is folded into LedgerSnapshot so it rides the session document's ledger slot.",
        "shipped_machinery",
        "session_state.encode raises SessionFormatError for any value whose type name is absent from the closed _TYPES registry (session_state.py:130).",
    ),
    (
        "session_document",
        "session_state.session_document's `state` payload",
        "A PersonSymbolDeclaration instance is attached to RetrievalState and the document is encoded.",
        "shipped_machinery",
        "encode recurses into the attached value and hits the same _TYPES check, so the refusal comes from the codec rather than from the slot it was hidden in.",
    ),
    (
        "session_document",
        "session_state.session_document's `story_state` payload",
        "A StoryBeat's text carries the admitted symbol name as narrative content, riding a type that IS registered.",
        "shipped_machinery",
        "The codec passes this one, which is why the fence is B5's name sweep over the written document rather than the type registry. This mutant exists to keep that distinction live.",
    ),
    (
        "session_document",
        "session_state.encode's type registry",
        "An AdmissibilityVerdict is handed straight to session_state.encode.",
        "shipped_machinery",
        "encode's _TYPES lookup raises on the unregistered type name; neither record type is registered at this commit.",
    ),
    (
        "session_document",
        "the session document's `active_slot`",
        "The admitted symbol name is written as the active slot identifier.",
        "shipped_machinery",
        "active_slot is a plain string field, so the codec permits it; B5's sweep reads every string in the written document and finds the name.",
    ),
    (
        "session_document",
        "a Literal in FrameSpec.declarations",
        "The declaration is re-expressed as a subject-predicate-value Literal and attached to a FrameSpec so it persists through a frame.",
        "shipped_machinery",
        "FrameSpec.declarations holds three-field Literals that cannot represent an arity-3 application, so an arity-3 fixture symbol cannot be encoded at all; an arity-2 one encodes and is then found by B5's sweep.",
    ),
    (
        "session_document",
        "the session document's `owner` field",
        "The admitted symbol name is smuggled into the owner string.",
        "shipped_machinery",
        "B5 sweeps names rather than fields, so a name in any string in the document is found regardless of which slot carried it.",
    ),
    (
        "session_document",
        "a ClarificationRequest's question text",
        "A ClarificationRequest quoting the admitted symbol is constructed and written into the session document.",
        "shipped_machinery",
        "ClarificationRequest is a registered type, so the codec permits it and B5's sweep over the written document is what finds the quoted name.",
    ),
    (
        "journal",
        "experiments/sessions/<session_id>.json turns[]",
        "The declaration turn is journalled with its source_line, putting the person's symbol in a committed journal.",
        "shipped_machinery",
        "B5's sweep covers experiments/sessions/*.json and B4's working_tree_digest moves, the journal path being outside the two declared output paths.",
    ),
    (
        "journal",
        "experiments/sessions/<session_id>.json header pins",
        "The symbol ledger's digest is added as a journal header pin.",
        "shipped_machinery",
        "prereg_pins.resolve_pin raises PinChainError for a pin naming no registered prereg row, so an unregistered pin cannot be written and read back.",
    ),
    (
        "journal",
        "experiments/sessions/<session_id>.reads.json",
        "The read log records a read of the declared symbol, naming it in the read record.",
        "shipped_machinery",
        "B5's sweep covers the .reads.json sibling and B4's digest covers the write.",
    ),
    (
        "journal",
        "a journalled refusal turn",
        "A REFUSED declaration is journalled verbatim, so the name would persist even though no ledger mutation occurred.",
        "shipped_machinery",
        "B5's sweep reads the journal for admitted fixture symbol names irrespective of the turn's verdict, and B4's digest moves on the write.",
    ),
    (
        "journal",
        "the journal's replayable turn transcript",
        "The `declare` line's verbatim bytes are stored as replay input so a replay re-admits the symbol.",
        "shipped_machinery",
        "replay_session re-runs the route into a fresh session whose symbol ledger is empty, which is the behaviour hr-fx-s4 seals, and B5's sweep covers the stored bytes.",
    ),
    (
        "journal",
        "a session-gate report under reports/",
        "The gate report summarizes the run by listing the admitted fixture symbol names.",
        "shipped_machinery",
        "reports/ is inside write_stage.working_tree_digest and outside the two declared output paths, so B4 goes red on the write.",
    ),
    (
        "journal",
        "the cold registry census artifact",
        "The symbol ledger is registered in the cold registry census so the declaration appears in a committed census.",
        "shipped_machinery",
        "cold_registry_census.py --check recomputes the census from the tree and reports CENSUS DRIFT on any member it did not derive.",
    ),
    (
        "journal",
        "the run's own two declared output paths, used as a carrier",
        "house_rules_verdicts.json is used to smuggle the name into a path B4 excludes, then read back by a later session.",
        "checker",
        "B4 excludes those paths from the DIGEST, not from B5's name sweep, and the checker's inputs are the line, the census and the schema — it never reads the run's outputs, so there is no path back in.",
    ),
    (
        "library_path",
        "data/*/nodes.json",
        "The declared symbol is emitted as a node into the boot corpus, joining the merged resolver graph.",
        "shipped_machinery",
        "write_stage.working_tree_digest is byte-identical across the run (B4), and durable_digest over data/ moves too as the narrow named control.",
    ),
    (
        "library_path",
        "data/*/nodes.json symbol_lexicon",
        "The declared symbol is added to a node's symbol_lexicon, which is exactly the namespace the census guards.",
        "shipped_machinery",
        "Both digests move on the write, and the census checker's fresh recomputation would then contain a member no committed node justifies.",
    ),
    (
        "library_path",
        "the generated library file emitted by the formula-adding path",
        "A declaration is compiled into a generated library file as a fresh relation.",
        "shipped_machinery",
        "write_stage.working_tree_digest is compared byte for byte before and after the registered run, so any generated file is a digest difference (B4).",
    ),
    (
        "library_path",
        "protocol/protocols.json",
        "The declared symbol is written into the protocol corpus, which is deliberately outside data/ and so outside durable_digest.",
        "shipped_machinery",
        "The gate uses the wider working_tree_digest for exactly this escape, and check_protocol_regeneration re-derives the corpus from its builder and would not reproduce the member.",
    ),
    (
        "library_path",
        "schema/equation-node.schema.json",
        "A person's category is appended to the syntactic_category enum so their declaration would validate.",
        "shipped_machinery",
        "The schema's sha256_lf is a sealed field of this artifact and of every AdmissibilityVerdict, so the digest comparison fails and B4's tree digest moves.",
    ),
    (
        "library_path",
        "scripts/ — the escape durable_digest's own docstring names",
        "A generated module under scripts/ carries the admitted symbol as a constant.",
        "shipped_machinery",
        "durable_digest covers data/ only and says so, which is why the gate uses working_tree_digest; the cold census's program-tree scan moves as well.",
    ),
    (
        "library_path",
        "experiments/symbol_census.json",
        "The admitted symbol is added to the committed census so a later session's collision check finds it.",
        "shipped_machinery",
        "The census checker is a separate invocation proving the artifact matches a fresh recomputation (B2), so an inserted member fails regeneration.",
    ),
    (
        "library_path",
        "the anonymized_template corpus",
        "A supposition applying the declared symbol is templated and added to the committed template corpus.",
        "shipped_machinery",
        "check_report_regeneration re-derives the template ledgers from their committed writer, so an inserted template is a regeneration mismatch, and B4's digest moves.",
    ),
)


# --------------------------------------------------------------------------
# B12 — reserved-prefix-adjacent mutants.
# --------------------------------------------------------------------------

#: DESIGN §7 B12: "for every admitted fixture symbol, declare then use, and
#: assert the surface the use-side checker resolves is byte-identical to the
#: ledger key. Mutants for this gate are seeded specifically at
#: reserved-prefix-adjacent names."
#:
#: REPLAY POLICY, sealed here so session arithmetic cannot be argued later:
#: each B12 mutant is replayed in its OWN fresh session holding exactly one
#: declaration and (where admitted) one use. No B12 mutant enters the four
#: authored sessions' budgets, and the three that coincide with hr-fx-s3
#: admissions name that fixture rather than being counted twice.
B12_REPLAY_POLICY = (
    "Each B12 mutant is replayed in its own fresh single-declaration session; "
    "no B12 mutant counts against an authored session's four-symbol budget."
)

B12_MUTANTS: tuple[tuple[str, str, str, str], ...] = (
    # (name, adjacency, expected_code_or_NONE, note)
    (
        "sum_total", "starts_with_prefix", "RESERVED_PREFIX",
        "B2's mandated fixture and the design's named hazard. The prefix guard's positive control.",
    ),
    (
        "sum_", "prefix_exactly", "RESERVED_PREFIX",
        "The bare prefix, which the name production admits (a trailing underscore is legal) and the guard must still refuse.",
    ),
    (
        "SUM_TOTAL", "starts_with_prefix_uppercased", "RESERVED_PREFIX",
        "Casefold runs before the comparison, so the uppercased hazard is the same hazard.",
    ),
    (
        "prod_uct", "starts_with_prefix", "RESERVED_PREFIX",
        "A second reserved prefix, and a name a person would plausibly type meaning `product`.",
    ),
    (
        "lim_it", "starts_with_prefix", "RESERVED_PREFIX",
        "Third prefix. `lim_it` reads as an English word split across the guard.",
    ),
    (
        "max_of", "starts_with_prefix", "RESERVED_PREFIX",
        "Fourth prefix.",
    ),
    (
        "min_or", "starts_with_prefix", "RESERVED_PREFIX",
        "Fifth prefix; all five of BIG_OP_PREFIXES are now exercised.",
    ),
    (
        "sun_total", "one_character_from_prefix", "NONE",
        "m -> n. Admitted, and the ledger key must be `sun_total` byte for byte — no near-miss correction.",
    ),
    (
        "sumtotal", "prefix_without_underscore", "NONE",
        "The underscore is part of the prefix: the shipped trigger is "
        "`tok.lower().startswith(BIG_OP_PREFIXES)` (scripts/match_signatures.py:547) and "
        "`sumtotal(x)` was verified to parse as ('call', 'sumtotal', ...) with an empty "
        "`parse_rewrites` — no capture. Admitted, and the clean negative control for the "
        "`sum_total` capture beside it.",
    ),
    (
        "presum_total", "contains_prefix_not_leading", "NONE",
        "Contains `sum_` in the interior. A substring guard would refuse this; a prefix guard admits it.",
    ),
    (
        "maximal_of", "prefix_minus_underscore_then_letters", "NONE",
        "Starts with `max` but not `max_`. Admitted, and the round-trip must not clip it to `max`.",
    ),
    (
        "product_of", "prefix_minus_underscore_then_letters", "NONE",
        "Starts with `prod` but not `prod_`.",
    ),
    (
        "limit_of", "prefix_minus_underscore_then_letters", "NONE",
        "Starts with `lim` but not `lim_`.",
    ),
    (
        "minor_key", "prefix_minus_underscore_then_letters", "NONE",
        "Starts with `min` but not `min_`. The four `prefix-minus-underscore` mutants are the round-trip's real load.",
    ),
    (
        "sum", "prefix_minus_underscore_exactly", "COLLIDES_WITH_LIBRARY_SYMBOL",
        "The prefix minus its underscore. The prefix guard does NOT reach it — `sum` does not "
        "start with `sum_` — so the census must, and it does: `sum` is a lowercase call head in "
        "16 committed templates and the one lowercase HEAD_ALIASES key, aliased to `aggregate`. "
        "The refusal arrives from c5, one clause later than a reader would guess.",
    ),
    (
        "sum_i", "starts_with_prefix_and_is_a_census_member", "RESERVED_PREFIX",
        "Both c4 and c5 would fire; c4 runs first. Cross-referenced to the hr-fx-s3 fixture of "
        "the same NAME, which is where the order-sensitivity is scored under its own category.",
    ),
)


# --------------------------------------------------------------------------
# Codes deleted with a reason — the U-PRE mechanic.
# --------------------------------------------------------------------------

#: DESIGN §6.1: "A refusal code no grammatical fixture can fire is deleted
#: here, U-PRE-style — and two of the first draft's codes are already deleted
#: by this rule at design time". They are recorded, never resurrected: the
#: audit trail is the point of the mechanic.
DELETED_CODES: tuple[dict[str, str], ...] = (
    {
        "code": "UNBOUND_VARIABLE",
        "deleted_at": "design time (DESIGN-house-rules §6.1)",
        "reason": (
            "No premises means no variables to bind. The reworked design sheds premises "
            "entirely, so no grammatical declaration line can contain a variable "
            "occurrence that a clause could find unbound — the code would owe a fixture "
            "that cannot be written."
        ),
        "ground_fixture": "hr-fx-s3 — the axiom-attempt line, which refuses UNPARSED",
    },
    {
        "code": "REQUIRES_CONSERVATIVITY_VERDICT",
        "deleted_at": "design time (DESIGN-house-rules §6.1)",
        "reason": (
            "No clause could fire it. Conservativity is refused as out-of-scope by "
            "UNPARSED's grammar, not by a dead code: connectives, binders and relational "
            "axioms are outside the registered declaration form, so a request for a "
            "conservativity verdict never reaches a clause that could answer it."
        ),
        "ground_fixture": "hr-fx-s3 — the `declare conservative ...` line, which refuses UNPARSED",
    },
)

#: H-PRE's own deletion verdict on the eight live codes is computed, not
#: authored: a code with no fixture would be deleted here with its reason.
#: All eight fire, so the list below is empty and the builder proves it.
DELETED_AT_H_PRE: tuple[dict[str, str], ...] = ()


# --------------------------------------------------------------------------
# Derivation.
# --------------------------------------------------------------------------


def _expected_verdict(code: str) -> str:
    return ADMIT_VERDICT if code == "NONE" else REFUSED


def _expected_clause(code: str) -> str:
    if code == "NONE":
        return ADMIT_CLAUSE
    if code not in CLAUSE_BY_CODE:
        raise ConstructionRefusal(
            f"`{code}` is not one of the eight committed refusal codes. A code deleted with "
            "a reason stays deleted; H-PRE does not resurrect one by using it."
        )
    return CLAUSE_BY_CODE[code]


def derive_grounds(
    turn: dict[str, Any],
    *,
    categories: Sequence[str],
    library_names: set[str],
    admitted_names: set[str],
    session_names: set[str],
    admitted_running: int,
) -> tuple[set[str], bool]:
    """Every clause this line grounds, derived from the SEALED READING.

    This is the answer to "who checks the author?". Six of the eight clauses
    are mechanically decidable from fields this generator already holds, so
    `also_grounds_for` is COMPUTED here and compared against what the author
    wrote; a mismatch refuses the build. An omitted earlier ground — the one
    mistake that would silently make a sealed expectation wrong — cannot
    survive it.

    **This is not a parser and must not become one.** It never reads
    `turn["line"]`. It operates on the author's structured reading of the line
    (name, arity, categories), which is exactly the reading H-P0's parser will
    be scored against. Deriving the verdict from the surface bytes is H-P0's
    job; deriving it from the sealed reading is how H-PRE checks itself.

    Returns (grounds, derivable). `derivable` is False for UNPARSED lines,
    which carry no readable name and where no later clause can be decided.
    """

    name = turn["read_symbol_name"]
    arity = turn["read_arity"]
    cats = turn["read_argument_categories"]
    if name is None or arity is None or cats is None:
        return set(), False

    grounds: set[str] = set()
    if len(cats) != arity:
        grounds.add("ARITY_CATEGORY_MISMATCH")
    if any(category not in categories for category in cats):
        grounds.add("CATEGORY_NOT_IN_SCHEMA")
    if name.startswith(RESERVED_PREFIXES):
        grounds.add("RESERVED_PREFIX")
    if name in library_names:
        grounds.add("COLLIDES_WITH_LIBRARY_SYMBOL")
    if name in admitted_names:
        grounds.add("REDEFINITION_ATTEMPT")
    if name in session_names:
        grounds.add("COLLIDES_WITH_SESSION_NAME")
    if admitted_running >= SESSION_ADMITTED_CAP:
        grounds.add("SYMBOL_BUDGET")
    return grounds, True


def build_fixtures(repo: Path) -> dict[str, Any]:
    categories = schema_categories(repo)
    sessions_out: list[dict[str, Any]] = []
    fixtures: list[dict[str, Any]] = []

    library_names = {row["name"] for row in LIBRARY_COLLISION_TARGETS}

    for session in authored_sessions():
        session_id = session["session_id"]
        admitted_running = 0
        # Session state the derivation below reads, carried turn by turn: the
        # symbols admitted so far, and DESIGN §4's three-source session-name
        # union (admitted symbols, binding subjects, applied heads of live
        # non-binding suppositions).
        admitted_names: set[str] = set()
        session_names: set[str] = set()
        decl_ids: list[str] = []
        use_ids: list[str] = []
        for position, turn in enumerate(session["turns"], start=1):
            fixture_id = f"{session_id}-t{position:02d}"
            record: dict[str, Any] = {
                "fixture_id": fixture_id,
                "session_id": session_id,
                "turn_index": position,
                "kind": turn["kind"],
                "line": turn["line"],
            }
            if turn["kind"] == "declaration":
                code = turn["expected_refusal_code"]
                # Validated FIRST, so a code outside the committed eight is
                # refused by name rather than by the grounds derivation
                # disagreeing with it for a less specific reason. This is the
                # clause that keeps a design-time-deleted code deleted.
                _expected_clause(code)
                grounds, derivable = derive_grounds(
                    turn,
                    categories=categories,
                    library_names=library_names,
                    admitted_names=admitted_names,
                    session_names=session_names,
                    admitted_running=admitted_running,
                )
                if derivable:
                    earliest = (
                        min(grounds, key=lambda c: CLAUSE_RANK[c]) if grounds else "NONE"
                    )
                    if earliest != code:
                        raise ConstructionRefusal(
                            f"{fixture_id}: authored expectation {code}, but the committed "
                            f"order decides {earliest} from the derived grounds "
                            f"{sorted(grounds)}"
                        )
                    derived_also = sorted(grounds - {code})
                    if derived_also != sorted(turn["also_grounds_for"]):
                        raise ConstructionRefusal(
                            f"{fixture_id}: authored also_grounds_for "
                            f"{sorted(turn['also_grounds_for'])} != derived {derived_also}. "
                            "An omitted earlier ground is exactly the mistake this "
                            "derivation exists to make impossible."
                        )
                    also = derived_also
                else:
                    # UNPARSED lines carry no readable name, arity or categories,
                    # so no clause after the first can be derived. They must
                    # therefore declare no further grounds.
                    if turn["also_grounds_for"]:
                        raise ConstructionRefusal(
                            f"{fixture_id}: an unparsed line cannot ground a later clause"
                        )
                    also = []
                record.update(
                    {
                        "raw_symbol_name": turn["raw_symbol_name"],
                        "read_symbol_name": turn["read_symbol_name"],
                        "read_arity": turn["read_arity"],
                        "read_argument_categories": turn["read_argument_categories"],
                        "expected_verdict": _expected_verdict(code),
                        "expected_refusal_code": code,
                        "expected_deciding_clause": _expected_clause(code),
                        "also_grounds_for": also,
                        "grounds_derived_by_generator": derivable,
                        "order_sensitive": bool(also),
                        "session_name_subcase": turn["session_name_subcase"],
                        "admitted_in_session_before_this_turn": admitted_running,
                        "rationale": turn["rationale"],
                    }
                )
                if code == "NONE":
                    admitted_running += 1
                    admitted_names.add(turn["read_symbol_name"])
                    session_names.add(turn["read_symbol_name"])
                decl_ids.append(fixture_id)
            else:
                record.update(
                    {
                        "read_applied_head": turn["read_applied_head"],
                        "read_argument_count": turn["read_argument_count"],
                        "expected_disposition": turn["expected_disposition"],
                        "expected_refusal_name": turn["expected_refusal_name"],
                        "cites_declaration_symbol": turn["cites_declaration_symbol"],
                        "binds_subject": turn["binds_subject"],
                        "round_trip_for": turn["round_trip_for"],
                        "rationale": turn["rationale"],
                    }
                )
                if turn["binds_subject"]:
                    session_names.add(turn["binds_subject"])
                if turn["expected_disposition"] == USE_OPAQUE and turn["read_applied_head"]:
                    session_names.add(turn["read_applied_head"])
                use_ids.append(fixture_id)
            fixtures.append(record)

        session_decls = [f for f in fixtures if f["session_id"] == session_id and f["kind"] == "declaration"]
        sessions_out.append(
            {
                "session_id": session_id,
                "gloss": session["gloss"],
                "admitted_cap": SESSION_ADMITTED_CAP,
                "turn_count": len(session["turns"]),
                "declaration_fixture_ids": decl_ids,
                "use_fixture_ids": use_ids,
                "admitted_count": sum(1 for f in session_decls if f["expected_verdict"] == ADMIT_VERDICT),
                "refused_count": sum(1 for f in session_decls if f["expected_verdict"] == REFUSED),
            }
        )

    declarations = [f for f in fixtures if f["kind"] == "declaration"]
    admitted = [f for f in declarations if f["expected_verdict"] == ADMIT_VERDICT]
    uses = [f for f in fixtures if f["kind"] == "use"]

    arities = sorted({f["read_arity"] for f in admitted})
    used_categories = sorted({c for f in admitted for c in f["read_argument_categories"]})

    by_code: dict[str, list[str]] = {}
    for fixture in declarations:
        by_code.setdefault(fixture["expected_refusal_code"], []).append(fixture["fixture_id"])

    b3 = [
        {
            "mutant_id": f"b3-m{index:02d}",
            "vector": vector,
            "target": target,
            "attempt": attempt,
            "expected_outcome": "STOPPED",
            "stopper_kind": kind,
            "stopper_mechanism": mechanism,
        }
        for index, (vector, target, attempt, kind, mechanism) in enumerate(B3_MUTANTS, start=1)
    ]

    library_names = {row["name"] for row in LIBRARY_COLLISION_TARGETS}
    b12 = []
    for index, (name, adjacency, code, note) in enumerate(B12_MUTANTS, start=1):
        normalized = normalize_name(name)
        # B12 mutants get the same derived grounds the declaration fixtures do,
        # so `sum_i`'s dual grounding is a field rather than a sentence.
        grounds = set()
        if normalized.startswith(RESERVED_PREFIXES):
            grounds.add("RESERVED_PREFIX")
        if normalized in library_names:
            grounds.add("COLLIDES_WITH_LIBRARY_SYMBOL")
        earliest = min(grounds, key=lambda c: CLAUSE_RANK[c]) if grounds else "NONE"
        if earliest != code:
            raise ConstructionRefusal(
                f"b12-m{index:02d} (`{normalized}`) expects {code} but the committed order "
                f"decides {earliest} from its derived grounds {sorted(grounds)}"
            )
        b12.append(
            {
                "mutant_id": f"b12-m{index:02d}",
                "line": f"declare {name}/1 (variable)",
                "raw_symbol_name": name,
                "read_symbol_name": normalized,
                "adjacency": adjacency,
                "expected_verdict": _expected_verdict(code),
                "expected_refusal_code": code,
                "expected_deciding_clause": _expected_clause(code),
                "also_grounds_for": sorted(grounds - {code}),
                "order_sensitive": bool(grounds - {code}),
                # B12 is a ROUND TRIP, so an admitted mutant owes a use line in
                # bytes, not a sentence about one. The sentence was a tautology:
                # the generator interpolated the name into the string a test then
                # asserted contained it.
                "use_line": f"suppose {name}(x)" if code == "NONE" else None,
                "expected_resolved_key": normalized if code == "NONE" else None,
                "note": note,
            }
        )

    b9 = build_b9(declarations)

    document: dict[str, Any] = {
        "schema": SCHEMA,
        "stage": STAGE,
        "date": DATE,
        "design": DESIGN,
        "design_clause": DESIGN_CLAUSE,
        "roadmap": ROADMAP,
        "generator": GENERATOR,
        "generator_placement_note": PLACEMENT_NOTE,
        "source_commit": SOURCE_COMMIT,
        "precedent": PRECEDENT,
        "checker_module_registered_as_not_existing": CHECKER_MODULE,
        "generated_note": (
            "Generated artifact. Every count, split, and coverage figure below is "
            "derived by the generator from the authored turn list; nothing is "
            "hand-tallied. A direct edit of this file is a DESIGN §9 stop condition."
        ),
        "scope_note": (
            "Fixture seal, not a run. No checker exists: "
            f"{CHECKER_MODULE} is registered here as not existing at this commit, and "
            "this builder contains no parser by construction. H-PRE seals surface bytes "
            "and the verdict each is expected to receive; H-P0's checker is scored "
            "against these bytes, including DESIGN §9's stop condition that the "
            "declaration form must express them inside the registered grammar without "
            "parser exceptions."
        ),
        "construction_note": (
            "Construction fixtures authored by this repository. The floors "
            f"(>={FLOOR_ADMITTED} admitted, >={FLOOR_ARITIES} arities, "
            f">={FLOOR_CATEGORIES} categories, >={FLOOR_B3_MUTANTS} B3 mutants) are "
            "DECLARED CONSTRUCTION BOUNDS, NOT MEASUREMENTS. They license no population "
            "claim about what people will declare once they can."
        ),
        "honesty_note": (
            "These checks certify ledger-groundedness, never correspondence. An admitted "
            "declaration is well-formed and fresh; it is never true or useful."
        ),
        "generation": {
            "randomness": "none",
            "seed": None,
            "wall_clock": "none; `date` above is a committed constant",
            "environment_reads": "none",
            "files_read": [SCHEMA_PATH],
            "determinism_claim": "re-running the generator reproduces these bytes exactly",
        },
        "surface_form": {
            "declaration": "declare <name>/<arity> (<category>, ...)",
            "declaration_source": "DESIGN-house-rules §6.2 — the row H-P0 registers",
            "use": "suppose <claim>",
            "use_source": "the shipped supposition row; this slice changes no grammar on the use side",
            "name_production": "[a-z][a-z0-9_]*, after NFC + casefold",
            "arity_production": "integer >= 1",
            "normalization": "NFC + casefold on both sides before any comparison (DESIGN §4)",
            "normalization_order": NORMALIZATION_ORDER,
            "normalization_applied_by_generator": (
                "unicodedata.normalize('NFC', raw).casefold() — this generator runs the rule "
                "rather than describing it, and session hr-fx-s5 seals fixtures whose verdicts "
                "differ under `.lower()` or under match-before-normalize."
            ),
        },
        "schema_source": {
            "path": SCHEMA_PATH,
            "sha256_lf": sha256_lf(repo / SCHEMA_PATH),
            "pointer": "$defs.symbolToken.properties.syntactic_category.enum",
            "categories": list(categories),
            "note": (
                "Read out of the committed schema by the generator, never transcribed. "
                "A schema edit moves these bytes and reddens the regeneration test, "
                "which is B8's second mutation with its safety catch on."
            ),
        },
        "clause_order": [
            {"rank": rank + 1, "clause": clause, "refusal_code": code}
            for rank, (clause, code) in enumerate(CLAUSE_ORDER)
        ],
        "clause_order_note": (
            "DESIGN §3, quoted in order; first hit decides. `" + ADMIT_CLAUSE + "` names the "
            "order's only fall-through so that B1's 'exactly one deciding_clause, zero "
            "fall-throughs' is checkable on admissions as well as refusals."
        ),
        "session_name_union_note": (
            "DESIGN §4 unions three sources into COLLIDES_WITH_SESSION_NAME: the session's "
            "admitted symbols, the supposition ledger's binding subjects, and the "
            "applied-term heads of live non-binding suppositions. All three are exercised, "
            "but only two can DECIDE: a name already admitted in this session is reached by "
            "REDEFINITION_ATTEMPT, which the committed order runs first. That is sealed as "
            "an expectation here rather than discovered at H-P0."
        ),
        "use_side_note": (
            "USE_ARITY_MISMATCH is a refusal name in the supposition ledger's existing "
            "vocabulary (beside `assumption_budget` / `unknown_assumption`, "
            "scripts/session_ledger.py:120-122). It is NOT an AdmissibilityVerdict "
            "refusal_code and is deliberately absent from the clause order. Argument-CATEGORY "
            "checking on uses is not claimed at all."
        ),
        "budget": {
            "admitted_per_session_cap": SESSION_ADMITTED_CAP,
            "live_assumption_cap_for_reference": 8,
            "note": (
                "A declared bound in the supposition ledger's style, not a measurement. The "
                "fifth admitted declaration in a session refuses SYMBOL_BUDGET before any "
                "ledger mutation. Because the cap is 4 and the admitted floor is "
                f"{FLOOR_ADMITTED}, the corpus necessarily spans multiple sessions."
            ),
        },
        "sessions": sessions_out,
        "coverage": {
            "admitted_count": len(admitted),
            "admitted_floor": FLOOR_ADMITTED,
            "arities_exercised": arities,
            "arity_floor": FLOOR_ARITIES,
            "categories_exercised": used_categories,
            "category_floor": FLOOR_CATEGORIES,
            "categories_unused": [c for c in categories if c not in used_categories],
            "refusal_code_coverage": {
                code: sorted(by_code.get(code, [])) for _, code in CLAUSE_ORDER
            },
            "order_sensitive_fixture_ids": sorted(
                f["fixture_id"] for f in declarations if f["order_sensitive"]
            ),
        },
        "deleted_codes": {
            "at_design_time": list(DELETED_CODES),
            "at_h_pre": list(DELETED_AT_H_PRE),
            "note": (
                "The U-PRE mechanic: a code no grammatical fixture can fire is deleted with "
                "a recorded reason rather than carried as an unfireable expectation. The two "
                "design-time deletions are recorded for the audit trail and are NOT "
                "resurrected here. H-PRE deletes none of the eight live codes: every one "
                "has at least one fixture, and the generator refuses to write this file "
                "otherwise."
            ),
        },
        "b3_containment": {
            "gate": "B3",
            "vectors": list(B3_VECTORS),
            "mutant_count": len(b3),
            "floor": FLOOR_B3_MUTANTS,
            "note": (
                "These rows are DESCRIPTIONS of attempts. The machinery that stops them "
                "ships at H-P0/H-P1; H-PRE fixes what must be attempted so the later run "
                "cannot choose an easier set. B3 requires 100% stopped by shipped machinery "
                "or the checker — never by a test assertion reading a mutant's name. One "
                "survivor fails the slice (DESIGN §9)."
            ),
            "mutants": b3,
        },
        "b12_round_trip": {
            "gate": "B12",
            "reserved_prefixes": list(RESERVED_PREFIXES),
            "replay_policy": B12_REPLAY_POLICY,
            "mutant_count": len(b12),
            "note": (
                "The census and the sweep test refusal; B12 tests that an ADMITTED name "
                "survives parsing unchanged. Mutants are seeded at reserved-prefix-adjacent "
                "names because that is where the shipped rewrite lives: the ordered parser "
                "fix (the sum_total lane, commit 156e94f) is necessary but not sufficient, "
                "and without this gate there is no standing detector for the regression."
            ),
            "mutants": b12,
        },
        "b9_class_balance": b9,
        "counts": {
            "sessions": len(sessions_out),
            "fixtures_total": len(fixtures),
            "declaration_fixtures": len(declarations),
            "use_fixtures": len(uses),
            "admitted": len(admitted),
            "refused": len(declarations) - len(admitted),
            "b3_mutants": len(b3),
            "b12_mutants": len(b12),
            "b12_mutants_expected_admitted": sum(
                1 for m in b12 if m["expected_verdict"] == ADMIT_VERDICT
            ),
            "use_checked": sum(1 for f in uses if f["expected_disposition"] == USE_CHECKED),
            "use_arity_mismatch": sum(
                1 for f in uses if f["expected_disposition"] == USE_ARITY_MISMATCH
            ),
            "use_opaque_atom": sum(1 for f in uses if f["expected_disposition"] == USE_OPAQUE),
            "use_binding_unchanged": sum(
                1 for f in uses if f["expected_disposition"] == USE_BINDING_UNCHANGED
            ),
            "round_trip_pairs": sum(1 for f in uses if f["round_trip_for"]),
        },
        "library_collision_targets": [dict(row) for row in LIBRARY_COLLISION_TARGETS],
        "census_source_findings": [dict(row) for row in CENSUS_SOURCE_FINDINGS],
        "fixtures": fixtures,
    }

    check_construction(document, categories)
    return document


def build_b9(declarations: list[dict[str, Any]]) -> dict[str, Any]:
    """B9's split rule and class balance, sealed here so the anchor cannot move.

    DESIGN §7 B9 anchors the blind control's threshold to *the scored half's
    majority-class rate*. Because the fixture corpus is self-authored, that
    rate is a number the author influences — so the split rule and the balance
    are committed at H-PRE, before any surface-only admitter exists to be
    fitted, and reported beside the agreement figure at H-P1.
    """

    fit: list[str] = []
    scored: list[str] = []
    for index, fixture in enumerate(declarations):
        (fit if index % 2 == 0 else scored).append(fixture["fixture_id"])

    verdict_by_id = {f["fixture_id"]: f["expected_verdict"] for f in declarations}

    def balance(ids: list[str]) -> dict[str, Any]:
        admitted = sum(1 for i in ids if verdict_by_id[i] == ADMIT_VERDICT)
        refused = len(ids) - admitted
        majority = max(admitted, refused)
        return {
            "n": len(ids),
            "admitted": admitted,
            "refused": refused,
            "majority_class": ADMIT_VERDICT if admitted > refused else REFUSED,
            # A tie resolves to REFUSED and is recorded rather than left to be
            # read off the comparison above: the rate is 0.5 either way, so the
            # anchor is unaffected, but the class NAME should not be an accident.
            "majority_class_is_a_tie": admitted == refused,
            "majority_class_rate": round(majority / len(ids), 6),
        }

    scored_balance = balance(scored)
    return {
        "gate": "B9",
        "scored_verdict_space": [ADMIT_VERDICT, REFUSED],
        "population": (
            "declaration fixtures only. Use fixtures carry supposition-ledger "
            "dispositions, not AdmissibilityVerdicts, and B12 mutants are replayed "
            "outside the authored sessions — neither is scored by the blind control."
        ),
        "split_rule": (
            "Enumerate the declaration fixtures in this artifact's sealed `fixtures` "
            "order, 0-based. Even index -> FIT half; odd index -> SCORED (held-out) "
            "half. Deterministic, committed before any admitter exists, and "
            "recomputable from these bytes alone."
        ),
        "split_rule_is_stratified_note": (
            "Disclosed rather than glossed: the sealed fixture order is CLUSTERED (eight "
            "consecutive UNPARSED rows, admissions in blocks), so an even/odd parity split "
            "is effectively STRATIFIED — the two halves get near-identical class "
            "distributions rather than independently drawn ones. It is deterministic and "
            "committed before any admitter exists, which is what B9 requires, and the bias "
            "runs the conservative way: matched distributions RAISE a surface-only "
            "admitter's expected agreement and so make the voiding sentence easier to fire, "
            "not harder."
        ),
        "fit_half_fixture_ids": fit,
        "scored_half_fixture_ids": scored,
        "corpus_balance": balance([f["fixture_id"] for f in declarations]),
        "fit_half_balance": balance(fit),
        "scored_half_balance": scored_balance,
        "majority_class_anchor": scored_balance["majority_class_rate"],
        "declared_margin_points": 10,
        "margin_note": "A declared bound, not a measurement.",
        "voiding_sentence": (
            "if the surface-only admitter's out-of-half agreement with the checker "
            "exceeds the scored half's majority-class rate by more than ten points, the "
            "verdict is separable from every ledger and schema input, the capability is "
            "void, and the slice ships as an honest negative."
        ),
        "void_threshold": round(scored_balance["majority_class_rate"] + 0.10, 6),
        "admitter_inputs_allowed": [
            "token count",
            "line length",
            "presence of the command word",
        ],
        "admitter_inputs_forbidden": ["the census", "the schema enum", "the ledger"],
    }


# --------------------------------------------------------------------------
# Construction checks. A violated floor refuses; it does not write.
# --------------------------------------------------------------------------


def check_construction(document: dict[str, Any], categories: tuple[str, ...]) -> None:
    declarations = [f for f in document["fixtures"] if f["kind"] == "declaration"]
    admitted = [f for f in declarations if f["expected_verdict"] == ADMIT_VERDICT]

    if len(admitted) < FLOOR_ADMITTED:
        raise ConstructionRefusal(
            f"{len(admitted)} admitted fixtures; the floor is {FLOOR_ADMITTED}"
        )

    arities = {f["read_arity"] for f in admitted}
    if len(arities) < FLOOR_ARITIES:
        raise ConstructionRefusal(
            f"{len(arities)} distinct admitted arities; the floor is {FLOOR_ARITIES}"
        )

    used = {c for f in admitted for c in f["read_argument_categories"]}
    if len(used) < FLOOR_CATEGORIES:
        raise ConstructionRefusal(
            f"{len(used)} distinct admitted categories; the floor is {FLOOR_CATEGORIES}"
        )
    outside = sorted(used - set(categories))
    if outside:
        raise ConstructionRefusal(
            f"admitted fixtures cite categories outside the schema enum: {outside}"
        )

    # Every refusal code fires, or is deleted with a reason. None may be silent.
    fired = {f["expected_refusal_code"] for f in declarations}
    fired |= {m["expected_refusal_code"] for m in document["b12_round_trip"]["mutants"]}
    deleted_here = {row["code"] for row in document["deleted_codes"]["at_h_pre"]}
    for _, code in CLAUSE_ORDER:
        if code not in fired and code not in deleted_here:
            raise ConstructionRefusal(
                f"refusal code {code} is neither fired by a fixture nor deleted with a "
                "reason; H-PRE may not carry an unfireable expectation"
            )
    # A design-time-deleted code cannot reach this point at all: `_expected_clause`
    # refuses any code outside the committed eight while the fixtures are still
    # being built, which is earlier and stricter than a check here could be. The
    # enforcement is named rather than duplicated, because a second check that can
    # never fire reads like coverage and is not.

    # Clause/code agreement, and the committed order actually deciding.
    for fixture in declarations:
        code = fixture["expected_refusal_code"]
        if fixture["expected_deciding_clause"] != _expected_clause(code):
            raise ConstructionRefusal(f"{fixture['fixture_id']}: clause/code disagreement")
        grounds = set(fixture["also_grounds_for"])
        if code != "NONE" and grounds:
            earliest = min(grounds | {code}, key=lambda c: CLAUSE_RANK[c])
            if earliest != code:
                raise ConstructionRefusal(
                    f"{fixture['fixture_id']}: expects {code} but {earliest} runs earlier "
                    "in the committed order"
                )
        if code == "NONE" and grounds:
            raise ConstructionRefusal(
                f"{fixture['fixture_id']}: an admitted line may ground no refusal clause"
            )

    order_sensitive = [f for f in declarations if f["order_sensitive"]]
    if len(order_sensitive) < 2:
        raise ConstructionRefusal(
            f"{len(order_sensitive)} order-sensitive fixtures; at least two are required"
        )

    # Session arithmetic: no session admits more than the cap, and the
    # SYMBOL_BUDGET fixture really is a fifth declaration in a full session.
    # This reads the derived SUMMARY, not the turn list, so it is not the same
    # property `derive_grounds` already enforces: it catches a bug in this
    # generator's own counting rather than a mis-authored fixture.
    for session in document["sessions"]:
        if session["admitted_count"] > SESSION_ADMITTED_CAP:
            raise ConstructionRefusal(
                f"{session['session_id']} admits {session['admitted_count']}; the cap is "
                f"{SESSION_ADMITTED_CAP}"
            )
    budget_fixtures = [f for f in declarations if f["expected_refusal_code"] == "SYMBOL_BUDGET"]
    if not budget_fixtures:
        raise ConstructionRefusal("no SYMBOL_BUDGET fixture")
    for fixture in budget_fixtures:
        if fixture["admitted_in_session_before_this_turn"] != SESSION_ADMITTED_CAP:
            raise ConstructionRefusal(
                f"{fixture['fixture_id']} expects SYMBOL_BUDGET but its session had "
                f"{fixture['admitted_in_session_before_this_turn']} admitted symbols before it"
            )
    if len({f["session_id"] for f in declarations}) < 3:
        raise ConstructionRefusal("the declaration corpus spans fewer than three sessions")

    # B3 and B12.
    b3 = document["b3_containment"]["mutants"]
    if len(b3) < FLOOR_B3_MUTANTS:
        raise ConstructionRefusal(f"{len(b3)} B3 mutants; the floor is {FLOOR_B3_MUTANTS}")
    if {m["vector"] for m in b3} != set(B3_VECTORS):
        raise ConstructionRefusal("B3 mutants do not cover all four declared vectors")
    # B3's wording is "stopped by the shipped machinery or the checker". A row
    # whose stopper is a design argument is a row H-P1 could only score by
    # agreeing with the author, so the vocabulary is closed and enforced.
    for mutant in b3:
        if mutant["stopper_kind"] not in STOPPER_KINDS:
            raise ConstructionRefusal(
                f"{mutant['mutant_id']}: stopper_kind {mutant['stopper_kind']!r} is not one "
                f"of {list(STOPPER_KINDS)}; B3 is not satisfied by an argument"
            )
        if len(mutant["stopper_mechanism"].split()) < 6:
            raise ConstructionRefusal(
                f"{mutant['mutant_id']}: stopper_mechanism must name a module, digest or "
                "sweep, not a gesture"
            )

    # B12 is a ROUND TRIP: "for every admitted fixture symbol, declare then use".
    round_trips = {
        f["round_trip_for"] for f in document["fixtures"] if f.get("round_trip_for")
    }
    missing = sorted({f["read_symbol_name"] for f in admitted} - round_trips)
    if missing:
        raise ConstructionRefusal(
            f"admitted symbols with no declare-then-use round trip: {missing}. B12 says "
            "EVERY admitted fixture symbol, and a seal that leaves the choice to H-P1 is "
            "the choice this seal exists to remove."
        )
    for fixture in document["fixtures"]:
        target = fixture.get("round_trip_for")
        if target and fixture["read_applied_head"] != target:
            raise ConstructionRefusal(
                f"{fixture['fixture_id']}: round trip claims `{target}` but applies "
                f"`{fixture['read_applied_head']}`"
            )

    # DESIGN §4's union has three members; each is named by a fixture so the
    # three cannot be collapsed into "two codes are present".
    subcases = {
        f["session_name_subcase"] for f in declarations if f["session_name_subcase"]
    }
    expected_subcases = {
        "already_admitted_symbol",
        "supposition_binding_subject",
        "live_non_binding_supposition_head",
    }
    if subcases != expected_subcases:
        raise ConstructionRefusal(
            f"session-name sub-cases exercised {sorted(subcases)}, expected "
            f"{sorted(expected_subcases)}"
        )

    b12 = document["b12_round_trip"]["mutants"]
    if not b12:
        raise ConstructionRefusal("no B12 mutants")
    for mutant in b12:
        name = mutant["read_symbol_name"]
        leading = any(name.startswith(prefix) for prefix in RESERVED_PREFIXES)
        if mutant["expected_refusal_code"] == "RESERVED_PREFIX" and not leading:
            raise ConstructionRefusal(
                f"{mutant['mutant_id']} expects RESERVED_PREFIX but `{name}` starts with no "
                "reserved prefix"
            )
        if mutant["expected_verdict"] == ADMIT_VERDICT:
            if leading:
                raise ConstructionRefusal(
                    f"{mutant['mutant_id']} expects admission but `{name}` starts with a "
                    "reserved prefix"
                )
            if not mutant["use_line"] or mutant["expected_resolved_key"] != name:
                raise ConstructionRefusal(
                    f"{mutant['mutant_id']} is admitted but owes a use line resolving to "
                    f"`{name}`; B12 scores a round trip, not a sentence about one"
                )
    if not any(prefix in {m["adjacency"] for m in b12} for prefix in ("prefix_exactly",)):
        raise ConstructionRefusal("B12 does not exercise a bare reserved prefix")
    if not any(m["expected_verdict"] == ADMIT_VERDICT for m in b12):
        raise ConstructionRefusal(
            "no B12 mutant is expected to be admitted; a round-trip gate with no admitted "
            "name tests nothing"
        )

    # The collision targets have to be real.
    if not document["library_collision_targets"]:
        raise ConstructionRefusal(
            "no library collision target is recorded; B2's fixture would name nothing"
        )
    library_fixtures = [
        f for f in declarations if f["expected_refusal_code"] == "COLLIDES_WITH_LIBRARY_SYMBOL"
    ]
    targets = {row["name"] for row in document["library_collision_targets"]}
    grounded = library_fixtures + [
        f for f in declarations if "COLLIDES_WITH_LIBRARY_SYMBOL" in f["also_grounds_for"]
    ]
    # No "is this name a recorded target?" loop here any more: `derive_grounds`
    # decides the library ground FROM the recorded targets, so a fixture naming
    # an invented head is refused while the fixtures are still being built, and
    # a check here could never fire. Naming the live enforcement beats keeping a
    # second one that reads like coverage.
    if not library_fixtures:
        raise ConstructionRefusal("no COLLIDES_WITH_LIBRARY_SYMBOL fixture")
    for mutant in document["b12_round_trip"]["mutants"]:
        if (
            mutant["expected_refusal_code"] == "COLLIDES_WITH_LIBRARY_SYMBOL"
            and mutant["read_symbol_name"] not in targets
        ):
            raise ConstructionRefusal(
                f"{mutant['mutant_id']} expects a library collision on "
                f"`{mutant['read_symbol_name']}`, which is not a recorded census target"
            )
    unused = (
        targets
        - {f["read_symbol_name"] for f in grounded}
        - {
            m["read_symbol_name"]
            for m in document["b12_round_trip"]["mutants"]
            # Only a mutant that actually SCORES the collision counts as reaching
            # the target; an admitted mutant that merely shares the name does not.
            if m["expected_refusal_code"] == "COLLIDES_WITH_LIBRARY_SYMBOL"
            or "COLLIDES_WITH_LIBRARY_SYMBOL" in m["also_grounds_for"]
        }
    )
    if unused:
        raise ConstructionRefusal(
            f"recorded census targets no fixture reaches: {sorted(unused)} — a target that "
            "scores nothing is provenance theatre"
        )

    # B9's halves partition the declaration corpus exactly once.
    b9 = document["b9_class_balance"]
    halves = b9["fit_half_fixture_ids"] + b9["scored_half_fixture_ids"]
    if sorted(halves) != sorted(f["fixture_id"] for f in declarations):
        raise ConstructionRefusal("B9's two halves are not a partition of the declaration corpus")
    if not b9["scored_half_fixture_ids"]:
        raise ConstructionRefusal("B9's scored half is empty")


# --------------------------------------------------------------------------
# Writing. Byte-deterministic, LF, trailing newline.
# --------------------------------------------------------------------------


def render(document: dict[str, Any]) -> bytes:
    return (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def summary(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "counts": document["counts"],
        "coverage": document["coverage"],
        "sessions": [
            {k: session[k] for k in ("session_id", "admitted_count", "refused_count", "turn_count")}
            for session in document["sessions"]
        ],
        "b9": {
            k: document["b9_class_balance"][k]
            for k in (
                "corpus_balance",
                "fit_half_balance",
                "scored_half_balance",
                "majority_class_anchor",
                "void_threshold",
            )
        },
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0] or GENERATOR)
    parser.add_argument("--out", default=DEFAULT_OUT, help=f"output path (default {DEFAULT_OUT})")
    parser.add_argument(
        "--check",
        action="store_true",
        help="regenerate and compare against the committed file; write nothing",
    )
    parser.add_argument("--summary", action="store_true", help="print the derived counts as JSON")
    args = parser.parse_args(argv)

    try:
        document = build_fixtures(REPO)
    except ConstructionRefusal as exc:
        print(f"BLOCKED CONSTRUCTION: {exc}", file=sys.stderr)
        return 2

    path = Path(args.out)
    path = path if path.is_absolute() else REPO / path
    payload = render(document)

    # --check outranks --summary: a CI line carrying both must not report green
    # while checking nothing.
    if args.summary and not args.check:
        print(json.dumps(summary(document), indent=2, ensure_ascii=False))
        return 0

    if args.check:
        if not path.exists():
            print(f"MISSING: {args.out}", file=sys.stderr)
            return 1
        if path.read_bytes() != payload:
            print(f"DRIFT: {args.out} is not this generator's output", file=sys.stderr)
            return 1
        print(f"ok {args.out}")
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
