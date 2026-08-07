#!/usr/bin/env python3
"""Seed data/machine_learning/nodes.json.

Fourteen equations from modern ML/LLM training and architecture, chosen so
that their relationship to the *existing* corpus is decided mechanically
rather than asserted. Machine learning is the discipline most likely to be
accused of borrowing its mathematics from elsewhere, so this corpus is
written as a test of that accusation: four predictions were registered before
`scripts/match_signatures.py` was run, and the report records the verdict on
each, hits and misses alike.

Predictions registered before running the matcher
-------------------------------------------------

1. GRPO's group-relative advantage IS z-standardization, and must land on
   `probstat.transform.z_standardization`'s typed skeleton.        FIRED
2. The linear state-space update is the noisy-affine / AR-style statistics
   node with the noise slot filled by an autoregressive term.      MISSED as
   a twin; recovered as a specialization edge (see below).
3. The softmax/Boltzmann policy family-twins chemistry's Arrhenius factor
   by sign absorption.                                             MISSED
   against Arrhenius as a twin (chemistry keeps R*T explicit, arity four,
   where ML folds it into one beta, arity three); FIRED against Arrhenius's
   sibling the first-order integrated rate law and the whole exponential
   family, and recovered against Arrhenius itself as a specialization edge.
4. The gradient-descent step joins the affine family.              MISSED,
   by exactly one slot category (see `gradient_descent_step` below).

Two of the three misses were recovered one level down, by
scripts/specialize.py rather than by the twin matcher, which is worth
recording as a pattern: the twin matcher answers "is this the same
statement", the specialization matcher answers "is this a case of that", and
a prediction phrased as the first can be right as the second.

What actually fires
-------------------

- `grpo_group_relative_advantage` and `probstat.transform.z_standardization`
  share `?0:V = *(+(?1:V, neg(?2:P)), inv(?3:P))` character for character.
  GRPO's advantage is a z-score of the reward within a sampled group; the
  matcher confirms it without being told.
- `token_cross_entropy_loss` and `infotheory.divergence.cross_entropy` share
  `?0:V = neg(*(?1:P, sum⟨*(?2:V, LOG⟨?3:V⟩)⟩))`. This one is *authored to
  match* (docs/BACKLOG.md's `authored_to_match` vs `emergent` distinction):
  the 1/N batch average is written explicitly so it occupies the same
  unit-scale slot that carries 1/ln 2 in information theory. That is a
  translation, not a disguise -- the two nodes are the same functional -- and
  the corpus records reciprocal `equivalent_to` edges in both files.
- `policy_probability_ratio` joins the rate/density family
  `?0:V = *(?1:V, inv(?2:V))` alongside average rate of change, average
  speed, mass density, molarity and price elasticity. The importance-sampling
  ratio of PPO is a density in the same sense those are.
- `boltzmann_softmax_policy` typed-twins
  `chemistry.kinetics.first_order_integrated_rate_law` and
  `economics.finance.present_value_continuous`, and family-twins exponential
  growth and continuous compounding on top of those.
- `gradient_descent_step` and `kl_regularized_rl_objective` typed-twin each
  other, and both shape-twin `chemistry.thermodynamics.gibbs_free_energy` and
  `chemistry.thermodynamics.helmholtz_free_energy`. That is not a pun: the
  KL-regularized objective *is* a free energy, and its maximizer is the
  Boltzmann distribution this corpus also carries.

What does not fire, and why -- recorded because the misses are the findings
--------------------------------------------------------------------------

- `elman_rnn_hidden_state` and `lstm_gate_activation` have skeletons that are
  character-for-character identical apart from one head string (`ACTIVATION`
  vs `SIGMOID`) and they do not twin at any level. Call heads are literal at
  every match level (docs/BACKLOG.md), so this is the same obstacle
  `data/morphology` hit, now with both halves inside one corpus.
- Even unwrapped, the recurrent pre-activation
  `+(?BIAS:P, *(?P,?V), *(?P,?V))` is *multiple* linear regression, and the
  statistics corpus carries only the simple (one-regressor) form. So the
  nonlinearity is not the only blocker; the arity is a second, independent
  one.
- `mlstm_matrix_memory_update` does NOT twin `linear_ssm_state_update`, even
  though both are "state = coefficient*state + coefficient*drive". Two
  blockers: xLSTM's coefficients are *gates* (data-dependent, variable-like)
  where the SSM's are learned matrices held fixed at inference
  (parameter-like); and the rank-1 covariance update needs an `OUTER(.,.)`
  call that the SSM's scalar-diagonal form does not.
- `belief_state_update` (`?0:V = UPDATE⟨?1:V, ?2:V⟩`) is the fifth head in
  the corpus carrying the two-argument opaque-composition shape
  `?0 = HEAD⟨?1, ?2⟩`, after morphology's `CONCAT` and `REALIZE`,
  information theory's `CAPMAX` and geospatial topology's `MEET`. Five nodes,
  five heads, and no two of them twin.
- Five of the fourteen nodes are isolated at every level -- no twin, no
  specialization edge in either direction: `elman_rnn_hidden_state`,
  `lstm_gate_activation`, `belief_state_update`, `ppo_clipped_surrogate` and
  `dpo_preference_loss`. Their blockers are, in order: a call head wrapping
  an affine map; the same, plus a second head that differs only in name from
  the first; an opaque head with no relatives; two opaque heads standing in
  for a minimum and a clamp the grammar cannot write; and a plain slot
  binding that `specialize.py` suppresses by design. Only the last is a tool
  bug rather than a grammar limit, and docs/BACKLOG.md already carries it.

Authoring constraints observed (all from docs/BACKLOG.md)
---------------------------------------------------------

- `statement_id` may not contain `_` in its first segment, so ids are `ml.*`
  while the directory and the `discipline` field are `machine_learning` --
  the same split `settheory.`/`set_theory` and `infotheory.`/
  `information_theory` already carry.
- `constantToken` has no `name` key.
- `symbol_lexicon.symbols` needs at least one scalar entry and cannot hold
  functionals, so ACTIVATION / SIGMOID / EXP / LOG / OUTER / UPDATE / MINOF /
  CLIPCALL live in `functionals`.
- Identifiers beginning `sum_ prod_ lim_ max_ min_` are silently parsed as
  prefix big-operators. `sum_i` is used on purpose in the cross-entropy
  template; PPO's minimum is spelled `MINOF(...)` rather than `min_(...)`
  and its clip `CLIPCALL(...)`, since the grammar has no binder and no
  min/clip form. Both are opaque calls and are declared as such.
- Call arguments are ORDERED, so `MINOF`, `CLIPCALL`, `OUTER` and `UPDATE`
  all fix an argument order here that anything added later must keep.
"""

from __future__ import annotations

import json
from pathlib import Path


def sym(s, cat, role, desc, order=0):
    return {"symbol": s, "syntactic_category": cat, "semantic_role": role,
            "mathematical_order": order, "description": desc}


def op(symbol, name, arity=2, family="arithmetic"):
    return {"symbol": symbol, "name": name, "arity": arity, "operator_family": family}


def slot(sid, cat, role):
    return {"slot_id": sid, "syntactic_category": cat, "semantic_role": role}


def links(entailed_by=None, entails=None, equivalent_to=None,
          special_case_of=None, generalizes=None, composed_with=None):
    return {"entailed_by": entailed_by or [], "entails": entails or [],
            "equivalent_to": equivalent_to or [],
            "special_case_of": special_case_of or [],
            "generalizes": generalizes or [],
            "composed_with": composed_with or []}


def node(sid, title, cls, status, subfield, topic, ascii_, latex, forms,
         archetype, template, slots, invariants, symbols, operators,
         meaning, significance, conditions, provenance, disciplines=None,
         functionals=None, constants=None, index_sets=None, failure_modes=None,
         inferential_links=None, keywords=None, canonical_objects=None):
    context = {"disciplines": disciplines or ["machine_learning"],
               "subfield": subfield, "topic": topic}
    if canonical_objects:
        context["canonical_objects"] = canonical_objects
    interpretation = {"statement_meaning": meaning,
                      "statistical_significance": significance,
                      "regularity_conditions": conditions}
    if failure_modes:
        interpretation["failure_modes"] = failure_modes
    out = {
        "statement_id": sid, "title": title, "statement_class": cls,
        "epistemic_status": status,
        "theory_context": context,
        "formal_statement": {"canonical_ascii": ascii_, "canonical_latex": latex,
                             "equivalent_forms": forms},
        "structural_signature": {"archetype_id": archetype,
                                 "anonymized_template": template,
                                 "slot_schema": slots, "invariants": invariants},
        "symbol_lexicon": {"symbols": symbols, "operators": operators,
                           "functionals": functionals or [],
                           "index_sets": index_sets or [],
                           "constants": constants or []},
        "semantic_interpretation": interpretation,
        "inferential_links": inferential_links or links(),
        "provenance": provenance,
    }
    if keywords:
        out["keywords"] = keywords
    return out


# --------------------------------------------------------------------------
# Lexicon fragments
# --------------------------------------------------------------------------

EQ = op("=", "equality", 2, "relational")
ADD = op("+", "addition", 2, "arithmetic")
SUB = op("-", "subtraction", 2, "arithmetic")
MUL = op("*", "multiplication", 2, "arithmetic")
DIV = op("/", "division", 2, "arithmetic")
NEG = op("-", "negation", 1, "arithmetic")
SUM = op("sum", "finite summation over an index set", 1, "arithmetic")
EXPECT = op("E", "expectation under the stated distribution", 1, "stochastic")

ACTIVATION_FN = {
    "notation": "ACTIVATION(.)", "name": "elementwise nonlinearity",
    "input_arity": 1, "codomain": "a bounded or half-bounded interval",
    "description": "An elementwise nonlinearity, tanh in Elman's and Jordan's "
                   "networks and in the original LSTM's input/output "
                   "transformations, ReLU in most feedforward practice. Written "
                   "as an opaque head because the identity of the nonlinearity "
                   "is not what the recurrence asserts -- but see the node's "
                   "significance field: writing it as a head is exactly what "
                   "prevents this statement from meeting the affine family it "
                   "contains."}

SIGMOID_FN = {
    "notation": "SIGMOID(.)", "name": "logistic function", "input_arity": 1,
    "codomain": "the open unit interval",
    "description": "1/(1 + EXP(-x)). Used here as a *gate*: its output "
                   "multiplies a memory or an input, so its codomain (0,1) is "
                   "load-bearing, not incidental. A separate head from "
                   "ACTIVATION on purpose, because an LSTM gate is specifically "
                   "logistic while an Elman unit's nonlinearity is generic."}

SIGMOID_LINK_FN = {
    "notation": "SIGMOID(.)", "name": "logistic link function", "input_arity": 1,
    "codomain": "the open unit interval",
    "description": "1/(1 + EXP(-x)). Used here as a *link*, not a gate: it "
                   "maps a latent score difference to the probability that the "
                   "preferred item wins, which is the Bradley-Terry model. The "
                   "same head as in ml.recurrence.lstm_gate_activation and a "
                   "different job -- the corpus reuses the head deliberately, "
                   "since it is one function, but the two nodes' semantics "
                   "should not be read across."}

EXP_FN = {"notation": "EXP(.)", "name": "exponential", "input_arity": 1,
          "codomain": "positive reals",
          "description": "Natural exponential. Turns the additive score scale "
                         "on which models are trained into the multiplicative "
                         "probability scale on which they are evaluated."}

LOG_FN = {"notation": "LOG(.)", "name": "logarithm", "input_arity": 1,
          "codomain": "extended reals",
          "description": "Natural logarithm of a positive argument. Base is a "
                         "units convention: changing it multiplies the whole "
                         "expression by a constant, which is the role the "
                         "BATCHSCALE slot plays in the cross-entropy node."}

OUTER_FN = {"notation": "OUTER(left, right)", "name": "rank-one outer product",
            "input_arity": 2, "codomain": "matrices",
            "description": "The rank-one matrix v k^T built from two vectors. "
                           "Written as a call rather than with `*` because the "
                           "template canonicalizer flattens and SORTS `*`, "
                           "which would silently assert v k^T = k^T v -- one a "
                           "matrix, the other a scalar. Argument order is fixed: "
                           "value (column) first, key (row) second."}

UPDATE_FN = {"notation": "UPDATE(state, observation)", "name": "state update operator",
             "input_arity": 2, "codomain": "the state space",
             "description": "Opaque one-step update of a state from the previous "
                            "state and a new observation: the POMDP belief "
                            "update, the dialogue-state tracker's turn update, "
                            "and the abstract form of every recurrence in this "
                            "corpus. Argument order is fixed: prior state first, "
                            "new observation second."}

MINOF_FN = {"notation": "MINOF(left, right)", "name": "binary minimum",
            "input_arity": 2, "codomain": "reals",
            "description": "Pointwise minimum of two expressions. Spelled as a "
                           "call because the grammar has no binder and because "
                           "identifiers beginning `min_` are silently parsed as "
                           "prefix big-operators (docs/BACKLOG.md). Argument "
                           "order is fixed: unclipped term first, clipped term "
                           "second. The matcher cannot see that MINOF is "
                           "commutative."}

CLIPCALL_FN = {"notation": "CLIPCALL(value, lower, upper)", "name": "interval clamp",
               "input_arity": 3, "codomain": "the closed interval [lower, upper]",
               "description": "Clamps its first argument into the interval given "
                              "by the other two. An opaque call: the grammar has "
                              "no piecewise or conditional form, so the fact that "
                              "the clamp is the identity on the interval and "
                              "constant outside it is invisible to the matcher, "
                              "and with it the entire mechanism by which PPO "
                              "kills the gradient outside the trust region."}

IDX_VOCAB = {"notation": "i in V", "domain": "the model's token vocabulary",
             "description": "Index running over vocabulary entries at one "
                            "position; the sum is over the vocabulary, and the "
                            "batch/sequence average is carried by the scale slot."}

BATCHSCALE_CONST = {
    "symbol": "1/N",
    "description": "Reciprocal of the number of scored positions in the batch. "
                   "Kept explicit rather than folded away because it occupies "
                   "the same unit-scale slot that carries 1/ln 2 in "
                   "infotheory.divergence.cross_entropy and kB in "
                   "physics.thermodynamics.gibbs_entropy; dropping it would "
                   "break the typed twin with information theory for a purely "
                   "notational reason."}

