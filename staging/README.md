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
| `correspondence` | which declared form of the statement the theorem matched |
| `matcher_delta` | measured before/after twin counts, and the candidate's own declared prediction |
| `durable_store` | `data/` digest before and after; `byte_identical` must be true |
| `approval_granted` | always empty — this tool never accepts |

`record_id` is the SHA-256 prefix of the candidate's canonical payload, so the
same candidate always writes the same filename and a re-run overwrites rather
than accumulates.
