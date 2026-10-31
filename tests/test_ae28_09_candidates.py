"""Acceptance of native declarations and synthetic examples; no wire decoder."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/ebus-services/ebus-service-09h.md'
FIXTURE = PAGE.parent / 'fixtures/ae28_09_candidates.json'

# Independent finite inventory: service, direction, field, position, width,
# encoding, default, minimum, maximum, conflicting candidate maximum.
EXPECTED = [
    ('0900', 'request', 'PB', 0, 1, None, None, None, None, None),
    ('0900', 'request', 'SB', 1, 1, None, None, None, None, None),
    ('0900', 'request', 'address', None, 2, 'unsigned-le16', 0, 0, 65535, None),
    ('0900', 'request', 'count', None, 1, 'unsigned-u8', 0, 0, 255, None),
    ('0900', 'positive', 'PB', 0, 1, None, None, None, None, None),
    ('0900', 'positive', 'SB', 1, 1, None, None, None, None, None),
    ('0900', 'positive', 'data', 2, None, 'opaque-to-end', None, 0, None, None),
    ('0901', 'request', 'PB', 0, 1, None, None, None, None, None),
    ('0901', 'request', 'SB', 1, 1, None, None, None, None, None),
    ('0901', 'request', 'address', None, 2, 'unsigned-le16', 0, 0, 65535, None),
    ('0901', 'positive', 'PB', 0, 1, None, None, None, None, None),
    ('0901', 'positive', 'SB', 1, 1, None, None, None, None, None),
    ('0902', 'request', 'PB', 0, 1, None, None, None, None, None),
    ('0902', 'request', 'SB', 1, 1, None, None, None, None, None),
    ('0902', 'request', 'address_low', None, 1, 'unsigned-u8', 0, 0, 255, None),
    ('0902', 'request', 'address_high', None, 1, 'unsigned-u8', 0, 0, 255, None),
    ('0902', 'request', 'count', None, 1, 'unsigned-u8', 0, 0, 255, 10),
    ('0902', 'positive', 'data', 0, None, 'opaque-to-end', None, 0, None, None),
    ('0903', 'request', 'PB', 0, 1, None, None, None, None, None),
    ('0903', 'request', 'SB', 1, 1, None, None, None, None, None),
    ('0903', 'request', 'address_low', None, 1, 'unsigned-u8', 0, 0, 255, None),
    ('0903', 'request', 'address_high', None, 1, 'unsigned-u8', 0, 0, 255, None),
    ('0903', 'positive', 'PB', 0, 1, None, None, None, None, None),
    ('0903', 'positive', 'SB', 1, 1, None, None, None, None, None),
    ('0903', 'positive', 'data', 2, None, 'opaque-to-end', None, 0, None, None),
]
SECONDARY = {'0900': 0, '0901': 1, '0902': 2, '0903': 3}
UNKNOWN = [
    'physical memory space', 'peer effects', 'address equivalence',
    'actual packet extent', 'empty-request acceptance', 'installed support',
    'unprovided request field positions',
]


class DirectionAlternatives(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def test_finite_fixture_declarations(self):
        entries = self.fixture['entries']
        self.assertEqual(len(entries), 25)
        actual = []
        for entry in entries:
            key = entry['key']
            self.assertEqual(set(key), {
                'family', 'variant', 'primary', 'secondary', 'operation',
                'direction', 'field',
            })
            self.assertEqual(key['family'], 'memory-service')
            self.assertEqual(key['primary'], 9)
            self.assertEqual(key['secondary'], SECONDARY[key['variant']])
            self.assertIsNone(key['operation'])
            self.assertIn(key['direction'], ('abstract-request', 'abstract-positive'))
            self.assertEqual(entry['grade'], 'Hypothesis')
            for name in ('physical_offset', 'unit', 'enum', 'scale', 'sentinel'):
                self.assertIn(name, entry)
                self.assertIsNone(entry[name])
            actual.append((
                key['variant'], key['direction'].removeprefix('abstract-'),
                key['field'], entry['abstract_offset'], entry['width'],
                entry['encoding'], entry['default'], entry['minimum'],
                entry['maximum'], entry['alternative_maximum'],
            ))
            expected_notes = []
            if key['field'] == 'data':
                expected_notes = ['Empty data is preserved without a success claim.']
            if key['variant'] == '0901' and key['direction'] == 'abstract-positive':
                expected_notes = ['Prefix-only; no body or success claim.']
            if key['variant'] == '0902' and key['field'] == 'count':
                expected_notes = ['Candidate maximum 10 conflicts with formal maximum 255; neither clips raw values.']
            self.assertEqual(entry['notes'], expected_notes)
        self.assertCountEqual(actual, EXPECTED)

    def test_structured_page_declarations(self):
        rows = [tuple(cell.strip() for cell in line.strip('|').split('|'))
                for line in self.page.splitlines() if line.startswith('| Hypothesis |')]
        self.assertEqual(len(rows), 25)
        raw_types = {
            'PB': 'byte / PB=09', 'address': 'unsigned LE16 / 0..65535',
            'address_low': 'u8 / 0..255', 'address_high': 'u8 / 0..255',
            'count': 'u8 / 0..255', 'data': 'opaque / no defined unit or enum',
        }
        expected_rows = []
        for service, direction, field, position, width, _, default, _, _, _ in EXPECTED:
            raw = f'byte / SB={SECONDARY[service]:02X}' if field == 'SB' else raw_types[field]
            extent = str(width) if width is not None else 'to end-of-data; min 0; max unset'
            conflict = 'sentinel unset; default unset; conflict unset'
            if default == 0:
                conflict = 'sentinel unset; default 0; conflict unset'
            if service == '0902' and field == 'count':
                conflict = 'sentinel unset; default 0; candidate max 10 conflicts with formal 255'
            unresolved = 'physical position Unknown'
            if direction == 'request' and field not in ('PB', 'SB'):
                unresolved = 'logical and physical positions Unknown'
            if field == 'data':
                unresolved = 'physical position and packet extent Unknown; empty does not establish success'
            if service == '0901' and direction == 'positive':
                unresolved = 'physical position Unknown; prefix-only; no body or success claim'
            expected_rows.append((
                'Hypothesis', service, direction, field,
                'Unknown' if position is None else str(position),
                extent, raw, 'unset', conflict, unresolved,
            ))
        self.assertCountEqual(rows, expected_rows)
        # Reject extra declarations or promoted grades within the bounded inventory.
        inventory = self.page.split('## Bounded direction declarations\n', 1)[1]
        all_rows = [line for line in inventory.splitlines() if line.startswith('|')]
        self.assertEqual(len(all_rows), 27)

    def test_standard_layouts_separate_from_synthetic_inventory(self):
        standard, inventory = self.page.split('## Bounded direction declarations\n', 1)
        standard = standard.split('## Standard command layouts\n', 1)[1]
        rows = [line for line in standard.splitlines() if line.startswith('|')]
        self.assertEqual(rows, [
            '| Service | Standard name | Request payload | Response payload |',
            '|---|---|---|---|',
            '| `0x0900` | Read RAM | 0: address low; 1: address high; 2: count DN | 0..DN-1: data (DN bytes) |',
            '| `0x0901` | Write RAM | 0: address low; 1: address high; 2..: data | Empty (response NN=0) |',
            '| `0x0902` | Read EEPROM | 0: address low; 1: address high; 2: count DN | 0..DN-1: data (DN bytes) |',
            '| `0x0903` | Write EEPROM | 0: address low; 1: address high; 2..: data | Empty (response NN=0) |',
        ])
        normalized = ' '.join(standard.split())
        for statement in (
            '**Proven:** these are the service-only Memory Server layouts.',
            'Offsets below are zero-based within the payload, excluding PB/SB, length, CRC and ACK.',
            'read requests have NN=3; DN has nominal range 0..10, with DN>10 permitted in service mode.',
            '**Unknown:** write-data count:',
            'These imply NN-1 versus NN data bytes; the ambiguity is retained.',
        ):
            self.assertIn(statement, normalized)
        self.assertIn('Its omission of request data is not an address-only standard write layout;',
                      ' '.join(inventory.split()))

    def test_address_examples_independent_values(self):
        self.assertEqual(self.fixture['address_cases'], [
            {'service': '0900', 'direction': 'abstract-request', 'raw': [52, 18], 'address': 4660},
            {'service': '0901', 'direction': 'abstract-request', 'raw': [52, 18], 'address': 4660},
            {'service': '0902', 'direction': 'abstract-request', 'raw': [52, 18], 'address_low': 52, 'address_high': 18},
            {'service': '0903', 'direction': 'abstract-request', 'raw': [52, 18], 'address_low': 52, 'address_high': 18},
        ])
        for case in self.fixture['address_cases'][:2]:
            self.assertEqual(int.from_bytes(bytes(case['raw']), 'little'), 4660)
            self.assertEqual(case['raw'][0] + 256 * case['raw'][1], 4660)
        for case in self.fixture['address_cases'][2:]:
            self.assertEqual((case['address_low'], case['address_high']), (52, 18))

    def test_positive_and_empty_examples(self):
        self.assertEqual(self.fixture['positive_cases'], [
            {'service': '0900', 'direction': 'abstract-positive', 'raw': [9, 0, 170, 85], 'data_position': 2, 'data': [170, 85], 'empty_raw': [9, 0], 'empty_data': [], 'success': None},
            {'service': '0902', 'direction': 'abstract-positive', 'raw': [170, 85], 'data_position': 0, 'data': [170, 85], 'empty_raw': [], 'empty_data': [], 'success': None},
            {'service': '0903', 'direction': 'abstract-positive', 'raw': [9, 3, 170, 85], 'data_position': 2, 'data': [170, 85], 'empty_raw': [9, 3], 'empty_data': [], 'success': None},
        ])
        self.assertEqual(self.fixture['prefix_only'], {
            'service': '0901', 'direction': 'abstract-positive',
            'raw': [9, 1], 'data': None, 'success': None,
        })

    def test_counts_preserved_with_separate_conflict(self):
        cases = self.fixture['count_cases']
        self.assertEqual(len(cases), 8)
        for service, conflict in [('0900', None), ('0902', 10)]:
            actual = [(c['raw'], c['retained'], c['formal_maximum'], c['candidate_maximum'])
                      for c in cases if c['service'] == service]
            self.assertEqual(actual, [
                ([0], 0, 255, conflict), ([10], 10, 255, conflict),
                ([11], 11, 255, conflict), ([255], 255, 255, conflict),
            ])

    def test_evidence_boundaries_and_local_link(self):
        self.assertEqual(self.fixture['evidence'], 'Hypothesis')
        self.assertIs(self.fixture['candidate'], True)
        self.assertEqual(self.fixture['physical_qualification'], 'Unknown')
        self.assertEqual(self.fixture['unknown_grade'], 'Unknown')
        self.assertEqual(self.fixture['unknowns'], UNKNOWN)
        self.assertIn('[Synthetic direction examples](fixtures/ae28_09_candidates.json)', self.page)
        # Full boundary statements, alongside exact graded table checks above.
        normalized = ' '.join(self.page.split())
        for statement in (
            'A logical position is not a wire offset.',
            'an abstract positive prefix does not establish physical response positions.',
            'a storage-name inconsistency must not change PB/SB service identity.',
            'No service-mode rule or execution authority follows from these declarations.',
            '**Unknown:** physical memory space, peer effects, address equivalence, actual packet extent, empty-request acceptance and installed support.',
        ):
            self.assertIn(statement, normalized)


if __name__ == '__main__':
    unittest.main()
