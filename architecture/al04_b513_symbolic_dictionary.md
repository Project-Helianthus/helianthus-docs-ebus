# B513 symbolic labels without value codecs

Refs #1028; partial child of #736, which remains open. The public
[native B513 OP04 contract](../protocols/vaillant/ebus-vaillant-B513.md#op04-get-symbolic-address-with-range-information)
and its [finite public catalog](../protocols/vaillant/fixtures/hem-b513-symbolic-addresses.csv)
are the protocol prerequisites. The catalog prerequisite must merge before this
page. Its merge state is not established here. No cross-repository runtime
import is added. Nothing is stable before Helianthus 1.0.

## Evidence and finite scope

**Hypothesis:** one finite B513 OP04 dictionary contains 1263 distinct raw u16
addresses with native labels. Each address has separate eBUS and PeBUS
candidate membership: 1263 per bus family, 2526 membership declarations in all,
not 2526 addresses. These declarations do not qualify physical equivalence,
variant applicability, direction applicability or a value codec. The dictionary
namespace is `b513-generic-candidate`; it never wildcard-matches a concrete
family variant. Literal native symbols are opaque dictionary labels; their
spelling does not assert support for an individual product. Narrative claims
apply only to device families whose applicability remains unresolved.

**Proven:** cardinality arithmetic, exact public-table correspondence and
synthetic representation controls can be checked locally. That grade does not
promote candidate interpretation. **Unknown:** physical qualification, presence,
freshness, execution, units, defaults and value types. Grade is independent of
those dimensions. There is no executable capability in any entry.

## Pure library contract

`Ab38Entries()` returns the finite list of 1263 address entries, not an iterable
address interval. Each entry retains family `B513`, opcode `04`, dictionary
namespace, numeric raw address, its two little-endian address bytes, native
label, both separately declared bus-family memberships, literal `unqualified`
variant and direction metadata, Hypothesis grade, null value codec and false
executable capability. These address bytes represent a u16 key; they are not a
value codec or an assertion that a native request has been verified. List order
is ascending numeric address; labels are not unique keys.

`Lookup(key)` returns `(entry, found, error)` for the exact seven axes below.
The signatures describe the required representation contract; they are not a
claim that companion code has been executed or that language bindings match.
No bus family, namespace, opcode, variant or direction is inferred.

| Key axis | Required dictionary value | Independent control |
|---|---|---|
| family | B513 | B512 is absent |
| opcode | 04 | 05 is absent |
| dictionary_namespace | b513-generic-candidate | synthetic-other-dictionary is absent |
| raw_address | explicit numeric u16 | 0000 and 0001 have different labels; 0100 differs from 0000 |
| bus_family | eBUS or PeBUS, matched separately | synthetic-other-bus is absent |
| variant | literal unqualified | synthetic-family-a is absent |
| direction | literal unqualified | request and response are each absent |

The literal `unqualified` is metadata, never all-directions permission or a
variant wildcard. eBUS and PeBUS queries keep distinct key contexts even when
the returned candidate label is equal. Membership on either bus grants no
transmit route, polling default, automatic native qualification or write
admission. Admission remains fail-closed.

A known exact key returns an independent entry, `found=true`, no error.
A complete, well-formed but unmatched key returns no entry, `found=false`, no
error and Unknown interpretation; it does not mean unsupported. Preserve the
raw query and every independently useful key field on all outcomes. A caller
must not erase independently useful prior state on lookup failure; this helper
has no cache or state-replacement policy.

Missing, null or empty address returns `missing-address`, never numeric zero.
A Boolean, string, noninteger or out-of-u16 address returns `invalid-address`.
Other missing, null or empty identity fields return `incomplete-key`. Errors
return no entry and `found=false`; address validation precedes other key checks.
Numeric 0000 is present and has the literal label AccessoryRelaisOne.

Every call owns its returned list, entries, address-byte buffers and nested
membership maps. Lookup results and retained query snapshots are independent
of the catalog, caller inputs and all prior results; mutation of one returned
object cannot change any later result. These are required ownership semantics,
not evidence of companion implementation correctness.

## Representative synthetic examples

The [small JSON example set](fixtures/al04_b513_symbolic_dictionary.json) is
synthetic representation data, not a second dictionary or a native profile.
The complete finite catalog remains the linked public table.

| Raw address | Literal native label | eBUS membership | PeBUS membership |
|---|---|---|---|
| 0000 | AccessoryRelaisOne | Hypothesis | Hypothesis |
| 0001 | AccessoryRelaisTwo | Hypothesis | Hypothesis |
| 00EE | DCF is Valid | Hypothesis | Hypothesis |
| 02D0 | IsInSavingsFunction | Hypothesis | Hypothesis |
| 02D3 | LanguageVariant | Hypothesis | Hypothesis |
| 0371 | PowerOnCounter | Hypothesis | Hypothesis |
| 0372 | PowerOnCounter | Hypothesis | Hypothesis |
| FFFF | All Addresses | Hypothesis | Hypothesis |

FFFF carries the All Addresses label only in this dictionary. It is neither an
iterable interval nor an admitted all-address operation. Equal labels at 0371
and 0372 retain distinct raw addresses. Actual gaps 02D1, 02D2, 0364, 0365,
0368 and 0391 through 0398 remain unknown raw addresses; they are not filled
from adjacent labels. No closed-interval validity, other variant dictionary,
default or value type follows from numeric proximity. Unknown addresses retain
their raw numeric key and Unknown interpretation.

## Machine-readable contract

The following assertions constrain this page and its examples only.

```json
{
  "api": [
    "Ab38Entries",
    "Lookup"
  ],
  "key_axes": [
    "family",
    "opcode",
    "dictionary_namespace",
    "raw_address",
    "bus_family",
    "variant",
    "direction"
  ],
  "family": "B513",
  "opcode": "04",
  "dictionary_namespace": "b513-generic-candidate",
  "variant": "unqualified",
  "direction": "unqualified",
  "unique_addresses": 1263,
  "candidate_memberships": {
    "eBUS": 1263,
    "PeBUS": 1263
  },
  "candidate_grade": "Hypothesis",
  "representation_grade": "Proven",
  "physical_qualification": "Unknown",
  "presence": "Unknown",
  "freshness": "Unknown",
  "execution": "Unknown",
  "missing_address": "error:missing-address",
  "invalid_address": "error:invalid-address",
  "incomplete_key": "error:incomplete-key",
  "unknown_key": "absent:Unknown",
  "zero_address": "literal-address",
  "ffff": "label-only",
  "gap_fill": false,
  "value_codec": null,
  "executable_capability": false,
  "returned_memory": "independent-deep-copies"
}
```

## Validation and companion boundary

The scoped standard-library suite checks the full public catalog's 1263 unique
numeric keys, exact address/label correspondence, separate memberships and
representative independent expectations. It computes a SHA-256 fingerprint
from the linked public table's ordered `AAAA|native-label` lines with a trailing
newline per row; the expectation uses base64 bytes, not a commit identifier.
The JSON includes only eight examples. Tests vary every key axis independently,
both address bytes, both bus memberships, every example address and label,
actual gaps, error/absence/zero controls and nested returned memory. A local
specification oracle exercises synthetic controls without importing companion
code. It establishes no code result, native effect or full parity before the
companion's own checks.

This page adds no runtime integration or application endpoint. Existing eBUS
MCP compatibility and GraphQL parity remain requirements for their owners;
neither surface is validated here. Navigation and runtime integration are
carried elsewhere. Independent committed-change review, full CI, publication
checks and applicable transport classification remain later ship requirements.
