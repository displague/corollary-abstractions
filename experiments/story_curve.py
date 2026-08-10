#!/usr/bin/env python3
"""The SAME policy protocol over story actions (ROADMAP-v0.7 item 1, last bullet).

The roadmap's constraint is exact: *"Run the same policy protocol over story
actions before claiming a general controller. Domain-specific weights are
acceptable; a second controller is not."*  So this module reuses, unchanged:

* :class:`controller.SearchController` -- the same bounded breadth-first
  search that drives the Lean arms, imported, not reimplemented;
* the ``BranchPolicy`` protocol and the same two-layer split -- a **ranker**
  orders action SCHEMAS, a closed-form **argument generator** turns a schema
  into concrete actions;
* :class:`oracle_controller_demo.StoryFrameVerifier` as the sole transition
  authority, exactly as Lean is on the proof side.  A beat that the frame
  refutes supplies no next state.

What is domain-specific, and allowed to be: the schema vocabulary (five story
transitions instead of eight tactic schemas), the argument generator, the
syntax-aware rules, and the learned weights.  There is no second controller,
no second search, and no second verdict vocabulary.

Disclosure, same rule as the proof side
--------------------------------------
Two construction pilots were run and discarded while this module was written:
one with a single seed on a first draft of the briefs, and one after the
briefs were deepened.  They are why every brief now offers two plantable
elements and an outcome that binds nothing -- the first draft produced almost
no accepted dead branches, and a story family with no dead branches cannot
answer the roadmap's pruning-evidence bullet.  Marked below: **informed**
means a pilot has already shown me the direction; **blind** means it has not.

Registered predictions (P-SC, committed BEFORE the adjudicating run):

P-SC1. **Blind, and the point of this module.**  Under the SHARED breadth-
    first controller, ranking headroom in the story domain is structurally
    tiny, because ``SearchController`` expands every node's full candidate
    list and the story grammar fixes the solution at depth five: everything
    above it must be expanded whatever the order.  Concretely -- the spread
    between the best and worst arm's proposals-to-solution on any single
    brief stays under 5% of that brief's mean, while on the proof side the
    arbitrary-to-syntax spread exceeds 20% on at least one theorem.  The
    protocol transfers; the LEVER does not.  This is the honest form of "one
    shared policy protocol in both domains".
P-SC2. **Informed for seed 0, blind for seeds 1-2.**  The learned story
    ranker ties or loses to the syntax arm on mean proposals-to-solution over
    the held-out briefs.  Same shape as the v0.6 proof verdict.
P-SC3. The state-blind FREQUENCY order is degenerate in this domain and
    collapses onto the arbitrary order.  Every legal story fires each of the
    five schemas exactly once, so a global count carries no signal at all.
    This is a claim about the baseline, not the model, and it is recorded
    because a baseline that cannot differ is not a control.
P-SC4. **Informed.**  Every arm SOLVES every held-out brief at the maximum
    budget: with a five-step chain and a verifier that refuses every illegal
    order, breadth-first search alone is sufficient.  Ranking buys proposals,
    not reachability.
P-SC5. **Blind.**  Planting the decoy element is ACCEPTED by the frame and
    strands an obligation no outcome discharges, so every arm records
    accepted dead branches, and no arm's cross-brief dead-signature share
    falls below half of any other's.  Dead-branch avoidance, like ranking,
    has no room to differ here.
P-SC6. Domain separation holds: the learned story ranker is a different weight
    set over the same architecture, and no tactic schema name appears in the
    story vocabulary or vice versa.  Checked in the result file and by test,
    not asserted in prose.

Budgets match the proof side exactly (states 4/8/16/32/64, proposals
32/64/128/256/512, seconds 0.02/0.05/0.20/1.00/5.00) so one budget axis reads
across both domains.  A step-shaped story curve is the expected consequence of
P-SC1 and is reported as such, with mean proposals-to-solution beside it as the
finer-grained comparator.

ADJUDICATION (appended after the run; the text above is unedited)
-----------------------------------------------------------------
48 runs, 8 briefs x 6 arms, 95.1 s, 20 training rows, three seeds.

P-SC1 **FIRED**, and it is the result of this arm.  The largest
    best-to-worst proposal spread on any brief is **1.07%** (373 vs 377),
    against a largest proof-side spread of **65.6%** (8 vs 15 on
    ``curve.implication_chain.triple_middle``).  Same controller, same policy
    protocol, same two-layer ranker/argument split -- and the ranking lever
    is two orders of magnitude smaller in the story domain.  The mechanism is
    structural, not a property of the weights: ``SearchController`` expands
    every node's full candidate list, and the story grammar fixes the
    solution at depth five, so all 31 nodes above it are expanded whatever
    the order.  Every arm expands exactly 32 nodes.
P-SC2 **FIRED.**  Held-out mean proposals-to-solution: syntax 373.0,
    learned 373.0 / 373.0 / 377.0.  Two seeds tie, one loses; none wins.
P-SC3 **FIRED.**  Each of the five schemas occurs exactly 4 times in the 20
    training rows, so the frequency order is the alphabetical order and the
    frequency arm is byte-identical to the arbitrary arm on every brief.  A
    state-blind count is not a control in a grammar where every action fires
    once per story.
P-SC4 **FIRED.**  8/8 briefs solved by every arm at (64, 512); 0/8 at every
    lower rung, for every arm.  The curve is a single step, exactly as
    P-SC1's mechanism predicts.
P-SC5 **FIRED.**  Every arm records 496 accepted dead branches -- the decoy
    plant strands an obligation no outcome discharges -- and the cross-brief
    dead-signature share is 0.1823 for five arms and 0.1804 for the sixth.
    No arm is within a factor of two of any other because no arm differs at
    all.  Dead-branch avoidance has the same non-existent headroom that
    ranking does.
P-SC6 **FIRED.**  ``STORY_SCHEMAS`` and ``tactic_grammar.SCHEMAS`` are
    disjoint, and ``tests/test_proof_curve.py`` asserts the story module's
    ``SearchController`` IS ``controller.SearchController`` by object
    identity, not by name.

Honest limit this arm establishes: "one shared policy protocol works in both
domains" is TRUE and nearly EMPTY as stated.  The protocol ports; the thing it
buys does not.  Claiming a general controller on this evidence would mean
claiming a lever that measurably is not there -- and a best-first or
depth-limited search, which this cycle deliberately did not build because it
would have been a second controller, is where the story-side headroom would
have to come from.
"""

