"""Finite documentation oracle; does not implement or invoke the Go interpreter."""
import copy as ab03ao03Copy
import json as ab03ao03Json
from pathlib import Path as Ab03Ao03Path
import re as ab03ao03Re
import unittest as ab03ao03Unittest

ab03ao03Root = Ab03Ao03Path(__file__).resolve().parents[1]
ab03ao03Context = {
    'primary': 181, 'secondary': 6, 'operation': 17,
    'direction': 'request', 'view': 'parameter-union',
    'family': 'synthetic-family', 'variant': 'synthetic-variant',
}
ab03ao03Contract = {
    'api': 'Ab03Ao03Interpret(ab03ao03Input json.RawMessage) (json.RawMessage, error)',
    'package': 'vaillant',
    'selection': {'primary': 181, 'secondary': 6, 'operation': 17,
                  'direction': 'request', 'view': 'parameter-union'},
    'opaque_keys': [0, 1, 2, 4, 5],
    'scalar_keys': [3, 6, 7, 8, 9, 32, 33, 34, 35, 36, 37],
    'boolean_key': 10, 'boolean_labels': {'0': 'no', '1': 'yes'},
    'semantic_grade': 'Hypothesis', 'physical': 'Unknown', 'qualified': False,
    'empty_sequence': 'representable-only', 'arguments': {},
    'states': ['complete', 'partial', 'Unknown'],
    'field_states': ['Hypothesis', 'incomplete', 'width-conflict', 'unmapped'],
    'numeric': 'exact unsigned byte only for complete scalar or mapped Boolean; calculation Proven',
    'missing_value': 'omit semantic field; partial',
    'unknown_selection': 'empty semantic fields; Unknown',
    'errors': 'error and no successful result',
    'copy': 'independent deep copies on every call',
    'transport': 'isolated value; no offset, termination, minimum or maximum established',
}


