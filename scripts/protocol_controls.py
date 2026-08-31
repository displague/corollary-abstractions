#!/usr/bin/env python3
"""The capability-blind controls, and the broken runtimes that prove they fire.

``docs/DESIGN-protocol-uptake.md`` §8 states the voiding sentence:

    If the best surface-only classifier of the runtime's selected moves, or
    the best position-only classifier of those moves, agrees with the runtime
    on more than ``c_surface`` or ``c_position`` cells of the sealed 32, the
    runtime leaked labels into that view and the protocol uptake claim is
    void.

and a second control that selects ``greeting`` at ``fresh_root`` and
``REFUSED`` elsewhere, whose frozen table-agreement U-P0 seals. §6 step 4
requires this file **before** the runtime implementation exists, together with
the B10 receipt-replay checker: an instrument written after the thing it
measures is an instrument fitted to it.

A control nobody has watched fire is a comment
----------------------------------------------

AGENTS.md's third working rule is that every test is vacuity-checked with the
cheapest capability-blind baseline. The two functions at the bottom of this
file are that check made executable: they are **deliberately broken
runtimes**, and the tests require each to *fire* the voiding sentence.

* :func:`lexical_trigger_runtime` is the lexical trigger this whole design
  abolishes — surface in, family out, position ignored. Its labels are
  constant along each row, so the best surface-only fit to them is 32/32,
  which is above ``c_surface`` and voids the claim.
* :func:`position_switch_runtime` *is* §8's position switch. Its agreement
  with that control is 32/32, above the frozen table-agreement, and voids the
  claim.

Neither is importable into the real path: ``scripts/protocol_runtime.py``
imports nothing from this module, and a test asserts that. They exist so the
gate that clears the runtime is known to be a gate and not a rubber stamp.

Equality is not a firing
------------------------

A table-faithful runtime reproduces the sealed table exactly, so its
restricted-view fits *equal* the frozen ceilings. §7's B4 is explicit that
equality passes and only exceeding fires. The sealed table itself is
therefore a negative control, and the tests score it as one.

Shape of a labeling
-------------------

Every function here takes ``labels`` as the 8x4 grid of the sealed table:
eight rows in ``product_surfaces`` order, four columns in the ``positions``
order, each cell a move-family name or ``REFUSED``. That is the object §7's
B4 fits, and the runtime's 32 selected moves reduce to exactly that shape.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

REPO = Path(__file__).resolve().parents[1]
FIXTURES_PATH = REPO / "experiments" / "protocol_uptake_fixtures.json"

REFUSED = "REFUSED"
CELLS = 32
FRESH_ROOT = "fresh_root"
GREETING = "greeting"

Labels = Sequence[Sequence[str]]


class ControlError(ValueError):
    """A labeling that is not an 8x4 grid — never silently scored."""


def _check(labels: Labels) -> list[list[str]]:
    grid = [list(row) for row in labels]
    if sum(len(row) for row in grid) != CELLS:
        raise ControlError(
            f"a labeling of {sum(len(row) for row in grid)} cells is not the sealed 32"
        )
    widths = {len(row) for row in grid}
    if len(widths) != 1:
        raise ControlError(f"ragged labeling: row widths {sorted(widths)}")
    return grid


# --------------------------------------------------------------------------
# Loading the sealed table (the fitting target B1 recomputes).
# --------------------------------------------------------------------------


def load_fixtures(path: Path | str | None = None) -> dict[str, Any]:
    return json.loads(Path(path or FIXTURES_PATH).read_text(encoding="utf-8"))


def sealed_labels(fixtures: dict[str, Any]) -> list[list[str]]:
    """The sealed 8x4 table as a labeling."""

    return [[cell["label"] for cell in row["cells"]] for row in fixtures["sealed_table"]]


def position_ids(fixtures: dict[str, Any]) -> list[str]:
    return [cell["position_id"] for cell in fixtures["sealed_table"][0]["cells"]]


# --------------------------------------------------------------------------
# The two restricted-view fits.
# --------------------------------------------------------------------------


def _best_constant_agreement(group: Sequence[str]) -> int:
    """The best a classifier blind to everything but the group can do on it."""

    return max(Counter(group).values())


def fit_surface_only(labels: Labels) -> int:
    """Fit the best function of **surface alone** and score it in-sample.

    A surface-only view sees which row a cell is in and nothing else, so the
    best such classifier answers one label per row: the row's most frequent
    label. Its agreement is the sum of those multiplicities. Fitted to the
    sealed table this is ``c_surface``; fitted to a runtime's labels it is
    what B4 compares against ``c_surface``.

    Equivalently witness-only: under exact lookup the witness set is a
    function of the surface (DESIGN §3), so there is no third independent
    view to fit.
    """

    return sum(_best_constant_agreement(row) for row in _check(labels))


def fit_position_only(labels: Labels) -> int:
    """Fit the best function of **position alone** and score it in-sample."""

    return sum(_best_constant_agreement(column) for column in zip(*_check(labels)))


def best_surface_map(labels: Labels) -> list[str]:
    """The fitted surface-only classifier's answer per row (ties: lowest label)."""

    return [min(Counter(row).most_common(), key=lambda kv: (-kv[1], kv[0]))[0] for row in _check(labels)]


def best_position_map(labels: Labels) -> list[str]:
    """The fitted position-only classifier's answer per column (ties: lowest label)."""

    return [
        min(Counter(column).most_common(), key=lambda kv: (-kv[1], kv[0]))[0]
        for column in zip(*_check(labels))
    ]


