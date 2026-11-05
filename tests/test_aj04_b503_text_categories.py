"""Independent document/tuple expectations; no physical or runtime qualification."""
import copy
import json
from pathlib import Path
import re
import tempfile
import unittest

Ab96Root = Path(__file__).resolve().parents[1]
Ab96Paths = (
    'protocols/vaillant/ebus-b503-text-categories.md',
    'protocols/vaillant/fixtures/aj04_b503_text_categories.json',
    'architecture/aj04_b503_text_categories_api.md',
)
Ab96Fields = [
    (3, 'unlock', 8, None, None),
    (3, 'trailing-byte', 1, 'unsigned byte', 0),
    (4, 'text', None, 'ASCII', None),
    (5, 'text', None, 'ASCII', None),
    (5, 'mode', 1, 'unsigned byte', None),
    (6, 'unlock', 8, None, None),
    (6, 'trailing-byte', 1, 'unsigned byte', 0),
]
Ab96CategoryRows = [
    ('common', 1, True, None, 'Hypothesis'),
    ('common', 2, True, 'predictive maintenance', 'Hypothesis'),
    ('common', 3, True, None, 'Hypothesis'),
    ('common', 4, True, None, 'Hypothesis'),
    ('common', 5, True, None, 'Hypothesis'),
    ('reset', 1, True, 'error', 'Hypothesis'),
    ('reset', 2, False, None, 'Unknown'),
    ('reset', 3, True, 'status', 'Hypothesis'),
]
Ab96KeyRows = [
    ('Ab96Family', 'string'), ('Ab96Variant', 'string'),
    ('Ab96Primary', '*uint8'), ('Ab96Secondary', '*uint8'),
    ('Ab96Operation', '*uint8'), ('Ab96Direction', 'string'),
    ('Ab96Field', 'string'), ('Ab96Group', '*uint8'),
    ('Ab96RequestedInstance', '*uint8'), ('Ab96Register', '*uint16'),
    ('Ab96CommandRole', 'string'),
]
Ab96NativeClauses = (
    'Each supplied native field is **Hypothesis**; unprovided properties remain **Unknown**.',
    'For OP03 and OP06, the separate unsigned byte follows the eight-character unlock field.',
    'OP04 and OP05 text extends through its declared data extent.',
    'ASCII `41 42` represents `AB`.',
    'OP05 mode is a separate byte, never the numeric value `FFFFFFFF`.',
    'Character encoding, padding and absolute coordinates are Unknown;',
    'Its position relative to variable text is Unknown.',
    'no fixed tail position or rule splitting a physical payload follows.',
    'The direction and operation associated with these category alternatives are Unknown.',
    'Never extend the reset alternative using common labels.',
    'Positive forms with only a declared prefix do not establish an empty physical response.',
    'Physical success, session exclusivity and physical effects are **Unknown**.',
    'a prefix-only or ambiguous form cannot replace it or establish success.',
)
Ab96ApiClauses = (
    'These are the only exposed functions.',
    '`Ab96Entry` retains `Ab96Key`, `Ab96Grade`, `Ab96Raw`, `Ab96Unknown` and `Ab96Data` as independent properties.',
    'Every new declaration and field uses the `Ab96` or `ab96` prefix;',
    'All axes participate in identity independently.',
    'absent differs from explicit zero.',
    'never pointer address:',
    'equal register numbers never merge operation namespaces.',
    '`Ab96Grade` is Proven, Hypothesis or Unknown, independently of raw evidence, unknown metadata and physical qualification.',
    'including keys\' numeric pointers, raw slices, unknown metadata and any nested maps, slices or pointers in `Ab96Data`.',
    'Mutating one result must change neither embedded data, another result, nor a later call.',
    'Entries within the same returned list must not share mutable nested storage.',
    'A well-formed missing key returns `Ab96Entry{}, false, nil`.',
    '`Ab96Entries` returns no entries and an error,',
    '`Ab96Lookup` returns `Ab96Entry{}, false` and an error, even for a key that would otherwise match or be missing.',
    'No partially validated successful result escapes.',
    'Nothing here is stable before 1.0.',
)


