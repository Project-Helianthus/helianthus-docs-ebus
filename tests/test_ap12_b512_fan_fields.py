"""Independent documentation/scenario checks; no runtime API implementation."""
import copy
import json
from pathlib import Path
import re
import unittest

ab11ap11Root = Path(__file__).resolve().parents[1]
ab11ap11PagePath = ab11ap11Root / 'architecture/ap12-b512-fan-fields.md'
ab11ap11FixturePath = ab11ap11Root / 'architecture/fixtures/ap12_b512_fan_fields.json'


def ab11ap11ExpectedRows():
    # Independent constants: order distinguishes fan and temperature positions.
    return [
        ('fan', 11, 'request', 'fan1', 2, 'leu16', 'rpm', None),
        ('fan', 11, 'request', 'fan2', 2, 'leu16', 'rpm', None),
        ('fan', 11, 'request', 'relay', 1, 'relay', 'Unknown', None),
        ('fan', 11, 'positive', 'fan1', 2, 'leu16', 'rpm', None),
        ('fan', 11, 'positive', 'fan2', 2, 'leu16', 'rpm', None),
        ('fan', 11, 'positive', 'status', 1, 'status', 'Unknown', None),
        ('fan', 11, 'positive', 'temperature1', 2, 's16/16', 'Celsius', None),
        ('fan', 11, 'positive', 'temperature2', 2, 's16/16', 'Celsius', None),
        ('fan', 11, 'positive', 'temperature3', 2, 's16/16', 'Celsius', None),
        ('fan-control', 12, 'request', 'pulse', 1, 'u8', 'Unknown', 0),
        ('fan-control', 12, 'request', 'p', 1, 'u8', 'Unknown', 0),
        ('fan-control', 12, 'request', 'i', 1, 'u8', 'Unknown', 0),
        ('fan-control', 12, 'request', 'd', 1, 'u8', 'Unknown', 0),
        ('fan-control', 12, 'request', 'fan_count', 1, 'u8', 'Unknown', 0),
        ('fan-control', 12, 'request', 'minimum_pwm', 2, 's16/256', 'percent', 1.0),
        ('fan-control', 12, 'request', 'maximum_pwm', 2, 's16/256', 'percent', 1.0),
        ('fan-control', 12, 'positive', 'feedback', 1, 'feedback', 'Unknown', None),
        ('digital-air', 13, 'positive', 'digital', 1, 'digital', 'Unknown', 0),
        ('digital-air', 13, 'positive', 'temperature1', 2, 's16/16', 'Celsius', 0),
        ('digital-air', 13, 'positive', 'temperature2', 2, 's16/16', 'Celsius', 0),
        ('air-quality', 14, 'positive', 'temperature', 2, 's16/16', 'Celsius', 0),
        ('air-quality', 14, 'positive', 'humidity', 2, 'leu16/16', 'percent', 0),
        ('air-quality', 14, 'positive', 'air_quality', 2, 'leu16', 'Unknown', 0),
    ]


def ab11ap11ExpectedContract():
    return {
        'signature': 'Ab11Ap11Evaluate(ab11ap11Input json.RawMessage) (json.RawMessage, error)',
        'package': 'vaillant', 'primary': 181, 'secondary': 18,
        'physical': 'Unknown', 'qualified': False, 'grade': 'Hypothesis',
        'calculation': 'Proven',
        'arguments': {'required': [], 'known': {}, 'unknown': 'preserve'},
        'fields': [dict(zip(('view', 'operation', 'direction', 'name', 'width',
                             'codec', 'unit', 'default'), ab11ap11Row))
                   for ab11ap11Row in ab11ap11ExpectedRows()],
        'empty_views': [['digital-air', 13, 'request'], ['air-quality', 14, 'request']],
        'mappings': {'status': {'0': 'idle', '1': 'running', '255': 'fault'},
                     'feedback': {'1': 'accepted', 'other': 'rejected'},
                     'digital': {'0': False, '1': True, 'other': 'unmapped'},
                     'relay': {'0': '15V', '1': 'tray-heater-relay', 'reserved_mask': 252}},
        'pwm_domain': [-128, 127.99609375],
        'rules': {
            'input_required': ['context', 'fields'], 'input_optional': ['arguments'],
            'output_required': ['context', 'raw', 'state', 'fields', 'physical', 'qualified'],
            'output_optional': ['arguments'], 'arguments_presence': 'same_as_input',
            'raw_presence': 'omit_if_absent_preserve_if_present',
            'unknown_fields': 'raw_and_unmodeled', 'unknown_selectors': 'raw_only_Unknown',
            'invalid_input': 'error_no_result', 'duplicate_keys': 'reject_at_every_depth',
            'numeric_kinds': 'integral_not_boolean_no_coercion',
            'bounds': {'u8': [0, 255], 'u16': [0, 65535], 'u32': [0, 4294967295]},
            'supported_complete': 'complete', 'any_incomplete': 'partial',
            'unmapped_sibling': 'complete', 'storage': 'deep_independent_across_calls',
            'defaults': 'annotations_never_fill', 'minimum_maximum_order': 'not_enforced',
            'pwm_clip': None, 'humidity_cap': None,
            'family_grade': 'Hypothesis', 'calculation_grade': 'Proven',
            'physical': 'Unknown', 'qualified': False,
        },
    }


