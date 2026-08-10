"""Seeded corpus generator and the adjudication harness for steps 1-5.

Subcommands
-----------

``generate``   write the corpus (JSONL, text only) to an out-dir
``adjudicate`` run the registered protocol and emit the verdict report
``fixtures``   regenerate the committed byte-level fixture set

Artifact policy: bulk output is regenerable from this file plus a seed and
never enters git (``experiments/visual/out/`` is ignored). A single figure's
SVG/JSON is committed under ``fixtures/`` because it is a few kilobytes of
diffable text and it is the only way a silent change to the emitted byte
format shows up in review -- the same argument that makes
``check_regeneration.py`` byte-exact for the corpora. Nothing binary is
committed anywhere.

Determinism: parameters are drawn from ``random.Random(seed)`` and everything
downstream of the draw is a pure function. Splits come from an md5 of the
parameter signature rather than ``hash()``, whose per-process randomization
would break regeneration from seeds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

if __package__ in (None, ""):  # allow `python experiments/visual/genvisual.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    __package__ = "visual"

from .mutate import (INVALID_CLASSES, Instance, REGISTERED_GATE,  # noqa: E402
                     instances_for)
from .parse import parse_svg  # noqa: E402
from .render import STYLES, render_svg  # noqa: E402
from .scene import (ROLE_TO_ANGLE, ROLE_TO_EDGE, ROLE_TO_VERTEX,  # noqa: E402
                    TriangleParams, fmt, normalize, to_dict)
from .verify import (DERIVED_CHECKS, DERIVED_IMPLIED_BY,  # noqa: E402
                     GATED_CHECKS, verify)

# Primitive leg directions. q/p controls the exact near-miss angle
# 2*atan(q/p), which spans 1.53 to 16.26 degrees over this pool; p != q keeps
# the near-miss non-degenerate.
DIRECTIONS = ((7, 1), (8, 1), (9, 1), (11, 1), (12, 1), (13, 1), (15, 1),
              (16, 1), (19, 1), (21, 1), (25, 1), (31, 1), (49, 1), (60, 1),
              (75, 1), (15, 2), (17, 2), (21, 2), (25, 2), (27, 2), (35, 2),
              (25, 3), (28, 3), (35, 3), (40, 3), (35, 4), (45, 4))
LEG_UNITS = (2, 3, 4, 5, 6, 8, 10, 12)
ORIGINS = tuple(range(0, 100, 10))
DEFAULT_N = 240
DEFAULT_SEED = 11
DEFAULT_STYLES = ("plain", "bold", "sparse")


def split_for(signature: str) -> str:
    """md5-stable split (not ``hash()``: that is process-randomized)."""
    b = hashlib.md5(signature.encode()).digest()[0] % 100
    return "test" if b < 15 else "val" if b < 30 else "train"


def draw_params(n: int, seed: int) -> list[TriangleParams]:
    import random
    rng = random.Random(seed)
    seen: set[str] = set()
    out: list[TriangleParams] = []
    attempts = 0
    while len(out) < n and attempts < n * 200:
        attempts += 1
        p, q = rng.choice(DIRECTIONS)
        params = TriangleParams(p=p, q=q,
                                m=rng.choice(LEG_UNITS),
                                n=rng.choice(LEG_UNITS),
                                ox=rng.choice(ORIGINS),
                                oy=rng.choice(ORIGINS),
                                hand=rng.choice((1, -1)),
                                dih=rng.randrange(4))
        sig = params.signature()
        if sig in seen:
            continue
        seen.add(sig)
        out.append(params)
    if len(out) < n:  # pragma: no cover - pool is far larger than any n used
        raise RuntimeError(f"only {len(out)} distinct figures for n={n}")
    return out


def build_corpus(n: int = DEFAULT_N, seed: int = DEFAULT_SEED
                 ) -> list[Instance]:
    corpus: list[Instance] = []
    for i, params in enumerate(draw_params(n, seed)):
        figure_id = f"rt-{i:04d}"
        corpus.extend(instances_for(params, figure_id,
                                    split_for(params.signature())))
    return corpus


def instance_row(inst: Instance, styles=DEFAULT_STYLES) -> dict:
    res = verify(inst.graph, inst.claim)
    return {
        "instance_id": inst.instance_id,
        "figure_id": inst.figure_id,
        "family": inst.graph.family,
        "kind": inst.kind,
        "label": 1 if inst.expected_valid else 0,
        "split": inst.split,
        "params": {"p": inst.params.p, "q": inst.params.q,
                   "m": inst.params.m, "n": inst.params.n,
                   "ox": inst.params.ox, "oy": inst.params.oy,
                   "hand": inst.params.hand, "dih": inst.params.dih,
                   "near_miss_degrees": round(inst.params.epsilon_degrees, 6)},
        "claim": inst.claim.to_dict(),
        "scene": to_dict(inst.graph),
        "mutation": inst.mutation.to_dict() if inst.mutation else None,
        "verdict": res.to_dict(),
        "svg": {s: render_svg(inst.graph, s) for s in styles},
    }


# --------------------------------------------------------------------------
# Capability-blind surface baselines (P-VO7)
# --------------------------------------------------------------------------

_ATTR = re.compile(r'([A-Za-z][\w-]*)="([^"]*)"')
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
# Attributes whose values are numeric. Reading numbers out of these rather
# than out of the whole document is what keeps the baseline honest: the first
# implementation of this feature matched the "2000" in the SVG namespace URI,
# scored a constant on every figure, and was therefore blind by accident
# rather than by result. A control that cannot see is not a control.
_NUMERIC_ATTRS = frozenset({"x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r",
                            "width", "height", "viewBox", "d", "font-size",
                            "stroke-width"})

SURFACE_FEATURES = ("element_count", "byte_length", "coord_magnitude")


def surface_features(svg: str) -> dict[str, float]:
    coords = [abs(float(n)) for key, val in _ATTR.findall(svg)
              if key in _NUMERIC_ATTRS for n in _NUMBER.findall(val)]
    return {
        "element_count": float(svg.count('data-sid="')),
        "byte_length": float(len(svg)),
        "coord_magnitude": max(coords, default=0.0),
    }


def _best_threshold_balanced_accuracy(neg: list[float],
                                      pos: list[float]) -> float:
    """Best balanced accuracy any threshold rule could reach, tuned on the
    very data it is scored on. Deliberately unfair to the oracle."""
    best = 0.5
    cuts = sorted(set(neg) | set(pos))
    for t in cuts:
        for sign in (1, -1):
            tp = sum(1 for v in pos if v * sign > t * sign)
            tn = sum(1 for v in neg if v * sign <= t * sign)
            best = max(best, (tp / len(pos) + tn / len(neg)) / 2)
    return best


def blind_baselines(corpus: list[Instance], style: str = "plain") -> dict:
    """Reject anything whose feature value was never seen among valids.

    Fitting and scoring on the same valid set gives every baseline a zero
    false-positive rate by construction. That is deliberate: the control is
    only informative if it is handed the most favourable possible reading.
    The novelty rule is the optimal zero-false-positive rule for a discrete
    feature; ``best_threshold_balanced_accuracy`` additionally reports what
    an oracle-tuned threshold could do with the false-positive constraint
    lifted, which is strictly stronger than the registered P-VO7 wording.
    """
    feats = {inst.instance_id: surface_features(render_svg(inst.graph, style))
             for inst in corpus}
    valids = [i for i in corpus if i.expected_valid]
    seen = {name: {feats[v.instance_id][name] for v in valids}
            for name in SURFACE_FEATURES}
    report: dict[str, dict] = {}
    for name, allowed in seen.items():
        neg = [feats[v.instance_id][name] for v in valids]
        fpr = sum(1 for v in neg if v not in allowed) / len(neg)
        per_class = {}
        for cls in INVALID_CLASSES:
            rows = [i for i in corpus if i.kind == cls]
            pos = [feats[r.instance_id][name] for r in rows]
            tpr = sum(1 for v in pos if v not in allowed) / len(pos)
            per_class[cls] = {
                "detected": round(tpr, 6),
                "balanced_accuracy": round((tpr + 1 - fpr) / 2, 6),
                "best_threshold_balanced_accuracy":
                    round(_best_threshold_balanced_accuracy(neg, pos), 6)}
        report[name] = {"false_positive_rate": round(fpr, 6),
                        "distinct_values_among_valids": len(allowed),
                        "per_class": per_class}
    return report


# --------------------------------------------------------------------------
# Adjudication
# --------------------------------------------------------------------------

def adjudicate(corpus: list[Instance], styles=DEFAULT_STYLES) -> dict:
    valids = [i for i in corpus if i.expected_valid]
    report: dict = {"n_figures": len(valids), "n_instances": len(corpus),
                    "styles": list(styles),
                    "invalid_classes": list(INVALID_CLASSES),
                    "gated_checks": list(GATED_CHECKS),
                    "derived_checks": list(DERIVED_CHECKS)}

    # P-VO1 / P-VO2 -------------------------------------------------------
    accepted = sum(1 for i in valids if verify(i.graph, i.claim).ok)
    report["P-VO1"] = {"valids": len(valids), "accepted": accepted,
                       "rate": accepted / len(valids),
                       "fired": accepted == len(valids)}
    per_class = {}
    diagonal = True
    for cls in INVALID_CLASSES:
        rows = [i for i in corpus if i.kind == cls]
        gates: dict[str, int] = {}
        rejected = 0
        for r in rows:
            res = verify(r.graph, r.claim)
            rejected += 0 if res.ok else 1
            key = ",".join(sorted(res.failed_checks)) or "<none>"
            gates[key] = gates.get(key, 0) + 1
        want = REGISTERED_GATE[cls]
        exact = gates.get(want, 0)
        diagonal = diagonal and exact == len(rows)
        per_class[cls] = {"n": len(rows), "rejected": rejected,
                          "rate": rejected / len(rows),
                          "registered_gate": want,
                          "observed_failing_check_sets": gates,
                          "exactly_registered_gate": exact}
    report["P-VO2"] = {"per_class": per_class, "diagonal": diagonal,
                       "fired": diagonal and all(
                           c["rejected"] == c["n"]
                           for c in per_class.values())}

    # P-VO3: ablation ------------------------------------------------------
    ablation: dict[str, dict] = {}
    ablation_fired = True
    for check in GATED_CHECKS:
        off = (check,)
        valid_ok = sum(1 for i in valids if verify(i.graph, i.claim, off).ok)
        escapes = {}
        for cls in INVALID_CLASSES:
            rows = [i for i in corpus if i.kind == cls]
            passed = sum(1 for r in rows
                         if verify(r.graph, r.claim, off).ok)
            escapes[cls] = {"n": len(rows), "passed_when_disabled": passed,
                            "rate": passed / len(rows)}
        gated_class = next(c for c, g in REGISTERED_GATE.items()
                           if g == check)
        load_bearing = (escapes[gated_class]["passed_when_disabled"]
                        == escapes[gated_class]["n"])
        others_held = all(e["passed_when_disabled"] == 0
                          for c, e in escapes.items() if c != gated_class)
        ablation_fired = (ablation_fired and load_bearing and others_held
                          and valid_ok == len(valids))
        ablation[check] = {"uniquely_gates": gated_class,
                           "valids_still_accepted": valid_ok,
                           "load_bearing": load_bearing,
                           "other_classes_still_rejected": others_held,
                           "per_class_escape": escapes}
    report["P-VO3"] = {"per_check": ablation, "fired": ablation_fired}

    # P-VO4: round trip ----------------------------------------------------
    rt = {}
    rt_fired = True
    for style in styles:
        graph_eq = verdict_eq = byte_eq = 0
        for inst in corpus:
            svg = render_svg(inst.graph, style)
            parsed = parse_svg(svg)
            graph_eq += parsed == normalize(inst.graph)
            src = verify(inst.graph, inst.claim)
            dst = verify(parsed, inst.claim)
            verdict_eq += (src.ok == dst.ok
                           and src.failed_checks == dst.failed_checks)
            byte_eq += render_svg(parsed, style) == svg
        rt[style] = {"n": len(corpus), "graph_equal": graph_eq,
                     "verdict_equal": verdict_eq,
                     "byte_identical_rerender": byte_eq}
        rt_fired = (rt_fired
                    and graph_eq == verdict_eq == byte_eq == len(corpus))
    report["P-VO4"] = {"per_style": rt,
                       "round_trips": len(corpus) * len(styles),
                       "fired": rt_fired}

    # P-VO5: stable identities --------------------------------------------
    expected_map = {"vertices": ROLE_TO_VERTEX, "edges": ROLE_TO_EDGE,
                    "angles": ROLE_TO_ANGLE}
    id_sets = set()
    role_maps = set()
    coord_leak = []
    for inst in corpus:
        g = inst.graph
        id_sets.add(frozenset(e.id for e in (*g.vertices, *g.edges,
                                             *g.angles)))
        role_maps.add((tuple(sorted((v.role, v.id) for v in g.vertices)),
                       tuple(sorted((e.role, e.id) for e in g.edges)),
                       tuple(sorted((a.role, a.id) for a in g.angles))))
        for el in (*g.vertices, *g.edges, *g.angles):
            if any(ch.isdigit() for ch in el.id):
                coord_leak.append(el.id)
    only_map = (len(role_maps) == 1)
    matches_registry = only_map and all(
        dict(next(iter(role_maps))[i]) == expected_map[k]
        for i, k in enumerate(("vertices", "edges", "angles")))
    report["P-VO5"] = {"distinct_id_sets": len(id_sets),
                       "distinct_role_maps": len(role_maps),
                       "matches_registered_map": matches_registry,
                       "ids_containing_digits": sorted(set(coord_leak)),
                       "fired": (len(id_sets) == 1 and only_map
                                 and matches_registry and not coord_leak)}

    # P-VO6: derived checks are verdict-redundant --------------------------
    # As registered, "never changes a verdict" is a theorem on the invalids:
    # the derived set is a superset of the gated set, so ok can only go
    # True->False, and every invalid is already False. The registered number
    # is kept (predictions are corrected by attachment, not by rewriting),
    # and the sharper statistics that carry the real content are added
    # beside it: how often a derived check fires on an invalid the gate
    # already caught, and whether one ever fires on a valid.
    changed = []
    fires_without_gate = []
    fired_on_invalid = []
    without_implier = []
    for inst in corpus:
        base = verify(inst.graph, inst.claim)
        with_derived = verify(inst.graph, inst.claim, derived=True)
        if base.ok != with_derived.ok:
            changed.append(inst.instance_id)
        derived_fired = [f.check for f in with_derived.failures
                         if f.check in DERIVED_CHECKS]
        if derived_fired and base.ok:
            fires_without_gate.append(inst.instance_id)
        if derived_fired and not inst.expected_valid:
            fired_on_invalid.append(inst.instance_id)
        for name in set(derived_fired):
            if not set(DERIVED_IMPLIED_BY[name]) & set(base.failed_checks):
                without_implier.append(f"{inst.instance_id}:{name}")
    invalids = len(corpus) - len(valids)
    report["P-VO6"] = {"verdict_changes": len(changed),
                       "derived_fired_while_gate_passed":
                           len(fires_without_gate),
                       "derived_fired_on_invalids": len(fired_on_invalid),
                       "derived_fired_without_its_implier":
                           len(without_implier),
                       "invalids": invalids,
                       "valids_scored": len(valids),
                       "note": "verdict_changes is provably zero on the "
                               "invalids (derived is a superset of gated, "
                               "so ok can only go True->False and every "
                               "invalid is already False); the measured "
                               "content is that no derived check fires on "
                               "any of the valids, while "
                               f"{len(fired_on_invalid)}/{invalids} invalids "
                               "do trip one on top of a gated failure",
                       "examples": (changed[:5] + fires_without_gate[:5]
                                    + without_implier[:5]),
                       "fired": (not changed and not fires_without_gate
                                 and not without_implier)}

    # P-VO7: capability-blind surface baselines ----------------------------
    # Every style, not just the default: a baseline that fails on `plain`
    # and succeeds on `bold` would still make the negative set too easy.
    blind = {style: blind_baselines(corpus, style) for style in styles}
    worst = max(c["balanced_accuracy"] for s in blind.values()
                for b in s.values() for c in b["per_class"].values())
    worst_thr = max(c["best_threshold_balanced_accuracy"]
                    for s in blind.values() for b in s.values()
                    for c in b["per_class"].values())
    elem_chance = all(
        abs(c["balanced_accuracy"] - 0.5) < 1e-9 for s in blind.values()
        for c in s["element_count"]["per_class"].values())
    report["P-VO7"] = {"baselines_by_style": blind,
                       "baselines": blind[styles[0]],
                       "max_balanced_accuracy": worst,
                       "max_best_threshold_balanced_accuracy": worst_thr,
                       "element_count_at_chance": elem_chance,
                       "fired": (worst < 1.0 and worst_thr < 1.0
                                 and elem_chance)}

    report["all_fired"] = all(report[k]["fired"] for k in
                              ("P-VO1", "P-VO2", "P-VO3", "P-VO4", "P-VO5",
                               "P-VO6", "P-VO7"))
    return report


def format_report(rep: dict) -> str:
    lines = [f"figures={rep['n_figures']} instances={rep['n_instances']} "
             f"styles={','.join(rep['styles'])}", ""]
    p1 = rep["P-VO1"]
    lines.append(f"P-VO1 acceptance      {p1['accepted']}/{p1['valids']} "
                 f"-> {'FIRED' if p1['fired'] else 'MISSED'}")
    p2 = rep["P-VO2"]
    lines.append(f"P-VO2 rejection       "
                 f"{'FIRED' if p2['fired'] else 'MISSED'}")
    for cls, c in p2["per_class"].items():
        lines.append(f"    {cls:<24} {c['rejected']}/{c['n']} rejected; "
                     f"exactly [{c['registered_gate']}]: "
                     f"{c['exactly_registered_gate']}/{c['n']}")
    p3 = rep["P-VO3"]
    lines.append(f"P-VO3 ablation        "
                 f"{'FIRED' if p3['fired'] else 'MISSED'}")
    for check, a in p3["per_check"].items():
        esc = a["per_class_escape"][a["uniquely_gates"]]
        lines.append(f"    disable {check:<17} -> {a['uniquely_gates']} "
                     f"passes {esc['passed_when_disabled']}/{esc['n']}; "
                     f"others held: {a['other_classes_still_rejected']}; "
                     f"valids kept: {a['valids_still_accepted']}")
    p4 = rep["P-VO4"]
    lines.append(f"P-VO4 round trip      "
                 f"{'FIRED' if p4['fired'] else 'MISSED'} "
                 f"({p4['round_trips']} round trips)")
    for style, s in p4["per_style"].items():
        lines.append(f"    {style:<8} graph={s['graph_equal']}/{s['n']} "
                     f"verdict={s['verdict_equal']}/{s['n']} "
                     f"bytes={s['byte_identical_rerender']}/{s['n']}")
    p5 = rep["P-VO5"]
    verdict5 = 'FIRED' if p5['fired'] else 'MISSED'
    lines.append(f"P-VO5 slot identities {verdict5}"
                 f" (id sets={p5['distinct_id_sets']}, role maps="
                 f"{p5['distinct_role_maps']})")
    p6 = rep["P-VO6"]
    verdict6 = 'FIRED' if p6['fired'] else 'MISSED'
    lines.append(f"P-VO6 derived redundant {verdict6}"
                 f" (verdict changes={p6['verdict_changes']}; measured on "
                 f"{p6['valids_scored']} valids -- "
                 f"{p6['derived_fired_on_invalids']}/{p6['invalids']} "
                 f"invalids trip a derived check atop a gated failure)")
    p7 = rep["P-VO7"]
    verdict7 = 'FIRED' if p7['fired'] else 'MISSED'
    lines.append(f"P-VO7 blind baselines {verdict7}"
                 f" (max balanced accuracy={p7['max_balanced_accuracy']:.3f}, "
                 f"oracle-threshold max="
                 f"{p7['max_best_threshold_balanced_accuracy']:.3f})")
    for name, b in p7["baselines"].items():
        cells = " ".join(f"{c['balanced_accuracy']:.3f}"
                         for c in b["per_class"].values())
        thr = " ".join(f"{c['best_threshold_balanced_accuracy']:.3f}"
                       for c in b["per_class"].values())
        lines.append(f"    {name:<16} novelty  {cells}")
        lines.append(f"    {'':<16} oracle   {thr}")
    lines.append("")
    overall = "FIRED" if rep["all_fired"] else "MISSED"
    lines.append(f"ALL PREDICTIONS {overall}")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

FIXTURE_FIGURE = 0
FIXTURE_CLASS = "right_angle_epsilon"


def write_fixtures(out_dir: Path, seed: int = DEFAULT_SEED) -> list[Path]:
    params = draw_params(FIXTURE_FIGURE + 1, seed)[FIXTURE_FIGURE]
    figure_id = f"rt-{FIXTURE_FIGURE:04d}"
    insts = instances_for(params, figure_id, split_for(params.signature()))
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    def _write(name: str, text: str) -> None:
        path = out_dir / name
        path.write_text(text, encoding="utf-8", newline="\n")
        written.append(path)

    valid = insts[0]
    for style in DEFAULT_STYLES:
        _write(f"{figure_id}.{style}.svg", render_svg(valid.graph, style))
    _write(f"{figure_id}.scene.json",
           json.dumps(to_dict(valid.graph), indent=2) + "\n")
    near = next(i for i in insts if i.kind == FIXTURE_CLASS)
    _write(f"{figure_id}.{FIXTURE_CLASS}.plain.svg",
           render_svg(near.graph, "plain"))
    _write(f"{figure_id}.{FIXTURE_CLASS}.scene.json",
           json.dumps(to_dict(near.graph), indent=2) + "\n")
    manifest = {
        "generator": "experiments/visual/genvisual.py",
        "seed": seed,
        "figure_id": figure_id,
        "params": {"p": params.p, "q": params.q, "m": params.m,
                   "n": params.n, "ox": params.ox, "oy": params.oy,
                   "hand": params.hand, "dih": params.dih,
                   "signature": params.signature(),
                   "near_miss_degrees": round(params.epsilon_degrees, 6)},
        "instances": [
            {"instance_id": i.instance_id, "kind": i.kind, "split": i.split,
             "claim": i.claim.to_dict(),
             "mutation": i.mutation.to_dict() if i.mutation else None,
             "verdict": verify(i.graph, i.claim).to_dict()}
            for i in insts],
    }
    _write("manifest.json", json.dumps(manifest, indent=2) + "\n")
    return written


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    gen = sub.add_parser("generate", help="write the seeded corpus")
    gen.add_argument("--out-dir", type=Path,
                     default=Path(__file__).resolve().parent / "out")
    gen.add_argument("--n", type=int, default=DEFAULT_N)
    gen.add_argument("--seed", type=int, default=DEFAULT_SEED)
    gen.add_argument("--emit-svg", action="store_true",
                     help="also write one .svg file per instance per style")

    adj = sub.add_parser("adjudicate", help="run the registered protocol")
    adj.add_argument("--out-dir", type=Path,
                     default=Path(__file__).resolve().parent / "out")
    adj.add_argument("--n", type=int, default=DEFAULT_N)
    adj.add_argument("--seed", type=int, default=DEFAULT_SEED)
    adj.add_argument("--no-write", action="store_true")

    fix = sub.add_parser("fixtures", help="regenerate committed fixtures")
    fix.add_argument("--out-dir", type=Path,
                     default=Path(__file__).resolve().parent / "fixtures")
    fix.add_argument("--seed", type=int, default=DEFAULT_SEED)

    args = ap.parse_args(argv)

    if args.cmd == "generate":
        corpus = build_corpus(args.n, args.seed)
        args.out_dir.mkdir(parents=True, exist_ok=True)
        path = args.out_dir / "corpus.jsonl"
        with path.open("w", encoding="utf-8", newline="\n") as f:
            for inst in corpus:
                f.write(json.dumps(instance_row(inst)) + "\n")
        print(f"corpus: {len(corpus)} instances "
              f"({args.n} figures x {1 + len(INVALID_CLASSES)}) -> {path}")
        if args.emit_svg:
            svg_dir = args.out_dir / "svg"
            svg_dir.mkdir(parents=True, exist_ok=True)
            for inst in corpus:
                for style in DEFAULT_STYLES:
                    name = inst.instance_id.replace("/", "__")
                    (svg_dir / f"{name}.{style}.svg").write_text(
                        render_svg(inst.graph, style), encoding="utf-8",
                        newline="\n")
            print(f"svg: {len(corpus) * len(DEFAULT_STYLES)} files -> "
                  f"{svg_dir}")
        return 0

    if args.cmd == "adjudicate":
        corpus = build_corpus(args.n, args.seed)
        rep = adjudicate(corpus)
        rep["seed"] = args.seed
        print(format_report(rep))
        if not args.no_write:
            args.out_dir.mkdir(parents=True, exist_ok=True)
            path = args.out_dir / "report.json"
            path.write_text(json.dumps(rep, indent=2) + "\n",
                            encoding="utf-8", newline="\n")
            print(f"\nreport -> {path}")
        return 0 if rep["all_fired"] else 1

    if args.cmd == "fixtures":
        written = write_fixtures(args.out_dir, args.seed)
        for p in written:
            print(f"fixture -> {p}")
        return 0

    return 2  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main())
