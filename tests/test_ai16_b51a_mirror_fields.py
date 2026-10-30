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
        EXPECTED_FIELDS.append([op, side, 'sequence', '3', '1', 'u8', '0', '0..255', 'Unknown', 'Hypothesis'])
EXPECTED_FIELDS += rows('''
00|positive|acknowledgement|4|1|u8|0|0..255|Unknown|Hypothesis
02|request|flags|4|1|u8|Unknown|0..255|Unknown|Hypothesis
02|request|length|5|1|u8|Unknown|0..255|Unknown|Hypothesis
02|request|mirror_address|6|2|LE u16|Unknown|0..65535|0..mirror-length-1|Hypothesis
02|positive|positive|4|1|u8|Unknown|0..255|Unknown|Hypothesis
02|positive|data|5|end|opaque|Unknown|not scalar|length 0..unset|Hypothesis
03|request|flags|4|1|u8|0|0..255|Unknown|Hypothesis
03|request|mirror_address|5|2|LE u16|0|0..65535|independent mirror limit Unknown|Hypothesis
03|request|symbol_address|7|2|LE u16|0|0..65535|independent symbol limit Unknown|Hypothesis
03|request|data|9|end|opaque|Unknown|not scalar|length 0..unset|Hypothesis
03|positive|flags|4|1|u8|0|0..255|Unknown|Hypothesis
06|request|level|4|1|u8|Unknown|0..255|Unknown|Hypothesis
06|request|point|5|1|u8|Unknown|0..255|0..99|Hypothesis
06|request|value|6|2|LE u16|Unknown|0..65535|Unknown|Hypothesis
06|positive|save_status|4|1|u8|0|0..255|5..255 unlabeled; no implicit success|Hypothesis
06|positive|mirror_address|5|2|LE u16|Unknown|0..65535|independent mirror limit Unknown|Hypothesis
06|positive|symbol_address|7|2|LE u16|Unknown|0..65535|independent symbol limit Unknown|Hypothesis
06|positive|value|9|conditional|LE u16|Unknown|0..65535|display type selects width|Hypothesis
''')
RULE_COLUMNS = ['Rule', 'Declaration', 'Grade']
EXPECTED_RULES = rows('''
correlation|00,01 only: equal sequence is candidate correlation; no retry or freshness policy|Hypothesis
reset-bit|0:denied:false|Hypothesis
reset-other|1..7:unnamed; defaults Unknown|Unknown
read-flags|0:triple-storage; default Unknown; bits 1..7 Unknown|Hypothesis
read-positive|0:false;1:true|Hypothesis
read-unresolved|2..255:unresolved|Unknown
read-alternative|bit 0:out-of-area; conflicts with whole-u8 interpretation|Hypothesis
read-length|requested and returned lengths independent|Hypothesis
write-request-bits|0:triple-storage:false;1:direct-update:false;2..7:reserved:false|Hypothesis
write-positive-bits|0:not-written:false;1:invalid-symbol:false;2:invalid-parameter:false;3:storage-error:false;4..7:reserved:false|Hypothesis
opaque-data|end-delimited; minimum 0; maximum unset; empty does not prove acceptance|Hypothesis
save-status|0:value-not-saved;1:point-not-found;2:write-protected;3:range-violation;4:misconfiguration|Hypothesis
save-widths|formal-u16:2;display-one-byte:1;display-two-byte:2|Hypothesis
address-limits|mirror and symbol logical limits independent; no other address dictionary|Hypothesis
physical-adaptation|Unknown|Unknown
storage-durability|Unknown|Unknown
success-semantics|Unknown|Unknown
''')
CASE_COLUMNS = ['Case', 'Op', 'Side', 'Logical bytes', 'Alternative', 'Result', 'Grade']
EXPECTED_CASES = []
for op in ('00', '01', '02', '03', '06'):
    for side in ('request', 'positive'):
        for value in (0, 255):
            EXPECTED_CASES.append([f'seq-{op}-{side}-{value}', op, side,
                                   f'B5 1A {op} {value:02X}', '-', f'sequence={value}', 'Proven'])
