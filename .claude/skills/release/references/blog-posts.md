# Release blog posts

The notes are the record. The post is the argument a stranger can
finish.

## What the post is for

Every release since v0.5 has a post in `docs/blog/`. Title it for
the finding, not the version (`how-much-of-it-fits.md`,
`when-the-honest-baseline-wins.md`, `the-curve-changed-sign.md`).
Lead with the result that complicates the story, not the one that
flatters it. If the cycle produced a negative, that is the post.

## Voice

Write for a technically curious reader who has never opened this
repository. Prefer a situation they already understand (a library,
a story, a cookbook) over a project noun. When a project word is
unavoidable, define it in the same breath and then use the
definition.

The model is [the-world-outside-the-weights.md](../../../../docs/blog/the-world-outside-the-weights.md):
a scene, a wager, sections that earn their terms, tables of real
numbers, an honest boundary, a last paragraph that looks forward.

The anti-model is a first draft that only another agent walking
the internals can parse: route names, prediction codes, pin
tables, and “this post is the argument, not the inventory.”

Grounded, not sold. Do not claim a benchmark, a proof, or a
person-facing product the binary does not have. Do not bury a
sign flip under a flattering full-N gap.

## What must not appear

Do not bleed the writing brief into the post. No “as a newcomer,”
no “without jargon,” no instructions to a later agent, no
inventory dump of work that is not this finding. Those belong in
the release notes.

Design documents stay deep. The post may link them. It must not
read like one.

## The chain each post closes

A release blog sits in a loop, and the last section has to walk
it in public:

1. The previous post capped the previous release and named what
   this cycle owed.
2. This cycle implemented against that debt (and against a design
   written before the data existed, when one did).
3. Implementation produced a finding — often an accident nobody
   asked for.
4. That finding forced a *new* design, written before *this*
   post, so the post cannot choose the next question after the
   fact.
5. The last section of the post looks forward to the next
   release in the terms of that design: what will be measured,
   what would count as a miss, why one size is not enough if the
   finding said so.

If step 4 does not exist yet, stop and write the design. Do not
improvise the next question in the blog.

## Checklist before merge

- A stranger can retell the finding in one sentence after the
  opening.
- The previous chapter is linked and its unpaid debt is named.
- The next chapter’s question is the committed design, not a
  vibe.
- **That design is linked.** The post claims the question was
  written before the post; the link is the only way a reader
  can check that, and the v0.11 draft made the claim without
  it.
- Every number that names a winner and a loser has been read
  off the committed ledger, not recalled. The v0.11 draft had
  the matcher and the bag the wrong way round on the one pair
  where they disagree — `only_matcher_pairs` in
  `experiments/item4_operator_bag.json` settles it, and
  DISCOVERIES says it in English.
- Every table’s columns are English.
- The release notes still hold the inventory, the pins, and the
  commands.
