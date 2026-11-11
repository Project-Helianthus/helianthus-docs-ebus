"""Offline page/fixture contract checks; reference model is not a shipped codec."""
import copy
import json
import math
from pathlib import Path
import re
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/am06-b524-circuit-scalars.md'
FIXTURE = ROOT / 'architecture/fixtures/am06_b524_circuit_scalars.json'
FIELDS = ('family', 'software', 'hardware', 'api_version', 'api_revision',
          'opcode', 'group', 'instance', 'register', 'reply_kind',
          'returned_group', 'returned_register', 'codec_grade')
# Independent finite oracle: never derive expected rows from the fixture/model.
EXPECTED_GROUPS = (
    ('controller-720', '°C', (0x07, 0x08, 0x10, 0x11, 0x12, 0x14, 0x1F)),
    ('controller-720', 'K', (0x0A, 0x0B)),
    ('controller-720', 'Unknown', (0x0F, 0x1C)),
    ('controller-720', '%', (0x1A,)),
    ('controller-700', '°C', (0x07, 0x08, 0x10, 0x11, 0x12, 0x14, 0x1F)),
    ('controller-700', 'K', (0x0A, 0x0B)),
    ('controller-700', 'Unknown', (0x0F,)),
)
EXPECTED = {(family, reg): unit for family, unit, regs in EXPECTED_GROUPS
            for reg in regs}
NON_ECHO = ('empty', 'status_only', 'short', 'header_only', 'nack_or_crc',
            'timeout', 'transport_error', 'unknown_kind')


def instance_accepts(rule, instance):
    return (type(instance) is int and 0 <= instance <= 255
            and (rule == 'dynamic' or (rule == 'fixed_00' and instance == 0)))


def scalar(codec, raw):
    if codec == 'float32_le' and len(raw) == 4:
        value = struct.unpack('<f', raw)[0]
        return value if math.isfinite(value) else None
    if codec == 'uint16_le' and len(raw) == 2:
        return int.from_bytes(raw, 'little', signed=False)
    return None


def interpret(context, raw, bindings, requested_grade='Hypothesis'):
    if not isinstance(raw, (bytes, bytearray, memoryview)):
        raise TypeError('value bytes required')
    result = dict(context=copy.deepcopy(context), raw=bytearray(raw), value=None,
                  grade=None, unit='Unknown', requested_grade=copy.deepcopy(requested_grade))
    if any(field not in context for field in FIELDS):
        return result
    for field in ('family', 'software', 'hardware'):
        if not isinstance(context[field], str) or not context[field]:
            return result
    for field, ceiling in (('api_version', None), ('api_revision', None),
                           ('opcode', 255), ('group', 255), ('instance', 255),
                           ('register', 65535), ('returned_group', 255),
                           ('returned_register', 65535)):
        value = context[field]
        if type(value) is not int or value < 0 or (ceiling is not None and value > ceiling):
            return result
    binding = next((b for b in bindings if
                    b['family'] == context['family'] and
                    b['opcode'] == context['opcode'] and
                    b['group'] == context['group'] and
                    b['register'] == context['register'] and
                    instance_accepts(b['instance_rule'], context['instance'])), None)
    if binding is None:
        return result
    result['unit'] = binding['unit']
    if context['codec_grade'] not in ('Hypothesis', 'Proven'):
        return result
    if context['reply_kind'] != 'echo_payload':
        return result
    if context['returned_group'] != context['group']:
        return result
    if context['returned_register'] != context['register']:
        return result
    value = scalar(binding['codec'], result['raw'])
    if value is not None:
        result.update(value=value, grade='Hypothesis')
    return result


