#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from typing import Any


MANIFEST_PATH = pathlib.Path(
    "docs/platform/manifests/modbus-foundation-profile-contract-v1.json"
)
PROTECTED_PATHS = (
    pathlib.Path(".github/workflows/modbus-trusted-revision.yml"),
    pathlib.Path("scripts/validate_modbus_revision_transition.py"),
    pathlib.Path("scripts/validate_modbus_companion.py"),
)
V1_SEMANTIC_VALIDATOR_SHA256 = (
    "7a22d9f88defdc53c1db893dcc496b07232fd60115ddf25f2aad6bcd8152525c"
)
V1_NORMALIZED_MANIFEST_SHA256 = (
    "9ba7a7a02397aec46cb42c69a2fd7bc1572055f68414761b0a49f4460aea8d4d"
)
MAX_MANIFEST_BYTES = 256 * 1024
MAX_ARTIFACT_BYTES = 4 * 1024 * 1024


def expected_workflow(trust_anchor_sha: str) -> dict[str, Any]:
    checkout = (
        "actions/checkout@"
        "11bd71901bbe5b1630ceea73d27597364c9af683"
    )
    return {
        "jobs": {
            "trusted-revision": {
                "name": "Modbus Trusted Revision",
                "runs-on": "ubuntu-latest",
                "steps": [
                    {
                        "name": "Checkout immutable trust anchor",
                        "uses": checkout,
                        "with": {
                            "clean": True,
                            "path": "anchor",
                            "persist-credentials": False,
                            "ref": trust_anchor_sha,
                            "repository": (
                                "Project-Helianthus/"
                                "helianthus-execution-plans"
                            ),
                        },
                    },
                    {
                        "name": "Checkout trusted prior state",
                        "uses": checkout,
                        "with": {
                            "clean": True,
                            "path": "prior",
                            "persist-credentials": False,
                            "ref": "${{ github.event.pull_request.base.sha }}",
                            "repository": (
                                "Project-Helianthus/helianthus-docs-ebus"
                            ),
                        },
                    },
                    {
                        "name": "Checkout untrusted PR head as data",
                        "uses": checkout,
                        "with": {
                            "clean": True,
                            "path": "current",
                            "persist-credentials": False,
                            "ref": "${{ github.event.pull_request.head.sha }}",
                            "repository": (
                                "${{ github.event.pull_request.head.repo.full_name }}"
                            ),
                        },
                    },
                    {
                        "env": {
                            "TRUSTED_BASE_SHA": (
                                "${{ github.event.pull_request.base.sha }}"
                            ),
                            "UNTRUSTED_HEAD_SHA": (
                                "${{ github.event.pull_request.head.sha }}"
                            ),
                        },
                        "name": "Verify immutable checkout identities",
                        "run": (
                            'set -euo pipefail\n'
                            'test "$(git -C anchor rev-parse HEAD)" = '
                            f'"{trust_anchor_sha}"\n'
                            'test "$(git -C prior rev-parse HEAD)" = '
                            '"${TRUSTED_BASE_SHA}"\n'
                            'test "$(git -C current rev-parse HEAD)" = '
                            '"${UNTRUSTED_HEAD_SHA}"'
                        ),
                        "shell": "bash",
                    },
                    {
                        "name": (
                            "Validate Modbus revision transition "
                            "with immutable anchor"
                        ),
                        "run": (
                            "python3 "
                            "anchor/scripts/validate_modbus_docs_trust.py "
                            "--prior-root prior "
                            "--current-root current "
                            f"--trust-anchor-sha {trust_anchor_sha}"
                        ),
                        "shell": "bash",
                    },
                ],
            }
        },
        "name": "Modbus Trusted Revision",
        "on": {
            "pull_request_target": {
                "types": ["opened", "reopened", "synchronize"],
            }
        },
        "permissions": {"contents": "read"},
    }


def _read_manifest(
    root: pathlib.Path,
    label: str,
    errors: list[str],
) -> dict[str, Any] | None:
    path = root / MANIFEST_PATH
    if not path.exists():
        return None
    if not path.is_file() or path.is_symlink():
        errors.append(f"{label} manifest must be a regular file")
        return {}
    try:
        if path.stat().st_size > MAX_MANIFEST_BYTES:
            errors.append(f"{label} manifest exceeds the size limit")
            return {}
        raw = path.read_text(encoding="utf-8")
        value = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label} manifest unreadable: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} manifest root must be an object")
        return {}
    canonical = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if raw != canonical:
        errors.append(f"{label} manifest must use canonical sorted JSON")
    return value


def _positive_int(value: object) -> bool:
    return type(value) is int and value >= 1


