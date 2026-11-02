"""Offline acceptance of finite native declarations; no decoder or live coverage."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ae14_b510_candidates.json'
PAGE = ROOT / 'protocols/vaillant/ebus-vaillant-B510.md'

# Independent expected native tuples: OP, field, domain, divisor, unit, values.
EXPECTED = [
    (2, 'remote_status', [0, 255], None, None, None),
    (2, 'CH_setpoint_upper_limit', [0, 255], 2, 'degrees Celsius', None),
    (2, 'DHW_setpoint_upper_limit', [0, 255], 2, 'degrees Celsius', None),
    (3, 'climate', [0, 255], None, None,
     {'0': 'off', '1': 'heating', '2': 'cooling'}),
    (3, 'capacity', [0, 250], 10, 'kW', None),
    (3, 'cost', [0, 250], None, 'reciprocal-MWh', None),
    (3, 'force', [0, 255], None, None,
     {'0': 'normal', '1': 'maximum', '2': 'minimum', '3': 'off',
      '4': 'cooling-leak-test', '5': 'cooling-charge-test',
      '6': 'capacity-test', '7': 'I/O-test'}),
    (4, 'energy', [0, 255], None, None,
     {'0': 'unknown', '1': 'gas', '2': 'electricity-one',
      '3': 'electricity-two', '4': 'fuel', '5': 'pellet'}),
    (5, 'DHW_setpoint', [0, 255], 2, 'degrees Celsius', None),
    (5, 'adjustment', [0, 255], None, None, None),
    (6, 'status', [0, 255], None, None, None),
    (0, 'disable', [0, 255], None, None, None),
]

# Exact structured cells check grade, identity, extent and adjacent uncertainty,
# independently of the fixture's representation.
PAGE_CLAIMS = [
    ('02', 'remote_status', 'u8 0..255', 'Unknown', 'raw status only',
     'sentinel/default Unknown; semantics Unknown'),
    ('02', 'CH_setpoint_upper_limit', 'u8 0..255', 'raw/2 degrees Celsius', 'none declared',
     'sentinel/default Unknown; physical acceptance Unknown'),
    ('02', 'DHW_setpoint_upper_limit', 'u8 0..255', 'raw/2 degrees Celsius', 'none declared',
     'sentinel/default Unknown; physical acceptance Unknown'),
    ('03', 'climate', 'u8 0..255', 'none declared', '0 off; 1 heating; 2 cooling',
     'sentinel/default Unknown; other values unmapped'),
    ('03', 'capacity', 'u8 0..250', 'raw/10 kW', 'none declared',
     'sentinel/default Unknown; 251..255 outside candidate domain'),
    ('03', 'cost', 'u8 0..250', 'reciprocal-MWh; divisor Unknown', 'none declared',
     'sentinel/default Unknown; monetary versus emissions Unknown'),
    ('03', 'force', 'u8 0..255', 'none declared',
     '0 normal; 1 maximum; 2 minimum; 3 off; 4 cooling-leak-test; 5 cooling-charge-test; 6 capacity-test; 7 I/O-test',
     'sentinel/default Unknown; 8..255 unmapped'),
    ('04', 'energy', 'u8 0..255', 'none declared',
     '0 unknown; 1 gas; 2 electricity-one; 3 electricity-two; 4 fuel; 5 pellet',
     'sentinel/default Unknown; monetary versus emissions Unknown; 6..255 unmapped'),
    ('05', 'DHW_setpoint', 'u8 0..255', 'raw/2 degrees Celsius', 'none declared',
     'sentinel/default Unknown; physical acceptance Unknown'),
    ('05', 'adjustment', 'u8 0..255', 'none declared',
     'bit 0 CH; bit 1 DHW; 0 released / 1 blocked; bits 2..7 reserved, retained',
     'sentinel/default Unknown; reserved expected values Unknown'),
    ('06', 'status', 'u8 0..255', 'none declared',
     'bit 0: 0 off / 1 on; bits 1..7 reserved zero, retained',
     'sentinel/default Unknown; nonzero reserved bits do not acquire meaning'),
    ('00', 'disable', 'u8 0..255', 'none declared',
     'bits 0..2 active only in automatic; ignored in forced-heating, forced-DHW, forced-off; bit 6 relates to subsequent flame status; bit 7 starts legionella protection, persists until corresponding status, does not command termination',
     'sentinel/default Unknown; bits 3/4 timer assignment unresolved (Unknown); bit 5 meaning Unknown; numeric mode codes Unknown; bit 7 mode applicability Unknown'),
]


class B510Candidates(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.entries = {(e['key']['operation'], e['key']['field']): e
                        for e in self.data['entries']}

    def test_finite_native_declarations(self):
        self.assertEqual(self.data['evidence'], 'synthetic; no observed telegrams')
        self.assertEqual(self.data['physical_qualification'], 'Unknown')
        self.assertEqual(len(self.data['entries']), 12)
        self.assertEqual(len(self.entries), 12)
        self.assertEqual(set(self.entries), {(e[0], e[1]) for e in EXPECTED})
        for op, field, domain, divisor, unit, values in EXPECTED:
            with self.subTest(op=op, field=field):
                e = self.entries[op, field]
                self.assertEqual(e['key'], dict(family='vaillant', variant='B510',
                    primary=181, secondary=16, operation=op, direction='request', field=field))
                self.assertIsNone(e['position'])
                self.assertEqual(e['width_bits'], 8)
                self.assertEqual(e['grade'], 'Hypothesis')
                self.assertEqual(e['interpretation'], 'Unknown')
                self.assertEqual((e['raw_domain'], e['divisor'], e['unit'], e['values']),
                                 (domain, divisor, unit, values))
                if field not in ('adjustment', 'status', 'disable'):
                    self.assertIsNone(e['bits'])

    def test_structured_page_claims(self):
        text = PAGE.read_text()
        section = text.split('### Bounded operational enums and disable-bit candidates\n', 1)[1].split('\n## ', 1)[0]
        rows = [[c.strip() for c in line.strip('|').split('|')]
                for line in section.splitlines() if line.startswith('| Hypothesis')]
        expected = []
        for op, field, raw, scale, values, unresolved in PAGE_CLAIMS:
            position = 'Unknown; 8 bits'
            if field == 'disable':
                position += ' (logical argument 5 in eight-argument variant)'
            expected.append(['Hypothesis', op, field, 'request', position,
                             raw, scale, values, unresolved])
        self.assertEqual(rows, expected)
        self.assertIn('fixtures/ae14_b510_candidates.json', section)
        self.assertIn('A logical position is\nnot a wire offset.', section)
        self.assertNotIn('4 clear the burner DHW blocking time', text)
        self.assertNotIn('6 clear the burner CH blocking time', text)
        self.assertNotIn('`0` auto, `1` forced off', text)

    def test_numeric_and_enum_examples(self):
        examples = self.data['examples']
        self.assertEqual(examples['capacity'], [[0, True, 0], [250, True, 25], [251, False, None]])
        capacity = self.entries[3, 'capacity']
        for raw, inside, value in examples['capacity']:
            self.assertEqual(capacity['raw_domain'][0] <= raw <= capacity['raw_domain'][1], inside)
            if inside:
                self.assertEqual(raw / capacity['divisor'], value)
        self.assertEqual(examples['temperature'], [
            [2, 'CH_setpoint_upper_limit', 1, 0.5],
            [2, 'DHW_setpoint_upper_limit', 1, 0.5], [5, 'DHW_setpoint', 1, 0.5]])
        for op, field, raw, value in examples['temperature']:
            self.assertEqual(raw / self.entries[op, field]['divisor'], value)
        self.assertEqual(examples['force'], [[7, 'I/O-test'], [8, None]])
        self.assertEqual(examples['energy'], [[2, 'electricity-one'], [3, 'electricity-two']])
        for name, op in [('force', 3), ('energy', 4)]:
            for raw, label in examples[name]:
                self.assertEqual(self.entries[op, name]['values'].get(str(raw)), label)

    def test_bit_declarations(self):
        for op, field in [(5, 'adjustment'), (6, 'status'), (0, 'disable')]:
            bits = self.entries[op, field]['bits']
            self.assertEqual([b['bit'] for b in bits], list(range(8)))
            for i, b in enumerate(bits):
                # Every nullable property is checked: absent metadata is meaningful.
                want = dict(bit=i, grade='Hypothesis', values=None, reserved=False,
                            expected=None, active_modes=None, ignored_modes=None,
                            meaning=None, persists_until_status=None, commands_termination=None)
                if field == 'adjustment':
                    if i < 2:
                        want.update(values={'0': 'released', '1': 'blocked'}, meaning=['CH', 'DHW'][i])
                    else:
                        want['reserved'] = True
                elif field == 'status':
                    if i == 0:
                        want['values'] = {'0': 'off', '1': 'on'}
                    else:
                        want.update(reserved=True, expected=0)
                elif i < 3:
                    want.update(active_modes=['automatic'], ignored_modes=[
                        'forced-heating', 'forced-DHW', 'forced-off'])
                elif i in (3, 4):
                    want.update(grade='Unknown', meaning='timer assignment unresolved')
                elif i == 5:
                    want['grade'] = 'Unknown'
                elif i == 6:
                    want['meaning'] = 'relates to subsequent flame status'
                else:
                    want.update(meaning='starts legionella protection',
                                persists_until_status=True, commands_termination=False)
                with self.subTest(field=field, bit=i):
                    self.assertEqual(b, want)

    def test_adjustment_examples(self):
        cases = self.data['examples']['adjustment']
        self.assertEqual(cases, [[0, 'released', 'released', 0],
                                [3, 'blocked', 'blocked', 0], [252, 'released', 'released', 252]])
        bits = self.entries[5, 'adjustment']['bits']
        for raw, ch, dhw, reserved in cases:
            self.assertEqual(bits[0]['values'][str(raw & 1)], ch)
            self.assertEqual(bits[1]['values'][str((raw >> 1) & 1)], dhw)
            self.assertEqual(sum(raw & (1 << b['bit']) for b in bits if b['reserved']), reserved)

    def test_disable_mode_and_independent_bits(self):
        cases = self.data['examples']['disable']
        self.assertEqual(cases, [[7, 'automatic', 7, 0, 0],
            [7, 'forced-heating', 0, 0, 0], [7, 'forced-DHW', 0, 0, 0],
            [7, 'forced-off', 0, 0, 0], [128, 'automatic', 0, 0, 128],
            [135, 'automatic', 7, 0, 128], [24, 'automatic', 0, 24, 0]])
        bits = self.entries[0, 'disable']['bits']
        for raw, mode, active, unresolved, legionella in cases:
            self.assertEqual(sum(raw & (1 << b['bit']) for b in bits[:3]
                                 if mode in b['active_modes']), active)
            self.assertEqual(raw & 0x18, unresolved)
            self.assertEqual(raw & 0x80, legionella)


if __name__ == '__main__':
    unittest.main()