from __future__ import annotations

import argparse
import json
import platform
import random
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import torch

ROOT = Path(__file__).resolve().parent.parent
for _extra in (ROOT / "scripts", ROOT / "prover", ROOT / "experiments"):
    if str(_extra) not in sys.path:
        sys.path.insert(0, str(_extra))

from controller import (  # noqa: E402
    Action,
    ActionKind,
    SearchController,
    SearchResult,
)
from frames import (  # noqa: E402
    CHEKHOV_GUN,
    FRAME_CONSISTENCY,
    NO_DEUS,
    FrameSpec,
    Literal,
)
from oracle_controller_demo import (  # noqa: E402
    NarrativeElement,
    StoryFrameVerifier,
    StoryState,
)
from train_tactic_policy import TacticRanker, encode  # noqa: E402


#: The story schema vocabulary.  Disjoint from ``tactic_grammar.SCHEMAS`` by
#: construction -- domain weights, not a shared label space.
STORY_SCHEMAS = ("discharge", "introduce", "obstruct", "plant", "resolve")
ARBITRARY_STORY_ORDER = STORY_SCHEMAS  # alphabetical: deterministic, uninformed

NODE_BUDGETS = (4, 8, 16, 32, 64)
PROPOSAL_BUDGETS = (32, 64, 128, 256, 512)
TIME_BUDGETS = (0.02, 0.05, 0.20, 1.00, 5.00)
MIDDLE = 1


