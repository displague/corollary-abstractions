#!/usr/bin/env python3
"""Closed-form Lean goal reading, tactic-argument generation, blind orders.

ROADMAP-v0.7 item 1 asks for two things this module keeps apart on purpose:

* **schema choice** -- which *kind* of tactic to try next.  That is the only
  graded decision, and it is what a ranking arm (arbitrary, frequency,
  syntax-aware, learned) owns.
* **tactic-argument generation** -- turning a chosen schema into concrete
  tactic text (``intro P Q h``, ``exact h.right``, ``clear h``).  That is a
  closed form computed from the rendered proof state, never learned and never
  varied between arms.  Every arm receives the *same* candidate set for a
  state and may only permute it by schema.

Consequences that make the comparison honest:

* an arm cannot win by being handed better arguments;
* within one schema the candidate order is fixed by this module, so a
  reported win is a schema-ordering win;
* Lean remains the sole transition authority -- nothing here decides whether a
  tactic *works*, only whether it is worth proposing.

Rendered-state parsing is deliberately narrow and fail-soft.  Pantograph
renders the *unelaborated* source text for a fresh goal
(``\\n⊢ forall (P Q : Prop) (h : P /\\\\ Q), Q /\\\\ P``) and the elaborated
pretty-printed form afterwards (``P : Prop\\n…\\n⊢ Q ∧ P``), so ASCII and
Unicode spellings are normalized to one vocabulary before anything is read.
Multi-goal states are rendered as consecutive ``case`` blocks; only the FIRST
goal is read, because ``goal_tactic`` applies to goal 0.  Goals are assumed to
render on one line -- true for every theorem in ``theorems_v1.json`` and
asserted by the theorem-set loader rather than hoped for.
"""

from __future__ import annotations

from dataclasses import dataclass


TURNSTILE = "⊢"
AND = "∧"
OR = "∨"
ARROW = "→"
FORALL = "∀"
INACCESSIBLE = "✝"

#: The bounded schema vocabulary.  This is exactly the v0.6 checkpoint's
#: vocabulary, in exactly its order, so the released tactic-policy asset can
#: rank the new families without retraining.  ``ARBITRARY_ORDER`` below is this
#: tuple: an unmotivated declaration order that leads with the known dead
#: branch, which is what makes it the arbitrary control.
SCHEMAS = (
    "clear",
    "intro",
    "constructor",
    "assumption",
    "projection",
    "left",
    "right",
    "trivial",
)
ARBITRARY_ORDER = SCHEMAS

_ASCII_REPLACEMENTS = (
    ("/\\", AND),
    ("\\/", OR),
    ("->", ARROW),
    ("forall", FORALL),
)


def normalize(text: str) -> str:
    """One vocabulary for the ASCII source form and the pretty-printed form."""
    for ascii_form, unicode_form in _ASCII_REPLACEMENTS:
        text = text.replace(ascii_form, unicode_form)
    return text


@dataclass(frozen=True)
class Hypothesis:
    name: str
    type_text: str

    @property
    def accessible(self) -> bool:
        """Bare ``intro`` mints names Lean will not let a tactic mention.

        v0.6's first live run failed exactly here: ``h.left`` against an
        ``h✝`` binder is ``Unknown identifier``.  Generating arguments over
        inaccessible names would spend the proposal budget on transitions that
        can never succeed, so they are filtered at the source.
        """
        return INACCESSIBLE not in self.name


@dataclass(frozen=True)
class Goal:
    """The first goal of a rendered proof state, in normalized spelling."""

    hypotheses: tuple[Hypothesis, ...]
    conclusion: str
    case_label: str | None = None

    @property
    def accessible(self) -> tuple[Hypothesis, ...]:
        return tuple(item for item in self.hypotheses if item.accessible)


