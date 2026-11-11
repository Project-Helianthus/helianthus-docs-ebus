"""Independent finite documentation oracle; no replacement production interpreter."""
import copy
import json
from pathlib import Path
import unittest

ab01ao01Root = Path(__file__).resolve().parents[1]
ab01ao01Page = ab01ao01Root / 'architecture/ao02-b505-sentinel-views.md'
ab01ao01Fixture = ab01ao01Root / 'architecture/fixtures/ao02_b505_sentinel_views.json'


def ab01ao01ExpectedContract():
    return {
        'id': 'ab01ao01_replacement_pair',
        'api': 'Ab01Ao01Interpret(ab01ao01Input json.RawMessage) (json.RawMessage, error)',
        'package': 'vaillant',
        'selector': {'primary': 181, 'secondary': 5, 'operation': 50,
                     'direction': 'request', 'view': 'replacement-pair'},
        'field_names': ['temperature_one', 'temperature_two'],
        'word_bytes': 2, 'byte_order': 'little-endian-token-only',
        'branches': [
            {'raw': [0, 128], 'state': 'preserve-existing', 'grade': 'Hypothesis'},
            {'raw': [0, 0], 'state': 'circuit-default', 'grade': 'Hypothesis'},
            {'raw': [1, 0], 'state': 'numeric-unqualified', 'grade': 'Hypothesis'},
            {'raw': [255, 255], 'state': 'numeric-unqualified', 'grade': 'Hypothesis'}],
        'numeric_results': [], 'physical': 'Unknown', 'qualified': False,
        'unknowns': ['absolute_positions', 'complete_write_body', 'ordinary_numeric_scale',
                     'conflicting_bounds', 'persistence', 'physical_effects', 'acceptance',
                     'family_applicability'],
        'arguments': {'allowed_keys': [], 'optional': True},
        'output_keys': ['context', 'raw', 'state', 'fields', 'physical', 'qualified'],
        'optional_output_keys': ['arguments'], 'field_keys': ['raw', 'state', 'grade'],
        'absent_field_keys': ['state', 'grade'],
        'forbidden_field_keys': ['number', 'label', 'flags', 'reserved',
                                 'candidate_domain', 'calculation'],
        'states': {'selected': 'complete', 'unresolved': 'partial', 'unselected': 'Unknown',
                   'short': 'incomplete', 'overlong': 'incomplete', 'empty': 'incomplete',
                   'absent': 'missing', 'unmodelled': 'Unknown'},
        'errors': ['malformed_json', 'duplicate_key', 'wrong_kind', 'invalid_byte',
                   'unsupported_argument'],
        'copy_contract': ['context_deep_copy', 'raw_independent_copy',
                          'arguments_independent_copy', 'no_cross_result_alias',
                          'no_cross_call_alias'],
        'round_trip': 'preserve_presence_states_and_errors',
        'implementation_scope': 'pure_library_no_cache_catalog_registration_or_call_site'}