def ab03ao03Oracle():
    """Build fixed expected tuples by ID; never interpret an artifact input."""
    ab03ao03Rows = {}

    def ab03ao03Row(ab03ao03Id, ab03ao03Key, ab03ao03Value,
                    ab03ao03State='complete', ab03ao03Semantic=None,
                    ab03ao03Patch=None, ab03ao03Raw=None, ab03ao03Arguments=False):
        ab03ao03Ctx = dict(ab03ao03Context, **(ab03ao03Patch or {}))
        ab03ao03Bytes = ({'key': ab03ao03Key, 'value': ab03ao03Value}
                         if ab03ao03Raw is None else ab03ao03Raw)
        ab03ao03Input = {'context': ab03ao03Ctx, 'fields': ab03ao03Bytes}
        ab03ao03Output = {
            'context': ab03ao03Copy.deepcopy(ab03ao03Ctx),
            'raw': ab03ao03Copy.deepcopy(ab03ao03Bytes),
            'state': ab03ao03State, 'fields': {}, 'physical': 'Unknown', 'qualified': False,
        }
        if ab03ao03Semantic is not None:
            ab03ao03Output['fields']['value'] = dict(raw=ab03ao03Value, **ab03ao03Semantic)
        if ab03ao03Arguments:
            ab03ao03Input['arguments'] = {}
            ab03ao03Output['arguments'] = {}
        ab03ao03Id = 'ab03ao03' + ab03ao03Id
        ab03ao03Rows[ab03ao03Id] = {
            'id': ab03ao03Id, 'input': ab03ao03Input, 'expected': ab03ao03Output,
        }

    for ab03ao03Key in (0, 1, 2, 4, 5):
        ab03ao03Row('Opaque' + str(ab03ao03Key), [ab03ao03Key], [0, 170, 255],
                    ab03ao03Semantic={'state': 'Hypothesis'})
    for ab03ao03Key in (3, 6, 7, 8, 9, 32, 33, 34, 35, 36, 37):
        ab03ao03Row('Scalar' + str(ab03ao03Key), [ab03ao03Key], [127],
                    ab03ao03Semantic={'state': 'Hypothesis', 'number': 127, 'calculation': 'Proven'})
    for ab03ao03Value, ab03ao03Label in ((0, 'no'), (1, 'yes')):
        ab03ao03Row('Boolean' + str(ab03ao03Value), [10], [ab03ao03Value],
                    ab03ao03Semantic={'state': 'Hypothesis', 'number': ab03ao03Value,
                                      'label': ab03ao03Label, 'calculation': 'Proven'})
    ab03ao03Row('Boolean2', [10], [2], 'Unknown', {'state': 'unmapped'})
    for ab03ao03Key in (31, 38, 255):
        ab03ao03Row('UnknownKey' + str(ab03ao03Key), [ab03ao03Key], [0, 170, 255], 'Unknown')
    for ab03ao03Key in (3, 6, 7, 8, 9, 10, 32, 33, 34, 35, 36, 37):
        ab03ao03Row('Empty' + str(ab03ao03Key), [ab03ao03Key], [], 'partial',
                    {'state': 'incomplete'})
        ab03ao03Row('Wide' + str(ab03ao03Key), [ab03ao03Key], [0, 170], 'partial',
                    {'state': 'width-conflict'})
    ab03ao03Row('Key3Tail', [3], [0, 170, 255], 'partial', {'state': 'width-conflict'})
    ab03ao03Row('OpaqueEmpty', [2], [], ab03ao03Semantic={'state': 'Hypothesis'})
    ab03ao03Row('ScalarZero', [3], [0], ab03ao03Semantic={
        'state': 'Hypothesis', 'number': 0, 'calculation': 'Proven'})
    ab03ao03Row('ScalarMax', [3], [255], ab03ao03Semantic={
        'state': 'Hypothesis', 'number': 255, 'calculation': 'Proven'})
    for ab03ao03Axis, ab03ao03Value in (
            ('primary', 180), ('secondary', 7), ('operation', 18),
            ('direction', 'response'), ('view', 'other')):
        ab03ao03Row('Axis' + ab03ao03Axis.title(), [2], [0, 170, 255], 'Unknown',
                    ab03ao03Patch={ab03ao03Axis: ab03ao03Value})
    for ab03ao03Axis in ('family', 'variant'):
        ab03ao03Row('Opaque' + ab03ao03Axis.title(), [2], [0, 170, 255],
                    ab03ao03Semantic={'state': 'Hypothesis'},
                    ab03ao03Patch={ab03ao03Axis: {'opaque': [0, 'alternative', False]}})
    ab03ao03Row('ExtraContext', [2], [0, 170, 255],
                ab03ao03Semantic={'state': 'Hypothesis'},
                ab03ao03Patch={'extension': {'nested': [1, 2]}})
    for ab03ao03Id, ab03ao03Extra in (('ExtraRaw', [255, 0]), ('EmptyRawSibling', [])):
        ab03ao03Row(ab03ao03Id, [2], [0, 170, 255],
                    ab03ao03Semantic={'state': 'Hypothesis'},
                    ab03ao03Raw={'key': [2], 'value': [0, 170, 255], 'extension': ab03ao03Extra})
    ab03ao03Row('MissingValue', [2], [], 'partial', ab03ao03Raw={'key': [2]})
    ab03ao03Row('MissingKey', [], [0], 'partial', ab03ao03Raw={'value': [0]})
    ab03ao03Row('EmptyKey', [], [0], 'partial')
    ab03ao03Row('WideKey', [2, 3], [0], 'partial')
    ab03ao03Row('EmptyFields', [], [], 'partial', ab03ao03Raw={})
    ab03ao03Row('EmptyArguments', [2], [0, 170, 255],
                ab03ao03Semantic={'state': 'Hypothesis'}, ab03ao03Arguments=True)
    return ab03ao03Rows


