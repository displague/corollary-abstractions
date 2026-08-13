"""Drive one real session end to end and record it (ROADMAP-v0.10 item 5).

Design and registered predictions: docs/DESIGN-v010-harness-session.md.

Three legs over one booted session, chosen so the session exercises the WRITE
gate's DECISION rather than only its happy path:

* **A — authored.** A need the corpus cannot meet, dispatched and found dead;
  a pinned Lean source re-checked by the external verifier; the traced rows
  and the manifest pin; a candidate through `write_stage.accept_write`; and
  then the same need, met by the next session.
* **B — refused.** The same-shaped statement one exponent too large. The
  verifier FAILS it on the axiom audit, and the gate refuses the candidate
  built from it. The working tree is byte-identical afterwards.
* **C — asked, not guessed.** The roadmap's own "why did the chicken cross
  the road?" probe, routed to a path no registered subsystem claims.

Every record in the transcript comes from the components' own structured
objects — `SessionEvent`, `DispatchEvent`, the verdict JSON, `StagingRecord`,
`AcceptanceRecord`. Nothing here re-types a component's conclusion in prose,
because a transcript that paraphrases its sources is a story about a session.

Determinism: the transcript carries no timestamps, no random session id (it
is supplied below), and no absolute paths. It is NOT re-runnable byte-for-
byte, and cannot be: leg A mutates the corpus, so a second run meets a
different world. `--check` therefore re-verifies the RECORD — every digest it
names still matches, every verdict still rechecks, the authored node is still
what the committed seed emits — which is the honest version of the guarantee
the design registered as P5. That correction is adjudicated in the design's
§7 rather than edited into the prediction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from dispatcher import (  # noqa: E402
    DispatchOutcome,
    NeedDispatcher,
    RegisteredPath,
)
from external_verifier import (  # noqa: E402
    check_lean4,
    load_verdict,
    recheck,
)
from frames import FrameSpec, Literal  # noqa: E402
from harness import CoreSession  # noqa: E402
from retrieval import RetrievalState  # noqa: E402
from write_stage import (  # noqa: E402
    ACCEPTED,
    _canonical_seed_source,
    PROVEN,
    REFUSED,
    WriteCandidate,
    accept_write,
    stage_write,
    working_tree_digest,
)

# Fixed so the transcript is a record, not a lottery ticket. A session id is
# an identity, and this session's identity is "the v0.10 item 5 run".
SESSION_ID = "v010-item5-session"

TRANSCRIPT = REPO_ROOT / "experiments" / "harness_session.json"

AUTHORED_ID = "numbertheory.ingested.lean_workbook_22080"
AUTHORED_REFERENCE = "lean_workbook_22080"
AUTHORED_ARTIFACT = "prover/session_triples.json"
AUTHORED_VERDICT = "prover/verifier-verdicts/lean_workbook_22080.lean4.json"

# The gate refuses a PROVEN candidate that has not DECLARED what it will do to
# the matcher: "an undeclared delta is an unregistered prediction". This is
# the session's prediction, made before the gate measures it — one node added
# and NOTHING else moves, because a fully ground residue equation has no slots
# to fold and no partner anywhere in the corpus to twin with. The same claim
# the twin-null streak has made five times; here the gate is what checks it.
EXPECTED_MATCHER_DELTA = {
    "nodes_analyzed": 1,
    "shape_groups": 0,
    "typed_groups": 0,
    "family_groups": 0,
    "aliased_groups": 0,
    "mirror_groups": 0,
    "ladder_violations": 0,
    "parse_problems": 0,
    "slot_schema_gaps": 0,
    "new_typed_twin_partners": [],
}
REFUSED_SOURCE = "prover/lean/session/Threshold26313.lean"
REFUSED_ID = "numbertheory.ingested.lean_workbook_26313"
REFUSED_REFERENCE = "lean_workbook_26313"
CHICKEN = "why did the chicken cross the road?"

SEED_SCRIPT = "scripts/seed_ingested_arithmetic.py"
CORPUS = "ingested_arithmetic"

# Why a corpus of its own rather than an append to data/number_theory: the
# declarative WRITE lane stages NEW seed / NEW corpus pairs only — appending
# to an existing corpus "needs a trusted patch format" (write_stage's
# `seed_ownership` refusal), which is the carried-open multi-corpus WRITE
# patch in ROADMAP-v0.10 §7. The design note registered this leg as an
# append; the gate refused, and the refusal is right, so the session takes
# the lane that exists. Adjudicated in the design's §7 rather than edited
# into §5.
# The session proposes the gate's OWN canonical declarative seed
# (`write_stage._canonical_seed_source`): `CORPUS = json.loads(<literal>)`
# and nothing else, parsed as data and never executed. Rendering it with the
# gate's renderer rather than hand-shaping a file is the point — an untrusted
# proposer gets exactly one accepted shape, and the session is an untrusted
# proposer.


# The node the session authors, built with the SAME helpers the hand-written
# seeds use (imported, not re-implemented, so a schema change reaches this
# route too). The gate judges the node the scratch regeneration EMITS from
# the seed text below, so anything claimed here that the seed does not carry
# is caught by the gate rather than believed.


def authored_node() -> dict:
    from seed_number_theory import (  # noqa: PLC0415
        LEAN_WORKBOOK, MOD_FN, MUL, POW, node, slot, sym,
    )

    built = node(
        AUTHORED_ID,
        "Two to the Thirtieth Leaves 824 Modulo 1000 (Ingested)",
        "proposition", "formal", "modular_arithmetic",
        "ingested_ground_arithmetic",
        "2^30 % 1000 = 824", "2^{30} \\bmod 1000 = 824",
        [{"form_id": "ascii_ground",
          "notation_system": "ascii",
          "expression": "2^30 % 1000 = 824",
          "scope_note": "The same ground surface the pinned Lean source "
          "states as `(2^30) % 1000 = 824`; translated by the correspondence "
          "rung's ground-arithmetic fragment, not the propositional one."}],
        "ingested_ground_residue",
        "MOD(2 ^ 30, 1000) = 824",
        [slot("GROUND_MODULUS_1000", "constant",
              "documentation of the ground modulus 1000 \u2014 the template "
              "itself is fully ground and carries no matcher slots")],
        ["Fully ground: no slots, no variables \u2014 a single decidable "
         "arithmetic fact, the exact shape of the traced Lean goal "
         "`\u22a2 2 ^ 30 % 1000 = 824`.",
         "MOD is the corpus reading of Lean's `%` on \u2115, already declared "
         "ordered_compose in the head algebra; the ground-arithmetic "
         "fragment translates the goal with no slot folding, so CORRESPONDS "
         "here is exact structural identity of the ground equation.",
         "The last three digits of 2^30 = 1073741824 \u2014 the ordinary "
         "reason a problem set asks for it, and irrelevant to what the "
         "verifier actually certified."],
        [sym("1000", "constant", "modulus",
             "The fixed modulus: a ground object, not a placeholder.", 0)],
        [MUL, POW],
        "2^30 leaves remainder 824 on division by 1000: the ground residue "
        "fact stated by Lean-workbook problem lean_workbook_22080, restated "
        "verbatim from the pinned extract.",
        "Authored BY the recorded v0.10 item 5 session through the audited "
        "route (docs/DESIGN-v010-harness-session.md): a dispatched need the "
        "corpus could not meet -> external-verifier lean4 verdict over the "
        "pinned source prover/lean/session/Session22080.lean (exit 0, no "
        "warnings, axiom footprint EMPTY \u2014 `%` on \u2115 decides "
        "without propext, where the first bridge's `\u2223` needed it) -> "
        "transition rows traced by prover/ExtractData.win.lean and "
        "post-processed by scripts/trace_to_triples.py -> digest pin in "
        "prover/proof-artifact-manifest.json -> this link, applied by "
        "write_stage.accept_write. The verdict certifies exactly what it "
        "checked, not correctness in general.",
        ["Natural-number carrier: `%` and `^` are read on \u2115, where they "
         "agree with the corpus heads; no subtraction or division appears, "
         "so no monus/floor-division carrier hazard arises"],
        [LEAN_WORKBOOK],
        functionals=[MOD_FN],
        constants=[{"symbol": "1000", "value": 1000,
                    "description": "the modulus"},
                   {"symbol": "824", "value": 824,
                    "description": "the residue"}],
        keywords=["ingested", "lean workbook", "modular arithmetic",
                  "decidable", "external verifier", "verified_by",
                  "authored in session"])
    built["verified_by"] = [{
        "system": "lean4",
        "artifact": AUTHORED_ARTIFACT,
        "reference": AUTHORED_REFERENCE,
    }]
    return built




# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corpus_ids(repo_root: Path) -> set[str]:
    ids: set[str] = set()
    for path in sorted((repo_root / "data").glob("*/nodes.json")):
        corpus = json.loads(path.read_text(encoding="utf-8"))
        ids.update(n["statement_id"] for n in corpus["statement_nodes"])
    return ids


def need_state(session: CoreSession, key: str, frame_name: str) -> RetrievalState:
    frame = session.executor.open_frame(
        FrameSpec(frame=frame_name, retrieval="open")
    )
    return RetrievalState.from_unknown(
        session.executor, frame, "answer", key, Literal("request", "needs", key)
    )


def dispatch_leg(
    session: CoreSession, key: str, subsystem: str, *, registered: bool,
    frame_name: str,
) -> dict:
    """One dispatched need, recorded from the dispatcher's own events."""

    registry = {
        subsystem: RegisteredPath(
            subsystem,
            registered=registered,
            build_state=lambda _sid: need_state(session, key, frame_name),
        )
    }
    dispatcher = NeedDispatcher.for_session(session, registry)
    result = dispatcher.dispatch(session.session_id, subsystem)
    return {
        "key": key,
        "routed_to": subsystem,
        "stop_reason": result.stop_reason.value,
        "materialized": result.materialized,
        "reason": result.reason,
        "events": [
            {
                "hop": event.hop,
                "subsystem_id": event.subsystem_id,
                "outcome": event.outcome.value,
                "detail": event.detail,
            }
            for event in result.events
        ],
    }


