"""Synthetic AM14 contract seam; does not import or verify the AM13 runtime."""

import copy
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/am14_b509_heatpump_codec_dictionary.md'
FIXTURE = ROOT / 'architecture/fixtures/am14_b509_heatpump_codec_dictionary.json'
KEY_FIELDS = ('target_family', 'variant', 'primary', 'secondary', 'operation',
              'direction', 'selector')
BASE = dict(zip(KEY_FIELDS, ('heat_pump', 'direct-symbolic-candidate', 181, 9,
                             13, 'request', 'D000')))

# Independently transcribed finite expectations, never derived from fixture rows.
# selector, quantity, declaration, unit (None means absent), qualifiers, conflicts
EXPECTED = (
    ('D000', 'heat_pump_status', 'hpstatus enum', None, (), ()),
    ('BC00', 'environmental_energy_yield_total', 'energy4', 'kWh', (),
     ('environmental versus delivered yield unresolved',)),
    ('BA00', 'environmental_power', 'power', 'kW', (), ()),
    ('BB00', 'environmental_power_ratio', 'percent0', '%', (), ()),
    ('8D00', 'refrigerant_superheat', 'temp', 'K delta', (), ()),
    ('8E00', 'refrigerant_subcooling', 'temp', 'K delta', (), ()),
    ('0F00', 'source_inlet_temperature', 'tempsensor', 'C', (), ()),
    ('1400', 'refrigerant_high_pressure', 'sensor', 'bar', (), ()),
    ('1500', 'refrigerant_low_pressure', 'sensor', 'bar', (), ()),
    ('E400', 'compressor_state', 'UCH enum', None, (), ()),
    ('E900', 'compressor_control_state', 'UCH enum', None, (), ()),
    ('E600', 'compressor_minimum_on_duration', 'seconds', 's', (), ()),
    ('E700', 'compressor_minimum_off_duration', 'seconds', 's', (), ()),
    ('E800', 'compressor_minimum_start_interval', 'seconds', 's', (), ()),
    ('A800', 'compressor_dhw_start_count', 'counter', 'count', (), ()),
    ('B400', 'compressor_high_pressure_cutout_count', 'counter', 'count', (), ()),
    ('CE01', 'defrost_active', 'yesno', 'bool', (), ()),
    ('5701', 'phase_order_status', 'phaseok enum', None, (), ()),
    ('8800', 'phase_status_flags', 'phase flags (bitmask)', None, (), ()),
    ('3F00', 'inrush_current_limiter_output_active', 'on/off', None, (), ()),
    ('A901', 'noise_reduction_active', 'yesno', 'bool', (), ()),
    ('2401', 'noise_reduction_factor', 'percent0', None, (),
     ('ratio unit Unknown',)),
    ('E201', 'environmental_power', 'UCH', '100W units',
     ('100 W per unsigned byte',), ()),
    ('E301', 'bivalent_mode', 'UCH enum', None, (), ()),
    ('E401', 'source_temperature_limit_at_maximum_flow', 'SCH', 'C',
     ('signed',), ()),
    ('E501', 'source_temperature_limit_slope', 'UCH (slope)', None, (), ()),
    ('E901', 'refrigerant_low_pressure_maximum', 'ULG', None, (),
     ('pressure unit Unknown',)),
    ('8000', 'compressor_energy_integral', 'value (unknown)', None, (),
     ('integral codec and unit Unknown',)),
)
CONTRACT = {
    'key_fields': list(KEY_FIELDS), 'selected': BASE,
    'access': 'read', 'row_count': 28,
    'selector': 'two ordered bytes as four uppercase hex digits',
    'software_grade': 'Proven', 'association_grade': 'Hypothesis',
    'qualification': False,
    'unknown': ['native_support', 'presence', 'freshness', 'execution',
                'effects', 'persistence', 'delivery', 'physical_qualification'],
    'absent_properties': ['width', 'endian', 'mapping', 'sentinel', 'converter'],
    'no_row': None, 'malformed': 'ValueError',
    'copy_policy': 'deep independent', 'provider_registration': False,
    'generic_raw_access': 'unchanged', 'discovery': 'unchanged',
    'mcp': 'unchanged', 'graphql': 'unchanged',
}


