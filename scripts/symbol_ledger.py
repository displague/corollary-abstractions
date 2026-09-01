#!/usr/bin/env python3
"""The symbol ledger — a person declares a relation symbol, the system decides.

`docs/DESIGN-house-rules.md` is the contract and its field names are binding.
This module is H-P0's new trusted code: the two records of §3, the
admissibility checker with §3's committed clause order, and the use-side
arity check of §3's last paragraph. There is no learned component anywhere in
it, and B11 asserts that mechanically rather than trusting this sentence
(`echo_population_audit.import_closure`; the closure of this file is three
exact modules).

## What is genuinely new here

A person can already *suppose* a claim. A supposition that is not a binding
is held as an **opaque atom**: `suppose parent(alice, bob)` stores normalized
text, and the system cannot tell a well-formed use of the person's own
vocabulary from a typo — because the person has no way to tell the system
what their vocabulary *is*. This module gives them the way, and it gives the
system exactly one thing to do with it: admit the symbol into a
session-scoped ledger, or refuse it with **one** deciding clause.

It certifies **ledger-groundedness, never correspondence.** An admitted
declaration is well-formed and fresh. It is never true, and never useful.

## Built in `AssumptionSet`'s discipline, not pretending to be it

`session_ledger.AssumptionSet` supplies the shape: a declared cap,
supersession, typed refusal names, and a record that says what it consumed.
This module borrows all four and none of the machinery — no MAC, no read
barrier, no journal. A declaration is not an assumption: it introduces
vocabulary rather than content, so it has no normal form to cite and nothing
for a barrier to guard.

## The clause order is the mechanism, not a comment

§3 commits the evaluation order and this module is where it is committed:

    UNPARSED, ARITY_CATEGORY_MISMATCH, CATEGORY_NOT_IN_SCHEMA,
    RESERVED_PREFIX, COLLIDES_WITH_LIBRARY_SYMBOL, REDEFINITION_ATTEMPT,
    COLLIDES_WITH_SESSION_NAME, SYMBOL_BUDGET

**First hit decides**, which is what makes "exactly one deciding clause" true
rather than asserted. :func:`grounds_for` computes *every* clause that holds
and :func:`decide` takes the first in this order; the two are separate
functions so a test can check that a line's later grounds really are later,
which is what H-PRE's `also_grounds_for` fixtures exist to check. The
function is **total**: every input string receives exactly one verdict, and
the default is refusal — `c9_admit` is reached only by falling off the end of
eight clauses that each said no.

`SYMBOL_BUDGET` is last on purpose. A fifth declaration that is *also*
ill-formed is refused for being ill-formed, because telling a person "you are
out of budget" when their line would have been refused anyway is telling them
the less useful of two true things.

## Normalization, in one place

NFC, then casefold, then match `^[a-z][a-z0-9_]*$` against the RESULT. The
order is load-bearing and H-PRE sealed fixtures that disagree under any other
one: `SUM_TOTAL` is read as `sum_total` though its raw bytes match no
production, and a casefold *expansion* (U+FB01 → `fi`, U+00DF → `ss`) can
carry a surface INTO the production that the raw bytes are outside of — while
a combining accent still refuses, so the rule cannot be read as "normalize
until it fits".

That expansion is also why B12 is worth having: for `ﬁrst_of` the ledger key
(`first_of`) and the bytes the person typed are **not** the same string, so
"byte-identical to the ledger key" and "byte-identical to what was typed"
come apart, and the gate asks for the first.

## Non-persistence

Neither record type is registered in `session_state._TYPES`, so `encode`
refuses both. That is a fact and a test, but it is deliberately **not** the
fence: a symbol could in principle ride a registered type. The fence is B5 —
no written session document, journal, or durable artifact contains an
admitted symbol name, checked over the run's full output tree. The verdict
travels with its scope: this evidences *no writes observed under this
harness*, never *cannot write*.

## The budget

At most **4** admitted symbols per session. `LIVE_ASSUMPTION_CAP` is 8;
declarations are heavier objects; the bound is **declared, not measured**.
The fifth is `SYMBOL_BUDGET`, refused before any ledger mutation — which is
structural here rather than a promise, because :func:`decide` is pure and
only :meth:`SymbolLedger.admit` mutates anything.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field, replace
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

DECLARATION_SCHEMA = "corollary.person-symbol-declaration/1"
VERDICT_SCHEMA = "corollary.admissibility-verdict/1"

#: The command word the registered grammar dispatches on.
DECLARE_COMMAND = "declare"

#: §3's budget. A declared bound in the supposition ledger's style.
SYMBOL_CAP = 4

#: Where the two committed inputs live. The checker cites BOTH by digest in
#: every verdict, so a verdict can always say what it was decided against.
CENSUS_PATH = "experiments/symbol_census.json"
SCHEMA_PATH = "schema/equation-node.schema.json"
SCHEMA_POINTER = "$defs.symbolToken.properties.syntactic_category.enum"

VERDICT_ADMITTED = "ADMITTED_DECLARED_SYMBOL"
VERDICT_REFUSED = "REFUSED"

REFUSAL_NONE = "NONE"

#: §3's use-side refusal name, and it lives HERE rather than where the design
#: said to put it. That deviation is deliberate, forced by the code, and
#: recorded rather than quietly taken.
#:
#: DESIGN §3 says `USE_ARITY_MISMATCH` "is a new refusal name in the
#: supposition ledger's existing refusal vocabulary (the `assumption_budget` /
#: `unknown_assumption` family, `scripts/session_ledger.py:120-122`)". Adding
#: it there is **refused by the shipped tree**: `session_ledger.py` is one of
#: the two `RECORDER_MODULES` that `session_recorder.recorder_code_digest`
#: pins, that digest is frozen in `session_ledger_prereg.json`'s amendment 1,
#: and `record_session_corpus.py` refuses to record under a recorder whose
#: bytes moved. Prereg amendment 6 states the rule in as many words — *"the
#: two recorder modules do not accept edits, cosmetic or otherwise, for as
#: long as the corpus they recorded is sealed"* — and the repository has
#: enforced it twice by reverting the edit rather than moving the pin, once
#: for a comment refresh and once (commit `0cf7dee`) for a new module-level
#: constant of exactly this shape, which "moved to the replayer, which no
#: protocol pins".
#:
#: So the name moves to the new unpinned module and the design's INTENT is
#: kept intact: it is still not an `AdmissibilityVerdict` code, still absent
#: from the clause order, and still carried on the supposition route beside
#: `unknown_assumption` — `harness.USE_ARITY_MISMATCH` is the route's own
#: reference, exactly as `harness.UNKNOWN_ASSUMPTION` already duplicates
#: `session_ledger.REFUSAL_UNKNOWN_ASSUMPTION` for the same reason. A test
#: asserts the two spellings agree and that the recorder digest never moved.
#:
#: Upper-cased against that family's lower-case habit because DESIGN §3 and
#: the sealed H-PRE fixtures both spell it that way, and the seal predates
#: this constant.
REFUSAL_USE_ARITY_MISMATCH = "USE_ARITY_MISMATCH"

#: §3's committed clause order. `(clause_id, refusal_code)`, first hit decides.
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

#: The order's only fall-through, named so B1's "exactly one deciding_clause,
#: zero fall-throughs" is checkable on admissions as well as on refusals.
CLAUSE_ADMIT = "c9_admit"

REFUSAL_CODES = tuple(code for _, code in CLAUSE_ORDER)
CLAUSE_IDS = tuple(clause for clause, _ in CLAUSE_ORDER)
_CODE_BY_CLAUSE = dict(CLAUSE_ORDER)
_CLAUSE_BY_CODE = {code: clause for clause, code in CLAUSE_ORDER}

#: The declared alphabet, matched against the NORMALIZED surface.
NAME_PRODUCTION = r"^[a-z][a-z0-9_]*$"
_NAME_RE = re.compile(NAME_PRODUCTION)

#: `declare <name>/<arity> (<category>, ...)`, minus the command word.
#: `[^\s/()]+` for the name so a malformed name still REACHES the production
#: check and refuses UNPARSED there, rather than failing to match and
#: refusing UNPARSED for a different reason. Same verdict either way; this
#: spelling keeps the reason honest.
_DECLARATION_RE = re.compile(
    r"^(?P<name>[^\s/()]+)/(?P<arity>\d+)\s*\((?P<categories>[^()]*)\)$"
)

#: The three sub-cases §4 unions into COLLIDES_WITH_SESSION_NAME.
SESSION_NAME_SUBCASES = (
    "already_admitted_symbol",
    "supposition_binding_subject",
    "live_non_binding_supposition_head",
)


class SymbolLedgerError(RuntimeError):
    """A committed input this module cannot decide against.

    Deliberately NOT raised by any admissibility path: the checker is total
    over input strings. This is raised only when the census or the schema is
    missing or malformed, which is a broken tree rather than a bad line.
    """


# --------------------------------------------------------------------------
# canonical digests
# --------------------------------------------------------------------------


def canonical(value) -> str:
    """SPEC §4.1's canonical-JSON/compact — the same spelling the session
    ledger digests with, so two ledgers standing beside each other do not
    disagree about what a record's identity is."""

    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha256_lf(path: Path) -> str:
    """The digest every prereg and every census in this repository records."""

    return hashlib.sha256(
        Path(path).read_bytes().replace(b"\r\n", b"\n")
    ).hexdigest()


