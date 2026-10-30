"""Independent synthetic documentation contracts; no companion runtime execution."""
import copy
import json
import re
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE = Path('protocols/vaillant/ebus-b509-op59-quantities.md')
TUPLES = Path('protocols/vaillant/fixtures/aj16_b509_op59_quantities.json')
API = Path('architecture/aj16_b509_op59_quantities_api.md')
FIELDS = [
    ['temperature', 'signedLE16', 16, 'Celsius', 'Hypothesis'],
    ['flow', 'unsignedLE16', 100, 'litres per minute', 'Hypothesis'],
    ['volume', 'unsignedLE16', 10, 'litres', 'Hypothesis'],
    ['minimum_volume', 'raw', None, None, 'Hypothesis'],
    ['maximum_volume', 'raw', None, None, 'Hypothesis'],
]
FRAGMENTS = [
    ['temperature', 'F0 FF', -1, 'Celsius'],
    ['temperature', '00 80', -2048, 'Celsius'],
    ['flow', '7B 00', 1.23, 'litres per minute'],
    ['flow', 'FF FF', 655.35, 'litres per minute'],
    ['volume', '7B 00', 12.3, 'litres'],
    ['volume', 'FF FF', 6553.5, 'litres'],
    ['minimum_volume', 123, 123, None],
    ['maximum_volume', 456, 456, None],
]
UNKNOWN = [
    'absolute_field_positions', 'native_support', 'sentinels',
    'response_adaptation', 'direction', 'physical_qualification',
    'limit_widths', 'limit_scales', 'limit_units', 'limit_coordinates',
    'limit_enforcement',
]
SELECTOR = dict(family='vaillant', variant='B509', primary=181,
                secondary=9, operation=89, direction=None)
AXES = [
    ['Ab14Family', 'string', 'exact family'],
    ['Ab14Variant', 'string', 'exact variant'],
    ['Ab14Primary', 'uint8', 'exact primary'],
    ['Ab14Secondary', '*uint8', 'absent differs from explicit zero'],
    ['Ab14Operation', '*uint8', 'absent differs from explicit zero'],
    ['Ab14Direction', '*string', 'absent differs from supplied direction'],
    ['Ab14Field', 'string', 'exact field'],
    ['Ab14Group', '*uint8', 'absent differs from explicit zero'],
    ['Ab14RequestedInstance', '*uint8', 'absent differs from explicit zero'],
    ['Ab14Register', '*uint16', 'absent differs from explicit zero'],
    ['Ab14CommandRole', '*string', 'absent differs from supplied role'],
]
BOUNDARIES = [
    ['Ab14Grade', 'Hypothesis for each of the five fields'],
    ['Ab14MetadataPresence', 'Proven describes metadata presence only'],
    ['Ab14PhysicalQualification', 'Unknown independently of grade'],
    ['Ab14PreserveRaw', 'true independently of codec'],
    ['Ab14Position', 'absent; absolute positions are Unknown'],
    ['Ab14Label', 'absent; no fabricated label'],
    ['Ab14Unknown', 'preserves each unprovided fact independently'],
]
BEHAVIOR = [
    ['Ab14Entries success', 'five finite entries; nil error; independently owned nested data'],
    ['Ab14Lookup hit', 'matching entry; true; nil error; independently owned nested data'],
    ['Ab14Lookup well-formed miss', 'zero Ab14Entry; false; nil error'],
    ['Ab14Entries invalid embedded data', 'nil entries; non-nil error'],
    ['Ab14Lookup invalid embedded data', 'zero Ab14Entry; false; non-nil error'],
    ['returned nested data mutation', 'no change to another result or later call'],
]


def tables(text):
    groups = re.findall(r'(?:^\|.*\|\n)+', text, re.M)
    return [[list(map(str.strip, line.strip().strip('|').split('|')))
             for line in group.splitlines()][2:] for group in groups]


