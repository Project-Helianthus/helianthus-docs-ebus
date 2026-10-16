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

- The new baud series have no exporter labels: one observation source per
  gateway collector. Never choose one of several physical buses implicitly;
  ambiguous source selection makes observation unavailable.
- Semantic quantity and status series have only `slot`, from the fixed set
  `0` through `15`. Each domain admits at most 16 concrete
  resource/service/dimension tuples. Assignment is explicit, collision-free
  and fixed for a collector lifetime. Slots are local bounded selections,
  never raw identifiers, hashes, fingerprints or encoded locators. A source
  replacement invalidates its slot before any new value is published.
- `helianthus_semantic_field_available` additionally has `domain` from
  `thermal`, `infrastructure` and `field` from exactly the corresponding
  field column below. Only configured tuples exist. Thus each of the 32
  fields has at most 16 value and 16 availability series: at most 1024
  semantic series, without a domain/field cross product. The two baud series
  add two. Existing bus series retain their own bounded source-owner budgets.
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

| Series | Type / unit | Labels | Owner, missing behavior and coverage |
|---|---|---|---|
| `ebus_passive_tap_connected` | gauge / boolean | none | Bus store; implemented in inspected source, known connection state 0/1; exact-candidate revalidation required |
| `ebus_bus_busy_seconds_total` | counter / seconds | none | Bus store; implemented, emitted only when passive state is available and timing is available; revalidate candidate |
| `ebus_bus_busy_ratio` | gauge / ratio 0..1 | `window`: `1m`, `5m`, `15m`, `1h` | Bus store; implemented with the same availability condition; recomputed rolling window, not a baud estimate; revalidate candidate |
| `ebus_passive_tap_reconnect_attempts_total` | counter / attempts | none | Bus store; implemented, cumulative connection attempts; revalidate candidate |
| `ebus_passive_tap_reconnect_successes_total` | counter / connections | none | Bus store; implemented, cumulative successful connections; revalidate candidate |
| `ebus_passive_tap_reconnect_failures_total` | counter / failures | none | Bus store; implemented, cumulative failed connections; revalidate candidate |
| `ebus_baud_observed_symbols_per_second` | gauge / physical symbols per second | none | **Target**, gateway transport timing owner; absent until a qualified native timing observation exists |
| `ebus_baud_observation_available` | gauge / boolean | none | **Target**, same owner; 0 when configured but no valid observation, 1 with current observation; absent if collector not implemented/configured |
| CAN transport or semantic measurements | unavailable | none admitted | **Pending CAN acquisition**; no native acquisition seam established by this contract, no reserved fake value series |

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
by the named SemReg pack for meaning and the gateway for export. No row is
claimed implemented. The field identifiers are a closed allowlist, not
free-form labels. All rows use the gauge lifecycle and `slot` bound above.

### Thermal/HVAC

| Pack field | Target series | Unit / conversion |
|---|---|---|
| `thermal.action.state` | `helianthus_thermal_action_state` | enum: idle=0, heating=1, cooling=2, dhw=3, ventilating=4 |
| `thermal.demand.level` | `helianthus_thermal_demand_ratio` | ratio; percent / 100 |
| `thermal.measurement.air_temperature` | `helianthus_thermal_air_temperature_celsius` | Celsius; identity |
| `thermal.measurement.flow_rate` | `helianthus_thermal_flow_cubic_meters_per_second` | m³/s; litre/minute / 60,000 |
| `thermal.measurement.humidity_relative` | `helianthus_thermal_relative_humidity_ratio` | ratio; percent / 100 |
| `thermal.measurement.power` | `helianthus_thermal_power_watts` | watts; preserve sign |
| `thermal.measurement.water_temperature` | `helianthus_thermal_water_temperature_celsius` | Celsius; identity |
| `thermal.mode.system` | `helianthus_thermal_system_mode` | enum: off=0, auto=1, heat=2, cool=3 |
| `thermal.mode.zone` | `helianthus_thermal_zone_mode` | enum: off=0, auto=1, comfort=2, eco=3 |
| `thermal.setpoint.dhw_temperature` | `helianthus_thermal_dhw_setpoint_celsius` | Celsius; identity; read-only observation |
| `thermal.setpoint.temperature` | `helianthus_thermal_setpoint_celsius` | Celsius; identity; read-only observation |
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
collector with a healthy field. YAML parsing checks structure only. PromQL
evaluation, exporter tests, candidate revalidation and physical acquisition
evidence are separate acceptance work. Existing
[adaptermux alert rules](prometheus-alerts.md) retain their source contracts.

[bus-owner]: https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/bus_observability_store.go
[thermal-owner]: https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/thermal/definitions.go
[infrastructure-owner]: https://github.com/Project-Helianthus/helianthus-semreg/blob/main/semreg/v1/packs/infrastructure/definitions.go
[native-b524]: ../protocols/vaillant/ebus-vaillant-B524.md
[thermal-map]: ../architecture/b524-semantic-mapping.md
[thermal-fixture]: ../architecture/fixtures/vaillant-semreg-thermal-map-v1.json
[qualification]: ../architecture/vaillant-controller-qualification-v1.md
