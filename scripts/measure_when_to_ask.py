#!/usr/bin/env python3
"""Frozen v0.14 clarification evaluator.

`validate` is safe before the candidate exists: it checks construction only
and never calls a resolver on a new row.  `score` is the one-shot boundary and
refuses until a later, provenance-pinned candidate supplies `resolve_masked`.
`compact` accepts only an already-committed raw ledger.  Do not add a preview
or dry-run scoring path.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import random
import re
import statistics
import subprocess
import sys
import tarfile
import tempfile
import unicodedata
from io import BytesIO
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from answer import records  # noqa: E402
from decompose import INGESTED_CORPUS_PREFIXES  # noqa: E402
from resolver import GraphIndex, default_index, reduce_text  # noqa: E402

DESIGN = "docs/DESIGN-when-to-ask.md"
SPEC_PATH = REPO / "experiments" / "when_to_ask_holdout.json"
MANIFEST_PATH = REPO / "experiments" / "when_to_ask_prereg_manifest.json"
RAW_PATH = REPO / "experiments" / "when_to_ask_result.raw.json"
COMPACT_PATH = REPO / "experiments" / "when_to_ask_result.json"

STRATA = {
    "negative_bind": 8,
    "negative_ask": 8,
    "ordinary_ask": 12,
    "ordinary_bind": 10,
    "out_of_corpus_pass": 10,
}
EXPECTED_ROUTE = {
    "negative_bind": "BIND",
    "negative_ask": "ASK",
    "ordinary_ask": "ASK",
    "ordinary_bind": "BIND",
    "out_of_corpus_pass": "PASS",
}
FOLLOWUP_PROFILE = {"corpus": 6, "discipline": 6, "word": 8}
FOLLOWUP_HALVING_FLOOR = {"corpus": 5, "discipline": 5, "word": 6}
PRIOR_SPECS = (
    "experiments/text_resolution_queries.json",
    "experiments/text_resolution_holdout.json",
    "experiments/text_resolution_holdout2.json",
    "experiments/text_resolution_holdout3.json",
)
FORBIDDEN_PATH = REPO / "experiments" / "when_to_ask_forbidden_ids.json"
OEWN_ARCHIVE_SHA256 = "7d749f6e2c39e6970e4997839dcf6e42fd281f3c2fae0171d2192bae8cfa4b51"
F4_SCORER_BLOB = "32dc0a0d45474dc5f2ba9d06d9f6f40e8fddb685"
F4_SEED = 20260818
OEWN_SEEDS = (20260825, 20260826, 20260827)
OEWN_SAMPLE_SIZE = 1000
BLIND_LIMIT = 25
FRESHNESS_CEILING = 0.50

_NEGATIVE_RE = re.compile(
    r"^(?P<positive>.+?) without (?P<term>[a-z0-9]+(?: [a-z0-9]+)?)$"
)
_WITHOUT_BOUNDARY_RE = re.compile(r"(?<![a-z0-9])without(?![a-z0-9])")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_TITLE_TOKEN_RE = re.compile(r"[a-z0-9]+")
_FOLLOWUP_RE = re.compile(r"^narrow (corpus|discipline|word) (\S(?:.*\S)?)$")


class ProtocolError(RuntimeError):
    """Fail-closed preregistration or scoring error."""


@dataclass(frozen=True)
class NegativePlan:
    normalized_query: str
    positive: str
    term: str
    required_tokens: tuple[str, ...]
    veto_ids: tuple[str, ...]


@dataclass(frozen=True, order=True)
class OewnKey:
    synset_id: str
    source_field: str
    ordinal: int

    def serial(self) -> str:
        return f"{self.synset_id}\t{self.source_field}\t{self.ordinal}"


@dataclass(frozen=True)
class OewnEntry:
    key: OewnKey
    text: str
    normalized_text: str


def canonical_bytes(path: Path) -> bytes:
    """Canonical LF bytes used by every preregistration digest."""
    return path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(canonical_bytes(path))


def normalize_query(text: str) -> str:
    """Freshness normalization, deliberately distinct from grammar parsing."""
    value = unicodedata.normalize("NFKC", text).casefold()
    return _NON_ALNUM_RE.sub(" ", value).strip()


def grammar_normalize(text: str) -> str:
    """NFKC + casefold + whitespace only; punctuation remains observable."""
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def parse_negative(
    query: str,
    corpus: dict[str, tuple[dict, str]],
    reducer: Callable[[str], Sequence[str]] = reduce_text,
) -> NegativePlan:
    normalized = grammar_normalize(query)
    match = _NEGATIVE_RE.fullmatch(normalized)
    if match is None:
        raise ProtocolError("negative query does not match the frozen grammar")
    positive = match.group("positive")
    term = match.group("term")
    if _WITHOUT_BOUNDARY_RE.search(positive):
        raise ProtocolError("negative query contains more than one without marker")
    positive_tokens = tuple(reducer(positive))
    required_tokens = tuple(reducer(term))
    if not positive_tokens:
        raise ProtocolError("negative query has an empty reduced positive payload")
    if not required_tokens:
        raise ProtocolError("negative TERM reduces to no tokens")
    vetoes = tuple(
        sorted(
            sid
            for sid, (node, _corpus) in corpus.items()
            if all(token in node_inventory_tokens(node, reducer) for token in required_tokens)
        )
    )
    if not vetoes:
        raise ProtocolError("negative TERM vetoes no committed statement")
    return NegativePlan(normalized, positive, term, required_tokens, vetoes)


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)


def node_inventory_tokens(
    node: dict,
    reducer: Callable[[str], Sequence[str]] = reduce_text,
) -> frozenset[str]:
    fields = (
        node.get("title", ""),
        node.get("semantic_interpretation", {}).get("statement_meaning", ""),
        node.get("keywords", []),
        node.get("symbol_lexicon", {}),
    )
    return frozenset(token for field in fields for text in _strings(field) for token in reducer(text))


def title_tokens(text: str) -> frozenset[str]:
    return frozenset(_TITLE_TOKEN_RE.findall(normalize_query(text)))


def jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def blind_initial(query: str, corpus: dict[str, tuple[dict, str]]) -> tuple[str, ...]:
    asked = title_tokens(query)
    ranked = sorted(
        (
            (-jaccard(asked, title_tokens(str(node.get("title", "")))), sid)
            for sid, (node, _corpus) in corpus.items()
        ),
        key=lambda item: (item[0], item[1]),
    )
    return tuple(sid for _negative_score, sid in ranked[:BLIND_LIMIT])


def parse_followup(line: str) -> tuple[str, str]:
    match = _FOLLOWUP_RE.fullmatch(grammar_normalize(line))
    if match is None:
        raise ProtocolError("follow-up does not match 'narrow CLASS VALUE'")
    return match.group(1), match.group(2)


def blind_followup(
    candidates: Sequence[str],
    line: str,
    corpus: dict[str, tuple[dict, str]],
) -> tuple[str, ...]:
    _kind, value = parse_followup(line)
    asked = title_tokens(value)
    scores = [
        (jaccard(asked, title_tokens(str(corpus[sid][0].get("title", "")))), sid)
        for sid in candidates
    ]
    positive = [(score, sid) for score, sid in scores if score > 0]
    if not positive:
        return tuple(candidates)
    return tuple(sid for score, sid in sorted(positive, key=lambda item: (-item[0], item[1])))


def reciprocal_candidate_load(primary_id: str, candidates: Sequence[str]) -> float:
    k = len(candidates)
    return 1 / k if 0 < k <= BLIND_LIMIT and primary_id in candidates else 0.0


def character_trigrams(text: str) -> frozenset[str]:
    normalized = normalize_query(text)
    return frozenset(normalized[i : i + 3] for i in range(max(0, len(normalized) - 2)))


_SPEC_KEYS = {"schema", "design", "authorship_note", "rows"}
_ROW_KEYS = {
    "row_id", "stratum", "query", "expected_route", "primary_id",
    "follow_up", "retained_ids", "negative_span", "rationale",
}
_FOLLOWUP_KEYS = {"line", "class", "value"}
_NEGATIVE_KEYS = {"text", "term"}
_FORBIDDEN_KEYS = {
    "schema", "method", "resolver_commit", "resolver_tree", "id_count", "ordered_ids_sha256",
    "prior_specs", "forbidden_intended_ids",
}
_MANIFEST_KEYS = {
    "schema", "design", "base_commit", "base_tree", "scripts_tree",
    "existing_inputs", "data_trees", "preregistration_paths",
    "allowed_candidate_paths", "raw_ledger_contract",
}
_INPUT_KEYS = {"path", "git_commit", "git_blob", "canonical_lf_sha256"}
_TREE_KEYS = {
    "path", "git_commit", "git_tree", "combined_canonical_lf_sha256", "node_files",
}
_SCRIPTS_TREE_KEYS = {
    "git_commit", "git_tree", "combined_canonical_lf_sha256", "tracked_files",
}
_RAW_CONTRACT_KEYS = {"path", "exclusive_create", "must_precede_compact"}


def _context_constraint(line: str) -> tuple[str, str] | None:
    """The live shell's own follow-up parse, imported rather than restated."""
    from harness import _context_constraint as runtime_parse  # noqa: PLC0415

    return runtime_parse(line)


