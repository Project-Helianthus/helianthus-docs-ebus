"""Documentation/scenario checks, not an implementation of the Go evaluator."""
import copy
import json
from pathlib import Path
import unittest

ab03ap03Root = Path(__file__).resolve().parents[1]
ab03ap03PagePath = ab03ap03Root / 'architecture/ap04_b531_ordinary_limit.md'
ab03ap03FixturePath = ab03ap03Root / 'architecture/fixtures/ap04_b531_ordinary_limit.json'

# Independent constants: do not obtain expected numbers or rules from the page.
ab03ap03Rules = {
    'signature': 'Ab03Ap03Evaluate(ab03ap03Input json.RawMessage) (json.RawMessage, error)',
    'package': 'vaillant', 'primary': 181, 'secondary': 49, 'operation': 3,
    'direction': 'local', 'view': 'ordinary-limit', 'rows': 9,
    'slot_order': [0, 1, 2, 3, 4, 5, 6, 7, 8], 'special_slot': 1,
    'admission': 'registered && capable && !failure',
    'sum_slots': 'admitted except slot 1', 'sum_width': 'u64', 'scale': 1,
    'effective': 'token_sum < maximum_sum && limited != 0',
    'requested_state': 'gate == 0 ? 0 : (effective known ? 1 + effective : Unknown)',
    'candidate_grade': 'Hypothesis', 'calculation_grade': 'Proven',
    'physical': 'Unknown', 'qualified': False,
    'unknown_selectors': 'raw-only Unknown',
    'incomplete_fields': 'partial; independent siblings retained',
    'special_admitted': 'ordinary subtotals retained; effective Unknown',
    'errors': 'error; no successful result',
    'copies': 'deep independent input, output, and later results',
    'argument_types': {'rows': 'array[9]', 'registered': 'bool', 'capable': 'bool',
                       'failure': 'bool', 'token': 'u32', 'maximum': 'u32', 'limited': 'u32'},
    'output_required': ['context', 'raw', 'state', 'fields', 'physical', 'qualified'],
    'output_optional': ['arguments'], 'unknown_number': 'absent',
    'field_lengths': {'gate': 1}, 'u8_max': 255, 'u16_max': 65535,
    'u32_max': 4294967295, 'duplicates': 'reject anywhere',
    'context': 'preserve absent, null, zero, opaque keys distinctly',
    'arguments': 'preserve unknown extra keys; preserve absence on raw-only result',
}
ab03ap03Expected = {
    'ordinary': [[0], 3, 4, True, 2, 'complete'],
    'equality': [[0], 4, 4, False, 1, 'complete'],
    'limited-zero': [[0], 3, 4, False, 1, 'complete'],
    'gate-zero': [[0], 3, 4, True, 0, 'complete'],
    'gate-high': [[0], 3, 4, True, 2, 'complete'],
    'wide': [[0, 2], 8589934590, 8589934590, False, 1, 'complete'],
    'deny-registered': [[], 0, 0, False, 1, 'complete'],
    'deny-capable': [[], 0, 0, False, 1, 'complete'],
    'deny-failure': [[], 0, 0, False, 1, 'complete'],
    'special': [[0, 1], 3, 4, 'Unknown', 'Unknown', 'complete'],
    'special-zero': [[0, 1], 3, 4, 'Unknown', 0, 'complete'],
    'special-deny-registered': [[0], 3, 4, True, 2, 'complete'],
    'special-deny-capable': [[0], 3, 4, True, 2, 'complete'],
    'special-deny-failure': [[0], 3, 4, True, 2, 'complete'],
    'empty': [[], 0, 0, False, 1, 'complete'],
    'gate-missing': [[0], 3, 4, True, 'Unknown', 'partial'],
    'gate-empty': [[0], 3, 4, True, 'Unknown', 'partial'],
    'gate-overlong': [[0], 3, 4, True, 'Unknown', 'partial'],
    'maximum-zero': [[0], 3, 0, False, 1, 'complete'],
    'token-zero': [[0], 0, 4, True, 2, 'complete'],
    'limited-max': [[0], 3, 4, True, 2, 'complete'],
}


