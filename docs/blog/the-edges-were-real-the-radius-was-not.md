# The edges were real; the radius was not

The [last chapter](one-row-was-carrying-the-table.md) ended with a
promise: unsaying gets a receipt. This
project keeps its exact knowledge outside the model weights, in a
library of statements anyone can inspect — and it had just discovered
that it could not say what else moves when one of those statements is
found wrong. Twice in its history it has retracted a result, and both
times the blast radius was worked out by hand, after the fact. So the
next machine had a clear job: given one falsified artifact, compute the
exact set of published claims downstream of it, and seal that set under
a digest.

We built it. And the gate we froze for it said no.

## What the machine was

A provenance graph over everything the repository commits: generator
scripts, data files, generated ledgers, and one node per section of
every published document, each anchored by its heading and a hash of
its text. The ledgers now sign their own lineage — each writer emits
the exact inputs it read, hash by hash. On top of the graph, a radius
tool: point at one artifact, get back a certificate naming every claim
downstream. And because this project does not trust its own tools, an
independent checker — written by an author who was contractually
forbidden from reading the builder's code, and committed to history
before the builder existed — re-derives every certificate from the
schemas alone.

The hard part was never the lineage between files; writers know their
inputs. The hard part is the last hop: connecting a *sentence in a
document* to the artifact that makes it true. Sentences were written by
people who cited nothing. So the builder scanned for citations — six
frozen mechanical rules: explicit paths, file names, writer names,
backticked field names, characteristic words, glob patterns.

## The gate, and what it said

Before the tool existed, we committed the answer key: two hand-audited
lists of every published claim that actually depends on the two
artifacts we would test — twenty-seven claims across eighteen documents,
quotes verified by machine. The tool was forbidden, by a test that reads
its source, from ever opening those files. The gate: each computed
radius must contain every audited claim, within three times the audit's
size. And a blind control: one hundred shuffles of the graph's edges,
each preserving every node's degree and kind — if shuffled edges explain
the audits as well as real ones, the graph knows nothing.

The control came back clean: zero of one hundred shuffles reproduce the
coverage. The edges are real. And the gate still failed, on both
artifacts. One radius covered all eleven of its audited claims but
swelled to fifty-four nodes against a cap of thirty-three —
the flood arriving mostly through one backticked word, `nodes`, which is
both a field in the ledger and half the filenames in the repository. The
other missed two claims outright and doubled its cap. The two it missed
are the interesting ones: they cite only *derived numbers* — a decimal
like 0.490 and its history — with no lexical trace of the artifact they
came from.

That is the finding, and it is sharper than a success would have been:
**information and precision are different capabilities.** The
connections exist; no shuffle fakes them. But prose written by people
cites numbers and concepts, not artifacts, and no defensible mechanical
reading of finished prose can be both complete and precise about what
each sentence rests on. We shipped the void, the certificates, the
attribution table that names which rule caused which flood, and the
instruments — which are green, kept, and now unemployed.

One more thing shipped with it. The written registration of the
adjudication names the two artifacts under test — which made the
registration itself a claim about them, which added it to both radii
before the run. A claim about the graph is a claim in the graph. We
wrote that down and smiled about it, because it is not a paradox; it is
the object working.

## The instrument that came back

The same cycle closed an older account. Two releases ago we suspended
our favorite number — the count of cross-field structural matches — until
a check on what the symbols actually denote could be adjudicated. Last
release that check half-passed: its flags landed where registered, but
the control meant to prove its labels carry information turned out to be
un-runnable, because the label table had been scoped, by its own author,
in a way permutation could starve.

This cycle we re-authored the table the only honest way left: an
isolated context, shown nothing but the twenty-six kind definitions and
the judging rules — not the data, not the old table — ruled on all 325
possible pairs. Against that table the control runs properly, and the
verdict is unambiguous: the real labels flag twenty-one conflicts; the
twenty registered shuffled labelings flag between forty-five and
sixty-one. Real sits below half the shuffled minimum. And the blind author, who had
never seen our analysis, independently made the one judgement our
sensitivity analysis had found carrying the entire instrument — that
Boolean algebra and set algebra are the same thing. The load-bearing
call has now been made twice, by authors who could not see each other.
The suspension lifts, and the number returns to use wearing two
permanent riders: eight of twenty-six groups contain a conflict, and one
row still does most of the work.

## The honest boundary

The void is a void. This repository still cannot certify a retraction
radius; its published claims are still tethered to their evidence by
nothing but memory and audits. The veto's establishment is exploratory
forever — its population is a census with no fresh half. And the
instruments we kept are stewardship, not results.

## Four arrivals

When the cycle's design course ran — three outside advisors, isolated
from the repository and from each other, fifteen proposed directions —
something happened that has not happened before: all three, plus the
void post-mortem written before the course, arrived at the same
sentence. If lineage cannot be recovered from finished prose, it must be
paid at authoring time. One advisor proposed it outright as their first
idea. The other two each drafted it, recognized it collided with claimed
territory, and disclosed the drift.

So the next design is the one everything pointed at: [claims are
emitted, not written](../DESIGN-ledger-first-claims.md). A quantitative
sentence in the covered document becomes a generated artifact of a typed
citation — resolved at emission, refused at emission when the printed
value disagrees with its source. The failed scanner is not thrown away;
it is demoted to the one job its adjudication proved it can do — flagging
the sentence that cites nothing at all. The gate is thirteen frozen
clauses, and its two blind controls can void the whole thing — including
a strict path-matching baseline that this cycle's void never got to
score, and that might genuinely win. The population of sentences and the
document they live in are sealed before anything is scored, because this
cycle also taught us — twice — that a denominator the scored author can
still move is not a denominator.

Next release, the sentence is bound to its source, or it is not printed.
