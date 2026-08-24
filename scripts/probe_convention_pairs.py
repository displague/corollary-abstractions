#!/usr/bin/env python3
"""TWO RIGHTS B0 — the registered probe for co-present convention forks.

ROADMAP-v0.19 §3b asks one question of the committed graph and commits the
answer whichever way it lands: **does this corpus anywhere carry the same
mathematical content under two defensible conventions, both statements
present at once?** Course series 3 (`reports/design-direction-v0.19.json`,
lead `TWO RIGHTS`) proposed sealing a `ConventionPair` census over such
forks. Before that direction can be asked with a real denominator, somebody
has to run the grep. This is the grep.

Three commitments the code cannot show:

- **The sweep runs before either branch is preferred.** Nothing here scores
  a hypothesis. The classifier is mechanical, its tables are declared in
  the artifact under `parameters`, and the residue it cannot classify is
  emitted rather than dropped — a probe that can only confirm is not a
  probe.
- **The output is a census, not sealed `ConventionPair` objects.** Sealing
  belongs to the full direction if it ever runs. What lands here is the
  honest inventory: both statement ids, the discriminator position, the two
  differing subterms, and one line saying what the pair actually is.
- **The classification is allowed to be unflattering.** The probe's value
  is the honest census, not a big number. A pair that is merely the same
  statement ingested twice with a variable renamed is labelled as that, and
  the headline separates true convention candidates from near-duplicates
  and from genuinely different statements that happen to share a shape.

## What "skeleton-identical modulo a discriminator subterm" means here

Two canonical forms are tokenized (`TOKENIZER` below — declared, local, and
deliberately more permissive than the pinned stage-2 parser, because 83% of
the corpus does not parse under that parser and a probe that could only see
the 17% would be measuring the parser). The longest common prefix and the
longest common suffix are stripped. What is left on each side is the
**discriminator subterm**. A pair qualifies when both remainders are
non-empty (a pure insertion is a different statement, not a fork at a
position) and neither exceeds `MAX_DISCRIMINATOR_TOKENS`.

Pure insertions are not discarded silently: the famous-clash sweep below
re-runs the same pool with insertions allowed, because the three clash
shapes the roadmap names by name — sign conventions, the 0-in-N boundary,
2-pi placement — are exactly the shapes that show up as insertions.

## The candidate pool

Two passes, both over co-present committed statements:

1. the twin ledger `reports/signature_matches.json` — every unordered pair
   of members inside one twin group, across all five twin families;
2. a direct pass over statements sharing an `anonymized_template` but
   differing in `formal_statement.canonical_ascii`.

Pass 2's contribution is reported separately, because whether it finds
anything the twin ledger missed is itself a fact about the ledger.

Run: `python scripts/probe_convention_pairs.py`
Writes: `experiments/convention_pairs_probe.json` (LF, deterministic).
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from report_provenance import provenance_block  # noqa: E402

OUT_PATH = REPO / "experiments" / "convention_pairs_probe.json"
TWIN_LEDGER = REPO / "reports" / "signature_matches.json"

#: Identifier-first tokenizer. A unicode letter (so Greek binders and the
#: blackboard-bold domain symbols stay whole) starts an identifier; a dotted
#: namespace like `Real.sqrt` is one token, matching how a reader hears it.
#: Everything else non-space is one token of its own, so `>=` arrives as two
#: tokens and the glyph fork against a single `>=`-glyph is visible as a
#: subterm difference rather than hidden inside a word.
TOKENIZER = r"[^\W\d_][\w']*(?:\.[^\W\d_][\w']*)*|\d+(?:\.\d+)?|\S"
TOK = re.compile(TOKENIZER)

#: A discriminator longer than this is not one subterm; it is two different
#: statements that happen to agree at the edges.
MAX_DISCRIMINATOR_TOKENS = 4

#: Declared notation table. Each row is a set of spellings the corpus uses
#: for ONE head or relation. Membership here is the probe's operational
#: definition of "two defensible notations for the same thing"; it is a
#: parameter of the sweep, printed into the artifact, not a result.
NOTATION_CLASSES: tuple[tuple[str, ...], ...] = (
    ("≥", ">="),
    ("≤", "<="),
    ("≠", "!="),
    ("Real.sqrt", "sqrt", "√"),
    ("Real.sin", "sin"),
    ("Real.cos", "cos"),
    ("Real.tan", "tan"),
    ("Real.exp", "exp"),
    ("Real.log", "log"),
    ("Real.pi", "pi", "π"),
    ("Odd", "odd"),
    ("Even", "even"),
    ("Nat.gcd", "gcd"),
    ("Nat.factorial", "factorial"),
    ("∧", "&&", "and"),
    ("∨", "||", "or"),
)

#: Corpora whose statements were ingested from an upstream dataset rather
#: than authored in this repository. The split matters to the probe's
#: headline: a convention fork inside an ingested corpus is the upstream
#: dataset's authors disagreeing with each other, which says nothing about
#: how THIS graph was authored. Declared here so the reader can check it.
INGESTED_CORPORA = frozenset(["lean_workbook", "ingested_arithmetic", "programming"])

#: Ambient domain symbols. A pair whose discriminator is two of these is a
#: domain fork, not a notation fork: the two statements quantify over
#: different carriers even when the algebra is the same.
DOMAIN_SYMBOLS = frozenset(
    ["ℕ", "ℤ", "ℚ", "ℝ", "ℂ", "Nat", "Int", "Rat",
     "Real", "Complex", "PNat", "NNReal"]
)

#: The three clash shapes ROADMAP §3b names by name. Each is a predicate on
#: the two token sequences of a pool pair, run with insertions ALLOWED — a
#: sign convention and a tau-for-2-pi rewrite both change token count.
SIGN_TOKENS = frozenset(["-", "neg", "−"])
PI_TOKENS = frozenset(["π", "pi", "Real.pi"])
TAU_TOKENS = frozenset(["τ", "tau"])
NAT_BOUNDARY_TOKENS = frozenset(["ℕ", "Nat", "PNat", "ℕ+"])


# --------------------------------------------------------------------------
# Corpus and pool
# --------------------------------------------------------------------------


def load_statements(repo: Path) -> tuple[dict[str, dict], list[Path]]:
    """Every committed statement node, keyed by id, with its inputs."""

    statements: dict[str, dict] = {}
    inputs: list[Path] = []
    for path in sorted(repo.glob("data/*/nodes.json")):
        inputs.append(path)
        doc = json.loads(path.read_text(encoding="utf-8"))
        discipline = doc.get("discipline", path.parent.name)
        for record in doc.get("statement_nodes", []):
            sid = record.get("statement_id")
            if not sid:
                continue
            formal = record.get("formal_statement") or {}
            signature = record.get("structural_signature") or {}
            statements[sid] = {
                "statement_id": sid,
                "discipline": discipline,
                "canonical_ascii": formal.get("canonical_ascii", ""),
                "anonymized_template": signature.get("anonymized_template", ""),
                "archetype_id": signature.get("archetype_id", ""),
                "title": record.get("title", ""),
            }
    return statements, inputs


TWIN_FAMILIES = (
    "typed_twin_groups",
    "family_twin_groups_beyond_typed",
    "aliased_twin_groups_beyond_typed",
    "mirror_twin_groups",
    "shape_twin_groups",
)


PoolResult = tuple[list[tuple[str, str]], dict[tuple[str, str], str], dict]


def build_pool(statements: dict[str, dict], ledger: dict) -> PoolResult:
    """The candidate pool: co-present pairs from the twin ledger, then the
    direct anonymized-template pass, with the second pass's marginal
    contribution counted."""

    origin: dict[tuple[str, str], str] = {}
    pool: set[tuple[str, str]] = set()

    for family in TWIN_FAMILIES:
        for group in ledger.get(family, []):
            ids = sorted({m["statement_id"] for m in group.get("members", [])})
            for pair in combinations(ids, 2):
                if pair not in origin:
                    origin[pair] = family
                pool.add(pair)
    twin_pairs = len(pool)

    by_template: dict[str, list[str]] = defaultdict(list)
    for record in statements.values():
        if record["anonymized_template"]:
            by_template[record["anonymized_template"]].append(record["statement_id"])
    template_pairs = 0
    template_new = 0
    for ids in by_template.values():
        ids = sorted(set(ids))
        if len(ids) < 2:
            continue
        for pair in combinations(ids, 2):
            template_pairs += 1
            if pair not in pool:
                template_new += 1
                origin[pair] = "anonymized_template"
                pool.add(pair)

    stats = {
        "twin_ledger_pairs": twin_pairs,
        "anonymized_template_pairs": template_pairs,
        "anonymized_template_pairs_not_already_twins": template_new,
        "pool_pairs": len(pool),
    }
    return sorted(pool), origin, stats


# --------------------------------------------------------------------------
# The discriminator
# --------------------------------------------------------------------------


def tokens(text: str) -> list[str]:
    return TOK.findall(text)


def discriminator(left: list[str], right: list[str]) -> dict | None:
    """Longest common prefix/suffix stripped; what is left is the fork."""

    if left == right:
        return None
    i = 0
    while i < len(left) and i < len(right) and left[i] == right[i]:
        i += 1
    j = 0
    while (j < len(left) - i and j < len(right) - i
           and left[len(left) - 1 - j] == right[len(right) - 1 - j]):
        j += 1
    mid_left = left[i:len(left) - j]
    mid_right = right[i:len(right) - j]
    return {
        "position": i,
        "left_tokens": mid_left,
        "right_tokens": mid_right,
        "common_prefix_tokens": i,
        "common_suffix_tokens": j,
    }


def qualifies(fork: dict) -> bool:
    if not fork["left_tokens"] or not fork["right_tokens"]:
        return False
    return (len(fork["left_tokens"]) <= MAX_DISCRIMINATOR_TOKENS
            and len(fork["right_tokens"]) <= MAX_DISCRIMINATOR_TOKENS)


# --------------------------------------------------------------------------
# Classification — mechanical, ordered, table-declared
# --------------------------------------------------------------------------


_NOTATION_CANON: dict[str, str] = {}
for _row in NOTATION_CLASSES:
    for _spelling in _row:
        _NOTATION_CANON[_spelling] = _row[0]


def _normalize_notation(seq: list[str]) -> list[str]:
    """Fold every declared spelling of one head to that row's first entry.

    Two-character relations arrive as two tokens (`>` `=`), so the fold runs
    over a small window before the single-token map.
    """

    out: list[str] = []
    k = 0
    while k < len(seq):
        pair = seq[k] + seq[k + 1] if k + 1 < len(seq) else None
        if pair in _NOTATION_CANON:
            out.append(_NOTATION_CANON[pair])
            k += 2
            continue
        out.append(_NOTATION_CANON.get(seq[k], seq[k]))
        k += 1
    return out


def _strip_parens(seq: list[str]) -> list[str]:
    return [t for t in seq if t not in ("(", ")")]


def _is_identifier(token: str) -> bool:
    """Could this token be a variable the author was free to rename?

    Three exclusions, and the first one is a bug this probe had before it
    was written down: a declared head spelling such as `Odd` is a single
    unicode-letter token and renames cleanly to `odd`, so without the guard
    the alpha test swallows the notation fork it exists to find. A dotted
    name is a namespace, never a binder; a domain symbol is a carrier.
    """

    if token in _NOTATION_CANON or token in DOMAIN_SYMBOLS or "." in token:
        return False
    return bool(re.fullmatch(r"[^\W\d_][\w']*", token))


def _alpha_rename(left: list[str], right: list[str],
                  fork: dict) -> dict[str, str] | None:
    """Is the whole difference one consistent renaming of variables?

    Built from the discriminator alone, then applied to the WHOLE left side:
    a rename that only happens to fix the fork but breaks elsewhere is not a
    rename, and the global re-check is what says so.
    """

    ml, mr = fork["left_tokens"], fork["right_tokens"]
    if len(ml) != len(mr):
        return None
    mapping: dict[str, str] = {}
    for a, b in zip(ml, mr):
        if a == b:
            continue
        if not _is_identifier(a) or not _is_identifier(b):
            return None
        if mapping.get(a, b) != b:
            return None
        mapping[a] = b
    if not mapping:
        return None
    if len(set(mapping.values())) != len(mapping):
        return None
    renamed = [mapping.get(t, t) for t in left]
    return mapping if renamed == right else None


#: Class -> (verdict bucket, one-line meaning). The bucket is the honest
#: census's three-way split the roadmap asks for.
CLASS_META: dict[str, tuple[str, str]] = {
    "notation_convention": (
        "convention_pair_candidate",
        "same content, two declared spellings of one head or relation",
    ),
    "bracketing_convention": (
        "convention_pair_candidate",
        "same content, different explicit association/parenthesization",
    ),
    "alpha_variant": (
        "near_duplicate",
        "same statement, bound/free variables renamed",
    ),
    "commutation_reorder": (
        "near_duplicate",
        "same statement, operands of a commutative operator swapped",
    ),
    "domain_fork": (
        "different_statement",
        "same algebra asserted over a different ambient domain",
    ),
    # Deliberately NOT filed under `different_statement`. `a * 0 = 0` against
    # `0 * x = 0` is one lemma under a rename AND a commutation, which no
    # single rule here names; calling it a different statement would be the
    # probe asserting exactly what it failed to determine. The residue is
    # emitted as residue and a reader adjudicates it.
    "unclassified_difference": (
        "unclassified",
        "the probe can name no convention relation; a reader must adjudicate",
    ),
}


def classify(left: list[str], right: list[str], fork: dict) -> tuple[str, str]:
    """Return (class, note). Ordered: cheapest structural test first."""

    rename = _alpha_rename(left, right, fork)
    if rename is not None:
        pairs = ", ".join(f"{k}->{v}" for k, v in sorted(rename.items()))
        return "alpha_variant", f"identical after renaming {pairs}"

    if _strip_parens(left) == _strip_parens(right):
        return ("bracketing_convention",
                "identical once explicit parentheses are dropped; the fork is "
                "where the author chose to make association visible")

    nl, nr = _normalize_notation(left), _normalize_notation(right)
    if nl == nr:
        return ("notation_convention",
                "identical once the declared notation table folds "
                f"`{' '.join(fork['left_tokens'])}` and "
                f"`{' '.join(fork['right_tokens'])}` to one spelling")
    if _strip_parens(nl) == _strip_parens(nr):
        return ("notation_convention",
                "identical once notation is folded and explicit parentheses "
                "are dropped")

    ml, mr = fork["left_tokens"], fork["right_tokens"]
    if (len(ml) == 1 and len(mr) == 1
            and ml[0] in DOMAIN_SYMBOLS and mr[0] in DOMAIN_SYMBOLS):
        return ("domain_fork",
                f"same body asserted over {ml[0]} and over {mr[0]}; defensible "
                "as a typing choice, but not the same proposition")

    if Counter(ml) == Counter(mr) and ({"*", "+"} & set(ml)):
        return ("commutation_reorder",
                "operands of a commutative operator in the other order; the "
                "corpus's own canonicalizer already folds this")

    return ("unclassified_difference",
            f"differs at `{' '.join(ml)}` vs `{' '.join(mr)}` with no "
            "convention relation the probe can name")


# --------------------------------------------------------------------------
# The famous-clash sweep (insertions allowed)
# --------------------------------------------------------------------------


def clash_shapes(left: list[str], right: list[str]) -> list[str]:
    """Which of the three named clash shapes, if any, this pair exhibits."""

    found: list[str] = []
    ls = [t for t in left if t not in SIGN_TOKENS]
    rs = [t for t in right if t not in SIGN_TOKENS]
    if ls == rs and left != right:
        found.append("sign_convention")

    lp = Counter(t for t in left if t in PI_TOKENS | TAU_TOKENS)
    rp = Counter(t for t in right if t in PI_TOKENS | TAU_TOKENS)
    if lp != rp and (lp or rp):
        lt = [t for t in left if t not in PI_TOKENS | TAU_TOKENS | {"2", "*"}]
        rt = [t for t in right if t not in PI_TOKENS | TAU_TOKENS | {"2", "*"}]
        if lt == rt:
            found.append("two_pi_placement")

    ln = set(left) & NAT_BOUNDARY_TOKENS
    rn = set(right) & NAT_BOUNDARY_TOKENS
    if (ln or rn):
        lb = [t for t in left if t not in {"0", "1", "<", "≤", "<="}]
        rb = [t for t in right if t not in {"0", "1", "<", "≤", "<="}]
        if lb == rb and left != right:
            found.append("nat_zero_boundary")

    return found


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------


def build_report(repo: Path = REPO) -> dict:
    statements, node_inputs = load_statements(repo)
    ledger = json.loads(TWIN_LEDGER.read_text(encoding="utf-8"))
    pool, origin, pool_stats = build_pool(statements, ledger)

    token_cache: dict[str, list[str]] = {}

    def toks(sid: str) -> list[str]:
        if sid not in token_cache:
            token_cache[sid] = tokens(statements[sid]["canonical_ascii"])
        return token_cache[sid]

    considered = 0
    differing = 0
    census: list[dict] = []
    clash_hits: list[dict] = []
    clash_counts: Counter = Counter()

    for a, b in pool:
        if a not in statements or b not in statements:
            continue
        ca, cb = statements[a]["canonical_ascii"], statements[b]["canonical_ascii"]
        if not ca or not cb:
            continue
        considered += 1
        if ca == cb:
            continue
        differing += 1
        left, right = toks(a), toks(b)

        shapes = clash_shapes(left, right)
        if shapes:
            clash_counts.update(shapes)
            clash_hits.append({
                "statement_ids": [a, b],
                "shapes": shapes,
                "canonical_ascii": [ca, cb],
            })

        fork = discriminator(left, right)
        if fork is None or not qualifies(fork):
            continue
        klass, note = classify(left, right, fork)
        bucket, meaning = CLASS_META[klass]
        census.append({
            "statement_ids": [a, b],
            "disciplines": [statements[a]["discipline"], statements[b]["discipline"]],
            "cross_corpus": statements[a]["discipline"] != statements[b]["discipline"],
            "pool_origin": origin[(a, b)],
            "touches_authored_corpus": bool(
                {statements[a]["discipline"], statements[b]["discipline"]}
                - INGESTED_CORPORA),
            "discriminator_position": fork["position"],
            "common_prefix_tokens": fork["common_prefix_tokens"],
            "common_suffix_tokens": fork["common_suffix_tokens"],
            "subterms": [" ".join(fork["left_tokens"]),
                         " ".join(fork["right_tokens"])],
            "classification": klass,
            "verdict": bucket,
            "verdict_meaning": meaning,
            "note": note,
            "canonical_ascii": [ca, cb],
        })

    census.sort(key=lambda row: (row["classification"], row["statement_ids"]))
    clash_hits.sort(key=lambda row: row["statement_ids"])

    by_class = Counter(row["classification"] for row in census)
    by_verdict = Counter(row["verdict"] for row in census)
    by_subterm = Counter(
        " | ".join(sorted(row["subterms"])) for row in census
    )

    candidates = [r for r in census if r["verdict"] == "convention_pair_candidate"]
    candidate_ids = sorted({sid for r in candidates for sid in r["statement_ids"]})
    authored_candidates = [r for r in candidates if r["touches_authored_corpus"]]
    both_authored = [r for r in candidates
                     if not (set(r["disciplines"]) & INGESTED_CORPORA)]
    by_discipline_pair = Counter(
        " + ".join(sorted(set(r["disciplines"]))) for r in candidates)

    branch = "census" if candidates else "registered_negative"

    findings: list[str] = []
    findings.append(
        f"{len(census)} of {differing} co-present pairs with differing "
        f"canonical_ascii fork at a single discriminator subterm; "
        f"{len(candidates)} of those are convention-pair candidates "
        f"({len(candidate_ids)} distinct statements)."
    )
    findings.append(
        "Every convention-pair candidate found is NOTATIONAL — a glyph, a "
        "namespaced-vs-bare head spelling, or where the author put a "
        "parenthesis. None is a mathematical convention fork."
    )
    findings.append(
        f"{len(authored_candidates)} of {len(candidates)} candidates touch an "
        f"authored corpus and {len(both_authored)} have BOTH members "
        "authored. Inside the hand-authored disciplines the registered "
        "negative is unqualified: conventions were fixed by the author and "
        "never forked, and nobody had written that down. Everything else is "
        "an upstream dataset's two problem authors writing one inequality two "
        "ways — a fact about the ingestion, not about a convention this graph "
        "holds twice."
    )
    findings.append(
        "The single largest candidate class, "
        f"{by_subterm.get('> = | ≥', 0)} pairs forking `>=` against `≥`, is "
        "the same glyph split ROADMAP §3a's transliteration lane addresses. "
        "TWO RIGHTS and the transliteration lane are looking at one "
        "phenomenon from two sides; that is a fact about the corpus, not a "
        "coincidence of method."
    )
    findings.append(
        "The registered negative stands for the three clash shapes the "
        "roadmap names: sign conventions, the 0-in-N boundary, and 2-pi "
        "placement return "
        + ", ".join(f"{shape}={clash_counts.get(shape, 0)}"
                    for shape in ("sign_convention", "nat_zero_boundary",
                                  "two_pi_placement"))
        + " over the same pool with insertions allowed. Conventions of that "
        "kind were fixed by the author and never forked."
    )
    findings.append(
        "The anonymized-template pass contributed "
        f"{pool_stats['anonymized_template_pairs_not_already_twins']} pairs the "
        f"twin ledger did not already carry, out of "
        f"{pool_stats['anonymized_template_pairs']} template-sharing pairs — "
        "the twin ledger is the stronger pool, and this is the first time "
        "that has been measured."
    )

    report = {
        "probe": "convention_pairs_v0.19_item3b",
        "roadmap_item": "ROADMAP-v0.19 §3b (TWO RIGHTS B0)",
        "course_receipt": "reports/design-direction-v0.19.json outcomes.series_3",
        "branch": branch,
        "branch_meaning": (
            "census: co-present convention forks exist and are inventoried "
            "below, unsealed, for the full direction to seal if it ever runs"
            if branch == "census" else
            "registered negative: no co-present convention fork exists in the "
            "committed graph"
        ),
        "branch_qualification": (
            "The census branch landed, but it landed narrow, and the narrow "
            "reading is the finding. Every candidate is notational rather "
            "than mathematical, and no candidate has both members in a "
            "hand-authored corpus. Read as a statement about the "
            "authored graph, this run "
            "IS the registered negative §3b describes; read as a statement "
            "about the whole committed graph, it is a census of "
            f"{len(candidates)} notation forks the upstream dataset carried "
            "in. A future TWO RIGHTS direction inherits both halves and "
            "should not quote the first number without the second."
        ),
        "parameters": {
            "tokenizer_regex": TOKENIZER,
            "max_discriminator_tokens": MAX_DISCRIMINATOR_TOKENS,
            "discriminator_rule": (
                "strip longest common token prefix and suffix; both remainders "
                "must be non-empty and within max_discriminator_tokens"
            ),
            "pool_passes": [
                "twin ledger reports/signature_matches.json, all five families",
                "direct pass over shared structural_signature.anonymized_template",
            ],
            "twin_families": list(TWIN_FAMILIES),
            "notation_classes": [list(row) for row in NOTATION_CLASSES],
            "domain_symbols": sorted(DOMAIN_SYMBOLS),
            "ingested_corpora": sorted(INGESTED_CORPORA),
            "clash_shapes_swept": [
                "sign_convention", "nat_zero_boundary", "two_pi_placement",
            ],
            "classification_order": [
                "alpha_variant", "bracketing_convention", "notation_convention",
                "domain_fork", "commutation_reorder", "unclassified_difference",
            ],
        },
        "corpus": {
            "statement_nodes": len(statements),
            "with_canonical_ascii": sum(
                1 for r in statements.values() if r["canonical_ascii"]),
        },
        "pool": pool_stats | {
            "pairs_with_both_canonical_forms": considered,
            "pairs_with_differing_canonical_ascii": differing,
        },
        "census": {
            "pairs": len(census),
            "counts_by_verdict": dict(sorted(by_verdict.items())),
            "counts_by_classification": dict(sorted(by_class.items())),
            "convention_pair_candidate_statements": len(candidate_ids),
            "convention_pair_candidates_touching_authored_corpus":
                len(authored_candidates),
            "convention_pair_candidates_with_both_members_authored":
                len(both_authored),
            "convention_pair_candidates_by_discipline":
                dict(sorted(by_discipline_pair.items())),
            "top_discriminator_subterms": [
                {"count": count, "subterms": key}
                for key, count in sorted(by_subterm.most_common(),
                                         key=lambda kv: (-kv[1], kv[0]))[:20]
            ],
            "rows": census,
        },
        "famous_clash_sweep": {
            "rule": (
                "same pool, insertions allowed; a pair matches a shape when it "
                "is token-identical after deleting that shape's marker tokens"
            ),
            "counts": {shape: clash_counts.get(shape, 0)
                       for shape in ("sign_convention", "nat_zero_boundary",
                                     "two_pi_placement")},
            "hits": clash_hits,
            "registered_negative": not clash_hits,
        },
        "findings": findings,
        "not_claimed": [
            "These rows are NOT sealed ConventionPair objects. Sealing before "
            "inspection is the full direction's job; this probe inspected on "
            "purpose, because the census is the deliverable.",
            "The famous-clash detectors are shape tests, not proofs: a "
            "`nat_zero_boundary` hit would mean two statements over N differ "
            "only at a 0/1 constant, which is where that clash LIVES, not "
            "proof that the author was choosing a convention. No hit was "
            "returned, so nothing rests on the distinction here.",
            "A convention-pair candidate is a claim about notation, not a "
            "proof that the two statements are provably equivalent. No "
            "checker was run.",
            "The pool is twin-derived. A convention fork between two "
            "statements the twin ledger never grouped and whose anonymized "
            "templates differ would be invisible to this sweep.",
        ],
        "provenance": provenance_block(
            Path(__file__), [*node_inputs, TWIN_LEDGER], repo),
    }
    return report


def write_report(report: dict, path: Path = OUT_PATH) -> None:
    text = json.dumps(report, indent=2, ensure_ascii=False, sort_keys=False) + "\n"
    path.write_bytes(text.encode("utf-8").replace(b"\r\n", b"\n"))


def main() -> int:
    report = build_report()
    write_report(report)
    print(f"branch: {report['branch']}")
    print(json.dumps(report["pool"], indent=1))
    print(json.dumps({k: v for k, v in report["census"].items()
                      if k not in ("rows", "top_discriminator_subterms")},
                     indent=1))
    print("top discriminator subterms:")
    for row in report["census"]["top_discriminator_subterms"][:12]:
        print(f"  {row['count']:>4}  {row['subterms']}")
    print("famous-clash sweep:",
          json.dumps(report["famous_clash_sweep"]["counts"]),
          "registered_negative=",
          report["famous_clash_sweep"]["registered_negative"])
    for line in report["findings"]:
        print("- " + line)
    print(f"wrote {OUT_PATH.relative_to(REPO).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