def ab03ap03Unique(ab03ap03Pairs):
    ab03ap03Object = {}
    for ab03ap03Key, ab03ap03Value in ab03ap03Pairs:
        if ab03ap03Key in ab03ap03Object:
            raise ValueError('duplicate key')
        ab03ap03Object[ab03ap03Key] = ab03ap03Value
    return ab03ap03Object


def ab03ap03Decode(ab03ap03Text):
    return json.loads(ab03ap03Text, object_pairs_hook=ab03ap03Unique,
                      parse_constant=lambda ab03ap03Value: (_ for _ in ()).throw(ValueError(ab03ap03Value)))


def ab03ap03Transition(ab03ap03Rows, ab03ap03Limited, ab03ap03Gate):
    """Bounded tuple oracle only; no JSON API or semantic result implementation."""
    ab03ap03Admitted = [ab03ap03Index for ab03ap03Index in range(9)
                       if (ab03ap03Rows[ab03ap03Index]['registered']
                           and ab03ap03Rows[ab03ap03Index]['capable']
                           and not ab03ap03Rows[ab03ap03Index]['failure'])]
    ab03ap03Ordinary = [ab03ap03Index for ab03ap03Index in ab03ap03Admitted if ab03ap03Index != 1]
    ab03ap03Token = sum(ab03ap03Rows[ab03ap03Index]['token'] for ab03ap03Index in ab03ap03Ordinary)
    ab03ap03Maximum = sum(ab03ap03Rows[ab03ap03Index]['maximum'] for ab03ap03Index in ab03ap03Ordinary)
    ab03ap03Effective = ('Unknown' if 1 in ab03ap03Admitted else
                        ab03ap03Token < ab03ap03Maximum and ab03ap03Limited != 0)
    ab03ap03CompleteGate = isinstance(ab03ap03Gate, list) and len(ab03ap03Gate) == 1
    ab03ap03Requested = 'Unknown'
    if ab03ap03CompleteGate:
        if ab03ap03Gate[0] == 0:
            ab03ap03Requested = 0
        elif ab03ap03Effective != 'Unknown':
            ab03ap03Requested = 1 + int(ab03ap03Effective)
    return [ab03ap03Admitted, ab03ap03Token, ab03ap03Maximum, ab03ap03Effective,
            ab03ap03Requested, 'complete' if ab03ap03CompleteGate else 'partial']