# --------------------------------------------------------------------------
# normalization
# --------------------------------------------------------------------------


def normalize(raw: str) -> str:
    """§4's rule, run rather than described. NFC first, then casefold."""

    return unicodedata.normalize("NFC", raw).casefold()


def is_name_shaped(normalized: str) -> bool:
    """Whether a NORMALIZED surface is spelled by the declared alphabet."""

    return bool(_NAME_RE.match(normalized))


# --------------------------------------------------------------------------
# the committed inputs
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class CommittedInputs:
    """The census and the schema enum, with the digests a verdict cites.

    Held as one object because a verdict that cited one and not the other
    would be a verdict you could not reproduce.
    """

    census_path: str
    census_sha256_lf: str
    equality_members: frozenset[str]
    reserved_prefixes: tuple[str, ...]
    schema_path: str
    schema_sha256_lf: str
    categories: frozenset[str]

    @property
    def census_ref(self) -> dict:
        return {"path": self.census_path, "sha256_lf": self.census_sha256_lf}


def load_inputs(
    repo: Path | None = None,
    *,
    census_path: str = CENSUS_PATH,
    schema_path: str = SCHEMA_PATH,
) -> CommittedInputs:
    """Read the committed census and the committed schema enum.

    Both paths are parameters so B8's two corruption arms can point this at a
    mutated COPY without touching the committed tree — which is the whole
    reason B8 can be a test rather than a ritual.
    """

    root = Path(repo) if repo is not None else REPO
    census_file = root / census_path
    schema_file = root / schema_path
    if not census_file.is_file():
        raise SymbolLedgerError(f"census artifact does not exist: {census_path}")
    if not schema_file.is_file():
        raise SymbolLedgerError(f"schema does not exist: {schema_path}")

    census = json.loads(census_file.read_text(encoding="utf-8"))
    members = census.get("equality_members")
    guard = (census.get("prefix_guard") or {}).get("prefixes")
    if not isinstance(members, list) or not isinstance(guard, list):
        raise SymbolLedgerError(
            f"{census_path}: expected `equality_members` and "
            "`prefix_guard.prefixes` lists"
        )

    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    try:
        enum = schema["$defs"]["symbolToken"]["properties"]["syntactic_category"][
            "enum"
        ]
    except (KeyError, TypeError) as exc:
        raise SymbolLedgerError(
            f"{schema_path}: no enum at {SCHEMA_POINTER}"
        ) from exc
    if not isinstance(enum, list) or not enum:
        raise SymbolLedgerError(f"{schema_path}: {SCHEMA_POINTER} is not a list")

    return CommittedInputs(
        census_path=census_path,
        census_sha256_lf=sha256_lf(census_file),
        equality_members=frozenset(str(name) for name in members),
        reserved_prefixes=tuple(str(prefix) for prefix in guard),
        schema_path=schema_path,
        schema_sha256_lf=sha256_lf(schema_file),
        categories=frozenset(str(name) for name in enum),
    )


