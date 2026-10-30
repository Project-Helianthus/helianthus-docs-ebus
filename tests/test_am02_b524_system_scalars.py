"""Offline page-contract checks; no production interpreter or native qualification."""

import copy
import json
import math
from pathlib import Path
import re
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/am02_b524_system_scalars.md'
PACKAGE = ROOT / 'architecture/fixtures/am02_b524_system_scalars.json'

# Independent finite oracle transcribed from the bounded issue, not the package.
ROWS = [
    ('controller-720', '00', 'float32', '°C',
     '0002 0022 0023 0026 0038 0046 004B 0067 0068 0073 0095 009D 009E 009F 00A0 00EF'),
    ('controller-720', '00', 'uint16', 'min', '0004 0017 0018'),
    ('controller-720', '00', 'float32', 'K', '0029'),
    ('controller-720', '00', 'uint16', 'Unknown', '002F 0036'),
    ('controller-720', '00', 'float32', 'bar', '0039'),
    ('controller-700', '00', 'float32', '°C',
     '0002 0022 0023 0026 0038 0046 004B 0067 0068 0073 0095 009D 009E 009F 00A0'),
    ('controller-700', '00', 'uint16', 'Unknown', '0006 002F 0036'),
    ('controller-700', '00', 'uint16', 'min', '0017'),
    ('controller-700', '00', 'float32', 'K', '0029'),
    ('controller-700', '00', 'float32', 'bar', '0039'),
    ('controller-700', 'dynamic', 'uint16', 'Unknown', '0042 0043'),
]
EXPECTED = [dict(family=f, opcode=2, group=0, instance_rule=i,
                 register=int(r, 16), codec=c, unit=u, grade='Hypothesis')
            for f, i, c, u, registers in ROWS for r in registers.split()]
AXES = ('family', 'software', 'hardware', 'api_version', 'api_revision',
        'opcode', 'group', 'instance', 'register')
NON_ECHO = ('empty', 'status_only', 'short', 'header_only', 'nack_or_crc',
            'timeout', 'transport_error', 'failed', 'unknown')


