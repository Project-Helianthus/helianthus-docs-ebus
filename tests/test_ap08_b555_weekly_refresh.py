"""Synthetic documentation checks; bounded oracles, never a runtime API substitute."""
import copy as ab07ap07Copy
import json as ab07ap07Json
import os as ab07ap07Os
from pathlib import Path as Ab07Ap07Path
import re as ab07ap07Re
import unittest as ab07ap07Unittest

ab07ap07Root = Ab07Ap07Path(ab07ap07Os.environ.get(
    'AB07AP07_ROOT', str(Ab07Ap07Path(__file__).resolve().parents[1])))


def ab07ap07Tables(ab07ap07Text):
    ab07ap07Result = []
    for ab07ap07Block in ab07ap07Text.split('\n\n'):
        ab07ap07Lines = ab07ap07Block.splitlines()
        if ab07ap07Lines and all(ab07ap07Line.startswith('|') for ab07ap07Line in ab07ap07Lines):
            ab07ap07Result.append([
                [ab07ap07Cell.strip() for ab07ap07Cell in ab07ap07Line.strip('|').split('|')]
                for ab07ap07Line in ab07ap07Lines])
    return ab07ap07Result


def ab07ap07Pairs(ab07ap07PairsInput):
    ab07ap07Result = {}
    for ab07ap07Key, ab07ap07Value in ab07ap07PairsInput:
        if ab07ap07Key in ab07ap07Result:
            raise ValueError('duplicate key')
        ab07ap07Result[ab07ap07Key] = ab07ap07Value
    return ab07ap07Result


def ab07ap07Integer(ab07ap07Value, ab07ap07Maximum):
    if type(ab07ap07Value) is not int or not 0 <= ab07ap07Value <= ab07ap07Maximum:
        raise ValueError('typed integer')


def ab07ap07Bytes(ab07ap07Value):
    if type(ab07ap07Value) is not list:
        raise ValueError('byte array')
    for ab07ap07Byte in ab07ap07Value:
        ab07ap07Integer(ab07ap07Byte, 255)


def ab07ap07Admit(ab07ap07Text):
    """Test-only admission oracle: validate specimens, produce no API result."""
    ab07ap07Input = ab07ap07Json.loads(ab07ap07Text, object_pairs_hook=ab07ap07Pairs,
                                      parse_constant=lambda ab07ap07Token: (_ for _ in ()).throw(ValueError('nonfinite')))
    if type(ab07ap07Input) is not dict:
        raise ValueError('object')
    for ab07ap07Key in ('context', 'fields'):
        if type(ab07ap07Input.get(ab07ap07Key)) is not dict:
            raise ValueError('required object')
    for ab07ap07Value in ab07ap07Input['fields'].values():
        ab07ap07Bytes(ab07ap07Value)
    if 'arguments' in ab07ap07Input and type(ab07ap07Input['arguments']) is not dict:
        raise ValueError('arguments object')
    ab07ap07Context = ab07ap07Input['context']
    ab07ap07Identity = tuple(ab07ap07Context.get(ab07ap07Key) for ab07ap07Key in
                             ('primary', 'secondary', 'operation', 'direction', 'view'))
    if ab07ap07Identity not in ((181, 85, 164, 'local', 'weekly'),
                                (181, 85, 166, 'local', 'nonheating-shape')):
        return False
    ab07ap07Arguments = ab07ap07Input.get('arguments', {})
    try:
        if ab07ap07Identity[2] == 164:
            if type(ab07ap07Arguments['status_ok']) is not bool:
                raise ValueError('status Boolean')
            ab07ap07Integer(ab07ap07Arguments['slot_limit'], 255)
            ab07ap07Days = ab07ap07Arguments['days']
            if type(ab07ap07Days) is not list or len(ab07ap07Days) != 7:
                raise ValueError('seven days')
            for ab07ap07Day in ab07ap07Days:
                if type(ab07ap07Day) is not dict:
                    raise ValueError('day object')
                ab07ap07Integer(ab07ap07Day['count'], 255)
                if type(ab07ap07Day['slots']) is not list:
                    raise ValueError('slots array')
                for ab07ap07Slot in ab07ap07Day['slots']:
                    if type(ab07ap07Slot) is not dict or type(ab07ap07Slot['ok']) is not bool:
                        raise ValueError('slot Boolean')
                    ab07ap07Bytes(ab07ap07Slot['raw'])
        else:
            ab07ap07Initial = ab07ap07Arguments['initial']
            if type(ab07ap07Initial) is not list or len(ab07ap07Initial) != 5 or any(
                    type(ab07ap07Value) in (list, dict) for ab07ap07Value in ab07ap07Initial):
                raise ValueError('five scalars')
            ab07ap07Integer(ab07ap07Arguments['count'], 255)
            ab07ap07Values = ab07ap07Arguments['slot_setpoints']
            if type(ab07ap07Values) is not list or len(ab07ap07Values) < ab07ap07Arguments['count']:
                raise ValueError('setpoint count')
            for ab07ap07Value in ab07ap07Values:
                ab07ap07Integer(ab07ap07Value, 65535)
    except (KeyError, TypeError) as ab07ap07Error:
        raise ValueError('required typed argument') from ab07ap07Error
    return True


