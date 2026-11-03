"""Specification checks only; no implementation of the proposed Go runtime API."""
import copy
import json
from pathlib import Path
import re
import tempfile
import unittest


AB23AP23_ROOT = Path(__file__).resolve().parents[1]
AB23AP23_PAGE = AB23AP23_ROOT / 'architecture/ap24_b516_energy_type_fields.md'
AB23AP23_FIXTURE = AB23AP23_ROOT / 'architecture/fixtures/ap24_b516_energy_type_fields.json'
AB23AP23_CONTRACT = {
    'package': 'vaillant',
    'signature': 'Ab23Ap23Evaluate(ab23ap23Input json.RawMessage) (json.RawMessage, error)',
    'selector': {'primary': 181, 'secondary': 22, 'operation': None,
                 'view': 'energy-type',
                 'directions': ['request', 'read-positive', 'write-positive']},
    'value_width': 1, 'typed_arguments': {},
    'grades': {'candidate': 'Hypothesis', 'calculation': 'Proven',
               'physical': 'Unknown', 'qualified': False},
    'states': {'supported': 'complete', 'incomplete': 'partial', 'unsupported': 'Unknown'},
    'output_keys': ['context', 'raw', 'state', 'fields', 'physical', 'qualified'],
    'optional_output_keys': ['arguments'],
    'errors': ['malformed-json', 'duplicate-key', 'wrong-kind',
               'nonintegral-number', 'out-of-range'],
    'unknowns': ['request-defaults', 'enum-labels', 'encoded-operation',
                 'physical-coordinates', 'meter-selector', 'clear-selector',
                 'OP10-statistics-flag', 'support', 'freshness', 'effects',
                 'persistence', 'delivery'],
}
# Independent literal tuples: byte, low six, bit 6, bit 7, retained high bits.
AB23AP23_TUPLES = (
    (0, 0, False, False, 0), (1, 1, False, False, 0),
    (63, 63, False, False, 0), (64, 0, True, False, 64),
    (128, 0, False, True, 128), (192, 0, True, True, 192),
    (193, 1, True, True, 192), (255, 63, True, True, 192),
)


def ab23ap23_pairs(ab23ap23_items):
    ab23ap23_object = {}
    for ab23ap23_key, ab23ap23_value in ab23ap23_items:
        if ab23ap23_key in ab23ap23_object:
            raise ValueError('duplicate-key')
        ab23ap23_object[ab23ap23_key] = ab23ap23_value
    return ab23ap23_object


def ab23ap23_admission(ab23ap23_text):
    """Small test oracle for JSON admission, never a runtime entry point."""
    try:
        ab23ap23_input = json.loads(ab23ap23_text, object_pairs_hook=ab23ap23_pairs)
    except json.JSONDecodeError:
        return 'malformed-json'
    except ValueError:
        return 'duplicate-key'
    if type(ab23ap23_input) is not dict:
        return 'wrong-kind'
    for ab23ap23_key in ('context', 'fields'):
        if type(ab23ap23_input.get(ab23ap23_key)) is not dict:
            return 'wrong-kind'
    if 'arguments' in ab23ap23_input and type(ab23ap23_input['arguments']) is not dict:
        return 'wrong-kind'
    for ab23ap23_array in ab23ap23_input['fields'].values():
        if type(ab23ap23_array) is not list:
            return 'wrong-kind'
        for ab23ap23_byte in ab23ap23_array:
            if type(ab23ap23_byte) not in (int, float):
                return 'wrong-kind'
            if ab23ap23_byte % 1:
                return 'nonintegral-number'
            if not 0 <= ab23ap23_byte <= 255:
                return 'out-of-range'
    return None


