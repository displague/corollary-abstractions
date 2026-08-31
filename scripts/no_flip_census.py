#!/usr/bin/env python3
"""R-NF: replay the registered answered-turn cohort for visible regressions."""

from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

if __package__ in {None, ""}:  # pragma: no cover - CLI import shim
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import replay_session  # noqa: E402
import session_ledger as ledger  # noqa: E402
from harness import CoreSession, route_line  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PREREG = ROOT / "experiments" / "no_flip_prereg.json"
DEFAULT_OUT = ROOT / "experiments" / "no_flip_census.json"
SESSIONS = ROOT / "experiments" / "sessions"
HEX64 = re.compile(r"[0-9a-f]{64}")
REGISTRATION_PATHS = (
    "experiments/no_flip_prereg.json",
    "scripts/no_flip_census.py",
    "tests/test_no_flip_census.py",
)


class CensusRefusal(RuntimeError):
    """The registered census cannot run against this tree."""


def sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise CensusRefusal(f"{path}: expected a JSON object")
    return value


def group_manifest(patterns: list[str]) -> tuple[str, list[dict]]:
    paths: set[Path] = set()
    for pattern in patterns:
        paths.update(path for path in ROOT.glob(pattern) if path.is_file())
    if not paths:
        raise CensusRefusal(f"freeze group matched no files: {patterns!r}")
    rows = [
        {"path": path.relative_to(ROOT).as_posix(), "sha256_lf": sha256_lf(path)}
        for path in sorted(paths)
    ]
    payload = "\n".join(f"{row['path']}\0{row['sha256_lf']}" for row in rows)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest(), rows


def revalidate(prereg: dict) -> list[dict]:
    rows = []
    amendments = {
        entry.get("amendment_id"): entry for entry in prereg.get("amendments", ())
    }
    for name, spec in sorted(prereg["freeze_groups"].items()):
        observed, members = group_manifest(spec["patterns"])
        row = {
            "group": name,
            "expected": spec["expected_digest"],
            "observed": observed,
            "agrees": observed == spec["expected_digest"],
            "members": members,
        }
        marker = spec.get("retired_for_future_comparisons")
        if marker is not None:
            # Retirement in writing, never edit in place (the prereg_pins
            # discipline, applied to a pattern group): the original digest
            # stays so the registered run's numbers remain checkable against
            # it, and a dated amendment carries the movement. A marker that
            # names no recorded amendment is a pin deleted, and it raises.
            amendment = amendments.get(marker.get("amendment"))
            if amendment is None:
                raise CensusRefusal(
                    f"freeze group {name!r} claims retirement by amendment "
                    f"{marker.get('amendment')!r}, which this prereg does not "
                    "record; a pin retired in writing names an amendment that "
                    "exists"
                )
            row["retired"] = True
            row["retired_by"] = amendment["amendment_id"]
        rows.append(row)
    moved = [
        row["group"] for row in rows if not row["agrees"] and not row.get("retired")
    ]
    if moved:
        raise CensusRefusal("preregistration digest drift: " + ", ".join(moved))
    return rows


def journal_paths() -> list[Path]:
    return [
        path for path in sorted(SESSIONS.glob("v021-s*.json"))
        if not path.name.endswith(".reads.json")
    ]


def population(paths: list[Path]) -> dict:
    kinds: collections.Counter[str] = collections.Counter()
    turns = 0
    for path in paths:
        journal = load_object(path)
        for record in journal["turns"]:
            turns += 1
            kinds[record["result"]["kind"]] += 1
    answering = {name: kinds[name] for name in ("solved", "found")}
    excluded = {
        name: kinds[name]
        for name in ("waiting", "refused", "exhausted", "canceled")
    }
    return {
        "journals": len(paths),
        "turns": turns,
        "answering_by_kind": answering,
        "answering_total": sum(answering.values()),
        "excluded_by_kind": excluded,
        "excluded_total": sum(excluded.values()),
    }


