"""Synthetic representation oracle; does not exercise companion code."""
from collections.abc import Mapping
import copy
import json
import math
from pathlib import Path
import re
import struct
import unittest

ab44_root = Path(__file__).resolve().parents[1]
ab44_fields = ['family', 'software', 'hardware',
               'api_version', 'api_revision', 'op',
               'gg', 'ii', 'rr']
ab44_context = dict(zip(ab44_fields, ['synthetic-controller-family',
    'synthetic-software-a', 'synthetic-hardware-a', 1, 1, 1, 2, 1, 2]))
ab44_uin = [2, 2, 0, 0, 0, 4, 0, 1, 0]
ab44_exp = [2, 2, 0, 0, 0, 160, 193, 0, 0, 160, 65, 0, 0, 128, 63]


def ab44_build(ab44_ctx):
    if not isinstance(ab44_ctx, Mapping) or set(ab44_ctx) != set(ab44_fields) or any(
            ab44_ctx[ab44_key] is None for ab44_key in ab44_fields):
        return {'request': None, 'reason': 'context'}
    if type(ab44_ctx['op']) is not int or ab44_ctx['op'] not in (1, 7):
        return {'request': None, 'reason': 'op'}
    for ab44_field, ab44_max in (('gg', 255), ('ii', 255),
                                  ('rr', 65535)):
        if type(ab44_ctx[ab44_field]) is not int or not 0 <= ab44_ctx[ab44_field] <= ab44_max:
            return {'request': None, 'reason': ab44_field}
    return {'request': [ab44_ctx['op'], ab44_ctx['gg'], ab44_ctx['ii'],
            ab44_ctx['rr'] & 255, ab44_ctx['rr'] >> 8], 'reason': None}


def ab44_decode(ab44_ctx, ab44_codec, ab44_width, ab44_grade, ab44_raw):
    ab44_byte_container = isinstance(ab44_raw, (list, tuple, bytes, bytearray))
    ab44_result = {'context': copy.deepcopy(ab44_ctx),
                   'raw': list(ab44_raw) if ab44_byte_container else copy.deepcopy(ab44_raw),
                   'header': None, 'spans': None,
                   'limits': None, 'reason': None,
                   'grade': ab44_grade}
    def ab44_fail(ab44_reason):
        ab44_result['reason'] = ab44_reason
        return ab44_result
    if not ab44_byte_container:
        return ab44_fail('bytes')
    ab44_raw = ab44_result['raw']
    if len(ab44_raw) >= 3 and all(type(ab44_byte) is int and 0 <= ab44_byte <= 255
                                  for ab44_byte in ab44_raw[:3]):
        ab44_result['header'] = list(ab44_raw[:3])
    if not isinstance(ab44_width, int) or isinstance(ab44_width, bool) or ab44_width <= 0:
        return ab44_fail('width')
    if any(type(ab44_byte) is not int or not 0 <= ab44_byte <= 255
           for ab44_byte in ab44_raw):
        return ab44_fail('bytes')
    if len(ab44_raw) != 3 + 3 * ab44_width:
        return ab44_fail('length')
    ab44_result['spans'] = [ab44_raw[3 + ab44_index * ab44_width:
        3 + (ab44_index + 1) * ab44_width] for ab44_index in range(3)]
    if ab44_build(ab44_ctx)['request'] is None:
        return ab44_fail('context')
    if ab44_raw[:3] != [ab44_ctx['gg'], ab44_ctx['rr'] & 255,
                          ab44_ctx['rr'] >> 8]:
        return ab44_fail('echo')
    if ab44_codec not in ('UCH', 'UIN', 'EXP', 'date/time'):
        return ab44_fail('codec')
    if ab44_width != {'UCH': 1, 'UIN': 2, 'EXP': 4, 'date/time': 3}[ab44_codec]:
        return ab44_fail('codec_width')
    if ab44_grade not in ('Hypothesis', 'Proven'):
        return ab44_fail('grade')
    if ab44_codec == 'date/time':
        return ab44_fail('date_step_unknown')
    ab44_values = [struct.unpack('<f', bytes(ab44_span))[0]
        if ab44_codec == 'EXP' else int.from_bytes(bytes(ab44_span), 'little')
        for ab44_span in ab44_result['spans']]
    if not all(math.isfinite(ab44_value) for ab44_value in ab44_values):
        return ab44_fail('nonfinite')
    if ab44_values[0] > ab44_values[1]:
        return ab44_fail('reversed')
    if ab44_values[2] < 0:
        return ab44_fail('negative_step')
    ab44_result['limits'] = ab44_values
    return ab44_result


