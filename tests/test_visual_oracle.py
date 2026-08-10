"""Tests for the visual ground-truth oracle layer (ROADMAP-v0.7 item 8, 1-5).

Two kinds of test live here and they are kept visibly separate.

*Protocol tests* run the registered N=240 protocol and assert the numbers in
``experiments/visual/__init__.py``'s prediction block. If a prediction is
falsified this suite fails loudly rather than reporting a softer number.

*Anti-vacuity tests* attack the oracle itself: that each verifier check can be
disabled into a specific escape, that the redundant checks really are
redundant, that a check with no teeth would be caught, and that normalization
does not quietly erase the relation the verifier depends on. A verifier that
accepts everything and a verifier that rejects everything both score
perfectly on a badly chosen metric; these tests are what separate this one
from both.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "experiments"))

from visual.genvisual import (  # noqa: E402
    DEFAULT_N, DEFAULT_SEED, DEFAULT_STYLES, adjudicate, blind_baselines,
    build_corpus, draw_params, split_for, surface_features, write_fixtures)
from visual.mutate import (  # noqa: E402
    INVALID_CLASSES, REGISTERED_GATE, instances_for, mutate)
from visual.parse import parse_svg  # noqa: E402
from visual.render import STYLES, render_svg  # noqa: E402
from visual.scene import (  # noqa: E402
    A_RIGHT, E_HYP, E_LEG_A, ELEMENT_IDS, Pt, ROLE_TO_ANGLE, ROLE_TO_EDGE,
    ROLE_TO_VERTEX, SceneGraphError, TriangleParams, V_LEG_A, V_LEG_B,
    V_RIGHT, build_claim, build_scene, fmt, from_dict, leg_vectors, normalize,
    to_dict)
from visual.verify import DERIVED_CHECKS, GATED_CHECKS, verify  # noqa: E402

FIXTURES = ROOT / "experiments" / "visual" / "fixtures"
SMALL_N = 24


def small_corpus():
    return build_corpus(SMALL_N, DEFAULT_SEED)


class RendererTests(unittest.TestCase):
    """Step 1: deterministic right-triangle renderer."""

    def test_render_is_a_pure_function_of_graph_and_style(self) -> None:
        params = draw_params(3, DEFAULT_SEED)[2]
        g = build_scene(params, "rt-0002")
        for style in DEFAULT_STYLES:
            self.assertEqual(render_svg(g, style), render_svg(g, style))
            # rebuilding the graph from the same parameters must reproduce
            # the bytes: nothing downstream of the seeded draw is random
            again = build_scene(params, "rt-0002")
            self.assertEqual(render_svg(again, style), render_svg(g, style))

    def test_rendered_geometry_is_exact_not_floating_point(self) -> None:
        """Every emitted coordinate parses back to the exact rational.

        Floats in a coordinate would make the verifier approximate without
        anyone saying so, which is the failure mode this layer exists to
        prevent.
        """
        for inst in small_corpus():
            parsed = parse_svg(render_svg(inst.graph, "plain"))
            for src, dst in zip(normalize(inst.graph).vertices,
                                parsed.vertices):
                self.assertIsInstance(dst.point.x, Fraction)
                self.assertEqual(src.point, dst.point)

    def test_serializer_refuses_a_non_terminating_coordinate(self) -> None:
        with self.assertRaises(SceneGraphError):
            fmt(Fraction(1, 3))
        self.assertEqual(fmt(Fraction(-1, 2)), "-0.5")
        self.assertEqual(fmt(Fraction(7)), "7")

    def test_styles_change_appearance_and_not_structure(self) -> None:
        g = small_corpus()[0].graph
        svgs = {s: render_svg(g, s) for s in DEFAULT_STYLES}
        self.assertEqual(len(set(svgs.values())), len(DEFAULT_STYLES))
        parsed = {parse_svg(v) for v in svgs.values()}
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed.pop(), normalize(g))


class SlotIdentityTests(unittest.TestCase):
    """Step 2: stable slot-to-element identities (P-VO5)."""

    def test_ids_survive_every_parameter_change(self) -> None:
        base = TriangleParams(p=15, q=2, m=4, n=6, ox=0, oy=0, hand=1, dih=0)
        variants = [
            base,
            TriangleParams(**{**vars(base), "m": 12, "n": 2}),   # legs swapped
            TriangleParams(**{**vars(base), "p": 75, "q": 1}),   # direction
            TriangleParams(**{**vars(base), "ox": 90, "oy": 40}),  # translate
            TriangleParams(**{**vars(base), "dih": 3}),          # rotate
            TriangleParams(**{**vars(base), "hand": -1}),        # mirror
        ]
        maps = set()
        for i, params in enumerate(variants):
            g = build_scene(params, f"rt-{i:04d}")
            self.assertEqual(
                frozenset(e.id for e in (*g.vertices, *g.edges, *g.angles)),
                ELEMENT_IDS)
            maps.add((tuple(sorted((v.role, v.id) for v in g.vertices)),
                      tuple(sorted((e.role, e.id) for e in g.edges)),
                      tuple(sorted((a.role, a.id) for a in g.angles))))
        self.assertEqual(len(maps), 1)
        vmap, emap, amap = maps.pop()
        self.assertEqual(dict(vmap), ROLE_TO_VERTEX)
        self.assertEqual(dict(emap), ROLE_TO_EDGE)
        self.assertEqual(dict(amap), ROLE_TO_ANGLE)

    def test_no_id_encodes_geometry(self) -> None:
        for eid in ELEMENT_IDS:
            self.assertFalse(any(ch.isdigit() for ch in eid), eid)

    def test_mutations_rebind_referents_never_ids(self) -> None:
        params = draw_params(1, DEFAULT_SEED)[0]
        for cls in INVALID_CLASSES:
            g, _, _ = mutate(params, "rt-0000", cls)
            self.assertEqual(
                frozenset(e.id for e in (*g.vertices, *g.edges, *g.angles)),
                ELEMENT_IDS, cls)

    def test_incomplete_slot_inventory_is_refused_at_the_door(self) -> None:
        """Keeps the ablation readable.

        Verifier checks stay silent about relations they cannot evaluate, so
        that disabling one never mutes another. Refusing an incomplete
        inventory here makes those silent branches unreachable: a graph the
        verifier sees always has every slot each check addresses.
        """
        g = build_scene(draw_params(1, DEFAULT_SEED)[0], "rt-0000")
        from visual.scene import SceneGraph
        missing = SceneGraph(g.figure_id, g.family,
                             tuple(v for v in g.vertices if v.id != V_LEG_B),
                             g.edges, g.angles)
        with self.assertRaises(SceneGraphError):
            from visual.scene import check_wellformed
            check_wellformed(missing)
        renamed = g.with_vertex(V_LEG_A, role="leg_b_end")
        with self.assertRaises(SceneGraphError):
            from visual.scene import check_wellformed as cw
            cw(renamed)

    def test_dangling_references_cannot_verify_ok(self) -> None:
        """Regression for a real accept-a-broken-figure hole.

        Found by adversarial review: an angle annotation pointing at a
        nonexistent vertex passed well-formedness, round-tripped through the
        SVG, and verified ``ok`` — because no gated check audits the acute
        annotations and none resolved the reference. Refused at the door now
        rather than gated as a seventh check: no controlled class exercises
        it, and a check without a class is the decoration this layer avoids.
        """
        from visual.scene import Angle, SceneGraph, check_wellformed
        g = build_scene(draw_params(1, DEFAULT_SEED)[0], "rt-0000")
        ghosts = [
            ("angle vertex", SceneGraph(
                g.figure_id, g.family, g.vertices, g.edges,
                tuple(Angle(a.id, a.role, "V.ghost", a.arms, a.measure)
                      if a.id == "A.acu_b" else a for a in g.angles))),
            ("angle arm", SceneGraph(
                g.figure_id, g.family, g.vertices, g.edges,
                tuple(Angle(a.id, a.role, a.vertex, ("E.ghost", a.arms[1]),
                            a.measure) if a.id == "A.acu_b" else a
                      for a in g.angles))),
            ("angle measure", SceneGraph(
                g.figure_id, g.family, g.vertices, g.edges,
                tuple(Angle(a.id, a.role, a.vertex, a.arms, "wobbly")
                      if a.id == "A.acu_b" else a for a in g.angles))),
            ("edge endpoint", g.with_edge(E_HYP, to="V.ghost")),
        ]
        for label, broken in ghosts:
            with self.subTest(label):
                with self.assertRaises(SceneGraphError):
                    check_wellformed(broken)
                with self.assertRaises(SceneGraphError):
                    parse_svg(render_svg(broken, "plain"))

    def test_scene_graph_json_round_trips(self) -> None:
        for inst in small_corpus():
            self.assertEqual(from_dict(to_dict(inst.graph)),
                             normalize(inst.graph))


class InvalidGeneratorTests(unittest.TestCase):
    """Step 3: controlled-invalid pairs."""

    def test_every_valid_gets_one_near_miss_per_class(self) -> None:
        insts = instances_for(draw_params(1, DEFAULT_SEED)[0], "rt-0000",
                              "train")
        self.assertEqual(len(insts), 1 + len(INVALID_CLASSES))
        self.assertEqual([i.kind for i in insts],
                         ["valid", *INVALID_CLASSES])

    def test_mutation_metadata_names_what_was_broken(self) -> None:
        params = draw_params(1, DEFAULT_SEED)[0]
        for cls in INVALID_CLASSES:
            _, _, mut = mutate(params, "rt-0000", cls)
            self.assertEqual(mut.kind, cls)
            self.assertTrue(mut.elements)
            self.assertTrue(set(mut.elements) <= ELEMENT_IDS)
            self.assertTrue(mut.detail)
            self.assertEqual(mut.to_dict()["registered_gate"],
                             REGISTERED_GATE[cls])

    def test_right_angle_break_preserves_leg_lengths_exactly(self) -> None:
        """The mechanism that makes the right-angle check separably testable.

        If the near-miss changed a leg length, the length check would
        co-detect it and neither check could be ablated into a unique escape.
        """
        for params in draw_params(12, DEFAULT_SEED):
            a_vec, b_vec, w_vec = leg_vectors(params)
            self.assertEqual(b_vec.norm_sq(), w_vec.norm_sq())
            self.assertEqual(a_vec.dot(b_vec), 0)
            self.assertNotEqual(a_vec.dot(w_vec), 0)
            self.assertNotEqual(a_vec.cross(w_vec), 0)
            g, claim, _ = mutate(params, "rt-x", "right_angle_epsilon")
            r = g.vertex(V_RIGHT).point
            self.assertEqual((g.vertex(V_LEG_A).point - r).norm_sq(),
                             claim.leg_a_sq)
            self.assertEqual((g.vertex(V_LEG_B).point - r).norm_sq(),
                             claim.leg_b_sq)

    def test_out_of_contract_parameters_fail_loudly(self) -> None:
        """The diagonal has preconditions, and they are enforced, not hoped.

        With ``p == q`` the equal-length near-miss direction is collinear
        with leg a, so the right-angle break would also fire
        ``nondegenerate`` and the ablation for either check would be
        unsound. A figure like that must raise rather than score.
        """
        for bad in (dict(p=3, q=3), dict(p=1, q=4), dict(n=0), dict(m=0),
                    dict(hand=0)):
            base = dict(p=15, q=2, m=4, n=6, ox=0, oy=0, hand=1, dih=0)
            params = TriangleParams(**{**base, **bad})
            with self.subTest(**bad):
                with self.assertRaises(SceneGraphError):
                    build_scene(params, "rt-bad")
                with self.assertRaises(SceneGraphError):
                    mutate(params, "rt-bad", "right_angle_epsilon")

    def test_generated_parameters_satisfy_the_contract(self) -> None:
        for params in draw_params(DEFAULT_N, DEFAULT_SEED):
            params.validate()

    def test_near_misses_are_near(self) -> None:
        """A near-miss the eye can see is not a near-miss."""
        for params in draw_params(24, DEFAULT_SEED):
            self.assertLess(params.epsilon_degrees, 17.0)
            self.assertGreater(params.epsilon_degrees, 1.0)

    def test_slot_only_mutation_changes_no_coordinate(self) -> None:
        params = draw_params(1, DEFAULT_SEED)[0]
        base = build_scene(params, "rt-0000")
        g, _, _ = mutate(params, "rt-0000", "right_angle_mislabeled")
        self.assertEqual([v.point for v in base.vertices],
                         [v.point for v in g.vertices])
        self.assertEqual([(e.p1, e.p2) for e in base.edges],
                         [(e.p1, e.p2) for e in g.edges])

    def test_degenerate_class_agrees_with_its_own_claim(self) -> None:
        """The only class allowed to move the claim, and why it must.

        A zero-length leg whose claim still asserted a positive length would
        be caught by the length check, leaving nondegeneracy untestable.
        """
        params = draw_params(1, DEFAULT_SEED)[0]
        g, claim, mut = mutate(params, "rt-0000", "degenerate_zero_leg")
        self.assertTrue(mut.claim_adjusted)
        self.assertEqual(claim.leg_b_sq, 0)
        self.assertEqual(verify(g, claim).failed_checks, ("nondegenerate",))
        others = [c for c in INVALID_CLASSES if c != "degenerate_zero_leg"]
        for cls in others:
            _, _, m = mutate(params, "rt-0000", cls)
            self.assertFalse(m.claim_adjusted, cls)


class VerifierTests(unittest.TestCase):
    """Step 4: the exact verifier and its ablations."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus = small_corpus()

    def test_accepts_every_valid(self) -> None:
        valids = [i for i in self.corpus if i.expected_valid]
        self.assertEqual(
            sum(1 for i in valids if verify(i.graph, i.claim).ok),
            len(valids))

    def test_rejects_every_invalid_at_its_registered_gate(self) -> None:
        for inst in self.corpus:
            if inst.expected_valid:
                continue
            res = verify(inst.graph, inst.claim)
            self.assertFalse(res.ok, inst.instance_id)
            self.assertEqual(res.failed_checks,
                             (REGISTERED_GATE[inst.kind],), inst.instance_id)

    def test_failures_localize_the_violated_elements(self) -> None:
        """Step 6 has to score 'point at the broken relation'; the verifier
        has to be able to answer it first."""
        for inst in self.corpus:
            if inst.expected_valid:
                continue
            res = verify(inst.graph, inst.claim)
            named = {e for f in res.failures for e in f.elements}
            # the first element of the mutation record is the one that was
            # actually broken; a non-empty intersection would pass almost
            # regardless of what the check reported
            self.assertIn(inst.mutation.elements[0], named,
                          f"{inst.instance_id}: {sorted(named)}")

    def test_every_gated_check_is_load_bearing(self) -> None:
        """The ablation: disable one check, watch exactly one class escape."""
        valids = [i for i in self.corpus if i.expected_valid]
        for check in GATED_CHECKS:
            gated_class = next(c for c, g in REGISTERED_GATE.items()
                               if g == check)
            with self.subTest(check=check):
                self.assertEqual(
                    sum(1 for i in valids
                        if verify(i.graph, i.claim, (check,)).ok),
                    len(valids), "ablation must not reject valids")
                for cls in INVALID_CLASSES:
                    rows = [i for i in self.corpus if i.kind == cls]
                    escaped = sum(1 for r in rows
                                  if verify(r.graph, r.claim, (check,)).ok)
                    self.assertEqual(escaped,
                                     len(rows) if cls == gated_class else 0,
                                     f"{check} vs {cls}")

    def test_each_check_alone_catches_exactly_its_own_class(self) -> None:
        """Leave-one-in, the dual of the ablation.

        Disabling a check shows it is necessary; enabling only that check
        shows the six do not overlap. Together they say the checks partition
        the negative set, which is the strongest form of 'no decoration'.
        """
        invalids = [i for i in self.corpus if not i.expected_valid]
        valids = [i for i in self.corpus if i.expected_valid]
        for keep in GATED_CHECKS:
            off = tuple(c for c in GATED_CHECKS if c != keep)
            gated_class = next(c for c, g in REGISTERED_GATE.items()
                               if g == keep)
            with self.subTest(only=keep):
                caught = [i for i in invalids
                          if not verify(i.graph, i.claim, off).ok]
                self.assertEqual({i.kind for i in caught}, {gated_class})
                self.assertEqual(len(caught),
                                 len(invalids) // len(INVALID_CLASSES))
                self.assertFalse([i for i in valids
                                  if not verify(i.graph, i.claim, off).ok])

    def test_check_inventory_is_exactly_the_gated_set(self) -> None:
        """No check without a class, no class without a check."""
        self.assertEqual(set(GATED_CHECKS), set(REGISTERED_GATE.values()))
        self.assertEqual(len(GATED_CHECKS), len(INVALID_CLASSES))

    def test_derived_checks_are_true_and_verdict_redundant(self) -> None:
        """P-VO6, with correction C1 applied.

        ``base.ok == withd.ok`` cannot fail on an invalid: the derived set is
        a superset of the gated set, so the verdict can only move accept ->
        reject, and an invalid is already a reject. The content is on the
        valids, where a derived check firing would mean it is not implied by
        the gate at all. The invalids get the other half of the statement:
        the derived checks are live assertions that do fire, always on top of
        a gated failure rather than instead of one.
        """
        fired_on_invalid = 0
        for inst in self.corpus:
            base = verify(inst.graph, inst.claim)
            withd = verify(inst.graph, inst.claim, derived=True)
            self.assertEqual(base.ok, withd.ok, inst.instance_id)
            derived = [f for f in withd.failures if f.check in DERIVED_CHECKS]
            if base.ok:
                self.assertFalse(derived, inst.instance_id)
            elif derived:
                fired_on_invalid += 1
        self.assertGreater(fired_on_invalid, 0,
                           "derived checks that never fire anywhere are not "
                           "redundant assertions, they are dead code")

    def test_disabling_everything_accepts_everything(self) -> None:
        """Proves ``disabled`` removes capability rather than relabelling it.

        Without this, an ablation that silently kept checking would report a
        load-bearing result for a check that does nothing.
        """
        for inst in self.corpus:
            self.assertTrue(verify(inst.graph, inst.claim, GATED_CHECKS).ok)

    def test_rejects_an_ordinary_non_right_triangle(self) -> None:
        """A triangle that was never a right triangle, not a mutation of one.

        Guards against a verifier that only recognizes its own generator.
        """
        params = TriangleParams(p=15, q=2, m=4, n=6, ox=0, oy=0, hand=1,
                                dih=0)
        g = build_scene(params, "rt-scalene")
        moved = Pt(Fraction(11), Fraction(97))
        g = g.with_vertex(V_LEG_B, point=moved)
        g = g.with_edge("E.leg_b", p2=moved).with_edge(E_HYP, p2=moved)
        res = verify(g, build_claim(params))
        self.assertFalse(res.ok)
        self.assertIn("right_angle", res.failed_checks)

    def test_a_single_unit_perturbation_is_not_tolerated(self) -> None:
        """There is no epsilon in the verifier; this is what that means."""
        inst = self.corpus[0]
        v = inst.graph.vertex(V_LEG_A)
        moved = Pt(v.point.x + 1, v.point.y)
        g = inst.graph.with_vertex(V_LEG_A, point=moved)
        g = g.with_edge(E_LEG_A, p2=moved).with_edge(E_HYP, p1=moved)
        self.assertFalse(verify(g, inst.claim).ok)

    def test_unknown_check_name_is_refused(self) -> None:
        inst = self.corpus[0]
        with self.assertRaises(ValueError):
            verify(inst.graph, inst.claim, ("no_such_check",))


class ParserTests(unittest.TestCase):
    """Step 5: normalized SVG/tree input."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus = small_corpus()

    def test_round_trip_equals_the_source_graph(self) -> None:
        for inst in self.corpus:
            for style in DEFAULT_STYLES:
                self.assertEqual(parse_svg(render_svg(inst.graph, style)),
                                 normalize(inst.graph),
                                 f"{inst.instance_id}/{style}")

    def test_round_trip_preserves_verdict_and_localization(self) -> None:
        for inst in self.corpus:
            src = verify(inst.graph, inst.claim)
            dst = verify(parse_svg(render_svg(inst.graph, "plain")),
                         inst.claim)
            self.assertEqual(src.ok, dst.ok)
            self.assertEqual(src.failed_checks, dst.failed_checks)
            self.assertEqual([f.to_dict() for f in src.failures],
                             [f.to_dict() for f in dst.failures])

    def test_rerender_from_parsed_graph_is_byte_identical(self) -> None:
        """The anti-erasure control.

        Normalization drops background, colours, fonts, labels, marker path
        data and attribute order. If any of that had encoded a relation the
        graph does not carry, the re-render could not reproduce the bytes.
        """
        for inst in self.corpus:
            for style in DEFAULT_STYLES:
                svg = render_svg(inst.graph, style)
                self.assertEqual(render_svg(parse_svg(svg), style), svg)

    def test_parser_reads_geometry_from_geometry_not_metadata(self) -> None:
        """Corrupt a coordinate attribute only; the parser must follow it.

        A parser that trusted ``data-*`` for positions would round-trip
        perfectly and verify nothing.
        """
        inst = self.corpus[0]
        svg = render_svg(inst.graph, "plain")
        v = inst.graph.vertex(V_RIGHT)
        needle = f'cx="{fmt(v.point.x)}" cy="{fmt(v.point.y)}"'
        self.assertIn(needle, svg)
        moved = svg.replace(needle, f'cx="{fmt(v.point.x + 5)}" '
                                    f'cy="{fmt(v.point.y)}"', 1)
        parsed = parse_svg(moved)
        self.assertNotEqual(parsed, normalize(inst.graph))
        self.assertFalse(verify(parsed, inst.claim).ok)

    def test_parser_refuses_input_it_does_not_understand(self) -> None:
        svg = render_svg(self.corpus[0].graph, "plain")
        with self.assertRaises(SceneGraphError):
            parse_svg(svg.replace('data-schema="visual-scene/1"',
                                  'data-schema="visual-scene/9"'))
        with self.assertRaises(SceneGraphError):
            parse_svg(svg.replace('data-kind="vertex"', 'data-kind="blob"'))
        with self.assertRaises(SceneGraphError):
            parse_svg("<svg></svg>")

    def test_labels_and_background_are_appearance_only(self) -> None:
        g = self.corpus[0].graph
        plain = parse_svg(render_svg(g, "plain"))     # has both
        sparse = parse_svg(render_svg(g, "sparse"))   # has neither
        self.assertEqual(plain, sparse)


class CorpusTests(unittest.TestCase):
    """Generator conventions: seeds, splits, artifacts."""

    def test_corpus_is_regenerable_from_the_seed(self) -> None:
        a = build_corpus(SMALL_N, DEFAULT_SEED)
        b = build_corpus(SMALL_N, DEFAULT_SEED)
        self.assertEqual([i.instance_id for i in a],
                         [i.instance_id for i in b])
        self.assertEqual([to_dict(i.graph) for i in a],
                         [to_dict(i.graph) for i in b])

    def test_figures_are_distinct(self) -> None:
        params = draw_params(DEFAULT_N, DEFAULT_SEED)
        self.assertEqual(len({p.signature() for p in params}), DEFAULT_N)

    def test_splits_are_md5_stable_not_process_hash(self) -> None:
        self.assertEqual(split_for("p75q1m12n12o80,90h1d1"),
                         split_for("p75q1m12n12o80,90h1d1"))
        splits = [split_for(p.signature())
                  for p in draw_params(DEFAULT_N, DEFAULT_SEED)]
        self.assertEqual(set(splits), {"train", "val", "test"})
        self.assertGreater(splits.count("train"), splits.count("val"))

    def test_a_figures_pair_set_shares_one_split(self) -> None:
        """Held-out figures must not leak through their own near-misses."""
        by_figure: dict[str, set[str]] = {}
        for inst in small_corpus():
            by_figure.setdefault(inst.figure_id, set()).add(inst.split)
        self.assertTrue(all(len(v) == 1 for v in by_figure.values()))

    def test_committed_fixtures_regenerate_identically(self) -> None:
        """Byte-format regression guard, in the spirit of check_regeneration.

        Compared as text rather than raw bytes: Windows checkout policy
        rewrites line endings, which is the same provenance edge v0.6 hit
        with the depth manifest. Content, not newline convention, is what
        this guard is about.
        """
        with tempfile.TemporaryDirectory() as tmp:
            written = write_fixtures(Path(tmp), DEFAULT_SEED)
            self.assertTrue(written)
            for path in written:
                committed = FIXTURES / path.name
                self.assertTrue(committed.exists(), committed)
                self.assertEqual(committed.read_text(encoding="utf-8"),
                                 path.read_text(encoding="utf-8"),
                                 committed.name)
        self.assertEqual({p.name for p in FIXTURES.iterdir()},
                         {p.name for p in written})

    def test_fixture_figure_is_the_corpus_figure_it_claims_to_be(self) -> None:
        """The fixture is drawn with its own call; if that ever diverged from
        the corpus draw it would pin a figure nobody generates."""
        import json
        manifest = json.loads((FIXTURES / "manifest.json")
                              .read_text(encoding="utf-8"))
        first = build_corpus(1, DEFAULT_SEED)[0]
        self.assertEqual(manifest["figure_id"], first.figure_id)
        self.assertEqual(manifest["params"]["signature"],
                         first.params.signature())
        self.assertEqual(
            parse_svg((FIXTURES / "rt-0000.plain.svg")
                      .read_text(encoding="utf-8")),
            normalize(first.graph))

    def test_fixture_svg_parses_and_verifies_as_recorded(self) -> None:
        import json
        manifest = json.loads((FIXTURES / "manifest.json")
                              .read_text(encoding="utf-8"))
        recorded = {i["instance_id"]: i for i in manifest["instances"]}
        for name, iid in (("rt-0000.plain.svg", "rt-0000/valid"),
                          ("rt-0000.right_angle_epsilon.plain.svg",
                           "rt-0000/right_angle_epsilon")):
            g = parse_svg((FIXTURES / name).read_text(encoding="utf-8"))
            from visual.scene import Claim
            claim = Claim.from_dict(recorded[iid]["claim"])
            self.assertEqual(verify(g, claim).to_dict(),
                             recorded[iid]["verdict"], name)

    def test_no_weights_leaked_into_the_oracle_layer(self) -> None:
        """Steps 1-5 are pre-model; step 6 is a separate delivery."""
        pkg = ROOT / "experiments" / "visual"
        for path in pkg.glob("*.py"):
            text = path.read_text(encoding="utf-8")
            for banned in ("import torch", "import numpy", "torch.nn"):
                self.assertNotIn(banned, text, f"{path.name}: {banned}")


class RegisteredProtocolTests(unittest.TestCase):
    """The registered N=240 protocol, adjudicated (P-VO1..P-VO7)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = adjudicate(build_corpus(DEFAULT_N, DEFAULT_SEED))

    def test_corpus_size_matches_the_registration(self) -> None:
        self.assertEqual(self.report["n_figures"], 240)
        self.assertEqual(self.report["n_instances"], 240 * 7)
        self.assertEqual(self.report["P-VO4"]["round_trips"], 240 * 7 * 3)

    def test_p_vo1_acceptance(self) -> None:
        p = self.report["P-VO1"]
        self.assertEqual((p["accepted"], p["valids"]), (240, 240))
        self.assertTrue(p["fired"])

    def test_p_vo2_rejection_and_diagonal_localization(self) -> None:
        p = self.report["P-VO2"]
        for cls, c in p["per_class"].items():
            self.assertEqual(c["rejected"], 240, cls)
            self.assertEqual(c["exactly_registered_gate"], 240, cls)
        self.assertTrue(p["diagonal"])
        self.assertTrue(p["fired"])

    def test_p_vo3_ablation(self) -> None:
        p = self.report["P-VO3"]
        self.assertEqual(set(p["per_check"]), set(GATED_CHECKS))
        for check, a in p["per_check"].items():
            self.assertTrue(a["load_bearing"], check)
            self.assertTrue(a["other_classes_still_rejected"], check)
            self.assertEqual(a["valids_still_accepted"], 240, check)
        self.assertTrue(p["fired"])

    def test_p_vo4_round_trip(self) -> None:
        p = self.report["P-VO4"]
        for style, s in p["per_style"].items():
            self.assertEqual(s["graph_equal"], 1680, style)
            self.assertEqual(s["verdict_equal"], 1680, style)
            self.assertEqual(s["byte_identical_rerender"], 1680, style)
        self.assertTrue(p["fired"])

    def test_p_vo5_slot_identities(self) -> None:
        p = self.report["P-VO5"]
        self.assertEqual(p["distinct_id_sets"], 1)
        self.assertEqual(p["distinct_role_maps"], 1)
        self.assertEqual(p["ids_containing_digits"], [])
        self.assertTrue(p["fired"])

    def test_p_vo6_derived_redundancy(self) -> None:
        p = self.report["P-VO6"]
        self.assertEqual(p["verdict_changes"], 0)
        self.assertEqual(p["derived_fired_while_gate_passed"], 0)
        # correction C1: the registered wording is only falsifiable on the
        # valids, so the report must also carry the number that has content
        self.assertEqual(p["valids_scored"], 240)
        self.assertGreater(p["derived_fired_on_invalids"], 0)
        self.assertTrue(p["fired"])

    def test_p_vo7_no_surface_baseline_solves_a_class(self) -> None:
        p = self.report["P-VO7"]
        self.assertLess(p["max_balanced_accuracy"], 1.0)
        self.assertLess(p["max_best_threshold_balanced_accuracy"], 1.0)
        self.assertTrue(p["element_count_at_chance"])
        self.assertTrue(p["fired"])

    def test_blind_baselines_can_still_see_something(self) -> None:
        """Anti-vacuity for the anti-vacuity control.

        A surface feature that is constant on every instance would 'prove'
        the invalid set is hard by being blind. At least one baseline must
        separate better than chance on at least one class.
        """
        blind = blind_baselines(small_corpus())
        best = max(c["balanced_accuracy"] for b in blind.values()
                   for c in b["per_class"].values())
        self.assertGreater(best, 0.5)
        feats = [surface_features(render_svg(i.graph, "plain"))
                 for i in small_corpus()]
        self.assertGreater(len({f["coord_magnitude"] for f in feats}), 1)

    def test_all_registered_predictions_fired(self) -> None:
        self.assertTrue(self.report["all_fired"])


if __name__ == "__main__":
    unittest.main()
