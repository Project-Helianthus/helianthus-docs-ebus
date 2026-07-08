# Helianthus Platform Contracts

This directory is the temporary canonical home for cross-protocol Helianthus
platform contracts.

It owns contracts that apply across protocol families:

- MCP-first lifecycle and namespace governance;
- raw evidence and snapshot rules;
- semantic promotion gates;
- multi-runtime coexistence and conflict handling;
- consumer rollout order for GraphQL, Portal, and Home Assistant.

Protocol-specific repositories may link here, but they must not duplicate these
contracts as normative text. Non-owning pages are summary-only.

## Transition Rule

This directory remains the platform-contract home until a separate
`helianthus-docs-platform` repository is created. The trigger is either:

- a second non-eBUS protocol reaches a promoted-leaf gate; or
- a cross-protocol contract changes for non-eBUS reasons.

When that happens, platform pages move as a unit, this directory keeps stubs,
and canonical links are updated.
