#!/usr/bin/env python3
"""G-P1 — the quarantine fence, proven to catch a planted write.

DESIGN-guest-axiom §5: a deliberately-writing control session must move
the digest over data/ and be caught before any real guest session runs.
The callable is write_stage.durable_digest, the same digest the session
ledger and erratum probe already pin.
"""

from __future__ import annotations

from pathlib import Path

from write_stage import durable_digest

PLANT_NAME = "_gp1_planted_write.txt"
PLANT_BODY = "G-P1 planted write; a fence that cannot catch this is no fence.\n"


def digest_data(data_dir: Path) -> str:
    return durable_digest(data_dir)


def plant_write(data_dir: Path) -> Path:
    """Write one file under data/. Caller deletes it."""
    data_dir.mkdir(parents=True, exist_ok=True)
    planted = data_dir / PLANT_NAME
    planted.write_text(PLANT_BODY, encoding="utf-8")
    return planted


def planted_write_is_caught(data_dir: Path) -> dict:
    """1/1 control: the digest must move, then the plant is removed."""
    before = digest_data(data_dir)
    planted = plant_write(data_dir)
    after = digest_data(data_dir)
    caught = before != after
    planted.unlink()
    restored = digest_data(data_dir)
    return {
        "digest_before": before,
        "digest_after_plant": after,
        "digest_after_remove": restored,
        "caught": caught,
        "restored": restored == before,
    }


def session_unchanged(data_dir: Path, digest_before: str) -> bool:
    """B1's checked half: a real session may not move data/."""
    return digest_data(data_dir) == digest_before
