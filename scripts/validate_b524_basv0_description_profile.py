#!/usr/bin/env python3
"""Validate native B524 BASV0 description-profile evidence."""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any


class ValidationError(ValueError):
    """The fixture overstates or corrupts a B524 metadata observation."""


HEX = re.compile(r"^(?:[0-9A-F]{2})*$")


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _description_operation(operation: str) -> int:
    return {"02": 0x01, "06": 0x07}[operation]


def _decode_limit(codec: str, raw: str) -> Any:
    value = bytes.fromhex(raw)
    if codec == "UCH": return value[0]
    if codec == "UIN": return int.from_bytes(value, "little")
    if codec == "U32": return int.from_bytes(value, "little")
    if codec == "EXP": return struct.unpack("<f", value)[0]
    if codec == "HDA:3": return f"{2000 + value[2]:04d}-{value[1]:02d}-{value[0]:02d}"
    if codec == "HTI": return f"{value[0]:02d}:{value[1]:02d}:{value[2]:02d}"
    raise ValidationError(f"unsupported qualified codec {codec}")


def _validate_record(record: Any, index: int) -> None:
    context = f"records[{index}]"
    _require(isinstance(record, dict), f"{context} must be an object")
    selector = record.get("selector")
    _require(isinstance(selector, dict), f"{context}.selector must be an object")
    operation = selector.get("operation")
    group = selector.get("group")
    instance = selector.get("instance")
    register = selector.get("register")
    _require(operation in {"02", "06"}, f"{context}.selector.operation is unsupported")
    for name, value, length in (("group", group, 2), ("instance", instance, 2), ("register", register, 4)):
        _require(isinstance(value, str) and len(value) == length and HEX.fullmatch(value) is not None,
                 f"{context}.selector.{name} is not uppercase hexadecimal")
    _require(record.get("identity_scope") == ("local" if operation == "02" else "remote"),
             f"{context}.identity_scope does not match native operation")
    remote_identity = record.get("remote_identity")
    if operation == "02":
        _require(remote_identity is None, f"{context} must not attach remote identity to a local selector")
    else:
        _require(isinstance(remote_identity, dict) and remote_identity.get("qualification") in {"observed_remote_header", "unqualified"},
                 f"{context} must retain remote identity qualification")
        if "group" in remote_identity:
            _require(remote_identity["group"] == group, f"{context}.remote_identity.group disagrees with selector")
    raw = record.get("raw_description_hex")
    lengths = record.get("description_payload_length")
    limits = record.get("raw_limits")
    decoded = record.get("decoded")
    if raw is None:
        _require(lengths is None and limits is None and decoded is None,
                 f"{context} cannot decode or bound a missing description")
        _require(record.get("response_state") == "describe_unavailable", f"{context} missing description has wrong response state")
        return
    _require(isinstance(raw, str) and HEX.fullmatch(raw) is not None, f"{context}.raw_description_hex is invalid")
    response = bytes.fromhex(raw)
    _require(record.get("response_state") == "describe_matched", f"{context} retained description has wrong response state")
    _require(len(response) >= 3 and response[0] == int(group, 16)
             and response[1:3] == int(register, 16).to_bytes(2, "little"),
             f"{context}.raw_description_hex does not echo GG/RR")
    body = response[3:]
    _require(len(body) % 3 == 0, f"{context}.raw_description_hex has unequal limit spans")
    _require(lengths == len(body), f"{context}.description_payload_length does not match raw description")
    _require(isinstance(limits, dict), f"{context}.raw_limits is required with a description")
    width = len(body) // 3
    for offset, name in enumerate(("min_hex", "max_hex", "step_hex")):
        value = limits.get(name)
        _require(isinstance(value, str) and HEX.fullmatch(value) is not None and len(value) == width * 2,
                 f"{context}.raw_limits.{name} does not match description width")
        _require(value == body[offset * width:(offset + 1) * width].hex().upper(),
                 f"{context}.raw_limits.{name} does not match raw description")
    if decoded is not None:
        _require(isinstance(decoded, dict), f"{context}.decoded must be an object or null")
        provenance = decoded.get("codec_provenance")
        basis = decoded.get("codec_basis")
        qualification = decoded.get("qualification")
        _require(provenance in {"selector_qualified", "length_inferred"}, f"{context}.decoded.codec_provenance is invalid")
        _require(basis in {"public_exact_selector_schema", "public_local_constraint_codec", "payload_length_inferred"}, f"{context}.decoded.codec_basis is invalid")
        _require(qualification in {"qualified", "unqualified"}, f"{context}.decoded.qualification is invalid")
        _require(not (provenance == "length_inferred" and qualification == "qualified"),
                 f"{context} promotes a length-inferred codec")
        _require((provenance == "length_inferred") == (basis == "payload_length_inferred"),
                 f"{context}.decoded codec basis disagrees with provenance")
        if qualification == "qualified":
            codec = decoded.get("codec")
            for field in ("min", "max"):
                _require(decoded.get(field) == _decode_limit(codec, limits[f"{field}_hex"]),
                         f"{context}.decoded.{field} disagrees with raw limits")
            if codec in {"HDA:3", "HTI"}:
                _require(decoded.get("step") is None, f"{context}.decoded.step must remain unknown")
            else:
                _require(decoded.get("step") == _decode_limit(codec, limits["step_hex"]),
                         f"{context}.decoded.step disagrees with raw limits")
    if record.get("validation_scope") == "format_range_and_step":
        _require(decoded is not None and decoded.get("qualification") == "qualified"
                 and decoded.get("codec_provenance") == "selector_qualified",
                 f"{context} grants range validation without a qualified selector codec")


