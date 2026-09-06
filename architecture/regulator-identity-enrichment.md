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

## Canonical Qualified-Identity Normalization

**Contract status: Normative registry behavior. This is an implementation
canonicalization contract, not proof of a native eBUS identity.** Every member
is canonicalized independently before equality decides whether the triple is
an exact match.

The machine-readable canonical companion is the public
[qualified-identity policy](regulator-qualified-identity-policy.json), currently
schema version 2. It is a small, closed documentation contract for this
qualified-identity boundary; this
page retains the explanatory architecture and evidence context.

## Schema Version and Historical V1 Boundary

The canonical path publishes the expanded **schema version 2** policy. Current
repository references consume that v2 shape, including its required `instance`
and `consumer_witness` sections. This is a breaking replacement for a consumer
pinned to the historical v1 policy; it is never described as v1-compatible.

Version 1 remains the accepted historical cross-address qualified-identity
policy: its closed root has no `instance` or `consumer_witness` section. A v1
reader must reject the v2 shape, and the current v2 checker rejects an expanded
shape labelled v1. The historical fixture exists only to identify and regress
that accepted v1 rule; this documentation publishes no migration runtime or
general compatibility engine.

For a fixed-width native `DeviceID`, the decoder removes only terminal NUL
(`0x00`) and ASCII-space (`0x20`) padding before constructing `DeviceInfo`.
It does not remove leading or embedded bytes. This is the decoder-to-registry
boundary: the registry normalizer does not remove NUL padding from a value that
reaches it. The observed `STR:*` decoder convention documents trailing NUL
padding removal in [`ebusd-csv.md`](../types/ebusd-csv.md#type-specs).

The registry identity normalizer then applies the same operation separately to
`Manufacturer`, `DeviceID`, and `SerialNumber`: trim leading and trailing
Unicode whitespace and fold case to uppercase. It preserves internal whitespace
and punctuation in every member. In particular, `VR_71` and `VR71` are distinct
`DeviceID` values; a selector, display, or `productCode` naming convention does
not collapse them for cross-address identity. The implementation evidence is
[`registry/identity.go` at the issue-159 start
commit](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/c12c864b1773c00f6ead4f360e9b4f42d3930659/registry/identity.go).

The serial sentinel recognition below is a separate, narrow denylist. It does
not add punctuation removal, product-name equivalence, or any other identity
equivalence rule to this canonicalization.

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
original observation timestamp. A current-session active scan MAY promote that
face to `active_confirmed`/`identity_confirmed` without establishing a
cross-address stable identity. The directed `0x07/0x04` identification response
used by that existing active-scan contract carries manufacturer, `DeviceID`, and
software/hardware versions, not `SerialNumber`; it is per-face verification,
not the qualified cross-address merge evidence. Identity confirmation MUST NOT
rewrite a face's `static_seed` or `passive_observed` source label. A qualified
observation may confirm faces already grouped by explicit topology evidence,
but it does not turn topology evidence into an identity merge.

## Exact-Address Consumer Witness

**Contract status: Normative registry behavior. This is not an eBUS wire
identity claim or a general attestation system.** A consumer witness is a small,
value-typed registry value for one exact address. Its required fields and closed
values are defined by the `consumer_witness` section of the
[qualified-identity policy](regulator-qualified-identity-policy.json).

The registry alone produces an immutable witness from a direct complete
observation at that exact address. It binds that address to the complete
normalized `(Manufacturer, DeviceID, SerialNumber)` authority, not merely a
field label or partial value, and retains direct-observation provenance. It
MUST carry nonzero registry observation and proof generations.

Currentness is not a cached `current: true` field. At consumer decision time,
the lookup, validation, and use form one atomic registry boundary: the supplied
witness authority, observation generation, and proof generation MUST equal the
current registry state for that exact address and complete normalized triple
authority. Positive generation values alone are insufficient. Replacement,
retirement, or a conflict in any supplied triple member makes a prior immutable
witness unavailable/not-current until a fresh direct complete observation
produces a new witness. A witness for another address cannot substitute.

Observable nonempty fields, `identity_confirmed`, a topology alias or
topology-propagated confirmation, `static_seed`, `passive_observed`, caller
assertions, and last-known-good data are not consumer witnesses. A directed
`0x07/0x04` reply may confirm its responding face in the current session without
a serial number, but it is not a qualified cross-address identity witness.

The public implementation at
[`helianthus-ebusreg@e118b9a90bd7ee4035cf108571fbe86b2de020bd`](https://github.com/Project-Helianthus/helianthus-ebusreg/tree/e118b9a90bd7ee4035cf108571fbe86b2de020bd)
is compatibility input only. It neither proves a native eBUS identity nor
replaces this public registry contract.

This contract concerns registry behavior only. It does not make a device's wire
identity, a source/target relationship, or a companion relationship Proven.
For the corresponding ATR contract, see
[Qualified Identity Merge Gate](atr/04-sn-merge-gate.md).

## Atomic Passive Companion Admission API Roles

<!-- qualified-identity-policy:registry-api:begin same_source_positive_ack_plus_current_exact_address_witness -->
`DeviceRegistry.WithCurrentQualifiedIdentityWitness(address, callback)` remains the read-locked operation for bounded non-registry derived-state commits. Its callback MUST NOT call `DeviceRegistry` methods; it cannot lock-upgrade or use an unlock/relock check-then-use sequence.

`DeviceRegistry.AdmitPassiveCompanionWithCurrentQualifiedIdentityWitness(source, observedAt)` is the state-changing operation. The registry MUST derive the canonical companion from `source` and MUST atomically validate the current exact-source direct complete normalized witness plus passive target companion-slot admission in one write-critical section. It MUST NOT accept a caller-supplied companion. Replacement, retirement, or conflict cannot interleave between successful validation and the committed passive slot.

The accepted registry implementation is [`registry/admit_passive_companion.go` at `7971e0ab21c55414beb52ab84d6b38b25e27f37d`](https://github.com/Project-Helianthus/helianthus-ebusreg/blob/7971e0ab21c55414beb52ab84d6b38b25e27f37d/registry/admit_passive_companion.go).

This records one registry admission decision. It does not prove wire identity, create attestation authority, perform I/O, make topology an identity proof, or close gateway, M7, or physical acceptance criteria.
<!-- qualified-identity-policy:registry-api:end same_source_positive_ack_plus_current_exact_address_witness -->

## Cross-Links

- Semantic root discovery: [`b524-semantic-root-discovery.md`](./b524-semantic-root-discovery.md)
- Vaillant regulator model: [`vaillant.md`](./vaillant.md)
- Functional-module target: [`functional-modules.md`](./functional-modules.md)
- Family naming reference: [`../protocols/vaillant/basv.md`](../protocols/vaillant/basv.md)
- Product IDs catalog: [`helianthus-ebus-vaillant-productids`](https://github.com/Project-Helianthus/helianthus-ebus-vaillant-productids)
