# Energy Merge Contract v2

This page documents the deterministic energy merge algorithm used by the gateway to combine energy data from multiple sources.

## Data Sources

Energy data arrives via two paths:

| Source | Confidence | Origin |
| --- | --- | --- |
| **Broadcast** | Low | eBUS bus broadcast events (passive listening) |
| **Register** | High | Direct B524 register reads from the regulator (active polling) |

## Merge Key

Each energy data point is uniquely identified by a composite key:

```text
(channel, usage, period, year_kind)
```

- **Channel:** `gas`, `electricity`, `solar`
- **Usage:** `hot_water`, `climate` (canonicalized from `heating`/`cooling`)
- **Period:** `day`, `year`
- **YearKind:** empty for day; `previous` or `current` for year

Usage canonicalization: both `heating` and `cooling` bus values map to the single `climate` series in the `EnergyChannel` struct. This prevents nondeterministic snapshot writes from separate keys targeting the same output field.

Maximum unique keys: 3 channels x 2 usages x 3 periods = **18 canonical data points**.

## Merge Truth Table

| Existing Source | Incoming Source | Incoming Newer? | Action |
| --- | --- | --- | --- |
| none | any | - | **accept** |
| broadcast | register | any | **accept** (register always wins) |
| broadcast | broadcast | yes | **accept** |
| broadcast | broadcast | no | **reject** (monotonic) |
| register | register | yes | **accept** |
| register | register | no | **reject** (monotonic) |
| register | broadcast | any | **reject** (broadcast never overwrites register) |

**Key invariants:**

1. **Source confidence:** Register data always takes precedence over broadcast data, regardless of timestamps.
2. **Monotonic ingest:** Within the same source, only strictly newer timestamps are accepted. Equal timestamps are rejected.
3. **No data loss:** Rejected writes do not affect the existing stored value.

## Snapshot and Publish

After each accepted merge, the store rebuilds a full `EnergyTotals` snapshot. The publish to the `LiveSemanticProvider` is **revision-gated**: each accepted write increments a monotonic revision counter, and the provider only updates its cached snapshot if the offered revision is >= its current revision. This prevents stale snapshots from concurrent callers from regressing the published state.

## Thread Safety

The `energyMergeStore` has its own `sync.RWMutex`, separate from the `LiveSemanticProvider.mu`. Lock ordering is:

1. `energyMerge.mu` (for Apply/Snapshot)
2. `provider.mu` (for publishing the snapshot)

These locks are never held simultaneously — `Apply` and `Snapshot` complete before `provider.mu` is acquired.

## Cross-Links

- EnergyTotals types: `graphql/semantic.go`
- Merge implementation: `graphql/energy_merge.go`
- Integration: `graphql/semantic_live.go` (`applyEnergy`)
- Register-primary energy ingestion (future): issue #196
