# B555 additional forms: local API companion

The [native supplement](../protocols/vaillant/ebus-b555-additional-forms.md)
and its [finite data](../protocols/vaillant/fixtures/ak16_b555_additional_forms.json)
come first. **Hypothesis:** candidate native relationships and coordinates.
**Proven:** the declared local API contract and synthetic arithmetic only.
**Unknown:** native support, physical qualification, physical adaptation, prefix
presence, other timer variants, physical effects, persistence and delivery.
Qualification is independent of representation completeness and candidate grade.
Nothing is stable before Helianthus 1.0.

## Ab26 API contract

Package `vaillant` exposes exactly these signatures for this finite addition:

```go
Ab26Entries() (json.RawMessage, error)
Ab26Lookup(Ab26Key) (json.RawMessage, bool, error)
```

`Ab26Entries` returns a JSON array. `Ab26Lookup` returns exactly one whole row,
false for a missing exact key, and an error for invalid embedded JSON or duplicate
keys. Both calls validate the whole embedded data before returning results;
even a duplicate outside the requested key is an error. No wildcard or
nearest-key lookup is permitted. There is no cross-family, variant, direction,
field or alternative fallback. Missing exact keys do not expose a nearby row.

| Ab26Key field | Go type | Matching |
| --- | --- | --- |
| Ab26Family | string | exact |
| Ab26Variant | string | exact |
| Ab26Primary | uint8 | exact |
| Ab26Secondary | *uint8 | exact, absent differs from zero |
| Ab26Operation | *uint8 | exact, absent differs from zero |
| Ab26Direction | string | exact |
| Ab26Field | string | exact |
| Ab26Alternative | string | exact |
| Ab26Group | *uint8 | exact, absent differs from zero |
| Ab26InstanceScope | string | exact |
| Ab26Register | *uint16 | exact, absent differs from zero |

All eleven axes participate in identity. Optional values compare by presence
and numeric value, never pointer address. Non-applicable string axes use `none`.
Instance scope is an explicit string, such as `00` or `dynamic`; it is not an
invented numeric instance. Each production row has an `ab26-` prefixed ID,
the complete Ab26Key identity, stated fields/relations, grade `Hypothesis`,
explicit Unknown metadata, and retained raw form. The finite area is A0/A7
function/channel masks, A1/A2/A8/A9 reserved forms, and positive A4/A5 fields.
No A3 or A6 API or another general family schema is introduced.

The registry companion embeds its owned JSON in its owned Go file, validates
identity uniqueness, and returns independent deep byte copies on every call.
Mutating any returned row or entries buffer cannot affect a later result,
including a later call through the other API. Invalid JSON and duplicate keys
fail closed without returning partial entries or a partial row. The existing
package name is retained where it exists; otherwise `vaillant` is used. No pending API
is imported; shared registration, existing catalog/provider APIs and routability
remain unchanged.

## Machine-checked finite contract

This declaration is consumed by the documentation oracle. It specifies the
companion contract; the oracle does not execute the registry implementation.

```json
{
  "package": "vaillant",
  "entries_signature": "Ab26Entries() (json.RawMessage, error)",
  "lookup_signature": "Ab26Lookup(Ab26Key) (json.RawMessage, bool, error)",
  "key_axes": [
    ["Ab26Family", "string"],
    ["Ab26Variant", "string"],
    ["Ab26Primary", "uint8"],
    ["Ab26Secondary", "*uint8"],
    ["Ab26Operation", "*uint8"],
    ["Ab26Direction", "string"],
    ["Ab26Field", "string"],
    ["Ab26Alternative", "string"],
    ["Ab26Group", "*uint8"],
    ["Ab26InstanceScope", "string"],
    ["Ab26Register", "*uint16"]
  ],
  "optional_presence": "distinct",
  "lookup": "exact_whole_row",
  "missing": "false",
  "invalid_json": "error",
  "duplicate_keys": "error",
  "copies": "independent_deep_bytes",
  "row_id_prefix": "ab26-",
  "row_grade": "Hypothesis",
  "row_unknown": ["native_support", "physical_qualification", "physical_adaptation", "persistence", "delivery"],
  "retain_raw": true,
  "extent_axes": ["declared_extent", "accessible_extent", "initialized_extent", "storage_length"],
  "extent_rule": "minimum_of_all_four",
  "a4_complete_bytes": 9,
  "a5_complete_bytes": 7,
  "count_supplies_extent": false,
  "capacity_supplies_extent": false,
  "threshold_supplies_extent": false,
  "status_supplies_extent": false,
  "status_is_acceptance": false,
  "raw_setpoint_scale": 1,
  "ffff_sentinel": "Unknown",
  "hour_domain": [0, 24],
  "minute_domain": [0, 59]
}
```

## Bounded local representation

The safe-decoder policy keeps status, numeric threshold, actual accessible bytes,
initialized storage and local count independent. For each field, its exclusive
end must fit all four bounds: declared extent, accessible extent, initialized
extent and storage length. Nonnegative integer extents are required. An
accessible or initialized extent exceeding storage is inconsistent and cannot
admit completeness. Available backing capacity does not create received bytes;
local count and numeric threshold never supply extent. A status byte does not
establish admission or native success.

A4 needs all nine accessible initialized bytes for a complete field
representation. Eight bytes can retain status and seven weekday counts while
the 24-hour count is missing. The existing requester threshold of eight does
not make that full representation complete. A5 needs all seven accessible
initialized bytes: a low setpoint byte alone never becomes a word. Storage 16
with accessible 6 does not complete A5, even with a larger local count.

Retain raw accessible initialized bytes, including bytes beyond the declared
field span; do not expose storage beyond the received extent as raw evidence.
Preserve each independently bounded field and partial last-known-good state;
an incomplete replacement cannot overwrite a complete prior field. Missing
fields are absent, never fabricated zeros. Completeness concerns field presence;
status and time-domain results remain separate. Out-of-domain time bytes stay
raw with an invalid-domain result. FFFF stays numeric 65535 with no contextual
unit or sentinel promotion; no A3 scale or unit is imported.

The synthetic extent matrix crosses accessible 8/9/10 for A4 and 6/7/8 for A5
with declared extents, initialized extents, numeric thresholds and local counts
independently. Extra bytes remain raw. A1/A2/A8/A9 produce reserved bytes only,
never executable settings. No physical offset subtraction, prefix adaptation,
A6 weekly refresh implementation or automatic native qualification is added.

## Companion and integration boundary

Registry-first: AK15 must merge before this page; both belong to the same
delivery cycle. The registry has no dependency back to this page. Neither
merge constitutes native qualification. Refs #1020 and #736; this partial child
does not close the parent.

Existing eBUS MCP compatibility and GraphQL parity remain required; this
documentation adds no transport, transmit route, scan-default change, active
executor or runtime integration. Independent committed-change review, full CI,
Gate D and applicable publication/transport classification remain later ship
requirements. The documentation oracle establishes declared representation
consistency only; companion runtime, transport and hardware qualification are
**Unknown** here.
