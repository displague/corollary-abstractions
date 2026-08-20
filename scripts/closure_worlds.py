#!/usr/bin/env python3
"""The two registered closure worlds behind one four-operation contract.

DESIGN-compile-before-query §4: a world is eligible only if it exposes

    initial_state()                     -> native state
    validate_and_apply(state, action)   -> Refusal | native state
    canonicalize(state)                 -> canonical bytes

with the fourth operation — the action schema — living as DATA in the
world's committed registration (``data/closure_worlds/*.json``), never as a
callback here. The generic builder and checker enumerate the schema product
themselves; an adapter maps each enumerated ``(name, params)`` pair to its
native action and hands it to the world's OWN verifier. Nothing in this
module decides legality: the story adapter's verdicts come from
:class:`oracle_controller_demo.StoryFrameVerifier` and the visual adapter's
from :func:`visual.verify.verify`, exactly the code those worlds already
trust.

Adapters are world-specific by definition; this is the one module that may
know a world's name. The generic layer (``closure_check``, ``closure_build``)
selects an adapter only through the registration's declared ``adapter_id``
via :func:`load_world`, per §5's registry rule, and is forbidden from
branching on world names — a prohibition ``tests/test_bounded_closure.py``
enforces by scanning their source.

Determinism notes, argued rather than hoped:

* The story adapter derives native arguments (event_id, mention text, bind
  offsets) with the same closed-form rules as
  ``experiments/story_curve.story_candidates`` — `bind_spec` over the
  rendered string, never a magic number. A derivation that cannot be
  realized (a surface absent from its text) is a deterministic
  :class:`Refusal`, not an exception escaping the contract.
* Story canonical bytes come from ``session_state.encode`` — the committed,
  registry-closed codec — dumped with sorted keys. NOT ``repr(state)``:
  ``StoryFrameVerifier.state_key`` is `repr`-based and is deliberately not
  blessed here (two notions of state identity is one too many, and `repr`
  is not a designed serialization).
* Visual canonical bytes come from ``visual.scene``'s own float-free
  ``normalize`` + ``to_dict``, the strongest canonical form in the repo,
  wrapped with the claim (a mutation may adjust the claim, so the claim is
  state, not context).
* The visual world's committed mutation semantics are anchored to the
  frozen figure parameters (``mutate`` rebuilds from params), so its
  transitions are defined at the initial state only. Any action offered to
  a different state is refused with a named code rather than silently
  re-anchored — that refusal IS the honest shape of a one-shot classifier
  world, recorded as data instead of worked around.
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "experiments"))

from controller import Action, ActionKind, Verification  # noqa: E402
from frames import (  # noqa: E402
    CHEKHOV_GUN,
    FRAME_CONSISTENCY,
    NO_DEUS,
    FrameSpec,
    Literal,
)
from narrative_realize import bind_spec  # noqa: E402
from oracle_controller_demo import (  # noqa: E402
    NarrativeElement,
    StoryFrameVerifier,
    StoryState,
)
from session_state import encode as session_encode  # noqa: E402

WORLD_DIR = REPO / "data" / "closure_worlds"
WORLD_SCHEMA_TAG = "closure-world/1"


@dataclass(frozen=True)
class Refusal:
    """The world said no, in its own words. A value, never an exception."""

    code: str


def canonical_json(obj: object) -> str:
    """One JSON spelling for everything digested: sorted keys, no spaces."""

    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def canonical_action(name: str, params: dict[str, str]) -> str:
    """The schema action as canonical text — the closure's edge key."""

    return canonical_json({"name": name, "params": params})


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_lf_file(path: Path) -> str:
    """Canonical-LF SHA-256 of a file (design §8): newline-translation on a
    Windows checkout must not change a frozen source's identity."""

    return sha256_hex(path.read_bytes().replace(b"\r\n", b"\n"))


def adapter_digest() -> str:
    """The digest that pins THIS module's action-mapping code."""

    return sha256_lf_file(Path(__file__).resolve())


# ---------------------------------------------------------------------------
# World 1: the committed story world
# ---------------------------------------------------------------------------


