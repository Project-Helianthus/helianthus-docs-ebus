"""Finite native declaration acceptance checks, not a decoder or device test."""
import csv
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-vaillant-B506.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ae06_b506_candidates.json'

# Independent expected declarations: do not derive these from the fixture/page.
PARAMETERS = {
    0: ('opaque-through-end', None), 1: ('opaque-through-end', None),
    2: ('opaque-through-end', None), 4: ('opaque-through-end', None),
    5: ('opaque-through-end', None), 3: ('raw-byte', 1),
    6: ('raw-byte', 1), 7: ('raw-byte', 1), 8: ('raw-byte', 1),
    9: ('raw-byte', 1), 10: ('boolean', 1), 32: ('raw-byte', 1),
    33: ('raw-byte', 1), 34: ('raw-byte', 1), 35: ('raw-byte', 1),
    36: ('raw-byte', 1), 37: ('raw-byte', 1),
}
PAGE_ROWS = [
    ('Hypothesis', 'OP11 production-test parameter; keys 0,1,2,4,5', 'Unknown',
     'Position Unknown; through end-of-data', 'Opaque bytes', 'Unknown',
     'Sentinel Unknown; default Unknown; row order is not key association',
     'Minimum/maximum length Unknown; zero length representable; empty-request acceptance Unknown'),
    ('Hypothesis', 'OP11 production-test parameter; keys 3,6,7,8,9,32,33,34,35,36,37', 'Unknown',
     'Position Unknown; one byte', 'Raw byte 00..FF', 'Unknown',
     'Sentinel Unknown; default Unknown; row order is not key association',
     'Meaning, unit and additional constraints Unknown'),
    ('Hypothesis', 'OP11 production-test parameter; key 10', 'Unknown',
     'Position Unknown; one byte', 'Boolean 0=no, 1=yes; 2 unmapped', 'Unknown',
     'Sentinel Unknown; default Unknown; no meaning invented for other values',
     'Behavior for unmapped values Unknown'),
    ('Hypothesis', 'OP02 backlight-only outputs', 'Unknown',
     'Position Unknown; one byte', 'Bit 0 backlight; mask 01; reserved mask FE', 'Unknown',
     'Sentinel Unknown; default Unknown; reserved bits retained raw',
     'Bits 1..7 reserved; variant selection Unknown; no automatic choice'),
    ('Hypothesis', 'OP02 three-output outputs', 'Unknown',
     'Position Unknown; one byte', 'Bits 0..2 outputs 1..3; mask 07; reserved mask F8', 'Unknown',
     'Sentinel Unknown; default Unknown; reserved bits retained raw',
     'Bits 3..7 reserved; variant selection Unknown; no automatic choice'),
    ('Hypothesis', 'EEPROM checksum_type; operation Unknown', 'Unknown',
     'Position Unknown; type one byte; returned width Unknown',
     '00=query-supported-types; 01..7F=scalar-type; 80 unmapped', 'Unknown',
     'Sentinel Unknown; default Unknown; scalar, not flags; conflicting EEPROM algorithm assignments withdrawn',
     'Algorithm Unknown; returned checksum width Unknown; completion Unknown; checksum data Unknown'),
]


