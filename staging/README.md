# staging/ — WRITE proposals, never durable knowledge

`scripts/write_stage.py` writes one JSON receipt here for every WRITE candidate
it judges, accepted or refused. Nothing in this directory is corpus content and
nothing here is read by any other tool.

## Why the directory is committed and the records are not

The directory, this README, and `.gitignore` are tracked; `*.json` records are
ignored. That split is the point of the item this directory belongs to
(`docs/ROADMAP-v0.7.md` item 3):

- **Records must not be committed by default.** A staging record is runtime
  output. Runtime output that lands in git automatically is exactly how policy
  output quietly becomes trusted knowledge — the failure the PROVEN gate exists
  to prevent. A machine may not promote its own proposal, and "it is in the
  repository" is a form of promotion.
- **The path must still be declared.** A receipt a reviewer cannot be pointed at
  is not a receipt. An ambient temp directory would make refusals unauditable
  and would vary by machine, so the location is a committed part of the
  repository even though its contents are not.

Attaching a specific receipt to a review is therefore a deliberate `git add -f`
by a human, which is the same shape as every other promotion in this project:
the tool produces evidence, a person decides.

## Reading a receipt

Receipts are deterministic — sorted keys, no wall-clock timestamps, scratch
paths scrubbed — so two runs of the same candidate produce byte-identical files
and a receipt diff shows a real change. Key fields:

| field | meaning |
|---|---|
| `outcome` | `STAGED_CANDIDATE`, `STAGED_REVIEW_REQUEST`, or `REFUSED` |
| `checks` | every gate in pipeline order with `PASS`/`REFUSED` and its reason |
| `refusal` | the single gate that said no, for a refused candidate |
| `correspondence` | which declared form of the statement the theorem matched, and every form considered |
| `matcher_delta` | `before`/`after` counts, the measured `delta`, and the candidate's own `declared` prediction beside it |
| `working_tree_integrity` | digest of the whole working tree before and after, with what it `covers` and `excludes`; `byte_identical` must be true |
| `approval_granted` | always empty — this tool never accepts |

`record_id` is the full SHA-256 of the candidate's canonical payload —
including a digest of the `rationale`, so two candidates with the same proof and
different justifications get two receipts instead of overwriting one. The same
candidate always writes the same filename and a re-run overwrites rather than
accumulates.

### What a `STAGED_CANDIDATE` is not

A staged receipt says a proposal survived sixteen checks. It does **not** say
the statement is true, and it does not say this statement rather than a
structural twin is what the theorem proves. `semantic_correspondence` compares
SKELETONS: the theorem's opening goal, translated into the corpus template
grammar, is one of the forms the statement declares. That is a floor above byte
integrity, not semantic ownership — which is exactly why `structural_unambiguity`
exists, why `correspondence.ambiguous_with` is recorded, and why nothing in this
directory is ever accepted by the tool that wrote it.

## Shape of a proposal

`python scripts/write_stage.py <proposal.json>` reads this. Every path is
repository-relative with forward slashes, and none of them may be under
`data/`.

**This is a SHAPE TEMPLATE, not a runnable example.** The values below are
placeholders: `BooleanLaws.domination_and_false` is not in
`prover/sample_triples.json` and `scripts/seed_logic_candidate.py` does not
exist — a candidate names a seed script it proposes the CONTENT of, and
`seed_source_path` must resolve to an existing `scripts/seed_<name>.py`. For a
worked end-to-end candidate that really stages, read
`tests/test_write_stage.py`, whose fixture stages the domination law
`P and false = false` against a real closing transition.

```json
{
  "statement_id": "<corpus>.<topic>.<name>",
  "corpus": "<corpus directory under data/>",
  "seed_script": "scripts/seed_<corpus>.py",
  "seed_source_path": "scripts/seed_<corpus>_candidate.py",
  "rung": "PROVEN",
  "rationale": "why this belongs in the durable corpus",
  "artifact": "prover/<artifact>.json",
  "artifact_sha256": "<sha256 of the artifact bytes>",
  "reference": "<Namespace.theorem_name>",
  "transition_trace": [
    {"theorem": "...", "tactic": "...", "stateBefore": "...", "stateAfter": "..."}
  ],
  "expected_matcher_delta": {
    "nodes_analyzed": 1,
    "shape_groups": 0,
    "typed_groups": 0,
    "family_groups": 0,
    "aliased_groups": 0,
    "mirror_groups": 0,
    "ladder_violations": 0,
    "parse_problems": 0,
    "slot_schema_gaps": 0,
    "new_typed_twin_partners": []
  },
  "frame_local": false
}
```

