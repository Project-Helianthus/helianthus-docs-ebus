from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
import subprocess
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


def test_live_publication_exact_bytes_and_m8_report() -> None:
    assert sha256(M8_EVIDENCE) == (
        "a55a17eb24b965debf218dcb8e4d2b49d5bdde284aa642bea729c35d8acac789"
    )
    assert sha256(M8_REPORT) == (
        "5266db89e4086e61b88d0242233bdffe7a05422efdacfeca4fb04e3239cc6457"
    )
    assert sha256(M85_RESULT) == (
        "98c5b9a6dc176b64a7e56baeec31ba869ff4c24498804e79cd86678bd74c4f7e"
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
