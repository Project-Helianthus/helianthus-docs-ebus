"""Synthetic AN16 prose model and independent oracles. No production codec."""
import copy
from collections.abc import Mapping
import json
import os
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = Path(os.environ['AN16_PAGE']) if os.environ.get('AN16_PAGE') else (
    ROOT / 'architecture/an16_b516_clock_word_views.md')
FIXTURE = Path(os.environ['AN16_FIXTURE']) if os.environ.get('AN16_FIXTURE') else (
    ROOT / 'architecture/fixtures/an16_b516_clock_word_views.json')

EXPECTED_ORDER = ('minute', 'hour', 'day', 'month', 'year')
CLOCK_ORDER = ('minute', 'hour', 'day', 'month', 'year')
CONTEXT_FIELDS = ('family', 'variant', 'operation', 'direction')
FAMILIES = ('synthetic-display-family-a', 'synthetic-display-family-b')
VARIANTS = ('synthetic-variant-a', 'synthetic-variant-b')
MESSAGE_COUNT = 5
WORD_COUNT = 4
CANON_RAW = {
    'minute': bytes.fromhex('12'),
    'hour': bytes.fromhex('23'),
    'day': bytes.fromhex('31'),
    'month': bytes.fromhex('12'),
    'year': bytes.fromhex('99'),
}
CANON_NUMERIC = {'minute': 12, 'hour': 23, 'day': 31, 'month': 12, 'year': 99}
MESSAGE_RAW = (bytes.fromhex('10'), bytes.fromhex('21'), bytes.fromhex('32'),
               bytes.fromhex('43'), bytes.fromhex('54'))
WORD_RAW = (bytes.fromhex('0000'), bytes.fromhex('0100'), bytes.fromhex('0001'),
            bytes.fromhex('ffff'))
