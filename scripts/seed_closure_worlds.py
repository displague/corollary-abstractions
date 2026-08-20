#!/usr/bin/env python3
"""Seed the two frozen closure-world registrations (DESIGN-compile-before-query).

This is the preregistration data of ROADMAP-v0.15 item 1: the two frozen
source snapshots, their action schemas, horizons, and resource ceilings,
committed BEFORE any builder exists so that no target, horizon, or bound can
be tuned to make a gate pass. The files land in ``data/closure_worlds/`` and
regenerate byte-identically from this script (`check_regeneration.py`
enforces it, same as every corpus seed).

The two worlds are the two the design names, not new demonstrations:

* **story.golden_chicken** — the committed story world. The source is the
  ``golden_chicken`` brief exactly as ``experiments/story_curve.py`` commits
  it in ``BRIEFS`` (copied verbatim, not imported: a frozen snapshot must
  not move when an experiment file does). Its action schema is the full
  cartesian product of the domains ``story_curve.story_candidates`` draws
  from — including the ``desire`` argument, which `story_candidates` fills
  from the live state. Declaring desire in the product is what makes the
  schema a pure function of frozen sources: an action whose desire does not
  match the state is *refused by the native verifier* and recorded as a
  refusal edge, never filtered out of the enumeration.
* **visual.rt0000** — the deterministic diagram world. The source is the
  committed fixture figure ``rt-0000`` (``experiments/visual/fixtures/
  manifest.json``), and the action schema is the committed mutation
  vocabulary ``INVALID_CLASSES`` — six actions whose entire purpose is to be
  refused by ``visual.verify``. If the closure over this world is one state
  with six refusal edges, that is the honest shape of the world, reported as
  such; the design forbids authoring new actions to make it look richer.

Ceilings are the design §8 constants, frozen here as data: at most 512
distinct states, at most 32 syntactic actions per interior state, at most 30
seconds per closure on the release host, at most 8 MiB per serialized
closure. Horizons: story 5 (the oracle solution depth), visual 1 (the
committed vocabulary is one-shot). None of these numbers may move after this
commit; a closure that does not fit reports a miss (INSUFFICIENT_STRUCTURE
or a resource refusal), it does not get a resized bound.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "data" / "closure_worlds"

SCHEMA_TAG = "closure-world/1"
MANIFEST_TAG = "closure-world-manifest/1"

#: Design §8 resource ceilings, one copy, embedded in both registrations.
CEILINGS = {
    "max_states": 512,
    "max_actions_per_state": 32,
    "max_seconds_per_closure": 30,
    "max_closure_bytes": 8388608,
}

#: The ``golden_chicken`` StoryBrief, verbatim from
#: ``experiments/story_curve.py`` BRIEFS (train split). A copy, not an
#: import, so this snapshot cannot drift when the experiment module does;
#: the adapter digest pins the code, this file pins the data.
STORY_SOURCE = {
    "id": "golden_chicken",
    "agent": "the golden chicken",
    "desires": [
        "to sing the sunrise awake",
        "to out-crow the rooster",
    ],
    "trait": "golden",
    "denied_trait": "silver",
    "element": "fallen feather",
    "element_surface": "fallen feather",
    "decoy_element": "key",
    "decoy_surface": "key",
    "plant_mention": "A fallen feather lay beside a key that fit no lock.",
    "obstacles": ["the locked coop door", "a sudden frost"],
    "outcomes": [
        "It used a fallen feather as a lever, stepped outside, and sang "
        "until the sun rose",
        "It waited quietly until morning came on its own",
    ],
}

#: The committed fixture figure, verbatim from
#: ``experiments/visual/fixtures/manifest.json`` (seed 11, figure rt-0000).
#: ``near_miss_degrees`` is deliberately absent: it is a float, it is
#: informational only, and a canonical source snapshot carries no floats.
VISUAL_SOURCE = {
    "figure_id": "rt-0000",
    "params": {
        "p": 75,
        "q": 1,
        "m": 12,
        "n": 12,
        "ox": 80,
        "oy": 90,
        "hand": 1,
        "dih": 1,
    },
}


def story_action_schema(source: dict) -> list[dict]:
    """The full product `story_candidates` draws from, as literal data.

    Every parameter value is copied out of the source snapshot; nothing is
    computed at enumeration time. The derived native arguments (event_id,
    mention text, bind offsets) are the adapter's job and are pinned by the
    adapter digest, not declared here — the schema declares *which actions
    exist*, the adapter declares *what they mean natively*.
    """
    desires = list(source["desires"])
    elements = [source["element"], source["decoy_element"]]
    return [
        {
            "name": "introduce",
            "parameters": [
                {"name": "desire", "values": desires},
                {"name": "trait",
                 "values": [source["trait"], source["denied_trait"]]},
            ],
        },
        {
            "name": "plant",
            "parameters": [
                {"name": "desire", "values": desires},
                {"name": "element", "values": elements},
            ],
        },
        {
            "name": "obstruct",
            "parameters": [
                {"name": "desire", "values": desires},
                {"name": "obstacle", "values": list(source["obstacles"])},
            ],
        },
        {
            "name": "resolve",
            "parameters": [
                {"name": "desire", "values": desires},
                {"name": "outcome", "values": list(source["outcomes"])},
            ],
        },
        {
            "name": "discharge",
            "parameters": [
                {"name": "desire", "values": desires},
                {"name": "element", "values": elements},
            ],
        },
    ]


def visual_action_schema() -> list[dict]:
    """The committed mutation vocabulary, verbatim from
    ``experiments/visual/mutate.py`` INVALID_CLASSES order."""
    return [
        {
            "name": "mutate",
            "parameters": [
                {
                    "name": "kind",
                    "values": [
                        "right_angle_epsilon",
                        "leg_length",
                        "edge_disconnected",
                        "hypotenuse_retargeted",
                        "degenerate_zero_leg",
                        "right_angle_mislabeled",
                    ],
                }
            ],
        }
    ]


def registrations() -> dict[str, dict]:
    """Both world registrations, keyed by output filename."""
    return {
        "story_golden_chicken.json": {
            "schema": SCHEMA_TAG,
            "world_id": "story.golden_chicken",
            "adapter_id": "story.frame.v1",
            "horizon": 5,
            "ceilings": CEILINGS,
            "source": STORY_SOURCE,
            "action_schema": story_action_schema(STORY_SOURCE),
        },
        "visual_rt0000.json": {
            "schema": SCHEMA_TAG,
            "world_id": "visual.rt0000",
            "adapter_id": "visual.scene.v1",
            "horizon": 1,
            "ceilings": CEILINGS,
            "source": VISUAL_SOURCE,
            "action_schema": visual_action_schema(),
        },
    }


def render(obj: dict) -> str:
    return json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def sha256_lf(text: str) -> str:
    """Canonical-LF SHA-256 (design §8): CRLF normalized before hashing so
    the digest is a property of the content, not of the platform's newline
    translation."""
    return hashlib.sha256(
        text.replace("\r\n", "\n").encode("utf-8")
    ).hexdigest()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    entries = []
    for filename, registration in sorted(registrations().items()):
        text = render(registration)
        (OUT_DIR / filename).write_text(text, encoding="utf-8")
        entries.append({
            "path": f"data/closure_worlds/{filename}",
            "sha256_lf": sha256_lf(text),
        })
    manifest = {"schema": MANIFEST_TAG, "files": entries}
    (OUT_DIR / "manifest.json").write_text(
        render(manifest), encoding="utf-8"
    )
    print(f"wrote {len(entries)} registration(s) + manifest to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
