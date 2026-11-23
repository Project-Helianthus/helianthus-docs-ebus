#!/usr/bin/env python3
"""Check the closed deployment metric contract; no exporter/runtime acceptance."""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import re

import yaml


DOCUMENT = Path("deployment/prometheus-semantic-coverage.md")
# Reviewed field/name/unit associations, independent of the document being checked.
SEMANTIC_ROWS = """
thermal.action.state | helianthus_thermal_action_state | enum: idle=0, heating=1, cooling=2, dhw=3, ventilating=4
thermal.demand.level | helianthus_thermal_demand_ratio | ratio; percent / 100
thermal.measurement.air_temperature | helianthus_thermal_air_temperature | Kelvin; identity
thermal.measurement.circuit_flow_temperature | helianthus_thermal_circuit_flow_temperature_kelvin | Kelvin; identity
thermal.measurement.dhw_temperature | helianthus_thermal_dhw_temperature_kelvin | Kelvin; identity
thermal.measurement.flow_rate | helianthus_thermal_flow_cubic_meters_per_second | m³/s; litre/minute / 60,000
thermal.measurement.heat_generator_flow_temperature | helianthus_thermal_heat_generator_flow_temperature_kelvin | Kelvin; identity
thermal.measurement.humidity | helianthus_thermal_relative_humidity_ratio | ratio; percent / 100
thermal.measurement.thermal_power | helianthus_thermal_power_watts | watts; preserve sign
thermal.mode.system | helianthus_thermal_system_mode | enum: off=0, auto=1, heat=2, cool=3
thermal.mode.zone | helianthus_thermal_zone_mode | enum: off=0, auto=1, comfort=2, eco=3
thermal.setpoint.dhw_temperature_setpoint | helianthus_thermal_dhw_setpoint_kelvin | Kelvin; identity; read-only observation
thermal.setpoint.temperature_setpoint | helianthus_thermal_temperature_setpoint | Kelvin; identity; read-only observation
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
ebus_passive_tap_connected | gauge / boolean | none | Proven
ebus_bus_busy_seconds_total | counter / seconds | none | Proven
ebus_bus_busy_ratio | gauge / ratio 0..1 | window: 1m, 5m, 15m, 1h | Proven
ebus_passive_tap_reconnect_attempts_total | counter / attempts | none | Proven
ebus_passive_tap_reconnect_successes_total | counter / connections | none | Proven
ebus_passive_tap_reconnect_failures_total | counter / failures | none | Proven
ebus_baud_observed_symbols_per_second | gauge / physical symbols per second | none | Unknown
ebus_baud_observation_available | gauge / boolean | none | Unknown
CAN transport or semantic measurements | unavailable | none admitted | Unknown
"""
THERMAL_FIXTURE = Path(__file__).resolve().parents[1] / (
    "architecture/fixtures/vaillant-semreg-thermal-map-v1.json"
)
# Structured label domains; field membership comes from the semantic tables.
LABEL_ROWS = """
semantic_values | slot | 0..15
helianthus_semantic_field_available | slot | 0..15
helianthus_semantic_field_available | domain | thermal, infrastructure
helianthus_semantic_field_available | field | domain_field_table
"""

