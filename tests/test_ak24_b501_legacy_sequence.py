"""Finite synthetic declarations; no registry runtime or wire qualification."""
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / 'protocols/vaillant/ebus-b501-legacy-sequence.md'
DATA = ROOT / 'protocols/vaillant/fixtures/ak24_b501_legacy_sequence.json'
API = ROOT / 'architecture/ak24-b501-legacy-sequence-api.md'
IDENTITY = {
    'family': 'legacy-interface', 'variant': 'computer-interface',
    'primary': 181, 'secondary': 1, 'operation': None,
    'direction': 'initiator-to-initiator', 'field': 'sequencing',
    'alternative': 'none', 'group': None, 'instance_scope': 'none',
    'register': None,
}
UNKNOWNS = (
    'exact_synchronization_bytes', 'state_order_beyond_wait', 'timeout_duration',
    'segmentation', 'retries', 'return_codec', 'transport_adaptation',
    'native_support', 'physical_effects', 'persistence', 'delivery',
)
CASES = [
    ('timeout-below', 'legacy-interface', 'timeout', 3499, 'below-minimum', 'Hypothesis'),
    ('timeout-at', 'legacy-interface', 'timeout', 3500, 'minimum-met', 'Hypothesis'),
    ('timeout-above', 'legacy-interface', 'timeout', 3501, 'minimum-met', 'Hypothesis'),
    ('successful-return', 'legacy-interface', 'successful-return', 3499,
     'not-applicable', 'Hypothesis'),
    ('no-timeout', 'legacy-interface', 'none', 3500, 'not-applicable', 'Hypothesis'),
    ('missing-elapsed', 'legacy-interface', 'timeout', None, 'elapsed-unknown', 'Unknown'),
    ('modern-timeout', 'modern-controller', 'timeout', 3500, 'no-family-entry', 'Unknown'),
]
AXES = [
    ('Ab34Family', 'string', 'family', 'legacy-interface'),
    ('Ab34Variant', 'string', 'variant', 'computer-interface'),
    ('Ab34Primary', 'uint8', 'primary', '181'),
    ('Ab34Secondary', '*uint8', 'secondary', '1'),
    ('Ab34Operation', '*uint8', 'operation', 'null'),
    ('Ab34Direction', 'string', 'direction', 'initiator-to-initiator'),
    ('Ab34Field', 'string', 'field', 'sequencing'),
    ('Ab34Alternative', 'string', 'alternative', 'none'),
    ('Ab34Group', '*uint8', 'group', 'null'),
    ('Ab34InstanceScope', 'string', 'instance_scope', 'none'),
    ('Ab34Register', '*uint16', 'register', 'null'),
]
CONTROLS = [
    ('family', 'legacy-interface', 'modern-controller', 'ignore family'),
    ('variant', 'computer-interface', 'other-variant', 'ignore variant'),
    ('primary', '181', '182', 'ignore primary'),
    ('secondary', '1', '2', 'ignore secondary'),
    ('operation', 'null', '1', 'ignore operation'),
    ('direction', 'initiator-to-initiator', 'reverse', 'ignore direction'),
    ('field', 'sequencing', 'other-field', 'ignore field'),
    ('alternative', 'none', 'other-alternative', 'ignore alternative'),
    ('group', 'null', '1', 'ignore group'),
    ('instance_scope', 'none', 'dynamic', 'ignore instance_scope'),
    ('register', 'null', '1', 'ignore register'),
    ('secondary', 'null', '0', 'collapse absent and zero secondary'),
    ('operation', 'null', '0', 'collapse absent and zero operation'),
    ('group', 'null', '0', 'collapse absent and zero group'),
    ('register', 'null', '0', 'collapse absent and zero register'),
]


def table(text, first_header):
    """Parse one finite Markdown table without deriving expected results."""
    found = []
    current = []
    for line in text.splitlines() + ['']:
        if line.startswith('|'):
            current.append(tuple(cell.strip() for cell in line.strip('|').split('|')))
        elif current:
            if current[0][0] == first_header:
                found.append(current[2:])
            current = []
    if len(found) != 1:
        raise AssertionError('expected exactly one table: ' + first_header)
    return found[0]


