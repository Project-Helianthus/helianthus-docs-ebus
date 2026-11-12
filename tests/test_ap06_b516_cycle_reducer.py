"""Documentation conformance only: bounded oracles, no runtime evaluator."""
import copy as ab05ap05copy
import json as ab05ap05json
import os as ab05ap05os
from pathlib import Path as Ab05Ap05Path
import re as ab05ap05re
import unittest as ab05ap05unittest

ab05ap05root = Ab05Ap05Path(ab05ap05os.environ.get(
    'AB05AP05_ARTIFACT_ROOT', str(Ab05Ap05Path(__file__).resolve().parents[1])))
ab05ap05page = ab05ap05root / 'architecture/ap06-b516-cycle-reducer.md'
ab05ap05fixture = ab05ap05root / 'architecture/fixtures/ap06_b516_cycle_reducer.json'
ab05ap05rules = {
    'slot_count': '9', 'modulus': '4294967296', 'sentinel': '4294967295',
    'threshold': '2', 'eligibility': 'registered && capable',
    'delta': '(current - prior) modulo U',
    'changed': 'prior == sentinel OR delta >= threshold',
    'sum': 'successful admitted current values modulo U', 'clean_counter': '0',
    'failed_counter': 'prior + explicit counter_increment modulo U; otherwise Unknown',
    'partial_cycle': 'failed > 0 OR skipped > 0', 'skip_count': 'skipped',
    'partial_sum': 'retain',
}


def ab05ap05tables(ab05ap05text):
    ab05ap05result = []
    for ab05ap05block in ab05ap05re.findall(r'(?:^\|.*\|\n)+', ab05ap05text, ab05ap05re.M):
        ab05ap05rows = [[ab05ap05cell.strip() for ab05ap05cell in ab05ap05line.strip().split('|')[1:-1]]
                       for ab05ap05line in ab05ap05block.strip().splitlines()]
        ab05ap05result.append([ab05ap05rows[0]] + ab05ap05rows[2:])
    return ab05ap05result


def ab05ap05pairs(ab05ap05items):
    ab05ap05result = {}
    for ab05ap05key, ab05ap05value in ab05ap05items:
        if ab05ap05key in ab05ap05result:
            raise ValueError('duplicate key')
        ab05ap05result[ab05ap05key] = ab05ap05value
    return ab05ap05result


def ab05ap05nonfinite(ab05ap05value):
    raise ValueError('nonfinite JSON')


def ab05ap05uint(ab05ap05value, ab05ap05maximum=4294967295):
    if type(ab05ap05value) is not int or not 0 <= ab05ap05value <= ab05ap05maximum:
        raise ValueError('unsigned integral number required')


def ab05ap05admission(ab05ap05wire):
    """Test-only schema oracle; unsupported identity never reaches slot arithmetic."""
    ab05ap05input = ab05ap05json.loads(ab05ap05wire, object_pairs_hook=ab05ap05pairs,
                                     parse_constant=ab05ap05nonfinite)
    if type(ab05ap05input) is not dict:
        raise ValueError('object required')
    for ab05ap05key in ('context', 'fields'):
        if type(ab05ap05input.get(ab05ap05key)) is not dict:
            raise ValueError('object required')
    if 'arguments' in ab05ap05input and type(ab05ap05input['arguments']) is not dict:
        raise ValueError('arguments object required')
    for ab05ap05bytes in ab05ap05input['fields'].values():
        if type(ab05ap05bytes) is not list:
            raise ValueError('byte array required')
        for ab05ap05byte in ab05ap05bytes:
            ab05ap05uint(ab05ap05byte, 255)
    ab05ap05selector = {'primary':181, 'secondary':22, 'operation':20,
                       'direction':'local', 'view':'cycle'}
    ab05ap05context = ab05ap05input['context']
    if any(type(ab05ap05context.get(ab05ap05key)) is not type(ab05ap05value)
           or ab05ap05context.get(ab05ap05key) != ab05ap05value
           for ab05ap05key, ab05ap05value in ab05ap05selector.items()):
        return ab05ap05input, False
    ab05ap05arguments = ab05ap05input.get('arguments', {})
    ab05ap05uint(ab05ap05arguments.get('failure_counter'))
    if 'counter_increment' in ab05ap05arguments:
        ab05ap05uint(ab05ap05arguments['counter_increment'])
    ab05ap05slots = ab05ap05arguments.get('slots')
    if type(ab05ap05slots) is not list or len(ab05ap05slots) != 9:
        raise ValueError('nine ordered slots required')
    for ab05ap05slot in ab05ap05slots:
        if type(ab05ap05slot) is not dict:
            raise ValueError('slot object required')
        for ab05ap05key in ('registered', 'capable', 'prior_changed'):
            if type(ab05ap05slot.get(ab05ap05key)) is not bool:
                raise ValueError('Boolean required')
        for ab05ap05key in ('prior', 'prior_previous'):
            ab05ap05uint(ab05ap05slot.get(ab05ap05key))
        if ab05ap05slot.get('outcome') not in ('success', 'read-failure', 'parse-failure'):
            raise ValueError('outcome required')
        if ab05ap05slot['outcome'] == 'success':
            ab05ap05uint(ab05ap05slot.get('value'))
        elif 'value' in ab05ap05slot:
            raise ValueError('failure value must be absent')
    return ab05ap05input, True