# --------------------------------------------------------------------------
# §3's two records
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PersonSymbolDeclaration:
    """§3's PersonSymbolDeclaration. Field names are the contract.

    Deliberately NOT registered in `session_state._TYPES`: `encode` refuses
    it, which is a lifetime fact this module states and a test asserts. It is
    not the fence — see the module docstring — it is the codec agreeing with
    the fence.
    """

    schema: str
    decl_id: str
    session_id: str
    turn_index: int
    source_line: str
    symbol_name: str
    arity: int
    argument_categories: tuple[str, ...]

    def payload(self) -> dict:
        return {
            "schema": self.schema,
            "decl_id": self.decl_id,
            "session_id": self.session_id,
            "turn_index": self.turn_index,
            "source_line": self.source_line,
            "symbol_name": self.symbol_name,
            "arity": self.arity,
            "argument_categories": list(self.argument_categories),
        }

    def record(self) -> dict:
        return self.payload()


@dataclass(frozen=True)
class AdmissibilityVerdict:
    """§3's AdmissibilityVerdict. Field names are the contract."""

    schema: str
    verdict_id: str
    decl_id: str
    verdict: str
    refusal_code: str
    deciding_clause: str
    schema_digest: str
    census_ref: dict

    def payload(self) -> dict:
        return {
            "schema": self.schema,
            "verdict_id": self.verdict_id,
            "decl_id": self.decl_id,
            "verdict": self.verdict,
            "refusal_code": self.refusal_code,
            "deciding_clause": self.deciding_clause,
            "schema_digest": self.schema_digest,
            "census_ref": dict(self.census_ref),
        }

    def record(self) -> dict:
        return self.payload()

    @property
    def admitted(self) -> bool:
        return self.verdict == VERDICT_ADMITTED


