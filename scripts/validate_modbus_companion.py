#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any


MANIFEST_PATH = pathlib.Path(
    "docs/platform/manifests/modbus-foundation-profile-contract-v1.json"
)
CONSUMER_LOCK_SCHEMA_PATH = pathlib.Path(
    "docs/platform/schemas/modbus-companion-consumer-lock-v1.schema.json"
)
CANONICAL_REPOSITORY_URL = (
    "https://github.com/Project-Helianthus/helianthus-docs-ebus.git"
)
CANONICAL_MAIN_REF = "refs/helianthus-validation/canonical-main"
GIT_EXECUTABLE = shutil.which("git", path=os.defpath)
EXPECTED_TOP_LEVEL = {
    "artifact_sha256",
    "artifacts",
    "companion_for",
    "consumer_pin",
    "content_revision",
    "contract_id",
    "execution",
    "licenses",
    "phase1_operations",
    "read_only",
    "repository",
    "schema",
    "source_policy",
    "trust_anchor",
    "transport_recovery_rows",
    "version",
}
EXPECTED_STATIC_ARTIFACT_SHA256 = {
    "consumer_lock_schema": (
        "369a724954d21614d71fd970c8b6224d8c892af8870819cbef159619acce4ad0"
    ),
    "policy": (
        "1a53f203eed42766ac2d91580c41f72674b5eaea374a1cf4fff650396f06b196"
    ),
    "wire": (
        "b941a60b39409c570f904f8e6830787203f8041c2fee462164c4c50c7a8f4444"
    ),
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
    "contract_id": "HELIANTHUS_MODBUS_FOUNDATION_PROFILE_V1",
    "contract_version": 1,
    "content_revision": 1,
    "lock_schema": CONSUMER_LOCK_SCHEMA_PATH.as_posix(),
    "manifest_sha256": {
        "format": "lowercase_64_hex",
        "required": True,
    },
    "merged_commit_sha": {
        "format": "full_lowercase_40_hex",
        "required": True,
    },
    "repository": "Project-Helianthus/helianthus-docs-ebus",
    "validation": {
        "canonical_main": "fresh_https_fetch_required_ancestor",
        "docs_checkout": "fully_clean_exact_head",
        "docs_commit_sha": "exact_match",
        "manifest_bytes": "sha256_exact",
        "validator": "scripts/validate_modbus_companion.py",
    },
}
CONSUMER_LOCK_KEYS = {
    "schema",
    "schema_version",
    "repository",
    "merged_commit_sha",
    "contract_id",
    "contract_version",
    "content_revision",
    "manifest_sha256",
}
EXPECTED_CONSUMER_LOCK_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": (
        "https://docs.helianthus.local/schemas/"
        "modbus-companion-consumer-lock-v1.schema.json"
    ),
    "title": "Helianthus Modbus Companion Consumer Lock V1",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "schema",
        "schema_version",
        "repository",
        "merged_commit_sha",
        "contract_id",
        "contract_version",
        "content_revision",
        "manifest_sha256",
    ],
    "properties": {
        "schema": {
            "const": "helianthus.modbus.companion-consumer-lock",
        },
        "schema_version": {"const": 1},
        "repository": {
            "const": "Project-Helianthus/helianthus-docs-ebus",
        },
        "merged_commit_sha": {
            "type": "string",
            "pattern": "^[0-9a-f]{40}$",
        },
        "contract_id": {
            "const": "HELIANTHUS_MODBUS_FOUNDATION_PROFILE_V1",
        },
        "contract_version": {"const": 1},
        "content_revision": {
            "type": "integer",
            "minimum": 1,
        },
        "manifest_sha256": {
            "type": "string",
            "pattern": "^[0-9a-f]{64}$",
        },
    },
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
    "max_active_admission_keys",
    "protected_slots_per_key",
    "shared_burst_slots",
    "another key still activates, admits its protected request",
    "schemas/modbus-companion-consumer-lock-v1.schema.json",
    "fresh bare",
    "trust_anchor.commit_sha",
    "runtime-gates/fronius-modbus-m1-admission.json",
    "protocols/modbus/modbus-phase-one-wire-v1.md",
)


def _read_json(
    path: pathlib.Path,
    errors: list[str],
    label: str = "manifest",
) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label} unreadable: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} root must be an object")
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