class CircuitScalars(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = json.loads(FIXTURE.read_text())
        cls.bindings = cls.package['bindings']

    def context(self, family, register):
        return dict(family=family, software='synthetic-software',
                    hardware='synthetic-hardware', api_version=0, api_revision=0,
                    opcode=2, group=2, instance=0, register=register,
                    reply_kind='echo_payload', returned_group=2,
                    returned_register=register, codec_grade='Hypothesis')

    def check_result(self, context, expected, raw=None, requested='Proven'):
        if raw is None:
            # Independent binary32 construction, not a table from interpret().
            raw = bytearray((0, 0, 192, 63))
        result = interpret(context, raw, self.bindings, requested)
        self.assertEqual(result['context'], context)
        self.assertEqual(result['raw'], bytearray(raw))
        self.assertIsNot(result['raw'], raw)
        self.assertEqual(result['requested_grade'], requested)
        self.assertEqual(result['value'], expected)
        self.assertEqual(result['grade'], None if expected is None else 'Hypothesis')
        return result

    def test_complete_binding_inventory(self):
        expected = [dict(family=f, opcode=2, group=2, instance_rule='dynamic',
                         register=r, codec='float32_le', unit=u, grade='Hypothesis')
                    for (f, r), u in EXPECTED.items()]
        self.assertCountEqual(self.bindings, expected)
        self.assertEqual(len(self.bindings), 22)

    def test_page_table_and_policy(self):
        page = PAGE.read_text()
        rows = re.findall(r'^\| (controller-\d+) \| ([0-9A-F, ]+) \| ([^|]+) \|$', page, re.M)
        self.assertEqual(len(rows), len(EXPECTED_GROUPS))
        self.assertEqual([(f, u.strip(), tuple(int(x.strip(), 16) for x in regs.split(',')))
                          for f, regs, u in rows], list(EXPECTED_GROUPS))
        policy = json.loads(re.search(r'```json\n(.*?)\n```', page, re.S).group(1))
        expected = dict(context_fields=list(FIELDS), reply_kind='echo_payload',
                        grade='Hypothesis', unknown_unit='Unknown', finite_only=True,
                        exact_width=True, match_returned_group=True,
                        match_returned_register=True, own_raw=True, explicit_selection=True)
        self.assertEqual(policy, expected)
        self.assertEqual(self.package['policy'], expected)
        for phrase in ('no uint16 binding', 'no fixed\nII00 binding',
                       'do not\nclip, add 273.15', 'physical device identity',
                       'Physical support', 'last-known-good', 'eBUS MCP compatibility',
                       'GraphQL parity', 'Unknown', 'Hypothesis', 'Proven'):
            self.assertIn(phrase, page)

    def test_page_normative_controls(self):
        page = PAGE.read_text()
        normalized = ' '.join(page.split())
        for sentence in (
            'Every row below has opcode `02`, group `02`, dynamic II, codec `float32_le` and grade `Hypothesis`.',
            'II is request context, never an echoed field.',
            'The generic fixed II00 rule accepts only 00, but adds no binding here.',
            'No family fallback is allowed, including for rows shared by both families.',
            'Unknown or missing codec grade is raw-only.',
            'Only finite results qualify as candidate values: do not clip, add 273.15, or invent a sentinel.',
            '`float32_le` means exactly four little-endian IEEE binary32 bytes.',
            '`uint16_le`, where separately selected, means exactly two little-endian unsigned bytes;',
            '`34 12` is 4660 and `FF FF` is 65535 without sentinel inference.',
            'A successful result always remains `Hypothesis`, including when `requested_grade` is `Proven`;',
            'For **every** listed row, `00 00 C0 3F` gives 1.5, `00 00 80 BF` gives -1,',
            'and binary32 bits `7F800000`, materialized little-endian as `00 00 80 7F`, are non-finite and raw-only.',
            'require matching returned GG and RR;',
            'require the selected codec\'s exact width;',
            'an independent raw byte buffer',
            'A malformed byte container is an input type error',
        ):
            self.assertIn(sentence, normalized)

    def test_all_relative_links(self):
        links = re.findall(r'\]\(([^)]+)\)', PAGE.read_text())
        self.assertGreater(len(links), 0)
        for target in links:
            self.assertNotIn('://', target)
            self.assertTrue((PAGE.parent / target.split('#')[0]).is_file(), target)

    def test_package_examples_independent_numbers(self):
        controls = {'0000c03f': 1.5, '000080bf': -1.0, '0000807f': None}
        expected_keys = {(f, r, raw) for f, r in EXPECTED for raw in controls}
        keys = []
        for case in self.package['examples']:
            c = case['input']
            key = (c['family'], c['register'], case['raw_hex'])
            keys.append(key)
            self.assertIn(key, expected_keys)
            self.assertEqual(c, self.context(*key[:2]))
            self.assertEqual(case['requested_grade'], 'Proven')
            value = controls[key[2]]
            self.assertEqual(case['expected'], dict(value=value,
                             grade='Hypothesis' if value is not None else None,
                             unit=EXPECTED[key[:2]]))
            result = self.check_result(c, value, bytes.fromhex(key[2]))
            self.assertEqual(result['unit'], EXPECTED[key[:2]])
        self.assertCountEqual(keys, expected_keys)
        # Binary32 arithmetic corroborates the constants without model output.
        self.assertEqual(struct.unpack('<f', bytes((0, 0, 192, 63)))[0], 1 + 1/2)
        self.assertEqual(struct.unpack('<f', bytes((0, 0, 128, 191)))[0], -1)
        self.assertEqual(int.from_bytes(bytes((0, 0, 128, 127)), 'little'), (0x7F8 << 20))

    def test_package_edge_scenarios(self):
        expected = []
        def add(name, patch=None, absent=None, raw='0000c03f', value=None):
            expected.append(dict(name=name, patch=patch or {}, absent=absent or [],
                                 raw_hex=raw, expected_value=value))
        add('width_3', raw='0000c0')
        add('width_5', raw='0000c03f00')
        add('unlisted_neighbor', dict(register=9, returned_register=9))
        add('op06', dict(opcode=6))
        add('unknown_family', dict(family='unknown-family'))
        add('ii00', dict(instance=0), value=1.5)
        add('ii01', dict(instance=1), value=1.5)
        add('returned_gg', dict(returned_group=3))
        add('returned_rr', dict(returned_register=9))
        for kind in NON_ECHO:
            add(kind, dict(reply_kind=kind))
        for grade in ('Unknown', 'Proven'):
            add('codec_grade_' + grade, dict(codec_grade=grade),
                value=1.5 if grade == 'Proven' else None)
        for field in FIELDS:
            add('absent_' + field, absent=[field])
        for field, value in [('software', 'synthetic-other-software'),
                             ('hardware', 'synthetic-other-hardware'),
                             ('api_version', 1), ('api_revision', 1)]:
            add('changed_' + field, {field: value}, value=1.5)
        self.assertEqual(self.package['edge_scenarios'], expected)
        for family, reg in EXPECTED:
            for case in self.package['edge_scenarios']:
                with self.subTest(family=family, register=reg, scenario=case['name']):
                    c = dict(self.context(family, reg), **case['patch'])
                    for key in case['absent']:
                        del c[key]
                    self.check_result(c, case['expected_value'], bytes.fromhex(case['raw_hex']))

    def test_each_axis_for_every_binding(self):
        for family, reg in EXPECTED:
            valid = self.context(family, reg)
            other_family = 'controller-700' if family == 'controller-720' else 'controller-720'
            variants = {
                'family': (other_family, 1.5 if (other_family, reg) in EXPECTED else None),
                'software': ('synthetic-other-software', 1.5),
                'hardware': ('synthetic-other-hardware', 1.5),
                'api_version': (1, 1.5), 'api_revision': (1, 1.5),
                'opcode': (6, None), 'group': (3, None), 'instance': (1, 1.5),
                'register': (0x0009, None), 'reply_kind': ('status_only', None),
                'returned_group': (3, None), 'returned_register': (0x0009, None),
                'codec_grade': ('Unknown', None),
            }
            self.assertEqual(set(variants), set(FIELDS))
            for field, (changed, expected) in variants.items():
                with self.subTest(family=family, register=reg, axis=field):
                    context = dict(valid, **{field: changed})
                    self.assertEqual(sum(context[k] != valid[k] for k in FIELDS), 1)
                    self.check_result(context, expected)
            for field in FIELDS:
                with self.subTest(family=family, register=reg, absent=field):
                    context = valid.copy()
                    del context[field]
                    self.check_result(context, None)
                with self.subTest(family=family, register=reg, null=field):
                    self.check_result(dict(valid, **{field: None}), None)

    def test_every_binding_failure_shapes_and_grades(self):
        for family, reg in EXPECTED:
            context = self.context(family, reg)
            for size in (0, 1, 2, 3, 5):
                with self.subTest(family=family, register=reg, size=size):
                    self.check_result(context, None, bytearray(size))
            for kind in NON_ECHO:
                with self.subTest(family=family, register=reg, kind=kind):
                    # Valid four-byte tail must not override normalized reply kind.
                    self.check_result(dict(context, reply_kind=kind), None)
            for grade in ('Unknown', '', 'unknown'):
                self.check_result(dict(context, codec_grade=grade), None)
            self.check_result(dict(context, codec_grade='Proven'), 1.5)
            for request in ('Unknown', 'Hypothesis', 'Proven', None):
                self.check_result(context, 1.5, requested=request)
            for bits in ((0x7F8 << 20), (0xFF8 << 20), (0x7FC << 20)):
                self.check_result(context, None, bits.to_bytes(4, 'little'))
            self.check_result(dict(context, family='unknown-family'), None)
            # Neighbor is unlisted for both families; alter request and echo together.
            self.check_result(dict(context, register=9, returned_register=9), None)
            self.check_result(dict(context, opcode=6), None)

    def test_malformed_context_every_binding(self):
        for family, reg in EXPECTED:
            valid = self.context(family, reg)
            bad = {'family': ('', 0), 'software': ('', 0), 'hardware': ('', 0),
                   'api_version': (-1, False, '0'), 'api_revision': (-1, False, '0'),
                   'opcode': (-1, 256, False, '2'), 'group': (-1, 256, False, '2'),
                   'instance': (-1, 256, False, '0'),
                   'register': (-1, 65536, False, '7'),
                   'returned_group': (-1, 256, False, '2'),
                   'returned_register': (-1, 65536, False, '7'),
                   'reply_kind': ('', 0), 'codec_grade': ('', 0)}
            for field, values in bad.items():
                for value in values:
                    with self.subTest(family=family, register=reg, field=field, value=value):
                        self.check_result(dict(valid, **{field: value}), None)
            for instance in (0, 1, 255):
                self.check_result(dict(valid, instance=instance), 1.5)

    def test_every_binding_raw_and_context_ownership(self):
        for family, reg in EXPECTED:
            for kind in ('echo_payload', 'status_only'):
                c = dict(self.context(family, reg), reply_kind=kind,
                         extra={'items': [0]})
                raw = bytearray((0, 0, 192, 63))
                snapshot = copy.deepcopy(c)
                result = self.check_result(c, 1.5 if kind == 'echo_payload' else None, raw)
                raw[0] = 99
                c['extra']['items'][0] = 99
                self.assertEqual(result['raw'], bytearray((0, 0, 192, 63)))
                self.assertEqual(result['context'], snapshot)
                result['raw'][1] = 77
                result['context']['extra']['items'].append(1)
                self.assertEqual(raw, bytearray((99, 0, 192, 63)))
                self.assertEqual(c['extra']['items'], [99])
                second = interpret(snapshot, bytes((0, 0, 192, 63)), self.bindings)
                self.assertEqual(second['raw'], bytearray((0, 0, 192, 63)))
                self.assertEqual(second['context'], snapshot)
            c = self.context(family, reg)
            source = bytearray((0, 0, 192, 63))
            result = self.check_result(c, 1.5, memoryview(source))
            source[0] = 99
            self.assertEqual(result['raw'], bytearray((0, 0, 192, 63)))

    def test_unknown_units_and_no_width_fallback(self):
        for family, reg in EXPECTED:
            c = self.context(family, reg)
            for raw in (bytes((0, 0, 192, 63)), bytes((0, 0, 128, 127))):
                result = interpret(c, raw, self.bindings)
                self.assertEqual(result['unit'], EXPECTED[(family, reg)])
            for raw in (bytes((0x34, 0x12)), bytes((255, 255))):
                self.check_result(c, None, raw)
            # No fallback into a listed family, or codec choice from value width.
            result = self.check_result(dict(c, family='unknown-family'), None)
            self.assertEqual(result['unit'], 'Unknown')

    def test_generic_representation_and_instance_rule_only(self):
        self.assertEqual(scalar('uint16_le', bytes((0x34, 0x12))), 0x12 * 256 + 0x34)
        self.assertEqual(scalar('uint16_le', bytes((255, 255))), (1 << 16) - 1)
        for size in (0, 1, 3, 4):
            self.assertIsNone(scalar('uint16_le', bytes(size)))
        for size in (2, 4):
            self.assertIsNone(scalar('unknown', bytes(size)))
        self.assertTrue(instance_accepts('fixed_00', 0))
        for value in (1, 255, -1, 256, False, None, '0'):
            self.assertFalse(instance_accepts('fixed_00', value))
        self.assertFalse(instance_accepts('unknown', 0))
        self.assertTrue(all(b['codec'] == 'float32_le' and b['instance_rule'] == 'dynamic'
                            for b in self.bindings))

    def test_malformed_byte_container(self):
        for raw in (None, '0000c03f', [0, 0, 192, 63], 4):
            with self.assertRaises(TypeError):
                interpret(self.context('controller-720', 7), raw, self.bindings)


if __name__ == '__main__':
    unittest.main()