def ab05ap05expand(ab05ap05base, ab05ap05case):
    ab05ap05input = ab05ap05copy.deepcopy(ab05ap05base)
    for ab05ap05index, ab05ap05slot in ab05ap05case['slot_updates'].items():
        ab05ap05input['arguments']['slots'][int(ab05ap05index)] = ab05ap05copy.deepcopy(ab05ap05slot)
    ab05ap05input['arguments'].update(ab05ap05copy.deepcopy(ab05ap05case['argument_updates']))
    for ab05ap05key in ab05ap05case.get('remove_arguments', []):
        ab05ap05input['arguments'].pop(ab05ap05key, None)
    return ab05ap05input


def ab05ap05transition(ab05ap05slot, ab05ap05index, ab05ap05policy):
    """Small transition oracle; intentional fault alternatives support negative controls."""
    ab05ap05admitted = ab05ap05slot['registered'] and ab05ap05slot['capable']
    if ab05ap05policy['eligibility'] == 'registered OR capable':
        ab05ap05admitted = ab05ap05slot['registered'] or ab05ap05slot['capable']
    if not ab05ap05admitted:
        return [ab05ap05index, False, 'skipped', int(ab05ap05policy['sentinel']),
                ab05ap05slot['prior_previous'], 'Unknown', ab05ap05slot['prior_changed']]
    if ab05ap05slot['outcome'] != 'success':
        return [ab05ap05index, True, ab05ap05slot['outcome'], int(ab05ap05policy['sentinel']),
                ab05ap05slot['prior'], 'Unknown', ab05ap05slot['prior_changed']]
    # Euclidean remainder via divmod gives an independent bounded unsigned oracle.
    ab05ap05delta = divmod(ab05ap05slot['value'] - ab05ap05slot['prior'],
                          int(ab05ap05policy['modulus']))[1]
    if ab05ap05policy['delta'] == 'absolute delta':
        ab05ap05delta = abs(ab05ap05slot['value'] - ab05ap05slot['prior'])
    elif ab05ap05policy['delta'] == 'signed delta':
        ab05ap05delta = ab05ap05slot['value'] - ab05ap05slot['prior']
    ab05ap05changed = (ab05ap05slot['prior'] == int(ab05ap05policy['sentinel'])
                      or ab05ap05delta >= int(ab05ap05policy['threshold']))
    return [ab05ap05index, True, 'success', ab05ap05slot['value'], ab05ap05slot['prior'],
            ab05ap05changed, ab05ap05slot['prior_changed']]


def ab05ap05cycle(ab05ap05input, ab05ap05policy):
    """Bounded projection for comparing documented scenario tuples, not an API."""
    ab05ap05arguments = ab05ap05input['arguments']
    ab05ap05rows = [ab05ap05transition(ab05ap05slot, ab05ap05index, ab05ap05policy)
                    for ab05ap05index, ab05ap05slot in enumerate(
                        ab05ap05arguments['slots'][:int(ab05ap05policy['slot_count'])])]
    ab05ap05success = sum(ab05ap05row[2] == 'success' for ab05ap05row in ab05ap05rows)
    ab05ap05failed = sum(ab05ap05row[2] in ('read-failure', 'parse-failure') for ab05ap05row in ab05ap05rows)
    ab05ap05skipped = sum(ab05ap05row[2] == 'skipped' for ab05ap05row in ab05ap05rows)
    if ab05ap05policy['skip_count'] == 'failed':
        ab05ap05failed += ab05ap05skipped
    ab05ap05sum = sum(ab05ap05row[3] for ab05ap05row in ab05ap05rows if ab05ap05row[2] == 'success')
    if ab05ap05policy['sum'] == 'saturate':
        ab05ap05sum = min(ab05ap05sum, 4294967295)
    else:
        ab05ap05sum %= int(ab05ap05policy['modulus'])
    if ab05ap05policy['partial_sum'] == 'suppress' and ab05ap05failed:
        ab05ap05sum = 'Unknown'
    ab05ap05counter = 'Unknown'
    if not ab05ap05failed:
        ab05ap05counter = (ab05ap05arguments['failure_counter'] if ab05ap05policy['clean_counter'] == 'prior'
                          else int(ab05ap05policy['clean_counter']))
    elif 'counter_increment' in ab05ap05arguments:
        ab05ap05counter = divmod(ab05ap05arguments['failure_counter'] + ab05ap05arguments['counter_increment'],
                                int(ab05ap05policy['modulus']))[1]
    return {'slots':ab05ap05rows, 'sum':ab05ap05sum, 'successful':ab05ap05success,
            'failed':ab05ap05failed, 'skipped':ab05ap05skipped, 'attempts':ab05ap05success+ab05ap05failed,
            'counter':ab05ap05counter, 'prior_failure_counter':ab05ap05arguments['failure_counter'],
            'partial_cycle':bool(ab05ap05failed or ab05ap05skipped),
            'state':'partial' if ab05ap05failed or ab05ap05skipped else 'complete'}


