"""Offline AJ20 contract checks; the arithmetic oracle is test-only."""
import copy
import itertools
import json
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/aj20_b531_pending_conversion.md'
FIXTURE = ROOT / 'architecture/fixtures/aj20_b531_pending_conversion.json'

BASE = dict(family='synthetic-heat-pump', limit_id='limit-a', operation='merge',
            direction='local-request', value=123, number=123, scale=-1,
            active=True, duration=60, end_time=120, changeable=True)
VARIANTS = dict(family='synthetic-backup-heater', limit_id='limit-b',
                operation='partial', direction='local-feedback', value=124,
                number=124, scale=1, active=False, duration=61, end_time=121,
                changeable=False)
UNKNOWN = ('native_behavior', 'physical_qualification', 'production_capacity',
           'replacement_policy', 'coalescing_policy', 'nonfinite_handling',
           'intermediate_overflow_handling', 'native_units',
           'exact_changeability_predicate', 'exact_active_predicate',
           'ack_correlation', 'applied_OP01', 'applied_OP03')
STAGES = [('requested only', True, False, False, False, 'Unknown'),
          ('queued', True, True, False, False, 'Unknown'),
          ('dispatched', True, True, True, False, 'Unknown'),
          ('completed', True, True, True, True, 'Unknown')]
ARITHMETIC = [(123, -1, 12), (2, 1, 20), (-2, 0, 0),
              (4294967296, 0, 4294967295)]


def table(page, heading):
    section = page.split(heading, 1)[1].split('\n## ', 1)[0]
    lines = [line for line in section.splitlines() if line.startswith('|')]
    return [tuple(cell.strip() for cell in line.strip('|').split('|'))
            for line in lines[2:]]


def finite_oracle(number, scale):
    # No nonfinite or intermediate-overflow policy is supplied by this oracle.
    value = float(number) * (10.0 ** scale)
    if not math.isfinite(value):
        raise ValueError('outside finite examples')
    return min(max(math.trunc(value), 0), 2**32 - 1)


def validate(case, data):
    """Closed synthetic expectations, independent of documentation prose."""
    case.assertEqual(data['synthetic_capacity'], 2)
    facts = data['facts']
    expected_facts = dict.fromkeys(UNKNOWN, 'Unknown')
    expected_facts.update(candidate_grade='Hypothesis', implemented=False,
                          health_seconds=10, health_is_physical_timeout=False,
                          upstream_metadata=['consume', 'obligation',
                                             'active-power-limit', 'W'],
                          heartbeat_seconds=[60, 120], statuses=[2, 3, 8],
                          optional_wait_seconds=2,
                          ack_signature='(u32,u32,bool)->bool',
                          request_identifier=None)
    case.assertEqual(facts, expected_facts)
    expected_pending = [
        dict(identity='request-a', requested=True, queued=True, dispatched=False,
             completed=False, applied='Unknown'),
        dict(identity='request-b', requested=True, queued=True, dispatched=True,
             completed=False, applied='Unknown'),
        dict(identity='request-c', requested=True, queued=False, dispatched=False,
             completed=False, applied='Unknown', overflow='unresolved policy')]
    case.assertEqual(data['pending'], expected_pending)
    case.assertEqual(sum(row['queued'] for row in data['pending']), 2)
    case.assertEqual(len({row['identity'] for row in data['pending']}), 3)
    case.assertEqual(data['stages'], [dict(zip(
        ('stage', 'requested', 'queued', 'dispatched', 'completed', 'applied'), row))
        for row in STAGES])
    case.assertEqual(data['arithmetic'], [dict(number=n, scale=s, expected=e)
                                        for n, s, e in ARITHMETIC])
    records = [dict(case='control', record=BASE)]
    records += [dict(case=k, record={**BASE, k: v}) for k, v in VARIANTS.items()]
    records += [dict(case='delete', record={**BASE, 'operation': 'delete'})]
    case.assertEqual(data['records'], records)
    case.assertEqual(data['partial'], dict(
        before=BASE, patch={'active': False}, after={**BASE, 'active': False},
        raw_patch={'active': False}, omitted_fields='preserved', admission=False))
    case.assertEqual(data['capability'], [dict(
        event=event, requested=requested, feedback=feedback,
        before=True, after=False, last_known_good={'number': 123, 'scale': -1},
        admission=False) for event, requested, feedback in itertools.product(
            ('initialization', 'reset', 'topology change', 'late completion'),
            (False, True), (False, True))])
    case.assertEqual(data['acknowledgements'], [dict(
        arguments=[7, 9, True], result=True, request_identifier=None,
        correlated_request=None) for _ in range(2)])


