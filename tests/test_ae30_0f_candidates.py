"""Explicit acceptance checks for the bounded synthetic 0F declaration.

These check documentation and fixture contracts, not a decoder or physical bus.
Only the secondary is a varied key axis; primary is held fixed at 0F.
"""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/ebus-services/ebus-service-0fh.md'
FIXTURE = ROOT / 'protocols/ebus-services/fixtures/ae30_0f_candidates.json'

# Independently specified cells, including grade and neighboring uncertainty.
EXPECTED_ROWS = [
    ('Hypothesis', '0F / absent', 'request', 'primary', 'Unknown / 1 byte declared',
     'byte / 0F', 'Unknown',
     'sentinel Unknown; default Unknown; conflict none declared',
     'physical position Unknown'),
    ('Hypothesis', '0F / absent', 'request', 'secondary', 'absent / absent encoded byte',
     'absent; distinct from 00, 01, 02, 03 and wildcard', 'Unknown',
     'sentinel Unknown; default Unknown; absent is not zero',
     'exact partial identity Unknown; no alias to 0F01/0F02/0F03'),
    ('Unknown', '0F / absent', 'request', 'body', 'Unknown / Unknown',
     'Unknown; no typed body declared', 'Unknown',
     'sentinel Unknown; default Unknown; conflict none declared',
     'request body and physical NN Unknown'),
    ('Hypothesis', '0F / absent', 'positive', 'prefix', 'Unknown / Unknown',
     'PeBUS-relevant prefix; typed data absent', 'Unknown',
     'sentinel Unknown; default Unknown; no typed data does not mean no physical data',
     'response body, physical NN and ACK Unknown'),
    ('Unknown', '0F / absent', 'response', 'opaque bytes', 'Unknown / Unknown',
     'AA retained raw / meaning Unknown', 'Unknown',
     'sentinel Unknown; default Unknown; nonempty reply is not rejected',
     'AA is synthetic; response body and physical extent Unknown'),
    ('Unknown', '0F / absent', 'exchange', 'physical framing', 'Unknown / Unknown',
     'NN Unknown; ACK Unknown', 'Unknown',
     'sentinel Unknown; default Unknown; PeBUS relevance supplies neither length nor ACK',
     'raw one-byte 0F declaration is not a sendable packet'),
    ('Unknown', '0F / absent', 'exchange', 'support and effects', 'Unknown / Unknown',
     'support Unknown; effects Unknown', 'Unknown',
     'sentinel Unknown; default Unknown; conflict none declared',
     'no start/ready/test/end executor or active-testing permission established'),
]


class PartialTestingIdentity(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def test_metadata_preserves_absence_and_unknown(self):
        self.assertEqual(self.fixture['grade'], 'Hypothesis')
        self.assertEqual(self.fixture['physical_qualification'], 'Unknown')
        self.assertEqual(self.fixture['metadata'], {
            'primary': '0F', 'secondary': None, 'secondary_state': 'absent',
            'body': 'Unknown', 'typed_positive_data': 'absent',
        })

    def test_secondary_axis_has_five_independent_keys(self):
        cases = self.fixture['identity_cases']
        self.assertEqual(cases, [
            {'primary': '0F', 'secondary': None, 'key': ['0F', None]},
            {'primary': '0F', 'secondary': '00', 'key': ['0F', '00']},
            {'primary': '0F', 'secondary': '01', 'key': ['0F', '01']},
            {'primary': '0F', 'secondary': '02', 'key': ['0F', '02']},
            {'primary': '0F', 'secondary': '03', 'key': ['0F', '03']},
        ])
        keys = [tuple(case['key']) for case in cases]
        self.assertEqual(len(set(keys)), 5)
        for control in cases[1:]:
            with self.subTest(secondary=control['secondary']):
                self.assertEqual(control['primary'], cases[0]['primary'])
                self.assertNotEqual(control['secondary'], cases[0]['secondary'])
                self.assertNotEqual(control['key'], cases[0]['key'])

    def test_single_byte_is_declaration_only(self):
        self.assertEqual(self.fixture['declaration'], {
            'raw_hex': '0F', 'declared_byte_count': 1, 'sendable': False,
        })
        self.assertEqual(bytes.fromhex(self.fixture['declaration']['raw_hex']), b'\x0f')
        self.assertEqual(len(bytes.fromhex(self.fixture['declaration']['raw_hex'])), 1)

    def test_prefix_does_not_determine_framing(self):
        self.assertEqual(self.fixture['positive'], {
            'grade': 'Hypothesis', 'prefix': 'PeBUS-relevant',
            'typed_data': 'absent', 'body': 'Unknown',
            'physical_nn': 'Unknown', 'ack': 'Unknown',
        })

    def test_opaque_reply_retains_independent_raw_value(self):
        self.assertEqual(self.fixture['opaque_reply'], {
            'raw_hex': 'AA', 'raw_bytes': [170], 'meaning': 'Unknown', 'retained': True,
        })
        self.assertEqual(list(bytes.fromhex(self.fixture['opaque_reply']['raw_hex'])), [170])

    def test_support_is_not_executable(self):
        self.assertEqual(self.fixture['support'], {
            'grade': 'Unknown', 'installed': 'Unknown', 'effects': 'Unknown',
            'executable_support': False, 'active_testing_permission': False,
        })

    def test_page_complete_scoped_table(self):
        bounded = self.page.split('### Bounded partial testing declarations\n', 1)[1]
        bounded = bounded.split('## Open questions', 1)[0]
        rows = [tuple(cell.strip() for cell in line.strip('|').split('|'))
                for line in bounded.splitlines() if line.startswith('|')]
        self.assertEqual(rows[:2], [
            ('Grade', 'Identity', 'Direction', 'Property', 'Logical position / extent',
             'Raw type / domain', 'Scale', 'Sentinel / default / conflict', 'Unresolved'),
            ('---',) * 9,
        ])
        self.assertEqual(rows[2:], EXPECTED_ROWS)
        self.assertIn('[synthetic partial-identity cases](./fixtures/ae30_0f_candidates.json)', bounded)

    def test_partial_prose_and_open_questions_agree(self):
        partial = self.page.split('## Vaillant variants\n', 1)[1].split('## Communication Flow', 1)[0]
        normalized = ' '.join(partial.split())
        for statement in (
            '**Hypothesis:** the request declares primary `0F`, no encoded secondary byte and no typed body.',
            'Its positive declaration consists only of a PeBUS-relevant prefix without typed data.',
            'This logical declaration does not establish an empty physical eBUS reply.',
            'Logical positions are not wire offsets; unprovided positions and extents remain Unknown.',
            'The absent secondary remains explicit metadata rather than a zero, wildcard or standard service identifier.',
            'No standard-service lifecycle or executable support follows from this partial form.',
            '**Unknown:** the exact partial identity, request/response body, physical NN, ACK, installed support and effects for the partial testing family remain unresolved.',
            '**Unknown:** whether the family implements the separate standard `0x0F 0x01`–`0x0F 0x03` lifecycle is not established by this declaration.',
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, normalized)
        self.assertNotIn('positive target response carries no data', partial)


if __name__ == '__main__':
    unittest.main()
