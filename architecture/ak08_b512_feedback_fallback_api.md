# B512 OP01 feedback fallback API companion

The [native family supplement](../protocols/vaillant/ebus-b512-feedback-fallback.md)
defines the finite candidate relationships first. **Hypothesis:** Its twelve
field/direction combinations describe B512 OP01 only. **Unknown:** Native
support, physical effects, persistence and delivery remain separately qualified.
Synthetic correctness establishes the declared representation only.

**Proven (local API contract):** Package `vaillant` exposes:

```go
func Ab18Entries() (json.RawMessage, error)
func Ab18Lookup(Ab18Key) (json.RawMessage, bool, error)
```

`Ab18Entries` returns a JSON array. `Ab18Lookup` returns exactly one whole row
for an exact key, with `true` and no error; a missing exact key returns no row,
`false` and no error. Invalid embedded JSON or duplicate keys produce an error.
Validation covers the entire array before any matching row is admitted; an
invalid later row cannot admit an earlier match. An error yields no lookup row
and `false`. No wildcard or nearest-key lookup is permitted.

| Ab18Key field | Go type | JSON axis | Finite value |
| --- | --- | --- | --- |
| Ab18Family | string | family | B512 |
| Ab18Variant | string | variant | OP01 |
| Ab18Primary | uint8 | primary | 181 |
| Ab18Secondary | *uint8 | secondary | 18 |
| Ab18Operation | *uint8 | operation | 1 |
| Ab18Direction | string | direction | request or positive |
| Ab18Field | string | field | one of the six native fields |
| Ab18Alternative | string | alternative | none |
| Ab18Group | *uint8 | group | absent |
| Ab18InstanceScope | string | instance_scope | none |
| Ab18Register | *uint16 | register | absent |

All eleven axes match independently. Optional absent and explicit zero differ
for Secondary, Operation, Group and Register. A complete JSON key retains
nullable axes explicitly; absent optional values are represented by null.
Non-applicable string axes use the explicit `none` token. Instance scope is an
explicit string, such as `00` or `dynamic` when applicable; this finite area
uses `none`, without inventing numeric instances. No cross-family, variant,
direction, field or alternative fallback is permitted.

Each production row has an `ab18-` ticket-prefixed ID, the complete identity,
logical position, u8 type, candidate grade `Hypothesis`, explicit `Unknown`
metadata and retained `raw_form`. `raw_fallback` retains the raw token and
candidate meaning independently. The four pump request rows map FF to
leave-unchanged; positive rows map FF to function-unavailable. Relay/flap rows
retain state-0F and state-F0, with other values no-action and polarity Unknown.
Logical positions are not physical offsets. Boolean default true is separate
from raw_default null and raw_default_encoding Unknown. Feedback source remains
setpoint-fallback without an actual signal and actual-signal when present;
equality with setpoint never establishes actual provenance. Wire discriminator
and physical value remain Unknown.

**Proven (local storage behavior):** The owned registry Go file embeds its JSON.
Identity uniqueness is validated before returning data. Every entries buffer
and every returned row is an independent deep byte copy. Mutating one result
cannot affect an existing independent result or any later call. Invalid data
fails closed; a consumer retaining partial last-known-good state must preserve
its raw evidence and provenance and must not admit failed new data as fresh.
No refresh or state-update API is introduced here.

**Proven (finite boundary):** Existing catalog/provider APIs and routability
remain unchanged. No transmit route, scan-default change, active executor or
automatic native qualification follows from this representation. Existing eBUS
MCP compatibility and GraphQL parity remain unchanged; this companion adds no
endpoint, projection or application command. No new major or experimental
namespace is introduced. Nothing is stable before Helianthus 1.0.

## Evidence

The merged AK07 implementation is in
[the registry source](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/main/catalog/vaillant/ab18_b512_feedback_fallback.go),
[its finite data](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/main/catalog/vaillant/data/ab18_b512_feedback_fallback.json)
and [its tests](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/main/catalog/vaillant/ab18_b512_feedback_fallback_test.go).
This implementation evidence establishes the local API contract, not native
wire qualification. AK07 precedes this page within the same delivery cycle;
there is no dependency from the registry back to this page.