_INDEX_CACHE: list[GraphIndex] = []


def _index() -> GraphIndex:
    if not _INDEX_CACHE:
        _INDEX_CACHE.append(default_index())
    return _INDEX_CACHE[0]


def _exact_keys(value: dict, expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        raise ProtocolError(
            f"{label} keys differ: missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )


def _read_rows(path: Path = SPEC_PATH) -> list[dict]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ProtocolError("holdout must be an object")
    _exact_keys(doc, _SPEC_KEYS, "holdout")
    if (
        doc.get("schema") != "when_to_ask_holdout.v1"
        or doc.get("design") != DESIGN
        or not isinstance(doc.get("authorship_note"), str)
        or not isinstance(doc.get("rows"), list)
    ):
        raise ProtocolError("wrong holdout schema")
    for position, row in enumerate(doc["rows"]):
        if not isinstance(row, dict):
            raise ProtocolError(f"row {position} must be an object")
        _exact_keys(row, _ROW_KEYS, f"row {position}")
        for key in ("row_id", "stratum", "query", "expected_route", "rationale"):
            if not isinstance(row[key], str) or not row[key]:
                raise ProtocolError(f"row {position}.{key} must be a nonempty string")
        if row["primary_id"] is not None and not isinstance(row["primary_id"], str):
            raise ProtocolError(f"row {position}.primary_id has wrong type")
        if not isinstance(row["retained_ids"], list) or not all(
            isinstance(sid, str) and sid for sid in row["retained_ids"]
        ):
            raise ProtocolError(f"row {position}.retained_ids has wrong type")
        follow = row["follow_up"]
        if follow is not None:
            if not isinstance(follow, dict):
                raise ProtocolError(f"row {position}.follow_up must be an object or null")
            _exact_keys(follow, _FOLLOWUP_KEYS, f"row {position}.follow_up")
            if not all(isinstance(follow[key], str) and follow[key] for key in _FOLLOWUP_KEYS):
                raise ProtocolError(f"row {position}.follow_up values must be strings")
        negative = row["negative_span"]
        if negative is not None:
            if not isinstance(negative, dict):
                raise ProtocolError(f"row {position}.negative_span must be an object or null")
            _exact_keys(negative, _NEGATIVE_KEYS, f"row {position}.negative_span")
            if not all(isinstance(negative[key], str) and negative[key] for key in _NEGATIVE_KEYS):
                raise ProtocolError(f"row {position}.negative_span values must be strings")
    return doc["rows"]


def _prior_queries(prior_paths: Sequence[Path] | None = None) -> list[str]:
    out: list[str] = []
    paths = prior_paths or tuple(REPO / rel for rel in PRIOR_SPECS)
    for path in paths:
        doc = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict) or not isinstance(doc.get("queries"), list):
            raise ProtocolError(f"malformed prior spec: {path}")
        for position, row in enumerate(doc["queries"]):
            if not isinstance(row, dict) or not isinstance(row.get("text"), str):
                raise ProtocolError(f"malformed prior query {path}:{position}")
            out.append(row["text"])
    return out


def _read_forbidden(path: Path) -> set[str]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ProtocolError("forbidden-id ledger must be an object")
    _exact_keys(doc, _FORBIDDEN_KEYS, "forbidden-id ledger")
    ids = doc.get("forbidden_intended_ids")
    if (
        doc.get("schema") != "when_to_ask_forbidden_ids.v1"
        or not isinstance(doc.get("method"), str)
        or not isinstance(doc.get("resolver_commit"), str)
        or not isinstance(doc.get("resolver_tree"), str)
        or not isinstance(doc.get("prior_specs"), list)
        or not isinstance(ids, list)
        or not all(isinstance(sid, str) and sid for sid in ids)
    ):
        raise ProtocolError("malformed forbidden-id ledger")
    digest = sha256_bytes(("\n".join(ids) + "\n").encode("utf-8"))
    if ids != sorted(set(ids)) or doc.get("id_count") != len(ids) or doc.get("ordered_ids_sha256") != digest:
        raise ProtocolError("forbidden-id count/order/digest mismatch")
    if doc["prior_specs"] != list(PRIOR_SPECS):
        raise ProtocolError("forbidden-id prior-spec list drift")
    return set(ids)


def recompute_forbidden_ids(path: Path = FORBIDDEN_PATH) -> tuple[str, ...]:
    """Re-run only spent queries with the exact archived v0.13 tree."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    commit = doc.get("resolver_commit")
    tree = doc.get("resolver_tree")
    if not isinstance(commit, str) or _git("rev-parse", f"{commit}^{{tree}}") != tree:
        raise ProtocolError("pinned forbidden-id resolver tree mismatch")
    wanted = ["scripts", "data", "data_holdout", *PRIOR_SPECS]
    archive = subprocess.run(
        ["git", "archive", "--format=tar", commit, "--", *wanted],
        cwd=REPO, check=True, capture_output=True,
    ).stdout
    program = r"""
import json,sys
from pathlib import Path
sys.path.insert(0, 'scripts')
from resolver import default_index, resolve
specs = sys.argv[1:]
index = default_index()
ids = set()
for rel in specs:
    doc = json.loads(Path(rel).read_text(encoding='utf-8'))
    for row in doc['queries']:
        outcome = resolve(row['text'], index)
        ids.update(outcome.candidates)
        if rel.endswith('text_resolution_holdout3.json'):
            ids.add(row['target'])
print(json.dumps(sorted(ids)))
"""
    with tempfile.TemporaryDirectory(prefix="when-to-ask-spent-") as temp:
        root = Path(temp)
        with tarfile.open(fileobj=BytesIO(archive), mode="r:") as bundle:
            bundle.extractall(root, filter="data")
        result = subprocess.run(
            [sys.executable, "-c", program, *PRIOR_SPECS], cwd=root,
            check=True, capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    ids = json.loads(result.stdout)
    if not isinstance(ids, list) or not all(isinstance(sid, str) for sid in ids):
        raise ProtocolError("pinned forbidden-id recomputation returned malformed output")
    return tuple(ids)


def validate_structure(
    spec_path: Path = SPEC_PATH,
    forbidden_path: Path = FORBIDDEN_PATH,
    prior_paths: Sequence[Path] | None = None,
) -> dict:
    """Validate preregistration without resolving any new query."""
    rows = _read_rows(spec_path)
    errors: list[str] = []
    counts = Counter(row.get("stratum") for row in rows)
    if counts != Counter(STRATA):
        errors.append(f"strata {dict(counts)} != {STRATA}")
    row_ids = [row["row_id"] for row in rows]
    if len(row_ids) != len(set(row_ids)):
        errors.append("row_id values are not unique")
    normalized = [normalize_query(row["query"]) for row in rows]
    if any(not text for text in normalized) or len(normalized) != len(set(normalized)):
        errors.append("queries are empty or duplicate after normalization")

    corpus = records([REPO / "data"])
    holdout_ids = set(records([REPO / "data_holdout"]))
    forbidden = _read_forbidden(forbidden_path)
    recomputed_forbidden = recompute_forbidden_ids(forbidden_path)
    if tuple(sorted(forbidden)) != recomputed_forbidden:
        raise ProtocolError("forbidden-id ledger differs from pinned v0.13 recomputation")
    credit_ids: list[str] = []
    followups: Counter[str] = Counter()
    negative_report: list[dict] = []

    prior_trigrams = [(text, character_trigrams(text)) for text in _prior_queries(prior_paths)]
    max_prior: list[dict] = []
    for row, norm in zip(rows, normalized, strict=True):
        row_id = row["row_id"]
        stratum = row["stratum"]
        route = row["expected_route"]
        if EXPECTED_ROUTE.get(stratum) != route:
            errors.append(f"{row_id}: route does not match stratum")
        primary = row.get("primary_id")
        retained = row.get("retained_ids")
        if not isinstance(retained, list) or len(retained) != len(set(retained)):
            errors.append(f"{row_id}: retained_ids must be a unique list")
            retained = []
        ask = route == "ASK"
        if ask:
            if not isinstance(primary, str) or primary not in retained:
                errors.append(f"{row_id}: ASK retained_ids must contain primary_id")
            follow = row.get("follow_up")
            if not isinstance(follow, dict):
                errors.append(f"{row_id}: ASK needs follow_up")
            else:
                try:
                    line = str(follow.get("line", ""))
                    kind, value = parse_followup(line)
                    if kind != follow.get("class") or value != follow.get("value"):
                        errors.append(f"{row_id}: follow-up fields disagree with parser")
                    # Design section 4 binds the blind arm to the runtime's own
                    # parse; freeze that equivalence instead of assuming it.
                    if _context_constraint(line) != (kind, value):
                        errors.append(f"{row_id}: follow-up parse differs from the runtime parse")
                    # A follow-up that cannot keep its own declared reading is a
                    # miss the one-shot run would only rediscover; refuse now.
                    declared = tuple(sid for sid in retained if isinstance(sid, str))
                    if declared and set(declared) - set(
                        _narrow_matched(_index(), declared, kind, value)
                    ):
                        errors.append(f"{row_id}: follow-up drops its own declared retained ids")
                    followups[kind] += 1
                except ProtocolError as exc:
                    errors.append(f"{row_id}: {exc}")
        elif row.get("follow_up") is not None or retained:
            errors.append(f"{row_id}: non-ASK rows may not carry follow-up credit")
        if route == "PASS":
            if primary is not None:
                errors.append(f"{row_id}: PASS primary_id must be null")
        elif isinstance(primary, str):
            credit_ids.extend([primary, *retained])
        else:
            errors.append(f"{row_id}: in-corpus row needs primary_id")

        is_negative = stratum in {"negative_bind", "negative_ask"}
        if is_negative:
            try:
                plan = parse_negative(str(row.get("query", "")), corpus)
                span = row.get("negative_span")
                if span != {"text": f"without {plan.term}", "term": plan.term}:
                    errors.append(f"{row_id}: negative_span disagrees with parser")
                protected = {sid for sid in [primary, *retained] if isinstance(sid, str)}
                overlap = protected & set(plan.veto_ids)
                if overlap:
                    errors.append(f"{row_id}: veto removes credit ids {sorted(overlap)}")
                negative_report.append({
                    "row_id": row_id,
                    "term": plan.term,
                    "required_tokens": list(plan.required_tokens),
                    "veto_count": len(plan.veto_ids),
                })
            except ProtocolError as exc:
                errors.append(f"{row_id}: {exc}")
        elif row.get("negative_span") is not None:
            errors.append(f"{row_id}: ordinary row has negative_span")

        tri = character_trigrams(norm)
        prior_scores = [(jaccard(tri, other), text) for text, other in prior_trigrams]
        score, prior = max(prior_scores, default=(0.0, ""))
        max_prior.append({"row_id": row_id, "similarity": round(score, 6), "prior": prior})
        if score >= FRESHNESS_CEILING:
            errors.append(f"{row_id}: prior trigram overlap {score:.6f} >= {FRESHNESS_CEILING}")

    for i, left in enumerate(rows):
        for right in rows[i + 1 :]:
            score = jaccard(character_trigrams(left["query"]), character_trigrams(right["query"]))
            if score >= FRESHNESS_CEILING:
                errors.append(f"{left['row_id']}/{right['row_id']}: pairwise trigram overlap {score:.6f}")

    unique_credit = set(credit_ids)
    if len(unique_credit) != 38 or len(credit_ids) != 58:
        # 38 primaries plus the same 20 repeated as ASK retained ids.
        errors.append(f"credit-id shape is {len(unique_credit)} unique/{len(credit_ids)} declarations")
    for sid in sorted(unique_credit):
        if sid not in corpus:
            errors.append(f"credit id absent from data/: {sid}")
            continue
        if sid in holdout_ids:
            errors.append(f"credit id appears in data_holdout/: {sid}")
        if sid in forbidden:
            errors.append(f"credit id is forbidden by prior sets: {sid}")
        corpus_id = corpus[sid][1]
        if corpus_id.startswith(tuple(INGESTED_CORPUS_PREFIXES)):
            errors.append(f"credit id belongs to ineligible generated corpus: {sid}")
    primary_ids = [row["primary_id"] for row in rows if row["primary_id"] is not None]
    if len(primary_ids) != 38 or len(primary_ids) != len(set(primary_ids)):
        errors.append("primary ids are not 38 distinct ids")
    prefix_counts = Counter(sid.split(".", 1)[0] for sid in primary_ids)
    if len(prefix_counts) < 10 or max(prefix_counts.values(), default=0) > 6:
        errors.append(f"discipline diversity fails: {dict(prefix_counts)}")
    if followups != Counter(FOLLOWUP_PROFILE):
        errors.append(f"follow-up profile {dict(followups)} != {FOLLOWUP_PROFILE}")

    if errors:
        raise ProtocolError("construction failed:\n- " + "\n- ".join(errors))
    return {
        "schema": "when_to_ask_construction.v1",
        "rows": len(rows),
        "strata": dict(sorted(counts.items())),
        "follow_up_profile": dict(sorted(followups.items())),
        "unique_primary_ids": len(set(primary_ids)),
        "top_level_prefixes": dict(sorted(prefix_counts.items())),
        "negative_inventory": negative_report,
        "freshness": {"ceiling": FRESHNESS_CEILING, "max_against_prior": max_prior},
    }


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True, text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _git_bytes(*args: str) -> bytes:
    return subprocess.run(
        ["git", *args], cwd=REPO, check=True, capture_output=True,
    ).stdout


def verify_manifest(path: Path = MANIFEST_PATH) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ProtocolError("preregistration manifest must be an object")
    _exact_keys(manifest, _MANIFEST_KEYS, "preregistration manifest")
    if (
        manifest.get("schema") != "when_to_ask_prereg_manifest.v1"
        or manifest.get("design") != DESIGN
        or not all(isinstance(manifest.get(key), str) for key in ("base_commit", "base_tree"))
    ):
        raise ProtocolError("wrong preregistration manifest schema")
    if not isinstance(manifest["scripts_tree"], dict):
        raise ProtocolError("scripts_tree must be an object")
    _exact_keys(manifest["scripts_tree"], _SCRIPTS_TREE_KEYS, "scripts_tree")
    if not isinstance(manifest["existing_inputs"], list):
        raise ProtocolError("existing_inputs must be a list")
    for position, entry in enumerate(manifest["existing_inputs"]):
        if not isinstance(entry, dict):
            raise ProtocolError(f"existing input {position} must be an object")
        _exact_keys(entry, _INPUT_KEYS, f"existing input {position}")
        if not all(isinstance(entry[key], str) for key in _INPUT_KEYS):
            raise ProtocolError(f"existing input {position} values must be strings")
    if not isinstance(manifest["data_trees"], list) or len(manifest["data_trees"]) != 2:
        raise ProtocolError("data_trees must contain data and data_holdout")
    for position, entry in enumerate(manifest["data_trees"]):
        if not isinstance(entry, dict):
            raise ProtocolError(f"data tree {position} must be an object")
        _exact_keys(entry, _TREE_KEYS, f"data tree {position}")
    if {entry["path"] for entry in manifest["data_trees"]} != {"data", "data_holdout"}:
        raise ProtocolError("data tree paths drifted")
    for key in ("preregistration_paths", "allowed_candidate_paths"):
        value = manifest[key]
        if not isinstance(value, list) or value != sorted(set(value)) or not all(
            isinstance(path, str) and path for path in value
        ):
            raise ProtocolError(f"{key} must be a sorted unique path list")
    if not isinstance(manifest["raw_ledger_contract"], dict):
        raise ProtocolError("raw_ledger_contract must be an object")
    _exact_keys(manifest["raw_ledger_contract"], _RAW_CONTRACT_KEYS, "raw_ledger_contract")
    contract = manifest["raw_ledger_contract"]
    if (
        contract["path"] != str(RAW_PATH.relative_to(REPO)).replace("\\", "/")
        or contract["must_precede_compact"] != str(COMPACT_PATH.relative_to(REPO)).replace("\\", "/")
        or contract["exclusive_create"] is not True
    ):
        raise ProtocolError("raw ledger contract drifted")
    if _git("rev-parse", f"{manifest['base_commit']}^{{tree}}") != manifest["base_tree"]:
        raise ProtocolError("manifest base tree mismatch")
    scripts_entry = manifest["scripts_tree"]
    if _git("rev-parse", f"{scripts_entry['git_commit']}:scripts") != scripts_entry["git_tree"]:
        raise ProtocolError("scripts tree mismatch")
    script_paths = _git(
        "ls-tree", "-r", "--name-only", scripts_entry["git_commit"], "scripts"
    ).splitlines()
    script_payload = b"".join(
        rel.encode("utf-8") + b"\0"
        + _git_bytes("show", f"{scripts_entry['git_commit']}:{rel}")
        .replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        for rel in sorted(script_paths)
    )
    if (
        len(script_paths) != scripts_entry["tracked_files"]
        or sha256_bytes(script_payload) != scripts_entry["combined_canonical_lf_sha256"]
    ):
        raise ProtocolError("scripts tree canonical digest mismatch")
    for entry in manifest["existing_inputs"]:
        payload = _git_bytes("show", f"{entry['git_commit']}:{entry['path']}")
        canonical = payload.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        if sha256_bytes(canonical) != entry["canonical_lf_sha256"]:
            raise ProtocolError(f"manifest mismatch: {entry['path']}")
        if _git("rev-parse", f"{entry['git_commit']}:{entry['path']}") != entry["git_blob"]:
            raise ProtocolError(f"Git object mismatch: {entry['path']}")
    for data_entry in manifest["data_trees"]:
        root = data_entry["path"]
        if _git("rev-parse", f"{data_entry['git_commit']}:{root}") != data_entry["git_tree"]:
            raise ProtocolError(f"{root} tree mismatch")
        combined = b"".join(
            rel.as_posix().encode("utf-8") + b"\0" + canonical_bytes(REPO / rel)
            for rel in sorted(
                Path(root) / path.relative_to(REPO / root)
                for path in (REPO / root).glob("*/nodes.json")
            )
        )
        if sha256_bytes(combined) != data_entry["combined_canonical_lf_sha256"]:
            raise ProtocolError(f"{root} canonical digest mismatch")
    return manifest


def _candidate_resolvers():
    import resolver  # noqa: PLC0415

    negative = getattr(resolver, "resolve_negative", None)
    if negative is None:
        raise ProtocolError("candidate absent: resolver.resolve_negative is not implemented")
    parameters = tuple(inspect.signature(negative).parameters)
    if parameters != ("text", "index"):
        raise ProtocolError(f"resolve_negative signature changed: {parameters}")
    ordinary = getattr(resolver, "resolve", None)
    if ordinary is None:
        raise ProtocolError("candidate removed resolver.resolve")
    return ordinary, negative


def _narrow_matched(
    index: GraphIndex, candidates: tuple[str, ...], kind: str, value: str
) -> tuple[str, ...]:
    """Raw constraint match, mirroring `harness._narrow_candidates` exactly."""
    from answer import compose  # noqa: PLC0415

    if kind == "corpus":
        matched = tuple(
            sid for sid in candidates
            if index.corpus_of.get(sid, "").casefold() == value
        )
    elif kind == "discipline":
        matched = tuple(
            sid for sid in candidates
            if (answer := compose(sid)) is not None
            and value in {discipline.casefold() for discipline in answer.disciplines}
        )
    else:
        words = tuple(reduce_text(value.replace("_", " ").replace(".", " ")))
        if len(words) != 1:
            matched = ()
        else:
            owners: set[str] = set()
            for postings in (index.by_keyword, index.by_lexicon, index.by_prose):
                owners.update(postings.get(words[0], ()))
            matched = tuple(sid for sid in candidates if sid in owners)
    return matched


def _narrow(index: GraphIndex, candidates: tuple[str, ...], kind: str, value: str) -> tuple[str, ...]:
    """Runtime no-guess rule: a zero-match follow-up keeps the pending set."""
    return _narrow_matched(index, candidates, kind, value) or candidates


def _kind_name(outcome: Any) -> str:
    return str(outcome.kind).upper()


def _candidate_negative(query: str, index: GraphIndex, resolve_negative, reference: NegativePlan):
    """Exercise and verify the candidate's public parser/inventory path."""
    result = resolve_negative(query, index)
    try:
        outcome = result.outcome
        observed = (
            result.positive,
            result.term,
            tuple(result.required_tokens),
            tuple(result.veto_ids),
        )
    except AttributeError as exc:
        raise ProtocolError("resolve_negative must return outcome/positive/term/required_tokens/veto_ids") from exc
    expected = (reference.positive, reference.term, reference.required_tokens, reference.veto_ids)
    if observed != expected:
        raise ProtocolError(f"candidate negative plan drift: {observed!r} != {expected!r}")
    return outcome


def score_holdout(resolve, resolve_negative, index: GraphIndex, corpus: dict[str, tuple[dict, str]]) -> tuple[list[dict], dict]:
    rows_out: list[dict] = []
    for row in _read_rows():
        query = row["query"]
        if row["negative_span"] is not None:
            plan = parse_negative(query, corpus)
            outcome = _candidate_negative(query, index, resolve_negative, plan)
            stripped_outcome = resolve(plan.positive, index)
        else:
            plan = None
            outcome = resolve(grammar_normalize(query), index)
            stripped_outcome = None
        candidates = tuple(outcome.candidates)
        follow_result: tuple[str, ...] = ()
        if row["follow_up"] is not None and _kind_name(outcome) == "ASK":
            kind, value = parse_followup(row["follow_up"]["line"])
            follow_result = _narrow(index, candidates, kind, value)
        blind = blind_initial(query, corpus)
        blind_after = blind_followup(blind, row["follow_up"]["line"], corpus) if row["follow_up"] else ()
        primary = row["primary_id"]
        rows_out.append({
            "row_id": row["row_id"], "stratum": row["stratum"],
            "expected_route": row["expected_route"], "observed_route": _kind_name(outcome),
            "primary_id": primary, "retained_ids": row["retained_ids"],
            "candidates": list(candidates), "candidate_count": len(candidates),
            "primary_recalled": primary in candidates if primary else False,
            "wrong_bind": _kind_name(outcome) == "BIND" and outcome.bound != primary,
            "follow_up_class": row["follow_up"]["class"] if row["follow_up"] else None,
            "follow_candidates": list(follow_result), "follow_count": len(follow_result),
            "retained_after_follow": all(sid in follow_result for sid in row["retained_ids"]),
            "blind_candidates": list(blind), "blind_follow_candidates": list(blind_after),
            "resolver_reciprocal_load": reciprocal_candidate_load(primary, candidates) if primary else 0.0,
            "blind_reciprocal_load": reciprocal_candidate_load(primary, blind) if primary else 0.0,
            "stripped_route": _kind_name(stripped_outcome) if stripped_outcome else None,
            "stripped_bound": stripped_outcome.bound if stripped_outcome else None,
            "stripped_bound_was_vetoed": bool(
                stripped_outcome is not None
                and _kind_name(stripped_outcome) == "BIND"
                and stripped_outcome.bound in plan.veto_ids
            ),
        })
    return rows_out, adjudicate(rows_out)


def adjudicate(rows: Sequence[dict]) -> dict:
    negative = [row for row in rows if row["stratum"].startswith("negative_")]
    asks = [row for row in rows if row["expected_route"] == "ASK"]
    in_corpus = [row for row in rows if row["primary_id"] is not None]
    wrong = sum(row["wrong_bind"] for row in negative)
    neg_reach = sum(row["observed_route"] in {"BIND", "ASK"} and row["primary_recalled"] for row in negative)
    neg_route = sum(row["observed_route"] == row["expected_route"] for row in negative)
    halvings = [row["follow_count"] * 2 <= row["candidate_count"] and row["retained_after_follow"] for row in asks]
    class_stats: dict[str, dict] = {}
    for kind in FOLLOWUP_PROFILE:
        members = [row for row in asks if row["follow_up_class"] == kind]
        fired = [row["follow_count"] * 2 <= row["candidate_count"] and row["retained_after_follow"] for row in members]
        class_stats[kind] = {
            "halved_and_retained": sum(fired), "of": len(members),
            "floor": FOLLOWUP_HALVING_FLOOR[kind],
            "survivor_sizes": [row["follow_count"] for row in members],
            "singletons": sum(row["follow_count"] == 1 for row in members),
        }
    tuples = {tuple(row["candidates"]) for row in asks}
    profile_ok = (
        len(tuples) == 20
        and sum(row["candidate_count"] >= 4 for row in asks) >= 10
        and sum(row["candidate_count"] >= 8 for row in asks) >= 4
        and all(row["candidate_count"] <= BLIND_LIMIT for row in asks)
    )
    q2 = (
        all(row["retained_after_follow"] for row in asks)
        and sum(halvings) >= 15
        and all(class_stats[k]["halved_and_retained"] >= FOLLOWUP_HALVING_FLOOR[k] for k in class_stats)
        and profile_ok
    )
    resolver_mean = statistics.fmean(row["resolver_reciprocal_load"] for row in in_corpus)
    blind_mean = statistics.fmean(row["blind_reciprocal_load"] for row in in_corpus)
    blind_halvings = [
        len(row["blind_follow_candidates"]) * 2 <= len(row["blind_candidates"])
        and row["primary_id"] in row["blind_follow_candidates"]
        for row in asks
    ]
    blind_class_halvings = {
        kind: sum(
            len(row["blind_follow_candidates"]) * 2 <= len(row["blind_candidates"])
            and row["primary_id"] in row["blind_follow_candidates"]
            for row in asks if row["follow_up_class"] == kind
        )
        for kind in FOLLOWUP_PROFILE
    }
    blind_meets_q2 = (
        sum(blind_halvings) >= 15
        and all(
            blind_class_halvings[kind] >= FOLLOWUP_HALVING_FLOOR[kind]
            for kind in FOLLOWUP_PROFILE
        )
    )
    reach = sum(row["observed_route"] in {"BIND", "ASK"} for row in in_corpus)
    recall = sum(row["primary_recalled"] for row in in_corpus)
    return {
        "Q1": {"fired": wrong == 0 and neg_reach >= 14 and neg_route >= 14,
               "wrong_negative_binds": wrong, "negative_primary_reach": neg_reach,
               "negative_expected_routes": neg_route, "of": 16},
        "Q2": {"fired": q2, "halved_and_retained": sum(halvings), "of": 20,
               "classes": class_stats, "distinct_initial_tuples": len(tuples),
               "initial_k_ge_4": sum(row["candidate_count"] >= 4 for row in asks),
               "initial_k_ge_8": sum(row["candidate_count"] >= 8 for row in asks),
               "initial_k_over_25": sum(row["candidate_count"] > 25 for row in asks)},
        "Q3": {"fired": resolver_mean - blind_mean >= 0.10 and not blind_meets_q2,
               "resolver_mean": resolver_mean, "blind_mean": blind_mean,
               "gap": resolver_mean - blind_mean,
               "blind_halved_and_retained": sum(blind_halvings),
               "blind_class_halvings": blind_class_halvings,
               "blind_meets_q2_bar": blind_meets_q2},
        "Q5": {"fired": reach / 38 >= 0.833 and recall / 38 >= 0.833,
               "reach": reach, "target_recall": recall, "of": 38},
        "Q6": {
            "fired": sum(row["stripped_bound_was_vetoed"] for row in negative) >= 4
            and wrong == 0 and neg_reach >= 14 and neg_route >= 14,
            "stripped_single_binds_to_vetoed_ids": sum(
                row["stripped_bound_was_vetoed"] for row in negative
            ),
            "of": 16,
            "threshold": 4,
        },
    }


def masked_rank_reference(
    scored: Sequence[tuple[str, float]], veto_ids: Iterable[str]
) -> tuple[tuple[str, float], ...]:
    """Synthetic oracle for the frozen admission seam; not the candidate."""
    veto = frozenset(veto_ids)
    allowed = [(sid, score) for sid, score in scored if sid not in veto]
    return tuple(sorted(allowed, key=lambda item: (-item[1], item[0])))


def oewn_pool(index: Any) -> list[OewnEntry]:
    pool: list[OewnEntry] = []
    for synset_id in sorted(index.synsets):
        synset = index.synsets[synset_id]
        chosen: OewnEntry | None = None
        for field in ("examples", "definitions"):
            for ordinal, raw in enumerate(getattr(synset, field)):
                text = " ".join(str(raw).split())
                if 20 <= len(text) <= 120:
                    chosen = OewnEntry(OewnKey(synset_id, field, ordinal), text, normalize_query(text))
                    break
            if chosen is not None:
                break
        if chosen is not None:
            pool.append(chosen)
    return pool


def _oewn_samples(archive: Path) -> tuple[dict, list[list[OewnEntry]]]:
    """Construct receipts and in-memory samples; never persist text or keys."""
    from wordnet_store import WordNetIndex  # noqa: PLC0415

    if sha256_bytes(archive.read_bytes()) != OEWN_ARCHIVE_SHA256:
        raise ProtocolError("OEWN archive digest mismatch")
    pool = oewn_pool(WordNetIndex.load(archive))
    canonical = list(pool)
    random.Random(F4_SEED).shuffle(canonical)
    canonical_spent = canonical[:OEWN_SAMPLE_SIZE]
    f4 = json.loads((REPO / "experiments" / "false_positive_rate_f4.json").read_text(encoding="utf-8"))
    claimed_norm = {normalize_query(row["text"]) for row in f4["claimed_samples"]}
    pool_norm = {entry.normalized_text for entry in pool}
    if not claimed_norm <= pool_norm:
        raise ProtocolError("published F4 claimed text is absent from pinned archive pool")
    excluded_keys = {entry.key for entry in canonical_spent}
    excluded_text = set(claimed_norm)
    arms: list[dict] = []
    arm_entries: list[list[OewnEntry]] = []
    for seed in OEWN_SEEDS:
        unique: dict[str, OewnEntry] = {}
        for entry in sorted(pool, key=lambda item: item.key):
            if entry.key in excluded_keys or entry.normalized_text in excluded_text:
                continue
            unique.setdefault(entry.normalized_text, entry)
        survivors = sorted(unique.values(), key=lambda item: item.key)
        selected = random.Random(seed).sample(survivors, OEWN_SAMPLE_SIZE)
        serialized = "\n".join(entry.key.serial() for entry in selected).encode("utf-8") + b"\n"
        arms.append({
            "seed": seed, "sample_size": len(selected), "survivor_pool": len(survivors),
            "ordered_key_sha256": sha256_bytes(serialized),
        })
        arm_entries.append(selected)
        excluded_keys.update(entry.key for entry in selected)
        excluded_text.update(entry.normalized_text for entry in selected)
    receipt = {
        "schema": "when_to_ask_oewn_keys.v1", "archive_sha256": OEWN_ARCHIVE_SHA256,
        "f4_seed": F4_SEED, "canonical_spent_keys": len(canonical_spent),
        "published_claimed_texts": len(claimed_norm), "runtime": sys.implementation.name,
        "python_version": sys.version, "arms": arms,
        "limitation": "F4 did not retain its keys/runtime; absolute overlap with 966 unpublished non-claims is unprovable.",
    }
    return receipt, arm_entries


def reconstruct_oewn_samples(archive: Path) -> dict:
    """Public construction-only key receipt."""
    receipt, _entries = _oewn_samples(archive)
    return receipt


def score_oewn(resolve, index: GraphIndex, archive: Path) -> tuple[dict, list[dict]]:
    receipt, arms = _oewn_samples(archive)
    scored_arms: list[dict] = []
    raw_rows: list[dict] = []
    for arm_info, entries in zip(receipt["arms"], arms, strict=True):
        claimed = 0
        for entry in entries:
            outcome = resolve(entry.text, index)
            kind = _kind_name(outcome)
            is_claim = kind in {"BIND", "ASK"}
            claimed += is_claim
            raw_rows.append({
                "seed": arm_info["seed"],
                "key_sha256": sha256_bytes(entry.key.serial().encode("utf-8")),
                "kind": kind,
                "bound": outcome.bound,
                "candidates": list(outcome.candidates),
            })
        scored_arms.append({
            **arm_info,
            "claimed": claimed,
            "false_positive_rate": claimed / len(entries),
        })
    rates = [arm["false_positive_rate"] for arm in scored_arms]
    total_claimed = sum(arm["claimed"] for arm in scored_arms)
    adjudication = {
        "fired": total_claimed / (len(arms) * OEWN_SAMPLE_SIZE) <= 0.030,
        "pooled_claimed": total_claimed,
        "pooled_of": len(arms) * OEWN_SAMPLE_SIZE,
        "pooled_rate": total_claimed / (len(arms) * OEWN_SAMPLE_SIZE),
        "threshold": 0.030,
        "mean_rate": statistics.fmean(rates),
        "population_stddev": statistics.pstdev(rates),
        "arms": scored_arms,
        "selection_limitation": receipt["limitation"],
    }
    return adjudication, raw_rows


def _require_clean_candidate(manifest: dict, prereg_commit: str, candidate_commit: str) -> dict:
    if _git("rev-parse", "HEAD") != candidate_commit:
        raise ProtocolError("HEAD must equal candidate commit")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", prereg_commit, candidate_commit],
        cwd=REPO, check=False,
    )
    if ancestor.returncode != 0:
        raise ProtocolError("preregistration commit is not an ancestor of candidate")
    if _git("status", "--porcelain"):
        raise ProtocolError("whole worktree must be clean before one-shot scoring")
    allowed = set(manifest["allowed_candidate_paths"])
    changed = set(_git("diff", "--name-only", prereg_commit, candidate_commit).splitlines())
    if not changed or not changed <= allowed:
        raise ProtocolError(f"candidate diff {sorted(changed)} is empty or outside {sorted(allowed)}")
    dirty = _git("status", "--porcelain", "--", *sorted(allowed))
    if dirty:
        raise ProtocolError("score-affecting candidate paths are dirty")
    return {"allowed_paths": sorted(allowed), "changed_paths": sorted(changed)}


