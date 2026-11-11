# Bounded transport and semantic Prometheus coverage

This is the deployment contract for the remaining baud-observation and
Thermal/HVAC and Infrastructure exports. **Target** names below reserve a
bounded projection; they do not claim an implemented collector, qualified
binding, live measurement, or release acceptance. Existing transport names
remain compatible. Nothing here changes MCP namespaces or GraphQL contracts;
all MCP namespaces remain pre-stable.

## Source owners and evidence boundary

The gateway owns collection, lifecycle and Prometheus exposition. Its
[bus observability store][bus-owner] owns the implemented transport names in
the coverage table. SemReg owns the [Thermal/HVAC][thermal-owner] and
[Infrastructure][infrastructure-owner] definitions, canonical units and
validation. A pack definition is neither a native acquisition seam nor an
exporter. Branch links identify source owners, not immutable acceptance
evidence; revalidate the exact deployment candidate before enabling rules.

For eBUS facts, start with the public [native B524 contract][native-b524],
then the [semantic mapping][thermal-map] and its
[typed candidate index][thermal-fixture]. Preserve the native
`(opcode, group, instance, register)` identity in provenance, outside metric
labels. Never substitute OP02 and OP06 or infer writes from reads. For other
protocols, their corresponding public native documentation and admitted
source owner must establish the mapping first; this page defines no native
Modbus, eeBUS or CAN behavior.

Evidence conclusions remain `Proven`, `Hypothesis` or `Unknown`, separately
from qualification, freshness and export implementation. In particular the
[controller qualification gap][qualification] is `Unknown`, and the thermal
candidate index forbids runtime qualification and does not establish
Prometheus output. The two exact candidate rows are not live series.
An exact mapping disposition does not mean a qualified device.

## Bounded label and admission contract

The structured domains below apply to the semantic value rows and availability
series. `domain_field_table` selects exactly the pack fields under the matching
domain heading in the semantic tables; it does not form a cross product.

| Series group | Label | Allowed domain |
| --- | --- | --- |
| `semantic_values` | `slot` | `0..15` |
| `helianthus_semantic_field_available` | `slot` | `0..15` |
| `helianthus_semantic_field_available` | `domain` | `thermal, infrastructure` |
| `helianthus_semantic_field_available` | `field` | `domain_field_table` |

- The new baud series have no exporter labels: one observation source per
  gateway collector. Never choose one of several physical buses implicitly;
  ambiguous source selection makes observation unavailable.
- Semantic quantity and status series have `slot` and, where specified below, a constant `unit` label. The slot is from the fixed set
  `0` through `15`. Each domain admits at most 16 concrete
  resource/service/dimension tuples. Assignment is explicit, collision-free
  and durably persisted before publication for the lifetime of the scrape
  target's `{job, instance}`, including collector restarts. Each binding
  includes the exact source and resource/service/dimension tuple. Retired
  slots remain reserved and must never be reassigned under that target,
  including after source replacement. Admit a replacement only in a never-used
  slot; exhaustion makes the replacement unavailable. If the binding registry
  is missing or corrupt after prior publication, omit all semantic values
  until the original registry is restored and bindings are revalidated.
  Slots are local bounded selections, never raw identifiers, hashes,
  fingerprints or encoded locators. Retire a replaced source's slot before
  publishing replacement values; its availability remains 0. An availability
  reset alone does not separate historical time series.
- `helianthus_semantic_field_available` additionally has `domain` from
  `thermal`, `infrastructure` and `field` from exactly the corresponding
  field column below. Only configured tuples exist. Thus each of the 32
  fields has at most 16 value and 16 availability series: at most 1024
  semantic series per scrape target for the exporter label set, without a
  domain/field cross product. Deployment-wide, the semantic bound is
  `T × 1024`, where `T` counts distinct retained target-label combinations,
  including `job`, `instance` and any other relabeled target labels. Multiple
  collectors and changes to those combinations multiply the budget; capacity
  acceptance must bound `T` over the retention period. The baud target budget reserves two per target; only availability is emitted. Existing bus series retain their own bounded
  source-owner budgets.