@dataclass(frozen=True)
class StoryBrief:
    """One authored story problem: the search must find the legal ordering."""

    id: str
    split: str
    agent: str
    desires: tuple[str, ...]
    trait: str
    denied_trait: str
    element: str
    element_surface: str
    decoy_element: str
    decoy_surface: str
    plant_mention: str
    obstacles: tuple[str, ...]
    outcomes: tuple[str, ...]

    def spec(self) -> FrameSpec:
        return FrameSpec(
            frame=f"runtime.frames.{self.id}",
            title=self.id.replace("_", " "),
            declarations=(
                ("agent", Literal("story", "agent", self.agent)),
                (self.trait, Literal(self.agent, "trait", self.trait)),
                (
                    f"no_{self.denied_trait}",
                    Literal(self.agent, "trait", self.denied_trait,
                            polarity=False),
                ),
            ),
            governed_by=(FRAME_CONSISTENCY, CHEKHOV_GUN, NO_DEUS),
        )

    def elements(self) -> tuple[NarrativeElement, ...]:
        return (
            NarrativeElement(self.element, (self.element_surface,)),
            NarrativeElement(self.decoy_element, (self.decoy_surface,)),
        )

    def verifier(self) -> StoryFrameVerifier:
        return StoryFrameVerifier(spec=self.spec(), elements=self.elements())


def _span(text: str, needle: str) -> tuple[int, int]:
    start = text.index(needle)
    return start, start + len(needle)


def story_candidates(
    brief: StoryBrief, state: StoryState
) -> dict[str, tuple[Action, ...]]:
    """Closed-form argument generation for one story state.

    Mirrors :func:`tactic_grammar.candidates`: every arm receives this exact
    candidate set, in this exact within-schema order, and may only permute the
    schema keys.  Offsets are computed from the rendered text, never guessed,
    and the decoy element is offered alongside the real one so that choosing
    *which* element to plant is a real branch rather than a formality.
    """
    shared = {"agent": brief.agent}
    introduce: list[Action] = []
    for desire in brief.desires:
        for trait in (brief.trait, brief.denied_trait):
            introduce.append(
                Action.build(
                    ActionKind.GEN, "introduce",
                    {**shared, "desire": desire, "trait": trait},
                )
            )

    desire = state.desire or brief.desires[0]
    plant: list[Action] = []
    for element, surface in (
        (brief.element, brief.element_surface),
        (brief.decoy_element, brief.decoy_surface),
    ):
        if surface not in brief.plant_mention:
            continue
        start, end = _span(brief.plant_mention, surface)
        plant.append(
            Action.build(
                ActionKind.GEN, "plant",
                {
                    **shared,
                    "desire": desire,
                    "event_id": f"{element.replace(' ', '_')}_planted",
                    "element": element,
                    "mention": brief.plant_mention,
                    "binds": f"{element}@{start}:{end}",
                },
            )
        )

    obstruct = [
        Action.build(
            ActionKind.GEN, "obstruct",
            {**shared, "desire": desire, "obstacle": obstacle},
        )
        for obstacle in brief.obstacles
    ]

    resolve: list[Action] = []
    for outcome in brief.outcomes:
        binds = []
        for element, surface in (
            (brief.element, brief.element_surface),
            (brief.decoy_element, brief.decoy_surface),
        ):
            if surface in outcome:
                start, end = _span(outcome, surface)
                binds.append(f"{element}@{start}:{end}")
        resolve.append(
            Action.build(
                ActionKind.GEN, "resolve",
                {
                    **shared,
                    "desire": desire,
                    "outcome": outcome,
                    **({"binds": ";".join(binds)} if binds else {}),
                },
            )
        )

    discharge = [
        Action.build(
            ActionKind.GEN, "discharge",
            {
                **shared,
                "desire": desire,
                "event_id": f"{element.replace(' ', '_')}_discharged",
                "element": element,
            },
        )
        for element in (brief.element, brief.decoy_element)
    ]

    return {
        "introduce": tuple(introduce),
        "plant": tuple(plant),
        "obstruct": tuple(obstruct),
        "resolve": tuple(resolve),
        "discharge": tuple(discharge),
    }