class TestAb03Ap03Contract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ab03ap03Page = ab03ap03PagePath.read_text()
        cls.ab03ap03Fixture = ab03ap03Decode(ab03ap03FixturePath.read_text())
        cls.ab03ap03Cases = {ab03ap03Case['id'].removeprefix('ab03ap03-'): ab03ap03Case
                           for ab03ap03Case in cls.ab03ap03Fixture['cases']}

    def ab03ap03Validate(self, ab03ap03Input):
        """Assertions about synthetic input shapes, not a callable runtime API."""
        self.assertIs(type(ab03ap03Input), dict)
        for ab03ap03Key in ('context', 'fields'):
            self.assertIs(type(ab03ap03Input[ab03ap03Key]), dict)
        for ab03ap03Bytes in ab03ap03Input['fields'].values():
            self.assertIs(type(ab03ap03Bytes), list)
            for ab03ap03Byte in ab03ap03Bytes:
                self.assertIs(type(ab03ap03Byte), int)
                self.assertLessEqual(0, ab03ap03Byte)
                self.assertLessEqual(ab03ap03Byte, 255)
        if 'arguments' in ab03ap03Input:
            self.assertIs(type(ab03ap03Input['arguments']), dict)
        ab03ap03Context = ab03ap03Input['context']
        if any(type(ab03ap03Context.get(ab03ap03Key)) is not type(ab03ap03Value)
               or ab03ap03Context.get(ab03ap03Key) != ab03ap03Value
               for ab03ap03Key, ab03ap03Value in
               [('primary', 181), ('secondary', 49), ('operation', 3),
                ('direction', 'local'), ('view', 'ordinary-limit')]):
            return
        ab03ap03Arguments = ab03ap03Input['arguments']
        ab03ap03Rows = ab03ap03Arguments['rows']
        self.assertIs(type(ab03ap03Rows), list)
        self.assertEqual(len(ab03ap03Rows), 9)
        ab03ap03Numbers = [ab03ap03Arguments['limited']]
        for ab03ap03Row in ab03ap03Rows:
            self.assertIs(type(ab03ap03Row), dict)
            for ab03ap03Key in ('registered', 'capable', 'failure'):
                self.assertIs(type(ab03ap03Row[ab03ap03Key]), bool)
            ab03ap03Numbers.extend([ab03ap03Row['token'], ab03ap03Row['maximum']])
        for ab03ap03Number in ab03ap03Numbers:
            self.assertIs(type(ab03ap03Number), int)
            self.assertLessEqual(0, ab03ap03Number)
            self.assertLessEqual(ab03ap03Number, 4294967295)

    def test_ab03ap03_normative_table_and_signature(self):
        ab03ap03Table = {}
        for ab03ap03Line in self.ab03ap03Page.splitlines():
            if ab03ap03Line.startswith('| ') and ' | `' in ab03ap03Line:
                ab03ap03Key, ab03ap03Value = ab03ap03Line[2:-2].split(' | ', 1)
                self.assertNotIn(ab03ap03Key, ab03ap03Table)
                ab03ap03Table[ab03ap03Key] = ab03ap03Decode(ab03ap03Value.strip('`'))
        self.assertEqual(ab03ap03Table, ab03ap03Rules)
        ab03ap03Signature = self.ab03ap03Page.split('```go\n')[1].split('\n```')[0]
        self.assertEqual(ab03ap03Signature, 'func ' + ab03ap03Rules['signature'])

    def test_ab03ap03_result_shapes(self):
        ab03ap03Rows = self.ab03ap03Page.split('| Semantic field | Result shape |\n')[1].split('\n\n')[0].splitlines()[1:]
        self.assertEqual(ab03ap03Rows, [
            '| gate | raw byte array when present, state complete or incomplete, number only for exactly one byte |',
            '| slots | raw rows, state complete, ordered per-slot raw values and admitted Boolean |',
            '| admitted | raw rows, state complete, indices of all admitted slots including slot 1 |',
            '| token_sum | raw ordinary admitted token values, state complete, u64 number |',
            '| maximum_sum | raw ordinary admitted maximum values, state complete, u64 number |',
            '| effective | raw limited and admitted rows, state complete with Boolean number or Unknown without number |',
            '| requested_state | raw gate and effective evidence, state complete with integer number or Unknown without number |',
        ])

    def test_ab03ap03_fixture_constants_and_transitions(self):
        self.assertEqual(self.ab03ap03Fixture['provenance'], 'synthetic')
        self.assertEqual(set(self.ab03ap03Cases), set(ab03ap03Expected))
        self.assertEqual(len(self.ab03ap03Cases), len(self.ab03ap03Fixture['cases']))
        for ab03ap03Name, ab03ap03ExpectedTuple in ab03ap03Expected.items():
            with self.subTest(case=ab03ap03Name):
                ab03ap03Case = self.ab03ap03Cases[ab03ap03Name]
                self.ab03ap03Validate(ab03ap03Case['input'])
                # JSON comparison distinguishes true from 1 and false from 0.
                self.assertEqual(json.dumps(ab03ap03Case['expected']), json.dumps(ab03ap03ExpectedTuple))
                ab03ap03Input = ab03ap03Case['input']
                self.assertEqual(json.dumps(ab03ap03Transition(
                    ab03ap03Input['arguments']['rows'], ab03ap03Input['arguments']['limited'],
                    ab03ap03Input['fields'].get('gate'))), json.dumps(ab03ap03ExpectedTuple))

    def test_ab03ap03_page_scenario_tuples(self):
        ab03ap03Lines = self.ab03ap03Page.split('| Case | token sum | maximum sum | effective | requested state |\n')[1].split('\n\n')[0].splitlines()[1:]
        ab03ap03Names = ['ordinary', 'equality', 'limited-zero', 'gate-zero', 'gate-high',
                         'wide', 'special', 'special-zero', 'empty']
        self.assertEqual(len(ab03ap03Lines), len(ab03ap03Names))
        for ab03ap03Line, ab03ap03Name in zip(ab03ap03Lines, ab03ap03Names):
            ab03ap03Cells = ab03ap03Line[2:-2].split(' | ')
            self.assertEqual(ab03ap03Cells[0], ab03ap03Name)
            ab03ap03Tuple = ['Unknown' if ab03ap03Cell == 'Unknown' else json.loads(ab03ap03Cell)
                            for ab03ap03Cell in ab03ap03Cells[1:]]
            self.assertEqual(json.dumps(ab03ap03Tuple), json.dumps(ab03ap03Expected[ab03ap03Name][1:5]))
            self.assertEqual(json.dumps(ab03ap03Tuple), json.dumps(self.ab03ap03Cases[ab03ap03Name]['expected'][1:5]))

    def test_ab03ap03_each_slot_and_each_admission_predicate(self):
        for ab03ap03Index in range(9):
            ab03ap03Input = copy.deepcopy(self.ab03ap03Cases['empty']['input'])
            ab03ap03Input['arguments']['rows'][ab03ap03Index].update(
                registered=True, capable=True, failure=False, token=3, maximum=4)
            ab03ap03Rows = ab03ap03Input['arguments']['rows']
            self.ab03ap03Validate(ab03ap03Input)
            self.assertEqual(ab03ap03Transition(ab03ap03Rows, 1, [2]),
                             [[1], 0, 0, 'Unknown', 'Unknown', 'complete'] if ab03ap03Index == 1
                             else [[ab03ap03Index], 3, 4, True, 2, 'complete'])
            for ab03ap03Key, ab03ap03Denied in [('registered', False), ('capable', False), ('failure', True)]:
                with self.subTest(slot=ab03ap03Index, predicate=ab03ap03Key):
                    ab03ap03Changed = copy.deepcopy(ab03ap03Rows)
                    ab03ap03Changed[ab03ap03Index][ab03ap03Key] = ab03ap03Denied
                    self.assertEqual(ab03ap03Transition(ab03ap03Changed, 1, [2]), [[], 0, 0, False, 1, 'complete'])

    def test_ab03ap03_bounded_strict_comparison_gate_and_limit(self):
        for ab03ap03Token in range(5):
            for ab03ap03Maximum in range(5):
                for ab03ap03Limited in (0, 1, 4294967295):
                    for ab03ap03Gate in (0, 1, 2, 128, 255):
                        ab03ap03Rows = copy.deepcopy(self.ab03ap03Cases['ordinary']['input']['arguments']['rows'])
                        ab03ap03Rows[0].update(token=ab03ap03Token, maximum=ab03ap03Maximum)
                        # Membership in a finite truth set is independent of the oracle's '<'.
                        ab03ap03Effective = (ab03ap03Token, ab03ap03Maximum) in {
                            (0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (1, 3), (1, 4),
                            (2, 3), (2, 4), (3, 4)} and ab03ap03Limited in (1, 4294967295)
                        ab03ap03Requested = 0 if ab03ap03Gate == 0 else {False: 1, True: 2}[ab03ap03Effective]
                        self.assertEqual(ab03ap03Transition(ab03ap03Rows, ab03ap03Limited, [ab03ap03Gate]),
                                         [[0], ab03ap03Token, ab03ap03Maximum, ab03ap03Effective, ab03ap03Requested, 'complete'])

    def test_ab03ap03_unsupported_identity_axes_are_distinct(self):
        ab03ap03Entries = self.ab03ap03Fixture['unsupported']
        self.assertEqual(len(ab03ap03Entries), 20)
        self.assertEqual({ab03ap03Entry['id'] for ab03ap03Entry in ab03ap03Entries},
                         {'ab03ap03-' + ab03ap03Key + '-' + ab03ap03Kind
                          for ab03ap03Key in ('primary', 'secondary', 'operation', 'direction', 'view')
                          for ab03ap03Kind in ('other', 'null', 'zero', 'absent')})
        ab03ap03Selectors = {'primary': 181, 'secondary': 49, 'operation': 3,
                            'direction': 'local', 'view': 'ordinary-limit'}
        for ab03ap03Entry in ab03ap03Entries:
            ab03ap03Input = ab03ap03Entry['input']
            self.ab03ap03Validate(ab03ap03Input)
            ab03ap03Key, ab03ap03Kind = ab03ap03Entry['id'].removeprefix('ab03ap03-').split('-')
            self.assertEqual(ab03ap03Entry['expected_state'], 'Unknown')
            self.assertEqual({ab03ap03Name: ab03ap03Input['context'][ab03ap03Name]
                              for ab03ap03Name in ab03ap03Selectors if ab03ap03Name != ab03ap03Key},
                             {ab03ap03Name: ab03ap03Value for ab03ap03Name, ab03ap03Value in ab03ap03Selectors.items()
                              if ab03ap03Name != ab03ap03Key})
            if ab03ap03Kind == 'absent':
                self.assertNotIn(ab03ap03Key, ab03ap03Input['context'])
            else:
                self.assertNotEqual(ab03ap03Input['context'][ab03ap03Key], ab03ap03Selectors[ab03ap03Key])
                if ab03ap03Kind == 'null':
                    self.assertIsNone(ab03ap03Input['context'][ab03ap03Key])
                elif ab03ap03Kind == 'zero':
                    self.assertIs(type(ab03ap03Input['context'][ab03ap03Key]), int)
                    self.assertEqual(ab03ap03Input['context'][ab03ap03Key], 0)
            self.assertEqual(json.dumps(ab03ap03Input), json.dumps(json.loads(json.dumps(ab03ap03Input))))
            # Unsupported selectors need no view arguments.
            ab03ap03Changed = copy.deepcopy(ab03ap03Input)
            del ab03ap03Changed['arguments']
            self.ab03ap03Validate(ab03ap03Changed)

    def test_ab03ap03_opaque_axes_fields_arguments_and_json_copy(self):
        ab03ap03Original = self.ab03ap03Cases['ordinary']['input']
        for ab03ap03Container, ab03ap03Keys in [('context', ('family', 'variant', 'opaque')),
                                               ('arguments', ('opaque',)), ('fields', ('independent',))]:
            for ab03ap03Key in ab03ap03Keys:
                for ab03ap03Value in ([[], [0], [255]] if ab03ap03Container == 'fields' else
                                     [None, False, 0, '', [], {'nested': [0, False, None]}]):
                    ab03ap03Changed = copy.deepcopy(ab03ap03Original)
                    ab03ap03Changed[ab03ap03Container][ab03ap03Key] = ab03ap03Value
                    self.ab03ap03Validate(ab03ap03Changed)
                    ab03ap03RoundTrip = json.loads(json.dumps(ab03ap03Changed))
                    self.assertEqual(ab03ap03RoundTrip, ab03ap03Changed)
                    self.assertEqual(ab03ap03Transition(ab03ap03Changed['arguments']['rows'], 1, [2]), ab03ap03Expected['ordinary'])
                    del ab03ap03Changed[ab03ap03Container][ab03ap03Key]
                    self.assertIn(ab03ap03Key, ab03ap03RoundTrip[ab03ap03Container])
                    self.assertIn(ab03ap03Key, ab03ap03Original[ab03ap03Container])
        # Synthetic JSON ownership controls: these do not test production allocations.
        ab03ap03First = json.loads(json.dumps(ab03ap03Original))
        ab03ap03Second = json.loads(json.dumps(ab03ap03Original))
        ab03ap03First['arguments']['rows'][0]['token'] = 255
        ab03ap03First['context']['opaque']['values'].append(255)
        ab03ap03First['fields']['gate'][0] = 0
        self.assertEqual(ab03ap03Second, ab03ap03Original)
        self.assertEqual(ab03ap03Second['arguments']['rows'][0]['token'], 3)
        self.assertEqual(ab03ap03Second['fields']['gate'], [2])

    def test_ab03ap03_invalid_corpus_rejected_by_shape_assertions(self):
        ab03ap03Invalid = self.ab03ap03Fixture['invalid']
        self.assertEqual(len(ab03ap03Invalid), 85)
        self.assertEqual(len({ab03ap03Case['id'] for ab03ap03Case in ab03ap03Invalid}), len(ab03ap03Invalid))
        # A valid control must survive these same shape assertions first.
        self.ab03ap03Validate(self.ab03ap03Cases['ordinary']['input'])
        for ab03ap03Case in ab03ap03Invalid:
            with self.subTest(case=ab03ap03Case['id']):
                with self.assertRaises((AssertionError, ValueError, KeyError)):
                    self.ab03ap03Validate(ab03ap03Decode(ab03ap03Case['json']))


if __name__ == '__main__':
    unittest.main()