def key_of(key):
    if type(key) is not dict or set(key) != set(KEY_FIELDS):
        raise ValueError('malformed key fields')
    for field in ('target_family', 'variant', 'direction'):
        if type(key[field]) is not str or not key[field]:
            raise ValueError('malformed key token')
    for field in ('primary', 'secondary', 'operation'):
        if type(key[field]) is not int or not 0 <= key[field] <= 255:
            raise ValueError('malformed key byte')
    if (type(key['selector']) is not str
            or re.fullmatch(r'[0-9A-F]{4}', key['selector']) is None):
        raise ValueError('malformed ordered selector')
    return tuple(key[field] for field in KEY_FIELDS)


def validate_row(row):
    if type(row) is not dict or set(row) != {
            'key', 'quantity', 'codec', 'grade', 'conflicts'}:
        raise ValueError('malformed row fields')
    key_of(row['key'])
    if type(row['quantity']) is not str or not row['quantity']:
        raise ValueError('malformed quantity')
    codec = row['codec']
    if (type(codec) is not dict or 'declaration' not in codec
            or set(codec) - {'declaration', 'unit', 'qualifiers'}):
        raise ValueError('malformed codec fields')
    for field in ('declaration', 'unit'):
        if field in codec and (type(codec[field]) is not str or not codec[field]):
            raise ValueError('malformed literal declaration or unit')
    for values in (row['conflicts'], codec.get('qualifiers', [])):
        if (type(values) is not list
                or any(type(v) is not str or not v for v in values)):
            raise ValueError('malformed declaration list')
    if row['grade'] != 'Hypothesis':
        raise ValueError('association grade must stay Hypothesis')


class ExampleDictionary:
    """Owned injection seam over synthetic rows, not a production provider."""

    def __init__(self, rows):
        if type(rows) is not list:
            raise ValueError('rows must be a list')
        self._rows = {}
        for row in rows:
            validate_row(row)
            identity = key_of(row['key'])
            if identity in self._rows:
                raise ValueError('duplicate complete key')
            self._rows[identity] = copy.deepcopy(row)

    def metadata(self):
        return copy.deepcopy(list(self._rows.values()))

    def lookup(self, key):
        return copy.deepcopy(self._rows.get(key_of(key)))


def envelope(dictionary, key, raw, last_known_good):
    """Example-only partial-result envelope, with no decoder or shared cache."""
    result = {'raw': copy.deepcopy(raw),
              'last_known_good': copy.deepcopy(last_known_good),
              'row': None, 'error': None, 'qualified': False}
    try:
        result['row'] = dictionary.lookup(key)
    except ValueError:
        result['error'] = 'malformed-key'
    return result


def expected_rows():
    rows = []
    for selector, quantity, label, unit, qualifiers, conflicts in EXPECTED:
        codec = {'declaration': label}
        if unit is not None:
            codec['unit'] = unit
        if qualifiers:
            codec['qualifiers'] = list(qualifiers)
        rows.append({'key': dict(BASE, selector=selector), 'quantity': quantity,
                     'codec': codec, 'grade': 'Hypothesis',
                     'conflicts': list(conflicts)})
    return rows


