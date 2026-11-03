# B50F status spans: finite library contract

Refs: helianthus-docs-ebus#858; partial slice of helianthus-docs-ebus#736.
The [native supplement](../protocols/vaillant/ebus-b50f-status-spans.md) owns the
candidate wire facts. This page specifies the bounded pre-1.0 library interface;
its behavior does not qualify those facts physically. Nothing is stable before
1.0. No new major or experimental namespace is introduced.

The only exported functions in this slice are:

```go
Ab12Entries() ([]Ab12Entry, error)
Ab12Lookup(key Ab12Key) (Ab12Entry, bool, error)
```

`Ab12Entry` and `Ab12Key` are the entry and identity types. Every new declaration
and field has an `ab12` or `Ab12` prefix; semantic labels remain data. There is no
runtime decoder, generic schema or provider API in this documentation slice.

## Identity

All of these axes participate in exact equality. Optional fields use pointers;
absence differs from an explicit zero, and absent strings differ from empty
strings. Values are compared, never pointer addresses. A B50F key does not gain
B524 semantics merely because a numeric selector matches.

| Field | Type | Meaning |
| --- | --- | --- |
| Ab12Family | string | Device family |
| Ab12Variant | string | Native variant |
| Ab12Primary | byte | Primary selector |
| Ab12Secondary | *byte | Optional secondary selector |
| Ab12Operation | *byte | Optional operation |
| Ab12Direction | *string | Optional direction |
| Ab12Field | string | Independent field identity |
| Ab12Group | *byte | B524 group |
| Ab12RequestedInstance | *byte | B524 requested instance |
| Ab12Register | *uint16 | B524 register |
| Ab12CommandRole | *string | B524 command role |

B524 identity preserves operation, group, requested instance, register and
command role together; OP=0x02 and OP=0x06 never collapse. These key axes add no
B524 records or claims to this B50F slice. The companion library's `request`
direction key is catalog identity, not proof of native direction; native direction
remains Unknown under the supplied evidence.

## Entry boundaries

`Ab12Entry.Ab12Key` retains the complete identity. `Ab12Grade` is Hypothesis for
each of the eight spans, independently of `Ab12Qualification` (Unknown),
`Ab12CoordinateGrade` (Unknown), and `Ab12Unknown`. `Ab12Position` is absent and
`Ab12WidthBits` is eight. The six containers have their own `Ab12AllocatedMask`
and `Ab12ReservedMask`; the two raw bytes have absent masks and no `Ab12Bits`.
The nested bit data retains `Ab12Bit`, `Ab12Label`, `Ab12Category` and
`Ab12Reserved`. An absent label remains absent even when a category is known.
`Ab12RawFallback` requires full independent raw-byte preservation, including
reserved bits, without physical inference. Unknown names and coordinates must
not be filled from demand or integrity declarations. Grade promotion requires
new native evidence; a library result alone supplies none.

## Ownership and failure

`Ab12Entries` and every successful `Ab12Lookup` return independently owned nested
data: the list, entries, key pointers, masks, width/position pointers, bit slices,
label/category pointers and unknown-metadata slices share no mutable storage
with another result or retained library data. Mutating a returned value cannot
alter a later result or another entry. Pointer addresses do not define identity.

A well-formed missing key returns an empty `Ab12Entry`, false and no error.
Invalid embedded data returns an error: `Ab12Entries` returns no entries and
`Ab12Lookup` returns an empty entry and false. Admission fails closed for
malformed data, incomplete or duplicate identities, invalid partitions and
invalid grade/unknown metadata; malformed data must not become a missing-key
success or a partial successful catalog. No new authorization gate is added.

Raw/partial observations and last-known-good state remain independently retained;
a missing current byte is not zero and does not erase earlier evidence. Such
observations do not relax catalog admission. This contract adds no control
execution or physical qualification, and changes no eBUS MCP compatibility or
GraphQL parity contract. Runtime, transport and physical qualification require
separate evidence; synthetic documentation checks cannot establish them.
