#!/usr/bin/env python3
"""Build `experiments/symbol_census.json` — the namespace a declared name can hit.

`docs/DESIGN-house-rules.md` §4 is the contract. The first draft of that
design carried a four-name census and review falsified it: the namespace a
fresh `[a-z][a-z0-9_]*` head can collide with is not the relational operator
glyphs, it is the **call-head and lexicon vocabulary**. This builder writes
that vocabulary as data so the admissibility checker compares against a
committed artifact rather than against whatever the corpus happens to hold
the day it runs.

## What goes in, and why each bullet is separately necessary

1. **All five `symbol_lexicon` categories** — `symbols`, `operators`,
   `functionals`, `constants`, `index_sets` — across the merged graph, read
   with the repository's own loader convention (`sorted(glob("*/nodes.json"))`,
   `handles_census.py:112-116`). Every raw member is carried. Only the
   **name-shaped** subset can guard anything, and the artifact says which
   members those are rather than implying that `±` defends a namespace it
   cannot even be spelled into. That honesty is §4's own instruction: glyphs
   are "carried as members without pretending they guard anything".
2. **The leading identifier of every functional notation.** `RANK(.)`
   contributes `rank`. The notation string itself can never equal a declared
   name — it has parens in it — so without this bullet `rank` and `closure`
   are reachable through no other source at all, which review checked
   directly. That is this bullet's whole justification.
3. **Every call head of every committed `anonymized_template`**, taken from
   the shipped parser rather than a regex, because the head that ends up in
   a tree is the head the parser decided on and no second reading of the
   template is authoritative over it.
4. **`HEAD_ALIASES` keys and targets, and `COMMUTATIVE_CALL_HEADS`.** An
   alias target is a name the matcher will produce even where no corpus
   template spells it.
5. **`BIG_OP_PREFIXES` as a PREFIX GUARD, kept apart from the equality
   members.** This is the live hazard the v0.25 review found: the parser
   rewrites any identifier beginning `sum_ / prod_ / lim_ / max_ / min_`
   into a corpus aggregate head, so equality cannot see a rewrite that
   happens at tokenization. A declared name *starting with* a reserved
   prefix must refuse `RESERVED_PREFIX`. The prefixes are therefore stored
   under their own key with their own semantics; folding them into the
   member list would have silently converted a prefix test into an equality
   test and let `sum_total` through.

## The normalization rule, in one place

NFC, then casefold, then match `^[a-z][a-z0-9_]*$` against the RESULT. Both
sides of every comparison run it. Corpus heads are uppercase — `GCD` — and a
declared `gcd` colliding with one is the point of the census, not an accident
of it.

## The leading-identifier rule H-PRE said H-P0 still owed in writing

`house_rules_fixtures.json`'s fourth `census_source_findings` row records
that §4's prose under-specifies the extraction for `sum_i`. **The rule this
builder commits: normalize, then take the MAXIMAL match of
`^[a-z][a-z0-9_]*`.** The match is greedy, so it swallows the underscore and
`sum_i` yields `sum_i`, not `sum`. That is deliberate — a rule that stopped
at the first underscore would be a second, unstated tokenization living
beside the parser's own. `sum` is not lost by this choice: it enters
independently as a call head and as the one lowercase `HEAD_ALIASES` key,
which is exactly why H-PRE sealed both names with independent provenance and
said the fixture expectations hold under either reading.

## Determinism

No clock, no randomness, no environment reads. `DATE` is a committed
constant. Every set is sorted before it reaches the output, so the bytes do
not depend on `PYTHONHASHSEED` or on filesystem order.

Usage::

    python scripts/build_symbol_census.py --out experiments/symbol_census.json
    python scripts/check_symbol_census.py experiments/symbol_census.json
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

from match_signatures import (
    BIG_OP_PREFIXES,
    COMMUTATIVE_CALL_HEADS,
    HEAD_ALIASES,
    Parser,
    TemplateParseError,
    tokenize,
)
from report_provenance import provenance_block

REPO = Path(__file__).resolve().parents[1]

SCHEMA = "corollary.symbol-census/1"
STAGE = "H-P0"
DATE = "2026-09-01"
DESIGN = "docs/DESIGN-house-rules.md"
DESIGN_CLAUSE = "§4 — the collision census, the namespace that can actually collide"
ROADMAP = "docs/ROADMAP-v0.25.md#1"
GENERATOR = "scripts/build_symbol_census.py"
CHECKER = "scripts/check_symbol_census.py"

#: The declared alphabet, matched against the NORMALIZED surface.
NAME_PRODUCTION = r"^[a-z][a-z0-9_]*$"
_NAME_RE = re.compile(NAME_PRODUCTION)

#: The leading-identifier extraction, greedy — see the module docstring.
_LEADING_RE = re.compile(r"^[a-z][a-z0-9_]*")

#: The five `symbol_lexicon` categories and the field each spells a member in.
LEXICON_CATEGORIES = (
    ("symbols", "symbol"),
    ("operators", "symbol"),
    ("functionals", "notation"),
    ("constants", "symbol"),
    ("index_sets", "notation"),
)

GENERATED_NOTE = (
    "Generated artifact. Every member, count and provenance row below is "
    "derived by the generator from the committed corpus and the shipped "
    "parser's own constants; nothing is transcribed. A direct edit of this "
    "file is a DESIGN §9 stop condition, and scripts/check_symbol_census.py "
    "recomputes the whole census from source to say so."
)

SCOPE_NOTE = (
    "This census is the namespace a DECLARED name is compared against. It is "
    "not a global symbol table and this repository does not have one; it is "
    "the union DESIGN §4 names, and its authority stops exactly there. A name "
    "absent from this census is FRESH, which is a statement about this corpus "
    "and these parser constants on this commit, never a statement that the "
    "name means nothing."
)

HONESTY_NOTE = (
    "Carrying a member is not claiming it guards. Operator glyphs like `±` "
    "cannot be spelled by the declared alphabet [a-z][a-z0-9_]*, so they can "
    "never be hit by a declaration; they are carried as raw members with the "
    "name-shaped subset identified separately, because a census that quietly "
    "dropped them would be claiming a completeness it had not measured, and "
    "one that counted them as guards would be claiming a protection they "
    "cannot give."
)

NORMALIZATION_ORDER = (
    "NFC, then casefold, then match ^[a-z][a-z0-9_]*$ against the RESULT. "
    "Both sides of every comparison run it. The supposition path's existing "
    ".lower() is equivalent on the declared alphabet; the rule is stated once "
    "here rather than as two rules that happen to agree."
)

LEADING_IDENTIFIER_RULE = (
    "Normalize the notation, then take the MAXIMAL match of ^[a-z][a-z0-9_]* "
    "(greedy, so the underscore is swallowed: `sum_i` yields `sum_i`, not "
    "`sum`). This is the rule house_rules_fixtures.json's fourth "
    "census_source_findings row records as still owed at H-P0. A rule that "
    "stopped at the first underscore would be a second tokenization living "
    "beside the parser's own; `sum` is not lost by the greedy choice because "
    "it enters independently as a call head and as the one lowercase "
    "HEAD_ALIASES key."
)

PREFIX_GUARD_NOTE = (
    "Kept apart from the equality members ON PURPOSE. These are the "
    "`BIG_OP_PREFIXES` the shipped parser rewrites at tokenization "
    "(scripts/match_signatures.py, the big-op branch of Parser.parse_atom): "
    "an identifier whose casefold starts with one of these is turned into a "
    "corpus aggregate head and the rest of the name is discarded. Equality "
    "cannot see a rewrite that happens before equality runs, so a declared "
    "name STARTING WITH one of these refuses RESERVED_PREFIX. None of the "
    "five prefixes is itself an equality member — a checker that folded them "
    "into the member list would silently turn a prefix test into an equality "
    "test and admit `sum_total`."
)

#: H-PRE's `census_source_findings` are four things the design's PROSE does
#: not say, found while verifying the fixtures' collision targets against the
#: committed graph. This builder is their named consumer. The rule is: honor
#: the CODE over the prose, and record the deviation rather than quietly
#: following one of the two.
PROSE_DEVIATIONS = (
    {
        "finding": "the design's `parse_sum` citation names the wrong method",
        "design_says": (
            "DESIGN §4 places the big-op branch in `parse_sum` around "
            "match_signatures.py:541-563."
        ),
        "code_says": (
            "The line range is exact; the method is `Parser.parse_atom`. "
            "`parse_sum` is the additive-precedence production and contains "
            "no big-op branch."
        ),
        "this_builder_does": (
            "Reads the constants BIG_OP_PREFIXES / HEAD_ALIASES / "
            "COMMUTATIVE_CALL_HEADS by import and takes call heads from the "
            "parser's own output, so no line number and no method name is "
            "load-bearing here at all."
        ),
    },
    {
        "finding": (
            "the design's `rank(·)` / `closure(·)` spelling is not the "
            "committed spelling"
        ),
        "design_says": "§4 illustrates the functional bullet with `rank(·)` / `closure(·)`.",
        "code_says": (
            "The committed notations are `RANK(.)` and `CLOSURE(.)` — "
            "uppercase head, ASCII full stop. The illustration is off; the "
            "claim is not, because the casefolded leading identifiers are "
            "`rank` and `closure` either way."
        ),
        "this_builder_does": (
            "Extracts from the committed notation strings, so the "
            "illustration's spelling is never relied on."
        ),
    },
    {
        "finding": "the census contains a collision with itself",
        "design_says": "§4 does not mention that two sources can merge under normalization.",
        "code_says": (
            "The corpus carries uppercase call heads `SUM` and `LIM` as "
            "ordinary heads AND the synthetic lowercase heads the big-op "
            "branch produces. After NFC + casefold these are one member each."
        ),
        "this_builder_does": (
            "Unions into a set AFTER normalizing and never asserts "
            "distinctness before normalizing. The per-source counts below are "
            "therefore counts WITH overlap, and the union is smaller than "
            "their sum by construction — which the artifact states rather "
            "than leaving to arithmetic."
        ),
    },
    {
        "finding": "the functional leading-identifier rule is under-specified for `sum_i`",
        "design_says": "§4 gives `rank(·) → rank` and no rule for an underscore.",
        "code_says": (
            "Of 95 functional notations all 95 yield a name-shaped leading "
            "identifier. Under a greedy ^[a-z][a-z0-9_]* the extraction "
            "swallows the underscore and yields `sum_i`."
        ),
        "this_builder_does": (
            "Commits the greedy rule in writing (see `leading_identifier_rule`"
            "). H-PRE sealed both `sum_i` and `sum` with independent "
            "provenance so the fixture expectations hold under either "
            "reading; under THIS rule `sum_i` comes from the functional and "
            "`sum` from the call heads and HEAD_ALIASES."
        ),
    },
)


def normalize(raw: str) -> str:
    """§4's rule, run rather than described. NFC first, then casefold."""

    return unicodedata.normalize("NFC", raw).casefold()


