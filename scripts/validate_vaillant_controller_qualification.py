#!/usr/bin/env python3
"""Validate the Vaillant controller qualification evidence-gap record."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


FIXTURE = Path("architecture/fixtures/vaillant-controller-qualification-v1.json")
THERMAL = Path("architecture/fixtures/vaillant-semreg-thermal-map-v1.json")
CONTEXT_RECEIPT = {
    "path": "architecture/fixtures/vaillant-controller-context-receipt-v1.json",
    "sha256": "45c49efa12526add9d6f1a975c37b9a159cf081b0925cca9476193c244d58f0a",
    "sha256_path": "architecture/fixtures/vaillant-controller-context-receipt-v1.sha256",
}
RECEIPT = {
    "schema_version": 1,
    "receipt_id": "helianthus.docs.ebus.vaillant-controller-context/v1",
    "conclusion": "Unknown",
    "receipt_status": "context_only_not_direct_identification",
    "direct_identification_evidence": None,
    "canonical_upstream": {
        "repository": "Project-Helianthus/helianthus-docs-ebus",
        "revision": "055738bbad31f5cfe7fcd87bffc16bc09e021571",
        "path": "protocols/vaillant/ebus-vaillant-b555-timer-protocol.md",
        "lines": "28-37",
        "blob_sha256": "2eff947174e4eb163b8e38f5eb93deb795491ec084e3e89ebc1dcdb7431e12ff",
        "canonical_url": "https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/055738bbad31f5cfe7fcd87bffc16bc09e021571/protocols/vaillant/ebus-vaillant-b555-timer-protocol.md",
        "canonical_url_status": "upstream metadata only; this receipt validator does not retrieve network or Git history",
    },
    "extracted_context": {"address": "0x15", "device_id": "BASV2", "software_version": "0507", "hardware_version": "1704"},
    "does_not_establish": ["direct 0x07/0x04 request", "direct 0x07/0x04 response", "raw manufacturer byte for this tuple", "registry qualification authority"],
}


class CheckError(ValueError):
    pass


def require(value: object, expected: object, label: str) -> None:
    if value != expected:
        raise CheckError(f"{label}: expected {expected!r}, got {value!r}")


def receipt_bytes() -> bytes:
    return Path(CONTEXT_RECEIPT["path"]).read_bytes()


def validate_context_receipt() -> None:
    received = receipt_bytes()
    if b"](" in received:
        raise CheckError("context receipt must not contain relative links")
    if hashlib.sha256(received).hexdigest() != CONTEXT_RECEIPT["sha256"]:
        raise CheckError("context receipt digest")
    sidecar = Path(CONTEXT_RECEIPT["sha256_path"]).read_text(encoding="utf-8")
    expected_sidecar = f"{CONTEXT_RECEIPT['sha256']}  {Path(CONTEXT_RECEIPT['path']).name}\n"
    if sidecar != expected_sidecar:
        raise CheckError("context receipt digest sidecar")
    require(json.loads(received), RECEIPT, "context receipt")


def validate_fixture(value: object, thermal: object) -> None:
    if not isinstance(value, dict) or not isinstance(thermal, dict):
        raise CheckError("fixtures must be objects")
    require(value.get("schema_version"), 1, "schema_version")
    require(value.get("contract_id"), "helianthus.docs.ebus.vaillant-controller-qualification/v1", "contract_id")
    require(value.get("revision"), "vaillant-controller-qualification-evidence-gap/v1", "revision")
    require(value.get("scope"), "native_read_only_qualification_evidence_gap", "scope")
    require(value.get("evidence_status"), "Unknown", "evidence_status")
    require(value.get("qualified_use_permitted"), False, "qualified_use_permitted")
    require(value.get("direct_identification_evidence"), None, "direct_identification_evidence")
    require(value.get("context_receipt"), CONTEXT_RECEIPT, "context_receipt")
    validate_context_receipt()
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
        "evidence_status": "Unknown",
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
