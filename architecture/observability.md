# Observability Reference

This page documents the runtime metrics and structured log markers available for debugging and monitoring.

## Metrics Endpoint

All metrics are exposed via Go's `expvar` package at `/debug/vars` (JSON format).

## Metric Reference

### Startup FSM

| Metric | Type | Description |
| --- | --- | --- |
| `semantic_startup_phase_transitions_total` | map | Count of phase transitions, keyed by `"FROM->TO"` |
| `semantic_startup_current_phase` | string | Current startup phase (BOOT_INIT, CACHE_LOADED_STALE, LIVE_WARMUP, LIVE_READY, DEGRADED) |
| `semantic_cache_epoch` | int | Current cache epoch counter |
| `semantic_live_epoch` | int | Current live epoch counter |

### Zone Presence

| Metric | Type | Description |
| --- | --- | --- |
| `semantic_zone_presence_transitions_total` | map | Count of zone presence transitions, keyed by `"FROM->TO"` |
| `semantic_zone_count` | int | Current number of visible zones |

### DHW Lifecycle

| Metric | Type | Description |
| --- | --- | --- |
| `semantic_dhw_stale_expiry_total` | int | Count of DHW stale expiry events |
| `semantic_dhw_updates_total` | int | Count of DHW update events |

### Energy Merge

| Metric | Type | Description |
| --- | --- | --- |
| `semantic_energy_merges_total` | map | Count of accepted merges, keyed by source (`"broadcast"`, `"register"`) |
| `semantic_energy_rejections_total` | map | Count of rejected merges, keyed by reason (`"monotonic"`, `"source_downgrade"`) |

### Regulator State

| Metric | Type | Description |
| --- | --- | --- |
| `semantic_regulator_state` | string | Current regulator absence state (PRESENT, ABSENCE_GRACE, ABSENT) |
| `semantic_regulator_transitions_total` | map | Count of regulator state transitions |

### Bus Health

| Metric | Type | Description |
| --- | --- | --- |
| `semantic_bus_collisions_total` | int | Count of bus collision events during scan |

### Read Circuit Breaker

| Metric | Type | Description |
| --- | --- | --- |
| `semantic_read_breaker_transitions_total` | map | Count of breaker state transitions, keyed by `"FROM->TO"` |
| `semantic_read_breaker_suppressed_total` | map | Count of suppressed reads, keyed by breaker state |

## Troubleshooting Mapping

| Symptom | Metrics to Check | What to Look For |
| --- | --- | --- |
| Zones not appearing | `semantic_zone_count`, `semantic_zone_presence_transitions_total` | Zone count = 0, no PRESENT transitions |
| Stale data after boot | `semantic_startup_current_phase`, `semantic_live_epoch` | Phase stuck in CACHE_LOADED_STALE, live_epoch = 0 |
| DHW disappearing | `semantic_dhw_stale_expiry_total`, `semantic_dhw_updates_total` | High expiry count relative to updates |
| Energy not updating | `semantic_energy_merges_total`, `semantic_energy_rejections_total` | High rejection count, check "source_downgrade" |
| Regulator lost | `semantic_regulator_state`, `semantic_regulator_transitions_total` | State = ABSENT, transitions show PRESENT→ABSENCE_GRACE→ABSENT |
| Bus communication issues | `semantic_bus_collisions_total`, `semantic_read_breaker_transitions_total` | High collision count, breaker in OPEN state |

## Cross-Links

- Startup FSM: [`architecture/startup-semantic-fsm.md`](./startup-semantic-fsm.md)
- B524 semantic root discovery: [`architecture/b524-semantic-root-discovery.md`](./b524-semantic-root-discovery.md)
- Regulator identity enrichment: [`architecture/regulator-identity-enrichment.md`](./regulator-identity-enrichment.md)
- Energy merge: [`architecture/energy-merge.md`](./energy-merge.md)
- Zone presence FSM: [`architecture/zone-presence-fsm.md`](./zone-presence-fsm.md)
- DHW freshness: [`architecture/dhw-freshness-fsm.md`](./dhw-freshness-fsm.md)
- Adversarial matrix: [`architecture/adversarial-matrix.md`](./adversarial-matrix.md)
