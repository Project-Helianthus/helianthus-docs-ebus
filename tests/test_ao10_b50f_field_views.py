"""Finite documentation checks; these do not implement or invoke the Go API."""
import copy
import json
from pathlib import Path
import re
import unittest

ab09ao09Root = Path(__file__).resolve().parents[1]
ab09ao09Page = ab09ao09Root / 'architecture/ao10-b50f-field-views.md'
ab09ao09Fixture = ab09ao09Root / 'architecture/fixtures/ao10_b50f_field_views.json'
ab09ao09Flags = ['burner', 'reformer-gas-valve', 'gas-flow', 'fan-power', 'valve']
ab09ao09Widths = {
    'temperature_one': 2, 'temperature_two': 2, 'temperature_three': 2,
    'stack_voltage': 2, 'error_one': 1, 'error_two': 1, 'error_three': 1,
    'demand': 1, 'feedback': 1, 'integrity_one': 1, 'integrity_two': 1,
}
ab09ao09Contract = {
    'api': 'func Ab09Ao09Interpret(ab09ao09Input json.RawMessage) (json.RawMessage, error)',
    'package': 'vaillant', 'dependencies': 'standard library only',
    'selection': [[181, 15, 0, 'positive', 'thermal-fields'],
                  [181, 15, 1, 'positive', 'thermal-fields'],
                  [181, 15, 2, 'positive', 'integrity-only'],
                  [181, 15, 3, 'positive', 'demand']],
    'output_keys': ['context', 'raw', 'state', 'fields', 'physical', 'qualified'],
    'optional_output_keys': ['arguments'],
    'physical': 'Unknown', 'qualified': False, 'semantic_grade': 'Hypothesis',
    'calculation_grade': 'Proven', 'states': ['Hypothesis', 'partial', 'Unknown'],
    'field_states': ['Hypothesis', 'incomplete', 'unit-conflict', 'unknown-order'],
    'arguments': {},
    'thermal_fields': {'0': ['temperature_one', 'temperature_two', 'temperature_three'],
                       '1': ['temperature_one', 'temperature_two', 'stack_voltage']},
    'error_fields': ['error_one', 'error_two', 'error_three'],
    'widths': ab09ao09Widths,
    'temperature_cases': [[[240, 255], -1], [[0, 0], 0], [[16, 0], 1]],
    'demand_flags': ab09ao09Flags,
    'demand_cases': [[0, [], 0], [1, ['burner'], 0], [31, ab09ao09Flags, 0],
                     [224, [], 224], [255, ab09ao09Flags, 224]],
    'feedback_cases': [[0, 'rejected'], [1, 'accepted'], [2, 'rejected'], [255, 'rejected']],
    'integrity_positions': {'0': [12, 13], '1': [12, 13], '2': [11, 12], '3': [4, 5]},
    'integrity_cases': [[12], [34]], 'integrity_word_order': 'Unknown',
    'crc_algorithm': 'Unknown', 'crc_validity': 'Unknown',
    'absolute_scalar_positions': 'Unknown',
    'unknown_selection': 'raw-only Unknown; fields={}; no guessed selection',
    'validation': ['malformed JSON', 'duplicate keys at every object depth',
                   'wrong JSON kinds', 'non-integer or out-of-range bytes',
                   'non-integer context primary/secondary/operation',
                   'missing required context selectors', 'nonempty arguments'],
    'preservation': ['every context key', 'every field byte including tails and unmodelled fields',
                     'arguments if supplied', 'missing versus empty versus explicit zero',
                     'independent deep copies', 'complete independent siblings'],
    'numeric_forbidden_states': ['incomplete', 'unit-conflict', 'unknown-order', 'Unknown'],
    'forbidden_inferences': ['native qualification', 'actuation', 'effects', 'persistence',
                            'validated CRC', 'voltage number', 'family applicability from view'],
}