def _declaration_id(record: PersonSymbolDeclaration) -> str:
    """§3: the canonical digest of the record with `decl_id` empty."""

    payload = record.payload()
    payload["decl_id"] = ""
    return digest(payload)


def _verdict_id(record: AdmissibilityVerdict) -> str:
    """The same rule, applied to the verdict: its own id is not its input."""

    payload = record.payload()
    payload["verdict_id"] = ""
    return digest(payload)


# --------------------------------------------------------------------------
# the declaration production
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ParsedDeclaration:
    """A line that reached the production. Says nothing about admissibility."""

    raw_symbol_name: str
    symbol_name: str
    arity: int
    argument_categories: tuple[str, ...]


def parse_declaration(source_line: str) -> ParsedDeclaration | None:
    """`<name>/<arity> (<category>, ...)`, or None. **Never raises.**

    Totality here is the §9 stop condition: the sealed fixtures must be
    expressible in the registered grammar *without parser exceptions*, and
    every fixture the design calls UNPARSED must arrive as an UNPARSED
    VERDICT rather than as a raised exception. So this function returns None
    for every malformed line and there is no path out of it that throws.

    What returning a ParsedDeclaration does NOT mean: the arity and the
    category count may disagree, and the categories may not be in the schema.
    Those are clauses 2 and 3 and they are decided later, in order. Folding
    them in here would collapse three distinct refusals into one and make
    `declare owns_pet/2 (hedgehog)` unable to say that the *count* is what is
    wrong.
    """

    normalized = normalize(source_line).strip()
    match = _DECLARATION_RE.match(normalized)
    if match is None:
        return None

    name = match.group("name")
    if not is_name_shaped(name):
        return None

    try:
        arity = int(match.group("arity"))
    except ValueError:  # pragma: no cover - the group is \d+
        return None
    if arity < 1:
        # §3: `arity` is an integer >= 1. A zero-ary declaration is not a
        # relation symbol with argument slots, and the record shape has no
        # way to hold one.
        return None

    inner = match.group("categories").strip()
    if inner:
        categories = tuple(part.strip() for part in inner.split(","))
        if any(not part for part in categories):
            # `(a, )` or `(a,,b)`: a category slot with nothing in it is a
            # malformed list, not a category that happens to be wrong.
            return None
    else:
        categories = ()

    return ParsedDeclaration(
        raw_symbol_name=source_line.strip().split("/", 1)[0],
        symbol_name=name,
        arity=arity,
        argument_categories=categories,
    )


# --------------------------------------------------------------------------
# the admissibility checker
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class SessionNames:
    """§4's three-source union for COLLIDES_WITH_SESSION_NAME.

    Kept as three named sets rather than one, because the artifact and the
    tests both need to say WHICH sub-case decided, and a union that has
    forgotten where its members came from cannot.
    """

    admitted_symbols: frozenset[str] = frozenset()
    binding_subjects: frozenset[str] = frozenset()
    applied_heads: frozenset[str] = frozenset()

    @property
    def union(self) -> frozenset[str]:
        return self.admitted_symbols | self.binding_subjects | self.applied_heads

    def subcase(self, name: str) -> str | None:
        """Which sub-case a name is in, in §4's own listing order."""

        if name in self.admitted_symbols:
            return "already_admitted_symbol"
        if name in self.binding_subjects:
            return "supposition_binding_subject"
        if name in self.applied_heads:
            return "live_non_binding_supposition_head"
        return None


