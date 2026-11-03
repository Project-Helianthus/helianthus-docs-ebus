# B501 legacy sequencing registry companion

## Evidence and delivery order

The [native family supplement](../protocols/vaillant/ebus-b501-legacy-sequence.md)
and its [synthetic declarations](../protocols/vaillant/fixtures/ak24_b501_legacy_sequence.json)
define the candidate relationships first. **Hypothesis:** sequencing metadata
applies only to `legacy-interface`; `modern-controller` has no alias or fallback.
**Unknown:** native support, physical effects, persistence and delivery.
Independent B502 return-service identity supplies context, not additional
sequencing coverage.

AK23 must merge before AK24 in the same delivery cycle. The registry has no
dependency back to this page. Merge does not confer native qualification.

**Proven (local API contract):** package `vaillant` exposes:

```go
Ab34Entries() (json.RawMessage, error)
Ab34Lookup(Ab34Key) (json.RawMessage, bool, error)
```

The registry embeds its owned JSON in its owned Go file and validates identity
uniqueness. This companion describes the finite contract; it introduces no
pending API import, shared registration or general family schema.

## Exact identity

`Ab34Key` matches all eleven axes. Optional absent and explicit zero differ.
Every JSON identity axis is present; `null` represents an absent optional
integer. Non-applicable string axes use the explicit `none` token. Instance
scope is an explicit string, such as `00` or `dynamic`, never an invented
numeric instance. The finite row uses `none` for this non-applicable axis.

| Field | Go type | JSON axis | Finite value |
| --- | --- | --- | --- |
| Ab34Family | string | family | legacy-interface |
| Ab34Variant | string | variant | computer-interface |
| Ab34Primary | uint8 | primary | 181 |
| Ab34Secondary | *uint8 | secondary | 1 |
| Ab34Operation | *uint8 | operation | null |
| Ab34Direction | string | direction | initiator-to-initiator |
| Ab34Field | string | field | sequencing |
| Ab34Alternative | string | alternative | none |
| Ab34Group | *uint8 | group | null |
| Ab34InstanceScope | string | instance_scope | none |
| Ab34Register | *uint16 | register | null |

No wildcard or nearest-key lookup is permitted. There is no cross-family,
variant, direction, field or alternative fallback. In particular, changing only
family to `modern-controller` returns a missing exact key.

| Production ID | Candidate relationships | Grade | Qualification |
| --- | --- | --- | --- |
| ab34-legacy-sequence-none | B501 request; B502 return; synchronization required; post-timeout minimum 3500 ms | Hypothesis | Unknown |

Each production row retains this complete identity, stated fields and relations,
the candidate grade, explicit Unknown metadata and raw form
`retain-original-bytes`. The native synthetic row uses the `ak24-` ID prefix;
the registry row uses `ab34-`. The numeric pair 181/1 denotes B501; B502 remains
related return-service context rather than a second sequencing row.

## Return, error and retention behavior

**Proven (local API contract):** `Ab34Entries` returns a JSON array.
`Ab34Lookup` returns exactly one whole row for an exact key; a missing exact key
returns `(nil, false, nil)`. Invalid embedded JSON or duplicate keys return an
error, with no successful lookup. Validation checks identity uniqueness and
requires every axis. Invalid top-level shape, missing identity axes or incomplete
candidate metadata fail closed.

Every call returns independent deep byte copies. Mutating any returned row or
entries buffer cannot affect another outstanding result or a later result,
including a later call through the other API. Raw form and candidate grade are
retained in whole-row results.

**Hypothesis:** after an explicitly supplied timeout event, elapsed 3499 ms is
below the minimum; 3500 and 3501 ms meet only the cooldown minimum. A regular
successful return contributes no timeout cooldown solely from this entry.
Synchronization-required remains true without an invented synchronization token.
B501 positive-status and B502 return-data remain separate service roles.

**Unknown:** exact synchronization bytes, state order beyond the synchronization
wait, timeout duration, segmentation, retries, return codec, transport adaptation,
native support, physical effects, persistence and delivery. The synchronization
token and timeout duration remain absent; the cooldown minimum never supplies
a timeout duration or zero default. Minimum-met is not admission to transmit.

Fail-closed admission preserves raw evidence and partial last-known-good state
with uncertain freshness; it admits no successful new typed claim from unknown
metadata. No clock, transport or session executor is added. Existing
catalog/provider APIs and routability remain unchanged. eBUS MCP compatibility
and GraphQL parity remain unchanged. No transmit route, scan-default change or
automatic native qualification follows. These contracts are not stable before
Helianthus 1.0.

## Independent identity controls

Each pair below changes only the named axis; both values are valid synthetic
identity controls. Exact lookup must distinguish the pair, and uniqueness
validation must accept them as distinct keys. The first eleven controls start
from the finite identity; the optional-absence controls use a null control and
change only that field to explicit zero. The production mutation named on each
line would violate that contract. These are declared controls; documentation
checks do not execute the registry implementation.

| Axis | Control | Changed | Mutation rejected |
| --- | --- | --- | --- |
| family | legacy-interface | modern-controller | ignore family |
| variant | computer-interface | other-variant | ignore variant |
| primary | 181 | 182 | ignore primary |
| secondary | 1 | 2 | ignore secondary |
| operation | null | 1 | ignore operation |
| direction | initiator-to-initiator | reverse | ignore direction |
| field | sequencing | other-field | ignore field |
| alternative | none | other-alternative | ignore alternative |
| group | null | 1 | ignore group |
| instance_scope | none | dynamic | ignore instance_scope |
| register | null | 1 | ignore register |
| secondary | null | 0 | collapse absent and zero secondary |
| operation | null | 0 | collapse absent and zero operation |
| group | null | 0 | collapse absent and zero group |
| register | null | 0 | collapse absent and zero register |

Malformed JSON, duplicate keys, missing exact keys, and independent entries/row
buffer mutation require registry executable validation. The documentation
checks independently assert the finite native declarations and this API
contract; they do not replace those executable checks or qualify hardware.
