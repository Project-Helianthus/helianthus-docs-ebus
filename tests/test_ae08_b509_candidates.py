"""Offline acceptance checks of native declarations and synthetic arithmetic.

These checks exercise documentation and fixture content, not a wire decoder.
"""
import json
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = Path('protocols/vaillant/ebus-vaillant-B509.md')
FIXTURE = Path('protocols/vaillant/fixtures/ae08_b509_candidates.json')


class B509Candidates(unittest.TestCase):
    def setUp(self):
        self.page = (ROOT / PAGE).read_text()
        self.fixture = json.loads((ROOT / FIXTURE).read_text())

    def test_finite_structured_page_claims(self):
        section = self.page.split('### Bounded width and feedback alternatives:', 1)[1]
        section = section.split('### Request and reply widths', 1)[0]
        lines = [line for line in section.splitlines() if line.startswith('|')]
        self.assertEqual(lines[0], '| Grade | Operation | Variant | Field | Direction | Logical position / extent | Raw type/domain | Scale | Default/sentinel/conflict | Unresolved |')
        actual = [tuple(cell.strip() for cell in line.strip('|').split('|')) for line in lines[2:]]
        # Independent finite expectations; every cell includes its own nearby grade
        # and unresolved/conflict evidence rather than searching the whole page.
        quantity_unknown = 'Five separate raw quantities; factor is not a converter; conversion and minimum<=maximum enforcement Unknown'
        width_unknown = 'Alternative width remains incomplete/raw; selection, wire adaptation and installed support Unknown'
        support_unknown = 'Wire adaptation and installed support Unknown'
        expected = [
            ('Hypothesis', '07', 'selector', 'selector', 'request', 'Unknown / 8 bits', 'unsigned byte', 'raw', 'Unknown', 'Request selector cannot select reply width; wire adaptation and installed support Unknown'),
            ('Hypothesis', '07', 'positive-u16', 'value', 'response', 'Unknown / 16 bits', 'unsigned LE16', 'raw', 'default 0; sentinel Unknown', width_unknown),
            ('Hypothesis', '07', 'positive-u32', 'value', 'response', 'Unknown / 32 bits', 'unsigned LE32', 'raw', 'default 0; sentinel Unknown', width_unknown),
            ('Hypothesis', '32', 'status-query', 'address', 'request', 'Unknown / Unknown', 'Unknown', 'Unknown', 'Unknown', 'Queries status; does not toggle an address; address width Unknown'),
            ('Hypothesis', '33', 'raw-quantities', 'address', 'Unknown', 'Unknown / Unknown', 'Unknown', 'Unknown', 'Unknown', 'Address width, byte order and conversion Unknown'),
            ('Hypothesis', '33', 'raw-quantities', 'minimum', 'Unknown', 'Unknown / 16 bits', 'signed LE16', 'raw', 'Unknown', quantity_unknown),
            ('Hypothesis', '33', 'raw-quantities', 'maximum', 'Unknown', 'Unknown / 16 bits', 'signed LE16', 'raw', 'Unknown', quantity_unknown),
            ('Hypothesis', '33', 'raw-quantities', 'default', 'Unknown', 'Unknown / 16 bits', 'signed LE16', 'raw', 'Unknown', quantity_unknown),
            ('Hypothesis', '33', 'raw-quantities', 'step', 'Unknown', 'Unknown / 16 bits', 'signed LE16', 'raw', 'Unknown', quantity_unknown),
            ('Hypothesis', '33', 'raw-quantities', 'factor', 'Unknown', 'Unknown / 16 bits', 'signed LE16', 'raw', 'Unknown', quantity_unknown),
            ('Hypothesis', '39', 'raw-u16', 'value', 'Unknown', 'Unknown / 16 bits', 'unsigned 16-bit; byte order Unknown', 'raw', 'Unknown', 'Complement algorithm Unknown'),
            ('Hypothesis', '41', 'raw-0f-f0', 'value', 'Unknown', 'Unknown / 8 bits', 'unsigned byte; raw 0F/F0', 'raw', 'Unknown', 'Other values have no established labels'),
            ('Hypothesis', '44', 'default-domain-conflict', 'value', 'Unknown', 'Unknown / 8 bits', 'unsigned byte; domain 1..255', 'Unknown; minute interpretation Hypothesis', 'default 0 conflicts with domain 1..255; sentinel Unknown', 'Conflict unresolved; conversion Unknown'),
            ('Hypothesis', '59', 'quantities', 'temperature', 'Unknown', 'Unknown / 16 bits', 'signed LE16', '/16 degrees Celsius', 'Unknown', support_unknown),
            ('Hypothesis', '59', 'quantities', 'flow', 'Unknown', 'Unknown / 16 bits', 'unsigned LE16', '/100 litres per minute', 'Unknown', support_unknown),
            ('Hypothesis', '59', 'quantities', 'volume', 'Unknown', 'Unknown / 16 bits', 'unsigned LE16', '/10 litres', 'Unknown', support_unknown),
            ('Hypothesis', '59', 'quantities', 'minimum_volume', 'Unknown', 'Unknown / Unknown', 'width, signedness and byte order Unknown', 'raw; no division', 'Unknown', 'Unit and interpretation Unknown; preserve raw bytes'),
            ('Hypothesis', '59', 'quantities', 'maximum_volume', 'Unknown', 'Unknown / Unknown', 'width, signedness and byte order Unknown', 'raw; no division', 'Unknown', 'Unit and interpretation Unknown; preserve raw bytes'),
            ('Hypothesis', '06', 'prefix-only-positive', 'prefix', 'response', 'Unknown / Unknown', 'Unknown', 'Unknown', 'Unknown', 'Shared apparent prefix cannot select alternative or establish successful reset; wire adaptation and installed support Unknown'),
            ('Hypothesis', '06', 'positive-with-feedback', 'feedback', 'response', 'Unknown / 8 bits', 'unsigned byte', '01 accepted; every other byte rejected', 'Unknown', 'Only explicit feedback form; accepted feedback does not establish successful reset; wire adaptation and installed support Unknown'),
            ('Hypothesis', '06', 'negative-without-extra-discriminator', 'prefix', 'response', 'Unknown / Unknown', 'Unknown', 'Unknown', 'Unknown', 'Ambiguous negative; no extra discriminator; prefix does not establish physical NACK or successful reset; wire adaptation and installed support Unknown'),
        ]
        self.assertEqual(len(actual), 21)
        self.assertEqual(actual, expected)
        self.assertIn('`PB=0xB5`, `SB=0x09`', section)
        self.assertIn('Vaillant family', section)
        self.assertIn('a logical position is not a wire\noffset', section)
        self.assertIn('[synthetic examples](fixtures/ae08_b509_candidates.json)', section)
        self.assertIn('exactly these 21 entries', section)
        self.assertIn('OP0D/0E access and identity scanning are outside', section)
        self.assertIn('Synthetic\ncorrectness provides no physical qualification', section)

    def test_fixture_evidence_boundaries(self):
        self.assertEqual(set(self.fixture), {'grade', 'wire_adaptation', 'installed_support', 'op07', 'op33', 'op39', 'op41', 'op44', 'op59', 'op06'})
        self.assertEqual(self.fixture['grade'], 'Hypothesis')
        self.assertIsNone(self.fixture['wire_adaptation'])
        self.assertIsNone(self.fixture['installed_support'])

    def test_op07_width_alternatives(self):
        self.assertEqual(self.fixture['op07'], [
            {'variant': 'positive-u16', 'raw': '34 12', 'value': 4660, 'state': 'positive-candidate', 'default': 0},
            {'variant': 'positive-u32', 'raw': '78 56 34 12', 'value': 305419896, 'state': 'positive-candidate', 'default': 0},
            {'variant': 'positive-u16', 'raw': '78 56 34 12', 'value': None, 'state': 'incomplete/raw', 'default': 0},
            {'variant': 'positive-u32', 'raw': '34 12', 'value': None, 'state': 'incomplete/raw', 'default': 0},
        ])
        self.assertEqual(struct.unpack('<H', bytes.fromhex(self.fixture['op07'][0]['raw'])), (4660,))
        self.assertEqual(struct.unpack('<I', bytes.fromhex(self.fixture['op07'][1]['raw'])), (305419896,))
        self.assertEqual([len(bytes.fromhex(c['raw'])) for c in self.fixture['op07']], [2, 4, 4, 2])

    def test_op33_independent_signed_raw_quantities(self):
        self.assertEqual(self.fixture['op33'], {
            'address': None, 'fields': ['minimum', 'maximum', 'default', 'step', 'factor'],
            'cases': [
                {'raw_words': ['FF FF', '02 00', '00 00', '01 00', 'FE FF'], 'raw_values': [-1, 2, 0, 1, -2]},
                {'raw_words': ['02 00', 'FF FF', '00 00', '01 00', 'FE FF'], 'raw_values': [2, -1, 0, 1, -2]},
            ], 'conversion': None, 'minimum_le_maximum_enforcement': None,
        })
        for case, expected in zip(self.fixture['op33']['cases'], [(-1, 2, 0, 1, -2), (2, -1, 0, 1, -2)]):
            self.assertEqual(struct.unpack('<5h', bytes.fromhex(' '.join(case['raw_words']))), expected)
        self.assertGreater(self.fixture['op33']['cases'][1]['raw_values'][0], self.fixture['op33']['cases'][1]['raw_values'][1])

    def test_op39_op41_and_op44_keep_raw_conflict(self):
        self.assertEqual(self.fixture['op39'], {'raw': 'FF FF', 'value': 65535, 'complement_algorithm': None, 'byte_order': None})
        # FFFF is endian-symmetric; this arithmetic makes no byte-order claim.
        self.assertEqual(int.from_bytes(bytes.fromhex(self.fixture['op39']['raw']), 'big'), 65535)
        self.assertEqual(self.fixture['op41'], {'raw_values': ['0F', 'F0'], 'other_labels': None})
        self.assertEqual(self.fixture['op44'], {'default': 0, 'lower': 1, 'upper': 255, 'unit': 'minutes', 'conflict': 'unresolved'})
        self.assertLess(self.fixture['op44']['default'], self.fixture['op44']['lower'])

    def test_op59_independent_arithmetic_and_raw_bounds(self):
        self.assertEqual(self.fixture['op59'], [
            {'field': 'temperature', 'raw': 'F0 FF', 'raw_value': -16, 'divisor': 16, 'value': -1},
            {'field': 'flow', 'raw': '64 00', 'raw_value': 100, 'divisor': 100, 'value': 1},
            {'field': 'flow', 'raw': 'FF FF', 'raw_value': 65535, 'divisor': 100, 'value': 655.35},
            {'field': 'volume', 'raw': '0A 00', 'raw_value': 10, 'divisor': 10, 'value': 1},
            {'field': 'minimum_volume', 'raw': '0A 00', 'raw_value': None, 'divisor': None, 'value': None},
            {'field': 'maximum_volume', 'raw': '64 00', 'raw_value': None, 'divisor': None, 'value': None},
        ])
        cases = self.fixture['op59']
        self.assertEqual(struct.unpack('<h', bytes.fromhex(cases[0]['raw']))[0] / 16, -1)
        self.assertEqual(struct.unpack('<H', bytes.fromhex(cases[1]['raw']))[0] / 100, 1)
        self.assertEqual(struct.unpack('<H', bytes.fromhex(cases[2]['raw']))[0] / 100, 655.35)
        self.assertEqual(struct.unpack('<H', bytes.fromhex(cases[3]['raw']))[0] / 10, 1)
        self.assertEqual([bytes.fromhex(c['raw']) for c in cases[4:]], [b'\x0a\x00', b'\x64\x00'])

    def test_op06_feedback_is_explicit_and_prefix_states_separate(self):
        self.assertEqual(self.fixture['op06'], {
            'positive-with-feedback': [
                {'raw': '00', 'state': 'rejected'}, {'raw': '01', 'state': 'accepted'},
                {'raw': '02', 'state': 'rejected'}, {'raw': 'FF', 'state': 'rejected'},
            ],
            'prefix-only-positive': {'raw_prefix': None, 'state': 'prefix-only-positive', 'feedback': None},
            'negative-without-extra-discriminator': {'raw_prefix': None, 'state': 'ambiguous-negative', 'feedback': None},
            'successful_reset': None, 'physical_nack': None,
        })

    def test_open_questions_preserve_unresolved_contract(self):
        questions = self.page.split('## Open questions', 1)[1].split('## References', 1)[0]
        self.assertIn('default/domain conflict of `44`', questions)
        self.assertIn('`32` queries status rather than toggling an address', questions)
        self.assertIn('neither a shared prefix nor accepted feedback proves a reset', questions)


if __name__ == '__main__':
    unittest.main()
