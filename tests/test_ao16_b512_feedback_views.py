"""Finite acceptance checks of the B512 OP01 software API page and fixture.

The checks compare the page contract table and the fixture against constants
written here; no interpreter is implemented in this file.
"""

import copy
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
AB15AO15_PAGE = ROOT / 'architecture/ao16_b512_feedback_views.md'
AB15AO15_FIXTURE = ROOT / 'architecture/fixtures/ao16_b512_feedback_views.json'

AB15AO15_SIGNATURE = ('func Ab15Ao15Interpret(ab15ao15Input json.RawMessage) '
                      '(json.RawMessage, error)')
AB15AO15_NAMES = ['secondary_heating_pump', 'circulation_pump', 'solar_pump',
                  'error_relay', 'loading_pump', 'fume_flap']
AB15AO15_LOGICAL = [3, 4, 5, 6, 7, 8]
AB15AO15_KINDS = ['pump', 'pump', 'pump', 'candidate', 'pump', 'candidate']
AB15AO15_CONTROL = {'secondary_heating_pump': [32], 'circulation_pump': [64],
                    'solar_pump': [80], 'error_relay': [15],
                    'loading_pump': [96], 'fume_flap': [240]}
AB15AO15_CONTROL_SUMMARY = {
    'secondary_heating_pump': 'raw', 'circulation_pump': 'raw',
    'solar_pump': 'raw', 'error_relay': 'candidate:state-0F',
    'loading_pump': 'raw', 'fume_flap': 'candidate:state-F0'}
AB15AO15_BASE_CONTEXT = {'primary': 181, 'secondary': 18, 'operation': 1,
                         'direction': 'request', 'view': 'directional-fields',
                         'family': 'opaque-family-a',
                         'variant': 'opaque-variant-a'}
AB15AO15_UNKNOWNS = ['physical_values', 'actual_signal_wire_discriminator',
                     'materialized_defaults', 'peer_support',
                     'relay_polarity', 'default_true_encoding']
AB15AO15_ORIGINS = {'absent': 'origin-Unknown', 'false': 'fallback-candidate',
                    'true': 'actual-input-candidate'}
AB15AO15_PUMPS = {'secondary_heating_pump', 'circulation_pump', 'solar_pump',
                  'loading_pump'}

