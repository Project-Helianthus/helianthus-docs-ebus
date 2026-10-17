#!/usr/bin/env python3
"""Check the closed deployment metric contract; no exporter/runtime acceptance."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re

import yaml


DOCUMENT = Path("deployment/prometheus-semantic-coverage.md")
# Reviewed field/name/unit associations, independent of the document being checked.
SEMANTIC_ROWS = """
thermal.action.state | helianthus_thermal_action_state | enum: idle=0, heating=1, cooling=2, dhw=3, ventilating=4
thermal.demand.level | helianthus_thermal_demand_ratio | ratio; percent / 100
thermal.measurement.air_temperature | helianthus_thermal_air_temperature_celsius | Celsius; identity
thermal.measurement.flow_rate | helianthus_thermal_flow_cubic_meters_per_second | m³/s; litre/minute / 60,000
thermal.measurement.humidity_relative | helianthus_thermal_relative_humidity_ratio | ratio; percent / 100
thermal.measurement.power | helianthus_thermal_power_watts | watts; preserve sign
thermal.measurement.water_temperature | helianthus_thermal_water_temperature_celsius | Celsius; identity
thermal.mode.system | helianthus_thermal_system_mode | enum: off=0, auto=1, heat=2, cool=3
thermal.mode.zone | helianthus_thermal_zone_mode | enum: off=0, auto=1, comfort=2, eco=3
thermal.setpoint.dhw_temperature | helianthus_thermal_dhw_setpoint_celsius | Celsius; identity; read-only observation
thermal.setpoint.temperature | helianthus_thermal_setpoint_celsius | Celsius; identity; read-only observation
thermal.status.fault | helianthus_thermal_fault_present | boolean: clear=0, present=1
thermal.status.operation | helianthus_thermal_operation_active | boolean: idle=0, active=1
infrastructure.ac.active_power | helianthus_infrastructure_ac_active_power_watts | watts; preserve sign
infrastructure.ac.apparent_power | helianthus_infrastructure_ac_apparent_power_volt_amperes | VA; identity
infrastructure.ac.current | helianthus_infrastructure_ac_current_amperes | amperes; identity
infrastructure.ac.frequency | helianthus_infrastructure_ac_frequency_hertz | hertz; identity
infrastructure.ac.power_factor | helianthus_infrastructure_ac_power_factor_ratio | ratio; preserve sign
infrastructure.ac.reactive_power | helianthus_infrastructure_ac_reactive_power_vars | var; preserve sign
infrastructure.ac.voltage | helianthus_infrastructure_ac_voltage_volts | volts; identity
infrastructure.energy.export | helianthus_infrastructure_energy_export_joules | joules; kWh × 3,600,000; gauge
infrastructure.energy.import | helianthus_infrastructure_energy_import_joules | joules; kWh × 3,600,000; gauge
infrastructure.power.apparent | helianthus_infrastructure_apparent_power_volt_amperes | VA; identity
infrastructure.power.export_active | helianthus_infrastructure_export_active_power_watts | watts; nonnegative directional value
infrastructure.power.export_reactive | helianthus_infrastructure_export_reactive_power_vars | var; nonnegative directional value
infrastructure.power.import_active | helianthus_infrastructure_import_active_power_watts | watts; nonnegative directional value
infrastructure.power.import_reactive | helianthus_infrastructure_import_reactive_power_vars | var; nonnegative directional value
infrastructure.status.breaker | helianthus_infrastructure_breaker_open | boolean: closed=0, open=1
infrastructure.status.connection | helianthus_infrastructure_connection_connected | boolean: disconnected=0, connected=1
infrastructure.status.fault | helianthus_infrastructure_fault_present | boolean: clear=0, present=1
infrastructure.status.interlock | helianthus_infrastructure_interlock_active | boolean: clear=0, active=1
infrastructure.status.readiness | helianthus_infrastructure_ready | boolean: not_ready=0, ready=1
"""
TRANSPORT_ROWS = """
ebus_passive_tap_connected | gauge / boolean | none | Bus store; implemented in inspected source, known connection state 0/1; exact-candidate revalidation required
ebus_bus_busy_seconds_total | counter / seconds | none | Bus store; implemented, emitted only when passive state is available and timing is available; revalidate candidate
ebus_bus_busy_ratio | gauge / ratio 0..1 | window: 1m, 5m, 15m, 1h | Bus store; implemented with the same availability condition; recomputed rolling window, not a baud estimate; revalidate candidate
ebus_passive_tap_reconnect_attempts_total | counter / attempts | none | Bus store; implemented, cumulative connection attempts; revalidate candidate
ebus_passive_tap_reconnect_successes_total | counter / connections | none | Bus store; implemented, cumulative successful connections; revalidate candidate
ebus_passive_tap_reconnect_failures_total | counter / failures | none | Bus store; implemented, cumulative failed connections; revalidate candidate
ebus_baud_observed_symbols_per_second | gauge / physical symbols per second | none | **Target**, gateway transport timing owner; absent until a qualified native timing observation exists
ebus_baud_observation_available | gauge / boolean | none | **Target**, same owner; 0 when configured but no valid observation, 1 with current observation; absent if collector not implemented/configured
CAN transport or semantic measurements | unavailable | none admitted | **Pending CAN acquisition**; no native acquisition seam established by this contract, no reserved fake value series
"""
# Required verbatim policy clauses within the semantic section.
SEMANTIC_POLICIES = (
    "Enum numbers encode exactly the pack symbols with the corresponding field\n"
    "prefix; they are categories, never ordinal severity or unknown sentinels.",
    "No unlisted symbol maps to 0.",
    "Setpoint visibility supplies no write authority.",
    "Only the air-temperature and water-temperature rows have exact candidate\n"
    "links in the local thermal mapping fixture, and both still require qualified\n"
    "binding and export revalidation.",
    "The rolling-average candidate remains\n"
    "withheld: its time-window loss cannot become an instantaneous temperature.",
    "Other pack fields have definitions, not native mapping evidence here.",
    "Phase, meter and grid-connection dimensions remain distinct source keys;\n"
    "never sum or substitute them to populate a missing field.",
    "The pack does not\n"
    "establish a native Infrastructure binding or a CAN measurement.",
)
# These clauses jointly define label admission and the series-budget arithmetic.
LABEL_CONTRACT = """
- The new baud series have no exporter labels: one observation source per
  gateway collector. Never choose one of several physical buses implicitly;
  ambiguous source selection makes observation unavailable.