- Do not export raw asset IDs, addresses, locators, request bytes, serials,
  network endpoints, contributor identities, capture times or fingerprints
  as labels. Do not turn arbitrary pack dimension text into labels. Internal
  provenance retains the exact source binding and dimensions separately.
  A slot must not silently aggregate different sources or dimensions.
- Scrape configuration must use bounded, non-identifying target labels too;
  replace an endpoint-valued `instance` before ingestion. Alert annotations
  must not copy native payloads or private identifiers.
- Overflow, ambiguous selection, unknown symbols, invalid units or conflicting
  contributions fail closed for the affected selection. Retain valid siblings
  and their last-known-good provenance; do not evict them to admit new series.

## Missing values, lifecycle and resets

For every target numeric/status field, emit a value only from the current,
admitted, qualified, valid and fresh source record, using the same semantic
revision and evaluation as the public projection. Do not read native devices
from a scrape, reconstruct from UI labels, or use raw MCP as a fallback.
Preserve eBUS MCP compatibility and GraphQL parity: unavailable public facts
cannot become current Prometheus measurements.

Unknown, unsupported, withheld, stale, withdrawn, conflicting or invalid
values have **no value sample**. The availability gauge is `0` for such a
configured field and `1` only when its value is exportable. An unconfigured
field has neither series. Zero availability describes a known export state,
never a zero measurement. No `or vector(0)`, zero fill, carried-forward
measurement, or fabricated CAN sample is allowed. Historical samples remain
historical; dashboards and alerts must join availability to suppress old
samples during Prometheus lookback. Retained last-known-good records keep
their original receipt and explicit non-current state outside these gauges;
reevaluation cannot refresh acquisition time. Partial updates preserve valid
sibling fields.

All target value and availability series are gauges, including cumulative
energy readings. They have no exporter reset-to-zero operation. At startup,
reconnect, source replacement or freshness/clock discontinuity, availability
is `0` until revalidated; omit the value. A changed source reading can move a
gauge in either direction. Do not compute `rate` on energy gauges or infer
consumption across meter replacement/reset. Energy totals remain native
readings, with kWh converted to joules by multiplying by 3,600,000.

Existing transport counters reset on recreation of their owning in-memory
store/process. Reconnection does not mean a new counter epoch; use
`rate`/`increase`, never subtract unrelated absolute totals. Busy-time
availability may disappear during warmup while retained counters survive.
Connectivity is a state gauge, so a known disconnected state is legitimately
`0`; it is not a measurement of traffic or baud.

## Transport coverage

`Proven` below applies only to the cited bus-store implementation observation,
not native wire behavior or deployment acceptance. `Unknown` marks targets
without qualified timing or acquisition evidence.

| Series | Type / unit | Labels | Owner, missing behavior and coverage | Status |
|---|---|---|---|---|
| `ebus_passive_tap_connected` | gauge / boolean | none | Bus store; implemented in inspected source, known connection state 0/1; exact-candidate revalidation required | `Proven` |
| `ebus_bus_busy_seconds_total` | counter / seconds | none | Bus store; implemented, emitted only when passive state is available and timing is available; revalidate candidate | `Proven` |
| `ebus_bus_busy_ratio` | gauge / ratio 0..1 | `window`: `1m`, `5m`, `15m`, `1h` | Bus store; implemented with the same availability condition; recomputed rolling window, not a baud estimate; revalidate candidate | `Proven` |
| `ebus_passive_tap_reconnect_attempts_total` | counter / attempts | none | Bus store; implemented, cumulative connection attempts; revalidate candidate | `Proven` |
| `ebus_passive_tap_reconnect_successes_total` | counter / connections | none | Bus store; implemented, cumulative successful connections; revalidate candidate | `Proven` |
| `ebus_passive_tap_reconnect_failures_total` | counter / failures | none | Bus store; implemented, cumulative failed connections; revalidate candidate | `Proven` |
| `ebus_baud_observed_symbols_per_second` | gauge / physical symbols per second | none | **Target**, gateway transport timing owner; absent until a qualified native timing observation exists | `Unknown` |
| `ebus_baud_observation_available` | gauge / boolean | none | **Target**, same owner; 0 when configured but no valid observation, 1 with current observation; absent if collector not implemented/configured | `Unknown` |
| CAN transport or semantic measurements | unavailable | none admitted | **Pending CAN acquisition**; no native acquisition seam established by this contract, no reserved fake value series | `Unknown` |