def ab96Expected():
    return {
        'ab96Family': 'Vaillant', 'ab96Primary': 181, 'ab96Secondary': 3,
        'ab96Declarations': [dict(zip(
            ('ab96Operation', 'ab96Field', 'ab96Width', 'ab96Encoding', 'ab96Default'), ab96Row),
            ab96Variant=None, ab96Direction=None, ab96Coordinate=None,
            ab96Grade='Hypothesis') for ab96Row in Ab96Fields],
        'ab96Categories': [dict(ab96Family='Vaillant', ab96Variant=ab96Variant,
            ab96Direction=None, ab96Category=ab96Value, ab96Named=ab96Named,
            ab96Label=ab96Label, ab96Grade=ab96Grade)
            for ab96Variant, ab96Value, ab96Named, ab96Label, ab96Grade in Ab96CategoryRows],
        'ab96Unknown': ['physical offsets', 'wire termination', 'success',
            'session exclusivity', 'physical effects', 'unlock encoding',
            'unlock padding', 'mode position'],
        'ab96UnlockCases': [
            {'ab96Raw': 'ABCDEFG', 'ab96DeclaredWidthMatch': False},
            {'ab96Raw': 'ABCDEFGH', 'ab96DeclaredWidthMatch': True},
            {'ab96Raw': 'ABCDEFGHI', 'ab96DeclaredWidthMatch': False}],
        'ab96TextCases': [
            {'ab96Operation': 4, 'ab96Raw': [65, 66], 'ab96Text': 'AB', 'ab96ModeCoordinate': None},
            {'ab96Operation': 5, 'ab96Raw': [], 'ab96Text': '', 'ab96ModeCoordinate': None},
            {'ab96Operation': 5, 'ab96Raw': [65, 66], 'ab96Text': 'AB', 'ab96ModeCoordinate': None},
            {'ab96Operation': 5, 'ab96Raw': [65, 66, 67, 68, 69], 'ab96Text': 'ABCDE', 'ab96ModeCoordinate': None}],
        'ab96Partial': {'ab96Raw': [181, 3, 5], 'ab96LastKnownGoodRaw': [65, 66],
            'ab96PhysicalSuccess': None, 'ab96ReplaceLastKnownGood': False,
            'ab96Qualification': 'Unknown'},
    }


def ab96Rows(ab96Text, ab96Header):
    ab96Lines = ab96Text.splitlines()
    ab96Start = ab96Lines.index(ab96Header) + 2
    ab96Result = []
    for ab96Line in ab96Lines[ab96Start:]:
        if not ab96Line.startswith('|'):
            break
        ab96Result.append([ab96Cell.strip() for ab96Cell in ab96Line.strip('|').split('|')])
    return ab96Result


