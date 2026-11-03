"""Publication contract checks; no production interpreter is available here."""
import copy
import json
from pathlib import Path
import re
import unittest

ab21ao21Root = Path(__file__).resolve().parents[1]


def ab21ao21Unique(ab21ao21Pairs):
    ab21ao21Value = {}
    for ab21ao21Key, ab21ao21Item in ab21ao21Pairs:
        if ab21ao21Key in ab21ao21Value:
            raise ValueError('duplicate object key')
        ab21ao21Value[ab21ao21Key] = ab21ao21Item
    return ab21ao21Value


def ab21ao21Load(ab21ao21Text):
    return json.loads(ab21ao21Text, object_pairs_hook=ab21ao21Unique)


# Independent finite oracle: these are fixed expected tuples, not a JSON API
# implementation. No arbitrary input is interpreted or accepted by this suite.
ab21ao21Selectors = (0, 1, 2, 3, 4, 5, 6, 7, 8, 170)
ab21ao21Selection = [
    [0, 'request', 'none'], [1, 'request', 'opaque'],
    [2, 'request', 'none'], [3, 'request', 'opaque'],
    [4, 'request', 'opaque'], [5, 'request', 'opaque'],
    [6, 'request', 'opaque'], [7, 'request', 'opaque'],
    [8, 'request', 'address-opaque'], [170, 'request', 'none'],
    [0, 'positive', 'Unknown'], [1, 'positive', 'Unknown'],
    [2, 'positive', 'Unknown'], [3, 'positive', 'opaque'],
    [4, 'positive', 'Unknown'], [5, 'positive', 'Unknown'],
    [6, 'positive', 'prefix-only'], [7, 'positive', 'Unknown'],
    [8, 'positive', 'Unknown'], [170, 'positive', 'opaque'],
]
ab21ao21Axes = [
    ['request03_data', 3, 'request', [0, 0, 0, 0], 3],
    ['request08_address', 8, 'request', [0, 0, 0, 0, 65], 3],
    ['request08_data', 8, 'request', [0, 0, 0, 127, 0], 4],
    ['positive03_data', 3, 'positive', [0, 0, 0, 0], 3],
    ['positiveaa_data', 170, 'positive', [0, 0, 0, 0], 3],
    ['positive06_tail', 6, 'positive', [0, 0, 0, 0], 3],
]
ab21ao21Examples = [
    ['ab21ao21_request03', 3, 'request', [0, 0, 0, 0, 255, 65],
     'Hypothesis', {'opaque': {'raw': [0, 255, 65], 'state': 'Hypothesis'}}],
    ['ab21ao21_request08', 8, 'request', [0, 0, 0, 127, 0, 255],
     'Hypothesis', {'slave_address': {'raw': [127], 'state': 'Hypothesis'},
                    'opaque': {'raw': [0, 255], 'state': 'Hypothesis'}}],
    ['ab21ao21_positive03', 3, 'positive', [0, 0, 0, 0, 255, 65],
     'Hypothesis', {'opaque': {'raw': [0, 255, 65], 'state': 'Hypothesis'}}],
    ['ab21ao21_positiveaa', 170, 'positive', [0, 0, 0, 0, 255, 65],
     'Hypothesis', {'opaque': {'raw': [0, 255, 65], 'state': 'Hypothesis'}}],
    ['ab21ao21_positive06tail', 6, 'positive', [0, 0, 0, 0, 255],
     'Hypothesis', {'declared_form': {'raw': [], 'state': 'Hypothesis', 'label': 'prefix-only'},
                    'unmodelled': {'raw': [0, 255], 'state': 'Unknown'}}],
    ['ab21ao21_positive01crc', 1, 'positive', [0, 0, 0, 165], 'Unknown', {}],
]


