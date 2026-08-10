"""Step 4: the exact incidence / length / right-angle verifier.

Six gated checks decide the verdict. Two further checks are implemented and
deliberately *not* gated, because a check that cannot be shown load-bearing
is decoration and inflates the inventory without adding evidence:

- ``pythagorean`` (``|hyp|^2 == |leg_a|^2 + |leg_b|^2``) is implied by
  ``right_angle`` plus ``incidence``;
- ``hypotenuse_claim`` (``|hyp|^2 == claim.a_sq + claim.b_sq``) is implied by
  those plus ``leg_lengths``.

Both are true of every valid figure and both are redundant, so gating them
would give two invalid classes a second detector and destroy the ablation
argument for the checks that actually earn their place. They are kept behind
``derived=True`` so that redundancy is *demonstrated* on the whole corpus
(P-VO6) rather than claimed in a comment.

Independence discipline: every check is evaluable on its own. No check
assumes an earlier one passed, and a check that cannot evaluate a relation
(an unresolvable reference, a missing role) reports nothing rather than
borrowing another check's failure. Without that rule an ablation would be
meaningless -- disabling one check would silently mute another.

All arithmetic is exact rational arithmetic on ``Fraction`` coordinates.
There is no tolerance parameter anywhere in this file, so "accepts" and
"rejects" mean what they say.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from .scene import (A_RIGHT, Claim, SceneGraph, check_wellformed, fmt)

GATED_CHECKS = ("incidence", "topology", "right_angle", "leg_lengths",
                "nondegenerate", "right_angle_slot")
DERIVED_CHECKS = ("pythagorean", "hypotenuse_claim")

# Which gated checks imply each derived check. This is the specific claim
# behind excluding them from the gate, so it is the specific claim the tests
# check: "some gate also failed" would be satisfied by an unrelated check and
# would not show that the derived one is implied.
DERIVED_IMPLIED_BY = {
    "pythagorean": ("right_angle", "incidence"),
    "hypotenuse_claim": ("right_angle", "incidence", "leg_lengths"),
}


@dataclass(frozen=True)
class Failure:
    check: str
    elements: tuple[str, ...]
    detail: str

    def to_dict(self) -> dict:
        return {"check": self.check, "elements": list(self.elements),
                "detail": self.detail}


@dataclass(frozen=True)
class Result:
    ok: bool
    failures: tuple[Failure, ...]

    @property
    def failed_checks(self) -> tuple[str, ...]:
        seen: list[str] = []
        for f in self.failures:
            if f.check not in seen:
                seen.append(f.check)
        return tuple(seen)

    def to_dict(self) -> dict:
        return {"ok": self.ok,
                "failed_checks": list(self.failed_checks),
                "failures": [f.to_dict() for f in self.failures]}


# --------------------------------------------------------------------------
# Gated checks
# --------------------------------------------------------------------------

def _check_incidence(g: SceneGraph, claim: Claim) -> list[Failure]:
    """Every edge endpoint sits exactly on the vertex the edge names.

    Unresolvable references cannot reach here -- ``check_wellformed``
    refuses them at the door -- so the guard below is unreachable rather
    than a silent skip. That matters for the ablation: a check that quietly
    declined to evaluate could make a neighbouring check look load-bearing
    when it was only covering for this one.
    """
    out: list[Failure] = []
    for e in g.edges:
        for ref, point, end in ((e.frm, e.p1, "start"), (e.to, e.p2, "end")):
            v = g.vertex(ref)
            if v is None:
                continue
            if v.point != point:
                out.append(Failure(
                    "incidence", (e.id, ref),
                    f"{e.id} {end} ({fmt(point.x)},{fmt(point.y)}) is not on "
                    f"{ref} ({fmt(v.point.x)},{fmt(v.point.y)})"))
    return out


def _check_topology(g: SceneGraph, claim: Claim) -> list[Failure]:
    """The three edges join the three required vertex pairs, once each."""
    out: list[Failure] = []
    for e in g.edges:
        for ref in (e.frm, e.to):
            if g.vertex(ref) is None:
                out.append(Failure("topology", (e.id, ref),
                                   f"{e.id} references unknown vertex {ref}"))
    roles = {v.id: v.role for v in g.vertices}
    required = {"leg_a": frozenset({"right_angle", "leg_a_end"}),
                "leg_b": frozenset({"right_angle", "leg_b_end"}),
                "hypotenuse": frozenset({"leg_a_end", "leg_b_end"})}
    for e in g.edges:
        want = required.get(e.role)
        if want is None:
            out.append(Failure("topology", (e.id,),
                               f"{e.id} has unknown edge role {e.role!r}"))
            continue
        got = frozenset({roles.get(e.frm, "?"), roles.get(e.to, "?")})
        if got != want:
            out.append(Failure(
                "topology", (e.id, e.frm, e.to),
                f"{e.id} ({e.role}) joins {sorted(got)}, expected "
                f"{sorted(want)}"))
    pairs = [frozenset({e.frm, e.to}) for e in g.edges]
    for i, pr in enumerate(pairs):
        if pairs.index(pr) != i:
            out.append(Failure("topology", (g.edges[i].id,),
                               f"{g.edges[i].id} duplicates an existing edge "
                               f"between {sorted(pr)}"))
    for v in g.vertices:
        deg = sum(1 for e in g.edges if v.id in (e.frm, e.to))
        if deg != 2:
            out.append(Failure("topology", (v.id,),
                               f"{v.id} has degree {deg}, expected 2"))
    return out


def _check_right_angle(g: SceneGraph, claim: Claim) -> list[Failure]:
    """The legs meet at exactly a right angle at the right-angle vertex.

    Role-addressed on purpose. Whether the figure's *annotation* points at
    that vertex is a separate claim owned by ``right_angle_slot``; keeping
    them apart is what makes both separately ablatable.
    """
    r = g.by_vertex_role("right_angle")
    a = g.by_vertex_role("leg_a_end")
    b = g.by_vertex_role("leg_b_end")
    if r is None or a is None or b is None:
        return []
    dot = (a.point - r.point).dot(b.point - r.point)
    if dot != 0:
        return [Failure("right_angle", (r.id, a.id, b.id),
                        f"dot((leg_a),(leg_b)) = {fmt(dot)}, expected 0")]
    return []


def _check_leg_lengths(g: SceneGraph, claim: Claim) -> list[Failure]:
    """Both legs have exactly the squared lengths the claim asserts."""
    r = g.by_vertex_role("right_angle")
    out: list[Failure] = []
    for role, want in (("leg_a_end", claim.leg_a_sq),
                       ("leg_b_end", claim.leg_b_sq)):
        v = g.by_vertex_role(role)
        if r is None or v is None:
            continue
        got = (v.point - r.point).norm_sq()
        if got != want:
            out.append(Failure("leg_lengths", (r.id, v.id),
                               f"|{v.id}-{r.id}|^2 = {fmt(got)}, claimed "
                               f"{fmt(want)}"))
    return out


def _check_nondegenerate(g: SceneGraph, claim: Claim) -> list[Failure]:
    """A right angle between a leg and nothing is still not a triangle."""
    out: list[Failure] = []
    for e in g.edges:
        if e.p1 == e.p2:
            out.append(Failure("nondegenerate", (e.id,),
                               f"{e.id} has zero length"))
    pts = {v.point for v in g.vertices}
    if len(pts) != len(g.vertices):
        out.append(Failure("nondegenerate",
                           tuple(v.id for v in g.vertices),
                           "two vertices occupy the same point"))
    r = g.by_vertex_role("right_angle")
    a = g.by_vertex_role("leg_a_end")
    b = g.by_vertex_role("leg_b_end")
    if r is not None and a is not None and b is not None:
        cross = (a.point - r.point).cross(b.point - r.point)
        if cross == 0:
            out.append(Failure("nondegenerate", (r.id, a.id, b.id),
                               "the three vertices are collinear "
                               "(cross product 0)"))
    return out


def _check_right_angle_slot(g: SceneGraph, claim: Claim) -> list[Failure]:
    """The right-angle annotation binds the slot it claims to bind.

    This is the slot-to-element alignment step 6's model must produce, so it
    is checked as its own relation. Only the right-angle annotation is
    audited here; the acute annotations carry no assertion that the geometry
    checks do not already own.
    """
    out: list[Failure] = []
    rights = [a for a in g.angles if a.measure == "right"]
    if len(rights) != 1:
        return [Failure("right_angle_slot",
                        tuple(a.id for a in rights) or (A_RIGHT,),
                        f"expected exactly one right-angle annotation, found "
                        f"{len(rights)}")]
    ang = rights[0]
    if ang.id != A_RIGHT:
        out.append(Failure("right_angle_slot", (ang.id,),
                           f"right-angle annotation has id {ang.id}, expected "
                           f"{A_RIGHT}"))
    r = g.by_vertex_role("right_angle")
    if r is not None and ang.vertex != r.id:
        out.append(Failure("right_angle_slot", (ang.id, ang.vertex),
                           f"{ang.id} is bound to {ang.vertex}, but the "
                           f"right-angle vertex is {r.id}"))
    leg_a = g.by_edge_role("leg_a")
    leg_b = g.by_edge_role("leg_b")
    want = {e.id for e in (leg_a, leg_b) if e is not None}
    if set(ang.arms) != want:
        out.append(Failure("right_angle_slot", (ang.id, *ang.arms),
                           f"{ang.id} arms {sorted(ang.arms)}, expected "
                           f"{sorted(want)}"))
    for arm in ang.arms:
        e = g.edge(arm)
        if e is not None and ang.vertex not in (e.frm, e.to):
            out.append(Failure("right_angle_slot", (ang.id, arm),
                               f"arm {arm} is not incident to {ang.vertex}"))
    return out


# --------------------------------------------------------------------------
# Derived (implemented, deliberately not gated -- see the module docstring)
# --------------------------------------------------------------------------

def _check_pythagorean(g: SceneGraph, claim: Claim) -> list[Failure]:
    r = g.by_vertex_role("right_angle")
    a = g.by_vertex_role("leg_a_end")
    b = g.by_vertex_role("leg_b_end")
    if r is None or a is None or b is None:
        return []
    hyp = (b.point - a.point).norm_sq()
    legs = (a.point - r.point).norm_sq() + (b.point - r.point).norm_sq()
    if hyp != legs:
        return [Failure("pythagorean", (r.id, a.id, b.id),
                        f"|hyp|^2 = {fmt(hyp)}, legs sum to {fmt(legs)}")]
    return []


def _check_hypotenuse_claim(g: SceneGraph, claim: Claim) -> list[Failure]:
    a = g.by_vertex_role("leg_a_end")
    b = g.by_vertex_role("leg_b_end")
    if a is None or b is None:
        return []
    hyp = (b.point - a.point).norm_sq()
    want = claim.leg_a_sq + claim.leg_b_sq
    if hyp != want:
        return [Failure("hypotenuse_claim", (a.id, b.id),
                        f"|hyp|^2 = {fmt(hyp)}, claim implies {fmt(want)}")]
    return []


CHECK_FNS: dict[str, Callable[[SceneGraph, Claim], list[Failure]]] = {
    "incidence": _check_incidence,
    "topology": _check_topology,
    "right_angle": _check_right_angle,
    "leg_lengths": _check_leg_lengths,
    "nondegenerate": _check_nondegenerate,
    "right_angle_slot": _check_right_angle_slot,
    "pythagorean": _check_pythagorean,
    "hypotenuse_claim": _check_hypotenuse_claim,
}


def verify(g: SceneGraph, claim: Claim, disabled: Iterable[str] = (),
           derived: bool = False) -> Result:
    """Exact verdict on one scene graph against one claim.

    ``disabled`` is the ablation handle: it is a real capability removal, not
    a scoring flag. ``derived=True`` additionally runs the redundant checks,
    which must never change ``ok`` -- that invariance is P-VO6.

    Well-formedness is re-enforced here rather than trusted from
    construction time, and it *raises* instead of returning a verdict. A
    graph whose references do not resolve is not a figure that failed a
    geometric check; it is not a figure. Enforcing it at the verdict
    boundary is what makes "no check can be silently muted" a property of
    the code rather than a claim in a docstring: every check below either
    evaluates its relation or is never reached.
    """
    check_wellformed(g)
    off = set(disabled)
    unknown = off - set(GATED_CHECKS) - set(DERIVED_CHECKS)
    if unknown:
        raise ValueError(f"unknown check(s) to disable: {sorted(unknown)}")
    names = list(GATED_CHECKS) + (list(DERIVED_CHECKS) if derived else [])
    failures: list[Failure] = []
    for name in names:
        if name in off:
            continue
        failures.extend(CHECK_FNS[name](g, claim))
    return Result(not failures, tuple(failures))
