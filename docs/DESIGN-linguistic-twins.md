# Design: Linguistic Twins — grammar as the next discipline corpus

Status: design + first experiment (experiments/langgen.py). Extends
DESIGN-concept-tokens.md into natural-language syntax. Creation dual
(construct → verify → linearize), demo-debt, and P-LS* predictions:
`docs/DESIGN-language-as-structure.md`.

## The claim

Natural language is not a new kind of object for this project; it is another
discipline whose statements have structural signatures, and whose surface
forms are skins over shared skeletons. Concretely:

- **Modifiers are modifiers, with recursion (discrete infinity).**
  Modification is a closed operator that applies to its own output: adjective
  stacks, intensifier chains ("very very big"), relative clauses. In tree
  terms, intersective modifier *sets* are a commutative operation (big red
  dog = red big dog) — the same commutative-flatten-sort our canonicalizer
  applies to `+` and `*` — while modifier *application* (very ∘ big) is
  non-commutative nesting, like function composition. Unbounded recursion is
  where discrete infinity lives, exactly as in expression trees.

- **Statements are proofs.** A declarative sentence asserts a judgment: it
  is the closed, provable object. In ontology terms it carries
  epistemic_status the way a theorem node does.

- **Comparisons are inequalities.** "The dog is bigger than the cat" is
  `size(dog) > size(cat)` — an order relation on measure functions. The
  matcher's relation set already contains `<`, `>`, `<=`, `>=`.

- **Questions are equations.** A WH-question is an open formula with an
  unknown: "who chases the cat" is `EVT(chase, X, cat)` — solve for X.
  Answering is unification against a knowledge base, the same operation as
  solving an equation. A yes/no question is a decision problem — proof
  search over the corresponding statement.

- **Languages are twins of languages.** Two languages' sentences about one
  proposition are two surface realizations of one skeleton — precisely the
  relationship between `Y = alpha*X + beta` and `y = m*x + b`, or between a
  formula and its "thesaurical twin." Translation is twin matching plus a
  lexicon swap, which is the extrinsic-lexicon architecture doing what it
  was designed for: concept core in one place, per-language realization
  outside it.

- **Understanding as emergent division of labor.** The bet, carried over
  from the equiv experiment result: parse always (it paid on every task),
  canonicalize per query (it paid only when the query IS canonical
  identity), and let weights learn only the residual (lexicon alignment,
  graded semantics). Surface parse and canonical form should both be
  exposed — two channels, not a replacement.

## First experiment: cross-language twin detection (xlang task)

`experiments/langgen.py` builds a controlled bilingual world:

- One semantic tree language (the interlingua): STMT/ASK/CMP heads, EVT
  predicate-argument structure, commutative modifier sets, non-commutative
  intensifier nesting, WH unknowns.
- Language A: SVO, adjectives before nouns, intensifiers before adjectives,
  English-like lexicon.
- Language B: SOV, adjectives after nouns, intensifiers after adjectives,
  disjoint pseudo-word lexicon, question particle.

Task: given a Language-A sentence and a Language-B sentence, do they express
the same proposition? Negatives are near-misses: swapped roles, one changed
concept, an adjective moved across NPs, changed sentence type.

Same three arms, same ~880k-param model:

| arm | front-end gives | model must learn |
|---|---|---|
| char | nothing | parsing of two grammars + bilingual dictionary + role semantics |
| struct | both parse trees (surface order, native words) | bilingual dictionary + canonical order |
| canon | canonical interlingua (concept ids) | ~nothing (sanity ceiling) |

Predictions (falsifiable): char << struct << canon ~= 1.0; char's OOD gap
(deeper modifier recursion) largest; struct's residual error concentrates on
dictionary confusions, not structure. If char matches struct at this scale,
the parse-front-end thesis weakens for language and we should say so.
