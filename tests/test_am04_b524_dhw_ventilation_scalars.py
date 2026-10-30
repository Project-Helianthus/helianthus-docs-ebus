"""Offline conformance checks for the executable architecture example, not AM03."""
from copy import deepcopy
import json
import math
from pathlib import Path
import re
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/am04_b524_dhw_ventilation_scalars.md'
FIXTURE = ROOT / 'architecture/fixtures/am04_b524_dhw_ventilation_scalars.json'
# Independent finite oracle; never derived from the example's binding dictionary.
EXPECTED = {
    ('controller-720', 2, 1, 0, 4): ('float32', '°C'),
    ('controller-720', 2, 1, 0, 5): ('float32', '°C'),
    ('controller-720', 2, 9, 0, 13): ('uint16', 'Unknown'),
    ('controller-720', 2, 9, 0, 14): ('uint16', 'Unknown'),
    ('controller-700', 2, 1, 0, 4): ('float32', '°C'),
    ('controller-700', 2, 1, 0, 5): ('float32', '°C'),
}
KEY = ('family', 'opcode', 'group', 'instance', 'register')
CONTEXT = ('family', 'software', 'hardware', 'api_version', 'api_revision',
           'opcode', 'group', 'instance', 'register')
NON_ECHO = ('empty', 'status_only', 'short', 'header_only', 'nack', 'timeout',
            'transport_error', 'decode_failed', 'mismatched', 'unrecognized')


class ScalarContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text()
        blocks = re.findall(r'```python\n(.*?)\n```', cls.page, re.S)
        if len(blocks) != 1:
            raise AssertionError('exactly one executable contract required')
        cls.namespace = {}
        exec(compile(blocks[0], str(PAGE), 'exec'), cls.namespace)
        cls.package = json.loads(FIXTURE.read_text())

    def inputs(self, row):
        context = deepcopy(row['context'])
        reply = deepcopy(row['examples'][0]['reply'])
        reply['value_bytes'] = bytearray.fromhex(reply.pop('value_hex'))
        return context, reply

    def check(self, context, reply, grade='Hypothesis', expected=None, unit=None):
        before_context, before_reply = deepcopy(context), deepcopy(reply)
        result = self.namespace['interpret'](context, reply, grade)
        self.assertEqual(context, before_context)
        self.assertEqual(reply, before_reply)
        self.assertEqual(result['context'], before_context)
        self.assertEqual(result['reply'], {k: v for k, v in before_reply.items()
                                           if k != 'value_bytes'})
        self.assertEqual(result['raw'], before_reply.get('value_bytes'))
        self.assertEqual(result['codec_grade'], grade)
        self.assertEqual(result['value'], expected)
        self.assertEqual(result['value_grade'], 'Unknown' if expected is None else 'Hypothesis')
        if unit is not None:
            self.assertEqual(result['declared_unit'], unit)
            self.assertEqual(result['unit_grade'], 'Unknown' if unit == 'Unknown' else 'Hypothesis')
        else:
            self.assertEqual(result['declared_unit'], 'Unknown')
            self.assertEqual(result['unit_grade'], 'Unknown')
        return result

    def test_complete_table_and_fixture(self):
        parsed = {}
        for line in self.page.splitlines():
            if not line.startswith('| controller-'):
                continue
            family, op, group, ii, rr, codec, unit, grade = [x.strip() for x in line.strip('|').split('|')]
            key = (family, int(op, 16), int(group, 16), int(ii, 16), int(rr, 16))
            self.assertNotIn(key, parsed)
            self.assertEqual(grade, 'Hypothesis')
            parsed[key] = (codec.removesuffix(' LE'), unit)
        self.assertEqual(parsed, EXPECTED)
        self.assertEqual(self.namespace['BINDINGS'], EXPECTED)
        rows = self.package['bindings']
        self.assertEqual(len(rows), len(EXPECTED))
        self.assertEqual({tuple(r['context'][k] for k in KEY) for r in rows}, set(EXPECTED))
        self.assertEqual(self.package['native_support'], 'Unknown')
        for row in rows:
            key = tuple(row['context'][k] for k in KEY)
            codec, unit = EXPECTED[key]
            self.assertEqual((row['codec'], row['declared_unit']), (codec, unit))
            self.assertEqual(set(row['context']), set(CONTEXT))
            self.assertEqual(row['codec_grade'], 'Hypothesis')
            vectors = [('0000c03f', 1.5), ('000080bf', -1), ('0000807f', None)] if codec == 'float32' else [('3412', 4660), ('ffff', 65535)]
            self.assertEqual(len(row['examples']), len(vectors))
            for example, (hex_bytes, expected) in zip(row['examples'], vectors):
                with self.subTest(key=key, vector=hex_bytes):
                    self.assertEqual(example['reply'], {'kind': 'echo_payload', 'returned_group': key[2], 'returned_register': key[4], 'value_hex': hex_bytes})
                    self.assertEqual(example['value'], expected)
                    self.assertEqual(example['value_grade'], 'Unknown' if expected is None else 'Hypothesis')
                    raw = bytes.fromhex(hex_bytes)
                    # Independent arithmetic corroborates literal expectations.
                    if expected is not None:
                        number = struct.unpack('<f', raw)[0] if codec == 'float32' else sum(b << (8 * i) for i, b in enumerate(raw))
                        self.assertEqual(number, expected)
                    else:
                        self.assertFalse(math.isfinite(struct.unpack('<f', raw)[0]))
                    reply = {k: v for k, v in example['reply'].items() if k != 'value_hex'}
                    reply['value_bytes'] = raw
                    self.check(row['context'], reply, expected=expected, unit=unit)

    def test_each_context_axis_independently(self):
        for row in self.package['bindings']:
            context, reply = self.inputs(row)
            key = tuple(context[k] for k in KEY)
            codec, unit = EXPECTED[key]
            number = 1.5 if codec == 'float32' else 4660
            for axis in CONTEXT:
                for missing in (True, False):
                    with self.subTest(key=key, axis=axis, missing=missing):
                        changed = deepcopy(context)
                        if missing:
                            del changed[axis]
                        else:
                            changed[axis] = None
                        self.check(changed, reply)
                values = {'family': 'unknown-family', 'software': 'synthetic-software',
                          'hardware': 'synthetic-hardware', 'api_version': 1,
                          'api_revision': 1, 'opcode': 6, 'group': 0,
                          'instance': 1, 'register': 6 if context['group'] == 1 else 15}
                changed = dict(context, **{axis: values[axis]})
                with self.subTest(key=key, changed=axis):
                    self.check(changed, reply, expected=number if axis in CONTEXT[1:5] else None,
                               unit=unit if axis in CONTEXT[1:5] else None)
            other = 'controller-700' if context['family'] == 'controller-720' else 'controller-720'
            changed = dict(context, family=other)
            self.check(changed, reply, expected=number if codec == 'float32' else None,
                       unit=unit if codec == 'float32' else None)
            # Same width/name cannot supply another family's missing binding.
            if codec == 'uint16':
                self.check(dict(context, family='controller-700', name='ventilation'), reply)
            for axis in CONTEXT[1:5]:
                for malformed in ('', -1, False, [], {}):
                    with self.subTest(key=key, axis=axis, malformed=malformed):
                        self.check(dict(context, **{axis: malformed}), reply)
            for axis, limit in (('opcode', 255), ('group', 255), ('instance', 255), ('register', 65535)):
                for malformed in (-1, limit + 1, False, str(context[axis])):
                    self.check(dict(context, **{axis: malformed}), reply)
            for family in (None, [], 0):
                self.check(dict(context, family=family), reply)

    def test_each_reply_and_grade_axis_independently(self):
        for row in self.package['bindings']:
            context, reply = self.inputs(row)
            codec, unit = EXPECTED[tuple(context[k] for k in KEY)]
            number = 1.5 if codec == 'float32' else 4660
            for kind in NON_ECHO:
                with self.subTest(context=context, kind=kind):
                    self.check(context, dict(reply, kind=kind), unit=unit)
            for axis in ('kind', 'returned_group', 'returned_register', 'value_bytes'):
                changed = deepcopy(reply)
                del changed[axis]
                self.check(context, changed, unit=unit)
                self.check(context, dict(reply, **{axis: None}), unit=unit)
            for axis in ('returned_group', 'returned_register'):
                for value in (reply[axis] + 1, -1, False, str(reply[axis])):
                    with self.subTest(context=context, axis=axis, value=value):
                        self.check(context, dict(reply, **{axis: value}), unit=unit)
            for grade in ('Proven', 'Unknown', None, 'unrecognized'):
                with self.subTest(context=context, grade=grade):
                    self.check(context, reply, grade, expected=number if grade == 'Proven' else None, unit=unit)
            omitted = self.namespace['interpret'](context, reply)
            self.assertIsNone(omitted['value'])
            for raw in (reply['value_bytes'][:-1], reply['value_bytes'] + b'\x00',
                        b'', '3412', [52, 18], 0):
                self.check(context, dict(reply, value_bytes=raw), unit=unit)
            # Reject another listed codec's width rather than infer from width.
            alternate = b'\x34\x12' if codec == 'float32' else b'\x00\x00\xc0\x3f'
            self.check(context, dict(reply, value_bytes=alternate), unit=unit)
            if codec == 'float32':
                # Exact little-endian bytes for positive/negative infinity and NaN.
                for raw in (bytes((0, 0, 0x80, 0x7f)),
                            bytes((0, 0, 0x80, 0xff)),
                            bytes((1, 0, 0xc0, 0x7f))):
                    self.check(context, dict(reply, value_bytes=raw), unit=unit)
                # Finite, out-of-assumed-range values remain candidate numbers.
                self.check(context, dict(reply, value_bytes=struct.pack('<f', -500)), expected=-500, unit=unit)
            self.check(dict(context, extra={'items': [0]}), dict(reply, extra={'items': [0]}), expected=number, unit=unit)

    def test_owned_memory_every_binding(self):
        for row in self.package['bindings']:
            context, reply = self.inputs(row)
            context['extra'] = {'items': [0]}
            reply['extra'] = {'items': [0]}
            first = self.namespace['interpret'](context, reply, 'Hypothesis')
            second = self.namespace['interpret'](context, reply, 'Hypothesis')
            original = bytes(reply['value_bytes'])
            reply['value_bytes'][0] ^= 255
            context['extra']['items'][0] = 1
            reply['extra']['items'][0] = 1
            self.assertEqual(first['raw'], original)
            self.assertEqual(first['context']['extra']['items'], [0])
            self.assertEqual(first['reply']['extra']['items'], [0])
            first['raw'][0] ^= 127
            first['context']['extra']['items'][0] = 2
            first['reply']['extra']['items'][0] = 2
            self.assertEqual(second['raw'], original)
            self.assertEqual(second['context']['extra']['items'], [0])
            self.assertEqual(second['reply']['extra']['items'], [0])
            self.assertEqual(reply['value_bytes'][0], original[0] ^ 255)
            # Raw-only results have the same ownership requirement.
            reply['kind'] = 'status_only'
            raw_only = self.namespace['interpret'](context, reply, 'Unknown')
            saved = bytes(raw_only['raw'])
            reply['value_bytes'][0] ^= 1
            self.assertEqual(raw_only['raw'], saved)

    def test_page_semantics_and_relative_links(self):
        for phrase in ('physical support', 'presence', 'freshness', 'effects', 'persistence',
                       'delivery', 'Unknown', 'Hypothesis', 'Proven software contract',
                       'partial', 'last-known-good', 'GraphQL', 'eBUS MCP',
                       '273.15', '00 00 C0 3F', '00 00 80 BF', '00 00 80 7F',
                       '34 12', 'FF FF', '65535', '4660', 'II01',
                       *NON_ECHO[:-1]):
            self.assertIn(phrase, self.page)
        for link in re.findall(r'\]\(([^)]+)\)', self.page):
            self.assertNotIn('://', link)
            self.assertTrue((PAGE.parent / link).is_file(), link)


if __name__ == '__main__':
    unittest.main()
