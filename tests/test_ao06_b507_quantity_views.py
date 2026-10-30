"""Finite documentation checks; no production interpreter is implemented here."""
import copy
import json
from pathlib import Path
import re
import unittest


ab05ao05Root = Path(__file__).resolve().parents[1]
ab05ao05Context = {
    'primary': 181, 'secondary': 7, 'operation': 6, 'direction': 'positive',
    'view': 'capacity', 'family': 'synthetic-family', 'variant': 'synthetic-variant',
}
# Independent literal oracle: no result is calculated from its input carrier.
ab05ao05Capacity = (
    (0, 0, 'complete', True),
    (1, 0.1, 'complete', True),
    (250, 25, 'complete', True),
    (251, 25.1, 'outside-candidate-domain', False),
    (255, 25.5, 'outside-candidate-domain', False),
)
ab05ao05Preference = (
    ('0000', [0, 0], 'complete', 'appliance-unavailable'),
    ('FFFF', [255, 255], 'complete', 'maximum-efficiency-preference'),
    ('0001', [1, 0], 'unmapped', None),
    ('0100', [0, 1], 'unmapped', None),
)


def ab05ao05ExpectedCases():
    """Construct fixed expected tuples, not an input-driven interpreter."""
    ab05ao05Rows = []

    def ab05ao05Row(ab05ao05Id, ab05ao05Raw, ab05ao05Fields,
                    ab05ao05State='complete', ab05ao05Ctx=None,
                    ab05ao05Args=None):
        ab05ao05Ctx = copy.deepcopy(ab05ao05Context if ab05ao05Ctx is None else ab05ao05Ctx)
        ab05ao05Input = {'context': ab05ao05Ctx, 'fields': ab05ao05Raw}
        ab05ao05Output = {
            'context': copy.deepcopy(ab05ao05Ctx), 'raw': copy.deepcopy(ab05ao05Raw),
            'state': ab05ao05State, 'fields': ab05ao05Fields,
            'physical': 'Unknown', 'qualified': False,
        }
        if ab05ao05Args is not None:
            ab05ao05Input['arguments'] = ab05ao05Args
            ab05ao05Output['arguments'] = copy.deepcopy(ab05ao05Args)
        ab05ao05Rows.append({'id': 'ab05ao05' + ab05ao05Id,
                            'input': ab05ao05Input, 'expected': ab05ao05Output})

    for ab05ao05Byte, ab05ao05Number, ab05ao05State, ab05ao05Domain in ab05ao05Capacity:
        ab05ao05Row('Capacity' + str(ab05ao05Byte), {'capacity': [ab05ao05Byte]}, {
            'capacity': {'raw': [ab05ao05Byte], 'state': ab05ao05State,
                         'number': ab05ao05Number, 'unit': 'kW',
                         'grade': 'Hypothesis', 'calculation': 'Proven',
                         'candidate_domain': ab05ao05Domain}})
    for ab05ao05Word, ab05ao05Bytes, ab05ao05State, ab05ao05Label in ab05ao05Preference:
        ab05ao05Ctx = dict(ab05ao05Context, operation=8, view='preference')
        ab05ao05Field = {'raw': ab05ao05Bytes, 'state': ab05ao05State, 'grade': 'Hypothesis'}
        if ab05ao05Label is not None:
            ab05ao05Field['label'] = ab05ao05Label
        ab05ao05Row('Preference' + ab05ao05Word, {'preference': ab05ao05Bytes},
                    {'preference': ab05ao05Field},
                    'partial' if ab05ao05State == 'unmapped' else 'complete', ab05ao05Ctx)
        for ab05ao05Op in (9, 11):
            ab05ao05Row('Operation' + str(ab05ao05Op) + 'Word' + ab05ao05Word,
                        {'preference': ab05ao05Bytes}, {}, 'Unknown',
                        dict(ab05ao05Ctx, operation=ab05ao05Op))
    # Width is independent of operation/view; absent is not an empty array.
    for ab05ao05View, ab05ao05Op, ab05ao05Arrays in (
            ('capacity', 6, ([], [1, 2])), ('preference', 8, ([], [0], [0, 0, 0]))):
        ab05ao05Ctx = dict(ab05ao05Context, operation=ab05ao05Op, view=ab05ao05View)
        ab05ao05Row(ab05ao05View.title() + 'Missing', {}, {}, 'partial', ab05ao05Ctx)
        for ab05ao05Bytes in ab05ao05Arrays:
            ab05ao05Row(ab05ao05View.title() + 'Width' + str(len(ab05ao05Bytes)),
                        {ab05ao05View: ab05ao05Bytes},
                        {ab05ao05View: {'raw': ab05ao05Bytes, 'state': 'incomplete',
                                       'grade': 'Hypothesis'}}, 'partial', ab05ao05Ctx)
    for ab05ao05Key, ab05ao05Value in (
            ('primary', 180), ('secondary', 8), ('operation', 7),
            ('direction', 'request'), ('view', 'preference'), ('view', 'unknown')):
        ab05ao05Row('Axis' + ab05ao05Key.title() + str(ab05ao05Value),
                    {'capacity': [1]}, {}, 'Unknown',
                    dict(ab05ao05Context, **{ab05ao05Key: ab05ao05Value}))
    ab05ao05One = {'capacity': {'raw': [1], 'state': 'complete', 'number': 0.1,
                              'unit': 'kW', 'grade': 'Hypothesis',
                              'calculation': 'Proven', 'candidate_domain': True}}
    for ab05ao05Key in ('family', 'variant'):
        ab05ao05Row('Opaque' + ab05ao05Key.title(), {'capacity': [1]},
                    copy.deepcopy(ab05ao05One), ab05ao05Ctx=dict(
                        ab05ao05Context, **{ab05ao05Key: {'opaque': [0, False, 'synthetic']}}))
    ab05ao05Row('UnknownSibling', {'capacity': [1], 'unmodelled': [0, 255, 1]},
                copy.deepcopy(ab05ao05One), 'partial')
    ab05ao05Row('CostUnknown', {'capacity': [1], 'cost': [10]},
                copy.deepcopy(ab05ao05One), 'partial')
    ab05ao05Row('ArgumentsEmpty', {'capacity': [1]}, copy.deepcopy(ab05ao05One),
                ab05ao05Args={})
    return ab05ao05Rows


