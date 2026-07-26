#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
from typing import Any


MANIFEST_PATH = pathlib.Path(
    "docs/platform/manifests/modbus-foundation-profile-contract-v1.json"
)
EXPECTED_TOP_LEVEL = {
    "artifacts",
    "companion_for",
    "consumer_pin",
    "contract_id",
    "execution",
    "licenses",
    "phase1_operations",
    "read_only",
    "repository",
    "schema",
    "source_policy",
    "transport_recovery_rows",
    "version",
}
EXPECTED_OPERATIONS = [
    "fc03_read_holding_registers",
    "fc04_read_input_registers",
    "fc2b_mei0e_read_device_identification",
]
EXPECTED_COMPANIONS = [
    "FMV3-M1-01",
    "FMV3-M1-02",
    "FMV3-M1-03",
    "FMV3-M1-04",
    "FMV3-M2-01",
    "FMV3-M2-02",
    "FMV3-M2-03",
]
EXPECTED_RECOVERY_ROWS = [
    "tcp_provable_zero_no_abandonment",
    "tcp_partial_write_close_reconnect",
    "tcp_indeterminate_error_close_reconnect",
    "tcp_cancellation_race_close_reconnect",
    "tcp_ambiguous_completion_close_reconnect",
    "tcp_full_transmit_timeout_tombstone",
    "tcp_full_transmit_cancellation_tombstone",
    "tcp_same_socket_tombstone_reuse_rejected",
    "tcp_tombstone_exhaustion_controlled_rollover",
    "tcp_old_generation_late_frame_rejected",
    "rtu_provable_zero_no_abandonment",
    "rtu_partial_write_quarantine",
    "rtu_indeterminate_error_quarantine",
    "rtu_cancellation_race_quarantine",
    "rtu_ambiguous_completion_quarantine",
    "rtu_full_transmit_timeout_quarantine",
    "rtu_full_transmit_cancellation_quarantine",
    "rtu_late_same_shape_discarded",
    "rtu_quiescence_failure_endpoint_recovery",
]
EXPECTED_CONSUMER_PIN = {
    "manifest_sha256": {
        "format": "lowercase_64_hex",
        "required": True,
    },
    "merged_commit_sha": {
        "format": "full_lowercase_40_hex",
        "required": True,
    },
    "repository": "Project-Helianthus/helianthus-docs-ebus",
    "validation": "exact",
}
OFFICIAL_SOURCE_URLS = (
    "https://www.modbus.org/file/secure/modbusprotocolspecification.pdf",
    "https://www.modbus.org/file/secure/messagingimplementationguide.pdf",
    "https://www.modbus.org/file/secure/modbusoverserial.pdf",
)
AGPL_WIRE_MARKERS = (
    "0xA001",
    "quantity_registers",
    "transaction_id  2 bytes",
    "A Modbus TCP ADU is at most",
    "An RTU ADU is at most",
    "VendorName",
    "ProductCode",
    "MajorMinorRevision",
)
POLICY_REQUIRED_TERMS = (
    "RTU_PHYSICAL_QUALIFICATION_V1",
    "wire_response_id",
    "logical_view_id",
    "late_after_abandonment",
    "virtual monotonic clock",
    "(authorization_scope, unit_id)",
    "protocols/modbus/modbus-phase-one-wire-v1.md",
)