AB15AO15_CASES = [
    {'id': 'ab15ao15-control-request', 'direction': 'request', 'state': 'complete', 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-control-positive', 'direction': 'positive', 'state': 'complete', 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-ff-request-secondary_heating_pump', 'direction': 'request', 'set': {'secondary_heating_pump': [255]}, 'state': 'complete', 'deviations': {'secondary_heating_pump': 'mapped:leave-unchanged'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-ff-positive-secondary_heating_pump', 'direction': 'positive', 'set': {'secondary_heating_pump': [255]}, 'state': 'complete', 'deviations': {'secondary_heating_pump': 'mapped:function-unavailable'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-ff-request-circulation_pump', 'direction': 'request', 'set': {'circulation_pump': [255]}, 'state': 'complete', 'deviations': {'circulation_pump': 'mapped:leave-unchanged'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-ff-positive-circulation_pump', 'direction': 'positive', 'set': {'circulation_pump': [255]}, 'state': 'complete', 'deviations': {'circulation_pump': 'mapped:function-unavailable'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-ff-request-solar_pump', 'direction': 'request', 'set': {'solar_pump': [255]}, 'state': 'complete', 'deviations': {'solar_pump': 'mapped:leave-unchanged'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-ff-positive-solar_pump', 'direction': 'positive', 'set': {'solar_pump': [255]}, 'state': 'complete', 'deviations': {'solar_pump': 'mapped:function-unavailable'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-ff-request-loading_pump', 'direction': 'request', 'set': {'loading_pump': [255]}, 'state': 'complete', 'deviations': {'loading_pump': 'mapped:leave-unchanged'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-ff-positive-loading_pump', 'direction': 'positive', 'set': {'loading_pump': [255]}, 'state': 'complete', 'deviations': {'loading_pump': 'mapped:function-unavailable'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-relay-0F', 'direction': 'request', 'state': 'complete', 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-relay-F0', 'direction': 'request', 'set': {'error_relay': [240]}, 'state': 'complete', 'deviations': {'error_relay': 'candidate:state-F0'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-relay-00', 'direction': 'request', 'set': {'error_relay': [0]}, 'state': 'complete', 'deviations': {'error_relay': 'candidate:no-action-candidate'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-relay-01', 'direction': 'request', 'set': {'error_relay': [1]}, 'state': 'complete', 'deviations': {'error_relay': 'candidate:no-action-candidate'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-relay-FF', 'direction': 'request', 'set': {'error_relay': [255]}, 'state': 'complete', 'deviations': {'error_relay': 'candidate:no-action-candidate'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-fume-0F', 'direction': 'request', 'set': {'fume_flap': [15]}, 'state': 'complete', 'deviations': {'fume_flap': 'candidate:state-0F'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-fume-F0', 'direction': 'request', 'state': 'complete', 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-fume-00', 'direction': 'request', 'set': {'fume_flap': [0]}, 'state': 'complete', 'deviations': {'fume_flap': 'candidate:no-action-candidate'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-fume-01', 'direction': 'request', 'set': {'fume_flap': [1]}, 'state': 'complete', 'deviations': {'fume_flap': 'candidate:no-action-candidate'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-fume-FF', 'direction': 'request', 'set': {'fume_flap': [255]}, 'state': 'complete', 'deviations': {'fume_flap': 'candidate:no-action-candidate'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-relay-01-positive', 'direction': 'positive', 'set': {'error_relay': [1]}, 'state': 'complete', 'deviations': {'error_relay': 'candidate:no-action-candidate'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-actual-absent-equal', 'direction': 'request', 'extra_fields': {'setpoint': [50], 'feedback': [50]}, 'state': 'complete', 'origin': 'origin-Unknown', 'raw_equal': True},
    {'id': 'ab15ao15-actual-absent-differ', 'direction': 'request', 'extra_fields': {'setpoint': [50], 'feedback': [51]}, 'state': 'complete', 'origin': 'origin-Unknown', 'raw_equal': False},
    {'id': 'ab15ao15-actual-false-equal', 'direction': 'request', 'extra_fields': {'setpoint': [50], 'feedback': [50]}, 'arguments': {'actual_signal': False}, 'state': 'complete', 'origin': 'fallback-candidate', 'raw_equal': True},
    {'id': 'ab15ao15-actual-false-differ', 'direction': 'request', 'extra_fields': {'setpoint': [50], 'feedback': [51]}, 'arguments': {'actual_signal': False}, 'state': 'complete', 'origin': 'fallback-candidate', 'raw_equal': False},
    {'id': 'ab15ao15-actual-true-equal', 'direction': 'request', 'extra_fields': {'setpoint': [50], 'feedback': [50]}, 'arguments': {'actual_signal': True}, 'state': 'complete', 'origin': 'actual-input-candidate', 'raw_equal': True},
    {'id': 'ab15ao15-actual-true-differ', 'direction': 'request', 'extra_fields': {'setpoint': [50], 'feedback': [51]}, 'arguments': {'actual_signal': True}, 'state': 'complete', 'origin': 'actual-input-candidate', 'raw_equal': False},
    {'id': 'ab15ao15-actual-absent-empty-arguments', 'direction': 'request', 'arguments': {}, 'state': 'complete', 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-actual-true-no-feedback-field', 'direction': 'request', 'extra_fields': {'setpoint': [50]}, 'arguments': {'actual_signal': True}, 'state': 'complete', 'origin': 'actual-input-candidate', 'raw_equal': None},
    {'id': 'ab15ao15-missing-error-relay', 'direction': 'request', 'set': {'error_relay': None}, 'state': 'partial', 'deviations': {'error_relay': 'missing'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-short-solar-pump', 'direction': 'request', 'set': {'solar_pump': []}, 'state': 'partial', 'deviations': {'solar_pump': 'short'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-overlong-circulation-pump', 'direction': 'request', 'set': {'circulation_pump': [1, 2]}, 'state': 'partial', 'deviations': {'circulation_pump': 'overlong'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-missing-all-fields', 'direction': 'request', 'set': {'secondary_heating_pump': None, 'circulation_pump': None, 'solar_pump': None, 'error_relay': None, 'loading_pump': None, 'fume_flap': None}, 'state': 'raw-only', 'deviations': {'secondary_heating_pump': 'missing', 'circulation_pump': 'missing', 'solar_pump': 'missing', 'error_relay': 'missing', 'loading_pump': 'missing', 'fume_flap': 'missing'}, 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-tail-and-context-preserved', 'direction': 'request', 'context_set': {'note': {'nested': [1, {'k': True}]}}, 'extra_fields': {'unmodelled_tail': [9, 8, 0, 255]}, 'state': 'complete', 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-opaque-context-b', 'direction': 'request', 'context_set': {'family': 'opaque-family-b', 'variant': 7}, 'state': 'complete', 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-opaque-context-absent-labels', 'direction': 'request', 'context_set': {'family': None, 'variant': None}, 'state': 'complete', 'origin': 'origin-Unknown', 'raw_equal': None},
    {'id': 'ab15ao15-unknown-primary', 'direction': 'request', 'context_set': {'primary': 180}, 'state': 'unknown', 'reason': 'unknown-primary'},
    {'id': 'ab15ao15-unknown-secondary', 'direction': 'request', 'context_set': {'secondary': 19}, 'state': 'unknown', 'reason': 'unknown-secondary'},
    {'id': 'ab15ao15-unknown-operation', 'direction': 'request', 'context_set': {'operation': 2}, 'state': 'unknown', 'reason': 'unknown-operation'},
    {'id': 'ab15ao15-unknown-operation-zero', 'direction': 'request', 'context_set': {'operation': 0}, 'state': 'unknown', 'reason': 'unknown-operation'},
    {'id': 'ab15ao15-unknown-direction', 'direction': 'response', 'state': 'unknown', 'reason': 'unknown-direction'},
    {'id': 'ab15ao15-unknown-view', 'direction': 'request', 'context_set': {'view': 'directional-fields-v2'}, 'state': 'unknown', 'reason': 'unknown-view'},
]

AB15AO15_ERROR_IDS = [
    'ab15ao15-error-duplicate-top-level-key',
    'ab15ao15-error-duplicate-field-key',
    'ab15ao15-error-duplicate-context-key',
    'ab15ao15-error-malformed-json',
    'ab15ao15-error-trailing-data',
    'ab15ao15-error-byte-256',
    'ab15ao15-error-byte-negative',
    'ab15ao15-error-byte-fraction',
    'ab15ao15-error-byte-exponent',
    'ab15ao15-error-byte-string',
    'ab15ao15-error-byte-null',
    'ab15ao15-error-field-not-array',
    'ab15ao15-error-field-null',
    'ab15ao15-error-fields-not-object',
    'ab15ao15-error-fields-missing',
    'ab15ao15-error-context-missing',
    'ab15ao15-error-context-not-object',
    'ab15ao15-error-operation-string',
    'ab15ao15-error-primary-missing',
    'ab15ao15-error-direction-not-string',
    'ab15ao15-error-view-missing',
    'ab15ao15-error-actual-signal-string',
    'ab15ao15-error-actual-signal-null',
    'ab15ao15-error-actual-signal-integer',
    'ab15ao15-error-arguments-unknown-key',
    'ab15ao15-error-arguments-not-object',
    'ab15ao15-error-top-level-unknown-key',
    'ab15ao15-error-top-level-not-object',
]

AB15AO15_ERROR_MARKERS = {
    'duplicate-top-level-key': None, 'duplicate-field-key': None,
    'duplicate-context-key': None, 'malformed-json': None,
    'trailing-data': None,
    'byte-256': '[256]', 'byte-negative': '[-1]', 'byte-fraction': '[1.5]',
    'byte-exponent': '[1e1]', 'byte-string': '["1"]', 'byte-null': '[null]',
    'field-not-array': '"solar_pump":1}', 'field-null': '"solar_pump":null}',
    'fields-not-object': '"fields":[]', 'fields-missing': None,
    'context-missing': None, 'context-not-object': '"context":[]',
    'operation-string': '"operation": "1"', 'primary-missing': None,
    'direction-not-string': '"direction": 1', 'view-missing': None,
    'actual-signal-string': '"actual_signal":"true"',
    'actual-signal-null': '"actual_signal":null',
    'actual-signal-integer': '"actual_signal":1',
    'arguments-unknown-key': '"default_true"',
    'arguments-not-object': '"arguments":[]',
    'top-level-unknown-key': '"extra":1', 'top-level-not-object': None,
}


def ab15ao15_load_page_contract(text):
    found = re.findall(r'```json ao16-contract\n(.*?)\n```', text, re.S)
    assert len(found) == 1, 'exactly one contract table'
    return json.loads(found[0])


def ab15ao15_summary(expect):
    out = {}
    for name in AB15AO15_NAMES:
        field = expect['fields'][name]
        out[name] = field['state'] + (':' + field['label'] if 'label' in field else '')
    return out


def ab15ao15_expected_summary(row):
    merged = dict(AB15AO15_CONTROL_SUMMARY)
    merged.update(row.get('deviations', {}))
    return merged


def ab15ao15_expected_input(row):
    context = dict(AB15AO15_BASE_CONTEXT)
    context['direction'] = row['direction']
    for key, value in row.get('context_set', {}).items():
        if value is None:
            context.pop(key)
        else:
            context[key] = value
    fields = copy.deepcopy(AB15AO15_CONTROL)
    for key, value in row.get('set', {}).items():
        if value is None:
            fields.pop(key)
        else:
            fields[key] = value
    fields.update(copy.deepcopy(row.get('extra_fields', {})))
    result = {'context': context, 'fields': fields}
    if 'arguments' in row:
        result['arguments'] = copy.deepcopy(row['arguments'])
    return result


def ab15ao15_walk_keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from ab15ao15_walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from ab15ao15_walk_keys(item)


def ab15ao15_check_contract(contract):
    expect = {
        'contract_id': 'ab15ao15-b512-op01-directional-fields',
        'signature': AB15AO15_SIGNATURE, 'package': 'vaillant',
        'family_grade': 'Hypothesis', 'qualification': 'Unknown',
        'physical': 'Unknown', 'qualified': False,
        'input_keys': {'required': ['context', 'fields'],
                       'optional': ['arguments']},
        'context': {'primary': 181, 'secondary': 18, 'operation': 1,
                    'directions': ['request', 'positive'],
                    'view': 'directional-fields'},
        'arguments': {'actual_signal': ['absent', 'false', 'true']},
        'pump_labels': {'request_FF': 'leave-unchanged',
                        'positive_FF': 'function-unavailable', 'other': 'raw'},
        'candidate_labels': {'0F': 'state-0F', 'F0': 'state-F0',
                             'other': 'no-action-candidate'},
        'field_states': ['mapped', 'raw', 'candidate', 'missing', 'short',
                         'overlong'],
        'result_states': ['complete', 'partial', 'raw-only', 'unknown'],
        'feedback_origins': AB15AO15_ORIGINS,
        'output_keys': ['context', 'raw', 'arguments', 'state', 'reason',
                        'fields', 'feedback', 'unknowns', 'physical',
                        'qualified'],
        'unknowns': AB15AO15_UNKNOWNS,
        'unknown_reasons': ['unknown-primary', 'unknown-secondary',
                            'unknown-operation', 'unknown-direction',
                            'unknown-view'],
        'numbers': 'none',
        'control_input': AB15AO15_CONTROL,
        'control_summary': AB15AO15_CONTROL_SUMMARY,
        'error_ids': AB15AO15_ERROR_IDS,
        'cases': AB15AO15_CASES,
    }
    for key, value in expect.items():
        assert contract.get(key) == value, 'contract key ' + key
    assert set(contract) == set(expect) | {'fields'}, 'contract key set'
    assert [(f['name'], f['logical'], f['kind']) for f in contract['fields']] == \
        list(zip(AB15AO15_NAMES, AB15AO15_LOGICAL, AB15AO15_KINDS)), 'fields'


def ab15ao15_check_fixture(fixture):
    assert fixture['fixture_id'] == 'ab15ao15-b512-op01-directional-fields'
    assert fixture['family_grade'] == 'Hypothesis'
    assert fixture['qualification'] == 'Unknown'
    assert fixture['qualified'] is False and fixture['physical'] == 'Unknown'
    assert fixture['provenance'] == ('synthetic; software API result tuples '
                                     'only; no device observation')
    assert set(fixture) == {'fixture_id', 'provenance', 'family_grade',
                            'qualification', 'qualified', 'physical', 'cases',
                            'errors'}
    assert [c['id'] for c in fixture['cases']] == [r['id'] for r in AB15AO15_CASES]
    for case, row in zip(fixture['cases'], AB15AO15_CASES):
        assert set(case) == {'id', 'input', 'expect'}, row['id']
        assert case['input'] == ab15ao15_expected_input(row), row['id'] + ' input'
        ab15ao15_check_expect(case['input'], case['expect'], row)
    assert [e['id'] for e in fixture['errors']] == AB15AO15_ERROR_IDS
    for entry in fixture['errors']:
        assert set(entry) == {'id', 'input_text', 'error'}
        assert entry['error'] is True
        short = entry['id'][len('ab15ao15-error-'):]
        marker = AB15AO15_ERROR_MARKERS[short]
        if short.startswith('duplicate'):
            seen = []

            def hook(pairs):
                keys = [k for k, _ in pairs]
                seen.append(len(keys) != len(set(keys)))
                return dict(pairs)
            json.loads(entry['input_text'], object_pairs_hook=hook)
            assert any(seen), entry['id']
        elif short in ('malformed-json', 'trailing-data'):
            try:
                json.loads(entry['input_text'])
            except ValueError:
                pass
            else:
                raise AssertionError(entry['id'] + ' must not parse')
        elif short == 'top-level-not-object':
            assert isinstance(json.loads(entry['input_text']), list)
        elif marker is not None:
            assert marker in entry['input_text'], entry['id']
        else:
            parsed = json.loads(entry['input_text'])
            if short == 'fields-missing':
                assert 'fields' not in parsed
            elif short == 'context-missing':
                assert 'context' not in parsed
            elif short == 'primary-missing':
                assert 'primary' not in parsed['context']
            elif short == 'view-missing':
                assert 'view' not in parsed['context']


def ab15ao15_check_expect(inp, expect, row):
    cid = row['id']
    assert expect['context'] == inp['context'], cid
    assert expect['raw'] == inp['fields'], cid
    assert ('arguments' in expect) == ('arguments' in inp), cid
    if 'arguments' in inp:
        assert expect['arguments'] == inp['arguments'], cid
    assert expect['physical'] == 'Unknown' and expect['qualified'] is False, cid
    assert list(expect['unknowns']) == AB15AO15_UNKNOWNS, cid
    assert set(expect['unknowns'].values()) == {'Unknown'}, cid
    assert 'number' not in set(ab15ao15_walk_keys(expect)), cid
    assert expect['state'] == row['state'], cid
    assert expect.get('reason') == row.get('reason'), cid
    if row['state'] == 'unknown':
        assert expect['fields'] == {} and 'feedback' not in expect, cid
        return
    assert 'reason' not in expect, cid
    assert list(expect['fields']) == AB15AO15_NAMES, cid
    assert ab15ao15_summary(expect) == ab15ao15_expected_summary(row), cid
    for name in AB15AO15_NAMES:
        field = expect['fields'][name]
        assert field['grade'] == 'Hypothesis', cid + name
        assert set(field) <= {'raw', 'state', 'grade', 'label'}, cid + name
        supplied = inp['fields'].get(name)
        if supplied is None:
            assert 'raw' not in field and field['state'] == 'missing', cid + name
        else:
            assert field['raw'] == supplied, cid + name
        if name in AB15AO15_PUMPS and 'label' in field:
            want = ('leave-unchanged' if inp['context']['direction'] == 'request'
                    else 'function-unavailable')
            assert field['label'] == want and field['raw'] == [255], cid + name
    feedback = expect['feedback']
    assert feedback['grade'] == 'Hypothesis', cid
    assert feedback['origin'] == row['origin'], cid
    assert feedback.get('raw_equal') == row['raw_equal'], cid
    assert ('calculation' in feedback) == ('raw_equal' in feedback), cid
    assert feedback.get('calculation', 'Proven') == 'Proven', cid
    assert set(feedback) <= {'origin', 'grade', 'raw_equal', 'calculation'}, cid
    if 'arguments' not in inp or 'actual_signal' not in inp['arguments']:
        assert feedback['origin'] == 'origin-Unknown', cid
    else:
        flag = inp['arguments']['actual_signal']
        assert feedback['origin'] == AB15AO15_ORIGINS['true' if flag else 'false'], cid
    sibling = [n for n in AB15AO15_NAMES if expect['fields'][n]['state'] in
               ('mapped', 'raw', 'candidate')]
    assert expect['state'] == ('complete' if len(sibling) == 6 else
                               'partial' if sibling else 'raw-only'), cid


class TestAb15Ao15Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ab15ao15_text = AB15AO15_PAGE.read_text()
        cls.ab15ao15_contract = ab15ao15_load_page_contract(cls.ab15ao15_text)
        cls.ab15ao15_fixture = json.loads(AB15AO15_FIXTURE.read_text())

    def ab15ao15_fix(self):
        return copy.deepcopy(self.ab15ao15_fixture)

    def ab15ao15_case(self, fixture, suffix):
        return next(c for c in fixture['cases']
                    if c['id'] == 'ab15ao15-' + suffix)

    def test_page_text_and_contract_table(self):
        self.assertIn(AB15AO15_SIGNATURE, self.ab15ao15_text)
        for phrase in ('pure selected field/state interpreter',
                       'Native physical support, effects',
                       'never materialized'):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, ' '.join(self.ab15ao15_text.split()))
        ab15ao15_check_contract(self.ab15ao15_contract)

    def test_fixture_matches_constants(self):
        self.assertEqual(len(self.ab15ao15_fixture['cases']), 42)
        self.assertEqual(len(self.ab15ao15_fixture['errors']), 28)
        ab15ao15_check_fixture(self.ab15ao15_fixture)

    def test_directional_pump_ff_labels_differ_per_pump(self):
        fixture = self.ab15ao15_fixture
        for name in sorted(AB15AO15_PUMPS):
            request = self.ab15ao15_case(fixture, 'ff-request-' + name)
            positive = self.ab15ao15_case(fixture, 'ff-positive-' + name)
            with self.subTest(pump=name):
                self.assertEqual(request['expect']['fields'][name]['label'],
                                 'leave-unchanged')
                self.assertEqual(positive['expect']['fields'][name]['label'],
                                 'function-unavailable')
                for other in AB15AO15_NAMES:
                    if other != name:
                        self.assertNotIn('mapped', request['expect']['fields'][other]['state'])

    def test_relay_and_flap_states_have_no_polarity(self):
        for kind, name in (('relay', 'error_relay'), ('fume', 'fume_flap')):
            labels = {b: self.ab15ao15_case(self.ab15ao15_fixture,
                                            '%s-%s' % (kind, b))
                      ['expect']['fields'][name]['label']
                      for b in ('0F', 'F0', '00', '01', 'FF')}
            self.assertEqual(labels, {'0F': 'state-0F', 'F0': 'state-F0',
                                      '00': 'no-action-candidate',
                                      '01': 'no-action-candidate',
                                      'FF': 'no-action-candidate'})
        self.assertNotIn('polarity', json.dumps(self.ab15ao15_fixture['cases']).replace('relay_polarity', ''))

    def test_actual_signal_is_independent_of_raw_equality(self):
        got = {}
        for flag in ('absent', 'false', 'true'):
            for eq in ('equal', 'differ'):
                case = self.ab15ao15_case(self.ab15ao15_fixture,
                                          'actual-%s-%s' % (flag, eq))
                feedback = case['expect']['feedback']
                got[(flag, eq)] = (feedback['origin'], feedback['raw_equal'])
        self.assertEqual(got, {
            ('absent', 'equal'): ('origin-Unknown', True),
            ('absent', 'differ'): ('origin-Unknown', False),
            ('false', 'equal'): ('fallback-candidate', True),
            ('false', 'differ'): ('fallback-candidate', False),
            ('true', 'equal'): ('actual-input-candidate', True),
            ('true', 'differ'): ('actual-input-candidate', False)})

    def test_partial_cases_keep_five_siblings(self):
        for suffix, bad, state in (('missing-error-relay', 'error_relay', 'missing'),
                                   ('short-solar-pump', 'solar_pump', 'short'),
                                   ('overlong-circulation-pump', 'circulation_pump', 'overlong')):
            expect = self.ab15ao15_case(self.ab15ao15_fixture, suffix)['expect']
            with self.subTest(case=suffix):
                self.assertEqual(expect['state'], 'partial')
                self.assertEqual(expect['fields'][bad]['state'], state)
                good = [n for n in AB15AO15_NAMES if n != bad]
                self.assertEqual([expect['fields'][n]['state'] != state for n in good],
                                 [True] * 5)
        short = self.ab15ao15_case(self.ab15ao15_fixture, 'short-solar-pump')
        self.assertEqual(short['expect']['fields']['solar_pump']['raw'], [])
        missing = self.ab15ao15_case(self.ab15ao15_fixture, 'missing-error-relay')
        self.assertNotIn('raw', missing['expect']['fields']['error_relay'])
        self.assertNotIn('error_relay', missing['expect']['raw'])

    def test_unknown_branches_are_raw_only(self):
        for suffix, reason in (('unknown-primary', 'unknown-primary'),
                               ('unknown-secondary', 'unknown-secondary'),
                               ('unknown-operation', 'unknown-operation'),
                               ('unknown-operation-zero', 'unknown-operation'),
                               ('unknown-direction', 'unknown-direction'),
                               ('unknown-view', 'unknown-view')):
            case = self.ab15ao15_case(self.ab15ao15_fixture, suffix)
            with self.subTest(case=suffix):
                self.assertEqual(case['expect']['state'], 'unknown')
                self.assertEqual(case['expect']['reason'], reason)
                self.assertEqual(case['expect']['fields'], {})
                self.assertEqual(case['expect']['raw'], case['input']['fields'])

    def test_context_and_tail_preserved(self):
        case = self.ab15ao15_case(self.ab15ao15_fixture, 'tail-and-context-preserved')
        self.assertEqual(case['expect']['context']['note'], {'nested': [1, {'k': True}]})
        self.assertEqual(case['expect']['raw']['unmodelled_tail'], [9, 8, 0, 255])
        self.assertNotIn('unmodelled_tail', case['expect']['fields'])
        other = self.ab15ao15_case(self.ab15ao15_fixture, 'opaque-context-b')
        self.assertEqual((other['expect']['context']['family'],
                          other['expect']['context']['variant']), ('opaque-family-b', 7))
        self.assertFalse(other['expect']['qualified'])

    def test_arguments_presence_survives(self):
        empty = self.ab15ao15_case(self.ab15ao15_fixture, 'actual-absent-empty-arguments')
        self.assertEqual(empty['expect']['arguments'], {})
        plain = self.ab15ao15_case(self.ab15ao15_fixture, 'control-request')
        self.assertNotIn('arguments', plain['expect'])

    def test_fixture_round_trips(self):
        again = json.loads(json.dumps(self.ab15ao15_fixture))
        self.assertEqual(again, self.ab15ao15_fixture)
        ab15ao15_check_fixture(again)

    # Each mutation models a production defect; the checker must reject it.
    def ab15ao15_rejects(self, fixture):
        with self.assertRaises(AssertionError):
            ab15ao15_check_fixture(fixture)

    def test_mutation_aliased_fields(self):
        fixture = self.ab15ao15_fix()
        fields = self.ab15ao15_case(fixture, 'ff-request-solar_pump')['expect']['fields']
        fields['circulation_pump'] = fields['solar_pump']
        self.ab15ao15_rejects(fixture)

    def test_mutation_request_ff_positive_meaning(self):
        fixture = self.ab15ao15_fix()
        field = self.ab15ao15_case(fixture, 'ff-request-solar_pump')['expect']['fields']['solar_pump']
        field['label'] = 'function-unavailable'
        self.ab15ao15_rejects(fixture)

    def test_mutation_equality_labelled_actual(self):
        fixture = self.ab15ao15_fix()
        self.ab15ao15_case(fixture, 'actual-absent-equal')['expect']['feedback']['origin'] = 'actual-input-candidate'
        self.ab15ao15_rejects(fixture)
        fixture = self.ab15ao15_fix()
        self.ab15ao15_case(fixture, 'actual-false-equal')['expect']['feedback']['origin'] = 'actual-input-candidate'
        self.ab15ao15_rejects(fixture)

    def test_mutation_relay_polarity_invented(self):
        fixture = self.ab15ao15_fix()
        self.ab15ao15_case(fixture, 'relay-00')['expect']['fields']['error_relay']['label'] = 'off'
        self.ab15ao15_rejects(fixture)
        fixture = self.ab15ao15_fix()
        self.ab15ao15_case(fixture, 'relay-00')['expect']['fields']['error_relay']['polarity'] = 'on'
        self.ab15ao15_rejects(fixture)

    def test_mutation_default_true_materialized(self):
        fixture = self.ab15ao15_fix()
        expect = self.ab15ao15_case(fixture, 'missing-error-relay')['expect']
        expect['fields']['error_relay'] = {'raw': [1], 'state': 'candidate',
                                           'label': 'no-action-candidate',
                                           'grade': 'Hypothesis'}
        self.ab15ao15_rejects(fixture)

    def test_mutation_dropped_siblings(self):
        fixture = self.ab15ao15_fix()
        expect = self.ab15ao15_case(fixture, 'short-solar-pump')['expect']
        expect['fields']['loading_pump'] = {'state': 'missing', 'grade': 'Hypothesis'}
        self.ab15ao15_rejects(fixture)
        fixture = self.ab15ao15_fix()
        self.ab15ao15_case(fixture, 'missing-error-relay')['expect']['state'] = 'raw-only'
        self.ab15ao15_rejects(fixture)

    def test_mutation_fixture_values_and_grades(self):
        def number(f):
            self.ab15ao15_case(f, 'control-request')['expect']['fields']['solar_pump']['number'] = 80
        def qualified(f):
            f['qualified'] = True
        def promoted(f):
            f['family_grade'] = 'Proven'
        def field_grade(f):
            self.ab15ao15_case(f, 'control-request')['expect']['fields']['solar_pump']['grade'] = 'Proven'
        def physical(f):
            self.ab15ao15_case(f, 'control-request')['expect']['physical'] = 'Proven'
        def input_byte(f):
            self.ab15ao15_case(f, 'control-request')['input']['fields']['solar_pump'] = [81]
        def raw_copy(f):
            self.ab15ao15_case(f, 'control-request')['expect']['raw']['solar_pump'] = [81]
        def context(f):
            self.ab15ao15_case(f, 'opaque-context-b')['expect']['context']['variant'] = 8
        def drop_case(f):
            f['cases'].pop()
        def drop_error(f):
            f['errors'].pop()
        def calc(f):
            self.ab15ao15_case(f, 'actual-true-equal')['expect']['feedback']['calculation'] = 'Hypothesis'
        def unknown_branch(f):
            self.ab15ao15_case(f, 'unknown-view')['expect']['state'] = 'partial'
        def unknowns(f):
            self.ab15ao15_case(f, 'control-request')['expect']['unknowns']['peer_support'] = 'Proven'
        def error_text(f):
            f['errors'][5]['input_text'] = f['errors'][5]['input_text'].replace('256', '255')
        for mutate in (number, qualified, promoted, field_grade, physical, input_byte,
                       raw_copy, context, drop_case, drop_error, calc,
                       unknown_branch, unknowns, error_text):
            with self.subTest(mutation=mutate.__name__):
                fixture = self.ab15ao15_fix()
                mutate(fixture)
                self.ab15ao15_rejects(fixture)

    def test_mutation_page_contract(self):
        def rejects(mutate):
            contract = copy.deepcopy(self.ab15ao15_contract)
            mutate(contract)
            with self.assertRaises(AssertionError):
                ab15ao15_check_contract(contract)

        def case_value(c):
            c['cases'][2]['deviations']['secondary_heating_pump'] = 'mapped:function-unavailable'
        def missing_alternative(c):
            c['feedback_origins'].pop('false')
        def promoted(c):
            c['qualification'] = 'Proven'
        def qualified(c):
            c['qualified'] = True
        def field_order(c):
            c['fields'][3], c['fields'][4] = c['fields'][4], c['fields'][3]
        def label(c):
            c['pump_labels']['request_FF'] = 'function-unavailable'
        def drop_case(c):
            c['cases'].pop(5)
        def signature(c):
            c['signature'] = c['signature'].replace('json.RawMessage, error', 'json.RawMessage')
        def context(c):
            c['context']['secondary'] = 17
        def extra(c):
            c['native_support'] = 'Proven'
        for mutate in (case_value, missing_alternative, promoted, qualified, field_order,
                       label, drop_case, signature, context, extra):
            with self.subTest(mutation=mutate.__name__):
                rejects(mutate)

    def test_page_loader_requires_single_table(self):
        with self.assertRaises(AssertionError):
            ab15ao15_load_page_contract(self.ab15ao15_text.replace('ao16-contract', 'x', 1))
        with self.assertRaises(AssertionError):
            ab15ao15_load_page_contract(self.ab15ao15_text + self.ab15ao15_text[self.ab15ao15_text.index('```json ao16-contract'):])


if __name__ == '__main__':
    unittest.main()
