# B524 energy roles: finite library contract

The [native supplement](../protocols/vaillant/ebus-b524-energy-roles.md) defines
the five Hypothesis targets first. This page specifies only a finite metadata
interface, not a runtime decoder or duplicate catalog.

```go
func Ab95Entries() ([]Ab95Entry, error)
func Ab95Lookup(ab95Key Ab95Key) (Ab95Entry, bool, error)
```

These are exactly the two entry points, using Ab95Entry and Ab95Key.
Every new declaration and field uses the ab95 or Ab95 prefix; semantic labels
remain data. No generic schema or provider API is introduced.

## Exact key identity

| Field | Type | Identity rule |
| --- | --- | --- |
| Ab95Family | string | exact family |
| Ab95Variant | string | exact variant |
| Ab95Primary | uint8 | exact primary service |
| Ab95Secondary | *uint8 | absent differs from explicit zero |
| Ab95Operation | *uint8 | opcode; absent differs from explicit zero |
| Ab95Direction | *string | absent differs from supplied direction |
| Ab95Field | string | exact field |
| Ab95Group | *uint8 | absent differs from explicit zero |
| Ab95RequestedInstance | *uint8 | absent differs from explicit zero |
| Ab95Register | *uint16 | full register; absent differs from explicit zero |
| Ab95CommandRole | *string | absent differs from supplied command role |

No axis is a wildcard. B524 retains opcode, group, requested instance, full
register and command role separately. Readback instance 00 never substitutes
for command instance FF; OP06 never aliases OP02. Changing any one key axis
must not inherit the original entry, including family, variant and direction.
Codec is entry metadata, independent of both field and command role.

## Grades and unknown metadata

Ab95Entry retains Ab95Key, Ab95Grade, Ab95Codec, Ab95WidthBytes,
Ab95Raw, Ab95UnknownMetadata and Ab95PhysicalQualification as independent
properties. Optional numeric metadata also uses pointers: absence differs
from explicit zero. The five target mappings remain Hypothesis. Control codec
and width are absent; three scalars declare binary32 and four bytes, activation
declares one byte. Binary32 order, offsets, units, control enumeration and
response forms remain Unknown. No neighboring entry supplies missing facts.

Proven describes only the limitation that metadata lookup cannot establish
applied state or installed capability. Ab95Grade remains independent of
Ab95PhysicalQualification, raw evidence and unknown metadata. Qualification,
applied state and installed capability remain Unknown. Metadata presence does
not authorize execution or prove a physical result.

## Ownership and errors

Every successful Ab95Entries call and successful Ab95Lookup result returns
independently owned nested data, including key pointers, optional scalar
pointers, raw byte slices, unknown-metadata maps and all nested contents.
Mutating one result cannot affect another held result or any subsequent call.

A well-formed missing key returns Ab95Entry{}, false, nil. Invalid embedded
data returns an error and no successful result: Ab95Entries yields no usable
collection; Ab95Lookup returns Ab95Entry{}, false, error. Malformed syntax,
trailing data, unknown fields, empty data, invalid entries and duplicate exact
keys fail closed; a partial catalog is never admitted after failure.

Failed admission must preserve the caller's independently owned prior
last-known-good partial state and raw values, without marking them fresh or
admitting failed data. Unknown semantics do not erase retained raw evidence.
No command builder or writer is included. Existing eBUS MCP compatibility and
GraphQL parity remain requirements; this contract adds no surface to either.
Nothing is stable before 1.0; no new major or experimental namespace is added.
No authorization gate is introduced before 0.9; roadmap wording remains 0.11.
