# The limit is no longer method

*A conversation you can finally drive, a model that meets its real ceiling and
loses, a write that dares to happen — and the honest admission that the thing
holding this project back is no longer how it works, but how little it knows*

There is a moment in every research project where the interesting question
quietly changes. For a long time the question here has been *method*: can a
model this small — tens of thousands to a couple of million parameters — do
genuinely compositional work if everything with a closed form is computed
outside the weights and handed to it as an interface? Parse, canonicalize,
check equality, address structure, verify a proof: none of that lives in the
network. The network only points.

Across seven releases the answer to the method question kept coming back *yes,
and here is the baseline it has to beat*. v0.8 continues that discipline and, we
think, closes the method question for now. It also makes something else
undeniable, which is the real subject of this post: the limiting factor is no
longer method. It is scale, and external relevance, of the knowledge the system
reasons over. But first, what shipped.

## The conversation can now be driven

We keep returning to a small, stubborn example: a story about a golden chicken.
One person asks that their version lay silver eggs, another asks for blue, the
first changes their mind to copper. Since v0.6 the system has held that
conversation as signed, owner-private state over one shared public story, and
since v0.7 it has survived its own restart. What it could not do was *author*.
The story rendered through a single fixed template. The surface could not vary,
and — more importantly — "is this prose still faithful to the accepted facts?"
was not a question the system could ask itself.

v0.8 makes the conversation authorable. A constrained surface pointer renders
the same accepted facts in prose that genuinely varies its wording — a
distinct-surface ratio of 0.98 across fifty seeds, against 0.06 for a rich fixed
template — while a control proves that the varying never moves a fact. That
control is the part worth telling honestly, because the first version of it was
wrong.

The first control checked that every accepted fact's anchor words were present
and that no foreign egg-color word appeared. It looked sound. An independent
adversarial reviewer — the same discipline we apply at every trust boundary —
built four narratives it certified as faithful: one that appended "the golden
chicken was a thief who had poisoned the farmer's well," one that gave the
copper eggs to the neighbour's grey duck, one that declared the whole story a
lie, and one that dropped the complication beat while keeping a coop as scenery.
All four passed. A presence check cannot catch a fact that is *added*, *negated*,
or *misattributed*, because those do not remove any of the right words.

The verdict was DO NOT MERGE, and the fix was not a patch. The control became a
*closure* gate: it tiles the rendered prose into segments, each of which must be
an approved way of stating one accepted fact, and then requires that the covered
facts equal the accepted facts exactly, with the beats in the right order and no
obligation discharged before it is planted. Under that gate, added content
leaves an untileable remainder; a wrong owner is not an approved segment; a
dropped beat fails coverage; a reversed narrative fails ordering. All six
adversaries — the reviewer's four plus two of ours — are now caught by name.
The gate reads the surface and trusts nothing the renderer asserts about its own
faithfulness. That is the property that makes "the conversation can be driven"
a claim rather than a hope: a person, or a less constrained author, can now put
words in, and the system can tell whether the words still mean what was agreed.

## A model that meets its real ceiling, and loses

In v0.7 we built a corpus-analogy task and then, in the same release, confessed
that our own split was inflated: the "families" were typed skeletons, so a blind
nearest-template rule scored a headline 0.400 largely by seeing each held-out
shape's untyped form still present in training. The honest ceiling, we
disclosed, was closer to 0.10–0.14 — and we deliberately did *not* re-roll the
split to make the number nicer, because re-rolling against a measured ceiling is
how a benchmark launders its own result.

v0.8 pays that debt twice. First it adds the untyped-shape holdout the split
should always have been — cut on shape, not typed skeleton — and measures its
blind ceiling at 0.1069, with zero leak: not one held-out shape survives in
training. Then, for the first time, it trains a model against that ceiling. A
1.49-million-parameter pointer, three seeds, fully fit on the training rows,
scores 0.104 ± 0.012 on the strict shape holdout. It beats no blind baseline on
any of the four holdouts. On genuinely unseen structural shapes it internalizes
no more of the pointing mechanism than a cheap edit-distance replay.

This is not a disappointment; it is the measurement. This lane, we have said
from the start, tests *pointing*, not reasoning — add two corpus declarations
and a plain symbolic solver reaches 1.000, so the residual a model could learn
is small by construction. The result confirms it: the residual is not there to
be learned on this distribution. An independent reviewer recomputed the whole
thing from the per-seed data, retrained two fresh seeds to check the straddle,
and confirmed the negative holds. Training more parameters on the same data
would not change it, and the ceilings have been telling us so.

## A write that dares to happen

For two releases, PROVEN-gated WRITE has been a gate that stages and never
accepts. It would take a machine-checked proof, regenerate a formal skeleton,
check that the skeleton corresponds to the citing statement, run fourteen
checks — and then leave `approval_granted` empty, every time. It was a careful
refusal machine.

v0.8 lets it act. A candidate that clears every gate is now *applied*: the
audited seed is written to disk and its corpus regenerated by one trusted
generator — never by candidate code, never as a direct `nodes.json` copy — and
a receipt records the exact transition so it can be reproduced. The engineering
around that write is where the honesty lives, because a durable write is only as
trustworthy as its failure modes. The write is atomic (temp file, fsync,
rename), so a crash mid-write leaves the old bytes or nothing. Rollback is
tracked before the first byte is written, so a failure cleans up even the empty
directory a file-only check would miss. The receipt is written inside the
rollback guard, so there is never an applied change without a diffable receipt.
And after the write, the system asserts that the *only* files whose bytes
changed are exactly the declared seed and corpus — not a script, not another
corpus, not the repository root.

