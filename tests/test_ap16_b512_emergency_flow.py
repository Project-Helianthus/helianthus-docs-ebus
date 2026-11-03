"""Synthetic specification checks; no Python runtime evaluator or Go API binding."""
import copy as ab15ap15_copy
import json as ab15ap15_json
import os as ab15ap15_os
from pathlib import Path as Ab15Ap15Path
import re as ab15ap15_re
import unittest as ab15ap15_unittest

ab15ap15_root = Ab15Ap15Path(ab15ap15_os.environ.get(
    'ab15ap15_contract_root', str(Ab15Ap15Path(__file__).resolve().parents[1])))
ab15ap15_page = ab15ap15_root / 'architecture/ap16_b512_emergency_flow.md'
ab15ap15_fixture = ab15ap15_root / 'architecture/fixtures/ap16_b512_emergency_flow.json'
# Independent finite expectations: never derive these from the page or fixture.
ab15ap15_rows = (
    ('flow-io', 17, 'request', 'temperature1', 2, 'signedLE16/16', 'Celsius', 0, 0, 0),
    ('flow-io', 17, 'request', 'temperature2', 2, 'signedLE16/16', 'Celsius', 0, 0, 0),
    ('flow-io', 17, 'request', 'temperature3', 2, 'signedLE16/16', 'Celsius', 0, 0, 0),
    ('flow-io', 17, 'request', 'pressure', 1, 'u8/10', 'bar', 0, 0, 0),
    ('flow-io', 17, 'request', 'flow', 1, 'signed8*10', 'l/h', 0, 0, 0),
    ('flow-io', 17, 'request', 'pump_status', 1, 'raw-u8', 'none', 0, 0, 0),
    ('flow-io', 17, 'request', 'flags', 1, 'bits', 'none', 1, 126, 128),
    ('flow-io', 17, 'positive', 'flags', 1, 'bits', 'none', 3, 252, 0),
    ('flow-io', 17, 'positive', 'setpoint', 1, 'u8', 'percent', 0, 0, 0),
    ('emergency-io', 18, 'request', 'flags', 1, 'bits', 'none', 1, 126, 128),
    ('emergency-io', 18, 'request', 'switch', 1, 'raw-u8', 'none', 0, 0, 0),
    ('emergency-io', 18, 'request', 'co2_1', 2, 'LEu16', 'ppm', 0, 0, 0),
    ('emergency-io', 18, 'request', 'co2_2', 2, 'LEu16', 'ppm', 0, 0, 0),
    ('emergency-io', 18, 'positive', 'flags', 1, 'bits', 'none', 1, 126, 128),
)
ab15ap15_controls = (
    ('flow-negative-one', 'FF', '-10', 'l/h'),
    ('flow-negative-boundary', '80', '-1280', 'l/h'),
    ('flow-positive-boundary', '7F', '1270', 'l/h'),
    ('temperature-one', '10 00', '1', 'Celsius'),
    ('pressure-maximum', 'FF', '25.5', 'bar'),
    ('flow-request-flags', '81', '128', 'unmodeled; compressor-off=true'),
    ('flow-positive-flags', '81', '128', 'reserved; compressor-off=true'),
    ('setpoint-outside', '65', '101', 'candidate_domain=false'),
    ('emergency-co2-first', 'FF FF', '65535', 'ppm; no sentinel'),
    ('emergency-co2-second', '01 00', '1', 'ppm; independent field'),
    ('emergency-request-flags', '80', '128', 'unmodeled'),
    ('emergency-positive-flags', '80', '128', 'unmodeled'),
    ('flow-positive-prefix', 'B5 12 0C', '12', 'conflict with requested17'),
    ('emergency-positive-prefix', 'B5 12 0C', '12', 'conflict with requested18'),
)


def ab15ap15_pairs(ab15ap15_pairs_value):
    ab15ap15_value = {}
    for ab15ap15_key, ab15ap15_item in ab15ap15_pairs_value:
        if ab15ap15_key in ab15ap15_value:
            raise ValueError('duplicate key')
        ab15ap15_value[ab15ap15_key] = ab15ap15_item
    return ab15ap15_value