def grounds_for(
    parsed: ParsedDeclaration | None,
    inputs: CommittedInputs,
    *,
    admitted: tuple[str, ...] = (),
    session_names: SessionNames | None = None,
) -> tuple[str, ...]:
    """EVERY refusal code that holds, in clause order. Never raises.

    :func:`decide` takes `[0]` of this. Computing all of them is what lets a
    test assert that a fixture's *later* grounds really are later — H-PRE's
    `also_grounds_for`, which exists because a fixture that omitted an
    EARLIER ground would be structurally invisible to a check that only
    verified the expected code is earliest among the declared ones.
    """

    if parsed is None:
        # Nothing else is evaluable: there is no name to test a prefix
        # against and no category list to count. UNPARSED is not merely
        # first here, it is the only clause with an input.
        return ("UNPARSED",)

    names = session_names or SessionNames()
    held: list[str] = []

    if len(parsed.argument_categories) != parsed.arity:
        held.append("ARITY_CATEGORY_MISMATCH")
    if any(
        category not in inputs.categories
        for category in parsed.argument_categories
    ):
        held.append("CATEGORY_NOT_IN_SCHEMA")
    if parsed.symbol_name.startswith(tuple(inputs.reserved_prefixes)):
        held.append("RESERVED_PREFIX")
    if parsed.symbol_name in inputs.equality_members:
        held.append("COLLIDES_WITH_LIBRARY_SYMBOL")
    if parsed.symbol_name in admitted:
        held.append("REDEFINITION_ATTEMPT")
    if parsed.symbol_name in names.union:
        held.append("COLLIDES_WITH_SESSION_NAME")
    if len(admitted) >= SYMBOL_CAP:
        held.append("SYMBOL_BUDGET")

    return tuple(held)


@dataclass(frozen=True)
class Decision:
    """One line, decided. The two records plus what a caller needs to act."""

    declaration: PersonSymbolDeclaration | None
    verdict: AdmissibilityVerdict
    parsed: ParsedDeclaration | None
    grounds: tuple[str, ...]
    session_name_subcase: str | None

    @property
    def admitted(self) -> bool:
        return self.verdict.admitted


def decide(
    source_line: str,
    inputs: CommittedInputs,
    *,
    session_id: str,
    turn_index: int,
    admitted: tuple[str, ...] = (),
    session_names: SessionNames | None = None,
) -> Decision:
    """The TOTAL admissibility function. One verdict, one deciding clause.

    Pure: it reads the ledger's state and mutates nothing. That is what makes
    §3's "SYMBOL_BUDGET is refused before any ledger mutation" structural
    rather than a promise — there is no mutation in here to be before.
    """

    parsed = parse_declaration(source_line)
    held = grounds_for(
        parsed, inputs, admitted=admitted, session_names=session_names
    )

    declaration: PersonSymbolDeclaration | None = None
    if parsed is not None:
        declaration = PersonSymbolDeclaration(
            schema=DECLARATION_SCHEMA,
            decl_id="",
            session_id=session_id,
            turn_index=turn_index,
            source_line=source_line,
            symbol_name=parsed.symbol_name,
            arity=parsed.arity,
            argument_categories=parsed.argument_categories,
        )
        declaration = replace(declaration, decl_id=_declaration_id(declaration))

    if held:
        # First hit decides. `held` is already in clause order because
        # `grounds_for` appends in clause order, but the lookup below is by
        # code rather than by position so the two orderings cannot drift.
        code = min(held, key=REFUSAL_CODES.index)
        clause = _CLAUSE_BY_CODE[code]
        outcome = VERDICT_REFUSED
    else:
        code = REFUSAL_NONE
        clause = CLAUSE_ADMIT
        outcome = VERDICT_ADMITTED

    verdict = AdmissibilityVerdict(
        schema=VERDICT_SCHEMA,
        verdict_id="",
        decl_id=declaration.decl_id if declaration is not None else "",
        verdict=outcome,
        refusal_code=code,
        deciding_clause=clause,
        schema_digest=inputs.schema_sha256_lf,
        census_ref=inputs.census_ref,
    )
    verdict = replace(verdict, verdict_id=_verdict_id(verdict))

    subcase = None
    if parsed is not None and session_names is not None:
        subcase = session_names.subcase(parsed.symbol_name)

    return Decision(
        declaration=declaration,
        verdict=verdict,
        parsed=parsed,
        grounds=held,
        session_name_subcase=subcase,
    )