# Closed emitted name/type/label/unit associations.
RENDERER_ROWS = """
active_read_saved_seconds | gauge | family, freshness_profile | none
active_reads_avoided_total | counter | family, freshness_profile | none
ambiguous_total | counter | family, reason | none
direct_apply_total | counter | family, freshness_profile | none
ebus_active_echo_mismatch_subclass_total | counter | subclass | none
ebus_adaptermux_active_arbitration_held | gauge | none | none
ebus_adaptermux_escape_pair_verify_failures_total | counter | step | none
ebus_adaptermux_foreign_initiator_releases_total | counter | none | none
ebus_adaptermux_inter_write_drained_bytes_total | counter | none | none
ebus_adaptermux_stale_active_bytes_discarded_total | counter | none | none
ebus_adaptermux_syn_seen_after_transport_window_expired_total | counter | none | none
ebus_adaptermux_syn_seen_during_grant_window_total | counter | none | none
ebus_adaptermux_syn_seen_while_inter_write_empty_total | counter | none | none
ebus_adaptermux_syn_suppressed_between_writes_total | counter | none | none
ebus_adaptermux_syn_suppressed_pre_echo_total | counter | none | none
ebus_adaptermux_transaction_endings_total | counter | reason | none
ebus_baud_observation_available | gauge | none | none
ebus_bus_busy_ratio | gauge | window | none
ebus_bus_busy_seconds_total | counter | none | none
ebus_dedup_degraded_state | gauge | none | none
ebus_dedup_degraded_total | counter | reason | none
ebus_dedup_epoch_resets_total | counter | none | none
ebus_dedup_local_participant_inbound_total | counter | none | none
ebus_dedup_pending_flush_total | counter | reason | none
ebus_errors_total | counter | class, phase, scope | none
ebus_frame_bytes_total | counter | family, frame_type, part, scope | none
ebus_frames_observed_total | counter | dst, family, frame_type, scope, src | none
ebus_observability_recent_messages | gauge | none | none
ebus_observability_series_budget_overflow_total | counter | none | none
ebus_observability_transport_info | gauge | scope, timing_quality, transport_class | none
ebus_passive_capability_probe_attempts_total | counter | none | none
ebus_passive_capability_probe_outcomes_total | counter | outcome | none
ebus_passive_capability_transitions_total | counter | from, to | none
ebus_passive_capability_unavailable_reason | gauge | reason | none
ebus_passive_completed_transactions_total | counter | none | none
ebus_passive_direct_apply_candidates_evaluated_total | counter | none | none
ebus_passive_fanout_overflow_total | counter | consumer, criticality | none
ebus_passive_reconstructor_abandons_total | counter | reason | none
ebus_passive_reconstructor_invalid_src_class_skipped_total | counter | none | none
ebus_passive_reconstructor_prefix_resync_skipped_total | counter | none | none
ebus_passive_reconstructor_recoveries_total | counter | reason | none
ebus_passive_tap_connected | gauge | none | none
ebus_passive_tap_reconnect_attempts_total | counter | none | none
ebus_passive_tap_reconnect_failures_total | counter | none | none
ebus_passive_tap_reconnect_successes_total | counter | none | none
ebus_passive_warmup_blocker_reason | gauge | reason | none
ebus_passive_warmup_completed_transactions | gauge | none | none
ebus_passive_warmup_completion_mode | gauge | mode | none
ebus_passive_warmup_elapsed_seconds | gauge | none | none
ebus_passive_warmup_required_transactions | gauge | none | none
ebus_passive_warmup_state | gauge | state | none
ebus_periodicity_tuple_budget_overflow_total | counter | none | none
energy_broadcast_freshness_transitions_total | counter | from, to | none
energy_broadcast_selectors | gauge | state | none
external_write_policy_state | gauge | policy | none
feature_flag_enabled | gauge | flag | none
feature_flag_normalizations_total | counter | reason | none
helianthus_huawei_transport_events_total | counter | family, function, outcome | none
helianthus_infrastructure_ac_active_power_watts | gauge | slot | none
helianthus_infrastructure_ac_apparent_power_volt_amperes | gauge | slot | none
helianthus_infrastructure_ac_current_amperes | gauge | slot | none
helianthus_infrastructure_ac_frequency_hertz | gauge | slot | none
helianthus_infrastructure_ac_power_factor_ratio | gauge | slot | none
helianthus_infrastructure_ac_reactive_power_vars | gauge | slot | none
helianthus_infrastructure_ac_voltage_volts | gauge | slot | none
helianthus_infrastructure_apparent_power_volt_amperes | gauge | slot | none
helianthus_infrastructure_breaker_open | gauge | slot | none
helianthus_infrastructure_connection_connected | gauge | slot | none
helianthus_infrastructure_energy_export_joules | gauge | slot | none
helianthus_infrastructure_energy_import_joules | gauge | slot | none
helianthus_infrastructure_export_active_power_watts | gauge | slot | none
helianthus_infrastructure_export_reactive_power_vars | gauge | slot | none
helianthus_infrastructure_fault_present | gauge | slot | none
helianthus_infrastructure_import_active_power_watts | gauge | slot | none
helianthus_infrastructure_import_reactive_power_vars | gauge | slot | none
helianthus_infrastructure_interlock_active | gauge | slot | none
helianthus_infrastructure_ready | gauge | slot | none
helianthus_native_temperature | gauge | protocol, device, index, point, unit, driver_instance | kelvin
helianthus_native_temperature_difference | gauge | protocol, device, index, point, unit, driver_instance | kelvin
helianthus_native_pressure | gauge | protocol, device, index, point, unit, driver_instance | pascals
helianthus_native_volume_flow | gauge | protocol, device, index, point, unit, driver_instance | cubic_meters_per_second
helianthus_native_energy | gauge | protocol, device, index, point, unit, driver_instance | joules
helianthus_native_power | gauge | protocol, device, index, point, unit, driver_instance | watts
helianthus_native_time | gauge | protocol, device, index, point, unit, driver_instance | seconds
helianthus_native_ratio | gauge | protocol, device, index, point, unit, driver_instance | ratio
helianthus_native_count | gauge | protocol, device, index, point, unit, driver_instance | count
helianthus_native_rotational_speed | gauge | protocol, device, index, point, unit, driver_instance | hertz
helianthus_native_frequency | gauge | protocol, device, index, point, unit, driver_instance | hertz
helianthus_native_current | gauge | protocol, device, index, point, unit, driver_instance | amperes
helianthus_native_voltage | gauge | protocol, device, index, point, unit, driver_instance | volts
helianthus_native_point_age | gauge | protocol, device, index, point, unit, driver_instance | seconds
helianthus_native_render_overflow | gauge | none | none
helianthus_payload_aa_auto_syn_absorbed_total | counter | none | none
helianthus_payload_aa_auto_syn_drain_exhausted_total | counter | none | none
helianthus_payload_aa_auto_syn_recovered_total | counter | none | none
helianthus_round9_absorb_entered_total | counter | none | none
helianthus_semantic_evidence_age | gauge | connector, dimension, fact, pack, resource, resource_kind, unit | seconds
helianthus_semantic_fact_state | gauge | availability, connector, dimension, fact, freshness, pack, promotion, qualification, quality, resource, resource_kind | none
helianthus_semantic_fact_value | gauge | connector, dimension, fact, pack, resource, resource_kind, unit | none
helianthus_semantic_field_available | gauge | domain, field, slot | none
helianthus_semantic_open_conflicts | gauge | connector, dimension, fact, pack, resource, resource_kind | none
helianthus_semantic_projection_available | gauge | domain | none
helianthus_semantic_projection_item | gauge | domain, item, outcome | none
helianthus_semantic_projection_loss | gauge | domain, item, loss_kind | none
helianthus_semantic_render_overflow | gauge | none | none
helianthus_thermal_action_state | gauge | slot | none
helianthus_thermal_air_temperature | gauge | slot, unit | kelvin
helianthus_thermal_circuit_flow_temperature_kelvin | gauge | slot | none
helianthus_thermal_demand_ratio | gauge | slot | none
helianthus_thermal_dhw_setpoint_kelvin | gauge | slot | none
helianthus_thermal_dhw_temperature_kelvin | gauge | slot | none
helianthus_thermal_fault_present | gauge | slot | none
helianthus_thermal_flow_cubic_meters_per_second | gauge | slot | none
helianthus_thermal_heat_generator_flow_temperature_kelvin | gauge | slot | none
helianthus_thermal_operation_active | gauge | slot | none
helianthus_thermal_power_watts | gauge | slot | none
helianthus_thermal_relative_humidity_ratio | gauge | slot | none
helianthus_thermal_temperature_setpoint | gauge | slot, unit | kelvin
helianthus_thermal_system_mode | gauge | slot | none
helianthus_thermal_zone_mode | gauge | slot | none
helianthus_transport_runtime_status | gauge | outcome, protocol, reason, state | none
helianthus_v8_shadow_would_have_dropped_total | counter | none | none
missed_due_to_transport_limitations_total | counter | family, freshness_profile, limitation | none
passive_hits_total | counter | family, freshness_profile | none
"""