An independent reviewer spent a full pass trying to break it: to make candidate
content escape the target corpus, to execute candidate code, to make what was
applied diverge from what was audited, to redirect the receipt. Every attempt
failed. A refused candidate still leaves the tree byte-identical. The honesty
boundary stays bright: acceptance means a receipt exists and the audited delta
was applied by trusted code — not that the statement is true.

## A negative that finally names the wall

The depth experiment has been a closed negative since v0.6: address-only pointer
construction extrapolates best, and adding recurrence to the consumers makes it
worse, not better. But its out-of-distribution number carried a quiet blind
spot — it was computed on 2,450 of 3,000 generated rows, because 550 rows
exceeded the model's copy budget and were silently dropped from the denominator.

v0.8 removes the blind spot and then asks the obvious question. The unconditional
metric — scored over all 3,000, the 550 excluded rows counted as the failures
they are — is now reported beside the retained one, with the exclusions broken
out by depth (all of them depth 4 and 5, the deepest rows). And then we enlarge
the interface budget so nothing is excluded at all, and measure whether that
moves OOD. It does not: the movement is inside the pre-registered materiality
bar, sign-inconsistent across seeds, and the previously-excluded rows still score
zero even fully untruncated — because their targets run past any length the
model was ever trained on. The copy budget was never the wall.

We had also predicted where the remaining failures would concentrate: at the
deep end of the sequence. We were wrong, and we left the prediction standing and
wrote the correction beside it. Three-quarters of the first decode errors happen
in the *earliest* deciles. The cliff is an early-token failure, not a deep-tail
collapse — a fact about the interface, not the budget, exactly as the ablation
implied.

## The part that matters most: the limit is no longer method

Step back from the four lanes and the pattern is unmistakable. The method works.
The engineering and the experimental hygiene are, we will say plainly, unusually
high — every claim is forced to beat a capability-blind baseline, negatives are
first-class, predictions are registered before they are scored, and a trust
boundary does not merge without an independent adversary trying to break it.
This is one of the cleanest working statements of "put the closed forms outside
the weights" that we know of.

And it is all happening inside a closed world of 221 hand-authored nodes.

That number has not moved since v0.7. Everything in this release — the
proof-search curve, the analogy splits, the durable conversations, the visual
oracle, the write path — is real and carefully measured, and all of it lives
inside a body of knowledge the authors fully control. The moment this system has
to deal with an uncontrolled, larger, messier formal or semi-formal corpus, most
of the current numbers become unknown. Not wrong — *unknown*. The structural-twin
claim, the specialization graph, the residual-learning ceilings: they are
interesting exactly to the degree that they survive contact with knowledge
nobody curated to be well-behaved. Hand-authoring 221 nodes proved the method.
It cannot carry the thesis.

So the majority of effort now pivots, and the next release makes the pivot its
headline. Two moves, in priority order.

**Make the corpus non-toy, by ingestion.** The authoring pattern — a `seed_*.py`
script plus a schema — is already there. The next step is to point it at
knowledge that already exists and is already verified: miniF2F-style problems,
Mathlib theorems turned into statement nodes, formalized statements from arXiv
papers that ship with Lean or Isabelle proofs, a cleaned ProofWiki extract. The
matcher, the specialization graph, and the proof-search neighborhood need
thousands, then tens of thousands, of nodes before the twin and residual claims
are interesting outside the lab. The instruction is *ingest, don't invent*.

**Treat programming as a first-class discipline.** The architecture is almost
perfectly shaped for it: source to AST, AST to canonical form, canonical form to
structural address, a pointer residual, and an external verifier — Lean for
properties, Z3 for SMT, or, at the floor, a type checker and unit tests.
Verified code becomes another set of nodes. Synthesis, debugging, and "find the
structural twin of this algorithm" become the same operations the system already
runs over physics and economics formulas. It is the clearest route to a
capability an outsider immediately understands and can test, and it comes with a
natural, effectively unlimited corpus.

The guardrails matter as much as the moves, and we are writing them down in
`DESIGN-corpus-scale-and-programming.md`. Ship the open harness — done this
release — and then stop expanding surface area until it is load-bearing.
Hybrid only at the edges: a larger language model is welcome as a proposal
generator or a fluent front-end, but it must be filtered through the same
closed-form interfaces and the same verifiers, and the moment it starts owning
structure or equality, the project has quietly become a RAG-plus-LLM wrapper
with extra steps, and the thesis is gone. Keep the brutal internal baseline
discipline, and add an external one — a benchmark the architecture can win
*because* of its design, not in spite of a small corpus. Structural-analogy
recovery across formalized scientific papers; verified code completion on a
held-out library with formal specs. Something that forces the corpus to grow and
gives an outsider a reason to care.

And there are things we will deliberately *not* do next. We will not keep
extending the physics, affect, oscillation, and visual rungs while the core
graph is 221 nodes — they are elegant, and they are demonstrations inside the
same closed world. We will not train more tiny models on the current
distribution hoping for a breakthrough the ceilings have already ruled out. And
we will not chase general LLM fluency scores; that is a different game, and the
rule stands — no external comparison until the input/output contract maps
honestly onto the capability actually built. The open harness earns the first
half of that contract. Scale earns the rest.

That is the honest state of the project after v0.8. The method is done proving
itself. What it needs now is something real to chew on.

*The shipped evidence, every registered prediction and its adjudication, and the
corrections we attached rather than edited away are in the release notes and in
`DISCOVERIES.md`. The next increment is staged in
`DESIGN-corpus-scale-and-programming.md` and planned in `ROADMAP-v0.9.md`.*
