---
name: forge-design-direction
description: Derive and write a bold, falsifiable project design through three independent outside-agent inquiries, three constraint rounds per inquiry, deliberate cross-series exclusion, repository grounding, and adversarial review. Use during release rotation before creating the next roadmap or release blog, after a surprising result or failed prediction forces a new direction, or whenever asked to propose a DESIGN document that extends the project's conceptual bounds instead of incrementally extending its current vocabulary.
---

# Forge a Design Direction

Produce one reviewed `docs/DESIGN-*.md`, not a brainstorm list. Use fresh
outside reasoning to escape accumulated project language, then make the idea
survive the repository's real limits.

Read [references/round-prompts.md](references/round-prompts.md) before starting.

## 1. Orient without choosing an answer

Read the four current coordinates:

- highest-versioned `docs/ROADMAP-v*.md`;
- `experiments/ANALYSIS.md`;
- `docs/DISCOVERIES.md`;
- `docs/BACKLOG.md`.

During release rotation, also read the previous two roadmaps and releases, the
current release triage, governing design documents, and the release skill. Read
the release skill only for lifecycle context: the current invocation satisfies
its design-direction gate. Do not invoke either skill again from inside this
skill.

Extract two separate notes:

1. **Plain ambition:** what a person should eventually be able to do and what
   research boundary the project wants to move.
2. **Constraints:** physical limits, existing capabilities, trust boundaries,
   authoring conventions, evidence rules, resource costs, and spent data.

Do not propose a solution yet. Do not let the project's current roadmap become
the plain ambition.

If the roadmap already names a reviewed but unadjudicated forward design,
record it as the **incumbent**. Do not reveal it to the outside agents. Compare
it with the three new directions only during synthesis; never silently replace
it because a newer idea is more vivid.

## 2. Remove the project's dialect

Write a short outside brief using ordinary language. Omit:

- the project and repository names;
- internal acronyms, status words, prediction labels, and version numbers;
- current feature names and queued implementations;
- the preferred answer, if one is already suspected.

Describe goals and ambitions: the kind of reliable capability sought, what
must remain inspectable, what exact work belongs in ordinary code, and what a
small learned component may or may not do.

If the brief sounds like a roadmap summary, rewrite it.

## 3. Run three independent three-round inquiries

Use three fresh high-divergence subagents or equivalent isolated contexts.
Each context must be launched with:

- no forked conversation turns;
- no repository or workspace mount;
- no network access;
- no tools.

An instruction saying “do not use tools” is not isolation. If the platform
cannot enforce all four properties, mark the design gate `BLOCKED` and stop.
Pass only the brief and the current series' exclusions. Run the series
sequentially because later series depend on earlier exclusions.

Before round one, hash the canonical-LF plain brief with SHA-256. Retain a
compact receipt in `reports/design-direction-<cycle>.json` containing the
three context ids and provider/model names, enforced isolation mode, brief
hash, start/order timestamps, each round-prompt hash, and each exclusion-card
hash. The receipt contains no model responses or reasoning transcript.

For each series, keep the same outside agent for all three rounds:

1. **Diverge.** Ask for one surprising conceptual boundary, one human ability
   it unlocks, and the seductive wrong version. Reject grab bags.
2. **Ground.** Translate only relevant repository constraints into plain
   terms. Name existing capabilities that make a shallow version duplicative.
   Ask for the minimum authored information, exact machinery, optional graded
   residue, one bounded experiment, and its cheapest blind control.
3. **Pressure-test.** Present the strongest remaining objections. Require the
   agent to keep, narrow, or replace its direction. Demand one first-class
   object, exact trust boundary, smallest non-anecdotal slice, human
   demonstration, registered failure conditions, and one established habit to
   suspend.

Do not leak an intended solution during grounding. Constraints may kill an
idea; that is success.

### Force conceptual separation

After series one, write an **exclusion card** containing its:

- problem boundary;
- mechanism;
- success shape.

Give that card to series two as forbidden territory and aim the brief at a
different relationship in the project. After series two, give both cards to
series three. “Use another algorithm for the same task” is not a distinct
direction.