# --------------------------------------------------------------------------
# Provenance
# --------------------------------------------------------------------------

ELMAN1990 = {"citation_key": "elman1990",
             "bibliographic_entry": "Elman, J. L. (1990). Finding Structure in Time. Cognitive Science, 14(2), 179-211.",
             "url": "https://doi.org/10.1207/s15516709cog1402_1"}
RUMELHART1986 = {"citation_key": "rumelhart1986",
                 "bibliographic_entry": "Rumelhart, D. E., Hinton, G. E., Williams, R. J. (1986). Learning representations by back-propagating errors. Nature, 323(6088), 533-536.",
                 "url": "https://doi.org/10.1038/323533a0"}
JORDAN1986 = {"citation_key": "jordan1986",
              "bibliographic_entry": "Jordan, M. I. (1986). Serial Order: A Parallel Distributed Processing Approach. ICS Report 8604, Institute for Cognitive Science, University of California, San Diego."}
HOCHREITER1997 = {"citation_key": "hochreiter1997",
                  "bibliographic_entry": "Hochreiter, S., Schmidhuber, J. (1997). Long Short-Term Memory. Neural Computation, 9(8), 1735-1780.",
                  "url": "https://doi.org/10.1162/neco.1997.9.8.1735"}
GERS2000 = {"citation_key": "gers2000",
            "bibliographic_entry": "Gers, F. A., Schmidhuber, J., Cummins, F. (2000). Learning to Forget: Continual Prediction with LSTM. Neural Computation, 12(10), 2451-2471.",
            "url": "https://doi.org/10.1162/089976600300015015"}
GU2022S4 = {"citation_key": "gu2022s4",
            "bibliographic_entry": "Gu, A., Goel, K., Re, C. (2022). Efficiently Modeling Long Sequences with Structured State Spaces. International Conference on Learning Representations (ICLR 2022). arXiv:2111.00396.",
            "url": "https://arxiv.org/abs/2111.00396"}
GU2022S4D = {"citation_key": "gu2022s4d",
             "bibliographic_entry": "Gu, A., Goel, K., Gupta, A., Re, C. (2022). On the Parameterization and Initialization of Diagonal State Space Models. Advances in Neural Information Processing Systems 35 (NeurIPS 2022). arXiv:2206.11893.",
             "url": "https://arxiv.org/abs/2206.11893"}
GU2023MAMBA = {"citation_key": "gu2023mamba",
               "bibliographic_entry": "Gu, A., Dao, T. (2023). Mamba: Linear-Time Sequence Modeling with Selective State Spaces. arXiv:2312.00752.",
               "url": "https://arxiv.org/abs/2312.00752"}
KALMAN1960 = {"citation_key": "kalman1960",
              "bibliographic_entry": "Kalman, R. E. (1960). A New Approach to Linear Filtering and Prediction Problems. Journal of Basic Engineering, 82(1), 35-45.",
              "url": "https://doi.org/10.1115/1.3662552"}
BECK2024 = {"citation_key": "beck2024xlstm",
            "bibliographic_entry": "Beck, M., Poeppel, K., Spanring, M., Auer, A., Prudnikova, O., Kopp, M., Klambauer, G., Brandstetter, J., Hochreiter, S. (2024). xLSTM: Extended Long Short-Term Memory. Advances in Neural Information Processing Systems 37 (NeurIPS 2024). arXiv:2405.04517.",
            "url": "https://arxiv.org/abs/2405.04517"}
MLSTM_KERNELS = {"citation_key": "nxai2024mlstmkernels",
                 "bibliographic_entry": "NX-AI (2024). mlstm_kernels: Tiled and chunkwise-parallel Triton/CUDA kernels for the mLSTM matrix-memory recurrence. Software repository.",
                 "url": "https://github.com/NX-AI/mlstm_kernels"}
SCHLAG2021 = {"citation_key": "schlag2021",
              "bibliographic_entry": "Schlag, I., Irie, K., Schmidhuber, J. (2021). Linear Transformers Are Secretly Fast Weight Programmers. International Conference on Machine Learning (ICML 2021). arXiv:2102.11174.",
              "url": "https://arxiv.org/abs/2102.11174"}
KAELBLING1998 = {"citation_key": "kaelbling1998",
                 "bibliographic_entry": "Kaelbling, L. P., Littman, M. L., Cassandra, A. R. (1998). Planning and acting in partially observable stochastic domains. Artificial Intelligence, 101(1-2), 99-134.",
                 "url": "https://doi.org/10.1016/S0004-3702(98)00023-X"}
YOUNG2013 = {"citation_key": "young2013",
             "bibliographic_entry": "Young, S., Gasic, M., Thomson, B., Williams, J. D. (2013). POMDP-Based Statistical Spoken Dialog Systems: A Review. Proceedings of the IEEE, 101(5), 1160-1179.",
             "url": "https://doi.org/10.1109/JPROC.2012.2225812"}
WILLIAMS2016DSTC = {"citation_key": "williams2016dstc",
                    "bibliographic_entry": "Williams, J. D., Raux, A., Henderson, M. (2016). The Dialog State Tracking Challenge Series: A Review. Dialogue & Discourse, 7(3), 4-33.",
                    "url": "https://doi.org/10.5087/dad.2016.301"}
XU2024DST = {"citation_key": "xu2024cote",
             "bibliographic_entry": "Xu, L., Peng, N., Zhou, D., Ng, S.-K., Fu, J. (2024). Chain of Thought Explanation for Dialogue State Tracking. arXiv:2403.04656.",
             "url": "https://arxiv.org/abs/2403.04656"}
NIU2024DST = {"citation_key": "niu2024dst",
              "bibliographic_entry": "Niu, C., Wang, X., Cheng, X., Song, J., Zhang, T. (2024). Enhancing Dialogue State Tracking Models through LLM-backed User-Agents Simulation. arXiv:2405.13037.",
              "url": "https://arxiv.org/abs/2405.13037"}
HONG2023DTN = {"citation_key": "hong2023llmtwin",
               "bibliographic_entry": "Hong, Y., Wu, J., Morello, R. (2023). LLM-Twin: Mini-Giant Model-driven Beyond 5G Digital Twin Networking Framework with Semantic Secure Communication and Computation. arXiv:2312.10631.",
               "url": "https://arxiv.org/abs/2312.10631"}
CAUCHY1847 = {"citation_key": "cauchy1847",
              "bibliographic_entry": "Cauchy, A.-L. (1847). Methode generale pour la resolution des systemes d'equations simultanees. Comptes Rendus Hebdomadaires des Seances de l'Academie des Sciences, 25, 536-538."}
ROBBINS1951 = {"citation_key": "robbins1951",
               "bibliographic_entry": "Robbins, H., Monro, S. (1951). A Stochastic Approximation Method. Annals of Mathematical Statistics, 22(3), 400-407.",
               "url": "https://doi.org/10.1214/aoms/1177729586"}
KINGMA2015 = {"citation_key": "kingma2015adam",
              "bibliographic_entry": "Kingma, D. P., Ba, J. (2015). Adam: A Method for Stochastic Optimization. International Conference on Learning Representations (ICLR 2015). arXiv:1412.6980.",
              "url": "https://arxiv.org/abs/1412.6980"}
BOLTZMANN1877 = {"citation_key": "boltzmann1877",
                 "bibliographic_entry": "Boltzmann, L. (1877). Ueber die Beziehung zwischen dem zweiten Hauptsatze der mechanischen Waermetheorie und der Wahrscheinlichkeitsrechnung. Sitzungsberichte der Kaiserlichen Akademie der Wissenschaften in Wien, 76, 373-435."}
BRIDLE1990 = {"citation_key": "bridle1990",
              "bibliographic_entry": "Bridle, J. S. (1990). Probabilistic Interpretation of Feedforward Classification Network Outputs, with Relationships to Statistical Pattern Recognition. In Neurocomputing: Algorithms, Architectures and Applications, NATO ASI Series F68, 227-236."}
LUCE1959 = {"citation_key": "luce1959",
            "bibliographic_entry": "Luce, R. D. (1959). Individual Choice Behavior: A Theoretical Analysis. New York: Wiley."}
SUTTON2018 = {"citation_key": "sutton2018",
              "bibliographic_entry": "Sutton, R. S., Barto, A. G. (2018). Reinforcement Learning: An Introduction (2nd ed.). Cambridge, MA: MIT Press."}
GOOD1952 = {"citation_key": "good1952",
            "bibliographic_entry": "Good, I. J. (1952). Rational Decisions. Journal of the Royal Statistical Society Series B, 14(1), 107-114."}
SHANNON1948 = {"citation_key": "shannon1948",
               "bibliographic_entry": "Shannon, C. E. (1948). A Mathematical Theory of Communication. Bell System Technical Journal, 27(3), 379-423 and 27(4), 623-656.",
               "url": "https://doi.org/10.1002/j.1538-7305.1948.tb01338.x"}
GOODFELLOW2016 = {"citation_key": "goodfellow2016",
                  "bibliographic_entry": "Goodfellow, I., Bengio, Y., Courville, A. (2016). Deep Learning. Cambridge, MA: MIT Press."}
BENGIO2003 = {"citation_key": "bengio2003",
              "bibliographic_entry": "Bengio, Y., Ducharme, R., Vincent, P., Jauvin, C. (2003). A Neural Probabilistic Language Model. Journal of Machine Learning Research, 3, 1137-1155."}
ZIEGLER2019 = {"citation_key": "ziegler2019",
               "bibliographic_entry": "Ziegler, D. M., Stiennon, N., Wu, J., Brown, T. B., Radford, A., Amodei, D., Christiano, P., Irving, G. (2019). Fine-Tuning Language Models from Human Preferences. arXiv:1909.08593.",
               "url": "https://arxiv.org/abs/1909.08593"}
STIENNON2020 = {"citation_key": "stiennon2020",
                "bibliographic_entry": "Stiennon, N., Ouyang, L., Wu, J., Ziegler, D. M., Lowe, R., Voss, C., Radford, A., Amodei, D., Christiano, P. (2020). Learning to summarize from human feedback. Advances in Neural Information Processing Systems 33 (NeurIPS 2020). arXiv:2009.01325.",
                "url": "https://arxiv.org/abs/2009.01325"}
OUYANG2022 = {"citation_key": "ouyang2022",
              "bibliographic_entry": "Ouyang, L., Wu, J., Jiang, X., Almeida, D., Wainwright, C. L., Mishkin, P., et al. (2022). Training language models to follow instructions with human feedback. Advances in Neural Information Processing Systems 35 (NeurIPS 2022). arXiv:2203.02155.",
              "url": "https://arxiv.org/abs/2203.02155"}
LEVINE2018 = {"citation_key": "levine2018",
              "bibliographic_entry": "Levine, S. (2018). Reinforcement Learning and Control as Probabilistic Inference: Tutorial and Review. arXiv:1805.00909.",
              "url": "https://arxiv.org/abs/1805.00909"}
TODOROV2007 = {"citation_key": "todorov2007",
               "bibliographic_entry": "Todorov, E. (2007). Linearly-solvable Markov decision problems. Advances in Neural Information Processing Systems 19 (NIPS 2006), 1369-1376."}
SCHULMAN2015 = {"citation_key": "schulman2015trpo",
                "bibliographic_entry": "Schulman, J., Levine, S., Moritz, P., Jordan, M. I., Abbeel, P. (2015). Trust Region Policy Optimization. International Conference on Machine Learning (ICML 2015). arXiv:1502.05477.",
                "url": "https://arxiv.org/abs/1502.05477"}
SCHULMAN2017 = {"citation_key": "schulman2017ppo",
                "bibliographic_entry": "Schulman, J., Wolski, F., Dhariwal, P., Radford, A., Klimov, O. (2017). Proximal Policy Optimization Algorithms. arXiv:1707.06347.",
                "url": "https://arxiv.org/abs/1707.06347"}
KAKADE2002 = {"citation_key": "kakade2002",
              "bibliographic_entry": "Kakade, S., Langford, J. (2002). Approximately Optimal Approximate Reinforcement Learning. International Conference on Machine Learning (ICML 2002), 267-274."}
RAFAILOV2023 = {"citation_key": "rafailov2023dpo",
                "bibliographic_entry": "Rafailov, R., Sharma, A., Mitchell, E., Ermon, S., Manning, C. D., Finn, C. (2023). Direct Preference Optimization: Your Language Model is Secretly a Reward Model. Advances in Neural Information Processing Systems 36 (NeurIPS 2023). arXiv:2305.18290.",
                "url": "https://arxiv.org/abs/2305.18290"}
BRADLEY1952 = {"citation_key": "bradley1952",
               "bibliographic_entry": "Bradley, R. A., Terry, M. E. (1952). Rank Analysis of Incomplete Block Designs: I. The Method of Paired Comparisons. Biometrika, 39(3/4), 324-345.",
               "url": "https://doi.org/10.2307/2334029"}
ETHAYARAJH2024 = {"citation_key": "ethayarajh2024kto",
                  "bibliographic_entry": "Ethayarajh, K., Xu, W., Muennighoff, N., Jurafsky, D., Kiela, D. (2024). KTO: Model Alignment as Prospect Theoretic Optimization. International Conference on Machine Learning (ICML 2024). arXiv:2402.01306.",
                  "url": "https://arxiv.org/abs/2402.01306"}
HONG2024ORPO = {"citation_key": "hong2024orpo",
                "bibliographic_entry": "Hong, J., Lee, N., Thorne, J. (2024). ORPO: Monolithic Preference Optimization without Reference Model. Conference on Empirical Methods in Natural Language Processing (EMNLP 2024). arXiv:2403.07691.",
                "url": "https://arxiv.org/abs/2403.07691"}
SHAO2024 = {"citation_key": "shao2024grpo",
            "bibliographic_entry": "Shao, Z., Wang, P., Zhu, Q., Xu, R., Song, J., Bi, X., Zhang, H., Zhang, M., Li, Y. K., Wu, Y., Guo, D. (2024). DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models. arXiv:2402.03300.",
            "url": "https://arxiv.org/abs/2402.03300"}
DEEPSEEK2025 = {"citation_key": "deepseek2025r1",
                "bibliographic_entry": "DeepSeek-AI (2025). DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning. arXiv:2501.12948.",
                "url": "https://arxiv.org/abs/2501.12948"}