def _digest(path: pathlib.Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as artifact_file:
        for chunk in iter(lambda: artifact_file.read(64 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _validate_artifacts(
    root: pathlib.Path,
    manifest: dict[str, Any],
    label: str,
    errors: list[str],
) -> None:
    artifacts = manifest.get("artifacts")
    hashes = manifest.get("artifact_sha256")
    if (
        not isinstance(artifacts, dict)
        or not isinstance(hashes, dict)
        or not artifacts
        or set(artifacts) != set(hashes)
    ):
        errors.append(f"{label} artifact paths and hashes must have equal keys")
        return
    for key, raw_path in artifacts.items():
        digest = hashes.get(key)
        if not isinstance(raw_path, str):
            errors.append(f"{label} artifact {key} path must be a string")
            continue
        relative = pathlib.PurePosixPath(raw_path)
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"{label} artifact {key} path is unsafe")
            continue
        path = root / pathlib.Path(*relative.parts)
        if (
            not path.is_file()
            or path.is_symlink()
            or not path.resolve().is_relative_to(root)
        ):
            errors.append(f"{label} artifact {key} must be a regular in-repo file")
            continue
        if path.stat().st_size > MAX_ARTIFACT_BYTES:
            errors.append(f"{label} artifact {key} exceeds the size limit")
            continue
        if not isinstance(digest, str) or re.fullmatch(
            r"[0-9a-f]{64}", digest
        ) is None:
            errors.append(f"{label} artifact {key} hash must be lowercase 64-hex")
            continue
        if _digest(path) != digest:
            errors.append(f"{label} artifact {key} bytes do not match its hash")


def _revision_payload(manifest: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(manifest)
    payload.pop("content_revision", None)
    consumer_pin = payload.get("consumer_pin")
    if isinstance(consumer_pin, dict):
        consumer_pin.pop("content_revision", None)
    return payload


def _normalized_manifest_digest(manifest: dict[str, Any]) -> str | None:
    normalized = copy.deepcopy(manifest)
    trust_anchor = normalized.get("trust_anchor")
    hashes = normalized.get("artifact_sha256")
    if not isinstance(trust_anchor, dict) or not isinstance(hashes, dict):
        return None
    trust_anchor["commit_sha"] = "<trust-anchor-sha>"
    hashes["trusted_revision_validator"] = (
        "<trusted-revision-validator-sha256>"
    )
    hashes["trusted_revision_workflow"] = (
        "<trusted-revision-workflow-sha256>"
    )
    canonical = json.dumps(normalized, indent=2, sort_keys=True) + "\n"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_closed_v1(
    root: pathlib.Path,
    manifest: dict[str, Any],
    label: str,
    trust_anchor_sha: str,
    errors: list[str],
) -> None:
    if _normalized_manifest_digest(manifest) != V1_NORMALIZED_MANIFEST_SHA256:
        errors.append(
            f"{label} manifest is not the independently frozen V1 contract"
        )
    trust_anchor = manifest.get("trust_anchor")
    if (
        not isinstance(trust_anchor, dict)
        or trust_anchor.get("commit_sha") != trust_anchor_sha
    ):
        errors.append(
            f"{label} manifest trust anchor does not match the executing anchor"
        )
    semantic_validator = root / PROTECTED_PATHS[2]
    if (
        not semantic_validator.is_file()
        or semantic_validator.is_symlink()
        or _digest(semantic_validator) != V1_SEMANTIC_VALIDATOR_SHA256
    ):
        errors.append(
            f"{label} semantic validator is not the independently frozen V1 "
            "validator"
        )


def _validate_protected_paths(
    prior_root: pathlib.Path,
    current_root: pathlib.Path,
    trust_anchor_sha: str,
    errors: list[str],
) -> None:
    bootstrap = any(
        not (prior_root / relative).exists() for relative in PROTECTED_PATHS
    )
    for relative in PROTECTED_PATHS:
        prior = prior_root / relative
        current = current_root / relative
        if not prior.exists():
            if not current.is_file() or current.is_symlink():
                errors.append(
                    f"bootstrap must introduce protected path {relative.as_posix()}"
                )
            continue
        if not prior.is_file() or prior.is_symlink():
            errors.append(f"prior protected path is invalid: {relative.as_posix()}")
            continue
        if not current.is_file() or current.is_symlink():
            errors.append(f"protected path cannot be removed: {relative.as_posix()}")
            continue
        if _digest(prior) != _digest(current):
            errors.append(f"protected path is immutable: {relative.as_posix()}")
    if not bootstrap:
        return
    mirror = current_root / PROTECTED_PATHS[1]
    workflow = current_root / PROTECTED_PATHS[0]
    if mirror.is_file() and _digest(mirror) != _digest(
        pathlib.Path(__file__).resolve()
    ):
        errors.append("bootstrap transition mirror must equal the trust anchor")
    semantic_validator = current_root / PROTECTED_PATHS[2]
    if (
        semantic_validator.is_file()
        and _digest(semantic_validator) != V1_SEMANTIC_VALIDATOR_SHA256
    ):
        errors.append(
            "bootstrap semantic validator must equal the frozen V1 validator"
        )
    if not workflow.is_file():
        return
    try:
        raw = workflow.read_text(encoding="utf-8")
        parsed = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"bootstrap trusted workflow must be canonical JSON: {exc}")
        return
    canonical = json.dumps(parsed, indent=2, sort_keys=True) + "\n"
    if raw != canonical:
        errors.append("bootstrap trusted workflow must use canonical sorted JSON")
    if parsed != expected_workflow(trust_anchor_sha):
        errors.append("bootstrap trusted workflow structure is not exact")


def validate_transition(
    prior_root: pathlib.Path,
    current_root: pathlib.Path,
    trust_anchor_sha: str,
) -> list[str]:
    errors: list[str] = []
    if re.fullmatch(r"[0-9a-f]{40}", trust_anchor_sha) is None:
        errors.append("trust anchor SHA must be full lowercase 40-hex")
    prior = _read_manifest(prior_root, "prior", errors)
    current = _read_manifest(current_root, "current", errors)
    _validate_protected_paths(
        prior_root,
        current_root,
        trust_anchor_sha,
        errors,
    )

    if prior is None and current is None:
        return errors
    if prior is not None and current is None:
        errors.append("the Modbus companion manifest cannot be removed")
        return errors
    if not current:
        return errors

    current_version = current.get("version")
    current_revision = current.get("content_revision")
    if not _positive_int(current_version) or not _positive_int(
        current_revision
    ):
        errors.append("current version and content_revision must be positive integers")
        return errors
    consumer_pin = current.get("consumer_pin")
    if (
        not isinstance(consumer_pin, dict)
        or consumer_pin.get("content_revision") != current_revision
        or type(consumer_pin.get("content_revision")) is not int
    ):
        errors.append("current consumer pin must carry the content_revision")
    _validate_artifacts(current_root, current, "current", errors)
    _validate_closed_v1(
        current_root,
        current,
        "current",
        trust_anchor_sha,
        errors,
    )

    if prior is None:
        if current_version != 1 or current_revision != 1:
            errors.append("the first Modbus companion must start at version 1 revision 1")
        return errors
    if not prior:
        return errors

    prior_version = prior.get("version")
    prior_revision = prior.get("content_revision")
    if not _positive_int(prior_version) or not _positive_int(prior_revision):
        errors.append("prior version and content_revision must be positive integers")
        return errors
    _validate_artifacts(prior_root, prior, "prior", errors)
    _validate_closed_v1(
        prior_root,
        prior,
        "prior",
        trust_anchor_sha,
        errors,
    )
    if current.get("repository") != prior.get("repository"):
        errors.append("companion repository identity cannot change")

    if current_version == prior_version:
        changed = _revision_payload(current) != _revision_payload(prior)
        expected_revision = prior_revision + 1 if changed else prior_revision
        if current_revision != expected_revision:
            errors.append(
                "same-version contract changes require exactly the next "
                "content_revision; unchanged contracts retain the prior revision"
            )
    elif current_version == prior_version + 1:
        if current_revision != 1:
            errors.append("a new contract version must start at content_revision 1")
    else:
        errors.append("contract version cannot decrease or skip")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior-root", type=pathlib.Path, required=True)
    parser.add_argument("--current-root", type=pathlib.Path, required=True)
    parser.add_argument("--trust-anchor-sha", required=True)
    args = parser.parse_args()
    errors = validate_transition(
        args.prior_root.resolve(),
        args.current_root.resolve(),
        args.trust_anchor_sha,
    )
    anchor_root = pathlib.Path(__file__).resolve().parents[1]
    try:
        anchor_head = subprocess.check_output(
            ["git", "-C", str(anchor_root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        anchor_status = subprocess.check_output(
            [
                "git",
                "-C",
                str(anchor_root),
                "status",
                "--porcelain",
                "--untracked-files=all",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        errors.append("trust anchor must execute from a Git checkout")
    else:
        if anchor_head != args.trust_anchor_sha:
            errors.append("executed trust anchor HEAD does not match pinned SHA")
        if anchor_status:
            errors.append("trust anchor checkout must be fully clean")
    if errors:
        for error in errors:
            print(f"modbus_docs_trust_invalid: {error}", file=sys.stderr)
        return 1
    print("modbus_docs_trust_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
