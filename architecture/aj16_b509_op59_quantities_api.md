# B509 OP59 finite library contract

The native authority for this slice is the
[B509 OP59 supplement](../protocols/vaillant/ebus-b509-op59-quantities.md).
The companion finite library contract has exactly two functions:

```go
Ab14Entries() ([]Ab14Entry, error)
Ab14Lookup(key Ab14Key) (Ab14Entry, bool, error)
```

No runtime decoder, generic schema or provider API is introduced here.
All new declarations and fields use the `ab14` or `Ab14` prefix; semantic
labels remain data. This is a pre-1.0 contract with no stability promise,
new major namespace or experimental namespace.

## Exact key axes

| Field | Type | Identity rule |
| --- | --- | --- |
| Ab14Family | string | exact family |
| Ab14Variant | string | exact variant |
| Ab14Primary | uint8 | exact primary |
| Ab14Secondary | *uint8 | absent differs from explicit zero |
| Ab14Operation | *uint8 | absent differs from explicit zero |
| Ab14Direction | *string | absent differs from supplied direction |
| Ab14Field | string | exact field |
| Ab14Group | *uint8 | absent differs from explicit zero |
| Ab14RequestedInstance | *uint8 | absent differs from explicit zero |
| Ab14Register | *uint16 | absent differs from explicit zero |
| Ab14CommandRole | *string | absent differs from supplied role |

`Ab14Key` retains every axis above. B524 additionally retains group,
requested instance, register and command role; these axes do not imply any
B524 entry or semantics in this five-entry B509 slice. Matching compares
pointer presence and pointed-to values, never pointer addresses. No axis is
a wildcard: absent direction does not match a supplied direction, and an
absent optional numeric axis does not collapse into zero.

## Entry boundaries

`Ab14Entry` carries `Ab14Key`, `Ab14Grade`, `Ab14MetadataPresence`,
`Ab14PhysicalQualification`, `Ab14Codec`, `Ab14Position`, `Ab14Label`,
`Ab14PreserveRaw` and `Ab14Unknown`. The nested `Ab14Codec` carries
`Ab14Representation`, `Ab14Width`, `Ab14Divisor` and `Ab14Unit`.

| Property | Contract |
| --- | --- |
| Ab14Grade | Hypothesis for each of the five fields |
| Ab14MetadataPresence | Proven describes metadata presence only |
| Ab14PhysicalQualification | Unknown independently of grade |
| Ab14PreserveRaw | true independently of codec |
| Ab14Position | absent; absolute positions are Unknown |
| Ab14Label | absent; no fabricated label |
| Ab14Unknown | preserves each unprovided fact independently |

Temperature, flow and volume retain their independent codecs from the native
page. Minimum and maximum volume retain raw representation and absent width,
divisor and unit; scale, coordinates and enforcement remain Unknown.
Sentinels, native support, response adaptation, direction and broad catalog
completeness remain Unknown. Neither metadata presence nor successful lookup
qualifies a device family, authorizes a write or supplies a missing fact.

## Ownership and errors

| Case | Result |
| --- | --- |
| Ab14Entries success | five finite entries; nil error; independently owned nested data |
| Ab14Lookup hit | matching entry; true; nil error; independently owned nested data |
| Ab14Lookup well-formed miss | zero Ab14Entry; false; nil error |
| Ab14Entries invalid embedded data | nil entries; non-nil error |
| Ab14Lookup invalid embedded data | zero Ab14Entry; false; non-nil error |
| returned nested data mutation | no change to another result or later call |

Independent ownership includes the entry slice, key pointers, codec pointer
and its optional values, position and label pointers, and unknown slices.
Entries must not share mutable nested storage with each other or successful
lookups. Mutating either function's result cannot alter library data.

Malformed or trailing embedded data, unknown embedded fields, wrong entry
count, duplicate exact keys, invalid required identity or grade metadata,
missing codecs, unsupported representations, nonpositive divisors, incomplete
quantity codecs and scaled raw limits fail closed. A bad embedded entry cannot
be hidden by a lookup miss. A validation error produces no successful partial
library result; callers retain their previous last-known-good data and raw
partial observations independently, without promoting stale or unknown facts.

This document specifies the contract; the offline documentation checks do not
execute the companion library's copy, lookup or error paths. Existing eBUS MCP
compatibility and GraphQL parity remain unchanged; this slice adds no adapter,
transport behavior, polling defaults or control execution.
