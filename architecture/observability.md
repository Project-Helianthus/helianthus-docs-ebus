# Observability Reference

This page documents the runtime observability signals currently emitted by `helianthus-ebusgateway`.

## HTTP Metrics Surface

- Operator-facing metrics are served as Prometheus text on `-metrics-path` (default `/metrics`).
- The gateway does not mount `/debug/vars` over HTTP.
- Several counters still use Go `expvar` internally; those variables back tests and some `/metrics` synthesis, but they are not a public HTTP surface today.

## Prometheus Metrics (`/metrics`)

### Bus Traffic and Transport Capability

| Metric | Type | Description |
| --- | --- | --- |
| `ebus_observability_transport_info` | gauge | Transport metadata labelled by `scope`, `transport_class`, and `timing_quality`. |
| `ebus_frames_observed_total` | counter | Bounded frame counters labelled by `scope`, normalized `src`/`dst`, `family`, and `frame_type`. |
| `ebus_errors_total` | counter | Bounded error counters labelled by `scope`, `class`, and `phase`. |
| `ebus_frame_bytes_total` | counter | Aggregate request/response byte totals labelled by `scope`, `family`, `frame_type`, and `part`. |
| `ebus_observability_recent_messages` | gauge | Occupancy of the bounded recent-message ring. |
| `ebus_observability_series_budget_overflow_total` | counter | Series-budget overflow events in the bounded observability store. |
| `ebus_bus_busy_seconds_total` | counter | Cumulative passive busy time. Emitted only while passive state is `available` and passive timing is not `unavailable`. |
| `ebus_bus_busy_ratio` | gauge | Recent passive busy ratio for `window=1m|5m|15m|1h`. Emitted only when busy-time tracking is active. |
| `ebus_periodicity_tuple_budget_overflow_total` | counter | Periodicity tuple evictions when the bounded tuple budget is exceeded. |

### Passive Capability and Warmup

| Metric | Type | Description |
| --- | --- | --- |
| `ebus_passive_tap_reconnect_attempts_total` | counter | Passive tap connect attempts. |
| `ebus_passive_tap_reconnect_successes_total` | counter | Successful passive tap connects. |
| `ebus_passive_tap_reconnect_failures_total` | counter | Failed passive tap connects. |
| `ebus_passive_tap_connected` | gauge | Current passive tap connection state (`1` connected, `0` disconnected). |
| `ebus_passive_capability_probe_attempts_total` | counter | Passive capability probe attempts. |
| `ebus_passive_capability_probe_outcomes_total` | counter | Probe outcomes labelled by `outcome=confirmed|withdrawn|timed_out`. |
| `ebus_passive_warmup_state` | gauge | One-hot passive state labelled by `state=unavailable|warming_up|available`. |
| `ebus_passive_capability_unavailable_reason` | gauge | Current passive unavailability reason labelled by `reason=startup_timeout|reconnect_timeout|socket_loss|flap_dampened|unsupported_or_misconfigured|capability_withdrawn`. |
| `ebus_passive_warmup_elapsed_seconds` | gauge | Elapsed time in the current warmup session. |
| `ebus_passive_warmup_completed_transactions` | gauge | Completed passive transactions counted toward the current warmup threshold. |
| `ebus_passive_warmup_required_transactions` | gauge | Required transactions for the current warmup threshold. |
| `ebus_passive_warmup_completion_mode` | gauge | One-hot completion mode labelled by `mode=thresholds_met|fallback_path`. |
| `ebus_passive_warmup_blocker_reason` | gauge | Dominant warmup blocker labelled by `reason=connected_observation_window|completed_transactions|healthy_symbol_ingress|post_reset_settling|startup_outer_window`. |
| `ebus_passive_capability_transitions_total` | counter | Passive capability transitions labelled by `from` and `to`. |

### Dedup and Passive Pipeline Health

| Metric | Type | Description |
| --- | --- | --- |
| `ebus_dedup_degraded_state` | gauge | Current dedup degraded state (`1` degraded, `0` healthy). |
| `ebus_dedup_degraded_total` | counter | Dedup degraded transitions labelled by `reason=fingerprint_emission_failure|observer_panic|epoch_reset|critical_overflow|explicit_discontinuity|dedup_output_overflow`. |
| `ebus_dedup_epoch_resets_total` | counter | Dedup epoch resets. |
| `ebus_dedup_pending_flush_total` | counter | Dedup pending flushes labelled by `reason=capacity|grace_expiry|epoch_reset|critical_overflow`. |
| `ebus_dedup_local_participant_inbound_total` | counter | Passive traffic classified as local-participant inbound. |
| `ebus_passive_fanout_overflow_total` | counter | Passive classified fan-out overflows labelled by `consumer` and `criticality`. |
| `ebus_passive_reconstructor_recoveries_total` | counter | Passive reconstructor recoveries labelled by `reason=unexpected_syn|transport_reset|decode_fault`. |
| `ebus_passive_reconstructor_abandons_total` | counter | Passive reconstructor abandons labelled by `reason` (e.g. `corrupted_request`, `no_response`). |
| `ebus_passive_reconstructor_prefix_resync_skipped_total` | counter | Bytes dropped because no `SymbolSyn` was observed since the previous frame boundary (P6 Layer 1 inter-frame SYN gate). |
| `ebus_passive_reconstructor_invalid_src_class_skipped_total` | counter | Bytes rejected as non-initiator-class in source position (P6 Layer 2 SRC AddressClass validation; direct measure of upstream byte loss). |

