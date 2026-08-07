# Backlog

Actionable friction found while working, kept here so it isn't lost in chat
or commit history. Each item names the evidence that motivated it.

## Parser / matcher

- **No call juxtaposition.** `D(F)(POINT)` fails to parse (`parse_atom`
  returns after the first call). Forced the calculus corpus to reshape the
  chain rule via a `COMPOSE(...)` head. Support `expr(...)` application or
  document the `COMPOSE` convention as canonical.
- **Big-op prefix namespace hazard.** Identifiers starting `sum_ prod_ lim_
  max_ min_` silently become prefix big-operators; and `lim_h` (big-op) vs
  `LIM(...)` (plain call) produce different skeleton heads that can never
  twin. Normalize: lower-case the big-op head AND fold `LIM(` calls into the
  same head, or lint templates for the ambiguity.
- **Specialization matching (v2).** Current matcher only groups exact
  skeletons. Slot-to-subtree subsumption (`OUT = SCALE*IN + SHIFT` subsumes
  `Y = M*X + 0`-style instances) and identity-element reasoning (SHIFT=0)
  would connect e.g. circumference to the affine family.
  Further evidence from the economics corpus, all arity mismatches an
  identity-element rule would close: the equation of exchange
  `MONEY*VELOCITY = PRICE_LEVEL*OUTPUT` (2x2) misses the ideal gas law
  `PRESSURE*VOLUME = AMOUNT*CONSTANT*TEMPERATURE` (2x3) only because the gas
  law carries an explicit dimensional constant; Cobb-Douglas
  `OUTPUT = PRODUCTIVITY*CAPITAL^A*LABOR^B` misses the chemistry power-law
  rate law `RATE = RATECONST*CONCENTRATION^ORDER` only by one extra power
  factor; and simple interest `VALUE = PRINCIPAL*(1 + RATE*TIME)` is the
  first-order truncation of continuous compounding
  `VALUE = PRINCIPAL*EXP(RATE*TIME)` with no relation between them recorded.

## Schema

- **`symbolToken.syntactic_category` lacks `functional`/`operator`** (unlike
  `signatureSlot`), so operator symbols (`D`, `f`, `g`) must go in
  `functionals` while `symbols` still demands `minItems: 1` — FTC part 1
  needed a scalar symbol it didn't naturally have. Either add the enum
  members or relax `minItems`.
- **Cross-corpus entailment is blocked by reciprocity.** `entails` /
  `special_case_of` / `generalizes` require the reciprocal edge in the other
  corpus's file, so genuine cross-discipline entailments (physics average
  speed IS a special case of calculus average rate of change) go unrecorded;
  only `composed_with` (unchecked) is usable one-sided. Options: a repair
  tool that writes the reciprocal edge into the target corpus, or relax
  reciprocity to a warning for cross-corpus edges.

## Experiments

- **Buffered subprocess logging.** train.py prints don't flush through
  run_all.py's redirect until process exit; add flush/`-u` for live tailing.
