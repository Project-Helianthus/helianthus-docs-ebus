"""Finite synthetic B520 declarations; no native execution or admission."""
import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ac20_simulator_adc.json'
PAGE = ROOT / 'protocols/vaillant/ebus-vaillant-B520.md'


def expected():
    """Independent finite oracle: never read expectations from the fixture/page."""
    def field(name, pos, width=1, high=255, signed=False, divisor=None,
              unit=None, **extra):
        value = dict(name=name, logical_position=pos, width=width,
                     raw_domain=[0, high], signed=signed,
                     byte_order='little_endian' if width == 2 else None,
                     conversion={'divide_by': divisor} if divisor else None,
                     unit=unit, default=None, mappings={}, reserved_regions=[],
                     grade='Hypothesis', raw_fallback='preserve_raw_bytes')
        value.update(extra)
        return value
    request = [
        field('relay', 3, bit_roles=None),
        field('PWM1', 4, divisor=2, unit='percent'),
        field('PWM2', 5, divisor=2, unit='percent'),
        field('stepper', 6, steps_domain=None, unmapped_regions=[]),
        field('LED', 7, unmapped_regions=[]),
        field('ED', 8, unit='percent'),
        field('temperature-table', 9, unmapped_regions=[[4, 255]], mappings={
            '0': {'label': 'standard3K3', 'candidate_celsius_range': None},
            '1': {'label': 'extended1K', 'candidate_celsius_range': None},
            '2': {'label': 'low-temperature15K', 'candidate_celsius_range': None},
            '3': {'label': 'standard1K', 'candidate_celsius_range': None}}),
    ]
    positive = [field('ADC', 3, 2, raw_domain=None)]
    for name, pos in [('temperature1', 5), ('temperature2', 7),
                      ('temperature3', 9), ('temperature4', 11)]:
        positive.append(field(name, pos, 2, signed=True, divisor=16, unit='degrees_C',
                              raw_domain=None, candidate_physical_domain=None, sentinel=None))
    positive += [field('unknown13', 13),
                 field('impeller', 14, 2, unit='Hz', raw_domain=None),
                 field('vortex', 16, 2, unit='Hz', raw_domain=None,
                       candidate_operational_domain=None,
                       candidate_hysteresis_hz=None, sentinel=None)]
    entries = []
    for alternative, direction, extent, fields, reserved in [
        ('request', 'request', 10, request, []),
        ('positive', 'response', 18, positive, []),
        ('negative', 'response', None, [], []),
    ]:
        entries.append(dict(id='ac20_b520_op00_' + alternative,
                            family='Vaillant simulator', variant=None,
                            direction=direction, service='B520', operation=0,
                            alternative=alternative, logical_extent=extent,
                            physical_extent=None, grade='Hypothesis',
                            raw_fallback='preserve_raw_bytes', fields=fields,
                            reserved_regions=reserved, remaining_selectors=None,
                            address_space=None, support=None))
    return dict(id='ac20_simulator_adc', representation_grade='Proven',
                candidate_grade='Hypothesis', physical_qualification='Unknown',
                coordinate_system='logical_including_prefix_not_physical_offsets',
                limitations=['partial_catalog', 'remaining_selectors_unknown',
                             'address_space_unknown', 'support_unknown',
                             'zero_not_established_sentinel',
                             'vortex_domains_and_hysteresis_unknown',
                             'defaults_unknown', 'actuator_semantics_unknown',
                             'acceptance_bounds_unknown', 'thermistor_celsius_ranges_unknown'],
                entries=entries)


def candidate(field, raw):
    value = int.from_bytes(raw, 'little' if field['byte_order'] in
                           (None, 'little_endian') else 'big', signed=field['signed'])
    conversion = field['conversion']
    return value / conversion['divide_by'] if conversion else value


def inside(domain, value):
    return domain[0] <= value <= domain[1]


def tables(text):
    groups = []
    for section in text.split('\n\n'):
        lines = section.splitlines()
        if lines and lines[0].startswith('|'):
            groups.append([[cell.strip() for cell in line.strip('|').split('|')]
                           for line in lines if not line.startswith('| ---')])
    return groups


