#!/usr/bin/env python3
"""Independent checks of the finite native data and documentary API contract."""

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / 'protocols/ebus-services/ebus-standard07-residual-fields.md'
DATA = ROOT / 'protocols/ebus-services/fixtures/ak18_standard07_residual_fields.json'
API = ROOT / 'architecture/ak18-standard07-residual-fields-api.md'

# These expectations come from the finite issue contract, independently of the
# production page/data. No executable registry implementation is modeled here.
SHAPES = [
    ('0700', 'body', 9), ('0702', 'request', 3),
    ('0703', 'request', 1), ('0703', 'positive', 10),
    ('0705', 'request', 2), ('0705', 'positive', 10),
    ('07FE', 'pair-only', 0), ('07FF', 'pair-only', 0),
]
FIELDS = [
    ('0700', 'body', 'outdoor_temperature', 0, 2, 'signed-le16/256', [-50, 50], 'degrees Celsius', None),
    ('0700', 'body', 'second', 2, 1, 'packed-decimal', [0, 59], 'none', None),
    ('0700', 'body', 'minute', 3, 1, 'packed-decimal', [0, 59], 'none', None),
    ('0700', 'body', 'hour', 4, 1, 'packed-decimal', [0, 23], 'none', None),
    ('0700', 'body', 'day', 5, 1, 'packed-decimal', [1, 31], 'none', None),
    ('0700', 'body', 'month', 6, 1, 'packed-decimal', [1, 12], 'none', None),
    ('0700', 'body', 'weekday', 7, 1, 'u8', [0, 255], 'none', None),
    ('0700', 'body', 'year', 8, 1, 'packed-decimal', [0, 99], 'none', None),
    ('0702', 'request', 'outdoor_temperature', 0, 2, 'signed-le16/256', [-50, 50], 'degrees Celsius', None),
    ('0702', 'request', 'duration', 2, 1, 'u8', [0, 255], 'minutes', 0),
    ('0703', 'request', 'secondary_block', 0, 1, 'u8', [0, 255], 'none', None),
    ('0705', 'request', 'secondary_block', 0, 1, 'u8', [0, 255], 'none', None),
    ('0705', 'request', 'primary_block', 1, 1, 'u8', [0, 255], 'none', None),
]
for service in ('0703', '0705'):
    FIELDS += [
        (service, 'positive', 'version', 0, 1, 'packed-decimal', [0, 99], 'none', None),
        (service, 'positive', 'revision', 1, 1, 'packed-decimal', [0, 99], 'none', None),
    ]
    FIELDS += [(service, 'positive', f'bitmap_{n}', n + 2, 1, 'raw-bitmap', [0, 255], 'none', None)
               for n in range(8)]
LABELS = dict(enumerate(('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')))
AXES = [
    ('Ab28Family', 'string', 'system-data', 'other-family'),
    ('Ab28Variant', 'string', 'vaillant-candidate', 'other-variant'),
    ('Ab28Primary', 'uint8', 7, 8),
    ('Ab28Secondary', '*uint8', 0, 2),
    ('Ab28Operation', '*uint8', None, 0),
    ('Ab28Direction', 'string', 'body', 'request'),
    ('Ab28Field', 'string', 'weekday', 'year'),
    ('Ab28Alternative', 'string', 'none', 'other-alternative'),
    ('Ab28Group', '*uint8', None, 0),
    ('Ab28InstanceScope', 'string', 'none', 'dynamic'),
    ('Ab28Register', '*uint16', None, 0),
]
UNKNOWN = {
    'native_support', 'emission', 'physical_responses', 'physical_effects',
    'persistence', 'delivery', 'century', 'timezone', 'calendar_validation',
    'complete_native_decimal_conversion', 'bit_selection',
    'version_control_overlap_0704', 'duration_zero_permanent',
    'temperature_8000_sentinel', 'direct_inquiry_reply',
}


def table(text, heading):
    section = text.split(heading, 1)[1].split('\n## ', 1)[0]
    lines = [line for line in section.splitlines() if line.startswith('|')]
    return [[cell.strip() for cell in line.strip('|').split('|')] for line in lines[2:]]


def prose(text):
    return ' '.join(text.split())


class ResidualContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text())
        cls.native = NATIVE.read_text()
        cls.api = API.read_text()
        cls.vectors = json.loads(re.search(r'```json\n(.*?)\n```', cls.api, re.S).group(1))

    def test_finite_family_and_unknowns(self):
        self.assertEqual(self.data['candidate_identities'], ['0700', '0702', '0703', '0704', '0705', '07FE', '07FF'])
        self.assertEqual(self.data['identity_only'], ['0704'])
        self.assertEqual(self.data['undefined_bodies'], ['0701'])
        self.assertEqual(self.data['family'], 'system-data')
        self.assertEqual(self.data['variant'], 'vaillant-candidate')
        self.assertEqual(self.data['grade'], 'Hypothesis')
        self.assertEqual(self.data['qualification'], 'Unknown')
        self.assertEqual(self.data['coordinates'], 'body offsets after PB/SB; PB/SB excluded')
        self.assertEqual(self.data['unknowns'], dict.fromkeys(UNKNOWN, 'Unknown'))

    def test_exact_shape_inventory(self):
        self.assertEqual(self.data['shapes'], [dict(service=s, direction=d, body_width=w) for s, d, w in SHAPES])
        self.assertEqual(table(self.native, '## Finite body shapes'), [[s, d, str(w)] for s, d, w in SHAPES])

    def test_temperature_name_inventory_and_consumer_drift(self):
        names = {row['field'] for row in self.data['fields']
                 if (row['service'], row['direction'], row['offset']) in
                 {('0700', 'body', 0), ('0702', 'request', 0)}}
        self.assertEqual(names, {'outdoor_temperature'})
        inventory = json.loads((ROOT / 'architecture/fixtures/non-b524-name-inventory.json').read_text())
        candidates = [row for row in inventory['candidates']
                      if row['current_name'] in names]
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]['evidence_class'], 'Hypothesis')
        self.assertEqual(candidates[0]['status'], 'candidate')
        consumers = json.loads((ROOT / 'architecture/fixtures/naming-consumers.json').read_text())
        bindings = [row for row in consumers['bindings']
                    if row['repository'] == 'ebusreg'
                    and row['file'] == 'catalog/ebus_standard/testdata/ab28_standard07_residual_fields.json'
                    and row['binding'] == '/0/key/field']
        self.assertEqual(len(bindings), 1)
        self.assertIn(bindings[0]['current_name'], names)
        # The consumer still uses its earlier spelling; this is correspondence,
        # not a claim that a downstream rename has already been implemented.
        self.assertEqual(bindings[0]['consumer_name'], 'outside_temperature')
        self.assertEqual(bindings[0]['evidence_class'], 'Unknown')
        self.assertEqual(bindings[0]['status'], 'candidate')

    def test_exact_native_field_rows(self):
        expected = []
        for s, d, f, o, w, encoding, domain, unit, default in FIELDS:
            expected.append(dict(id=f'ak18-{s}-{d}-{f}', service=s, direction=d, field=f,
                                 offset=o, width=w, encoding=encoding, domain=domain,
                                 unit=unit, default=default,
                                 labels={str(k): v for k, v in LABELS.items()} if f == 'weekday' else None,
                                 grade='Hypothesis', qualification='Unknown', raw_form='retained'))
        self.assertEqual(self.data['fields'], expected)
        self.assertEqual(len({r['id'] for r in self.data['fields']}), 33)

    def test_page_fields_against_independent_expectations(self):
        expected = []
        for s, d, f, o, w, encoding, domain, unit, default in FIELDS:
            labels = '; '.join(f'{k} {v}' for k, v in LABELS.items()) if f == 'weekday' else '-'
            expected.append([s, d, f, str(o), str(w), encoding,
                             f'{domain[0]}..{domain[1]}', unit,
                             '-' if default is None else str(default), labels])
        self.assertEqual(table(self.native, '## Finite fields'), expected)

    def test_unassociated_defaults(self):
        self.assertEqual(self.data['unassociated_defaults'], [
            {'service': '0700', 'literal': 6, 'field': None, 'association': 'Unknown'},
            {'service': '0702', 'literal': 1, 'field': None, 'association': 'Unknown'},
        ])
        self.assertEqual([(r['service'], r['field'], r['default']) for r in self.data['fields'] if r['default'] is not None],
                         [('0702', 'duration', 0)])
        self.assertIn('neither literal is assigned to a field.', prose(self.native))

    def test_temperature_and_zero_boundaries(self):
        self.assertEqual(self.data['temperature_representation'], {
            'raw_domain': [-12800, 12800], 'logical_domain': [-50, 50],
            'raw_word_hex': '8000', 'sentinel': 'Unknown',
        })
        self.assertEqual(int.from_bytes(bytes([0, 50]), 'little', signed=True) / 256, 50)
        self.assertEqual(int.from_bytes(bytes([0, 206]), 'little', signed=True) / 256, -50)
        self.assertIn('duration zero has no established permanent meaning in this variant.', prose(self.native))
        self.assertIn('The raw word `8000` has **Unknown** sentinel meaning;', prose(self.native))

    def test_synthetic_cases_independent_results(self):
        expected = []
        def add(name, service, direction, raw, result):
            expected.append(dict(name=name, service=service, direction=direction, raw=raw,
                                 expected=result, grade='Hypothesis', qualification='Unknown'))
        for value, label in [(6, 'Sunday'), (7, None), (255, None)]:
            add(f'weekday-{value}', '0700', 'body', [0, 0, 0, 0, 0, 1, 1, value, 0],
                {'weekday_raw': value, 'weekday_label': label})
        add('temperature-50', '0702', 'request', [0, 50, 0], {'temperature': 50, 'duration': 0, 'permanent': 'Unknown'})
        add('temperature--50', '0702', 'request', [0, 206, 0], {'temperature': -50, 'duration': 0, 'permanent': 'Unknown'})
        add('duration-zero', '0702', 'request', [0, 0, 0], {'temperature': 0, 'duration': 0, 'permanent': 'Unknown'})
        add('calendar-domains', '0700', 'body', [0, 0, 89, 88, 35, 49, 18, 6, 153],
            {'second': 59, 'minute': 58, 'hour': 23, 'day': 31, 'month': 12, 'weekday_raw': 6, 'weekday_label': 'Sunday', 'year': 99})
        for service in ['0703', '0705']:
            add(f'version-bitmap-{service}', service, 'positive', [18, 52, 128, 1, 2, 4, 8, 16, 32, 64],
                {'version': 12, 'revision': 34, 'bitmaps': [128, 1, 2, 4, 8, 16, 32, 64], 'selected_services': 'Unknown'})
        for value in [0, 1, 255]:
            add(f'block-0703-{value}', '0703', 'request', [value], {'secondary_block': value})
        for a, b in [(0, 0), (1, 0), (0, 1), (255, 0), (0, 255)]:
            add(f'blocks-0705-{a}-{b}', '0705', 'request', [a, b], {'secondary_block': a, 'primary_block': b})
        for service, pair, relation in [('07FE', [7, 254], 'inquiry'), ('07FF', [7, 255], 'sign-of-life')]:
            add(f'pair-{service}', service, 'pair-only', [], {'pair': pair, 'relationship': relation, 'emission': 'Unknown',
                                                         'physical_response': 'Unknown', 'direct_reply_required': False})
        self.assertEqual(self.data['cases'], expected)

    def test_raw_examples_follow_declared_representation(self):
        # Arithmetic covers only explicit valid examples, not native decimal admission.
        widths = {(s, d): n for s, d, n in SHAPES}
        for case in self.data['cases']:
            with self.subTest(case=case['name']):
                raw, result = case['raw'], case['expected']
                self.assertEqual(len(raw), widths[(case['service'], case['direction'])])
                self.assertTrue(all(type(b) is int and 0 <= b <= 255 for b in raw))
                if 'temperature' in result:
                    self.assertEqual(int.from_bytes(bytes(raw[:2]), 'little', signed=True) / 256, result['temperature'])
                    self.assertEqual(raw[2], result['duration'])
                if 'weekday_raw' in result:
                    self.assertEqual(raw[7], result['weekday_raw'])
                    self.assertEqual(LABELS.get(raw[7]), result['weekday_label'])
                if 'version' in result:
                    self.assertEqual([(raw[n] >> 4) * 10 + (raw[n] & 15) for n in (0, 1)], [12, 34])
                    self.assertEqual(raw[2:], result['bitmaps'])
                    self.assertEqual(result['selected_services'], 'Unknown')
                if 'secondary_block' in result:
                    self.assertEqual(raw[0], result['secondary_block'])
                if 'primary_block' in result:
                    self.assertEqual(raw[1], result['primary_block'])
                if 'second' in result:
                    for offset, field in [(2, 'second'), (3, 'minute'), (4, 'hour'), (5, 'day'), (6, 'month'), (8, 'year')]:
                        self.assertEqual((raw[offset] >> 4) * 10 + (raw[offset] & 15), result[field])

    def test_native_page_unknown_and_scope_boundaries(self):
        text = prose(self.native)
        for clause in [
            'No `0701` candidate body is defined.',
            '`0704` remains identity-only here;',
            '7..255 remains raw and unlabelled. It is not BCD 1..7.',
            'version and revision are two independent packed-decimal bytes, followed by eight independent raw bitmap bytes',
            'Bitmap `80` establishes no selected service.',
            'No direct inquiry reply is required by these candidate structures.',
            '**Unknown:** century, timezone, calendar validation, and complete native decimal conversion.',
            'Explicit candidate logical examples are not executable schemas.',
            'Synthetic correctness establishes only the declared representation, not qualification.',
            'Every row in both tables is **Hypothesis**, with qualification **Unknown**.',
        ]:
            self.assertIn(clause, text)
        self.assertIn('(ebus-service-07h.md#vaillant-variants)', self.native)
        self.assertNotRegex(self.native + DATA.read_text(), r'Ab28|json.RawMessage|GraphQL|\bMCP\b|\bGo\b|Helianthus')

    def test_page_synthetic_results(self):
        self.assertEqual(table(self.native, '## Synthetic cases'), [
            ['Weekday Sunday', '00 00 00 00 00 01 01 06 00', 'raw 6; Sunday'],
            ['Weekday unlabelled', '00 00 00 00 00 01 01 07 00', 'raw 7; no label'],
            ['Weekday unlabelled maximum', '00 00 00 00 00 01 01 FF 00', 'raw 255; no label'],
            ['Temperature upper boundary', '00 32 00', '50 degrees Celsius; duration 0; permanent Unknown'],
            ['Temperature lower boundary', '00 CE 00', '-50 degrees Celsius; duration 0; permanent Unknown'],
            ['Duration zero', '00 00 00', '0 degrees Celsius; duration 0; permanent Unknown'],
            ['Calendar domains', '00 00 59 58 23 31 12 06 99', 'second 59; minute 58; hour 23; day 31; month 12; weekday Sunday; year 99'],
            ['0703 positive', '12 34 80 01 02 04 08 10 20 40', 'version 12; revision 34; eight raw bitmaps; selected services Unknown'],
            ['0705 positive', '12 34 80 01 02 04 08 10 20 40', 'version 12; revision 34; eight raw bitmaps; selected services Unknown'],
            ['0703 request', '00; 01; FF', 'one independent raw secondary block'],
            ['0705 request', '00 00; 01 00; 00 01; FF 00; 00 FF', 'secondary and primary blocks varied independently'],
            ['07FE inquiry', 'empty', 'PB/SB 07 FE; no argument body; emission Unknown'],
            ['07FF sign-of-life', 'empty', 'PB/SB 07 FF; no argument body; emission Unknown'],
        ])

    def test_exact_go_signatures_and_types(self):
        blocks = re.findall(r'```go\n(.*?)\n```', self.api, re.S)
        self.assertEqual(len(blocks), 1)
        signatures, struct = blocks[0].split('type Ab28Key struct {\n')
        self.assertEqual(signatures.strip(), 'func Ab28Entries() (json.RawMessage, error)\nfunc Ab28Lookup(Ab28Key) (json.RawMessage, bool, error)')
        self.assertEqual([line.split() for line in struct.strip().removesuffix('}').strip().splitlines()],
                         [[name, kind] for name, kind, _, _ in AXES])
        self.assertIn('package `ebus_standard_catalog`', self.api)

    def test_documented_key_types_and_controls(self):
        self.assertEqual(table(self.api, '## Exact identity'),
                         [[name, kind, json.dumps(base), json.dumps(other)] for name, kind, base, other in AXES])
        self.assertEqual(self.vectors['present_key'], {name: base for name, _, base, _ in AXES})
        self.assertEqual(len(self.vectors['lookup_cases']), 13)
        self.assertEqual(self.vectors['lookup_cases'][0], {'name': 'exact', 'query': self.vectors['present_key'], 'result': 'whole-row'})
        self.assertEqual(self.vectors['lookup_cases'][-1], {
            'name': 'Ab28Secondary-absent', 'query': {**self.vectors['present_key'], 'Ab28Secondary': None}, 'result': 'missing'})

    def test_result_copy_and_error_contract(self):
        # Assert complete behavioral clauses, not just the presence of API names.
        section = prose(self.api)
        for expected in [
            '`Ab28Entries()` returns a JSON array of whole rows.',
            '`Ab28Lookup(Ab28Key)` returns exactly one whole row for an exact key.',
            'A missing exact key returns `found=false`, without a lookup error.',
            'Invalid embedded JSON returns an error from both entry points.',
            'Duplicate complete keys return an error from both entry points; no row wins.',
            'Every call returns independent deep byte copies. Mutating any returned row or entries buffer cannot affect a later result from either entry point.',
            'Each production row has a ticket-prefixed ID, the complete eleven-axis identity, stated fields/relations, candidate grade `Hypothesis`, explicit `Unknown` metadata, and retained raw form.',
        ]:
            self.assertIn(expected, section)

    def test_api_admission_parity_and_ordering(self):
        section = prose(self.api)
        for expected in [
            'Optional absent and explicit zero differ.',
            'Non-applicable string axes use `none`.',
            'an explicit string such as `00` or `dynamic`, never an invented numeric instance.',
            'No wildcard or nearest-key lookup is permitted.',
            'There is no cross-family, variant, direction, field, or alternative fallback.',
            'embeds its owned JSON in its owned Go file, validates complete identity uniqueness',
            'Shared registration, existing catalog/provider APIs, and routability remain unchanged.',
            'Admission fails closed for an incomplete or mismatched identity, malformed data, or unresolved candidate semantics.',
            'Retain raw evidence and partial last-known-good state without promoting an incomplete result.',
            'No transmit route, active executor, scan-default change, or automatic native qualification follows from catalog data.',
            'Existing eBUS MCP compatibility and GraphQL parity remain unchanged.',
            'AK17 must merge before this page in the same delivery cycle.',
            'The registry has no dependency back to this page.',
            'Merging either companion does not establish native qualification.',
        ]:
            self.assertIn(expected, section)

    def test_api_unknowns(self):
        section = prose(self.api)
        for expected in [
            'Duration 0 stays literal 0 with permanent interpretation **Unknown**.',
            'The unassociated defaults 6 and 1 retain **Unknown** field associations.',
            'Version 12 and revision 34 remain independent values, never one API number.',
            'Eight bitmap bytes remain raw; `80` does not select or admit a method.',
            '**Unknown:** native support, physical effects, persistence, delivery, emission, physical responses, exact bit selection, version-control overlap with `0704`, century, timezone, calendar validation, complete native decimal conversion, and qualified sentinel meaning for raw word `8000`.',
        ]:
            self.assertIn(expected, section)


# Each generated test varies exactly one identity axis in the published contract
# vector. Changing that vector's query/result/type is a documentary regression;
# running the companion Go implementation remains a separate integration gate.
def identity_test(axis, other):
    def check(self):
        base = {name: value for name, _, value, _ in AXES}
        cases = {case['name']: case for case in self.vectors['lookup_cases']}
        expected = dict(base)
        expected[axis] = other
        self.assertEqual(cases[axis], {'name': axis, 'query': expected, 'result': 'missing'})
        changed = [key for key in base if cases[axis]['query'][key] != base[key]]
        self.assertEqual(changed, [axis])
        self.assertEqual(cases['exact'], {'name': 'exact', 'query': base, 'result': 'whole-row'})
    return check


for _axis, _kind, _base, _other in AXES:
    setattr(ResidualContract, 'test_identity_' + _axis, identity_test(_axis, _other))


if __name__ == '__main__':
    unittest.main(verbosity=2)
