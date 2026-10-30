"""Synthetic representation oracle; does not exercise companion code."""
import copy
import json
import math
from pathlib import Path
import re
import struct
import unittest

ab44_root = Path(__file__).resolve().parents[1]
ab44_fields = ['ab44_family', 'ab44_software', 'ab44_hardware',
               'ab44_api_version', 'ab44_api_revision', 'ab44_op',
               'ab44_gg', 'ab44_ii', 'ab44_rr']
ab44_context = dict(zip(ab44_fields, ['synthetic-controller-family',
    'synthetic-software-a', 'synthetic-hardware-a', 1, 1, 1, 2, 1, 2]))
ab44_uin = [2, 2, 0, 0, 0, 4, 0, 1, 0]
ab44_exp = [2, 2, 0, 0, 0, 160, 193, 0, 0, 160, 65, 0, 0, 128, 63]


def ab44_build(ab44_ctx):
    if set(ab44_ctx) != set(ab44_fields) or any(
            ab44_ctx[ab44_key] is None for ab44_key in ab44_fields):
        return {'ab44_request': None, 'ab44_reason': 'ab44_context'}
    if type(ab44_ctx['ab44_op']) is not int or ab44_ctx['ab44_op'] not in (1, 7):
        return {'ab44_request': None, 'ab44_reason': 'ab44_op'}
    for ab44_field, ab44_max in (('ab44_gg', 255), ('ab44_ii', 255),
                                  ('ab44_rr', 65535)):
        if type(ab44_ctx[ab44_field]) is not int or not 0 <= ab44_ctx[ab44_field] <= ab44_max:
            return {'ab44_request': None, 'ab44_reason': ab44_field}
    return {'ab44_request': [ab44_ctx['ab44_op'], ab44_ctx['ab44_gg'], ab44_ctx['ab44_ii'],
            ab44_ctx['ab44_rr'] & 255, ab44_ctx['ab44_rr'] >> 8], 'ab44_reason': None}


def ab44_decode(ab44_ctx, ab44_codec, ab44_width, ab44_grade, ab44_raw):
    ab44_result = {'ab44_context': copy.deepcopy(ab44_ctx),
                   'ab44_raw': list(ab44_raw), 'ab44_header': None, 'ab44_spans': None,
                   'ab44_limits': None, 'ab44_reason': None,
                   'ab44_grade': ab44_grade}
    def ab44_fail(ab44_reason):
        ab44_result['ab44_reason'] = ab44_reason
        return ab44_result
    if len(ab44_raw) >= 3 and all(type(ab44_byte) is int and 0 <= ab44_byte <= 255
                                  for ab44_byte in ab44_raw[:3]):
        ab44_result['ab44_header'] = list(ab44_raw[:3])
    if not isinstance(ab44_width, int) or isinstance(ab44_width, bool) or ab44_width <= 0:
        return ab44_fail('ab44_width')
    if any(type(ab44_byte) is not int or not 0 <= ab44_byte <= 255
           for ab44_byte in ab44_raw):
        return ab44_fail('ab44_bytes')
    if len(ab44_raw) != 3 + 3 * ab44_width:
        return ab44_fail('ab44_length')
    ab44_result['ab44_spans'] = [ab44_raw[3 + ab44_index * ab44_width:
        3 + (ab44_index + 1) * ab44_width] for ab44_index in range(3)]
    if ab44_build(ab44_ctx)['ab44_request'] is None:
        return ab44_fail('ab44_context')
    if ab44_raw[:3] != [ab44_ctx['ab44_gg'], ab44_ctx['ab44_rr'] & 255,
                          ab44_ctx['ab44_rr'] >> 8]:
        return ab44_fail('ab44_echo')
    if ab44_codec not in ('UCH', 'UIN', 'EXP', 'date/time'):
        return ab44_fail('ab44_codec')
    if ab44_width != {'UCH': 1, 'UIN': 2, 'EXP': 4, 'date/time': 3}[ab44_codec]:
        return ab44_fail('ab44_codec_width')
    if ab44_grade not in ('Hypothesis', 'Proven'):
        return ab44_fail('ab44_grade')
    if ab44_codec == 'date/time':
        return ab44_fail('ab44_date_step_unknown')
    ab44_values = [struct.unpack('<f', bytes(ab44_span))[0]
        if ab44_codec == 'EXP' else int.from_bytes(bytes(ab44_span), 'little')
        for ab44_span in ab44_result['ab44_spans']]
    if not all(math.isfinite(ab44_value) for ab44_value in ab44_values):
        return ab44_fail('ab44_nonfinite')
    if ab44_values[0] > ab44_values[1]:
        return ab44_fail('ab44_reversed')
    if ab44_values[2] < 0:
        return ab44_fail('ab44_negative_step')
    ab44_result['ab44_limits'] = ab44_values
    return ab44_result


