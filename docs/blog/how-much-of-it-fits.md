# How much of it fits

*We set out to make a toy corpus non-toy by pouring real formal mathematics into
it. What we got back was not a scale number but a reach number — about a third —
and two walls we can now see clearly. That is the better result.*

For eight releases the hard question here was *method*: could a very small model
do compositional work if everything with a closed form — parsing,
canonicalization, equality, the lexicon, structural addresses, verification — was
computed outside the weights and handed to it as an interface? The answer kept
coming back yes, with unusual hygiene: every claim forced to beat a
capability-blind baseline, every negative result kept, every trust boundary
reviewed before it merged. By v0.8 that question was substantially answered, and a
different one took its place. The thing holding the project back was no longer how
it works, but how little it knows: 221 hand-authored statement nodes across 22
disciplines, a closed world the author fully controls.

So v0.9's job was to break that closed world by ingestion — to point the existing
seed-and-schema pipeline at real formal sources instead of inventing each node by
hand. The design doc was explicit about the first honest deliverable, and it was
not a node count. It was a *coverage number*: what fraction of a real formal
source expresses in the corpus grammar at all, measured before any claim about
scale. Because if you cannot say how much of Mathlib or miniF2F your grammar can
even represent, a bigger corpus is just a bigger pile of things you can't talk
about.

## The instrument, and what it says

We built one shared classifier that takes a formal statement, reduces it to the
corpus's head-algebra skeleton — relations over slots, the Boolean operators,
arithmetic, a handful of function heads — and reports either COVERED or the first
construct it has no head for. A statement counts as covered only if the whole
conditional `if these hypotheses then this goal` reduces to that skeleton with
numerals and typed variables at the leaves. One rule is load-bearing: a head
counts as *supported* only if a node already in the corpus actually carries it. A
test checks that against the corpus, not against anyone's memory.

Then we ran it, on three real, digest-pinned Lean sources:

- **miniF2F** — 488 competition problems — **29.7%**.
- **Lean-workbook-proofs** — 29,750 theorems, each with a real proof — **64.1%**.
- **Goedel-Pset-v1** — **1,732,594** statements — **32.8%**.

The number to sit with is not the 64. It is that the two competition/olympiad
sources land near thirty, and the one hand-curated inequality set is the outlier
at sixty-four. Lean-workbook is dominated by exactly the algebraic inequalities
the grammar was built around; it is the closed world in a different costume. The
1.73-million-statement set, formalized by a model from word problems, is the
messy, uncontrolled thing we actually wanted to meet — and there the honest reach
of the grammar is about a third. At that scale the single largest gap is not even
a missing operator: 22% of goals have *no relation at all* that the grammar
recognizes — they are bare predicates and definitions, claims that simply are not
(in)equations. You do not learn that from 221 curated nodes. You learn it from a
million and a half you did not choose.

## The part I'm proudest of is where the number went down

Three times this cycle, an independent adversarial reviewer read the classifier
and found it counting things it should not have. Each time the number moved down,
and each time that was the honest core of the result.

The first pass reported the coverage a few points too high because it treated
modulo and divides as heads the corpus supports. It does not — the only `MOD` in
the whole corpus is a *linguistic modifier* from the morphology discipline, not
integer modulo, and there is no divides head at all. I had asserted a capability
from the surface symbol instead of checking it against the corpus. We reclassified
them as the gaps they are.

The second finding was sharper. Over the natural numbers, `a / b` is not real
division — it is floor division, `Nat.div` — and `a - b` is truncated
subtraction, and `x^(1/3)` is `x^0`, which is `1`. So a statement like
`(1 + 1/n)^n < 3`, which looks like it is circling the number *e*, is over the
naturals just `1 < 3`: trivially true, and trivially the wrong theorem. The
classifier had been reading the surface arithmetic and ignoring the carrier. We
taught the extract to record whether each variable lives over a field or over the
integers, and to treat integer division, monus, and fractional exponents as the
gaps they are unless something proves the arithmetic is real. That single
correction moved Lean-workbook from 68% to 64% and miniF2F from 31% to 30%.

The third only showed up because 1.73 million statements contain shapes that
thirty thousand do not — cross products, scalar multiplication, lattice
meets, the imaginary unit spelled six different ways, and a base-*b* logarithm
`log b x` that the classifier was accepting because it was blind to how many
arguments `log` takes. We caught all of it because the scale run carries its own
audit: it counts, for every one of half a million covered statements, whether any
non-grammar glyph survived. That count is committed in the artifact, and a test
insists it be zero. An audit you can read is worth more than a claim you have to
trust.

None of these corrections is embarrassing. They are the mechanism working. The
reusable rule that falls out of all three is one sentence: a supported head is a
claim to verify — against the corpus, and against what the operation actually does
under its carrier — never an assertion you can read off the glyph.

## The two walls

We measured the reach. We did not, this cycle, author the covered statements into
the graph — and the reason is the more interesting deliverable.

The corpus has an honesty ladder. A statement can be *stated*; it earns the
`verified_by` bridge only when a machine-checked proof backs it. The trouble is
that the checker is entirely offline: it looks a proof up in a manifest and parses
a committed record of its tactic states — there is no Lean toolchain in the repo —
and the part that checks the proof actually *matches* the statement understands
only propositional logic, the algebra of and/or/not/implies. Every theorem we want
to ingest is arithmetic. So an ingested inequality, even one that comes with a
real proof, cannot earn a `verified_by` today. Not because we did it wrong —
because the bridge only reaches one side of the river, and we can now say exactly
where it stops.

That is the first wall, and it is precise. The second is the coverage remainder
itself: two-thirds of real formal math needs heads the grammar does not have — a
way to say "for all" and "there exists," a first-class notion of an unknown
function, indexed sums, and above all a relational head for the claims that are
not equations at all. These are not cosmetic gaps. They are the specification for
what to build next.

## What v0.10 does with this

The next cycle is not "ingest more." It is: extend the grammar to the heads the
measurement demanded — each one justified by the coverage number it moves, on all
three committed sources, not by taste — and build the external verifier that the
`verified_by` wall requires. A type-checker and unit tests to start, Lean to
follow; the same verifier that lets an ingested theorem earn its bridge is the one
that turns *programming* into a first-class discipline, running the architecture's
existing operations over code with the checker swapped in. Only once those two are
in hand does authoring the covered subset — and finally recomputing the twin and
specialization ledgers on a graph that is thousands of nodes instead of hundreds —
become honest work rather than a pile of unverifiable assertions.

Eight releases ago the question was whether a two-megabyte model could point at
structure it was handed. It can. The question now is how much structure there is
to hand it, and this release answers the first honest version of that question
with a number and two walls instead of a boast. A third of the way in, with the
map of what's missing drawn to scale. That is a good place to be standing.
