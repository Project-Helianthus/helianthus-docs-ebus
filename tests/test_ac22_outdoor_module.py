"""Synthetic declaration checks; no native behavior or qualification is inferred."""
import copy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-vaillant-b521.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ac22_outdoor_module.json'

# Independent finite expectations, not values loaded from the declaration.
REQUEST = '''3|0|raw-bit-0|01
3|1|raw-bit-1|02
3|2|raw-bit-2|04
3|3|raw-bit-3|08
3|4|raw-bit-4|10
3|5|raw-bit-5|20
3|6..7|reserved|C0
4|0|appliance-code-bit-0|01
4|1|appliance-code-bit-1|02
4|2|appliance-code-bit-2|04
4|3|appliance-code-bit-3|08
4|4|appliance-code-bit-4|10
4|5..7|reserved|E0'''
POSITIVE = '''3|0|ready|01
3|1|deicing-request|02
3|2|deicing-active|04
3|3|deicing-timeout-error|08
3|4|deicing-with-heater|10
3|5..6|reserved|60
3|7|cleaning-request|80
4|0|heater|01
4|1|relay-output|02
4|2|fan-running|04
4|3|brine-flow-reverse|08
4|4|fan-error|10
4|5|safety-limiter-error|20
4|6|hot-summer|40
4|7|bad-weather|80'''
SCALARS = [
    ('request', 5, 'noise-reduction', 'u8', [0, 255], 1, 1, 'percent'),
    ('request', 6, 'frost-protection-temperature', 'u8', [0, 255], 1, 1, 'degrees C'),
    ('positive', None, 'brine-pump-speed', 'u8', [0, 255], 1, 1, 'percent'),
    ('positive', None, 'fan-PWM', 'u8', [0, 255], 1, 1, 'percent'),
    ('positive', None, 'fan-speed', 'u8', [0, 255], 10, 1, 'rpm'),
    ('positive', None, 'temperature-1', 'signed LE16', [-32768, 32767], 1, 16, 'degrees C'),
    ('positive', None, 'temperature-2', 'signed LE16', [-32768, 32767], 1, 16, 'degrees C'),
]
UNKNOWN = ['complete request-bit names', 'positive scalar positions', 'variant',
           'operation', 'ventilation role', 'negative forms', 'acknowledgement',
           'retries/deadlines', 'atomicity', 'endpoint effects',
           'relationship to other registers', 'physical lengths',
           'native adaptation', 'peer effects', 'physical qualification']

EXAMPLES = [
    {'alternative': 'positive', 'field': 'ready', 'logical': 3, 'raw': '01', 'value': 'enabled'},
    {'alternative': 'positive', 'field': 'reserved', 'logical': 3, 'raw': '20', 'value': 1},
    {'alternative': 'positive', 'field': 'reserved', 'logical': 3, 'raw': '40', 'value': 2},
    {'alternative': 'positive', 'field': 'cleaning-request', 'logical': 3, 'raw': '80', 'value': 'enabled'},
    {'alternative': 'request', 'field': 'noise-reduction', 'raw': 'FF', 'value': 255, 'unit': 'percent'},
    {'alternative': 'positive', 'field': 'brine-pump-speed', 'raw': 'FF', 'value': 255, 'unit': 'percent'},
    {'alternative': 'positive', 'field': 'fan-PWM', 'raw': 'FF', 'value': 255, 'unit': 'percent'},
    {'alternative': 'positive', 'field': 'fan-speed', 'raw': 'FF', 'value': 2550, 'unit': 'rpm'},
    {'alternative': 'positive', 'field': 'temperature-1', 'raw': 'FE FF', 'value': -0.125, 'unit': 'degrees C'},
    {'alternative': 'positive', 'field': 'temperature-2', 'raw': 'FE FF', 'value': -0.125, 'unit': 'degrees C'},
]


