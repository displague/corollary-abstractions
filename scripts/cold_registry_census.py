#!/usr/bin/env python3
"""CR-P0 — the receipt-kind registry census, run as a rule and not as a list.

`docs/DESIGN-cold-receipt.md` §5 registers this census as a *construction
prerequisite*: it lands before any COLD RECEIPT harness code exists, and it
publishes whichever way it reads. Its job is not to state how many receipt
kinds this program emits — the design deliberately declines to predict that —
but to answer a prior question the design makes the gate on B1:

    can this program enumerate its own evidence by running a rule, or only
    by a maintainer reading its code?

Everything below is that rule. The rule is stated once, in
``ENUMERATION_RULE``, in machine-readable form, and the artifact carries it
so a reader can re-run the enumeration and compare rather than trust the
output. A hand-written kind list presented as a registry is the construction
defect ``docs/ROADMAP-v0.21.md`` §4.0(3) exists to catch, so there is no kind
list in this file — only predicates.

THE RULE, in prose (the machine-readable spelling is ``ENUMERATION_RULE``)
--------------------------------------------------------------------------

*Universe.* Every ``*.py`` under ``scripts/`` — precisely the tree the COLD
RECEIPT harness renames away — plus the committed artifact roots
``reports/``, ``experiments/``, ``prover/``, ``staging/`` (``*.json`` /
``*.jsonl``, recursive). ``data/``, ``data_holdout/`` and ``data_sources/``
are outside the universe by the rule and not by a judgement: they are the
program's *inputs*, and a census of emitted evidence that counted its own
corpora would be counting what the program was handed rather than what it
wrote.

*Marking.* A mapping display in the source is **receipt-marked** when at
least one of three decidable predicates holds:

- ``RM-A`` (self-tagging): it carries a ``schema``/``kind``/``type`` key whose
  string value — literal, or a module-level string constant resolved by name —
  matches ``receipt|certificate``.
- ``RM-B`` (name-bound): it is the direct value of a ``return`` from, or an
  assignment to, a name matching ``(^|_)(receipt|cert|certificate)s?($|_)``.
- ``RM-C`` (member): it is the value of a key drawn from the **exact** set
  {receipt, receipts, cert, certificate, certificates}. The set is exact
  rather than a substring match on purpose: ``receipt_expect``,
  ``receipts_committed``, ``correct_with_receipt`` and ``receipt_sha256`` are
  facts *about* receipts, and a substring rule that swept them in would be
  counting the program's prose about its evidence as evidence.

A fourth predicate reaches evidence built by a class rather than by a mapping
display, which the three above cannot see:

- ``RM-D`` (named write boundary): a call whose callee name matches
  ``(^|_)(write|emit|record)_?(receipt|verdict|certificate|cert)s?($|_)`` —
  the program's own name for the write says it is writing evidence. This is
  how ``external_verifier._write_verdict`` and
  ``write_stage._write_receipt_atomic`` enter a census that would otherwise
  see only ``dataclass.as_dict()``.

*Kind formation.* ``RM-A`` sites take the tag as ``kind_id``. ``RM-C`` sites
whose value is a call resolve to the callee's kind, so a route that merely
attaches a receipt built elsewhere does not mint a second kind. Everything
else takes ``<module>:<enclosing symbol>``.

*Exclusions.* Every exclusion is a rule with an id, and every firing is
recorded in ``excluded[]`` with the path and line range the rule computed.
The register is reproducible by re-running this script; a maintainer having
known about an exclusion is never what makes it hold.

- ``X1`` vacuous-literal: every receipt-marked mapping of the candidate is the
  empty display ``{}``. This is the exclusion ``DESIGN-cold-receipt.md`` §5
  seeds with ``scripts/dump_server.py`` — a deliberately empty receipt beside
  a ``"found"`` status, committed as a voiding control for the throughput
  metric. The rule reaches it without knowing that.
- ``X2`` non-mapping member: an ``RM-C``-only candidate whose key's value is
  not a mapping-producing expression (a non-empty ``dict`` display, or a call
  to a receipt-named symbol). ``"receipt": str(path)`` names a file; it is not
  one.

*Route resolution.* ``route_id`` comes from the guards that dominate the site
— comparisons and memberships against a variable named ``route`` — filtered
against ``serve_chat.LINE_GRAMMAR``'s own route vocabulary, which this script
extracts from the source rather than restating. A site under no route guard
takes its writer symbol as its route: the writer is the route.

*Declared recheck procedure.* Derived from the kind's committed instances,
never from a docstring:

- ``raw_checker_invocation`` when a committed instance's artifact carries a
  **self-contained** recheck descriptor — a digest of a checker's own bytes
  (``*binary_sha256``), or a ``recheck_command`` that does **not** name the
  program tree. A ``recheck_command`` reading ``python scripts/…`` describes
  a program replay wearing a descriptor's clothes, and the rule says so.
- ``program_replay`` when instances exist but carry no such descriptor.
- ``none`` when the rule finds no committed instance at all.

The declaration is CR-P0's; ``DESIGN-cold-receipt.md`` §4 gives the harness's
*executed* procedure the last word, and records a disagreement as a census
miss under B10 rather than letting either side quietly win.

*Instance resolution*, three sub-rules, each recorded with the instances it
found:

- ``I1`` tag: an artifact mapping carrying the kind's tag.
- ``I2`` key set: an artifact mapping whose key set is **exactly** one of the
  site's literal key sets. Structural equality is the whole test — no path
  convention, no filename guess.
- ``I3`` destination: for ``RM-D`` kinds **only**, a module-level string
  constant in the writer's module that resolves to an existing **directory**
  under an artifact root. Scoped to ``RM-D`` because that is the case I1 and
  I2 cannot reach — a payload that is a class, not a mapping display — and
  restricted to directories because a file-valued constant in a module is as
  often an input as a destination. It is what tells the census that
  ``write_stage``'s two receipt kinds have **zero** committed instances
  (``staging/*.json`` is git-ignored on purpose) rather than leaving them
  unreached and unexplained.

*Program-defined canonicalization.* §11 asks the census to distinguish a kind
that needs the program to **adjudicate** from one that needs it only to
**serialize**. The test is decidable: the site's enclosing symbol calls a
function whose name matches ``canonical``. Such kinds carry
``canonicalization_is_program_defined``, which is a recorded reason and not a
verdict.

*Recall probes, two of them.* The rule's own recall is measured rather than
asserted, on **both** sides:

- *site side*: a deliberately wider net — substring name matching, no
  exact-key restriction — is run beside the rule, and the sites it reaches
  that the rule does not are published as ``recall_probe.uncovered_sites``.
- *instance side* (**amendment 2**): ``I2``'s exact key-set match is brittle
  in a way the first run did not price. A site whose mapping gains one
  conditional key matches nothing, and the census then reads ``none`` for a
  kind with thousands of committed instances. ``I2b`` runs a **proper
  superset** match beside the exact one, and both counts are published per
  kind. The exact rule stays the rule; the superset count is what makes its
  brittleness a number.

Every uncovered site and every superset-only instance is a candidate census
miss under B10, computed rather than remembered.

Usage
-----

    python scripts/cold_registry_census.py --out experiments/cold_registry_census.json
    python scripts/cold_registry_census.py --check experiments/cold_registry_census.json
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from importlib.metadata import version
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from report_provenance import provenance_block, repo_relative  # noqa: E402

SCHEMA_TAG = "cold-registry-census/1"

# --------------------------------------------------------------------------
# The rule, machine-readable. The artifact carries this verbatim.
# --------------------------------------------------------------------------

PROGRAM_TREE_GLOB = "scripts/**/*.py"
ARTIFACT_ROOTS = ("reports", "experiments", "prover", "staging")
ARTIFACT_SUFFIXES = (".json", ".jsonl")
UNIVERSE_EXCLUDED_ROOTS = ("data", "data_holdout", "data_sources")

TAG_KEYS = ("schema", "kind", "type")
TAG_VALUE_RE = r"(?i)receipt|certificate"
BINDING_NAME_RE = r"(?i)(^|_)(receipt|cert|certificate)s?($|_)"
MEMBER_KEY_EXACT = ("receipt", "receipts", "cert", "certificate", "certificates")
WRITE_BOUNDARY_RE = (
    r"(?i)(^|_)(write|emit|record)_?(receipt|verdict|certificate|cert)s?($|_)"
)

RECHECK_DESCRIPTOR_FIELDS = ("recheck_command",)
RECHECK_BINARY_PIN_RE = r"(?i)binary_sha256$"

# The wider net the recall probe runs beside the rule, to measure what the
# rule's exactness costs. Never used to admit a kind.
RECALL_SUBSTRING_RE = r"(?i)receipt|certificate|verdict|journal"

ENUMERATION_RULE = {
    "rule_id": "CR-P0/1",
    "universe": {
        "program_tree_glob": PROGRAM_TREE_GLOB,
        "artifact_roots": list(ARTIFACT_ROOTS),
        "artifact_suffixes": list(ARTIFACT_SUFFIXES),
        "roots_outside_the_universe": list(UNIVERSE_EXCLUDED_ROOTS),
        "why_those_roots_are_outside": (
            "they are the program's inputs; a census of emitted evidence that "
            "counted its own corpora would be counting what the program was "
            "handed rather than what it wrote"
        ),
    },
    "marking_predicates": {
        "RM-A": {
            "name": "self-tagging",
            "test": (
                "an ast.Dict carrying one of TAG_KEYS whose string value "
                "(literal, or a module-level string constant resolved by name) "
                "matches TAG_VALUE_RE"
            ),
            "tag_keys": list(TAG_KEYS),
            "tag_value_regex": TAG_VALUE_RE,
        },
        "RM-B": {
            "name": "name-bound",
            "test": (
                "an ast.Dict that is the direct value of a return from, or an "
                "assignment to, a name matching BINDING_NAME_RE"
            ),
            "binding_name_regex": BINDING_NAME_RE,
        },
        "RM-C": {
            "name": "member",
            "test": (
                "an ast.Dict that is the value of a key drawn from the EXACT "
                "set MEMBER_KEY_EXACT"
            ),
            "member_keys_exact": list(MEMBER_KEY_EXACT),
            "why_exact": (
                "a substring rule would sweep in receipt_expect, "
                "receipts_committed, correct_with_receipt and receipt_sha256 — "
                "facts about receipts rather than receipts"
            ),
        },
        "RM-D": {
            "name": "named write boundary",
            "test": (
                "an ast.Call whose callee name matches WRITE_BOUNDARY_RE: the "
                "program's own name for the write says it is writing evidence"
            ),
            "write_boundary_regex": WRITE_BOUNDARY_RE,
            "why": (
                "RM-A/B/C see mapping displays only; a kind whose payload is a "
                "dataclass rendered by as_dict() is invisible to them"
            ),
        },
    },
    "kind_formation": [
        "RM-A: kind_id is the tag string",
        "RM-C whose value is a Call: kind_id is the callee's kind",
        "otherwise: kind_id is '<module>:<enclosing symbol>'",
    ],
    "exclusion_rules": {
        "X1": {
            "name": "vacuous-literal",
            "test": (
                "every receipt-marked mapping of the candidate is the empty "
                "display {}"
            ),
            "reason_template": (
                "committed voiding control or empty shape: every emitted "
                "mapping for this candidate is the empty display, so there is "
                "no content any procedure could re-check"
            ),
        },
        "X2": {
            "name": "non-mapping-member",
            "test": (
                "an RM-C-only candidate whose member value is neither a "
                "non-empty dict display nor a call to a symbol matching "
                "BINDING_NAME_RE"
            ),
            "reason_template": (
                "the receipt-named key's value is not a mapping-producing "
                "expression: the site names or measures a receipt rather than "
                "constructing one"
            ),
        },
    },
    "route_resolution": (
        "string literals compared against, or tested for membership by, a "
        "variable named 'route' in an ast.If that dominates the site, "
        "intersected with the route vocabulary extracted from "
        "serve_chat.LINE_GRAMMAR; a site under no route guard takes "
        "'<module>.<symbol>' — the writer is the route"
    ),
    "declared_recheck_procedure": {
        "raw_checker_invocation": (
            "the artifact holding a committed instance carries a SELF-CONTAINED "
            "recheck descriptor: a digest of a checker's own bytes matching "
            "RECHECK_BINARY_PIN_RE, or a field in RECHECK_DESCRIPTOR_FIELDS "
            "whose value does not name the program tree"
        ),
        "program_replay": "committed instances exist, carrying no such descriptor",
        "none": "the rule finds no committed instance",
        "descriptor_fields": list(RECHECK_DESCRIPTOR_FIELDS),
        "binary_pin_regex": RECHECK_BINARY_PIN_RE,
        "program_tree_reference_disqualifies": True,
        "why_it_disqualifies": (
            "a recheck_command reading 'python scripts/…' describes a program "
            "replay wearing a descriptor's clothes"
        ),
        "authority": (
            "DESIGN-cold-receipt.md §4 gives the harness's EXECUTED procedure "
            "the last word; a disagreement with this declaration is a census "
            "miss under B10"
        ),
    },
    "instance_resolution": {
        "I1": "a mapping in a committed artifact carrying the kind's tag",
        "I2": (
            "a mapping whose key set is exactly one of the site's literal key "
            "sets"
        ),
        "I3": (
            "RM-D kinds only: a module-level string constant in the writer's "
            "module resolving to an existing DIRECTORY under an artifact root"
        ),
        "I3_scope_note": (
            "scoped to RM-D because that is the case I1/I2 cannot reach, and "
            "restricted to directories because a file-valued module constant is "
            "as often an input as a destination"
        ),
    },
    "program_defined_canonicalization": {
        "test": (
            "the site's enclosing symbol calls a function whose name matches "
            "'canonical'"
        ),
        "why": (
            "DESIGN-cold-receipt.md §11: the census must distinguish a kind "
            "that needs the program to ADJUDICATE from one that needs it only "
            "to SERIALIZE. Recorded as a reason, never as a verdict."
        ),
    },
    "scramble_rule": {
        "type": "permute_instances_within_artifact",
        "statement": (
            "B6's per-kind rule, committed here: reassign a kind's committed "
            "instances across that kind's own records by a seeded permutation, "
            "preserving every file and every digest field's shape"
        ),
        "seed_derivation": "int(sha256(kind_id)[:8], 16) — derived, not chosen",
    },
    "recall_probe": {
        "substring_regex": RECALL_SUBSTRING_RE,
        "purpose": (
            "measure what the rule's exactness costs: sites a deliberately "
            "wider net reaches that the rule does not are published as "
            "candidate census misses under B10, computed rather than remembered"
        ),
    },
}

_TAG_VALUE = re.compile(TAG_VALUE_RE)
_BINDING_NAME = re.compile(BINDING_NAME_RE)
_WRITE_BOUNDARY = re.compile(WRITE_BOUNDARY_RE)
_RECALL_SUBSTRING = re.compile(RECALL_SUBSTRING_RE)


# --------------------------------------------------------------------------
# Source side: receipt-marked mapping sites
# --------------------------------------------------------------------------


def _string_keys(node: ast.Dict) -> list[str]:
    return [
        k.value
        for k in node.keys
        if isinstance(k, ast.Constant) and isinstance(k.value, str)
    ]


def _module_string_constants(tree: ast.Module) -> dict[str, str]:
    """Module-level ``NAME = "literal"`` bindings, so RM-A can resolve a tag
    written as a constant (``RECEIPT_SCHEMA_TAG``) rather than inline."""

    out: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            target, value = node.target, node.value
        else:
            continue
        if (
            isinstance(target, ast.Name)
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
        ):
            out[target.id] = value.value
    return out


def _is_mapping_producing(value: ast.expr) -> tuple[bool, str | None]:
    """RM-C's admission test, and the callee when it resolves to one."""

    if isinstance(value, ast.Dict):
        return (len(value.keys) > 0, None)
    if isinstance(value, ast.Call):
        func = value.func
        name = None
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        if name and _BINDING_NAME.search(name):
            return (True, name)
        return (False, None)
    return (False, None)