def ab05ap05quantity(ab05ap05value):
    ab05ap05result = {'state':'Unknown', 'grade':'Hypothesis'}
    if ab05ap05value != 'Unknown':
        ab05ap05result.update(state='complete', number=ab05ap05value, calculation='Proven')
    return ab05ap05result


def ab05ap05envelope(ab05ap05wire, ab05ap05policy):
    """Test representation projection to check detachment and Unknown boundaries."""
    ab05ap05input, ab05ap05supported = ab05ap05admission(ab05ap05wire)
    ab05ap05result = {'context':ab05ap05copy.deepcopy(ab05ap05input['context']),
                      'raw':ab05ap05copy.deepcopy(ab05ap05input['fields']),
                      'fields':{ab05ap05key:{'raw':ab05ap05copy.deepcopy(ab05ap05value),
                                          'state':'Unknown','unmodeled':True}
                                for ab05ap05key, ab05ap05value in ab05ap05input['fields'].items()},
                      'physical':'Unknown','qualified':False,
                      'grade':'Hypothesis' if ab05ap05supported else 'Unknown','state':'Unknown'}
    if 'arguments' in ab05ap05input:
        ab05ap05result['arguments'] = ab05ap05copy.deepcopy(ab05ap05input['arguments'])
    if ab05ap05supported:
        ab05ap05projection = ab05ap05cycle(ab05ap05input, ab05ap05policy)
        ab05ap05result['state'] = ab05ap05projection.pop('state')
        ab05ap05rows = ab05ap05projection.pop('slots')
        ab05ap05projection['slots'] = []
        for ab05ap05row in ab05ap05rows:
            ab05ap05changed = {'state':'Unknown', 'grade':'Hypothesis'}
            if type(ab05ap05row[5]) is bool:
                ab05ap05changed.update(state='complete', flags={'changed':ab05ap05row[5]}, calculation='Proven')
            ab05ap05projection['slots'].append({
                'index':ab05ap05row[0], 'raw':ab05ap05copy.deepcopy(ab05ap05input['arguments']['slots'][ab05ap05row[0]]),
                'admitted':ab05ap05row[1], 'outcome':ab05ap05row[2],
                'state':'complete' if ab05ap05row[2]=='success' else 'partial',
                'current':ab05ap05quantity(ab05ap05row[3]), 'previous':ab05ap05quantity(ab05ap05row[4]),
                'changed':ab05ap05changed, 'prior_changed':ab05ap05row[6], 'grade':'Hypothesis'})
        for ab05ap05key in ('sum','counter'):
            ab05ap05projection[ab05ap05key] = ab05ap05quantity(ab05ap05projection[ab05ap05key])
        ab05ap05result['cycle'] = ab05ap05projection
    return ab05ap05result


