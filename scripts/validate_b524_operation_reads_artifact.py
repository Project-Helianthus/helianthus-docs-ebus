#!/usr/bin/env python3
"""Validate semantic B524 operation-read artifact invariants."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class ValidationError(ValueError):
    pass


CHANNELS = {
    "ventilation": (0, 0, 1),
    "noise-reduction": (0, 0, 2),
    "tariff": (0, 0, 3),
    "dhw": (1, 0, 1),
    "circulation": (1, 0, 2),
    "zone-cooling": (3, None, 1),
    "zone-heating": (3, None, 2),
}
PROFILES = {"system": 0, "dhw": 1, "zone": 3}
OPCODES = {"ReadTimer": 0x03, "ReadVR91": 0x08, "GetEvent": 0x09, "GetEventSetPoint": 0x0B}
RESPONSE_LENGTHS = {"ReadTimer": 7, "ReadVR91": 8, "GetEvent": 8, "GetEventSetPoint": 8}
VRC700_DEVICE_IDS = {"70000", "B7S00"}


def _u8(value: Any, context: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 255:
        raise ValidationError(f"{context} must be an integer in 0..255")
    return value


def _payload(value: Any, context: str) -> bytes:
    if not isinstance(value, str):
        raise ValidationError(f"{context} must be hexadecimal text")
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise ValidationError(f"{context} must be hexadecimal text") from exc


def _expect_payload(entry: dict[str, Any], expected: bytes, context: str) -> None:
    payload = _payload(entry.get("request_payload_hex"), f"{context}.request_payload_hex")
    if payload != expected:
        raise ValidationError(f"{context}.request_payload_hex does not match operation and selector")


def _response_evidence(entry: dict[str, Any], operation: str, context: str) -> bytes | None:
    state = entry.get("response_state")
    attempts = entry.get("request_attempts")
    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 0:
        raise ValidationError(f"{context}.request_attempts must be a non-negative integer")
    raw_value = entry.get("response_raw_hex")
    raw = None if raw_value is None else _payload(raw_value, f"{context}.response_raw_hex")
    decoded = entry.get("decoded")
    expected_length = RESPONSE_LENGTHS[operation]

    if state == "unattempted":
        if attempts != 0 or raw is not None or decoded is not None:
            raise ValidationError(
                f"{context} unattempted evidence requires zero attempts and null raw/decoded values"
            )
        return None
    if attempts < 1:
        raise ValidationError(f"{context}.{state} requires at least one attempted exchange")
    if state == "value":
        if raw is None or len(raw) != expected_length:
            raise ValidationError(
                f"{context}.response_raw_hex must contain {expected_length} bytes for {operation} value"
            )
        return raw
    if decoded is not None:
        raise ValidationError(f"{context}.decoded must be null for response_state {state}")
    if state == "empty":
        if raw != b"":
            raise ValidationError(f"{context}.response_raw_hex must be empty for response_state empty")
        return raw
    if state == "malformed":
        if raw is None or not raw or len(raw) == expected_length:
            raise ValidationError(
                f"{context}.response_raw_hex must retain a nonempty wrong-length {operation} reply"
            )
        return raw
    if state in {"nack", "timeout", "transport_error"}:
        if raw is not None:
            raise ValidationError(f"{context}.response_raw_hex must be null for response_state {state}")
        return None
    raise ValidationError(f"{context}.response_state is unsupported")


def _exact_object(value: Any, fields: set[str], context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{context} must be an object")
    if set(value) != fields:
        raise ValidationError(f"{context} fields do not match the decoded contract")
    return value


def _exact_list(value: Any, length: int, context: str) -> list[Any]:
    if not isinstance(value, list) or len(value) != length:
        raise ValidationError(f"{context} must contain exactly {length} items")
    return value


def _decoded_raw_hex(decoded: dict[str, Any], raw: bytes, context: str) -> None:
    if _payload(decoded.get("raw_hex"), f"{context}.raw_hex") != raw:
        raise ValidationError(f"{context}.raw_hex must equal response_raw_hex")


def _timer_decoded(decoded_value: Any, raw: bytes, context: str) -> None:
    decoded = _exact_object(decoded_value, {"parameter_config", "slots", "raw_hex"}, context)
    if _u8(decoded["parameter_config"], f"{context}.parameter_config") != raw[0]:
        raise ValidationError(f"{context}.parameter_config does not match the first reply byte")
    slots = _exact_list(decoded["slots"], 3, f"{context}.slots")
    for index, (slot_value, start, stop) in enumerate(
        zip(slots, raw[1::2], raw[2::2], strict=True)
    ):
        slot_context = f"{context}.slots[{index}]"
        slot = _exact_object(
            slot_value,
            {"start_raw", "stop_raw", "start_minutes", "stop_minutes", "unused"},
            slot_context,
        )
        if _u8(slot["start_raw"], f"{slot_context}.start_raw") != start:
            raise ValidationError(f"{slot_context}.start_raw does not match response_raw_hex")
        if _u8(slot["stop_raw"], f"{slot_context}.stop_raw") != stop:
            raise ValidationError(f"{slot_context}.stop_raw does not match response_raw_hex")
        unused = start == stop == 0x90
        qualified = start < stop <= 0x90
        expected_start = start * 10 if qualified else None
        expected_stop = stop * 10 if qualified else None
        if slot["unused"] is not unused:
            raise ValidationError(f"{slot_context}.unused does not match the raw pair")
        if slot["start_minutes"] != expected_start or slot["stop_minutes"] != expected_stop:
            raise ValidationError(f"{slot_context} minutes do not match the raw pair")
    _decoded_raw_hex(decoded, raw, context)


def _vr91_decoded(decoded_value: Any, raw: bytes, context: str) -> None:
    fields = (
        "binding_zone",
        "special_function_status",
        "heating_operating_mode",
        "cooling_operating_mode",
        "status_info",
        "frost_protection",
        "heating_temperature_raw",
        "cooling_temperature_raw",
    )
    decoded = _exact_object(decoded_value, {*fields, "raw_hex"}, context)
    for field, expected in zip(fields, raw, strict=True):
        if _u8(decoded[field], f"{context}.{field}") != expected:
            raise ValidationError(f"{context}.{field} does not match response_raw_hex")
    _decoded_raw_hex(decoded, raw, context)


def _event_decoded(decoded_value: Any, raw: bytes, context: str) -> None:
    decoded = _exact_object(
        decoded_value, {"parameter_config", "start1_raw", "starts", "raw_hex"}, context
    )
    if _u8(decoded["parameter_config"], f"{context}.parameter_config") != raw[0]:
        raise ValidationError(f"{context}.parameter_config does not match response_raw_hex")
    if _u8(decoded["start1_raw"], f"{context}.start1_raw") != raw[1]:
        raise ValidationError(f"{context}.start1_raw does not match response_raw_hex")
    starts = _exact_list(decoded["starts"], 6, f"{context}.starts")
    for index, (value, expected_raw) in enumerate(zip(starts, raw[2:], strict=True)):
        item_context = f"{context}.starts[{index}]"
        item = _exact_object(value, {"raw", "minutes"}, item_context)
        if _u8(item["raw"], f"{item_context}.raw") != expected_raw:
            raise ValidationError(f"{item_context}.raw does not match response_raw_hex")
        expected_minutes = expected_raw * 10 if expected_raw <= 0x90 else None
        if item["minutes"] != expected_minutes:
            raise ValidationError(f"{item_context}.minutes does not match the raw byte")
    _decoded_raw_hex(decoded, raw, context)


def _event_setpoint_decoded(
    decoded_value: Any, raw: bytes, profile: str, context: str
) -> None:
    decoded = _exact_object(decoded_value, {"parameter_config", "values", "raw_hex"}, context)
    if _u8(decoded["parameter_config"], f"{context}.parameter_config") != raw[0]:
        raise ValidationError(f"{context}.parameter_config does not match response_raw_hex")
    values = _exact_list(decoded["values"], 7, f"{context}.values")
    states = {253: "enable", 254: "disable", 255: "replacement"}
    for index, (value, expected_raw) in enumerate(zip(values, raw[1:], strict=True)):
        item_context = f"{context}.values[{index}]"
        item = _exact_object(value, {"raw", "temperature_c", "state"}, item_context)
        if _u8(item["raw"], f"{item_context}.raw") != expected_raw:
            raise ValidationError(f"{item_context}.raw does not match response_raw_hex")
        expected_temperature = None if profile == "dhw" else expected_raw / 2.0
        expected_state = states.get(expected_raw) if profile == "dhw" else None
        if item["temperature_c"] != expected_temperature or item["state"] != expected_state:
            raise ValidationError(f"{item_context} interpretation does not match profile and raw byte")
    _decoded_raw_hex(decoded, raw, context)


def _known_decoded(entry: dict[str, Any], selector: dict[str, Any], raw: bytes, context: str) -> None:
    decoded_context = f"{context}.decoded"
    operation = entry["operation"]
    if operation == "ReadTimer":
        _timer_decoded(entry.get("decoded"), raw, decoded_context)
    elif operation == "ReadVR91":
        _vr91_decoded(entry.get("decoded"), raw, decoded_context)
    elif operation == "GetEvent":
        _event_decoded(entry.get("decoded"), raw, decoded_context)
    else:
        _event_setpoint_decoded(
            entry.get("decoded"), raw, str(selector.get("profile")), decoded_context
        )


def _known_timer(entry: dict[str, Any], selector: dict[str, Any], context: str) -> None:
    channel = selector.get("channel")
    if channel not in CHANNELS:
        raise ValidationError(f"{context}.selector.channel is unsupported")
    instance = _u8(selector.get("instance"), f"{context}.selector.instance")
    weekday = selector.get("weekday")
    if isinstance(weekday, bool) or not isinstance(weekday, int) or not 0 <= weekday <= 6:
        raise ValidationError(f"{context}.selector.weekday must be an integer in 0..6")
    group, fixed_instance, address = CHANNELS[channel]
    if fixed_instance is not None and instance != fixed_instance:
        raise ValidationError(f"{context}.selector.instance must be {fixed_instance} for {channel}")
    _expect_payload(entry, bytes((0x03, group, instance if fixed_instance is None else fixed_instance, address, weekday)), context)


def _known_event(entry: dict[str, Any], selector: dict[str, Any], context: str) -> None:
    profile = selector.get("profile")
    if profile not in PROFILES:
        raise ValidationError(f"{context}.selector.profile is unsupported")
    instance = _u8(selector.get("instance"), f"{context}.selector.instance")
    address = _u8(selector.get("address"), f"{context}.selector.address")
    weekday = _u8(selector.get("weekday_code"), f"{context}.selector.weekday_code")
    opcode = OPCODES[entry["operation"]]
    maximum_address = 3 if profile == "system" else 2
    if not 1 <= address <= maximum_address:
        raise ValidationError(f"{context}.selector.address is unsupported for {profile}")
    _expect_payload(entry, bytes((opcode, PROFILES[profile], instance, address, weekday)), context)
    if "pair_context" in entry and entry["pair_context"] != selector:
        raise ValidationError(f"{context}.pair_context must equal the canonical Event selector")
    if entry.get("decode_qualification") != "schema_unqualified":
        raise ValidationError(f"{context}.decode_qualification must be schema_unqualified for Events")


def _raw(entry: dict[str, Any], context: str) -> None:
    if entry.get("pair_context") is not None:
        raise ValidationError(f"{context}.pair_context is not allowed for raw-only selectors")
    if entry.get("decode_qualification") != "schema_unqualified":
        raise ValidationError(f"{context}.decode_qualification must be schema_unqualified for raw-only selectors")
    if entry.get("decoded") is not None:
        raise ValidationError(f"{context}.decoded must be null for raw-only selectors")
    raw = entry.get("raw_selector")
    if not isinstance(raw, dict):
        raise ValidationError(f"{context}.raw_selector is required for an empty selector")
    day_field = "weekday" if entry["operation"] == "ReadTimer" else "weekday_code"
    expected_fields = {"system_type", "instance", "address", day_field}
    if set(raw) != expected_fields:
        raise ValidationError(
            f"{context}.raw_selector must contain exactly system_type, instance, address, "
            f"and {day_field} for {entry['operation']}"
        )
    system_type = _u8(raw.get("system_type"), f"{context}.raw_selector.system_type")
    instance = _u8(raw.get("instance"), f"{context}.raw_selector.instance")
    address = _u8(raw.get("address"), f"{context}.raw_selector.address")
    day = _u8(raw.get(day_field), f"{context}.raw_selector.{day_field}")
    _expect_payload(entry, bytes((OPCODES[entry["operation"]], system_type, instance, address, day)), context)


def _validate_profile_qualified_target(artifact: dict[str, Any], path: Path) -> None:
    meta = artifact.get("meta")
    identity = meta.get("resolved_identity") if isinstance(meta, dict) else None
    if not isinstance(identity, dict):
        raise ValidationError(
            f"{path}: profile_vrc700 requires meta.resolved_identity from the target probe"
        )
    manufacturer = identity.get("manufacturer")
    device_id = identity.get("device_id")
    eid = identity.get("eid")
    if (
        manufacturer != "0xB5"
        or not isinstance(device_id, str)
        or not isinstance(eid, str)
        or device_id.strip().upper() != eid.strip().upper()
        or device_id.strip().upper() not in VRC700_DEVICE_IDS
    ):
        raise ValidationError(
            f"{path}: profile_vrc700 requires matching Vaillant VRC700 device_id and EID"
        )


def validate_artifact(path: Path) -> None:
    try:
        artifact = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path}: cannot read JSON") from exc
    records = artifact.get("b524_operation_reads") if isinstance(artifact, dict) else None
    if not isinstance(records, list):
        raise ValidationError(f"{path}: b524_operation_reads must be an array")
    if any(
        isinstance(entry, dict) and entry.get("decode_qualification") == "profile_vrc700"
        for entry in records
    ):
        _validate_profile_qualified_target(artifact, path)
    for index, entry in enumerate(records):
        context = f"{path}: b524_operation_reads[{index}]"
        if not isinstance(entry, dict):
            raise ValidationError(f"{context} must be an object")
        operation = entry.get("operation")
        if operation not in OPCODES:
            raise ValidationError(f"{context}.operation is unsupported")
        if entry.get("decode_qualification") == "profile_vrc700" and operation not in {
            "ReadTimer",
            "ReadVR91",
        }:
            raise ValidationError(
                f"{context}.decode_qualification profile_vrc700 is only for Timer and VR91"
            )
        if entry.get("opcode_hex") != f"0x{OPCODES[operation]:02X}":
            raise ValidationError(f"{context}.opcode_hex does not match operation")
        response = _response_evidence(entry, operation, context)
        selector = entry.get("selector")
        if not isinstance(selector, dict):
            raise ValidationError(f"{context}.selector must be an object")
        if operation == "ReadVR91":
            if selector or entry.get("raw_selector") is not None:
                raise ValidationError(f"{context} ReadVR91 has no selector")
            _expect_payload(entry, b"\x08", context)
            if entry.get("response_state") == "value":
                assert response is not None
                _known_decoded(entry, selector, response, context)
            continue
        if selector:
            if entry.get("raw_selector") is not None:
                raise ValidationError(f"{context}.raw_selector is only for empty selectors")
            if operation == "ReadTimer":
                _known_timer(entry, selector, context)
            else:
                _known_event(entry, selector, context)
            if entry.get("response_state") == "value":
                assert response is not None
                _known_decoded(entry, selector, response, context)
        else:
            _raw(entry, context)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifacts", nargs="+", type=Path)
    args = parser.parse_args()
    try:
        for artifact in args.artifacts:
            validate_artifact(artifact)
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
