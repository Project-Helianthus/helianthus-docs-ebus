"""Check documentary examples, not a production interpreter or native support."""

import copy
import json
from pathlib import Path
import re
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/am22_standard05_candidate_views.md'
FIXTURE = ROOT / 'architecture/fixtures/am22_standard05_candidate_views.json'
IDENTITY = dict(family='burner', variant='vaillant-candidate', operation='05/01',
                direction='request', selector='burner-five-field')
NAMES = ('heat_state', 'boiler_target', 'dhw_target', 'outside_temperature', 'setting')
HEAT = {0: 'shutdown', 85: 'DHW', 170: 'heating',
        204: 'emission-check', 238: 'controller-stop'}
UNKNOWN = ('physical_support', 'presence', 'freshness', 'effects', 'persistence',
           'delivery', 'execution', 'acknowledgement', 'command_acceptance',
           'physical_length', 'empty_wire_response')


def independent_result(identity, body):
    """Test-only oracle using literal domains and struct, never fixture metadata."""
    valid = (isinstance(body, list) and
             all(type(byte) is int and 0 <= byte <= 255 for byte in body))
    malformed = not valid or not isinstance(identity, dict)
    selected = not malformed and identity == IDENTITY
    fields = []
    if selected:
        for offset, name in enumerate(NAMES):
            raw = body[offset] if offset < len(body) else None
            value = raw
            state = 'absent'
            if raw is not None:
                if offset == 0:
                    value = HEAT.get(raw)
                    state = 'unmapped' if value is None else 'in-candidate-domain'
                else:
                    value = struct.unpack('b', bytes([raw]))[0] if offset == 3 else raw
                    state = ('out-of-candidate-domain' if offset in (1, 2) and value > 90
                             else 'in-candidate-domain')
            fields.append(dict(name=name, raw=raw, interpretation=value, domain_state=state))
    return dict(identity=copy.deepcopy(identity), raw_body=copy.deepcopy(body),
                status='malformed' if malformed else 'candidate' if selected else 'raw-only',
                complete=bool(selected and len(body) == 5), fields=fields,
                remainder=copy.deepcopy(body[5:] if selected else body),
                grade='Hypothesis', qualification='Unknown')


