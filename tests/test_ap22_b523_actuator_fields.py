"""Synthetic specification checks, not a runtime B523 evaluator or Go API test."""
import copy
import json
from pathlib import Path
import re
import unittest

ab21ap21Root = Path(__file__).resolve().parents[1]


def ab21ap21Pairs(ab21ap21PairsInput):
    ab21ap21Object = {}
    for ab21ap21Key, ab21ap21Value in ab21ap21PairsInput:
        if ab21ap21Key in ab21ap21Object:
            raise ValueError('duplicate-key')
        ab21ap21Object[ab21ap21Key] = ab21ap21Value
    return ab21ap21Object


def ab21ap21Load(ab21ap21Text):
    return json.loads(ab21ap21Text, object_pairs_hook=ab21ap21Pairs,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('constant')))


def ab21ap21Tables(ab21ap21Text):
    ab21ap21Groups = []
    for ab21ap21Block in ab21ap21Text.split('\n\n'):
        ab21ap21Lines = ab21ap21Block.splitlines()
        if ab21ap21Lines and all(ab21ap21Line.startswith('|') for ab21ap21Line in ab21ap21Lines):
            ab21ap21Rows = [[ab21ap21Cell.strip() for ab21ap21Cell in ab21ap21Line.strip('|').split('|')]
                           for ab21ap21Line in ab21ap21Lines]
            ab21ap21Groups.append((ab21ap21Rows[0], ab21ap21Rows[2:]))
    return ab21ap21Groups


def ab21ap21Semantic(ab21ap21Raw, **ab21ap21Values):
    return dict(raw=copy.deepcopy(ab21ap21Raw), state='complete',
                grade='Hypothesis', **ab21ap21Values)


def ab21ap21Byte(ab21ap21Value):
    return type(ab21ap21Value) is int and 0 <= ab21ap21Value <= 255


def ab21ap21InvalidWitness(ab21ap21Text):
    """Bounded admission predicate for rejection witnesses; produces no result."""
    try:
        ab21ap21Input = ab21ap21Load(ab21ap21Text)
    except (ValueError, TypeError):
        return True
    if not isinstance(ab21ap21Input, dict):
        return True
    if any(type(ab21ap21Input.get(ab21ap21Key)) is not dict
           for ab21ap21Key in ('context', 'fields')):
        return True
    ab21ap21Context = ab21ap21Input['context']
    for ab21ap21Key in ('primary', 'secondary', 'operation', 'direction', 'view'):
        ab21ap21Value = ab21ap21Context.get(ab21ap21Key)
        if ab21ap21Value is None:
            continue
        if ab21ap21Key in ('primary', 'secondary', 'operation'):
            if not ab21ap21Byte(ab21ap21Value):
                return True
        elif type(ab21ap21Value) is not str:
            return True
    for ab21ap21Value in ab21ap21Input['fields'].values():
        if type(ab21ap21Value) is not list or not all(map(ab21ap21Byte, ab21ap21Value)):
            return True
    if 'arguments' in ab21ap21Input and type(ab21ap21Input['arguments']) is not dict:
        return True
    if tuple(ab21ap21Context.get(ab21ap21Key) for ab21ap21Key in
             ('primary', 'secondary', 'operation', 'direction', 'view')) == (181, 35, 2, 'request', 'mixer'):
        return ab21ap21Input.get('arguments', {}).get('variant') not in ('two-circuit', 'three-circuit')
    return False