# --------------------------------------------------------------------------
# the session-scoped ledger
# --------------------------------------------------------------------------


@dataclass
class SymbolLedger:
    """The admitted symbols of ONE session, and nothing that outlives it.

    Attached to a `CoreSession` the way an `AssumptionSet` is — by a recorder
    or a gate runner, never by `main()` and never by the chat skin, so
    ¶DEV-1's rule that requests replay into fresh sessions is untouched and
    declared vocabulary cannot cross an HTTP turn.
    """

    session_id: str
    inputs: CommittedInputs
    #: Deliberately duck-typed, exactly as `CoreSession.assumptions` is: the
    #: supposition ledger imports nothing from here and this imports nothing
    #: from it, so neither buys a cycle for a type annotation.
    assumptions: object | None = None
    _order: list[str] = field(default_factory=list)
    _by_name: dict[str, PersonSymbolDeclaration] = field(default_factory=dict)
    _verdicts: list[AdmissibilityVerdict] = field(default_factory=list)

    # -- state a caller may read ----------------------------------------

    @property
    def cap(self) -> int:
        return SYMBOL_CAP

    @property
    def pending_turn_index(self) -> int:
        """The turn a declaration made now would carry.

        Delegates to the supposition ledger when one is attached, so a
        session with both keeps ONE turn numbering rather than two that drift
        apart; falls back to counting its own verdicts when it stands alone.
        """

        live = self.assumptions
        if live is not None:
            return live.pending_turn_index
        return len(self._verdicts) + 1

    def admitted_names(self) -> tuple[str, ...]:
        return tuple(self._order)

    def declaration_for(self, name: str) -> PersonSymbolDeclaration | None:
        return self._by_name.get(name)

    def verdicts(self) -> tuple[AdmissibilityVerdict, ...]:
        return tuple(self._verdicts)

    def session_names(self) -> SessionNames:
        """§4's three-source union, assembled from the live session.

        Every source is read through a barrier-free accessor. `bound_names`
        and `applied_heads` both carry the same argument in
        `session_ledger`'s own words: knowing that somebody supposed
        something *about* `x`, or something *applying* `parent`, is not
        knowing what they supposed — so no citation follows and no declaring
        turn grows one.
        """

        binding: frozenset[str] = frozenset()
        heads: frozenset[str] = frozenset()
        live = self.assumptions
        if live is not None:
            binding = frozenset(
                normalize(name) for name in live.bound_names()
            )
            heads = supposition_applied_heads(live)
        return SessionNames(
            admitted_symbols=frozenset(self._order),
            binding_subjects=binding,
            applied_heads=heads,
        )

    # -- the door --------------------------------------------------------

    def declare(self, source_line: str, turn_index: int) -> Decision:
        """Decide a declaration line and, only on ADMITTED, record it.

        The decision is taken by the pure :func:`decide`; this method's only
        extra job is the mutation, which happens after a verdict exists and
        never before one.
        """

        decision = decide(
            source_line,
            self.inputs,
            session_id=self.session_id,
            turn_index=turn_index,
            admitted=tuple(self._order),
            session_names=self.session_names(),
        )
        self._verdicts.append(decision.verdict)
        if decision.admitted and decision.declaration is not None:
            self._order.append(decision.declaration.symbol_name)
            self._by_name[decision.declaration.symbol_name] = decision.declaration
        return decision

    # -- the use side ----------------------------------------------------

    def check_use(self, claim: str) -> UseCheck | None:
        """§3's use-side check, or None to leave today's path alone.

        Returns None whenever this slice has nothing to say — which is every
        line whose applied head is **not** a declared symbol, and every line
        that is not an applied atom at all. That None is the regression
        fence: B6 requires an undeclared applied atom to behave
        byte-identically to the same line on a tip without this slice, and
        the only way to guarantee that is for this method to hand the line
        back untouched rather than to re-render it identically.
        """

        head = applied_head(claim)
        if head is None:
            return None
        name, count = head
        declaration = self._by_name.get(name)
        if declaration is None:
            return None
        return UseCheck(
            head=name,
            argument_count=count,
            declaration=declaration,
            refused=count != declaration.arity,
        )