def ab21ao21Boundaries():
    ab21ao21Context = {'primary': 181, 'secondary': 25, 'operation': 3, 'direction': 'request',
                       'view': 'logical-body', 'family': 'synthetic-family', 'variant': 0}
    ab21ao21Raw = {'logical_object': [0, 0, 0, 0, 255, 65]}
    ab21ao21Semantic = {'opaque': {'raw': [0, 255, 65], 'state': 'Hypothesis'}}
    ab21ao21Base = {'context': ab21ao21Context, 'fields': ab21ao21Raw}
    ab21ao21Output = {'context': ab21ao21Context, 'raw': ab21ao21Raw, 'state': 'Hypothesis',
                       'fields': ab21ao21Semantic, 'physical': 'Unknown', 'qualified': False}
    ab21ao21Rows = [['ab21ao21_control', copy.deepcopy(ab21ao21Base), copy.deepcopy(ab21ao21Output)]]
    for ab21ao21Name, ab21ao21Value, ab21ao21State in [
        ('primary', 182, 'Unknown'), ('secondary', 26, 'Unknown'), ('operation', 9, 'Unknown'),
        ('direction', 'other', 'Unknown'), ('view', 'other', 'Unknown'),
        ('family', {'opaque': [0, 255]}, 'Hypothesis'),
        ('variant', {'opaque': False}, 'Hypothesis'),
        ('extension', {'nested': [0, {}, False]}, 'Hypothesis')]:
        ab21ao21Input = copy.deepcopy(ab21ao21Base)
        ab21ao21Expected = copy.deepcopy(ab21ao21Output)
        ab21ao21Input['context'][ab21ao21Name] = copy.deepcopy(ab21ao21Value)
        ab21ao21Expected['context'][ab21ao21Name] = copy.deepcopy(ab21ao21Value)
        ab21ao21Expected['state'] = ab21ao21State
        if ab21ao21State == 'Unknown':
            ab21ao21Expected['fields'] = {}
        ab21ao21Rows.append(['ab21ao21_context_' + ab21ao21Name, ab21ao21Input, ab21ao21Expected])
    for ab21ao21Position in (0, 1, 2):
        ab21ao21Input = copy.deepcopy(ab21ao21Base)
        ab21ao21Expected = copy.deepcopy(ab21ao21Output)
        ab21ao21Input['fields']['logical_object'][ab21ao21Position] = 255
        ab21ao21Expected['raw']['logical_object'][ab21ao21Position] = 255
        ab21ao21Rows.append(['ab21ao21_leading_' + str(ab21ao21Position), ab21ao21Input, ab21ao21Expected])
    for ab21ao21Name, ab21ao21RawValue, ab21ao21State, ab21ao21Fields in [
        ('missing', {}, 'partial', {}), ('empty', {'logical_object': []}, 'partial', {}),
        ('empty_opaque', {'logical_object': [0, 0, 0]}, 'Hypothesis',
         {'opaque': {'raw': [], 'state': 'Hypothesis'}}),
        ('unknown_sibling', {'logical_object': [0, 0, 0, 0, 255, 65], 'extra': [255, 0]},
         'Hypothesis', ab21ao21Semantic)]:
        ab21ao21Input = copy.deepcopy(ab21ao21Base)
        ab21ao21Input['fields'] = copy.deepcopy(ab21ao21RawValue)
        ab21ao21Expected = copy.deepcopy(ab21ao21Output)
        ab21ao21Expected.update(raw=copy.deepcopy(ab21ao21RawValue), state=ab21ao21State,
                               fields=copy.deepcopy(ab21ao21Fields))
        ab21ao21Rows.append(['ab21ao21_' + ab21ao21Name, ab21ao21Input, ab21ao21Expected])
    ab21ao21Input = copy.deepcopy(ab21ao21Base)
    ab21ao21Expected = copy.deepcopy(ab21ao21Output)
    ab21ao21Input['arguments'] = {}
    ab21ao21Expected['arguments'] = {}
    ab21ao21Rows.append(['ab21ao21_empty_arguments', ab21ao21Input, ab21ao21Expected])
    return ab21ao21Rows


