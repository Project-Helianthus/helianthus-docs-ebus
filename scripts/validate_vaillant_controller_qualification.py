#!/usr/bin/env python3
"""Validate the Vaillant controller qualification evidence-gap record."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


FIXTURE = Path("architecture/fixtures/vaillant-controller-qualification-v1.json")
THERMAL = Path("architecture/fixtures/vaillant-semreg-thermal-map-v1.json")
ARTIFACT = {
    "repository": "Project-Helianthus/helianthus-docs-ebus",
    "revision": "055738bbad31f5cfe7fcd87bffc16bc09e021571",
    "path": "protocols/vaillant/ebus-vaillant-b555-timer-protocol.md",
    "canonical_url": "https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/055738bbad31f5cfe7fcd87bffc16bc09e021571/protocols/vaillant/ebus-vaillant-b555-timer-protocol.md",
    "sha256": "2eff947174e4eb163b8e38f5eb93deb795491ec084e3e89ebc1dcdb7431e12ff",
    "establishes": ["BASV2 validation-environment summary", "address 0x15", "software 0507", "hardware 1704"],
    "does_not_establish": ["direct 0x07/0x04 request", "direct 0x07/0x04 response", "raw manufacturer byte for this tuple", "registry qualification authority"],
}


class CheckError(ValueError):
    pass


def require(value: object, expected: object, label: str) -> None:
    if value != expected:
        raise CheckError(f"{label}: expected {expected!r}, got {value!r}")


def artifact_bytes() -> bytes:
    # The artifact is selected by the fixture's exact path after the fixture
    # has been compared to ARTIFACT in full. The expected digest is fixed
    # independently, so a changed checkout file cannot be accepted by merely
    # updating a fixture field. Reading the checked-out path also works in the
    # shallow PR checkout where the pinned historical tree is unavailable.
    return Path(ARTIFACT["path"]).read_bytes()


def validate_fixture(value: object, thermal: object) -> None:
    if not isinstance(value, dict) or not isinstance(thermal, dict):
        raise CheckError("fixtures must be objects")
    require(value.get("schema_version"), 1, "schema_version")
    require(value.get("contract_id"), "helianthus.docs.ebus.vaillant-controller-qualification/v1", "contract_id")
    require(value.get("revision"), "vaillant-controller-qualification-evidence-gap/v1", "revision")
    require(value.get("scope"), "native_read_only_qualification_evidence_gap", "scope")
    require(value.get("evidence_status"), "unproven", "evidence_status")
    require(value.get("qualified_use_permitted"), False, "qualified_use_permitted")
    require(value.get("direct_identification_evidence"), None, "direct_identification_evidence")
    require(value.get("context_artifact"), ARTIFACT, "context_artifact")
    if hashlib.sha256(artifact_bytes()).hexdigest() != ARTIFACT["sha256"]:
        raise CheckError("context artifact digest")
    require(value.get("required_for_future_qualification"), {
        "direct_identification": {"primary": "0x07", "secondary": "0x04"},
        "same_exact_address_request_and_response": True,
        "raw_members": ["manufacturer", "device_id", "software_version", "hardware_version"],
        "complete_current_identity_witness": ["manufacturer", "device_id", "serial_number"],
        "immutable_public_artifact_reference_and_digest": True,
    }, "required_for_future_qualification")
    require(value.get("transition_contract"), {
        "malformed_or_incomplete_input": "reject_without_mutation",
        "valid_direct_conflicting_observation": "retire_current_qualification_atomically",
        "sparse_matching_refresh": "may_retain_existing_direct_proof",
    }, "transition_contract")
    require(value.get("thermal_mapping"), {
        "contract_id": "helianthus.docs.ebus.b524-semreg-thermal/v1",
        "fixture": "architecture/fixtures/vaillant-semreg-thermal-map-v1.json",
        "qualified_binding_required": True,
    }, "thermal_mapping")
    require(thermal.get("qualification"), {
        "contract_id": value["contract_id"],
        "revision": value["revision"],
        "fixture": "architecture/fixtures/vaillant-controller-qualification-v1.json",
        "evidence_status": "unproven",
        "qualified_binding_required": True,
        "runtime_qualification_permitted": False,
    }, "thermal qualification binding")
    require(value.get("nonclaims"), {
        "controller_or_firmware_tuple_qualified": False,
        "controller_family_range_qualified": False,
        "write_or_operation_authority": False,
        "live_or_physical_qualification": False,
    }, "nonclaims")


def main() -> int:
    try:
        validate_fixture(json.loads(FIXTURE.read_text()), json.loads(THERMAL.read_text()))
    except (OSError, json.JSONDecodeError, CheckError) as error:
        print(f"Vaillant controller qualification evidence-gap failed: {error}")
        return 1
    print("Vaillant controller qualification evidence-gap passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
