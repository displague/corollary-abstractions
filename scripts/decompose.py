#!/usr/bin/env python3
"""Derivational composition: read each statement as a construct of known forms.

The matchers relate WHOLE statements; this tool walks every statement's
canonical tree and asks, for each constituent subterm, "which known form is
this an instance of?" — where the form inventory is (a) the expression-side
skeletons of every corpus statement and (b) recurring subterm families
across statements. Output: per-statement decompositions ("the SSM update's
right side is two scaled-linear constituents joined by +"), i.e. statements
as constructs of other forms — commitment #1 of docs/DESIGN-concept-tokens.md
made mechanical, and the substrate for composing new mathematically grounded
statements from named parts.

Constituents are matched at the typed level (parameter/variable categories
respected). Trivial subterms (single leaves) are excluded; a constituent
reports every statement whose expression side shares its skeleton, plus how
many corpus statements contain it as a subterm.

Groundedness v2 repairs two MEASURED pathologies of the v1 score (both in
docs/BACKLOG.md):

1. *An instance graded less grounded than its pattern.*
   `narrative.constraint.chekhov_gun` scored 0.000 while the abstraction it
   instantiates, `temporal.response.response_pattern`, scored 0.500 — because
   exact skeleton lookup sees `EVENTUALLY⟨DISCHARGED⟨?0⟩⟩` and
   `EVENTUALLY⟨?0⟩` as unrelated strings. A constituent that fails exact
   lookup is now re-tried with the specialize.py matcher, every known form
   used AS PATTERN against it, so a pattern slot may bind the constituent's
   instantiated call subtree. Counted separately as `grounded_via_pattern`.

2. *Recursive definitions graded 0.000, i.e. as gibberish.*
   `temporal.recurrence.until_unfolding` defines UNTIL in terms of itself, so
   every constituent carried the head being defined and none could be found in
   an inventory built from *other* statements. A statement whose definiendum
   head recurs in the other side of the relation is marked `recursive`, and
   its self-headed constituents leave the denominator: they are definitional,
   not ungrounded.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from match_signatures import (
    Parser, TemplateParseError, canonicalize, load_nodes, skeleton,
    slot_classes, tokenize,
)
from specialize import MatchState, match, op_count


def subterms(t: tuple, path: tuple = ()):
    """Yield (path, subtree) for every non-leaf subtree, including relation
    sides but not the relation itself."""
    if t[0] == "rel":
        for i, side in enumerate(t[2]):
            yield from subterms(side, path + (i,))
        return
    if t[0] in {"op", "call"}:
        yield path, t
        for i, a in enumerate(t[2]):
            yield from subterms(a, path + (i,))


def tree_size(t: tuple) -> int:
    if t[0] in {"slot", "num"}:
        return 1
    if t[0] == "rel":
        return sum(tree_size(a) for a in t[2])
    return 1 + sum(tree_size(a) for a in t[2])


def head_of(t: tuple) -> tuple | None:
    """(kind, name) for an applied node; None for leaves and relations."""
    return (t[0], t[1]) if t[0] in {"op", "call"} else None


def contains_head(t: tuple, head: tuple) -> bool:
    if t[0] in {"slot", "num"}:
        return False
    if head_of(t) == head:
        return True
    return any(contains_head(a, head) for a in t[2])


def defined_head(t: tuple) -> tuple | None:
    """The head a statement recursively defines, or None.

    A recursive definition has a *definiendum* side — a bare application of one
    named head to leaves, `UNTIL(PROPA, PROPB)` — whose head occurs again on
    the other side, under a different head. Both sides are tested because
    `canonicalize` sorts the operands of `=` by shape, so the definiendum is
    not reliably the left one.

    Three guards keep this to actual recursion; each was measured firing on the
    corpus when absent:

    - `call` heads only. `HYP^2 = LEG1^2 + LEG2^2` otherwise "defines" `^`, and
      the ideal gas law "defines" `*`. Arithmetic operators are shared
      vocabulary, never a definiendum.
    - the other side's root head must differ. Otherwise `ALWAYS(ALWAYS(P)) =
      ALWAYS(P)` (idempotence), `CATEGORY(CONCAT(STEM, AFFIX)) =
      CATEGORY(STEM)` (preservation) and contraposition read as definitions of
      their own head and empty their denominators.
    - the head must occur *below* the other side's root, which the previous
      guard implies but `EULERCHAR(M) = EULERCHAR(N)` (invariance under
      diffeomorphism) makes worth stating: same head both sides, no recursion.
    """
    if t[0] != "rel":
        return None
    for i, side in enumerate(t[2]):
        other = t[2][1 - i]
        if side[0] != "call" or not side[2]:
            continue
        if any(a[0] not in {"slot", "num"} for a in side[2]):
            continue
        head = head_of(side)
        if head_of(other) == head or other[0] not in {"op", "call"}:
            continue
        if any(contains_head(a, head) for a in other[2]):
            return head
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    ap.add_argument("--min-family", type=int, default=2,
                    help="a subterm family counts if it recurs in >= this many statements")
    ap.add_argument("--max-pattern-attempts", type=int, default=250,
                    help="cap on known forms tried as patterns per constituent")
    ap.add_argument("--no-pattern-membership", action="store_true",
                    help="disable v2 pattern matching (exact skeleton lookup only)")
    ap.add_argument("--write-report", type=Path, default=None)
    args = ap.parse_args()

    nodes, _ = load_nodes(args.data_dir)

    # Rebuild trees + slot classes (load_nodes keeps only skeleton strings).
    trees: dict[str, tuple] = {}
    classes: dict[str, dict[str, str]] = {}
    for corpus_path in sorted(args.data_dir.glob("*/nodes.json")):
        corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
        for nj in corpus.get("statement_nodes", []):
            sid = nj.get("statement_id")
            tmpl = nj.get("structural_signature", {}).get("anonymized_template", "")
            try:
                trees[sid] = canonicalize(Parser(tokenize(tmpl)).parse())
            except TemplateParseError:
                continue
            classes[sid] = slot_classes(nj)

    # Form inventory 1: expression-side skeletons of whole statements.
    # `form_rep` keeps one concrete (tree, slot_class) witness per skeleton so
    # the form can later be used as a *pattern* by specialize.py's matcher.
    side_forms: dict[str, list[str]] = defaultdict(list)
    form_rep: dict[str, tuple[tuple, dict[str, str]]] = {}
    for n in nodes:
        t = trees.get(n.statement_id)
        if t is None:
            continue
        sides = t[2] if t[0] == "rel" else (t,)
        for side in sides:
            if side[0] in {"op", "call"}:
                skel = skeleton(side, classes[n.statement_id])
                side_forms[skel].append(n.statement_id)
                form_rep.setdefault(skel, (side, classes[n.statement_id]))

    # Form inventory 2: recurring subterm families across statements.
    subterm_hosts: dict[str, set] = defaultdict(set)
    for n in nodes:
        t = trees.get(n.statement_id)
        if t is None:
            continue
        for _, sub in subterms(t):
            if tree_size(sub) < 2:
                continue
            skel = skeleton(sub, classes[n.statement_id])
            subterm_hosts[skel].add(n.statement_id)
            form_rep.setdefault(skel, (sub, classes[n.statement_id]))

    # Pattern index for v2 grounding: known forms bucketed by root head, so a
    # constituent only ever tries the forms that could possibly match it.
    forms_by_head: dict[tuple, list[tuple]] = defaultdict(list)
    for skel, (tree, cls) in form_rep.items():
        owners = set(side_forms.get(skel, ())) | subterm_hosts.get(skel, set())
        forms_by_head[head_of(tree)].append(
            (op_count(tree), skel, tree, cls, owners))
    for bucket in forms_by_head.values():
        bucket.sort(key=lambda f: (-f[0], f[1]))  # most specific pattern first

    def known_form(skel: str, exclude: str) -> bool:
        """The v1 grounding test, reused to keep patterns to *known* forms."""
        if set(side_forms.get(skel, ())) - {exclude}:
            return True
        return len(subterm_hosts.get(skel, set())) >= args.min_family

    def pattern_cover(sub: tuple, own_skel: str, sid: str) -> tuple | None:
        """Find a known form that covers `sub` when read as a pattern.

        This is the fix for "an instance grades less grounded than its
        pattern": `EVENTUALLY⟨?0⟩` is a known form and Chekhov's gun's
        `EVENTUALLY⟨DISCHARGED⟨?0⟩⟩` is that form with the slot instantiated,
        which exact skeleton lookup cannot see.

        The accepted evidence is exactly the recorded pathology: some slot of
        the known form binds a *named-head application*. Weaker matches are
        refused on purpose —

        - slot-to-slot renaming is a twin, not a membership, and accepting it
          would silently grade P-vs-V category mismatches as grounding;
        - absorbing extra commutative arguments or vanishing a parameter into
          an identity element is *specialization*, which `specialize.py`
          already reports and where its recorded noise lives. Allowing it
          moves the corpus mean by +0.003 and is therefore not worth the
          justifications it prints: Beer-Lambert's `?0:P * ?1:V * ?2:V` was
          credited with grounding `?0:P * D⟨?1:V⟩` by letting a factor
          disappear, where the honest citation is the plain product form.
        """
        budget = args.max_pattern_attempts
        limit = op_count(sub)
        for pop, skel, tree, cls, owners in forms_by_head.get(head_of(sub), ()):
            if budget <= 0:
                break
            if pop > limit or skel == own_skel or not owners - {sid}:
                continue
            if not known_form(skel, sid):
                continue
            budget -= 1
            st = MatchState(cls)
            if (match(tree, sub, st)
                    and not (st.used_absorption or st.used_identity)
                    and any(v[0] == "call" for v in st.binds.values())):
                return skel, sorted(owners - {sid})
        return None

    decompositions = []
    for n in nodes:
        t = trees.get(n.statement_id)
        if t is None:
            continue
        cls = classes[n.statement_id]
        constituents = []
        n_considered = 0
        n_exact = 0
        n_pattern = 0
        n_self = 0
        self_head = defined_head(t)
        atomic = not any(path for path, _ in subterms(t))
        for path, sub in subterms(t):
            # Atomic statements (single call over leaves) are graded by their
            # root -- otherwise they fall off the ladder entirely (falsum
            # agent's finding: ex falso had no groundedness rung at all).
            if not path and not atomic:
                continue
            # A recursive definition's own head is definitional, not
            # ungrounded: the inventory is built from *other* statements, so
            # UNTIL cannot appear in it while UNTIL is being defined. Such
            # constituents leave the denominator instead of failing it.
            if self_head is not None and head_of(sub) == self_head:
                n_self += 1
                continue
            skel = skeleton(sub, cls)
            named = sorted(set(side_forms.get(skel, [])) - {n.statement_id})
            hosts = subterm_hosts.get(skel, set())
            n_considered += 1
            if named or len(hosts) >= args.min_family:
                n_exact += 1
                constituents.append({
                    "path": list(path),
                    "skeleton": skel,
                    "grounded_via": "exact",
                    "instance_of_statements": named[:8],
                    "recurs_in_n_statements": len(hosts),
                })
                continue
            cover = None if args.no_pattern_membership else pattern_cover(
                sub, skel, n.statement_id)
            if cover is None:
                continue
            n_pattern += 1
            pat_skel, pat_owners = cover
            constituents.append({
                "path": list(path),
                "skeleton": skel,
                "grounded_via": "pattern",
                "instance_of_pattern": pat_skel,
                "pattern_known_from": pat_owners[:8],
                "pattern_recurs_in_n_statements": len(pat_owners),
            })
        # Groundedness: the epistemic-ladder grade for "disorder" — fraction
        # of non-trivial constituents matching known forms, exactly or as
        # instances of a known pattern. 1.0 = every piece is a named/recurring
        # form; low values shade toward gibberish.
        n_grounded = n_exact + n_pattern
        score = round(n_grounded / n_considered, 3) if n_considered else 1.0
        if constituents or n_considered or n_self:
            entry = {
                "statement_id": n.statement_id,
                "template": n.template,
                "groundedness": score,
                "considered": n_considered,
                "grounded_exact": n_exact,
                "grounded_via_pattern": n_pattern,
                "constituents": constituents,
            }
            if self_head is not None:
                entry["recursive"] = True
                entry["defines_head"] = self_head[1]
                entry["self_headed_constituents_excluded"] = n_self
            decompositions.append(entry)

    n_with = sum(1 for d in decompositions if d["constituents"])
    n_named = sum(1 for d in decompositions
                  if any(c.get("instance_of_statements")
                         for c in d["constituents"]))
    scores = [d["groundedness"] for d in decompositions]
    mean_score = sum(scores) / len(scores) if scores else 0.0
    lowest = sorted(decompositions, key=lambda d: d["groundedness"])[:3]
    print(f"{n_with} of {len(nodes)} statements decompose into known forms; "
          f"{n_named} contain a constituent that IS another statement's "
          f"expression side.")
    print("Corpus mean groundedness: "
          f"{mean_score:.3f}; least grounded: "
          + ", ".join(f"{d['statement_id']} ({d['groundedness']})"
                      for d in lowest))
    n_exact_total = sum(d["grounded_exact"] for d in decompositions)
    n_pattern_total = sum(d["grounded_via_pattern"] for d in decompositions)
    print(f"Grounded constituents: {n_exact_total} exact, {n_pattern_total} "
          f"via pattern membership (a known form with a slot instantiated).")
    recursives = [d for d in decompositions if d.get("recursive")]
    if recursives:
        print("Recursive definitions (self-headed constituents excluded from "
              "the denominator): "
              + ", ".join(f"{d['statement_id']} defines {d['defines_head']}, "
                          f"{d['groundedness']}" for d in recursives))
    print()

    # Show the ones whose constituents are named statements — the
    # 'built from lemmas' readout.
    shown = 0
    for d in decompositions:
        named_cs = [c for c in d["constituents"]
                    if c.get("instance_of_statements")]
        if not named_cs or shown >= 20:
            continue
        shown += 1
        print(f"  {d['statement_id']}")
        print(f"    template: {d['template']}")
        for c in named_cs:
            others = ", ".join(c["instance_of_statements"][:3])
            more = ("..." if len(c["instance_of_statements"]) > 3 else "")
            print(f"    constituent at {c['path']}: {c['skeleton']}")
            print(f"      = expression side of: {others}{more} "
                  f"(recurs in {c['recurs_in_n_statements']} statements)")
        print()

    # The v2 readout: constituents that are a known form with a slot
    # instantiated — the membership exact skeleton lookup could not see.
    pattern_rows = [(d, c) for d in decompositions for c in d["constituents"]
                    if c["grounded_via"] == "pattern"]
    if pattern_rows:
        print(f"## Pattern membership ({len(pattern_rows)} constituents; "
              f"first 20)")
        for d, c in pattern_rows[:20]:
            print(f"  {d['statement_id']} at {c['path']}: {c['skeleton']}")
            known = ", ".join(c["pattern_known_from"][:3])
            n_from = c["pattern_recurs_in_n_statements"]
            print(f"    instantiates {c['instance_of_pattern']} "
                  f"(known from {n_from} statement{'' if n_from == 1 else 's'}"
                  f": {known})")
        print()

    if args.write_report:
        args.write_report.parent.mkdir(parents=True, exist_ok=True)
        args.write_report.write_text(json.dumps(
            {"decompositions": decompositions}, indent=2, ensure_ascii=False)
            + "\n", encoding="utf-8")
        print(f"Report written to {args.write_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
