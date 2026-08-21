#!/usr/bin/env python3
"""The provenance-graph assembler: DESIGN-retraction-closure §4, built.

Writes ``reports/provenance_graph.jsonl`` — one JSON record per line, each
validating against ``schema/provenance-graph.schema.json`` — from nothing
but the committed bytes of this repository. The graph is the substrate the
radius tool traverses; §1's question (*if this input is wrong, what exactly
falls?*) is answerable only if the chain seeds → corpora → ledgers →
published claims exists as an object rather than as a habit.

**Who counts as a writer** (§4's dated clarification). ``inferred: false``
belongs to an edge whose emitter is a deterministic function of committed
bytes run at generation time. Two emitters qualify: a report writer naming
its own inputs (the ``provenance`` block that ``report_provenance.py``
factored out, and ``proof_correspondence.json``'s older ``inputs`` map),
and *this assembler* emitting structural and citation edges from a fixed,
committed scan over committed text. Both are reproducible byte-for-byte,
which is exactly what R5 asks of them. ``inferred: true`` is reserved for
an edge a writer should have emitted and did not — the committed
``reports/decompositions.json`` predates the convention and is the design's
standing example — and those edges are excluded from every scored clause,
including closure traversal.

**The scan never reads the answer key.** R2 compares this graph's computed
closure against an independently hand-audited list committed before this
module existed. An assembler that read those hand-audited files would make
the clause a tautology, so this module opens none of them, names none of
them, and contains no path that could reach them; a source-scanning test in
``tests/test_retraction_closure.py`` keeps it that way — the same
mechanical prohibition the bounded-closure suite puts on world-name
literals in its generic layer. The rule is stronger than "do not read":
even the filenames are absent, so the ban cannot be quietly relaxed into a
comment that a later reader treats as permission.

**v1 emits no ``ledger_section`` nodes.** The kind is in the schema's
frozen enum and stays unused this slice: a ledger's internal sections are
not addressed by any published claim in the repository today, and inventing
an addressing scheme for them would add denominator without adding
information. The consequence is stated rather than hidden: **R1's
denominator in v1 is edges into ``report_ledger`` nodes only.** The clause
reads "edges into ``report_ledger`` and ``ledger_section`` nodes"; the
second set is empty, so the fraction this module prints is R1 as computed
over the first.

**Determinism (R5).** Sorted node records then sorted edge records, LF
newlines, canonical JSON (sorted keys, compact separators). Nothing here
reads a clock, a hostname, an absolute path, or git state; ``first_seen_build``
is the graph's own format tag, not a build timestamp, for the same reason
``emitted_at_generation`` in a provenance block is a flag and not a date.

Node id conventions, frozen:

``seed:scripts/seed_<x>.py``       every ``scripts/seed_*.py``
``corpus:data/<d>/nodes.json``     every ``data/*/nodes.json`` and
                                   ``data_holdout/*/nodes.json``
``external:<source_id>``           every ``data_sources/manifest.json`` source
``ledger:reports/<name>.json``     the four registered ledgers, plus
                                   ``reports/proof_correspondence.json``
``claim:<file>#<heading>``         one per markdown section, ``~<n>``
                                   appended for the nth duplicate heading
                                   within a file, in document order

Edge ids are ``e:<from>-><to>:<relation>``, truncated and hash-suffixed past
200 characters so a long claim heading cannot produce an unbounded key.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

#: The graph's format tag, written into every node's ``first_seen_build``.
#: A version, not a timestamp: R5 forbids anything that differs between two
#: clean builds of the same bytes.
FORMAT_TAG = "v1"

GRAPH_RELATIVE_PATH = "reports/provenance_graph.jsonl"

#: Longest edge_id emitted verbatim; past this the id is a stable prefix
#: plus a digest of the full key, which keeps ids unique without letting a
#: section heading set the key length.
MAX_EDGE_ID = 200

EMITTER_STRUCTURE = "provenance_graph.py/structure"
EMITTER_CITATION = "provenance_graph.py/citation-scan"
EMITTER_RECONSTRUCTED = "provenance_graph.py/reconstructed"

#: ledger repo-path -> writer repo-path. The same knowledge
#: ``check_report_regeneration.REGISTRY`` holds, plus the older
#: ``proof_correspondence.json``, which set the precedent §4 cites. It is
#: duplicated rather than imported: the regeneration check owns an
#: *executable* mapping (writer plus argv) and this module owns a
#: *descriptive* one, and coupling the graph's shape to a check's CLI would
#: make a change to that CLI a change to the graph.
LEDGER_WRITERS: dict[str, str] = {
    "reports/compression.json": "scripts/measure_compression.py",
    "reports/decompositions.json": "scripts/decompose.py",
    "reports/proof_correspondence.json": "scripts/proof_correspondence.py",
    "reports/signature_matches.json": "scripts/match_signatures.py",
    "reports/specializations.json": "scripts/specialize.py",
}

#: The four core ledgers of §3 — the ones that carried no provenance at all
#: and that the citation scan's basename, writer-name, field-name, and stem
#: rules resolve to. ``proof_correspondence.json`` is a ledger node and a
#: citation target by path and basename, but it owns no stem vocabulary.
CORE_LEDGERS = (
    "reports/compression.json",
    "reports/decompositions.json",
    "reports/signature_matches.json",
    "reports/specializations.json",
)

#: R-e's stem vocabulary: the plain English word a claim uses when it cites
#: a ledger without naming the file. Case-insensitive, word-bounded.
LEDGER_STEMS: dict[str, tuple[str, ...]] = {
    "reports/compression.json": ("compression",),
    "reports/decompositions.json": ("decomposition", "decompositions"),
    "reports/specializations.json": ("specialization", "specializations"),
    "reports/signature_matches.json": (
        "signature match",
        "signature matches",
        "typed twin",
    ),
}

#: Documents whose sections become ``release_claim`` nodes. ANALYSIS.md is
#: handled separately as ``analysis_claim``; the two kinds exist because §6
#: R3's coverage floor is stated over *the current release's* claims.
RELEASE_DOC_GLOBS = (
    "README.md",
    "docs/RELEASE-*.md",
    "docs/ROADMAP-*.md",
    "docs/DESIGN-*.md",
    "docs/TRIAGE-*.md",
    "docs/BACKLOG.md",
    "docs/DISCOVERIES.md",
    "docs/blog/*.md",
)

ANALYSIS_DOC = "experiments/ANALYSIS.md"

HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^ {0,3}(```|~~~)")
BACKTICKED = re.compile(r"`([^`\n]+)`")

#: R-f's candidate glob: a slash-bearing path token carrying at least one
#: ``*``. Backticked or bare — the repository writes ``reports/*.json`` both
#: ways and a rule that only saw one spelling would be a typography rule.
GLOB_TOKEN = re.compile(r"[A-Za-z0-9_.*-]*(?:/[A-Za-z0-9_.*-]+)+")

#: R-d's component split: everything that cannot appear in an identifier.
#: ``constituents[].owners`` is three characters of punctuation around two
#: real field names, and the punctuation is markdown's way of showing a
#: path into a record, not part of either name.
NON_IDENTIFIER = re.compile(r"[^A-Za-z0-9_]+")


# ---------------------------------------------------------------------------
# Canonical bytes
# ---------------------------------------------------------------------------


def canonical_json(obj: object) -> str:
    """One JSON spelling for everything written or digested.

    Copied from ``closure_worlds.canonical_json`` rather than imported, for
    the reason ``report_provenance.sha256_lf_file`` gives about its own
    copy: the core artifact chain must not acquire a dependency on a
    bounded-worlds instrument's lifetime.
    """

    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def sha256_lf_bytes(data: bytes) -> str:
    """Canonical-LF SHA-256 of raw bytes."""

    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def sha256_lf_file(path: Path) -> str:
    """Canonical-LF SHA-256 of a file: CRLF folded before hashing, so a
    Windows checkout and a Linux checkout agree on a frozen file's identity."""

    return sha256_lf_bytes(path.read_bytes())


