# Unscoped B524 hint view

This is the finite application contract for AM10, with companion AM09. It is
pre-1.0 work, with no stability promise or new experimental namespace. It adds
no native protocol claim. The public [B524 contract](../protocols/vaillant/ebus-vaillant-B524.md)
owns wire identity and partial response handling; the [register map](../protocols/vaillant/ebus-vaillant-B524-register-map.md)
keeps historical range hints distinct from complete parameter descriptions.
The native identity retains `(opcode, group, instance, register)`. Omitting
instance from the hint key is a limitation of the historic implementation
table, never permission to collapse native identities.

## Evidence and limits

**Proven (supplied implementation contract):** `b524StaticConstraintsCatalog`
has 46 OP02 entries keyed by opcode, group and register, each with `Type`,
`Min`, `Max`, `Step`. It has no instance, family, software, hardware or API
identity. OP02/GG00/RR0001 is deliberately absent. `lookupB524Constraint`
already distinguishes opcode and furnishes no OP06 hints. These facts describe
software structure, not native evidence or a qualified controller profile.

**Hypothesis:** historic numeric ranges are candidate hints only; universal
numeric interpretation is unsupported. **Unknown:** exact family applicability,
physical support, fresh presence, freshness, execution, effects, persistence
and delivery. Evidence grade and qualification are separate: the table's
existence is Proven while every returned hint has applicability grade Unknown
and `qualified=false`. No family, variant or instance supplied by a caller can
upgrade it. No live observation is contained in this page or its examples.

## Pure exported view

The companion exposes `ListB524UnscopedHints()` and
`LookupB524UnscopedHint(opcode, group, register)`. These are proposed exported
view names for this contract; this documentation does not implement or verify
the production wrapper. Lookup accepts a byte opcode, byte group and unsigned
16-bit register. The view reads the existing immutable table, with no second
embedded catalog and no change to the table or its consumers.

Enumeration returns exactly 46 independent `AM09B524UnscopedHint` values,
sorted numerically ascending by `(opcode, group, register)`, independent of map
iteration order. Each value contains exactly the following fields:

| Field | Required value or meaning |
| --- | --- |
| opcode | Original opcode byte |
| group | Original group byte |
| register | Original unsigned 16-bit register |
| status | `unscoped_hint` |
| qualified | `false` |
| grade | `Unknown` (applicability) |
| Type | Original type hint |
| Min | Original minimum hint |
| Max | Original maximum hint |
| Step | Original step hint |

Lookup uses all three key components exactly. A hit returns a fresh value of
that distinct ticket-prefixed type; a miss returns no hint (`null` in examples,
an absent optional value in the typed API). Neither a hit nor a miss has the
shape or success status of an exact controller bound. OP06 always misses,
including every corresponding OP02 key. OP02/GG00/RR0001 always misses. Other
absent keys miss, without fallback. Register zero and group zero are explicit
values, not missing fields or wildcards; the all-zero key is a well-formed miss.

Returned collections and values own their storage. Mutating one result,
including its numeric fields or key, cannot change a later lookup, enumeration
or the existing table. The view must not call `LookupB524Bound`, merge exact
profiles with hints, validate edit inputs, or change request routing. It adds
no transmit route, active executor, scan default or automatic qualification.
Existing eBUS MCP compatibility and GraphQL parity remain unchanged; no new
transport contract is established here.

## Synthetic example package

The [example package](fixtures/am10_b524_unscoped_hints.json) contains the
three independently specified controls below, not a reconstructed 46-entry
catalog. Numbers are candidate hint properties, with no asserted unit or
wire decoder. Values are preserved without normalization.

| Opcode | Group | Register | Type | Min | Max | Step |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 0 | 2 | f32_range | -26 | 10 | 1 |
| 2 | 0 | 4 | u16_range | 0 | 300 | 10 |
| 2 | 3 | 2 | f32_range | 15 | 30 | 0.5 |

Every control returns `status=unscoped_hint`, `qualified=false`, `grade=Unknown`.
The package also includes the deliberate OP02 absence and each control's OP06
counterpart, all returning no hint. The following normative case declarations
are checked against the examples and the owned validation seam:

```json
{
  "valid": "unscoped_hint",
  "op06": "no_hint",
  "absent_register": "no_hint",
  "all_zero_key": "no_hint",
  "missing_key_field": "malformed",
  "extra_key_field": "malformed",
  "invalid_key_type_or_width": "malformed",
  "duplicate_key": "malformed",
  "partial_hint": "malformed",
  "unknown_type": "malformed",
  "exact_bound_or_identity_fields": "malformed",
  "storage": "independent"
}
```

The owned Python seam validates synthetic package structure, not edit values
or native data. It rejects missing, extra, boolean, noninteger, negative and
over-width key components; missing differs from explicit zero. Each caller
context axis (family, variant, instance, software, hardware, API identity,
operation, direction, selector and field) is an extra field, rejected rather
than attached to or used to specialize a hint. No direction or operation
semantics are inferred from this rejection. Unknown opcodes and unknown
well-formed keys miss. Missing numeric fields, nonfinite numbers, unknown
types, duplicate keys, exact-bound fields and qualified results invalidate
the synthetic package. A malformed package is not admitted to a view. Its
raw source and prior independently useful fields remain available separately.

The partial example preserves synthetic raw payload `0000020000`, prior
`independent_field=0` and a `malformed` hint diagnostic with `qualified=false`.
These bytes are opaque here: there is no decode or fresh-presence claim.
A failed hint interpretation does not erase raw bytes or last-known-good
fields, and neither retained state nor a hint authorizes execution.

## Verification boundary

The [focused tests](../tests/test_am10_b524_unscoped_hints.py) independently
check the three numeric controls with integer and IEEE float arithmetic,
page/example agreement, negative cases and mutable-memory isolation. A
separate 46-key synthetic catalog stresses enumeration cardinality, exact
lookup and sorting; its invented keys are not production evidence.

Companion AM09 must exercise all 46 actual keys against the existing table,
including each OP06 counterpart, and demonstrate immutable source storage,
no exact-bound calls or merging, and no routing changes. That production
wrapper and table are absent from this documentation checkout; this suite
cannot establish production parity. Changes to an unowned production table
are reasoned mutation mappings only. Focused checks establish only the page
and synthetic software contract. Full repository CI, Gate D, publication
checks, independent committed-change review and applicable transport
classification remain later ship requirements; automatic Gate D discovery of
this test is not claimed. AM09 holds its merge for this page; the page has no
code dependency. Refs #863 and #736; this partial child leaves the parent open.
