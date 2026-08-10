# Design: the epistemic ladder

The system has an ontology; this document specifies its epistemology. Six
concepts (unknowns, disorder, conjecture, truth/provability, drift and
correction, falsehood) are not separate features but one ladder of
epistemic statuses, and the house rule that has won every experiment
applies: **each rung has a closed form, so status is symbolic and
structural — never learned.** The one genuinely graded judgment, and
therefore the only one weights should own, is *which conjectures are
worth proposing*.

## The ladder

| rung | closed form that decides it |
|---|---|
| PROVEN | a machine-checked proof exists (`verified_by` → Lean artifact) |
| VERIFIED | the statement is a corpus node / recorded identity |
| CONJECTURED | registered with its adjudication procedure, awaiting verdict |
| UNKNOWN | a well-formed statement with a hole (WH-slot); a question |
| REFUTED | its consequences contradict a VERIFIED statement (derives ⊥) |
| UNGROUNDED | parses, but groundedness score below threshold |
| GIBBERISH | no parse |

Groundedness score := fraction of a statement's non-trivial constituents
that match known forms (`decompose.py`); it grades "disorder" instead of
gating it.

The score is reported **by provenance channel**, because "matches a known
form" was measured hiding *whose* form it matched: `external`,
`prior_corpus` (other corpus, shared discipline), `same_corpus` (siblings
authored in the same act), `recursive` (self/definitional), and
`pattern_absorption` (a known form with a slot swallowing this
constituent's structure). Channel counts partition the same numerator over
the same denominator, so the aggregate is unchanged and only its
attribution is new. Any future use of groundedness as an *admission*
signal must read the channels, not the aggregate.

**Corrected 2026-08-09 after review.** This paragraph originally read "a
corpus can reach 1.000 on `same_corpus` + `pattern_absorption` alone, and
one in the corpus does (`data/provability`)". That is false of corpora.
What was measured: `data/provability` grades 1.000 aggregate while taking
0.967 of it from `same_corpus` (0.775) + `pattern_absorption` (0.192),
against `external` 0.033 — five of its six statements take *no* external
credit at all, and 26 individual statements graph-wide do reach 1.000 on
those two channels alone (5 of provability's 6, the rest spread over
`temporal_logic`, `narrative`, `morphology`, `differential_topology` and
`geometry`). No *corpus* mean reaches 1.000 on them; provability's
0.967 is the highest, and the only other corpus grading 1.000 aggregate
(`differential_topology`) takes 0.634 there against 0.367 external. The
conclusion survives the correction — a near-perfect aggregate can be almost
entirely self- and absorption-supplied, which is exactly why an admission
gate must read channels — but the number was wrong and is now stated as
measured.

Two further readings the channels demand:

- **`external` is an upper bound, not a point.** A constituent with owners
  in several channels is credited to the most independent one, and 190 of
  the graph's 440 exact constituents are multi-owner (all 190 credited
  `external`). `channel_summary` therefore publishes the least-independent
  counterpart beside every figure (`external_lower`, `independent_lower`,
  `self_certifying_lower`): graph external is 0.535 generously and 0.246
  conservatively. A gate must be argued against the *lower* bound. The
  provability readout is rule-invariant (0.033 either way) and it is the
  only corpus flagged `self_certifying` under either rule.
- **`recursive` is structurally empty at the shipped defaults**, so the rung
  has four live channels, not five. See `scripts/decompose.py`.

## Where each concept already lives

- **Unknowns**: WH-slots and typed template slots — first-class since the
  qa/solvex tasks; unification binds them.
- **Disorder**: parser rejection (GIBBERISH) + form-matching (UNGROUNDED,
  graded by the score).
- **Conjecture**: the HYPOTHESIS tier; registered-prediction discipline
  (GRPO=z-score cashed, canon-ceiling falsified); proposals live in
  `reports/`, never in `inferential_links`. Schema now carries
  `conjectured` as an `epistemic_status`.
- **Truth vs provable**: `epistemic_status` kinds vs the prover lane;
  bridged by the optional `verified_by` field linking a node to its
  machine-checked artifact. Truth-vs-provable becomes structural.
- **Drift & correction**: process level — drift detectors in the matcher,
  public retractions, BACKLOG as correction queue. Model level — the syn
  result: weight-stored knowledge drifts (chance OOD), extrinsic
  knowledge doesn't; therefore corrigible facts live extrinsically and
  correction is an edit, not a retrain.
- **Falsehood**: BOT exists algebraically; the two reasoning directions
  are now authored (ex falso as `IMPLIES(BOT, PROP)`; reductio as
  `IMPLIES(IMPLIES(PROP, BOT), NEG(PROP))`; set-theoretic echo: the
  empty set is LEQ-minimal). *Operational* falsification — deriving ⊥
  along a branch — is the prover search loop, the v0.4 thesis; the
  extraction already contains `by_cases` hypothetical splits.

## The residual

The model proposes; the ladder disposes. "Abstract thought," in this
system's honest vocabulary, is high-quality conjecture generation over
grounded constituents — everything else on the ladder is exact.
