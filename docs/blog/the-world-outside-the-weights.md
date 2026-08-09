# The world outside the weights

*How a tiny model acquired stories, questions, retrieval, beliefs, and a more
honest measure of its own limits*

The easiest way to describe this project is with a chicken.

Suppose you ask an AI: “Tell me a story about a golden chicken, with a
beginning, middle, and end.” A large language model can answer immediately. It
has absorbed enough language and narrative regularity to produce something
pleasant. But it is difficult to say where the story's facts live, why a later
sentence follows from an earlier one, or what exactly should happen when you
continue: “Now make the chicken lay silver eggs.”

Our experiment begins from the opposite end. We are trying to build a system
whose learned core is extremely small — around one to one-and-a-half million
parameters, with a long-term whole-system target under 64 MB — but whose
reasoning is compositional, inspectable, and correctable. The central wager is
simple:

> If an operation has a closed form, it should live outside the weights.

Parsing, equality, algebraic normalization, proof checking, scope, temporal
obligations, provenance, and exact retrieval rules do not become more valuable
when approximated by a neural network. They become less reliable and consume
capacity. The weights should learn what remains genuinely graded: which
structure is relevant, which role a candidate fills, which proposal to try
next, and how to rank ambiguous possibilities.

The [previous chapter](a-tiny-model-in-a-symbolic-world.md) described the first
evidence for that thesis. A symbolic matcher found the same mathematical forms
reappearing across 21 disciplines. Tiny pointer models learned to select and
recombine structure when exact parsing and addresses were supplied. A shared
recurrent computation over tree depth generalized where lookup tables and
additional exposure failed.

Version 0.5 asks a harder question: can those pieces inhabit one world? Can a
small proposer take a step, have an external system verify it, keep the result,
notice what is missing, retrieve or ask, and continue?

The answer is now “yes” for a controlled world. It is not yet “yes” for open
mathematics or unrestricted conversation. That boundary is the most important
part of the result.

## One loop, two costumes

A mathematical proof and a short story seem like different products. At the
level this project cares about, they have the same shape.

1. There is a current state.
2. A policy proposes an action.
3. A domain verifier accepts, rejects, or leaves it unresolved.
4. Only an accepted proposal becomes part of the next state.
5. The process repeats until the goal is solved, paused, exhausted, or refused.

For a proof, the state is a Lean goal and the proposal is a tactic. For a
story, the state is a frame containing premises, events, characters, desires,
and outstanding narrative obligations. The verifier changes — Lean for the
proof, frame and temporal laws for the story — but the controller does not.

That distinction matters. If every domain receives a bespoke “reasoning loop,”
we have written several programs and named their wrapper intelligence. A common
controller with swappable truth adapters is a stronger architectural claim.

The current deterministic oracle demonstrates both paths. It replays three
authenticated Lean transitions through one side and constructs a golden-chicken
setup, complication, and resolution through the other. The story must keep one
desire across all three beats. Its setup visibly plants an element. Its ending
must discharge that same element. A contradictory trait is rejected rather
than quietly incorporated.

The result is plain, not literary. That is deliberate. Version 0.5 establishes
coherence and state transition before surface richness.

## Five verbs for a solver

The controller has a small vocabulary:

- **POINT** — bind something already present in context;
- **GEN** — propose new symbolic structure, such as a tactic or story beat;
- **RETRIEVE** — query an external store for a missing value;
- **ASK** — request information that only the interlocutor can provide;
- **WRITE** — stage a proven result for durable storage.

The first four now have executable paths. WRITE is deliberately still only a
word in the protocol. Durable knowledge deserves a higher bar: a runtime result
must not silently edit generated corpus files or promote a plausible thought
into a fact. The intended symmetry is that UNKNOWN licenses a read, while
PROVEN may license a staged write carrying its proof, provenance, and proposed
seed edit. Human and machine audit remain between staging and permanence.

This five-verb view also clarifies what “tool use” means. Tool choice is not a
mystical ability bolted onto conversation. It is action selection under an
unresolved slot. If the value can be derived exactly, derive it. If an
appropriate store could contain it, retrieve. If only the user can know it,
ask. If no channel can resolve it, preserve the unknown and abstain.

## Fiction needed a local truth, not permission to lie

Stories create an apparent problem for a verification-centered system. A
golden chicken is not a world fact. Should a system devoted to truth refuse to
say it?

