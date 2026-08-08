# A tiny model in a symbolic world

## What this project is trying to learn

Could a very small AI system become a useful mathematical, scientific, and
conversational reasoner without trying to compress the world's formulas,
vocabulary, and proof rules into neural-network weights?

That is the question behind **corollary-abstractions**. The original ambition
was a roughly 64 MB model that learned the abstract relationships shared by
mathematics, physics, language, and reasoning: recurrence for reusable proof
steps, pointers for selecting relevant facts, memory for sustained thought, and
state-space machinery around the outside. In the strongest version of the
idea, it would be small enough to run almost anywhere while remaining useful on
tasks normally associated with large language models.

The project has not produced that general solver. It has produced something
more specific and, so far, better supported by evidence: a tiny learned policy
works best when it lives inside a symbolic world that performs every exact
operation for it.

Parsing has an exact answer. Equality has an exact answer. Looking up a known
formula has an exact answer. Applying a proof rule can be checked exactly.
These operations do not need to be rediscovered approximately inside weights.
The model should spend its limited capacity on the genuinely graded remainder:
which relevant fact to inspect, which plausible step to try, which analogy to
follow, or which conjecture is worth testing.

The working thesis is therefore:

> The model proposes; symbolic machinery parses, retrieves, executes,
> verifies, and remembers.

That is not a claim that weights are unimportant. It is a claim about division
of labor.

## Three projects that became one

The repository now has three interlocking systems.

The first is a cross-discipline ontology: 199 mathematical and scientific
statements from 21 disciplines. Each statement records its formula, typed
slots, meaning, provenance, limitations, and links to other statements. The
corpora are generated from seed scripts rather than edited as loose JSON, so a
change can be regenerated and audited byte for byte.

The second is a symbolic matcher stack. It asks questions such as:

- Do these statements have the same shape?
- Do their corresponding variables play compatible roles?
- Are they members of the same family after a declared sign or head alias?
- Is one a specialization of another?
- Can one statement be decomposed into forms already present elsewhere?

This machinery finds relationships that textbooks normally leave separated by
department boundaries. Newtonian gravitation and Coulomb's law share an
inverse-square skeleton. Gradient descent is an Euler step on gradient flow.
The trapezoidal integration rule is the trapezoid area formula. A pH formula
has the shape of surprisal. GRPO's normalized advantage has the same form as a
z-score. Transitivity appears across logic, set inclusion, geospatial
containment, and temporal precedence.

The third system is an experiment suite of models with roughly 0.8 to 1.5
million parameters. These models do not reproduce the ontology. They point
into structured inputs, compare residual meanings, or choose pieces that exact
code later assembles. Their checkpoints occupy only a few megabytes.

A Lean sub-project adds a fourth role without changing the architecture: a
machine verifier. Phase 1 extracted 155 real state–tactic–state transitions
from 16 Lean theorems corresponding to Boolean laws in the corpus. Both
extraction and interactive PyPantograph proof steps have run natively on
Windows. The learned tactic policy and verifier-guided search remain to be
built.

## The experiments changed the thesis

Early experiments compared raw characters with increasingly symbolic inputs.
The result was not simply “symbolic is better.” It revealed a boundary.

On cross-language question answering, raw characters could sit at chance while
a parsed representation exposed a learnable residual. When the symbolic front
end reduced a task to exact equality, a tiny transformer still learned equality
poorly, reaching only about 0.71 where a direct comparison is perfect and free.
That failure became a design rule: once the answer is closed-form, stop asking
the model.

The same lesson appeared in knowledge storage. A tiny model asked to induce a
lexicon from examples learned part of it in-distribution and collapsed to
chance out of distribution: 0.508. Supplying the same lexicon externally kept
the task alive at greater depth. A hybrid system combining an exact structural
feature with a learned lexical residual reached 0.805 OOD. External knowledge
was not merely smaller than memorized knowledge; it was more robust.

Scale did not rescue the wrong interface. Across an 8-fold change in model
width and a 10-fold change in training data, learned absolute positions still
failed to extrapolate through deeper structures. Supplying tree-path addresses
made even the smallest tested model generalize. The interface delivered a
capability that extra parameters and exposure did not.