If isolated agents or an auditable isolation receipt are unavailable, report
the design gate blocked. Do not simulate independence in one context and call
it three outside views.

## 4. Select; do not average

Summarize the three surviving directions in plain terms. Choose one direction
by asking:

- Does it change what the system can know or what a person can do?
- Is the trust boundary exact and narrower than the claim?
- Does it reuse existing substance without renaming an existing feature?
- Can a blind method or construction failure honestly defeat it?
- Does it serve the broad ambition rather than accumulated project language?

Do not vote, score prose, or combine all three into a platform. Select one.
Explicitly decline the others, or import only a sharply bounded lesson from
each. It is acceptable to conclude that none survives; record that refusal
instead of manufacturing a design for release symmetry.

When an incumbent exists, retain it unless the current release evidence or the
selected direction supplies an explicit, grounded reason to supersede it. A
new direction that is merely interesting parks behind the incumbent with a
named prerequisite; it does not become a second floating roadmap promise.

## 5. Inspect reality before writing

Read the actual modules, schemas, and tests that the selected direction would
reuse. Treat every outside-agent statement about current capabilities as a
hypothesis. Never claim an adapter, finite action set, verifier, artifact, or
interface exists until the repository shows it.

Resolve conflicts with current designs and the current roadmap. A direction
scheduled after the active cycle must say so; it must not silently reopen an
explicit park.

## 6. Write the DESIGN document

Use a plain title and define only unavoidable new terms. Avoid decorative
layers, ladders, named principles, and prediction codes without executable
consequences.

The document must contain:

- status: design only, prerequisite, implemented, or measured;
- the boundary being moved and the human capability it unlocks;
- why this direction survived and why the other two did not;
- one new first-class object or contract;
- exact trusted and untrusted components;
- the smallest slice that uses existing substance and cannot be a demo zoo;
- the cheapest capability-blind baseline;
- preregistration order and source/provenance requirements;
- measurable construction and result gates;
- corruption, vacuity, and negative controls;
- stop conditions and explicit non-claims;
- the established habit being suspended, with scope and duration;
- how status will land in roadmap, analysis, discoveries, and backlog.

Freeze numbers only when they are justified before measurement. When scale is
unknown, register a construction prerequisite that must be committed before
implementation rather than inventing a convenient denominator.

The design must distinguish:

- a construction refusal from an unfavorable result;
- a bounded negative from an unrestricted negative;
- a human demonstration from scored evidence;
- source truth from generated artifacts;
- exact checking from correctness of the trusted source rules.

## 7. Make it a release input

When used during release rotation:

1. finish and review the design before writing the release blog;
2. link it from the next roadmap with an explicit lifecycle status;
3. make the blog's final forward-looking section follow from the chosen
   design, not precede it;
4. keep declined directions parked unless the next roadmap names a dependant.

Do not let a release deadline weaken the three-series separation or review
gate. An explicit “no direction survived” is a valid release finding.

## 8. Review and land

Stage the exact design diff and run the repository's mandatory code-review
skill with architecture/spec context. Review especially for:

- a claim already supplied by existing code;
- a checker that validates only its own output;
- missing or extra population members escaping equality checks;
- selector freedom, target leakage, or authored-after-result fields;
- unbounded witnesses or hidden resource blowups;
- a blind baseline that already solves the task;
- conflict with source-generation and status conventions;
- wording that promotes a hypothesis into an implemented fact.

Fix every Critical and High finding and re-review. Validate Markdown links and
`git diff --check`. Follow the repository's normal worktree, commit, merge,
and push rules when the user authorized a repository change.

## Output contract

Report:

- the three final directions and how each changed under pressure;
- the selected direction and bounded lessons imported from the others;
- the DESIGN path and roadmap linkage;
- the decisive construction, blind-control, and stop gates;
- review findings fixed or remaining;
- commit/publish status.

Do not dump raw subagent transcripts into the repository. Preserve the
decision and its falsifiers, not the chat that produced them.
