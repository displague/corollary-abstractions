"""Step 5: normalized SVG/tree input.

The parser reads the emitted SVG back into the same normalized scene graph
the renderer was given. Two rules keep it honest:

1. **Geometry comes from geometric attributes.** Coordinates are read from
   ``x1/y1/x2/y2``, ``cx/cy`` -- never from a ``data-*`` hint. If the parser
   read positions out of metadata it would be validating a copy of the
   source graph, and the round-trip test would prove nothing.
2. **Identity comes from source structure.** ``data-sid``/``data-role``/
   ``data-from``/``data-to`` carry the slot identity that the SVG format
   itself has no vocabulary for. That is the parse-first premise of the lane:
   the picture is emitted from a structure, and the structure is what is
   read back.

Everything else -- background, stroke widths, colours, fonts, text labels,
marker path data, attribute order, the group wrappers -- is appearance and is
dropped. The anti-erasure control for that decision is not an argument, it is
``render_svg(parse_svg(svg), style)`` reproducing ``svg`` byte for byte: a
normalization that discarded a load-bearing relation could not rebuild the
picture.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from .scene import (Angle, Edge, Pt, SceneGraph, SceneGraphError, Vertex,
                    check_wellformed, normalize, num)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _require(el: ET.Element, name: str) -> str:
    val = el.get(name)
    if val is None:
        raise SceneGraphError(
            f"<{_local(el.tag)}> is missing required attribute {name!r}")
    return val


def parse_svg(svg_text: str) -> SceneGraph:
    """Step 5. Normalized scene graph from rendered SVG text."""
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as exc:
        raise SceneGraphError(f"unparseable SVG: {exc}") from exc
    if _local(root.tag) != "svg":
        raise SceneGraphError(
            f"root element is <{_local(root.tag)}>, not <svg>")
    if root.get("data-schema") != "visual-scene/1":
        raise SceneGraphError(
            f"unknown scene schema {root.get('data-schema')!r}")
    figure_id = _require(root, "data-figure")
    family = _require(root, "data-family")

    vertices: list[Vertex] = []
    edges: list[Edge] = []
    angles: list[Angle] = []
    for el in root.iter():
        kind = el.get("data-kind")
        if kind is None or kind == "label":
            continue
        sid = _require(el, "data-sid")
        role = _require(el, "data-role")
        if kind == "vertex":
            vertices.append(Vertex(sid, role,
                                   Pt(num(_require(el, "cx")),
                                      num(_require(el, "cy")))))
        elif kind == "edge":
            edges.append(Edge(sid, role,
                              _require(el, "data-from"),
                              _require(el, "data-to"),
                              Pt(num(_require(el, "x1")),
                                 num(_require(el, "y1"))),
                              Pt(num(_require(el, "x2")),
                                 num(_require(el, "y2")))))
        elif kind == "angle":
            arms = tuple(_require(el, "data-arms").split())
            if len(arms) != 2:
                raise SceneGraphError(
                    f"angle {sid} declares {len(arms)} arms, expected 2")
            angles.append(Angle(sid, role, _require(el, "data-vertex"),
                                arms, _require(el, "data-measure")))
        else:
            raise SceneGraphError(f"unknown data-kind {kind!r} on {sid}")

    g = SceneGraph(figure_id, family, tuple(vertices), tuple(edges),
                   tuple(angles))
    check_wellformed(g)
    return normalize(g)
