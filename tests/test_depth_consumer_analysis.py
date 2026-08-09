from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import torch
import hashlib


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))

from analyze_depth_consumers import (ARMS, SEEDS, adjudicate,  # noqa: E402
                                     material_gain)
from depth_consumer_protocol import P_DC5, P_DC6, P_DC7  # noqa: E402


class DepthConsumerAnalysisTests(unittest.TestCase):
    def write_matrix(self, root: Path) -> None:
        implementation = ROOT / "experiments" / "analyze_depth_consumers.py"
        implementation_digest = hashlib.sha256(
            implementation.read_bytes()).hexdigest()
        scores = {
            "address": (0.10, 0.11, 0.12),
            "query": (0.26, 0.27, 0.28),
            "memory": (0.27, 0.28, 0.29),
            "both": (0.43, 0.44, 0.45),
            "mlp": (0.12, 0.13, 0.14),
        }
        for arm in ARMS:
            for seed, score in zip(SEEDS, scores[arm]):
                diagnostics = {
                    "mode": "teacher-forced", "step_perfect_rate": score,
                    "by_kind": {
                        kind: {"accuracy": score}
                        for kind in ("B-struct", "C-leaf", "EOS")
                    },
                    "by_decile": {
                        str(index): {"accuracy": score} for index in range(10)
                    },
                    "by_absolute_step": {"0": {"accuracy": score}},
                }
                row = {"consumer": arm, "seed": seed, "params": 100,
                       "level_code": "recurrent",
                       "batch_size": 192, "microbatch_size": 64,
                       "eval_batch_size": 32, "memory_fraction": 0.70,
                       "test_exact": 1.0, "ood_exact": score,
                       "test_diagnostics": diagnostics,
                       "ood_diagnostics": diagnostics,
                       "cuda_memory": {
                           "pre_model_device_footprint_bytes": 500,
                           "train_validation": {
                               "peak_allocated_bytes": 1000,
                               "peak_reserved_bytes": 2000,
                               "peak_device_footprint_bytes": 3000,
                           },
                           "final_evaluation": {
                               "peak_allocated_bytes": 1100,
                               "peak_reserved_bytes": 2100,
                               "peak_device_footprint_bytes": 3100,
                           },
                       },
                       "inclusion": {
                           split: {"generated": 10, "kept": 8,
                                   "dropped_max_len": 1,
                                   "dropped_max_tgt": 1,
                                   "by_depth": {"4": {
                                       "generated": 10, "kept": 8,
                                       "dropped_max_len": 1,
                                       "dropped_max_tgt": 1}}}
                           for split in ("train", "val", "test", "ood")
                       },
                       "run_provenance": {
                           "consumer": arm, "seed": seed,
                           "task_prefix": "analogy",
                           "data_sha256": {"train": "a", "val": "b",
                                           "test": "c", "ood": "d"},
                           "epochs": 10, "level_code": "recurrent",
                           "max_tgt": 96,
                           "max_len": 512,
                           "batch_size": 192,
                           "microbatch_size": 64,
                           "eval_batch_size": 32,
                           "memory_fraction": 0.70,
                           "runtime_environment": {
                               "cuda_available": True,
                               "driver_version": "test-driver",
                               "device_name": "test-gpu",
                               "device_total_bytes": 10000,
                           },
                           "implementation_sha256": {
                               "experiments/analyze_depth_consumers.py":
                               implementation_digest},
                       }}
                torch.save({"seed": seed,
                            "config": {"consumer": arm,
                                       "level_code": "recurrent",
                                       "batch_size": 192,
                                       "microbatch_size": 64,
                                       "eval_batch_size": 32,
                                       "memory_fraction": 0.70}},
                           root / f"depth_{arm}_s{seed}.pt")
                raw = (root / f"depth_{arm}_s{seed}.pt").read_bytes()
                row["checkpoint_sha256"] = hashlib.sha256(raw).hexdigest()
                (root / f"depth_{arm}_s{seed}.json").write_text(
                    json.dumps(row), encoding="utf-8")

    def test_complete_matrix_adjudicates_registered_predictions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            result = adjudicate(root)
        self.assertTrue(all(
            result["adjudication"][key]["status"] == "FIRED"
            for key in ("P-DC1", "P-DC2", "P-DC3")))
        self.assertEqual(result["adjudication"]["P-DC4"]["status"],
                         "SATISFIED")
        self.assertEqual(result["adjudication"]["P-DC1"][
            "both_seedwise_wins"], 3)
        self.assertEqual(len(result["checkpoints"]), 15)
        self.assertTrue(all(
            item["prediction"]
            for item in result["adjudication"].values()))

    def test_machine_predictions_quote_registered_roadmap_wording(self) -> None:
        roadmap = (ROOT / "docs" / "ROADMAP-v0.6.md").read_text(
            encoding="utf-8")
        normalized_roadmap = " ".join(roadmap.split())
        for prediction in (P_DC5, P_DC6, P_DC7):
            self.assertIn(" ".join(prediction.split()), normalized_roadmap)

    def test_pdc1_misses_when_in_distribution_collapses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            for seed in SEEDS:
                path = root / f"depth_both_s{seed}.json"
                row = json.loads(path.read_text(encoding="utf-8"))
                row["test_exact"] = 0.0
                path.write_text(json.dumps(row), encoding="utf-8")
            result = adjudicate(root)
        self.assertEqual(result["adjudication"]["P-DC1"]["status"], "MISSED")

    def test_pdc3_blocks_when_control_is_not_parameter_matched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            for seed in SEEDS:
                path = root / f"depth_mlp_s{seed}.json"
                row = json.loads(path.read_text(encoding="utf-8"))
                row["params"] = 200
                path.write_text(json.dumps(row), encoding="utf-8")
            result = adjudicate(root)
        self.assertEqual(result["adjudication"]["P-DC3"]["status"], "BLOCKED")
        self.assertFalse(result["parameter_match"]["within_two_parameters"])

    def test_materiality_boundary_prevents_epsilon_firing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            for arm in ("query", "memory", "both"):
                for seed in SEEDS:
                    path = root / f"depth_{arm}_s{seed}.json"
                    row = json.loads(path.read_text(encoding="utf-8"))
                    row["ood_exact"] = 0.159
                    path.write_text(json.dumps(row), encoding="utf-8")
            result = adjudicate(root)
        self.assertEqual(result["adjudication"]["P-DC1"]["status"], "MISSED")
        self.assertEqual(result["adjudication"]["P-DC2"]["status"], "MISSED")

    def test_materiality_boundary_is_float_stable(self) -> None:
        self.assertTrue(material_gain(0.35, 0.20))
        self.assertTrue(material_gain(0.40000000000000002, 0.25))
        self.assertFalse(material_gain(0.3499, 0.20))

    def test_missing_inclusion_accounting_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            path = root / "depth_both_s0.json"
            row = json.loads(path.read_text(encoding="utf-8"))
            del row["inclusion"]
            path.write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing inclusion"):
                adjudicate(root)

    def test_empty_by_depth_accounting_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            path = root / "depth_both_s0.json"
            row = json.loads(path.read_text(encoding="utf-8"))
            row["inclusion"]["ood"]["by_depth"] = {}
            path.write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "empty ood by-depth"):
                adjudicate(root)

    def test_result_level_code_must_match_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            path = root / "depth_query_s1.json"
            row = json.loads(path.read_text(encoding="utf-8"))
            row["level_code"] = "table"
            path.write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "mislabelled provenance"):
                adjudicate(root)

    def test_manifest_refuses_cross_seed_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            torch.save({"seed": 2, "config": {"consumer": "both"}},
                       root / "depth_both_s1.pt")
            with self.assertRaisesRegex(ValueError, "mislabelled checkpoint"):
                adjudicate(root)

    def test_matrix_refuses_mixed_dataset_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            path = root / "depth_query_s2.json"
            row = json.loads(path.read_text(encoding="utf-8"))
            row["run_provenance"]["data_sha256"]["train"] = "changed"
            path.write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "mixed experiment provenance"):
                adjudicate(root)

    def test_matrix_refuses_unsafe_evaluation_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            path = root / "depth_both_s0.json"
            row = json.loads(path.read_text(encoding="utf-8"))
            row["run_provenance"]["eval_batch_size"] = 192
            path.write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unsafe batch protocol"):
                adjudicate(root)

    def test_matrix_refuses_result_batch_binding_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            path = root / "depth_both_s0.json"
            row = json.loads(path.read_text(encoding="utf-8"))
            row["eval_batch_size"] = 64
            path.write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "result batch binding"):
                adjudicate(root)

    def test_matrix_refuses_incomplete_gpu_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            path = root / "depth_both_s0.json"
            row = json.loads(path.read_text(encoding="utf-8"))
            del row["run_provenance"]["runtime_environment"]["driver_version"]
            path.write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "incomplete GPU environment"):
                adjudicate(root)

    def test_matrix_refuses_missing_cuda_memory_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            path = root / "depth_both_s0.json"
            row = json.loads(path.read_text(encoding="utf-8"))
            del row["cuda_memory"]
            path.write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing CUDA memory"):
                adjudicate(root)

    def test_pdc6_misses_when_evaluation_adds_over_half_gib(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            path = root / "depth_both_s0.json"
            row = json.loads(path.read_text(encoding="utf-8"))
            row["cuda_memory"]["final_evaluation"][
                "peak_device_footprint_bytes"] = 3000 + 512 * 1024 ** 2 + 1
            path.write_text(json.dumps(row), encoding="utf-8")
            result = adjudicate(root)
        self.assertEqual(result["adjudication"]["P-DC5"]["status"],
                         "RETRACTED")
        self.assertEqual(result["adjudication"]["P-DC6"]["status"],
                         "MISSED")

    def test_pdc6_fires_at_exact_increment_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            path = root / "depth_both_s0.json"
            row = json.loads(path.read_text(encoding="utf-8"))
            increment = 512 * 1024 ** 2
            row["cuda_memory"]["final_evaluation"][
                "peak_reserved_bytes"] = 2000 + increment
            row["cuda_memory"]["final_evaluation"][
                "peak_device_footprint_bytes"] = 3000 + increment
            path.write_text(json.dumps(row), encoding="utf-8")
            result = adjudicate(root)
        self.assertEqual(result["adjudication"]["P-DC6"]["status"], "FIRED")

    def test_pdc7_misses_original_high_absolute_footprint_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            path = root / "depth_both_s0.json"
            row = json.loads(path.read_text(encoding="utf-8"))
            row["cuda_memory"]["train_validation"][
                "peak_device_footprint_bytes"] = 8000
            path.write_text(json.dumps(row), encoding="utf-8")
            result = adjudicate(root)
        self.assertEqual(result["adjudication"]["P-DC7"]["status"], "MISSED")

    def test_implementation_drift_refuses_adjudication(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            for arm in ARMS:
                for seed in SEEDS:
                    path = root / f"depth_{arm}_s{seed}.json"
                    row = json.loads(path.read_text(encoding="utf-8"))
                    key = next(iter(
                        row["run_provenance"]["implementation_sha256"]))
                    row["run_provenance"]["implementation_sha256"][key] = (
                        "0" * 64)
                    path.write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "implementation drift"):
                adjudicate(root)

    def test_incomplete_matrix_refuses_instead_of_summarizing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            (root / "depth_query_s2.json").unlink()
            with self.assertRaisesRegex(ValueError, "incomplete matrix"):
                adjudicate(root)

    def test_missing_diagnostics_refuses_instead_of_hiding_failure_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            path = root / "depth_memory_s0.json"
            row = json.loads(path.read_text(encoding="utf-8"))
            del row["ood_diagnostics"]
            path.write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing teacher-forced"):
                adjudicate(root)

    def test_mislabelled_result_refuses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_matrix(root)
            path = root / "depth_both_s1.json"
            row = json.loads(path.read_text(encoding="utf-8"))
            row["consumer"] = "address"
            path.write_text(json.dumps(row), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "mislabelled"):
                adjudicate(root)


if __name__ == "__main__":
    unittest.main()
