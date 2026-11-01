"""Synthetic B513 declarations; no wire exchange or physical qualification."""
import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-vaillant-B513.md'
FIXTURE = PAGE.parent / 'fixtures/ac10_appliance_info.json'


def field(name, position=None, default=0, mappings=None, bits=None, reserved=(), domain=(0, 255), exclusions=()):
    definition = dict(name=name, logical_position=position, width_bytes=1,
                raw_domain=list(domain), signedness='unsigned', byte_order='not-applicable',
                conversion='identity', unit=None, default=default, mappings=mappings or {},
                bits=bits or {}, reserved_bits=list(reserved), grade='Hypothesis',
                raw_fallback='preserve-raw-byte')
    if exclusions:
        definition['raw_domain_exclusions'] = list(exclusions)
    return definition


def row(operation, direction, alternative, fields, extent=None):
    return dict(family='B513', variant=None, direction=direction, service='B513',
                operation=operation, alternative=alternative,
                logical_positions_include_prefix=True, physical_offsets=None,
                extent_bytes=extent, grade='Hypothesis', raw_fallback='preserve-raw-bytes',
                fields=fields)


FLAGS = (
    ('appliance_flags', ('floor-standing', 'condensing', 'fan-assisted', 'open-vented',
                         'high-modulation-range', 'water-heater', 'step-modulation', 'ECS')),
    ('fuel_flags', ('gas', 'oil', 'ABC')),
    ('tank_flags', ('layer-tank', 'warm-start', 'external-tank', 'combination')),
    ('feature_flags', ('solar-compact', 'basic-solar', 'AAPS', 'advanced-power',
                       'partial-load', 'parameter-master')),
)


def expected():
    """Independent finite expectations, never read from the page or fixture."""
    entries = [
        row('OP05', 'request', 'request', [field('request_bits', default=8, bits={
            str(i): {'default': i == 3, 'role': 'request-data'} for i in range(6)
        }, reserved=(6, 7))]),
        row('OP05', 'response', 'positive', [field('feedback', default=None,
            mappings={'1': 'accepted'}, domain=(1, 1))]),
        row('OP05', 'response', 'negative', [field('feedback', default=None,
            mappings={'0': 'not-accepted-or-not-supported', '2..255': 'not-accepted-or-not-supported'}, exclusions=(1,))]),
        row('OP06', 'request', 'request', [
            field('light', 3, mappings={'0': 'off', '100': 'on', '255': 'replacement'}),
            field('colour', 4)]),
        row('OP06', 'response', 'positive', [field('feedback', 3, None,
            {'1': 'accepted'}, domain=(1, 1))]),
        row('OP06', 'response', 'negative', [field('feedback', 3, None,
            {'0': 'rejected', '2..255': 'rejected'}, exclusions=(1,))]),
        row('OP07', 'request', 'request', [], extent=0),
        row('OP07', 'response', 'positive', [
            field('appliance_type', 3, mappings={'0': 'modulating', '1': 'single-step', '2': 'two-step'}),
            *[field(name, pos, bits={str(i): {'label': label, 'default': False}
                 for i, label in enumerate(labels)}, reserved=range(len(labels), 8))
              for pos, (name, labels) in enumerate(FLAGS, 4)],
            field('pump_mode', 8, mappings={'0': False, '1': True}),
            field('opaque_9', 9), field('opaque_10', 10), field('opaque_11', 11)]),
    ]
    return dict(representation_grade='Proven', candidate_grade='Hypothesis',
                physical_qualification='Unknown', synthetic=True,
                coordinate_system='logical-including-prefix-not-physical-offsets',
                unknowns=['physical-adaptation', 'peer-effects', 'OP00-complement',
                          'OP04-address-dictionaries', 'unspecified-positions-and-extents', 'variant'],
                entries=entries, examples={'opaque_tail': [7, 8, 9], 'unlabeled_type': 3,
                                          'pump_mode_values': [0, 1, 2]})


def label(definition, raw):
    mappings = definition['mappings']
    if str(raw) in mappings:
        return mappings[str(raw)]
    if 2 <= raw <= 255:
        return mappings.get('2..255')
    return None


