# Design — a trusted append format for an existing corpus (unblocks ROADMAP-v0.10 item 4)

Committed BEFORE implementation. The registered predictions in §7 are floors
written down before any adjudication run. §7 also discloses what was already
known from reading the gate and the item-5 session, because a prediction
registered after its experiment is not a prediction.

This is Slice A of the item-4 handoff. Slice B (author the covered
Lean-workbook subset onto the enlarged graph) is a separate design, and
does not start until this one has landed.

## 1. Why this exists

Item 5 drove a real session that wanted to add one node to
`data/number_theory`. The WRITE gate refused, at `seed_ownership`:

> the declarative WRITE lane stages new seed/new corpus pairs only;
> replacing an existing seed could orphan another corpus it owns, and
> appending to an existing corpus needs a trusted patch format

That refusal is right. `scripts/seed_logic.py` owns two corpora; replacing
it could orphan one. Hand-authored seeds are trusted Python the gate must
not overwrite with a proposer's envelope. The session took the lane that
existed — a whole new corpus, `data/ingested_arithmetic/`, for a single
statement — and recorded the deviation
(`docs/DESIGN-v010-harness-session.md` §7).

Item 4 wants to author thousands of ingested nodes through PROVEN-WRITE.
On today's lane that is either thousands of one-node corpora or nothing.
The trusted patch format is therefore the first deliverable, not a
courtesy to item 5.

## 2. What the format IS (and is not)

An append is a **JSON document**, parsed as data, never executed. It is
the sibling of `_canonical_seed_source`, not a second Python envelope.

```json
{
  "kind": "append_nodes",
  "schema_version": 1,
  "seed_script": "scripts/seed_ingested_arithmetic.py",
  "corpus": "ingested_arithmetic",
  "statement_nodes": [ { "...one or more full statement nodes..." } ]
}
```

`WriteCandidate.seed_source` carries exactly that text. Two accepted
shapes, still one discipline:

| `seed_source` parses as | lane |
|---|---|
| the canonical `CORPUS = json.loads(<literal>)` AST | **new_corpus** (unchanged) |
| JSON with `kind: "append_nodes"` | **append** (this slice) |
| anything else | `declarative_seed` refusal |

No third shape. An append that contains `import`, a callback, or any
Python is not an append — it fails to parse as the JSON document and is
refused. That is the item-5 lesson: "an append format that admits
arbitrary Python has handed an untrusted proposer an execution channel."

## 3. What the gate still guarantees

Unchanged, and the reason to write a format rather than relax
`seed_ownership`:

1. **The node judged is the one scratch regeneration emits**, never the
   candidate's claim. Scratch runs the *existing committed seed* (trusted
   Python already in the tree), then merges the append as data, then
   reads `nodes.json`. The candidate never supplies a pre-baked corpus
   that the gate would rubber-stamp.
2. **Other corpora stay byte-identical.** The merger writes only
   `data/<corpus>/nodes.json` (and, on accept, the append file).
3. **The matcher delta is still declared before it is measured.** An
   undeclared delta is still an unregistered prediction. A bulk append
   declares one delta for the whole batch (`nodes_analyzed` equals the
   number of new nodes, plus the existing `group_counts` keys).
4. **The working tree is byte-identical on refusal.** Same
   `working_tree_digest` cover as today.

New, specific to append:

5. **The existing seed is not rewritten.** Replacing `seed_logic.py`
   with a literal envelope is still refused. Acceptance writes
   `data/<corpus>/appends/<primary_id>.json` and regenerates
   `data/<corpus>/nodes.json` via the same merger the scratch used.
6. **An append that would replace an existing node is a different
   operation, and is refused.** If any `statement_id` in the patch is
   already present in the seed's own output (or in a previously accepted
   append), the check is `append_collision`, not `seed_ownership`.
   Replace/revise is a separate rung and is not this slice.
7. **Confinement for N nodes.** Today's `_regenerate` requires
   `added == [candidate.statement_id]`. Append requires
   `set(added) == set(ids in the patch)` and
   `candidate.statement_id in that set`. The receipt still names one
   primary id; the patch is the declared batch.

## 4. How regeneration stays coherent

`check_regeneration.py` today runs every `seed_*.py` and diffs `data/`.
If acceptance writes nodes the seed does not emit, the next regeneration
clobbers them. So the merger is shared, not a WRITE-only side effect.

After every seed runs, trusted code applies `data/<corpus>/appends/*.json`
(sorted by filename) onto that corpus's `nodes.json`. The same function
is what scratch and `accept_write` call. Seeds stay the source of truth
for the nodes they already emit; appends are the source of truth for the
nodes they add. Neither is Python from the proposer.

An `appends/` directory is not a corpus and is not an orphan. The orphan
scan already requires `data/<name>/` to be a directory; it must ignore
`appends` as a corpus name (it will not appear as one) and must not
treat a corpus that has appends as unowned.

## 5. seed_ownership, rewritten as two rules