class B506Declarations(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def test_finite_identity_and_qualification(self):
        d = self.data
        self.assertEqual((d['family'], d['primary'], d['secondary'], d['grade'],
                          d['native_qualification'], d['physical_qualification']),
                         ('vaillant', 181, 6, 'Hypothesis', 'Unknown', 'Unknown'))
        p = d['parameters']
        self.assertEqual((p['operation'], p['variant'], p['field']),
                         (17, 'production-test', 'parameter'))
        self.assertEqual([(v['operation'], v['variant'], v['field']) for v in d['outputs']],
                         [(2, 'backlight-only', 'outputs'), (2, 'three-output', 'outputs')])
        c = d['checksum']
        self.assertEqual((c['operation'], c['variant'], c['field']),
                         (None, 'eeprom-checksum', 'checksum_type'))

    def test_every_explicit_union_key_in_permuted_rows(self):
        rows = self.data['parameters']['rows']
        self.assertEqual(len(rows), 17)
        self.assertNotEqual([r['key'] for r in rows], sorted(PARAMETERS))
        # Every rotation plus reversal; dictionary indexes declarations, not bytes.
        for shift in range(17):
            for ordered in (rows[shift:] + rows[:shift], list(reversed(rows[shift:] + rows[:shift]))):
                actual = {r['key']: r for r in ordered}
                self.assertEqual(set(actual), set(PARAMETERS))
                for key in range(256):
                    with self.subTest(shift=shift, key=key):
                        if key not in PARAMETERS:
                            self.assertNotIn(key, actual)
                            continue
                        r = actual[key]
                        self.assertEqual((r['representation'], r['width']), PARAMETERS[key])
                        self.assertEqual((r['grade'], r['direction'], r['logical_position'],
                                          r['minimum_bytes'], r['maximum_bytes'], r['scale'],
                                          r['sentinel'], r['default']),
                                         ('Hypothesis', None, None, None, None, None, None, None))
                        self.assertEqual(r['boolean_values'], {'0': 'no', '1': 'yes'} if key == 10 else None)
        self.assertEqual(self.data['parameters']['unmapped_keys'], [31, 38])

    def test_opaque_and_boolean_cases(self):
        p = self.data['parameters']
        self.assertEqual(p['opaque_cases'], [
            {'raw': [0, 170, 255], 'length': 3}, {'raw': [], 'length': 0}])
        for case, expected in zip(p['opaque_cases'], (b'\x00\xaa\xff', b'')):
            self.assertEqual(bytes(case['raw']), expected)
            self.assertEqual(len(case['raw']), case['length'])
        self.assertEqual(p['empty_request_acceptance'], 'Unknown')
        boolean = {r['key']: r for r in p['rows']}[10]['boolean_values']
        self.assertEqual((boolean.get('0'), boolean.get('1'), boolean.get('2')), ('no', 'yes', None))

    def test_output_alternatives_and_raw_arithmetic(self):
        for row, expected in zip(self.data['outputs'], (
                ('backlight-only', 1, 254, 7, 1, 6),
                ('three-output', 7, 248, 7, 7, 0))):
            self.assertEqual(tuple(row[k] for k in ('variant', 'output_mask', 'reserved_mask', 'raw', 'active', 'reserved')), expected)
            self.assertEqual(row['raw'] & row['output_mask'], expected[4])
            self.assertEqual(row['raw'] & row['reserved_mask'], expected[5])
            self.assertEqual(row['active'] | row['reserved'], 7)
            self.assertEqual((row['direction'], row['logical_position'], row['width'],
                              row['scale'], row['sentinel'], row['default']),
                             (None, None, 1, None, None, None))

    def test_checksum_is_scalar_with_separate_unknowns(self):
        c = self.data['checksum']
        self.assertEqual((c['interpretation'], c['query'], c['scalar_min'], c['scalar_max']),
                         ('scalar, not flags', 0, 1, 127))
        self.assertEqual([(v['raw'], v['meaning']) for v in c['cases']], [
            (0, 'query-supported-types'), (1, 'scalar-type'), (3, 'scalar-type'),
            (127, 'scalar-type'), (128, None)])
        self.assertEqual((c['direction'], c['logical_position'], c['type_width'], c['scale'],
                          c['sentinel'], c['default'], c['algorithm'],
                          c['returned_checksum_width'], c['completion'], c['checksum_data']),
                         (None, None, 1, None, None, None, 'Unknown', None, 'Unknown', 'Unknown'))

    def test_structured_page_claims_with_grade_conflict_and_unknowns(self):
        section = self.page.split('## Scoped parameter and checksum declarations\n', 1)[1].split('## Profiles', 1)[0]
        lines = [line for line in section.splitlines() if line.startswith('|')]
        self.assertEqual(len(lines), 8)
        self.assertEqual(tuple(cell.strip() for cell in lines[0].strip('|').split('|')), (
            'Grade', 'Identity (PB B5 / SB 06, Vaillant family)', 'Direction',
            'Logical position / extent', 'Raw type / domain', 'Scale',
            'Sentinel / default / conflict', 'Unresolved properties'))
        actual = [tuple(cell.strip() for cell in line.strip('|').split('|')) for line in lines[2:]]
        self.assertEqual(actual, PAGE_ROWS)
        for statement in (
            'row order has no meaning. All other keys remain unmapped.',
            'Logical position is not a wire offset.',
            'Native wire qualification and physical qualification\nare **Unknown**.',
            '[synthetic cases](fixtures/ae06_b506_candidates.json)',
            'backlight-only retains active bits `01` and reserved\nbits `06`',
            'three-output retains active bits `07` and reserved bits `00`',
            'Checksum `03` is one scalar type, not flags `01` and `02`;',
            '`80` has no new declared type.',
        ):
            self.assertIn(statement, section)
        # Reject the earlier conflicting blanket claims, outside the new table too.
        self.assertNotIn('ROM and EEPROM check**', self.page)
        self.assertNotIn('sets, reply bodies and framing beyond this byte are unknown', self.page)
        self.assertNotIn('| EEPROM checksum or CRC request | 2 | 3 |', self.page)
        self.assertIn('OP11 parameter representations have the explicit keyed Hypothesis declarations', self.page)
        self.assertIn('EEPROM\n  algorithm, returned checksum width, completion, checksum data and operation', self.page)
        self.assertIn('are superseded by this declaration. Their algorithm assignments, operation\n'
                      'associations and fixed 16-bit checksum width are withdrawn;', section)
        with (ROOT / 'protocols/vaillant/fixtures/b506-b508-candidate-fields.csv').open() as source:
            eeprom_rows = [row for row in csv.DictReader(source)
                           if row['op'] in ('B5 06 0F', 'B5 06 10')]
        self.assertEqual(len(eeprom_rows), 5)
        for row in eeprom_rows:
            self.assertEqual(row['candidate_variant'],
                             'Superseded by ../ebus-vaillant-B506.md#scoped-parameter-and-checksum-declarations; '
                             'algorithm, operation association and returned checksum width Unknown')


if __name__ == '__main__':
    unittest.main()
