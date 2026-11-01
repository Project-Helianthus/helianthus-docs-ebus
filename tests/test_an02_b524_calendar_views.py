"""Independent executable examples of a hypothetical API, not a native codec."""
import copy
import json
import os
from pathlib import Path
import re
import unittest

ROOT = Path(os.environ.get('AN02_ROOT', Path(__file__).resolve().parents[1]))
PAGE = ROOT / 'architecture/an02_b524_calendar_views.md'
FIXTURE = ROOT / 'architecture/fixtures/an02_b524_calendar_views.json'
FIELDS = ('family', 'software', 'hardware', 'api_version', 'api_revision',
          'opcode', 'group', 'instance', 'register')


def independent_selectors():
    # Explicit independent oracle: no selection data is taken from the fixture.
    result = set()
    for family, group, dates, times in (
        ('controller-700', 0, (52, 113, 114), (53,)),
        ('controller-700', 1, (9, 10), ()),
        ('controller-700', 3, (3, 4), ()),
        ('controller-720', 0, (52, 218, 219), (53,)),
        ('controller-720', 1, (9, 10), (16, 17)),
        ('controller-720', 3, (3, 4, 36), (30, 32, 33)),
        ('controller-720', 9, (7, 9), (8, 10)),
    ):
        for alternative, registers in (('date', dates), ('time', times)):
            for register in registers:
                result.add((family, 2, group, 'caller' if group == 3 else 0,
                            register, alternative))
    return result


def selector(row):
    return tuple(row[k] for k in
                 ('family', 'opcode', 'group', 'instance', 'register', 'alternative'))


def validate_policy(policy):
    """Semantic assertions also reject dangerous normative page declarations."""
    assert policy['encoding'] == 'unsigned-byte', 'plain byte interpretation'
    assert policy['family_fallback'] is False, 'explicit family required'
    assert policy['opcode'] == 2, 'OP02 namespace only'
    assert policy['echo_match_required'] is True, 'echo match required'
    assert set(policy['context_fields']) == set(FIELDS), 'retain API revision/context'
    assert len(policy['context_fields']) == len(FIELDS)
    assert policy['missing_fill'] is None, 'missing is not zero'
    assert policy['timestamp'] is False, 'timestamp Unknown'
    assert policy['edit_permission'] is False, 'edit validation Unknown'
    assert policy['joint_date_validation'] is False
    assert policy['date_domains'] == [[1, 31], [1, 12], [0, 99]]
    assert policy['time_domains'] == [[0, 255]] * 3
    assert policy['numeric_grade'] == 'Proven'
    assert policy['semantic_grade'] == 'Hypothesis'
    assert policy['native_grade'] == 'Unknown'


def byte(value):
    return type(value) is int and 0 <= value <= 255


def interpret_example(case, policy, rows):
    """Test-only model of declared states; deliberately no AN01 import."""
    ctx, reply, cells = (case[k] for k in ('context', 'reply', 'cells'))
    alt = case['alternative']
    result = dict(context=copy.deepcopy(ctx), alternative=alt,
                  reply=copy.deepcopy(reply), input_cells=copy.deepcopy(cells),
                  numeric_grade=policy['numeric_grade'], semantic_grade='Unknown',
                  native_grade=policy['native_grade'])
    context_valid = all(ctx.get(k) is not None for k in FIELDS)
    context_valid &= all(isinstance(ctx.get(k), str) and bool(ctx[k]) for k in FIELDS[:5])
    context_valid &= all(byte(ctx.get(k)) for k in ('opcode', 'group', 'instance'))
    context_valid &= type(ctx.get('register')) is int and 0 <= ctx['register'] <= 65535
    selected = any(ctx.get('family') == r['family'] and
                   ctx.get('opcode') == policy['opcode'] == r['opcode'] and
                   ctx.get('group') == r['group'] and
                   (r['instance'] == 'caller' or ctx.get('instance') == r['instance']) and
                   ctx.get('register') == r['register'] and alt == r['alternative']
                   for r in rows)
    valid_cells = isinstance(cells, list) and len(cells) == 3 and all(
        isinstance(c, dict) and c.get('state') in ('present', 'missing', 'failed') and
        (byte(c.get('raw')) or (c.get('raw') is None and c['state'] != 'present'))
        for c in cells)
    eligible = context_valid and selected and valid_cells and reply['state'] == 'echo-payload'
    if policy['echo_match_required']:
        eligible &= reply.get('group') == ctx.get('group') and reply.get('register') == ctx.get('register')
    components = []
    if not valid_cells:
        components = [dict(state='raw-only', raw=cells[i].get('raw') if i < len(cells)
                           and isinstance(cells[i], dict) else None, value=None)
                      for i in range(3)]
    else:
        domains = policy['date_domains'] if alt == 'date' else policy['time_domains']
        for i, cell in enumerate(cells):
            raw, state = cell['raw'], cell['state']
            if state == 'present':
                state = ('candidate' if domains[i][0] <= raw <= domains[i][1]
                         else 'out-of-domain') if eligible else 'raw-only'
            components.append(dict(state=state, raw=raw,
                                   value=raw if state == 'candidate' else None))
    result.update(components=components,
                  complete_candidate=all(c['state'] == 'candidate' for c in components))
    if eligible:
        result['semantic_grade'] = policy['semantic_grade']
    return result