| situation | check | outcome |
|---|---|---|
| new seed + new corpus, literal envelope | `seed_ownership` | pass (today) |
| existing seed, literal envelope that would replace it | `seed_ownership` | refuse (today) |
| existing seed + existing corpus, append document | `seed_ownership` | pass, if the named seed already owns that corpus |
| append document naming a seed that does not own the corpus | `seed_ownership` | refuse |
| append whose ids collide with seed output or prior appends | `append_collision` | refuse |
| append document against a corpus that does not yet exist | `seed_ownership` | refuse (that is new_corpus's job) |

"Owns" means: the committed seed is the one `check_regeneration` already
treats as producing `data/<corpus>/nodes.json`. For the hand-authored
seeds this is the existing filename convention (`seed_number_theory.py`
→ `number_theory`). For the item-5 literal seed it is
`seed_ingested_arithmetic.py` → `ingested_arithmetic`. A multi-output
seed (`seed_logic.py` owns `logic` and `set_theory`) may receive an
append on either corpus it owns; the seed file is not touched, so the
other corpus cannot be orphaned.

## 6. What this slice will demonstrate, and what it will not

Demonstrate, in tests, against the live gate:

- an append of one node to `ingested_arithmetic` stages and, on
  `accept_write`, lands the node; the existing seed bytes are unchanged;
  `check_regeneration` is green;
- the same append with a colliding `statement_id` is refused at
  `append_collision`; tree byte-identical;
- a literal-envelope candidate aimed at `scripts/seed_logic.py` is
  still refused at `seed_ownership` (the item-5 tests stay);
- an append whose `seed_source` is Python is refused at
  `declarative_seed`;
- a bulk append of two new ids is confined to exactly those two;
- a refused append leaves the working tree byte-identical.

Not this slice: replacing a node, rewriting a hand-authored seed,
authoring the Lean-workbook covered set (Slice B), or silently
re-pinning the absorption rate-gap.

## 7. Registered predictions (floors)

Disclosure: before this note was written, the item-5 design §7–§8 and
`write_stage._gate` / `_canonical_seed_source` / `_regenerate` were
read. No append path was executed; no seed was modified; no
`accept_write` of an append was attempted. P1 is therefore a
*confirmation being pinned* of a refusal the session already recorded.
The rest are blind.

- **P1** (probed as item 5's refusal): a literal-envelope candidate
  whose `seed_script` is an existing tracked seed is still refused at
  `seed_ownership`, with the orphan/patch-format detail. The new lane
  does not weaken this.

- **P2** (blind): an append document adding one fresh id to
  `ingested_arithmetic` stages `STAGED_CANDIDATE` and `accept_write`
  applies it. After accept: that id is in
  `data/ingested_arithmetic/nodes.json`;
  `scripts/seed_ingested_arithmetic.py` is byte-identical to before;
  `data/ingested_arithmetic/appends/<id>.json` exists; every other
  corpus is byte-identical; `check_regeneration` exits 0.

- **P3** (blind): the same document with the id already in that corpus
  (the session's `numbertheory.ingested.lean_workbook_22080`) is refused
  at `append_collision`. Working-tree digest unchanged.

- **P4** (blind): `seed_source` that is valid Python but not the
  canonical envelope and not the append JSON (the `sys.executable`
  walk) is still refused at `declarative_seed`. An append JSON that
  includes a `python` key or a non-list `statement_nodes` is refused
  at `declarative_seed`.

- **P5** (blind): a two-node append whose declared primary is one of
  the two ids, and whose `expected_matcher_delta.nodes_analyzed` is 2,
  is confined to exactly those two ids. A two-node append that
  declares `nodes_analyzed: 1` is refused at `matcher_delta_prediction`
  or `regeneration_confinement` — the declared batch and the emitted
  batch must agree.

- **P6** (blind): an undeclared matcher delta is still refused, on the
  append lane, with the same "unregistered prediction" detail the
  session hit.

- **P7** (blind): no existing `test_write_stage` assertion of
  `seed_ownership` on a *replacement* candidate flips. The new tests
  are additions.

Adjudication lands in §8 after implementation, exact to the row.
Disclosures append; the registered text is not edited.

## 8. Adjudication — after implementation

§7 above is frozen as registered.

| # | outcome | where it is checked |
|---|---|---|
| P1 | **CONFIRMED** — literal envelope against `seed_logic.py` still refused at `seed_ownership` with the orphan detail | `test_literal_envelope_against_existing_seed_still_refused`; `RegenerationConfinementTests` |
| P2 | **CONFIRMED** — one-node append to the just-created `writestage_demo` corpus stages and accepts; seed bytes unchanged; append file written; both ids present | `test_append_one_node_accepts_without_rewriting_the_seed` |
| P3 | **CONFIRMED** — colliding id refused at `append_collision`; tree digest unchanged | `test_colliding_id_is_refused_and_tree_is_identical` |
| P4 | **CONFIRMED** — a `sys.executable` walk is still `declarative_seed` | `test_python_is_not_an_append` |
| P5 | **CONFIRMED** — two-id append with `nodes_analyzed: 1` is refused | `test_two_node_append_is_confined_to_those_ids` |
| P6 | **CONFIRMED** — undeclared delta refused on the append lane, same detail | `test_undeclared_delta_is_still_refused_on_the_append_lane` |
| P7 | **CONFIRMED** — existing replacement-ownership tests still pass | `RegenerationConfinementTests` (13 tests) |

**Disclosure 1 — the first append fixture dualized onto the node it
was appending to.** A JOIN-domination law is the lattice dual of the
MEET-domination fixture the new-corpus lane uses; `structural_unambiguity`
correctly refused it. The append fixture is a ground `1 + 1 = 2`, which
cannot dualize. The registered tests stand; the fixture was wrong, not
the gate.

**Disclosure 2 — MiniRepos have no `.git`.** The append lane's
"committed seed" check cannot call `git ls-files` in the test fixture.
Existence of the seed file is required always; the tracked check runs
only when `repo_root/.git` exists. The real tree still refuses an
untracked seed.
