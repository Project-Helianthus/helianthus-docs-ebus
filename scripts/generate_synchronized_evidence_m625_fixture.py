#!/usr/bin/env python3
"""Generate the independent M6.25 synchronized-evidence bundle and replay."""

from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys
from typing import Any


SCRIPT_ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_ROOT.parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

import validate_synchronized_evidence as synchronized


HISTORICAL_BUNDLE = (
    REPO_ROOT
    / "docs/platform/fixtures/synchronized-evidence/v1/positive/bundle.json"
)
REGISTRY = (
    REPO_ROOT
    / "docs/platform/schemas/synchronized-evidence-source-registry-v1.json"
)
DEFAULT_OUTPUT = (
    REPO_ROOT
    / "docs/platform/fixtures/synchronized-evidence/v1/m625/positive"
)
SOURCE_CONTRACT = "helianthus.eebus.m625.public-redacted-evidence.v1"
OWNER_COMMIT = "a09e3a77153204bc3117e233c71e77ef1859834e"
OWNER_PATH = (
    "api/_candidate/msp-0625/"
    "helianthus.eebus.m625.public-redacted-evidence.v1.schema.json"
)
SCHEMA_SHA256 = (
    "0a2885d01d6703389541e246db59bcd845a332e7ed296abca2d49b4f8de31811"
)
OPERATION_VERSION = "git:1a02388170a1ee6befeed1529956a7104aa94e21"


def load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object: {path}")
    return value


def pretty_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def compact_bytes(value: Any) -> bytes:
    return synchronized.canonical(value) + b"\n"


def source_payload(source_observed_at: str) -> dict[str, Any]:
    service = "K" * 43
    entity = "L" * 43
    feature = "M" * 43
    field = "N" * 43
    observation = "P" * 43
    return {
        "contract": SOURCE_CONTRACT,
        "schema_version": 1,
        "source_observed_at": source_observed_at,
        "services": [service],
        "feature_paths": [
            {
                "service": service,
                "entity": entity,
                "feature": feature,
                "feature_path": [
                    {"kind": "SERVICE", "selector": service},
                    {"kind": "ENTITY", "selector": entity},
                    {"kind": "FEATURE", "selector": feature},
                    {"kind": "FIELD", "selector": field},
                ],
            }
        ],
        "observations": [
            {
                "observation_ref": "obs-" + observation,
                "path_index": 0,
                "feature_type": "Measurement",
                "feature_role": "server",
                "function": "measurementListData",
                "source_observed_at": source_observed_at,
                "terminal_classification": "SUCCESS",
                "value_type": "DECIMAL",
                "value": "21.5",
                "unit": "degC",
                "quality": "OBSERVED",
            }
        ],
    }


def replace_eebus_source(bundle: dict[str, Any]) -> None:
    source = next(
        row for row in bundle["sources"] if row["source_kind"] == "EEBUS"
    )
    artifact = next(
        row for row in bundle["artifacts"] if row["source_kind"] == "EEBUS"
    )
    binding = copy.deepcopy(source["source_binding"])
    binding.update(
        {
            "operation_id": "eebus.v1.features.data.get",
            "operation_version": OPERATION_VERSION,
            "snapshot_scope": {
                "mode": "LIVE_READ",
                "selector": "feature-data",
            },
            "source_contract": SOURCE_CONTRACT,
            "source_schema_version": 1,
            "owner_repository": "Project-Helianthus/helianthus-docs-eebus",
            "owner_path": OWNER_PATH,
            "owner_commit": OWNER_COMMIT,
            "schema_sha256": SCHEMA_SHA256,
        }
    )
    binding["request_scope"]["operation_scope"] = "feature-data"

    source["source_contract"] = SOURCE_CONTRACT
    source["source_schema_version"] = 1
    source["source_binding"] = copy.deepcopy(binding)

    payload = source_payload(artifact["source_observed_at"])
    artifact["source_contract"] = SOURCE_CONTRACT
    artifact["source_schema_version"] = 1
    artifact["source_binding"] = copy.deepcopy(binding)
    artifact["normalized_evidence"] = payload
    artifact["item_count"] = len(payload["observations"])
    artifact["byte_count"] = len(synchronized.canonical(payload))
    artifact["remasking"] = {
        "method": "PER_BUNDLE_CSPRNG",
        "scope_id": artifact["remasking"]["scope_id"],
        "entries": [
            {
                "path": "/feature_paths/0/entity",
                "pseudonym": payload["feature_paths"][0]["entity"],
            },
            {
                "path": "/feature_paths/0/feature",
                "pseudonym": payload["feature_paths"][0]["feature"],
            },
            {
                "path": "/feature_paths/0/feature_path/3/selector",
                "pseudonym": payload["feature_paths"][0]["feature_path"][3][
                    "selector"
                ],
            },
            {
                "path": "/observations/0/observation_ref",
                "pseudonym": payload["observations"][0][
                    "observation_ref"
                ].removeprefix("obs-"),
            },
            {
                "path": "/services/0",
                "pseudonym": payload["services"][0],
            },
        ],
    }

    artifact_view = {
        key: value
        for key, value in artifact.items()
        if key not in {"artifact_id", "redacted_hash"}
    }
    artifact_hash = synchronized.digest(
        synchronized.ARTIFACT_DOMAIN, artifact_view
    )
    artifact["artifact_id"] = "seav1:sha256:" + artifact_hash
    artifact["redacted_hash"] = "sha256:" + artifact_hash
    source["artifact_ids"] = [artifact["artifact_id"]]


def generate() -> tuple[bytes, bytes]:
    bundle = load_json(HISTORICAL_BUNDLE)
    replace_eebus_source(bundle)
    bundle["sources"].sort(
        key=lambda row: (
            synchronized.PHASE_RANK[row["phase"]],
            synchronized.KIND_RANK[row["source_kind"]],
            row["source_id"],
        )
    )
    bundle["artifacts"].sort(
        key=lambda row: (
            synchronized.PHASE_RANK[row["phase"]],
            synchronized.KIND_RANK[row["source_kind"]],
            row["source_id"],
            row["artifact_id"],
        )
    )
    bundle_view = {
        key: value
        for key, value in bundle.items()
        if key not in {"bundle_id", "bundle_hash"}
    }
    bundle_hash = synchronized.digest(
        synchronized.BUNDLE_DOMAIN, bundle_view
    )
    bundle["bundle_id"] = "sebv1:sha256:" + bundle_hash
    bundle["bundle_hash"] = "sha256:" + bundle_hash
    bundle_bytes = pretty_bytes(bundle)

    registry = synchronized.load_registry(REGISTRY)
    verified = synchronized.verify(
        copy.deepcopy(bundle), registry, len(bundle_bytes)
    )
    replay = synchronized.replay(verified)
    return bundle_bytes, compact_bytes(replay)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=pathlib.Path,
        default=DEFAULT_OUTPUT,
    )
    args = parser.parse_args()
    bundle, replay = generate()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "bundle.json").write_bytes(bundle)
    (args.output_dir / "replay-result.json").write_bytes(replay)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
