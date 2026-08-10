# The small model meets a hard baseline

*What live proof search, private conversation, grounded analogy, and a deferred
vision experiment taught us about building intelligence outside the weights*

Imagine asking an AI for a story about a golden chicken.

The request sounds simple: “Tell me a story about a golden chicken, with a
beginning, middle, and end.” Then the conversation continues. “In my version,
make the chicken lay silver eggs.” Someone else says, “Make mine blue.” A
moment later the first person changes their mind: “Actually, make mine copper.”

A large language model handles this fluidly. It draws on an enormous learned
model of language and the world, keeps enough conversational context to follow
the revisions, and produces polished prose. Our project starts from almost the
opposite premise. We are asking how much of that process can be made explicit,
verifiable, and correctable while the learned model remains extraordinarily
small—roughly 28,000 to 1.7 million parameters in the experiments discussed
here, with a long-term target
for the complete system under 64 MB.

The wager is:

> If an operation has a closed form, it should live outside the weights.

Equality, parsing, proof checking, address arithmetic, scope, contradiction,
temporal ordering, provenance, and receipt verification are not improved by
being remembered approximately. They are already algorithms. The weights
should be reserved for what is genuinely graded: which proposal is promising,
which object fills a role, which relationship is relevant, and which branch is
worth trying next.

The external world is not a bag of prose. It is a seed-generated corpus of 221
mathematical statements across 22 disciplines, plus matchers that reduce each
statement to a typed structural skeleton. When statements share a skeleton,
the project calls them *twins*: Newtonian gravitation and Coulomb's law become
the same inverse-square form with different names; exponential growth,
continuous compounding, and a softmax policy occupy one broader exponential
family. A specialization graph records when one form is a cheaper, more
specific derivation of another. Lean artifacts anchor the portion that is
machine-proved. That is the symbolic world the tiny models navigate.

The [previous chapter](the-world-outside-the-weights.md) built the world around
that idea. It introduced one controller for proofs and stories, executable
fictional and belief frames, retrieval with provenance, clarifying questions,
and a recurrent tree-address mechanism that generalized farther than lookup
tables. This iteration asks the uncomfortable next question:

> What happens when a learned model is finally allowed to choose inside that
> verified world?

The short answer is encouraging but humbling. The learned policy really learns
something. It also loses to a better simple baseline. Live search succeeds,
but search—not the model—does much of the work. A first corpus analogy lane is
fully verifiable, but a one-line blind rule solves all of it. Conversation
becomes genuinely maintained and revisable, while still remaining narrow and
symbolic. And the first visual experiment is deliberately not run, because its
ground-truth layer does not exist yet.

That combination is the point of the release. A small, inspectable system can
tell us not only what worked, but which attractive interpretation did not
survive contact with a stronger control.

## A proof is a conversation with a stricter listener

The controller sees a proof and a story as the same kind of process:

1. hold a current state;
2. propose an action;
3. ask a domain verifier what the action actually does;
4. keep accepted transitions and reject invalid ones;
5. continue, backtrack, ask, retrieve, or stop.

In a story, the verifier checks premises, event order, and obligations. In a
Lean proof, Lean itself checks every tactic. The controller does not need to
know the internal truth rules of either domain. It needs a typed action
protocol and an adapter whose verdicts it cannot forge.

Until now, the proof side replayed transitions extracted earlier. That was
useful for authentic state progression, but it was not search. The next step
connected the controller to a live Lean process through PyPantograph and gave
it a fixed, deliberately unsophisticated tactic palette.

The held-out proposition was small. The demo opens this goal directly; it is
not an authored repository theorem named `swap_and`:

```lean
∀ (P Q : Prop), P ∧ Q → Q ∧ P
```

The search must introduce the propositions and hypothesis, construct a new
conjunction, and project the original conjunction in reverse order. Lean
decides whether each tactic is accepted and returns the next proof state.