def synthetic_cooldown(row, family, event, elapsed):
    """Evaluate the fixture's finite relation, never a clock or admission rule."""
    if family != row['family']:
        return 'no-family-entry'
    if event != row['cooldown']['trigger']:
        return 'not-applicable'
    if elapsed is None:
        return 'elapsed-unknown'
    return ('minimum-met' if elapsed >= row['cooldown']['minimum_ms']
            else 'below-minimum')


def scalar(text):
    return json.loads(text) if text == 'null' or text.isdecimal() else text


class LegacySequenceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text())
        cls.native = NATIVE.read_text()
        cls.api = API.read_text()
        cls.flat_native = ' '.join(cls.native.split())
        cls.flat_api = ' '.join(cls.api.split())

    def test_complete_finite_native_declaration(self):
        self.assertEqual(set(self.data), {'grade', 'qualification', 'rows',
                                         'timing_cases', 'raw_cases'})
        self.assertEqual(self.data['grade'], 'Hypothesis')
        self.assertEqual(self.data['qualification'], 'Unknown')
        expected = dict(
            IDENTITY, id='ak24-legacy-sequence-none', grade='Hypothesis',
            qualification='Unknown', raw_form='retain-original-bytes',
            unknown={name: 'Unknown' for name in UNKNOWNS},
            synchronization_required=True,
            cooldown={'trigger': 'timeout', 'minimum_ms': 3500},
            service_roles=[
                {'role': 'request', 'service': 'B501', 'body': 'opaque-request'},
                {'role': 'positive-status', 'service': 'B501', 'body': 'status-form'},
                {'role': 'return-data', 'service': 'B502', 'body': 'opaque-return-data'},
            ])
        self.assertEqual(self.data['rows'], [expected])
        # bool is an int subclass: require the intended JSON scalar types too.
        row = self.data['rows'][0]
        for axis in ('primary', 'secondary'):
            self.assertIs(type(row[axis]), int)
        self.assertIs(type(row['cooldown']['minimum_ms']), int)
        self.assertIs(row['synchronization_required'], True)

    def test_independent_native_relationship_table(self):
        self.assertEqual(table(self.native, 'Property'), [
            ('family', 'legacy-interface', 'Hypothesis'),
            ('variant', 'computer-interface', 'Hypothesis'),
            ('request service', 'B501', 'Hypothesis'),
            ('return service', 'B502', 'Hypothesis'),
            ('sequencing direction', 'initiator-to-initiator', 'Hypothesis'),
            ('synchronization required', 'true', 'Hypothesis'),
            ('synchronization token', 'absent; exact bytes Unknown', 'Unknown'),
            ('post-timeout cooldown minimum', '3500 milliseconds', 'Hypothesis'),
            ('cooldown trigger', 'explicit timeout event only', 'Hypothesis'),
            ('timeout duration', 'absent; not zero or cooldown-derived', 'Unknown'),
            ('modern-controller inheritance', 'none', 'Hypothesis'),
        ])

    def test_independent_timing_cases_and_page(self):
        names = ('id', 'family', 'event', 'elapsed_ms', 'result', 'grade')
        self.assertEqual(self.data['timing_cases'],
                         [dict(zip(names, case)) for case in CASES])
        self.assertEqual(table(self.native, 'Case'), [
            (name, family, event, 'absent' if elapsed is None else str(elapsed), result, grade)
            for name, family, event, elapsed, result, grade in CASES])
        for name, family, event, elapsed, result, _ in CASES:
            with self.subTest(case=name):
                self.assertEqual(synthetic_cooldown(self.data['rows'][0], family,
                                                   event, elapsed), result)

    def test_b501_status_is_not_b502_return_data(self):
        self.assertEqual(table(self.native, 'Service role'), [
            ('request', 'B501', 'opaque request', 'Hypothesis'),
            ('positive-status', 'B501', 'status form; not B502 return data', 'Hypothesis'),
            ('return-data', 'B502', 'opaque return data; not B501 status', 'Hypothesis'),
        ])
        roles = {item['role']: item for item in self.data['rows'][0]['service_roles']}
        self.assertEqual(roles['positive-status']['service'], 'B501')
        self.assertEqual(roles['return-data']['service'], 'B502')
        self.assertNotEqual(roles['positive-status']['body'], roles['return-data']['body'])
        self.assertIn('does not make it a B502 return-data body', self.flat_native)

    def test_timeout_and_synchronization_are_not_fabricated(self):
        row = self.data['rows'][0]
        self.assertIs(row['synchronization_required'], True)
        self.assertNotIn('synchronization_token', row)
        self.assertNotIn('timeout_duration_ms', row)
        self.assertNotIn('duration_ms', row['cooldown'])
        self.assertEqual(row['unknown'], {name: 'Unknown' for name in UNKNOWNS})
        self.assertIn('The cooldown minimum is not a timeout duration.', self.flat_native)
        self.assertIn('does not acquire a timeout cooldown solely from this entry',
                      self.flat_native)
        self.assertIn('does not establish synchronization completion, permission to send',
                      self.flat_native)

    def test_raw_fallback_and_independent_qualification(self):
        self.assertEqual(self.data['raw_cases'], [
            dict(raw_hex=h, retention='retain-original-bytes', interpretation='opaque',
                 qualification='Unknown') for h in ('', 'B5 01', 'B5 02 A6')])
        self.assertEqual(table(self.native, 'Synthetic fragment (hex)'), [
            (h, 'retain-original-bytes', 'opaque', 'Unknown')
            for h in ('empty', 'B5 01', 'B5 02 A6')])
        self.assertEqual([bytes.fromhex(c['raw_hex']) for c in self.data['raw_cases']],
                         [b'', bytes([181, 1]), bytes([181, 2, 166])])
        for text in (self.flat_native, self.flat_api):
            for phrase in ('last-known-good', 'uncertain freshness', 'native support',
                           'physical effects', 'persistence and delivery'):
                self.assertIn(phrase, text)
        self.assertIn('not complete telegrams or synchronization tokens', self.flat_native)
        self.assertIn('Grade and qualification are independent', self.flat_native)

    def test_all_native_identity_axes_with_independent_controls(self):
        row = self.data['rows'][0]
        self.assertEqual({axis: row[axis] for axis in IDENTITY}, IDENTITY)
        self.assertEqual(len(IDENTITY), 11)
        # Independently specified probes protect every fixture identity axis.
        # They make no claim to execute Ab34Lookup in a different repository.
        for axis, control, changed, _ in CONTROLS:
            with self.subTest(axis=axis, control=control, changed=changed):
                left = dict(IDENTITY, **{axis: scalar(control)})
                right = dict(left, **{axis: scalar(changed)})
                self.assertEqual([k for k in left if left[k] != right[k]], [axis])
                for key in (left, right):
                    expected_match = key == IDENTITY
                    actual_match = all(row[k] == key[k] for k in IDENTITY)
                    self.assertEqual(actual_match, expected_match)

    def test_api_signatures_and_eleven_key_axes(self):
        self.assertEqual(re.findall(r'^Ab34\w+\(.*$', self.api, re.M), [
            'Ab34Entries() (json.RawMessage, error)',
            'Ab34Lookup(Ab34Key) (json.RawMessage, bool, error)',
        ])
        self.assertIn('package `vaillant`', self.api)
        self.assertEqual(table(self.api, 'Field'), AXES)
        for phrase in ('matches all eleven axes',
                       'Optional absent and explicit zero differ',
                       'Every JSON identity axis is present',
                       '`null` represents an absent optional integer',
                       'such as `00` or `dynamic`', 'explicit `none` token'):
            self.assertIn(phrase, self.flat_api)

    def test_api_production_row_and_identity_mutation_mapping(self):
        self.assertEqual(table(self.api, 'Production ID'), [
            ('ab34-legacy-sequence-none',
             'B501 request; B502 return; synchronization required; post-timeout minimum 3500 ms',
             'Hypothesis', 'Unknown')])
        self.assertEqual(table(self.api, 'Axis'), CONTROLS)
        self.assertEqual({r[0] for r in CONTROLS}, set(IDENTITY))
        for phrase in ('embeds its owned JSON in its owned Go file',
                       'validates identity uniqueness', '`ak24-` ID prefix',
                       'registry row uses `ab34-`', 'complete identity',
                       'explicit Unknown metadata', '`retain-original-bytes`'):
            self.assertIn(phrase, self.flat_api)

    def test_api_returns_errors_copies_and_exact_lookup(self):
        for phrase in (
            '`Ab34Entries` returns a JSON array',
            '`Ab34Lookup` returns exactly one whole row for an exact key',
            'returns `(nil, false, nil)`',
            'Invalid embedded JSON or duplicate keys return an error',
            'with no successful lookup', 'Validation checks identity uniqueness',
            'requires every axis', 'Invalid top-level shape',
            'missing identity axes or incomplete candidate metadata fail closed',
            'No wildcard or nearest-key lookup is permitted',
            'There is no cross-family, variant, direction, field or alternative fallback',
            'Every call returns independent deep byte copies',
            'Mutating any returned row or entries buffer',
            'cannot affect another outstanding result or a later result',
            'including a later call through the other API',
            'Raw form and candidate grade are retained in whole-row results',
            'changing only family to `modern-controller` returns a missing exact key',
        ):
            self.assertIn(phrase, self.flat_api)

    def test_api_unknowns_compatibility_and_delivery_order(self):
        for phrase in (
            'AK23 must merge before AK24 in the same delivery cycle',
            'registry has no dependency back to this page',
            'Merge does not confer native qualification',
            'No clock, transport or session executor is added',
            'catalog/provider APIs and routability remain unchanged',
            'eBUS MCP compatibility and GraphQL parity remain unchanged',
            'No transmit route, scan-default change or automatic native qualification',
            'not stable before Helianthus 1.0',
            'Synchronization-required remains true without an invented synchronization token',
            'synchronization token and timeout duration remain absent',
            'cooldown minimum never supplies a timeout duration or zero default',
            'Minimum-met is not admission to transmit',
            'B501 positive-status and B502 return-data remain separate service roles',
            'documentation checks do not execute the registry implementation',
        ):
            self.assertIn(phrase, self.flat_api)
        for phrase in (
            'exact synchronization bytes', 'state order beyond the synchronization wait',
            'timeout duration', 'segmentation', 'retries', 'return codec',
            'transport adaptation',
        ):
            self.assertIn(phrase, self.flat_native)
            self.assertIn(phrase, self.flat_api)

    def test_native_evidence_first_and_application_boundary(self):
        self.assertIn('ebus-vaillant.md#b501-and-b502-symbolic-access-and-service-pc-interface',
                      self.native)
        self.assertLess(self.native.index('native B501 and B502 contract'),
                        self.native.index('## Finite candidate relationships'))
        self.assertIn('No native capture or measured timing is supplied', self.flat_native)
        self.assertIn('independent return-service identity is context', self.flat_native)
        self.assertIn('Synthetic correctness establishes the declared representation only',
                      self.flat_native)
        self.assertIsNone(re.search(
            r'Ab34|GraphQL|MCP|Helianthus|json\.RawMessage|\bGo\b|executor|API',
            self.native + DATA.read_text()))
        self.assertEqual(re.findall(r'\]\(([^)]+)\)', self.native), [
            'ebus-vaillant.md#b501-and-b502-symbolic-access-and-service-pc-interface',
            'fixtures/ak24_b501_legacy_sequence.json',
        ])


if __name__ == '__main__':
    unittest.main(verbosity=2)
