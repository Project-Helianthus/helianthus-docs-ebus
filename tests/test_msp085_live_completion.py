from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE = ROOT / "docs/platform/live/msp-085-0.6.38"
M8_EVIDENCE = LIVE / "m8-evidence.json"
M8_REPORT = LIVE / "m8-report.json"
M85_RESULT = LIVE / "m8.5-result.json"
M8_REGISTRY = ROOT / "docs/platform/schemas/multi-runtime-coexistence-registry-v1.json"
M85_REGISTRY = (
    ROOT / "docs/platform/schemas/leaf-promotion-captured-multi-leaf-registry-v1.json"
)
M7_ROOT = ROOT / "docs/platform/fixtures/candidate-fact-graph/v1/positive"
M7_REGISTRY = ROOT / "docs/platform/schemas/draft-candidate-fact-registry-v1.json"
M8_VALIDATOR = ROOT / "scripts/validate_multi_runtime_coexistence.py"


def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_m8_public(evidence: pathlib.Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(M8_VALIDATOR),
            "verify-public",
            "--evidence",
            str(evidence),
            "--registry",
            str(M8_REGISTRY),
            "--m7-registry",
            str(M7_REGISTRY),
            "--m7-terminal-graph",
            str(M7_ROOT / "source-terminal-graph.json"),
            "--m7-terminal-replay",
            str(M7_ROOT / "source-terminal-replay-result.json"),
            "--m7-terminal-source-bundle",
            str(M7_ROOT / "source-terminal-bundle.json"),
            "--m7-terminal-source-replay",
            str(M7_ROOT / "source-terminal-source-replay.json"),
            "--m7-live-status",
            str(M7_ROOT / "live-public-status.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def refresh_public_evidence(validator, evidence: dict[str, object]) -> None:
    registry = load(M8_REGISTRY)
    rules = {rule["view_id"]: rule for rule in registry["view_rules"]}
    for run in evidence["runs"]:
        inputs = {
            item["input_id"]: item for item in run["provenance"]["immutable_inputs"]
        }
        for view in run["protected_views"]:
            normalized = validator.normalized_payload(
                view["payload"], rules[view["view_id"]], evidence["normalization"]
            )
            view["raw_payload_hash"] = validator.digest(
                validator.RAW_PAYLOAD_DOMAIN, view["payload"]
            )
            view["shape_hash"] = validator.digest(
                validator.SHAPE_DOMAIN, validator.payload_shape(view["payload"])
            )
            view["canonical_payload_hash"] = validator.digest(
                validator.CANONICAL_PAYLOAD_DOMAIN, normalized
            )
            immutable = inputs["view:" + view["view_id"]]
            immutable["digest"] = view["raw_payload_hash"]
            immutable["byte_length"] = len(validator.canonical(view["payload"]))
    evidence_view = {
        key: value
        for key, value in evidence.items()
        if key not in {"evidence_id", "evidence_hash"}
    }
    evidence_hash = validator.digest(validator.EVIDENCE_DOMAIN, evidence_view)
    evidence["evidence_hash"] = evidence_hash
    evidence["evidence_id"] = "mrcv1:" + evidence_hash


def test_live_publication_exact_bytes_and_m8_report() -> None:
    assert sha256(M8_EVIDENCE) == (
        "9959206059a091a3805ab87e6dab6db753672c4fe03b453496260be2fb02b7c5"
    )
    assert sha256(M8_REPORT) == (
        "f211ab24f3718af21d6f414385f1554dacf654b610fb4f5b7695d57b0743424d"
    )
    assert sha256(M85_RESULT) == (
        "a0b41745f675e234f11729b2730bd640f04b673d4b8c97e3d0b56cc74ddb5b1e"
    )

    validator = load_module(
        "msp085_live_m8_validator",
        ROOT / "scripts/validate_multi_runtime_coexistence.py",
    )
    evidence = load(M8_EVIDENCE)
    report = load(M8_REPORT)
    registry = load(M8_REGISTRY)
    validator.schema_check(evidence)
    validator.check_limits(evidence, len(M8_EVIDENCE.read_bytes()))
    validator.check_public_redaction(evidence)
    verified = verify_m8_public(M8_EVIDENCE)
    assert (verified.returncode, verified.stdout, verified.stderr) == (
        0,
        "public-only-ok\n",
        "",
    )
    assert validator.report(copy.deepcopy(evidence), registry) == report
    assert report["verdict"] == "PASS"


def test_live_m8_canonical_verifier_rejects_evidence_hash_mutation(
    tmp_path: pathlib.Path,
) -> None:
    evidence = load(M8_EVIDENCE)
    evidence["evidence_hash"] = "sha256:" + "0" * 64
    mutated = tmp_path / "mutated-evidence.json"
    mutated.write_text(json.dumps(evidence, separators=(",", ":")), encoding="utf-8")

    verified = verify_m8_public(mutated)
    assert verified.returncode == 1
    assert verified.stdout == "hash.evidence\n"
    assert verified.stderr == ""


@pytest.mark.parametrize(
    ("target", "admission_alias"),
    [
        ("device_address", None),
        ("admission_alias", "selected-source"),
        ("admission_alias", "lastSuccessfulSource"),
        ("admission_alias", "companion target"),
        ("via_device", None),
    ],
)
def test_live_m8_canonical_verifier_rejects_enumerable_address_hashes(
    tmp_path: pathlib.Path,
    target: str,
    admission_alias: str | None,
) -> None:
    validator = load_module(
        "msp085_live_address_validator",
        ROOT / "scripts/validate_multi_runtime_coexistence.py",
    )
    evidence = load(M8_EVIDENCE)
    enumerable = "redacted:sha256:0123456789ab"
    for run in evidence["runs"]:
        views = {view["view_id"]: view for view in run["protected_views"]}
        devices = views["mcp.ebus.v1.responses"]["payload"]["data"]["responses"][0][
            "result"
        ]["devices"]
        if target == "device_address":
            devices[0]["address"] = enumerable
        admission = views["debug.ebus"]["payload"]["data"]["status"]["admission"]
        if admission_alias is not None:
            admission[admission_alias] = enumerable
        if target == "via_device":
            views["ha.identity"]["payload"]["data"]["devices"][0][
                "via_device"
            ] = enumerable
    refresh_public_evidence(validator, evidence)

    mutated = tmp_path / "enumerable-address-evidence.json"
    mutated.write_bytes(validator.canonical(evidence) + b"\n")
    verified = verify_m8_public(mutated)
    assert verified.returncode == 1
    assert verified.stdout == "redaction.public\n"
    assert verified.stderr == ""


@pytest.mark.parametrize(
    "target",
    [
        "auth_subject",
        "auth_subject_address_hash",
        "uncontracted_mcp_address",
        "uncontracted_mcp_address_value_hash",
        "uncontracted_mcp_address_hash_alias",
        "uncontracted_mcp_address_digest_alias",
        "uncontracted_debug_alias",
    ],
)
def test_live_m8_canonical_verifier_rejects_opaque_address_outside_canonical_paths(
    tmp_path: pathlib.Path, target: str,
) -> None:
    validator = load_module(
        "msp085_live_opaque_scope_validator",
        ROOT / "scripts/validate_multi_runtime_coexistence.py",
    )
    evidence = load(M8_EVIDENCE)
    for run in evidence["runs"]:
        views = {view["view_id"]: view for view in run["protected_views"]}
        if target in {"auth_subject", "auth_subject_address_hash"}:
            for view in views.values():
                view["payload"]["meta"]["auth_subject"] = (
                    validator.OPAQUE_ADDRESS
                    if target == "auth_subject"
                    else validator._source_redacted("ebus-address:127")
                )
        elif target in {
            "uncontracted_mcp_address",
            "uncontracted_mcp_address_value_hash",
            "uncontracted_mcp_address_hash_alias",
            "uncontracted_mcp_address_digest_alias",
        }:
            if target == "uncontracted_mcp_address_hash_alias":
                key, value = "address_hash", "sha256:" + "a" * 64
            elif target == "uncontracted_mcp_address_digest_alias":
                key, value = "address_digest", "sha256:" + "b" * 64
            else:
                key = "address"
                value = (
                    validator.OPAQUE_ADDRESS
                    if target == "uncontracted_mcp_address"
                    else validator._source_redacted("ebus-address:127")
                )
            views["mcp.ebus.v1.responses"]["payload"]["data"]["uncontracted"] = {
                key: value
            }
        else:
            views["debug.ebus"]["payload"]["data"]["uncontracted"] = {
                "selected_source": validator.OPAQUE_ADDRESS
            }
    refresh_public_evidence(validator, evidence)

    mutated = tmp_path / "misplaced-opaque-address-evidence.json"
    mutated.write_bytes(validator.canonical(evidence) + b"\n")
    verified = verify_m8_public(mutated)
    assert verified.returncode == 1
    assert verified.stdout == "redaction.public\n"
    assert verified.stderr == ""


@pytest.mark.parametrize(
    "mutation", ["reordered", "missing", "null", "wrong_operation", "extra"]
)
def test_live_m8_verifier_rejects_malformed_response_array_without_traceback(
    tmp_path: pathlib.Path, mutation: str,
) -> None:
    validator = load_module(
        "msp085_live_response_shape_validator",
        ROOT / "scripts/validate_multi_runtime_coexistence.py",
    )
    evidence = load(M8_EVIDENCE)
    for run in evidence["runs"]:
        view = next(
            view
            for view in run["protected_views"]
            if view["view_id"] == "mcp.ebus.v1.responses"
        )
        responses = view["payload"]["data"]["responses"]
        if mutation == "reordered":
            responses.reverse()
        elif mutation == "missing":
            responses.pop()
        elif mutation == "null":
            responses[1] = None
        elif mutation == "wrong_operation":
            responses[1]["operation"] = "ebus.v1.semantic.snapshot.list"
        else:
            responses.append({"operation": "ebus.v1.extra", "result": {}})
    refresh_public_evidence(validator, evidence)

    mutated = tmp_path / "reordered-mcp-responses.json"
    mutated.write_bytes(validator.canonical(evidence) + b"\n")
    verified = verify_m8_public(mutated)
    assert verified.returncode == 1
    assert verified.stdout == "redaction.public\n"
    assert verified.stderr == ""


@pytest.mark.parametrize(
    "mutation",
    [
        "missing_selection",
        "count_mismatch",
        "empty_inventory",
        "empty_semantic",
        "extra_device_result_member",
        "extra_semantic_member",
    ],
)
def test_live_m8_verifier_rejects_noncanonical_response_results(
    tmp_path: pathlib.Path, mutation: str,
) -> None:
    validator = load_module(
        "msp085_live_result_shape_validator",
        ROOT / "scripts/validate_multi_runtime_coexistence.py",
    )
    evidence = load(M8_EVIDENCE)
    for run in evidence["runs"]:
        views = {view["view_id"]: view for view in run["protected_views"]}
        responses = views["mcp.ebus.v1.responses"]["payload"]["data"]["responses"]
        device_result = responses[0]["result"]
        semantic_result = responses[1]["result"]
        if mutation == "missing_selection":
            device_result.pop("selection")
        elif mutation == "count_mismatch":
            device_result["selection"]["selected_count"] += 1
        elif mutation == "empty_inventory":
            device_result["devices"] = []
            views["ha.identity"]["payload"]["data"]["devices"] = []
        elif mutation == "empty_semantic":
            responses[1]["result"] = {}
        elif mutation == "extra_device_result_member":
            device_result["uncontracted"] = None
        else:
            semantic_result["uncontracted"] = None
    refresh_public_evidence(validator, evidence)

    mutated = tmp_path / "noncanonical-mcp-result.json"
    mutated.write_bytes(validator.canonical(evidence) + b"\n")
    verified = verify_m8_public(mutated)
    assert verified.returncode == 1
    assert verified.stdout == "redaction.public\n"
    assert verified.stderr == ""


@pytest.mark.parametrize(
    "mutation", ["missing_alias", "empty_admission", "missing_admission"]
)
def test_live_m8_verifier_requires_canonical_debug_admission_aliases(
    tmp_path: pathlib.Path, mutation: str,
) -> None:
    validator = load_module(
        "msp085_live_admission_shape_validator",
        ROOT / "scripts/validate_multi_runtime_coexistence.py",
    )
    evidence = load(M8_EVIDENCE)
    for run in evidence["runs"]:
        view = next(
            view
            for view in run["protected_views"]
            if view["view_id"] == "debug.ebus"
        )
        status = view["payload"]["data"]["status"]
        if mutation == "missing_alias":
            status["admission"].pop("selected_source")
        elif mutation == "empty_admission":
            status["admission"] = {}
        else:
            status.pop("admission")
    refresh_public_evidence(validator, evidence)

    mutated = tmp_path / "noncanonical-debug-admission.json"
    mutated.write_bytes(validator.canonical(evidence) + b"\n")
    verified = verify_m8_public(mutated)
    assert verified.returncode == 1
    assert verified.stdout == "redaction.public\n"
    assert verified.stderr == ""


@pytest.mark.parametrize("discovery_source", ["passive_observed", "static_seed"])
def test_live_m8_verifier_accepts_confirmed_devices_from_supported_discovery_sources(
    tmp_path: pathlib.Path, discovery_source: str,
) -> None:
    validator = load_module(
        "msp085_live_discovery_source_validator",
        ROOT / "scripts/validate_multi_runtime_coexistence.py",
    )
    evidence = load(M8_EVIDENCE)
    for run in evidence["runs"]:
        view = next(
            view
            for view in run["protected_views"]
            if view["view_id"] == "mcp.ebus.v1.responses"
        )
        view["payload"]["data"]["responses"][0]["result"]["devices"][0][
            "discovery_source"
        ] = discovery_source
    refresh_public_evidence(validator, evidence)

    mutated = tmp_path / "supported-discovery-source.json"
    mutated.write_bytes(validator.canonical(evidence) + b"\n")
    verified = verify_m8_public(mutated)
    assert verified.returncode == 0
    assert verified.stdout == "public-only-ok\n"
    assert verified.stderr == ""


def test_live_m8_canonical_verifier_rejects_duplicate_public_device_identity(
    tmp_path: pathlib.Path,
) -> None:
    validator = load_module(
        "msp085_live_duplicate_identity_validator",
        ROOT / "scripts/validate_multi_runtime_coexistence.py",
    )
    evidence = load(M8_EVIDENCE)
    for run in evidence["runs"]:
        views = {view["view_id"]: view for view in run["protected_views"]}
        devices = views["mcp.ebus.v1.responses"]["payload"]["data"]["responses"][0][
            "result"
        ]["devices"]
        ha_devices = views["ha.identity"]["payload"]["data"]["devices"]
        devices[1]["device_id"] = devices[0]["device_id"]
        ha_devices[1]["unique_id"] = ha_devices[0]["unique_id"]
        ha_devices[1]["via_device"] = ha_devices[0]["via_device"]
    refresh_public_evidence(validator, evidence)

    mutated = tmp_path / "duplicate-public-device-evidence.json"
    mutated.write_bytes(validator.canonical(evidence) + b"\n")
    verified = verify_m8_public(mutated)
    assert verified.returncode == 1
    assert verified.stdout == "redaction.public\n"
    assert verified.stderr == ""


def test_live_m8_canonical_verifier_rejects_address_derived_device_identities(
    tmp_path: pathlib.Path,
) -> None:
    validator = load_module(
        "msp085_live_address_identity_validator",
        ROOT / "scripts/validate_multi_runtime_coexistence.py",
    )
    evidence = load(M8_EVIDENCE)
    for run in evidence["runs"]:
        views = {view["view_id"]: view for view in run["protected_views"]}
        devices = views["mcp.ebus.v1.responses"]["payload"]["data"]["responses"][0][
            "result"
        ]["devices"]
        ha_devices = views["ha.identity"]["payload"]["data"]["devices"]
        for index, (device, ha_device) in enumerate(
            zip(devices, ha_devices, strict=True)
        ):
            device_id = validator._source_redacted(f"ebus-address:{index}")
            device["device_id"] = device_id
            ha_device["unique_id"] = validator._source_redacted("ha:" + device_id)
            ha_device["via_device"] = validator._source_redacted(
                "ha-via:" + device_id
            )
    refresh_public_evidence(validator, evidence)

    mutated = tmp_path / "address-derived-device-identities.json"
    mutated.write_bytes(validator.canonical(evidence) + b"\n")
    verified = verify_m8_public(mutated)
    assert verified.returncode == 1
    assert verified.stdout == "redaction.public\n"
    assert verified.stderr == ""


def test_live_m8_canonical_verifier_rejects_address_derived_model_aliases(
    tmp_path: pathlib.Path,
) -> None:
    validator = load_module(
        "msp085_live_address_model_validator",
        ROOT / "scripts/validate_multi_runtime_coexistence.py",
    )
    evidence = load(M8_EVIDENCE)
    for run in evidence["runs"]:
        views = {view["view_id"]: view for view in run["protected_views"]}
        devices = views["mcp.ebus.v1.responses"]["payload"]["data"]["responses"][0][
            "result"
        ]["devices"]
        ha_devices = views["ha.identity"]["payload"]["data"]["devices"]
        for index, (device, ha_device) in enumerate(
            zip(devices, ha_devices, strict=True)
        ):
            model = validator._source_redacted(f"ebus-address:{index}")
            device["model"] = model
            ha_device["model"] = model
    refresh_public_evidence(validator, evidence)

    mutated = tmp_path / "address-derived-model-aliases.json"
    mutated.write_bytes(validator.canonical(evidence) + b"\n")
    verified = verify_m8_public(mutated)
    assert verified.returncode == 1
    assert verified.stdout == "redaction.public\n"
    assert verified.stderr == ""


def test_live_publication_has_eight_locked_candidates_and_no_public_leak() -> None:
    validator = load_module(
        "msp085_live_m85_validator",
        ROOT / "scripts/validate_captured_multi_leaf_promotion.py",
    )
    result = load(M85_RESULT)
    validator._verify_public_structure(result, load(M85_REGISTRY))

    promoted = [
        item for item in result["candidate_results"] if item["decision"] == "PROMOTED"
    ]
    assert result["counts"] == {"total": 18, "promoted": 8, "withheld": 10}
    assert result["verdict"] == "VALID_PROMOTION_LOCK"
    assert result["m9_consumer_gate"] == "READY_FOR_M9_PLANNING"
    assert all(item["visibility"] == "LOCKED_NOT_EXPOSED" for item in promoted)
    assert [item["candidate_id"] for item in promoted] == [
        "m7-candidate-0007",
        "m7-candidate-0009",
        "m7-candidate-0010",
        "m7-candidate-0011",
        "m7-candidate-0014",
        "m7-candidate-0015",
        "m7-candidate-0016",
        "m7-candidate-0018",
    ]

    published = b"\n".join(
        path.read_bytes() for path in (M8_EVIDENCE, M8_REPORT, M85_RESULT)
    ).lower()
    for forbidden in (
        b"candidate_ref",
        b"private_key",
        b"private key",
        b"begin private",
        b"trust_store",
        b"remote_ski",
        b"local_ski",
        b"ship_id",
    ):
        assert forbidden not in published