# Literal page rows intentionally independent of the JSON representation.
OP05_ROWS = '''0 | disable tank-loading/warm-start time program (display) | false
1 | disable CH time program | false
2 | disable circulation-pump program and parameters | false
3 | disable weather-compensated control and parameters | true
4 | disable drop-temperature adjustment | false
5 | weather-compensated controller connected; request data | false
6..7 | reserved | zero'''
FEEDBACK_ROWS = '''05 | response | positive | Unknown | 1 | accepted | Hypothesis
05 | response | negative | Unknown | 0, 2..255 | not-accepted-or-not-supported | Hypothesis
06 | response | positive | 3 | 1 | accepted | Hypothesis
06 | response | negative | 3 | 0, 2..255 | rejected | Hypothesis'''
LIGHT_ROWS = '''3 | light | 0 off; 100 on; 255 replacement; others unlabeled | 0 (off) | Hypothesis
4 | colour | raw u8, no colour interpretation | 0 | Hypothesis'''
INFO_ROWS = '''3 | appliance type | 0 modulating; 1 single-step; 2 two-step; others unlabeled | 0 (modulating) | Hypothesis
4 | appliance flags | bits 0..7: floor-standing, condensing, fan-assisted, open-vented, high-modulation-range, water-heater, step-modulation, ECS | 0 | Hypothesis
5 | fuel flags | bits 0/1/2: gas, oil, ABC; bits 3..7 reserved | 0 | Hypothesis
6 | tank flags | bits 0/1/2/3: layer-tank, warm-start, external-tank, combination; bits 4..7 reserved | 0 | Hypothesis
7 | feature flags | bits 0..5: solar-compact, basic-solar, AAPS, advanced-power, partial-load, parameter-master; bits 6..7 reserved | 0 | Hypothesis
8 | pump-mode Boolean | 0 false; 1 true; others unlabeled | 0 (false) | Hypothesis
9 | opaque | raw u8 | 0 | Hypothesis
10 | opaque | raw u8 | 0 | Hypothesis
11 | opaque | raw u8 | 0 | Hypothesis'''


def cells(text):
    return [[cell.strip() for cell in line.strip().strip('|').split('|')]
            for line in text.splitlines() if line.strip()]


def scoped_rows(page, start, end):
    section = page.split(start, 1)[1].split(end, 1)[0]
    return cells('\n'.join(line for line in section.splitlines()
                           if line.startswith('|') and line[1:].lstrip()[:1].isdigit()))