def ab21ao21Errors():
    ab21ao21Base = ab21ao21Boundaries()[0][1]
    ab21ao21RawErrors = ['{', '{"context":{},"context":{}}',
                         '{"context":{"family":{"x":0,"x":1}}}', '[]', 'null']
    ab21ao21Edits = []
    for ab21ao21Key in ('context', 'fields', 'arguments'):
        for ab21ao21Value in (None, [], 0, 'x'):
            ab21ao21Edits.append(([ab21ao21Key], ab21ao21Value))
    for ab21ao21Key in ('primary', 'secondary', 'operation'):
        for ab21ao21Value in (True, 1.0, '3', None):
            ab21ao21Edits.append((['context', ab21ao21Key], ab21ao21Value))
    ab21ao21Edits.extend([(['context', 'direction'], 0), (['context', 'view'], 0)])
    for ab21ao21Value in (None, 0, '00', [True], [1.0], [-1], [256], ['0'], [None]):
        ab21ao21Edits.append((['fields', 'logical_object'], ab21ao21Value))
    for ab21ao21Path, ab21ao21Value in ab21ao21Edits:
        ab21ao21Input = copy.deepcopy(ab21ao21Base)
        if len(ab21ao21Path) == 1:
            ab21ao21Input[ab21ao21Path[0]] = ab21ao21Value
        else:
            ab21ao21Input[ab21ao21Path[0]][ab21ao21Path[1]] = ab21ao21Value
        ab21ao21RawErrors.append(json.dumps(ab21ao21Input, separators=(',', ':')))
    for ab21ao21Key in ('primary', 'secondary', 'operation', 'direction', 'view'):
        ab21ao21Input = copy.deepcopy(ab21ao21Base)
        del ab21ao21Input['context'][ab21ao21Key]
        ab21ao21RawErrors.append(json.dumps(ab21ao21Input, separators=(',', ':')))
    ab21ao21Input = copy.deepcopy(ab21ao21Base)
    ab21ao21Input['arguments'] = {'flag': 0}
    ab21ao21RawErrors.append(json.dumps(ab21ao21Input, separators=(',', ':')))
    ab21ao21Input = copy.deepcopy(ab21ao21Base)
    ab21ao21Input['context']['operation'] = 9
    ab21ao21Input['fields']['extra'] = [256]
    ab21ao21RawErrors.append(json.dumps(ab21ao21Input, separators=(',', ':')))
    return [[f'ab21ao21_error_{ab21ao21N}', ab21ao21Text, 'error', None]
            for ab21ao21N, ab21ao21Text in enumerate(ab21ao21RawErrors)]