def _route_vocabulary(repo: Path) -> list[str]:
    """Route strings, extracted from ``serve_chat.LINE_GRAMMAR`` by rule.

    The design calls LINE_GRAMMAR the strongest evidence in this tree that a
    registry of this shape can be enumerated and frozen. It is read here as a
    vocabulary, never as a kind list: it enumerates serving routes, and a
    serving route is not a receipt kind.
    """

    path = repo / "scripts" / "serve_chat.py"
    if not path.is_file():
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    routes: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value_node = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            target, value_node = node.target, node.value
        else:
            continue
        if not (isinstance(target, ast.Name) and target.id == "LINE_GRAMMAR"):
            continue
        for element in ast.walk(value_node):
            if not isinstance(element, ast.Dict):
                continue
            for key, value in zip(element.keys, element.values):
                if (
                    isinstance(key, ast.Constant)
                    and key.value == "route"
                    and isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                ):
                    routes.append(value.value)
    return sorted(set(routes))


class _SiteVisitor(ast.NodeVisitor):
    """Walks one module, recording every receipt-marked mapping display."""

    def __init__(self, rel_path: str, constants: dict[str, str]) -> None:
        self.rel_path = rel_path
        self.constants = constants
        self.sites: list[dict[str, Any]] = []
        self._symbols: list[str] = []
        self._guards: list[list[str]] = []
        self._seen: set[int] = set()

    # -- context ---------------------------------------------------------
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._symbols.append(node.name)
        self.generic_visit(node)
        self._symbols.pop()

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._symbols.append(node.name)
        self.generic_visit(node)
        self._symbols.pop()

    def visit_If(self, node: ast.If) -> None:
        routes = _guard_routes(node.test)
        self._guards.append(routes)
        for stmt in node.body:
            self.visit(stmt)
        self._guards.pop()
        for stmt in node.orelse:
            self.visit(stmt)

    # -- marking ---------------------------------------------------------
    def visit_Assign(self, node: ast.Assign) -> None:
        names = []
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.append(target.id)
            elif isinstance(target, ast.Attribute):
                names.append(target.attr)
        self._mark_binding(node.value, names)
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        if node.value is not None and self._symbols:
            self._mark_binding(node.value, [self._symbols[-1]])
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> None:
        self._mark_tag(node)
        self._mark_member(node)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        name = None
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        if name and _WRITE_BOUNDARY.search(name):
            self.sites.append(
                {
                    "file": self.rel_path,
                    "line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                    "symbol": self._symbols[-1] if self._symbols else "<module>",
                    "symbol_path": ".".join(self._symbols) or "<module>",
                    "rule": "RM-D",
                    "keys": [],
                    "key_count": 0,
                    "empty_display": False,
                    "route_guards": sorted(
                        {r for frame in self._guards for r in frame}
                    ),
                    "write_callee": name,
                }
            )
        self.generic_visit(node)

    # -- predicates ------------------------------------------------------
    def _record(self, node: ast.Dict, rule: str, **extra: Any) -> None:
        site = {
            "file": self.rel_path,
            "line": node.lineno,
            "end_line": getattr(node, "end_lineno", node.lineno),
            "symbol": self._symbols[-1] if self._symbols else "<module>",
            "symbol_path": ".".join(self._symbols) or "<module>",
            "rule": rule,
            "keys": _string_keys(node),
            "key_count": len(node.keys),
            "empty_display": len(node.keys) == 0,
            "route_guards": sorted({r for frame in self._guards for r in frame}),
        }
        site.update(extra)
        self.sites.append(site)

    def _mark_tag(self, node: ast.Dict) -> None:
        for key, value in zip(node.keys, node.values):
            if not (isinstance(key, ast.Constant) and key.value in TAG_KEYS):
                continue
            literal: str | None = None
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                literal = value.value
            elif isinstance(value, ast.Name):
                literal = self.constants.get(value.id)
            if literal and _TAG_VALUE.search(literal):
                self._record(node, "RM-A", tag=literal)
                return

    def _mark_binding(self, value: ast.expr, names: Iterable[str]) -> None:
        if not isinstance(value, ast.Dict):
            return
        matched = [n for n in names if _BINDING_NAME.search(n)]
        if matched:
            self._record(value, "RM-B", bound_to=sorted(matched))

    def _mark_member(self, node: ast.Dict) -> None:
        for key, value in zip(node.keys, node.values):
            if not (
                isinstance(key, ast.Constant) and key.value in MEMBER_KEY_EXACT
            ):
                continue
            admitted, callee = _is_mapping_producing(value)
            member_line = getattr(value, "lineno", node.lineno)
            member_end = getattr(value, "end_lineno", member_line)
            self._record(
                node,
                "RM-C",
                member_key=key.value,
                member_admitted=admitted,
                member_callee=callee,
                member_is_empty_display=(
                    isinstance(value, ast.Dict) and len(value.keys) == 0
                ),
                member_keys=(
                    _string_keys(value) if isinstance(value, ast.Dict) else []
                ),
                member_line=member_line,
                member_end_line=member_end,
                member_expr=type(value).__name__,
            )


