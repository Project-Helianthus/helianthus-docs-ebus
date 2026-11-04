# Finite B503 library contract

The [native supplement](../protocols/vaillant/ebus-b503-text-categories.md)
is the source contract for the finite candidate fields. This page specifies a
bounded pre-1.0 library interface; it supplies no runtime implementation or
generic schema. Nothing here is stable before 1.0.

## Signatures

```go
Ab96Entries() ([]Ab96Entry, error)
Ab96Lookup(key Ab96Key) (Ab96Entry, bool, error)
```

These are the only exposed functions. Every new declaration and field uses the
`Ab96` or `ab96` prefix; semantic labels remain data.

## Key axes

| type | field | representation |
| --- | --- | --- |
| Ab96Key | Ab96Family | string |
| Ab96Key | Ab96Variant | string |
| Ab96Key | Ab96Primary | *uint8 |
| Ab96Key | Ab96Secondary | *uint8 |
| Ab96Key | Ab96Operation | *uint8 |
| Ab96Key | Ab96Direction | string |
| Ab96Key | Ab96Field | string |
| Ab96Key | Ab96Group | *uint8 |
| Ab96Key | Ab96RequestedInstance | *uint8 |
| Ab96Key | Ab96Register | *uint16 |
| Ab96Key | Ab96CommandRole | string |

All axes participate in identity independently. Optional numeric pointers compare
by presence and pointed-to value, never pointer address: absent differs from
explicit zero. B524 additionally retains group, requested instance, register and
command role; equal register numbers never merge operation namespaces. Unprovided
axes stay absent or explicitly Unknown, without guessed selectors or coordinates.

## Entry boundaries and ownership

`Ab96Entry` retains `Ab96Key`, `Ab96Grade`, `Ab96Raw`, `Ab96Unknown` and
`Ab96Data` as independent properties. `Ab96Data` holds only the bounded native
field declarations; semantic labels are values, not declaration names.
`Ab96Grade` is Proven, Hypothesis or Unknown, independently of raw evidence,
unknown metadata and physical qualification. The native fields remain candidates;
synthetic success cannot promote a grade or establish physical success.

`Ab96Entries` and every successful `Ab96Lookup` return independently owned nested
data, including keys' numeric pointers, raw slices, unknown metadata and any
nested maps, slices or pointers in `Ab96Data`. Mutating one result must change
neither embedded data, another result, nor a later call. Entries within the same
returned list must not share mutable nested storage.

A well-formed missing key returns `Ab96Entry{}, false, nil`. Invalid embedded
data fails closed: `Ab96Entries` returns no entries and an error, and
`Ab96Lookup` returns `Ab96Entry{}, false` and an error, even for a key that would
otherwise match or be missing. No partially validated successful result escapes.
Raw/partial evidence remains available as evidence, without replacing a
last-known-good complete state. This finite contract introduces no provider API
and changes no eBUS MCP compatibility or GraphQL parity behavior.
