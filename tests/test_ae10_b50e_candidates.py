"""Explicit acceptance checks for native candidate declarations, not a decoder."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-vaillant-B50E.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ae10_b50e_candidates.json'


def tables(text):
    """Read Markdown cells so grade and caveats stay attached to their row."""
    result = []
    for line in text.splitlines():
        if line.startswith('|'):
            result.append(tuple(cell.strip() for cell in line.strip('|').split('|')))
    return result


class B50ECandidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.page = PAGE.read_text()
        cls.rows = tables(cls.page)

    def test_finite_declarations_and_all_identity_axes(self):
        expected = [
            {'identity': {'family': 'vaillant', 'variant': 'B50E', 'primary': 181,
                          'secondary': 14, 'operation': None, 'direction': None,
                          'field': 'rule_comparison'},
             'grade': 'Hypothesis', 'logical_position': None, 'width_bits': 8,
             'scale': 1, 'unit': None, 'default': None, 'sentinel': None,
             'mode_mask': 7, 'stop_override_fifo_mask': 128, 'unresolved_mask': 120,
             'flag_scope': 'all scalar modes on rule match', 'raw_preserved': True},
            {'identity': {'family': 'vaillant', 'variant': 'B50E', 'primary': 181,
                          'secondary': 14, 'operation': 1, 'direction': 'response',
                          'field': 'clear_rule_positive_index'},
             'grade': 'Hypothesis', 'logical_position': None, 'width_bits': 16,
             'scale': 1, 'unit': None, 'default': None, 'byte_order': 'little_endian',
             'unsigned': True, 'sentinel': 65535, 'sentinel_scope': 'OP01 positive echo only',
             'echo_optional': True, 'deletion': 'Unknown', 'persistence': 'Unknown',
             'raw_preserved': True},
        ]
        self.assertEqual(self.fixture['entries'], expected)
        self.assertEqual(self.fixture['metadata_presence'], 'Proven')
        self.assertEqual(self.fixture['physical_qualification'], 'Unknown')
        self.assertEqual(self.fixture['provenance'], 'synthetic only; no device observation')

    def test_structured_declarations_grade_conflict_and_unknowns(self):
        expected = [
            ('Hypothesis', 'vaillant / B50E / PB=B5 / SB=0E / OP=Unknown / rule_comparison',
             'Unknown', 'Unknown / 8 bits',
             'uint8; full byte 00..FF; scalar bits 0..2, modes 0..7; bit 7 independent stop-override-FIFO on match',
             '1 / none',
             'No sentinel or default established; high flag applies across all modes, not only mode 7',
             'Bits 3..6 (mask 78) unresolved; preserve full raw byte; physical prefix adaptation Unknown'),
            ('Hypothesis', 'vaillant / B50E / PB=B5 / SB=0E / OP=01 / clear_rule_positive_index',
             'response (positive candidate)', 'Unknown / 16 bits',
             'uint16 unsigned little-endian; 0..65535; optional echo', '1 / none',
             'FFFF (65535) may mean all rules cleared only in this OP01 positive echo form; no default established; other operations have no clear meaning here',
             'One-byte echo incomplete/raw; echo presence does not establish physical deletion or persistence; physical prefix adaptation Unknown'),
        ]
        declarations = [r for r in self.rows if any(' / B50E / ' in c for c in r)]
        self.assertEqual(declarations, expected)
        self.assertIn('a logical position is not a wire offset', self.page)
        self.assertIn('[synthetic examples](fixtures/ae10_b50e_candidates.json)', self.page)
        self.assertNotIn('With mode `7`, the most significant bit', self.page)
        self.assertNotIn('rule index; `FFFF` clears all rules', self.page)
        self.assertNotIn('The reply layout of operation `01` is not established.', self.page)
        self.assertIn('Request sentinel semantics are Unknown.', self.page)
        self.assertIn('Rule-table\ndeclarations are separate from active rule execution.', self.page)
        self.assertIn('Native recording,\nother rule fields and checksum/stuffing semantics remain Unknown.', self.page)

    def test_comparison_examples_independent_expected_tuples_and_arithmetic(self):
        expected = [('00', 0, False, 0, 'Hypothesis'), ('07', 7, False, 0, 'Hypothesis'),
                    ('80', 0, True, 0, 'Hypothesis'), ('87', 7, True, 0, 'Hypothesis'),
                    ('88', 0, True, 8, 'Hypothesis')]
        actual = [(c['raw'], c['mode'], c['high_flag'], c['unresolved_bits'], c['grade'])
                  for c in self.fixture['comparison_cases']]
        self.assertEqual(actual, expected)
        page_expected = [('00', '0', 'false', '00', 'Hypothesis'),
                         ('07', '7', 'false', '00', 'Hypothesis'),
                         ('80', '0', 'true', '00', 'Hypothesis'),
                         ('87', '7', 'true', '00', 'Hypothesis'),
                         ('88', '0', 'true', '08', 'Hypothesis')]
        self.assertEqual([r for r in self.rows if len(r) == 5 and r[0] in
                          {'00', '07', '80', '87', '88'}], page_expected)
        # Arithmetic checks the published examples; it is not production decoding.
        for raw, mode, flag, reserved, _ in actual:
            with self.subTest(raw=raw):
                self.assertEqual(int(raw, 16), mode + reserved + (128 if flag else 0))
        self.assertEqual(0x34 + 256 * 0x12, 4660)
        self.assertEqual(0xFF + 256 * 0xFF, 65535)

    def test_echo_examples_keep_operation_and_completeness(self):
        expected = [(1, 'positive response', '34 12', 4660, False,
                     'complete candidate carrier', 'Hypothesis'),
                    (1, 'positive response', 'FF FF', 65535, True,
                     'complete candidate carrier', 'Hypothesis'),
                    (1, 'positive response', 'FF', None, None, 'incomplete/raw', 'Unknown'),
                    (2, 'positive response', 'FF FF', None, None,
                     'raw; outside clear candidate', 'Unknown')]
        self.assertEqual([(c['operation'], c['direction'], c['raw'], c['index'],
                           c['all_rules'], c['completeness'], c['grade'])
                          for c in self.fixture['echo_cases']], expected)
        page_expected = [('01', 'positive response', '34 12', '4660', 'false',
                          'complete candidate carrier', 'Hypothesis'),
                         ('01', 'positive response', 'FF FF', '65535', 'true',
                          'complete candidate carrier', 'Hypothesis'),
                         ('01', 'positive response', 'FF', 'Unknown', 'Unknown',
                          'incomplete/raw', 'Unknown'),
                         ('02', 'positive response', 'FF FF', 'Unknown', 'Unknown',
                          'raw; outside clear candidate', 'Unknown')]
        self.assertEqual([r for r in self.rows if len(r) == 7 and
                          r[1] == 'positive response'], page_expected)


if __name__ == '__main__':
    unittest.main()
