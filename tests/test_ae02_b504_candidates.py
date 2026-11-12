"""Explicit acceptance checks for synthetic B504 declarations, not runtime coverage."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "protocols/vaillant/ebus-vaillant-b504.md"
FIXTURE = ROOT / "protocols/vaillant/fixtures/ae02_b504_candidates.json"
EXPECTED_COLUMNS = ['ID',
 'Grade',
 'Identity',
 'Direction',
 'Logical position / extent',
 'Raw type / domain',
 'Scale',
 'Sentinel / default / conflict',
 'Unresolved properties']
EXPECTED_CLAIMS = [('op16-div16',
  'Hypothesis',
  'OP16 corrected outside temperature /16',
  'response',
  'logical 3; 16 bits',
  'i16 LE; -32768..32767',
  'raw / 16 °C',
  'Default and sentinels Unknown; /256 is a separate unqualified alternative',
  'Physical adaptation, installed support and polling permission Unknown; reply length '
  'cannot select variant'),
 ('op16-div256',
  'Hypothesis',
  'OP16 corrected outside temperature /256',
  'response',
  'logical 3; 16 bits',
  'i16 LE; -32768..32767',
  'raw / 256 °C',
  'Default and sentinels Unknown; separate unqualified alternative to /16',
  'Physical adaptation, installed support and polling permission Unknown; reply length '
  'cannot select variant'),
 ('op16-tail',
  'Unknown',
  'OP16 unused tail',
  'response',
  'position Unknown; extent Unknown',
  'raw bytes; domain Unknown',
  'Unknown',
  'Default and sentinels Unknown; no fixed trailing offset',
  'Meaning, physical adaptation, installed support and polling permission Unknown'),
 ('op20-setpoint',
  'Hypothesis',
  'OP20 setpoint',
  'response',
  'position Unknown; extent Unknown',
  'zero or nonzero; raw type Unknown',
  'Nonzero includes declared offsets; exact arithmetic Unknown',
  '0 = no-demand; default and other sentinels Unknown',
  'Physical adaptation, installed support and polling permission Unknown'),
 ('op21-protection',
  'Hypothesis',
  'OP21 protection temperature',
  'response',
  'position Unknown; extent Unknown',
  'zero or positive; raw type Unknown',
  'Unknown',
  '0 = off; positive = protection-active; default and other sentinels Unknown',
  'Physical adaptation, installed support and polling permission Unknown'),
 ('op26-adjustment',
  'Hypothesis',
  'OP26 adjustment flag',
  'response',
  'position Unknown; extent Unknown',
  'flag; other raw values Unknown',
  'Unknown',
  '1 = permits setpoint change; default and other sentinels Unknown',
  'Physical adaptation, installed support and polling permission Unknown; no writable '
  'contract established'),
 ('op26-room',
  'Hypothesis',
  'OP26 room temperature',
  'response',
  'position Unknown; extent Unknown',
  'FF; remaining raw domain Unknown',
  'Unknown',
  'FF = unavailable only in this context; default and other sentinels Unknown',
  'Other selectors inherit no FF label; physical adaptation, installed support and '
  'polling permission Unknown'),
 ('solar-three',
  'Hypothesis',
  'solar-state scalar 0/1/2',
  'response',
  'position Unknown; extent Unknown',
  'scalar codes {0,1,2}',
  'None declared',
  'Competing bit descriptions remain separate; default and sentinels Unknown',
  'Exact selector binding, physical adaptation, installed support and polling '
  'permission Unknown'),
 ('solar-two',
  'Hypothesis',
  'solar-state scalar 0/1',
  'response',
  'position Unknown; extent Unknown',
  'scalar codes {0,1}',
  'None declared',
  'Code 2 outside this table; competing bit descriptions separate; default and '
  'sentinels Unknown',
  'Exact selector binding, physical adaptation, installed support and polling '
  'permission Unknown'),
 ('preheat-five',
  'Hypothesis',
  'preheating five-minute variant',
  'response',
  'position Unknown; extent Unknown',
  'duration 0..60 minutes; step 5; raw type Unknown',
  'Raw conversion Unknown',
  'Separate from 0..300 alternative; default and sentinels Unknown',
  'Exact selector binding, physical adaptation, installed support and polling '
  'permission Unknown'),
 ('preheat-300',
  'Hypothesis',
  'preheating 300-minute variant',
  'response',
  'position Unknown; extent Unknown',
  'duration 0..300 minutes; step Unknown; raw type Unknown',
  'Raw conversion Unknown',
  'Separate from five-minute alternative; default and sentinels Unknown',
  'Exact selector binding, physical adaptation, installed support and polling '
  'permission Unknown')]
EXPECTED_CASES = {'temperature': [{'raw_hex': '10 00', 'signed': 16, 'div16': 1.0, 'div256': 0.0625},
                 {'raw_hex': 'F0 FF', 'signed': -16, 'div16': -1.0, 'div256': -0.0625}],
 'setpoint': [{'op': '20', 'raw': 0, 'meaning': 'no-demand'},
              {'op': '20', 'raw': 1, 'meaning': 'nonzero-candidate'}],
 'protection': [{'op': '21', 'raw': 0, 'meaning': 'off'},
                {'op': '21', 'raw': 1, 'meaning': 'protection-active'}],
 'adjustment': [{'op': '26', 'raw': 1, 'meaning': 'permits-setpoint-change'}],
 'room': [{'op': '26', 'raw_hex': 'FF', 'meaning': 'unavailable'},
          {'op': '20', 'raw_hex': 'FF', 'meaning': None}],
 'duration': [{'minutes': 60, 'five_minute': True, 'alternative_300': True},
              {'minutes': 65, 'five_minute': False, 'alternative_300': True},
              {'minutes': 300, 'five_minute': False, 'alternative_300': True}],
 'solar': [{'code': 0, 'three_value': True, 'two_value': True},
           {'code': 1, 'three_value': True, 'two_value': True},
           {'code': 2, 'three_value': True, 'two_value': False}]}


class B504CandidateAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.page = PAGE.read_text()

    def test_structured_claims_and_nearby_grade_conflict_unknowns(self):
        self.assertEqual(self.fixture["columns"], EXPECTED_COLUMNS)
        self.assertEqual([tuple(row) for row in self.fixture["claims"]], EXPECTED_CLAIMS)
        section = self.page.split("## Bounded read candidate declarations\n", 1)[1].split("## Profiles", 1)[0]
        table = [tuple(cell.strip() for cell in line.strip("|").split("|"))
                 for line in section.splitlines() if line.startswith("| ")]
        self.assertEqual(table, [tuple(EXPECTED_COLUMNS), *EXPECTED_CLAIMS])
        self.assertIn("[synthetic field cases](fixtures/ae02_b504_candidates.json)", section)
        self.assertIn("A logical position is not a wire offset", section)
        self.assertNotIn("whose reply ends with a field to the end", self.page)
        self.assertNotIn("The divisor of the `B5 04 16`", self.page)

    def test_explicit_absent_metadata_and_qualification(self):
        self.assertEqual(self.fixture["qualification"], "Unknown")
        self.assertEqual(self.fixture["absent_metadata"], {
            "physical_adaptation": None, "installed_support": None,
            "polling_permission": None, "wire_offsets": None})

    def test_signed_little_endian_and_independent_divisors(self):
        self.assertEqual(self.fixture["cases"]["temperature"], EXPECTED_CASES["temperature"])
        for case, expected in zip(self.fixture["cases"]["temperature"],
                                  [(16, 1.0, 0.0625), (-16, -1.0, -0.0625)]):
            with self.subTest(raw=case["raw_hex"]):
                signed = int.from_bytes(bytes.fromhex(case["raw_hex"]), "little", signed=True)
                self.assertEqual((signed, signed / 16, signed / 256), expected)

    def test_zero_positive_and_adjustment_branches(self):
        for name in ("setpoint", "protection", "adjustment"):
            with self.subTest(field=name):
                self.assertEqual(self.fixture["cases"][name], EXPECTED_CASES[name])

    def test_selector_alone_changes_ff_context(self):
        cases = self.fixture["cases"]["room"]
        self.assertEqual(cases, EXPECTED_CASES["room"])
        self.assertEqual(cases[0]["raw_hex"], cases[1]["raw_hex"])
        self.assertEqual([(c["op"], c["meaning"]) for c in cases],
                         [("26", "unavailable"), ("20", None)])

    def test_duration_alternatives_are_not_a_union(self):
        cases = self.fixture["cases"]["duration"]
        self.assertEqual(cases, EXPECTED_CASES["duration"])
        self.assertEqual([(c["minutes"], c["five_minute"], c["alternative_300"]) for c in cases],
                         [(60, True, True), (65, False, True), (300, False, True)])

    def test_solar_domains_remain_distinct(self):
        cases = self.fixture["cases"]["solar"]
        self.assertEqual(cases, EXPECTED_CASES["solar"])
        self.assertEqual([(c["code"], c["three_value"], c["two_value"]) for c in cases],
                         [(0, True, True), (1, True, True), (2, True, False)])


if __name__ == "__main__":
    unittest.main()