def seed_with_authored_node(repo_root: Path, corpus: str = CORPUS) -> str:
    """The FULL seed text the candidate proposes — never a node payload."""

    existing = repo_root / SEED_SCRIPT
    if existing.is_file():
        return existing.read_text(encoding="utf-8")
    payload = {
        "schema": "../../schema/equation-node.schema.json",
        "corpus_id": f"{corpus}.session.v1",
        "discipline": corpus,
        "version": "1.0.0-alpha",
        "statement_nodes": [authored_node()],
    }
    return _canonical_seed_source(payload, corpus)


def authored_candidate(repo_root: Path) -> WriteCandidate:
    rows = json.loads(
        (repo_root / AUTHORED_ARTIFACT).read_text(encoding="utf-8")
    )
    return WriteCandidate(
        statement_id=AUTHORED_ID,
        corpus=CORPUS,
        seed_script=SEED_SCRIPT,
        seed_source=seed_with_authored_node(repo_root),
        seed_source_path=SEED_SCRIPT,
        rung=PROVEN,
        rationale=(
            "Authored by the recorded v0.10 item 5 session. The PROVEN rung "
            "rests on a committed external-verifier lean4 verdict over a "
            "pinned source and the transition rows traced from that same "
            "source; the verdict certifies elaboration and axiom footprint, "
            "not correctness in general."
        ),
        artifact=AUTHORED_ARTIFACT,
        artifact_sha256=digest(repo_root / AUTHORED_ARTIFACT),
        reference=AUTHORED_REFERENCE,
        transition_trace=tuple(rows),
        expected_matcher_delta=EXPECTED_MATCHER_DELTA,
    )