class Ab05Ap05Contract(ab05ap05unittest.TestCase):
    def setUp(ab05ap05self):
        ab05ap05self.ab05ap05data = ab05ap05json.loads(ab05ap05fixture.read_text(), object_pairs_hook=ab05ap05pairs)
        ab05ap05self.ab05ap05base = ab05ap05self.ab05ap05data['ab05ap05_base']
        ab05ap05self.ab05ap05cases = {ab05ap05case['id']:ab05ap05case for ab05ap05case in ab05ap05self.ab05ap05data['ab05ap05_cases']}
        ab05ap05self.ab05ap05tables = ab05ap05tables(ab05ap05page.read_text())
        ab05ap05self.ab05ap05policy = dict(ab05ap05self.ab05ap05tables[2][1:])

    def TestAb05Ap05PageTables(ab05ap05self):
        ab05ap05self.assertEqual(ab05ap05self.ab05ap05tables[0], [
            ['primary','secondary','operation','direction','view'], ['181','22','20','local','cycle']])
        ab05ap05self.assertEqual(ab05ap05self.ab05ap05policy, ab05ap05rules)
        ab05ap05self.assertEqual(ab05ap05self.ab05ap05tables[1], [
            ['argument','kind','requirement'],
            ['slots','array','exactly 9 ordered objects, index 0..8'],
            ['failure_counter','u32','required'], ['counter_increment','u32','optional; absent differs from zero'],
            ['slots[].registered','Boolean','required'], ['slots[].capable','Boolean','required'],
            ['slots[].prior','u32','required'], ['slots[].prior_previous','u32','required'],
            ['slots[].prior_changed','Boolean','required'],
            ['slots[].outcome','string','success, read-failure, parse-failure'],
            ['slots[].value','u32','required only for success; absent otherwise']])
        ab05ap05self.assertEqual(ab05ap05self.ab05ap05tables[3], [
            ['eligibility','supplied outcome','admitted','current','previous','changed','counted as'],
            ['false','any valid outcome','false','sentinel','prior_previous','Unknown','skipped'],
            ['true','success','true','value','prior','formula','successful'],
            ['true','read-failure','true','sentinel','prior','Unknown','failed'],
            ['true','parse-failure','true','sentinel','prior','Unknown','failed']])
        ab05ap05self.assertEqual(ab05ap05re.findall(r'```go\n(.*?)\n```', ab05ap05page.read_text(), ab05ap05re.S),
                                ['func Ab05Ap05Evaluate(ab05ap05Input json.RawMessage) (json.RawMessage, error)'])
        ab05ap05self.assertEqual(ab05ap05self.ab05ap05tables[4], [
            ['member','supported cycle representation'], ['context','unchanged object'],
            ['raw','independent deep copy of fields'], ['arguments','unchanged object if supplied; absent if absent'],
            ['state','partial if any failure or skip; otherwise complete'], ['grade','Hypothesis'],
            ['physical','Unknown'], ['qualified','false'],
            ['fields','one raw/state=Unknown/unmodeled=true object per supplied raw field'],
            ['cycle.slots','exactly nine results in input order'], ['cycle.successful','successful admitted count'],
            ['cycle.failed','failed admitted count'], ['cycle.skipped','nonadmitted count'],
            ['cycle.attempts','successful + failed'],
            ['cycle.sum','state=complete, number=u32 sum, grade=Hypothesis, calculation=Proven'],
            ['cycle.counter','complete/number/calculation=Proven if computable; otherwise Unknown without number; grade=Hypothesis'],
            ['cycle.prior_failure_counter','unchanged input failure_counter'],
            ['cycle.partial_cycle','true if failure or skip; false otherwise']])

    def TestAb05Ap05Scenarios(ab05ap05self):
        ab05ap05self.assertEqual(len(ab05ap05self.ab05ap05cases), 14)
        for ab05ap05case in ab05ap05self.ab05ap05cases.values():
            with ab05ap05self.subTest(case=ab05ap05case['id']):
                ab05ap05input = ab05ap05expand(ab05ap05self.ab05ap05base, ab05ap05case)
                ab05ap05admission(ab05ap05json.dumps(ab05ap05input))
                ab05ap05self.assertEqual(ab05ap05cycle(ab05ap05input, ab05ap05self.ab05ap05policy), ab05ap05case['expected'])
        # Independent constants prevent coherent input/expected drift of key witnesses.
        ab05ap05witnesses = {'delta_one':(11,False), 'delta_two':(12,True),
                            'wrap_delta':(10,True), 'sentinel_zero':(0,True),
                            'success_sentinel':(4294967295,True)}
        for ab05ap05name, (ab05ap05number, ab05ap05changed) in ab05ap05witnesses.items():
            ab05ap05expected = ab05ap05self.ab05ap05cases['ab05ap05_'+ab05ap05name]['expected']
            ab05ap05self.assertEqual((ab05ap05expected['sum'], ab05ap05expected['slots'][0][5]),
                                    (ab05ap05number, ab05ap05changed))
        ab05ap05self.assertEqual(ab05ap05self.ab05ap05cases['ab05ap05_sum_wrap']['expected']['sum'], 1)
        ab05ap05self.assertEqual(ab05ap05self.ab05ap05cases['ab05ap05_partial_sibling']['expected']['sum'], 12)

    def TestAb05Ap05AllSlotPredicatesAndOutcomes(ab05ap05self):
        for ab05ap05index in range(9):
            for ab05ap05registered in (False, True):
                for ab05ap05capable in (False, True):
                    for ab05ap05outcome in ('success', 'read-failure', 'parse-failure'):
                        for ab05ap05oldchanged in (False, True):
                            with ab05ap05self.subTest(index=ab05ap05index, registered=ab05ap05registered,
                                                    capable=ab05ap05capable, outcome=ab05ap05outcome,
                                                    prior_changed=ab05ap05oldchanged):
                                ab05ap05input = ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
                                ab05ap05slot = {'registered':ab05ap05registered,'capable':ab05ap05capable,
                                               'prior':10,'prior_previous':23,'prior_changed':ab05ap05oldchanged,
                                               'outcome':ab05ap05outcome}
                                if ab05ap05outcome == 'success':
                                    ab05ap05slot['value'] = 12
                                ab05ap05input['arguments']['slots'][ab05ap05index] = ab05ap05slot
                                ab05ap05admission(ab05ap05json.dumps(ab05ap05input))
                                ab05ap05result = ab05ap05cycle(ab05ap05input, ab05ap05self.ab05ap05policy)
                                ab05ap05admit = ab05ap05registered and ab05ap05capable
                                ab05ap05success = ab05ap05admit and ab05ap05outcome == 'success'
                                ab05ap05self.assertEqual(ab05ap05result['slots'][ab05ap05index], [
                                    ab05ap05index, ab05ap05admit, ab05ap05outcome if ab05ap05admit else 'skipped',
                                    12 if ab05ap05success else 4294967295, 10 if ab05ap05admit else 23,
                                    True if ab05ap05success else 'Unknown', ab05ap05oldchanged])
                                ab05ap05self.assertEqual(ab05ap05result['sum'], 12 if ab05ap05success else 0)
                                ab05ap05self.assertEqual((ab05ap05result['successful'],ab05ap05result['failed'],
                                                         ab05ap05result['skipped'],ab05ap05result['attempts']),
                                                        (8+int(ab05ap05success),int(ab05ap05admit and not ab05ap05success),
                                                         int(not ab05ap05admit),8+int(ab05ap05admit)))

    def TestAb05Ap05UnsignedThresholds(ab05ap05self):
        for ab05ap05prior, ab05ap05value, ab05ap05changed in (
                (10,11,False),(10,12,True),(12,10,True),(12,11,True),
                (4294967295,0,True),(4294967294,0,True),(0,0,False),
                (4294967295,4294967295,True),(0,4294967295,True)):
            ab05ap05slot = dict(ab05ap05self.ab05ap05base['arguments']['slots'][0],
                                prior=ab05ap05prior, value=ab05ap05value)
            ab05ap05self.assertIs(ab05ap05transition(ab05ap05slot,0,ab05ap05self.ab05ap05policy)[5], ab05ap05changed)

    def TestAb05Ap05ContextAxesAndOpaquePreservation(ab05ap05self):
        for ab05ap05key in ('primary','secondary','operation','direction','view'):
            for ab05ap05value in (None,0,False,'unsupported',[],{},14):
                ab05ap05input = ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
                ab05ap05input['context'][ab05ap05key] = ab05ap05value
                for ab05ap05absent in (False, True):
                    if ab05ap05absent:
                        ab05ap05input['context'].pop(ab05ap05key, None)
                    ab05ap05result = ab05ap05envelope(ab05ap05json.dumps(ab05ap05input),ab05ap05self.ab05ap05policy)
                    ab05ap05self.assertEqual(ab05ap05result['state'],'Unknown')
                    ab05ap05self.assertNotIn('cycle',ab05ap05result)
                    ab05ap05self.assertEqual(ab05ap05result['context'],ab05ap05input['context'])
                    ab05ap05self.assertFalse(ab05ap05result['qualified'])
        for ab05ap05key in ('family','variant','opaque'):
            for ab05ap05value in (None,0,False,'other-family',[],{'nested':[0,None,False]}):
                ab05ap05input = ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
                ab05ap05input['context'][ab05ap05key] = ab05ap05value
                ab05ap05result = ab05ap05envelope(ab05ap05json.dumps(ab05ap05input),ab05ap05self.ab05ap05policy)
                ab05ap05self.assertEqual(ab05ap05result['context'],ab05ap05input['context'])
                ab05ap05self.assertEqual((ab05ap05result['state'],ab05ap05result['grade'],ab05ap05result['physical'],ab05ap05result['qualified']),
                                        ('complete','Hypothesis','Unknown',False))
        for ab05ap05key in ('family','variant','opaque'):
            ab05ap05input = ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
            del ab05ap05input['context'][ab05ap05key]
            ab05ap05result=ab05ap05envelope(ab05ap05json.dumps(ab05ap05input),ab05ap05self.ab05ap05policy)
            ab05ap05self.assertNotIn(ab05ap05key,ab05ap05result['context'])
            ab05ap05self.assertEqual(ab05ap05result['state'],'complete')
        ab05ap05input = {'context':{},'fields':{}}
        ab05ap05self.assertNotIn('arguments',ab05ap05envelope(ab05ap05json.dumps(ab05ap05input),ab05ap05self.ab05ap05policy))

    def TestAb05Ap05RawFieldsAndRoundTrips(ab05ap05self):
        for ab05ap05key in ('sample','empty','new_raw'):
            for ab05ap05value in ([],[0],[255],[0,1,2,3,4,5,6,7,8,255]):
                ab05ap05input = ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
                ab05ap05input['fields'][ab05ap05key] = ab05ap05value
                ab05ap05result = ab05ap05envelope(ab05ap05json.dumps(ab05ap05input),ab05ap05self.ab05ap05policy)
                ab05ap05self.assertEqual(ab05ap05result['fields'][ab05ap05key],
                                        {'raw':ab05ap05value,'state':'Unknown','unmodeled':True})
                ab05ap05self.assertEqual(ab05ap05result['cycle']['sum']['number'],0)
                ab05ap05self.assertEqual(ab05ap05json.loads(ab05ap05json.dumps(ab05ap05result)),ab05ap05result)
            ab05ap05input['fields'].pop(ab05ap05key)
            ab05ap05self.assertNotIn(ab05ap05key,ab05ap05envelope(ab05ap05json.dumps(ab05ap05input),ab05ap05self.ab05ap05policy)['fields'])

    def TestAb05Ap05MalformedDuplicateAndWrongKinds(ab05ap05self):
        for ab05ap05wire in ('{','{} []','[]','null','{"context":{},"context":{},"fields":{}}',
                '{"context":{"x":{"a":0,"a":1}},"fields":{}}',
                '{"context":{},"fields":{"x":[NaN]}}',
                '{"context":{},"fields":{},"arguments":{"x":{"a":0,"a":1}}}'):
            with ab05ap05self.assertRaises(ValueError):
                ab05ap05admission(ab05ap05wire)
        for ab05ap05key in ('context','fields','arguments'):
            for ab05ap05bad in (None,False,0,'',[]):
                ab05ap05input=ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
                ab05ap05input[ab05ap05key]=ab05ap05bad
                with ab05ap05self.assertRaises(ValueError):
                    ab05ap05admission(ab05ap05json.dumps(ab05ap05input))
        for ab05ap05bad in (None,False,True,0,1.5,'',{},[True],[False],[-1],[256],[1.5],[None],['0']):
            ab05ap05input=ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
            ab05ap05input['fields']['sample']=ab05ap05bad
            with ab05ap05self.assertRaises(ValueError):
                ab05ap05admission(ab05ap05json.dumps(ab05ap05input))
        for ab05ap05key in ('slots','failure_counter','counter_increment'):
            for ab05ap05bad in (None,False,True,-1,4294967296,1.5,'0',{},[]):
                ab05ap05input=ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
                ab05ap05input['arguments'][ab05ap05key]=ab05ap05bad
                with ab05ap05self.assertRaises(ValueError):
                    ab05ap05admission(ab05ap05json.dumps(ab05ap05input))
        for ab05ap05length in (0,8,10):
            ab05ap05input=ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
            ab05ap05input['arguments']['slots']=[ab05ap05copy.deepcopy(ab05ap05input['arguments']['slots'][0]) for ab05ap05index in range(ab05ap05length)]
            with ab05ap05self.assertRaises(ValueError):
                ab05ap05admission(ab05ap05json.dumps(ab05ap05input))
        for ab05ap05key in ('slots','failure_counter'):
            ab05ap05input=ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
            del ab05ap05input['arguments'][ab05ap05key]
            with ab05ap05self.assertRaises(ValueError):
                ab05ap05admission(ab05ap05json.dumps(ab05ap05input))
        ab05ap05input=ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
        del ab05ap05input['arguments']
        with ab05ap05self.assertRaises(ValueError):
            ab05ap05admission(ab05ap05json.dumps(ab05ap05input))

    def TestAb05Ap05MissingObjectsAndNestedDuplicates(ab05ap05self):
        for ab05ap05key in ('context','fields'):
            ab05ap05input=ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
            del ab05ap05input[ab05ap05key]
            with ab05ap05self.assertRaises(ValueError):
                ab05ap05admission(ab05ap05json.dumps(ab05ap05input))
        ab05ap05wire=ab05ap05json.dumps(ab05ap05self.ab05ap05base)
        for ab05ap05old,ab05ap05new in (
                ('"prior": 0','"prior": 0, "prior": 1'),
                ('"sample": [0, 255]','"sample": [0, 255], "sample": []'),
                ('"values": [null, 0, false]','"values": [null, 0, false], "values": []')):
            ab05ap05self.assertIn(ab05ap05old,ab05ap05wire)
            with ab05ap05self.assertRaises(ValueError):
                ab05ap05admission(ab05ap05wire.replace(ab05ap05old,ab05ap05new,1))
        for ab05ap05index in range(9):
            for ab05ap05bad in (None,False,[],0,''):
                ab05ap05input=ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
                ab05ap05input['arguments']['slots'][ab05ap05index]=ab05ap05bad
                with ab05ap05self.assertRaises(ValueError):
                    ab05ap05admission(ab05ap05json.dumps(ab05ap05input))
            for ab05ap05outcome in ('read-failure','parse-failure'):
                ab05ap05input=ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
                ab05ap05input['arguments']['slots'][ab05ap05index]['outcome']=ab05ap05outcome
                with ab05ap05self.assertRaises(ValueError):
                    ab05ap05admission(ab05ap05json.dumps(ab05ap05input))

    def TestAb05Ap05EverySlotMemberAdmission(ab05ap05self):
        for ab05ap05index in range(9):
            for ab05ap05key in ('registered','capable','prior','prior_previous','prior_changed','outcome','value'):
                ab05ap05badvalues = (None,0,1,'false',[],{}) if ab05ap05key in ('registered','capable','prior_changed') else (
                    (None,False,0,'unknown',[],{}) if ab05ap05key=='outcome' else (None,True,False,-1,4294967296,1.5,'0',[],{}))
                for ab05ap05bad in ab05ap05badvalues:
                    ab05ap05input=ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
                    ab05ap05input['arguments']['slots'][ab05ap05index][ab05ap05key]=ab05ap05bad
                    with ab05ap05self.assertRaises(ValueError):
                        ab05ap05admission(ab05ap05json.dumps(ab05ap05input))
                ab05ap05input=ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
                del ab05ap05input['arguments']['slots'][ab05ap05index][ab05ap05key]
                with ab05ap05self.assertRaises(ValueError):
                    ab05ap05admission(ab05ap05json.dumps(ab05ap05input))
            for ab05ap05key in ('prior','prior_previous','value'):
                for ab05ap05number in (0,1,4294967295):
                    ab05ap05input=ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
                    ab05ap05input['arguments']['slots'][ab05ap05index][ab05ap05key]=ab05ap05number
                    ab05ap05admission(ab05ap05json.dumps(ab05ap05input))
                    ab05ap05row=ab05ap05cycle(ab05ap05input,ab05ap05self.ab05ap05policy)['slots'][ab05ap05index]
                    if ab05ap05key=='prior':
                        ab05ap05self.assertEqual(ab05ap05row[4],ab05ap05number)
                    elif ab05ap05key=='value':
                        ab05ap05self.assertEqual(ab05ap05row[3],ab05ap05number)
                    else:
                        ab05ap05input['arguments']['slots'][ab05ap05index]['registered']=False
                        ab05ap05self.assertEqual(ab05ap05cycle(ab05ap05input,ab05ap05self.ab05ap05policy)['slots'][ab05ap05index][4],ab05ap05number)

    def TestAb05Ap05IndependentCopies(ab05ap05self):
        ab05ap05input=ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
        ab05ap05wire=ab05ap05json.dumps(ab05ap05input)
        ab05ap05first=ab05ap05envelope(ab05ap05wire,ab05ap05self.ab05ap05policy)
        ab05ap05second=ab05ap05envelope(ab05ap05wire,ab05ap05self.ab05ap05policy)
        for ab05ap05tree in (ab05ap05input, ab05ap05first):
            ab05ap05tree['context']['opaque']['values'].append('mutation')
            ab05ap05tree['arguments']['opaque']['values'].append('mutation')
            ab05ap05tree['arguments']['slots'][0]['prior']=123
        ab05ap05first['raw']['sample'].append(42)
        ab05ap05self.assertEqual(ab05ap05first['fields']['sample']['raw'],[0,255])
        ab05ap05first['fields']['sample']['raw'].append(43)
        ab05ap05self.assertEqual(ab05ap05first['raw']['sample'],[0,255,42])
        ab05ap05first['cycle']['slots'][0]['current']['number']=123
        ab05ap05first['cycle']['slots'][0]['raw']['prior']=124
        ab05ap05self.assertEqual(ab05ap05first['arguments']['slots'][0]['prior'],123)
        ab05ap05self.assertEqual(ab05ap05second,ab05ap05envelope(ab05ap05wire,ab05ap05self.ab05ap05policy))
        ab05ap05self.assertEqual(ab05ap05second['cycle']['slots'][0]['current']['number'],0)

    def TestAb05Ap05CounterPresenceAndOpaqueArguments(ab05ap05self):
        for ab05ap05prior in (0,1,4294967295):
            for ab05ap05increment in (None,0,1,4294967295):
                ab05ap05input=ab05ap05expand(ab05ap05self.ab05ap05base,ab05ap05self.ab05ap05cases['ab05ap05_failure_unknown'])
                ab05ap05input['arguments']['failure_counter']=ab05ap05prior
                if ab05ap05increment is not None:
                    ab05ap05input['arguments']['counter_increment']=ab05ap05increment
                ab05ap05result=ab05ap05envelope(ab05ap05json.dumps(ab05ap05input),ab05ap05self.ab05ap05policy)
                ab05ap05expected='Unknown' if ab05ap05increment is None else (ab05ap05prior+ab05ap05increment)&4294967295
                ab05ap05self.assertEqual(ab05ap05result['cycle']['counter'].get('number','Unknown'),ab05ap05expected)
                ab05ap05self.assertEqual(ab05ap05result['cycle']['prior_failure_counter'],ab05ap05prior)
                ab05ap05self.assertEqual(ab05ap05result['arguments'],ab05ap05input['arguments'])
        for ab05ap05value in (None,False,0,[],{}, {'nested':[False,None,0]}):
            ab05ap05input=ab05ap05copy.deepcopy(ab05ap05self.ab05ap05base)
            ab05ap05input['arguments']['opaque']=ab05ap05value
            ab05ap05self.assertEqual(ab05ap05envelope(ab05ap05json.dumps(ab05ap05input),ab05ap05self.ab05ap05policy)['arguments'],ab05ap05input['arguments'])

    def TestAb05Ap05SemanticShapesAndGrades(ab05ap05self):
        for ab05ap05case in ab05ap05self.ab05ap05cases.values():
            ab05ap05input=ab05ap05expand(ab05ap05self.ab05ap05base,ab05ap05case)
            ab05ap05result=ab05ap05envelope(ab05ap05json.dumps(ab05ap05input),ab05ap05self.ab05ap05policy)
            ab05ap05self.assertEqual(set(ab05ap05result),
                                    {'context','raw','arguments','fields','state','grade','physical','qualified','cycle'})
            ab05ap05self.assertEqual(ab05ap05result['raw'],ab05ap05input['fields'])
            ab05ap05self.assertEqual(ab05ap05result['state'],ab05ap05case['expected']['state'])
            ab05ap05self.assertEqual((ab05ap05result['grade'],ab05ap05result['physical'],ab05ap05result['qualified']),
                                    ('Hypothesis','Unknown',False))
            for ab05ap05key in ('sum','counter'):
                ab05ap05expected={'state':'Unknown','grade':'Hypothesis'}
                if ab05ap05case['expected'][ab05ap05key]!='Unknown':
                    ab05ap05expected={'state':'complete','grade':'Hypothesis','calculation':'Proven',
                                      'number':ab05ap05case['expected'][ab05ap05key]}
                ab05ap05self.assertEqual(ab05ap05result['cycle'][ab05ap05key],ab05ap05expected)
            for ab05ap05slot, ab05ap05tuple in zip(ab05ap05result['cycle']['slots'],ab05ap05case['expected']['slots']):
                ab05ap05self.assertEqual(set(ab05ap05slot),{'index','raw','admitted','outcome','state',
                                                          'current','previous','changed','prior_changed','grade'})
                ab05ap05self.assertEqual(ab05ap05slot['raw'],ab05ap05input['arguments']['slots'][ab05ap05tuple[0]])
                ab05ap05self.assertEqual(ab05ap05slot['grade'],'Hypothesis')
                for ab05ap05key, ab05ap05offset in (('current',3),('previous',4)):
                    ab05ap05self.assertEqual(ab05ap05slot[ab05ap05key],{'state':'complete',
                        'number':ab05ap05tuple[ab05ap05offset],'grade':'Hypothesis','calculation':'Proven'})
                ab05ap05expected={'state':'Unknown','grade':'Hypothesis'}
                if type(ab05ap05tuple[5]) is bool:
                    ab05ap05expected={'state':'complete','grade':'Hypothesis','calculation':'Proven',
                                      'flags':{'changed':ab05ap05tuple[5]}}
                ab05ap05self.assertEqual(ab05ap05slot['changed'],ab05ap05expected)
            ab05ap05self.assertEqual(ab05ap05json.loads(ab05ap05json.dumps(ab05ap05result)),ab05ap05result)

    def TestAb05Ap05DiscriminatingFaultControls(ab05ap05self):
        # Each negative control fails the same equality its valid control passes.
        for ab05ap05key, ab05ap05fault, ab05ap05case in (
                ('slot_count','8','clean'),('eligibility','registered OR capable','skip_registration'),
                ('delta','signed delta','wrap_delta'),('threshold','1','delta_one'),
                ('sum','saturate','sum_wrap'),('skip_count','failed','skip_registration'),
                ('clean_counter','prior','clean'),('partial_sum','suppress','partial_sibling')):
            ab05ap05scenario=ab05ap05self.ab05ap05cases['ab05ap05_'+ab05ap05case]
            ab05ap05input=ab05ap05expand(ab05ap05self.ab05ap05base,ab05ap05scenario)
            ab05ap05self.assertEqual(ab05ap05cycle(ab05ap05input,ab05ap05self.ab05ap05policy),ab05ap05scenario['expected'])
            ab05ap05faulty=dict(ab05ap05self.ab05ap05policy)
            ab05ap05faulty[ab05ap05key]=ab05ap05fault
            with ab05ap05self.assertRaises(AssertionError):
                ab05ap05self.assertEqual(ab05ap05cycle(ab05ap05input,ab05ap05faulty),ab05ap05scenario['expected'])
        ab05ap05slot=dict(ab05ap05self.ab05ap05base['arguments']['slots'][0], prior=12,value=11)
        ab05ap05self.assertTrue(ab05ap05transition(ab05ap05slot,0,ab05ap05self.ab05ap05policy)[5])
        ab05ap05self.assertFalse(ab05ap05transition(ab05ap05slot,0,dict(ab05ap05self.ab05ap05policy,delta='absolute delta'))[5])


def load_tests(ab05ap05loader, ab05ap05tests, ab05ap05pattern):
    ab05ap05loader.testMethodPrefix = 'TestAb05Ap05'
    return ab05ap05loader.loadTestsFromTestCase(Ab05Ap05Contract)
