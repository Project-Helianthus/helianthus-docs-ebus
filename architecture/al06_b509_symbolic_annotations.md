# Qualified B509 symbolic annotations

This finite library contract is the residual B509 correspondence area for
[issue #905](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/905),
a partial child of [#736](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/736).
The public [native correspondence contract](../protocols/vaillant/ebus-vaillant-B509.md#register-name-correspondence-fixture)
and its [raw correspondence fixture](../protocols/vaillant/fixtures/b509-register-name-correspondence.csv)
come first. Their class, operation and complete selector identities remain intact.
This architecture page specifies annotation representation, not additional wire facts.

The catalog prerequisite, helianthus-ebusreg PR #342, must merge before this page.
The supplied dependency snapshot records it as merged. Its
[catalog implementation](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/main/catalog/vaillant/ab40_b509_symbolic_annotations.go),
[catalog tests](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/main/catalog/vaillant/ab40_b509_symbolic_annotations_test.go)
and [catalog data](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/main/catalog/vaillant/data/ab40_b509_symbolic_annotations.json)
are companion evidence for implementation shape. No cross-repository runtime import
is introduced. Nothing here is stable before Helianthus 1.0.

## API and exact identity

`Ab40Entries() (json.RawMessage, error)` returns the complete raw JSON array after
validating the source. `Ab40Lookup(Ab40Key) (json.RawMessage, bool, error)` returns
one raw JSON row for an exact key. Each successful call returns independent memory:
mutating one result must not alter another result or future calls.

The `Ab40Key` JSON fields below are all identity axes. The Go field names are
`Ab40` followed by the corresponding capitalized JSON name (`Ab40InstanceScope`
for `instance_scope`). Required strings use literal `none` when inapplicable;
`primary` is a required uint8. `secondary`, `operation` and `group` are optional
uint8 pointers; `register` is an optional uint16 pointer; `selector` is an optional
string pointer. Missing optional fields differ from present zero values. Explicit
null optional fields are invalid source data. This finite catalog's direction is
literal `none`: operation labels do not establish a physical traffic direction.

Class `any` is a literal class-neutral annotation, not a wildcard. A selectorless
OP0D or OP0E row describes an operation; it does not select address zero, construct
requests or admit writes. OP0D `0x1800` is a literal dictionary token. OP54
`54 02 00 0D 0A` is a complete opaque byte-sequence token: changing any byte must
miss. Keep its prefix and full length; do not project it into a u16 address or
construct a packet. A row with only an opaque selector has no register identity.

## Errors, absence and retention

A successful lookup yields `(copied row, true, nil)`; a miss yields
`(nil, false, nil)`. Invalid source yields `(nil, false, error)` for Lookup and
`(nil, error)` for Entries. Invalid JSON, a non-array or null source, invalid key
field types or ranges, missing required axes, empty required strings, explicit
null optional axes and duplicate exact keys fail source validation. An empty
array is valid. Validation covers source structure and identity; it does not
certify annotation semantics or native support.

Missing name or unit stays absent. An explicit `unresolved: true` stays explicit;
`false` does not promote a candidate interpretation. Non-key metadata and raw
fields survive without becoming identity axes. Retain raw bytes and independent
useful fields on partial interpretation failure; do not manufacture missing
names, units or register numbers. Invalid source returns no partial catalog.
These return semantics add no cache or last-known-good replacement policy.
Admission remains fail closed: this library creates no transmit route,
automatic qualification, converter or write permission.

## Grades, finite bounds and controls

**Proven** describes the finite representation contract: 108 rows, including
78 OP0D, one OP0E and 29 OP54 rows, all direction-qualified by `none`. Class,
operation, optional selector, canonical name, optional unit and unresolved flag
remain independent. This is the finite correspondence area, not a complete
family catalog or exhaustive support claim.

**Hypothesis** describes symbolic labels and units as candidate annotations.
No label determines signedness, scale, field extent or native effect. A unit
is never a converter: neither temperature nor power receives an automatic codec.
**Unknown** remains the physical qualification and native effect. Presence,
freshness and execution are separate questions; row presence proves none of them.
A generic dictionary may be reused only after exact mapping agreement; boiler
and heat-pump classes remain distinct. eBUS MCP compatibility and GraphQL parity
are constraints on later integration; neither is established by this page.

The [small synthetic example set](fixtures/al06_b509_symbolic_annotations.json)
keeps boiler OP0D `0x1800` flow_temperature separate from same-number keys with
another class or operation. Boiler and heat-pump OP0D `0xBB00` deliberately carry
different names. The two selectorless operation controls retain unresolved flags;
the OP54 controls retain full opaque tokens with no invented register. The
synthetic absence probe retains missing name/unit and raw `[0, 255]` independently.
It is a retention control, not another catalog row or a device observation.

The following machine-readable declaration is checked against independent
expectations by the scoped standard-library test. The test checks this page,
examples and a synthetic exact-key model without importing the companion
repository. It checks declared cardinalities, not a second full dictionary.
Passing it establishes no companion code result, native effect, physical
qualification, runtime smoke result or full parity; each requires its own checks.

```json
{
  "api": {
    "entries": "Ab40Entries() (json.RawMessage, error)",
    "lookup": "Ab40Lookup(Ab40Key) (json.RawMessage, bool, error)",
    "key_type": "Ab40Key",
    "hit": [
      "copied row",
      true,
      null
    ],
    "miss": [
      null,
      false,
      null
    ],
    "invalid_source": [
      null,
      false,
      "error"
    ],
    "entries_invalid_source": [
      null,
      "error"
    ],
    "independent_returned_memory": true
  },
  "identity": {
    "required": [
      "family",
      "variant",
      "primary",
      "direction",
      "field",
      "alternative",
      "instance_scope",
      "class"
    ],
    "optional": [
      "secondary",
      "operation",
      "group",
      "register",
      "selector"
    ],
    "matching": "exact",
    "any": "literal",
    "selector_type": "optional string",
    "absent_equals_zero": false,
    "op54": "complete opaque token"
  },
  "catalog": {
    "rows": 108,
    "direction_operation_counts": {
      "none|0D": 78,
      "none|0E": 1,
      "none|54": 29
    }
  },
  "interpretation": {
    "representation_grade": "Proven",
    "grade": "Hypothesis",
    "physical_qualification": "Unknown",
    "native_effect": "Unknown",
    "signedness": "Unknown",
    "width_bytes": null,
    "scale": null,
    "automatic_codec": false,
    "unit_is_converter": false
  },
  "admission": {
    "construct_request": false,
    "automatic_qualification": false,
    "write_admission": false,
    "raw_fallback": "preserve-raw-bytes"
  }
}
```
