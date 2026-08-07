# Design: fictional frames and retrieval-as-action

Two extensions toward sustained composition (the golden-chicken test),
both instances of existing machinery rather than new mechanisms.

## 1. Frames: falsehood-as-premise gets a scope

A fiction is a hypothetical frame: "suppose a golden chicken exists"
opens a scope whose premise set extends the corpus. Inside the frame,
the epistemic ladder operates unchanged over a LOCAL corpus:

- Frame declarations are the frame's VERIFIED tier ("the chicken is
  golden" is world-truth *within scope*).
- Later statements are checked against frame + corpus: contradicting the
  frame is REFUTED-against-the-story (chapter three's "silver chicken"
  is flagged exactly as a false physics claim would be).
- Frame truths never leak outward: on scope exit, they revert to
  CONJECTURED-under-premise. The boundary is structural, not stylistic.

This yields non-hallucinating fiction: unlimited invention at the frame
boundary, strict consistency inside it — the inverse of the standard LLM
failure (loose inside stories, falsely confident outside them). Frames
are exactly reductio's machinery pointed at creation instead of
refutation: assume P, develop consequences — just without seeking ⊥.

## 2. Retrieval as an action; UNKNOWN as its trigger

The extrinsic stores (lexicon, skeleton vocabulary, twin ledger,
decomposition index, proof artifacts) are today consulted by pipelines.
For the model to *source* context, retrieval becomes an action type
alongside the two we have measured:

    POINT(pos)      copy from present context        (proven, 1.000)
    GEN(tok)        emit structural vocabulary        (proven, small)
    RETRIEVE(key)   query an extrinsic store          (new)

- **Trigger**: an UNKNOWN — a slot unification cannot bind from local
  context — is the retrieval-initiation condition. The ladder rung IS
  the "should I look something up?" predicate; no learned gating needed
  for *whether*, only taste for *what* (part of the one graded judgment
  weights own).
- **Execution is symbolic**: the query runs against the store exactly
  as the lexicon lookup does; results enter context as pointable
  material (retrieval feeds POINT).
- **Absence handling is already specified**: a miss degrades to
  neighborhood search, then to honest abstention (UNKNOWN stays open,
  stated as a question) — tip-of-the-tongue, never confabulation. A
  frame may also declare an unknown *unresolvable-by-retrieval*
  (fiction: do not look up real chickens).

The knowledge graph thereby stays dynamic, extrinsic, unbound: stores
grow by edit (correction is an edit, not a retrain), and the model's
access to them is an auditable action stream.

## 3. What the story demo still needs (build order)

1. **Temporal logic corpus** (in flight): ALWAYS/EVENTUALLY/NEXT/UNTIL
   as heads; duality ALWAYS(P) = NEG(EVENTUALLY(NEG(P))) is a modal
   De Morgan — predicted twin with the Boolean dualities; the
   until-unfolding recurrence is predicted kin to the state-update
   family (SSM/RNN/belief update). Time becomes structure the matcher
   can see — the substrate for "beginning precedes middle precedes end."
2. **Narrative skeleton corpus** (in flight): story grammars are
   grammars — setup(agent, desire) -> complication -> resolution as a
   typed skeleton family (Propp, Rumelhart), instantiable and
   decomposable like any other form.
3. **Chained composition** — the hard gap, shared verbatim with v0.4
   reasoning chains: each proposal becomes the next step's premise. The
   prover's propose-verify-repeat loop is the backbone; a plot event is
   a tactic applied to story state, checked against the frame.
4. **Expressive rendering** — richer symbolic realizer, or a small
   learned surface model that only points into the extrinsic lexicon.

Story generation and abstract reasoning are one problem here; the
chicken is the friendlier costume.
