# Design — one typed line after the boot list (live session, v0.12 item 5)

Written during v0.11, *before* the tag, so the release notes cannot
choose this after. This note does not implement the loop. It freezes
what “you sit down and type” is allowed to mean.

A newcomer should be able to read this file without the rest of the
repo. Project words appear only after a definition, and the
definition is the subject from then on.

Three antagonist cycles produced the destination. The registered
predictions in §7 are floors for a **future** implementation. No
loop has been added to `scripts/harness.py`.

## Terms, said so they can stand alone

**Boot list.** When the session program starts, it prints which
optional pieces answered a smoke call (a dictionary of English
words, a proof assistant, a neural-net library). Green on that
list means “present,” not “sound.”

**Registered path.** A route a booted piece declared, that the
kernel will let a checker judge. Unregistered work is not
improvised.

**Dispatcher.** The program that sends a need down registered
paths only. If no path claims the need, the system asks or stops
exhausted, with the missing piece named. It does not invent a
path.

**Write gate.** The program that accepts or refuses a proposal to
change the corpus. It already refuses: replacing a seed file that
owns a corpus, sending Python where JSON is required, colliding
ids, citing a failed test as if it were a node. The refuse text is
the check’s name. A passing Python test is a citation of a finite
check, never a proof.

**Recorded session.** Four scripted legs saved as structured
records (`experiments/harness_session.json`). Re-running
`python scripts/session_run.py --check` re-verifies those
records. It is not a person typing.

**Self-grounding.** A part of a statement is owned by another
statement from the same ingested source. “More often than a
matched random baseline” is the claim v0.11 measured and v0.12
will re-measure on sources this project did not fit the emitter
to. That measurement is not a conversation.

## 1. What a person should see

You run `python scripts/harness.py`. It prints the boot list, then
waits. You type one line.

- If the line is a path, relative to the repository, to a write
  proposal the write gate already knows how to parse, that program
  runs. You see its named refuse or accept. On refuse, the working
  tree is unchanged.
- If the line is ordinary language, the dispatcher runs. A
  registered path proceeds, or the system asks, or it stops
  exhausted with the missing capability named.
- Then the process stops.

A second sitting with the legal follow-up the refuse named
(an append document, the same payload as JSON, or withdraw) is
recover. The status is a machine verdict: solved, refused,
waiting, exhausted, or budget. Fluency does not invent a slot, a
path, or a fact.

## 2. Why this note exists (reclamation, not a new product)

v0.8 asked for a live session with a text prompt and an optional
chat-shaped web skin. The release said the system can now be
driven. What landed: the boot list and exit; a program that
rewords an accepted story without moving facts; the dispatcher; a
later recorded session. v0.9 called that pair an earned
foundation. v0.11 and the first draft of v0.12 dropped the
conversational surface from the roadmap.

So v0.12 item 5 is reclaiming a capability the notes already
claimed, not inventing a chat product. A prettier print of the
recorded session is a costume.

## 3. Where this sits in the next cycle

v0.12’s reason for existing is still the held-out self-grounding
measurement (two sources the emitter was not built for). That
stays first. Making the prompt the headline, or blocking the tag
on it before that curve, would steal the cycle.

This loop is **v0.12 item 5**, ordered after that curve (and after
the groundedness gate if that gate is drawn). **Named dependant:**
a person can type the illegal write that a later write-recovery
measurement will rank. That is not a fourth silent carry of “open
harness.”

v0.11 commits this design. It does not implement the loop.

## 4. What “done” looks like (a newcomer can try)

```text
python scripts/harness.py
```

After the boot list, the process waits.

1. Type a path to a proposal that replaces a seed that owns a
   corpus. The prompt prints `seed_ownership` from the write
   program. The working tree is byte-identical.
2. Type a sentence no registered path claims. The prompt asks or
   stops exhausted. Nothing is marked verified or solved.
3. Type a line that is not one of the recorded session’s legs.
   The same two programs still run.

Then the process exits.

## 5. What is not this slice

- A chat-shaped HTTP skin.
- Any ranker (which already-authored edit to try next; which
  recovery document to keep).
- A fifth algorithm source file.
- Open English that authors a new node.
- Rewording of accepted facts sold as authoring new content
  (v0.8 already shipped that render; it stays last for *new*
  content).
- Multi-turn memory across two typed lines.
- Promoting a passing test to a proof.
- A translator from syntax trees to remainder recurrences.
- New matcher operators.

## 6. Loop detection: already cashed, and still a debt

Inside **one** dispatch of **one** need, two registered paths that
bounce that need stop with the cycle named, or at a visible hop
ceiling. That was measured in v0.8. Do not sell it again.

The visited-dead table is rebuilt at the start of each dispatch
call. A second user line that dispatches again starts empty. The
first slice is one line then stop, so that hole is not this work.
A later multi-turn loop must not claim session memory it does not
have.

## 7. Predictions to freeze before the loop exists

Registered before `harness.main` reads a line. Fired and missed
both land in §8.

- **P-LS1.** After the boot list, `python scripts/harness.py` on a
  text prompt reads one line and stops with a structured verdict.
  Miss if it still exits after the list, or if it loops past a
  terminal stop.
- **P-LS2.** A sentence no registered path claims stops as a
  question or as exhausted with the missing capability named.
  Miss if fluent unregistered content is emitted as a fact.
- **P-LS3.** A typed path to a proposal that replaces a seed that
  owns a corpus prints `seed_ownership` from the write program and
  leaves the working tree byte-identical. Miss if the refuse text
  is a paraphrase the gate did not emit, or if any file changes.
- **P-LS4 (costume).** The loop does not read
  `experiments/harness_session.json`. A line that is not one of
  that recording’s legs still reaches the dispatcher or the write
  program. Miss if the only inputs that produce ask or refuse are
  the recorded chicken prompt and the two Lean-workbook legs.
- **P-LS5.** On a pause, no slot is bound to a value the person
  did not type. Miss if the shell supplies a default, a
  placeholder, or a generated fill.
- **P-LS6 (parked).** A later multi-turn loop that dispatches
  again for a second user line terminates by naming a cycle or at
  a visible hop ceiling. First slice is one line then stop;
  implementing that slice without parking this debt in writing is
  a miss of this close, not of P-LS1.

## 8. Adjudication — after the loop exists

§7 above is frozen as registered. Outcomes land here.

## 9. Next to the other frozen notes

The held-out self-grounding curve decides the environment. It
does not become the prompt. If the shape fails to recur, item 5
still stages.

The budgeted-edit note still parks a family-holdout ranker unless
a cell exists that passes the source’s tests and is not the same
remainder recurrence. Only Stein (binary gcd: same tests as
Euclid, different recurrence) is that cell. This slice does not
unpark that ranker and does not author a second foil.

The write-recovery note still waits on a training leftover that
is not write-recovery itself. This slice does not run that
ranker. It is how a person types the illegal write that
measurement will need. The conversation works with the residual
off.

## 10. How this was produced (disclosure, not a prediction)

1. Thesis: the leftover, driven live, is the person meeting the
   programs that already refuse and ask.
2. Grounding: v0.8 already claimed “driven”; the binary still
   exits after the boot list; loop detection inside one dispatch
   is shipped; across two typed lines it is not.
3. Close: one line, two existing programs, five live predictions,
   one parked multi-turn debt; v0.12 item 5 after the curve.

The registered sentences in §7 are the floors. The dialectic is
not a result.
