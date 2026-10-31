"""Synthetic representation checks and an offline probe of the merged registry."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-b512-feedback-fallback.md'
DATA = ROOT / 'protocols/vaillant/fixtures/ak08_b512_feedback_fallback.json'
API = ROOT / 'architecture/ak08_b512_feedback_fallback_api.md'
FIELDS = ('secondary-heating-pump', 'circulation-pump', 'solar-pump',
          'error-relay', 'loading-pump', 'fume-flap')
BASES = {'request': ['21', '22', '23', '24', '25', '26'],
         'positive': ['31', '32', '33', '34', '35', '36']}
AXES = ('family', 'variant', 'primary', 'secondary', 'operation', 'direction',
        'field', 'alternative', 'group', 'instance_scope', 'register')
KEY_FIELDS = ('Ab18Family', 'Ab18Variant', 'Ab18Primary', 'Ab18Secondary',
              'Ab18Operation', 'Ab18Direction', 'Ab18Field', 'Ab18Alternative',
              'Ab18Group', 'Ab18InstanceScope', 'Ab18Register')
TYPES = ('string', 'string', 'uint8', '*uint8', '*uint8', 'string', 'string',
         'string', '*uint8', 'string', '*uint16')
FEEDBACK = dict(actual_signal_absent='setpoint-fallback',
                actual_signal_present='actual-signal',
                equal_to_setpoint_establishes_actual=False,
                wire_discriminator='Unknown', physical_value='Unknown')
DEFAULTS = dict(boolean_default=True, raw_default=None, raw_default_encoding='Unknown')
QUALIFICATION = dict(native_support='Unknown', physical_effects='Unknown',
                     persistence='Unknown', delivery='Unknown')


def expected_entries():
    rows = []
    for side in ('request', 'positive'):
        for index, field in enumerate(FIELDS):
            values = ({'0F': 'state-0F', 'F0': 'state-F0'} if index in (3, 5)
                      else {'FF': {'request': 'leave-unchanged',
                                   'positive': 'function-unavailable'}[side]})
            rows.append(dict(field=field, logical_position=index + 3, direction=side,
                             type='u8', grade='Hypothesis', physical_offset='Unknown',
                             values=values, other_values='no-action' if index in (3, 5)
                             else 'retain-raw', polarity='Unknown',
                             raw_retention='preserve each independent raw token'))
    return rows


def expected_cases():
    independent, pumps, states, feedback = [], [], [], []
    for side, baseline in BASES.items():
        for index, field in enumerate(FIELDS):
            changed = baseline.copy()
            changed[index] = ('71', '72', '73', '74', '75', '76')[index]
            independent.append(dict(field=field, direction=side, before=baseline, raw=changed))
            if index in (0, 1, 2, 4):
                raw = baseline.copy()
                raw[index] = 'FF'
                pumps.append(dict(field=field, direction=side, previous=baseline,
                                  raw=raw, retained=baseline if side == 'request' else raw,
                                  meaning='leave-unchanged' if side == 'request'
                                  else 'function-unavailable'))
            else:
                for token, meaning in (('0F', 'state-0F'), ('F0', 'state-F0'),
                                       ('00', 'no-action'), ('01', 'no-action'),
                                       ('FF', 'no-action')):
                    raw = baseline.copy()
                    raw[index] = token
                    states.append(dict(field=field, direction=side, previous=baseline,
                                       raw=raw, retained=baseline if meaning == 'no-action'
                                       else raw, meaning=meaning))
    for index, field in enumerate(FIELDS):
        setpoint = BASES['request'][index]
        distinct = BASES['positive'][index]
        for present, actual, token, source in (
                (False, None, setpoint, 'setpoint-fallback'),
                (True, setpoint, setpoint, 'actual-signal'),
                (True, distinct, distinct, 'actual-signal')):
            feedback.append(dict(field=field, setpoint=setpoint,
                                 actual_signal_present=present, actual_token=actual,
                                 feedback_token=token, source=source, physical_value='Unknown'))
    return dict(independent_fields=independent, pump_ff=pumps,
                declared_states=states, feedback=feedback)


def expected_production():
    rows = []
    for entry in expected_entries():
        row = dict(entry)
        side, field = row.pop('direction'), row.pop('field')
        retention = row.pop('raw_retention')
        row.update(id='ab18-' + side + '-' + field,
                   key=dict(zip(AXES, ('B512', 'OP01', 181, 18, 1, side, field,
                                      'none', None, 'none', None))),
                   raw_form=dict(type='u8', retention=retention),
                   raw_fallback='retain raw token and candidate meaning independently',
                   feedback=FEEDBACK, **DEFAULTS, **QUALIFICATION)
        rows.append(row)
    return rows


def tables(text):
    groups = []
    for block in text.split('\n\n'):
        lines = block.splitlines()
        if lines and all(line.startswith('|') for line in lines):
            rows = [[cell.strip() for cell in line.strip('|').split('|')] for line in lines]
            groups.append((rows[0], rows[2:]))
    return groups


class NativeContract(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(DATA.read_text())
        self.page = PAGE.read_text()
        self.api = API.read_text()

    def test_finite_fixture_independent_oracle(self):
        self.assertEqual(self.data, dict(
            service='B512', operation='01', family='Vaillant B512 family',
            provenance='synthetic', grade='Hypothesis', entries=expected_entries(),
            feedback=FEEDBACK, defaults=DEFAULTS, qualification=QUALIFICATION,
            cases=expected_cases()))
        self.assertIs(self.data['defaults']['boolean_default'], True)
        self.assertIs(self.data['defaults']['raw_default'], None)
        self.assertIs(self.data['feedback']['equal_to_setpoint_establishes_actual'], False)

    def test_native_tables_independent_oracle(self):
        parsed = tables(self.page)
        self.assertEqual(len(parsed), 4)
        self.assertEqual(parsed[0], (
            ['Logical position', 'Field', 'Type', 'Request grade', 'Positive grade', 'Physical offset'],
            [[str(i + 3), field, 'u8', 'Hypothesis', 'Hypothesis', 'Unknown']
             for i, field in enumerate(FIELDS)]))
        pumps = 'secondary-heating-pump, circulation-pump, solar-pump, loading-pump'
        relay = 'error-relay, fume-flap'
        self.assertEqual(parsed[1], (
            ['Fields', 'Side', 'Raw token', 'Candidate meaning', 'Grade'],
            [[pumps, 'request', 'FF', 'leave-unchanged', 'Hypothesis'],
             [pumps, 'positive', 'FF', 'function-unavailable', 'Hypothesis'],
             [relay, 'request and positive', '0F', 'state-0F', 'Hypothesis'],
             [relay, 'request and positive', 'F0', 'state-F0', 'Hypothesis'],
             [relay, 'request and positive', 'other', 'no-action', 'Hypothesis']]))
        self.assertEqual(parsed[2], (
            ['Internal actual signal', 'Feedback source', 'Physical value', 'Wire discriminator', 'Grade'],
            [['absent', 'setpoint-fallback', 'Unknown', 'Unknown', 'Hypothesis'],
             ['present', 'actual-signal', 'Unknown', 'Unknown', 'Hypothesis']]))
        self.assertEqual(parsed[3], (['Metadata', 'Value', 'Grade'], [
            ['Boolean default', 'true', 'Hypothesis'],
            ['Materialized raw default', 'absent', 'Unknown'],
            ['Raw default encoding', 'Unknown', 'Unknown'],
            ['Relay and fume-flap polarity', 'Unknown', 'Unknown'],
            *[[label, 'Unknown', 'Unknown'] for label in
              ('Native support', 'Physical effects', 'Persistence', 'Delivery')]]))
        prose = ' '.join(self.page.split())
        for phrase in ('Logical positions are not physical offsets',
                       'Feedback equal to setpoint is not sufficient to classify it as actual',
                       'raw 01 cannot be inferred', 'OP00, OP02, OP04/05 and OP07',
                       'not complete telegrams', 'representation only',
                       '**Proven (synthetic representation only):**', '**Unknown:**'):
            self.assertIn(phrase, prose)

    def test_independent_fields_and_token_meanings(self):
        rows = {(r['direction'], r['field']): r for r in self.data['entries']}
        for case in expected_cases()['independent_fields']:
            with self.subTest(direction=case['direction'], field=case['field']):
                row = rows[case['direction'], case['field']]
                selected = row['logical_position'] - 3
                changed = [i for i, (a, b) in enumerate(zip(case['before'], case['raw'])) if a != b]
                self.assertEqual(changed, [selected])
        for group in ('pump_ff', 'declared_states'):
            for case in expected_cases()[group]:
                with self.subTest(group=group, side=case['direction'], field=case['field'], raw=case['raw']):
                    row = rows[case['direction'], case['field']]
                    selected = row['logical_position'] - 3
                    token = case['raw'][selected]
                    meaning = row['values'].get(token, row['other_values'])
                    retained = case['raw'].copy()
                    if meaning in ('leave-unchanged', 'no-action'):
                        retained[selected] = case['previous'][selected]
                    self.assertEqual(meaning, case['meaning'])
                    self.assertEqual(retained, case['retained'])
                    self.assertEqual(row['grade'], 'Hypothesis')
                    self.assertEqual(row['polarity'], 'Unknown')

    def test_feedback_source_not_value_equality(self):
        for case in expected_cases()['feedback']:
            with self.subTest(field=case['field'], present=case['actual_signal_present'], token=case['feedback_token']):
                present = case['actual_signal_present']
                token = case['actual_token'] if present else case['setpoint']
                source = self.data['feedback']['actual_signal_present' if present else 'actual_signal_absent']
                self.assertEqual((token, source), (case['feedback_token'], case['source']))
                self.assertIs(self.data['feedback']['equal_to_setpoint_establishes_actual'], False)
                self.assertEqual(self.data['feedback']['physical_value'], 'Unknown')
                self.assertEqual(self.data['feedback']['wire_discriminator'], 'Unknown')

    def test_api_document_exact_contract(self):
        self.assertEqual(re.findall(r'^func .*$', self.api, re.M), [
            'func Ab18Entries() (json.RawMessage, error)',
            'func Ab18Lookup(Ab18Key) (json.RawMessage, bool, error)'])
        parsed = tables(self.api)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0], (
            ['Ab18Key field', 'Go type', 'JSON axis', 'Finite value'],
            [list(row) for row in zip(KEY_FIELDS, TYPES, AXES, (
                'B512', 'OP01', '181', '18', '1', 'request or positive',
                'one of the six native fields', 'none', 'absent', 'none', 'absent'))]))
        prose = ' '.join(self.api.split())
        for phrase in ('**Proven (local API contract):**', 'returns a JSON array',
                       'exactly one whole row', 'missing exact key returns no row',
                       'Invalid embedded JSON or duplicate keys produce an error',
                       'entire array before any matching row', 'No wildcard or nearest-key',
                       'All eleven axes match independently', 'Optional absent and explicit zero differ',
                       'No cross-family, variant, direction, field or alternative fallback',
                       'independent deep byte copy', 'Mutating one result cannot affect',
                       'raw_fallback', 'raw_form', 'candidate grade `Hypothesis`',
                       'raw_default null', 'raw_default_encoding Unknown',
                       'Wire discriminator and physical value remain Unknown',
                       'partial last-known-good state', 'fails closed',
                       'MCP compatibility and GraphQL parity remain unchanged',
                       'AK07 precedes this page', 'no dependency from the registry back',
                       'Nothing is stable before Helianthus 1.0'):
            self.assertIn(phrase, prose)

    def test_polarity_relationship_to_main_reference(self):
        text = ' '.join(PAGE.read_text().split())
        self.assertIn('kept there as an alternative candidate', text)
        self.assertIn('This supplement does not adopt it', text)
        self.assertIn('state-0F and state-F0 as distinct declared states with Unknown polarity', text)

    def test_native_boundary_and_local_links(self):
        native = PAGE.read_text() + DATA.read_text()
        self.assertNotRegex(native, r'\b(?:Ab18\w*|GraphQL|MCP|Helianthus|gateway|json.RawMessage)\b')
        for page in (PAGE, API):
            for target in re.findall(r'\]\(([^)]+)\)', page.read_text()):
                if ':' not in target:
                    self.assertTrue((page.parent / target).is_file(), target)
        for path in (PAGE, DATA, API, Path(__file__)):
            self.assertNotRegex(path.read_text(), r'(?<![\w])[a-f0-9]{40,64}(?![\w])')


GO_PROBE = r'''
package vaillant
import (
 "bytes"
 "encoding/json"
 "os"
 "reflect"
 "testing"
)
var axes = []string{"family","variant","primary","secondary","operation","direction","field","alternative","group","instance_scope","register"}
func rows(t *testing.T) ([]json.RawMessage, []Ab18Key) {
 t.Helper()
 var entries func() (json.RawMessage,error) = Ab18Entries
 var lookup func(Ab18Key) (json.RawMessage,bool,error) = Ab18Lookup
 _ = lookup
 b,e:=entries(); if e!=nil {t.Fatal(e)}
 var r []json.RawMessage; if e=json.Unmarshal(b,&r); e!=nil {t.Fatal(e)}
 var k []Ab18Key
 for _,v:=range r { var x struct{Key Ab18Key `json:"key"`}; if e=json.Unmarshal(v,&x); e!=nil {t.Fatal(e)}; k=append(k,x.Key) }
 return r,k
}
func same(t *testing.T, a,b []byte) {
 t.Helper(); var x,y any
 if e:=json.Unmarshal(a,&x);e!=nil {t.Fatal(e)}
 if e:=json.Unmarshal(b,&y);e!=nil {t.Fatal(e)}
 if !reflect.DeepEqual(x,y) {t.Fatalf("whole row mismatch: %s != %s",a,b)}
}
func TestAK08FiniteRows(t *testing.T) {
 b,e:=Ab18Entries();if e!=nil {t.Fatal(e)}
 expected,e:=os.ReadFile("expected.json");if e!=nil {t.Fatal(e)};same(t,b,expected)
 r,k:=rows(t);if len(r)!=12 {t.Fatal("finite rows",len(r))}
 for i,key:=range k {out,found,e:=Ab18Lookup(key);if e!=nil||!found {t.Fatal("exact hit",e)};same(t,out,r[i])}
}
func pair(t *testing.T, raw json.RawMessage, a,b Ab18Key) {
 t.Helper(); var obj map[string]json.RawMessage
 if e:=json.Unmarshal(raw,&obj);e!=nil {t.Fatal(e)}
 var rr []json.RawMessage
 for _,key:=range []Ab18Key{a,b} {obj["key"],_=json.Marshal(key);out,e:=json.Marshal(obj);if e!=nil {t.Fatal(e)};rr=append(rr,out)}
 fixture,e:=json.Marshal(rr);if e!=nil {t.Fatal(e)}
 for i,key:=range []Ab18Key{a,b} {out,found,e:=ab18Lookup(fixture,key);if e!=nil||!found {t.Fatal("valid control",e)};same(t,out,rr[i])}
}
func TestAK08EveryAxis(t *testing.T) {
 r,k:=rows(t)
 typ:=reflect.TypeOf(Ab18Key{})
 names:=[]string{"Ab18Family","Ab18Variant","Ab18Primary","Ab18Secondary","Ab18Operation","Ab18Direction","Ab18Field","Ab18Alternative","Ab18Group","Ab18InstanceScope","Ab18Register"}
 types:=[]string{"string","string","uint8","*uint8","*uint8","string","string","string","*uint8","string","*uint16"}
 if typ.NumField()!=11 {t.Fatal("key width")}
 for axis,name:=range names {t.Run(name,func(t *testing.T){
  if typ.Field(axis).Name!=name||typ.Field(axis).Type.String()!=types[axis]||typ.Field(axis).Tag.Get("json")!=axes[axis] {t.Fatal("key shape")}
  key:=k[0];v:=reflect.ValueOf(&key).Elem().Field(axis)
  switch v.Kind() {case reflect.String:v.SetString("other-"+v.String());case reflect.Uint8:v.SetUint(v.Uint()+1);case reflect.Ptr:p:=reflect.New(v.Type().Elem());if !v.IsNil(){p.Elem().SetUint(v.Elem().Uint()+1)};v.Set(p);default:t.Fatal("type")}
  if out,found,e:=Ab18Lookup(key);e!=nil||found||out!=nil {t.Fatal("exact miss",e)}
  pair(t,r[0],k[0],key)
 })}
 for _,axis:=range []int{3,4,8,10} {t.Run(names[axis]+"-absent-zero",func(t *testing.T){
  absent,zero:=k[0],k[0]
  reflect.ValueOf(&absent).Elem().Field(axis).SetZero()
  v:=reflect.ValueOf(&zero).Elem().Field(axis);v.Set(reflect.New(v.Type().Elem()))
  pair(t,r[0],absent,zero)
 })}
}
func TestAK08Errors(t *testing.T) {
 r,k:=rows(t)
 dup,_:=json.Marshal([]json.RawMessage{r[0],r[0]})
 inputs:=[][]byte{[]byte("["),[]byte("{}"),[]byte("null"),[]byte("[null]"),[]byte("[{}]"),dup}
 for _,axis:=range axes {var obj map[string]json.RawMessage;json.Unmarshal(r[0],&obj);var key map[string]any;json.Unmarshal(obj["key"],&key);delete(key,axis);obj["key"],_=json.Marshal(key);bad,_:=json.Marshal(obj);poisoned,_:=json.Marshal([]json.RawMessage{r[0],bad});inputs=append(inputs,poisoned)}
 for _,b:=range inputs {
  if _,e:=ab18Validate(b);e==nil {t.Fatalf("accepted invalid %s",b)}
  if out,found,e:=ab18Lookup(b,k[0]);e==nil||found||out!=nil {t.Fatal("fail closed")}
 }
 saved:=ab18Data;defer func(){ab18Data=saved}()
 for _,b:=range inputs {ab18Data=string(b)
  if out,e:=Ab18Entries();e==nil||out!=nil {t.Fatal("entries error")}
  if out,found,e:=Ab18Lookup(k[0]);e==nil||found||out!=nil {t.Fatal("public lookup error")}
 }
}
func TestAK08Copies(t *testing.T) {
 r,k:=rows(t);a,e:=Ab18Entries();if e!=nil {t.Fatal(e)};expected:=bytes.Clone(a)
 b,e:=Ab18Entries();if e!=nil {t.Fatal(e)};for i:=range a {a[i]='x'}
 c,e:=Ab18Entries();if e!=nil||!bytes.Equal(b,expected)||!bytes.Equal(c,expected) {t.Fatal("entries alias")}
 for i,key:=range k {a,found,e:=Ab18Lookup(key);if e!=nil||!found {t.Fatal(e)};b,found,e:=Ab18Lookup(key);if e!=nil||!found {t.Fatal(e)}
 for j:=range a {a[j]='x'};c,found,e:=Ab18Lookup(key);if e!=nil||!found||!bytes.Equal(b,r[i])||!bytes.Equal(c,r[i]) {t.Fatal("row alias")}}
 d,e:=Ab18Entries();if e!=nil||!bytes.Equal(d,expected) {t.Fatal("cross-call alias")}
}
'''


class RegistryContract(unittest.TestCase):
    def test_merged_production_contract_offline(self):
        # Unchanged merged AK07 source/data, cited in the API companion.
        # An explicit override probes provisioned production files instead.
        configured = os.environ.get(
            'AK08_AB18_ROOT', str(ROOT / 'tests/fixtures/ak08_ab18_registry'))
        self.assertTrue(configured, 'AK08_AB18_ROOT must identify a read-only vaillant directory')
        source = Path(configured)
        self.assertTrue(source.is_dir(), f'registry source directory missing: {source}')
        go = shutil.which('go')
        self.assertIsNotNone(go, 'cached Go toolchain required; no installation permitted')
        temp_root = ROOT / '.tmp'
        temp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='ak08-probe-', dir=temp_root) as name:
            target = Path(name)
            (target / 'data').mkdir()
            for relative in ('ab18_b512_feedback_fallback.go', 'data/ab18_b512_feedback_fallback.json'):
                self.assertTrue((source / relative).is_file(), relative)
                shutil.copyfile(source / relative, target / relative)
            (target / 'ak08_test.go').write_text(GO_PROBE)
            (target / 'expected.json').write_text(json.dumps(expected_production()))
            env = dict(os.environ, GO111MODULE='off', GOPROXY='off', GOSUMDB='off',
                       GOTOOLCHAIN='local', GOWORK='off')
            result = subprocess.run([go, 'test', '-v', '-count=1', '-timeout=30s', '.'],
                                    cwd=target, env=env, capture_output=True, text=True, timeout=55)
            print(result.stdout, end='')
            print(result.stderr, end='')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(len(re.findall(r'^--- PASS: TestAK08', result.stdout, re.M)), 4,
                             'four nonzero production tests required')
            self.assertEqual(len(re.findall(r'    --- PASS: TestAK08EveryAxis/', result.stdout)), 15,
                             'eleven axes and four absent/zero controls required')


if __name__ == '__main__':
    unittest.main(verbosity=2)
