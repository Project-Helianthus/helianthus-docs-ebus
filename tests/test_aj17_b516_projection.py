"""Offline document and synthetic scenario checks; no runtime projection."""
import itertools
import json
import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LocalEnergyContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'architecture/fixtures/aj17_b516_projection.json').read_text())
        cls.page = (ROOT / 'architecture/aj17_b516_projection.md').read_text()

    def table(self, header):
        lines = self.page.splitlines()
        start = lines.index(header) + 2
        rows = []
        for line in lines[start:]:
            if not line.startswith('|'):
                break
            rows.append(tuple(cell.strip() for cell in line.strip('|').split('|')))
        return rows

    def test_grades_and_unknowns(self):
        properties = ['native_behavior', 'numeric_identity', 'receipt', 'word_offsets',
                      'word1_type', 'physical_qualification', 'variant_callback_mapping']
        self.assertEqual(self.data['grade'], 'Hypothesis')
        self.assertEqual(self.data['unknown'], dict.fromkeys(properties, 'Unknown'))
        self.assertEqual(self.table('| Property | Grade |'), [
            ('Local software candidate', 'Hypothesis'), ('Native behavior', 'Unknown'),
            ('Numeric identity', 'Unknown'), ('Receipt', 'Unknown'),
            ('Word offsets', 'Unknown'), ('Word1 type', 'Unknown'),
            ('Physical qualification', 'Unknown'), ('Variant callback mapping', 'Unknown')])
        for text in ['not a byte decoder', 'request/reply', 'eBUS/PeBUS',
                     'No offsets for either word', 'Nothing is stable before 1.0',
                     'GraphQL parity', 'MCP compatibility', 'partial last-known-good']:
            self.assertIn(text, self.page)

    def test_extent_and_raw_partial_preservation(self):
        pairs = [(8, 9), (9, 8), (9, 9), (10, 10), (0, 9), (9, 0)]
        cases = self.data['extent']
        self.assertEqual([(c['declared'], len(c['raw'])) for c in cases], pairs)
        expected_rows = []
        for c, (declared, available) in zip(cases, pairs):
            expected = 'complete' if min(declared, available) >= 9 else 'incomplete/raw'
            self.assertEqual(c['expected'], expected)
            self.assertEqual(c['raw'], list(range(available)))
            self.assertEqual(c['retained_raw'], c['raw'])
            self.assertEqual(c['last_known_good'], 7)
            self.assertEqual(c['retained_last_known_good'], 7)
            expected_rows.append((str(declared), str(available), expected))
        self.assertEqual(self.table('| Declared extent | Available bytes | Local result |'), expected_rows)

    def test_actor_ranges_and_scale(self):
        self.assertEqual(self.data['actors'], {
            'actor0': {'type': 'u32', 'unit': 'W', 'domain': [0, 1, 2], 'rating': None},
            'actor1': {'minimum': 0, 'maximum': 'maximum', 'step': 100}})
        self.assertEqual(self.table('| Actor | Type/range | Metadata/predicate |'), [
            ('actor0', 'u32; no inherited rating range', 'W; actor-domain 0..2; availability and change are independent'),
            ('actor1', '0..maximum', 'step100; separate from actor0')])
        self.assertEqual(self.data['scales'], [
            {'number': 0, 'effective_scale': 0},
            {'number': 0, 'scale': 0, 'effective_scale': 0}])
        for case in self.data['scales']:
            self.assertEqual(case.get('scale', 0), case['effective_scale'])

    def test_independent_actor_predicates(self):
        cases = self.data['actor_predicates']
        axes = list(itertools.product([-1, 0, 1, 2, 3], [False, True], [False, True]))
        self.assertEqual([(c['domain'], c['available'], c['changed']) for c in cases], axes)
        for c in cases:
            admitted = c['domain'] in range(3) and c['available']
            self.assertIs(c['admitted'], admitted)
            self.assertIs(c['change_notification'], admitted and c['changed'])

    def test_unsigned_powers(self):
        expected = [(0, 0), (2**32 - 1, None), (7, 7), (2**32 - 2, 2**32 - 2)]
        self.assertEqual([(c['raw'], c['current_power']) for c in self.data['powers']], expected)
        for c in self.data['powers']:
            self.assertEqual(c['entry'], {'participant_address': 'synthetic-a',
                                         'coupler_address': 0, 'current_power': c['current_power']})
            if c['raw'] != 2**32 - 1:
                self.assertIs(type(c['current_power']), int)
                self.assertGreaterEqual(c['current_power'], 0)
                self.assertLess(c['current_power'], 2**32)
        self.assertEqual(self.table('| Raw local power | Published current_power |'), [
            ('0', '0'), ('2^32 - 1', 'null'), ('7', '7'), ('2^32 - 2', str(2**32 - 2))])

    def test_slot_selection_and_entry_shape(self):
        cases = self.data['slots']
        axes = list(itertools.product([False, True], [False, True], ['synthetic-a', 'synthetic-b']))
        self.assertEqual([(c['registered'], c['capable'], c['participant_address']) for c in cases], axes)
        for c in cases:
            eligible = all((c['registered'], c['capable']))
            self.assertIs(c['reread'], eligible)
            expected = {'participant_address': c['participant_address'], 'coupler_address': 0,
                        'current_power': 7} if eligible else None
            self.assertEqual(c['entry'], expected)
            if eligible:
                self.assertIs(type(c['entry']['coupler_address']), int)

    def test_ack_attempt_receipt_and_variants(self):
        cases = self.data['publication']
        gates = [(True, True, True), (False, True, True), (True, False, True), (True, True, False)]
        axes = list(itertools.product([False, True], [None, 0, 7],
                                     ['callback-present', 'callback-absent'], gates))
        self.assertEqual([(c['eligible'], c['power'], c['variant'],
                           (c['membership'], c['restriction'], c['connection'])) for c in cases], axes)
        for c in cases:
            self.assertIs(c['local_ack'], True)
            self.assertEqual(c['trace'], ['local_ack', 'membership', 'restriction', 'connection'])
            self.assertIs(c['attempt'], c['eligible'] and all(
                (c['membership'], c['restriction'], c['connection'])))
            self.assertEqual(c['delivered'], 'Unknown')
            self.assertIs(c['callback_available'], c['variant'] == 'callback-present')
        self.assertEqual(self.table('| Transition | Local acknowledgement | Attempt | Delivered |'), [
            ('No eligible entries', 'true', 'false', 'Unknown'),
            ('Sole eligible null, all checks allow', 'true', 'true', 'Unknown'),
            ('Membership denied', 'true', 'false', 'Unknown'),
            ('Restriction denied', 'true', 'false', 'Unknown'),
            ('Connection denied', 'true', 'false', 'Unknown')])

    def test_serialization_and_duplicates(self):
        self.assertEqual(self.data['serialization'], [
            {'bytes': [0, 255, 7], 'count': 3, 'serialized_bytes': [0, 255, 7], 'serialized_count': 3},
            {'bytes': [], 'count': 0, 'serialized_bytes': [], 'serialized_count': 0}])
        for c in self.data['serialization']:
            self.assertEqual(bytes(c['bytes']), bytes(c['serialized_bytes']))
            self.assertEqual(len(c['bytes']), c['count'])
            self.assertEqual(c['serialized_count'], c['count'])
        self.assertEqual(self.data['duplicates'], [
            {'duplicate': False, 'materialized_states': 1},
            {'duplicate': True, 'materialized_states': 0}])

    def test_native_reference_omits_private_suffix(self):
        suffix = 'current'
        banned = re.compile(r'(?<![\w-])\w[\w-]*-' + suffix + r'\b(?!ly)', re.I)
        self.assertIsNone(banned.search(self.page))
        fixture = (ROOT / 'architecture/fixtures/aj17_b516_projection.json').read_text()
        self.assertIsNone(banned.search(fixture))
        self.assertIn(
            '[B516 energy](../protocols/vaillant/ebus-vaillant-B516-energy.md)',
            self.page)
        self.assertIn('§9', self.page)
        self.assertIn('sub-id 0x14', self.page)
        self.assertIn('current electrical power candidate', self.page)
        self.assertIn(
            '../protocols/vaillant/ebus-vaillant-B516-energy.md#11-open-questions',
            self.page)
        self.assertIsNone(re.search(r'B516-energy\.md#9-', self.page))


if __name__ == '__main__':
    unittest.main()