WORD_NUMERIC = (0, 1, 256, 65535)
# Contract switch: one failed clock cell stays local to that cell.
FAILED_CELL_DISCARDS_NEIGHBORS = False
POLICY = {
    'context_fields': ['family', 'variant', 'operation', 'direction'],
    'families': ['synthetic-display-family-a', 'synthetic-display-family-b'],
    'variants': ['synthetic-variant-a', 'synthetic-variant-b'],
    'operations': ['OP08', 'OP0D'],
    'direction': 'positive',
    'clock_order': ['minute', 'hour', 'day', 'month', 'year'],
    'seconds_component': False,
    'century': False,
    'timezone': False,
    'implicit_date_completion': False,
    'replacement_byte': 255,
    'replacement_before_packed_decimal': True,
    'both_nibbles_required': True,
    'numeric_min': 0,
    'numeric_max': 99,
    'clock_numeric_of_raw_12': 12,
    'plain_byte_value_of_raw_12': 18,
    'calendar_validator': False,
    'setpoint_divisor': 2,
    'setpoint_unit': 'Celsius',
    'missing_setpoint_is_zero': False,
    'message_count': 5,
    'word_count': 4,
    'word_codec': 'uint16le',
    'word_unit': None,
    'word_scale': 1,
    'word_sentinel': False,
    'word_positions': 'Unknown',
    'failed_cell_discards_neighbors': False,
    'native_support': 'Unknown',
    'physical_adaptation': 'Unknown',
    'interpretation_grade': 'Hypothesis',
    'software_contract': 'Proven',
}
CLOCK_ROWS = [
    ('canonical', 'minute', '12', 'present_numeric', 12),
    ('canonical', 'hour', '23', 'present_numeric', 23),
    ('canonical', 'day', '31', 'present_numeric', 31),
    ('canonical', 'month', '12', 'present_numeric', 12),
    ('canonical', 'year', '99', 'present_numeric', 99),
    ('replacement', 'minute', 'FF', 'replacement', None),
    ('malformed_fa', 'minute', 'FA', 'malformed_decimal', None),
    ('malformed_low', 'minute', '1A', 'malformed_decimal', None),
    ('malformed_high', 'minute', 'A0', 'malformed_decimal', None),
    ('missing_month', 'month', 'missing', 'missing', None),
    ('failed_month', 'month', '3112', 'failed', None),
]
NEIGHBOR_ROWS = [
    ('missing_month', '12', '23', '31', 'missing', '99'),
    ('failed_month', '12', '23', '31', 'failed', '99'),
]
SETPOINT_ROWS = [
    ('present_half', '01', 'present_numeric', 0.5, 'Celsius'),
    ('present_zero', '00', 'present_numeric', 0.0, 'Celsius'),
    ('missing', 'missing', 'missing', None, 'none'),
]
MESSAGE_ROWS = [
    (0, '10', 'present_raw'),
    (1, '21', 'present_raw'),
    (2, '32', 'present_raw'),
    (3, '43', 'present_raw'),
    (4, '54', 'present_raw'),
]
WORD_ROWS = [
    (0, '00 00', 'present_numeric', 0, 'none', False),
    (1, '01 00', 'present_numeric', 1, 'none', False),
    (2, '00 01', 'present_numeric', 256, 'none', False),
    (3, 'FF FF', 'present_numeric', 65535, 'none', False),
]
OPERATION_ROWS = [
    ('OP08', 'OP08', 'admitted', 'withheld'),
    ('OP0D', 'OP0D', 'withheld', 'admitted'),
    ('OP10', 'none', 'withheld', 'withheld'),
]
AXES = {
    'families': ['synthetic-display-family-a', 'synthetic-display-family-b', 'unknown-family'],
    'variants': ['synthetic-variant-a', 'synthetic-variant-b', 'unknown-variant'],
    'operations': ['OP08', 'OP0D', 'OP10'],
    'directions': ['positive', 'request'],
}
SENTENCES = (
    'Clock order is minute, hour, day, month, year.',
    'There is no seconds component.',
    'Replacement is selected on raw FF before packed-decimal conversion.',
    'Both nibbles must be decimal digits.',
    'Numeric interpretation is 0..99.',
    'The unsigned byte value eighteen is the wrong clock result.',
    'FA and 1A are malformed decimal and retain raw.',
    'A0 is malformed decimal and retains raw.',
    'A failed cell does not discard its neighbors.',
    'Missing month keeps the other four cells.',
    'Missing setpoint is not zero.',
    'Setpoint 01 is 0.5 Celsius.',
    'Each message byte remains separately available.',
    'Words are raw unsigned little-endian 16-bit values.',
    'Identity conversion has no units, scaling or sentinel.',
    'FFFF is 65535 and is not a sentinel.',
    'Absolute word positions are Unknown.',
    'Wrong operation is a raw-only view.',
    'Native support and physical adaptation stay Unknown on every result',
    'A present clock numeric grade is Hypothesis.',
    'Clock calendar semantics stay Unknown.',
    'Native grade stays Unknown.',
    'Mode, special-function and message tables stay Unknown.',
    'eBUS MCP compatibility and GraphQL parity',
    'last-known-good',
    'Nothing here is stable before Helianthus 1.0.',
    'passive energy decoder',
    'ab15an15.view(context, fields)',
    'The helper adds no century, no timezone and no implicit date completion.',
    'statistics selectors, voltage variants and identity-bearing structures receive no changes from either branch.',
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


def is_buffer(value):
    return isinstance(value, (bytes, bytearray, memoryview))


def copy_buffer(value):
    if isinstance(value, memoryview):
        return bytearray(value.tobytes())
    return bytearray(bytes(value))


def copy_fields(fields):
    copied = {}
    for key, value in fields.items():
        if is_buffer(value):
            copied[key] = copy_buffer(value)
        elif isinstance(value, (list, tuple)):
            items = []
            for item in value:
                if is_buffer(item):
                    items.append(copy_buffer(item))
                else:
                    items.append(copy.deepcopy(item))
            copied[key] = items
        else:
            copied[key] = copy.deepcopy(value)
    return copied


def blank(index=None):
    field = {
        'state': 'missing',
        'raw': None,
        'numeric': None,
        'numeric_grade': None,
        'semantic_grade': None,
        'native_grade': 'Unknown',
    }
    if index is not None:
        field['index'] = index
    return field


def classify_clock_byte(raw_byte):
    """Reference packed-decimal cell. Replacement wins before nibble checks."""
    high, low = (raw_byte >> 4) & 0x0F, raw_byte & 0x0F
    if raw_byte == 0xFF:
        return 'replacement', None
    if high > 9 or low > 9:
        return 'malformed_decimal', None
    return 'present_numeric', (high * 10) + low


def independent_clock_byte(raw_byte):
    """Oracle using divmod, separate from classify_clock_byte."""
    tens, ones = divmod(raw_byte, 16)
    if raw_byte == 255:
        return 'replacement', None
    if tens > 9 or ones > 9:
        return 'malformed_decimal', None
    return 'present_numeric', (tens * 10) + ones


def independent_word(raw):
    return raw[0] | (raw[1] << 8)


def independent_setpoint(raw):
    return raw[0] * 0.5


def finish_clock(field, state, numeric):
    field['state'] = state
    field['numeric'] = numeric
    if state == 'present_numeric':
        field['numeric_grade'] = 'Hypothesis'
        field['semantic_grade'] = 'Unknown'
    elif state == 'replacement':
        field['semantic_grade'] = 'Hypothesis'
    return field


def interpret_clock_slot(value):
    field = blank()
    if value is None:
        return field
    if not is_buffer(value):
        field['state'] = 'failed'
        return field
    raw = copy_buffer(value)
    field['raw'] = raw
    if len(raw) != 1:
        field['state'] = 'failed'
        return field
    state, numeric = classify_clock_byte(raw[0])
    return finish_clock(field, state, numeric)


def retain_slot(value, kind):
    field = blank()
    if value is None:
        return field
    if not is_buffer(value):
        field['state'] = 'failed'
        return field
    raw = copy_buffer(value)
    field['raw'] = raw
    width = {'clock': 1, 'setpoint': 1, 'mode': 1, 'special_function': 1,
             'message': 1, 'word': 2}[kind]
    if len(raw) != width:
        field['state'] = 'failed'
        return field
    field['state'] = 'raw_only'
    return field


def interpret_setpoint(value):
    field = blank()
    field['unit'] = None
    if value is None:
        return field
    if not is_buffer(value):
        field['state'] = 'failed'
        return field
    raw = copy_buffer(value)
    field['raw'] = raw
    if len(raw) != 1:
        field['state'] = 'failed'
        return field
    field['state'] = 'present_numeric'
    field['numeric'] = raw[0] / 2
    field['unit'] = 'Celsius'
    field['numeric_grade'] = 'Hypothesis'
    field['semantic_grade'] = 'Hypothesis'
    return field


def interpret_raw_byte(value):
    field = blank()
    if value is None:
        field['semantic_grade'] = 'Unknown'
        return field
    if not is_buffer(value):
        field['state'] = 'failed'
        return field
    raw = copy_buffer(value)
    field['raw'] = raw
    if len(raw) != 1:
        field['state'] = 'failed'
        return field
    field['state'] = 'present_raw'
    field['semantic_grade'] = 'Unknown'
    return field


def slot_group(value, count, width):
    if value is None:
        return 'absent', [None] * count
    if isinstance(value, (list, tuple)) and not is_buffer(value) and len(value) == count:
        return 'delimited', list(value)
    return 'undelimited', [None] * count


def build_messages(value, interpret):
    mode, supplied = slot_group(value, MESSAGE_COUNT, 1)
    out = []
    for index in range(MESSAGE_COUNT):
        if mode == 'undelimited':
            item = blank(index)
            item['state'] = 'failed'
        elif not interpret:
            item = retain_slot(supplied[index], 'message')
            item['index'] = index
        else:
            item = interpret_raw_byte(supplied[index])
            item['index'] = index
        out.append(item)
    return out


def build_words(value, interpret):
    mode, supplied = slot_group(value, WORD_COUNT, 2)
    decoded = []
    states = []
    raws = []
    for index in range(WORD_COUNT):
        if mode == 'absent' or (mode == 'delimited' and supplied[index] is None):
            states.append('missing')
            raws.append(None)
            decoded.append(None)
            continue
        if mode == 'undelimited' or not is_buffer(supplied[index]):
            states.append('failed')
            raws.append(None)
            decoded.append(None)
            continue
        raw = copy_buffer(supplied[index])
        if len(raw) != 2 or not interpret:
            states.append('failed' if len(raw) != 2 else 'raw_only')
            raws.append(raw)
            decoded.append(None)
            continue
        states.append('present_numeric')
        raws.append(raw)
        own_numeric = int.from_bytes(raw, 'little')
        numeric = own_numeric
        decoded.append(numeric)
    out = []
    for index in range(WORD_COUNT):
        item = blank(index)
        item['state'] = states[index]
        item['raw'] = raws[index]
        item['unit'] = None
        item['sentinel'] = False
        item['position'] = 'Unknown'
        item['scale'] = None
        if states[index] == 'present_numeric':
            item['numeric'] = decoded[index]
            item['numeric_grade'] = 'Hypothesis'
            item['semantic_grade'] = 'Unknown'
            item['scale'] = 1
        out.append(item)
    return out


def admitted_branch(context):
    if any(key not in context for key in CONTEXT_FIELDS):
        return None
    if any(type(context[key]) is not str or context[key] == '' for key in CONTEXT_FIELDS):
        return None
    if context['family'] not in FAMILIES or context['variant'] not in VARIANTS:
        return None
    if context['direction'] != 'positive':
        return None
    if context['operation'] not in ('OP08', 'OP0D'):
        return None
    return context['operation']


def expected_branch(family, variant, operation, direction):
    if family not in FAMILIES or variant not in VARIANTS:
        return None
    if direction != 'positive' or operation not in ('OP08', 'OP0D'):
        return None
    return operation


def view(context, fields):
    """ab15an15.view(context, fields) reference model of the architecture page."""
    if not isinstance(context, Mapping) or not isinstance(fields, Mapping):
        raise TypeError('context and fields must be mappings')
    branch = admitted_branch(context)
    interpret_clock = branch == 'OP08'
    interpret_words = branch == 'OP0D'
    clock = {}
    for name in CLOCK_ORDER:
        if interpret_clock:
            clock[name] = interpret_clock_slot(fields.get(name))
        else:
            clock[name] = retain_slot(fields.get(name), 'clock')
    if FAILED_CELL_DISCARDS_NEIGHBORS and any(
            item['state'] == 'failed' for item in clock.values()):
        for item in clock.values():
            item['state'] = 'failed'
            item['numeric'] = None
            item['numeric_grade'] = None
            item['semantic_grade'] = None
    if interpret_clock:
        setpoint = interpret_setpoint(fields.get('setpoint'))
        mode = interpret_raw_byte(fields.get('mode'))
        special = interpret_raw_byte(fields.get('special_function'))
    else:
        setpoint = retain_slot(fields.get('setpoint'), 'setpoint')
        setpoint['unit'] = None
        mode = retain_slot(fields.get('mode'), 'mode')
        special = retain_slot(fields.get('special_function'), 'special_function')
    return {
        'context': copy.deepcopy(context),
        'fields_raw': copy_fields(fields),
        'state': 'candidate' if branch else 'raw_only',
        'operation_branch': branch,
        'interpretation_grade': 'Hypothesis' if branch else None,
        'software_contract': 'Proven',
        'native_support': 'Unknown',
        'physical_adaptation': 'Unknown',
        'clock_order': list(CLOCK_ORDER),
        'clock': clock,
        'setpoint': setpoint,
        'mode': mode,
        'special_function': special,
        'messages': build_messages(fields.get('messages'), interpret_clock),
        'words': build_words(fields.get('words'), interpret_words),
    }


def context(**patch):
    base = {
        'family': 'synthetic-display-family-a',
        'variant': 'synthetic-variant-a',
        'operation': 'OP08',
        'direction': 'positive',
    }
    base.update(patch)
    return base


def canon_fields(**patch):
    fields = {name: bytearray(raw) for name, raw in CANON_RAW.items()}
    fields['setpoint'] = bytearray(b'\x01')
    fields['mode'] = bytearray(b'\x02')
    fields['special_function'] = bytearray(b'\x03')
    fields['messages'] = [bytearray(raw) for raw in MESSAGE_RAW]
    fields['words'] = [bytearray(raw) for raw in WORD_RAW]
    fields.update(patch)
    return fields


def slug(heading):
    return re.sub(r'[^\w -]', '', heading.lower()).replace(' ', '-')


class ClockWordViews(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.page = PAGE.read_text()
        cls.package = json.loads(FIXTURE.read_text())

    def test_page_policy_tables_links_and_grades(self):
        self.assertEqual(self.package['policy'], POLICY)
        self.assertEqual(json.loads(re.search(r'```json\n(.*?)\n```', self.page, re.S)[1]), POLICY)
        self.assertEqual(self.package['policy']['clock_order'][0], 'minute')
        self.assertNotIn('second', self.package['policy']['clock_order'])
        self.assertNotIn('seconds', self.package['policy']['clock_order'])
        self.assertTrue(POLICY['replacement_before_packed_decimal'])
        self.assertTrue(POLICY['both_nibbles_required'])
        self.assertFalse(POLICY['word_sentinel'])
        self.assertIsNone(POLICY['word_unit'])
        self.assertFalse(POLICY['failed_cell_discards_neighbors'])
        self.assertNotEqual(POLICY['clock_numeric_of_raw_12'], POLICY['plain_byte_value_of_raw_12'])
        self.assertEqual(POLICY['plain_byte_value_of_raw_12'], 0x12)
        rows = re.findall(
            r'^\| (canonical|replacement|malformed_fa|malformed_low|malformed_high|'
            r'missing_month|failed_month) \| (minute|hour|day|month|year) \| '
            r'([0-9A-Fa-f]+|missing) \| ([a-z_]+) \| (none|\d+) \|$',
            self.page, re.M)
        parsed = []
        for case, cell, raw, state, numeric in rows:
            parsed.append((case, cell, raw, state, None if numeric == 'none' else int(numeric)))
        self.assertEqual(parsed, CLOCK_ROWS)
        neighbors = re.findall(
            r'^\| (missing_month|failed_month) \| ([0-9]+|missing|failed) \| '
            r'([0-9]+|missing|failed) \| ([0-9]+|missing|failed) \| '
            r'([0-9]+|missing|failed) \| ([0-9]+|missing|failed) \|$',
            self.page, re.M)
        self.assertEqual([tuple(row) for row in neighbors], NEIGHBOR_ROWS)
        setpoints = re.findall(
            r'^\| ([a-z_]+) \| ([0-9A-Fa-f]+|missing) \| ([a-z_]+) \| (none|0\.0|0\.5) \| ([A-Za-z]+) \|$',
            self.page, re.M)
        self.assertEqual([(c, raw, state, None if num == 'none' else float(num), unit)
                          for c, raw, state, num, unit in setpoints], SETPOINT_ROWS)
        messages = re.findall(r'^\| ([0-4]) \| ([0-9A-Fa-f]{2}) \| (present_raw) \|$', self.page, re.M)
        self.assertEqual([(int(i), raw, state) for i, raw, state in messages], MESSAGE_ROWS)
        words = re.findall(
            r'^\| ([0-3]) \| ([0-9A-Fa-f]{2} [0-9A-Fa-f]{2}) \| ([a-z_]+) \| (none|\d+) \| '
            r'([A-Za-z]+) \| (true|false) \|$',
            self.page, re.M)
        self.assertEqual([(int(i), raw, state, None if num == 'none' else int(num), unit, flag == 'true')
                          for i, raw, state, num, unit, flag in words], WORD_ROWS)
        operations = re.findall(
            r'^\| (OP[0-9A-F]+) \| (OP08|OP0D|none) \| (admitted|withheld) \| (admitted|withheld) \|$',
            self.page, re.M)
        self.assertEqual([tuple(row) for row in operations], OPERATION_ROWS)
        for raw, state, numeric in (
                (0x12, 'present_numeric', 12), (0x23, 'present_numeric', 23),
                (0x31, 'present_numeric', 31), (0x99, 'present_numeric', 99),
                (0xFF, 'replacement', None), (0xFA, 'malformed_decimal', None),
                (0x1A, 'malformed_decimal', None), (0xA0, 'malformed_decimal', None)):
            self.assertEqual(independent_clock_byte(raw), (state, numeric))
            self.assertEqual(classify_clock_byte(raw), (state, numeric))
        self.assertEqual(independent_word(bytes.fromhex('0000')), 0)
        self.assertEqual(independent_word(bytes.fromhex('0100')), 1)
        self.assertEqual(independent_word(bytes.fromhex('0001')), 256)
        self.assertEqual(independent_word(bytes.fromhex('ffff')), 65535)
        self.assertEqual(int.from_bytes(bytes.fromhex('0100'), 'big'), 256)
        self.assertEqual(independent_setpoint(b'\x01'), 0.5)
        for sentence in SENTENCES:
            self.assertIn(sentence, self.page)
        for link in re.findall(r'\]\(([^)]+)\)', self.page):
            path, _, anchor = link.partition('#')
            target = resolve_link(path)
            self.assertTrue(target.is_file(), link)
            if anchor:
                headings = re.findall(r'^#+ (.+)$', target.read_text(), re.M)
                self.assertIn(anchor, [slug(heading) for heading in headings], link)
        self.assertEqual(self.package['identity_axes'], AXES)
        self.assertEqual(self.package['clock_rows'], [
            {'case': case, 'cell': cell, 'raw': raw, 'state': state, 'numeric': numeric}
            for case, cell, raw, state, numeric in CLOCK_ROWS])
        self.assertEqual(self.package['neighbor_rows'], [
            {'case': case, 'minute': minute, 'hour': hour, 'day': day, 'month': month, 'year': year}
            for case, minute, hour, day, month, year in NEIGHBOR_ROWS])
        self.assertEqual(self.package['setpoint_rows'], [
            {'case': case, 'raw': raw, 'state': state, 'numeric': numeric, 'unit': unit}
            for case, raw, state, numeric, unit in SETPOINT_ROWS])
        self.assertEqual(self.package['message_rows'], [
            {'index': index, 'raw': raw, 'state': state} for index, raw, state in MESSAGE_ROWS])
        self.assertEqual(self.package['word_rows'], [
            {'index': index, 'raw': raw, 'state': state, 'numeric': numeric,
             'unit': unit, 'sentinel': sentinel}
            for index, raw, state, numeric, unit, sentinel in WORD_ROWS])
        self.assertEqual(self.package['operation_rows'], [
            {'operation': op, 'branch': branch, 'clock': clock, 'words': words}
            for op, branch, clock, words in OPERATION_ROWS])

    def test_canonical_examples_and_wrong_branch_retention(self):
        op08 = view(context(), canon_fields())
        self.assertEqual(list(op08['clock']), ['minute', 'hour', 'day', 'month', 'year'])
        self.assertEqual(op08['clock_order'], ['minute', 'hour', 'day', 'month', 'year'])
        self.assertNotIn('second', op08['clock'])
        self.assertEqual(op08['state'], 'candidate')
        self.assertEqual(op08['operation_branch'], 'OP08')
        self.assertEqual(op08['software_contract'], 'Proven')
        self.assertEqual(op08['interpretation_grade'], 'Hypothesis')
        self.assertEqual(op08['native_support'], 'Unknown')
        self.assertEqual(op08['physical_adaptation'], 'Unknown')
        for name in EXPECTED_ORDER:
            cell = op08['clock'][name]
            self.assertEqual(cell['numeric'], CANON_NUMERIC[name])
            self.assertNotEqual(cell['numeric'], CANON_RAW[name][0])
            self.assertEqual(cell['state'], 'present_numeric')
            self.assertEqual(cell['raw'], CANON_RAW[name])
            self.assertEqual(cell['numeric_grade'], 'Hypothesis')
            self.assertEqual(cell['semantic_grade'], 'Unknown')
            self.assertEqual(cell['native_grade'], 'Unknown')
        self.assertEqual(op08['clock']['minute']['numeric'], 12)
        self.assertEqual(CANON_RAW['minute'][0], 18)
        self.assertEqual(op08['setpoint']['numeric'], 0.5)
        self.assertEqual(op08['setpoint']['unit'], 'Celsius')
        self.assertEqual(op08['setpoint']['state'], 'present_numeric')
        self.assertIsNone(op08['mode']['numeric'])
        self.assertEqual(op08['mode']['state'], 'present_raw')
        self.assertEqual(op08['mode']['raw'], b'\x02')
        self.assertEqual(op08['mode']['semantic_grade'], 'Unknown')
        self.assertIsNone(op08['special_function']['numeric'])
        self.assertEqual(op08['special_function']['raw'], b'\x03')
        self.assertEqual([item['raw'] for item in op08['messages']], list(MESSAGE_RAW))
        self.assertEqual([item['index'] for item in op08['messages']], [0, 1, 2, 3, 4])
        self.assertTrue(all(item['numeric'] is None and item['state'] == 'present_raw'
                            for item in op08['messages']))
        for word, raw, numeric in zip(op08['words'], WORD_RAW, WORD_NUMERIC):
            self.assertEqual(word['state'], 'raw_only')
            self.assertIsNone(word['numeric'])
            self.assertEqual(word['raw'], raw)
            self.assertIsNone(word['unit'])
            self.assertFalse(word['sentinel'])
            self.assertNotEqual(word['state'], 'present_numeric')
            self.assertNotEqual(word.get('numeric'), numeric)
        op0d = view(context(operation='OP0D'), canon_fields())
        self.assertEqual(op0d['operation_branch'], 'OP0D')
        for name in EXPECTED_ORDER:
            self.assertEqual(op0d['clock'][name]['state'], 'raw_only')
            self.assertIsNone(op0d['clock'][name]['numeric'])
            self.assertEqual(op0d['clock'][name]['raw'], CANON_RAW[name])
        self.assertEqual(op0d['setpoint']['state'], 'raw_only')
        self.assertIsNone(op0d['setpoint']['numeric'])
        self.assertIsNone(op0d['setpoint']['unit'])
        self.assertNotEqual(op0d['setpoint']['numeric'], 0.5)
        for word, raw, numeric in zip(op0d['words'], WORD_RAW, WORD_NUMERIC):
            self.assertEqual(word['numeric'], numeric)
            self.assertEqual(word['numeric'], independent_word(raw))
            self.assertEqual(word['state'], 'present_numeric')
            self.assertIsNone(word['unit'])
            self.assertFalse(word['sentinel'])
            self.assertEqual(word['scale'], 1)
            self.assertEqual(word['position'], 'Unknown')
            self.assertEqual(word['semantic_grade'], 'Unknown')
            self.assertEqual(word['native_grade'], 'Unknown')
        self.assertEqual(op0d['words'][3]['numeric'], 65535)
        raw_only = view(context(operation='OP10'), canon_fields())
        self.assertEqual(raw_only['state'], 'raw_only')
        self.assertIsNone(raw_only['operation_branch'])
        self.assertIsNone(raw_only['interpretation_grade'])
        self.assertEqual(raw_only['clock']['minute']['state'], 'raw_only')
        self.assertIsNone(raw_only['clock']['minute']['numeric'])
        self.assertEqual(raw_only['clock']['minute']['raw'], b'\x12')
        self.assertIsNone(raw_only['words'][3]['numeric'])
        self.assertEqual(raw_only['words'][3]['state'], 'raw_only')
        self.assertFalse(raw_only['words'][3]['sentinel'])
        promoted = context()
        promoted['native_support'] = 'Proven'
        held = view(promoted, canon_fields())
        self.assertEqual(held['native_support'], 'Unknown')
        self.assertEqual(held['context']['native_support'], 'Proven')

    def test_every_clock_slot_state_and_neighbor_retention(self):
        probes = (
            (bytes.fromhex('00'), 'present_numeric', 0),
            (bytes.fromhex('09'), 'present_numeric', 9),
            (bytes.fromhex('10'), 'present_numeric', 10),
            (bytes.fromhex('99'), 'present_numeric', 99),
            (bytes.fromhex('12'), 'present_numeric', 12),
            (bytes.fromhex('FF'), 'replacement', None),
            (bytes.fromhex('FA'), 'malformed_decimal', None),
            (bytes.fromhex('1A'), 'malformed_decimal', None),
            (bytes.fromhex('A0'), 'malformed_decimal', None),
            (bytes.fromhex('0A'), 'malformed_decimal', None),
            (None, 'missing', None),
            (bytes.fromhex('3112'), 'failed', None),
            (b'', 'failed', None),
            (True, 'failed', None),
            (18, 'failed', None),
            ('12', 'failed', None),
        )
        for slot in EXPECTED_ORDER:
            for raw, state, numeric in probes:
                with self.subTest(slot=slot, state=state, raw=raw if not is_buffer(raw) else raw.hex()):
                    fields = canon_fields()
                    if raw is None:
                        fields[slot] = None
                    else:
                        fields[slot] = raw
                    result = view(context(), fields)
                    cell = result['clock'][slot]
                    self.assertEqual(cell['state'], state)
                    self.assertEqual(cell['numeric'], numeric)
                    if is_buffer(raw):
                        self.assertEqual(cell['raw'], raw)
                    else:
                        self.assertIsNone(cell['raw'])
                    if state == 'present_numeric' and raw is not None and is_buffer(raw) and len(raw) == 1:
                        self.assertEqual((state, numeric), independent_clock_byte(raw[0]))
                        self.assertNotEqual(numeric, raw[0]) if raw[0] > 9 else None
                    for other in EXPECTED_ORDER:
                        if other == slot:
                            continue
                        neighbor = result['clock'][other]
                        self.assertEqual(neighbor['state'], 'present_numeric')
                        self.assertEqual(neighbor['numeric'], CANON_NUMERIC[other])
                        self.assertEqual(neighbor['raw'], CANON_RAW[other])
                    self.assertEqual(result['setpoint']['numeric'], 0.5)
        self.assertFalse(FAILED_CELL_DISCARDS_NEIGHBORS)
        blocked = view(context(), {'cells': [bytearray(CANON_RAW[name]) for name in EXPECTED_ORDER]})
        for name in EXPECTED_ORDER:
            self.assertEqual(blocked['clock'][name]['state'], 'missing')
            self.assertIsNone(blocked['clock'][name]['numeric'])
        self.assertEqual(blocked['fields_raw']['cells'][0], CANON_RAW['minute'])

    def test_messages_setpoint_and_each_word_slice(self):
        for index in range(MESSAGE_COUNT):
            messages = [bytearray(raw) for raw in MESSAGE_RAW]
            messages[index] = None
            result = view(context(), canon_fields(messages=messages))
            self.assertEqual(result['messages'][index]['state'], 'missing')
            self.assertIsNone(result['messages'][index]['numeric'])
            for other in range(MESSAGE_COUNT):
                if other == index:
                    continue
                self.assertEqual(result['messages'][other]['state'], 'present_raw')
                self.assertEqual(result['messages'][other]['raw'], MESSAGE_RAW[other])
                self.assertEqual(result['messages'][other]['index'], other)
                self.assertIsNone(result['messages'][other]['numeric'])
            messages[index] = bytearray(b'\xfa')
            present = view(context(), canon_fields(messages=messages))
            self.assertEqual(present['messages'][index]['state'], 'present_raw')
            self.assertEqual(present['messages'][index]['raw'], b'\xfa')
            self.assertIsNone(present['messages'][index]['numeric'])
            messages[index] = bytearray(b'\x10\x11')
            failed = view(context(), canon_fields(messages=messages))
            self.assertEqual(failed['messages'][index]['state'], 'failed')
            self.assertEqual(failed['messages'][index]['raw'], b'\x10\x11')
            for other in range(MESSAGE_COUNT):
                if other != index:
                    self.assertEqual(failed['messages'][other]['raw'], MESSAGE_RAW[other])
        blob = view(context(), canon_fields(messages=b'\x10\x21\x32\x43\x54'))
        self.assertTrue(all(item['state'] == 'failed' and item['numeric'] is None
                            for item in blob['messages']))
        self.assertEqual(blob['fields_raw']['messages'], b'\x10\x21\x32\x43\x54')
        self.assertEqual(blob['clock']['minute']['numeric'], 12)
        missing_setpoint = view(context(), canon_fields(setpoint=None))
        self.assertEqual(missing_setpoint['setpoint']['state'], 'missing')
        self.assertIsNone(missing_setpoint['setpoint']['numeric'])
        self.assertIsNone(missing_setpoint['setpoint']['unit'])
        self.assertNotEqual(missing_setpoint['setpoint']['numeric'], 0)
        self.assertNotEqual(missing_setpoint['setpoint']['numeric'], 0.0)
        zero = view(context(), canon_fields(setpoint=bytearray(b'\x00')))
        self.assertEqual(zero['setpoint']['state'], 'present_numeric')
        self.assertEqual(zero['setpoint']['numeric'], 0.0)
        self.assertEqual(zero['setpoint']['numeric'], independent_setpoint(b'\x00'))
        high = view(context(), canon_fields(setpoint=bytearray(b'\xff')))
        self.assertEqual(high['setpoint']['numeric'], 127.5)
        self.assertEqual(high['setpoint']['state'], 'present_numeric')
        self.assertNotEqual(high['setpoint']['state'], 'replacement')
        absent = view(context(operation='OP0D'), {})
        self.assertTrue(all(word['state'] == 'missing' and word['numeric'] is None
                            for word in absent['words']))
        probes = (
            bytes.fromhex('0000'), bytes.fromhex('0100'), bytes.fromhex('0001'),
            bytes.fromhex('ffff'), bytes.fromhex('0201'), None,
            bytes.fromhex('ff'), bytes.fromhex('000000'), b'',
        )
        expected = {
            '0000': ('present_numeric', 0),
            '0100': ('present_numeric', 1),
            '0001': ('present_numeric', 256),
            'ffff': ('present_numeric', 65535),
            '0201': ('present_numeric', 258),
            'missing': ('missing', None),
            'ff': ('failed', None),
            '000000': ('failed', None),
            '': ('failed', None),
        }
        for index in range(WORD_COUNT):
            for raw in probes:
                key = 'missing' if raw is None else raw.hex()
                state, numeric = expected[key]
                words = [bytearray(item) for item in WORD_RAW]
                words[index] = raw
                result = view(context(operation='OP0D'), canon_fields(words=words))
                word = result['words'][index]
                self.assertEqual(word['state'], state)
                self.assertEqual(word['numeric'], numeric)
                self.assertIsNone(word['unit'])
                self.assertFalse(word['sentinel'])
                self.assertEqual(word['position'], 'Unknown')
                if state == 'present_numeric':
                    self.assertEqual(word['numeric'], independent_word(raw))
                    self.assertEqual(word['scale'], 1)
                    if raw[0] != raw[1]:
                        self.assertNotEqual(word['numeric'], int.from_bytes(raw, 'big'))
                for other in range(WORD_COUNT):
                    if other == index:
                        continue
                    self.assertEqual(result['words'][other]['numeric'], WORD_NUMERIC[other])
                    self.assertEqual(result['words'][other]['state'], 'present_numeric')
                self.assertEqual(result['clock']['hour']['state'], 'raw_only')
                self.assertIsNone(result['clock']['hour']['numeric'])
        packed = view(context(operation='OP0D'), canon_fields(
            words=bytearray(b'\x00\x00\x01\x00\x00\x01\xff\xff')))
        self.assertTrue(all(word['state'] == 'failed' and word['numeric'] is None
                            for word in packed['words']))
        self.assertEqual(packed['fields_raw']['words'], b'\x00\x00\x01\x00\x00\x01\xff\xff')
        one_missing = view(context(operation='OP0D'), canon_fields(
            words=[bytearray(b'\x00\x00'), None, bytearray(b'\x00\x01'), bytearray(b'\xff\xff')]))
        self.assertEqual(one_missing['words'][1]['state'], 'missing')
        self.assertIsNone(one_missing['words'][1]['numeric'])
        self.assertEqual([word['numeric'] for word in one_missing['words']], [0, None, 256, 65535])

    def test_every_identity_axis_changes_only_its_field(self):
        self.assertEqual(self.package['identity_axes'], AXES)
        for family in AXES['families']:
            for variant in AXES['variants']:
                for operation in AXES['operations']:
                    for direction in AXES['directions']:
                        with self.subTest(family=family, variant=variant,
                                          operation=operation, direction=direction):
                            ctx = context(family=family, variant=variant,
                                          operation=operation, direction=direction)
                            result = view(ctx, canon_fields())
                            branch = expected_branch(family, variant, operation, direction)
                            self.assertEqual(result['operation_branch'], branch)
                            self.assertEqual(result['context']['family'], family)
                            self.assertEqual(result['context']['variant'], variant)
                            self.assertEqual(result['context']['operation'], operation)
                            self.assertEqual(result['context']['direction'], direction)
                            if branch == 'OP08':
                                self.assertEqual(result['clock']['minute']['numeric'], 12)
                                self.assertEqual(result['setpoint']['numeric'], 0.5)
                                self.assertIsNone(result['words'][1]['numeric'])
                            elif branch == 'OP0D':
                                self.assertIsNone(result['clock']['minute']['numeric'])
                                self.assertEqual(result['clock']['minute']['state'], 'raw_only')
                                self.assertIsNone(result['setpoint']['numeric'])
                                self.assertEqual([word['numeric'] for word in result['words']],
                                                 list(WORD_NUMERIC))
                            else:
                                self.assertEqual(result['state'], 'raw_only')
                                self.assertIsNone(result['clock']['year']['numeric'])
                                self.assertIsNone(result['words'][2]['numeric'])
                                self.assertEqual(result['clock']['year']['raw'], CANON_RAW['year'])
                                self.assertEqual(result['words'][2]['raw'], WORD_RAW[2])
        base = context()
        for field, bad in (
                ('family', 'unknown-family'),
                ('variant', 'unknown-variant'),
                ('operation', 'OP00'),
                ('operation', 'B516'),
                ('operation', 'op08'),
                ('direction', 'request'),
                ('direction', 'negative'),
                ('direction', 'response'),
        ):
            changed = dict(base)
            changed[field] = bad
            self.assertEqual(sum(changed[key] != base[key] for key in CONTEXT_FIELDS), 1)
            result = view(changed, canon_fields())
            self.assertIsNone(result['operation_branch'])
            self.assertEqual(result['clock']['minute']['raw'], b'\x12')
            self.assertIsNone(result['clock']['minute']['numeric'])
        for field, good in (
                ('family', 'synthetic-display-family-b'),
                ('variant', 'synthetic-variant-b'),
                ('operation', 'OP0D'),
        ):
            changed = dict(base)
            changed[field] = good
            self.assertEqual(sum(changed[key] != base[key] for key in CONTEXT_FIELDS), 1)
            result = view(changed, canon_fields())
            self.assertEqual(result['operation_branch'], expected_branch(
                changed['family'], changed['variant'], changed['operation'], changed['direction']))
        for field in CONTEXT_FIELDS:
            for bad in (None, '', False, 8, [], {}):
                changed = dict(base)
                changed[field] = bad
                self.assertIsNone(view(changed, canon_fields())['operation_branch'])
            absent = dict(base)
            del absent[field]
            self.assertIsNone(view(absent, canon_fields())['operation_branch'])

    def test_detached_raw_memory_and_type_errors(self):
        for selected in ('OP08', 'OP0D'):
            caller = context(operation=selected, trace={'items': [1]})
            snapshot = copy.deepcopy(caller)
            minute = bytearray(b'\x12')
            word = bytearray(b'\x01\x00')
            backing = bytearray(b'\x23')
            fields = canon_fields(
                minute=minute,
                hour=memoryview(backing),
                words=[bytearray(b'\x00\x00'), word, bytearray(b'\x00\x01'), bytearray(b'\xff\xff')],
            )
            result = view(caller, fields)
            minute[0] = 0x99
            word[0] = 0xFF
            backing[0] = 0x00
            caller['trace']['items'][0] = 7
            fields['messages'][0][0] = 0x00
            self.assertEqual(result['clock']['minute']['raw'], b'\x12')
            self.assertEqual(result['clock']['hour']['raw'], b'\x23')
            self.assertEqual(result['words'][1]['raw'], b'\x01\x00')
            self.assertEqual(result['messages'][0]['raw'], MESSAGE_RAW[0])
            self.assertEqual(result['context'], snapshot)
            self.assertEqual(result['fields_raw']['minute'], b'\x12')
            self.assertIsNot(result['clock']['minute']['raw'], minute)
            self.assertIsNot(result['fields_raw']['minute'], minute)
            self.assertIsNot(result['words'][1]['raw'], word)
            result['clock']['minute']['raw'][0] = 0
            result['words'][1]['raw'][0] = 0
            result['context']['trace']['items'].append(9)
            self.assertEqual(minute[0], 0x99)
            self.assertEqual(word[0], 0xFF)
            self.assertEqual(caller['trace']['items'], [7])
            if selected == 'OP08':
                self.assertEqual(result['clock']['minute']['numeric'], 12)
                self.assertIsNone(result['words'][1]['numeric'])
            else:
                self.assertIsNone(result['clock']['minute']['numeric'])
                self.assertEqual(result['words'][1]['numeric'], 1)
        for fields in (None, [], b'\x12', 'fields'):
            with self.assertRaises(TypeError):
                view(context(), fields)
        for ctx in (None, [], 'context', bytearray()):
            with self.assertRaises(TypeError):
                view(ctx, {})


class NeighborProseGuard(unittest.TestCase):
    def test_no_prose_authorizes_neighbor_erasure(self):
        page = PAGE.read_text()
        self.assertNotIn('discards its neighbors', page)
        self.assertNotIn('discards neighbors', page)
        self.assertEqual(page.count('A failed cell does not discard its neighbors.'), 2)


if __name__ == '__main__':
    unittest.main()
