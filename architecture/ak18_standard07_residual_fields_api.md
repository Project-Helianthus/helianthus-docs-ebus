# Standard 07 residual fields: catalog API companion

## Contract and native boundary

**Proven local API contract:** package `ebus_standard_catalog` exposes exactly
these catalog entry points for this area:

```go
func Ab28Entries() (json.RawMessage, error)
func Ab28Lookup(Ab28Key) (json.RawMessage, bool, error)

type Ab28Key struct {
    Ab28Family        string
    Ab28Variant       string
    Ab28Primary       uint8
    Ab28Secondary     *uint8
    Ab28Operation     *uint8
    Ab28Direction     string
    Ab28Field         string
    Ab28Alternative   string
    Ab28Group         *uint8
    Ab28InstanceScope string
    Ab28Register      *uint16
}
```

The [native residual supplement](../protocols/ebus-services/ebus-standard07-residual-fields.md)
and its [finite candidate data](../protocols/ebus-services/fixtures/ak18_standard07_residual_fields.json)
are the native representation contract. API behavior is separate from native
qualification. **Hypothesis:** the seven candidate identities are `0700`, `0702`,
`0703`, `0704`, `0705`, `07FE`, and `07FF`. This area exposes only residual
`00/02/03/05/FE/FF` fields and relations. `0704` identity/parser contracts retain
their existing owner; no `0701` body is introduced.

## Exact identity

**Proven local API contract:** all eleven axes participate in exact equality.
Optional absent and explicit zero differ. Non-applicable string axes use `none`.
An applicable instance scope is an explicit string such as `00` or `dynamic`,
never an invented numeric instance. No wildcard or nearest-key lookup is permitted.
There is no cross-family, variant, direction, field, or alternative fallback.

The table gives one synthetic present-key control and independent valid type
changes that must miss when only the control row is present. `null` denotes an
absent pointer; it is distinct from a pointer to zero.

| Axis | Go type | Present control | Isolated miss |
|---|---|---|---|
| Ab28Family | string | "system-data" | "other-family" |
| Ab28Variant | string | "vaillant-candidate" | "other-variant" |
| Ab28Primary | uint8 | 7 | 8 |
| Ab28Secondary | *uint8 | 0 | 2 |
| Ab28Operation | *uint8 | null | 0 |
| Ab28Direction | string | "body" | "request" |
| Ab28Field | string | "weekday" | "year" |
| Ab28Alternative | string | "none" | "other-alternative" |
| Ab28Group | *uint8 | null | 0 |
| Ab28InstanceScope | string | "none" | "dynamic" |
| Ab28Register | *uint16 | null | 0 |

The following synthetic contract vectors describe exact-key behavior. They are
examples of the API contract, not additional native rows or evidence that a
registry implementation has been executed. Each miss changes only its named
axis; the final case isolates absent versus explicit zero for Secondary.

