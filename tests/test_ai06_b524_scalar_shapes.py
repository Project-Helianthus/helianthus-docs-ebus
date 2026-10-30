"""Offline native declaration checks; no physical qualification or wire execution."""
import json
import re
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-b524-scalar-shapes.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ai06_b524_scalar_shapes.json'
# Independent contract: id, GG, RR, family, direction, role, codec, width.
EXPECTED = (
    ('zone-u8', 3, 27, None, 'read', 'scalar', 'u8', 1),
    ('zone-u16', 3, 27, None, 'read', 'scalar', 'u16', 2),
    ('gg01-byte14', 1, 20, None, 'read', 'scalar', 'u8', 1),
    ('gg01-byte19', 1, 25, None, 'read', 'scalar', 'u8', 1),
    ('gg01-float15', 1, 21, None, 'read', 'scalar', 'binary32', 4),
    ('room-mode', 3, 6, 'controller-family', 'write', 'mode', 'u16', 2),
    ('room-manual', 3, 34, 'VRC720 family', 'write', 'manual-temperature', 'binary32', 4),
    ('room-comfort', 3, 7, 'VRC700 family', 'write', 'comfort-temperature', 'binary32', 4),
)
CASES = (
    ('zone-u8', '01', 1), ('zone-u16', '01', None),
    ('zone-u8', '01 00', None), ('zone-u16', '01 00', 1),
    ('zone-u8', '00 01', None), ('zone-u16', '00 01', 256),
    ('gg01-byte14', '0E', 14), ('gg01-byte19', '13', 19),
    ('gg01-float15', '00 00 80 3F', 1.0), ('room-mode', '01 01', 257),
    ('room-manual', '00 00 80 3F', 1.0), ('room-comfort', '00 00 80 3F', 1.0),
)
AXES = ('opcode', 'group', 'instance', 'register', 'family', 'direction', 'role')


def tables(text):
    """Parse actual Markdown cells, including ordering and header names."""
    groups = []
    for block in text.split('\n\n'):
        lines = block.splitlines()
        if lines and all(line.startswith('|') for line in lines):
            rows = [[cell.strip() for cell in line.strip('|').split('|')] for line in lines]
            groups.append((rows[0], rows[2:]))
    return groups


def declarations():
    result = []
    for name, group, register, family, direction, role, codec, width in EXPECTED:
        result.append(dict(
            id=name,
            identity=dict(opcode=2, group=group, instance=None, register=register,
                          family=family, direction=direction, role=role),
            codec=codec, width=width,
            byte_order='not-applicable' if width == 1 else 'little-endian',
            factor=1, offset=0, unit=None, grade='Hypothesis'))
    return result


def candidates(entries, identity, request=b'', reply=b''):
    """Local exact declaration predicate: lengths never select alternatives."""
    return [entry for entry in entries if entry['identity'] == identity]


def interpret(entry, raw):
    """Local isolated-field arithmetic, not a native reply decoder."""
    evidence = bytes(raw)
    if len(raw) != entry['width']:
        return None, evidence
    codecs = {'u8': ('B', 1), 'u16': ('<H', 2), 'binary32': ('<f', 4)}
    fmt, width = codecs[entry['codec']]
    if len(raw) != width:
        return None, evidence
    value = struct.unpack(fmt, raw)[0]
    return value * entry['factor'] + entry['offset'], evidence


