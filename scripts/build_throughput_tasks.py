#!/usr/bin/env python3
"""Build the preregistered throughput task book (T3).

`docs/DESIGN-grounded-throughput.md` §3 names the book and §6's T3 says what
it is for: **the receipt exists before the question does**. That sentence is
a construction rule, not a slogan, and this module is where it is either
kept or quietly broken.

## The one inviolable rule

This builder reads **committed artifacts as data** and computes every
expected record **itself**. It never imports and never executes an engine
module — not `harness`, `answer`, `evaluate`, `resolver`, `belief`,
`ownership`, `closure_query`, `request_grammar`, `retrieval`,
`conversation`, `story`, `supposition`, `gloss`. Executing them to produce
expected values would make the book validate the engine against itself, and
a benchmark whose answer key is the system under test measures nothing.

Reading their **source text** is a different act and is allowed, because the
rendering labels and the closed tables are *facts about the committed
tree*, not outputs of a run:

- frozen label spellings (``"exact      : "``, ``"believes   : "``) are
  quoted here and then **verified to occur in the module source**, so a
  relabelled renderer breaks the build rather than the run;
- closed tables (`request_grammar.SLOT_VALUES`, `harness.TWIN_LEVEL_ORDER`)
  are lifted with :mod:`ast` from the module's parse tree — a literal read,
  never an import.

A guard at the end of :func:`build` asserts no engine module reached
``sys.modules``, so the rule is enforced rather than promised.

## What the book contains

Seven kinds, ~107 tasks, each carrying the artifact its answer is copied or
computed from. Halves are assigned by the frozen hash rule quoted in the
``seal`` field; half B is sealed until the registered run. The rendering
modules' canonical-LF digests ride in the book as the **seal witness** that
SPEC §6 asks for: if the engine's rendering changes after the seal, the
committed test goes red and the run is void, which is exactly the effect
§6 declares.

Run twice, it writes byte-identical output: sorted keys, LF newlines, no
timestamps, no random ids.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

SCHEMA = "corollary.throughput-tasks/1"
BUILT_BY = "scripts/build_throughput_tasks.py"

SEAL = (
    "Half B is sealed until the registered run: implementation and debugging "
    "may exercise half A only; half B's first execution is the registered "
    "run. The half rule is frozen: half = 'B' if "
    "int(sha256(task_id.encode()).hexdigest()[:2], 16) % 2 else 'A'."
)

#: How a scorer must read these records. Written into the book rather than
#: left to the stopwatch's implementer, because every one of these is a place
#: a reasonable reader would otherwise guess — and guess differently from the
#: person who wrote the expectations.
SCORING_RULES = {
    "receipt_subset": (
        "receipt_expect and need_expect are subset assertions: every key "
        "present must match; absent keys are unconstrained."
    ),
    "clarification_leg": (
        "T5's clarification leg is graded per marked WAITING turn, not per "
        "task. Every clarification_due task carries at least one turn with "
        "expected_status 'waiting'; the leg passes only if the skin returns "
        "a WAITING status at 100% of those turns. On corollary/conversation "
        "that turn must additionally carry x_corollary.need matching "
        "need_expect; on corollary/kernel a WAITING status with its "
        "candidate answer lines satisfies the leg (SPEC §6.2 emits no need "
        "record on that profile). A phase:'resume' task that never waited "
        "fails the leg even if its final answer is correct."
    ),
    "per_kind_floor": (
        "T5's per-kind >=80% correctness-with-receipts floor applies to the "
        "five all-answer kinds (belief_query, closure_reachability, "
        "corpus_definition, exact_value, twin_lookup), which are the kinds "
        "counted in answerable_total. clarification_due and refusal_due are "
        "governed by their 100% gates only -- the WAITING leg above and "
        "T5's refusal gate -- and never by the 80% floor; their tasks may "
        "not be counted toward it in either direction."
    ),
    "bounded_negative_is_an_answer": (
        "A closure task whose arm is 'unreachable' expects status "
        "'exhausted' and outcome 'answer': SPEC §6.1 names it a certified "
        "bounded negative carrying its closure-receipt/1 verbatim. Likewise "
        "a relation check with holds:no is a correct answer, not a refusal."
    ),
    "zero_token_turns": (
        "Refusal, WAITING and abstained turns contribute zero useful tokens "
        "whatever their content length (SPEC §6), which is why refusal tasks "
        "carry an empty content_must_contain: there is no prose there for a "
        "score to reward."
    ),
}

#: The eleven rendering modules SPEC §6's seal-witness clause names. Their
#: canonical-LF digests are the witness that the rendering measured by the
#: registered run is the rendering the book was built against.
RENDERING_MODULES = (
    "scripts/answer.py",
    "scripts/belief.py",
    "scripts/closure_query.py",
    "scripts/evaluate.py",
    "scripts/gloss.py",
    "scripts/harness.py",
    "scripts/ownership.py",
    "scripts/resolver.py",
    "scripts/retrieval.py",
    "scripts/story.py",
    "scripts/supposition.py",
)

#: Never importable from here. The guard is a list rather than a convention
#: because a convention is what an implementer under time pressure edits.
FORBIDDEN_MODULES = (
    "answer", "belief", "closure_check", "closure_query", "closure_worlds",
    "controller", "conversation", "decompose", "dispatcher", "evaluate",
    "frames", "gloss", "harness", "match_signatures", "ownership",
    "request_grammar", "resolver", "retrieval", "story", "supposition",
    "write_stage",
)

#: Corpora authored mechanically in bulk. Their `statement_meaning` is a
#: provenance sentence, not an explanation, so a definition task built from
#: one would score a machine's boilerplate as a person-authored answer.
#: (`scripts/answer.py` reads the same registry from `decompose`; the value
#: is lifted from that module's source below rather than assumed.)
INGESTED_PREFIX_SOURCE = "scripts/decompose.py"

TWIN_LEDGER_PATH = "reports/signature_matches.json"
CLOSURE_TARGET_MANIFEST = "data/closure_targets/manifest.json"
UNREGISTERED_PATH = "tool.freeform_answer"

#: The five twin levels and their strength order, lifted from
#: `harness.TWIN_LEVEL_ORDER`, paired with the ledger field each reads.
TWIN_LEDGER_FIELDS = {
    "typed": "typed_twin_groups",
    "family": "family_twin_groups_beyond_typed",
    "aliased": "aliased_twin_groups_beyond_typed",
    "mirror": "mirror_twin_groups",
    "shape": "shape_twin_groups",
}

ANSWERABLE_KINDS = (
    "belief_query",
    "closure_reachability",
    "corpus_definition",
    "exact_value",
    "twin_lookup",
)

#: T3's floor, and the kinds a drop would take with it (SPEC §9 ¶DEV-2).
CONDITIONAL_KINDS = ("closure_reachability", "twin_lookup")

#: Kinds whose task population IS the committed artifact supply, exhausted.
#: `closure_reachability` can hold exactly the eight targets
#: `data/closure_targets/manifest.json` registers, and W2's route answers
#: about no other file by design (`harness._unregistered_target`). A kind
#: like this keeps whatever half-B count its fixed population yields: the
#: alternative is padding — the same target asked twice, or a manufactured
#: state — and SPEC §9 already refuses manufactured states for exactly this
#: reason, recording a world's shortfall in the manifest instead. The cap is
#: recorded in the book's counts rather than worked around.
POPULATION_CAPPED_KINDS = ("closure_reachability",)

MIN_TASKS = 100
MIN_ANSWERABLE = 50

#: Raised from 3 to 5 before the seal (pre-seal construction change, not a
#: half reassignment): at three half-B tasks T5's per-kind 80% floor turns
#: on a single answer, which grades the coin toss rather than the kind.
MIN_HALF_B_PER_ANSWERABLE_KIND = 5


class BuildRefused(RuntimeError):
    """A construction rule could not be satisfied. Never worked around."""


# ---------------------------------------------------------------------------
# reading the tree as data
# ---------------------------------------------------------------------------


@lru_cache(maxsize=None)
def read_text(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


@lru_cache(maxsize=None)
def read_json(rel: str):
    return json.loads(read_text(rel))


def canonical_lf_sha256(rel: str) -> str:
    """SPEC §6's canonical-LF digest: file bytes with CRLF folded to LF."""

    payload = (REPO / rel).read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(payload).hexdigest()


