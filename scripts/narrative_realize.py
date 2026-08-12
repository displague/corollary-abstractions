#!/usr/bin/env python3
"""Structured story briefs → surface strings (P-LS3 slice).

Policy and search arms must not treat whole English beats as the source of
truth. A brief holds typed slots (agent, desire, obstacle, plantable
elements, outcome pattern). Named realization patterns produce mention and
outcome text; bind offsets are computed from the realized string, never
hand-authored as magic numbers.

This is the dual of the story adapter's setup/complication templates: those
already build ``"{agent} wanted {desire}."`` and ``"But {obstacle}..."``
inside the verifier. Plant and resolve were the remaining prose blobs in the
oracle policy; they move here.

Fragment: ``narrative.realize.v1`` — three patterns only (setup is adapter-
owned; plant_gleamed_nest; obstruct is adapter-owned; outcome_used_as_key).
Not open English.
"""

from __future__ import annotations

from dataclasses import dataclass

from controller import Action, ActionKind


FRAGMENT_ID = "narrative.realize.v1"


def span_of(text: str, needle: str) -> tuple[int, int]:
    """First exact occurrence; raises ValueError if missing (fail closed)."""
    start = text.index(needle)
    return start, start + len(needle)


def bind_spec(element: str, text: str, surface: str) -> str:
    start, end = span_of(text, surface)
    return f"{element}@{start}:{end}"


# ---------------------------------------------------------------------------
# Realization patterns (closed inventory)
# ---------------------------------------------------------------------------


def realize_plant_gleamed_nest(surface: str) -> str:
    """``A {surface} gleamed beside its nest.``"""
    if not surface.strip():
        raise ValueError("plant surface must be non-empty")
    return f"A {surface} gleamed beside its nest."


def realize_outcome_used_as_key(tool_surface: str, key_surface: str) -> str:
    """It used a {tool} as a {key}, stepped outside, and sang until the sun rose."""
    if not tool_surface.strip() or not key_surface.strip():
        raise ValueError("outcome surfaces must be non-empty")
    return (
        f"It used a {tool_surface} as a {key_surface}, stepped outside, "
        "and sang until the sun rose"
    )


REALIZE_PLANT = {
    "gleamed_beside_nest": realize_plant_gleamed_nest,
}
REALIZE_OUTCOME = {
    "used_as_key_and_sang": realize_outcome_used_as_key,
}


# ---------------------------------------------------------------------------
# Brief
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NarrativeBrief:
    """Structured story problem; English only via realization patterns."""

    id: str
    agent: str
    desire: str
    trait: str
    denied_trait: str
    plant_element: str
    plant_surface: str
    plant_pattern: str
    decoy_element: str
    decoy_surface: str
    obstacle: str
    outcome_pattern: str
    # outcome_used_as_key maps tool→plant surface, key→decoy surface by default
    outcome_tool_element: str | None = None
    outcome_key_element: str | None = None

    def __post_init__(self) -> None:
        if self.plant_pattern not in REALIZE_PLANT:
            raise ValueError(
                f"unknown plant_pattern {self.plant_pattern!r}; "
                f"fragment {FRAGMENT_ID} admits {sorted(REALIZE_PLANT)}"
            )
        if self.outcome_pattern not in REALIZE_OUTCOME:
            raise ValueError(
                f"unknown outcome_pattern {self.outcome_pattern!r}; "
                f"fragment {FRAGMENT_ID} admits {sorted(REALIZE_OUTCOME)}"
            )

    def realize_plant_mention(self) -> str:
        return REALIZE_PLANT[self.plant_pattern](self.plant_surface)

    def realize_outcome(self) -> str:
        tool = self.plant_surface
        key = self.decoy_surface
        return REALIZE_OUTCOME[self.outcome_pattern](tool, key)

    def plant_binds(self) -> str:
        mention = self.realize_plant_mention()
        return bind_spec(self.plant_element, mention, self.plant_surface)

    def outcome_binds(self) -> str:
        outcome = self.realize_outcome()
        tool_el = self.outcome_tool_element or self.plant_element
        key_el = self.outcome_key_element or self.decoy_element
        tool_surface = (
            self.plant_surface
            if tool_el == self.plant_element
            else self.decoy_surface
        )
        key_surface = (
            self.decoy_surface
            if key_el == self.decoy_element
            else self.plant_surface
        )
        return ";".join(
            (
                bind_spec(tool_el, outcome, tool_surface),
                bind_spec(key_el, outcome, key_surface),
            )
        )

    def oracle_actions(self) -> tuple[Action, ...]:
        """Fixed legal sequence for the demo/oracle regression (not search)."""
        shared = {"agent": self.agent, "desire": self.desire}
        mention = self.realize_plant_mention()
        outcome = self.realize_outcome()
        return (
            Action.build(
                ActionKind.GEN,
                "introduce",
                {**shared, "trait": self.trait},
            ),
            Action.build(
                ActionKind.GEN,
                "plant",
                {
                    **shared,
                    "event_id": f"{self.plant_element.replace(' ', '_')}_planted",
                    "element": self.plant_element,
                    "mention": mention,
                    "binds": self.plant_binds(),
                },
            ),
            Action.build(
                ActionKind.GEN,
                "obstruct",
                {**shared, "obstacle": self.obstacle},
            ),
            Action.build(
                ActionKind.GEN,
                "resolve",
                {
                    **shared,
                    "outcome": outcome,
                    "binds": self.outcome_binds(),
                },
            ),
            Action.build(
                ActionKind.GEN,
                "discharge",
                {
                    **shared,
                    "event_id": (
                        f"{self.plant_element.replace(' ', '_')}_used_as_key"
                    ),
                    "element": self.plant_element,
                },
            ),
        )


# Canonical golden-chicken brief: slots + patterns, no hand-written binds.
GOLDEN_CHICKEN_BRIEF = NarrativeBrief(
    id="golden_chicken",
    agent="the golden chicken",
    desire="to sing the sunrise awake",
    trait="golden",
    denied_trait="silver",
    plant_element="fallen feather",
    plant_surface="fallen feather",
    plant_pattern="gleamed_beside_nest",
    decoy_element="key",
    decoy_surface="key",
    obstacle="the locked coop door",
    outcome_pattern="used_as_key_and_sang",
)


# P-LS2: licensed surface packagings that denote the denied trait "silver"
# (structured trait field still carries the denotation; packaging is the
# English that claims that trait — not desire-string variation).
SILVER_TRAIT_PACKAGES: tuple[str, ...] = tuple(
    f"appears {w}"
    for w in (
        "silver",
        "silvery",
        "argent",
        "chrome-like",
        "pewter-toned",
        "quicksilver",
        "moon-metal",
        "white-metal",
        "tin-bright",
        "mercury-sheen",
        "frost-metal",
        "coin-colored",
        "steel-pale",
        "ash-metal",
        "mirror-pale",
        "cloud-metal",
        "ghost-metal",
        "pale-metal",
        "luster-silver",
        "sheen-silver",
    )
)


def package_trait_denotation(surface: str) -> str | None:
    """Map a trait packaging surface to a trait id, or None if unregistered."""
    text = " ".join(surface.split()).casefold()
    if text in {p.casefold() for p in SILVER_TRAIT_PACKAGES} or text == "silver":
        return "silver"
    if text in {"golden", "appears golden", "gold-colored"}:
        return "golden"
    return None
