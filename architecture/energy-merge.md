# Energy Merge Contract v2

This page documents the deterministic energy merge algorithm used by the gateway to combine energy data from multiple sources.

## Data Sources

Energy data arrives via two paths:

| Source | Confidence | Origin |
| --- | --- | --- |
| **Broadcast** | Low | eBUS bus broadcast events (passive listening) |
| **Register** | High | Direct B5/16 register reads from the boiler (BAI device, active polling, 5-minute interval) |

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

## Register-Primary Ingestion (B5/16)

The register-primary path reads energy statistics directly from the boiler (BAI device) using the B5/16 protocol:

```text
Request:  [period, source, usage]
Response: IEEE 754 float32 LE (value in Wh, converted to kWh)
```

### Parameters

| Byte | Name | Values |
| --- | --- | --- |
| period | Time range | 0 = today, 1 = current year, 2 = previous year |
| source | Energy source | 0 = gas, 1 = electricity, 2 = solar |
| usage | Energy usage | 0 = climate (heating/cooling), 1 = hot_water |

Total: 3 × 3 × 2 = **18 register reads** per refresh cycle.

### Hardware Gating

B5/16 energy stats are only available on devices with hardware version >= 7603. The gateway checks for the `get_energy_stats` method in the target device's (BAI) registry planes before attempting reads.

### Lifecycle

- Energy register reads are scheduled every 5 minutes (configurable via `-semantic-energy-interval`).
- The refresh is gated on: BAI device discovered (via `findDeviceAddressByPrefix`) AND regulator capability is `ControllerPresent`.
- Each successful read calls `ApplyEnergyFromRegister()` with `EnergySourceRegister`, feeding through the merge truth table.
- Failed reads are logged with a failure count but do not block other reads.

### Source Precedence

Once a register value has been written for a given merge key, broadcast updates for the same key are permanently rejected (until the merge store is reset). This ensures register-primary data integrity even when broadcast traffic is available.

## Cross-Links

- EnergyTotals types: `graphql/semantic.go`
- Merge implementation: `graphql/energy_merge.go`
- Integration: `graphql/semantic_live.go` (`applyEnergyPoint`)
- Register ingestion: `cmd/gateway/semantic_vaillant.go` (`refreshEnergy`, `readB516Value`)
- B5/16 protocol template: `helianthus-ebusreg/vaillant/heating/energy.go`