def read_lf_text(path: Path) -> str:
    """File text with newlines normalised to LF."""

    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def repo_path(path: Path, repo_root: Path) -> str:
    """Repo-relative POSIX spelling — never an absolute path (R5)."""

    return Path(path).resolve().relative_to(Path(repo_root).resolve()).as_posix()


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------


def node_record(
    node_id: str, kind: str, content_sha256: str, produced_by: str
) -> dict:
    return {
        "record": "node",
        "node_id": node_id,
        "kind": kind,
        "content_sha256": content_sha256,
        "produced_by": produced_by,
        "first_seen_build": FORMAT_TAG,
    }


def edge_id_for(from_node: str, to_node: str, relation: str) -> str:
    """``e:<from>-><to>:<relation>``, hash-suffixed past ``MAX_EDGE_ID``."""

    key = f"e:{from_node}->{to_node}:{relation}"
    if len(key) <= MAX_EDGE_ID:
        return key
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]
    return f"{key[:MAX_EDGE_ID - 17]}~{digest}"


def edge_record(
    from_node: str, to_node: str, relation: str, emitted_by: str, inferred: bool
) -> dict:
    return {
        "record": "edge",
        "edge_id": edge_id_for(from_node, to_node, relation),
        "from_node": from_node,
        "to_node": to_node,
        "relation": relation,
        "emitted_by": emitted_by,
        "inferred": inferred,
    }


