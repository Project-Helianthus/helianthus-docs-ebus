"""Finite owned page/example seam; no production registry or native decoder."""

import copy
import json
from pathlib import Path
import re
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/am18_b50e_rule_value_rows.md'
FIXTURE = ROOT / 'architecture/fixtures/am18_b50e_rule_value_rows.json'
IDENTITY = dict(family='vaillant', variant='B50E', primary=181, secondary=14,
                operation=2, direction='positive', field='rule_value_row')
CONTRACT = dict(
    identity=IDENTITY, count=19, offset_origin='isolated_row', byte_order='Unknown',
    default='Unknown', inverse='opaque', numeric_decoder=False,
    universal_boolean=False, qualified=False,
    grades=dict(software='Proven', meaning='Hypothesis', native='Unknown'),
    unknown=['physical_support', 'presence', 'freshness', 'execution', 'effects',
             'persistence', 'delivery', 'physical_base', 'logical_base'])
# Literal independent oracle: key, kind, value width, companion, offset, width.
EXPECTED = [
    (0, 'opaque', None, None, None, None),
    (1, 'boolean_u8', 1, None, None, None),
    (2, 'u8', 1, None, None, None),
    (3, 'i8', 1, None, None, None),
    (4, 'u16', 2, None, None, None),
    (5, 'i16', 2, None, None, None),
    (6, 'u32', 4, None, None, None),
    (7, 'i32', 4, None, None, None),
    (8, 'secure_boolean_u8', 1, None, None, None),
    (9, 'u8', 1, 'inverse', 1, 1),
    (10, 'i8', 1, 'inverse', 1, 1),
    (11, 'u16', 2, 'inverse', 2, 2),
    (12, 'i16', 2, 'inverse', 2, 2),
    (13, 'u32', 4, 'inverse', 4, 4),
    (14, 'i32', 4, 'inverse', 4, 4),
    (15, 'opaque', None, None, None, None),
    (16, 'opaque', None, None, None, None),
    (17, 'temperature_i16_div16_celsius', 2, 'status', 2, 1),
    (18, 'temperature_i16_div16_celsius', 2, 'inverse', 2, 2)]
RAW = ['d37a', '01', 'c7', '80', '1234', '0080', '12345678', '00000080',
       '0f', 'a517', '8062', '12341952', '00806328', '1234567807243958',
       '0000008018365572', '9b', '8271', '008055', 'ff7f2361']


def identity(key, **changes):
    return dict(IDENTITY, key=key, **changes)


def validate_identity(value):
    if not isinstance(value, dict) or set(value) != set(IDENTITY) | {'key'}:
        raise ValueError('identity shape')
    for field in ('primary', 'secondary', 'operation', 'key'):
        if type(value[field]) is not int or not 0 <= value[field] <= 255:
            raise ValueError('identity byte')
    for field in ('family', 'variant', 'direction', 'field'):
        if type(value[field]) is not str or not value[field]:
            raise ValueError('identity string')


class RowView:
    """Test-only admission and raw projection of the owned examples."""

    def __init__(self, rows):
        if not isinstance(rows, list) or len(rows) != 19:
            raise ValueError('catalog count')
        admitted = {}
        kinds = ['opaque', 'boolean_u8', 'u8', 'i8', 'u16', 'i16', 'u32', 'i32',
                 'secure_boolean_u8', 'u8', 'i8', 'u16', 'i16', 'u32', 'i32',
                 'opaque', 'opaque', 'temperature_i16_div16_celsius',
                 'temperature_i16_div16_celsius']
        widths = dict(boolean_u8=1, u8=1, i8=1, u16=2, i16=2, u32=4, i32=4,
                      secure_boolean_u8=1, temperature_i16_div16_celsius=2)
        for row in rows:
            if not isinstance(row, dict) or type(row.get('key')) is not int:
                raise ValueError('row key')
            key = row['key']
            if not 0 <= key < 19 or key in admitted:
                raise ValueError('row key coverage')
            value = dict(kind=kinds[key], offset=0)
            width = widths.get(kinds[key])
            if width is not None:
                value['width'] = width
            expected = dict(key=key, grade='Hypothesis', value=value)
            if 9 <= key <= 14 or key in (17, 18):
                expected['companion'] = dict(
                    kind='status' if key == 17 else 'inverse', offset=width,
                    width=1 if key == 17 else width)
            # JSON equivalence also rejects bool/float aliases for integers.
            if json.dumps(row, sort_keys=True) != json.dumps(expected, sort_keys=True):
                raise ValueError('row metadata')
            admitted[key] = copy.deepcopy(row)
        self._rows = admitted

    def enumerate(self):
        return [copy.deepcopy(self._rows[k]) for k in sorted(self._rows)]

    def lookup(self, selection):
        validate_identity(selection)
        if any(selection[k] != v for k, v in IDENTITY.items()):
            return None
        return copy.deepcopy(self._rows.get(selection['key']))


