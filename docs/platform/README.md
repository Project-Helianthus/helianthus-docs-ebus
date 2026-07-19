# Helianthus Platform Contracts

This directory is the temporary canonical home for cross-protocol Helianthus
platform contracts.

It owns contracts that apply across protocol families:

- MCP-first lifecycle and namespace governance;
- raw evidence and snapshot rules;
- semantic promotion gates;
- multi-runtime coexistence and conflict handling;
- consumer rollout order for GraphQL, Portal, and Home Assistant.

Current platform contracts:

- [`cross-runtime-envelope.md`](./cross-runtime-envelope.md)
- [`hash-auth-binding.md`](./hash-auth-binding.md)
- [`shared-registry-boundary.md`](./shared-registry-boundary.md)
- [`promotion-and-consumer-contract.md`](./promotion-and-consumer-contract.md)
- [`ownership-validation.md`](./ownership-validation.md)
- [`ownership-and-doc-gates.md`](./ownership-and-doc-gates.md)
- [`eebus-raw-first-contract.md`](./eebus-raw-first-contract.md)
- [`eebus-raw-runtime-freeze.md`](./eebus-raw-runtime-freeze.md) - M3.5
  identity, snapshot-envelope, and evidence-object freeze boundary
- [`raw-correlation-and-leaf-promotion.md`](./raw-correlation-and-leaf-promotion.md)
- [`synchronized-evidence-bundle-v1.md`](./synchronized-evidence-bundle-v1.md) -
  MSP-065 closed synchronized capture and deterministic offline replay contract
- [`draft-candidate-fact-graph-v1.md`](./draft-candidate-fact-graph-v1.md) -
  MSP-07 closed M7 candidate-only fact graph and deterministic replay contract
- [`multi-runtime-coexistence-no-drift-v1.md`](./multi-runtime-coexistence-no-drift-v1.md) -
  MSP-08 closed EEBUS-G18 coexistence, protected-view no-drift, and rollback
  contract
- [`eebus-ha-network-proof.md`](./eebus-ha-network-proof.md)
- [`eebus-interop-smoke.md`](./eebus-interop-smoke.md) - canonical G01/G17/G19
  evidence, authority, redaction, and promotion boundary

The publication-contract v2 canonical collection is the exact foundational
inventory of `cross-runtime-envelope.md`, `hash-auth-binding.md`,
`shared-registry-boundary.md`, `promotion-and-consumer-contract.md`, and
`ownership-validation.md`. The remaining pages are milestone-specific
operational contracts and are not silently added to that collection. The
G17/G19 smoke page cross-seeds only the platform evidence boundary; eeBUS-native
transport evidence remains with the protocol-owned companion.

The authoritative eeBUS ownership state is the versioned
[`manifests/eebus-doc-ownership.yaml`](./manifests/eebus-doc-ownership.yaml)
manifest.

Protocol-specific repositories may link here, but they must not duplicate these
contracts as normative text. Non-owning pages are summary-only.

## Transition Rule

This directory remains the platform-contract home until a separate
`helianthus-docs-platform` repository is created after the current eeBUS
raw-first bootstrap. The trigger is either:

- a later non-eBUS protocol reaches a promoted-leaf gate; or
- a cross-protocol contract changes for reasons unrelated to eBUS or the eeBUS
  VR940f raw-first track.

When that happens, platform pages move as a unit, this directory keeps stubs,
and canonical links are updated.
