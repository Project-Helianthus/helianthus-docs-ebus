"""Independent finite B520 synthetic contract; no native qualification."""
import copy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-b520-blocks.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ai20_b520_blocks.json'
HEADERS = 'operation direction field position encoding domain minimum maximum default prefix grade'.split()


def expected_rows():
    # Independent layouts from the issue, not from the page or fixture.
    layouts = [
        ('01', 'request', 'status:3'), ('01', 'positive', 'status:3'),
        ('02', 'request', 'status:3 address:4 flags:8 size-bits:9 block:10 start-bit:11'),
        ('02', 'positive', 'status:3'),
        ('03', 'request', 'status:3 block:4'),
        ('03', 'positive', 'status:3 block:4 data:5'),
        ('04', 'request', 'status:3 block:4 data:5'),
        ('04', 'positive', 'status:3'), ('05', 'request', 'status:3'),
        ('05', 'positive', 'status:3 version:4 max-block-length:5 max-variable-count:6 current-variable-count:7 max-block-count:8 current-block-count:9 error-code:10'),
        ('06', 'request', 'status:3 write-block:4 read-block:5 data:6'),
        ('06', 'positive', 'status:3 write-block:4 read-block:5 data:6'),
        ('07', 'request', 'reserved-identifier:3 reserved-offset:7 data:9'),
        ('07', 'positive', 'reserved-identifier:3 reserved-offset:7 data:9'),
        ('02', 'negative', 'status:3 error:4'),
        ('03', 'negative', 'status:3 error:4'),
        ('04', 'negative', 'status:3 error:4'),
        ('06', 'negative', 'status:3 write-error:4 read-error:5')]
    rows = []
    for op, direction, layout in layouts:
        for item in layout.split():
            field, position = item.split(':')
            encoding, domain, low, high, default = 'u8', '0..255', '-', '-', '0'
            if field in ('address', 'reserved-identifier'):
                encoding, domain = 'u32 LE', '0..4294967295'
            elif field == 'reserved-offset':
                encoding, domain = 'u16 LE', '0..65535'
            elif field == 'data':
                encoding, domain, low, high, default = 'opaque', '-', 'Unknown', 'Unknown', 'Unknown'
                if op == '03':
                    low, high = '0', 'unset'
                if op == '07':
                    low, high, default = '0', '23', '0'
            elif (op in ('02', '03') and field == 'block') or (
                    op == '06' and direction == 'request' and field.endswith('-block')):
                domain = '0..254'
            if (direction != 'negative' and op in ('03', '04', '06')) or (
                    direction == 'negative' and field == 'status'):
                default = 'Unknown'
            rows.append(dict(zip(HEADERS, [op, direction, field, position,
                encoding, domain, low, high, default,
                'B5 20 ' + op if direction == 'negative' else 'Unknown', 'Hypothesis'])))
    return rows


POLICIES = {
    'native-grade': 'Hypothesis', 'physical-qualification': 'Unknown',
    'status-semantics': 'Unknown', 'block-correlation': 'Unknown',
    'atomicity': 'Unknown', 'physical-adaptation': 'Unknown', 'effects': 'Unknown',
    'support': 'Unknown', 'address-meaning': 'raw', 'reserved-meaning': 'raw',
    'ff-meaning': 'raw; no universal sentinel',
    'returned-maxima': 'raw; no universal limit', 'error-meaning': 'raw; no enum',
    'negative-is-nak': 'false', 'automatic-branch-selection': 'false',
    'incomplete-admission': 'false', 'last-known-good': 'retain'}


def expected_cases():
    values = [
        ('03', 'request', [0, 254], True), ('03', 'request', [0, 255], False),
        ('04', 'request', [0, 255], True), ('06', 'request', [0, 255, 1], False),
        ('06', 'positive', [0, 255, 255], True),
        ('02', 'request', [0, 120, 86, 52, 18, 0, 0, 254, 0], True),
        ('05', 'positive', list(range(8)), True),
        ('07', 'request', [120, 86, 52, 18, 52, 18] + list(range(23)), True),
        ('07', 'positive', [120, 86, 52, 18, 52, 18] + list(range(24)), False),
        ('06', 'negative', [0, 1, 2], True), ('02', 'negative', [0, 255], True),
        ('03', 'negative', [0, 0], True), ('04', 'negative', [0, 0], True),
        ('03', 'positive', [0, 0], True), ('04', 'positive', [0], True)]
    return [dict(operation=op, direction=d, body=' '.join(f'{b:02X}' for b in body), fits=fits)
            for op, d, body, fits in values]


