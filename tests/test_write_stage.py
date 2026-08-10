"""The PROVEN-gated WRITE trust boundary.

Every test here runs against a MINI-REPOSITORY: a temporary copy of `scripts/`,
`data/`, `prover/` and `schema/`. That is not convenience, it is the control --
if a bug let the stager write to `data/`, a test using the real repository would
corrupt the durable store to discover it. The real repository's `data/` digest is
also asserted unchanged around the whole class, so the isolation itself is
checked rather than assumed.

The candidate exercised is a real Boolean law the corpus does not yet carry --
the domination law `P and false = false` -- proved by a real closing Lean
transition, staged through the full pipeline: path containment, rung, digest
pin, closure, transition trace, exclusive ownership, scratch regeneration,
regeneration confinement, semantic correspondence, schema and link validation,
matcher-delta prediction, durable byte-identity.
"""

from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from write_stage import (  # noqa: E402
    CONJECTURED,
    PROVEN,
    REFUSED,
    STAGED_CANDIDATE,
    STAGED_REVIEW_REQUEST,
    VERIFIED,
    WriteCandidate,
    durable_digest,
    stage_write,
)


CORPUS = "writestage_demo"
STATEMENT_ID = "writestagedemo.boolean_laws.domination_laws"
THEOREM = "BooleanLaws.domination_and_false"
ARTIFACT = "prover/candidate_proof.json"
SEED = "scripts/seed_writestage_demo.py"

TRANSITIONS = [
    {
        "theorem": THEOREM,
        "tactic": "simp",
        "stateBefore": "P : Prop\n\u22a2 P \u2227 False \u2194 False",
        "stateAfter": "no goals",
    }
]

NODE = {
    "statement_id": STATEMENT_ID,
    "title": "Domination Law for Meet (Propositional Form)",
    "statement_class": "identity",
    "epistemic_status": "formal",
    "theory_context": {
        "disciplines": ["logic"],
        "subfield": "propositional_logic",
        "topic": "boolean_laws",
        "canonical_objects": ["proposition", "Boolean lattice"],
    },
    "formal_statement": {
        "canonical_ascii": "P and false = false",
        "canonical_latex": "P \\land \\bot \\equiv \\bot",
        "equivalent_forms": [
            {
                "form_id": "unicode",
                "notation_system": "ascii",
                "expression": "P and false = false",
                "scope_note": "Standard connective notation",
            }
        ],
    },
    "structural_signature": {
        "archetype_id": "lattice_domination",
        "anonymized_template": "MEET(PROP1, FALSITY) = FALSITY",
        "slot_schema": [
            {
                "slot_id": "PROP1",
                "syntactic_category": "variable",
                "semantic_role": "propositional_operand",
            },
            {
                "slot_id": "FALSITY",
                "syntactic_category": "constant",
                "semantic_role": "lattice_bottom",
            },
        ],
        "invariants": [
            "BOT is the annihilator for MEET, dual to TOP being the "
            "annihilator for JOIN.",
        ],
    },
    "symbol_lexicon": {
        "symbols": [
            {
                "symbol": "P",
                "syntactic_category": "variable",
                "semantic_role": "propositional_operand",
                "mathematical_order": 0,
                "description": "An arbitrary proposition of the object language.",
            }
        ],
        "operators": [
            {
                "symbol": "=",
                "name": "logical equivalence",
                "arity": 2,
                "operator_family": "relational",
            },
            {
                "symbol": "and",
                "name": "conjunction",
                "arity": 2,
                "operator_family": "logical",
            },
        ],
        "functionals": [
            {
                "notation": "MEET(.,.)",
                "name": "lattice meet",
                "input_arity": 2,
                "description": "Greatest lower bound in the Boolean lattice.",
                "codomain": "propositions modulo logical equivalence",
            }
        ],
        "index_sets": [],
        "constants": [
            {
                "symbol": "false",
                "description": "The bottom of the Boolean lattice.",
            }
        ],
    },
    "semantic_interpretation": {
        "statement_meaning": (
            "Conjoining anything with falsity yields falsity; BOT absorbs MEET."
        ),
        "statistical_significance": (
            "Registered as the WRITE-staging fixture: a real Boolean law the "
            "committed corpora do not carry, so it can be staged without "
            "colliding with an existing statement or an owned theorem."
        ),
        "regularity_conditions": ["Classical two-valued semantics"],
        "failure_modes": [],
    },
    "inferential_links": {
        "entailed_by": [],
        "entails": [],
        "equivalent_to": [],
        "special_case_of": [],
        "generalizes": [],
        "composed_with": [],
    },
    "keywords": ["domination", "annihilator", "Boolean lattice"],
    "verified_by": [
        {"system": "lean4", "artifact": ARTIFACT, "reference": THEOREM}
    ],
}