WILLIAMS1992 = {"citation_key": "williams1992",
                "bibliographic_entry": "Williams, R. J. (1992). Simple statistical gradient-following algorithms for connectionist reinforcement learning. Machine Learning, 8(3-4), 229-256.",
                "url": "https://doi.org/10.1007/BF00992696"}
HU2021LORA = {"citation_key": "hu2021lora",
              "bibliographic_entry": "Hu, E. J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S., Wang, L., Chen, W. (2021). LoRA: Low-Rank Adaptation of Large Language Models. International Conference on Learning Representations (ICLR 2022). arXiv:2106.09685.",
              "url": "https://arxiv.org/abs/2106.09685"}
LIU2024DORA = {"citation_key": "liu2024dora",
               "bibliographic_entry": "Liu, S.-Y., Wang, C.-Y., Yin, H., Molchanov, P., Wang, Y.-C. F., Cheng, K.-T., Chen, M.-H. (2024). DoRA: Weight-Decomposed Low-Rank Adaptation. International Conference on Machine Learning (ICML 2024). arXiv:2402.09353.",
               "url": "https://arxiv.org/abs/2402.09353"}
MENG2024PISSA = {"citation_key": "meng2024pissa",
                 "bibliographic_entry": "Meng, F., Wang, Z., Zhang, M. (2024). PiSSA: Principal Singular Values and Singular Vectors Adaptation of Large Language Models. Advances in Neural Information Processing Systems 37 (NeurIPS 2024). arXiv:2404.02948.",
                 "url": "https://arxiv.org/abs/2404.02948"}
LI2023LOFTQ = {"citation_key": "li2023loftq",
               "bibliographic_entry": "Li, Y., Yu, Y., Liang, C., He, P., Karampatziakis, N., Chen, W., Zhao, T. (2023). LoftQ: LoRA-Fine-Tuning-Aware Quantization for Large Language Models. arXiv:2310.08659.",
               "url": "https://arxiv.org/abs/2310.08659"}
AGHAJANYAN2021 = {"citation_key": "aghajanyan2021",
                  "bibliographic_entry": "Aghajanyan, A., Gupta, S., Zettlemoyer, L. (2021). Intrinsic Dimensionality Explains the Effectiveness of Language Model Fine-Tuning. Annual Meeting of the Association for Computational Linguistics (ACL 2021). arXiv:2012.13255.",
                  "url": "https://arxiv.org/abs/2012.13255"}

# --------------------------------------------------------------------------
# Nodes
# --------------------------------------------------------------------------

