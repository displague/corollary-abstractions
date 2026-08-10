#!/usr/bin/env python3
"""From one live theorem to a proof-search curve (ROADMAP-v0.7 item 1).

Four ranking arms over one versioned held-out theorem set, one shared tactic-
argument generator, one shared ``SearchController``, and Lean as the sole
transition authority.  No arm replays a committed transition: every number
below came from a live PyPantograph round trip.

Arms
----
``arbitrary``   the schema declaration order, leading with ``clear``.
``frequency``   v0.6's WINNER -- one global state-blind order rebuilt from the
                same 44 training rows of ``prover/sample_triples.json`` that
                produced its 64-proposal live solution.
``syntax``      closed-form rules over the rendered goal.  Capability-blind:
                it reads syntax, it has no weights and no training data.
``learned_sN``  the released v0.6 checkpoints ``tactic_policy_s{0,1,2}.pt``,
                27,688 parameters each, ranking the same eight schemas.  They
                are used AS SHIPPED.  Retraining was considered and rejected:
                the new families are expressible in the checkpoint's own
                schema vocabulary, so the checkpoint can rank them, and
                retraining on the new set would have replaced "does the v0.6
                artifact generalize?" with a different question.

Disclosure BEFORE the predictions, because it changes what they are worth
-----------------------------------------------------------------------
A three-theorem plumbing pilot and then a 20-theorem all-blind pilot were run
while this harness was being built, with the learned arm disabled and every
result discarded.  Those runs are why ``implication_chain`` grew two deeper
members and ``disjunction`` and ``project_import`` one each: on the shorter
set, every blind arm solved every chain at the LOWEST budget rung, which is a
vacuous family by AGENTS.md rule 3, not a result.  So:

* the ``learned`` column below, P-PC1, P-PC4's share comparison, P-PC5 and
  P-PC6 are **blind** -- no learned arm and no cross-task ledger has ever
  been computed;
* the ``arbitrary``/``frequency``/``syntax`` columns are **pilot-informed** on
  20 of the 24 theorems and are registered as calibrated expectations rather
  than as blind predictions.  They are still written down and adjudicated,
  because a calibrated expectation that misses is also evidence -- about the
  four new theorems, and about whether adding them changed the ordering.

Registered predictions (P-PC, committed BEFORE the adjudicating run; see the
commit that introduces this file with no results attached).

P-PC1. **Blind.** On EVERY family, the syntax-aware blind arm's solved-rate at
    the middle budget (8 expanded states / 64 proposals) is greater than or
    equal to the learned arms' mean.  v0.6's verdict was that a state-blind
    order beat the learned proposer; a learned loss or tie here is the
    expected result and is reported as a valid result either way.
P-PC2. Solved-rate guesses at that middle budget, out of the family size:

    ======================  =========  =========  ======  ==========
    family (n)              arbitrary  frequency  syntax  learned mu
    ======================  =========  =========  ======  ==========
    conjunction (6)         3          4          5       4
    implication_chain (7)   5          5          6       5
    disjunction (5)         3          3          4       3
    project_import (6)      3          4          4       4
    ======================  =========  =========  ======  ==========

P-PC3. The syntax arm's advantage COLLAPSES on ``project_import``: its margin
    over ``frequency`` in MEAN PROPOSALS-TO-SOLUTION is strictly smaller there
    than on the conjunction family.  Mechanism, registered before any live run
    and independent of the pilot: Lean's pretty printer does not unfold
    ``ProofCurve.Both P Q``, so every conclusion-shape rule sees an atom.
    This is the designed stress on the v0.6 winner.
P-PC4. **Blind.** ``clear`` supplies the plurality of accepted dead branches
    across all arms, and the arbitrary arm -- which proposes it first --
    spends a strictly larger share of its proposals on signatures already
    recorded dead on OTHER theorems than the syntax arm does.
P-PC5. **Blind.** The learned arms do not avoid cross-task dead branches
    better than the syntax arm: their mean cross-task dead-signature proposal
    share is greater than or equal to the syntax arm's.  This is the "does
    learned ranking avoid branches that died elsewhere, across tasks?" test,
    and the prediction is that it does not.
P-PC6. **Blind.** Budget monotonicity holds: for every sampled (theorem, arm),
    a fresh live run at the middle budget agrees with the solved/unsolved
    value derived by thresholding the maximum-budget run.  If any pair
    disagrees, the derived curve is withdrawn and the full ladder is run.
P-PC7. The project-import family is genuinely imported: an ``Init``-only
    server cannot even STATE its propositions.  Recorded as a live control in
    the results file rather than asserted in prose.

Budget choices, stated before the adjudicating run because they bound what can
be claimed: state budgets 4/8/16/32/64, proposal budgets 32/64/128/256/512,
wall-time budgets 0.02/0.05/0.20/1.00/5.00 s.

* The maximum rung (64 states, 512 proposals) is *exactly* v0.6's registered
  live budget, so "solved at maximum budget" means the same thing it meant
  then.  Every theorem in the set carries a witness inside the same eight
  schemas, so a theorem unsolved at the maximum is a ranking failure, not an
  impossible target.
* The middle rung (8 states, 64 proposals) sits where v0.6's own numbers
  discriminate: its blind arm needed 86 proposals, its frequency winner 64,
  its learned arms 61-71.
* The wall-time rungs were calibrated on a three-theorem PLUMBING pilot (no
  learned arm, results discarded) purely to put the ladder inside the range
  where local Pantograph round trips actually land -- sub-millisecond per
  tactic on this host.  Wall time is the noisiest axis here and is reported as
  secondary: it measures Lean RPC latency at least as much as ranking.

ADJUDICATION (appended after the run; the text above is unedited)
-----------------------------------------------------------------
144 live runs, 24 theorems x 6 arms, theorem set sha256 af6f6cb7...

P-PC1 **FIRED** on all four families.  Syntax-aware blind solved-rate at
    (8, 64) vs the learned mean: conjunction 5 vs 4.67, implication_chain
    7 vs 7.00 (tie), disjunction 3 vs 3.00 (tie), project_import 6 vs 4.67.
    Overall 21/24 vs 19.33/24.  v0.6's verdict survives a 24-theorem set:
    a closed-form order still beats the learned proposer, and the two ties
    are ties, not wins.
P-PC2 **PARTIALLY MISSED** -- 7 of 16 registered cells exact.  Correct:
    conjunction's whole row (3/4/5, learned guessed 4 vs 4.67 observed) and
    disjunction's arbitrary, frequency and learned.  Missed:
    * the entire ``implication_chain`` row (guessed 5/5/6/5, observed
      7/7/7/7).  The two deeper members added *after* the pilot did not
      make the family discriminate: an eight-tactic witness still costs
      only 11-15 proposals, because the chain is nearly linear and every
      arm's first guess is right at almost every state.  **The family is
      vacuous as a budget discriminator at every rung** and separates arms
      only on mean proposals (syntax 9.29 vs frequency 12.86).  Filed in
      BACKLOG; the repair is structural branching, not more theorems.
    * ``disjunction`` syntax (guessed 4, observed 3);
    * the whole ``project_import`` row, underestimated by 1-2 everywhere.
P-PC3 **FIRED ON ITS LETTER, REFUTED IN SUBSTANCE.**  The registered
    quantity -- syntax's mean-proposal margin over frequency -- is indeed
    strictly smaller on project_import (1.67) than on conjunction (1.83).
    But 0.16 proposals is not a collapse, and by solved-rate the syntax arm
    scored 6/6 at the middle budget on project_import, its BEST family.  The
    mechanism is real and separately tested (``syntax_order`` provably falls
    back to the arbitrary order on an opaque conclusion), but its consequence
    is small because the FIRST step of every project theorem is still a
    visible ``∀`` goal where the syntax rule fires normally.  Opacity costs
    the blind arm the interior states, not the entrance.
P-PC4 **FIRED AFTER A BLOCKING ACCOUNTING CORRECTION.**  The first run called
    every accepted off-path sibling dead, even when BFS stopped while it was
    still queued.  Frontier-aware accounting now requires the entire queued
    subtree to have been expanded without proof.  Of 227 such transitions,
    ``clear`` supplies 101, the plurality (next: ``constructor`` 66).
    Arbitrary's known-dead share (0.2338) exceeds syntax's (0.2053 pooled).
P-PC5 **FIRED AFTER THAT CORRECTION.**  The registered prediction remains
    under-specified because it did not name a ledger.  On the corrected
    evidence the learned aggregate exceeds syntax under both the own ledger
    (0.1905 vs 0.1553) and pooled ledger (0.2063 vs 0.2053), though the pooled
    margin is only 0.0010 and is not practically meaningful.  The substantive
    answer is still no measurable cross-task avoidance.  The earlier split
    verdict (own missed / pooled fired) is retracted because it rested on the
    invalid off-path-is-dead definition; the prediction text above is kept.
    The substantive answer to the roadmap's question -- "does learned ranking
    avoid branches that died on other tasks?" -- is **no, not measurably**.
P-PC6 **FIRED.**  24 fresh live re-runs at (8, 64), zero disagreements with
    the values derived by thresholding the maximum-budget runs.  The derived
    curve is a real curve.
P-PC7 **FIRED.**  An ``Init``-only server refuses
    ``curve.project_import.both_commute`` with ``Unknown identifier
    `ProofCurve.Both``` -- recorded live in ``import_control``.

Two findings nobody registered, both worth more than the predictions:

1. **The learned arms beat v0.6's winner and still lose.**  Mean proposals:
   syntax 48.29 < learned 49.00 < frequency 51.58 < arbitrary 55.96.  In v0.6
   the frequency order beat the learned mean 64 to 65.0 on one theorem; over
   24 theorems the learned checkpoints now beat it by 2.6 proposals.  The
   ranking result moved; the VERDICT did not, because the syntax-aware order
   this cycle adds is stronger than either.
2. **On this recorded wall-clock run the learned arms trail every blind arm.**
   At 0.02 s: blind 17/24, learned 14/13/14. Proposal count and observed time
   disagree, but fixed arm order and one timing sample confound warm-up and
   host drift. Treat this as a diagnostic that motivates counterbalanced
   latency measurement, not a causal or stable performance claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
for _extra in (ROOT / "prover", ROOT / "scripts", ROOT / "experiments"):
    if str(_extra) not in sys.path:
        sys.path.insert(0, str(_extra))

import theorem_set  # noqa: E402
from curve_search import (  # noqa: E402
    ArbitraryRanker,
    BackendPool,
    FrequencyRanker,
    RunRecord,
    SyntaxRanker,
    run_theorem,
    solved_at,
    solved_by_time,
    state_leakage,
    training_schema_counts,
    verify_budget_monotonicity,
)
from tactic_grammar import SCHEMAS, frequency_order  # noqa: E402
from train_tactic_policy import encode, load_checkpoint  # noqa: E402


NODE_BUDGETS = (4, 8, 16, 32, 64)
PROPOSAL_BUDGETS = (32, 64, 128, 256, 512)
TIME_BUDGETS = (0.02, 0.05, 0.20, 1.00, 5.00)
MIDDLE = 1  # index of the middle budget rung used by the registered guesses

REGISTERED_GUESSES = {
    "conjunction": {"arbitrary": 3, "frequency": 4, "syntax": 5, "learned": 4},
    "implication_chain": {"arbitrary": 5, "frequency": 5, "syntax": 6, "learned": 5},
    "disjunction": {"arbitrary": 3, "frequency": 3, "syntax": 4, "learned": 3},
    "project_import": {"arbitrary": 3, "frequency": 4, "syntax": 4, "learned": 4},
}


@dataclass
class LearnedRanker:
    """The v0.6 checkpoint, ranking the same eight schemas from goal text."""

    model: object
    device: str
    name: str
    state_aware: bool = True

    def order(self, rendered: str) -> tuple[str, ...]:
        data, lengths = encode([rendered])
        with torch.no_grad():
            scores = self.model(data.to(self.device), lengths)[0].cpu()
        return tuple(
            sorted(
                SCHEMAS,
                key=lambda name: (
                    -float(scores[SCHEMAS.index(name)]),
                    SCHEMAS.index(name),
                ),
            )
        )


def gpu_footprint() -> dict[str, object]:
    """Record the GPU footprint this experiment actually cost.

    ROADMAP-v0.7 item 4 fixes a conservative recovery protocol after two
    bugchecks.  Nothing here trains, and the only tensors are three 27,688-
    parameter rankers scoring one 512-byte sequence at a time, so no batch
    ladder applies; the number is recorded so the claim is checkable rather
    than assumed.
    """
    footprint: dict[str, object] = {
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "trains_anything": False,
        "batch_ladder_applicable": False,
    }
    if torch.cuda.is_available():
        footprint["max_memory_allocated_bytes"] = int(
            torch.cuda.max_memory_allocated()
        )
        footprint["max_memory_reserved_bytes"] = int(
            torch.cuda.max_memory_reserved()
        )
        try:
            output = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used,memory.total",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=30, check=False,
            ).stdout.strip().splitlines()
            if output:
                used, total = (int(part) for part in output[0].split(","))
                footprint["whole_device_used_mib"] = used
                footprint["whole_device_total_mib"] = total
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            footprint["nvidia_smi_error"] = str(error)
    return footprint


def import_control(pool: BackendPool, theorems: theorem_set.TheoremSet) -> dict:
    """P-PC7: prove the project family needs the project (live, not asserted)."""
    project = [t for t in theorems.theorems if t.backend != "init"]
    if not project:
        return {"applicable": False}
    init_backend = theorems.backends["init"]
    verifier = pool.verifier(init_backend)
    probe = project[0]
    try:
        verifier.start(probe.id, probe.proposition)
    except Exception as error:  # noqa: BLE001 - the refusal IS the evidence
        return {
            "applicable": True,
            "theorem": probe.id,
            "init_only_refuses": True,
            "message": str(error)[:200],
        }
    return {"applicable": True, "theorem": probe.id, "init_only_refuses": False}


def cross_task_dead(records: list[RunRecord]) -> dict[str, object]:
    """Do branches that died on OTHER theorems keep getting proposed here?

    For each arm, the dead-signature ledger is built LEAVE-ONE-THEOREM-OUT
    from that arm's own runs, so an arm is judged against its own experience
    and never credited with another arm's discoveries.  A pooled ledger (the
    union over all arms) is reported beside it as a common yardstick, because
    a weak arm that explores little would otherwise look virtuous simply for
    having learned nothing.
    """
    by_arm: dict[str, list[RunRecord]] = {}
    for record in records:
        by_arm.setdefault(record.arm, []).append(record)
    pooled: set[tuple[str, str]] = set()
    for record in records:
        pooled.update(item.signature for item in record.dead_branches)

    summary: dict[str, object] = {"pooled_signatures": sorted(pooled)}
    arms: dict[str, object] = {}
    for arm, runs in by_arm.items():
        own_repeats = own_total = 0
        pooled_repeats = pooled_total = 0
        per_theorem = []
        for run in runs:
            others: set[tuple[str, str]] = set()
            for other in runs:
                if other.theorem != run.theorem:
                    others.update(item.signature for item in other.dead_branches)
            pooled_others = {
                item.signature
                for other in records
                if other.theorem != run.theorem
                for item in other.dead_branches
            }
            hits = sum(sig in others for sig in run.proposal_signatures)
            phits = sum(sig in pooled_others for sig in run.proposal_signatures)
            own_repeats += hits
            own_total += len(run.proposal_signatures)
            pooled_repeats += phits
            pooled_total += len(run.proposal_signatures)
            per_theorem.append(
                {
                    "theorem": run.theorem,
                    "proposals": len(run.proposal_signatures),
                    "known_dead_elsewhere": hits,
                    "known_dead_elsewhere_pooled": phits,
                }
            )
        arms[arm] = {
            "own_ledger_share": round(own_repeats / own_total, 4) if own_total else 0.0,
            "pooled_ledger_share": (
                round(pooled_repeats / pooled_total, 4) if pooled_total else 0.0
            ),
            "own_ledger_hits": own_repeats,
            "pooled_ledger_hits": pooled_repeats,
            "proposals": own_total,
            "dead_branches": sum(len(run.dead_branches) for run in runs),
            "per_theorem": per_theorem,
        }
    summary["arms"] = arms
    return summary


def curve(
    records: list[RunRecord], families: list[str], arms: list[str],
    budget_pairs: tuple[tuple[int, int], ...] | None = None,
) -> dict:
    """Solved-rate at every (state, proposal) rung and every time rung."""
    if budget_pairs is None:
        budget_pairs = tuple(zip(NODE_BUDGETS, PROPOSAL_BUDGETS))
    table: dict[str, object] = {}
    for family in ["ALL", *families]:
        family_rows = [
            item for item in records
            if family == "ALL" or item.family == family
        ]
        per_arm: dict[str, object] = {}
        for arm in arms:
            runs = [item for item in family_rows if item.arm == arm]
            if not runs:
                continue
            per_arm[arm] = {
                "n": len(runs),
                "budget_curve": [
                    {
                        "nodes": nodes,
                        "proposals": proposals,
                        "solved": sum(
                            solved_at(item, nodes, proposals) for item in runs
                        ),
                    }
                    for nodes, proposals in budget_pairs
                ],
                "time_curve": [
                    {
                        "seconds": seconds,
                        "solved": sum(
                            solved_by_time(item, seconds) for item in runs
                        ),
                    }
                    for seconds in TIME_BUDGETS
                ],
                "mean_proposals_when_solved": (
                    round(
                        sum(item.proposals for item in runs if item.solved)
                        / max(sum(item.solved for item in runs), 1),
                        2,
                    )
                ),
            }
        table[family] = per_arm
    return table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--theorems", type=Path,
                        default=ROOT / "prover" / "theorems_v1.json")
    parser.add_argument("--checkpoint-dir", type=Path,
                        default=ROOT / "experiments" / "results")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--out", type=Path,
                        default=ROOT / "experiments" / "results" / "proof_curve.json")
    parser.add_argument("--max-nodes", type=int, default=NODE_BUDGETS[-1])
    parser.add_argument("--max-proposals", type=int, default=PROPOSAL_BUDGETS[-1])
    parser.add_argument("--limit", type=int, default=0,
                        help="pilot mode: only the first N theorems")
    parser.add_argument("--no-learned", action="store_true")
    parser.add_argument(
        "--leakage-out", type=Path,
        default=ROOT / "experiments" / "results" / "proof_curve_leakage.json",
        help="separate file: state-level overlap with the training extraction",
    )
    args = parser.parse_args()

    budget_pairs = tuple(
        (nodes, proposals)
        for nodes, proposals in zip(NODE_BUDGETS, PROPOSAL_BUDGETS)
        if nodes <= args.max_nodes and proposals <= args.max_proposals
    )
    if not budget_pairs:
        budget_pairs = ((args.max_nodes, args.max_proposals),)

    theorems = theorem_set.load(args.theorems)
    selected = list(theorems.theorems)
    if args.limit:
        selected = selected[: args.limit]

    triples = json.loads(
        (ROOT / "prover" / "sample_triples.json").read_text(encoding="utf-8")
    )
    counts = training_schema_counts(triples)

    rankers = [
        ArbitraryRanker(),
        FrequencyRanker(tuple(sorted(counts.items()))),
        SyntaxRanker(),
    ]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    checkpoints: dict[str, str] = {}
    if not args.no_learned:
        for seed in args.seeds:
            path = args.checkpoint_dir / f"tactic_policy_s{seed}.pt"
            if not path.exists():
                raise SystemExit(
                    f"missing v0.6 checkpoint {path}; it ships as a release "
                    "asset and is gitignored (prover/README.md)"
                )
            checkpoints[f"learned_s{seed}"] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            rankers.append(
                LearnedRanker(load_checkpoint(path, device), device,
                              f"learned_s{seed}")
            )

    pool = BackendPool()
    records: list[RunRecord] = []
    started = time.perf_counter()
    try:
        control = import_control(pool, theorems)
        for theorem in selected:
            backend = theorems.backend_of(theorem)
            for ranker in rankers:
                verifier = pool.verifier(backend)
                record = run_theorem(
                    verifier, theorem, ranker,
                    args.max_nodes, args.max_proposals,
                )
                records.append(record)
                print(
                    f"{record.theorem:<42} {record.arm:<12} "
                    f"{'SOLVED' if record.solved else record.stop_reason:<9} "
                    f"nodes={record.nodes:<3} proposals={record.proposals:<4} "
                    f"{record.seconds:.2f}s",
                    flush=True,
                )
        # P-PC6: re-run a live sample at the middle budget and compare with the
        # value derived by thresholding.  One theorem per family per arm.
        checks = []
        seen: set[tuple[str, str]] = set()
        for record in records:
            key = (record.family, record.arm)
            if key in seen:
                continue
            seen.add(key)
            theorem = next(t for t in selected if t.id == record.theorem)
            ranker = next(r for r in rankers if r.name == record.arm)
            if (NODE_BUDGETS[MIDDLE] > args.max_nodes
                    or PROPOSAL_BUDGETS[MIDDLE] > args.max_proposals):
                continue
            checks.append(
                verify_budget_monotonicity(
                    pool, theorems, theorem, ranker,
                    NODE_BUDGETS[MIDDLE], PROPOSAL_BUDGETS[MIDDLE],
                    solved_at(record, NODE_BUDGETS[MIDDLE],
                              PROPOSAL_BUDGETS[MIDDLE]),
                )
            )
        # State-level holdout control.  Every arm is measured because schema
        # order changes which accepted states BFS reaches before its first
        # proof.  It lives in its OWN file so adding provenance does not
        # perturb the primary curve artifact.
        training_states = theorem_set.training_states()
        leakage = {
            "experiment": "proof-search-state-leakage-v0.7",
            "theorem_set": theorems.provenance(),
            "selected_theorem_ids": [item.id for item in selected],
            "training_extraction": {
                "file": theorem_set.TRAINING_EXTRACTION.name,
                "sha256": theorem_set.digest(theorem_set.TRAINING_EXTRACTION),
                "distinct_states": len(training_states),
            },
            "checkpoints": checkpoints,
            "budgets": {
                "max_nodes": args.max_nodes,
                "max_proposals": args.max_proposals,
            },
            "arms": {
                ranker.name: state_leakage(
                    pool, theorems, ranker, training_states,
                    args.max_nodes, args.max_proposals,
                )
                for ranker in rankers
            },
        }
    finally:
        pool.close()
    elapsed = time.perf_counter() - started
    if args.leakage_out is not None:
        args.leakage_out.parent.mkdir(parents=True, exist_ok=True)
        args.leakage_out.write_text(
            json.dumps(leakage, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        overlaps = {
            arm: row["states_in_training_extraction"]
            for arm, row in leakage["arms"].items()
        }
        print(
            "state-leakage control by arm: "
            f"{overlaps}; {len(training_states)} extracted training states "
            f"-> {args.leakage_out}"
        )

    families = sorted({item.family for item in selected})
    arms = [ranker.name for ranker in rankers]
    payload = {
        "experiment": "proof-search-curve-v0.7",
        "roadmap_item": "ROADMAP-v0.7 item 1",
        "authority": "Lean/PyPantograph (live); no replayed transition in any arm",
        "theorem_set": theorems.provenance(),
        "backend_projects": {
            name: backend.project_provenance()
            for name, backend in theorems.backends.items()
            if backend.needs_project
        },
        "checkpoints": checkpoints,
        "frequency_counts": counts,
        "frequency_order": list(frequency_order(counts)),
        "budgets": {
            "nodes": [nodes for nodes, _ in budget_pairs],
            "proposals": [proposals for _, proposals in budget_pairs],
            "seconds": list(TIME_BUDGETS),
            "middle_index": (
                budget_pairs.index((NODE_BUDGETS[MIDDLE], PROPOSAL_BUDGETS[MIDDLE]))
                if (NODE_BUDGETS[MIDDLE], PROPOSAL_BUDGETS[MIDDLE]) in budget_pairs
                else None
            ),
            "run_max_nodes": args.max_nodes,
            "run_max_proposals": args.max_proposals,
        },
        "registered_guesses_middle_budget": REGISTERED_GUESSES,
        "import_control": control,
        "budget_monotonicity": checks,
        "curve": curve(records, families, arms, budget_pairs),
        "cross_task_dead_branches": cross_task_dead(records),
        "runs": [item.as_json() for item in records],
        "gpu": gpu_footprint(),
        "host": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "torch": torch.__version__,
        },
        "seconds": round(elapsed, 2),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {args.out} ({len(records)} live runs, {elapsed:.1f}s)")


if __name__ == "__main__":
    main()
