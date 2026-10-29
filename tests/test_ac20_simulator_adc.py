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
                     unit=unit, default=0, mappings={}, reserved_regions=[],
                     grade='Hypothesis', raw_fallback='preserve_raw_bytes')
        value.update(extra)
        return value
    request = [
        field('relay', 3, bit_roles=None),
        field('PWM1', 4, divisor=2, unit='percent'),
        field('PWM2', 5, divisor=2, unit='percent'),
        field('stepper', 6, unit='steps', steps_domain=[0, 240],
              mappings={'255': 'calibrate/go-to-zero'}, unmapped_regions=[[241, 254]]),
        field('LED', 7, mappings={'0': 'disabled', '1': 'enabled'},
              unmapped_regions=[[2, 255]]),
        field('ED', 8, divisor=2, unit='percent'),
        field('temperature-table', 9, unmapped_regions=[[4, 255]], mappings={
            '0': {'label': 'standard3K3', 'candidate_celsius_range': [-13.5, 116]},
            '1': {'label': 'extended1K', 'candidate_celsius_range': [-20, 155]},
            '2': {'label': 'low-temperature15K', 'candidate_celsius_range': [-39, 80]},
            '3': {'label': 'standard1K', 'candidate_celsius_range': [-13.9, 130]}}),
    ]
    positive = [field('ADC', 3, 2, 1023)]
    for name, pos in [('temperature1', 5), ('temperature2', 7),
                      ('temperature3', 9), ('temperature4', 11)]:
        positive.append(field(name, pos, 2, 3200, True, 16, 'degrees_C',
                              candidate_physical_domain=[0, 200], sentinel=None))
    positive += [field('reserved', 13, reserved_regions=[[13, 1]]),
                 field('impeller', 14, 2, 1000, unit='Hz'),
                 field('vortex', 16, 2, unit='Hz', raw_domain=None,
                       candidate_operational_domain=None,
                       candidate_hysteresis_hz=None, sentinel=None)]
    entries = []
    for alternative, direction, extent, fields, reserved in [
        ('request', 'request', 10, request, []),
        ('positive', 'response', 18, positive, [[13, 1]]),
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
                             'signed_carrier_does_not_admit_negative_values',
                             'vortex_domains_and_hysteresis_unknown'],
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
        for name in ('PWM1', 'PWM2', 'ED'):
            with self.subTest(field=name):
                f = self.field('request', name)
                self.assertEqual(candidate(f, bytes.fromhex('FF')), 127.5)
                self.assertTrue(inside(f['raw_domain'], 255))

    def test_stepper_boundaries(self):
        f = self.field('request', 'stepper')
        for raw, steps, unmapped, label in [
            (240, True, False, None), (241, False, True, None),
            (254, False, True, None), (255, False, False, 'calibrate/go-to-zero')]:
            with self.subTest(raw=raw):
                self.assertEqual(inside(f['steps_domain'], raw), steps)
                self.assertEqual(inside(f['unmapped_regions'][0], raw), unmapped)
                self.assertEqual(f['mappings'].get(str(raw)), label)

    def test_temperature_carriers(self):
        for name in ('temperature1', 'temperature2', 'temperature3', 'temperature4'):
            f = self.field('positive', name)
            for raw, carrier, result, valid in [
                ('00 0C', 3072, 192, True), ('FF FF', -1, -0.0625, False),
                ('00 00', 0, 0, True), ('80 0C', 3200, 200, True),
                ('81 0C', 3201, 200.0625, False)]:
                with self.subTest(field=name, raw=raw):
                    self.assertEqual(candidate(f, bytes.fromhex(raw)), result)
                    self.assertEqual(inside(f['raw_domain'], carrier), valid)
                    self.assertEqual(inside(f['candidate_physical_domain'], result), valid)
                    self.assertIsNone(f['sentinel'])

    def test_adc_and_impeller(self):
        for name, cases in [('ADC', [('FF 03', 1023, True), ('00 04', 1024, False)]),
                            ('impeller', [('E8 03', 1000, True), ('E9 03', 1001, False)])]:
            f = self.field('positive', name)
            for raw, value, valid in cases:
                with self.subTest(field=name, raw=raw):
                    self.assertEqual(candidate(f, bytes.fromhex(raw)), value)
                    self.assertEqual(inside(f['raw_domain'], value), valid)

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
            'relay | 3 | u8 | 0..255 | raw; bit roles Unknown | 0',
            'PWM1 | 4 | u8 | 0..255 | raw/2 percent; 0..127.5 | 0',
            'PWM2 | 5 | u8 | 0..255 | raw/2 percent; 0..127.5 | 0',
            'stepper | 6 | u8 | 0..255 | 0..240 steps; 241..254 unmapped; 255 calibrate/go-to-zero | 0',
            'LED | 7 | u8 | 0..255 | 0 disabled; 1 enabled; 2..255 unmapped | 0',
            'ED | 8 | u8 | 0..255 | raw/2 percent; 0..127.5 | 0',
            'temperature-table | 9 | u8 | 0..255 | labels below; 4..255 unmapped | 0']]
        labels = [['Temperature-table raw', 'Candidate label', 'Candidate range (degrees C)', 'Grade']]
        for raw, label, domain in [('0', 'standard3K3', '-13.5..116'),
                                   ('1', 'extended1K', '-20..155'),
                                   ('2', 'low-temperature15K', '-39..80'),
                                   ('3', 'standard1K', '-13.9..130')]:
            labels.append([raw, label, domain, 'Hypothesis'])
        positive = [header, ['ADC', '3', 'u16 LE', '0..1023', 'raw quantity; unit Unknown', '0']]
        for name, pos in [('temperature1', '5'), ('temperature2', '7'),
                          ('temperature3', '9'), ('temperature4', '11')]:
            positive.append([name, pos, 'i16 LE', '0..3200', 'raw/16 degrees C; 0..200', '0'])
        positive += [
            ['reserved', '13', 'u8', '0..255', 'raw; meaning Unknown', '0'],
            ['impeller', '14', 'u16 LE', '0..1000', 'Hz', '0'],
            ['vortex', '16', 'u16 LE', 'Unknown',
             'Hz; operational domain and hysteresis Unknown', '0']]
        self.assertEqual(tables(self.page), [identity, request, labels, positive])

    def test_page_grade_boundaries(self):
        text = ' '.join(self.page.split())
        for phrase in [
            'All field interpretations below are **Hypothesis**, unconfirmed on the wire.',
            '**Proven** applies only to their checked software representation and arithmetic.',
            'Physical qualification is **Unknown**.',
            'these declarations grant no runtime capability or write admission.',
            'Every row is **Hypothesis**.',
            'Absence does not mean zero length.',
            'Zero is not an established sentinel.',
            'Signed temperature carriers do not admit negative values into the declared domain.',
            'independent physical channel behavior is **Unknown**.',
            'Native adaptation, physical lengths, peer effects, device support and physical qualification remain **Unknown**.',
            'Do not clip at 100 or interpret `FF` as unavailable.',
            'Raw `FF` for either PWM label or ED gives candidate 127.5 percent.',
            'ADC raw 1023 lies inside its declared domain and 1024 lies outside.',
            'Temperature bytes `00 0C` carry 3072, giving candidate 192 degrees C inside both declared ranges.',
            'Bytes `FF FF` carry signed -1, giving -0.0625 degrees C outside the declared domain;',
            'its declared raw domain, operational domain and hysteresis remain **Unknown** because the linked overview supplies no threshold evidence.',
            'Vortex carrier values are preserved without classifying them as inside or outside an operational domain.',
            'Remaining selectors, address-space semantics and support remain **Unknown**',
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        self.assertEqual(text.count('Every row is **Hypothesis**.'), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