def _validate_prior_revision(
    manifest: dict[str, Any],
    prior_root: pathlib.Path,
    errors: list[str],
) -> None:
    prior_manifest_file = prior_root / MANIFEST_PATH
    current_version = manifest.get("version")
    current_revision = manifest.get("content_revision")
    if not prior_manifest_file.exists():
        if current_revision != 1 or type(current_revision) is not int:
            errors.append(
                "a newly introduced contract must start at content_revision 1"
            )
        return
    if not prior_manifest_file.is_file() or prior_manifest_file.is_symlink():
        errors.append("prior manifest must be a regular file")
        return

    prior = _read_json(prior_manifest_file, errors, "prior manifest")
    if not prior:
        return
    prior_version = prior.get("version")
    prior_revision = prior.get("content_revision")
    if (
        type(current_version) is not int
        or type(current_revision) is not int
        or type(prior_version) is not int
        or type(prior_revision) is not int
        or min(
            current_version,
            current_revision,
            prior_version,
            prior_revision,
        )
        < 1
    ):
        errors.append(
            "current and prior contract versions/revisions must be positive integers"
        )
        return

    if current_version == prior_version:
        artifacts_changed = (
            manifest.get("artifact_sha256") != prior.get("artifact_sha256")
            or manifest.get("artifacts") != prior.get("artifacts")
        )
        expected_revision = (
            prior_revision + 1 if artifacts_changed else prior_revision
        )
        if current_revision != expected_revision:
            errors.append(
                "normative artifact changes require exactly the next "
                "content_revision; unchanged artifacts retain the prior revision"
            )
        return

    if current_version == prior_version + 1:
        if current_revision != 1:
            errors.append("a new contract version must start at content_revision 1")
        return
    errors.append("contract version cannot decrease or skip")


def _validate_consumer_lock_schema(
    root: pathlib.Path,
    errors: list[str],
) -> None:
    schema_file = root / CONSUMER_LOCK_SCHEMA_PATH
    schema = _read_json(schema_file, errors, "consumer lock schema")
    if schema != EXPECTED_CONSUMER_LOCK_SCHEMA:
        errors.append("consumer lock schema must equal the closed V1 schema")


def _canonical_main_contains(
    commit_sha: str,
    errors: list[str],
) -> bool:
    if GIT_EXECUTABLE is None:
        errors.append("canonical GitHub main fetch failed: system Git not found")
        return False
    try:
        with tempfile.TemporaryDirectory(
            prefix="helianthus-modbus-canonical-main-"
        ) as temporary:
            temporary_root = pathlib.Path(temporary)
            bare = temporary_root / "canonical.git"
            clean_env = {
                "GIT_CONFIG_COUNT": "0",
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_SYSTEM": os.devnull,
                "GIT_TERMINAL_PROMPT": "0",
                "HOME": str(temporary_root),
                "LANG": "C",
                "LC_ALL": "C",
                "PATH": os.defpath,
            }
            subprocess.run(
                [GIT_EXECUTABLE, "init", "--bare", "-q", str(bare)],
                check=True,
                capture_output=True,
                text=True,
                env=clean_env,
            )
            subprocess.run(
                [
                    GIT_EXECUTABLE,
                    "-C",
                    str(bare),
                    "-c",
                    "credential.helper=",
                    "-c",
                    "protocol.file.allow=never",
                    "fetch",
                    "--no-tags",
                    "--force",
                    CANONICAL_REPOSITORY_URL,
                    f"+refs/heads/main:{CANONICAL_MAIN_REF}",
                ],
                check=True,
                capture_output=True,
                text=True,
                env=clean_env,
                timeout=120,
            )
            result = subprocess.run(
                [
                    GIT_EXECUTABLE,
                    "-C",
                    str(bare),
                    "merge-base",
                    "--is-ancestor",
                    commit_sha,
                    CANONICAL_MAIN_REF,
                ],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=clean_env,
            )
    except (
        OSError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
    ) as exc:
        errors.append(f"canonical GitHub main fetch failed: {exc}")
        return False
    return result.returncode == 0