class TestAb21Ap21Specification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ab21ap21Page = (ab21ap21Root / 'architecture/ap22_b523_actuator_fields.md').read_text()
        cls.ab21ap21Fixture = ab21ap21Load((ab21ap21Root / 'architecture/fixtures/ap22_b523_actuator_fields.json').read_text())
        cls.ab21ap21Contract = ab21ap21Load(re.findall(r'```json\n(.*?)\n```', cls.ab21ap21Page, re.S)[0])

    def ab21ap21Equal(self, ab21ap21Actual, ab21ap21Expected):
        # Canonical JSON comparison distinguishes False/0 and null/absence.
        self.assertEqual(json.dumps(ab21ap21Actual, sort_keys=True),
                         json.dumps(ab21ap21Expected, sort_keys=True))

    def test_ab21ap21_exact_callable_and_structural_contract(self):
        self.assertEqual(re.findall(r'```go\n(.*?)\n```', self.ab21ap21Page, re.S),
                         ['func Ab21Ap21Evaluate(ab21ap21Input json.RawMessage) (json.RawMessage, error)'])
        self.ab21ap21Equal(self.ab21ap21Fixture['contract'], self.ab21ap21Contract)
        ab21ap21Expected = {
            'signature': 'Ab21Ap21Evaluate(ab21ap21Input json.RawMessage) (json.RawMessage, error)',
            'package': 'vaillant', 'library': 'Go standard library',
            'context': {'primary': 181, 'secondary': 35, 'operation': 'integral u8',
                        'direction': ['request', 'positive-feedback'],
                        'view': ['relay-six', 'relay-twelve', 'mixer'],
                        'opaque': 'preserve verbatim; never qualify'},
            'routes': [[1,'request','relay-six',{'relays':6,'pwm1':1},{}],
                       [1,'positive-feedback','relay-six',{'feedback':1},{}],
                       [5,'request','relay-twelve',{'relays':12,'pwm1':1,'pwm2':1},{}],
                       [5,'positive-feedback','relay-twelve',{'feedback':1},{}],
                       [2,'request','mixer',{'circuit':1,'mode':1,'setpoint':1},
                        {'variant':['two-circuit','three-circuit']}],
                       [2,'positive-feedback','mixer',{'feedback':1,'movement':1},{}]],
            'input': {'root':'object','required':['context','fields'],
                      'fields':'object of arrays of integral u8; missing or nonexact length is incomplete',
                      'arguments':'optional object; variant required only for mixer request; unknown keys preserved',
                      'duplicates':'reject at every depth', 'kinds':'no coercion; Boolean is not integer',
                      'numbers':{'u8':[0,255],'u16':[0,65535],'u32':[0,4294967295]},
                      'context-presence':'missing, null, zero remain distinct; absent/null selectors are unsupported; opaque kinds unchanged'},
            'result': {'required':['context','raw','state','fields','physical','qualified'],
                       'optional':['arguments'], 'physical':'Unknown','qualified':False,
                       'states':['complete','partial','Unknown'],
                       'copy':'context, raw, arguments and field raw are independent; no shared mutable storage across calls',
                       'grades':{'family':'Hypothesis','arithmetic':'Proven','physical':'Unknown'},
                       'unsupported':'raw-only Unknown; fields={}; no formulas',
                       'partial':'nonexact field length; complete independent siblings survive',
                       'incomplete':'state=incomplete; raw omitted only when input field absent; no number or label',
                       'unmapped':'state=Unknown; raw retained; no invented number or label',
                       'arguments':'preserve iff supplied'},
            'relay': [[0,0,'off'],[1,253,'on-for-seconds-then-off'],[254,254,'on'],[255,255,'unchanged']],
            'pwm': {'numeric':{'formula':'raw/2','domain':[0,250],'outside':'retain calculation; candidate_domain=false'},
                    'behavior':{'domain':[0,200],'formula':'raw/2','otherwise':'unchanged'},'selection':'none'},
            'mixer': {'circuits':{'two-circuit':[0,1],'three-circuit':[0,1,2]},
                      'circuit-labels':['circuit-1','circuit-2','circuit-3'],
                      'modes':['stop/pump-off/close','heating-regulation','cooling-regulation',
                               'pump-off/open','pump-on/close','pump-on/open'],
                      'other':'ignored','setpoint-relevant':[1,2],
                      'signed':{'formula':'signed8(raw)*0.5','range':[-64,63.5]},
                      'conflicting':{'raw':190,'number':95,'clamp':95,'other':'Unknown'},'selection':'none'},
            'movement': [[-128,-101,'Unknown'],[-100,-1,'closing'],[0,0,'stopped'],[1,100,'opening'],[101,127,'Unknown']],
            'feedback': {'1':{'1':'accepted','other':'rejected'},'2':{'1':'accepted','other':'rejected'},
                         '5':{'1':'accepted','other':'rejected-or-unsupported'}},
            'errors': ['malformed-json','duplicate-key','wrong-kind','fraction','out-of-range','missing-required-argument'],
            'invariants': {'side-effects':False,'persistent-cache':False,'generic-catalog':False,'listing-api':False,
                           'runtime-caller':False,'native-qualification':False,
                           'mcp':'compatibility preserved; no registration',
                           'graphql':'same raw/context/state/alternatives/grades; no new resolver'}
        }
        self.ab21ap21Equal(self.ab21ap21Contract, ab21ap21Expected)

    def test_ab21ap21_page_tables(self):
        ab21ap21Expected = [
            (['OP','Direction','View','Fields with exact lengths','Required arguments'], [
                ['1','request','relay-six','relays:6, pwm1:1','none'],
                ['1','positive-feedback','relay-six','feedback:1','none'],
                ['5','request','relay-twelve','relays:12, pwm1:1, pwm2:1','none'],
                ['5','positive-feedback','relay-twelve','feedback:1','none'],
                ['2','request','mixer','circuit:1, mode:1, setpoint:1','variant:two-circuit/three-circuit'],
                ['2','positive-feedback','mixer','feedback:1, movement:1','none']]),
            (['Relay minimum','Relay maximum','Label','Quantity'], [
                ['0','0','off','none'], ['1','253','on-for-seconds-then-off','raw seconds'],
                ['254','254','on','none'], ['255','255','unchanged','none']]),
            (['PWM raw','Numeric percent','Numeric candidate domain','Behavior'], [
                ['200','100','true','100 percent'], ['201','100.5','true','unchanged'],
                ['250','125','true','unchanged'], ['255','127.5','false','unchanged']]),
            (['Mode','Label','Setpoint relevant'], [
                ['0','stop/pump-off/close','false'], ['1','heating-regulation','true'],
                ['2','cooling-regulation','true'], ['3','pump-off/open','false'],
                ['4','pump-on/close','false'], ['5','pump-on/open','false'], ['6..255','ignored','false']]),
            (['Setpoint raw','Signed Celsius','Conflicting Celsius','Clamp'], [
                ['0','0','Unknown','95'], ['127','63.5','Unknown','95'], ['128','-64','Unknown','95'],
                ['190','-33','95','95'], ['255','-0.5','Unknown','95']]),
            (['Movement raw','Signed percent','Label','Maximum'], [
                ['156','-100','closing','true'], ['100','100','opening','true'],
                ['155','Unknown','Unknown','Unknown'], ['101','Unknown','Unknown','Unknown']]),
            (['OP','Feedback 1','Other feedback'], [
                ['1','accepted','rejected'], ['2','accepted','rejected'], ['5','accepted','rejected-or-unsupported']])]
        self.assertEqual(ab21ap21Tables(self.ab21ap21Page), ab21ap21Expected)

    def test_ab21ap21_every_relay_slot_independently(self):
        ab21ap21Coverage = set()
        for ab21ap21Case in self.ab21ap21Fixture['relay_cases']:
            ab21ap21Op, ab21ap21Slot = ab21ap21Case['operation'], ab21ap21Case['slot']
            ab21ap21Count = {1:6, 5:12}[ab21ap21Op]
            self.assertEqual(len(ab21ap21Case['raw']), ab21ap21Count)
            self.assertEqual(len(ab21ap21Case['expected']), ab21ap21Count)
            ab21ap21Value = ab21ap21Case['raw'][ab21ap21Slot]
            ab21ap21Coverage.add((ab21ap21Op, ab21ap21Slot, ab21ap21Value))
            for ab21ap21Index, ab21ap21Raw in enumerate(ab21ap21Case['raw']):
                self.assertEqual(ab21ap21Raw, ab21ap21Value if ab21ap21Index==ab21ap21Slot else 255)
                ab21ap21Label = {0:'off',1:'on-for-seconds-then-off',253:'on-for-seconds-then-off',254:'on',255:'unchanged'}[ab21ap21Raw]
                ab21ap21Expected = ab21ap21Semantic([ab21ap21Raw], label=ab21ap21Label)
                if ab21ap21Raw in (1,253):
                    ab21ap21Expected.update(number=ab21ap21Raw, unit='seconds')
                self.ab21ap21Equal(ab21ap21Case['expected'][ab21ap21Index], ab21ap21Expected)
        self.assertEqual(ab21ap21Coverage, {(ab21ap21Op,ab21ap21Slot,ab21ap21Raw)
                         for ab21ap21Op,ab21ap21Count in ((1,6),(5,12))
                         for ab21ap21Slot in range(ab21ap21Count) for ab21ap21Raw in (0,1,253,254,255)})
        self.assertEqual(len(self.ab21ap21Fixture['relay_cases']),90)
        # Bounded intervals independently cover all remaining timer bytes.
        for ab21ap21Raw in range(1,254):
            self.assertEqual(sum(ab21ap21Low<=ab21ap21Raw<=ab21ap21High
                                 for ab21ap21Low,ab21ap21High,_ in self.ab21ap21Contract['relay']),1)
            self.assertEqual(next(ab21ap21Label for ab21ap21Low,ab21ap21High,ab21ap21Label
                                  in self.ab21ap21Contract['relay'] if ab21ap21Low<=ab21ap21Raw<=ab21ap21High),
                             'on-for-seconds-then-off')

    def ab21ap21AssertPwm(self, ab21ap21Result, ab21ap21Raw):
        ab21ap21Expected = ab21ap21Semantic([ab21ap21Raw], alternatives=[
            dict(id='numeric',number=ab21ap21Raw/2,unit='percent',candidate_domain=ab21ap21Raw<=250,
                 grade='Hypothesis',calculation='Proven'),
            dict(id='behavior',grade='Hypothesis', **(
                dict(number=ab21ap21Raw/2,unit='percent',calculation='Proven') if ab21ap21Raw<=200
                else dict(label='unchanged')))])
        self.ab21ap21Equal(ab21ap21Result,ab21ap21Expected)

    def test_ab21ap21_pwm_channels_and_alternatives(self):
        ab21ap21Coverage=set()
        for ab21ap21Case in self.ab21ap21Fixture['pwm_cases']:
            ab21ap21Channel=ab21ap21Case['channel']; ab21ap21Raw=ab21ap21Case['fields'][ab21ap21Channel][0]
            ab21ap21Coverage.add((ab21ap21Channel,ab21ap21Raw))
            self.assertEqual(ab21ap21Case['operation'],5)
            self.assertEqual(ab21ap21Case['fields']['relays'],[255]*12)
            self.assertEqual(ab21ap21Case['fields']['pwm2' if ab21ap21Channel=='pwm1' else 'pwm1'],[200])
            self.ab21ap21AssertPwm(ab21ap21Case['expected'],ab21ap21Raw)
            self.ab21ap21AssertPwm(ab21ap21Case['sibling'],200)
        self.assertEqual(ab21ap21Coverage,{(ab21ap21Channel,ab21ap21Raw) for ab21ap21Channel in ('pwm1','pwm2') for ab21ap21Raw in (0,1,200,201,250,251,255)})
        self.assertEqual(len(self.ab21ap21Fixture['pwm_cases']),14)

    def test_ab21ap21_circuit_variants_and_modes(self):
        ab21ap21Coverage=set()
        for ab21ap21Case in self.ab21ap21Fixture['circuit_cases']:
            ab21ap21Variant=ab21ap21Case['variant']; ab21ap21Raw=ab21ap21Case['raw'][0]
            ab21ap21Coverage.add((ab21ap21Variant,ab21ap21Raw))
            ab21ap21Names = {0:'circuit-1',1:'circuit-2'}
            if ab21ap21Variant=='three-circuit': ab21ap21Names[2]='circuit-3'
            self.ab21ap21Equal(ab21ap21Case['expected'],ab21ap21Semantic([ab21ap21Raw],label=ab21ap21Names.get(ab21ap21Raw,'ignored')))
        self.assertEqual(ab21ap21Coverage,{(ab21ap21Variant,ab21ap21Raw) for ab21ap21Variant in ('two-circuit','three-circuit') for ab21ap21Raw in (0,1,2,3,255)})
        ab21ap21Labels={0:'stop/pump-off/close',1:'heating-regulation',2:'cooling-regulation',3:'pump-off/open',4:'pump-on/close',5:'pump-on/open'}
        self.assertEqual([ab21ap21Case['raw'][0] for ab21ap21Case in self.ab21ap21Fixture['mode_cases']],[0,1,2,3,4,5,6,255])
        for ab21ap21Case in self.ab21ap21Fixture['mode_cases']:
            ab21ap21Raw=ab21ap21Case['raw'][0]
            self.ab21ap21Equal(ab21ap21Case['expected'],ab21ap21Semantic([ab21ap21Raw],label=ab21ap21Labels.get(ab21ap21Raw,'ignored'),setpoint_relevant=ab21ap21Raw in (1,2)))

    def ab21ap21AssertSetpoint(self, ab21ap21Result, ab21ap21Raw, ab21ap21Relevant):
        # Independent endpoint constants avoid an unsigned conversion oracle.
        ab21ap21Signed={0:0.0,127:63.5,128:-64.0,190:-33.0,255:-0.5}[ab21ap21Raw]
        self.ab21ap21Equal(ab21ap21Result,ab21ap21Semantic([ab21ap21Raw],relevant=ab21ap21Relevant,alternatives=[
            dict(id='signed',number=ab21ap21Signed,unit='Celsius',grade='Hypothesis',calculation='Proven'),
            dict(id='conflicting',clamp=95,grade='Hypothesis',**(dict(number=95,unit='Celsius') if ab21ap21Raw==190 else dict(state='Unknown')))]))

    def test_ab21ap21_competing_setpoints_and_relevance(self):
        ab21ap21Coverage=set()
        for ab21ap21Case in self.ab21ap21Fixture['setpoint_cases']:
            ab21ap21Mode=ab21ap21Case['mode']; ab21ap21Raw=ab21ap21Case['raw'][0]
            ab21ap21Coverage.add((ab21ap21Mode,ab21ap21Raw))
            self.ab21ap21AssertSetpoint(ab21ap21Case['expected'],ab21ap21Raw,ab21ap21Mode in (1,2))
        self.assertEqual(ab21ap21Coverage,{(ab21ap21Mode,ab21ap21Raw) for ab21ap21Mode in (0,1,2,3,4,5,255) for ab21ap21Raw in (0,127,128,190,255)})

    def test_ab21ap21_movement_signed_boundaries(self):
        ab21ap21Expected={0:(0,'stopped',False),1:(1,'opening',False),100:(100,'opening',True),
                          101:None,127:None,128:None,155:None,156:(-100,'closing',True),255:(-1,'closing',False)}
        self.assertEqual([ab21ap21Case['raw'][0] for ab21ap21Case in self.ab21ap21Fixture['movement_cases']], list(ab21ap21Expected))
        for ab21ap21Case in self.ab21ap21Fixture['movement_cases']:
            ab21ap21Raw=ab21ap21Case['raw'][0]; ab21ap21Tuple=ab21ap21Expected[ab21ap21Raw]
            ab21ap21Result = dict(raw=[ab21ap21Raw],state='Unknown',grade='Hypothesis') if ab21ap21Tuple is None else ab21ap21Semantic([ab21ap21Raw],number=ab21ap21Tuple[0],label=ab21ap21Tuple[1],maximum=ab21ap21Tuple[2],unit='percent',calculation='Proven')
            self.ab21ap21Equal(ab21ap21Case['expected'],ab21ap21Result)
        # Full signed partition: no overlap, gap or unsigned reinterpretation.
        for ab21ap21Signed in range(-128,128):
            ab21ap21Labels=[ab21ap21Label for ab21ap21Low,ab21ap21High,ab21ap21Label in self.ab21ap21Contract['movement'] if ab21ap21Low<=ab21ap21Signed<=ab21ap21High]
            self.assertEqual(ab21ap21Labels,['Unknown' if abs(ab21ap21Signed)>100 else 'stopped' if ab21ap21Signed==0 else 'closing' if ab21ap21Signed<0 else 'opening'])

    def test_ab21ap21_feedback_operation_specific(self):
        ab21ap21Coverage=set()
        for ab21ap21Case in self.ab21ap21Fixture['feedback_cases']:
            ab21ap21Op=ab21ap21Case['operation']; ab21ap21Raw=ab21ap21Case['raw'][0]
            ab21ap21Coverage.add((ab21ap21Op,ab21ap21Raw))
            ab21ap21Rejected={1:'rejected',2:'rejected',5:'rejected-or-unsupported'}[ab21ap21Op]
            self.ab21ap21Equal(ab21ap21Case['expected'],ab21ap21Semantic([ab21ap21Raw],label='accepted' if ab21ap21Raw==1 else ab21ap21Rejected))
        self.assertEqual(ab21ap21Coverage,{(ab21ap21Op,ab21ap21Raw) for ab21ap21Op in (1,2,5) for ab21ap21Raw in (0,1,2,255)})

    def test_ab21ap21_envelopes_partial_siblings_and_raw(self):
        ab21ap21Routes={(1,'request','relay-six'):{'relays':6,'pwm1':1},
                        (5,'request','relay-twelve'):{'relays':12,'pwm1':1,'pwm2':1},
                        (2,'request','mixer'):{'circuit':1,'mode':1,'setpoint':1},
                        (1,'positive-feedback','relay-six'):{'feedback':1},
                        (5,'positive-feedback','relay-twelve'):{'feedback':1},
                        (2,'positive-feedback','mixer'):{'feedback':1,'movement':1}}
        ab21ap21Seen=set()
        for ab21ap21Case in self.ab21ap21Fixture['envelopes']:
            with self.subTest(ab21ap21Case=ab21ap21Case['id']):
                ab21ap21Input=ab21ap21Case['input']; ab21ap21Output=ab21ap21Case['expected']
                self.assertFalse(ab21ap21InvalidWitness(json.dumps(ab21ap21Input)))
                self.ab21ap21Equal(ab21ap21Output['context'],ab21ap21Input['context'])
                self.ab21ap21Equal(ab21ap21Output['raw'],ab21ap21Input['fields'])
                self.assertEqual(ab21ap21Output['physical'],'Unknown'); self.assertIs(ab21ap21Output['qualified'],False)
                self.assertEqual(set(ab21ap21Output),{'context','raw','state','fields','physical','qualified'} | ({'arguments'} if 'arguments' in ab21ap21Input else set()))
                if 'arguments' in ab21ap21Input:
                    self.ab21ap21Equal(ab21ap21Output['arguments'],ab21ap21Input['arguments'])
                ab21ap21Context=ab21ap21Input['context']
                ab21ap21Key=tuple(ab21ap21Context.get(ab21ap21Key) for ab21ap21Key in ('operation','direction','view'))
                ab21ap21Supported = ab21ap21Context.get('primary')==181 and ab21ap21Context.get('secondary')==35 and ab21ap21Key in ab21ap21Routes
                if not ab21ap21Supported:
                    self.assertEqual(ab21ap21Output['state'],'Unknown'); self.assertEqual(ab21ap21Output['fields'],{})
                    continue
                ab21ap21Seen.add(ab21ap21Key)
                ab21ap21Lengths=ab21ap21Routes[ab21ap21Key]
                self.assertEqual(set(ab21ap21Output['fields']),set(ab21ap21Lengths))
                ab21ap21Incomplete=False
                for ab21ap21Field,ab21ap21Width in ab21ap21Lengths.items():
                    ab21ap21Result=ab21ap21Output['fields'][ab21ap21Field]
                    ab21ap21Raw=ab21ap21Input['fields'].get(ab21ap21Field)
                    if ab21ap21Raw is None or len(ab21ap21Raw)!=ab21ap21Width:
                        ab21ap21Incomplete=True
                        self.ab21ap21Equal(ab21ap21Result,dict(state='incomplete',**({'raw':ab21ap21Raw} if ab21ap21Raw is not None else {})))
                        continue
                    if ab21ap21Field.startswith('pwm'):
                        self.ab21ap21AssertPwm(ab21ap21Result,ab21ap21Raw[0])
                    elif ab21ap21Field=='setpoint':
                        ab21ap21Mode=ab21ap21Input['fields'].get('mode',[])
                        self.ab21ap21AssertSetpoint(ab21ap21Result,ab21ap21Raw[0],ab21ap21Mode[0] in (1,2) if len(ab21ap21Mode)==1 else 'Unknown')
                    elif ab21ap21Field=='relays':
                        self.ab21ap21Equal(ab21ap21Result,ab21ap21Semantic(ab21ap21Raw,items=[ab21ap21Semantic([ab21ap21Value],label={0:'off',255:'unchanged'}[ab21ap21Value]) for ab21ap21Value in ab21ap21Raw]))
                    elif ab21ap21Field=='circuit':
                        self.ab21ap21Equal(ab21ap21Result,ab21ap21Semantic(ab21ap21Raw,label={0:'circuit-1',2:'circuit-3'}[ab21ap21Raw[0]]))
                    elif ab21ap21Field=='mode':
                        self.ab21ap21Equal(ab21ap21Result,ab21ap21Semantic(ab21ap21Raw,label={0:'stop/pump-off/close',1:'heating-regulation'}[ab21ap21Raw[0]],setpoint_relevant=ab21ap21Raw[0]==1))
                    elif ab21ap21Field=='feedback':
                        self.ab21ap21Equal(ab21ap21Result,ab21ap21Semantic(ab21ap21Raw,label={0:'rejected',1:'accepted'}[ab21ap21Raw[0]]))
                    elif ab21ap21Field=='movement':
                        self.ab21ap21Equal(ab21ap21Result,ab21ap21Semantic(ab21ap21Raw,number={0:0,156:-100}[ab21ap21Raw[0]],unit='percent',label={0:'stopped',156:'closing'}[ab21ap21Raw[0]],calculation='Proven',maximum=ab21ap21Raw[0]==156))
                self.assertEqual(ab21ap21Output['state'],'partial' if ab21ap21Incomplete else 'complete')
        self.assertEqual(ab21ap21Seen,set(ab21ap21Routes))

    def test_ab21ap21_every_identity_axis_and_presence(self):
        ab21ap21Cases={ab21ap21Case['id'].removeprefix('ab21ap21-'):ab21ap21Case for ab21ap21Case in self.ab21ap21Fixture['envelopes']}
        ab21ap21Base=ab21ap21Cases['complete']['input']
        for ab21ap21Axis in ('primary','secondary','operation','direction','view'):
            ab21ap21Case=ab21ap21Cases['unsupported-'+ab21ap21Axis]
            self.assertEqual({ab21ap21Key for ab21ap21Key in ab21ap21Base['context'] if ab21ap21Base['context'][ab21ap21Key]!=ab21ap21Case['input']['context'][ab21ap21Key]}, {ab21ap21Axis})
            self.assertEqual(ab21ap21Case['input']['fields'],ab21ap21Base['fields'])
            self.assertEqual(ab21ap21Case['expected']['state'],'Unknown')
            for ab21ap21Tag in ('absent','null') + (('zero',) if ab21ap21Axis in ('primary','secondary','operation') else ()):
                ab21ap21Context=ab21ap21Cases[ab21ap21Axis+'-'+ab21ap21Tag]['expected']['context']
                if ab21ap21Tag=='absent': self.assertNotIn(ab21ap21Axis,ab21ap21Context)
                elif ab21ap21Tag=='null': self.assertIsNone(ab21ap21Context[ab21ap21Axis])
                else: self.assertIs(type(ab21ap21Context[ab21ap21Axis]),int); self.assertEqual(ab21ap21Context[ab21ap21Axis],0)
        for ab21ap21Axis in ('family','variant','opaque'):
            ab21ap21Case=ab21ap21Cases['opaque-'+ab21ap21Axis]
            self.assertEqual(ab21ap21Case['expected']['fields'],ab21ap21Cases['complete']['expected']['fields'])
            self.assertIs(ab21ap21Case['expected']['qualified'],False)
            self.assertEqual({ab21ap21Key for ab21ap21Key in set(ab21ap21Base['context'])|set(ab21ap21Case['input']['context']) if ab21ap21Base['context'].get(ab21ap21Key)!=ab21ap21Case['input']['context'].get(ab21ap21Key)}, {ab21ap21Axis})

    def test_ab21ap21_every_named_field_partial_and_zero(self):
        ab21ap21Envelopes={ab21ap21Case['id']:ab21ap21Case for ab21ap21Case in self.ab21ap21Fixture['envelopes']}
        for ab21ap21Op,ab21ap21Fields in ((1,('relays','pwm1')),(5,('relays','pwm1','pwm2')),(2,('circuit','mode','setpoint'))):
            for ab21ap21Field in ab21ap21Fields:
                for ab21ap21Tag in ('absent','empty','short','long'):
                    ab21ap21Case=ab21ap21Envelopes[f'ab21ap21-partial-{ab21ap21Op}-{ab21ap21Field}-{ab21ap21Tag}']
                    self.assertEqual(ab21ap21Case['expected']['state'],'partial')
                    self.assertEqual(ab21ap21Case['expected']['fields'][ab21ap21Field]['state'],'incomplete')
                    self.assertTrue(all(ab21ap21Result['state']=='complete' for ab21ap21Key,ab21ap21Result in ab21ap21Case['expected']['fields'].items() if ab21ap21Key!=ab21ap21Field))
                self.assertEqual(ab21ap21Envelopes[f'ab21ap21-zero-{ab21ap21Op}-{ab21ap21Field}']['expected']['state'],'complete')
        for ab21ap21Field in ('feedback','movement'):
            for ab21ap21Tag in ('absent','empty','long','zero'):
                self.assertIn(f'ab21ap21-{ab21ap21Field}-{ab21ap21Tag}',ab21ap21Envelopes)

    def test_ab21ap21_rejection_witnesses_with_valid_controls(self):
        self.assertGreater(len(self.ab21ap21Fixture['validation_cases']),100)
        for ab21ap21Case in self.ab21ap21Fixture['validation_cases']:
            with self.subTest(ab21ap21Case=ab21ap21Case['id']):
                self.assertTrue(ab21ap21InvalidWitness(ab21ap21Case['json']))
                self.assertEqual(ab21ap21Case['outcome'],'error')
                self.assertIs(ab21ap21Case['successful_result'],False)
        ab21ap21Control={'context':{'primary':181,'secondary':35,'operation':2,'direction':'request','view':'mixer'},'fields':{'circuit':[2],'mode':[1],'setpoint':[190]},'arguments':{'variant':'three-circuit','opaque':{'false':False}}}
        self.assertFalse(ab21ap21InvalidWitness(json.dumps(ab21ap21Control)))
        for ab21ap21Variant in ('two-circuit','three-circuit'):
            ab21ap21Control['arguments']['variant']=ab21ap21Variant
            self.assertFalse(ab21ap21InvalidWitness(json.dumps(ab21ap21Control)))
        # Every named field has independent Boolean and numeric-kind rejection controls.
        for ab21ap21Field in ('relays','pwm1','pwm2','circuit','mode','setpoint','feedback','movement'):
            for ab21ap21Bad in (False, [False], [0.5], [-1], [256]):
                ab21ap21Input={'context':{},'fields':{ab21ap21Field:ab21ap21Bad}}
                self.assertTrue(ab21ap21InvalidWitness(json.dumps(ab21ap21Input)))
            self.assertFalse(ab21ap21InvalidWitness(json.dumps({'context':{},'fields':{ab21ap21Field:[0]}})))
        for ab21ap21Text in ('{"context":{},"fields":{},"arguments":{"x":[{"a":0,"a":1}]}}', '{"context":{"x":{"a":0,"a":1}},"fields":{}}'):
            with self.assertRaises(ValueError): ab21ap21Load(ab21ap21Text)
        for ab21ap21Name,ab21ap21Maximum in (('u8',255),('u16',65535),('u32',4294967295)):
            self.assertEqual(self.ab21ap21Contract['input']['numbers'][ab21ap21Name],[0,ab21ap21Maximum])
            for ab21ap21Value,ab21ap21Valid in ((0,True),(ab21ap21Maximum,True),(-1,False),(ab21ap21Maximum+1,False),(False,False),(0.5,False)):
                self.assertIs(type(ab21ap21Value) is int and 0<=ab21ap21Value<=ab21ap21Maximum,ab21ap21Valid)

    def test_ab21ap21_json_witness_storage_and_roundtrips(self):
        # Demonstrates witness storage independence only; runtime copies need Go tests.
        for ab21ap21Case in self.ab21ap21Fixture['envelopes']:
            ab21ap21Snapshot=ab21ap21Load(json.dumps(ab21ap21Case))
            ab21ap21Input=ab21ap21Case['input']; ab21ap21Output=ab21ap21Case['expected']
            self.ab21ap21Equal(ab21ap21Snapshot,ab21ap21Case)
            ab21ap21Saved=copy.deepcopy(ab21ap21Output)
            ab21ap21Input['context']['ab21ap21Probe']={'x':[False]}
            ab21ap21Input['fields']['ab21ap21Probe']=[255]
            self.ab21ap21Equal(ab21ap21Output,ab21ap21Saved)
            # Restore shared test fixture before checking the opposite direction.
            ab21ap21Input.clear(); ab21ap21Input.update(copy.deepcopy(ab21ap21Snapshot['input']))
            ab21ap21Output['raw']['ab21ap21Probe']=[0]
            ab21ap21Output['context']['ab21ap21Probe']=[0]
            if 'arguments' in ab21ap21Output: ab21ap21Output['arguments']['ab21ap21Probe']=[0]
            self.ab21ap21Equal(ab21ap21Input,ab21ap21Snapshot['input'])
            ab21ap21Output.clear(); ab21ap21Output.update(copy.deepcopy(ab21ap21Saved))
            for ab21ap21Name,ab21ap21Field in ab21ap21Output['fields'].items():
                if 'raw' in ab21ap21Field:
                    ab21ap21Original=copy.deepcopy(ab21ap21Output['raw'])
                    ab21ap21Field['raw'].append(0)
                    self.ab21ap21Equal(ab21ap21Output['raw'],ab21ap21Original)
                    ab21ap21Field['raw'].pop()
                if 'alternatives' in ab21ap21Field:
                    ab21ap21Other=copy.deepcopy(ab21ap21Field['alternatives'][1])
                    ab21ap21Field['alternatives'][0]['ab21ap21Probe']=[0]
                    self.ab21ap21Equal(ab21ap21Field['alternatives'][1],ab21ap21Other)
                    del ab21ap21Field['alternatives'][0]['ab21ap21Probe']
            self.ab21ap21Equal(ab21ap21Case,ab21ap21Snapshot)

    def test_ab21ap21_synthetic_ids_and_top_level_sections(self):
        self.assertEqual(self.ab21ap21Fixture['provenance'],'synthetic')
        self.assertEqual(set(self.ab21ap21Fixture),{'provenance','contract','relay_cases','pwm_cases','circuit_cases','mode_cases','setpoint_cases','movement_cases','feedback_cases','envelopes','validation_cases'})
        ab21ap21Ids=[]
        for ab21ap21Section,ab21ap21Cases in self.ab21ap21Fixture.items():
            if isinstance(ab21ap21Cases,list):
                ab21ap21Ids.extend(ab21ap21Case['id'] for ab21ap21Case in ab21ap21Cases)
        self.assertEqual(len(ab21ap21Ids),len(set(ab21ap21Ids)))
        self.assertTrue(all(ab21ap21Id.startswith('ab21ap21-') for ab21ap21Id in ab21ap21Ids))


if __name__=='__main__':
    unittest.main()
