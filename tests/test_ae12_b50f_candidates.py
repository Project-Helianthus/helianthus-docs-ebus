"""Finite page/fixture acceptance checks; no runtime decoder coverage claimed."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-vaillant-B50F.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ae12_b50f_candidates.json'


def expected_rows():
    """Independent, finite declarations; missing metadata is not a wildcard."""
    rows = []

    def add(op, field, position, raw, scale, conflict, unresolved):
        rows.append(['Hypothesis',
                     f'vaillant / B50F / PB=B5 / SB=0F / OP={op} / {field}',
                     'Unknown', position, raw, scale, conflict, unresolved])

    add('03', 'demand', 'Unknown / 8 bits',
        'uint8 00..FF; bits 0..4: five positional flags, individual meanings Unknown; bits 5..7 reserved',
        'none', 'Sentinel/default Unknown; demand is not applied actuation',
        'Reserved semantics and physical effect Unknown; preserve all bits')
    for op, fields in [('00', (1, 2, 3)), ('01', (1, 2))]:
        for field in fields:
            add(op, f'temperature_{field}', 'Unknown / 16 bits',
                'signed int16 little-endian -32768..32767',
                'divide by 16 / degrees Celsius', 'Sentinel/default Unknown',
                'Absolute scalar position and channel meaning Unknown')
            add(op, f'error_{field}',
                f'immediately after temperature_{field} / 8 bits',
                'uint8 00..FF', 'none',
                'Sentinel/default Unknown; independent raw error byte',
                'Absolute scalar position and error meanings Unknown')
    add('01', 'stack_voltage_label', 'Unknown / 16 bits',
        'raw ordered pair 00..FF each', 'Unknown / Unknown',
        'Stack-voltage label conflicts with temperature conversion metadata; no voltage scale chosen; sentinel/default Unknown',
        'Conversion, unit, signedness and absolute scalar position Unknown')
    for op, positions in [('00', '12, 13'), ('01', '12, 13'),
                          ('02', '11, 12'), ('03', '4, 5')]:
        add(op, 'integrity', positions + ' / two independent 8-bit bytes',
            'two uint8 00..FF; ordered bytes, not a word', 'none',
            'Sentinel/default Unknown; preserve each byte independently',
            'Word byte order, polynomial, initialization, reflection, final transform and coverage Unknown')
    for op in ('00', '01', '02', '03'):
        add(op, 'feedback', 'Unknown / 8 bits',
            'uint8 00..FF; 01 accepted; 00 and 02..FF rejected', 'none',
            'Sentinel/default Unknown; acceptance does not validate integrity',
            'Physical effect Unknown; feedback does not establish physical effect')
    return rows


class B50FCandidates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.page = PAGE.read_text()
        cls.rows = [[c.strip() for c in line.strip('|').split('|')]
                    for line in cls.page.splitlines() if line.startswith('|')]

    def test_finite_scope_and_explicit_unknowns(self):
        self.assertEqual(self.fixture['scope'], {
            'family': 'vaillant', 'variant': 'B50F', 'primary': 181,
            'secondary': 15, 'qualification': 'Unknown',
            'native_evidence': 'Unknown', 'grade': 'Hypothesis'})
        self.assertIn('None is Proven.', self.page)
        self.assertIn('no broader completed catalog', self.page)
        self.assertIn('A logical\nposition is not a wire offset.', self.page)
        self.assertIn('[synthetic examples](fixtures/ae12_b50f_candidates.json)', self.page)

    def test_structured_page_and_fixture_declarations(self):
        columns = ['Grade', 'Identity', 'Direction', 'Logical position / extent',
                   'Raw type / domain', 'Scale / unit',
                   'Sentinel / default / conflict', 'Unresolved properties']
        self.assertEqual(self.fixture['columns'], columns)
        self.assertEqual(self.rows, [columns, ['---'] * 8] + expected_rows())
        self.assertEqual(self.fixture['declarations'], expected_rows())

    def test_demand_individual_and_reserved_bits(self):
        expected = [
            ['00', [False, False, False, False, False], '00'],
            ['01', [True, False, False, False, False], '00'],
            ['1F', [True, True, True, True, True], '00'],
            ['E0', [False, False, False, False, False], 'E0'],
            ['FF', [True, True, True, True, True], 'E0'],
            ['02', [False, True, False, False, False], '00'],
            ['04', [False, False, True, False, False], '00'],
            ['08', [False, False, False, True, False], '00'],
            ['10', [False, False, False, False, True], '00'],
            ['20', [False, False, False, False, False], '20'],
            ['40', [False, False, False, False, False], '40'],
            ['80', [False, False, False, False, False], '80']]
        self.assertEqual(self.fixture['demand_cases'], expected)
        # Arithmetic validates these synthetic examples, not a production path.
        for raw, flags, reserved in self.fixture['demand_cases']:
            self.assertEqual(int(raw, 16), sum(mask for mask, on in
                             zip((1, 2, 4, 8, 16), flags) if on) + int(reserved, 16))

    def test_signed_arithmetic_and_adjacent_errors(self):
        self.assertEqual(self.fixture['temperature_cases'],
                         [['F0 FF', -16, -1], ['00 00', 0, 0], ['10 00', 16, 1]])
        self.assertEqual(0xF0 + 256 * 0xFF - 65536, -16)
        self.assertEqual(-16 / 16, -1)
        self.assertEqual(0 / 16, 0)
        self.assertEqual(16 / 16, 1)
        self.assertEqual(self.fixture['error_cases'],
                         [['F0 FF', '00', -1], ['F0 FF', '01', -1], ['F0 FF', 'FF', -1]])
        expected = []
        for op, channel in [('00', 1), ('00', 2), ('00', 3), ('01', 1), ('01', 2)]:
            for raw, error, value in [('F0 FF', '00', -1), ('F0 FF', '01', -1),
                                      ('F0 FF', 'FF', -1), ('00 00', '00', 0),
                                      ('10 00', '00', 1)]:
                expected.append([op, channel, raw, error, value])
        self.assertEqual(self.fixture['channel_cases'], expected)

    def test_stack_voltage_conflict_is_not_converted(self):
        self.assertEqual(self.fixture['stack_voltage_case'], {
            'raw': '10 00', 'label': 'stack-voltage', 'converted_value': None,
            'unit': None, 'conflict': 'temperature conversion metadata'})
        self.assertIn('not 1 volt.', self.page)

    def test_integrity_order_and_each_byte_at_every_coordinate(self):
        expected = []
        for op, positions in [('00', [12, 13]), ('01', [12, 13]),
                              ('02', [11, 12]), ('03', [4, 5])]:
            for pair in [['00', '00'], ['12', '00'], ['00', '34'], ['12', '34']]:
                expected.append([op, positions, pair, None])
        self.assertEqual(self.fixture['integrity_cases'], expected)
        self.assertIn('never composed into a CRC word.', self.page)

    def test_feedback_independent_of_integrity_and_effect(self):
        expected = []
        for op in ['00', '01', '02', '03']:
            for pair in [['00', '00'], ['12', '00'], ['00', '34'], ['12', '34']]:
                for raw, accepted in [('00', False), ('01', True),
                                      ('02', False), ('FF', False)]:
                    expected.append([op, pair, raw, accepted, None, None])
        self.assertEqual(self.fixture['feedback_cases'], expected)
        self.assertIn('Acceptance does not validate\nintegrity and does not establish physical effect.', self.page)

    def test_partial_current_does_not_consume_last_known_good(self):
        self.assertEqual(self.fixture['partial_case'], {
            'operation': '00', 'positions': [12, 13], 'current': ['12', None],
            'last_known_good': ['12', '34'], 'current_word': None,
            'admitted_as_complete': False})
        self.assertIn('not admitted as complete', self.page)
        self.assertIn('does not fill the missing current byte', self.page)


if __name__ == '__main__':
    unittest.main()
