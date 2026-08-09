"""Single source of truth for the v0.6 depth-consumer safety protocol."""

from __future__ import annotations

import json
import os
from pathlib import Path

LOGICAL_BATCH_SIZE = 192
MICROBATCH_SIZE = 64
EVAL_BATCH_SIZE = 32
MAX_EVAL_INCREMENT_BYTES = 512 * 1024 ** 2
PER_PROCESS_MEMORY_FRACTION = 0.70
MAX_DEVICE_FOOTPRINT_FRACTION = 0.80
RUN_TIMEOUT_SECONDS = 2 * 60 * 60

P_DC5 = (
    "Two identical Windows bugchecks occurred after all ten epochs of the "
    "combined arm, at the final-evaluation boundary, while the GPU held about "
    "15.76/16.30 GiB. The replacement matrix keeps training batch 192, uses "
    "final test/OOD evaluation batch 32, binds both values into every result "
    "and checkpoint, and records final-evaluation peak below 12 GiB for every "
    "arm. A breach stops the matrix; it is not permission to retry the unsafe "
    "protocol. The nine pre-correction rows are archived as interrupted-"
    "protocol evidence and are not mixed into adjudication."
)

P_DC6 = (
    "Keep logical batch 192 and paired data order, but accumulate gradients "
    "over 64-example GPU microbatches; use batch 32 for validation, test, OOD, "
    "and diagnostics. Every row binds all three values and records peak "
    "allocated, reserved, and whole-device footprint separately for train/"
    "validation and final evaluation. All fifteen rows complete, and final "
    "evaluation adds no more than 512 MiB above the train/validation reserved "
    "or whole-device high-water mark. A breach is a missed safety prediction "
    "and stops release adjudication."
)

P_DC7 = (
    "Before model construction, cap the PyTorch caching allocator at 70% of "
    "device memory. Treat that cap as a mechanism-enforced clause, report "
    "whether every completed phase stayed within it, and require every "
    "observed whole-device footprint to stay below 80%; a breach is a missed "
    "safety prediction and stops the matrix."
)


def atomic_write_json(path: Path, payload: dict) -> None:
    """Flush payload bytes before atomically replacing the destination."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        json.dump(payload, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
