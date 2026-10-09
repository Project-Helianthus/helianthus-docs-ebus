#!/usr/bin/env python3
"""Validate native selector correlation in the public OP06 observed-window fixture."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


class ValidationError(ValueError):
    """An observed-window sample is not correlated to its native selector."""


def _hex_bytes(value: Any, context: str) -> bytes:
    if not isinstance(value, str) or re.fullmatch(r"(?:[0-9A-Fa-f]{2})+", value) is None:
        raise ValidationError(f"{context} must be nonempty compact hexadecimal bytes")
    return bytes.fromhex(value)


def _selector_int(value: Any, *, width: int, context: str) -> int:
    if not isinstance(value, str) or re.fullmatch(rf"0x[0-9A-Fa-f]{{{width}}}", value) is None:
        raise ValidationError(f"{context} must be 0x-prefixed {width}-digit hexadecimal")
    return int(value, 16)


def _selector(value: Any, context: str) -> tuple[int, int, int, int]:
    if not isinstance(value, dict) or set(value) != {"op", "gg", "ii", "rr"}:
        raise ValidationError(f"{context} must contain exactly op, gg, ii, and rr")
    return (
        _selector_int(value["op"], width=2, context=f"{context}.op"),
        _selector_int(value["gg"], width=2, context=f"{context}.gg"),
        _selector_int(value["ii"], width=2, context=f"{context}.ii"),
        _selector_int(value["rr"], width=4, context=f"{context}.rr"),
    )


def _validate_sample(sample: Any, context: str) -> tuple[int, int]:
    if not isinstance(sample, dict):
        raise ValidationError(f"{context} must be an object")
    kind = sample.get("kind")
    operation, group, instance, register = _selector(sample.get("selector"), f"{context}.selector")
    request = _hex_bytes(sample.get("request_payload_hex"), f"{context}.request_payload_hex")
    reply = _hex_bytes(sample.get("reply_payload_hex"), f"{context}.reply_payload_hex")
    rr = register.to_bytes(2, "little")

    if kind in {"generic_description", "generic_description_raw"}:
        if operation != 0x07 or instance != 0xFF:
            raise ValidationError(f"{context}.selector must identify OP07/IIFF")
        if request != bytes((0x07, group, 0xFF)) + rr:
            raise ValidationError(f"{context}.request_payload_hex does not match OP/GG/II/RR")
        if len(reply) < 3 or reply[:3] != bytes((group,)) + rr:
            raise ValidationError(f"{context}.reply_payload_hex does not echo GG/RR")
        if kind == "generic_description":
            if (
                sample.get("qualification") != "generic_class_observation"
                or sample.get("device_identity_verified") is not False
            ):
                raise ValidationError(f"{context} overstates generic description qualification")
            decoded = sample.get("decoded")
            if not isinstance(decoded, dict) or set(decoded) != {"type", "min", "max", "step"}:
                raise ValidationError(f"{context}.decoded does not match the description contract")
            if decoded["type"] != "BOOL" or len(reply) != 6:
                raise ValidationError(f"{context}.decoded BOOL requires three retained limit bytes")
            raw_limits = reply[3:]
            expected = (decoded["min"], decoded["max"], decoded["step"])
            if any(value not in (0, 1) for value in raw_limits) or tuple(
                bool(value) for value in raw_limits
            ) != expected:
                raise ValidationError(f"{context}.decoded limits do not match reply_payload_hex")
        elif sample.get("qualification") != "unqualified" or "decoded" in sample:
            raise ValidationError(f"{context} raw description must remain unqualified and undecoded")
        return group, register

    if kind == "concrete_read":
        if operation != 0x06:
            raise ValidationError(f"{context}.selector must identify OP06")
        if request != bytes((0x06, 0x00, group, instance)) + rr:
            raise ValidationError(f"{context}.request_payload_hex does not match OP/GG/II/RR")
        if len(reply) < 4 or reply[1:4] != bytes((group,)) + rr:
            raise ValidationError(f"{context}.reply_payload_hex does not echo GG/RR")
        flags = _selector_int(sample.get("flags"), width=2, context=f"{context}.flags")
        classification = {
            0x00: "read_only_not_visible",
            0x01: "read_only_visible",
        }.get(flags)
        if (
            classification is None
            or reply[0] != flags
            or sample.get("response_state") != "active"
            or sample.get("classification") != classification
        ):
            raise ValidationError(f"{context} flags and classification do not match the reply")
        return group, register

    raise ValidationError(f"{context}.kind is unsupported")


def validate_fixture(path: Path) -> None:
    try:
        fixture = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path}: cannot read JSON fixture") from exc
    if not isinstance(fixture, dict):
        raise ValidationError(f"{path}: fixture must be an object")
    if fixture.get("schema_version") != "b524-op06-observed-windows/v1":
        raise ValidationError(f"{path}: schema_version is unsupported")
    samples = fixture.get("samples")
    if not isinstance(samples, list) or not samples:
        raise ValidationError(f"{path}: samples must be a nonempty array")
    observed = {
        _validate_sample(sample, f"{path}: samples[{index}]")
        for index, sample in enumerate(samples)
    }
    windows = fixture.get("observed_scheduling_windows")
    if not isinstance(windows, list) or not windows:
        raise ValidationError(f"{path}: observed_scheduling_windows must be a nonempty array")
    for index, window in enumerate(windows):
        context = f"{path}: observed_scheduling_windows[{index}]"
        if not isinstance(window, dict):
            raise ValidationError(f"{context} must be an object")
        groups = window.get("groups")
        if not isinstance(groups, list) or not groups:
            raise ValidationError(f"{context}.groups must be a nonempty array")
        register_value = window.get("rr_through")
        if register_value is None:
            continue
        register = _selector_int(register_value, width=4, context=f"{context}.rr_through")
        for group_value in groups:
            group = _selector_int(group_value, width=2, context=f"{context}.groups")
            if (group, register) not in observed:
                raise ValidationError(f"{context} lacks a correlated ceiling sample for {group_value}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixtures", nargs="+", type=Path)
    args = parser.parse_args()
    try:
        for fixture in args.fixtures:
            validate_fixture(fixture)
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
