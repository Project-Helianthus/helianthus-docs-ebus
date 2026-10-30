# Exact family lookup for B524 candidate codebooks

Proven: the [native B524 contract](../protocols/vaillant/ebus-vaillant-B524.md),
[register map](../protocols/vaillant/ebus-vaillant-B524-register-map.md) and
[scalar shapes](../protocols/vaillant/ebus-b524-scalar-shapes.md) retain native
opcode/group/instance/register identity before interpretation. OP06 cannot
inherit OP02 labels. Family selection is explicit; there is no auto-detection.
The [synthetic fixture](fixtures/ak20_b524_family_codebooks.json) records the
finite representation, not observations or physical qualification.

Hypothesis: all seven codebooks use OP02 and the candidate family tokens
`controller-700` and `controller-720`. The following complete finite tables
use decimal raw codes. Unlisted codes remain unlabelled with Unknown meaning.
Each `raw:label` pair retains the unsigned raw code; signed8 alone interprets
raw 255 (`FF`) as candidate -1/unbound. No unrelated u16 sign extension occurs.

| Group | Register | Instance scope | Alternative | controller-700 | controller-720 |
| --- | --- | --- | --- | --- | --- |
| 01 | 0003 | 00 | u16 | 0:off,1:automatic,2:day | 0:off,1:time-controlled,2:manual |
| 02 | 0002 | dynamic | u16 | 0:deactivated,1:heating,2:fixed-flow,3:DHW,4:return-flow,5:pool | 0:deactivated,1:heating,2:fixed-flow,3:DHW,4:return-flow |
| 03 | 0001 | dynamic | u16 | 0:off,1:automatic,2:day | 0:off,1:time-controlled,2:manual |
| 03 | 0006 | dynamic | u16 | 0:off,1:automatic,2:day,3:setback | 0:off,1:time-controlled,2:manual |
| 03 | 0013 | dynamic | u16 | 0:none,1:central,2:remote-circuit-one,3:remote-circuit-two,4:remote-circuit-three,5:remote-circuit-four,6:remote-circuit-five,7:remote-circuit-six,8:remote-circuit-seven,9:remote-circuit-eight | 0:none,1:central,2:remote-circuit-one,3:remote-circuit-two,4:remote-circuit-three,5:remote-circuit-four |
| 03 | 001B | dynamic | u8 | 0:no-quick-mode,1:ventilation-boost,3:party,4:quick-veto,5:one-day-holiday,6:one-day-bank-holiday,7:holiday,8:bank-holiday,10:system-off | 0:no-special-function,1:ventilation-boost,4:quick-veto,7:holiday,10:system-off |
| 03 | 001B | dynamic | u16 | 0:no-quick-mode,1:ventilation-boost,3:party,4:quick-veto,5:one-day-holiday,6:one-day-bank-holiday,7:holiday,8:bank-holiday,10:system-off | 0:no-special-function,1:ventilation-boost,4:quick-veto,7:holiday,10:system-off |
| 03 | 001C | dynamic | signed8 | 255:unbound,0:control-circuit-one,1:control-circuit-two,2:control-circuit-three | 255:unbound,0:control-circuit-one,1:control-circuit-two,2:control-circuit-three,3:control-circuit-four,4:control-circuit-five,5:control-circuit-six,6:control-circuit-seven,7:control-circuit-eight,8:control-circuit-nine |

Proven representation rule: RR001B has separate u8 and u16 alternatives;
reply length does not select either alternative. Dynamic instance scope is
metadata-only, not a scan bound or installed cardinality or proof of a present
slot. The string `00` describes the singleton scope; it does not turn dynamic
scope into a numeric instance. Unknown family returns raw/Unknown meaning.

## Local architecture API

Proven local API contract: package `vaillant` exposes exactly these signatures:

```go
Ab30Entries() (json.RawMessage, error)
Ab30Lookup(Ab30Key) (json.RawMessage, bool, error)
```

`Ab30Entries` returns a JSON array. `Ab30Lookup` returns exactly one whole row,
false for a missing exact key and an error for invalid embedded JSON or duplicate
keys. Invalid data fails closed before any row is returned. No wildcard or
nearest-key lookup is permitted. The complete key is:

| Go field | Type | JSON axis | Finite value |
| --- | --- | --- | --- |
| Ab30Family | string | family | controller-700 or controller-720 |
| Ab30Variant | string | variant | none |
| Ab30Primary | uint8 | primary | 181 |
| Ab30Secondary | *uint8 | secondary | 36 |
| Ab30Operation | *uint8 | operation | 2 |
| Ab30Direction | string | direction | read |
| Ab30Field | string | field | value |
| Ab30Alternative | string | alternative | u8, u16 or signed8 |
| Ab30Group | *uint8 | group | 1, 2 or 3 |
| Ab30InstanceScope | string | instance_scope | 00 or dynamic |
| Ab30Register | *uint16 | register | table register |

Proven: all eleven axes match exactly, with no cross-family, variant, direction,
field or alternative fallback. Optional absent and explicit zero differ.
Non-applicable string axes use an explicit none token. Every identity axis is
present in each JSON key; optional pointer absence is represented by null.
Empty or omitted string axes cannot act as wildcards.

Proven representation: each row has an `ab30_` ID, the complete identity,
`enumeration` fields/relations, Hypothesis candidate grade, Proven representation
grade, explicit Unknown metadata and retained raw form. The finite area contains
16 rows, including both RR001B widths for each family. AK19 embeds its JSON in
its Go file, validates identity uniqueness and returns independent deep byte
copies on every call. A mutation to any returned row or entries buffer cannot
affect a later result. Existing catalog/provider APIs and routability remain
unchanged. This page introduces no Go implementation or shared registration.

## Evidence and admission boundaries

Proven synthetic checks cover every listed mapping and independent single-axis
changes, including optional absent versus zero. A missing key or unlisted raw
code retains raw bytes with Unknown meaning. Invalid admission preserves partial
last-known-good state and raw evidence; it does not publish a new qualified
value. This is a consumer preservation rule, not a new stateful catalog API.

Unknown: native_support, physical_effects, persistence, delivery,
installed_cardinality, present_slots, freshness and unlisted_codes.
Synthetic correctness establishes the declared representation only. Native
support and physical qualification remain separate from Proven local behavior.
No names import, generic codec, constraint admission, UI label path, routed
method or physical permission is added. eBUS MCP compatibility and GraphQL
parity remain unchanged; this contract adds no transport surface or executor.
Nothing is stable before Helianthus 1.0.

Proven dependency order: AK19 registry delivery precedes this page in the same
delivery cycle. The registry has no dependency back to this page. Merging the
registry and page does not establish native qualification. Refs #929; partial
parent slice: Refs #736. The fixture is a synthetic representation of the
finite AK19 area; the Python checks execute that representation and page
contract, not the companion Go implementation.
