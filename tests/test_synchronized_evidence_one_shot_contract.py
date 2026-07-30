from __future__ import annotations

import json
import pathlib


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = REPO_ROOT / "docs/platform/synchronized-evidence-one-shot-control-v1.md"
SCHEMA = (
    REPO_ROOT
    / "docs/platform/schemas/synchronized-evidence-one-shot-control-v1.schema.json"
)
INDEX = REPO_ROOT / "docs/platform/README.md"


def load_json(path: pathlib.Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_one_shot_control_inventory_is_canonical_and_indexed() -> None:
    assert PAGE.is_file()
    assert SCHEMA.is_file()
    assert PAGE.name in INDEX.read_text(encoding="utf-8")


def test_machine_contract_freezes_private_tool_paths_and_empty_args() -> None:
    schema = load_json(SCHEMA)
    control = schema["x-helianthus-one-shot-control"]
    assert control == {
        "tool": "helianthus.v1.synchronized_evidence.capture",
        "arguments": "#/$defs/EmptyArgsV1",
        "transport": "AF_UNIX",
        "socket_boundary": "EXISTING_OPERATOR_SOCKET",
        "peer_uid": "SAME_UID",
        "visibility": "OWNER_ONLY_PRIVATE",
        "public_tools_list": "OMITTED",
        "request_path": (
            "/data/synchronized-evidence/one-shot-request-v1.json"
        ),
        "request_mode": "0600",
        "request_loading": "DESCRIPTOR_RELATIVE_NO_SYMLINK_NO_TRAVERSAL",
        "store_directory": "/data/synchronized-evidence/store",
        "store_loading": "DESCRIPTOR_RELATIVE_NO_SYMLINK_NO_TRAVERSAL",
        "selection": "ALL_SERVER_MEASUREMENT_SETPOINT_HVAC",
        "sort_key": "COMPLETE_NATIVE_TUPLE",
        "batch_max": 16,
        "caller_targets": "FORBIDDEN",
        "action_input": "PRECAPTURED_CLOUD_APP",
        "source_kind": "EEBUS",
        "source_contract": (
            "helianthus.eebus.m625.public-redacted-evidence.v1"
        ),
        "source_schema_version": 1,
        "idempotency_key": "ACTION_EVIDENCE_REF_PLUS_SOURCE_TUPLE",
        "prepublish_replay_count": 2,
        "prepublish_replay_input": "FINALIZED_CANONICAL_STAGING_BYTES",
        "prepublish_replay_equality": "BYTE_IDENTICAL",
        "postpublish_verification": "REOPEN_VALIDATE_REPLAY_MATCH",
        "receipt_after": "ATOMIC_PUBLISH_REOPEN_VALIDATE_REPLAY",
        "repeat_result": (
            "EXISTING_NO_RUNTIME_NETWORK_SOURCE_ACQUISITION_IO"
        ),
        "repeat_allowed_io": (
            "REQUEST_STORE_READ_RETAINED_VALIDATION_OFFLINE_REPLAY"
        ),
        "repeat_forbidden_new": "TIMESTAMPS_BUNDLE_PSEUDONYMS_STAGING",
    }
    args = schema["$defs"]["EmptyArgsV1"]
    assert args == {
        "type": "object",
        "additionalProperties": False,
        "maxProperties": 0,
    }


def test_request_is_closed_precaptured_and_has_no_target_selection() -> None:
    schema = load_json(SCHEMA)
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "contract",
        "schema_version",
        "action_evidence_ref",
        "cloud_app_action",
    }
    encoded = json.dumps(schema, sort_keys=True).lower()
    for forbidden in (
        '"targets"',
        '"target"',
        '"selectors"',
        '"feature_addresses"',
        '"remote_ski"',
    ):
        assert forbidden not in encoded
    cloud = schema["properties"]["cloud_app_action"]
    assert cloud["additionalProperties"] is False
    assert set(cloud["required"]) == {"evidence_ref", "normalized_evidence"}


def test_receipt_is_category_only_and_closed() -> None:
    receipt = load_json(SCHEMA)["$defs"]["ReceiptV1"]
    assert receipt["additionalProperties"] is False
    assert receipt["required"] == ["category"]
    assert set(receipt["properties"]) == {"category"}
    assert set(receipt["properties"]["category"]["enum"]) == {
        "PUBLISHED",
        "EXISTING",
        "INVALID_REQUEST",
        "PERMISSION_DENIED",
        "CONFLICT",
        "ACQUISITION_FAILED",
        "REPLAY_MISMATCH",
        "PUBLISH_FAILED",
        "INTERNAL",
    }


def test_docs_freeze_crash_idempotency_selection_and_publish_order() -> None:
    text = PAGE.read_text(encoding="utf-8")
    required = (
        "already existing `AF_UNIX` operator socket",
        "same effective UID",
        "descriptor-relative no-symlink/no-traversal loader",
        "`/data/synchronized-evidence/one-shot-request-v1.json`",
        "mode `0600`",
        "`/data/synchronized-evidence/store`",
        "all server Measurement, Setpoint, and HVAC features",
        "complete native tuple",
        "maximum batch size is exactly 16",
        "caller cannot supply targets",
        "pre-captured `CLOUD_APP` action evidence",
        "validated retained-bundle lookup",
        "action evidence ref plus the M6.25 source tuple",
        "before any acquisition",
        "two offline byte-identical replays consume the finalized canonical staging bytes",
        "before atomic publication",
        "re-opens the final bundle, validates it, and verifies replay",
        "success receipt only after",
        "including after process restart",
        "request and store reads, retained-bundle validation, and offline replay",
        "no runtime, network, or source-acquisition I/O",
        "no new timestamps, bundle, pseudonyms, or staging artifact",
        "response and logs contain no raw evidence",
        "public `tools/list` omits",
    )
    for phrase in required:
        assert phrase in text
    assert "no new reads" not in text
    assert "EXISTING_NO_IO" not in SCHEMA.read_text(encoding="utf-8")