def seed_source(node: dict, corpus: str = CORPUS) -> str:
    """A complete, self-contained seed script emitting one corpus."""

    payload = json.dumps(
        {
            "schema": "equation-node.schema.json",
            "corpus_id": corpus,
            "discipline": corpus,
            "version": "0.1.0",
            "statement_nodes": [node],
        },
        ensure_ascii=False,
        indent=2,
    )
    return (
        "import json\n"
        "from pathlib import Path\n"
        "\n"
        "CORPUS = json.loads(r'''\n" + payload + "\n''')\n"
        "\n"
        "def main() -> None:\n"
        f"    out = Path('data') / {corpus!r} / 'nodes.json'\n"
        "    out.parent.mkdir(parents=True, exist_ok=True)\n"
        "    out.write_text(\n"
        "        json.dumps(CORPUS, indent=2, ensure_ascii=False) + '\\n',\n"
        "        encoding='utf-8',\n"
        "    )\n"
        "\n"
        "main()\n"
    )


class MiniRepo:
    """A throwaway repository the stager may safely be pointed at."""

    def __init__(self) -> None:
        self._temporary = tempfile.TemporaryDirectory(prefix="write-stage-test-")
        self.root = Path(self._temporary.name) / "repo"
        for tree in ("scripts", "data", "prover", "schema"):
            shutil.copytree(
                REPO_ROOT / tree,
                self.root / tree,
                ignore=shutil.ignore_patterns("__pycache__"),
            )
        (self.root / ARTIFACT).write_text(
            json.dumps(TRANSITIONS, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.staging = self.root / "staging"

    @property
    def artifact_sha256(self) -> str:
        import hashlib

        return hashlib.sha256((self.root / ARTIFACT).read_bytes()).hexdigest()

    def close(self) -> None:
        self._temporary.cleanup()


class WriteStageTestCase(unittest.TestCase):
    """Shared fixture plus the standing guarantee about the REAL corpus."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.real_digest = durable_digest(REPO_ROOT / "data")

    @classmethod
    def tearDownClass(cls) -> None:
        assert durable_digest(REPO_ROOT / "data") == cls.real_digest, (
            "a WRITE-staging test changed the repository's durable store"
        )

    def setUp(self) -> None:
        self.repo = MiniRepo()
        self.addCleanup(self.repo.close)

    def candidate(self, **overrides) -> WriteCandidate:
        base = WriteCandidate(
            statement_id=STATEMENT_ID,
            corpus=CORPUS,
            seed_script=SEED,
            seed_source=seed_source(NODE),
            rung=PROVEN,
            rationale="A Boolean law with a machine-checked closing proof.",
            artifact=ARTIFACT,
            artifact_sha256=self.repo.artifact_sha256,
            reference=THEOREM,
            transition_trace=tuple(TRANSITIONS),
            expected_matcher_delta=EXPECTED_DELTA,
        )
        return replace(base, **overrides)

    def stage(self, candidate: WriteCandidate):
        return stage_write(candidate, self.repo.root, self.repo.staging)

    def assertRefusedBy(self, record, check: str) -> None:
        self.assertEqual(record.outcome, REFUSED, record.refusal)
        self.assertEqual(record.refusal["check"], check, record.refusal)


# Declared BEFORE the pipeline measures it; a candidate that cannot say what it
# will do to the twin matcher does not get staged (P-PW8).
EXPECTED_DELTA = {
    "nodes_analyzed": 1,
    "shape_groups": 0,
    "typed_groups": 0,
    "family_groups": 0,
    "aliased_groups": 0,
    "mirror_groups": 0,
    "new_typed_twin_partners": [],
}


class AcceptedCandidateTests(WriteStageTestCase):
    def test_proven_correspondent_candidate_stages(self) -> None:
        record = self.stage(self.candidate())
        self.assertEqual(record.outcome, STAGED_CANDIDATE, record.refusal)
        self.assertEqual(record.approval_required, ("human_or_prover_review",))
        self.assertEqual(record.approval_granted, ())

    def test_every_pipeline_stage_is_recorded_in_order(self) -> None:
        record = self.stage(self.candidate())
        self.assertEqual(
            [check["check"] for check in record.checks],
            [
                "path_containment",
                "epistemic_rung",
                "artifact_digest_pin",
                "theorem_closure",
                "transition_trace",
                "exclusive_theorem_ownership",
                "seed_source_screen",
                "scratch_regeneration",
                "regeneration_confinement",
                "semantic_correspondence",
                "structural_unambiguity",
                "schema_and_link_validation",
                "matcher_delta_prediction",
                "durable_store_byte_identity",
            ],
        )
        self.assertTrue(all(c["status"] == "PASS" for c in record.checks))

    def test_staged_record_carries_proof_identity_and_trace(self) -> None:
        record = self.stage(self.candidate())
        proof = record.staged["proof"]
        self.assertEqual(proof["reference"], THEOREM)
        self.assertEqual(proof["artifact"], ARTIFACT)
        self.assertEqual(proof["artifact_sha256"], self.repo.artifact_sha256)
        self.assertEqual(len(proof["transition_trace"]), 1)
        self.assertEqual(
            record.staged["node"]["statement_id"], STATEMENT_ID
        )
        self.assertEqual(record.staged["seed_script"], SEED)

    def test_correspondence_route_is_recorded(self) -> None:
        record = self.stage(self.candidate())
        self.assertEqual(record.correspondence["verdict"], "CORRESPONDS")
        self.assertEqual(record.correspondence["matched_route"], "canonical")

    def test_matcher_delta_is_measured_and_recorded(self) -> None:
        record = self.stage(self.candidate())
        delta = record.matcher_delta
        self.assertEqual(delta["delta"]["nodes_analyzed"], 1)
        self.assertEqual(delta["before"]["nodes_analyzed"] + 1,
                         delta["after"]["nodes_analyzed"])
        self.assertEqual(delta["delta"]["new_typed_twin_partners"], [])
        self.assertEqual(
            delta["candidate_typed_skeleton"], "?0:P = MEET⟨?0:P, ?1:V⟩"
        )

    def test_receipt_is_written_and_deterministic(self) -> None:
        first = self.stage(self.candidate())
        path = self.repo.staging / f"{first.record_id}.json"
        self.assertTrue(path.is_file())
        original = path.read_bytes()
        second = self.stage(self.candidate())
        self.assertEqual(second.record_id, first.record_id)
        self.assertEqual(path.read_bytes(), original)
        payload = json.loads(original.decode("utf-8"))
        self.assertEqual(payload["outcome"], STAGED_CANDIDATE)
        self.assertTrue(payload["durable_store"]["byte_identical"])
        self.assertEqual(payload["approval_granted"], [])

    def test_nothing_is_promoted_into_the_mini_repo_corpus(self) -> None:
        before = durable_digest(self.repo.root / "data")
        self.stage(self.candidate())
        self.assertEqual(durable_digest(self.repo.root / "data"), before)
        self.assertFalse((self.repo.root / "data" / CORPUS).exists())


class GateMatrixTests(WriteStageTestCase):
    """P-PW7: one row per rung, each with the outcome it is allowed."""

    def test_verified_stages_a_review_request_with_no_content(self) -> None:
        record = self.stage(self.candidate(rung=VERIFIED))
        self.assertEqual(record.outcome, STAGED_REVIEW_REQUEST)
        self.assertEqual(record.staged["kind"], "review_request")
        self.assertNotIn("seed_source", record.staged)
        self.assertNotIn("node", record.staged)
        self.assertNotIn("proof", record.staged)
        self.assertIsNone(record.correspondence)
        self.assertIsNone(record.matcher_delta)

    def test_conjectured_is_refused(self) -> None:
        self.assertRefusedBy(
            self.stage(self.candidate(rung=CONJECTURED)), "epistemic_rung"
        )

    def test_frame_local_is_refused_at_every_rung(self) -> None:
        for rung in (PROVEN, VERIFIED, CONJECTURED):
            with self.subTest(rung=rung):
                record = self.stage(self.candidate(rung=rung, frame_local=True))
                self.assertRefusedBy(record, "epistemic_rung")
                self.assertIn("frame-local", record.refusal["detail"])

    def test_unknown_rung_is_refused(self) -> None:
        self.assertRefusedBy(
            self.stage(self.candidate(rung="PROBABLY")), "epistemic_rung"
        )

    def test_proven_with_a_mismatching_theorem_is_refused(self) -> None:
        """The gravity-control shape, inside the WRITE gate."""
        node = copy.deepcopy(NODE)
        node["structural_signature"]["anonymized_template"] = (
            "MEET(PROP1, JOIN(PROP1, FALSITY)) = PROP1"
        )
        node["formal_statement"]["equivalent_forms"] = [
            {
                "form_id": "unicode",
                "notation_system": "ascii",
                "expression": "P and (P or false) = P",
                "scope_note": "Standard connective notation",
            }
        ]
        record = self.stage(self.candidate(seed_source=seed_source(node)))
        self.assertRefusedBy(record, "semantic_correspondence")
        self.assertIn("MISMATCH", record.refusal["detail"])

    def test_proven_with_an_untranslatable_theorem_fails_closed(self) -> None:
        """UNTRANSLATABLE is reported by the lint but REFUSED by the gate."""
        artifact = self.repo.root / ARTIFACT
        rows = copy.deepcopy(TRANSITIONS)
        rows[0]["stateBefore"] = "n : Nat\n\u22a2 n + 0 = n"
        artifact.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        record = self.stage(
            self.candidate(
                artifact_sha256=self.repo.artifact_sha256,
                transition_trace=tuple(rows),
            )
        )
        self.assertRefusedBy(record, "semantic_correspondence")
        self.assertIn("UNTRANSLATABLE", record.refusal["detail"])


class MaliciousPathTests(WriteStageTestCase):
    """No runtime action may write `data/*/nodes.json`."""

    def test_candidate_targeting_the_durable_store_is_refused(self) -> None:
        record = self.stage(
            self.candidate(seed_script="data/logic/nodes.json")
        )
        self.assertRefusedBy(record, "path_containment")
        self.assertIn("durable store is never a WRITE target",
                      record.refusal["detail"])

    def test_refusal_leaves_the_durable_store_byte_identical(self) -> None:
        before = durable_digest(self.repo.root / "data")
        record = self.stage(
            self.candidate(seed_script="data/logic/nodes.json")
        )
        self.assertEqual(durable_digest(self.repo.root / "data"), before)
        self.assertEqual(record.durable_digest_before, before)
        self.assertEqual(record.durable_digest_after, before)

    def test_refusal_still_writes_a_diffable_receipt(self) -> None:
        record = self.stage(
            self.candidate(seed_script="data/logic/nodes.json")
        )
        path = self.repo.staging / f"{record.record_id}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["outcome"], REFUSED)
        self.assertEqual(payload["refusal"]["check"], "path_containment")
        self.assertTrue(payload["durable_store"]["byte_identical"])
        self.assertIsNone(payload["staged"])

    def test_escaping_and_absolute_targets_are_refused(self) -> None:
        for target in (
            "../outside/seed_evil.py",
            "/etc/seed_evil.py",
            "scripts\\seed_evil.py",
            "scripts/not_a_seed.py",
            "scripts/nested/seed_evil.py",
            "data/../data/logic/nodes.json",
        ):
            with self.subTest(target=target):
                self.assertRefusedBy(
                    self.stage(self.candidate(seed_script=target)),
                    "path_containment",
                )

    def test_proposal_file_cannot_read_bytes_from_outside_the_repository(
        self,
    ) -> None:
        """Self-review: a proposal is untrusted input, and `seed_source_path`
        was an uncontained read that could pull arbitrary bytes into a record."""
        from write_stage import Refusal, candidate_from_json

        for path in ("../../secret.py", "/etc/passwd", "scripts/retrieval.py"):
            with self.subTest(path=path), self.assertRaises(Refusal) as caught:
                candidate_from_json(
                    {
                        "statement_id": STATEMENT_ID,
                        "corpus": CORPUS,
                        "seed_script": SEED,
                        "seed_source_path": path,
                        "rung": PROVEN,
                    },
                    self.repo.root,
                )
            self.assertEqual(caught.exception.check, "path_containment")

    def test_seed_naming_a_path_outside_the_scratch_is_screened(self) -> None:
        source = seed_source(NODE).replace(
            "Path('data')", "Path('../data')"
        )
        self.assertRefusedBy(
            self.stage(self.candidate(seed_source=source)), "seed_source_screen"
        )


class RegenerationConfinementTests(WriteStageTestCase):
    def test_seed_touching_another_corpus_is_refused(self) -> None:
        extra = (
            "\nimport json as _j\nfrom pathlib import Path as _P\n"
            "_p = _P('data') / 'logic' / 'nodes.json'\n"
            "_d = _j.loads(_p.read_text(encoding='utf-8'))\n"
            "_d['version'] = '9.9.9'\n"
            "_p.write_text(_j.dumps(_d, indent=2, ensure_ascii=False) + '\\n',"
            " encoding='utf-8')\n"
        )
        record = self.stage(
            self.candidate(seed_source=seed_source(NODE) + extra)
        )
        self.assertRefusedBy(record, "regeneration_confinement")
        self.assertIn("logic/nodes.json", record.refusal["detail"])

    def test_seed_adding_an_undeclared_statement_is_refused(self) -> None:
        second = copy.deepcopy(NODE)
        second["statement_id"] = "writestagedemo.boolean_laws.smuggled"
        second["verified_by"] = []
        payload = json.dumps(
            {
                "schema": "equation-node.schema.json",
                "corpus_id": CORPUS,
                "discipline": CORPUS,
                "version": "0.1.0",
                "statement_nodes": [NODE, second],
            },
            ensure_ascii=False,
            indent=2,
        )
        source = (
            "import json\nfrom pathlib import Path\n"
            "CORPUS = json.loads(r'''\n" + payload + "\n''')\n"
            f"out = Path('data') / {CORPUS!r} / 'nodes.json'\n"
            "out.parent.mkdir(parents=True, exist_ok=True)\n"
            "out.write_text(json.dumps(CORPUS, indent=2, ensure_ascii=False)"
            " + '\\n', encoding='utf-8')\n"
        )
        record = self.stage(self.candidate(seed_source=source))
        self.assertRefusedBy(record, "regeneration_confinement")
        self.assertIn("smuggled", record.refusal["detail"])

    def test_failing_seed_is_refused_without_leaking_a_temp_path(self) -> None:
        record = self.stage(
            self.candidate(seed_source="raise SystemExit('seed exploded')\n")
        )
        self.assertRefusedBy(record, "scratch_regeneration")
        self.assertIn("seed exploded", record.refusal["detail"])
        self.assertNotIn("write-stage-", record.refusal["detail"])

    def test_the_seed_never_learns_where_the_repository_is(self) -> None:
        """Containment by construction, not by screen.

        The seed runs with cwd inside a throwaway scratch tree, a relative
        argv, and an environment carrying no repository path -- so it cannot
        name the durable store even if it wants to. Proved by making the seed
        report its own working directory: the refusal shows the scrubbed
        scratch marker and never the repository root.
        """
        record = self.stage(
            self.candidate(
                seed_source=(
                    "from pathlib import Path\n"
                    "raise SystemExit('cwd=' + str(Path.cwd()))\n"
                )
            )
        )
        self.assertRefusedBy(record, "scratch_regeneration")
        self.assertIn("cwd=<scratch>", record.refusal["detail"])
        self.assertNotIn(str(self.repo.root), record.refusal["detail"])

    def test_extending_an_existing_corpus_is_confined_too(self) -> None:
        """The other regeneration shape: add one node to a committed corpus."""
        node = copy.deepcopy(NODE)
        node["statement_id"] = "logic.boolean_laws.domination_laws"
        source = (
            "import json\nfrom pathlib import Path\n"
            "NODE = json.loads(r'''\n"
            + json.dumps(node, ensure_ascii=False, indent=2)
            + "\n''')\n"
            "path = Path('data') / 'logic' / 'nodes.json'\n"
            "corpus = json.loads(path.read_text(encoding='utf-8'))\n"
            "corpus['statement_nodes'].append(NODE)\n"
            "path.write_text(\n"
            "    json.dumps(corpus, indent=2, ensure_ascii=False) + '\\n',\n"
            "    encoding='utf-8',\n"
            ")\n"
        )
        record = self.stage(
            self.candidate(
                statement_id="logic.boolean_laws.domination_laws",
                corpus="logic",
                seed_script="scripts/seed_logic.py",
                seed_source=source,
            )
        )
        self.assertEqual(record.outcome, STAGED_CANDIDATE, record.refusal)
        self.assertEqual(
            record.staged["node"]["statement_id"],
            "logic.boolean_laws.domination_laws",
        )

    def test_extending_an_existing_corpus_may_not_drop_its_statements(
        self,
    ) -> None:
        source = (
            "import json\nfrom pathlib import Path\n"
            "path = Path('data') / 'logic' / 'nodes.json'\n"
            "corpus = json.loads(path.read_text(encoding='utf-8'))\n"
            "corpus['statement_nodes'] = corpus['statement_nodes'][:2]\n"
            "path.write_text(\n"
            "    json.dumps(corpus, indent=2, ensure_ascii=False) + '\\n',\n"
            "    encoding='utf-8',\n"
            ")\n"
        )
        record = self.stage(
            self.candidate(
                corpus="logic",
                seed_script="scripts/seed_logic.py",
                seed_source=source,
            )
        )
        self.assertRefusedBy(record, "regeneration_confinement")
        self.assertIn("removes existing statements", record.refusal["detail"])

    def test_declared_node_cannot_differ_from_the_regenerated_one(self) -> None:
        """The judged node is the one the SEED emits, not one the candidate
        asserts: a candidate declaring `statement_id` X while its seed emits Y
        is refused rather than judged on X."""
        record = self.stage(
            self.candidate(statement_id="writestagedemo.boolean_laws.other")
        )
        self.assertRefusedBy(record, "regeneration_confinement")


class ProofGateTests(WriteStageTestCase):
    def test_unpinned_artifact_digest_is_refused(self) -> None:
        self.assertRefusedBy(
            self.stage(self.candidate(artifact_sha256="")),
            "artifact_digest_pin",
        )

    def test_wrong_artifact_digest_is_refused(self) -> None:
        self.assertRefusedBy(
            self.stage(self.candidate(artifact_sha256="0" * 64)),
            "artifact_digest_pin",
        )

    def test_theorem_that_does_not_close_is_refused(self) -> None:
        rows = copy.deepcopy(TRANSITIONS)
        rows[0]["stateAfter"] = "P : Prop\n\u22a2 False"
        (self.repo.root / ARTIFACT).write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self.assertRefusedBy(
            self.stage(
                self.candidate(
                    artifact_sha256=self.repo.artifact_sha256,
                    transition_trace=tuple(rows),
                )
            ),
            "theorem_closure",
        )

    def test_fabricated_transition_trace_is_refused(self) -> None:
        forged = copy.deepcopy(TRANSITIONS)
        forged[0]["tactic"] = "sorry"
        self.assertRefusedBy(
            self.stage(self.candidate(transition_trace=tuple(forged))),
            "transition_trace",
        )

    def test_empty_transition_trace_is_refused(self) -> None:
        self.assertRefusedBy(
            self.stage(self.candidate(transition_trace=())), "transition_trace"
        )

    def test_contentless_transition_row_is_refused(self) -> None:
        """Self-review: a row stating nothing would match any artifact row,
        because the subsequence test compares only the keys a row declares."""
        for row in ({}, {"theorem": THEOREM}, dict(TRANSITIONS[0], tactic="  ")):
            with self.subTest(row=sorted(row)):
                self.assertRefusedBy(
                    self.stage(self.candidate(transition_trace=(row,))),
                    "transition_trace",
                )

    def test_two_theorem_artifact_cannot_lend_its_good_theorem(self) -> None:
        """Self-review: pack a corresponding theorem beside the cited one."""
        rows = [
            {
                "theorem": "BooleanLaws.decoy",
                "tactic": "simp",
                "stateBefore": "P : Prop\n⊢ P ∧ False ↔ False",
                "stateAfter": "no goals",
            },
            {
                "theorem": THEOREM,
                "tactic": "simp",
                "stateBefore": "P Q : Prop\n⊢ P ∧ Q ↔ Q ∧ P",
                "stateAfter": "no goals",
            },
        ]
        (self.repo.root / ARTIFACT).write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        record = self.stage(
            self.candidate(
                artifact_sha256=self.repo.artifact_sha256,
                transition_trace=(rows[1],),
            )
        )
        self.assertRefusedBy(record, "semantic_correspondence")
        self.assertIn("MISMATCH", record.refusal["detail"])

    def test_already_owned_theorem_is_refused(self) -> None:
        """A candidate may not re-cite a theorem an existing statement owns."""
        node = copy.deepcopy(NODE)
        node["verified_by"] = [
            {
                "system": "lean4",
                "artifact": "prover/sample_triples.json",
                "reference": "BooleanLaws.modus_ponens",
            }
        ]
        record = self.stage(
            self.candidate(
                seed_source=seed_source(node),
                artifact="prover/sample_triples.json",
                reference="BooleanLaws.modus_ponens",
                artifact_sha256=_sha256(
                    self.repo.root / "prover" / "sample_triples.json"
                ),
                transition_trace=(_first_row(
                    self.repo.root / "prover" / "sample_triples.json",
                    "BooleanLaws.modus_ponens",
                ),),
            )
        )
        self.assertRefusedBy(record, "exclusive_theorem_ownership")

    def test_candidate_node_citing_another_theorem_is_refused(self) -> None:
        """Attack: prove theorem A, ship a node that cites theorem B."""
        node = copy.deepcopy(NODE)
        node["verified_by"] = [
            {
                "system": "lean4",
                "artifact": ARTIFACT,
                "reference": "BooleanLaws.something_else",
            }
        ]
        record = self.stage(self.candidate(seed_source=seed_source(node)))
        self.assertRefusedBy(record, "semantic_correspondence")
        self.assertIn("different theorem", record.refusal["detail"])


class ValidationAndDeltaTests(WriteStageTestCase):
    def test_schema_invalid_candidate_is_refused(self) -> None:
        node = copy.deepcopy(NODE)
        node["epistemic_status"] = "vibes"
        self.assertRefusedBy(
            self.stage(self.candidate(seed_source=seed_source(node))),
            "schema_and_link_validation",
        )

    def test_dangling_inferential_link_is_refused(self) -> None:
        node = copy.deepcopy(NODE)
        node["inferential_links"]["entails"] = ["logic.does.not.exist"]
        self.assertRefusedBy(
            self.stage(self.candidate(seed_source=seed_source(node))),
            "schema_and_link_validation",
        )

    def test_undeclared_matcher_delta_is_refused(self) -> None:
        self.assertRefusedBy(
            self.stage(self.candidate(expected_matcher_delta=None)),
            "matcher_delta_prediction",
        )

    def test_wrong_matcher_delta_is_refused_though_everything_else_passes(
        self,
    ) -> None:
        """P-PW8: a candidate that passes schema, link and regeneration checks
        but mispredicts its effect on the twin matcher does not stage."""
        wrong = dict(EXPECTED_DELTA, nodes_analyzed=0)
        record = self.stage(self.candidate(expected_matcher_delta=wrong))
        self.assertRefusedBy(record, "matcher_delta_prediction")
        self.assertIn("nodes_analyzed", record.refusal["detail"])
        self.assertIn("declared 0", record.refusal["detail"])
        passed = [c["check"] for c in record.checks if c["status"] == "PASS"]
        self.assertIn("schema_and_link_validation", passed)
        self.assertIn("semantic_correspondence", passed)

    def test_structural_twin_of_a_committed_statement_is_refused(self) -> None:
        """Self-review, the forgery attack: cite a theorem whose skeleton an
        existing statement already declares.

        `logic.boolean_laws.idempotence` declares `MEET(P, P) = P`, so a
        candidate proving `P and P <-> P` is structurally indistinguishable from
        it. Correspondence would say CORRESPONDS; only the unambiguity gate can
        say that CORRESPONDS is not enough to name an owner. Refused, with the
        claimant named.
        """
        node = copy.deepcopy(NODE)
        node["structural_signature"]["anonymized_template"] = (
            "MEET(PROP1, PROP1) = PROP1"
        )
        node["structural_signature"]["slot_schema"] = [
            {
                "slot_id": "PROP1",
                "syntactic_category": "variable",
                "semantic_role": "propositional_operand",
            }
        ]
        node["formal_statement"]["canonical_ascii"] = "P and P = P"
        node["formal_statement"]["equivalent_forms"] = [
            {
                "form_id": "unicode",
                "notation_system": "ascii",
                "expression": "P and P = P",
                "scope_note": "Standard connective notation",
            }
        ]
        rows = copy.deepcopy(TRANSITIONS)
        rows[0]["stateBefore"] = "P : Prop\n\u22a2 P \u2227 P \u2194 P"
        (self.repo.root / ARTIFACT).write_text(
            json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        record = self.stage(
            self.candidate(
                seed_source=seed_source(node),
                artifact_sha256=self.repo.artifact_sha256,
                transition_trace=tuple(rows),
            )
        )
        self.assertRefusedBy(record, "structural_unambiguity")
        self.assertIn("logic.boolean_laws.idempotence", record.refusal["detail"])
        self.assertIn("settheory.boolean_laws.idempotence", record.refusal["detail"])

    def test_partial_delta_declaration_is_refused(self) -> None:
        self.assertRefusedBy(
            self.stage(
                self.candidate(expected_matcher_delta={"nodes_analyzed": 1})
            ),
            "matcher_delta_prediction",
        )


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _first_row(path: Path, theorem: str) -> dict:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return next(row for row in rows if row["theorem"] == theorem)


if __name__ == "__main__":
    unittest.main()
