"""Finite AN04 contract checks; no runtime helper or external package required."""
import copy
import json
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = Path('architecture/an04_b524_codebook_views.md')
FIXTURE = Path('architecture/fixtures/an04_b524_codebook_views.json')
POLICY = {
    'cross_family_fallback': False,
    'automatic_width_selection': False,
    'signed8_unsigned_reinterpretation': False,
    'controller_720_pool5': False,
    'merge_op02_op06': False,
    'unlabelled_is_unsupported': False,
    'unlabelled_is_writable': False,
    'native_qualification': 'Unknown',
    'candidate_grade': 'Hypothesis',
}
# Independent, literal expectations: do not read or derive labels from examples.
LABELS = {
    'controller-700': {
        (1, 3): '0 off; 1 automatic; 2 day',
        (3, 1): '0 off; 1 automatic; 2 day',
        (3, 6): '0 off; 1 automatic; 2 day; 3 setback',
        (2, 2): '0 deactivated; 1 heating; 2 fixed-flow; 3 DHW; 4 return-flow; 5 pool',
        (3, 19): '0 none; 1 central; 2 remote-circuit-one; 3 remote-circuit-two; 4 remote-circuit-three; 5 remote-circuit-four; 6 remote-circuit-five; 7 remote-circuit-six; 8 remote-circuit-seven; 9 remote-circuit-eight',
        (3, 27): '0 no-quick-mode; 1 ventilation-boost; 3 party; 4 quick-veto; 5 one-day-holiday; 6 one-day-bank-holiday; 7 holiday; 8 bank-holiday; 10 system-off',
        (3, 28): '-1 unbound; 0 control-circuit-one; 1 control-circuit-two; 2 control-circuit-three',
    },
    'controller-720': {
        (1, 3): '0 off; 1 time-controlled; 2 manual',
        (3, 1): '0 off; 1 time-controlled; 2 manual',
        (3, 6): '0 off; 1 time-controlled; 2 manual',
        (2, 2): '0 deactivated; 1 heating; 2 fixed-flow; 3 DHW; 4 return-flow',
        (3, 19): '0 none; 1 central; 2 remote-circuit-one; 3 remote-circuit-two; 4 remote-circuit-three; 5 remote-circuit-four',
        (3, 27): '0 no-special-function; 1 ventilation-boost; 4 quick-veto; 7 holiday; 10 system-off',
        (3, 28): '-1 unbound; 0 control-circuit-one; 1 control-circuit-two; 2 control-circuit-three; 3 control-circuit-four; 4 control-circuit-five; 5 control-circuit-six; 6 control-circuit-seven; 7 control-circuit-eight; 8 control-circuit-nine',
    },
}
INPUT_FIELDS = {
    'family', 'software', 'hardware', 'api_version', 'api_revision',
    'op', 'gg', 'ii', 'rr', 'alternative', 'requested_gg', 'requested_rr',
    'returned_gg', 'returned_rr', 'response_state', 'raw_value', 'raw_status',
}
UNKNOWN_FIELDS = ('native_qualification', 'support', 'edit_permission',
                  'presence', 'freshness', 'execution')


def labels(text):
    return dict(part.split(' ', 1) for part in text.split('; '))


def alternatives(key):
    if key == (3, 27):
        return ['u8', 'u16le']
    return ['signed8'] if key == (3, 28) else ['u16le']


