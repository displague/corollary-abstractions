from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import torch


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))

from run_depth_consumers import (bind_artifacts, load_resumable,  # noqa: E402
                                 requested_provenance)


class DepthConsumerRunnerTests(unittest.TestCase):
    def make_pair(self, root: Path) -> tuple[Path, Path, dict]:
        diagnostic = {"mode": "teacher-forced"}
        result = root / "depth_both_s1.json"
        result.write_text(json.dumps({
            "consumer": "both", "seed": 1, "level_code": "recurrent",
            "test_diagnostics": diagnostic, "ood_diagnostics": diagnostic,
        }), encoding="utf-8")
        checkpoint = root / "depth_both_s1.pt"
        torch.save({"seed": 1, "config": {"consumer": "both",
                                           "level_code": "recurrent"}}, checkpoint)
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
                                               "level_code": "recurrent"}}, checkpoint)
            with self.assertRaisesRegex(ValueError, "mislabelled"):
                load_resumable(result, checkpoint, provenance)

    def test_resume_refuses_checkpoint_from_separate_rerun(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result, checkpoint, provenance = self.make_pair(Path(tmp))
            torch.save({"seed": 1, "config": {"consumer": "both",
                                               "level_code": "recurrent"},
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

    def test_provenance_refuses_noncanonical_dataset_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data = Path(tmp)
            for split in ("train", "val", "test", "ood"):
                (data / f"custom_{split}.jsonl").write_text(
                    f"custom-{split}", encoding="utf-8")
            with self.assertRaises(FileNotFoundError):
                requested_provenance(data, 4, "query", 2)


if __name__ == "__main__":
    unittest.main()
