"""Bounded candidate oracle only; no native or installed-support qualification."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
UNKNOWN = 'Unknown'


def capability(service, success, feedback, count, prior):
    if service != 'B510':
        return UNKNOWN, UNKNOWN
    if not success or feedback != 1:
        return prior, 'stale/unknown'
    if count in (1, 2):
        return 0, UNKNOWN
    if count > 2:
        return 64, UNKNOWN
    return UNKNOWN, UNKNOWN


def health(event):
    value = {'initialize': 0, 'connected': 1, 'leave': 2,
             'reset': 2, 'disconnect': 2}.get(event, UNKNOWN)
    return value, value == 1 if value != UNKNOWN else UNKNOWN


def association(event):
    return {'connected': 2, 'connecting': 1}.get(event, UNKNOWN)


def getter(service, op, obj, count, wired, wireless, cached_health, signal, raw):
    if service != 'B511' or op != 14 or not obj or count <= 0:
        return UNKNOWN
    if cached_health not in (0, 1, 2):
        return UNKNOWN
    return (raw & 232) | wired | (wireless << 1) | ((cached_health == 1) << 2) | (signal << 4)


def counter(previous, steps):
    streak = 0
    resets = []
    for step, value in enumerate(steps, 1):
        streak = streak + 1 if value == previous else 0
        previous = value
        if streak == 6:
            resets.append(step)
            # Scheduling after this first reset is unprovided.
            break
    return resets


def signal_query(success, result, prior):
    return result if success else prior


def refresh(service, op, registration, index, selector, success, count, reply, prior):
    if service != 'B511' or op != 1:
        return UNKNOWN, UNKNOWN
    if not registration & 1 or index == 1 or index == selector or not success or count == 0:
        return prior, []  # No copy: retain last-known-good bytes separately.
    if len(reply) < 9:
        return UNKNOWN, UNKNOWN
    copied = reply[:9]
    return copied[8] & 1, copied


def timer(index, failure):
    if index != 0:
        return UNKNOWN, UNKNOWN
    return (120, 'failure') if failure != 0 else (UNKNOWN, 'capability')


# Independent expected declarations: never derived from the page or loaded fixture.
EXPECTED = {
 'capability': [['service','success','feedback','count','prior','value','freshness','grade'],
 ['B510',1,1,1,85,0,'Unknown','Hypothesis'],['B510',1,1,2,85,0,'Unknown','Hypothesis'],['B510',1,1,3,85,64,'Unknown','Hypothesis'],['B510',1,1,0,85,'Unknown','Unknown','Unknown'],['B510',0,1,3,85,85,'stale/unknown','Hypothesis'],['B510',1,2,3,85,85,'stale/unknown','Hypothesis'],['B511',1,1,3,85,'Unknown','Unknown','Unknown']],
 'health': [['event','value','exposed','grade'],['initialize',0,False,'Hypothesis'],['connected',1,True,'Hypothesis'],['leave',2,False,'Hypothesis'],['reset',2,False,'Hypothesis'],['disconnect',2,False,'Hypothesis'],['other','Unknown','Unknown','Unknown']],
 'association': [['event','value','grade'],['connected',2,'Hypothesis'],['connecting',1,'Hypothesis'],['other','Unknown','Unknown']],
 'bits': [['bit','mask','meaning','grade'],[0,1,'wired diagnostic','Hypothesis'],[1,2,'wireless diagnostic','Hypothesis'],[2,4,'cached connection health','Hypothesis'],[3,8,'raw','Unknown'],[4,16,'retained successful signal-query result','Hypothesis'],[5,32,'raw','Unknown'],[6,64,'raw','Unknown'],[7,128,'raw','Unknown']],
 'getter': [['service','op','object','logical_count','wired','wireless','health','signal','raw','value','grade'],['B511',14,True,1,0,0,0,0,0,0,'Hypothesis'],['B511',14,True,2,1,1,1,1,232,255,'Hypothesis'],['B511',14,True,1,0,0,2,0,232,232,'Hypothesis'],['B510',14,True,1,0,0,1,0,0,'Unknown','Unknown'],['B511',1,True,1,0,0,1,0,0,'Unknown','Unknown'],['B511',14,False,1,0,0,1,0,0,'Unknown','Unknown'],['B511',14,True,0,0,0,1,0,0,'Unknown','Unknown']],
 'counter': [['previous','steps','reset_at','grade'],[7,[7,7,7,7,7],[],'Hypothesis'],[7,[7,7,7,7,7,7],[6],'Hypothesis'],[7,[7,7,7,7,7,8,8,8,8,8,8],[],'Hypothesis'],[7,[7,7,7,7,7,8,8,8,8,8,8,8],[12],'Hypothesis']],
 'signal': [['success','result','prior','retained','grade'],[False,0,1,1,'Hypothesis'],[False,1,0,0,'Hypothesis'],[True,0,1,0,'Hypothesis'],[True,1,0,1,'Hypothesis']],
 'refresh': [['service','op','registration','index','selector','success','count','reply','prior','failure','copied','grade'],
 ['B511',1,1,0,3,True,1,[10,11,12,13,14,15,16,17,0],1,0,[10,11,12,13,14,15,16,17,0],'Hypothesis'],
 ['B511',1,1,0,3,True,2,[10,11,12,13,14,15,16,17,1],0,1,[10,11,12,13,14,15,16,17,1],'Hypothesis'],
 ['B511',1,3,0,3,True,1,[10,11,12,13,14,15,16,17,2,99],1,0,[10,11,12,13,14,15,16,17,2],'Hypothesis'],
 ['B511',1,2,0,3,True,1,[0,0,0,0,0,0,0,0,0],1,1,[],'Hypothesis'],
 ['B511',1,1,1,3,True,1,[0,0,0,0,0,0,0,0,0],1,1,[],'Hypothesis'],
 ['B511',1,1,0,0,True,1,[0,0,0,0,0,0,0,0,0],1,1,[],'Hypothesis'],
 ['B511',1,1,0,3,False,1,[0,0,0,0,0,0,0,0,0],1,1,[],'Hypothesis'],
 ['B511',1,1,0,3,True,0,[0,0,0,0,0,0,0,0,0],1,1,[],'Hypothesis'],
 ['B511',1,1,0,3,True,1,[0,0,0,0,0,0,0,0],1,'Unknown','Unknown','Unknown'],
 ['B510',1,1,0,3,True,1,[0,0,0,0,0,0,0,0,0],1,'Unknown','Unknown','Unknown'],
 ['B511',14,1,0,3,True,1,[0,0,0,0,0,0,0,0,0],1,'Unknown','Unknown','Unknown']],
 'timer': [['index','failure','argument','path','grade'],[0,1,120,'failure','Hypothesis'],[0,2,120,'failure','Hypothesis'],[0,0,'Unknown','capability','Hypothesis'],[1,1,'Unknown','Unknown','Unknown']],
 'constants': [['name','value','grade'],['check_interval_seconds',5,'Hypothesis'],['unchanged_threshold',6,'Hypothesis'],['copy_bytes',9,'Hypothesis'],['failure_index',8,'Hypothesis'],['failure_mask',1,'Hypothesis'],['getter_bytes',1,'Hypothesis'],['refresh_before_timer','Unknown','Unknown'],['failure_initial',0,'Hypothesis'],['capability_initial','Unknown','Unknown']]
}


def page_tables(text):
    tables = {}
    current = None
    for line in text.splitlines():
        if line.startswith('## '):
            current = line[3:]
        elif line.startswith('| ') and current in EXPECTED:
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            if all(cell == '---' for cell in cells):
                continue
            if current not in tables:
                tables[current] = [cells]
            else:
                tables[current].append([json.loads(cell) for cell in cells])
    return tables


class CandidateTransitions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / 'architecture/fixtures/ai28_b510_b511_local_cache.json').read_text())
        cls.tables = cls.fixture['tables']

    def test_independent_page_and_fixture_contract(self):
        self.assertEqual(set(self.fixture), {'scope', 'tables'})
        self.assertEqual(self.fixture['scope'], 'synthetic local candidate oracle; no installed qualification')
        self.assertEqual(list(self.tables), list(EXPECTED))
        parsed = page_tables((ROOT / 'architecture/b510_b511_local_cache.md').read_text())
        self.assertEqual(list(parsed), list(EXPECTED))
        for name, rows in EXPECTED.items():
            with self.subTest(table=name):
                # JSON comparison also distinguishes true from integer 1.
                self.assertEqual(json.dumps(self.tables[name]), json.dumps(rows))
                self.assertEqual(json.dumps(parsed[name]), json.dumps(rows))

    def test_capability(self):
        for row in self.tables['capability'][1:]:
            self.assertEqual(capability(*row[:5]), tuple(row[5:7]))
        for count in range(1, 301):
            self.assertEqual(capability('B510', True, 1, count, 85)[0], 0 if count <= 2 else 64)
        for prior in range(256):
            for feedback in (0, 2, 255):
                self.assertEqual(capability('B510', True, feedback, 3, prior), (prior, 'stale/unknown'))
            self.assertEqual(capability('B510', False, 1, 3, prior), (prior, 'stale/unknown'))
        self.assertEqual(capability('B510', True, 1, 0, 85), (UNKNOWN, UNKNOWN))

    def test_health_and_association_are_distinct(self):
        for event, value, exposed, _ in self.tables['health'][1:]:
            self.assertEqual(health(event), (value, exposed))
        for event, value, _ in self.tables['association'][1:]:
            self.assertEqual(association(event), value)
        self.assertEqual(health('connected'), (1, True))
        self.assertEqual(association('connected'), 2)
        self.assertEqual(health('reset'), (2, False))

    def test_getter_bits_and_guards(self):
        for row in self.tables['getter'][1:]:
            self.assertEqual(getter(*row[:9]), row[9])
        for bit, mask, _, grade in self.tables['bits'][1:]:
            self.assertEqual(mask, 1 << bit)
            self.assertEqual(grade, UNKNOWN if bit in (3, 5, 6, 7) else 'Hypothesis')
        # Independent bit arithmetic across the full raw-byte domain.
        for raw in range(256):
            for cached in (0, 1, 2):
                self.assertEqual(getter('B511',14,True,1,0,0,cached,0,raw), (raw & 232) + (4 if cached == 1 else 0))
        for offset, expected in ((4,1),(5,2),(6,4),(7,16)):
            args = ['B511',14,True,1,0,0,0,0,0]
            args[offset] = 1
            self.assertEqual(getter(*args), expected)
        base = ['B511',14,True,1,0,0,1,0,0]
        self.assertEqual(getter(*base), 4)
        for axis, alternative in ((0,'B510'),(1,1),(2,False),(3,0),(6,3)):
            changed = base.copy(); changed[axis] = alternative
            self.assertEqual(getter(*changed), UNKNOWN)

    def test_counter_and_signal(self):
        for previous, steps, reset_at, _ in self.tables['counter'][1:]:
            self.assertEqual(counter(previous, steps), reset_at)
        for position in range(6):
            self.assertEqual(counter(7, [7]*position + [8] + [8]*5), [])
        self.assertEqual(5 * 6, 30)
        for success, result, prior, retained, _ in self.tables['signal'][1:]:
            self.assertEqual(signal_query(success, result, prior), retained)
            self.assertEqual(getter('B511',14,True,1,0,0,0,retained,0), retained * 16)

    def test_refresh_selection_copy_and_retention(self):
        for row in self.tables['refresh'][1:]:
            self.assertEqual(refresh(*row[:9]), (row[9], row[10]))
        # Vary each selector/identity axis alone against one valid control.
        base = ['B511',1,1,0,3,True,1,list(range(9)),1]
        self.assertEqual(refresh(*base), (0, list(range(9))))
        for axis, alternative, expected in (
                (0,'B510',(UNKNOWN,UNKNOWN)), (1,14,(UNKNOWN,UNKNOWN)),
                (2,2,(1,[])), (3,1,(1,[])), (4,0,(1,[])),
                (5,False,(1,[])), (6,0,(1,[])),
                (7,list(range(8)),(UNKNOWN,UNKNOWN)), (8,0,(0,list(range(9))))):
            changed = base.copy(); changed[axis] = alternative
            with self.subTest(axis=axis):
                self.assertEqual(refresh(*changed), expected)
        for count in (1,2,10):
            for last in range(256):
                reply = list(range(8)) + [last, 99]
                args = base.copy(); args[6] = count; args[7] = reply
                flag, copied = refresh(*args)
                self.assertEqual(flag, last & 1)
                self.assertEqual(copied, reply[:9])
                self.assertEqual(len(copied), 9)
        for byte_index in range(8):
            args = base.copy(); reply = list(range(9)); reply[byte_index] = 255
            args[7] = reply
            self.assertEqual(refresh(*args), (0, reply))
        for prior in (0,1):
            args = base.copy(); args[5] = False; args[8] = prior
            self.assertEqual(refresh(*args), (prior, []))
        # Initialization is separately declared; no refresh is needed to clear it.
        self.assertEqual(dict((r[0], r[1]) for r in self.tables['constants'][1:])['failure_initial'], 0)

    def test_timer_without_refresh(self):
        for index, failure, argument, path, _ in self.tables['timer'][1:]:
            self.assertEqual(timer(index, failure), (argument, path))
        for retained in range(1,256):
            self.assertEqual(timer(0, retained), (120, 'failure'))
        self.assertEqual(timer(0,0), (UNKNOWN, 'capability'))
        self.assertEqual(timer(1,0), (UNKNOWN, UNKNOWN))


if __name__ == '__main__':
    unittest.main()