The project also records its failed claims. An early 1.000 composition score
turned out to admit a capability-blind shortcut. That claim was retracted, the
task was rebuilt with distractors, and the new instrument measured its own
floor. This predict-then-adjudicate discipline is now part of the repository's
operating method: a negative result and a public correction are successful
outcomes when they narrow the design.

## What pointing can and cannot do

The clearest end-to-end demonstration takes a question written in one invented
language and a small knowledge base written in another. The model points to the
answer span. Exact code parses that span, maps it through the external lexicon,
and renders a grammatical answer.

The harder version supplies three distracting statements and holds out
particular verb–noun combinations. Its capability-blind floor is 0.31. With
symbolic tree addresses, the model reaches 1.000 on both held-out-combination
seeds. On deeper knowledge bases containing distractors it falls to 0.69, so
depth remains open.

Two learned decoders failed where the pointer succeeded. A conventional
sequence decoder could not reliably copy variable-length content. A
pointer-generator learned content associations in familiar combinations and
then collapsed on held-out ones. The system became more capable when the
decoder was removed: point to the material, then let deterministic code perform
the reversible transformation and realization.

Non-extractive creation needs more. In the analogy task, the answer tree exists
nowhere in the input. A pointer-only decoder constructs it by taking structure
from one example and fillers from another. It reaches 1.000 at trained depth on
held-out transform–skeleton combinations. Its initial OOD score at greater
depth was only 0.014.

That failure produced the v0.4 headline experiment.

## Iteration generalizes; exposure does not

The analogy model originally represented each tree-path level with a learned
lookup row. Every example that went deeper than the trained rows failed.
Replacing the rows with sinusoidal values made deeper addresses representable
but did not teach the consumer how to use them.

The decisive fork compared more exposure with shared iteration:

| Address mechanism | Training depth | OOD depth | OOD exact |
|---|---:|---:|---:|
| Lookup table | 2–3 | 4–5 | 0.014 |
| Lookup table with curriculum | 2–4 | 5–6 | 0.006 |
| One shared GRU cell iterated over levels | 2–3 | 4–5 | 0.226 |

Curriculum moved the cliff and did not remove it. The recurrent encoder, with
less exposure, was the only arm that extrapolated. This vindicated one part of
the original architectural intuition in a narrow and useful way: depth should
be computation repeated with shared weights, not a vocabulary of levels.

It did not prove that a GRU belongs everywhere, or that an LSTM and an SSM must
be added because they appeared in the original sketch. Named components should
earn responsibilities through controlled comparisons. The result supports
recurrence as a mechanism. The remaining 0.226-to-1.0 gap likely requires the
pointer queries and decoder attention—the consumers of the address—to become
iterative as well.

## The “golden chicken” test

A deliberately friendly goal has guided the discussion:

> “Tell me a story about a golden chicken, with a beginning, middle, and end.”

An LLM can answer immediately. This project cannot currently answer end to
end. That zero is important.

Yet many declarative pieces already exist. The narrative corpus contains a
three-part story sequence and separate setup, complication, and resolution
forms joined by a shared desire. It contains a causality bridge: precedence
plus enablement is read as narrative causation. Chekhov's gun is represented as
a temporal liveness requirement: a deliberately planted element must
eventually be discharged. Frame consistency says that a story cannot accept a
premise and its negation.

The matcher finds that frame consistency is a typed structural twin of Boolean
complement laws in logic and set theory. The logical member is linked to a
machine-checked Lean proof. That makes the frame axiom more than an informal
design intention, but it does not mean an evolving story has been verified.
The declarative axiom layer is implemented; the scope metadata and executor
that apply it to runtime state are not.

The golden-chicken milestone is therefore not “author a story grammar.” It is:

1. Open a fictional frame in which a golden chicken exists.
2. Store its declarations as truths local to that frame.
3. Propose a setup, complication, and resolution in sequence.
4. Verify each transition before it becomes the next premise.
5. Track causal and temporal obligations, including planted elements.
6. Render the accepted trace as readable prose.

The same loop should also produce a three-step mathematical derivation. A plot
event and a proof tactic are different domain actions with the same control
shape: propose, execute, verify, retain or reject, and repeat.

That shared loop is an integration achievement, not yet proof of generalized
model weights. Two bespoke policies can hide behind one API. The evaluation
must proceed in rungs: first a deterministic oracle in both domains, then
separate learned policies, then one shared policy with thin verifier adapters,
then held-out structures and greater depth, and finally transfer to a third
domain such as equation derivation or a scientific problem.

