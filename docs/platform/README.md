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

- [`ownership-and-doc-gates.md`](./ownership-and-doc-gates.md)
- [`eebus-raw-first-contract.md`](./eebus-raw-first-contract.md)
- [`raw-correlation-and-leaf-promotion.md`](./raw-correlation-and-leaf-promotion.md)
- [`eebus-ha-network-proof.md`](./eebus-ha-network-proof.md)

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
