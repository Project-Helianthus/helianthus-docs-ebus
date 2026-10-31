"""Offline documentation contract checks; no runtime implementation or I/O on a bus."""
import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/aj24_b555_manager_predicate.md'
FIXTURE = ROOT / 'architecture/fixtures/aj24_b555_manager_predicate.json'


def table(page, header):
    lines = page.splitlines()
    start = lines.index(header) + 2
    rows = []
    for line in lines[start:]:
        if not line.startswith('|'):
            break
        rows.append([cell.strip() for cell in line.strip('|').split('|')])
    return rows


def check_contract(test, contract):
    test.assertEqual(contract, {
        'grade': 'Hypothesis',
        'unknown': dict.fromkeys((
            'native_behavior', 'exact_family_prefix', 'response_adaptation',
            'physical_qualification', 'other_caller_prerequisites',
            'runtime_transition_policy'), 'Unknown'),
        'request': {'initiator': 'F1', 'target': '08', 'service': 'B555',
                    'count': 1, 'data': '00', 'direction': 'initiator_to_target'},
        'roles': {'family_address': '15', 'route_address': '08'},
        'predicate': {'controller_type': 2, 'spn': 385, 'family_match': True,
                      'required_bits': [0, 1], 'operator': 'all'},
        'outputs': {'first': 0, 'second': 1},
        'authority': {'trust': False, 'write_permission': False,
                      'runtime_implemented': False},
    })


def oracle(case):
    raw = case['raw_r1']
    value = None if raw is None else int(raw, 16)
    # Division/remainder deliberately differs from the page's bit-mask equations.
    first = None if value is None else value % 2 == 1
    second = None if value is None else (value // 2) % 2 == 1
    eligible = (case['controller_type'] == 2 and case['spn'] == 385
                and case['family_match'] is True and first is True
                and second is True)
    return {'first': first, 'second': second,
            'unknown_high_bits': None if value is None else (value // 4) * 4,
            'eligible': eligible, 'local_flag': eligible,
            'first_bit_policy': first,
            'last_known_good': copy.deepcopy(case['last_known_good'])}


class ManagerPredicateContract(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def test_page_tables_and_fixture_contract(self):
        c = self.data['contract']
        check_contract(self, c)
        self.assertEqual(table(self.page, '| Property | Grade |'),
                         [['local_candidate', 'Hypothesis']] +
                         [[key, 'Unknown'] for key in c['unknown']])
        self.assertEqual(table(self.page, '| Request field | Value |'),
                         [[key, str(value)] for key, value in c['request'].items()])
        self.assertEqual(table(self.page, '| Role property | Address |'),
                         [['family_address', '15'], ['route_address', '08']])
        self.assertEqual(table(self.page, '| Output | R1 bit |'),
                         [['first', '0'], ['second', '1']])
        self.assertEqual(table(self.page,
            '| R1 | first | second | unknown_high_bits | both_bits | first_bit_policy |'), [
                ['00', 'false', 'false', '0', 'false', 'false'],
                ['01', 'true', 'false', '0', 'false', 'true'],
                ['02', 'false', 'true', '0', 'false', 'false'],
                ['03', 'true', 'true', '0', 'true', 'true'],
                ['80', 'false', 'false', '128', 'false', 'false']])
        for phrase in ('does not grant trust or write permission',
                       'Nothing is stable', 'before 1.0', 'Unknown family fails closed',
                       'eBUS MCP compatibility and GraphQL parity',
                       '../protocols/vaillant/ebus-vaillant-b555-timer-protocol.md#56'):
            self.assertIn(phrase, ' '.join(self.page.split()))

    def test_scenarios_and_independent_transitions(self):
        cases = self.data['scenarios']
        self.assertEqual([c['id'] for c in cases], [
            'zero', 'first', 'second', 'both', 'high', 'wrong_type',
            'wrong_spn', 'wrong_family', 'unknown_family', 'partial'])
        # Explicit control tuples prevent removal or joint variation of selectors.
        self.assertEqual([(c['controller_type'], c['spn'], c['family_match'],
                           c['raw_r1']) for c in cases], [
            (2, 385, True, '00'), (2, 385, True, '01'),
            (2, 385, True, '02'), (2, 385, True, '03'),
            (2, 385, True, '80'), (1, 385, True, '03'),
            (2, 384, True, '03'), (2, 385, False, '03'),
            (2, 385, 'Unknown', '03'), (2, 385, True, None)])
        for case in cases:
            with self.subTest(case=case['id']):
                before = copy.deepcopy(case)
                self.assertEqual(case['last_known_good'],
                                 {'raw_r1': '03', 'grade': 'Hypothesis'})
                self.assertEqual(case['expected'], oracle(case))
                self.assertEqual(case, before)
        # Exhaustive arithmetic agreement, independent of stored expected rows.
        for value in range(256):
            case = dict(cases[3], raw_r1=format(value, '02X'))
            result = oracle(case)
            self.assertEqual(result['first'], bool(value & 1))
            self.assertEqual(result['second'], bool(value & 2))
            self.assertEqual(result['eligible'], (value & 3) == 3)
            self.assertEqual(result['unknown_high_bits'], value & 252)
        # Vary retained state independently: it must never supply current flags.
        partial = dict(cases[-1], last_known_good={'raw_r1': '01', 'grade': 'Unknown'})
        result = oracle(partial)
        self.assertFalse(result['eligible'])
        self.assertIsNone(result['first'])
        self.assertEqual(result['last_known_good'], partial['last_known_good'])

    def test_each_contract_field_rejects_mutation(self):
        c = self.data['contract']
        mutations = {
            'request': {'initiator': 'F0', 'target': '15', 'service': 'B554',
                        'count': 2, 'data': '01', 'direction': 'target_to_initiator'},
            'roles': {'family_address': '08', 'route_address': '15'},
            'outputs': {'first': 1, 'second': 0},
            'predicate': {'controller_type': None, 'spn': None,
                          'family_match': 'Unknown', 'required_bits': [0],
                          'operator': 'any'},
            'authority': {'trust': True, 'write_permission': True,
                          'runtime_implemented': True},
            'unknown': dict.fromkeys(c['unknown'], 'Hypothesis'),
        }
        for group, changes in mutations.items():
            for field, replacement in changes.items():
                with self.subTest(group=group, field=field):
                    mutant = copy.deepcopy(c)
                    mutant[group][field] = replacement
                    with self.assertRaises(AssertionError):
                        check_contract(self, mutant)
        mutant = copy.deepcopy(c)
        mutant['grade'] = 'Proven'
        with self.assertRaises(AssertionError):
            check_contract(self, mutant)


if __name__ == '__main__':
    unittest.main()