class PendingConversionContract(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def test_synthetic_scenarios(self):
        validate(self, self.data)
        for number, scale, expected in ARITHMETIC:
            with self.subTest(number=number, scale=scale):
                self.assertEqual(finite_oracle(number, scale), expected)
        fractional = self.data['arithmetic'][0]
        self.assertNotEqual(math.ceil(fractional['number'] *
                                      10.0 ** fractional['scale']),
                            fractional['expected'])
        above_u32 = self.data['arithmetic'][-1]
        self.assertNotEqual(above_u32['number'] % (2**32),
                            above_u32['expected'])

    def test_page_tables(self):
        def text(value):
            return str(value).lower() if isinstance(value, bool) else str(value)
        self.assertEqual(table(self.page, '## Local pending work'),
                         [tuple(map(text, row)) for row in STAGES])
        self.assertEqual(table(self.page, '## Finite scaled numbers'),
                         [tuple(map(str, row)) for row in ARITHMETIC])
        self.assertEqual(table(self.page, '## Independent fields'),
                         [(key, text(BASE[key]), text(value) if key != 'operation'
                           else 'partial; delete separately')
                          for key, value in VARIANTS.items()])
        self.assertEqual(table(self.page, '## Local feedback'),
                         [('candidate_grade', 'Hypothesis', 'Hypothesis')] +
                         [(key, 'Unknown', 'Unknown') for key in UNKNOWN])
        for phrase in ('../protocols/vaillant/ebus-vaillant-B531-hem-power-limit.md',
                       'Ten-second local health timing is not a physical control timeout.',
                       'No queue, heartbeat, writer or acknowledgement protocol is implemented.',
                       'does not establish native\nunits', 'eBUS MCP', 'GraphQL parity',
                       'Nothing is stable before 1.0', 'before 0.9', '0.11'):
            self.assertIn(phrase, self.page)

    def reject(self, mutate):
        changed = copy.deepcopy(self.data)
        mutate(changed)
        with self.assertRaises(AssertionError):
            validate(self, changed)

    def test_grade_and_unknown_mutants(self):
        for field in ('candidate_grade',) + UNKNOWN:
            with self.subTest(field=field):
                self.reject(lambda d: d['facts'].__setitem__(field, 'Proven'))
        self.reject(lambda d: d['facts'].__setitem__('fabricated_predicate', True))
        for field in ('implemented', 'health_is_physical_timeout'):
            with self.subTest(field=field):
                self.reject(lambda d: d['facts'].__setitem__(field, True))

    def test_every_independent_record_field_mutant(self):
        # Each row must retain its single changed field; dropping any variant
        # back to the control catches conflation of precisely that field.
        for index, field in enumerate(VARIANTS, 1):
            with self.subTest(field=field):
                self.assertEqual([key for key in BASE if
                                  self.data['records'][index]['record'][key] != BASE[key]],
                                 [field])
                self.reject(lambda d: d['records'][index]['record'].__setitem__(field, BASE[field]))
        self.reject(lambda d: d['records'][-1]['record'].__setitem__('operation', 'partial'))

    def test_partial_and_capability_mutants(self):
        for field in BASE:
            if field != 'active':
                with self.subTest(omitted=field):
                    self.reject(lambda d: d['partial']['after'].pop(field))
        for field in ('before', 'patch', 'after', 'raw_patch', 'omitted_fields', 'admission'):
            with self.subTest(partial=field):
                self.reject(lambda d: d['partial'].__setitem__(field, None))
        for index in range(16):
            for field in ('event', 'requested', 'feedback', 'before', 'after',
                          'last_known_good', 'admission'):
                with self.subTest(capability=index, field=field):
                    self.reject(lambda d: d['capability'][index].__setitem__(field, None))

    def test_stages_capacity_and_arithmetic_mutants(self):
        self.reject(lambda d: d.__setitem__('synthetic_capacity', 3))
        for index in range(3):
            for field in self.data['pending'][index]:
                with self.subTest(pending=index, field=field):
                    self.reject(lambda d: d['pending'][index].__setitem__(field, None))
        for index in range(4):
            for field in self.data['stages'][index]:
                with self.subTest(stage=index, field=field):
                    self.reject(lambda d: d['stages'][index].__setitem__(field, None))
        for index, wrong in ((0, 13), (3, 0)):
            self.reject(lambda d: d['arithmetic'][index].__setitem__('expected', wrong))
        for index in range(4):
            for field in ('number', 'scale', 'expected'):
                with self.subTest(arithmetic=index, field=field):
                    self.reject(lambda d: d['arithmetic'][index].__setitem__(field, None))

    def test_feedback_variants_do_not_supply_correlation(self):
        baseline = dict(first_u32=7, second_u32=9, argument_flag=True,
                        result=True, heartbeat_seconds=60, status=2,
                        wait_seconds=2, value=123, engaged=True)
        variants = dict(first_u32=8, second_u32=10, argument_flag=False,
                        result=False, heartbeat_seconds=120, status=3,
                        wait_seconds=None, value=124, engaged=False)
        expected = [dict(case='control', local=baseline, request_identifier=None,
                         correlated_request=None, applied='Unknown')]
        for key, value in variants.items():
            expected.append(dict(case=key, local={**baseline, key: value},
                                 request_identifier=None, correlated_request=None,
                                 applied='Unknown'))
        expected.append(dict(case='status-8', local={**baseline, 'status': 8},
                             request_identifier=None, correlated_request=None,
                             applied='Unknown'))
        self.assertEqual(self.data['feedback_variants'], expected)
        for index, field in enumerate(variants, 1):
            with self.subTest(field=field):
                self.assertEqual([key for key in baseline if
                                  expected[index]['local'][key] != baseline[key]], [field])
                changed = copy.deepcopy(self.data['feedback_variants'])
                changed[index]['local'][field] = baseline[field]
                self.assertNotEqual(changed, expected)
        for index in range(len(expected)):
            for field in ('request_identifier', 'correlated_request', 'applied'):
                with self.subTest(index=index, field=field):
                    changed = copy.deepcopy(self.data['feedback_variants'])
                    changed[index][field] = 'invented'
                    self.assertNotEqual(changed, expected)

    def test_acknowledgement_and_argument_mutants(self):
        for index in range(2):
            for argument, value in enumerate((8, 10, False)):
                with self.subTest(ack=index, argument=argument):
                    self.reject(lambda d: d['acknowledgements'][index]['arguments'].__setitem__(argument, value))
            for field, value in (('result', False), ('request_identifier', 'invented'),
                                 ('correlated_request', 'request-a')):
                with self.subTest(ack=index, field=field):
                    self.reject(lambda d: d['acknowledgements'][index].__setitem__(field, value))
        for field in ('health_seconds', 'optional_wait_seconds', 'ack_signature',
                      'request_identifier'):
            self.reject(lambda d: d['facts'].__setitem__(field, None if field != 'request_identifier' else 'invented'))
        for field in ('heartbeat_seconds', 'statuses', 'upstream_metadata'):
            for index in range(len(self.data['facts'][field])):
                with self.subTest(field=field, index=index):
                    self.reject(lambda d: d['facts'][field].__setitem__(index, None))


if __name__ == '__main__':
    unittest.main()