def ab21ao21Contract():
    return {
        'boundary_cases': ab21ao21Boundaries(),
        'error_cases': ab21ao21Errors(),
        'api': {'package': 'vaillant', 'signature': 'Ab21Ao21Interpret(ab21ao21Input json.RawMessage) (json.RawMessage, error)',
                'view': 'logical-body', 'primary': 181, 'secondary': 25,
                'directions': ['request', 'positive'], 'arguments': {}},
        'grades': {'semantic': 'Hypothesis', 'physical': 'Unknown', 'qualified': False,
                   'numeric_results': [], 'calculation': 'Proven only for independently exact numeric calculations; none declared here'},
        'selection': copy.deepcopy(ab21ao21Selection),
        'field_table': {
            'opaque': {'offset': 3, 'request08_offset': 4, 'encoding': 'bytes', 'minimum': 0,
                       'maximum': None, 'empty_acceptance': 'Unknown'},
            'slave_address': {'offset': 3, 'width': 1, 'encoding': 'raw byte'},
            'declared_form': {'raw': [], 'label': 'prefix-only', 'physical_completeness': 'Unknown'},
            'unmodelled': {'state': 'Unknown', 'encoding': 'bytes'}},
        'states': {'complete_selected': 'Hypothesis', 'short_selected': 'partial',
                   'unresolved': 'Unknown', 'unknown_sibling': 'preserve complete independent fields'},
        'finite_cases': {'tuple_columns': ['id', 'operation', 'direction', 'logical_object', 'state', 'fields'],
                         'lengths': [0, 1, 2, 3, 4, 5], 'length_carrier': [0, 0, 0, 127, 0],
                         'byte_axes': copy.deepcopy(ab21ao21Axes), 'byte_values': list(range(256)),
                         'examples': copy.deepcopy(ab21ao21Examples)},
        'identity_axes': [['primary', 182, 'Unknown'], ['secondary', 26, 'Unknown'],
                          ['operation', 9, 'Unknown'], ['direction', 'other', 'Unknown'],
                          ['view', 'other', 'Unknown'], ['family', {'opaque': [0, 255]}, 'Hypothesis'],
                          ['variant', {'opaque': False}, 'Hypothesis']],
        'presence': {'missing_logical_object': 'partial', 'empty_logical_object': 'partial',
                     'zero_logical_object': 'error', 'unknown_raw_field': 'preserve',
                     'missing_arguments': 'omit', 'empty_arguments': {}, 'unknown_argument': 'error'},
        'errors': ['malformed JSON', 'duplicate object key at any depth',
                   'non-object root/context/fields/arguments', 'missing required context key',
                   'non-integer primary/secondary/operation', 'non-string direction/view',
                   'non-array raw field', 'non-integer byte', 'byte outside 0..255', 'undeclared argument'],
        'ownership': 'independent deep copies of context, raw and supplied arguments; no shared state across calls',
        'selection_rule': 'explicit context only; first three logical positions opaque; no family, name or length inference',
        'unknowns': ['CRC coordinates except declared opaque forms', 'CRC algorithm', 'correlation',
                     'transport maximum', 'programming effect', 'effects', 'persistence', 'native support',
                     'accepted emptiness', 'unlimited carrier'],
    }


def ab21ao21ExpectedCases():
    ab21ao21Cases = []
    # Fixed length outcomes for each policy. Address-at-3 has a different
    # partial boundary; the complete address survives an empty data slice.
    ab21ao21Outcomes = {
        'opaque': [('partial', {})] * 3 + [
            ('Hypothesis', {'opaque': {'raw': [], 'state': 'Hypothesis'}}),
            ('Hypothesis', {'opaque': {'raw': [127], 'state': 'Hypothesis'}}),
            ('Hypothesis', {'opaque': {'raw': [127, 0], 'state': 'Hypothesis'}})],
        'none': [('partial', {})] * 3 + [('Hypothesis', {}),
            ('Hypothesis', {'unmodelled': {'raw': [127], 'state': 'Unknown'}}),
            ('Hypothesis', {'unmodelled': {'raw': [127, 0], 'state': 'Unknown'}})],
        'address-opaque': [('partial', {})] * 4 + [
            ('Hypothesis', {'slave_address': {'raw': [127], 'state': 'Hypothesis'},
                            'opaque': {'raw': [], 'state': 'Hypothesis'}}),
            ('Hypothesis', {'slave_address': {'raw': [127], 'state': 'Hypothesis'},
                            'opaque': {'raw': [0], 'state': 'Hypothesis'}})],
        'Unknown': [('Unknown', {})] * 6,
        'prefix-only': [('partial', {})] * 3 + [
            ('Hypothesis', {'declared_form': {'raw': [], 'state': 'Hypothesis', 'label': 'prefix-only'}}),
            ('Hypothesis', {'declared_form': {'raw': [], 'state': 'Hypothesis', 'label': 'prefix-only'},
                            'unmodelled': {'raw': [127], 'state': 'Unknown'}}),
            ('Hypothesis', {'declared_form': {'raw': [], 'state': 'Hypothesis', 'label': 'prefix-only'},
                            'unmodelled': {'raw': [127, 0], 'state': 'Unknown'}})],
    }
    for ab21ao21Operation, ab21ao21Direction, ab21ao21Policy in ab21ao21Selection:
        for ab21ao21Length, (ab21ao21State, ab21ao21Fields) in enumerate(ab21ao21Outcomes[ab21ao21Policy]):
            ab21ao21Cases.append([
                f'ab21ao21_{ab21ao21Direction}_{ab21ao21Operation:02x}_length_{ab21ao21Length}',
                ab21ao21Operation, ab21ao21Direction, [0, 0, 0, 127, 0][:ab21ao21Length],
                ab21ao21State, copy.deepcopy(ab21ao21Fields)])
    ab21ao21Cases.extend(copy.deepcopy(ab21ao21Examples))
    for ab21ao21Tag, ab21ao21Operation, ab21ao21Direction, ab21ao21Base, ab21ao21Offset in ab21ao21Axes:
        for ab21ao21Byte in range(256):
            ab21ao21Raw = ab21ao21Base.copy()
            ab21ao21Raw[ab21ao21Offset] = ab21ao21Byte
            # Enumerated byte-axis oracle: no API dispatch or admission code.
            ab21ao21Fields = {
                'request03_data': {'opaque': {'raw': [ab21ao21Byte], 'state': 'Hypothesis'}},
                'request08_address': {'slave_address': {'raw': [ab21ao21Byte], 'state': 'Hypothesis'},
                                     'opaque': {'raw': [65], 'state': 'Hypothesis'}},
                'request08_data': {'slave_address': {'raw': [127], 'state': 'Hypothesis'},
                                  'opaque': {'raw': [ab21ao21Byte], 'state': 'Hypothesis'}},
                'positive03_data': {'opaque': {'raw': [ab21ao21Byte], 'state': 'Hypothesis'}},
                'positiveaa_data': {'opaque': {'raw': [ab21ao21Byte], 'state': 'Hypothesis'}},
                'positive06_tail': {'declared_form': {'raw': [], 'state': 'Hypothesis', 'label': 'prefix-only'},
                                    'unmodelled': {'raw': [ab21ao21Byte], 'state': 'Unknown'}},
            }[ab21ao21Tag]
            ab21ao21Cases.append([f'ab21ao21_{ab21ao21Tag}_{ab21ao21Byte}', ab21ao21Operation,
                                   ab21ao21Direction, ab21ao21Raw, 'Hypothesis', ab21ao21Fields])
    return ab21ao21Cases