def canonical_json(value) -> str:
    """SPEC §4.1's canonical-JSON/compact."""

    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def node_sha256(node: dict) -> str:
    return hashlib.sha256(canonical_json(node).encode("utf-8")).hexdigest()


def half_of(task_id: str) -> str:
    """The frozen rule, spelled once and quoted in the book's `seal`."""

    return "B" if int(hashlib.sha256(task_id.encode()).hexdigest()[:2], 16) % 2 else "A"


def module_literal(rel: str, name: str):
    """Lift a module-level literal by parsing the source. Never an import."""

    tree = ast.parse(read_text(rel), filename=rel)
    for statement in tree.body:
        targets = []
        if isinstance(statement, ast.Assign):
            targets = statement.targets
        elif isinstance(statement, ast.AnnAssign):
            targets = [statement.target]
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id == name:
                if statement.value is None:
                    continue
                return ast.literal_eval(statement.value)
    raise BuildRefused(f"{rel} has no module-level literal named {name!r}")


def require_label(rel: str, label: str, source_cache: dict[str, str]) -> str:
    """A frozen rendering label, checked against the module that spells it.

    The builder quotes labels rather than calling the renderer. That is only
    honest if a relabelled renderer breaks the build, so every quoted label
    is asserted to occur in the module's source text.
    """

    text = source_cache.setdefault(rel, read_text(rel))
    if label not in text:
        raise BuildRefused(
            f"{rel} no longer spells the label {label!r}; the frozen "
            "rendering this book quotes has changed and the expected records "
            "must be rebuilt against it rather than patched"
        )
    return label


# ---------------------------------------------------------------------------
# corpora
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def corpus_files() -> tuple[tuple[str, str], ...]:
    """`(repo-relative path, corpus_id)` for every committed corpus, sorted."""

    out = []
    for path in sorted((REPO / "data").glob("*/nodes.json")):
        rel = path.relative_to(REPO).as_posix()
        doc = read_json(rel)
        out.append((rel, str(doc.get("corpus_id", path.parent.name))))
    return tuple(out)


def corpus_nodes(rel: str) -> list[dict]:
    return read_json(rel).get("statement_nodes", [])


def ingested_prefixes() -> tuple[str, ...]:
    return tuple(module_literal(INGESTED_PREFIX_SOURCE, "INGESTED_CORPUS_PREFIXES"))


@lru_cache(maxsize=1)
def statement_id_to_corpus() -> dict[str, str]:
    out: dict[str, str] = {}
    for rel, corpus in corpus_files():
        for node in corpus_nodes(rel):
            sid = node.get("statement_id")
            if isinstance(sid, str):
                out[sid] = corpus
    return out


def all_statement_ids() -> set[str]:
    return set(statement_id_to_corpus())


@lru_cache(maxsize=1)
def _folded_corpus_text() -> tuple[str, ...]:
    return tuple(read_text(rel).casefold() for rel, _corpus in corpus_files())


def token_is_absent(token: str) -> bool:
    """True when `token` occurs in no committed corpus file, case-blind."""

    needle = token.casefold()
    return all(needle not in text for text in _folded_corpus_text())


# ---------------------------------------------------------------------------
# kind 1 — corpus_definition
# ---------------------------------------------------------------------------

#: A statement id reaches the resolver's exact-id rung only if nothing
#: upstream claims the line. Every upstream claimant is excluded by
#: construction: `_looks_like_path` needs a `/`, a `\` or a `.json` tail;
#: `match_signatures.TOKEN_RE` has no `.`, so a dotted id cannot tokenize and
#: both the expression resolver and the evaluator decline it. This pattern is
#: the set of ids for which those facts hold.
ID_SHAPE = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"


def id_is_routable(sid: str) -> bool:
    if "." not in sid or sid.endswith(".json"):
        return False
    if "/" in sid or "\\" in sid:
        return False
    parts = sid.split(".")
    if any(not part for part in parts):
        return False
    return all(all(ch in ID_SHAPE for ch in part) for part in parts)


def corpus_definition_pool() -> list[dict]:
    """Eligible definition tasks, in a fixed spread across every corpus.

    Round-robin rather than "first N of the sorted whole": taking the first
    two ids per corpus in corpus order would have filled the book from the
    alphabetically early half of `data/` and left twelve corpora unmeasured.
    Round-robin visits every corpus before it visits any corpus twice, which
    is the spread the design asks for and is just as deterministic.
    """

    ingested = ingested_prefixes()
    per_corpus: list[tuple[str, str, list[dict]]] = []
    for rel, corpus in corpus_files():
        if corpus.startswith(ingested):
            continue
        eligible = []
        for node in sorted(
            corpus_nodes(rel), key=lambda n: str(n.get("statement_id", ""))
        ):
            sid = node.get("statement_id")
            title = node.get("title")
            meaning = (node.get("semantic_interpretation") or {}).get(
                "statement_meaning"
            )
            if not isinstance(sid, str) or not id_is_routable(sid):
                continue
            if not isinstance(title, str) or not title.strip():
                continue
            if not isinstance(meaning, str) or not meaning.strip():
                continue
            eligible.append(
                {
                    "statement_id": sid,
                    "corpus_path": rel,
                    "corpus_id": corpus,
                    "title": title,
                    "meaning": meaning,
                    "node_sha256": node_sha256(node),
                }
            )
        if eligible:
            per_corpus.append((rel, corpus, eligible))

    pool: list[dict] = []
    depth = 0
    while True:
        added = False
        for _rel, _corpus, eligible in per_corpus:
            if depth < len(eligible):
                pool.append(eligible[depth])
                added = True
        if not added:
            break
        depth += 1
    return pool


def corpus_definition_task(record: dict) -> dict:
    sid = record["statement_id"]
    return {
        "task_id": f"corpus_definition/{sid}",
        "kind": "corpus_definition",
        "profile": "corollary/kernel",
        "turns": [{"role": "user", "content": sid}],
        "expected": {
            "outcome": "answer",
            "check": "receipt",
            "status_expect": "found",
            "content_must_contain": [record["title"], record["meaning"]],
            "artifact_refs": [f"{record['corpus_path']}#{sid}"],
            "receipt_expect": {
                "statement_id": sid,
                "corpus_path": record["corpus_path"],
                "node_sha256": record["node_sha256"],
            },
        },
    }


# ---------------------------------------------------------------------------
# kind 2 — exact_value (generated here, with this module's own arithmetic)
# ---------------------------------------------------------------------------


def num(value: int) -> dict:
    return {"num": str(value)}


def var(name: str) -> dict:
    return {"var": name}


def op(symbol: str, *args: dict) -> dict:
    return {"op": symbol, "args": list(args)}


def eval_node(node: dict, bindings: dict[str, Fraction]) -> Fraction:
    """Exact evaluation, written here so the book never asks the engine."""

    if "num" in node:
        return Fraction(node["num"])
    if "var" in node:
        return bindings[node["var"]]
    symbol = node["op"]
    args = [eval_node(arg, bindings) for arg in node["args"]]
    if symbol == "+":
        return sum(args, Fraction(0))
    if symbol == "*":
        out = Fraction(1)
        for arg in args:
            out *= arg
        return out
    if symbol == "neg":
        return -args[0]
    if symbol == "inv":
        if args[0] == 0:
            raise BuildRefused("division by zero")
        return Fraction(1) / args[0]
    if symbol == "^":
        base, exponent = args
        if exponent.denominator != 1:
            raise BuildRefused("only integer exponents are exact")
        return base ** int(exponent)
    raise BuildRefused(f"no exact rule for operator {symbol!r}")