def check_contract(root):
    """Semantically validate both artifacts against an independent specification."""
    data = json.loads((root / FIXTURE).read_text())
    page = (root / PAGE).read_text()
    page_policy = json.loads(re.search(r'```json\n(.*?)\n```', page, re.S)[1])
    assert data['policy'] == POLICY, 'fixture policy'
    assert page_policy == POLICY, 'page policy'
    rows = [line.split('|')[1:-1] for line in page.splitlines()
            if re.match(r'\| [0-9A-F]{2}/[0-9A-F]{4} \|', line)]
    assert len(rows) == 7, 'seven page selectors'
    seen = set()
    for row in rows:
        identity, ii, alt, older, newer = [cell.strip() for cell in row]
        gg, rr = (int(x, 16) for x in identity.split('/'))
        key = gg, rr
        assert key not in seen, 'duplicate page selector'
        seen.add(key)
        assert labels(older) == labels(LABELS['controller-700'][key]), 'page 700 labels'
        assert labels(newer) == labels(LABELS['controller-720'][key]), 'page 720 labels'
        assert ii == ('00' if key == (1, 3) else 'explicit'), 'page II'
        assert alt == ('u8 or u16le, explicitly selected' if key == (3, 27)
                       else alternatives(key)[0]), 'page width'
    books = data['codebooks']
    assert len(books) == 14, 'seven selectors in each family'
    identities = set()
    for book in books:
        key = book['gg'], book['rr']
        family = book['family']
        assert (family, key) not in identities, 'duplicate codebook'
        identities.add((family, key))
        assert book['op'] == 2, 'OP02 only'
        assert book['labels'] == labels(LABELS[family][key]), 'fixture labels'
        assert book['alternatives'] == alternatives(key), 'fixture width'
        assert book['instance_policy'] == ('zero' if key == (1, 3) else 'explicit'), 'fixture II'
    expected_identities = {(family, key) for family in LABELS for key in LABELS[family]}
    assert identities == expected_identities, 'complete family selectors'
    return data


def interpret(inp, books):
    """Executable documentation model, not the companion production implementation."""
    raw = inp['raw_value']
    assert all(type(byte) is int and 0 <= byte <= 255 for byte in raw)
    out = dict(context=copy.deepcopy(inp), raw_integer=None, candidate_label=None,
               state='raw', numeric_grade='Unknown', semantic_grade='Unknown')
    out.update({key: 'Unknown' for key in UNKNOWN_FIELDS})
    alt = inp['alternative']
    widths = {'u8': 1, 'u16le': 2, 'signed8': 1}
    if not raw and inp['response_state'] != 'echo-payload':
        out['state'] = 'partial'
        return out
    if alt not in widths:
        return out
    if len(raw) != widths[alt]:
        out['state'] = 'malformed-width'
        return out
    integer = int.from_bytes(bytes(raw), 'little', signed=alt == 'signed8')
    out.update(raw_integer=integer, numeric_grade='Proven')
    ii = inp['ii']
    if type(ii) is not int or not 0 <= ii <= 255:
        return out
    if (inp['response_state'] != 'echo-payload'
            or inp['requested_gg'] != inp['gg']
            or inp['requested_rr'] != inp['rr']
            or inp['returned_gg'] != inp['requested_gg']
            or inp['returned_rr'] != inp['requested_rr']):
        return out
    for book in books:
        if any(inp[key] != book[key] for key in ('family', 'op', 'gg', 'rr')):
            continue
        if alt not in book['alternatives'] or (book['instance_policy'] == 'zero' and ii != 0):
            continue
        label = book['labels'].get(str(integer))
        out.update(candidate_label=label, semantic_grade='Hypothesis',
                   state='interpreted' if label is not None else 'unlabelled')
        break
    return out