def _guard_routes(test: ast.expr) -> list[str]:
    """Route literals a guard compares against a variable named ``route``."""

    routes: list[str] = []
    for node in ast.walk(test):
        if not isinstance(node, ast.Compare):
            continue
        left = node.left
        if not (isinstance(left, ast.Name) and left.id.endswith("route")):
            continue
        for comparator in node.comparators:
            if isinstance(comparator, ast.Constant) and isinstance(
                comparator.value, str
            ):
                routes.append(comparator.value)
            elif isinstance(comparator, (ast.Set, ast.List, ast.Tuple)):
                for element in comparator.elts:
                    if isinstance(element, ast.Constant) and isinstance(
                        element.value, str
                    ):
                        routes.append(element.value)
    return sorted(set(routes))


def scan_program_tree(repo: Path) -> list[dict[str, Any]]:
    sites: list[dict[str, Any]] = []
    for path in sorted(repo.glob(PROGRAM_TREE_GLOB)):
        rel = repo_relative(path, repo)
        source = path.read_text(encoding="utf-8", errors="replace")
        try:
            tree = ast.parse(source)
        except SyntaxError:  # pragma: no cover - the tree parses today
            continue
        visitor = _SiteVisitor(rel, _module_string_constants(tree))
        visitor.visit(tree)
        sites.extend(visitor.sites)
    return sites


