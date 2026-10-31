"""Offline AJ27 documentation checks; no responder or scanner implementation."""
import copy
import itertools
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'architecture/aj27_standard07_local_responder.md'
FIXTURE = ROOT / 'architecture/fixtures/aj27_standard07_local_responder.json'
UNKNOWN = ('store_a_capacity', 'store_b_capacity', 'copy_ordering',
           'short_read_completion', 'identity_override_predicates',
           'sweep_destinations', 'decimal_above_99_output', 'persistence',
           'physical_response_seconds')


def packed(n):
    if not 0 <= n <= 99:
        return None
    tens, units = divmod(n, 10)
    return tens * 16 + units


def expected_builder(identifier, versions, number):
    quotient, remainder = divmod(number, 100)
    narrowed = quotient % 256
    components = [packed(v) for v in [*versions, remainder, narrowed]]
    output = None
    if (len(identifier) == 5
            and all(type(n) is int and 0 <= n <= 255 for n in identifier)
            and len(versions) == 2 and None not in components):
        output = [0xB5, *identifier, *components]
    return remainder, quotient, narrowed, output, output is not None


def selection(path, condition):
    if path == 'gpio':
        return 'gpio'
    if path == 'conditional_import':
        return 'import' if condition is True else 'withheld'
    return 'withheld'


def budget(variant, jobs):
    if any(type(n) is not int or n < 0 for n in jobs):
        return False
    if variant == 'A':
        return sum(jobs) <= 7
    if variant == 'B':
        return len(jobs) <= 3 and all(n <= 2 for n in jobs)
    return False


def validate(c):
    assert (c['grade'], c['native_behavior'], c['physical_qualification'],
            c['runtime_implemented']) == ('Hypothesis', 'Unknown', 'Unknown', False)
    assert c['unknown'] == dict.fromkeys(UNKNOWN, 'Unknown')
    assert c['builder'] == dict(prefix=181, identifier_bytes=5, data_bytes=10,
                                direction='local_response', grade='Hypothesis')
    assert c['variants'] == {
        'A': dict(sweep_count=230, solar=['06', 'ED', 'EE', 'EF', 'F2'],
                  secondary=['FC', '0A', '12'], controller_jobs=None,
                  attempts_per_job=None, max_attempts=7),
        'B': dict(sweep_count=0, solar=['06'], secondary=['FC'],
                  controller_jobs=3, attempts_per_job=2, max_attempts=6)}
    assert c['queue'] == dict(seconds=180, meaning='queue_timeout', physical_timing='Unknown')
    assert c['lifecycles'] == dict(stores=['store_a', 'store_b'], scratch='shared_scratch',
        clear_scope='selected_store_only', copy_completion='Unknown',
        short_success_full_identity=False, setter_persistence='Unknown')
    assert c['selection'] == dict(paths=['gpio', 'conditional_import'],
        import_condition='Unknown', unconditional_import=False, precedence='Unknown')
    assert c['boundaries'] == dict(mutative_follow_up='outside_discovery',
        low_nibble_parser='outside_slice', **{'0704_07FE_distinction':'outside_slice'},
        shared_io_ordering='does_not_merge_variants', admission=False,
        mcp_graphql='no_surface_change', stability='pre_1.0')
    assert [r['id'] for r in c['builders']] == ['ordinary', 'narrowed', 'short']
    for r in c['builders']:
        assert tuple(r[k] for k in ('remainder', 'quotient', 'quotient_low8',
                                   'output', 'full_identity')) == expected_builder(
                                       r['identifier'], r['versions'], r['number'])
    assert [r['event'] for r in c['transitions']] == ['short_success', 'clear', 'copy']
    for r in c['transitions']:
        assert r['target'] in ('store_a', 'store_b')
        assert r['full_identity'] is False
        assert r['other_store'] == 'preserved' and r['scratch'] == 'separate'
        event = r['event']
        assert r['last_known_good'] == {'short_success':'preserved',
            'clear':'cleared_selected', 'copy':'preserved_pending_completion'}[event]
        assert r['local_success'] is (True if event == 'short_success' else None)
        assert r['raw'] == {'short_success':[65,66,67,68], 'clear':[], 'copy':[65,66]}[event]


def rows(page):
    return [tuple(cell.strip() for cell in line.strip().strip('|').split('|'))
            for line in page.splitlines() if line.startswith('|')]