class Ab96Contract(unittest.TestCase):
    Ab96Kills = 0

    @classmethod
    def tearDownClass(cls):
        print(f'Ab96 executed document/tuple mutant kills: {cls.Ab96Kills}; '
              f'valid controls: {cls.Ab96Kills}')

    def ab96Validate(self, ab96Root):
        ab96Native, ab96Fixture, ab96Api = [(ab96Root / ab96Path).read_text()
            for ab96Path in Ab96Paths]
        # Strict JSON rendering comparison also distinguishes bool from numeric zero/one.
        self.assertEqual(json.dumps(json.loads(ab96Fixture), sort_keys=True),
                         json.dumps(ab96Expected(), sort_keys=True))
        ab96RowsExpected = []
        for ab96Op, ab96Field, ab96Width, ab96Encoding, ab96Default in Ab96Fields:
            ab96RowsExpected.append([
                f'{ab96Op:02X}', 'Unknown', 'Unknown', ab96Field,
                '8 characters' if ab96Field == 'unlock' else
                'through data extent' if ab96Field == 'text' else '1 byte',
                ab96Encoding or 'Unknown', str(ab96Default) if ab96Default is not None else 'Unknown',
                'Unknown', 'Hypothesis'])
        self.assertEqual(ab96Rows(ab96Native,
            '| operation | variant | direction | field | width | encoding | default | coordinate | grade |'), ab96RowsExpected)
        self.assertEqual(ab96Rows(ab96Native,
            '| family | variant | direction | category | named | label | grade |'),
            [['Vaillant', ab96Variant, 'Unknown', str(ab96Value),
              'yes' if ab96Named else 'no', ab96Label or 'Unknown', ab96Grade]
             for ab96Variant, ab96Value, ab96Named, ab96Label, ab96Grade in Ab96CategoryRows])
        self.assertEqual(ab96Rows(ab96Api, '| type | field | representation |'),
                         [['Ab96Key', *ab96Row] for ab96Row in Ab96KeyRows])
        self.assertEqual(re.findall(r'^Ab96\w+\(.*$', ab96Api, re.M), [
            'Ab96Entries() ([]Ab96Entry, error)',
            'Ab96Lookup(key Ab96Key) (Ab96Entry, bool, error)'])
        for ab96Text, ab96Clauses in [(ab96Native, Ab96NativeClauses), (ab96Api, Ab96ApiClauses)]:
            ab96Flat = ' '.join(ab96Text.split())
            for ab96Clause in ab96Clauses:
                self.assertIn(ab96Clause, ab96Flat)
        self.assertNotRegex(ab96Native, r'Ab96|GraphQL|MCP|CLI|unittest')
        for ab96Target in re.findall(r'\]\(([^)]+)\)', ab96Native):
            self.assertTrue((ab96Root / Ab96Paths[0]).parent.joinpath(ab96Target).resolve()
                .is_relative_to((ab96Root / 'protocols').resolve()))

    def ab96RejectFixture(self, ab96Mutation):
        # Every executed mutant lives in a disposable temporary copy.
        with tempfile.TemporaryDirectory(prefix='ab96-') as ab96Temp:
            ab96Root = Path(ab96Temp)
            for ab96Path in Ab96Paths:
                (ab96Root / ab96Path).parent.mkdir(parents=True, exist_ok=True)
                (ab96Root / ab96Path).write_text((Ab96Root / ab96Path).read_text())
            self.ab96Validate(ab96Root)  # valid control for every mutant
            ab96Fixture = json.loads((ab96Root / Ab96Paths[1]).read_text())
            ab96Mutation(ab96Fixture)
            (ab96Root / Ab96Paths[1]).write_text(json.dumps(ab96Fixture))
            with self.assertRaises(AssertionError):
                self.ab96Validate(ab96Root)
            type(self).Ab96Kills += 1

    def test_ab96_valid_documents_and_tuples(self):
        self.ab96Validate(Ab96Root)

    def test_ab96_synthetic_representation_controls(self):
        ab96Data = json.loads((Ab96Root / Ab96Paths[1]).read_text())
        self.assertEqual([len(ab96Row['ab96Raw']) for ab96Row in
                          ab96Data['ab96UnlockCases']], [7, 8, 9])
        for ab96Row in ab96Data['ab96UnlockCases']:
            self.assertEqual(ab96Row['ab96DeclaredWidthMatch'],
                             len(ab96Row['ab96Raw']) == 8)
        for ab96Row in ab96Data['ab96TextCases']:
            self.assertEqual(bytes(ab96Row['ab96Raw']).decode('ascii'), ab96Row['ab96Text'])
            self.assertIsNone(ab96Row['ab96ModeCoordinate'])
        self.assertEqual([len(ab96Row['ab96Raw']) for ab96Row in ab96Data['ab96TextCases']
                          if ab96Row['ab96Operation'] == 5], [0, 2, 5])

    def test_ab96_every_declaration_field_independently(self):
        for ab96Index, ab96Row in enumerate(ab96Expected()['ab96Declarations']):
            for ab96Field, ab96Value in ab96Row.items():
                with self.subTest(row=ab96Index, field=ab96Field):
                    ab96Replacement = 0 if ab96Value is None else 'fabricated'
                    self.ab96RejectFixture(lambda ab96Data, i=ab96Index, f=ab96Field, v=ab96Replacement:
                        ab96Data['ab96Declarations'][i].__setitem__(f, v))

    def test_ab96_every_category_axis_and_predicate_independently(self):
        for ab96Index, ab96Row in enumerate(ab96Expected()['ab96Categories']):
            for ab96Field, ab96Value in ab96Row.items():
                with self.subTest(row=ab96Index, field=ab96Field):
                    ab96Replacement = not ab96Value if isinstance(ab96Value, bool) else 'fabricated'
                    self.ab96RejectFixture(lambda ab96Data, i=ab96Index, f=ab96Field, v=ab96Replacement:
                        ab96Data['ab96Categories'][i].__setitem__(f, v))

    def test_ab96_family_primary_secondary_independently(self):
        for ab96Field in ('ab96Family', 'ab96Primary', 'ab96Secondary'):
            with self.subTest(field=ab96Field):
                self.ab96RejectFixture(lambda ab96Data, f=ab96Field: ab96Data.__setitem__(f, 0))

    def test_ab96_required_bad_mode_and_unlock_mutations(self):
        for ab96Index, ab96Field, ab96Value in [(4, 'ab96Default', 0xFFFFFFFF),
                (4, 'ab96Width', 4), (0, 'ab96Width', 7), (5, 'ab96Width', 7)]:
            with self.subTest(row=ab96Index, field=ab96Field):
                self.ab96RejectFixture(lambda ab96Data, i=ab96Index, f=ab96Field, v=ab96Value:
                    ab96Data['ab96Declarations'][i].__setitem__(f, v))
        for ab96Index in (1, 2, 3):
            self.ab96RejectFixture(lambda ab96Data, i=ab96Index:
                ab96Data['ab96TextCases'][i].__setitem__('ab96ModeCoordinate',
                    len(ab96Data['ab96TextCases'][i]['ab96Raw'])))

    def test_ab96_reset_does_not_inherit_common_label(self):
        self.ab96RejectFixture(lambda ab96Data: ab96Data['ab96Categories'][6]
            .__setitem__('ab96Label', 'predictive maintenance'))

    def test_ab96_all_synthetic_raw_and_result_fields_independently(self):
        for ab96Collection in ('ab96UnlockCases', 'ab96TextCases'):
            for ab96Index, ab96Row in enumerate(ab96Expected()[ab96Collection]):
                for ab96Field in ab96Row:
                    with self.subTest(collection=ab96Collection, row=ab96Index, field=ab96Field):
                        self.ab96RejectFixture(lambda ab96Data, c=ab96Collection, i=ab96Index, f=ab96Field:
                            ab96Data[c][i].__setitem__(f, 'fabricated'))

    def test_ab96_partial_state_and_qualification_independently(self):
        for ab96Field in ab96Expected()['ab96Partial']:
            with self.subTest(field=ab96Field):
                self.ab96RejectFixture(lambda ab96Data, f=ab96Field:
                    ab96Data['ab96Partial'].__setitem__(f, True))

    def test_ab96_each_unknown_cannot_be_fabricated(self):
        for ab96Index in range(len(ab96Expected()['ab96Unknown'])):
            self.ab96RejectFixture(lambda ab96Data, i=ab96Index:
                ab96Data['ab96Unknown'].__setitem__(i, 'Proven'))

    def test_ab96_page_rows_and_api_axes_independently(self):
        for ab96PathIndex, ab96Header in [
            (0, '| operation | variant | direction | field | width | encoding | default | coordinate | grade |'),
            (0, '| family | variant | direction | category | named | label | grade |'),
            (2, '| type | field | representation |')]:
            ab96Text = (Ab96Root / Ab96Paths[ab96PathIndex]).read_text()
            for ab96Index, ab96Row in enumerate(ab96Rows(ab96Text, ab96Header)):
                for ab96Column in range(len(ab96Row)):
                    with self.subTest(table=ab96Header, row=ab96Index, column=ab96Column):
                        ab96Old = '| ' + ' | '.join(ab96Row) + ' |'
                        ab96Changed = list(ab96Row)
                        ab96Changed[ab96Column] = 'fabricated'
                        self.ab96RejectPage(ab96PathIndex, ab96Old,
                            '| ' + ' | '.join(ab96Changed) + ' |')

    def ab96RejectPage(self, ab96Index, ab96Old, ab96New):
        with tempfile.TemporaryDirectory(prefix='ab96-') as ab96Temp:
            ab96Root = Path(ab96Temp)
            for ab96Path in Ab96Paths:
                (ab96Root / ab96Path).parent.mkdir(parents=True, exist_ok=True)
                (ab96Root / ab96Path).write_text((Ab96Root / ab96Path).read_text())
            self.ab96Validate(ab96Root)
            ab96Path = ab96Root / Ab96Paths[ab96Index]
            self.assertIn(ab96Old, ab96Path.read_text())
            ab96Path.write_text(ab96Path.read_text().replace(ab96Old, ab96New, 1))
            with self.assertRaises(AssertionError):
                self.ab96Validate(ab96Root)
            type(self).Ab96Kills += 1

    def test_ab96_critical_prose_and_signatures(self):
        for ab96Index, ab96Clauses in [(0, Ab96NativeClauses), (2, Ab96ApiClauses)]:
            ab96Text = (Ab96Root / Ab96Paths[ab96Index]).read_text()
            for ab96Clause in ab96Clauses:
                ab96Match = re.search(r'\s+'.join(re.escape(ab96Word) for ab96Word in ab96Clause.split()), ab96Text)
                self.assertIsNotNone(ab96Match)
                self.ab96RejectPage(ab96Index, ab96Match.group(), 'fabricated')
        for ab96Signature in ('Ab96Entries() ([]Ab96Entry, error)',
                'Ab96Lookup(key Ab96Key) (Ab96Entry, bool, error)'):
            self.ab96RejectPage(2, ab96Signature, ab96Signature.replace('error', 'bool'))


if __name__ == '__main__':
    unittest.main()