The important result is not merely that the theorem was solved. The search
entered a real dead branch. Lean accepted `clear h`: removing an unused
hypothesis is a valid proof-state transition. But in this theorem `h` is the
only evidence from which the reversed conjunction can be built. The branch is
legal and hopeless. Breadth-first search retains that state as evidence,
abandons it when no continuation works, and solves through another branch.

With the complete blind palette, the theorem closes after 9 expanded states
and 86 tactic proposals. Remove the two conjunction projections and the same
search exhausts its reachable state space at 10 states and 80 proposals—well
before the configured resource budget. The projection
ablation is load-bearing: the theorem is not being solved by a hidden shortcut
in the wrapper.

This is a modest theorem, not a general prover. But it establishes the part of
“reasoning” that demonstrations often omit: an accepted step can still be a
bad idea, and a useful system must distinguish invalid actions from valid dead
ends.

## The first learned policy enters—and the simplest strong rival wins

The learned tactic policy is intentionally tiny: a 27,688-parameter byte-level
GRU. It reads a Lean state and ranks eight tactic schemas. It does not check
proofs, execute tactics, or decide that a theorem is solved. Those operations
remain in Lean and the controller.

The data are also small: 60 usable atomic transitions drawn from 16 Boolean-law
theorems. For classification evaluation, models hold out entire theorem groups,
so they cannot earn credit by seeing neighboring states from the same proof.

Across three cold seeds, those heldout evaluation models reach 0.8125 top-1
every time. The most
frequent training label reaches 0.4375; independently shuffled labels reach
0.25, 0.375, and 0.375. So the GRU learns a stable relationship between proof
state text and tactic schema. That is a real result.

Live search uses a separate all-data model per seed, trained on all 60 usable
transitions—including the four theorem groups used by the classification
holdout. Those are the checkpoints released as assets. All three solve the
conjunction goal in 71, 63, and 61 proposals, for a mean of 65. The arbitrary
blind palette needs 86. It is tempting to stop there and announce that learned
ranking improves proof search.

Then comes the baseline that matters: rank the palette globally by training
frequency, without reading the current proof state at all. That state-blind
order solves in 64 proposals—one better than the learned mean. Two learned
seeds beat it; one loses badly enough to erase the average gain.

The resulting table is a useful summary of the project's method:

| evaluation / policy | held-out classification | live proposals | outcome |
|---|---:|---:|---|
| arbitrary palette | — | 86 | solves |
| heldout GRU architecture, each seed | 0.8125 | — | classification only |
| all-data GRU checkpoint, seed 0 | — | 71 | solves |
| all-data GRU checkpoint, seed 1 | — | 63 | solves |
| all-data GRU checkpoint, seed 2 | — | 61 | solves |
| state-blind frequency order | 0.4375 | **64** | solves |

The model learned. The model did not demonstrate a mean live-search advantage
against the strongest cheap control.

That distinction is easy to lose in modern AI evaluation. A model metric can
look impressive while the deployed decision problem is already handled by a
frequency table, a parser, or search. Small models make this especially
visible because every unnecessary learned operation consumes a noticeable
fraction of the capacity budget.

The correct next step is breadth, not celebration or immediate scaling. One
theorem gives one ordering profile. A real policy result needs solved-rate
curves across multiple proof families, imported projects, fixed budgets, and
separate tactic-argument generation. The policy should also use the same action
protocol in the story domain before the controller is called general.

## Where the models fit—and what can be run

The system is not one monolithic network. Its learned pieces are small and
replaceable: an approximately 800,000-parameter span pointer answers questions
by selecting material already in context; a roughly 1.5–1.7-million-parameter
analogy pointer reconstructs a target entirely by copying input positions; and
the new 27,688-parameter byte GRU ranks tactic schemas. Exact parsers,
realizers, verifiers, stores, and frame transitions surround them.

Three demonstrations expose different boundaries:

```console
cd experiments
python demo_answer.py
cd ..
python scripts/conversation.py
# after native Lean + PyPantograph setup described in prover/FEASIBILITY.md:
python prover/live_search.py
```

