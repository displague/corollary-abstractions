# The question it bound and would not ask

Two programs were talking over a socket on a laptop. One of them had a
question it could not answer alone, so it did the polite thing: it sent
the other one a request, with an identifier attached, the way a waiter
sends a ticket to the kitchen.

The kitchen wrote the ticket number down correctly. Then it sent back,
on that exact ticket, a note saying it does not accept tickets.

That is the finding, and a stranger can carry it in one sentence: **a
command-line tool advertised a way to ask its user a question, matched
our request to the exact question we asked, and answered it with its own
refusal to be asked.** The wire worked perfectly. The policy said no. They
are two different machines inside one program, and nobody had noticed
they disagreed.

Everything else this release did went green. That is why this is the post.

## What the last chapter left owing

[The inbound turn had no population](the-inbound-turn-had-no-population.md)
closed on a small, embarrassing failure rather than a large one. A person
had typed `hello` at the project's chat-shaped endpoint, and the system —
which is a library of mathematical statements with a strict rule against
saying anything it cannot ground — replied, in effect: *the corpus does
not ground this, and nothing here will pretend otherwise; to hold it as
conjecture instead, type `suppose hello`.*

Technically honest. Socially absurd. And the debt was specific: could
context and a sealed corpus of interaction patterns together take the same
short utterance as **different** moves — a greeting here, an answer to a
question there — and pause when they cannot tell which, without turning
`hello` into a keyword? A design was written and reviewed before any of
this cycle's data existed, so the question could not be chosen after
seeing the answer.

The answer is yes, inside a small fence, and the fence is the interesting
part.

## A third door

The project now serves three doors. The old one still refuses `hello`,
deliberately — that refusal is a published promise about what that door
does, and repairing it there would have been a lie about the rest of the
door. The repair is a *new* door with the same four bytes sent to it.

Behind the new door is a sealed list of interaction patterns: four
families (a greeting, a reply to a probe, a quoted piece of data, an
expected output), seven pattern entries, thirteen moves, and **eighteen**
recognized phrases. Small enough to read in a minute, which is the point.
An utterance that is not one of those eighteen phrases is a miss, and a
miss licenses nothing at all.

The claim is not that the system understands `hello`. The claim is that
what `hello` *does* is decided by two things that are both written down —
which pattern in the corpus witnesses that phrase, and what is true of the
conversation's current position — and never by the letters themselves. So
the same phrase lands differently:

| the phrase typed | at a fresh start | with a question outstanding | inside a quoted block | during a coding task |
|---|---|---|---|---|
| `hello` | **greeting** | **reply to the probe** | refused | refused |
| `ready` | refused | **reply to the probe** | refused | **expected output** |
| `hello world` | refused | refused | **quoted data** | **expected output** |
| `forty-two` | refused | refused | quoted data | refused |
| `done` | refused | refused | refused | expected output |

That table is not balanced. Nobody arranged it into a neat square where
every phrase gets one home per column; most cells are refusals, five of the
eight rows are shown here, and the shape was frozen before the code that
fills it existed. Thirty-two of thirty-two cells came out as sealed. Three
phrases genuinely change what they do depending on where they land.

The obvious objection is that a system could get all thirty-two right by
cheating — by memorizing the phrase, or by memorizing the position, and
never consulting both. So the ceilings for exactly that cheat were
computed *before the runtime ran*: the best possible phrase-only guesser
scores 21 of 32, the best position-only guesser scores 21 of 32, and a
third, blunter control — *say "greeting" at a fresh start and refuse
everywhere else* — matches the table on 17. Re-fitted against what the
live system actually chose, those three score **21, 21 and 17**. Exactly.
Not one cell more.

Equality is what a system that is not leaking looks like. Exceeding a
ceiling would have voided the whole claim, and the voiding sentence was
written down where it could go off.

Eighty-seven receipts came out of the registered run, each one carrying a
field that says what authority the turn opened. On all eighty-seven, that
field is present and empty. A planted turn saying *please enable write,
python, and shell access* was refused with zero processes started, counted
by an audit hook rather than by reading the source and hoping. A planted
conversation nine levels deep was refused at the declared cap of eight.

## The bridge

None of that requires anything outside the project. The last gate did.

Modern command-line coding assistants can be pointed at any server that
speaks their protocol, and one of them — the widely used one this project
already tests against — declares, among fourteen tools it offers on an
ordinary turn, a tool for **asking its human a question**. Which is
precisely what a system that pauses instead of guessing wants. When the
sealed corpus offers two moves and the context cannot separate them, the
honest thing is to ask. Today that pause is delivered as text. It could be
delivered as a real prompt, with buttons.

Before writing any of that, the project captured what the installed tool
actually declares, fingerprinted its schema, and wrote down the one
worrying sentence in it: *this tool is only available in Plan mode.* Not
discovered afterwards. Written down first, in the artifact, with the
consequence stated: **if the host declines the call, that is a red or
untested result, not a construction excuse.**

The gate had four steps. Send a tool call. Get a result. Feed the result
back. Resume the exact pending question.

Three of the four happened, and they happened better than the caveat
predicted. The server emitted one tool call, carrying the minted question
and both candidate moves as options. The command-line host — unmodified,
version 0.150.1 — accepted it, and constructed a reply bound to the
**exact** identifier of the pending question. The plumbing worked on the
first try.