# --------------------------------------------------------------------------
# Kind formation and exclusion
# --------------------------------------------------------------------------


_CANONICAL_RE = re.compile(r"(?i)canonical")


def _canonicalizing_symbols(repo: Path, rel_path: str) -> set[str]:
    """Symbols whose body calls a function whose name matches ``canonical``.

    §11's distinction, made decidable: a receipt whose digest is taken over a
    program-defined canonicalization is not offline-recheckable even in
    principle without the program.
    """

    path = repo / rel_path
    if not path.is_file():
        return set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:  # pragma: no cover
        return set()
    out: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for inner in ast.walk(node):
            if not isinstance(inner, ast.Call):
                continue
            func = inner.func
            name = (
                func.id
                if isinstance(func, ast.Name)
                else func.attr
                if isinstance(func, ast.Attribute)
                else None
            )
            if name and _CANONICAL_RE.search(name):
                out.add(node.name)
                break
    return out


def _module_of(rel_path: str) -> str:
    return Path(rel_path).stem


def form_kinds(
    sites: list[dict[str, Any]], routes_vocabulary: list[str]
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Group sites into candidate kinds; return (kinds, excluded records)."""

    candidates: dict[str, dict[str, Any]] = {}
    excluded: list[dict[str, Any]] = []

    for site in sites:
        module = _module_of(site["file"])
        if site["rule"] == "RM-A":
            kind_id = site["tag"]
        elif site["rule"] == "RM-C" and site.get("member_callee"):
            kind_id = f"{module}:{site['member_callee']}"
        else:
            kind_id = f"{module}:{site['symbol']}"
        record = candidates.setdefault(
            kind_id,
            {"kind_id": kind_id, "sites": [], "tags": set()},
        )
        record["sites"].append(site)
        if site["rule"] == "RM-A":
            record["tags"].add(site["tag"])

    kinds: dict[str, dict[str, Any]] = {}
    for kind_id, record in sorted(candidates.items()):
        sites_ = record["sites"]
        # X1 — vacuous literal. A candidate every one of whose receipt-marked
        # mappings is the empty display carries no content to re-check.
        shapes = []
        for site in sites_:
            if site["rule"] == "RM-C":
                shapes.append(site.get("member_is_empty_display", False))
            else:
                shapes.append(site["empty_display"])
        if shapes and all(shapes):
            for site in sites_:
                excluded.append(
                    {
                        "rule_id": "X1",
                        "kind_id_candidate": kind_id,
                        "path": site["file"],
                        "line_range": [
                            site.get("member_line", site["line"]),
                            site.get("member_end_line", site["end_line"]),
                        ],
                        "enclosing_line_range": [site["line"], site["end_line"]],
                        "reason": ENUMERATION_RULE["exclusion_rules"]["X1"][
                            "reason_template"
                        ],
                    }
                )
            continue
        # X2 — an RM-C-only candidate whose member value produces no mapping.
        rules = {site["rule"] for site in sites_}
        if rules == {"RM-C"} and not any(
            site.get("member_admitted") for site in sites_
        ):
            for site in sites_:
                excluded.append(
                    {
                        "rule_id": "X2",
                        "kind_id_candidate": kind_id,
                        "path": site["file"],
                        "line_range": [
                            site.get("member_line", site["line"]),
                            site.get("member_end_line", site["end_line"]),
                        ],
                        "enclosing_line_range": [site["line"], site["end_line"]],
                        "member_expression": site.get("member_expr"),
                        "reason": ENUMERATION_RULE["exclusion_rules"]["X2"][
                            "reason_template"
                        ],
                    }
                )
            continue

        emitting: list[dict[str, Any]] = []
        for site in sites_:
            guards = [r for r in site["route_guards"] if r in routes_vocabulary]
            module = _module_of(site["file"])
            if guards:
                for route in guards:
                    emitting.append(
                        {
                            "route_id": route,
                            "writer_file": site["file"],
                            "writer_symbol": site["symbol_path"],
                            "line": site["line"],
                            "route_source": "dominating_guard",
                        }
                    )
            else:
                emitting.append(
                    {
                        "route_id": f"{module}.{site['symbol_path']}",
                        "writer_file": site["file"],
                        "writer_symbol": site["symbol_path"],
                        "line": site["line"],
                        "route_source": "writer_is_the_route",
                    }
                )
        emitting.sort(key=lambda row: (row["writer_file"], row["line"], row["route_id"]))

        # The key set the instance rule matches on: the widest literal shape
        # this kind constructs. A kind whose mapping is assembled dynamically
        # has no literal key set, and the rule says so rather than guessing.
        key_sets = []
        for site in sites_:
            keys = (
                site.get("member_keys")
                if site["rule"] == "RM-C" and site.get("member_keys")
                else site["keys"]
            )
            if keys:
                key_sets.append(sorted(set(keys)))
        widest = max(key_sets, key=len) if key_sets else []

        kinds[kind_id] = {
            "kind_id": kind_id,
            "tags": sorted(record["tags"]),
            "marking_rules": sorted(rules),
            "emitting_routes": emitting,
            "site_key_set": widest,
            "site_key_sets": [list(k) for k in key_sets],
            "sites": [
                {
                    "path": site["file"],
                    "line_range": [site["line"], site["end_line"]],
                    "rule": site["rule"],
                    "symbol": site["symbol_path"],
                    # L4: this site's OWN key set. The union across sites is a
                    # shape no single site ever constructs, and publishing only
                    # the union hides which site the instance rule matches on.
                    "key_set": sorted(
                        set(
                            site.get("member_keys")
                            if site["rule"] == "RM-C" and site.get("member_keys")
                            else site["keys"]
                        )
                    ),
                }
                for site in sites_
            ],
        }
    return kinds, excluded


# --------------------------------------------------------------------------
# Artifact side: committed instances
# --------------------------------------------------------------------------


def _iter_artifacts(repo: Path) -> Iterable[Path]:
    for root in ARTIFACT_ROOTS:
        base = repo / root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix in ARTIFACT_SUFFIXES:
                yield path


def _iter_mappings(value: Any) -> Iterable[dict]:
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _iter_mappings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_mappings(item)


def _load_any(path: Path) -> Any:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".jsonl":
        rows = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _destination_constants(repo: Path, module_rel: str) -> list[str]:
    """I3 — module-level string constants that resolve under an artifact root.

    The only instance rule that reaches a kind whose payload is a class rather
    than a mapping display. It is also what lets the census say that
    ``write_stage``'s two receipt kinds have zero committed instances because
    ``staging/*.json`` is git-ignored on purpose, rather than leaving them
    unreached and unexplained.
    """

    path = repo / module_rel
    if not path.is_file():
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:  # pragma: no cover
        return []
    out: list[str] = []
    for _name, value in _module_string_constants(tree).items():
        candidate = value.strip().replace("\\", "/").lstrip("./")
        if not candidate:
            continue
        head = candidate.split("/", 1)[0]
        if head not in ARTIFACT_ROOTS:
            continue
        if (repo / candidate).is_dir():
            out.append(candidate)
    return sorted(set(out))


def _artifact_descriptors(data: Any) -> set[str]:
    """Recheck-descriptor fields anywhere in one artifact document.

    Document-level rather than mapping-level on purpose: the C-E3 supplement
    pins its checker's own bytes in a ``checker`` block beside the rows, not
    inside each row's receipt, and a mapping-local scan would miss the only
    binary digest in this tree.
    """

    fields: set[str] = set()
    for mapping in _iter_mappings(data):
        for field in mapping:
            text = str(field)
            if text in RECHECK_DESCRIPTOR_FIELDS or re.search(
                RECHECK_BINARY_PIN_RE, text
            ):
                value = mapping[field]
                if text in RECHECK_DESCRIPTOR_FIELDS and isinstance(value, str):
                    root = PROGRAM_TREE_GLOB.split("/", 1)[0] + "/"
                    if root in value.replace("\\", "/"):
                        # A recheck_command naming the program tree describes a
                        # program replay wearing a descriptor's clothes.
                        fields.add(f"{text}(names-the-program-tree)")
                        continue
                fields.add(text)
    return fields


def resolve_instances(
    repo: Path, kinds: dict[str, dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Match committed artifacts to kinds by tag (I1), key set (I2), path (I3)."""

    by_tag: dict[str, list[str]] = {}
    by_keyset: dict[tuple[str, ...], list[str]] = {}
    # I2b's index, anchored on each key set's lexicographically-first key so a
    # superset test is only run against mappings that could possibly match.
    by_anchor: dict[str, list[tuple[str, frozenset]]] = {}
    for kind_id, kind in kinds.items():
        for tag in kind["tags"]:
            by_tag.setdefault(tag, []).append(kind_id)
        for keys in kind["site_key_sets"]:
            if keys:
                by_keyset.setdefault(tuple(sorted(keys)), []).append(kind_id)
                frozen = frozenset(keys)
                by_anchor.setdefault(min(frozen), []).append((kind_id, frozen))

    found: dict[str, dict[str, Any]] = {
        kind_id: {
            "count": 0,
            "superset_count": 0,
            "paths": set(),
            "superset_paths": set(),
            "descriptor_fields": set(),
            "rules": set(),
        }
        for kind_id in kinds
    }

    # I3 first: destinations are a property of the writer, not of the scan.
    destinations: dict[str, set[str]] = {}
    for kind_id, kind in kinds.items():
        dests: set[str] = set()
        if "RM-D" in kind["marking_rules"]:
            modules = {row["writer_file"] for row in kind["emitting_routes"]}
            for module_rel in sorted(modules):
                dests.update(_destination_constants(repo, module_rel))
        destinations[kind_id] = dests

    parsed: dict[str, Any] = {}
    for path in _iter_artifacts(repo):
        data = _load_any(path)
        if data is None:
            continue
        rel = repo_relative(path, repo)
        parsed[rel] = data
        descriptors = _artifact_descriptors(data)
        for mapping in _iter_mappings(data):
            hits: dict[str, str] = {}
            for tag_key in TAG_KEYS:
                tag = mapping.get(tag_key)
                if isinstance(tag, str) and tag in by_tag:
                    for kind_id in by_tag[tag]:
                        hits[kind_id] = "I1"
            string_keys = frozenset(k for k in mapping if isinstance(k, str))
            keyset = tuple(sorted(string_keys))
            if keyset in by_keyset:
                for kind_id in by_keyset[keyset]:
                    hits.setdefault(kind_id, "I2")
            for kind_id, rule in hits.items():
                slot = found[kind_id]
                slot["count"] += 1
                slot["rules"].add(rule)
                if len(slot["paths"]) < 8:
                    slot["paths"].add(rel)
                slot["descriptor_fields"].update(descriptors)

            # I2b — proper superset, counted beside the exact rule and never
            # instead of it. This is what prices the exact rule's brittleness.
            for anchor in string_keys & by_anchor.keys():
                for kind_id, frozen in by_anchor[anchor]:
                    if kind_id in hits or not frozen < string_keys:
                        continue
                    slot = found[kind_id]
                    slot["superset_count"] += 1
                    slot["rules"].add("I2b")
                    if len(slot["superset_paths"]) < 8:
                        slot["superset_paths"].add(rel)
                    slot["descriptor_fields"].update(descriptors)

    for kind_id, dests in destinations.items():
        if not dests:
            continue
        slot = found[kind_id]
        for rel, data in parsed.items():
            if not any(rel == dest or rel.startswith(dest + "/") for dest in dests):
                continue
            slot["count"] += 1
            slot["rules"].add("I3")
            if len(slot["paths"]) < 8:
                slot["paths"].add(rel)
            slot["descriptor_fields"].update(_artifact_descriptors(data))

    return {
        kind_id: {
            "count": slot["count"] + slot["superset_count"],
            "exact_count": slot["count"],
            "superset_only_count": slot["superset_count"],
            "resolved_by": sorted(slot["rules"]),
            "sample_paths": sorted(slot["paths"]),
            "superset_sample_paths": sorted(slot["superset_paths"]),
            "instance_rule_note": (
                "count = exact (I1/I2/I3) + superset-only (I2b). Amendment 2: "
                "the first run counted the exact match alone and read `none` "
                "for kinds with thousands of committed instances, because a "
                "site whose mapping gains one conditional key matches nothing "
                "exactly."
            ),
            "destination_constants": sorted(destinations[kind_id]),
            "recheck_descriptor_fields": sorted(slot["descriptor_fields"]),
        }
        for kind_id, slot in found.items()
    }


def instance_recall_probe(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Amendment 2: price I2's brittleness the way the site probe prices RM-C's.

    A kind whose exact count is zero and whose superset count is not is a kind
    the first run called `none` while the tree held its instances all along.
    Those are census misses under B10, and they are computed here rather than
    found by a reviewer.
    """

    rows = []
    for record in records:
        instances = record["committed_instances"]
        if instances["exact_count"] == 0 and instances["superset_only_count"] > 0:
            rows.append(
                {
                    "kind_id": record["kind_id"],
                    "exact_count": instances["exact_count"],
                    "superset_only_count": instances["superset_only_count"],
                    "sample_paths": instances["superset_sample_paths"],
                    "why_the_exact_rule_missed": (
                        "the committed mapping carries keys the site's literal "
                        "key set does not, so an exact match found nothing "
                        "while a proper superset match found these"
                    ),
                }
            )
    total_exact = sum(r["committed_instances"]["exact_count"] for r in records)
    total_superset = sum(
        r["committed_instances"]["superset_only_count"] for r in records
    )
    return {
        "exact_instances": total_exact,
        "superset_only_instances": total_superset,
        "kinds_the_exact_rule_alone_would_have_read_as_none": rows,
        "means": (
            "the exact key-set rule stays the rule; this probe is what makes "
            "its brittleness a number instead of a surprise"
        ),
    }


def scramble_rule(kind_id: str, instances: dict[str, Any]) -> dict[str, Any]:
    """B6's seeded per-kind scramble rule, committed by CR-P0 (§7).

    *"reassign one kind's artifacts across that kind's own records, preserving
    every file and every digest field's shape."* The seed is derived from the
    kind's own id rather than chosen, so nobody picked the permutation that
    happened to read well.
    """

    seed = int(hashlib.sha256(kind_id.encode("utf-8")).hexdigest()[:8], 16)
    return {
        "type": "permute_instances_within_artifact",
        "statement": (
            "reassign this kind's committed instances across this kind's own "
            "records by a seeded permutation, preserving every file and every "
            "digest field's shape"
        ),
        "seed": seed,
        "seed_derivation": "int(sha256(kind_id)[:8], 16) — derived, not chosen",
        "applicable": instances["count"] > 1,
        "why_not_applicable": (
            None
            if instances["count"] > 1
            else "a permutation needs at least two records to reassign between"
        ),
    }


def declare_recheck(instances: dict[str, Any]) -> dict[str, Any]:
    if instances["count"] == 0:
        return {
            "type": "none",
            "basis": "the rule found no committed instance of this kind",
        }
    self_contained = [
        field
        for field in instances["recheck_descriptor_fields"]
        if not field.endswith("(names-the-program-tree)")
    ]
    if self_contained:
        return {
            "type": "raw_checker_invocation",
            "basis": (
                "the artifact holding a committed instance carries a "
                "self-contained recheck descriptor: " + ", ".join(self_contained)
            ),
        }
    return {
        "type": "program_replay",
        "basis": (
            "committed instances exist and carry no self-contained recheck "
            "descriptor"
            + (
                " (the descriptors present name the program tree: "
                + ", ".join(instances["recheck_descriptor_fields"])
                + ")"
                if instances["recheck_descriptor_fields"]
                else ""
            )
            + ", so re-deriving the recorded verdict needs this repository's code"
        ),
    }


# --------------------------------------------------------------------------
# The pin table, captured BEFORE any rename (DESIGN §6's ordering repair C4)
# --------------------------------------------------------------------------


def capture_pin_table(repo: Path) -> dict[str, Any]:
    """`session_ledger.pins()`, run now because the harness cannot run it later.

    §6 records the ordering finding: ``session_ledger.pins()`` lives under
    ``scripts/`` and imports ``serve_chat`` and ``write_stage``, so after the
    harness renames the script tree away it cannot run at all. The pin table is
    therefore CR-P0's artifact and not the harness's, and this function is
    where that lands.
    """

    table: dict[str, Any] = {
        "captured_by": "session_ledger.pins()",
        "captured_before_rename": True,
        "why_here": (
            "session_ledger.pins() lives under scripts/ and imports serve_chat "
            "and write_stage; after the harness's rename it cannot run, so the "
            "pin table is CR-P0's artifact (DESIGN-cold-receipt.md §6, C4)"
        ),
    }
    try:
        import session_ledger  # noqa: PLC0415
        from harness import CoreSession  # noqa: PLC0415

        table["pin_fields"] = sorted(getattr(session_ledger, "PIN_FIELDS", []))
        boot = CoreSession.boot(repo, offline=True)
        table["pins"] = session_ledger.pins(repo, boot.matrix)
        table["status"] = "captured"
    except Exception as exc:  # pragma: no cover - reported, never swallowed
        table["status"] = "unavailable"
        table["error"] = f"{type(exc).__name__}: {exc}"
    return table


# --------------------------------------------------------------------------
# The recall probe — the rule's exactness, priced rather than asserted
# --------------------------------------------------------------------------


class _RecallVisitor(ast.NodeVisitor):
    """The wider net: substring name matching, no exact-key restriction."""

    def __init__(self, rel_path: str) -> None:
        self.rel_path = rel_path
        self.sites: list[dict[str, Any]] = []
        self._symbols: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._symbols.append(node.name)
        self.generic_visit(node)
        self._symbols.pop()

    visit_AsyncFunctionDef = visit_FunctionDef  # type: ignore[assignment]

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._symbols.append(node.name)
        self.generic_visit(node)
        self._symbols.pop()

    def visit_Dict(self, node: ast.Dict) -> None:
        keys = _string_keys(node)
        if any(_RECALL_SUBSTRING.search(k) for k in keys):
            self.sites.append(
                {
                    "path": self.rel_path,
                    "line_range": [
                        node.lineno,
                        getattr(node, "end_lineno", node.lineno),
                    ],
                    "symbol": ".".join(self._symbols) or "<module>",
                    "matched_keys": sorted(
                        k for k in keys if _RECALL_SUBSTRING.search(k)
                    ),
                }
            )
        self.generic_visit(node)

    def visit_ClassDef_dataclass(self, node: ast.ClassDef) -> None:  # pragma: no cover
        self.generic_visit(node)


def recall_probe(
    repo: Path, kinds: dict[str, dict[str, Any]], excluded: list[dict[str, Any]]
) -> dict[str, Any]:
    covered: set[tuple[str, int]] = set()
    for kind in kinds.values():
        for site in kind["sites"]:
            for line in range(site["line_range"][0], site["line_range"][1] + 1):
                covered.add((site["path"], line))
    for row in excluded:
        lo, hi = row["enclosing_line_range"]
        for line in range(lo, hi + 1):
            covered.add((row["path"], line))

    wide: list[dict[str, Any]] = []
    for path in sorted(repo.glob(PROGRAM_TREE_GLOB)):
        rel = repo_relative(path, repo)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:  # pragma: no cover
            continue
        visitor = _RecallVisitor(rel)
        visitor.visit(tree)
        wide.extend(visitor.sites)

    uncovered = [
        site
        for site in wide
        if not any(
            (site["path"], line) in covered
            for line in range(site["line_range"][0], site["line_range"][1] + 1)
        )
    ]
    uncovered.sort(key=lambda row: (row["path"], row["line_range"][0]))
    return {
        "substring_regex": RECALL_SUBSTRING_RE,
        "wider_net_sites": len(wide),
        "uncovered_site_count": len(uncovered),
        "uncovered_sites": uncovered,
        "means": (
            "each uncovered site is a mapping whose key names mention this "
            "program's evidence vocabulary and that the census rule did not "
            "admit. They are candidate census misses under B10 — computed by "
            "the probe, not remembered by a maintainer — and the census claims "
            "no coverage over them."
        ),
    }


def capture_external_deps(repo: Path) -> list[dict[str, Any]]:
    """Each dependency's `pin_hash` and `selection_provenance` (§4, §8).

    Captured **now**, before any rename, because §6's ordering repair (C4) says
    the pin table is CR-P0's artifact and not the harness's. `provenance` — the
    test on the BYTES — is deliberately **absent**: §8 assigns it to the
    HARNESS, from the pin hash and the resolved path in `path_audit.txt`, and a
    census that pre-assigned it would be handing the harness a declaration to
    read instead of a fact to test.
    """

    def under_home(path: Path | str | None) -> str | None:
        """Home-relative POSIX spelling, on the C-E3 supplement's convention.

        R5 forbids an absolute path in a committed artifact, and a resolved
        dependency path is exactly where one would otherwise leak.
        """

        if path is None:
            return None
        resolved = Path(path).resolve()
        try:
            return "~/" + resolved.relative_to(Path.home()).as_posix()
        except ValueError:
            return resolved.as_posix()

    deps: list[dict[str, Any]] = []

    supplement = repo / "experiments" / "conformance_ce3_supplement.json"
    lean_pin: str | None = None
    lean_toolchain: str | None = None
    lean_path: str | None = None
    if supplement.is_file():
        checker = json.loads(supplement.read_text(encoding="utf-8")).get(
            "checker", {}
        )
        lean_pin = checker.get("binary_sha256")
        lean_toolchain = checker.get("toolchain")
        lean_path = checker.get("binary")
    toolchain_file = repo / "prover" / "lean" / "normalizer" / "lean-toolchain"

    # Recomputed here, not trusted: the pin the harness will test against is
    # confirmed to still be the bytes at that path WHILE the program is
    # present, so a later mismatch is about the harness and not about drift
    # nobody noticed.
    live_digest: str | None = None
    resolved = None
    if lean_path:
        resolved = Path(str(lean_path).replace("~", str(Path.home()), 1))
        if resolved.is_file():
            live_digest = hashlib.sha256(resolved.read_bytes()).hexdigest()

    deps.append(
        {
            "name": "lean.exe",
            "role": "the pinned external checker the C-E3 probes invoke by path",
            "pin_hash": lean_pin,
            "pin_is_over": (
                "the executing binary's own bytes, recorded per-artifact by "
                "conformance_ce3_supplement.py as checker.binary_sha256"
            ),
            "toolchain": lean_toolchain,
            "resolved_path": lean_path,
            "recomputed_digest_now": live_digest,
            "recomputed_matches_pin": (
                None if live_digest is None else live_digest == lean_pin
            ),
            "selection_provenance": "repository_file",
            "selection_evidence": (
                repo_relative(toolchain_file, repo)
                if toolchain_file.is_file()
                else None
            ),
            "selection_note": (
                "prover/lean/normalizer/lean-toolchain selects this release out "
                "of the toolchains this machine's elan installed; §8 records "
                "the choice and declines to downgrade on it, which is a "
                "decision and not a proof"
            ),
        }
    )

    interpreter = Path(sys.executable)
    deps.append(
        {
            "name": "python (this repository's .venv interpreter)",
            "role": "runs every python-based recheck procedure",
            "pin_hash": None,
            "pin_is_over": None,
            "resolved_path": under_home(interpreter),
            "version": sys.version.split()[0],
            "selection_provenance": "machine_state",
            "selection_note": (
                "no digest of the interpreter is pinned anywhere in this "
                "repository; §6 pre-tags it program_configured and §8 states "
                "the consequence — every python-based recheck's SURVIVES "
                "downgrades to UNTESTED"
            ),
        }
    )

    for name in ("mypy", "jsonschema"):
        row: dict[str, Any] = {
            "name": name,
            "role": (
                "pinned in the python-tests verdicts' environment block"
                if name == "mypy"
                else "imported by scripts/radius_recheck.py; no manifest in "
                "this repository pins it"
            ),
            "pin_hash": None,
            "pin_is_over": None,
            "selection_provenance": "machine_state",
        }
        try:
            module = __import__(name)
            row["version"] = version(name)
            row["resolved_path"] = under_home(getattr(module, "__file__", None))
        except Exception as exc:  # pragma: no cover - reported, never swallowed
            row["import_error"] = f"{type(exc).__name__}: {exc}"
        deps.append(row)

    return deps


def seeded_exclusion_check(excluded: list[dict[str, Any]]) -> dict[str, Any]:
    """Does the rule reproduce the exclusion §5 seeds, without being told it?

    §5: *"the enumeration rule must reproduce the exclusion rather than depend
    on a maintainer having known about it. An exclusion that the rule cannot
    reproduce is a census miss under B10, not a judgement call."* The seed is
    ``{scripts/dump_server.py, 169-178}``. This function asks only whether the
    rule reached that site by itself; the line range it computes is its own,
    and a difference from the seeded range is published rather than adjusted.
    """

    seeded_path = "scripts/dump_server.py"
    seeded_range = [169, 178]
    matches = [row for row in excluded if row["path"] == seeded_path]
    overlapping = [
        row
        for row in matches
        if row["enclosing_line_range"][0] <= seeded_range[1]
        and row["enclosing_line_range"][1] >= seeded_range[0]
    ]
    return {
        "seed": {"path": seeded_path, "line_range": seeded_range},
        "reproduced_by_the_rule": bool(overlapping),
        "rule_that_reached_it": sorted({row["rule_id"] for row in overlapping}),
        "line_range_the_rule_computed": [
            row["line_range"] for row in overlapping
        ],
        "enclosing_line_range_the_rule_computed": [
            row["enclosing_line_range"] for row in overlapping
        ],
        "note": (
            "the rule reached this site knowing nothing about the control it "
            "is; the seeded range and the computed range are both published, "
            "and a difference between them is a fact about the seed's citation "
            "rather than about the exclusion"
        ),
    }


def pin_divergences(repo: Path) -> list[dict[str, Any]]:
    """Divergences the census observes and B9 declines to adjudicate.

    §11 names the standing instance: three ``lean-toolchain`` files pin
    v4.32.2 and ``prover/lean/proofcurve/lean-toolchain`` pins v4.29.1.
    Whether that is deliberate or drift is not determinable from the files, so
    every record here carries ``adjudicated: false``.
    """

    toolchains: dict[str, str] = {}
    for path in sorted((repo / "prover").rglob("lean-toolchain")):
        toolchains[repo_relative(path, repo)] = path.read_text(
            encoding="utf-8"
        ).strip()
    out: list[dict[str, Any]] = []
    values = sorted(set(toolchains.values()))
    if len(values) > 1:
        out.append(
            {
                "pin_a": "prover/**/lean-toolchain",
                "pin_b": "prover/**/lean-toolchain",
                "values": toolchains,
                "adjudicated": False,
                "note": (
                    "B9 cedes version drift to the pin audit, and "
                    "DESIGN-cold-receipt.md §4 records that the pin audit is "
                    "parked: this is recorded, not resolved"
                ),
            }
        )
    return out