def project(rows, selection, raw, previous):
    """No endian choice, numeric decoding, padding, or inverse validation."""
    result = dict(status='malformed', metadata=None, fields={}, raw=None,
                  tail=bytearray(), last_known_good=copy.deepcopy(previous),
                  grade='Unknown', qualified=False)
    if not isinstance(raw, (bytes, bytearray)):
        return result
    result['raw'] = bytearray(raw)
    try:
        meta = RowView(rows).lookup(selection)
    except (ValueError, TypeError):
        return result
    if meta is None:
        result['status'] = 'no_match'
        return result
    result.update(metadata=meta, grade='Hypothesis')
    if 'width' not in meta['value']:
        result['status'] = 'opaque'
        result['fields']['value'] = dict(raw=bytearray(raw), complete=None)
        return result
    end = 0
    for field in ('value', 'companion'):
        if field not in meta:
            continue
        spec = meta[field]
        start, width = spec['offset'], spec['width']
        end = max(end, start + width)
        piece = bytearray(raw[start:start + width])
        output = dict(raw=piece, complete=len(piece) == width)
        if output['complete'] and field == 'value' and selection['key'] == 8:
            output['mapping'] = {15: 'true', 240: 'false'}.get(piece[0], 'unmapped')
        if output['complete'] and spec['kind'] == 'status':
            output['mapping'] = {0: 'okay', 85: 'short', 170: 'interrupted'}.get(
                piece[0], 'unmapped')
        result['fields'][field] = output
    result['status'] = 'complete' if len(raw) >= end else 'partial'
    result['tail'] = bytearray(raw[end:])
    return result