## M4 Observe-First Watch Notes

The merged M4 watch stack (`GW-06..GW-09`) introduces policy-carried passive
adjudication behavior. At architecture level:

- family-policy verdicts flow into runtime adjudication, not only into
  fingerprint hashing
- direct-apply-eligible policies and record/invalidate policies are both
  runtime third-party eligible, but with different runtime semantics
- observability-only adjudication remains explicit and does not imply runtime
  application

### B524 Policy Guardrails

- `state_default` wording is descriptor-backed and policy-backed
- retained-active fallback is conservative and depends on retained active
  fingerprint policy evidence (`request_response + state_default`)
- request-shape heuristics alone are not sufficient to promote B524 entries to
  `state_default`

### M5 Deferral

This reference does not freeze watch-summary or scheduler/shadow public
contracts. Those remain an M5 docs-owner concern.

## Internal `expvar` State

These variables exist in-process today but are not mounted as a public HTTP endpoint.

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

### Read Circuit Breaker

| Metric | Type | Description |
| --- | --- | --- |
| `semantic_read_breaker_transitions_total` | map | Count of breaker state transitions, keyed by `"FROM->TO"` |
| `semantic_read_breaker_suppressed_total` | map | Count of suppressed reads, keyed by breaker state |

### Passive Broadcast Supervisor

| Metric | Type | Description |
| --- | --- | --- |
| `observe_first_broadcast_supervisor_state` | string | Current broadcast supervisor state (`healthy` or `degraded`) |
| `observe_first_broadcast_supervisor_transitions_total` | map | Count of supervisor transitions keyed by `"healthy->degraded:<reason>"` and `"degraded->healthy:<reason>"` |
| `observe_first_broadcast_supervisor_faults_total` | map | Count of supervisor faults keyed by fault reason (for example `router_overflow`) |
| `observe_first_broadcast_supervisor_resubscribe_total` | int | Count of broadcast-listener resubscriptions |

### Active/Passive Dedup

| Metric | Type | Description |
| --- | --- | --- |
| `observe_first_dedup_state` | string | Current dedup state (`healthy` or `degraded`) |
| `observe_first_dedup_epoch` | int | Current dedup epoch |
| `observe_first_dedup_epoch_reset_total` | int | Count of dedup epoch resets |
| `observe_first_dedup_pending_flush_total` | map | Count of pending-passive flushes keyed by reason |
| `observe_first_dedup_adjudications_total` | map | Count of passive adjudications keyed by disposition |
| `observe_first_dedup_degraded_transitions_total` | map | Count of degraded transitions keyed by reason |
| `observe_first_dedup_local_participant_inbound_total` | int | Count of local-participant inbound adjudications |

### Bus Health

| Metric | Type | Description |
| --- | --- | --- |
| `semantic_bus_collisions_total` | int | Count of bus collision events during scan |

### Adaptermux Session Frame Pipeline Latency

The gateway's external-session multiplexer (`adaptermux`) measures the
enqueue→TCP-write latency for every frame delivered to a connected
client (e.g. ebusd). The intent is to surface gateway-side pipeline
stalls that correlate with downstream "send to fe: ERR: read timeout"
events on ebusd, whose default `--receivetimeout` is 25 ms.

| Metric | Type | Description |
| --- | --- | --- |
| `adaptermux_session_frame_latency_us_bucket_total` | map | Cumulative latency histogram. Keys are `le_1000`, `le_5000`, `le_25000`, `le_100000`, and `gt_100000`. |

The histogram is **Prometheus-style cumulative**: each `le_X` counter
holds the total number of frame samples whose elapsed enqueue→write
time was ≤ X microseconds. A sample at 500 µs increments `le_1000`,
`le_5000`, `le_25000`, and `le_100000`. The `gt_100000` counter is the
**non-cumulative overflow bin** for samples exceeding every `le_*`
boundary.

| Quantity | Formula |
| --- | --- |
| Total samples | `le_100000 + gt_100000` |
| Frames within ebusd's 25 ms budget | `le_25000` |
| Frames over the 25 ms budget | `(le_100000 + gt_100000) - le_25000` |
| Frames over 100 ms (tail) | `gt_100000` |

The latency measurement uses a monotonic clock anchor captured at
process start, so wall-clock steps (NTP/chrony correction, manual
`date -s`) cannot produce negative or inflated samples. The metric is
exposed via the in-process Go `expvar` map and is currently **not
mounted on a public HTTP endpoint** — it backs internal observability
and slow-frame log markers below.

In addition to the histogram, frames with latency above
**25 ms** emit a structured log line:

```
adaptermux: session <ID> frame delivery slow: kind=<K> latency=<USES>us
   (threshold=25000us — exceeds ebusd's default --receivetimeout)
```

