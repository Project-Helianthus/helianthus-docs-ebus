#!/usr/bin/env python3
"""Generate deterministic MSP-085-LIVE-R2 conformance fixtures."""

from __future__ import annotations

import importlib.util
import json
import pathlib
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/validate_captured_multi_leaf_promotion.py"
REGISTRY = ROOT / "docs/platform/schemas/leaf-promotion-captured-multi-leaf-registry-v1.json"
FIXTURE = ROOT / "docs/platform/fixtures/leaf-promotion-captured-multi-leaf/v1"


def validator_module():
    spec = importlib.util.spec_from_file_location("multi_leaf_validator", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(character: str) -> str:
    return "sha256:" + character * 64


def encoded(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        + b"\n"
    )


def typed_numeric(number: int, scale: int) -> dict[str, object]:
    return {
        "kind": "NUMERIC",
        "decimal": {"number": number, "scale": scale},
        "enum": None,
        "boolean": None,
    }


def typed_enum(value: str) -> dict[str, object]:
    return {"kind": "ENUM", "decimal": None, "enum": value, "boolean": None}


def typed_boolean(value: bool) -> dict[str, object]:
    return {"kind": "BOOLEAN", "decimal": None, "enum": None, "boolean": value}


def ebus_identity(module, candidate: dict[str, Any]) -> dict[str, Any]:
    selector = candidate["ebus_selector"]
    assert isinstance(selector, dict)
    identity = {
        **selector,
        "target_pseudonym": "target-" + "1" * 32,
        "target_address": 21,
        "source_address": 253,
        "selector_hash": sha("0"),
    }
    identity["selector_hash"] = module.digest(
        module.EBUS_SELECTOR_DOMAIN,
        {key: value for key, value in identity.items() if key != "selector_hash"},
    )
    return identity


def eebus_identity(module, candidate: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(candidate["candidate_id"])
    source = candidate["eebus_source"]
    assert isinstance(source, dict)
    index = int(candidate_id[-4:])
    identity = {
        "service_id": "sanitized-service-v1",
        "device_address": "sanitized-device-v1",
        "entity_address": [1000 + index],
        "feature_address": 100 + index,
        **source,
        "source_profile_hash": module.digest(module.SOURCE_PROFILE_DOMAIN, source),
        "identity_hash": sha("0"),
    }
    identity["identity_hash"] = module.digest(
        module.EEBUS_IDENTITY_DOMAIN,
        {key: value for key, value in identity.items() if key != "identity_hash"},
    )
    return identity


def sample(
    module,
    source: str,
    timestamp: str,
    raw_value: dict[str, object],
    value: dict[str, object],
    unit: str | None,
    window: dict[str, object],
    suffix: str,
) -> dict[str, object]:
    return {
        "source": source,
        "observed_at": timestamp,
        "valid": True,
        "capture_generation": window["capture_generation"],
        "poll_id": "poll-" + suffix if source == "EBUS" else None,
        "poll_generation": window["ebus_poll_generation"] if source == "EBUS" else None,
        "runtime_epoch": window["eebus_runtime_epoch"] if source == "EEBUS" else None,
        "connection_generation": (
            window["connection_generation"] if source == "EEBUS" else None
        ),
        "raw_hash": module.digest(module.RAW_VALUE_DOMAIN, raw_value),
        "raw_value": raw_value,
        "value": value,
        "unit": unit,
    }


def comparator(module, expected: dict[str, Any], outcome: str) -> dict[str, Any]:
    source = expected["eebus_source"]
    assert isinstance(source, dict)
    if expected["comparator_class"] == "NUMERIC_DECLARED_GRANULARITY":
        return {
            "class": expected["comparator_class"],
            "declared_spine_step": source["declared_constraints"]["step"],
            "delta": None,
            "conversion": source["conversion"],
            "mapping_hash": None,
            "outcome": outcome,
        }
    return {
        "class": expected["comparator_class"],
        "declared_spine_step": None,
        "delta": None,
        "conversion": None,
        "mapping_hash": module.digest(module.MAPPING_DOMAIN, source["mapping_profile"]),
        "outcome": outcome,
    }


def missing_eebus_sample(
    module,
    expected: dict[str, Any],
    window: dict[str, object],
    timestamp: str,
    suffix: str,
) -> dict[str, object]:
    source = expected["eebus_source"]
    assert isinstance(source, dict)
    if expected["comparator_class"] == "NUMERIC_DECLARED_GRANULARITY":
        raw = typed_numeric(20, 0)
        value = typed_numeric(20, 0)
    elif expected["comparator_class"] == "ENUM_EXACT_MAPPING":
        raw = typed_numeric(2, 0)
        value = typed_enum("off")
    else:
        raw = typed_boolean(False)
        value = typed_boolean(False)
    return sample(module, "EEBUS", timestamp, raw, value, source["unit"], window, suffix)


def build_campaign(module, registry: dict[str, Any]) -> dict[str, Any]:
    windows: list[dict[str, Any]] = [
        {
            "window_id": "window-pre-restart",
            "phase": "PRE_RESTART",
            "started_at": "2026-08-11T10:00:00Z",
            "ended_at": "2026-08-11T10:00:10Z",
            "capture_generation": "capture-pre",
            "process_instance_hash": sha("1"),
            "local_identity_hash": sha("3"),
            "trust_state_hash": sha("4"),
            "admitted_source": 253,
            "eebus_runtime_epoch": 2,
            "connection_generation": 94,
            "ebus_poll_generation": "poll-generation-pre",
            "m8_no_drift": True,
            "rollback_exact": True,
        },
        {
            "window_id": "window-post-restart",
            "phase": "POST_RESTART",
            "started_at": "2026-08-11T10:05:00Z",
            "ended_at": "2026-08-11T10:05:10Z",
            "capture_generation": "capture-post",
            "process_instance_hash": sha("2"),
            "local_identity_hash": sha("3"),
            "trust_state_hash": sha("4"),
            "admitted_source": 253,
            "eebus_runtime_epoch": 2,
            "connection_generation": 1,
            "ebus_poll_generation": "poll-generation-post",
            "m8_no_drift": True,
            "rollback_exact": True,
        },
    ]
    candidates: list[dict[str, Any]] = []
    for expected in registry["candidate_catalog"]:
        candidate = {
            "candidate_id": expected["candidate_id"],
            "fact_hash": expected["fact_hash"],
            "source_status": expected["source_status"],
            "semantic_path": expected["semantic_path"],
            "comparator_class": expected["comparator_class"],
            "ebus_identity": None,
            "eebus_identity": None,
            "assessments": [],
            "decision": "WITHHELD",
            "terminal_state": expected["terminal_state"],
            "visibility": "RAW_DEBUG_ONLY",
            "dossier_hash": None,
        }
        if expected["protocol_eligibility"] != "TERMINAL":
            candidate["eebus_identity"] = eebus_identity(module, expected)
        if expected["protocol_eligibility"] == "WITHHOLD_NO_EBUS_CAPABILITY_SOURCE":
            candidate["terminal_state"] = "NOT_COMPARABLE"
        elif expected["protocol_eligibility"] == "ELIGIBLE":
            candidate["ebus_identity"] = ebus_identity(module, expected)
            candidate["terminal_state"] = "MISSING"
            for position, window in enumerate(windows):
                prefix = "2026-08-11T10:00:05" if position == 0 else "2026-08-11T10:05:05"
                candidate["assessments"].append(
                    {
                        "window_id": window["window_id"],
                        "ebus_sample": None,
                        "eebus_sample": missing_eebus_sample(
                            module,
                            expected,
                            window,
                            prefix + ".100000000Z",
                            "pre" if position == 0 else "post",
                        ),
                        "skew_ns": None,
                        "max_skew_ns": registry["capture_limits"]["max_skew_ns"],
                        "age_ns": None,
                        "max_age_ns": registry["capture_limits"]["max_age_ns"],
                        "comparator": comparator(module, expected, "MISSING"),
                    }
                )
        candidates.append(candidate)

    promoted = candidates[-1]
    promoted_expected = registry["candidate_catalog"][-1]
    promoted["decision"] = "PROMOTED"
    promoted["terminal_state"] = None
    promoted["visibility"] = "LOCKED_NOT_EXPOSED"
    promoted["assessments"] = []
    for position, window in enumerate(windows):
        prefix = "2026-08-11T10:00:05" if position == 0 else "2026-08-11T10:05:05"
        ebus_value = typed_numeric(125 if position == 0 else 13, -1 if position == 0 else 0)
        eebus_value = typed_numeric(13 if position == 0 else 135, 0 if position == 0 else -1)
        promoted_comparator = comparator(module, promoted_expected, "MATCH")
        promoted_comparator["delta"] = {"number": 5, "scale": -1}
        promoted["assessments"].append(
            {
                "window_id": window["window_id"],
                "ebus_sample": sample(
                    module,
                    "EBUS",
                    prefix + "Z",
                    ebus_value,
                    ebus_value,
                    "degC",
                    window,
                    "pre" if position == 0 else "post",
                ),
                "eebus_sample": sample(
                    module,
                    "EEBUS",
                    prefix + ".100000000Z",
                    eebus_value,
                    eebus_value,
                    "degC",
                    window,
                    "pre" if position == 0 else "post",
                ),
                "skew_ns": 100_000_000,
                "max_skew_ns": registry["capture_limits"]["max_skew_ns"],
                "age_ns": 5_000_000_000,
                "max_age_ns": registry["capture_limits"]["max_age_ns"],
                "comparator": promoted_comparator,
            }
        )
    promoted["dossier_hash"] = module.digest(
        module.DOSSIER_DOMAIN, module._candidate_payload(promoted)
    )

    campaign = {
        "contract": "helianthus.platform.leaf-promotion-captured-multi-leaf.v1",
        "schema_version": 1,
        "profile": "CAPTURED_RUNTIME_MULTI_LEAF_V1",
        "evidence_mode": "SANITIZED_CONFORMANCE",
        "export_tier": "PRIVATE_OPERATOR",
        "provenance": registry["sanitized_provenance"],
        "source_bindings": {
            "registry_sha256": module.PINNED_REGISTRY_SHA256,
            "docs_eebus_commit": registry["docs_eebus_source_commit"],
            "m7_graph_id": "dcfgv1:captured-campaign",
            "m7_graph_hash": sha("a"),
            "m7_status_id": "dcfpsv1:captured-campaign",
            "m7_status_hash": sha("b"),
            "m8_evidence_id": "mrcv1:captured-campaign",
            "m8_evidence_hash": sha("c"),
            "m8_report_id": "mrcrv1:captured-campaign",
            "m8_report_hash": sha("d"),
            "replay_hash": sha("0"),
        },
        "windows": windows,
        "candidates": candidates,
        "campaign_hash": sha("0"),
    }
    campaign["source_bindings"]["replay_hash"] = module.replay_hash(campaign)
    campaign["campaign_hash"] = module.digest(
        module.CAMPAIGN_DOMAIN,
        {key: value for key, value in campaign.items() if key != "campaign_hash"},
    )
    module.verify_private(campaign, registry)
    return campaign


def write(path: pathlib.Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(encoded(value))


def main() -> None:
    module = validator_module()
    registry, _ = module.load_json(REGISTRY)
    module.registry_value(REGISTRY)
    campaign = build_campaign(module, registry)
    private_raw = encoded(campaign)
    public = module.derive_public(campaign, registry, private_raw)
    write(FIXTURE / "positive/private-campaign.json", campaign)
    write(FIXTURE / "positive/public-result.json", public)
    negatives = {
        "granularity-substitution.json": ("GRANULARITY_SUBSTITUTION", "comparator.invalid"),
        "missing-granularity.json": ("MISSING_GRANULARITY", "schema.private"),
        "identity-mismatch.json": ("IDENTITY_MISMATCH", "identity.binding"),
        "generation-change.json": ("GENERATION_CHANGE", "sample.invalid"),
        "skew-exceeded.json": ("SKEW_EXCEEDED", "sample.invalid"),
        "stale-sample.json": ("STALE_SAMPLE", "sample.invalid"),
        "missing-sample.json": ("MISSING_SAMPLE", "comparator.invalid"),
        "conflict-as-match.json": ("CONFLICT_AS_MATCH", "state.invalid"),
        "replay-drift.json": ("REPLAY_DRIFT", "hash.replay"),
        "public-identity-leak.json": ("PUBLIC_IDENTITY_LEAK", "schema.public"),
        "public-secret-leak.json": ("PUBLIC_SECRET_LEAK", "schema.public"),
    }
    for name, (mutation, category) in negatives.items():
        write(
            FIXTURE / "negative" / name,
            {
                "contract": "helianthus.platform.leaf-promotion-captured-multi-leaf-negative.v1",
                "mutation": mutation,
                "expected_category": category,
            },
        )


if __name__ == "__main__":
    main()