def require_population(prereg: dict, observed: dict) -> None:
    expected = prereg["population"]
    if observed != expected:
        raise CensusRefusal(
            "PREREGISTRATION_DISCREPANCY: population changed: "
            f"expected {expected!r}, observed {observed!r}"
        )


def digest_changed(recorded_digest: str, live_digest: str) -> bool:
    """B5's entire primary comparator: two digests in, one inequality out."""
    if not HEX64.fullmatch(recorded_digest) or not HEX64.fullmatch(live_digest):
        raise CensusRefusal("primary comparator requires two lowercase SHA-256 digests")
    return recorded_digest != live_digest


def _semantic_rows(verdict: dict) -> tuple[list[str], list[str], str]:
    answer = list(verdict.get("answer") or ())
    members = [row for row in answer if row.startswith("member     : ")]
    ledgers = [row for row in answer if row.startswith("ledger     : ")]
    if len(members) != 2 or len(ledgers) != 1:
        raise CensusRefusal("INVALID_PLANT: source is not two members plus one ledger")
    if len(set(answer)) != len(answer):
        raise CensusRefusal("INVALID_PLANT: source contains duplicate rows")
    return answer, members, ledgers[0]


def plant_verdicts(source: dict) -> dict[str, dict]:
    """Build and prove the two set-equivalent, ordering-only mutations."""
    answer, members, ledger_row = _semantic_rows(source)
    member_positions = [answer.index(row) for row in members]
    ledger_position = answer.index(ledger_row)
    if member_positions[1] != member_positions[0] + 1 or ledger_position != member_positions[1] + 1:
        raise CensusRefusal("INVALID_PLANT: source row order drifted")

    member_order = copy.deepcopy(source)
    member_answer = list(answer)
    member_answer[member_positions[0]], member_answer[member_positions[1]] = (
        member_answer[member_positions[1]], member_answer[member_positions[0]]
    )
    member_order["answer"] = tuple(member_answer)
    ledger_first = copy.deepcopy(source)
    ledger_answer = list(answer)
    ledger_answer.pop(ledger_position)
    ledger_answer.insert(member_positions[0], ledger_row)
    ledger_first["answer"] = tuple(ledger_answer)

    for name, mutated in {
        "MEMBER_ORDER": member_order,
        "LEDGER_POSITION": ledger_first,
    }.items():
        mutated_answer, _, _ = _semantic_rows(mutated)
        if collections.Counter(mutated_answer) != collections.Counter(answer):
            raise CensusRefusal(f"INVALID_PLANT: {name} changed the row multiset")
        before_rest = {key: value for key, value in source.items() if key != "answer"}
        after_rest = {key: value for key, value in mutated.items() if key != "answer"}
        if before_rest != after_rest:
            raise CensusRefusal(f"INVALID_PLANT: {name} changed a non-answer field")
    expected_member = list(answer)
    expected_member[member_positions[0]:member_positions[1] + 1] = reversed(members)
    if list(member_order["answer"]) != expected_member:
        raise CensusRefusal("INVALID_PLANT: MEMBER_ORDER is not the registered reversal")
    expected_ledger = list(answer)
    expected_ledger.pop(ledger_position)
    expected_ledger.insert(member_positions[0], ledger_row)
    if list(ledger_first["answer"]) != expected_ledger:
        raise CensusRefusal("INVALID_PLANT: LEDGER_POSITION is not the registered move")
    return {"MEMBER_ORDER": member_order, "LEDGER_POSITION": ledger_first}