def ab05ao05ExpectedRejections():
    ab05ao05Input = {'context': copy.deepcopy(ab05ao05Context), 'fields': {'capacity': [1]}}
    ab05ao05Text = json.dumps(ab05ao05Input, separators=(',', ':'))
    ab05ao05Rows = [
        ('Malformed', '{'),
        ('DuplicateRoot', ab05ao05Text[:-1] + ',"fields":{}}'),
        ('DuplicateContext', ab05ao05Text.replace('"primary":181', '"primary":181,"primary":181')),
        ('DuplicateField', ab05ao05Text.replace('"capacity":[1]', '"capacity":[1],"capacity":[1]')),
        ('DuplicateOpaque', ab05ao05Text.replace('"synthetic-family"', '{"x":0,"x":1}')),
        ('RootArray', '[]'),
    ]
    for ab05ao05Id, ab05ao05Value in (
            ('Negative', [-1]), ('Overflow', [256]), ('Boolean', [True]),
            ('Fraction', [1.5]), ('FloatToken', [1.0]), ('String', ['1']),
            ('NullElement', [None]), ('FieldScalar', 1), ('FieldNull', None)):
        ab05ao05Bad = copy.deepcopy(ab05ao05Input)
        ab05ao05Bad['fields']['capacity'] = ab05ao05Value
        ab05ao05Rows.append((ab05ao05Id, json.dumps(ab05ao05Bad)))
    for ab05ao05Id, ab05ao05Key, ab05ao05Value in (
            ('ContextKind', 'context', []), ('FieldsKind', 'fields', []),
            ('ArgumentsKind', 'arguments', []),
            ('ArgumentsFlag', 'arguments', {'execute': True}),
            ('ArgumentsInteger', 'arguments', {'limit': 0})):
        ab05ao05Bad = copy.deepcopy(ab05ao05Input)
        ab05ao05Bad[ab05ao05Key] = ab05ao05Value
        ab05ao05Rows.append((ab05ao05Id, json.dumps(ab05ao05Bad)))
    for ab05ao05Key in ('context', 'fields'):
        ab05ao05Bad = copy.deepcopy(ab05ao05Input)
        del ab05ao05Bad[ab05ao05Key]
        ab05ao05Rows.append(('Missing' + ab05ao05Key.title(), json.dumps(ab05ao05Bad)))
    for ab05ao05Key in ('primary', 'secondary', 'operation', 'direction', 'view'):
        for ab05ao05Kind in ('Missing', 'WrongKind'):
            ab05ao05Bad = copy.deepcopy(ab05ao05Input)
            if ab05ao05Kind == 'Missing':
                del ab05ao05Bad['context'][ab05ao05Key]
            else:
                ab05ao05Bad['context'][ab05ao05Key] = []
            ab05ao05Rows.append((ab05ao05Kind + ab05ao05Key.title(), json.dumps(ab05ao05Bad)))
    ab05ao05Rows.extend([
        ('Trailing', json.dumps(ab05ao05Input) + ' {}'),
        ('DuplicateArguments', json.dumps(ab05ao05Input)[:-1] + ',"arguments":{"x":0,"x":1}}'),
    ])
    return [{'id': 'ab05ao05' + ab05ao05Id, 'input_json': ab05ao05Text,
             'error': True, 'successful_result': False}
            for ab05ao05Id, ab05ao05Text in ab05ao05Rows]