The baud target measures physical signaling intervals over a completed,
source-owner-validated observation window, with window validity, expiry and
timing uncertainty retained in provenance. Configured baud, retained frame
byte rate, idle time and TCP arrival spacing cannot supply it. The transport
owner must establish a qualified timing seam and its window/expiry policy
before implementation acceptance. The latest valid completed estimate is a
gauge, not a running counter; after expiry or reconnection omit it and mark
availability 0. No numerical default baud is a measurement. These target
names remain unimplemented in the inspected bus store.

## Semantic coverage and units

Every row below is **Target / exact-candidate revalidation required**, owned
by the named SemReg pack for meaning and the gateway for export. Renderer support is Proven for the names in the emitted table below; qualification remains separate. The field identifiers are a closed allowlist, not
free-form labels. All rows use the gauge lifecycle and `slot` bound above.

### Thermal/HVAC

| Pack field | Target series | Unit / conversion |
|---|---|---|
| `thermal.action.state` | `helianthus_thermal_action_state` | enum: idle=0, heating=1, cooling=2, dhw=3, ventilating=4 |
| `thermal.demand.level` | `helianthus_thermal_demand_ratio` | ratio; percent / 100 |
| `thermal.measurement.air_temperature` | `helianthus_thermal_air_temperature` | Celsius; identity |
| `thermal.measurement.flow_rate` | `helianthus_thermal_flow_cubic_meters_per_second` | m³/s; litre/minute / 60,000 |
| `thermal.measurement.humidity` | `helianthus_thermal_relative_humidity_ratio` | ratio; percent / 100 |
| `thermal.measurement.power` | `helianthus_thermal_power_watts` | watts; preserve sign |
| `thermal.measurement.water_temperature` | `helianthus_thermal_water_temperature_celsius` | Celsius; identity |
| `thermal.mode.system` | `helianthus_thermal_system_mode` | enum: off=0, auto=1, heat=2, cool=3 |
| `thermal.mode.zone` | `helianthus_thermal_zone_mode` | enum: off=0, auto=1, comfort=2, eco=3 |
| `thermal.setpoint.dhw_temperature_setpoint` | `helianthus_thermal_dhw_setpoint_celsius` | Celsius; identity; read-only observation |
| `thermal.setpoint.temperature_setpoint` | `helianthus_thermal_temperature_setpoint` | Celsius; identity; read-only observation |
| `thermal.status.fault` | `helianthus_thermal_fault_present` | boolean: clear=0, present=1 |
| `thermal.status.operation` | `helianthus_thermal_operation_active` | boolean: idle=0, active=1 |

Enum numbers encode exactly the pack symbols with the corresponding field
prefix; they are categories, never ordinal severity or unknown sentinels.
No unlisted symbol maps to 0. Setpoint visibility supplies no write authority.
Only the air-temperature and water-temperature rows have exact candidate
links in the local thermal mapping fixture, and both still require qualified
binding and export revalidation. The rolling-average candidate remains
withheld: its time-window loss cannot become an instantaneous temperature.
Other pack fields have definitions, not native mapping evidence here.

### Infrastructure