# ---------------------------------------------------------------------------
# Markdown sections
# ---------------------------------------------------------------------------


def split_sections(text: str) -> list[tuple[str, str]]:
    """``[(heading_text, section_text)]`` in document order.

    A section is a heading line of any level plus every line until the next
    heading of any level, so nesting does not nest: a claim under an ``##``
    is not silently attributed to the ``#`` above it. Headings inside fenced
    code blocks are not headings — a shell comment in an example block would
    otherwise mint a claim node that no reader would recognise as one.

    ``section_text`` includes the heading line, because the heading is part
    of what a claim asserts and part of what the citation scan should see.
    """

    lines = text.split("\n")
    sections: list[tuple[str, list[str]]] = []
    in_fence = False
    fence_marker = ""
    for line in lines:
        fence = FENCE.match(line)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence, fence_marker = True, marker
            elif marker == fence_marker:
                in_fence, fence_marker = False, ""
        heading = None if in_fence else HEADING.match(line)
        if heading:
            sections.append((heading.group(2), [line]))
        elif sections:
            sections[-1][1].append(line)
    return [(title, "\n".join(body)) for title, body in sections]


def claim_node_ids(doc_rel: str, sections: list[tuple[str, str]]) -> list[str]:
    """Node ids for one document's sections, duplicates disambiguated.

    A repeated heading ("Honest limits carried forward" appears in most
    release notes, and twice within some) gets ``~1``, ``~2``, … in document
    order. The suffix is positional, not content-derived, so a section whose
    prose is edited keeps its identity while a section that moves does not.
    """

    seen: Counter[str] = Counter()
    ids: list[str] = []
    for title, _ in sections:
        seen[title] += 1
        n = seen[title]
        suffix = "" if n == 1 else f"~{n}"
        ids.append(f"claim:{doc_rel}#{title}{suffix}")
    return ids


# ---------------------------------------------------------------------------
# Field vocabularies (citation rule R-d)
# ---------------------------------------------------------------------------