def render_story(state: StoryState) -> str:
    """A deterministic text view of story progress, for state-aware rankers."""
    lines = [f"agent: {state.agent}", f"desire: {state.desire}"]
    lines.extend(f"{beat.role}: {beat.text}" for beat in state.beats)
    lines.append(f"beats: {len(state.beats)}")
    for obligation in state.frame_state.obligations:
        lines.append(
            f"obligation {obligation.element}: "
            f"{'outstanding' if obligation.outstanding else 'discharged'}"
        )
    return "\n".join(lines)


@dataclass(frozen=True)
class ArbitraryStoryRanker:
    name: str = "arbitrary"
    state_aware: bool = False

    def order(self, rendered: str) -> tuple[str, ...]:
        del rendered
        return ARBITRARY_STORY_ORDER


@dataclass(frozen=True)
class FrequencyStoryRanker:
    counts: tuple[tuple[str, int], ...]
    name: str = "frequency"
    state_aware: bool = False

    def order(self, rendered: str) -> tuple[str, ...]:
        del rendered
        counts = dict(self.counts)
        return tuple(
            sorted(
                STORY_SCHEMAS,
                key=lambda name: (
                    -counts.get(name, 0), ARBITRARY_STORY_ORDER.index(name)
                ),
            )
        )


@dataclass(frozen=True)
class SyntaxStoryRanker:
    """Closed-form rules over beat structure and the obligation ledger.

    Every rule is a fact the state already carries: how many beats exist, what
    role the last one has, and whether any obligation is outstanding.  No
    weights, no training data, no prose inspection.
    """

    name: str = "syntax"
    state_aware: bool = True

    def order(self, rendered: str) -> tuple[str, ...]:
        roles = [
            line.split(":", 1)[0]
            for line in rendered.split("\n")
            if line.split(":", 1)[0] in {"setup", "complication", "resolution"}
        ]
        outstanding = "outstanding" in rendered
        planted = "obligation " in rendered
        scores = {name: 0.0 for name in STORY_SCHEMAS}
        if not roles:
            scores["introduce"] = 4.0
        elif roles == ["setup"] and not planted:
            scores["plant"] = 4.0
        elif roles == ["setup"]:
            scores["obstruct"] = 4.0
        elif roles == ["setup", "complication"]:
            scores["resolve"] = 4.0
        elif roles[-1:] == ["resolution"] and outstanding:
            scores["discharge"] = 4.0
        return tuple(
            sorted(
                STORY_SCHEMAS,
                key=lambda name: (
                    -scores[name], ARBITRARY_STORY_ORDER.index(name)
                ),
            )
        )


@dataclass
class LearnedStoryRanker:
    model: object
    device: str
    name: str = "learned"
    state_aware: bool = True

    def order(self, rendered: str) -> tuple[str, ...]:
        data, lengths = encode([rendered])
        with torch.no_grad():
            scores = self.model(data.to(self.device), lengths)[0].cpu()
        return tuple(
            sorted(
                STORY_SCHEMAS,
                key=lambda name: (
                    -float(scores[STORY_SCHEMAS.index(name)]),
                    ARBITRARY_STORY_ORDER.index(name),
                ),
            )
        )


@dataclass
class RankedStoryPolicy:
    """The same two-layer policy shape the Lean arms use."""

    brief: StoryBrief
    ranker: object
    orders: list[tuple[str, ...]] = field(default_factory=list)

    def propose_all(self, state: StoryState, trace) -> Iterable[Action]:
        del trace
        available = story_candidates(self.brief, state)
        order = self.ranker.order(render_story(state))
        self.orders.append(order)
        return tuple(
            action for schema in order for action in available.get(schema, ())
        )


