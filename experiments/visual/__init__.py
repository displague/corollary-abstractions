"""Visual ground truth before visual weights (ROADMAP-v0.7 item 8, steps 1-5).

This package is the oracle layer for the parse-first visual lane. It builds
the four artifacts whose absence forced the v0.6 deferral -- a deterministic
renderer, a source scene graph with stable slot identities, a controlled
invalid-pair generator, and an exact geometry verifier -- plus the normalized
SVG parser that step 6's parsed-vector arm will consume. No learned arm, no
parameter-matched raster control, and no weight of any kind lives here.

P-V1..P-V4 in ``docs/DESIGN-visual-structure.md`` remain REGISTERED and
UNADJUDICATED. They compare model arms; nothing in this package trains or
evaluates a model, so nothing here may be read as evidence for or against
them.

Exactness contract
------------------

Every coordinate is a ``fractions.Fraction`` and every verdict is decided by
integer/rational arithmetic. No floating-point value participates in any
check, any mutation, or any rendered coordinate. Floats appear only in
informational metadata (the angular deviation in degrees), which is labelled
as such and is never read back by the verifier.

The controlled right-angle break is therefore exact and length-preserving:
for a leg direction ``u = (p, q)`` the perpendicular leg direction is
``v = (-q, p)`` and the near-miss replaces it with ``w = (q, p)``. Both have
squared length ``p^2 + q^2``, so the mutation moves the angle by exactly
``2*atan(q/p)`` while leaving both leg lengths and all incidences intact.
That is what makes the right-angle check separably load-bearing rather than
co-detected by the length check.

Registered predictions (written before the first adjudication run)
------------------------------------------------------------------

Corpus under test: ``N = 240`` seeded valid right triangles (``--seed 11``),
each paired with one controlled invalid per class across 6 classes, i.e.
1,440 controlled invalids and 1,680 instances total. Three render styles
(``plain``, ``bold``, ``sparse``).

**P-VO1 -- acceptance.** With all six gated checks enabled, the verifier
accepts 240/240 valid source scene graphs (100%). A single rejection
falsifies the generator or the verifier and blocks step 6.

**P-VO2 -- rejection and localization.** The verifier rejects 240/240
instances in each of the six controlled-invalid classes (1,440/1,440), and
for every instance the set of failing checks is exactly the single check
registered as that class's gate. The predicted class-to-check matrix is
diagonal:

===========================  =====================
invalid class                registered gate
===========================  =====================
``right_angle_epsilon``      ``right_angle``
``leg_length``               ``leg_lengths``
``edge_disconnected``        ``incidence``
``hypotenuse_retargeted``    ``topology``
``degenerate_zero_leg``      ``nondegenerate``
``right_angle_mislabeled``   ``right_angle_slot``
===========================  =====================

A non-diagonal cell is a reportable miss: it means two checks co-detect a
class and the ablation below cannot prove both are load-bearing.

**P-VO3 -- no vacuous check.** For each of the six gated checks ``X``,
disabling ``X`` alone lets 240/240 of ``X``'s class pass while the other five
classes stay 100% rejected and all 240 valids stay accepted. If any check can
be disabled without a class escaping, that check is decoration and must be
removed rather than counted.

**P-VO4 -- round trip.** For all 1,680 instances and all 3 styles (5,040
round trips): ``parse_svg(render_svg(g, style))`` equals ``normalize(g)``
exactly, the verifier verdict and failing-check set are identical on the
source and the parsed graph, and ``render_svg(parse_svg(render_svg(g, s)), s)``
is byte-identical to ``render_svg(g, s)``. The last clause is the
anti-erasure control: if normalization dropped a load-bearing relation, the
re-render could not reproduce the bytes.

**P-VO5 -- stable slot identities.** Across the full parameter sweep the
role-to-id map is constant, every scene graph carries the identical id set,
and no id encodes a coordinate, a length, or a seed. Mutations preserve ids;
only ``right_angle_mislabeled`` rebinds an annotation, and it rebinds the
annotation's referents, never its id.

**P-VO6 -- declared redundancy.** The two derived checks (``pythagorean``,
``hypotenuse_claim``) never change a verdict on any of the 1,680 instances.
They are excluded from the gate deliberately, and this prediction is the
evidence that the exclusion was correct rather than convenient.

**P-VO7 -- the invalid set is not surface-detectable.** Three
capability-blind surface baselines (structural element count, SVG byte
length, maximum coordinate magnitude) are fit on the valid corpus and scored
on that same corpus, so their false-positive rate is zero by construction
and their balanced accuracy is maximally favourable. Prediction: none of
them reaches 1.000 balanced accuracy on any invalid class, and the
element-count baseline sits at chance (0.500) on all six because every
mutation preserves the element inventory. This is the vacuity control for
step 6: a class that a byte counter separates perfectly is too easy to
inform a parsed-vector-versus-raster comparison and must be hardened first.
"""

from __future__ import annotations