## Why the first controller should not learn

The first chained-composition controller will use a deterministic oracle
policy. This is the project's capability-blind-baseline rule applied to the
harness itself.

If a learned controller fails immediately, the cause could be any of the
following:

- the state omitted information;
- an action was malformed;
- the executor applied it incorrectly;
- the verifier adapter returned the wrong result;
- a retrieval result was not made pointable;
- the search mishandled a dead branch;
- or the learned policy simply chose badly.

An oracle that completes both target chains proves that the machinery can
represent and execute them. Only then is replacing the oracle with a small
policy an interpretable experiment.

The controller protocol is intended to be domain-neutral. It carries typed
state, unresolved slots, an action, a verifier outcome, the accepted next
state, and a branch trace. Its action vocabulary is:

- `POINT`: bind material already present in context;
- `GEN`: propose symbolic structure, including a tactic or story transition;
- `RETRIEVE`: query an external store;
- `ASK`: ask the interlocutor for frame-private information;
- `WRITE`: stage a proved conclusion for durable storage.

The verifier changes by domain. Lean checks proof tactics. A story adapter
checks frame consistency, temporal order, causality, and outstanding narrative
obligations. Corpus operations use parsers, matchers, and exact executors.

## Retrieval: using knowledge is ahead of seeking it

Retrieval has three different stages, and their status should not be blurred.

**Consumption is measured.** When a relevant small knowledge base is placed in
context, the pointer uses it under distractors and held-out combinations. The
external-lexicon experiments show why the knowledge should remain outside the
weights.

**Initiation is designed but unbuilt.** A well-formed unresolved slot occupies
the epistemic ladder's UNKNOWN rung. That is a closed-form signal that more
information is required. It can trigger `RETRIEVE(key)` without asking a model
to improvise whether ignorance exists. The learned residual is choosing a
useful key or source. Today, no unified adapter connects UNKNOWN to the corpus,
lexicon, twin ledger, decomposition index, proof artifacts, or external tools,
and no retrieved result automatically returns as pointable context.

**Miss handling is specified but unbuilt.** A direct miss should widen to a
neighborhood search. If the value is private to the current conversation, the
system should ask the user. If neither source can answer, UNKNOWN remains open
and the system abstains. “I cannot establish that” is a valid terminal state,
not an invitation to fabricate.

This also clarifies tool choice. The exact harness decides whether a local
closed form already resolves the slot and whether the slot is actually
unknown. The policy chooses among plausible queries and actions. Oracle-first
dispatch establishes the correct routing before that choice is learned.

## Storage: durable knowledge, session state, and write-back

The project already has unusually strong durable storage. A human or agent
edits a seed file, regenerates the corpus, validates the merged graph, and
recomputes symbolic relationships. Proven statements can carry `verified_by`
links to machine-checked Lean artifacts. Knowledge is corrected by an auditable
edit rather than a retraining run.

What does not exist is model-initiated durable storage.

The proposed symmetry is simple:

- UNKNOWN licenses an attempt to read through `RETRIEVE`.
- PROVEN licenses a candidate durable write through `WRITE`.

`WRITE` must not directly edit generated node files or silently promote model
output to truth. It stages a seed-level candidate with its proof and
provenance. The usual regeneration, schema, link, matcher, and review gates
still decide whether it enters the durable corpus. A conjecture remains a
conjecture. A fact declared inside a fictional frame remains session-local. A
failed branch is evidence for search, not a theorem.

Session storage arrives through frame state. Every accepted step becomes a
premise available to the next step. When a frame closes, its local truths do
not leak into the global corpus; they revert to claims under that premise set.
That is as important for a fictional golden chicken as it is for a temporary
assumption in a proof.

## Conversation, clarification, and dead ends

Not every incomplete request should trigger a database lookup. “Make the story
funny” may be clear enough to attempt. “Make it like the one I told you
yesterday” may require session memory. “Which Alex?” can only be answered by
the user. A private preference is not missing world knowledge.

The proposed `ASK(slot)` action treats the user as the authoritative source for
frame-private UNKNOWNs. The reply binds the slot in mutable session state and
the same controller branch resumes. This is the beginning of an actual
conversation loop rather than a sequence of unrelated prompts.