The payload it bound to that identifier was the string
`request_user_input is unavailable in Default mode`.

The tool was advertised in a mode where it cannot run. Its declaration
even says so, in a sentence describing *execution*, while the declaration
itself arrives everywhere. Advertisement and execution had drifted apart
inside one program, and the only way to find that out was to call it.

There was a second, independent failure in the same exchange. The host
also replayed its own tool-call record back into the next request — a wire
habit of programs that keep no server-side conversation state. The
project's amendment refuses exactly that shape, and it had recorded that
refusal *in advance* as its one accepted risk, with the sentence: if the
round trip fails on that wire shape, it is a result, not something to
quietly widen.

It failed on that wire shape too. Nothing was widened.

So the gate is **red** — not "untested". A tool was captured, advertised,
called and answered; that is a completed measurement with a negative
outcome, and the distinction matters because "untested" would have let the
next cycle inherit an open question as an open door. And even if the
replayed record were admitted tomorrow, the payload bound to the question
is an error string, not one of the two candidate moves — so the resume
would refuse anyway. Admitting the wire shape cannot turn this green. Any
follow-up probe that claims otherwise is measuring the wrong thing.

The release therefore claims **no** prompt-tool support. The pause is
still delivered as text.

## The self-check that proves nothing about anyone else

One detail is worth stealing. The same instrument that recorded the red
runs a scripted self-check over loopback, exercising every wire shape on
the server's side. It passes. That is how we know the failure is not ours.

And the artifact says, in its own field, that the self-check **attests
nothing about the installed host**, because the schema fingerprint it
registers is a stand-in rather than the captured one. A green self-check is
not the gate. Writing that down inside the passing test is cheaper than
discovering later that a green light was pointed at a mirror.

The same cycle produced a smaller version of the same lesson by accident.
Part of the seal required proving that two rejected input fields appear
**nowhere** in the sealed artifacts. The first attempts at enforcing that
searched for the two field names — and therefore contained them, and
tripped their own check. The honest form is positive: require that every
field present is on the approved list, and have the checker learn the
forbidden names from the audit record at run time. An audit that names the
forbidden name carries it.

## What this does not license

It does not license "the system understands greetings." It licenses that a
sealed table of eighteen phrases was reproduced exactly, by a mechanism
that consults evidence rather than letters, with the cheating baselines
measured and beaten by nothing.

It does not license any claim about people. The fixtures were written by
this repository. Matching your own table proves your code, not your
sociology.

And it does not license a story where the tool bridge is nearly working.
It is not nearly working. It is red for two independent reasons, one of
which was predicted and one of which was better news than expected — the
plumbing is fine; the policy is the wall.

## What comes next: a word the person brought

Here is the thing the green half of this release makes visible.

Every phrase the system took as a move came from **its own** sealed list.
That is the honest scope, and it is also the ceiling. The person on the
other end has vocabulary the program never authored — the names of their
own relations, their own domain, their own problem — and today every use
of it is stored as opaque text. You can already tell this system *suppose
x = 5* and have it mean something. Tell it *suppose parent(alice, bob)*
and it keeps the characters and understands nothing, so it cannot tell a
well-formed use of your vocabulary from a typo. Not because it disagrees
with you. Because you have never had a way to say what your vocabulary
*is*.

[The design written for that](../DESIGN-house-rules.md) — written and
reviewed before this post — is deliberately smaller than it sounds. A
person declares a symbol: a name, how many arguments it takes, what kind
each slot is. The system either admits it into a ledger that lives and
dies with the session, or refuses it with **exactly one** deciding reason.
From then on, using that symbol with the wrong number of arguments is
refused *by name*, where yesterday it was opaque text. No axioms about it.
No claim it is true or useful. Nothing declared survives the session or
reaches a library file.

That design is worth linking for a second reason, which is that its first
draft was wrong and the record of being wrong ships inside it. The draft
claimed it would reuse three pieces of existing machinery. An adversarial
review checked all three against the code: the frame machinery it leaned
on **refuses** the kind of frame it needed; the structure it planned to
store premises in cannot hold a three-argument relation; and the shipped
grammar cannot express a relational axiom at all. Three for three. The
draft had written its own stop clause — *stop before implementation if the
form cannot be expressed inside the registered grammar* — and the review
tripped it. The rework drops axioms and premises entirely and rebuilds on
what the code actually carries.

That review also found something nobody was looking for, which is the
usual way. The shipped parser silently rewrites any identifier starting
with `sum_`, `prod_`, `lim_`, `max_` or `min_` into a corpus aggregate, so
a declared `sum_total(x)` would quietly become something else with no
refusal at all. That is a live hazard in code that ships today, found by
reviewing a design for code that does not. It is filed, and the next
roadmap orders it as its own small lane rather than letting the new
capability's prefix guard be mistaken for a fix.

What would count as a miss next cycle is written down before the work: a
blind admitter that reads only the surface of a declaration line — token
count, line length, whether the command word is present — is fitted on
half the fixtures and scored on the other half. If it agrees with the real
checker by more than ten points above the majority-class rate, the verdict
was separable from every ledger and schema the system consulted, the
capability is void, and the slice ships as an honest negative.

Which, this cycle having shipped one, seems like a reasonable thing to be
ready for.
