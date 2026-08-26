#!/usr/bin/env python3
"""P1 — how many commands does the registered line grammar admit?

DESIGN-session-ledger §6 P1: *"Compute and commit the bound on admitted
commands per template class of the registered grammar (series 1's fold: the
grammar is finite; enumeration cost becomes a number)."*

This script is the computation. It writes
``experiments/session_p1_command_bound.json`` and asserts nothing that the
artifact does not carry.

## The counting rule, stated before any number

The template classes are the rows of ``serve_chat.LINE_GRAMMAR``, in their
committed order — that tuple *is* the registered grammar, and the capability
sheet publishes it row by row. Classes are filled by ROUTE NAME, never by
row index: v0.21's own session ledger inserted a row and shifted everything
after it, and a builder that quietly attached one class's analysis to
another's row would produce a plausible wrong artifact rather than an error.

A line is **admitted by a class** when two things hold:

1. ``harness.route_line``'s first-match-wins chain (`harness.py:2062-2115`)
   dispatches it to that class's route; and
2. every slot in the class's form carries a value drawn from that class's
   **registered vocabulary** — the finite set the route can act on, rather
   than a value it will refuse by name.

Clause 2 is what makes the count worth having. `twin zzzz` reaches the twin
route and is refused for an id the ledger does not hold; counting it would
be counting the refusals, and the refusals are unbounded in every class at
once. So the count is over lines the class can *act on*.

Every class carries a declared ``bound_kind``, and the kind — never a null
count — is what sorts it:

* **closed** — every slot's values are a finite set fixed by a committed
  producer (a corpus file, a manifest, a module constant). The script
  enumerates the producer and reports ``size`` with the producer named. No
  size in this artifact is estimated, sampled, or asserted from a docstring.
* **open** — at least one slot ranges over a recursively generated or
  free-text language (an arithmetic expression, a claim a person types, a
  path that need not exist). Its cardinality is countably infinite. The
  class's admitted count is then ``null`` and ``unbounded_reason`` names the
  slot and what actually bounds it at runtime, which is never a vocabulary.
* **gated** — the slot is closed in principle and its producer is not
  readable on this boot. Exactly one class is gated: `what is X` over the
  WordNet lemma set, whose archive is not a committed artifact.

**Open classes are never folded into the total.** A total that silently
absorbed an infinite class would be a number pretending to be a bound, which
is the failure mode this whole artifact exists to avoid. The artifact
publishes ``closed_total`` (the sum over closed classes) and lists the open
and gated classes by index; ``open_total`` is explicitly ``null`` with its
reason. A class whose declared kind disagrees with what its producer
returned raises rather than publishing.

## The second column, and why it is here

For several open classes the *input* language is infinite while the
committed material the class can answer **from** is finite and countable:
`owns` accepts any template expression but can only ever host a subterm
skeleton some committed statement carries; the resolver accepts any prose
but can only bind one of 14,830 statements. That number is reported as
``answering_vocabulary`` beside the admitted count, with its own producer.
It is not a bound on the grammar and the artifact says so — it is the bound
on what an enumerating proposer could usefully aim at, which is the question
P1 was folded out of FORK to answer.

## Determinism

Every number is read from committed bytes under the repository root. The
one environment-gated number is the gloss class's WordNet lemma count: the
archive is not a committed artifact, so when its probe does not register the
class reports ``size: null`` with ``gated_on`` naming the subsystem, exactly
as the capability sheet publishes that row off rather than hiding it
(`serve_chat.py:339-342`). Per ROADMAP-v0.21 §4.0(2) the artifact is
committed from a deterministic runner; reproductions are welcome and
recorded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

ARTIFACT = "experiments/session_p1_command_bound.json"
SCHEMA = "corollary.session-p1-command-bound/1"

#: A rendered slot placeholder, `?N:CLASS` (`match_signatures.py:755-759`).
_SLOT_CLASS = re.compile(r"\?\d+:([A-Za-z_]+)")


# --------------------------------------------------------------------------
# closed vocabularies, each read from its named producer
# --------------------------------------------------------------------------


def _statement_vocabulary(repo_root: Path) -> dict:
    """Statement ids, corpus names, disciplines and resolver word keys."""

    from answer import compose  # noqa: PLC0415
    from resolver import default_index  # noqa: PLC0415

    index = default_index()
    statement_ids = sorted(index.corpus_of)
    corpora = sorted({name for name in index.corpus_of.values() if name})
    words = sorted(
        set(index.by_keyword) | set(index.by_lexicon) | set(index.by_prose)
    )
    disciplines: set[str] = set()
    for sid in statement_ids:
        composed = compose(sid)
        if composed is None:
            continue
        for discipline in composed.disciplines:
            disciplines.add(discipline.casefold())
    return {
        "statement_ids": len(statement_ids),
        "corpora": len(corpora),
        "corpus_names": corpora,
        "words": len(words),
        "disciplines": len(disciplines),
        "discipline_names": sorted(disciplines),
    }


def _owns_vocabulary(repo_root: Path) -> dict:
    """Distinct compound subterm skeletons a query can name.

    `ownership.lookup` compares ``skeleton(sub, node_classes)`` against a
    query skeleton built with every slot in class ``V``
    (`ownership.py:88-110`). So the answerable set is exactly the distinct
    skeletons of compound (`op`/`call`) subterms whose slots all print as
    ``V`` — a skeleton carrying a parameter-class slot is unreachable from
    any typed query, and the count says so separately rather than rolling
    the two together.
    """

    from decompose import load_trees, subterms  # noqa: PLC0415
    from match_signatures import skeleton  # noqa: PLC0415

    _nodes, trees, classes, _corpus_of, _disc = load_trees(repo_root / "data")
    reachable: set[str] = set()
    unreachable: set[str] = set()
    for statement_id, tree in trees.items():
        node_classes = classes.get(statement_id, {})
        for _path, sub in subterms(tree):
            if sub[0] not in {"op", "call"}:
                continue
            printed = skeleton(sub, node_classes)
            # A slot prints as `?N:CLASS` (`match_signatures.py:755-759`). Any
            # class other than V is unreachable from a typed query, because
            # `parse_query` types every query slot V (`ownership.py:104-108`).
            slots_ok = all(
                found == "V" for found in _SLOT_CLASS.findall(printed)
            )
            (reachable if slots_ok else unreachable).add(printed)
    return {
        "query_reachable_skeletons": len(reachable),
        "query_unreachable_skeletons": len(unreachable - reachable),
        "statements_searched": len(trees),
    }


#: The twin ledger's group-bearing fields, NAMED. `_route_twin` answers
#: `found` for a statement listed in one of these and `exhausted` otherwise
#: (`retrieval.py:583` builds its material from them), so these five lists
#: are the admission set and nothing else in the file is.
TWIN_GROUP_FIELDS = (
    "typed_twin_groups",
    "family_twin_groups_beyond_typed",
    "aliased_twin_groups_beyond_typed",
    "mirror_twin_groups",
    "shape_twin_groups",
)


def _twin_vocabulary(repo_root: Path) -> dict:
    """Statement ids the committed twin ledger actually lists.

    **Corrected 2026-08-26, after independent review.** The first version
    walked the whole document for any dict carrying a `members` list of
    STRINGS. Real twin groups carry members as lists of DICTS
    (`{"statement_id", "discipline", "template"}`), so that walk matched
    neither of them — it matched the two DIAGNOSTIC lists that happen to
    hold bare id strings, `archetype_label_drift` and
    `skeletons_with_split_archetypes`, and reported 12,589 ids of which
    10,111 route to `exhausted`. It also missed 59 ids that are real
    members. Two wrongs in one number, and it inflated the closed total by
    10,052.

    The fix is to stop pattern-matching the document's shape and name the
    five fields that hold groups. Members are read by their `statement_id`
    key and a member that is not a dict with one RAISES: the whole defect
    was a walker that quietly accepted a shape it did not understand, and
    the repair has to be loud where the original was accommodating.
    """

    from harness import TWIN_LEDGER_PATH, TWIN_LEVEL_ORDER  # noqa: PLC0415

    path = repo_root / TWIN_LEDGER_PATH
    try:
        ledger = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"members": None, "reason": f"{type(exc).__name__}: {exc}"}
    members: set[str] = set()
    groups = 0
    per_field: dict[str, int] = {}
    for field in TWIN_GROUP_FIELDS:
        listed = ledger.get(field)
        if listed is None:
            raise RuntimeError(
                f"{TWIN_LEDGER_PATH} carries no {field!r}; the twin ledger's "
                "shape moved and this count would be about something else"
            )
        per_field[field] = len(listed)
        for group in listed:
            groups += 1
            for member in group["members"]:
                if not isinstance(member, dict) or "statement_id" not in member:
                    raise RuntimeError(
                        f"{field} holds a member this reader does not "
                        f"understand: {member!r}. The v0.21 review found this "
                        "count wrong precisely because an earlier version "
                        "accepted a shape it had not checked."
                    )
                members.add(member["statement_id"])
    return {
        "members": len(members),
        "groups": groups,
        "groups_by_field": per_field,
        "levels": list(TWIN_LEVEL_ORDER),
        "producer": TWIN_LEDGER_PATH,
        "producer_fields": list(TWIN_GROUP_FIELDS),
        "corrected": (
            "2026-08-26. The first reading walked for members-as-strings and "
            "found the two diagnostic lists instead of the five group lists: "
            "12,589 ids reported, 10,111 of them routing to `exhausted`, and "
            "59 real members missed."
        ),
    }


def _reachable_vocabulary(repo_root: Path) -> dict:
    """`reachable <world-id> <target-path>` pairs listed in the manifest."""

    from harness import CLOSURE_TARGET_MANIFEST  # noqa: PLC0415

    path = repo_root / CLOSURE_TARGET_MANIFEST
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"pairs": None, "reason": f"{type(exc).__name__}: {exc}"}
    files = manifest.get("files", [])
    pairs = {
        (entry.get("world_id", ""), entry.get("path", ""))
        for entry in files
        if isinstance(entry, dict)
    }
    worlds = {world for world, _path in pairs}
    return {
        "pairs": len(pairs),
        "worlds": len(worlds),
        "producer": CLOSURE_TARGET_MANIFEST,
    }


def _conform_vocabulary(repo_root: Path) -> dict:
    """Statement ids the frozen conformance register admits."""

    path = repo_root / "experiments/conformance_register.json"
    try:
        register = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"entries": None, "reason": f"{type(exc).__name__}: {exc}"}
    entries = register.get("entries", {})
    if isinstance(entries, dict):
        total = len(entries)
    else:
        total = len(list(entries))
    return {
        "entries": total,
        "producer": "experiments/conformance_register.json",
    }


def _write_gate_vocabulary() -> dict:
    """Row 10's closed half exists and is deliberately NOT given a number.

    `_existing_file` (`harness.py:961-968`) admits every regular file under
    the root, so the closed half of this row is the working tree itself. That
    set changes with **every commit, including the commit that would carry
    this artifact** — counting it would make the number stale the moment it
    was written and would make a reproduction check go red for reasons that
    have nothing to do with the grammar. A self-referential count is not a
    bound, so this vocabulary reports `null` with the reason instead.

    The open half is `_looks_like_path`, which admits any whitespace-free
    string ending `.json` or carrying a separator whether or not it exists —
    deliberately, so the gate's own named refusal is what the person sees
    (`harness.py:947-958`).
    """

    return {
        "existing_files": None,
        "producer": "harness._existing_file over the working tree",
        "reason": (
            "the vocabulary is the working tree, which changes with every "
            "commit including the one carrying this artifact; a count that "
            "cannot be frozen is not a bound, and a self-referential count "
            "would make the reproduction check red for reasons unrelated to "
            "the grammar"
        ),
    }


def _gloss_vocabulary() -> dict:
    """WordNet lemmas — closed when the probe registers, gated when not."""

    try:
        from gloss import REQUIRES_SUBSYSTEM  # noqa: PLC0415
        from harness import probe_wordnet  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - import shape is stable
        return {"lemmas": None, "gated_on": "retrieve.wordnet", "reason": str(exc)}
    record = probe_wordnet(offline=False, env=None)
    if getattr(record.liveness, "value", "") != "OK":
        return {
            "lemmas": None,
            "gated_on": REQUIRES_SUBSYSTEM,
            "reason": (
                "the WordNet archive is not a committed artifact and did not "
                f"register on this boot: {record.detail}"
            ),
        }
    try:
        from gloss import lemma_count  # noqa: PLC0415

        return {"lemmas": int(lemma_count()), "gated_on": REQUIRES_SUBSYSTEM}
    except (ImportError, AttributeError, TypeError, ValueError) as exc:
        return {
            "lemmas": None,
            "gated_on": REQUIRES_SUBSYSTEM,
            "reason": (
                "the probe registered but the module exposes no committed "
                f"lemma count to read: {type(exc).__name__}: {exc}"
            ),
        }


# --------------------------------------------------------------------------
# the classes
# --------------------------------------------------------------------------


def _classes(repo_root: Path) -> tuple[list[dict], dict]:
    from serve_chat import LINE_GRAMMAR  # noqa: PLC0415
    from harness import CONTEXT_KINDS  # noqa: PLC0415
    from session_ledger import LIVE_ASSUMPTION_CAP, TURN_CAP  # noqa: PLC0415

    words = _statement_vocabulary(repo_root)
    owns = _owns_vocabulary(repo_root)
    twin = _twin_vocabulary(repo_root)
    reach = _reachable_vocabulary(repo_root)
    conform = _conform_vocabulary(repo_root)
    gate = _write_gate_vocabulary()
    gloss = _gloss_vocabulary()

    vocabularies = {
        "statement_ids": {
            "size": words["statement_ids"],
            "producer": "resolver.default_index().corpus_of",
        },
        "corpus_names": {
            "size": words["corpora"],
            "producer": "resolver.default_index().corpus_of values",
            "values": words["corpus_names"],
        },
        "disciplines": {
            "size": words["disciplines"],
            "producer": "answer.compose(statement_id).disciplines, casefolded",
            "values": words["discipline_names"],
        },
        "resolver_words": {
            "size": words["words"],
            "producer": (
                "resolver.default_index() by_keyword | by_lexicon | by_prose "
                "posting keys"
            ),
        },
        "owns_query_skeletons": owns,
        "twin_ledger": twin,
        "closure_targets": reach,
        "conformance_register": conform,
        "write_gate_existing_files": gate,
        "denominators_that_differ_and_why": {
            "statement_ids": words["statement_ids"],
            "statements_with_a_template_tree": owns["statements_searched"],
            "difference": (
                words["statement_ids"] - owns["statements_searched"]
            ),
            "why": (
                "the resolver index covers every committed statement node; "
                "`decompose.load_trees` covers only the nodes carrying a "
                "template tree. The gap is the goedelpset skeleton corpus, "
                "which the resolver can name and the ownership matcher has no "
                "tree to search. Two classes therefore report two different "
                "corpus sizes on purpose, and neither is wrong for its own "
                "route."
            ),
        },
        "wordnet_lemmas": gloss,
        "context_kinds": {
            "size": len(CONTEXT_KINDS),
            "producer": "harness.CONTEXT_KINDS",
            "values": sorted(CONTEXT_KINDS),
        },
    }

    narrow_admitted = (
        words["corpora"] + words["disciplines"] + words["words"]
        + words["statement_ids"] + 1
    )

    rows: list[dict] = []
    for position, row in enumerate(LINE_GRAMMAR):
        entry = {
            "class_index": position,
            "form": row["form"],
            "route": row["route"],
            "example": row["example"],
        }
        rows.append(entry)

    by_route = {row["route"]: row for row in rows}

    def _fill(route: str, **fields) -> None:
        """Fill a class by ROUTE NAME, never by row index.

        The first version of this script filled by index, and v0.21's own
        session ledger then inserted a row into `LINE_GRAMMAR` and shifted
        every class after it. Route names are stable where positions are
        not, and a builder that silently attaches the `owns` analysis to the
        `twin` row is a builder that produces a plausible wrong artifact.
        The KeyError below is the loud version of the same event.
        """

        by_route[route].update(fields)

    _fill(
        "none",
        bound_kind="closed",
        slots=[],
        admitted_commands=1,
        counting="the empty line, and nothing else (harness.py:2065-2076)",
        answering_vocabulary=None,
    )
    _fill(
        "resolver_context",
        bound_kind="closed",
        slots=[
            {
                "name": "kind",
                "kind": "closed",
                "size": len(CONTEXT_KINDS),
                "vocabulary": "context_kinds",
            },
            {
                "name": "value",
                "kind": "closed",
                "size": None,
                "vocabulary": "per-kind: corpus_names | disciplines | "
                "resolver_words | statement_ids",
                "note": (
                    "`narrow id V` narrows to V only when V is already in the "
                    "pending candidate set, so the id arm's live vocabulary is "
                    "a subset of statement_ids bounded by the pending set; the "
                    "count below uses the full id vocabulary, which is the "
                    "ceiling"
                ),
            },
        ],
        admitted_commands=narrow_admitted,
        counting=(
            f"corpus {words['corpora']} + discipline {words['disciplines']} + "
            f"word {words['words']} + id {words['statement_ids']} + "
            "cancel 1 = " + str(narrow_admitted)
        ),
        precondition=(
            "reachable only while a resolver candidate set is pending "
            "(harness.py:2078-2079); the precondition gates *when* the class "
            "is reachable, not *how many* lines it admits"
        ),
        answering_vocabulary=words["statement_ids"],
    )
    _fill(
        "ownership",
        bound_kind="open",
        slots=[
            {
                "name": "template-expr",
                "kind": "open",
                "size": None,
                "why": (
                    "the matcher's expression grammar is recursive: `x ^ 2`, "
                    "`x ^ 2 + 1`, `f(x ^ 2 + 1)` … are all parses, so the "
                    "admitted input language is countably infinite"
                ),
            }
        ],
        admitted_commands=None,
        unbounded_reason=(
            "template-expr is a recursively generated expression language; "
            "nothing bounds its size but the line the person can type"
        ),
        answering_vocabulary=owns["query_reachable_skeletons"],
        answering_note=(
            "the distinct compound subterm skeletons committed statements "
            "host with every slot in class V — the exact set of queries this "
            "route can answer `solved` for; "
            f"{owns['query_unreachable_skeletons']} further compound "
            "skeletons carry a parameter-class slot and are unreachable from "
            "any typed query (ownership.py:104-108)"
        ),
    )
    _fill(
        "supposition",
        bound_kind="open",
        slots=[
            {
                "name": "claim",
                "kind": "open",
                "size": None,
                "why": (
                    "`_route_suppose` holds whatever text follows the command "
                    "word; `_atom` lowercases, collapses whitespace and strips "
                    "one of three leading negation markers, and admits "
                    "everything else (supposition.py:77-86)"
                ),
            }
        ],
        admitted_commands=None,
        unbounded_reason=(
            "claim is free text; the supposition route refuses no claim for "
            "being outside a vocabulary, because holding a claim is not "
            "checking it"
        ),
        answering_vocabulary=None,
        answering_note=(
            "a suppose line that binds a variable and computes is routed to "
            "evaluate first (harness.py:2083-2091), so this class's *answering* "
            "half is evaluate's and is counted there"
        ),
    )
    _fill(
        "retraction",
        bound_kind="closed",
        slots=[
            {
                "name": "assumption-id",
                "kind": "closed",
                "size": TURN_CAP,
                "vocabulary": "session_assumption_ids",
                "note": (
                    "ids are minted `aNNN` in declaration order within one "
                    "session, and a session is capped at "
                    f"{TURN_CAP} turns, so at most {TURN_CAP} assumptions "
                    "can ever be declared in one — the ceiling is the turn "
                    "cap, not the live-assumption cap of "
                    f"{LIVE_ASSUMPTION_CAP}, because a retracted or "
                    "superseded id stays a real id"
                ),
            }
        ],
        admitted_commands=TURN_CAP,
        counting=(
            "one line per assumption id a session can hold. This is the only "
            "class in the grammar whose vocabulary is SESSION-scoped rather "
            "than corpus-scoped: `a001` names different claims in different "
            "sessions, so the number is a per-session ceiling and the "
            "artifact says so rather than multiplying it by anything"
        ),
        answering_vocabulary=LIVE_ASSUMPTION_CAP,
        answering_note=(
            "only a LIVE assumption can be retracted, and §3 caps live "
            "assumptions at "
            f"{LIVE_ASSUMPTION_CAP}; the rest refuse with "
            "`unknown_assumption`"
        ),
    )
    _fill(
        "twin",
        bound_kind="closed",
        slots=[
            {
                "name": "statement-id",
                "kind": "closed",
                "size": twin.get("members"),
                "vocabulary": "twin_ledger",
            }
        ],
        admitted_commands=twin.get("members"),
        counting=(
            "one line per statement id the committed twin ledger lists; an id "
            "outside the ledger reaches the route and is answered `exhausted`, "
            "which is a refusal to name a group and is not counted"
        ),
        answering_vocabulary=twin.get("members"),
    )
    _fill(
        "closure",
        bound_kind="closed",
        slots=[
            {
                "name": "world-id",
                "kind": "closed",
                "size": reach.get("worlds"),
                "vocabulary": "closure_targets",
            },
            {
                "name": "target-path",
                "kind": "closed",
                "size": reach.get("pairs"),
                "vocabulary": "closure_targets",
                "note": "targets must be listed in the committed manifest",
            },
        ],
        admitted_commands=reach.get("pairs"),
        counting=(
            "the manifest's (world_id, path) pairs, counted as pairs rather "
            "than as a product: an unlisted path is refused by name"
        ),
        answering_vocabulary=reach.get("pairs"),
    )
    _fill(
        "conform",
        bound_kind="open",
        slots=[
            {
                "name": "statement-id",
                "kind": "closed",
                "size": conform.get("entries"),
                "vocabulary": "conformance_register",
            },
            {
                "name": "bindings",
                "kind": "open",
                "size": None,
                "why": (
                    "a binding is `name=value` over exact numerals; the value "
                    "alphabet is the integers and rationals the evaluator "
                    "parses, which is countably infinite"
                ),
            },
        ],
        admitted_commands=None,
        unbounded_reason=(
            "the statement-id factor is closed at "
            f"{conform.get('entries')} register entries, but the bindings "
            "factor is an open numeral language, so the product is unbounded"
        ),
        answering_vocabulary=conform.get("entries"),
    )
    _fill(
        "story",
        bound_kind="open",
        slots=[
            {
                "name": "story request",
                "kind": "open",
                "size": None,
                "why": (
                    "`story.STORY_REQUEST` is a `search`, not a `fullmatch`: "
                    "any line containing one of five trigger phrases is "
                    "admitted, so the admitted language is infinite while the "
                    "material behind it is one story"
                ),
            }
        ],
        admitted_commands=None,
        unbounded_reason=(
            "the trigger is a substring search over free text "
            "(story.py:65-73)"
        ),
        answering_vocabulary=1,
        answering_note="one committed story, verified rather than invented",
    )
    _fill(
        "belief",
        bound_kind="open",
        slots=[
            {
                "name": "agent",
                "kind": "open",
                "size": None,
                "why": "`belief.QUERY`'s WORD group matches any word",
            },
            {
                "name": "subject",
                "kind": "open",
                "size": None,
                "why": "same group; the narration that binds them is the line",
            },
        ],
        admitted_commands=None,
        unbounded_reason=(
            "the belief route reads its world out of the narration in the "
            "same line (belief.py:175-201), so it has no external vocabulary "
            "to be closed over"
        ),
        answering_vocabulary=None,
    )
    _fill(
        "evaluate",
        bound_kind="open",
        slots=[
            {
                "name": "expression",
                "kind": "open",
                "size": None,
                "why": "arbitrary numerals and a recursive operator grammar",
            }
        ],
        admitted_commands=None,
        unbounded_reason=(
            "exact arithmetic over unbounded numerals; the one registered "
            "bound is on the RESULT (`evaluate.MAX_RESULT_DIGITS`, E0e), not "
            "on the input vocabulary — a bound on what may be rendered is not "
            "a bound on what may be typed"
        ),
        answering_vocabulary=None,
    )
    _fill(
        "write_gate",
        bound_kind="open",
        slots=[
            {
                "name": "repo-relative path",
                "kind": "open",
                "size": gate["existing_files"],
                "why": (
                    "`_existing_file` admits every regular file under the "
                    "root — a closed set — but `_looks_like_path` also admits "
                    "any whitespace-free string ending `.json` or carrying a "
                    "separator, existing or not, so the class as a whole is "
                    "open"
                ),
            }
        ],
        admitted_commands=None,
        unbounded_reason=(
            "`_looks_like_path` is a syntactic test over free strings "
            "(harness.py:947-958); a path that does not exist routes here on "
            "purpose so the gate's own refusal is what the person reads"
        ),
        answering_vocabulary=None,
        answering_note=gate["reason"],
    )
    _fill(
        "resolver",
        bound_kind="open",
        slots=[
            {
                "name": "free text",
                "kind": "open",
                "size": None,
                "why": "the resolver takes any line the earlier rows declined",
            }
        ],
        admitted_commands=None,
        unbounded_reason="free text",
        answering_vocabulary=words["statement_ids"],
        answering_note=(
            "the resolver can BIND or ASK about committed statements and "
            "nothing else, so its answering vocabulary is the statement set "
            "even though its input language is not"
        ),
    )
    _fill(
        "gloss",
        bound_kind="gated",
        slots=[
            {
                "name": "X",
                "kind": "closed",
                "size": gloss.get("lemmas"),
                "vocabulary": "wordnet_lemmas",
                "note": (
                    "`definitional_target` additionally requires the question "
                    "to END at X in the forward form (gloss.py:95-120), so the "
                    "carrier phrase is fixed and X is the only free slot"
                ),
            }
        ],
        admitted_commands=gloss.get("lemmas"),
        counting=(
            "two carrier forms (`what is X`, `define X` and the inverted "
            "form) over the WordNet lemma set; the count above is the lemma "
            "set itself, and it is null when the archive did not register"
        ),
        gated_on=gloss.get("gated_on"),
        gate_reason=gloss.get("reason"),
        answering_vocabulary=gloss.get("lemmas"),
    )
    _fill(
        "dispatcher",
        bound_kind="open",
        slots=[
            {
                "name": "everything else",
                "kind": "open",
                "size": None,
                "why": "the complement of the thirteen rows above",
            }
        ],
        admitted_commands=None,
        unbounded_reason=(
            "row 13 is defined as a complement; a complement of finite and "
            "infinite languages inside an infinite alphabet is infinite"
        ),
        answering_vocabulary=0,
        answering_note=(
            "the dispatcher abstains by construction — it materializes "
            "nothing and can reach no verdict (P-LS2), so its answering "
            "vocabulary is empty, not merely small"
        ),
    )

    # `bound_kind` is declared per class above and is the ONLY thing that
    # sorts a class here. Inferring the kind from a null count would silently
    # relabel the gated gloss row as open the day WordNet stops registering —
    # a classification that changes with the environment is not a
    # classification. A class whose declared kind disagrees with its count is
    # a builder defect and raises rather than publishing.
    closed = [row for row in rows if row["bound_kind"] == "closed"]
    open_rows = [row for row in rows if row["bound_kind"] == "open"]
    gated = [row for row in rows if row["bound_kind"] == "gated"]
    for row in closed:
        if row.get("admitted_commands") is None:
            raise RuntimeError(
                f"class {row['class_index']} declares bound_kind 'closed' but "
                "produced no count; its producer did not read"
            )
    for row in open_rows:
        if row.get("admitted_commands") is not None:
            raise RuntimeError(
                f"class {row['class_index']} declares bound_kind 'open' but "
                "produced a count; one of the two is wrong"
            )
    closed_total = sum(int(row["admitted_commands"]) for row in closed)

    totals = {
        "template_classes": len(rows),
        "closed_classes": len(closed),
        "open_classes": len(open_rows),
        "gated_classes": len(gated),
        "closed_total": closed_total,
        "closed_class_indices": [row["class_index"] for row in closed],
        "open_class_indices": [row["class_index"] for row in open_rows],
        "gated_class_indices": [row["class_index"] for row in gated],
        "open_total": None,
        "why_open_total_is_null": (
            f"{len(open_rows)} of the {len(rows)} classes admit a countably "
            "infinite language. Summing them into a total would publish a "
            "number that is not a bound, so the total is reported over the "
            "closed classes only and the open classes are listed by index."
        ),
        "why_gated_is_its_own_kind": (
            "a gated class is closed in principle and unreadable on this "
            "boot. Folding it into `open` would claim the grammar is more "
            "open than it is; folding it into `closed` would put a null in a "
            "sum. It gets its own bucket and its own reason."
        ),
        "answering_vocabulary_union_is_not_summed": (
            "answering vocabularies are per-class sets over overlapping "
            "material (statement ids appear in the resolver's, the twin "
            "ledger's and `narrow`'s), so they are published per class and "
            "never added."
        ),
    }
    return rows, {"vocabularies": vocabularies, "totals": totals}


def _finding(totals: dict, rows: list[dict]) -> str:
    """P1's answer, assembled from the counts rather than asserted beside them.

    Written as a function so the sentence cannot survive a change in the
    numbers it describes: the cycle's own standing review question is whether
    a green assertion could ever have gone red, and a hand-typed "eight of
    fourteen" beside a computed 4 is exactly that failure.
    """

    total = totals["template_classes"]
    n_closed = totals["closed_classes"]
    n_open = totals["open_classes"]
    n_gated = totals["gated_classes"]
    open_forms = ", ".join(
        f"row {row['class_index']} ({row['form']})"
        for row in rows
        if row["bound_kind"] == "open"
    )
    verdict = (
        "The registered grammar is NOT finite."
        if n_open
        else "The registered grammar is finite."
    )
    return (
        f"{verdict} Of {total} template classes, {n_closed} are closed and "
        f"together admit {totals['closed_total']} commands; {n_open} admit "
        f"countably infinite languages ({open_forms}); {n_gated} is closed in "
        "principle but unreadable on this boot. Series 1's fold — 'the "
        "grammar is finite, so enumeration cost stops being an argument and "
        "becomes a number' — holds for the closed classes and FAILS for the "
        "open ones, and the open ones are exactly where plain prose lands "
        "(the resolver row and the complement row). So the number enumeration "
        "buys is the ANSWERING vocabulary, not the admitted language: an "
        "enumerating proposer has a finite target only because the committed "
        "material is finite, never because the grammar is. That is the "
        "correction P1 makes to the fold it was folded out of."
    )


def _self_digest() -> str:
    """This builder's own bytes, CRLF folded to LF.

    The committed convention (`experiments/conformance_prereg.json`'s
    `digest_algorithm`), and not a stylistic choice: git rewrites line
    endings on checkout on this workstation, so a raw-bytes self-digest
    would make the artifact disagree with its own builder on the next
    checkout — a red test with no defect behind it.
    """

    payload = Path(__file__).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(payload).hexdigest()


def build(repo_root: Path) -> dict:
    rows, extra = _classes(repo_root)
    from serve_chat import LINE_GRAMMAR  # noqa: PLC0415

    rendered = json.dumps(LINE_GRAMMAR, sort_keys=True, default=list)
    return {
        "schema": SCHEMA,
        "prerequisite": "P1",
        "design": "docs/DESIGN-session-ledger.md",
        "design_clause": (
            "§6 P1 — compute and commit the bound on admitted commands per "
            "template class of the registered grammar"
        ),
        "built_by": "scripts/measure_command_bound.py",
        "builder_digest": _self_digest(),
        "line_grammar_digest": hashlib.sha256(
            rendered.encode("utf-8")
        ).hexdigest(),
        "line_grammar_source": "scripts/serve_chat.py LINE_GRAMMAR",
        "determinism": (
            "artifact committed from a deterministic runner; reproductions "
            "welcome and recorded (ROADMAP-v0.21 §4.0(2))"
        ),
        "counting_rule": {
            "admitted": (
                "a line is admitted by a class when route_line's "
                "first-match-wins chain dispatches it to that class's route "
                "AND every slot carries a value from that class's registered "
                "vocabulary — a value the route can act on rather than refuse "
                "by name"
            ),
            "slot_kinds": {
                "closed": (
                    "a finite set fixed by a named committed producer; the "
                    "builder enumerates the producer and reports its size"
                ),
                "open": (
                    "a recursively generated or free-text language; the "
                    "class's admitted count is null and unbounded_reason "
                    "names the slot"
                ),
            },
            "open_classes_are_never_folded_into_the_total": True,
            "refusals_are_not_counted": (
                "every class refuses an unbounded set of lines by name; "
                "counting refusals would count the same infinity fourteen "
                "times"
            ),
        },
        "measured_against": (
            "the grammar whose digest this artifact carries, and only that "
            "one. P1 was first computed against a 14-row grammar and "
            "committed; v0.21's session ledger then added the `retract "
            "<assumption-id>` row its own §3 status alphabet required, which "
            "moved the grammar this measurement is OF. The artifact is "
            "recomputed rather than annotated: P1 is a computation over a "
            "committed input, not a control that ran and read unfavourably, "
            "so the record-over-rerun rule does not reach it, and a bound "
            "measured against a grammar that no longer exists would be a "
            "false sentence in a canonical artifact. The first reading and "
            "this one are both in the history, and `line_grammar_digest` "
            "dates each of them exactly."
        ),
        "classes": rows,
        **extra,
        "finding": _finding(extra["totals"], rows),
        "what_this_does_not_claim": [
            "no claim that the closed total is a bound on anything a person "
            "would type — it is a bound on what the closed classes can act on",
            "no completeness claim over readings of prose (the unreceiptable "
            "claim series 1 refused; DESIGN-session-ledger §11)",
            "no claim about slice 2's proposer, which does not exist",
            "the gloss row's lemma count is environment-gated and null here "
            "unless the WordNet archive registered on the measuring boot",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=ARTIFACT)
    ap.add_argument(
        "--check",
        action="store_true",
        help="recompute and compare with the committed artifact",
    )
    args = ap.parse_args(argv)

    payload = build(REPO)
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    out = REPO / args.out
    if args.check:
        try:
            existing = out.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"MISSING: {out}: {exc}")
            return 1
        if existing != text:
            print(f"DRIFT: recomputed {args.out} differs from the committed file")
            return 1
        print(f"P1 OK: {args.out} reproduces byte-identically")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    totals = payload["totals"]
    print(f"wrote {args.out}")
    print(
        f"  {totals['closed_classes']} closed classes admit "
        f"{totals['closed_total']} commands"
    )
    print(
        f"  {totals['open_classes']} open classes: "
        f"{totals['open_class_indices']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
