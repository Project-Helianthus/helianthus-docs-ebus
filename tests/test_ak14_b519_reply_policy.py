"""Independent finite documentation checks; no registry or wire execution."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / 'protocols/vaillant/ebus-b519-reply-policy.md'
FIXTURE = ROOT / 'protocols/vaillant/fixtures/ak14_b519_reply_policy.json'
API = ROOT / 'architecture/ak14_b519_reply_policy_api.md'

# Hand-authored expectations from the finite task, independent of published data.
POLICIES = [
    ('ak14-op03-target', 3, 'initiator-to-target', 'mode-dependent',
     'target-response', 'receiving-target-B', 'none', None),
    ('ak14-op03-initiator', 3, 'initiator-to-initiator', 'mode-dependent',
     'service-toward-A', 'sender-A', 'associated-initiator-C', None),
    ('ak14-op03-broadcast', 3, 'broadcast', 'mode-dependent',
     'retained-CRC-for-02', 'none', 'associated-initiator-C', 2),
    ('ak14-op01-initiator-ack', 1, 'initiator-to-initiator', 'ack-only',
     'ACK-only', 'Unknown', 'associated-initiator-C', None),
    ('ak14-op01-initiator-crc', 1, 'initiator-to-initiator', 'crc-positive',
     'CRC-positive', 'Unknown', 'associated-initiator-C', None),
    ('ak14-op01-broadcast-ack', 1, 'broadcast', 'ack-only',
     'ACK-only', 'Unknown', 'associated-initiator-C', None),
    ('ak14-op01-broadcast-crc', 1, 'broadcast', 'crc-positive',
     'CRC-positive', 'Unknown', 'associated-initiator-C', None),
]
AXES = [
    ('Ab21Family', 'string', 'family'),
    ('Ab21Variant', 'string', 'variant'),
    ('Ab21Primary', 'uint8', 'primary'),
    ('Ab21Secondary', '*uint8', 'secondary'),
    ('Ab21Operation', '*uint8', 'operation'),
    ('Ab21Direction', 'string', 'direction'),
    ('Ab21Field', 'string', 'field'),
    ('Ab21Alternative', 'string', 'alternative'),
    ('Ab21Group', '*uint8', 'group'),
    ('Ab21InstanceScope', 'string', 'instance_scope'),
    ('Ab21Register', '*uint16', 'register'),
]
PROBES = [
    ('Ab21Family', 'Vaillant', 'other-family', 'missing'),
    ('Ab21Variant', 'Unknown', 'other-variant', 'missing'),
    ('Ab21Primary', '181', '0', 'missing'),
    ('Ab21Secondary', '25', 'absent', 'missing'),
    ('Ab21Secondary', '25', '0', 'missing'),
    ('Ab21Operation', '3', 'absent', 'missing'),
    ('Ab21Operation', '3', '0', 'missing'),
    ('Ab21Direction', 'initiator-to-target', 'none', 'missing'),
    ('Ab21Field', 'reply-policy', 'none', 'missing'),
    ('Ab21Alternative', 'mode-dependent', 'none', 'missing'),
    ('Ab21Group', 'absent', '0', 'missing'),
    ('Ab21InstanceScope', 'none', '00', 'missing'),
    ('Ab21Register', 'absent', '0', 'missing'),
]
UNKNOWNS = {
    'native_support': 'Unknown', 'physical_effects': 'Unknown',
    'persistence': 'Unknown', 'delivery': 'Unknown', 'routing': 'Unknown',
    'actual_acknowledgement': 'Unknown', 'storage_effects': 'Unknown',
    'peer_capacity_bytes': 'Unknown', 'crc_algorithm': 'Unknown',
    'crc_coverage': 'Unknown',
}


def table(text, header):
    """Read one Markdown table, requiring its exact independent header."""
    lines = text.splitlines()
    start = lines.index('| ' + ' | '.join(header) + ' |')
    rows = []
    for line in lines[start + 2:]:
        if not line.startswith('| '):
            break
        rows.append(tuple(cell.strip() for cell in line.strip('|').split('|')))
    return rows


def expected_identity(operation, mode, alternative):
    return {
        'family': 'Vaillant', 'variant': 'Unknown', 'primary': 181,
        'secondary': 25, 'operation': operation, 'direction': mode,
        'field': 'reply-policy', 'alternative': alternative, 'group': None,
        'instance_scope': 'none', 'register': None,
    }


def expected_relation(policy, related, associated, later):
    return {
        'reply_policy': policy, 'related_participant': related,
        'associated_initiator': associated, 'later_query_operation': later,
    }


class Ak14ReplyPolicy(unittest.TestCase):
    def setUp(self):
        self.native = NATIVE.read_text()
        self.api = API.read_text()
        self.fixture = json.loads(FIXTURE.read_text())

    def test_native_policy_table(self):
        actual = table(self.native, [
            'Operation', 'Mode', 'Alternative', 'Reply policy',
            'Related participant', 'Associated initiator',
            'Later query operation', 'Grade', 'Qualification',
        ])
        expected = [
            (f'{op:02X}', mode, alt, policy, related, associated,
             'none' if later is None else f'{later:02X}', 'Hypothesis', 'Unknown')
            for _, op, mode, alt, policy, related, associated, later in POLICIES
        ]
        self.assertEqual(actual, expected)

    def test_native_data_table(self):
        self.assertEqual(table(self.native, [
            'Operation', 'Minimum data bytes', 'Maximum data bytes',
            'Block number in data', 'Grade',
        ]), [
            ('03', '0', 'Unknown', 'no', 'Hypothesis'),
            ('01', 'Unknown', 'Unknown', 'no', 'Hypothesis'),
        ])

    def test_native_boundaries(self):
        prose = ' '.join(self.native.split())
        for phrase in [
            'The family variant remains **Unknown**.',
            'Actual routing remains **Unknown**.',
            'numeric peer capacity is **Unknown**',
            'Data excludes the block number.',
            'Neither alternative establishes a completed physical outcome.',
            'ACK-only is a response-policy candidate',
            'CRC-positive remains available as a separate alternative',
            'Native support, physical effects, persistence, delivery, routing, actual acknowledgement and storage effects',
            'independent partial last-known-good information',
            '**Proven (synthetic representation only):**',
            'not telegrams or wire captures',
            'Its separate coordinate and encoding are **Unknown**',
            '[field and CRC catalog](ebus-vaillant-B519.md)',
            '[Synthetic cases](fixtures/ak14_b519_reply_policy.json)',
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, prose)
        self.assertNotRegex(self.native, r'Ab21|GraphQL|\bMCP\b|\bGo\b')

    def test_fixture_envelope_and_unique_identities(self):
        self.assertEqual(set(self.fixture), {
            'provenance', 'representation_grade', 'rows', 'cases',
        })
        self.assertEqual(self.fixture['provenance'],
                         'synthetic declarations only; not wire observations')
        self.assertEqual(self.fixture['representation_grade'], 'Proven')
        rows = self.fixture['rows']
        self.assertEqual(len(rows), 7)
        self.assertEqual([row['id'] for row in rows], [p[0] for p in POLICIES])
        identities = [json.dumps(row['identity'], sort_keys=True) for row in rows]
        self.assertEqual(len(set(identities)), 7)

    def test_all_row_fields_against_independent_expectations(self):
        self.assertEqual(len(self.fixture['rows']), len(POLICIES))
        for actual, spec in zip(self.fixture['rows'], POLICIES):
            ident, op, mode, alt, policy, related, associated, later = spec
            with self.subTest(row=ident):
                self.assertEqual(actual, {
                    'id': ident,
                    'identity': expected_identity(op, mode, alt),
                    'relations': expected_relation(policy, related, associated, later),
                    'data_length': {
                        'minimum_bytes': 0 if op == 3 else 'Unknown',
                        'maximum_bytes': 'Unknown', 'block_number_in_data': False,
                    },
                    'grade': 'Hypothesis', 'qualification': 'Unknown',
                    'unknowns': UNKNOWNS,
                    'raw_form': {
                        'service_prefix': [181, 25, op], 'data_encoding': 'opaque',
                        'block_position': 'Unknown', 'crc_bytes': 'Unknown',
                    },
                })

    def test_synthetic_cases_against_independent_expectations(self):
        expected = []
        for ident, op, _, _, policy, related, associated, later in POLICIES:
            for data in ([[], [0, 255, 65]] if op == 3 else [[0, 255, 65]]):
                expected.append({
                    'id': ident + ('-empty' if not data else '-three'),
                    'row_id': ident,
                    'participants': {
                        'initial_sender': 'sender-A',
                        'receiving_target': 'receiving-target-B',
                        'associated_initiator': 'associated-initiator-C',
                    },
                    'raw': {
                        'service_prefix': [181, 25, op], 'data': data,
                        'block_token': 'fabricated-block-token',
                    },
                    'expected_relation': expected_relation(policy, related, associated, later),
                    'peer_capacity_bytes': 'Unknown', 'grade': 'Hypothesis',
                    'qualification': 'Unknown', 'physical_outcome': 'Unknown',
                })
        self.assertEqual(len(self.fixture['cases']), 10)
        self.assertEqual(self.fixture['cases'], expected)

    def test_mode_is_the_only_op03_input_change(self):
        cases = {case['id']: case for case in self.fixture['cases']}
        for suffix in ['empty', 'three']:
            controls = [cases[f'ak14-op03-{mode}-{suffix}']
                        for mode in ['target', 'initiator', 'broadcast']]
            for case in controls:
                self.assertEqual(case['raw'], controls[0]['raw'])
                self.assertEqual(case['participants'], controls[0]['participants'])
                self.assertEqual(case['peer_capacity_bytes'], 'Unknown')
            self.assertEqual([case['expected_relation']['reply_policy'] for case in controls],
                             ['target-response', 'service-toward-A', 'retained-CRC-for-02'])
            self.assertEqual(controls[1]['expected_relation']['related_participant'], 'sender-A')
            self.assertEqual([case['expected_relation']['associated_initiator']
                              for case in controls[1:]],
                             ['associated-initiator-C', 'associated-initiator-C'])

    def test_exact_api_and_all_key_types(self):
        self.assertEqual([line for line in self.api.splitlines() if line.startswith('func ')], [
            'func Ab21Entries() (json.RawMessage, error)',
            'func Ab21Lookup(Ab21Key) (json.RawMessage, bool, error)',
        ])
        self.assertEqual(table(self.api, ['Field', 'Type', 'Native identity member']), AXES)
        self.assertIn('Package `vaillant`', self.api)
        self.assertIn('**Proven (local API contract):**', self.api)

    def test_exact_key_probes_have_valid_controls(self):
        self.assertEqual(table(self.api, ['Axis', 'Control', 'Probe', 'Result']), PROBES)
        rows = self.fixture['rows']
        control = expected_identity(3, 'initiator-to-target', 'mode-dependent')
        numeric = {'primary', 'secondary', 'operation', 'group', 'register'}
        member_for = {axis: member for axis, _, member in AXES}
        seen = set()
        for axis, before, after, _ in PROBES:
            with self.subTest(axis=axis, probe=after):
                # This checks finite declarations, not a replacement Ab21Lookup.
                hits = [row for row in rows if row['identity'] == control]
                self.assertEqual(len(hits), 1)
                self.assertEqual(hits[0]['id'], 'ak14-op03-target')
                member = member_for[axis]
                value = lambda text: (None if text == 'absent' else
                                      int(text) if member in numeric else text)
                self.assertEqual(control[member], value(before))
                probe = dict(control, **{member: value(after)})
                self.assertEqual([key for key in control if probe[key] != control[key]], [member])
                self.assertEqual([row for row in rows if row['identity'] == probe], [])
                seen.add(axis)
        self.assertEqual(seen, {axis for axis, _, _ in AXES})
        for row in rows:
            self.assertEqual([other for other in rows if other['identity'] == row['identity']], [row])

    def test_absent_zero_and_explicit_string_axes(self):
        for member in ['secondary', 'operation', 'group', 'register']:
            values = [after for axis, _, after, _ in PROBES
                      if dict((a, m) for a, _, m in AXES)[axis] == member]
            self.assertIn('0', values)
            if member in ['secondary', 'operation']:
                self.assertIn('absent', values)
        for row in self.fixture['rows']:
            for axis, kind, member in AXES:
                with self.subTest(row=row['id'], axis=axis):
                    value = row['identity'][member]
                    if kind == 'string':
                        self.assertIs(type(value), str)
                        self.assertTrue(value)
                    elif value is not None:
                        self.assertIs(type(value), int)
                        self.assertGreaterEqual(value, 0)
                        self.assertLessEqual(value, 65535 if kind == '*uint16' else 255)
                    else:
                        self.assertTrue(kind.startswith('*'))
            self.assertEqual(row['identity']['instance_scope'], 'none')

    def test_api_copy_error_and_admission_contract(self):
        prose = ' '.join(self.api.split())
        for phrase in [
            'All eleven axes match exactly.',
            'No wildcard or nearest-key lookup is permitted',
            'no cross-family, variant, direction, field or alternative fallback',
            'Optional absent and explicit zero differ',
            'non-applicable string axes use the explicit `none` token',
            'Variant `Unknown` is a literal unresolved identity value, not a wildcard',
            'Ab21Entries returns a JSON array',
            'Ab21Lookup returns exactly one whole row',
            'A missing exact key returns `nil, false, nil`',
            'Invalid embedded JSON or duplicate keys',
            'Ab21Entries to return `nil, error`',
            'Ab21Lookup to return `nil, false, error`',
            'neither exposes a partial valid prefix',
            'including pointer presence and value',
            'Admission fails closed',
            'embeds its owned JSON in its owned Go file',
            'independent deep byte copies on every call',
            'A mutation to any returned row or entries buffer cannot affect a later result, across either API',
            'Caller-owned key pointers are read by value',
            'Raw fallback remains available',
            'partial last-known-good state or raw evidence',
            'Hypothesis and Unknown metadata intact',
            'Each production row has a ticket-prefixed ID, the complete identity',
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, prose)

    def test_api_native_unknowns_and_companion_order(self):
        prose = ' '.join(self.api.split())
        for phrase in [
            '../protocols/vaillant/ebus-b519-reply-policy.md',
            'AK13 is the registry companion and merges before AK14',
            'The registry has no dependency back to this page',
            'Merge order does not establish native qualification',
            'not execution evidence from this documentation repository',
            'documentation checks do not execute a registry implementation',
            'Routing, actual acknowledgement and storage effects remain Unknown',
            'qualification, native support, physical effects, persistence and delivery remain **Unknown**',
            'Zero-length and three-byte data keep Unknown numeric peer capacity',
            'The block token remains outside data',
            'Existing catalog/provider APIs and routability remain unchanged',
            'eBUS MCP compatibility and GraphQL parity',
            'Nothing is stable before Helianthus 1.0',
            'Candidate metadata alone cannot admit execution or automatically qualify native support',
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, prose)


if __name__ == '__main__':
    unittest.main()