def controls(repo_root: Path, answering_total: int) -> dict:
    session = CoreSession.boot(repo_root, offline=True, session_id="v023-r-nf-control")
    source = route_line(repo_root, session, "twin programming.euclid.recursive")
    if source.get("status") not in {"solved", "found", "held", "PROVEN", "VERIFIED"}:
        raise CensusRefusal("INVALID_PLANT: registered source no longer answers")
    mutations = plant_verdicts(source)
    source_digest = ledger.answer_bytes_digest(source)
    rows = []
    for name, mutated in mutations.items():
        mutated_digest = ledger.answer_bytes_digest(mutated)
        exact = digest_changed(source_digest, mutated_digest)
        shape = (source.get("route"), source.get("status")) != (
            mutated.get("route"), mutated.get("status")
        )
        rows.append({
            "mutation": name,
            "equivalence_gate": "FIRES",
            "source_digest": source_digest,
            "mutated_digest": mutated_digest,
            "exact_detected": exact,
            "shape_only_detected": shape,
            "always_changed_detected": True,
        })
    exact_count = sum(row["exact_detected"] for row in rows)
    shape_count = sum(row["shape_only_detected"] for row in rows)
    always_count = sum(row["always_changed_detected"] for row in rows)
    observed = {
        "plants": rows,
        "exact_detected": exact_count,
        "shape_only_detected": shape_count,
        "always_changed_detected": always_count,
        "always_changed_false_positives_on_identical_self_pairs": answering_total,
        "identical_self_pairs": answering_total,
    }
    if (exact_count, shape_count, always_count) != (2, 0, 2):
        raise CensusRefusal(f"INVALID_CONTROL: mutation sensitivity {observed!r}")
    if observed["always_changed_false_positives_on_identical_self_pairs"] != 220:
        raise CensusRefusal("INVALID_CONTROL: always-changed vacuity denominator drifted")
    return observed


def replay_answering(repo_root: Path, paths: list[Path], prereg: dict) -> list[dict]:
    from resolver import build_index  # noqa: PLC0415

    shared_index = build_index([repo_root / "data", repo_root / "data_holdout"])
    answering_kinds = set(prereg["recorded_answering_kinds"])
    live_answering = set(prereg["live_answering_statuses"])
    rows: list[dict] = []
    for path in paths:
        journal = load_object(path)
        header = journal["header"]
        session = CoreSession.boot(repo_root, offline=True,
                                   session_id=header["session_id"])
        session.resolver_index = shared_index
        barrier = ledger.ReadBarrier()
        assumptions = replay_session._rebuild_assumptions(  # noqa: SLF001
            header["session_id"], journal.get("assumptions", []), barrier
        )
        session.assumptions = assumptions
        for record in journal["turns"]:
            turn_index = record["turn_index"]
            barrier.open_turn(turn_index)
            assumptions.advance(turn_index)
            verdict = route_line(repo_root, session, record["input_bytes"])
            barrier.close_turn()
            if record["result"]["kind"] not in answering_kinds:
                continue
            recorded_digest = record["result"]["answer_bytes_digest"]
            live_digest = ledger.answer_bytes_digest(verdict)
            retained = verdict.get("status") in live_answering
            changed = digest_changed(recorded_digest, live_digest)
            classification = (
                "ANSWER_LOST" if not retained else
                "DIGEST_MISMATCH" if changed else
                "DIGEST_MATCH"
            )
            rows.append({
                "session_id": header["session_id"],
                "turn_index": turn_index,
                "input_bytes": record["input_bytes"],
                "recorded_kind": record["result"]["kind"],
                "recorded_digest": recorded_digest,
                "live_digest": live_digest,
                "live_route": verdict.get("route"),
                "live_status": verdict.get("status"),
                "classification": classification,
            })
    return rows


def validate_accounting(rows: list[dict], denominator: int) -> dict:
    counts = collections.Counter(row["classification"] for row in rows)
    if len(rows) != denominator or sum(counts.values()) != denominator:
        raise CensusRefusal("INVALID_ACCOUNTING: receipt rows do not partition 220")
    red = [row for row in rows if row["classification"] != "DIGEST_MATCH"]
    required = {
        "session_id", "turn_index", "input_bytes", "recorded_kind",
        "recorded_digest", "live_digest", "live_route", "live_status",
        "classification",
    }
    if any(set(row) != required or any(row[key] is None for key in required)
           for row in red):
        raise CensusRefusal("INVALID_ACCOUNTING: incomplete red row")
    expected_red = counts["DIGEST_MISMATCH"] + counts["ANSWER_LOST"]
    if len(red) != expected_red:
        raise CensusRefusal("INVALID_ACCOUNTING: red row count disagrees")
    return {
        "digest_matches": counts["DIGEST_MATCH"],
        "digest_mismatches": counts["DIGEST_MISMATCH"],
        "answers_lost": counts["ANSWER_LOST"],
        "regression_candidates": expected_red,
        "denominator": denominator,
        "red_rows": red,
        "receipt_rows": rows,
    }


