"""Static API-contract tests; bounded oracles do not supply a runtime API."""
import copy
import json
from pathlib import Path
import re
import unittest

Ab19Ap19Root = Path(__file__).resolve().parents[1]
Ab19Ap19Page = Ab19Ap19Root / 'architecture/ap20_b51a_mirror_fields.md'
Ab19Ap19Fixture = Ab19Ap19Root / 'architecture/fixtures/ap20_b51a_mirror_fields.json'

# Independent constants, including asymmetric address bytes and reply extents.
Ab19Ap19Layouts = [
    (2, 'request', 'mirror-get', 'sequence', 3, 1, 'u8', 0, 0),
    (2, 'request', 'mirror-get', 'flags', 4, 1, 'bits', 1, 254),
    (2, 'request', 'mirror-get', 'length', 5, 1, 'u8', 0, 0),
    (2, 'request', 'mirror-get', 'address', 6, 2, 'le16', 0, 0),
    (2, 'positive', 'mirror-get', 'sequence', 3, 1, 'u8', 0, 0),
    (2, 'positive', 'mirror-get', 'status', 4, 1, 'alternatives', 1, 0),
    (2, 'positive', 'mirror-get', 'data', 5, '0..end', 'opaque', 0, 0),
    (3, 'request', 'mirror-put', 'sequence', 3, 1, 'u8', 0, 0),
    (3, 'request', 'mirror-put', 'flags', 4, 1, 'bits', 3, 252),
    (3, 'request', 'mirror-put', 'mirror_address', 5, 2, 'le16', 0, 0),
    (3, 'request', 'mirror-put', 'symbol_address', 7, 2, 'le16', 0, 0),
    (3, 'request', 'mirror-put', 'data', 9, '0..end', 'opaque', 0, 0),
    (3, 'positive', 'mirror-put', 'sequence', 3, 1, 'u8', 0, 0),
    (3, 'positive', 'mirror-put', 'flags', 4, 1, 'bits', 15, 240),
]
Ab19Ap19Bits = {
    (2, 'request'): ['triple-storage'],
    (3, 'request'): ['triple-storage', 'direct-update'],
    (3, 'positive'): ['not-written', 'invalid-symbol', 'invalid-parameter', 'storage-error'],
}
Ab19Ap19Bases = [
    {'sequence': [0], 'flags': [0], 'length': [3], 'address': [52, 18]},
    {'sequence': [255], 'status': [2], 'data': [17, 34]},
    {'sequence': [0], 'flags': [0], 'mirror_address': [52, 18], 'symbol_address': [120, 86], 'data': []},
    {'sequence': [255], 'flags': [0]},
]


def ab19ap19unique(ab19ap19pairs):
    ab19ap19object = {}
    for ab19ap19key, ab19ap19value in ab19ap19pairs:
        if ab19ap19key in ab19ap19object:
            raise ValueError('duplicate key')
        ab19ap19object[ab19ap19key] = ab19ap19value
    return ab19ap19object


def ab19ap19nonjson(ab19ap19value):
    raise ValueError('non-JSON constant')


def ab19ap19admission(ab19ap19text):
    """Test-only admission oracle; no semantic decoding or result production."""
    ab19ap19input = json.loads(ab19ap19text, object_pairs_hook=ab19ap19unique,
                              parse_constant=ab19ap19nonjson)
    if type(ab19ap19input) is not dict:
        raise ValueError('object required')
    for ab19ap19key in ('context', 'fields'):
        if type(ab19ap19input.get(ab19ap19key)) is not dict:
            raise ValueError('required object')
    if 'arguments' in ab19ap19input and type(ab19ap19input['arguments']) is not dict:
        raise ValueError('arguments object')
    for ab19ap19key in ('primary', 'secondary', 'operation'):
        if ab19ap19key in ab19ap19input['context']:
            ab19ap19value = ab19ap19input['context'][ab19ap19key]
            if ab19ap19value is not None and (type(ab19ap19value) is not int or not 0 <= ab19ap19value <= 255):
                raise ValueError('u8 selector or null')
    for ab19ap19key in ('direction', 'view'):
        if ab19ap19key in ab19ap19input['context']:
            ab19ap19value = ab19ap19input['context'][ab19ap19key]
            if ab19ap19value is not None and type(ab19ap19value) is not str:
                raise ValueError('string selector or null')
    for ab19ap19raw in ab19ap19input['fields'].values():
        if type(ab19ap19raw) is not list or any(type(ab19ap19byte) is not int or not 0 <= ab19ap19byte <= 255 for ab19ap19byte in ab19ap19raw):
            raise ValueError('byte array required')
    return ab19ap19input