| Pack field | Target series | Unit / conversion |
|---|---|---|
| `infrastructure.ac.active_power` | `helianthus_infrastructure_ac_active_power_watts` | watts; preserve sign |
| `infrastructure.ac.apparent_power` | `helianthus_infrastructure_ac_apparent_power_volt_amperes` | VA; identity |
| `infrastructure.ac.current` | `helianthus_infrastructure_ac_current_amperes` | amperes; identity |
| `infrastructure.ac.frequency` | `helianthus_infrastructure_ac_frequency_hertz` | hertz; identity |
| `infrastructure.ac.power_factor` | `helianthus_infrastructure_ac_power_factor_ratio` | ratio; preserve sign |
| `infrastructure.ac.reactive_power` | `helianthus_infrastructure_ac_reactive_power_vars` | var; preserve sign |
| `infrastructure.ac.voltage` | `helianthus_infrastructure_ac_voltage_volts` | volts; identity |
| `infrastructure.energy.export` | `helianthus_infrastructure_energy_export_joules` | joules; kWh × 3,600,000; gauge |
| `infrastructure.energy.import` | `helianthus_infrastructure_energy_import_joules` | joules; kWh × 3,600,000; gauge |
| `infrastructure.power.apparent` | `helianthus_infrastructure_apparent_power_volt_amperes` | VA; identity |
| `infrastructure.power.export_active` | `helianthus_infrastructure_export_active_power_watts` | watts; nonnegative directional value |
| `infrastructure.power.export_reactive` | `helianthus_infrastructure_export_reactive_power_vars` | var; nonnegative directional value |
| `infrastructure.power.import_active` | `helianthus_infrastructure_import_active_power_watts` | watts; nonnegative directional value |
| `infrastructure.power.import_reactive` | `helianthus_infrastructure_import_reactive_power_vars` | var; nonnegative directional value |
| `infrastructure.status.breaker` | `helianthus_infrastructure_breaker_open` | boolean: closed=0, open=1 |
| `infrastructure.status.connection` | `helianthus_infrastructure_connection_connected` | boolean: disconnected=0, connected=1 |
| `infrastructure.status.fault` | `helianthus_infrastructure_fault_present` | boolean: clear=0, present=1 |
| `infrastructure.status.interlock` | `helianthus_infrastructure_interlock_active` | boolean: clear=0, active=1 |
| `infrastructure.status.readiness` | `helianthus_infrastructure_ready` | boolean: not_ready=0, ready=1 |

Phase, meter and grid-connection dimensions remain distinct source keys;
never sum or substitute them to populate a missing field. The pack does not
establish a native Infrastructure binding or a CAN measurement.

## Thermal mapping dispositions

These structured claims are compared to the [thermal fixture][thermal-fixture].
They describe candidate dispositions, with qualification and export still
requiring separate acceptance.

### Exact fact IDs

| semreg_fact |
| --- |
| `thermal.measurement.air_temperature` |
| `thermal.measurement.water_temperature` |

### Withheld associations

| legacy_system_field | loss |
| --- | --- |
| `state.outdoor_temperature_avg24h` | `rolling_average_window_unrepresentable` |

## Offline alert examples

These rules illustrate known-unavailable versus observed-fault alerts. Enable
target-series rules only after exact-candidate collector verification. They
are passive diagnostics and authorize no polling, device writes or rollout.
Here `job` and `instance` are bounded non-identifying deployment labels;
one collector owns each pair. No rule fills unknown measurements with zero.

```yaml
groups:
  - name: helianthus.bounded-coverage
    rules:
      - alert: HelianthusPassiveTapDisconnected
        expr: ebus_passive_tap_connected == 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: Passive tap reports disconnected
      - alert: HelianthusBaudObservationUnavailable
        expr: ebus_baud_observation_available == 0
        for: 10m
        labels:
          severity: info
        annotations:
          summary: Configured baud observation is unavailable
      - alert: HelianthusSemanticFieldUnavailable
        expr: helianthus_semantic_field_available == 0
        for: 10m
        labels:
          severity: info
        annotations:
          summary: Configured semantic field is unavailable
      - alert: HelianthusThermalFaultObserved
        expr: |
          (helianthus_thermal_fault_present == 1)
          and on(job, instance, slot)
          (helianthus_semantic_field_available{domain="thermal",field="thermal.status.fault"} == 1)
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: Admitted fresh thermal fault is present
      - alert: HelianthusInfrastructureInterlockObserved
        expr: |
          (helianthus_infrastructure_interlock_active == 1)
          and on(job, instance, slot)
          (helianthus_semantic_field_available{domain="infrastructure",field="infrastructure.status.interlock"} == 1)
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: Admitted fresh infrastructure interlock is active
```

Collector absence requires a separately configured expected-target inventory
and scrape-health alert; these rules intentionally do not equate an absent
collector with a healthy field. The local CI gate runs
`python3 scripts/validate_prometheus_semantic_coverage.py` and its mutation
tests to check the structured field/name/unit tables, label domains, thermal
dispositions against their source fixture, and example selectors. Explanatory
prose, lifecycle rationale, transport ownership descriptions and alert
annotations require human review under the
[finite validation scope](../development/prometheus-validation-scope.md).
These static checks do not evaluate PromQL. PromQL evaluation, exporter tests, candidate revalidation and physical acquisition
evidence are separate acceptance work. Existing
[adaptermux alert rules](prometheus-alerts.md) retain their source contracts.