The answer is scope.

A fictional frame declares premises that are locally valid without becoming
claims about the outside world. Inside the story, “the chicken is golden” can
be VERIFIED. “The chicken is silver” can be REFUTED relative to the story's
premise. Outside the frame, neither statement is promoted to fact.

The same rule already has a mathematical twin. The corpus's frame-consistency
statement — a story may not contain a premise and its negation — shares the
strictest structural skeleton with complement laws in Boolean logic and set
theory. Fiction does not need weaker logic. It needs logic evaluated under
declared premises.

Version 0.5 turns that axiom into an executor. A frame can:

- declare local truths;
- suspend a world law it explicitly replaces;
- admit an invention only through that suspension channel;
- reject contradictions with its premises and accepted assertions;
- keep missing information UNKNOWN rather than calling it false;
- demote local truths when a fictional frame closes, so nothing leaks.

Temporal rules execute too. Chekhov's gun becomes an obligation: if the story
plants an element, the frame cannot close cleanly until the story discharges
it. The converse — no deus ex machina — can be adopted as a genre rule: a
payoff with no earlier herald is refuted. It is governance-gated because some
genres deliberately allow coincidence.

This creates a useful kind of constraint. The story is free to invent a golden
chicken. It is not free to forget what it invented, contradict it without an
explicit revision, or produce a magic key at the ending when the chosen genre
forbids an unprepared rescue.

## Asking is retrieval from the person

An unresolved request can fail for different reasons. Perhaps the answer is in
the corpus. Perhaps it follows from current premises. Perhaps it is a private
preference that no database could hold.

That last case is a clarifying question. Architecturally, ASK is retrieval where
the authoritative store is the user.

The new conversation path begins with an already parsed revision to the
golden-chicken story. The controller reaches a frame-private UNKNOWN, asks one
question, and stops with a distinct WAITING outcome. A reply is bound to the
exact session, frame, owner, question, slot, and value. Replays, cross-session
transplants, modified replies, and answers to questions that were never asked
are refused.

The important epistemic result is quieter: the user's reply clears the need,
but does not become a world assertion. The system can remember “this is what
the user requested for this story” without claiming “this is true.”

When the second turn resumes, the original three beats and discharged
obligation are still present. Rebuilding only the visible text is insufficient;
the signed waiting state and session attribution are load-bearing. This is a
small conversation, but it is a real stateful dependence rather than two
independent prompts styled as a dialogue.

## Belief is another kind of frame

The move from a user frame to a theory of mind is surprisingly short.

Consider the classic Sally–Anne false-belief story. Sally sees a marble placed
in a basket. While she is away, Anne moves it to a box. Where will Sally look?

The world says box. Sally's belief says basket. A system that answers only from
world state gives Sally telepathy. A system that merely authors “Sally believes
basket” has encoded the test answer rather than derived it.

Here the difference comes from event visibility. Sally witnesses the placement
but not the move. Her owned frame therefore retains basket. Anne and the world,
which receive the move event, hold box. No special “false belief” verdict was
added.

Nested frames extend the same idea. Anne can hold a model of Sally. Anne's
model answers basket while Anne herself answers box. A deeper update reaches a
modeled agent only if every owner on the path had access to the event; a parent
cannot learn through eyes it does not have.

This is controlled theory of mind, not unrestricted social intelligence. There
is no rich model of motives, emotion, deception, or cultural context. But the
primitive is valuable: information has an owner, owners observe different
events, and belief divergence follows from visibility rather than from an
unscoped falsehood.

## “Frame” was not just a metaphor

Fictional frames led naturally to physical frames of reference.

In an inertial frame, Newton's laws take their familiar form. In a rotating
frame, additional apparent forces enter the description. The project represents
that as the same scope operation: suspend the ordinary inertial statement for
the local frame and admit a centrifugal correction. Laws that remain invariant
stay at world tier; frame-dependent measurements and terms remain local.

The first physics-frame corpus produced a revealing pair of outcomes.

Galilean velocity addition,

```text
OBJECT_VELOCITY = RELATIVE_VELOCITY + FRAME_VELOCITY
```

mechanically matched algebraic topology's chain rank-nullity form,

```text
CHAINRANK = CYCLERANK + IMAGERANK
```

as the same typed skeleton. But a registered prediction that rotating-frame
physics would template-match cartoon gravity failed. The two frames share
scope behavior — both suspend a law and admit a local premise — while their
equations remain structurally different.