def ab09ao09Input(ab09ao09Operation=0, ab09ao09View='thermal-fields', ab09ao09Fields=None):
    """Build a synthetic input tuple, never a semantic interpreter."""
    return {'context': {'primary': 181, 'secondary': 15, 'operation': ab09ao09Operation,
                        'direction': 'positive', 'view': ab09ao09View,
                        'family': 'synthetic-family', 'variant': {'opaque': 0}},
            'fields': {} if ab09ao09Fields is None else ab09ao09Fields}


def ab09ao09ExpectedCases():
    """Independent finite oracle: numbers and masks are literal constants."""
    ab09ao09Rows = []

    def ab09ao09Add(ab09ao09Id, ab09ao09InputValue, ab09ao09ExpectedValue):
        ab09ao09Rows.append({'id': 'ab09ao09_' + ab09ao09Id,
                            'input': ab09ao09InputValue, 'expected': ab09ao09ExpectedValue})

    ab09ao09Thermal = {'temperature_one': [240, 255], 'temperature_two': [0, 0],
                      'temperature_three': [16, 0], 'error_one': [0], 'error_two': [1],
                      'error_three': [2], 'integrity_one': [12], 'integrity_two': [34]}
    ab09ao09Add('op0_thermal', ab09ao09Input(ab09ao09Fields=ab09ao09Thermal), {
        'state': 'Hypothesis', 'numbers': {'temperature_one': -1, 'temperature_two': 0,
                                         'temperature_three': 1},
        'errors': {'error_one': 0, 'error_two': 1, 'error_three': 2},
        'stack_state': None, 'integrity': [[12], [34]]})
    ab09ao09Stack = copy.deepcopy(ab09ao09Thermal)
    del ab09ao09Stack['temperature_three']
    ab09ao09Stack['stack_voltage'] = [16, 0]
    ab09ao09Add('op1_thermal', ab09ao09Input(1, ab09ao09Fields=ab09ao09Stack), {
        'state': 'Hypothesis', 'numbers': {'temperature_one': -1, 'temperature_two': 0},
        'errors': {'error_one': 0, 'error_two': 1, 'error_three': 2},
        'stack_state': 'unit-conflict', 'integrity': [[12], [34]]})
    for ab09ao09Id, ab09ao09Raw, ab09ao09Number in [
            ('temperature_-1', [240, 255], -1), ('temperature_0', [0, 0], 0),
            ('temperature_1', [16, 0], 1)]:
        ab09ao09Add(ab09ao09Id, ab09ao09Input(ab09ao09Fields={'temperature_one': ab09ao09Raw}),
                    {'state': 'partial', 'numbers': {'temperature_one': ab09ao09Number}})
    for ab09ao09Raw, ab09ao09ExpectedFlags, ab09ao09Reserved in [
            (0, [], 0), (1, ['burner'], 0), (31, ab09ao09Flags, 0),
            (224, [], 224), (255, ab09ao09Flags, 224)]:
        ab09ao09Add('demand_' + str(ab09ao09Raw),
                    ab09ao09Input(3, 'demand', {'demand': [ab09ao09Raw], 'feedback': [1]}),
                    {'state': 'Hypothesis', 'flags': ab09ao09ExpectedFlags,
                     'reserved': ab09ao09Reserved, 'feedback': 'accepted', 'actuation': 'Unknown'})
    for ab09ao09Raw, ab09ao09Label in [(0, 'rejected'), (1, 'accepted'),
                                      (2, 'rejected'), (255, 'rejected')]:
        ab09ao09Add('feedback_' + str(ab09ao09Raw),
                    ab09ao09Input(3, 'demand', {'demand': [31], 'feedback': [ab09ao09Raw]}),
                    {'state': 'Hypothesis', 'flags': ab09ao09Flags, 'feedback': ab09ao09Label})
    ab09ao09Add('integrity_only', ab09ao09Input(2, 'integrity-only', {
        'integrity_one': [12], 'integrity_two': [34], 'temperature_one': [240, 255]}),
        {'state': 'Hypothesis', 'integrity': [[12], [34]], 'numbers': {}, 'crc_validity': 'Unknown'})
    ab09ao09Add('short_sibling', ab09ao09Input(ab09ao09Fields={
        'temperature_one': [240], 'temperature_two': [16, 0], 'error_one': [], 'error_two': [9]}),
        {'state': 'partial', 'numbers': {'temperature_two': 1}, 'errors': {'error_two': 9},
         'incomplete': ['temperature_one', 'error_one']})
    for ab09ao09Key, ab09ao09Value in [('primary', 180), ('secondary', 14), ('operation', 4),
                                      ('direction', 'negative'), ('view', 'unrecognised')]:
        ab09ao09ValueInput = ab09ao09Input(ab09ao09Fields={
            'temperature_one': [240, 255], 'unmodelled': [0, 255]})
        ab09ao09ValueInput['context'][ab09ao09Key] = ab09ao09Value
        ab09ao09Add('unknown_' + ab09ao09Key, ab09ao09ValueInput,
                    {'state': 'Unknown', 'fields': {}, 'physical': 'Unknown', 'qualified': False})
    for ab09ao09Key, ab09ao09Value in [('family', {'opaque': [1]}), ('variant', ['other', 0])]:
        ab09ao09ValueInput = ab09ao09Input(ab09ao09Fields={'temperature_one': [240, 255]})
        ab09ao09ValueInput['context'][ab09ao09Key] = ab09ao09Value
        ab09ao09Add('opaque_' + ab09ao09Key, ab09ao09ValueInput,
                    {'state': 'partial', 'numbers': {'temperature_one': -1},
                     'physical': 'Unknown', 'qualified': False})
    for ab09ao09Name in ['error_one', 'error_two', 'error_three']:
        ab09ao09ValueInput = ab09ao09Input(ab09ao09Fields=copy.deepcopy(ab09ao09Thermal))
        ab09ao09ValueInput['fields'][ab09ao09Name] = [255]
        ab09ao09Add('vary_' + ab09ao09Name, ab09ao09ValueInput,
                    {'state': 'Hypothesis', 'numbers': {'temperature_one': -1,
                     'temperature_two': 0, 'temperature_three': 1},
                     'changed_error': {ab09ao09Name: 255}})
    for ab09ao09Byte, ab09ao09ExpectedFlags, ab09ao09Reserved in [
            (2, ['reformer-gas-valve'], 0), (4, ['gas-flow'], 0),
            (8, ['fan-power'], 0), (16, ['valve'], 0),
            (32, [], 32), (64, [], 64), (128, [], 128)]:
        ab09ao09Add('bit_' + str(ab09ao09Byte),
                    ab09ao09Input(3, 'demand', {'demand': [ab09ao09Byte], 'feedback': [1]}),
                    {'state': 'Hypothesis', 'flags': ab09ao09ExpectedFlags,
                     'reserved': ab09ao09Reserved, 'feedback': 'accepted', 'actuation': 'Unknown'})
    for ab09ao09Byte in [0, 255]:
        ab09ao09Add('feedback_integrity_' + str(ab09ao09Byte),
                    ab09ao09Input(3, 'demand', {'demand': [31], 'feedback': [1],
                     'integrity_one': [ab09ao09Byte], 'integrity_two': [34]}),
                    {'state': 'Hypothesis', 'feedback': 'accepted',
                     'integrity': [[ab09ao09Byte], [34]], 'crc_validity': 'Unknown'})
    for ab09ao09Op, ab09ao09View in [
            (0, 'demand'), (0, 'integrity-only'), (1, 'demand'), (1, 'integrity-only'),
            (2, 'demand'), (2, 'thermal-fields'), (3, 'thermal-fields'), (3, 'integrity-only')]:
        ab09ao09Add('pair_' + str(ab09ao09Op) + '_' + ab09ao09View,
                    ab09ao09Input(ab09ao09Op, ab09ao09View,
                     {'temperature_one': [240, 255], 'demand': [31]}),
                    {'state': 'Unknown', 'fields': {}, 'physical': 'Unknown', 'qualified': False})
    for ab09ao09Kind in ['absent', 'empty']:
        ab09ao09ValueInput = ab09ao09Input(3, 'demand', {'demand': [0], 'feedback': [1]})
        ab09ao09Expected = {'state': 'Hypothesis', 'arguments_present': ab09ao09Kind == 'empty'}
        if ab09ao09Kind == 'empty':
            ab09ao09ValueInput['arguments'] = {}
            ab09ao09Expected['arguments'] = {}
        ab09ao09Add('arguments_' + ab09ao09Kind, ab09ao09ValueInput, ab09ao09Expected)
    for ab09ao09Op, ab09ao09Names in [(0, ['temperature_one', 'temperature_two', 'temperature_three']),
                                      (1, ['temperature_one', 'temperature_two'])]:
        for ab09ao09Name in ab09ao09Names:
            for ab09ao09Label, ab09ao09Raw, ab09ao09Number in [
                    ('negative', [240, 255], -1), ('zero', [0, 0], 0), ('positive', [16, 0], 1)]:
                ab09ao09ValueInput = copy.deepcopy(ab09ao09Rows[ab09ao09Op]['input'])
                ab09ao09ValueInput['fields'][ab09ao09Name] = ab09ao09Raw
                ab09ao09Expected = copy.deepcopy(ab09ao09Rows[ab09ao09Op]['expected'])
                ab09ao09Expected['numbers'][ab09ao09Name] = ab09ao09Number
                ab09ao09Add('op' + str(ab09ao09Op) + '_' + ab09ao09Name + '_' + ab09ao09Label,
                            ab09ao09ValueInput, ab09ao09Expected)
    for ab09ao09Name in ['error_one', 'error_two', 'error_three']:
        ab09ao09ValueInput = copy.deepcopy(ab09ao09Rows[1]['input'])
        ab09ao09ValueInput['fields'][ab09ao09Name] = [255]
        ab09ao09Expected = copy.deepcopy(ab09ao09Rows[1]['expected'])
        ab09ao09Expected['errors'][ab09ao09Name] = 255
        ab09ao09Add('op1_vary_' + ab09ao09Name, ab09ao09ValueInput, ab09ao09Expected)
    for ab09ao09Byte in [0, 255]:
        ab09ao09Add('feedback_integrity_two_' + str(ab09ao09Byte),
                    ab09ao09Input(3, 'demand', {'demand': [31], 'feedback': [1],
                     'integrity_one': [12], 'integrity_two': [ab09ao09Byte]}),
                    {'state': 'Hypothesis', 'feedback': 'accepted',
                     'integrity': [[12], [ab09ao09Byte]], 'crc_validity': 'Unknown'})
    return ab09ao09Rows


