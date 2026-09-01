"""The big-operator capture is disclosed in the term's own receipt, never silent.

`parse_atom` rewrites any identifier whose lowercase begins with one of
`BIG_OP_PREFIXES` into a bare big-operator call: `sum_i x` becomes
`("call", "sum", (x,))`. That rule is load-bearing for the corpus — sixteen
committed templates write `sum_i` and one writes `lim_h` — but it is a *lossy*
rule, and until v0.25 it was a **silent** one. The suffix after the underscore
was discarded with no record anywhere, so a person-authored `sum_total(x)` and
a person-authored `sum_anything(x)` produced the identical tree and the
identical skeleton, and nothing a reader could open said that a rewrite had
happened at all.

ROADMAP-v0.25 §2 fixes the acceptance for this lane: *a refusal or a
disclosure, never a silent rewrite* — either the parser refuses the capture by
name, or the rewrite is recorded in the term's own receipt where a reader can
see it. The census decided the arm: a refusal would break seventeen sealed
committed parses, so the arm is **disclosure**, and the disclosure is
**total** — every rewrite is recorded, the innocent `sum_i` exactly as loudly
as the surprising `sum_total`. Totality is what makes it judgment-free: the
parser never decides which captures are suspicious, because deciding that
would be a new authored rule this lane did not price.

The tests below fence both directions:

* the hazard direction — a `sum_total`-shaped identifier discloses the
  capture, naming the token verbatim and the suffix it lost;
* the regression direction — a genuine `sum_i` still parses to exactly the
  tree it always did, *and* now carries its own disclosure row; and a parse
  with no capture in it carries an empty list, so no committed receipt grows
  a field it did not have.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from match_signatures import (  # noqa: E402
    BIG_OP_PREFIXES,
    Parser,
    canonicalize,
    load_nodes,
    tokenize,
)


def parse(text: str) -> tuple[tuple, list[dict]]:
    """The tree and the parser's rewrite record, together."""

    parser = Parser(tokenize(text))
    tree = parser.parse()
    return tree, parser.rewrites


_CORPUS: list | None = None


def corpus() -> list:
    """`load_nodes` over `data/` costs ~87s; four tests read it, so read it once."""

    global _CORPUS
    if _CORPUS is None:
        nodes, _ = load_nodes(REPO_ROOT / "data")
        _CORPUS = nodes
    return _CORPUS


def captured_tokens(template: str) -> list[str]:
    """The identifiers in `template` the big-op branch will capture."""

    return [
        tok
        for tok in tokenize(template)
        if tok[:1].isalpha() and tok.lower().startswith(BIG_OP_PREFIXES)
    ]


class BigOpCaptureIsDisclosed(unittest.TestCase):
    """The hazard direction: a captured word-suffix identifier says so."""

    def test_sum_total_discloses_the_capture_it_performs(self) -> None:
        tree, rewrites = parse("sum_total(x)")

        # The capture still happens — this lane changes the record, not the
        # tree — but it is no longer silent.
        self.assertEqual(tree, ("call", "sum", (("slot", "x"),)))
        self.assertEqual(len(rewrites), 1, f"expected one disclosed rewrite, got {rewrites!r}")
        row = rewrites[0]
        self.assertEqual(row["token"], "sum_total")
        self.assertEqual(row["head"], "sum")
        self.assertEqual(row["discarded"], "total")
        self.assertEqual(row["rule"], "BIG_OP_PREFIXES")
        self.assertEqual(row["token_index"], 0)

    def test_two_distinct_identifiers_are_told_apart_by_their_records(self) -> None:
        """The exact collapse the review found: same tree, different receipt.

        `sum_total` and `sum_anything` still canonicalize to one tree — that is
        the rewrite doing its job — so the tree can never distinguish them. The
        disclosure is the only place the difference survives, which is why the
        acceptance asks for a record rather than for a different tree.
        """

        total_tree, total_rewrites = parse("sum_total(x)")
        anything_tree, anything_rewrites = parse("sum_anything(x)")

        self.assertEqual(canonicalize(total_tree), canonicalize(anything_tree))
        self.assertNotEqual(total_rewrites, anything_rewrites)
        self.assertEqual(
            [r["token"] for r in total_rewrites], ["sum_total"]
        )
        self.assertEqual(
            [r["token"] for r in anything_rewrites], ["sum_anything"]
        )

    def test_every_reserved_prefix_discloses(self) -> None:
        """Totality across the reserved set, not a special case for `sum_`."""

        for prefix in BIG_OP_PREFIXES:
            with self.subTest(prefix=prefix):
                _, rewrites = parse(f"{prefix}total(x)")
                self.assertEqual(len(rewrites), 1)
                self.assertEqual(rewrites[0]["token"], f"{prefix}total")
                self.assertEqual(rewrites[0]["head"], prefix[:-1])
                self.assertEqual(rewrites[0]["discarded"], "total")


