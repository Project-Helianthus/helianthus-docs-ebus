# AK22: B524 component catalog and property grouping

Refs #1018; partial slice of #736. Nothing here is stable before Helianthus 1.0.
The [native component supplement](../protocols/vaillant/ebus-b524-component-selectors.md)
and its public B524 contract come first. Plain-byte representation is a
Hypothesis about native components; synthetic arithmetic is Proven only as
local arithmetic. Native qualification and physical support remain Unknown.

## Proven local Ab32 API contract

Package `vaillant` exposes exactly these catalog accessors for this finite area:

```go
func Ab32Entries() (json.RawMessage, error)
func Ab32Lookup(Ab32Key) (json.RawMessage, bool, error)

type Ab32Key struct {
    Ab32Family        string
    Ab32Variant       string
    Ab32Primary       uint8
    Ab32Secondary     *uint8
    Ab32Operation     *uint8
    Ab32Direction     string
    Ab32Field         string
    Ab32Alternative   string
    Ab32Group         *uint8
    Ab32InstanceScope string
    Ab32Register      *uint16
}
```

`Ab32Entries()` returns a JSON array. `Ab32Lookup` returns exactly one whole row
for an exact key, `(nil, false, nil)` for a missing exact key, and an error for
invalid embedded JSON or duplicate keys. Both accessors validate the complete
embedded catalog before returning any data; even duplicates unrelated to the
requested key fail closed. Each call returns independent deep byte copies.
Mutating a returned row or entries buffer cannot affect later results from
either accessor. Wildcard and nearest-key lookup are forbidden.

All eleven axes participate in equality, including optional pointer presence:
absent and explicit zero differ for Secondary, Operation, Group and Register.
Non-applicable string axes use the explicit `none` token. Instance scope is the
literal string `00` or `dynamic`; neither is an invented numeric instance, and
`dynamic` is not a lookup wildcard. No cross-family, variant, direction, field
or alternative fallback is permitted.

Each production row has a ticket-prefixed `ab32-` ID, all eleven identity
fields, stated component fields and relations, candidate grade `Hypothesis`,
explicit `Unknown` metadata and retained raw form. The finite mapping from
each native row is normative: prefix its ID with `ab32-`; copy family, field,
group, instance scope and register; set Variant=`none`, Primary=181,
Secondary=36, Operation=2, Direction=`read` and Alternative=`date` or `time`
according to its component order. All optional numeric axes are present in
these fifteen rows. No string-part or additional family entries are exposed.

AK21 embeds its owned JSON in its owned Go file, validates full identity
uniqueness and preserves the existing package name (otherwise `vaillant`).
This companion describes that contract without importing a pending API or
introducing shared registration or another general family schema. Existing
catalog/provider APIs and routability remain unchanged.

The declaration below is machine-checked documentation of these behaviors;
the checks model the contract, not a linked Go implementation.

```json
{
  "package": "vaillant",
  "entries_shape": "array",
  "lookup_result": "whole-row",
  "missing_result": [null, false, null],
  "invalid_json": "error",
  "duplicate_keys": "error",
  "validate_before_lookup": true,
  "copy": "independent-deep-bytes-every-call",
  "matching": "all-eleven-exact-with-optional-presence",
  "wildcard": false,
  "nearest": false,
  "id_prefix": "ab32-",
  "axes": [
    ["Ab32Family", "string"],
    ["Ab32Variant", "string"],
    ["Ab32Primary", "uint8"],
    ["Ab32Secondary", "*uint8"],
    ["Ab32Operation", "*uint8"],
    ["Ab32Direction", "string"],
    ["Ab32Field", "string"],
    ["Ab32Alternative", "string"],
    ["Ab32Group", "*uint8"],
    ["Ab32InstanceScope", "string"],
    ["Ab32Register", "*uint16"]
  ],
  "grouping": {
    "retain_siblings": true,
    "retain_last_known_good": true,
    "missing_overwrites_retained": false,
    "component_raw_and_failure_independent": true,
    "fresh_on_merge": false,
    "timestamp": false,
    "century": "Unknown",
    "timezone": "Unknown",
    "admission": "withheld",
    "semantic_grade": "Hypothesis",
    "native_grade": "Unknown"
  },
  "synthetic_grouping_cases": [
    {
      "id": "missing-month",
      "previous": [null, null, null],
      "incoming": [31, null, 99],
      "states": ["present", "missing", "present"],
      "expected_retained": [31, null, 99],
      "expected_complete": false
    },
    {
      "id": "failed-month",
      "previous": [30, 11, 98],
      "incoming": [31, 255, 99],
      "states": ["present", "failed", "present"],
      "expected_retained": [31, 11, 99],
      "expected_complete": false
    },
    {
      "id": "missing-retained-month",
      "previous": [30, 11, 98],
      "incoming": [31, null, 99],
      "states": ["present", "missing", "present"],
      "expected_retained": [31, 11, 99],
      "expected_complete": false
    }
  ]
}
```

## Component grouping and retention

**Proven local grouping contract:** retain component order, raw incoming byte,
field-level state (`present`, `missing`, `failed`) and the separate last-known-good
cell. For `[31, missing, 99]`, retain raw day 31 and year 99 and an explicit
missing month. A missing/failed month never overwrites a retained month. Failed
raw 255 remains evidence of that failure, separately from retained month 11.
Failure in any position leaves unaffected retained cells intact. Retained
history cannot turn a partial incoming group into a complete observation.

Merge creates no fresh flag. Retention is not a new observation and cannot
refresh siblings or last-known-good cells. Existing per-field freshness evidence
remains separate; unavailable freshness withholds admission. No complete
timestamp or century is constructed, even when all three components are present.
Independent date domains are metadata, not joint date validation or a calendar
edit constraint. Zone dates are never paired with unrelated time selectors by
adjacent position. OP06, wrong group and wrong family yield no component entry;
their raw evidence remains available without an admitted semantic value.

## Unknowns, parity and dependency direction

**Unknown:** zone-name selectors, string encoding, width and termination;
no suffix creates a string-part row. Native support, physical effects,
persistence and delivery remain Unknown independently of local API correctness.
The unresolved native DA/DB role and codec conflicts remain visible in the
native supplement. Candidate grades and raw fallback survive every projection.
There is no decoder, transmit route, scan-default change, active executor or
automatic native qualification here. eBUS MCP compatibility and GraphQL parity
are preserved: any later projection retains identical raw, partial, failure,
qualification and freshness distinctions on both surfaces.

Registry-first order is AK21 before AK22 in the same delivery cycle. The registry
has no dependency back to this page. Merging either companion does not qualify
native behavior. Focused documentation examples establish no runtime copy/error
behavior in AK21; that implementation needs its own independent checks.
