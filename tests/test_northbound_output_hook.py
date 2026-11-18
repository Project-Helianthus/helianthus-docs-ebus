"""Pin the northbound output hook page.

Each case changes one field of the admission the page states. The checker
must reject that page. Fields and the wording change each case catches:

- direction: accepting `output` on a southbound descriptor
- spelling: accepting a name other than `output`
- cardinality: accepting more than the single name `output`
- hook version: accepting `output` at a version other than `1`
- absent version: accepting an `output` declaration with no version
- empty list: refusing an empty hook list
- southbound eeBUS registration: requiring that driver to declare `output`
- wrong direction: admitting `output` on a descriptor that is not northbound
- reserved names: accepting `mcp`, `setup`, `portal`, `semantic` or `evidence`
- other names: accepting a name that is neither `output` nor reserved
- refusal effect: installing a partial registry
- retained state: discarding last-known-good state
- publication: treating registration as publication of a fact
- lifecycle owner: moving start or stop off the driver manager
- disabled: starting a disabled descriptor
- health observed state: dropping observed state from the snapshot
- health reason: dropping reason from the snapshot
- health flag: dropping the safety-quarantine flag
- full driver object: reducing the MCP driver object to the three indicators
- reduced object: defining a separate reduced health object
- health surface: adding a second health API
- health GraphQL: naming a lifecycle GraphQL read for the snapshot
- health authority: citing the superseded driver runtime API page instead of
  the MCP lifecycle contract
- lens: restating the lens rules
- device choice: choosing which devices are published
- provenance label: dropping Proven, naming a Hypothesis, or emptying Unknown
- precedence: letting the registration page's empty-hook rule win for `output`
- precedence scope: widening the exception beyond the single name `output`
- precedence remainder: lifting the empty-hook rule for other names or
  directions
- owner narrowing: the lifecycle page drops, hides, moves or widens the
  narrowing it states right after its hook rejection paragraph
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts import check_northbound_output_hook as checker


ROOT = Path(__file__).resolve().parents[1]
TEXT = (ROOT / checker.DOCUMENT).read_text(encoding="utf-8")
OWNER_TEXT = (ROOT / checker.OWNER_DOCUMENT).read_text(encoding="utf-8")
NARROWING = checker.OWNER["paragraph"]
BLOCKS = [block for blocks in checker.REQUIREMENTS.values() for block in blocks]

# (field, exact wording, replacement that weakens that field)
MUTATIONS = (
    ("direction", "A northbound descriptor may register", "A southbound descriptor may register"),
    ("spelling", "may register the hook spelling `output`", "may register the hook spelling `outputs`"),
    ("cardinality", "the single name `output`", "several names"),
    ("hook version", "hook version `1`, the only supported\nversion", "any hook version, each a supported\nversion"),
    ("absent version", "with no version or with any other version\nfails", "with any other version\nfails"),
    ("empty list", "An empty hook list remains a valid registration", "An empty hook list is refused"),
    ("southbound eeBUS registration", "registers with an empty hook list, and that\nregistration stays valid", "must declare `output`, and that\nregistration stays valid"),
    ("wrong direction", "on a descriptor that is not\nnorthbound is refused", "on a descriptor that is not\nnorthbound is accepted"),
    ("reserved names", "`evidence` fail as unimplemented", "`evidence` are admitted"),
    ("other names", "fails as\nunknown", "is accepted"),
    ("refusal effect", "admits nothing", "installs a partial registry"),
    ("retained state", "last-known-good state unchanged", "last-known-good state discarded"),
    ("publication", "does not by itself publish a fact", "publishes a fact"),
    ("lifecycle owner", "existing driver-manager lifecycle", "a second lifecycle owner"),
    ("disabled", "A disabled\ndescriptor does not start", "A disabled\ndescriptor starts"),
    ("health observed state", "observed state, reason and", "reason and"),
    ("health reason", "observed state, reason and", "observed state and"),
    ("health flag", "the safety-quarantine flag", "a fresh counter"),
    ("health surface", "and no second\nhealth API.", "and a second\nhealth API reports liveness."),
    ("health GraphQL", "There is no lifecycle GraphQL API", "GraphQL also reads that snapshot"),
    ("health MCP read", "existing MCP driver object", "existing MCP and GraphQL surfaces"),
    ("full driver object", "which keeps every\nmember that contract lists", "which keeps only these\nthree members"),
    ("reduced object", "this page defines no reduced object", "this page defines a reduced object"),
    ("lens", "does not restate the lens rules", "restates the lens rules"),
    ("device choice", "does not choose which devices\nare published", "chooses which devices\nare published"),
    ("provenance Proven", "**Proven** means a fact", "**Proven** names nothing"),
    ("provenance Hypothesis", "**Hypothesis**\nnames nothing on this page", "**Hypothesis**\nnames a second hook on this page"),
    ("provenance Unknown", "**Unknown** names device publication", "**Unknown** names nothing"),
    ("precedence", "this page\ntakes precedence over that rule", "that rule\ntakes precedence over this page"),
    ("precedence scope", "narrows that rule for one\nname only", "lifts that rule for every\nname"),
    ("precedence remainder", "that rule stands unchanged", "that rule no longer applies"),
)


class NorthboundOutputHookTest(unittest.TestCase):
    def test_repository_matches_pin(self) -> None:
        self.assertEqual(checker.validate(TEXT), [])

    def test_each_block_is_visible_once(self) -> None:
        for block in BLOCKS:
            with self.subTest(block=block[:48]):
                self.assertEqual(TEXT.count(block), 1)
                self.assertTrue(checker.validate(TEXT.replace(block, "")))
                fenced = TEXT.replace(block, f"```text\n{block}\n```")
                self.assertTrue(checker.validate(fenced))
                hidden = TEXT.replace(block, f"<!--\n{block}\n-->")
                self.assertTrue(checker.validate(hidden))
                relocated = TEXT.replace(block, "") + "\n\n## Other\n\n" + block
                self.assertTrue(checker.validate(relocated))

    def test_field_mutations(self) -> None:
        for field, before, after in MUTATIONS:
            with self.subTest(field=field):
                self.assertIn(before, TEXT)
                self.assertEqual(TEXT.count(before), 1)
                self.assertTrue(checker.validate(TEXT.replace(before, after)))

    def test_added_graphql_health_claim(self) -> None:
        for claim in (
            "That snapshot is also the health read on GraphQL.",
            "```text\nignored\n```\n\nA GraphQL query returns the observed state.",
        ):
            with self.subTest(claim=claim[:32]):
                errors = checker.validate(TEXT + "\n" + claim + "\n")
                self.assertTrue(any(e.startswith("GraphQL health claim") for e in errors))

    def test_health_authority_is_mcp_contract(self) -> None:
        authority = "(../api/mcp.md#g5-runtime-lifecycle-mcp-contract-d4)"
        self.assertEqual(TEXT.count(authority), 1)
        self.assertNotIn(checker.SUPERSEDED, TEXT)
        for claim in (
            TEXT.replace(authority, "(../api/driver-runtime-v1.md)"),
            TEXT + "\nSee the [driver API](../api/driver-runtime-v1.md).\n",
        ):
            with self.subTest(claim=claim[-48:]):
                errors = checker.validate(claim)
                self.assertTrue(
                    any(e.startswith("superseded authority cited") for e in errors)
                )

    def test_rewrapping_stays_valid(self) -> None:
        changed = TEXT
        for block in BLOCKS:
            changed = changed.replace(block, checker.normalize(block))
        self.assertEqual(checker.validate(changed), [])

    def test_missing_section(self) -> None:
        for heading in checker.REQUIREMENTS:
            with self.subTest(heading=heading):
                before, section = TEXT.split(f"## {heading}\n\n", 1)
                parts = section.split("\n## ", 1)
                remainder = "\n## " + parts[1] if len(parts) == 2 else ""
                self.assertTrue(checker.validate(before + remainder))

    def test_owner_states_narrowing(self) -> None:
        self.assertEqual(TEXT.count("hook version `1`"), 1)
        self.assertEqual(OWNER_TEXT.count(NARROWING), 1)
        self.assertEqual(checker.validate_owner(OWNER_TEXT), [])
        rule = checker.REGISTRATION[checker.OWNER["follows"]]
        moved = OWNER_TEXT.replace(NARROWING, "").replace(rule, NARROWING + "\n\n" + rule)
        for name, changed in (
            ("dropped", OWNER_TEXT.replace(NARROWING, "")),
            ("hidden", OWNER_TEXT.replace(NARROWING, f"<!--\n{NARROWING}\n-->")),
            ("fenced", OWNER_TEXT.replace(NARROWING, f"```text\n{NARROWING}\n```")),
            ("moved", moved),
            ("version", OWNER_TEXT.replace("at hook version `1`", "at any hook version")),
            ("direction", OWNER_TEXT.replace("a northbound descriptor may", "any descriptor may")),
            ("remainder", OWNER_TEXT.replace("still fails as stated above", "is also accepted")),
        ):
            with self.subTest(owner=name):
                self.assertNotEqual(changed, OWNER_TEXT)
                self.assertTrue(checker.validate_owner(changed))

    def test_cli(self) -> None:
        checker_path = ROOT / "scripts" / "check_northbound_output_hook.py"
        weakened = TEXT.replace("the single name `output`", "several names")
        owner_dropped = OWNER_TEXT.replace(NARROWING, "")
        with tempfile.TemporaryDirectory(prefix="northbound-output-hook-") as tmp:
            root = Path(tmp)
            document = root / checker.DOCUMENT
            document.parent.mkdir(parents=True)
            owner = root / checker.OWNER_DOCUMENT
            owner.parent.mkdir(parents=True, exist_ok=True)
            for text, owner_text, expected in (
                (TEXT, OWNER_TEXT, 0),
                (weakened, OWNER_TEXT, 1),
                (TEXT, owner_dropped, 1),
            ):
                document.write_text(text, encoding="utf-8")
                owner.write_text(owner_text, encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(checker_path), "--root", str(root)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, expected, result.stderr)

    def test_cli_missing_page(self) -> None:
        checker_path = ROOT / "scripts" / "check_northbound_output_hook.py"
        with tempfile.TemporaryDirectory(prefix="northbound-output-hook-") as tmp:
            result = subprocess.run(
                [sys.executable, str(checker_path), "--root", tmp],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing architecture/northbound-output-hook.md", result.stderr)
        self.assertIn("missing architecture/runtime-driver-lifecycle.md", result.stderr)


if __name__ == "__main__":
    unittest.main()
