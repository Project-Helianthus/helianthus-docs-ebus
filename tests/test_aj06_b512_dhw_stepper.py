"""Offline documentation contracts; independent expectations, no runtime decoder."""
import json
from pathlib import Path
import unittest

AB97_ROOT = Path(__file__).resolve().parents[1]
AB97_NATIVE = 'protocols/vaillant/ebus-b512-dhw-stepper.md'
AB97_FIXTURE = 'protocols/vaillant/fixtures/aj06_b512_dhw_stepper.json'
AB97_API = 'architecture/aj06_b512_dhw_stepper_api.md'


def ab97_expected():
    # Hand-authored expectations from the bounded issue, not loaded from a catalog.
    ab97_rows = {}

    def ab97_add(ab97_op, ab97_side, ab97_field, ab97_position, ab97_encoding,
                 ab97_unit='—', ab97_default='0', ab97_meaning='—',
                 ab97_variant='B512', ab97_secondary='12'):
        ab97_row = [ab97_variant, 'B5', ab97_secondary, ab97_op, ab97_side,
                    ab97_field, str(ab97_position), ab97_encoding, ab97_unit,
                    str(ab97_default), ab97_meaning, 'Hypothesis', 'Unknown']
        ab97_rows[tuple(ab97_row[:6])] = ab97_row

    for ab97_spec in [
        ('03', 'request', 'selector', 3, 'u8', '—', '—', '0=valve-temperature-input (candidate)'),
        ('03', 'positive', 'status', 3, 'u8', '—', '—', '0=okay; 1=disconnected; 2=short-circuit'),
        ('03', 'positive', 'temperature_raw', 4, 'LEu16', 'unresolved', '—', 'raw only; conversion Unknown'),
        ('06', 'request', 'modulation', 4, 'u8/2', 'Unknown (formal Celsius conflict)', '0', 'unit conflict unresolved'),
        ('06', 'request', 'flow', 5, 'u8/10', 'l/min'),
        ('06', 'request', 'temperature_6', 6, 'u8/2', 'Celsius'),
        ('06', 'request', 'temperature_7', 7, 'u8/2', 'Celsius'),
        ('06', 'request', 'temperature_8', 8, 'u8/2', 'Celsius'),
        ('06', 'positive', 'dhw_setpoint', 4, 'u8/2', 'Celsius'),
        ('06', 'positive', 'return', 5, 'u8/2', 'Celsius'),
        ('06', 'positive', 'adjustment', 6, 's8', '—', '-1', 'candidates -1/0/1/2'),
        ('08', 'request', 'inlet', 3, 'signedLE16/16', 'Celsius'),
        ('08', 'positive', 'dhw_setpoint', 3, 'signedLE16/16', 'Celsius'),
        ('08', 'request', 'status', 5, 'u8', '—', 'valid (0)', '00=valid; 55=short; AA=interruption-or-disconnected; other=unmapped'),
    ]:
        ab97_add(*ab97_spec)
    for ab97_side, ab97_names in [
        ('request', ['task-active', 'heat-demand', 'loading-active', 'loading-pump-fault',
                     'condition_4', 'condition_5', 'condition_6', 'condition_7']),
        ('positive', ['loading-disabled', 'internal-test-active', 'ready',
                      'frost-protection-active', 'legionella-demand', 'reset',
                      'reserved_6', 'reserved_7']),
    ]:
        for ab97_bit, ab97_field in enumerate(ab97_names):
            ab97_reserved = ab97_field.startswith('reserved')
            ab97_meaning = ('reserved' if ab97_reserved else
                            'label Unknown' if ab97_field.startswith('condition') else ab97_field)
            ab97_add('06', ab97_side, ab97_field, 3, f'bit {ab97_bit}',
                     '—', '0' if ab97_reserved else 'false', ab97_meaning)
    for ab97_bit in range(8):
        ab97_add('06', 'request', f'inlet_condition_{ab97_bit}' if ab97_bit < 2 else
                 f'inlet_reserved_{ab97_bit}', 9, f'bit {ab97_bit}', '—',
                 'false' if ab97_bit < 2 else '0',
                 'separate inlet-condition flag; label Unknown' if ab97_bit < 2 else 'reserved')
    for ab97_op, ab97_side, ab97_position in [
        ('08', 'request', 6), ('08', 'positive', 5),
        ('09', 'request', 3), ('09', 'positive', 3),
    ]:
        for ab97_bit in range(8):
            ab97_add(ab97_op, ab97_side, 'stepper-release' if ab97_bit == 0 else
                     f'reserved_{ab97_bit}', ab97_position, f'bit {ab97_bit}',
                     '—', 'false' if ab97_bit == 0 else '0',
                     'release does not prove movement' if ab97_bit == 0 else 'reserved')
    for ab97_side in ['request', 'positive']:
        ab97_add('0A', ab97_side, 'declaration', '—', 'untyped', '—', '—', 'no typed body')
        ab97_add('absent', ab97_side, 'declaration', '—', 'untyped', '—', '—',
                 'name supplies no encoded 14 operation', 'B51214', 'F5')
    return ab97_rows


