#!/usr/bin/env python3
"""Apply `data/foreign_voice/rule_r.json` — the declared interpretation.

DESIGN-foreign-voice §3.2 makes rule R a **trusted, reviewed artifact with its
own digest, not inverter logic**.  This module is the applier and the load
gate, and it holds no policy of its own: every substitution, every frozen
constant and every step of the preamble rule is read out of the JSON file, so
a change in behaviour is a change in a digested artifact rather than a change
in code that the digest would not see.

Why the rule exists at all is Correction 3 of the design, restated in the file:
at Lean's defaults 680 of a 1,000-statement sample of the mute set
"elaborated cleanly"; with `autoImplicit false` and `relaxedAutoImplicit
false`, 1 of 1,000.  The difference is Lean auto-binding every unknown
identifier — including the type glyph, which becomes an auto-bound *type*
variable.  An oracle run at the defaults certifies round trips between two
elaborations of a proposition nobody wrote.  So autoImplicit is off, the
surface must carry an explicit binder preamble, and choosing binder types is
semantic work that belongs in a frozen file.

## The one thing this module must not become

R is applied **independently on each side** of the identity relation.  It never
sees the rendering, never sees the inverse table, and takes no argument that
could carry information from one side to the other.  A preamble mismatch is a
B1 failure, never a repair (design §3.2).  `apply(text)` therefore takes one
string and returns one string; there is deliberately no `apply(original,
roundtrip)` shape for a later caller to reach for.

## The measurement bug this module's settings exist to prevent

`harness_settings.maxErrors` is not decoration.  The pinned frontend stops
reporting after 100 errors, and a batch prober that infers acceptance from the
*absence* of an error reads everything after the hundredth error as accepted.
Measured on this tree, that reported **2,982 eligible where the truth is
2,319**.  `foreign_voice_eligibility.py` refuses a batch whose output carries
the cutoff line; the option that prevents it lives here because it is part of
the declared interpretation's operating conditions, not a harness detail.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_RULE_PATH = (
    Path(__file__).resolve().parent.parent / "data" / "foreign_voice" / "rule_r.json"
)

#: Every field the applier reads. A file missing one of these is refused rather
#: than defaulted, because a default is a policy this module is not allowed to
#: hold.
_REQUIRED = (
    "rule_id",
    "type_substitutions",
    "elaboration_settings",
    "harness_settings",
    "identifier_grammar",
    "binder_scan",
    "frozen_constants",
    "preamble_rule",
)

_IDENT_START = r"A-Za-z_α-ωΑ-Ω"
_IDENT_CONT = _IDENT_START + r"0-9'₀-₉ₐ-ₜ"
_IDENT_RE = re.compile(
    rf"[{_IDENT_START}][{_IDENT_CONT}]*(?:\.[{_IDENT_START}][{_IDENT_CONT}]*)*"
)


class RuleError(ValueError):
    """The rule file is malformed, or asks for something this applier cannot do."""


def _load_pairs(pairs: list[tuple[str, object]]) -> dict:
    seen: set[str] = set()
    out: dict[str, object] = {}
    for key, value in pairs:
        if key in seen:
            raise RuleError(f"duplicate key {key!r} in the rule file")
        seen.add(key)
        out[key] = value
    return out


@dataclass(frozen=True)
class RuleR:
    """A loaded, gated interpretation. Immutable; the file is the artifact."""

    path: Path
    rule_id: str
    type_substitutions: tuple[tuple[str, str], ...]
    auto_implicit: bool
    relaxed_auto_implicit: bool
    max_heartbeats: int
    max_errors: int
    binder_openers: tuple[str, ...]
    frozen_names: frozenset[str]
    preamble_type: str
    prop_branch: str

    # -- the rule itself ---------------------------------------------------

    def substitute(self, text: str) -> str:
        """Step 1: the type-glyph substitution, literal and order-independent."""
        for glyph, name in self.type_substitutions:
            text = text.replace(glyph, name)
        return text

    def bound_names(self, text: str) -> set[str]:
        """Step 2: every name any binder group mentions, LEXICALLY not scoped.

        The simplification is declared in the rule file and its consequence is
        that a genuinely-free identifier sharing a spelling with a binder
        elsewhere in the statement is left unbound — so the oracle rejects it
        as unknown rather than the preamble silently reinterpreting it.
        Rejection costs coverage; it cannot invent a proposition.
        """
        bound: set[str] = set()
        for match in self._binder_re.finditer(text):
            bound.update(match.group(1).split())
        return bound

    def free_names(self, text: str) -> list[str]:
        """Steps 3–4: the sorted, deduplicated free identifiers."""
        bound = self.bound_names(text)
        free: set[str] = set()
        for match in _IDENT_RE.finditer(text):
            name = match.group(0)
            if "." in name or name in self.frozen_names or name in bound:
                continue
            free.add(name)
        return sorted(free)

    def apply(self, source: str) -> "Interpretation":
        """R(s). One string in, one string out — see the module docstring."""
        body = self.substitute(source)
        free = self.free_names(body)
        if free:
            text = f"∀ {' '.join(free)} : {self.preamble_type}, {body}"
        else:
            text = body
        shifts = tuple(
            f"{glyph}→{name}"
            for glyph, name in self.type_substitutions
            if glyph in source
        )
        return Interpretation(
            rule_id=self.rule_id,
            source=source,
            text=text,
            preamble_binders=tuple(free),
            preamble_type=self.preamble_type,
            interpretation_shift=shifts,
        )

    # -- what the harness must emit around it ------------------------------

    def set_option_lines(self) -> tuple[str, ...]:
        """The semantic settings, as source lines, inside the digested bytes.

        B5 asserts these as *committed settings* rather than leaving them to a
        flag, which is why they are text in the file the binary reads.
        """
        return (
            f"set_option autoImplicit {str(self.auto_implicit).lower()}",
            f"set_option relaxedAutoImplicit "
            f"{str(self.relaxed_auto_implicit).lower()}",
            f"set_option maxHeartbeats {self.max_heartbeats}",
        )

    def command_line_options(self) -> tuple[str, ...]:
        """The frontend options that must be passed to the binary itself.

        `set_option maxErrors` inside the file does not take effect — the
        frontend reads it before elaborating — so this is the only form that
        works, and without it a batch prober silently over-counts acceptance.
        """
        return (f"-DmaxErrors={self.max_errors}",)

    @property
    def _binder_re(self) -> re.Pattern[str]:
        openers = "".join(re.escape(o) for o in self.binder_openers)
        return re.compile(
            rf"[{openers}]!?\s*\(?\s*((?:[{_IDENT_START}][{_IDENT_CONT}]*\s+)*"
            rf"[{_IDENT_START}][{_IDENT_CONT}]*)"
        )


@dataclass(frozen=True)
class Interpretation:
    """R(s) with the shift it applied, for the receipt's `interpretation_shift`."""

    rule_id: str
    source: str
    text: str
    preamble_binders: tuple[str, ...]
    preamble_type: str
    interpretation_shift: tuple[str, ...]


