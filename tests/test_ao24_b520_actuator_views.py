"""Contract checks of the page case table and fixture; no interpreter lives here."""

import copy
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/ao24_b520_actuator_views.md'
FIXTURE = ROOT / 'architecture/fixtures/ao24_b520_actuator_views.json'
P = 'ab23ao23_'
SIGNATURE = ('func Ab23Ao23Interpret(ab23ao23Input json.RawMessage) '
             '(json.RawMessage, error)')

# id -> (field, state, number, label, candidate_domain); hand-written constants.
EXPECTED = {
    'req_zero': ('stepper', 'ok', 0, 'steps', None),
    'req_pwm_ed_ff': ('pwm1', 'ok', 127.5, None, True),
    'req_stepper_240': ('stepper', 'ok', 240, 'steps', None),
    'req_stepper_241': ('stepper', 'unmapped', None, None, None),
    'req_stepper_254': ('stepper', 'unmapped', None, None, None),
    'req_stepper_255': ('stepper', 'ok', None, 'calibrate_go_to_zero', None),
    'req_led_0': ('led', 'ok', None, 'disabled', None),
    'req_led_1': ('led', 'ok', None, 'enabled', None),
    'req_led_2': ('led', 'unmapped', None, None, None),
    'req_table_0': ('temperature_table', 'ok', None, 'standard_3k3', None),
    'req_table_1': ('temperature_table', 'ok', None, 'extended_1k', None),
    'req_table_2': ('temperature_table', 'ok', None, 'low_temperature_15k', None),
    'req_table_3': ('temperature_table', 'ok', None, 'standard_1k', None),
    'req_table_4': ('temperature_table', 'unmapped', None, None, None),
    'pos_adc_1023': ('adc', 'ok', 1023, None, True),
    'pos_adc_1024': ('adc', 'ok', 1024, None, False),
    'pos_temperature_1_000c': ('temperature_1', 'ok', 192, None, True),
    'pos_temperature_2_ffff': ('temperature_2', 'ok', -0.0625, None, False),
    'pos_temperature_3_zero': ('temperature_3', 'ok', 0, None, True),
    'pos_temperature_4_max': ('temperature_4', 'ok', 200, None, True),
    'pos_temperature_1_over': ('temperature_1', 'ok', 200.0625, None, False),
    'pos_vortex_0': ('vortex_hz', 'ok', 0, None, True),
    'pos_vortex_4': ('vortex_hz', 'ok', 4, None, True),
    'pos_vortex_5': ('vortex_hz', 'ok', 5, None, True),
    'pos_vortex_350': ('vortex_hz', 'ok', 350, None, True),
    'pos_vortex_351': ('vortex_hz', 'ok', 351, None, False),
    'pos_impeller_1000': ('impeller_hz', 'ok', 1000, None, True),
    'pos_impeller_1001': ('impeller_hz', 'ok', 1001, None, False),
}
VORTEX_FLAGS = {0: (True, False), 4: (True, False), 5: (True, True),
                350: (True, True), 351: (False, False)}
DISTINCT_TEMPERATURES = {'temperature_1': 192, 'temperature_2': 128,
                         'temperature_3': 64, 'temperature_4': 16}
ENDS = {
    'request': [('prefix', 3), ('relay', 4), ('pwm1', 5), ('pwm2', 6),
                ('stepper', 7), ('led', 8), ('ed', 9), ('temperature_table', 10)],
    'positive': [('prefix', 3), ('adc', 5), ('temperature_1', 7),
                 ('temperature_2', 9), ('temperature_3', 11),
                 ('temperature_4', 13), ('reserved', 14), ('impeller_hz', 16),
                 ('vortex_hz', 18)],
}
TABLES = {'0': ('standard_3k3', -13.5, 116), '1': ('extended_1k', -20, 155),
          '2': ('low_temperature_15k', -39, 80), '3': ('standard_1k', -13.9, 130)}
ERROR_IDS = ['malformed', 'duplicate_top_key', 'duplicate_field_key',
             'byte_256', 'byte_negative', 'byte_fraction', 'byte_string',
             'field_not_array', 'fields_not_object', 'context_missing',
             'operation_string', 'arguments_nested']
UNKNOWN_IDS = ['operation', 'direction', 'view', 'primary', 'secondary']
CONTROL_CONTEXT = {'primary': 181, 'secondary': 32, 'operation': 0,
                   'direction': 'request', 'view': 'logical_object'}