def ab09ao09ExpectedAxes():
    ab09ao09Rows = []
    for ab09ao09Name, ab09ao09Width in ab09ao09Widths.items():
        ab09ao09CompleteState = ('unit-conflict' if ab09ao09Name == 'stack_voltage'
                                else 'unknown-order' if ab09ao09Name in
                                ['integrity_one', 'integrity_two'] else 'Hypothesis')
        ab09ao09Variants = [('missing', None, 'incomplete'), ('empty', [], 'incomplete'),
                            ('zero', [0, 0] if ab09ao09Width == 2 else [0], ab09ao09CompleteState),
                            ('complete', [16, 0] if ab09ao09Width == 2 else [7], ab09ao09CompleteState),
                            ('tail', [16, 0, 255] if ab09ao09Width == 2 else [7, 255], ab09ao09CompleteState)]
        if ab09ao09Width == 2:
            ab09ao09Variants.append(('short', [16], 'incomplete'))
        for ab09ao09Presence, ab09ao09Raw, ab09ao09State in ab09ao09Variants:
            ab09ao09Row = {'id': 'ab09ao09_' + ab09ao09Name + '_' + ab09ao09Presence,
                           'field': ab09ao09Name, 'presence': ab09ao09Presence, 'state': ab09ao09State}
            if ab09ao09Presence != 'missing':
                ab09ao09Row['raw'] = ab09ao09Raw
            if ab09ao09Name in ['temperature_one', 'temperature_two', 'temperature_three']:
                if ab09ao09Presence in ['zero', 'complete', 'tail']:
                    ab09ao09Row['number'] = {'zero': 0, 'complete': 1, 'tail': 1}[ab09ao09Presence]
            ab09ao09Rows.append(ab09ao09Row)
    return ab09ao09Rows