class Ab44ContractTests(unittest.TestCase):
    def test_ab44_admitted_raw_containers(self):
        for ab44_container in (list, tuple, bytes, bytearray):
            with self.subTest(ab44_container=ab44_container.__name__):
                ab44_result = ab44_decode(ab44_context, 'UIN', 2, 'Hypothesis',
                                          ab44_container(ab44_uin))
                self.assertEqual(ab44_result, {
                    'context': ab44_context, 'raw': ab44_uin,
                    'header': [2, 2, 0],
                    'spans': [[0, 0], [4, 0], [1, 0]],
                    'limits': [0, 4, 1], 'reason': None,
                    'grade': 'Hypothesis'})
                for ab44_value in (ab44_result['raw'],
                        ab44_result['header'], ab44_result['spans'],
                        *ab44_result['spans']):
                    self.assertIs(type(ab44_value), list)

    def test_ab44_malformed_raw_containers(self):
        for ab44_raw in (None, 1, 1.5, True, 'bytes', {}, {'byte': 2}):
            with self.subTest(ab44_raw=ab44_raw):
                ab44_result = ab44_decode(ab44_context, 'UIN', 2, 'Hypothesis', ab44_raw)
                self.assertEqual(ab44_result['reason'], 'bytes')
                self.assertEqual(ab44_result['raw'], ab44_raw)
                self.assertIs(type(ab44_result['raw']), type(ab44_raw))
                self.assertEqual(ab44_result['context'], ab44_context)
                self.assertIsNone(ab44_result['header'])
                self.assertIsNone(ab44_result['spans'])
                self.assertIsNone(ab44_result['limits'])

    def test_ab44_malformed_context_containers(self):
        for ab44_ctx in (None, 1, 1.5, True, 'context', [], ab44_fields):
            with self.subTest(ab44_ctx=ab44_ctx):
                self.assertEqual(ab44_build(ab44_ctx),
                    {'request': None, 'reason': 'context'})
                ab44_result = ab44_decode(ab44_ctx, 'UIN', 2, 'Hypothesis', ab44_uin)
                self.assertEqual(ab44_result['reason'], 'context')
                self.assertEqual(ab44_result['context'], ab44_ctx)
                self.assertEqual(ab44_result['raw'], ab44_uin)
                self.assertEqual(ab44_result['header'], [2, 2, 0])
                self.assertEqual(ab44_result['spans'], [[0, 0], [4, 0], [1, 0]])
                self.assertIsNone(ab44_result['limits'])

    def test_ab44_page_contract(self):
        ab44_page = (ab44_root / 'architecture/al10-b524-description-spans.md').read_text()
        ab44_policy = json.loads(re.search(r'```json\n(.*?)\n```', ab44_page, re.S)[1])
        self.assertEqual(ab44_policy, {
            'request_ops': [1, 7], 'metadata_ops': {'1': 2, '7': 6},
            'context_fields': ab44_fields,
            'reply_header': ['GG', 'RRlo', 'RRhi'], 'span_count': 3,
            'length': '3+3w', 'infer_codec': False,
            'echo': ['GG', 'RRlo', 'RRhi'], 'ii_echo': False,
            'typed_grades': ['Hypothesis', 'Proven'],
            'codecs': {'UCH': 1, 'UIN': 2, 'EXP': 4, 'date/time': 3},
            'nonfinite_valid': False, 'reversed_valid': False,
            'negative_step_valid': False, 'zero_step': 'literal zero',
            'date_numeric_permission': False,
            'presence_authority': False, 'write_authority': False})
        for ab44_clause in ('B524BuildDescription(context)',
                'B524DecodeDescription(context, explicitCodec, explicitWidth, grade, raw)',
                'II remains request context and is never an\necho.',
                'length never selects a codec.', 'Step zero means literal zero,',
                'OP01 corresponds only to OP02 local metadata; OP07 only to OP06 remote',
                'Grade and implementation-valid state are independent.',
                'its step meaning is Unknown and supplies no numeric edit validation.'):
            with self.subTest(ab44_clause=ab44_clause):
                self.assertIn(ab44_clause, ab44_page)

    def test_ab44_fixture_independent_expectations(self):
        ab44_data = json.loads((ab44_root /
            'architecture/fixtures/al10_b524_description_spans.json').read_text())
        ab44_expected = [
            ('uin', 'UIN', 2, ab44_uin, [0, 4, 1], None),
            ('wrong_pair', 'EXP', 4, ab44_uin, None, 'length'),
            ('exp', 'EXP', 4, ab44_exp, [-20, 20, 1], None),
            ('date', 'date/time', 3, [2, 2, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                None, 'date_step_unknown')]
        self.assertEqual(set(ab44_data), {'examples'})
        self.assertEqual(len(ab44_data['examples']), 4)
        for ab44_case, ab44_want in zip(ab44_data['examples'], ab44_expected):
            with self.subTest(ab44_name=ab44_want[0]):
                self.assertEqual(ab44_case, dict(zip([
                    'name', 'codec', 'width', 'raw',
                    'expected_limits', 'expected_reason'], ab44_want),
                    context=ab44_context, grade='Hypothesis'))
                ab44_result = ab44_decode(ab44_case['context'],
                    ab44_case['codec'], ab44_case['width'],
                    ab44_case['grade'], ab44_case['raw'])
                self.assertEqual(ab44_result['limits'], ab44_want[4])
                self.assertEqual(ab44_result['reason'], ab44_want[5])
                self.assertEqual(ab44_result['raw'], ab44_want[3])

    def test_ab44_identity_axes(self):
        self.assertEqual(ab44_build(ab44_context),
                         {'request': [1, 2, 1, 2, 0], 'reason': None})
        ab44_variants = [('family', 'synthetic-controller-family-b'),
            ('software', 'synthetic-software-b'),
            ('hardware', 'synthetic-hardware-b'), ('api_version', 2),
            ('api_revision', 2), ('op', 7), ('gg', 3),
            ('ii', 2), ('rr', 3), ('rr', 258)]
        ab44_identities = set()
        for ab44_field, ab44_value in ab44_variants:
            with self.subTest(ab44_field=ab44_field, ab44_value=ab44_value):
                ab44_ctx = dict(ab44_context, **{ab44_field: ab44_value})
                ab44_raw = [ab44_ctx['gg'], ab44_ctx['rr'] & 255,
                            ab44_ctx['rr'] >> 8] + ab44_exp[3:]
                ab44_result = ab44_decode(ab44_ctx, 'EXP', 4, 'Hypothesis', ab44_raw)
                self.assertEqual(ab44_result['context'], ab44_ctx)
                self.assertEqual(ab44_result['limits'], [-20, 20, 1])
                self.assertNotEqual(ab44_result['context'], ab44_context)
                ab44_identities.add(tuple(ab44_result['context'].items()))
                self.assertIsNone(ab44_build(ab44_ctx)['reason'])
                self.assertEqual(ab44_build(ab44_ctx)['request'], [ab44_ctx['op'],
                    ab44_raw[0], ab44_ctx['ii'], ab44_raw[1], ab44_raw[2]])
        self.assertEqual(len(ab44_identities), 10)
        for ab44_field in ab44_fields:
            ab44_ctx = dict(ab44_context)
            del ab44_ctx[ab44_field]
            self.assertEqual(ab44_build(ab44_ctx),
                {'request': None, 'reason': 'context'})
            ab44_ctx[ab44_field] = None
            self.assertEqual(ab44_build(ab44_ctx),
                {'request': None, 'reason': 'context'})
        for ab44_op in (0, 2, 6, 8, True, False, 1.0, '1'):
            self.assertEqual(ab44_build(dict(ab44_context, op=ab44_op)),
                {'request': None, 'reason': 'op'})
            self.assertEqual(ab44_decode(dict(ab44_context, op=ab44_op),
                'EXP', 4, 'Hypothesis', ab44_exp)['reason'], 'context')

    def test_ab44_build_selector_boundaries(self):
        self.assertEqual(ab44_build(dict(ab44_context, extra=1)),
            {'request': None, 'reason': 'context'})
        for ab44_field, ab44_max, ab44_index in (
                ('gg', 255, 1), ('ii', 255, 2), ('rr', 65535, 3)):
            for ab44_value in (-1, ab44_max + 1, True, False, 1.0, '1'):
                with self.subTest(ab44_field=ab44_field, ab44_value=ab44_value):
                    self.assertEqual(ab44_build(dict(ab44_context, **{ab44_field: ab44_value})),
                        {'request': None, 'reason': ab44_field})
            for ab44_value in (0, ab44_max):
                with self.subTest(ab44_field=ab44_field, ab44_value=ab44_value):
                    ab44_expected = [1, 2, 1, 2, 0]
                    if ab44_field == 'rr':
                        ab44_expected[3:] = [0, 0] if ab44_value == 0 else [255, 255]
                    else:
                        ab44_expected[ab44_index] = ab44_value
                    self.assertEqual(ab44_build(dict(ab44_context, **{ab44_field: ab44_value})),
                        {'request': ab44_expected, 'reason': None})

    def test_ab44_echo_and_spans(self):
        ab44_ctx = dict(ab44_context)
        del ab44_ctx['family']
        ab44_result = ab44_decode(ab44_ctx, 'UIN', 2, 'Hypothesis', ab44_uin)
        self.assertEqual(ab44_result['reason'], 'context')
        self.assertEqual(ab44_result['context'], ab44_ctx)
        self.assertEqual(ab44_result['raw'], ab44_uin)
        self.assertEqual(ab44_result['header'], [2, 2, 0])
        self.assertEqual(ab44_result['spans'], [[0, 0], [4, 0], [1, 0]])
        self.assertIsNone(ab44_result['limits'])
        for ab44_index in range(3):
            with self.subTest(ab44_echo=ab44_index):
                ab44_raw = ab44_exp.copy()
                ab44_raw[ab44_index] ^= 1
                ab44_result = ab44_decode(ab44_context, 'EXP', 4, 'Hypothesis', ab44_raw)
                self.assertEqual(ab44_result['reason'], 'echo')
                self.assertEqual(ab44_result['header'], ab44_raw[:3])
                self.assertEqual(ab44_result['raw'], ab44_raw)
                self.assertEqual(len(ab44_result['spans']), 3)
        for ab44_index, ab44_value, ab44_expected in (
                (0, -19, [-19, 20, 1]), (1, 21, [-20, 21, 1]),
                (2, 2, [-20, 20, 2]), (2, 0, [-20, 20, 0]),
                (2, -1, None), (0, 21, None), (1, -21, None)):
            with self.subTest(ab44_span=ab44_index, ab44_value=ab44_value):
                ab44_raw = ab44_exp.copy()
                ab44_raw[3+4*ab44_index:7+4*ab44_index] = struct.pack('<f', ab44_value)
                ab44_result = ab44_decode(ab44_context, 'EXP', 4, 'Hypothesis', ab44_raw)
                self.assertEqual(ab44_result['limits'], ab44_expected)
                self.assertEqual(ab44_result['header'], ab44_raw[:3])
                self.assertEqual(ab44_result['raw'], ab44_raw)
                self.assertEqual(ab44_result['spans'][ab44_index], ab44_raw[3+4*ab44_index:7+4*ab44_index])
        for ab44_index in range(3):
            ab44_raw = ab44_exp.copy()
            del ab44_raw[3+4*ab44_index]
            ab44_result = ab44_decode(ab44_context, 'EXP', 4, 'Hypothesis', ab44_raw)
            self.assertEqual(ab44_result['reason'], 'length')
            self.assertEqual(ab44_result['raw'], ab44_raw)
            self.assertIsNone(ab44_result['spans'])
            for ab44_value in (math.inf, -math.inf, math.nan):
                ab44_raw = ab44_exp.copy()
                ab44_raw[3+4*ab44_index:7+4*ab44_index] = struct.pack('<f', ab44_value)
                self.assertEqual(ab44_decode(ab44_context, 'EXP', 4, 'Hypothesis',
                    ab44_raw)['reason'], 'nonfinite')

    def test_ab44_codec_grade_width_and_malformed(self):
        for ab44_raw in ([2, 2], [256, 2, 0], [True, 2, 0]):
            with self.subTest(ab44_raw=ab44_raw):
                ab44_result = ab44_decode(ab44_context, 'UIN', 2, 'Hypothesis', ab44_raw)
                self.assertIsNone(ab44_result['header'])
                self.assertIsNone(ab44_result['spans'])
                self.assertEqual(ab44_result['raw'], ab44_raw)
        for ab44_codec, ab44_width, ab44_grade, ab44_raw, ab44_reason in (
                (None, 2, 'Hypothesis', ab44_uin, 'codec'),
                ('unsupported', 2, 'Hypothesis', ab44_uin, 'codec'),
                ('EXP', 2, 'Hypothesis', ab44_uin, 'codec_width'),
                ('UIN', 0, 'Hypothesis', ab44_uin, 'width'),
                ('UIN', -1, 'Hypothesis', ab44_uin, 'width'),
                ('UIN', None, 'Hypothesis', ab44_uin, 'width'),
                ('UIN', 2, None, ab44_uin, 'grade'),
                ('UIN', 2, 'Unknown', ab44_uin, 'grade'),
                ('UIN', 2, 'Hypothesis', ab44_uin[:-1], 'length'),
                ('UIN', 2, 'Hypothesis', ab44_uin + [0], 'length'),
                ('UIN', 2, 'Hypothesis', [], 'length'),
                ('UIN', 2, 'Hypothesis', ab44_uin[:-1] + [256], 'bytes')):
            with self.subTest(ab44_codec=ab44_codec, ab44_width=ab44_width,
                              ab44_grade=ab44_grade, ab44_reason=ab44_reason):
                ab44_result = ab44_decode(ab44_context, ab44_codec, ab44_width,
                                          ab44_grade, ab44_raw)
                self.assertEqual(ab44_result['reason'], ab44_reason)
                self.assertIsNone(ab44_result['limits'])
                self.assertEqual(ab44_result['header'], ab44_raw[:3] if len(ab44_raw) >= 3 else None)
                self.assertEqual(ab44_result['raw'], ab44_raw)
                self.assertEqual(ab44_result['context'], ab44_context)
        for ab44_grade in ('Hypothesis', 'Proven'):
            ab44_result = ab44_decode(ab44_context, 'UCH', 1, ab44_grade, [2, 2, 0, 0, 4, 1])
            self.assertEqual(ab44_result['limits'], [0, 4, 1])
            self.assertEqual(ab44_result['grade'], ab44_grade)
        for ab44_index in range(3):
            ab44_raw = [2, 2, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            ab44_raw[3+3*ab44_index] += 1
            ab44_result = ab44_decode(ab44_context, 'date/time', 3, 'Hypothesis', ab44_raw)
            self.assertEqual(ab44_result['reason'], 'date_step_unknown')
            self.assertIsNone(ab44_result['limits'])
            self.assertEqual(ab44_result['spans'], [ab44_raw[3:6], ab44_raw[6:9], ab44_raw[9:12]])


if __name__ == '__main__':
    unittest.main()