def ab01ao01ExpectedRows():
    """Assemble explicit tuples, never decode an input word to obtain an expectation."""
    ab01ao01Context = {'primary': 181, 'secondary': 5, 'operation': 50,
                       'direction': 'request', 'view': 'replacement-pair',
                       'family': 'synthetic-family', 'variant': 'synthetic-variant',
                       'opaque': {'value': [0]}}
    ab01ao01Base = {'temperature_one': [0, 128], 'temperature_two': [0, 0]}
    ab01ao01Rows = []

    def ab01ao01Row(ab01ao01Suffix, ab01ao01Raw, ab01ao01States,
                    ab01ao01Overall='complete', ab01ao01Ctx=None, ab01ao01Arguments=None):
        ab01ao01Input = {'context': copy.deepcopy(ab01ao01Context if ab01ao01Ctx is None
                                                 else ab01ao01Ctx),
                         'fields': copy.deepcopy(ab01ao01Raw)}
        ab01ao01Fields = {}
        for ab01ao01Name, ab01ao01State in ab01ao01States.items():
            ab01ao01Fields[ab01ao01Name] = {
                'state': ab01ao01State,
                'grade': 'Unknown' if ab01ao01State == 'Unknown' else 'Hypothesis'}
            if ab01ao01Name in ab01ao01Raw:
                ab01ao01Fields[ab01ao01Name]['raw'] = copy.deepcopy(ab01ao01Raw[ab01ao01Name])
        ab01ao01Output = {'context': copy.deepcopy(ab01ao01Input['context']),
                          'raw': copy.deepcopy(ab01ao01Raw), 'state': ab01ao01Overall,
                          'fields': ab01ao01Fields, 'physical': 'Unknown', 'qualified': False}
        if ab01ao01Arguments is not None:
            ab01ao01Input['arguments'] = copy.deepcopy(ab01ao01Arguments)
            ab01ao01Output['arguments'] = copy.deepcopy(ab01ao01Arguments)
        ab01ao01Rows.append({'id': 'ab01ao01_' + ab01ao01Suffix,
                            'input': ab01ao01Input, 'expected': ab01ao01Output})

    ab01ao01Resolved = {'temperature_one': 'preserve-existing',
                        'temperature_two': 'circuit-default'}
    ab01ao01Row('pair', ab01ao01Base, ab01ao01Resolved)
    ab01ao01Row('reverse', {'temperature_one': [0, 0], 'temperature_two': [0, 128]},
                {'temperature_one': 'circuit-default', 'temperature_two': 'preserve-existing'})
    for ab01ao01Name in ('temperature_one', 'temperature_two'):
        for ab01ao01Token, ab01ao01Raw, ab01ao01State, ab01ao01Overall in (
                ('8000', [0, 128], 'preserve-existing', 'complete'),
                ('0000', [0, 0], 'circuit-default', 'complete'),
                ('0001', [1, 0], 'numeric-unqualified', 'partial'),
                ('ffff', [255, 255], 'numeric-unqualified', 'partial'),
                ('short', [0], 'incomplete', 'partial'),
                ('empty', [], 'incomplete', 'partial'),
                ('absent', None, 'missing', 'partial'),
                ('overlong', [0, 128, 0], 'incomplete', 'partial')):
            ab01ao01Fields = copy.deepcopy(ab01ao01Base)
            if ab01ao01Raw is None:
                del ab01ao01Fields[ab01ao01Name]
            else:
                ab01ao01Fields[ab01ao01Name] = ab01ao01Raw
            ab01ao01States = dict(ab01ao01Resolved)
            ab01ao01States[ab01ao01Name] = ab01ao01State
            ab01ao01Row(ab01ao01Name + '_' + ab01ao01Token, ab01ao01Fields,
                        ab01ao01States, ab01ao01Overall)
    for ab01ao01Axis, ab01ao01Value in (('primary', 180), ('secondary', 4),
            ('operation', 49), ('direction', 'response'), ('view', 'other')):
        ab01ao01Ctx = copy.deepcopy(ab01ao01Context)
        ab01ao01Ctx[ab01ao01Axis] = ab01ao01Value
        ab01ao01Row('context_' + ab01ao01Axis, ab01ao01Base,
                    {'temperature_one': 'Unknown', 'temperature_two': 'Unknown'},
                    'Unknown', ab01ao01Ctx)
    for ab01ao01Axis, ab01ao01Value in (('family', {'opaque': [1]}),
            ('variant', None), ('opaque', {'value': [1]})):
        ab01ao01Ctx = copy.deepcopy(ab01ao01Context)
        ab01ao01Ctx[ab01ao01Axis] = ab01ao01Value
        ab01ao01Row('opaque_' + ab01ao01Axis, ab01ao01Base, ab01ao01Resolved,
                    ab01ao01Ctx=ab01ao01Ctx)
    ab01ao01Row('arguments_empty', ab01ao01Base, ab01ao01Resolved, ab01ao01Arguments={})
    ab01ao01Row('unmodelled', dict(ab01ao01Base, unmodelled=[0, 255, 128]),
                dict(ab01ao01Resolved, unmodelled='Unknown'), 'partial')
    ab01ao01Row('both_missing', {}, {'temperature_one': 'missing',
                                    'temperature_two': 'missing'}, 'partial')
    return ab01ao01Rows


def ab01ao01ExpectedErrors():
    ab01ao01Input = ab01ao01ExpectedRows()[0]['input']
    ab01ao01Errors = [
        ('malformed', '{'),
        ('duplicate_top', '{"context":{},"context":{},"fields":{}}'),
        ('duplicate_nested', '{"context":{"primary":181,"primary":181},"fields":{}}'),
        ('duplicate_field', '{"context":{},"fields":{"temperature_one":[],"temperature_one":[]}}'),
        ('root_array', '[]'), ('root_null', 'null')]
    for ab01ao01Suffix, ab01ao01Value in (('fields_null', None), ('fields_array', []),
                                         ('fields_string', '')):
        ab01ao01Copy = copy.deepcopy(ab01ao01Input)
        ab01ao01Copy['fields'] = ab01ao01Value
        ab01ao01Errors.append((ab01ao01Suffix, json.dumps(ab01ao01Copy)))
    for ab01ao01Suffix, ab01ao01Value in (
            ('negative', [-1]), ('overflow', [256]), ('float', [0.0]),
            ('boolean', [True]), ('null', [None]), ('string', ['0']),
            ('word_null', None), ('word_scalar', 0), ('word_object', {})):
        ab01ao01Copy = copy.deepcopy(ab01ao01Input)
        ab01ao01Copy['fields']['temperature_one'] = ab01ao01Value
        ab01ao01Errors.append((ab01ao01Suffix, json.dumps(ab01ao01Copy)))
    for ab01ao01Suffix, ab01ao01Value in (('arguments_null', None),
            ('arguments_array', []), ('arguments_flag', {'flag': False}),
            ('arguments_zero', {'value': 0})):
        ab01ao01Copy = copy.deepcopy(ab01ao01Input)
        ab01ao01Copy['arguments'] = ab01ao01Value
        ab01ao01Errors.append((ab01ao01Suffix, json.dumps(ab01ao01Copy)))
    for ab01ao01Axis in ('primary', 'secondary', 'operation', 'direction', 'view'):
        ab01ao01Copy = copy.deepcopy(ab01ao01Input)
        ab01ao01Copy['context'][ab01ao01Axis] = True if ab01ao01Axis in (
            'primary', 'secondary', 'operation') else 0
        ab01ao01Errors.append(('kind_' + ab01ao01Axis, json.dumps(ab01ao01Copy)))
    for ab01ao01Suffix, ab01ao01Value in (
            ('missing_fields', {'context': ab01ao01Input['context']}),
            ('missing_context', {'fields': ab01ao01Input['fields']}),
            ('context_null', {'context': None, 'fields': ab01ao01Input['fields']})):
        ab01ao01Errors.append((ab01ao01Suffix, json.dumps(ab01ao01Value)))
    return [{'id': 'ab01ao01_' + ab01ao01Suffix, 'input_json': ab01ao01Value,
             'expected_error': True, 'successful_result': False}
            for ab01ao01Suffix, ab01ao01Value in ab01ao01Errors]


