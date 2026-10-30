# B509 identity shapes: feedback and content

This finite library representation contract is a partial child of
[issue 736](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/736).
It is provisional before Helianthus 1.0.

## Evidence and ownership

Start with the public [native B509 contract](../protocols/vaillant/ebus-vaillant-B509.md#configuration-and-data-point-read-54).
That page's data-point envelope does not establish the identity layout here:
do not transfer its flags or selectors into these examples. No public native
layout establishing these identity fields is supplied here. The identity
interpretations below remain **Hypothesis**; missing native details remain
**Unknown**. Synthetic arithmetic and the inspected library shape are
**Proven** only within their stated scope.

The prerequisite is the merged AL11 catalog,
[helianthus-ebusreg PR 349](https://github.com/Project-Helianthus/helianthus-ebusreg/pull/349):
`catalog/vaillant/ab46_b509_identity_shapes.go`, its adjacent test and
`data/ab46_b509_identity_shapes.json`. Those are implementation evidence,
not proof of native behavior. This page depends on that catalog merging first;
it adds no cross-repository runtime import. The local
[examples](fixtures/al12_b509_identity_shapes.json) are a small synthetic set,
not another catalog, native profile, installed identifier set or family inventory.

## Library contract

`Ab46Entries() (json.RawMessage, error)` validates the entire embedded array
and returns the JSON array. `Ab46Lookup(key Ab46Key) (json.RawMessage, bool, error)`
validates the entire array before exact matching and returns the entire original
row, including opaque metadata. A valid array with no match returns
`nil, false, nil`; an empty array is valid. Invalid JSON, non-array/null roots,
non-object rows, incomplete keys, unknown key members or duplicate exact keys
produce errors. Entries returns nil on error; Lookup returns nil, false and the
error, even if an earlier row would match. Validation is structural; it does
not promote a metadata grade or qualify a device.

Each call returns independent memory: mutating an Entries or Lookup result
must not change the catalog, another result or a later call. No Python check
here executes those Go functions or establishes their runtime parity.

All eleven key members participate in exact identity. Numeric members are
nullable uint16 values; absence is distinct from zero. Primary is required;
secondary, operation, group and register can be absent. String members are
required and nonempty. Strings are literal, case-sensitive tokens; `none`,
`Unknown` and `*` are not wildcards. These are library axes, not proven native
field positions.

| Key member | Matching |
|---|---|
| family | exact string |
| variant | exact string |
| primary | required uint16 |
| secondary | nullable uint16 |
| operation | nullable uint16 |
| direction | exact string |
| field | exact string |
| alternative | exact string |
| group | nullable uint16 |
| instance_scope | exact string |
| register | nullable uint16 |

The companion has six rows, all for the Vaillant family, variant B509,
primary 181, secondary 9, group/register null and instance scope `none`.
Operation values below are decimal library values, corresponding to hex OP53
and OP54. This table summarizes cardinalities rather than duplicating rows.

| Operation | Directions | Field | Alternatives | Rows |
|---|---|---|---|---|
| 83 | read, write | hardware_identifier | packed_decimal_candidate | 2 |
| 84 | Unknown | identity_content | link_address_six, conflicting_seven, segmented_characters | 3 |
| 84 | Unknown | identity_state | none | 1 |

## Interpretation boundaries

| Property | Value | Grade |
|---|---|---|
| hardware_encoding | packed_decimal_pairs | Hypothesis |
| hardware_width_bytes | 6 | Hypothesis |
| flags_bits | Unknown | Unknown |
| invalid_nibble | candidate absent; preserve all raw bytes | Proven |
| selection_by_length | false | Proven |
| complete_identity_inference | false | Proven |
| native_request_admission | false | Proven |
| qualification | Unknown | Unknown |
| presence | Unknown | Unknown |
| freshness | Unknown | Unknown |
| execution | Unknown | Unknown |

OP53 read and write remain separate directions. Retain six opaque bytes and
an optional candidate array independently. Synthetic hex `12 34 56 78 90 12`
permits decimal pairs `12/34/56/78/90/12`: each nibble must be at most nine.
Hex `FA` invalidates the candidate while preserving every original byte.
This is neither an assumed ASCII decode nor a u48 or security identity.
Unknown flag bits forbid constructing a native request here.

OP54 content may have a six-byte link-address candidate or segmented
character fields. Keep the conflicting seven-byte alternative separate and
the extra byte uninterpreted. Length alone cannot select an alternative.
All link-like example bytes are synthetic opaque bytes. Field positions,
segment selectors, padding, termination, transport correlation and the
completion predicate remain **Unknown**.

## Independent state and partial failure

`feedback_success`, `status_success`, `content_extent`,
`segment_completeness` and full-identity validity are separate properties.
The example spelling `completeIdentity` represents validity, not a new
application API. Success feedback with empty or partial content never yields
`completeIdentity=true`. Even otherwise full synthetic content and complete
segments do not establish a native complete identity; status failure does not
discard their raw bytes. The local full-content control therefore also keeps
`completeIdentity=false` because the completion predicate is Unknown.

The examples vary feedback, status, content extent and segment completeness
one at a time from that control. A separate segment failure preserves the
unaffected segment bytes, the failed segment's raw bytes, and the prior useful
bytes for that segment independently. Retained bytes do not imply freshness
or successful completion. Physical qualification, presence, freshness and
execution stay Unknown independently of epistemic grades.

## Verification boundary

The scoped standard-library test checks the declared page contract, exact key
axes and synthetic examples against independent expectations. Its arithmetic
and retention oracle is local, not a native decoder or a Go runtime test.
No native effect, full parity, automatic qualification, transmit route, polling
default or write admission follows. Runtime integration, eBUS MCP compatibility
and GraphQL parity remain carried work with their own checks; this change adds
no application endpoint or schema. Full CI, independent committed-change review,
publication checks and transport classification remain merge requirements.
