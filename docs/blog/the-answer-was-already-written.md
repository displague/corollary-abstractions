# The answer was already written; the model had to type it

The [last chapter](the-edges-were-real-the-radius-was-not.md) ended with a
promise about the next release: *the sentence is bound to its source, or it
is not printed.* That promise is not what this release kept, and the reason
is worth saying first.

The maintainer read the plan and named something the plan could not see.
For three cycles running, this project had been building instruments about
its own evidence — a check on whether cross-field coincidences are real, a
machine for computing what a retraction breaks, and next a discipline for
citing sources at the moment a claim is written. All real, all kept. But
the thing the whole library exists *for* — a person, or a program, asking
it a question and getting an answer — had been sitting parked for five
consecutive releases. So the direction changed, on the record, and the
citation work parked whole with its design and its receipts intact.

The new question was blunt: this project keeps its exact knowledge outside
the model weights, in a library of statements anyone can inspect. Fine.
**What is that worth to somebody at a keyboard?**

We picked an answer we could be wrong about in public: *speed.*

## The wager

A language model writes by sampling. Every word it produces is drawn, one
at a time, from a probability distribution — that is what a language model
is, and its ceiling is how fast it can draw. This project's engine does
something else: it looks a sentence up, or computes a value exactly, or
replays a receipt it already holds. Its ceiling is how fast it can move
bytes.

If that difference is real, then grounding is not only about
trustworthiness. It moves answering into a different *speed class*
entirely. So: build a chat endpoint over the engine, put a small language
model beside it with **the very same source records pasted into its
context**, ask both the same hundred-odd questions, and time them.

The bar was set before anything was built and written into a file we
committed: the engine must be at least **five times** faster, measured on
correct-and-receipted answers only, at correctness no worse than the
model's. Five. If it came in at four, we would have published four and said
the claim was smaller than we thought.

## Keeping ourselves honest, in order

The awkward thing about benchmarking your own work is that you are the
person best placed to cheat, and you will not notice yourself doing it. So
the cycle was built in a fixed order, each artifact committed before the
one that could have been tuned against it: the protocol spec, then the
question set, then the opponent's configuration — and only then the server,
the stopwatch, and the single timed run.

The question set is 119 conversations across seven kinds. Half were sealed:
their first execution was the graded run, and the tool refuses to touch the
sealed half without an explicit flag. Crucially, **the answers existed
before the questions did** — a builder computed every expected answer from
committed files and can prove it never once called the engine it was going
to grade. Two rounds of review then re-derived the entire answer key from
scratch: 46 recomputed values, 73 quotes checked against their source, zero
disagreements.

Four things that review caught are worth more than the number they protect:

- **Any file in the repository could be minted into a certificate.** One of
  the question kinds asks whether a state of a small sealed world is
  reachable. As first wired, the route would answer about any file path
  handed to it — meaning we could have quietly grown the set of questions
  our own system was good at. Now only pre-registered targets answer, and
  everything else refuses by name.
- **A setting we believed in did nothing.** We had configured the opponent
  model's context window in the request body. A live probe found that the
  OpenAI-compatible layer silently drops that field — so the model would
  have been truncating its source material at its 4,096-token default while
  our file claimed otherwise. That is not a small error: it would have
  inflated our result by exactly the mechanism the file was written to
  prevent. Fixed to a server-side setting, and re-verified.
- **The opponent was never told to quote.** On a practice run it scored 5
  out of 45, because it paraphrased material our checks compare exactly. A
  crippled opponent is not a fair fight — worse, it makes the whole
  comparison vacuous, since dividing by zero gives you any number you like.
  So we amended its instructions to say *reproduce the relevant content
  verbatim*, before the graded run. (Read on for what that bought.)
- **Our first measurement was timing a JSON parse.** The first practice run
  clocked the server at 83 tokens per second, which felt wrong. It was: every
  single request was re-reading and re-parsing the entire corpus from disk,
  405 milliseconds of it, before answering anything. We were not measuring
  a mechanism. We were measuring a cold cache.

## The numbers

One run, on the sealed half, on a throttled laptop. The opponent is
Qwen3-4B-Instruct-2507, an open-weights instruct model running at its
vendor's own settings — and it got **the GPU**, while our engine ran on the
CPU.

| | answers correct, with receipts | speed on correct answers (median) | time to first useful token |
|---|---|---|---|
| **the engine, over HTTP** | **49 of 49** — and 100% within every question kind | **3,451 tokens per second** | **25 ms** |
| **the model, handed the same records** | 4 of 49 | **0** | 45 ms |
| the same model, working from memory (reported, never gated) | 1 of 49 | 0 | 53 ms |
| a server that just dumps text as fast as it can | 0 of 49 | 0 | — |
| our own engine with its answers shuffled between questions | 0 of 49 | 0 | — |

The bar was five times. Totalled across the whole run, the engine measures
**220 times** the grounded model's throughput. On the statistic the bar
actually names — the middle question, not the total — the model's score is
zero, so the multiple is not five, or 220: it is **satisfied without a
finite value**, which is a stranger and more honest way to say it than
picking a big number.

