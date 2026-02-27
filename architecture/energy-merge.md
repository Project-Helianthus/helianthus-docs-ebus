# Energy Merge Contract v2

This page documents the deterministic energy merge algorithm used by the gateway to combine energy data from multiple sources.

## Data Sources

Energy data arrives via two paths:

| Source | Confidence | Origin |
| --- | --- | --- |
| **Broadcast** | Low | eBUS bus broadcast events (passive listening) |
| **Register** | High | Direct B5/24 register reads from the VRC controller (BASV2 device, active polling, 5-minute interval) |

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

## Register-Primary Ingestion (B5/24)

The register-primary path reads cumulative energy totals from the VRC controller (BASV2 device) using the B5/24 extended register protocol:

```text
Request:  B5.24 read selector [opcode=0x02, op=0x00, group=0x00, instance=0x00, addr_lo, addr_hi]
Response: ULG (unsigned 32-bit LE integer, value in kWh)
```

### Registers

| Addr | TSP Name | Channel | Usage |
| --- | --- | --- | --- |
| 0x56 | PrFuelSumHc | gas | climate |
| 0x57 | PrEnergySumHc | electricity | climate |
| 0x58 | PrEnergySumHwc | electricity | hot_water |
| 0x59 | PrFuelSumHwc | gas | hot_water |

These are cumulative all-time totals from the VRC 720f TSP (15.720). Solar registers are not available.

Total: **4 register reads** per refresh cycle.

### Merge Key Mapping

Each register value is written to 3 merge keys:

| Period | YearKind | Value |
| --- | --- | --- |
| year | current | all-time total from VRC |
| year | previous | 0 (lock) |
| day | (empty) | 0 (lock) |

The zero-locks for `day` and `year/previous` prevent broadcast double-counting, since the all-time total already includes those periods. The ULG sentinel `0xFFFFFFFF` is rejected as invalid.

### Lifecycle

- Energy register reads are scheduled every 5 minutes (configurable via `-semantic-energy-interval`).
- The refresh is gated on: VRC controller discovered (`p.controller != 0`).
- Each successful read calls `ApplyEnergyFromRegister()` with `EnergySourceRegister`, feeding through the merge truth table.
- Failed reads are logged with a failure count but do not block other reads.

### Source Precedence

Once a register value has been written for a given merge key, broadcast updates for the same key are permanently rejected (until the merge store is reset). This ensures register-primary data integrity even when broadcast traffic is available.

### Historical Note

Prior to PR #232, the gateway attempted B5/16 register reads from the BAI device. BAI responds to B5/16 but returns 0 kWh (boilers don't store cumulative energy). The VRC controller stores energy data via B5/24 registers, not B5/16.

## Cross-Links

- EnergyTotals types: `graphql/semantic.go`
- Merge implementation: `graphql/energy_merge.go`
- Integration: `graphql/semantic_live.go` (`applyEnergyPoint`)
- Register ingestion: `cmd/gateway/semantic_vaillant.go` (`refreshEnergy`, `readB524Uint32LE`)
- VRC energy TSP: `helianthus-ebus-vaillant-productids` (15.720.tsp, opcodes 0x4E–0x5D)