Some branches will still fail. A verifier may refute a candidate. A tool may
miss. Search may exhaust its budget. The user may defer an answer. The harness
must record these outcomes distinctly.

A dead-end trace should retain the rejected action, its dependencies, the
verifier involved, and the reason for rejection. That information prevents the
controller from retrying an equivalent failure. It does not enter the accepted
premise set. Terminal outcomes should distinguish contradiction, exhaustion,
tool miss, unresolved user input, and budget limits. Honest failure is part of
the result.

The specialization matcher already supplies a symbolic precedent: it explores
alternative derivations, rejects unacceptable paths, and returns the cheapest
surviving one. Lean proof search will have the same shape. The missing work is
to make branch accounting part of the common controller rather than a private
detail of individual tools.

## Where the project stands

| Capability | Present state |
|---|---|
| Cross-discipline symbolic knowledge | Operational: 199 nodes, 21 disciplines |
| Structural twins, specializations, decomposition | Operational and measured |
| Knowledge supplied in context | Consumed successfully by a tiny pointer |
| Retrieval initiated by the model | Designed; no unified adapter |
| Durable human/agent-authored storage | Operational through seeds and validation |
| Model-initiated durable write | Newly specified; unbuilt |
| Narrative grammar and axioms | Authored and matcher-visible |
| Runtime fictional frame | Scope designed; executor unbuilt |
| Lean training transitions | Phase 1 delivered: 155 transitions |
| Learned tactic policy and proof search | Unbuilt |
| Multi-step shared controller | Protocol specified; implementation unbuilt |
| Conversational clarification | `ASK` specified; conversation loop unbuilt |
| Expressive LLM-like prose | Far from the present renderer |
| End-to-end golden-chicken story | 0/1 |

That final zero prevents the component inventory from becoming self-congratulatory.
The project has rails, forms, measurements, and verifier footholds. It does not
yet have the integrated behavior.

## What “comparable to an LLM” can honestly mean

A system this small is unlikely to match a large language model's unrestricted
vocabulary, cultural recall, stylistic breadth, and effortless prose using its
weights alone. The project makes the opposite storage bet: vocabulary and
knowledge belong in editable external stores, and exact transformations belong
in code.

There is still a meaningful comparison to pursue. A tiny system could be
competitive in task satisfaction, premise fidelity, causal coherence,
traceability, correction, and conversational revision. A golden-chicken story
could be plainly written yet mechanically show:

- where every premise entered;
- which event established each later possibility;
- whether a planted element was paid off;
- which rejected branches contradicted the frame;
- what was retrieved, from where, and why;
- which missing choice came from the user;
- and why the final sequence was accepted.

That would not be a miniature imitation of an LLM. It would be a different
kind of system: less fluent, much smaller, and more explicit about what it
knows, assumes, tries, proves, and cannot resolve.

## The next experiment

The immediate path is now concrete:

1. Implement the common state/action/verifier protocol.
2. Add the runtime frame executor and frame-local ladder.
3. Connect UNKNOWN to retrieval, user clarification, and abstention.
4. Run the deterministic oracle through one proof and one story.
5. Preserve rejected branches as structured evidence.
6. Replace the oracle with a tiny verifier-coupled policy.
7. Extend recurrent processing into the consumers that still fail at depth.
8. Test one shared policy across proof and story tasks.
9. Transfer to a third scientific or mathematical domain.
10. Add a richer renderer and multi-turn interaction without weakening the
    symbolic audit trail.

The golden chicken is the approachable demonstration. The real experiment is
whether the same small controller can navigate proofs, stories, and scientific
relationships because their closed-form machinery is explicit and their
uncertain choices share one learned residual.

The project is not there. It now has a sharper account of what “there” means,
which components have earned their place, and which experiment should come
next.

## Follow the evidence

The detailed numerical record, including negative results and retractions, is
in [`experiments/ANALYSIS.md`](../../experiments/ANALYSIS.md). The live next
steps are in the [v0.5 roadmap](../ROADMAP-v0.5.md); discovered relationships
and known friction are recorded separately in
[`DISCOVERIES.md`](../DISCOVERIES.md) and [`BACKLOG.md`](../BACKLOG.md). The
[repository README](../../README.md) contains reproduction commands and a map
of the implementation.
