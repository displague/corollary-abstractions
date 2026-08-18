# Round prompt templates

Use these as structures, not scripts. Replace bracketed fields with plain,
task-specific content. Keep the outside agent isolated from the repository.

## Series round 1 — diverge

```text
You have no access to a repository. Do not use tools or assume project
vocabulary. Think with maximum divergence.

Plain ambition:
[Goals, human capability, inspectability, exact-code boundary, role of any
learned component.]

Forbidden territory from earlier series:
[None for series one. Add exclusion cards for later series.]

Pick one surprising conceptual boundary to push. Explain why it changes the
effort rather than adding a feature, what it lets a person do, and the
seductive but wrong version. Return one direction, not a list.
```

## Series round 2 — ground

```text
Keep the conceptual splinter, but confront these physical and methodological
constraints in plain terms:

[Only relevant repository constraints and existing capabilities. Do not name
the answer you want.]

Revise the direction so it is not a renamed existing feature. State the
minimum new authored information, what is computed exactly, whether any
graded component remains, one bounded experiment that can fail, and the
cheapest blind method that might make the claim vacuous.
```

## Series round 3 — pressure-test

```text
Final pressure test.

[Strongest factual objections found by inspecting the repository: missing
APIs, duplicated machinery, answer-by-authoring risk, trust coupling,
resource limits, or prior negative results.]

Decide whether the direction survives. You may narrow or replace it while
staying on this series' distinct conceptual splinter. Return one decisive
recommendation with:
1. one first-class object and exact trust boundary;
2. the smallest non-anecdotal slice;
3. a human demonstration;
4. preregistered pass/fail and blind-control conditions;
5. explicit non-claims;
6. the established habit to suspend.
```

## Exclusion card

```text
Problem boundary: [What relationship or limitation this direction attacks.]
Mechanism: [The essential means, not implementation trivia.]
Success shape: [What new knowledge or human ability would count.]
```

Forbid all three fields in the next series. A change of algorithm, interface,
data source, or vocabulary does not create a new conceptual splinter.

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