def validate_documents(page, fixture):
    policy = json.loads(re.search(r'```json\n(.*?)\n```', page, re.S).group(1))
    for source in (policy, fixture['contract']):
        validate_policy(source)
        assert {selector(r) for r in fixture['selectors']} == independent_selectors()
        assert len(fixture['selectors']) == 26
        for case in fixture['cases']:
            assert interpret_example(case, source, fixture['selectors']) == case['expected'], case['name']
            assert case['raw_hex'] == [f'{c["raw"]:02X}' if byte(c.get('raw')) else None
                                       for c in case['cells']], case['name']
    return policy


class CalendarContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text()
        cls.fixture = json.loads(FIXTURE.read_text())
        cls.policy = validate_documents(cls.page, cls.fixture)
        cls.cases = {c['name']: c for c in cls.fixture['cases']}

    def test_independent_examples_and_all_26_positive_controls(self):
        controls = [c for c in self.fixture['cases'] if c['name'].startswith('selector-')]
        self.assertEqual(len(controls), 26)
        seen = set()
        for c in controls:
            with self.subTest(c=c['name']):
                ctx = c['context']
                seen.add((ctx['family'], ctx['opcode'], ctx['group'],
                          'caller' if ctx['group'] == 3 else ctx['instance'],
                          ctx['register'], c['alternative']))
                self.assertTrue(c['expected']['complete_candidate'])
                expected = [31, 12, 99] if c['alternative'] == 'date' else [23, 59, 58]
                self.assertEqual([v['value'] for v in c['expected']['components']], expected)
        self.assertEqual(seen, independent_selectors())

    def test_numeric_partial_and_grade_boundaries(self):
        self.assertEqual(self.cases['plain-hex-12']['raw_hex'][0], '12')
        self.assertEqual(self.cases['plain-hex-12']['expected']['components'][0]['value'], 18)
        partial = self.cases['missing-month']['expected']
        self.assertEqual([c['value'] for c in partial['components']], [31, None, 99])
        self.assertFalse(partial['complete_candidate'])
        for name in ('domain-0', 'domain-1', 'domain-2'):
            self.assertIn('out-of-domain', [c['state'] for c in self.cases[name]['expected']['components']])
        self.assertTrue(self.cases['domain-3']['expected']['complete_candidate'])
        self.assertEqual([c['value'] for c in self.cases['time-plain-bytes']['expected']['components']], [255]*3)
        for c in self.fixture['cases']:
            self.assertEqual(c['expected']['native_grade'], 'Unknown')
            self.assertEqual(c['expected']['numeric_grade'], 'Proven')

    def test_every_context_field_and_byte_varies_independently(self):
        baseline = self.cases['selector-1']
        for field in FIELDS:
            for prefix in ('missing-', 'vary-'):
                c = self.cases[prefix+field]
                self.assertEqual({k for k in FIELDS if c['context'][k] != baseline['context'][k]}, {field})
                self.assertEqual(c['expected']['context'], c['context'])
        for i in range(3):
            c = self.cases['byte-'+str(i)]
            self.assertEqual([j for j in range(3) if c['cells'][j] != baseline['cells'][j]], [i])
            failed = self.cases['failed-'+str(i)]['expected']
            self.assertEqual(failed['components'][i]['state'], 'failed')
            self.assertEqual(sum(x['state'] == 'candidate' for x in failed['components']), 2)
            for suffix in ('raw', 'null'):
                missing = self.cases[f'missing-cell-{i}-{suffix}']['expected']
                self.assertEqual(missing['components'][i]['state'], 'missing')
                self.assertIsNone(missing['components'][i]['value'])
                self.assertEqual(sum(x['state'] == 'candidate' for x in missing['components']), 2)
                self.assertFalse(missing['complete_candidate'])

    def test_input_and_returned_buffers_are_independently_owned(self):
        for target in ('context', 'reply', 'cells'):
            c = copy.deepcopy(self.cases['selector-1'])
            result = interpret_example(c, self.policy, self.fixture['selectors'])
            before = copy.deepcopy(result)
            if target == 'context': c[target]['api_revision'] = 'synthetic-b'
            elif target == 'reply': c[target]['raw'][0] = 255
            else: c[target][0]['raw'] = 0
            self.assertEqual(result, before)
        c = copy.deepcopy(self.cases['selector-1'])
        before = copy.deepcopy(c)
        a = interpret_example(c, self.policy, self.fixture['selectors'])
        b = interpret_example(c, self.policy, self.fixture['selectors'])
        a['context']['api_revision'] = 'synthetic-b'
        a['reply']['raw'][0] = 255
        a['input_cells'][0]['raw'] = 0
        a['components'][0]['value'] = 0
        self.assertEqual(c, before)
        self.assertEqual(b, before['expected'])

    def test_malformed_and_ineligible_cases_retain_raw(self):
        names = ('unmatched-controller-700', 'unmatched-controller-720', 'vary-opcode',
                 'wrong-alternative', 'echo-group', 'echo-register', 'status',
                 'transport-error', 'unknown')
        for name in names:
            c = self.cases[name]
            self.assertFalse(c['expected']['complete_candidate'])
            self.assertEqual([v['value'] for v in c['expected']['components']], [None]*3)
            self.assertEqual(c['expected']['reply'], c['reply'])
            self.assertEqual(c['expected']['semantic_grade'], 'Unknown')
        for c in self.fixture['cases']:
            if c['name'].startswith('malformed-'):
                self.assertEqual([v['state'] for v in c['expected']['components']], ['raw-only']*3)

    def test_dynamic_instance_is_requested_context_without_physical_ceiling(self):
        c = copy.deepcopy(self.cases['selector-7'])
        self.assertEqual(c['context']['group'], 3)
        for ii in (0, 1, 127, 255):
            c['context']['instance'] = ii
            r = interpret_example(c, self.policy, self.fixture['selectors'])
            self.assertTrue(r['complete_candidate'])
            self.assertEqual(r['context']['instance'], ii)
            self.assertNotIn('instance', r['reply'])

    def test_unsafe_policy_mutations_fail_for_page_and_fixture(self):
        mutations = dict(encoding='bcd', family_fallback=True, opcode=6,
                         echo_match_required=False, missing_fill=0,
                         timestamp=True, edit_permission=True,
                         context_fields=[f for f in FIELDS if f != 'api_revision'])
        for key, value in mutations.items():
            for location in ('page', 'fixture'):
                with self.subTest(key=key, location=location):
                    page, fixture = self.page, copy.deepcopy(self.fixture)
                    if location == 'page':
                        policy = copy.deepcopy(self.policy)
                        policy[key] = value
                        page = re.sub(r'```json\n.*?\n```', lambda _: '```json\n'+json.dumps(policy)+'\n```', page, flags=re.S)
                    else:
                        fixture['contract'][key] = value
                    with self.assertRaises(AssertionError):
                        validate_documents(page, fixture)

    def test_corrupt_independent_fixture_expectations_fail(self):
        for name, component, value in (('plain-hex-12', 0, 12), ('missing-month', 1, 0)):
            f = copy.deepcopy(self.fixture)
            c = next(c for c in f['cases'] if c['name'] == name)
            c['expected']['components'][component]['value'] = value
            with self.assertRaises(AssertionError):
                validate_documents(self.page, f)

    def test_relative_page_links_resolve_locally(self):
        for link in re.findall(r'\]\(([^)]+)\)', self.page):
            self.assertNotIn('://', link)
            self.assertTrue((PAGE.parent / link.split('#')[0]).is_file(), link)


if __name__ == '__main__':
    unittest.main()