class RuleValueRowsContract(unittest.TestCase):
    def setUp(self):
        self.package = json.loads(FIXTURE.read_text())
        self.rows = self.package['rows']
        self.page = PAGE.read_text()
        self.view = RowView(self.rows)

    def test_exact_package_policy_and_page(self):
        self.assertEqual(set(self.package), {'kind', 'contract', 'rows', 'examples',
                                          'mapping_cases', 'partial', 'extra'})
        self.assertEqual(self.package['kind'], 'AM18SyntheticRowPackage')
        self.assertEqual(self.package['contract'], CONTRACT)
        declared = json.loads(re.search(r'```json\n(.*?)\n```', self.page, re.S)[1])
        self.assertEqual(declared, CONTRACT)
        for text in ('End-of-data keys\n0/15/16 do not mean zero-width values',
                     'no bitwise-complement validation',
                     'The OP02 table must not decode OP03 buffer bytes',
                     'Byte order and defaults remain Unknown',
                     'No signed word is\ndecoded without explicit byte-order qualification',
                     'Existing eBUS MCP compatibility and GraphQL parity remain unchanged',
                     'comparison flags, the clear-index catalog and active rule execution remain',
                     'following registry prerequisite AM17', 'Proven (software contract)',
                     'Hypothesis', 'Unknown'):
            self.assertIn(text, self.page)

    def test_all_19_independent_metadata_and_page_cells(self):
        self.assertEqual([r['key'] for r in self.rows], list(range(19)))
        self.assertEqual(self.view.enumerate(), self.rows)
        self.assertEqual(RowView(list(reversed(self.rows))).enumerate(), self.rows)
        section = self.page.split('| Key | Value kind |', 1)[1].split('\n\n', 1)[0]
        page_rows = [line for line in section.splitlines() if line.startswith('|')][1:]
        self.assertEqual(len(page_rows), 19)
        for row, expected, line in zip(self.rows, EXPECTED, page_rows):
            key, kind, width, companion, offset, cwidth = expected
            with self.subTest(key=key):
                self.assertEqual(row['grade'], 'Hypothesis')
                self.assertEqual(row['value']['offset'], 0)
                self.assertEqual(row['value']['kind'], kind)
                self.assertEqual(row['value'].get('width'), width)
                self.assertEqual('width' in row['value'], width is not None)
                self.assertEqual('companion' in row, companion is not None)
                c = row.get('companion', {})
                self.assertEqual((c.get('kind'), c.get('offset'), c.get('width')),
                                 (companion, offset, cwidth))
                cells = [s.strip() for s in line.strip('|').split('|')]
                self.assertEqual(cells, [str(key), kind, '0',
                    str(width) if width is not None else 'absent',
                    companion or 'absent', str(offset) if offset is not None else 'absent',
                    str(cwidth) if cwidth is not None else 'absent', 'Hypothesis'])
                self.assertEqual(self.view.lookup(identity(key)), row)

    def test_independent_raw_controls_and_arithmetic(self):
        self.assertEqual(self.package['examples'],
                         [dict(key=k, raw=raw) for k, raw in enumerate(RAW)])
        for (key, kind, width, companion, offset, cwidth), raw in zip(EXPECTED, RAW):
            data = bytes.fromhex(raw)
            got = project(self.rows, identity(key), data, {})
            self.assertEqual(got['raw'], data)
            self.assertEqual(got['fields']['value']['raw'],
                             data if width is None else data[:width])
            self.assertEqual(got['status'], 'opaque' if width is None else 'complete')
            self.assertEqual(got['grade'], 'Hypothesis')
            self.assertIs(got['qualified'], False)
            if companion:
                self.assertEqual(got['fields']['companion']['raw'], data[offset:offset+cwidth])
            self.assertNotIn('number', got['fields']['value'])
            if key == 1:
                self.assertNotIn('mapping', got['fields']['value'])
        # Explicit endian here qualifies arithmetic only, never the dictionary.
        low = struct.unpack('<h', b'\x00\x80')[0]
        high = int.from_bytes(b'\xff\x7f', 'little', signed=True)
        self.assertEqual((low, high), (-32768, 32767))
        self.assertEqual((low / 16, high / 16), (-2048, 2047.9375))
        self.assertEqual(struct.unpack('b', b'\x80')[0], -128)
        self.assertEqual(int.from_bytes(b'\xc7', 'big'), 199)
        self.assertIn('-32768..32767', self.page)
        self.assertIn('-2048..2047.9375', self.page)

    def test_all_boolean_status_bytes_and_page_cases(self):
        expected_cases = [dict(name='key8_'+name, key=8, raw=raw, mapping=name)
                          for raw, name in [('0f', 'true'), ('f0', 'false'), ('00', 'unmapped')]]
        expected_cases += [dict(name='key17_'+name, key=17, raw='1234'+raw, mapping=name)
                           for raw, name in [('00', 'okay'), ('55', 'short'),
                                             ('aa', 'interrupted'), ('ff', 'unmapped')]]
        self.assertEqual(self.package['mapping_cases'], expected_cases)
        section = self.page.split('| Case | Key | Raw row | Mapping |', 1)[1].split('\n\n', 1)[0]
        lines = [line for line in section.splitlines() if line.startswith('|')][1:]
        page_cases = [[cell.strip() for cell in line.strip('|').split('|')] for line in lines]
        self.assertEqual(page_cases, [[c['name'], str(c['key']), c['raw'], c['mapping']]
                                     for c in expected_cases])
        for case in expected_cases:
            got = project(self.rows, identity(case['key']), bytes.fromhex(case['raw']), {})
            field = 'value' if case['key'] == 8 else 'companion'
            self.assertEqual(got['fields'][field]['mapping'], case['mapping'])
        for byte in range(256):
            b = bytes([byte])
            a = project(self.rows, identity(8), b, {})
            s = project(self.rows, identity(17), b'\x12\x34'+b, {})
            self.assertEqual(a['fields']['value']['mapping'],
                             'true' if byte == 15 else 'false' if byte == 240 else 'unmapped')
            self.assertEqual(s['fields']['companion']['mapping'],
                             'okay' if byte == 0 else 'short' if byte == 85 else
                             'interrupted' if byte == 170 else 'unmapped')
            plain = project(self.rows, identity(1), b, {})
            self.assertNotIn('mapping', plain['fields']['value'])

    def test_every_identity_axis_independently(self):
        control = identity(9)
        changes = dict(family='other-family', variant='other-variant', primary=180,
                       secondary=15, operation=3, direction='request', key=19,
                       field='rule_comparison')
        for axis, alternative in changes.items():
            with self.subTest(axis=axis):
                changed = dict(control, **{axis: alternative})
                got = project(self.rows, changed, b'\xa5\x17', {})
                self.assertEqual((got['status'], got['metadata'], got['fields']),
                                 ('no_match', None, {}))
                self.assertEqual(got['raw'], b'\xa5\x17')
                self.assertEqual(got['grade'], 'Unknown')
                self.assertEqual(project(self.rows, control, b'\xa5\x17', {})['status'], 'complete')
        self.assertIsNotNone(self.view.lookup(identity(0)))
        for key in range(19):
            self.assertIsNone(self.view.lookup(dict(identity(key), operation=3)))

    def test_missing_zero_malformed_extra_identity(self):
        control = identity(9)
        for axis in control:
            missing = dict(control)
            del missing[axis]
            self.assertEqual(project(self.rows, missing, b'ab', {})['status'], 'malformed')
            if axis in ('primary', 'secondary', 'operation', 'key'):
                zero = dict(control, **{axis: 0})
                self.assertNotEqual(project(self.rows, zero, b'ab', {})['status'], 'malformed')
                bad_values = (None, True, '0', -1, 256, 0.0, [], {})
            else:
                bad_values = (None, True, 0, '', [], {})
            for bad in bad_values:
                self.assertEqual(project(self.rows, dict(control, **{axis: bad}), b'ab', {})['status'],
                                 'malformed', (axis, bad))
        for selection in (None, [], dict(control, extra=0)):
            self.assertEqual(project(self.rows, selection, b'ab', {})['status'], 'malformed')

    def test_admission_fails_closed_preserving_raw_and_previous(self):
        malformed = [None, [], self.rows[:-1], self.rows+[copy.deepcopy(self.rows[0])]]
        for index in range(19):
            for axis in self.rows[index]:
                rows = copy.deepcopy(self.rows)
                del rows[index][axis]
                malformed.append(rows)
            for field in ('value', 'companion'):
                if field not in self.rows[index]:
                    continue
                for axis in self.rows[index][field]:
                    rows = copy.deepcopy(self.rows)
                    del rows[index][field][axis]
                    malformed.append(rows)
                    for bad in (None, True, 0.0, 'unknown', 255):
                        rows = copy.deepcopy(self.rows)
                        rows[index][field][axis] = bad
                        malformed.append(rows)
            rows = copy.deepcopy(self.rows)
            rows[index]['extra'] = 0
            malformed.append(rows)
        for index in (0, 15, 16):
            rows = copy.deepcopy(self.rows)
            rows[index]['value']['width'] = 0
            malformed.append(rows)
        for field, value in [('key', 19), ('key', 1), ('grade', 'Proven')]:
            rows = copy.deepcopy(self.rows)
            rows[0][field] = value
            malformed.append(rows)
        previous = {'independent_field': 0, 'old': [5]}
        for rows in malformed:
            got = project(rows, identity(9), b'\xa5\x17', previous)
            self.assertEqual(got['status'], 'malformed')
            self.assertIsNone(got['metadata'])
            self.assertEqual(got['fields'], {})
            self.assertEqual(got['grade'], 'Unknown')
            self.assertIs(got['qualified'], False)
            self.assertEqual(got['raw'], b'\xa5\x17')
            self.assertEqual(got['last_known_good'], previous)
        bad_rows = copy.deepcopy(self.rows)
        bad_rows[0]['value']['width'] = 0
        source = bytearray(b'ab')
        prior = {'nested': [0]}
        fallback = project(bad_rows, identity(9), source, prior)
        source[0] = 9
        prior['nested'][0] = 8
        self.assertEqual(fallback['raw'], b'ab')
        self.assertEqual(fallback['last_known_good'], {'nested': [0]})
        fallback['raw'][1] = 7
        fallback['last_known_good']['nested'][0] = 6
        self.assertEqual(source, bytearray([9, 98]))
        self.assertEqual(prior, {'nested': [8]})
        self.assertEqual(project(self.rows, identity(9), b'ab', {})['status'], 'complete')

    def test_every_inverse_byte_independently_without_complement(self):
        for key, width in [(9, 1), (10, 1), (11, 2), (12, 2), (13, 4), (14, 4), (18, 2)]:
            base = bytearray.fromhex(RAW[key])
            self.assertEqual(len(base), 2 * width)
            for position in range(width):
                changed = bytearray(base)
                changed[width+position] ^= 0x39
                got = project(self.rows, identity(key), changed, {})
                self.assertEqual(got['status'], 'complete')
                self.assertEqual(got['fields']['value']['raw'], base[:width])
                self.assertEqual(got['fields']['companion']['raw'], changed[width:])
                self.assertNotEqual(changed[width+position], base[width+position])
                self.assertNotEqual(changed[width+position], base[position] ^ 255)

    def test_all_prefixes_extra_tail_and_independent_fields(self):
        self.assertEqual(self.package['partial'], dict(key=13, raw='123456780724',
                                                     previous=dict(independent_field=0)))
        self.assertEqual(self.package['extra'], dict(key=9, raw='a517ee', tail='ee'))
        for key, kind, width, companion, offset, cwidth in EXPECTED:
            raw = bytes.fromhex(RAW[key])
            if width is None:
                for data in (b'', raw):
                    got = project(self.rows, identity(key), data, {})
                    self.assertEqual(got['status'], 'opaque')
                    self.assertIsNone(got['fields']['value']['complete'])
                continue
            extent = width + (cwidth or 0)
            for size in range(extent + 1):
                got = project(self.rows, identity(key), raw[:size], {'independent_field': 0})
                self.assertEqual(got['status'], 'complete' if size == extent else 'partial')
                self.assertEqual(got['grade'], 'Hypothesis')
                self.assertIs(got['qualified'], False)
                self.assertEqual(got['fields']['value']['raw'], raw[:min(size, width)])
                self.assertEqual(got['fields']['value']['complete'], size >= width)
                if companion:
                    c = got['fields']['companion']
                    self.assertEqual(c['raw'], raw[offset:min(size, extent)])
                    self.assertEqual(c['complete'], size >= extent)
                    if not c['complete']:
                        self.assertNotIn('mapping', c)
                self.assertEqual(got['last_known_good'], {'independent_field': 0})
            extra = project(self.rows, identity(key), raw + b'\xee', {})
            self.assertEqual(extra['tail'], b'\xee')
            self.assertEqual(extra['raw'], raw + b'\xee')
        p = project(self.rows, identity(13), bytes.fromhex('123456780724'), {'independent_field': 0})
        self.assertEqual(p['fields']['value']['raw'], bytes.fromhex('12345678'))
        self.assertEqual(p['fields']['companion']['raw'], bytes.fromhex('0724'))
        for bad in (None, 'a517', [165, 23], 0):
            self.assertEqual(project(self.rows, identity(9), bad, {})['status'], 'malformed')

    def test_owned_memory_for_inputs_outputs_and_enumeration(self):
        rows = copy.deepcopy(self.rows)
        view = RowView(rows)
        rows[9]['value']['offset'] = 99
        first = view.lookup(identity(9))
        first['value']['offset'] = 77
        listing = view.enumerate()
        listing[9]['companion']['width'] = 99
        self.assertEqual(view.lookup(identity(9))['value']['offset'], 0)
        self.assertEqual(view.enumerate()[9]['companion']['width'], 1)
        raw = bytearray.fromhex('a517ee')
        previous = {'nested': [0]}
        got = project(self.rows, identity(9), raw, previous)
        raw[0] = 0
        previous['nested'][0] = 3
        self.assertEqual(got['raw'], bytes.fromhex('a517ee'))
        self.assertEqual(got['last_known_good'], {'nested': [0]})
        got['fields']['value']['raw'][0] = 4
        got['fields']['companion']['raw'][0] = 5
        got['tail'][0] = 6
        self.assertEqual(got['raw'], bytes.fromhex('a517ee'))
        got['raw'][0] = 7
        got['metadata']['value']['offset'] = 88
        got['last_known_good']['nested'][0] = 8
        self.assertEqual(raw, bytes.fromhex('0017ee'))
        self.assertEqual(previous, {'nested': [3]})
        self.assertEqual(self.rows[9]['value']['offset'], 0)
        self.assertEqual(project(self.rows, identity(9), b'\xa5\x17', {})['status'], 'complete')

    def test_local_relative_links_and_native_prerequisite(self):
        for target in re.findall(r'\]\(([^)]+)\)', self.page):
            self.assertNotIn('://', target)
            path, anchor = (target.split('#', 1) + [''])[:2]
            linked = PAGE.parent / path
            self.assertTrue(linked.is_file(), target)
            if anchor:
                headings = re.findall(r'^#+ (.+)$', linked.read_text(), re.M)
                slugs = [re.sub(r'[^\w -]', '', h.lower()).replace(' ', '-') for h in headings]
                self.assertIn(anchor, slugs)
        native = (ROOT / 'protocols/vaillant/ebus-vaillant-B50E.md').read_text()
        self.assertIn('Inverse bytes are carried raw.', native)
        self.assertIn('the rule-read type table does not apply to the buffer', native)


if __name__ == '__main__':
    unittest.main()