class SimulatorADC(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def field(self, alternative, name):
        return next(f for e in self.data['entries'] if e['alternative'] == alternative
                    for f in e['fields'] if f['name'] == name)

    def test_exact_declarations(self):
        self.assertEqual(self.data, expected())

    def test_identity_axes_independently(self):
        self.assertEqual(self.data, expected())  # valid control
        for index in range(3):
            for axis in ('family', 'variant', 'direction', 'service', 'operation', 'alternative'):
                for mode in ('vary', 'drop'):
                    with self.subTest(entry=index, axis=axis, mode=mode):
                        mutated = copy.deepcopy(self.data)
                        if mode == 'drop':
                            del mutated['entries'][index][axis]
                        else:
                            mutated['entries'][index][axis] = 1 if axis == 'operation' else 'other'
                        self.assertNotEqual(mutated, expected())

    def test_percent_ff(self):
        for name in ('PWM1', 'PWM2'):
            with self.subTest(field=name):
                f = self.field('request', name)
                self.assertEqual(candidate(f, bytes.fromhex('FF')), 127.5)
                self.assertTrue(inside(f['raw_domain'], 255))

    def test_ed_scaling_unknown_preserves_raw(self):
        f = self.field('request', 'ED')
        self.assertIsNone(f['conversion'])
        self.assertEqual(f['unit'], 'percent')
        self.assertEqual(f['raw_domain'], [0, 255])
        for raw in range(256):
            with self.subTest(raw=raw):
                self.assertEqual(candidate(f, bytes([raw])), raw)

    def test_unsupported_properties_remain_unknown(self):
        for entry in self.data['entries']:
            for f in entry['fields']:
                with self.subTest(field=f['name']):
                    self.assertIsNone(f['default'])
                    if f['width'] == 2:
                        self.assertIsNone(f['raw_domain'])
        for name in ('stepper', 'LED'):
            f = self.field('request', name)
            self.assertEqual(f['mappings'], {})
            self.assertEqual(f['unmapped_regions'], [])
            for raw in (0, 1, 240, 241, 254, 255):
                self.assertEqual(candidate(f, bytes([raw])), raw)
        self.assertIsNone(self.field('request', 'stepper')['steps_domain'])
        self.assertIsNone(self.field('request', 'stepper')['unit'])
        for mapping in self.field('request', 'temperature-table')['mappings'].values():
            self.assertIsNone(mapping['candidate_celsius_range'])

    def test_temperature_carriers(self):
        for name in ('temperature1', 'temperature2', 'temperature3', 'temperature4'):
            f = self.field('positive', name)
            for raw, result in [('00 0C', 192), ('FF FF', -0.0625),
                                ('00 00', 0), ('80 0C', 200), ('81 0C', 200.0625)]:
                with self.subTest(field=name, raw=raw):
                    self.assertEqual(candidate(f, bytes.fromhex(raw)), result)
                    self.assertIsNone(f['raw_domain'])
                    self.assertIsNone(f['candidate_physical_domain'])
                    self.assertIsNone(f['sentinel'])

    def test_adc_and_impeller(self):
        for name in ('ADC', 'impeller'):
            f = self.field('positive', name)
            for value in (0, 1000, 1001, 1023, 1024, 65535):
                with self.subTest(field=name, value=value):
                    self.assertEqual(candidate(f, value.to_bytes(2, 'little')), value)
                    self.assertIsNone(f['raw_domain'])

    def test_vortex_carrier_without_threshold_claims(self):
        f = self.field('positive', 'vortex')
        for raw in (0, 4, 5, 350, 351, 65535):
            with self.subTest(raw=raw):
                self.assertEqual(candidate(f, raw.to_bytes(2, 'little')), raw)
        for key in ('raw_domain', 'candidate_operational_domain',
                    'candidate_hysteresis_hz', 'sentinel'):
            with self.subTest(key=key):
                self.assertIsNone(f[key])

    def test_service_index_links_page(self):
        overview = (PAGE.parent / 'ebus-vaillant.md').read_text()
        index = overview.split('## Scope', 1)[0]
        self.assertIn('[`ebus-vaillant-B520.md`](ebus-vaillant-B520.md)', index)
        without_page = next(line for line in index.splitlines()
                            if 'without a dedicated page' in line)
        self.assertNotIn('B520', without_page)
        section = overview.split('## Other B5 services (candidate layouts)', 1)[1]
        preamble = ' '.join(section.split('###', 1)[0].split())
        self.assertIn('The services below have no dedicated page except for '
                      '[B520](ebus-vaillant-B520.md).', preamble)

    def test_page_tables(self):
        identity = [['Family', 'Variant', 'Direction', 'Service', 'Operation', 'Alternative',
                     'Logical extent', 'Physical extent', 'Grade']]
        for direction, alternative, extent in [('request', 'request', '10'),
                                               ('response', 'positive', '18'),
                                               ('response', 'negative', 'Unknown')]:
            identity.append(['Vaillant simulator', 'Unknown', direction, 'B520', '0x00',
                             alternative, extent, 'Unknown', 'Hypothesis'])
        header = ['Field', 'Logical position', 'Carrier', 'Declared raw domain',
                  'Candidate interpretation', 'Default']
        request = [header] + [line.split(' | ') for line in [
            'relay | 3 | u8 | 0..255 | raw; bit roles Unknown | Unknown',
            'PWM1 | 4 | u8 | 0..255 | raw/2 percent; 0..127.5 | Unknown',
            'PWM2 | 5 | u8 | 0..255 | raw/2 percent; 0..127.5 | Unknown',
            'stepper | 6 | u8 | 0..255 | raw; steps and calibration semantics Unknown | Unknown',
            'LED | 7 | u8 | 0..255 | raw; value meanings Unknown | Unknown',
            'ED | 8 | u8 | 0..255 | percent label; scaling Unknown; preserve raw | Unknown',
            'temperature-table | 9 | u8 | 0..255 | labels below; 4..255 unmapped | Unknown']]
        labels = [['Temperature-table raw', 'Candidate label', 'Candidate range (degrees C)', 'Grade']]
        for raw, label, domain in [('0', 'standard3K3', 'Unknown'),
                                   ('1', 'extended1K', 'Unknown'),
                                   ('2', 'low-temperature15K', 'Unknown'),
                                   ('3', 'standard1K', 'Unknown')]:
            labels.append([raw, label, domain, 'Hypothesis'])
        positive = [header, ['ADC', '3', 'u16 LE', 'Unknown', 'raw quantity; unit Unknown', 'Unknown']]
        for name, pos in [('temperature1', '5'), ('temperature2', '7'),
                          ('temperature3', '9'), ('temperature4', '11')]:
            positive.append([name, pos, 'i16 LE', 'Unknown', 'raw/16 degrees C', 'Unknown'])
        positive += [
            ['unknown13', '13', 'u8', '0..255', 'raw; meaning Unknown', 'Unknown'],
            ['impeller', '14', 'u16 LE', 'Unknown', 'Hz', 'Unknown'],
            ['vortex', '16', 'u16 LE', 'Unknown',
             'Hz; operational domain and hysteresis Unknown', 'Unknown']]
        self.assertEqual(tables(self.page), [identity, request, labels, positive])

    def test_page_grade_boundaries(self):
        text = ' '.join(self.page.split())
        for phrase in [
            'All field interpretations below are **Hypothesis**, unconfirmed on the wire.',
            '**Proven** applies only to their checked software representation and arithmetic.',
            'Physical qualification is **Unknown**.',
            'these declarations grant no runtime capability or write admission.',
            'Every row is **Hypothesis** for the sourced layout and scaling; defaults and unsupported interpretations are **Unknown**.',
            'Absence does not mean zero length.',
            'Zero is not an established sentinel or default.',
            'Accepted raw and physical domains are **Unknown**;',
            'independent physical channel behavior is **Unknown**.',
            'Native adaptation, physical lengths, peer effects, device support and physical qualification remain **Unknown**.',
            'Do not clip at 100 or interpret `FF` as unavailable.',
            'Raw `FF` for either PWM label gives candidate 127.5 percent.',
            'ED has a candidate percent label, but its scaling is **Unknown**;',
            'acceptance and sentinel meanings **Unknown**.',
            'Those properties remain **Unknown** in both this page and the synthetic fixture;',
            'Remaining selectors, address-space semantics and support remain **Unknown**',
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertEqual(text.count('Every row is **Hypothesis** for the sourced layout and scaling;'), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
