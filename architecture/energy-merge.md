# Energy Merge Contract v2

This page documents the deterministic energy merge algorithm used by the gateway to combine energy data from multiple sources.

## Data Sources

Energy data arrives via two paths:

| Source | Confidence | Origin |
| --- | --- | --- |
| **Broadcast** | Low | eBUS bus broadcast events (passive listening) |
| **Register** | High | Direct B5/24 register reads from the regulator-family controller (active polling, 5-minute interval) |

## Merge Key

The merge store holds two kinds of window:

- **Dated windows**, identified by the absolute window they measure:

  ```text
  (channel, usage, period, year, month, day)
  ```

  A day key carries year, month and day; a month key carries year and month with day zero, `(year, month, 0)`; a year key carries the year only. Unused components are zero.
- **Lifetime windows**, identified by `(channel, usage)` with period `all` and no date. A lifetime window is the cumulative all-time total read from the register path. It is never keyed by a reference year.

Common to both kinds:

- **Channel:** `gas`, `electricity`, `solar`
- **Usage:** `hot_water`, `climate` (canonicalized from `heating`/`cooling`)

No key holds a relative label. The B516 selector carries an absolute date and a dated key stores that date, so a stored key never goes stale when the calendar year or day changes. A lifetime key has no date to go stale.

Usage canonicalization: both `heating` and `cooling` bus values map to the single `climate` series in the `EnergyChannel` struct. This prevents nondeterministic snapshot writes from separate keys targeting the same output field.

### Public Two-Slot Projection

The public yearly series keeps its two-slot shape (current year and previous year). It is a projection of the stored windows, rebuilt on each live accessor call against the current gateway clock; it is not fixed at merge time. A snapshot is also built after an accepted merge and cached by the provider, but live readers are not served that cached copy. Every live reader (the GraphQL query root, the live MCP tools, the portal and the semantic inventory) obtains the energy totals through one provider call that builds the snapshot from the store at that moment. Consequently a day, month or year boundary is reflected on the next live read even when no merge has happened since (all register reads failing, or a quiet bus), and the only thing that ages without a merge is the freshness metadata. Two surfaces are frozen by design and do not recompute: a captured MCP snapshot returns the energy totals as projected at capture time for the snapshot's lifetime (five-minute TTL), so a snapshot captured before a boundary keeps the pre-boundary projection until it expires; and a GraphQL subscription event (`energy`, `energy_update`) carries the projection computed when the event was built. Consumers of those two surfaces read the projection as of the capture or event time. Two rules apply:

| Stored window | Public position |
| --- | --- |
| dated year, `year` equals the reference year | current slot |
| dated year, `year` equals the reference year minus one | previous slot |
| dated month, `(year, month)` equals the reference month | current month position |
| dated month, `(year, month)` equals the month before the reference month (December of the previous year when the reference month is January) | previous month position |
| dated day equal to the reference date | today value |
| lifetime total | compatibility mapping: current slot; the previous slot and today are held at zero |

The public monthly series has the same two-slot shape (previous month and current month). Lifetime totals have no monthly mapping. The reference-date rule applies to dated values and the compatibility mapping applies to lifetime values. The lifetime mapping does not depend on the reference year, so it holds unchanged across a year rollover.

Lifetime projection truth table (reference date 2027-01-01). Slots: `Yearly[1]` = current year, `Yearly[0]` = previous year, `Today`. `L` = register lifetime total (`period=all`). A dated point is keyed by its absolute window; register beats broadcast. "Among register points the later ingest wins" applies to points of the same window key. Between the lifetime total and a dated register point of a different key the slot rules decide: the current slot shows the dated register current-year point only if its ingest is newer than the lifetime total, otherwise `L`; for the previous slot and today, a register-sourced dated point outranks the lifetime zero regardless of ingest order; a broadcast-sourced dated point never displaces the lifetime mapping. Every row is intended; provenance is shown per slot.

| Case | Yearly[1] current | Yearly[0] previous | Today |
|---|---|---|---|
| Lifetime only | L (register) | 0 (register, lifetime meta) | 0 (register, lifetime meta) |
| L + dated register current-year point, newer ingest than L | the dated point (register) | 0 (register) | 0 (register) |
| L + dated register current-year point, older ingest than L | L (register) | 0 (register) | 0 (register) |
| L + dated broadcast current-year point | L (register; broadcast never wins) | 0 (register) | 0 (register) |
| L + dated previous-year point | L (register) | register-sourced: that value (register); broadcast-sourced: 0 (register) | unchanged |
| L + dated day point for the reference day | L (register) | 0 (register) | register-sourced: that value (register); broadcast-sourced: 0 (register) |
| Dated only (no L) | dated current point (own provenance) or 0/none | dated previous point (own provenance) or 0/none | dated day point for the reference day (own provenance) or 0/none |

