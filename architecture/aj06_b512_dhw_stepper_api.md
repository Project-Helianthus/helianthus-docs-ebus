# Bounded B512 library contract

Refs Project-Helianthus/helianthus-docs-ebus#887 and
Project-Helianthus/helianthus-docs-ebus#736 (partial parent slice).

The public native contract comes first:
[B512 candidate supplement](../protocols/vaillant/ebus-b512-dhw-stepper.md).
The companion finite library surface is exactly:

```go
func Ab97Entries() ([]Ab97Entry, error)
func Ab97Lookup(ab97Key Ab97Key) (Ab97Entry, bool, error)
```

No generic schema or provider API is introduced. This is a pre-1.0 contract with
no stability promise, no new major namespace and no experimental namespace.

## Identity

All declarations and fields use the `ab97` or `Ab97` prefix; semantic labels
remain data. `Ab97Key` retains these independent axes:

| Field | Type | Meaning |
|---|---|---|
| Ab97Family | string | family |
| Ab97Variant | string | variant; B512 and B51214 remain distinct |
| Ab97Primary | uint8 | primary |
| Ab97Secondary | *uint8 | optional secondary |
| Ab97Operation | *uint8 | optional operation |
| Ab97Direction | string | request or positive |
| Ab97Field | string | field |
| Ab97Group | *uint8 | optional B524 group |
| Ab97RequestedInstance | *uint8 | optional B524 requested instance |
| Ab97Register | *uint16 | optional B524 register |
| Ab97CommandRole | *string | optional B524 command role |

Optional numeric axes use pointers: absent differs from explicit zero. An absent
operation also differs from 0A and 14. B524 retains operation, group, requested
instance, register and command role independently; matching numbers do not merge
namespaces. No B524 entries or native B524 facts are added by this slice.

## Ownership and errors

`Ab97Entries` returns independently owned entries and nested data on every call.
A successful `Ab97Lookup` returns independently owned nested data, including key
pointers, metadata pointers, value maps and unknown slices. Mutating one returned
entry, its nested data or its key cannot alter another result or embedded data.

A well-formed missing key returns `Ab97Entry{}, false, nil`.
Invalid embedded data returns an error and no successful result:
`Ab97Entries` returns `nil, error`; `Ab97Lookup` returns
`Ab97Entry{}, false, error`. Admission fails closed; malformed data does not
become an empty successful catalog or a missing-key success.

## Grade and preservation boundaries

Entry grade, label grade, qualification, raw policy and unknown metadata remain
independent properties. Here entry grade is Hypothesis, qualification is Unknown;
missing condition labels and actual movement remain Unknown. Proven requires
native evidence; arithmetic checks do not supply it. Formal modulation Celsius
remains a conflict, and OP03 stays raw without a temperature conversion.

Preserve raw bytes, reserved bits, unmapped values and independent partial
last-known-good fields. Missing or malformed fields do not overwrite independent
known fields, and defaults do not manufacture observed values. Candidate metadata
alone cannot admit control execution or establish support. Stepper release does
not prove movement. Existing eBUS MCP compatibility and GraphQL parity remain
requirements; this finite metadata contract adds no endpoint or execution policy.