That is exactly the distinction we want the system to preserve. Sharing an
execution protocol does not make two statements mathematically identical.

## A lexical graph outside the model

Information retrieval existed in the earlier project only in the passive
sense: when relevant material was placed in context, the model could point to
it. Version 0.5 adds initiation and provenance.

The local store exposes corpus statements, their lexicon, twin and mirror
groups, decomposition records, and proof summaries. An UNKNOWN can initiate a
query. Exact matches take precedence. Neighborhood results are announced.
Every returned item keeps its own epistemic status. A successful RETRIEVE says
the transaction succeeded; it does not say every result is true.

POINT is stricter than selecting an array index. The selected record must come
from the authoritative store snapshot, belong to the current receipt, match the
pending key, and resolve to an appropriate owner. This prevents a real record
about modus ponens from “answering” a need about De Morgan's laws merely because
both were retrievable.

The optional sixth store is Open English WordNet, the modern continuation of
the pre-LLM human-authored lexical graph. It contributes synonyms and sense
structure without adding model weights. In a fixed eight-term test, WordNet
moved request-term coverage from 0/8 to 8/8 while changing zero frame verdicts.
Only 7/8 could safely bind: an ambiguous term remained unresolved pending a
sense cue.

That refusal is part of the capability. “Ring,” “field,” “group,” and “energy”
have everyday and mathematical senses. An open vocabulary is useful only if it
does not let the everyday sense shadow an exact project concept. Corpus-exact
meaning therefore wins; ambiguous lexical material can be viewed but not
silently promoted.

WordNet remains external and empirical. It cannot ground a mathematical
verdict or appear in a proof link. Vocabulary can expand without authority
expanding with it.

## Proofs, provability, and why the system cannot bless itself

The Lean subproject provides 155 machine-extracted state–tactic–state
transitions across 16 theorems. Retrieval authenticates the committed artifact,
checks that cited theorem transitions exist, and requires a closing “no goals”
state before proof material receives the strongest available label.

But artifact integrity is not semantic correspondence. A deliberately wrong
corpus statement can cite a real, completed theorem about something else and
pass today's lint. That negative control is essential: it marks precisely what
the system does not know. The next proof phase must compare the formal theorem
to the statement skeleton, not merely trust metadata linking their names.

This release also adds a small corpus of provability logic: necessitation,
distribution, Löb's axiom, consistency statements, and Gödel's second
incompleteness theorem. Löb's axiom and temporal induction share a declared
archetype but refuse every structural twin level. Their similarity is real;
their modal laws are not interchangeable.

The deeper architectural lesson is that trust roots stay external. A receipt
can prove freshness and session integrity. Lean can check a theorem. Neither is
the harness proving its own universal soundness. The corpus now contains the
mathematics explaining why self-certification deserves suspicion.

It also caught a flaw in our graded groundedness measure. All six new
provability nodes scored 1.000 because they repeated the new BOX vocabulary
among themselves and fit broad existing patterns. A dense new island could
certify itself as grounded. Future scoring must distinguish prior external
support, same-corpus recurrence, recursive definition, and loose pattern
absorption.

## What the GPU corrected

Most of this release is symbolic, so the GPU was quiet for much of the cycle.
It returned for a focused question inspired by BERT: can masked modeling teach
structure rather than vocabulary?

Instead of masking a word and generating it, the experiment masks one node in a
tree and asks the model to recover it by pointing into a shuffled candidate
bag. The pretraining corpus contains 150,000 trees, all at trained depth. After
three epochs the model recovered 51.8% of held-out masked nodes. Its encoder
then transferred directly into the recurrent analogy pointer.

The result is useful because it is two-sided.

| model | seed | trained-depth exact | deeper-tree exact |
|---|---:|---:|---:|
| cold recurrent | 0 | 1.000 | 0.226 |
| cold recurrent | 1 | 1.000 | 0.087 |
| masked warm start | 0 | 1.000 | 0.215 |
| masked warm start | 1 | 1.000 | 0.187 |

The second cold seed retires 0.226 as a standalone headline. The honest cold
estimate is 0.16 ± 0.07. This does not overturn the earlier fork: both recurrent
seeds remain dramatically above lookup addressing at 0.014 and curriculum at
0.006. Shared iteration still generalizes where exposure does not. But its
magnitude is seed-sensitive.