class SystemScalars(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text()
        cls.package = json.loads(PACKAGE.read_text())
        blocks = re.findall(r'```python\n(.*?)\n```', cls.page, re.S)
        if len(blocks) != 1:
            raise AssertionError('exactly one executable contract required')
        namespace = {}
        exec(compile(blocks[0], str(PAGE), 'exec'), namespace)
        cls.interpret = staticmethod(namespace['interpret'])

    def call(self, ctx, reply, grade='Hypothesis'):
        return self.interpret(ctx, reply, grade, self.package['bindings'])

    def inputs(self, binding):
        context = dict(family=binding['family'], software='synthetic-software',
                       hardware='synthetic-hardware', api_version=0, api_revision=0,
                       opcode=2, group=0,
                       instance=1 if binding['instance_rule'] == 'dynamic' else 0,
                       register=binding['register'])
        raw = bytes.fromhex('0000c03f' if binding['codec'] == 'float32' else '3412')
        return context, dict(kind='echo_payload', group=0,
                             register=binding['register'], value=bytearray(raw))

    def retained(self, result, context, reply, grade):
        self.assertEqual(set(result), {'context', 'reply', 'raw', 'codec_grade',
                                      'value', 'grade', 'unit', 'outcome'})
        self.assertEqual(result['context'], context)
        self.assertEqual(result['reply'], reply)
        self.assertEqual(result['raw'], reply.get('value'))
        self.assertEqual(result['codec_grade'], grade)

    def raw_only(self, context, reply, grade='Hypothesis'):
        result = self.call(context, reply, grade)
        self.retained(result, context, reply, grade)
        self.assertEqual((result['value'], result['grade'], result['outcome']),
                         (None, 'Unknown', 'raw-only'))
        return result

    def candidate(self, context, reply, expected, unit, grade='Hypothesis'):
        result = self.call(context, reply, grade)
        self.retained(result, context, reply, grade)
        self.assertEqual((result['value'], result['grade'], result['unit'], result['outcome']),
                         (expected, 'Hypothesis', unit, 'candidate'))
        return result

    def test_finite_set_and_page_table(self):
        self.assertEqual(len(EXPECTED), 46)
        self.assertEqual(self.package['bindings'], EXPECTED)
        section = self.page.split('## Finite candidates\n')[1].split('## Input and output contract\n')[0]
        rows = [line for line in section.splitlines() if line.startswith('|')]
        self.assertEqual(rows, [
            '| Family | II rule | Codec | Declared unit | Registers |',
            '| --- | --- | --- | --- | --- |',
        ] + [f'| {f} | {i} | {c} | {u} | {r} |' for f, i, c, u, r in ROWS])
        self.assertEqual(self.package['provenance'], 'synthetic; no device observation')
        self.assertEqual(self.package['variant'], 'B524')
        self.assertEqual(self.package['direction'], 'normalized reply')
        self.assertEqual(self.package['software_contract_grade'], 'Proven')
        self.assertEqual(self.package['candidate_grade'], 'Hypothesis')
        self.assertEqual(self.package['native'], dict.fromkeys(
            ('physical_support', 'presence', 'freshness', 'effects', 'persistence',
             'delivery', 'execution'), 'Unknown'))
        self.assertEqual(self.package['non_echo_kinds'], list(NON_ECHO))

    def test_package_controls_match_independent_page_cases(self):
        self.assertEqual(self.package['controls'], {
            'float32': [{'value_hex': '0000c03f', 'value': 1.5},
                        {'value_hex': '000080bf', 'value': -1},
                        {'value_hex': '0000807f', 'value': None}],
            'uint16': [{'value_hex': '3412', 'value': 4660},
                       {'value_hex': 'ffff', 'value': 65535}],
            'raw_only': ['width_minus_one', 'width_plus_one', 'unlisted_neighbor',
                         'opcode_06', 'unknown_family', 'fixed_ii_01',
                         'changed_returned_group', 'changed_returned_register',
                         'non_echo_kind', 'unknown_grade', 'missing_grade',
                         'malformed', 'partial', 'extra'],
            'candidate': ['fixed_ii_00', 'dynamic_ii_00', 'dynamic_ii_01',
                          'hypothesis_request', 'proven_request_capped',
                          'context_only_change'],
            'ownership': ['input_mutation', 'returned_mutation'],
            'unknown_unit': 'Unknown',
        })
        for binding in EXPECTED:
            ctx, reply = self.inputs(binding)
            for vector in self.package['controls'][binding['codec']]:
                reply['value'] = bytearray.fromhex(vector['value_hex'])
                if vector['value'] is None:
                    self.raw_only(ctx, reply)
                else:
                    self.candidate(ctx, reply, vector['value'], binding['unit'])

    def test_each_package_example_is_independently_expected(self):
        self.assertEqual(len(self.package['examples']), len(EXPECTED))
        for binding, example in zip(EXPECTED, self.package['examples']):
            with self.subTest(binding=binding):
                ctx, reply = self.inputs(binding)
                self.assertEqual(example['context'], ctx)
                self.assertEqual(example['reply'], dict(kind='echo_payload', group=0,
                                 register=ctx['register'], value_hex=reply['value'].hex()))
                number = 1.5 if binding['codec'] == 'float32' else 4660
                self.assertEqual(example['expected'], dict(value=number,
                                 grade='Hypothesis', unit=binding['unit']))
                self.assertEqual(example['codec_grade'], 'Hypothesis')
                self.candidate(ctx, reply, number, binding['unit'])

    def test_independent_numeric_vectors_for_every_binding(self):
        # Known constants plus struct and integer arithmetic, not interpreter output.
        self.assertEqual(struct.unpack('<f', bytes.fromhex('0000c03f'))[0], 1.5)
        self.assertEqual(struct.unpack('<f', bytes.fromhex('000080bf'))[0], -1)
        self.assertEqual(0x34 + 256 * 0x12, 4660)
        self.assertEqual(255 + 256 * 255, 65535)
        for binding in EXPECTED:
            ctx, reply = self.inputs(binding)
            vectors = [('0000c03f', 1.5), ('000080bf', -1), ('00000000', 0)] if binding['codec'] == 'float32' else [('3412', 4660), ('ffff', 65535), ('0000', 0)]
            for raw, number in vectors:
                with self.subTest(binding=binding, raw=raw):
                    reply['value'] = bytearray.fromhex(raw)
                    self.candidate(ctx, reply, number, binding['unit'])
            if binding['codec'] == 'float32':
                for octets in ((0x00, 0x00, 0x80, 0x7F),
                               (0x00, 0x00, 0x80, 0xFF),
                               (0x00, 0x00, 0xC0, 0x7F)):
                    raw = bytes(octets)
                    self.assertFalse(math.isfinite(struct.unpack('<f', raw)[0]))
                    reply['value'] = bytearray(raw)
                    self.assertEqual(self.raw_only(ctx, reply)['unit'], binding['unit'])

    def test_every_context_axis_independently_for_every_binding(self):
        for binding in EXPECTED:
            ctx, reply = self.inputs(binding)
            number = 1.5 if binding['codec'] == 'float32' else 4660
            # Opaque context is independent; valid changes cannot be dropped or normalized.
            for axis in ('software', 'hardware', 'api_version', 'api_revision'):
                for value in ('synthetic-other', 0, 1):
                    with self.subTest(binding=binding, axis=axis, value=value):
                        changed = dict(ctx, **{axis: value})
                        self.candidate(changed, reply, number, binding['unit'])
            for axis, value in (('family', 'unknown-family'), ('opcode', 6),
                                ('group', 1), ('register', 0)):
                with self.subTest(binding=binding, axis=axis):
                    self.raw_only(dict(ctx, **{axis: value}), reply)
            # Request group change with a matching echo isolates selector admission.
            self.raw_only(dict(ctx, group=1), dict(reply, group=1))
            # Change only family. A listed tuple in the other family is allowed;
            # otherwise reject rather than borrow the original candidate.
            other = 'controller-700' if ctx['family'] == 'controller-720' else 'controller-720'
            alternate = next((b for b in EXPECTED if b['family'] == other and
                              b['register'] == ctx['register'] and
                              (b['instance_rule'] == 'dynamic' or ctx['instance'] == 0)), None)
            changed = dict(ctx, family=other)
            if alternate:
                self.candidate(changed, reply, number, alternate['unit'])
            else:
                self.raw_only(changed, reply)
            for instance in (0, 1, 255):
                changed = dict(ctx, instance=instance)
                if binding['instance_rule'] == 'dynamic' or instance == 0:
                    self.candidate(changed, reply, number, binding['unit'])
                else:
                    self.raw_only(changed, reply)
            # Every context field: absence, null, malformed, extra; zero not invented.
            for axis in AXES:
                for mode in ('absent', 'null', 'malformed'):
                    with self.subTest(binding=binding, axis=axis, mode=mode):
                        changed = copy.deepcopy(ctx)
                        if mode == 'absent':
                            del changed[axis]
                        else:
                            changed[axis] = None if mode == 'null' else []
                        result = self.raw_only(changed, reply)
                        self.assertEqual(result['unit'], binding['unit'] if axis in
                                         ('software', 'hardware', 'api_version',
                                          'api_revision') else 'Unknown')
            for axis in ('variant', 'direction', 'unexpected'):
                self.assertEqual(self.raw_only(dict(ctx, **{axis: 'extra'}), reply)['unit'],
                                 binding['unit'])
            # An actual unlisted neighboring RR, independently found from oracle.
            listed = {b['register'] for b in EXPECTED if b['family'] == ctx['family']}
            neighbor = ctx['register'] + 1
            while neighbor in listed:
                neighbor += 1
            self.raw_only(dict(ctx, register=neighbor), dict(reply, register=neighbor))

    def test_reply_and_grade_axes_for_every_binding(self):
        for binding in EXPECTED:
            ctx, reply = self.inputs(binding)
            number = 1.5 if binding['codec'] == 'float32' else 4660
            for kind in NON_ECHO + ('arbitrary', None):
                with self.subTest(binding=binding, kind=kind):
                    self.raw_only(ctx, dict(reply, kind=kind))
            for axis, value in (('group', 1), ('register', ctx['register'] + 1)):
                with self.subTest(binding=binding, returned_axis=axis):
                    self.raw_only(ctx, dict(reply, **{axis: value}))
            for axis in ('kind', 'group', 'register', 'value'):
                changed = dict(reply)
                del changed[axis]
                self.raw_only(ctx, changed)
                self.raw_only(ctx, dict(reply, **{axis: None}))
            for extra in ('instance', 'variant', 'direction'):
                self.raw_only(ctx, dict(reply, **{extra: 0}))
            for grade in ('Hypothesis', 'Proven'):
                self.candidate(ctx, reply, number, binding['unit'], grade)
            for grade in ('Unknown', None, '', 'stronger', 0):
                self.raw_only(ctx, reply, grade)
            absent = self.interpret(ctx, reply, bindings=self.package['bindings'])
            self.assertIsNone(absent['value'])
            for raw in (reply['value'][:-1], reply['value'] + b'\x00', b'',
                        b'\x00', b'\xff', '3412', [52, 18]):
                self.raw_only(ctx, dict(reply, value=raw))
            # Same length can never select a codec for an unlisted selector.
            self.raw_only(dict(ctx, register=65535), dict(reply, register=65535))

    def test_malformed_domains_for_every_binding(self):
        for binding in EXPECTED:
            ctx, reply = self.inputs(binding)
            for axis, maximum in (('opcode', 255), ('group', 255),
                                  ('instance', 255), ('register', 65535)):
                for value in (-1, maximum + 1, True, '00', 0.0):
                    self.assertEqual(self.raw_only(dict(ctx, **{axis: value}), reply)['unit'],
                                     'Unknown')
            for axis, maximum in (('group', 255), ('register', 65535)):
                for value in (-1, maximum + 1, False, '00', 0.0):
                    self.raw_only(ctx, dict(reply, **{axis: value}))
            for axis in ('software', 'hardware', 'api_version', 'api_revision'):
                for value in ('', -1, False, 0.0):
                    self.assertEqual(self.raw_only(dict(ctx, **{axis: value}), reply)['unit'],
                                     binding['unit'])

    def test_owned_memory_for_every_binding_and_partial_result(self):
        for binding in EXPECTED:
            for kind in ('echo_payload', 'status_only'):
                ctx, reply = self.inputs(binding)
                reply['kind'] = kind
                original = copy.deepcopy(reply)
                result = self.call(ctx, reply)
                ctx['software'] = 'mutated-input'
                reply['value'][0] ^= 255
                self.assertEqual(result['context']['software'], 'synthetic-software')
                self.assertEqual(result['raw'], original['value'])
                self.assertEqual(result['reply'], original)
                result['raw'][0] ^= 127
                self.assertEqual(result['reply'], original)
                result['reply']['value'][1] ^= 127
                self.assertNotEqual(reply['value'], result['reply']['value'])
                fresh_ctx, fresh_reply = self.inputs(binding)
                fresh = self.call(fresh_ctx, fresh_reply)
                self.assertEqual(fresh['raw'], original['value'])
                self.assertEqual(fresh_reply['value'], original['value'])
            ctx, reply = self.inputs(binding)
            ctx['extra'] = {'nested': [0]}
            result = self.raw_only(ctx, reply)
            ctx['extra']['nested'][0] = 1
            self.assertEqual(result['context']['extra'], {'nested': [0]})

    def test_page_controls_and_limits(self):
        # Exact expected controls independently bind prose examples to tested cases.
        cases = self.page.split('## Synthetic controls and limits\n')[1]
        rows = [line for line in cases.splitlines() if line.startswith('|')]
        self.assertEqual(rows, [
            '| Case | Input | Expected |', '| --- | --- | --- |',
            '| float positive | 00 00 C0 3F | 1.5; Hypothesis; declared unit |',
            '| float negative | 00 00 80 BF | -1; Hypothesis; declared unit |',
            '| float nonfinite | 00 00 80 7F (bits 7F800000 LE) | raw-only |',
            '| uint16 positive | 34 12 | 4660; Hypothesis; declared unit |',
            '| uint16 maximum | FF FF | 65535; Hypothesis; no sentinel inference |',
            '| width minus/plus one | truncated or extra byte | raw-only |',
            '| unlisted neighbor | nearest unlisted RR | raw-only |',
            '| different operation | OP06, other inputs valid | raw-only |',
            '| unknown family | otherwise valid selector | raw-only |',
            '| fixed instance | II00 versus II01 | candidate versus raw-only |',
            '| dynamic instance | concrete II00 versus II01 | both candidate; II retained |',
            '| changed echo | different returned GG or RR | raw-only |',
            '| non-echo kind | empty, status_only, short, header_only, nack_or_crc, timeout, transport_error, failed, unknown | raw-only, even at valid width |',
            '| grade | Hypothesis or Proven request | Hypothesis output |',
            '| unknown grade | Unknown, null, absent request or other label | raw-only |',
            '| memory | mutate input or returned storage | independent snapshots |',
            '| context-only change | software, hardware, API version or API revision | unchanged arithmetic; changed context retained |',
            '| partial/malformed/extra | absent or null context, invalid domains or extra key | raw-only; supplied fields retained |',
        ])
        for text in (
            'Physical support,\npresence, freshness, effects, persistence, delivery and execution are **Unknown**.',
            'II is request context, never\nan echoed value.',
            'Do not choose by width, name, another family or a fallback.',
            'Unknown, missing or unrecognized codec grade is raw-only.',
            'OP06 is a distinct namespace', 'never\nqualified device identity',
            'No route, poll, writer, profile change, cached-value replacement, bounds import',
            'Preserve partial last-known-good state and\nfail-closed admission',
            'MCP compatibility and GraphQL parity remain required',
            'nothing is stable before Helianthus 1.0',
        ):
            self.assertIn(text, self.page)

    def test_relative_links(self):
        links = re.findall(r'\]\(([^)]+)\)', self.page)
        self.assertGreater(len(links), 0)
        for link in links:
            self.assertNotIn('://', link)
            self.assertTrue((PAGE.parent / link.split('#', 1)[0]).is_file(), link)


if __name__ == '__main__':
    unittest.main()