class GenuineBigOpsKeepTheirTreesAndGetRecords(unittest.TestCase):
    """The regression direction: the corpus's own usage is unmoved and total."""

    def test_sum_i_parses_to_the_tree_it_always_did(self) -> None:
        tree, rewrites = parse("sum_i x")
        self.assertEqual(tree, ("call", "sum", (("slot", "x"),)))
        self.assertEqual(len(rewrites), 1)
        self.assertEqual(rewrites[0]["token"], "sum_i")
        self.assertEqual(rewrites[0]["head"], "sum")
        self.assertEqual(rewrites[0]["discarded"], "i")

    def test_a_parse_with_no_capture_records_nothing(self) -> None:
        """Empty is empty — the guard that keeps committed receipts byte-stable."""

        for text in ("a + b", "f(x, y)", "summation(x)", "maximal", "P[a | b]"):
            with self.subTest(text=text):
                _, rewrites = parse(text)
                self.assertEqual(rewrites, [])

    def test_several_captures_in_one_template_are_all_recorded(self) -> None:
        tree, rewrites = parse("sum_i x + prod_j y")
        self.assertEqual(len(rewrites), 2)
        self.assertEqual(
            [(r["token"], r["head"]) for r in rewrites],
            [("sum_i", "sum"), ("prod_j", "prod")],
        )
        self.assertLess(rewrites[0]["token_index"], rewrites[1]["token_index"])


class TheCorpusReceiptsCarryTheDisclosure(unittest.TestCase):
    """The receipt side: a term whose parse was rewritten says so on its row."""

    def test_committed_nodes_disclose_their_captures(self) -> None:
        nodes = corpus()
        disclosed = {
            node.statement_id: [r["token"] for r in node.parse_rewrites]
            for node in nodes
            if node.parse_rewrites
        }
        self.assertTrue(
            disclosed, "the committed corpus contains big-op captures; none disclosed"
        )
        tokens = sorted({t for toks in disclosed.values() for t in toks})
        # The census taken for this lane: `sum_i` in sixteen templates and
        # `lim_h` in one, and nothing else in 14,830 committed templates.
        self.assertEqual(tokens, ["lim_h", "sum_i"])

    def test_uncaptured_nodes_carry_an_empty_record(self) -> None:
        nodes = corpus()
        clean = [node for node in nodes if not node.parse_rewrites]
        self.assertTrue(clean)
        for node in clean[:50]:
            self.assertEqual(node.parse_rewrites, [])

    def test_the_record_agrees_with_the_template_it_came_from(self) -> None:
        """Totality, checked against the corpus rather than declared.

        Every node whose template contains a capturable identifier has a
        record naming exactly those identifiers, and no node without one has a
        record. This is the assertion that would go red if the disclosure ever
        became selective.
        """

        for node in corpus():
            expected = captured_tokens(node.template)
            self.assertEqual(
                [row["token"] for row in node.parse_rewrites],
                expected,
                f"{node.statement_id}: {node.template!r}",
            )


class TheWrittenReportPublishesTheDisclosure(unittest.TestCase):
    """The committed ledger is where a reader actually looks.

    Two places, because they answer different questions. The top-level
    `parse_rewrites` section is the **total** one — every captured statement in
    the corpus, whether or not it landed in a twin group — and it sits beside
    `parse_problems`, the section that already exists to tell a reader what the
    parser wants them to know. The per-member field is the **local** one: a
    twin group is exactly where a reader sees two templates collapse into one
    skeleton, so it is exactly where the note that one of them got there by a
    lossy rewrite has to appear.
    """

    REPORT = REPO_ROOT / "reports" / "signature_matches.json"

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = json.loads(cls.REPORT.read_text(encoding="utf-8"))

    def test_the_report_carries_a_total_parse_rewrites_section(self) -> None:
        section = self.report["parse_rewrites"]
        self.assertTrue(section, "the corpus has captures; the section is empty")
        by_id = {row["statement_id"]: row for row in section}
        self.assertEqual(
            len(by_id), len(section), "a statement disclosed twice"
        )
        for row in section:
            self.assertEqual(
                [r["token"] for r in row["rewrites"]],
                captured_tokens(row["template"]),
                row["statement_id"],
            )
        tokens = sorted({r["token"] for row in section for r in row["rewrites"]})
        self.assertEqual(tokens, ["lim_h", "sum_i"])

    def test_the_section_is_sorted_so_the_diff_is_readable(self) -> None:
        ids = [row["statement_id"] for row in self.report["parse_rewrites"]]
        self.assertEqual(ids, sorted(ids))

    def test_captured_members_carry_parse_rewrites_and_clean_ones_do_not(self) -> None:
        seen_captured = False
        # Every group section, including the two spelled
        # `*_twin_groups_beyond_typed`; an `endswith` filter silently skips
        # those two and fences half of what it claims to fence.
        sections = [k for k in self.report if "twin_groups" in k]
        self.assertEqual(len(sections), 5, sections)
        for key in sections:
            groups = self.report[key]
            for group in groups:
                for member in group.get("members", []):
                    if captured_tokens(member["template"]):
                        seen_captured = True
                        self.assertIn(
                            "parse_rewrites",
                            member,
                            f"{member['statement_id']} was rewritten with no record",
                        )
                        self.assertEqual(
                            [r["token"] for r in member["parse_rewrites"]],
                            captured_tokens(member["template"]),
                        )
                    else:
                        self.assertNotIn(
                            "parse_rewrites",
                            member,
                            f"{member['statement_id']} grew an empty record",
                        )
        self.assertTrue(
            seen_captured,
            "no captured member found in the committed report; the fence is not fencing",
        )


if __name__ == "__main__":
    unittest.main()