class ScalarShapes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = PAGE.read_text()
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.entries = cls.fixture['entries']

    def test_fixture_entire_contract_and_order(self):
        self.assertEqual(self.fixture, dict(
            service='B524', provenance='synthetic', physical_support='Unknown',
            entries=declarations(),
            cases=[dict(candidate=name, raw=raw, value=value) for name, raw, value in CASES]))
        for entry in self.entries:
            key = entry['identity']
            for axis in ('opcode', 'group'):
                self.assertIs(type(key[axis]), int)
                self.assertGreaterEqual(key[axis], 0)
                self.assertLessEqual(key[axis], 255)
            self.assertGreaterEqual(key['register'], 0)
            self.assertLessEqual(key['register'], 65535)
            self.assertIsNone(key['instance'])
            self.assertEqual(tuple(key), AXES)

    def test_page_tables_independent_constants(self):
        parsed = tables(self.document)
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0][0], [
            'Candidate', 'OP', 'GG', 'II', 'RR', 'Family', 'Direction', 'Role',
            'Codec', 'Width', 'Order', 'Factor', 'Offset', 'Unit', 'Grade'])
        expected = []
        for name, group, register, family, direction, role, codec, width in EXPECTED:
            expected.append([name, '02', f'{group:02X}', 'Unknown', f'{register:04X}',
                             family or 'Unknown', direction, role, codec, str(width),
                             'not-applicable' if width == 1 else 'little-endian',
                             '1', '0', 'Unknown', 'Hypothesis'])
        self.assertEqual(parsed[0][1], expected)
        self.assertEqual(parsed[1][0], ['Candidate', 'Raw field bytes', 'Local result'])
        self.assertEqual(parsed[1][1], [
            [name, raw, 'raw-only' if value is None else str(value)]
            for name, raw, value in CASES])
        # Every page declaration also reconstructs the independent fixture tuple.
        for row, entry in zip(parsed[0][1], self.entries):
            self.assertEqual(row[0], entry['id'])
            self.assertEqual(int(row[4], 16), entry['identity']['register'])
            self.assertEqual(int(row[9]), entry['width'])

    def test_synthetic_arithmetic_and_raw_preservation(self):
        entries = {entry['id']: entry for entry in self.entries}
        for name, raw_hex, expected in CASES:
            with self.subTest(candidate=name, raw=raw_hex):
                raw = bytes.fromhex(raw_hex)
                value, evidence = interpret(entries[name], raw)
                self.assertEqual(value, expected)
                self.assertEqual(evidence, raw)
        self.assertNotEqual(entries['gg01-byte14']['identity'], entries['gg01-byte19']['identity'])
        self.assertNotEqual(entries['room-manual']['identity'], entries['room-comfort']['identity'])

    def test_unsigned_ranges_byte_order_and_float_arithmetic(self):
        byte_range = re.search(r'Unsigned-byte representation has range (\d+)\.\.(\d+)', self.document)
        word_range = re.search(r'unsigned u16 has\s+range (\d+)\.\.(\d+)', self.document)
        self.assertIsNotNone(byte_range)
        self.assertIsNotNone(word_range)
        self.assertEqual(tuple(map(int, byte_range.groups())), (0, 255))
        self.assertEqual(tuple(map(int, word_range.groups())), (0, 65535))
        for entry in self.entries:
            codec = entry['codec']
            probes = {
                'u8': ((b'\x00', 0), (b'\xff', 255)),
                'u16': ((b'\x00\x00', 0), (b'\xff\xff', 65535),
                        (b'\x00\x01', 256), (b'\x01\x01', 257)),
                'binary32': ((b'\x00\x00\x80\x3f', 1.0),
                             (b'\x00\x00\x80\xbf', -1.0),
                             (b'\x00\x00\x00\x3f', 0.5)),
            }[codec]
            for raw, expected in probes:
                with self.subTest(candidate=entry['id'], raw=raw):
                    self.assertEqual(interpret(entry, raw), (expected, raw))

    def test_each_identity_axis_independently_with_valid_control(self):
        alternatives = dict(opcode=6, group=127, instance=0, register=0x011B,
                            family='other-family', direction=None, role='other-role')
        for entry in self.entries:
            identity = entry['identity']
            control = candidates(self.entries, identity)
            expected_ids = ['zone-u8', 'zone-u16'] if entry['id'].startswith('zone-') else [entry['id']]
            self.assertEqual([row['id'] for row in control], expected_ids)
            for axis in AXES:
                changes = [alternatives[axis]]
                if axis == 'direction':
                    changes += ['write' if identity[axis] == 'read' else 'read']
                if axis == 'family':
                    changes += [None if identity[axis] else 'controller-family']
                    if entry['id'] in ('room-manual', 'room-comfort'):
                        changes += ['controller-family']
                        changes += [family for family in ('VRC720 family', 'VRC700 family')
                                    if family != identity[axis]]
                for changed in changes:
                    wrong = dict(identity, **{axis: changed})
                    with self.subTest(candidate=entry['id'], axis=axis, value=changed):
                        self.assertNotEqual(wrong, identity)
                        self.assertEqual(candidates(self.entries, wrong), [])
                missing = dict(identity)
                del missing[axis]
                with self.subTest(candidate=entry['id'], missing=axis):
                    self.assertEqual(candidates(self.entries, missing), [])

    def test_request_and_reply_lengths_never_choose_candidate(self):
        identity = self.entries[0]['identity']
        for request in (b'', bytes.fromhex('02 00 03 00 1B 00'), bytes(7)):
            for reply in (b'', b'\x01', b'\x01\x00', bytes(6)):
                with self.subTest(request=request, reply=reply):
                    matches = candidates(self.entries, identity, request, reply)
                    self.assertEqual([e['id'] for e in matches], ['zone-u8', 'zone-u16'])
                    self.assertEqual([e['grade'] for e in matches], ['Hypothesis'] * 2)
        matches = candidates(self.entries, identity)
        self.assertEqual([interpret(e, b'\x01')[0] for e in matches], [1, None])
        self.assertEqual([interpret(e, b'\x01\x00')[0] for e in matches], [None, 1])
        concrete = dict(identity, instance=0)
        self.assertEqual(candidates(self.entries, concrete, bytes(6), b'\x01\x00'), [])

    def test_short_extra_field_bytes_no_typed_claim(self):
        for entry in self.entries:
            width = entry['width']
            for length in sorted({0, width - 1, width + 1, 6}):
                raw = b'\x01' * length
                with self.subTest(candidate=entry['id'], length=length):
                    self.assertEqual(interpret(entry, raw), (None, raw))

    def test_qualification_grades_and_local_links(self):
        for text in ('**Proven (identity rule):**', '**Hypothesis (native mappings):**',
                     '**Proven (local arithmetic only):**', '**Unknown:**',
                     'uncertain freshness', 'no cache updater', 'never a wildcard',
                     'No active', 'installed support', 'persistence and wire adaptation'):
            self.assertIn(text, self.document)
        for target in re.findall(r'\]\(([^)]+)\)', self.document):
            self.assertNotIn(':', target)
            self.assertTrue((PAGE.parent / target.split('#')[0]).is_file(), target)


if __name__ == '__main__':
    unittest.main()
