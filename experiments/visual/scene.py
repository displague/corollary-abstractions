"""Step 1-2: deterministic right-triangle parameters and the source scene
graph with stable slot-to-element identities.

Identity discipline: every element id is derived from its *role*, never from
its coordinates, its seed, or its position in a list. ``V.right`` is the
right-angle vertex of every figure this package will ever emit, whatever the
leg lengths, orientation, translation, or handedness. That is what makes a
slot pointable: step 6's model must answer "which element fills the
right-angle slot", and the answer is only checkable if the identity survives
parameter change.

Element geometry is stored twice on purpose. A vertex owns a point; an edge
owns *its own* two endpoints plus the ids of the vertices it claims to join.
Incidence is therefore a real, falsifiable relation (do the edge's endpoints
actually sit on the vertices it names?) rather than a tautology, and an SVG
``<line>`` -- which likewise carries its own coordinates -- round-trips into
it without inventing anything.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, replace
from fractions import Fraction
from math import atan2, degrees
from typing import Iterable

FAMILY = "right_triangle"

# Stable slot ids. Deliberately equal-length within each kind so that a
# byte-length surface baseline cannot separate a rebound reference from an
# original one (see P-VO7).
V_RIGHT = "V.right"
V_LEG_A = "V.leg_a"
V_LEG_B = "V.leg_b"
E_LEG_A = "E.leg_a"
E_LEG_B = "E.leg_b"
E_HYP = "E.hypot"
A_RIGHT = "A.right"
A_AT_A = "A.acu_a"
A_AT_B = "A.acu_b"

ROLE_TO_VERTEX = {"right_angle": V_RIGHT,
                  "leg_a_end": V_LEG_A,
                  "leg_b_end": V_LEG_B}
ROLE_TO_EDGE = {"leg_a": E_LEG_A, "leg_b": E_LEG_B, "hypotenuse": E_HYP}
ROLE_TO_ANGLE = {"right_angle": A_RIGHT,
                 "angle_at_a": A_AT_A,
                 "angle_at_b": A_AT_B}

ELEMENT_IDS = frozenset({V_RIGHT, V_LEG_A, V_LEG_B, E_LEG_A, E_LEG_B, E_HYP,
                         A_RIGHT, A_AT_A, A_AT_B})


class SceneGraphError(ValueError):
    """Structural malformation refused at the door.

    Not a verifier verdict: a graph that cannot be read is not a graph that
    failed a geometric check. Keeping these separate is what stops the
    verifier from claiming credit for catching nonsense it never evaluated.
    """


@dataclass(frozen=True, order=True)
class Pt:
    x: Fraction
    y: Fraction

    def __sub__(self, other: "Pt") -> "Vec":
        return Vec(self.x - other.x, self.y - other.y)

    def __add__(self, other: "Vec") -> "Pt":
        return Pt(self.x + other.x, self.y + other.y)


@dataclass(frozen=True, order=True)
class Vec:
    x: Fraction
    y: Fraction

    def __mul__(self, k) -> "Vec":
        k = Fraction(k)
        return Vec(self.x * k, self.y * k)

    def dot(self, other: "Vec") -> Fraction:
        return self.x * other.x + self.y * other.y

    def cross(self, other: "Vec") -> Fraction:
        return self.x * other.y - self.y * other.x

    def norm_sq(self) -> Fraction:
        return self.x * self.x + self.y * self.y


def pt(x, y) -> Pt:
    return Pt(Fraction(x), Fraction(y))


def fmt(v: Fraction) -> str:
    """Exact decimal text for a rational coordinate.

    Refuses anything that is not exactly representable as a terminating
    decimal, because an approximated coordinate would make the SVG round trip
    lossy and quietly turn an exact verifier into an approximate one.
    """
    v = Fraction(v)
    if v.denominator == 1:
        return str(v.numerator)
    d = v.denominator
    twos = fives = 0
    while d % 2 == 0:
        d //= 2
        twos += 1
    while d % 5 == 0:
        d //= 5
        fives += 1
    if d != 1:
        raise SceneGraphError(
            f"coordinate {v} is not a terminating decimal; SVG serialization "
            "would be lossy")
    places = max(twos, fives)
    scaled = v * (10 ** places)
    sign = "-" if scaled < 0 else ""
    digits = str(abs(scaled.numerator)).rjust(places + 1, "0")
    return f"{sign}{digits[:-places]}.{digits[-places:]}"


_DECIMAL = re.compile(r"^-?\d+(?:\.\d+)?$")


def num(text: str) -> Fraction:
    """Exact inverse of :func:`fmt` for SVG attribute text.

    Restricted to the grammar ``fmt`` can actually emit. ``Fraction`` alone
    would accept ``1/3`` and ``1e3``, which parse silently and then explode
    at render time far from the cause, and it raises bare ``ValueError`` on
    junk instead of the ``SceneGraphError`` the parser contract promises.
    """
    if not _DECIMAL.match(text.strip()):
        raise SceneGraphError(
            f"{text!r} is not a coordinate this renderer can emit "
            "(expected an exact decimal)")
    return Fraction(text.strip())


@dataclass(frozen=True)
class TriangleParams:
    """Seeded parameters of one figure.

    ``(p, q)`` is a primitive direction with ``p > q >= 1``. The leg
    directions are ``u = (p, q)`` and ``v = (-q, p)``; the registered
    near-miss direction is ``w = (q, p)``, which has the same squared length
    as ``v`` and makes an exact angle of ``2*atan(q/p)`` with it.
    """

    p: int
    q: int
    m: int
    n: int
    ox: int
    oy: int
    hand: int  # +1 or -1: which side of u the second leg lies on
    dih: int   # 0..3: exact multiple-of-90-degree rotation of the whole figure

    def validate(self) -> None:
        """Enforce the contract the ablation depends on.

        Not defensive style: these are the conditions under which each
        controlled invalid trips exactly one check. With ``p == q`` the
        near-miss direction ``w = (q, p)`` becomes parallel to ``u``, so the
        right-angle break also collapses the triangle and fires
        ``nondegenerate`` alongside ``right_angle``; with ``m`` or ``n`` zero
        the *valid* figure is already degenerate. Either would quietly turn
        the one-class-one-check matrix off-diagonal and vacate P-VO3, so an
        out-of-contract figure must fail loudly instead of scoring.
        """
        if not (self.p > self.q >= 1):
            raise SceneGraphError(
                f"direction must satisfy p > q >= 1, got ({self.p}, {self.q}):"
                " the equal-length near-miss would be collinear with leg a")
        if self.m < 1 or self.n < 1:
            raise SceneGraphError(
                f"leg units must be positive, got m={self.m}, n={self.n}")
        if self.hand not in (1, -1):
            raise SceneGraphError(f"hand must be +/-1, got {self.hand}")

    def signature(self) -> str:
        return (f"p{self.p}q{self.q}m{self.m}n{self.n}"
                f"o{self.ox},{self.oy}h{self.hand}d{self.dih}")

    @property
    def epsilon_degrees(self) -> float:
        """Informational only. Never read by any check."""
        return degrees(2 * atan2(self.q, self.p))


def _rot90(v: Vec, times: int) -> Vec:
    for _ in range(times % 4):
        v = Vec(-v.y, v.x)
    return v


def leg_vectors(params: TriangleParams) -> tuple[Vec, Vec, Vec]:
    """Return ``(leg_a, leg_b, leg_b_near_miss)`` as exact vectors.

    ``leg_b_near_miss`` has the same squared length as ``leg_b`` and a
    non-zero dot product with ``leg_a``; it is the only length-preserving way
    to break the right angle in exact rational arithmetic, and it is why the
    right-angle check can be ablated without the length check catching the
    escape for it.
    """
    params.validate()
    p, q = Fraction(params.p), Fraction(params.q)
    u = Vec(p, q)
    v = Vec(-q, p) * params.hand
    w = Vec(q, p) * params.hand
    d = params.dih
    return (_rot90(u, d) * params.m,
            _rot90(v, d) * params.n,
            _rot90(w, d) * params.n)


@dataclass(frozen=True)
class Claim:
    """The symbolic side of a formula/figure pair.

    Step 6 will present a formula and a diagram; the claim is what the
    formula asserts about the diagram's measurable slots. Hypotenuse length
    is deliberately absent: it is implied by the legs plus the right angle,
    and checking it would give the verifier a second detector for the same
    violation (see the derived-check discussion in ``verify``).
    """

    leg_a_sq: Fraction
    leg_b_sq: Fraction

    def to_dict(self) -> dict:
        return {"leg_a_sq": fmt(self.leg_a_sq), "leg_b_sq": fmt(self.leg_b_sq)}

    @staticmethod
    def from_dict(d: dict) -> "Claim":
        return Claim(num(d["leg_a_sq"]), num(d["leg_b_sq"]))


@dataclass(frozen=True)
class Vertex:
    id: str
    role: str
    point: Pt


@dataclass(frozen=True)
class Edge:
    id: str
    role: str
    frm: str
    to: str
    p1: Pt
    p2: Pt


@dataclass(frozen=True)
class Angle:
    id: str
    role: str
    vertex: str
    arms: tuple[str, str]
    measure: str  # "right" or "acute"


@dataclass(frozen=True)
class SceneGraph:
    figure_id: str
    family: str
    vertices: tuple[Vertex, ...]
    edges: tuple[Edge, ...]
    angles: tuple[Angle, ...]

    def vertex(self, vid: str) -> Vertex | None:
        for v in self.vertices:
            if v.id == vid:
                return v
        return None

    def edge(self, eid: str) -> Edge | None:
        for e in self.edges:
            if e.id == eid:
                return e
        return None

    def by_vertex_role(self, role: str) -> Vertex | None:
        for v in self.vertices:
            if v.role == role:
                return v
        return None

    def by_edge_role(self, role: str) -> Edge | None:
        for e in self.edges:
            if e.role == role:
                return e
        return None

    def points(self) -> Iterable[Pt]:
        for v in self.vertices:
            yield v.point
        for e in self.edges:
            yield e.p1
            yield e.p2

    # ``replace`` rather than ``changes.get(...)``: a typo'd keyword must
    # raise, not silently produce an unmutated graph that then "passes" a
    # test written to prove a mutation is caught.
    def with_vertex(self, vid: str, **changes) -> "SceneGraph":
        vs = tuple(replace(v, **changes) if v.id == vid else v
                   for v in self.vertices)
        return SceneGraph(self.figure_id, self.family, vs, self.edges,
                          self.angles)

    def with_edge(self, eid: str, **changes) -> "SceneGraph":
        es = tuple(replace(e, **changes) if e.id == eid else e
                   for e in self.edges)
        return SceneGraph(self.figure_id, self.family, self.vertices, es,
                          self.angles)

    def with_angle(self, aid: str, **changes) -> "SceneGraph":
        angs = tuple(replace(a, **changes) if a.id == aid else a
                     for a in self.angles)
        return SceneGraph(self.figure_id, self.family, self.vertices,
                          self.edges, angs)


def normalize(g: SceneGraph) -> SceneGraph:
    """Canonical form: elements sorted by id, nothing else touched.

    The parser produces exactly this, so ``parse_svg(render_svg(g)) ==
    normalize(g)`` is plain dataclass equality with no tolerance parameter.
    """
    return SceneGraph(
        g.figure_id, g.family,
        tuple(sorted(g.vertices, key=lambda v: v.id)),
        tuple(sorted(g.edges, key=lambda e: e.id)),
        tuple(sorted(g.angles, key=lambda a: a.id)),
    )


def check_wellformed(g: SceneGraph) -> None:
    """Refuse graphs that are not readable as scene graphs at all.

    This is not one of the gated checks and must never become one: no
    controlled-invalid class is malformed, and a check with no invalid class
    to catch would inflate the inventory without being load-bearing. It is a
    precondition, and it raises rather than returning a verdict.

    It is also what keeps the ablation honest. The verifier's checks are
    written to report nothing about a relation they cannot evaluate, so that
    disabling one check never silently mutes another. Resolving every
    reference here -- and, for the registered family, requiring the complete
    slot inventory -- makes each of those skip branches unreachable for a
    graph that got through the door: every check either evaluates its
    relation or the graph never reached the verifier at all.

    Reference resolution is a precondition and not a gated check for the
    same reason as the rest of this function: no controlled-invalid class is
    built from a dangling reference, and adding a seventh check with no
    class to catch would inflate the inventory without being load-bearing.
    It closes a real hole all the same -- before it, an angle pointing at a
    nonexistent vertex round-tripped through the SVG and verified ``ok``.
    """
    ids = [e.id for e in (*g.vertices, *g.edges, *g.angles)]
    if len(ids) != len(set(ids)):
        raise SceneGraphError(f"duplicate element ids in {g.figure_id}")
    if not g.vertices or not g.edges or not g.angles:
        raise SceneGraphError(f"empty element class in {g.figure_id}")
    vertex_ids = {v.id for v in g.vertices}
    edge_ids = {e.id for e in g.edges}
    for e in g.edges:
        for ref in (e.frm, e.to):
            if ref not in vertex_ids:
                raise SceneGraphError(
                    f"edge {e.id} references unknown vertex {ref!r}")
    for a in g.angles:
        if len(a.arms) != 2:
            raise SceneGraphError(f"angle {a.id} must name exactly two arms")
        if a.vertex not in vertex_ids:
            raise SceneGraphError(
                f"angle {a.id} references unknown vertex {a.vertex!r}")
        for arm in a.arms:
            if arm not in edge_ids:
                raise SceneGraphError(
                    f"angle {a.id} references unknown edge {arm!r}")
        if a.measure not in ("right", "acute"):
            raise SceneGraphError(
                f"angle {a.id} has unknown measure {a.measure!r}")
    if g.family != FAMILY:
        raise SceneGraphError(
            f"{g.figure_id}: unknown family {g.family!r}. Silently falling "
            "back to the generic checks would downgrade validation for a "
            "typo; a new family must arrive with its own slot registry.")
    if set(ids) != ELEMENT_IDS:
        raise SceneGraphError(
            f"{g.figure_id}: element ids {sorted(set(ids))} are not the "
            f"registered slot inventory {sorted(ELEMENT_IDS)}")
    for kind, elements, registry in (("vertex", g.vertices, ROLE_TO_VERTEX),
                                     ("edge", g.edges, ROLE_TO_EDGE),
                                     ("angle", g.angles, ROLE_TO_ANGLE)):
        got = {e.role: e.id for e in elements}
        if got != registry:
            raise SceneGraphError(
                f"{g.figure_id}: {kind} role map {got} does not match the "
                f"registered map {registry}")


def build_scene(params: TriangleParams, figure_id: str) -> SceneGraph:
    """Step 1-2: the pure function from parameters to the source graph.

    Deterministic, total, and free of randomness: the seeded generator draws
    parameters, and everything downstream of that draw is a function.
    """
    a_vec, b_vec, _ = leg_vectors(params)
    r = pt(params.ox, params.oy)
    a = r + a_vec
    b = r + b_vec
    vertices = (Vertex(V_RIGHT, "right_angle", r),
                Vertex(V_LEG_A, "leg_a_end", a),
                Vertex(V_LEG_B, "leg_b_end", b))
    edges = (Edge(E_LEG_A, "leg_a", V_RIGHT, V_LEG_A, r, a),
             Edge(E_LEG_B, "leg_b", V_RIGHT, V_LEG_B, r, b),
             Edge(E_HYP, "hypotenuse", V_LEG_A, V_LEG_B, a, b))
    angles = (Angle(A_RIGHT, "right_angle", V_RIGHT, (E_LEG_A, E_LEG_B),
                    "right"),
              Angle(A_AT_A, "angle_at_a", V_LEG_A, (E_LEG_A, E_HYP), "acute"),
              Angle(A_AT_B, "angle_at_b", V_LEG_B, (E_LEG_B, E_HYP), "acute"))
    g = normalize(SceneGraph(figure_id, FAMILY, vertices, edges, angles))
    check_wellformed(g)
    return g


def build_claim(params: TriangleParams) -> Claim:
    a_vec, b_vec, _ = leg_vectors(params)
    return Claim(a_vec.norm_sq(), b_vec.norm_sq())


# --------------------------------------------------------------------------
# JSON serialization (text only; no binary artifact ever leaves this package)
# --------------------------------------------------------------------------

def to_dict(g: SceneGraph) -> dict:
    return {
        "schema": "visual-scene/1",
        "figure_id": g.figure_id,
        "family": g.family,
        "vertices": [{"id": v.id, "role": v.role,
                      "x": fmt(v.point.x), "y": fmt(v.point.y)}
                     for v in g.vertices],
        "edges": [{"id": e.id, "role": e.role, "from": e.frm, "to": e.to,
                   "x1": fmt(e.p1.x), "y1": fmt(e.p1.y),
                   "x2": fmt(e.p2.x), "y2": fmt(e.p2.y)}
                  for e in g.edges],
        "angles": [{"id": a.id, "role": a.role, "vertex": a.vertex,
                    "arms": list(a.arms), "measure": a.measure}
                   for a in g.angles],
    }


def from_dict(d: dict) -> SceneGraph:
    if d.get("schema") != "visual-scene/1":
        raise SceneGraphError(f"unknown scene schema {d.get('schema')!r}")
    g = SceneGraph(
        d["figure_id"], d["family"],
        tuple(Vertex(v["id"], v["role"], Pt(num(v["x"]), num(v["y"])))
              for v in d["vertices"]),
        tuple(Edge(e["id"], e["role"], e["from"], e["to"],
                   Pt(num(e["x1"]), num(e["y1"])),
                   Pt(num(e["x2"]), num(e["y2"])))
              for e in d["edges"]),
        tuple(Angle(a["id"], a["role"], a["vertex"], tuple(a["arms"]),
                    a["measure"])
              for a in d["angles"]),
    )
    check_wellformed(g)
    return normalize(g)


def to_json(g: SceneGraph) -> str:
    return json.dumps(to_dict(g), indent=2, sort_keys=False) + "\n"
