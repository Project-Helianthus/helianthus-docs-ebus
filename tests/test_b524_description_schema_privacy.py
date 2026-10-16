"""Exercise closed native description objects through the public schema."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "protocols/vaillant/fixtures/b524-basv0-description-profile-schema-v1.json"
SCHEMA_DOCUMENT = json.loads(SCHEMA.read_text())

# Schema pointers and corresponding locations in the synthetic profile. Only
# explicit additionalProperties=false nodes belong here, not open subschemas.
CLOSED_OBJECTS = [
    ("", ()),
    ("/properties/local_profile", ("local_profile",)),
    ("/$defs/record", ("records", 0)),
    ("/$defs/selector", ("records", 0, "selector")),
    ("/$defs/decoded", ("records", 0, "decoded")),
    ("/$defs/rawLimits", ("records", 0, "raw_limits")),
    (
        "/$defs/record/properties/remote_identity/oneOf/1",
        ("records", 1, "remote_identity"),
    ),
]


def synthetic_profile() -> dict:
    properties = SCHEMA_DOCUMENT["properties"]
    local = {
        "selector": {
            "operation": "02", "group": "FE", "instance": "00",
            "register": "FFFE",
        },
        "identity_scope": "local",
        "name": "synthetic_parameter",
        "access_flags": "00",
        "presence_state": "unknown",
        "response_state": "describe_matched",
        "raw_description_hex": "000000000000",
        "description_payload_length": 3,
        "raw_limits": {"min_hex": "00", "max_hex": "01", "step_hex": "01"},
        "decoded": {
            "codec": "UCH", "codec_provenance": "length_inferred",
            "codec_basis": "payload_length_inferred",
            "qualification": "unqualified", "min": 0, "max": 1, "step": 1,
        },
        "observed_read_payload_width": 1,
        "remote_identity": None,
    }
    remote = deepcopy(local)
    remote["selector"]["operation"] = "06"
    remote["identity_scope"] = "remote"
    remote["remote_identity"] = {
        "qualification": "observed_remote_header", "group": "FE",
        "address_raw": "00", "firmware_raw": "000000",
    }
    return {
        key: properties[key]["const"]
        for key in ("schema_version", "evidence_class", "observation_id")
    } | {
        "local_profile": {
            key: value["const"]
            for key, value in properties["local_profile"]["properties"].items()
        },
        "records": [local, remote],
        "nonclaims": ["Synthetic schema control; no device observation or qualification."],
    }


def closed_nodes(node, pointer="") -> set[str]:
    if isinstance(node, dict):
        found = {pointer} if node.get("additionalProperties") is False else set()
        for key, value in node.items():
            found.update(closed_nodes(value, f"{pointer}/{key}"))
        return found
    if isinstance(node, list):
        return set().union(*(
            closed_nodes(value, f"{pointer}/{index}")
            for index, value in enumerate(node)
        ))
    return set()


def test_closed_object_inventory_matches_public_description_schema() -> None:
    assert closed_nodes(SCHEMA_DOCUMENT) == {schema for schema, _ in CLOSED_OBJECTS}


def validate(tmp_path: Path, document: dict) -> subprocess.CompletedProcess[str]:
    path = tmp_path / "synthetic-description.json"
    path.write_text(json.dumps(document))
    return subprocess.run(
        ["jv", "-o", "detailed", str(SCHEMA), str(path)],
        cwd=ROOT, text=True, capture_output=True, check=False, timeout=15,
    )


def errors(node):
    yield node
    for child in node.get("errors", []):
        yield from errors(child)


def assert_extra_field_rejected(
    tmp_path: Path, schema_pointer: str, instance_path: tuple, field: str,
    value: str,
) -> None:
    document = synthetic_profile()
    control = validate(tmp_path, document)
    assert control.returncode == 0, control.stdout + control.stderr
    target = document
    for part in instance_path:
        target = target[part]
    assert field not in target
    target[field] = value
    result = validate(tmp_path, document)
    assert result.returncode == 1, result.stdout + result.stderr
    # jv prefixes its JSON diagnostics with schema/instance status lines.
    output = result.stdout + result.stderr
    diagnostic = json.loads(output[output.index("{"):])
    assert diagnostic["valid"] is False
    location = "".join(f"/{part}" for part in instance_path)
    matches = [
        error for error in errors(diagnostic)
        if error.get("instanceLocation") == location
        and (
            error["AbsoluteKeywordLocation"].split("#", 1)[1]
            if "AbsoluteKeywordLocation" in error else error["keywordLocation"]
        ) == f"{schema_pointer}/additionalProperties"
    ]
    assert len(matches) == 1, output
    assert matches[0]["valid"] is False
    assert field in matches[0]["error"], output
    del target[field]
    restored = validate(tmp_path, document)
    assert restored.returncode == 0, restored.stdout + restored.stderr


@pytest.mark.parametrize("schema_pointer,instance_path", CLOSED_OBJECTS)
def test_description_closed_objects_reject_private_field(
    tmp_path: Path, schema_pointer: str, instance_path: tuple,
) -> None:
    assert_extra_field_rejected(
        tmp_path, schema_pointer, instance_path,
        "synthetic_private_field", "synthetic sentinel",
    )


@pytest.mark.parametrize("record_index", [0, 1], ids=["local", "remote"])
def test_native_record_rejects_application_validation_scope(
    tmp_path: Path, record_index: int,
) -> None:
    assert_extra_field_rejected(
        tmp_path, "/$defs/record", ("records", record_index),
        "validation_scope", "raw_evidence_only",
    )