def ledger_field_vocabularies(repo_root: Path) -> dict[str, set[str]]:
    """Each core ledger's field names, read from its committed bytes.

    Top-level keys plus the keys of dict items in top-level lists — one
    level, because a deeper walk would drag in the field names of nested
    records that no prose ever cites by name.
    """

    vocab: dict[str, set[str]] = {}
    for rel in CORE_LEDGERS:
        path = repo_root / rel
        if not path.is_file():
            continue
        doc = json.loads(read_lf_text(path))
        names: set[str] = set()
        if isinstance(doc, dict):
            names.update(doc)
            for value in doc.values():
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            names.update(item)
        vocab[rel] = names
    return vocab


def unique_field_owners(vocab: dict[str, set[str]]) -> dict[str, str]:
    """Field name -> the single ledger that owns it.

    A name in two or more vocabularies is ambiguous and never makes an
    edge. The exclusion is arithmetic, not a hand-maintained stoplist: a
    stoplist would have to be edited every time a ledger gained a field, and
    the edit would be made by whoever wanted the edge.
    """

    owners: Counter[str] = Counter()
    for names in vocab.values():
        for name in names:
            owners[name] += 1
    return {
        name: rel
        for rel, names in vocab.items()
        for name in names
        if owners[name] == 1
    }


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def _external_digest(source: dict) -> str | None:
    """The manifest-recorded digest for one external source.

    Most entries pin a single archive by ``sha256``. The four git/HF-pinned
    entries pin a *file list* instead, each file with its own digest; their
    node identity is the digest of those recorded digests, in canonical
    form. Either way the value is read from the manifest and never computed
    from a downloaded artifact — the archives are gitignored, and a node
    whose identity depended on a local download would not survive R5.
    """

    recorded = source.get("sha256")
    if isinstance(recorded, str) and re.fullmatch(r"[0-9a-f]{64}", recorded):
        return recorded
    files = source.get("files")
    if isinstance(files, list):
        digests = sorted(
            f["sha256"]
            for f in files
            if isinstance(f, dict) and isinstance(f.get("sha256"), str)
        )
        if digests:
            return hashlib.sha256(
                canonical_json(digests).encode("utf-8")
            ).hexdigest()
    return None


def _ledger_inputs(doc: object) -> list[str]:
    """The input paths a ledger names about itself, from either convention.

    ``provenance.inputs`` is the block ``report_provenance`` factored out
    (a list of ``{path, sha256_lf}``); ``inputs`` is
    ``proof_correspondence.json``'s older path->digest map, which §3 credits
    as the precedent. A ledger naming neither returns nothing, and its
    edges — if any — are somebody's reconstruction.
    """

    if not isinstance(doc, dict):
        return []
    block = doc.get("provenance")
    if isinstance(block, dict) and isinstance(block.get("inputs"), list):
        return [
            row["path"]
            for row in block["inputs"]
            if isinstance(row, dict) and isinstance(row.get("path"), str)
        ]
    older = doc.get("inputs")
    if isinstance(older, dict):
        return [key for key in older if isinstance(key, str)]
    return []