[bus-owner]: https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/bus_observability_store.go
[thermal-owner]: https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go
[infrastructure-owner]: https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/infrastructure/definitions.go
[native-b524]: ../protocols/vaillant/ebus-vaillant-b524.md
[thermal-map]: ../architecture/b524-semantic-mapping.md
[thermal-fixture]: ../architecture/fixtures/vaillant-semreg-thermal-map-v1.json
[qualification]: ../architecture/vaillant-controller-qualification-v1.md

## Emitted metric names

Proven means renderer support, independently of qualification. This table covers
all 106 custom families; enablement and omission conditions still apply. Expvar-only
values are outside Prometheus exposition. No library-emitted exception is established
for these custom families. The bounded naming map changes only the three series
with a constant unit below. Numeric scales, signs and conversions remain unchanged,
including seconds, Celsius, percent divided by 100, litre/minute divided by 60,000
and kWh multiplied by 3,600,000. Counter names retain `_total`.

A constant unit admits exactly one value per family, adds no series multiplier,
and cannot carry arbitrary dimensions. Removing a suffix must preserve unique
series names; collisions fail admission. Existing bounded labels and partial
last-known-good state remain required.

| Series | Type | Labels | Constant unit |
| --- | --- | --- | --- |
| `active_read_saved_seconds` | `gauge` | `family, freshness_profile` | `none` |
| `active_reads_avoided_total` | `counter` | `family, freshness_profile` | `none` |
| `ambiguous_total` | `counter` | `family, reason` | `none` |
| `direct_apply_total` | `counter` | `family, freshness_profile` | `none` |
| `ebus_active_echo_mismatch_subclass_total` | `counter` | `subclass` | `none` |
| `ebus_adaptermux_escape_pair_verify_failures_total` | `counter` | `step` | `none` |
| `ebus_adaptermux_foreign_initiator_releases_total` | `counter` | `none` | `none` |
| `ebus_adaptermux_inter_write_drained_bytes_total` | `counter` | `none` | `none` |
| `ebus_adaptermux_stale_active_bytes_discarded_total` | `counter` | `none` | `none` |
| `ebus_adaptermux_syn_seen_after_transport_window_expired_total` | `counter` | `none` | `none` |
| `ebus_adaptermux_syn_seen_during_grant_window_total` | `counter` | `none` | `none` |
| `ebus_adaptermux_syn_seen_while_inter_write_empty_total` | `counter` | `none` | `none` |
| `ebus_adaptermux_syn_suppressed_between_writes_total` | `counter` | `none` | `none` |
| `ebus_adaptermux_syn_suppressed_pre_echo_total` | `counter` | `none` | `none` |
| `ebus_adaptermux_transaction_endings_total` | `counter` | `reason` | `none` |
| `ebus_baud_observation_available` | `gauge` | `none` | `none` |
| `ebus_bus_busy_ratio` | `gauge` | `window` | `none` |
| `ebus_bus_busy_seconds_total` | `counter` | `none` | `none` |
| `ebus_dedup_degraded_state` | `gauge` | `none` | `none` |
| `ebus_dedup_degraded_total` | `counter` | `reason` | `none` |
| `ebus_dedup_epoch_resets_total` | `counter` | `none` | `none` |
| `ebus_dedup_local_participant_inbound_total` | `counter` | `none` | `none` |
| `ebus_dedup_pending_flush_total` | `counter` | `reason` | `none` |
| `ebus_errors_total` | `counter` | `class, phase, scope` | `none` |
| `ebus_frame_bytes_total` | `counter` | `family, frame_type, part, scope` | `none` |
| `ebus_frames_observed_total` | `counter` | `dst, family, frame_type, scope, src` | `none` |
| `ebus_observability_recent_messages` | `gauge` | `none` | `none` |
| `ebus_observability_series_budget_overflow_total` | `counter` | `none` | `none` |
| `ebus_observability_transport_info` | `gauge` | `scope, timing_quality, transport_class` | `none` |
| `ebus_passive_capability_probe_attempts_total` | `counter` | `none` | `none` |
| `ebus_passive_capability_probe_outcomes_total` | `counter` | `outcome` | `none` |
| `ebus_passive_capability_transitions_total` | `counter` | `from, to` | `none` |
| `ebus_passive_capability_unavailable_reason` | `gauge` | `reason` | `none` |
| `ebus_passive_completed_transactions_total` | `counter` | `none` | `none` |
| `ebus_passive_direct_apply_candidates_evaluated_total` | `counter` | `none` | `none` |
| `ebus_passive_fanout_overflow_total` | `counter` | `consumer, criticality` | `none` |
| `ebus_passive_reconstructor_abandons_total` | `counter` | `reason` | `none` |
| `ebus_passive_reconstructor_invalid_src_class_skipped_total` | `counter` | `none` | `none` |
| `ebus_passive_reconstructor_prefix_resync_skipped_total` | `counter` | `none` | `none` |
| `ebus_passive_reconstructor_recoveries_total` | `counter` | `reason` | `none` |
| `ebus_passive_tap_connected` | `gauge` | `none` | `none` |
| `ebus_passive_tap_reconnect_attempts_total` | `counter` | `none` | `none` |
| `ebus_passive_tap_reconnect_failures_total` | `counter` | `none` | `none` |
| `ebus_passive_tap_reconnect_successes_total` | `counter` | `none` | `none` |
| `ebus_passive_warmup_blocker_reason` | `gauge` | `reason` | `none` |
| `ebus_passive_warmup_completed_transactions` | `gauge` | `none` | `none` |
| `ebus_passive_warmup_completion_mode` | `gauge` | `mode` | `none` |
| `ebus_passive_warmup_elapsed_seconds` | `gauge` | `none` | `none` |
| `ebus_passive_warmup_required_transactions` | `gauge` | `none` | `none` |
| `ebus_passive_warmup_state` | `gauge` | `state` | `none` |
| `ebus_periodicity_tuple_budget_overflow_total` | `counter` | `none` | `none` |
| `energy_broadcast_freshness_transitions_total` | `counter` | `from, to` | `none` |
| `energy_broadcast_selectors` | `gauge` | `state` | `none` |
| `external_write_policy_state` | `gauge` | `policy` | `none` |
| `feature_flag_enabled` | `gauge` | `flag` | `none` |
| `feature_flag_normalizations_total` | `counter` | `reason` | `none` |
| `helianthus_huawei_transport_events_total` | `counter` | `family, function, outcome` | `none` |
| `helianthus_infrastructure_ac_active_power_watts` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_ac_apparent_power_volt_amperes` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_ac_current_amperes` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_ac_frequency_hertz` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_ac_power_factor_ratio` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_ac_reactive_power_vars` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_ac_voltage_volts` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_apparent_power_volt_amperes` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_breaker_open` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_connection_connected` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_energy_export_joules` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_energy_import_joules` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_export_active_power_watts` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_export_reactive_power_vars` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_fault_present` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_import_active_power_watts` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_import_reactive_power_vars` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_interlock_active` | `gauge` | `slot` | `none` |
| `helianthus_infrastructure_ready` | `gauge` | `slot` | `none` |
| `helianthus_payload_aa_auto_syn_absorbed_total` | `counter` | `none` | `none` |
| `helianthus_payload_aa_auto_syn_drain_exhausted_total` | `counter` | `none` | `none` |
| `helianthus_payload_aa_auto_syn_recovered_total` | `counter` | `none` | `none` |
| `helianthus_round9_absorb_entered_total` | `counter` | `none` | `none` |
| `helianthus_semantic_evidence_age` | `gauge` | `connector, dimension, domain, fact_id, pack, unit` | `seconds` |
| `helianthus_semantic_fact_state` | `gauge` | `availability, connector, dimension, domain, fact_id, freshness, pack, promotion, qualification, quality` | `none` |
| `helianthus_semantic_fact_value` | `gauge` | `connector, dimension, domain, fact_id, pack, unit` | `none` |
| `helianthus_semantic_field_available` | `gauge` | `domain, field, slot` | `none` |
| `helianthus_semantic_open_conflicts` | `gauge` | `connector, dimension, domain, fact_id, pack` | `none` |
| `helianthus_semantic_projection_available` | `gauge` | `domain` | `none` |
| `helianthus_semantic_projection_item` | `gauge` | `domain, item, outcome` | `none` |
| `helianthus_semantic_projection_loss` | `gauge` | `domain, item, loss_kind` | `none` |
| `helianthus_semantic_render_overflow` | `gauge` | `none` | `none` |
| `helianthus_thermal_action_state` | `gauge` | `slot` | `none` |
| `helianthus_thermal_air_temperature` | `gauge` | `slot, unit` | `celsius` |
| `helianthus_thermal_demand_ratio` | `gauge` | `slot` | `none` |
| `helianthus_thermal_dhw_setpoint_celsius` | `gauge` | `slot` | `none` |
| `helianthus_thermal_fault_present` | `gauge` | `slot` | `none` |
| `helianthus_thermal_flow_cubic_meters_per_second` | `gauge` | `slot` | `none` |
| `helianthus_thermal_operation_active` | `gauge` | `slot` | `none` |
| `helianthus_thermal_power_watts` | `gauge` | `slot` | `none` |
| `helianthus_thermal_relative_humidity_ratio` | `gauge` | `slot` | `none` |
| `helianthus_thermal_temperature_setpoint` | `gauge` | `slot, unit` | `celsius` |
| `helianthus_thermal_system_mode` | `gauge` | `slot` | `none` |
| `helianthus_thermal_water_temperature_celsius` | `gauge` | `slot` | `none` |
| `helianthus_thermal_zone_mode` | `gauge` | `slot` | `none` |
| `helianthus_transport_runtime_status` | `gauge` | `outcome, protocol, reason, state` | `none` |
| `helianthus_v8_shadow_would_have_dropped_total` | `counter` | `none` | `none` |
| `missed_due_to_transport_limitations_total` | `counter` | `family, freshness_profile, limitation` | `none` |
| `passive_hits_total` | `counter` | `family, freshness_profile` | `none` |

## Provisional metric exceptions

Each name below remains emitted and provisional, outside the unit-label rule.
For each, the open question is which bounded unit-label change preserves its
quantity and every consumer? These are custom exceptions, not proven library
constraints. Other unchanged names retain their recorded meaning.

- `active_read_saved_seconds`: provisional; unit-label adoption is unresolved.
- `ebus_passive_warmup_elapsed_seconds`: provisional; unit-label adoption is unresolved.
- `helianthus_infrastructure_ac_active_power_watts`: provisional; unit-label adoption is unresolved.
- `helianthus_infrastructure_ac_apparent_power_volt_amperes`: provisional; unit-label adoption is unresolved.
- `helianthus_infrastructure_ac_current_amperes`: provisional; unit-label adoption is unresolved.
- `helianthus_infrastructure_ac_frequency_hertz`: provisional; unit-label adoption is unresolved.
- `helianthus_infrastructure_ac_reactive_power_vars`: provisional; unit-label adoption is unresolved.
- `helianthus_infrastructure_ac_voltage_volts`: provisional; unit-label adoption is unresolved.
- `helianthus_infrastructure_apparent_power_volt_amperes`: provisional; unit-label adoption is unresolved.
- `helianthus_infrastructure_energy_export_joules`: provisional; unit-label adoption is unresolved.
- `helianthus_infrastructure_energy_import_joules`: provisional; unit-label adoption is unresolved.
- `helianthus_infrastructure_export_active_power_watts`: provisional; unit-label adoption is unresolved.
- `helianthus_infrastructure_export_reactive_power_vars`: provisional; unit-label adoption is unresolved.
- `helianthus_infrastructure_import_active_power_watts`: provisional; unit-label adoption is unresolved.
- `helianthus_infrastructure_import_reactive_power_vars`: provisional; unit-label adoption is unresolved.
- `helianthus_thermal_dhw_setpoint_celsius`: provisional; unit-label adoption is unresolved.
- `helianthus_thermal_flow_cubic_meters_per_second`: provisional; unit-label adoption is unresolved.
- `helianthus_thermal_power_watts`: provisional; unit-label adoption is unresolved.
- `helianthus_thermal_water_temperature_celsius`: provisional; unit-label adoption is unresolved.