class Ab97Contract(unittest.TestCase):
    def test_ab97_native_table(self):
        ab97_text = (AB97_ROOT / AB97_NATIVE).read_text()
        ab97_rows = [[ab97_cell.strip() for ab97_cell in ab97_line.strip('|').split('|')]
                     for ab97_line in ab97_text.splitlines() if ab97_line.startswith('| ')]
        self.assertEqual(ab97_rows.pop(0), ['Variant', 'PB', 'SB', 'Operation', 'Direction',
                         'Field', 'Position', 'Encoding', 'Unit', 'Default', 'Meaning',
                         'Grade', 'Qualification'])
        self.assertEqual(len(ab97_rows), 74)
        self.assertEqual({tuple(ab97_row[:6]): ab97_row for ab97_row in ab97_rows}, ab97_expected())
        for ab97_phrase in ['Coordinates are logical and include the three-position B5/12/operation prefix.',
                            'Release does not prove movement.',
                            'independent last-known-good fields',
                            'no native capture establishing these offsets or flags',
                            'Exact missing condition labels are **Unknown**',
                            'physical adaptation, solar/two-zone role, support and actual movement',
                            'no stability promise']:
            self.assertIn(ab97_phrase, ab97_text)
        self.assertNotIn('Ab97', ab97_text)

    def test_ab97_synthetic_tuples(self):
        ab97_data = json.loads((AB97_ROOT / AB97_FIXTURE).read_text())
        self.assertEqual(set(ab97_data), {'provenance', 'cases'})
        self.assertEqual(ab97_data['provenance'], 'synthetic arithmetic only; not wire observations')
        self.assertEqual(len(ab97_data['cases']), 196)
        ab97_seen = {}
        for ab97_case in ab97_data['cases']:
            with self.subTest(ab97_case=ab97_case):
                self.assertEqual(set(ab97_case), {'variant', 'primary', 'secondary', 'operation',
                                 'direction', 'field', 'raw', 'value', 'unit', 'grade',
                                 'qualification', 'movement'})
                ab97_op = ab97_case['operation']
                ab97_identity = (ab97_case['variant'], f"{ab97_case['primary']:02X}",
                                 f"{ab97_case['secondary']:02X}",
                                 'absent' if ab97_op is None else f'{ab97_op:02X}',
                                 ab97_case['direction'], ab97_case['field'])
                ab97_row = ab97_expected()[ab97_identity]
                self.assertEqual(ab97_case['grade'], 'Hypothesis')
                self.assertEqual(ab97_case['qualification'], 'Unknown')
                self.assertEqual(ab97_case['movement'], 'Unknown')
                ab97_raw = ab97_case['raw']
                self.assertTrue(all(type(ab97_byte) is int and 0 <= ab97_byte <= 255 for ab97_byte in ab97_raw))
                self.assertEqual(ab97_raw[:2], [181, 245 if ab97_case['variant'] == 'B51214' else 18])
                if ab97_op is not None:
                    self.assertEqual(ab97_raw[2], ab97_op)
                ab97_encoding = ab97_row[7]
                if ab97_encoding == 'untyped':
                    self.assertEqual(ab97_raw, [181, 245] if ab97_op is None else [181, 18, 10])
                    ab97_value = None
                else:
                    ab97_position = int(ab97_row[6])
                    ab97_byte = ab97_raw[ab97_position]
                    if ab97_encoding.startswith('bit '):
                        ab97_value = bool(ab97_byte & (1 << int(ab97_encoding[-1])))
                    elif ab97_case['field'] == 'selector':
                        ab97_value = {0: 'valve-temperature-input'}.get(ab97_byte, 'unmapped')
                    elif ab97_case['field'] == 'status':
                        ab97_mapping = ({0: 'okay', 1: 'disconnected', 2: 'short-circuit'} if ab97_op == 3
                                        else {0: 'valid', 85: 'short', 170: 'interruption-or-disconnected'})
                        ab97_value = ab97_mapping.get(ab97_byte, 'unmapped')
                    elif ab97_encoding == 'LEu16':
                        ab97_value = int.from_bytes(bytes(ab97_raw[ab97_position:ab97_position + 2]), 'little')
                    elif ab97_encoding == 'signedLE16/16':
                        ab97_value = int.from_bytes(bytes(ab97_raw[ab97_position:ab97_position + 2]), 'little', signed=True) / 16
                    elif ab97_encoding == 's8':
                        ab97_value = ab97_byte - 256 if ab97_byte >= 128 else ab97_byte
                    else:
                        ab97_value = ab97_byte / (10 if ab97_encoding == 'u8/10' else 2)
                self.assertEqual(ab97_case['value'], ab97_value)
                self.assertIs(type(ab97_case['value']), type(ab97_value))
                self.assertEqual(ab97_case['unit'], ab97_row[8] if ab97_row[8] in ['Celsius', 'l/min'] else None)
                ab97_seen.setdefault(ab97_identity, []).append(ab97_case)
        self.assertEqual(set(ab97_seen), set(ab97_expected()))
        for ab97_identity, ab97_row in ab97_expected().items():
            ab97_cases = ab97_seen[ab97_identity]
            if ab97_row[7].startswith('bit '):
                ab97_bit = int(ab97_row[7][-1])
                self.assertEqual(sorted(ab97_case['raw'][int(ab97_row[6])] for ab97_case in ab97_cases),
                                 sorted([0, 1 << ab97_bit, 255 ^ (1 << ab97_bit)]))
            elif ab97_row[5] == 'adjustment':
                self.assertEqual({ab97_case['value'] for ab97_case in ab97_cases}, {-1, 0, 1, 2})
            elif ab97_row[5] == 'status':
                self.assertEqual({ab97_case['raw'][int(ab97_row[6])] for ab97_case in ab97_cases},
                                 {0, 1, 2, 3} if ab97_row[3] == '03' else {0, 85, 170, 84})
            elif ab97_row[5] == 'selector':
                self.assertEqual({ab97_case['raw'][3] for ab97_case in ab97_cases}, {0, 1})
        self.assertEqual(len({json.dumps(ab97_case, sort_keys=True) for ab97_case in ab97_data['cases']}), 196)

    def test_ab97_api_documentation(self):
        ab97_text = (AB97_ROOT / AB97_API).read_text()
        self.assertEqual([ab97_line for ab97_line in ab97_text.splitlines() if ab97_line.startswith('func ')], [
            'func Ab97Entries() ([]Ab97Entry, error)',
            'func Ab97Lookup(ab97Key Ab97Key) (Ab97Entry, bool, error)'])
        ab97_types = {'Family': 'string', 'Variant': 'string', 'Primary': 'uint8',
                      'Secondary': '*uint8', 'Operation': '*uint8', 'Direction': 'string',
                      'Field': 'string', 'Group': '*uint8', 'RequestedInstance': '*uint8',
                      'Register': '*uint16', 'CommandRole': '*string'}
        ab97_rows = [ab97_line for ab97_line in ab97_text.splitlines() if ab97_line.startswith('| Ab97')]
        self.assertEqual(len(ab97_rows), len(ab97_types))
        for ab97_field, ab97_type in ab97_types.items():
            self.assertTrue(any(ab97_line.startswith(f'| Ab97{ab97_field} | {ab97_type} |') for ab97_line in ab97_rows))
        for ab97_phrase in ['absent differs from explicit zero', 'independently owned entries and nested data',
                            'independently owned nested data', 'key\npointers, metadata pointers, value maps and unknown slices',
                            'Ab97Entry{}, false, nil', 'nil, error', 'Ab97Entry{}, false, error',
                            'Admission fails closed', 'Entry grade, label grade, qualification, raw policy and unknown metadata remain\nindependent properties',
                            'Stepper release does\nnot prove movement', 'eBUS MCP compatibility and GraphQL parity',
                            'no stability promise', '../protocols/vaillant/ebus-b512-dhw-stepper.md']:
            self.assertIn(ab97_phrase, ab97_text)


if __name__ == '__main__':
    unittest.main()