def build_graph(
    repo_root: Path | str = REPO_ROOT, out_path: Path | None = None
) -> Path:
    """Assemble the graph and write it (default: the committed path).

    Returns the path written. Everything is derived from committed bytes;
    calling this twice on an unchanged tree produces identical bytes, which
    is R5 and is asserted in the suite rather than promised here.

    ``out_path`` exists because the committed graph is an ADJUDICATION
    input once certificates pin its hash: a build over a later tree is a
    different graph, and writing it over the committed one silently breaks
    every certificate's recheck. Callers that build for inspection (the
    gate tests) build to a temp path; only a deliberate re-adjudication
    writes the committed path.
    """

    repo_root = Path(repo_root).resolve()
    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def add_node(node: dict) -> None:
        nodes[node["node_id"]] = node

    def add_edge(
        from_node: str,
        to_node: str,
        relation: str,
        emitted_by: str,
        inferred: bool,
    ) -> None:
        edges.append(edge_record(from_node, to_node, relation, emitted_by,
                                 inferred))

    # -- seeds ------------------------------------------------------------
    seed_ids: dict[str, str] = {}
    for path in sorted((repo_root / "scripts").glob("seed_*.py")):
        rel = repo_path(path, repo_root)
        node_id = f"seed:{rel}"
        add_node(node_record(node_id, "seed_script", sha256_lf_file(path), ""))
        seed_ids[path.stem[len("seed_"):]] = node_id

    # -- corpora ----------------------------------------------------------
    corpus_ids: dict[str, str] = {}
    corpus_docs: dict[str, dict] = {}
    corpus_paths = sorted((repo_root / "data").glob("*/nodes.json")) + sorted(
        (repo_root / "data_holdout").glob("*/nodes.json")
    )
    for path in corpus_paths:
        rel = repo_path(path, repo_root)
        node_id = f"corpus:{rel}"
        # A seed exists when scripts/seed_<dirname>.py does; several corpora
        # were authored before that convention and legitimately have none,
        # and produced_by "" says so rather than guessing a producer.
        seed_id = seed_ids.get(path.parent.name, "")
        produced_by = (
            repo_path(repo_root / seed_id[len("seed:"):], repo_root)
            if seed_id
            else ""
        )
        add_node(
            node_record(node_id, "corpus_file", sha256_lf_file(path),
                        produced_by)
        )
        corpus_ids[rel] = node_id
        corpus_docs[rel] = json.loads(read_lf_text(path))
        if seed_id:
            # Structural, not reconstructed: the committed layout fixes this
            # edge, and §4's clarification licenses the assembler as the
            # writer of edges that are a deterministic function of it.
            add_edge(node_id, seed_id, "derived_from", EMITTER_STRUCTURE,
                     False)

    # -- external sources -------------------------------------------------
    external_urls: dict[str, str] = {}
    manifest_path = repo_root / "data_sources" / "manifest.json"
    if manifest_path.is_file():
        manifest = json.loads(read_lf_text(manifest_path))
        for source in manifest.get("sources", []):
            digest = _external_digest(source)
            if digest is None:
                continue
            node_id = f"external:{source['id']}"
            add_node(node_record(node_id, "external_source", digest, ""))
            url = source.get("url")
            if isinstance(url, str) and url:
                external_urls.setdefault(url, node_id)

    # -- corpus pinned_from external --------------------------------------
    # The only mechanically derivable link between a committed corpus and a
    # pinned outside archive: a statement's own provenance entry carries the
    # source's URL, and the manifest carries the same URL against its id.
    # Exact string equality, both sides committed. Where a corpus's citation
    # keys have no manifest counterpart (every hand-authored discipline),
    # nothing is emitted — a guessed pin is worse than a missing one.
    for rel, doc in corpus_docs.items():
        urls: set[str] = set()
        for node in doc.get("statement_nodes", []) if isinstance(doc, dict) else []:
            for entry in node.get("provenance", []) or []:
                if isinstance(entry, dict) and isinstance(entry.get("url"), str):
                    urls.add(entry["url"])
        for url in sorted(urls):
            if url in external_urls:
                add_edge(corpus_ids[rel], external_urls[url], "pinned_from",
                         EMITTER_STRUCTURE, False)

    # -- ledgers ----------------------------------------------------------
    ledger_ids: dict[str, str] = {}
    for rel, writer in sorted(LEDGER_WRITERS.items()):
        path = repo_root / rel
        if not path.is_file():
            continue
        node_id = f"ledger:{rel}"
        add_node(node_record(node_id, "report_ledger", sha256_lf_file(path),
                             writer))
        ledger_ids[rel] = node_id
        inputs = _ledger_inputs(json.loads(read_lf_text(path)))
        if inputs:
            for input_rel in sorted(set(inputs)):
                target = corpus_ids.get(input_rel)
                if target:
                    # Emitted by the writer itself at generation time: the
                    # ledger's own block is the edge, in ledger form.
                    add_edge(node_id, target, "derived_from", writer, False)
        else:
            # §4's standing example. decompositions.json is the declared
            # pre-scale snapshot (TRIAGE-v0.11 gate table row 6) and predates
            # provenance blocks entirely; regenerating it to gain one would
            # destroy the snapshot the decision preserved. So its input
            # edges are reconstructed from the writer's known corpus glob
            # and marked inferred, which excludes them from every scored
            # clause including closure traversal.
            for input_rel in sorted(corpus_ids):
                if input_rel.startswith("data/"):
                    add_edge(node_id, corpus_ids[input_rel], "derived_from",
                             EMITTER_RECONSTRUCTED, True)

    # -- claims -----------------------------------------------------------
    documents: list[tuple[str, str]] = [(ANALYSIS_DOC, "analysis_claim")]
    release_docs: set[str] = set()
    for pattern in RELEASE_DOC_GLOBS:
        for path in repo_root.glob(pattern):
            if path.is_file():
                release_docs.add(repo_path(path, repo_root))
    documents.extend((rel, "release_claim") for rel in sorted(release_docs))

    vocab = ledger_field_vocabularies(repo_root)
    field_owner = unique_field_owners(vocab)
    stem_patterns = {
        rel: re.compile(
            r"\b(?:" + "|".join(re.escape(s) for s in stems) + r")\b",
            re.IGNORECASE,
        )
        for rel, stems in LEDGER_STEMS.items()
    }
    writer_names = {
        Path(writer).name: rel
        for rel, writer in LEDGER_WRITERS.items()
        if rel in ledger_ids
    }
    basenames = {
        Path(rel).name: rel for rel in ledger_ids
    }
    artifact_by_path: dict[str, str] = {}
    artifact_by_path.update(
        {rel: node_id for rel, node_id in corpus_ids.items()}
    )
    artifact_by_path.update(
        {rel: node_id for rel, node_id in ledger_ids.items()}
    )
    artifact_by_path.update(
        {
            node_id[len("seed:"):]: node_id
            for node_id in seed_ids.values()
        }
    )

    for doc_rel, kind in documents:
        path = repo_root / doc_rel
        if not path.is_file():
            continue
        text = read_lf_text(path)
        sections = split_sections(text)
        ids = claim_node_ids(doc_rel, sections)
        for node_id, (_, body) in zip(ids, sections):
            add_node(
                node_record(
                    node_id,
                    kind,
                    sha256_lf_bytes(body.encode("utf-8")),
                    doc_rel,
                )
            )
            for target, rule in _cited_artifacts(
                body, artifact_by_path, basenames, writer_names, field_owner,
                stem_patterns,
            ):
                add_edge(node_id, target, "derived_from",
                         f"{EMITTER_CITATION}/{rule}", False)

    return _write(repo_root, nodes, edges, out_path)