Monthly rollover: when the reference month advances, the key that was the current month becomes the previous month and the key that was the previous month leaves the projection. A month key stays stored under its own `(year, month)` and is never relabelled.

A stored dated window outside these positions is not part of the snapshot. A value for an old year that is received again updates its own dated key and appears in the projection only while that year is still the reference year or the year before it.

### Freshness and Persistence

Calendar projection and freshness are separate. A lifetime total persists when register refreshes fail, including across a year rollover: its value stays in the current position, while its freshness metadata turns stale once the point is 45 minutes old. A stale register value still takes precedence over broadcasts for the same window. Consumers must read the calendar projection and the freshness metadata separately and must not treat a stale value as absent or a fresh value as belonging to a different window.

Structural capacity: up to **30 dated points** (3 channels x 2 usages x 5 slots: day, previous year, current year, previous month, current month) plus up to **6 lifetime points** (3 channels x 2 usages).

Reachable maxima under the documented query coverage (no solar register queries; monthly broadcasts are not consumed): **26 dated points**, being 18 broadcast day and yearly points (3 channels x 2 usages x day, previous year, current year) plus 8 register monthly points (2 channels x 2 usages x 2 months), and **4 lifetime points** (2 channels x 2 usages). Fixtures should use the reachable bounds.

## Broadcast Date Mapping

