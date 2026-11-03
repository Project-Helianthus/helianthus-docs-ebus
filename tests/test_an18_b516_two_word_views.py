"""Synthetic AN18 prose model and independent extent oracles.

Identity fields and the production mutation each focused check catches:

- family: admitting unknown-family still decodes word0.
- variant: admitting unknown-variant still decodes word0.
- operation: treating OP08 as OP14 still decodes word0.
- direction: treating request as positive still decodes word0.
- selection: a missing selection still decodes word0.
- declared_count: declared 4 with available 9 still exposes word0,
  or declared 8 with available 9 becomes complete-two-word.
- available length: a 4-byte slice with declared 9 still exposes word0,
  or an 8-byte slice with declared 9 becomes complete-two-word.
"""
import copy
from collections.abc import Mapping
import json
import math
import os
from pathlib import Path
import re
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = Path(os.environ['AN18_PAGE']) if os.environ.get('AN18_PAGE') else (
    ROOT / 'architecture/an18_b516_two_word_views.md')
FIXTURE = Path(os.environ['AN18_FIXTURE']) if os.environ.get('AN18_FIXTURE') else (
    ROOT / 'architecture/fixtures/an18_b516_two_word_views.json')

FAMILIES = ('synthetic-power-family-a', 'synthetic-power-family-b')
VARIANTS = ('synthetic-variant-a', 'synthetic-variant-b')
CONTEXT_FIELDS = (
    'family', 'variant', 'operation', 'direction', 'declared_count', 'selection')
PATTERN = bytes.fromhex('000000803f01020304aa')
POLICY = {
    'helper': 'ab17an17.view(context, body)',
    'context_fields': list(CONTEXT_FIELDS),
    'families': list(FAMILIES),
    'variants': list(VARIANTS),
    'operation': 'OP14',
    'direction': 'positive',
    'selection': 'preselected',
    'declared_count': 'nonnegative integer',
    'body': 'owned available-byte slice',
    'transport_adaptation': False,
    'preselected_normalized_body': True,
    'extent_rule': 'both',
    'status_end': 1,
    'word0_end': 5,
    'word1_end': 9,
    'two_word_minimum': 9,
    'accept_eight_byte_two_words': False,
    'declared_count_alone': False,
    'available_length_alone': False,
    'capacity_is_extent': False,
    'read_past_actual': False,
    'status_label': None,
    'status_converter': None,
    'word0_codec': 'float32le',
    'word0_quantity': 'candidate_power',
    'word0_unit': None,
    'word0_native_sign': 'Unknown',
    'asserts_watts': False,
    'unsigned_power_conversion': False,
    'word1_label': None,
    'word1_type': 'Unknown',
    'word1_scale': 'Unknown',
    'word1_sign': 'Unknown',
    'word1_converter': None,
    'partial_word0_without_word1': True,
    'retain_nonfinite_raw': True,
    'usable_finite_for_nonfinite': False,
    'trailing_raw': True,
    'complete_two_word_implies_complete_message': False,
    'complete_two_word_implies_successful_response': False,
    'complete_two_word_implies_presence': False,
    'physical_reply_extent': 'Unknown',
    'support': 'Unknown',
    'cache_generation': 'Unknown',
    'cadence': 'Unknown',
    'runtime_publication': 'Unknown',
    'native_units': 'Unknown',
    'interpretation_grade': 'Hypothesis',
    'software_contract': 'Proven',
    'native_grade': 'Unknown',
}
AXES = {
    'families': ['synthetic-power-family-a', 'synthetic-power-family-b', 'unknown-family'],
    'variants': ['synthetic-variant-a', 'synthetic-variant-b', 'unknown-variant'],
    'operations': ['OP14', 'OP08', 'OP10'],
    'directions': ['positive', 'request'],
    'selections': ['preselected', 'missing'],
    'declared_counts': [0, 4, 8, 9, 10, -1],
    'available_lengths': [0, 4, 8, 9, 10],
}
EXTENT_ROWS = (
    ('both0', 0, 0, False, False, False, False),
    ('both1', 1, 1, True, False, False, False),
    ('both5', 5, 5, True, True, False, False),
    ('actual9_declared4', 4, 9, True, False, False, False),
    ('actual8_declared9', 9, 8, True, True, False, False),
    ('actual9_declared8', 8, 9, True, True, False, False),
    ('canonical', 9, 9, True, True, True, True),
    ('tail10', 10, 10, True, True, True, True),
)
FLOAT_ROWS = (
    ('canonical', '00 00 80 3F', True, '1'),
    ('zero', '00 00 00 00', True, '0'),
    ('negative_zero', '00 00 00 80', True, '-0'),
    ('negative', '00 00 80 BF', True, '-1'),
    ('nan', '00 00 C0 7F', False, 'none'),
    ('payload_nan', '01 00 80 7F', False, 'none'),
    ('positive_infinity', '00 00 80 7F', False, 'none'),
    ('negative_infinity', '00 00 80 FF', False, 'none'),
)
SENTENCES = (
    'ab17an17.view(context, body)',
    'Pair with AN17.',
    'Complete-two-word state requires both declared count>=9 and available length>=9.',
    'Neither declared count alone nor available length alone admits a field.',
    'Eight available bytes are not two complete words.',
    'The helper does not read past the actual available slice.',
    'Status stays unlabelled and has no converter.',
    'Word1 stays unlabelled and has no converter.',
    'Word0 is never watts and is never an unsigned integer.',
    'NaN and infinities retain raw bits and have no usable finite numeric value.',
    'A fully available word0 may be returned as a partial candidate field when the second is incomplete.',
    'Actual8/declared9 and actual9/declared8 are not complete-two-word.',
    'Actual9/declared4 does not expose word0.',
    'complete-two-word is not a complete message, a successful response, or presence.',
    'No conversion of negative or nonfinite bits to unsigned power.',
    'Every available length from 0 through 10 is paired with every declared count from 0 through 10.',
    'eBUS MCP compatibility and GraphQL parity',
    'last-known-good',
    'Nothing here is stable before Helianthus 1.0.',
    'Physical reply extent, support, cache generation, cadence, runtime publication and native units stay Unknown.',
)
FORBIDDEN = (
    ('declared-only-prose', 'Declared count alone is sufficient'),
    ('available-only-prose', 'Available length alone is sufficient'),
    ('eight-bytes-prose', 'Eight available bytes are two complete words'),
    ('read-past-prose', 'The helper reads past the actual available slice'),
    ('status-label-prose', 'Status label is ok'),
    ('word1-label-prose', 'Word1 label is secondary'),
    ('watts-prose', 'Word0 unit is watts'),
    ('nonfinite-prose', 'Nonfinite raw bits are dropped'),
    ('unsigned-prose', 'Negative bits are unsigned power'),
)


