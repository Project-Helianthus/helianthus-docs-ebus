"""Offline contract checks; the oracles below are not a runtime feature."""
import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def refresh(outcomes, cached=None):
    attempts = 0
    result = 'failed'
    for outcome in outcomes[:2]:
        attempts += 1
        if outcome == 'success':
            result = 'success'
            break
    # A failed optional refresh must leave identification data and any
    # last-known-good state exactly as they were.
    state = copy.deepcopy(cached)
    if result == 'success':
        state = dict(state or {}, refreshed=True)
    return attempts, 'success', result, state


def forwarding(frame):
    selector = frame['variant'] == 'B' or (
        frame['variant'] == 'A' and
        (frame['operation'], frame['destination']) in
        {('0902', '35'), ('0903', '15')})
    structural = (5 <= frame['extent'] <= 21 and
                  frame['nn'] + 5 == frame['extent'] and
                  frame['request_length'] <= 16 and
                  frame['reply_length'] <= 21 and frame['role_ok'] and
                  frame['state_ok'] and frame['capacity_ok'])
    known = (frame['variant'] in {'A', 'B'} and
             frame['path'] in {'direct', 'scheduled'} and
             frame['direction'] in {'request', 'reply'})
    return selector, bool(known and selector and structural)


def identity(row):
    return (row['low'], row['high'], len(row['written']))


def verification(row, read_identity=None):
    # The 0902 read must address the same pair that was written: identical
    # bytes under a different address/count never verify.
    if not row['positive']:
        return 'not_positive'
    if read_identity is None:
        read_identity = row.get('read_identity', identity(row) if 'low' in row else None)
    bound = 'low' not in row or read_identity == identity(row)
    if row['verify'] and bound and row['written'] == row['read']:
        return 'synthetic_verified'
    return 'positive_unverified'


def merge_pair(state, row):
    retained = copy.deepcopy(state)
    key = identity(row)
    pair = {field: copy.deepcopy(row[field]) for field in
            ('low', 'high', 'written', 'positive', 'verify', 'read')}
    pair['result'] = verification(row)
    pair['last_known_good'] = copy.deepcopy(
        row['read'] if pair['result'] == 'synthetic_verified'
        else retained[key]['last_known_good'])
    retained[key] = pair
    return retained


def table(page, header):
    lines = page.splitlines()
    start = lines.index(header) + 2
    rows = []
    for line in lines[start:]:
        if not line.startswith('|'):
            break
        rows.append(tuple(cell.strip() for cell in line.strip('|').split('|')))
    return rows


class LocalPolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = (ROOT / 'architecture/aj26_standard09_local_policy.md').read_text()
        cls.fixture = json.loads((ROOT / 'architecture/fixtures/aj26_standard09_local_policy.json').read_text())

    def test_refresh_transition_and_page(self):
        expected = [(['fail', 'success'], 2, 'success'),
                    (['success'], 1, 'success'),
                    (['fail', 'fail', 'success'], 2, 'failed')]
        self.assertEqual(self.fixture['refresh_request'], dict(operation='0902', address='0000', count='09', after='identification_success', maximum_attempts=2))
        self.assertEqual(len(self.fixture['refresh']), 3)
        rows = []
        for case, (outcomes, attempts, result) in zip(self.fixture['refresh'], expected):
            self.assertEqual(case['outcomes'], outcomes)
            self.assertEqual((case['attempts'], case['identification'], case['refresh']),
                             (attempts, 'success', result))
            self.assertEqual(refresh(outcomes)[:3], (attempts, 'success', result))
            cached = {'raw': ['aa'], 'last_known_good': ['11']}
            before_state = copy.deepcopy(cached)
            _, _, _, after_state = refresh(outcomes, cached)
            self.assertEqual(cached, before_state)
            if result == 'failed':
                self.assertEqual(after_state, before_state)
            else:
                self.assertEqual(after_state, before_state | {'refreshed': True})
            rows.append((', '.join(outcomes), str(attempts), 'success', result))
        self.assertEqual(table(self.page, '| Refresh input | Attempts | Identification | Optional refresh |'), rows)
        self.assertIn('address `0000`', self.page)
        self.assertIn('count `09`', self.page)

    def test_selector_matrix_and_page(self):
        cases = {row['name']: row for row in self.fixture['forwarding']}
        self.assertEqual(len(cases), len(self.fixture['forwarding']))
        self.assertEqual(len(cases), 136)
        for variant in ('A', 'B'):
            for path in ('direct', 'scheduled'):
                for direction in ('request', 'reply'):
                    for operation, destination in (('0902', '35'), ('0903', '15')):
                        for target in (destination, '15' if destination == '35' else '35'):
                            for data in ('00', 'FF'):
                                name = '-'.join((variant, path, direction, operation, target, data))
                                case = cases[name]
                                f = case['input']
                                self.assertEqual(tuple(f[k] for k in ('variant', 'path', 'direction', 'operation', 'destination', 'data_selector')),
                                                 (variant, path, direction, operation, target, data))
                                expected = variant == 'B' or target == destination
                                self.assertEqual((case['selector'], case['admitted']), (expected, expected), name)
                                self.assertEqual(forwarding(f), (expected, expected), name)
        self.assertEqual(table(self.page, '| Variant | Operation | Destination | Selector predicate |'), [
            ('A', '0902', '35', 'pass'), ('A', '0902', '15', 'fail'),
            ('A', '0903', '15', 'pass'), ('A', '0903', '35', 'fail'),
            ('B', 'any', 'any', 'absent')])

    def test_structural_predicates_independently(self):
        cases = {row['name']: row for row in self.fixture['forwarding']}
        base = dict(extent=21, nn=16, request_length=16, reply_length=21,
                    role_ok=True, state_ok=True, capacity_ok=True)
        # Extent mutations preserve NN consistency to isolate the range gate.
        expected = {'extent-low': ({'extent': 4, 'nn': -1}, False),
                    'extent-high': ({'extent': 22, 'nn': 17}, False),
                    'extent-min': ({'extent': 5, 'nn': 0}, True),
                    'nn': ({'nn': 15}, False),
                    'request-max': ({'request_length': 17}, False),
                    'reply-max': ({'reply_length': 22}, False),
                    'role': ({'role_ok': False}, False),
                    'state': ({'state_ok': False}, False),
                    'capacity': ({'capacity_ok': False}, False)}
        for variant in ('A', 'B'):
            for path in ('direct', 'scheduled'):
                for direction in ('request', 'reply'):
                    for label, (delta, admitted) in expected.items():
                        name = '-'.join((variant, path, direction, label))
                        row = cases[name]
                        f = row['input']
                        self.assertEqual({k: f[k] for k in base}, base | delta, name)
                        self.assertEqual((f['variant'], f['path'], f['direction']), (variant, path, direction))
                        self.assertEqual((row['selector'], row['admitted']), (True, admitted), name)
                        self.assertEqual(forwarding(f), (True, admitted), name)
        self.assertEqual(table(self.page, '| Structural field | Required predicate |'), [
            ('extent', '5 <= extent <= 21'), ('nn', 'nn + 5 == extent'),
            ('request_length', 'request_length <= 16'), ('reply_length', 'reply_length <= 21'),
            ('role_ok', 'true'), ('state_ok', 'true'), ('capacity_ok', 'true')])
        for field in ('variant', 'path', 'direction'):
            frame = copy.deepcopy(self.fixture['forwarding'][0]['input'])
            frame[field] = 'unknown'
            self.assertFalse(forwarding(frame)[1], field)

    def test_verification_and_page(self):
        expected = [
            (True, True, ['11', '23'], 'positive_unverified', 'mismatch'),
            (True, True, ['11', '22'], 'synthetic_verified', 'match'),
            (True, False, ['11', '22'], 'positive_unverified', 'match'),
            (False, True, ['11', '22'], 'not_positive', 'match')]
        self.assertEqual(len(self.fixture['verification']), 4)
        rows = []
        for row, (positive, verify, read, result, comparison) in zip(self.fixture['verification'], expected):
            self.assertEqual(row, dict(positive=positive, verify=verify, written=['11', '22'], read=read, result=result))
            self.assertEqual(verification(row), result)
            rows.append((str(positive).lower(), str(verify).lower(), comparison, result))
        self.assertEqual(table(self.page, '| Positive 0903 | Verify requested | 0902 comparison | Result |'), rows)
        # Every returned data position must participate in equality.
        for index in range(2):
            row = copy.deepcopy(self.fixture['verification'][1])
            row['read'][index] = 'FF'
            self.assertEqual(verification(row), 'positive_unverified')

    def test_client_identity_raw_and_partial_states(self):
        baseline = dict(low='00', high='00', count='09', data=['11', '22'])
        expected = [baseline, baseline | {'low': '01'}, baseline | {'high': '01'},
                    baseline | {'count': '08'}, baseline | {'data': ['33', '22']}]
        self.assertEqual(self.fixture['client_reads'], expected)
        # Low, high and count are independent identity axes, never a guessed endian address.
        keys = [tuple(row[k] for k in ('low', 'high', 'count')) for row in expected[:4]]
        self.assertEqual(len(set(keys)), 4)
        self.assertNotEqual(expected[0]['data'], expected[4]['data'])
        sequence = self.fixture['partial_sequence']
        self.assertEqual(sequence, [
            dict(low='00', high='00', written=['11'], positive=True, verify=True,
                 read=['11'], result='synthetic_verified', last_known_good=['11']),
            dict(low='01', high='00', written=['22'], positive=True, verify=True,
                 read=['23'], result='positive_unverified', last_known_good=['10']),
            dict(low='00', high='01', written=['33'], positive=False, verify=False,
                 read=[], result='not_positive', last_known_good=['20'])])
        for row, outcome in zip(sequence, ('synthetic_verified', 'positive_unverified', 'not_positive')):
            self.assertEqual(verification(row), outcome)
        self.assertEqual(sequence[0]['result'], 'synthetic_verified')
        self.assertEqual([r['last_known_good'] for r in sequence], [['11'], ['10'], ['20']])
        state = {
            ('00', '00', 1): {'last_known_good': ['00']},
            ('01', '00', 1): {'last_known_good': ['10']},
            ('00', '01', 1): {'last_known_good': ['20']}}
        expected_state = copy.deepcopy(state)
        for row in sequence:
            before_state = copy.deepcopy(state)
            after_state = merge_pair(state, row)
            self.assertEqual(state, before_state)
            expected_state[identity(row)] = copy.deepcopy(row)
            # Compare every pair after each transition, including both later
            # failures: earlier outcomes and raw data must survive the merge.
            self.assertEqual(after_state, expected_state)
            state = after_state
        # Pairs with identical bytes are told apart only by read identity.
        twin = dict(sequence[0])
        self.assertEqual(verification(twin, identity(twin)), 'synthetic_verified')
        self.assertEqual(verification(twin, ('01', '00', 1)), 'positive_unverified')
        self.assertEqual(verification(twin, ('00', '01', 1)), 'positive_unverified')
        self.assertEqual(verification(twin, ('00', '00', 2)), 'positive_unverified')
        before = copy.deepcopy(self.fixture)
        for row in self.fixture['refresh']:
            refresh(row['outcomes'], {'raw': ['aa']})
        for row in self.fixture['verification']:
            verification(row)
        self.assertEqual(self.fixture, before)
        self.assertEqual(self.fixture['no_match'], dict(length=0, transmission='Unknown', ack='Unknown'))
        self.assertIn('partial successes', self.page)
        self.assertIn('last-known-good', self.page)

    def test_grades_unknowns_and_nonimplementation(self):
        self.assertEqual(self.fixture['grade'], 'Hypothesis')
        self.assertEqual(self.fixture['native_behavior'], 'Unknown')
        self.assertEqual(self.fixture['qualification'], 'Unknown')
        self.assertEqual(self.fixture['unknown'], ['physical_effect', 'periodicity', 'service_mode_meaning', 'blocksize', 'extra_endian_rules'])
        self.assertEqual(self.fixture['implemented'], dict(memory_client=False, writer=False, authorization_gate=False, forwarder=False))
        self.assertIn('candidate is **Hypothesis**', self.page)
        self.assertIn('Native behavior remains **Unknown**', self.page)
        self.assertIn('Physical qualification is independently **Unknown**', self.page)
        self.assertIn('effect, periodicity and service-mode meaning are **Unknown**', self.page)
        self.assertIn('endian rules: both are **Unknown**', self.page)
        self.assertIn('No memory client, writer, authorization gate or forwarder is implemented', self.page)
        self.assertIn('Nothing here is stable before 1.0', self.page)
        self.assertIn('No authorization gate is introduced before 0.9; any roadmap discussion belongs to 0.11.', self.page.splitlines())
        self.assertIn('0.11', self.page)
        for forbidden in ('candidate is **Proven**', 'blocksize is 16', 'periodicity is 60'):
            self.assertNotIn(forbidden, self.page)


if __name__ == '__main__':
    unittest.main()