def ab15ap15_constant(ab15ap15_value):
    raise ValueError('non-JSON constant')


def ab15ap15_load(ab15ap15_wire):
    return ab15ap15_json.loads(ab15ap15_wire, object_pairs_hook=ab15ap15_pairs,
                              parse_constant=ab15ap15_constant)


def ab15ap15_admission_oracle(ab15ap15_wire):
    """Bounded structural predicate only, no evaluation or result construction."""
    ab15ap15_value = ab15ap15_load(ab15ap15_wire)
    if type(ab15ap15_value) is not dict:
        raise ValueError('root object required')
    if not {'context', 'fields'} <= ab15ap15_value.keys():
        raise ValueError('required object missing')
    if ab15ap15_value.keys() - {'context', 'fields', 'arguments'}:
        raise ValueError('unknown root key')
    for ab15ap15_key in ('context', 'fields', 'arguments'):
        if ab15ap15_key in ab15ap15_value and type(ab15ap15_value[ab15ap15_key]) is not dict:
            raise ValueError('object kind')
    for ab15ap15_key, ab15ap15_item in ab15ap15_value['context'].items():
        if ab15ap15_key in ('primary', 'secondary', 'operation'):
            if ab15ap15_item is not None and (
                    type(ab15ap15_item) is not int or not 0 <= ab15ap15_item <= 255):
                raise ValueError('selector integer')
        if ab15ap15_key in ('direction', 'view'):
            if ab15ap15_item is not None and type(ab15ap15_item) is not str:
                raise ValueError('selector string')
    for ab15ap15_array in ab15ap15_value['fields'].values():
        if type(ab15ap15_array) is not list or any(
                type(ab15ap15_byte) is not int or not 0 <= ab15ap15_byte <= 255
                for ab15ap15_byte in ab15ap15_array):
            raise ValueError('byte array')
    return ab15ap15_value


def ab15ap15_table(ab15ap15_text, ab15ap15_header):
    ab15ap15_tail = ab15ap15_text.split(ab15ap15_header + '\n', 1)[1].splitlines()[1:]
    ab15ap15_result = []
    for ab15ap15_line in ab15ap15_tail:
        if not ab15ap15_line.startswith('|'):
            break
        ab15ap15_result.append(tuple(ab15ap15_cell.strip()
                                    for ab15ap15_cell in ab15ap15_line.strip('|').split('|')))
    return ab15ap15_result


