"""The PROVEN-gated WRITE trust boundary.

Every test here runs against a MINI-REPOSITORY: a temporary copy of `scripts/`,
`data/`, `prover/` and `schema/`. That is not convenience, it is the control --
if a bug let the stager write to `data/`, a test using the real repository would
corrupt the durable store to discover it. The real repository's digest is also
asserted unchanged around every class, so the isolation itself is checked rather
than assumed.

That control was itself two notches weaker than it advertised, and both are
fixed here. It digested `data/` alone while the fixture copies four trees, so an
escape into `scripts/` or `prover/` was invisible to the very guard whose job is
to see it; and it was a bare `assert`, which `python -O` deletes, so the guard
could be compiled out of existence. It now digests every copied tree and raises
unconditionally.

The candidate exercised is a real Boolean law the corpus does not yet carry --
the domination law `P and false = false` -- proved by a real closing Lean
transition, staged through the full pipeline: path containment, rung, digest
pin, closure, transition trace, exclusive ownership, scratch regeneration,
regeneration confinement, semantic correspondence, structural unambiguity,
schema and link validation, matcher-delta prediction, durable byte-identity.
The last class runs the same gate through `controller.py`'s ordinary loop.
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
    working_tree_digest,
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
        # All four copied trees plus the repository's root files, not `data/`
        # alone: a stager bug that landed a file in `scripts/` or `prover/`
        # would have slipped past a corpus-only digest, which is precisely the
        # blind spot this suite exists to have covered.
        cls.real_digest = working_tree_digest(REPO_ROOT)

    @classmethod
    def tearDownClass(cls) -> None:
        # `raise`, not `assert`: `python -O` strips assert statements, and a
        # safety control that a compile flag can delete is not a control.
        if working_tree_digest(REPO_ROOT) != cls.real_digest:
            raise AssertionError(
                "a WRITE-staging test changed the repository working tree "
                "(root files, data/, prover/, schema/ or scripts/)"
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
# will do to the twin matcher does not get staged (P-PW8). Every counter the
# matcher summary emits is here: the first delivery gated seven of nine, so a
# candidate could add a `slot_schema_gaps` and never have predicted it.
EXPECTED_DELTA = {
    "nodes_analyzed": 1,
    "shape_groups": 0,
    "typed_groups": 0,
    "family_groups": 0,
    "aliased_groups": 0,
    "mirror_groups": 0,
    "ladder_violations": 0,
    "parse_problems": 0,
    "slot_schema_gaps": 0,
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
                "working_tree_byte_identity",
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
        self.assertTrue(payload["working_tree_integrity"]["byte_identical"])
        self.assertEqual(
            payload["working_tree_integrity"]["covers"],
            ["<repository root files>", "data", "prover", "schema", "scripts"],
        )
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
        # Asserted against the STRUCTURED record, not against prose: the
        # refusal detail is a human sentence and a substring of it is a weak
        # pin on a strong claim. "A diffable receipt explaining why" is also
        # worth little if the MISMATCH receipt omits the skeletons.
        self.assertEqual(record.correspondence["verdict"], "MISMATCH")
        self.assertIsNone(record.correspondence["matched_route"])
        self.assertTrue(record.correspondence["theorem_skeleton"])
        self.assertTrue(record.correspondence["considered_forms"])
        self.assertNotIn(
            record.correspondence["theorem_skeleton"],
            [
                form.split(": ", 1)[1]
                for form in record.correspondence["considered_forms"]
            ],
        )

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
        self.assertEqual(record.correspondence["verdict"], "UNTRANSLATABLE")
        self.assertIsNone(record.correspondence["matched_route"])


class MaliciousPathTests(WriteStageTestCase):
    """No runtime action may write `data/*/nodes.json`."""

    def test_candidate_targeting_the_durable_store_is_refused(self) -> None:
        record = self.stage(
            self.candidate(seed_script="data/logic/nodes.json")
        )
        self.assertRefusedBy(record, "path_containment")
        self.assertIn("durable store is never a WRITE target",
                      record.refusal["detail"])

    def test_receipts_may_not_be_written_into_the_durable_store(self) -> None:
        """Self-review: every candidate-controlled path was contained; the
        caller-supplied receipt directory was not."""
        before = durable_digest(self.repo.root / "data")
        for target in (
            self.repo.root / "data",
            self.repo.root / "data" / "logic",
            self.repo.root / "data" / "new" / "receipts",
        ):
            # Not a bare `assertRaises(ValueError)`: `Refusal` is not a
            # ValueError but `proof_correspondence.Untranslatable` IS, and a
            # test that accepts any ValueError would go green on a leak from
            # deep inside the pipeline while claiming to pin this guard. The
            # message is asserted for the same reason.
            with self.subTest(target=target.name), self.assertRaises(
                ValueError
            ) as caught:
                stage_write(self.candidate(), self.repo.root, target)
            self.assertIs(type(caught.exception), ValueError)
            self.assertIn(
                "staging directory may not live under the durable store",
                str(caught.exception),
            )
        self.assertEqual(durable_digest(self.repo.root / "data"), before)

    def test_refusal_leaves_the_working_tree_byte_identical(self) -> None:
        before_data = durable_digest(self.repo.root / "data")
        before_tree = working_tree_digest(self.repo.root)
        record = self.stage(
            self.candidate(seed_script="data/logic/nodes.json")
        )
        self.assertEqual(durable_digest(self.repo.root / "data"), before_data)
        self.assertEqual(working_tree_digest(self.repo.root), before_tree)
        self.assertEqual(record.working_tree_digest_before, before_tree)
        self.assertEqual(record.working_tree_digest_after, before_tree)

    def test_refusal_still_writes_a_diffable_receipt(self) -> None:
        record = self.stage(
            self.candidate(seed_script="data/logic/nodes.json")
        )
        path = self.repo.staging / f"{record.record_id}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["outcome"], REFUSED)
        self.assertEqual(payload["refusal"]["check"], "path_containment")
        self.assertTrue(payload["working_tree_integrity"]["byte_identical"])
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

    def proposal_payload(self, source_path: str) -> dict:
        return {
            "statement_id": STATEMENT_ID,
            "corpus": CORPUS,
            "seed_script": SEED,
            "seed_source_path": source_path,
            "rung": PROVEN,
        }

    def test_proposal_seed_source_path_must_be_a_contained_seed_script(
        self,
    ) -> None:
        """Self-review: a proposal is untrusted input, and `seed_source_path`
        was an uncontained read that could pull arbitrary bytes into a record.

        Renamed from `..._cannot_read_bytes_from_outside_the_repository`,
        which the third case falsified: `scripts/retrieval.py` is INSIDE the
        repository and is refused for not being a `seed_*.py` script. The rule
        is containment AND naming, and the name now says so.
        """
        from write_stage import Refusal, candidate_from_json

        for path, why in (
            ("../../secret.py", "escapes the repository"),
            ("/etc/passwd", "is absolute"),
            ("scripts/retrieval.py", "is contained but is not a seed script"),
            ("data/logic/nodes.json", "is the durable store"),
            ("scripts/seed_absent.py", "does not exist"),
        ):
            with self.subTest(path=path, why=why), self.assertRaises(
                Refusal
            ) as caught:
                candidate_from_json(self.proposal_payload(path), self.repo.root)
            self.assertEqual(caught.exception.check, "path_containment")

    def test_a_contained_seed_script_is_actually_read(self) -> None:
        """The accepting branch. Five refusals and no acceptance would pass
        just as well against a `seed_source_path` that refused everything --
        including the shape the README documents."""
        from write_stage import candidate_from_json

        (self.repo.root / SEED).write_text(
            seed_source(NODE), encoding="utf-8"
        )
        candidate = candidate_from_json(
            self.proposal_payload(SEED), self.repo.root
        )
        self.assertEqual(candidate.seed_source, seed_source(NODE))
        self.assertEqual(candidate.seed_script, SEED)

    def test_seed_naming_a_path_outside_the_scratch_is_screened(self) -> None:
        source = seed_source(NODE).replace(
            "Path('data')", "Path('../data')"
        )
        self.assertRefusedBy(
            self.stage(self.candidate(seed_source=source)), "seed_source_screen"
        )


class WorkingTreeIntegrityTests(WriteStageTestCase):
    """The integrity digest covered `data/` while the fixture copies FOUR trees.

    A candidate seed that reached `scripts/`, `prover/`, `schema/` or the
    repository root therefore landed its file AND collected a receipt saying
    `byte_identical: true` -- it could have rewritten `scripts/write_stage.py`
    to own the next run, or poisoned the `prover/` artifacts that every
    `artifact_sha256` pin in the corpus resolves against.

    The seeds below defeat `_screen_seed_source` on purpose, by assembling the
    path at runtime instead of writing a literal. That is the point: the screen
    is documented as catching non-adversarial mistakes, so the digest is the
    only thing standing behind the boundary and it must be shown standing.
    """

    def escaping_seed(self, relative: str, payload: str) -> str:
        """A seed that writes `relative` inside the REAL mini-repo root.

        The root is passed as character codes so no absolute-path literal and
        no `..` literal appears in the source -- exactly the shape the module
        docstring warns a determined candidate can take.
        """
        codes = [ord(c) for c in str(self.repo.root)]
        return (
            seed_source(NODE)
            + "\nfrom pathlib import Path as _P\n"
            f"_root = _P(''.join(chr(c) for c in {codes!r}))\n"
            f"_target = _root / {'/'.join(repr(p) for p in relative.split('/'))}\n"
            "_target.parent.mkdir(parents=True, exist_ok=True)\n"
            f"_target.write_text({payload!r}, encoding='utf-8')\n"
        )

    def assertEscapeCaught(self, relative: str) -> None:
        before_tree = working_tree_digest(self.repo.root)
        before_data = durable_digest(self.repo.root / "data")
        record = self.stage(
            self.candidate(seed_source=self.escaping_seed(relative, "# owned\n"))
        )
        self.assertRefusedBy(record, "working_tree_byte_identity")
        self.assertIsNone(record.staged)
        self.assertNotEqual(
            record.working_tree_digest_before,
            record.working_tree_digest_after,
        )
        # The escape really happened -- the digest is catching a real write,
        # not refusing a hypothetical one.
        self.assertTrue((self.repo.root / relative).is_file())
        self.assertNotEqual(working_tree_digest(self.repo.root), before_tree)
        # ... and it is invisible to the `data/`-only digest the gate used to
        # enforce, which is why that digest was the wrong cover.
        self.assertEqual(durable_digest(self.repo.root / "data"), before_data)
        payload = json.loads(
            (self.repo.staging / f"{record.record_id}.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(payload["working_tree_integrity"]["byte_identical"])

    def test_a_seed_that_escapes_into_scripts_is_caught_by_the_digest(self) -> None:
        """The worst case: overwrite the gate itself for the next run."""
        self.assertEscapeCaught("scripts/write_stage.py")

    def test_a_seed_that_escapes_into_prover_is_caught_by_the_digest(self) -> None:
        """Poison the artifacts every `artifact_sha256` pin resolves against."""
        self.assertEscapeCaught("prover/sample_triples.json")

    def test_a_seed_that_escapes_into_the_repository_root_is_caught(self) -> None:
        self.assertEscapeCaught("AGENTS.md")

    def test_a_seed_that_escapes_into_schema_is_caught(self) -> None:
        self.assertEscapeCaught("schema/equation-node.schema.json")

    def test_the_digest_ignores_this_gates_own_receipts(self) -> None:
        """`staging/` is excluded, and it has to be: the gate writes there.

        Without the exclusion the second run of a candidate would see a
        different before-digest and every re-run would look like tampering.
        """
        first = self.stage(self.candidate())
        second = self.stage(self.candidate())
        self.assertEqual(
            first.working_tree_digest_before, second.working_tree_digest_before
        )
        self.assertEqual(second.outcome, STAGED_CANDIDATE, second.refusal)


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

    def test_seed_runs_with_its_cwd_inside_the_scratch_tree(self) -> None:
        """What the containment actually is: cwd, argv and environment.

        Renamed from `test_the_seed_never_learns_where_the_repository_is`,
        which asserted more than it checked. The seed is HANDED no repository
        path -- proved below by making it report its own working directory --
        but it is started as `sys.executable`, which is the project's own
        `.venv` interpreter, so a seed that walks up from `sys.executable` finds
        the project root. Containment here is over cwd/argv/environment only;
        the integrity digest is what stands behind the residual threat, and
        `test_a_seed_that_escapes_into_scripts_is_caught_by_the_digest` is
        where that is exercised.
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

    def test_the_seed_is_handed_one_absolute_path_the_interpreters(self) -> None:
        """The honest half, asserted rather than admitted only in prose.

        `cwd` is scratch and `argv[0]` is relative, but the process is started
        as `sys.executable` and Python hands that to the child. It is the one
        absolute path outside the scratch tree the seed always has, and a
        walk up from it reaches whatever project the interpreter belongs to.
        """
        record = self.stage(
            self.candidate(
                seed_source=(
                    "import sys\n"
                    "from pathlib import Path\n"
                    "raise SystemExit('exe=' + Path(sys.executable).as_posix())\n"
                )
            )
        )
        self.assertRefusedBy(record, "scratch_regeneration")
        detail = record.refusal["detail"]
        self.assertIn("exe=", detail)
        # Not scrubbed to `<scratch>`, because it is not in the scratch tree.
        self.assertNotIn("exe=<scratch>", detail)

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

    def test_seed_writing_malformed_json_is_refused_with_a_receipt(self) -> None:
        """`stage_write` caught only its own `Refusal`, so a seed emitting a
        truncated corpus raised `JSONDecodeError` out of `_regenerate` -- past
        the after-digest, past the receipt, and (through the adapter) out of
        `Controller().run`. A candidate is judged or it is not; it may not
        vanish."""
        source = (
            "from pathlib import Path\n"
            f"out = Path('data') / {CORPUS!r} / 'nodes.json'\n"
            "out.parent.mkdir(parents=True, exist_ok=True)\n"
            "out.write_text('{\"statement_nodes\": [', encoding='utf-8')\n"
        )
        record = self.stage(self.candidate(seed_source=source))
        self.assertRefusedBy(record, "regeneration_confinement")
        self.assertIn("not a corpus document", record.refusal["detail"])
        self.assertTrue(
            (self.repo.staging / f"{record.record_id}.json").is_file()
        )
        self.assertTrue(
            record.working_tree_digest_before == record.working_tree_digest_after
        )

    def test_an_unforeseen_crash_is_a_refusal_with_a_receipt(self) -> None:
        """The blanket guard behind the named ones.

        A corpus whose `statement_nodes` holds strings instead of objects is
        valid JSON, has the key the confinement check reads, and then raises
        `AttributeError` on `node.get` -- a shape no gate anticipated, which is
        the whole category the blanket guard exists for. It must still produce a
        judged, digested, scrubbed receipt rather than an exception.
        """
        source = (
            "import json\nfrom pathlib import Path\n"
            f"out = Path('data') / {CORPUS!r} / 'nodes.json'\n"
            "out.parent.mkdir(parents=True, exist_ok=True)\n"
            "out.write_text(json.dumps({'statement_nodes': ['not a node']}),"
            " encoding='utf-8')\n"
        )
        record = self.stage(self.candidate(seed_source=source))
        self.assertRefusedBy(record, "staging_crashed")
        self.assertIn("AttributeError", record.refusal["detail"])
        # Receipts stay diffable even when the gate is surprised.
        self.assertNotIn("write-stage-", record.refusal["detail"])
        self.assertNotIn(str(self.repo.root), record.refusal["detail"])
        payload = json.loads(
            (self.repo.staging / f"{record.record_id}.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(payload["working_tree_integrity"]["byte_identical"])
        self.assertIsNone(payload["staged"])

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
        self.assertEqual(record.correspondence["verdict"], "MISMATCH")
        self.assertIsNone(record.correspondence["matched_route"])
        # The decoy's proposition is what the candidate wanted judged; the
        # CITED theorem's is what was judged.
        self.assertEqual(
            record.correspondence["reference"], THEOREM
        )

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
        """Attack: prove theorem A, ship a node that cites theorem B.

        Refused at `candidate_link_shape`, not `semantic_correspondence`: no
        correspondence has been computed at this point, and naming the check
        after one put a `semantic_correspondence` refusal in the receipt beside
        a null `correspondence` field -- a receipt that reads as "the skeletons
        were compared and disagreed" when nothing was compared at all.
        """
        node = copy.deepcopy(NODE)
        node["verified_by"] = [
            {
                "system": "lean4",
                "artifact": ARTIFACT,
                "reference": "BooleanLaws.something_else",
            }
        ]
        record = self.stage(self.candidate(seed_source=seed_source(node)))
        self.assertRefusedBy(record, "candidate_link_shape")
        self.assertIsNone(record.correspondence)

    def test_candidate_node_with_no_verified_by_link_is_refused(self) -> None:
        node = copy.deepcopy(NODE)
        node["verified_by"] = []
        record = self.stage(self.candidate(seed_source=seed_source(node)))
        self.assertRefusedBy(record, "candidate_link_shape")
        self.assertIsNone(record.correspondence)

    def test_two_candidates_differing_only_in_rationale_get_two_receipts(
        self,
    ) -> None:
        """`record_id` names the receipt FILE, and `rationale` was not in the
        payload it digests -- so two candidates with the same proof and
        different justifications silently overwrote one another's receipt. The
        rationale is the one field a reviewer reads and no gate checks, which
        makes exactly that pair the one a reviewer must see both of."""
        first = self.stage(self.candidate(rationale="because it is a lattice law"))
        second = self.stage(self.candidate(rationale="because I say so"))
        self.assertNotEqual(first.record_id, second.record_id)
        self.assertTrue((self.repo.staging / f"{first.record_id}.json").is_file())
        self.assertTrue((self.repo.staging / f"{second.record_id}.json").is_file())
        self.assertEqual(
            first.staged["rationale"], "because it is a lattice law"
        )
        self.assertEqual(second.staged["rationale"], "because I say so")


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
        # Structured, not prose: the disagreement is visible in the receipt as
        # declared-versus-measured, which is the thing a reviewer audits.
        self.assertEqual(record.matcher_delta["declared"]["nodes_analyzed"], 0)
        self.assertEqual(record.matcher_delta["delta"]["nodes_analyzed"], 1)
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
        # The claimants come from the structured field, not from a sentence:
        # `ambiguous_with` is what a reviewer reads and what the gate acts on.
        self.assertEqual(
            record.correspondence["ambiguous_with"],
            [
                "logic.boolean_laws.idempotence",
                "settheory.boolean_laws.idempotence",
            ],
        )
        self.assertEqual(record.correspondence["verdict"], "CORRESPONDS")
        self.assertEqual(record.correspondence["matched_route"], "canonical")

    def test_delta_declared_with_the_wrong_type_is_refused(self) -> None:
        """Python's `True == 1`, and a JSON proposal is where `true` arrives."""
        for bad in (
            dict(EXPECTED_DELTA, nodes_analyzed=True),
            dict(EXPECTED_DELTA, shape_groups="0"),
            dict(EXPECTED_DELTA, typed_groups=0.0),
            # A tuple is not a list. JSON cannot produce one, so accepting it
            # widened only what an in-process caller could pass.
            dict(EXPECTED_DELTA, new_typed_twin_partners=()),
            dict(EXPECTED_DELTA, new_typed_twin_partners="none"),
            dict(EXPECTED_DELTA, new_typed_twin_partners=[1]),
        ):
            with self.subTest(bad=sorted(bad.items(), key=repr)):
                self.assertRefusedBy(
                    self.stage(self.candidate(expected_matcher_delta=bad)),
                    "matcher_delta_prediction",
                )

    def test_partial_delta_declaration_is_refused(self) -> None:
        self.assertRefusedBy(
            self.stage(
                self.candidate(expected_matcher_delta={"nodes_analyzed": 1})
            ),
            "matcher_delta_prediction",
        )

    def test_every_matcher_summary_key_is_gated(self) -> None:
        """Seven of the nine counters were gated, so `ladder_violations`,
        `parse_problems` and `slot_schema_gaps` were measured, recorded and
        never predicted. This pins the gate list to the summary itself, so a
        counter added to `_matcher_summary` cannot slip out of the prediction.
        """
        from write_stage import _MATCHER_DELTA_KEYS, _matcher_summary

        summary, _typed = _matcher_summary(self.repo.root / "data")
        self.assertEqual(
            set(_MATCHER_DELTA_KEYS),
            set(summary) | {"new_typed_twin_partners"},
        )
        self.assertEqual(set(EXPECTED_DELTA), set(_MATCHER_DELTA_KEYS))

    def test_an_undeclared_slot_schema_gap_is_refused(self) -> None:
        """The concrete escape the seven-of-nine gate allowed: a candidate
        whose node uses a template slot its `slot_schema` does not declare
        raises `slot_schema_gaps` by one and, before this fix, staged with
        that delta undeclared."""
        node = copy.deepcopy(NODE)
        # PROP1 rather than FALSITY: an undeclared slot defaults to
        # variable-like, which is what PROP1 already was, so nothing else about
        # the candidate moves -- correspondence, validation and every other
        # counter are unchanged and `slot_schema_gaps` is the only delta.
        node["structural_signature"]["slot_schema"] = [
            slot
            for slot in node["structural_signature"]["slot_schema"]
            if slot["slot_id"] != "PROP1"
        ]
        record = self.stage(self.candidate(seed_source=seed_source(node)))
        self.assertRefusedBy(record, "matcher_delta_prediction")
        self.assertIn("slot_schema_gaps", record.refusal["detail"])
        self.assertEqual(record.matcher_delta["delta"]["slot_schema_gaps"], 1)

    def test_the_receipt_carries_the_declared_delta_beside_the_measured_one(
        self,
    ) -> None:
        """`staging/README.md` said this field carried the prediction; it did
        not. The prediction survived only as free text in a PASS detail, so a
        receipt could not be audited for predicted-versus-measured without
        going back to the proposal file."""
        record = self.stage(self.candidate())
        self.assertEqual(record.matcher_delta["declared"], EXPECTED_DELTA)
        payload = json.loads(
            (self.repo.staging / f"{record.record_id}.json").read_text(
                encoding="utf-8"
            )
        )
        declared = payload["matcher_delta"]["declared"]
        measured = payload["matcher_delta"]["delta"]
        self.assertEqual(
            {key: declared[key] for key in sorted(declared)},
            {key: measured[key] for key in sorted(declared)},
        )

    def test_the_declared_delta_is_recorded_even_when_it_is_wrong(self) -> None:
        wrong = dict(EXPECTED_DELTA, nodes_analyzed=0)
        record = self.stage(self.candidate(expected_matcher_delta=wrong))
        self.assertRefusedBy(record, "matcher_delta_prediction")
        self.assertEqual(record.matcher_delta["declared"], wrong)
        self.assertEqual(record.matcher_delta["delta"]["nodes_analyzed"], 1)


class ControllerAdapterTests(WriteStageTestCase):
    """`ActionKind.WRITE` finally has an adapter, and it advances a LEDGER."""

    def proposal(self, name: str, **overrides) -> str:
        candidate = self.candidate(**overrides)
        payload = {
            "statement_id": candidate.statement_id,
            "corpus": candidate.corpus,
            "seed_script": candidate.seed_script,
            "seed_source": candidate.seed_source,
            "rung": candidate.rung,
            "rationale": candidate.rationale,
            "artifact": candidate.artifact,
            "artifact_sha256": candidate.artifact_sha256,
            "reference": candidate.reference,
            "transition_trace": list(candidate.transition_trace),
            "expected_matcher_delta": candidate.expected_matcher_delta,
            "frame_local": candidate.frame_local,
        }
        directory = self.repo.root / "proposals"
        directory.mkdir(exist_ok=True)
        (directory / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return f"proposals/{name}"

    def verifier(self):
        from write_stage import WriteStagingVerifier

        return WriteStagingVerifier(self.repo.root, self.repo.staging)

    def test_staged_candidate_advances_only_a_receipt_ledger(self) -> None:
        from controller import Verdict
        from write_stage import WriteStagingState, write_action

        verification = self.verifier().evaluate(
            WriteStagingState(), write_action(self.proposal("good.json"))
        )
        self.assertEqual(verification.verdict, Verdict.PROVEN)
        self.assertEqual(len(verification.next_state.receipts), 1)
        record_id, outcome = verification.next_state.receipts[0]
        self.assertEqual(outcome, STAGED_CANDIDATE)
        # The advanced state holds an id and an outcome. Nothing else fits.
        self.assertEqual(
            set(verification.next_state.__dataclass_fields__), {"receipts"}
        )
        self.assertTrue(
            (self.repo.staging / f"{record_id}.json").is_file()
        )

    def test_verified_rung_advances_as_verified(self) -> None:
        from controller import Verdict
        from write_stage import WriteStagingState, write_action

        verification = self.verifier().evaluate(
            WriteStagingState(),
            write_action(self.proposal("review.json", rung=VERIFIED)),
        )
        self.assertEqual(verification.verdict, Verdict.VERIFIED)
        self.assertEqual(
            verification.next_state.receipts[0][1], STAGED_REVIEW_REQUEST
        )

    def test_refused_candidate_cannot_mutate_the_ledger(self) -> None:
        from controller import Verdict
        from write_stage import WriteStagingState, write_action

        verification = self.verifier().evaluate(
            WriteStagingState(),
            write_action(self.proposal("bad.json", rung=CONJECTURED)),
        )
        self.assertEqual(verification.verdict, Verdict.REFUSED)
        self.assertIsNone(verification.next_state)
        verification.validate()

    def test_non_write_actions_and_bad_proposals_are_refused(self) -> None:
        from controller import Action, ActionKind, Verdict
        from write_stage import WriteStagingState, write_action

        verifier = self.verifier()
        cases = [
            Action.build(ActionKind.RETRIEVE, "lookup", {"key": "x"}),
            Action.build(ActionKind.WRITE, "stage", {}),
            write_action("../outside.json"),
            write_action("/etc/proposal.json"),
            write_action("data/logic/nodes.json"),
            write_action("proposals/absent.json"),
        ]
        for action in cases:
            with self.subTest(action=action.arguments):
                verification = verifier.evaluate(WriteStagingState(), action)
                self.assertEqual(verification.verdict, Verdict.REFUSED)
                self.assertIsNone(verification.next_state)

    def test_a_crashing_candidate_refuses_the_step_not_the_run(self) -> None:
        """`stage_write` sat OUTSIDE this adapter's `try`, so anything it
        raised propagated out of `Controller().run`: a WRITE that crashed was
        not a rejected step, it was an aborted loop and a lost ledger."""
        from controller import Controller, SequencePolicy, StopReason, Verdict
        from write_stage import WriteStagingState, write_action

        broken = (
            "from pathlib import Path\n"
            f"out = Path('data') / {CORPUS!r} / 'nodes.json'\n"
            "out.parent.mkdir(parents=True, exist_ok=True)\n"
            "out.write_text('{not json at all', encoding='utf-8')\n"
        )
        action = write_action(
            self.proposal("broken.json", seed_source=broken)
        )
        verification = self.verifier().evaluate(WriteStagingState(), action)
        self.assertEqual(verification.verdict, Verdict.REFUSED)
        self.assertIsNone(verification.next_state)
        result = Controller().run(
            WriteStagingState(),
            SequencePolicy([action]),
            self.verifier(),
            lambda state: False,
        )
        self.assertEqual(result.stop_reason, StopReason.EXHAUSTED)
        self.assertEqual(result.rejected_steps, 1)
        self.assertEqual(result.final_state.receipts, ())

    def test_an_unreadable_proposal_file_refuses_rather_than_raises(self) -> None:
        directory = self.repo.root / "proposals"
        directory.mkdir(exist_ok=True)
        from controller import Verdict
        from write_stage import WriteStagingState, write_action

        cases = {
            "not_json.json": "{ this is not json",
            "an_array.json": "[1, 2, 3]",
            "missing_keys.json": '{"statement_id": "x"}',
        }
        for name, text in cases.items():
            (directory / name).write_text(text, encoding="utf-8")
            with self.subTest(name=name):
                verification = self.verifier().evaluate(
                    WriteStagingState(), write_action(f"proposals/{name}")
                )
                self.assertEqual(verification.verdict, Verdict.REFUSED)
                self.assertIsNone(verification.next_state)

    def test_a_controller_run_stages_then_refuses_without_losing_state(
        self,
    ) -> None:
        from controller import Controller, SequencePolicy, StopReason
        from write_stage import WriteStagingState, write_action

        good = write_action(self.proposal("good.json"))
        bad = write_action(self.proposal("bad.json", rung=CONJECTURED))
        result = Controller().run(
            WriteStagingState(),
            SequencePolicy([good, bad]),
            self.verifier(),
            lambda state: False,
        )
        self.assertEqual(result.stop_reason, StopReason.EXHAUSTED)
        self.assertEqual(result.accepted_steps, 1)
        self.assertEqual(result.rejected_steps, 1)
        self.assertEqual(len(result.final_state.receipts), 1)
        self.assertEqual(
            durable_digest(self.repo.root / "data"), self.repo_data_digest
        )

    def setUp(self) -> None:
        super().setUp()
        self.repo_data_digest = durable_digest(self.repo.root / "data")


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _first_row(path: Path, theorem: str) -> dict:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return next(row for row in rows if row["theorem"] == theorem)


if __name__ == "__main__":
    unittest.main()