class TestAb21Ao21OpaqueViews(unittest.TestCase):
    def ab21ao21AssertJSONEqual(self, ab21ao21Actual, ab21ao21Expected):
        # Canonical JSON preserves bool/int/float distinctions at every depth.
        self.assertEqual(json.dumps(ab21ao21Actual, sort_keys=True).encode(),
                         json.dumps(ab21ao21Expected, sort_keys=True).encode())

    def setUp(self):
        self.ab21ao21Page = (ab21ao21Root / 'architecture/ao22_b519_opaque_views.md').read_text()
        self.ab21ao21Fixture = ab21ao21Load((ab21ao21Root / 'architecture/fixtures/ao22_b519_opaque_views.json').read_text())
        ab21ao21Match = re.search(r'<!-- ab21ao21-contract -->\s*```json\n(.*?)\n```\s*<!-- /ab21ao21-contract -->', self.ab21ao21Page, re.S)
        self.assertIsNotNone(ab21ao21Match)
        self.ab21ao21PageContract = ab21ao21Load(ab21ao21Match[1])

    def TestAb21Ao21ExactPageAndFixtureContract(self):
        self.ab21ao21AssertJSONEqual(self.ab21ao21PageContract, ab21ao21Contract())
        self.assertEqual(set(self.ab21ao21Fixture), {'ab21ao21_contract', 'ab21ao21_cases'})
        self.ab21ao21AssertJSONEqual(self.ab21ao21Fixture['ab21ao21_contract'], ab21ao21Contract())

    def TestAb21Ao21EveryFiniteTuple(self):
        self.ab21ao21AssertJSONEqual(self.ab21ao21Fixture['ab21ao21_cases'], ab21ao21ExpectedCases())
        self.assertEqual(len(self.ab21ao21Fixture['ab21ao21_cases']), 1662)
        self.assertEqual(len({ab21ao21Row[0] for ab21ao21Row in self.ab21ao21Fixture['ab21ao21_cases']}), 1662)

    def TestAb21Ao21ProseJSONExamples(self):
        ab21ao21Blocks = re.findall(r'```json\n(.*?)\n```', self.ab21ao21Page, re.S)
        self.assertEqual(len(ab21ao21Blocks), 3)
        self.ab21ao21AssertJSONEqual(ab21ao21Load(ab21ao21Blocks[0]), {
            'context': {'primary': 181, 'secondary': 25, 'operation': 8, 'direction': 'request',
                        'view': 'logical-body', 'family': 'synthetic-family', 'variant': 0},
            'fields': {'logical_object': [0, 0, 0, 127, 0, 255]}, 'arguments': {}})
        self.ab21ao21AssertJSONEqual(ab21ao21Load(ab21ao21Blocks[1]), {
            'slave_address': {'raw': [127], 'state': 'Hypothesis'},
            'opaque': {'raw': [0, 255], 'state': 'Hypothesis'}})

    def TestAb21Ao21BoundaryAndErrorVectors(self):
        self.ab21ao21AssertJSONEqual(self.ab21ao21PageContract['boundary_cases'], ab21ao21Boundaries())
        self.ab21ao21AssertJSONEqual(self.ab21ao21PageContract['error_cases'], ab21ao21Errors())
        self.assertEqual(len(self.ab21ao21PageContract['boundary_cases']), 17)
        self.assertEqual(len(self.ab21ao21PageContract['error_cases']), 47)

    def TestAb21Ao21RoundTripOfPublishedTuples(self):
        self.ab21ao21AssertJSONEqual(ab21ao21Load(json.dumps(self.ab21ao21Fixture)), self.ab21ao21Fixture)
        self.ab21ao21AssertJSONEqual(ab21ao21Load(json.dumps(self.ab21ao21PageContract)), self.ab21ao21PageContract)

    def TestAb21Ao21DuplicateAndMalformedPublicationJSON(self):
        # These exercise the artifact parser, not production API rejection.
        for ab21ao21Bad in ('{', '{"a":0,"a":1}', '{"a":{"b":0,"b":1}}'):
            with self.subTest(ab21ao21Bad=ab21ao21Bad):
                with self.assertRaises(ValueError):
                    ab21ao21Load(ab21ao21Bad)

    def TestAb21Ao21ContractMutationKills(self):
        # Each control passes first, then a single publication predicate changes.
        self.ab21ao21AssertJSONEqual(self.ab21ao21PageContract, ab21ao21Contract())
        ab21ao21Changes = [
            ('ascii', lambda ab21ao21C: ab21ao21C['field_table']['opaque'].update(encoding='ASCII')),
            ('u32', lambda ab21ao21C: ab21ao21C['field_table']['opaque'].update(encoding='u32')),
            ('crc-guess', lambda ab21ao21C: ab21ao21C['selection'][11].__setitem__(2, 'opaque')),
            ('selector-alias', lambda ab21ao21C: ab21ao21C['selection'][2].__setitem__(0, 0)),
            ('missing-alternative', lambda ab21ao21C: ab21ao21C['selection'].pop()),
            ('maximum', lambda ab21ao21C: ab21ao21C['field_table']['opaque'].update(maximum=255)),
            ('physical-empty', lambda ab21ao21C: ab21ao21C['field_table']['declared_form'].update(physical_completeness='empty')),
            ('native-promotion', lambda ab21ao21C: ab21ao21C['grades'].update(physical='Proven', qualified=True)),
        ]
        for ab21ao21Name, ab21ao21Change in ab21ao21Changes:
            with self.subTest(ab21ao21Name=ab21ao21Name):
                ab21ao21Mutant = copy.deepcopy(self.ab21ao21PageContract)
                ab21ao21Change(ab21ao21Mutant)
                with self.assertRaises(AssertionError):
                    self.ab21ao21AssertJSONEqual(ab21ao21Mutant, ab21ao21Contract())

    def TestAb21Ao21TupleMutationKills(self):
        ab21ao21Control = self.ab21ao21Fixture['ab21ao21_cases']
        self.ab21ao21AssertJSONEqual(ab21ao21Control, ab21ao21ExpectedCases())
        # Changed field, missing zero, missing FF, and discarded unexpected tail.
        for ab21ao21Index, ab21ao21Field, ab21ao21Value in (
                (120, 'opaque', [0, 255, 66]), (120, 'opaque', [255, 65]),
                (120, 'opaque', [0, 65]), (124, 'unmodelled', [])):
            with self.subTest(ab21ao21Index=ab21ao21Index, ab21ao21Value=ab21ao21Value):
                ab21ao21Mutant = copy.deepcopy(ab21ao21Control)
                ab21ao21Mutant[ab21ao21Index][5][ab21ao21Field]['raw'] = ab21ao21Value
                with self.assertRaises(AssertionError):
                    self.ab21ao21AssertJSONEqual(ab21ao21Mutant, ab21ao21ExpectedCases())

    def TestAb21Ao21ByteTypeMutationKills(self):
        ab21ao21Control = self.ab21ao21Fixture['ab21ao21_cases']
        self.ab21ao21AssertJSONEqual(ab21ao21Control, ab21ao21ExpectedCases())
        # Mutate input, output, and both together; numeric equality must not
        # admit JSON booleans or floats in any published byte position.
        for ab21ao21Index, ab21ao21Position, ab21ao21Value in (
                (120, 3, False), (120, 3, 0.0),
                (127, 3, True), (127, 3, 1.0)):
            for ab21ao21Side in ('input', 'output', 'both'):
                with self.subTest(ab21ao21Value=ab21ao21Value, ab21ao21Side=ab21ao21Side):
                    ab21ao21Mutant = copy.deepcopy(ab21ao21Control)
                    ab21ao21Row = ab21ao21Mutant[ab21ao21Index]
                    if ab21ao21Side in ('input', 'both'):
                        ab21ao21Row[3][ab21ao21Position] = ab21ao21Value
                    if ab21ao21Side in ('output', 'both'):
                        ab21ao21Row[5]['opaque']['raw'][0] = ab21ao21Value
                    with self.assertRaises(AssertionError):
                        self.ab21ao21AssertJSONEqual(ab21ao21Mutant, ab21ao21ExpectedCases())

    def TestAb21Ao21EachIdentityAndPresencePredicateMutation(self):
        for ab21ao21Key in ('identity_axes', 'presence', 'errors', 'ownership', 'selection_rule', 'states'):
            ab21ao21Original = self.ab21ao21PageContract[ab21ao21Key]
            ab21ao21Count = len(ab21ao21Original) if isinstance(ab21ao21Original, (list, dict)) else 1
            for ab21ao21Index in range(ab21ao21Count):
                with self.subTest(ab21ao21Key=ab21ao21Key, ab21ao21Index=ab21ao21Index):
                    ab21ao21Mutant = copy.deepcopy(self.ab21ao21PageContract)
                    ab21ao21Value = ab21ao21Mutant[ab21ao21Key]
                    if isinstance(ab21ao21Value, list):
                        ab21ao21Value.pop(ab21ao21Index)
                    elif isinstance(ab21ao21Value, dict):
                        del ab21ao21Value[list(ab21ao21Value)[ab21ao21Index]]
                    else:
                        ab21ao21Mutant[ab21ao21Key] = 'changed'
                    with self.assertRaises(AssertionError):
                        self.ab21ao21AssertJSONEqual(ab21ao21Mutant, ab21ao21Contract())


def load_tests(ab21ao21Loader, ab21ao21Tests, ab21ao21Pattern):
    ab21ao21Loader.testMethodPrefix = 'TestAb21Ao21'
    return ab21ao21Loader.loadTestsFromTestCase(TestAb21Ao21OpaqueViews)
