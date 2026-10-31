# B506 RF registry companion

## Evidence and delivery order

The [native RF supplement](../protocols/vaillant/ebus-b506-rf-sequence.md)
defines the candidate wire boundary first. **Hypothesis:** count and sequence
relationships remain candidates; **Unknown:** native support, physical effects,
persistence and delivery. Synthetic representation checks do not qualify them.

**Proven (local API contract):** package `vaillant` exposes:

```go
Ab17Entries() (json.RawMessage, error)
Ab17Lookup(Ab17Key) (json.RawMessage, bool, error)
```

AK05, registry PR #343, is merged and precedes AK06 in the same delivery cycle.
The registry has no dependency back to this page. Merge does not confer native
qualification. The registry implementation is `catalog/vaillant/ab17_b506_rf_sequence.go`
and embeds `data/ab17_b506_rf_sequence.json` in that owned Go file. This page
introduces no Go file, pending API, shared registration or general family schema.

The registry's operation integers are 13 for count/sequence and 14 for stop;
its related-operation integers are 12 and 13. These are the exact AK05 data
values, not hexadecimal-to-decimal conversions. The native page uses OP12,
OP13 and OP14 as hexadecimal labels. **Unknown:** their numeric wire adaptation;
no conversion or transmit route follows from the catalog representation.

## Exact identity

`Ab17Key` matches all eleven axes. Optional absent and explicit zero differ.
Non-applicable string axes use the explicit `none` token. Instance scope is an
explicit string, such as `00` or `dynamic`, never an invented numeric instance.
The finite RF rows use `none` for that non-applicable axis.

| Field | Go type | JSON axis | Finite RF value |
| --- | --- | --- | --- |
| Ab17Family | string | family | vaillant |
| Ab17Variant | string | variant | B506-RF |
| Ab17Primary | uint8 | primary | 181 |
| Ab17Secondary | *uint8 | secondary | 6 |
| Ab17Operation | *uint8 | operation | 13 or 14 |
| Ab17Direction | string | direction | none |
| Ab17Field | string | field | count, sequence or stop |
| Ab17Alternative | string | alternative | none or 0/1/2/3 |
| Ab17Group | *uint8 | group | null |
| Ab17InstanceScope | string | instance_scope | none |
| Ab17Register | *uint16 | register | null |

No wildcard or nearest-key lookup is permitted. There is no cross-family,
variant, direction, field or alternative fallback. Each production row has an
`ab17-` prefixed ID, this complete identity, stated fields/relations,
`grade: Hypothesis`, `qualification: Unknown`, `ab17_raw_form: retain-original-bytes`
and explicit `ab17_unknown` metadata. All four extent/position fields are
explicit `null`, never inferred zero.

| ID | Operation | Field | Alternative | Declared relationship |
| --- | --- | --- | --- | --- |
| ab17-rf-count-none | 13 | count | none | 0 unlimited; 1..255 finite count-value |
| ab17-rf-sequence-0 | 13 | sequence | 0 | ab17-class-a |
| ab17-rf-sequence-1 | 13 | sequence | 1 | ab17-class-a |
| ab17-rf-sequence-2 | 13 | sequence | 2 | ab17-class-a |
| ab17-rf-sequence-3 | 13 | sequence | 3 | ab17-class-b |
| ab17-rf-stop-none | 14 | stop | none | associated with 12 and 13; order Unknown |

All other sequence values remain unmapped. Class names are local labels for
the two native candidate classes; they assert no numeric extent.

## Return, error and retention behavior

**Proven (local API contract):** `Ab17Entries` returns a JSON array.
`Ab17Lookup` returns exactly one whole row for an exact key; a missing exact key
returns `(nil, false, nil)`. Invalid embedded JSON or duplicate keys return an
error, with no successful lookup. Validation checks identity uniqueness and
requires every axis, including explicit null optional axes. Invalid top-level
shape, missing identity axes or incomplete candidate metadata fail closed.

Every call returns independent deep byte copies. Mutating any returned row or
entries buffer cannot affect another outstanding result or a later result,
including a later call through the other API. Raw form and candidate grade are
retained in whole-row results.

**Unknown:** `ab17_extent_bytes`, `ab17_minimum_bytes`, `ab17_maximum_bytes`,
`ab17_field_position`; stop `ab17_activation_order`, `ab17_retry_count`,
`ab17_timeout`, `ab17_delivery_guarantee`, `ab17_completed_stop`. Count does not
supply retry policy. Neither empty nor nonempty fabricated payloads become
qualified with absent extent. Missing extent is not zero.

Fail-closed admission retains raw evidence and partial last-known-good state
with uncertain freshness; it supplies no cache updater or successful new typed
claim. Existing catalog/provider APIs and routability remain unchanged. eBUS
MCP compatibility and GraphQL parity remain unchanged: no new route, executor,
scan default or automatic native qualification is introduced. These contracts
are not stable before Helianthus 1.0.

## Independent identity controls

Each row below changes only its named axis; both values are valid synthetic
identity controls. Exact lookup must distinguish each pair, and duplicate-key
validation must accept the pair as distinct. Ignoring that axis is the
corresponding production mutation caught by the control. These are declared
contract controls, not a claim that this documentation test executes Go.

| Axis | Control | Changed | Mutation rejected |
| --- | --- | --- | --- |
| family | vaillant | other-family | ignore family |
| variant | B506-RF | other-variant | ignore variant |
| primary | 181 | 182 | ignore primary |
| secondary | 6 | 7 | ignore secondary |
| operation | 13 | 7 | ignore operation |
| direction | none | read | ignore direction |
| field | count | other-field | ignore field |
| alternative | none | other-alternative | ignore alternative |
| group | null | 1 | ignore group |
| instance_scope | none | dynamic | ignore instance_scope |
| register | null | 1 | ignore register |
| secondary | null | 0 | collapse absent and zero secondary |
| operation | null | 0 | collapse absent and zero operation |
| group | null | 0 | collapse absent and zero group |
| register | null | 0 | collapse absent and zero register |

Malformed JSON and duplicate-key error controls, missing exact-key controls,
and independent buffer mutation controls belong to registry executable
validation. The local documentation checks assert this API declaration and the
finite native tables independently; they do not replace registry Go tests.