def run_score(prereg_commit: str, candidate_commit: str, archive: Path) -> dict:
    """The only scoring entrypoint. It writes raw output and no compact view."""
    if RAW_PATH.exists() or COMPACT_PATH.exists():
        raise ProtocolError("result path already exists; one-shot output is never overwritten")
    construction = validate_structure()
    manifest = verify_manifest()
    diff_receipt = _require_clean_candidate(manifest, prereg_commit, candidate_commit)
    resolve, resolve_negative = _candidate_resolvers()
    index = default_index()
    corpus = records([REPO / "data"])
    rows, adjudication = score_holdout(resolve, resolve_negative, index, corpus)
    q4, oewn_rows = score_oewn(resolve, index, archive)
    adjudication["Q4"] = q4
    adjudication["shipping_conjunction"] = all(
        adjudication[f"Q{i}"]["fired"] for i in range(1, 7)
    )
    # OEWN text is held only in memory; raw rows expose one-way key digests.
    result = {
        "schema": "when_to_ask_result.raw.v1", "design": DESIGN,
        "construction": construction, "provenance": {
            "prereg_commit": prereg_commit, "prereg_tree": _git("rev-parse", f"{prereg_commit}^{{tree}}"),
            "candidate_commit": candidate_commit, "candidate_tree": _git("rev-parse", f"{candidate_commit}^{{tree}}"),
            "runtime": sys.version, "candidate_diff": diff_receipt,
        },
        "oewn_rows": oewn_rows, "adjudication": adjudication, "rows": rows,
    }
    with RAW_PATH.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    return result


