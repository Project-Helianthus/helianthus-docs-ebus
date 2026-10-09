#!/usr/bin/env python3
"""Validate selector-to-wire consistency in B524 bounded-survey profiles."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


class ValidationError(ValueError):
    """A profile has a selector, payload, or outcome inconsistency."""


FIXTURES = Path(__file__).resolve().parents[1] / "protocols" / "vaillant" / "fixtures"
OP02_SEMANTIC_CATALOG_SCOPE = (
    "static OP02 semantic names only; values and bounds remain profile-qualified"
)
OP02_SEMANTIC_CATALOG_FIELDS = ["opcode", "group", "register", "name"]


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
    _selector_byte(selector, "gg", "reply")
    _selector_register(selector, "reply")
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


def _catalog_path(path_value: str, profile_path: Path) -> Path:
    candidates = (profile_path.parent / path_value, FIXTURES / path_value)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise ValidationError(f"{profile_path}: catalog_reference.path does not identify a local file")


def _validate_op02_semantic_catalog(catalog_path: Path, profile_path: Path) -> None:
    context = f"{profile_path}: catalog_reference.path"
    if catalog_path.suffix.lower() != ".csv":
        raise ValidationError(f"{context} must identify an OP02 semantic catalog CSV")
    try:
        with catalog_path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            if reader.fieldnames != OP02_SEMANTIC_CATALOG_FIELDS:
                raise ValidationError(
                    f"{context} must use the opcode,group,register,name catalog columns"
                )
            rows = list(reader)
    except (OSError, csv.Error) as exc:
        raise ValidationError(f"{context} cannot be read as a semantic catalog CSV") from exc
    if not rows:
        raise ValidationError(f"{context} must contain at least one semantic catalog row")
    identities: set[tuple[int, int, int]] = set()
    for index, row in enumerate(rows, start=2):
        row_context = f"{context} row {index}"
        if None in row:
            raise ValidationError(f"{row_context} has fields outside the catalog columns")
        try:
            opcode_text = row["opcode"]
            group_text = row["group"]
            register_text = row["register"]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValidationError(f"{row_context} has invalid hexadecimal identity fields") from exc
        if (
            not all(isinstance(value, str) for value in (opcode_text, group_text, register_text))
            or re.fullmatch(r"0x[0-9A-Fa-f]{2}", opcode_text) is None
            or re.fullmatch(r"0x[0-9A-Fa-f]{2}", group_text) is None
            or re.fullmatch(r"0x[0-9A-Fa-f]{4}", register_text) is None
        ):
            raise ValidationError(f"{row_context} has invalid hexadecimal identity fields")
        opcode = int(opcode_text, 16)
        group = int(group_text, 16)
        register = int(register_text, 16)
        if opcode != 0x02 or not 0 <= group <= 0xFF or not 0 <= register <= 0xFFFF:
            raise ValidationError(f"{row_context} is outside the declared OP02 catalog scope")
        name = row.get("name")
        if not isinstance(name, str) or re.fullmatch(r"[a-z][a-z0-9_]*", name) is None:
            raise ValidationError(f"{row_context}.name must be a snake_case semantic name")
        identity = (opcode, group, register)
        if identity in identities:
            raise ValidationError(f"{row_context} duplicates an OP02 selector")
        identities.add(identity)


def _selector_identity(selector: dict[str, Any], context: str) -> tuple[int, int, int, int]:
    return (
        _selector_byte(selector, "op", context),
        _selector_byte(selector, "gg", context),
        _selector_byte(selector, "ii", context),
        int.from_bytes(_selector_register(selector, context), "little"),
    )


def _correlate_qualified_limit(
    limit: dict[str, Any], samples: Any, context: str
) -> None:
    if not isinstance(samples, list):
        raise ValidationError(f"{context} cannot be correlated without profile samples")
    selector = limit["selector"]
    identity = _selector_identity(selector, context)
    matches = [
        sample
        for sample in samples
        if isinstance(sample, dict)
        and sample.get("kind") == "op07_generic_description"
        and isinstance(sample.get("selector"), dict)
        and _selector_identity(sample["selector"], f"{context}.sample") == identity
    ]
    if len(matches) != 1:
        raise ValidationError(
            f"{context}.selector must identify exactly one OP07 generic-description sample"
        )
    sample = matches[0]
    if (
        sample.get("outcome") != "value_reply"
        or sample.get("qualification") != "generic_class_observation"
    ):
        raise ValidationError(f"{context} requires a qualified OP07 value-reply sample")
    reply = _hex(sample.get("reply_payload_hex"), f"{context}.sample.reply_payload_hex")
    if len(reply) != 6:
        raise ValidationError(f"{context}.sample reply must contain GG/RR and three limit bytes")
    if limit["codec"] != "BOOL":
        raise ValidationError(f"{context}.codec is not supported for qualified limit correlation")
    if limit["qualification"] != "generic_class_observation_not_concrete_identity":
        raise ValidationError(f"{context}.qualification does not match the retained sample boundary")
    observed_limits = tuple(bool(value) for value in reply[3:])
    declared_limits = (limit["min"], limit["max"], limit["step"])
    if any(value not in (0, 1) for value in reply[3:]) or declared_limits != observed_limits:
        raise ValidationError(f"{context} min/max/step do not match the retained BOOL reply")


def _validate_catalog_reference(profile: dict[str, Any], profile_path: Path) -> None:
    reference = profile.get("catalog_reference")
    if not isinstance(reference, dict):
        raise ValidationError(f"{profile_path}: catalog_reference must be an object")
    path_value = reference.get("path")
    if not isinstance(path_value, str) or not path_value:
        raise ValidationError(f"{profile_path}: catalog_reference.path must be nonempty text")
    reference_path = Path(path_value)
    if reference_path.is_absolute() or ".." in reference_path.parts:
        raise ValidationError(f"{profile_path}: catalog_reference.path must be a safe relative path")
    catalog_path = _catalog_path(path_value, profile_path)
    _validate_op02_semantic_catalog(catalog_path, profile_path)

    scope = reference.get("scope")
    if scope != OP02_SEMANTIC_CATALOG_SCOPE:
        raise ValidationError(
            f"{profile_path}: catalog_reference.scope does not match the supported OP02 catalog"
        )
    limits = reference.get("qualified_description_limits")
    if not isinstance(limits, list):
        raise ValidationError(
            f"{profile_path}: catalog_reference.qualified_description_limits must be an array"
        )
    required = {"selector", "semantic_name", "codec", "min", "max", "step", "qualification"}
    for index, limit in enumerate(limits):
        context = f"{profile_path}: catalog_reference.qualified_description_limits[{index}]"
        if not isinstance(limit, dict) or set(limit) != required:
            raise ValidationError(f"{context} fields do not match the qualified-limit contract")
        selector = limit.get("selector")
        if not isinstance(selector, dict) or set(selector) != {"op", "gg", "ii", "rr"}:
            raise ValidationError(f"{context}.selector must contain exactly OP/GG/II/RR")
        if _selector_byte(selector, "op", context) != 0x07:
            raise ValidationError(f"{context}.selector.op must be 07")
        _selector_byte(selector, "gg", context)
        if _selector_byte(selector, "ii", context) != 0xFF:
            raise ValidationError(f"{context}.selector.ii must be FF")
        _selector_register(selector, context)
        for field in ("semantic_name", "codec", "qualification"):
            if not isinstance(limit[field], str) or not limit[field]:
                raise ValidationError(f"{context}.{field} must be nonempty text")
        scalar_types = (bool, int, float, str)
        for field in ("min", "max", "step"):
            if not isinstance(limit[field], scalar_types):
                raise ValidationError(f"{context}.{field} must be a scalar value")
        if limit["codec"] == "BOOL" and not all(
            isinstance(limit[field], bool) for field in ("min", "max", "step")
        ):
            raise ValidationError(f"{context} BOOL limits must use boolean min/max/step")
        _correlate_qualified_limit(limit, profile.get("samples"), context)


def validate_profile(profile_path: Path) -> None:
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{profile_path}: cannot read JSON profile") from exc
    if not isinstance(profile, dict):
        raise ValidationError(f"{profile_path}: profile must be an object")
    _validate_catalog_reference(profile, profile_path)
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
        if kind in {"op02_read", "op06_read"} and outcome == "value_reply":
            expected_flags_class = {
                0x00: "read_only_hidden",
                0x01: "read_only_visible",
                0x02: "writable_hidden",
                0x03: "writable_visible",
            }.get(reply[0])
            if expected_flags_class is None or sample.get("flags_class") != expected_flags_class:
                raise ValidationError(
                    f"{context}.flags_class does not match reply_payload_hex byte 0"
                )
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
