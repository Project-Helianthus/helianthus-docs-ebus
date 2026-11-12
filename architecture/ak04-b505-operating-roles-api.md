# B505 operating-role library contract

Refs Project-Helianthus/helianthus-docs-ebus#1013 and
Project-Helianthus/helianthus-docs-ebus#736 (partial parent slice).

Read the public native [operating-role supplement](../protocols/vaillant/ebus-b505-operating-roles.md)
first. Its finite role table and [synthetic declarations](../protocols/vaillant/fixtures/ak04_b505_operating_roles.json)
remain Hypothesis; qualification is Unknown. The following is the **Proven local
API contract**, not proof of native behavior or of implementation verification.

## Finite surface and exact identity

Package `vaillant` exposes exactly these companion functions:

```go
func Ab16Entries() (json.RawMessage, error)
func Ab16Lookup(Ab16Key) (json.RawMessage, bool, error)
```

`Ab16Entries` returns a JSON array. `Ab16Lookup` returns exactly one whole row,
including its complete identity, stated fields/relations, candidate grade,
explicit Unknown metadata and retained raw form. Production IDs and exported
fields are ticket-prefixed. The finite new area is precisely the 54
operation/field/role associations in the native supplement; no other catalogue
area is implied. This page specifies that companion surface without importing
a pending API or changing shared registration.

| Field | Type | Native identity axis |
| --- | --- | --- |
| Ab16Family | string | family |
| Ab16Variant | string | variant |
| Ab16Primary | uint8 | primary |
| Ab16Secondary | *uint8 | secondary |
| Ab16Operation | *uint8 | operation |
| Ab16Direction | string | direction |
| Ab16Field | string | field |
| Ab16Alternative | string | alternative |
| Ab16Group | *uint8 | group |
| Ab16InstanceScope | string | instance_scope |
| Ab16Register | *uint16 | register |

Match all eleven axes. No wildcard, nearest-key, cross-family, variant,
direction, field or alternative fallback is permitted. Optional absent and
explicit zero differ for Secondary, Operation, Group and Register. String axes
that do not apply use the explicit `none` token. Instance scope is a string,
for example `00` or `dynamic`; these are identity examples, not evidence of
numeric instance support. This finite B505 table uses `none` for instance scope.

These synthetic exact-key vectors use the first native row as the admitted
baseline. Each independent miss changes only the named axis. They specify
matching requirements; they are not records of a runtime lookup.

| Field | Baseline | Independent miss |
| --- | --- | --- |
| Ab16Family | "vaillant" | "synthetic_family" |
| Ab16Variant | "B505" | "synthetic_variant" |
| Ab16Primary | 181 | 180 |
| Ab16Secondary | 5 | 0 |
| Ab16Operation | 90 | 0 |
| Ab16Direction | "request" | "response" |
| Ab16Field | "room_setpoint" | "synthetic_field" |
| Ab16Alternative | "room" | "synthetic_role" |
| Ab16Group | null | 0 |
| Ab16InstanceScope | "none" | "dynamic" |
| Ab16Register | null | 0 |

For each optional numeric axis independently, an otherwise identical key with
that axis absent differs from the same key with explicit zero. An admitted
absent control matches itself; an admitted zero control matches itself, but
neither matches the other. A missing exact key returns `nil, false, nil`.

The independent optional-axis controls are explicit:

| Field | Absent control | Zero control | Cross-match |
| --- | --- | --- | --- |
| Ab16Secondary | null | 0 | false |
| Ab16Operation | null | 0 | false |
| Ab16Group | null | 0 | false |
| Ab16Register | null | 0 | false |

Each control is admitted in its own synthetic catalogue, with every other axis
held equal. These controls do not add operations or instances to the native area.

## Ownership and fail-closed errors

Embed the companion's owned JSON in its owned Go file; validate identity
uniqueness before returning data. Invalid embedded JSON and duplicate complete
keys are errors, not missing-key results. Independent keys may share operation
numbers. No second general family schema, provider API, transmit route or
routability change is introduced. Existing catalog/provider APIs remain
unchanged; preserve an existing package name, otherwise use `vaillant`.

| Condition | Ab16Entries result | Ab16Lookup result |
| --- | --- | --- |
| valid data / exact match | JSON array, nil | whole JSON row, true, nil |
| valid data / missing exact key | JSON array, nil | nil, false, nil |
| invalid embedded JSON | nil, error | nil, false, error |
| duplicate complete key | nil, error | nil, false, error |

Every call returns independent deep byte copies. Mutating any returned row or
entries buffer cannot affect a later result, including calls through the other
function. No embedded buffer, nested slice or earlier result is shared.
Admission fails closed; invalid data cannot become an empty successful array or
reuse a previously successful lookup as if it matched. Raw form and independent
partial last-known-good values survive unresolved semantic updates; unknown
fields do not erase unrelated known fields or manufacture successful admission.

## Grades, parity and delivery order

Hypothesis is a candidate grade, independent of Unknown qualification. Raw
replacement codes for OP5A, OP3D and OP41 remain Unknown. Explicit replacement
selection precedes numeric conversion; numeric candidates acquire no new scale.
Only OP17's stated semantic addition is supplied. Unprovided encodings, offsets,
durations, other formulas and enforcement remain Unknown. Reset requests do not
establish acceptance or persistence; eligibility does not establish execution.
Native support, physical effects, persistence and delivery remain Unknown.

Preserve eBUS MCP compatibility and GraphQL parity. This finite metadata
contract changes no endpoint, active executor, scan default or automatic native
qualification. Nothing is stable before Helianthus 1.0; no new major or
experimental namespace is introduced. Authorization has no gate before 0.9;
any authorization roadmap wording is 0.11.

AK03 must merge before this page. Both belong to the same delivery cycle;
there is no dependency from the registry back to this page. Their merge does
not qualify native behavior. The documentation checks verify declarations,
synthetic cases and this exact contract; runtime uniqueness, invalid-JSON errors
and defensive-copy behavior require separate companion implementation evidence.
