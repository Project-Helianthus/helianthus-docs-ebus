# B519 finite reply-policy API companion

Refs Project-Helianthus/helianthus-docs-ebus#1016 and
Project-Helianthus/helianthus-docs-ebus#736 (partial parent slice).

The public native contract comes first:
[B519 mode-policy supplement](../protocols/vaillant/ebus-b519-reply-policy.md).
Its [finite synthetic declarations](../protocols/vaillant/fixtures/ak14_b519_reply_policy.json)
establish representation only. Native relationships remain **Hypothesis**;
qualification, native support, physical effects, persistence and delivery remain
**Unknown**. The separate ten-selector field/CRC catalog is not duplicated.

## Local API contract

**Proven (local API contract):** Package `vaillant` exposes exactly this finite
surface for these rows:

```go
func Ab21Entries() (json.RawMessage, error)
func Ab21Lookup(Ab21Key) (json.RawMessage, bool, error)
```

This is the supplied companion contract, not execution evidence from this
documentation repository. AK13 is the registry companion and merges before
AK14 in the same delivery cycle. The registry has no dependency back to this
page. Merge order does not establish native qualification.

| Field | Type | Native identity member |
| --- | --- | --- |
| Ab21Family | string | family |
| Ab21Variant | string | variant |
| Ab21Primary | uint8 | primary |
| Ab21Secondary | *uint8 | secondary |
| Ab21Operation | *uint8 | operation |
| Ab21Direction | string | direction |
| Ab21Field | string | field |
| Ab21Alternative | string | alternative |
| Ab21Group | *uint8 | group |
| Ab21InstanceScope | string | instance_scope |
| Ab21Register | *uint16 | register |

All eleven axes match exactly. No wildcard or nearest-key lookup is permitted;
there is no cross-family, variant, direction, field or alternative fallback.
Optional absent and explicit zero differ: this applies separately to Secondary,
Operation, Group and Register. Primary is a required uint8. All remaining axes
are strings; non-applicable string axes use the explicit `none` token. Instance
scope is an explicit string, such as `00`, `dynamic` or `none`, never an invented
numeric instance. For these rows it is `none`. Variant `Unknown` is a literal
unresolved identity value, not a wildcard. Direction names the transaction mode;
the candidate related participant does not establish an actual response route.

Each production row has a ticket-prefixed ID, the complete identity, stated
fields/relations, candidate grade, explicit Unknown metadata and retained raw
form. The finite declaration has seven `ak14-` rows: three OP03 mode rows and two
OP01 alternatives in each of two modes. Family is `Vaillant`, primary is B5,
secondary is 19, field is `reply-policy`, group and register are absent. JSON
null maps to an absent optional numeric axis, independently of explicit zero.

Ab21Entries returns a JSON array, including every whole row and its raw form.
Ab21Lookup returns exactly one whole row, never a projected field or subset.
A missing exact key returns `nil, false, nil`. Invalid embedded JSON or duplicate
keys cause Ab21Entries to return `nil, error` and Ab21Lookup to return
`nil, false, error`; neither exposes a partial valid prefix. Duplicate identity
is checked across all eleven axes, including pointer presence and value.
Admission fails closed on malformed data and ambiguity.

The registry embeds its owned JSON in its owned Go file, validates identity
uniqueness and returns independent deep byte copies on every call. A mutation to
any returned row or entries buffer cannot affect a later result, across either
API. Caller-owned key pointers are read by value for comparison. Malformed rows
cannot erase independent partial last-known-good state or raw evidence; keeping
that state does not admit the malformed snapshot. Raw fallback remains available
for unresolved interpretation, with Hypothesis and Unknown metadata intact.

## Independent exact-key probes

The following probes describe missing keys relative to the valid
`ak14-op03-target` control. Each changes only the named member; each control
lookup returns its whole row with `true, nil`, and each probe returns
`nil, false, nil`. All other values stay equal to the control. Secondary and
Operation also compare absent to explicit zero independently: both are missing
keys in this finite area, rather than aliases. Group and Register use absent
controls and explicit-zero probes. These are declarative integration vectors;
documentation checks do not execute a registry implementation.

| Axis | Control | Probe | Result |
| --- | --- | --- | --- |
| Ab21Family | Vaillant | other-family | missing |
| Ab21Variant | Unknown | other-variant | missing |
| Ab21Primary | 181 | 0 | missing |
| Ab21Secondary | 25 | absent | missing |
| Ab21Secondary | 25 | 0 | missing |
| Ab21Operation | 3 | absent | missing |
| Ab21Operation | 3 | 0 | missing |
| Ab21Direction | initiator-to-target | none | missing |
| Ab21Field | reply-policy | none | missing |
| Ab21Alternative | mode-dependent | none | missing |
| Ab21Group | absent | 0 | missing |
| Ab21InstanceScope | none | 00 | missing |
| Ab21Register | absent | 0 | missing |

## Representation and admission boundaries

OP03 mode alone selects target-response, service-toward-A or retained-CRC-for-02.
The initiator associated with receiving-target-B remains associated-initiator-C
for initiator-to-initiator and broadcast modes. The initial sender is sender-A.
OP01 ACK-only and CRC-positive coexist; neither is a completed physical outcome.
Zero-length and three-byte data keep Unknown numeric peer capacity. The block
token remains outside data. Routing, actual acknowledgement and storage effects
remain Unknown. These conditions are independent of lookup success.

Existing catalog/provider APIs and routability remain unchanged. No pending API
is imported, no shared registration or general family schema is introduced, and
no transport code, transmit route, scan-default change or active executor follows
from this metadata. Existing eBUS MCP compatibility and GraphQL parity remain
requirements; this slice adds no endpoint. Candidate metadata alone cannot admit
execution or automatically qualify native support. No authorization gate is
introduced. Nothing is stable before Helianthus 1.0; there is no new major or
experimental namespace.