NODES = [

    # ---------------------------------------------------------------- 1 ----
    node("ml.recurrence.elman_rnn_hidden_state",
         "Elman Recurrent Hidden-State Update",
         "model_specification", "assumed", "sequence_models", "recurrence",
         "h_t = phi(W_h * h_(t-1) + W_x * x_t + b)",
         "h_t = \\phi\\!\\left(W_h h_{t-1} + W_x x_t + b\\right)",
         [{"form_id": "concatenated", "notation_system": "matrix_notation",
           "expression": "h_t = phi(W * [h_(t-1); x_t] + b)",
           "scope_note": "The two weight matrices stacked; the same map, written as one affine block"},
          {"form_id": "jordan", "notation_system": "ascii",
           "expression": "h_t = phi(W_h * y_(t-1) + W_x * x_t + b)",
           "scope_note": "Jordan's (1986) variant: the recurrent input is the previous output, not the previous hidden state"},
          {"form_id": "unrolled", "notation_system": "ascii",
           "expression": "h_t = phi(W_h * phi(W_h * h_(t-2) + W_x * x_(t-1) + b) + W_x * x_t + b)",
           "scope_note": "One step of unrolling; iterating this is what produces the vanishing/exploding gradient the LSTM was designed against"}],
         "nonlinear_affine_recurrence",
         "HIDDENNEXT = ACTIVATION(WEIGHTREC*HIDDEN + WEIGHTIN*INPUT + BIAS)",
         [slot("HIDDENNEXT", "variable", "output_state"),
          slot("WEIGHTREC", "parameter", "recurrent_weight"),
          slot("HIDDEN", "variable", "previous_state"),
          slot("WEIGHTIN", "parameter", "input_weight"),
          slot("INPUT", "variable", "observation"),
          slot("BIAS", "parameter", "offset")],
         ["The argument of ACTIVATION is an affine map of the pair (previous "
          "state, current input): two parameter-weighted variable terms plus a "
          "parameter offset. Everything the network learns lives in the "
          "parameter-like slots; everything that changes with time lives in the "
          "variable-like ones.",
          "The same two weight slots are reused at every time step. That "
          "sharing is not visible in a one-step template -- the template says "
          "nothing about t -- and it is the whole reason recurrent networks "
          "generalize across sequence length. Recorded here because the "
          "matcher cannot see it.",
          "The nonlinearity is applied *outside* the affine map, not inside "
          "it. That ordering is the statement: an affine recurrence composed "
          "with a squashing function, iterated.",
          "The composition is what makes the recurrence contractive or "
          "expansive; the Jacobian of the iterated map is a product of terms "
          "W_h * phi', and whether its spectral radius sits above or below 1 "
          "is exactly the vanishing/exploding gradient problem."],
         [sym("h_t", "variable", "output_state",
              "Hidden state after consuming the t-th input.", 1),
          sym("x_t", "variable", "observation",
              "Input vector at step t.", 1),
          sym("b", "parameter", "offset",
              "Bias vector, learned and shared across time steps.", 1),
          sym("W_h", "parameter", "recurrent_weight",
              "Recurrent weight matrix, shared across time steps.", 2),
          sym("W_x", "parameter", "input_weight",
              "Input weight matrix, shared across time steps.", 2),
          sym("t", "index", "time_index",
              "Discrete time step; a scalar index over the sequence.", 0)],
         [EQ, ADD, MUL],
         "A recurrent unit's new state is a learned affine mixture of its old "
         "state and the current input, squashed through a nonlinearity.",
         "The corpus's clearest demonstration that a wrapper is a wall. The "
         "expression *inside* ACTIVATION is the affine family this graph is "
         "full of -- tangent-line linearization, CAPM, the Keynesian "
         "consumption function, probstat.transform.affine_location_scale -- but "
         "the node's skeleton is "
         "`?0:V = ACTIVATION⟨+(?1:P, *(?2:P, ?3:V), *(?4:P, ?5:V))⟩` and it "
         "twins with nothing at shape, typed or family level. Two independent "
         "obstacles stack, and it is worth separating them because fixing "
         "either alone changes nothing. (1) Call heads are literal at every "
         "match level, so the nonlinearity quarantines its whole argument; the "
         "same obstacle data/morphology recorded, here inside a single "
         "expression rather than between corpora. (2) Even stripped of the "
         "wrapper, the argument is *multiple* linear regression -- two "
         "regressors -- and the statistics corpus carries only the simple "
         "one-regressor form, so the arities differ. The honest reading is "
         "that this node's relationship to the affine family is real and the "
         "matcher cannot certify it; the claim sits in this prose, which is "
         "exactly the situation docs/BACKLOG.md flags as the limit on any "
         "claim that the tool *finds* structure.",
         ["A fixed input and state dimensionality across the sequence",
          "Parameters tied across time steps (that tying is the model, not the equation)",
          "An initial state h_0 supplied by convention, usually zero"],
         [ELMAN1990, JORDAN1986, RUMELHART1986, GOODFELLOW2016],
         functionals=[ACTIVATION_FN],
         failure_modes=[
             "Iterating the map multiplies Jacobians, so gradients through long "
             "sequences vanish or explode; the equation is silent about this "
             "because the pathology is a property of the iteration, not of one "
             "step.",
             "Reading the hidden state as 'memory' overstates it: nothing in "
             "the equation protects information across steps, which is "
             "precisely the gap ml.recurrence.lstm_gate_activation's gating "
             "was introduced to close."],
         inferential_links=links(
             special_case_of=["ml.recurrence.belief_state_update"],
             composed_with=["ml.recurrence.lstm_gate_activation",
                            "ml.recurrence.linear_ssm_state_update"]),
         keywords=["recurrent neural network", "Elman network", "hidden state",
                   "affine map", "nonlinearity", "sequence model"],
         canonical_objects=["hidden state vector", "weight matrix", "input sequence"]),

    # ---------------------------------------------------------------- 2 ----
    node("ml.recurrence.lstm_gate_activation",
         "LSTM Gate Activation",
         "model_specification", "assumed", "sequence_models", "gating",
         "g_t = sigma(W_x * x_t + W_h * h_(t-1) + b)",
         "g_t = \\sigma\\!\\left(W_x x_t + W_h h_{t-1} + b\\right)",
         [{"form_id": "forget_gate", "notation_system": "ascii",
           "expression": "f_t = sigma(W_xf * x_t + W_hf * h_(t-1) + b_f)",
           "scope_note": "The forget gate of Gers et al. (2000); the same equation with the forget-gate parameters"},
          {"form_id": "input_gate", "notation_system": "ascii",
           "expression": "i_t = sigma(W_xi * x_t + W_hi * h_(t-1) + b_i)",
           "scope_note": "The input gate of Hochreiter and Schmidhuber (1997)"},
          {"form_id": "peephole", "notation_system": "ascii",
           "expression": "g_t = sigma(W_x * x_t + W_h * h_(t-1) + W_c * c_(t-1) + b)",
           "scope_note": "Peephole variant: the cell state joins the affine argument, adding a third regressor"},
          {"form_id": "cell_update", "notation_system": "ascii",
           "expression": "c_t = f_t * c_(t-1) + i_t * ctilde_t",
           "scope_note": "What the gates are for: the constant-error-carousel cell update they multiply"}],
         "gated_affine_recurrence",
         "GATE = SIGMOID(WEIGHTIN*INPUT + WEIGHTREC*HIDDEN + BIAS)",
         [slot("GATE", "variable", "gate_value"),
          slot("WEIGHTIN", "parameter", "input_weight"),
          slot("INPUT", "variable", "observation"),
          slot("WEIGHTREC", "parameter", "recurrent_weight"),
          slot("HIDDEN", "variable", "previous_state"),
          slot("BIAS", "parameter", "offset")],
         ["Structurally identical to ml.recurrence.elman_rnn_hidden_state "
          "modulo the head string: the same affine argument, the same slot "
          "categories, the same arity. Only SIGMOID versus ACTIVATION differs, "
          "and that one string is enough to keep the two nodes apart at every "
          "match level.",
          "The codomain (0,1) is load-bearing here in a way it is not for a "
          "generic activation: the output is multiplied into a memory, so it "
          "must be interpretable as a fraction retained. A ReLU here would not "
          "be a variant, it would be a different mechanism.",
          "The bias slot is the one practitioners initialize deliberately "
          "positive for the forget gate, which starts the network in a "
          "remember-by-default regime. That is a statement about the parameter "
          "slot's initial value, not about the equation's form.",
          "Three or four instances of this one equation, with different "
          "parameters in the same slots, constitute an LSTM cell; the cell's "
          "distinguishing feature is not this equation but what the gates "
          "multiply."],
         [sym("g_t", "variable", "gate_value",
              "Gate activation in (0,1), elementwise.", 1),
          sym("x_t", "variable", "observation", "Input vector at step t.", 1),
          sym("h_t", "variable", "previous_state",
              "Hidden state carried in from the previous step.", 1),
          sym("b", "parameter", "offset", "Gate bias vector.", 1),
          sym("W_x", "parameter", "input_weight", "Input-to-gate weight matrix.", 2),
          sym("W_h", "parameter", "recurrent_weight", "State-to-gate weight matrix.", 2),
          sym("t", "index", "time_index", "Discrete time step.", 0)],
         [EQ, ADD, MUL],
         "A gate is a logistic function of the same affine mixture a plain "
         "recurrent unit computes; its output is a per-coordinate fraction "
         "that says how much of some quantity to keep.",
         "A controlled experiment on the matcher, run inside one corpus. This "
         "node and ml.recurrence.elman_rnn_hidden_state produce "
         "`?0:V = SIGMOID⟨+(?1:P, *(?2:P, ?3:V), *(?4:P, ?5:V))⟩` and "
         "`?0:V = ACTIVATION⟨+(?1:P, *(?2:P, ?3:V), *(?4:P, ?5:V))⟩` -- "
         "character for character the same string apart from the head -- and "
         "they do not twin at shape level, which is supposed to be the loosest "
         "level available. docs/BACKLOG.md records this obstacle from "
         "data/morphology, where four skeletons differed from existing ones by "
         "one head string across corpus boundaries; the case here is stronger, "
         "because both halves were authored by the same hand in the same file "
         "with no intent to hide the relationship, and the tool still cannot "
         "see it. Whatever head-alias mechanism the backlog eventually gets "
         "should be tested on this pair first: it is the smallest possible "
         "instance, one differing token in an otherwise identical tree.",
         ["Elementwise application of the logistic function",
          "Gate parameters distinct from the cell's other parameters",
          "A supplied previous hidden state"],
         [HOCHREITER1997, GERS2000, GOODFELLOW2016],
         functionals=[SIGMOID_FN],
         failure_modes=[
             "Saturated gates have vanishing derivative, so a gate driven hard "
             "to 0 or 1 stops learning; the equation cannot express that its "
             "own trainability depends on staying off the rails.",
             "Calling the gate 'attention' or 'a decision' reads intent into a "
             "coordinatewise scalar multiplier. It is a learned interpolation "
             "coefficient and nothing more."],
         inferential_links=links(
             composed_with=["ml.recurrence.elman_rnn_hidden_state",
                            "ml.recurrence.mlstm_matrix_memory_update"]),
         keywords=["LSTM", "gate", "logistic", "forget gate",
                   "constant error carousel", "head literalism"],
         canonical_objects=["gate vector", "cell state", "weight matrix"]),

    # ---------------------------------------------------------------- 3 ----
    node("ml.recurrence.linear_ssm_state_update",
         "Linear State-Space Model State Update",
         "model_specification", "assumed", "sequence_models", "state_space",
         "s_(t+1) = a * s_t + b * u_t",
         "s_{t+1} = a\\, s_t + b\\, u_t",
         [{"form_id": "matrix", "notation_system": "matrix_notation",
           "expression": "s_(t+1) = A * s_t + B * u_t",
           "scope_note": "Full matrix form; S4D and Mamba take A diagonal, which is what makes the scalar reading above exact per channel"},
          {"form_id": "continuous", "notation_system": "ascii",
           "expression": "ds/dt = A * s + B * u",
           "scope_note": "The continuous-time system that S4 discretizes; the discrete coefficients are its zero-order hold or bilinear transform"},
          {"form_id": "convolution", "notation_system": "ascii",
           "expression": "y_t = sum_k (C * A^k * B) * u_(t-k)",
           "scope_note": "The same recurrence unrolled into a convolution with a structured kernel; the dual view that makes S4 trainable in parallel"},
          {"form_id": "selective", "notation_system": "ascii",
           "expression": "s_(t+1) = a(u_t) * s_t + b(u_t) * u_t",
           "scope_note": "Mamba's selective variant: the coefficients become functions of the input, which is the step that makes them gates"}],
         "linear_two_term_state_recurrence",
         "STATENEXT = TRANSITION*STATE + INPUTGAIN*DRIVE",
         [slot("STATENEXT", "variable", "next_state"),
          slot("TRANSITION", "parameter", "state_coefficient"),
          slot("STATE", "variable", "current_state"),
          slot("INPUTGAIN", "parameter", "input_coefficient"),
          slot("DRIVE", "variable", "input_signal")],
         ["Written in the per-channel scalar form that S4D and Mamba actually "
          "use: their state matrix is diagonal, so each channel's recurrence is "
          "genuinely a scalar one and the commutative `*` of the template "
          "grammar tells no lie here. That is not true of the general matrix "
          "form, and it is not true of "
          "ml.recurrence.mlstm_matrix_memory_update.",
          "Both coefficients are parameter-like: learned, then held fixed while "
          "the sequence is processed. This is the single property that "
          "separates a state-space model from a gated one, and it is visible in "
          "the slot categories rather than in the shape.",
          "No nonlinearity anywhere. Linearity is what buys the convolutional "
          "form: the recurrence can be unrolled into a kernel and evaluated "
          "with an FFT, which is the entire engineering argument for the family.",
          "Stability is a condition on the transition slot's magnitude, not a "
          "property of the equation: |a| < 1 for the discrete form. The "
          "HiPPO initialization exists to place that slot well.",
          "Identical in form to the Kalman filter's state equation minus its "
          "process noise; the ML literature reinvented it with learned rather "
          "than physically identified coefficients."],
         [sym("s_t", "variable", "current_state",
              "State at step t; a scalar per channel in the diagonal form.", 0),
          sym("u_t", "variable", "input_signal", "Input at step t.", 0),
          sym("a", "parameter", "state_coefficient",
              "State transition coefficient, learned and fixed at inference.", 0),
          sym("b", "parameter", "input_coefficient",
              "Input gain, learned and fixed at inference.", 0),
          sym("t", "index", "time_index", "Discrete time step.", 0)],
         [EQ, ADD, MUL],
         "The next state is a fixed linear blend of the current state and the "
         "current input: memory decays at a learned rate while new signal is "
         "injected at a learned gain.",
         "Prediction 2, registered before running the matcher, was that this "
         "node would typed- or family-twin the noisy-affine / AR-style "
         "statistics nodes. It does not, and the reason is arity: "
         "probstat.regression.slr_stochastic_specification is "
         "`?0:V = +(?1:P, ?2:V, *(?3:P, ?4:V))` -- intercept, noise, one "
         "weighted regressor -- while this node is "
         "`?0:V = +(*(?1:P, ?2:V), *(?3:P, ?4:V))`, two weighted terms and no "
         "intercept. The prediction is not simply wrong, though: "
         "scripts/specialize.py recovers it, deriving the regression "
         "specification as the general case with the intercept bound to the "
         "additive identity and the noise slot absorbing the autoregressive "
         "term. Which is the correct relationship -- an AR(1) process is the "
         "regression of a series on its own past -- reached at the "
         "specialization level rather than the twin level.",
         ["Time-invariant coefficients within a sequence",
          "Diagonal (per-channel) state matrix, as in S4D and Mamba; the "
          "scalar template is exact only under that assumption",
          "|a| < 1 for a stable discrete recurrence",
          "A discretization step already applied if the model was specified in "
          "continuous time"],
         [GU2022S4, GU2022S4D, GU2023MAMBA, KALMAN1960],
         failure_modes=[
             "Linearity is the whole computational advantage and the whole "
             "expressive limit: without input-dependent coefficients the model "
             "cannot select what to remember, which is why Mamba reintroduces "
             "them and thereby leaves this equation's typed skeleton.",
             "The convolutional and recurrent views agree only for a linear "
             "time-invariant system; any input dependence in the coefficients "
             "voids the equivalence that the fast training path relies on.",
             "Reading `a` as an interpretable decay rate is safe only in the "
             "diagonal parameterization; for a general A the eigenvalues, not "
             "the entries, carry that meaning."],
         inferential_links=links(
             special_case_of=["ml.recurrence.belief_state_update"],
             composed_with=["ml.recurrence.elman_rnn_hidden_state",
                            "ml.recurrence.mlstm_matrix_memory_update"]),
         keywords=["state-space model", "S4", "Mamba", "linear recurrence",
                   "HiPPO", "Kalman", "autoregression"],
         canonical_objects=["state vector", "transition coefficient", "input sequence"]),

    # ---------------------------------------------------------------- 4 ----
    node("ml.recurrence.mlstm_matrix_memory_update",
         "mLSTM Matrix-Memory Covariance Update (xLSTM)",
         "model_specification", "assumed", "sequence_models", "associative_memory",
         "C_t = f_t * C_(t-1) + i_t * outer(v_t, k_t)",
         "C_t = f_t\\, C_{t-1} + i_t\\, v_t k_t^{\\top}",
         [{"form_id": "retrieval", "notation_system": "matrix_notation",
           "expression": "htilde_t = C_t * q_t",
           "scope_note": "What the memory is for: a query retrieves a weighted mixture of stored values"},
          {"form_id": "fast_weights", "notation_system": "matrix_notation",
           "expression": "W_t = W_(t-1) + v_t * k_t^T",
           "scope_note": "The ungated ancestor: Schlag et al.'s fast-weight programmer, equivalently the linear-attention state"},
          {"form_id": "unrolled", "notation_system": "ascii",
           "expression": "C_t = sum_j (prod over l>j of f_l) * i_j * outer(v_j, k_j)",
           "scope_note": "Unrolled: a decayed sum of rank-one writes, which is the covariance-update reading"}],
         "gated_rank_one_memory_accumulation",
         "MEMORYNEXT = FORGETGATE*MEMORY + INPUTGATE*OUTER(VALUE, KEY)",
         [slot("MEMORYNEXT", "variable", "next_memory"),
          slot("FORGETGATE", "variable", "retention_coefficient"),
          slot("MEMORY", "variable", "current_memory"),
          slot("INPUTGATE", "variable", "write_coefficient"),
          slot("VALUE", "variable", "stored_content"),
          slot("KEY", "variable", "address")],
         ["Every slot is variable-like. The two coefficients are gates computed "
          "from the current input, so unlike "
          "ml.recurrence.linear_ssm_state_update nothing here is held fixed "
          "while the sequence runs. That difference is the whole architectural "
          "argument of xLSTM against a plain linear state-space model, and it "
          "is expressed entirely in the slot categories.",
          "The written quantity is a rank-one matrix, not a vector. OUTER is a "
          "call rather than a `*` because the canonicalizer flattens and sorts "
          "`*`, which would assert that v k^T equals k^T v -- an outer product "
          "against an inner product. The extra call node is the price of not "
          "lying, and it is one of the two reasons this node cannot twin the "
          "state-space update.",
          "The memory is an accumulator of key-value associations, so the state "
          "is quadratic in the model width while the recurrence stays linear in "
          "sequence length. That is the trade the design is making.",
          "Retrieval is a separate statement (see equivalent_forms): this "
          "equation only writes. Splitting write from read is what allows the "
          "chunkwise-parallel kernels in the reference implementation."],
         [sym("f_t", "variable", "retention_coefficient",
              "Forget gate at step t, a scalar per head in the mLSTM.", 0),
          sym("i_t", "variable", "write_coefficient",
              "Input gate at step t, a scalar per head.", 0),
          sym("v_t", "variable", "stored_content", "Value vector at step t.", 1),
          sym("k_t", "variable", "address", "Key vector at step t.", 1),
          sym("C_t", "variable", "next_memory",
              "Matrix memory after step t.", 2),
          sym("t", "index", "time_index", "Discrete time step.", 0)],
         [EQ, ADD, MUL],
         "A matrix memory is decayed by a forget gate and then has a fresh "
         "key-value association added to it, scaled by an input gate: a gated "
         "running covariance of the sequence.",
         "The comparison the corpus was built to make, and it comes back "
         "negative twice over. Read informally, this equation and "
         "ml.recurrence.linear_ssm_state_update are the same statement -- "
         "state = coefficient*state + coefficient*drive -- with gates where the "
         "state-space model has learned constants. The matcher disagrees, and "
         "both of its reasons are substantive rather than notational. First, "
         "the coefficients differ in *kind*: an SSM's a and b are learned and "
         "then frozen (parameter-like), while f_t and i_t are recomputed from "
         "every token (variable-like), so the typed skeletons "
         "`?0:V = +(*(?1:P, ?2:V), *(?3:P, ?4:V))` and "
         "`?0:V = +(*(?1:V, ?2:V), *(?3:V, OUTER⟨?4:V, ?5:V⟩))` differ in "
         "their categories. Second, the drive term is not a vector but a "
         "rank-one matrix, which costs an extra call node and breaks the arity "
         "even at shape level, where categories are ignored. The honest summary "
         "is that the informal reading elides exactly the two things that "
         "distinguish the architectures, and the matcher declined to elide "
         "them.",
         ["Scalar gates per head, as in the reference mLSTM formulation",
          "Keys and values of matching dimensionality for the outer product",
          "Normalization of the retrieval, omitted here, needed in practice to "
          "keep the memory's scale bounded"],
         [BECK2024, MLSTM_KERNELS, SCHLAG2021, HOCHREITER1997],
         functionals=[OUTER_FN],
         failure_modes=[
             "Without the accompanying normalizer state the memory's magnitude "
             "grows with sequence length and retrieval saturates; the write "
             "equation alone is not a complete specification.",
             "The covariance reading suggests the memory is a statistic of the "
             "sequence, but the gates make it a *weighted* one with weights "
             "chosen by the model, so it estimates nothing in particular.",
             "Matrix memory is quadratic in head dimension, so the constant "
             "factor that linear-in-length buys can be lost outright at "
             "realistic widths."],
         inferential_links=links(
             special_case_of=["ml.recurrence.belief_state_update"],
             composed_with=["ml.recurrence.lstm_gate_activation",
                            "ml.recurrence.linear_ssm_state_update"]),
         keywords=["xLSTM", "mLSTM", "matrix memory", "covariance update",
                   "fast weights", "linear attention", "gating"],
         canonical_objects=["matrix memory", "key-value pair", "gate"]),

    # ---------------------------------------------------------------- 5 ----
    node("ml.recurrence.belief_state_update",
         "One-Step State Update (Belief / Dialogue-State Recurrence)",
         "model_specification", "assumed", "sequential_decision", "state_tracking",
         "b_t = U(b_(t-1), o_t)",
         "b_t = U\\!\\left(b_{t-1}, o_t\\right)",
         [{"form_id": "pomdp_belief", "notation_system": "measure_theoretic",
           "expression": "b_t(s') = eta * O(o_t | s') * sum_s T(s' | s, a) * b_(t-1)(s)",
           "scope_note": "The POMDP belief update: the concrete U when the model is a hidden Markov decision process"},
          {"form_id": "dialogue_state", "notation_system": "ascii",
           "expression": "B_t = U(B_(t-1), utterance_t)",
           "scope_note": "Dialogue state tracking: the state is a slot-value assignment and U is the tracker"},
          {"form_id": "llm_tracker", "notation_system": "ascii",
           "expression": "B_t = decode(LM(prompt(B_(t-1), utterance_t)))",
           "scope_note": "The generative-LLM tracker of the 2024 DST literature: U is a decoder call on a prompt built from the previous state"}],
         "opaque_binary_state_update",
         "STATENEXT = UPDATE(STATE, OBSERVATION)",
         [slot("STATENEXT", "variable", "next_state"),
          slot("STATE", "variable", "previous_state"),
          slot("OBSERVATION", "variable", "new_observation")],
         ["The Markov commitment: the new state depends on the past only "
          "through the previous state. That, and not the identity of U, is the "
          "content of the statement -- and it is the one thing the template "
          "genuinely records.",
          "U is opaque on purpose. Filling it in with an affine map plus a "
          "nonlinearity gives ml.recurrence.elman_rnn_hidden_state; with a "
          "fixed linear blend, ml.recurrence.linear_ssm_state_update; with a "
          "gated rank-one write, ml.recurrence.mlstm_matrix_memory_update; with "
          "Bayes' rule against an observation model, the POMDP belief update, "
          "which is probstat.probability.bayes_rule iterated.",
          "Argument order is fixed as (prior state, new observation) and must "
          "stay fixed: call arguments are ordered for the matcher, and U is not "
          "symmetric in any reading.",
          "The state space is unconstrained by the template. In dialogue state "
          "tracking it is a finite slot-value assignment; in a POMDP it is a "
          "distribution over latent states; in a neural sequence model it is a "
          "real vector. The archetype survives all three, which is the reason "
          "for having the node."],
         [sym("b_t", "variable", "next_state",
              "State after absorbing the t-th observation.", 1),
          sym("o_t", "variable", "new_observation",
              "Observation (utterance, token, measurement) at step t.", 1),
          sym("t", "index", "time_index", "Discrete turn or time index.", 0)],
         [EQ],
         "Tracking anything over time means carrying a state forward and "
         "revising it with each new observation.",
         "Included to test whether the corpus can express an *archetype* rather "
         "than an equation, and the answer is: it can state one, and the "
         "matcher can do nothing with it. Dialogue state tracking and digital "
         "twin networking are the two system-level concepts this corpus was "
         "asked to cover, and neither is a single equation; what they share "
         "with every recurrence above is exactly this shape, a state revised by "
         "an observation. The skeleton `?0:V = UPDATE⟨?1:V, ?2:V⟩` is now the "
         "fifth head in the graph carrying the two-argument opaque-composition "
         "shape `?0 = HEAD⟨?1, ?2⟩`, after morphology's CONCAT and REALIZE, "
         "information theory's CAPMAX and geospatial topology's MEET (in "
         "geotop.predicates.de9im_disjoint) -- five nodes, five heads, and no "
         "two of them twin at any level. That count is the "
         "point: docs/BACKLOG.md's proposed head-alias table has been motivated "
         "three times by corpora that could not adopt an existing head "
         "truthfully, and this is the fourth. The hand-written "
         "`generalizes` edges to the three concrete recurrences below are "
         "likewise unverifiable -- specialize.py cannot bind a call head to an "
         "operator tree -- so the most useful relation in this node is one the "
         "tooling takes on trust.",
         ["A state space fixed in advance, so that successive states are "
          "comparable objects",
          "Markov property: the update reads only the previous state and the "
          "new observation",
          "An initial state supplied by convention (empty slot assignment, "
          "prior belief, zero vector)"],
         [KAELBLING1998, YOUNG2013, WILLIAMS2016DSTC, XU2024DST, NIU2024DST,
          HONG2023DTN],
         functionals=[UPDATE_FN],
         failure_modes=[
             "The Markov assumption is a modelling choice that dialogue "
             "routinely violates; trackers that need turn history smuggle it "
             "into the state, at which point the state is not a state but a "
             "transcript.",
             "Digital twin networking (arXiv:2312.10631) is cited here as an "
             "instance of the same archetype -- a maintained model revised by "
             "telemetry -- and NOT as a node of its own, because the framework "
             "has no single governing equation to formalize. Writing one would "
             "have been invention, not citation.",
             "An opaque U makes every property that matters (contractivity, "
             "information retention, calibration) unstateable; the node buys "
             "generality by giving up all of them."],
         inferential_links=links(
             generalizes=["ml.recurrence.elman_rnn_hidden_state",
                          "ml.recurrence.linear_ssm_state_update",
                          "ml.recurrence.mlstm_matrix_memory_update"],
             composed_with=["probstat.probability.bayes_rule"]),
         keywords=["dialogue state tracking", "belief update", "POMDP",
                   "recurrence archetype", "digital twin", "head alias"],
         canonical_objects=["belief state", "slot-value assignment", "observation"]),

    # ---------------------------------------------------------------- 6 ----
    node("ml.optimization.gradient_descent_step",
         "Gradient Descent Step",
         "transformation", "derived", "optimization", "first_order_methods",
         "theta_(k+1) = theta_k - eta * g_k",
         "\\theta_{k+1} = \\theta_k - \\eta\\, g_k",
         [{"form_id": "full_gradient", "notation_system": "ascii",
           "expression": "theta_(k+1) = theta_k - eta * grad L(theta_k)",
           "scope_note": "Cauchy's original: the exact gradient of the objective"},
          {"form_id": "stochastic", "notation_system": "ascii",
           "expression": "theta_(k+1) = theta_k - eta_k * ghat_k",
           "scope_note": "Robbins-Monro form: an unbiased gradient estimate and a decaying step size"},
          {"form_id": "preconditioned", "notation_system": "matrix_notation",
           "expression": "theta_(k+1) = theta_k - eta * P_k * g_k",
           "scope_note": "Adam, Newton and natural gradient all live here; they differ only in P_k"},
          {"form_id": "ascent", "notation_system": "ascii",
           "expression": "theta_(k+1) = theta_k + eta * g_k",
           "scope_note": "Gradient ascent, for objectives to be maximized; the sign convention the family match level is designed to absorb"}],
         "state_minus_scaled_correction",
         "PARAMNEXT = PARAM - LEARNRATE*GRADIENT",
         [slot("PARAMNEXT", "variable", "updated_parameters"),
          slot("PARAM", "variable", "current_parameters"),
          slot("LEARNRATE", "parameter", "step_size"),
          slot("GRADIENT", "variable", "descent_direction")],
         ["The parameter vector occupies a *variable* slot on both sides. That "
          "is the honest reading -- it is the thing being changed, the state of "
          "the optimizer -- and it is exactly what keeps this node out of the "
          "affine family, whose corresponding slot is a fixed intercept.",
          "The step size is parameter-like and its sign is a convention: "
          "descent on L is ascent on -L. The family match level absorbs that "
          "sign, which is why the family skeleton "
          "`?0:V = +(?1:V, *(?2:P, ?3:V))` no longer carries the minus.",
          "Affine in the gradient at fixed step size, which is what makes the "
          "method's analysis tractable and what every preconditioned variant "
          "preserves: Adam, Newton and natural gradient all replace GRADIENT by "
          "a transformed direction and leave this skeleton alone.",
          "One step only. Convergence is a statement about the iteration and "
          "its objective (convexity, smoothness, step-size schedule), none of "
          "which the template can hold."],
         [sym("theta", "variable", "current_parameters",
              "Parameter vector before the step.", 1),
          sym("g", "variable", "descent_direction",
              "Gradient of the objective at the current parameters, or an "
              "unbiased estimate of it.", 1),
          sym("eta", "parameter", "step_size",
              "Learning rate; positive, and constant within one step.", 0),
          sym("k", "index", "iteration_index", "Iteration counter.", 0)],
         [EQ, SUB, MUL],
         "Move the parameters a small distance in the direction that most "
         "steeply decreases the objective.",
         "Prediction 4 was that sign absorption would place this node in the "
         "affine family, and it MISSED -- by exactly one slot category. The "
         "affine family skeleton is `?0:V = +(?1:P, *(?2:P, ?3:V))` "
         "(tangent-line linearization, CAPM, the Keynesian consumption "
         "function, probstat.transform.affine_location_scale); this node's "
         "family skeleton is `?0:V = +(?1:V, *(?2:P, ?3:V))`. The differing "
         "slot is the additive term: an affine map adds a fixed intercept, "
         "while gradient descent adds the current *state*. That is not a "
         "quibble -- it is the difference between a map and an iteration, and "
         "the matcher caught it where an informal reading ('descent is affine "
         "in the gradient') would not have. What did fire instead is more "
         "interesting: at shape level this node groups with "
         "chemistry.thermodynamics.gibbs_free_energy and "
         "helmholtz_free_energy, `?0 = +(?1, neg(*(?2, ?3)))`, and at typed "
         "level it twins ml.objective.kl_regularized_rl_objective exactly. "
         "'Quantity minus weighted penalty' turns out to be one skeleton "
         "spanning thermodynamics, optimization and alignment.",
         ["A differentiable objective at the current point",
          "Positive step size, small enough for the objective's smoothness",
          "For the stochastic form, an unbiased gradient estimate and a step-"
          "size schedule satisfying the Robbins-Monro conditions"],
         [CAUCHY1847, ROBBINS1951, RUMELHART1986, KINGMA2015],
         failure_modes=[
             "A single step says nothing about convergence; with a step size "
             "above 2/L for an L-smooth objective the iteration diverges while "
             "every individual step remains a valid instance of this equation.",
             "Non-convex objectives make 'the direction of steepest decrease' a "
             "local statement only, and the equation offers no warning that the "
             "point reached is a saddle.",
             "In the stochastic form the gradient is an estimate, so the step "
             "is a random variable; treating this deterministic equation as the "
             "description of SGD hides all of its variance."],
         inferential_links=links(
             composed_with=["ml.objective.token_cross_entropy_loss",
                            "ml.objective.kl_regularized_rl_objective",
                            "ml.adaptation.lora_low_rank_update"]),
         keywords=["gradient descent", "SGD", "learning rate", "optimization",
                   "Robbins-Monro", "sign absorption"],
         canonical_objects=["parameter vector", "gradient", "learning rate"]),

    # ---------------------------------------------------------------- 7 ----
    node("ml.policy.boltzmann_softmax_policy",
         "Boltzmann (Softmax) Policy",
         "definition", "formal", "policy_learning", "action_selection",
         "p_i = Z^(-1) * exp(-beta * E_i)",
         "p_i = Z^{-1} e^{-\\beta E_i}",
         [{"form_id": "softmax_scores", "notation_system": "ascii",
           "expression": "p_i = exp(z_i / tau) / sum_j exp(z_j / tau)",
           "scope_note": "The form written in every ML codebase; E_i = -z_i and beta = 1/tau"},
          {"form_id": "boltzmann_physics", "notation_system": "ascii",
           "expression": "p_i = exp(-E_i/(kB*T)) / Z",
           "scope_note": "The Gibbs measure; beta = 1/(kB*T) is the inverse temperature"},
          {"form_id": "logit", "notation_system": "ascii",
           "expression": "log(p_i) = -beta*E_i - log(Z)",
           "scope_note": "Log-linear form: the reason scores are called logits and the reason the normalizer is an additive constant on that scale"},
          {"form_id": "rl_policy", "notation_system": "ascii",
           "expression": "pi(a) = exp(Q(a)/tau) / sum_b exp(Q(b)/tau)",
           "scope_note": "Sutton and Barto's Boltzmann exploration policy over action values"},
          {"form_id": "rlhf_optimum", "notation_system": "ascii",
           "expression": "pi*(y|x) = piref(y|x) * exp(r(x,y)/beta) / Z(x)",
           "scope_note": "The maximizer of ml.objective.kl_regularized_rl_objective: the same measure, tilted by a reference policy"}],
         "normalized_exponential_tilt",
         "PROBABILITY = INVPARTITION * EXP(-(INVTEMPERATURE * ENERGY))",
         [slot("PROBABILITY", "variable", "outcome_probability"),
          slot("INVPARTITION", "constant", "normalizing_prefactor"),
          slot("INVTEMPERATURE", "parameter", "inverse_temperature"),
          slot("ENERGY", "variable", "state_energy")],
         ["The normalizer is a *prefactor*, not a term: it does not depend on "
          "the index the statement ranges over, which is what makes it a "
          "constant slot here even though it depends on the temperature and on "
          "the whole score vector. Writing it as Z^(-1) rather than as a "
          "division is the standard statistical-mechanics spelling and is what "
          "puts this node in the exponential family the corpus already has.",
          "The inverse temperature is parameter-like and its sign is a "
          "convention: energies with beta > 0 and scores with beta < 0 are the "
          "same one-parameter family, which is precisely what the family match "
          "level absorbs.",
          "Invariant to adding a constant to every energy: the shift cancels "
          "against the normalizer. Probabilities depend on energy *differences* "
          "only, which is why logits are identified up to a constant and why "
          "implementations may subtract the maximum before exponentiating.",
          "Two limits bracket the family: beta -> infinity concentrates all "
          "mass on the lowest-energy state (greedy), beta -> 0 gives the "
          "uniform distribution (pure exploration).",
          "Log-linear in the energy, which is the same statement as: the "
          "surprisal of an outcome is affine in its energy. That connects this "
          "node to infotheory.entropy.surprisal from the other direction."],
         [sym("p_i", "distribution", "outcome_probability",
              "Probability assigned to outcome (token, action, microstate) i.", 0),
          sym("E_i", "variable", "state_energy",
              "Energy of outcome i; the negative of its score or logit.", 0),
          sym("beta", "parameter", "inverse_temperature",
              "Inverse temperature, 1/tau; controls how sharply the "
              "distribution concentrates on low-energy outcomes.", 0),
          sym("Z", "constant", "normalizing_prefactor",
              "Partition function, the sum of exp(-beta*E_j) over all "
              "outcomes; constant with respect to the index i.", 0)],
         [EQ, MUL, NEG],
         "The probability of an outcome falls off exponentially in its energy, "
         "at a rate set by the inverse temperature, with a constant chosen so "
         "the probabilities sum to one.",
         "Prediction 3 was that this node would family-twin chemistry's "
         "Arrhenius factor by sign absorption. Against Arrhenius specifically "
         "it MISSED, and the reason is worth quoting: "
         "chemistry.kinetics.arrhenius_equation is "
         "`?0:V = *(?1:P, EXP⟨neg(*(?2:P, inv(*(?3:P, ?4:V))))⟩)` -- its "
         "denominator is an explicit product R*T, arity four -- while this node "
         "carries a single inverse-temperature slot, arity three. Chemistry "
         "keeps the gas constant visible; ML folds it into beta. Two spellings "
         "of one idea, and the matcher separates them. What FIRED instead is "
         "Arrhenius's sibling: this node typed-twins "
         "chemistry.kinetics.first_order_integrated_rate_law and "
         "economics.finance.present_value_continuous on "
         "`?0:V = *(?1:P, EXP⟨neg(*(?2:P, ?3:V))⟩)`, and at family level joins "
         "calculus.growth.exponential_growth_law and "
         "economics.finance.continuous_compounding as well -- a five-member, "
         "four-discipline group. The token-probability distribution of a "
         "language model, radioactive decay, discounting a cash flow and "
         "compound interest are one equation. Arrhenius is not lost either, "
         "merely demoted a level: scripts/specialize.py reports "
         "`ml.policy.boltzmann_softmax_policy >= "
         "chemistry.kinetics.arrhenius_equation` (looseness 3, via "
         "absorption+identity), the ENERGY slot absorbing the whole "
         "BARRIER/(GASCONST*TEMPERATURE) subtree and the inverse-temperature "
         "slot binding the multiplicative identity. Which is the right "
         "relationship after all -- Arrhenius is a Boltzmann factor with the "
         "energy measured in molar units -- reached at the specialization "
         "level rather than the twin level, exactly as happened to the "
         "state-space prediction. The spelling was chosen "
         "deliberately (beta rather than 1/tau, Z^(-1) rather than a "
         "division), so by docs/BACKLOG.md's proposed provenance flag this twin "
         "is `authored_to_match`, not emergent.",
         ["A finite or countable outcome set with a summable partition function",
          "Positive inverse temperature (a negative one reverses the "
          "preference order rather than scaling it)",
          "Energies finite; an infinite energy is an excluded outcome by "
          "convention"],
         [BOLTZMANN1877, LUCE1959, BRIDLE1990, SUTTON2018, BENGIO2003],
         functionals=[EXP_FN],
         constants=[{"symbol": "Z",
                     "description": "Partition function: the sum of "
                                    "exp(-beta*E_j) over outcomes. Constant "
                                    "with respect to the outcome index, which "
                                    "is the sense in which it is a constant "
                                    "here; it is a function of beta and of the "
                                    "score vector."}],
         failure_modes=[
             "Computing the normalizer requires the whole outcome set, so the "
             "equation is only cheap when that set is small; sampled softmax "
             "and noise-contrastive estimation exist because for a large "
             "vocabulary it is not.",
             "Exponentiating raw scores overflows; the shift-invariance noted "
             "in the invariants is what implementations exploit, and forgetting "
             "it is a numerical bug rather than a modelling one.",
             "Temperature is not a calibration: rescaling logits changes the "
             "distribution's sharpness but cannot fix a model whose energy "
             "ordering is wrong."],
         inferential_links=links(
             composed_with=["ml.objective.token_cross_entropy_loss",
                            "ml.objective.kl_regularized_rl_objective",
                            "infotheory.entropy.surprisal"]),
         keywords=["softmax", "Boltzmann distribution", "temperature", "logits",
                   "partition function", "Gibbs measure", "exploration"],
         canonical_objects=["probability distribution over tokens", "logit vector",
                            "partition function"]),

    # ---------------------------------------------------------------- 8 ----
    node("ml.objective.token_cross_entropy_loss",
         "Token Cross-Entropy Training Loss",
         "definition", "formal", "objectives", "likelihood",
         "L = -(1/N) * sum_i y_i * log(qhat_i)",
         "\\mathcal{L} = -\\frac{1}{N}\\sum_i y_i \\log \\hat q_i",
         [{"form_id": "one_hot", "notation_system": "ascii",
           "expression": "L = -(1/N) * sum_t log(qhat(token_t))",
           "scope_note": "With one-hot targets the inner sum collapses to the log-probability of the observed token: the standard next-token loss"},
          {"form_id": "perplexity", "notation_system": "ascii",
           "expression": "PPL = exp(L)",
           "scope_note": "Perplexity is the exponential of this loss in nats; the reporting convention, not a different quantity"},
          {"form_id": "kl_decomposition", "notation_system": "ascii",
           "expression": "L = H(y) + KL(y || qhat)",
           "scope_note": "Entropy of the data plus divergence from it; only the second term depends on the model, which is why minimizing either is the same problem"},
          {"form_id": "likelihood", "notation_system": "ascii",
           "expression": "L = -(1/N) * log Pr(corpus | model)",
           "scope_note": "Negative average log-likelihood: the loss is maximum likelihood, renamed"}],
         "negated_scaled_cross_log",
         "LOSS = -(BATCHSCALE * sum_i TARGET_i * LOG(PREDICTED_i))",
         [slot("LOSS", "variable", "objective_value"),
          slot("BATCHSCALE", "constant", "unit_scale_constant"),
          slot("TARGET_i", "variable", "true_weight"),
          slot("PREDICTED_i", "variable", "model_weight")],
         ["Two distinct distribution slots, target and prediction, where "
          "infotheory.entropy.shannon_entropy has one slot repeated. That "
          "single difference is the whole distinction between measuring your "
          "own uncertainty and paying for a model's, and the matcher keys on it "
          "directly: `LOG⟨?2:V⟩` against `LOG⟨?3:V⟩`.",
          "The 1/N batch average occupies a constant slot and is kept explicit. "
          "In information theory the same slot carries 1/ln 2 (choosing bits) "
          "and in physics.thermodynamics.gibbs_entropy it carries kB. Folding "
          "it away, as implementations do, would break the typed twin for a "
          "reason with no mathematical content.",
          "Linear in the target distribution, so an average over sampled "
          "positions is an unbiased estimate of the population quantity. That "
          "is why this and not KL divergence is the loss: the term KL adds "
          "does not depend on the model at all.",
          "Bounded below by the entropy of the target distribution, with "
          "equality exactly when the model matches it. The floor is the data's "
          "irreducible uncertainty, which is why a perplexity of 1 is not a "
          "goal."],
         [sym("L", "statistic", "objective_value",
              "Average cross-entropy over the scored positions, in nats.", 0),
          sym("y_i", "distribution", "true_weight",
              "Target probability of vocabulary entry i; one-hot in ordinary "
              "next-token training, soft under label smoothing or "
              "distillation.", 0),
          sym("qhat_i", "distribution", "model_weight",
              "Model's predicted probability for vocabulary entry i; strictly "
              "positive.", 0),
          sym("N", "constant", "count", "Number of scored positions.", 0)],
         [EQ, MUL, NEG, SUM, EXPECT],
         "The training loss is the average surprisal the model assigns to the "
         "tokens that actually occurred.",
         "The node that closes the loop between this corpus and "
         "data/information_theory, and it is authored to do so. Its typed "
         "skeleton `?0:V = neg(*(?1:P, sum⟨*(?2:V, LOG⟨?3:V⟩)⟩))` is shared "
         "character for character with infotheory.divergence.cross_entropy, and "
         "the two nodes now carry reciprocal `equivalent_to` edges written into "
         "both corpora, because the claim is identity rather than resemblance: "
         "the loss minimized by every language model in production is Shannon's "
         "cross-entropy with the empirical distribution in the first argument. "
         "Two authoring decisions made the twin possible and both are "
         "declarative rather than cosmetic: keeping the 1/N average in the "
         "scale slot that information theory reserves for the base constant, "
         "and keeping the target and prediction as separate slots rather than "
         "collapsing the one-hot case. By docs/BACKLOG.md's proposed "
         "provenance flag this twin is `authored_to_match` -- it belongs with "
         "diffgeo.stokes.stokes_zero_form_case and "
         "infotheory.mutualinfo.entropy_inclusion_exclusion, not with the "
         "emergent ones, and pooling the three counts would overstate what the "
         "matcher discovered.",
         ["Predicted probabilities strictly positive wherever the target is",
          "Target and prediction distributions over the same vocabulary",
          "The same logarithm base throughout an argument (nats here; "
          "perplexity conventions assume it)"],
         [SHANNON1948, GOOD1952, BRIDLE1990, BENGIO2003, GOODFELLOW2016],
         functionals=[LOG_FN],
         constants=[BATCHSCALE_CONST],
         index_sets=[IDX_VOCAB],
         failure_modes=[
             "A zero predicted probability on an observed token makes the loss "
             "infinite, which is why implementations clip, smooth or work in "
             "log space throughout.",
             "The loss is an average over positions and hides its own "
             "distribution: a model can improve mean cross-entropy while "
             "getting worse on every rare token.",
             "Cross-entropy is not a distance. It does not vanish at a perfect "
             "model -- it equals the data's entropy there -- so a nonzero "
             "training loss is not evidence of underfitting."],
         inferential_links=links(
             equivalent_to=["infotheory.divergence.cross_entropy"],
             composed_with=["infotheory.entropy.surprisal",
                            "ml.policy.boltzmann_softmax_policy",
                            "ml.optimization.gradient_descent_step"]),
         keywords=["cross-entropy", "log loss", "perplexity",
                   "maximum likelihood", "next-token prediction"],
         canonical_objects=["target distribution", "predicted distribution",
                            "vocabulary"]),

    # ---------------------------------------------------------------- 9 ----
    node("ml.objective.kl_regularized_rl_objective",
         "KL-Regularized Reinforcement Learning Objective",
         "definition", "formal", "alignment", "regularized_objectives",
         "J = R - beta * D",
         "J = \\mathbb{E}_{\\pi}[r] - \\beta\\, D_{KL}(\\pi \\,\\|\\, \\pi_{ref})",
         [{"form_id": "expanded", "notation_system": "ascii",
           "expression": "J(pi) = E_(y~pi)[r(x,y)] - beta * KL(pi(.|x) || piref(.|x))",
           "scope_note": "The RLHF objective as written by Ziegler et al. and Ouyang et al."},
          {"form_id": "per_token_penalty", "notation_system": "ascii",
           "expression": "rtilde(x,y) = r(x,y) - beta * log(pi(y|x)/piref(y|x))",
           "scope_note": "The implementation form: the penalty folded into the reward, token by token"},
          {"form_id": "optimal_policy", "notation_system": "ascii",
           "expression": "pi*(y|x) = piref(y|x) * exp(r(x,y)/beta) / Z(x)",
           "scope_note": "The closed-form maximizer: a Boltzmann tilt of the reference policy, which is what DPO inverts"},
          {"form_id": "free_energy", "notation_system": "ascii",
           "expression": "-J = F = U - T*S",
           "scope_note": "The thermodynamic reading: beta is a temperature and the objective is (minus) a variational free energy"}],
         "value_minus_weighted_penalty",
         "OBJECTIVE = EXPECTEDREWARD - KLWEIGHT*DIVERGENCE",
         [slot("OBJECTIVE", "variable", "objective_value"),
          slot("EXPECTEDREWARD", "variable", "utility_term"),
          slot("KLWEIGHT", "parameter", "penalty_weight"),
          slot("DIVERGENCE", "variable", "penalty_term")],
         ["A scalarized two-objective problem: maximize reward, stay near the "
          "reference. The penalty weight is parameter-like and traces out the "
          "Pareto frontier as it varies, so the equation is really a family of "
          "objectives indexed by one number.",
          "Because the penalty is a KL divergence and not an arbitrary "
          "regularizer, the maximization has a closed-form solution -- the "
          "Boltzmann tilt in the equivalent forms -- and the whole of DPO "
          "follows from inverting it. The choice of penalty is doing far more "
          "work than the shape of the objective suggests.",
          "The penalty is non-negative and vanishes exactly at the reference "
          "policy (infotheory.divergence.gibbs_inequality), so the objective is "
          "bounded above by the best achievable reward and the reference policy "
          "is always feasible.",
          "The direction of the divergence is fixed: KL(pi || piref), "
          "mode-seeking. Reversing it is a different objective with different "
          "optima, and nothing in this skeleton records the asymmetry -- it "
          "lives in infotheory.divergence.kl_divergence's slot reuse pattern."],
         [sym("J", "statistic", "objective_value",
              "Regularized objective to be maximized.", 0),
          sym("r", "variable", "utility_term",
              "Expected reward of the current policy.", 0),
          sym("D", "statistic", "penalty_term",
              "KL divergence from the current policy to the reference.", 0),
          sym("beta", "parameter", "penalty_weight",
              "Regularization strength; equivalently a temperature.", 0)],
         [EQ, SUB, MUL, EXPECT],
         "Maximize reward, but pay a price proportional to how far the policy "
         "has drifted from the model you started with.",
         "The node where the corpus's chemistry pays off. Its shape skeleton "
         "`?0 = +(?1, neg(*(?2, ?3)))` is shared with "
         "chemistry.thermodynamics.gibbs_free_energy (G = H - T*S) and "
         "chemistry.thermodynamics.helmholtz_free_energy (A = U - T*S), and the "
         "correspondence is exact rather than decorative: this objective IS a "
         "variational free energy, its maximizer IS a Boltzmann distribution "
         "(the node ml.policy.boltzmann_softmax_policy carries), and the slot "
         "that separates it from the thermodynamic version is the one holding "
         "beta -- which in that reading *is* the temperature. The twin stops at "
         "shape rather than typed for a single reason: chemistry declares "
         "TEMPERATURE a variable, since a chemist varies it, while an alignment "
         "researcher fixes beta as a hyperparameter, so it is declared a "
         "parameter here. Both are honest about their own practice, and the "
         "one-category gap is the entire distance between the fields on this "
         "equation. At typed level the node twins "
         "ml.optimization.gradient_descent_step instead: 'quantity minus "
         "weighted penalty' and 'state minus scaled gradient' are the same "
         "skeleton, which is a fair description of what KL regularization does "
         "to a policy gradient.",
         ["A reference policy with support covering the trained policy, else "
          "the divergence is infinite",
          "Non-negative penalty weight; beta = 0 recovers unregularized RL",
          "Reward defined on the same outputs the policy generates"],
         [ZIEGLER2019, STIENNON2020, OUYANG2022, LEVINE2018, TODOROV2007],
         failure_modes=[
             "The penalty constrains drift from the reference, not truth: a "
             "policy can satisfy it perfectly and still be optimizing a "
             "misspecified reward, which is what reward hacking looks like from "
             "inside this equation.",
             "Estimated KL in practice is a per-token Monte Carlo estimate that "
             "can be negative for a finite sample, so the non-negativity the "
             "invariants rely on is a population statement.",
             "Tuning beta trades alignment against capability along a frontier "
             "the equation describes but does not locate; there is no principled "
             "value and reported ones are task-specific."],
         inferential_links=links(
             composed_with=["infotheory.divergence.kl_divergence",
                            "ml.policy.boltzmann_softmax_policy",
                            "ml.preference.dpo_preference_loss",
                            "ml.optimization.gradient_descent_step"]),
         keywords=["RLHF", "KL regularization", "free energy", "alignment",
                   "reference policy", "control as inference"],
         canonical_objects=["policy", "reference policy", "reward model"]),

    # --------------------------------------------------------------- 10 ----
    node("ml.policy.policy_probability_ratio",
         "Policy Probability Ratio (Importance Weight)",
         "definition", "formal", "policy_learning", "off_policy_correction",
         "rho = pi_new / pi_old",
         "\\rho_t(\\theta) = \\frac{\\pi_\\theta(a_t \\mid s_t)}{\\pi_{\\theta_{old}}(a_t \\mid s_t)}",
         [{"form_id": "log_form", "notation_system": "ascii",
           "expression": "log(rho) = log(pi_new) - log(pi_old)",
           "scope_note": "The form implementations use, and the quantity DPO's loss differences are built from"},
          {"form_id": "importance_sampling", "notation_system": "ascii",
           "expression": "E_(a~pi_new)[f(a)] = E_(a~pi_old)[rho * f(a)]",
           "scope_note": "What the ratio is for: reweighting samples drawn under the old policy"},
          {"form_id": "surrogate", "notation_system": "ascii",
           "expression": "L = E[rho * A]",
           "scope_note": "The unclipped surrogate objective; PPO's contribution is what it does to this expression, not the expression itself"}],
         "ratio_rate",
         "RATIO = POLICYNEW / POLICYOLD",
         [slot("RATIO", "variable", "relative_measure"),
          slot("POLICYNEW", "variable", "numerator_measure"),
          slot("POLICYOLD", "variable", "denominator_measure")],
         ["Both operands are variable-like: two probabilities of the same event "
          "under two different distributions. Neither is a fixed reference "
          "constant, which is what distinguishes this from a normalization.",
          "Equals 1 exactly when the policies agree on the sampled action, so "
          "the deviation from unity, not the value, is the signal. Every "
          "trust-region method is a statement about how far from 1 this "
          "quantity may travel.",
          "Positive by construction, and its logarithm is the pointwise "
          "log-likelihood ratio whose expectation under the new policy is a KL "
          "divergence -- the bridge from this node to "
          "ml.objective.kl_regularized_rl_objective.",
          "Unbounded above: a rare action under the old policy can produce an "
          "arbitrarily large weight, which is the variance problem that "
          "motivates clipping."],
         [sym("rho", "statistic", "relative_measure",
              "Importance weight for the sampled action.", 0),
          sym("pi_new", "distribution", "numerator_measure",
              "Probability of the sampled action under the current policy.", 0),
          sym("pi_old", "distribution", "denominator_measure",
              "Probability of the same action under the behaviour policy that "
              "generated the sample.", 0)],
         [EQ, DIV],
         "How much more likely the updated policy is to take the action that "
         "was actually taken, relative to the policy that took it.",
         "The most ordinary equation in the corpus and it lands in the largest "
         "cross-discipline family available. Its typed skeleton "
         "`?0:V = *(?1:V, inv(?2:V))` is shared with "
         "calculus.differentiation.average_rate_of_change, "
         "physics.kinematics.average_speed, physics.materials.mass_density, "
         "chemistry.solutions.molarity_definition and "
         "economics.microeconomics.price_elasticity_of_demand -- five "
         "disciplines, six nodes, one skeleton. Nothing was authored to make "
         "this happen; a ratio of two quantities of the same kind is a density, "
         "and the importance weight is the density of one policy with respect "
         "to another in exactly the sense that molarity is the density of "
         "solute in solvent. It is also the corpus's cleanest reminder that "
         "twin groups are cheap at the bottom of the structural hierarchy: "
         "membership in this family says the quantity is a ratio and nothing "
         "more, which is why the report should weight it far below the GRPO / "
         "z-score twin.",
         ["Both policies assign positive probability to the sampled action",
          "The same action and state in numerator and denominator",
          "Samples drawn under the denominator's policy for the importance-"
          "sampling reading to be valid"],
         [SCHULMAN2015, SCHULMAN2017, KAKADE2002, WILLIAMS1992],
         failure_modes=[
             "Importance weights have unbounded variance when the policies "
             "diverge, so the estimator this ratio defines can be arbitrarily "
             "bad long before it looks wrong.",
             "The ratio is per-token in language-model practice but the "
             "theory is per-trajectory; products of per-token ratios over long "
             "sequences underflow or explode, and implementations quietly "
             "differ on which they use."],
         inferential_links=links(
             composed_with=["ml.policy.ppo_clipped_surrogate",
                            "ml.preference.dpo_preference_loss",
                            "infotheory.divergence.kl_divergence"]),
         keywords=["importance sampling", "probability ratio", "PPO", "TRPO",
                   "off-policy", "density"],
         canonical_objects=["policy", "action", "importance weight"]),

    # --------------------------------------------------------------- 11 ----
    node("ml.policy.ppo_clipped_surrogate",
         "PPO Clipped Surrogate Objective",
         "approximation", "empirical", "policy_learning", "trust_region",
         "L = MINOF(rho * A, clip(rho, 1-eps, 1+eps) * A)",
         "L^{CLIP} = \\min\\!\\left(\\rho_t A_t,\\ \\mathrm{clip}(\\rho_t, 1-\\epsilon, 1+\\epsilon) A_t\\right)",
         [{"form_id": "expectation", "notation_system": "ascii",
           "expression": "L = E_t[min(rho_t * A_t, clip(rho_t, 1-eps, 1+eps) * A_t)]",
           "scope_note": "Schulman et al.'s objective as published; the expectation over sampled timesteps is omitted from the template"},
          {"form_id": "piecewise", "notation_system": "ascii",
           "expression": "L = rho*A if A>0 and rho<1+eps, or A<0 and rho>1-eps; else the clipped constant",
           "scope_note": "The mechanism spelled out: the objective goes flat once the update is large in the direction the advantage favours"},
          {"form_id": "trust_region", "notation_system": "ascii",
           "expression": "maximize E[rho*A] subject to KL(pi_old || pi_new) <= delta",
           "scope_note": "TRPO's constrained problem, which this objective approximates with a first-order penalty instead of a constraint"}],
         "clipped_pessimistic_surrogate",
         "SURROGATE = MINOF(RATIO*ADVANTAGE, CLIPCALL(RATIO, LOWERBOUND, UPPERBOUND)*ADVANTAGE)",
         [slot("SURROGATE", "variable", "objective_value"),
          slot("RATIO", "variable", "importance_weight"),
          slot("ADVANTAGE", "variable", "advantage_estimate"),
          slot("LOWERBOUND", "parameter", "clip_floor"),
          slot("UPPERBOUND", "parameter", "clip_ceiling")],
         ["The ratio slot occurs twice -- once bare, once inside the clamp -- "
          "and the advantage slot occurs twice, once in each branch. That "
          "double reuse is the entire mechanism: the objective compares a "
          "quantity with a clamped copy of itself and takes the pessimistic "
          "one.",
          "MINOF is commutative in every model and the matcher cannot know it, "
          "because call arguments are ordered (docs/BACKLOG.md). The order "
          "fixed here is unclipped term first, clipped term second, and "
          "anything added later must keep it or the skeletons will not meet.",
          "CLIPCALL is opaque, and what it hides is the whole point of the "
          "method. The clamp is the identity inside the interval and constant "
          "outside it, so the gradient of the second branch vanishes once the "
          "ratio leaves the trust region; the template records that the bounds "
          "are arguments and nothing about what happens at them. The grammar "
          "has no piecewise or conditional form, so this is the most that can "
          "honestly be written.",
          "The bounds are symmetric around 1 in practice (1-eps, 1+eps) but are "
          "kept as two independent parameter slots, because asymmetric clipping "
          "is a live variant and nothing in the objective requires symmetry.",
          "The minimum makes the surrogate a lower bound on the unclipped "
          "objective, which is why the method is described as pessimistic; the "
          "bound is what licenses taking several gradient steps on one batch."],
         [sym("L", "statistic", "objective_value",
              "Clipped surrogate objective at one sampled timestep.", 0),
          sym("rho", "statistic", "importance_weight",
              "Policy probability ratio; see ml.policy.policy_probability_ratio.", 0),
          sym("A", "variable", "advantage_estimate",
              "Advantage estimate for the sampled action.", 0),
          sym("eps", "parameter", "clip_halfwidth",
              "Clipping half-width, typically 0.1 to 0.3.", 0)],
         [EQ, MUL],
         "Take the smaller of the plain importance-weighted advantage and the "
         "same thing with the weight clamped near one, so that the update stops "
         "paying off once it moves the policy too far.",
         "Where this corpus meets the grammar's ceiling, in the same way "
         "infotheory.channel.channel_capacity did. Two constructs have no "
         "form in the template language: a minimum (identifiers beginning "
         "`min_` are silently parsed as prefix big-operators, so even the "
         "natural spelling is unavailable) and a clamp (there is no piecewise "
         "or conditional syntax at all). Both are written as opaque calls, "
         "which parse cleanly and record the dependency structure while making "
         "the objective's actual mechanism -- flat gradient outside the trust "
         "region -- invisible. The cost is concrete and can be stated exactly: "
         "the node is a singleton at every match level, it cannot be compared "
         "with TRPO's constrained problem or with any other trust-region "
         "method, and the relationship to ml.policy.policy_probability_ratio "
         "(whose defined quantity fills the RATIO slot twice) is expressible "
         "only as a hand-written `composed_with` edge. Recorded rather than "
         "worked around: inventing a smooth surrogate that happened to parse "
         "would have made the node twin something and would have been a "
         "different equation.",
         ["An advantage estimate available for the sampled action",
          "Bounds straddling 1, so that the unclipped ratio is admissible near "
          "the old policy",
          "Samples drawn under the old policy within the current update window"],
         [SCHULMAN2017, SCHULMAN2015, KAKADE2002, OUYANG2022],
         functionals=[MINOF_FN, CLIPCALL_FN],
         failure_modes=[
             "Clipping bounds the objective, not the policy update: several "
             "gradient steps on one batch can still move the policy far outside "
             "the interval the bounds name, since the clip only removes the "
             "incentive, not the ability.",
             "The objective is not a lower bound on the true return, only on "
             "the surrogate, so its guarantees are much weaker than TRPO's "
             "monotonic-improvement statement it is often said to inherit.",
             "With a negative advantage the two branches swap roles, and "
             "implementations that clip symmetrically without checking the sign "
             "get the pessimism backwards."],
         inferential_links=links(
             composed_with=["ml.policy.policy_probability_ratio",
                            "ml.preference.grpo_group_relative_advantage",
                            "ml.objective.kl_regularized_rl_objective"]),
         keywords=["PPO", "clipping", "trust region", "surrogate objective",
                   "grammar limit", "opaque call"],
         canonical_objects=["policy", "advantage", "clipping interval"]),

    # --------------------------------------------------------------- 12 ----
    node("ml.preference.dpo_preference_loss",
         "Direct Preference Optimization Loss",
         "definition", "derived", "alignment", "preference_learning",
         "L = -log(sigma(beta * (d_w - d_l)))",
         "\\mathcal{L}_{DPO} = -\\log\\sigma\\!\\left(\\beta\\left(\\log\\frac{\\pi_\\theta(y_w|x)}{\\pi_{ref}(y_w|x)} - \\log\\frac{\\pi_\\theta(y_l|x)}{\\pi_{ref}(y_l|x)}\\right)\\right)",
         [{"form_id": "expanded", "notation_system": "ascii",
           "expression": "L = -log(sigma(beta*log(pi(y_w|x)/piref(y_w|x)) - beta*log(pi(y_l|x)/piref(y_l|x))))",
           "scope_note": "The published form: each d is a log-ratio of the trained policy to the reference on one completion"},
          {"form_id": "implicit_reward", "notation_system": "ascii",
           "expression": "rhat(x,y) = beta * log(pi(y|x)/piref(y|x)) + beta*log(Z(x))",
           "scope_note": "The reparameterization the derivation turns on: inverting the KL-regularized optimum makes the policy its own reward model"},
          {"form_id": "bradley_terry", "notation_system": "ascii",
           "expression": "Pr(y_w > y_l) = sigma(rhat(x,y_w) - rhat(x,y_l))",
           "scope_note": "Bradley-Terry: the loss is the negative log-likelihood of the observed preference under this model"},
          {"form_id": "logsigmoid", "notation_system": "ascii",
           "expression": "L = -logsigmoid(beta*(d_w - d_l))",
           "scope_note": "The numerically stable spelling used in implementations; one function, not a log of a sigmoid, to avoid underflow"}],
         "negated_log_of_squashed_difference",
         "LOSS = -(LOG(SIGMOID(BETA * (LOGRATIOCHOSEN - LOGRATIOREJECTED))))",
         [slot("LOSS", "variable", "objective_value"),
          slot("BETA", "parameter", "sharpness"),
          slot("LOGRATIOCHOSEN", "variable", "preferred_log_ratio"),
          slot("LOGRATIOREJECTED", "variable", "rejected_log_ratio")],
         ["The two log-ratio slots enter only through their difference, so "
          "anything added to both cancels. That is the reparameterization "
          "invariance that lets DPO dispense with the partition function Z(x) "
          "which ml.objective.kl_regularized_rl_objective's optimal policy "
          "carries -- the intractable term is common to both completions and "
          "subtracts out.",
          "Written as LOG(SIGMOID(...)) rather than as a single LOGSIGMOID "
          "head, deliberately: the decomposition is what makes the node's "
          "relationship to infotheory.entropy.surprisal visible, since "
          "-LOG(p) with p a probability is a surprisal and SIGMOID's codomain "
          "is exactly the probabilities. Implementations use the fused form for "
          "numerical reasons only.",
          "Beta is parameter-like and is the same beta as in the KL-regularized "
          "objective this loss is derived from; it sets how sharply a given "
          "log-ratio gap is converted into a preference probability.",
          "The loss is the negative log-likelihood of one observed pairwise "
          "preference under a Bradley-Terry model whose latent scores are the "
          "implicit rewards. Nothing about it is specific to language: it is "
          "logistic regression on preference pairs, with the design matrix "
          "supplied by the policy itself."],
         [sym("L", "statistic", "objective_value",
              "Loss for one preference pair.", 0),
          sym("beta", "parameter", "sharpness",
              "Inverse temperature inherited from the KL-regularized objective "
              "this loss is derived from.", 0),
          sym("d_w", "variable", "preferred_log_ratio",
              "Log-ratio of trained to reference policy on the preferred "
              "completion.", 0),
          sym("d_l", "variable", "rejected_log_ratio",
              "Log-ratio of trained to reference policy on the rejected "
              "completion.", 0)],
         [EQ, MUL, SUB, NEG],
         "Push up the policy's log-probability of the preferred completion "
         "relative to the rejected one, measured against a frozen reference, "
         "and score the result as the log-likelihood of the human's choice.",
         "A singleton at every match level, and instructive about why. The "
         "closest thing in the graph is infotheory.entropy.surprisal, "
         "`?0:V = neg(LOG⟨?1:V⟩)`, and the reading is exact -- SIGMOID's output "
         "is the Bradley-Terry probability that the annotator prefers the "
         "chosen completion, so this loss IS the surprisal of the observed "
         "preference, and DPO is maximum likelihood on preference data. The "
         "matcher cannot see it because surprisal's argument is a bare slot "
         "while this node's is a two-level call tree, and "
         "scripts/specialize.py, which exists precisely to bind a slot to a "
         "subtree, drops the match: its filter reports only bindings that used "
         "absorption or an identity element, and this one is a plain slot "
         "binding. That is the suppression docs/BACKLOG.md already records "
         "twice from the topology corpora, hit a third time here on the "
         "relation the node most wants stated. KTO (Ethayarajh et al. 2024) "
         "and ORPO (Hong et al. 2024) belong beside this node and are cited "
         "rather than formalized: KTO's value function is a piecewise "
         "prospect-theoretic transform with a reference point, and ORPO's "
         "odds-ratio penalty is a log of a ratio of odds -- both need "
         "conditional or nested-ratio syntax the grammar does not have, and "
         "forcing either into an opaque call would have added a head and no "
         "structure.",
         ["A pairwise preference dataset with a designated preferred completion",
          "A frozen reference policy with positive probability on both "
          "completions",
          "Bradley-Terry preference model, i.e. preferences depend on a latent "
          "scalar score difference only",
          "Positive beta"],
         [RAFAILOV2023, BRADLEY1952, ZIEGLER2019, ETHAYARAJH2024, HONG2024ORPO],
         functionals=[LOG_FN, SIGMOID_LINK_FN],
         failure_modes=[
             "Minimizing this loss can decrease the probability of the "
             "preferred completion outright, as long as the rejected one falls "
             "faster; the objective constrains the difference, not the levels.",
             "The derivation assumes the reference policy is the KL-regularized "
             "optimum's reference and that preferences are Bradley-Terry; under "
             "noisy or intransitive human labels neither holds and the implicit "
             "reward is not identified.",
             "Written as LOG(SIGMOID(x)) it underflows for moderately negative "
             "x; the fused logsigmoid in the equivalent forms is not an "
             "optimization but a correctness requirement in floating point."],
         inferential_links=links(
             composed_with=["ml.objective.kl_regularized_rl_objective",
                            "ml.policy.policy_probability_ratio",
                            "infotheory.entropy.surprisal"]),
         keywords=["DPO", "preference optimization", "Bradley-Terry",
                   "implicit reward", "log-ratio", "KTO", "ORPO"],
         canonical_objects=["preference pair", "reference policy",
                            "implicit reward"]),

    # --------------------------------------------------------------- 13 ----
    node("ml.preference.grpo_group_relative_advantage",
         "GRPO Group-Relative Advantage",
         "estimator", "empirical", "alignment", "advantage_estimation",
         "A_i = (r_i - mean(r)) / sd(r)",
         "A_i = \\frac{r_i - \\mathrm{mean}(\\mathbf{r})}{\\mathrm{std}(\\mathbf{r})}",
         [{"form_id": "group_form", "notation_system": "ascii",
           "expression": "A_i = (r_i - (1/G)*sum_j r_j) / sqrt((1/G)*sum_j (r_j - rbar)^2)",
           "scope_note": "Shao et al.'s definition with the group statistics written out; G is the number of sampled completions per prompt"},
          {"form_id": "centered_only", "notation_system": "ascii",
           "expression": "A_i = r_i - mean(r)",
           "scope_note": "The mean-only variant several later implementations prefer, on the grounds that dividing by the group standard deviation biases the gradient"},
          {"form_id": "baseline", "notation_system": "ascii",
           "expression": "A = r - b",
           "scope_note": "The classical variance-reduction baseline of REINFORCE; the group mean is a baseline estimated from the sample itself"}],
         "center_scale_map",
         "ADVANTAGE = (REWARD - MEANREWARD)/STDREWARD",
         [slot("ADVANTAGE", "variable", "standardized_variable"),
          slot("REWARD", "variable", "raw_variable"),
          slot("MEANREWARD", "parameter", "location"),
          slot("STDREWARD", "parameter", "positive_scale")],
         ["The location and scale slots are parameter-like: within the "
          "standardization of one group they are fixed numbers, applied "
          "identically to every member. They are also *estimated from the same "
          "group*, which makes this a studentization rather than a z-score in "
          "the strict sense -- the honest wrinkle behind the twin, recorded "
          "here rather than hidden.",
          "The scale slot must be strictly positive, which fails exactly when "
          "the group's rewards are all equal; implementations add a small "
          "epsilon, and the degenerate case is the one where the group carries "
          "no learning signal at all.",
          "Invariant to any affine relabelling of the reward: adding a constant "
          "to every reward or multiplying all of them leaves the advantage "
          "unchanged. That is why GRPO tolerates uncalibrated reward models, "
          "and it is the same invariance a z-score has by construction.",
          "The advantages within a group sum to zero and have unit sample "
          "variance, so the group supplies its own baseline; no learned value "
          "network appears anywhere, which is the whole computational argument "
          "for the method.",
          "Slot ids avoid the `sum_ prod_ lim_ max_ min_` prefixes "
          "(docs/BACKLOG.md); the natural name `MEAN_REWARD` would have been "
          "fine but `MIN_REWARD` in a sibling node would not."],
         [sym("A_i", "statistic", "standardized_variable",
              "Advantage assigned to the i-th sampled completion.", 0),
          sym("r_i", "random_variable", "raw_variable",
              "Reward of the i-th sampled completion for a given prompt.", 0),
          sym("rbar", "parameter", "location",
              "Mean reward over the sampled group.", 0),
          sym("s", "parameter", "positive_scale",
              "Standard deviation of the rewards over the sampled group; "
              "strictly positive.", 0),
          sym("G", "constant", "group_size",
              "Number of completions sampled per prompt.", 0)],
         [EQ, SUB, DIV],
         "Score each sampled completion by how many group standard deviations "
         "its reward sits above the group's mean.",
         "The flagship prediction of this corpus, registered before the matcher "
         "was run and FIRED exactly: this node and "
         "probstat.transform.z_standardization share "
         "`?0:V = *(+(?1:V, neg(?2:P)), inv(?3:P))` character for character at "
         "typed level, and no notation was adopted to arrange it -- GRPO's "
         "advantage was written the way Shao et al. write it and the "
         "statistics node was written years of corpus-time earlier for a "
         "different purpose. The claim the twin certifies is small and exact: "
         "the advantage estimator at the centre of the training recipe behind "
         "recent reasoning models is a z-score, with the population mean and "
         "standard deviation replaced by group sample statistics. Everything "
         "that follows about it follows from that -- affine invariance of the "
         "reward scale, zero-sum advantages within a group, degeneracy when the "
         "group agrees, and the known bias from estimating the scale on the "
         "same sample being standardized. It is also the one twin in this "
         "corpus that is unambiguously `emergent` rather than "
         "`authored_to_match`, which is why the report should weight it above "
         "the cross-entropy twin next door.",
         ["Two or more sampled completions per prompt",
          "Non-degenerate group rewards, i.e. strictly positive sample standard "
          "deviation",
          "Rewards comparable within a group (they need not be comparable "
          "across prompts, and the standardization is what buys that)"],
         [SHAO2024, DEEPSEEK2025, WILLIAMS1992, SUTTON2018],
         failure_modes=[
             "The scale is estimated from the very sample it standardizes, so "
             "the resulting advantages are biased and the gradient is not the "
             "policy gradient of any fixed objective; the mean-only variant in "
             "the equivalent forms exists for this reason.",
             "A group whose rewards are all equal produces a zero denominator "
             "and no signal, which for binary correctness rewards is the "
             "common case on problems that are always solved or never solved.",
             "Standardization discards the reward's magnitude, so a group that "
             "is uniformly bad and a group that is uniformly good yield "
             "identical advantages; the method cannot express that a whole "
             "group was worthless."],
         inferential_links=links(
             composed_with=["probstat.transform.z_standardization",
                            "ml.policy.ppo_clipped_surrogate",
                            "ml.objective.kl_regularized_rl_objective"]),
         keywords=["GRPO", "advantage", "z-score", "standardization",
                   "group relative", "baseline", "variance reduction"],
         canonical_objects=["reward", "sampled group", "advantage"]),

    # --------------------------------------------------------------- 14 ----
    node("ml.adaptation.lora_low_rank_update",
         "LoRA Low-Rank Weight Update",
         "transformation", "assumed", "adaptation", "parameter_efficiency",
         "W = W0 + (alpha/r) * B * A",
         "W = W_0 + \\frac{\\alpha}{r} B A",
         [{"form_id": "forward", "notation_system": "matrix_notation",
           "expression": "h = W0 * x + (alpha/r) * B * (A * x)",
           "scope_note": "The form actually evaluated: the adapter is applied as two thin matrix products, never materializing the update"},
          {"form_id": "delta", "notation_system": "matrix_notation",
           "expression": "dW = B * A, with rank(dW) <= r",
           "scope_note": "The rank constraint is the whole hypothesis: adaptation lives in a low-dimensional subspace"},
          {"form_id": "dora", "notation_system": "matrix_notation",
           "expression": "W = m * (W0 + B*A) / norm(W0 + B*A)",
           "scope_note": "DoRA (Liu et al. 2024): the same update, then decomposed into magnitude and direction and rescaled"},
          {"form_id": "pissa", "notation_system": "matrix_notation",
           "expression": "W = Wresidual + B*A, with B,A initialized from the principal singular vectors of W0",
           "scope_note": "PiSSA (Meng et al. 2024): identical equation, different initialization of the same slots"},
          {"form_id": "loftq", "notation_system": "matrix_notation",
           "expression": "W approx quantize(W0) + B*A, with B,A chosen to absorb the quantization error",
           "scope_note": "LoftQ (Li et al. 2023): the frozen term is quantized and the adapter initialized to compensate"}],
         "frozen_base_plus_scaled_factorization",
         "WEIGHT = WEIGHTFROZEN + SCALING*LOWRANKB*LOWRANKA",
         [slot("WEIGHT", "variable", "effective_weight"),
          slot("WEIGHTFROZEN", "parameter", "frozen_base"),
          slot("SCALING", "parameter", "adapter_scale"),
          slot("LOWRANKB", "variable", "left_factor"),
          slot("LOWRANKA", "variable", "right_factor")],
         ["The base weight is parameter-like because it is genuinely frozen -- "
          "not merely slow-moving, but excluded from the optimizer -- while the "
          "two factors are variable-like, since they are what changes. That "
          "split is the method, and it is visible in the slot categories rather "
          "than in the shape.",
          "The two factors are symmetric in the template and asymmetric in "
          "practice: B is initialized to zero and A to a random matrix, so the "
          "product starts at zero and the adapted model starts equal to the "
          "base. The template cannot record an initialization, so this is "
          "prose.",
          "The rank constraint is invisible here. `LOWRANKB*LOWRANKA` says only "
          "that the update factors through a product; that the inner dimension "
          "is small is the entire hypothesis of the paper and the template has "
          "no way to say it. Compare the corpus's other missing side "
          "conditions: this is the same class of loss as the quantifiers "
          "docs/BACKLOG.md records for differential topology.",
          "Affine in the adapter product at fixed base, and exactly linear in "
          "each factor with the other held fixed -- which is why alternating "
          "views of LoRA training are natural and why the loss is non-convex in "
          "the pair.",
          "The scaling slot is alpha/r and is a genuine hyperparameter, kept "
          "explicit because folding it into the factors changes the effective "
          "learning rate; it is also what makes the specialization edge from "
          "the affine family fire."],
         [sym("W", "variable", "effective_weight",
              "Effective weight matrix used at inference.", 2),
          sym("W0", "parameter", "frozen_base",
              "Pretrained weight matrix, frozen throughout adaptation.", 2),
          sym("B", "variable", "left_factor",
              "Left adapter factor, initialized to zero.", 2),
          sym("A", "variable", "right_factor",
              "Right adapter factor, randomly initialized.", 2),
          sym("r", "constant", "adapter_rank",
              "Inner dimension of the factorization; the rank budget.", 0),
          sym("alpha", "parameter", "adapter_scale",
              "Scaling hyperparameter; the update enters as alpha/r times the "
              "product.", 0)],
         [EQ, ADD, MUL],
         "Adapt a pretrained model by adding a scaled product of two thin "
         "matrices to a frozen weight, and train only those two.",
         "Affine in the adapter, and the corpus can prove it: "
         "scripts/specialize.py derives this node from "
         "probstat.transform.affine_location_scale by absorption, the affine "
         "map's SCALE slot swallowing part of the three-factor product while "
         "SHIFT binds the frozen base. That is the correct relationship and it "
         "is one of the few in this corpus reached by machine rather than by "
         "assertion. What the structure cannot carry is the only interesting "
         "thing about the method: `?0:V = +(?1:P, *(?2:P, ?3:V, ?4:V))` says "
         "the update factors through a product, not that the inner dimension is "
         "tiny, and the low-rank hypothesis -- that fine-tuning moves weights "
         "within a subspace of dimension in the tens -- is the empirical claim "
         "the paper actually makes. DoRA, PiSSA and LoftQ are recorded as "
         "equivalent forms rather than as separate nodes for the same reason: "
         "PiSSA and LoftQ differ from this equation only in how the same slots "
         "are initialized, which the template cannot express, and DoRA's "
         "magnitude-direction rescaling needs a norm the grammar has no head "
         "for. Three papers, one skeleton, and the differences between them all "
         "live where the formalism cannot see.",
         ["The frozen base excluded from the optimizer",
          "Inner dimension r much smaller than the weight matrix's dimensions, "
          "which the template cannot state",
          "Adapter product initialized to zero, so adaptation begins at the "
          "pretrained model",
          "Compatible shapes: B is d-by-r and A is r-by-k for a d-by-k base"],
         [HU2021LORA, AGHAJANYAN2021, LIU2024DORA, MENG2024PISSA, LI2023LOFTQ],
         failure_modes=[
             "The rank budget is a hard ceiling on what adaptation can express; "
             "tasks that genuinely require a full-rank change fail in a way "
             "that looks like underfitting and is not.",
             "Merging the adapter into the base is exact only for a linear "
             "layer with no intervening quantization; with a quantized base "
             "(LoftQ, QLoRA) the merged model is not the model that was "
             "trained.",
             "alpha and r interact: changing r while holding alpha fixed "
             "changes the effective learning rate of the adapter, so reported "
             "rank ablations that do not hold alpha/r fixed are confounded."],
         inferential_links=links(
             composed_with=["probstat.transform.affine_location_scale",
                            "ml.optimization.gradient_descent_step"]),
         keywords=["LoRA", "low-rank adaptation", "parameter-efficient "
                   "fine-tuning", "frozen weights", "DoRA", "PiSSA", "LoftQ"],
         canonical_objects=["weight matrix", "adapter factors", "rank budget"]),
]


def main() -> None:
    corpus = {
        "schema": "../../schema/equation-node.schema.json",
        "corpus_id": "machine_learning.training_and_architecture.v1",
        "discipline": "machine_learning",
        "version": "1.0.0-alpha",
        "statement_nodes": NODES,
    }
    out = Path("data/machine_learning/nodes.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(corpus, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"wrote {len(NODES)} machine learning nodes -> {out}")


if __name__ == "__main__":
    main()