class Ab23Ap23ContractTests(unittest.TestCase):
    def setUp(self):
        self.ab23ap23_page = AB23AP23_PAGE.read_text()
        self.ab23ap23_data = json.loads(AB23AP23_FIXTURE.read_text())

    def ab23ap23_equal(self, ab23ap23_actual, ab23ap23_expected):
        # JSON equality preserves Boolean versus numeric zero, unlike Python ==.
        self.assertEqual(json.dumps(ab23ap23_actual, sort_keys=True),
                         json.dumps(ab23ap23_expected, sort_keys=True))

    def ab23ap23_check_page(self, ab23ap23_page):
        ab23ap23_blocks = re.findall(r'```json\n(.*?)\n```', ab23ap23_page, re.S)
        self.assertEqual(len(ab23ap23_blocks), 1)
        self.ab23ap23_equal(json.loads(ab23ap23_blocks[0]), AB23AP23_CONTRACT)
        self.assertEqual(re.findall(r'```go\n(.*?)\n```', ab23ap23_page, re.S),
                         ['func ' + AB23AP23_CONTRACT['signature']])
        ab23ap23_rows = [tuple(ab23ap23_cell.strip() for ab23ap23_cell in
                              ab23ap23_line.strip('|').split('|'))
                        for ab23ap23_line in ab23ap23_page.splitlines()
                        if ab23ap23_line.startswith('| ')]
        self.assertEqual([ab23ap23_row for ab23ap23_row in ab23ap23_rows
                          if ab23ap23_row[0] == 'null'], [
            ('null', 'request', 'energy-type', '1', 'value', 'absent', 'absent', 'absent', 'absent'),
            ('null', 'read-positive', 'energy-type', '1', 'absent', 'value & 63',
             '(value & 64) != 0', '(value & 128) != 0', 'absent'),
            ('null', 'write-positive', 'energy-type', '1', 'absent', 'value & 63',
             'absent', 'absent', 'value & 192'),
        ])
        self.assertEqual([ab23ap23_row for ab23ap23_row in ab23ap23_rows
                          if ab23ap23_row[0].isdigit()], [
            tuple(str(ab23ap23_cell).lower() for ab23ap23_cell in
                  (ab23ap23_v, ab23ap23_v, ab23ap23_low, ab23ap23_f6,
                   ab23ap23_f7, ab23ap23_low, ab23ap23_high))
            for ab23ap23_v, ab23ap23_low, ab23ap23_f6, ab23ap23_f7, ab23ap23_high
            in AB23AP23_TUPLES])
        self.assertEqual([ab23ap23_row for ab23ap23_row in ab23ap23_rows
                          if len(ab23ap23_row) == 3 and ab23ap23_row[1] in
                          ('complete', 'partial', 'Unknown', 'error')], [
            ('supported selector and one byte', 'complete', 'value complete, grade Hypothesis'),
            ('supported selector and missing/empty/overlong value', 'partial', 'value incomplete, grade Hypothesis'),
            ('unsupported selector', 'Unknown', 'empty object; raw retained'),
            ('invalid JSON or admission failure', 'error', 'no successful result'),
        ])

    def ab23ap23_check_scenarios(self, ab23ap23_data):
        self.ab23ap23_equal(ab23ap23_data['contract'], AB23AP23_CONTRACT)
        for ab23ap23_case in ab23ap23_data['scenarios']:
            ab23ap23_input = ab23ap23_case['input']
            self.assertIsNone(ab23ap23_admission(json.dumps(ab23ap23_input)))
            ab23ap23_c = ab23ap23_input['context']
            ab23ap23_raw = ab23ap23_input['fields']
            ab23ap23_expected = {
                'context': ab23ap23_c, 'raw': ab23ap23_raw, 'state': 'Unknown',
                'fields': {}, 'physical': 'Unknown', 'qualified': False}
            if 'arguments' in ab23ap23_input:
                ab23ap23_expected['arguments'] = ab23ap23_input['arguments']
            ab23ap23_selected = all(
                ab23ap23_key in ab23ap23_c and
                type(ab23ap23_c[ab23ap23_key]) is type(ab23ap23_value) and
                ab23ap23_c[ab23ap23_key] == ab23ap23_value
                for ab23ap23_key, ab23ap23_value in
                (('primary', 181), ('secondary', 22), ('operation', None), ('view', 'energy-type')))
            ab23ap23_direction = ab23ap23_c.get('direction')
            ab23ap23_selected &= ab23ap23_direction in ('request', 'read-positive', 'write-positive')
            if ab23ap23_selected:
                ab23ap23_value = ab23ap23_raw.get('value', [])
                ab23ap23_f = {'state': 'incomplete', 'grade': 'Hypothesis'}
                if 'value' in ab23ap23_raw:
                    ab23ap23_f['raw'] = ab23ap23_value
                ab23ap23_expected['fields'] = {'value': ab23ap23_f}
                ab23ap23_expected['state'] = 'partial'
                if len(ab23ap23_value) == 1:
                    ab23ap23_v = ab23ap23_value[0]
                    ab23ap23_f['state'] = 'complete'
                    ab23ap23_expected['state'] = 'complete'
                    if ab23ap23_direction == 'request':
                        ab23ap23_f.update(number=ab23ap23_v, unmapped=True)
                    else:
                        # Division/remainder oracle independent of documented bit masks.
                        ab23ap23_f.update(low_six=ab23ap23_v % 64, calculation='Proven')
                        if ab23ap23_direction == 'read-positive':
                            ab23ap23_f.update(flag6=(ab23ap23_v // 64) % 2 == 1,
                                             flag7=ab23ap23_v >= 128)
                        else:
                            ab23ap23_f['unmodeled_high'] = (ab23ap23_v // 64) * 64
            self.ab23ap23_equal(ab23ap23_case['result'], ab23ap23_expected)

    def test_ab23ap23_exact_page_contract_and_tables(self):
        self.ab23ap23_check_page(self.ab23ap23_page)

    def test_ab23ap23_scenario_transitions(self):
        self.ab23ap23_check_scenarios(self.ab23ap23_data)

    def test_ab23ap23_literal_vectors_and_independent_axes(self):
        ab23ap23_cases = self.ab23ap23_data['scenarios']
        self.assertEqual(len(ab23ap23_cases), 67)
        self.assertEqual(len({ab23ap23_c['id'] for ab23ap23_c in ab23ap23_cases}), 67)
        self.assertTrue(all(ab23ap23_c['id'].startswith('ab23ap23_') for ab23ap23_c in ab23ap23_cases))
        ab23ap23_by_id = {ab23ap23_c['id']: ab23ap23_c for ab23ap23_c in ab23ap23_cases}
        for ab23ap23_v, ab23ap23_low, ab23ap23_f6, ab23ap23_f7, ab23ap23_high in AB23AP23_TUPLES:
            for ab23ap23_d in ('request', 'read_positive', 'write_positive'):
                ab23ap23_case = ab23ap23_by_id['ab23ap23_' + ab23ap23_d + '_' + str(ab23ap23_v)]
                self.assertEqual(ab23ap23_case['input']['fields']['value'], [ab23ap23_v])
                ab23ap23_f = ab23ap23_case['result']['fields']['value']
                if ab23ap23_d == 'request':
                    self.assertEqual(ab23ap23_f['number'], ab23ap23_v)
                else:
                    self.assertEqual(ab23ap23_f['low_six'], ab23ap23_low)
                    if ab23ap23_d == 'read_positive':
                        self.assertIs(ab23ap23_f['flag6'], ab23ap23_f6)
                        self.assertIs(ab23ap23_f['flag7'], ab23ap23_f7)
                    else:
                        self.assertEqual(ab23ap23_f['unmodeled_high'], ab23ap23_high)
        ab23ap23_axis_values = {
            'primary': [0, 182, None, False], 'secondary': [0, 23, None, False],
            'operation': ['ABSENT', 0, False, 16],
            'direction': ['ABSENT', None, 'write-request'],
            'view': ['ABSENT', None, 'meter'],
            'family': ['ABSENT', None, 0, False, {}, 'another-family'],
            'variant': ['ABSENT', None, 0, False, {}, ['another-variant']],
        }
        for ab23ap23_key, ab23ap23_values in ab23ap23_axis_values.items():
            for ab23ap23_index, ab23ap23_value in enumerate(ab23ap23_values):
                ab23ap23_context = ab23ap23_by_id['ab23ap23_' + ab23ap23_key + '_' + str(ab23ap23_index)]['input']['context']
                if ab23ap23_value == 'ABSENT':
                    self.assertNotIn(ab23ap23_key, ab23ap23_context)
                else:
                    self.ab23ap23_equal(ab23ap23_context[ab23ap23_key], ab23ap23_value)
        for ab23ap23_key in ('primary', 'secondary'):
            self.assertNotIn(ab23ap23_key, ab23ap23_by_id['ab23ap23_' + ab23ap23_key + '_absent']['input']['context'])
        ab23ap23_base = ab23ap23_by_id['ab23ap23_read_positive_193']['input']
        for ab23ap23_key in ('primary', 'secondary', 'operation', 'direction', 'view', 'family', 'variant'):
            ab23ap23_axis = [ab23ap23_c for ab23ap23_c in ab23ap23_cases
                             if ab23ap23_c['id'].startswith('ab23ap23_' + ab23ap23_key + '_')]
            self.assertGreaterEqual(len(ab23ap23_axis), 3)
            for ab23ap23_case in ab23ap23_axis:
                ab23ap23_c = ab23ap23_case['input']['context']
                self.ab23ap23_equal({ab23ap23_k: ab23ap23_v for ab23ap23_k, ab23ap23_v in ab23ap23_c.items() if ab23ap23_k != ab23ap23_key},
                                     {ab23ap23_k: ab23ap23_v for ab23ap23_k, ab23ap23_v in ab23ap23_base['context'].items() if ab23ap23_k != ab23ap23_key})
                self.ab23ap23_equal(ab23ap23_case['input']['fields'], ab23ap23_base['fields'])
        self.ab23ap23_equal([ab23ap23_by_id['ab23ap23_arguments_' + str(ab23ap23_i)]['input']['arguments'] for ab23ap23_i in range(6)],
                             [{}, {'opaque': None}, {'opaque': False}, {'opaque': 0}, {'opaque': []}, {'opaque': {'items': [0, False, None]}}])
        for ab23ap23_id, ab23ap23_raw in (('missing', {}), ('empty', {'value': []}), ('long', {'value': [193, 0]}), ('partial_sibling', {'value': [], 'opaque': [0, 255]})):
            self.ab23ap23_equal(ab23ap23_by_id['ab23ap23_' + ab23ap23_id]['result']['raw'], ab23ap23_raw)
            self.assertEqual(ab23ap23_by_id['ab23ap23_' + ab23ap23_id]['result']['state'], 'partial')

    def test_ab23ap23_admission_rejections(self):
        self.assertEqual(len(self.ab23ap23_data['rejections']), 36)
        for ab23ap23_case in self.ab23ap23_data['rejections']:
            with self.subTest(ab23ap23_id=ab23ap23_case['id']):
                self.assertEqual(ab23ap23_admission(ab23ap23_case['json']), ab23ap23_case['error'])
        self.assertEqual(ab23ap23_admission('{"context":{},"fields":{"sibling":[false]}}'), 'wrong-kind')
        for ab23ap23_text in ('{}', '{"context":{}}', '{"fields":{}}'):
            self.assertEqual(ab23ap23_admission(ab23ap23_text), 'wrong-kind')

    def test_ab23ap23_roundtrip_and_serialized_storage_independence(self):
        for ab23ap23_case in self.ab23ap23_data['scenarios']:
            ab23ap23_input = copy.deepcopy(ab23ap23_case['input'])
            ab23ap23_result = json.loads(json.dumps(ab23ap23_case['result']))
            ab23ap23_later = json.loads(json.dumps(ab23ap23_case['result']))
            self.ab23ap23_equal(ab23ap23_result, ab23ap23_case['result'])
            if type(ab23ap23_input['context'].get('variant')) is dict:
                ab23ap23_input['context']['variant']['changed'] = [False]
            ab23ap23_input['context']['variant'] = {'changed': [False]}
            if 'arguments' in ab23ap23_input:
                ab23ap23_input['arguments'].setdefault('nested', []).append(False)
            ab23ap23_input['fields'].setdefault('value', []).append(255)
            ab23ap23_input['fields']['value'] = [0]
            ab23ap23_result['context'].setdefault('nested', []).append(0)
            ab23ap23_result['raw'].setdefault('value', []).append(1)
            if 'value' in ab23ap23_result['fields'] and 'raw' in ab23ap23_result['fields']['value']:
                self.assertNotEqual(ab23ap23_result['raw']['value'], ab23ap23_result['fields']['value']['raw'])
            if 'arguments' in ab23ap23_result:
                ab23ap23_result['arguments']['opaque'] = {'changed': [False]}
            ab23ap23_again = json.loads(json.dumps(ab23ap23_case['result']))
            if 'value' in ab23ap23_again['fields'] and 'raw' in ab23ap23_again['fields']['value']:
                ab23ap23_raw_before = copy.deepcopy(ab23ap23_again['raw'])
                ab23ap23_again['fields']['value']['raw'].append(255)
                self.ab23ap23_equal(ab23ap23_again['raw'], ab23ap23_raw_before)
            if type(ab23ap23_again['context'].get('variant')) is dict:
                ab23ap23_again['context']['variant']['changed'] = [False]
            self.ab23ap23_equal(ab23ap23_later, ab23ap23_case['result'])
        # JSON decoding checks representation isolation only, not Go runtime copies.

    def test_ab23ap23_disposable_mutant_kills(self):
        self.ab23ap23_check_page(self.ab23ap23_page)
        # Each mutant is an owned fixture/page copy under .tmp, never a source edit.
        ab23ap23_mutants = [
            ('request_flags', 'request_193', {'flag6': True}),
            ('write_flags', 'write_positive_193', {'flag7': True}),
            ('drop_high', 'write_positive_193', {'unmodeled_high': 0}),
            ('high_zero', 'write_positive_193', {'state': 'incomplete'}),
            ('enum_label', 'request_193', {'label': 'invented'}),
            ('meter_selector', 'read_positive_193', {'meter_selector': 1}),
        ]
        (AB23AP23_ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='ab23ap23-', dir=AB23AP23_ROOT / '.tmp') as ab23ap23_tmp:
            for ab23ap23_name, ab23ap23_id, ab23ap23_patch in ab23ap23_mutants:
                ab23ap23_copy = copy.deepcopy(self.ab23ap23_data)
                next(ab23ap23_c for ab23ap23_c in ab23ap23_copy['scenarios'] if ab23ap23_c['id'] == 'ab23ap23_' + ab23ap23_id)['result']['fields']['value'].update(ab23ap23_patch)
                ab23ap23_path = Path(ab23ap23_tmp) / (ab23ap23_name + '.json')
                ab23ap23_path.write_text(json.dumps(ab23ap23_copy))
                with self.assertRaises(AssertionError, msg=ab23ap23_name):
                    self.ab23ap23_check_scenarios(json.loads(ab23ap23_path.read_text()))
            ab23ap23_copy = copy.deepcopy(self.ab23ap23_data)
            ab23ap23_zero = next(ab23ap23_c for ab23ap23_c in ab23ap23_copy['scenarios'] if ab23ap23_c['id'] == 'ab23ap23_operation_1')
            ab23ap23_selected = next(ab23ap23_c for ab23ap23_c in ab23ap23_copy['scenarios'] if ab23ap23_c['id'] == 'ab23ap23_read_positive_193')
            ab23ap23_zero['result']['fields'] = copy.deepcopy(ab23ap23_selected['result']['fields'])
            ab23ap23_zero['result']['state'] = 'complete'
            ab23ap23_path = Path(ab23ap23_tmp) / 'operation_zero.json'
            ab23ap23_path.write_text(json.dumps(ab23ap23_copy))
            with self.assertRaises(AssertionError):
                self.ab23ap23_check_scenarios(json.loads(ab23ap23_path.read_text()))
            for ab23ap23_old, ab23ap23_new in (('value & 63', 'value & 31'), ('| 193 | 193 | 1 |', '| 193 | 1 | 1 |'), ('"operation": null', '"operation": 0')):
                ab23ap23_path = Path(ab23ap23_tmp) / 'page.md'
                ab23ap23_path.write_text(self.ab23ap23_page.replace(ab23ap23_old, ab23ap23_new))
                with self.assertRaises(AssertionError):
                    self.ab23ap23_check_page(ab23ap23_path.read_text())


if __name__ == '__main__':
    unittest.main()