def _cited_artifacts(
    body: str,
    artifact_by_path: dict[str, str],
    basenames: dict[str, str],
    writer_names: dict[str, str],
    field_owner: dict[str, str],
    stem_patterns: dict[str, re.Pattern[str]],
) -> list[str]:
    """THE CITATION SCAN. Five rules, frozen, in force for every claim.

    A claim ``derived_from`` an artifact means the claim's text cites that
    artifact, by one of exactly these five spellings. The rules are listed
    here and nowhere else, because a scan whose rules live in the commit
    message can be widened on the day a closure comes up short.

    - **R-a — repo-relative path.** The section names a known ledger,
      corpus, or seed by its path (``reports/compression.json``,
      ``data/logic/nodes.json``, ``scripts/seed_logic.py``).
    - **R-b — ledger basename.** The section names a ledger file without
      its directory (``compression.json``).
    - **R-c — writer script name.** The section names a registered writer
      (``measure_compression.py``); the edge goes to the ledger that writer
      produces, since citing the producer is citing the product.
    - **R-d — uniquely owned field name, backticked.** A backticked token is
      split on every non-identifier character (``.``, ``[``, ``]``, ``/``,
      ``(``, ``)`` …) and each resulting component is matched against the
      field names that belong to exactly ONE of the four core ledgers'
      committed vocabularies. The split is why ``constituents[].owners``
      counts as a citation of ``constituents``: markdown's punctuation is
      how prose spells a path *into* a record, and the field name is the
      part that names something. A component in two or more vocabularies is
      ambiguous and never makes an edge — the exclusion is computed from the
      ledger bytes at build time, not maintained as a stoplist. Backticks
      are still required: the same word in running prose is English, not a
      reference.
    - **R-e — the ledger's stem as a plain word,** case-insensitive:
      "compression", "decomposition(s)", "specialization(s)", and
      "signature match(es)" / "typed twin". This is the rule that catches
      the way the repository's prose actually cites its own measurements,
      which is almost never by filename. It is also the broadest rule here,
      and the one whose cost shows up in a closure size rather than in a
      miss; it is left exactly as registered.
    - **R-f — glob expansion.** A slash-bearing path token containing ``*``
      (``reports/*.json``, ``data/*/nodes.json``, backticked or bare) is
      expanded against this graph's own node set, and every artifact the
      glob matches gets an edge. The repository's release notes cite whole
      directories this way — a table row reading ``reports/*.json`` is a
      citation of five ledgers — and a scan that only understood literal
      paths would score that row as citing nothing. ``*`` does not cross a
      path separator, so the glob means what its writer meant.

    All six emit ``inferred: false`` under §4's clarification: the scan is
    a fixed, committed function of committed text, run at generation time,
    and this assembler is the edges' writer. Deduplication is by target, so
    a section that cites a ledger five ways still yields one edge.

    Returns ``[(node_id, rule)]``. The rule rides out on the edge's
    ``emitted_by`` as ``provenance_graph.py/citation-scan/R-x``, and is
    **diagnostics only**: it names which rule would have sufficed alone,
    alphabetically first when several match, so the post-mortem can
    attribute a closure's width to the rules that produced it. It cannot
    change the edge set — every rule writes into one target set, and the
    tag is chosen after that set is closed.
    """

    hits: dict[str, str] = {}

    def record(node_id: str, rule: str) -> None:
        # Alphabetically first rule wins. The tag is diagnostics: it names
        # which rule would have sufficed on its own, and cannot change which
        # edges exist, because every rule writes into the same target set.
        current = hits.get(node_id)
        if current is None or rule < current:
            hits[node_id] = rule

    for rel, node_id in artifact_by_path.items():          # R-a
        if rel in body:
            record(node_id, "R-a")
    for name, rel in basenames.items():                     # R-b
        if name in body:
            record(f"ledger:{rel}", "R-b")
    for name, rel in writer_names.items():                  # R-c
        if name in body:
            record(f"ledger:{rel}", "R-c")
    for token in BACKTICKED.findall(body):                  # R-d
        for component in NON_IDENTIFIER.split(token.strip()):
            owner = field_owner.get(component)
            if owner:
                record(f"ledger:{owner}", "R-d")
    for rel, pattern in stem_patterns.items():              # R-e
        if pattern.search(body):
            record(f"ledger:{rel}", "R-e")
    for token in sorted(set(GLOB_TOKEN.findall(body))):     # R-f
        if "*" not in token:
            continue
        pattern = _glob_pattern(token)
        for rel, node_id in artifact_by_path.items():
            if pattern.fullmatch(rel):
                record(node_id, "R-f")
    return sorted(hits.items())