class StoryWorld:
    """The story frame world over one frozen brief snapshot."""

    adapter_id = "story.frame.v1"

    def __init__(self, source: dict):
        self.source = source
        spec = FrameSpec(
            frame=f"runtime.frames.{source['id']}",
            title=source["id"].replace("_", " "),
            declarations=(
                ("agent", Literal("story", "agent", source["agent"])),
                (source["trait"],
                 Literal(source["agent"], "trait", source["trait"])),
                (
                    f"no_{source['denied_trait']}",
                    Literal(source["agent"], "trait", source["denied_trait"],
                            polarity=False),
                ),
            ),
            governed_by=(FRAME_CONSISTENCY, CHEKHOV_GUN, NO_DEUS),
        )
        elements = (
            NarrativeElement(source["element"], (source["element_surface"],)),
            NarrativeElement(source["decoy_element"],
                             (source["decoy_surface"],)),
        )
        self._verifier = StoryFrameVerifier(spec=spec, elements=elements)
        self._surfaces = {
            source["element"]: source["element_surface"],
            source["decoy_element"]: source["decoy_surface"],
        }

    def initial_state(self) -> StoryState:
        return self._verifier.initial_state()

    def _native_action(self, name: str, params: dict[str, str]) -> Action:
        """Canonical (name, params) -> native Action, the same closed-form
        derivation as ``story_curve.story_candidates`` (cited, not imported:
        that module is a frozen experiment instrument)."""

        source = self.source
        args: dict[str, str] = {"agent": source["agent"],
                                "desire": params["desire"]}
        if name == "introduce":
            args["trait"] = params["trait"]
        elif name == "plant":
            element = params["element"]
            surface = self._surfaces[element]
            mention = source["plant_mention"]
            args["event_id"] = f"{element.replace(' ', '_')}_planted"
            args["element"] = element
            args["mention"] = mention
            args["binds"] = bind_spec(element, mention, surface)
        elif name == "obstruct":
            args["obstacle"] = params["obstacle"]
        elif name == "resolve":
            outcome = params["outcome"]
            args["outcome"] = outcome
            binds = [
                bind_spec(element, outcome, surface)
                for element, surface in self._surfaces.items()
                if surface in outcome
            ]
            if binds:
                args["binds"] = ";".join(binds)
        elif name == "discharge":
            element = params["element"]
            args["event_id"] = f"{element.replace(' ', '_')}_discharged"
            args["element"] = element
        else:
            raise ValueError(f"unregistered story action {name!r}")
        return Action.build(ActionKind.GEN, name, args)

    def validate_and_apply(
        self, state: StoryState, name: str, params: dict[str, str]
    ) -> Refusal | StoryState:
        try:
            action = self._native_action(name, params)
        except ValueError as exc:
            # A derivation the frozen sources cannot realize (e.g. a surface
            # absent from its text). Deterministic, so a legal refusal edge.
            return Refusal(f"unrealizable: {exc}")
        verification: Verification[StoryState] = self._verifier.evaluate(
            state, action
        )
        verification.validate()
        if verification.verdict.accepts:
            assert verification.next_state is not None
            return verification.next_state
        return Refusal(
            f"{verification.verdict.value}: {verification.reason}"
        )

    def canonicalize(self, state: StoryState) -> bytes:
        return canonical_json(session_encode(state)).encode("utf-8")


# ---------------------------------------------------------------------------
# World 2: the deterministic diagram world
# ---------------------------------------------------------------------------


class VisualWorld:
    """The right-triangle scene world over one frozen figure snapshot."""

    adapter_id = "visual.scene.v1"

    def __init__(self, source: dict):
        from visual.mutate import mutate  # noqa: PLC0415
        from visual.scene import (  # noqa: PLC0415
            TriangleParams,
            build_claim,
            build_scene,
            normalize,
        )
        from visual.scene import to_dict as scene_to_dict  # noqa: PLC0415
        from visual.verify import verify  # noqa: PLC0415

        self._mutate = mutate
        self._normalize = normalize
        self._scene_to_dict = scene_to_dict
        self._verify = verify
        self._figure_id = source["figure_id"]
        self._params = TriangleParams(**source["params"])
        self._initial = (
            build_scene(self._params, self._figure_id),
            build_claim(self._params),
        )
        self._initial_bytes = self.canonicalize(self._initial)

    def initial_state(self):
        return self._initial

    def validate_and_apply(
        self, state, name: str, params: dict[str, str]
    ) -> Refusal | tuple:
        if name != "mutate":
            return Refusal(f"unregistered visual action {name!r}")
        if self.canonicalize(state) != self._initial_bytes:
            # The committed mutation semantics rebuild from the frozen
            # figure parameters; they define transitions at the initial
            # state only. Unreachable while nothing accepts, and named
            # rather than silently re-anchored if that ever changes.
            return Refusal(
                "mutation_semantics_anchored_to_frozen_figure: this world "
                "defines its committed mutations only at the initial state"
            )
        graph, claim, _mutation = self._mutate(
            self._params, self._figure_id, params["kind"]
        )
        result = self._verify(graph, claim)
        if result.ok:
            return (graph, claim)
        checks = "+".join(sorted({f.check for f in result.failures}))
        return Refusal(f"verify_failed: {checks}")

    def canonicalize(self, state) -> bytes:
        graph, claim = state
        # `to_dict` over scenes is a module function in visual.scene;
        # `Claim.to_dict` is a method. Both spellings are the world's own.
        document = {
            "scene": self._scene_to_dict(self._normalize(graph)),
            "claim": claim.to_dict(),
        }
        return canonical_json(document).encode("utf-8")


# ---------------------------------------------------------------------------
# Registry: adapter_id -> implementation (design §5's sanctioned selection)
# ---------------------------------------------------------------------------


_ADAPTERS = {
    StoryWorld.adapter_id: StoryWorld,
    VisualWorld.adapter_id: VisualWorld,
}


def load_registration(path: Path) -> dict:
    registration = json.loads(path.read_text(encoding="utf-8"))
    if registration.get("schema") != WORLD_SCHEMA_TAG:
        raise ValueError(
            f"{path} declares schema {registration.get('schema')!r}, "
            f"expected {WORLD_SCHEMA_TAG!r}"
        )
    return registration


def load_world(registration: dict):
    adapter = _ADAPTERS.get(registration["adapter_id"])
    if adapter is None:
        raise ValueError(
            f"no adapter registered for {registration['adapter_id']!r}"
        )
    return adapter(registration["source"])


def registration_paths() -> tuple[Path, ...]:
    """The committed registrations, manifest order."""

    manifest = json.loads(
        (WORLD_DIR / "manifest.json").read_text(encoding="utf-8")
    )
    return tuple(REPO / entry["path"] for entry in manifest["files"])