`expected_matcher_delta` must declare EVERY counter the matcher summary emits —
all nine, plus `new_typed_twin_partners` — and no others. An omitted key is
refused: a counter left ungated is a prediction nobody registered.

`seed_source` may be given inline instead of `seed_source_path`; it is the FULL
text the seed script should have after the edit. It must be the canonical
`CORPUS = json.loads(<literal>)` envelope emitted by the gate's own formatter.
The source is parsed as data and never executed; any extra statement is refused.
The proof artifact must independently appear with the same digest in
`prover/proof-artifact-manifest.json`; a candidate pin alone is not authority.
This v0.7 lane accepts only a seed path not tracked by git (an untracked proposed
file at that same path is allowed) and a corpus directory that does not already
exist. Existing seeds may own multiple corpora, so replacing one with this
single-corpus envelope could orphan an output even if the named corpus validates.
Existing-corpus write-back waits for a trusted seed-aware patch format.

`expected_matcher_delta` is mandatory for a PROVEN candidate and is a
REGISTERED PREDICTION in the house sense: it is compared against the delta
measured in the scratch checkout, and a candidate that mispredicts its own
effect on the twin matcher is refused even though schema, link and
regeneration checks passed. A candidate that cannot say what it will do to the
corpus's structural output does not get to change it. The declaration is copied
into the receipt beside the measurement (`matcher_delta.declared` next to
`matcher_delta.delta`), so predicted-versus-measured is auditable from the
receipt alone.

`rung` is what the candidate CLAIMS. `VERIFIED` stages a review request and
ignores everything below `rationale`; `CONJECTURED` and `frame_local: true` are
refused outright.

## Acceptance: applying a candidate (v0.8)

Staging never accepts — `approval_granted` is always empty — because a machine
may not put its own proposal in the corpus. `--apply` is the SEPARATE, explicit
act that applies a candidate that already cleared every gate:

```
python scripts/write_stage.py <proposal.json> --apply
```

It is deliberate and is NOT reachable from the controller loop (the controller
only advances a receipt ledger; letting it apply would be the machine promoting
itself). Acceptance:

1. runs the FULL staging audit first and applies **nothing** unless the outcome
   is `STAGED_CANDIDATE`. A refused candidate returns its ordinary refusal
   receipt and the working tree is byte-identical — acceptance cannot apply what
   the gate would refuse, including a seed that would orphan a co-owned corpus
   (refused at `seed_ownership`);
2. writes the audited **seed** as the durable source of truth, then regenerates
   `data/<corpus>/nodes.json` through the one trusted generator — byte-for-byte
   what running the committed seed produces. Both writes are atomic (temp file,
   fsync, `os.replace`), so a crash mid-write never leaves a torn corpus.
   Candidate Python is never executed; the candidate never hands over
   `nodes.json` bytes;
3. re-verifies in the real tree: exactly the declared node is present and nothing
   else, every other corpus is byte-identical, schema and links validate, the
   declared matcher delta matches the delta now measured against the applied
   data, and the whole-tree delta is exactly the two files it declared it would
   write (nothing in `scripts/`, `prover/`, `schema/`, another corpus, or the
   root). Any failure — including an inability to write the receipt — rolls the
   tree back to byte-identical and refuses: an applied change without a diffable
   receipt is not allowed.

An acceptance writes a second receipt, `<record_id>.accepted.json`, recording
the exact transition — seed path, corpus, node id, and corpus/working-tree
digests before and after — so the change is reproducible: the same seed source,
materialized by the same generator, yields the recorded after-digest. Unlike a
staging receipt the working tree is deliberately NOT byte-identical across an
acceptance; applying the change is the point, and a human still decides whether
to `git add` the resulting seed and corpus.

**What acceptance is not.** It means a receipt exists AND the audited seed was
written and its corpus regenerated so the declared delta was applied. It does
**not** certify the statement is true; correspondence certifies STRUCTURE only,
and exclusive ownership, not skeleton identity, is what breaks a twin tie.
