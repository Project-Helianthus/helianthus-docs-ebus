"""Independent synthetic contract oracle; no decoder or physical qualification."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / 'protocols/vaillant/ebus-b523-config-mixer.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/aj10_b523_config_mixer.json'
API = ROOT / 'architecture/aj10_b523_config_mixer_api.md'


def ab99_tables(text):
    result = {}
    heading = None
    for line in text.splitlines():
        if line.startswith('## '):
            heading = line[3:]
        elif line.startswith('| ') and not line.startswith('| ---'):
            result.setdefault(heading, []).append([v.strip() for v in line.strip('|').split('|')])
    return result


class Ab99Contract(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = NATIVE.read_text()

    def test_identity_grades_and_unknowns(self):
        d = self.data
        self.assertEqual((d['family'], d['primary'], d['secondary']), ('functional-module', 0xB5, 0x23))
        self.assertEqual(d['provenance'], 'synthetic; no observed telegrams')
        self.assertEqual((d['grade'], d['qualification']), ('Hypothesis', 'Unknown'))
        self.assertIs(d['one_hot_required'], False)
        self.assertEqual(d['nibble_alternative'], 'competing nibble-code interpretation; repeated sensor associations unresolved')
        self.assertEqual(d['tables']['Unknowns'], [['Property', 'Grade']] + [[v, 'Unknown'] for v in (
            'physical adaptation', 'selected competing interpretation', 'support', 'executed movement',
            'physical qualification', 'source and destination', 'wire response offsets')])
        self.assertEqual(d['sensor_defaults'], dict(kindA=True, kindB=False, digital=False, PWM=False, reserved=0))

    def test_native_tables(self):
        self.assertEqual(ab99_tables(self.page), self.data['tables'])
        self.assertIn('(ebus-vaillant-B523.md#candidate-layouts)', self.page)
        expected = [
            ['00','smaller','request','relay-groups134/256','3/4','0 output default; 1 mixer','Hypothesis'],
            ['00','smaller','request','S1..S6','5..10','0 kindA default; 1 kindB; 2 digital; other undefined-or-ignored','Hypothesis'],
            ['00','smaller','request/positive','extent','11/4','logical only','Hypothesis'],
            ['04','larger','request','R1/R7/R8;R2/R9/R10;R3/R11/R12','3..5','0 output default; 1 mixer','Hypothesis'],
            ['04','larger','request/positive','extent','13/4','logical only','Hypothesis'],
            ['02','smaller/larger','request','circuit','3','0 first; 1 second; 2 third only larger; others ignored','Hypothesis'],
            ['02','smaller/larger','request','mode','4','0 stop/pump-off/close; 1 heating-regulation; 2 cooling-regulation; 3 pump-off/open; 4 pump-on/close; 5 pump-on/open; others ignored','Hypothesis'],
            ['02','smaller/larger','request','setpoint','5','relevant only mode 1/2; signed i8 times 0.5 Celsius; default 0; range -64..63.5; competing raw 190 means 95 Celsius with 95 clamp','Hypothesis'],
            ['02','smaller/larger','positive','feedback','3','raw retained; no new meaning','Hypothesis'],
            ['02','smaller/larger','positive','movement','4','signed i8 percent; 0 stopped; -100..-1 closing; 1..100 opening; magnitude 100 maximum; outside unresolved','Hypothesis']]
        self.assertEqual(self.data['tables']['Coordinates'], [['OP','Variant','Direction','Field','Position','Meaning','Grade']] + expected)
        self.assertEqual(self.data['tables']['Examples'], [
            ['Raw','Field','Interpretations','Grade'],
            ['BE','setpoint','-33 Celsius signed; separate 95 Celsius candidate; selection Unknown','Proven'],
            ['9C','movement','-100 closing','Proven'], ['64','movement','100 opening','Proven'],
            ['9B','movement','-101 outside named intervals','Proven'], ['65','movement','101 outside named intervals','Proven']])

    def test_sensor_flags_and_every_bit(self):
        # Independent explicit positions and shifts, including the S11/S12 boundary.
        layout = [(1,6,0),(2,6,4),(3,7,0),(4,7,4),(5,8,0),(6,8,4),
                  (7,9,0),(8,9,4),(9,10,0),(10,10,4),(11,11,0),(12,12,0),(13,12,4)]
        rows = [['OP','Variant','Direction','Sensor','Position','kindA bit','kindB bit','digital bit','PWM bit','Reserved bits','Grade']]
        cases = []
        for sensor, pos, shift in layout:
            pwm = sensor in (9,10)
            rows.append(['04','larger','request',f'S{sensor}',str(pos),str(shift),str(shift+1),str(shift+2),
                         str(shift+3) if pwm else 'none', '3..7' if sensor==11 else ('none' if pwm else '3/7'),'Hypothesis'])
            for raw in (0,1,2,3,4,8,16,32,64,128,255):
                flags = dict(zip(('kindA','kindB','digital'), [bool((raw >> shift) & mask) for mask in (1,2,4)]))
                if pwm:
                    flags['PWM'] = bool(raw & (8 << shift))
                residual = raw & (255 ^ ((15 if pwm else 7) << shift))
                cases.append([f'S{sensor}',pos,raw,flags,residual,'unresolved','Hypothesis'])
        self.assertEqual(self.data['tables']['Sensor flags'], rows)
        self.assertEqual(self.data['sensor_cases'], cases)

    def test_op00_and_relay_identity(self):
        expected=[]
        for sensor in range(1,7):
            for raw in range(256):
                expected.append([0,'smaller','request',f'S{sensor}',sensor+4,raw,
                                 ('kindA','kindB','digital')[raw] if raw<3 else 'undefined-or-ignored','Hypothesis'])
        self.assertEqual(self.data['op00_sensor_cases'], expected)
        relays=[]
        for op,variant,groups in [(0,'smaller',('134','256')),(4,'larger',('R1/R7/R8','R2/R9/R10','R3/R11/R12'))]:
            for position, group in enumerate(groups,3):
                for raw,meaning in enumerate(('output','mixer')):
                    relays.append([op,variant,'request',group,position,raw,meaning,'Hypothesis'])
        self.assertEqual(self.data['relay_cases'],relays)

    def test_circuit_variant_predicate(self):
        self.assertEqual(self.data['circuit_cases'], [[2,v,'request','circuit',3,r,
            r in ((0,1) if v=='smaller' else (0,1,2)), 'Hypothesis']
            for v in ('smaller','larger') for r in range(256)])

    def test_mode_relevance(self):
        meanings={0:'stop/pump-off/close',1:'heating-regulation',2:'cooling-regulation',
                  3:'pump-off/open',4:'pump-on/close',5:'pump-on/open'}
        self.assertEqual(self.data['mode_cases'], [[2,'request','mode',4,r,meanings.get(r,'ignored'),
            r==1 or r==2,'Hypothesis'] for r in range(256)])

    def test_setpoint_conflicts(self):
        expected=[]
        for raw in range(256):
            # Independent signed conversion via standard-library byte conversion.
            value=int.from_bytes(bytes([raw]),byteorder='big',signed=True)/2
            expected.append([2,'request','setpoint',5,raw,value,95 if raw==0xBE else 'Unknown','Unknown','Proven'])
        self.assertEqual(self.data['setpoint_cases'],expected)

    def test_movement_intervals(self):
        expected=[]
        for raw in range(256):
            value=int.from_bytes(bytes([raw]),byteorder='big',signed=True)
            state='unresolved'
            if value==0: state='stopped'
            if value in range(-100,0): state='closing'
            if value in range(1,101): state='opening'
            expected.append([2,'positive','movement',4,raw,value,state,'Proven'])
        self.assertEqual(self.data['movement_cases'],expected)

    def test_partial_preservation(self):
        self.assertEqual(self.data['partial_cases'],[{'raw':[181,35,2,0],
            'last_known_good':{'feedback_raw':17},'admitted':False,'missing':['mode','setpoint'],
            'grade':'Hypothesis','qualification':'Unknown'}])

    def test_api_document_contract(self):
        page=API.read_text()
        signatures=page.split('```go\n')[1].split('```')[0].strip().splitlines()
        self.assertEqual(signatures,['Ab99Entries() ([]Ab99Entry, error)',
                                     'Ab99Lookup(key Ab99Key) (Ab99Entry, bool, error)'])
        expected=[['Field','Type','Identity meaning']]
        for field,kind,meaning in [('Family','string','family'),('Variant','string','variant'),
            ('Primary','*uint8','primary'),('Secondary','*uint8','secondary'),('Operation','*uint8','operation'),
            ('Direction','string','direction'),('Field','string','field'),('Group','*uint8','B524 group'),
            ('RequestedInstance','*uint8','B524 requested instance'),('Register','*uint16','B524 register'),
            ('CommandRole','string','B524 command role')]:
            expected.append(['Ab99'+field,kind,meaning])
        self.assertEqual(ab99_tables(page),{'Key axes':expected})
        for clause in ('nil is absent','explicit zero','independently owned nested data',
            'copy slices, maps, nested collections, raw bytes and key pointers recursively',
            'false and nil error','nil entries and an error','false\nand an error',
            'Validate embedded data before admitting any result','Ab99Grade','Ab99Raw','Ab99Unknown',
            'Ab99Qualification','Nothing is\nstable before 1.0','MCP compatibility and GraphQL parity'):
            self.assertIn(clause,page)


if __name__ == '__main__':
    unittest.main()
