"""Explicit document/fixture acceptance checks; no runtime decoder coverage."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
NATIVE = 'protocols/ebus-services/ebus-service-07h.md'
ARCH = 'architecture/ae26-0704-local-parser.md'
FIXTURE = 'protocols/ebus-services/fixtures/ae26_07_candidates.json'


def rows(text):
    return [tuple(cell.strip() for cell in line.strip('|').split('|'))
            for line in text.splitlines() if line.startswith('|')]


class CandidateAcceptance(unittest.TestCase):
    def setUp(self):
        self.native = (ROOT / NATIVE).read_text()
        self.arch = (ROOT / ARCH).read_text()
        self.fixture = json.loads((ROOT / FIXTURE).read_text())

    def test_native_structured_claims(self):
        scoped = self.native.split('#### Bounded 0704 candidate declarations\n', 1)[1].split('**Broadcast', 1)[0]
        expected = [
            ('Hypothesis', '0704; identifier', 'response', 'Unknown / Unknown', 'Unknown', 'Unknown', 'No sentinel established', 'Native extent and character domain Unknown'),
            ('Hypothesis', '0704; major', 'response', 'Unknown / Unknown', 'Unknown', 'Unknown', 'No sentinel established', 'Native representation Unknown'),
            ('Hypothesis', '0704; minor', 'response', 'Unknown / Unknown', 'Unknown', 'Unknown', 'No sentinel established', 'Native representation Unknown'),
            ('Hypothesis', '0704; product_number', 'response', 'Unknown / Unknown', 'Unknown', 'Unknown', 'Alternative to hardware version/revision interpretation', 'Family predicates and native representation Unknown'),
            ('Hypothesis', '0704; version_control', 'response', '8 / Unknown', 'candidate control domain 0..98 not-okay', 'Unknown', 'Default not-okay; no okay value established', 'Overlap at logical position 8; physical placement Unknown'),
            ('Hypothesis', '0704; revision_control', 'response', '9 / Unknown', 'candidate control domain 0..98 not-okay', 'Unknown', 'Default not-okay; no okay value established', 'Overlap at logical position 9; physical placement Unknown'),
            ('Hypothesis', '07FE; existence_inquiry', 'request', 'Unknown / Unknown', 'empty request', 'None', 'Direct reply not required; missing direct response is not identification failure', 'Installed support Unknown'),
        ]
        self.assertEqual(rows(scoped)[2:], expected)
        self.assertIn('Control value 99 has no established okay meaning.', scoped)
        self.assertIn('A logical position is not a wire offset', scoped)
        self.assertIn('(fixtures/ae26_07_candidates.json)', scoped)
        self.assertIn('The partial local-parser behaviour is described in the application architecture documentation.', scoped)
        self.assertNotIn('architecture/', self.native)

    def test_local_structured_claims(self):
        expected = [
            ('Hypothesis', 'declared count', 'at least 10; no own upper bound', 'Native variable lengths Unknown'),
            ('Hypothesis', 'available bytes', 'every access bounded by actual available bytes; at least 10 needed', 'A larger declared count cannot supply missing bytes'),
            ('Hypothesis', 'identifier', 'exactly bytes 1..5; first byte nonzero; every byte 00 or 20..7E', 'Internal 00 permitted; native character domain Unknown'),
            ('Hypothesis', 'numeric predicate', 'bytes 6..9: low nibble <=9 only; no high-nibble bound', 'Distinct from stricter physical BCD qualification'),
            ('Hypothesis', 'decimal', '10*(byte>>4)+(byte&15)', 'Local arithmetic only'),
            ('Hypothesis', 'major / minor', 'decimal(byte6) / decimal(byte7)', 'Native representation Unknown'),
            ('Hypothesis', 'product number', 'decimal(byte8)+100*decimal(byte9)', 'Separate from major/minor; family predicates Unknown'),
            ('Hypothesis', 'byte 0', 'not consumed', 'Never a family selector in this partial parser'),
            ('Hypothesis', '07FE', 'missing direct response is not identification failure', 'Separate identity from 0704'),
        ]
        self.assertEqual(rows(self.arch)[:11][2:], expected)
        self.assertIn('../protocols/ebus-services/ebus-service-07h.md#bounded-0704-candidate-declarations', self.arch)
        self.assertIn('**Hold:**', self.arch)
        self.assertIn('Candidate metadata\nnever selects a family by itself.', self.arch)

    def test_exact_synthetic_vectors_and_page_results(self):
        # Independent literal oracles. No decoder is defined or invoked here.
        expected = [
            ('baseline', [161,65,66,67,68,69,249,153,23,4], 10, 'admitted', [65,66,67,68,69], [159,99,417]),
            ('low_nibble_a', [161,65,66,67,68,69,250,153,23,4], 10, 'invalid', None, None),
            ('first_zero', [161,0,66,67,68,69,249,153,23,4], 10, 'invalid', None, None),
            ('internal_zero', [161,65,66,0,68,69,249,153,23,4], 10, 'admitted', [65,66,0,68,69], [159,99,417]),
            ('below_character_domain', [161,65,66,31,68,69,249,153,23,4], 10, 'invalid', None, None),
            ('above_character_domain', [161,65,66,127,68,69,249,153,23,4], 10, 'invalid', None, None),
            ('byte_zero_changed', [0,65,66,67,68,69,249,153,23,4], 10, 'admitted', [65,66,67,68,69], [159,99,417]),
            ('declared_nine', [161,65,66,67,68,69,249,153,23,4], 9, 'incomplete', None, None),
            ('declared_eleven', [161,65,66,67,68,69,249,153,23,4], 11, 'admitted', [65,66,67,68,69], [159,99,417]),
            ('available_nine', [161,65,66,67,68,69,249,153,23], 10, 'incomplete', None, None),
        ]
        actual = [(c['name'], c['raw'], c['declared_count'], c['result'], c['identifier_bytes'], c['numeric_tuple']) for c in self.fixture['cases']]
        self.assertEqual(actual, expected)
        page_rows = rows(self.arch)[13:]
        self.assertEqual(len(page_rows), len(expected))
        for row, (name, raw, count, state, identifier, numeric) in zip(page_rows, expected):
            with self.subTest(case=name):
                self.assertEqual(row, (name, state,
                    'absent' if identifier is None else ' '.join(f'{b:02X}' for b in identifier),
                    'absent' if numeric is None else ', '.join(str(n) for n in numeric)))
        for c in self.fixture['cases']:
            self.assertEqual(c['grade'], 'Hypothesis')
            self.assertEqual(c['qualification'], 'not established')

    def test_independent_arithmetic_and_unknowns(self):
        # Expanded literal arithmetic is independent of a parser implementation.
        self.assertEqual([150 + 9, 90 + 9, 400 + 17], [159, 99, 417])
        self.assertEqual(bytes([65,66,67,68,69]).decode('ascii'), 'ABCDE')
        self.assertEqual(self.fixture['native_grade'], 'Hypothesis')
        self.assertEqual(self.fixture['unknown'], ['native variable lengths', 'physical extra bytes', 'family override predicates', 'complete schemas for all seven services', 'installed support'])
        self.assertIn('not a wire offset', self.native)
        self.assertIn('partial last-known-good state', self.arch)


if __name__ == '__main__':
    unittest.main()