# Emitted native point families: name, type, quantity, constant unit, labels
# and status. Each tuple agrees with the emitted table.
NATIVE_ROWS = """
helianthus_native_temperature | gauge | temperature | kelvin | protocol, device, index, point, unit, driver_instance | emitted
helianthus_native_temperature_difference | gauge | temperature difference | kelvin | protocol, device, index, point, unit, driver_instance | emitted
helianthus_native_pressure | gauge | pressure | pascals | protocol, device, index, point, unit, driver_instance | emitted
helianthus_native_volume_flow | gauge | volume flow | cubic_meters_per_second | protocol, device, index, point, unit, driver_instance | emitted
helianthus_native_energy | gauge | energy | joules | protocol, device, index, point, unit, driver_instance | emitted
helianthus_native_power | gauge | power | watts | protocol, device, index, point, unit, driver_instance | emitted
helianthus_native_time | gauge | time | seconds | protocol, device, index, point, unit, driver_instance | emitted
helianthus_native_ratio | gauge | ratio | ratio | protocol, device, index, point, unit, driver_instance | emitted
helianthus_native_count | gauge | count | count | protocol, device, index, point, unit, driver_instance | emitted
helianthus_native_rotational_speed | gauge | rotational speed | hertz | protocol, device, index, point, unit, driver_instance | emitted
helianthus_native_frequency | gauge | frequency | hertz | protocol, device, index, point, unit, driver_instance | emitted
helianthus_native_current | gauge | electric current | amperes | protocol, device, index, point, unit, driver_instance | emitted
helianthus_native_voltage | gauge | voltage | volts | protocol, device, index, point, unit, driver_instance | emitted
helianthus_native_point_age | gauge | age of the held observation | seconds | protocol, device, index, point, unit, driver_instance | emitted
helianthus_native_render_overflow | gauge | value series omitted in the scrape | none | none | emitted
"""
# Closed native label keys and their documented domains.
NATIVE_LABEL_ROWS = """
protocol | ebus, modbus, eebus, can
device | documented_device_class
index | documented_instance_index
point | canonical_register_name
unit | family_constant_unit
driver_instance | stable_instance_component
"""
NATIVE_LABEL_KEYS = frozenset({"protocol", "device", "index", "point", "unit", "driver_instance"})
SI_UNITS = frozenset({"kelvin", "pascals", "cubic_meters_per_second", "joules", "watts",
                      "seconds", "ratio", "count", "hertz", "amperes", "volts"})
