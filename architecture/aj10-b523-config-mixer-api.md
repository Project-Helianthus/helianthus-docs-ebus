# B523 configuration and mixer finite library contract

The [native supplement](../protocols/vaillant/ebus-b523-config-mixer.md) owns the
candidate wire facts. This page specifies a finite pre-1.0 library contract;
it introduces no runtime decoder, generic schema or provider API. Nothing is
stable before 1.0. This documentation does not claim an implemented library.

## Signatures

```go
Ab99Entries() ([]Ab99Entry, error)
Ab99Lookup(key Ab99Key) (Ab99Entry, bool, error)
```

These are exactly the two exported operations. The entry and key types are
Ab99Entry and Ab99Key. Every new declaration and field begins with ab99 or
Ab99; semantic labels remain data, never generated declarations.

## Key axes

| Field | Type | Identity meaning |
| --- | --- | --- |
| Ab99Family | string | family |
| Ab99Variant | string | variant |
| Ab99Primary | *uint8 | primary |
| Ab99Secondary | *uint8 | secondary |
| Ab99Operation | *uint8 | operation |
| Ab99Direction | string | direction |
| Ab99Field | string | field |
| Ab99Group | *uint8 | B524 group |
| Ab99RequestedInstance | *uint8 | B524 requested instance |
| Ab99Register | *uint16 | B524 register |
| Ab99CommandRole | string | B524 command role |

Ab99Key retains every axis. Optional numeric axes use pointers: nil is absent,
which differs from an explicit zero. Equality compares pointer presence and
pointed-to values, never pointer addresses. B524 operation namespaces remain
distinct, including OP02 and OP06; requested instance is not a returned instance.
No field, variant, direction or command role may collapse into another key.

## Entry boundaries

Ab99Entry has Ab99Key, Ab99Grade, Ab99Raw, Ab99Unknown and
Ab99Qualification fields. Ab99Grade is independent of raw/unknown metadata and
Ab99Qualification. Candidate declarations remain Hypothesis; Proven arithmetic
never upgrades native claims. Missing physical facts stay Unknown. Raw bytes,
reserved values, competing interpretations and partial last-known-good state
remain independently represented; absence does not become zero or a default.

## Ownership and errors

Ab99Entries and successful Ab99Lookup return independently owned nested data:
copy slices, maps, nested collections, raw bytes and key pointers recursively.
Mutating a returned entry, nested value or pointer cannot affect stored data,
another returned entry or any later call. Lookup and enumeration do not alias
each other, including across repeated calls.

A well-formed missing key returns an empty Ab99Entry, false and nil error.
Invalid embedded data returns an error and no successful result: Ab99Entries
returns nil entries and an error; Ab99Lookup returns an empty Ab99Entry, false
and an error. Validate embedded data before admitting any result, even for a
missing lookup. Never return a partially valid catalog on malformed data.
Raw/partial evidence may survive separately without becoming an admitted entry.

The same finite evidence, Unknown states and absent/zero identity must remain
visible through eBUS MCP compatibility and GraphQL parity. No control execution,
active request, polling default or authorization gate is introduced here.