def registration_commit() -> str:
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT,
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout.strip()
    if status:
        raise CensusRefusal("the registered census runs only from a clean tree")
    commits = []
    for relative in REGISTRATION_PATHS:
        commit = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", relative], cwd=ROOT,
            capture_output=True, text=True, encoding="utf-8", check=True,
        ).stdout.strip()
        if not commit:
            raise CensusRefusal(f"registration input is not committed: {relative}")
        commits.append(commit)
    if len(set(commits)) != 1:
        raise CensusRefusal("preregistration and instruments were not committed together")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", check=True,
    ).stdout.strip()
    if head != commits[0]:
        raise CensusRefusal("the census must run at the clean registration commit")
    return head


def census() -> dict:
    commit = registration_commit()
    prereg = load_object(PREREG)
    pins = revalidate(prereg)
    paths = journal_paths()
    observed_population = population(paths)
    require_population(prereg, observed_population)
    control = controls(ROOT, observed_population["answering_total"])
    rows = replay_answering(ROOT, paths, prereg)
    accounting = validate_accounting(rows, observed_population["answering_total"])

    first = load_object(paths[0])
    boot = CoreSession.boot(ROOT, offline=True, session_id="v023-r-nf-pins")
    live_pins = replay_session.live_pin_table(
        ROOT, boot.matrix, first["header"]["pins"]
    )
    moved_pins = replay_session.compare_pins(first["header"]["pins"], live_pins)
    count = accounting["regression_candidates"]
    return {
        "schema": "no_flip.census.v1",
        "design": "docs/DESIGN-no-flip.md",
        "roadmap": "docs/ROADMAP-v0.23.md",
        "roadmap_item": "R-NF -- NO-FLIP's regression census",
        "registration_commit": commit,
        "preregistration": "experiments/no_flip_prereg.json",
        "preregistration_sha256": sha256_lf(PREREG),
        "pins": pins,
        "population": observed_population,
        "controls": control,
        "accounting": accounting,
        "gates": {
            "B1_population": "FIRES",
            "B2_exact_sensitivity": "FIRES",
            "B3_hostile_controls": "FIRES",
            "B4_accounting": "FIRES",
            "B5_no_hidden_canonicalizer": "FIRES",
            "B6_publication_completeness": "FIRES",
        },
        "outcome": {
            "regression_candidates": count,
            "denominator": observed_population["answering_total"],
            "sentence": (
                f"{count}/{observed_population['answering_total']} rendered-answer "
                "digest regressions in this recorded window"
            ),
        },
        "method_disclosures": {
            "recorded_pin_bypass": (
                "the replay rebuilds the recorded assumptions and serves the line "
                "directly; genuine live pin drift is reported separately"
            ),
            "genuine_pins_that_moved": moved_pins,
            "macs_verified": False,
            "sha256_match_is_collision_free_proof": False,
        },
        "non_claims": [
            "no semantic-correctness or mathematical-equivalence claim",
            "no claim about recorded non-answer turns or unrecorded sessions",
            "no corpus-improvement, authentication, forgery, or future-stability claim",
        ],
    }


def write_once(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    if temp.exists():
        raise CensusRefusal(f"temporary output already exists: {temp}")
    try:
        with temp.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, indent=1, ensure_ascii=False, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temp, path)
        except FileExistsError as exc:
            raise CensusRefusal(f"registered artifact already exists: {path}") from exc
    finally:
        temp.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--write-registered-census", action="store_true")
    args = parser.parse_args(argv)
    if not args.write_registered_census:
        parser.error("the once-only census requires --write-registered-census")
    result = census()
    write_once(DEFAULT_OUT, result)
    print(json.dumps(result, indent=1, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