NATIVE_NAME = re.compile(r"helianthus_native_[a-z]+(?:_[a-z]+)*")
NATIVE_FAMILY_HEADER = ("Series", "Type", "Quantity", "Constant unit", "Labels", "Status")


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
         "5m", "warning"),
        ("HelianthusBaudObservationUnavailable", "ebus_baud_observation_available == 0",
         "10m", "info"),
        ("HelianthusSemanticFieldUnavailable", "helianthus_semantic_field_available == 0",
         "10m", "info"),
        ("HelianthusThermalFaultObserved",
         '(helianthus_thermal_fault_present == 1) and on(job, instance, slot) '
         '(helianthus_semantic_field_available{domain="thermal",field="thermal.status.fault"} == 1)',
         "2m", "warning"),
        ("HelianthusInfrastructureInterlockObserved",
         '(helianthus_infrastructure_interlock_active == 1) and on(job, instance, slot) '
         '(helianthus_semantic_field_available{domain="infrastructure",field="infrastructure.status.interlock"} == 1)',
         "2m", "warning"),
    ]
    return {"groups": [{"name": "helianthus.bounded-coverage", "rules": [
        {"alert": name, "expr": expr, "for": duration,
         "labels": {"severity": severity}}
        for name, expr, duration, severity in examples
    ]}]}


