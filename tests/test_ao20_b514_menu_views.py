"""Finite documentation oracles; these tests do not implement the Go interpreter."""
import copy
import json
from pathlib import Path
import re
import unittest

ab19ao19Root = Path(__file__).resolve().parents[1]


def ab19ao19ExpectedCases():
    """Explicit expected tuples, with no byte decoder or view dispatcher."""
    ab19ao19Rows = []

    def ab19ao19Add(ab19ao19Name, ab19ao19Operation, ab19ao19View,
                    ab19ao19Raw, ab19ao19Fields, ab19ao19State='complete',
                    ab19ao19Context=None, ab19ao19Arguments=None):
        ab19ao19Identity = dict(primary=181, secondary=20,
                               operation=ab19ao19Operation, direction='positive',
                               view=ab19ao19View, family='synthetic-family',
                               variant='synthetic-variant')
        ab19ao19Identity.update(ab19ao19Context or {})
        ab19ao19Input = dict(context=ab19ao19Identity, fields=ab19ao19Raw)
        if ab19ao19Arguments is not None:
            ab19ao19Input['arguments'] = ab19ao19Arguments
        ab19ao19Rows.append(dict(
            id='ab19ao19_' + ab19ao19Name, input=ab19ao19Input,
            expected=dict(state=ab19ao19State, fields=ab19ao19Fields,
                          physical='Unknown', qualified=False)))

    def ab19ao19Feedback(ab19ao19Raw, ab19ao19State, ab19ao19Label=None):
        ab19ao19Value = dict(raw=ab19ao19Raw, state=ab19ao19State,
                            grade='Hypothesis')
        if ab19ao19Label is not None:
            ab19ao19Value['label'] = ab19ao19Label
        return {'feedback': ab19ao19Value}

    # The three alternatives are intentionally independent literal tables.
    for ab19ao19Slug, ab19ao19View, ab19ao19Values in [
        ('generic', 'generic-result', [(0, 'unmapped', None),
         (1, 'mapped', 'in-progress'), (2, 'unmapped', None),
         (3, 'unmapped', None), (255, 'mapped', 'unsupported')]),
        ('specific_a', 'specific-a-result', [(0, 'unmapped', None),
         (1, 'mapped', 'not-successful'), (2, 'unmapped', None),
         (3, 'invalid', None), (255, 'invalid', None)]),
        ('specific_b', 'specific-b-result', [(0, 'unmapped', None),
         (1, 'mapped', 'not-successful'), (2, 'unmapped', None),
         (3, 'invalid', None), (255, 'invalid', None)]),
    ]:
        for ab19ao19Byte, ab19ao19State, ab19ao19Label in ab19ao19Values:
            ab19ao19Add('op06_' + ab19ao19Slug + '_' + str(ab19ao19Byte),
                        6, ab19ao19View, {'feedback': [ab19ao19Byte]},
                        ab19ao19Feedback([ab19ao19Byte], ab19ao19State,
                                        ab19ao19Label))
    for ab19ao19Byte, ab19ao19Label in [
        (0, 'idle'), (1, 'progress'), (2, 'passed'), (3, 'warning'),
        (4, 'combustion-error'), (5, 'gas-type-error'), (6, 'aborted'),
        (7, None), (254, None), (255, 'unsupported'),
    ]:
        ab19ao19Add('op07_' + str(ab19ao19Byte), 7, 'progress',
                    {'feedback': [ab19ao19Byte]}, ab19ao19Feedback(
                        [ab19ao19Byte], 'mapped' if ab19ao19Label else 'unmapped',
                        ab19ao19Label))

    ab19ao19Base = [17, 34, 51, 0, 1, 0, 0, 1, 52, 18, 0, 100, 0]
    ab19ao19Pressure = {
        'feedback': dict(raw=[0], state='unmapped', grade='Hypothesis'),
        'pressure': dict(raw=[1, 0], state='mapped', number=1,
                         grade='Hypothesis', calculation='Proven'),
        'minimum': dict(raw=[0, 1], state='mapped', number=256,
                        grade='Hypothesis', calculation='Proven'),
        'maximum': dict(raw=[52, 18], state='mapped', number=4660,
                        grade='Hypothesis', calculation='Proven'),
        'step': dict(raw=[0], state='unit-conflict', grade='Hypothesis'),
        'flow': dict(raw=[100, 0], state='mapped', number=1,
                     grade='Hypothesis', calculation='Proven'),
    }
    ab19ao19Add('pressure_control', 8, 'pressure',
                {'logical_object': ab19ao19Base}, copy.deepcopy(ab19ao19Pressure))
    # Each word's low and high bytes change alone; answers are literal constants.
    for (ab19ao19Name, ab19ao19Position, ab19ao19Byte, ab19ao19Field,
         ab19ao19Word, ab19ao19Number) in [
        ('pressure_low', 4, 2, 'pressure', [2, 0], 2),
        ('pressure_high', 5, 1, 'pressure', [1, 1], 257),
        ('minimum_low', 6, 1, 'minimum', [1, 1], 257),
        ('minimum_high', 7, 2, 'minimum', [0, 2], 512),
        ('maximum_low', 8, 53, 'maximum', [53, 18], 4661),
        ('maximum_high', 9, 19, 'maximum', [52, 19], 4916),
        ('flow_low', 11, 200, 'flow', [200, 0], 2),
        ('flow_high', 12, 1, 'flow', [100, 1], 3.56),
    ]:
        ab19ao19Raw = ab19ao19Base.copy()
        ab19ao19Raw[ab19ao19Position] = ab19ao19Byte
        ab19ao19Fields = copy.deepcopy(ab19ao19Pressure)
        ab19ao19Fields[ab19ao19Field].update(raw=ab19ao19Word,
                                            number=ab19ao19Number)
        ab19ao19Add(ab19ao19Name, 8, 'pressure',
                    {'logical_object': ab19ao19Raw}, ab19ao19Fields)
    for ab19ao19Position in range(3):
        ab19ao19Raw = ab19ao19Base.copy()
        ab19ao19Raw[ab19ao19Position] = 255
        ab19ao19Add('prefix_' + str(ab19ao19Position), 8, 'pressure',
                    {'logical_object': ab19ao19Raw}, copy.deepcopy(ab19ao19Pressure))
    ab19ao19Raw = ab19ao19Base.copy()
    ab19ao19Raw[10] = 1
    ab19ao19Fields = copy.deepcopy(ab19ao19Pressure)
    ab19ao19Fields['step']['raw'] = [1]
    ab19ao19Add('step_one', 8, 'pressure', {'logical_object': ab19ao19Raw},
                ab19ao19Fields)
    ab19ao19Raw = ab19ao19Base.copy()
    ab19ao19Raw[3] = 6
    ab19ao19Fields = copy.deepcopy(ab19ao19Pressure)
    ab19ao19Fields['feedback']['raw'] = [6]
    ab19ao19Add('pressure_feedback', 8, 'pressure',
                {'logical_object': ab19ao19Raw}, ab19ao19Fields)
    ab19ao19Add('tail_and_sibling', 8, 'pressure',
                {'logical_object': ab19ao19Base + [255, 0], 'unmodelled': [0, 255]},
                copy.deepcopy(ab19ao19Pressure))
    # Explicit incomplete sets avoid implementing a production length dispatcher.
    for ab19ao19Length, ab19ao19Incomplete in [
        (0, ['feedback', 'pressure', 'minimum', 'maximum', 'step', 'flow']),
        (3, ['feedback', 'pressure', 'minimum', 'maximum', 'step', 'flow']),
        (4, ['pressure', 'minimum', 'maximum', 'step', 'flow']),
        (5, ['pressure', 'minimum', 'maximum', 'step', 'flow']),
        (6, ['minimum', 'maximum', 'step', 'flow']),
        (7, ['minimum', 'maximum', 'step', 'flow']),
        (8, ['maximum', 'step', 'flow']), (9, ['maximum', 'step', 'flow']),
        (10, ['step', 'flow']), (11, ['flow']), (12, ['flow']),
    ]:
        ab19ao19Fields = copy.deepcopy(ab19ao19Pressure)
        for ab19ao19Field in ab19ao19Incomplete:
            ab19ao19Fields[ab19ao19Field] = dict(raw=[], state='incomplete',
                                                grade='Hypothesis')
        # Single-byte fragments are explicitly enumerated, not decoded.
        for ab19ao19At, ab19ao19Field, ab19ao19Fragment in [
            (5, 'pressure', [1]), (7, 'minimum', [0]),
            (9, 'maximum', [52]), (12, 'flow', [100]),
        ]:
            if ab19ao19Length == ab19ao19At:
                ab19ao19Fields[ab19ao19Field]['raw'] = ab19ao19Fragment
        ab19ao19Add('length_' + str(ab19ao19Length), 8, 'pressure',
                    {'logical_object': ab19ao19Base[:ab19ao19Length]},
                    ab19ao19Fields, 'partial')
    ab19ao19Fields = {ab19ao19Field: dict(raw=[], state='incomplete',
                                          grade='Hypothesis')
                       for ab19ao19Field in ab19ao19Pressure}
    ab19ao19Add('missing_object', 8, 'pressure', {}, ab19ao19Fields, 'partial')
    ab19ao19Fields = copy.deepcopy(ab19ao19Pressure)
    for ab19ao19Field in ['pressure', 'minimum', 'maximum', 'flow']:
        ab19ao19Fields[ab19ao19Field].update(raw=[0, 0], number=0)
    ab19ao19Add('explicit_zero', 8, 'pressure',
                {'logical_object': [17, 34, 51, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
                ab19ao19Fields)
    for ab19ao19Name, ab19ao19Operation, ab19ao19View, ab19ao19Context in [
        ('primary', 8, 'pressure', {'primary': 180}),
        ('secondary', 8, 'pressure', {'secondary': 21}),
        ('direction', 8, 'pressure', {'direction': 'negative'}),
        ('view', 8, 'other', {}), ('operation', 9, 'pressure', {}),
        ('op2', 2, 'pressure', {}), ('op5', 5, 'pressure', {}),
    ]:
        ab19ao19Add('unknown_' + ab19ao19Name, ab19ao19Operation, ab19ao19View,
                    {'logical_object': ab19ao19Base}, {}, 'Unknown', ab19ao19Context)
    for ab19ao19Key in ['family', 'variant']:
        ab19ao19Add('opaque_' + ab19ao19Key, 8, 'pressure',
                    {'logical_object': ab19ao19Base}, copy.deepcopy(ab19ao19Pressure),
                    ab19ao19Context={ab19ao19Key: {'opaque': [0, 'candidate']}})
    for ab19ao19View in ['generic-result', 'specific-a-result', 'specific-b-result']:
        ab19ao19Add('wrong_view_' + ab19ao19View, 8, ab19ao19View,
                    {'logical_object': ab19ao19Base}, {}, 'Unknown')
    for ab19ao19Name, ab19ao19Raw in [('missing', {}), ('empty', {'feedback': []})]:
        ab19ao19Add('feedback_' + ab19ao19Name, 6, 'generic-result', ab19ao19Raw,
                    ab19ao19Feedback([], 'incomplete'), 'partial')
    ab19ao19Add('feedback_tail', 6, 'generic-result',
                {'feedback': [1, 255], 'other': [6]},
                ab19ao19Feedback([1, 255], 'mapped', 'in-progress'))
    ab19ao19Add('arguments_empty', 8, 'pressure', {'logical_object': ab19ao19Base},
                copy.deepcopy(ab19ao19Pressure), ab19ao19Arguments={})
    return ab19ao19Rows


def ab19ao19ExpectedErrors():
    ab19ao19Errors = [
        ('malformed', '{"context":'),
        ('duplicate_top', '{"context":{},"context":{},"fields":{}}'),
        ('duplicate_context', '{"context":{"view":"pressure","view":"progress"},"fields":{}}'),
        ('duplicate_fields', '{"context":{},"fields":{"feedback":[0],"feedback":[1]}}'),
        ('duplicate_arguments', '{"context":{},"fields":{},"arguments":{"x":0,"x":1}}'),
        ('wrong_root', '[]'), ('wrong_context', '{"context":[],"fields":{}}'),
        ('wrong_fields', '{"context":{},"fields":[]}'),
        ('wrong_arguments', '{"context":{},"fields":{},"arguments":[]}'),
    ]
    for ab19ao19Name, ab19ao19Value in [
        ('negative', -1), ('overflow', 256), ('fraction', 0.5), ('boolean', True),
        ('null', None), ('string', '0'), ('object', {}), ('nested', []),
    ]:
        ab19ao19Errors.append(('byte_' + ab19ao19Name, json.dumps({
            'context': dict(primary=181, secondary=20, operation=6,
                            direction='positive', view='generic-result'),
            'fields': {'feedback': [ab19ao19Value]}}, separators=(',', ':'))))
    ab19ao19Errors.append(('wrong_array', '{"context":{},"fields":{"feedback":0}}'))
    for ab19ao19Name, ab19ao19Input in [
        ('missing_context', {'fields': {}}), ('missing_fields', {'context': {}}),
        ('null_fields', {'context': {}, 'fields': None}),
        ('operation_string', {'context': dict(primary=181, secondary=20,
         operation='8', direction='positive', view='pressure'), 'fields': {}}),
        ('operation_bool', {'context': dict(primary=181, secondary=20,
         operation=True, direction='positive', view='pressure'), 'fields': {}}),
    ]:
        ab19ao19Errors.append((ab19ao19Name, json.dumps(ab19ao19Input,
                                                      separators=(',', ':'))))
    return [dict(id='ab19ao19_' + ab19ao19Name, json=ab19ao19Json,
                 expected='error; no successful result')
            for ab19ao19Name, ab19ao19Json in ab19ao19Errors]


ab19ao19ExpectedContract = {'api': 'Ab19Ao19Interpret(ab19ao19Input json.RawMessage) (json.RawMessage, error)',
 'package': 'vaillant',
 'dependencies': 'standard library',
 'input': {'required': ['context', 'fields'],
           'optional': ['arguments'],
           'context': {'primary': 181,
                       'secondary': 20,
                       'operation': 'integer',
                       'direction': 'string',
                       'view': 'explicit string'},
           'fields': 'object of integer byte arrays, each element 0..255',
           'arguments': 'object; no nonempty argument vocabulary is specified by this slice'},
 'output': {'required': ['context', 'raw', 'state', 'fields', 'physical', 'qualified'],
            'optional': ['arguments'],
            'physical': 'Unknown',
            'qualified': False,
            'field_required': ['raw', 'state'],
            'field_optional': ['number',
                               'label',
                               'flags',
                               'reserved',
                               'candidate_domain',
                               'grade',
                               'calculation'],
            'semantic_grade': 'Hypothesis',
            'exact_calculation': 'Proven'},
 'selection': [[6, 'positive', 'generic-result'],
               [6, 'positive', 'specific-a-result'],
               [6, 'positive', 'specific-b-result'],
               [7, 'positive', 'progress'],
               [8, 'positive', 'pressure']],
 'op06': {'generic-result': {'1': 'in-progress', '255': 'unsupported'},
          'specific-a-result': {'1': 'not-successful', 'invalid': [3, 255]},
          'specific-b-result': {'1': 'not-successful', 'invalid': [3, 255]},
          'unmapped': [0, 2]},
 'op07': {'0': 'idle',
          '1': 'progress',
          '2': 'passed',
          '3': 'warning',
          '4': 'combustion-error',
          '5': 'gas-type-error',
          '6': 'aborted',
          '255': 'unsupported',
          'unmapped': [7, 254]},
 'op08': {'field': 'logical_object',
          'extent': 13,
          'opaque_positions': [0, 1, 2],
          'layout': [['feedback', 3, 1, 'unmapped'],
                     ['pressure', 4, 2, 'LEu16 carrier'],
                     ['minimum', 6, 2, 'LEu16 carrier'],
                     ['maximum', 8, 2, 'LEu16 carrier'],
                     ['step', 10, 1, 'unit-conflict'],
                     ['flow', 11, 2, 'LEu16 / 100 l/min']],
          'pressure_unit': 'Unknown',
          'step_conflict': {'constant': 1, 'unit': 'mbar', 'default': 0}},
 'rules': {'unknown_selection': 'raw-only Unknown; no guessed view or identity',
           'identity_mismatch': 'raw-only Unknown',
           'raw_preservation': 'all context keys, raw fields, opaque prefix and tails; arguments '
                               'if supplied',
           'partial': 'retain complete independent fields; never decode a truncated word',
           'number_omission': ['incomplete', 'unmapped', 'unit-conflict', 'unknown-order'],
           'outside_domain': 'an explicitly defined carrier may keep number with '
                             'candidate_domain=false; none defined here',
           'isolation': 'deep independent context, raw and arguments; calls and sibling fields '
                        'share no mutable storage',
           'presence': 'missing, empty and explicit zero remain distinct through JSON round trips',
           'errors': 'malformed JSON, duplicate object keys at every depth, wrong JSON kinds, '
                     'invalid bytes: error and no successful result',
           'unknown_sibling': 'cannot erase complete independent fields',
           'qualification': 'never inferred from family, variant, selection or arithmetic',
           'effects': 'feedback alone proves no completed effect; physical adaptation, peer '
                      'effects and persistence Unknown',
           'op02': 'twenty-row union Unknown',
           'op05': '128 typed rows Unknown',
           'non_goals': ['command builder',
                         'global cache',
                         'generic catalog',
                         'metadata listing',
                         'registration',
                         'pending API import',
                         'runtime call site'],
           'parity': 'no eBUS MCP or GraphQL surface change'}}


class TestAb19Ao19MenuViews(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ab19ao19Page = (ab19ao19Root / 'architecture/ao20_b514_menu_views.md').read_text()
        ab19ao19Blocks = re.findall(r'^```json\n(.*?)^```$', cls.ab19ao19Page,
                                    flags=re.M | re.S)
        if len(ab19ao19Blocks) != 1:
            raise AssertionError('exactly one finite JSON contract table required')
        cls.ab19ao19Documents = {
            'page': json.loads(ab19ao19Blocks[0]),
            'fixture': json.loads((ab19ao19Root /
                'architecture/fixtures/ao20_b514_menu_views.json').read_text()),
        }

    def test_ab19ao19_exact_signature_and_contract(self):
        for ab19ao19Source, ab19ao19Document in self.ab19ao19Documents.items():
            with self.subTest(source=ab19ao19Source):
                self.assertEqual(set(ab19ao19Document), {'contract', 'cases', 'error_cases'})
                self.assertEqual(ab19ao19Document['contract'], ab19ao19ExpectedContract)
                self.assertEqual(json.dumps(ab19ao19Document['contract'], sort_keys=True),
                                 json.dumps(ab19ao19ExpectedContract, sort_keys=True))
        ab19ao19Go = re.findall(r'^```go\n(.*?)^```$', self.ab19ao19Page,
                                flags=re.M | re.S)
        self.assertEqual(ab19ao19Go, [
            'Ab19Ao19Interpret(ab19ao19Input json.RawMessage) (json.RawMessage, error)\n'])

    def test_ab19ao19_visible_field_and_selection_tables(self):
        ab19ao19Tables = re.findall(r'(?m)^\|.*\|$', self.ab19ao19Page)
        self.assertEqual(ab19ao19Tables, [
            '| Operation / positive view | Input field | Software interpretation (Hypothesis) |',
            '|---|---|---|',
            '| 6 / `generic-result` | isolated `feedback` | 1 in-progress; 255 unsupported; 0, 2 and other unmapped values have no label |',
            '| 6 / `specific-a-result` | isolated `feedback` | 1 not-successful; 3..255 invalid; 0 and 2 unmapped |',
            '| 6 / `specific-b-result` | isolated `feedback` | 1 not-successful; 3..255 invalid; 0 and 2 unmapped |',
            '| 7 / `progress` | isolated `feedback` | 0 idle; 1 progress; 2 passed; 3 warning; 4 combustion-error; 5 gas-type-error; 6 aborted; 255 unsupported; all others unmapped |',
            '| 8 / `pressure` | `logical_object` | extent 13; fields below; no command builder |',
            '| Logical position | Width | Field | Result and boundary |',
            '|---|---:|---|---|',
            '| 0..2 | 3 | opaque prefix | preserve; no prefix assertion, operation or identity decoding |',
            '| 3 | 1 | feedback | raw/unmapped; no borrowed OP07 enum |',
            '| 4 | 2 | pressure | LEu16 carrier only, no physical converter or pressure unit |',
            '| 6 | 2 | minimum | independent LEu16 carrier only |',
            '| 8 | 2 | maximum | independent LEu16 carrier only |',
            '| 10 | 1 | step | raw unit-conflict: constant 1 mbar versus default 0; no number or silent normalization |',
            '| 11 | 2 | flow | LEu16 / 100, l/min; exact carrier arithmetic Proven |',
        ])

    def test_ab19ao19_every_finite_tuple_against_independent_constants(self):
        ab19ao19Expected = ab19ao19ExpectedCases()
        self.assertEqual(len(ab19ao19Expected), 69)
        for ab19ao19Source, ab19ao19Document in self.ab19ao19Documents.items():
            self.assertEqual(len(ab19ao19Document['cases']), 69)
            for ab19ao19Actual, ab19ao19Oracle in zip(ab19ao19Document['cases'],
                                                     ab19ao19Expected):
                with self.subTest(source=ab19ao19Source, case=ab19ao19Oracle['id']):
                    self.assertEqual(ab19ao19Actual, ab19ao19Oracle)
                    self.assertEqual(json.dumps(ab19ao19Actual, sort_keys=True),
                                     json.dumps(ab19ao19Oracle, sort_keys=True))

    def test_ab19ao19_all_required_error_vectors(self):
        for ab19ao19Source, ab19ao19Document in self.ab19ao19Documents.items():
            with self.subTest(source=ab19ao19Source):
                self.assertEqual(len(ab19ao19Document['error_cases']), 23)
                self.assertEqual(ab19ao19Document['error_cases'], ab19ao19ExpectedErrors())

    def test_ab19ao19_grades_and_forbidden_numbers(self):
        for ab19ao19Document in self.ab19ao19Documents.values():
            for ab19ao19Case in ab19ao19Document['cases']:
                ab19ao19Result = ab19ao19Case['expected']
                self.assertEqual(ab19ao19Result['physical'], 'Unknown')
                self.assertIs(ab19ao19Result['qualified'], False)
                for ab19ao19Field in ab19ao19Result['fields'].values():
                    with self.subTest(case=ab19ao19Case['id'], field=ab19ao19Field):
                        self.assertEqual(ab19ao19Field['grade'], 'Hypothesis')
                        if ab19ao19Field['state'] in ('incomplete', 'unmapped', 'invalid',
                                                      'unit-conflict', 'unknown-order'):
                            self.assertNotIn('number', ab19ao19Field)
                        if 'calculation' in ab19ao19Field:
                            self.assertEqual(ab19ao19Field['calculation'], 'Proven')

    def test_ab19ao19_single_context_axis_controls(self):
        ab19ao19Rows = {ab19ao19Row['id']: ab19ao19Row for ab19ao19Row in ab19ao19ExpectedCases()}
        ab19ao19Control = ab19ao19Rows['ab19ao19_pressure_control']['input']
        for ab19ao19Axis in ['primary', 'secondary', 'operation', 'direction', 'view',
                             'family', 'variant']:
            ab19ao19Id = ('ab19ao19_opaque_' if ab19ao19Axis in ('family', 'variant')
                          else 'ab19ao19_unknown_') + ab19ao19Axis
            ab19ao19Case = ab19ao19Rows[ab19ao19Id]
            self.assertEqual(ab19ao19Case['input']['fields'], ab19ao19Control['fields'])
            self.assertEqual([ab19ao19Key for ab19ao19Key in ab19ao19Control['context']
                              if ab19ao19Case['input']['context'][ab19ao19Key] !=
                              ab19ao19Control['context'][ab19ao19Key]], [ab19ao19Axis])

    def test_ab19ao19_each_byte_axis_has_a_valid_control(self):
        ab19ao19Rows = {ab19ao19Row['id']: ab19ao19Row for ab19ao19Row in ab19ao19ExpectedCases()}
        ab19ao19Control = ab19ao19Rows['ab19ao19_pressure_control']['input']
        for ab19ao19Name, ab19ao19Position in [
            ('pressure_low', 4), ('pressure_high', 5), ('minimum_low', 6),
            ('minimum_high', 7), ('maximum_low', 8), ('maximum_high', 9),
            ('flow_low', 11), ('flow_high', 12), ('step_one', 10),
            ('pressure_feedback', 3), ('prefix_0', 0), ('prefix_1', 1), ('prefix_2', 2),
        ]:
            ab19ao19Input = ab19ao19Rows['ab19ao19_' + ab19ao19Name]['input']
            self.assertEqual(ab19ao19Input['context'], ab19ao19Control['context'])
            self.assertEqual([ab19ao19Index for ab19ao19Index, ab19ao19Pair in enumerate(zip(
                ab19ao19Input['fields']['logical_object'],
                ab19ao19Control['fields']['logical_object']))
                if ab19ao19Pair[0] != ab19ao19Pair[1]], [ab19ao19Position])

    def test_ab19ao19_presence_round_trip_contract_vectors(self):
        for ab19ao19Document in self.ab19ao19Documents.values():
            ab19ao19Rows = {ab19ao19Row['id']: json.loads(json.dumps(ab19ao19Row))
                            for ab19ao19Row in ab19ao19Document['cases']}
            self.assertNotIn('feedback', ab19ao19Rows['ab19ao19_feedback_missing']['input']['fields'])
            self.assertEqual(ab19ao19Rows['ab19ao19_feedback_empty']['input']['fields']['feedback'], [])
            self.assertEqual(ab19ao19Rows['ab19ao19_op06_generic_0']['input']['fields']['feedback'], [0])
            self.assertNotIn('arguments', ab19ao19Rows['ab19ao19_pressure_control']['input'])
            self.assertEqual(ab19ao19Rows['ab19ao19_arguments_empty']['input']['arguments'], {})
            self.assertEqual(ab19ao19Rows['ab19ao19_length_12']['expected']['state'], 'partial')
            self.assertEqual(ab19ao19Rows['ab19ao19_length_12']['expected']['fields']['pressure']['number'], 1)
            self.assertNotIn('number', ab19ao19Rows['ab19ao19_length_12']['expected']['fields']['flow'])
            self.assertEqual(ab19ao19Rows['ab19ao19_unknown_operation']['expected']['state'], 'Unknown')

    def test_ab19ao19_unique_ids_and_json_kinds(self):
        for ab19ao19Document in self.ab19ao19Documents.values():
            ab19ao19Ids = [ab19ao19Row['id'] for ab19ao19Row in
                           ab19ao19Document['cases'] + ab19ao19Document['error_cases']]
            self.assertEqual(len(ab19ao19Ids), len(set(ab19ao19Ids)))
            self.assertTrue(all(ab19ao19Id.startswith('ab19ao19_') for ab19ao19Id in ab19ao19Ids))
            for ab19ao19Row in ab19ao19Document['cases']:
                for ab19ao19Raw in ab19ao19Row['input']['fields'].values():
                    self.assertIs(type(ab19ao19Raw), list)
                    for ab19ao19Byte in ab19ao19Raw:
                        self.assertIs(type(ab19ao19Byte), int)
                        self.assertTrue(0 <= ab19ao19Byte <= 255)
                self.assertEqual(json.loads(json.dumps(ab19ao19Row)), ab19ao19Row)


if __name__ == '__main__':
    unittest.main()