def story_complete(state: StoryState) -> bool:
    return (
        tuple(beat.role for beat in state.beats)
        == ("setup", "complication", "resolution")
        and bool(state.frame_state.obligations)
        and not any(
            obligation.outstanding
            for obligation in state.frame_state.obligations
        )
    )


@dataclass(frozen=True)
class StoryRun:
    brief: str
    split: str
    arm: str
    solved: bool
    stop: str
    nodes: int
    states: int
    proposals: int
    accepted: int
    rejected: int
    seconds: float
    solution: tuple[str, ...]
    dead_branches: tuple[tuple[str, str], ...]
    proposal_signatures: tuple[tuple[str, str], ...]

    def as_json(self) -> dict[str, object]:
        return {
            "brief": self.brief,
            "split": self.split,
            "arm": self.arm,
            "solved": self.solved,
            "stop": self.stop,
            "nodes": self.nodes,
            "states": self.states,
            "proposals": self.proposals,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "seconds": round(self.seconds, 4),
            "solution": list(self.solution),
            "dead_branches": [list(item) for item in self.dead_branches],
        }


def _story_signature(entry) -> tuple[str, str]:
    beats = tuple(beat.role for beat in entry.state_before.beats)
    return ("|".join(beats) or "empty", entry.action.name)


def run_brief(
    brief: StoryBrief, ranker: object, max_nodes: int, max_proposals: int
) -> StoryRun:
    verifier = brief.verifier()
    policy = RankedStoryPolicy(brief, ranker)
    started = time.perf_counter()
    result: SearchResult[StoryState] = SearchController[StoryState](
        max_nodes, max_proposals
    ).run(verifier.initial_state(), policy, verifier, story_complete)
    elapsed = time.perf_counter() - started
    on_path = {entry.index for entry in result.solution_trace}
    dead = tuple(
        _story_signature(entry)
        for entry in result.trace
        if entry.accepted and entry.index not in on_path
    )
    return StoryRun(
        brief=brief.id,
        split=brief.split,
        arm=ranker.name,
        solved=result.solved,
        stop=result.stop_reason.value,
        nodes=result.nodes_expanded,
        states=result.states_seen,
        proposals=result.proposals,
        accepted=result.accepted_proposals,
        rejected=result.rejected_proposals,
        seconds=elapsed,
        solution=tuple(
            entry.action.name for entry in result.solution_trace
        ),
        dead_branches=dead,
        proposal_signatures=tuple(
            _story_signature(entry) for entry in result.trace
        ),
    )


def oracle_walk(brief: StoryBrief) -> tuple[tuple[str, str], ...]:
    """(rendered state, schema) rows along the brief's one legal ordering.

    Rows are read off an ACCEPTED solution path, so every label is a
    transition the frame verifier admitted -- never hand-labelled.  The walk
    is driven by the ARBITRARY arm on purpose: distilling the syntax baseline
    into the learned arm and then reporting the learned arm as an independent
    comparison would be circular.  The schema sequence is a property of the
    grammar, not of the arm that found it.
    """
    verifier = brief.verifier()
    policy = RankedStoryPolicy(brief, ArbitraryStoryRanker())
    result = SearchController[StoryState](64, 512).run(
        verifier.initial_state(), policy, verifier, story_complete
    )
    return tuple(
        (render_story(entry.state_before), entry.action.name)
        for entry in result.solution_trace
    )


def train_story_ranker(
    rows: tuple[tuple[str, str], ...], seed: int, epochs: int, device: str
) -> TacticRanker:
    """Domain weights over the SAME architecture as the tactic ranker."""
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    random.seed(seed)
    model = TacticRanker(classes=len(STORY_SCHEMAS)).to(device)
    data, lengths = encode([row[0] for row in rows])
    targets = torch.tensor(
        [STORY_SCHEMAS.index(row[1]) for row in rows], dtype=torch.long
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-3,
                                  weight_decay=0.01)
    loss_fn = torch.nn.CrossEntropyLoss()
    generator = torch.Generator().manual_seed(seed)
    for _ in range(epochs):
        order = torch.randperm(len(rows), generator=generator)
        model.train()
        for start in range(0, len(order), 16):
            index = order[start:start + 16]
            optimizer.zero_grad()
            logits = model(data[index].to(device), lengths[index])
            loss = loss_fn(logits, targets[index].to(device))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
    return model.eval()


