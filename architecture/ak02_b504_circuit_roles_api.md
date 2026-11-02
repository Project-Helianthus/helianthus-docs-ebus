# B504 circuit roles API companion

The [native family supplement](../protocols/vaillant/ebus-b504-circuit-roles.md)
defines the finite semantic candidates first. **Hypothesis:** Its twenty
relationships distinguish circuit roles, cooling support, generation, flow
suppression, drying indication, corrected average and solar calculations.
**Unknown:** Native support, physical effects, persistence and delivery remain
separately qualified. Synthetic correctness establishes the declared
representation only.

## Local API contract

**Proven (local API contract):** Package `vaillant` exposes exactly:

```go
func Ab15Entries() (json.RawMessage, error)
func Ab15Lookup(Ab15Key) (json.RawMessage, bool, error)
```

`Ab15Entries` returns a JSON array. `Ab15Lookup` returns exactly one whole row
for an exact key, with `true` and no error. A missing exact key returns no row,
`false` and no error. Invalid embedded JSON or duplicate keys produce an error.
Validation of the entire embedded array precedes admission of any matching row;
a malformed later row cannot admit an earlier match. Errors return no entries
buffer or lookup row; lookup also returns `false`. No wildcard or nearest-key
lookup is permitted.

| Ab15Key field | Go type | Identity axis | Matching rule |
| --- | --- | --- | --- |
| Ab15Family | string | family | exact family |
| Ab15Variant | string | variant | exact variant |
| Ab15Primary | uint8 | primary | exact primary |
| Ab15Secondary | *uint8 | secondary | absent differs from zero |
| Ab15Operation | *uint8 | operation | absent differs from zero |
| Ab15Direction | string | direction | exact direction |
| Ab15Field | string | field | exact field |
| Ab15Alternative | string | alternative | exact alternative |
| Ab15Group | *uint8 | group | absent differs from zero |
| Ab15InstanceScope | string | instance_scope | exact explicit string |
| Ab15Register | *uint16 | register | absent differs from zero |

All eleven axes match independently. No cross-family, variant, direction,
field or alternative fallback is permitted. Optional absent and explicit zero
differ for Secondary, Operation, Group and Register. Non-applicable string axes
use an explicit `none` token. Instance scope is an explicit string such as `00`
or `dynamic`; numeric instances are not invented. This supplement selects no
new instance scope, group or register value.

Each production row has an `ab15-` ticket-prefixed ID, this complete identity,
stated fields/relations, candidate grade `Hypothesis`, explicit `Unknown`
metadata and retained `raw_form`. An unclassified role retains the raw token
with Unknown interpretation; it does not borrow a familiar role's meaning.
Only the twenty relationships in the native supplement belong to this area.
No OP16 conversion, OP20/21 sentinel table, solar scalar enumeration or
preheat-domain table is introduced. Unprovided byte positions, widths,
generation values, suppression algorithm, percentage formula and switching-ratio
formula remain Unknown. OP33 retains correction-included metadata without
selecting averaging or correction arithmetic.

**Proven (local storage contract):** The AK01 registry Go file embeds its own
JSON. Identity uniqueness is validated before returning data. Every entries
buffer and returned row is an independent deep byte copy. Mutating any returned
entries buffer or row cannot affect an existing independent result or a later
call, including calls through the other function. Invalid new data fails closed.
A consumer retaining partial last-known-good state preserves its raw evidence
and provenance; failed new data cannot replace it or be admitted as fresh.
No refresh, write or state-update API is added here.

## Independent identity controls

**Proven (contract controls):** Each pair below changes only the named axis.
Both keys are valid typed controls. With both complete rows present, each exact
lookup selects its own whole row. With only the left row present, the right key
is a miss. The pairs describe conformance expectations, not observed native
traffic or executed registry qualification. Other axes remain fixed per pair.

| Axis | Left control | Right control | Mutation detected |
| --- | --- | --- | --- |
| Ab15Family | B504 | B505 | ignoring family |
| Ab15Variant | role-a | role-b | ignoring variant |
| Ab15Primary | 181 | 180 | ignoring primary |
| Ab15Secondary | 4 | 5 | ignoring secondary |
| Ab15Operation | 13 | 24 | ignoring operation |
| Ab15Direction | request | response | ignoring direction |
| Ab15Field | circuit-temperature | desired-temperature | ignoring field |
| Ab15Alternative | none | candidate-b | ignoring alternative |
| Ab15Group | 1 | 2 | ignoring group |
| Ab15InstanceScope | 00 | dynamic | ignoring instance scope |
| Ab15Register | 1 | 2 | ignoring register |
| Ab15Secondary | absent | 0 | coalescing absent secondary with zero |
| Ab15Operation | absent | 0 | coalescing absent operation with zero |
| Ab15Group | absent | 0 | coalescing absent group with zero |
| Ab15Register | absent | 0 | coalescing absent register with zero |

**Proven (copy/error expectations):** Independent entries and row buffers retain
their original bytes after a separately returned buffer is mutated. Invalid
embedded JSON and duplicate complete identities each cause errors through both
functions, even when a requested row precedes the invalid data. Raw evidence
and candidate grades survive successful whole-row retrieval. These controls
require the registry implementation for execution; prose and synthetic data
checks alone do not establish production behavior.

## Compatibility and companion order

**Proven (scope boundary):** Existing catalog/provider APIs and routability
remain unchanged. eBUS MCP compatibility and GraphQL parity remain unchanged;
this companion adds no endpoint, projection or application command. There is
no transmit route, scan-default change, active executor or automatic native
qualification. No new general family schema, major namespace or experimental
namespace is introduced. Nothing is stable before Helianthus 1.0.

**Proven (dependency direction):** AK01 must merge before AK02 within the same
delivery cycle. There is no dependency from the registry back to this page.
Their merge does not establish native qualification. The local API contract
above is separate from the Hypothesis grade of native role associations and
the Unknown status of native support, physical effects, persistence and delivery.