# --------------------------------------------------------------------------
# The seal, the stop clause, and the artifact
# --------------------------------------------------------------------------


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def census_seal(kinds: list[dict[str, Any]], excluded: list[dict[str, Any]]) -> str:
    payload = {
        "enumeration_rule": ENUMERATION_RULE,
        "kinds": kinds,
        "excluded": excluded,
    }
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def adjudicate_stop(kinds: list[dict[str, Any]]) -> dict[str, Any]:
    """§5's B1 stop: is the enumeration machine-executable, or is it reading?

    The clause fires when identifying a kind's emitting routes requires
    reading code rather than running a rule. The test applied here is the
    narrowest honest one: every kind this census publishes was reached by a
    predicate in ``ENUMERATION_RULE`` and carries at least one emitting route
    that a rule resolved. A kind with no machine-resolved route would be one a
    maintainer had to supply, and its presence fires the stop.
    """

    unmapped = [k["kind_id"] for k in kinds if not k["emitting_routes"]]
    return {
        "clause": (
            "DESIGN-cold-receipt.md §5: if the enumeration cannot be made "
            "machine-executable — if identifying a kind's emitting routes "
            "requires reading code rather than running a rule — then B1 is not "
            "meetable, the harness does not open, and CR-P0 publishes as the "
            "result"
        ),
        "test": (
            "every published kind was reached by an ENUMERATION_RULE predicate "
            "and carries at least one rule-resolved emitting route"
        ),
        "kinds_with_no_machine_resolved_route": unmapped,
        "fired": bool(unmapped),
        "b1_unmapped_emitting_routes": len(unmapped),
    }


