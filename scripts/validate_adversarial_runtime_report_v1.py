#!/usr/bin/env python3
"""Fail-closed validator for the public adversarial runtime report v1."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "docs/platform/schemas/adversarial-runtime-report-v1.schema.json"
SCHEMA_ID = "https://raw.githubusercontent.com/Project-Helianthus/helianthus-docs-ebus/main/docs/platform/schemas/adversarial-runtime-report-v1.schema.json"
SUITE_ID = "helianthus.adversarial.ADV01-04"
FIXTURE_MANIFEST = ROOT / "docs/platform/fixtures/adversarial-runtime/v1/fixture-input-manifest.json"
MAX_BYTES = 1024 * 1024
TS_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"

CATALOG = {
    "ADV-01": {
        "name": "HA Core/integration consumer restart while gateway stays stable",
        "trigger_kind": "ha_consumer_restart",
        "recovery_target": "ha_consumer_synchronized",
        "maximum_recovery_ms": 90000,
        "zones_required": True,
        "dhw_required": True,
        "maximum_collisions_delta": 5,
        "events": ["restart_requested", "consumer_stopped", "consumer_started", "ha_consumer_synchronized"],
        "anchor": "consumer_stopped",
        "recovery_event": "ha_consumer_synchronized",
    },
    "ADV-02": {
        "name": "eBUS adapter reset while polling",
        "trigger_kind": "adapter_reset",
        "recovery_target": "gateway_live_ready",
        "maximum_recovery_ms": 120000,
        "zones_required": True,
        "dhw_required": False,
        "maximum_collisions_delta": 20,
        "events": ["reset_requested", "reset_started", "transport_unavailable", "transport_available", "gateway_live_ready"],
        "anchor": "reset_started",
        "recovery_event": "gateway_live_ready",
    },
    "ADV-03": {
        "name": "60 second gateway-to-adapter transport partition and recovery",
        "trigger_kind": "transport_partition",
        "recovery_target": "gateway_live_ready",
        "maximum_recovery_ms": 90000,
        "zones_required": True,
        "dhw_required": False,
        "maximum_collisions_delta": 10,
        "events": ["partition_requested", "partition_active", "partition_cleared", "gateway_live_ready"],
        "anchor": "partition_cleared",
        "recovery_event": "gateway_live_ready",
    },
    "ADV-04": {
        "name": "fresh isolated gateway boot with corrupted cache fixture",
        "trigger_kind": "isolated_corrupt_cache_boot",
        "recovery_target": "gateway_live_ready",
        "maximum_recovery_ms": 120000,
        "zones_required": True,
        "dhw_required": True,
        "maximum_collisions_delta": 5,
        "events": ["isolated_cache_staged", "runtime_started", "gateway_live_ready"],
        "anchor": "runtime_started",
        "recovery_event": "gateway_live_ready",
    },
}


class ValidationError(ValueError):
    pass


def _no_duplicates(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValidationError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _non_integer_number(value):
    raise ValidationError(f"non-integer JSON number: {value}")


def _non_finite_number(value):
    raise ValidationError(f"non-finite JSON number: {value}")


def load_report(path: Path):
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValidationError(f"report exceeds {MAX_BYTES} bytes")
    try:
        text = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as error:
        raise ValidationError("report is not valid UTF-8") from error
    try:
        return json.loads(
            text,
            object_pairs_hook=_no_duplicates,
            parse_float=_non_integer_number,
            parse_constant=_non_finite_number,
        )
    except json.JSONDecodeError as error:
        raise ValidationError(f"malformed JSON: {error.msg}") from error


def _stamp(value):
    try:
        return dt.datetime.strptime(value, TS_FORMAT).replace(tzinfo=dt.timezone.utc)
    except (TypeError, ValueError) as error:
        raise ValidationError("timestamp is outside the restricted RFC3339 profile") from error


def _same_timestamp(anchor, offset_ms, observed):
    try:
        expected = anchor + dt.timedelta(milliseconds=offset_ms)
    except OverflowError as error:
        raise ValidationError("timestamp offset overflows supported datetime range") from error
    return abs((expected - _stamp(observed)).total_seconds() * 1000) <= 1


def _error(errors, rule):
    errors.add(rule)


def _validate_catalog(definition, errors):
    scenario_id = definition.get("scenario_id")
    expected = CATALOG.get(scenario_id)
    if expected is None:
        _error(errors, "scenario_catalog")
        return None
    fields = {
        "name": expected["name"],
        "duration_limit_ms": 180000,
        "trigger_kind": expected["trigger_kind"],
        "recovery_target": expected["recovery_target"],
        "maximum_recovery_ms": expected["maximum_recovery_ms"],
        "minimum_live_epoch_delta": 2,
        "zones_required": expected["zones_required"],
        "dhw_required": expected["dhw_required"],
        "maximum_collisions_delta": expected["maximum_collisions_delta"],
    }
    for field, value in fields.items():
        if definition.get(field) != value:
            _error(errors, "scenario_catalog")
    return expected


def _event_offsets(events, start, errors, *, elapsed_ms=None):
    offsets = {}
    previous = -1
    for event in events:
        kind = event["kind"]
        offset = event["offset_ms"]
        if offset < previous or kind in offsets:
            _error(errors, "action_order")
        previous = offset
        offsets[kind] = offset
        if elapsed_ms is not None and offset > elapsed_ms:
            _error(errors, "action_bounds")
            continue
        if not _same_timestamp(start, offset, event["at"]):
            _error(errors, "wall_monotonic_binding")
    return offsets


def _validate_evaluated(scenario, expected, errors):
    definition = scenario["definition"]
    timing = scenario["timing"]
    metrics = scenario["metrics"]
    evaluation = scenario["evaluation"]
    start = _stamp(timing["scenario_started_at"])
    end = _stamp(timing["scenario_ended_at"])
    if end < start or not _same_timestamp(start, timing["elapsed_ms"], timing["scenario_ended_at"]):
        _error(errors, "wall_monotonic_binding")

    events = scenario["action"]["events"]
    kinds = [event["kind"] for event in events]
    if kinds != expected["events"]:
        _error(errors, "action_semantics")
    offsets = _event_offsets(events, start, errors, elapsed_ms=timing["elapsed_ms"])
    if timing["error_bound_ms"] < max((event["error_bound_ms"] for event in events), default=0):
        _error(errors, "timing_error_bound")
    anchor = expected["anchor"]
    recovery_event = expected["recovery_event"]
    if timing["recovery_anchor"] != anchor or timing["recovery_observed"] != recovery_event:
        _error(errors, "action_semantics")
    if anchor not in offsets or recovery_event not in offsets:
        _error(errors, "action_semantics")
        recovery_ms = None
        recovery_error_bound_ms = None
    else:
        recovery_ms = offsets[recovery_event] - offsets[anchor]
        event_by_kind = {event["kind"]: event for event in events}
        recovery_error_bound_ms = (
            event_by_kind[anchor]["error_bound_ms"]
            + event_by_kind[recovery_event]["error_bound_ms"]
        )
    if recovery_ms is None or timing["recovery_ms"] != recovery_ms:
        _error(errors, "recovery_measurement")

    if definition["scenario_id"] == "ADV-03":
        if "partition_active" not in offsets or "partition_cleared" not in offsets:
            _error(errors, "partition_duration")
        else:
            event_by_kind = {event["kind"]: event for event in events}
            partition_error_bound_ms = (
                event_by_kind["partition_active"]["error_bound_ms"]
                + event_by_kind["partition_cleared"]["error_bound_ms"]
            )
            if abs(offsets["partition_cleared"] - offsets["partition_active"] - 60000) + partition_error_bound_ms > 1000:
                _error(errors, "partition_duration")

    baseline, finish, delta = metrics["baseline"], metrics["end"], metrics["delta"]
    if baseline["counter_epoch"] != finish["counter_epoch"]:
        _error(errors, "counter_epoch")
    for snap in (baseline, finish):
        if not _same_timestamp(start, snap["offset_ms"], snap["captured_at"]):
            _error(errors, "wall_monotonic_binding")
    if baseline["offset_ms"] > finish["offset_ms"] or finish["offset_ms"] > timing["elapsed_ms"]:
        _error(errors, "snapshot_order")
    if abs(baseline["offset_ms"]) > timing["error_bound_ms"] or abs(finish["offset_ms"] - timing["elapsed_ms"]) > timing["error_bound_ms"]:
        _error(errors, "snapshot_window")
    live_delta = finish["semantic_live_epoch"] - baseline["semantic_live_epoch"]
    collision_delta = finish["semantic_bus_collisions_total"] - baseline["semantic_bus_collisions_total"]
    if live_delta < 0 or collision_delta < 0:
        _error(errors, "negative_counter_delta")
    if delta != {"semantic_live_epoch": live_delta, "semantic_bus_collisions_total": collision_delta}:
        _error(errors, "counter_delta")

    duration = evaluation["duration"]
    action = evaluation["action"]
    recovery = evaluation["recovery"]
    live = evaluation["live_epoch"]
    zones = evaluation["zones"]
    dhw = evaluation["dhw"]
    collisions = evaluation["collisions"]
    if duration["error_bound_ms"] != timing["error_bound_ms"] or recovery["error_bound_ms"] != recovery_error_bound_ms:
        _error(errors, "timing_error_bound")
    expected_decisions = {
        "duration": abs(timing["elapsed_ms"] - 180000) + timing["error_bound_ms"] <= 1000,
        "action": not {"action_semantics", "partition_duration"} & errors,
        "recovery": recovery_ms is not None and recovery_ms + recovery_error_bound_ms <= expected["maximum_recovery_ms"],
        "live_epoch": live_delta >= 2,
        "zones": (not expected["zones_required"]) or finish["semantic_zone_count"] > 0,
        "dhw": (not expected["dhw_required"]) or finish["semantic_dhw_present"],
        "collisions": collision_delta <= expected["maximum_collisions_delta"],
    }
    if timing["elapsed_ms"] < 179000 or timing["elapsed_ms"] > 181000:
        _error(errors, "duration_window")
    if duration["observed_ms"] != timing["elapsed_ms"] or duration["passed"] != expected_decisions["duration"]:
        _error(errors, "duration_decision")
    if action != {"expected_kind": definition["trigger_kind"], "observed_kind": definition["trigger_kind"], "passed": expected_decisions["action"]}:
        _error(errors, "action_decision")
    if recovery["maximum_ms"] != expected["maximum_recovery_ms"] or recovery["observed_ms"] != recovery_ms or recovery["passed"] != expected_decisions["recovery"]:
        _error(errors, "recovery_decision")
    if live != {"minimum": 2, "observed": live_delta, "passed": expected_decisions["live_epoch"]}:
        _error(errors, "live_epoch_decision")
    if zones != {"required": expected["zones_required"], "observed": finish["semantic_zone_count"] > 0, "passed": expected_decisions["zones"]}:
        _error(errors, "zones_decision")
    if dhw != {"required": expected["dhw_required"], "observed": finish["semantic_dhw_present"], "passed": expected_decisions["dhw"]}:
        _error(errors, "dhw_decision")
    if collisions != {"maximum": expected["maximum_collisions_delta"], "observed": collision_delta, "passed": expected_decisions["collisions"]}:
        _error(errors, "collisions_decision")
    expected_outcome = "pass" if all(expected_decisions.values()) and not errors else "fail"
    if scenario["outcome"] != expected_outcome:
        _error(errors, "evaluated_outcome")


def validate_semantics(report):
    errors = set()
    try:
        execution = report["execution"]
        if report["$schema"] != SCHEMA_ID or report["schema_version"] != 1 or report["suite"] != {"id": SUITE_ID, "version": 1}:
            _error(errors, "contract_identity")
        if _stamp(execution["completed_at"]) < _stamp(execution["started_at"]):
            _error(errors, "execution_order")
        provenance = report["provenance"]
        subject = provenance["subject"]
        producer = provenance["producer"]
        if subject["source_tree"] == "dirty" and report["summary"]["verdict"] == "pass":
            _error(errors, "dirty_provenance_pass")
        is_gateway_producer = producer["repository"] == "Project-Helianthus/helianthus-ebusgateway"
        is_ha_producer = producer["repository"] == "Project-Helianthus/helianthus-ha-integration"
        if is_gateway_producer:
            if (producer["component"], producer["build_kind"], execution["mode"], subject["artifact_kind"], producer["input_gateway_report_sha256"]) != ("internal/adversarial", "go-test-binary", "offline-fixture", "gateway-fixture-set", None):
                _error(errors, "producer_subject_pairing")
            if any(any(event["source"] != "fixture" for event in item["action"]["events"]) for item in report["scenarios"]):
                _error(errors, "producer_subject_pairing")
        elif is_ha_producer:
            if (producer["component"], producer["build_kind"]) != ("ha-adversarial-harness", "ha-harness"):
                _error(errors, "producer_subject_pairing")
            if execution["mode"] == "offline-fixture":
                if subject["artifact_kind"] != "gateway-fixture-set" or producer["input_gateway_report_sha256"] is None or any(any(event["source"] != "fixture" for event in item["action"]["events"]) for item in report["scenarios"]):
                    _error(errors, "producer_subject_pairing")
            elif execution["mode"] == "operator-live":
                if subject["artifact_kind"] != "gateway-binary" or producer["input_gateway_report_sha256"] is not None:
                    _error(errors, "producer_subject_pairing")
                if any(any(event["source"] != "observer" for event in item["action"]["events"]) for item in report["scenarios"]):
                    _error(errors, "producer_subject_pairing")
        else:
            _error(errors, "producer_subject_pairing")
        fixture_digest = hashlib.sha256(FIXTURE_MANIFEST.read_bytes()).hexdigest()
        if subject["artifact_kind"] == "gateway-fixture-set" and (provenance["fixture_set_sha256"] != subject["artifact_sha256"] or subject["artifact_sha256"] != fixture_digest):
            _error(errors, "fixture_subject_binding")
        if subject["artifact_kind"] == "gateway-binary" and provenance["fixture_set_sha256"] is not None:
            _error(errors, "fixture_subject_binding")
        scenarios = report["scenarios"]
        run_start = _stamp(execution["started_at"])
        run_end = _stamp(execution["completed_at"])
        previous_end = None
        for index, scenario in enumerate(scenarios):
            scenario_start = _stamp(scenario["timing"]["scenario_started_at"])
            scenario_end = _stamp(scenario["timing"]["scenario_ended_at"])
            if scenario_start < run_start or scenario_end > run_end or scenario_end < scenario_start:
                _error(errors, "scenario_run_containment")
            if (index == 0 and scenario_start != run_start) or (index == len(scenarios) - 1 and scenario_end != run_end):
                _error(errors, "scenario_run_binding")
            if previous_end is not None and scenario_start != previous_end:
                _error(errors, "scenario_sequence")
            if scenario["timing"]["error_bound_ms"] < max((event["error_bound_ms"] for event in scenario["action"]["events"]), default=0):
                _error(errors, "timing_error_bound")
            previous_end = scenario_end
        ids = [item["definition"]["scenario_id"] for item in scenarios]
        if ids != list(CATALOG):
            _error(errors, "scenario_order")
        if len(set(ids)) != 4:
            _error(errors, "scenario_identity")
        for scenario in scenarios:
            scenario_errors = set()
            expected = _validate_catalog(scenario["definition"], scenario_errors)
            if expected is None:
                errors.update(scenario_errors)
                continue
            kind = scenario["result_kind"]
            events = scenario["action"]["events"]
            timing = scenario["timing"]
            start = _stamp(timing["scenario_started_at"])
            event_kinds = [event["kind"] for event in events]
            if event_kinds != expected["events"][: len(events)]:
                _error(scenario_errors, "action_prefix")
            _event_offsets(events, start, scenario_errors, elapsed_ms=timing["elapsed_ms"])
            if kind == "evaluated":
                if scenario["errors"] or any(scenario["metrics"][field] is None for field in ("baseline", "end", "delta")) or scenario["evaluation"] is None:
                    _error(scenario_errors, "evaluated_shape")
                _validate_evaluated(scenario, expected, scenario_errors)
            elif kind == "infrastructure-block":
                if events or scenario["outcome"] != "blocked-infra" or scenario["errors"] != [{"phase": "precondition", "code": "precondition_unavailable"}] or scenario["evaluation"] is not None or any(scenario["metrics"][field] is not None for field in ("baseline", "end", "delta")) or any(timing[field] is not None for field in ("recovery_anchor", "recovery_observed", "recovery_ms")):
                    _error(scenario_errors, "infrastructure_block_precedence")
            elif kind == "execution-error":
                if scenario["outcome"] != "fail" or not scenario["errors"] or scenario["evaluation"] is not None or any(scenario["metrics"][field] is not None for field in ("baseline", "end", "delta")):
                    _error(scenario_errors, "execution_error_precedence")
            else:
                _error(scenario_errors, "result_kind")
            errors.update(scenario_errors)

        outcomes = [item["outcome"] for item in scenarios]
        summary = report["summary"]
        counts = {
            "total": len(scenarios),
            "passed": outcomes.count("pass"),
            "failed": outcomes.count("fail"),
            "xfailed": 0,
            "blocked": outcomes.count("blocked-infra"),
            "unknown": 0,
        }
        if any(summary.get(key) != value for key, value in counts.items()):
            _error(errors, "summary_accounting")
        verdict = "fail" if counts["failed"] else "blocked-infra" if counts["blocked"] else "pass"
        if summary.get("verdict") != verdict:
            _error(errors, "summary_verdict")
    except (KeyError, TypeError, ValidationError):
        _error(errors, "structural_shape")
    return sorted(errors)


def validate_schema(path: Path):
    result = subprocess.run(["jv", str(SCHEMA), str(path)], text=True, capture_output=True, check=False)
    if result.returncode:
        raise ValidationError("schema: " + (result.stdout + result.stderr).strip())


def validate_path(path: Path):
    report = load_report(path)
    validate_schema(path)
    errors = validate_semantics(report)
    if errors:
        raise ValidationError("semantic: " + ",".join(errors))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args(argv)
    try:
        validate_path(args.report)
    except ValidationError as error:
        print(f"adversarial_runtime_report_v1_invalid: {error}", file=sys.stderr)
        return 1
    print("adversarial_runtime_report_v1_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
