"""Independent finite declarations and arithmetic; no physical reply decoder."""
import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ak10_b512_heatpump_io.json'
PAGE = ROOT / 'protocols/vaillant/ebus-b512-heatpump-io.md'
API = ROOT / 'architecture/ak10_b512_heatpump_io_api.md'

# Literal coordinates and carriers: independent of the page and fixture.
COORDINATES = '''0F request outputs 3 8 bits
0F request valve 4 8 u8
0F positive temperature_one 3 16 signed-le16
0F positive temperature_two 6 16 signed-le16
0F positive input 5 8 u8
0F positive pressure 8 8 u8
0F positive backup 9 8 u8
10 request actuators_one 3 8 bits
10 request actuators_two 4 8 bits
10 request inverse_actuator 5 16 opaque-16
10 positive status 3 8 bits
10 positive single_phase 4 8 u8
10 positive three_phase 5 8 u8
10 positive adc_1 6 16 raw-le16
10 positive adc_2 8 16 raw-le16
10 positive adc_3 10 16 raw-le16
10 positive adc_4 12 16 raw-le16
10 positive adc_5 14 16 raw-le16
10 positive adc_6 16 16 raw-le16
10 positive board 18 8 u8
11 request temperature_1 3 16 signed-le16
11 request temperature_2 5 16 signed-le16
11 request temperature_3 7 16 signed-le16
11 request pressure 9 8 u8
11 request flow 10 8 signed8
11 request pump_status 11 8 raw-u8
11 request compressor 12 8 bits
11 positive status 3 8 bits
11 positive setpoint 4 8 u8
12 request emergency 3 8 bits
12 request switch 4 8 raw-u8
12 request co2_1 5 16 raw-le16
12 request co2_2 7 16 raw-le16
12 positive led 3 8 bits'''

BITS = {
    (15, 'request', 'outputs'): ['output one', 'output two'] + ['reserved'] * 6,
    (16, 'request', 'actuators_one'): ['cooling valve', 'passive mixer one',
        'passive mixer two', 'cooling active', 'well pump', 'backup safety',
        'backup one', 'backup two'],
    (16, 'request', 'actuators_two'): ['backup three', 'external valve',
        'external backup'] + ['reserved'] * 5,
    (16, 'positive', 'status'): ['anode channel one', 'anode channel two',
        'smart-grid', 'well', 'safety limiter', 'safety', 'reserved', 'reserved'],
    (17, 'request', 'compressor'): ['compressor-off'] + ['reserved'] * 6 + ['unmodeled'],
    (17, 'positive', 'status'): ['compressor-off', 'pump-relay'] + ['reserved'] * 6,
    (18, 'request', 'emergency'): ['emergency'] + ['reserved'] * 6 + ['unmodeled'],
    (18, 'positive', 'led'): ['LED'] + ['reserved'] * 6 + ['unmodeled'],
}

RELATIONSHIPS = '''0F | request | valve | 0 off; 1 CH; 2 DHW
0F | positive | temperature_one, temperature_two | Select raw word 8000 replacement before signed LE16 /16 degrees Celsius; FFF0 = -1 degree Celsius
0F | positive | input | 0 multipurpose; 1 utility contact
0F | positive | pressure | u8/10 bar; byte FF = raw 255 = 25.5 bar; domain 0..25.5; declared default 255.0 conflicts with domain and is retained without clipping
0F | positive | backup | 0 off; 1..3 steps; FF replacement
10 | request | inverse_actuator | Opaque 16-bit data; algorithm Unknown; no complement algorithm follows even from coincidental complement values
10 | positive | single_phase | Percent; approximately 50 powered; 0 absent; tolerance Unknown
10 | positive | three_phase | Percent; 100 powered; 0 all phases absent; 33 one phase absent; 66 two phases absent
10 | positive | adc_1, adc_2, adc_3, adc_4, adc_5, adc_6 | Six independent raw LE u16 channels; units and calibration Unknown
10 | positive | board | Opaque codes 0/1/2/3/11/12; 13 and other unmapped values stay raw
11 | request | temperature_1, temperature_2, temperature_3 | Signed LE16 /16 degrees Celsius; no replacement declared
11 | request | pressure | u8/10 bar; no default declared
11 | request | flow | Signed8 times10 l/h; FF = -10 l/h
11 | request | pump_status | Raw u8; meanings Unknown
11 | positive | setpoint | u8; 0..100 percent
12 | request | switch | Raw u8; meanings Unknown
12 | request | co2_1, co2_2 | LE u16 ppm; full 0..65535; FFFF = 65535 ppm, not a sentinel'''