def _validate_thermal_dispositions(text: str, thermal_fixture: Path) -> None:
    dispositions = section(text, "## Thermal mapping dispositions\n", "## Offline alert examples\n")
    try:
        mappings = json.loads(thermal_fixture.read_text(encoding="utf-8"))["mappings"]
        exact = {(row["semreg_fact"],) for row in mappings if row["disposition"] == "exact"}
        withheld = [(row["legacy_system_field"], row["loss"])
                    for row in mappings if row["disposition"] == "withheld"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise CheckError(f"invalid thermal mapping fixture: {exc}") from exc
    exact_claims = section(dispositions, "### Exact fact IDs\n", "### Withheld associations\n")
    withheld_claims = dispositions.split("### Withheld associations\n", 1)[1]
    if Counter(rows(exact_claims)) != Counter(list(exact) + [("semreg_fact",), ("---",)]):
        raise CheckError("exact fact IDs differ from the source fixture")
    if Counter(rows(withheld_claims)) != Counter(withheld + [
            ("legacy_system_field", "loss"), ("---", "---")]):
        raise CheckError("withheld associations differ from the source fixture")


def table(text: str) -> list[tuple[str, ...]]:
    return rows("\n".join("| " + line for line in text.strip().splitlines()))


def _check_native_family(row: tuple[str, ...], emitted: dict[str, tuple[str, ...]]) -> None:
    name, kind, _quantity, unit, labels, status = row
    if not NATIVE_NAME.fullmatch(name) or name.endswith("_total") or any(
            name.endswith("_" + suffix) for suffix in SI_UNITS - {"ratio", "count"}):
        raise CheckError(f"invalid native family name: {name}")
    if kind != "gauge" or status != "emitted":
        raise CheckError(f"native family must be an emitted gauge: {name}")
    keys = [] if labels == "none" else labels.split(", ")
    if len(keys) != len(set(keys)) or not set(keys) <= NATIVE_LABEL_KEYS:
        raise CheckError(f"forbidden native label key: {name}")
    if labels != "none" and "driver_instance" not in keys:
        raise CheckError(f"native family drops driver_instance: {name}")
    if ("unit" in keys) != (unit in SI_UNITS) or ("unit" not in keys and unit != "none"):
        raise CheckError(f"native family needs exactly one constant SI unit: {name}")
    match = emitted.get(name)
    if match is None:
        raise CheckError(f"native family is not a member of the emitted table: {name}")
    if match != (name, kind, labels, unit):
        raise CheckError(f"native family tuple differs from the emitted table: {name}")


NATIVE_LIFETIME_RULES = (
    "A label set belongs to one native identity for the lifetime of the scrape target",
)
NATIVE_INDEX_RULE = (
    "A row without a documented instance index has no `index` label."
)
OLD_ADMISSION_SENTENCE = (
    "lifetime admission set of value series, each keyed by its family name "
    "together with its label set"
)
# The unit rule covers the value and age families only; the overflow family
# carries neither labels nor a unit.
NATIVE_UNIT_RULES = (
    "Each value family and the age family has exactly one constant `unit` label value, and it is SI.",
    "`helianthus_native_render_overflow` has no labels and no unit.",
)


def _validate_native_family_table(native: str, emitted: dict[str, tuple[str, ...]]) -> None:
    families = rows(section(native, "### Native families\n", "### Native labels\n"))
    if (families[:2] != [NATIVE_FAMILY_HEADER, ("---",) * 6]
            or any(len(row) != 6 for row in families[2:])):
        raise CheckError("native family table header or row shape differs")
    for row in families[2:]:
        _check_native_family(row, emitted)
    names = [row[0] for row in families[2:]]
    if len(names) != len(set(names)):
        raise CheckError("native family has more than one row or unit")
    if Counter(families[2:]) != Counter(table(NATIVE_ROWS)):
        raise CheckError("native families differ from the reviewed emitted rows")


def _validate_native_labels_and_rules(native: str) -> None:
    labels = rows(section(native, "### Native labels\n", "### Clear interpretation\n"))
    if (Counter(labels) != Counter(table(NATIVE_LABEL_ROWS) + [
            ("Label", "Allowed domain"), ("---", "---")])
            or {row[0] for row in labels[2:]} != NATIVE_LABEL_KEYS):
        raise CheckError("native label keys or domains differ from the closed vocabulary")
    flat = " ".join(native.split())
    if any(rule not in flat for rule in NATIVE_LIFETIME_RULES):
        raise CheckError("native label and series lifetime rules are missing")
    if NATIVE_INDEX_RULE not in flat:
        raise CheckError("native index rule is missing")
    if OLD_ADMISSION_SENTENCE in flat or "1,024 value series" in flat:
        raise CheckError("native section still carries the old admission-set sentence")
    if (any(rule not in flat for rule in NATIVE_UNIT_RULES)
            or "Each family has exactly one constant unit" in normalized(native)):
        raise CheckError("native unit rule must exempt the label-free overflow family")


def _validate_native_points(text: str, emitted: dict[str, tuple[str, ...]]) -> None:
    if text.count("## Native point coverage\n") != 1:
        raise CheckError("missing or duplicate native point coverage section")
    native = text.split("## Native point coverage\n", 1)[1]
    _validate_native_family_table(native, emitted)
    _validate_native_labels_and_rules(native)


def validate(text: str, *, thermal_fixture: Path = THERMAL_FIXTURE) -> None:
    emitted = section(text, "## Emitted metric names\n", "## Provisional metric exceptions\n")
    expected_emitted = rows("\n".join("| " + line for line in RENDERER_ROWS.strip().splitlines()))
    actual_emitted = rows(emitted)
    if Counter(actual_emitted) != Counter(expected_emitted + [
            ("Series", "Type", "Labels", "Constant unit"), ("---", "---", "---", "---")]):
        raise CheckError("emitted metric name/type/labels/constant unit differ")
    names = [row[0] for row in expected_emitted]
    if len(names) != len(set(names)):
        raise CheckError("emitted metric name collision")
    semantic = section(text, "## Semantic coverage and units\n", "## Thermal mapping dispositions\n")
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
    if (len(set(fields)) != 34 or len(set(names)) != 34
            or sum(field.startswith("thermal.") for field in fields) != 15
            or sum(field.startswith("infrastructure.") for field in fields) != 19
            or len(fields) * 16 * 2 != 1088):
        raise CheckError("invalid reviewed field count or legacy configured-slot estimate")
    transport = section(text, "## Transport coverage\n", "## Semantic coverage and units\n")
    actual_transport = rows(transport)
    expected_transport = rows("\n".join("| " + line for line in TRANSPORT_ROWS.strip().splitlines()))
    if (actual_transport[:2] != [
            ("Series", "Type / unit", "Labels", "Owner, missing behavior and coverage", "Status"),
            ("---", "---", "---", "---", "---")]
            or any(len(row) != 5 for row in actual_transport[2:])
            or Counter(row[:3] + row[4:] for row in actual_transport[2:])
            != Counter(expected_transport)):
        raise CheckError("transport metric names, types, labels or coverage changed")
    admission = section(text, "## Bounded label and admission contract\n",
                        "## Missing values, lifecycle and resets\n")
    expected_labels = rows("\n".join("| " + line for line in LABEL_ROWS.strip().splitlines()))
    if Counter(rows(admission)) != Counter(expected_labels + [
            ("Series group", "Label", "Allowed domain"), ("---", "---", "---")]):
        raise CheckError("structured label domains differ from the contract")
    _validate_thermal_dispositions(text, thermal_fixture)
    _validate_native_points(text, {row[0]: row for row in expected_emitted})
    blocks = re.findall(r"^```yaml\n(.*?)^```$", text, re.MULTILINE | re.DOTALL)
    if len(blocks) != 1:
        raise CheckError("expected one alert YAML block")
    try:
        rules = yaml.load(blocks[0], Loader=UniqueKeyLoader)
        for group in rules["groups"]:
            for rule in group["rules"]:
                rule["expr"] = " ".join(rule["expr"].split())
                rule.pop("annotations", None)
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
    print("Prometheus semantic coverage passed: 34 bounded fields, 124 emitted metric "
          "families and 15 emitted native families.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
