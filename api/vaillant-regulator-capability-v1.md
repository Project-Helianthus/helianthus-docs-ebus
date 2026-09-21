# Vaillant Regulator Capability API V1

**Status:** Accepted additive public contract. The implementation merged through
[helianthus-ebusgateway#947](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/947),
which owns [gateway issue #946](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/946).
Merge status is repository evidence only; this page makes no deployment or live
qualification claim.

This contract publishes one Vaillant catalog-derived eBUS capability for consumers. It
does not expose product catalog rows, device roles, native frames, or a
controller address. The machine-readable companion is
[`vaillant-regulator-capability-api-v1.json`](../docs/platform/manifests/vaillant-regulator-capability-api-v1.json).

This is not a gateway-wide regulator aggregate and not a cross-protocol result.
Every detected Vaillant identity participates in the result through the accepted
Vaillant product catalog; an identity that the catalog cannot classify is not
discarded.

## Public surfaces

The gateway's existing GraphQL `Query` gains this non-null root field:

```graphql
type Query {
  vaillant_regulator_capability: VaillantRegulatorCapability!
}

enum VaillantRegulatorCapability {
  UNKNOWN
  NONE
  PRESENT
}
```

The matching MCP response member is
`ebus.v1.runtime.status.get.data.vaillant_regulator_capability`. The semantic snapshot
uses the same value at `runtime_status.vaillant_regulator_capability`. All three surfaces
are one provider-owned result; GraphQL, MCP, and snapshot consumers must not
recalculate it.

Examples:

```json
{"data":{"vaillant_regulator_capability":"PRESENT"}}
```

```json
{"data":{"vaillant_regulator_capability":"UNKNOWN"}}
```

## Closed result and precedence

`PRESENT` wins when any detected Vaillant identity is catalog-classified as a
regulator. `NONE` requires at least one detected Vaillant identity and every
detected identity to be catalog-known non-regulator. `UNKNOWN` is returned for
catalog failure, no Vaillant inventory, or a catalog lookup miss for any
detected Vaillant identity when no regulator is present. Therefore an
unclassified detected identity cannot be discarded to produce `NONE`.

An unwired or failing provider returns `UNKNOWN`. An older gateway or a missing
`vaillant_regulator_capability` member is interpreted by a consumer as
`UNKNOWN`, preserving the V1 API and runner compatibility boundary.

Consumers MUST NOT infer this result from BASV/VRC prefixes, display names, or
per-device roles. Those are not inputs to the public result.

The separate regulator absence-grace lifecycle from gateway #194/#212 is not
part of this field. Consumers that handle `NONE` and `UNKNOWN` identically do
not need a settled-removal signal.

## Catalog capability classification

**Contract status:** Normative target for `helianthus-ebusreg` issue #169.
**Evidence status:** `Unknown` until an accepted implementation of #169 provides
matching repository evidence. This section does not claim that current accepted
registry code already satisfies the target.

`ControllerCapability` MUST remain a read-only catalog classification owned by
`helianthus-ebusreg`. Its capability index MUST include every catalog row whose
normalized `part_number` and `role` are both nonempty. It does not require
`brand`, `family`, `product_model`, notes, or any other enrichment metadata.
That capability index MUST remain distinct from the enrichment index, which may
require richer metadata for identity presentation and product enrichment.

The controller-role vocabulary is closed and case-insensitive:

- `Regulator` and `Thermostat` classify as `PRESENT`.
- A known row with another nonempty role classifies as `NONE`.
- A missing part number, no matching catalog row, or a roleless row classifies
  as `UNKNOWN`.

This classification MUST remain read-only. It neither admits a profile nor proves B524
capability, routing eligibility, or control authority. In particular, it does
not bypass the direct controller-qualification evidence required by
[ebusreg#167](https://github.com/Project-Helianthus/helianthus-ebusreg/issues/167).

## Evidence and ownership

The defining gateway revision is
[`76d66a60b2895b3392bba798a5f690a1d73daa1f`](https://github.com/Project-Helianthus/helianthus-ebusgateway/commit/76d66a60b2895b3392bba798a5f690a1d73daa1f),
the independently reviewed source head of merged gateway
[#947](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/947).
Its review returned `NO_BLOCKING_FINDINGS`; the original coordinated
documentation gate was accepted through closed issue
[#511](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/511).
It uses accepted `helianthus-ebusreg`
[`e24532a50caa00c113751b98b88239e045d731e8`](https://github.com/Project-Helianthus/helianthus-ebusreg/commit/e24532a50caa00c113751b98b88239e045d731e8)
and retains the historical `ControllerCapability` dependency introduced by
[ebusreg#97](https://github.com/Project-Helianthus/helianthus-ebusreg/issues/97)
through [#98](https://github.com/Project-Helianthus/helianthus-ebusreg/pull/98)
at `ad503214d698ee5a0c58da2ce637a54dd714409b`. The catalog role-policy
clarification is owned by [ebusreg#169](https://github.com/Project-Helianthus/helianthus-ebusreg/issues/169).

Gateway [#193](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/193)
through [#211](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/211)
established catalog-only derivation. Gateway
[#194](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/194)
through [#212](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/212)
owns re-detection and absence grace; gateway [#947](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/947)
implements this additive public projection. This documentation issue is
[#532](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/532);
the first consumer is Home Assistant
[#101](https://github.com/Project-Helianthus/helianthus-ha-integration/issues/101).

This is an additive read-only API contract. It adds no eBUS decoding, transport
I/O, write/control behavior, persistence, deployment, or physical test.