def load(path: Path | str | None = None) -> RuleR:
    """Read, gate and return the interpretation. Raises `RuleError`."""
    path = Path(path) if path is not None else DEFAULT_RULE_PATH
    raw = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_load_pairs)
    return build(raw, path)


def build(raw: dict, path: Path | str = "<memory>") -> RuleR:
    """Gate an already-parsed rule. Split from `load` so tests can inject."""
    path = Path(path) if not isinstance(path, str) else Path(path)

    for field in _REQUIRED:
        if field not in raw:
            raise RuleError(f"missing required field {field!r}")

    subs = raw["type_substitutions"]
    if not isinstance(subs, dict) or not subs:
        raise RuleError("`type_substitutions` must be a non-empty object")
    for glyph, name in subs.items():
        if len(glyph) != 1:
            raise RuleError(
                f"type substitution key {glyph!r} is not a single character; the "
                f"rule file declares the substitution order-independent, which "
                f"only holds for single characters"
            )
        if not isinstance(name, str) or not _IDENT_RE.fullmatch(name):
            raise RuleError(f"type substitution {glyph!r} -> {name!r} is not an identifier")
    # Order-independence is a claim the file makes; check it rather than trust it.
    for glyph in subs:
        for other, name in subs.items():
            if glyph in name:
                raise RuleError(
                    f"substitution {other!r} -> {name!r} reintroduces the key "
                    f"{glyph!r}; the substitution would not be idempotent"
                )

    settings = raw["elaboration_settings"]
    for key in ("autoImplicit", "relaxedAutoImplicit"):
        if settings.get(key) is not False:
            raise RuleError(
                f"`elaboration_settings.{key}` must be false. Correction 3 of the "
                f"design measured what happens otherwise: 680 of 1,000 mute "
                f"statements 'elaborate cleanly' at Lean's defaults because every "
                f"unknown identifier — the type glyph included — is auto-bound."
            )

    harness = raw["harness_settings"]
    for key in ("maxHeartbeats", "maxErrors"):
        value = harness.get(key)
        if not isinstance(value, int) or value <= 0:
            raise RuleError(f"`harness_settings.{key}` must be a positive integer")

    scan = raw["binder_scan"]
    openers = scan.get("openers")
    if not isinstance(openers, list) or not openers:
        raise RuleError("`binder_scan.openers` must be a non-empty list")

    frozen = raw["frozen_constants"]
    names = frozen.get("names")
    if not isinstance(names, list) or not names:
        raise RuleError("`frozen_constants.names` must be a non-empty list")
    if list(names) != sorted(names):
        raise RuleError("`frozen_constants.names` must be sorted, so a diff is readable")
    if len(set(names)) != len(names):
        raise RuleError("`frozen_constants.names` repeats a name")
    for name in names:
        if "." in name:
            raise RuleError(
                f"frozen constant {name!r} is qualified; qualified names are "
                f"covered by the rule, and listing one implies the rule is not "
                f"doing its job"
            )
    missing = set(subs.values()) - set(names)
    if missing:
        raise RuleError(
            f"the substitution produces {sorted(missing)}, which the preamble "
            f"would then bind and shadow; they must be frozen constants"
        )

    preamble = raw["preamble_rule"]
    ptype = preamble.get("preamble_type")
    if ptype not in set(subs.values()):
        raise RuleError(
            f"`preamble_rule.preamble_type` is {ptype!r}, which is not one of the "
            f"types this rule substitutes to ({sorted(set(subs.values()))}); a "
            f"preamble type the interpretation never mentions is a third reading "
            f"nobody declared"
        )

    branch = (raw.get("prop_branch") or {}).get("decision")
    if branch not in {"branch_i", "branch_ii"}:
        raise RuleError(
            "`prop_branch.decision` must be `branch_i` or `branch_ii`. The design "
            "requires the branch to be chosen at B0 time and recorded; an absent "
            "decision is the one thing the clause forbids."
        )

    return RuleR(
        path=path,
        rule_id=raw["rule_id"],
        type_substitutions=tuple(subs.items()),
        auto_implicit=False,
        relaxed_auto_implicit=False,
        max_heartbeats=harness["maxHeartbeats"],
        max_errors=harness["maxErrors"],
        binder_openers=tuple(openers),
        frozen_names=frozenset(names),
        preamble_type=ptype,
        prop_branch=branch,
    )


__all__ = ["Interpretation", "RuleError", "RuleR", "DEFAULT_RULE_PATH", "build", "load"]
