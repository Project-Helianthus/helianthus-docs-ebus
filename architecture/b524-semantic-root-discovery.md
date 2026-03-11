# B524 Semantic Root Discovery

This page documents the structural precondition for B524-backed semantic discovery.

The key rule is simple:

- if a slave endpoint proves coherent B524 capability, semantic discovery may run;
- product identity and regulator branding are optional enrichment, not prerequisites.

## Purpose

B524 semantic root discovery determines whether the gateway is allowed to evaluate and publish:

- `zones`
- `circuits`
- `radioDevices`
- `fm5SemanticMode`
- `solar`
- `cylinders`

It is therefore the true precondition behind structural discovery.

## Contract

B524 structure discovery is enabled when at least one candidate slave address responds coherently to B524 discovery probes.

This means:

- B524 root discovery is capability-based;
- it is not tied to one product prefix or branding family;
- it does not require the product-IDs catalog to recognize the endpoint.

## Candidate Address Policy

Recommended gateway policy:

1. start with `0x15` when present, because it is a common regulator address in known topologies;
2. continue across other discovered slave addresses;
3. do not assume that `0x15` is mandatory or unique;
4. do not reject a candidate only because its identity is unknown.

This ordering is a gateway policy convenience, not protocol truth.

## Success Criterion

A candidate slave qualifies as a semantic root when it responds coherently to B524 probing.

For the purposes of this contract, coherent response means:

- the request is accepted as B524 traffic;
- the response shape is compatible with B524 framing and selector semantics;
- the endpoint can serve as the root for further `GG/II/RR` discovery.

This page does not freeze one exact probe sequence yet. The key point is that capability is proven by protocol behavior, not by product naming.

## Failure Behavior

If no candidate slave proves B524 capability:

- B524-backed semantic families remain unavailable;
- B524 structural discovery does not run;
- identity enrichment alone does not revive the semantic root.

## Startup Recovery Rule

Startup recovery follows the same capability-first contract.

- Partial inventory from startup preload does not prove that semantic discovery is ready.
- Product identity, regulator branding, and metadata imported from `ebusd scan result`
  are enrichment inputs, not root-discovery proof.
- If narrowed/preloaded startup inventory still does not yield a coherent B524 root,
  gateway must perform one bounded full-range discovery retry before closing startup
  scan.
- If startup preload already yields a coherent B524 root, no broadened retry is needed.

This keeps startup behavior aligned with the semantic contract:

- prove coherent B524 capability first;
- then keep or enrich identity around the proven root.

Important scope note:

- proving a coherent B524 root does not by itself prove that passive
  observe-first is supported on the configured transport topology;
- passive observe-first support remains transport-dependent runtime contract
  surface, documented in [`deployment/full-stack.md`](../deployment/full-stack.md).

## Relationship to Identity Enrichment

Identity enrichment happens after, or alongside, semantic-root discovery:

- semantic-root discovery answers: “can this endpoint serve B524?”
- identity enrichment answers: “what do we know about this endpoint?”

See:

- [`regulator-identity-enrichment.md`](./regulator-identity-enrichment.md)

## Why This Matters

The semantic root must not be coupled to a single family such as:

- `BASV2`
- `BASS2`
- `CTLV2`
- `CTLS2`

Those are identity families, not the definition of B524 capability.

The same principle applies to:

- older generations;
- alternative branding;
- catalog-unknown devices that still expose the private regulator API.

## Current Implementation Divergence

The current gateway code still uses a prefix-oriented shortcut in `refreshDiscovery()`.

That implementation detail is code debt. It must not be read as the semantic contract.

The contract is capability-first:

- prove B524;
- then enrich identity.

## Cross-Links

- Structural decision catalog: [`../protocols/ebus-vaillant-B524-structural-decisions.md`](../protocols/ebus-vaillant-B524-structural-decisions.md)
- Structure discovery flow: [`semantic-structure-discovery.md`](./semantic-structure-discovery.md)
- Configuration gates: [`semantic-configuration-gates.md`](./semantic-configuration-gates.md)
- Identity enrichment: [`regulator-identity-enrichment.md`](./regulator-identity-enrichment.md)