class ApplianceInfo(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def test_exact_native_declarations(self):
        # Catches conversions, enums, field extents, grades, alternatives and codecs.
        self.assertEqual(json.dumps(self.data, sort_keys=True),
                         json.dumps(expected(), sort_keys=True))

    def test_each_identity_axis(self):
        # Each row is a valid control; changing only one axis must break equality.
        self.assertEqual(self.data, expected())
        for index in range(8):
            for axis in ('family', 'variant', 'direction', 'service', 'operation', 'alternative'):
                with self.subTest(row=index, axis=axis):
                    changed = copy.deepcopy(self.data)
                    changed['entries'][index][axis] = 'synthetic-other'
                    with self.assertRaises(AssertionError):
                        self.assertEqual(changed, expected())
                    self.assertEqual(self.data, expected())

    def test_op05_each_bit_and_packed_default(self):
        request = self.data['entries'][0]['fields'][0]
        packed = 0
        for bit in range(8):
            with self.subTest(bit=bit):
                raw = 1 << bit
                selected = [int(key) for key in request['bits'] if raw & (1 << int(key))]
                self.assertEqual(selected, [bit] if bit < 6 else [])
                definition = request['bits'].get(str(bit))
                if bit < 6:
                    self.assertEqual(definition, {'default': bit == 3, 'role': 'request-data'})
                    packed |= int(definition['default']) << bit
                else:
                    self.assertIsNone(definition)
                    self.assertIn(bit, request['reserved_bits'])
        self.assertEqual(packed, 0x08)
        self.assertEqual(request['default'], 0x08)

    def test_feedback_alternatives_all_u8(self):
        for positive, negative, rejected in ((1, 2, 'not-accepted-or-not-supported'),
                                             (4, 5, 'rejected')):
            for raw in range(256):
                with self.subTest(positive=positive, raw=raw):
                    selected = [index for index in (positive, negative)
                                if (self.data['entries'][index]['fields'][0]['raw_domain'][0]
                                    <= raw <=
                                    self.data['entries'][index]['fields'][0]['raw_domain'][1])
                                and raw not in self.data['entries'][index]['fields'][0].get(
                                    'raw_domain_exclusions', [])]
                    self.assertEqual(selected, [positive] if raw == 1 else [negative])
                    self.assertEqual(label(self.data['entries'][positive]['fields'][0], raw),
                                     'accepted' if raw == 1 else None)
                    self.assertEqual(label(self.data['entries'][negative]['fields'][0], raw),
                                     None if raw == 1 else rejected)

    def test_light_colour_and_type(self):
        light, colour = self.data['entries'][3]['fields']
        kind = self.data['entries'][7]['fields'][0]
        for raw in range(256):
            with self.subTest(raw=raw):
                self.assertEqual(label(light, raw), {0: 'off', 100: 'on', 255: 'replacement'}.get(raw))
                self.assertIsNone(label(colour, raw))
                self.assertEqual(label(kind, raw), {0: 'modulating', 1: 'single-step', 2: 'two-step'}.get(raw))

    def test_op07_walking_bits(self):
        for offset, (_, labels) in enumerate(FLAGS, 1):
            definition = self.data['entries'][7]['fields'][offset]
            for bit in range(8):
                with self.subTest(position=offset + 3, bit=bit):
                    raw = 1 << bit
                    active = [value['label'] for key, value in definition['bits'].items()
                              if raw & (1 << int(key))]
                    self.assertEqual(active, [labels[bit]] if bit < len(labels) else [])
                    self.assertEqual(bit in definition['reserved_bits'], bit >= len(labels))

    def test_op07_boolean_and_opaque_tail(self):
        fields = self.data['entries'][7]['fields']
        for raw, want in ((0, False), (1, True), (2, None)):
            self.assertIs(label(fields[5], raw), want)
        # Logical positions only; this synthetic array is not a wire frame.
        logical = [0, 0, 0, 3, 0, 0, 0, 0, 2, 7, 8, 9]
        self.assertEqual([logical[f['logical_position']] for f in fields[6:]], [7, 8, 9])
        for definition in fields[6:]:
            self.assertEqual(definition['mappings'], {})
            self.assertEqual(definition['raw_fallback'], 'preserve-raw-byte')

    def test_page_scoped_tables(self):
        self.assertEqual(scoped_rows(self.page, '### `OP=05`', 'The packed request'), cells(OP05_ROWS))
        self.assertEqual(scoped_rows(self.page, 'The packed request', '### `OP=06`'), cells(FEEDBACK_ROWS))
        self.assertEqual(scoped_rows(self.page, '### `OP=06`', '### `OP=07`'), cells(LIGHT_ROWS))
        self.assertEqual(scoped_rows(self.page, '### `OP=07`', '### Evidence and limits'), cells(INFO_ROWS))
        self.assertIn('appliance information at logical positions 3..11 (see below); total physical extent Unknown', self.page)

    def test_page_grade_and_unknown_boundaries(self):
        for claim in (
            'All declarations in the following tables are **Hypothesis**, unconfirmed on\nthe wire.',
            'All\nfields are raw unsigned bytes with identity conversion and no known unit.',
            'The packed request default is raw `08`. Bit 5 is request data, not feedback.',
            'An unspecified position or extent is **Unknown**, not zero.',
            'The candidate request has no arguments (argument extent zero).',
            'total physical extent and physical offsets remain Unknown.',
            '**Proven** applies only to the mechanically\nchecked declared representation, never to a native exchange.',
            'Physical qualification, native\nadaptation and peer effects remain **Unknown**.',
            'OP00 complement semantics and OP04 address dictionaries remain **Unknown**',
            'no address codec is supplied.',
            'No runtime capability or write\nadmission follows from these declarations.',
            'Which one a\ntarget uses is unresolved.',
            'Another family uses the same numbers for different quantities',
        ):
            with self.subTest(claim=claim):
                self.assertIn(claim, self.page)
        self.assertIn('(fixtures/ac10_appliance_info.json)', self.page)


if __name__ == '__main__':
    unittest.main(verbosity=2)
