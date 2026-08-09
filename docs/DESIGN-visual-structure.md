# Visual structure — a parse-first multimodal lane

Status: post-v0.5 design; first experiment queued in ROADMAP-v0.6 item 8.

## Why vision belongs here

The project asks one question across every modality: what has a closed form,
and therefore should not consume model capacity?

For language, raw characters were below the learnable floor at this scale;
parsed trees made composition possible. For mathematical vision, many useful
images already have a latent exact form: SVG paths, TikZ primitives, plot data,
diagram nodes and edges, geometric constraints, or a scene graph produced by a
deterministic renderer. Those sources are not merely captions. They state what
the picture is made from.

The first visual program should therefore not ask a 1.5M-parameter model to
discover objects from arbitrary pixels. It should ask the model to align two
structured descriptions — a formula and a figure — while exact geometry,
topology, rendering, and verification remain outside the weights.

This is a bounded starting claim. Pixels are not literally characters: images
have continuous variation, occlusion, viewpoint, texture, and ambiguous object
boundaries that text does not. “Parse first” is a hypothesis to test, not a
metaphor to substitute for the test.

## What larger multimodal systems teach us

SigLIP replaces global contrastive softmax normalization with pairwise sigmoid
loss and reports strong image-text representation learning with smaller batch
sizes ([SigLIP paper](https://arxiv.org/abs/2303.15343)). SigLIP 2 expands that
program with multilingual understanding, localization, dense features, and
self-supervised/captioning objectives
([SigLIP 2 paper](https://arxiv.org/abs/2502.14786)). Gemma 3 integrates vision
understanding into a family spanning 1B–27B parameters
([Gemma 3 technical report](https://arxiv.org/abs/2503.19786)); Gemma 4 explores
an encoder-free unified architecture that ingests raw image and audio patches
([Gemma 4 technical report](https://arxiv.org/abs/2607.02770)).

Those systems show that broad visual-language alignment can be bought through
large representation learners and large-scale image-text data. We are testing
a different operating point:

- domain first: diagrams, plots, geometry, and scientific figures;
- source structure before raster appearance;
- exact relations outside weights;
- weights only for graded correspondence under visual variation;
- every observation carries provenance and epistemic status;
- a parameter budget small enough that the entire system can remain under
  64 MB.

This is not a claim that web-scale representation learning is unnecessary for
general natural-image understanding. It is a claim that much scientific visual
reasoning should not be relearned from pixels when its originating structure is
available.

## Experiment V1: visual twins

### Task

Select corpus families that have natural visual realizations: right triangles,
circle measurements, affine transforms, graph connectivity, set relations,
coordinate frames, and simple plots. A deterministic renderer produces:

1. the source formula skeleton;
2. an SVG or scene graph with stable object identities;
3. one or more raster renderings with varied style;
4. the exact alignment from symbolic slots to visual objects;
5. negative pairs with one controlled structural violation.

Given a formula and diagram, the model must:

- decide whether they share the registered structure;
- point each symbolic slot to the corresponding visual element;
- point to the violated relation for a negative pair.

The answer is checked against the renderer's source graph and a symbolic
geometry/topology verifier. No learned decoder invents measurements or labels.

### Arms

| arm | input | purpose |
|---|---|---|
| source oracle | renderer scene graph | closed-form capability ceiling |
| parsed vector | normalized SVG/tree tokens | main tiny pointer model |
| raster control | pixels through a parameter-matched tiny encoder | tests whether source structure matters at this scale |
| shuffled-structure control | correct pixels, wrong scene graph | proves the verifier and structural channel are load-bearing |

The source oracle is not a competitor to the model; it identifies which parts
of the task never needed learning. The raster arm is not expected to be a good
general vision model. It is the capability-blind control for the parse-first
hypothesis at the project's parameter scale.

### Splits

- **content ID:** known families and rendering styles;
- **recombination:** held-out formula–style combinations;
- **style OOD:** new stroke widths, fonts, colors, layout, and label placement;
- **structural OOD:** deeper or larger scene graphs;
- **family OOD:** a held-out mathematical family with known primitives;
- **cross-domain:** the same skeleton rendered in a second discipline, such as
  an additive vector diagram versus rank decomposition.

Do not collapse these into one score. A model that survives color changes has
not thereby generalized to new topology.

### Metrics

- exact pair classification;
- exact slot-to-element alignment;
- exact violated-relation localization;
- performance by style, structure depth, and family;
- verifier catch rate on deliberately inconsistent pairs;
- parameter count, artifact size, and inference latency;
- change in result when the source graph or verifier is ablated.

## Registered predictions (before V1 adjudication)

**P-V1 — parsed structure at tiny scale.** At a matched parameter budget, the
parsed-vector arm beats the raster arm on family and structural OOD. If the
raster arm matches or wins, the strong parse-first claim is falsified for this
task.

**P-V2 — rendering robustness.** Style variation hurts raster input more than
normalized SVG structure, while both arms remain sensitive to genuine topology
changes. If normalization erases a load-bearing visual relation, that is a
parser defect, not model robustness.

**P-V3 — verification is load-bearing.** Injected inconsistent diagrams pass a
soft similarity score often enough to matter and are rejected by exact
geometry/topology checks. If the neural arm alone rejects all controls, the
verifier has not yet been shown necessary and the negative set must become
harder.

**P-V4 — third-modality twins.** At least one formula family already shared by
two disciplines forms a common formula/scene skeleton without adding a
vision-only alias. A miss is equally reportable: it identifies where visual
structure needs a distinct relation rather than an asserted equivalence.

## What stays symbolic, what weights own

Symbolic:

- SVG/TikZ parsing and canonicalization;
- incidence, containment, adjacency, ordering, congruence, and exact
  measurements available from source;
- chart values when the data series is present;
- coordinate transforms with declared frames of reference;
- provenance, receipts, epistemic status, and consistency checks;
- deterministic rendering and answer realization.

Learned:

- soft correspondence under layout/style variation;
- which visible element fills which symbolic role when multiple candidates fit;
- ranking ambiguous observations;
- later, object/relation proposals when only a raster or natural image exists.

The learned output is a proposal into symbolic state, not an assertion that
becomes true because the encoder emitted it.

## From diagrams to natural images

Natural images remove the source graph. A future adapter may use a compact
pretrained or task-trained visual encoder to propose objects, attributes, and
relations. Those proposals enter the same harness as retrieval results:

- source and model identity recorded;
- confidence retained as graded evidence, not converted to VERIFIED;
- exact checks applied where geometry or metadata permits;
- ambiguity triggers another view, a tool, ASK, or abstention;
- later corrections replace extrinsic observations without retraining the
  reasoning core.

Medical and other high-stakes imagery is not an early benchmark. It requires
specialized data governance, domain validation, uncertainty calibration, and
external expert ground truth. Synthetic diagrams cannot establish any of
those.

## Expected advantage if the bet holds

The useful outcome is not “a miniature Gemma.” It is a visual-scientific solver
whose compact learned part maps appearance into explicit roles, while the
relationship graph, geometry, proof obligations, and vocabulary remain
auditable and replaceable. New diagram families can arrive as renderers,
parsers, and corpus nodes rather than millions of weight updates. A corrected
figure-to-statement link is an edit with a trace, not a retraining campaign.

The failure is useful too. If parameter-matched pixels consistently beat parsed
vectors on true structural OOD, or if scene-graph normalization discards the
features needed for correspondence, the project must narrow or revise its
claim before expanding the modality.
