"""Offline document/tuple contract checks; no decoder or physical qualification."""
import json
from pathlib import Path
import re
import unittest


Ab98Root = Path(__file__).resolve().parents[1]
Ab98Native = 'protocols/vaillant/ebus-b51a-diagnostic-variants.md'
Ab98Fixture = 'protocols/vaillant/fixtures/aj08_b51a_diagnostic_variants.json'
Ab98Architecture = 'architecture/aj08_b51a_diagnostic_variants_api.md'


def ab98_tables(ab98_text):
    ab98_result = []
    ab98_current = []
    for ab98_line in ab98_text.splitlines() + ['']:
        if ab98_line.startswith('|'):
            ab98_cells = [ab98_cell.strip() for ab98_cell in ab98_line.strip('|').split('|')]
            if not all(re.fullmatch(r'[-: ]+', ab98_cell) for ab98_cell in ab98_cells):
                ab98_current.append(ab98_cells)
        elif ab98_current:
            ab98_result.append(ab98_current)
            ab98_current = []
    return ab98_result


def ab98_rows(ab98_text):
    return [ab98_line.split('|') for ab98_line in ab98_text.strip().splitlines()]


class Ab98Contract(unittest.TestCase):
    @classmethod
    def setUpClass(ab98_cls):
        ab98_cls.ab98_page = (Ab98Root / Ab98Native).read_text()
        ab98_cls.ab98_api = (Ab98Root / Ab98Architecture).read_text()
        ab98_cls.ab98_fixture = json.loads((Ab98Root / Ab98Fixture).read_text())

    def test_ab98_unsupported_mappings_withheld(self):
        self.assertEqual(ab98_tables(self.ab98_page), [])
        for ab98_phrase in (
                'Their native interpretation is\n**Unknown**',
                'Exact field coordinates, encodings, domains, defaults, flag meanings,',
                'conditional layouts and replication behavior are withheld',
                'No native\nmapping is admitted by this supplement or its fixture',
                'Physical qualification and invocation are **Unknown**'):
            self.assertIn(ab98_phrase, self.ab98_page)
        self.assertNotRegex(self.ab98_page, r'Ab98|GraphQL|MCP|\bCLI\b')
        for ab98_link in re.findall(r'\]\(([^)]+)\)', self.ab98_page):
            ab98_target = (Ab98Root / Ab98Native).parent / ab98_link.split('#')[0]
            self.assertTrue(ab98_target.resolve().is_relative_to((Ab98Root / 'protocols').resolve()))
            self.assertTrue(ab98_target.exists())
        self.assertIn('admits no native entries from them', self.ab98_api)
        self.assertNotIn('are Hypothesis', self.ab98_api)

    def test_ab98_finite_api(self):
        self.assertEqual(re.findall(r'^func (\w+)\((.*)\) (.*)$', self.ab98_api, re.M), [
            ('Ab98Entries', '', '([]Ab98Entry, error)'),
            ('Ab98Lookup', 'ab98Key Ab98Key', '(Ab98Entry, bool, error)')])
        ab98_expected = ab98_rows('''
Ab98Family|string|device family
Ab98Variant|string|native variant
Ab98Primary|uint8|primary service
Ab98Secondary|*uint8|optional secondary service
Ab98Operation|*uint8|optional operation
Ab98Direction|string|request or positive
Ab98Field|string|native field
Ab98Group|*uint8|optional B524 group
Ab98RequestedInstance|*uint8|optional B524 requested instance
Ab98Register|*uint16|optional B524 register
Ab98CommandRole|*string|optional B524 command role
''')
        self.assertEqual(ab98_tables(self.ab98_api)[0][1:], ab98_expected)
        for ab98_phrase in ('Every axis participates in identity.',
                            'Pointer absence differs from explicit zero',
                            'independently owned nested\ndata',
                            'pointers, maps, slices, labels, conditions, alternatives and their nested\nfields',
                            'zero Ab98Entry, false and nil error',
                            'Ab98Entries returns no entries',
                            'false, never a successful partial admission',
                            'erase last-known-good evidence',
                            'existing eBUS MCP compatibility and GraphQL\nparity',
                            'Ab98Grade independently of Ab98MetadataPresence'):
            self.assertIn(ab98_phrase, self.ab98_api)

    def test_ab98_fixture_withholds_unsupported_cases(self):
        self.assertEqual(self.ab98_fixture, {
            'provenance': 'No traceable source supplied; unsupported mappings withheld',
            'grade': 'Unknown',
            'qualification': 'Unknown',
            'cases': {},
        })


if __name__ == '__main__':
    unittest.main()
