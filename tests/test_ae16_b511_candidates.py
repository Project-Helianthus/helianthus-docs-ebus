"""Finite synthetic declaration acceptance, without a decoder or wire qualification."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-vaillant-b511.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ae16_b511_candidates.json'

# Independently transcribed acceptance tuples, not loaded from either artifact.
# Identity, direction, logical positions/extent, raw domain, scale, meaning,
# unresolved properties. Every row also requires Hypothesis and unknown defaults.
EXPECTED = [
    ('OP04 / Boolean', 'request', '3; extent Unknown', 'Boolean 0/1', 'Unknown',
     '0/1; labels Unknown', 'width and physical prefix Unknown'),
    ('OP07 / flags', 'request', '3; extent Unknown', 'flags byte 0..255', 'none',
     'bit 0 assistant; bit 1 factory-initialization; bits 2..7 reserved',
     'reserved values retained; physical prefix Unknown'),
    ('OP09 / flags', 'request', '3; extent Unknown', 'flags byte 0..255', 'none',
     'bit 0 assistant; bit 1 factory-initialization; bits 2..7 reserved',
     'reserved values retained; physical prefix Unknown'),
    ('OP0B / assistant', 'request', '3; extent Unknown', 'bit 0; carrier width Unknown', 'none',
     'bit 0 assistant; other bits Unknown',
     'factory-initialization not declared; physical prefix Unknown'),
    ('OP0C / mode', 'request', '3; extent Unknown', '0..3; width Unknown', 'none',
     '0 not-in-standby; 1 in-standby; 2 request-enter; 3 request-exit',
     'other values unmapped; physical prefix Unknown'),
    ('OP0A / temperature', 'request', '3; extent Unknown', 'Unknown', 'Unknown',
     'temperature', 'width, unit and physical prefix Unknown'),
    ('OP0A / actuator', 'request', '5; extent Unknown', 'Unknown', 'Unknown',
     'actuator', 'width, bits and physical prefix Unknown'),
    ('OP0D / setpoint', 'request', '3; extent Unknown', 'Unknown', 'Unknown',
     'setpoint', 'width, unit and physical prefix Unknown'),
    ('OP0D / configuration', 'request', '4; extent Unknown', 'Unknown', 'Unknown',
     'configuration', 'width, bits and physical prefix Unknown'),
    ('OP0F / first special-function', 'positive', '4; extent Unknown',
     '{0,1,3,4,5,6,7,8,10}; width Unknown', 'none', 'membership only; labels Unknown',
     'variant selection Unknown; no union; other codes unmapped'),
    ('OP0F / second special-function', 'positive', '4; extent Unknown',
     '{0,1,4,7,10,11}; width Unknown', 'none', 'membership only; labels Unknown',
     'variant selection Unknown; no union; other codes unmapped'),
    ('OP0F / third special-function', 'positive', '4; extent Unknown',
     '{0,1,4,7,10}; width Unknown', 'none', 'membership only; labels Unknown',
     'variant selection Unknown; no union; other codes unmapped'),
    ('OP0F / binding', 'positive', '3; extent Unknown', 'Unknown', 'Unknown',
     'binding', 'width and physical prefix Unknown'),
    ('OP0F / heating', 'positive', '5; extent Unknown', 'Unknown', 'Unknown',
     'heating', 'width and physical prefix Unknown'),
    ('OP0F / error/maintenance/cooling-allowed', 'positive', '6; extent Unknown',
     'Unknown', 'Unknown', 'error/maintenance/cooling-allowed', 'width and physical prefix Unknown'),
    ('OP0F / wish-temperature', 'positive', '7; extent Unknown', 'u8 0..255',
     'raw/2 degrees', 'wish-temperature', 'physical prefix Unknown'),
    ('OP0F / quick-veto hour', 'positive', '8; extent Unknown', '0..255; width Unknown',
     'none', 'raw carrier retained', 'clock validation and physical prefix Unknown'),
    ('OP0F / quick-veto minute', 'positive', '9; extent Unknown', '0..255; width Unknown',
     'none', 'raw carrier retained', 'clock validation and physical prefix Unknown'),
    ('OP0F / event-end hour', 'positive', '10; extent Unknown', '0..255; width Unknown',
     'none', 'raw carrier retained', 'clock validation and physical prefix Unknown'),
    ('OP0F / event-end minute', 'positive', '11; extent Unknown', '0..255; width Unknown',
     'none', 'raw carrier retained', 'clock validation and physical prefix Unknown'),
    ('OP00 / reserved status-byte-one', 'positive', '8; extent 12 abstract positions',
     'status byte 0..255', 'none', 'bit 7 reserved; raw retained',
     'two independent variants; selection and physical prefix Unknown'),
    ('OP00 / fan status-byte-one', 'positive', '8; extent 12 abstract positions',
     'status byte 0..255', 'none', 'bit 7 fan-running 0/1',
     'two independent variants; selection and physical prefix Unknown'),
    ('OP07 / base', 'positive', 'positions 0..7; extent 8 abstract positions', 'Unknown',
     'Unknown', 'base form',
     'physical prefix and widths Unknown; separate from six-field State profile'),
    ('OP07 / extended pressure', 'positive', '8; maximum extent 9 abstract positions',
     '0..100; width Unknown', 'percent', 'building-circuit-pressure',
     'not bar; physical prefix Unknown; separate from six-field State profile'),
    ('OP07 / overlapping room-setpoint', 'positive', '7; maximum extent 9 abstract positions',
     'u8 0..255', 'raw/2 degrees', 'room-setpoint',
     'other structures overlap 7; do not concatenate; selection Unknown'),
    ('name 10 / partial prefix', 'request', '0; extent Unknown', 'B5; width Unknown',
     'none', 'encoded selector absent; body absent',
     'suffix is not an operation byte; physical prefix and installed support Unknown'),
    ('name 10 / partial prefix', 'positive', '0; extent Unknown', 'F5; width Unknown',
     'none', 'encoded selector absent; body absent',
     'suffix is not an operation byte; physical prefix and installed support Unknown'),
    ('name 11 / partial prefix', 'request', '0; extent Unknown', 'B5; width Unknown',
     'none', 'encoded selector absent; body absent',
     'suffix is not an operation byte; physical prefix and installed support Unknown'),
    ('name 11 / partial prefix', 'positive', '0; extent Unknown', 'F5; width Unknown',
     'none', 'encoded selector absent; body absent',
     'suffix is not an operation byte; physical prefix and installed support Unknown'),
]


def expected_rows():
    return [['Hypothesis', *row[:6], 'sentinel/default Unknown', row[6]]
            for row in EXPECTED]


class B511Candidates(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.text = PAGE.read_text()

    def test_complete_fixture_declarations(self):
        self.assertEqual(self.data['evidence'], 'synthetic; no observed telegrams')
        self.assertEqual(self.data['physical_qualification'], 'Unknown')
        self.assertEqual(self.data['columns'], ['grade', 'identity', 'direction',
            'logical position/extent', 'raw type/domain', 'scale', 'meaning',
            'sentinel/default/conflict', 'unresolved'])
        self.assertEqual(len(self.data['declarations']), 29)
        self.assertEqual(self.data['declarations'], expected_rows())

    def test_structured_page_claims_and_nearby_uncertainty(self):
        section = self.text.split('### Bounded request and response-variant declarations\n', 1)[1]
        section = section.split('Candidate codec notes', 1)[0]
        rows = [[cell.strip() for cell in line.strip('|').split('|')]
                for line in section.splitlines() if line.startswith('| Hypothesis')]
        self.assertEqual(rows, expected_rows())
        for statement in ('A logical position is not a wire offset.',
                          'No universal empty poll or default control\narguments follow; absent arguments remain absent.',
                          'fixtures/ae16_b511_candidates.json',
                          'physical qualification, which remains **Unknown**',
                          'no\nbroader catalog completion or installed support follows.'):
            self.assertIn(statement, section)
        self.assertNotIn('| `10` |', self.text)
        self.assertNotIn('| `11` |', self.text)
        self.assertNotIn('Class `0F` special function (candidate): the base values', self.text)
        self.assertIn('partial names `10` and `11` remain Unknown', self.text)
        self.assertIn('Clock validation for OP0F hour/minute carriers is Unknown', self.text)

    def test_absent_arguments_and_explicit_mode(self):
        self.assertIsNone(self.data['universal_empty_poll'])
        self.assertIsNone(self.data['default_arguments'])
        self.assertEqual(self.data['examples']['mode'], [[None, None], [2, 'request-enter']])

    def test_independent_flags_and_reserved_carrier(self):
        # Single-axis controls: assistant alone, initialization alone, then both.
        cases = self.data['examples']['flags']
        self.assertEqual(cases, [['07', 0, 0, 0], ['07', 1, 1, 0],
            ['07', 2, 0, 1], ['07', 3, 1, 1], ['09', 3, 1, 1], ['0B', 3, 1, None]])
        for op, raw, assistant, factory in cases:
            self.assertEqual(raw & 1, assistant)
            if op in ('07', '09'):
                self.assertEqual((raw & 2) >> 1, factory)
            else:
                self.assertIsNone(factory)

    def test_three_memberships_remain_independent(self):
        cases = self.data['examples']['membership']
        self.assertEqual(cases, [[11, [False, True, False]],
                                [3, [True, False, False]], [2, [False, False, False]]])
        domains = [set(map(int, row[4].split('}', 1)[0].lstrip('{').split(',')))
                   for row in self.data['declarations'][9:12]]
        for code, expected in cases:
            self.assertEqual([code in domain for domain in domains], expected)

    def test_temperature_arithmetic_and_raw_hour(self):
        self.assertEqual(self.data['examples']['wish_temperature'], [[1, 0.5]])
        raw, value = self.data['examples']['wish_temperature'][0]
        self.assertEqual(raw / 2, value)
        self.assertEqual(self.data['examples']['hour'], [[255, None]])

    def test_status_alternatives_and_overlapping_extents(self):
        self.assertEqual(self.data['examples']['status_byte_one'],
            [['reserved', 128, 'reserved', 128], ['fan', 128, 'fan-running', 1]])
        self.assertEqual(128 & 0x80, 128)
        self.assertEqual((128 & 0x80) >> 7, 1)
        self.assertEqual(self.data['examples']['overlap'],
                         {'positions': [7, 7], 'maximum_extent': 9})

    def test_partial_labels_never_supply_selector_or_body(self):
        self.assertEqual(self.data['examples']['partial'], [
            ['10', 'request', 'B5', None, None], ['10', 'positive', 'F5', None, None],
            ['11', 'request', 'B5', None, None], ['11', 'positive', 'F5', None, None]])


if __name__ == '__main__':
    unittest.main()