class Ab19Ap19Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ab19ap19page = Ab19Ap19Page.read_text()
        cls.ab19ap19fixture = json.loads(Ab19Ap19Fixture.read_text(), object_pairs_hook=ab19ap19unique)
        cls.ab19ap19cases = {ab19ap19case['id']: ab19ap19case for ab19ap19case in cls.ab19ap19fixture['cases']}

    def TestAb19Ap19PageTablesAndSignature(self):
        ab19ap19blocks = re.findall(r'```go\n(.*?)\n```', self.ab19ap19page, re.S)
        self.assertEqual(ab19ap19blocks, ['func Ab19Ap19Evaluate(ab19ap19Input json.RawMessage) (json.RawMessage, error)'])
        ab19ap19rows = [tuple(ab19ap19cell.strip() for ab19ap19cell in ab19ap19line.strip('|').split('|')) for ab19ap19line in self.ab19ap19page.splitlines() if ab19ap19line.startswith('| ')]
        ab19ap19layoutrows = [ab19ap19row for ab19ap19row in ab19ap19rows if len(ab19ap19row) == 9 and ab19ap19row[0].isdigit()]
        self.assertEqual(ab19ap19layoutrows, [tuple(map(str, ab19ap19row)) for ab19ap19row in Ab19Ap19Layouts])
        self.assertEqual([ab19ap19row for ab19ap19row in ab19ap19rows if len(ab19ap19row) == 4 and ab19ap19row[1] in ('request', 'positive')],
                         [(str(ab19ap19op), ab19ap19direction, str(ab19ap19bit), ab19ap19name) for (ab19ap19op, ab19ap19direction), ab19ap19names in Ab19Ap19Bits.items() for ab19ap19bit, ab19ap19name in enumerate(ab19ap19names)])
        self.assertEqual([ab19ap19row for ab19ap19row in ab19ap19rows if len(ab19ap19row) == 4 and ab19ap19row[1] in ('complete', 'unmapped')],
                         [('0', 'complete', 'false', 'false'), ('1', 'complete', 'true', 'true'), ('2', 'unmapped', 'absent', 'false'), ('3', 'unmapped', 'absent', 'true'), ('4..255', 'unmapped', 'absent', 'bit0')])
        self.assertEqual([ab19ap19row for ab19ap19row in ab19ap19rows if len(ab19ap19row) == 3 and ab19ap19row[0] != 'admission or extent'], [
            ('invalid JSON or kind', 'error', 'no successful result'),
            ('unsupported context', 'Unknown', 'empty semantic fields'),
            ('missing required field', 'incomplete', 'no raw or number'),
            ('fixed field shorter than width', 'incomplete', 'retain raw only'),
            ('fixed field longer than width', 'incomplete', 'retain raw only'),
            ('fixed field exactly width', 'complete', 'apply declared decoder'),
            ('opaque explicit empty', 'complete', 'raw empty and unmodeled'),
            ('opaque explicit nonempty', 'complete', 'raw unchanged and unmodeled'),
            ('any incomplete sibling', 'partial', 'retain complete siblings'),
            ('all required fields complete', 'complete', 'retain unresolved alternatives'),
        ])
        # Exact clauses bind table arithmetic and states to the specified prose.
        for ab19ap19clause in ['`le16` is `raw[0] + 256 * raw[1]`; `u8` is `raw[0]`.',
                              '`raw[0] & reserved_mask`', 'state="Unknown"',
                              'A request length\nof 3 and a positive data array of length 2 remain 3 and 2.',
                              'none of these four views declares an interpreted argument or required argument.',
                              'no reset/01 correlation rule is\ntransferred to OP02/03.',
                              '65535 is an ordinary\nfull-range value, never an all-addresses token.']:
            self.assertIn(ab19ap19clause, self.ab19ap19page)

    def ab19ap19assert_case(self, ab19ap19case):
        ab19ap19input, ab19ap19out = ab19ap19case['input'], ab19ap19case['result']
        self.assertEqual(ab19ap19admission(json.dumps(ab19ap19input)), ab19ap19input)
        self.assertEqual(set(ab19ap19out), {'context', 'raw', 'state', 'fields', 'physical', 'qualified'} | ({'arguments'} if 'arguments' in ab19ap19input else set()))
        self.assertEqual(json.dumps(ab19ap19out['context'], sort_keys=True), json.dumps(ab19ap19input['context'], sort_keys=True))
        self.assertEqual(json.dumps(ab19ap19out['raw'], sort_keys=True), json.dumps(ab19ap19input['fields'], sort_keys=True))
        if 'arguments' in ab19ap19input:
            self.assertEqual(json.dumps(ab19ap19out['arguments'], sort_keys=True), json.dumps(ab19ap19input['arguments'], sort_keys=True))
        self.assertEqual(ab19ap19out['physical'], 'Unknown')
        self.assertIs(ab19ap19out['qualified'], False)
        ab19ap19context = ab19ap19input['context']
        ab19ap19rows = [ab19ap19row for ab19ap19row in Ab19Ap19Layouts if ab19ap19row[:3] == (ab19ap19context.get('operation'), ab19ap19context.get('direction'), ab19ap19context.get('view'))] if ab19ap19context.get('primary') == 181 and ab19ap19context.get('secondary') == 26 else []
        self.assertEqual(set(ab19ap19out['fields']), {ab19ap19row[3] for ab19ap19row in ab19ap19rows})
        ab19ap19incomplete = False
        for ab19ap19row in ab19ap19rows:
            ab19ap19name, ab19ap19width, ab19ap19decoder = ab19ap19row[3], ab19ap19row[5], ab19ap19row[6]
            ab19ap19field = ab19ap19out['fields'][ab19ap19name]
            ab19ap19raw = ab19ap19input['fields'].get(ab19ap19name)
            self.assertEqual(ab19ap19field['grade'], 'Hypothesis')
            if ab19ap19raw is None or (ab19ap19width != '0..end' and len(ab19ap19raw) != ab19ap19width):
                ab19ap19incomplete = True
                self.assertEqual(ab19ap19field, {'state': 'incomplete', 'grade': 'Hypothesis', **({'raw': ab19ap19raw} if ab19ap19raw is not None else {})})
                continue
            self.assertEqual(json.dumps(ab19ap19field['raw']), json.dumps(ab19ap19raw))
            self.assertEqual(ab19ap19field['state'], 'complete')
            ab19ap19keys = {'raw', 'state', 'grade'}
            if ab19ap19decoder == 'opaque':
                self.assertIs(ab19ap19field['unmodeled'], True)
                self.assertEqual(set(ab19ap19field), ab19ap19keys | {'unmodeled'})
                continue
            self.assertEqual(ab19ap19field['calculation'], 'Proven')
            ab19ap19keys.add('calculation')
            if ab19ap19decoder == 'bits':
                ab19ap19names = Ab19Ap19Bits[ab19ap19row[:2]]
                # Division/modulo oracle is independent of the specified bitwise formula.
                self.assertEqual(ab19ap19field['flags'], {ab19ap19name: bool((ab19ap19raw[0] // 2**ab19ap19bit) % 2) for ab19ap19bit, ab19ap19name in enumerate(ab19ap19names)})
                self.assertIs(type(ab19ap19field['reserved']), int)
                self.assertTrue(all(type(ab19ap19value) is bool for ab19ap19value in ab19ap19field['flags'].values()))
                self.assertEqual(ab19ap19field['reserved'], (ab19ap19raw[0] // 2**len(ab19ap19names)) * 2**len(ab19ap19names))
                ab19ap19keys.update(('flags', 'reserved'))
            else:
                self.assertIs(type(ab19ap19field['number']), int)
                self.assertEqual(ab19ap19field['number'], int.from_bytes(bytes(ab19ap19raw), 'little'))
                ab19ap19keys.add('number')
                if ab19ap19decoder == 'le16':
                    self.assertEqual(ab19ap19field['logical_validity'], 'Unknown')
                    ab19ap19keys.add('logical_validity')
                if ab19ap19decoder == 'alternatives':
                    ab19ap19value = ab19ap19raw[0]
                    if ab19ap19value < 2:
                        self.assertIs(type(ab19ap19field['alternatives']['whole_boolean']['label']), bool)
                    self.assertIs(type(ab19ap19field['alternatives']['out_of_area']['flags']['out-of-area']), bool)
                    self.assertEqual(ab19ap19field['alternatives'], {
                        'whole_boolean': ({'state': 'complete', 'label': (False, True)[ab19ap19value]} if ab19ap19value < 2 else {'state': 'unmapped'}),
                        'out_of_area': {'state': 'complete', 'flags': {'out-of-area': ab19ap19value % 2 == 1}},
                    })
                    ab19ap19keys.add('alternatives')
            self.assertEqual(set(ab19ap19field), ab19ap19keys)
        self.assertEqual(ab19ap19out['state'], ('partial' if ab19ap19incomplete else 'complete') if ab19ap19rows else 'Unknown')
        self.assertEqual(json.loads(json.dumps(ab19ap19out)), ab19ap19out)

    def TestAb19Ap19EveryScenarioAndIndependentConstants(self):
        self.assertEqual(self.ab19ap19fixture['schema'], 'ab19ap19-mirror-fields')
        self.assertEqual(len(self.ab19ap19cases), len(self.ab19ap19fixture['cases']))
        self.assertEqual(len(self.ab19ap19cases), 245)
        for ab19ap19case in self.ab19ap19cases.values():
            with self.subTest(ab19ap19case=ab19ap19case['id']):
                self.assertTrue(ab19ap19case['id'].startswith('ab19ap19'))
                self.ab19ap19assert_case(ab19ap19case)
        for ab19ap19index, ab19ap19fields in enumerate(Ab19Ap19Bases):
            self.assertEqual(self.ab19ap19cases[f'ab19ap19_{ab19ap19index}_base']['input']['fields'], ab19ap19fields)
        self.assertEqual(self.ab19ap19cases['ab19ap19_2_base']['result']['fields']['mirror_address']['number'], 4660)
        self.assertEqual(self.ab19ap19cases['ab19ap19_2_base']['result']['fields']['symbol_address']['number'], 22136)
        for ab19ap19index, ab19ap19name in ((0, 'address'), (2, 'mirror_address'), (2, 'symbol_address')):
            self.assertEqual(self.ab19ap19cases[f'ab19ap19_{ab19ap19index}_{ab19ap19name}_maximum']['result']['fields'][ab19ap19name]['number'], 65535)

    def TestAb19Ap19IndependentFieldTransitions(self):
        for ab19ap19index, ab19ap19base in enumerate(Ab19Ap19Bases):
            ab19ap19control = self.ab19ap19cases[f'ab19ap19_{ab19ap19index}_base']
            for ab19ap19name in ab19ap19base:
                for ab19ap19suffix in ('missing', 'empty', 'zero', 'overlong', 'maximum'):
                    ab19ap19case = self.ab19ap19cases[f'ab19ap19_{ab19ap19index}_{ab19ap19name}_{ab19ap19suffix}']
                    self.assertEqual(ab19ap19case['input']['context'], ab19ap19control['input']['context'])
                    for ab19ap19sibling in ab19ap19base:
                        if ab19ap19sibling != ab19ap19name:
                            self.assertEqual(ab19ap19case['result']['fields'][ab19ap19sibling], ab19ap19control['result']['fields'][ab19ap19sibling])
                if len(ab19ap19base[ab19ap19name]) == 2:
                    for ab19ap19suffix, ab19ap19number in [('low', 1), ('high', 256)]:
                        ab19ap19field = self.ab19ap19cases[f'ab19ap19_{ab19ap19index}_{ab19ap19name}_{ab19ap19suffix}']['result']['fields'][ab19ap19name]
                        if ab19ap19name != 'data':
                            self.assertEqual(ab19ap19field['number'], ab19ap19number)
            for ab19ap19suffix, ab19ap19value in [('minimum', 0), ('maximum', 255)]:
                self.assertEqual(self.ab19ap19cases[f'ab19ap19_{ab19ap19index}_sequence_{ab19ap19suffix}']['result']['fields']['sequence']['number'], ab19ap19value)
            if 'flags' in ab19ap19base:
                for ab19ap19bit in range(8):
                    ab19ap19case = self.ab19ap19cases[f'ab19ap19_{ab19ap19index}_flags_bit{ab19ap19bit}']
                    self.assertEqual(ab19ap19case['input']['fields']['flags'], [2**ab19ap19bit])
                    self.ab19ap19assert_case(ab19ap19case)
        self.assertEqual(self.ab19ap19fixture['pairs'], [{'id': 'ab19ap19_independent_extents', 'request': 'ab19ap19_0_base', 'positive': 'ab19ap19_1_base'}])
        ab19ap19request = self.ab19ap19cases['ab19ap19_0_base']['result']
        ab19ap19positive = self.ab19ap19cases['ab19ap19_1_base']['result']
        self.assertEqual(ab19ap19request['fields']['length']['number'], 3)
        self.assertEqual(ab19ap19positive['fields']['data']['raw'], [17, 34])
        self.assertEqual([ab19ap19request['fields']['sequence']['number'], ab19ap19positive['fields']['sequence']['number']], [0, 255])
        self.assertEqual([ab19ap19request['context']['direction'], ab19ap19positive['context']['direction']], ['request', 'positive'])

    def TestAb19Ap19ContextAndArgumentsCoverage(self):
        for ab19ap19index in range(4):
            ab19ap19base = self.ab19ap19cases[f'ab19ap19_{ab19ap19index}_base']
            for ab19ap19key in ('primary', 'secondary', 'operation', 'direction', 'view', 'family', 'variant'):
                for ab19ap19suffix in ('other', 'missing', 'null'):
                    ab19ap19case = self.ab19ap19cases[f'ab19ap19_{ab19ap19index}_context_{ab19ap19key}_{ab19ap19suffix}']
                    self.assertEqual(ab19ap19case['input']['fields'], ab19ap19base['input']['fields'])
                    ab19ap19expected = copy.deepcopy(ab19ap19base['input']['context'])
                    if ab19ap19suffix == 'missing':
                        del ab19ap19expected[ab19ap19key]
                    else:
                        ab19ap19expected[ab19ap19key] = {'primary': 180, 'secondary': 25, 'operation': 6, 'direction': 'negative', 'view': 'configured-register', 'family': 'other-family', 'variant': {'kind': 1}}[ab19ap19key] if ab19ap19suffix == 'other' else None
                    self.assertEqual(ab19ap19case['result']['context'], ab19ap19expected)
                    self.assertEqual(ab19ap19case['result']['state'], 'complete' if ab19ap19key in ('family', 'variant') else 'Unknown')
            for ab19ap19key in ('primary', 'secondary', 'operation'):
                self.assertEqual(self.ab19ap19cases[f'ab19ap19_{ab19ap19index}_context_{ab19ap19key}_zero']['result']['context'][ab19ap19key], 0)
            for ab19ap19suffix, ab19ap19arguments in [('empty', {}), ('zero', {'opaque': 0}), ('false', {'opaque': False}), ('null', {'opaque': None}), ('nested', {'opaque': {'items': [False, 0, None]}}), ('selectors', {'register': 255, 'selector': [5, 255, 51]})]:
                ab19ap19case = self.ab19ap19cases[f'ab19ap19_{ab19ap19index}_arguments_{ab19ap19suffix}']
                self.assertEqual(json.dumps(ab19ap19case['result']['arguments']), json.dumps(ab19ap19arguments))
                self.assertEqual(ab19ap19case['result']['fields'], ab19ap19base['result']['fields'])
            self.assertNotIn('arguments', ab19ap19base['result'])
            ab19ap19opaque = self.ab19ap19cases[f'ab19ap19_{ab19ap19index}_opaque']['result']
            self.assertEqual(ab19ap19opaque['context']['extension'], {'values': [False, 0, None]})
            self.assertEqual(ab19ap19opaque['raw']['selector'], [5, 255, 51])
            self.assertNotIn('selector', ab19ap19opaque['fields'])

    def TestAb19Ap19AdmissionRejectsWithValidControls(self):
        self.assertEqual(len(self.ab19ap19fixture['rejections']), 117)
        for ab19ap19case in self.ab19ap19fixture['rejections']:
            with self.subTest(ab19ap19case=ab19ap19case['id']):
                with self.assertRaises(ValueError):
                    ab19ap19admission(ab19ap19case['text'])
        for ab19ap19index, ab19ap19fields in enumerate(Ab19Ap19Bases):
            ab19ap19control = self.ab19ap19cases[f'ab19ap19_{ab19ap19index}_base']['input']
            self.assertEqual(ab19ap19admission(json.dumps(ab19ap19control)), ab19ap19control)
            for ab19ap19field in ab19ap19fields:
                for ab19ap19suffix in ('bool', 'fraction', 'negative', 'overflow', 'null', 'string', 'scalar', 'nested'):
                    self.assertIn(f'ab19ap19_reject_{ab19ap19index}_{ab19ap19field}_{ab19ap19suffix}', {ab19ap19case['id'] for ab19ap19case in self.ab19ap19fixture['rejections']})
        for ab19ap19key in ('primary', 'secondary', 'operation', 'direction', 'view'):
            for ab19ap19value in (False, [], {}):
                ab19ap19input = copy.deepcopy(self.ab19ap19cases['ab19ap19_0_base']['input'])
                ab19ap19input['context'][ab19ap19key] = ab19ap19value
                with self.assertRaises(ValueError):
                    ab19ap19admission(json.dumps(ab19ap19input))
        for ab19ap19text in ('null', '[]', '{}', '{"context":{},"fields":{},"arguments":null}', '{"context":{},"fields":{"x":[NaN]}}'):
            with self.assertRaises(ValueError):
                ab19ap19admission(ab19ap19text)

    def TestAb19Ap19NestedStorageAndRoundTrips(self):
        # Serialized examples test storage separation, not a nonexistent Go implementation.
        ab19ap19case = self.ab19ap19cases['ab19ap19_2_arguments_nested']
        ab19ap19input = copy.deepcopy(ab19ap19case['input'])
        ab19ap19first = json.loads(json.dumps(ab19ap19case['result']))
        ab19ap19later = json.loads(json.dumps(ab19ap19case['result']))
        ab19ap19input['fields']['mirror_address'][0] = 0
        ab19ap19input['context']['variant']['kind'] = 99
        ab19ap19input['arguments']['opaque']['items'][0] = True
        self.assertEqual(ab19ap19first, ab19ap19case['result'])
        ab19ap19first['raw']['mirror_address'][0] = 0
        self.assertEqual(ab19ap19first['fields']['mirror_address']['raw'], [52, 18])
        ab19ap19first['fields']['mirror_address']['raw'][1] = 0
        ab19ap19first['context']['variant']['kind'] = 99
        ab19ap19first['arguments']['opaque']['items'].append(99)
        self.assertEqual(ab19ap19later, ab19ap19case['result'])
        for ab19ap19index in range(4):
            ab19ap19values = [self.ab19ap19cases[f'ab19ap19_{ab19ap19index}_context_primary_{ab19ap19suffix}']['result']['context'] for ab19ap19suffix in ('missing', 'null', 'zero')]
            self.assertEqual(len({json.dumps(ab19ap19value, sort_keys=True) for ab19ap19value in ab19ap19values}), 3)


def load_tests(ab19ap19loader, ab19ap19tests, ab19ap19pattern):
    ab19ap19local_loader = unittest.TestLoader()
    ab19ap19local_loader.testMethodPrefix = 'TestAb19Ap19'
    return ab19ap19local_loader.loadTestsFromTestCase(Ab19Ap19Contract)


if __name__ == '__main__':
    unittest.main()