```json
{
  "present_key": {
    "Ab28Family": "system-data",
    "Ab28Variant": "vaillant-candidate",
    "Ab28Primary": 7,
    "Ab28Secondary": 0,
    "Ab28Operation": null,
    "Ab28Direction": "body",
    "Ab28Field": "weekday",
    "Ab28Alternative": "none",
    "Ab28Group": null,
    "Ab28InstanceScope": "none",
    "Ab28Register": null
  },
  "lookup_cases": [
    {
      "name": "exact",
      "query": {
        "Ab28Family": "system-data",
        "Ab28Variant": "vaillant-candidate",
        "Ab28Primary": 7,
        "Ab28Secondary": 0,
        "Ab28Operation": null,
        "Ab28Direction": "body",
        "Ab28Field": "weekday",
        "Ab28Alternative": "none",
        "Ab28Group": null,
        "Ab28InstanceScope": "none",
        "Ab28Register": null
      },
      "result": "whole-row"
    },
    {
      "name": "Ab28Family",
      "query": {
        "Ab28Family": "other-family",
        "Ab28Variant": "vaillant-candidate",
        "Ab28Primary": 7,
        "Ab28Secondary": 0,
        "Ab28Operation": null,
        "Ab28Direction": "body",
        "Ab28Field": "weekday",
        "Ab28Alternative": "none",
        "Ab28Group": null,
        "Ab28InstanceScope": "none",
        "Ab28Register": null
      },
      "result": "missing"
    },
    {
      "name": "Ab28Variant",
      "query": {
        "Ab28Family": "system-data",
        "Ab28Variant": "other-variant",
        "Ab28Primary": 7,
        "Ab28Secondary": 0,
        "Ab28Operation": null,
        "Ab28Direction": "body",
        "Ab28Field": "weekday",
        "Ab28Alternative": "none",
        "Ab28Group": null,
        "Ab28InstanceScope": "none",
        "Ab28Register": null
      },
      "result": "missing"
    },
    {
      "name": "Ab28Primary",
      "query": {
        "Ab28Family": "system-data",
        "Ab28Variant": "vaillant-candidate",
        "Ab28Primary": 8,
        "Ab28Secondary": 0,
        "Ab28Operation": null,
        "Ab28Direction": "body",
        "Ab28Field": "weekday",
        "Ab28Alternative": "none",
        "Ab28Group": null,
        "Ab28InstanceScope": "none",
        "Ab28Register": null
      },
      "result": "missing"
    },
    {
      "name": "Ab28Secondary",
      "query": {
        "Ab28Family": "system-data",
        "Ab28Variant": "vaillant-candidate",
        "Ab28Primary": 7,
        "Ab28Secondary": 2,
        "Ab28Operation": null,
        "Ab28Direction": "body",
        "Ab28Field": "weekday",
        "Ab28Alternative": "none",
        "Ab28Group": null,
        "Ab28InstanceScope": "none",
        "Ab28Register": null
      },
      "result": "missing"
    },
    {
      "name": "Ab28Operation",
      "query": {
        "Ab28Family": "system-data",
        "Ab28Variant": "vaillant-candidate",
        "Ab28Primary": 7,
        "Ab28Secondary": 0,
        "Ab28Operation": 0,
        "Ab28Direction": "body",
        "Ab28Field": "weekday",
        "Ab28Alternative": "none",
        "Ab28Group": null,
        "Ab28InstanceScope": "none",
        "Ab28Register": null
      },
      "result": "missing"
    },
    {
      "name": "Ab28Direction",
      "query": {
        "Ab28Family": "system-data",
        "Ab28Variant": "vaillant-candidate",
        "Ab28Primary": 7,
        "Ab28Secondary": 0,
        "Ab28Operation": null,
        "Ab28Direction": "request",
        "Ab28Field": "weekday",
        "Ab28Alternative": "none",
        "Ab28Group": null,
        "Ab28InstanceScope": "none",
        "Ab28Register": null
      },
      "result": "missing"
    },
    {
      "name": "Ab28Field",
      "query": {
        "Ab28Family": "system-data",
        "Ab28Variant": "vaillant-candidate",
        "Ab28Primary": 7,
        "Ab28Secondary": 0,
        "Ab28Operation": null,
        "Ab28Direction": "body",
        "Ab28Field": "year",
        "Ab28Alternative": "none",
        "Ab28Group": null,
        "Ab28InstanceScope": "none",
        "Ab28Register": null
      },
      "result": "missing"
    },
    {
      "name": "Ab28Alternative",
      "query": {
        "Ab28Family": "system-data",
        "Ab28Variant": "vaillant-candidate",
        "Ab28Primary": 7,
        "Ab28Secondary": 0,
        "Ab28Operation": null,
        "Ab28Direction": "body",
        "Ab28Field": "weekday",
        "Ab28Alternative": "other-alternative",
        "Ab28Group": null,
        "Ab28InstanceScope": "none",
        "Ab28Register": null
      },
      "result": "missing"
    },
    {
      "name": "Ab28Group",
      "query": {
        "Ab28Family": "system-data",
        "Ab28Variant": "vaillant-candidate",
        "Ab28Primary": 7,
        "Ab28Secondary": 0,
        "Ab28Operation": null,
        "Ab28Direction": "body",
        "Ab28Field": "weekday",
        "Ab28Alternative": "none",
        "Ab28Group": 0,
        "Ab28InstanceScope": "none",
        "Ab28Register": null
      },
      "result": "missing"
    },
    {
      "name": "Ab28InstanceScope",
      "query": {
        "Ab28Family": "system-data",
        "Ab28Variant": "vaillant-candidate",
        "Ab28Primary": 7,
        "Ab28Secondary": 0,
        "Ab28Operation": null,
        "Ab28Direction": "body",
        "Ab28Field": "weekday",
        "Ab28Alternative": "none",
        "Ab28Group": null,
        "Ab28InstanceScope": "dynamic",
        "Ab28Register": null
      },
      "result": "missing"
    },
    {
      "name": "Ab28Register",
      "query": {
        "Ab28Family": "system-data",
        "Ab28Variant": "vaillant-candidate",
        "Ab28Primary": 7,
        "Ab28Secondary": 0,
        "Ab28Operation": null,
        "Ab28Direction": "body",
        "Ab28Field": "weekday",
        "Ab28Alternative": "none",
        "Ab28Group": null,
        "Ab28InstanceScope": "none",
        "Ab28Register": 0
      },
      "result": "missing"
    },
    {
      "name": "Ab28Secondary-absent",
      "query": {
        "Ab28Family": "system-data",
        "Ab28Variant": "vaillant-candidate",
        "Ab28Primary": 7,
        "Ab28Secondary": null,
        "Ab28Operation": null,
        "Ab28Direction": "body",
        "Ab28Field": "weekday",
        "Ab28Alternative": "none",
        "Ab28Group": null,
        "Ab28InstanceScope": "none",
        "Ab28Register": null
      },
      "result": "missing"
    }
  ]
}
```

