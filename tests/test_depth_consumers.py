from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))

from train_analogy import (AnalogyPointer, AnalogyDataset, Vocab, collate,
                           teacher_forced_diagnostics)  # noqa: E402
from diagnose_analogy import restore_model  # noqa: E402


class DepthConsumerTests(unittest.TestCase):
    def test_consumer_ladder_preserves_shapes(self) -> None:
        source = torch.randint(1, 8, (2, 7))
        coords = torch.zeros(2, 7, 1 + 10, dtype=torch.long)
        coords[:, :, 1:4] = torch.randint(1, 3, (2, 7, 3))
        mask = torch.ones(2, 7, dtype=torch.bool)
        target = torch.tensor([[1, 3, 4], [1, 3, 5]])
        target_paths = torch.zeros(2, 3, 10, dtype=torch.long)
        target_paths[:, :, :3] = torch.randint(1, 3, (2, 3, 3))
        for consumer in ("address", "query", "memory", "both", "mlp"):
            model = AnalogyPointer(8, d_model=16, n_layers=1, n_dec=1,
                                   n_heads=4, max_tgt=8,
                                   level_code="recurrent",
                                   consumer=consumer)
            memory = model.encode(source, coords, mask)
            prepared = model.prepare_memory(memory, coords[..., 1:])
            logits = model.decode(prepared, mask, target, target_paths)
            self.assertEqual(logits.shape, (2, 3, 3 + 7))

    def test_inactive_recurrent_path_preserves_base(self) -> None:
        model = AnalogyPointer(8, d_model=16, n_layers=1, n_dec=1,
                               n_heads=4, level_code="recurrent",
                               consumer="both")
        base = torch.randn(2, 3, 16)
        paths = torch.zeros(2, 3, 10, dtype=torch.long)
        actual = model.recurrent_consume(
            base, paths, model.memory_path_cell
        )
        self.assertTrue(torch.equal(actual, base))

    def test_mlp_control_matches_both_parameter_count_within_two(self) -> None:
        both = AnalogyPointer(8, level_code="recurrent", consumer="both")
        mlp = AnalogyPointer(8, level_code="recurrent", consumer="mlp")
        both_count = sum(parameter.numel() for parameter in both.parameters())
        mlp_count = sum(parameter.numel() for parameter in mlp.parameters())
        self.assertEqual(mlp_count - both_count, 2)

    def test_new_consumers_reject_depth_indexed_addressing(self) -> None:
        for level_code in ("table", "sinusoidal"):
            with self.assertRaises(ValueError):
                AnalogyPointer(8, level_code=level_code, consumer="query")

    def test_mlp_adds_no_iterative_path_calls_beyond_address_control(self) -> None:
        source = torch.randint(1, 8, (2, 7))
        coords = torch.zeros(2, 7, 1 + 10, dtype=torch.long)
        coords[:, :, 1:4] = torch.randint(1, 3, (2, 7, 3))
        mask = torch.ones(2, 7, dtype=torch.bool)
        target = torch.tensor([[1, 3, 4], [1, 3, 5]])
        target_paths = torch.zeros(2, 3, 10, dtype=torch.long)
        target_paths[:, :, :3] = torch.randint(1, 3, (2, 3, 3))
        calls = {}
        for consumer in ("address", "mlp"):
            model = AnalogyPointer(8, d_model=16, n_layers=1, n_dec=1,
                                   n_heads=4, max_tgt=8,
                                   level_code="recurrent",
                                   consumer=consumer)
            count = [0]
            hook = model.path_cell.register_forward_hook(
                lambda *_args: count.__setitem__(0, count[0] + 1))
            memory = model.encode(source, coords, mask)
            prepared = model.prepare_memory(memory, coords[..., 1:])
            model.decode(prepared, mask, target, target_paths)
            hook.remove()
            calls[consumer] = count[0]
        self.assertEqual(calls["mlp"], calls["address"])
        self.assertGreater(calls["address"], 0)

    def test_mlp_one_shot_is_order_aware_and_zero_path_is_identity(self) -> None:
        model = AnalogyPointer(8, d_model=16, n_layers=1, n_dec=1,
                               n_heads=4, level_code="recurrent", consumer="mlp")
        ordered = torch.zeros(1, 1, 10, dtype=torch.long)
        reversed_path = torch.zeros(1, 1, 10, dtype=torch.long)
        ordered[0, 0, :2] = torch.tensor([1, 2])
        reversed_path[0, 0, :2] = torch.tensor([2, 1])
        self.assertFalse(torch.equal(
            model.one_shot_path_summary(ordered),
            model.one_shot_path_summary(reversed_path),
        ))
        base = torch.randn(1, 1, 16)
        zero = torch.zeros(1, 1, 10, dtype=torch.long)
        self.assertTrue(torch.equal(model.prepare_memory(base, zero), base))

    def test_teacher_forced_diagnostics_name_steps_and_deciles(self) -> None:
        row = {
            "tokens_struct": ["f", "(", "x", ")", "<sep>", "f", "(",
                              "y", ")", "<sep>", "z"],
            "target_positions": [5, 6, 10, 8],
            "target_tokens": ["f", "(", "z", ")"],
            "depth": 2,
        }
        vocab = Vocab(set(row["tokens_struct"]))
        dataset = AnalogyDataset([row], vocab, 32, 16)
        loader = torch.utils.data.DataLoader(dataset, batch_size=1,
                                             collate_fn=collate)
        model = AnalogyPointer(len(vocab), d_model=16, n_layers=1, n_dec=1,
                               n_heads=4, max_tgt=16,
                               level_code="recurrent", consumer="address")
        result = teacher_forced_diagnostics(model, loader, "cpu", vocab.itos)
        self.assertEqual(result["examples"], 1)
        self.assertEqual(set(result["by_kind"]), {"B-struct", "C-leaf", "EOS"})
        self.assertEqual(set(result["by_decile"]), {str(i) for i in range(10)})
        self.assertEqual(sum(item["total"] for item in result["by_kind"].values()), 5)

    def test_every_consumer_checkpoint_round_trips(self) -> None:
        for consumer in ("address", "query", "memory", "both", "mlp"):
            original = AnalogyPointer(8, d_model=16, max_tgt=8,
                                      level_code="recurrent", consumer=consumer)
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / f"{consumer}.pt"
                torch.save({"state_dict": original.state_dict(), "seed": 2,
                            "config": {"consumer": consumer}}, path)
                checkpoint = torch.load(path, weights_only=False)
            restored = AnalogyPointer(8, d_model=16, max_tgt=8,
                                      level_code="recurrent", consumer=consumer)
            restored.load_state_dict(checkpoint["state_dict"])
            self.assertEqual(checkpoint["config"]["consumer"], consumer)

    def test_diagnostic_loader_restores_every_consumer(self) -> None:
        for consumer in ("address", "query", "memory", "both", "mlp"):
            original = AnalogyPointer(8, d_model=16, max_tgt=8,
                                      level_code="recurrent", consumer=consumer)
            checkpoint = {
                "state_dict": original.state_dict(),
                "vocab": ["<pad>", "<unk>", "<cls>", "<sep>",
                          "a", "b", "c", "d"],
                "config": {"d_model": 16, "max_tgt": 8,
                           "level_code": "recurrent", "consumer": consumer},
            }
            restored, _ = restore_model(checkpoint, "cpu")
            self.assertEqual(restored.consumer, consumer)


if __name__ == "__main__":
    unittest.main()