def ab09ao09ExpectedInvalid():
    ab09ao09Rows = [
        ('malformed', '{'), ('duplicate_root', '{"context":{},"context":{},"fields":{}}'),
        ('duplicate_context', '{"context":{"primary":181,"primary":181},"fields":{}}'),
        ('duplicate_field', '{"context":{},"fields":{"demand":[1],"demand":[1]}}'),
        ('duplicate_opaque', '{"context":{"variant":{"x":1,"x":2}},"fields":{}}'),
        ('array_root', '[]'), ('null_root', 'null')]
    for ab09ao09Id, ab09ao09Value in [('negative', [-1]), ('overflow', [256]),
            ('fraction', [1.5]), ('boolean', [True]), ('string', ['1']),
            ('null_element', [None]), ('nonarray', 1), ('null_array', None)]:
        ab09ao09Rows.append((ab09ao09Id, json.dumps(ab09ao09Input(
            ab09ao09Fields={'temperature_one': ab09ao09Value}), separators=(',', ':'))))
    for ab09ao09Key in ['primary', 'secondary', 'operation', 'direction', 'view']:
        for ab09ao09Kind in ['missing', 'wrong-kind']:
            ab09ao09ValueInput = ab09ao09Input(3, 'demand')
            if ab09ao09Kind == 'missing':
                del ab09ao09ValueInput['context'][ab09ao09Key]
            else:
                ab09ao09ValueInput['context'][ab09ao09Key] = True
            ab09ao09Rows.append(('selector_' + ab09ao09Key + '_' + ab09ao09Kind,
                                json.dumps(ab09ao09ValueInput, separators=(',', ':'))))
    for ab09ao09Key, ab09ao09Value in [('context', None), ('fields', []),
                                      ('arguments', None), ('arguments', {'flag': 1})]:
        ab09ao09ValueInput = ab09ao09Input(3, 'demand')
        ab09ao09ValueInput[ab09ao09Key] = ab09ao09Value
        ab09ao09Rows.append(('kind_' + ab09ao09Key + ('_nonempty' if isinstance(ab09ao09Value, dict) else ''),
                            json.dumps(ab09ao09ValueInput, separators=(',', ':'))))
    return [{'id': 'ab09ao09_' + ab09ao09Id, 'json': ab09ao09Json,
             'expected': {'error': True, 'successful_result': False}}
            for ab09ao09Id, ab09ao09Json in ab09ao09Rows]


