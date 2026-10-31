"""Documentation contract tests; bounded oracles do not implement a runtime API."""
import copy
import json
import os
from pathlib import Path
import re
import unittest


class Ab17Ap17Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ab17ap17_root = Path(os.environ.get('AB17AP17_ROOT', Path(__file__).resolve().parents[1]))
        cls.ab17ap17_page = (cls.ab17ap17_root / 'architecture/ap18_b509_diagnostic_fields.md').read_text()
        cls.ab17ap17_fixture = json.loads((cls.ab17ap17_root / 'architecture/fixtures/ap18_b509_diagnostic_fields.json').read_text())
        cls.ab17ap17_table = json.loads(re.search(r'```json\n(.*?)\n```', cls.ab17ap17_page, re.S).group(1))

    def TestAb17Ap17ExactContract(self):
        ab17ap17_expected = {
            'signature': 'Ab17Ap17Evaluate(ab17ap17Input json.RawMessage) (json.RawMessage, error)',
            'package': 'vaillant', 'primary': 181, 'secondary': 9,
            'views': [[52, 'request', 'diagnostic-get', {'address': 4, 'count': 1}, {}],
                      [52, 'positive', 'diagnostic-get', {'address': 4, 'data': 'opaque'}, {'requested_address': 'optional u32'}],
                      [53, 'request', 'diagnostic-put', {'address': 4, 'data': 'opaque'}, {}],
                      [53, 'positive', 'diagnostic-put', {'status': 1}, {}]],
            'address_weights': [1, 256, 65536, 16777216], 'status_domain': [0, 6],
            'opaque_minimum': 0, 'opaque_maximum': None, 'recommendation': 10,
            'physical': 'Unknown', 'qualified': False, 'grade': 'Hypothesis', 'calculation': 'Proven',
            'unsupported_state': 'Unknown', 'incomplete_state': 'partial', 'complete_state': 'complete',
            'correlation': 'Unknown', 'status_labels': {}, 'count_data_relation': 'independent',
            'input_keys': ['context', 'fields', 'arguments'],
            'result_keys': ['context', 'raw', 'arguments', 'state', 'fields', 'physical', 'qualified'],
            'argument_kinds': {'requested_address': 'u32'},
            'errors': ['malformed JSON', 'duplicate key anywhere', 'wrong kind', 'fraction', 'out of range', 'missing required argument'],
            'copy': 'deep independent', 'context': 'unchanged', 'arguments': 'unchanged if supplied'
        }
        self.assertEqual(self.ab17ap17_table, ab17ap17_expected)
        self.assertEqual(self.ab17ap17_fixture['contract'], ab17ap17_expected)
        self.assertIs(self.ab17ap17_fixture['synthetic'], True)
        # Parse actual presentation rows, rather than merely finding vocabulary.
        ab17ap17_rows = [ab17ap17_line.split('|')[1:-1] for ab17ap17_line in self.ab17ap17_page.splitlines() if ab17ap17_line.startswith('| ')]
        ab17ap17_rows = [[ab17ap17_cell.strip() for ab17ap17_cell in ab17ap17_row] for ab17ap17_row in ab17ap17_rows]
        self.assertEqual(ab17ap17_rows[1:5], [
            ['34 / 52', 'request', 'diagnostic-get', 'address: 4 bytes; count: 1 byte', 'none required'],
            ['34 / 52', 'positive', 'diagnostic-get', 'address: 4 bytes; data: opaque array', 'requested_address: optional u32'],
            ['35 / 53', 'request', 'diagnostic-put', 'address: 4 bytes; data: opaque array', 'none required'],
            ['35 / 53', 'positive', 'diagnostic-put', 'status: 1 byte', 'none required']])
        self.assertEqual(ab17ap17_rows[6:10], [
            ['address', 'b0 + 256*b1 + 65536*b2 + 16777216*b3', '[120,86,52,18] = 305419896', 'Hypothesis; calculation Proven'],
            ['count', 'b0', '[0] = 0; [255] = 255', 'Hypothesis; calculation Proven'],
            ['data', 'unchanged bytes through end-of-data', 'unmodeled=true; length=len(data); [] is complete', 'Hypothesis'],
            ['status', 'b0; candidate_domain=(0 <= b0 <= 6)', '0,6 in domain; 7,255 outside; no label', 'Hypothesis; calculation Proven']])

    @staticmethod
    def ab17ap17_pairs(ab17ap17_pairs):
        ab17ap17_seen = {}
        for ab17ap17_key, ab17ap17_value in ab17ap17_pairs:
            if ab17ap17_key in ab17ap17_seen:
                raise ValueError('duplicate key anywhere')
            ab17ap17_seen[ab17ap17_key] = ab17ap17_value
        return ab17ap17_seen

    @staticmethod
    def ab17ap17_constant(ab17ap17_value):
        raise ValueError('non-JSON number')

    def ab17ap17_read(self, ab17ap17_text):
        # Strict parsing is a test oracle, not a production parser.
        ab17ap17_value = json.loads(ab17ap17_text, object_pairs_hook=self.ab17ap17_pairs, parse_constant=self.ab17ap17_constant)
        if type(ab17ap17_value) is not dict or type(ab17ap17_value.get('context')) is not dict or type(ab17ap17_value.get('fields')) is not dict:
            raise ValueError('wrong kind')
        if 'arguments' in ab17ap17_value and type(ab17ap17_value['arguments']) is not dict:
            raise ValueError('wrong kind')
        for ab17ap17_bytes in ab17ap17_value['fields'].values():
            if type(ab17ap17_bytes) is not list or any(type(ab17ap17_byte) is not int or not 0 <= ab17ap17_byte <= 255 for ab17ap17_byte in ab17ap17_bytes):
                raise ValueError('invalid bytes')
        ab17ap17_context = ab17ap17_value['context']
        if (ab17ap17_context.get('operation'), ab17ap17_context.get('direction'), ab17ap17_context.get('view')) == (52, 'positive', 'diagnostic-get'):
            ab17ap17_arguments = ab17ap17_value.get('arguments', {})
            if 'requested_address' in ab17ap17_arguments:
                ab17ap17_address = ab17ap17_arguments['requested_address']
                if type(ab17ap17_address) is not int or not 0 <= ab17ap17_address <= 4294967295:
                    raise ValueError('invalid u32')
        return ab17ap17_value

    def ab17ap17_assert_transition(self, ab17ap17_case):
        ab17ap17_input = self.ab17ap17_read(json.dumps(ab17ap17_case['input']))
        ab17ap17_result = ab17ap17_case['expected']
        self.assertEqual(set(ab17ap17_result), {'context', 'raw', 'state', 'fields', 'physical', 'qualified'} | ({'arguments'} if 'arguments' in ab17ap17_input else set()))
        self.assertEqual(ab17ap17_result['context'], ab17ap17_input['context'])
        self.assertEqual(ab17ap17_result['raw'], ab17ap17_input['fields'])
        self.assertEqual(ab17ap17_result['physical'], 'Unknown')
        self.assertIs(ab17ap17_result['qualified'], False)
        self.assertEqual('arguments' in ab17ap17_result, 'arguments' in ab17ap17_input)
        if 'arguments' in ab17ap17_input:
            self.assertEqual(ab17ap17_result['arguments'], ab17ap17_input['arguments'])
        ab17ap17_context = ab17ap17_input['context']
        ab17ap17_key = (ab17ap17_context.get('operation'), ab17ap17_context.get('direction'), ab17ap17_context.get('view'))
        ab17ap17_shapes = {(52, 'request', 'diagnostic-get'): {'address': 4, 'count': 1},
                            (52, 'positive', 'diagnostic-get'): {'address': 4, 'data': None},
                            (53, 'request', 'diagnostic-put'): {'address': 4, 'data': None},
                            (53, 'positive', 'diagnostic-put'): {'status': 1}}
        if ab17ap17_context.get('primary') != 181 or ab17ap17_context.get('secondary') != 9 or ab17ap17_key not in ab17ap17_shapes:
            self.assertEqual(ab17ap17_result['state'], 'Unknown')
            self.assertEqual(ab17ap17_result['fields'], {})
            return
        self.assertEqual(set(ab17ap17_result['fields']), set(ab17ap17_shapes[ab17ap17_key]))
        ab17ap17_partial = False
        for ab17ap17_name, ab17ap17_width in ab17ap17_shapes[ab17ap17_key].items():
            ab17ap17_semantic = ab17ap17_result['fields'][ab17ap17_name]
            self.assertEqual(ab17ap17_semantic['grade'], 'Hypothesis')
            if ab17ap17_name not in ab17ap17_input['fields']:
                self.assertEqual(ab17ap17_semantic, {'state': 'incomplete', 'grade': 'Hypothesis'})
                ab17ap17_partial = True
                continue
            ab17ap17_raw = ab17ap17_input['fields'][ab17ap17_name]
            self.assertEqual(ab17ap17_semantic['raw'], ab17ap17_raw)
            if ab17ap17_width is not None and len(ab17ap17_raw) != ab17ap17_width:
                self.assertEqual(ab17ap17_semantic, {'raw': ab17ap17_raw, 'state': 'incomplete', 'grade': 'Hypothesis'})
                ab17ap17_partial = True
                continue
            self.assertEqual(ab17ap17_semantic['state'], 'complete')
            self.assertNotIn('label', ab17ap17_semantic)
            if ab17ap17_name == 'data':
                self.assertIs(ab17ap17_semantic['unmodeled'], True)
                self.assertEqual(ab17ap17_semantic['length'], len(ab17ap17_raw))
                self.assertNotIn('number', ab17ap17_semantic)
            else:
                ab17ap17_number = int.from_bytes(bytes(ab17ap17_raw), 'little')
                self.assertEqual(ab17ap17_semantic['number'], ab17ap17_number)
                self.assertEqual(ab17ap17_semantic['calculation'], 'Proven')
                if ab17ap17_name == 'status':
                    self.assertIs(ab17ap17_semantic['candidate_domain'], ab17ap17_number in range(7))
        self.assertEqual(ab17ap17_result['state'], 'partial' if ab17ap17_partial else 'complete')

    def TestAb17Ap17Scenarios(self):
        ab17ap17_ids = set()
        self.assertGreaterEqual(len(self.ab17ap17_fixture['scenarios']), 20)
        for ab17ap17_case in self.ab17ap17_fixture['scenarios']:
            with self.subTest(ab17ap17_id=ab17ap17_case['id']):
                self.assertTrue(ab17ap17_case['id'].startswith('ab17ap17_'))
                self.assertNotIn(ab17ap17_case['id'], ab17ap17_ids)
                ab17ap17_ids.add(ab17ap17_case['id'])
                self.ab17ap17_assert_transition(ab17ap17_case)
                self.assertEqual(json.loads(json.dumps(ab17ap17_case)), ab17ap17_case)
        ab17ap17_by_id = {ab17ap17_case['id']: ab17ap17_case for ab17ap17_case in self.ab17ap17_fixture['scenarios']}
        self.assertEqual(ab17ap17_by_id['ab17ap17_count_0']['expected']['fields']['address']['number'], 305419896)
        self.assertEqual(ab17ap17_by_id['ab17ap17_count_255']['expected']['fields']['count']['number'], 255)
        self.assertEqual(ab17ap17_by_id['ab17ap17_opaque_52_11']['expected']['fields']['data']['length'], 11)
        self.assertEqual(ab17ap17_by_id['ab17ap17_opaque_52_11']['expected']['arguments']['requested_address'], 1)

    def TestAb17Ap17EverySelector(self):
        ab17ap17_base = copy.deepcopy(self.ab17ap17_fixture['scenarios'][0])
        for ab17ap17_name in ('primary', 'secondary', 'operation', 'direction', 'view'):
            for ab17ap17_value in (None, 0, False, 'other'):
                ab17ap17_case = copy.deepcopy(ab17ap17_base)
                ab17ap17_case['input']['context'][ab17ap17_name] = ab17ap17_value
                ab17ap17_case['expected']['context'][ab17ap17_name] = ab17ap17_value
                ab17ap17_case['expected'].update(state='Unknown', fields={})
                self.ab17ap17_assert_transition(ab17ap17_case)
            ab17ap17_case = copy.deepcopy(ab17ap17_base)
            del ab17ap17_case['input']['context'][ab17ap17_name]
            del ab17ap17_case['expected']['context'][ab17ap17_name]
            ab17ap17_case['expected'].update(state='Unknown', fields={})
            self.ab17ap17_assert_transition(ab17ap17_case)
        for ab17ap17_name in ('family', 'variant', 'opaque'):
            for ab17ap17_value in (None, 0, False, [], {'nested': [False]}):
                ab17ap17_case = copy.deepcopy(ab17ap17_base)
                ab17ap17_case['input']['context'][ab17ap17_name] = ab17ap17_value
                ab17ap17_case['expected']['context'][ab17ap17_name] = copy.deepcopy(ab17ap17_value)
                self.ab17ap17_assert_transition(ab17ap17_case)

    def TestAb17Ap17EveryFieldPartial(self):
        for ab17ap17_id in ('ab17ap17_count_0', 'ab17ap17_opaque_52_11', 'ab17ap17_opaque_53_11', 'ab17ap17_status_6'):
            ab17ap17_base = next(ab17ap17_case for ab17ap17_case in self.ab17ap17_fixture['scenarios'] if ab17ap17_case['id'] == ab17ap17_id)
            for ab17ap17_name, ab17ap17_raw in ab17ap17_base['input']['fields'].items():
                for ab17ap17_value in (None, [], [0] * (len(ab17ap17_raw) + 1)):
                    ab17ap17_case = copy.deepcopy(ab17ap17_base)
                    if ab17ap17_value is None:
                        del ab17ap17_case['input']['fields'][ab17ap17_name]
                        del ab17ap17_case['expected']['raw'][ab17ap17_name]
                        ab17ap17_semantic = {'state': 'incomplete', 'grade': 'Hypothesis'}
                    else:
                        ab17ap17_case['input']['fields'][ab17ap17_name] = ab17ap17_value
                        ab17ap17_case['expected']['raw'][ab17ap17_name] = copy.deepcopy(ab17ap17_value)
                        ab17ap17_semantic = {'state': 'incomplete', 'grade': 'Hypothesis', 'raw': copy.deepcopy(ab17ap17_value)}
                    if ab17ap17_name == 'data' and ab17ap17_value is not None:
                        ab17ap17_semantic.update(state='complete', length=len(ab17ap17_value), unmodeled=True)
                    else:
                        ab17ap17_case['expected']['state'] = 'partial'
                    ab17ap17_case['expected']['fields'][ab17ap17_name] = ab17ap17_semantic
                    self.ab17ap17_assert_transition(ab17ap17_case)

    def TestAb17Ap17Admission(self):
        ab17ap17_base = next(copy.deepcopy(ab17ap17_case['input']) for ab17ap17_case in self.ab17ap17_fixture['scenarios'] if ab17ap17_case['id'] == 'ab17ap17_opaque_52_11')
        for ab17ap17_text in ('{', 'null', '[]', '{"context":{},"context":{},"fields":{}}', '{"context":{},"fields":{},"arguments":{"opaque":{"x":1,"x":2}}}', '{"context":{},"fields":{"data":[NaN]}}'):
            with self.assertRaises((ValueError, TypeError)):
                self.ab17ap17_read(ab17ap17_text)
        for ab17ap17_name in ('context', 'fields', 'arguments'):
            for ab17ap17_value in (False, None, 0, [], 'object'):
                ab17ap17_input = copy.deepcopy(ab17ap17_base)
                ab17ap17_input[ab17ap17_name] = ab17ap17_value
                with self.assertRaises(ValueError):
                    self.ab17ap17_read(json.dumps(ab17ap17_input))
        for ab17ap17_case in self.ab17ap17_fixture['scenarios']:
            for ab17ap17_name in ab17ap17_case['input']['fields']:
                for ab17ap17_value in (False, None, 0, 'byte', [False], [None], ['0'], [1.5], [-1], [256]):
                    ab17ap17_input = copy.deepcopy(ab17ap17_case['input'])
                    ab17ap17_input['fields'][ab17ap17_name] = ab17ap17_value
                    with self.assertRaises(ValueError):
                        self.ab17ap17_read(json.dumps(ab17ap17_input))
        for ab17ap17_value in (False, None, [], '0', 1.5, -1, 4294967296):
            ab17ap17_input = copy.deepcopy(ab17ap17_base)
            ab17ap17_input['arguments']['requested_address'] = ab17ap17_value
            with self.assertRaises(ValueError):
                self.ab17ap17_read(json.dumps(ab17ap17_input))
        for ab17ap17_value in (0, 4294967295):
            ab17ap17_input = copy.deepcopy(ab17ap17_base)
            ab17ap17_input['arguments']['requested_address'] = ab17ap17_value
            self.assertEqual(self.ab17ap17_read(json.dumps(ab17ap17_input)), ab17ap17_input)
        for ab17ap17_value in (None, False, 0, [], {'nested': [False]}):
            ab17ap17_input = copy.deepcopy(ab17ap17_base)
            ab17ap17_input['arguments']['opaque'] = ab17ap17_value
            self.assertEqual(self.ab17ap17_read(json.dumps(ab17ap17_input)), ab17ap17_input)

    def TestAb17Ap17StorageDistinctions(self):
        # Only fixture storage independence is exercised; runtime ownership is unverified.
        ab17ap17_text = json.dumps(self.ab17ap17_fixture['scenarios'])
        ab17ap17_first = json.loads(ab17ap17_text)
        ab17ap17_second = json.loads(ab17ap17_text)
        ab17ap17_first[0]['input']['fields']['address'][0] = 0
        self.assertEqual(ab17ap17_first[0]['expected']['raw']['address'][0], 120)
        self.assertEqual(ab17ap17_second[0]['input']['fields']['address'][0], 120)
        ab17ap17_first[0]['expected']['raw']['address'][0] = 1
        self.assertEqual(ab17ap17_first[0]['expected']['fields']['address']['raw'][0], 120)
        ab17ap17_first[0]['expected']['context']['opaque']['items'][0] = False
        self.assertIsNone(ab17ap17_first[0]['input']['context']['opaque']['items'][0])
        ab17ap17_first[2]['expected']['arguments']['opaque']['enabled'] = True
        self.assertIs(ab17ap17_first[2]['input']['arguments']['opaque']['enabled'], False)
        for ab17ap17_case in ab17ap17_second:
            self.ab17ap17_assert_transition(ab17ap17_case)

    def TestAb17Ap17PermittedSemanticKeys(self):
        ab17ap17_flat = ' '.join(self.ab17ap17_page.split())
        ab17ap17_match = re.search(r'plus only applicable (.*?)\. calculation=Proven', ab17ap17_flat)
        self.assertIsNotNone(ab17ap17_match)
        ab17ap17_listed = set(re.split(r',\s*(?:or\s+)?|\s+or\s+', ab17ap17_match.group(1)))
        ab17ap17_permitted = ab17ap17_listed | {'raw', 'state', 'grade'}
        self.assertEqual(ab17ap17_listed, {'number', 'label', 'flags', 'reserved', 'unmodeled',
                                           'candidate_domain', 'calculation', 'length', 'alternatives'})
        for ab17ap17_case in self.ab17ap17_fixture['scenarios']:
            for ab17ap17_semantic in ab17ap17_case['expected']['fields'].values():
                self.assertLessEqual(set(ab17ap17_semantic), ab17ap17_permitted)


def load_tests(ab17ap17_loader, ab17ap17_tests, ab17ap17_pattern):
    # Standard unittest hook preserves the requested TestAb17Ap17 method prefix.
    return unittest.TestSuite(Ab17Ap17Contract(ab17ap17_name) for ab17ap17_name in sorted(dir(Ab17Ap17Contract)) if ab17ap17_name.startswith('TestAb17Ap17'))