def expected_bits(text):
    result = []
    for line in text.splitlines():
        logical, bits, name, mask = line.split('|')
        result.append(dict(logical=int(logical), bits=bits, name=name,
                           mask=int(mask, 16), default=0, grade='Hypothesis',
                           mappings={} if name == 'reserved' else
                           {'0': 'disabled', '1': 'enabled'}))
    return result


def expected_scalars(alternative):
    return [dict(logical=p, name=n, carrier=c, raw_domain=d, numerator=num,
                 denominator=den, unit=u, default=0, grade='Hypothesis')
            for a, p, n, c, d, num, den, u in SCALARS if a == alternative]


def expected_contract():
    entries = []
    for a, direction, extent, bits in [
            ('request', 'request', 7, expected_bits(REQUEST)),
            ('positive', 'response', 12, expected_bits(POSITIVE)),
            ('negative', 'response', None, [])]:
        entries.append(dict(family='outdoor-module', variant=None,
                            direction=direction, service='B521', operation=None,
                            alternative=a, logical_extent=extent,
                            physical_extent=None, grade='Hypothesis', bits=bits,
                            scalars=expected_scalars(a)))
    return dict(synthetic=True, representation_grade='Proven',
                interpretation_grade='Hypothesis', physical_qualification='Unknown',
                alternatives=['register-family', 'process-data'], unknown=UNKNOWN,
                entries=entries, examples=EXAMPLES)


def convert(field, raw):
    # Units annotate the single numeric conversion; they do not transform it.
    carrier = int.from_bytes(bytes.fromhex(raw), 'little',
                             signed=field['carrier'] == 'signed LE16')
    return carrier * field['numerator'] / field['denominator']


def rows(section):
    return [[cell.strip() for cell in line.strip('|').split('|')]
            for line in section.splitlines() if line.startswith('|')][2:]


# Same legacy role terms the initiator/target terminology lint rejects.
_LEGACY_ROLE = re.compile(
    r'\b(?:' + 'm' + 'aster' + '|' + 'sl' + 'ave' + r')\b', re.IGNORECASE)
_ROLE_MAP_BEGIN = '<!-- legacy-role-mapping:begin -->'
_ROLE_MAP_END = '<!-- legacy-role-mapping:end -->'


def legacy_role_hits(text):
    return [match.group(0) for match in _LEGACY_ROLE.finditer(text)]


def legacy_role_hits_outside_mapping(text):
    allowed = []
    search = 0
    while True:
        start = text.find(_ROLE_MAP_BEGIN, search)
        if start == -1:
            break
        stop = text.find(_ROLE_MAP_END, start)
        if stop == -1:
            break
        allowed.append((start, stop + len(_ROLE_MAP_END)))
        search = stop + len(_ROLE_MAP_END)
    return [match.group(0) for match in _LEGACY_ROLE.finditer(text)
            if not any(lo <= match.start() < hi for lo, hi in allowed)]


class OutdoorModuleTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def assert_contract(self, data):
        self.assertEqual(data, expected_contract())

    def test_complete_declaration(self):
        """Kills any altered field, conversion, grade, extent or lost alternative."""
        self.assert_contract(self.data)

    def test_identity_axes_independently(self):
        """Rejects each changed/missing identity component with a valid control."""
        self.assert_contract(self.data)
        for index in range(3):
            for axis in ('family', 'variant', 'direction', 'service', 'operation', 'alternative'):
                for replacement in ('distinct-synthetic-value', None):
                    with self.subTest(entry=index, axis=axis, replacement=replacement):
                        changed = copy.deepcopy(self.data)
                        if replacement is None:
                            del changed['entries'][index][axis]
                        else:
                            changed['entries'][index][axis] = replacement
                        with self.assertRaises(AssertionError):
                            self.assert_contract(changed)

    def test_walking_bits(self):
        """Kills swapped named/reserved masks and composite flag interpretation."""
        wants = [
            (0, 3, ['raw-bit-0', 'raw-bit-1', 'raw-bit-2', 'raw-bit-3',
                    'raw-bit-4', 'raw-bit-5', 'reserved', 'reserved']),
            (0, 4, ['appliance-code-bit-0', 'appliance-code-bit-1',
                    'appliance-code-bit-2', 'appliance-code-bit-3',
                    'appliance-code-bit-4', 'reserved', 'reserved', 'reserved']),
            (1, 3, ['ready', 'deicing-request', 'deicing-active',
                    'deicing-timeout-error', 'deicing-with-heater', 'reserved',
                    'reserved', 'cleaning-request']),
            (1, 4, ['heater', 'relay-output', 'fan-running', 'brine-flow-reverse',
                    'fan-error', 'safety-limiter-error', 'hot-summer', 'bad-weather'])]
        for index, position, names in wants:
            fields = [f for f in self.data['entries'][index]['bits'] if f['logical'] == position]
            for bit, want in enumerate(names):
                with self.subTest(entry=index, position=position, bit=bit):
                    self.assertEqual([f['name'] for f in fields if f['mask'] & (1 << bit)], [want])
            self.assertEqual(sum(f['mask'] for f in fields), 255)
            self.assertEqual(sum(f['mask'] & 255 for f in fields if f['name'] != 'reserved'),
                             [63, 31, 159, 255][wants.index((index, position, names))])

    def test_scalar_values(self):
        """Kills /10 fan speed, clipped percent, unsigned/BCD/sentinel temperature."""
        cases = [
            (0, 'noise-reduction', [('00', 0), ('01', 1), ('64', 100), ('FF', 255)]),
            (0, 'frost-protection-temperature', [('00', 0), ('FF', 255)]),
            (1, 'brine-pump-speed', [('00', 0), ('FF', 255)]),
            (1, 'fan-PWM', [('00', 0), ('FF', 255)]),
            (1, 'fan-speed', [('00', 0), ('01', 10), ('FF', 2550)]),
            (1, 'temperature-1', [('00 00', 0), ('FE FF', -0.125),
                                  ('00 80', -2048), ('FF 7F', 2047.9375)]),
            (1, 'temperature-2', [('00 00', 0), ('FE FF', -0.125),
                                  ('00 80', -2048), ('FF 7F', 2047.9375)])]
        for index, name, vectors in cases:
            field = next(f for f in self.data['entries'][index]['scalars'] if f['name'] == name)
            for raw, value in vectors:
                with self.subTest(name=name, raw=raw):
                    self.assertEqual(convert(field, raw), value)

    def test_synthetic_examples(self):
        """Kills raw/value changes, lost reserved evidence or invented positions."""
        self.assertEqual(self.data['examples'], EXAMPLES)
        for example in self.data['examples']:
            entry = next(e for e in self.data['entries'] if e['alternative'] == example['alternative'])
            if 'logical' in example:
                field = next(f for f in entry['bits'] if
                             f['name'] == example['field'] and f['logical'] == example['logical'])
                raw = int(example['raw'], 16)
                shift = (field['mask'] & -field['mask']).bit_length() - 1
                value = (raw & field['mask']) >> shift
                if field['mappings']:
                    value = field['mappings'][str(value)]
                self.assertEqual(value, example['value'])
            else:
                field = next(f for f in entry['scalars'] if f['name'] == example['field'])
                self.assertEqual(convert(field, example['raw']), example['value'])
                self.assertEqual(field['unit'], example['unit'])

    def test_page_bit_tables(self):
        """Kills page-only mask, field, position, mapping or grade changes."""
        candidate = self.page.split('## Candidate layout\n', 1)[1].split('## Profiles', 1)[0]
        for heading, following, expected in [
                ('### Request bits (Hypothesis)', '### Positive bits', REQUEST),
                ('### Positive bits (Hypothesis)', '### Scalars', POSITIVE)]:
            section = candidate.split(heading, 1)[1].split(following, 1)[0]
            wanted = [line.split('|')[:3] + ['0x' + line.split('|')[3]]
                      for line in expected.splitlines()]
            self.assertEqual(rows(section), wanted)
        self.assertIn('0 means disabled, 1 means enabled', candidate)
        self.assertIn('No composite appliance-code enum is\nestablished.', candidate)
        self.assertIn('zero default. Reserved bits default to zero', candidate)

    def test_page_scalar_table(self):
        """Kills guessed scalar positions, wrong scale/range/unit or added rows."""
        section = self.page.split('### Scalars (Hypothesis)', 1)[1].split('### Unresolved', 1)[0]
        self.assertEqual(rows(section), [
            ['request', '5', 'noise-reduction', 'u8', '0..255', 'raw', 'percent'],
            ['request', '6', 'frost-protection-temperature', 'u8', '0..255', 'raw', 'degrees C'],
            ['positive', 'Unknown', 'brine-pump-speed', 'u8', '0..255', 'raw', 'percent'],
            ['positive', 'Unknown', 'fan-PWM', 'u8', '0..255', 'raw', 'percent'],
            ['positive', 'Unknown', 'fan-speed', 'u8', '0..255', 'raw × 10', 'rpm'],
            ['positive', 'Unknown', 'temperature-1', 'signed LE16', '-32768..32767', 'raw ÷ 16', 'degrees C'],
            ['positive', 'Unknown', 'temperature-2', 'signed LE16', '-32768..32767', 'raw ÷ 16', 'degrees C']])
        for claim in ['All scalars default to zero', 'full raw carrier domain',
                      'Unit metadata does not scale the converted value again.',
                      'No BCD or sentinel\nconversion is established.',
                      'Percent values are not clipped to 100.',
                      '255 percent', '2550 rpm', '-0.125 degrees C']:
            self.assertIn(claim, section)

    def test_page_boundaries_and_unknowns(self):
        """Kills removed alternatives, changed extents/grades or erased unknowns."""
        section = self.page.split('## Candidate layout\n', 1)[1].split('## Profiles', 1)[0]
        for claim in [
                '**Hypothesis:** the outdoor-module family',
                'public TypeSpec register-family\ninterpretation',
                'same service, separate variants,\nor both remains **Unknown**',
                'Variant and operation are **Unknown**',
                '**Proven** applies only to the declared representation',
                'Every field interpretation below is **Hypothesis**',
                'Physical qualification,\nnative adaptation and peer effects are **Unknown**',
                'establishes no runtime capability or safe transmission',
                'they are not physical payload offsets',
                'Abstract request extent is 7', 'positive extent is 12',
                'Physical lengths are **Unknown**, not zero',
                'negative\nalternative has no established logical extent or fields',
                'Preserve raw bytes and\nunresolved alternatives',
                'slice remains partial',
                'acknowledgement alone does not establish resulting device state']:
            self.assertIn(claim, section)
        unresolved = section.split('### Unresolved properties (Unknown)', 1)[1]
        normalized = ' '.join(unresolved.split()).lower()
        for unknown in UNKNOWN:
            self.assertIn(unknown.lower(), normalized)
        # Preserve the separate, pre-existing register-family evidence.
        self.assertIn('| `4a 00` | `SourceInputSensorOffset` |', self.page)
        self.assertIn('| `3f 00` | `FanSpeedMax` |', self.page)

    def test_references_omit_legacy_role_term(self):
        """Kills restoring the rejected branch word in a public TypeSpec link.

        Page mutation: put that legacy role term back into either reference
        URL, or drop either TypeSpec file citation. A valid control keeps both
        public file paths and has no such term outside a role-mapping region.
        """
        references = self.page.split('## References\n', 1)[1]
        self.assertEqual(legacy_role_hits(references), [])
        self.assertIn(
            '- Public TypeSpec: [e0.omu.tsp](https://github.com/john30/ebusd-configuration) '
            'path `src/vaillant/e0.omu.tsp`',
            references)
        self.assertIn(
            '- Public TypeSpec: [e1.omu.1.tsp](https://github.com/john30/ebusd-configuration) '
            'path `src/vaillant/e1.omu.1.tsp`',
            references)
        self.assertEqual(legacy_role_hits_outside_mapping(self.page), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
