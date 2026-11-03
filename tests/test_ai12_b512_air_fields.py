"""Independent synthetic contract checks; no native-device qualification."""
import copy
import json
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-b512-air-fields.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ai12_b512_air_fields.json'

# Independent oracle: never derive expected constants from the page or fixture.
FIELD_TEXT = '''0B request 3 fan-1-target u16le 1 rpm 0
0B request 5 fan-2-target u16le 1 rpm 0
0B request 7 relay u8 1 raw 0
0B positive 3 fan-1-actual u16le 1 rpm 0
0B positive 5 fan-2-actual u16le 1 rpm 0
0B positive 7 status u8 1 raw 0
0B positive 8 temperature-1 s16le 16 degC 0
0B positive 10 temperature-2 s16le 16 degC 0
0B positive 12 temperature-3 s16le 16 degC 0
0C request 3 pulse u8 1 raw Unknown
0C request 4 P u8 1 raw Unknown
0C request 5 I u8 1 raw Unknown
0C request 6 D u8 1 raw Unknown
0C request 7 minimum-PWM s16le 256 percent 1.0
0C request 9 maximum-PWM s16le 256 percent 1.0
0C request 11 fan-count u8 1 raw Unknown
0C positive 3 feedback u8 1 raw 0
0D positive 3 digital u8 1 raw 0
0D positive 4 temperature-1 s16le 16 degC Unknown
0D positive 6 temperature-2 s16le 16 degC Unknown
0E positive 3 temperature s16le 16 degC 0
0E positive 5 humidity u16le 16 percent 0
0E positive 7 air-quality u16le 1 Unknown 0'''
FIELDS = []
for line in FIELD_TEXT.splitlines():
    row = line.split()
    row[2], row[5] = int(row[2]), int(row[5])
    FIELDS.append(row + ['Hypothesis'])
SHAPES = [['0B', 'request', 5], ['0B', 'positive', 11],
          ['0C', 'request', 9], ['0C', 'positive', 1],
          ['0D', 'request', 0], ['0D', 'positive', 5],
          ['0E', 'request', 0], ['0E', 'positive', 6]]
MEANINGS = [line.split() + ['Hypothesis'] for line in '''0B request relay bit-0=0 output-1-15V
0B request relay bit-0=1 output-1-tray-heater-relay
0B request relay bit-1=0 output-2-15V
0B request relay bit-1=1 output-2-tray-heater-relay
0B request relay bits-2..7 reserved
0B positive status 0 idle
0B positive status 1 running
0B positive status 255 fault
0B positive status 2..254 unlabeled
0C positive feedback 1 accepted
0C positive feedback 0,2..255 rejected
0D positive digital 0 false
0D positive digital 1 true
0D positive digital 2..255 unlabeled'''.splitlines()]
RANGES = [['u8', 0, 255, 1, 0, 255], ['u16le', 0, 65535, 1, 0, 65535],
          ['s16le', -32768, 32767, 16, -2048, 2047.9375],
          ['s16le', -32768, 32767, 256, -128, 127.99609375],
          ['u16le', 0, 65535, 16, 0, 4095.9375]]
SAMPLES = [
    ['0B', 'request', '02 01 04 03 04', [258, 772, 4]],
    ['0B', 'positive', '02 01 04 03 FF 10 00 F0 FF 00 00', [258, 772, 255, 1, -1, 0]],
    ['0C', 'request', '02 03 05 07 00 01 FF 7F 02', [2, 3, 5, 7, 1, 127.99609375, 2]],
    ['0C', 'request', '02 03 05 07 00 80 00 01 02', [2, 3, 5, 7, -128, 1, 2]],
    ['0C', 'positive', '01', [1]], ['0C', 'positive', '02', [2]],
    ['0D', 'request', '', []], ['0D', 'positive', '02 10 00 F0 FF', [2, 1, -1]],
    ['0E', 'request', '', []], ['0E', 'positive', 'F0 FF 40 06 FF FF', [-1, 100, 65535]],
    ['0E', 'positive', '10 00 50 06 FF FF', [1, 101, 65535]],
]
META = {'family': 'B512', 'grade': 'Hypothesis', 'physical_support': 'Unknown',
        'acknowledgement': 'Unknown', 'coordinate_system': 'logical, not wire offsets',
        'physical_packet_complete': False}
TABLES = {'Fields': FIELDS, 'Field spans': SHAPES,
          'Candidate token meanings': MEANINGS, 'Representation ranges': RANGES,
          'Evidence': [[op, side, raw or '(empty)',
                        ','.join(map(str, values)) or '(empty)']
                       for op, side, raw, values in SAMPLES]}


def page_tables(text):
    result = {}
    heading = None
    for line in text.splitlines():
        if line.startswith('## '):
            heading = line[3:]
        elif line.startswith('|'):
            result.setdefault(heading, []).append([v.strip() for v in line.strip('|').split('|')])
    return {key: rows[2:] for key, rows in result.items()}


