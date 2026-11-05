# B512 heat-pump I/O catalog contract

The [native family supplement](../protocols/vaillant/ebus-b512-heatpump-io.md)
is the protocol contract for this finite area. Native fields and candidate
relationships precede application projections. **Hypothesis** describes all
candidate wire interpretations. **Proven** describes the local API contract
below, not native support. Physical effects, persistence, delivery, native
support, physical reply form and qualification remain **Unknown**.

## Local API

Package `vaillant` exposes exactly these signatures for this catalog:

```go
func Ab19Entries() (json.RawMessage, error)
func Ab19Lookup(Ab19Key) (json.RawMessage, bool, error)
```

`Ab19Entries` returns a JSON array. `Ab19Lookup` returns exactly one whole row
for an exact key; a missing exact key returns `(nil, false, nil)`. Invalid
embedded JSON or duplicate keys produce an error from both calls; lookup then
returns no row and false. Validation covers the whole embedded catalog before
lookup, so an earlier match cannot hide later invalid or duplicate data.
Empty arrays, incomplete identities and invalid or duplicate IDs also fail closed.

The owned catalog JSON is embedded in its companion Go source. Each production
row has an `ab19_` ID, the complete eleven-axis identity, stated fields and
relations, `Hypothesis` grade, explicit `Unknown` metadata and retained raw form.
`metadata_presence` being `Proven` establishes presence only. The finite scope is
B5/12 operations 0F, 10, 11 and 12, with the stated request and positive fields.
No other family or general family schema is introduced.

`Ab19Key` uses these exact fields and types. Nullable axes use JSON null for
absent, not an omitted identity member. Every string axis is explicit;
non-applicable strings use `none`. Instance scope is a string such as `00` or
`dynamic`, never an invented numeric instance. The current rows use `none`.

| Field | Go type | Exact matching boundary | Single-axis control |
| --- | --- | --- | --- |
| Ab19Family | string | family | vaillant to other-family |
| Ab19Variant | string | variant | B512-heatpump-io to other-variant |
| Ab19Primary | uint8 | primary | 181 to 180 |
| Ab19Secondary | *uint8 | secondary | 18 to 0; absent differs from explicit zero |
| Ab19Operation | *uint8 | operation | 15 to 0; absent differs from explicit zero |
| Ab19Direction | string | direction | request to other-direction |
| Ab19Field | string | field | ab19_outputs to ab19_other |
| Ab19Alternative | string | alternative | none to other-alternative |
| Ab19Group | *uint8 | group | absent to explicit zero |
| Ab19InstanceScope | string | instance_scope | none to dynamic |
| Ab19Register | *uint16 | register | absent to explicit zero |

All eleven axes match independently. Optional absent and explicit zero differ
for Secondary, Operation, Group and Register. There is no wildcard, nearest-key,
cross-family, variant, direction, field or alternative fallback. An exact key
with each axis changed alone remains a distinct identity even when all other
axes agree. The single-axis controls above describe distinct keys, not
additional production rows or supported mappings.

Every call returns independent deep byte copies. Mutating any returned row or
entries buffer cannot affect a later result from either function. Returned JSON
is metadata, not an active decoder or an instruction to transmit. Copy isolation
and exact matching are local API behavior; they do not qualify native behavior.

## Raw state and admission

Raw form is retained, including short and extra abstract structures. The raw
8000 replacement is selected before signed scaling for each OP0F temperature;
replacement does not assert unavailability. The pressure default 255.0 remains
in conflict with 0..25.5 bar. Inverse-actuator data has no complement algorithm.
CO2 FFFF remains 65535 ppm. OP11 and OP12 each retain literal positive B5/12/0C
with selector conflict, decoder selection false and acceptance false. No physical
reply selection follows from a field width, a synthetic example or an exact key.

Partial last-known-good state and raw evidence must survive an unrecognized,
short, extra or conflicting observation. Unknown fields cannot erase independently
known values. Admission fails closed: candidates grant no transmit route,
scan-default change, active executor or automatic native qualification.
Existing catalog/provider APIs and routability remain unchanged. eBUS MCP
compatibility and GraphQL parity remain unchanged: neither surface gains a
capability or promoted support claim from these rows. No pending API or shared
registration is imported by this documentation.

## Companion order and validation boundary

[AK09 registry companion](https://github.com/Project-Helianthus/helianthus-ebusreg/pull/366)
is merged and precedes this page in the same delivery cycle. Dependency direction
is page to registry; the registry has no dependency back to this page. Merge does
not reinterpret a candidate as native qualification.

The [synthetic contract tests](../tests/test_ak10_b512_heatpump_io.py) independently
check the finite native tables, cases and this API declaration. Their key-axis
controls vary documentation contracts independently, including absent versus
zero; they do not execute the companion Go package or establish its runtime
behavior. Copy and error behavior require the registry's independent runtime
checks as well. No device or physical delivery is qualified by these tests.
Nothing is stable before Helianthus 1.0.