The first self-bootstraps a model-driven question-answering checkpoint. The
second is a symbolic maintained-conversation demo. The third performs real
kernel-adjudicated search. Release assets let model-driven paths be rerun
without a GPU; each asset's notes say whether it is a winner, a control, or—in
the tactic policy's case—a useful negative result.

## The chicken now remembers whose eggs are whose

The earlier conversation demo could ask one clarifying question, accept a
signed answer, and resume. This release turns that exchange into maintained
session state.

Alice and Bob begin with the same accepted golden-chicken story. The public
story has the same setup, complication, resolution, planted feather, and
discharged obligation for both people. What differs is a private unresolved
slot: the color of the eggs in each person's requested revision.

Alice answers “silver.” Bob answers “blue.” Their renderers now produce:

> Alice: “Now the golden chicken laid silver eggs.”

> Bob: “Now the golden chicken laid blue eggs.”

Neither answer enters the public story or the corpus. Neither appears in the
other user's frame. User testimony resolves a private request; it does not
become a fact about the world merely because the system remembers it.

Alice then says, “Change mine: make the eggs copper instead.” The session does
not discard history. Both signed bindings remain as provenance, while the
silver request becomes explicitly superseded and copper becomes current.

This sounds like ordinary application state, and in one sense it is. The hard
part is authority. If a public tuple can say “this old answer is superseded,” a
caller can forge or delete that tuple. If the system trusts an old binding's
slot name without authenticating the binding, forged metadata can revoke a
different preference. The runtime therefore keeps supersession authority in
verifier-private committed state and derives the slot being changed only from
the authentic new reply.

The result survives two cross-slot forgery attacks and public-state surgery.
The remaining boundary is equally explicit: the signing secret, consumed
request set, and supersession ledger are process-local. This is maintained
conversation, not durable restart. Persisting it safely requires key identity,
rotation, revocation, and a host-kept authority model; simply serializing the
dataclasses would create plausible-looking unauthenticated memory.

This is also where theory of mind becomes operational rather than decorative.
An `ASK` action exists because some unknowns are private to another agent. A
user frame says who is authoritative for a preference. The same ownership
principle lets Sally believe the marble remains in the basket while the world
says it moved to the box. Conversation, false belief, and deictic relations
such as “mine” and “yours” are not three unrelated features. They are scoped
knowledge with owners and visibility.

## A real corpus analogy that turns out to be too easy

The project's earlier analogy result was exact but synthetic. A generated task
provided A:B::C:? where B applied one of five operations to A—negate, invert,
square, take a root, or multiply by itself. C used a different vocabulary. The
model reconstructed D entirely by pointing: structure from B, fillers from C.
It reached 1.000 on held-out transform/shape combinations.

That proved a mechanism. It did not prove transfer to the mathematical corpus.

The first grounded evaluation now builds each quadruple from two audited graph
relationships:

- A→B is a committed cheapest-specialization edge;
- A↔C is a typed structural twin crossing disciplines;
- D transfers B's specialization into C's vocabulary;
- a fresh specializer search must independently accept C→D;
- D must be absent from every authored corpus template.

One concrete example is:

```text
A: RATE = QUANTITY / INTERVAL
B: WIDTHNEXT = WIDTH / 2
C: CONCENTRATION = AMOUNT / VOLUME
D: CONCENTRATION = AMOUNT / 2
```

A is average rate of change. B is interval halving in bisection. C is molarity.
D exists nowhere in the corpus, but every step that creates it is inspectable:
the ratio skeleton is shared, the denominator specialization is transferred,
and the specializer verifies the result.

The evaluator finds 40 provenance-distinct rows across six source and six
target disciplines. Review reveals that these collapse to only five distinct
D equations in one ratio family.

The symbolic resolver scores 1.000 by checked construction: the admission
procedure has already verified the transferred specialization. The released
synthetic pointer scores
0.000 exact even when the equality shell remains symbolic and it sees only the
right-hand expression in its known vocabulary. This confirms a domain gap:
learning five whole-tree transforms did not teach numeric slot
specialization.

