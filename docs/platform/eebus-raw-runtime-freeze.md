# eeBUS Raw Runtime Contract Freeze

Status: M3.5 companion draft. This page must not merge until the exact public
contract table and replay hashes are pinned to the final `helianthus-eebusreg`
MSP-035 head.

Canonical source: this page.

Implementation companion:
[`Project-Helianthus/helianthus-eebusreg#18`](https://github.com/Project-Helianthus/helianthus-eebusreg/issues/18).

## Freeze Boundary

MSP-035 freezes only these versioned, immutable raw data shapes:

1. the redacted raw runtime identity document;
2. the raw snapshot envelope; and
3. the evidence object carried by that envelope.

The final revision of this page will list every exported field, canonical JSON
name, enum value, ordering key, validation rule, and version identifier. The
implementation and documentation must change together before either companion
PR can merge.

## Deterministic Replay

For identical version, mask tier, effective authorization scope, raw input, and
data timestamp, replay must produce identical canonical JSON and `data_hash`.
Collection order must not affect output. Identity entries, snapshot entries,
evidence objects, and unknown-field collections use contract-defined stable
ordering before serialization and hashing.

Capture time is metadata and is not part of the data hash. A data timestamp is
part of the hashed content. Hash comparisons are invalid across contract
versions, mask tiers, authorization scopes, tools, or snapshot scopes.

## Public Boundary

The frozen API contains Helianthus-owned value types only. No exported type,
function signature, field, or constant may expose an `enbility/*`, SHIP, or
SPINE implementation type. Unmapped protocol values remain explicit unknown
raw evidence and are never silently normalized into semantic values.

Raw eeBUS fields must not enter `ebus.v1.*`, the eBUS registry, semantic
projections, GraphQL, Portal, Home Assistant, command routing, or write paths.

## Explicitly Unfrozen

This milestone does not freeze or grant authority to:

- trust or pairing decisions and mutations;
- lifecycle start, shutdown, reconnect, or readiness behavior;
- availability or freshness guarantees;
- administration APIs or persistence policy;
- the final `eebus.v1.*` MCP schema;
- semantic identities, promoted leaves, or consumer contracts.

Those surfaces require their later plan rows and independent gates. Adding one
of them to the MSP-035 public API is a contract violation, not an additive
extension of this freeze.

## Publication And Evidence

This page contains only project-owned architecture and observable contract
rules. It must not quote or reproduce restricted eeBUS specifications. Public
claims must trace to publishable issue, test, or redacted evidence identifiers.