class CodebookViewsTest(unittest.TestCase):
    def setUp(self):
        self.data = check_contract(ROOT)
        self.cases = self.data['cases']
        self.books = self.data['codebooks']

    def test_page_and_fixture_contract(self):
        self.assertEqual('an04', self.data['contract'])

    def test_every_finite_example(self):
        self.assertGreater(len(self.cases), 0)
        ids = set()
        for case in self.cases:
            with self.subTest(case=case['id']):
                self.assertNotIn(case['id'], ids)
                ids.add(case['id'])
                self.assertEqual(INPUT_FIELDS, set(case['input']))
                self.assertEqual(case['expected'], interpret(case['input'], self.books))
                for key in UNKNOWN_FIELDS:
                    self.assertEqual('Unknown', case['expected'][key])

    def test_all_named_values_have_independent_examples(self):
        expected = set()
        for family, table in LABELS.items():
            for key, entries in table.items():
                for alt in alternatives(key):
                    for code, label in labels(entries).items():
                        integer = int(code)
                        # Raw encoding is checked separately from the model's decoder.
                        raw = [integer & 255] if alt != 'u16le' else [integer & 255, integer >> 8]
                        expected.add((family, *key, alt, tuple(raw), integer, label))
        actual = set()
        for case in self.cases:
            if not case['id'].startswith('named-'):
                continue
            inp, out = case['input'], case['expected']
            actual.add((inp['family'], inp['gg'], inp['rr'], inp['alternative'],
                        tuple(inp['raw_value']), out['raw_integer'], out['candidate_label']))
            self.assertEqual(('interpreted', 'Proven', 'Hypothesis', 'Unknown'),
                             (out['state'], out['numeric_grade'], out['semantic_grade'],
                              out['native_qualification']))
        self.assertEqual(expected, actual)

    def test_each_context_and_key_axis(self):
        baseline = next(c['input'] for c in self.cases if c['id'] == 'unknown-family').copy()
        baseline['family'] = 'controller-700'
        changes = {
            'family': 'controller-other', 'op': 6, 'gg': 4, 'rr': 4, 'ii': None,
            'alternative': None, 'requested_gg': 3, 'requested_rr': 3,
            'returned_gg': 3, 'returned_rr': 3, 'response_state': 'transport-failure',
            'software': 'other-software', 'hardware': 'other-hardware',
            'api_version': 1, 'api_revision': 1, 'raw_value': [254, 0], 'raw_status': 255,
        }
        retained_axes = {'software', 'hardware', 'api_version', 'api_revision', 'raw_status'}
        for field, value in changes.items():
            with self.subTest(field=field):
                inp = copy.deepcopy(baseline)
                inp[field] = value
                out = interpret(inp, self.books)
                self.assertEqual(inp, out['context'])
                self.assertEqual('pool' if field in retained_axes else None, out['candidate_label'])
                self.assertEqual('Unknown', out['native_qualification'])
                self.assertTrue(any(c['input'].get(field) == value for c in self.cases),
                                'finite fixture must vary each axis')
        for ii in (1, 255):
            inp = dict(baseline, ii=ii)
            self.assertEqual('pool', interpret(inp, self.books)['candidate_label'])
        for ii in (-1, 256, None):
            inp = dict(baseline, ii=ii)
            self.assertIsNone(interpret(inp, self.books)['candidate_label'])

    def test_signed_and_width_boundaries(self):
        cases = {c['id']: c for c in self.cases}
        for name, value in [('u16-max', 65535), ('u16-unknown', 254),
                            ('signed-boundary--128', -128), ('signed-boundary-127', 127)]:
            self.assertEqual(value, cases[name]['expected']['raw_integer'])
        for family in LABELS:
            signed = [c for c in self.cases if c['input']['family'] == family
                      and c['input']['rr'] == 28 and c['input']['raw_value'] == [255]
                      and c['input']['alternative'] == 'signed8']
            self.assertEqual(1, len(signed))
            self.assertEqual((-1, 'unbound'), (signed[0]['expected']['raw_integer'],
                                             signed[0]['expected']['candidate_label']))
        self.assertEqual('malformed-width', cases['quick-u16le-[3]']['expected']['state'])
        for state in ('status-only-0', 'status-only-255', 'empty-None', 'short-None',
                      'header-only-None', 'transport-failure-None'):
            self.assertEqual('partial', cases[state]['expected']['state'])
            self.assertIsNone(cases[state]['expected']['raw_integer'])

    def test_finite_negative_and_boundary_coverage(self):
        cases = {case['id']: case for case in self.cases}
        required = {
            '720-no-pool', 'unknown-family', 'missing-family', '720-no-eighth',
            '720-no-party', 'missing-alternative', 'unknown-alternative',
            'signed-unsigned-selection', 'singleton-nonzero-ii',
            'partial-owned-value', 'quick-u16le-[3]',
        }
        self.assertTrue(required <= cases.keys())
        for family, table in LABELS.items():
            for gg, rr in table:
                for alt in alternatives((gg, rr)):
                    for kind in ('max-or-min', 'truncated', 'extra'):
                        name = f'boundary-{family}-{gg}-{rr}-{alt}-{kind}'
                        self.assertIn(name, cases)
                        out = cases[name]['expected']
                        self.assertEqual('unlabelled' if kind == 'max-or-min'
                                         else 'malformed-width', out['state'])
        for ii in (-1, 255, 256):
            self.assertEqual(ii, cases['ii-boundary-' + str(ii)]['input']['ii'])

    def test_input_and_output_ownership(self):
        case = self.cases[0]
        inp = copy.deepcopy(case['input'])
        before = copy.deepcopy(inp)
        first = interpret(inp, self.books)
        second = interpret(inp, self.books)
        first['context']['raw_value'][0] = 99
        first['context']['software'] = 'changed'
        self.assertEqual(before, inp)
        self.assertEqual(before, second['context'])
        inp['raw_value'].append(99)
        self.assertEqual(before, second['context'])
        self.assertEqual(case['input'], case['expected']['context'])
        self.assertIsNot(case['input']['raw_value'], case['expected']['context']['raw_value'])

    def test_relative_page_links(self):
        page = (ROOT / PAGE).read_text()
        links = re.findall(r'\]\(([^)]+)\)', page)
        self.assertGreater(len(links), 0)
        for link in links:
            self.assertNotIn('://', link)
            self.assertTrue((ROOT / PAGE.parent / link.split('#')[0]).is_file(), link)

    def test_disposable_policy_mutants_are_rejected(self):
        # Fourteen executed kills, confined to copies of the two owned artifacts.
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='an04-mutants-', dir=ROOT / '.tmp') as tmp:
            mutant_root = Path(tmp)
            for relative in (PAGE, FIXTURE):
                (mutant_root / relative).parent.mkdir(parents=True, exist_ok=True)
            for key, value in POLICY.items():
                if type(value) is not bool:
                    continue
                for target in ('page', 'fixture'):
                    with self.subTest(policy=key, target=target):
                        page = (ROOT / PAGE).read_text()
                        data = copy.deepcopy(self.data)
                        if target == 'fixture':
                            data['policy'][key] = True
                        else:
                            old = json.dumps(key) + ': false'
                            self.assertIn(old, page)
                            page = page.replace(old, json.dumps(key) + ': true', 1)
                        (mutant_root / PAGE).write_text(page)
                        (mutant_root / FIXTURE).write_text(json.dumps(data))
                        with self.assertRaises(AssertionError):
                            check_contract(mutant_root)

    def test_semantic_mutants_are_rejected(self):
        # More than policy equality: table, width, opcode and expected integer kills.
        (ROOT / '.tmp').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='an04-semantics-', dir=ROOT / '.tmp') as tmp:
            mutant_root = Path(tmp)
            for relative in (PAGE, FIXTURE):
                (mutant_root / relative).parent.mkdir(parents=True, exist_ok=True)
            mutations = ('cross-family', 'width', 'opcode', 'page-label')
            for mutation in mutations:
                data = copy.deepcopy(self.data)
                page = (ROOT / PAGE).read_text()
                book = next(b for b in data['codebooks'] if b['family'] == 'controller-720'
                            and b['gg'] == 2 and b['rr'] == 2)
                if mutation == 'cross-family':
                    book['labels']['5'] = 'pool'
                elif mutation == 'width':
                    book['alternatives'].append('u8')
                elif mutation == 'opcode':
                    book['op'] = 6
                else:
                    page = page.replace('0 no-special-function;', '0 no-quick-mode;')
                (mutant_root / PAGE).write_text(page)
                (mutant_root / FIXTURE).write_text(json.dumps(data))
                with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                    check_contract(mutant_root)
            signed = next(c for c in self.cases if c['input']['alternative'] == 'signed8'
                          and c['input']['raw_value'] == [255])
            data = copy.deepcopy(self.data)
            bad = next(c for c in data['cases'] if c['id'] == signed['id'])
            bad['expected']['raw_integer'] = 255
            (mutant_root / FIXTURE).write_text(json.dumps(data))
            mutated = json.loads((mutant_root / FIXTURE).read_text())
            bad = next(c for c in mutated['cases'] if c['id'] == signed['id'])
            with self.assertRaises(AssertionError):
                self.assertEqual(bad['expected'], interpret(bad['input'], self.books))


if __name__ == '__main__':
    unittest.main()
