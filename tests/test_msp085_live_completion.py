from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
LIVE = ROOT / "docs/platform/live/msp-085-0.6.38"
M8_EVIDENCE = LIVE / "m8-evidence.json"
M8_REPORT = LIVE / "m8-report.json"
M85_RESULT = LIVE / "m8.5-result.json"
M8_REGISTRY = ROOT / "docs/platform/schemas/multi-runtime-coexistence-registry-v1.json"
M85_REGISTRY = (
    ROOT / "docs/platform/schemas/leaf-promotion-captured-multi-leaf-registry-v1.json"
)


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


def test_live_publication_exact_bytes_and_m8_report() -> None:
    assert sha256(M8_EVIDENCE) == (
        "1b898a5d1fa836576190cc83e82ebe01abdd54705f93dd25e95b3e594cfffd14"
    )
    assert sha256(M8_REPORT) == (
        "81dcdcffab5a4d7ddb9f784c6bc55a996ab4bf2bb5c3806b936351e96ee8a111"
    )
    assert sha256(M85_RESULT) == (
        "cdfd6522e482ba083a5f3c964f95e953ea94e3d829321904be507952c767f460"
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
    assert validator.report(copy.deepcopy(evidence), registry) == report
    assert report["verdict"] == "PASS"


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