def _validate_consumer_lock(
    root: pathlib.Path,
    manifest: dict[str, Any],
    manifest_digest: str,
    lock_path: pathlib.Path,
    docs_commit_sha: str,
    errors: list[str],
) -> None:
    if lock_path.is_relative_to(root):
        errors.append("consumer lock must reside outside the docs checkout")
    lock = _read_json(lock_path, errors, "consumer lock")
    if not lock:
        return
    if set(lock) != CONSUMER_LOCK_KEYS:
        errors.append("consumer lock keys must match the closed schema")

    expected_values = {
        "schema": "helianthus.modbus.companion-consumer-lock",
        "schema_version": 1,
        "repository": manifest.get("repository"),
        "merged_commit_sha": docs_commit_sha,
        "contract_id": manifest.get("contract_id"),
        "contract_version": manifest.get("version"),
        "content_revision": manifest.get("content_revision"),
        "manifest_sha256": manifest_digest,
    }
    for key, expected in expected_values.items():
        if lock.get(key) != expected or (
            isinstance(expected, int) and type(lock.get(key)) is not int
        ):
            errors.append(f"consumer lock {key} does not match companion")

    if re.fullmatch(r"[0-9a-f]{40}", docs_commit_sha) is None:
        errors.append("docs commit SHA must be full lowercase 40-hex")
    try:
        origin_url = subprocess.check_output(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        docs_head = subprocess.check_output(
            [
                "git",
                "-C",
                str(root),
                "rev-parse",
                "--verify",
                "HEAD^{commit}",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        dirty = subprocess.check_output(
            [
                "git",
                "-C",
                str(root),
                "status",
                "--porcelain",
                "--untracked-files=all",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        errors.append("consumer validation requires a valid Git checkout")
    else:
        canonical_urls = {
            "https://github.com/Project-Helianthus/helianthus-docs-ebus",
            "https://github.com/Project-Helianthus/helianthus-docs-ebus.git",
            "git@github.com:Project-Helianthus/helianthus-docs-ebus",
            "git@github.com:Project-Helianthus/helianthus-docs-ebus.git",
        }
        if origin_url not in canonical_urls:
            errors.append("docs checkout origin is not the canonical repository")
        if docs_head != docs_commit_sha:
            errors.append("docs checkout HEAD does not match the consumer lock")
        if dirty:
            errors.append("docs checkout has tracked or untracked modifications")
        if not _canonical_main_contains(docs_commit_sha, errors):
            errors.append("locked docs commit is not on canonical GitHub main")
    merged_commit_sha = lock.get("merged_commit_sha")
    if (
        not isinstance(merged_commit_sha, str)
        or re.fullmatch(r"[0-9a-f]{40}", merged_commit_sha) is None
    ):
        errors.append(
            "consumer lock merged_commit_sha must be full lowercase 40-hex"
        )
    manifest_sha256 = lock.get("manifest_sha256")
    if (
        not isinstance(manifest_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", manifest_sha256) is None
    ):
        errors.append("consumer lock manifest_sha256 must be lowercase 64-hex")


def validate(
    root: pathlib.Path,
    prior_root: pathlib.Path | None = None,
    consumer_lock: pathlib.Path | None = None,
    docs_commit_sha: str | None = None,
    expected_trust_anchor_sha: str | None = None,
) -> tuple[list[str], str | None]:
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
    _validate_consumer_lock_schema(root, errors)
    _require_equal(manifest, "version", 1, errors)
    _require_equal(manifest, "content_revision", 1, errors)
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
        {
            "consumer_lock_schema": "AGPL-3.0",
            "policy": "AGPL-3.0",
            "trusted_revision_validator": "AGPL-3.0",
            "trusted_revision_workflow": "AGPL-3.0",
            "wire": "CC0-1.0",
        },
        errors,
    )
    artifact_hashes = manifest.get("artifact_sha256")
    expected_artifact_keys = {
        "consumer_lock_schema",
        "policy",
        "trusted_revision_validator",
        "trusted_revision_workflow",
        "wire",
    }
    if (
        not isinstance(artifact_hashes, dict)
        or set(artifact_hashes) != expected_artifact_keys
        or any(
            not isinstance(value, str)
            or re.fullmatch(r"[0-9a-f]{64}", value) is None
            for value in artifact_hashes.values()
        )
    ):
        errors.append(
            "artifact_sha256 must contain exact lowercase hashes for "
            "the five normative companion artifacts"
        )
        artifact_hashes = {}
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
    trust_anchor = manifest.get("trust_anchor")
    if not isinstance(trust_anchor, dict) or set(trust_anchor) != {
        "commit_sha",
        "local_mirror",
        "m1_admission_gate",
        "repository",
        "workflow",
    }:
        errors.append("trust_anchor must match the closed schema")
    else:
        commit_sha = trust_anchor.get("commit_sha")
        if (
            not isinstance(commit_sha, str)
            or re.fullmatch(r"[0-9a-f]{40}", commit_sha) is None
        ):
            errors.append(
                "trust_anchor.commit_sha must be full lowercase 40-hex"
            )
        if (
            expected_trust_anchor_sha is not None
            and commit_sha != expected_trust_anchor_sha
        ):
            errors.append(
                "trust_anchor.commit_sha does not match the external anchor"
            )
        expected_anchor_fields = {
            "local_mirror": "scripts/validate_modbus_revision_transition.py",
            "m1_admission_gate": (
                "runtime-gates/fronius-modbus-m1-admission.json"
            ),
            "repository": (
                "Project-Helianthus/helianthus-execution-plans"
            ),
            "workflow": ".github/workflows/modbus-trusted-revision.yml",
        }
        for key, value in expected_anchor_fields.items():
            if trust_anchor.get(key) != value:
                errors.append(f"trust_anchor.{key} must equal {value!r}")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != {
        "consumer_lock_schema",
        "policy",
        "trusted_revision_validator",
        "trusted_revision_workflow",
        "wire",
    }:
        errors.append(
            "artifacts must contain the exact five normative companion artifacts"
        )
        schema_path = None
        policy_path = None
        trusted_validator_path = None
        trusted_workflow_path = None
        wire_path = None
    else:
        schema_path = _artifact(
            root,
            artifacts["consumer_lock_schema"],
            "docs/platform/schemas/",
            "consumer_lock_schema",
            errors,
        )
        policy_path = _artifact(
            root,
            artifacts["policy"],
            "docs/platform/",
            "policy",
            errors,
        )
        trusted_validator_path = _artifact(
            root,
            artifacts["trusted_revision_validator"],
            "scripts/",
            "trusted_revision_validator",
            errors,
        )
        trusted_workflow_path = _artifact(
            root,
            artifacts["trusted_revision_workflow"],
            ".github/workflows/",
            "trusted_revision_workflow",
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
    for label, path in (
        ("consumer_lock_schema", schema_path),
        ("policy", policy_path),
        ("trusted_revision_validator", trusted_validator_path),
        ("trusted_revision_workflow", trusted_workflow_path),
        ("wire", wire_path),
    ):
        if path is None:
            continue
        actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if artifact_hashes.get(label) != actual_digest:
            errors.append(
                f"{label} artifact bytes do not match the manifest hash"
            )
        static_digest = EXPECTED_STATIC_ARTIFACT_SHA256.get(label)
        if static_digest is not None and actual_digest != static_digest:
            errors.append(
                f"{label} artifact bytes do not match contract v1 revision 1"
            )

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
    if prior_root is not None:
        _validate_prior_revision(manifest, prior_root, errors)
    lock_arguments = (consumer_lock, docs_commit_sha)
    if any(value is None for value in lock_arguments) and any(
        value is not None for value in lock_arguments
    ):
        errors.append(
            "--consumer-lock and --docs-commit-sha must be provided together"
        )
    elif (
        consumer_lock is not None
        and docs_commit_sha is not None
    ):
        _validate_consumer_lock(
            root,
            manifest,
            digest,
            consumer_lock,
            docs_commit_sha,
            errors,
        )
    return errors, digest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--prior-root", type=pathlib.Path)
    parser.add_argument("--consumer-lock", type=pathlib.Path)
    parser.add_argument("--docs-commit-sha")
    parser.add_argument("--expected-trust-anchor-sha")
    args = parser.parse_args()
    errors, digest = validate(
        args.root.resolve(),
        args.prior_root.resolve() if args.prior_root else None,
        args.consumer_lock.resolve() if args.consumer_lock else None,
        args.docs_commit_sha,
        args.expected_trust_anchor_sha,
    )
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