EXPECTED_CASES += rows('''
reset-high|00|positive|B5 1A 00 00 02|-|raw=2;denied=false;unnamed=2|Proven
read-request|02|request|B5 1A 02 07 01 03 34 12|-|requested=3;mirror=4660|Proven
read-short|02|positive|B5 1A 02 07 01 AA BB|-|positive=true;actual=2;data=AA BB|Proven
read-false|02|positive|B5 1A 02 07 00|-|positive=false;actual=0;data=|Proven
read-raw-two|02|positive|B5 1A 02 07 02|-|positive=unresolved;actual=0;data=|Proven
write-empty|03|request|B5 1A 03 07 00 34 12 78 56|-|mirror=4660;symbol=22136;actual=0;acceptance=Unknown|Proven
save-point-99|06|request|B5 1A 06 FF 09 63 34 12|-|sequence=255;level=9;point=99;fits=true;value=4660|Proven
save-point-100|06|request|B5 1A 06 00 09 64 34 12|-|sequence=0;level=9;point=100;fits=false;value=4660|Proven
save-zero|06|positive|B5 1A 06 07 00 34 12 78 56 34|display-one-byte|status=value-not-saved;mirror=4660;symbol=22136;value=52;width=1|Proven
save-one|06|positive|B5 1A 06 07 01 34 12 78 56 34 12|display-two-byte|status=point-not-found;mirror=4660;symbol=22136;value=4660;width=2|Proven
save-five|06|positive|B5 1A 06 07 05 34 12 78 56 34 12|formal-u16|status=unmapped;mirror=4660;symbol=22136;value=4660;width=2|Proven
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


def enumeration(data, name):
    return {int(k): v for k, v in (item.split(':') for item in declaration(data, name).split(';'))}


def scalar(data, op, side, name, raw, alternative='-'):
    field = lookup(data, 'vaillant', 181, 26, op, side, name)
    position = int(field[3])
    width = int(field[4]) if field[4] != 'conditional' else enumeration_width(data, alternative)
    part = raw[position:position + width]
    if len(part) != width:
        raise ValueError('short logical carrier')
    return int.from_bytes(part, 'little')


def enumeration_width(data, alternative):
    return {k: int(v) for k, v in (item.split(':') for item in declaration(data, 'save-widths').split(';'))}[alternative]


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
    if op == '02' and side == 'request':
        return f'requested={get("length")};mirror={get("mirror_address")}'
    if op == '02':
        value = enumeration(data, 'read-positive').get(get('positive'), 'unresolved')
        start = int(lookup(data, 'vaillant', 181, 26, op, side, 'data')[3])
        payload = raw[start:]
        return f'positive={value};actual={len(payload)};data={payload.hex(" ").upper()}'
    if op == '03':
        start = int(lookup(data, 'vaillant', 181, 26, op, side, 'data')[3])
        return f'mirror={get("mirror_address")};symbol={get("symbol_address")};actual={len(raw[start:])};acceptance=Unknown'
    if side == 'request':
        point = get('point')
        bounds = lookup(data, 'vaillant', 181, 26, op, side, 'point')[8]
        low, high = map(int, bounds.split('..'))
        fits = str(low <= point <= high).lower()
        return f'sequence={get("sequence")};level={get("level")};point={point};fits={fits};value={get("value")}'
    status = enumeration(data, 'save-status').get(get('save_status'), 'unmapped')
    return f'status={status};mirror={get("mirror_address")};symbol={get("symbol_address")};value={get("value")};width={enumeration_width(data, alternative)}'


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
        self.assertEqual(len(self.data['fields']), 28)
        self.assertEqual(len(self.data['cases']), 31)

    def test_synthetic_arithmetic(self):
        for case in self.data['cases']:
            with self.subTest(case=case[0]):
                raw = bytes.fromhex(case[3])
                self.assertEqual(list(raw[:3]), [181, 26, int(case[1], 16)])
                self.assertEqual(evaluate(self.data, case), case[5])
                # Oracle stays independent even if raw and claimed result change together.
                expected = next(row for row in EXPECTED_CASES if row[0] == case[0])
                self.assertEqual(evaluate(self.data, case), expected[5])

    def test_domains_ordering_and_widths(self):
        for field in self.data['fields']:
            op, side, name, pos, width, encoding, default, domain, limit, grade = field
            with self.subTest(op=op, side=side, field=name):
                if domain != 'not scalar':
                    low, high = map(int, domain.split('..'))
                    formal_width = 2 if encoding == 'LE u16' else 1
                    self.assertEqual((low, high), (0, 2 ** (8 * formal_width) - 1))
                    if default != 'Unknown':
                        self.assertTrue(low <= int(default) <= high)
                if width not in ('end', 'conditional'):
                    self.assertGreaterEqual(int(pos), 3)
                    self.assertEqual(int(width), 2 if encoding == 'LE u16' else 1)
        for op, side in (('02', 'request'), ('03', 'request'), ('06', 'request'), ('06', 'positive')):
            fields = [f for f in self.data['fields'] if f[:2] == [op, side]]
            positions = [int(f[3]) for f in fields]
            self.assertEqual(positions, sorted(set(positions)))
            for left, right in zip(fields, fields[1:]):
                self.assertEqual(int(left[3]) + int(left[4]), int(right[3]))
        self.assertEqual([enumeration_width(self.data, key) for key in ('formal-u16', 'display-one-byte', 'display-two-byte')], [2, 1, 2])
        # Formal address representability is not a logical mirror bound.
        address = lookup(self.data, 'vaillant', 181, 26, '02', 'request', 'mirror_address')
        self.assertEqual(address[7:9], ['0..65535', '0..mirror-length-1'])
        for mirror_length, value, fits in ((0, 0, False), (3, 2, True), (3, 3, False), (65536, 65535, True)):
            self.assertEqual(0 <= value < mirror_length, fits)

    def test_sequence_correlation_is_bounded(self):
        ops = declaration(self.data, 'correlation').split(' only:', 1)[0].split(',')
        self.assertEqual(ops, ['00', '01'])
        for op in ('00', '01', '02', '03', '06'):
            for request, positive in ((0, 0), (255, 255), (0, 255), (255, 0)):
                with self.subTest(op=op, request=request, positive=positive):
                    rq = scalar(self.data, op, 'request', 'sequence', bytes([181, 26, int(op, 16), request]))
                    rp = scalar(self.data, op, 'positive', 'sequence', bytes([181, 26, int(op, 16), positive]))
                    correlated = op in ops and rq == rp
                    self.assertEqual(correlated, op in ('00', '01') and request == positive)
        # Correlation alone has no fresh-success result in either declaration.
        self.assertEqual(declaration(self.data, 'success-semantics'), 'Unknown')

    def test_identity_axes_independently(self):
        base = ['vaillant', 181, 26, '02', 'request', 'length']
        control = lookup(self.data, *base)
        self.assertIsNotNone(control)
        for index, other in enumerate(('other-family', 180, 27, '03', 'positive', 'other-field')):
            changed = base.copy()
            changed[index] = other
            with self.subTest(axis=('family', 'primary', 'secondary', 'op', 'side', 'field')[index]):
                self.assertIsNone(lookup(self.data, *changed))
                self.assertEqual(lookup(self.data, *base), control)

    def test_negative_semantics_over_full_domains(self):
        positive = enumeration(self.data, 'read-positive')
        status = enumeration(self.data, 'save-status')
        for value in range(256):
            self.assertEqual(positive.get(value, 'unresolved'), {0: 'false', 1: 'true'}.get(value, 'unresolved'))
            self.assertEqual(status.get(value, 'unmapped'), {0: 'value-not-saved', 1: 'point-not-found', 2: 'write-protected', 3: 'range-violation', 4: 'misconfiguration'}.get(value, 'unmapped'))
        cases = {row[0]: row for row in self.data['cases']}
        requested = scalar(self.data, '02', 'request', 'length', bytes.fromhex(cases['read-request'][3]))
        start = int(lookup(self.data, 'vaillant', 181, 26, '02', 'positive', 'data')[3])
        actual = len(bytes.fromhex(cases['read-short'][3])[start:])
        self.assertEqual((requested, actual), (3, 2))
        self.assertNotEqual(requested, actual)
        for name in ('save-zero', 'save-one', 'save-five'):
            raw = bytes.fromhex(cases[name][3])
            self.assertEqual(raw[9], 0x34)
        self.assertNotEqual(evaluate(self.data, cases['save-zero']).split(';value=')[1], evaluate(self.data, cases['save-one']).split(';value=')[1])


if __name__ == '__main__':
    unittest.main()