AXES = '''Ab19Family | string | family | vaillant to other-family
Ab19Variant | string | variant | B512-heatpump-io to other-variant
Ab19Primary | uint8 | primary | 181 to 180
Ab19Secondary | *uint8 | secondary | 18 to 0; absent differs from explicit zero
Ab19Operation | *uint8 | operation | 15 to 0; absent differs from explicit zero
Ab19Direction | string | direction | request to other-direction
Ab19Field | string | field | ab19_outputs to ab19_other
Ab19Alternative | string | alternative | none to other-alternative
Ab19Group | *uint8 | group | absent to explicit zero
Ab19InstanceScope | string | instance_scope | none to dynamic
Ab19Register | *uint16 | register | absent to explicit zero'''


def expected_entries():
    rows = []
    for line in COORDINATES.splitlines():
        op, direction, name, pos, width, encoding = line.split()
        op = int(op, 16)
        f = dict(name=name, position=int(pos), width_bits=int(width), encoding=encoding)
        key = (op, direction, name)
        if key in BITS:
            f['bits'] = [dict(bit=i, label=label,
                status=label if label in ('reserved', 'unmodeled') else 'candidate')
                for i, label in enumerate(BITS[key])]
        if encoding == 'signed-le16':
            f.update(scale=0.0625, unit='degrees Celsius')
        if key in [(15, 'positive', 'temperature_one'), (15, 'positive', 'temperature_two'),
                   (15, 'positive', 'backup')]:
            f['replacement'] = dict(raw_word=255 if name == 'backup' else 32768,
                selection='before_scaling', meaning='replacement', unavailable_assertion=False)
        if name == 'pressure':
            f.update(scale=0.1, unit='bar')
            if op == 15:
                f.update(domain=[0, 25.5], default=255.0, default_conflict=True,
                         raw_domain=[0, 255])
        if name == 'valve':
            f['values'] = {'0': 'off', '1': 'CH', '2': 'DHW'}
        if name == 'input':
            f['values'] = {'0': 'multipurpose', '1': 'utility contact'}
        if name == 'backup':
            f['values'] = {'0': 'off', '1': 'step one', '2': 'step two', '3': 'step three'}
        if name == 'inverse_actuator':
            f['algorithm'] = 'Unknown'
        if name in ('single_phase', 'three_phase', 'setpoint'):
            f['unit'] = 'percent'
        if name == 'single_phase':
            f.update(relations=[dict(raw=50, comparison='approximately', meaning='powered'),
                dict(raw=0, comparison='exact', meaning='absent')], tolerance='Unknown')
        if name == 'three_phase':
            f['values'] = {'100': 'powered', '0': 'all phases absent',
                           '33': 'one phase absent', '66': 'two phases absent'}
        if name == 'board':
            f.update(values={str(i): 'opaque' for i in (0, 1, 2, 3, 11, 12)}, unmapped='retain_raw')
        if name == 'flow':
            f.update(scale=10, unit='l/h')
        if name == 'setpoint':
            f['domain'] = [0, 100]
        if name in ('co2_1', 'co2_2'):
            f.update(domain=[0, 65535], unit='ppm')
        rows.append(dict(operation=op, direction=direction, grade='Hypothesis', field=f))
    return rows


def expected_cases():
    """Sample values are literal independent expectations, not fixture-derived."""
    result = []
    def add(op, d, field, raw, value=None, replacement=False, **extra):
        result.append(dict(operation=op, direction=d, field=field, raw=raw,
                           value=value, replacement=replacement, **extra))
    for f in ('temperature_one', 'temperature_two'):
        add(15, 'positive', f, '00 80', replacement=True)
        add(15, 'positive', f, 'F0 FF', -1)
    add(15, 'positive', 'pressure', 'FF', 25.5, raw_integer=255)
    add(15, 'positive', 'backup', 'FF', replacement=True)
    for op, d, f in BITS:
        for bit, raw in enumerate(('01', '02', '04', '08', '10', '20', '40', '80')):
            add(op, d, f, raw, 2**bit, active_bits=[bit])
    for f in ('adc_1', 'adc_2', 'adc_3', 'adc_4', 'adc_5', 'adc_6'):
        for raw, value in [('00 00', 0), ('01 00', 1), ('00 01', 256), ('FF FF', 65535)]:
            add(16, 'positive', f, raw, value)
    for f in ('single_phase', 'three_phase'):
        for raw, value in [('00', 0), ('21', 33), ('32', 50), ('42', 66), ('64', 100)]:
            add(16, 'positive', f, raw, value)
    add(16, 'positive', 'board', '0C', 12, mapped=True)
    add(16, 'positive', 'board', '0D', 13, mapped=False)
    for raw in ('FF FF', '00 00', 'AA 55'):
        add(16, 'request', 'inverse_actuator', raw)
    for f in ('temperature_1', 'temperature_2', 'temperature_3'):
        add(17, 'request', f, 'F0 FF', -1)
    add(17, 'request', 'pressure', 'FF', 25.5)
    add(17, 'request', 'flow', 'FF', -10)
    for f in ('co2_1', 'co2_2'):
        add(18, 'request', f, 'FF FF', 65535)
    return result


