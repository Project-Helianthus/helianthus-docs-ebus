# Registry catalog metadata and callable capability

## Scope and evidence

**Proven:** catalog identity, candidate schema, method descriptor, routable
invocation and qualified physical support are different properties. This page
records their application architecture boundary; it does not add a transmit
route or describe a newly repaired runtime. No pre-1.0 stability promise follows.

Native protocol facts come first from the public
[standard service references](./ebus_standard/01-services-catalog.md#scope)
and [B516 energy contract](../protocols/vaillant/ebus-vaillant-B516-energy.md).
Implementation behavior can corroborate a wire interpretation but cannot
establish it. **Proven**, **Hypothesis** and **Unknown** describe evidence for
an individual claim, independently of implementation completeness, codec
qualification and qualified physical support. A working codec does not promote
a candidate mapping or qualify a device family.

## Five independent properties

| Property | What it establishes | What it does not establish |
|---|---|---|
| Catalog identity | A named command identity and its native discriminators are represented. The standard catalog contains 57 command identities across `03/05/07/08/09/0F/FE/FF`. | These are not 57 executable body schemas or 57 executable methods. A catalog row and its safety classification do not build a request. |
| Candidate schema | Alternatives and possible body interpretations can be described with evidence grades and raw fallback. | A candidate is not a qualified codec, a request builder or execution authority. |
| Method descriptor | An application method can describe inputs, outputs and metadata. Heating/DHW descriptors include unbuilt setters. | Descriptor existence does not supply a missing setter builder. Selectorless solar templates do not establish an invocable request. |
| Routable invocation | A particular invocation has a route and a concrete request builder for its required selectors and body. | Legacy routability defaults do not qualify the native body, its codec or physical support. This page does not claim those runtime defaults have been repaired. |
| Qualified physical support | Separate evidence supports the particular operation for the applicable device family and context. | Neither a descriptor, a successful decode nor a hardware-version threshold alone establishes this property or a wire contract. |

**Proven:** the implemented `07/04` identity scanner remains independent of
catalog-wide body-schema coverage. Preserve that implementation; neither the
57-identity count nor gaps elsewhere retract its capability. Conversely,
scanner implementation does not make all catalog entries callable. The public
[Identification contract](./ebus_standard/03-identification.md) describes the
standard method and its raw fields; it is not evidence of broad physical support.

## Synthetic metadata boundary

The common native metadata representation retains alternatives, optional
offsets and widths, units, enums, sentinels, grades and raw fallback. The
following is a synthetic explanatory record, not a new artifact schema or a
native device mapping:

```text
field: synthetic_measurement
raw: [00, 00]
alternatives:
  - interpretation: candidate_scalar
    offset: unspecified
    width: unspecified
    unit: unknown
    enum: {00: candidate_idle}
    sentinel: [FF, FF]
    grade: Hypothesis
  - interpretation: raw_only
    offset: unspecified
    width: unspecified
    unit: unknown
    enum: unspecified
    sentinel: unspecified
    grade: Unknown
raw_fallback: [00, 00]
```

**Proven:** retaining this metadata adds no execution authority. Unspecified
offsets or widths stay unspecified; competing interpretations stay separate.
The example's enum and sentinel are synthetic candidates, not protocol facts.
**Unknown** stays **Unknown** rather than inheriting a grade from a method
label, a UI label or a successful decoder.

Preserve raw bytes beside each interpretation and retain useful prior state
per field when a partial refresh cannot replace it. Last-known-good values
are not a substitute for current qualification or missing request selectors.
Admission remains fail-closed: incomplete metadata cannot create an invocation
or write permission. A readable value does not establish writable behavior.

## B516: passive and active contracts remain separate

The native authority is the public B516 page's
[request layout](../protocols/vaillant/ebus-vaillant-B516-energy.md#3-request-payload-layout)
and [response format](../protocols/vaillant/ebus-vaillant-B516-energy.md#6-response-format).
These describe the energy-statistics sub-command, not every B516 body.

| Path | Request body | Reply/value contract | Capability conclusion |
|---|---|---|---|
| Passive processing | Accepts eight bytes beginning `10`: `[10, period, period_index, energy_index, source, usage, date_lo, date_hi]`. | Accepts an eleven-byte reply with a trailing little-endian IEEE 754 binary32 energy value at bytes 7–10. | **Proven** implementation acceptance shape; passive processing does not originate a request or establish active support. It does not promote every native field interpretation to Proven. |
| Heating/DHW active builder | Emits three bytes: `[period, source, usage]`. | Its descriptor is `WORD`, distinct from the passive binary32 value contract. | **Proven** separate implementation shape. Three bytes plus a WORD descriptor are not equivalent to the eight-byte request and eleven-byte passive energy reply. |
| Hardware-version threshold | Does not supply missing bytes, selectors or a native body definition. | Does not reconcile WORD with binary32. | **Unknown** equivalence remains Unknown; a threshold alone cannot equate these contracts or qualify physical support. |

This distinction establishes no new controller profile, write admission or
broad active energy support. Qualification remains separate for each path and
device family. The native page's field uncertainties remain in force; an
implementation acceptance shape does not override them.

## Consumer boundary

Keep eBUS MCP compatibility and GraphQL parity: the same five-property
distinctions apply on both surfaces. Catalog or candidate metadata must not
become callable merely because one surface exposes it. This documentation
introduces no API change, runtime route, authorization gate or grade promotion.
Focused offline documentation checks establish only the stated document
contract; they do not qualify transport behavior or physical equipment.
