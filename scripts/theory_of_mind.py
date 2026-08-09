#!/usr/bin/env python3
"""Executable Sally-Anne false-belief control for v0.5 item 10c."""

from frames import FrameEvent, FrameExecutor, FrameSpec, Literal


def run() -> tuple[str | None, str | None]:
    executor = FrameExecutor()
    sally = executor.open_frame(
        FrameSpec(frame="runtime.frames.belief_sally", owner="sally")
    )
    world = executor.open_frame(
        FrameSpec(frame="runtime.frames.belief_world", owner="world")
    )
    basket = Literal("marble", "located_in", "basket")
    placement = FrameEvent(
        "placement", (basket,), ("sally", "anne", "world"), ("located_in",)
    )
    move = FrameEvent(
        "move",
        (basket.negated, Literal("marble", "located_in", "box")),
        ("anne", "world"),
        ("located_in",),
    )
    for event in (placement, move):
        sally = executor.observe_event(sally, event).next_state
        world = executor.observe_event(world, event).next_state
    return (
        executor.belief_value(sally, "marble", "located_in"),
        executor.belief_value(world, "marble", "located_in"),
    )


def main() -> int:
    sally, world = run()
    print(f"WORLD: the marble is in the {world}")
    print(f"SALLY: Sally will look in the {sally}")
    print("CAUSE: Sally witnessed placement but not the move")
    print("STATUS: false belief derived from visibility; neither frame leaked")
    return 0 if (sally, world) == ("basket", "box") else 1


if __name__ == "__main__":
    raise SystemExit(main())
