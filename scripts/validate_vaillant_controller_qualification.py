#!/usr/bin/env python3
"""Validate the exact Vaillant controller qualification fixture."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path


FIXTURE = Path("architecture/fixtures/vaillant-controller-qualification-v1.json")
THERMAL = Path("architecture/fixtures/vaillant-semreg-thermal-map-v1.json")
OBSERVATION = Path("protocols/vaillant/ebus-vaillant-b555-timer-protocol.md")


class CheckError(ValueError):
    pass


EXPECTED_DIRECT = {
    "service": {"primary": "0x07", "secondary": "0x04"},
    "target_address": "0x15",
    "manufacturer_wire_byte": "0xB5",
    "manufacturer_normalized": "VAILLANT",
    "device_id": "BASV2",
    "software_version": "0507",
    "hardware_version": "1704",
    "normalization": "trim_ascii_padding_then_uppercase",
}


def require(value: object, expected: object, label: str) -> None:
    if value != expected:
        raise CheckError(f"{label}: expected {expected!r}, got {value!r}")


def validate_fixture(value: object, thermal: object) -> None:
    if not isinstance(value, dict) or not isinstance(thermal, dict):
        raise CheckError("fixtures must be objects")
    require(value.get("schema_version"), 1, "schema_version")
    require(value.get("contract_id"), "helianthus.docs.ebus.vaillant-controller-qualification/v1", "contract_id")
    require(value.get("rule_revision"), "vaillant-controller-qualification/v1", "rule_revision")
    require(value.get("scope"), "native_read_only_current_use_qualification", "scope")
    require(value.get("direct_identification"), EXPECTED_DIRECT, "direct_identification")
    require(value.get("required_current_authority"), {
        "complete_identity_witness": ["manufacturer", "device_id", "serial_number"],
        "direct_observation_only": True,
        "no_last_known_good_composite": True,
        "reject": ["missing", "sentinel", "malformed", "unsupported", "conflicting"],
    }, "required_current_authority")
    evidence = value.get("native_evidence")
    if not isinstance(evidence, dict) or evidence.get("kind") != "protocol.observation":
        raise CheckError("native_evidence kind")
    reference = evidence.get("reference")
    digest = evidence.get("sha256")
    if not isinstance(reference, str) or "/blob/055738bbad31f5cfe7fcd87bffc16bc09e021571/" not in reference:
        raise CheckError("native_evidence reference must pin the observed source revision")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise CheckError("native_evidence sha256")
    if digest != hashlib.sha256(OBSERVATION.read_bytes()).hexdigest():
        raise CheckError("native_evidence sha256 does not match the observed source")
    require(value.get("thermal_mapping"), {
        "contract_id": "helianthus.docs.ebus.b524-semreg-thermal/v1",
        "fixture": "architecture/fixtures/vaillant-semreg-thermal-map-v1.json",
        "qualified_binding_required": True,
    }, "thermal_mapping")
    require(thermal.get("qualification"), {
        "contract_id": value["contract_id"],
        "rule_revision": value["rule_revision"],
        "fixture": "architecture/fixtures/vaillant-controller-qualification-v1.json",
        "qualified_binding_required": True,
    }, "thermal qualification binding")
    require(value.get("lifecycle"), {
        "retire_on": ["identity_replacement", "address_split", "conflicting_observation", "proof_retirement", "product_or_version_change"],
        "sparse_matching_refresh_retains_direct_proof": True,
    }, "lifecycle")
    require(value.get("nonclaims"), {
        "controller_family_range_qualified": False,
        "other_product_qualified": False,
        "other_software_or_hardware_qualified": False,
        "write_or_operation_authority": False,
        "live_or_physical_qualification": False,
    }, "nonclaims")


def main() -> int:
    try:
        validate_fixture(json.loads(FIXTURE.read_text()), json.loads(THERMAL.read_text()))
    except (OSError, json.JSONDecodeError, CheckError) as error:
        print(f"Vaillant controller qualification failed: {error}")
        return 1
    print("Vaillant controller qualification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
