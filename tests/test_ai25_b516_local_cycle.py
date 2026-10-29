"""Synthetic candidate oracle only; no runtime or physical qualification."""
import json
import math
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
POLICY = dict(slots=9, sentinel=4294967295, threshold=2, modulus=4294967296,
              gates='registration_and_capability', positive_only=False,
              partial_sum='retain', scheduler_arguments=[1, 60])
KEYS = ('id slot registered capable outcome prior raw marker previous new '
        'diagnostic changed contribution failure').split()
# Independent expectations: changing fixture or page does not change these.
ROWS = [
    ('delta_one', 0, True, True, 'success', 10, '00003041', '00', 10, 11, 'success', False, 11, 0),
    ('delta_two', 1, True, True, 'success', 10, '00004041', '00', 10, 12, 'success', True, 12, 0),
    ('prior_sentinel', 2, True, True, 'success', 4294967295, '00000000', '00', 4294967295, 0, 'success', True, 0, 0),
    ('read_failure', 3, True, True, 'read_failure', 10, None, 'A1', 10, 4294967295, 'read_failure', True, 0, 1),
    ('parse_failure', 4, True, True, 'parse_failure', 10, 'AA', 'B2', 10, 4294967295, 'parse_failure', True, 0, 1),
    ('unregistered', 5, False, True, 'success', 10, '00004041', 'C3', None, 4294967295, 'skip_registration', None, 0, 0),
    ('incapable', 6, True, False, 'success', 10, '00004041', 'D4', None, 4294967295, 'skip_capability', None, 0, 0),
    ('decrease_one', 7, True, True, 'success', 12, '00003041', '00', 12, 11, 'success', True, 11, 0),
    ('ninth_slot', 8, True, True, 'success', 10, '00004041', '00', 10, 12, 'success', True, 12, 0),
    ('negative', 0, True, True, 'success', 10, '000080BF', 'E5', 10, None, 'Unknown', None, None, 0),
    ('nan', 1, True, True, 'success', 10, '0000C07F', 'F6', 10, None, 'Unknown', None, None, 0),
    ('unsupported_step', 2, True, True, 'unprovided', 10, None, '17', 10, None, 'Unknown', None, None, 0),
    ('wrap_large', 0, True, True, 'success', 10, 'injected_u32:FFFFFFFE', '00', 10, 4294967294, 'success', True, 4294967294, 0),
    ('wrap_small', 1, True, True, 'success', 10, '00004040', '00', 10, 3, 'success', True, 3, 0),
]
CYCLES = [
    ('partial', ['delta_one', 'read_failure'], 4, 11, 5, True),
    ('sum_wrap', ['wrap_large', 'wrap_small'], 2, 1, 0, True),
    ('counter_wrap', ['read_failure'], 4294967295, 0, 0, 'Unknown'),
    ('clean', ['delta_two'], 7, 12, 0, True),
    ('skip', ['unregistered'], 7, 0, 0, 'Unknown'),
    ('conversion_unknown', ['negative'], 7, 0, 0, 'Unknown'),
]
CYCLE_KEYS = 'id steps counter_before sum counter_after publication'.split()
OUTPUT_KEYS = 'previous new diagnostic changed contribution failure'.split()


def transition(step, policy):
    """Bounded local interpretation of injected inputs, with raw retention."""
    result = dict(previous=None, new=None, diagnostic='Unknown', changed=None,
                  contribution=None, failure=0, raw=step['raw'], marker=step['marker'],
                  slot=step['slot'])
    if (type(step['slot']) is not int or not 0 <= step['slot'] < policy['slots']
            or type(step['prior']) is not int or not 0 <= step['prior'] < policy['modulus']
            or type(step['registered']) is not bool or type(step['capable']) is not bool):
        return result
    if not step['registered'] or not step['capable']:
        result.update(new=policy['sentinel'], contribution=0)
        # Both absent is unprovided: do not invent diagnostic precedence.
        if step['registered'] != step['capable']:
            result['diagnostic'] = ('skip_registration' if not step['registered']
                                    else 'skip_capability')
        return result
    result['previous'] = step['prior']
    if step['outcome'] in ('read_failure', 'parse_failure'):
        result.update(new=policy['sentinel'], diagnostic=step['outcome'],
                      contribution=0, failure=1)
    elif step['outcome'] == 'success':
        if step['raw'] == 'injected_u32:FFFFFFFE':
            value = 4294967294
        else:
            try:
                value = struct.unpack('<f', bytes.fromhex(step['raw']))[0]
            except (TypeError, ValueError, struct.error):
                return result
            # Only integral finite nonnegative supplied conversions are bounded here.
            if (not math.isfinite(value) or value < 0 or not value.is_integer()
                    or value >= policy['modulus']):
                return result
            if policy['positive_only'] and value <= 0:
                return result
            value = int(value)
        result.update(new=value, diagnostic='success', contribution=value)
    else:
        return result
    result['changed'] = (result['previous'] == policy['sentinel'] or
                         (result['new'] - result['previous']) % policy['modulus']
                         >= policy['threshold'])
    return result


