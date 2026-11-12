"""Explicit acceptance of AE24 documents and synthetic data, not runtime coverage."""

import json
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
NATIVE = Path('protocols/vaillant/ebus-vaillant-b531-hem-power-limit.md')
LOCAL = Path('architecture/ae24-b531-local-projection.md')
FIXTURE = Path('protocols/vaillant/fixtures/ae24_b531_candidates.json')
PROJECTION = Path('architecture/fixtures/ae24_b531_local_projection.json')
UNRESOLVED = ('endpoint support; native units; correlation; reply adaptation; '
              'cache freshness; target eligibility; applied limits: Unknown')
NATIVE_HEADER = ('Grade', 'Identity', 'Direction', 'Logical position / extent',
                 'Raw type / domain', 'Native unit / scale',
                 'Sentinel / default / conflict', 'Unresolved')
LOCAL_HEADER = ('Grade', 'Identity', 'Direction', 'Logical position / extent',
                'Raw type / domain', 'Local transform / result domain',
                'Projected metadata / native unit', 'Sentinel / default / conflict',
                'Unresolved')
ARITH_HEADER = ('Case', 'Minimum raw', 'Maximum raw', 'Minimum unsigned',
                'Maximum unsigned', 'Minimum local u32', 'Maximum local u32',
                'Native unit', 'Arithmetic grade', 'Native grade')
SLOT_HEADER = ('Grade', 'Example index', 'Index domain', 'Associated quantity',
               'Value source', 'Default', 'Unresolved')
# Literal independent oracle: no decoding or scaling algorithm in this suite.
EXPECTED = (
    ('endpoints', '00 00', 'FF FF', 0, 65535, 0, 655350, 'Unknown'),
    ('independent-order', '02 00', '01 00', 2, 1, 20, 10, 'Unknown'),
    ('minimum-only', '02 00', 'FF FF', 2, 65535, 20, 655350, 'Unknown'),
    ('maximum-only', '00 00', '01 00', 0, 1, 0, 10, 'Unknown'),
)


def table(text, header):
    """Read one structured claim table without interpreting its quantities."""
    lines = text.splitlines()
    found = []
    for i, line in enumerate(lines):
        if line.startswith('|') and tuple(cell.strip() for cell in line.strip('|').split('|')) == header:
            rows = []
            for row in lines[i + 2:]:
                if not row.startswith('|'):
                    break
                rows.append(tuple(cell.strip() for cell in row.strip('|').split('|')))
            found.append(rows)
    if len(found) != 1:
        raise AssertionError('expected exactly one scoped table: ' + str(header))
    return found[0]


def check_contract(test, root):
    native = (root / NATIVE).read_text()
    local = (root / LOCAL).read_text()
    fixture = json.loads((root / FIXTURE).read_text())
    test.assertEqual(fixture['provenance'], 'synthetic only; no physical qualification')
    test.assertEqual(fixture['native_grade'], 'Hypothesis')
    test.assertEqual(fixture['native_unit'], 'Unknown')
    keys = ('id', 'minimum_raw', 'maximum_raw', 'minimum_unsigned',
            'maximum_unsigned', 'native_unit')
    test.assertTrue(all(set(row) == set(keys) for row in fixture['cases']))
    test.assertEqual(tuple(tuple(row[k] for k in keys) for row in fixture['cases']),
                     tuple(row[:5] + row[7:] for row in EXPECTED))
    projection = json.loads((root / PROJECTION).read_text())
    test.assertEqual(projection['provenance'], 'synthetic only; no physical qualification')
    test.assertEqual(projection['arithmetic_grade'], 'Proven')
    test.assertEqual(projection['native_grade'], 'Hypothesis')
    test.assertEqual(projection['native_unit'], 'Unknown')
    pkeys = ('id', 'minimum_unsigned', 'maximum_unsigned', 'minimum_times_ten', 'maximum_times_ten')
    test.assertTrue(all(set(row) == set(pkeys) for row in projection['cases']))
    test.assertEqual(tuple(tuple(row[k] for k in pkeys) for row in projection['cases']),
                     tuple((r[0], r[3], r[4], r[5], r[6]) for r in EXPECTED))
    native_rows = []
    local_rows = []
    for quantity, position in (('minimum', 'first'), ('maximum', 'second')):
        identity = 'B531 OP02 ' + quantity
        extent = position + ' quantity / 2 octets; wire offset Unknown'
        native_rows.append((
            'Hypothesis', identity, 'target to requester (candidate reply)', extent,
            'unsigned LE16 / 0..65535', 'Unknown / Unknown',
            'FFFF sentinel Unknown; default Unknown; minimum greater than maximum retained as an independent alternative',
            UNRESOLVED))
        local_rows.append((
            'Hypothesis', identity, 'local representation of candidate reply', extent,
            'unsigned LE16 / 0..65535', 'multiply by 10 into u32 / 0..655350',
            'W / Unknown', 'FFFF remains numeric; default absent; no ordering rejection',
            UNRESOLVED))
    test.assertEqual(table(native, NATIVE_HEADER), native_rows)
    test.assertEqual(table(local, LOCAL_HEADER), local_rows)
    test.assertEqual(table(local, ARITH_HEADER), [
        tuple(str(v) for v in row) + ('Proven', 'Hypothesis') for row in EXPECTED])
    test.assertEqual(table(local, SLOT_HEADER), [
        ('Hypothesis', index, '0..8 inclusive', 'maximum only', 'projected maximum u32',
         'absent', 'endpoint support; cache freshness; target eligibility; applied limits: Unknown')
        for index in ('0', '8')])
    test.assertIn('](fixtures/ae24_b531_candidates.json)', native)
    test.assertNotIn('architecture/ae24-b531-local-projection.md', native)
    test.assertIn('Logical positions below order the two candidate', native)
    test.assertIn('they are not wire offsets', native)
    test.assertIn('No native 10 W-per-count claim follows', native)
    test.assertNotIn('(**Hypothesis**: a power value in units of 10 W)', native)
    test.assertNotIn('(candidate: 10 W', native)
    test.assertIn('No actual table or cache is\nwritten', local)


