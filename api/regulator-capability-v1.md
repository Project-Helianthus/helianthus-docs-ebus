# Canonical Regulator Capability API V1

**Status:** Target additive public contract; gateway implementation is owned by
[helianthus-ebusgateway#946](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/946).

This contract publishes one catalog-derived eBUS capability for consumers. It
does not expose product catalog rows, device roles, native frames, or a
controller address. The machine-readable companion is
[`regulator-capability-api-v1.json`](../docs/platform/manifests/regulator-capability-api-v1.json).

## Public surfaces

The gateway's existing GraphQL `Query` gains this non-null root field:

```graphql
type Query {
  regulator_capability: RegulatorCapability!
}

enum RegulatorCapability {
  UNKNOWN
  NONE
  PRESENT
}
```

The matching MCP response member is
`ebus.v1.runtime.status.get.data.regulator_capability`. The semantic snapshot
uses the same value at `runtime_status.regulator_capability`. All three surfaces
are one provider-owned result; GraphQL, MCP, and snapshot consumers must not
recalculate it.

Examples:

```json
{"data":{"regulator_capability":"PRESENT"}}
```

```json
{"data":{"regulator_capability":"UNKNOWN"}}
```

## Closed result and precedence

`PRESENT` wins when any Vaillant identity is catalog-classified as a regulator.
`NONE` requires at least one Vaillant identity and every relevant identity to
be catalog-known non-regulator. `UNKNOWN` is returned for catalog failure, no
Vaillant inventory, or any unclassified Vaillant identity when no regulator is
present.

An unwired or failing provider returns `UNKNOWN`. An older gateway or a missing
member is interpreted by a consumer as `UNKNOWN`, preserving the V1 API and
runner compatibility boundary.

Consumers MUST NOT infer this result from BASV/VRC prefixes, display names, or
per-device roles. Those are not inputs to the public result.

The separate regulator absence-grace lifecycle from gateway #194/#212 is not
part of this field. Consumers that handle `NONE` and `UNKNOWN` identically do
not need a settled-removal signal.

## Evidence and ownership

The defining gateway revision is
[`f52c08405e48609fb05ae8b231d1530bcfb46094`](https://github.com/Project-Helianthus/helianthus-ebusgateway/commit/f52c08405e48609fb05ae8b231d1530bcfb46094).
It uses accepted `helianthus-ebusreg`
[`e24532a50caa00c113751b98b88239e045d731e8`](https://github.com/Project-Helianthus/helianthus-ebusreg/commit/e24532a50caa00c113751b98b88239e045d731e8)
and retains the historical `ControllerCapability` dependency introduced by
[ebusreg#97](https://github.com/Project-Helianthus/helianthus-ebusreg/issues/97)
through [#98](https://github.com/Project-Helianthus/helianthus-ebusreg/pull/98)
at `ad503214d698ee5a0c58da2ce637a54dd714409b`.

Gateway [#193](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/193)
through [#211](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/211)
established catalog-only derivation. Gateway
[#194](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/194)
through [#212](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/212)
owns re-detection and absence grace. This documentation issue is
[#511](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/511);
the first consumer is Home Assistant
[#101](https://github.com/Project-Helianthus/helianthus-ha-integration/issues/101).

This is an additive read-only API contract. It adds no eBUS decoding, transport
I/O, write/control behavior, persistence, deployment, or physical test.
