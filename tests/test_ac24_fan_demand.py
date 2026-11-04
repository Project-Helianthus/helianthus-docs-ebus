"""Synthetic B522 declaration checks; no native execution or qualification."""
import copy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-vaillant-B522.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ac24_fan_demand.json'
AXES = ('family', 'variant', 'direction', 'service', 'operation', 'alternative')
IDENTITIES = [
    ('vaillant', 'B522', None, 'B522', None, 'current-mode', None, 'Hypothesis'),
    ('vaillant', 'B522', 'request', 'B522', None, 'request', 7, 'Hypothesis'),
    ('vaillant', 'B522', 'response', 'B522', None, 'positive', 4, 'Hypothesis'),
    ('vaillant', 'B522', 'response', 'B522', None, 'negative', None, 'Hypothesis'),
    ('vaillant', 'B522', None, 'B522', None, 'FF FF unset', None, 'Hypothesis'),
]
MODES = {
    '0': ['no heating demand to source/circuits'],
    '1': ['no source demand but demand from a sink', None],
    '2': ['source heating demand'],
    '3': ['no source cooling demand but demand from a sink'],
    '4': ['source cooling demand'],
}
# Independent expectations: alternative, name, kind, domain, default, scale,
# bits, reserved mask. Coordinates and grades are asserted separately.
FIELDS = [
    ('current-mode', 'current_mode', 'u8', [0, 255], 0, 1, None, 0),
    ('request', 'fan', 'u8', [0, 255], 0, 1, None, 0),
    ('request', 'automatic', 'boolean', [0, 1], False, 1, [0], 254),
    ('request', 'room_temperature', 'u8', [0, 255], 0, 0.5, None, 0),
    ('request', 'mode', 'u8', [0, 255], 0, 1, None, 0),
    ('positive', None, 'boolean', [0, 1], False, 1, [0], 248),
    ('positive', None, 'boolean', [0, 1], False, 1, [1], 248),
    ('positive', None, 'boolean', [0, 1], False, 1, [2], 248),
]
EXAMPLES = [
    ('request', 'room_temperature', '00', 0, '00'),
    ('request', 'room_temperature', '01', 0.5, '00'),
    ('request', 'room_temperature', 'FF', 127.5, '00'),
    ('request', 'fan', 'FF', 255, '00'),
    ('request', 'mode', 'FF', 255, '00'),
    ('request', 'automatic', '01', True, '00'),
    ('request', 'automatic', '80', False, '80'),
    ('positive', None, '08', [False, False, False], '08'),
]


def table(text, heading):
    """Read only the named section's single Markdown table, including header."""
    section = text.split(heading + '\n', 1)[1].split('\n##', 1)[0]
    rows = [tuple(cell.strip() for cell in line.strip('|').split('|'))
            for line in section.splitlines() if line.startswith('|')]
    return [row for row in rows if not all(re.fullmatch(r'[-:]+', c) for c in row)]


class FanDemandTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def assert_identities(self, rows):
        keys = AXES + ('logical_extent', 'grade')
        self.assertEqual(len(rows), 5)
        for row, expected in zip(rows, IDENTITIES):
            self.assertEqual(set(row), set(keys))
            self.assertEqual(tuple(row[k] for k in keys), expected)

    def test_identity_extent_and_grade(self):
        self.assert_identities(self.data['identities'])

    def test_identity_axes_independent(self):
        # Validate the real data first, then alter exactly one identity field.
        # This is a declaration guard, not evidence of a runtime lookup key.
        rows = self.data['identities']
        self.assert_identities(rows)
        for index in range(5):
            for axis in AXES:
                with self.subTest(row=index, axis=axis):
                    changed = copy.deepcopy(rows)
                    changed[index][axis] = 'synthetic-distinct'
                    with self.assertRaises(AssertionError):
                        self.assert_identities(changed)
                    changed[index][axis] = rows[index][axis]
                    self.assert_identities(changed)

    def test_fields_exact(self):
        keys = ('alternative', 'name', 'kind', 'domain', 'default', 'scale',
                'bits', 'reserved_mask')
        self.assertEqual(len(self.data['fields']), 8)
        for field, expected in zip(self.data['fields'], FIELDS):
            with self.subTest(field=expected[:2], bits=expected[6]):
                self.assertEqual(set(field), set(keys) | {'coordinate', 'grade'})
                self.assertEqual(tuple(field[k] for k in keys), expected)
                self.assertIs(type(field['default']), type(expected[4]))
                self.assertIsNone(field['coordinate'])
                self.assertEqual(field['grade'], 'Hypothesis')

    def test_modes_and_unset_are_separate(self):
        self.assertEqual(self.data['current_modes'], MODES)
        self.assertEqual(len(self.data['current_modes']['1']), 2)
        self.assertIsNone(self.data['current_modes']['1'][1])
        for raw in range(5, 256):
            self.assertNotIn(str(raw), self.data['current_modes'])
        self.assertEqual(self.data['unset'], {
            'raw_hex': 'FF FF', 'interpretation': 'candidate unset',
            'coordinate': None, 'grade': 'Hypothesis'})

    def test_evidence_grades(self):
        self.assertIs(self.data['synthetic'], True)
        self.assertEqual(self.data['software_representation'], 'Proven')
        self.assertEqual(self.data['candidate_semantics'], 'Hypothesis')
        self.assertEqual(self.data['physical_qualification'], 'Unknown')
        self.assertEqual(self.data['unknown'], {
            'physical_mapping': 'Unknown', 'installed_support': 'Unknown',
            'execution': 'Unknown', 'semantic_equivalence': 'Unknown',
            'native_adaptation': 'Unknown', 'peer_effects': 'Unknown'})

    def test_explicit_examples_and_declared_conversion(self):
        keys = ('alternative', 'field', 'raw_hex', 'value', 'reserved_hex')
        self.assertEqual(len(self.data['examples']), 8)
        for example, expected in zip(self.data['examples'], EXAMPLES):
            with self.subTest(raw=expected[2], field=expected[1]):
                self.assertEqual(set(example), set(keys))
                self.assertEqual(tuple(example[k] for k in keys), expected)
                raw = int(example['raw_hex'], 16)
                fields = [f for f in self.data['fields']
                          if f['alternative'] == example['alternative']
                          and f['name'] == example['field']]
                self.assertTrue(fields)
                decoded = []
                for field in fields:
                    if field['bits'] is None:
                        value = raw * field['scale']
                    else:
                        value = bool(raw & (1 << field['bits'][0]))
                    decoded.append(value)
                result = decoded if example['alternative'] == 'positive' else decoded[0]
                self.assertEqual(result, expected[3])
                self.assertEqual(raw & fields[0]['reserved_mask'], int(expected[4], 16))
                self.assertEqual(example['raw_hex'], expected[2])

    def test_full_u8_domains_remain_raw(self):
        for name in ('fan', 'mode'):
            field = next(f for f in self.data['fields'] if f['name'] == name)
            for raw in range(256):
                with self.subTest(field=name, raw=raw):
                    self.assertLessEqual(field['domain'][0], raw)
                    self.assertGreaterEqual(field['domain'][1], raw)
                    self.assertEqual(raw * field['scale'], raw)

    def test_page_identity_table(self):
        self.assertEqual(table(self.page, '### Candidate identities'), [
            ('Family', 'Variant', 'Direction', 'Service', 'Operation', 'Alternative', 'Logical extent', 'Grade'),
            ('vaillant', 'B522', 'absent', 'B522', 'absent', 'current-mode', 'absent', 'Hypothesis'),
            ('vaillant', 'B522', 'request', 'B522', 'absent', 'request', '7', 'Hypothesis'),
            ('vaillant', 'B522', 'response', 'B522', 'absent', 'positive', '4', 'Hypothesis'),
            ('vaillant', 'B522', 'response', 'B522', 'absent', 'negative', 'absent', 'Hypothesis'),
            ('vaillant', 'B522', 'absent', 'B522', 'absent', 'FF FF unset', 'absent', 'Hypothesis'),
        ])

    def test_page_field_table(self):
        self.assertEqual(table(self.page, '### Candidate fields'), [
            ('Alternative', 'Field', 'Representation', 'Raw domain', 'Default', 'Reserved bits', 'Grade'),
            ('current-mode', 'current_mode', 'u8, identity', '0..255', '0', 'none declared', 'Hypothesis'),
            ('request', 'fan', 'u8, identity, no established enum', '0..255', '0', 'none declared', 'Hypothesis'),
            ('request', 'automatic', 'bit0: 0 disabled, 1 enabled', '0..1', 'disabled', '1..7 zero', 'Hypothesis'),
            ('request', 'room_temperature', 'u8 times 0.5 degrees C', '0..255', '0', 'none declared', 'Hypothesis'),
            ('request', 'mode', 'u8, identity, unlabeled', '0..255', '0', 'none declared', 'Hypothesis'),
            ('positive', 'unnamed bit0', 'Boolean', '0..1', 'false', '3..7 zero', 'Hypothesis'),
            ('positive', 'unnamed bit1', 'Boolean', '0..1', 'false', '3..7 zero', 'Hypothesis'),
            ('positive', 'unnamed bit2', 'Boolean', '0..1', 'false', '3..7 zero', 'Hypothesis'),
        ])

    def test_page_mode_table(self):
        self.assertEqual(table(self.page, '### Current-mode candidate meanings'), [
            ('Raw', 'Candidate meaning', 'Competing alternative', 'Grade'),
            ('0', 'no heating demand to source/circuits', 'none declared', 'Hypothesis'),
            ('1', 'no source demand but demand from a sink', 'Unknown (unresolved label)', 'Hypothesis'),
            ('2', 'source heating demand', 'none declared', 'Hypothesis'),
            ('3', 'no source cooling demand but demand from a sink', 'none declared', 'Hypothesis'),
            ('4', 'source cooling demand', 'none declared', 'Hypothesis'),
            ('5..255', 'unlabeled', 'Unknown', 'Unknown'),
        ])

    def test_page_examples(self):
        self.assertEqual(table(self.page, '### Synthetic carrier examples'), [
            ('Alternative', 'Field', 'Raw hex', 'Declared result', 'Reserved discrepancy', 'Grade'),
            ('request', 'room_temperature', '00', '0 degrees C', 'none', 'Hypothesis'),
            ('request', 'room_temperature', '01', '0.5 degrees C', 'none', 'Hypothesis'),
            ('request', 'room_temperature', 'FF', '127.5 degrees C', 'none', 'Hypothesis'),
            ('request', 'fan', 'FF', 'raw255', 'none', 'Hypothesis'),
            ('request', 'mode', 'FF', 'raw255, unlabeled', 'none', 'Hypothesis'),
            ('request', 'automatic', '01', 'enabled (bit0 only)', 'none', 'Hypothesis'),
            ('request', 'automatic', '80', 'disabled', '80', 'Hypothesis'),
            ('positive', 'unnamed bits0..2', '08', 'false, false, false', '08', 'Hypothesis'),
        ])

    def test_page_scoped_claims(self):
        normalized = ' '.join(self.page.split())
        for claim in (
            'Its absent operation, direction, extent, names and coordinates stay absent;',
            'logical extents include prefix positions and are not physical response lengths.',
            'All field coordinates in this partial catalog are absent.',
            'The older offset and status-role hypotheses above do not fill these absences.',
            '**Proven** applies only to the declared representation checked with',
            'Every physical interpretation below is **Hypothesis**.',
            'Physical mapping, installed support, execution, semantic equivalence, native adaptation, peer effects and physical qualification remain **Unknown**.',
            'This page grants no runtime capability or write admission;',
            'Raw 1 retains two unresolved alternatives: the competing label is Unknown,',
            'Heating priority during simultaneous cooling and bypass behavior remain candidate semantics only (**Hypothesis**)',
            'Preserve raw bytes and reserved-bit discrepancies alongside useful independent fields.',
            'Room temperature uses raw u8 scaling, not BCD conversion.',
            'FF is not a sentinel for the individual room, mode or fan carriers.',
            'The separate **Hypothesis** that FF FF means unset has no established coordinates or equivalence to those fields.',
            'A reserved bit is not a fourth positive Boolean and does not enable automatic.',
        ):
            with self.subTest(claim=claim):
                self.assertIn(claim, normalized)
        self.assertNotRegex(self.page, r'\b[0-9a-f]{40,64}\b')

    def test_existing_ventilation_variant_preserved(self):
        self.assertEqual(table(self.page, '## Known Selectors'), [
            ('Request suffix', 'TypeSpec name', 'Configured direction', 'Candidate meaning', 'Grade'),
            ('`02 00 ff ff`', '`VentDay`', 'write', 'ventilation day mode', 'Hypothesis'),
            ('`01 00 ff ff`', '`VentNight`', 'write', 'ventilation night mode', 'Hypothesis'),
            ('`03 00 ff ff`', '`VentBoost`', 'write', 'boost ventilation', 'Hypothesis'),
        ])
        self.assertIn('## Configured ventilation layout (separate hypothesis)', self.page)
        self.assertIn('op `B5 22 00`', self.page)
        self.assertIn('fan stage `u8` at offset 3', self.page)
        self.assertIn('bit 1 maintenance, bit 2 filter maintenance', self.page)


if __name__ == '__main__':
    unittest.main(verbosity=2)
