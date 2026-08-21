> **REVISED 2026-08-21, by maintainer redirect.** This file's first
> draft (committed hours earlier, preserved in git history) made
> ledger-first claims the headline. The maintainer named the drift that
> draft continued: three consecutive cycles of instruments about the
> project's own evidence while the conversational surface carried since
> v0.8 sat parked five cycles. The redirect is recorded in
> [DESIGN-grounded-throughput](DESIGN-grounded-throughput.md) §2;
> ledger-first claims parks whole in §3 below with its design and
> course receipt intact. The escalation this file's first draft wrote —
> "the v0.18 rotation owes either a schedule or a retirement" for the
> HTTP skin — is answered early: scheduled, here, as the headline.

# Roadmap v0.17 — the graph answers at wire speed, or the thesis was smaller than claimed

Sixteen releases have defended the exact-code-outside-weights thesis
with instruments. This cycle demonstrates its consequence for a
consumer: a microkernel — small programs plus, optionally, small
models — grounded by extrinsic data, algorithmic comprehension, and
logic, delivers useful receipt-bearing answer tokens **many-fold
faster** than a language model generating the same content from
weights, through an API surface any agent harness can attach to.

Governing design: [grounded tokens arrive at wire
speed](DESIGN-grounded-throughput.md), standing on
[DESIGN-interactive-harness](DESIGN-interactive-harness.md) (Phases 0–2
shipped and adjudicated across two release gates; Phase 4 unblocked in
fact since durable session restore shipped, unscheduled by choice until
now).

## 1. Grounded throughput (headline, architecture and product)

Implement DESIGN-grounded-throughput in its registered order: the
skin's protocol subset and trace-to-API mapping spec (including the
capability sheet that teaches an attaching orchestrator the registered
line grammar); the task book (N ≥ 100 typed conversations in that
grammar, halves by hash, half B sealed) authored from committed
artifacts before the skin answers anything; the pinned baseline
manifest — two arms, grounded and ungrounded — before K freezes;
`scripts/serve_chat.py` over the existing session engine, with one
named wiring step (closure reachability as a registered route; dropped
from the book with the reason if unwired at sealing);
`scripts/measure_throughput.py` speaking only the public API; one
registered run.

The gate is T1–T7 as frozen in the design: an unmodified
OpenAI-compatible client completes answer, WAITING round-trip, and
refusal (adjudicating the substrate's P-IH6); honesty crosses the wire
(no token that is not a rendering of accepted content); the task book
precedes the answers; K = 5× median perceived throughput over sealed
half B at correctness ≥ the baseline's, with the
correct-answers-only denominator; usefulness gates throughput (≥ 90%
answerable correct with receipts, 100% of refusals refused, before any
speed number is read); the small-model lane degrades honestly; receipts
revalidate from the client side. Three blind controls, each with a
voiding sentence — the dump server, the shuffled kernel, and the pinned
baseline itself, which is allowed to win and thereby falsify the
thesis at this scale.

## 2. Session-native small models (instrument lane, bounded)

The substrate's Phase 3, sliced: register at least one existing
specialist checkpoint (span pointer, analogy pointer, or tactic ranker)
as a session subsystem behind the tool admission bar
(DESIGN-interactive-harness §8: closed outputs, capability-blind
baseline on the same path, OFF-not-crash, session-scoped pruning), so
the boot matrix can show a small model registering, serving through the
same API, and losing honestly to its blind baseline if that is what the
measurement says. If no checkpoint clears the bar in-cycle, the lane
ships "symbolic-only" in writing per T6 — an honest readout, not a
failure of item 1.

## 3. Carried, with dependants named

| lane | named dependant | disposition |
|---|---|---|
| Chat-completions HTTP skin | **item 1** — the headline | five-cycle park RESOLVED by scheduling; park history preserved in BACKLOG |
| Ledger-first claims (v0.17 course lead, gate L1–L13, hardened) | *none this cycle* | **parked whole by the redirect**, design and receipt intact and preregistration-ready; unparks as a headline candidate the first cycle after the throughput readout — or mid-cycle only through the suspension's own lift trigger (§4), of which a release again quoting a number its artifact no longer supports is the canonical case |
| Sans-template open-prose rendering (substrate Phase 6) | *none — explicitly not smuggled into item 1* | parked; becomes the next surface candidate if T4 fires (design §10) |
| Unless-receipts, detached receipt, residual ledger, antibody, two referees, wild text, negative space, and the remaining course parks | *none* | parked with dispositions recorded in DESIGN-ledger-first-claims §2 and both course receipts |
| Load-bearing / premise-necessity | *named by ledger-first's residual* | parked, travels with it |
| Conservativity compiler, two witnesses, and older course parks | *none* | unchanged |
| Resolver coverage lane, A3–A5, verified-ambiguity, range certification, W1–W3 and the long tail | *none* | parked in BACKLOG, unchanged from the v0.15 drift audit |

## 4. Governance

Unchanged from v0.16, plus two entries this redirect earned:

- **Headline selection is part of the evidence trail.** A maintainer
  redirect is a first-class, recorded decision (design §2), exactly as
  a course selection is — what is forbidden is the drift that needs no
  decision because nobody wrote one down.
- **Instrument-first headlines are suspended for this cycle**
  (design §9): the shipped instruments keep running; no new
  meta-evidence instrument may headline. The suspension lifts when a
  product-lane failure names a missing instrument.

## Release gate

v0.17 is ready only if:

- grounded throughput ships its registered run with T1–T7 adjudicated,
  or stops on a named stop condition with the reading published — a
  baseline win or a control void is a publishable result, not a
  failure to ship;
- the small-model lane reads out (registered subsystem with its blind
  baseline, or "symbolic-only" in writing);
- `check_report_regeneration.py` runs in the release refresh with its
  verdicts in the notes;
- the full suite is green on a frozen tip with retained receipts;
- every unfinished item ships or parks in writing;
- the outside design inquiry gate is discharged for v0.18 — run, or
  explicitly reaffirmed with the receipt named, and the v0.18 course
  brief must carry the throughput readout, whichever way it lands.