def evaluate(field, raw):
    """Exercise field declarations only; preserve raw without physical admission."""
    result = dict(raw=raw, value=None, replacement=False, physical_reply_selection=False)
    if len(raw) * 8 != field['width_bits'] or field['encoding'] == 'opaque-16':
        return result
    word = int.from_bytes(raw, 'little')
    replacement = field.get('replacement')
    if (replacement and replacement['selection'] == 'before_scaling'
            and word == replacement['raw_word']):
        result['replacement'] = True
        return result
    value = int.from_bytes(raw, 'little', signed=field['encoding'] in ('signed-le16', 'signed8'))
    result['value'] = value * field.get('scale', 1)
    if 'bits' in field:
        result['active_bits'] = [b['bit'] for b in field['bits'] if word & (1 << b['bit'])]
    if 'values' in field:
        result['mapped'] = str(word) in field['values']
    result['raw_integer'] = word
    return result


def tables(text):
    blocks = []
    for block in text.split('\n\n'):
        if block.startswith('|'):
            blocks.append([[c.strip() for c in line.strip('|').split('|')]
                for line in block.splitlines() if not line.startswith('| ---')])
    return blocks


def split_rows(text):
    return [line.split(' | ') for line in text.splitlines()]


def assert_axis_contract(test, text):
    header = ['Field', 'Go type', 'Exact matching boundary', 'Single-axis control']
    test.assertEqual(tables(text), [[header] + split_rows(AXES)])