def format_exact(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


RELATION_TESTS = {
    "=": lambda a, b: a == b,
    "<": lambda a, b: a < b,
    ">": lambda a, b: a > b,
    "<=": lambda a, b: a <= b,
    ">=": lambda a, b: a >= b,
}


#: Eight evaluation shapes, cycled. Shapes 4-7 exist to stop the kind from
#: only ever asking for a positive integer:
#:
#: - **non-integer results** reach `inv` through the `/` glyph, which is a
#:   real surface form: `match_signatures.TOKEN_RE` accepts `/`, and
#:   `Parser.parse_product` rewrites `a / b` to `*(a, inv(b))`
#:   (`scripts/match_signatures.py:359-366`), which `evaluate._eval_tree`
#:   evaluates as `Fraction(1) / b`. `Evaluation.formatted` then prints
#:   `n/d`, so `exact      : 19/13` is a renderable answer and the kind is
#:   no longer blind to the exactness the whole module is named for.
#: - **negative results** reach `neg` two ways, both glyph-surfaced:
#:   `Parser.parse_sum` rewrites binary `a - b` to `+(a, neg(b))`, and
#:   `Parser.parse_atom` reads a leading `-` as `neg` directly
#:   (`scripts/match_signatures.py:341-349`, `:374-376`).
#:
#: Both were read out of the parser's source, not discovered by running it.
#: The generator asserts the intended property of every shape it emits, so a
#: parameter that quietly divided evenly would break the build.
EVALUATION_SHAPES = 8

#: Eight relation shapes, cycled, arranged so the truth value does NOT
#: correlate with the operator glyph: `>` and `<` each appear once true and
#: once false, `=` twice each. Every false relation is off by exactly one,
#: so a system that got the arithmetic nearly right still scores wrong —
#: which is the only way this kind separates computing from approximating.
RELATION_SHAPES = 8


def evaluation_spec(index: int) -> dict:
    """One generated evaluation: English line, parse shape, exact value.

    The line and the tree come out of the same generator, so they cannot
    disagree; `expression` is the substring the committed front end selects
    (the longest fragment after the `what is` separator), which is a
    property of the text this function wrote, not a guess about a run.
    """

    a, b, c = 7 + 3 * index, 5 + 2 * index, 11 + index
    shape = index % EVALUATION_SHAPES
    bindings: dict[str, str] = {}
    if shape == 0:
        expression = f"{a} * {b} + {c}"
        tree = op("+", op("*", num(a), num(b)), num(c))
    elif shape == 1:
        expression = f"{a} + {b} * {c}"
        tree = op("+", num(a), op("*", num(b), num(c)))
    elif shape == 2:
        expression = f"{a} ^ 2 + {b}"
        tree = op("+", op("^", num(a), num(2)), num(b))
    elif shape == 3:
        expression = f"x ^ 2 + {b} * x"
        tree = op("+", op("^", var("x"), num(2)), op("*", num(b), var("x")))
        bindings = {"x": str(a)}
    elif shape == 4:
        expression = f"{a} / {b}"
        tree = op("*", num(a), op("inv", num(b)))
    elif shape == 5:
        expression = f"{c} / {b}"
        tree = op("*", num(c), op("inv", num(b)))
    elif shape == 6:
        expression = f"{c} - {a}"
        tree = op("+", num(c), op("neg", num(a)))
    else:
        expression = f"{b} * -{a}"
        tree = op("*", num(b), op("neg", num(a)))

    line = (
        f"suppose x = {a}, what is {expression}"
        if bindings
        else f"what is {expression}"
    )
    resolved = {k: Fraction(v) for k, v in bindings.items()}
    value = eval_node(tree, resolved)

    if shape in (4, 5) and value.denominator == 1:
        raise BuildRefused(
            f"evaluation shape {shape} at index {index} divided evenly "
            f"({expression} = {value}); the shape exists to exercise a "
            "non-integer exact answer and would be testing nothing"
        )
    if shape in (6, 7) and value >= 0:
        raise BuildRefused(
            f"evaluation shape {shape} at index {index} is not negative "
            f"({expression} = {value}); the shape exists to exercise `neg`"
        )

    return {
        "form": "evaluate",
        "line": line,
        "expression": expression,
        "tree": tree,
        "bindings": bindings,
        "expected_exact": format_exact(value),
    }


def relation_spec(index: int) -> dict:
    """One generated relation check. A false relation is still an ANSWER."""

    a, b = 13 + 2 * index, 4 + 3 * index
    total = a + b
    shape = index % RELATION_SHAPES
    bindings: dict[str, str] = {}
    if shape == 0:
        left, right, symbol = op("*", num(a), num(b)), num(a * b), "="
        expression = f"{a} * {b} = {a * b}"
    elif shape == 1:
        left, right, symbol = op("*", num(a), num(b)), num(a * b + 1), "="
        expression = f"{a} * {b} = {a * b + 1}"
    elif shape == 2:
        left, right, symbol = op("+", num(a), num(b)), num(total - 1), ">"
        expression = f"{a} + {b} > {total - 1}"
    elif shape == 3:
        left, right, symbol = op("+", num(a), num(b)), num(total + 1), ">"
        expression = f"{a} + {b} > {total + 1}"
    elif shape == 4:
        left, right, symbol = op("+", num(a), num(b)), num(total + 1), "<"
        expression = f"{a} + {b} < {total + 1}"
    elif shape == 5:
        left, right, symbol = op("+", num(a), num(b)), num(total - 1), "<"
        expression = f"{a} + {b} < {total - 1}"
    elif shape == 6:
        left, right, symbol = op("^", var("y"), num(2)), num(a * a), "="
        expression = f"y ^ 2 = {a * a}"
        bindings = {"y": str(a)}
    else:
        left, right, symbol = op("^", var("y"), num(2)), num(a * a + 1), "="
        expression = f"y ^ 2 = {a * a + 1}"
        bindings = {"y": str(a)}

    line = (
        f"suppose y = {a}, does {expression}"
        if bindings
        else f"does {expression}"
    )
    resolved = {k: Fraction(v) for k, v in bindings.items()}
    holds = RELATION_TESTS[symbol](
        eval_node(left, resolved), eval_node(right, resolved)
    )
    return {
        "form": "relation",
        "line": line,
        "expression": expression,
        "relation": symbol,
        "left": left,
        "right": right,
        "bindings": bindings,
        "expected_holds": bool(holds),
    }


def exact_value_task(spec: dict, labels: dict[str, str]) -> dict:
    if spec["form"] == "evaluate":
        content = [
            f"{labels['expression']}{spec['expression']}",
            f"{labels['exact']}{spec['expected_exact']}",
        ]
        if spec["bindings"]:
            given = ", ".join(
                f"{k} = {v}" for k, v in sorted(spec["bindings"].items())
            )
            content.insert(1, f"{labels['given']}{given}")
        receipt = {
            "expression": spec["expression"],
            "exact": spec["expected_exact"],
            "grounding": "computed",
        }
        # `/` would read as another path segment in the task id, which the
        # half rule hashes verbatim; spell it instead of embedding it.
        slug = spec["expression"].replace(" ", "").replace("/", "over")
    else:
        content = [
            f"{labels['relation']}{spec['expression']}",
            f"{labels['holds']}{'yes' if spec['expected_holds'] else 'no'}",
        ]
        receipt = {"expression": spec["expression"], "grounding": "computed"}
        # `/` would read as another path segment in the task id, which the
        # half rule hashes verbatim; spell it instead of embedding it.
        slug = spec["expression"].replace(" ", "").replace("/", "over")
    return {
        "task_id": f"exact_value/{spec['form']}/{slug}",
        "kind": "exact_value",
        "profile": "corollary/kernel",
        "turns": [{"role": "user", "content": spec["line"]}],
        "expr_spec": spec,
        "expected": {
            "outcome": "answer",
            "check": "exact",
            "status_expect": "solved",
            "content_must_contain": content,
            "artifact_refs": [],
            "receipt_expect": receipt,
        },
    }


# ---------------------------------------------------------------------------
# kind 3 — twin_lookup
# ---------------------------------------------------------------------------


def twin_pool() -> list[dict]:
    """Ledger groups a `twin <id>` line can be answered from unambiguously.

    Three data conditions, all checkable in the committed ledger:

    1. the queried id is not an ingested one (the answer should be readable);
    2. every group listing the id carries the **same** member tuple, so the
       reported members do not depend on which group the miss chain surfaced;
    3. the group has two to four members, which is a group a person can read.

    Condition 2 is the load-bearing one. `_route_twin` reports the strongest
    level among the groups that list the id; without it, a book built from
    one group could disagree with an engine that reported another.
    """

    report = read_json(TWIN_LEDGER_PATH)
    levels = list(module_literal("scripts/harness.py", "TWIN_LEVEL_ORDER"))
    if set(levels) != set(TWIN_LEDGER_FIELDS):
        raise BuildRefused(
            "harness.TWIN_LEVEL_ORDER no longer matches the ledger fields "
            "this builder reads"
        )
    ingested = ingested_prefixes()
    corpora = statement_id_to_corpus()

    owner: dict[str, list[tuple[int, int, str, tuple[str, ...]]]] = {}
    for order, level in enumerate(levels):
        field = TWIN_LEDGER_FIELDS[level]
        for index, group in enumerate(report.get(field, [])):
            members = tuple(
                member["statement_id"] for member in group["members"]
            )
            for member in members:
                owner.setdefault(member, []).append(
                    (order, index, level, members)
                )

    chosen: dict[tuple[int, int], dict] = {}
    for sid in sorted(owner):
        if not id_is_routable(sid):
            continue
        if corpora.get(sid, "").startswith(ingested):
            continue
        entries = owner[sid]
        member_sets = {entry[3] for entry in entries}
        if len(member_sets) != 1:
            continue
        members = entries[0][3]
        if not 2 <= len(members) <= 4:
            continue
        if any(corpora.get(m, "").startswith(ingested) for m in members):
            continue
        order, index, level, _members = min(entries)
        key = (order, index)
        if key in chosen:
            # One task per distinct ledger group: two members of the same
            # group are the same receipt asked twice.
            continue
        # `_route_twin` reports the STRONGEST level among the groups that
        # list the id, so a task claiming level L is only a test of that
        # selection if no stronger level lists the id at all. `min(entries)`
        # already picks the strongest; this asserts what that implies, so a
        # ledger change that added a stronger group would break the build
        # rather than silently make the task expect the wrong level.
        stronger = [entry for entry in entries if entry[0] < order]
        if stronger:
            raise BuildRefused(
                f"{sid} is listed at a stronger level than {level}"
            )
        chosen[key] = {
            "statement_id": sid,
            "level": level,
            "group_index": index,
            "member_ids": list(members),
            "group_count": len(entries),
            "levels_listing_id": sorted({entry[2] for entry in entries}),
        }
    # Strongest level first, then the smallest groups: a `typed` pair is the
    # most legible receipt the ledger holds, and the weak levels are the ones
    # whose membership a reader has to take on trust.
    return [
        chosen[key]
        for key in sorted(
            chosen, key=lambda k: (k[0], len(chosen[k]["member_ids"]), k[1])
        )
    ]


def twin_task(record: dict, labels: dict[str, str]) -> dict:
    sid = record["statement_id"]
    others = [m for m in record["member_ids"] if m != sid]
    return {
        "task_id": f"twin_lookup/{sid}",
        "kind": "twin_lookup",
        "profile": "corollary/kernel",
        "turns": [{"role": "user", "content": f"twin {sid}"}],
        "ledger_group": {
            "level": record["level"],
            "group_index": record["group_index"],
            "field": TWIN_LEDGER_FIELDS[record["level"]],
            # Every level that lists this id. The reported level is the
            # strongest of these, so a task whose id sits in exactly one
            # level tests the lookup and a task whose id sits in several
            # tests the strongest-level selection as well.
            "levels_listing_id": list(record["levels_listing_id"]),
        },
        "expected": {
            "outcome": "answer",
            "check": "receipt",
            "status_expect": "found",
            "content_must_contain": others,
            "artifact_refs": [TWIN_LEDGER_PATH],
            "receipt_expect": {
                "ledger_path": TWIN_LEDGER_PATH,
                "level": record["level"],
                "group_index": record["group_index"],
                "member_ids": list(record["member_ids"]),
            },
        },
        "rendered_lines": [
            f"{labels['level']}{record['level']}",
            *[f"{labels['member']}{m}" for m in record["member_ids"]],
            f"{labels['ledger']}{TWIN_LEDGER_PATH}",
        ],
    }


# ---------------------------------------------------------------------------
# kind 4 — closure_reachability
# ---------------------------------------------------------------------------


def closure_tasks(labels: dict[str, str]) -> list[dict]:
    """Every committed target, both arms.

    The bounded negative is an ANSWER: SPEC §6.1 names `exhausted` on the
    `closure` route as a certified bounded negative carrying its
    `closure-receipt/1` verbatim. Scoring it as a refusal would be the
    benchmark discarding the one result the closure machinery exists to
    produce.
    """

    manifest = read_json(CLOSURE_TARGET_MANIFEST)
    worlds = {}
    for summary in manifest["worlds"]:
        world_id = summary["world_id"]
        closure_rel = summary["closure"]
        closure = read_json(closure_rel)
        worlds[world_id] = {
            "closure_path": closure_rel,
            "closure_digest": closure["closure_digest"],
            "adapter_id": closure["adapter_id"],
            "horizon": closure["horizon"],
            "visited_states": len(closure["states"]),
        }

    out = []
    for entry in manifest["files"]:
        world_id = entry["world_id"]
        world = worlds[world_id]
        target = entry["path"]
        reachable = entry["arm"] == "reachable"
        outcome = "REACHABLE" if reachable else "NOT_REACHABLE_WITHIN_HORIZON"
        status = "found" if reachable else "exhausted"

        digest = hashlib.sha256((REPO / target).read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            raise BuildRefused(
                f"{target} does not match its manifest digest; the target set "
                "is not the one the manifest registers"
            )

        content = [
            f"{labels['closure_line']}{world['closure_path']}",
            f"{labels['world_id']}{world_id}",
            f"{labels['horizon']}{world['horizon']}",
            f"{labels['visited_states']}{world['visited_states']}",
            f"{labels['closure_digest']}{world['closure_digest']}",
            f"{labels['adapter_id']}{world['adapter_id']}",
            f"{labels['target_digest']}{digest}",
            f"{labels['outcome']}{outcome}",
        ]
        if reachable:
            route_length = entry["route_length"]
            content.append(
                f"{labels['shortest_route']}{route_length} action(s), "
                "replayed through the world's own verifier"
            )
            if route_length == 0:
                content.append("(the target IS the initial state)")
        else:
            content.append(
                f"these canonical bytes are not reachable within horizon "
                f"{world['horizon']} of the closure named above, which "
                f"visited {world['visited_states']} states"
            )

        out.append(
            {
                "task_id": (
                    f"closure_reachability/{world_id}.{entry['arm']}."
                    f"{entry['index']}"
                ),
                "kind": "closure_reachability",
                "profile": "corollary/kernel",
                "turns": [
                    {"role": "user", "content": f"reachable {world_id} {target}"}
                ],
                "expected": {
                    "outcome": "answer",
                    "check": "verdict",
                    "status_expect": status,
                    "content_must_contain": content,
                    "artifact_refs": [target, world["closure_path"]],
                    "receipt_expect": {
                        "schema": "closure-receipt/1",
                        "world_id": world_id,
                        "closure_digest": world["closure_digest"],
                        "adapter_id": world["adapter_id"],
                        "horizon": world["horizon"],
                        "visited_states": world["visited_states"],
                        "target_digest": digest,
                        "outcome": outcome,
                    },
                },
            }
        )
    return out


# ---------------------------------------------------------------------------
# kind 5 — belief_query
# ---------------------------------------------------------------------------

#: Each row: agent, subject, the place the agent SAW, an optional world fact
#: the agent did not witness, an optional identity the agent knows, and which
#: narration form states the world fact.
#:
#: The expected place is derived here from the documented visibility rule
#: (`scripts/belief.py`'s module docstring): an agent believes what it
#: witnessed, rewritten through the identities it holds; a world fact the
#: agent did not see never enters the agent's store. That derivation is read
#: off the design, not off a run.
#:
#: Two world-fact forms, because `belief.read` has two and a book that only
#: ever used one would leave half the narrator channel unmeasured:
#: ``moves`` matches `WORLD_MOVE`, ``in`` matches `WORLD_IN` — the
#: "bob is in the kitchen" sentence the module's own docstring opens with
#: (`scripts/belief.py:76-82`). Both land in the world store, which the
#: query does not read; that separation is the whole false-belief result.
BELIEF_ROWS = (
    ("dotty", "bob", "room", None, None, None),
    ("ann", "ball", "box", None, None, None),
    ("marco", "cat", "garden", None, None, None),
    ("sally", "marble", "basket", "box", None, "moves"),
    ("nina", "kite", "attic", "shed", None, "moves"),
    ("omar", "coin", "drawer", "pocket", None, "moves"),
    ("pia", "book", "shelf", "table", None, "moves"),
    ("quinn", "lamp", "hall", None, "corridor", None),
    ("rosa", "key", "porch", None, "veranda", None),
    ("sam", "apple", "crate", "sink", "bin", "moves"),
    ("tess", "hat", "locker", "bench", "cupboard", "moves"),
    ("ivo", "dog", "yard", "kennel", "shed", "moves"),
    # The docstring's own opening case, and its rewrite-carrying sibling.
    ("hugo", "bob", "room", "kitchen", None, "in"),
    ("lena", "vase", "study", "cellar", "office", "in"),
)


def belief_task(row: tuple, labels: dict[str, str]) -> dict:
    agent, subject, seen, moved, alias, world_form = row
    believed = alias if alias else seen
    if bool(moved) != bool(world_form):
        raise BuildRefused(f"{agent}: a world fact needs a narration form")

    sentences = [f"{agent} sees {subject} go into the {seen}"]
    if alias:
        sentences.append(f"{agent} knows the {seen} is the {alias}")
    if moved:
        sentences.append(
            f"{subject} is in the {moved}"
            if world_form == "in"
            else f"{subject} moves to the {moved}"
        )
    sentences.append(f"where does {agent} think {subject} is")
    line = ". ".join(sentences)

    content = [
        f"{labels['agent']}{agent}",
        f"{labels['subject']}{subject}",
        f"{labels['believes']}located_in({subject}) = {believed}",
    ]
    if moved:
        content.append(f"{labels['world_says']}located_in({subject}) = {moved}")
        if moved != believed:
            content.append(labels["divergence"])
    content.append(f"{agent} observed  located_in({subject}) = {seen}")
    if alias:
        content.append(f"{agent} holds     same_as({seen}) = {alias}")
        content.append(f"rewrite         located_in({subject}) = {alias}")
    if moved:
        content.append(f"narrator        located_in({subject}) = {moved}")

    return {
        "task_id": f"belief_query/{agent}.{subject}.{seen}",
        "kind": "belief_query",
        "profile": "corollary/kernel",
        "turns": [{"role": "user", "content": line}],
        "false_belief": bool(moved and moved != believed),
        "world_fact_form": world_form,
        "expected": {
            "outcome": "answer",
            "check": "verdict",
            "status_expect": "found",
            "content_must_contain": content,
            "artifact_refs": [],
            "receipt_expect": {"derivation": "session"},
        },
    }


# ---------------------------------------------------------------------------
# kind 6 — refusal_due (verified absences and pinned refusals)
# ---------------------------------------------------------------------------

PINNED_LINE_TESTS = "tests/test_harness_line.py"
PINNED_WIRING_TESTS = "tests/test_wiring_routes.py"

#: Statement ids that name nothing, spelled out of tokens the corpora do not
#: contain anywhere. The spelling matters: a plausible-looking absent id
#: ("no.such.statement.anywhere") still reduces to ordinary English content
#: words, and the word resolver's disposition on those is a property of the
#: index rather than of the absence. Alien tokens make the absence total, and
#: the builder verifies it against every committed corpus file.
ABSENT_ID_TOKENS = (
    ("zzqx", "frobnitzim", "glarblewurt"),
    ("blorptaxis", "wug", "zzqx"),
)

#: `owns ACKERMANN(x, y)` is exhausted rather than refused: the query parses,
#: and no committed statement hosts the head. Verified, not assumed.
ABSENT_HEAD = "ACKERMANN"


def refusal_tasks() -> list[dict]:
    known_ids = all_statement_ids()
    manifest = read_json(CLOSURE_TARGET_MANIFEST)
    listed = {entry["path"] for entry in manifest["files"]}
    story_targets = [
        entry
        for entry in manifest["files"]
        if entry["world_id"] == "story.golden_chicken"
        and entry["arm"] == "reachable"
    ]
    visual_targets = [
        entry for entry in manifest["files"] if entry["world_id"] == "visual.rt0000"
    ]
    if not story_targets or not visual_targets:
        raise BuildRefused("the target manifest lost a world this book cites")
    cross_world_target = visual_targets[0]["path"]
    other_world_target = story_targets[1]["path"]

    if "README.md" in listed:
        raise BuildRefused("README.md is a registered target; the gate case is void")
    if not token_is_absent(ABSENT_HEAD):
        raise BuildRefused(
            f"{ABSENT_HEAD} now occurs in a committed corpus; the unhosted-head "
            "case no longer tests an absence"
        )

    tasks: list[dict] = []

    def add(slug, line, route, status, refs, receipt=None, extra=None):
        task = {
            "task_id": f"refusal_due/{slug}",
            "kind": "refusal_due",
            "profile": "corollary/kernel",
            "turns": [{"role": "user", "content": line}],
            "route_expect": route,
            "expected": {
                "outcome": "refuse",
                "check": "verdict",
                "status_expect": status,
                # Refusal turns score zero useful tokens whatever their
                # length (SPEC §6), so a required substring here would grade
                # nothing. The claim under test is the status, not the prose.
                "content_must_contain": [],
                "artifact_refs": list(refs),
                "receipt_expect": receipt or {},
            },
        }
        if extra:
            task.update(extra)
        tasks.append(task)

    add("owns_bare_variable", "owns x", "ownership", "refused",
        [PINNED_LINE_TESTS])
    add("owns_unparseable", "owns ((((", "ownership", "refused",
        [PINNED_LINE_TESTS])
    add(
        "owns_unhosted_head",
        f"owns {ABSENT_HEAD}(x, y)",
        "ownership",
        "exhausted",
        [PINNED_LINE_TESTS],
        extra={
            "verified_absence": {
                "tokens": [ABSENT_HEAD],
                "searched": "data/*/nodes.json",
            }
        },
    )
    add("english_owns_question", "who owns x^2?", "dispatcher", "exhausted",
        [PINNED_LINE_TESTS], {"missing_capability": UNREGISTERED_PATH})
    add(
        "english_open_domain",
        "why did the chicken cross the road?",
        "dispatcher",
        "exhausted",
        [PINNED_LINE_TESTS],
        {"missing_capability": UNREGISTERED_PATH},
    )

    for index, tokens in enumerate(ABSENT_ID_TOKENS):
        absent_id = ".".join(tokens)
        if absent_id in known_ids:
            raise BuildRefused(f"{absent_id} is a committed statement id")
        for token in tokens:
            if not token_is_absent(token):
                raise BuildRefused(
                    f"{token!r} now occurs in a committed corpus; "
                    f"{absent_id} is no longer a total absence"
                )
        add(
            f"absent_statement_{index}",
            absent_id,
            "dispatcher",
            "exhausted",
            [],
            {"missing_capability": UNREGISTERED_PATH},
            extra={
                "verified_absence": {
                    "tokens": list(tokens),
                    "searched": "data/*/nodes.json",
                }
            },
        )

    add("twin_bare_command", "twin", "twin", "refused", [PINNED_WIRING_TESTS])
    add("twin_two_arguments", "twin logic.a logic.b", "twin", "refused",
        [PINNED_WIRING_TESTS])
    add(
        "reachable_unregistered_target",
        "reachable story.golden_chicken README.md",
        "closure",
        "refused",
        [CLOSURE_TARGET_MANIFEST, PINNED_WIRING_TESTS],
    )
    add(
        "reachable_cross_world_target",
        f"reachable story.golden_chicken {cross_world_target}",
        "closure",
        "refused",
        [CLOSURE_TARGET_MANIFEST, PINNED_WIRING_TESTS],
    )
    add(
        "reachable_unknown_world",
        f"reachable nonsense.world {other_world_target}",
        "closure",
        "refused",
        [PINNED_WIRING_TESTS],
    )
    add(
        "reachable_missing_argument",
        "reachable story.golden_chicken",
        "closure",
        "refused",
        [PINNED_WIRING_TESTS],
    )
    add(
        "reachable_absent_target_file",
        "reachable story.golden_chicken data/closure_targets/no_such.json",
        "closure",
        "refused",
        [CLOSURE_TARGET_MANIFEST, PINNED_WIRING_TESTS],
    )
    add(
        "reachable_closure_is_not_a_target",
        "reachable story.golden_chicken "
        "reports/closures/story.golden_chicken.closure.json",
        "closure",
        "refused",
        [CLOSURE_TARGET_MANIFEST, PINNED_WIRING_TESTS],
    )
    return tasks


# ---------------------------------------------------------------------------
# kind 7 — clarification_due
# ---------------------------------------------------------------------------

REQUEST_GRAMMAR = "scripts/request_grammar.py"
CONVERSATION_SLOT = "egg_color"

#: Utterances that name a registered slot phrase and an UNREGISTERED value.
#: Each must reach `unregistered-value`, which is a WAITING need and never a
#: nearest-match: that is precisely what T5's clarification leg grades.
UNREGISTERED_UTTERANCES = (
    ("imperative_purple", "make the eggs purple", "purple"),
    ("imperative_turquoise", "make the egg color turquoise", "turquoise"),
    ("turn_chartreuse", "turn the eggs chartreuse", "chartreuse"),
    ("set_magenta", "set the eggs magenta", "magenta"),
    ("owner_lavender", "make my eggs lavender", "lavender"),
    ("slot_phrase_only", "the eggs", None),
)


def clarification_tasks(labels: dict[str, str]) -> list[dict]:
    slot_phrases = module_literal(REQUEST_GRAMMAR, "SLOT_PHRASES")
    slot_values = module_literal(REQUEST_GRAMMAR, "SLOT_VALUES")
    registered = tuple(slot_values[CONVERSATION_SLOT])

    for _slug, utterance, value in UNREGISTERED_UTTERANCES:
        if value is not None and value in registered:
            raise BuildRefused(
                f"{value!r} is a registered value; the ask task would answer"
            )
        if not any(phrase in utterance for phrase in slot_phrases):
            raise BuildRefused(
                f"{utterance!r} names no registered slot phrase, so it would "
                "fail for the wrong reason"
            )

    ask_prompt = f"{labels['need_prompt']}{CONVERSATION_SLOT!r} for"
    tasks: list[dict] = []

    for slug, utterance, _value in UNREGISTERED_UTTERANCES:
        tasks.append(
            {
                "task_id": f"clarification_due/ask/{slug}",
                "kind": "clarification_due",
                "profile": "corollary/conversation",
                "phase": "ask",
                # Marked on the turn as well as on the task: T5's
                # clarification leg is graded per WAITING turn, and a leg
                # that had to infer which turn it meant would grade a
                # different set for every implementer.
                "turns": [
                    {
                        "role": "user",
                        "content": utterance,
                        "expected_status": "waiting",
                    }
                ],
                "expected": {
                    "outcome": "ask",
                    "check": "verdict",
                    "status_expect": "waiting",
                    "content_must_contain": [ask_prompt],
                    "artifact_refs": [REQUEST_GRAMMAR],
                    "receipt_expect": {},
                    "need_expect": {"slot": CONVERSATION_SLOT},
                },
            }
        )

    # The round trip: the same ask, then a registered value, ending solved.
    # The two replies are the first and fifth entries of the slot's closed
    # vocabulary as `request_grammar.SLOT_VALUES` orders it — positions, not
    # a taste in colours, so the pair moves with the table if it is edited
    # and neither task can drift onto the same value as the other. Index 4
    # rather than 1 because entries 1 and 2 ("gold", "golden") are a prefix
    # pair, and a resume task is a weaker test when its expected content is
    # a prefix of another registered value.
    for slug, utterance, _value in UNREGISTERED_UTTERANCES[:2]:
        reply = registered[0] if slug == UNREGISTERED_UTTERANCES[0][0] else registered[4]
        tasks.append(
            {
                "task_id": f"clarification_due/resume/{slug}",
                "kind": "clarification_due",
                "profile": "corollary/conversation",
                "phase": "resume",
                "resume_of": f"clarification_due/ask/{slug}",
                "turns": [
                    {
                        "role": "user",
                        "content": utterance,
                        "expected_status": "waiting",
                    },
                    {"role": "user", "content": reply},
                ],
                "expected": {
                    "outcome": "answer",
                    "check": "verdict",
                    "status_expect": "solved",
                    "content_must_contain": [reply],
                    "artifact_refs": [REQUEST_GRAMMAR],
                    "receipt_expect": {
                        "binding": {"slot": CONVERSATION_SLOT, "value": reply},
                        "derivation": "user-frame",
                    },
                },
            }
        )

    # The kernel's own ambiguity, taken only from lines a committed test
    # pins as ambiguous. Inventing an ambiguous query here would be guessing
    # at the resolver's disposition, which is the engine grading itself.
    for slug, first, narrow, bound in (
        (
            "double_factorial",
            "double factorial",
            "narrow word recursive",
            "programming.dfactorial.recursive",
        ),
        (
            "entropy_in_thermodynamics",
            "entropy in thermodynamics",
            "narrow discipline machine_learning",
            "ml.objective.token_cross_entropy_loss",
        ),
    ):
        record = statement_record(bound)
        tasks.append(
            {
                "task_id": f"clarification_due/narrow/{slug}",
                "kind": "clarification_due",
                "profile": "corollary/kernel",
                "phase": "resume",
                "turns": [
                    {
                        "role": "user",
                        "content": first,
                        "expected_status": "waiting",
                    },
                    {"role": "user", "content": narrow},
                ],
                "expected": {
                    "outcome": "answer",
                    "check": "receipt",
                    "status_expect": "found",
                    "content_must_contain": [
                        record["title"],
                        record["meaning"],
                    ],
                    "artifact_refs": [
                        PINNED_LINE_TESTS,
                        f"{record['corpus_path']}#{bound}",
                    ],
                    "receipt_expect": {
                        "statement_id": bound,
                        "corpus_path": record["corpus_path"],
                        "node_sha256": record["node_sha256"],
                    },
                },
            }
        )
    return tasks


def statement_record(statement_id: str) -> dict:
    for rel, corpus in corpus_files():
        for node in corpus_nodes(rel):
            if node.get("statement_id") == statement_id:
                return {
                    "statement_id": statement_id,
                    "corpus_path": rel,
                    "corpus_id": corpus,
                    "title": str(node.get("title", "")),
                    "meaning": str(
                        (node.get("semantic_interpretation") or {}).get(
                            "statement_meaning", ""
                        )
                    ),
                    "node_sha256": node_sha256(node),
                }
    raise BuildRefused(f"{statement_id} is not a committed statement")


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------


def frozen_labels() -> dict[str, str]:
    """Every rendering label this book quotes, checked against its module."""

    cache: dict[str, str] = {}

    def label(rel: str, text: str) -> str:
        return require_label(rel, text, cache)

    return {
        "expression": label("scripts/evaluate.py", "expression : "),
        "given": label("scripts/evaluate.py", "given      : "),
        "exact": label("scripts/evaluate.py", "exact      : "),
        "relation": label("scripts/evaluate.py", "relation   : "),
        "left": label("scripts/evaluate.py", "left       : "),
        "right": label("scripts/evaluate.py", "right      : "),
        "holds": label("scripts/evaluate.py", "holds      : "),
        "agent": label("scripts/belief.py", "agent      : "),
        "subject": label("scripts/belief.py", "subject    : "),
        "believes": label("scripts/belief.py", "believes   : "),
        "world_says": label("scripts/belief.py", "world says : "),
        "divergence": label(
            "scripts/belief.py",
            "divergence : belief and world differ; the question asked ",
        )
        + "for the belief",
        "level": label("scripts/harness.py", "level      : "),
        "member": label("scripts/harness.py", "member     : "),
        "ledger": label("scripts/harness.py", "ledger     : "),
        "closure_line": label("scripts/closure_query.py", "closure: "),
        "world_id": label("scripts/closure_query.py", "world_id: "),
        "horizon": label("scripts/closure_query.py", "horizon: "),
        "visited_states": label("scripts/closure_query.py", "visited_states: "),
        "closure_digest": label("scripts/closure_query.py", "closure_digest: "),
        "adapter_id": label("scripts/closure_query.py", "adapter_id: "),
        "target_digest": label("scripts/closure_query.py", "target_digest: "),
        "outcome": label("scripts/closure_query.py", "outcome: "),
        "shortest_route": label("scripts/closure_query.py", "shortest_route: "),
        "need_prompt": label(
            "scripts/retrieval.py", "What value should fill "
        ),
    }


TARGET_COUNTS = {
    "corpus_definition": 30,
    "evaluations": 12,
    "relations": 14,
    "twin_lookup": 12,
    "belief_query": 14,
}


def twin_selection(pool: list[dict]) -> list[dict]:
    """The base twin set: the strongest groups, plus one of every level.

    Taking the pool's head alone fills the kind entirely with `typed` pairs,
    and the four weaker levels — the ones whose membership a reader has most
    reason to doubt — go unmeasured. So the head is followed by the first
    group of each remaining level in the same (size, index) order. Every
    chosen id is already verified to appear at no stronger level
    (:func:`twin_pool`), which is what makes a `shape` task a test of the
    strongest-level selection rather than an accident.
    """

    selected = list(pool[: TARGET_COUNTS["twin_lookup"]])
    taken = {(record["level"], record["group_index"]) for record in selected}
    for level in TWIN_LEDGER_FIELDS:
        if any(record["level"] == level for record in selected):
            continue
        for record in pool:
            key = (record["level"], record["group_index"])
            if record["level"] == level and key not in taken:
                selected.append(record)
                taken.add(key)
                break
        else:
            raise BuildRefused(
                f"the ledger offers no unambiguous {level} group; the level "
                "coverage this book claims is not available"
            )
    return selected


def assemble() -> list[dict]:
    labels = frozen_labels()

    definitions = corpus_definition_pool()
    twins = twin_pool()
    selected_twins = twin_selection(twins)

    tasks: list[dict] = []
    tasks += [
        corpus_definition_task(record)
        for record in definitions[: TARGET_COUNTS["corpus_definition"]]
    ]
    evaluations = TARGET_COUNTS["evaluations"]
    tasks += [
        exact_value_task(evaluation_spec(i), labels) for i in range(evaluations)
    ]
    tasks += [
        exact_value_task(relation_spec(i), labels)
        for i in range(TARGET_COUNTS["relations"])
    ]
    tasks += [twin_task(record, labels) for record in selected_twins]
    tasks += closure_tasks(labels)
    tasks += [
        belief_task(row, labels)
        for row in BELIEF_ROWS[: TARGET_COUNTS["belief_query"]]
    ]
    tasks += refusal_tasks()
    tasks += clarification_tasks(labels)

    for task in tasks:
        task["half"] = half_of(task["task_id"])

    # The half rule is frozen, so a kind short of half B is topped up with
    # MORE tasks of that kind — never by reassigning a half.
    extra_definitions = TARGET_COUNTS["corpus_definition"]
    extra_evaluations = evaluations
    # The base twin set is no longer a prefix of the pool (level coverage
    # pulls records from further down), so top-up walks the pool and skips
    # whatever the base already took rather than counting from an offset.
    used_twins = {
        (record["level"], record["group_index"]) for record in selected_twins
    }
    remaining_twins = [
        record
        for record in twins
        if (record["level"], record["group_index"]) not in used_twins
    ]
    while True:
        short = [
            kind
            for kind in ANSWERABLE_KINDS
            if kind not in POPULATION_CAPPED_KINDS
            and sum(
                1 for t in tasks if t["kind"] == kind and t["half"] == "B"
            )
            < MIN_HALF_B_PER_ANSWERABLE_KIND
        ]
        if not short:
            break
        kind = short[0]
        if kind == "corpus_definition":
            if extra_definitions >= len(definitions):
                raise BuildRefused(
                    f"corpus_definition cannot reach "
                    f"{MIN_HALF_B_PER_ANSWERABLE_KIND} half-B tasks: the "
                    "eligible pool is exhausted"
                )
            new = corpus_definition_task(definitions[extra_definitions])
            extra_definitions += 1
        elif kind == "twin_lookup":
            if not remaining_twins:
                raise BuildRefused(
                    f"twin_lookup cannot reach "
                    f"{MIN_HALF_B_PER_ANSWERABLE_KIND} half-B tasks: the "
                    "eligible ledger-group pool is exhausted"
                )
            new = twin_task(remaining_twins.pop(0), labels)
        elif kind == "exact_value":
            new = exact_value_task(evaluation_spec(extra_evaluations), labels)
            extra_evaluations += 1
        elif kind == "belief_query":
            raise BuildRefused(
                f"belief_query cannot reach {MIN_HALF_B_PER_ANSWERABLE_KIND} "
                "half-B tasks without new narration rows; add them to "
                "BELIEF_ROWS deliberately"
            )
        else:
            raise BuildRefused(
                f"{kind} is short of {MIN_HALF_B_PER_ANSWERABLE_KIND} half-B "
                "tasks and its pool is the committed artifact set, which this "
                "builder may not extend"
            )
        new["half"] = half_of(new["task_id"])
        tasks.append(new)

    tasks.sort(key=lambda t: t["task_id"])
    return tasks


#: Where each kind's task ids come from, which decides what a miss means.
#: An artifact-derived task's id was read out of a committed file, so the
#: engine and the book are looking at the same object and a disagreement is
#: a real disagreement. An author-authored task's id was written here, so a
#: miss can also mean this file wrote a line the registered grammar never
#: claimed — a different finding, and the reader is owed the distinction.
ID_PROVENANCE = {
    "corpus_definition": "artifact-derived",
    "twin_lookup": "artifact-derived",
    "closure_reachability": "artifact-derived",
    "exact_value": "author-authored",
    "belief_query": "author-authored",
    "refusal_due": "author-authored",
    "clarification_due": "author-authored",
}


def count_book(tasks: list[dict]) -> dict:
    kinds = sorted({t["kind"] for t in tasks})
    # `answerable` is the T3/T5 population: the five all-answer kinds only.
    # `clarification_due`'s four resume tasks end in an answer but the kind
    # is gated by T5's 100% WAITING leg, not by the per-kind 80% floor, and
    # counting them here would let a resume task pad the floor that governs
    # a kind it is not in.
    answerable = [
        t
        for t in tasks
        if t["expected"]["outcome"] == "answer"
        and t["kind"] in ANSWERABLE_KINDS
    ]
    unconditional = [
        t for t in answerable if t["kind"] not in CONDITIONAL_KINDS
    ]

    def halves(rows):
        return {
            "A": sum(1 for t in rows if t["half"] == "A"),
            "B": sum(1 for t in rows if t["half"] == "B"),
        }

    return {
        "total": len(tasks),
        "by_half": halves(tasks),
        "by_kind": {k: sum(1 for t in tasks if t["kind"] == k) for k in kinds},
        "by_kind_half": {
            k: halves([t for t in tasks if t["kind"] == k]) for k in kinds
        },
        "by_outcome": {
            outcome: sum(
                1 for t in tasks if t["expected"]["outcome"] == outcome
            )
            for outcome in ("answer", "ask", "refuse")
        },
        "answerable_total": len(answerable),
        "answerable_by_half": halves(answerable),
        # Keyed on the answerable kinds alone. A zero row for a kind that is
        # graded by a 100% gate rather than by the per-kind floor would read
        # as "this kind answered nothing", which is not what it means.
        "answerable_by_kind": {
            k: sum(1 for t in answerable if t["kind"] == k)
            for k in sorted(ANSWERABLE_KINDS)
        },
        "answerable_without_conditional_kinds": len(unconditional),
        # Counted apart, deliberately: these end in an answer but belong to
        # a kind T5 grades by its WAITING leg.
        "clarification_answer_tasks": sum(
            1
            for t in tasks
            if t["kind"] == "clarification_due"
            and t["expected"]["outcome"] == "answer"
        ),
        # The clarification leg's denominator, stated so it is not rederived.
        "waiting_marked_turns": sum(
            1
            for t in tasks
            for turn in t["turns"]
            if turn.get("expected_status") == "waiting"
        ),
        "false_belief_tasks": sum(1 for t in tasks if t.get("false_belief")),
        "id_provenance": {kind: ID_PROVENANCE[kind] for kind in kinds},
        "half_b_floor_per_answerable_kind": MIN_HALF_B_PER_ANSWERABLE_KIND,
        # A kind whose population IS the committed artifact supply keeps the
        # half-B count that supply yields. Recorded, not padded: padding is
        # the same target asked twice, which measures nothing and inflates a
        # denominator T5 reads.
        "population_capped": {
            kind: True for kind in sorted(POPULATION_CAPPED_KINDS)
        },
    }


def validate(tasks: list[dict], counts: dict) -> None:
    if counts["total"] < MIN_TASKS:
        raise BuildRefused(
            f"{counts['total']} tasks is below T3's floor of {MIN_TASKS}"
        )
    if counts["answerable_total"] < MIN_ANSWERABLE:
        raise BuildRefused(
            f"{counts['answerable_total']} answerable tasks is below T3's "
            f"stop condition of {MIN_ANSWERABLE}"
        )
    if counts["answerable_without_conditional_kinds"] < MIN_ANSWERABLE:
        raise BuildRefused(
            "dropping the conditional kinds would take the book below "
            f"{MIN_ANSWERABLE} answerable tasks"
        )
    for kind in ANSWERABLE_KINDS:
        in_b = counts["by_kind_half"].get(kind, {}).get("B", 0)
        if kind in POPULATION_CAPPED_KINDS:
            # The exception, and its own floor: a capped kind still has to be
            # measurable in half B at all. Zero would mean the kind cannot be
            # scored there, which is a drop, not a cap.
            if in_b < 1:
                raise BuildRefused(
                    f"{kind} is population-capped and has no half-B task; a "
                    "kind that cannot be scored in B is dropped, not capped"
                )
            continue
        if in_b < MIN_HALF_B_PER_ANSWERABLE_KIND:
            raise BuildRefused(
                f"{kind} has {in_b} half-B task(s); every answerable kind "
                f"needs {MIN_HALF_B_PER_ANSWERABLE_KIND}"
            )

    # The scoring rules make a claim about the tasks; it has to be true.
    for task in tasks:
        if task["kind"] != "clarification_due":
            continue
        if not any(
            turn.get("expected_status") == "waiting" for turn in task["turns"]
        ):
            raise BuildRefused(
                f"{task['task_id']!r} is a clarification task with no turn "
                "marked WAITING; T5's clarification leg is graded per marked "
                "turn and would silently skip it"
            )
        if task["profile"] == "corollary/conversation":
            waiting_first = task["turns"][0].get("expected_status") == "waiting"
            if waiting_first and not (
                task["expected"].get("need_expect")
                or task.get("phase") == "resume"
            ):
                raise BuildRefused(
                    f"{task['task_id']!r} waits on the conversation profile "
                    "but names no need record for the leg to match"
                )

    seen_ids: set[str] = set()
    seen_turns: set[str] = set()
    for task in tasks:
        task_id = task["task_id"]
        if task_id in seen_ids:
            raise BuildRefused(f"duplicate task_id {task_id!r}")
        seen_ids.add(task_id)
        signature = canonical_json(
            [[turn["role"], turn["content"]] for turn in task["turns"]]
        )
        if signature in seen_turns:
            raise BuildRefused(
                f"{task_id!r} repeats another task's turns; a half-B task "
                "whose content also sits in half A is not sealed"
            )
        seen_turns.add(signature)
        if task["half"] != half_of(task_id):
            raise BuildRefused(f"{task_id!r} carries the wrong half")

        for ref in task["expected"]["artifact_refs"]:
            path, _, fragment = ref.partition("#")
            if not (REPO / path).exists():
                raise BuildRefused(f"{task_id!r} cites missing artifact {path!r}")
            if fragment and fragment not in {
                node.get("statement_id") for node in corpus_nodes(path)
            }:
                raise BuildRefused(
                    f"{task_id!r} cites {fragment!r}, which {path} does not hold"
                )

    verify_content_against_artifacts(tasks)


def verify_content_against_artifacts(tasks: list[dict]) -> None:
    """Check the quoted strings of the two kinds that quote an artifact.

    Scope, stated rather than implied: this covers `twin_lookup` (member ids
    against the cited ledger group) and every task carrying an artifact ref
    with a `#statement_id` fragment — the definition tasks and the kernel
    ambiguity tasks, whose required strings are the node's own `title` and
    `statement_meaning`. It does NOT cover `exact_value`, `belief_query`,
    `refusal_due`, or the conversation clarification tasks: those quote
    computed values, session derivations, or minted prompts, which are not
    in any committed artifact and are checked elsewhere (the arithmetic by
    recomputation, the labels by :func:`require_label`).
    """

    ledger = read_json(TWIN_LEDGER_PATH)
    for task in tasks:
        expected = task["expected"]
        if task["kind"] == "twin_lookup":
            group = ledger[task["ledger_group"]["field"]][
                task["ledger_group"]["group_index"]
            ]
            members = {member["statement_id"] for member in group["members"]}
            for text in expected["content_must_contain"]:
                if text not in members:
                    raise BuildRefused(
                        f"{task['task_id']!r} quotes {text!r}, which the cited "
                        "ledger group does not list"
                    )
            continue
        refs = [r for r in expected["artifact_refs"] if "#" in r]
        if not refs:
            continue
        path, _, fragment = refs[0].partition("#")
        node = next(
            n for n in corpus_nodes(path) if n.get("statement_id") == fragment
        )
        quotable = {
            str(node.get("title", "")),
            str(
                (node.get("semantic_interpretation") or {}).get(
                    "statement_meaning", ""
                )
            ),
        }
        for text in expected["content_must_contain"]:
            if text not in quotable:
                raise BuildRefused(
                    f"{task['task_id']!r} quotes text absent from {path}#{fragment}"
                )


#: Printed by :func:`assert_clean_imports` so a parent process can see that
#: the guard actually ran, rather than inferring it from a zero exit code
#: that a build skipping the guard would also produce.
CLEAN_IMPORTS_LINE = "engine-clean imports: verified in this process"


def assert_clean_imports() -> None:
    """No engine module may be in this interpreter. Checked, not promised.

    The guard has to run in the process that did the building, and it is
    only meaningful there: an in-process assertion inside a test suite says
    nothing, because a sibling test module that imported `harness` first
    would fail it while this builder stayed innocent. So the check lives
    here, in the child, and the parent reads the exit code and the line
    below.
    """

    leaked = sorted(set(FORBIDDEN_MODULES) & set(sys.modules))
    if leaked:
        raise BuildRefused(
            "an engine module was imported while building the answer key: "
            f"{leaked}. The receipt must exist before the question does, and "
            "a book computed by the system under test grades nothing."
        )


def build() -> dict:
    tasks = assemble()
    counts = count_book(tasks)
    validate(tasks, counts)
    assert_clean_imports()

    return {
        "schema": SCHEMA,
        "built_by": BUILT_BY,
        "seal": SEAL,
        "scoring_rules": SCORING_RULES,
        "rendering_module_digests": {
            rel: canonical_lf_sha256(rel) for rel in RENDERING_MODULES
        },
        "counts": counts,
        "tasks": tasks,
    }


def serialize(book: dict) -> str:
    return json.dumps(book, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(REPO / "experiments" / "throughput_tasks.json"),
        help="where to write the book (default: the committed path)",
    )
    parser.add_argument(
        "--assert-clean-imports",
        action="store_true",
        help=(
            "re-run the engine-import guard after the build and print "
            f"{CLEAN_IMPORTS_LINE!r}, so a parent process can see that this "
            "interpreter stayed clean rather than trust that it did"
        ),
    )
    args = parser.parse_args(argv)

    book = build()
    if args.assert_clean_imports:
        assert_clean_imports()
        print(CLEAN_IMPORTS_LINE)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(serialize(book), encoding="utf-8", newline="\n")

    counts = book["counts"]
    print(f"{counts['total']} tasks -> {out}")
    for kind in sorted(counts["by_kind"]):
        half = counts["by_kind_half"][kind]
        print(
            f"  {kind:22s} {counts['by_kind'][kind]:4d}  "
            f"A={half['A']:3d}  B={half['B']:3d}"
        )
    print(
        f"  answerable {counts['answerable_total']} "
        f"(A={counts['answerable_by_half']['A']}, "
        f"B={counts['answerable_by_half']['B']}); "
        f"without conditional kinds "
        f"{counts['answerable_without_conditional_kinds']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
