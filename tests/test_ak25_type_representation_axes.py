"""Finite synthetic contracts; arithmetic oracles do not assert native support."""
import json
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]


def arithmetic(c):
    raw = bytes(c['raw'])
    if len(raw) * 8 != c['width_bits']:
        return None
    rep = c['representation']
    if rep == 'integer':
        return int.from_bytes(raw, c['byte_order'], signed=c['signedness'] == 'signed')
    if rep == 'binary32':
        return struct.unpack('<f', raw)[0]
    if rep == 'packed-decimal':
        high, low = divmod(raw[0], 16)
        return high * 10 + low if high <= 9 and low <= 9 else None
    if rep == 'unpacked-decimal':
        return int(''.join(str(b) for b in raw)) if all(b <= 9 for b in raw) else None
    if rep == 'ASCII-digits':
        return int(raw.decode('ascii')) if all(48 <= b <= 57 for b in raw) else None
    raise AssertionError(rep)


def raw_text(raw):
    return ' '.join(format(b, '02X') for b in raw) or 'empty'


def output(value):
    return 'invalid' if value is None else str(value)


def row(fields):
    return '| ' + ' | '.join(str(f) for f in fields) + ' |'


class RepresentationAxes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'types/fixtures/ak25_type_representation_axes.json').read_text())
        cls.page = (ROOT / 'types/ak25_type_representation_axes.md').read_text()

    def test_finite_cases_and_independent_arithmetic(self):
        # Independent inputs/results pin both valid and invalid digit positions.
        expected = [
            ('packed42', 'packed-decimal', [0x42], 8, 42),
            ('packed00', 'packed-decimal', [0], 8, 0),
            ('packed99', 'packed-decimal', [0x99], 8, 99),
            ('packedFA', 'packed-decimal', [0xFA], 8, None),
            ('packed_low_invalid', 'packed-decimal', [0x4A], 8, None),
            ('packed_empty', 'packed-decimal', [], 8, None),
            ('packed_wide', 'packed-decimal', [0, 0x42], 8, None),
            ('unpacked-decimal_42', 'unpacked-decimal', [4, 2], 16, 42),
            ('unpacked-decimal_leading', 'unpacked-decimal', [0, 2], 16, 2),
            ('unpacked-decimal_invalid', 'unpacked-decimal', [4, 10], 16, None),
            ('unpacked-decimal_ascii', 'unpacked-decimal', [0x34, 0x32], 16, None),
            ('unpacked-decimal_short', 'unpacked-decimal', [4], 16, None),
            ('ASCII-digits_42', 'ASCII-digits', [0x34, 0x32], 16, 42),
            ('ASCII-digits_leading', 'ASCII-digits', [0x30, 0x32], 16, 2),
            ('ASCII-digits_invalid', 'ASCII-digits', [0x34, 0x41], 16, None),
            ('ASCII-digits_unpacked', 'ASCII-digits', [4, 2], 16, None),
            ('ASCII-digits_short', 'ASCII-digits', [0x34], 16, None),
            ('signed_le', 'integer', [0xFE, 0xFF], 16, -2),
            ('signed_be', 'integer', [0xFE, 0xFF], 16, -257),
            ('unsigned_le', 'integer', [0xFE, 0xFF], 16, 65534),
            ('signed_min', 'integer', [0, 0x80], 16, -32768),
            ('signed_max', 'integer', [0xFF, 0x7F], 16, 32767),
            ('integer_short', 'integer', [0xFE], 16, None),
            ('float', 'binary32', [0, 0, 0xC0, 0x3F], 32, 1.5),
            ('float_integer', 'integer', [0, 0, 0xC0, 0x3F], 32, 1069547520),
            ('float_short', 'binary32', [0, 0xC0, 0x3F], 32, None),
        ]
        self.assertEqual(len(self.data['cases']), len(expected))
        for c, (name, rep, raw, width, value) in zip(self.data['cases'], expected):
            with self.subTest(case=name):
                self.assertEqual((c['id'], c['representation'], c['raw'], c['width_bits'], c['expected']),
                                 (name, rep, raw, width, value))
                order = 'big' if name == 'signed_be' else 'little'
                signed = 'unsigned' if name in ('unsigned_le', 'float_integer') else 'signed'
                self.assertEqual(c['byte_order'], order if rep in ('integer', 'binary32') else 'not-applicable')
                self.assertEqual(c['signedness'], signed if rep == 'integer' else 'not-applicable')
                self.assertEqual(arithmetic(c), value)
                self.assertIn(row([name, rep, raw_text(raw), width, c['byte_order'], c['signedness'], output(value), 'Unknown']), self.page)

    def test_each_scenario_axis_independently(self):
        baseline = dict(representation='integer', raw=[0x34, 0x32], width_bits=16,
                        byte_order='little', signedness='unsigned', computation='identity', unit='Unknown')
        specifications = [
            ('base', {}, 12852),
            ('representation', {'representation': 'ASCII-digits'}, 42),
            ('width_bits', {'width_bits': 8}, None),
            ('byte_order', {'byte_order': 'big'}, 13362),
            ('computation', {'computation': 'raw/16'}, 803.25),
            ('unit', {'unit': 'degrees Celsius'}, 12852),
            ('sign_control', {'raw': [0xFE, 0xFF]}, 65534),
            ('signedness', {'raw': [0xFE, 0xFF], 'signedness': 'signed'}, -2),
        ]
        self.assertEqual(len(self.data['scenarios']), len(specifications))
        contracts = {}
        for s, (name, changes, expected) in zip(self.data['scenarios'], specifications):
            with self.subTest(axis=name):
                contract = dict(baseline, **changes)
                self.assertEqual(s['id'], name)
                self.assertEqual(s['contract'], contract)
                self.assertEqual(s['expected'], expected)
                value = arithmetic(contract)
                if value is not None and contract['computation'] == 'raw/16':
                    value /= 16
                self.assertEqual(value, expected)
                self.assertIn(row([name, contract['representation'], raw_text(contract['raw']),
                                   contract['width_bits'], contract['byte_order'], contract['signedness'],
                                   contract['computation'], contract['unit'], output(expected), 'Unknown']), self.page)
                contracts[name] = contract
        for axis in ('representation', 'width_bits', 'byte_order', 'computation', 'unit', 'signedness'):
            control = contracts['sign_control' if axis == 'signedness' else 'base']
            self.assertEqual([key for key in control if control[key] != contracts[axis][key]], [axis])

    def test_raw_characters_are_lossless(self):
        self.assertEqual(self.data['fixed_characters'], dict(
            raw=[65, 0, 66, 0, 0], retained=[65, 0, 66, 0, 0], width_bits=40,
            grade='Proven', native='Unknown', text_encoding='Unknown', termination='Unknown',
            padding='Unknown', normalization='Unknown'))
        self.assertIn(row(['41 00 42 00 00', '41 00 42 00 00', 40] + ['Unknown'] * 5), self.page)

    def test_width_raw_and_semantic_domains_are_independent(self):
        expected = []
        for limit, admitted in [(100, True), (40, False)]:
            expected.append(dict(width_bits=16, raw_domain=[0, 65535], allowed_semantic_domain=[0, limit],
                                 value=42, admitted=admitted, grade='Hypothesis', native='Unknown'))
            self.assertEqual(0 <= 42 <= limit, admitted)
            self.assertIn(row([16, '0..65535', f'0..{limit}', 42, str(admitted).lower(), 'Unknown']), self.page)
        self.assertEqual(self.data['domains'], expected)
        self.assertEqual(int.from_bytes(bytes([255, 255]), 'little'), 2 ** 16 - 1)

    def test_grades_and_every_unknown_boundary(self):
        self.assertEqual(self.data['provenance'], 'synthetic arithmetic only')
        self.assertEqual(self.data['contract_grade'], 'Hypothesis')
        self.assertEqual(self.data['qualification'], 'Unknown')
        self.assertEqual(self.data['unknown'], {k: 'Unknown' for k in (
            'native_field_selection', 'mixed_encodings', 'decimal_sign_conventions',
            'physical_qualification', 'native_support', 'physical_effects', 'persistence', 'delivery')})
        for c in self.data['cases'] + self.data['scenarios']:
            with self.subTest(row=c['id']):
                self.assertEqual((c['grade'], c['native']), ('Proven', 'Unknown'))
        # Exact table row count prevents extra unsupported rows being appended.
        rows = [line for line in self.page.splitlines() if line.startswith('| ')]
        self.assertEqual(len(rows), 26 + 8 + 1 + 2 + 4)
        for statement in (
            '**Hypothesis:** a family type contract states representation, signedness, bit\nwidth, byte order, computation and unit as separate axes.',
            'Packed decimal uses two decimal nibbles; unpacked decimal uses\none decimal digit per byte; ASCII digits use bytes 30 through 39 hex.',
            'Unit metadata alone adds no 273.15.',
            'a fixed character field retains embedded and trailing zero bytes and\nall raw bytes.',
            '**Unknown:** native field selection, mixed encodings, decimal sign conventions,\nphysical qualification, native support, physical effects, persistence and delivery.',
            'Mathematical **Proven** and candidate **Hypothesis** grades do not qualify any of\nthose properties.',
            'No codec implementation, namespace, generic family schema or replacement for\nexisting B524 helpers is added.',
        ):
            self.assertIn(statement, self.page)
        self.assertIn('[primitive declarations](primitives.md)', self.page)
        self.assertIn('[synthetic tables](fixtures/ak25_type_representation_axes.json)', self.page)


if __name__ == '__main__':
    unittest.main(verbosity=2)
