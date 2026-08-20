# Round prompt templates

Use these as structures, not scripts. Replace bracketed fields with plain,
task-specific content. Keep the outside agent isolated from the repository.
Rounds two and three are written AFTER reading the previous round's output —
their value is the main agent reacting to specific proposals, not a form
letter. The v0.16 course (scratchpad `forge16_*` prompts, receipts in
`reports/design-direction-v0.16.json`) is the worked example of this shape.

## Series round 1 — diverge (five directions)

```text
You are an outside advisor to a small research program you have never seen.
Everything you know about it is in this message; no code or data will be
provided. Your value here is precisely that you are outside it.

[The dialect-free brief: thesis, what exists today described by kind rather
than name, measurement culture, standing constraints, the recurring failure
mode.]

[For later series only — EXCLUDED TERRITORY: every round-one direction from
each earlier series, described abstractly, plus an instruction to disclose
and replace any idea that drifts toward one.]

Propose FIVE distinct forward directions. For each, in under 150 words:
(a) the new kind of claim it would make true; (b) why the current shape
cannot make that claim today; (c) a falsifiable construction gate — what,
decided in advance, would count as the idea failing; (d) the cheapest
honest failure. Do not propose [the suspended proxies]. Range widely; at
least one should feel risky to you. Number them with short memorable names.
```

Round one carries no occupied-ground disclosure beyond earlier series'
exclusions: a collision with ground the project already holds is convergent
evidence, recorded at synthesis, and staging the disclosure at round two is
what makes that observation possible.

## Series round 2 — ground (narrow to three)

```text
ROUND 2 — narrowing. The program reacts and adds constraints.

Occupied ground (differentiate or fold; do not re-propose):
[This cycle's incumbent territory, spent instruments, parked directions,
gate-refused directions — each in plain terms.]

Reactions to your five:
[One reaction per proposal, by name: confirmations of what is real, the
denominator it cannot know, the boundary it must sharpen, the fold it
should consider.]

New constraints, all binding:
1. A first slice must fit one release cycle for one maintainer and produce
   a COMMITTED, CHECKABLE ARTIFACT — never a score alone.
2. Outside participation must degrade honestly when nobody shows up;
   "untested" is acceptable, blocking the cycle is not.
3. Every direction names its capability-blind control and what a PERFECT
   control score would void.
4. Every direction states its refusals — adjacent temptations declined in
   writing.

Task: reduce your five to THREE by keeping, merging, or replacing. For each
survivor, under 250 words: first slice as a concrete artifact; construction
gate with numbers where possible; blind control; refusals. Then rank the
three by expected information per unit of effort and defend the ranking.
```

## Series round 3 — pressure-test (one lead)

```text
ROUND 3 — final. The program accepts [or contests] your ranking's logic.

Task: produce this series' FINAL form — ONE lead direction ([name]) and ONE
named runner-up, defended in one sentence.

For the lead, a complete design proposal ready for preregistration, under
700 words: (1) the larger move in two sentences; (2) the first-class
artifact with exact named fields — schema-shaped, no hand-waving; (3) the
construction gate as numbered clauses B1..Bn, every number frozen now;
(4) the blind control and the exact sentence that voids the capability;
(5) stop conditions and non-claims; (6) the question that becomes askable
next if the gate fires.

Do not soften any gate you set in round 2; you may tighten.

Finally: name the single most likely way this direction produces a
plausible-but-wrong artifact that SURVIVES its own gate — the residual risk
the gate does not price, stated plainly.
```

## Exclusion card

```text
Problem boundary: [What relationship or limitation this direction attacks.]
Mechanism: [The essential means, not implementation trivia.]
Success shape: [What new knowledge or human ability would count.]
```

Forbid all three fields in the next series. A change of algorithm, interface,
data source, or vocabulary does not create a new conceptual splinter.

Exclude a series' ENTIRE round-one territory — all five directions — not
only its final survivor: the discarded four are still claimed conceptual
ground, and a later series re-proposing one wastes its divergence budget on
a duplicate the synthesis already holds. One abstract line per direction
suffices; the later series is also instructed to disclose and replace any
idea of its own that drifts toward an excluded one (the drift disclosures
themselves are synthesis material).

## Synthesis prompt for the main agent

Do not send this to an outside agent. The repository-aware main agent decides:

```text
Which direction most changes the system's boundary while preserving a claim
narrower than its evidence? Which can be defeated before implementation by a
construction check or blind control? Which serves the long ambition instead
of the current roadmap's vocabulary?

Choose one. Decline the others or import one bounded lesson from each. Then
inspect the actual code before writing the design.
```