def _glob_pattern(token: str) -> re.Pattern[str]:
    """Compile one repo-relative glob, ``*`` stopping at a path separator.

    ``fnmatch`` would let ``reports/*.json`` swallow
    ``reports/radius/x.cert.json``, which is not what a reader writing that
    glob means. One segment, one star.
    """

    return re.compile(
        "".join(
            "[^/]*" if part == "*" else re.escape(part)
            for part in re.split(r"(\*)", token)
        )
    )


def _write(
    repo_root: Path,
    nodes: dict[str, dict],
    edges: list[dict],
    out_path: Path | None = None,
) -> Path:
    """Write the graph: sorted nodes, then sorted edges, LF, canonical JSON."""

    # One edge per (from, to, relation). If two rules produced the same
    # triple, the emitted one wins over the reconstructed one and the tie
    # after that breaks on emitter name — deterministic, and never silently
    # downgrading a writer-emitted edge to an inference.
    best: dict[tuple[str, str, str], dict] = {}
    for edge in edges:
        key = (edge["from_node"], edge["to_node"], edge["relation"])
        rank = (edge["inferred"], edge["emitted_by"])
        current = best.get(key)
        if current is None or rank < (current["inferred"],
                                      current["emitted_by"]):
            best[key] = edge

    known = set(nodes)
    records = [nodes[node_id] for node_id in sorted(nodes)]
    records.extend(
        edge
        for edge in sorted(best.values(), key=lambda e: e["edge_id"])
        # A dangling edge would let a closure walk off the graph; both
        # endpoints are nodes this build emitted, or the edge is not real.
        if edge["from_node"] in known and edge["to_node"] in known
    )

    out = Path(out_path) if out_path is not None else (
        repo_root / GRAPH_RELATIVE_PATH
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(canonical_json(record) + "\n" for record in records)
    out.write_bytes(payload.encode("utf-8"))
    return out


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def summarize(graph_path: Path) -> dict:
    """Counts and R1, read back from the written file rather than from
    memory: the summary should describe the artifact, not the intent."""

    node_kinds: Counter[str] = Counter()
    relations: Counter[str] = Counter()
    emitters: Counter[str] = Counter()
    kind_of: dict[str, str] = {}
    records = [
        json.loads(line)
        for line in graph_path.read_text(encoding="utf-8").splitlines()
    ]
    for record in records:
        if record["record"] == "node":
            node_kinds[record["kind"]] += 1
            kind_of[record["node_id"]] = record["kind"]
    into_ledger = 0
    into_ledger_emitted = 0
    for record in records:
        if record["record"] != "edge":
            continue
        relations[record["relation"]] += 1
        emitters[record["emitted_by"]] += 1
        # R1's denominator: edges into report_ledger nodes. v1 emits no
        # ledger_section nodes, so the clause's second set is empty.
        if kind_of.get(record["to_node"]) in {"report_ledger", "ledger_section"}:
            into_ledger += 1
            if not record["inferred"]:
                into_ledger_emitted += 1
    return {
        "node_kinds": dict(sorted(node_kinds.items())),
        "relations": dict(sorted(relations.items())),
        "emitted_by": dict(sorted(emitters.items())),
        "edges_into_ledgers": into_ledger,
        "edges_into_ledgers_emitted": into_ledger_emitted,
        "r1_fraction": (
            into_ledger_emitted / into_ledger if into_ledger else 0.0
        ),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Build reports/provenance_graph.jsonl")
    ap.add_argument("--repo", default=str(REPO_ROOT))
    args = ap.parse_args(argv)

    path = build_graph(Path(args.repo))
    report = summarize(path)
    print(f"wrote {GRAPH_RELATIVE_PATH}")
    print("nodes by kind:")
    for kind, count in report["node_kinds"].items():
        print(f"  {kind:<16} {count}")
    print("edges by relation:")
    for relation, count in report["relations"].items():
        print(f"  {relation:<16} {count}")
    print("edges by emitter:")
    for emitter, count in report["emitted_by"].items():
        print(f"  {emitter:<40} {count}")
    print(
        f"R1 (emitted edges into report_ledger nodes): "
        f"{report['edges_into_ledgers_emitted']}/{report['edges_into_ledgers']}"
        f" = {report['r1_fraction']:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