@dataclass(frozen=True)
class UseCheck:
    """What the supposition route needs to know about one applied atom.

    Carries `refused` and not a refusal NAME, and that is a B11 constraint
    rather than a style choice. §3 puts `USE_ARITY_MISMATCH` in the
    supposition ledger's refusal vocabulary, but importing `session_ledger`
    from here would pull `serve_chat` into this module's import closure
    (`session_ledger.line_grammar_digest` imports it), and `serve_chat` calls
    `importlib.import_module` — which `echo_population_audit.import_closure`
    REFUSES outright. So the name lives where §3 says it lives, the harness
    route reads it from there, and this module reports the arithmetic. That
    is the same division `harness.UNKNOWN_ASSUMPTION` already makes for
    exactly the same reason, and a test asserts the two spellings agree.
    """

    head: str
    argument_count: int
    declaration: PersonSymbolDeclaration
    refused: bool

    def detail(self) -> str:
        """The refusal, naming the declaration — §3 requires that it does."""

        return (
            f"{self.head!r} was declared with arity "
            f"{self.declaration.arity} "
            f"({', '.join(self.declaration.argument_categories)}) at turn "
            f"{self.declaration.turn_index} of this session, and this line "
            f"applies it to {self.argument_count}. Nothing was held and "
            "nothing is claimed"
        )


def supposition_applied_heads(assumptions) -> frozenset[str]:
    """§4's third source: the applied heads of live NON-BINDING suppositions.

    A free function taking the `AssumptionSet`, and not a method ON it, for
    the same pinned-recorder reason `REFUSAL_USE_ARITY_MISMATCH` lives here:
    `session_ledger.py` is byte-frozen by `recorder_code_digest` while the
    v0.21 corpus is sealed, so this slice reads that module rather than
    growing it.

    It touches **only** `live()` and `subject`, both public and both
    documented as barrier-free, and it never reads `_binding` or
    `normal_form` — so no read event fires and no citation can follow. That
    is not incidental: a declaring turn that grew a citation is what §3
    forbids by construction.

    `subject` does the binding/non-binding split for free and exactly:
    `session_ledger` derives it as the bound NAME for a binding claim and as
    the whole ATOM otherwise. A name has no parens, so `applied_head` returns
    None for it; an atom like `parent_link(alice, bob)` yields its head. No
    second rule is needed and none is written.
    """

    heads = set()
    for item in assumptions.live():
        found = applied_head(item.subject)
        if found is not None:
            heads.add(found[0])
    return frozenset(heads)


def applied_head(claim: str) -> tuple[str, int] | None:
    """`name(arg, ...)` → (normalized head, argument count), else None.

    §5 names the template parser's atom production as the reused trusted
    code for exactly this, and it is reused rather than re-implemented for a
    reason that is not tidiness: `parse_atom` is the code the reserved-prefix
    rewrite lives in, so detecting applied atoms with a second, private regex
    would mean the ledger and the parser could disagree about what a head is
    — which is the class of defect the whole `sum_total` lane is about.

    The claim is NORMALIZED before tokenizing. That is required, not
    cosmetic: `ﬁrst_of(page)` contains no character the template tokenizer
    accepts, so without NFC + casefold first it would raise rather than
    resolve to the ledger key `first_of`. Every exception is swallowed —
    this function is a detector, and a detector that throws on the person's
    typo would be a new refusal where §3 promised none.
    """

    from match_signatures import Parser, TemplateParseError, tokenize  # noqa: PLC0415

    try:
        tree = Parser(tokenize(normalize(claim).strip())).parse()
    except (TemplateParseError, RecursionError, ValueError, IndexError):
        return None
    if not isinstance(tree, tuple) or len(tree) != 3 or tree[0] != "call":
        return None
    head = tree[1]
    if not isinstance(head, str) or not is_name_shaped(head):
        return None
    return head, len(tree[2])
