"""Independent native declaration and synthetic arithmetic checks; no bus access."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-b51a-mirror-fields.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ai16_b51a_mirror_fields.json'


def rows(text):
    return [line.split('|') for line in text.strip().splitlines()]


FIELD_COLUMNS = rows('Op|Side|Field|Position|Width|Encoding|Default|Formal domain|Logical limit|Grade')[0]
# Expected constants are maintained here independently of the page and JSON.
EXPECTED_FIELDS = []
for op in ('00', '01', '02', '03', '06'):
    for side in ('request', 'positive'):
        EXPECTED_FIELDS.append([op, side, 'sequence', '3', '1', 'u8', 'Unknown', '0..255', 'Unknown', 'Hypothesis'])
EXPECTED_FIELDS += rows('00|positive|acknowledgement|4|1|u8|Unknown|0..255|Unknown|Hypothesis')
for op in ('02', '03', '06'):
    for side in ('request', 'positive'):
        EXPECTED_FIELDS.append([op, side, 'supplemental_layout'] + ['Unknown'] * 7)
RULE_COLUMNS = ['Rule', 'Declaration', 'Grade']
EXPECTED_RULES = rows('''reset-bit|0:denied; default Unknown|Hypothesis
reset-other|1..7:unnamed; defaults Unknown|Unknown
correlation|Unknown|Unknown
read-layout|Unknown|Unknown
write-layout|Unknown|Unknown
save-layout|Unknown|Unknown
physical-adaptation|Unknown|Unknown
storage-durability|Unknown|Unknown
success-semantics|Unknown|Unknown''')
CASE_COLUMNS = ['Case', 'Op', 'Side', 'Logical bytes', 'Alternative', 'Result', 'Grade']
EXPECTED_CASES = []
for op in ('00', '01', '02', '03', '06'):
    for side in ('request', 'positive'):
        for value in (0, 255):
            EXPECTED_CASES.append([f'seq-{op}-{side}-{value}', op, side,
                                   f'B5 1A {op} {value:02X}', '-', f'sequence={value}', 'Proven'])
EXPECTED_CASES += rows('''
reset-high|00|positive|B5 1A 00 00 02|-|raw=2;denied=false;unnamed=2|Proven
opaque-02-request|02|request|B5 1A 02 07 01 03 34 12|-|Unknown|Unknown
opaque-02-positive|02|positive|B5 1A 02 07 02 AA BB|-|Unknown|Unknown
opaque-03-request|03|request|B5 1A 03 07 00 34 12 78 56|-|Unknown|Unknown
opaque-03-positive|03|positive|B5 1A 03 07 00|-|Unknown|Unknown
opaque-06-request|06|request|B5 1A 06 FF 09 63 34 12|-|Unknown|Unknown
opaque-06-positive|06|positive|B5 1A 06 07 00 34 12 78 56 34|-|Unknown|Unknown
''')


def page_table(text, heading):
    block = text.split('## ' + heading + '\n', 1)[1].split('\n## ', 1)[0]
    lines = [line.strip() for line in block.splitlines() if line.startswith('|')]
    return [[cell.strip() for cell in line.strip('|').split('|')] for line in lines if not line.startswith('|---')]


def lookup(data, family, pb, sb, op, side, field):
    if [family, pb, sb] != [data['family'], data['primary'], data['secondary']]:
        return None
    return next((row for row in data['fields'] if row[:3] == [op, side, field]), None)


def declaration(data, name):
    return next(row[1] for row in data['rules'] if row[0] == name)


def scalar(data, op, side, name, raw, alternative='-'):
    field = lookup(data, 'vaillant', 181, 26, op, side, name)
    if field is None or field[-1] == 'Unknown':
        raise ValueError('Unknown field layout')
    position = int(field[3])
    width = int(field[4])
    part = raw[position:position + width]
    if len(part) != width:
        raise ValueError('short logical carrier')
    return int.from_bytes(part, 'little')


def evaluate(data, case):
    name, op, side, hex_bytes, alternative, _, _ = case
    raw = bytes.fromhex(hex_bytes)
    get = lambda field: scalar(data, op, side, field, raw, alternative)
    if name.startswith('seq-'):
        return f'sequence={get("sequence")}'
    if name == 'reset-high':
        value = get('acknowledgement')
        bit = int(declaration(data, 'reset-bit').split(':')[0])
        return f'raw={value};denied={str(bool(value & (1 << bit))).lower()};unnamed={value & ~(1 << bit)}'
    return 'Unknown'


class MirrorFieldsTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def test_exact_tables_and_fixture(self):
        self.assertEqual(set(self.data), {'family', 'primary', 'secondary', 'synthetic', 'fields', 'rules', 'cases'})
        self.assertEqual([self.data[k] for k in ('family', 'primary', 'secondary', 'synthetic')], ['vaillant', 181, 26, True])
        for heading, columns, expected, key in (
            ('Candidate fields', FIELD_COLUMNS, EXPECTED_FIELDS, 'fields'),
            ('Interpretations and unknowns', RULE_COLUMNS, EXPECTED_RULES, 'rules'),
            ('Synthetic logical tuples', CASE_COLUMNS, EXPECTED_CASES, 'cases'),
        ):
            with self.subTest(table=heading):
                self.assertEqual(page_table(self.page, heading), [columns] + expected)
                self.assertEqual(self.data[key], expected)
        self.assertEqual(len(self.data['fields']), 17)
        self.assertEqual(len(self.data['cases']), 27)

    def test_synthetic_arithmetic(self):
        for case in self.data['cases']:
            with self.subTest(case=case[0]):
                raw = bytes.fromhex(case[3])
                self.assertEqual(list(raw[:3]), [181, 26, int(case[1], 16)])
                self.assertEqual(evaluate(self.data, case), case[5])
                # Oracle stays independent even if raw and claimed result change together.
                expected = next(row for row in EXPECTED_CASES if row[0] == case[0])
                self.assertEqual(evaluate(self.data, case), expected[5])

    def test_known_domains_and_unknown_layouts(self):
        for field in self.data['fields']:
            with self.subTest(field=field[:3]):
                if field[2] == 'supplemental_layout':
                    self.assertEqual(field[3:], ['Unknown'] * 7)
                    with self.assertRaisesRegex(ValueError, 'Unknown field layout'):
                        scalar(self.data, *field[:3], bytes(range(16)))
                else:
                    self.assertEqual(field[4:10], ['1', 'u8', 'Unknown', '0..255', 'Unknown', 'Hypothesis'])
        for rule in ('correlation', 'read-layout', 'write-layout', 'save-layout', 'success-semantics'):
            self.assertEqual(declaration(self.data, rule), 'Unknown')

    def test_identity_axes_independently(self):
        base = ['vaillant', 181, 26, '00', 'positive', 'acknowledgement']
        control = lookup(self.data, *base)
        self.assertIsNotNone(control)
        for index, other in enumerate(('other-family', 180, 27, '03', 'request', 'other-field')):
            changed = base.copy()
            changed[index] = other
            with self.subTest(axis=('family', 'primary', 'secondary', 'op', 'side', 'field')[index]):
                self.assertIsNone(lookup(self.data, *changed))
                self.assertEqual(lookup(self.data, *base), control)

    def test_opaque_bytes_never_supply_a_mapping(self):
        for case in self.data['cases']:
            if not case[0].startswith('opaque-'):
                continue
            for value in range(256):
                changed = case.copy()
                changed[3] = case[3][:11] + f' {value:02X}'
                with self.subTest(case=case[0], value=value):
                    self.assertEqual(evaluate(self.data, changed), 'Unknown')
                    self.assertEqual(case[4:], ['-', 'Unknown', 'Unknown'])
            for name in ('flags', 'length', 'mirror_address', 'symbol_address',
                         'save_status', 'point', 'level', 'value', 'data', 'positive'):
                self.assertIsNone(lookup(self.data, 'vaillant', 181, 26, case[1], case[2], name))

    def test_reset_bit_over_full_domain(self):
        for value in range(256):
            case = ['reset-high', '00', 'positive', f'B5 1A 00 00 {value:02X}', '-', '', 'Proven']
            self.assertEqual(evaluate(self.data, case),
                             f'raw={value};denied={str(bool(value & 1)).lower()};unnamed={value & 254}')


if __name__ == '__main__':
    unittest.main()
