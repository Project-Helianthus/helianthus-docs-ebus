"""Finite AN06 contract checks; the model below is not companion production code."""
import copy
import json
import os
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/an06_b503_history_branches.md'
FIXTURE = ROOT / 'architecture/fixtures/an06_b503_history_branches.json'
NAMES = ('minute', 'hour', 'day', 'month', 'year')
DOMAINS = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 99))


def unsigned(value):
    return type(value) is int and value >= 0


def history_branch_view(context, marker, remainder, error, cells):
    """Test-local model of the hypothetical ab05an05.history_branch_view API."""
    supplied = copy.deepcopy(dict(context=context, marker=marker, remainder=remainder,
                                  error=error, cells=cells))
    error_state = 'missing' if error is None else ('present' if unsigned(error) else 'malformed')
    result = {'input': supplied, 'state': 'unknown-branch',
              'error': {'state': error_state, 'value': error if error_state == 'present' else None},
              'components': [], 'complete': False}
    context_ok = (isinstance(context, dict)
                  and all(isinstance(context.get(k), str) and context[k]
                          for k in ('family', 'variant', 'direction'))
                  and type(context.get('operation')) is int and context['operation'] == 1)
    selected = context_ok and type(marker) is int and marker in (1, 2)
    vector = cells if isinstance(cells, list) else []
    for i, (low, high) in enumerate(DOMAINS):
        cell = vector[i] if i < len(vector) else None
        raw = copy.deepcopy(cell.get('raw')) if isinstance(cell, dict) else None
        state, value = 'unselected', None
        if selected:
            if cell is None:
                state = 'missing'
            elif not isinstance(cell, dict):
                state = 'malformed'
            elif cell.get('state') in ('missing', 'replacement'):
                state = cell['state']
            elif cell.get('state') != 'value' or not unsigned(cell.get('value')):
                state = 'malformed'
            else:
                value = cell['value']
                state = 'candidate' if low <= value <= high else 'out-of-domain'
        result['components'].append({'state': state, 'raw': raw, 'value': value})
    complete = selected and all(c['state'] == 'candidate' for c in result['components'])
    result['complete'] = complete
    if context_ok and type(marker) is int and marker == 0:
        if (isinstance(remainder, list) and len(remainder) == 7
                and all(type(b) is int and b == 255 for b in remainder)):
            result['state'] = 'no-item'
    elif (selected and isinstance(cells, list) and len(cells) == 5
          and all(isinstance(cell, dict) for cell in cells)):
        if marker == 1 and error_state == 'present' and not complete:
            result['state'] = 'error-without-complete-time'
        elif marker == 2 and complete:
            result['state'] = 'candidate-components'
    result['grades'] = {'software': 'Proven',
                        'numeric': 'Proven' if selected else 'Unknown',
                        'semantic': 'Unknown' if result['state'] == 'unknown-branch' else 'Hypothesis',
                        'native': 'Unknown'}
    return result


def validate_page(text):
    match = re.search(r'```json history-branch-rules\n(.*?)\n```', text, re.S)
    assert match, 'missing executable declaration'
    rules = json.loads(match.group(1))
    # Independent critical rules, not a whole-file golden or page/fixture equality.
    assert rules['selection_order'] == ['context-operation', 'marker', 'remainder-or-components',
                                        'component-presence', 'component-domain']
    assert rules['no_item'] == {'operation': 1, 'marker': 0, 'remainder_length': 7, 'every_byte': 255}
    assert rules['replacement'] == 'retain-raw-without-normalization'
    assert rules['error'] == 'retain-independently-of-time'
    for key in ('packet_offsets', 'error_codec', 'decimal_algorithm', 'century'):
        assert rules[key] == 'Unknown', key
    assert rules['domains'] == dict(zip(NAMES, map(list, DOMAINS)))
    assert rules['grades'] == {'software': 'Proven', 'candidate_semantics': 'Hypothesis', 'native': 'Unknown'}
    for statement in (
        'Calendar inspection cannot override a no-item or unknown-marker selection.',
        'Missing/replacement selection precedes domain checking',
        'a valid\n  error survives every branch',
        'exactly seven bytes each equal to 255',
        'No conversion to an absolute timestamp, year expansion',
        'Byte positions, the wire error-number codec and the decimal algorithm are\n**Unknown**.',
        'Century, timezone, joint calendar validity, body freshness,',
        'test-local contract model, not the absent companion code',
        'Raw replacement FF is never a\ndate.',
        'component domains remain **Hypothesis**.',
    ):
        assert statement in text, statement
    # Reject affirmative redefinitions appended outside the declaration as well.
    assert not re.search(r'(?i)\b(?:packet offset|byte offset)\s*(?:is|=|:)\s*\d', text)
    assert not re.search(r'(?i)\bcentury\s*(?:is|=|:)\s*\d', text)
    assert not re.search(r'(?i)\b(?:use|assume|add)\s+(?:the\s+)?(?:century\s+)?(?:1900|2000)', text)
    return rules


