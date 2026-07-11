Canonical source: this page.

# Promotion And Consumer Contract

## Per-Leaf Gate

Promotion is per-leaf, never per device, runtime, candidate bundle, or protocol.
Each leaf requires a locked dossier with exact source identity, versioned
comparator, raw evidence, deterministic replay, coexistence evidence, stale and
conflict policy, and terminal negative-state handling.

`planned` and `candidate` material is not canonical semantic data. Candidate
material may be inspected only through an explicitly candidate output and must
remain absent from stable navigation, search, sitemap, versioned bundles,
release bundles, registry projections, and consumer APIs. `withdrawn` material
is never consumer-visible and requires cleanup.

## Delivery Order

After a dossier locks a leaf, delivery remains serialized:

1. A read-only MCP prototype exposes the raw and promoted views with provenance.
2. GraphQL parity freezes the stable consumer schema for that leaf.
3. Portal adopts the frozen GraphQL shape.
4. Home Assistant adopts the same stable shape after Portal validation.

One consumer cannot justify promotion for another. GraphQL, Portal, and Home
Assistant must not infer or rename an unpromoted native field. A failed or
expired gate removes candidate outputs and cannot leave a stale consumer link.

## Mutable Leaves

Write support is a separate gate after read promotion. It requires explicit
authorization scope, command ownership, optimistic and observed state rules,
replay-safe idempotency, failure compensation, and a runtime-specific safety
review. Read promotion alone never authorizes a write.