def refused_candidate(repo_root: Path) -> WriteCandidate:
    """A candidate for the statement the verifier just refused to certify.

    Deliberately submitted anyway. The session already knows the verdict is a
    FAIL, so its own politeness would be enough to stop here — and a gate that
    is only ever handed candidates its caller already approved has not been
    shown to be a gate.
    """

    return WriteCandidate(
        statement_id=REFUSED_ID,
        corpus="refused_arithmetic",
        seed_script="scripts/seed_refused_arithmetic.py",
        seed_source=seed_with_authored_node(
            repo_root, "refused_arithmetic"),
        seed_source_path="scripts/seed_refused_arithmetic.py",
        rung=PROVEN,
        rationale=(
            "Submitted to the gate AFTER its verifier check failed, to record "
            "that the refusal is the gate's and not merely the caller's."
        ),
        artifact=AUTHORED_ARTIFACT,
        artifact_sha256=digest(repo_root / AUTHORED_ARTIFACT),
        reference=REFUSED_REFERENCE,
        transition_trace=(),
        expected_matcher_delta=EXPECTED_MATCHER_DELTA,
    )


# --------------------------------------------------------------------------
# the session
# --------------------------------------------------------------------------


def run_session(repo_root: Path, *, apply: bool) -> dict:
    session = CoreSession.boot(repo_root, session_id=SESSION_ID)
    matrix = [
        {"subsystem": record.subsystem_id, "liveness": record.liveness.value,
         "optional": record.optional}
        for record in session.matrix.records
    ]
    transcript: dict = {
        "session_id": session.session_id,
        "design": "docs/DESIGN-v010-harness-session.md",
        "honesty_boundary": (
            "The boot matrix reports LIVENESS ONLY: a registered row is not "
            "evidence that a verifier is sound. A verifier PASS recorded "
            "below certifies exactly the check it names, not correctness in "
            "general."
        ),
        "boot": {
            "matrix": matrix,
            "events": [
                {"subsystem_id": e.subsystem_id, "kind": e.kind,
                 "detail": e.detail}
                for e in session.events
            ],
        },
        "corpus_before": sorted(corpus_ids(repo_root)),
        "legs": [],
    }

    tree_before = working_tree_digest(repo_root)

    # -- Leg A ------------------------------------------------------------
    leg_a: dict = {"name": "A", "intent": "author a node the corpus lacks"}
    leg_a["need_before_write"] = dispatch_leg(
        session, AUTHORED_ID, "retrieve.five_store", registered=True,
        frame_name="runtime.frames.session_leg_a",
    )
    ok, detail = recheck(repo_root, AUTHORED_VERDICT)
    verdict = load_verdict(repo_root, AUTHORED_VERDICT)
    leg_a["verifier"] = {
        "verdict_path": AUTHORED_VERDICT,
        "verdict": verdict["verdict"],
        "axioms": verdict["evidence"].get("axioms"),
        "checks": verdict["checks"],
        "recheck_ok": ok,
        "recheck_detail": detail,
    }
    leg_a["artifact"] = {
        "path": AUTHORED_ARTIFACT,
        "sha256": digest(repo_root / AUTHORED_ARTIFACT),
        "rows": len(json.loads(
            (repo_root / AUTHORED_ARTIFACT).read_text(encoding="utf-8"))),
    }

    if apply and AUTHORED_ID not in corpus_ids(repo_root):
        staged, accepted = accept_write(authored_candidate(repo_root),
                                        repo_root)
        leg_a["write"] = {
            "decision": staged.outcome,
            "rung": staged.rung,
            "record_id": staged.record_id,
            "checks": [c["check"] for c in staged.checks],
            "applied": accepted is not None,
            "applied_paths": sorted(accepted.applied) if accepted else [],
            "node_id": accepted.node_id if accepted else "",
            "verifications": (
                [v["check"] for v in accepted.verifications] if accepted else []
            ),
        }
    else:
        leg_a["write"] = {
            "decision": "not applied",
            "applied": False,
            "note": (
                "dry run"
                if not apply
                else "the authored node is already in the corpus; this run "
                "did not re-apply it (see --check)"
            ),
        }
    transcript["legs"].append(leg_a)

    # -- Leg A' — the next session meets the need ---------------------------
    after = CoreSession.boot(repo_root, session_id=SESSION_ID + "-next")
    transcript["legs"].append({
        "name": "A'",
        "intent": (
            "the same need, seen by the NEXT session — the running session's "
            "store is a boot-time snapshot, so the write it just applied is "
            "not visible to itself"
        ),
        "need_after_write": dispatch_leg(
            after, AUTHORED_ID, "retrieve.five_store", registered=True,
            frame_name="runtime.frames.session_leg_a_next",
        ),
    })

    # -- Leg B ------------------------------------------------------------
    failed = check_lean4(
        repo_root, REFUSED_SOURCE, REFUSED_ID, "(2^2006) % 7 = 4",
        REFUSED_REFERENCE,
    )
    staged_b = stage_write(refused_candidate(repo_root), repo_root)
    transcript["legs"].append({
        "name": "B",
        "intent": "the same shape, one exponent too large — refused twice",
        "verifier": {
            "source": REFUSED_SOURCE,
            "verdict": failed.verdict,
            "axioms": failed.evidence.get("axioms"),
            "reason": failed.evidence.get("reason"),
        },
        "write": {
            "decision": staged_b.outcome,
            "rung": staged_b.rung,
            "refusal": staged_b.refusal,
            "tree_byte_identical": (
                staged_b.working_tree_digest_before
                == staged_b.working_tree_digest_after
            ),
            "applied": False,
        },
    })

    # -- Leg C ------------------------------------------------------------
    transcript["legs"].append({
        "name": "C",
        "intent": "an unparseable request must ASK or abstain, never answer",
        "prompt": CHICKEN,
        "dispatch": dispatch_leg(
            session, CHICKEN, "tool.freeform_answer", registered=False,
            frame_name="runtime.frames.session_leg_c",
        ),
        "minted": [],
    })

    transcript["corpus_after"] = sorted(corpus_ids(repo_root))
    transcript["tree_unchanged_by_refusals"] = (
        working_tree_digest(repo_root) == tree_before
        if not apply or AUTHORED_ID in transcript["corpus_before"]
        else None
    )
    return transcript


