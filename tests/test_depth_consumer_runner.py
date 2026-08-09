from __future__ import annotations

import json
import pickle
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import torch


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))

from run_depth_consumers import (accept_safe_row, bind_artifacts,  # noqa: E402
                                 gpu_environment, load_resumable,
                                 requested_provenance, safety_breaches,
                                 try_load_resumable,
                                 validate_gpu_environment)


class DepthConsumerRunnerTests(unittest.TestCase):
    def make_pair(self, root: Path) -> tuple[Path, Path, dict]:
        diagnostic = {"mode": "teacher-forced"}
        result = root / "depth_both_s1.json"
        result.write_text(json.dumps({
            "consumer": "both", "seed": 1, "level_code": "recurrent",
            "batch_size": 192, "microbatch_size": 64,
            "eval_batch_size": 32, "memory_fraction": 0.70,
            "test_diagnostics": diagnostic, "ood_diagnostics": diagnostic,
        }), encoding="utf-8")
        checkpoint = root / "depth_both_s1.pt"
        torch.save({"seed": 1, "config": {"consumer": "both",
                                           "level_code": "recurrent",
                                           "batch_size": 192,
                                           "microbatch_size": 64,
                                           "eval_batch_size": 32,
                                           "memory_fraction": 0.70}}, checkpoint)
        data = root / "data"
        data.mkdir()
        for split in ("train", "val", "test", "ood"):
            (data / f"analogy_{split}.jsonl").write_text(split, encoding="utf-8")
        provenance = requested_provenance(data, 10, "both", 1)
        bind_artifacts(result, checkpoint, provenance)
        return result, checkpoint, provenance

    def test_resume_binds_result_to_checkpoint_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result, checkpoint, provenance = self.make_pair(Path(tmp))
            row = load_resumable(result, checkpoint, provenance)
        self.assertEqual(row["consumer"], "both")

    def test_resume_refuses_cross_arm_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result, checkpoint, provenance = self.make_pair(Path(tmp))
            torch.save({"seed": 1, "config": {"consumer": "query",
                                               "level_code": "recurrent",
                                               "batch_size": 192,
                                               "microbatch_size": 64,
                                               "eval_batch_size": 32,
                                               "memory_fraction": 0.70}}, checkpoint)
            with self.assertRaisesRegex(ValueError, "mislabelled"):
                load_resumable(result, checkpoint, provenance)

    def test_resume_refuses_checkpoint_from_separate_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result, checkpoint, provenance = self.make_pair(Path(tmp))
            torch.save({"seed": 1, "config": {"consumer": "both",
                                               "level_code": "recurrent",
                                               "batch_size": 192,
                                               "microbatch_size": 64,
                                               "eval_batch_size": 32,
                                               "memory_fraction": 0.70},
                        "different_weights": True}, checkpoint)
            with self.assertRaisesRegex(ValueError, "unbound checkpoint"):
                load_resumable(result, checkpoint, provenance)

    def test_resume_refuses_changed_epochs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result, checkpoint, provenance = self.make_pair(Path(tmp))
            changed = dict(provenance)
            changed["epochs"] = 11
            with self.assertRaisesRegex(ValueError, "different experiment"):
                load_resumable(result, checkpoint, changed)

    def test_resume_refuses_changed_evaluation_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result, checkpoint, provenance = self.make_pair(Path(tmp))
            changed = dict(provenance)
            changed["eval_batch_size"] = 64
            with self.assertRaisesRegex(ValueError, "mislabelled"):
                load_resumable(result, checkpoint, changed)

    def test_provenance_refuses_noncanonical_dataset_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            for split in ("train", "val", "test", "ood"):
                (data / f"custom_{split}.jsonl").write_text(
                    f"custom-{split}", encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                requested_provenance(data, 4, "query", 2)

    def test_environment_fails_fast_before_matrix(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "driver_version"):
            validate_gpu_environment({
                "cuda_available": True,
                "torch_version": "test",
                "cuda_runtime": "test",
                "device_name": "test",
                "device_total_bytes": 1,
                "driver_version": None,
            })

    @patch("run_depth_consumers.torch.cuda.get_device_properties",
           return_value=SimpleNamespace(name="test", total_memory=10_000))
    @patch("run_depth_consumers.torch.cuda.current_device", return_value=0)
    @patch("run_depth_consumers.torch.cuda.is_available", return_value=True)
    @patch("run_depth_consumers.subprocess.check_output",
           side_effect=FileNotFoundError)
    def test_missing_nvidia_smi_driver_fails_environment_gate(
            self, mocked_check_output, _mocked_available, _mocked_current,
            _mocked_properties) -> None:
        captured = gpu_environment()
        self.assertEqual(mocked_check_output.call_count, 2)
        with self.assertRaisesRegex(RuntimeError, "driver_version"):
            validate_gpu_environment(captured["stable"])

    def test_volatile_telemetry_is_not_resume_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result, checkpoint, provenance = self.make_pair(Path(tmp))
            row = json.loads(result.read_text(encoding="utf-8"))
            row["launch_telemetry"] = {"clock_event_reasons_active": "changed"}
            result.write_text(json.dumps(row), encoding="utf-8")
            resumed = load_resumable(result, checkpoint, provenance)
        self.assertEqual(resumed["consumer"], "both")

    def test_truncated_checkpoint_is_rejected_for_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result, checkpoint, provenance = self.make_pair(Path(tmp))
            checkpoint.write_bytes(b"not-a-checkpoint")
            row, error = try_load_resumable(result, checkpoint, provenance)
        self.assertIsNone(row)
        self.assertIsInstance(error, (RuntimeError, EOFError,
                                      pickle.UnpicklingError))

    def test_safety_breach_stops_before_next_row(self) -> None:
        environment = {"device_total_bytes": 10_000}
        row = {"cuda_memory": {
            "train_validation": {
                "peak_reserved_bytes": 2_000,
                "peak_device_footprint_bytes": 8_000,
            },
            "final_evaluation": {
                "peak_reserved_bytes": 2_000,
                "peak_device_footprint_bytes": 8_000,
            },
        }}
        breaches = safety_breaches(row, environment)
        self.assertTrue(any("device" in breach for breach in breaches))
        accepted = []
        with self.assertRaisesRegex(RuntimeError, "stopping matrix"):
            accept_safe_row(accepted, row, environment)
        self.assertEqual(accepted, [])


if __name__ == "__main__":
    unittest.main()
