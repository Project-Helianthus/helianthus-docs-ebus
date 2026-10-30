"""Document conformance only; no production API evaluator is implemented here."""
import copy
import json
from pathlib import Path
import re
import unittest


ab01ap01Root = Path(__file__).resolve().parents[1]
ab01ap01Page = ab01ap01Root / 'architecture/ap02_b531_capability_state.md'
ab01ap01Fixture = ab01ap01Root / 'architecture/fixtures/ap02_b531_capability_state.json'
ab01ap01Contract = {
    'signature': 'Ab01Ap01Evaluate(ab01ap01Input json.RawMessage) (json.RawMessage, error)',
    'package': 'vaillant',
    'selectors': dict(primary=181, secondary=49, operation=1, direction='local'),
    'views': {'capability': dict(registered='u32', prior='u32', result='u32'),
              'select': {'rows': {'length': 9, 'element': dict(a='u32', b='u32', c='u32')}}},
    'limits': dict(u8=255, u16=65535, u32=4294967295),
    'output_keys': ['context', 'raw', 'state', 'fields', 'physical', 'qualified'],
    'optional_output_keys': ['arguments'],
    'field_groups': ['raw_fields', 'derived'],
    'physical': 'Unknown', 'qualified': False, 'grade': 'Hypothesis',
    'calculation': 'Proven', 'unsupported_state': 'Unknown',
    'incomplete_state': 'partial', 'ordinary_state': 'complete',
    'marker': 65535, 'no_match': 9,
}