def build_census(repo: Path) -> dict[str, Any]:
    routes_vocabulary = _route_vocabulary(repo)
    sites = scan_program_tree(repo)
    kinds, excluded = form_kinds(sites, routes_vocabulary)
    instances = resolve_instances(repo, kinds)

    canonicalizers: dict[str, set[str]] = {}
    records = []
    for kind_id, kind in sorted(kinds.items()):
        inst = instances[kind_id]
        program_defined = False
        for site in kind["sites"]:
            rel = site["path"]
            if rel not in canonicalizers:
                canonicalizers[rel] = _canonicalizing_symbols(repo, rel)
            leaf = site["symbol"].split(".")[-1]
            if leaf in canonicalizers[rel]:
                program_defined = True
        record = {
            "kind_id": kind_id,
            "scramble_rule": scramble_rule(kind_id, inst),
            "tags": kind["tags"],
            "marking_rules": kind["marking_rules"],
            "emitting_routes": kind["emitting_routes"],
            "sites": kind["sites"],
            "site_key_set": kind["site_key_set"],
            "declared_recheck_procedure": declare_recheck(inst),
            "committed_instances": inst,
            "canonicalization_is_program_defined": program_defined,
        }
        if program_defined:
            record["canonicalization_note"] = (
                "the writer calls this repository's canonicalizer, so the "
                "recorded digest is taken over program-defined bytes: this kind "
                "needs the program to SERIALIZE, which is a different question "
                "from whether it needs it to ADJUDICATE "
                "(DESIGN-cold-receipt.md §11)"
            )
        records.append(record)
    excluded.sort(key=lambda row: (row["rule_id"], row["path"], row["line_range"][0]))

    inputs = sorted(repo.glob(PROGRAM_TREE_GLOB))
    census = {
        "schema": SCHEMA_TAG,
        "design": "docs/DESIGN-cold-receipt.md",
        "prerequisite": "CR-P0",
        "status_note": (
            "Committed BEFORE any COLD RECEIPT harness code exists, on the "
            "WITNESS W0 precedent. The count below is measured, never "
            "predicted: DESIGN-cold-receipt.md §5's indicative fifteen-kind "
            "walk is not this census's answer, and every difference from it is "
            "a finding rather than an error."
        ),
        "enumeration_rule": ENUMERATION_RULE,
        "route_vocabulary": {
            "source": "scripts/serve_chat.py LINE_GRAMMAR",
            "routes": routes_vocabulary,
            "note": (
                "a vocabulary, never a kind list: LINE_GRAMMAR enumerates "
                "serving routes, and a serving route is not a receipt kind"
            ),
        },
        "counts": {
            "program_tree_files_scanned": len(inputs),
            "receipt_marked_sites": len(sites),
            "kinds": len(records),
            "excluded_sites": len(excluded),
            "kinds_with_committed_instances": sum(
                1 for r in records if r["committed_instances"]["count"] > 0
            ),
            "declared_raw_checker_invocation": sum(
                1
                for r in records
                if r["declared_recheck_procedure"]["type"] == "raw_checker_invocation"
            ),
            "declared_program_replay": sum(
                1
                for r in records
                if r["declared_recheck_procedure"]["type"] == "program_replay"
            ),
            "declared_none": sum(
                1 for r in records if r["declared_recheck_procedure"]["type"] == "none"
            ),
        },
        "kinds": records,
        "excluded": excluded,
        "seeded_exclusion_check": seeded_exclusion_check(excluded),
        "recall_probe": recall_probe(repo, kinds, excluded),
        "instance_recall_probe": instance_recall_probe(records),
        "pin_table": capture_pin_table(repo),
        "external_deps_seed": capture_external_deps(repo),
        "pin_divergence": pin_divergences(repo),
        "stop_clause": adjudicate_stop(records),
    }
    census["census_seal"] = census_seal(records, excluded)
    census["provenance"] = provenance_block(Path(__file__), inputs, repo)
    return census