def validate_fixture(path: Path, observations: Path | None = None) -> None:
    try:
        fixture = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{path}: cannot read JSON") from exc
    _require(isinstance(fixture, dict), "fixture must be an object")
    _require(fixture.get("schema_version") == "b524-basv0-description-profile/v1", "unexpected schema version")
    _require(fixture.get("observation_id") == "basv0_sw0217_hw8803_api1", "unexpected observation identity")
    records = fixture.get("records")
    _require(isinstance(records, list) and records, "fixture must contain records")
    for index, record in enumerate(records):
        _validate_record(record, index)
    dhw = [record for record in records if record.get("selector") == {"operation": "02", "group": "00", "instance": "00", "register": "0001"}]
    _require(len(dhw) == 1, "fixture must retain exactly one local DHW bivalence record")
    _require(dhw[0].get("raw_limits", {}).get("max_hex") == "0000A041", "BASV0 DHW maximum must retain raw 20")
    solar = [record for record in records if record.get("selector") == {"operation": "02", "group": "04", "instance": "01", "register": "000B"}]
    _require(len(solar) == 1 and (solar[0].get("decoded") is None or solar[0]["decoded"].get("qualification") == "unqualified"),
             "solar II01 must not gain a qualified codec")
    for register in ("006C", "006D", "006F", "0070"):
        matches = [record for record in records if record.get("selector") == {"operation": "02", "group": "00", "instance": "00", "register": register}]
        _require(len(matches) == 1 and matches[0].get("decoded") is None, f"installer selector {register} must remain raw")
    ventilation = [record for record in records if record.get("selector") == {"operation": "02", "group": "09", "instance": "00", "register": "0001"}]
    _require(len(ventilation) == 1 and ventilation[0].get("observed_read_payload_width") == 2
             and ventilation[0].get("presence_state") == "unknown", "ventilation RR0001 must retain unknown two-byte evidence")
    if observations is not None:
        observed = json.loads(observations.read_text(encoding="utf-8"))
        _require(observed.get("observation_id") == fixture.get("observation_id"), "cross-fixture identity mismatch")
        _require(observed.get("description_catalog") == path.name, "cross-fixture catalog mismatch")
        for index, row in enumerate(observed.get("records", [])):
            selector = row.get("selector", {})
            _require(row.get("identity_scope") == ("local" if selector.get("operation") == "02" else "remote"), f"observation records[{index}] identity scope disagrees with selector")
            state = row.get("response_state")
            flags = row.get("access_flags")
            width = row.get("observed_payload_width")
            error = row.get("error_state")
            if state == "echo_payload":
                _require(isinstance(flags, str) and flags in {"00", "01", "02", "03"} and isinstance(width, int) and width > 0 and error in {None, "parse_error"},
                         f"observation records[{index}] echo_payload fields are inconsistent")
            elif state == "status_only":
                _require(flags == "00" and width is None and error is None,
                         f"observation records[{index}] status_only fields are inconsistent")
            elif state == "transport_error":
                _require(flags is None and width is None and error == "transport_error",
                         f"observation records[{index}] transport_error fields are inconsistent")
            else:
                raise ValidationError(f"observation records[{index}] response state is unsupported")
            reference = row.get("description")
            if reference is None:
                continue
            record_index = reference.get("record_index")
            _require(isinstance(record_index, int) and 0 <= record_index < len(records), f"observation records[{index}] description index out of bounds")
            _require(row.get("selector") == records[record_index].get("selector"), f"observation records[{index}] description selector mismatch")
            described = records[record_index]
            _require(row.get("access_flags") == described.get("access_flags"), f"observation records[{index}] access flags disagree with description")
            if reference.get("acquisition_state") == "unavailable":
                _require(described.get("raw_description_hex") is None and described.get("response_state") == "describe_unavailable", f"observation records[{index}] unavailable description has raw metadata")
            else:
                _require(described.get("raw_description_hex") is not None and described.get("response_state") == "describe_matched", f"observation records[{index}] available description lacks raw metadata")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--observations", type=Path)
    args = parser.parse_args()
    try:
        validate_fixture(args.fixture, args.observations)
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