class CandidateAcceptance(unittest.TestCase):
    def test_native_local_and_fixture_contract(self):
        check_contract(self, ROOT)

    def test_each_raw_quantity_varies_alone(self):
        rows = {row[0]: row for row in EXPECTED}
        baseline = rows['endpoints']
        minimum = rows['minimum-only']
        maximum = rows['maximum-only']
        self.assertEqual((baseline[2], baseline[4], baseline[6]),
                         (minimum[2], minimum[4], minimum[6]))
        self.assertEqual((baseline[1], baseline[3], baseline[5]),
                         (maximum[1], maximum[3], maximum[5]))
        self.assertEqual((minimum[1], minimum[3], minimum[5]), ('02 00', 2, 20))
        self.assertEqual((maximum[2], maximum[4], maximum[6]), ('01 00', 1, 10))

    def reject_file_mutant(self, path, old, new):
        # Disposable copies of owned documents/data only. No runtime decoder.
        with tempfile.TemporaryDirectory(prefix='ae24-', dir=os.environ.get('TMPDIR')) as tmp:
            root = Path(tmp)
            for rel in (NATIVE, LOCAL, FIXTURE, PROJECTION):
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / rel).read_bytes())
            check_contract(self, root)
            target = root / path
            text = target.read_text()
            self.assertIn(old, text, 'mutant must alter a real declaration')
            target.write_text(text.replace(old, new, 1))
            with self.assertRaises(AssertionError):
                check_contract(self, root)

    def test_signed16_mutants(self):
        for page in (NATIVE, LOCAL):
            with self.subTest(page=page):
                self.reject_file_mutant(page, 'unsigned LE16 / 0..65535', 'signed16 / -32768..32767')
        self.reject_file_mutant(FIXTURE, '"maximum_unsigned": 65535', '"maximum_unsigned": -1')

    def test_division_mutants(self):
        self.reject_file_mutant(LOCAL, 'multiply by 10 into u32 / 0..655350', 'divide by 10 into u32 / 0..6553')
        self.reject_file_mutant(PROJECTION, '"maximum_times_ten": 655350', '"maximum_times_ten": 6553')

    def test_ffff_unavailable_mutants(self):
        self.reject_file_mutant(NATIVE, 'FFFF sentinel Unknown', 'FFFF sentinel unavailable')
        self.reject_file_mutant(LOCAL, 'FFFF remains numeric', 'FFFF is unavailable')
        self.reject_file_mutant(PROJECTION, '"maximum_times_ten": 655350', '"maximum_times_ten": null')

    def test_order_enforcement_mutants(self):
        self.reject_file_mutant(NATIVE, 'minimum greater than maximum retained as an independent alternative', 'minimum must not exceed maximum')
        self.reject_file_mutant(LOCAL, 'no ordering rejection', 'require minimum<=maximum')
        self.reject_file_mutant(PROJECTION, '"minimum_times_ten": 20', '"minimum_times_ten": null')

    def test_minimum_table_mutant(self):
        self.reject_file_mutant(LOCAL, '| maximum only | projected maximum u32 |', '| minimum only | projected minimum u32 |')

    def test_native_watt_mutants(self):
        self.reject_file_mutant(NATIVE, '| Unknown / Unknown |', '| W / 10 |')
        self.reject_file_mutant(LOCAL, '| W / Unknown |', '| W / W |')
        self.reject_file_mutant(FIXTURE, '"native_unit": "Unknown"', '"native_unit": "W"')

    def test_grade_unresolved_and_index_mutants(self):
        self.reject_file_mutant(NATIVE, '| Hypothesis | B531 OP02 minimum', '| Proven | B531 OP02 minimum')
        self.reject_file_mutant(NATIVE, UNRESOLVED, 'none')
        self.reject_file_mutant(LOCAL, '| Hypothesis | 8 | 0..8 inclusive |', '| Hypothesis | 9 | 0..9 inclusive |')


if __name__ == '__main__':
    unittest.main()