def publication_root():
    for candidate in Path(__file__).resolve().parents:
        native = candidate / 'protocols/vaillant/ebus-vaillant-B516-energy.md'
        if native.is_file():
            return candidate
    raise AssertionError('local public B516 page is unavailable')


def resolve_link(rel):
    primary = (PAGE.parent / rel).resolve()
    if primary.is_file():
        return primary
    return (publication_root() / 'architecture' / rel).resolve()


def slug(heading):
    return re.sub(r'[^\w -]', '', heading.lower()).replace(' ', '-')


def is_buffer(value):
    return isinstance(value, (bytes, bytearray, memoryview)) and not isinstance(value, str)


def manual_f32(raw):
    """Independent binary32 decode. Nonfinite values have no usable number."""
    bits = int.from_bytes(raw, 'little')
    sign = -1.0 if (bits >> 31) else 1.0
    exp = (bits >> 23) & 0xFF
    frac = bits & ((1 << 23) - 1)
    if exp == 255:
        return None
    if exp == 0:
        magnitude = (frac / float(1 << 23)) * (2.0 ** -126)
    else:
        magnitude = (1.0 + frac / float(1 << 23)) * (2.0 ** (exp - 127))
    return sign * magnitude


def independent_extent(declared, available):
    """Conjunction oracle. Not used by the reference view."""
    return {
        'status': declared >= 1 and available >= 1,
        'word0': declared >= 5 and available >= 5,
        'word1': declared >= 9 and available >= 9,
        'complete': declared >= 9 and available >= 9,
    }


def page_policy(page):
    return json.loads(re.search(r'```json\n(.*?)\n```', page, re.S)[1])


def context(**patch):
    base = {
        'family': 'synthetic-power-family-a',
        'variant': 'synthetic-variant-a',
        'operation': 'OP14',
        'direction': 'positive',
        'declared_count': 9,
        'selection': 'preselected',
    }
    base.update(patch)
    return base


def classify(ctx):
    if ctx.get('family') not in FAMILIES:
        return 'raw_only', 'family'
    if ctx.get('variant') not in VARIANTS:
        return 'raw_only', 'variant'
    if ctx.get('operation') != 'OP14':
        return 'raw_only', 'operation'
    if ctx.get('direction') != 'positive':
        return 'raw_only', 'direction'
    if ctx.get('selection') != 'preselected':
        return 'missing_selection', 'selection'
    declared = ctx.get('declared_count')
    if type(declared) is not int or declared < 0:
        return 'raw_only', 'declared_count'
    return 'candidate', None


def take(raw, start, end):
    if end > len(raw):
        raise AssertionError('read past actual')
    return bytearray(raw[start:end])


def view(ctx, body):
    """ab17an17.view(context, body) reference model of the architecture page."""
    if not isinstance(ctx, Mapping) or not is_buffer(body):
        raise TypeError('context must be a mapping and body an owned slice')
    raw = bytearray(body)
    state, reason = classify(ctx)
    declared = ctx.get('declared_count')
    admitted_count = declared if state == 'candidate' else None
    available = len(raw)

    def covers(need):
        return admitted_count is not None and admitted_count >= need and available >= need

    status_available = covers(1)
    word0_available = covers(5)
    word1_available = covers(9)
    word0_raw = take(raw, 1, 5) if word0_available else None
    word0_numeric = None
    word0_finite = False
    if word0_raw is not None:
        unpacked = struct.unpack('<f', bytes(word0_raw))[0]
        if math.isfinite(unpacked):
            word0_numeric = unpacked
            word0_finite = True
    status = {
        'available': status_available,
        'raw': raw[0] if status_available else None,
        'label': None,
        'converter': None,
        'semantic_grade': 'Unknown',
        'native_grade': 'Unknown',
    }
    word0 = {
        'available': word0_available,
        'raw': word0_raw,
        'numeric': word0_numeric,
        'finite_numeric': word0_finite,
        'quantity': 'candidate_power' if word0_available else None,
        'unit': None,
        'unsigned_bits': None,
        'numeric_grade': 'Hypothesis' if word0_finite else None,
        'semantic_grade': 'Hypothesis' if word0_available else 'Unknown',
        'native_grade': 'Unknown',
    }
    word1 = {
        'available': word1_available,
        'raw': list(take(raw, 5, 9)) if word1_available else None,
        'label': None,
        'type': 'Unknown',
        'scale': 'Unknown',
        'sign': 'Unknown',
        'converter': None,
        'numeric': None,
        'semantic_grade': 'Unknown',
        'native_grade': 'Unknown',
    }
    return {
        'context': copy.deepcopy(ctx),
        'state': state,
        'reason': reason,
        'software_contract': 'Proven',
        'interpretation_grade': 'Hypothesis' if state == 'candidate' else None,
        'native_grade': 'Unknown',
        'declared_count': declared if type(declared) is int else None,
        'available_length': available,
        'raw': raw,
        'trailing': bytearray(raw[9:]),
        'status': status,
        'word0': word0,
        'word1': word1,
        'status_available': status_available,
        'word0_available': word0_available,
        'word1_available': word1_available,
        'finite_numeric': word0_finite,
        'complete_two_word': covers(9),
        'complete_message': False,
        'successful_response': False,
        'presence': 'Unknown',
        'physical_reply_extent': 'Unknown',
        'support': 'Unknown',
        'cache_generation': 'Unknown',
        'cadence': 'Unknown',
        'runtime_publication': 'Unknown',
        'native_units': 'Unknown',
    }


def parse_extent_table(page):
    rows = re.findall(
        r'^\| ([a-z0-9_]+) \| (\d+) \| (\d+) \| (true|false) \| '
        r'(true|false) \| (true|false) \| (true|false) \|$',
        page, re.M)
    parsed = []
    for name, declared, available, status, word0, word1, complete in rows:
        parsed.append((
            name, int(declared), int(available),
            status == 'true', word0 == 'true', word1 == 'true', complete == 'true'))
    return parsed