class Ab44ContractTests(unittest.TestCase):
    def test_ab44_page_contract(self):
        ab44_page = (ab44_root / 'architecture/al10_b524_description_spans.md').read_text()
        ab44_policy = json.loads(re.search(r'```json\n(.*?)\n```', ab44_page, re.S)[1])
        self.assertEqual(ab44_policy, {
            'ab44_request_ops': [1, 7], 'ab44_metadata_ops': {'1': 2, '7': 6},
            'ab44_context_fields': ab44_fields,
            'ab44_reply_header': ['GG', 'RRlo', 'RRhi'], 'ab44_span_count': 3,
            'ab44_length': '3+3w', 'ab44_infer_codec': False,
            'ab44_echo': ['GG', 'RRlo', 'RRhi'], 'ab44_ii_echo': False,
            'ab44_typed_grades': ['Hypothesis', 'Proven'],
            'ab44_codecs': {'UCH': 1, 'UIN': 2, 'EXP': 4, 'date/time': 3},
            'ab44_nonfinite_valid': False, 'ab44_reversed_valid': False,
            'ab44_negative_step_valid': False, 'ab44_zero_step': 'literal zero',
            'ab44_date_numeric_permission': False,
            'ab44_presence_authority': False, 'ab44_write_authority': False})
        for ab44_clause in ('Ab44BuildDescription(context)',
                'Ab44DecodeDescription(context, explicitCodec, explicitWidth, grade, raw)',
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
            ('ab44_uin', 'UIN', 2, ab44_uin, [0, 4, 1], None),
            ('ab44_wrong_pair', 'EXP', 4, ab44_uin, None, 'ab44_length'),
            ('ab44_exp', 'EXP', 4, ab44_exp, [-20, 20, 1], None),
            ('ab44_date', 'date/time', 3, [2, 2, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                None, 'ab44_date_step_unknown')]
        self.assertEqual(set(ab44_data), {'ab44_examples'})
        self.assertEqual(len(ab44_data['ab44_examples']), 4)
        for ab44_case, ab44_want in zip(ab44_data['ab44_examples'], ab44_expected):
            with self.subTest(ab44_name=ab44_want[0]):
                self.assertEqual(ab44_case, dict(zip([
                    'ab44_name', 'ab44_codec', 'ab44_width', 'ab44_raw',
                    'ab44_expected_limits', 'ab44_expected_reason'], ab44_want),
                    ab44_context=ab44_context, ab44_grade='Hypothesis'))
                ab44_result = ab44_decode(ab44_case['ab44_context'],
                    ab44_case['ab44_codec'], ab44_case['ab44_width'],
                    ab44_case['ab44_grade'], ab44_case['ab44_raw'])
                self.assertEqual(ab44_result['ab44_limits'], ab44_want[4])
                self.assertEqual(ab44_result['ab44_reason'], ab44_want[5])
                self.assertEqual(ab44_result['ab44_raw'], ab44_want[3])

    def test_ab44_identity_axes(self):
        self.assertEqual(ab44_build(ab44_context),
                         {'ab44_request': [1, 2, 1, 2, 0], 'ab44_reason': None})
        ab44_variants = [('ab44_family', 'synthetic-controller-family-b'),
            ('ab44_software', 'synthetic-software-b'),
            ('ab44_hardware', 'synthetic-hardware-b'), ('ab44_api_version', 2),
            ('ab44_api_revision', 2), ('ab44_op', 7), ('ab44_gg', 3),
            ('ab44_ii', 2), ('ab44_rr', 3), ('ab44_rr', 258)]
        ab44_identities = set()
        for ab44_field, ab44_value in ab44_variants:
            with self.subTest(ab44_field=ab44_field, ab44_value=ab44_value):
                ab44_ctx = dict(ab44_context, **{ab44_field: ab44_value})
                ab44_raw = [ab44_ctx['ab44_gg'], ab44_ctx['ab44_rr'] & 255,
                            ab44_ctx['ab44_rr'] >> 8] + ab44_exp[3:]
                ab44_result = ab44_decode(ab44_ctx, 'EXP', 4, 'Hypothesis', ab44_raw)
                self.assertEqual(ab44_result['ab44_context'], ab44_ctx)
                self.assertEqual(ab44_result['ab44_limits'], [-20, 20, 1])
                self.assertNotEqual(ab44_result['ab44_context'], ab44_context)
                ab44_identities.add(tuple(ab44_result['ab44_context'].items()))
                self.assertIsNone(ab44_build(ab44_ctx)['ab44_reason'])
                self.assertEqual(ab44_build(ab44_ctx)['ab44_request'], [ab44_ctx['ab44_op'],
                    ab44_raw[0], ab44_ctx['ab44_ii'], ab44_raw[1], ab44_raw[2]])
        self.assertEqual(len(ab44_identities), 10)
        for ab44_field in ab44_fields:
            ab44_ctx = dict(ab44_context)
            del ab44_ctx[ab44_field]
            self.assertEqual(ab44_build(ab44_ctx),
                {'ab44_request': None, 'ab44_reason': 'ab44_context'})
            ab44_ctx[ab44_field] = None
            self.assertEqual(ab44_build(ab44_ctx),
                {'ab44_request': None, 'ab44_reason': 'ab44_context'})
        for ab44_op in (0, 2, 6, 8, True, False, 1.0, '1'):
            self.assertEqual(ab44_build(dict(ab44_context, ab44_op=ab44_op)),
                {'ab44_request': None, 'ab44_reason': 'ab44_op'})
            self.assertEqual(ab44_decode(dict(ab44_context, ab44_op=ab44_op),
                'EXP', 4, 'Hypothesis', ab44_exp)['ab44_reason'], 'ab44_context')

    def test_ab44_build_selector_boundaries(self):
        self.assertEqual(ab44_build(dict(ab44_context, ab44_extra=1)),
            {'ab44_request': None, 'ab44_reason': 'ab44_context'})
        for ab44_field, ab44_max, ab44_index in (
                ('ab44_gg', 255, 1), ('ab44_ii', 255, 2), ('ab44_rr', 65535, 3)):
            for ab44_value in (-1, ab44_max + 1, True, False, 1.0, '1'):
                with self.subTest(ab44_field=ab44_field, ab44_value=ab44_value):
                    self.assertEqual(ab44_build(dict(ab44_context, **{ab44_field: ab44_value})),
                        {'ab44_request': None, 'ab44_reason': ab44_field})
            for ab44_value in (0, ab44_max):
                with self.subTest(ab44_field=ab44_field, ab44_value=ab44_value):
                    ab44_expected = [1, 2, 1, 2, 0]
                    if ab44_field == 'ab44_rr':
                        ab44_expected[3:] = [0, 0] if ab44_value == 0 else [255, 255]
                    else:
                        ab44_expected[ab44_index] = ab44_value
                    self.assertEqual(ab44_build(dict(ab44_context, **{ab44_field: ab44_value})),
                        {'ab44_request': ab44_expected, 'ab44_reason': None})

    def test_ab44_echo_and_spans(self):
        ab44_ctx = dict(ab44_context)
        del ab44_ctx['ab44_family']
        ab44_result = ab44_decode(ab44_ctx, 'UIN', 2, 'Hypothesis', ab44_uin)
        self.assertEqual(ab44_result['ab44_reason'], 'ab44_context')
        self.assertEqual(ab44_result['ab44_context'], ab44_ctx)
        self.assertEqual(ab44_result['ab44_raw'], ab44_uin)
        self.assertEqual(ab44_result['ab44_header'], [2, 2, 0])
        self.assertEqual(ab44_result['ab44_spans'], [[0, 0], [4, 0], [1, 0]])
        self.assertIsNone(ab44_result['ab44_limits'])
        for ab44_index in range(3):
            with self.subTest(ab44_echo=ab44_index):
                ab44_raw = ab44_exp.copy()
                ab44_raw[ab44_index] ^= 1
                ab44_result = ab44_decode(ab44_context, 'EXP', 4, 'Hypothesis', ab44_raw)
                self.assertEqual(ab44_result['ab44_reason'], 'ab44_echo')
                self.assertEqual(ab44_result['ab44_header'], ab44_raw[:3])
                self.assertEqual(ab44_result['ab44_raw'], ab44_raw)
                self.assertEqual(len(ab44_result['ab44_spans']), 3)
        for ab44_index, ab44_value, ab44_expected in (
                (0, -19, [-19, 20, 1]), (1, 21, [-20, 21, 1]),
                (2, 2, [-20, 20, 2]), (2, 0, [-20, 20, 0]),
                (2, -1, None), (0, 21, None), (1, -21, None)):
            with self.subTest(ab44_span=ab44_index, ab44_value=ab44_value):
                ab44_raw = ab44_exp.copy()
                ab44_raw[3+4*ab44_index:7+4*ab44_index] = struct.pack('<f', ab44_value)
                ab44_result = ab44_decode(ab44_context, 'EXP', 4, 'Hypothesis', ab44_raw)
                self.assertEqual(ab44_result['ab44_limits'], ab44_expected)
                self.assertEqual(ab44_result['ab44_header'], ab44_raw[:3])
                self.assertEqual(ab44_result['ab44_raw'], ab44_raw)
                self.assertEqual(ab44_result['ab44_spans'][ab44_index], ab44_raw[3+4*ab44_index:7+4*ab44_index])
        for ab44_index in range(3):
            ab44_raw = ab44_exp.copy()
            del ab44_raw[3+4*ab44_index]
            ab44_result = ab44_decode(ab44_context, 'EXP', 4, 'Hypothesis', ab44_raw)
            self.assertEqual(ab44_result['ab44_reason'], 'ab44_length')
            self.assertEqual(ab44_result['ab44_raw'], ab44_raw)
            self.assertIsNone(ab44_result['ab44_spans'])
            for ab44_value in (math.inf, -math.inf, math.nan):
                ab44_raw = ab44_exp.copy()
                ab44_raw[3+4*ab44_index:7+4*ab44_index] = struct.pack('<f', ab44_value)
                self.assertEqual(ab44_decode(ab44_context, 'EXP', 4, 'Hypothesis',
                    ab44_raw)['ab44_reason'], 'ab44_nonfinite')

    def test_ab44_codec_grade_width_and_malformed(self):
        for ab44_raw in ([2, 2], [256, 2, 0], [True, 2, 0]):
            with self.subTest(ab44_raw=ab44_raw):
                ab44_result = ab44_decode(ab44_context, 'UIN', 2, 'Hypothesis', ab44_raw)
                self.assertIsNone(ab44_result['ab44_header'])
                self.assertIsNone(ab44_result['ab44_spans'])
                self.assertEqual(ab44_result['ab44_raw'], ab44_raw)
        for ab44_codec, ab44_width, ab44_grade, ab44_raw, ab44_reason in (
                (None, 2, 'Hypothesis', ab44_uin, 'ab44_codec'),
                ('unsupported', 2, 'Hypothesis', ab44_uin, 'ab44_codec'),
                ('EXP', 2, 'Hypothesis', ab44_uin, 'ab44_codec_width'),
                ('UIN', 0, 'Hypothesis', ab44_uin, 'ab44_width'),
                ('UIN', -1, 'Hypothesis', ab44_uin, 'ab44_width'),
                ('UIN', None, 'Hypothesis', ab44_uin, 'ab44_width'),
                ('UIN', 2, None, ab44_uin, 'ab44_grade'),
                ('UIN', 2, 'Unknown', ab44_uin, 'ab44_grade'),
                ('UIN', 2, 'Hypothesis', ab44_uin[:-1], 'ab44_length'),
                ('UIN', 2, 'Hypothesis', ab44_uin + [0], 'ab44_length'),
                ('UIN', 2, 'Hypothesis', [], 'ab44_length'),
                ('UIN', 2, 'Hypothesis', ab44_uin[:-1] + [256], 'ab44_bytes')):
            with self.subTest(ab44_codec=ab44_codec, ab44_width=ab44_width,
                              ab44_grade=ab44_grade, ab44_reason=ab44_reason):
                ab44_result = ab44_decode(ab44_context, ab44_codec, ab44_width,
                                          ab44_grade, ab44_raw)
                self.assertEqual(ab44_result['ab44_reason'], ab44_reason)
                self.assertIsNone(ab44_result['ab44_limits'])
                self.assertEqual(ab44_result['ab44_header'], ab44_raw[:3] if len(ab44_raw) >= 3 else None)
                self.assertEqual(ab44_result['ab44_raw'], ab44_raw)
                self.assertEqual(ab44_result['ab44_context'], ab44_context)
        for ab44_grade in ('Hypothesis', 'Proven'):
            ab44_result = ab44_decode(ab44_context, 'UCH', 1, ab44_grade, [2, 2, 0, 0, 4, 1])
            self.assertEqual(ab44_result['ab44_limits'], [0, 4, 1])
            self.assertEqual(ab44_result['ab44_grade'], ab44_grade)
        for ab44_index in range(3):
            ab44_raw = [2, 2, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            ab44_raw[3+3*ab44_index] += 1
            ab44_result = ab44_decode(ab44_context, 'date/time', 3, 'Hypothesis', ab44_raw)
            self.assertEqual(ab44_result['ab44_reason'], 'ab44_date_step_unknown')
            self.assertIsNone(ab44_result['ab44_limits'])
            self.assertEqual(ab44_result['ab44_spans'], [ab44_raw[3:6], ab44_raw[6:9], ab44_raw[9:12]])


if __name__ == '__main__':
    unittest.main()