def compact(raw_path: Path = RAW_PATH, out_path: Path = COMPACT_PATH) -> dict:
    if not raw_path.is_file():
        raise ProtocolError("raw ledger does not exist")
    if _git("status", "--porcelain", "--", str(raw_path.relative_to(REPO))):
        raise ProtocolError("raw ledger must be committed before compacting")
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    if raw.get("schema") != "when_to_ask_result.raw.v1":
        raise ProtocolError("wrong raw schema")
    view = {key: value for key, value in raw.items() if key != "rows"}
    view["schema"] = "when_to_ask_result.compact.v1"
    view["raw_canonical_lf_sha256"] = file_sha256(raw_path)
    view["row_count"] = len(raw["rows"])
    out_path.write_text(json.dumps(view, indent=2) + "\n", encoding="utf-8", newline="\n")
    return view


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    score = sub.add_parser("score")
    score.add_argument("--prereg-commit", required=True)
    score.add_argument("--candidate-commit", required=True)
    score.add_argument("--wordnet", type=Path, required=True)
    sub.add_parser("compact")
    args = parser.parse_args(argv)
    if args.command == "validate":
        receipt = validate_structure()
        manifest = verify_manifest()
        receipt["provenance"] = {
            "base_commit": manifest["base_commit"],
            "base_tree": manifest["base_tree"],
            "scripts_tree": manifest["scripts_tree"]["git_tree"],
            "existing_inputs": len(manifest["existing_inputs"]),
            "data_trees": {
                entry["path"]: entry["git_tree"] for entry in manifest["data_trees"]
            },
        }
        print(json.dumps(receipt, indent=2))
    elif args.command == "score":
        print(json.dumps(run_score(args.prereg_commit, args.candidate_commit, args.wordnet)["adjudication"], indent=2))
    else:
        print(json.dumps(compact(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