def parse_float_table(page):
    rows = re.findall(
        r'^\| ([a-z_]+) \| ([0-9A-F]{2} [0-9A-F]{2} [0-9A-F]{2} [0-9A-F]{2}) \| '
        r'(true|false) \| (none|-0|-1|0|1) \|$',
        page, re.M)
    return [(name, raw, finite == 'true', numeric) for name, raw, finite, numeric in rows]


def machine(policy, declared, available):
    """Interpret a policy literally so an authorizing edit becomes visible."""
    avail = available
    if policy.get('read_past_actual') or policy.get('capacity_is_extent'):
        avail = max(available, declared)
    minimum = policy.get('two_word_minimum')
    word1_end = policy.get('word1_end')
    if policy.get('accept_eight_byte_two_words'):
        minimum = 8
        word1_end = 8
    rule = policy.get('extent_rule')
    if policy.get('declared_count_alone'):
        rule = 'declared_only'
    if policy.get('available_length_alone'):
        rule = 'available_only'

    def cover(need):
        if rule == 'declared_only':
            return declared >= need
        if rule == 'available_only':
            return avail >= need
        if rule == 'both':
            return declared >= need and avail >= need
        return None

    return {
        'status': cover(policy.get('status_end')),
        'word0': cover(policy.get('word0_end')),
        'word1': cover(word1_end),
        'complete': cover(minimum),
        'synthetic_length': avail,
    }


def authorization_codes(policy):
    codes = []
    got_declared = machine(policy, 9, 0)
    got_available = machine(policy, 0, 9)
    got_eight = machine(policy, 8, 8)
    if policy.get('declared_count_alone') is True or policy.get('extent_rule') == 'declared_only':
        codes.append('declared-only')
    if got_declared['complete'] is True and got_declared['synthetic_length'] == 0:
        codes.append('declared-only')
    if policy.get('available_length_alone') is True or policy.get('extent_rule') == 'available_only':
        codes.append('available-only')
    if got_available['complete'] is True and got_available['synthetic_length'] == 9:
        codes.append('available-only')
    if (policy.get('accept_eight_byte_two_words') is True
            or policy.get('two_word_minimum') != 9
            or got_eight['complete'] is True):
        codes.append('eight-bytes')
    if policy.get('read_past_actual') is True or policy.get('capacity_is_extent') is True:
        codes.append('read-past')
    if machine(policy, 9, 8)['synthetic_length'] != 8:
        codes.append('read-past')
    if policy.get('status_label') is not None or policy.get('status_converter') is not None:
        codes.append('status-label')
    if policy.get('word1_label') is not None or policy.get('word1_converter') is not None:
        codes.append('word1-label')
    if policy.get('asserts_watts') is True or policy.get('word0_unit') is not None:
        codes.append('watts')
    if policy.get('retain_nonfinite_raw') is not True or policy.get('usable_finite_for_nonfinite') is True:
        codes.append('nonfinite-raw')
    if policy.get('unsigned_power_conversion') is True:
        codes.append('unsigned-power')
    return codes


def prose_codes(page):
    return [code for code, phrase in FORBIDDEN if phrase in page]


def grid_codes(grid):
    codes = []
    seen = set()
    for row in grid:
        key = (row['declared'], row['available'])
        if key in seen:
            codes.append('grid-dup:%s:%s' % key)
        seen.add(key)
        expect = independent_extent(*key)
        if row['status_available'] != expect['status']:
            codes.append('grid:%s:%s:status' % key)
        if row['word0_available'] != expect['word0']:
            codes.append('grid:%s:%s:word0' % key)
        if row['word1_available'] != expect['word1']:
            codes.append('grid:%s:%s:word1' % key)
        if row['complete_two_word'] != expect['complete']:
            if key == (9, 8):
                codes.append('grid:declared-only')
            elif key == (8, 9):
                codes.append('grid:available-only')
            elif key == (8, 8):
                codes.append('grid:eight-bytes')
            elif key == (4, 9):
                codes.append('grid:declared4-word0')
            elif key == (9, 4):
                codes.append('grid:read-past')
            else:
                codes.append('grid:%s:%s:complete' % key)
        if key == (4, 9) and row['word0_available']:
            codes.append('grid:declared4-word0')
        if key == (9, 4) and row['word0_available']:
            codes.append('grid:read-past')
    for declared in range(11):
        for available in range(11):
            if (declared, available) not in seen:
                codes.append('grid-missing:%s:%s' % (declared, available))
    return codes


def case_definitions():
    def raw_with(word0_hex, word1_hex='01020304', status='00', tail=''):
        return bytes.fromhex(status + word0_hex + word1_hex + tail)

    rows = [
        ('canonical', '000000803f01020304', 9, {}),
        ('actual8_declared9', '000000803f010203', 9, {}),
        ('actual9_declared8', '000000803f01020304', 8, {}),
        ('actual9_declared4', '000000803f01020304', 4, {}),
        ('zero', raw_with('00000000').hex(), 9, {}),
        ('negative', raw_with('000080bf').hex(), 9, {}),
        ('negative_zero', raw_with('00000080').hex(), 9, {}),
        ('nan', raw_with('0000c07f').hex(), 9, {}),
        ('payload_nan', raw_with('0100807f').hex(), 9, {}),
        ('positive_infinity', raw_with('0000807f').hex(), 9, {}),
        ('negative_infinity', raw_with('000080ff').hex(), 9, {}),
        ('tail_aa', '000000803f01020304aa', 10, {}),
        ('status_unlabelled', '2a0000803f01020304', 9, {}),
        ('word1_unlabelled', '000000803fffffffff', 9, {}),
        ('wrong_operation', '000000803f01020304', 9, {'operation': 'OP08'}),
        ('wrong_direction', '000000803f01020304', 9, {'direction': 'request'}),
        ('missing_selection', '000000803f01020304', 9, {'selection': None}),
        ('negative_declared', '000000803f01020304', -1, {}),
    ]
    cases = []
    for name, raw_hex, declared, patch in rows:
        item = context(declared_count=declared)
        item.update(patch)
        if patch.get('selection') is None and 'selection' in patch:
            item.pop('selection')
        cases.append({'name': name, 'raw_hex': raw_hex, 'context': item})
    return cases