- Semantic quantity and status series have only `slot`, from the fixed set
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
  acceptance must bound `T` over the retention period. The two baud series
  add two per target. Existing bus series retain their own bounded
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
"""
# Reviewed missing-value, freshness, gauge and transport-counter lifecycle clauses.
LIFECYCLE_CONTRACT = """
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
"""


class CheckError(ValueError):
    pass


def normalized(text: str) -> str:
    return " ".join(text.replace("`", "").split())


def rows(text: str) -> list[tuple[str, ...]]:
    return [tuple(normalized(cell) for cell in line.strip().strip("|").split("|"))
            for line in text.splitlines() if line.strip().startswith("|")]


def section(text: str, heading: str, next_heading: str) -> str:
    if text.count(heading) != 1 or text.count(next_heading) != 1:
        raise CheckError(f"missing or duplicate heading: {heading.strip()}")
    return text.split(heading, 1)[1].split(next_heading, 1)[0]


class UniqueKeyLoader(yaml.SafeLoader):
    """Reject duplicate keys instead of silently hiding a changed rule."""


def unique_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode) -> dict:
    pairs = loader.construct_pairs(node, deep=True)
    result = dict(pairs)
    if len(result) != len(pairs):
        raise CheckError("duplicate YAML key")
    return result


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)


def expected_rules() -> dict:
    examples = [
        ("HelianthusPassiveTapDisconnected", "ebus_passive_tap_connected == 0",
         "5m", "warning", "Passive tap reports disconnected"),
        ("HelianthusBaudObservationUnavailable", "ebus_baud_observation_available == 0",
         "10m", "info", "Configured baud observation is unavailable"),
        ("HelianthusSemanticFieldUnavailable", "helianthus_semantic_field_available == 0",
         "10m", "info", "Configured semantic field is unavailable"),
        ("HelianthusThermalFaultObserved",
         '(helianthus_thermal_fault_present == 1) and on(job, instance, slot) '
         '(helianthus_semantic_field_available{domain="thermal",field="thermal.status.fault"} == 1)',
         "2m", "warning", "Admitted fresh thermal fault is present"),
        ("HelianthusInfrastructureInterlockObserved",
         '(helianthus_infrastructure_interlock_active == 1) and on(job, instance, slot) '
         '(helianthus_semantic_field_available{domain="infrastructure",field="infrastructure.status.interlock"} == 1)',
         "2m", "warning", "Admitted fresh infrastructure interlock is active"),
    ]
    return {"groups": [{"name": "helianthus.bounded-coverage", "rules": [
        {"alert": name, "expr": expr, "for": duration,
         "labels": {"severity": severity}, "annotations": {"summary": summary}}
        for name, expr, duration, severity, summary in examples
    ]}]}


def validate(text: str) -> None:
    semantic = section(text, "## Semantic coverage and units\n", "## Offline alert examples\n")
    for clause in SEMANTIC_POLICIES:
        if clause not in semantic:
            raise CheckError(f"missing semantic policy clause: {clause}")
    actual = rows(semantic)
    header = ("Pack field", "Target series", "Unit / conversion")
    separator = ("---", "---", "---")
    expected = rows("\n".join("| " + line for line in SEMANTIC_ROWS.strip().splitlines()))
    if Counter(actual) != Counter(expected + [header, separator] * 2):
        raise CheckError("semantic field/name/unit tables differ from the closed allowlist")
    thermal, infrastructure = semantic.split("### Infrastructure\n", 1) if semantic.count("### Infrastructure\n") == 1 else ("", "")
    for domain, table in (("thermal", thermal), ("infrastructure", infrastructure)):
        domain_rows = [row for row in expected if row[0].startswith(domain + ".")]
        if Counter(rows(table)) != Counter(domain_rows + [header, separator]):
            raise CheckError(f"fields under the wrong domain heading: {domain}")
    fields = [row[0] for row in expected]
    names = [row[1] for row in expected]
    if (len(set(fields)) != 32 or len(set(names)) != 32
            or sum(field.startswith("thermal.") for field in fields) != 13
            or sum(field.startswith("infrastructure.") for field in fields) != 19
            or len(fields) * 16 * 2 != 1024):
        raise CheckError("invalid reviewed field count or per-target series budget")
    transport = section(text, "## Transport coverage\n", "## Semantic coverage and units\n")
    actual_transport = rows(transport)
    expected_transport = rows("\n".join("| " + line for line in TRANSPORT_ROWS.strip().splitlines()))
    if (actual_transport[:2] != [
            ("Series", "Type / unit", "Labels", "Owner, missing behavior and coverage"),
            ("---", "---", "---", "---")]
            or any(len(row) != 4 for row in actual_transport[2:])
            or Counter(actual_transport[2:]) != Counter(expected_transport)):
        raise CheckError("transport metric names, types, labels or coverage changed")
    admission = section(text, "## Bounded label and admission contract\n",
                        "## Missing values, lifecycle and resets\n")
    if normalized(admission) != normalized(LABEL_CONTRACT):
        raise CheckError("label admission or per-target series budget changed")
    lifecycle = section(text, "## Missing values, lifecycle and resets\n",
                        "## Transport coverage\n")
    if normalized(lifecycle) != normalized(LIFECYCLE_CONTRACT):
        raise CheckError("missing values, lifecycle or resets changed")
    blocks = re.findall(r"^```yaml\n(.*?)^```$", text, re.MULTILINE | re.DOTALL)
    if len(blocks) != 1:
        raise CheckError("expected one alert YAML block")
    try:
        rules = yaml.load(blocks[0], Loader=UniqueKeyLoader)
        for group in rules["groups"]:
            for rule in group["rules"]:
                rule["expr"] = " ".join(rule["expr"].split())
        if rules != expected_rules():
            raise CheckError("alert rules differ from reviewed selectors and availability joins")
    except (yaml.YAMLError, KeyError, TypeError, AttributeError) as exc:
        raise CheckError(f"invalid alert rules: {exc}") from exc


def main() -> int:
    try:
        validate(DOCUMENT.read_text(encoding="utf-8"))
    except (CheckError, OSError) as exc:
        print(f"Prometheus semantic coverage: {exc}")
        return 1
    print("Prometheus semantic coverage passed: 32 fields, 1024 semantic series + 2 baud series per target.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