def amendment_block(previous: dict | None, census: dict) -> dict[str, Any]:
    """Amendment 2 (2026-08-27), under ROADMAP-v0.21 §4.0(1).

    The instrument did not do what it was written to do, which is a **bug and
    not a reading**: `I2`'s exact key-set match read `none` for kinds whose
    instances the tree held all along. The repair is additive — `I2b` counts a
    proper superset beside the exact match — and the diff against the previous
    seal is published rather than absorbed, because a regenerated registry that
    did not say what moved would be a re-seal wearing an amendment's clothes.
    """

    block: dict[str, Any] = {
        "amendment": 2,
        "dated": "2026-08-27",
        "authority": "ROADMAP-v0.21 §4.0(1) — an arm that never executed as designed is a bug, not a reading",
        "defect": (
            "I2 matched an artifact mapping only when its key set was EXACTLY "
            "the site's. A site whose mapping gains one conditional key "
            "therefore matched nothing, and the census declared "
            "recheck_procedure `none` for kinds with committed instances."
        ),
        "repair": (
            "I2b: a proper-superset match, counted beside the exact one and "
            "never instead of it, plus an instance-side recall probe so the "
            "exact rule's brittleness is a published number"
        ),
        "what_did_not_change": [
            "the four marking predicates RM-A/B/C/D",
            "the exclusion rules X1/X2 and the seeded-exclusion check",
            "the site-side recall probe",
            "the route resolution rule",
        ],
    }
    if previous is None:
        block["previous_seal"] = None
        block["diff_shape"] = "no previous artifact was present to diff against"
        return block

    before, after = previous.get("counts", {}), census["counts"]
    moved = {
        key: [before.get(key), after.get(key)]
        for key in sorted(set(before) | set(after))
        if before.get(key) != after.get(key)
    }
    previous_kinds = {k["kind_id"] for k in previous.get("kinds", [])}
    current_kinds = {k["kind_id"] for k in census["kinds"]}
    declared_moves = []
    previous_declared = {
        k["kind_id"]: k["declared_recheck_procedure"]["type"]
        for k in previous.get("kinds", [])
    }
    for record in census["kinds"]:
        was = previous_declared.get(record["kind_id"])
        now = record["declared_recheck_procedure"]["type"]
        if was is not None and was != now:
            declared_moves.append(
                {"kind_id": record["kind_id"], "from": was, "to": now}
            )
    block["previous_seal"] = previous.get("census_seal")
    block["new_seal"] = census["census_seal"]
    block["diff_shape"] = {
        "kinds_added": sorted(current_kinds - previous_kinds),
        "kinds_removed": sorted(previous_kinds - current_kinds),
        "counts_moved": moved,
        "declared_recheck_procedure_moved": declared_moves,
    }
    return block


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument(
        "--check",
        type=Path,
        default=None,
        help="recompute the census and compare against a committed artifact",
    )
    args = parser.parse_args(argv)

    previous = None
    if args.out is not None and args.out.is_file():
        try:
            previous = json.loads(args.out.read_text(encoding="utf-8"))
        except json.JSONDecodeError:  # pragma: no cover
            previous = None

    census = build_census(REPO)
    census["amendment"] = amendment_block(previous, census)

    if args.check is not None:
        committed = json.loads(args.check.read_text(encoding="utf-8"))
        drift = []
        for field in ("census_seal", "counts", "enumeration_rule"):
            if committed.get(field) != census.get(field):
                drift.append(field)
        if drift:
            print("CENSUS DRIFT: " + ", ".join(drift))
            return 1
        print(f"census matches: seal {census['census_seal'][:16]}")
        return 0

    text = json.dumps(census, indent=2, sort_keys=False, ensure_ascii=False) + "\n"
    if args.out is None:
        sys.stdout.write(text)
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(
        f"kinds {census['counts']['kinds']}  "
        f"sites {census['counts']['receipt_marked_sites']}  "
        f"excluded {census['counts']['excluded_sites']}  "
        f"seal {census['census_seal'][:16]}  "
        f"stop_fired {census['stop_clause']['fired']}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