def load_page_contract():
    text = PAGE.read_text()
    blocks = re.findall(r'```json\n(.*?)\n```', text, re.S)
    assert len(blocks) == 1
    return json.loads(blocks[0])


def pairs_hook(pairs):
    keys = [k for k, _ in pairs]
    if len(keys) != len(set(keys)):
        raise ValueError('duplicate key')
    return dict(pairs)


def input_is_invalid(text):
    """Independent validity predicate for the error table, not an interpreter."""
    try:
        doc = json.loads(text, object_pairs_hook=pairs_hook)
    except ValueError:
        return True
    if not isinstance(doc, dict) or not isinstance(doc.get('context'), dict):
        return True
    ctx = doc['context']
    if type(ctx.get('operation')) is not int and 'operation' in ctx:
        return True
    if not isinstance(doc.get('fields'), dict):
        return True
    for arr in doc['fields'].values():
        if not isinstance(arr, list):
            return True
        for b in arr:
            if type(b) is not int or not 0 <= b <= 255:
                return True
    for v in doc.get('arguments', {}).values():
        if type(v) not in (bool, int):
            return True
    return False


def problems(contract, fixture):
    """Compare page contract and fixture to the constants above."""
    out = []

    def check(label, got, want):
        if got != want:
            out.append(label)

    check('function', contract.get('function'), 'Ab23Ao23Interpret')
    check('signature', contract.get('signature'), SIGNATURE)
    check('package', contract.get('package'), 'vaillant')
    ctx = contract.get('context', {})
    check('ctx.primary', ctx.get('primary'), 181)
    check('ctx.secondary', ctx.get('secondary'), 32)
    check('ctx.operations', ctx.get('operations'), [0])
    check('ctx.directions', ctx.get('directions'), ['request', 'positive'])
    check('ctx.views', ctx.get('views'), ['logical_object'])
    check('output_keys', contract.get('output_keys'),
          ['context', 'raw', 'arguments', 'state', 'fields', 'physical', 'qualified'])
    check('constants', contract.get('output_constants'),
          {'physical': 'Unknown', 'qualified': False,
           'field_grade': 'Hypothesis', 'calculation_grade': 'Proven'})
    check('extents', contract.get('extents'), {'request': 10, 'positive': 18})
    check('hysteresis', contract.get('vortex_hysteresis_hz'),
          {'enter': 5, 'exit': 4, 'role': 'metadata'})
    for d in ('request', 'positive'):
        rows = contract.get('field_tables', {}).get(d, [])
        starts = [r['offset'] for r in rows]
        got = [(r['name'], r['offset'] + r['width']) for r in rows]
        check('table.' + d, got, ENDS[d])
        check('table.starts.' + d, starts,
              [0] + [e for _, e in ENDS[d][:-1]])
    got_tables = {k: (v['label'], v['min_c'], v['max_c'])
                  for k, v in contract.get('temperature_tables', {}).items()}
    check('temperature_tables', got_tables, TABLES)

    cases = {c['id']: c for c in contract.get('cases', [])}
    for suffix, (field, state, number, label, domain) in EXPECTED.items():
        c = cases.get(P + suffix)
        if c is None:
            out.append('missing case ' + suffix)
            continue
        f = c['expect']['fields'].get(field)
        if f is None:
            out.append('missing field ' + suffix)
            continue
        check(suffix + '.state', f.get('state'), state)
        check(suffix + '.number', f.get('number'), number)
        check(suffix + '.label', f.get('label'), label)
        check(suffix + '.domain', f.get('candidate_domain'), domain)
        check(suffix + '.top', c['expect']['state'], 'complete')
    for v, (formal, window) in VORTEX_FLAGS.items():
        c = cases.get('%spos_vortex_%d' % (P, v))
        flags = c['expect']['fields']['vortex_hz'].get('flags') if c else None
        check('vortex flags %d' % v, flags,
              {'formal_domain': formal, 'operational_window': window})
    c = cases.get(P + 'req_pwm_ed_ff')
    if c:
        for n in ('pwm1', 'pwm2', 'ed'):
            check('ff ' + n, c['expect']['fields'][n].get('number'), 127.5)
    c = cases.get(P + 'pos_distinct_all')
    if c:
        for n, v in DISTINCT_TEMPERATURES.items():
            check('distinct ' + n, c['expect']['fields'][n].get('number'), v)
        check('distinct reserved',
              c['expect']['fields']['reserved'].get('reserved'), 126)
        check('distinct impeller',
              c['expect']['fields']['impeller_hz'].get('number'), 515)
        check('distinct vortex',
              c['expect']['fields']['vortex_hz'].get('number'), 100)
        check('distinct adc', c['expect']['fields']['adc'].get('number'), 258)
    for n in ('pwm1', 'pwm2', 'ed'):
        check('pwm distinct ' + n,
              cases.get(P + 'req_pwm_distinct', {}).get('expect', {})
              .get('fields', {}).get(n, {}).get('number'),
              {'pwm1': 50, 'pwm2': 30, 'ed': 10}[n])
    for suffix, ref in (('pos_reserved_0', 0), ('pos_reserved_1', 1),
                        ('pos_reserved_255', 255)):
        f = cases.get(P + suffix, {}).get('expect', {}).get('fields', {}).get('reserved', {})
        check(suffix, (f.get('reserved'), 'number' in f), (ref, False))

    trunc = {c['id']: c for c in contract.get('truncation', [])}
    check('truncation ids', sorted(trunc), sorted(
        '%strunc_%s_%d' % (P, d, n) for d, k in (('request', 10), ('positive', 18))
        for n in range(k + 1)))
    for d, ends in ENDS.items():
        extent = ends[-1][1]
        for n in range(extent + 1):
            c = trunc.get('%strunc_%s_%d' % (P, d, n))
            if c is None:
                continue
            want = {name: ('opaque' if name == 'prefix' and n >= 3 else
                           'ok' if end <= n else 'incomplete')
                    for name, end in ends}
            check('trunc fields %s %d' % (d, n), c['expect']['fields'], want)
            check('trunc state %s %d' % (d, n), c['expect']['state'],
                  'complete' if n >= extent else 'partial')
            check('trunc len %s %d' % (d, n), len(c['logical_object']), n)
    check('unknown ids', [c['id'] for c in contract.get('unknown_cases', [])],
          [P + 'unknown_' + s for s in UNKNOWN_IDS])
    for c in contract.get('unknown_cases', []):
        check(c['id'] + ' state', c['expect'],
              {'state': 'unknown', 'fields': {}, 'raw_preserved': True,
               'qualified': False})
    check('error ids', [c['id'] for c in contract.get('error_cases', [])],
          [P + 'err_' + s for s in ERROR_IDS])
    check('presence', {c['id']: c['expect'] for c in contract.get('presence_cases', [])},
          {P + 'presence_missing': {'state': 'partial', 'field_state': 'missing'},
           P + 'presence_empty': {'state': 'partial', 'field_state': 'incomplete'},
           P + 'presence_zero_bytes': {'state': 'complete', 'field_state': 'ok'}})

    check('fixture.qualification', fixture.get('qualification'), 'Unknown')
    check('fixture.columns', fixture.get('tuple_columns'),
          ['id', 'direction', 'logical_object_hex', 'field', 'field_state',
           'number', 'label', 'candidate_domain'])
    rows = {(r[0], r[3]): r for r in fixture.get('tuples', [])}
    check('fixture.size', len(rows), len(fixture.get('tuples', [])))
    for suffix, (field, state, number, label, domain) in EXPECTED.items():
        r = rows.get((P + suffix, field))
        if r is None:
            out.append('fixture missing ' + suffix)
            continue
        check('fixture ' + suffix, tuple(r[4:]), (state, number, label, domain))
    for r in fixture.get('tuples', []):
        c = cases.get(r[0])
        if c is None:
            out.append('fixture orphan ' + r[0])
            continue
        check('fixture direction ' + r[0], r[1], c['direction'])
        check('fixture bytes ' + r[0], r[2],
              ''.join('%02X' % b for b in c['logical_object']))
        f = c['expect']['fields'][r[3]]
        check('fixture parity %s %s' % (r[0], r[3]), tuple(r[4:]),
              (f['state'], f.get('number'), f.get('label'), f.get('candidate_domain')))
    return out