The last two rows are the controls, and they are the reason the first row
means anything. A server that streams corpus text at maximum rate, ignoring
what you asked, scores zero — so the measurement is not secretly rewarding
bandwidth. Our own engine, with its correct answers reassigned to the wrong
questions, also scores zero — so the scoring genuinely separates right from
wrong rather than rewarding well-shaped output. Each control had a sentence
written in advance saying what would void the whole result. Neither fired.

## The interesting number is 4

The engine winning was the expected outcome. The opponent scoring 4 out of
49 is the finding.

Remember what this arm is: not a model asked to recall obscure facts, but a
model with **the exact source records in front of it**, explicitly
instructed to reproduce them verbatim. It got zero of 16 corpus
definitions. Zero of 5 twin lookups. Its four credits were all arithmetic —
4 of the 13 questions that ask for an exact computed value, the one kind
where the answer is short enough to survive being retyped.

And here is the part we did not expect: **the instruction to quote did not
help.** The practice run committed after the amendment scored 5 of 45, and
we can tell it is the post-amendment one because each result file records a
digest of the configuration it ran under. The 5 of 45 attributed to the
*un*amended prompt rests on the configuration file's own written rationale
rather than a second committed run — so read this as "the score did not
move", not as two files placed side by side. The amendment was the right
thing to do — it was argued on fairness, before the run — and it bought
nothing.

Which is the thesis arriving from an unexpected direction. We had claimed
that exact content belongs outside the weights. The opponent demonstrates
why, from the inside: **exact content does not survive being sampled
through a decoder, even when the decoder is looking straight at it.** Every
word passes through a probability distribution, and a distribution has no
special respect for the string it was conditioned on. It produces something
*like* the record. The check wants the record.

## What we are not claiming

The claim covers the registered question surface and nothing else. This is
not open-domain parity, and it is not a language model replacement: you
still have to speak the engine's grammar, which is why the server publishes
a machine-readable sheet describing that grammar for an orchestrator to
read once and configure itself from.

Some honest scars, all of them in the release notes with their numbers:

- One field in one result file records the opponent's context limit as
  262,144 tokens. It is wrong — the probe ran before the model had loaded,
  and read the model's *capability* instead of its *setting*. The real
  limit was 32,768, which the same file proves five times over by failing
  five oversized requests. We recomputed the affected reading by hand (it
  did not change), filed the defect, and **left the code exactly as it
  ran**, because quietly re-running a graded benchmark is how benchmarks
  rot.
- Five questions could not be given to the opponent fairly at all: their
  source material is about 130,000 tokens, and no configuration of a 16 GB
  graphics card holds that. Disclosed before the run, reported per
  question, not dropped.
- Two of the seven question kinds hand the model no material and check for
  the engine's own notation, which a prose model rarely produces
  unprompted. Written into the configuration file before the run rather
  than discovered afterwards.
- And the 83 tokens per second from the first practice run is *not* the
  before-half of a speedup story. It was a bug in the measurement, we fixed
  it, and the number we publish is the one from the graded run.

## The graph answers fast. Now it has to speak.

Here is what the run also showed, question by question. The engine is fast
because it *quotes* — it hands you a sentence a person wrote, or a value it
computed exactly. But of the 12,777 statements in this library, **12,515
are machine-ingested records** whose human-readable text is boilerplate.
The engine serves them today with a disclaimer that says so. Quotation has
nothing to quote there. The library answers at wire speed inside a
vocabulary of 262 hand-authored statements.

So the next design — written before this post, which is the rule — is that
the graph should **say its own structures**: not sentences pulled from a
bank of templates, but sentences composed by a grammar from the
mathematics itself, and then *proved* by feeding each sentence back through
the parser the system already trusts and checking that it recovers the exact
structure it claimed to render. `MOD(2 ^ 30, 1000) = 824` should become
something a person can read, with a receipt showing the sentence parses
back to precisely that term. A sentence that fails the round trip is not
printed.

That design has already produced the **next** cycle's first finding — here,
during this rotation, before a line of it was written. Its first draft set
the bar at 90% of all
12,777 statements. Review went and *measured* the parser against the
corpus, and the bar collapsed: only **2,172 statements — 17.0%** — parse at
all under the system's own grammar. The single ingested corpus that is
97.9% of the library's mass parses at 16.3%. Terms that do not parse have
no structure to round-trip against, so there is nothing here to render
faithfully or otherwise.

That is not a setback dressed up as a discovery. It is a fact about this
library that nobody had had a reason to check: **the corpus outgrew its own
template grammar, and nothing had ever asked it to speak.** Every ledger
here counts nodes; none of them counted *parseable* nodes, because until
now nothing depended on the answer.
The bar has been rescoped to the statements that actually parse, and the
parse-rate table — which corpus, which failure class, how many — now ships
as a result in its own right.

[Next release](../DESIGN-sans-template-rendering.md), the graph says a
sentence and hands you the proof that the sentence is the term — or it says
nothing at all.