But again, the stronger baseline changes the conclusion. A blind rule can look
at A and B, take the one new number in B, and put it in C's last slot. That rule
also scores 1.000.

So this is not yet a learned analogy benchmark. It is a verified dataset
construction and a diagnosis of why the first slice is shallow. The next lane
must include compound expansions with explicit source leaves, multiple
non-isomorphic families, deduplicated targets, and separate family,
discipline, and literal-vocabulary holdouts. The simple positional and numeric
heuristics must run before training.

This is an example of a broader advantage of the architecture. Because the
target is symbolic, we can explain exactly why a task is easy. A benchmark
score alone would not tell us that all examples reduce to “replace the last
denominator with 2.”

## Depth: shared iteration must reach the place that uses it

This experiment is deliberately a synthetic addressing stress test, not a
claim that the neural model has already learned temporal stories, perspective,
or proof logic. Each row is an analogy `A : B :: C : D`. A root-level operation
turns A into B; C keeps A's structure with different variable names; the model
must build D entirely by pointing to structural tokens in B and fillers in C.
It cannot freely invent an answer token.

The fixed dataset is:

| split | generated | scored | structural depth | role |
|---|---:|---:|---:|---|
| train | 50,000 | 50,000 | 2–3 | fit weights |
| validation | 5,000 | 5,000 | 2–3 | select checkpoint |
| in-distribution test | 5,000 | 5,000 | 2–3 | held-out transform/skeleton combinations |
| depth OOD | 3,000 | 2,450 | 4–5 | same held-out combinations at unseen depth |

The in-distribution test is 10% of the training count; the retained OOD set is
4.9% of it. Size is not the main distinction—the held-out axis is.

The OOD number is therefore **conditional depth-OOD exact**. Fixed sequence
limits exclude 550 generated rows: 72 of 1,464 depth-4 rows and 478 of 1,536
depth-5 rows. The harder depth is filtered more heavily, so the next protocol
must retain every case or publish an additional unconditional score.

All 50,000 training rows use one of five operations:

| operation | rows |
|---|---:|
| negate | 10,247 |
| invert | 9,699 |
| square | 10,088 |
| square root | 10,017 |
| multiply by itself | 9,949 |

For example:

```text
A: WIDTH × SPEED
B: √(WIDTH × SPEED)
C: theta × kappa
D: √(theta × kappa)
```

The `√` wrapper and product structure are pointed to in B; `theta` and `kappa`
are pointed to in C. The complete D sequence must match to pass.

That balance is useful, but the operations all change the root. A shallow
“transfer B's wrapper to C” control is therefore part of the next-task design;
internal subtree rewrites, argument order, binding, and composed operations are
not in this training set.

Nor are Chekhov obligations, past/future modalities, Sally–Anne perspective,
nested belief, Lean derivation chains, story beats, or conversational turns.
Those are executable in the symbolic harness, but the current analogy model
has not learned to choose among them. A corpus-grounded progression from logic
to temporal state to perspective to narrative remains the integration path.

Every arm sees the same rows and seeds. Training runs ten epochs with AdamW,
OneCycle scheduling, weight decay 0.01, gradient clipping at 1.0, and
Transformer-layer dropout 0.1. Dropout is active only during training;
validation and both tests use evaluation mode. The replacement run preserves
a logical batch of 192 through 64-example GPU microbatches and evaluates in
batches of 32 after two near-full-VRAM Windows bugchecks exposed the old final-
evaluation boundary. Memory safety is reported separately from model quality.

The completed result is the reverse of the motivating prediction:

| consumer arm | parameters | ID exact mean | depth-OOD s0 / s1 / s2 | OOD mean ± SD |
|---|---:|---:|---|---:|
| recurrent address only | 1,481,987 | 0.9999 | 0.284 / 0.171 / 0.134 | **0.196 ± 0.064** |
| recurrent query | 1,581,059 | 0.9998 | 0.186 / 0.204 / 0.146 | 0.179 ± 0.025 |
| recurrent memory | 1,581,059 | 0.9999 | 0.073 / 0.053 / 0.119 | 0.082 ± 0.027 |
| recurrent query + memory | 1,680,131 | 0.9999 | 0.030 / 0.054 / 0.033 | **0.039 ± 0.011** |
| one-shot level-aware MLP | 1,680,133 | 1.0000 | 0.131 / 0.134 / 0.162 | 0.142 ± 0.014 |

Address-only remains best. Query recurrence is a small mean loss. Memory
recurrence cuts performance by more than half, and recurrence in both
consumers is the worst arm. The MLP differs by only two parameters from the
combined recurrent model and recovers to 0.142, so “more learned processing”
is not the repair either. All three architectural predictions miss; the
complete-matrix and corrected GPU-safety gates pass.

The token diagnostics explain what exact accuracy compresses. Address-only
averages 0.910 accuracy when copying C's variable leaves and 1.000 on the end
marker. Memory recurrence falls to 0.705 and 0.913; both consumers fall to
0.677 on C leaves. The model did not need a deeper consumer. It needed the
consumer to preserve an address representation that already carried useful
iteration.

The architectural question is more general than whether a GRU is fashionable.
The earlier fork showed that a shared computation repeatedly applied over a
tree path extrapolated beyond trained depth, while a lookup table and extra
curriculum exposure did not. That supports “iteration can generalize,” not
“GRU is the reasoning organ.”

The ablation moved shared iteration through the consumers of an address:
the pointer query, the encoded memory, both, and a parameter-matched one-shot
MLP. The surviving mechanism is recurrent address construction alone. Seed
variance and the unchanged trained-depth ceiling remain visible, so the next
step is to freeze consumer complexity and inspect capacity, decoding, and
harder transformation interfaces—not to add recurrent blocks by name.

The safety result is equally concrete. The two old attempts bugchecked Windows
near 15.4 of 15.9 GiB at final evaluation. The replacement kept logical batch
192 through microbatches of 64, evaluated in batches of 32, capped PyTorch at
70%, and stopped above 80% whole-device use. All fifteen rows completed; the
largest whole-device footprint was about 5.95 GiB and final evaluation added
only 2 MiB. This strongly implicates the near-full-memory boundary, but does
not prove whether VRAM, the driver, or the hypervisor was the sole cause. A
later throughput study can test 60%, 70%, and 80% occupancy separately;
jumping straight to 14 GiB would cross the present safety guard.

This bears directly on the original architectural inspirations. Pointer
generation has been reduced to its useful half: pointing is the creation
mechanism; unconstrained generation is not. GRU recurrence has evidence as
shared iteration over structure, not as a universal cognitive module. An LSTM
has not been installed as a “reasoning core” because the verified controller
already owns chain state. State-space models remain an open possibility for
long sequential wrappers, but they must earn their place against explicit
state and closed-form transitions.

## Why the first vision experiment did not run