def ab03ao03Errors():
    ab03ao03Result = {
        'Malformed': '{',
        'DuplicateTop': '{"context":{},"context":{},"fields":{}}',
        'DuplicateContext': '{"context":{"primary":181,"primary":181},"fields":{}}',
        'DuplicateField': '{"context":{},"fields":{"key":[2],"key":[3]}}',
        'DuplicateArgument': '{"context":{},"fields":{},"arguments":{"x":0,"x":1}}',
        'RootArray': '[]', 'RootNull': 'null',
    }
    for ab03ao03Id, ab03ao03Patch in (
        ('MissingContext', {'context': 'DELETE'}), ('MissingFields', {'fields': 'DELETE'}),
        ('ContextNull', {'context': None}), ('FieldsArray', {'fields': []}),
        ('ArgumentsNull', {'arguments': None}), ('UnknownArgument', {'arguments': {'enabled': True}}),
        ('ByteBoolean', {'fields': {'key': [True]}}),
        ('ByteNegative', {'fields': {'value': [-1]}}),
        ('ByteOverflow', {'fields': {'value': [256]}}),
        ('ByteFloat', {'fields': {'value': [1.0]}}),
        ('ByteString', {'fields': {'value': ['0']}}),
        ('ByteNull', {'fields': {'value': [None]}}),
        ('FieldNull', {'fields': {'value': None}}),
        ('FieldString', {'fields': {'value': '00'}}),
        ('OperationString', {'context': dict(ab03ao03Context, operation='17')}),
        ('OperationBoolean', {'context': dict(ab03ao03Context, operation=True)}),
        ('OperationFloat', {'context': dict(ab03ao03Context, operation=17.0)}),
        ('ViewNull', {'context': dict(ab03ao03Context, view=None)}),
        ('DirectionInteger', {'context': dict(ab03ao03Context, direction=0)}),
    ):
        ab03ao03Input = {'context': dict(ab03ao03Context), 'fields': {'key': [2], 'value': [0, 170, 255]}}
        for ab03ao03Name, ab03ao03Value in ab03ao03Patch.items():
            if ab03ao03Value == 'DELETE':
                ab03ao03Input.pop(ab03ao03Name)
            else:
                ab03ao03Input[ab03ao03Name] = ab03ao03Value
        ab03ao03Result[ab03ao03Id] = ab03ao03Json.dumps(ab03ao03Input)
    for ab03ao03Axis in ('primary', 'secondary', 'operation', 'direction', 'view'):
        ab03ao03Input = {'context': dict(ab03ao03Context), 'fields': {'key': [2], 'value': [0, 170, 255]}}
        ab03ao03Input['context'].pop(ab03ao03Axis)
        ab03ao03Result['Missing' + ab03ao03Axis.title()] = ab03ao03Json.dumps(ab03ao03Input)
    for ab03ao03Axis, ab03ao03Value in (
            ('primary', True), ('primary', 181.0), ('primary', '181'),
            ('secondary', False), ('secondary', 6.0), ('secondary', '6')):
        ab03ao03Input = {'context': dict(ab03ao03Context), 'fields': {'key': [2], 'value': [0, 170, 255]}}
        ab03ao03Input['context'][ab03ao03Axis] = ab03ao03Value
        ab03ao03Result['Kind' + ab03ao03Axis.title() + type(ab03ao03Value).__name__.title()] = ab03ao03Json.dumps(ab03ao03Input)
    ab03ao03Result['DuplicateOpaque'] = '{"context":{"family":{"x":0,"x":1}},"fields":{}}'
    return {'ab03ao03' + ab03ao03Id: {'id': 'ab03ao03' + ab03ao03Id,
            'input_text': ab03ao03Text, 'error': True}
            for ab03ao03Id, ab03ao03Text in ab03ao03Result.items()}