def position_switch_agreement(
    labels: Labels, positions: Sequence[str] | None = None
) -> int:
    """Agreement of ``fresh_root -> greeting, else REFUSED`` with a labeling.

    Fitted to nothing: this control is fixed in advance, which is why U-P0
    could freeze its table-agreement. §8 voids the claim if the runtime's
    agreement with it **exceeds** that frozen number — that is, if the
    runtime *is* the position switch.
    """

    grid = _check(labels)
    columns = list(positions) if positions is not None else [FRESH_ROOT, "", "", ""]
    agree = 0
    for row in grid:
        for index, label in enumerate(row):
            predicted = GREETING if columns[index] == FRESH_ROOT else REFUSED
            agree += int(predicted == label)
    return agree


# --------------------------------------------------------------------------
# The voiding sentence, evaluated.
# --------------------------------------------------------------------------


def voiding_sentence_evaluation(
    labels: Labels,
    *,
    c_surface: int,
    c_position: int,
    frozen_position_switch_agreement: int,
    positions: Sequence[str] | None = None,
) -> dict[str, Any]:
    """§8's sentence as a computation, with its thresholds beside its numbers.

    "Reporting the score without a threshold is not a control" — so each arm
    carries the frozen number it is judged against and its own ``exceeds``
    verdict, and ``fired`` is their disjunction.
    """

    surface = fit_surface_only(labels)
    position = fit_position_only(labels)
    switch = position_switch_agreement(labels, positions)
    arms = {
        "surface_only_refit": {
            "agreement": surface,
            "frozen_ceiling": c_surface,
            "exceeds": surface > c_surface,
            "equality_is_not_a_firing": surface == c_surface,
        },
        "position_only_refit": {
            "agreement": position,
            "frozen_ceiling": c_position,
            "exceeds": position > c_position,
            "equality_is_not_a_firing": position == c_position,
        },
        "position_switch": {
            "agreement": switch,
            "frozen_table_agreement": frozen_position_switch_agreement,
            "exceeds": switch > frozen_position_switch_agreement,
            "equality_is_not_a_firing": switch == frozen_position_switch_agreement,
        },
    }
    return {
        "cells": CELLS,
        "arms": arms,
        "fired": any(arm["exceeds"] for arm in arms.values()),
        "fired_arms": sorted(name for name, arm in arms.items() if arm["exceeds"]),
    }


# --------------------------------------------------------------------------
# DELIBERATELY BROKEN RUNTIMES. Controls only. Never the real path.
# --------------------------------------------------------------------------

BROKEN_CONTROL_NOTE = (
    "A deliberately broken runtime, used only to prove the voiding sentence "
    "can fire. It is not an implementation of anything and nothing in "
    "scripts/protocol_runtime.py imports this module."
)


def lexical_trigger_runtime(sealed: Labels) -> list[list[str]]:
    """BROKEN CONTROL — the lexical trigger this design abolishes.

    Maps surface to the family that surface most often takes in the sealed
    table's *selected* cells, ignoring position entirely, and answers that
    family in all four positions. Ties are broken by the lowest family name,
    so the control is deterministic.

    Its output is constant along each row, so ``fit_surface_only`` scores it
    32/32 — above ``c_surface`` — and the claim is void. That is the point:
    a runtime that keys off bytes cannot hide inside this gate.
    """

    grid = _check(sealed)
    out = []
    for row in grid:
        selected = [label for label in row if label != REFUSED]
        pool = Counter(selected) if selected else Counter(row)
        family = min(pool.most_common(), key=lambda kv: (-kv[1], kv[0]))[0]
        out.append([family] * len(row))
    return out


def position_switch_runtime(
    sealed: Labels, positions: Sequence[str] | None = None
) -> list[list[str]]:
    """BROKEN CONTROL — §8's position switch, as a runtime.

    Answers ``greeting`` at ``fresh_root`` and ``REFUSED`` everywhere else,
    reading no surface at all. Its agreement with the position-switch control
    is 32/32, above the frozen table-agreement of the sealed table, so the
    claim is void.
    """

    grid = _check(sealed)
    columns = list(positions) if positions is not None else [FRESH_ROOT, "", "", ""]
    return [
        [GREETING if columns[index] == FRESH_ROOT else REFUSED for index in range(len(row))]
        for row in grid
    ]


# --------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    """Print the three control numbers for the sealed table and both controls."""

    fixtures = load_fixtures()
    sealed = sealed_labels(fixtures)
    columns = position_ids(fixtures)
    ceilings = fixtures["ceilings"]
    frozen_switch = fixtures["position_switch_control"]["frozen_table_agreement"]
    report = {
        "sealed_table": voiding_sentence_evaluation(
            sealed,
            c_surface=ceilings["c_surface"],
            c_position=ceilings["c_position"],
            frozen_position_switch_agreement=frozen_switch,
            positions=columns,
        ),
        "broken_lexical_trigger_runtime": voiding_sentence_evaluation(
            lexical_trigger_runtime(sealed),
            c_surface=ceilings["c_surface"],
            c_position=ceilings["c_position"],
            frozen_position_switch_agreement=frozen_switch,
            positions=columns,
        ),
        "broken_position_switch_runtime": voiding_sentence_evaluation(
            position_switch_runtime(sealed, columns),
            c_surface=ceilings["c_surface"],
            c_position=ceilings["c_position"],
            frozen_position_switch_agreement=frozen_switch,
            positions=columns,
        ),
        "note": BROKEN_CONTROL_NOTE,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
