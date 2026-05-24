# Semantic Startup FSM

This page documents the startup behavior for semantic data publication in `helianthus-ebusgateway`.

Goal: publish deterministic semantic data during startup without pretending cached values are live.

## State Machine

```mermaid
stateDiagram-v2
  [*] --> BOOT_INIT

  BOOT_INIT --> CACHE_LOADED_STALE: first cache epoch
  BOOT_INIT --> LIVE_WARMUP: first live epoch

  CACHE_LOADED_STALE --> LIVE_WARMUP: first live epoch
  LIVE_WARMUP --> LIVE_READY: live_ready_criteria met

  BOOT_INIT --> DEGRADED: boot_live_timeout
  CACHE_LOADED_STALE --> DEGRADED: boot_live_timeout
  LIVE_WARMUP --> DEGRADED: boot_live_timeout

  DEGRADED --> LIVE_WARMUP: first live epoch after degraded
  DEGRADED --> LIVE_READY: live_ready_criteria met after degraded
```

## Transition Table

| From | To | Trigger | Notes |
| --- | --- | --- | --- |
| `BOOT_INIT` | `CACHE_LOADED_STALE` | first cache snapshot applied | cache is exposed as stale bootstrap data |
| `BOOT_INIT` | `LIVE_WARMUP` | first live semantic update | first confirmed live signal |
| `CACHE_LOADED_STALE` | `LIVE_WARMUP` | first live semantic update | stale cache begins replacement by live stream |
| `LIVE_WARMUP` | `LIVE_READY` | `live_ready_criteria` satisfied | requires `live_epoch >= 2` and live-backed updates for every published stream |
| `BOOT_INIT`/`CACHE_LOADED_STALE`/`LIVE_WARMUP` | `DEGRADED` | `boot_live_timeout` elapsed | startup did not reach live-ready in time |
| `DEGRADED` | `LIVE_WARMUP` | first live semantic update after degraded | recovery started |
| `DEGRADED` | `LIVE_READY` | `live_ready_criteria` satisfied after degraded | same stream-aware readiness criteria used during normal startup |

## Epoch Semantics

- `cache_epoch` increments when cache-backed semantic payload is applied.
- `live_epoch` increments when live semantic payload is applied from zone/DHW refresh paths.
- `cache_epoch` and `live_epoch` are tracked independently.
- `live_epoch` is authoritative for startup readiness:
  - `live_epoch = 0`: no live signal yet.
  - `live_epoch = 1`: warmup only.
  - `live_epoch >= 2`: candidate for live-ready; stream criteria still apply.
- `LIVE_READY` additionally requires live updates for all published semantic streams:
  - if zones were published, at least one zones update must be live-backed;
  - if DHW was published, at least one DHW update must be live-backed.
  - repeated live updates on only one stream keep runtime in `LIVE_WARMUP`.

### Source classification notes

- Persistent semantic snapshot preload (`semantic_cache.json`) is cache-backed and only advances `cache_epoch`.
- In `ebusd-tcp` fallback mode, successful `grab result all` hydration for zones/DHW is classified as **live** and can advance `live_epoch`.
- Energy broadcast ingestion updates `energyTotals` but does **not** advance startup `live_epoch` and does not trigger startup phase transitions.

## M4 L1 Startup Priming

After B524 semantic root discovery succeeds, the gateway runs a bounded startup
priming pass before the normal periodic semantic loop. The purpose is L1 plane
availability: every MCP semantic plane required by the M4 O1 gate must publish a
non-null payload within 60 seconds of add-on startup when live bus access is
working.

Startup priming is a publication-ordering rule, not a transport or protocol
arbitration change. It does not change `bus.Send`, the adaptermux first-byte
arbitration behavior, or the Direction C F-NEW-29 predicate documented in
[`adaptermux/first-byte-arbitration-revalidation.md`](./adaptermux/first-byte-arbitration-revalidation.md).

The priming pass is intentionally bounded:

- run only after a B524-capable semantic root has been found;
- use short per-probe timeouts so a slow register family cannot monopolize the
  startup window;
- release source-selection semantic bootstrap as soon as active source evidence
  exists; physical identity confirmation and full-range recovery must not hold
  the semantic L1 barrier open;
- retry the DHW singleton path before the startup zone sweep so a transient
  first DHW miss cannot leave the `dhw` plane null while the heavier structural
  scan runs;
- publish lightweight structural or skeleton payloads for planes whose full
  detail is filled by later periodic pollers;
- seed radio-device availability from already-known regulator/FM5 registry
  evidence when remote slot scans have not completed yet;
- allow the first coherent zone-discovery result to publish zones during
  startup, then return zone lifecycle control to the normal presence hysteresis
  FSM.

Physical device identity enrichment is not part of the L1 semantic gate. Serial
number retry/enrichment may refine registry identity after startup, but it must
not consume the first 60 seconds needed to publish the required MCP semantic
planes. The L1 gate requires non-null publication for zones, circuits, DHW,
radio devices, FM5 mode, solar, cylinders, schedules, energy totals, system,
adapter info, and boiler status.

The normal steady-state pollers remain authoritative for complete values,
freshness, removal, and downgrade behavior. For example, schedules may become
non-null during startup before the heavier schedule read cycle fills detailed
entries, and FM5-related planes may publish a bounded startup interpretation
before later system/radio/solar/cylinder reads refine or downgrade the model.

