#!/usr/bin/env python3
"""Validate selector-to-wire consistency in B524 bounded-survey profiles."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class ValidationError(ValueError):
    """A profile has a selector, payload, or outcome inconsistency."""


def _hex(value: Any, context: str) -> bytes:
    if not isinstance(value, str):
        raise ValidationError(f"{context} must be a hexadecimal string")
    try:
        return bytes.fromhex(value)
    except ValueError as exc:
        raise ValidationError(f"{context} is not valid hexadecimal") from exc


def _selector_byte(selector: dict[str, Any], key: str, context: str) -> int:
    value = selector.get(key)
    if not isinstance(value, str) or len(value) != 2:
        raise ValidationError(f"{context}.selector.{key} must be two hex digits")
    try:
        return int(value, 16)
    except ValueError as exc:
        raise ValidationError(f"{context}.selector.{key} is not hexadecimal") from exc


def _selector_register(selector: dict[str, Any], context: str) -> bytes:
    value = selector.get("rr")
    if not isinstance(value, str) or len(value) != 4:
        raise ValidationError(f"{context}.selector.rr must be four hex digits")
    try:
        return int(value, 16).to_bytes(2, "little")
    except ValueError as exc:
        raise ValidationError(f"{context}.selector.rr is not hexadecimal") from exc


def _expected_request(kind: str, selector: dict[str, Any], context: str) -> bytes:
    op = _selector_byte(selector, "op", context)
    gg = _selector_byte(selector, "gg", context)
    instance = _selector_byte(selector, "ii", context)
    register = _selector_register(selector, context)
    expected_op = {"op02_read": 0x02, "op06_read": 0x06, "op07_generic_description": 0x07}.get(kind)
    if expected_op is None:
        raise ValidationError(f"{context}.kind is unsupported")
    if op != expected_op:
        raise ValidationError(f"{context}.selector.op does not match {kind}")
    if kind in {"op02_read", "op06_read"}:
        return bytes((op, 0, gg, instance)) + register
    if kind == "op07_generic_description":
        return bytes((op, gg, instance)) + register
    raise AssertionError("unreachable")


def _reply_echo(kind: str, reply: bytes, selector: dict[str, Any]) -> bytes | None:
    gg = _selector_byte(selector, "gg", "reply")
    register = _selector_register(selector, "reply")
    if kind in {"op02_read", "op06_read"}:
        if len(reply) < 4:
            return None
        return reply[1:2] + reply[2:4]
    if kind == "op07_generic_description":
        if len(reply) < 3:
            return None
        return reply[:1] + reply[1:3]
    return None


def _expected_reply_echo(selector: dict[str, Any]) -> bytes:
    return bytes((_selector_byte(selector, "gg", "reply"),)) + _selector_register(selector, "reply")


def validate_profile(profile_path: Path) -> None:
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{profile_path}: cannot read JSON profile") from exc
    samples = profile.get("samples") if isinstance(profile, dict) else None
    if not isinstance(samples, list) or not samples:
        raise ValidationError(f"{profile_path}: samples must be a nonempty array")

    for index, sample in enumerate(samples):
        context = f"{profile_path}: samples[{index}]"
        if not isinstance(sample, dict):
            raise ValidationError(f"{context} must be an object")
        kind = sample.get("kind")
        selector = sample.get("selector")
        outcome = sample.get("outcome")
        if not isinstance(kind, str) or not isinstance(selector, dict) or not isinstance(outcome, str):
            raise ValidationError(f"{context} is missing kind, selector, or outcome")
        request = _hex(sample.get("request_payload_hex"), f"{context}.request_payload_hex")
        reply = _hex(sample.get("reply_payload_hex"), f"{context}.reply_payload_hex")
        expected_request = _expected_request(kind, selector, context)
        if request != expected_request:
            raise ValidationError(
                f"{context}.request_payload_hex does not match OP/GG/II/RR selector"
            )

        if outcome in {"empty_reply", "transport_error"}:
            if reply:
                raise ValidationError(
                    f"{context}.reply_payload_hex must be empty for {outcome}"
                )
            continue

        if outcome == "value_reply" and not reply:
            raise ValidationError(f"{context}.value_reply requires a reply payload")
        observed_echo = _reply_echo(kind, reply, selector)
        if observed_echo is not None and observed_echo != _expected_reply_echo(selector):
            raise ValidationError(
                f"{context}.reply_payload_hex echo does not match GG/RR selector"
            )
        if outcome == "value_reply" and observed_echo is None:
            raise ValidationError(
                f"{context}.value_reply is too short for its applicable GG/RR reply echo"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profiles", nargs="+", type=Path)
    args = parser.parse_args()
    try:
        for profile_path in args.profiles:
            validate_profile(profile_path)
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