def validate_examples(data):
    assert data['api'] == 'ab05an05.history_branch_view'
    assert data['synthetic'] is True
    ids = set()
    for case in data['cases']:
        assert case['id'] not in ids
        ids.add(case['id'])
        actual = history_branch_view(**case['input'])
        expected = case['expected']
        for field in ('state', 'error', 'complete', 'grades'):
            assert actual[field] == expected[field], (case['id'], field, actual[field], expected[field])
        for field, key in (('component_states', 'state'), ('component_values', 'value'), ('component_raw', 'raw')):
            assert [c[key] for c in actual['components']] == expected[field], (case['id'], field)
        assert actual['input'] == case['input'], case['id']
    return ids


class HistoryBranchContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = PAGE.read_text(encoding='utf-8')
        cls.data = json.loads(FIXTURE.read_text(encoding='utf-8'))
        cls.cases = {case['id']: case for case in cls.data['cases']}

    def test_page_rules_and_grade_boundaries(self):
        validate_page(self.text)

    def test_all_independent_examples(self):
        self.assertGreater(len(validate_examples(self.data)), 0)

    def test_finite_coverage_and_independent_field_variation(self):
        ids = validate_examples(self.data)
        required = {'upper', 'lower', 'no-item', 'error-only', 'minute-high', 'hour-high',
                    'cells-missing', 'cells-short', 'impossible-joint-date', 'unavailable-context',
                    'marker-one-complete', 'error-all-missing', 'error-partial'}
        required.update('remainder-' + str(i) for i in range(7))
        required.update('remainder-' + s for s in ('short', 'long', 'malformed', 'missing'))
        required.update('marker-' + s for s in ('unknown', 'missing', 'malformed'))
        required.update('error-' + s for s in ('missing', 'zero', 'other', 'malformed', 'bool'))
        required.update(NAMES[i] + '-' + s for i in range(5)
                        for s in ('low', 'high', 'missing', 'replacement', 'malformed', 'value', 'bool'))
        required.update(('family', 'variant', 'operation', 'direction'))
        self.assertEqual(ids, required)
        base = self.cases['upper']['input']
        for field in ('family', 'variant', 'operation', 'direction'):
            with self.subTest(context=field):
                changed = copy.deepcopy(base)
                changed['context'][field] = self.cases[field]['input']['context'][field]
                self.assertNotEqual(changed['context'][field], base['context'][field])
                self.assertEqual(changed, self.cases[field]['input'])
        for i in range(7):
            with self.subTest(remainder=i):
                changed = self.cases['remainder-' + str(i)]['input']
                self.assertEqual([j for j in range(7) if changed['remainder'][j] != 255], [i])
        for i, name in enumerate(NAMES):
            for suffix in ('low', 'high', 'missing', 'replacement', 'malformed', 'value', 'bool'):
                with self.subTest(component=name, variant=suffix):
                    changed = self.cases[name + '-' + suffix]['input']
                    self.assertNotEqual(changed['cells'][i], base['cells'][i])
                    self.assertEqual(changed['cells'][:i] + changed['cells'][i+1:],
                                     base['cells'][:i] + base['cells'][i+1:])

    def test_result_and_caller_mutation_isolation(self):
        for case in self.data['cases']:
            with self.subTest(case=case['id']):
                caller = copy.deepcopy(case['input'])
                pristine = copy.deepcopy(caller)
                first = history_branch_view(**caller)
                baseline = copy.deepcopy(first)
                if isinstance(caller['context'], dict):
                    caller['context']['family'] = 'mutated-family'
                    caller['context']['variant'] = 'mutated-variant'
                    caller['context']['operation'] = 9
                    caller['context']['direction'] = 'mutated-direction'
                if isinstance(caller['remainder'], list):
                    caller['remainder'][:] = [0] * len(caller['remainder'])
                if isinstance(caller['cells'], list) and caller['cells']:
                    if isinstance(caller['cells'][0]['raw'], list):
                        caller['cells'][0]['raw'].append(9)
                self.assertEqual(first, baseline)
                first['input']['context'] = None
                first['input']['remainder'] = [0]
                if isinstance(first['input']['cells'], list) and first['input']['cells']:
                    first['input']['cells'][0]['value'] = 123
                first['components'][0]['raw'] = ['changed']
                first['error']['value'] = 999
                self.assertEqual(history_branch_view(**pristine), baseline)
                self.assertEqual(pristine, case['input'])

    def test_missing_vector_with_error_keeps_independent_error(self):
        inp = copy.deepcopy(self.cases['error-only']['input'])
        inp['cells'] = None
        result = history_branch_view(**inp)
        self.assertEqual(result['state'], 'unknown-branch')
        self.assertEqual(result['error'], {'state': 'present', 'value': 4660})
        self.assertEqual([c['state'] for c in result['components']], ['missing'] * 5)

    def test_raw_ff_does_not_select_replacement_or_decode_calendar(self):
        inp = copy.deepcopy(self.cases['upper']['input'])
        inp['cells'][0] = {'state': 'value', 'raw': [255], 'value': 59}
        self.assertEqual(history_branch_view(**inp)['components'][0],
                         {'state': 'candidate', 'raw': [255], 'value': 59})
        inp['cells'][0]['value'] = None
        self.assertEqual(history_branch_view(**inp)['components'][0]['state'], 'malformed')

    def test_malformed_cell_and_vector_remain_partial(self):
        inp = copy.deepcopy(self.cases['upper']['input'])
        for bad in (7, {'state': 'unrecognized', 'raw': [255], 'value': 0}):
            inp['cells'][0] = bad
            result = history_branch_view(**inp)
            self.assertEqual(result['state'], 'unknown-branch')
            self.assertEqual(result['components'][0]['state'], 'malformed')
            self.assertEqual([c['value'] for c in result['components'][1:]], [23, 31, 12, 99])
        inp = copy.deepcopy(self.cases['upper']['input'])
        inp['cells'].append({'state': 'value', 'raw': [0], 'value': 0})
        self.assertEqual(history_branch_view(**inp)['state'], 'unknown-branch')

    def test_marker_one_with_error_and_scalar_cell_is_unknown_branch(self):
        inp = copy.deepcopy(self.cases['error-only']['input'])
        self.assertEqual(inp['marker'], 1)
        inp['cells'][0] = 7
        result = history_branch_view(**inp)
        self.assertEqual(result['state'], 'unknown-branch')
        self.assertEqual(result['error']['state'], 'present')
        self.assertEqual(result['components'][0]['state'], 'malformed')

    def test_relative_page_links_resolve_locally(self):
        links = re.findall(r'\]\(([^)]+)\)', self.text)
        self.assertGreater(len(links), 0)
        for link in links:
            self.assertNotIn('://', link)
            self.assertTrue((PAGE.parent / link.split('#')[0]).is_file(), link)

    def test_disposable_page_mutants_are_rejected(self):
        mutations = (
            ('"context-operation",\n    "marker"', '"marker",\n    "context-operation"'),
            ('"component-presence",\n    "component-domain"', '"component-domain",\n    "component-presence"'),
            ('"retain-raw-without-normalization"', '"convert-FF-to-date"'),
            ('"retain-independently-of-time"', '"discard-if-time-incomplete"'),
            ('"remainder_length": 7', '"remainder_length": 1'),
            ('"packet_offsets": "Unknown"', '"packet_offsets": [0, 1, 2]'),
            ('"century": "Unknown"', '"century": 2000'),
            ('"native": "Unknown"', '"native": "Proven"'),
            ('Calendar inspection cannot override a no-item or unknown-marker selection.',
             'Check calendar before marker.'),
            ('Missing/replacement selection precedes domain checking',
             'Domain checking precedes missing/replacement selection'),
            ('Raw replacement FF is never a\ndate.', 'Raw replacement FF is a date.'),
            ('a valid\n  error survives every branch', 'an error is discarded without time'),
            ('exactly seven bytes each equal to 255', 'only the first byte equal to 255'),
            ('No conversion to an absolute timestamp, year expansion',
             'Use century 2000 for an absolute timestamp, year expansion'),
        )
        with tempfile.TemporaryDirectory(prefix='an06-page-', dir=os.environ.get('TMPDIR')) as directory:
            path = Path(directory) / PAGE.name
            for old, new in mutations:
                with self.subTest(mutation=new):
                    self.assertIn(old, self.text)
                    path.write_text(self.text.replace(old, new, 1), encoding='utf-8')
                    with self.assertRaises(AssertionError):
                        validate_page(path.read_text(encoding='utf-8'))
            for addition in ('\nPacket offset is 3.\n', '\nCentury is 2000.\n'):
                path.write_text(self.text + addition, encoding='utf-8')
                with self.assertRaises(AssertionError):
                    validate_page(path.read_text(encoding='utf-8'))

    def test_disposable_fixture_mutants_are_rejected(self):
        edits = [
            ('no-item', 'state', 'candidate-components'),
            ('error-only', 'error', {'state': 'missing', 'value': None}),
            ('error-only', 'component_states', ['candidate'] * 5),
            ('upper', 'grades', {'software': 'Proven', 'numeric': 'Proven',
                                 'semantic': 'Proven', 'native': 'Proven'}),
        ]
        edits += [('remainder-' + str(i), 'state', 'no-item') for i in range(7)]
        edits += [(name + '-high', 'component_states', ['candidate'] * 5) for name in NAMES]
        with tempfile.TemporaryDirectory(prefix='an06-fixture-', dir=os.environ.get('TMPDIR')) as directory:
            path = Path(directory) / FIXTURE.name
            for identity, field, value in edits:
                with self.subTest(case=identity, field=field):
                    data = copy.deepcopy(self.data)
                    case = next(c for c in data['cases'] if c['id'] == identity)
                    case['expected'][field] = value
                    path.write_text(json.dumps(data), encoding='utf-8')
                    with self.assertRaises(AssertionError):
                        validate_examples(json.loads(path.read_text(encoding='utf-8')))


if __name__ == '__main__':
    unittest.main()