class Ab01Ao01ContractTests(unittest.TestCase):
    def setUp(self):
        self.ab01ao01Fixture = json.loads(ab01ao01Fixture.read_text())
        self.ab01ao01Text = ab01ao01Page.read_text()
        self.ab01ao01Page = json.loads(self.ab01ao01Text.split(
            '<!-- ab01ao01-contract:start -->\n```json\n')[1].split(
                '\n```\n<!-- ab01ao01-contract:end -->')[0])

    def ab01ao01AssertExact(self, ab01ao01Actual, ab01ao01Expected):
        self.assertEqual(json.dumps(ab01ao01Actual, sort_keys=True),
                         json.dumps(ab01ao01Expected, sort_keys=True))

    def TestAb01Ao01ExactContract(self):
        for ab01ao01Source in (self.ab01ao01Page, self.ab01ao01Fixture):
            self.assertEqual(set(ab01ao01Source), {'contract', 'cases', 'errors'})
            self.ab01ao01AssertExact(ab01ao01Source['contract'], ab01ao01ExpectedContract())

    def TestAb01Ao01IndependentTuples(self):
        for ab01ao01Source in (self.ab01ao01Page, self.ab01ao01Fixture):
            self.assertEqual(len(ab01ao01Source['cases']), 29)
            for ab01ao01Actual, ab01ao01Expected in zip(
                    ab01ao01Source['cases'], ab01ao01ExpectedRows()):
                with self.subTest(ab01ao01Case=ab01ao01Expected['id']):
                    self.ab01ao01AssertExact(ab01ao01Actual, ab01ao01Expected)

    def TestAb01Ao01ErrorDeclarations(self):
        for ab01ao01Source in (self.ab01ao01Page, self.ab01ao01Fixture):
            self.ab01ao01AssertExact(ab01ao01Source['errors'], ab01ao01ExpectedErrors())

    def TestAb01Ao01RoundTripDeclarations(self):
        for ab01ao01Source in (self.ab01ao01Page, self.ab01ao01Fixture):
            self.ab01ao01AssertExact(json.loads(json.dumps(ab01ao01Source)), {
                'contract': ab01ao01ExpectedContract(), 'cases': ab01ao01ExpectedRows(),
                'errors': ab01ao01ExpectedErrors()})

    def TestAb01Ao01HumanFieldTable(self):
        ab01ao01Rows = [ab01ao01Line for ab01ao01Line in self.ab01ao01Text.splitlines()
                       if ab01ao01Line.startswith('|')]
        self.assertEqual(ab01ao01Rows, [
            '| Raw word (LE bytes) | Field state | Numeric result | Grade |',
            '| --- | --- | --- | --- |',
            '| 8000 (`[0,128]`) | preserve-existing | absent | Hypothesis |',
            '| 0000 (`[0,0]`) | circuit-default | absent | Hypothesis |',
            '| 0001 (`[1,0]`) | numeric-unqualified | absent | Hypothesis |',
            '| FFFF (`[255,255]`) | numeric-unqualified | absent | Hypothesis |',
            '| Any other exact two-byte word | numeric-unqualified | absent | Hypothesis |'])
        self.assertIn('func ' + ab01ao01ExpectedContract()['api'], self.ab01ao01Text)


def load_tests(ab01ao01Loader, ab01ao01Tests, ab01ao01Pattern):
    # unittest's protocol hook preserves the mandated TestAb01Ao01 method prefix.
    return unittest.TestSuite(Ab01Ao01ContractTests(ab01ao01Name)
                             for ab01ao01Name in sorted(dir(Ab01Ao01ContractTests))
                             if ab01ao01Name.startswith('TestAb01Ao01'))
