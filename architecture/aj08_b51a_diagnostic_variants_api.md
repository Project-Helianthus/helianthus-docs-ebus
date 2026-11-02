# B51A finite library contract

The native evidence boundary comes first: [B51A diagnostic variants](../protocols/vaillant/ebus-b51a-diagnostic-variants.md).
This page describes the bounded library interface; it introduces no runtime
decoder, generic schema, provider API or control operation. Nothing is stable
before 1.0.

```go
func Ab98Entries() ([]Ab98Entry, error)
func Ab98Lookup(ab98Key Ab98Key) (Ab98Entry, bool, error)
```

These are the only exposed functions in this contract. Every new declaration and
field uses the `ab98` or `Ab98` prefix; semantic labels remain data.

| Ab98Key field | Type | Identity meaning |
| --- | --- | --- |
| Ab98Family | string | device family |
| Ab98Variant | string | native variant |
| Ab98Primary | uint8 | primary service |
| Ab98Secondary | *uint8 | optional secondary service |
| Ab98Operation | *uint8 | optional operation |
| Ab98Direction | string | request or positive |
| Ab98Field | string | native field |
| Ab98Group | *uint8 | optional B524 group |
| Ab98RequestedInstance | *uint8 | optional B524 requested instance |
| Ab98Register | *uint16 | optional B524 register |
| Ab98CommandRole | *string | optional B524 command role |

Every axis participates in identity. Pointer absence differs from explicit zero
(and absent command role differs from an explicit empty string). B524 keeps
operation, group, requested instance, register and command role together;
matching register numbers do not merge operation namespaces. Role labels in the
companion catalog use responder for the native target role.

Ab98Entry carries Ab98Key and Ab98Grade independently of Ab98MetadataPresence,
Ab98PhysicalQualification, Ab98Invocation, Ab98Unknown and preserved raw metadata.
Native field interpretations and qualification/invocation remain Unknown.
The companion supplement and fixture withhold unsupported mappings; this interface
contract supplies no missing provenance and admits no native entries from them.
A grade is neither physical qualification nor write authorization. Optional
metadata is not fabricated from a label.

Ab98Entries and each successful Ab98Lookup return independently owned nested
data: pointers, maps, slices, labels, conditions, alternatives and their nested
fields cannot alias another result or future calls. Mutating one returned value
cannot alter a later listing or lookup. A well-formed missing key returns the
zero Ab98Entry, false and nil error. Invalid embedded data returns an error;
Ab98Entries returns no entries and Ab98Lookup returns the zero Ab98Entry and
false, never a successful partial admission. Raw partial evidence and previously
valid knowledge remain separate from admission of malformed data; rejection must
not fabricate a replacement value or erase last-known-good evidence.

This finite library contract requires no sibling checkout to understand it.
It adds no MCP or GraphQL surface; existing eBUS MCP compatibility and GraphQL
parity remain requirements for later consumers. Documentation checks do not
execute these Go functions or establish physical behavior.
