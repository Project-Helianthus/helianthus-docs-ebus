# Regulator Identity Enrichment

This page documents how the gateway enriches the identity of a discovered B524 semantic root or controller-class endpoint.

It does **not** define the structural precondition for B524 semantic discovery. That precondition is documented separately in:

- [`b524-semantic-root-discovery.md`](./b524-semantic-root-discovery.md)

## Purpose

Identity enrichment answers questions such as:

- Is this endpoint Vaillant-branded or Saunier Duval-branded?
- Is it wireless or wired?
- Which regulator family does the identification string resemble?
- Does the product-IDs catalog know the product?

These answers are useful for:

- labeling and UI presentation;
- profile-specific documentation hints;
- debugging and reverse engineering;
- selecting richer product metadata when available.

They are **not** the gate for whether B524-backed semantic discovery is allowed to run.

## Identity Sources

Identity enrichment may combine:

- eBUS identification strings;
- known family prefixes and naming conventions;
- product-IDs catalog matches;
- product/model documentation.

Examples already documented in the repo include:

- `BASV2` = wireless Vaillant 720-series base station
- `BASS2` = wireless Saunier Duval 720-series base station
- `CTLV2` = wired Vaillant 720-series controller
- `CTLS2` = wired Saunier Duval 720-series controller
- older families such as `E7C00`

See:

- [`../protocols/vaillant/basv.md`](../protocols/vaillant/basv.md)

## Product-IDs Catalog

The `helianthus-ebus-vaillant-productids` catalog remains useful here:

- it can recognize known part numbers;
- it can enrich branding/family/model metadata;
- it can distinguish known regulator-class products from clearly non-regulator products.

But catalog knowledge is **not authoritative for B524 capability**:

- an unknown product can still be a valid B524 semantic root;
- a known regulator-family product does not by itself prove B524 capability without protocol evidence.

## Normalized Product Identity

One useful output of identity enrichment is a normalized `productCode`.

This is the concrete product identifier used by higher-level contracts when Helianthus needs per-product interpretation, for example:

- `VR70`
- `VR71`
- `VR66`
- `VR61`
- `VR68`

Important constraints:

- `productCode` is derived from identity enrichment, not from B524 alone;
- `productCode` may combine eBUS identity strings, product-catalog matches, and documented naming conventions;
- `productCode` may remain unknown without blocking B524 semantic discovery;
- `productCode` is useful for per-product semantic interpretation, but it is not itself proof of B524 capability.

This distinction matters for deferred contracts such as [`functional-modules.md`](./functional-modules.md), where concrete product identity is a better discriminator than a synthetic family taxonomy.

## Separation of Concerns

The correct layering is:

1. discover a B524 semantic root by protocol capability;
2. enrich that root with identity metadata if possible.

This separation is critical because:

- B524 is a private regulator API and is not exclusive to one prefix such as `BASV`;
- wired and wireless regulators use different families;
- Vaillant and Saunier Duval branding can expose equivalent roles under different prefixes;
- future or older regulator generations may be absent from the local product catalog.

## Unknown Identity Is Acceptable

The gateway must tolerate:

- unknown part number;
- unknown family prefix;
- incomplete model/branding classification.

As long as B524 capability is proven, semantic discovery can proceed.

Identity enrichment can remain partial or unknown without blocking:

- `zones`
- `circuits`
- `radioDevices`
- `fm5SemanticMode`
- `solar`
- `cylinders`

## Current Anti-Pattern

Historically, the implementation mixed:

- regulator identity heuristics
- and B524 semantic-root discovery

This was wrong. Examples:

- `findDeviceAddressByPrefix("BASV")`
- product-catalog gating of “controller present”

These may still be useful as enrichment or hints, but they must not remain the structural gate for semantic discovery.

## Registry Alias-Group and Identity Qualification

**Contract status: Normative registry behavior. This section does not establish
an eBUS wire identity or a companion relationship.**

Identity enrichment can arrive after an address has been observed or after
explicit topology evidence has grouped faces. The two mechanisms are separate:

- Explicit topology aliasing based on source/target or canonical-companion
  evidence MAY group faces before a qualified identity exists. It is not a
  cross-address identity merge.
- A cross-address identity merge requires an exact normalized
  `(Manufacturer, DeviceID, SerialNumber)` triple. All three members MUST be
  present and non-empty. Empty or partial triples create no cross-address stable
  identity key.

`SerialNumber` is not qualified when it is a sentinel value: `0`,
`0x00000000`, `0xFFFFFFFF`, or `0x7FFFFFFF`. Only while recognizing those
hexadecimal sentinels, case is ignored, one optional `0x` prefix is accepted,
and leading zeros are ignored. That narrow recognition rule MUST NOT parse,
rewrite, or otherwise reinterpret ordinary product serial formats.

Partial enrichment of an already-known address MAY retain last-known-good
fields for that same address. It MUST NOT establish a cross-address stable
identity key or merge independent addresses. Likewise, a serial-only match, a
MAC-only match, or a matching model signature alone MUST NOT merge independent
addresses. If an observation carries a matching serial but a conflicting MAC,
it MUST NOT select or merge another entry; both independent groups and their
known fields remain unchanged until qualified, non-conflicting evidence is
available.

Each face retains its discovery provenance, role, verification state, and
original observation timestamp. A static candidate becomes
`identity_confirmed` only after a complete qualified observation. Identity
confirmation MUST NOT rewrite a face's `static_seed` or `passive_observed`
source label. A qualified observation may confirm faces already grouped by
explicit topology evidence, but it does not turn topology evidence into an
identity merge.

This contract concerns registry behavior only. It does not make a device's wire
identity, a source/target relationship, or a companion relationship Proven.
For the corresponding ATR contract, see
[Qualified Identity Merge Gate](atr/04-sn-merge-gate.md).

## Cross-Links

- Semantic root discovery: [`b524-semantic-root-discovery.md`](./b524-semantic-root-discovery.md)
- Vaillant regulator model: [`vaillant.md`](./vaillant.md)
- Functional-module target: [`functional-modules.md`](./functional-modules.md)
- Family naming reference: [`../protocols/vaillant/basv.md`](../protocols/vaillant/basv.md)
- Product IDs catalog: [`helianthus-ebus-vaillant-productids`](https://github.com/Project-Helianthus/helianthus-ebus-vaillant-productids)