class HeatPumpIO(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()
        self.api = API.read_text()

    def field(self, op, d, name):
        return next(e['field'] for e in self.data['entries']
                    if (e['operation'], e['direction'], e['field']['name']) == (op, d, name))

    def test_exact_finite_native_declarations(self):
        self.assertEqual(self.data['entries'], expected_entries())
        self.assertEqual(len(self.data['entries']), 34)
        self.assertEqual(self.data['family'], 'Vaillant heat-pump I/O')
        self.assertEqual(self.data['service'], {'primary': 181, 'secondary': 18})
        self.assertEqual(self.data['coordinate_system'],
                         'abstract logical positions; not physical wire offsets')
        self.assertEqual(self.data['representation_grade'], 'Proven')
        self.assertEqual(self.data['candidate_grade'], 'Hypothesis')
        self.assertEqual(self.data['unknown'], {k: 'Unknown' for k in (
            'native_support', 'physical_effects', 'persistence', 'delivery',
            'physical_reply_form', 'qualification', 'physical_lengths', 'negative_replies')})
        self.assertEqual(self.data['raw_policy'],
            'retain original bytes, including short, extra, reserved and unmodeled data')
        self.assertEqual(set(self.data), {'family', 'service', 'coordinate_system',
            'representation_grade', 'candidate_grade', 'unknown', 'raw_policy',
            'entries', 'positive_conflicts', 'cases'})

    def test_synthetic_expected_results(self):
        self.assertEqual(self.data['cases'], expected_cases())
        self.assertEqual(len(self.data['cases']), 116)
        for case in expected_cases():
            with self.subTest(case=case):
                f = self.field(case['operation'], case['direction'], case['field'])
                got = evaluate(f, bytes.fromhex(case['raw']))
                self.assertEqual(got['raw'], bytes.fromhex(case['raw']))
                self.assertFalse(got['physical_reply_selection'])
                for key in ('value', 'replacement', 'active_bits', 'mapped', 'raw_integer'):
                    if key in case:
                        self.assertEqual(got[key], case[key])

    def test_temperature_replacement_each_field(self):
        for name in ('temperature_one', 'temperature_two'):
            f = self.field(15, 'positive', name)
            self.assertEqual(evaluate(f, b'\x00\x80')['value'], None)
            self.assertTrue(evaluate(f, b'\x00\x80')['replacement'])
            self.assertEqual(evaluate(f, b'\xf0\xff')['value'], -1)
            self.assertFalse(evaluate(f, b'\xf0\xff')['replacement'])
            self.assertFalse(f['replacement']['unavailable_assertion'])

    def test_pressure_conflict_not_clipped(self):
        f = self.field(15, 'positive', 'pressure')
        self.assertEqual(f['default'], 255.0)
        self.assertEqual(f['domain'], [0, 25.5])
        self.assertTrue(f['default_conflict'])
        self.assertEqual(evaluate(f, b'\xff')['raw_integer'], 255)
        self.assertEqual(evaluate(f, b'\xff')['value'], 25.5)
        for e in self.data['entries']:
            if (e['operation'], e['direction'], e['field']['name']) != (15, 'positive', 'pressure'):
                self.assertNotIn('default', e['field'])

    def test_bits_toggle_independently_with_valid_controls(self):
        for key, labels in BITS.items():
            f = self.field(*key)
            self.assertEqual(evaluate(f, b'\x00')['active_bits'], [])
            self.assertEqual(evaluate(f, b'\xff')['active_bits'], list(range(8)))
            for bit, label in enumerate(labels):
                with self.subTest(key=key, bit=bit):
                    self.assertEqual(f['bits'][bit]['label'], label)
                    raw = bytes([1 << bit])
                    self.assertEqual(evaluate(f, raw)['active_bits'], [bit])
                    self.assertEqual(evaluate(f, raw)['raw'], raw)
        for key in [(17, 'request', 'compressor'), (18, 'request', 'emergency'),
                    (18, 'positive', 'led')]:
            self.assertEqual(self.field(*key)['bits'][7]['status'], 'unmodeled')

    def test_each_adc_and_phase_field_varies_alone(self):
        # Logical field samples, not an invented physical reply layout.
        for names in [('adc_1', 'adc_2', 'adc_3', 'adc_4', 'adc_5', 'adc_6'),
                      ('single_phase', 'three_phase')]:
            fields = [self.field(16, 'positive', name) for name in names]
            baseline = [b'\x00' * (f['width_bits'] // 8) for f in fields]
            self.assertEqual([evaluate(f, b)['value'] for f, b in zip(fields, baseline)],
                             [0] * len(names))
            for i, f in enumerate(fields):
                samples = baseline.copy()
                samples[i] = b'\x00\x01' if f['width_bits'] == 16 else b'\x64'
                values = [evaluate(field, b)['value'] for field, b in zip(fields, samples)]
                expected = [0] * len(names)
                expected[i] = 256 if f['width_bits'] == 16 else 100
                self.assertEqual(values, expected)
        self.assertEqual(self.field(16, 'positive', 'single_phase')['tolerance'], 'Unknown')

    def test_opaque_inverse_even_when_complement(self):
        f = self.field(16, 'request', 'inverse_actuator')
        self.assertEqual(f['algorithm'], 'Unknown')
        for actuator in (b'\x00\x00', b'\x55\xaa', b'\xff\xff'):
            raw = bytes(v ^ 255 for v in actuator)
            self.assertIsNone(evaluate(f, raw)['value'])
            self.assertEqual(evaluate(f, raw)['raw'], raw)

    def test_signed_flow_and_full_co2(self):
        self.assertEqual(evaluate(self.field(17, 'request', 'flow'), b'\xff')['value'], -10)
        for name in ('co2_1', 'co2_2'):
            f = self.field(18, 'request', name)
            self.assertEqual(f['domain'], [0, 65535])
            self.assertNotIn('replacement', f)
            self.assertEqual(evaluate(f, b'\xff\xff')['value'], 65535)

    def test_literal_positive_conflict_per_requested_selector(self):
        self.assertEqual(self.data['positive_conflicts'], [
            {'requested_operation': 17, 'declared_positive': [181, 18, 12], 'association': 'Unknown'},
            {'requested_operation': 18, 'declared_positive': [181, 18, 12], 'association': 'Unknown'}])
        for op in ('11', '12'):
            self.assertIn(f'| {op} | B5/12/0C | Unknown |', self.page)

    def test_short_extra_preserve_raw_no_reply_choice(self):
        for e in self.data['entries']:
            f = e['field']
            width = f['width_bits'] // 8
            for raw in (b'', b'\xa5' * (width - 1), b'\x5a' * (width + 1)):
                got = evaluate(f, raw)
                self.assertEqual(got, dict(raw=raw, value=None, replacement=False,
                                          physical_reply_selection=False))

    def test_page_tables_independent_of_fixture(self):
        coordinate = [['OP', 'Direction', 'Field', 'Position', 'Width (bits)', 'Encoding']]
        coordinate += [line.split() for line in COORDINATES.splitlines()]
        bits = [['OP', 'Direction', 'Field', 'Bits 0 through 7']]
        bits += [[f'{op:02X}', d, f, '; '.join(labels)] for (op, d, f), labels in BITS.items()]
        relationships = [['OP', 'Direction', 'Field(s)', 'Relationship']] + split_rows(RELATIONSHIPS)
        conflicts = [['Requested OP', 'Declared positive PB/SB/OP', 'Association'],
                     ['11', 'B5/12/0C', 'Unknown'], ['12', 'B5/12/0C', 'Unknown']]
        self.assertEqual(tables(self.page), [coordinate, bits, relationships, conflicts])

    def test_native_unknown_and_raw_boundaries(self):
        text = ' '.join(self.page.split())
        for phrase in (
            'are **Hypothesis**, not a native qualification.',
            '**Proven** is limited to the checked synthetic representation and arithmetic.',
            'physical lengths, negative replies and qualification remain **Unknown**.',
            'Positions are not physical wire offsets or a response-length rule.',
            'Replacement is not an unavailable assertion.',
            'All defaults except that pressure default are Unknown.',
            'Approximate 50 has no invented tolerance.',
            'Short or extra synthetic abstract structures stay raw and cannot choose a physical reply form.',
            'including reserved and unmodeled bit 7;',
            'The conflict establishes neither reply association nor acceptance.',
        ):
            self.assertIn(phrase, text)
        self.assertIn('(../ebus-services/ebus-overview.md)', self.page)
        self.assertIn('(ebus-vaillant-B512.md)', self.page)
        self.assertNotRegex(self.page + FIXTURE.read_text(), r'Ab19|GraphQL|MCP|json.RawMessage')

    def test_exact_api_types_and_all_eleven_axes(self):
        assert_axis_contract(self, self.api)
        for signature in ('func Ab19Entries() (json.RawMessage, error)',
                          'func Ab19Lookup(Ab19Key) (json.RawMessage, bool, error)'):
            self.assertIn(signature, self.api)
        self.assertIn('Package `vaillant`', self.api)

    def test_each_axis_contract_mutation_rejected(self):
        # This is a documentation validator, not a replacement Go lookup.
        # Each control changes only one documented identity axis.
        assert_axis_contract(self, self.api)
        for row in split_rows(AXES):
            with self.subTest(axis=row[0]):
                original = '| ' + ' | '.join(row) + ' |'
                for index in (0, 1, 2, 3):
                    changed = row.copy()
                    changed[index] = 'other'
                    text = self.api.replace(original, '| ' + ' | '.join(changed) + ' |')
                    self.assertNotEqual(text, self.api)
                    with self.assertRaises(AssertionError):
                        assert_axis_contract(self, text)
        for axis in ('Ab19Secondary', 'Ab19Operation', 'Ab19Group', 'Ab19Register'):
            row = next(row for row in split_rows(AXES) if row[0] == axis)
            text = self.api.replace(' | '.join(row), ' | '.join(row).replace(
                'absent differs from explicit zero', 'absent equals explicit zero').replace(
                'absent to explicit zero', 'absent equals explicit zero'))
            self.assertNotEqual(text, self.api)
            with self.assertRaises(AssertionError):
                assert_axis_contract(self, text)

    def test_api_error_copy_raw_and_qualification_contract(self):
        text = ' '.join(self.api.split())
        for phrase in (
            '`Ab19Entries` returns a JSON array.',
            '`Ab19Lookup` returns exactly one whole row for an exact key;',
            'a missing exact key returns `(nil, false, nil)`.',
            'Invalid embedded JSON or duplicate keys produce an error from both calls;',
            'Validation covers the whole embedded catalog before lookup,',
            'Every call returns independent deep byte copies.',
            'Mutating any returned row or entries buffer cannot affect a later result from either function.',
            'Optional absent and explicit zero differ for Secondary, Operation, Group and Register.',
            'non-applicable strings use `none`.',
            'Instance scope is a string such as `00` or `dynamic`, never an invented numeric instance.',
            'There is no wildcard, nearest-key, cross-family, variant, direction, field or alternative fallback.',
            'Each production row has an `ab19_` ID, the complete eleven-axis identity,',
            'Raw form is retained, including short and extra abstract structures.',
            'Partial last-known-good state and raw evidence must survive',
            'Admission fails closed:',
            'Existing catalog/provider APIs and routability remain unchanged.',
            'eBUS MCP compatibility and GraphQL parity remain unchanged:',
            'OP11 and OP12 each retain literal positive B5/12/0C',
            'with selector conflict, decoder selection false and acceptance false.',
            'Dependency direction is page to registry;',
            'Merge does not reinterpret a candidate as native qualification.',
            'they do not execute the companion Go package or establish its runtime behavior.',
            'Nothing is stable before Helianthus 1.0.',
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