Masked pretraining narrows the seed spread from 0.139 to 0.029 and improves the
weak seed by 0.100. With only two seeds, it cannot honestly claim a mean lift;
the apparent difference lies inside the cold arm's own variation. The supported
conclusion is “stabilizer,” not “depth solution.”

This is what a useful negative result looks like. It narrows the next
experiment. Recurrence currently lives in the address encoder, while pointer
queries and decoder attention still consume depth-naively. Version 0.6 will
ablate shared iterative computation through those consumers rather than simply
installing more named recurrent blocks.

The release checkpoint has a runnable demo that generates fresh analogy
problems. At trained depth, it exactly reconstructs held-out transform/shape
combinations. On deeper trees, it prints both successes and failures. The demo
does not select only the flattering examples because the wall is part of the
finding.

## Vision: begin with the figure's source, not billions of captions

Multimodal systems such as SigLIP and Gemma show the power of learning broad
image-text representations at enormous scale. SigLIP uses pairwise sigmoid
loss for image-text alignment ([paper](https://arxiv.org/abs/2303.15343));
SigLIP 2 adds multilingual, localization, and self-supervised objectives
([paper](https://arxiv.org/abs/2502.14786)). Gemma 3 integrates visual
understanding into a 1B–27B family
([technical report](https://arxiv.org/abs/2503.19786)), while Gemma 4 explores
an encoder-free architecture that consumes raw image and audio patches
([technical report](https://arxiv.org/abs/2607.02770)).

Those are important inspirations, but not templates we can shrink naively.
They buy broad perception through large learned representations. Our first
visual question is narrower: how much scientific visual reasoning is already
structured before it becomes pixels?

A mathematical diagram may begin as SVG, TikZ, a plotting specification, or a
geometry scene. That source contains paths, nodes, edges, coordinates, labels,
and exact relationships. Rasterizing it and asking a tiny model to rediscover
everything would discard the best supervision available.

The proposed first experiment renders corpus statements into diagrams and asks
whether a formula and figure are structural twins. One arm consumes normalized
SVG or scene-graph trees. A parameter-matched pixel arm is the honest control.
The model points visual elements into symbolic slots; exact incidence,
measurement, topology, and consistency remain symbolic.

If parsed vectors win on held-out structure and style, the project gains a
third modality without a large encoder. If pixels win, or normalization erases
the features needed for correspondence, the parse-first claim is falsified or
must be narrowed. Either result is valuable before moving toward natural
images.

Natural images will eventually require uncertain perception. Even then, an
object detector or small visual encoder can be treated as a proposer. Its
objects and relations enter the frame as attributed observations, not verified
facts. The harness can seek another view, check geometry, use a tool, ask, or
abstain. Correcting the observation store need not retrain the reasoning core.

## How far from the golden chicken?

At the start of this cycle, the honest score for the integrated capability was
zero: useful components existed, but no end-to-end story process did.

Now the system can execute a three-beat golden-chicken story under declared
premises; enforce setup/payoff and no-deus constraints; retain state across a
clarifying question; revise a frame-private value without laundering it into
world truth; retrieve vocabulary and formal structure; and model what another
agent did or did not witness.

That is meaningful progress toward the story. It is not yet comparable to an
LLM response in fluency, breadth, or open-ended instruction following.

The remaining path is clearer:

- replace the deterministic oracle with a tiny learned action/tactic policy;
- apply tactics live in Lean and search through failed branches;
- parse a bounded but growing range of natural requests into symbolic needs;
- maintain user and story frames over longer conversations;
- implement PROVEN-gated durable writes;
- ground analogy tasks in real corpus families;
- carry recurrence into the components that consume deep structure;
- build a constrained surface renderer that can vary prose without varying
  facts;
- add visual structure as another pointable, verifiable modality;
- only then test external reasoning and language benchmarks under the 64 MB
  budget.

The long-term artifact is not meant to be a tiny imitation of a giant language
model. It is meant to exploit a different division of labor. The corpus can
grow by audited edit rather than retraining. A proof can be checked by a prover.
A story can be locally fictional and globally honest. A user's preference can
be remembered without becoming fact. A retrieval can succeed without promoting
its contents. A visual observation can remain uncertain until another channel
confirms it.

The small model's job is not to contain the world. Its job is to navigate a
world whose relationships remain visible.