def is_name_shaped(normalized: str) -> bool:
    """Whether a NORMALIZED surface can be spelled by the declared alphabet."""

    return bool(_NAME_RE.match(normalized))


def leading_identifier(raw: str) -> str | None:
    """The greedy leading identifier of a notation, or None if it has none."""

    match = _LEADING_RE.match(normalize(raw))
    return match.group(0) if match else None


def call_heads(tree: tuple) -> set[str]:
    """Every `call` head anywhere in a parsed template, the parser's own."""

    heads: set[str] = set()
    pending: list = [tree]
    while pending:
        node = pending.pop()
        if not isinstance(node, tuple):
            continue
        # A `call` node is ("call", head, (args...)). The argument tuple is
        # itself pushed and popped like any other node; it simply fails this
        # test, because its first element is a child rather than the string
        # "call". That is why the length check is here and not implied.
        if len(node) == 3 and node[0] == "call" and isinstance(node[1], str):
            heads.add(node[1])
        for item in node:
            if isinstance(item, tuple):
                pending.append(item)
            elif isinstance(item, list):
                pending.extend(item)
    return heads


def corpus_paths(repo: Path) -> list[Path]:
    """The loader convention every other reader in the tree uses."""

    return sorted((repo / "data").glob("*/nodes.json"))


