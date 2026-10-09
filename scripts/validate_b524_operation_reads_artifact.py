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
    system_type = _u8(raw.get("system_type"), f"{context}.raw_selector.system_type")
    instance = _u8(raw.get("instance"), f"{context}.raw_selector.instance")
    address = _u8(raw.get("address"), f"{context}.raw_selector.address")
    if entry["operation"] == "ReadTimer":
        day = _u8(raw.get("weekday"), f"{context}.raw_selector.weekday")
    else:
        day = _u8(raw.get("weekday_code", raw.get("weekday")), f"{context}.raw_selector.weekday_code")
    _expect_payload(entry, bytes((OPCODES[entry["operation"]], system_type, instance, address, day)), context)


def validate_artifact(path: Path) -> None:
    try:
        artifact = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path}: cannot read JSON") from exc
    records = artifact.get("b524_operation_reads") if isinstance(artifact, dict) else None
    if not isinstance(records, list):
        raise ValidationError(f"{path}: b524_operation_reads must be an array")
    for index, entry in enumerate(records):
        context = f"{path}: b524_operation_reads[{index}]"
        if not isinstance(entry, dict):
            raise ValidationError(f"{context} must be an object")
        operation = entry.get("operation")
        if operation not in OPCODES:
            raise ValidationError(f"{context}.operation is unsupported")
        if entry.get("opcode_hex") != f"0x{OPCODES[operation]:02X}":
            raise ValidationError(f"{context}.opcode_hex does not match operation")
        selector = entry.get("selector")
        if not isinstance(selector, dict):
            raise ValidationError(f"{context}.selector must be an object")
        if operation == "ReadVR91":
            if selector or entry.get("raw_selector") is not None:
                raise ValidationError(f"{context} ReadVR91 has no selector")
            _expect_payload(entry, b"\x08", context)
            continue
        if selector:
            if entry.get("raw_selector") is not None:
                raise ValidationError(f"{context}.raw_selector is only for empty selectors")
            if operation == "ReadTimer":
                _known_timer(entry, selector, context)
            else:
                _known_event(entry, selector, context)
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