class AJ27Contract(unittest.TestCase):
    def setUp(self):
        self.c = json.loads(FIXTURE.read_text())
        self.page = PAGE.read_text()

    def test_valid_fixture(self):
        validate(self.c)

    def test_page_tables(self):
        table = rows(self.page)
        for row in [('direction','local_response'), ('prefix','B5'),
                    ('identifier','five raw bytes, in supplied order'),
                    ('versions','two decimal inputs, each packed decimal only within 0..99'),
                    ('number','remainder modulo 100, then quotient divided by 100 narrowed to low 8 bits'),
                    ('data_bytes','10'), ('grade','Hypothesis'),
                    ('A','230','06 ED EE EF F2','FC 0A 12','Unknown','Unknown','7'),
                    ('B','0','06','FC','3','2','6'),
                    ('queue_seconds','180','queue_timeout'),
                    ('physical_response_seconds','Unknown','Unknown')]:
            with self.subTest(row=row):
                self.assertEqual(table.count(row), 1)
        for key in UNKNOWN:
            self.assertIn((key, 'Unknown'), table)
        for r in self.c['builders']:
            output = 'Unknown' if r['output'] is None else ' '.join(f'{n:02X}' for n in r['output'])
            self.assertIn((r['id'], ' '.join(f'{n:02X}' for n in r['identifier']),
                ' / '.join(map(str,r['versions'])), str(r['number']), str(r['remainder']),
                str(r['quotient']), str(r['quotient_low8']), output,
                str(r['full_identity']).lower()), table)

    def test_independent_arithmetic(self):
        self.assertEqual(expected_builder([65,66,67,68,69], [12,34], 417),
            (17,4,4,[181,65,66,67,68,69,0x12,0x34,0x17,0x04],True))
        self.assertEqual(expected_builder([65,66,67,68,69], [12,34], 65535),
                         (35,655,143,None,False))
        for n in (0,1,99,100,25599,25600,65535):
            r,q,low,out,full = expected_builder([1,2,3,4,5], [0,99], n)
            self.assertEqual(q*100+r,n)
            self.assertEqual(low,q & 255)
            self.assertEqual(full,low <= 99)
        for i in range(5):
            identifier=[65,66,67,68,69]
            identifier[i] += 1
            out=expected_builder(identifier,[12,34],417)[3]
            self.assertEqual(out[1:6],identifier)
        for i in range(2):
            v=[12,34]
            v[i]=56
            self.assertEqual(expected_builder([1,2,3,4,5],v,417)[3][6+i],0x56)
            v[i]=100
            self.assertIsNone(expected_builder([1,2,3,4,5],v,417)[3])
        for length in (0,4,6):
            self.assertFalse(expected_builder([65]*length,[12,34],417)[4])

    def test_builder_requires_two_versions(self):
        for versions in ([], [12], [12,34,56], [12,34,56,78]):
            with self.subTest(versions=versions):
                self.assertEqual(expected_builder([65,66,67,68,69], versions, 417),
                                 (17,4,4,None,False))
                m=copy.deepcopy(self.c)
                r=m['builders'][0]
                r['versions']=versions
                r['output']=[181,65,66,67,68,69, *[packed(v) for v in versions], 0x17,0x04]
                r['full_identity']=True
                with self.assertRaises(AssertionError):
                    validate(m)

    def test_builder_requires_identifier_bytes(self):
        for index in range(5):
            for value in (300, -1, True, 65.0, 'A', None):
                with self.subTest(index=index, value=value):
                    m=copy.deepcopy(self.c)
                    r=m['builders'][0]
                    r['identifier'][index]=value
                    r['output'][1+index]=value
                    self.assertEqual(expected_builder(r['identifier'], r['versions'],
                                                     r['number']),
                                     (17,4,4,None,False))
                    with self.assertRaises(AssertionError):
                        validate(m)
            for value in (0, 255):
                with self.subTest(index=index, value=value):
                    m=copy.deepcopy(self.c)
                    r=m['builders'][0]
                    r['identifier'][index]=value
                    r['output'][1+index]=value
                    validate(m)

    def test_all_fixed_fields_reject_mutation(self):
        # Every leaf of the fixed contract is varied independently, including
        # variant names, set members, direction, grades and absent facts.
        for section in ('builder','variants','queue','lifecycles','selection','boundaries','unknown'):
            def leaves(value, path):
                if isinstance(value,dict):
                    for key,item in value.items():
                        yield from leaves(item,path+[key])
                elif isinstance(value,list):
                    for i,item in enumerate(value):
                        yield from leaves(item,path+[i])
                else:
                    yield path
            for path in leaves(self.c[section],[section]):
                with self.subTest(path=path):
                    mutant=copy.deepcopy(self.c)
                    parent=mutant
                    for key in path[:-1]:
                        parent=parent[key]
                    parent[path[-1]]='fabricated'
                    with self.assertRaises(AssertionError):
                        validate(mutant)
        for key in ('grade','native_behavior','physical_qualification','runtime_implemented'):
            m=copy.deepcopy(self.c)
            m[key]='Proven'
            with self.assertRaises(AssertionError):
                validate(m)
        for variant in ('A','B'):
            m=copy.deepcopy(self.c)
            m['variants']['other']=m['variants'].pop(variant)
            with self.assertRaises(AssertionError):
                validate(m)

    def test_candidate_and_scope_prose(self):
        text = ' '.join(self.page.split())
        for clause in (
            'candidate is **Hypothesis**.',
            'Native behavior remains Unknown.',
            'Exact capacities, copy ordering and short read completion rules are **Unknown**.',
            'The actual import/override predicates and path precedence are **Unknown**.',
            'A setter does not imply persistence.',
            'shared I/O/coupler ordering does not merge them.',
            'Mutative follow-up stays outside discovery.',
            'No responder, scanner, GPIO, request path, polling default or control execution is implemented.',
            'These offline checks establish no physical result or admission.',
        ):
            with self.subTest(clause=clause):
                self.assertIn(clause, text)

    def test_explicit_forbidden_promotions(self):
        changes = [
            ('variants', 'A', 'max_attempts', 8),
            ('variants', 'B', 'max_attempts', 7),
            ('variants', 'B', 'solar', ['06','ED','EE','EF','F2']),
            ('variants', 'B', 'secondary', ['FC','0A','12']),
            ('unknown', 'store_a_capacity', 5),
            ('unknown', 'store_b_capacity', 5),
            ('selection', 'unconditional_import', True),
            ('lifecycles', 'short_success_full_identity', True),
            ('queue', 'meaning', 'physical_response_timeout'),
            ('queue', 'physical_timing', 180),
        ]
        for *path, value in changes:
            m=copy.deepcopy(self.c)
            node=m
            for key in path[:-1]:
                node=node[key]
            node[path[-1]]=value
            with self.subTest(path=path,value=value):
                with self.assertRaises(AssertionError):
                    validate(m)

    def test_builder_input_mutations(self):
        # Unchanged outputs must reject every independent raw identity change.
        for field, indices in (('identifier', range(5)), ('versions', range(2))):
            for index in indices:
                m=copy.deepcopy(self.c)
                m['builders'][0][field][index] += 1
                with self.subTest(field=field,index=index):
                    with self.assertRaises(AssertionError):
                        validate(m)
        for number in (418,517,26017):
            m=copy.deepcopy(self.c)
            m['builders'][0]['number']=number
            with self.assertRaises(AssertionError):
                validate(m)

    def test_builder_derived_field_mutations(self):
        for i,r in enumerate(self.c['builders']):
            for field in ('remainder','quotient','quotient_low8','output','full_identity'):
                with self.subTest(case=r['id'],field=field):
                    m=copy.deepcopy(self.c)
                    m['builders'][i][field]='fabricated'
                    with self.assertRaises(AssertionError):
                        validate(m)

    def test_transition_controls_and_rejections(self):
        for target in ('store_a','store_b'):
            c=copy.deepcopy(self.c)
            for r in c['transitions']:
                r['target']=target
            validate(c)
        for i in range(3):
            for field in self.c['transitions'][i]:
                with self.subTest(event=i,field=field):
                    m=copy.deepcopy(self.c)
                    m['transitions'][i][field]='fabricated'
                    with self.assertRaises((AssertionError,KeyError)):
                        validate(m)

    def test_selection_paths_and_predicates(self):
        for condition in (True,False,None):
            self.assertEqual(selection('gpio',condition),'gpio')
        self.assertEqual(selection('conditional_import',True),'import')
        for condition in (False,None):
            self.assertEqual(selection('conditional_import',condition),'withheld')
        self.assertEqual(selection('other',True),'withheld')

    def test_budget_boundaries(self):
        for n in range(8):
            self.assertTrue(budget('A',[n]))
        self.assertFalse(budget('A',[8]))
        for jobs in itertools.product(range(3),repeat=3):
            self.assertTrue(budget('B',list(jobs)))
        for jobs in ([2,2,3],[2,2,2,1],[3],[-1]):
            self.assertFalse(budget('B',jobs))
        self.assertFalse(budget('other',[1]))
        self.assertTrue(budget('B',[]))


if __name__ == '__main__':
    unittest.main()