def gather(repo: Path) -> dict[str, dict]:
    """Collect raw members per source, with the files each source came from."""

    raw: dict[str, set[str]] = {
        f"symbol_lexicon.{category}": set() for category, _ in LEXICON_CATEGORIES
    }
    raw["anonymized_template_call_heads"] = set()
    files: dict[str, set[str]] = {key: set() for key in raw}
    templates_parsed = 0

    for path in corpus_paths(repo):
        relative = path.relative_to(repo).as_posix()
        document = json.loads(path.read_text(encoding="utf-8"))
        for node in document.get("statement_nodes", []):
            lexicon = node.get("symbol_lexicon") or {}
            for category, field in LEXICON_CATEGORIES:
                key = f"symbol_lexicon.{category}"
                for entry in lexicon.get(category) or []:
                    member = entry.get(field)
                    if isinstance(member, str) and member:
                        raw[key].add(member)
                        files[key].add(relative)
            template = (node.get("structural_signature") or {}).get(
                "anonymized_template"
            )
            if not template:
                continue
            templates_parsed += 1
            try:
                tree = Parser(tokenize(template)).parse()
            except TemplateParseError as exc:  # pragma: no cover - corpus is clean
                raise SystemExit(
                    f"{relative}: committed template does not parse, so the "
                    f"census cannot claim to cover it: {template!r} ({exc})"
                ) from exc
            heads = call_heads(tree)
            if heads:
                raw["anonymized_template_call_heads"].update(heads)
                files["anonymized_template_call_heads"].add(relative)

    # The functional leading identifiers are DERIVED from a source above
    # rather than read from the corpus, so their provenance names the source
    # they were derived from instead of a file list.
    raw["functional_leading_identifiers"] = {
        identifier
        for member in raw["symbol_lexicon.functionals"]
        if (identifier := leading_identifier(member)) is not None
    }
    files["functional_leading_identifiers"] = set()

    raw["head_aliases_keys"] = set(HEAD_ALIASES)
    raw["head_aliases_targets"] = set(HEAD_ALIASES.values())
    raw["commutative_call_heads"] = set(COMMUTATIVE_CALL_HEADS)
    for key in ("head_aliases_keys", "head_aliases_targets", "commutative_call_heads"):
        files[key] = set()

    return {
        "raw": raw,
        "files": files,
        "templates_parsed": templates_parsed,
    }