## Steady-State Poll Scheduling

The Vaillant semantic poller uses a single serialized task scheduler for active
semantic reads. Each recurring task family has a stable scheduler key:
regulator capability, discovery, config, state, circuits, system, radio
devices, energy, schedules, and the three boiler-status tiers.

The scheduler MUST coalesce duplicate queued or running tasks with the same key.
If a new tick arrives while the same task family is pending, the queued task is
kept once and its priority may be raised. If the same task family is already
running, at most one deferred rerun is kept for the next available task slot and
additional same-key signals merge into that rerun. This is a load-shaping rule:
it prevents bus contention or slow responders from creating an unbounded backlog
of identical B524/B509 sweeps while preserving edge-triggered refresh signals.

Coalescing does not change any eBUS wire format, `bus.Send` behavior,
adaptermux arbitration, retry classification, or semantic merge semantics. The
next successful execution of a task family remains authoritative for live values;
partial results are still merged according to the incremental freshness rules
below.

Broad B524 backfill tasks must also avoid repeating full topology sweeps when a
stable live inventory already exists. Circuit refresh is the reference pattern:
startup and periodic rediscovery may scan the full documented circuit instance
range, but normal steady-state refreshes operate on the known active circuit
instances until the rediscovery interval expires. This preserves detection of
new or removed circuits without making every config refresh pay the full
`GG=0x02` scan cost. The long rediscovery interval starts only after the full
documented range has produced definitive active/inactive answers; partial scans
retry on the regular configuration cadence. Critical state and boiler fast-tier
reads are not delayed by this backfill pacing rule.

Steady-state zone and DHW polling is split by freshness class:

- The 60-second state task is reserved for live-critical values: zone current
  temperature, target temperature, humidity, operating mode, special function,
  valve/HVAC action, and DHW current/target temperature plus DHW mode fields.
- Slow or rarely changing selectors run on the config cadence: zone quick-veto
  expiry/details, holiday windows, room-temperature-zone mapping, per-zone
  associated circuit type, and DHW holiday dates.
- The boiler fast tier may project DHW fields from the already-refreshed DHW
  semantic snapshot; it must not duplicate the DHW B524 state reads just to
  populate the boiler-status view.

This split bounds gateway-originated `0x7F -> 0x15` B524 traffic after startup
without weakening the L1 startup gate. Startup-specific priming paths may still
perform direct reads for the planes needed to become non-null within 60 seconds.

## Incremental Merge and Freshness Semantics

Zone and DHW updates are merged incrementally, not replaced wholesale.

- Merge is field-granular for zone config/state and DHW state/config slices.
- For each polling slice, only attempted fields participate in merge decisions.
- Attempted fields with valid values overwrite previous values and are marked fresh.
- Attempted fields without valid values keep last-known values and are marked stale.
- Unattempted fields are left unchanged (no implicit stale transition).

Operational consequences:

- Partial read failures do not wipe previously valid semantic values.
- Empty/nil partial snapshots do not remove zone or DHW entities by themselves.
- Zone visibility/removal remains controlled by zone presence hysteresis FSM.
- DHW is durable under transient cache-only cycles and expires after `-semantic-dhw-stale-ttl`.
- Startup phase progression remains driven by stream-level live/cache epochs.

Implementation note:

- Field freshness is currently tracked in runtime semantic state and used for merge/lifecycle decisions.
- GraphQL currently exposes the merged semantic values; field-level stale flags are not yet separately exposed as API fields.

## Persistent Cache Schema

- Runtime cache file path is configurable via `-semantic-cache-path` (default `./semantic_cache.json`).
- Current schema is **v2**:
  - top-level `schema_version: 2`
  - `metadata.persisted_at`
  - semantic payload: `zones[]` and optional `dhw`
- Legacy **v1** cache payloads (no `schema_version`) are migrated on load:
  - load as v1, convert to v2, rewrite atomically, continue startup using migrated data.
- Unknown schema versions are rejected as invalid cache (runtime continues without preload).

## Timeout Semantics

- Runtime bootstrap timeout is controlled by `-boot-live-timeout` (default `2m`).
- If timeout elapses before live-ready, runtime transitions to `DEGRADED`.
- `DEGRADED` does not block recovery; later live updates can still move runtime to warmup/live-ready.

## API and Runtime Cross-Links

- GraphQL runtime notes: [`api/graphql.md`](../api/graphql.md#semantic-startup-runtime-contract)
- Runtime and wiring context: [`architecture/overview.md`](./overview.md#semantic-startup-runtime)
- Semantic read breaker behavior for B524 polling: [`architecture/semantic-read-circuit-breaker.md`](./semantic-read-circuit-breaker.md)
- Zone presence hysteresis state machine: [`architecture/zone-presence-fsm.md`](./zone-presence-fsm.md)
- DHW durability and expiry lifecycle: [`architecture/dhw-freshness-fsm.md`](./dhw-freshness-fsm.md)
- B524 semantic root discovery: [`architecture/b524-semantic-root-discovery.md`](./b524-semantic-root-discovery.md)
- Regulator identity enrichment: [`architecture/regulator-identity-enrichment.md`](./regulator-identity-enrichment.md)
- HA consumer behavior: [`development/ha-integration.md`](../development/ha-integration.md)