def cycle(steps, counter, policy):
    results = [transition(step, policy) for step in steps]
    failures = sum(r['failure'] for r in results)
    successes = [r['contribution'] for r in results if r['diagnostic'] == 'success']
    total = sum(successes) % policy['modulus']
    publication = True if successes and all(r['contribution'] is not None for r in results) else 'Unknown'
    if failures and policy['partial_sum'] != 'retain':
        total, publication = None, False
    return total, (counter + failures) % policy['modulus'] if failures else 0, publication


def display(value):
    if value is None:
        return 'Unknown'
    if type(value) is bool:
        return str(value).lower()
    if isinstance(value, list):
        return ','.join(map(str, value))
    return str(value)


def tables(text):
    groups, current = [], []
    for line in text.splitlines() + ['']:
        if line.startswith('|'):
            current.append([c.strip() for c in line.strip('|').split('|')])
        elif current:
            groups.append(current)
            current = []
    return groups


class LocalCycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / 'architecture/fixtures/ai25_b516_local_cycle.json').read_text())
        cls.page = (ROOT / 'architecture/b516_local_cycle.md').read_text()
        cls.steps = {s['id']: s for s in cls.fixture['steps']}

    def test_fixture_and_page_independent_contract(self):
        expected = dict(grade='Hypothesis', policy=POLICY,
                        steps=[dict(zip(KEYS, r)) for r in ROWS],
                        cycles=[dict(zip(CYCLE_KEYS, r)) for r in CYCLES])
        self.assertEqual(self.fixture, expected)
        expected_tables = [
            [['Rule', 'Value', 'Grade'], ['---'] * 3] +
            [[k, display(v), 'Hypothesis'] for k, v in POLICY.items()],
            [KEYS, ['---'] * len(KEYS)] + [[display(v) for v in r] for r in ROWS],
            [CYCLE_KEYS, ['---'] * len(CYCLE_KEYS)] + [[display(v) for v in r] for r in CYCLES],
        ]
        self.assertEqual(tables(self.page), expected_tables)
        self.assertEqual([r[1] for r in ROWS[:9]], list(range(9)))

    def test_every_step_and_raw_retention(self):
        for row in ROWS:
            with self.subTest(step=row[0]):
                result = transition(self.steps[row[0]], self.fixture['policy'])
                for key, value in zip(KEYS[8:], row[8:]):
                    self.assertEqual(result[key], value, key)
                for key in ('raw', 'marker', 'slot'):
                    self.assertEqual(result[key], self.steps[row[0]][key])

    def test_every_cycle(self):
        for name, ids, before, total, after, publication in CYCLES:
            with self.subTest(cycle=name):
                self.assertEqual(cycle([self.steps[i] for i in ids], before, self.fixture['policy']),
                                 (total, after, publication))

    def test_identity_slot_axis_and_independent_gates(self):
        control = self.steps['delta_two']
        for slot in range(9):
            result = transition(dict(control, slot=slot), POLICY)
            self.assertEqual(result['slot'], slot)
            self.assertEqual(result['new'], 12)
            self.assertEqual(result['diagnostic'], 'success')
        for slot in (-1, 9, True, '1'):
            self.assertEqual(transition(dict(control, slot=slot), POLICY)['diagnostic'], 'Unknown')
        for registered, capable, diagnostic in [(False, True, 'skip_registration'),
                                                (True, False, 'skip_capability'),
                                                (False, False, 'Unknown')]:
            result = transition(dict(control, registered=registered, capable=capable), POLICY)
            self.assertEqual(result['diagnostic'], diagnostic)
            self.assertEqual(result['new'], 4294967295)
            self.assertEqual(result['failure'], 0)
            self.assertIsNone(result['previous'])

    def test_unsigned_decrease_and_fail_closed_unknowns(self):
        self.assertEqual((11 - 12) % 4294967296, 4294967295)
        self.assertLess(11 - 12, 2)
        self.assertLess(abs(11 - 12), 2)
        self.assertTrue(transition(self.steps['decrease_one'], POLICY)['changed'])
        control = self.steps['delta_two']
        for override in ({'prior': -1}, {'prior': 4294967296}, {'registered': 1},
                         {'raw': 'AA'}, {'raw': None}, {'raw': '0000C03F'},
                         {'raw': '0000807F'}, {'raw': '0000804F'},
                         {'outcome': 'unprovided'}):
            result = transition(dict(control, **override), POLICY)
            self.assertEqual(result['diagnostic'], 'Unknown')
            self.assertIsNone(result['new'])
        self.assertEqual(cycle([self.steps['delta_one'], self.steps['nan']], 3, POLICY),
                         (11, 0, 'Unknown'))

    def test_policy_mutation_witnesses(self):
        # Reasoned oracle mutation witnesses; disposable source kills are separate.
        for key, replacement, witness in [('slots', 8, 'ninth_slot'),
                                          ('threshold', 1, 'delta_one'),
                                          ('positive_only', True, 'prior_sentinel')]:
            mutated = dict(POLICY, **{key: replacement})
            self.assertNotEqual(transition(self.steps[witness], mutated),
                                transition(self.steps[witness], POLICY))
        self.assertNotEqual(cycle([self.steps['delta_one'], self.steps['read_failure']], 4,
                                 dict(POLICY, partial_sum='withhold')), (11, 5, True))
        self.assertNotEqual(min(4294967294 + 3, 4294967295), 1)
        self.assertNotEqual(min(4294967295 + 1, 4294967295), 0)


if __name__ == '__main__':
    unittest.main()
