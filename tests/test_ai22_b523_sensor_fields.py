"""Independent finite contract and arithmetic checks; no device evidence."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-b523-sensor-fields.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ai22_b523_sensor_fields.json'
# Constants are local oracles, never populated from the page or fixture.
LAYOUT = (
    ('03', ('S1', 'S2', 'S3', 'S4', 'S5', 'S6'), (3, 5, 7, 9, 11, 13), 16, 17, 4),
    ('06', ('S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7'), (3, 5, 7, 9, 11, 13, 15), 17, 18, 6),
    ('07', ('S8', 'S9', 'S10', 'S11', 'S12', 'S13'), (3, 5, 7, 9, 12, 14), 16, 17, 4),
)
VARIANTS = ('zero-valid-value', 'zero-valid-value-or-low-level')
LABELS = (
    ('valid-value', 'open-circuit', 'closed-circuit', 'high-level'),
    ('valid-value-or-low-level', 'open-circuit', 'closed-circuit', 'high-level'),
)
WORDS = (
    ('00 80', 'replacement', 32768), ('10 00', 'normal', 1),
    ('F0 FF', 'normal', -1), ('00 00', 'normal', 0),
    ('FF 7F', 'normal', 2047.9375), ('01 80', 'normal', -2047.9375),
    ('FF FF', 'normal', -0.0625),
)


def expected_tables():
    occurrences = []
    for op, sensors, positions, first, last, _ in LAYOUT:
        for i, (sensor, pos) in enumerate(zip(sensors, positions)):
            occurrences.append([op, sensor, str(pos), str(first if i < 4 else last),
                                str(i % 4 * 2), 'Hypothesis'])
    return {
        'Occurrences': {
            'headers': ['OP', 'Sensor', 'Word position', 'Status position', 'Pair bit', 'Grade'],
            'rows': occurrences},
        'Branches': {
            'headers': ['Branch', 'Selector', 'Encoding', 'Divisor', 'Unit', 'Raw minimum',
                        'Raw maximum', 'Default', 'Scaled minimum', 'Scaled maximum', 'Grade'],
            'rows': [
                ['replacement', 'raw-u16 == 32768', 'LE u16', '1', 'raw', '0', '65535',
                 '32768', '0', '65535', 'Hypothesis'],
                ['normal', 'raw-u16 != 32768', 'LE i16', '16', 'Celsius', '-32768',
                 '32767', '0', '-2048', '2047.9375', 'Hypothesis']]},
        'Status alternatives': {
            'headers': ['Variant', '0', '1', '2', '3', 'Default', 'Grade'],
            'rows': [[variant, *labels, '0', 'Hypothesis']
                     for variant, labels in zip(VARIANTS, LABELS)]},
        'Reserved tails': {
            'headers': ['OP', 'Position', 'First bit', 'Last bit', 'Grade'],
            'rows': [['03', '17', '4', '7', 'Hypothesis'],
                     ['06', '18', '6', '7', 'Hypothesis'],
                     ['07', '17', '4', '7', 'Hypothesis']]},
        'Auxiliary fields': {
            'headers': ['OP', 'Field', 'Position', 'Encoding', 'Divisor', 'Unit',
                        'Raw minimum', 'Raw maximum', 'Scaled minimum', 'Scaled maximum',
                        'Default', 'Grade'],
            'rows': [
                ['03', 'PWM', '15', 'u8', '2', 'percent', '0', '255', '0', '127.5',
                 'Unknown', 'Hypothesis'],
                ['07', 'opaque', '11', 'u8', 'none', 'Unknown', '0', '255', 'Unknown',
                 'Unknown', 'Unknown', 'Hypothesis']]},
        'Word examples': {
            'headers': ['Bytes in order', 'Raw u16', 'Branch', 'Value', 'Unit', 'Grade'],
            'rows': [['00 80', '32768', 'replacement', '32768', 'raw', 'Proven'],
                     ['10 00', '16', 'normal', '1', 'Celsius', 'Proven'],
                     ['F0 FF', '65520', 'normal', '-1', 'Celsius', 'Proven']]},
    }


def page_tables(text):
    result = {}
    title = None
    for line in text.splitlines():
        if line.startswith('## '):
            title = line[3:]
        elif line.startswith('|'):
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            if all(cell == '---' for cell in cells):
                continue
            if title not in result:
                result[title] = {'headers': cells, 'rows': []}
            else:
                result[title]['rows'].append(cells)
    return result


def vector(op):
    # A synthetic logical-coordinate container, not a wire frame.
    return bytearray([0xB5, 0x23, int(op, 16)] + [0] * 16)


def expected_cases():
    cases = []
    for op, sensors, positions, first, last, _ in LAYOUT:
        for i, (sensor, pos) in enumerate(zip(sensors, positions)):
            for raw, branch, value in WORDS:
                data = vector(op)
                data[pos:pos + 2] = bytes.fromhex(raw)
                cases.append(dict(kind='sensor', op=op, field=sensor, bytes=data.hex(),
                                  branch=branch, value=value))
            for variant, labels in zip(VARIANTS, LABELS):
                for state in range(4):
                    data = vector(op)
                    data[first if i < 4 else last] = state * (4 ** (i % 4))
                    cases.append(dict(kind='status', op=op, field=sensor, variant=variant,
                                      bytes=data.hex(), state=state, label=labels[state]))
    for op, _, _, _, last, start in LAYOUT:
        for bit in range(start, 8):
            data = vector(op)
            data[last] = 2 ** bit
            cases.append(dict(kind='reserved', op=op, bit=bit, bytes=data.hex(),
                              retained=2 ** bit, sensor_state_claim=None))
    for raw in (0, 1, 200, 201, 254, 255):
        data = vector('03')
        data[15] = raw
        cases.append(dict(kind='pwm', op='03', bytes=data.hex(), value=raw * 0.5))
    for raw in (0, 1, 128, 255):
        data = vector('07')
        data[11:16] = bytes([raw, 16, 0, 240, 255])
        cases.append(dict(kind='opaque', op='07', bytes=data.hex(), value=raw, S12=1, S13=-1))
    return cases


def decode_sensor(data, row, tables):
    pos = int(row[2])
    raw = int.from_bytes(data[pos:pos + 2], 'little')
    replacement, normal = tables['Branches']['rows']
    branch = replacement if raw == int(replacement[7]) else normal
    number = int.from_bytes(data[pos:pos + 2], 'little', signed=branch[2] == 'LE i16')
    return branch[0], number / int(branch[3]), data.hex()


class SensorFieldsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.text = PAGE.read_text()

    def test_page_tables_and_fixture_against_independent_contract(self):
        want = expected_tables()
        self.assertEqual(page_tables(self.text), want)
        self.assertEqual(self.fixture['tables'], want)
        self.assertEqual(set(self.fixture), {'family', 'synthetic', 'native_grade',
                         'physical_qualification', 'tables', 'cases'})
        self.assertEqual(self.fixture['family'], 'Vaillant B523')
        self.assertIs(self.fixture['synthetic'], True)
        self.assertEqual(self.fixture['native_grade'], 'Hypothesis')
        self.assertEqual(self.fixture['physical_qualification'], 'Unknown')
        self.assertEqual(len(want['Occurrences']['rows']), 19)

    def test_complete_ordered_synthetic_tuples(self):
        expected = expected_cases()
        self.assertEqual(len(expected), 305)
        self.assertEqual(self.fixture['cases'], expected)
        self.assertEqual(sum(c['kind'] == 'sensor' for c in expected), 133)
        self.assertEqual(sum(c['kind'] == 'status' for c in expected), 152)
        self.assertEqual(sum(c['kind'] == 'reserved' for c in expected), 10)

    def test_sensor_arithmetic_and_word_isolation(self):
        tables = self.fixture['tables']
        for case in self.fixture['cases']:
            if case['kind'] != 'sensor':
                continue
            data = bytes.fromhex(case['bytes'])
            for row in tables['Occurrences']['rows']:
                if row[0] != case['op']:
                    continue
                with self.subTest(op=case['op'], target=case['field'], sensor=row[1], raw=data.hex()):
                    expected = (case['branch'], case['value']) if row[1] == case['field'] else ('normal', 0)
                    self.assertEqual(decode_sensor(data, row, tables), (*expected, data.hex()))
            for row in tables['Occurrences']['rows']:
                if row[0] == case['op']:
                    self.assertEqual((data[int(row[3])] >> int(row[4])) & 3, 0)

    def test_status_pairs_variants_and_reserved_bits(self):
        tables = self.fixture['tables']
        for case in self.fixture['cases']:
            if case['kind'] not in ('status', 'reserved'):
                continue
            data = bytes.fromhex(case['bytes'])
            for row in tables['Occurrences']['rows']:
                if row[0] != case['op']:
                    continue
                with self.subTest(kind=case['kind'], op=case['op'], sensor=row[1], case=case):
                    state = (data[int(row[3])] >> int(row[4])) & 3
                    expected = case['state'] if case['kind'] == 'status' and case['field'] == row[1] else 0
                    self.assertEqual(state, expected)
                    self.assertEqual(decode_sensor(data, row, tables), ('normal', 0, case['bytes']))
                    for variant, labels in zip(VARIANTS, LABELS):
                        declaration = next(r for r in tables['Status alternatives']['rows'] if r[0] == variant)
                        self.assertEqual(declaration[1 + state], labels[expected])
                        if case['kind'] == 'status' and case['variant'] == variant and case['field'] == row[1]:
                            self.assertEqual(case['label'], labels[state])
            if case['kind'] == 'reserved':
                tail = next(r for r in tables['Reserved tails']['rows'] if r[0] == case['op'])
                self.assertEqual(data[int(tail[1])], case['retained'])
                self.assertEqual(case['retained'], 1 << case['bit'])
                self.assertIsNone(case['sensor_state_claim'])
                self.assertEqual(data.hex(), case['bytes'])

    def test_pwm_full_domain_and_opaque_gap(self):
        tables = self.fixture['tables']
        pwm, opaque = tables['Auxiliary fields']['rows']
        self.assertEqual([n / int(pwm[4]) for n in (0, 255)], [0, 127.5])
        for case in self.fixture['cases']:
            data = bytes.fromhex(case['bytes'])
            if case['kind'] == 'pwm':
                self.assertEqual(data[int(pwm[2])] / int(pwm[4]), case['value'])
            elif case['kind'] == 'opaque':
                self.assertEqual(data[int(opaque[2])], case['value'])
                for sensor, expected in [('S12', 1), ('S13', -1)]:
                    row = next(r for r in tables['Occurrences']['rows'] if r[:2] == ['07', sensor])
                    self.assertEqual(decode_sensor(data, row, tables), ('normal', expected, case['bytes']))

    def test_branch_domains_defaults_and_page_arithmetic(self):
        tables = self.fixture['tables']
        for row in tables['Branches']['rows']:
            self.assertEqual(float(row[5]) / int(row[3]), float(row[8]))
            self.assertEqual(float(row[6]) / int(row[3]), float(row[9]))
            self.assertLessEqual(int(row[5]), int(row[7]))
            self.assertLessEqual(int(row[7]), int(row[6]))
        for raw, unsigned, branch, value, _, _ in page_tables(self.text)['Word examples']['rows']:
            data = bytearray(5)
            data[3:5] = bytes.fromhex(raw)
            self.assertEqual(int.from_bytes(bytes.fromhex(raw), 'little'), int(unsigned))
            self.assertEqual(decode_sensor(data, ['03', 'S1', '3'], tables)[:2], (branch, float(value)))
        self.assertIn('unresolved materialization conflict', self.text)
        self.assertIn('does not establish unavailable', self.text)
        self.assertIn('not telegrams', self.text)
        self.assertIn('ebus-vaillant-B523.md#candidate-layouts', self.text)


if __name__ == '__main__':
    unittest.main()
