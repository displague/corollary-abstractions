#!/usr/bin/env python3
"""Train and adjudicate the first tiny learned Lean tactic ranker.

The model owns one graded choice: ordering tactic *schemas* from rendered proof
state.  It does not apply tactics, check proofs, synthesize binder names, or
search.  ``SearchController`` and Lean retain those exact operations.

Registered predictions (P-TP, written before the first training run):

P-TP1. Across three cold seeds, theorem-held-out top-1 schema accuracy beats
    both the train-frequency baseline and a label-shuffled control on mean.
    The split holds out four whole theorem identities, never individual rows.
P-TP2. All three all-data checkpoints close ``heldout.and_commute`` through
    live PyPantograph at the same 64-state / 512-proposal budget as the blind
    palette, and mean proposals are lower than the blind result of 86.
P-TP3. The projection schema is load-bearing: removing both concrete
    projections leaves every learned arm unsolved under the same budget.
P-TP4. Each ranker remains below 64K parameters and 1 MiB serialized.  This is
    a ranking result, not a general prover or a five-action shared policy.

Corrective prediction P-TP5 (registered after review identified the missing
stronger control, before running it): a global tactic-schema frequency order,
computed from the same 44 training rows but blind to the current state, also
beats the arbitrary palette but uses more than the learned mean of 65.0
proposals.  If it ties or wins, the live learned-ordering claim is retracted;
held-out classification remains a separate result.

The fixed evaluation split is declared here before metrics exist:
``double_negation``, ``identity_and_true``, ``distrib_and_or``, and
``modus_ponens`` are held out by theorem.  Complex multi-tactic blocks and
schemas outside the bounded live palette are excluded rather than mislabeled.

Adjudication: P-TP1 through P-TP4 FIRED against their registered controls, but
P-TP5 MISSED and retracts the strongest live interpretation. The three
theorem-held-out top-1
runs are 0.8125 each, versus 0.4375 for the frequency baseline and
0.25/0.375/0.375 for shuffled labels.  All three learned rankings close the
live theorem in 71/63/61 proposals (mean 65.0, blind 86) and 8/7/7 expanded
states; every projection ablation exhausts at 10 states / 80 proposals.  Each
27,688-parameter checkpoint serializes to 114,433 bytes. But the stronger
state-blind frequency order solves in 64 proposals: one better than the learned
mean. The live learned-gain claim is therefore REFUTED; what remains is stable
held-out schema classification on one tiny bounded vocabulary, not breadth.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import torch
import torch.nn as nn


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "prover"))

from live_search import (  # noqa: E402
    ABLATION_TACTICS,
    BLIND_TACTICS,
    LiveLeanState,
    LiveLeanVerifier,
    PantographBackend,
    blind_search,
)


SCHEMAS = (
    "clear",
    "intro",
    "constructor",
    "assumption",
    "projection",
    "left",
    "right",
    "trivial",
)
SCHEMA_INDEX = {name: index for index, name in enumerate(SCHEMAS)}
HELD_OUT_THEOREMS = {
    "BooleanLaws.double_negation",
    "BooleanLaws.identity_and_true",
    "BooleanLaws.distrib_and_or",
    "BooleanLaws.modus_ponens",
}


def tactic_schema(tactic: str) -> str | None:
    """Map one extracted atomic tactic to the bounded policy vocabulary."""
    lines = [line.strip() for line in tactic.splitlines() if line.strip()]
    if len(lines) != 1:
        return None
    line = lines[0]
    if line.startswith("· "):
        line = line[2:].strip()
    if line.startswith("intro ") or line == "intro":
        return "intro"
    if line == "constructor":
        return "constructor"
    if line == "assumption":
        return "assumption"
    if line.startswith("exact ") and any(
        marker in line for marker in (".left", ".right", ".1", ".2")
    ):
        return "projection"
    if line in {"left", "right", "trivial"}:
        return line
    if line.startswith("clear "):
        return "clear"
    return None


def action_schema(tactic: str) -> str:
    if tactic.startswith("clear "):
        return "clear"
    if tactic.startswith("intro"):
        return "intro"
    if tactic == "constructor":
        return "constructor"
    if tactic == "assumption":
        return "assumption"
    if tactic.startswith("exact ") and any(
        marker in tactic for marker in (".left", ".right", ".1", ".2")
    ):
        return "projection"
    if tactic in {"left", "right", "trivial"}:
        return tactic
    raise ValueError(f"unregistered live tactic schema: {tactic}")


@dataclass(frozen=True)
class Example:
    theorem: str
    state: str
    label: int


def load_examples(path: Path) -> list[Example]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    examples = []
    for row in rows:
        schema = tactic_schema(row["tactic"])
        if schema is not None:
            examples.append(
                Example(row["theorem"], row["stateBefore"],
                        SCHEMA_INDEX[schema])
            )
    return examples


def encode(states: list[str], max_bytes: int = 512) -> tuple[torch.Tensor, torch.Tensor]:
    payloads = [state.encode("utf-8")[-max_bytes:] for state in states]
    lengths = torch.tensor([max(len(value), 1) for value in payloads])
    data = torch.zeros((len(payloads), int(lengths.max())), dtype=torch.long)
    for row, value in enumerate(payloads):
        if value:
            data[row, :len(value)] = torch.tensor(
                [byte + 1 for byte in value], dtype=torch.long
            )
    return data, lengths


class TacticRanker(nn.Module):
    """Byte-GRU schema ranker.

    ``classes`` exists so a second DOMAIN can reuse this architecture with its
    own weights and its own vocabulary size (ROADMAP-v0.7 item 1 permits
    domain weights and forbids a second controller).  It defaults to the v0.6
    tactic vocabulary, so every released checkpoint loads unchanged.
    """

    def __init__(self, embed_dim: int = 32, hidden_dim: int = 64,
                 classes: int = len(SCHEMAS)):
        super().__init__()
        self.embed = nn.Embedding(257, embed_dim, padding_idx=0)
        self.encoder = nn.GRU(embed_dim, hidden_dim, batch_first=True)
        self.head = nn.Sequential(
            nn.LayerNorm(hidden_dim),
            nn.Linear(hidden_dim, classes),
        )

    def forward(self, data: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        embedded = self.embed(data)
        packed = nn.utils.rnn.pack_padded_sequence(
            embedded, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        _, hidden = self.encoder(packed)
        return self.head(hidden[-1])


def accuracy(model: TacticRanker, examples: list[Example], device: str) -> float:
    if not examples:
        return 0.0
    model.eval()
    data, lengths = encode([example.state for example in examples])
    labels = torch.tensor([example.label for example in examples])
    with torch.no_grad():
        predicted = model(data.to(device), lengths).argmax(dim=-1).cpu()
    return float((predicted == labels).float().mean().item())


def train_model(
    examples: list[Example], seed: int, epochs: int, device: str,
    shuffled_labels: bool = False,
) -> TacticRanker:
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True)
    random.seed(seed)
    model = TacticRanker().to(device)
    data, lengths = encode([example.state for example in examples])
    labels = [example.label for example in examples]
    if shuffled_labels:
        random.shuffle(labels)
    targets = torch.tensor(labels, dtype=torch.long)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-3,
                                  weight_decay=0.01)
    loss_fn = nn.CrossEntropyLoss()
    generator = torch.Generator().manual_seed(seed)
    for _ in range(epochs):
        order = torch.randperm(len(examples), generator=generator)
        model.train()
        for start in range(0, len(order), 32):
            indices = order[start:start + 32]
            optimizer.zero_grad()
            logits = model(data[indices].to(device), lengths[indices])
            loss = loss_fn(logits, targets[indices].to(device))
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
    return model


class LearnedTacticPolicy:
    """Rank the existing concrete palette by a learned schema score."""

    def __init__(self, model: TacticRanker, device: str,
                 tactics: tuple[str, ...] = BLIND_TACTICS):
        self.model = model.eval()
        self.device = device
        self.tactics = tactics

    def propose_all(self, state: LiveLeanState, trace) -> Iterable:
        del trace
        data, lengths = encode([state.goal_text])
        with torch.no_grad():
            scores = self.model(
                data.to(self.device), lengths
            )[0].detach().cpu()
        ranked = sorted(
            enumerate(self.tactics),
            key=lambda item: (-float(scores[SCHEMA_INDEX[action_schema(item[1])]]),
                              item[0]),
        )
        from controller import Action, ActionKind
        return tuple(
            Action.build(ActionKind.GEN, "lean_tactic", {"tactic": tactic})
            for _, tactic in ranked
        )


def frequency_baseline(train: list[Example], test: list[Example]) -> float:
    counts = [0] * len(SCHEMAS)
    for example in train:
        counts[example.label] += 1
    predicted = max(range(len(counts)), key=counts.__getitem__)
    return sum(example.label == predicted for example in test) / len(test)


def frequency_tactics(train: list[Example]) -> tuple[str, ...]:
    counts = [0] * len(SCHEMAS)
    for example in train:
        counts[example.label] += 1
    return tuple(
        tactic for index, tactic in sorted(
            enumerate(BLIND_TACTICS),
            key=lambda item: (
                -counts[SCHEMA_INDEX[action_schema(item[1])]], item[0]
            ),
        )
    )


def save_checkpoint(model: TacticRanker, path: Path, seed: int) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"state_dict": model.state_dict(), "schemas": SCHEMAS,
         "seed": seed, "architecture": "byte-gru-tactic-ranker"},
        path,
    )
    return path.stat().st_size


def load_checkpoint(path: Path, device: str) -> TacticRanker:
    payload = torch.load(path, map_location=device, weights_only=True)
    if tuple(payload.get("schemas", ())) != SCHEMAS:
        raise ValueError("checkpoint tactic schema vocabulary does not match")
    if payload.get("architecture") != "byte-gru-tactic-ranker":
        raise ValueError("checkpoint architecture is not a tactic ranker")
    model = TacticRanker().to(device)
    model.load_state_dict(payload["state_dict"], strict=True)
    return model.eval()


def run_live(model: TacticRanker, device: str, tactics: tuple[str, ...],
             max_nodes: int, max_proposals: int):
    backend = PantographBackend(None, ("Init",))
    try:
        verifier = LiveLeanVerifier(backend)
        initial = verifier.start("heldout.and_commute",
                                 "forall (P Q : Prop) (h : P ∧ Q), Q ∧ P")
        from controller import SearchController
        return SearchController[LiveLeanState](max_nodes, max_proposals).run(
            initial, LearnedTacticPolicy(model, device, tactics), verifier,
            lambda state: state.goal_text == "no goals",
        )
    finally:
        backend.close()


def run_static_live(tactics: tuple[str, ...], max_nodes: int,
                    max_proposals: int):
    backend = PantographBackend(None, ("Init",))
    try:
        return blind_search(
            LiveLeanVerifier(backend), tactics,
            max_nodes=max_nodes, max_proposals=max_proposals,
        )
    finally:
        backend.close()


def default_output(live: bool) -> Path:
    name = "tactic_policy.json" if live else "tactic_policy_nonlive.json"
    return ROOT / "experiments" / "results" / name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--triples", type=Path,
                        default=ROOT / "prover" / "sample_triples.json")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--checkpoint-dir", type=Path,
                        default=ROOT / "experiments" / "results")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--demo-checkpoint", type=Path, default=None,
                        help="load one release asset and run live search only")
    parser.add_argument("--max-nodes", type=int, default=64)
    parser.add_argument("--max-proposals", type=int, default=512)
    args = parser.parse_args()
    if args.out is None:
        args.out = default_output(args.live)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if args.demo_checkpoint is not None:
        if not args.live:
            parser.error("--demo-checkpoint requires --live")
        model = load_checkpoint(args.demo_checkpoint, device)
        full = run_live(model, device, BLIND_TACTICS,
                        args.max_nodes, args.max_proposals)
        ablated = run_live(model, device, ABLATION_TACTICS,
                           args.max_nodes, args.max_proposals)
        print(
            f"learned: {full.stop_reason.value}; nodes={full.nodes_expanded} "
            f"states={full.states_seen} proposals={full.proposals}"
        )
        for entry in full.solution_trace:
            print(f"  {entry.action.argument('tactic')} -> "
                  f"{entry.verification.verdict.value}")
        print(
            f"projection ablation: {ablated.stop_reason.value}; "
            f"nodes={ablated.nodes_expanded} proposals={ablated.proposals}"
        )
        raise SystemExit(0 if full.solved and not ablated.solved else 1)

    examples = load_examples(args.triples)
    train = [item for item in examples if item.theorem not in HELD_OUT_THEOREMS]
    test = [item for item in examples if item.theorem in HELD_OUT_THEOREMS]
    frequency = frequency_baseline(train, test)
    blind = None
    frequency_live = None
    if args.live:
        blind = run_static_live(
            BLIND_TACTICS, args.max_nodes, args.max_proposals
        )
        frequency_live = run_static_live(
            frequency_tactics(train), args.max_nodes, args.max_proposals
        )
    start = time.time()
    runs = []
    for seed in args.seeds:
        heldout_model = train_model(train, seed, args.epochs, device)
        shuffled_model = train_model(
            train, seed, args.epochs, device, shuffled_labels=True
        )
        all_model = train_model(examples, seed, args.epochs, device)
        checkpoint = args.checkpoint_dir / f"tactic_policy_s{seed}.pt"
        size = save_checkpoint(all_model, checkpoint, seed)
        run = {
            "seed": seed,
            "checkpoint": checkpoint.name,
            "heldout_top1": accuracy(heldout_model, test, device),
            "shuffled_top1": accuracy(shuffled_model, test, device),
            "checkpoint_bytes": size,
        }
        if args.live:
            full = run_live(all_model, device, BLIND_TACTICS,
                            args.max_nodes, args.max_proposals)
            ablated = run_live(all_model, device, ABLATION_TACTICS,
                               args.max_nodes, args.max_proposals)
            run["live"] = {
                "solved": full.solved,
                "nodes": full.nodes_expanded,
                "states": full.states_seen,
                "proposals": full.proposals,
                "accepted": full.accepted_proposals,
                "rejected": full.rejected_proposals,
                "solution": [entry.action.argument("tactic")
                             for entry in full.solution_trace],
                "ablation_solved": ablated.solved,
                "ablation_stop": ablated.stop_reason.value,
                "ablation_nodes": ablated.nodes_expanded,
                "ablation_proposals": ablated.proposals,
            }
        runs.append(run)
        print(json.dumps(run, ensure_ascii=False))

    params = sum(parameter.numel() for parameter in TacticRanker().parameters())
    result = {
        "experiment": "tactic-policy-v0.6",
        "device": device,
        "examples": len(examples),
        "train_examples": len(train),
        "heldout_examples": len(test),
        "heldout_theorems": sorted(HELD_OUT_THEOREMS),
        "schemas": SCHEMAS,
        "parameters": params,
        "epochs": args.epochs,
        "frequency_top1": frequency,
        "runs": runs,
        "seconds": round(time.time() - start, 2),
    }
    if blind is not None:
        result["blind_live"] = {
            "solved": blind.solved,
            "stop": blind.stop_reason.value,
            "nodes": blind.nodes_expanded,
            "states": blind.states_seen,
            "proposals": blind.proposals,
            "accepted": blind.accepted_proposals,
            "rejected": blind.rejected_proposals,
        }
        assert frequency_live is not None
        result["frequency_live"] = {
            "solved": frequency_live.solved,
            "stop": frequency_live.stop_reason.value,
            "nodes": frequency_live.nodes_expanded,
            "states": frequency_live.states_seen,
            "proposals": frequency_live.proposals,
            "accepted": frequency_live.accepted_proposals,
            "rejected": frequency_live.rejected_proposals,
            "tactics": frequency_tactics(train),
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out} ({params:,} parameters)")


if __name__ == "__main__":
    main()
