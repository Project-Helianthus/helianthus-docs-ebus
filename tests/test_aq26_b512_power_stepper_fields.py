"""Synthetic specification checks; no Python runtime evaluator or Go API binding."""
import json as ab25aq25_json
import os as ab25aq25_os
from pathlib import Path as Ab25Aq25Path
import unittest as ab25aq25_unittest

ab25aq25_root = Ab25Aq25Path(ab25aq25_os.environ.get(
    'ab25aq25_contract_root', str(Ab25Aq25Path(__file__).resolve().parents[1])))
ab25aq25_page = ab25aq25_root / 'architecture/aq26_b512_power_stepper_fields.md'
ab25aq25_fixture = ab25aq25_root / 'architecture/fixtures/aq26_b512_power_stepper_fields.json'
# Independent finite expectation: operation and direction to required field widths.
ab25aq25_widths = {
    (7, 'request'): {},
    (7, 'positive'): {'maximum_power': 1, 'minimum_power': 1},
    (8, 'request'): {'inlet': 2, 'status': 1, 'stepper': 1},
    (8, 'positive'): {'setpoint': 2, 'stepper': 1},
    (9, 'request'): {'release': 1},
    (9, 'positive'): {'release': 1},
}
ab25aq25_status = {0: 'valid', 0x55: 'short', 0xAA: 'interruption-or-disconnected'}


def ab25aq25_pairs(ab25aq25_items):
    ab25aq25_value = {}
    for ab25aq25_key, ab25aq25_item in ab25aq25_items:
        if ab25aq25_key in ab25aq25_value:
            raise ValueError('duplicate key')
        ab25aq25_value[ab25aq25_key] = ab25aq25_item
    return ab25aq25_value


def ab25aq25_constant(ab25aq25_value):
    raise ValueError('non-JSON constant')


def ab25aq25_load(ab25aq25_wire):
    return ab25aq25_json.loads(ab25aq25_wire, object_pairs_hook=ab25aq25_pairs,
                               parse_constant=ab25aq25_constant)


def ab25aq25_is_byte(ab25aq25_value):
    return type(ab25aq25_value) is int and 0 <= ab25aq25_value <= 255


def ab25aq25_admit(ab25aq25_wire):
    ab25aq25_value = ab25aq25_load(ab25aq25_wire)
    if type(ab25aq25_value) is not dict:
        raise ValueError('root object required')
    if not {'context', 'fields'} <= ab25aq25_value.keys():
        raise ValueError('required object missing')
    for ab25aq25_key in ('context', 'fields', 'arguments'):
        if ab25aq25_key in ab25aq25_value and type(ab25aq25_value[ab25aq25_key]) is not dict:
            raise ValueError('object kind')
    for ab25aq25_key in ('primary', 'secondary', 'operation'):
        if ab25aq25_key in ab25aq25_value['context'] and not ab25aq25_is_byte(
                ab25aq25_value['context'][ab25aq25_key]):
            raise ValueError('context byte')
    for ab25aq25_raw in ab25aq25_value['fields'].values():
        if type(ab25aq25_raw) is not list or not all(map(ab25aq25_is_byte, ab25aq25_raw)):
            raise ValueError('field bytes')
    return ab25aq25_value


def ab25aq25_signed16(ab25aq25_raw):
    ab25aq25_number = ab25aq25_raw[0] | ab25aq25_raw[1] << 8
    return (ab25aq25_number - 65536 if ab25aq25_number > 32767 else ab25aq25_number) / 16


def ab25aq25_number(ab25aq25_name, ab25aq25_raw):
    if ab25aq25_name == 'maximum_power':
        return {'number': ab25aq25_raw[0]}
    if ab25aq25_name == 'minimum_power':
        return {'number': ab25aq25_raw[0] / 2, 'candidate_domain': ab25aq25_raw[0] <= 250}
    if ab25aq25_name in ('inlet', 'setpoint'):
        return {'number': ab25aq25_signed16(ab25aq25_raw)}
    if ab25aq25_name == 'status':
        return {'label': ab25aq25_status.get(ab25aq25_raw[0], 'unmapped')}
    return {'flags': {'release': bool(ab25aq25_raw[0] & 1)}, 'reserved': ab25aq25_raw[0] & 254}