#: Eight briefs, four held out by STORY IDENTITY (never by beat).  Each one is
#: authored so that ordering is not the only decision:
#:
#: * two desires, both legal, so the tree branches at the very first step;
#: * two DECLARED elements, both visibly nameable in the setup mention, so
#:   ``plant`` is a real choice.  Planting the decoy is ACCEPTED by the frame
#:   and then strands an obligation the resolution never discharges -- an
#:   accepted dead branch by construction, which is what the roadmap's
#:   pruning-evidence bullet needs on the story side;
#: * two outcomes, one of which binds the real element and one of which binds
#:   nothing, so ``resolve`` can succeed into a story that can never close;
#: * a denied trait, so ``introduce`` also has a REFUTED option.
BRIEFS = (
    StoryBrief(
        id="golden_chicken", split="train", agent="the golden chicken",
        desires=("to sing the sunrise awake", "to out-crow the rooster"),
        trait="golden", denied_trait="silver",
        element="fallen feather", element_surface="fallen feather",
        decoy_element="key", decoy_surface="key",
        plant_mention="A fallen feather lay beside a key that fit no lock.",
        obstacles=("the locked coop door", "a sudden frost"),
        outcomes=(
            "It used a fallen feather as a lever, stepped outside, and sang "
            "until the sun rose",
            "It waited quietly until morning came on its own",
        ),
    ),
    StoryBrief(
        id="tin_lantern", split="train", agent="the tin lantern",
        desires=("to light the last mile", "to be carried home"),
        trait="dented", denied_trait="polished",
        element="cracked lens", element_surface="cracked lens",
        decoy_element="map", decoy_surface="map",
        plant_mention="A cracked lens rattled beside a folded map.",
        obstacles=("the rising fog", "an empty oil well"),
        outcomes=(
            "The cracked lens split the beam in two and both halves reached "
            "the road",
            "The night simply ended and nothing was needed",
        ),
    ),
    StoryBrief(
        id="paper_boat", split="train", agent="the paper boat",
        desires=("to cross the millpond", "to carry one message"),
        trait="folded", denied_trait="sealed",
        element="ink stain", element_surface="ink stain",
        decoy_element="pebble", decoy_surface="pebble",
        plant_mention="An ink stain darkened one flank and a pebble weighed "
                      "the other.",
        obstacles=("the weir gate", "a rising wind"),
        outcomes=(
            "The ink stain hardened into ballast and the crossing held",
            "The pond went still and the crossing needed nothing",
        ),
    ),
    StoryBrief(
        id="clay_whistle", split="train", agent="the clay whistle",
        desires=("to call the flock back", "to be heard once"),
        trait="fired", denied_trait="glazed",
        element="hairline crack", element_surface="hairline crack",
        decoy_element="ribbon", decoy_surface="ribbon",
        plant_mention="A hairline crack ran along its throat under a faded "
                      "ribbon.",
        obstacles=("the shouting market", "a wet season"),
        outcomes=(
            "The hairline crack bent the note flat and the flock knew it",
            "The flock returned by itself before anything was played",
        ),
    ),
    StoryBrief(
        id="iron_kite", split="heldout", agent="the iron kite",
        desires=("to outclimb the tower", "to see the far field"),
        trait="riveted", denied_trait="feathered",
        element="loose rivet", element_surface="loose rivet",
        decoy_element="rope", decoy_surface="rope",
        plant_mention="A loose rivet ticked against the spar above a frayed "
                      "rope.",
        obstacles=("the dead calm", "a low wall of pines"),
        outcomes=(
            "The loose rivet shed just enough weight and the tower fell away "
            "below",
            "The wind rose on its own and carried everything upward",
        ),
    ),
    StoryBrief(
        id="salt_mirror", split="heldout", agent="the salt mirror",
        desires=("to show the harbour once", "to keep one true face"),
        trait="clouded", denied_trait="silvered",
        element="salt bloom", element_surface="salt bloom",
        decoy_element="frame", decoy_surface="frame",
        plant_mention="A salt bloom crusted one corner of the frame.",
        obstacles=("the shuttered window", "a long grey week"),
        outcomes=(
            "The salt bloom scattered the light into the harbour and the "
            "boats were counted",
            "The clouds parted and the harbour showed itself",
        ),
    ),
    StoryBrief(
        id="wax_thimble", split="heldout", agent="the wax thimble",
        desires=("to finish the winter coat", "to survive one stitch"),
        trait="soft", denied_trait="steel",
        element="thumb dent", element_surface="thumb dent",
        decoy_element="needle", decoy_surface="needle",
        plant_mention="A thumb dent held its shape beside the eye of a "
                      "needle.",
        obstacles=("the frozen thread", "a failing lamp"),
        outcomes=(
            "The thumb dent gripped where a smooth face would have slipped "
            "and the coat closed",
            "The coat was finished by someone else entirely",
        ),
    ),
    StoryBrief(
        id="glass_bell", split="heldout", agent="the glass bell",
        desires=("to ring the low tide", "to be struck truly once"),
        trait="thin", denied_trait="bronze",
        element="chipped rim", element_surface="chipped rim",
        decoy_element="clapper", decoy_surface="clapper",
        plant_mention="A chipped rim caught the lamplight above a still "
                      "clapper.",
        obstacles=("the muffled cloth", "an early storm"),
        outcomes=(
            "The chipped rim shivered the note into a warning and the boats "
            "turned",
            "The tide announced itself and no bell was needed",
        ),
    ),
)