class CandidateViews(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package = json.loads(FIXTURE.read_text())
        cls.page = PAGE.read_text()
        cls.cases = {case['id']: case for case in cls.package['cases']}

    def test_exact_declarations_and_grades(self):
        self.assertEqual(self.package['identity'], IDENTITY)
        self.assertEqual(self.package['provenance'], 'synthetic; no device observation')
        self.assertEqual(self.package['grade'], 'Hypothesis')
        self.assertEqual(self.package['qualification'], 'Unknown')
        self.assertEqual(self.package['unresolved'], dict.fromkeys(UNKNOWN, 'Unknown'))
        expected = [
            dict(name='heat_state', offset=0, codec='u8', unit=None,
                 domain=[0, 85, 170, 204, 238], default=0, conversion='identity',
                 names={'00': 'shutdown', '55': 'DHW', 'AA': 'heating',
                        'CC': 'emission-check', 'EE': 'controller-stop'}),
            dict(name='boiler_target', offset=1, codec='u8', unit='Celsius',
                 domain=[0, 90], default=0, conversion='identity'),
            dict(name='dhw_target', offset=2, codec='u8', unit='Celsius',
                 domain=[0, 90], default=0, conversion='identity'),
            dict(name='outside_temperature', offset=3, codec='i8', unit='Celsius',
                 domain=[-128, 127], default=0, conversion='identity'),
            dict(name='setting', offset=4, codec='u8', unit='percent',
                 domain=[0, 255], default=0, conversion='identity'),
        ]
        self.assertEqual(self.package['fields'], expected)
        for axis, value in IDENTITY.items():
            self.assertIn(f'| {axis} | {value} |', self.page)
        units = ('none', 'Celsius', 'Celsius', 'Celsius', 'percent')
        domains = ('00,55,AA,CC,EE', '0..90', '0..90', '-128..127', '0..255')
        for field, unit, domain in zip(expected, units, domains):
            default = 'shutdown (00)' if field['offset'] == 0 else '0'
            self.assertIn(f"| {field['name']} | {field['offset']} | {field['codec']} | "
                          f'{unit} | {domain} | {default} | identity |', self.page)
        table = self.page.split('| Raw heat state | Candidate name |\n', 1)[1].split('\n\n', 1)[0]
        self.assertEqual(table.splitlines()[1:],
                         [f'| {raw:02X} | {name} |' for raw, name in HEAT.items()])

    def test_all_results_independent_oracle(self):
        self.assertEqual(len(self.package['cases']), len(self.cases))
        self.assertEqual(len(self.cases), 64)
        for name, case in self.cases.items():
            with self.subTest(case=name):
                self.assertEqual(set(case), {'id', 'input', 'expected'})
                self.assertEqual(set(case['input']), {'identity', 'body'})
                self.assertEqual(case['expected'], independent_result(**case['input']))

    def test_each_page_case_agrees_with_package(self):
        rows = []
        for case in self.package['cases']:
            body = case['input']['body']
            output = case['expected']
            raw = (' '.join(f'{byte:02X}' for byte in body)
                   if isinstance(body, list) and all(type(x) is int and 0 <= x <= 255 for x in body)
                   else json.dumps(body, separators=(',', ':')))
            values = json.dumps([f['interpretation'] for f in output['fields']], separators=(',', ':'))
            states = ','.join(f['domain_state'] for f in output['fields']) or 'none'
            remainder = json.dumps(output['remainder'], separators=(',', ':'))
            rows.append(f"| {case['id']} | `{raw}` | {output['status']} | "
                        f"{str(output['complete']).lower()} | `{values}` | {states} | `{remainder}` |")
        table = self.page.split('| Case | Input body | Status | Complete | Interpretations | Domain states | Remainder |\n', 1)[1].split('\n\n', 1)[0]
        self.assertEqual(table.splitlines()[1:], rows)

    def test_identity_axes_fail_closed_with_valid_control(self):
        control = self.cases['valid']
        self.assertEqual(control['expected']['status'], 'candidate')
        self.assertEqual(control['input']['identity'], IDENTITY)
        wrong = dict(family='other', variant='standard', operation='06/01',
                     direction='response', selector='automatic')
        for axis, value in wrong.items():
            altered = self.cases['wrong-' + axis + '-' + value.replace('/', '-')]
            expected = dict(IDENTITY, **{axis: value})
            with self.subTest(axis=axis):
                self.assertEqual(altered['input'], dict(identity=expected, body=control['input']['body']))
                self.assertEqual(altered['expected']['status'], 'raw-only')
                for prefix in ('absent-', 'null-'):
                    case = self.cases[prefix + axis]
                    key = IDENTITY.copy()
                    if prefix == 'absent-':
                        del key[axis]
                    else:
                        key[axis] = None
                    self.assertEqual(case['input'], dict(identity=key, body=control['input']['body']))
                    self.assertEqual(case['expected']['fields'], [])
                    self.assertFalse(case['expected']['complete'])
        for name in ('wrong-operation-05-04', 'wrong-direction-positive', 'positive-prefix',
                     'extra-identity-key'):
            self.assertEqual(self.cases[name]['expected']['status'], 'raw-only')
            self.assertEqual(self.cases[name]['expected']['fields'], [])
        self.assertEqual(self.cases['request-prefix']['expected']['status'], 'candidate')
        self.assertFalse(self.cases['request-prefix']['expected']['complete'])

    def test_each_field_axis_and_independent_numbers(self):
        # Each field is varied alone against its own fixed-neighbour control.
        groups = [(0, 'heat-', (0, 85, 170, 204, 238, 221, 1), True),
                  (1, 'boiler-', (0, 90, 91, 100, 255), False),
                  (2, 'dhw-', (0, 90, 91, 100, 255), False),
                  (3, 'outside-', (0, 63, 127, 128, 255), False),
                  (4, 'setting-', (0, 100, 101, 255), False)]
        for offset, prefix, values, hexadecimal in groups:
            baseline = None
            for value in values:
                case = self.cases[prefix + (f'{value:02X}' if hexadecimal else str(value))]
                body = case['input']['body']
                neighbours = body[:offset] + body[offset + 1:]
                if baseline is None:
                    baseline = neighbours
                with self.subTest(field=NAMES[offset], raw=value):
                    self.assertEqual(case['input']['identity'], IDENTITY)
                    self.assertEqual(body[offset], value)
                    self.assertEqual(neighbours, baseline)
                    self.assertTrue(case['expected']['complete'])
        self.assertEqual([f['interpretation'] for f in self.cases['valid']['expected']['fields']],
                         ['heating', 90, 35, -1, 255])
        self.assertEqual(int('5A', 16), 90)
        self.assertEqual(int('23', 16), 35)
        for raw, value in ((128, -128), (255, -1), (63, 63), (127, 127)):
            self.assertEqual(struct.unpack('b', bytes([raw]))[0], value)
            field = self.cases[f'outside-{raw}']['expected']['fields'][3]
            self.assertEqual((field['raw'], field['interpretation']), (raw, value))
        for prefix, offset in (('boiler', 1), ('dhw', 2)):
            field = self.cases[f'{prefix}-91']['expected']['fields'][offset]
            self.assertEqual(field, dict(name=NAMES[offset], raw=91, interpretation=91,
                                         domain_state='out-of-candidate-domain'))
        for value in ('DD', '01'):
            self.assertEqual(self.cases[f'heat-{value}']['expected']['fields'][0]['domain_state'], 'unmapped')
        self.assertEqual(self.cases['outside-3F']['expected']['fields'][3]['interpretation'], 63)

    def test_all_short_lengths_extra_and_explicit_zero(self):
        full = self.cases['valid']['input']['body']
        zero = self.cases['explicit-zero']['expected']
        self.assertTrue(zero['complete'])
        for length in range(5):
            case = self.cases[f'short-{length}']
            self.assertEqual(case['input']['body'], full[:length])
            output = case['expected']
            self.assertFalse(output['complete'])
            self.assertEqual(output['fields'][:length], self.cases['valid']['expected']['fields'][:length])
            for offset in range(length, 5):
                self.assertEqual(output['fields'][offset], dict(name=NAMES[offset], raw=None,
                                 interpretation=None, domain_state='absent'))
                self.assertEqual(zero['fields'][offset]['raw'], 0)
                self.assertNotEqual(output['fields'][offset], zero['fields'][offset])
        extra = self.cases['extra']['expected']
        self.assertFalse(extra['complete'])
        self.assertEqual(extra['fields'], self.cases['valid']['expected']['fields'])
        self.assertEqual(extra['remainder'], [17, 34])

    def test_malformed_inputs_and_example_memory_independence(self):
        for name, case in self.cases.items():
            if name.startswith('malformed-'):
                with self.subTest(case=name):
                    self.assertEqual(case['expected']['status'], 'malformed')
                    self.assertEqual(case['expected']['fields'], [])
                    self.assertEqual(case['expected']['raw_body'], case['input']['body'])
        # Documentary objects must not alias; this is not a production memory test.
        cases = copy.deepcopy(self.cases)
        saved = copy.deepcopy(cases['extra']['expected'])
        cases['extra']['input']['body'][0] = 0
        self.assertEqual(cases['extra']['expected'], saved)
        cases['extra']['expected']['raw_body'][0] = 1
        self.assertEqual(cases['extra']['expected']['fields'], saved['fields'])
        cases['extra']['expected']['raw_body'][5] = 99
        self.assertEqual(cases['extra']['expected']['remainder'], [17, 34])
        raw_only = cases['wrong-family-other']['expected']
        raw_only['raw_body'][0] = 1
        self.assertEqual(raw_only['remainder'], [170, 90, 35, 255, 255])
        raw_only['identity']['family'] = 'changed'
        self.assertEqual(cases['wrong-family-other']['input']['identity']['family'], 'other')
        self.assertEqual(cases['valid'], self.cases['valid'])

    def test_prose_limits_and_relative_links(self):
        for phrase in (
            '**Hypothesis:** a pure, explicitly selected five-field candidate-body interpreter',
            '**Proven:** this documentation adds an\nexplicit interpretation API contract',
            'qualification stays Unknown', 'not stable before Helianthus 1.0',
            '`DD` is a separate unresolved check alternative, never a named value',
            'raw outside `3F` remains 63', 'Setting 255 remains 255, without clipping to 100',
            'Defaults are metadata only; every missing position remains absent, never zero',
            'never\nadd 273.15 or apply 0.01', 'no five-value body, positive result',
            'not an established physical length', 'retain previous evidence beside the current',
            'All snapshots are independent of caller\nstorage and each other',
            'eBUS MCP compatibility and GraphQL parity remain unchanged',
            'focused\ntests do not claim automatic Gate D discovery',
            'AM21 in the registry is the companion implementation slice',
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.page)
        links = re.findall(r'\[[^\]]+\]\(([^)]+)\)', self.page)
        self.assertGreaterEqual(len(links), 3)
        for link in links:
            self.assertNotIn('://', link)
            self.assertTrue((PAGE.parent / link.split('#', 1)[0]).is_file(), link)


if __name__ == '__main__':
    unittest.main()