def ab11ap11FieldProjection(ab11ap11Row, ab11ap11Raw):
    """Bounded per-field test oracle, never a callable API emulator."""
    if ab11ap11Raw is None or len(ab11ap11Raw) != ab11ap11Row['width']:
        return {'state': 'incomplete'}
    ab11ap11Codec = ab11ap11Row['codec']
    ab11ap11Word = sum(ab11ap11Byte * (256 ** ab11ap11Index)
                      for ab11ap11Index, ab11ap11Byte in enumerate(ab11ap11Raw))
    if ab11ap11Codec == 'relay':
        return {'flags': {'bit0': 'tray-heater-relay' if ab11ap11Word & 1 else '15V',
                          'bit1': 'tray-heater-relay' if ab11ap11Word & 2 else '15V'},
                'reserved': ab11ap11Word & 252}
    if ab11ap11Codec == 'status':
        return ({'label': {0: 'idle', 1: 'running', 255: 'fault'}[ab11ap11Word]}
                if ab11ap11Word in (0, 1, 255) else {'state': 'unmapped'})
    if ab11ap11Codec == 'feedback':
        return {'label': 'accepted' if ab11ap11Word == 1 else 'rejected'}
    if ab11ap11Codec == 'digital':
        return {'number': bool(ab11ap11Word)} if ab11ap11Word < 2 else {'state': 'unmapped'}
    if ab11ap11Codec.startswith('s16'):
        # Signed byte construction differs from the page's subtraction formula.
        ab11ap11Word = int.from_bytes(bytes(ab11ap11Raw), 'little', signed=True)
    ab11ap11Divisor = int(ab11ap11Codec.split('/')[1]) if '/' in ab11ap11Codec else 1
    return {'number': ab11ap11Word / ab11ap11Divisor, 'unit': ab11ap11Row['unit']}


def ab11ap11SelectedRows(ab11ap11Contract, ab11ap11Context):
    if any(ab11ap11Context.get(ab11ap11Key) != ab11ap11Contract[ab11ap11Key]
           for ab11ap11Key in ('primary', 'secondary')):
        return None
    ab11ap11Key = [ab11ap11Context.get(ab11ap11Name)
                   for ab11ap11Name in ('view', 'operation', 'direction')]
    ab11ap11Rows = [ab11ap11Row for ab11ap11Row in ab11ap11Contract['fields']
                    if [ab11ap11Row[ab11ap11Name] for ab11ap11Name in
                        ('view', 'operation', 'direction')] == ab11ap11Key]
    return ab11ap11Rows if ab11ap11Rows or ab11ap11Key in ab11ap11Contract['empty_views'] else None


def ab11ap11UniquePairs(ab11ap11Pairs):
    ab11ap11Result = {}
    for ab11ap11Key, ab11ap11Value in ab11ap11Pairs:
        if ab11ap11Key in ab11ap11Result:
            raise ValueError('duplicate key')
        ab11ap11Result[ab11ap11Key] = ab11ap11Value
    return ab11ap11Result