def field_span(fields, op, side, raw):
    """Local field-only predicate; never claims physical packet completeness."""
    if (op, side) not in {(r[0], r[1]) for r in SHAPES}:
        raise ValueError('unknown candidate identity')
    rows = [r for r in fields if r[:2] == [op, side]]
    expected = sum(1 if r[4] == 'u8' else 2 for r in rows)
    if len(raw) != expected:
        raise ValueError('inexact synthetic field span')
    values = []
    cursor = 3
    for _, _, logical, _, kind, divisor, *_ in rows:
        if logical != cursor:
            raise ValueError('noncontiguous logical fields')
        width = 1 if kind == 'u8' else 2
        start = logical - 3  # Only within this synthetic field span, never a wire offset.
        value = int.from_bytes(raw[start:start + width], 'little', signed=kind == 's16le')
        values.append(value / divisor)
        cursor += width
    return values


class AirFieldsTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()
        (ROOT / '.tmp').mkdir(exist_ok=True)
        self.scratch = tempfile.TemporaryDirectory(prefix='ai12-', dir=ROOT / '.tmp')
        self.addCleanup(self.scratch.cleanup)

    def check_fixture_copy(self, data):
        path = Path(self.scratch.name) / FIXTURE.name
        path.write_text(json.dumps(data))
        self.assert_fixture(json.loads(path.read_text()))

    def check_page_copy(self, text):
        path = Path(self.scratch.name) / PAGE.name
        path.write_text(text)
        self.assert_page(path.read_text())

    def assert_fixture(self, data):
        self.assertEqual(set(data), set(META) | {'fields', 'shapes', 'meanings', 'ranges', 'samples'})
        for key, value in META.items():
            self.assertEqual(data[key], value, key)
        for key, value in [('fields', FIELDS), ('shapes', SHAPES), ('meanings', MEANINGS),
                           ('ranges', RANGES), ('samples', SAMPLES)]:
            self.assertEqual(data[key], value, key)

    def assert_page(self, text):
        expected = {key: [[str(cell) for cell in row] for row in rows]
                    for key, rows in TABLES.items()}
        self.assertEqual(page_tables(text), expected)

    def test_independent_fixture_and_page_tables(self):
        self.assert_fixture(self.data)
        self.assert_page(self.page)

    def test_all_samples_decode_in_order(self):
        for op, side, raw, expected in SAMPLES:
            with self.subTest(op=op, side=side, raw=raw):
                self.assertEqual(field_span(self.data['fields'], op, side, bytes.fromhex(raw)), expected)

    def test_ranges_and_default_arithmetic(self):
        for kind, low, high, divisor, minimum, maximum in self.data['ranges']:
            self.assertEqual(low / divisor, minimum)
            self.assertEqual(high / divisor, maximum)
            width = 1 if kind == 'u8' else 2
            for raw in (low, high):
                encoded = raw.to_bytes(width, 'little', signed=kind == 's16le')
                self.assertEqual(int.from_bytes(encoded, 'little', signed=kind == 's16le'), raw)
        for row in self.data['fields']:
            if row[7] != 'Unknown':
                raw = float(row[7]) * row[5]
                self.assertEqual(raw, int(raw))
                if row[3] in ('minimum-PWM', 'maximum-PWM'):
                    self.assertEqual(int(raw).to_bytes(2, 'little', signed=True), b'\x00\x01')

    def test_missing_extra_bytes_and_unknown_identities_fail_closed(self):
        for op, side, raw, expected in SAMPLES:
            control = bytes.fromhex(raw)
            self.assertEqual(field_span(self.data['fields'], op, side, control), expected)
            if control:
                with self.assertRaises(ValueError):
                    field_span(self.data['fields'], op, side, control[:-1])
            with self.assertRaises(ValueError):
                field_span(self.data['fields'], op, side, control + b'\x00')
        for op, side in [('0A', 'positive'), ('0B', 'negative')]:
            with self.assertRaises(ValueError):
                field_span(self.data['fields'], op, side, b'')
        self.assertIs(self.data['physical_packet_complete'], False)

    def test_every_claimed_fixture_cell_is_guarded(self):
        # Mutants execute against disposable copies of owned files, with a valid control.
        self.assert_fixture(self.data)
        for key in ('fields', 'shapes', 'meanings', 'ranges', 'samples'):
            for i, row in enumerate(self.data[key]):
                for j, value in enumerate(row):
                    mutant = copy.deepcopy(self.data)
                    mutant[key][i][j] = value + 1 if isinstance(value, (int, float)) else 'mutated'
                    with self.subTest(key=key, row=i, cell=j), self.assertRaises(AssertionError):
                        self.check_fixture_copy(mutant)

    def test_every_claimed_page_cell_is_guarded(self):
        self.assert_page(self.page)
        for line in self.page.splitlines():
            if not line.startswith('|') or line.startswith('| ---'):
                continue
            cells = line.strip('|').split('|')
            # Skip headers; all data rows are tested, including bytes and decoded values.
            if cells[0].strip() in ('OP', 'Type'):
                continue
            for j in range(len(cells)):
                changed = cells.copy()
                changed[j] = ' mutated '
                replacement = '|' + '|'.join(changed) + '|'
                with self.subTest(row=line, cell=j), self.assertRaises(AssertionError):
                    self.check_page_copy(self.page.replace(line, replacement, 1))

    def test_identity_axes_independently_with_valid_alternatives(self):
        self.assert_fixture(self.data)
        family = copy.deepcopy(self.data)
        family['family'] = 'B511'
        with self.assertRaises(AssertionError):
            self.check_fixture_copy(family)
        # OP, side, logical coordinate and named field each change independently.
        # All replacement values are valid elsewhere; no malformed-key shortcut.
        for axis, replacement in [(0, '0C'), (1, 'positive'), (2, 5), (3, 'fan-2-target')]:
            mutant = copy.deepcopy(self.data)
            mutant['fields'][0][axis] = replacement
            with self.subTest(axis=axis), self.assertRaises(AssertionError):
                self.check_fixture_copy(mutant)
        # Reversing direction layout or fan identity is independently rejected.
        mutant = copy.deepcopy(self.data)
        mutant['fields'][0], mutant['fields'][1] = mutant['fields'][1], mutant['fields'][0]
        with self.assertRaises(AssertionError):
            self.check_fixture_copy(mutant)

    def test_required_semantic_mutants_are_rejected(self):
        self.assert_fixture(self.data)
        mutants = {}
        shared = copy.deepcopy(self.data)
        shared['fields'] = [r for r in shared['fields'] if r[:2] != ['0B', 'positive']]
        shared['fields'][3:3] = [r[:1] + ['positive'] + r[2:] for r in FIELDS[:3]]
        mutants['shared-request-positive-layout'] = shared
        for name, key, row, cell, replacement in [
            ('unsigned-PWM', 'fields', 13, 4, 'u16le'),
            ('PWM-cap-100', 'ranges', 3, 5, 100),
            ('humidity-cap-100', 'ranges', 4, 5, 100),
            ('digital-2-as-true', 'meanings', 13, 4, 'true'),
            ('air-quality-ppm', 'fields', 22, 6, 'ppm'),
        ]:
            mutant = copy.deepcopy(self.data)
            mutant[key][row][cell] = replacement
            mutants[name] = mutant
        fan_swap = copy.deepcopy(self.data)
        fan_swap['samples'][0][2] = '04 03 02 01 04'
        mutants['reversed-fan-identity'] = fan_swap
        clipped = copy.deepcopy(self.data)
        clipped['samples'][10][3][1] = 100
        mutants['clipped-humidity-result'] = clipped
        for name, mutant in mutants.items():
            with self.subTest(mutation=name), self.assertRaises(AssertionError):
                self.check_fixture_copy(mutant)

    def test_token_alternatives_exhaustively(self):
        def label(op, side, field, raw):
            matches = []
            for row in self.data['meanings']:
                if row[:3] != [op, side, field]:
                    continue
                for alternative in row[3].split(','):
                    limits = [int(v) for v in alternative.split('..')]
                    if limits[0] <= raw <= limits[-1]:
                        matches.append(row[4])
            self.assertEqual(len(matches), 1)
            return matches[0]

        for raw in range(256):
            self.assertEqual(label('0C', 'positive', 'feedback', raw),
                             'accepted' if raw == 1 else 'rejected')
            self.assertEqual(label('0D', 'positive', 'digital', raw),
                             {0: 'false', 1: 'true'}.get(raw, 'unlabeled'))
            self.assertEqual(label('0B', 'positive', 'status', raw),
                             {0: 'idle', 1: 'running', 255: 'fault'}.get(raw, 'unlabeled'))
        relay = [r for r in self.data['meanings'] if r[:3] == ['0B', 'request', 'relay']]
        for raw in range(256):
            for bit in (0, 1):
                candidate = next(r[4] for r in relay if r[3] == f'bit-{bit}={(raw >> bit) & 1}')
                self.assertEqual(candidate, f'output-{bit + 1}-' +
                                 ('tray-heater-relay' if raw & (1 << bit) else '15V'))
            self.assertEqual(relay[-1][3:5], ['bits-2..7', 'reserved'])
            self.assertEqual(raw, (raw & 3) | (raw & 252))

    def test_grade_and_qualification_are_independent(self):
        for key in META:
            mutant = copy.deepcopy(self.data)
            mutant[key] = True if key == 'physical_packet_complete' else 'Proven'
            with self.subTest(key=key), self.assertRaises(AssertionError):
                self.check_fixture_copy(mutant)
        for required in ('**Proven (synthetic representation only):**', '**Hypothesis:**',
                         '**Unknown:**', 'Qualification\nis independent',
                         'not wire offsets', 'No native specification or capture'):
            self.assertIn(required, self.page)


if __name__ == '__main__':
    unittest.main()
