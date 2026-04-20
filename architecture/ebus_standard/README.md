# ebus_standard Normative Documentation

Status: Normative
Milestone: M0_DOC_GATE
Plan reference: ebus-standard-l7-services-w16-26.locked/00-canonical.md
Canonical SHA-256: 9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305

## Completion status

The first-delivery `ebus_standard` L7 namespace plan (cruise-run meta
`Project-Helianthus/helianthus-execution-plans#14`) completed 2026-04-20
with 17 milestones merged. Transport matrix:
`helianthus-ebusgateway/matrix/M6a-transport-matrix.md` (anchor commit
`686dfaf0`, helianthus-ebusgateway#514). BENCH-REPLACE operator
follow-up: pending (matrix §7 status `PLACEHOLDER`).

## Purpose

This directory freezes the first normative documentation set for the
Helianthus `ebus_standard` Layer 7 provider namespace.

The locked plan states:

> `ebus_standard` is a new L7 provider namespace for Helianthus that carries the
> official eBUS Application Layer standard services. It is a cross-vendor,
> catalog-driven surface applicable to any eBUS-conformant device. It runs in
> parallel with the existing Vaillant `0xB5` provider namespace and does not
> reuse Vaillant-specific logic.

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.locked/00-canonical.md`, SHA-256
`9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

## Index

| File | Normative subject |
|---|---|
| [`00-namespace.md`](./00-namespace.md) | Namespace boundary, catalog source of truth, identity key |
| [`01-services-catalog.md`](./01-services-catalog.md) | First-lock service and command catalog with `safety_class` |
| [`02-l7-types.md`](./02-l7-types.md) | Required primitive and selector decoding rules |
| [`03-identification.md`](./03-identification.md) | Canonical `0x07 0x04` Identification descriptor |
| [`04-capability-discovery.md`](./04-capability-discovery.md) | Optional `0x07 0x03` / `0x07 0x05` capability discovery |
| [`05-execution-safety.md`](./05-execution-safety.md) | Safety classes, default-deny policy, NM runtime whitelist |
| [`06-nm-adoption.md`](./06-nm-adoption.md) | Adopt-and-extend of merged NM docs |
| [`07-identity-provenance.md`](./07-identity-provenance.md) | Identity provenance and `DeviceInfo` non-overwrite policy |
| [`08-provider-contract.md`](./08-provider-contract.md) | M3 provider contract: ABI snapshot stability, disable switch, runtime enforcement pointer |
| [`09-mcp-envelope.md`](./09-mcp-envelope.md) | M4 MCP envelope contract, deterministic `data_hash`, golden fixture discipline |
| [`10-rpc-source-113.md`](./10-rpc-source-113.md) | M4 `rpc.invoke` gateway source byte invariant |
| [`11-m4b-semantic-lock.md`](./11-m4b-semantic-lock.md) | M4B semantic lock of read & decode surfaces (envelope, error, safety_class, decode scaffold, catalog version) |
| [`13-responder-capability-signal.md`](./13-responder-capability-signal.md) | M4D normative lock of `meta.capabilities.responder` (shape, invariants I1-I8, fail-closed consumer rule, enum catalogue at v1.1, subtree version policy) |
| [`14-transport-matrix-cross-reference.md`](./14-transport-matrix-cross-reference.md) | M6b pointer to the canonical transport matrix artifact in helianthus-ebusgateway (section pointers §3-§7, BENCH-REPLACE status) |

## Related Source Documents

- [`../nm-model.md`](../nm-model.md)
- [`../nm-discovery.md`](../nm-discovery.md)
- [`../nm-participant-policy.md`](../nm-participant-policy.md)
- [`../../protocols/ebus-services/ebus-application-layer.md`](../../protocols/ebus-services/ebus-application-layer.md)