class HeatPumpCodecDictionaryContract(unittest.TestCase):
    def setUp(self):
        self.package = json.loads(FIXTURE.read_text())
        self.rows = self.package['rows']
        self.view = ExampleDictionary(self.rows)
        self.page = PAGE.read_text()

    def test_finite_exact_tuple_set_and_metadata(self):
        self.assertEqual(self.package['kind'], 'AM14SyntheticCodecDictionary')
        self.assertEqual(set(self.package), {'kind', 'contract', 'rows', 'cases'})
        self.assertEqual(self.package['contract'], CONTRACT)
        self.assertEqual(len(self.rows), 28)
        self.assertEqual(self.rows, expected_rows())
        self.assertEqual(self.view.metadata(), expected_rows())
        for row in expected_rows():
            with self.subTest(selector=row['key']['selector']):
                self.assertEqual(self.view.lookup(row['key']), row)

    def test_page_contract_and_every_row(self):
        formal = re.search(r'```json\n(.*?)\n```', self.page, re.S)
        self.assertIsNotNone(formal)
        self.assertEqual(json.loads(formal[1]), CONTRACT)
        section = self.page.split(
            '| Selector | Quantity | Codec declaration | Unit | Qualifiers | Conflicts |', 1)[1]
        actual = [[v.strip() for v in line.strip('|').split('|')]
                  for line in section.split('\n\n', 1)[0].splitlines()
                  if line.startswith('|')][1:]
        wanted = [[s, q, c, u if u is not None else 'absent',
                   '; '.join(a) or 'absent', '; '.join(b) or 'none']
                  for s, q, c, u, a, b in EXPECTED]
        self.assertEqual(actual, wanted)

    def test_page_limits_and_grade_boundaries(self):
        for required in (
            'Codec labels are literal declarations, never executable converters.',
            'The second selector byte is not interpreted as a page.',
            'No OP0E write row or OP29 alternate is implied.',
            'BC00 environmental versus delivered yield remains unresolved.',
            '2401 ratio unit remains Unknown.',
            'E901 pressure unit remains Unknown.',
            '8000 integral codec and unit remain Unknown.',
            'BA00 and E201 stay separate even though both names are environmental_power.',
            '3F00, BB00, 1400 and E400 never acquire boiler semantics.',
            'The heat_pump_interface_unit family has no entry in this dictionary.',
            'No runtime device inference occurs.',
            'No pending schema/API is imported and no provider is registered.',
            'eBUS MCP compatibility and GraphQL parity are unchanged.',
            'Nothing is stable before Helianthus 1.0.',
            'AM13 is the registry prerequisite; its implementation is not verified here.',
            'Unknown native properties are independent of invocation and qualification.',
            'Partial failure keeps raw bytes, independently useful fields and last-known-good state.',
            'The example envelope admits no native value and changes no shared state.',
        ):
            with self.subTest(required=required):
                self.assertIn(required, self.page)

    def test_every_identity_axis_independently(self):
        # Each alternate is well formed; a miss cannot be explained by validation.
        alternatives = {
            'target_family': ('boiler', 'heat_pump_interface_unit', 'unknown'),
            'variant': ('other-candidate', 'unknown'),
            'primary': (0, 180, 255), 'secondary': (0, 8, 255),
            'operation': (0, 14, 41, 255),
            'direction': ('positive', 'read', 'unknown'),
            'selector': ('0000', 'FFFF'),
        }
        for expected in expected_rows():
            self.assertEqual(self.view.lookup(expected['key']), expected)
            for field, values in alternatives.items():
                for value in values:
                    with self.subTest(selector=expected['key']['selector'],
                                      field=field, value=value):
                        key = dict(expected['key'], **{field: value})
                        key_of(key)
                        self.assertIsNone(self.view.lookup(key))

    def test_selector_bytes_are_ordered_and_not_pages(self):
        self.assertEqual((int('B5', 16), int('09', 16), int('0D', 16)),
                         (181, 9, 13))
        self.assertEqual((int('0E', 16), int('29', 16)), (14, 41))
        for selector, *_ in EXPECTED:
            raw = bytes.fromhex(selector)
            self.assertEqual(len(raw), 2)
            # Independent byte arithmetic checks the textual pair, not address endianness.
            self.assertEqual(f'{raw[0]:02X}{raw[1]:02X}', selector)
            self.assertEqual(int(selector, 16), raw[0] * 256 + raw[1])
            reverse = raw[::-1].hex().upper()
            self.assertIsNone(self.view.lookup(dict(BASE, selector=reverse)))
            # Every individual byte is varied to a guaranteed absent selector.
            for changed in (bytes((0, raw[1])), bytes((raw[0], 255))):
                self.assertIsNone(self.view.lookup(
                    dict(BASE, selector=changed.hex().upper())))
        self.assertEqual(bytes.fromhex('CE01'), bytes((206, 1)))
        self.assertEqual(bytes.fromhex('E201'), bytes((226, 1)))

    def test_equal_names_and_family_collisions(self):
        ba = self.view.lookup(dict(BASE, selector='BA00'))
        e2 = self.view.lookup(dict(BASE, selector='E201'))
        self.assertEqual(ba['quantity'], 'environmental_power')
        self.assertEqual(e2['quantity'], 'environmental_power')
        self.assertEqual(ba['codec'], {'declaration': 'power', 'unit': 'kW'})
        self.assertEqual(e2['codec'], {'declaration': 'UCH', 'unit': '100W units',
                                     'qualifiers': ['100 W per unsigned byte']})
        controls = [copy.deepcopy(self.rows[0]) for _ in range(2)]
        controls[1]['key']['target_family'] = 'synthetic-other-family'
        controls[1]['quantity'] = 'synthetic_other_quantity'
        control_view = ExampleDictionary(controls)
        self.assertEqual(len(control_view.metadata()), 2)
        for control in controls:
            self.assertEqual(control_view.lookup(control['key']), control)
        for selector in ('3F00', 'BB00', '1400', 'E400'):
            self.assertIsNone(self.view.lookup(dict(BASE, selector=selector,
                                                   target_family='boiler')))

    def test_absent_null_zero_extra_and_malformed_key_fields(self):
        for field in KEY_FIELDS:
            missing = dict(BASE)
            del missing[field]
            for key in (missing, dict(BASE, **{field: None}),
                        dict(BASE, **{field: False}), dict(BASE, **{field: []})):
                with self.subTest(field=field, key=key):
                    with self.assertRaises(ValueError):
                        self.view.lookup(key)
            zero = dict(BASE, **{field: 0 if field in
                                 ('primary', 'secondary', 'operation') else '0'})
            if field == 'selector':
                zero[field] = '0000'
            self.assertIsNone(self.view.lookup(zero))
        malformed = [None, [], dict(BASE, extra=0)]
        for field in ('primary', 'secondary', 'operation'):
            malformed += [dict(BASE, **{field: value})
                          for value in (-1, 256, 13.0, '13')]
        for field in ('target_family', 'variant', 'direction'):
            malformed.append(dict(BASE, **{field: ''}))
        malformed += [dict(BASE, selector=value)
                      for value in ('D0', 'D00000', 'd000', 'DG00', 0, [208, 0])]
        for key in malformed:
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.view.lookup(key)

    def test_row_validation_seam_and_duplicate_rejection(self):
        ExampleDictionary(copy.deepcopy(self.rows))  # valid control
        with self.assertRaises(ValueError):
            ExampleDictionary(self.rows + [copy.deepcopy(self.rows[0])])
        for value in (None, {}, 'rows'):
            with self.assertRaises(ValueError):
                ExampleDictionary(value)
        for field in self.rows[0]:
            row = copy.deepcopy(self.rows[0])
            del row[field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                ExampleDictionary([row])
        bad_rows = []
        for field, value in (('quantity', 0), ('quantity', ''), ('grade', 'Proven'),
                             ('conflicts', None), ('conflicts', [0]), ('extra', 0)):
            bad_rows.append(dict(copy.deepcopy(self.rows[0]), **{field: value}))
        for codec in ({}, None, {'declaration': 0}, {'declaration': ''},
                      {'declaration': 'opaque', 'unit': 0},
                      {'declaration': 'opaque', 'unit': None},
                      {'declaration': 'opaque', 'unit': ''},
                      {'declaration': 'opaque', 'qualifiers': [False]},
                      {'declaration': 'opaque', 'qualifiers': None},
                      {'declaration': 'opaque', 'converter': 'numeric'}):
            bad_rows.append(dict(copy.deepcopy(self.rows[0]), codec=codec))
        for row in bad_rows:
            with self.subTest(row=row), self.assertRaises(ValueError):
                ExampleDictionary([row])

    def test_unknown_and_compound_labels_are_metadata_only(self):
        for label in ('synthetic-unknown-codec', 'alternative-a / alternative-b'):
            row = copy.deepcopy(self.rows[0])
            row['codec'] = {'declaration': label}
            view = ExampleDictionary([row])
            self.assertEqual(view.lookup(BASE), row)
            self.assertEqual(set(view.lookup(BASE)['codec']), {'declaration'})
            self.assertFalse(hasattr(view, 'decode'))
        for row in self.view.metadata():
            for absent in CONTRACT['absent_properties']:
                self.assertNotIn(absent, row['codec'])

    def test_catalog_rejection_is_atomic_and_optional_fields_stay_absent(self):
        before = copy.deepcopy(self.rows)
        for bad in (self.rows + [copy.deepcopy(self.rows[0])],
                    self.rows + [dict(copy.deepcopy(self.rows[0]), grade='Proven')]):
            with self.assertRaises(ValueError):
                ExampleDictionary(bad)
            self.assertEqual(self.rows, before)
            self.assertEqual(self.view.metadata(), expected_rows())
        for field in ('unit', 'qualifiers'):
            row = copy.deepcopy(self.rows[22])
            del row['codec'][field]
            view = ExampleDictionary([row])
            self.assertNotIn(field, view.lookup(row['key'])['codec'])
            for value in (None, 0, False):
                row['codec'][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    ExampleDictionary([row])

    def test_owned_catalog_input_lookup_and_enumeration_memory(self):
        supplied = copy.deepcopy(self.rows)
        view = ExampleDictionary(supplied)
        supplied[1]['conflicts'].clear()
        supplied[22]['codec']['qualifiers'].append('injected')
        supplied[0]['key']['selector'] = '0000'
        self.assertEqual(view.metadata(), expected_rows())
        for index in (0, 1, 22):
            expected = expected_rows()[index]
            result = view.lookup(expected['key'])
            result['key']['selector'] = '0000'
            result['codec']['qualifiers'] = ['changed']
            result['conflicts'].append('changed')
            self.assertEqual(view.lookup(expected['key']), expected)
        listing = view.metadata()
        listing[1]['conflicts'].clear()
        listing[22]['codec']['qualifiers'].clear()
        listing.clear()
        self.assertEqual(view.metadata(), expected_rows())

    def test_cases_page_fixture_and_independent_outcomes(self):
        cases = self.package['cases']
        expected_ids = ['match', 'same-name-ba', 'same-name-e2', 'unknown-family',
                        'interface-family', 'other-variant', 'wrong-primary',
                        'wrong-secondary', 'op0e', 'op29', 'positive', 'reversed',
                        'first-byte', 'second-byte', 'zero-selector',
                        'missing-selector', 'missing-operation', 'zero-operation',
                        'extra-key', 'malformed-selector', 'raw-absent',
                        'raw-empty', 'raw-zero', 'partial-raw']
        self.assertEqual([case['id'] for case in cases], expected_ids)
        section = self.page.split('| Case | Key change from D000 | Raw fields | Outcome |', 1)[1]
        page_cases = [[v.strip() for v in line.strip('|').split('|')]
                      for line in section.split('\n\n', 1)[0].splitlines()
                      if line.startswith('|')][1:]
        self.assertEqual([row[0] for row in page_cases], expected_ids)
        changes = {
            'same-name-ba': ('selector', 'BA00'), 'same-name-e2': ('selector', 'E201'),
            'unknown-family': ('target_family', 'unknown'),
            'interface-family': ('target_family', 'heat_pump_interface_unit'),
            'other-variant': ('variant', 'other-candidate'),
            'wrong-primary': ('primary', 0), 'wrong-secondary': ('secondary', 0),
            'op0e': ('operation', 14), 'op29': ('operation', 41),
            'positive': ('direction', 'positive'), 'reversed': ('selector', '00D0'),
            'first-byte': ('selector', 'D100'), 'second-byte': ('selector', 'D001'),
            'zero-selector': ('selector', '0000'), 'zero-operation': ('operation', 0),
            'extra-key': ('extra', 0), 'malformed-selector': ('selector', 'D0'),
        }
        for case, page_case in zip(cases, page_cases):
            self.assertEqual(set(case), {'id', 'key', 'raw', 'last_known_good', 'expect'})
            name = case['id']
            key = dict(BASE)
            if name in changes:
                field, value = changes[name]
                key[field] = value
                change_text = f'{field}={value}'
            elif name.startswith('missing-'):
                field = name.removeprefix('missing-')
                del key[field]
                change_text = f'{field}=absent'
            else:
                change_text = 'none'
            raw = {'payload': [0, 17], 'independent': [42]}
            if name == 'raw-absent':
                del raw['payload']
            elif name == 'raw-empty':
                raw['payload'] = []
            elif name == 'raw-zero':
                raw['payload'] = [0]
            elif name == 'partial-raw':
                raw['payload'] = [0]
                raw['unresolved'] = []
            previous = {'independent': {'raw': [42], 'grade': 'Unknown'}}
            self.assertEqual(case['key'], key)
            self.assertEqual(case['raw'], raw)
            self.assertEqual(case['last_known_good'], previous)
            error = 'malformed-key' if name in (
                'missing-selector', 'missing-operation', 'extra-key',
                'malformed-selector') else None
            matches = {'match': 'D000', 'same-name-ba': 'BA00',
                       'same-name-e2': 'E201', 'raw-absent': 'D000',
                       'raw-empty': 'D000', 'raw-zero': 'D000', 'partial-raw': 'D000'}
            selector = matches.get(name)
            outcome = 'malformed-key' if error else selector or 'no-row'
            self.assertEqual(case['expect'], {'row_selector': selector, 'error': error})
            raw_text = json.dumps(raw, separators=(',', ':'), sort_keys=True)
            self.assertEqual(page_case, [name, change_text, raw_text, outcome])
            output = envelope(self.view, key, raw, previous)
            self.assertEqual(output['raw'], raw)
            self.assertEqual(output['last_known_good'], previous)
            self.assertEqual(output['error'], error)
            self.assertIs(output['qualified'], False)
            expected = next((r for r in expected_rows()
                             if r['key']['selector'] == selector), None)
            self.assertEqual(output['row'], expected)

    def test_partial_failure_owns_raw_and_last_known_good(self):
        raw = {'payload': bytearray((0, 17)), 'independent': {'raw': [42]}}
        previous = {'independent': {'raw': [42], 'grade': 'Unknown'}}
        pristine_raw, pristine_previous = copy.deepcopy((raw, previous))
        for key in (BASE, dict(BASE, target_family='unknown'), {},
                    dict(BASE, operation=14)):
            output = envelope(self.view, key, raw, previous)
            output['raw']['payload'][0] = 255
            output['raw']['independent']['raw'].clear()
            output['last_known_good']['independent']['raw'].clear()
            self.assertEqual(raw, pristine_raw)
            self.assertEqual(previous, pristine_previous)
            again = envelope(self.view, key, raw, previous)
            raw['payload'][0] = 1
            previous['independent']['raw'][0] = 7
            self.assertEqual(again['raw'], pristine_raw)
            self.assertEqual(again['last_known_good'], pristine_previous)
            raw, previous = copy.deepcopy((pristine_raw, pristine_previous))
        self.assertEqual(self.view.metadata(), expected_rows())

    def test_raw_field_axes_preserve_malformed_unknown_and_zero(self):
        # Metadata access never attempts to decode or repair these raw fields.
        for field in ('payload', 'independent', 'unknown-extra'):
            for value in (None, [], [0], [0, 17], [256], 'malformed',
                          {'nested': [0]}):
                raw = {'payload': [0, 17], 'independent': [42]}
                raw[field] = value
                previous = {'independent': {'raw': [42], 'grade': 'Unknown'}}
                for key in (BASE, {}, dict(BASE, direction='positive')):
                    result = envelope(self.view, key, raw, previous)
                    self.assertEqual(result['raw'], raw)
                    self.assertEqual(result['last_known_good'], previous)
                    self.assertIs(result['qualified'], False)
            raw = {'payload': [0], 'independent': [42]}
            raw.pop(field, None)
            self.assertNotIn(field, envelope(self.view, BASE, raw, {})['raw'])
        shared = {'raw': [0]}
        result = envelope(self.view, BASE, {'independent': shared},
                          {'independent': shared})
        result['raw']['independent']['raw'].append(1)
        self.assertEqual(result['last_known_good'], {'independent': {'raw': [0]}})
        self.assertEqual(shared, {'raw': [0]})


if __name__ == '__main__':
    unittest.main()
