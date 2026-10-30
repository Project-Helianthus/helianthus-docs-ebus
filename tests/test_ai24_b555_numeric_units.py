"""Independent checks of synthetic native declarations, not device support."""
import json
import unittest
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'protocols/vaillant/ebus-b555-numeric-units.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ai24_b555_numeric_units.json'

# Deliberately independent expected constants: never generated from either input.
HEADERS = {
    'Declarations': 'id field context bits byte_order conversion raw_min raw_max numeric_min numeric_max grade'.split(),
    'Interpretations': 'id unit_code unit unit_grade replacement_raw replacement_role replacement_grade'.split(),
    'Synthetic tuples': 'id declaration raw_bytes raw_numeric_material formal_numeric contextual_branch semantic_value grade'.split(),
    'Boundaries': ['claim', 'grade'],
}
EXPECTED_TEXT = {
    'Declarations': '''u16|numeric|generic|16|little-endian|divide by 10|0|65535|0|6553.5|Hypothesis
u16-context|numeric|synthetic replacement condition|16|little-endian|divide by 10|0|65535|0|6553.5|Hypothesis
a3-min|A3 minimum setpoint|generic|8|not applicable|identity|0|255|0|255|Hypothesis
a3-max|A3 maximum setpoint|generic|8|not applicable|identity|0|255|0|255|Hypothesis
a3-qualified|A3 minimum setpoint|synthetic Celsius condition|8|not applicable|identity|0|255|0|255|Hypothesis
unit2|raw numeric material|unqualified unit 2|Unknown|Unknown|Unknown|Unknown|Unknown|Unknown|Unknown|Unknown''',
    'Interpretations': '''u16|Unknown|Unknown|Unknown|none selected|none selected|Unknown
u16-context|Unknown|Unknown|Unknown|65535|contextual replacement|Hypothesis
a3-min|Unknown|Unknown|Unknown|none selected|none selected|Unknown
a3-max|Unknown|Unknown|Unknown|none selected|none selected|Unknown
a3-qualified|Unknown|degrees C|Hypothesis|255|unavailable|Hypothesis
unit2|2|Unknown|Unknown|none selected|none selected|Unknown''',
    'Synthetic tuples': '''zero|u16|00 00|0|0|none selected|Unknown|Hypothesis
tenth|u16|01 00|1|0.1|none selected|Unknown|Hypothesis
byte-order|u16|00 01|256|25.6|none selected|Unknown|Hypothesis
maximum|u16|FF FF|65535|6553.5|none selected|Unknown|Hypothesis
replacement|u16-context|FF FF|65535|6553.5|contextual replacement|Unknown|Hypothesis
minimum-ff|a3-min|FF|255|255|none selected|Unknown|Hypothesis
maximum-ff|a3-max|FF|255|255|none selected|Unknown|Hypothesis
qualified-ff|a3-qualified|FF|255|255|unavailable|Unknown|Hypothesis
unit2-one|unit2|01 00|1|Unknown|none selected|Unknown|Unknown
unit2-ff|unit2|FF FF|65535|Unknown|none selected|Unknown|Unknown''',
    'Boundaries': '''physical qualification|Unknown
native support|Unknown
freshness|Unknown
persistence|Unknown
execution permission|Unknown
enforcement|Unknown
peer effects|Unknown
unqualified units|Unknown
sentinels outside their own contexts|Unknown''',
}
EXPECTED = {
    name: [dict(zip(HEADERS[name], line.split('|'))) for line in body.splitlines()]
    for name, body in EXPECTED_TEXT.items()
}


def page_tables(text):
    """Parse complete, ordered tables; reject missing/duplicate/extra tables."""
    tables = {}
    section = None
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('## '):
            section = line[3:]
        if line.startswith('|'):
            if section not in HEADERS or section in tables:
                raise ValueError('unexpected or duplicate table')
            header = [v.strip() for v in line.strip('|').split('|')]
            if header != HEADERS[section]:
                raise ValueError('table columns changed')
            i += 1
            separator = [v.strip() for v in lines[i].strip('|').split('|')]
            if separator != ['---'] * len(header):
                raise ValueError('table separator changed')
            i += 1
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                cells = [v.strip() for v in lines[i].strip('|').split('|')]
                if len(cells) != len(header):
                    raise ValueError('table row width changed')
                rows.append(dict(zip(header, cells)))
                i += 1
            tables[section] = rows
            continue
        i += 1
    if set(tables) != set(HEADERS):
        raise ValueError('table set changed')
    return tables


class NumericUnitsTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(FIXTURE.read_text())
        self.tables = page_tables(PAGE.read_text())

    def test_fixture_independent_constants_and_order(self):
        self.assertEqual(self.fixture, EXPECTED)

    def test_page_independent_constants_and_order(self):
        self.assertEqual(self.tables, EXPECTED)
        self.assertEqual(self.tables, self.fixture)

    def test_full_unsigned_domains_and_arithmetic(self):
        # Test both published sources, including the contextual numeric alternative.
        for source in (self.fixture, self.tables):
            for row in source['Declarations'][:5]:
                with self.subTest(source=source is self.fixture, declaration=row['id']):
                    bits = int(row['bits'])
                    self.assertEqual(bits, 16 if row['id'].startswith('u16') else 8)
                    divisor = 10 if bits == 16 else 1
                    self.assertEqual(row['conversion'], 'divide by 10' if bits == 16 else 'identity')
                    self.assertEqual(int(row['raw_min']), 0)
                    self.assertEqual(int(row['raw_max']), (1 << bits) - 1)
                    low, high = Decimal(row['numeric_min']), Decimal(row['numeric_max'])
                    self.assertEqual(low, Decimal(0))
                    self.assertEqual(high, Decimal('6553.5') if bits == 16 else Decimal(255))
                    previous = Decimal(-1)
                    for raw in range(1 << bits):
                        wire = raw.to_bytes(bits // 8, 'little')
                        decoded = int.from_bytes(wire, 'little', signed=False)
                        number = Decimal(decoded) / divisor
                        self.assertGreater(number, previous)
                        self.assertGreaterEqual(number, low)
                        self.assertLessEqual(number, high)
                        previous = number
                    self.assertEqual(previous, high)

    def test_tuple_arithmetic_and_context_selection(self):
        for source in (self.fixture, self.tables):
            declarations = {r['id']: r for r in source['Declarations']}
            meanings = {r['id']: r for r in source['Interpretations']}
            for row in source['Synthetic tuples']:
                with self.subTest(case=row['id']):
                    decl = declarations[row['declaration']]
                    meaning = meanings[row['declaration']]
                    wire = bytes.fromhex(row['raw_bytes'])
                    if decl['id'] == 'unit2':
                        # Opaque bytes and supplied material survive; no inferred decode.
                        self.assertEqual(decl['conversion'], 'Unknown')
                        self.assertEqual(row['formal_numeric'], 'Unknown')
                        self.assertEqual(meaning['unit_code'], '2')
                        self.assertEqual(meaning['unit'], 'Unknown')
                    else:
                        self.assertEqual(len(wire) * 8, int(decl['bits']))
                        raw = int.from_bytes(wire, 'little', signed=False)
                        self.assertEqual(raw, int(row['raw_numeric_material']))
                        divisor = 10 if decl['conversion'] == 'divide by 10' else 1
                        self.assertEqual(Decimal(row['formal_numeric']), Decimal(raw) / divisor)
                    selected = meaning['replacement_raw'] == row['raw_numeric_material']
                    self.assertEqual(row['contextual_branch'], meaning['replacement_role'] if selected else 'none selected')
                    self.assertEqual(row['semantic_value'], 'Unknown')

    def test_no_generic_or_cross_context_promotion(self):
        for source in (self.fixture, self.tables):
            meanings = {r['id']: r for r in source['Interpretations']}
            for key in ('u16', 'a3-min', 'a3-max', 'unit2'):
                self.assertEqual(meanings[key]['unit'], 'Unknown')
                self.assertEqual(meanings[key]['replacement_role'], 'none selected')
            self.assertEqual(meanings['a3-qualified']['unit'], 'degrees C')
            self.assertEqual(meanings['a3-qualified']['replacement_role'], 'unavailable')
            self.assertEqual(meanings['u16-context']['replacement_role'], 'contextual replacement')
            self.assertTrue(all(r['grade'] == 'Unknown' for r in source['Boundaries']))

    def test_native_links_resolve_locally(self):
        import re
        for target in re.findall(r'\]\(([^)]+)\)', PAGE.read_text()):
            self.assertNotIn(':', target)
            path = (PAGE.parent / target).resolve()
            self.assertTrue(path.is_relative_to((ROOT / 'protocols').resolve()))
            self.assertTrue(path.is_file(), target)


if __name__ == '__main__':
    unittest.main()