class TestAb05Ao05QuantityViews(unittest.TestCase):
    def ab05ao05AssertExact(ab05ao05Self, ab05ao05Actual, ab05ao05Expected):
        # JSON token types matter: Python equality conflates True/1 and False/0.
        ab05ao05Self.assertEqual(
            json.dumps(ab05ao05Actual, sort_keys=True),
            json.dumps(ab05ao05Expected, sort_keys=True))

    @classmethod
    def setUpClass(ab05ao05Cls):
        ab05ao05Page = (ab05ao05Root / 'architecture/ao06_b507_quantity_views.md').read_text()
        ab05ao05Match = re.findall(
            r'<!-- ab05ao05-contract:start -->\s*```json\n(.*?)\n```\s*'
            r'<!-- ab05ao05-contract:end -->', ab05ao05Page, re.S)
        if len(ab05ao05Match) != 1:
            raise AssertionError('exactly one finite page table required')
        ab05ao05Cls.ab05ao05Contracts = (
            json.loads(ab05ao05Match[0]),
            json.loads((ab05ao05Root / 'architecture/fixtures/ao06_b507_quantity_views.json')
                       .read_text())['contract'],
        )

    def TestAb05Ao05cases_independent_exact_oracle(ab05ao05Self):
        for ab05ao05Contract in ab05ao05Self.ab05ao05Contracts:
            ab05ao05Self.ab05ao05AssertExact(ab05ao05Contract['cases'], ab05ao05ExpectedCases())
            ab05ao05Self.ab05ao05AssertExact(len(ab05ao05Contract['cases']), 35)
            ab05ao05Self.ab05ao05AssertExact(ab05ao05Contract['rejections'], ab05ao05ExpectedRejections())
            ab05ao05Self.ab05ao05AssertExact(len(ab05ao05Contract['rejections']), 34)

    def TestAb05Ao05api_selection_and_shapes(ab05ao05Self):
        for ab05ao05Contract in ab05ao05Self.ab05ao05Contracts:
            ab05ao05Self.ab05ao05AssertExact(ab05ao05Contract['api'], {
                'package': 'vaillant',
                'signature': 'Ab05Ao05Interpret(ab05ao05Input json.RawMessage) (json.RawMessage, error)',
                'dependencies': 'standard-library', 'pure': True})
            ab05ao05Self.ab05ao05AssertExact(ab05ao05Contract['selection'], {
                'primary': 181, 'secondary': 7, 'direction': 'positive',
                'views': [{'operation': 6, 'view': 'capacity', 'field': 'capacity', 'width': 1},
                          {'operation': 8, 'view': 'preference', 'field': 'preference', 'width': 2}],
                'inference': False})
            ab05ao05Self.ab05ao05AssertExact(ab05ao05Contract['shapes'], {
                'input_required': ['context', 'fields'],
                'context_required': ['primary', 'secondary', 'operation', 'direction', 'view'],
                'arguments_allowed': [],
                'output_required': ['context', 'raw', 'state', 'fields', 'physical', 'qualified'],
                'output_optional': ['arguments'], 'field_required': ['raw', 'state'],
                'field_optional': ['number', 'unit', 'label', 'grade', 'calculation', 'flags',
                                   'reserved', 'candidate_domain'],
                'result_states': ['complete', 'partial', 'Unknown'],
                'field_states': ['complete', 'incomplete', 'unmapped',
                                 'outside-candidate-domain', 'Unknown']})

    def TestAb05Ao05numeric_and_grade_boundaries(ab05ao05Self):
        for ab05ao05Contract in ab05ao05Self.ab05ao05Contracts:
            ab05ao05Self.ab05ao05AssertExact(ab05ao05Contract['numeric'], {
                'capacity': {'unsigned': True, 'divisor': 10, 'unit': 'kW',
                             'candidate_min': 0, 'candidate_max': 250,
                             'outside': 'retain-number-candidate_domain-false'},
                'preference': {'order': 'LE', 'labels': {'0000': 'appliance-unavailable',
                               'FFFF': 'maximum-efficiency-preference'}, 'other': 'unmapped-no-number'},
                'no_number': ['incomplete', 'unmapped', 'unit-conflict', 'unknown-order']})
            ab05ao05Self.ab05ao05AssertExact(ab05ao05Contract['grades'], {
                'semantic': 'Hypothesis', 'capacity_calculation': 'Proven', 'physical': 'Unknown',
                'qualified': False, 'cost_reference': 'Unknown', 'cost_conversion': 'Unknown',
                'absolute_positions': 'Unknown', 'physical_availability': 'Unknown',
                'execution': 'Unknown', 'effects': 'Unknown', 'persistence': 'Unknown'})

    def TestAb05Ao05preservation_and_error_contract(ab05ao05Self):
        for ab05ao05Contract in ab05ao05Self.ab05ao05Contracts:
            ab05ao05Self.ab05ao05AssertExact(ab05ao05Contract['preservation'], {
                'context': 'unchanged-deep-copy', 'raw': 'independent-copy-all-fields-and-tails',
                'arguments': 'independent-copy-if-present', 'missing_vs_zero': True,
                'empty_vs_missing': True, 'unknown_sibling': 'retain-complete-independent-fields',
                'round_trip': 'preserve-state-and-presence', 'cross_call_aliasing': False})
            ab05ao05Self.ab05ao05AssertExact(ab05ao05Contract['errors'], [
                'malformed-json', 'duplicate-object-key-at-any-depth', 'wrong-json-kind',
                'invalid-byte-element', 'unsupported-argument'])
            # Serializing the declared examples must preserve their states/presence.
            ab05ao05Self.ab05ao05AssertExact(json.loads(json.dumps(ab05ao05Contract)), ab05ao05Contract)


def load_tests(ab05ao05Loader, ab05ao05Tests, ab05ao05Pattern):
    ab05ao05Loader.testMethodPrefix = 'TestAb05Ao05'
    return ab05ao05Loader.loadTestsFromTestCase(TestAb05Ao05QuantityViews)


if __name__ == '__main__':
    unittest.main()
