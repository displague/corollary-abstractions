#!/usr/bin/env python3
"""The transliteration lane's registered run — ROADMAP-v0.19 item 3a.

Writes `experiments/transliteration_rate.json`: the parse rate over the whole
corpus under the post-amendment parser, the composition of the set those two
glyphs newly reach, and the ROUND-TRIP rate over that set through v0.18's
realizer machinery, unchanged.

## Why two rates and not one

"the artifact must publish the parse rate *and* the round-trip rate over the
newly-reached set, because parsing is not rendering and v0.18's own R0/R1 split
is the reason we know to separate them" — ROADMAP-v0.19 item 3a.

A lane that reported only the parse gain would be claiming reach and letting a
reader supply "and therefore the system can say them", which is the inference
v0.18 spent a cycle learning not to make for free.

## Why no round-trip floor

`experiments/transliteration_prereg.json` freezes a parse-gain floor of 6,000
and deliberately freezes NO round-trip floor, with the reason recorded before
the reading. This is a probe: a high rate says the newly-reached statements are
the same grammar in every respect that matters, a low rate says parsing bought
reach without buying voice, and both are results. A floor here would have made
the second branch expensive to publish.

## How "newly reached" is decided, and why it does not need the old parser

A statement is newly reached iff it parses now and did not parse before. This
run does not load the retired parser to decide that; it uses an equivalence that
holds by construction:

    The only difference between the two parsers is that `≥` and `≤` tokenize.
    A source carrying neither glyph therefore tokenizes identically under both,
    so it parses under both or neither. A source carrying either glyph could not
    tokenize at all under the retired parser — `TOKEN_RE` matched no alternative
    at that character and `tokenize` raised. So: newly reached == parses now AND
    carries at least one glyph.

An argument is not a measurement, so the run CROSS-CHECKS its count against
`experiments/transliteration_served_diff.json`, whose corpus-wide reading was
computed by actually loading the retired parser from git in a separate
interpreter. If the two disagree the run refuses to write. That artifact is the
independent witness; this reasoning is the cheap path the witness licenses.

## Refusals are reported by class, with counts

The realization lexicon's head coverage is stated over v0.18's parseable set,
not over this one, so heads it never met can appear here. Refusals are therefore
never aggregated into one number: an uncovered head is a different fact about
the corpus than an unsupported numeral, and the lane's honest failure mode is
only visible if the classes stay apart.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import realization_lexicon as rlex  # noqa: E402
import realize_term as rt  # noqa: E402
from match_signatures import (  # noqa: E402
    GLYPH_EQUIVALENTS,
    Parser,
    TemplateParseError,
    canonicalize,
    tokenize,
)
from report_provenance import provenance_block, sha256_lf_file  # noqa: E402

RUN_ID = "transliteration.registered.v1"
REGISTERED_ON = "2026-08-24"
PREREG_PATH = REPO_ROOT / "experiments" / "transliteration_prereg.json"
SERVED_DIFF_PATH = REPO_ROOT / "experiments" / "transliteration_served_diff.json"

#: The retired pin, quoted so the artifact can state what it superseded without
#: reading a second file at run time.
RETIRED_PARSER_DIGEST = (
    "65fead2f47b6a2cea068cf2ee76db89e6e1bf0fcc7ab57220cdac328be05b599")


class PreregMismatch(RuntimeError):
    """The freeze does not describe the tree. The run does not get written."""


def revalidate_prereg(prereg_path: Path | None = None) -> dict:
    """Re-compute every pinned digest before a single statement is read.

    Same discipline as `measure_realization.revalidate_prereg`, and same reason:
    a reading path that moved between the freeze and the run produces a number
    nobody can interpret, so the run stops instead of producing it.

    `pending` rows are checked too, in the one way they can be: a row still in
    `pending` must name a file that is NOT in the tree. A pending row pointing
    at an existing file means the freeze was written after the thing it froze.
    """
    prereg_path = Path(prereg_path) if prereg_path is not None else PREREG_PATH
    prereg = json.loads(prereg_path.read_text(encoding="utf-8"))
    rows, drifted = [], []
    for row in prereg["frozen"]:
        path = REPO_ROOT / row["path"]
        actual = sha256_lf_file(path) if path.exists() else None
        agrees = actual == row["sha256_lf"]
        rows.append({
            "path": row["path"],
            "role": row["role"],
            "recorded_sha256_lf": row["sha256_lf"],
            "observed_sha256_lf": actual,
            "agrees": agrees,
        })
        if not agrees:
            drifted.append(row["path"])
    premature = [row["path"] for row in prereg.get("pending", ())
                 if (REPO_ROOT / row["path"]).exists()]
    if drifted:
        raise PreregMismatch(
            "these preregistered artifacts no longer match the tree: "
            + ", ".join(drifted)
            + ". The lane's floors were frozen against them; the registered run "
            "is NOT written."
        )
    if premature:
        raise PreregMismatch(
            "these rows are still `pending` but the files exist: "
            + ", ".join(premature)
            + ". A pending row is a promise that a file is not yet written; the "
            "row moves to `frozen` with its own recorded date when it is."
        )
    return {
        "prereg": str(prereg_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "prereg_sha256_lf": sha256_lf_file(prereg_path),
        "verdict": "HOLDS",
        "what_it_means": (
            "Every artifact this lane froze before the run is byte-identical to "
            "what the preregistration commit recorded — the post-amendment "
            "parser included. If any row disagreed this writer would refuse to "
            "emit the artifact."
        ),
        "the_parser_this_run_used": {
            "path": "scripts/match_signatures.py",
            "sha256_lf": sha256_lf_file(REPO_ROOT / "scripts" /
                                        "match_signatures.py"),
            "supersedes": RETIRED_PARSER_DIGEST,
            "retired_by": "realization.prereg.v1.amendment.transliteration-"
                          "2026-08-24, recorded in experiments/"
                          "realization_prereg.json and experiments/"
                          "foreign_voice_prereg.json",
        },
        "revalidated": rows,
    }


def iter_statements(data_dir: Path):
    """(corpus, statement_id, canonical_ascii), fully sorted.

    Same walk `measure_realization` uses, so the two artifacts' denominators are
    comparable statement for statement rather than approximately.
    """
    for path in sorted(data_dir.glob("*/nodes.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        corpus = doc.get("discipline", path.parent.name)
        for node in doc.get("statement_nodes", []):
            yield (
                corpus,
                node.get("statement_id", "<missing-id>"),
                ((node.get("formal_statement") or {}).get("canonical_ascii") or ""),
            )


def carries_a_glyph(source: str) -> bool:
    return any(glyph in source for glyph in GLYPH_EQUIVALENTS)


def parses(source: str) -> bool:
    try:
        canonicalize(Parser(tokenize(source)).parse())
    except (TemplateParseError, ValueError, RecursionError):
        return False
    return True


def _heads(tree, into: collections.Counter) -> None:
    """Every call head, operator and relation in a canonical tree."""
    kind = tree[0]
    if kind == "call":
        into[f"call:{tree[1]}"] += 1
        for arg in tree[2]:
            _heads(arg, into)
    elif kind in ("op", "rel"):
        into[f"{kind}:{tree[1]}"] += 1
        for arg in tree[2]:
            _heads(arg, into)


def measure(data_dir: Path, lex) -> dict:
    """Parse rate over the corpus, plus the round trip over the new set."""
    per_corpus: dict[str, dict] = {}
    newly: list[tuple[str, str, str]] = []
    total = parseable = 0
    for corpus, sid, source in iter_statements(data_dir):
        row = per_corpus.setdefault(
            corpus, {"corpus": corpus, "nodes": 0, "parseable": 0,
                     "newly_reached": 0, "served": 0, "refused": 0, "failed": 0})
        row["nodes"] += 1
        total += 1
        if not parses(source):
            continue
        parseable += 1
        row["parseable"] += 1
        if carries_a_glyph(source):
            row["newly_reached"] += 1
            newly.append((corpus, sid, source))

    heads = collections.Counter()
    relations = collections.Counter()
    glyph_use = collections.Counter()
    refusals = collections.Counter()
    failures: list[dict] = []
    refused_examples: dict[str, dict] = {}
    served = refused = failed = 0
    for corpus, sid, source in newly:
        for glyph in GLYPH_EQUIVALENTS:
            if glyph in source:
                glyph_use[glyph] += source.count(glyph)
        tree = canonicalize(Parser(tokenize(source)).parse())
        local = collections.Counter()
        _heads(tree, local)
        heads.update(local)
        for key in local:
            if key.startswith("rel:"):
                relations[key[4:]] += local[key]
        result = rt.realize(source, lex, statement_id=sid)
        if isinstance(result, rt.Refusal):
            refused += 1
            per_corpus[corpus]["refused"] += 1
            refusals[result.reason] += 1
            refused_examples.setdefault(result.reason, {
                "statement_id": sid, "detail": result.detail,
                "canonical_ascii": source})
        elif result.served:
            served += 1
            per_corpus[corpus]["served"] += 1
        else:
            failed += 1
            per_corpus[corpus]["failed"] += 1
            failures.append({"statement_id": sid, "canonical_ascii": source,
                             "round_trip": result.round_trip,
                             "surface": result.surface})

    if served + refused + failed != len(newly):
        raise RuntimeError(
            f"served+refused+failed = {served + refused + failed} but the newly "
            f"reached set has {len(newly)}. A statement in none of the three is "
            f"a construction failure, not a rounding detail."
        )
    return {
        "total": total,
        "parseable": parseable,
        "newly": newly,
        "per_corpus": [per_corpus[key] for key in sorted(per_corpus)],
        "heads": heads,
        "relations": relations,
        "glyph_use": glyph_use,
        "served": served,
        "refused": refused,
        "failed": failed,
        "refusals": refusals,
        "refused_examples": refused_examples,
        "failures": failures,
    }


def cross_check_newly_reached(count: int) -> dict:
    """The independent witness for the newly-reached count.

    `experiments/transliteration_served_diff.json` computed its corpus-wide
    gains by loading the RETIRED parser from git in a separate interpreter and
    diffing `answer._in_words` over every statement. Its gain count is the same
    population this run calls newly reached, arrived at without the equivalence
    argument above — so agreement is evidence and disagreement is a stop.

    Two of v0.18's parseable terms refuse at the lexicon (`unsupported_numeral`)
    and so serve no line; the same subtraction applies here, which is why the
    comparison is against `gained + <newly reached statements that refuse>`
    rather than against a raw parse count. The run computes that adjustment from
    its own refusal table rather than hardcoding two.
    """
    doc = json.loads(SERVED_DIFF_PATH.read_text(encoding="utf-8"))
    reading = doc["corpus_wide_reading"]
    return {
        "witness": "experiments/transliteration_served_diff.json",
        "witness_sha256_lf": sha256_lf_file(SERVED_DIFF_PATH),
        "how_the_witness_decided": (
            "it loaded the retired parser from git in its own interpreter and "
            "diffed answer._in_words over all 12,777 statements; its `gained` "
            "are statements that served no line under the retired parser and "
            "serve one now"
        ),
        "witness_gained": reading["gained"],
        "this_run_newly_reached": count,
        "agrees": None,
    }


def build_artifact(data_dir: Path, prereg_path: Path | None = None) -> dict:
    gate = revalidate_prereg(prereg_path)
    lexicon_path = rlex.DEFAULT_LEXICON_PATH
    lex = rlex.load(lexicon_path)
    prereg = json.loads((prereg_path or PREREG_PATH).read_text(encoding="utf-8"))
    floors = prereg["frozen_floors"]

    body = measure(data_dir, lex)
    newly = len(body["newly"])
    served, refused, failed = body["served"], body["refused"], body["failed"]

    full_corpus = data_dir.resolve() == (REPO_ROOT / "data").resolve()
    cross = cross_check_newly_reached(newly)
    # The witness counts statements that gained a SERVED line; this run counts
    # statements that gained a PARSE. They differ by exactly the newly-reached
    # statements that parse and then refuse or fail at the realizer.
    expected_gain = newly - refused - failed
    cross["this_run_newly_served"] = served
    cross["adjustment"] = {
        "refused": refused,
        "failed": failed,
        "why": "a statement can parse and still serve no line; the witness sees "
               "served lines, this run sees parses, and the gap is exactly the "
               "refusals and round-trip failures below",
    }
    if not full_corpus:
        # The witness was computed over the whole committed corpus. Comparing it
        # to a slice would fail for the one reason that is not a finding, and
        # silently passing a slice off as cross-checked would be worse — so the
        # artifact says which of the two it is instead of carrying a bare bool.
        cross["agrees"] = None
        cross["not_applicable"] = (
            f"this run walked {data_dir}, not the committed data/ the witness "
            f"was computed over. The check is skipped and SAID to be skipped; "
            f"an artifact from a partial corpus is not the registered run."
        )
    else:
        cross["agrees"] = cross["witness_gained"] == expected_gain
        if not cross["agrees"]:
            raise PreregMismatch(
                f"the newly-reached count disagrees with its independent "
                f"witness: this run {expected_gain} served-gains, "
                f"experiments/transliteration_served_diff.json "
                f"{cross['witness_gained']}. One of the two is wrong and the "
                f"run is not written."
            )

    rate = served / newly if newly else 0.0
    parse_rate = body["parseable"] / body["total"] if body["total"] else 0.0
    floor = floors["parse_gain"]["floor"]

    corpora = [row for row in body["per_corpus"] if row["newly_reached"]]
    heads = body["heads"]
    call_heads = sorted(
        ((key[5:], count) for key, count in heads.items()
         if key.startswith("call:")),
        key=lambda pair: (-pair[1], pair[0]))

    return {
        "run_id": RUN_ID,
        "registered": REGISTERED_ON,
        "lane": "ROADMAP-v0.19 item 3a — the transliteration lane",
        "prereg": "experiments/transliteration_prereg.json",
        "design": [
            "docs/DESIGN-sans-template-rendering.md — the realizer path this run "
            "re-uses unchanged, and the R0/R1 split that is why two rates are "
            "reported instead of one",
            "docs/DESIGN-foreign-voice.md §5 — the ordering rule that gated this "
            "lane behind v0.19's registered run, satisfied by commit 46edefd",
        ],
        "provenance": provenance_block(
            Path(__file__),
            sorted(data_dir.glob("*/nodes.json")) + [
                lexicon_path,
                REPO_ROOT / "scripts" / "match_signatures.py",
                REPO_ROOT / "scripts" / "realize_term.py",
                REPO_ROOT / "scripts" / "realization_lexicon.py",
                REPO_ROOT / "scripts" / "numeral_words.py",
                prereg_path or PREREG_PATH,
                SERVED_DIFF_PATH,
            ],
        ),
        "what_this_is": [
            "The transliteration lane's registered artifact. It is a PROBE, "
            "committed whichever way it lands (ROADMAP-v0.19 item 3: \"both of "
            "these commit their result whichever way it lands\").",
            "It carries two rates because parsing is not rendering: the parse "
            "rate over the whole corpus under the post-amendment parser, and "
            "the round-trip rate over the set the two glyphs newly reach.",
            "It does NOT amend, re-open or blend with "
            "experiments/realization_rate.json. That artifact was declared "
            "historical, in writing, by the dated amendment this lane's parser "
            "change was authorized by.",
        ],
        "prereg_revalidated": gate,
        "over_the_committed_corpus": {
            "yes": full_corpus,
            "why_it_is_recorded": "only a run over the committed data/ is the "
                                  "registered run. A run over a slice is a "
                                  "useful thing to have (the determinism and "
                                  "refusal tests build one) and must not be "
                                  "mistakable for the artifact of record, so "
                                  "the flag is in the file rather than in "
                                  "whoever remembers how it was invoked.",
        },
        "parse_rate": {
            "gate": "the lane's headline number",
            "nodes_total": body["total"],
            "parseable": body["parseable"],
            "rate": round(parse_rate, 6),
            "under_the_retired_parser": {
                "parseable": body["parseable"] - newly,
                "digest": RETIRED_PARSER_DIGEST,
                "note": "the v0.18 figure, recomputed here on the same walk so "
                        "the two are comparable statement for statement; "
                        "experiments/realization_rate.json remains the "
                        "artifact of record for what was MEASURED under it",
            },
            "newly_reached": newly,
            "sentence": (
                f"{body['parseable']} of {body['total']} statements parse "
                f"({parse_rate:.4f}), of which {newly} are newly reached by two "
                f"glyph equivalences; {body['parseable'] - newly} parsed before."
            ),
            "floor": floor,
            "floor_met": newly >= floor,
            "how_newly_reached_was_decided": [
                "parses now AND carries `≥` or `≤`. The two parsers differ only "
                "in whether those two characters tokenize, so a source without "
                "them parses under both or neither, and a source with them could "
                "not tokenize at all under the retired parser.",
                "The argument is not taken on trust: see `cross_check` below.",
            ],
            "cross_check": cross,
        },
        "newly_reached_composition": {
            "why": "DESIGN-sans-template-rendering R1's rule, imported: a rate "
                   "never travels without its denominator, and a denominator "
                   "nobody has described is not one a reader can check.",
            "statements": newly,
            "per_corpus": corpora,
            "corpora_reached": len(corpora),
            "concentration": (
                f"{max((row['newly_reached'] for row in corpora), default=0)} of "
                f"{newly} in the largest corpus"
            ),
            "glyph_occurrences": dict(sorted(body["glyph_use"].items())),
            "relations_present": dict(sorted(body["relations"].items())),
            "distinct_call_heads": len(call_heads),
            "call_heads_by_mass": [{"head": head, "count": count}
                                   for head, count in call_heads],
            "reading": [
                f"The set is {len(corpora)} corpus and "
                f"{len(call_heads)} distinct call heads over {newly} "
                f"statements. It is LARGE AND STRUCTURALLY NARROW: numeric "
                f"inequalities, overwhelmingly, with almost no function "
                f"application in them at all.",
                "That is the honest shape of what two glyphs unlock, and it is "
                "stated here rather than left for a reader to infer from a "
                "table, because the round-trip rate below is read against this "
                "denominator and not against the corpus.",
            ],
        },
        "round_trip": {
            "gate": "the lane's second rate — v0.18's realizer machinery, "
                    "unchanged, over statements it could not previously reach",
            "no_floor_was_pre_committed": True,
            "why_no_floor": floors["round_trip"]["no_floor_is_pre_committed"],
            "denominator": newly,
            "served": served,
            "refused": refused,
            "failed": failed,
            "rate_over_newly_reached": round(rate, 6),
            "sentence": (
                f"{served} of {newly} newly-reached statements round-trip "
                f"EXACTLY ({rate:.4f}); {refused} refused and {failed} failed "
                f"the round trip."
            ),
            "partition_balances": served + refused + failed == newly,
            "refusals_by_reason": dict(sorted(body["refusals"].items())),
            "refusal_examples": body["refused_examples"],
            "failures": body["failures"],
            "what_this_rate_does_and_does_not_establish": [
                f"ESTABLISHES: the {newly} statements the two glyphs reach are "
                f"the same grammar in every respect the realizer touches, not "
                f"only at the tokenizer. {served} of them realize to a sentence "
                f"that re-parses and canonicalizes back to the source skeleton, "
                f"with {refused} refusals and {failed} round-trip failures.",
                "DOES NOT ESTABLISH that the realization lexicon covers the "
                "corpus. The lexicon's head coverage was authored against "
                "v0.18's parseable set, and the reason it is not strained here "
                "is that this set carries almost no call heads — see the "
                "composition above. A rate of 1.0 over arithmetic inequalities "
                "is a weaker fact than a rate of 1.0 over a set with the "
                "corpus's head inventory in it, and the two must not be read as "
                "the same sentence.",
                "DOES NOT ESTABLISH anything about rendering QUALITY. The gate "
                "is skeleton identity under re-parse, which is a claim about a "
                "machine reading its own output. Whether a person recovers the "
                "mathematics from the English is a determinacy claim, and this "
                "lane runs no control that could license one.",
            ],
            "not_averaged_with_v018": (
                "This rate is over the newly-reached set. v0.18's 0.9991 is over "
                "its own 2,172, measured under the retired parser. The two are "
                "reported side by side and never blended — blending them is the "
                "figure the amendment declined to produce by re-running."
            ),
        },
        "non_claims": [
            "The parse rate is not a rendering rate and neither is a claim that "
            "a reader can recover the mathematics from the English. That claim "
            "needs a determinacy control this lane does not run.",
            "Nothing here is a claim about the 4,191-statement foreign residue, "
            "which is disjoint from this set by construction and measured under "
            "DESIGN-foreign-voice's own gate.",
            "A high round-trip rate over this set is not evidence that the "
            "realization lexicon covers the corpus. It is evidence that the "
            "newly-reached statements carry the heads it already had, which is "
            "a fact about which statements the two glyphs unlock.",
        ],
    }


def print_summary(artifact: dict) -> None:
    parse = artifact["parse_rate"]
    trip = artifact["round_trip"]
    print(parse["sentence"])
    print(f"  parse-gain floor {parse['floor']}: "
          f"{'MET' if parse['floor_met'] else 'NOT MET'}")
    print(trip["sentence"])
    if trip["refusals_by_reason"]:
        print("  refusals by reason:")
        for reason, count in trip["refusals_by_reason"].items():
            print(f"    {count:>6}  {reason}")
    comp = artifact["newly_reached_composition"]
    print(f"  composition: {comp['corpora_reached']} corpora, "
          f"{comp['distinct_call_heads']} distinct call heads, "
          f"relations {comp['relations_present']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--out", type=Path,
                        default=Path("experiments/transliteration_rate.json"))
    parser.add_argument("--prereg", type=Path, default=None)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    started = time.time()
    try:
        artifact = build_artifact(args.data_dir, args.prereg)
    except PreregMismatch as exc:
        print(f"REFUSING TO WRITE: {exc}", file=sys.stderr)
        return 3
    print_summary(artifact)
    print(f"\nwall clock: {time.time() - started:.1f}s "
          f"(not recorded in the artifact — it must stay byte-reproducible)")
    if not args.no_write:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_bytes(
            (json.dumps(artifact, indent=2, ensure_ascii=False) + "\n")
            .encode("utf-8"))
        print(f"registered run written to {args.out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