class TestAb01Ap01CapabilityState(unittest.TestCase):
    def setUp(self):
        self.ab01ap01Data = json.loads(ab01ap01Fixture.read_text())
        self.ab01ap01Cases = {ab01ap01Case['id']: ab01ap01Case
                             for ab01ap01Case in self.ab01ap01Data['cases']}
        self.ab01ap01Text = ab01ap01Page.read_text()

    def ab01ap01JsonEqual(self, ab01ap01Left, ab01ap01Right):
        self.assertEqual(json.dumps(ab01ap01Left, sort_keys=True),
                         json.dumps(ab01ap01Right, sort_keys=True))

    def ab01ap01Pairs(self, ab01ap01Pairs):
        ab01ap01Object = {}
        for ab01ap01Key, ab01ap01Value in ab01ap01Pairs:
            self.assertNotIn(ab01ap01Key, ab01ap01Object, 'duplicate key')
            ab01ap01Object[ab01ap01Key] = ab01ap01Value
        return ab01ap01Object

    def ab01ap01Uint(self, ab01ap01Value, ab01ap01Maximum):
        self.assertIs(type(ab01ap01Value), int)
        self.assertGreaterEqual(ab01ap01Value, 0)
        self.assertLessEqual(ab01ap01Value, ab01ap01Maximum)

    def ab01ap01CheckInput(self, ab01ap01Text):
        # This is a test assertion over synthetic input, not the proposed API.
        ab01ap01Input = json.loads(ab01ap01Text, object_pairs_hook=self.ab01ap01Pairs,
                                  parse_constant=lambda ab01ap01Value: self.fail('non-JSON number'))
        self.assertIs(type(ab01ap01Input), dict)
        for ab01ap01Key in ('context', 'fields'):
            self.assertIs(type(ab01ap01Input[ab01ap01Key]), dict)
        for ab01ap01Value in ab01ap01Input['fields'].values():
            self.assertIs(type(ab01ap01Value), list)
            for ab01ap01Byte in ab01ap01Value:
                self.ab01ap01Uint(ab01ap01Byte, 255)
        ab01ap01Context = ab01ap01Input['context']
        for ab01ap01Key in ('primary', 'secondary', 'operation'):
            if ab01ap01Context.get(ab01ap01Key) is not None:
                self.ab01ap01Uint(ab01ap01Context[ab01ap01Key], 255)
        for ab01ap01Key in ('direction', 'view'):
            if ab01ap01Context.get(ab01ap01Key) is not None:
                self.assertIs(type(ab01ap01Context[ab01ap01Key]), str)
        if 'arguments' in ab01ap01Input:
            self.assertIs(type(ab01ap01Input['arguments']), dict)
        ab01ap01Supported = all(ab01ap01Context.get(ab01ap01Key) == ab01ap01Value
                               for ab01ap01Key, ab01ap01Value in ab01ap01Contract['selectors'].items())
        if not ab01ap01Supported or ab01ap01Context.get('view') not in ('capability', 'select'):
            return ab01ap01Input
        ab01ap01Arguments = ab01ap01Input['arguments']
        if ab01ap01Context['view'] == 'capability':
            for ab01ap01Key in ('registered', 'prior', 'result'):
                self.ab01ap01Uint(ab01ap01Arguments[ab01ap01Key], 4294967295)
        else:
            self.assertIs(type(ab01ap01Arguments['rows']), list)
            self.assertEqual(len(ab01ap01Arguments['rows']), 9)
            for ab01ap01Row in ab01ap01Arguments['rows']:
                self.assertIs(type(ab01ap01Row), dict)
                for ab01ap01Key in ('a', 'b', 'c'):
                    self.ab01ap01Uint(ab01ap01Row[ab01ap01Key], 4294967295)
        return ab01ap01Input

    def test_ab01ap01_fixture_inputs_are_fixed_independently(self):
        ab01ap01Context = dict(primary=181, secondary=49, operation=1, direction='local',
                               view='capability', family='synthetic-heat-pump-family',
                               variant={'ab01ap01Tag': ['synthetic']})
        ab01ap01Raw = {'ab01ap01Left': [0,255], 'ab01ap01Right': []}
        ab01ap01Expected = {}
        def ab01ap01Add(ab01ap01Id, ab01ap01Arguments, ab01ap01C=None, ab01ap01F=None):
            ab01ap01Value = dict(context=copy.deepcopy(ab01ap01Context if ab01ap01C is None else ab01ap01C),
                                 fields=copy.deepcopy(ab01ap01Raw if ab01ap01F is None else ab01ap01F))
            if ab01ap01Arguments is not None:
                ab01ap01Value['arguments'] = ab01ap01Arguments
            ab01ap01Expected['ab01ap01'+ab01ap01Id] = ab01ap01Value
        for ab01ap01Id, ab01ap01Tuple in {
            'RetainTwo':(2,2,1), 'Admit':(1,0,1), 'Clear':(2,2,0), 'Skip':(0,2,1),
            'Unknown':(2,2,2), 'Maximum':(4294967295,4294967295,1),
            'UnknownMaximum':(1,2,4294967295), 'Zero':(0,0,0), 'Odd':(1,3,1)}.items():
            ab01ap01Add(ab01ap01Id, dict(zip(('registered','prior','result'), ab01ap01Tuple)))
        for ab01ap01Id, ab01ap01Indices in {'First':{0,8},'Last':{8},'Middle':{3,8},'Miss':set()}.items():
            ab01ap01Rows = [dict(a=2 if ab01ap01I in ab01ap01Indices else 0,b=2,c=2) for ab01ap01I in range(9)]
            ab01ap01Add(ab01ap01Id, dict(rows=ab01ap01Rows), dict(ab01ap01Context,view='select'))
        for ab01ap01Key in ('a','b','c'):
            ab01ap01Rows = [dict(a=2,b=2,c=2) for ab01ap01I in range(9)]
            for ab01ap01Row in ab01ap01Rows:
                ab01ap01Row[ab01ap01Key] = 0
            ab01ap01Add('Zero'+ab01ap01Key, dict(rows=ab01ap01Rows), dict(ab01ap01Context,view='select'))
        for ab01ap01Key, ab01ap01Other in dict(primary=180,secondary=48,operation=0,direction='reply',view='other').items():
            for ab01ap01Suffix in ('Other','Null','Absent'):
                ab01ap01C = copy.deepcopy(ab01ap01Context)
                if ab01ap01Suffix == 'Absent':
                    del ab01ap01C[ab01ap01Key]
                else:
                    ab01ap01C[ab01ap01Key] = ab01ap01Other if ab01ap01Suffix == 'Other' else None
                ab01ap01Add(ab01ap01Key+ab01ap01Suffix, None, ab01ap01C)
        for ab01ap01Key in ('family','variant'):
            for ab01ap01Suffix, ab01ap01Opaque in {'Null':None,'Zero':0,'False':False,'Empty':{},'Other':{'ab01ap01Opaque':[1,False,None]},'Absent':None}.items():
                ab01ap01C = copy.deepcopy(ab01ap01Context)
                if ab01ap01Suffix == 'Absent':
                    del ab01ap01C[ab01ap01Key]
                else:
                    ab01ap01C[ab01ap01Key] = ab01ap01Opaque
                ab01ap01Add(ab01ap01Key+ab01ap01Suffix,dict(registered=2,prior=2,result=1,ab01ap01Extra={'ab01ap01Nested':[False,None,0]}),ab01ap01C)
        for ab01ap01Key in ('ab01ap01Left','ab01ap01Right'):
            for ab01ap01Suffix, ab01ap01Bytes in {'Empty':[],'Zero':[0],'Short':[1],'Long':[1,2,3],'Absent':None}.items():
                ab01ap01F = copy.deepcopy(ab01ap01Raw)
                if ab01ap01Suffix == 'Absent':
                    del ab01ap01F[ab01ap01Key]
                else:
                    ab01ap01F[ab01ap01Key] = ab01ap01Bytes
                ab01ap01Add(ab01ap01Key+ab01ap01Suffix,dict(registered=2,prior=2,result=1),ab01ap01F=ab01ap01F)
        self.ab01ap01JsonEqual({ab01ap01K:ab01ap01V['input'] for ab01ap01K,ab01ap01V in self.ab01ap01Cases.items()},ab01ap01Expected)

    def test_ab01ap01_page_tables(self):
        ab01ap01Block = re.search(r'<!-- ab01ap01-contract -->\s*```json\s*(.*?)\s*```',
                                  self.ab01ap01Text, re.S)
        self.assertIsNotNone(ab01ap01Block)
        self.ab01ap01JsonEqual(json.loads(ab01ap01Block[1]), ab01ap01Contract)
        ab01ap01Rows = [ab01ap01Line for ab01ap01Line in self.ab01ap01Text.splitlines()
                        if ab01ap01Line.startswith('|')]
        self.assertEqual(ab01ap01Rows, [
            '| registered condition | result condition | prior condition | updated | outcome |',
            '|---|---|---|---|---|',
            '| zero | any | any | prior | skipped |',
            '| nonzero | 0 | any | 0 | cleared |',
            '| nonzero | 1 | zero | 1 | admitted |',
            '| nonzero | 1 | nonzero | prior | retained |',
            '| nonzero | other | any | prior | Unknown |',
            '| row predicate | choice | no match |', '|---|---|---|',
            '| a != 0 and b != 0 and c != 0 | first matching local index, 0 through 8 | 9 |'])

    def test_ab01ap01_scenario_shapes_and_formulas(self):
        self.assertIs(self.ab01ap01Data['synthetic'], True)
        self.assertEqual(len(self.ab01ap01Cases), len(self.ab01ap01Data['cases']))
        self.assertGreater(len(self.ab01ap01Cases), 40)
        for ab01ap01Id, ab01ap01Case in self.ab01ap01Cases.items():
            with self.subTest(ab01ap01Id=ab01ap01Id):
                self.assertTrue(ab01ap01Id.startswith('ab01ap01'))
                ab01ap01Input = self.ab01ap01CheckInput(json.dumps(ab01ap01Case['input']))
                ab01ap01Output = ab01ap01Case['expected']
                self.assertEqual(set(ab01ap01Output), set(ab01ap01Contract['output_keys']) |
                                 ({'arguments'} if 'arguments' in ab01ap01Input else set()))
                self.ab01ap01JsonEqual(ab01ap01Output['context'], ab01ap01Input['context'])
                self.ab01ap01JsonEqual(ab01ap01Output['raw'], ab01ap01Input['fields'])
                if 'arguments' in ab01ap01Input:
                    self.ab01ap01JsonEqual(ab01ap01Output['arguments'], ab01ap01Input['arguments'])
                self.assertEqual(ab01ap01Output['physical'], 'Unknown')
                self.assertIs(ab01ap01Output['qualified'], False)
                self.assertEqual(set(ab01ap01Output['fields']), {'raw_fields', 'derived'})
                self.assertEqual(ab01ap01Output['fields']['raw_fields'], {
                    ab01ap01Key: dict(raw=ab01ap01Value, state='Unknown')
                    for ab01ap01Key, ab01ap01Value in ab01ap01Input['fields'].items()})
                ab01ap01C = ab01ap01Input['context']
                ab01ap01D = ab01ap01Output['fields']['derived']
                ab01ap01Supported = all(ab01ap01C.get(ab01ap01K) == ab01ap01V
                                        for ab01ap01K, ab01ap01V in ab01ap01Contract['selectors'].items())
                if not ab01ap01Supported or ab01ap01C.get('view') not in ('capability', 'select'):
                    self.assertEqual(ab01ap01Output['state'], 'Unknown')
                    self.assertEqual(ab01ap01D, {})
                    continue
                self.assertEqual(ab01ap01Output['state'], 'complete')
                ab01ap01A = ab01ap01Input['arguments']
                if ab01ap01C['view'] == 'select':
                    ab01ap01Matches = [ab01ap01I for ab01ap01I in range(9)
                                       if 0 not in [ab01ap01A['rows'][ab01ap01I][ab01ap01K]
                                                    for ab01ap01K in ('a', 'b', 'c')]]
                    self.assertEqual(set(ab01ap01D), {'index'})
                    self.assertEqual(ab01ap01D['index']['number'], min(ab01ap01Matches + [9]))
                    self.assertEqual(ab01ap01D['index']['raw'], ab01ap01A['rows'])
                else:
                    ab01ap01P, ab01ap01R, ab01ap01S = (ab01ap01A[ab01ap01K]
                                                       for ab01ap01K in ('prior', 'registered', 'result'))
                    # Bounded truth table; distinct from fixture construction.
                    ab01ap01Transitions = {
                        (False, 0): (ab01ap01P, 'skipped'),
                        (False, 1): (ab01ap01P, 'skipped'),
                        (False, 2): (ab01ap01P, 'skipped'),
                        (True, 0): (0, 'cleared'),
                        (True, 1): (max(ab01ap01P, 1), 'retained' if ab01ap01P else 'admitted'),
                        (True, 2): (ab01ap01P, 'Unknown')}
                    ab01ap01U, ab01ap01O = ab01ap01Transitions[(ab01ap01R > 0, min(ab01ap01S, 2))]
                    self.assertEqual(set(ab01ap01D), {'marker','updated','cached_bit0','whole_nonzero'})
                    self.assertEqual(ab01ap01D['marker']['number'], 65535)
                    self.assertEqual(ab01ap01D['marker']['raw'], [])
                    self.assertEqual(ab01ap01D['updated']['number'], ab01ap01U)
                    self.assertEqual(ab01ap01D['updated']['outcome'], ab01ap01O)
                    self.assertEqual(ab01ap01D['cached_bit0']['flags'], {'cached_bit0': ab01ap01U % 2 == 1})
                    self.assertEqual(ab01ap01D['whole_nonzero']['flags'], {'whole_nonzero': ab01ap01U > 0})
                    for ab01ap01Key in ('updated','cached_bit0','whole_nonzero'):
                        self.assertEqual(ab01ap01D[ab01ap01Key]['raw'], {
                            ab01ap01K: ab01ap01A[ab01ap01K] for ab01ap01K in ('registered','prior','result')})
                for ab01ap01Key, ab01ap01Record in ab01ap01D.items():
                    ab01ap01RecordKeys = {'raw','state','grade','calculation'}
                    if ab01ap01Key in ('cached_bit0','whole_nonzero'):
                        ab01ap01RecordKeys.add('flags')
                        self.assertIs(type(ab01ap01Record['flags'][ab01ap01Key]), bool)
                    else:
                        ab01ap01RecordKeys.add('number')
                        self.ab01ap01Uint(ab01ap01Record['number'], 4294967295)
                    if ab01ap01Key == 'updated':
                        ab01ap01RecordKeys.add('outcome')
                    self.assertEqual(set(ab01ap01Record), ab01ap01RecordKeys)
                    self.assertEqual(ab01ap01Record['state'], 'complete')
                    self.assertEqual(ab01ap01Record['grade'], 'Hypothesis')
                    self.assertEqual(ab01ap01Record['calculation'], 'Proven')

    def test_ab01ap01_independent_controls(self):
        # Literal controls kill truthy canonicalization, admission bit0, marker suppression.
        for ab01ap01Id, ab01ap01Expected in {
            'RetainTwo': (2, False, True, 65535, 'retained'),
            'Admit': (1, True, True, 65535, 'admitted'),
            'Clear': (0, False, False, 65535, 'cleared'),
            'Skip': (2, False, True, 65535, 'skipped'),
            'Unknown': (2, False, True, 65535, 'Unknown')}.items():
            ab01ap01D = self.ab01ap01Cases['ab01ap01'+ab01ap01Id]['expected']['fields']['derived']
            self.assertIn('marker', ab01ap01D)
            self.assertEqual((ab01ap01D['updated']['number'], ab01ap01D['cached_bit0']['flags']['cached_bit0'],
                              ab01ap01D['whole_nonzero']['flags']['whole_nonzero'],
                              ab01ap01D['marker']['number'], ab01ap01D['updated']['outcome']), ab01ap01Expected)
        for ab01ap01Id, ab01ap01Index in {'First':0,'Last':8,'Middle':3,'Miss':9,'Zeroa':9,'Zerob':9,'Zeroc':9}.items():
            self.assertEqual(self.ab01ap01Cases['ab01ap01'+ab01ap01Id]['expected']['fields']['derived']['index']['number'], ab01ap01Index)

    def test_ab01ap01_invalid_json_and_all_typed_members(self):
        for ab01ap01Text in self.ab01ap01Data['invalid_json']:
            with self.subTest(ab01ap01Text=ab01ap01Text):
                with self.assertRaises((AssertionError, ValueError, KeyError)):
                    self.ab01ap01CheckInput(ab01ap01Text)
        ab01ap01Control = self.ab01ap01Cases['ab01ap01RetainTwo']['input']
        self.ab01ap01CheckInput(json.dumps(ab01ap01Control))
        for ab01ap01Key in ('registered','prior','result'):
            for ab01ap01Bad in (None, False, True, [], {}, '', '1', 1.5, -1, 4294967296):
                ab01ap01Copy = copy.deepcopy(ab01ap01Control)
                ab01ap01Copy['arguments'][ab01ap01Key] = ab01ap01Bad
                with self.subTest(ab01ap01Key=ab01ap01Key, ab01ap01Bad=ab01ap01Bad):
                    with self.assertRaises(AssertionError):
                        self.ab01ap01CheckInput(json.dumps(ab01ap01Copy))
            ab01ap01Copy = copy.deepcopy(ab01ap01Control)
            del ab01ap01Copy['arguments'][ab01ap01Key]
            with self.assertRaises(KeyError):
                self.ab01ap01CheckInput(json.dumps(ab01ap01Copy))
            for ab01ap01Good in (0, 1, 2, 4294967295):
                ab01ap01Copy['arguments'][ab01ap01Key] = ab01ap01Good
                self.ab01ap01CheckInput(json.dumps(ab01ap01Copy))
        for ab01ap01Key in ('ab01ap01Left','ab01ap01Right'):
            for ab01ap01Bad in (False, None, {}, [False], [-1], [256], [1.5], ['0']):
                ab01ap01Copy = copy.deepcopy(ab01ap01Control)
                ab01ap01Copy['fields'][ab01ap01Key] = ab01ap01Bad
                with self.assertRaises(AssertionError):
                    self.ab01ap01CheckInput(json.dumps(ab01ap01Copy))
        ab01ap01Select = self.ab01ap01Cases['ab01ap01First']['input']
        for ab01ap01Length in (8,10):
            ab01ap01Copy = copy.deepcopy(ab01ap01Select)
            ab01ap01Copy['arguments']['rows'] = [dict(a=2,b=2,c=2) for ab01ap01I in range(ab01ap01Length)]
            with self.assertRaises(AssertionError):
                self.ab01ap01CheckInput(json.dumps(ab01ap01Copy))
        for ab01ap01I in range(9):
            for ab01ap01Key in ('a','b','c'):
                for ab01ap01Bad in (False,None,[],{},'2',1.5,-1,4294967296):
                    ab01ap01Copy = copy.deepcopy(ab01ap01Select)
                    ab01ap01Copy['arguments']['rows'][ab01ap01I][ab01ap01Key] = ab01ap01Bad
                    with self.assertRaises(AssertionError):
                        self.ab01ap01CheckInput(json.dumps(ab01ap01Copy))
                ab01ap01Copy = copy.deepcopy(ab01ap01Select)
                del ab01ap01Copy['arguments']['rows'][ab01ap01I][ab01ap01Key]
                with self.assertRaises(KeyError):
                    self.ab01ap01CheckInput(json.dumps(ab01ap01Copy))

    def test_ab01ap01_structure_kinds_and_selector_ranges(self):
        ab01ap01Control = self.ab01ap01Cases['ab01ap01RetainTwo']['input']
        for ab01ap01Key in ('context','fields','arguments'):
            for ab01ap01Bad in (False,None,[],0,''):
                ab01ap01Copy = copy.deepcopy(ab01ap01Control)
                ab01ap01Copy[ab01ap01Key] = ab01ap01Bad
                with self.assertRaises(AssertionError):
                    self.ab01ap01CheckInput(json.dumps(ab01ap01Copy))
            ab01ap01Copy = copy.deepcopy(ab01ap01Control)
            del ab01ap01Copy[ab01ap01Key]
            with self.assertRaises(KeyError):
                self.ab01ap01CheckInput(json.dumps(ab01ap01Copy))
        for ab01ap01Key in ('primary','secondary','operation','direction','view'):
            ab01ap01BadValues = (False,[],{})
            ab01ap01BadValues += (-1,256,1.5,'181') if ab01ap01Key in ('primary','secondary','operation') else (0,1.5)
            for ab01ap01Bad in ab01ap01BadValues:
                ab01ap01Copy = copy.deepcopy(ab01ap01Control)
                ab01ap01Copy['context'][ab01ap01Key] = ab01ap01Bad
                with self.assertRaises(AssertionError):
                    self.ab01ap01CheckInput(json.dumps(ab01ap01Copy))
        ab01ap01Control = self.ab01ap01Cases['ab01ap01First']['input']
        for ab01ap01Bad in (None,False,{},0,''):
            ab01ap01Copy = copy.deepcopy(ab01ap01Control)
            ab01ap01Copy['arguments']['rows'] = ab01ap01Bad
            with self.assertRaises(AssertionError):
                self.ab01ap01CheckInput(json.dumps(ab01ap01Copy))
        for ab01ap01I in range(9):
            for ab01ap01Key in ('a','b','c'):
                for ab01ap01Good in (0,1,2,4294967295):
                    ab01ap01Copy = copy.deepcopy(ab01ap01Control)
                    ab01ap01Copy['arguments']['rows'][ab01ap01I][ab01ap01Key] = ab01ap01Good
                    self.ab01ap01CheckInput(json.dumps(ab01ap01Copy))
            for ab01ap01Bad in (None,False,[],0,''):
                ab01ap01Copy = copy.deepcopy(ab01ap01Control)
                ab01ap01Copy['arguments']['rows'][ab01ap01I] = ab01ap01Bad
                with self.assertRaises(AssertionError):
                    self.ab01ap01CheckInput(json.dumps(ab01ap01Copy))

    def test_ab01ap01_context_raw_and_json_copy_boundaries(self):
        for ab01ap01Key in ('primary','secondary','operation','direction','view'):
            for ab01ap01Suffix in ('Other','Null','Absent'):
                self.assertEqual(self.ab01ap01Cases['ab01ap01'+ab01ap01Key+ab01ap01Suffix]['expected']['state'], 'Unknown')
        for ab01ap01Key in ('family','variant'):
            for ab01ap01Suffix in ('Null','Zero','False','Empty','Other','Absent'):
                self.assertIs(self.ab01ap01Cases['ab01ap01'+ab01ap01Key+ab01ap01Suffix]['expected']['qualified'], False)
        for ab01ap01Case in self.ab01ap01Cases.values():
            ab01ap01First = json.loads(json.dumps(ab01ap01Case['expected']))
            ab01ap01Second = json.loads(json.dumps(ab01ap01Case['expected']))
            self.assertEqual(ab01ap01First, ab01ap01Case['expected'])
            ab01ap01Input = copy.deepcopy(ab01ap01Case['input'])
            ab01ap01Input['context']['variant'] = ['mutated']
            ab01ap01Input['fields']['ab01ap01Left'] = [99]
            ab01ap01First['context']['variant'] = ['different']
            ab01ap01First['raw']['ab01ap01Right'] = [88]
            ab01ap01First['fields']['derived'].clear()
            if 'arguments' in ab01ap01First:
                ab01ap01First['arguments']['ab01ap01Extra'] = {'changed': True}
            self.assertEqual(ab01ap01Second, ab01ap01Case['expected'])
            self.assertNotEqual(ab01ap01First, ab01ap01Second)


if __name__ == '__main__':
    unittest.main()
