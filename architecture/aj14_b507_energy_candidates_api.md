# B507 finite library contract

The public [native supplement](../protocols/vaillant/ebus-b507-energy-candidates.md)
is the first authority for the bounded candidate facts. The merged AJ13
companion in `helianthus-ebusreg` supplies the finite library interface below.
This page documents that contract; it introduces no decoder, duplicate catalog,
generic schema or provider API.

```go
func Ab13Entries() ([]Ab13Entry, error)
func Ab13Lookup(ab13Key Ab13Key) (Ab13Entry, bool, error)
```

These are exactly the two entry points. All new declarations and fields use
`ab13` or `Ab13` prefixes; semantic labels remain data.

## Exact identity

`Ab13Key` retains every axis without wildcarding absent values:

| Field | Type | Identity rule |
|---|---|---|
| Ab13Family | string | exact family |
| Ab13Variant | string | exact variant |
| Ab13Primary | uint8 | exact primary service |
| Ab13Secondary | *uint8 | absent differs from explicit zero |
| Ab13Operation | *uint8 | absent differs from explicit zero |
| Ab13Direction | *string | absent differs from a supplied direction |
| Ab13Field | string | exact field |
| Ab13Group | *uint8 | B524 group; absent differs from explicit zero |
| Ab13RequestedInstance | *uint8 | B524 requested instance; absent differs from explicit zero |
| Ab13Register | *uint16 | B524 full register; absent differs from explicit zero |
| Ab13CommandRole | *string | B524 command role; absent differs from a supplied role |

The B507 entries retain absent direction and absent B524 axes; they do not
invent coordinates. B524 operation, group, requested instance, register and
command role must remain distinct, including separate OP02 and OP06 identities.

## Grades, ownership and errors

`Ab13Entry` keeps `Ab13Grade` independent of `Ab13MetadataPresence`,
`Ab13PhysicalQualification`, `Ab13Invocation`, raw preservation and unknown
metadata. Proven metadata presence means the library contains the metadata;
it does not prove a native meaning or physical support. Capacity, cost,
and temperature remain Hypothesis. OP08, OP09 and OP0B are omitted from this
bounded B507 entry set; no preference fields or sentinel mappings are supplied.
Physical qualification and invocation remain Unknown. Absent coordinates,
converters, references and widths must not become fabricated defaults.

Every successful `Ab13Entries` call returns independently owned nested data.
Every successful `Ab13Lookup` result also owns its nested storage independently
of all other results, including results still held by the caller. This includes
key pointers, optional scalar pointers, slices, maps and their nested contents.
Mutating any result must leave subsequent calls and other held results intact.

A well-formed missing key returns `Ab13Entry{}, false, nil`. Invalid embedded
data returns an error: entries yield no usable collection, and lookup returns
`Ab13Entry{}, false, error`. Malformed syntax, trailing data, unknown fields,
empty data, invalid entries and duplicate exact keys must fail closed. A failed
read must not replace a caller's previously retained, independently owned
last-known-good result. That retained partial knowledge grants no admission or
execution permission; admission on failed data stays closed.

Raw values and partial states survive unknown semantics independently of grade.
The library's labels do not authorize writes or select active requests.
This bounded contract adds no eBUS MCP or GraphQL surface; existing compatibility
and parity remain requirements for any later integration. Nothing here is stable
before 1.0; no new major or experimental namespace is introduced, no authorization
gate is introduced before 0.9, and roadmap wording remains 0.11.
