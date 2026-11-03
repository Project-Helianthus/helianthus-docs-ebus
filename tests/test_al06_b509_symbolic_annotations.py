#!/usr/bin/env python3
"""Documentation checks and synthetic controls; no companion runtime imports."""
import copy
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/al06_b509_symbolic_annotations.md'
FIXTURE = ROOT / 'architecture/fixtures/al06_b509_symbolic_annotations.json'
REQUIRED = ('family', 'variant', 'primary', 'direction', 'field', 'alternative',
            'instance_scope', 'class')
OPTIONAL = ('secondary', 'operation', 'group', 'register', 'selector')
AXES = REQUIRED + OPTIONAL
BASE = dict(family='Vaillant', variant='none', primary=181, secondary=9,
            operation=13, direction='none', field='symbolic_annotation',
            alternative='none', instance_scope='none', **{'class': 'boiler'},
            selector='0x1800')


def identity(row):
    """Synthetic exact-key oracle, preserving optional presence explicitly."""
    return tuple((axis, axis in row, row.get(axis)) for axis in AXES)


def lookup(rows, key):
    matches = [row for row in rows if identity(row) == identity(key)]
    return copy.deepcopy(matches[0]) if matches else None


def expected_examples():
    # Finite controls supplied by the ticket, independent of JSON under test.
    tuples = (
        ('any', 13, None, 'read_symbolic_address', None, True),
        ('any', 14, None, 'write_symbolic_address', None, True),
        ('boiler', 13, '0x1800', 'flow_temperature', '°C', False),
        ('boiler', 13, '0xBB00', 'gas_valve_active', None, False),
        ('heat_pump', 13, '0xBB00', 'environmental_power_ratio', '%', False),
        ('heat_pump', 13, '0xE201', 'environmental_power', 'W', True),
        ('heat_pump_interface_unit', 84, '54 02 00 0D 0A',
         'compressor_speed', None, True),
        ('heat_pump_interface_unit', 84, '54 02 00 47 0A',
         'fan_1_speed', 'rpm', False),
    )
    result = []
    for cls, op, selector, name, unit, unresolved in tuples:
        row = dict(BASE, operation=op, name=name, unresolved=unresolved,
                   representation_grade='Proven', grade='Hypothesis',
                   physical_qualification='Unknown', width_bytes=None,
                   signedness='Unknown', scale=None, native_effect='Unknown',
                   raw_fallback='preserve-raw-bytes')
        row['class'] = cls
        row.pop('selector')
        if selector is not None:
            row['selector'] = selector
        if unit is not None:
            row['unit'] = unit
        row['raw_form'] = '|'.join((cls, f'{op:02X}', selector or '', name,
                                    unit or '', str(unresolved).lower()))
        result.append(row)
    return result


class AnnotationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text()
        blocks = re.findall(r'```json\n(.*?)\n```', cls.page, re.S)
        if len(blocks) != 1:
            raise AssertionError('exactly one authoritative JSON declaration required')
        cls.contract = json.loads(blocks[0])
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.rows = cls.fixture['examples']

    def test_api_declaration(self):
        self.assertEqual(self.contract['api'], {
            'entries': 'Ab40Entries() (json.RawMessage, error)',
            'lookup': 'Ab40Lookup(Ab40Key) (json.RawMessage, bool, error)',
            'key_type': 'Ab40Key', 'hit': ['copied row', True, None],
            'miss': [None, False, None], 'invalid_source': [None, False, 'error'],
            'entries_invalid_source': [None, 'error'],
            'independent_returned_memory': True})

    def test_identity_declaration(self):
        self.assertEqual(self.contract['identity'], {
            'required': list(REQUIRED), 'optional': list(OPTIONAL),
            'matching': 'exact', 'any': 'literal', 'selector_type': 'optional string',
            'absent_equals_zero': False, 'op54': 'complete opaque token'})

    def test_cardinalities_are_declared_not_example_counts(self):
        self.assertEqual(self.contract['catalog'], {
            'rows': 108, 'direction_operation_counts': {
                'none|0D': 78, 'none|0E': 1, 'none|54': 29}})
        self.assertEqual(sum(self.contract['catalog']['direction_operation_counts'].values()), 108)
        self.assertEqual(len(self.rows), 8)

    def test_grades_and_no_converter(self):
        self.assertEqual(self.contract['interpretation'], {
            'representation_grade': 'Proven', 'grade': 'Hypothesis',
            'physical_qualification': 'Unknown', 'native_effect': 'Unknown',
            'signedness': 'Unknown', 'width_bytes': None, 'scale': None,
            'automatic_codec': False, 'unit_is_converter': False})
        self.assertEqual(self.contract['admission'], {
            'construct_request': False, 'automatic_qualification': False,
            'write_admission': False, 'raw_fallback': 'preserve-raw-bytes'})

    def test_exact_examples_and_independent_metadata(self):
        self.assertEqual(self.rows, expected_examples())
        for row in self.rows:
            with self.subTest(name=row['name']):
                self.assertNotIn('register', row)
                self.assertIs(type(row['unresolved']), bool)
                self.assertIsNone(row['scale'])
                self.assertNotIn('codec', row)
                self.assertNotIn('packet', row)

    def test_every_key_axis_independently(self):
        changes = dict(family='synthetic_family', variant='synthetic_variant',
                       primary=182, secondary=10, operation=14,
                       direction='response', field='synthetic_field',
                       alternative='synthetic_alternative', group=1,
                       instance_scope='synthetic_scope', register=6144,
                       **{'class': 'heat_pump'}, selector='0x1900')
        self.assertEqual(set(changes), set(AXES))
        control = dict(BASE, marker='control')
        for axis, value in changes.items():
            with self.subTest(axis=axis):
                key = dict(BASE, **{axis: value})
                self.assertIsNotNone(lookup([control], BASE))
                self.assertIsNone(lookup([control], key))
                changed = dict(key, marker='changed')
                # Both identities are otherwise valid controls, not malformed input.
                self.assertEqual(lookup([control, changed], BASE)['marker'], 'control')
                self.assertEqual(lookup([control, changed], key)['marker'], 'changed')

    def test_optional_presence_distinct_from_zero(self):
        for axis in OPTIONAL:
            with self.subTest(axis=axis):
                absent = dict(BASE)
                absent.pop(axis, None)
                zero = dict(absent, **{axis: '0x0000' if axis == 'selector' else 0})
                rows = [dict(absent, marker='absent'), dict(zero, marker='zero')]
                self.assertEqual(lookup(rows, absent)['marker'], 'absent')
                self.assertEqual(lookup(rows, zero)['marker'], 'zero')

    def test_selectorless_and_literal_any(self):
        key = dict(BASE, **{'class': 'any'})
        key.pop('selector')
        self.assertEqual(lookup(self.rows, key)['name'], 'read_symbolic_address')
        for cls in ('boiler', 'heat_pump', 'heat_pump_interface_unit'):
            with self.subTest(cls=cls):
                self.assertIsNone(lookup(self.rows, dict(key, **{'class': cls})))
        for token in ('0x0000', '0', ''):
            with self.subTest(token=token):
                self.assertIsNone(lookup(self.rows, dict(key, selector=token)))
        self.assertIsNone(lookup(self.rows, dict(BASE, **{'class': 'any'})))
        self.assertIsNone(lookup(self.rows, dict(BASE, operation=14)))
        self.assertIsNone(lookup(self.rows, dict(BASE, **{'class': 'heat_pump'})))
        for cls, name in (('boiler', 'gas_valve_active'),
                          ('heat_pump', 'environmental_power_ratio')):
            self.assertEqual(lookup(self.rows, dict(BASE, selector='0xBB00',
                                                   **{'class': cls}))['name'], name)

    def test_each_opaque_byte_and_length(self):
        key = dict(BASE, operation=84, selector='54 02 00 0D 0A',
                   **{'class': 'heat_pump_interface_unit'})
        self.assertEqual(lookup(self.rows, key)['name'], 'compressor_speed')
        for position in range(5):
            with self.subTest(byte=position):
                tokens = ['54', '02', '00', '0D', '0A']
                tokens[position] = 'FF'
                other = dict(key, selector=' '.join(tokens))
                self.assertIsNone(lookup(self.rows, other))
                distinct = dict(other, marker='changed byte')
                self.assertEqual(lookup(self.rows + [distinct], other)['marker'], 'changed byte')
        for token in ('0x0D0A', '0D 0A', '02 00 0D 0A', '54 02 00 0D 0A 00'):
            with self.subTest(token=token):
                self.assertIsNone(lookup(self.rows, dict(key, selector=token)))

    def test_absent_metadata_and_independent_memory_model(self):
        expected = dict(BASE, unresolved=True, grade='Hypothesis', width_bytes=None,
                        synthetic_raw=[0, 255])
        self.assertEqual(self.fixture['absence_probe'], expected)
        first = lookup([self.fixture['absence_probe']], BASE)
        second = lookup([self.fixture['absence_probe']], BASE)
        self.assertNotIn('name', first)
        self.assertNotIn('unit', first)
        first['synthetic_raw'][0] = 42
        first['unresolved'] = False
        self.assertEqual(second, expected)
        self.assertEqual(lookup([self.fixture['absence_probe']], BASE), expected)
        # Metadata must not become part of identity, even when absent/changed.
        for field, value in (('name', 'synthetic'), ('unit', 'W'),
                             ('unresolved', False), ('grade', 'Unknown'),
                             ('width_bytes', 2), ('scale', 10)):
            with self.subTest(metadata=field):
                changed = dict(expected, **{field: value})
                self.assertEqual(identity(changed), identity(expected))
                self.assertEqual(lookup([changed], BASE), changed)

    def test_page_critical_qualifications(self):
        for text in (
            'Class `any` is a literal class-neutral annotation, not a wildcard.',
            'Missing name or unit stays absent.',
            'An explicit `unresolved: true` stays explicit;',
            'A unit\nis never a converter:',
            'No label determines signedness, scale, field extent or native effect.',
            'A row with only an opaque selector has no register identity.',
            'Invalid source returns no partial catalog.',
            'must merge before this page.',
            'not a complete\nfamily catalog',
            'Nothing here is stable before Helianthus 1.0.',
        ):
            with self.subTest(text=text):
                self.assertIn(text, self.page)
        self.assertIn('../protocols/vaillant/ebus-vaillant-B509.md#register-name-correspondence-fixture', self.page)
        self.assertEqual(set(self.contract), {'api', 'identity', 'catalog',
                                             'interpretation', 'admission'})
        self.assertEqual(set(self.fixture), {'purpose', 'examples', 'absence_probe'})


if __name__ == '__main__':
    unittest.main(verbosity=2)