class Ab11Ap11Contract(unittest.TestCase):
    def setUp(self):
        self.ab11ap11Data = json.loads(ab11ap11FixturePath.read_text())
        self.ab11ap11Page = ab11ap11PagePath.read_text()
        self.ab11ap11Contract = self.ab11ap11Data['contract']

    def TestAb11Ap11ExactDeclarationAndPageTable(self):
        self.assertEqual(self.ab11ap11Contract, ab11ap11ExpectedContract())
        ab11ap11Blocks = re.findall(r'```json\n(.*?)\n```', self.ab11ap11Page, re.S)
        self.assertEqual(len(ab11ap11Blocks), 1)
        self.assertEqual(json.loads(ab11ap11Blocks[0]), ab11ap11ExpectedContract())
        ab11ap11Rows = [tuple(ab11ap11Cell.strip() for ab11ap11Cell in ab11ap11Line.strip('|').split('|'))
                       for ab11ap11Line in self.ab11ap11Page.splitlines()
                       if ab11ap11Line.startswith('| ')][2:]
        self.assertEqual(ab11ap11Rows, [tuple('Unknown' if ab11ap11Value is None else str(ab11ap11Value)
                                             for ab11ap11Value in ab11ap11Row)
                                       for ab11ap11Row in ab11ap11ExpectedRows()])
        self.assertEqual(re.findall(r'func ([^\n]+)', self.ab11ap11Page),
                         [ab11ap11ExpectedContract()['signature']])

    def TestAb11Ap11ScenarioTransitions(self):
        self.assertGreaterEqual(len(self.ab11ap11Data['scenarios']), 24)
        ab11ap11Ids = set()
        for ab11ap11Case in self.ab11ap11Data['scenarios']:
            with self.subTest(case=ab11ap11Case['id']):
                self.assertTrue(ab11ap11Case['id'].startswith('ab11ap11'))
                self.assertNotIn(ab11ap11Case['id'], ab11ap11Ids)
                ab11ap11Ids.add(ab11ap11Case['id'])
                ab11ap11Input = ab11ap11Case['input']
                ab11ap11Rows = ab11ap11SelectedRows(self.ab11ap11Contract, ab11ap11Input['context'])
                if ab11ap11Rows is None:
                    self.assertEqual(ab11ap11Case['expected_state'], 'Unknown')
                    self.assertEqual(ab11ap11Case['expected_fields'], {})
                    continue
                ab11ap11Fields = {ab11ap11Row['name']: ab11ap11FieldProjection(
                    ab11ap11Row, ab11ap11Input['fields'].get(ab11ap11Row['name']))
                    for ab11ap11Row in ab11ap11Rows}
                self.assertEqual(set(ab11ap11Case['expected_fields']), set(ab11ap11Fields))
                self.assertEqual(ab11ap11Case['expected_state'], 'partial' if any(
                    ab11ap11Field.get('state') == 'incomplete' for ab11ap11Field in ab11ap11Fields.values()) else 'complete')
                for ab11ap11Name, ab11ap11Expected in ab11ap11Case['expected_fields'].items():
                    for ab11ap11Key, ab11ap11Value in ab11ap11Expected.items():
                        self.assertIn(ab11ap11Key, ab11ap11Fields[ab11ap11Name])
                        self.assertEqual(ab11ap11Fields[ab11ap11Name][ab11ap11Key], ab11ap11Value)
                        if type(ab11ap11Value) is bool:
                            self.assertIs(ab11ap11Fields[ab11ap11Name][ab11ap11Key], ab11ap11Value)

    def TestAb11Ap11IndependentArithmeticConstants(self):
        # Every numeric named field has independent low/high/sign controls.
        for ab11ap11Row in self.ab11ap11Contract['fields']:
            ab11ap11Codec = ab11ap11Row['codec']
            if ab11ap11Codec in ('relay', 'status', 'feedback', 'digital'):
                continue
            ab11ap11Controls = {
                'u8': [([0], 0), ([1], 1), ([255], 255)],
                'leu16': [([0, 0], 0), ([2, 1], 258), ([4, 3], 772), ([255, 255], 65535)],
                's16/16': [([0, 0], 0), ([16, 0], 1), ([240, 255], -1), ([0, 128], -2048), ([255, 127], 2047.9375)],
                's16/256': [([0, 0], 0), ([0, 1], 1), ([0, 128], -128), ([255, 127], 127.99609375)],
                'leu16/16': [([0, 0], 0), ([64, 6], 100), ([80, 6], 101), ([255, 255], 4095.9375)],
            }[ab11ap11Codec]
            for ab11ap11Raw, ab11ap11Expected in ab11ap11Controls:
                with self.subTest(field=ab11ap11Row['name'], direction=ab11ap11Row['direction'], raw=ab11ap11Raw):
                    self.assertEqual(ab11ap11FieldProjection(ab11ap11Row, ab11ap11Raw)['number'], ab11ap11Expected)
        ab11ap11Quality = self.ab11ap11Contract['fields'][-1]
        self.assertEqual(ab11ap11FieldProjection(ab11ap11Quality, [255, 255]),
                         {'number': 65535, 'unit': 'Unknown'})

    def TestAb11Ap11AllByteMappingsAndReservedBits(self):
        for ab11ap11Row in self.ab11ap11Contract['fields']:
            if ab11ap11Row['codec'] not in ('relay', 'status', 'feedback', 'digital'):
                continue
            for ab11ap11Byte in range(256):
                ab11ap11Result = ab11ap11FieldProjection(ab11ap11Row, [ab11ap11Byte])
                if ab11ap11Row['codec'] == 'relay':
                    self.assertEqual(ab11ap11Result['reserved'], 4 * (ab11ap11Byte // 4))
                    for ab11ap11Bit in (0, 1):
                        self.assertEqual(ab11ap11Result['flags']['bit'+str(ab11ap11Bit)],
                                         'tray-heater-relay' if (ab11ap11Byte // (2 ** ab11ap11Bit)) % 2 else '15V')
                elif ab11ap11Row['codec'] == 'feedback':
                    self.assertEqual(ab11ap11Result['label'] == 'accepted', ab11ap11Byte in {1})
                elif ab11ap11Row['codec'] == 'digital':
                    if ab11ap11Byte in (0, 1):
                        self.assertIs(ab11ap11Result['number'], (False, True)[ab11ap11Byte])
                    else:
                        self.assertEqual(ab11ap11Result, {'state': 'unmapped'})
                elif ab11ap11Byte not in (0, 1, 255):
                    self.assertEqual(ab11ap11Result, {'state': 'unmapped'})
                else:
                    self.assertEqual(ab11ap11Result['label'], {0:'idle', 1:'running', 255:'fault'}[ab11ap11Byte])

    def TestAb11Ap11EveryFieldPartialKeepsSiblings(self):
        for ab11ap11Row in self.ab11ap11Contract['fields']:
            ab11ap11Context = dict(primary=181, secondary=18, **{
                ab11ap11Key: ab11ap11Row[ab11ap11Key] for ab11ap11Key in ('view', 'operation', 'direction')})
            ab11ap11Rows = ab11ap11SelectedRows(self.ab11ap11Contract, ab11ap11Context)
            ab11ap11Fields = {ab11ap11Other['name']: [0] * ab11ap11Other['width'] for ab11ap11Other in ab11ap11Rows}
            for ab11ap11Raw in (None, [], [0] * (ab11ap11Row['width'] - 1), [0] * (ab11ap11Row['width'] + 1)):
                ab11ap11Changed = copy.deepcopy(ab11ap11Fields)
                if ab11ap11Raw is None:
                    del ab11ap11Changed[ab11ap11Row['name']]
                else:
                    ab11ap11Changed[ab11ap11Row['name']] = ab11ap11Raw
                for ab11ap11Other in ab11ap11Rows:
                    ab11ap11Result = ab11ap11FieldProjection(ab11ap11Other, ab11ap11Changed.get(ab11ap11Other['name']))
                    if ab11ap11Other['name'] == ab11ap11Row['name']:
                        self.assertEqual(ab11ap11Result, {'state': 'incomplete'})
                    else:
                        self.assertEqual(ab11ap11Result, ab11ap11FieldProjection(ab11ap11Other, ab11ap11Fields[ab11ap11Other['name']]))

    def TestAb11Ap11IdentityAxesAndOpaqueRoundTrips(self):
        for ab11ap11View, ab11ap11Operation in (('fan',11), ('fan-control',12), ('digital-air',13), ('air-quality',14)):
            for ab11ap11Direction in ('request', 'positive'):
                ab11ap11Context = dict(primary=181, secondary=18, operation=ab11ap11Operation,
                                       direction=ab11ap11Direction, view=ab11ap11View)
                self.assertIsNotNone(ab11ap11SelectedRows(self.ab11ap11Contract, ab11ap11Context))
                for ab11ap11Key in ('primary', 'secondary', 'operation', 'direction', 'view'):
                    for ab11ap11Value in (None, 0, 'other'):
                        ab11ap11Changed = dict(ab11ap11Context)
                        ab11ap11Changed[ab11ap11Key] = ab11ap11Value
                        self.assertIsNone(ab11ap11SelectedRows(self.ab11ap11Contract, ab11ap11Changed))
                    ab11ap11Changed = dict(ab11ap11Context)
                    del ab11ap11Changed[ab11ap11Key]
                    self.assertIsNone(ab11ap11SelectedRows(self.ab11ap11Contract, ab11ap11Changed))
                for ab11ap11Key in ('family', 'variant', 'opaque'):
                    for ab11ap11Value in (None, 0, False, '', [], {'nested':[False, 0, None]}):
                        ab11ap11Changed = dict(ab11ap11Context, **{ab11ap11Key: ab11ap11Value})
                        self.assertEqual(ab11ap11SelectedRows(self.ab11ap11Contract, ab11ap11Changed),
                                         ab11ap11SelectedRows(self.ab11ap11Contract, ab11ap11Context))
                        self.assertEqual(json.loads(json.dumps(ab11ap11Changed)), ab11ap11Changed)
                        self.assertIn(ab11ap11Key, json.loads(json.dumps(ab11ap11Changed)))

    def TestAb11Ap11CopyAndJSONDistinctionsAreScenarioProperties(self):
        # JSON/copy properties of examples, not claims about absent production code.
        for ab11ap11Case in self.ab11ap11Data['scenarios']:
            ab11ap11Original = copy.deepcopy(ab11ap11Case)
            ab11ap11Copy = json.loads(json.dumps(ab11ap11Case))
            self.assertEqual(ab11ap11Copy, ab11ap11Case)
            ab11ap11Copy['input']['context']['variant']['choice'] = True
            ab11ap11Copy['input']['fields']['unmodeled'] = [0]
            self.assertEqual(ab11ap11Case, ab11ap11Original)
        ab11ap11Samples = [{}, {'value':None}, {'value':0}, {'value':False}, {'value':[]}]
        self.assertEqual(len({json.dumps(ab11ap11Value) for ab11ap11Value in ab11ap11Samples}), 5)

    def TestAb11Ap11DuplicateAndMalformedJSONExamples(self):
        # Strict JSON parsing oracle only; production error behavior remains untested.
        for ab11ap11Text in ('{"context":{},"context":{}}', '{"fields":{"fan1":[],"fan1":[0]}}',
                             '{"arguments":{"x":{"v":0,"v":1}}}', '{', '{}{}', '[] trailing'):
            with self.assertRaises(ValueError):
                json.loads(ab11ap11Text, object_pairs_hook=ab11ap11UniquePairs)
        self.assertEqual(json.loads('{"context":{},"fields":{}}', object_pairs_hook=ab11ap11UniquePairs),
                         {'context':{}, 'fields':{}})

    def TestAb11Ap11FieldKindsAndArgumentJSONKinds(self):
        # Admission examples test a finite byte-domain predicate, not a runtime API.
        self.assertEqual(self.ab11ap11Data['invalid_byte_arrays'],
                         [None, False, 0, '00', [False], [True], [None], ['0'],
                          [0.5], [-1], [256], [[]], [{}]])
        self.assertEqual(self.ab11ap11Data['valid_byte_arrays'], [[], [0], [255], [0, 255]])
        for ab11ap11Array in self.ab11ap11Data['invalid_byte_arrays'] + self.ab11ap11Data['valid_byte_arrays']:
            ab11ap11Valid = isinstance(ab11ap11Array, list) and all(
                type(ab11ap11Byte) is int and 0 <= ab11ap11Byte <= 255 for ab11ap11Byte in ab11ap11Array)
            self.assertEqual(ab11ap11Valid, ab11ap11Array in self.ab11ap11Data['valid_byte_arrays']
                             and not any(type(ab11ap11Byte) is bool for ab11ap11Byte in
                                         (ab11ap11Array if isinstance(ab11ap11Array, list) else [])))
        for ab11ap11Value in (False, None, 0, '', [], [False, 0, None], {'nested':[False]}):
            ab11ap11Input = {'arguments': {'opaque': ab11ap11Value}}
            ab11ap11Copy = json.loads(json.dumps(ab11ap11Input))
            self.assertEqual(ab11ap11Copy, ab11ap11Input)
            self.assertIs(type(ab11ap11Copy['arguments']['opaque']), type(ab11ap11Value))


def load_tests(ab11ap11Loader, ab11ap11Tests, ab11ap11Pattern):
    # Standard-library discovery hook supports the prescribed TestAb11Ap11 prefix.
    ab11ap11Loader.testMethodPrefix = 'TestAb11Ap11'
    return ab11ap11Loader.loadTestsFromTestCase(Ab11Ap11Contract)
