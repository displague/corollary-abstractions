#!/usr/bin/env python3
"""Is the foreign voice armed? One read, so the line and the sheet agree.

DESIGN-voice-completion §5.1 lands 4d's code **before** the run that
authorises it, on one condition: the surface **arms itself from the
registered artifact**. With `experiments/foreign_voice_rate2.json` absent or
voided, nothing is emitted. So the code moves once, with §4's batch, and the
surface moves later — or never — without a second commit, and a void costs no
commit at all.

**Why this is a module and not two functions.** Two surfaces consult this:
the `in words` line in `answer.render` and the `foreign_voice` row in the
capability sheet. If each read the artifact its own way they could disagree —
a sheet advertising a surface that emits nothing, or a line appearing under a
row that says `served: false`. That disagreement is not hypothetical: the
v0.19 row keyed its behaviour off `c_v4["voided_classes"]` while the run's
own verdict lives at `verdicts["voided"]`, and the two are different fields
that merely happened to agree. One read, one answer, both callers.

**The arming rule, stated once — and it is NOT "nothing voided".** That was
this module's first rule and it was wrong in a way worth recording, because
the mistake is the natural one. The registered run reads `FIRES` with a
NON-EMPTY `voided` list: it contains `C-V3′`, the machine-reader claim,
which §8 voids **deliberately** and marks explicitly non-blocking. The design
declines to claim that a reader can recover the mathematics determinately
from the English, and it says so by voiding that control rather than by
omitting it. A gate keyed on an empty `voided` list would therefore read a
deliberate, published non-claim as a failure and leave the voice dark
forever — withholding a surface whose evidence had actually cleared.

So the gate asks the narrower question the design poses: **did every control
that can STOP the cycle clear?** That list is :data:`BLOCKING_CHECKS`, and a
run must also read `FIRES` overall. Anything else — absent file, unreadable
file, a failed blocking control, an `overall` that is not `FIRES` — leaves
the surface dark with the reason recorded. A non-blocking void is published
beside the armed surface, never hidden and never counted against it.

**What "dark" means, and what it does not.** Dark is not an error. It is the
honest state of a surface whose evidence has not landed: the `in words` line
is simply absent (R3's refusal-by-absence, the same discipline v0.18's line
already follows) and the sheet row publishes `served: false` with the reason.
Neither is a crash, and neither invents a sentence.
"""

from __future__ import annotations

import json
from pathlib import Path

#: The v0.20 run that can arm the surface. Absent today, by design.
FOREIGN_VOICE_RUN2 = "experiments/foreign_voice_rate2.json"

#: The v0.19 run. It is the record of a VOID and can never arm anything; it
#: is read only so the dark row can say WHY the surface is dark rather than
#: only that it is.
FOREIGN_VOICE_RUN1 = "experiments/foreign_voice_rate.json"

FOREIGN_VOICE_REGISTER = "data/foreign_voice/register.json"

#: The verdict a cleared run carries. `FIRES` is the gate's own word for a
#: floor that was met; it is not `HOLDS`, which is what a *control* reports.
FIRES = "FIRES"


#: The controls that STOP the cycle, each with the fields that decide it.
#:
#: **This list, and not `verdicts.voided`, is the arming gate — and the
#: distinction is load-bearing rather than pedantic.** The registered run
#: carries a non-empty `voided` list containing `C-V3′`, the machine-reader
#: claim, which §8 voids DELIBERATELY and marks explicitly non-blocking: the
#: design declines to claim a reader can recover the mathematics
#: determinately from the English, and says so by voiding that control rather
#: than by omitting it. A gate keyed on "nothing voided" would therefore read
#: a deliberate, published non-claim as a failure and leave the voice dark
#: forever — refusing to serve a surface whose evidence had actually cleared.
#:
#: So arming asks the narrower question the design actually poses: did every
#: control that can stop the cycle clear? Each entry is
#: (label, path-into-the-run, predicate, what-failure-means).
BLOCKING_CHECKS = (
    ("C-G1", "c_g1",
     lambda block: block.get("voided") is False
     and block.get("named_floor_met") is True,
     "the grouping control voided or missed its named floor"),
    ("C-V4′", "c_v4_prime",
     lambda block: block.get("voided") is False
     and list(block.get("voided_classes") or ()) == [],
     "the re-specified near-miss control voided, or a mutation class fell "
     "below its floor"),
    ("B1", "b1", lambda block: block.get("floor_met") is True,
     "the identity floor was not met"),
    ("B3", "b3", lambda block: block.get("closes_exactly") is True,
     "the rendered/registered arithmetic does not close"),
    ("B5", "b5", lambda block: block.get("byte_identical") is True,
     "two runs over one tree were not byte-identical"),
)