def display(value):
    return 'Unknown' if value is None else str(value)


class QuantityContract(unittest.TestCase):
    def validate(self, root):
        data = json.loads((root / TUPLES).read_text())
        expected = {
            'provenance': 'synthetic', 'selector': SELECTOR,
            'fields': [dict(zip(['field', 'representation', 'divisor', 'unit', 'grade'], row))
                       for row in FIELDS],
            'fragments': [dict(zip(['field', 'fragment', 'expected', 'unit'], row))
                          for row in FRAGMENTS],
            'unknown': dict.fromkeys(UNKNOWN, 'Unknown'), 'preserve_raw': True,
        }
        self.assertEqual(data, expected)
        # Equality alone treats False as zero and True as one: preserve JSON types too.
        self.assertEqual(json.dumps(data, sort_keys=True), json.dumps(expected, sort_keys=True))
        native = (root / NATIVE).read_text()
        fragment_rows = [[f, 'raw ' + str(raw) if isinstance(raw, int) else raw,
                          str(value), display(unit)] for f, raw, value, unit in FRAGMENTS]
        self.assertEqual(tables(native), [
            [[display(v) for v in row] for row in FIELDS], fragment_rows,
            [[name, 'Unknown', 'unprovided'] for name in UNKNOWN],
        ])
        self.assertIn('PB `0xB5`, SB `0x09`, operation `0x59`', native)
        self.assertNotRegex(native, r'\b(?:Ab14\w*|GraphQL|MCP|CLI|API)\b')
        for target in re.findall(r'\]\(([^)]+)\)', native):
            resolved = (ROOT / NATIVE.parent / target).resolve()
            self.assertTrue(any(resolved.is_relative_to((ROOT / area).resolve())
                                for area in ('protocols', 'types')))
            self.assertTrue(resolved.exists())
        api = (root / API).read_text()
        self.assertEqual(re.findall(r'```go\n(.*?)\n```', api, re.S), [
            'Ab14Entries() ([]Ab14Entry, error)\n'
            'Ab14Lookup(key Ab14Key) (Ab14Entry, bool, error)'])
        self.assertEqual(tables(api), [AXES, BOUNDARIES, BEHAVIOR])
        return data

    def test_tables_and_synthetic_tuples(self):
        self.validate(ROOT)

    def test_independent_arithmetic_controls(self):
        data = self.validate(ROOT)
        codecs = {row['field']: row for row in data['fields']}
        for row in data['fragments']:
            with self.subTest(field=row['field'], fragment=row['fragment']):
                codec = codecs[row['field']]
                if codec['representation'] == 'raw':
                    self.assertIsNone(codec['divisor'])
                    self.assertEqual(row['fragment'], row['expected'])
                    continue
                fragment = bytes.fromhex(row['fragment'])
                signed = codec['representation'] == 'signedLE16'
                value = Decimal(int.from_bytes(fragment, 'little', signed=signed))
                self.assertEqual(value / codec['divisor'], Decimal(str(row['expected'])))
                # Every asymmetric quantity control rejects reversed byte order.
                if fragment[0] != fragment[1]:
                    swapped = Decimal(int.from_bytes(fragment, 'big', signed=signed))
                    self.assertNotEqual(swapped / codec['divisor'], Decimal(str(row['expected'])))
                if fragment[1] & 128:
                    opposite = Decimal(int.from_bytes(fragment, 'little', signed=not signed))
                    self.assertNotEqual(opposite / codec['divisor'], Decimal(str(row['expected'])))

    def disposable(self):
        directory = tempfile.TemporaryDirectory(prefix='aj16-')
        self.addCleanup(directory.cleanup)
        root = Path(directory.name)
        for owned in (NATIVE, TUPLES, API):
            (root / owned).parent.mkdir(parents=True, exist_ok=True)
            (root / owned).write_text((ROOT / owned).read_text())
        self.validate(root)
        return root

    def reject_data_mutant(self, data):
        root = self.disposable()
        (root / TUPLES).write_text(json.dumps(data))
        with self.assertRaises(AssertionError):
            self.validate(root)

    def test_selector_axis_mutants(self):
        baseline = json.loads((ROOT / TUPLES).read_text())
        alternatives = dict(family=['other-family'], variant=['B524'], primary=[182, 0],
                            secondary=[10, None, 0], operation=[88, None, 0],
                            direction=['request', 'response', ''])
        for axis, values in alternatives.items():
            for value in values:
                with self.subTest(axis=axis, value=value):
                    mutant = copy.deepcopy(baseline)
                    mutant['selector'][axis] = value
                    self.reject_data_mutant(mutant)
        self.validate(ROOT)

    def test_field_codec_grade_and_unknown_mutants(self):
        baseline = json.loads((ROOT / TUPLES).read_text())
        for index, row in enumerate(baseline['fields']):
            changes = {'field': 'other-field', 'representation': 'signedLE16'
                       if row['representation'] != 'signedLE16' else 'unsignedLE16',
                       'unit': 'invented-unit', 'grade': 'Proven'}
            for axis, value in changes.items():
                with self.subTest(field=row['field'], axis=axis):
                    mutant = copy.deepcopy(baseline)
                    mutant['fields'][index][axis] = value
                    self.reject_data_mutant(mutant)
            for divisor in (16, 100, 10):
                if divisor != row['divisor']:
                    with self.subTest(field=row['field'], divisor=divisor):
                        mutant = copy.deepcopy(baseline)
                        mutant['fields'][index]['divisor'] = divisor
                        self.reject_data_mutant(mutant)
        for property_name in UNKNOWN:
            for value in ('Proven', 'Hypothesis'):
                with self.subTest(unknown=property_name, promotion=value):
                    mutant = copy.deepcopy(baseline)
                    mutant['unknown'][property_name] = value
                    self.reject_data_mutant(mutant)
        for property_name, value in [('preserve_raw', False), ('provenance', 'observed'),
                                     ('sentinels', {'FFFF': 'unavailable'})]:
            mutant = copy.deepcopy(baseline)
            mutant[property_name] = value
            self.reject_data_mutant(mutant)
        for index, row in enumerate(baseline['fragments']):
            for axis in ('field', 'fragment', 'expected', 'unit'):
                mutant = copy.deepcopy(baseline)
                mutant['fragments'][index][axis] = 'invented'
                with self.subTest(fragment=index, axis=axis):
                    self.reject_data_mutant(mutant)
        self.validate(ROOT)

    def test_native_table_cell_mutants(self):
        # Each field, divisor, grade, unknown predicate and arithmetic cell is bounded.
        self.reject_table_cells(NATIVE)

    def test_api_axis_boundary_and_behavior_mutants(self):
        # Includes all eleven key axes and pointer-presence/copy/error predicates.
        self.reject_table_cells(API)
        root = self.disposable()
        (root / API).write_text((root / API).read_text().replace(
            'Ab14Lookup(key Ab14Key)', 'Ab14Find(key Ab14Key)'))
        with self.assertRaises(AssertionError):
            self.validate(root)
        self.validate(ROOT)

    def reject_table_cells(self, path):
        original = (ROOT / path).read_text()
        for group, rows in enumerate(tables(original)):
            for index, row in enumerate(rows):
                line = '| ' + ' | '.join(row) + ' |'
                self.assertIn(line, original)
                for column in range(len(row)):
                    with self.subTest(path=str(path), table=group, row=index, column=column):
                        changed = row.copy()
                        changed[column] = 'invented'
                        root = self.disposable()
                        (root / path).write_text(original.replace(
                            line, '| ' + ' | '.join(changed) + ' |', 1))
                        with self.assertRaises(AssertionError):
                            self.validate(root)
        self.validate(ROOT)


if __name__ == '__main__':
    unittest.main()