def ab07ap07Weekly(ab07ap07Arguments):
    """Bounded prefix oracle, independent of any production implementation."""
    ab07ap07Success = []
    ab07ap07Attempts = []
    ab07ap07Completed = []
    ab07ap07Reason = None
    if not ab07ap07Arguments['status_ok']:
        ab07ap07Reason = 'status-failure'
    else:
        for ab07ap07Index, ab07ap07Day in enumerate(ab07ap07Arguments['days']):
            if ab07ap07Day['count'] > ab07ap07Arguments['slot_limit']:
                ab07ap07Reason = 'count-overflow'
                break
            for ab07ap07SlotIndex in range(ab07ap07Day['count']):
                if ab07ap07SlotIndex >= len(ab07ap07Day['slots']):
                    ab07ap07Reason = 'missing-slot'
                    break
                ab07ap07Attempts.append((ab07ap07Index, ab07ap07SlotIndex))
                if not ab07ap07Day['slots'][ab07ap07SlotIndex]['ok']:
                    ab07ap07Reason = 'slot-failure'
                    break
                ab07ap07Success.append(ab07ap07Copy.deepcopy(ab07ap07Day['slots'][ab07ap07SlotIndex]))
            if ab07ap07Reason:
                break
            ab07ap07Completed.append(ab07ap07Index)
    return {'reason': ab07ap07Reason, 'attempts': len(ab07ap07Attempts),
            'completed_days': len(ab07ap07Completed), 'successful_slots': len(ab07ap07Success),
            'complete': len(ab07ap07Completed) == 7}