def expected_case(case):
    ctx = case['context']
    raw = bytes.fromhex(case['raw_hex'])
    state, reason = classify(ctx)
    declared = ctx.get('declared_count')
    available = len(raw)
    extent = {'status': False, 'word0': False, 'word1': False, 'complete': False}
    if state == 'candidate':
        extent = independent_extent(declared, available)
    word0_raw = raw[1:5] if extent['word0'] else None
    numeric = manual_f32(word0_raw) if word0_raw is not None else None
    finite = numeric is not None
    return {
        'state': state,
        'reason': reason,
        'status_available': extent['status'],
        'status_raw': raw[0] if extent['status'] else None,
        'status_label': None,
        'word0_available': extent['word0'],
        'word0_raw_hex': None if word0_raw is None else word0_raw.hex(),
        'word0_numeric': numeric,
        'word0_finite': finite,
        'word0_unit': None,
        'word1_available': extent['word1'],
        'word1': list(raw[5:9]) if extent['word1'] else None,
        'word1_label': None,
        'complete_two_word': extent['complete'],
        'finite_numeric': finite,
        'complete_message': False,
        'successful_response': False,
        'presence': 'Unknown',
        'trailing_hex': raw[9:].hex(),
        'raw_hex': raw.hex(),
    }


def build_package():
    grid = []
    for declared in range(11):
        for available in range(11):
            extent = independent_extent(declared, available)
            grid.append({
                'declared': declared,
                'available': available,
                'status_available': extent['status'],
                'word0_available': extent['word0'],
                'word1_available': extent['word1'],
                'complete_two_word': extent['complete'],
            })
    examples = []
    for case in case_definitions():
        expect = expected_case(case)
        stored = dict(expect)
        if case['name'] == 'negative_zero':
            stored['word0_numeric'] = -0.0
        examples.append({
            'name': case['name'],
            'raw_hex': case['raw_hex'],
            'context': case['context'],
            'expect': stored,
        })
    return {
        'policy': POLICY,
        'identity_axes': AXES,
        'extent_rows': [
            {
                'case': name,
                'declared': declared,
                'available': available,
                'status': status,
                'word0': word0,
                'word1': word1,
                'complete_two_word': complete,
            }
            for name, declared, available, status, word0, word1, complete in EXTENT_ROWS
        ],
        'float_rows': [
            {'case': name, 'raw': raw, 'finite': finite, 'numeric': numeric}
            for name, raw, finite, numeric in FLOAT_ROWS
        ],
        'grid': grid,
        'examples': examples,
    }


def same_number(left, right):
    if left is None or right is None:
        return left is right
    if isinstance(left, float) or isinstance(right, float):
        if math.isnan(left) or math.isnan(right):
            return False
        return left == right and math.copysign(1.0, left) == math.copysign(1.0, right)
    return left == right


def example_codes(examples):
    codes = []
    by_name = {case['name']: case for case in case_definitions()}
    seen = set()
    for example in examples:
        name = example['name']
        seen.add(name)
        if name not in by_name:
            codes.append('example:%s' % name)
            continue
        expect = expected_case(by_name[name])
        got = example['expect']
        for key, value in expect.items():
            if key == 'word0_numeric':
                if not same_number(got.get(key), value):
                    codes.append('example:%s' % name)
                    break
            elif got.get(key) != value:
                codes.append('example:%s' % name)
                break
        if name == 'nan' and got.get('word0_raw_hex') in (None, ''):
            codes.append('example:nan')
        if name == 'canonical' and got.get('word0_numeric') not in (1, 1.0):
            codes.append('example:canonical')
        if name == 'negative' and got.get('word0_unit') not in (None,):
            codes.append('watts')
        if got.get('word1_label') not in (None,):
            codes.append('word1-label')
        if got.get('status_label') not in (None,):
            codes.append('status-label')
    for name in by_name:
        if name not in seen:
            codes.append('example-missing:%s' % name)
    return codes


def contract_problems(page, fixture):
    problems = []
    try:
        policy = page_policy(page)
    except (TypeError, json.JSONDecodeError, AttributeError):
        return ['policy-unreadable']
    problems.extend(authorization_codes(policy))
    if policy != fixture.get('policy'):
        problems.append('policy-split')
    if policy != POLICY:
        problems.append('policy')
    for sentence in SENTENCES:
        if sentence not in page:
            problems.append('sentence')
            break
    problems.extend(prose_codes(page))
    if parse_extent_table(page) != list(EXTENT_ROWS):
        problems.append('table:extents')
    if parse_float_table(page) != list(FLOAT_ROWS):
        problems.append('table:floats')
    problems.extend(grid_codes(fixture.get('grid', [])))
    problems.extend(example_codes(fixture.get('examples', [])))
    return problems