The B516 energy selector date is a packed absolute date; the packed-date layout and its worked decode are documented in [B516 energy statistics](../protocols/vaillant/ebus-vaillant-B516-energy.md) (§3, §4.3, §6.1), which is the native authority. The decoder publishes the date as absolute components; helianthus-ebusreg [#172](https://github.com/Project-Helianthus/helianthus-ebusreg/pull/172) is the decoder implementation evidence and corroborates, but does not establish, the wire contract:

| Field | Validity |
| --- | --- |
| `year` | absolute year (for example `2026`); valid for daily, monthly and yearly windows |
| `month` | valid for daily and monthly windows |
| `day` | valid for the daily window only |

Wire conclusions behind this mapping. The B516 page states these without a Proven label, so they are labelled Hypothesis here:

- **Hypothesis:** total requests ignore the packed date, so a total reply carries no date window and an echoed date in a total reply does not identify an energy window; the decoded date fields are therefore invalid for totals. Source: [§4.2](../protocols/vaillant/ebus-vaillant-B516-energy.md#42-system-totals-x0) and the total reply echoing `87 34` in [§6.1](../protocols/vaillant/ebus-vaillant-B516-energy.md#61-worked-evidence-read-only), observed on one installation of one controller family. A capture of total requests with differing date bytes returning identical values, on more than one installation, would settle it.
- **Hypothesis:** the yearly selector carries an absolute year, not a relative qualifier ("current year" and "previous year" are not wire selectors). Source: [§4.3](../protocols/vaillant/ebus-vaillant-B516-energy.md#43-yearly-windows-x3), including the half-year disambiguation note, and the reproducible decode in §6.1. Yearly requests for adjacent and non-adjacent years on more than one installation, with replies that follow the absolute year, would settle it.
- **Unknown:** which years a given regulator answers for ([§4.3](../protocols/vaillant/ebus-vaillant-B516-energy.md#43-yearly-windows-x3), [§11](../protocols/vaillant/ebus-vaillant-B516-energy.md#11-open-questions)).

The decoder publishes only the absolute components above and no relative year qualifier.

The reference date is the gateway process clock read in the process's local calendar (its time zone); ingest, each register acquisition and every live read use that same clock. The contract assumes that calendar matches the one the regulator uses for its energy windows. If the two differ, then between the two midnights a valid daily broadcast is dropped by the strict date match below, and the month and year projection rolls over at the gateway's midnight while the controller's relative monthly registers roll over at its own; making the calendar zone explicit and consistent is tracked in gateway #1022.

The merge rule takes a reference date (the gateway clock at ingest) and decides whether a broadcast is accepted and under which dated key:

| Period | Condition on the decoded date | Resulting key |
| --- | --- | --- |
| day | `year`, `month` and `day` are all valid and all equal to the reference date | day key dated with the reference date |
| year | `year` equals the reference year or the reference year minus one | year key dated with that `year` |

Anything else is dropped without touching the stored value:

- a daily value whose `year`, `month` or `day` is missing, invalid or different from the reference date (a missing component is never treated as a match);
- a yearly value whose `year` is missing, invalid, or neither the reference year nor the one before it;
- any period other than `day` and `year`. Monthly broadcasts are not consumed by this merge.

When a day key is accepted, day points of the same channel and usage dated earlier are pruned so day identities do not accumulate.

Because the year is absolute, the same selector bytes always name the same calendar year, and a value received again for an older accepted year updates that year's own key.

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

After each accepted merge, the store rebuilds a full `EnergyTotals` snapshot. The cached copy held by the `LiveSemanticProvider` is **revision-gated**: each accepted write increments a monotonic revision counter, and the provider only updates its cached snapshot if the offered revision is >= its current revision. This prevents stale snapshots from concurrent callers from regressing the cached state.

Live readers are not served the cached copy. Every live resolver calls the provider's energy-totals accessor, which builds the snapshot from the store against the current gateway clock on each call, so the two-slot projection (see [Public Two-Slot Projection](#public-two-slot-projection)) is rebuilt on every live read. Captured MCP snapshots and GraphQL subscription events are the exceptions described there: they carry the projection as of capture or event time.

## Thread Safety

The `energyMergeStore` has its own `sync.RWMutex`, separate from the `LiveSemanticProvider.mu`. Lock ordering is:

1. `energyMerge.mu` (for Apply/Snapshot)
2. `provider.mu` (for publishing the snapshot)

These locks are never held simultaneously — `Apply` and `Snapshot` complete before `provider.mu` is acquired.

## Register-Primary Ingestion (B5/24)

The register-primary path reads cumulative energy totals from the regulator-family controller using the B5/24 extended register protocol:

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

These four addresses are the lifetime (all-time) totals. The gateway issues no solar register queries, so solar values in the public series come from broadcasts only. This is a statement about the gateway's query coverage, not about native device capability.

These four addresses are the lifetime (all-time) reads. Each acquisition issues **12 register queries**: 4 lifetime, 4 for the current month and 4 for the previous month.

### Merge Key Mapping

Each of the four lifetime register values is a cumulative all-time total, so it is written to the lifetime window of its `(channel, usage)` and not to a dated year key. The projection maps the lifetime window to the current yearly slot and holds the previous slot and today at zero (see [Public Two-Slot Projection](#public-two-slot-projection)). Because the total already includes those periods, the zeros also stop a broadcast value from being counted twice in the public series. The ULG sentinel `0xFFFFFFFF` is rejected as invalid.

Each register acquisition captures one reference time and derives every dated key of that acquisition from it. If the reference clock crosses a month or year boundary while the acquisition is running, the replies read after the crossing are discarded (their relative windows would be mislabelled) and the acquisition stops; the next poll acquires again.

Relative monthly register windows (this month and last month) are always read fresh from the bus and are never served from the scheduler or shadow cache, so a cached value cannot be stored under a different month. Lifetime totals keep the normal cache lifetime.

The eight monthly queries (this month and last month) are not lifetime totals: each is written to a dated month key. The register path keeps its own window labels (all-time, and current/previous month). Where a register read targets a dated window, the label is resolved against the same reference clock to a dated key, so a register value and a broadcast value for the same window share one key and the truth table arbitrates between them. The two paths meet at the stored window, and the public two-slot projection is applied on top of it.

### Lifecycle

- Energy register reads are scheduled every 5 minutes (configurable via `-semantic-energy-interval`).
- The refresh is gated on: regulator-family controller discovered (`p.controller != 0`).
- Each successful read calls `ApplyEnergyFromRegister()` with `EnergySourceRegister`, feeding through the merge truth table.
- Failed reads are logged with a failure count but do not block other reads.

### Source Precedence

Once a register value has been written for a given merge key, broadcast updates for the same key are permanently rejected (until the merge store is reset). This ensures register-primary data integrity even when broadcast traffic is available.

### Historical Note

An earlier gateway revision attempted B5/16 register reads from the boiler-family device. In that setup the reads were answered with 0 kWh, whereas the regulator-family controller answered the energy reads over B5/24. This is an implementation observation from the maintainers' installation, not native evidence about what either device family stores.

## Cross-Links

- EnergyTotals types: `graphql/semantic.go`
- Merge implementation: `graphql/energy_merge.go`
- Integration: `graphql/semantic_live.go` (`applyEnergyPoint`)
- Broadcast date mapping: `graphql/semantic_live.go` (`matchesToday`)
- Dated keys and slot projection: `graphql/energy_merge.go` (`energyWindowKey`, `energySlotFor`, `energyLifetimeKey`); `graphql/semantic_live.go` (`EnergyWindowKey`, `EnergyLifetimeKey`)
- Register ingestion: `cmd/gateway/semantic_vaillant.go` (`refreshEnergy`, `readEnergyRegister`)
- Energy register table: `helianthus-ebus-vaillant-productids` (register addresses 0x4E–0x5D)