class Ab07Ap07Contract(ab07ap07Unittest.TestCase):
    def setUp(self):
        self.ab07ap07Page = (ab07ap07Root / 'architecture/ap08-b555-weekly-refresh.md').read_text()
        self.ab07ap07Fixture = ab07ap07Json.loads((ab07ap07Root /
            'architecture/fixtures/ap08_b555_weekly_refresh.json').read_text(), object_pairs_hook=ab07ap07Pairs)
        self.ab07ap07Cases = {ab07ap07Case['id']: ab07ap07Case
                             for ab07ap07Case in self.ab07ap07Fixture['scenarios']}

    def TestAb07Ap07PageTables(self):
        self.assertEqual(ab07ap07Re.findall(r'```go\n(.*?)\n```', self.ab07ap07Page, ab07ap07Re.S),
                         ['func Ab07Ap07Evaluate(ab07ap07Input json.RawMessage) (json.RawMessage, error)'])
        ab07ap07TablesValue = ab07ap07Tables(self.ab07ap07Page)
        self.assertEqual(len(ab07ap07TablesValue), 4)
        self.assertEqual(ab07ap07TablesValue[0][0], ['primary','secondary','operation','direction','view','arguments'])
        self.assertEqual(ab07ap07TablesValue[0][2:], [
            ['181','85','164','local','weekly','status_ok, slot_limit, days'],
            ['181','85','166','local','nonheating-shape','initial, count, slot_setpoints']])
        self.assertEqual(ab07ap07TablesValue[1][2:], [
            ['status_ok','Boolean','false terminates before slot work'],
            ['slot_limit','u8','0..255, local policy'],
            ['days','array','exactly seven ordered entries, positions 0..6'],
            ['days[].count','u8','0..255'], ['days[].slots','array','synthetic slot objects'],
            ['days[].slots[].ok','Boolean','false stops processing'],
            ['days[].slots[].raw','byte array','integers 0..255; no width inferred'],
            ['initial','array','exactly five opaque JSON scalars'], ['count','u8','0..255'],
            ['slot_setpoints','array of u16','integers 0..65535; length at least count']])
        self.assertEqual(ab07ap07TablesValue[2][2:], [
            ['weekly success','complete','complete','true','null'],
            ['status rejected','partial','partial','false','status-failure'],
            ['day count exceeds policy','partial','partial','false','count-overflow'],
            ['attempted slot fails','partial','partial','false','slot-failure'],
            ['required slot absent','partial','partial','false','missing-slot'],
            ['nonheating shape valid','complete','complete','not applicable','not applicable'],
            ['unsupported selector','Unknown','absent','not applicable','not applicable']])
        self.assertEqual(ab07ap07TablesValue[3][2:], [
            ['ab07ap07_status','0','0','0','false','status-failure'],
            ['ab07ap07_zero','0','7','0','true','null'],
            ['ab07ap07_overflow','2','2','2','false','count-overflow'],
            ['ab07ap07_first_failure','1','0','0','false','slot-failure'],
            ['ab07ap07_missing','0','0','0','false','missing-slot'],
            ['ab07ap07_extra','1','7','1','true','null']])
        for ab07ap07Row in ab07ap07TablesValue[3][2:]:
            ab07ap07Expected = self.ab07ap07Cases[ab07ap07Row[0]]['expected']
            self.assertEqual(ab07ap07Row[1:], [str(ab07ap07Expected['attempts']),
                str(ab07ap07Expected['completed_days']),str(ab07ap07Expected['successful_slots']),
                str(ab07ap07Expected['complete']).lower(),
                'null' if ab07ap07Expected['reason'] is None else ab07ap07Expected['reason']])

    def TestAb07Ap07OutputDeclaration(self):
        ab07ap07Declarations = ab07ap07Re.findall(r'```json\n(.*?)\n```', self.ab07ap07Page, ab07ap07Re.S)
        self.assertEqual(len(ab07ap07Declarations), 1)
        self.assertEqual(ab07ap07Json.loads(ab07ap07Declarations[0], object_pairs_hook=ab07ap07Pairs), {
            'signature':'Ab07Ap07Evaluate(ab07ap07Input json.RawMessage) (json.RawMessage, error)',
            'output_required':['context','raw','state','fields','physical','qualified'],
            'output_optional':['arguments'], 'unmodeled_keys':['raw','state','unmodeled'],
            'view_common_keys':['raw','state','grade','calculation'],
            'weekly_keys':['reason','attempts','completed_days','successful_slots','complete','days'],
            'shape_keys':['initial','processed','unused','processed_slots'],
            'physical':'Unknown','qualified':False,'grade':'Hypothesis','calculation':'Proven',
            'days':7,'replacement':65535,'zero_processed_slots':0,'attempt_on_missing':0,
            'attempt_on_present_failure':1,'status_failure_attempts':0,
            'overflow_policy':'stop-at-reached-day-preserve-prefix',
            'complete_predicate':'all-seven-days-completed','processed_length':'count',
            'unused_slice':'slot_setpoints[count:]','copy_policy':'deep-independent',
            'unsupported_state':'Unknown'})

    def TestAb07Ap07ScenarioTuples(self):
        self.assertEqual({ab07ap07Key: self.ab07ap07Fixture[ab07ap07Key]
                          for ab07ap07Key in ('grade','physical','qualified')},
                         {'grade':'Hypothesis','physical':'Unknown','qualified':False})
        self.assertEqual(len(self.ab07ap07Fixture['scenarios']), 23)
        self.assertEqual(set(self.ab07ap07Cases), {'ab07ap07_shape_0','ab07ap07_shape_1','ab07ap07_shape_2',
            'ab07ap07_status','ab07ap07_zero','ab07ap07_overflow','ab07ap07_first_failure',
            'ab07ap07_missing','ab07ap07_extra'} | {
                'ab07ap07_fail_%d_%d' % (ab07ap07Day, ab07ap07Slot)
                for ab07ap07Day in range(7) for ab07ap07Slot in range(2)})
        for ab07ap07Id, ab07ap07Case in self.ab07ap07Cases.items():
            with self.subTest(ab07ap07Id=ab07ap07Id):
                self.assertTrue(ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Case['input'])))
                ab07ap07Input = ab07ap07Case['input']
                self.assertEqual(ab07ap07Input['context'], {'primary':181,'secondary':85,
                    'operation':166 if 'shape_' in ab07ap07Id else 164,'direction':'local',
                    'view':'nonheating-shape' if 'shape_' in ab07ap07Id else 'weekly',
                    'family':'synthetic family','variant':None,'opaque':{'keep':[False,0,None]}})
                self.assertEqual(ab07ap07Input['fields'], {'opaque_bytes':[0,255],'empty_bytes':[]})
                ab07ap07Args = ab07ap07Input['arguments']
                if 'shape_' in ab07ap07Id:
                    ab07ap07Count = int(ab07ap07Id[-1])
                    self.assertEqual(ab07ap07Args, {'initial':[1,2,3,4,5], 'count':ab07ap07Count,
                                                   'slot_setpoints':[10,20,30]})
                    self.assertEqual(ab07ap07Case['expected'], {'initial':[1,2,3,4,5],
                        'processed':{0:[],1:[65535],2:[65535,65535]}[ab07ap07Count],
                        'unused':{0:[10,20,30],1:[20,30],2:[30]}[ab07ap07Count],
                        'processed_slots':ab07ap07Count})
                else:
                    ab07ap07ExpectedDays = [{'count':0,'slots':[]} for ab07ap07Index in range(7)]
                    ab07ap07ExpectedStatus, ab07ap07ExpectedLimit = True, 2
                    if 'fail_' in ab07ap07Id:
                        ab07ap07FailedDay, ab07ap07FailedSlot = map(int, ab07ap07Id.split('_')[-2:])
                        ab07ap07ExpectedDays = [{'count':2,'slots':[
                            {'ok':True,'raw':[17,0,255]}, {'ok':True,'raw':[17,0,255]}]}
                            for ab07ap07Index in range(7)]
                        ab07ap07ExpectedDays[ab07ap07FailedDay]['slots'][ab07ap07FailedSlot]['ok'] = False
                    elif ab07ap07Id == 'ab07ap07_zero':
                        ab07ap07ExpectedLimit = 0
                    elif ab07ap07Id == 'ab07ap07_overflow':
                        for ab07ap07Index, ab07ap07Count in enumerate((1,1,3)):
                            ab07ap07ExpectedDays[ab07ap07Index] = {'count':ab07ap07Count,'slots':[
                                {'ok':True,'raw':[17,0,255]} for ab07ap07Slot in range(ab07ap07Count)]}
                    else:
                        ab07ap07ExpectedDays[0]['count'] = 1
                        if ab07ap07Id != 'ab07ap07_missing':
                            ab07ap07ExpectedDays[0]['slots'] = [
                                {'ok':ab07ap07Id != 'ab07ap07_first_failure','raw':[17,0,255]}]
                        if ab07ap07Id == 'ab07ap07_status':
                            ab07ap07ExpectedStatus = False
                        if ab07ap07Id == 'ab07ap07_extra':
                            ab07ap07ExpectedDays[0]['slots'].append({'ok':False,'raw':[17,0,255]})
                    self.assertEqual(ab07ap07Args, {'status_ok':ab07ap07ExpectedStatus,
                        'slot_limit':ab07ap07ExpectedLimit,'days':ab07ap07ExpectedDays})
                    self.assertEqual(ab07ap07Weekly(ab07ap07Args), ab07ap07Case['expected'])
                    if 'fail_' in ab07ap07Id:
                        ab07ap07Day, ab07ap07Slot = map(int, ab07ap07Id.split('_')[-2:])
                        self.assertEqual(ab07ap07Case['expected'], {'reason':'slot-failure',
                            'attempts':2*ab07ap07Day+ab07ap07Slot+1,'completed_days':ab07ap07Day,
                            'successful_slots':2*ab07ap07Day+ab07ap07Slot,'complete':False})
                    for ab07ap07Day in ab07ap07Args['days']:
                        for ab07ap07Slot in ab07ap07Day['slots']:
                            self.assertEqual(ab07ap07Slot['raw'], [17,0,255])

    def TestAb07Ap07AdmissionAndIndependentAxes(self):
        ab07ap07Control = self.ab07ap07Cases['ab07ap07_extra']['input']
        for ab07ap07Key in ('primary','secondary','operation','direction','view'):
            for ab07ap07Value in (None, 0, False, '', [], {}):
                ab07ap07Input = ab07ap07Copy.deepcopy(ab07ap07Control)
                ab07ap07Input['context'][ab07ap07Key] = ab07ap07Value
                self.assertFalse(ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Input)))
            ab07ap07Input = ab07ap07Copy.deepcopy(ab07ap07Control)
            del ab07ap07Input['context'][ab07ap07Key]
            self.assertFalse(ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Input)))
        for ab07ap07Key in ('family','variant','opaque'):
            for ab07ap07Value in (None,0,False,'other family',{'nested':[1,None]}):
                ab07ap07Input = ab07ap07Copy.deepcopy(ab07ap07Control)
                ab07ap07Input['context'][ab07ap07Key] = ab07ap07Value
                self.assertTrue(ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Input)))
                self.assertEqual(ab07ap07Json.loads(ab07ap07Json.dumps(ab07ap07Input)), ab07ap07Input)
        for ab07ap07Text in ('{','[]','{"context":{},"context":{},"fields":{}}',
                '{"context":{"opaque":{"a":0,"a":1}},"fields":{}}',
                '{"context":{},"fields":{},"arguments":{"x":1,"x":2}}',
                '{"context":{},"fields":{"x":[],"x":[0]}}',
                '{"context":{},"fields":{},"arguments":{"days":[{"slots":[{"ok":true,"ok":false}]}]}}',
                '{"context":{},"fields":{"x":[NaN]}}'):
            with self.assertRaises(ValueError):
                ab07ap07Admit(ab07ap07Text)
        for ab07ap07CaseId in ('ab07ap07_extra','ab07ap07_shape_1'):
            ab07ap07Base = self.ab07ap07Cases[ab07ap07CaseId]['input']
            for ab07ap07Key in ab07ap07Base['arguments']:
                ab07ap07Input = ab07ap07Copy.deepcopy(ab07ap07Base)
                del ab07ap07Input['arguments'][ab07ap07Key]
                with self.assertRaises(ValueError):
                    ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Input))
                for ab07ap07Value in ((None,{},'wrong',-1,256,1.5) if ab07ap07Key == 'status_ok'
                                         else (None,False,{},'wrong',-1,256,1.5)):
                    ab07ap07Input = ab07ap07Copy.deepcopy(ab07ap07Base)
                    ab07ap07Input['arguments'][ab07ap07Key] = ab07ap07Value
                    with self.assertRaises(ValueError):
                        ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Input))
        for ab07ap07Key in ('opaque_bytes','empty_bytes'):
            for ab07ap07Value in (None,False,0,{},[True],[-1],[256],[1.5]):
                ab07ap07Input = ab07ap07Copy.deepcopy(ab07ap07Control)
                ab07ap07Input['fields'][ab07ap07Key] = ab07ap07Value
                with self.assertRaises(ValueError):
                    ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Input))
            for ab07ap07Value in ([],[0],[255,0,1]):
                ab07ap07Input = ab07ap07Copy.deepcopy(ab07ap07Control)
                ab07ap07Input['fields'][ab07ap07Key] = ab07ap07Value
                self.assertTrue(ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Input)))

    def TestAb07Ap07NestedArgumentKinds(self):
        ab07ap07Base = self.ab07ap07Cases['ab07ap07_extra']['input']
        for ab07ap07Key in ('count','slots'):
            for ab07ap07Value in (None, False, '0', -1, 256, 1.5, {}):
                ab07ap07Input = ab07ap07Copy.deepcopy(ab07ap07Base)
                ab07ap07Input['arguments']['days'][0][ab07ap07Key] = ab07ap07Value
                with self.assertRaises(ValueError):
                    ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Input))
            ab07ap07Input = ab07ap07Copy.deepcopy(ab07ap07Base)
            del ab07ap07Input['arguments']['days'][0][ab07ap07Key]
            with self.assertRaises(ValueError):
                ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Input))
        for ab07ap07Key in ('ok','raw'):
            for ab07ap07Value in (None, 0, 'false', {}, [True], [256]):
                ab07ap07Input = ab07ap07Copy.deepcopy(ab07ap07Base)
                ab07ap07Input['arguments']['days'][0]['slots'][0][ab07ap07Key] = ab07ap07Value
                with self.assertRaises(ValueError):
                    ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Input))
            ab07ap07Input = ab07ap07Copy.deepcopy(ab07ap07Base)
            del ab07ap07Input['arguments']['days'][0]['slots'][0][ab07ap07Key]
            with self.assertRaises(ValueError):
                ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Input))
        for ab07ap07Length in (0,6,8):
            ab07ap07Input = ab07ap07Copy.deepcopy(ab07ap07Base)
            ab07ap07Input['arguments']['days'] = [{'count':0,'slots':[]} for ab07ap07Index in range(ab07ap07Length)]
            with self.assertRaises(ValueError):
                ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Input))
        for ab07ap07BadValue in (False, -1, 65536, 1.5, '1', None):
            ab07ap07Input = ab07ap07Copy.deepcopy(self.ab07ap07Cases['ab07ap07_shape_1']['input'])
            ab07ap07Input['arguments']['slot_setpoints'][0] = ab07ap07BadValue
            with self.assertRaises(ValueError):
                ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Input))
        for ab07ap07Initial in ([], [1,2,3,4], [1,2,3,4,5,6], [1,2,3,4,[]], [1,2,3,4,{}]):
            ab07ap07Input = ab07ap07Copy.deepcopy(self.ab07ap07Cases['ab07ap07_shape_1']['input'])
            ab07ap07Input['arguments']['initial'] = ab07ap07Initial
            with self.assertRaises(ValueError):
                ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Input))
        for ab07ap07Count in (0,255):
            ab07ap07Input = ab07ap07Copy.deepcopy(self.ab07ap07Cases['ab07ap07_shape_1']['input'])
            ab07ap07Input['arguments'].update(initial=[None,False,'opaque',0,1.5],
                count=ab07ap07Count, slot_setpoints=[0,65535]*128)
            ab07ap07Input['arguments']['extra'] = {'nested':[None,0,False]}
            self.assertTrue(ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Input)))
        ab07ap07Input['arguments']['slot_setpoints'] = []
        with self.assertRaises(ValueError):
            ab07ap07Admit(ab07ap07Json.dumps(ab07ap07Input))

    def TestAb07Ap07SerializedEvidenceIndependence(self):
        # Specimen ownership only: this does not test a production return value.
        ab07ap07Original = self.ab07ap07Cases['ab07ap07_extra']['input']
        ab07ap07Snapshot = ab07ap07Json.dumps(ab07ap07Original, sort_keys=True)
        ab07ap07One = ab07ap07Json.loads(ab07ap07Snapshot)
        ab07ap07Two = ab07ap07Json.loads(ab07ap07Snapshot)
        ab07ap07One['context']['opaque']['keep'][0] = True
        ab07ap07One['fields']['opaque_bytes'][0] = 99
        ab07ap07One['arguments']['days'][0]['slots'][0]['raw'][0] = 99
        self.assertEqual(ab07ap07Json.dumps(ab07ap07Two,sort_keys=True), ab07ap07Snapshot)
        self.assertEqual(ab07ap07Json.dumps(ab07ap07Original,sort_keys=True), ab07ap07Snapshot)
        ab07ap07Two['arguments']['days'][0]['slots'][0]['ok'] = False
        self.assertTrue(ab07ap07One['arguments']['days'][0]['slots'][0]['ok'])
        self.assertEqual(ab07ap07Json.dumps(ab07ap07Original,sort_keys=True), ab07ap07Snapshot)
        ab07ap07Distinctions = []
        for ab07ap07Context in ({}, {'family':None}, {'family':0}, {'family':False}):
            ab07ap07Value = {'context':ab07ap07Context, 'fields':{'empty':[]}, 'state':'Unknown'}
            ab07ap07Distinctions.append(ab07ap07Json.dumps(ab07ap07Json.loads(ab07ap07Json.dumps(ab07ap07Value)),sort_keys=True))
        self.assertEqual(len(set(ab07ap07Distinctions)), 4)

    def TestAb07Ap07BoundedTransitions(self):
        for ab07ap07Day in range(7):
            for ab07ap07Slot in range(2):
                ab07ap07Args = ab07ap07Copy.deepcopy(self.ab07ap07Cases[
                    'ab07ap07_fail_%d_%d' % (ab07ap07Day,ab07ap07Slot)]['input']['arguments'])
                ab07ap07Args['days'][ab07ap07Day]['slots'][ab07ap07Slot]['ok'] = True
                self.assertEqual(ab07ap07Weekly(ab07ap07Args), {'reason':None,'attempts':14,
                    'completed_days':7,'successful_slots':14,'complete':True})
        ab07ap07Args = ab07ap07Copy.deepcopy(self.ab07ap07Cases['ab07ap07_overflow']['input']['arguments'])
        for ab07ap07Day in range(7):
            ab07ap07Variant = ab07ap07Copy.deepcopy(ab07ap07Args)
            ab07ap07Variant['days'] = [{'count':1,'slots':[{'ok':True,'raw':[0]}]} for ab07ap07Index in range(7)]
            ab07ap07Variant['days'][ab07ap07Day]['count'] = 3
            self.assertEqual(ab07ap07Weekly(ab07ap07Variant), {'reason':'count-overflow',
                'attempts':ab07ap07Day,'completed_days':ab07ap07Day,
                'successful_slots':ab07ap07Day,'complete':False})
        ab07ap07Args = ab07ap07Copy.deepcopy(self.ab07ap07Cases['ab07ap07_zero']['input']['arguments'])
        for ab07ap07Day in ab07ap07Args['days']:
            ab07ap07Day['slots'] = [{'ok':False,'raw':[]}]
        self.assertEqual(ab07ap07Weekly(ab07ap07Args), {'reason':None,'attempts':0,
            'completed_days':7,'successful_slots':0,'complete':True})


def load_tests(ab07ap07Loader, ab07ap07Tests, ab07ap07Pattern):
    return ab07ap07Unittest.TestSuite(Ab07Ap07Contract(ab07ap07Name)
        for ab07ap07Name in sorted(dir(Ab07Ap07Contract)) if ab07ap07Name.startswith('TestAb07Ap07'))