def render(transcript: dict) -> bytes:
    return (
        json.dumps(transcript, indent=1, ensure_ascii=False, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def check(repo_root: Path) -> int:
    """Re-verify the committed record: digests, verdicts, and the node."""

    if not TRANSCRIPT.is_file():
        print(f"no committed transcript at {TRANSCRIPT}", file=sys.stderr)
        return 1
    recorded = json.loads(TRANSCRIPT.read_text(encoding="utf-8"))
    problems: list[str] = []

    leg_a = next(leg for leg in recorded["legs"] if leg["name"] == "A")
    artifact = leg_a["artifact"]
    live = digest(repo_root / artifact["path"])
    if live != artifact["sha256"]:
        problems.append(
            f"{artifact['path']} now digests {live}, transcript recorded "
            f"{artifact['sha256']}"
        )
    ok, detail = recheck(repo_root, AUTHORED_VERDICT)
    if not ok:
        problems.append(f"verdict no longer rechecks: {detail}")
    if AUTHORED_ID not in corpus_ids(repo_root):
        problems.append(f"{AUTHORED_ID} is not in the corpus any more")
    if recorded["legs"][-1]["dispatch"]["materialized"]:
        problems.append("the chicken leg is recorded as materialized")

    for problem in problems:
        print(f"FAIL {problem}")
    if problems:
        return 1
    print("record re-verified: artifact digest, verdict recheck, authored "
          "node present, chicken leg still abstains")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true",
        help="re-verify the committed record instead of running the session",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="run every leg but never apply the authored write",
    )
    parser.add_argument("--out", type=Path, default=TRANSCRIPT)
    args = parser.parse_args(argv)

    if args.check:
        return check(REPO_ROOT)

    transcript = run_session(REPO_ROOT, apply=not args.dry_run)
    payload = render(transcript)
    if args.dry_run:
        print(payload.decode("utf-8"))
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(payload)
    print(f"session transcript -> {args.out.relative_to(REPO_ROOT)}")
    for leg in transcript["legs"]:
        summary = leg.get("write", {}).get("decision") or leg.get(
            "dispatch", {}
        ).get("stop_reason") or leg.get("need_after_write", {}).get(
            "stop_reason"
        )
        print(f"  leg {leg['name']}: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
