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

Implemented in v0.12 as `scripts/harness.py` `main()` plus `route_line`,
`read_one_line`, `render_verdict`. Checks live in
`tests/test_harness_line.py` (19 tests). Reproduce any row with a pipe:

```text
echo "why does this corpus exist" | python scripts/harness.py
echo "tests/fixtures/live_session_seed_replacement.json" | python scripts/harness.py
```

| | outcome |
|---|---|
| **P-LS1** | **FIRED** |
| **P-LS2** | **FIRED** |
| **P-LS3** | **FIRED** |
| **P-LS4** | **FIRED** |
| **P-LS5** | **FIRED** |
| **P-LS6** | still parked, in writing (below) |

**P-LS1 — one line, then a structured stop.** After the boot list the
process reads one line and prints `route`, `status`, `detail`. It exits 0.
A second piped line is *not* consumed: `test_only_one_line_is_consumed`
asserts the verdict block appears exactly once and that the second line
never appears in the output. Closed stdin is a `waiting` verdict, not a
traceback.

**P-LS2 — unregistered text asks or is exhausted.** Free text routes to
`tool.freeform_answer`, which the boot matrix does not register, and the
dispatcher stops `exhausted` naming the missing capability. This holds by
construction rather than by care: `DispatchResult` carries a `StopReason`
and **no `Verdict` at all**, so there is no value on that route that could
say "verified". The printed sentence is the dispatcher's own —

> routed to 'tool.freeform_answer', which the boot matrix did not
> register; abstaining rather than inventing a path (P-IH4: registered
> paths only)

— not a paraphrase written in `harness.py`; a test asserts the text comes
from the dispatcher.

**P-LS3 — `seed_ownership`, tree byte-identical.** A typed path to
`tests/fixtures/live_session_seed_replacement.json` prints:

```text
route   : write_gate
status  : REFUSED
detail  : candidate refused at seed_ownership
evidence: working_tree_byte_identical=True
```

`detail` is `record.refusal["check"]` verbatim. Byte-identity is checked
twice and independently: the gate's own before/after working-tree digest,
and a `git status --porcelain` comparison around the call.

*Getting there was narrower than §4 suggests, and this is worth writing
down.* `_candidate_lane` runs **before** the `seed_ownership` branch, so
the natural proposal shape — one whose `seed_source_path` points at the
real seed — refuses earlier at `declarative_seed` and never reaches
ownership. The proposal must instead carry the canonical envelope inline
in `seed_source` with no `seed_source_path`. The fixture is generated by
`write_stage._canonical_seed_source` itself so its AST matches exactly,
and a vacuity guard asserts the fixture still names a committed seed that
owns an existing corpus — otherwise the refusal could drift to an earlier
check and the test would stay green while testing nothing.

**P-LS4 — not a costume.** `harness.py` contains no reference to
`harness_session` (asserted against the source text). A sentence verified
absent from the recording still reaches the dispatcher. `python
scripts/session_run.py --check` still passes unchanged.

**P-LS5 — no slot is filled.** A pause returns `line: None`,
`route: none`, `status: waiting`, and the rendered output names no
capability and no default. This is a property of not writing the code that
would fill a slot, not of a check reporting that we did not.

**P-LS6 — parked, and the park is enforced.** The first slice reads one
line and stops. `test_only_one_line_is_consumed` is what stops that park
from being an omission: if a later change starts dispatching a second
line, that test fails and P-LS6's debt has to be paid deliberately.

### The second route: an exact question that ends `solved`

Added after the refuse/abstain loop existed, not instead of it. Before it,
every accepted line ended `REFUSED` or `exhausted` — honest, and a dead end
for the wager. The wager is that exact answers live outside the weights and
a person (or a small proposer) navigates them; **"which statements host this
part?" is exactly that kind of question**, and answering it is the first
thing the prompt does that is not a refusal.

```text
$ echo "owns x ^ 2" | python scripts/harness.py
route   : ownership
status  : solved
  6884 of 12777 statements host 'x ^ 2'
  skeleton  : ^(?0:V, 2)
      6870  lean_workbook.ground.v1
         7  geometry.foundations.v1
         ...
```

Why this is not a costume, stated as constraints the code meets:

- **`owns` is a command word, not comprehension.** `owns x ^ 2` routes;
  `who owns x^2?` does **not** — it abstains through the dispatcher exactly
  as before. A test asserts that asymmetry. Pretending to read English is
  the failure mode; a registered command is not that.
- **No new parser.** The expression goes through `match_signatures.tokenize`
  / `Parser` / `canonicalize` — the same front end that reads every
  committed template — and is matched by the matcher's own `skeleton`.
- **Registered, by the real boot matrix.** The lookup reads the committed
  corpus graph, so it is a capability of the already-registered
  `corpus.nodes` subsystem. If that subsystem does not register, the route
  refuses rather than answering from somewhere else.
- **`solved` means the lookup returned, not that anything is true.** It is
  exact and total — every hosting statement, unranked. No model, no scoring,
  no ranker.
- **Refusals stay refusals.** A bare variable is refused (every statement
  hosts `x`; answering 12,777 is not an answer), an unparseable query is
  refused, and a part nothing hosts is `exhausted` rather than dressed up.

Cross-checked against an independent oracle: the lookup reports **6,870**
Lean-workbook hosts for `x ^ 2`, the same number
[DESIGN-heldout-recovery.md](DESIGN-heldout-recovery.md) §1 records for the
most common subterm from a completely different code path. A test pins it,
so if the two ever drift, one of them is wrong and the suite says so.

### Not in this slice, as §5 required

No HTTP skin, no ranker, no fifth algorithm file, no English that authors
a node, no multi-turn memory, no promotion of a passing test to a proof.
`write_stage.py` and `dispatcher.py` were **not modified** — both routes
are called through public adapters that already existed.

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

## 11. v0.13 addendum — P-LS6 adjudication

The one-line scope above is the frozen v0.12 record.  v0.13 deliberately
unparks P-LS6 for resolver clarification only.  An ASK persists its exact
candidate identifiers across input turns.  A continuation must be explicit:
`narrow corpus VALUE`, `narrow discipline VALUE`, `narrow word VALUE`, or
`narrow id VALUE`.  `cancel` discards it.  Registered commands and new
questions continue through their normal routes; a new ASK replaces the old
one rather than silently becoming its clarification.

Narrowing is hard intersection, never relative scoring: every retained
candidate satisfies the complete declared predicate.  Zero matches preserve
the ASK and report the contradiction, more than one remains an ASK, and a
singleton is returned only with a title or statement meaning quoted from the
committed corpus.  Repeating a no-progress clarification names `cycle`; four
clarification hops name `hop_ceiling`; the real process exits on either status.
Focused process and routing tests exercise continuation, cancellation,
command escape, ASK replacement, session isolation, cycles, and the ceiling.
On that bounded contract P-LS6 **FIRED**.  This is not general conversational
memory, story continuation, or a claim that arbitrary prose supplies context.
