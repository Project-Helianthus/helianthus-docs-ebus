#!/usr/bin/env python3
"""Validate the Vaillant controller qualification evidence-gap record."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


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
MATERIALIZED_ARTIFACT = {
    "path": "architecture/fixtures/evidence/vaillant-b555-timer-protocol-055738bb.md",
    "sha256": "2eff947174e4eb163b8e38f5eb93deb795491ec084e3e89ebc1dcdb7431e12ff",
}
MATERIALIZED_RELATIVE_TARGETS = [{
    "relative_path": "./ebus-vaillant-B524.md",
    "materialized_path": "architecture/fixtures/evidence/ebus-vaillant-B524.md",
    "repository": "Project-Helianthus/helianthus-docs-ebus",
    "revision": "055738bbad31f5cfe7fcd87bffc16bc09e021571",
    "source_path": "protocols/vaillant/ebus-vaillant-B524.md",
    "sha256": "f675d3555eedc28850e22ded753aad8c3e5e989132fb85eb3563f63cfdbec89c",
}]


class CheckError(ValueError):
    pass


def require(value: object, expected: object, label: str) -> None:
    if value != expected:
        raise CheckError(f"{label}: expected {expected!r}, got {value!r}")


def artifact_bytes() -> bytes:
    # This checked-in byte copy is materialized from ARTIFACT's exact pinned
    # repository revision and path. It remains available in shallow CI after
    # the moving source document changes in a later checkout.
    return Path(MATERIALIZED_ARTIFACT["path"]).read_bytes()


def validate_materialized_relative_links() -> None:
    snapshot = Path(MATERIALIZED_ARTIFACT["path"])
    links = re.findall(r"\]\((\./[^)#]+)(?:#[^)]+)?\)", artifact_bytes().decode("utf-8"))
    expected_paths = [target["relative_path"] for target in MATERIALIZED_RELATIVE_TARGETS]
    if not links or any(link not in expected_paths for link in links):
        raise CheckError("materialized snapshot relative links")
    for target in MATERIALIZED_RELATIVE_TARGETS:
        if target["relative_path"] not in links:
            raise CheckError("missing materialized relative target")
        resolved = (snapshot.parent / target["relative_path"]).resolve()
        expected = Path(target["materialized_path"]).resolve()
        if resolved != expected or not resolved.is_file():
            raise CheckError("materialized relative target path")
        if hashlib.sha256(resolved.read_bytes()).hexdigest() != target["sha256"]:
            raise CheckError("materialized relative target digest")


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
    require(value.get("context_artifact"), ARTIFACT, "context_artifact")
    require(value.get("materialized_artifact"), MATERIALIZED_ARTIFACT, "materialized_artifact")
    require(value.get("materialized_relative_targets"), MATERIALIZED_RELATIVE_TARGETS, "materialized_relative_targets")
    if hashlib.sha256(artifact_bytes()).hexdigest() != MATERIALIZED_ARTIFACT["sha256"]:
        raise CheckError("context artifact digest")
    validate_materialized_relative_links()
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
