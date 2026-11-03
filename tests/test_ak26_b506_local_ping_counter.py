"""Offline documentation checks; these helpers are not a parser or radio counter."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/ak26_b506_local_ping_counter.md'
FIXTURE = ROOT / 'architecture/fixtures/ak26_b506_local_ping_counter.json'
UNKNOWN = {
    'line_admission_rule', 'rx_tx_selection', 'reset_conditions',
    'fallback_conditions', 'initial_state', 'native_support',
    'physical_effects', 'persistence', 'delivery',
}
MODULUS = 2 ** 32


def page_table(text, heading):
    section = text.split('| ' + heading + ' |', 1)[1].split('\n\n', 1)[0]
    result = {}
    for row in section.splitlines()[2:]:
        key, value = row.strip('|').strip().split(' | ')
        if key in result:
            raise AssertionError('duplicate table key: ' + key)
        result[key] = json.loads(value)
    return result


def advance(counter, event):
    """Declared representation: +1 modulo 2^32 only for an admitted event."""
    if event['admitted'] is True:
        return (counter + 1) % MODULUS
    return counter


def reset(context, rules):
    if rules is None:
        return {'outcome': 'Unknown', 'next': None}
    raise AssertionError('no reset rules are defined')


class LocalPingCounter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text(encoding='utf-8')
        cls.data = json.loads(FIXTURE.read_text(encoding='utf-8'))

    def test_page_tables(self):
        self.assertEqual(page_table(self.page, 'Representation key'), {
            'grade': 'Hypothesis', 'counter_type': 'unsigned32',
            'modulus': 4294967296, 'counts': 'admitted output lines',
            'increment_per_admitted_line': 1,
            'increment_per_non_admitted_line': 0,
            'overflow': 'wrap modulo 2^32',
            'text_token_role': 'opaque; not the increment amount',
            'not_counted_as': ['radio packets', 'delivered packets',
                               'parsed numeric values'],
            'wrap_is_reset': False,
        })
        self.assertEqual(page_table(self.page, 'Context key'), {
            'grade': 'Hypothesis', 'contexts': ['RX', 'TX'],
            'counters': 'separate per context', 'native_codes': None,
            'cross_context_reset': 'not assumed',
        })
        self.assertEqual(page_table(self.page, 'Property'),
                         dict.fromkeys(UNKNOWN, 'Unknown'))
        self.assertEqual(page_table(self.page, 'Representation key')['modulus'],
                         2 ** 32)

    def test_grade_and_scope(self):
        self.assertEqual(set(self.data), {'grade', 'unknown', 'events', 'reset'})
        self.assertEqual(self.data['grade'], 'Hypothesis')
        self.assertEqual(self.data['unknown'], dict.fromkeys(UNKNOWN, 'Unknown'))
        flat = ' '.join(self.page.split())
        for phrase in (
            '**Hypothesis**', 'Nothing here is stable before 1.0',
            '../protocols/vaillant/ebus-vaillant-B506.md',
            'does not count radio packets, delivered packets or parsed numeric values',
            'it is not a physical reset',
            'No hardware, transport or wall-clock procedure',
            'No parser, radio counter, transmit route',
            'roadmap wording remains 0.11',
        ):
            self.assertIn(phrase, flat)

    def test_independent_arithmetic_controls(self):
        self.assertEqual(advance(7, {'admitted': True, 'token': '100'}), 8)
        self.assertEqual(advance(7, {'admitted': False, 'token': '100'}), 7)
        self.assertEqual(advance((0xFFFFFFFF - 1), {'admitted': True, 'token': ''}),
                         0xFFFFFFFF)
        self.assertEqual(advance(0xFFFFFFFF, {'admitted': True, 'token': ''}), 0)
        self.assertEqual(advance(0xFFFFFFFF, {'admitted': False, 'token': ''}),
                         0xFFFFFFFF)

    def test_events_match_independent_arithmetic(self):
        self.assertGreaterEqual(len(self.data['events']), 8)
        for case in self.data['events']:
            with self.subTest(case['id']):
                self.assertIn(case['context'], ('RX', 'TX'))
                self.assertIsInstance(case['event']['admitted'], bool)
                self.assertIsInstance(case['event']['token'], str)
                expected = (case['start'] + 1) % MODULUS \
                    if case['event']['admitted'] else case['start']
                self.assertEqual(case['expected'], expected)
                self.assertEqual(advance(case['start'], case['event']), expected)
                self.assertTrue(0 <= case['expected'] < MODULUS)

    def test_token_is_not_increment_amount(self):
        by_id = {c['id']: c for c in self.data['events']}
        self.assertEqual(by_id['admitted-token-100']['expected'], 8)
        self.assertEqual(by_id['non-admitted-token-100']['expected'], 7)
        self.assertEqual(by_id['admitted-token-0']['expected'], 8)
        self.assertEqual(by_id['non-admitted-token-0']['expected'], 7)
        for token in ('0', '1', '100', '4294967295', 'abc'):
            self.assertEqual(advance(7, {'admitted': True, 'token': token}), 8)
            self.assertEqual(advance(7, {'admitted': False, 'token': token}), 7)

    def test_wrap_not_saturation(self):
        by_id = {c['id']: c for c in self.data['events']}
        self.assertEqual(by_id['near-wrap']['expected'], 0xFFFFFFFF)
        self.assertEqual(by_id['wrap']['expected'], 0)
        self.assertEqual(by_id['wrap-tx']['expected'], 0)
        self.assertEqual(by_id['non-admitted-at-max']['expected'], 0xFFFFFFFF)

    def test_axes_vary_independently(self):
        for context in ('RX', 'TX'):
            for start in (0, 7, (0xFFFFFFFF - 1), 0xFFFFFFFF):
                for admitted in (True, False):
                    for token in ('', '100', 'x'):
                        got = advance(start, {'admitted': admitted, 'token': token})
                        want = (start + 1) % MODULUS if admitted else start
                        self.assertEqual(got, want, (context, start, admitted, token))
        contexts = {c['context'] for c in self.data['events']}
        self.assertEqual(contexts, {'RX', 'TX'})
        self.assertEqual({c['event']['admitted'] for c in self.data['events']},
                         {True, False})

    def test_reset_stays_unknown(self):
        self.assertGreaterEqual(len(self.data['reset']), 2)
        self.assertEqual({c['context'] for c in self.data['reset']}, {'RX', 'TX'})
        for case in self.data['reset']:
            with self.subTest(case['id']):
                self.assertIsNone(case['rules'])
                self.assertEqual(case['outcome'], 'Unknown')
                self.assertIsNone(case['next'])
                self.assertEqual(reset(case['context'], case['rules']),
                                 {'outcome': 'Unknown', 'next': None})

    def test_no_delivered_packet_relabel(self):
        lowered = self.page.lower()
        self.assertIn('counts admitted output lines',
                      lowered.replace('| counts | "', 'counts ').replace('"', ''))
        self.assertNotIn('counts delivered packets', lowered)
        self.assertNotIn('counts radio packets', lowered)
        self.assertEqual(self.data['unknown']['delivery'], 'Unknown')


if __name__ == '__main__':
    unittest.main()
