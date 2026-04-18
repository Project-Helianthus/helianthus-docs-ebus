# NM Adopt-and-Extend

Status: Normative
Plan reference: ebus-standard-l7-services-w16-26.locked/00-canonical.md
Canonical SHA-256: 9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305

## Ownership Preface

The locked plan states:

> `ebus_standard` subsumes the locked NM plan via adopt-and-extend
>
> - `ebus-good-citizen-network-management` is superseded by `ebus_standard`.
> - Merged normative docs `#251`, `#253`, `#256` in `helianthus-docs-ebus`
>   remain authoritative. `ebus_standard` M0 inventories them, marks the
>   kept-verbatim sections with attribution, adopts them as subchapters
>   under `ebus_standard` ownership, and adds an ownership preface plus
>   migration appendix.
> - `ebus_standard` M0 does NOT duplicate or rewrite the normative text.
> - The superseded plan transitions to `.maintenance` only after M6b
>   reconciles cross-links, issue map, and canonical IDs.

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.locked/00-canonical.md`, SHA-256
`9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

This document adopts the merged NM documents in place. It does not
modify, restate, or supersede their normative content. Where this
directory adds catalog identity, execution-safety, or provenance policy,
those additions extend the NM documents under the `ebus_standard`
ownership umbrella.

## Adopted Subchapters

| Adopted document | Adopted role under `ebus_standard` | Ownership note |
|---|---|---|
| [`../nm-model.md`](../nm-model.md) | NM runtime model, state machine, wire behavior lanes, L7 classification | Adopted verbatim as the gateway-owned NM runtime model |
| [`../nm-discovery.md`](../nm-discovery.md) | NM-aligned discovery and discovery-to-target-configuration pipeline | Adopted verbatim as the topology evidence and enrollment model |
| [`../nm-participant-policy.md`](../nm-participant-policy.md) | Local participant behavior, address-pair authority, bus-load policy, cycle-time policy | Adopted verbatim as the local participant and load policy |

The NM documents remain authoritative for NM runtime semantics:

- `NMInit -> NMReset -> NMNormal`
- target configuration
- cycle-time monitoring
- self-monitoring
- status chart
- net status
- start flag
- passive/indirect monitoring model
- bus-load bounds and transport blindness behavior

## Extension Points Added by ebus_standard

The locked plan states:

> `NMInit/NMReset/NMNormal`, target configuration, cycle-time monitoring,
> self-monitoring, status chart, net status, and start flag remain owned
> by the gateway runtime as designed in the locked NM plan.
> `0xFF 00/01/02/03/04/05/06` and `07 FF` are catalog entries in
> `ebus_standard`. The gateway NM runtime consumes catalog metadata to
> emit broadcasts and drive responder replies.
> After M4c2 merges, no hand-coded `FF` command handler survives in the
> gateway.

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.locked/00-canonical.md`, SHA-256
`9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

This M0 doc set adds these extension points:

1. `0xFF 00..06` and `0x07 FF` are catalog methods with full identity
   keys.
2. The NM runtime emits or responds through catalog-driven method
   metadata.
3. `system_nm_runtime` is the only caller context allowed to execute the
   first-delivery NM whitelist beyond user-facing read-only invocation.
4. Every allowed `system_nm_runtime` invocation requires structured
   audit logging.
5. Runtime widening of NM wire surfaces requires a future locked plan.

## Migration Appendix

### Current State

The existing NM docs were produced by the
`ebus-good-citizen-network-management` plan and merged before this
`ebus_standard` plan. They remain normative and are not rewritten in
M0_DOC_GATE.

### Migration Target

The migration target is catalog-driven NM wire behavior:

1. Keep the gateway NM runtime state machine and state ownership from
   [`../nm-model.md`](../nm-model.md).
2. Keep the discovery evidence pipeline from
   [`../nm-discovery.md`](../nm-discovery.md).
3. Keep address-pair, bus-load, transport blindness, and cycle-time
   policy from [`../nm-participant-policy.md`](../nm-participant-policy.md).
4. Move `0xFF` and `0x07 FF` wire emission/response selection to
   `ebus_standard` catalog identities.
5. Remove hand-coded `FF` command handlers after catalog-driven runtime
   integration lands in the gateway milestone.

### Traceability Rules

1. Do not edit the adopted NM text to fit catalog terminology.
2. Add cross-links only when a future docs milestone explicitly scopes
   reconciliation.
3. Keep old plan issue references visible until M6b performs the
   `.maintenance` transition.
4. When terminology differs between the adopted NM documents and the
   catalog, preserve both terms and label the mapping rather than
   rewriting history.