SOURCE_ORDER = (
    "symbol_lexicon.symbols",
    "symbol_lexicon.operators",
    "symbol_lexicon.functionals",
    "symbol_lexicon.constants",
    "symbol_lexicon.index_sets",
    "functional_leading_identifiers",
    "anonymized_template_call_heads",
    "head_aliases_keys",
    "head_aliases_targets",
    "commutative_call_heads",
)

SOURCE_NOTES = {
    "symbol_lexicon.symbols": (
        "DESIGN §4 bullet 1. Slot symbols; mostly name-shaped single letters "
        "and words."
    ),
    "symbol_lexicon.operators": (
        "DESIGN §4 bullet 1. Mostly glyphs, which cannot be spelled by the "
        "declared alphabet and are carried without guarding; the name-shaped "
        "minority (`implies` among them) is what makes this category live."
    ),
    "symbol_lexicon.functionals": (
        "DESIGN §4 bullet 1. Almost every member carries parens or dots and "
        "so can never equal a declared name — which is exactly why bullet 2 "
        "exists."
    ),
    "symbol_lexicon.constants": "DESIGN §4 bullet 1.",
    "symbol_lexicon.index_sets": "DESIGN §4 bullet 1.",
    "functional_leading_identifiers": (
        "DESIGN §4 bullet 2, derived from symbol_lexicon.functionals by the "
        "committed leading_identifier_rule. Review found `rank` and `closure` "
        "reachable through no other bullet."
    ),
    "anonymized_template_call_heads": (
        "DESIGN §4 bullet 3, taken from the shipped parser's own output over "
        "every committed anonymized_template."
    ),
    "head_aliases_keys": "DESIGN §4 bullet 4 (scripts/match_signatures.py HEAD_ALIASES).",
    "head_aliases_targets": (
        "DESIGN §4 bullet 4. An alias TARGET is a head the matcher produces "
        "even where no committed template spells it."
    ),
    "commutative_call_heads": (
        "DESIGN §4 bullet 4 (scripts/match_signatures.py "
        "COMMUTATIVE_CALL_HEADS)."
    ),
}


