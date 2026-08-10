"""Registered predictions for ROADMAP-v0.7 item 6 (retrieval becomes tool use).

Registered BEFORE the implementation ran, per AGENTS.md working method 2.
Each prediction names its own miss condition; fired and missed are both
reportable, and the adjudication is recorded in the delivering commit.

**P-RT1 — The typed-protocol migration is behaviour-preserving.**
Replacing ``RetrievalNeed.resolution_channel``'s validated string with a
``Channel`` Enum, and ``Controller``'s ``getattr(verifier, "commit_run")``
with a ``runtime_checkable`` ``RunCommitter`` protocol, changes no observable
behaviour. Prediction: every existing test in ``tests/test_retrieval.py``,
``tests/test_ask.py``, ``tests/test_conversation_runtime.py``,
``tests/test_controller.py`` and ``tests/test_wordnet_retrieval.py`` passes
**unmodified**, including the receipt, forgery, replay and supersession
cases. *Miss* if any existing test file needs an edit to stay green.

**P-RT2 — The miss chain's rung order is observable in the trace.**
For a key that misses exact and neighborhood but is reachable through a
committed specialization/decomposition edge, the controller trace shows one
entry per attempted rung, in the order ``exact → neighborhood → derivation``,
each carrying its own outcome verdict, and the accepted entry is the
derivation rung. *Miss* if a rung is skipped, reordered, or if the chain
resolves without recording the rungs it walked past.

**P-RT3 — Ranked neighborhood announces its score and its cap.**
Neighborhood results are ordered by a closed-form token-overlap score in
[0, 1] (mean of query coverage, alias coverage, and exact-token share; 1.0
iff the query and alias token sets are equal), ties broken by the existing
deterministic (source, item_id) order. Prediction: the top-ranked
neighborhood item for a truncated statement id is that statement's own
corpus record; a truncated neighborhood announces the drop count **and** the
lowest admitted score; and no existing POINT outcome changes because of the
reordering. *Miss* if ranking flips any existing binding verdict.

**P-RT4 — Sense ambiguity survives relation traversal.** *(Hardest case,
named in advance: ``quickening``.)* ``quickening`` has three senses; only
``00331283-n`` shares members with ``acceleration``. Its hypernym is
``00330000-n`` = "change" — a common word whose lemma would alias many
corpus records. A traversal that flattened senses would therefore bridge
``quickening → change → several corpus statements`` and offer a POINT.
Prediction: hypernym/antonym/entailment traversal returns **per-sense**
records that name their originating synset and hop count, every one of them
stays ``empirical``, and **none of them is ever bindable** — a relation
record is WordNet's claim about a sense, not an answer to the key. *Miss* if
any relation-derived record binds a slot, if two senses are merged into one
record, or if a traversal record's status exceeds ``empirical``.

**P-RT5 — A tool transaction proves what was fetched, not that it is true.**
The local-filesystem observation adapter retains, per observation, its
source id, its declared record timestamp, the fetch timestamp, the exact
query that fetched it, and its epistemic rung. Prediction: an observation
file declaring a rung above the external ceiling (anything other than
``conjectured``/``empirical``) is refused at load with the file named; an
admitted observation's rung is unchanged by ranking, by neighbouring formal
corpus material, or by the receipt that authorised it. *Miss* if any
adapter-sourced record reaches a rung above ``empirical``.

**P-RT6 — Session pruning evidence is reusable and cannot poison a retry.**
REFUTED and exhausted (UNKNOWN/ABSTAIN) branches from a *returned* run are
recorded on the verifier at session scope, keyed by
``(session_id, verifier state_key, action fingerprint)``. Prediction: a
second run in the same session re-proposing the identical triple is pruned
with the original reason cited; the same action in the same session from a
**different** state is re-evaluated normally; and a different session is
never pruned. *Miss* if pruning refuses a branch that would otherwise have
been VERIFIED, or if a speculative (uncommitted) evaluation writes evidence.
"""