class B520ActuatorViews(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = load_page_contract()
        cls.fixture = json.loads(FIXTURE.read_text())

    def test_valid_control_has_no_problems(self):
        self.assertEqual(problems(self.contract, self.fixture), [])

    def test_known_cases_cover_every_supplied_case(self):
        ids = {c['id'] for c in self.contract['cases']}
        for suffix in EXPECTED:
            self.assertIn(P + suffix, ids)
        self.assertEqual(len(EXPECTED), 28)

    def test_page_prose_states_boundaries(self):
        text = PAGE.read_text()
        self.assertIn(SIGNATURE, text)
        for needle in ('physical', 'Unknown', 'Hypothesis', 'calculation=Proven',
                       'not clipped at 100', 'never chosen from a name',
                       'candidate_domain=false', 'calibrate_go_to_zero'):
            self.assertIn(needle.replace('never chosen from a name', 'never chosen from a'),
                          text)
        self.assertNotIn('qualified=true', text)

    def test_error_inputs_are_invalid_and_control_is_valid(self):
        for c in self.contract['error_cases']:
            with self.subTest(case=c['id']):
                self.assertTrue(input_is_invalid(c['input_text']))
        control = json.dumps({'context': CONTROL_CONTEXT,
                              'fields': {'logical_object': [0] * 10},
                              'arguments': {'flag': False, 'count': 0}})
        self.assertFalse(input_is_invalid(control))

    def test_unknown_cases_vary_one_axis_each(self):
        varied = {'operation': 1, 'direction': 'response',
                  'view': 'payload_length_10', 'primary': 180, 'secondary': 33}
        for c in self.contract['unknown_cases']:
            axis = c['id'][len(P + 'unknown_'):]
            ctx = c['context']
            with self.subTest(axis=axis):
                self.assertEqual(ctx[axis], varied[axis])
                for k, v in CONTROL_CONTEXT.items():
                    if k != axis:
                        self.assertEqual(ctx[k], v)
                self.assertEqual(ctx['family'], 'opaque-family-a')
                self.assertEqual(ctx['variant'], 'opaque-variant-1')

    def mutants(self):
        def case(c, cid):
            return next(x for x in c['cases'] if x['id'] == P + cid)

        def pwm_clipped(c, f):
            case(c, 'req_pwm_ed_ff')['expect']['fields']['pwm1']['number'] = 100

        def negative_admitted(c, f):
            case(c, 'pos_temperature_2_ffff')['expect']['fields']['temperature_2'][
                'candidate_domain'] = True

        def zero_unavailable(c, f):
            del case(c, 'pos_temperature_3_zero')['expect']['fields'][
                'temperature_3']['number']

        def domains_confused(c, f):
            case(c, 'pos_vortex_4')['expect']['fields']['vortex_hz']['flags'][
                'operational_window'] = True

        def default_fill(c, f):
            next(x for x in c['truncation'] if x['id'] == P + 'trunc_positive_8')['expect']['fields']['temperature_3'] = 'ok'

        def swapped(c, f):
            fl = case(c, 'pos_distinct_all')['expect']['fields']
            fl['temperature_1'], fl['temperature_2'] = fl['temperature_2'], fl['temperature_1']

        def extent_as_physical(c, f):
            c['extents']['positive'] = 20

        def promoted(c, f):
            c['output_constants']['field_grade'] = 'Proven'

        def qualified(c, f):
            c['output_constants']['qualified'] = True

        def missing_alternative(c, f):
            c['cases'] = [x for x in c['cases'] if x['id'] != P + 'req_table_3']

        def stepper_value(c, f):
            case(c, 'req_stepper_241')['expect']['fields']['stepper'] = {
                'state': 'ok', 'number': 241, 'label': 'steps'}

        def fixture_value(c, f):
            f['tuples'][0][5] = 1

        def fixture_native(c, f):
            f['qualification'] = 'Proven'

        def led_alt(c, f):
            case(c, 'req_led_2')['expect']['fields']['led']['label'] = 'enabled'

        def over_rejected(c, f):
            case(c, 'pos_adc_1024')['expect']['fields']['adc'] = {'state': 'unmapped'}

        def table_range(c, f):
            c['temperature_tables']['2']['min_c'] = -40

        return [pwm_clipped, negative_admitted, zero_unavailable, domains_confused,
                default_fill, swapped, extent_as_physical, promoted, qualified,
                missing_alternative, stepper_value, fixture_value, fixture_native,
                led_alt, over_rejected, table_range]

    def test_each_mutation_is_detected(self):
        for mutate in self.mutants():
            with self.subTest(mutation=mutate.__name__):
                contract = copy.deepcopy(self.contract)
                fixture = copy.deepcopy(self.fixture)
                mutate(contract, fixture)
                self.assertNotEqual(problems(contract, fixture), [])

    def test_page_case_table_round_trips(self):
        again = json.loads(json.dumps(self.contract))
        self.assertEqual(again, self.contract)
        self.assertEqual(problems(again, self.fixture), [])


if __name__ == '__main__':
    unittest.main()
