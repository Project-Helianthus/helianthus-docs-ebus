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

    def test_ab98_field_coordinates(self):
        ab98_expected = ab98_rows('''
01,04,05,07,08|request,positive|common|sequence|3|u8|0..255|0|always
01|request|common|flags|4|bits8|0..255|0|always
01|request|common|DSN|5|Unknown|Unknown|Unknown|always
01|request|common|start|7|Unknown|Unknown|Unknown|always
01|request|common|offset|9|Unknown|Unknown|Unknown|always
01|request|common|CRC|10|LEu16|0..65535|Unknown|always
01|positive|common|flags|4|bits8|0..255|0|always
01|positive|common|DSN|5|Unknown|Unknown|Unknown|change=1
01|positive|common|start|7|Unknown|Unknown|Unknown|change=1
01|positive|common|offset|9|Unknown|Unknown|Unknown|change=1
01|positive|common|family-code|10|u8|0..255|Unknown|always
04|request|common|level|4|u8|0..255|0|always
04|positive|common|enable-bits|4|13 bytes|104 bits|disabled|always
05|request|common|level|4|Unknown|Unknown|0|always
05|request|common|point|5|Unknown|0..99|0|always
05|positive|common|flags|4|bits8|0..255|0|always
05|positive|range|display-type|5|Unknown|Unknown|0|disabled=0
05|positive|range|value|6|LEu16|0..65535|0|disabled=0
05|positive|range|minimum|8|Unknown|Unknown|0|disabled=0
05|positive|range|maximum|10|Unknown|Unknown|0|disabled=0
05|positive|range|step|12|u8|0..255|0|disabled=0
05|positive|enum|alternatives-1..6|6..11|six u8|each 0..255|0|disabled=0
05|positive|four-byte|additional-value|6|LEu32|0..4294967295|0|disabled=0,bit3=1
05|positive|four-byte|reserved|10..12|three u8|each 0..255|0|disabled=0,bit3=1
07|request|common|flags|4|bits8|0..255|0|always
07|positive|common|replication-status|4|u8|0..255|0|always
08|request|common|target-written|4|LEu16|0..65535|0|always
08|request|common|initiator-to-write|6|LEu16|0..65535|0|always
08|request|common|configuration|8|u8|0..255|0|always
08|request|common|target-version|9|u8|0..255|0|always
08|request|common|initiator-version|10|u8|0..255|0|always
08|positive|common|initiator-written|4|Unknown|full/Unknown|0|always
08|positive|common|target-to-write|6|Unknown|full/Unknown|0|always
08|positive|common|target-version|8|u8|0..255|0|always
08|positive|common|initiator-version|9|u8|0..255|0|always
''')
        self.assertEqual(ab98_tables(self.ab98_page)[0][1:], ab98_expected)

    def test_ab98_flag_tables(self):
        ab98_expected = ab98_rows('''
01|request|0|power-on/start|Hypothesis
01|request|1|change|Hypothesis
01|request|2|CRC-support|Hypothesis
01|request|3..7|reserved|Hypothesis
01|positive|0|valid|Hypothesis
01|positive|1|invalid|Hypothesis
01|positive|2|blocked|Hypothesis
01|positive|3|change|Hypothesis
01|positive|4|denied|Hypothesis
01|positive|5|invalid-range|Hypothesis
01|positive|6|not-user-adjustable|Hypothesis
01|positive|7|reserved|Hypothesis
05|positive|0|disabled; following data omitted|Hypothesis
05|positive|1|writable|Hypothesis
05|positive|2|enum-vs-range|Hypothesis
05|positive|3|additional-four-byte/no-range; read-only over writable|Hypothesis
05|positive|4..5|reserved|Hypothesis
05|positive|6|text alternative 6|Hypothesis
05|positive|7|text alternative 7|Hypothesis
07|request|0|normal-replication|Hypothesis
07|request|1|inverted-replication|Hypothesis
07|request|2|refresh|Hypothesis
07|request|3..7|reserved|Hypothesis
''')
        self.assertEqual(ab98_tables(self.ab98_page)[1][1:], ab98_expected)
        self.assertIn('All bit defaults are false. Reserved bits remain raw.', self.ab98_page)
        self.assertIn('No flag exclusivity is\nestablished', self.ab98_page)

    def test_ab98_conflicts_and_unknowns(self):
        ab98_expected = ab98_rows('''
OP01 CRC|mirror candidate; unsupported CRC-support flag is 0|replacement number Unknown; no TTL or polling suppression|Hypothesis
OP04 enable bits|0 disabled, 1 enabled; all default disabled; 13 bytes = 104 independent bits|logical footprint 17 and separate tail (0,13,0) do not establish physical length|Hypothesis
OP05 disabled|bit0=1 omits all following data|raw partial positions remain preserved|Hypothesis
OP05 enum|six independent alternatives; repeat last when fewer; no separate current-value field|alternative selection Unknown|Hypothesis
OP05 bit3|additional-four-byte/no-range competes with read-only over writable|retain both; no selection by length or adaptation|Hypothesis
OP05 range|candidate min+n*step with n*step<=max|enforcement Unknown|Hypothesis
OP07 status|whole byte: 0 false, 1 true, default false; nonzero-truth competes with unlabeled 2..255|raw 02 unresolved; replication algorithms Unknown|Hypothesis
OP08 configuration|1 initiator-spare, 2 target-spare; named default initiator-spare conflicts with raw default 0|0 and 3..255 unmapped|Hypothesis
OP08 ownership|cross-device ownership|identity and persistence Unknown|Hypothesis
''')
        self.assertEqual(ab98_tables(self.ab98_page)[2][1:], ab98_expected)
        for ab98_phrase in ('every field\'s native interpretation\nbelow remains **Hypothesis**',
                            'Physical qualification and invocation are **Unknown**',
                            'Nothing is stable before 1.0.',
                            'Configured-register forms and previously allocated storage/save forms remain\noutside this slice'):
            self.assertIn(ab98_phrase, self.ab98_page)
        self.assertNotRegex(self.ab98_page, r'Ab98|GraphQL|MCP|\bCLI\b')
        for ab98_link in re.findall(r'\]\(([^)]+)\)', self.ab98_page):
            ab98_target = (Ab98Root / Ab98Native).parent / ab98_link.split('#')[0]
            self.assertTrue(ab98_target.resolve().is_relative_to((Ab98Root / 'protocols').resolve()))
            self.assertTrue(ab98_target.exists())

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

    def test_ab98_fixture_envelope(self):
        self.assertEqual(set(self.ab98_fixture), {'provenance', 'grade', 'qualification', 'cases'})
        self.assertEqual(self.ab98_fixture['provenance'], 'synthetic logical coordinates; not physical telegrams')
        self.assertEqual(self.ab98_fixture['grade'], 'Hypothesis')
        self.assertEqual(self.ab98_fixture['qualification'], 'Unknown')
        self.assertEqual(set(self.ab98_fixture['cases']), {'flags', 'conditional', 'enable', 'diagnostic', 'versions', 'scalars', 'status', 'configuration', 'partial'})

    def test_ab98_flag_tuples(self):
        ab98_cases = self.ab98_fixture['cases']['flags']
        ab98_expected = []
        for ab98_op, ab98_direction, ab98_names in (
            (1, 'request', ['power-on/start','change','CRC-support','reserved','reserved','reserved','reserved','reserved']),
            (1, 'positive', ['valid','invalid','blocked','change','denied','invalid-range','not-user-adjustable','reserved']),
            (5, 'positive', ['disabled; following data omitted','writable','enum-vs-range','additional-four-byte/no-range; read-only over writable','reserved','reserved','text alternative 6','text alternative 7']),
            (7, 'request', ['normal-replication','inverted-replication','refresh','reserved','reserved','reserved','reserved','reserved'])):
            for ab98_raw in [0] + [1 << ab98_bit for ab98_bit in range(8)] + [255]:
                ab98_expected.append({'tuple': ['vaillant','mirror-diagnosis',181,26,ab98_op,ab98_direction,'flags'],
                                      'raw': ab98_raw,
                                      'labels': [ab98_name for ab98_bit, ab98_name in enumerate(ab98_names) if ab98_raw & (1 << ab98_bit)]})
        self.assertEqual(ab98_cases, ab98_expected)

    def test_ab98_conditional_tuples(self):
        # Every flag combination independently varies change and all other bits.
        ab98_expected = []
        for ab98_raw in range(256):
            ab98_expected.append({'flags': ab98_raw, 'positions': {'5': 17, '7': 29, '9': 43} if ab98_raw & 8 else {}})
        self.assertEqual(self.ab98_fixture['cases']['conditional'], ab98_expected)

    def test_ab98_enable_tuples(self):
        ab98_cases = self.ab98_fixture['cases']['enable']
        self.assertEqual(len(ab98_cases), 104)
        for ab98_index, ab98_case in enumerate(ab98_cases):
            with self.subTest(ab98_bit=ab98_index):
                self.assertEqual(set(ab98_case), {'bit', 'bytes'})
                self.assertEqual(ab98_case['bit'], ab98_index)
                self.assertEqual(len(ab98_case['bytes']), 13)
                self.assertEqual(ab98_case['bytes'], [1 << (ab98_index % 8) if ab98_byte == ab98_index // 8 else 0 for ab98_byte in range(13)])

    def test_ab98_diagnostic_tuples(self):
        ab98_cases = self.ab98_fixture['cases']['diagnostic']
        self.assertEqual(ab98_cases['enum'], [11,23,37,41,59,67])
        self.assertEqual(ab98_cases['repeat_last'], [11,23,37,37,37,37])
        self.assertEqual(ab98_cases['overlap'], {'flags':8, 'positions':{'5':17,'6':35,'7':69,'8':103,'9':137,'10':171,'11':205,'12':239}, 'declarations':['range','enum','four-byte'], 'selected':None})
        self.assertEqual(ab98_cases['disabled'], [{'flags':ab98_raw,'following':{}} for ab98_raw in range(1,256,2)])
        self.assertEqual(ab98_cases['range_relation'], {'expression':'min+n*step with n*step<=max','enforcement':'Unknown'})
        self.assertEqual(ab98_cases['bit3'], ['additional-four-byte/no-range','read-only over writable'])
        self.assertEqual(set(ab98_cases), {'enum','repeat_last','overlap','disabled','range_relation','bit3'})

    def test_ab98_version_directions(self):
        self.assertEqual(self.ab98_fixture['cases']['versions'], [
            {'direction':'request','positions':{'9':41,'10':53},'target-version':41,'initiator-version':53},
            {'direction':'positive','positions':{'8':67,'9':79},'target-version':67,'initiator-version':79}])

    def test_ab98_scalars_and_partial(self):
        ab98_expected = []
        # Deliberately different field values catch position/field swaps.
        for ab98_op in (1,4,5,7,8):
            for ab98_direction, ab98_value in (('request',37),('positive',193)):
                ab98_expected.append([ab98_op,ab98_direction,'sequence',3,ab98_value])
        ab98_expected += [[4,'request','level',4,211], [5,'request','level',4,31],
                          [5,'request','point',5,99], [1,'positive','family-code',10,167],
                          [1,'request','CRC',10,[52,18]],
                          [8,'request','target-written',4,[33,67]],
                          [8,'request','initiator-to-write',6,[101,135]],
                          [8,'positive','initiator-written',4,{'raw':17,'width':'Unknown'}],
                          [8,'positive','target-to-write',6,{'raw':29,'width':'Unknown'}]]
        self.assertEqual(self.ab98_fixture['cases']['scalars'], ab98_expected)
        self.assertEqual(self.ab98_fixture['cases']['partial'], {'operation':1,'direction':'positive','positions':{'3':193,'4':8,'5':17},'missing':[7,9,10],'complete':False,'qualification':'Unknown'})

    def test_ab98_replication_and_configuration(self):
        self.assertEqual(self.ab98_fixture['cases']['status'], [
            {'raw':0,'meaning':'false'}, {'raw':1,'meaning':'true'},
            {'raw':2,'meaning':None,'competing':['nonzero-truth','unlabeled 2..255'],'algorithm':'Unknown'},
            {'raw':255,'meaning':None,'competing':['nonzero-truth','unlabeled 2..255'],'algorithm':'Unknown'}])
        self.assertEqual(self.ab98_fixture['cases']['configuration'], [
            {'raw':ab98_raw, 'meaning':{1:'initiator-spare',2:'target-spare'}.get(ab98_raw)} for ab98_raw in range(256)])


if __name__ == '__main__':
    unittest.main()