def _split_top(text: str, operator: str) -> list[str]:
    """Split on ``operator`` at parenthesis depth zero."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for character in text:
        if character in "([{":
            depth += 1
        elif character in ")]}":
            # max(0, ...): an unbalanced closer must not drive the depth
            # negative, because a negative depth would silently disable every
            # remaining top-level split and turn a parse failure into a wrong
            # answer.  Fail soft, not silently wrong.
            depth = max(0, depth - 1)
        if depth == 0 and character == operator:
            parts.append("".join(current).strip())
            current = []
            continue
        current.append(character)
    parts.append("".join(current).strip())
    return parts


def _strip_outer_parens(text: str) -> str:
    text = text.strip()
    while text.startswith("(") and text.endswith(")"):
        depth = 0
        for index, character in enumerate(text):
            if character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
                if depth == 0 and index != len(text) - 1:
                    return text
        text = text[1:-1].strip()
    return text


def parse_state(rendered: str) -> Goal | None:
    """Read the FIRST goal out of a rendered Pantograph proof state."""
    if not rendered.strip():
        return None
    lines = normalize(rendered).split("\n")
    case_label: str | None = None
    hypotheses: list[Hypothesis] = []
    for index, line in enumerate(lines):
        if line.startswith(TURNSTILE):
            return Goal(
                tuple(hypotheses),
                _strip_outer_parens(line[len(TURNSTILE):].strip()),
                case_label,
            )
        stripped = line.strip()
        if not stripped:
            continue
        names, separator, type_text = stripped.partition(" : ")
        # A goal-block header, not a hypothesis.  The ``" : "`` test comes
        # FIRST so that a binder legitimately named ``case`` (``case : Prop``)
        # is read as a hypothesis rather than swallowed as a block header --
        # the reverse order silently dropped it.
        if not separator and stripped.startswith("case "):
            if index == 0:
                case_label = stripped[len("case "):]
                continue
            break
        if not separator:
            continue
        for name in names.split():
            hypotheses.append(Hypothesis(name, type_text.strip()))
    return None


def _universal_binders(conclusion: str) -> tuple[tuple[str, ...], str]:
    """Declared names of the leading ``∀`` groups, and the body after them."""
    rest = conclusion
    names: list[str] = []
    while rest.startswith(FORALL):
        rest = rest[len(FORALL):].strip()
        consumed = False
        while rest.startswith("("):
            depth = 0
            close = -1
            for index, character in enumerate(rest):
                if character == "(":
                    depth += 1
                elif character == ")":
                    depth -= 1
                    if depth == 0:
                        close = index
                        break
            if close < 0:
                return tuple(names), rest
            group = rest[1:close]
            declared, separator, _ = group.partition(" : ")
            if separator:
                names.extend(declared.split())
            rest = rest[close + 1:].strip()
            consumed = True
        if not consumed:
            # ``∀ a b, body`` -- undecorated binder names.
            head, separator, tail = rest.partition(",")
            if not separator:
                return tuple(names), rest
            names.extend(head.split())
            rest = tail.strip()
            break
        if rest.startswith(","):
            rest = rest[1:].strip()
        else:
            break
    return tuple(names), _strip_outer_parens(rest)


def leading_binder_names(goal: Goal) -> tuple[str, ...]:
    """Names ``intro`` would need to bind every leading binder accessibly.

    Universals contribute their declared names; bare arrows have none, so a
    deterministic fresh name (``h1``, ``h2``, ...) is minted, skipping any
    name already visible in the context or already minted here.  This is the
    argument generator, not a policy: which schema to try is decided
    elsewhere, and this function only says what ``intro`` would have to say.
    """
    names_tuple, body = _universal_binders(goal.conclusion)
    names = list(names_tuple)
    arrows = len(_split_top(body, ARROW)) - 1
    taken = {item.name for item in goal.hypotheses} | set(names)
    counter = 1
    for _ in range(arrows):
        while f"h{counter}" in taken:
            counter += 1
        names.append(f"h{counter}")
        taken.add(f"h{counter}")
    return tuple(names[:6])


def conjuncts(type_text: str) -> tuple[str, ...]:
    """Top-level conjuncts of a normalized type, right-associated."""
    return tuple(_split_top(_strip_outer_parens(type_text), AND))


def projection_paths(type_text: str, depth: int = 2) -> tuple[tuple[str, str], ...]:
    """``(dotted path, reached type)`` pairs for a conjunctive hypothesis."""
    found: list[tuple[str, str]] = []

    def walk(text: str, path: str, level: int) -> None:
        if level > depth:
            return
        parts = conjuncts(text)
        if len(parts) < 2:
            return
        left = parts[0]
        right = AND.join(parts[1:]).strip()
        for suffix, reached in ((".left", left), (".right", right)):
            found.append((path + suffix, _strip_outer_parens(reached)))
            walk(_strip_outer_parens(reached), path + suffix, level + 1)

    walk(_strip_outer_parens(type_text), "", 1)
    return tuple(found)


SORTS = frozenset({"Prop", "Type", "Sort"})


def projectable(type_text: str) -> bool:
    """May ``h.left`` even be worth *asking* Lean about?

    A bare variable (``P``) or a sort binder never has projections.  A
    compound application might: ``P ∧ Q`` visibly, and an imported
    abbreviation like ``ProofCurve.Both P Q`` invisibly -- Lean's pretty
    printer does NOT unfold the abbreviation, so no amount of syntax reading
    reveals the conjunction.  Being permissive here is the honest choice:
    proposing is cheap and *Lean*, not this module, decides whether the
    projection exists.
    """
    text = _strip_outer_parens(type_text)
    return text not in SORTS and " " in text


def projection_candidates(hypothesis: Hypothesis) -> tuple[str, ...]:
    """Concrete ``exact h.<path>`` text for one hypothesis, fixed order."""
    if not projectable(hypothesis.type_text):
        return ()
    paths = [path for path, _ in projection_paths(hypothesis.type_text)]
    if not paths:
        # Opaque compound (project abbreviation, unfamiliar constant): offer
        # the two structure fields and let Lean refuse them if wrong.
        paths = [".left", ".right"]
    return tuple(f"exact {hypothesis.name}{path}" for path in paths)


def goal_shape(goal: Goal | None) -> str:
    """A coarse, arm-independent signature for the current conclusion.

    Used to fingerprint dead branches so a branch that died on one theorem is
    recognizable on another.  Deliberately coarse: it names the top-level
    structure only, because that is the granularity at which "this schema is
    hopeless here" transfers between theorems.
    """
    if goal is None:
        return "none"
    conclusion = goal.conclusion
    if conclusion.startswith(FORALL):
        return "forall"
    if len(_split_top(conclusion, ARROW)) > 1:
        return "arrow"
    if len(_split_top(conclusion, AND)) > 1:
        return "and"
    if len(_split_top(conclusion, OR)) > 1:
        return "or"
    if conclusion == "True":
        return "true"
    return "atom"


def action_schema(tactic: str) -> str:
    """Map concrete tactic text back to its schema.  Fail closed."""
    if tactic.startswith("clear "):
        return "clear"
    if tactic == "intro" or tactic.startswith("intro "):
        return "intro"
    if tactic == "constructor":
        return "constructor"
    if tactic == "assumption":
        return "assumption"
    if tactic.startswith("exact "):
        return "projection"
    if tactic in {"left", "right", "trivial"}:
        return tactic
    raise ValueError(f"unregistered tactic schema: {tactic!r}")


def extraction_schema(tactic: str) -> str | None:
    """Map one row of the committed Lean extraction to a schema, fail-closed.

    Byte-for-byte the rule ``experiments/train_tactic_policy.tactic_schema``
    used in v0.6, restated here so ``prover/`` does not import the training
    script (and its torch dependency) merely to rebuild a count.  It must not
    drift: the frequency arm is only v0.6's *winner* if it is computed from
    the same rows under the same mapping, and
    ``tests/test_proof_curve.py`` pins the two implementations equal.
    """
    lines = [line.strip() for line in tactic.splitlines() if line.strip()]
    if len(lines) != 1:
        return None
    line = lines[0]
    if line.startswith("· "):
        line = line[2:].strip()
    if line.startswith("intro ") or line == "intro":
        return "intro"
    if line == "constructor":
        return "constructor"
    if line == "assumption":
        return "assumption"
    if line.startswith("exact ") and any(
        marker in line for marker in (".left", ".right", ".1", ".2")
    ):
        return "projection"
    if line in {"left", "right", "trivial"}:
        return line
    if line.startswith("clear "):
        return "clear"
    return None


def candidates(goal: Goal | None) -> dict[str, tuple[str, ...]]:
    """Concrete tactic text per schema, in a FIXED within-schema order.

    Every ranking arm gets this identical mapping; arms differ only in the
    order they visit the keys.
    """
    if goal is None:
        return {schema: () for schema in SCHEMAS}
    names = leading_binder_names(goal)
    intro: list[str] = []
    if names:
        intro.append("intro " + " ".join(names))
    intro.append("intro")

    projections: list[str] = []
    for hypothesis in goal.accessible:
        projections.extend(projection_candidates(hypothesis))
    # ``clear`` targets proof hypotheses, never the sort binders other
    # hypotheses depend on: clearing ``P : Prop`` is refused by Lean for a
    # structural reason no ranking can learn from.
    clears = [
        f"clear {hypothesis.name}"
        for hypothesis in goal.accessible
        if _strip_outer_parens(hypothesis.type_text) not in SORTS
    ]
    return {
        "clear": tuple(clears[:4]),
        "intro": tuple(intro),
        "constructor": ("constructor",),
        "assumption": ("assumption",),
        "projection": tuple(projections[:8]),
        "left": ("left",),
        "right": ("right",),
        "trivial": ("trivial",),
    }


def syntax_order(goal: Goal | None) -> tuple[str, ...]:
    """The syntax-aware capability-BLIND order: closed-form, no weights.

    This is the strong baseline v0.6's verdict demands.  Every rule below is
    a fact about the rendered conclusion or context, computed exactly:

    * a goal under a binder wants ``intro``;
    * a conjunctive goal wants ``constructor``;
    * a disjunctive goal wants ``left``/``right``;
    * ``True`` wants ``trivial``;
    * a goal that IS a hypothesis wants ``assumption``;
    * a goal that is a conjunct of a hypothesis wants ``projection``;
    * ``clear`` is never preferred -- it is the registered dead branch.

    Ties break on :data:`ARBITRARY_ORDER`, so the syntax arm degrades to the
    arbitrary arm exactly where syntax says nothing.
    """
    scores = {schema: 0.0 for schema in SCHEMAS}
    if goal is not None:
        conclusion = goal.conclusion
        universals, body = _universal_binders(conclusion)
        under_binder = bool(universals) or len(_split_top(body, ARROW)) > 1
        if under_binder:
            # Nothing about the *body* is actionable yet: its connectives sit
            # behind binders Lean has not introduced.  Only ``intro`` earns a
            # boost, and everything else falls back to the arbitrary tie-break.
            scores["intro"] = 4.0
        else:
            if len(_split_top(conclusion, AND)) > 1:
                scores["constructor"] = 4.0
            if len(_split_top(conclusion, OR)) > 1:
                scores["left"] = 3.0
                scores["right"] = 2.9
            if conclusion == "True":
                scores["trivial"] = 4.0
            types = [item.type_text for item in goal.accessible]
            if any(_strip_outer_parens(text) == conclusion for text in types):
                scores["assumption"] = 5.0
            reachable = any(
                _strip_outer_parens(reached) == conclusion
                for text in types
                for _, reached in projection_paths(text)
            )
            if reachable:
                scores["projection"] = 5.0
            elif any(len(conjuncts(text)) > 1 for text in types):
                scores["projection"] = 1.0
    scores["clear"] = -1.0
    return tuple(
        schema
        for schema in sorted(
            SCHEMAS,
            key=lambda name: (-scores[name], ARBITRARY_ORDER.index(name)),
        )
    )


def frequency_order(counts: dict[str, int]) -> tuple[str, ...]:
    """One global, state-BLIND order from training-corpus schema counts."""
    return tuple(
        sorted(
            SCHEMAS,
            key=lambda name: (-counts.get(name, 0), ARBITRARY_ORDER.index(name)),
        )
    )