def ab25aq25_oracle(ab25aq25_input):
    ab25aq25_context = ab25aq25_input['context']
    ab25aq25_key = (ab25aq25_context.get('operation'), ab25aq25_context.get('direction'))
    if (ab25aq25_context.get('primary'), ab25aq25_context.get('secondary'),
            ab25aq25_context.get('view')) != (181, 18, 'power-stepper') \
            or ab25aq25_key not in ab25aq25_widths:
        return 'Unknown', {}
    ab25aq25_results = {}
    for ab25aq25_name, ab25aq25_width in ab25aq25_widths[ab25aq25_key].items():
        ab25aq25_raw = ab25aq25_input['fields'].get(ab25aq25_name)
        if ab25aq25_raw is None or len(ab25aq25_raw) != ab25aq25_width:
            ab25aq25_results[ab25aq25_name] = {'state': 'incomplete'}
        else:
            ab25aq25_results[ab25aq25_name] = dict(
                ab25aq25_number(ab25aq25_name, ab25aq25_raw), state='complete')
    ab25aq25_state = 'complete' if all(
        ab25aq25_item['state'] == 'complete' for ab25aq25_item in ab25aq25_results.values()
    ) else 'partial'
    return ab25aq25_state, ab25aq25_results


class Ab25Aq25PowerStepperTests(ab25aq25_unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ab25aq25_data = ab25aq25_load(ab25aq25_fixture.read_text(encoding='utf-8'))
        cls.ab25aq25_text = ab25aq25_page.read_text(encoding='utf-8')

    def test_cases_match_independent_oracle(self):
        for ab25aq25_case in self.ab25aq25_data['cases']:
            with self.subTest(ab25aq25_case['id']):
                ab25aq25_input = ab25aq25_admit(ab25aq25_json.dumps(ab25aq25_case['input']))
                self.assertEqual(
                    (ab25aq25_case['state'], ab25aq25_case['results']),
                    ab25aq25_oracle(ab25aq25_input))

    def test_rejections_fail_admission(self):
        for ab25aq25_case in self.ab25aq25_data['rejections']:
            with self.subTest(ab25aq25_case['id']):
                with self.assertRaises(ValueError):
                    ab25aq25_admit(ab25aq25_case['wire'])

    def test_fixture_covers_every_branch_and_boundary(self):
        ab25aq25_ids = {ab25aq25_case['id'] for ab25aq25_case in self.ab25aq25_data['cases']}
        for ab25aq25_id in (
                'op07-request-empty', 'op07-positive-max', 'op07-positive-minimum-ff',
                'op07-positive-minimum-zero', 'op07-positive-empty', 'op08-request-partial',
                'op08-request-complete', 'op08-positive-complete',
                'op08-positive-status-extra-not-interpreted', 'op09-request-release',
                'op09-positive-reserved', 'unsupported-op0a',
                'unsupported-absent-operation', 'unsupported-explicit-zero'):
            self.assertIn(ab25aq25_id, ab25aq25_ids)
        ab25aq25_branches = {
            (ab25aq25_case['input']['context'].get('operation'),
             ab25aq25_case['input']['context']['direction'])
            for ab25aq25_case in self.ab25aq25_data['cases']}
        self.assertTrue(set(ab25aq25_widths) <= ab25aq25_branches)

    def test_page_states_the_contract(self):
        for ab25aq25_text in (
                '`maximum_power`: 1; `minimum_power`: 1', '`inlet`: 2; `status`: 1; `stepper`: 1',
                '`setpoint`: 2; `stepper`: 1', '`release`: 1', 'signedLE16 / 16 Celsius',
                '`candidate_domain: false`', 'raw & 254', '`physical: "Unknown"`',
                '`qualified: false`', 'Hypothesis', 'interruption-or-disconnected'):
            self.assertIn(ab25aq25_text, self.ab25aq25_text)


if __name__ == '__main__':
    ab25aq25_unittest.main()