def ab09ao09Pairs(ab09ao09PairsValue):
    ab09ao09Object = {}
    for ab09ao09Key, ab09ao09Value in ab09ao09PairsValue:
        if ab09ao09Key in ab09ao09Object:
            raise ValueError('duplicate contract key')
        ab09ao09Object[ab09ao09Key] = ab09ao09Value
    return ab09ao09Object


def ab09ao09ParsePage(ab09ao09Text):
    ab09ao09Matches = re.findall(
        r'<!-- ab09ao09-contract:start -->\s*```json\n(.*?)\n```\s*<!-- ab09ao09-contract:end -->',
        ab09ao09Text, re.S)
    if len(ab09ao09Matches) != 1:
        raise ValueError('expected one finite contract table')
    return json.loads(ab09ao09Matches[0], object_pairs_hook=ab09ao09Pairs)


class Ab09Ao09ContractTests(unittest.TestCase):
    def setUp(self):
        self.ab09ao09PageText = ab09ao09Page.read_text()
        self.ab09ao09PageData = ab09ao09ParsePage(self.ab09ao09PageText)
        self.ab09ao09FixtureData = json.loads(ab09ao09Fixture.read_text(), object_pairs_hook=ab09ao09Pairs)
        self.ab09ao09ExpectedJson = json.dumps({
            'contract': ab09ao09Contract, 'cases': ab09ao09ExpectedCases(),
            'field_axes': ab09ao09ExpectedAxes(), 'invalid_json': ab09ao09ExpectedInvalid(),
        }, sort_keys=True, separators=(',', ':'))

    def ab09ao09AssertContract(self, ab09ao09Data):
        self.assertEqual(set(ab09ao09Data), {'contract', 'cases', 'invalid_json', 'field_axes'})
        # JSON comparison keeps bool distinct from integer zero/one and avoids
        # constructing enormous diffs for each independently killed mutant.
        self.assertTrue(json.dumps(ab09ao09Data, sort_keys=True, separators=(',', ':')) ==
                        self.ab09ao09ExpectedJson, 'finite contract differs from independent constants')

    def TestAb09Ao09PageIndependentConstants(self):
        self.ab09ao09AssertContract(self.ab09ao09PageData)

    def TestAb09Ao09FixtureIndependentConstants(self):
        self.ab09ao09AssertContract(self.ab09ao09FixtureData)

    def TestAb09Ao09PageFixtureParity(self):
        self.assertEqual(self.ab09ao09PageData, self.ab09ao09FixtureData)
        self.assertEqual(len(self.ab09ao09FixtureData['cases']), 65)
        self.assertEqual(len(self.ab09ao09FixtureData['field_axes']), 59)
        self.assertEqual(len(self.ab09ao09FixtureData['invalid_json']), 29)

    def TestAb09Ao09EveryFieldValueMutation(self):
        # Every scalar and container alternative of the published finite table
        # is changed independently. These are contract mutants, not Go mutants.
        def ab09ao09Leaves(ab09ao09Value, ab09ao09Path=()):
            if isinstance(ab09ao09Value, dict):
                for ab09ao09Key, ab09ao09Child in ab09ao09Value.items():
                    yield from ab09ao09Leaves(ab09ao09Child, ab09ao09Path + (ab09ao09Key,))
            elif isinstance(ab09ao09Value, list):
                for ab09ao09Index, ab09ao09Child in enumerate(ab09ao09Value):
                    yield from ab09ao09Leaves(ab09ao09Child, ab09ao09Path + (ab09ao09Index,))
            else:
                yield ab09ao09Path
        self.ab09ao09MutationCount = 0
        for ab09ao09Source in [self.ab09ao09PageData, self.ab09ao09FixtureData]:
            for ab09ao09Path in ab09ao09Leaves(ab09ao09Source):
                ab09ao09Mutant = copy.deepcopy(ab09ao09Source)
                ab09ao09Target = ab09ao09Mutant
                for ab09ao09Key in ab09ao09Path[:-1]:
                    ab09ao09Target = ab09ao09Target[ab09ao09Key]
                ab09ao09Target[ab09ao09Path[-1]] = 'ab09ao09_mutated'
                with self.subTest(path=ab09ao09Path), self.assertRaises(AssertionError):
                    self.ab09ao09AssertContract(ab09ao09Mutant)
                self.ab09ao09MutationCount += 1
        self.assertGreater(self.ab09ao09MutationCount, 1000)

    def TestAb09Ao09MissingAlternativeMutations(self):
        for ab09ao09Key in ['cases', 'field_axes', 'invalid_json']:
            for ab09ao09Index in range(len(self.ab09ao09PageData[ab09ao09Key])):
                ab09ao09Mutant = copy.deepcopy(self.ab09ao09PageData)
                del ab09ao09Mutant[ab09ao09Key][ab09ao09Index]
                with self.subTest(table=ab09ao09Key, index=ab09ao09Index), self.assertRaises(AssertionError):
                    self.ab09ao09AssertContract(ab09ao09Mutant)

    def TestAb09Ao09BooleanIsNotInteger(self):
        for ab09ao09Boolean in [True, False]:
            ab09ao09Mutant = copy.deepcopy(self.ab09ao09PageData)
            ab09ao09Mutant['cases'][0]['input']['fields']['error_two'] = [ab09ao09Boolean]
            with self.subTest(boolean=ab09ao09Boolean), self.assertRaises(AssertionError):
                self.ab09ao09AssertContract(ab09ao09Mutant)

    def TestAb09Ao09RequiredDiscriminatingContractMutations(self):
        ab09ao09Mutations = [
            ('unsigned', ('cases', 0, 'expected', 'numbers', 'temperature_one'), 4095),
            ('error_alias', ('cases', 0, 'expected', 'errors', 'error_two'), 0),
            ('voltage', ('cases', 1, 'expected', 'numbers', 'stack_voltage'), 1),
            ('actuation', ('cases', 5, 'expected', 'actuation'), 'Proven'),
            ('crc', ('contract', 'crc_validity'), 'Proven'),
            ('feedback_integrity', ('cases', 11, 'expected', 'feedback'), 'Unknown'),
            ('native_grade', ('contract', 'physical'), 'Proven'),
        ]
        self.ab09ao09AssertContract(self.ab09ao09PageData)
        for ab09ao09Name, ab09ao09Path, ab09ao09Value in ab09ao09Mutations:
            ab09ao09Mutant = copy.deepcopy(self.ab09ao09PageData)
            ab09ao09Target = ab09ao09Mutant
            for ab09ao09Key in ab09ao09Path[:-1]:
                ab09ao09Target = ab09ao09Target[ab09ao09Key]
            ab09ao09Target[ab09ao09Path[-1]] = ab09ao09Value
            with self.subTest(mutation=ab09ao09Name), self.assertRaises(AssertionError):
                self.ab09ao09AssertContract(ab09ao09Mutant)

    def TestAb09Ao09RoundTripPresence(self):
        for ab09ao09Source in [self.ab09ao09PageData, self.ab09ao09FixtureData]:
            self.assertEqual(json.loads(json.dumps(ab09ao09Source)), ab09ao09Source)
        ab09ao09ById = {ab09ao09Row['id']: ab09ao09Row for ab09ao09Row in self.ab09ao09PageData['field_axes']}
        for ab09ao09Name in ab09ao09Widths:
            self.assertNotIn('raw', ab09ao09ById['ab09ao09_' + ab09ao09Name + '_missing'])
            self.assertEqual(ab09ao09ById['ab09ao09_' + ab09ao09Name + '_empty']['raw'], [])
            self.assertEqual(ab09ao09ById['ab09ao09_' + ab09ao09Name + '_zero']['raw'],
                             [0, 0] if ab09ao09Widths[ab09ao09Name] == 2 else [0])

    def TestAb09Ao09DuplicateTableKeysRejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"fields":{},"fields":{}}', object_pairs_hook=ab09ao09Pairs)
        with self.assertRaises(ValueError):
            json.loads('{"context":{"x":1,"x":2}}', object_pairs_hook=ab09ao09Pairs)

    def TestAb09Ao09TableMarkers(self):
        with self.assertRaises(ValueError):
            ab09ao09ParsePage(self.ab09ao09PageText + self.ab09ao09PageText)
        with self.assertRaises(ValueError):
            ab09ao09ParsePage(self.ab09ao09PageText.replace('ab09ao09-contract:start', 'ab09ao09-absent'))


def load_tests(ab09ao09Loader, ab09ao09Tests, ab09ao09Pattern):
    # Explicit loader preserves the issue's required TestAb09Ao09 test prefix.
    return unittest.TestSuite(Ab09Ao09ContractTests(ab09ao09Name)
                              for ab09ao09Name in sorted(dir(Ab09Ao09ContractTests))
                              if ab09ao09Name.startswith('TestAb09Ao09'))


if __name__ == '__main__':
    unittest.main()
