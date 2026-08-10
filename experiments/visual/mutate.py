"""Step 3: controlled-invalid pair generation.

Each valid figure yields one near-miss per class. "Near-miss" is a design
constraint, not a description: every mutation preserves the element count,
the id set, the family, and (for four of six classes) every byte of the
figure's coordinate magnitudes, so that a step-6 arm cannot separate the
classes by counting anything. That is the capability-blind control being
built into the data rather than discovered after the fact.

The classes are chosen so that each one is caught by exactly one verifier
check. That diagonal is the whole point: it is what lets the ablation in
``verify`` prove that every check is load-bearing instead of asserting it.
A mutation that tripped two checks would make one of them unfalsifiable.

Each mutation records what it did, which elements it touched, and which
check is registered to catch it. The record is the future
capability-blind control and the future "point at the violated relation"
supervision signal, so it is metadata on the pair, never anything the
verifier is allowed to read.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .scene import (A_RIGHT, Claim, E_HYP, E_LEG_A, E_LEG_B, Pt, SceneGraph,
                    SceneGraphError, TriangleParams, V_LEG_A, V_LEG_B,
                    V_RIGHT, Vec, build_claim, build_scene, fmt, leg_vectors)

INVALID_CLASSES = (
    "right_angle_epsilon",
    "leg_length",
    "edge_disconnected",
    "hypotenuse_retargeted",
    "degenerate_zero_leg",
    "right_angle_mislabeled",
)

# The registered gate for each class, written before the adjudication run.
# ``verify`` re-derives the observed gate; a disagreement is a reportable
# miss on P-VO2, not something to quietly re-label.
REGISTERED_GATE = {
    "right_angle_epsilon": "right_angle",
    "leg_length": "leg_lengths",
    "edge_disconnected": "incidence",
    "hypotenuse_retargeted": "topology",
    "degenerate_zero_leg": "nondegenerate",
    "right_angle_mislabeled": "right_angle_slot",
}


@dataclass(frozen=True)
class Mutation:
    """What was broken, where, and how far."""

    kind: str
    elements: tuple[str, ...]
    detail: str
    magnitude: str          # exact, as text
    magnitude_degrees: float | None  # informational only; never verified
    claim_adjusted: bool

    def to_dict(self) -> dict:
        return {"kind": self.kind, "elements": list(self.elements),
                "detail": self.detail, "magnitude": self.magnitude,
                "magnitude_degrees": self.magnitude_degrees,
                "claim_adjusted": self.claim_adjusted,
                "registered_gate": REGISTERED_GATE[self.kind]}


@dataclass(frozen=True)
class Instance:
    """One verifiable item: a graph, the claim it is measured against, and
    (for invalids) the mutation that produced it."""

    instance_id: str
    figure_id: str
    kind: str            # "valid" or an INVALID_CLASSES member
    graph: SceneGraph
    claim: Claim
    params: TriangleParams
    mutation: Mutation | None
    split: str

    @property
    def expected_valid(self) -> bool:
        return self.kind == "valid"


def _move_vertex(g: SceneGraph, vid: str, new_pt: Pt) -> SceneGraph:
    """Move a vertex and carry every incident edge endpoint with it.

    Incidence stays intact, so this helper can never accidentally
    manufacture the ``edge_disconnected`` violation while trying to make a
    different one.
    """
    g = g.with_vertex(vid, point=new_pt)
    for e in g.edges:
        if e.frm == vid:
            g = g.with_edge(e.id, p1=new_pt)
        if e.to == vid:
            g = g.with_edge(e.id, p2=new_pt)
    return g


def mutate(params: TriangleParams, figure_id: str, kind: str
           ) -> tuple[SceneGraph, Claim, Mutation]:
    g = build_scene(params, figure_id)
    claim = build_claim(params)
    a_vec, b_vec, w_vec = leg_vectors(params)
    r = g.vertex(V_RIGHT).point

    if kind == "right_angle_epsilon":
        # Length-preserving rotation of leg b onto the exact near-miss
        # direction. |w| == |b| exactly, so the length check cannot see it
        # and the right-angle check is the only detector.
        new_b = r + w_vec
        g = _move_vertex(g, V_LEG_B, new_b)
        dot = a_vec.dot(w_vec)
        mut = Mutation(kind, (V_LEG_B, E_LEG_B, E_HYP),
                       "leg b rotated onto the equal-length near-miss "
                       "direction w=(q,p); both leg lengths unchanged",
                       f"dot={fmt(dot)}", params.epsilon_degrees, False)
        return g, claim, mut

    if kind == "leg_length":
        # Extend leg a along its own direction: the right angle survives
        # exactly, only the claimed length is violated.
        step = Vec(a_vec.x / params.m, a_vec.y / params.m)
        new_a = r + a_vec + step
        g = _move_vertex(g, V_LEG_A, new_a)
        mut = Mutation(kind, (V_LEG_A, E_LEG_A, E_HYP),
                       "leg a lengthened by one direction unit along its own "
                       "axis; right angle and all incidences preserved",
                       f"leg_a_sq={fmt((new_a - r).norm_sq())} "
                       f"claimed={fmt(claim.leg_a_sq)}", None, False)
        return g, claim, mut

    if kind == "edge_disconnected":
        # The hypotenuse stops touching the vertex it still names. Geometry
        # at the vertices is untouched, so only incidence sees it.
        e = g.edge(E_HYP)
        delta = Vec(Fraction(3), Fraction(-3))
        detached = e.p2 + delta
        if detached == e.p1:
            # Would collapse the hypotenuse to zero length and fire
            # `nondegenerate` alongside `incidence`, taking the class off the
            # diagonal. No figure in the current direction pool comes within
            # 16 units of this, but a future pool entry must fail loudly
            # rather than quietly weaken the ablation.
            raise SceneGraphError(
                f"{figure_id}: disconnection delta collapses the hypotenuse; "
                "choose a delta smaller than the figure")
        g = g.with_edge(E_HYP, p2=detached)
        mut = Mutation(kind, (E_HYP, V_LEG_B),
                       "hypotenuse endpoint detached from the vertex it "
                       "still references; vertex geometry untouched",
                       "delta=(3,-3)", None, False)
        return g, claim, mut

    if kind == "hypotenuse_retargeted":
        # The hypotenuse duplicates leg a. Coordinates are made consistent
        # with the new references so incidence still holds and topology is
        # the only detector.
        a = g.vertex(V_LEG_A).point
        g = g.with_edge(E_HYP, frm=V_RIGHT, to=V_LEG_A, p1=r, p2=a)
        mut = Mutation(kind, (E_HYP,),
                       "hypotenuse re-attached to V.right/V.leg_a, "
                       "duplicating leg a; endpoints kept incident",
                       "degree(V.leg_b)=1", None, False)
        return g, claim, mut

    if kind == "degenerate_zero_leg":
        # A figure that agrees with its own claim and still is not a
        # triangle. The claim is adjusted with it, which is exactly why the
        # length check cannot catch this one.
        g = _move_vertex(g, V_LEG_B, r)
        claim = Claim(claim.leg_a_sq, Fraction(0))
        mut = Mutation(kind, (V_LEG_B, E_LEG_B, E_HYP),
                       "leg b collapsed to zero length and the claim "
                       "collapsed with it; figure and claim agree, and the "
                       "figure is still not a triangle",
                       "leg_b_sq=0", None, True)
        return g, claim, mut

    if kind == "right_angle_mislabeled":
        # Pure slot violation: not one coordinate changes. The annotation
        # that binds the right-angle slot points at the wrong vertex.
        g = g.with_angle(A_RIGHT, vertex=V_LEG_A, arms=(E_LEG_A, E_HYP))
        mut = Mutation(kind, (A_RIGHT,),
                       "right-angle annotation rebound to V.leg_a with arms "
                       "(leg a, hypotenuse); no coordinate changed",
                       "vertex=V.leg_a", None, False)
        return g, claim, mut

    raise ValueError(f"unknown invalid class {kind!r}")


def valid_instance(params: TriangleParams, figure_id: str, split: str
                   ) -> Instance:
    return Instance(f"{figure_id}/valid", figure_id, "valid",
                    build_scene(params, figure_id), build_claim(params),
                    params, None, split)


def invalid_instance(params: TriangleParams, figure_id: str, kind: str,
                     split: str) -> Instance:
    g, claim, mut = mutate(params, figure_id, kind)
    return Instance(f"{figure_id}/{kind}", figure_id, kind, g, claim, params,
                    mut, split)


def instances_for(params: TriangleParams, figure_id: str, split: str
                  ) -> list[Instance]:
    """The complete pair set for one figure: one valid, one per class."""
    out = [valid_instance(params, figure_id, split)]
    out.extend(invalid_instance(params, figure_id, k, split)
               for k in INVALID_CLASSES)
    return out