def build_census(repo: Path) -> dict:
    """The whole artifact, as data."""

    collected = gather(repo)
    raw = collected["raw"]
    files = collected["files"]

    sources = []
    members_by_source: dict[str, list[str]] = {}
    raw_members_by_source: dict[str, list[str]] = {}
    equality: set[str] = set()

    for key in SOURCE_ORDER:
        members = raw[key]
        shaped = sorted({n for member in members if is_name_shaped(n := normalize(member))})
        equality.update(shaped)
        members_by_source[key] = shaped
        raw_members_by_source[key] = sorted(members)
        sources.append(
            {
                "source": key,
                "note": SOURCE_NOTES[key],
                "raw_member_count": len(members),
                "name_shaped_member_count": len(shaped),
                "carried_not_guarding_count": len(members) - len(shaped),
                "source_files": sorted(files[key]),
                "source_file_count": len(files[key]),
                "derived_from": (
                    "symbol_lexicon.functionals"
                    if key == "functional_leading_identifiers"
                    else None
                ),
                "constant": (
                    "scripts/match_signatures.py"
                    if key
                    in {
                        "head_aliases_keys",
                        "head_aliases_targets",
                        "commutative_call_heads",
                    }
                    else None
                ),
            }
        )

    equality_members = sorted(equality)
    prefixes = sorted(BIG_OP_PREFIXES)

    inputs = [*corpus_paths(repo), repo / "scripts" / "match_signatures.py"]

    return {
        "schema": SCHEMA,
        "stage": STAGE,
        "date": DATE,
        "design": DESIGN,
        "design_clause": DESIGN_CLAUSE,
        "roadmap": ROADMAP,
        "generator": GENERATOR,
        "checker": CHECKER,
        "generated_note": GENERATED_NOTE,
        "scope_note": SCOPE_NOTE,
        "honesty_note": HONESTY_NOTE,
        "normalization": {
            "rule": "NFC + casefold",
            "order": NORMALIZATION_ORDER,
            "name_production": NAME_PRODUCTION,
            "applied_by_generator": (
                "unicodedata.normalize('NFC', raw).casefold() — this "
                "generator runs the rule rather than describing it."
            ),
        },
        "leading_identifier_rule": LEADING_IDENTIFIER_RULE,
        "counts": {
            "corpus_files": len(corpus_paths(repo)),
            "templates_parsed": collected["templates_parsed"],
            "sources": len(SOURCE_ORDER),
            "equality_members": len(equality_members),
            "prefix_guard_entries": len(prefixes),
            "raw_members_summed_with_overlap": sum(
                len(raw[key]) for key in SOURCE_ORDER
            ),
            "name_shaped_summed_with_overlap": sum(
                len(members_by_source[key]) for key in SOURCE_ORDER
            ),
        },
        "overlap_note": (
            "`equality_members` is the UNION and is smaller than "
            "`name_shaped_summed_with_overlap` because sources genuinely "
            "overlap — `gcd` alone is reached by three of them, and after "
            "normalization the uppercase and synthetic-lowercase spellings of "
            "`sum` and `lim` merge. The overlap is the census working, not a "
            "defect: a target reached by several bullets survives a change to "
            "any one of them."
        ),
        "sources": sources,
        "equality_members": equality_members,
        "members_by_source": members_by_source,
        "raw_members_by_source": raw_members_by_source,
        "prefix_guard": {
            "prefixes": prefixes,
            "constant": "scripts/match_signatures.py BIG_OP_PREFIXES",
            "semantics": "startswith, against the NORMALIZED declared name",
            "distinct_from_equality_members": True,
            "prefixes_that_are_also_equality_members": [
                prefix for prefix in prefixes if prefix in equality
            ],
            "note": PREFIX_GUARD_NOTE,
        },
        "design_prose_deviations": list(PROSE_DEVIATIONS),
        "provenance": provenance_block(Path(__file__), inputs, repo),
    }


def render(census: dict) -> str:
    """Pure LF, trailing newline, stable key order (insertion order above)."""

    return json.dumps(census, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default="experiments/symbol_census.json",
        help="where to write the census (default: experiments/symbol_census.json)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="print the census instead of writing it",
    )
    args = parser.parse_args()

    census = build_census(REPO)
    text = render(census)
    if args.stdout:
        print(text, end="")
        return 0
    out = REPO / args.out
    out.write_text(text, encoding="utf-8", newline="\n")
    print(
        f"wrote {args.out}: {census['counts']['equality_members']} equality "
        f"members, {census['counts']['prefix_guard_entries']} prefix-guard "
        f"entries, over {census['counts']['templates_parsed']} templates"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