Modern multimodal systems provide an obvious inspiration. SigLIP learns broad
image-text alignment; official
[Gemma 3 architecture notes](https://developers.googleblog.com/en/gemma-explained-whats-new-in-gemma-3/)
describe a custom SigLIP encoder; and Google's
[WebLI account](https://research.google/blog/pali-scaling-language-image-learning-in-100-languages/)
shows what web-scale multilingual image/alt-text data buys. The comparison is
anchored in those published systems rather than speculative later-generation
descriptions.

Our proposed starting point is narrower. Mathematical figures often begin as
SVG, TikZ, plotting data, or a geometry scene. Their source already contains
objects, paths, labels, coordinates, and relations. The parse-first hypothesis
is that a tiny model should align visible roles to that structure while exact
incidence, measurement, and topology remain outside the weights.

The planned experiment compares a parsed-vector arm with a parameter-matched
raster arm. It needs four things before either model is meaningful:

1. a deterministic renderer;
2. a source scene graph with stable identities;
3. deliberately inconsistent diagrams;
4. an exact geometry/topology verifier that catches them.

At the release gate, none of that ground-truth layer exists in the repository.
There are no SVG or TikZ assets, no diagram renderer, no scene-graph schema,
and no geometry verifier. Running the neural contest anyway would create the
oracle, negative examples, verifier, and models at once. A self-confirming toy
result would be worse than a documented deferral.

The visual predictions therefore remain registered and untested. The next
milestone is data-only: deterministically render a right triangle, preserve the
mapping from formula slots to visual elements, generate a controlled-invalid
counterpart, and prove that exact geometry checks separate them. Only after
that foundation survives attack do the parsed-vector and pixel arms run.

This is how the project expects to differ from web-scale multimodality. It does
not deny that natural images eventually need learned perception. It refuses to
throw away source structure in domains where the structure is already there.
A later image encoder can propose objects and relations into the same harness
as a retrieval tool: attributed, uncertain, revisable, and never promoted to
VERIFIED merely because a network emitted them.

## Retrieval, storage, and the boundary of self-verification

The controller's five verbs remain `POINT`, `GEN`, `RETRIEVE`, `ASK`, and
`WRITE`. This cycle concentrated on learned `GEN`, maintained `ASK`, and the
search loop around them. The next storage step follows a symmetry already
visible in the epistemic ladder:

- UNKNOWN may license a read;
- PROVEN may license a staged write.

“Staged” matters. A model-generated conclusion should not edit generated
`nodes.json` files or declare itself true. A durable write must carry a proof
artifact, theorem identity, transition trace, proposed seed edit, and predicted
matcher movement. Regeneration, validation, and an external prover or human
gate decide whether it lands.

That is also the answer to ideas from self-verifying theories. Provability
logic is now part of the corpus, and it is a useful subject for the matcher.
But the runtime's trust roots remain external. A signed receipt proves that a
particular verifier issued a transaction in a particular session. It does not
prove the verifier is sound. A digest proves which bytes were checked. It does
not prove that the theorem means what a corpus statement says. The semantic
`verified_by` link is still a gap to close before proof-backed WRITE can become
authoritative.

This separation offers a practical advantage over knowledge stored only in
weights. New knowledge can be staged, inspected, rejected, corrected, and
regenerated without retraining the reasoning core. Negative results and dead
branches can also be stored as pruning evidence rather than forgotten.

## What was borrowed—and what was deliberately not borrowed

Several familiar ideas appear here in altered form.

**From BERT:** masked modeling, but over tree nodes rather than words. The prior
release found that masked-skeleton pretraining stabilized seed variance without
solving depth. This is the useful part of the inspiration: a self-supervised
objective aligned with the model's actual pointer interface. The project does
not try to compress BookCorpus-style world knowledge into a tiny parameter
array.

**From WordNet:** an external human-curated lexical graph. On eight fixed terms
absent from the corpus lexicon, the optional Open English WordNet bridge puts
the expected corpus owner into context for 8/8; safe unique binding is 7/8
because one term remains genuinely ambiguous. A capability-blind attempt to
use lexical evidence to mutate a frame verdict is detected 8/8. WordNet can
therefore extend vocabulary without growing the model or acquiring authority:
its records remain empirical, ambiguous senses remain explicit, and exact
corpus aliases take precedence. The 72 MB archive stays external; Open English
WordNet is attributed under CC BY 4.0, with the Princeton WordNet license noted
for inherited content rather than silently vendoring the download.

**From relational frame theory:** a coverage audit for kinds of relation:
sameness, opposition, comparison, hierarchy, time, causation, and deixis. The
corpus and matcher already mechanize many of these. The open deictic case—
I/you, here/there, now/then—connects owned conversation frames, physical
reference frames, and temporal modalities rather than demanding a separate
“social reasoning” module.

**From theory of mind:** frames with owners and visibility, not an opaque score
called empathy. A false belief is derived because an agent did not witness an
event. A private conversational preference is resolved by the person who owns
it. Nested beliefs and “mine versus yours” become different depths of the same
scope machinery.

**From physical reference frames:** the same scope mechanism now represents an
inertial frame and a uniformly rotating frame. The rotating frame suspends an
inertial law and admits a local fictitious-force term; measurements stay local
while invariant laws remain global. A registered prediction that this would
structurally twin cartoon gravity missed—the physical equation has three
additive terms and the fictional rule only one—but the failure is exactly the
kind of distinction the matcher is meant to expose. Galilean velocity addition
did form a genuine cross-discipline additive twin.

**From large multimodal models:** the importance of cross-modal alignment, but
not the assumption that raw pixels must always be the first interface. The
source representation is treated as the visual parse whenever it exists.

The common pattern is to extract the compositional idea while refusing to pay
weights for a closed-form operation.

## Emotion, oscillation, and what a “frame” must not hide

Two further directions sharpened that boundary during this cycle: emotion
maps, and multiplanar oscillation. They sound unrelated. The useful connection
is methodological, not metaphorical: both mix exact structure with observations
that must not be granted more authority than they have.

For oscillation, the exact lane begins with assumptions. The staged coverage
follows the progression visible in Fitzpatrick's
[Oscillations and Waves](https://farside.ph.utexas.edu/teaching/315/Waves/):
single oscillators, driven systems, coupled modes, Fourier analysis, and
multi-dimensional waves. In an undamped linear
mass–spring system, Hooke's law and Newton's second law yield

```text
m x'' = -k x
ω = √(k/m)
T = 2π/ω
```

Those are idealized physics statements with stated regularity conditions, not
patterns for a model to memorize approximately. Two perpendicular harmonic
motions can then trace a Lissajous figure. That does **not** mean they are
coupled. A coupled multi-mass system is a later rung: its normal modes arise by
diagonalizing the coupled equations, and its modal frequencies belong to that
system. Rotating reference frames are a third layer again; they change the
local terms used to describe motion without turning every multi-axis
oscillator into a frame-of-reference problem.

This yields a clean progression for the corpus and controller:

1. author and verify single-plane SHM, angular frequency, period, and energy;
2. separate independent orthogonal superposition from genuine coupling;
3. add resonance and normal modes with constant and “always resonates”
   controls that must fail;
4. add the frequency-domain view—Fourier components, amplitude/phase spectra,
   sampling and alias controls, and power spectral density—without confusing a
   physical spectrum with a statistical frequency table;
5. let the controller compute or retrieve a period and check a resonance
   condition before any learned physics policy is trained;
6. only after the visual oracle exists, render phase portraits and Lissajous
   figures from source parameters and compare their parsed structure with
   pixels.

The Fourier transform and a discrete power spectrum are closed-form consumers
of sampled data, so they belong outside the weights. A learned residual may
later rank noisy peaks, associate a mode with a source, or decide which
spectral record is relevant. It should not spend parameters approximating the
DFT or silently blur “how often a category occurred” into “which temporal
frequencies carry energy.”

“Multiplanar rotation” also needs three separate boxes. In three dimensions,
pitch, roll, and yaw are coordinate choices for composing rotations, and the
order generally matters. A torsional oscillator is rotational dynamics—the
mass–spring equation reappears as `I θ'' = -κ θ`, predicting the analogous
frequency `√(κ/I)`. In four dimensions and above, one rotation may contain
simultaneous rotations in orthogonal 2-planes with separate angles. The corpus
already has a 3D rigid transform and the unit-quaternion constraint; it does
not yet have these composition, torsional, or higher-dimensional statements.
Keeping them separate is what makes future twins meaningful rather than
wordplay.

Emotion needs an even stricter account of authority. Plutchik's wheel,
Russell's valence–arousal circumplex, PAD, and constructionist theories are
useful representational proposals, with primary references and admission rules
collected in [the affect design](../DESIGN-affect.md). They are not one agreed
coordinate system for every mind. The harness may verify a relation *inside a named theory*—for
example, which labels Plutchik places opposite, or which quadrant contains a
declared valence–arousal coordinate. It cannot infer from that geometry that a
person is angry, or that anger is the universal logical negation of another
state.

The existing belief machinery makes this distinction concrete. An owned frame
models what an agent believes. If Sally says “I am frightened,” Sally's frame
can hold an attributable self-report. Anne's nested frame can hold “Anne
believes Sally is frightened.” Neither statement gives the executor privileged
access to Sally's inner state. Likewise, `witnessed_by` says who received an
event; it does not say what they felt about it. A witnessed insult may license
a learned policy to *propose* anger, or an author may explicitly plant a future
response as a story obligation, but the symbolic layer must not manufacture
anger merely because the event was visible.

That leads to a demonstrable future golden-chicken example. Suppose the story
declares that Mira reports fear after the golden chicken disappears, and plants
a commitment that the fear receive some later response. The controller can
refuse to close the story while the commitment is open, accept a later comfort
or resolution, and keep a character who missed the disappearance unaware of
the report. A negative control removes the explicit report while leaving the
event visible; no fear literal may appear. What has been verified is
attribution, visibility, consistency, and narrative payoff—not a theory of how
all people must feel.

Weights still have a legitimate role. Text, voice, facial expression, or
physiology may support a graded affect proposal. That proposal enters with its
source, uncertainty, and empirical status; a user can correct it, and fluency
cannot promote it to VERIFIED. Emotion wheels and circumplex diagrams may one
day share the visual parsing protocol with SHM plots, but they share a protocol,
not an equation. “Emotional resonance” remains prose unless a real structural
prediction is registered and survives the matcher.

This is the broader advantage we expect: a small model can use rich continuous
signals without turning its latent space into an unauditable source of truth.
Exact transforms remain exact, competing theories remain named, observations
remain attributable, and conversation can repair a mistaken proposal without
retraining the model.

## How close is this to a general solver—or an LLM-quality chicken?

The answer has moved, but it remains bounded.

The system can now:

- run a live Lean proof search and backtrack from an accepted dead branch;
- use a tiny learned policy to rank tactics, while reporting that a frequency
  baseline wins on the current theorem;
- maintain two owners' private story revisions over one public story;
- accept a correction while preserving and revoking signed provenance;
- build novel cross-discipline analogy targets and verify every step;
- detect that the first grounded analogy lane is solved by a trivial blind
  rule;
- state exactly why vision is not yet ready for a model experiment.

It still cannot:

- solve open mathematics or a broad Lean benchmark;
- choose among all five action types with one learned policy;
- parse unrestricted conversational requests;
- persist authenticated conversation safely across process restarts;
- write proven discoveries back into the durable corpus;
- produce prose comparable to a large language model in richness and fluency;
- understand natural images;
- claim standing against external LLM benchmarks.

For the golden chicken, the rails, state, correction protocol, and verifier are
real. The prose remains controlled. The request grammar remains narrow. The
learned model is beginning to choose inside the process, but has not shown that
its choices beat simple priors across breadth.

That may sound less dramatic than “a 6 MB model reasons like an LLM.” It is far
more useful. The project now has a way to tell when search deserves the credit,
when a dataset is structurally trivial, when private memory is forgeable, when
a checkpoint cannot honestly consume a vocabulary, and when an experiment
lacks an oracle.

The intended destination is not a miniature imitation of a giant model. It is
a solver whose small learned core navigates proofs, relations, tools, frames,
and observations that remain visible outside it. New knowledge should arrive
as an audited edit. A proof should survive an external kernel. A story should
obey its own premises. A preference should belong to its owner. A failed
branch should make the next search cheaper. A visual claim should remain an
observation until geometry or another source checks it.

The weights do not need to contain the world. They need to learn where to look,
what to try, and when a simple rule already does the job better.
