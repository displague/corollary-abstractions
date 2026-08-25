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

**The arming rule, stated once.** The voice is armed when the registered run
exists AND its own verdict block says nothing voided. `verdicts["voided"]`
is the field, because it is the field the run calls its verdict —
`c_v4["voided_classes"]` is one control's internal detail that happened to
agree in the shipped artifact. Anything else — absent file, unreadable file,
a non-empty `voided` list, an `overall` that is not the all-clear — leaves
the surface dark with the reason recorded.

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

#: The verdict string a run must carry for the surface to arm. Anything else
#: — including a string this module does not recognise — leaves it dark,
#: because an unrecognised verdict is not an all-clear.
ALL_CLEAR = "HOLDS"


def _read(root: Path, relative: str):
    try:
        return json.loads((root / relative).read_text(encoding="utf-8")), None
    except (OSError, ValueError) as exc:
        return None, f"{type(exc).__name__}: {exc}"


def arming_state(repo_root: Path | str) -> dict:
    """Whether the foreign voice may be served, and why not when it may not.

    Returns a plain record so both callers branch on one field: `armed`.
    Everything else is for the sheet to publish and for a person to read.
    """

    root = Path(repo_root)
    state: dict = {
        "armed": False,
        "run": FOREIGN_VOICE_RUN2,
        "arming_rule": (
            "armed only when the registered run exists and its own "
            "verdicts.voided list is empty with an all-clear overall"
        ),
    }

    run2, error = _read(root, FOREIGN_VOICE_RUN2)
    if run2 is None:
        # The state this repository is actually in at §4's batch.
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
            verdicts = prior.get("verdicts") or {}
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

    verdicts = run2.get("verdicts") or {}
    voided = list(verdicts.get("voided") or ())
    overall = verdicts.get("overall")
    state["verdict"] = overall
    state["voided"] = voided
    state["summary"] = verdicts.get("summary")
    if voided or overall != ALL_CLEAR:
        state["reason"] = (
            f"{FOREIGN_VOICE_RUN2} reads {overall!r}"
            + (f" with {', '.join(voided)} voided" if voided else "")
            + "; a voided control outranks any floor it gates, so the "
            "foreign voice stays dark"
        )
        return state

    state["armed"] = True
    state["reason"] = (
        f"{FOREIGN_VOICE_RUN2} reads {overall!r} with nothing voided"
    )
    return state
