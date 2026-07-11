Canonical source: this page.

# Shared Registry Boundary

## Authority

The shared registry is protocol-neutral. Protocol adapters register raw device
identity, observations, evidence, and candidate correlations through versioned
contracts; they do not create canonical semantic facts by naming a native
field like an existing leaf.

Canonical semantic identity is the tuple of semantic path, schema version, and
accepted provenance policy. Runtime ids, protocol addresses, native paths, and
vendor labels remain source identity. They may participate in provenance but
cannot become cross-runtime registry keys.

## Write Boundary

An adapter may write only its native raw namespace and evidence references.
Candidate correlation records live outside stable registry projections. Only a
locked per-leaf promotion decision may create or update a canonical semantic
leaf, and that decision records all contributing sources and conflict policy.

Partial runtime failure preserves last-known valid leaves according to their
stale policy. It does not replace a device, zone, or service subtree. Conflicts
remain explicit and attributable; runtime order, arrival time, and adapter
priority do not silently choose semantic authority.

## Separation

Protocol behavior belongs to its protocol documentation owner. Runtime trust,
persistence, and lifecycle belong to that runtime's architecture owner. Native
API schema and examples belong to its API owner. This page owns only the
language-neutral registry boundary shared by every runtime.