class Ab15Ap15ContractTests(ab15ap15_unittest.TestCase):
    @classmethod
    def setUpClass(ab15ap15_cls):
        ab15ap15_cls.ab15ap15_text = ab15ap15_page.read_text()
        ab15ap15_cls.ab15ap15_data = ab15ap15_load(ab15ap15_fixture.read_text())
        ab15ap15_cls.ab15ap15_cases = {
            ab15ap15_case['id']: ab15ap15_case
            for ab15ap15_case in ab15ap15_cls.ab15ap15_data['cases']}

    def test_ab15ap15_api_shape_and_views(ab15ap15_self):
        ab15ap15_contract = ab15ap15_self.ab15ap15_data['contract']
        ab15ap15_page_contract = ab15ap15_load(ab15ap15_re.search(
            r'```json ab15ap15-contract\n(.*?)\n```',
            ab15ap15_self.ab15ap15_text, ab15ap15_re.S).group(1))
        ab15ap15_expected = {
            'package': 'vaillant',
            'signature': 'Ab15Ap15Evaluate(ab15ap15Input json.RawMessage) (json.RawMessage, error)',
            'input_required': ['context', 'fields'], 'input_optional': ['arguments'],
            'context_selector': {'primary': 181, 'secondary': 18},
            'views': [
                {'operation': 17, 'direction': 'request', 'view': 'flow-io', 'arguments': []},
                {'operation': 17, 'direction': 'positive', 'view': 'flow-io', 'arguments': [],
                 'candidate_positive_prefix': [181, 18, 12], 'physical_association': 'Unknown',
                 'matches_requested_operation': False},
                {'operation': 18, 'direction': 'request', 'view': 'emergency-io', 'arguments': []},
                {'operation': 18, 'direction': 'positive', 'view': 'emergency-io', 'arguments': [],
                 'candidate_positive_prefix': [181, 18, 12], 'physical_association': 'Unknown',
                 'matches_requested_operation': False}],
            'output_required': ['context', 'raw', 'state', 'fields', 'physical', 'qualified'],
            'output_optional': ['arguments', 'candidate'], 'physical': 'Unknown',
            'qualified': False, 'semantic_grade': 'Hypothesis', 'calculation_grade': 'Proven',
            'states': ['complete', 'partial', 'Unknown'],
            'field_states': ['complete', 'incomplete', 'Unknown'],
            'setpoint_candidate_domain': [0, 100], 'typed_arguments': [],
            'duplicate_keys': 'reject anywhere', 'copy': 'deep independent',
            'unsupported': 'raw-only', 'runtime_caller': False,
            'persistent_cache': False, 'physical_packet_decoder': False,
        }
        ab15ap15_self.assertEqual(ab15ap15_contract, ab15ap15_expected)
        ab15ap15_self.assertEqual(ab15ap15_page_contract, ab15ap15_expected)
        ab15ap15_self.assertIn('func ' + ab15ap15_expected['signature'],
                              ab15ap15_self.ab15ap15_text)
        ab15ap15_self.assertIs(ab15ap15_self.ab15ap15_data['synthetic'], True)

    def test_ab15ap15_page_tables(ab15ap15_self):
        ab15ap15_self.assertEqual(ab15ap15_table(ab15ap15_self.ab15ap15_text,
            '| view | operation | direction | field | width | formula | unit | known | reserved | unmodeled |'),
            [tuple(map(str, ab15ap15_row)) for ab15ap15_row in ab15ap15_rows])
        ab15ap15_self.assertEqual(ab15ap15_table(ab15ap15_self.ab15ap15_text,
            '| control | raw | expected | interpretation |'), list(ab15ap15_controls))

    def test_ab15ap15_all_tuple_shapes_and_selector_transitions(ab15ap15_self):
        ab15ap15_self.assertEqual(len(ab15ap15_self.ab15ap15_cases),
                                 len(ab15ap15_self.ab15ap15_data['cases']))
        ab15ap15_self.assertGreater(len(ab15ap15_self.ab15ap15_cases), 200)
        for ab15ap15_case in ab15ap15_self.ab15ap15_cases.values():
            with ab15ap15_self.subTest(ab15ap15_case=ab15ap15_case['id']):
                ab15ap15_self.assertTrue(ab15ap15_case['id'].startswith('ab15ap15_'))
                ab15ap15_input = ab15ap15_case['input']
                ab15ap15_result = ab15ap15_case['result']
                ab15ap15_c = ab15ap15_input['context']
                ab15ap15_self.assertEqual(ab15ap15_admission_oracle(
                    ab15ap15_json.dumps(ab15ap15_input)), ab15ap15_input)
                ab15ap15_self.assertEqual(ab15ap15_result['context'], ab15ap15_c)
                ab15ap15_self.assertEqual(ab15ap15_result['raw'], ab15ap15_input['fields'])
                ab15ap15_self.assertIs(ab15ap15_result['qualified'], False)
                ab15ap15_self.assertEqual(ab15ap15_result['physical'], 'Unknown')
                ab15ap15_self.assertEqual('arguments' in ab15ap15_input,
                                         'arguments' in ab15ap15_result)
                if 'arguments' in ab15ap15_input:
                    ab15ap15_self.assertEqual(ab15ap15_result['arguments'], ab15ap15_input['arguments'])
                ab15ap15_supported = (ab15ap15_c.get('primary') == 181 and
                    ab15ap15_c.get('secondary') == 18 and
                    (ab15ap15_c.get('operation'), ab15ap15_c.get('direction'),
                     ab15ap15_c.get('view')) in ((17, 'request', 'flow-io'),
                        (17, 'positive', 'flow-io'), (18, 'request', 'emergency-io'),
                        (18, 'positive', 'emergency-io')))
                ab15ap15_keys = {'context', 'raw', 'state', 'fields', 'physical', 'qualified'}
                if 'arguments' in ab15ap15_input:
                    ab15ap15_keys.add('arguments')
                if not ab15ap15_supported:
                    ab15ap15_self.assertEqual(ab15ap15_result['state'], 'Unknown')
                    ab15ap15_self.assertEqual(ab15ap15_result['fields'], {})
                else:
                    if ab15ap15_c['direction'] == 'positive':
                        ab15ap15_keys.add('candidate')
                        ab15ap15_self.assertEqual(ab15ap15_result['candidate'], {
                            'positive_prefix': [181, 18, 12],
                            'requested_operation': ab15ap15_c['operation'],
                            'matches_requested_operation': False,
                            'physical_association': 'Unknown', 'grade': 'Hypothesis'})
                    ab15ap15_active = [ab15ap15_row for ab15ap15_row in ab15ap15_rows
                        if ab15ap15_row[:3] == (ab15ap15_c['view'], ab15ap15_c['operation'], ab15ap15_c['direction'])]
                    ab15ap15_incomplete = any(ab15ap15_row[3] not in ab15ap15_input['fields']
                        or len(ab15ap15_input['fields'][ab15ap15_row[3]]) != ab15ap15_row[4]
                        for ab15ap15_row in ab15ap15_active)
                    ab15ap15_self.assertEqual(ab15ap15_result['state'],
                                             'partial' if ab15ap15_incomplete else 'complete')
                    ab15ap15_names = {ab15ap15_row[3] for ab15ap15_row in ab15ap15_active}
                    ab15ap15_self.assertEqual(set(ab15ap15_result['fields']),
                                             ab15ap15_names | ab15ap15_input['fields'].keys())
                    for ab15ap15_name in ab15ap15_input['fields'].keys() - ab15ap15_names:
                        ab15ap15_self.assertEqual(ab15ap15_result['fields'][ab15ap15_name],
                            {'raw': ab15ap15_input['fields'][ab15ap15_name], 'state': 'Unknown'})
                ab15ap15_self.assertEqual(set(ab15ap15_result), ab15ap15_keys)

    def test_ab15ap15_field_arithmetic_masks_and_partial_siblings(ab15ap15_self):
        for ab15ap15_case in ab15ap15_self.ab15ap15_cases.values():
            ab15ap15_c = ab15ap15_case['input']['context']
            if ab15ap15_case['result']['state'] == 'Unknown':
                continue
            for ab15ap15_row in ab15ap15_rows:
                if ab15ap15_row[:3] != (ab15ap15_c['view'], ab15ap15_c['operation'], ab15ap15_c['direction']):
                    continue
                ab15ap15_name, ab15ap15_width, ab15ap15_codec, ab15ap15_unit = ab15ap15_row[3:7]
                with ab15ap15_self.subTest(ab15ap15_case=ab15ap15_case['id'], ab15ap15_field=ab15ap15_name):
                    ab15ap15_raw = ab15ap15_case['input']['fields'].get(ab15ap15_name)
                    ab15ap15_field = ab15ap15_case['result']['fields'][ab15ap15_name]
                    ab15ap15_present = ab15ap15_raw is not None
                    ab15ap15_expected = {'state': 'incomplete', 'grade': 'Hypothesis',
                        'presence': 'present' if ab15ap15_present else 'absent'}
                    if ab15ap15_present:
                        ab15ap15_expected['raw'] = ab15ap15_raw
                    if ab15ap15_present and len(ab15ap15_raw) == ab15ap15_width:
                        ab15ap15_expected['state'] = 'complete'
                        if ab15ap15_codec == 'bits':
                            # Bit sets, independently of table mask arithmetic.
                            ab15ap15_set = {ab15ap15_bit for ab15ap15_bit in range(8)
                                           if ab15ap15_raw[0] & (1 << ab15ap15_bit)}
                            ab15ap15_positive_flow = ab15ap15_row[:3] == ('flow-io', 17, 'positive')
                            ab15ap15_labels = {'compressor-off': 0 in ab15ap15_set} if ab15ap15_c['operation'] == 17 else {
                                'emergency' if ab15ap15_c['direction'] == 'request' else 'LED': 0 in ab15ap15_set}
                            if ab15ap15_positive_flow:
                                ab15ap15_labels['pump-relay'] = 1 in ab15ap15_set
                            ab15ap15_reserved_bits = range(2, 8) if ab15ap15_positive_flow else range(1, 7)
                            ab15ap15_expected.update(flags=ab15ap15_labels,
                                reserved=sum(1 << ab15ap15_bit for ab15ap15_bit in ab15ap15_reserved_bits
                                             if ab15ap15_bit in ab15ap15_set),
                                unmodeled=0 if ab15ap15_positive_flow else (128 if 7 in ab15ap15_set else 0))
                        else:
                            ab15ap15_signed = ab15ap15_name in ('temperature1', 'temperature2', 'temperature3', 'flow')
                            ab15ap15_value = int.from_bytes(bytes(ab15ap15_raw), 'little', signed=ab15ap15_signed)
                            if ab15ap15_name.startswith('temperature'):
                                ab15ap15_value /= 16
                            elif ab15ap15_name == 'flow':
                                ab15ap15_value *= 10
                            elif ab15ap15_name == 'pressure':
                                ab15ap15_value /= 10
                            ab15ap15_expected.update(number=ab15ap15_value, unit=ab15ap15_unit, calculation='Proven')
                            if ab15ap15_name == 'setpoint':
                                ab15ap15_expected['candidate_domain'] = ab15ap15_raw[0] <= 100
                        # Exact shape forbids invented labels/numbers, grade replacement or omission.
                    ab15ap15_self.assertEqual(ab15ap15_field, ab15ap15_expected)

    def test_ab15ap15_independent_discriminating_controls(ab15ap15_self):
        for ab15ap15_id, ab15ap15_field, ab15ap15_number in (
                ('17_request_base', 'flow', -10), ('flow_128', 'flow', -1280),
                ('flow_127', 'flow', 1270), ('17_request_base', 'temperature1', 1),
                ('17_request_base', 'pressure', 25.5), ('17_positive_base', 'setpoint', 101),
                ('18_request_base', 'co2_1', 65535), ('18_request_base', 'co2_2', 1),
                ('co2_swap_control', 'co2_1', 1), ('co2_swap_control', 'co2_2', 65535)):
            ab15ap15_self.assertEqual(ab15ap15_self.ab15ap15_cases['ab15ap15_' + ab15ap15_id]
                ['result']['fields'][ab15ap15_field]['number'], ab15ap15_number)
        for ab15ap15_id, ab15ap15_reserved, ab15ap15_unmodeled in (
                ('17_request_base', 0, 128), ('17_positive_base', 128, 0),
                ('18_request_base', 0, 128), ('18_positive_base', 0, 128)):
            ab15ap15_flags = ab15ap15_self.ab15ap15_cases['ab15ap15_' + ab15ap15_id]['result']['fields']['flags']
            ab15ap15_self.assertEqual((ab15ap15_flags['reserved'], ab15ap15_flags['unmodeled']),
                                     (ab15ap15_reserved, ab15ap15_unmodeled))
        ab15ap15_self.assertIs(ab15ap15_self.ab15ap15_cases['ab15ap15_17_positive_base']
                              ['result']['fields']['setpoint']['candidate_domain'], False)
        for ab15ap15_op in (17, 18):
            ab15ap15_candidate = ab15ap15_self.ab15ap15_cases[f'ab15ap15_{ab15ap15_op}_positive_base']['result']['candidate']
            ab15ap15_self.assertEqual(ab15ap15_candidate['positive_prefix'], [181, 18, 12])
            ab15ap15_self.assertNotEqual(ab15ap15_candidate['requested_operation'], 12)
            ab15ap15_self.assertIs(ab15ap15_candidate['matches_requested_operation'], False)

    def test_ab15ap15_every_context_key_varies_independently(ab15ap15_self):
        for ab15ap15_op in (17, 18):
            for ab15ap15_direction in ('request', 'positive'):
                ab15ap15_prefix = f'ab15ap15_{ab15ap15_op}_{ab15ap15_direction}'
                ab15ap15_base = ab15ap15_self.ab15ap15_cases[ab15ap15_prefix + '_base']
                for ab15ap15_key in ('primary', 'secondary', 'operation', 'direction', 'view', 'family', 'variant'):
                    ab15ap15_case = ab15ap15_self.ab15ap15_cases[ab15ap15_prefix + '_context_' + ab15ap15_key]
                    ab15ap15_self.assertNotEqual(ab15ap15_case['input']['context'][ab15ap15_key],
                                                ab15ap15_base['input']['context'][ab15ap15_key])
                    ab15ap15_self.assertEqual(ab15ap15_case['input']['fields'], ab15ap15_base['input']['fields'])
                    for ab15ap15_other in ab15ap15_base['input']['context'].keys() - {ab15ap15_key}:
                        ab15ap15_self.assertEqual(ab15ap15_case['input']['context'][ab15ap15_other],
                                                ab15ap15_base['input']['context'][ab15ap15_other])
                    ab15ap15_self.assertEqual(ab15ap15_case['result']['state'],
                                             'complete' if ab15ap15_key in ('family', 'variant') else 'Unknown')
                    for ab15ap15_tag in ('absent', 'null') + (('zero',) if ab15ap15_key in ('primary', 'secondary', 'operation') else ()):
                        ab15ap15_c = ab15ap15_self.ab15ap15_cases[
                            ab15ap15_prefix + '_context_' + ab15ap15_key + '_' + ab15ap15_tag]['result']['context']
                        if ab15ap15_tag == 'absent':
                            ab15ap15_self.assertNotIn(ab15ap15_key, ab15ap15_c)
                        elif ab15ap15_tag == 'null':
                            ab15ap15_self.assertIsNone(ab15ap15_c[ab15ap15_key])
                        else:
                            ab15ap15_self.assertEqual(ab15ap15_c[ab15ap15_key], 0)

    def test_ab15ap15_every_field_varies_independently(ab15ap15_self):
        for ab15ap15_row in ab15ap15_rows:
            ab15ap15_prefix = f'ab15ap15_{ab15ap15_row[1]}_{ab15ap15_row[2]}'
            ab15ap15_name, ab15ap15_width = ab15ap15_row[3:5]
            ab15ap15_base = ab15ap15_self.ab15ap15_cases[ab15ap15_prefix + '_base']
            for ab15ap15_tag, ab15ap15_length in (('absent', None), ('empty', 0),
                    ('short', ab15ap15_width - 1), ('overlong', ab15ap15_width + 1),
                    ('zero', ab15ap15_width), ('maximum', ab15ap15_width)):
                ab15ap15_case = ab15ap15_self.ab15ap15_cases[ab15ap15_prefix + '_' + ab15ap15_name + '_' + ab15ap15_tag]
                ab15ap15_self.assertEqual(ab15ap15_case['input']['context'], ab15ap15_base['input']['context'])
                if ab15ap15_length is None:
                    ab15ap15_self.assertNotIn(ab15ap15_name, ab15ap15_case['input']['fields'])
                else:
                    ab15ap15_raw = ab15ap15_case['input']['fields'][ab15ap15_name]
                    ab15ap15_self.assertEqual(len(ab15ap15_raw), ab15ap15_length)
                    ab15ap15_self.assertEqual(ab15ap15_raw, [255 if ab15ap15_tag == 'maximum' else 0] * ab15ap15_length)
                for ab15ap15_sibling in ab15ap15_base['input']['fields'].keys() - {ab15ap15_name}:
                    ab15ap15_self.assertEqual(ab15ap15_case['result']['fields'][ab15ap15_sibling],
                                            ab15ap15_base['result']['fields'][ab15ap15_sibling])

    def test_ab15ap15_arguments_and_round_trip(ab15ap15_self):
        for ab15ap15_op in (17, 18):
            for ab15ap15_direction in ('request', 'positive'):
                ab15ap15_prefix = f'ab15ap15_{ab15ap15_op}_{ab15ap15_direction}'
                ab15ap15_self.assertNotIn('arguments', ab15ap15_self.ab15ap15_cases[ab15ap15_prefix + '_base']['result'])
                for ab15ap15_tag, ab15ap15_expected in (
                        ('empty', {}), ('false', {'opaque': False}), ('zero', {'opaque': 0}),
                        ('null', {'opaque': None}), ('array', {'opaque': [False, 0, None, {'nested': []}]}),
                        ('string', {'opaque': ''})):
                    ab15ap15_case = ab15ap15_self.ab15ap15_cases[ab15ap15_prefix + '_arguments_' + ab15ap15_tag]
                    ab15ap15_self.assertEqual(ab15ap15_case['input']['arguments'], ab15ap15_expected)
                    ab15ap15_self.assertEqual(ab15ap15_case['result']['arguments'], ab15ap15_expected)
                    ab15ap15_self.assertIs(type(ab15ap15_case['result']['arguments'].get('opaque')),
                                         type(ab15ap15_expected.get('opaque')))
        for ab15ap15_case in ab15ap15_self.ab15ap15_cases.values():
            ab15ap15_self.assertEqual(ab15ap15_load(ab15ap15_json.dumps(ab15ap15_case)), ab15ap15_case)

    def test_ab15ap15_nested_fixture_storage_is_independent(ab15ap15_self):
        # Checks serialized specification tuples, not implementation aliasing.
        ab15ap15_snapshot = ab15ap15_json.dumps(ab15ap15_self.ab15ap15_data, sort_keys=True)
        ab15ap15_case = ab15ap15_copy.deepcopy(ab15ap15_self.ab15ap15_cases['ab15ap15_17_request_arguments_array'])
        ab15ap15_original = ab15ap15_copy.deepcopy(ab15ap15_case)
        ab15ap15_case['input']['context']['variant']['opaque'].append('changed')
        ab15ap15_case['input']['fields']['flow'][0] = 0
        ab15ap15_case['input']['arguments']['opaque'][3]['nested'].append(False)
        ab15ap15_self.assertEqual(ab15ap15_case['result'], ab15ap15_original['result'])
        ab15ap15_case['result']['raw']['flow'][0] = 128
        ab15ap15_self.assertEqual(ab15ap15_case['result']['fields'], ab15ap15_original['result']['fields'])
        ab15ap15_case['result']['fields']['flow']['raw'][0] = 127
        ab15ap15_self.assertEqual(ab15ap15_case['result']['raw']['flow'], [128])
        ab15ap15_case['result']['context']['variant']['opaque'].append(None)
        ab15ap15_case['result']['arguments']['opaque'][3]['nested'].append(0)
        ab15ap15_other = ab15ap15_load(ab15ap15_json.dumps(ab15ap15_original))
        ab15ap15_self.assertEqual(ab15ap15_other, ab15ap15_original)
        ab15ap15_self.assertEqual(ab15ap15_json.dumps(ab15ap15_self.ab15ap15_data, sort_keys=True), ab15ap15_snapshot)

    def test_ab15ap15_opaque_kinds_and_empty_objects(ab15ap15_self):
        for ab15ap15_op in (17, 18):
            for ab15ap15_direction in ('request', 'positive'):
                ab15ap15_prefix = f'ab15ap15_{ab15ap15_op}_{ab15ap15_direction}'
                for ab15ap15_key in ('family', 'variant', 'opaque'):
                    for ab15ap15_tag, ab15ap15_value in (
                            ('false', False), ('zero', 0), ('string', ''),
                            ('array', []), ('object', {})):
                        ab15ap15_case = ab15ap15_self.ab15ap15_cases[
                            ab15ap15_prefix + '_opaque_' + ab15ap15_key + '_' + ab15ap15_tag]
                        ab15ap15_result = ab15ap15_case['result']
                        ab15ap15_self.assertEqual(ab15ap15_result['state'], 'complete')
                        ab15ap15_self.assertEqual(ab15ap15_result['context'][ab15ap15_key], ab15ap15_value)
                        ab15ap15_self.assertIs(type(ab15ap15_result['context'][ab15ap15_key]), type(ab15ap15_value))
                        ab15ap15_self.assertIs(ab15ap15_result['qualified'], False)
                ab15ap15_empty_fields = ab15ap15_self.ab15ap15_cases[ab15ap15_prefix + '_fields_empty']['result']
                ab15ap15_self.assertEqual(ab15ap15_empty_fields['raw'], {})
                ab15ap15_self.assertEqual(ab15ap15_empty_fields['state'], 'partial')
                ab15ap15_self.assertTrue(all(ab15ap15_field == {
                    'state': 'incomplete', 'grade': 'Hypothesis', 'presence': 'absent'}
                    for ab15ap15_field in ab15ap15_empty_fields['fields'].values()))
                ab15ap15_empty_context = ab15ap15_self.ab15ap15_cases[ab15ap15_prefix + '_context_empty']['result']
                ab15ap15_self.assertEqual(ab15ap15_empty_context['context'], {})
                ab15ap15_self.assertEqual(ab15ap15_empty_context['state'], 'Unknown')
                ab15ap15_self.assertEqual(ab15ap15_empty_context['fields'], {})

    def test_ab15ap15_rejections_and_valid_controls(ab15ap15_self):
        ab15ap15_self.assertGreater(len(ab15ap15_self.ab15ap15_data['rejections']), 100)
        for ab15ap15_case in ab15ap15_self.ab15ap15_data['rejections']:
            with ab15ap15_self.subTest(ab15ap15_case=ab15ap15_case['id']):
                ab15ap15_self.assertIs(ab15ap15_case['error'], True)
                ab15ap15_self.assertIsNone(ab15ap15_case['successful_result'])
                with ab15ap15_self.assertRaises(ValueError):
                    ab15ap15_admission_oracle(ab15ap15_case['json'])
        # Unsupported view still cannot admit invalid bytes; valid control remains raw-only.
        ab15ap15_input = ab15ap15_copy.deepcopy(ab15ap15_self.ab15ap15_cases['ab15ap15_17_request_context_view']['input'])
        ab15ap15_admission_oracle(ab15ap15_json.dumps(ab15ap15_input))
        ab15ap15_input['fields']['flow'] = [False]
        with ab15ap15_self.assertRaises(ValueError):
            ab15ap15_admission_oracle(ab15ap15_json.dumps(ab15ap15_input))
        for ab15ap15_key in ('primary', 'secondary', 'operation'):
            for ab15ap15_value in (-1, 256, '17'):
                ab15ap15_input = {'context': {ab15ap15_key: ab15ap15_value}, 'fields': {}}
                with ab15ap15_self.assertRaises(ValueError):
                    ab15ap15_admission_oracle(ab15ap15_json.dumps(ab15ap15_input))
        with ab15ap15_self.assertRaises(ValueError):
            ab15ap15_admission_oracle('{"context":{},"fields":{},"unexpected":0}')


if __name__ == '__main__':
    ab15ap15_unittest.main()