def _read(root: Path, relative: str):
    """One artifact as a MAPPING, or (None, reason). Never raises at a caller.

    The shape check is the point, not decoration (adversarial review, M1).
    `json.loads` happily returns a list, a string or a number, and every read
    below then did `.get(...)` on it — so a file containing `[]` raised an
    `AttributeError` straight through BOTH callers: out of `answer.render`,
    which is a served path, and out of the sheet build. A malformed artifact
    must leave the surface dark with the reason recorded, exactly as an
    absent one does. Failing open on a file this module cannot understand
    would be the arming gate deciding by accident.
    """

    try:
        loaded = json.loads((root / relative).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if not isinstance(loaded, dict):
        return None, (
            f"the file is valid JSON but not an object "
            f"({type(loaded).__name__}); an arming decision cannot be read "
            f"from it"
        )
    return loaded, None


def arming_state(repo_root: Path | str) -> dict:
    """Whether the foreign voice may be served, and why not when it may not.

    Returns a plain record so both callers branch on one field: `armed`.
    Everything else is for the sheet to publish and for a person to read —
    including `non_blocking_voids`, because a void this design took on
    purpose should be visible beside the surface it did not stop.
    """

    root = Path(repo_root)
    state: dict = {
        "armed": False,
        "run": FOREIGN_VOICE_RUN2,
        "arming_rule": (
            "armed when the registered run reads FIRES and every "
            "cycle-stopping control cleared: "
            + ", ".join(label for label, _, _, _ in BLOCKING_CHECKS)
            + ". A void that the design marks non-blocking (C-V3', the "
            "machine-reader claim) is published, not treated as a failure."
        ),
    }

    run2, error = _read(root, FOREIGN_VOICE_RUN2)
    if run2 is None:
        prior, _ = _read(root, FOREIGN_VOICE_RUN1)
        state["reason"] = (
            f"no registered run at {FOREIGN_VOICE_RUN2}; the foreign voice "
            f"stays dark until one lands"
        )
        if error is not None and "FileNotFoundError" not in error:
            # An unreadable file is a different fact from an absent one and
            # is never rounded to it.
            state["reason"] = (
                f"the registered run at {FOREIGN_VOICE_RUN2} could not be "
                f"read ({error}); the foreign voice stays dark"
            )
        if isinstance(prior, dict):
            verdicts = prior.get("verdicts")
            verdicts = verdicts if isinstance(verdicts, dict) else {}
            state["prior_run"] = {
                "path": FOREIGN_VOICE_RUN1,
                "verdict": verdicts.get("overall"),
                "voided": list(verdicts.get("voided") or ()),
                "summary": verdicts.get("summary"),
                "read_this_as": (
                    "the v0.19 run, kept as the record of what was measured. "
                    "It cannot arm anything; it is quoted so the dark row "
                    "says why rather than only that."
                ),
            }
        return state

    verdicts = run2.get("verdicts")
    if not isinstance(verdicts, dict):
        state["reason"] = (
            f"{FOREIGN_VOICE_RUN2} carries no readable `verdicts` object "
            f"({type(verdicts).__name__}); the foreign voice stays dark"
        )
        return state
    overall = verdicts.get("overall")
    raw_voided = verdicts.get("voided")
    voided = list(raw_voided) if isinstance(raw_voided, (list, tuple)) else []
    state["verdict"] = overall
    state["voided"] = voided
    state["summary"] = verdicts.get("summary")

    failures: list[str] = []
    checks: dict[str, bool] = {}
    if overall != FIRES:
        failures.append(f"the run reads {overall!r} rather than {FIRES!r}")
    for label, key, predicate, meaning in BLOCKING_CHECKS:
        block = run2.get(key)
        passed = isinstance(block, dict) and bool(predicate(block))
        checks[label] = passed
        if not passed:
            failures.append(
                f"{label}: {meaning}" if isinstance(block, dict)
                else f"{label}: the run carries no {key!r} block to read"
            )
    state["blocking_checks"] = checks

    # Published, never silently dropped: a void the design took on purpose is
    # part of what this surface is worth, and hiding it would make the row
    # claim more than the run does.
    blocking_labels = {label for label, _, _, _ in BLOCKING_CHECKS}
    state["non_blocking_voids"] = [
        name for name in voided
        if isinstance(name, str)
        and not any(name.startswith(label) for label in blocking_labels)
    ]

    if failures:
        state["reason"] = (
            "the foreign voice stays dark: " + "; ".join(failures)
        )
        return state

    state["armed"] = True
    state["reason"] = (
        f"{FOREIGN_VOICE_RUN2} reads {overall} and every cycle-stopping "
        f"control cleared"
        + (
            f"; {', '.join(state['non_blocking_voids'])} voided without "
            f"blocking, and that void is published rather than hidden"
            if state["non_blocking_voids"] else ""
        )
    )
    return state
