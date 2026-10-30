"""Bounded synthetic candidate oracle; no production implementation is exercised."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
U32 = (1 << 32) - 1
U64 = (1 << 64) - 1
UNKNOWN = 'Unknown'

# Independent acceptance constants: do not derive expectations from the fixture.
EXPECTED = {
    'transitions': [
        ['retain', 2, 1, 2, 'FFFF', False, True],
        ['set', 0, 1, 1, 'FFFF', True, True],
        ['clear', 2, 0, 0, 'FFFF', False, False],
        ['equal_zero', 0, 0, 0, 'FFFF', False, False]],
    'selectors': [
        ['all', 2, 2, 2, 0], ['first_zero', 0, 2, 2, 9],
        ['second_zero', 2, 0, 2, 9], ['third_zero', 2, 2, 0, 9]],
    'entries': [
        [0, 2, 2, 0, 1, 2], [2, 1, 1, 0, 2, 2],
        [1, 1, 1, 0, 100, 1], [3, 0, 1, 0, 50, 1],
        [4, 1, 0, 0, 50, 1], [5, 1, 1, 1, 50, 1]],
    'limits': [
        ['less', 3, 4, 1, True], ['equal', 4, 4, 1, False],
        ['greater', 5, 4, 1, False], ['disabled', 3, 4, 0, False],
        ['disabled_equal', 4, 4, 0, False]],
    'gates': [
        ['off_true', 0, True, 0, UNKNOWN, UNKNOWN],
        ['off_false', 0, False, 0, UNKNOWN, UNKNOWN],
        ['on_true', 2, True, 2, UNKNOWN, UNKNOWN],
        ['on_false', 2, False, 1, UNKNOWN, UNKNOWN]],
    'unknown': [[key, UNKNOWN] for key in (
        'index_1', 'unregistered_update', 'result_2', 'overflow', 'units',
        'routing', 'queue', 'executor', 'freshness', 'qualification')],
    'claims': [
        ['normal_loop', 'Hypothesis'], ['cached_helper', 'Hypothesis'],
        ['selector', 'Hypothesis'], ['effective_limit', 'Hypothesis'],
        ['requested_state', 'Hypothesis'], ['synthetic_representation', 'Proven']],
}
HEADERS = {
    'transitions': ['case', 'prior', 'result', 'next', 'leading_store', 'helper', 'whole'],
    'selectors': ['case', 'field_a', 'field_b', 'field_c', 'selected'],
    'entries': ['index', 'registered', 'capability', 'failure', 'tokens', 'maximum'],
    'limits': ['case', 'token_sum', 'maximum_sum', 'limited_u32', 'effective'],
    'gates': ['case', 'gate_byte', 'effective', 'requested', 'feedback', 'applied'],
    'unknown': ['branch', 'result'], 'claims': ['claim', 'grade'],
}


def uint(value, maximum):
    return type(value) is int and 0 <= value <= maximum


def transition(registered, prior, result):
    events = [('store', 'FFFF')]
    if (not uint(registered, U32) or not registered or not uint(prior, U32)
            or type(result) is not int):
        outcome = UNKNOWN
    elif result == 0:
        outcome = 0
    elif result == 1:
        outcome = 1 if prior == 0 else prior
    else:
        outcome = UNKNOWN
    events.append(('capability', outcome))
    return events


def helper(value):
    if not uint(value, U32):
        return UNKNOWN
    return bool(value & 1)


def selector(a, b, c):
    if not all(uint(value, U32) for value in (a, b, c)):
        return UNKNOWN
    return 0 if all(value != 0 for value in (a, b, c)) else 9


def ordinary_sums(entries):
    selected = []
    tokens = maximum = 0
    seen = set()
    for index, registered, capability, failure, token, limit in entries:
        if index in seen or not uint(index, U32):
            return UNKNOWN
        seen.add(index)
        if index == 1:
            continue  # Its separate branch has no supplied formula.
        if not all(uint(v, U32) for v in (registered, capability, failure)):
            return UNKNOWN
        if not uint(token, U64) or not uint(limit, U64):
            return UNKNOWN
        if registered != 0 and capability != 0 and failure == 0:
            selected.append(index)
            tokens += token
            maximum += limit
    if tokens > U64 or maximum > U64:
        return UNKNOWN
    return selected, tokens, maximum


def effective(tokens, maximum, limited):
    if not (uint(tokens, U64) and uint(maximum, U64) and uint(limited, U32)):
        return UNKNOWN
    return tokens < maximum and limited != 0


def request(gate, effect):
    if not uint(gate, 255):
        state = UNKNOWN
    elif gate == 0:
        state = 0
    elif type(effect) is bool:
        state = 1 + int(effect)
    else:
        state = UNKNOWN
    return state, UNKNOWN, UNKNOWN


class CandidatePredicates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((ROOT / 'architecture/fixtures/ai27_b531_local_predicates.json').read_text())
        cls.page = (ROOT / 'architecture/b531_local_predicates.md').read_text()

    def test_tables_and_fixture_independent_constants(self):
        # Exact scalar serialization also distinguishes booleans from integers.
        self.assertEqual(list(self.fixture), list(EXPECTED))
        for name, expected in EXPECTED.items():
            with self.subTest(table=name):
                self.assertEqual(json.dumps(self.fixture[name]), json.dumps(expected))
                section = self.page.split('### ' + name + '\n\n', 1)[1].split('\n\n', 1)[0]
                lines = section.splitlines()
                self.assertEqual(lines[0], '| ' + ' | '.join(HEADERS[name]) + ' |')
                self.assertEqual(lines[1], '| ' + ' | '.join(['---'] * len(HEADERS[name])) + ' |')
                actual = [[json.loads(c.strip()) for c in line.strip('|').split('|')]
                          for line in lines[2:]]
                self.assertEqual(json.dumps(actual), json.dumps(expected))

    def test_transitions_and_unconditional_store_order(self):
        for name, prior, result, after, marker, bit, whole in self.fixture['transitions']:
            for registered in (1, 2, U32):
                with self.subTest(case=name, registered=registered):
                    self.assertEqual(transition(registered, prior, result),
                                     [('store', marker), ('capability', after)])
                    self.assertIs(helper(after), bit)
                    self.assertIs(after != 0, whole)
        for registered, prior, result in ((0, 2, 1), (1, 2, 2), (1, -1, 1)):
            self.assertEqual(transition(registered, prior, result),
                             [('store', 'FFFF'), ('capability', UNKNOWN)])
        self.assertEqual(transition(2, U32, 1)[1], ('capability', U32))

    def test_transition_rejects_non_integer_results(self):
        for result in (True, False, 0.0, 1.0, '1', None):
            with self.subTest(result=result):
                self.assertEqual(transition(1, 2, result),
                                 [('store', 'FFFF'), ('capability', UNKNOWN)])

    def test_helper_unsigned_range(self):
        for value, expected in ((0, False), (1, True), (2, False), (U32, True)):
            self.assertIs(helper(value), expected)
        for invalid in (-1, U32 + 1, True, False, 1.0, '1', None):
            with self.subTest(invalid=invalid):
                self.assertEqual(helper(invalid), UNKNOWN)

    def test_selector_fields_independently(self):
        for name, a, b, c, expected in self.fixture['selectors']:
            with self.subTest(case=name):
                self.assertEqual(selector(a, b, c), expected)
        for axis in range(3):
            fields = [1, 1, 1]
            fields[axis] = 2
            self.assertEqual(selector(*fields), 0)
            fields[axis] = 0
            self.assertEqual(selector(*fields), 9)

    def test_selector_unsigned_ranges(self):
        for axis in range(3):
            fields = [1, 1, 1]
            fields[axis] = U32
            self.assertEqual(selector(*fields), 0)
            for invalid in (-1, U32 + 1, True, False, 1.0, '1', None):
                for other in (0, 1):
                    with self.subTest(axis=axis, invalid=invalid, other=other):
                        fields = [other, other, other]
                        fields[axis] = invalid
                        self.assertEqual(selector(*fields), UNKNOWN)

    def test_selection_identity_status_and_arithmetic(self):
        self.assertEqual(ordinary_sums(self.fixture['entries']), ([0, 2], 3, 4))
        control = [0, 2, 2, 0, 3, 4]
        self.assertEqual(ordinary_sums([control]), ([0], 3, 4))
        # Each field changes alone against the same valid control.
        for axis, value, expected in (
            (0, 1, ([], 0, 0)), (0, 2, ([2], 3, 4)),
            (1, 0, ([], 0, 0)), (2, 0, ([], 0, 0)),
            (3, 1, ([], 0, 0)), (4, 4, ([0], 4, 4)),
            (5, 5, ([0], 3, 5))):
            with self.subTest(axis=axis, value=value):
                row = control.copy()
                row[axis] = value
                self.assertEqual(ordinary_sums([row]), expected)
        self.assertEqual(ordinary_sums([[0, 1, 1, 0, 1 << 32, (1 << 32) + 1]]),
                         ([0], 1 << 32, (1 << 32) + 1))
        self.assertEqual(ordinary_sums([[0, 1, 1, 0, U64, U64],
                                       [2, 1, 1, 0, 1, 1]]), UNKNOWN)
        self.assertEqual(ordinary_sums([control, control]), UNKNOWN)

    def test_ordinary_token_bounds_before_eligibility(self):
        for status in ((1, 1, 0), (0, 1, 0), (1, 0, 0), (1, 1, 1)):
            for axis in (4, 5):
                for invalid in (-1, U64 + 1, True, False, 1.0, '1', None):
                    with self.subTest(status=status, axis=axis, invalid=invalid):
                        row = [0, *status, 1, 1]
                        row[axis] = invalid
                        self.assertEqual(ordinary_sums([row]), UNKNOWN)

    def test_limit_comparison_and_unsigned_ranges(self):
        for name, tokens, maximum, limited, expected in self.fixture['limits']:
            with self.subTest(case=name):
                self.assertIs(effective(tokens, maximum, limited), expected)
        self.assertIs(effective(3, 4, 2), True)
        self.assertIs(effective(U64 - 1, U64, U32), True)
        self.assertIs(effective(U64, U64, U32), False)
        for args in ((-1, 4, 1), (3, U64 + 1, 1), (3, 4, U32 + 1),
                     (True, 4, 1), (3, 4, -1)):
            self.assertEqual(effective(*args), UNKNOWN)

    def test_gate_whole_byte_and_unknown_feedback(self):
        for name, gate, effect, state, feedback, applied in self.fixture['gates']:
            with self.subTest(case=name):
                self.assertEqual(request(gate, effect), (state, feedback, applied))
        for gate in range(1, 256):
            self.assertEqual(request(gate, True), (2, UNKNOWN, UNKNOWN))
            self.assertEqual(request(gate, False), (1, UNKNOWN, UNKNOWN))
        self.assertEqual(request(2, UNKNOWN), (UNKNOWN, UNKNOWN, UNKNOWN))
        self.assertEqual(request(0, UNKNOWN), (0, UNKNOWN, UNKNOWN))
        for gate in (-1, 256):
            self.assertEqual(request(gate, True), (UNKNOWN, UNKNOWN, UNKNOWN))

    def test_unknown_branches_stay_partial(self):
        unknowns = dict(self.fixture['unknown'])
        self.assertEqual(unknowns['index_1'], UNKNOWN)
        self.assertEqual(ordinary_sums([[1, 1, 1, 0, 100, 1]]), ([], 0, 0))
        # Empty ordinary sums do not supply the missing full special-slot result.
        self.assertIs(effective(0, 0, 1), False)
        self.assertEqual(transition(0, 2, 1)[1][1], unknowns['unregistered_update'])
        self.assertEqual(transition(1, 2, 2)[1][1], unknowns['result_2'])
        self.assertEqual(effective(U64 + 1, 4, 1), unknowns['overflow'])
        for name in ('units', 'routing', 'queue', 'executor', 'freshness', 'qualification'):
            self.assertEqual(unknowns[name], UNKNOWN)


if __name__ == '__main__':
    unittest.main()