def tables(text):
    groups = []
    for line in text.splitlines():
        if line.startswith('|'):
            if not groups or not active:
                groups.append([])
            groups[-1].append([x.strip() for x in line.strip('|').split('|')])
            active = True
        else:
            active = False
    result = []
    for group in groups:
        header, separator, *rows = group
        if separator != ['---'] * len(header) or any(len(r) != len(header) for r in rows):
            raise ValueError('table shape')
        result.append((header, [dict(zip(header, row)) for row in rows]))
    return result


def decode(rows, op, direction, body):
    """Local abstract admission only; caller supplies alternative, never guessed."""
    selected = [r for r in rows if (r['operation'], r['direction']) == (op, direction)]
    if not selected or any(type(b) is not int or not 0 <= b <= 255 for b in body):
        raise ValueError('unknown identity or invalid byte')
    fields = {}
    for row in selected:
        start = int(row['position']) - 3
        if row['encoding'] == 'opaque':
            if len(body) < start:
                raise ValueError('missing fixed fields')
            raw = body[start:]
            if (row['minimum'] != 'Unknown' and len(raw) < int(row['minimum'])) or (
                    row['maximum'] not in ('unset', 'Unknown') and len(raw) > int(row['maximum'])):
                raise ValueError('data length')
        else:
            width = {'u8': 1, 'u16 LE': 2, 'u32 LE': 4}[row['encoding']]
            if len(body) < start + width:
                raise ValueError('incomplete')
            raw = int.from_bytes(bytes(body[start:start + width]), 'little')
            low, high = map(int, row['domain'].split('..'))
            if not low <= raw <= high:
                raise ValueError('field domain')
        fields[row['field']] = raw
    last = selected[-1]
    if last['encoding'] != 'opaque':
        end = int(last['position']) - 3 + {'u8': 1, 'u16 LE': 2, 'u32 LE': 4}[last['encoding']]
        if len(body) != end:
            raise ValueError('extra bytes')
    return fields


