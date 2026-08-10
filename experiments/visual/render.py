"""Step 1: the deterministic renderer, scene graph -> SVG.

Pure function of ``(graph, style)``. Every emitted coordinate is an exact
rational formatted as a terminating decimal, including the angle markers,
which are built from rational fractions along the arms rather than from
trigonometric arcs. Nothing in this file calls ``random`` or touches a float.

Styles vary exactly the things step 6's style-OOD split will vary -- stroke
width, colour, vertex radius, marker size, presence of background and labels,
and attribute order -- and vary nothing that a geometric relation depends on.
The parser must return the identical normalized graph from all of them; that
equivalence is the parser's contract, tested rather than asserted.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

from .scene import (Angle, Edge, Pt, SceneGraph, Vertex, fmt)

SVG_NS = "http://www.w3.org/2000/svg"


@dataclass(frozen=True)
class RenderStyle:
    name: str
    stroke: str
    stroke_width: int
    vertex_radius: int
    vertex_fill: str
    marker_stroke: str
    marker_t: Fraction
    background: str | None
    labels: bool
    margin: int
    data_first: bool  # attribute ordering; the parser must not care


STYLES: dict[str, RenderStyle] = {
    "plain": RenderStyle("plain", "#222222", 3, 6, "#222222", "#c0392b",
                         Fraction(1, 8), "#ffffff", True, 24, False),
    "bold": RenderStyle("bold", "#0a3d62", 7, 11, "#0a3d62", "#e58e26",
                        Fraction(3, 16), "#f7f1e3", True, 40, True),
    "sparse": RenderStyle("sparse", "#000000", 1, 2, "#000000", "#000000",
                          Fraction(1, 10), None, False, 12, False),
}

EDGE_LABEL = {"leg_a": "a", "leg_b": "b", "hypotenuse": "c"}


def _attrs(pairs: list[tuple[str, str]]) -> str:
    return " ".join(f'{k}="{v}"' for k, v in pairs)


def _order(style: RenderStyle, data: list, geom: list, paint: list) -> str:
    return _attrs((data + geom + paint) if style.data_first
                  else (geom + data + paint))


def _bbox(g: SceneGraph, margin: int) -> tuple[int, int, int, int]:
    xs = [p.x for p in g.points()]
    ys = [p.y for p in g.points()]
    x0 = math.floor(min(xs)) - margin
    y0 = math.floor(min(ys)) - margin
    x1 = math.ceil(max(xs)) + margin
    y1 = math.ceil(max(ys)) + margin
    return x0, y0, max(x1 - x0, 1), max(y1 - y0, 1)


def _far_point(g: SceneGraph, arm_id: str, at: Pt) -> Pt:
    """The end of ``arm_id`` away from ``at``.

    Total by construction: a mutated graph may name an arm that no longer
    touches the angle's vertex, and the renderer still has to draw
    *something* -- deciding what a broken figure looks like is the renderer's
    job, deciding that it is broken is the verifier's.
    """
    e = g.edge(arm_id)
    if e is None:
        return at
    d1 = (e.p1 - at).norm_sq()
    d2 = (e.p2 - at).norm_sq()
    return e.p1 if d1 > d2 else e.p2


def _along(a: Pt, b: Pt, t: Fraction) -> Pt:
    return Pt(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t)


def _marker_path(g: SceneGraph, ang: Angle, style: RenderStyle) -> str:
    v = g.vertex(ang.vertex)
    at = v.point if v is not None else Pt(Fraction(0), Fraction(0))
    f1 = _far_point(g, ang.arms[0], at)
    f2 = _far_point(g, ang.arms[1], at)
    p1 = _along(at, f1, style.marker_t)
    p2 = _along(at, f2, style.marker_t)
    if ang.measure == "right":
        corner = Pt(p1.x + p2.x - at.x, p1.y + p2.y - at.y)
        return (f"M {fmt(p1.x)} {fmt(p1.y)} L {fmt(corner.x)} "
                f"{fmt(corner.y)} L {fmt(p2.x)} {fmt(p2.y)}")
    return f"M {fmt(p1.x)} {fmt(p1.y)} L {fmt(p2.x)} {fmt(p2.y)}"


def _render_edge(e: Edge, style: RenderStyle) -> str:
    data = [("data-sid", e.id), ("data-kind", "edge"), ("data-role", e.role),
            ("data-from", e.frm), ("data-to", e.to)]
    geom = [("x1", fmt(e.p1.x)), ("y1", fmt(e.p1.y)),
            ("x2", fmt(e.p2.x)), ("y2", fmt(e.p2.y))]
    paint = [("stroke", style.stroke),
             ("stroke-width", str(style.stroke_width)),
             ("stroke-linecap", "round")]
    return f"    <line {_order(style, data, geom, paint)}/>"


def _render_vertex(v: Vertex, style: RenderStyle) -> str:
    data = [("data-sid", v.id), ("data-kind", "vertex"),
            ("data-role", v.role)]
    geom = [("cx", fmt(v.point.x)), ("cy", fmt(v.point.y)),
            ("r", str(style.vertex_radius))]
    paint = [("fill", style.vertex_fill)]
    return f"    <circle {_order(style, data, geom, paint)}/>"


def _render_angle(g: SceneGraph, a: Angle, style: RenderStyle) -> str:
    data = [("data-sid", a.id), ("data-kind", "angle"), ("data-role", a.role),
            ("data-vertex", a.vertex), ("data-arms", " ".join(a.arms)),
            ("data-measure", a.measure)]
    geom = [("d", _marker_path(g, a, style))]
    paint = [("fill", "none"), ("stroke", style.marker_stroke),
             ("stroke-width", str(max(1, style.stroke_width - 1)))]
    return f"    <path {_order(style, data, geom, paint)}/>"


def _render_label(e: Edge, style: RenderStyle) -> str:
    mid = Pt((e.p1.x + e.p2.x) / 2, (e.p1.y + e.p2.y) / 2)
    text = EDGE_LABEL.get(e.role, "?")
    return (f'    <text data-sid="L.{e.role}" data-kind="label" '
            f'x="{fmt(mid.x)}" y="{fmt(mid.y)}" '
            f'font-size="{style.vertex_radius * 2}" '
            f'fill="{style.stroke}">{text}</text>')


def render_svg(g: SceneGraph, style: RenderStyle | str = "plain") -> str:
    """Step 1. Deterministic SVG text for a scene graph."""
    if isinstance(style, str):
        style = STYLES[style]
    x0, y0, w, h = _bbox(g, style.margin)
    out = [
        f'<svg xmlns="{SVG_NS}" viewBox="{x0} {y0} {w} {h}" '
        f'width="{w}" height="{h}" data-schema="visual-scene/1" '
        f'data-figure="{g.figure_id}" data-family="{g.family}" '
        f'data-style="{style.name}">',
    ]
    if style.background is not None:
        out.append(f'  <rect x="{x0}" y="{y0}" width="{w}" height="{h}" '
                   f'fill="{style.background}"/>')
    out.append('  <g data-group="edges">')
    for e in sorted(g.edges, key=lambda e: e.id):
        out.append(_render_edge(e, style))
    out.append('  </g>')
    out.append('  <g data-group="vertices">')
    for v in sorted(g.vertices, key=lambda v: v.id):
        out.append(_render_vertex(v, style))
    out.append('  </g>')
    out.append('  <g data-group="angles">')
    for a in sorted(g.angles, key=lambda a: a.id):
        out.append(_render_angle(g, a, style))
    out.append('  </g>')
    if style.labels:
        out.append('  <g data-group="labels">')
        for e in sorted(g.edges, key=lambda e: e.id):
            out.append(_render_label(e, style))
        out.append('  </g>')
    out.append('</svg>')
    return "\n".join(out) + "\n"
