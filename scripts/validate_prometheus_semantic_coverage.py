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
ebus_passive_tap_connected | gauge / boolean | none
ebus_bus_busy_seconds_total | counter / seconds | none
ebus_bus_busy_ratio | gauge / ratio 0..1 | window: 1m, 5m, 15m, 1h
ebus_passive_tap_reconnect_attempts_total | counter / attempts | none
ebus_passive_tap_reconnect_successes_total | counter / connections | none
ebus_passive_tap_reconnect_failures_total | counter / failures | none
ebus_baud_observed_symbols_per_second | gauge / physical symbols per second | none
ebus_baud_observation_available | gauge / boolean | none
CAN transport or semantic measurements | unavailable | none admitted
"""
# These clauses jointly define label admission and the series-budget arithmetic.
LABEL_CONTRACT = """
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
        raise CheckError("invalid reviewed field count or series budget")
    transport = section(text, "## Transport coverage\n", "## Semantic coverage and units\n")
    actual_transport = rows(transport)
    expected_transport = rows("\n".join("| " + line for line in TRANSPORT_ROWS.strip().splitlines()))
    if (actual_transport[:2] != [
            ("Series", "Type / unit", "Labels", "Owner, missing behavior and coverage"),
            ("---", "---", "---", "---")]
            or any(len(row) != 4 for row in actual_transport[2:])
            or Counter(row[:3] for row in actual_transport[2:]) != Counter(expected_transport)):
        raise CheckError("transport metric names, types or labels changed")
    admission = section(text, "## Bounded label and admission contract\n",
                        "## Missing values, lifecycle and resets\n")
    if normalized(admission.split("- Do not export", 1)[0]) != normalized(LABEL_CONTRACT):
        raise CheckError("label admission or series budget changed")
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
    print("Prometheus semantic coverage passed: 32 fields, 1024 semantic series + 2 baud series.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