class B520BlocksTests(unittest.TestCase):
    def setUp(self):
        self.page = PAGE.read_text()
        self.fixture = json.loads(FIXTURE.read_text())
        self.parsed = tables(self.page)
        self.sources = [self.parsed[0][1], self.fixture['declarations']]

    def test_exact_ordered_contracts_and_cases(self):
        self.assertEqual(len(self.parsed), 3)
        self.assertEqual(self.parsed[0][0], HEADERS)
        for rows in self.sources:
            self.assertEqual(rows, expected_rows())
        self.assertEqual(self.parsed[1][0], ['property', 'value'])
        self.assertEqual(self.parsed[1][1], [dict(property=k, value=v) for k, v in POLICIES.items()])
        self.assertEqual(self.fixture['policies'], POLICIES)
        self.assertEqual(self.parsed[2][0], ['operation', 'direction', 'body', 'fits'])
        self.assertEqual(self.parsed[2][1], [dict(c, fits=str(c['fits']).lower()) for c in expected_cases()])
        self.assertEqual(self.fixture['cases'], expected_cases())
        self.assertEqual(set(self.fixture), {'family', 'provenance', 'declarations', 'policies', 'cases'})
        self.assertEqual(self.fixture['family'], 'B520')
        self.assertEqual(self.fixture['provenance'], 'synthetic; issue #1009 finite declarations')
        for target in re.findall(r'\]\(([^)]+)\)', self.page):
            self.assertFalse('://' in target or target.startswith('/'))
            self.assertTrue((PAGE.parent / target).is_file())
        for phrase in ('B5 20 02', 'B5 20 03', 'B5 20 04',
                       '**Proven** applies\nonly to synthetic representation',
                       'A negative object is separate from a physical NAK.'):
            self.assertIn(phrase, self.page)

    def test_cases_raw_arithmetic_and_independent_errors(self):
        for rows in self.sources:
            for case in self.fixture['cases']:
                body = list(bytes.fromhex(case['body']))
                if not case['fits']:
                    with self.assertRaises(ValueError):
                        decode(rows, case['operation'], case['direction'], body)
                else:
                    decode(rows, case['operation'], case['direction'], body)
            self.assertEqual(decode(rows, '02', 'request', [0, 120, 86, 52, 18, 0, 0, 254, 0])['address'],
                             120 + 86 * 256 + 52 * 65536 + 18 * 16777216)
            self.assertEqual(decode(rows, '06', 'negative', [0, 1, 2]),
                             {'status': 0, 'write-error': 1, 'read-error': 2})
            self.assertEqual(decode(rows, '05', 'positive', list(range(8))),
                dict(zip(['status', 'version', 'max-block-length', 'max-variable-count',
                          'current-variable-count', 'max-block-count', 'current-block-count', 'error-code'], range(8))))
            self.assertEqual(decode(rows, '07', 'request', [120, 86, 52, 18, 52, 18]),
                {'reserved-identifier': 305419896, 'reserved-offset': 0x1234, 'data': []})
            # Same body is valid under both labels; no selection or NAK follows.
            for direction in ('positive', 'negative'):
                self.assertEqual(decode(rows, '03', direction, [0, 0])['status'], 0)

    def test_exhaustive_byte_domains_and_data_lengths(self):
        for rows in self.sources:
            for row in rows:
                if row['encoding'] != 'u8':
                    continue
                selected = [r for r in rows if (r['operation'], r['direction']) == (row['operation'], row['direction'])]
                last = selected[-1]
                length = int(last['position']) - 3 + (0 if last['encoding'] == 'opaque' else 1)
                for value in range(256):
                    body = [0] * length
                    body[int(row['position']) - 3] = value
                    excluded = value == 255 and (row['field'] == 'block' and row['operation'] in ('02', '03') or
                        row['operation'] == '06' and row['direction'] == 'request' and row['field'].endswith('-block'))
                    if excluded:
                        with self.assertRaises(ValueError):
                            decode(rows, row['operation'], row['direction'], body)
                    else:
                        self.assertEqual(decode(rows, row['operation'], row['direction'], body)[row['field']], value)
            for direction in ('request', 'positive'):
                for length in (0, 1, 22, 23, 24):
                    if length == 24:
                        with self.assertRaises(ValueError):
                            decode(rows, '07', direction, [0] * (6 + length))
                    else:
                        self.assertEqual(len(decode(rows, '07', direction, [0] * (6 + length))['data']), length)

    def test_negative_prefix_constants_each_axis(self):
        for rows in self.sources:
            for op, opcode in [('02', 2), ('03', 3), ('04', 4), ('06', 6)]:
                selected = [r for r in rows if r['operation'] == op and r['direction'] == 'negative']
                for row in selected:
                    actual = list(bytes.fromhex(row['prefix']))
                    self.assertEqual(actual, [181, 32, opcode])
                    for index, wrong in enumerate([180, 33, 7]):
                        changed = [181, 32, opcode]
                        changed[index] = wrong
                        self.assertNotEqual(actual, changed)

    def test_identity_axes_and_partial_retention(self):
        for rows in self.sources:
            raw = [0, 254]
            good = decode(rows, '03', 'request', raw)
            # Vary operation and direction independently with valid controls.
            self.assertEqual(decode(rows, '04', 'request', [0, 255])['block'], 255)
            self.assertEqual(decode(rows, '03', 'negative', raw)['error'], 254)
            for op, direction in [('08', 'request'), ('03', 'other')]:
                with self.assertRaises(ValueError):
                    decode(rows, op, direction, raw)
            for bad in ([], [0], [0, 255], [0, 254, 1], [0, -1], [0, 256]):
                retained = bad.copy()
                last_good = copy.deepcopy(good)
                with self.assertRaises(ValueError):
                    replacement = decode(rows, '03', 'request', bad)
                    last_good = replacement
                self.assertEqual(bad, retained)
                self.assertEqual(last_good, {'status': 0, 'block': 254})



if __name__ == '__main__':
    unittest.main()