class Ab03Ao03ContractTests(ab03ao03Unittest.TestCase):
    def ab03ao03Documents(self):
        ab03ao03Page = (ab03ao03Root / 'architecture/ao04_b506_parameter_views.md').read_text()
        self.assertEqual(ab03ao03Re.findall(r'```go\n(.*?)\n```', ab03ao03Page, ab03ao03Re.S),
                         ['package vaillant\n\nfunc ' + ab03ao03Contract['api']])
        ab03ao03Blocks = ab03ao03Re.findall(r'```json ab03ao03-contract\n(.*?)\n```', ab03ao03Page, ab03ao03Re.S)
        self.assertEqual(len(ab03ao03Blocks), 1)
        return [ab03ao03Json.loads(ab03ao03Blocks[0]), ab03ao03Json.loads(
            (ab03ao03Root / 'architecture/fixtures/ao04_b506_parameter_views.json').read_text())]

    def ab03ao03AssertTable(self, ab03ao03Document):
        self.assertEqual(set(ab03ao03Document), {'contract', 'cases', 'errors'})
        # Canonical JSON comparison also distinguishes false, zero and 0.0.
        self.assertEqual(ab03ao03Json.dumps(ab03ao03Document['contract'], sort_keys=True),
                         ab03ao03Json.dumps(ab03ao03Contract, sort_keys=True))
        for ab03ao03Kind, ab03ao03Expected in (
                ('cases', ab03ao03Oracle()), ('errors', ab03ao03Errors())):
            ab03ao03Rows = ab03ao03Document[ab03ao03Kind]
            self.assertEqual(len(ab03ao03Rows), len(ab03ao03Expected))
            self.assertEqual({ab03ao03Row['id'] for ab03ao03Row in ab03ao03Rows}, set(ab03ao03Expected))
            for ab03ao03Row in ab03ao03Rows:
                with self.subTest(ab03ao03Id=ab03ao03Row['id']):
                    self.assertEqual(ab03ao03Json.dumps(ab03ao03Row, sort_keys=True),
                                     ab03ao03Json.dumps(ab03ao03Expected[ab03ao03Row['id']], sort_keys=True))

    def TestAb03Ao03PageExactContract(self):
        self.ab03ao03AssertTable(self.ab03ao03Documents()[0])

    def TestAb03Ao03FixtureExactContract(self):
        self.ab03ao03AssertTable(self.ab03ao03Documents()[1])

    def TestAb03Ao03OrderIndependentRoundTrip(self):
        ab03ao03Page, ab03ao03Fixture = self.ab03ao03Documents()
        self.assertNotEqual([ab03ao03Row['id'] for ab03ao03Row in ab03ao03Page['cases']],
                            [ab03ao03Row['id'] for ab03ao03Row in ab03ao03Fixture['cases']])
        for ab03ao03Doc in (ab03ao03Page, ab03ao03Fixture):
            ab03ao03Doc['cases'].reverse()
            self.ab03ao03AssertTable(ab03ao03Json.loads(ab03ao03Json.dumps(ab03ao03Doc)))

    def TestAb03Ao03IdentityAxesIndependent(self):
        ab03ao03Rows = ab03ao03Oracle()
        ab03ao03Control = ab03ao03Rows['ab03ao03Opaque2']['input']
        for ab03ao03Axis in ('primary', 'secondary', 'operation', 'direction', 'view'):
            ab03ao03Case = ab03ao03Rows['ab03ao03Axis' + ab03ao03Axis.title()]
            self.assertEqual(ab03ao03Case['input']['fields'], ab03ao03Control['fields'])
            self.assertEqual([ab03ao03Name for ab03ao03Name in ab03ao03Context
                              if ab03ao03Case['input']['context'][ab03ao03Name] != ab03ao03Context[ab03ao03Name]],
                             [ab03ao03Axis])
        for ab03ao03Doc in self.ab03ao03Documents():
            self.ab03ao03AssertTable(ab03ao03Doc)


def load_tests(ab03ao03Loader, ab03ao03Tests, ab03ao03Pattern):
    # Standard unittest hook preserves the contract's TestAb03Ao03 naming.
    return ab03ao03Unittest.TestSuite(
        Ab03Ao03ContractTests(ab03ao03Name)
        for ab03ao03Name in sorted(vars(Ab03Ao03ContractTests))
        if ab03ao03Name.startswith('TestAb03Ao03'))


if __name__ == '__main__':
    ab03ao03Unittest.main()