def _read_json(path: pathlib.Path, errors: list[str]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"manifest unreadable: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append("manifest root must be an object")
        return {}
    return value


def _artifact(
    root: pathlib.Path,
    raw_path: object,
    prefix: str,
    label: str,
    errors: list[str],
) -> pathlib.Path | None:
    if not isinstance(raw_path, str):
        errors.append(f"artifacts.{label} must be a string")
        return None
    relative = pathlib.PurePosixPath(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        errors.append(f"artifacts.{label} is not a safe relative path")
        return None
    if not raw_path.startswith(prefix):
        errors.append(f"artifacts.{label} must be under {prefix}")
        return None
    path = root / pathlib.Path(*relative.parts)
    if not path.is_file():
        errors.append(f"artifacts.{label} does not exist: {raw_path}")
        return None
    if path.is_symlink() or not path.resolve().is_relative_to(root):
        errors.append(f"artifacts.{label} must be a regular in-repo file")
        return None
    return path


def _require_equal(
    manifest: dict[str, Any],
    key: str,
    expected: object,
    errors: list[str],
) -> None:
    actual_json = json.dumps(
        manifest.get(key), sort_keys=True, separators=(",", ":")
    )
    expected_json = json.dumps(
        expected, sort_keys=True, separators=(",", ":")
    )
    if actual_json != expected_json:
        errors.append(f"{key} must equal the canonical value")


def validate(root: pathlib.Path) -> tuple[list[str], str | None]:
    errors: list[str] = []
    manifest_file = root / MANIFEST_PATH
    manifest = _read_json(manifest_file, errors)
    if not manifest:
        return errors, None

    if set(manifest) != EXPECTED_TOP_LEVEL:
        errors.append("manifest top-level keys must match the closed schema")
    _require_equal(
        manifest,
        "schema",
        "helianthus.modbus.foundation-profile-companion",
        errors,
    )
    _require_equal(manifest, "version", 1, errors)
    _require_equal(
        manifest,
        "contract_id",
        "HELIANTHUS_MODBUS_FOUNDATION_PROFILE_V1",
        errors,
    )
    _require_equal(
        manifest,
        "repository",
        "Project-Helianthus/helianthus-docs-ebus",
        errors,
    )
    _require_equal(manifest, "read_only", True, errors)
    _require_equal(manifest, "phase1_operations", EXPECTED_OPERATIONS, errors)
    _require_equal(manifest, "companion_for", EXPECTED_COMPANIONS, errors)
    _require_equal(
        manifest,
        "transport_recovery_rows",
        EXPECTED_RECOVERY_ROWS,
        errors,
    )
    _require_equal(manifest, "consumer_pin", EXPECTED_CONSUMER_PIN, errors)
    _require_equal(
        manifest,
        "licenses",
        {"policy": "AGPL-3.0", "wire": "CC0-1.0"},
        errors,
    )
    _require_equal(
        manifest,
        "source_policy",
        {
            "restricted_source_copy": "forbidden",
            "upstream_specification_mode": "link_and_independent_summary",
        },
        errors,
    )
    _require_equal(
        manifest,
        "execution",
        {
            "authorization_anchor": (
                "0576544bd8851c4e32da3ca7c401270eee43ef5c"
            ),
            "hard_stop_before": "FMV3-M4-01",
            "meta_issue": (
                "Project-Helianthus/helianthus-execution-plans#71"
            ),
            "plan_issue": "FMV3-M1-00",
        },
        errors,
    )

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != {"policy", "wire"}:
        errors.append("artifacts must contain exactly policy and wire")
        policy_path = None
        wire_path = None
    else:
        policy_path = _artifact(
            root,
            artifacts["policy"],
            "docs/platform/",
            "policy",
            errors,
        )
        wire_path = _artifact(
            root,
            artifacts["wire"],
            "protocols/modbus/",
            "wire",
            errors,
        )

    policy_text = (
        policy_path.read_text(encoding="utf-8") if policy_path else ""
    )
    wire_text = wire_path.read_text(encoding="utf-8") if wire_path else ""

    for term in POLICY_REQUIRED_TERMS:
        if term not in policy_text:
            errors.append(f"policy missing required term: {term}")
    for issue in EXPECTED_COMPANIONS:
        if issue not in policy_text:
            errors.append(f"policy missing companion issue: {issue}")
    for row in EXPECTED_RECOVERY_ROWS:
        if f"`{row}`" not in policy_text:
            errors.append(f"policy missing recovery row: {row}")
    for marker in AGPL_WIRE_MARKERS:
        if marker in policy_text:
            errors.append(f"neutral wire fact leaked into AGPL policy: {marker}")
    for url in OFFICIAL_SOURCE_URLS:
        if url in policy_text:
            errors.append("official wire source URL leaked into AGPL policy")
        if url not in wire_text:
            errors.append(f"wire reference missing official source: {url}")

    if "protocols/LICENSE" not in wire_text or "CC0-1.0" not in wire_text:
        errors.append("wire reference must declare protocols/LICENSE CC0-1.0")
    try:
        protocol_license = (root / "protocols/LICENSE").read_text(
            encoding="utf-8"
        )
    except OSError as exc:
        errors.append(f"protocols/LICENSE unreadable: {exc}")
    else:
        if "Creative Commons CC0 1.0 Universal" not in protocol_license:
            errors.append("protocols/LICENSE is not the expected CC0 license")

    try:
        readme = (root / "README.md").read_text(encoding="utf-8")
    except OSError as exc:
        errors.append(f"README.md unreadable: {exc}")
    else:
        if (
            "[`protocols/`](protocols/)" not in readme
            or "**CC0-1.0**" not in readme
            or "Everything else" not in readme
            or "**AGPL-3.0**" not in readme
        ):
            errors.append("README license-path boundary is incomplete")

    digest = hashlib.sha256(manifest_file.read_bytes()).hexdigest()
    return errors, digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path("."))
    args = parser.parse_args()
    errors, digest = validate(args.root.resolve())
    if errors:
        for error in errors:
            print(
                f"modbus_companion_contract_invalid: {error}",
                file=sys.stderr,
            )
        return 1
    print(
        "modbus_companion_contract_ok "
        f"manifest_sha256={digest}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
