"""Independent synthetic metadata/document checks, not library execution."""
import copy
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
NATIVE = Path('protocols/vaillant/ebus-b524-energy-roles.md')
FIXTURE = Path('protocols/vaillant/fixtures/aj02_b524_energy_roles.json')
API = Path('architecture/aj02-b524-energy-roles-api.md')

# Literal expectations are independent of the fixture and both pages.
TARGETS = [
    ('energy-setpoint', 1, 4, 'setpoint', 'binary32', 4),
    ('energy-hysteresis', 0, 39, 'hysteresis', 'binary32', 4),
    ('energy-control', 1, 13, 'control', None, None),
    ('energy-offset', 0, 162, 'offset', 'binary32', 4),
    ('energy-activation', 0, 182, 'activation', 'byte', 1),
]
NATIVE_ROWS = [
    ['energy-setpoint', '02', '01', 'FF', '0004', 'setpoint', 'binary32', '4', 'Hypothesis'],
    ['energy-hysteresis', '02', '00', 'FF', '0027', 'hysteresis', 'binary32', '4', 'Hypothesis'],
    ['energy-control', '02', '01', 'FF', '000D', 'control', 'Unknown', 'Unknown', 'Hypothesis'],
    ['energy-offset', '02', '00', 'FF', '00A2', 'offset', 'binary32', '4', 'Hypothesis'],
    ['energy-activation', '02', '00', 'FF', '00B6', 'activation', 'byte', '1', 'Hypothesis'],
]
UNKNOWN_ROWS = [[name, 'Unknown'] for name in (
    'Binary32 byte order', 'Field offsets', 'Control enumeration', 'Native units',
    'Response forms', 'Installed capability', 'Applied state')]
CONTEXT = {
    'readback_instance': 0, 'physical_qualification': 'Unknown',
    'applied_state': 'Unknown', 'installed_capability': 'Unknown',
    'metadata_limit_grade': 'Proven', 'metadata_establishes_applied_state': False,
    'metadata_establishes_installed_capability': False, 'preserve_raw': True,
    'preserve_partial_last_known_good': True, 'admit_on_invalid_evidence': False,
}
UNKNOWNS = dict.fromkeys(('binary32_byte_order', 'field_offsets',
                          'control_enumeration', 'native_units', 'response_forms'))
AXES = ('family', 'variant', 'primary', 'secondary', 'operation', 'direction',
        'field', 'group', 'requested_instance', 'register', 'command_role')
API_ROWS = [
    ['Ab95Family', 'string', 'exact family'],
    ['Ab95Variant', 'string', 'exact variant'],
    ['Ab95Primary', 'uint8', 'exact primary service'],
    ['Ab95Secondary', '*uint8', 'absent differs from explicit zero'],
    ['Ab95Operation', '*uint8', 'opcode; absent differs from explicit zero'],
    ['Ab95Direction', '*string', 'absent differs from supplied direction'],
    ['Ab95Field', 'string', 'exact field'],
    ['Ab95Group', '*uint8', 'absent differs from explicit zero'],
    ['Ab95RequestedInstance', '*uint8', 'absent differs from explicit zero'],
    ['Ab95Register', '*uint16', 'full register; absent differs from explicit zero'],
    ['Ab95CommandRole', '*string', 'absent differs from supplied command role'],
]


def expected_entries():
    return [dict(key=dict(family='Vaillant controller family', variant='local-energy',
                          primary=181, secondary=36, operation=2, direction='command',
                          field=field, group=group, requested_instance=255,
                          register=register, command_role=role),
                 grade='Hypothesis', codec=codec, width_bytes=width)
            for role, group, register, field, codec, width in TARGETS]


def tables(text):
    result, current = [], []
    for line in text.splitlines() + ['']:
        if line.startswith('|'):
            current.append([cell.strip() for cell in line.strip('|').split('|')])
        elif current:
            result.append(current[2:])
            current = []
    return result


def metadata_matches(entries, key):
    """Test-only exact metadata selection; no production API is implemented."""
    return [entry for entry in entries if entry['key'] == key]


class EnergyRolesTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / FIXTURE).read_text())
        self.native = (ROOT / NATIVE).read_text()
        self.api = (ROOT / API).read_text()

    def check_data(self, data):
        self.assertEqual(data, dict(synthetic_only=True, entries=expected_entries(),
                                    context=CONTEXT, unknowns=UNKNOWNS))

    def test_five_independent_targets_and_native_tables(self):
        self.check_data(self.data)
        self.assertEqual(tables(self.native), [NATIVE_ROWS, UNKNOWN_ROWS])
        self.assertEqual(len(self.data['entries']), 5)
        self.assertEqual([entry['width_bytes'] for entry in self.data['entries']],
                         [4, 4, None, 4, 1])
        for expected in expected_entries():
            self.assertEqual(metadata_matches(self.data['entries'], expected['key']),
                             [expected])

    def test_every_key_axis_independently_misses(self):
        # Each field is varied on every target, including the zero-valued groups.
        for expected in expected_entries():
            for axis in AXES:
                original = expected['key'][axis]
                changed = (original + 1 if isinstance(original, int)
                           else 'other-' + original)
                alternatives = [changed, None]
                if axis == 'requested_instance':
                    alternatives.append(0)  # Readback must not become command FF.
                if axis == 'operation':
                    alternatives.append(6)  # Remote namespace never aliases local.
                if isinstance(original, int) and original != 0:
                    alternatives.append(0)
                for value in alternatives:
                    with self.subTest(role=expected['key']['command_role'],
                                      axis=axis, value=value):
                        key = copy.deepcopy(expected['key'])
                        key[axis] = value
                        self.assertEqual(metadata_matches(self.data['entries'], key), [])
                        mutant = copy.deepcopy(self.data)
                        index = expected_entries().index(expected)
                        mutant['entries'][index]['key'][axis] = value
                        with self.assertRaises(AssertionError):
                            self.check_data(mutant)
            self.assertEqual(metadata_matches(self.data['entries'], expected['key']),
                             [expected])  # Valid controls survive negative cases.

    def test_each_role_codec_width_and_grade_is_sensitive(self):
        for index in range(5):
            for field, value in (('grade', 'Proven'), ('codec', 'binary32'),
                                 ('width_bytes', 4)):
                # Scalars need distinct mutations too; never count a no-op kill.
                if self.data['entries'][index][field] == value:
                    value = None
                with self.subTest(index=index, field=field):
                    mutant = copy.deepcopy(self.data)
                    mutant['entries'][index][field] = value
                    with self.assertRaises(AssertionError):
                        self.check_data(mutant)
            mutant = copy.deepcopy(self.data)
            del mutant['entries'][index]
            with self.assertRaises(AssertionError):
                self.check_data(mutant)
        self.check_data(copy.deepcopy(self.data))

    def test_all_unknowns_and_independent_predicates_are_sensitive(self):
        for section in ('context', 'unknowns'):
            for field, original in self.data[section].items():
                value = not original if isinstance(original, bool) else 'fabricated'
                with self.subTest(section=section, field=field):
                    mutant = copy.deepcopy(self.data)
                    mutant[section][field] = value
                    with self.assertRaises(AssertionError):
                        self.check_data(mutant)
        mutant = copy.deepcopy(self.data)
        mutant['synthetic_only'] = False
        with self.assertRaises(AssertionError):
            self.check_data(mutant)

    def test_every_native_table_cell_is_sensitive(self):
        expected = [NATIVE_ROWS, UNKNOWN_ROWS]
        self.assertEqual(tables(self.native), expected)
        for table, rows in enumerate(expected):
            for row, cells in enumerate(rows):
                for column in range(len(cells)):
                    with self.subTest(table=table, row=row, column=column):
                        mutant = tables(self.native)
                        mutant[table][row][column] = 'fabricated'
                        with self.assertRaises(AssertionError):
                            self.assertEqual(mutant, expected)

    def test_native_scope_and_evidence_limits(self):
        for phrase in ('comes first', 'OP02 and OP06 are independent namespaces',
                       'not captures, complete telegrams or sendable packets',
                       'readback context uses instance `00`',
                       'must not replace requested instance\n`FF`',
                       'metadata lookup cannot establish applied state or installed',
                       'capability', 'physical qualification, which remains Unknown',
                       'control codec and width remain unprovided',
                       'No activation\nvalues or control enumeration',
                       'Preserve raw values alongside partial interpretations',
                       'last-known-good partial state', 'uncertain freshness',
                       'Missing or malformed evidence withholds a usable claim',
                       'No command builder or writer is included'):
            self.assertIn(phrase, self.native)
        for term in ('Ab95', 'GraphQL', 'MCP', 'CLI', 'unittest', 'ebusd',
                     'Helianthus', 'API'):
            self.assertNotIn(term, self.native)
        for link in re.findall(r'\]\(([^)]+)\)', self.native):
            resolved = (ROOT / NATIVE.parent / link.split('#')[0]).resolve()
            self.assertTrue(resolved.is_relative_to(ROOT / 'protocols') or
                            resolved.is_relative_to(ROOT / 'types'))
            self.assertTrue(resolved.is_file())

    def test_exact_api_signatures_and_all_key_fields(self):
        self.assertEqual([line for line in self.api.splitlines()
                          if line.startswith('func ')], [
            'func Ab95Entries() ([]Ab95Entry, error)',
            'func Ab95Lookup(ab95Key Ab95Key) (Ab95Entry, bool, error)'])
        self.assertEqual(tables(self.api), [API_ROWS])
        for index, row in enumerate(API_ROWS):
            for column in range(len(row)):
                mutant = tables(self.api)
                mutant[0][index][column] = 'omitted'
                with self.assertRaises(AssertionError):
                    self.assertEqual(mutant, [API_ROWS])

    def test_api_ownership_errors_grades_and_compatibility(self):
        for phrase in ('Ab95Entry', 'Ab95Key', 'Ab95Grade', 'Ab95Codec',
                       'Ab95WidthBytes', 'Ab95Raw', 'Ab95UnknownMetadata',
                       'Ab95PhysicalQualification', 'ab95 or Ab95 prefix',
                       'No axis is a wildcard', 'absence differs\nfrom explicit zero',
                       'Readback instance 00 never substitutes',
                       'OP06 never aliases OP02', 'five target mappings remain Hypothesis',
                       'Control codec\nand width are absent',
                       'Qualification,\napplied state and installed capability remain Unknown',
                       'independently owned nested data', 'another held result',
                       'key pointers, optional scalar\npointers, raw byte slices',
                       'unknown-metadata maps and all nested contents',
                       'Ab95Entry{}, false, nil', 'Ab95Entry{}, false, error',
                       'no usable\ncollection', 'Malformed syntax', 'trailing data',
                       'unknown fields', 'empty data', 'invalid entries',
                       'duplicate exact\nkeys fail closed',
                       'partial catalog is never admitted after failure',
                       'last-known-good partial state and raw values',
                       'without marking them fresh', 'No command builder or writer',
                       'eBUS MCP compatibility', 'GraphQL parity',
                       'before 1.0', 'before 0.9', '0.11'):
            self.assertIn(phrase, self.api)


if __name__ == '__main__':
    unittest.main()