def curve(runs: list[StoryRun], arms: list[str], splits: list[str]) -> dict:
    table: dict[str, object] = {}
    for split in ["ALL", *splits]:
        rows = [r for r in runs if split == "ALL" or r.split == split]
        per_arm: dict[str, object] = {}
        for arm in arms:
            selected = [r for r in rows if r.arm == arm]
            if not selected:
                continue
            per_arm[arm] = {
                "n": len(selected),
                "budget_curve": [
                    {
                        "nodes": nodes,
                        "proposals": proposals,
                        "solved": sum(
                            r.solved and r.nodes <= nodes
                            and r.proposals <= proposals
                            for r in selected
                        ),
                    }
                    for nodes, proposals in zip(NODE_BUDGETS, PROPOSAL_BUDGETS)
                ],
                "time_curve": [
                    {
                        "seconds": seconds,
                        "solved": sum(
                            r.solved and r.seconds <= seconds for r in selected
                        ),
                    }
                    for seconds in TIME_BUDGETS
                ],
                "mean_proposals_when_solved": round(
                    sum(r.proposals for r in selected if r.solved)
                    / max(sum(r.solved for r in selected), 1), 2
                ),
            }
        table[split] = per_arm
    return table


def cross_task_dead(runs: list[StoryRun]) -> dict[str, object]:
    by_arm: dict[str, list[StoryRun]] = {}
    for run in runs:
        by_arm.setdefault(run.arm, []).append(run)
    summary: dict[str, object] = {}
    for arm, arm_runs in by_arm.items():
        hits = total = 0
        for run in arm_runs:
            others = {
                signature
                for other in arm_runs
                if other.brief != run.brief
                for signature in other.dead_branches
            }
            hits += sum(sig in others for sig in run.proposal_signatures)
            total += len(run.proposal_signatures)
        summary[arm] = {
            "own_ledger_share": round(hits / total, 4) if total else 0.0,
            "own_ledger_hits": hits,
            "proposals": total,
            "dead_branches": sum(len(r.dead_branches) for r in arm_runs),
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--epochs", type=int, default=240)
    parser.add_argument("--out", type=Path,
                        default=ROOT / "experiments" / "results" / "story_curve.json")
    parser.add_argument("--checkpoint-dir", type=Path,
                        default=ROOT / "experiments" / "results")
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    train = [brief for brief in BRIEFS if brief.split == "train"]
    heldout = [brief for brief in BRIEFS if brief.split == "heldout"]
    rows: list[tuple[str, str]] = []
    for brief in train:
        rows.extend(oracle_walk(brief))
    counts = Counter(schema for _, schema in rows)

    rankers: list[object] = [
        ArbitraryStoryRanker(),
        FrequencyStoryRanker(tuple(sorted(counts.items()))),
        SyntaxStoryRanker(),
    ]
    checkpoints = {}
    started = time.perf_counter()
    for seed in args.seeds:
        model = train_story_ranker(tuple(rows), seed, args.epochs, device)
        path = args.checkpoint_dir / f"story_policy_s{seed}.pt"
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "state_dict": model.state_dict(),
                "schemas": STORY_SCHEMAS,
                "seed": seed,
                "architecture": "byte-gru-tactic-ranker",
                "domain": "story",
            },
            path,
        )
        checkpoints[f"learned_s{seed}"] = {
            "file": path.name, "bytes": path.stat().st_size
        }
        rankers.append(LearnedStoryRanker(model, device, f"learned_s{seed}"))

    runs: list[StoryRun] = []
    for brief in BRIEFS:
        for ranker in rankers:
            run = run_brief(brief, ranker, NODE_BUDGETS[-1], PROPOSAL_BUDGETS[-1])
            runs.append(run)
            print(
                f"{run.brief:<16} {run.split:<8} {run.arm:<12} "
                f"{'SOLVED' if run.solved else run.stop:<9} "
                f"nodes={run.nodes:<3} proposals={run.proposals:<4} "
                f"{run.seconds:.3f}s",
                flush=True,
            )
    elapsed = time.perf_counter() - started

    # P-SC5's second clause, checked rather than asserted.
    from tactic_grammar import SCHEMAS as TACTIC_SCHEMAS  # noqa: PLC0415

    payload = {
        "experiment": "story-policy-curve-v0.7",
        "roadmap_item": "ROADMAP-v0.7 item 1, story-family arm",
        "controller": "scripts/controller.SearchController (shared, unmodified)",
        "verifier": "scripts/oracle_controller_demo.StoryFrameVerifier",
        "schemas": list(STORY_SCHEMAS),
        "vocabulary_disjoint_from_tactics": sorted(
            set(STORY_SCHEMAS) & set(TACTIC_SCHEMAS)
        ) == [],
        "briefs": {
            "train": [brief.id for brief in train],
            "heldout": [brief.id for brief in heldout],
        },
        "training_rows": len(rows),
        "frequency_counts": dict(counts),
        "frequency_order": list(
            FrequencyStoryRanker(tuple(sorted(counts.items()))).order("")
        ),
        "frequency_collapses_to_arbitrary": (
            FrequencyStoryRanker(tuple(sorted(counts.items()))).order("")
            == ARBITRARY_STORY_ORDER
        ),
        "checkpoints": checkpoints,
        "budgets": {
            "nodes": list(NODE_BUDGETS),
            "proposals": list(PROPOSAL_BUDGETS),
            "seconds": list(TIME_BUDGETS),
            "middle_index": MIDDLE,
        },
        "curve": curve(runs, [r.name for r in rankers], ["train", "heldout"]),
        "cross_task_dead_branches": cross_task_dead(runs),
        "runs": [run.as_json() for run in runs],
        "device": device,
        "gpu_max_memory_allocated_bytes": (
            int(torch.cuda.max_memory_allocated())
            if torch.cuda.is_available() else 0
        ),
        "gpu_max_memory_reserved_bytes": (
            int(torch.cuda.max_memory_reserved())
            if torch.cuda.is_available() else 0
        ),
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
    print(f"wrote {args.out} ({len(runs)} runs, {elapsed:.1f}s)")


if __name__ == "__main__":
    main()