class TwoWordViews(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text()
        cls.package = json.loads(FIXTURE.read_text())

    def test_policy_tables_links_and_grades(self):
        self.assertEqual(contract_problems(self.page, self.package), [])
        self.assertEqual(self.package['policy'], POLICY)
        self.assertEqual(page_policy(self.page), POLICY)
        self.assertFalse(POLICY['declared_count_alone'])
        self.assertFalse(POLICY['available_length_alone'])
        self.assertFalse(POLICY['accept_eight_byte_two_words'])
        self.assertFalse(POLICY['read_past_actual'])
        self.assertFalse(POLICY['asserts_watts'])
        self.assertFalse(POLICY['unsigned_power_conversion'])
        self.assertTrue(POLICY['retain_nonfinite_raw'])
        self.assertIsNone(POLICY['status_label'])
        self.assertIsNone(POLICY['word1_label'])
        self.assertIsNone(POLICY['word0_unit'])
        self.assertEqual(POLICY['two_word_minimum'], 9)
        self.assertEqual(parse_extent_table(self.page), list(EXTENT_ROWS))
        self.assertEqual(parse_float_table(self.page), list(FLOAT_ROWS))
        for sentence in SENTENCES:
            self.assertIn(sentence, self.page)
        for code, phrase in FORBIDDEN:
            self.assertNotIn(phrase, self.page, code)
        for link in re.findall(r'\]\(([^)]+)\)', self.page):
            path, _, anchor = link.partition('#')
            target = resolve_link(path)
            self.assertTrue(target.is_file(), link)
            if anchor:
                headings = re.findall(r'^#+ (.+)$', target.read_text(), re.M)
                self.assertIn(anchor, [slug(heading) for heading in headings], link)
        self.assertEqual(self.package['identity_axes'], AXES)
        self.assertEqual(len(self.package['grid']), 121)
        for row in EXTENT_ROWS:
            extent = independent_extent(row[1], row[2])
            self.assertEqual(
                (row[3], row[4], row[5], row[6]),
                (extent['status'], extent['word0'], extent['word1'], extent['complete']))
        for name, raw, finite, numeric in FLOAT_ROWS:
            decoded = manual_f32(bytes.fromhex(raw))
            unpacked = struct.unpack('<f', bytes.fromhex(raw))[0]
            if finite:
                self.assertEqual(decoded, unpacked)
                if numeric == '-0':
                    self.assertEqual(math.copysign(1.0, decoded), -1.0)
                elif numeric == '-1':
                    self.assertEqual(decoded, -1.0)
                else:
                    self.assertEqual(decoded, float(numeric))
                unsigned = int.from_bytes(bytes.fromhex(raw), 'little')
                if decoded != 0:
                    self.assertNotEqual(decoded, unsigned)
            else:
                self.assertIsNone(decoded)
                self.assertFalse(math.isfinite(unpacked))

    def test_canonical_declared9(self):
        result = view(context(), bytearray(PATTERN[:9]))
        self.assertEqual(result['state'], 'candidate')
        self.assertIsNone(result['reason'])
        self.assertEqual(result['software_contract'], 'Proven')
        self.assertEqual(result['interpretation_grade'], 'Hypothesis')
        self.assertEqual(result['native_grade'], 'Unknown')
        self.assertEqual(result['status']['raw'], 0)
        self.assertIsNone(result['status']['label'])
        self.assertIsNone(result['status']['converter'])
        self.assertEqual(result['status']['semantic_grade'], 'Unknown')
        self.assertEqual(result['word0']['raw'], bytearray.fromhex('0000803f'))
        self.assertEqual(result['word0']['numeric'], 1.0)
        self.assertEqual(result['word0']['numeric'], manual_f32(bytes.fromhex('0000803f')))
        self.assertNotEqual(result['word0']['numeric'], int.from_bytes(result['word0']['raw'], 'little'))
        self.assertTrue(result['word0']['finite_numeric'])
        self.assertEqual(result['word0']['quantity'], 'candidate_power')
        self.assertIsNone(result['word0']['unit'])
        self.assertIsNone(result['word0']['unsigned_bits'])
        self.assertEqual(result['word0']['numeric_grade'], 'Hypothesis')
        self.assertEqual(result['word0']['semantic_grade'], 'Hypothesis')
        self.assertEqual(result['word0']['native_grade'], 'Unknown')
        self.assertEqual(result['word1']['raw'], [1, 2, 3, 4])
        self.assertIsNone(result['word1']['label'])
        self.assertIsNone(result['word1']['numeric'])
        self.assertIsNone(result['word1']['converter'])
        self.assertEqual(result['word1']['type'], 'Unknown')
        self.assertEqual(result['word1']['scale'], 'Unknown')
        self.assertEqual(result['word1']['sign'], 'Unknown')
        self.assertTrue(result['status_available'])
        self.assertTrue(result['word0_available'])
        self.assertTrue(result['word1_available'])
        self.assertTrue(result['finite_numeric'])
        self.assertTrue(result['complete_two_word'])
        self.assertFalse(result['complete_message'])
        self.assertFalse(result['successful_response'])
        self.assertEqual(result['presence'], 'Unknown')
        self.assertEqual(result['native_units'], 'Unknown')
        self.assertEqual(result['trailing'], bytearray())
        self.assertEqual(result['raw'], bytearray(PATTERN[:9]))
        self.assertNotIn('watts', result['word0'].values())

    def test_extent_grid_zero_through_ten(self):
        self.assertEqual(len(self.package['grid']), 121)
        for declared in range(11):
            for available in range(11):
                with self.subTest(declared=declared, available=available):
                    result = view(context(declared_count=declared), bytearray(PATTERN[:available]))
                    extent = independent_extent(declared, available)
                    self.assertEqual(result['status_available'], declared >= 1 and available >= 1)
                    self.assertEqual(result['word0_available'], declared >= 5 and available >= 5)
                    self.assertEqual(result['word1_available'], declared >= 9 and available >= 9)
                    self.assertEqual(result['complete_two_word'], declared >= 9 and available >= 9)
                    self.assertEqual(result['status_available'], extent['status'])
                    self.assertEqual(result['word0_available'], extent['word0'])
                    self.assertEqual(result['word1_available'], extent['word1'])
                    self.assertEqual(result['complete_two_word'], extent['complete'])
                    self.assertEqual(result['available_length'], available)
                    self.assertEqual(result['declared_count'], declared)
                    self.assertEqual(result['raw'], bytearray(PATTERN[:available]))
                    self.assertEqual(result['trailing'], bytearray(PATTERN[9:available]))
                    self.assertLessEqual(len(result['raw']), available)
                    if result['word0_available']:
                        self.assertEqual(result['word0']['raw'], bytearray(PATTERN[1:5]))
                        self.assertEqual(result['word0']['numeric'], 1.0)
                        self.assertTrue(result['finite_numeric'])
                    else:
                        self.assertIsNone(result['word0']['raw'])
                        self.assertIsNone(result['word0']['numeric'])
                        self.assertFalse(result['finite_numeric'])
                    if result['word1_available']:
                        self.assertEqual(result['word1']['raw'], list(PATTERN[5:9]))
                    else:
                        self.assertIsNone(result['word1']['raw'])
                    if result['status_available']:
                        self.assertEqual(result['status']['raw'], 0)
                    else:
                        self.assertIsNone(result['status']['raw'])
                    self.assertFalse(result['complete_message'])
                    self.assertFalse(result['successful_response'])
                    self.assertEqual(result['presence'], 'Unknown')
                    stored = self.package['grid'][declared * 11 + available]
                    self.assertEqual(stored['declared'], declared)
                    self.assertEqual(stored['available'], available)
                    self.assertEqual(stored['complete_two_word'], declared >= 9 and available >= 9)

    def test_named_extent_counters_keep_partial_word0(self):
        short = view(context(declared_count=9), bytearray(PATTERN[:8]))
        narrow = view(context(declared_count=8), bytearray(PATTERN[:9]))
        hidden = view(context(declared_count=4), bytearray(PATTERN[:9]))
        for result in (short, narrow):
            self.assertFalse(result['complete_two_word'])
            self.assertTrue(result['word0_available'])
            self.assertEqual(result['word0']['numeric'], 1.0)
            self.assertEqual(result['word0']['raw'], bytearray.fromhex('0000803f'))
            self.assertFalse(result['word1_available'])
            self.assertIsNone(result['word1']['raw'])
            self.assertTrue(result['status_available'])
        self.assertEqual(short['available_length'], 8)
        self.assertEqual(short['declared_count'], 9)
        self.assertEqual(narrow['available_length'], 9)
        self.assertEqual(narrow['declared_count'], 8)
        self.assertEqual(hidden['raw'], bytearray(PATTERN[:9]))
        self.assertTrue(hidden['status_available'])
        self.assertFalse(hidden['word0_available'])
        self.assertIsNone(hidden['word0']['numeric'])
        self.assertIsNone(hidden['word0']['raw'])
        self.assertFalse(hidden['complete_two_word'])
        self.assertIn(b'\x00\x00\x80\x3f', bytes(hidden['raw']))

    def test_finite_zero_negative_and_nonfinite_keep_raw_bits(self):
        for case in case_definitions():
            if case['name'] not in {
                'zero', 'negative', 'negative_zero', 'nan', 'payload_nan',
                'positive_infinity', 'negative_infinity', 'canonical',
            }:
                continue
            with self.subTest(case=case['name']):
                result = view(case['context'], bytearray.fromhex(case['raw_hex']))
                expect = expected_case(case)
                self.assertEqual(result['word0_available'], True)
                self.assertEqual(bytes(result['word0']['raw']).hex(), expect['word0_raw_hex'])
                self.assertEqual(result['word0']['finite_numeric'], expect['word0_finite'])
                self.assertEqual(result['finite_numeric'], expect['word0_finite'])
                self.assertIsNone(result['word0']['unit'])
                self.assertIsNone(result['word0']['unsigned_bits'])
                self.assertTrue(result['complete_two_word'])
                self.assertEqual(result['word1']['raw'], [1, 2, 3, 4])
                if expect['word0_finite']:
                    self.assertTrue(same_number(result['word0']['numeric'], expect['word0_numeric']))
                    if result['word0']['numeric'] != 0:
                        self.assertNotEqual(
                            result['word0']['numeric'],
                            int.from_bytes(result['word0']['raw'], 'little'))
                    self.assertEqual(result['word0']['numeric_grade'], 'Hypothesis')
                else:
                    self.assertIsNone(result['word0']['numeric'])
                    self.assertIsNone(result['word0']['numeric_grade'])
                    self.assertEqual(bytes(result['word0']['raw']), bytes.fromhex(expect['word0_raw_hex']))
        labelled = view(context(), bytearray.fromhex('2a0000803f01020304'))
        self.assertEqual(labelled['status']['raw'], 0x2A)
        self.assertIsNone(labelled['status']['label'])
        opaque = view(context(), bytearray.fromhex('000000803fffffffff'))
        self.assertEqual(opaque['word1']['raw'], [255, 255, 255, 255])
        self.assertIsNone(opaque['word1']['label'])
        self.assertIsNone(opaque['word1']['numeric'])
        self.assertIsNone(opaque['word1']['converter'])

    def test_tail_capacity_and_one_larger_count(self):
        tail = view(context(declared_count=10), bytearray(PATTERN))
        self.assertTrue(tail['complete_two_word'])
        self.assertEqual(tail['trailing'], bytearray(b'\xaa'))
        self.assertEqual(tail['word1']['raw'], [1, 2, 3, 4])
        self.assertNotEqual(list(tail['trailing']), tail['word1']['raw'])
        backing = bytearray(PATTERN)
        window = memoryview(backing)[:8]
        limited = view(context(declared_count=9), window)
        self.assertEqual(limited['available_length'], 8)
        self.assertNotEqual(limited['available_length'], len(backing))
        self.assertFalse(limited['complete_two_word'])
        self.assertFalse(limited['word1_available'])
        self.assertTrue(limited['word0_available'])
        self.assertEqual(limited['word0']['numeric'], 1.0)
        wider = view(context(declared_count=8), bytearray(PATTERN))
        self.assertEqual(wider['available_length'], 10)
        self.assertFalse(wider['complete_two_word'])
        self.assertFalse(wider['word1_available'])
        self.assertEqual(wider['trailing'], bytearray(b'\xaa'))
        long_declared = view(context(declared_count=100), bytearray(PATTERN[:8]))
        self.assertEqual(long_declared['available_length'], 8)
        self.assertFalse(long_declared['word1_available'])
        self.assertFalse(long_declared['complete_two_word'])
        self.assertEqual(long_declared['raw'], bytearray(PATTERN[:8]))

    def test_rejected_identity_keeps_raw_and_hides_fields(self):
        body = bytearray(PATTERN[:9])
        operation = view(context(operation='OP08'), body)
        direction = view(context(direction='request'), body)
        absent = context()
        del absent['selection']
        missing = view(absent, body)
        negative = view(context(declared_count=-1), body)
        for result, reason, state in (
            (operation, 'operation', 'raw_only'),
            (direction, 'direction', 'raw_only'),
            (missing, 'selection', 'missing_selection'),
            (negative, 'declared_count', 'raw_only'),
        ):
            self.assertEqual(result['reason'], reason)
            self.assertEqual(result['state'], state)
            self.assertIsNone(result['interpretation_grade'])
            self.assertFalse(result['word0_available'])
            self.assertFalse(result['word1_available'])
            self.assertFalse(result['status_available'])
            self.assertFalse(result['complete_two_word'])
            self.assertIsNone(result['word0']['numeric'])
            self.assertEqual(result['raw'], body)
            self.assertEqual(result['software_contract'], 'Proven')
            self.assertEqual(result['native_grade'], 'Unknown')
        for bad in (True, 9.0, '9', None):
            result = view(context(declared_count=bad), body)
            self.assertEqual(result['reason'], 'declared_count')
            self.assertIsNone(result['word0']['numeric'])
            self.assertIsNone(result['declared_count'])
        for bad_body in (None, [0, 0, 0, 0x80, 0x3F], '000000803f', 9):
            with self.assertRaises(TypeError):
                view(context(), bad_body)
        for bad_ctx in (None, [], 'context', bytearray()):
            with self.assertRaises(TypeError):
                view(bad_ctx, body)

    def test_every_identity_field_changes_only_that_field(self):
        """Each field is the only difference from the canonical admitted key."""
        body = bytearray(PATTERN[:9])
        canonical = view(context(), body)
        self.assertEqual(canonical['word0']['numeric'], 1.0)
        mutations = (
            ('family', 'unknown-family', 'family'),
            ('variant', 'unknown-variant', 'variant'),
            ('operation', 'OP08', 'operation'),
            ('operation', 'OP10', 'operation'),
            ('operation', 'op14', 'operation'),
            ('direction', 'request', 'direction'),
            ('direction', 'negative', 'direction'),
            ('selection', None, 'selection'),
            ('declared_count', -1, 'declared_count'),
        )
        for field, bad, reason in mutations:
            with self.subTest(field=field, bad=bad):
                ctx = context()
                if bad is None:
                    del ctx[field]
                else:
                    ctx[field] = bad
                self.assertEqual(sum(ctx.get(key) != context().get(key) for key in CONTEXT_FIELDS), 1)
                result = view(ctx, body)
                self.assertEqual(result['reason'], reason)
                self.assertIsNone(result['word0']['numeric'])
                self.assertFalse(result['complete_two_word'])
                self.assertEqual(result['raw'], body)
                for other in ('family', 'variant', 'operation', 'direction'):
                    if other == field:
                        continue
                    self.assertEqual(result['context'].get(other), context()[other])
        declared4 = view(context(declared_count=4), body)
        self.assertTrue(declared4['status_available'])
        self.assertFalse(declared4['word0_available'])
        declared8 = view(context(declared_count=8), body)
        self.assertTrue(declared8['word0_available'])
        self.assertEqual(declared8['word0']['numeric'], 1.0)
        self.assertFalse(declared8['word1_available'])
        short = view(context(), bytearray(PATTERN[:4]))
        self.assertEqual(short['available_length'], 4)
        self.assertTrue(short['status_available'])
        self.assertFalse(short['word0_available'])
        self.assertIsNone(short['word0']['numeric'])
        eight = view(context(), bytearray(PATTERN[:8]))
        self.assertTrue(eight['word0_available'])
        self.assertFalse(eight['complete_two_word'])
        for field, good in (
            ('family', 'synthetic-power-family-b'),
            ('variant', 'synthetic-variant-b'),
        ):
            ctx = context()
            ctx[field] = good
            result = view(ctx, body)
            self.assertEqual(result['context'][field], good)
            self.assertEqual(result['word0']['numeric'], 1.0)
            self.assertTrue(result['complete_two_word'])
        for family in AXES['families']:
            for variant in AXES['variants']:
                for operation in AXES['operations']:
                    for direction in AXES['directions']:
                        for selection in AXES['selections']:
                            ctx = context(family=family, variant=variant, operation=operation,
                                          direction=direction)
                            if selection == 'missing':
                                del ctx['selection']
                            else:
                                ctx['selection'] = selection
                            result = view(ctx, body)
                            admitted = (
                                family in FAMILIES and variant in VARIANTS
                                and operation == 'OP14' and direction == 'positive'
                                and selection == 'preselected')
                            if admitted:
                                self.assertEqual(result['word0']['numeric'], 1.0)
                                self.assertTrue(result['complete_two_word'])
                            else:
                                self.assertIsNone(result['word0']['numeric'])
                                self.assertFalse(result['complete_two_word'])
                            self.assertEqual(result['raw'], body)

    def test_input_and_result_mutation_stay_detached(self):
        caller = context(note={'generation': 1})
        body = bytearray(PATTERN[:9])
        snapshot = copy.deepcopy(caller)
        result = view(caller, memoryview(body))
        body[1] = 0xFF
        caller['note']['generation'] = 2
        caller['declared_count'] = 4
        self.assertEqual(result['word0']['raw'], bytearray.fromhex('0000803f'))
        self.assertEqual(result['word0']['numeric'], 1.0)
        self.assertEqual(result['context'], snapshot)
        self.assertEqual(result['declared_count'], 9)
        result['raw'][0] = 0x11
        result['word0']['raw'][0] = 0x22
        result['word1']['raw'][0] = 9
        result['context']['note']['generation'] = 3
        self.assertEqual(body[0], 0x00)
        self.assertEqual(body[1], 0xFF)
        self.assertEqual(caller['note']['generation'], 2)
        self.assertEqual(caller['declared_count'], 4)
        promoted = context()
        promoted['native_units'] = 'watts'
        promoted['native_grade'] = 'Proven'
        held = view(promoted, bytearray(PATTERN[:9]))
        self.assertEqual(held['native_units'], 'Unknown')
        self.assertEqual(held['native_grade'], 'Unknown')
        self.assertIsNone(held['word0']['unit'])
        self.assertEqual(held['context']['native_units'], 'watts')
        self.assertEqual(held['presence'], 'Unknown')
        self.assertFalse(held['complete_message'])

    def test_examples_match_independent_expectations(self):
        self.assertEqual(example_codes(self.package['examples']), [])
        for example in self.package['examples']:
            with self.subTest(example=example['name']):
                ctx = copy.deepcopy(example['context'])
                result = view(ctx, bytearray.fromhex(example['raw_hex']))
                expect = example['expect']
                self.assertEqual(result['state'], expect['state'])
                self.assertEqual(result['reason'], expect['reason'])
                self.assertEqual(result['status_available'], expect['status_available'])
                self.assertEqual(result['status']['raw'], expect['status_raw'])
                self.assertEqual(result['status']['label'], expect['status_label'])
                self.assertEqual(result['word0_available'], expect['word0_available'])
                if expect['word0_raw_hex'] is None:
                    self.assertIsNone(result['word0']['raw'])
                else:
                    self.assertEqual(bytes(result['word0']['raw']).hex(), expect['word0_raw_hex'])
                self.assertTrue(same_number(result['word0']['numeric'], expect['word0_numeric']))
                self.assertEqual(result['word0']['finite_numeric'], expect['word0_finite'])
                self.assertIsNone(result['word0']['unit'])
                self.assertEqual(result['word1_available'], expect['word1_available'])
                self.assertEqual(result['word1']['raw'], expect['word1'])
                self.assertIsNone(result['word1']['label'])
                self.assertEqual(result['complete_two_word'], expect['complete_two_word'])
                self.assertEqual(result['finite_numeric'], expect['finite_numeric'])
                self.assertEqual(bytes(result['trailing']).hex(), expect['trailing_hex'])
                self.assertEqual(bytes(result['raw']).hex(), expect['raw_hex'])

    def test_executed_mutants_of_owned_copies(self):
        """Disposable copies only. Each authorizing edit must be rejected."""
        page = self.page
        fixture = json.loads(FIXTURE.read_text())
        self.assertEqual(contract_problems(page, fixture), [])

        def rejected(name, new_page, new_fixture, code):
            directory = tempfile.TemporaryDirectory(prefix='an18-mutant-', dir=Path.cwd() / '.tmp')
            try:
                path = Path(directory.name)
                (path / 'page.md').write_text(new_page)
                (path / 'fixture.json').write_text(json.dumps(new_fixture))
                found = contract_problems(
                    (path / 'page.md').read_text(),
                    json.loads((path / 'fixture.json').read_text()))
            finally:
                directory.cleanup()
            self.assertIn(code, found, name)
            return name

        killed = []
        declared_only = page.replace('"extent_rule": "both"', '"extent_rule": "declared_only"', 1)
        declared_only = declared_only.replace(
            '"declared_count_alone": false', '"declared_count_alone": true', 1)
        killed.append(rejected('declared-only', declared_only, fixture, 'declared-only'))
        available_only = page.replace('"extent_rule": "both"', '"extent_rule": "available_only"', 1)
        available_only = available_only.replace(
            '"available_length_alone": false', '"available_length_alone": true', 1)
        killed.append(rejected('available-only', available_only, fixture, 'available-only'))
        eight = page.replace('"two_word_minimum": 9', '"two_word_minimum": 8', 1)
        eight = eight.replace(
            '"accept_eight_byte_two_words": false',
            '"accept_eight_byte_two_words": true', 1)
        killed.append(rejected('eight-bytes', eight, fixture, 'eight-bytes'))
        past = page.replace('"read_past_actual": false', '"read_past_actual": true', 1)
        killed.append(rejected('read-past', past, fixture, 'read-past'))
        status = page.replace('"status_label": null', '"status_label": "ok"', 1)
        killed.append(rejected('status-label', status, fixture, 'status-label'))
        word1 = page.replace('"word1_label": null', '"word1_label": "secondary"', 1)
        killed.append(rejected('word1-label', word1, fixture, 'word1-label'))
        watts = page.replace('"word0_unit": null', '"word0_unit": "watts"', 1)
        watts = watts.replace('"asserts_watts": false', '"asserts_watts": true', 1)
        killed.append(rejected('watts', watts, fixture, 'watts'))
        dropped = page.replace('"retain_nonfinite_raw": true', '"retain_nonfinite_raw": false', 1)
        killed.append(rejected('nonfinite-raw', dropped, fixture, 'nonfinite-raw'))
        unsigned = page.replace(
            '"unsigned_power_conversion": false', '"unsigned_power_conversion": true', 1)
        killed.append(rejected('unsigned-power', unsigned, fixture, 'unsigned-power'))
        killed.append(rejected(
            'declared-only-prose',
            page + '\nDeclared count alone is sufficient.\n',
            fixture,
            'declared-only-prose'))
        killed.append(rejected(
            'eight-bytes-prose',
            page + '\nEight available bytes are two complete words.\n',
            fixture,
            'eight-bytes-prose'))
        killed.append(rejected(
            'watts-prose',
            page + '\nWord0 unit is watts.\n',
            fixture,
            'watts-prose'))
        killed.append(rejected(
            'nonfinite-prose',
            page + '\nNonfinite raw bits are dropped.\n',
            fixture,
            'nonfinite-prose'))

        def mutate_grid(declared, available, field, value):
            clone = json.loads(json.dumps(fixture))
            for row in clone['grid']:
                if row['declared'] == declared and row['available'] == available:
                    row[field] = value
            return clone

        killed.append(rejected(
            'grid-declared-only', page, mutate_grid(9, 8, 'complete_two_word', True),
            'grid:declared-only'))
        killed.append(rejected(
            'grid-available-only', page, mutate_grid(8, 9, 'complete_two_word', True),
            'grid:available-only'))
        killed.append(rejected(
            'grid-eight', page, mutate_grid(8, 8, 'complete_two_word', True),
            'grid:eight-bytes'))
        killed.append(rejected(
            'grid-declared4-word0', page, mutate_grid(4, 9, 'word0_available', True),
            'grid:declared4-word0'))
        killed.append(rejected(
            'grid-read-past', page, mutate_grid(9, 4, 'word0_available', True),
            'grid:read-past'))

        def mutate_example(name, change):
            clone = json.loads(json.dumps(fixture))
            for example in clone['examples']:
                if example['name'] == name:
                    change(example)
            return clone

        killed.append(rejected(
            'example-canonical-unsigned',
            page,
            mutate_example('canonical', lambda example: example['expect'].__setitem__(
                'word0_numeric', 1065353216)),
            'example:canonical'))
        killed.append(rejected(
            'example-nan-dropped',
            page,
            mutate_example('nan', lambda example: example['expect'].__setitem__(
                'word0_raw_hex', '')),
            'example:nan'))
        killed.append(rejected(
            'example-word1-label',
            page,
            mutate_example('canonical', lambda example: example['expect'].__setitem__(
                'word1_label', 'secondary')),
            'word1-label'))
        killed.append(rejected(
            'example-status-label',
            page,
            mutate_example('status_unlabelled', lambda example: example['expect'].__setitem__(
                'status_label', 'ok')),
            'status-label'))
        self.assertEqual(len(killed), 22)
        self.assertEqual(len(set(killed)), 22)


if __name__ == '__main__':
    unittest.main()