## Results, errors, and ownership

**Proven local API contract:**

- `Ab28Entries()` returns a JSON array of whole rows.
- `Ab28Lookup(Ab28Key)` returns exactly one whole row for an exact key.
- A missing exact key returns `found=false`, without a lookup error.
- Invalid embedded JSON returns an error from both entry points.
- Duplicate complete keys return an error from both entry points; no row wins.
- Every call returns independent deep byte copies. Mutating any returned row
  or entries buffer cannot affect a later result from either entry point.
- Each production row has a ticket-prefixed ID, the complete eleven-axis
  identity, stated fields/relations, candidate grade `Hypothesis`, explicit
  `Unknown` metadata, and retained raw form.

The registry implementation embeds its owned JSON in its owned Go file,
validates complete identity uniqueness, and preserves an existing package name
when one exists; otherwise the package is `ebus_standard_catalog`. This page
introduces no alternate family schema or pending API import. Shared registration,
existing catalog/provider APIs, and routability remain unchanged.

## Interpretation and admission

**Hypothesis:** the candidate field relationships and logical conversion examples
remain finite. Weekday 6 labels Sunday; raw 7..255 stays unlabelled. Duration 0
stays literal 0 with permanent interpretation **Unknown**. The unassociated
defaults 6 and 1 retain **Unknown** field associations. Version 12 and revision
34 remain independent values, never one API number. Eight bitmap bytes remain
raw; `80` does not select or admit a method. The `0703` request has one raw
secondary block; `0705` has independently retained secondary and primary blocks.
`07FE` inquiry and `07FF` sign-of-life stay separate without requiring a direct
inquiry reply.

**Unknown:** native support, physical effects, persistence, delivery, emission,
physical responses, exact bit selection, version-control overlap with `0704`,
century, timezone, calendar validation, complete native decimal conversion, and
qualified sentinel meaning for raw word `8000`. Candidate grade and physical
qualification are separate dimensions; a local representation pass does not
promote either to native support.

Admission fails closed for an incomplete or mismatched identity, malformed data,
or unresolved candidate semantics. Retain raw evidence and partial last-known-good
state without promoting an incomplete result. No transmit route, active executor,
scan-default change, or automatic native qualification follows from catalog data.
Existing eBUS MCP compatibility and GraphQL parity remain unchanged. These
contracts imply no stability guarantee before Helianthus 1.0.

## Companion ordering

AK17 must merge before this page in the same delivery cycle. The registry has no
dependency back to this page. Merging either companion does not establish native
qualification. Refs Project-Helianthus/helianthus-docs-ebus#1022 and
Project-Helianthus/helianthus-docs-ebus#736.