These log markers exist so operators can pinpoint concrete slow samples
without needing histogram tooling. (F-10 diagnostic — see
`_work_adaptermux_audit/EBUSD-VERIFICATION-2026-05-10.md`.)

## Structured Log Markers

Bus observability warmup and dedup health are metric-first today. The structured log markers currently emitted by gateway are the semantic lifecycle and merge markers below.

### Semantic Lifecycle

| Marker | When it appears | Key fields |
| --- | --- | --- |
| `semantic_startup_phase_transition` | Startup FSM changes phase | `from`, `to`, `reason`, `cache_epoch`, `live_epoch` |
| `semantic_zone_presence_transition` | Zone presence FSM changes state | `instance`, `from`, `to`, `hit_streak`, `miss_streak`, `zone_count` |
| `semantic_dhw_update` | DHW freshness timestamp advances | `last_update_utc` |
| `semantic_dhw_expired` | DHW stale TTL expires and the DHW snapshot is removed | `ttl`, `age`, `last_update_utc` |
| `semantic_regulator_capability` | Regulator capability classification changes or is re-announced | `capability` |
| `semantic_regulator_transition` | Regulator absence FSM changes state | `from`, `to`, `capability` |
| `semantic_regulator_absence` | Regulator absence state is published after a transition | `state`, `capability` |
| `semantic_regulator_recheck` | Inventory change triggers immediate discovery refresh | `prev`, `curr` |

### Read Path and Energy Merge

| Marker | When it appears | Key fields |
| --- | --- | --- |
| `semantic_read_breaker_transition` | Per-key B524 read breaker changes state | `key`, `from`, `to`, `consecutive_failures` |
| `semantic_read_breaker_suppressed` | Breaker suppresses a read while open | `key`, `state`, `retry_after`, `suppressed_total` |
| `semantic_energy_merge_accept` | Incoming energy point is accepted | `source` |
| `semantic_energy_merge_reject` | Incoming energy point is rejected | `reason`, `source`, and `existing_source` for `source_downgrade` rejections |

## Troubleshooting Mapping

| Symptom | Signals to Check | What to Look For |
| --- | --- | --- |
| Zones not appearing | `semantic_zone_count`, `semantic_zone_presence_transition` | Zone count stays `0`, or no transitions reach `PRESENT` |
| Startup stuck before live-ready | `semantic_startup_current_phase`, `semantic_live_epoch`, `semantic_startup_phase_transition` | Phase stays `CACHE_LOADED_STALE` or `LIVE_WARMUP`, or transition reasons point to missing live-backed updates |
| DHW disappearing | `semantic_dhw_stale_expiry_total`, `semantic_dhw_updates_total`, `semantic_dhw_expired` | Expiry count grows faster than updates, or `age` exceeds the configured TTL |
| Energy not updating | `semantic_energy_merges_total`, `semantic_energy_rejections_total`, `semantic_energy_merge_reject` | Rejections grow, especially `source_downgrade` or `monotonic` |
| Regulator lost | `semantic_regulator_state`, `semantic_regulator_transition`, `semantic_regulator_absence` | State reaches `ABSENT`, typically through `PRESENT -> ABSENCE_GRACE -> ABSENT` |
| Passive observe-first unavailable | `ebus_passive_warmup_state`, `ebus_passive_capability_unavailable_reason`, `ebus_observability_transport_info` | `state="unavailable"` with reason `unsupported_or_misconfigured` is expected on `ebusd-tcp` and direct adapter-class `enh`/`ens` endpoints |
| Busy metrics missing | `ebus_observability_transport_info`, `ebus_passive_warmup_state`, `ebus_bus_busy_ratio` | Busy metrics emit only once passive state is `available` and passive timing quality is not `unavailable` |
| Dedup stays degraded | `ebus_dedup_degraded_state`, `ebus_dedup_degraded_total`, `ebus_passive_fanout_overflow_total` | Degraded state stays `1`, or overflow/degraded counters keep increasing |
| Bus communication issues | `semantic_bus_collisions_total`, `semantic_read_breaker_transitions_total`, `semantic_read_breaker_suppressed` | Collision count rises, or a key stays in `open` with repeated suppressions |

## Cross-Links

- Passive transport contract and degraded topologies: [`deployment/full-stack.md`](../deployment/full-stack.md#passive-observe-first-transport-contract)
- Startup FSM: [`architecture/startup-semantic-fsm.md`](./startup-semantic-fsm.md)
- B524 semantic root discovery: [`architecture/b524-semantic-root-discovery.md`](./b524-semantic-root-discovery.md)
- Regulator identity enrichment: [`architecture/regulator-identity-enrichment.md`](./regulator-identity-enrichment.md)
- Energy merge: [`architecture/energy-merge.md`](./energy-merge.md)
- Zone presence FSM: [`architecture/zone-presence-fsm.md`](./zone-presence-fsm.md)
- DHW freshness: [`architecture/dhw-freshness-fsm.md`](./dhw-freshness-fsm.md)
- Adversarial matrix: [`architecture/adversarial-matrix.md`](./adversarial-matrix.md)
