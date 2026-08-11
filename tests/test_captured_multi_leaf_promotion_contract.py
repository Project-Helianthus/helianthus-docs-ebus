from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import pathlib
import subprocess
import sys

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs/platform/captured-multi-leaf-promotion-v1.md"
README = ROOT / "docs/platform/README.md"
SCHEMA_ROOT = ROOT / "docs/platform/schemas"
PRIVATE_SCHEMA = SCHEMA_ROOT / "leaf-promotion-captured-multi-leaf-v1.schema.json"
PUBLIC_SCHEMA = SCHEMA_ROOT / "leaf-promotion-captured-multi-leaf-result-v1.schema.json"
REGISTRY = SCHEMA_ROOT / "leaf-promotion-captured-multi-leaf-registry-v1.json"
FIXTURE = ROOT / "docs/platform/fixtures/leaf-promotion-captured-multi-leaf/v1"
PRIVATE = FIXTURE / "positive/private-campaign.json"
PUBLIC = FIXTURE / "positive/public-result.json"
NEGATIVE = FIXTURE / "negative"
VALIDATOR = ROOT / "scripts/validate_captured_multi_leaf_promotion.py"
GENERATOR = ROOT / "scripts/generate_captured_multi_leaf_promotion_fixture.py"
M7_FIXTURE = ROOT / "docs/platform/fixtures/candidate-fact-graph/v1/positive"
M7_REGISTRY = ROOT / "docs/platform/schemas/draft-candidate-fact-registry-v1.json"
M7_SOURCE_BUNDLE = ROOT / "docs/platform/fixtures/synchronized-evidence/v1/positive/bundle.json"
M7_SOURCE_REPLAY = ROOT / "docs/platform/fixtures/synchronized-evidence/v1/positive/replay-result.json"
M7_TERMINAL_GRAPH = M7_FIXTURE / "source-terminal-graph.json"
M7_TERMINAL_REPLAY = M7_FIXTURE / "source-terminal-replay-result.json"
M7_TERMINAL_SOURCE_BUNDLE = M7_FIXTURE / "source-terminal-bundle.json"
M7_TERMINAL_SOURCE_REPLAY = M7_FIXTURE / "source-terminal-source-replay.json"
M8_LIVE_TEST = ROOT / "tests/test_multi_runtime_live_coexistence_contract.py"
REGISTRY_SHA256 = "d17a66da1919796f57ecd2a515fa4e538c6be8d00a24c8c7e5d38bce7f36e3cd"


EXPECTED_NEGATIVE = {
    "granularity-substitution.json": ("GRANULARITY_SUBSTITUTION", "comparator.invalid"),
    "missing-granularity.json": ("MISSING_GRANULARITY", "schema.private"),
    "identity-mismatch.json": ("IDENTITY_MISMATCH", "identity.binding"),
    "generation-change.json": ("GENERATION_CHANGE", "sample.invalid"),
    "skew-exceeded.json": ("SKEW_EXCEEDED", "sample.invalid"),
    "stale-sample.json": ("STALE_SAMPLE", "sample.invalid"),
    "missing-sample.json": ("MISSING_SAMPLE", "identity.binding"),
    "conflict-as-match.json": ("CONFLICT_AS_MATCH", "state.invalid"),
    "replay-drift.json": ("REPLAY_DRIFT", "hash.replay"),
    "public-identity-leak.json": ("PUBLIC_IDENTITY_LEAK", "schema.public"),
    "public-secret-leak.json": ("PUBLIC_SECRET_LEAK", "schema.public"),
}


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def module():
    spec = importlib.util.spec_from_file_location("multi_leaf_validator_test", VALIDATOR)
    assert spec is not None and spec.loader is not None
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def write(path: pathlib.Path, value: object) -> pathlib.Path:
    path.write_text(json.dumps(value, separators=(",", ":")), encoding="utf-8")
    return path


def run(
    command: str,
    path: pathlib.Path,
    *,
    private_campaign: pathlib.Path | None = None,
    registry: pathlib.Path = REGISTRY,
) -> subprocess.CompletedProcess[str]:
    args = [
        sys.executable,
        str(VALIDATOR),
        command,
        "--input",
        str(path),
        "--registry",
        str(registry),
    ]
    if private_campaign is not None:
        args.extend(("--private-campaign", str(private_campaign)))
    return subprocess.run(
        args,
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONHASHSEED": "random"},
    )


def candidate(campaign: dict, candidate_id: str) -> dict:
    return next(item for item in campaign["candidates"] if item["candidate_id"] == candidate_id)


def promoted(campaign: dict) -> dict:
    return next(item for item in campaign["candidates"] if item["decision"] == "PROMOTED")


def rehash_campaign(validator, campaign: dict) -> None:
    for leaf in campaign["candidates"]:
        if leaf["decision"] == "PROMOTED":
            leaf["dossier_hash"] = validator.digest(
                validator.DOSSIER_DOMAIN, validator._candidate_payload(leaf)
            )
    campaign["source_bindings"]["replay_hash"] = validator.replay_hash(campaign)
    campaign["campaign_hash"] = validator.digest(
        validator.CAMPAIGN_DOMAIN,
        {key: value for key, value in campaign.items() if key != "campaign_hash"},
    )


def rehash_public(validator, public: dict) -> None:
    public["result_hash"] = validator.digest(
        validator.RESULT_DOMAIN,
        {key: value for key, value in public.items() if key != "result_hash"},
    )


def full_binding_hash(redacted_id: str, fill: str) -> str:
    prefix = "redacted:sha256:"
    assert redacted_id.startswith(prefix) and len(redacted_id) == len(prefix) + 12
    return "sha256:" + redacted_id[len(prefix) :] + fill * 52


def rehash_ebus_identity(validator, identity: dict) -> None:
    identity["selector_hash"] = validator.digest(
        validator.EBUS_SELECTOR_DOMAIN,
        {key: value for key, value in identity.items() if key != "selector_hash"},
    )


def rehash_eebus_identity(validator, identity: dict) -> None:
    identity["identity_hash"] = validator.digest(
        validator.EEBUS_IDENTITY_DOMAIN,
        {key: value for key, value in identity.items() if key != "identity_hash"},
    )


def rehash_raw(validator, sample: dict) -> None:
    sample["raw_hash"] = validator.digest(validator.RAW_VALUE_DOMAIN, sample["raw_value"])


def live_campaign(validator) -> dict:
    campaign = load(PRIVATE)
    campaign["evidence_mode"] = "LIVE_CAPTURE"
    campaign["provenance"] = {
        "class": "LIVE_CAPTURE",
        "fixture_id": None,
        "generator": None,
        "capture_campaign_id": "live-campaign-test",
        "capture_receipts": ["sha256:" + "e" * 64, "sha256:" + "f" * 64],
        "deployment_source_commit": "1" * 40,
        "deployment_source_hash": "sha256:" + "8" * 64,
        "deployment_binary_hash": "sha256:" + "9" * 64,
    }
    rehash_campaign(validator, campaign)
    return campaign


def load_module(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def generated_m7_bundle(validator, tmp_path: pathlib.Path, registry: dict) -> tuple:
    graph = load(M7_FIXTURE / "graph.json")
    templates = {
        "CLOUD_ONLY": graph["facts"][0],
        "NOT_TESTED": graph["facts"][4],
        "RAW_ONLY": graph["facts"][1],
    }
    facts = []
    for expected in registry["candidate_catalog"]:
        template = (
            templates[expected["terminal_state"]]
            if expected["protocol_eligibility"] == "TERMINAL"
            else templates["RAW_ONLY"]
        )
        fact = copy.deepcopy(template)
        fact["candidate_id"] = expected["candidate_id"]
        fact["proposed_path"] = (
            "/candidates/generated/candidate_" + expected["candidate_id"][-4:]
        )
        fact["status"] = expected["source_status"]
        fact["terminal_negative_state"] = expected["terminal_state"]
        fact["fact_hash"] = "sha256:" + validator.candidate_schema.fact_hexdigest(
            fact
        )
        facts.append(fact)
    graph["facts"] = facts
    graph_hash = validator.candidate_schema.graph_hexdigest(graph)
    graph["graph_hash"] = "sha256:" + graph_hash
    graph["graph_id"] = "dcfgv1:sha256:" + graph_hash
    replay = validator.candidate_schema.replay(graph)
    status = validator.status_projector.project(
        graph,
        replay,
        "8bcba2107d10b149f984ac9546ea6427a9cda8a1",
        "35d2eba256a77b6575a2b45c07e73f054ff74ced",
    )
    graph_path = write(tmp_path / "m7-graph.json", graph)
    replay_path = write(tmp_path / "m7-replay.json", replay)
    status_path = tmp_path / "m7-status.json"
    status_path.write_bytes(validator.status_projector.render(status))
    return graph, replay, status, graph_path, replay_path, status_path


def generated_gateway_source(tmp_path: pathlib.Path) -> tuple[pathlib.Path, str, str, str]:
    source_tree = tmp_path / "gateway-source"
    (source_tree / "cmd/gateway").mkdir(parents=True)
    (source_tree / "go.mod").write_text(
        "module github.com/Project-Helianthus/helianthus-ebusgateway\n\ngo 1.22\n",
        encoding="utf-8",
    )
    (source_tree / "cmd/gateway/main.go").write_text(
        'package main\n\nimport "fmt"\n\nfunc main() { fmt.Println("gateway") }\n',
        encoding="utf-8",
    )
    commands = (
        ["git", "init", "-q"],
        [
            "git",
            "remote",
            "add",
            "origin",
            "https://github.com/Project-Helianthus/helianthus-ebusgateway.git",
        ],
        ["git", "add", "go.mod", "cmd/gateway/main.go"],
        [
            "git",
            "-c",
            "user.name=Helianthus Test",
            "-c",
            "user.email=test@helianthus.invalid",
            "commit",
            "-q",
            "-m",
            "test source",
        ],
    )
    for command in commands:
        subprocess.run(command, cwd=source_tree, check=True, capture_output=True)
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source_tree,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    go_version = subprocess.run(
        ["go", "version"], check=True, capture_output=True, text=True
    ).stdout.split()[2]
    goarch = subprocess.run(
        ["go", "env", "GOARCH"], check=True, capture_output=True, text=True
    ).stdout.strip()
    return source_tree, source_commit, go_version, f"linux/{goarch}"


def generated_live_bundle(validator, tmp_path: pathlib.Path) -> dict:
    registry = load(REGISTRY)
    graph, replay, status, graph_path, replay_path, status_path = generated_m7_bundle(
        validator, tmp_path, registry
    )
    for item, fact in zip(registry["candidate_catalog"], graph["facts"], strict=True):
        item["fact_hash"] = fact["fact_hash"]
    registry["m7_public_status"] = str(status_path)
    registry_path = write(tmp_path / "registry.json", registry)
    registry_hash = validator.bytes_digest(registry_path.read_bytes())

    live_test = load_module(M8_LIVE_TEST, "captured_multi_leaf_m8_live_test")
    evidence = live_test.build_live_evidence(validator.coexistence)
    status_raw = status_path.read_bytes()
    source_bundle_raw = M7_SOURCE_BUNDLE.read_bytes()
    source_replay_raw = M7_SOURCE_REPLAY.read_bytes()
    m7_registry_raw = M7_REGISTRY.read_bytes()
    m8_registry = load(
        ROOT / "docs/platform/schemas/multi-runtime-coexistence-registry-v1.json"
    )
    m8_registry["m7_live_binding"] = validator.coexistence._binding(
        graph,
        replay,
        m7_registry_raw,
        source_bundle_raw,
        source_replay_raw,
    )
    m8_registry["m7_live_private_inputs"] = {
        name: {
            "digest": validator.bytes_digest(raw),
            "byte_length": len(raw),
        }
        for name, raw in {
            "graph": graph_path.read_bytes(),
            "replay": replay_path.read_bytes(),
            "source_bundle": source_bundle_raw,
            "source_replay": source_replay_raw,
        }.items()
    }
    m8_registry["m7_live_status_binding"] = {
        "contract": status["contract"],
        "projection_id": status["projection_id"],
        "projection_hash": status["projection_hash"],
        "content_hash": validator.bytes_digest(status_raw),
        "source_graph_id": status["source_graph_id"],
        "source_graph_hash": status["source_graph_hash"],
        "source_replay_id": status["source_replay_id"],
        "source_replay_hash": status["source_replay_hash"],
    }
    m8_registry_path = write(tmp_path / "m8-registry.json", m8_registry)
    validator.M8_REGISTRY = m8_registry_path
    validator.coexistence.EXPECTED_REGISTRY_SHA256 = hashlib.sha256(
        m8_registry_path.read_bytes()
    ).hexdigest()
    evidence["registry"]["digest"] = validator.bytes_digest(
        m8_registry_path.read_bytes()
    )
    evidence["m7_binding"] = {
        "source_commit": status["source_commit"],
        "docs_source_commit": status["docs_source_commit"],
        **m8_registry["m7_live_binding"],
    }
    evidence["m7_live_status"] = {
        "contract": status["contract"],
        "projection_id": status["projection_id"],
        "projection_hash": status["projection_hash"],
        "content_hash": validator.bytes_digest(status_raw),
        "source_graph_id": graph["graph_id"],
        "source_graph_hash": graph["graph_hash"],
        "source_replay_id": replay["replay_id"],
        "source_replay_hash": replay["replay_hash"],
    }
    m7_inputs = {
        "m7:private-graph": (
            validator.bytes_digest(graph_path.read_bytes()),
            len(graph_path.read_bytes()),
        ),
        "m7:private-replay": (
            validator.bytes_digest(replay_path.read_bytes()),
            len(replay_path.read_bytes()),
        ),
        "m7:private-source-bundle": (
            validator.bytes_digest(source_bundle_raw),
            len(source_bundle_raw),
        ),
        "m7:private-source-replay": (
            validator.bytes_digest(source_replay_raw),
            len(source_replay_raw),
        ),
        "m7:status-projection": (
            validator.bytes_digest(status_raw),
            len(status_raw),
        ),
    }
    source_tree, source_commit, go_version, target = generated_gateway_source(tmp_path)
    binary_path = tmp_path / "gateway.bin"
    target_parts = target.split("/")
    subprocess.run(
        [
            "go",
            "build",
            "-trimpath",
            "-buildvcs=true",
            "-o",
            str(binary_path),
            "./cmd/gateway",
        ],
        cwd=source_tree,
        env={
            **os.environ,
            "CGO_ENABLED": "0",
            "GOOS": target_parts[0],
            "GOARCH": target_parts[1],
            "GOTOOLCHAIN": "local",
            "GOFLAGS": "-mod=readonly",
            "GOWORK": "off",
        },
        check=True,
        capture_output=True,
    )
    binary_hash = validator.bytes_digest(binary_path.read_bytes())
    for run_item in evidence["runs"]:
        inputs = {
            item["input_id"]: item
            for item in run_item["provenance"]["immutable_inputs"]
        }
        for input_id, (input_hash, byte_length) in m7_inputs.items():
            inputs[input_id].update(digest=input_hash, byte_length=byte_length)
        runtime = run_item["provenance"]["runtime"]
        runtime.update(
            source_commit=source_commit,
            source_parent_commit=status["source_commit"],
            artifact_digest=binary_hash,
            artifact_id="gateway:" + binary_hash,
            artifact_size_bytes=len(binary_path.read_bytes()),
        )
        runtime["build_manifest"].update(
            go_version=go_version,
            target=target,
            flags=["-trimpath", "CGO_ENABLED=0"],
        )
        runtime["build_manifest"]["build_mode"] = "REPRODUCIBLE_BUILD"
        runtime["build_manifest_hash"] = validator.coexistence.digest(
            validator.coexistence.BUILD_DOMAIN, runtime["build_manifest"]
        )
    live_test.refresh_evidence_hash(validator.coexistence, evidence)
    report = validator.coexistence.report(copy.deepcopy(evidence), m8_registry)
    evidence_path = write(tmp_path / "m8-evidence.json", evidence)
    report_path = write(tmp_path / "m8-report.json", report)

    campaign = live_campaign(validator)
    for leaf, expected in zip(
        campaign["candidates"], registry["candidate_catalog"], strict=True
    ):
        leaf["fact_hash"] = expected["fact_hash"]
        if leaf["ebus_identity"] is not None:
            leaf["ebus_identity"]["target_pseudonym"] = "target-" + "a" * 32
            rehash_ebus_identity(validator, leaf["ebus_identity"])
        if leaf["eebus_identity"] is not None:
            suffix = leaf["candidate_id"][-4:]
            leaf["eebus_identity"]["service_id"] = "service-live-" + suffix
            leaf["eebus_identity"]["device_address"] = "device-live-" + suffix
            rehash_eebus_identity(validator, leaf["eebus_identity"])
        for assessment in leaf["assessments"]:
            if assessment["ebus_sample"] is not None:
                assessment["observed_ebus_identity_hash"] = leaf["ebus_identity"][
                    "selector_hash"
                ]
            if assessment["eebus_sample"] is not None:
                assessment["observed_eebus_identity_hash"] = leaf["eebus_identity"][
                    "identity_hash"
                ]

    transition_run = next(
        item
        for item in evidence["runs"]
        if item["state"] == "EEBUS_RESTART_PERSISTED"
    )
    transition = transition_run["state_evidence"]["restart_transition"]
    leaf_process_ids = (
        "process-leaf-" + "a" * 27,
        "process-leaf-" + "b" * 27,
    )
    window_bindings = (
        (
            leaf_process_ids[0],
            full_binding_hash(
                transition["before_snapshot"]["trust_state_id"], "4"
            ),
            full_binding_hash(
                transition["before_snapshot"]["peer_binding_id"], "5"
            ),
        ),
        (
            leaf_process_ids[1],
            full_binding_hash(
                transition["after_snapshot"]["trust_state_id"], "4"
            ),
            full_binding_hash(
                transition["after_snapshot"]["peer_binding_id"], "5"
            ),
        ),
    )
    for window, (process_id, trust_hash, peer_hash) in zip(
        campaign["windows"], window_bindings, strict=True
    ):
        window["process_instance_hash"] = validator._process_instance_hash(process_id)
        window["trust_state_hash"] = trust_hash
        window["peer_binding_hash"] = peer_hash

    campaign["source_bindings"].update(
        registry_sha256=registry_hash,
        m7_graph_id=graph["graph_id"],
        m7_graph_hash=graph["graph_hash"],
        m7_graph_bytes_hash=validator.bytes_digest(graph_path.read_bytes()),
        m7_replay_id=replay["replay_id"],
        m7_replay_hash=replay["replay_hash"],
        m7_replay_bytes_hash=validator.bytes_digest(replay_path.read_bytes()),
        m7_status_id=status["projection_id"],
        m7_status_hash=status["projection_hash"],
        m7_status_bytes_hash=validator.bytes_digest(status_raw),
        m8_evidence_id=evidence["evidence_id"],
        m8_evidence_hash=evidence["evidence_hash"],
        m8_evidence_bytes_hash=validator.bytes_digest(evidence_path.read_bytes()),
        m8_report_id=report["report_id"],
        m8_report_hash=report["report_hash"],
        m8_report_bytes_hash=validator.bytes_digest(report_path.read_bytes()),
    )
    source_receipt = {
        "contract": "helianthus.platform.deployment-source-receipt.v1",
        "source_commit": source_commit,
        "binary_hash": binary_hash,
    }
    deployment_path = write(tmp_path / "deployment.json", source_receipt)
    campaign["provenance"].update(
        deployment_source_commit=source_commit,
        deployment_source_hash=validator.bytes_digest(deployment_path.read_bytes()),
        deployment_binary_hash=binary_hash,
    )
    m7_binding = {
        "graph_id": graph["graph_id"],
        "graph_hash": graph["graph_hash"],
        "replay_id": replay["replay_id"],
        "replay_hash": replay["replay_hash"],
        "status_id": status["projection_id"],
        "status_hash": status["projection_hash"],
        "source_commit": status["source_commit"],
        "docs_source_commit": status["docs_source_commit"],
    }
    m8_binding = {
        "evidence_id": evidence["evidence_id"],
        "evidence_hash": evidence["evidence_hash"],
        "report_id": report["report_id"],
        "report_hash": report["report_hash"],
    }
    deployment_binding = {"source_commit": source_commit, "binary_hash": binary_hash}
    receipt_paths = []
    for index, window in enumerate(campaign["windows"]):
        receipt = {
            "contract": "helianthus.platform.leaf-promotion-capture-receipt.v1",
            "capture_campaign_id": campaign["provenance"]["capture_campaign_id"],
            "window_id": window["window_id"],
            "phase": window["phase"],
            "capture_generation": window["capture_generation"],
            "process_instance_hash": window["process_instance_hash"],
            "local_identity_hash": window["local_identity_hash"],
            "trust_state_hash": window["trust_state_hash"],
            "peer_binding_hash": window["peer_binding_hash"],
            "admitted_source": window["admitted_source"],
            "window_evidence_hash": validator.digest(
                validator.WINDOW_EVIDENCE_DOMAIN, window
            ),
            "m7_binding": m7_binding,
            "m8_binding": m8_binding,
            "deployment_binding": deployment_binding,
            "captured_at": window["ended_at"],
            "restart_event": (
                {
                    "event_type": "HA_ADDON_RESTART_COMPLETED",
                    "event_id": "leaf-restart-event-test",
                    "outcome": "COMPLETED",
                    "completed_at": "2026-08-11T10:02:00Z",
                    "before_process_instance_hash": validator._process_instance_hash(
                        leaf_process_ids[0]
                    ),
                    "after_process_instance_hash": validator._process_instance_hash(
                        leaf_process_ids[1]
                    ),
                }
                if index == 1
                else None
            ),
        }
        receipt_paths.append(write(tmp_path / f"receipt-{index}.json", receipt))
    campaign["provenance"]["capture_receipts"] = [
        validator.bytes_digest(path.read_bytes()) for path in receipt_paths
    ]
    rehash_campaign(validator, campaign)
    campaign_path = write(tmp_path / "live-campaign.json", campaign)
    return {
        "registry": registry_path,
        "registry_hash": registry_hash,
        "campaign": campaign_path,
        "m7_graph": graph_path,
        "m7_replay": replay_path,
        "m7_status": status_path,
        "m7_registry": M7_REGISTRY,
        "m7_source_bundle": M7_SOURCE_BUNDLE,
        "m7_source_replay": M7_SOURCE_REPLAY,
        "m7_terminal_graph": M7_TERMINAL_GRAPH,
        "m7_terminal_replay": M7_TERMINAL_REPLAY,
        "m7_terminal_source_bundle": M7_TERMINAL_SOURCE_BUNDLE,
        "m7_terminal_source_replay": M7_TERMINAL_SOURCE_REPLAY,
        "m8_evidence": evidence_path,
        "m8_report": report_path,
        "m8_trust_state_hash": campaign["windows"][0]["trust_state_hash"],
        "m8_peer_binding_hash": campaign["windows"][0]["peer_binding_hash"],
        "receipts": receipt_paths,
        "deployment": deployment_path,
        "binary": binary_path,
        "source_tree": source_tree,
    }


def live_cli_args(bundle: dict) -> list[str]:
    args = [
        "--registry",
        str(bundle["registry"]),
        "--m7-graph",
        str(bundle["m7_graph"]),
        "--m7-status",
        str(bundle["m7_status"]),
        "--m7-replay",
        str(bundle["m7_replay"]),
        "--m7-registry",
        str(bundle["m7_registry"]),
        "--m7-source-bundle",
        str(bundle["m7_source_bundle"]),
        "--m7-source-replay",
        str(bundle["m7_source_replay"]),
        "--m7-terminal-graph",
        str(bundle["m7_terminal_graph"]),
        "--m7-terminal-replay",
        str(bundle["m7_terminal_replay"]),
        "--m7-terminal-source-bundle",
        str(bundle["m7_terminal_source_bundle"]),
        "--m7-terminal-source-replay",
        str(bundle["m7_terminal_source_replay"]),
        "--m8-evidence",
        str(bundle["m8_evidence"]),
        "--m8-report",
        str(bundle["m8_report"]),
        "--m8-trust-state-hash",
        bundle["m8_trust_state_hash"],
        "--m8-peer-binding-hash",
        bundle["m8_peer_binding_hash"],
        "--deployment-source",
        str(bundle["deployment"]),
        "--deployment-binary",
        str(bundle["binary"]),
        "--deployment-source-tree",
        str(bundle["source_tree"]),
    ]
    for receipt in bundle["receipts"]:
        args.extend(("--capture-receipt", str(receipt)))
    return args


def live_sources(bundle: dict) -> dict:
    return {
        "m7_graph": bundle["m7_graph"],
        "m7_status": bundle["m7_status"],
        "m7_replay": bundle["m7_replay"],
        "m7_registry": bundle["m7_registry"],
        "m7_source_bundle": bundle["m7_source_bundle"],
        "m7_source_replay": bundle["m7_source_replay"],
        "m7_terminal_graph": bundle["m7_terminal_graph"],
        "m7_terminal_replay": bundle["m7_terminal_replay"],
        "m7_terminal_source_bundle": bundle["m7_terminal_source_bundle"],
        "m7_terminal_source_replay": bundle["m7_terminal_source_replay"],
        "m8_evidence": bundle["m8_evidence"],
        "m8_report": bundle["m8_report"],
        "m8_trust_state_hash": bundle["m8_trust_state_hash"],
        "m8_peer_binding_hash": bundle["m8_peer_binding_hash"],
        "capture_receipts": bundle["receipts"],
        "deployment_source": bundle["deployment"],
        "deployment_binary": bundle["binary"],
        "deployment_source_tree": bundle["source_tree"],
    }


def rebind_live_deployment(validator, bundle: dict) -> None:
    binary_hash = validator.bytes_digest(bundle["binary"].read_bytes())
    evidence = load(bundle["m8_evidence"])
    for run_item in evidence["runs"]:
        runtime = run_item["provenance"]["runtime"]
        runtime.update(
            artifact_digest=binary_hash,
            artifact_id="gateway:" + binary_hash,
            artifact_size_bytes=len(bundle["binary"].read_bytes()),
        )
    m8_live_test = load_module(M8_LIVE_TEST, "captured_multi_leaf_rebind_test")
    m8_live_test.refresh_evidence_hash(validator.coexistence, evidence)
    write(bundle["m8_evidence"], evidence)
    report = validator.coexistence.report(
        copy.deepcopy(evidence), load(validator.M8_REGISTRY)
    )
    write(bundle["m8_report"], report)

    deployment = load(bundle["deployment"])
    deployment["binary_hash"] = binary_hash
    write(bundle["deployment"], deployment)
    campaign = load(bundle["campaign"])
    campaign["source_bindings"].update(
        m8_evidence_id=evidence["evidence_id"],
        m8_evidence_hash=evidence["evidence_hash"],
        m8_evidence_bytes_hash=validator.bytes_digest(
            bundle["m8_evidence"].read_bytes()
        ),
        m8_report_id=report["report_id"],
        m8_report_hash=report["report_hash"],
        m8_report_bytes_hash=validator.bytes_digest(
            bundle["m8_report"].read_bytes()
        ),
    )
    campaign["provenance"].update(
        deployment_binary_hash=binary_hash,
        deployment_source_hash=validator.bytes_digest(
            bundle["deployment"].read_bytes()
        ),
    )
    for receipt_path in bundle["receipts"]:
        receipt = load(receipt_path)
        receipt["m8_binding"] = {
            "evidence_id": evidence["evidence_id"],
            "evidence_hash": evidence["evidence_hash"],
            "report_id": report["report_id"],
            "report_hash": report["report_hash"],
        }
        receipt["deployment_binding"]["binary_hash"] = binary_hash
        write(receipt_path, receipt)
    campaign["provenance"]["capture_receipts"] = [
        validator.bytes_digest(path.read_bytes()) for path in bundle["receipts"]
    ]
    rehash_campaign(validator, campaign)
    write(bundle["campaign"], campaign)


def promote_mapped_candidate(validator, campaign: dict, candidate_id: str) -> dict:
    registry = load(REGISTRY)
    expected = next(item for item in registry["candidate_catalog"] if item["candidate_id"] == candidate_id)
    leaf = candidate(campaign, candidate_id)
    templates = copy.deepcopy(candidate(campaign, "m7-candidate-0018")["assessments"])
    leaf.update(
        {
            "decision": "PROMOTED",
            "terminal_state": None,
            "visibility": "LOCKED_NOT_EXPOSED",
            "assessments": [],
        }
    )
    is_enum = expected["comparator_class"] == "ENUM_EXACT_MAPPING"
    for window, template in zip(campaign["windows"], templates, strict=True):
        assessment = copy.deepcopy(template)
        assessment["window_id"] = window["window_id"]
        if is_enum:
            ebus_raw = {"kind": "NUMERIC", "decimal": {"number": 0, "scale": 0}, "enum": None, "boolean": None}
            eebus_raw = {"kind": "NUMERIC", "decimal": {"number": 2, "scale": 0}, "enum": None, "boolean": None}
            decoded = {"kind": "ENUM", "decimal": None, "enum": "off", "boolean": None}
        else:
            ebus_raw = {"kind": "NUMERIC", "decimal": {"number": 0, "scale": 0}, "enum": None, "boolean": None}
            eebus_raw = {"kind": "BOOLEAN", "decimal": None, "enum": None, "boolean": False}
            decoded = {"kind": "BOOLEAN", "decimal": None, "enum": None, "boolean": False}
        assessment["ebus_sample"]["raw_value"] = ebus_raw
        assessment["eebus_sample"]["raw_value"] = eebus_raw
        for key in ("ebus_sample", "eebus_sample"):
            assessment[key]["value"] = copy.deepcopy(decoded)
            assessment[key]["unit"] = None
            rehash_raw(validator, assessment[key])
        assessment["comparator"] = {
            "class": expected["comparator_class"],
            "declared_spine_step": None,
            "delta": None,
            "conversion": None,
            "mapping_hash": validator.digest(
                validator.MAPPING_DOMAIN, expected["eebus_source"]["mapping_profile"]
            ),
            "outcome": "MATCH",
        }
        assessment["observed_ebus_identity_hash"] = leaf["ebus_identity"][
            "selector_hash"
        ]
        assessment["observed_eebus_identity_hash"] = leaf["eebus_identity"][
            "identity_hash"
        ]
        leaf["assessments"].append(assessment)
    return leaf


def test_inventory_and_normative_boundaries() -> None:
    for path in (PAGE, PRIVATE_SCHEMA, PUBLIC_SCHEMA, REGISTRY, PRIVATE, PUBLIC, VALIDATOR, GENERATOR):
        assert path.is_file()
    assert "captured-multi-leaf-promotion-v1.md" in README.read_text(encoding="utf-8")
    page = " ".join(PAGE.read_text(encoding="utf-8").split())
    for phrase in (
        "CAPTURED_RUNTIME_MULTI_LEAF_V1",
        "18 M7 VR940 facts",
        "11 protocol-comparable observations",
        "NUMERIC_DECLARED_GRANULARITY",
        "abs(convert(eBUS) - eeBUS) <= declared SPINE step",
        "PRE_RESTART",
        "POST_RESTART",
        "PRIVATE_OPERATOR",
        "PUBLIC_REDACTED",
        "SANITIZED_CONFORMANCE",
        "LIVE_CAPTURE",
        "private_campaign_bytes_hash",
        "registry_sha256",
        "--deployment-source-tree",
        "full 256-bit M8 trust-state and peer-binding hashes",
        "deterministic closed-bundle consistency",
        "do not authenticate that the operator performed a capture",
        "first non-`MATCH` outcome",
        "657a36d07e52570326384b757a5382a6789f641b",
    ):
        assert phrase in page


def test_registry_is_exact_and_contains_full_source_and_selector_profiles() -> None:
    validator = module()
    registry = load(REGISTRY)
    catalog = registry["candidate_catalog"]
    assert hashlib.sha256(REGISTRY.read_bytes()).hexdigest() == REGISTRY_SHA256
    assert validator.PINNED_REGISTRY_SHA256 == "sha256:" + REGISTRY_SHA256
    page = PAGE.read_text(encoding="utf-8")
    assert f"`{REGISTRY_SHA256}`" in page
    assert f"`registry_sha256=sha256:{REGISTRY_SHA256}`" in page
    assert [item["candidate_id"] for item in catalog] == [f"m7-candidate-{index:04d}" for index in range(1, 19)]
    assert sum(item["protocol_eligibility"] == "TERMINAL" for item in catalog) == 4
    assert sum(item["protocol_eligibility"] == "ELIGIBLE" for item in catalog) == 11
    assert sum(item["protocol_eligibility"] == "WITHHOLD_NO_EBUS_CAPABILITY_SOURCE" for item in catalog) == 3
    source_keys = {
        "entity_slot",
        "entity_type",
        "feature_type",
        "feature_role",
        "description_functions",
        "constraints_function",
        "value_functions",
        "field_path",
        "descriptor",
        "unit",
        "declared_constraints",
        "conversion",
        "exact_mapping",
        "mapping_profile",
    }
    active = [item for item in catalog if item["eebus_source"] is not None]
    assert len(active) == 14
    assert all(set(item["eebus_source"]) == source_keys for item in active)
    eligible = [item for item in catalog if item["protocol_eligibility"] == "ELIGIBLE"]
    assert all(item["ebus_selector"]["family"] == "B524" for item in eligible)
    assert all(item["ebus_selector"]["target_address"] == 0x15 for item in eligible)
    assert all(item["ebus_selector"] is None for item in catalog if item["protocol_eligibility"] != "ELIGIBLE")
    assert catalog[6]["eebus_source"]["description_functions"] == [
        "hvacSystemFunctionDescriptionListData",
        "hvacOperationModeDescriptionListData",
        "hvacSystemFunctionOperationModeRelationListData",
    ]
    assert catalog[8]["eebus_source"]["value_functions"] == [
        "hvacSystemFunctionListData",
        "hvacOverrunListData",
    ]
    assert catalog[-1]["eebus_source"]["descriptor"]["scope_type"] == "outsideAirTemperature"


def test_registry_argument_accepts_only_canonical_bytes(tmp_path: pathlib.Path) -> None:
    exact = tmp_path / "exact-registry.json"
    exact.write_bytes(REGISTRY.read_bytes())
    result = run("verify-private", PRIVATE, registry=exact)
    assert (result.returncode, result.stdout) == (0, "PASS\n")

    substituted = load(REGISTRY)
    substituted["capture_limits"]["max_skew_ns"] *= 2
    result = run("verify-private", PRIVATE, registry=write(tmp_path / "substitute.json", substituted))
    assert (result.returncode, result.stdout) == (1, "registry.binding\n")


def test_positive_subset_fixture_verifies_and_derives_byte_identically() -> None:
    private = run("verify-private", PRIVATE)
    assert (private.returncode, private.stdout, private.stderr) == (0, "PASS\n", "")
    derived = run("derive-public", PRIVATE)
    assert derived.returncode == 0 and derived.stderr == ""
    assert derived.stdout.encode("utf-8") == PUBLIC.read_bytes()
    public = run("verify-public", PUBLIC)
    assert (public.returncode, public.stdout, public.stderr) == (0, "PASS\n", "")
    bound = run("verify-public", PUBLIC, private_campaign=PRIVATE)
    assert (bound.returncode, bound.stdout, bound.stderr) == (0, "PASS\n", "")
    result = load(PUBLIC)
    assert result["source_bindings"]["private_campaign_bytes_hash"] == "sha256:" + hashlib.sha256(PRIVATE.read_bytes()).hexdigest()
    assert result["counts"] == {"total": 18, "promoted": 1, "withheld": 17}
    assert result["m9_consumer_gate"] == "BLOCKED_CONFORMANCE_ONLY"


def test_boolean_schema_version_aliases_are_rejected(tmp_path: pathlib.Path) -> None:
    private = load(PRIVATE)
    private["schema_version"] = True
    result = run("verify-private", write(tmp_path / "private-boolean-version.json", private))
    assert (result.returncode, result.stdout) == (1, "schema.private\n")

    public = load(PUBLIC)
    public["schema_version"] = True
    result = run("verify-public", write(tmp_path / "public-boolean-version.json", public))
    assert (result.returncode, result.stdout) == (1, "schema.public\n")


def test_relabelled_private_campaign_requires_external_live_source_bundle(
    tmp_path: pathlib.Path,
) -> None:
    validator = module()
    private_path = write(tmp_path / "live-private.json", live_campaign(validator))
    derived = run("derive-public", private_path)
    assert (derived.returncode, derived.stdout) == (1, "live.sources.required\n")
    verified = run("verify-private", private_path)
    assert (verified.returncode, verified.stdout) == (
        1,
        "live.sources.required\n",
    )


def test_live_cli_rejects_partial_source_bundle(tmp_path: pathlib.Path) -> None:
    validator = module()
    private_path = write(tmp_path / "live-private.json", live_campaign(validator))
    result = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "derive-public",
            "--input",
            str(private_path),
            "--registry",
            str(REGISTRY),
            "--m7-graph",
            str(PRIVATE),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert (result.returncode, result.stdout) == (1, "live.sources.required\n")


def test_generated_live_bundle_passes_public_cli_end_to_end(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    validator = module()
    bundle = generated_live_bundle(validator, tmp_path)
    monkeypatch.setattr(
        validator, "PINNED_REGISTRY_SHA256", bundle["registry_hash"]
    )
    args = live_cli_args(bundle)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(VALIDATOR),
            "derive-public",
            "--input",
            str(bundle["campaign"]),
            *args,
        ],
    )
    assert validator.main() == 0
    derived = capsys.readouterr()
    assert derived.err == ""
    public_path = tmp_path / "live-public.json"
    public_path.write_text(derived.out, encoding="utf-8")
    public = load(public_path)
    assert public["m9_consumer_gate"] == "READY_FOR_M9_PLANNING"

    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(VALIDATOR),
            "verify-public",
            "--input",
            str(public_path),
            "--private-campaign",
            str(bundle["campaign"]),
            *args,
        ],
    )
    assert validator.main() == 0
    verified = capsys.readouterr()
    assert (verified.out, verified.err) == ("PASS\n", "")


def test_live_cross_binding_rejects_component_splices(tmp_path: pathlib.Path) -> None:
    validator = module()
    bundle = generated_live_bundle(validator, tmp_path)
    campaign = load(bundle["campaign"])
    graph = load(bundle["m7_graph"])
    replay = load(bundle["m7_replay"])
    status = load(bundle["m7_status"])
    evidence = load(bundle["m8_evidence"])
    report = load(bundle["m8_report"])

    def validate(candidate_campaign=campaign, candidate_evidence=evidence) -> None:
        validator._validate_live_cross_bindings(
            candidate_campaign,
            graph,
            bundle["m7_graph"].read_bytes(),
            replay,
            bundle["m7_replay"].read_bytes(),
            status,
            bundle["m7_status"].read_bytes(),
            candidate_evidence,
            report,
        )

    validate()
    assert campaign["windows"][0]["process_instance_hash"] != validator._process_instance_hash(
        evidence["runs"][1]["provenance"]["process_instance_id"]
    )
    spliced_m7 = copy.deepcopy(evidence)
    spliced_m7["m7_binding"]["graph_id"] = "dcfgv1:spliced-run"
    with pytest.raises(validator.ValidationFailure) as raised:
        validate(candidate_evidence=spliced_m7)
    assert raised.value.category == "live.sources.binding"

    spliced_input = copy.deepcopy(evidence)
    item = next(
        value
        for value in spliced_input["runs"][1]["provenance"]["immutable_inputs"]
        if value["input_id"] == "m7:private-graph"
    )
    item["digest"] = "sha256:" + "f" * 64
    with pytest.raises(validator.ValidationFailure) as raised:
        validate(candidate_evidence=spliced_input)
    assert raised.value.category == "live.sources.binding"

    spliced_runtime = copy.deepcopy(evidence)
    spliced_runtime["runs"][1]["provenance"]["runtime"]["source_commit"] = "8" * 40
    with pytest.raises(validator.ValidationFailure) as raised:
        validate(candidate_evidence=spliced_runtime)
    assert raised.value.category == "live.deployment"

    synthetic_runtime = copy.deepcopy(evidence)
    for run_item in synthetic_runtime["runs"]:
        runtime = run_item["provenance"]["runtime"]
        runtime["build_manifest"]["build_mode"] = "SYNTHETIC_FIXTURE"
        runtime["build_manifest_hash"] = validator.coexistence.digest(
            validator.coexistence.BUILD_DOMAIN, runtime["build_manifest"]
        )
    with pytest.raises(validator.ValidationFailure) as raised:
        validate(candidate_evidence=synthetic_runtime)
    assert raised.value.category == "live.deployment"

    spliced_window = copy.deepcopy(campaign)
    spliced_window["windows"][1]["trust_state_hash"] = "sha256:" + "0" * 64
    with pytest.raises(validator.ValidationFailure) as raised:
        validate(candidate_campaign=spliced_window)
    assert raised.value.category == "live.restart.binding"

    malformed_window = copy.deepcopy(campaign)
    malformed_window["windows"][0]["peer_binding_hash"] = (
        "redacted:sha256:" + "5" * 12
    )
    with pytest.raises(validator.ValidationFailure) as raised:
        validate(candidate_campaign=malformed_window)
    assert raised.value.category == "live.restart.binding"


def test_full_live_verifier_rejects_synthetic_m8_baseline_only(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    validator = module()
    bundle = generated_live_bundle(validator, tmp_path)
    monkeypatch.setattr(
        validator, "PINNED_REGISTRY_SHA256", bundle["registry_hash"]
    )
    evidence = load(bundle["m8_evidence"])
    runtime = evidence["runs"][0]["provenance"]["runtime"]
    runtime["build_manifest"]["build_mode"] = "SYNTHETIC_FIXTURE"
    runtime["build_manifest_hash"] = validator.coexistence.digest(
        validator.coexistence.BUILD_DOMAIN, runtime["build_manifest"]
    )
    m8_live_test = load_module(M8_LIVE_TEST, "captured_multi_leaf_m8_mutation_test")
    m8_live_test.refresh_evidence_hash(validator.coexistence, evidence)
    write(bundle["m8_evidence"], evidence)
    campaign, _ = validator.load_json(bundle["campaign"])
    registry = validator.registry_value(bundle["registry"])
    with pytest.raises(validator.ValidationFailure) as raised:
        validator.verify_private(campaign, registry, live_sources(bundle))
    assert raised.value.category == "live.m8"


def test_full_live_verifier_rejects_forged_terminal_source_binding(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    validator = module()
    bundle = generated_live_bundle(validator, tmp_path)
    monkeypatch.setattr(
        validator, "PINNED_REGISTRY_SHA256", bundle["registry_hash"]
    )
    evidence = load(bundle["m8_evidence"])
    for run_item in evidence["runs"]:
        immutable = next(
            item
            for item in run_item["provenance"]["immutable_inputs"]
            if item["input_id"] == "m7:terminal-source-bundle"
        )
        immutable.update(digest="sha256:" + "0" * 64, byte_length=1)
    m8_live_test = load_module(M8_LIVE_TEST, "captured_multi_leaf_m8_m7_forgery_test")
    m8_live_test.refresh_evidence_hash(validator.coexistence, evidence)
    write(bundle["m8_evidence"], evidence)
    campaign, _ = validator.load_json(bundle["campaign"])
    registry = validator.registry_value(bundle["registry"])
    with pytest.raises(validator.ValidationFailure) as raised:
        validator.verify_private(campaign, registry, live_sources(bundle))
    assert raised.value.category == "live.m8"


def test_full_private_identity_binding_rejects_same_prefix_different_digest(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    validator = module()
    bundle = generated_live_bundle(validator, tmp_path)
    monkeypatch.setattr(
        validator, "PINNED_REGISTRY_SHA256", bundle["registry_hash"]
    )
    campaign = load(bundle["campaign"])
    for window in campaign["windows"]:
        replacement = "0" if window["trust_state_hash"][-1] != "0" else "1"
        window["trust_state_hash"] = window["trust_state_hash"][:-1] + replacement
    rehash_campaign(validator, campaign)
    write(bundle["campaign"], campaign)
    registry = validator.registry_value(bundle["registry"])
    with pytest.raises(validator.ValidationFailure) as raised:
        validator.verify_private(campaign, registry, live_sources(bundle))
    assert raised.value.category == "live.restart.binding"


def test_reproducible_build_rejects_coherently_relabelled_arbitrary_binary(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    validator = module()
    bundle = generated_live_bundle(validator, tmp_path)
    monkeypatch.setattr(
        validator, "PINNED_REGISTRY_SHA256", bundle["registry_hash"]
    )
    bundle["binary"].write_bytes(b"coherently-relabelled-arbitrary-binary")
    rebind_live_deployment(validator, bundle)

    campaign, _ = validator.load_json(bundle["campaign"])
    registry = validator.registry_value(bundle["registry"])
    with pytest.raises(validator.ValidationFailure) as raised:
        validator.verify_private(campaign, registry, live_sources(bundle))
    assert raised.value.category == "live.deployment"


def test_reproducible_build_rejects_ignored_source_input(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    validator = module()
    bundle = generated_live_bundle(validator, tmp_path)
    monkeypatch.setattr(
        validator, "PINNED_REGISTRY_SHA256", bundle["registry_hash"]
    )
    ignored_source = bundle["source_tree"] / "cmd/gateway/ignored.go"
    ignored_source.write_text(
        'package main\n\nimport "fmt"\n\nfunc init() { fmt.Print("ignored-input") }\n',
        encoding="utf-8",
    )
    (bundle["source_tree"] / ".git/info/exclude").write_text(
        "cmd/gateway/ignored.go\n", encoding="utf-8"
    )
    assert subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=bundle["source_tree"],
        check=True,
        capture_output=True,
    ).stdout == b""

    evidence = load(bundle["m8_evidence"])
    runtime = evidence["runs"][0]["provenance"]["runtime"]
    target = runtime["build_manifest"]["target"].split("/")
    environment = {
        **os.environ,
        "CGO_ENABLED": "0",
        "GOOS": target[0],
        "GOARCH": target[1],
        "GOTOOLCHAIN": "local",
        "GOFLAGS": "-mod=readonly",
        "GOWORK": "off",
    }
    if len(target) == 3:
        environment["GOARM"] = target[2].removeprefix("v")
    subprocess.run(
        [
            "go",
            "build",
            "-trimpath",
            "-buildvcs=true",
            "-o",
            str(bundle["binary"]),
            "./cmd/gateway",
        ],
        cwd=bundle["source_tree"],
        env=environment,
        check=True,
        capture_output=True,
    )
    rebind_live_deployment(validator, bundle)

    campaign, _ = validator.load_json(bundle["campaign"])
    registry = validator.registry_value(bundle["registry"])
    with pytest.raises(validator.ValidationFailure) as raised:
        validator.verify_private(campaign, registry, live_sources(bundle))
    assert raised.value.category == "live.deployment"


def test_reproducible_build_rejects_absolute_local_module_replacement(
    tmp_path: pathlib.Path,
) -> None:
    validator = module()
    source_tree, _, go_version, target_name = generated_gateway_source(tmp_path)
    ignored_module = source_tree / "ignored-module"
    ignored_module.mkdir()
    (ignored_module / "go.mod").write_text(
        "module example.invalid/ignored\n\ngo 1.22\n", encoding="utf-8"
    )
    (ignored_module / "ignored.go").write_text(
        'package ignored\n\nfunc Message() string { return "ignored-input" }\n',
        encoding="utf-8",
    )
    (source_tree / ".git/info/exclude").write_text(
        "ignored-module/\n", encoding="utf-8"
    )
    (source_tree / "go.mod").write_text(
        "module github.com/Project-Helianthus/helianthus-ebusgateway\n\n"
        "go 1.22\n\n"
        "require example.invalid/ignored v0.0.0\n\n"
        f"replace example.invalid/ignored => {ignored_module}\n",
        encoding="utf-8",
    )
    (source_tree / "cmd/gateway/main.go").write_text(
        'package main\n\nimport (\n\t"fmt"\n\t"example.invalid/ignored"\n)\n\n'
        "func main() { fmt.Println(ignored.Message()) }\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "go.mod", "cmd/gateway/main.go"],
        cwd=source_tree,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Helianthus Test",
            "-c",
            "user.email=test@helianthus.invalid",
            "commit",
            "-q",
            "-m",
            "add local replacement",
        ],
        cwd=source_tree,
        check=True,
        capture_output=True,
    )
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source_tree,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=source_tree,
        check=True,
        capture_output=True,
    ).stdout == b""

    binary = tmp_path / "local-replacement.bin"
    target = target_name.split("/")
    environment = {
        **os.environ,
        "CGO_ENABLED": "0",
        "GOOS": target[0],
        "GOARCH": target[1],
        "GOTOOLCHAIN": "local",
        "GOFLAGS": "-mod=readonly",
        "GOWORK": "off",
    }
    subprocess.run(
        [
            "go",
            "build",
            "-trimpath",
            "-buildvcs=true",
            "-o",
            str(binary),
            "./cmd/gateway",
        ],
        cwd=source_tree,
        env=environment,
        check=True,
        capture_output=True,
    )
    build_info = subprocess.run(
        ["go", "version", "-m", str(binary)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert "build\tvcs.modified=false" in build_info

    raw = binary.read_bytes()
    runtime = {
        "source_commit": source_commit,
        "artifact_digest": validator.bytes_digest(raw),
        "artifact_size_bytes": len(raw),
        "build_manifest": {
            "flags": ["-trimpath", "CGO_ENABLED=0"],
            "go_version": go_version,
            "target": target_name,
        },
    }
    with pytest.raises(validator.ValidationFailure) as raised:
        validator._validate_reproducible_build(source_tree, binary, runtime)
    assert raised.value.category == "live.deployment"


def test_reproducible_build_allows_versioned_module_replacement() -> None:
    validator = module()
    validator._reject_local_module_replacements(
        b'{"Replace":[{"New":{"Path":"example.invalid/new","Version":"v1.2.3"}}]}'
    )


def test_full_live_verifier_rejects_reused_m8_processes(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    validator = module()
    bundle = generated_live_bundle(validator, tmp_path)
    monkeypatch.setattr(
        validator, "PINNED_REGISTRY_SHA256", bundle["registry_hash"]
    )
    campaign = load(bundle["campaign"])
    evidence = load(bundle["m8_evidence"])
    transition = next(
        run["state_evidence"]["restart_transition"]
        for run in evidence["runs"]
        if run["state"] == "EEBUS_RESTART_PERSISTED"
    )
    for window, process_id in zip(
        campaign["windows"],
        (
            transition["before_process_instance_id"],
            transition["after_process_instance_id"],
        ),
        strict=True,
    ):
        window["process_instance_hash"] = validator._process_instance_hash(process_id)
    rehash_campaign(validator, campaign)
    write(bundle["campaign"], campaign)
    registry = validator.registry_value(bundle["registry"])
    with pytest.raises(validator.ValidationFailure) as raised:
        validator.verify_private(campaign, registry, live_sources(bundle))
    assert raised.value.category == "live.restart.binding"


def test_live_receipts_and_deployment_source_are_byte_bound(
    tmp_path: pathlib.Path,
) -> None:
    validator = module()
    campaign = live_campaign(validator)
    process_ids = ("process-" + "a" * 32, "process-" + "b" * 32)
    transition = {
        "event_id": "restart-event-live-test",
        "before_process_instance_id": process_ids[0],
        "after_process_instance_id": process_ids[1],
        "before_trust_state_hash": "sha256:" + "4" * 64,
        "after_trust_state_hash": "sha256:" + "4" * 64,
        "before_peer_binding_hash": "sha256:" + "5" * 64,
        "after_peer_binding_hash": "sha256:" + "5" * 64,
    }
    for index, window in enumerate(campaign["windows"]):
        window["process_instance_hash"] = validator._process_instance_hash(
            process_ids[index]
        )
        window["trust_state_hash"] = transition[
            "before_trust_state_hash" if index == 0 else "after_trust_state_hash"
        ]
        window["peer_binding_hash"] = transition[
            "before_peer_binding_hash" if index == 0 else "after_peer_binding_hash"
        ]
    binary_path = tmp_path / "gateway.bin"
    binary_path.write_bytes(b"captured-gateway-binary")
    binary_hash = validator.bytes_digest(binary_path.read_bytes())
    live_context = {
        "m7_binding": {"graph_id": "graph-live-test"},
        "m8_binding": {"evidence_id": "evidence-live-test"},
        "deployment_binding": {
            "source_commit": campaign["provenance"]["deployment_source_commit"],
            "binary_hash": binary_hash,
        },
        "runtime": {
            "source_commit": campaign["provenance"]["deployment_source_commit"],
            "artifact_digest": binary_hash,
            "artifact_size_bytes": len(binary_path.read_bytes()),
        },
        "transition": transition,
    }
    receipt_paths = []
    for index, window in enumerate(campaign["windows"]):
        receipt = {
            "contract": "helianthus.platform.leaf-promotion-capture-receipt.v1",
            "capture_campaign_id": campaign["provenance"]["capture_campaign_id"],
            "window_id": window["window_id"],
            "phase": window["phase"],
            "capture_generation": window["capture_generation"],
            "process_instance_hash": window["process_instance_hash"],
            "local_identity_hash": window["local_identity_hash"],
            "trust_state_hash": window["trust_state_hash"],
            "peer_binding_hash": window["peer_binding_hash"],
            "admitted_source": window["admitted_source"],
            "window_evidence_hash": validator.digest(
                validator.WINDOW_EVIDENCE_DOMAIN, window
            ),
            "m7_binding": live_context["m7_binding"],
            "m8_binding": live_context["m8_binding"],
            "deployment_binding": live_context["deployment_binding"],
            "captured_at": window["ended_at"],
            "restart_event": (
                {
                    "event_type": "HA_ADDON_RESTART_COMPLETED",
                    "event_id": transition["event_id"],
                    "outcome": "COMPLETED",
                    "completed_at": "2026-08-11T10:02:00Z",
                    "before_process_instance_hash": validator._process_instance_hash(
                        process_ids[0]
                    ),
                    "after_process_instance_hash": validator._process_instance_hash(
                        process_ids[1]
                    ),
                }
                if index == 1
                else None
            ),
        }
        path = write(tmp_path / f"{window['window_id']}.json", receipt)
        receipt_paths.append(path)
    campaign["provenance"]["capture_receipts"] = [
        validator.bytes_digest(path.read_bytes()) for path in receipt_paths
    ]
    validator._validate_capture_receipts(campaign, receipt_paths, live_context)

    post_receipt = load(receipt_paths[1])
    post_receipt["restart_event"]["completed_at"] = campaign["windows"][1][
        "started_at"
    ]
    write(receipt_paths[1], post_receipt)
    campaign["provenance"]["capture_receipts"][1] = validator.bytes_digest(
        receipt_paths[1].read_bytes()
    )
    with pytest.raises(validator.ValidationFailure) as raised:
        validator._validate_capture_receipts(campaign, receipt_paths, live_context)
    assert raised.value.category == "live.receipt"
    post_receipt["restart_event"]["completed_at"] = "2026-08-11T10:02:00Z"
    write(receipt_paths[1], post_receipt)
    campaign["provenance"]["capture_receipts"][1] = validator.bytes_digest(
        receipt_paths[1].read_bytes()
    )

    source = {
        "contract": "helianthus.platform.deployment-source-receipt.v1",
        "source_commit": campaign["provenance"]["deployment_source_commit"],
        "binary_hash": binary_hash,
    }
    source_path = write(tmp_path / "deployment-source.json", source)
    campaign["provenance"]["deployment_source_hash"] = validator.bytes_digest(
        source_path.read_bytes()
    )
    campaign["provenance"]["deployment_binary_hash"] = binary_hash
    validator._validate_deployment_source(
        campaign, source_path, binary_path, live_context
    )

    source["source_commit"] = "2" * 40
    write(source_path, source)
    with pytest.raises(validator.ValidationFailure) as raised:
        validator._validate_deployment_source(
            campaign, source_path, binary_path, live_context
        )
    assert raised.value.category == "live.deployment"


def test_live_selector_gate_rejects_sanitized_fixture_selectors() -> None:
    validator = module()
    campaign = live_campaign(validator)
    with pytest.raises(validator.ValidationFailure) as raised:
        validator._validate_non_synthetic_selectors(campaign)
    assert raised.value.category == "live.selector"


def test_relabelled_public_cannot_open_m9(tmp_path: pathlib.Path) -> None:
    validator = module()
    public = load(PUBLIC)
    public["evidence_mode"] = "LIVE_CAPTURE"
    public["provenance"]["class"] = "LIVE_CAPTURE"
    public["m9_consumer_gate"] = "READY_FOR_M9_PLANNING"
    public["verdict"] = "VALID_PROMOTION_LOCK"
    rehash_public(validator, public)
    path = write(tmp_path / "relabelled-public.json", public)
    standalone = run("verify-public", path)
    assert (standalone.returncode, standalone.stdout) == (1, "private.required\n")
    rebound = run("verify-public", path, private_campaign=PRIVATE)
    assert (rebound.returncode, rebound.stdout) == (1, "private.binding\n")


def test_eligible_terminal_state_is_derived_from_two_ordered_windows(tmp_path: pathlib.Path) -> None:
    validator = module()
    campaign = load(PRIVATE)
    registry = load(REGISTRY)
    for leaf, expected in zip(campaign["candidates"], registry["candidate_catalog"], strict=True):
        if expected["protocol_eligibility"] == "ELIGIBLE":
            assert [item["window_id"] for item in leaf["assessments"]] == [
                "window-pre-restart",
                "window-post-restart",
            ]
        else:
            assert leaf["assessments"] == []

    wrong_terminal = load(PRIVATE)
    candidate(wrong_terminal, "m7-candidate-0005")["terminal_state"] = "MISMATCH"
    rehash_campaign(validator, wrong_terminal)
    result = run("verify-private", write(tmp_path / "wrong-terminal.json", wrong_terminal))
    assert (result.returncode, result.stdout) == (1, "state.invalid\n")

    missing_window = load(PRIVATE)
    candidate(missing_window, "m7-candidate-0005")["assessments"].pop()
    rehash_campaign(validator, missing_window)
    result = run("verify-private", write(tmp_path / "missing-window.json", missing_window))
    assert (result.returncode, result.stdout) == (1, "state.invalid\n")


def test_catalog_terminal_and_capability_exceptions_remain_exact(tmp_path: pathlib.Path) -> None:
    validator = module()
    public = load(PUBLIC)
    terminal = public["candidate_results"][0]
    terminal.update({"terminal_state": "MISSING", "window_outcomes": ["MISSING", "MISSING"]})
    rehash_public(validator, public)
    result = run("verify-public", write(tmp_path / "terminal-relabel.json", public))
    assert (result.returncode, result.stdout) == (1, "candidate.catalog\n")

    public = load(PUBLIC)
    capability = next(item for item in public["candidate_results"] if item["candidate_id"] == "m7-candidate-0008")
    capability.update(
        {
            "decision": "PROMOTED",
            "terminal_state": None,
            "visibility": "LOCKED_NOT_EXPOSED",
            "dossier_hash": "sha256:" + "e" * 64,
            "window_outcomes": ["MATCH", "MATCH"],
        }
    )
    public["counts"] = {"total": 18, "promoted": 2, "withheld": 16}
    rehash_public(validator, public)
    result = run("verify-public", write(tmp_path / "capability-promoted.json", public))
    assert (result.returncode, result.stdout) == (1, "candidate.catalog\n")


def test_b524_selector_family_and_catalog_tuple_are_bound(tmp_path: pathlib.Path) -> None:
    validator = module()
    campaign = load(PRIVATE)
    identity = candidate(campaign, "m7-candidate-0005")["ebus_identity"]
    identity["RR"] += 1
    rehash_ebus_identity(validator, identity)
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "selector-substitution.json", campaign))
    assert (result.returncode, result.stdout) == (1, "identity.binding\n")

    campaign = load(PRIVATE)
    identity = candidate(campaign, "m7-candidate-0005")["ebus_identity"]
    identity["family"] = "B509"
    rehash_ebus_identity(validator, identity)
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "family-substitution.json", campaign))
    assert (result.returncode, result.stdout) == (1, "schema.private\n")


def test_full_eebus_source_profile_and_identity_hash_are_bound(tmp_path: pathlib.Path) -> None:
    validator = module()
    registry = load(REGISTRY)
    campaign = load(PRIVATE)
    leaf = candidate(campaign, "m7-candidate-0007")
    identity = leaf["eebus_identity"]
    identity["description_functions"] = ["hvacSystemFunctionDescriptionListData"]
    source_keys = registry["candidate_catalog"][6]["eebus_source"].keys()
    substituted_source = {key: identity[key] for key in source_keys}
    identity["source_profile_hash"] = validator.digest(
        validator.SOURCE_PROFILE_DOMAIN, substituted_source
    )
    rehash_eebus_identity(validator, identity)
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "source-profile-substitution.json", campaign))
    assert (result.returncode, result.stdout) == (1, "identity.binding\n")

    campaign = load(PRIVATE)
    candidate(campaign, "m7-candidate-0007")["eebus_identity"]["feature_address"] += 1
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "native-identity-substitution.json", campaign))
    assert (result.returncode, result.stdout) == (1, "identity.binding\n")


def test_raw_hash_and_numeric_raw_to_decoded_identity_are_bound(tmp_path: pathlib.Path) -> None:
    validator = module()
    campaign = load(PRIVATE)
    sample = promoted(campaign)["assessments"][0]["ebus_sample"]
    sample["raw_value"]["decimal"] = {"number": 126, "scale": -1}
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "raw-hash-substitution.json", campaign))
    assert (result.returncode, result.stdout) == (1, "raw.binding\n")

    campaign = load(PRIVATE)
    sample = promoted(campaign)["assessments"][0]["ebus_sample"]
    sample["raw_value"]["decimal"] = {"number": 126, "scale": -1}
    rehash_raw(validator, sample)
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "raw-decoded-substitution.json", campaign))
    assert (result.returncode, result.stdout) == (1, "raw.binding\n")


def test_enum_and_boolean_raw_pairs_are_catalog_mapped(tmp_path: pathlib.Path) -> None:
    validator = module()
    for candidate_id in ("m7-candidate-0007", "m7-candidate-0009"):
        campaign = load(PRIVATE)
        leaf = promote_mapped_candidate(validator, campaign, candidate_id)
        rehash_campaign(validator, campaign)
        passing = run("verify-private", write(tmp_path / f"{candidate_id}-valid.json", campaign))
        assert (passing.returncode, passing.stdout) == (0, "PASS\n")

        raw = leaf["assessments"][0]["eebus_sample"]["raw_value"]
        if raw["kind"] == "NUMERIC":
            raw["decimal"] = {"number": 1, "scale": 0}
        else:
            raw["boolean"] = True
        rehash_raw(validator, leaf["assessments"][0]["eebus_sample"])
        rehash_campaign(validator, campaign)
        result = run("verify-private", write(tmp_path / f"{candidate_id}-raw-substitution.json", campaign))
        assert (result.returncode, result.stdout) == (1, "comparator.invalid\n")

    campaign = load(PRIVATE)
    sample = candidate(campaign, "m7-candidate-0007")["assessments"][0]["eebus_sample"]
    sample["raw_value"]["decimal"] = {"number": 1, "scale": 0}
    rehash_raw(validator, sample)
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "missing-peer-raw-substitution.json", campaign))
    assert (result.returncode, result.stdout) == (1, "comparator.invalid\n")


def test_enum_non_match_rejects_scaled_numeric_raw_alias(
    tmp_path: pathlib.Path,
) -> None:
    validator = module()
    campaign = load(PRIVATE)
    leaf = promote_mapped_candidate(validator, campaign, "m7-candidate-0007")
    assessment = leaf["assessments"][0]
    assessment["ebus_sample"]["raw_value"]["decimal"] = {
        "number": 1,
        "scale": 0,
    }
    assessment["ebus_sample"]["value"]["enum"] = "auto"
    rehash_raw(validator, assessment["ebus_sample"])
    assessment["eebus_sample"]["raw_value"]["decimal"] = {
        "number": 20,
        "scale": -1,
    }
    assessment["eebus_sample"]["value"]["enum"] = "off"
    rehash_raw(validator, assessment["eebus_sample"])
    assessment["comparator"]["outcome"] = "MISMATCH"
    leaf.update(
        decision="WITHHELD",
        terminal_state="MISMATCH",
        visibility="RAW_DEBUG_ONLY",
        dossier_hash=None,
    )
    rehash_campaign(validator, campaign)
    result = run(
        "verify-private", write(tmp_path / "scaled-enum-non-match.json", campaign)
    )
    assert (result.returncode, result.stdout) == (1, "state.invalid\n")


def test_enum_raw_ids_reject_boolean_integer_aliases(tmp_path: pathlib.Path) -> None:
    validator = module()
    campaign = load(PRIVATE)
    leaf = candidate(campaign, "m7-candidate-0007")
    for assessment in leaf["assessments"]:
        sample = assessment["eebus_sample"]
        sample["raw_value"] = {
            "kind": "BOOLEAN",
            "decimal": None,
            "enum": None,
            "boolean": True,
        }
        sample["value"]["enum"] = "on"
        rehash_raw(validator, sample)
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "boolean-enum-id.json", campaign))
    assert (result.returncode, result.stdout) == (1, "comparator.invalid\n")


def test_numeric_rule_is_inclusive_and_catalog_owned(tmp_path: pathlib.Path) -> None:
    validator = module()
    campaign = load(PRIVATE)
    comparators = [item["comparator"] for item in promoted(campaign)["assessments"]]
    assert all(item["delta"] == item["declared_spine_step"] for item in comparators)
    comparators[0]["declared_spine_step"] = {"number": 99, "scale": 0}
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "inflated-step.json", campaign))
    assert (result.returncode, result.stdout) == (1, "comparator.invalid\n")


def test_mismatch_is_recomputed_from_bound_values(tmp_path: pathlib.Path) -> None:
    validator = module()
    campaign = load(PRIVATE)
    leaf = promoted(campaign)
    for assessment in leaf["assessments"]:
        assessment["comparator"]["outcome"] = "MISMATCH"
    leaf.update(
        decision="WITHHELD",
        terminal_state="MISMATCH",
        visibility="RAW_DEBUG_ONLY",
        dossier_hash=None,
    )
    rehash_campaign(validator, campaign)
    fabricated = run(
        "verify-private", write(tmp_path / "fabricated-mismatch.json", campaign)
    )
    assert (fabricated.returncode, fabricated.stdout) == (
        1,
        "state.invalid\n",
    )

    campaign = load(PRIVATE)
    leaf = promoted(campaign)
    for position, assessment in enumerate(leaf["assessments"]):
        sample = assessment["eebus_sample"]
        sample["raw_value"]["decimal"] = {"number": 14, "scale": 0}
        sample["value"]["decimal"] = {"number": 14, "scale": 0}
        rehash_raw(validator, sample)
        assessment["comparator"]["delta"] = (
            {"number": 15, "scale": -1}
            if position == 0
            else {"number": 1, "scale": 0}
        )
        assessment["comparator"]["outcome"] = "MISMATCH"
    leaf.update(
        decision="WITHHELD",
        terminal_state="MISMATCH",
        visibility="RAW_DEBUG_ONLY",
        dossier_hash=None,
    )
    rehash_campaign(validator, campaign)
    observed = run("verify-private", write(tmp_path / "observed-mismatch.json", campaign))
    assert (observed.returncode, observed.stdout) == (0, "PASS\n")


def observed_terminal_campaign(validator, outcome: str) -> dict:
    campaign = load(PRIVATE)
    leaf = promoted(campaign)
    assessment = leaf["assessments"][0]
    assessment["comparator"]["outcome"] = outcome
    assessment["comparator"]["delta"] = None
    if outcome == "MISSING":
        assessment["ebus_sample"] = None
        assessment["observed_ebus_identity_hash"] = None
        assessment["skew_ns"] = None
        assessment["age_ns"] = None
    elif outcome == "IDENTITY_MISMATCH":
        assessment["observed_ebus_identity_hash"] = "sha256:" + "f" * 64
    elif outcome == "GENERATION_CHANGED":
        assessment["eebus_sample"]["connection_generation"] += 1
    elif outcome == "INVALID":
        assessment["eebus_sample"]["valid"] = False
    elif outcome == "STALE":
        assessment["ebus_sample"]["observed_at"] = "2026-08-11T09:59:59.500000000Z"
        assessment["eebus_sample"]["observed_at"] = "2026-08-11T09:59:59.600000000Z"
        assessment["skew_ns"] = 100_000_000
        assessment["age_ns"] = 10_500_000_000
    elif outcome == "CONFLICT":
        first = copy.deepcopy(assessment["eebus_sample"])
        second = copy.deepcopy(first)
        second["observed_at"] = "2026-08-11T10:00:05.200000000Z"
        second["raw_value"] = {
            "kind": "NUMERIC",
            "decimal": {"number": 14, "scale": 0},
            "enum": None,
            "boolean": None,
        }
        second["value"] = copy.deepcopy(second["raw_value"])
        rehash_raw(validator, second)
        assessment["conflict_samples"] = [first, second]
    elif outcome == "MISMATCH":
        sample = assessment["eebus_sample"]
        sample["raw_value"] = {
            "kind": "NUMERIC",
            "decimal": {"number": 14, "scale": 0},
            "enum": None,
            "boolean": None,
        }
        sample["value"] = copy.deepcopy(sample["raw_value"])
        rehash_raw(validator, sample)
        assessment["comparator"]["delta"] = {"number": 15, "scale": -1}
    else:
        raise AssertionError(outcome)
    leaf.update(
        decision="WITHHELD",
        terminal_state=outcome,
        visibility="RAW_DEBUG_ONLY",
        dossier_hash=None,
    )
    rehash_campaign(validator, campaign)
    return campaign


def test_each_declared_eligible_terminal_outcome_is_recomputed(
    tmp_path: pathlib.Path,
) -> None:
    validator = module()
    outcomes = (
        "MISSING",
        "IDENTITY_MISMATCH",
        "GENERATION_CHANGED",
        "INVALID",
        "STALE",
        "CONFLICT",
        "MISMATCH",
    )
    for outcome in outcomes:
        campaign = observed_terminal_campaign(validator, outcome)
        result = run(
            "verify-private",
            write(tmp_path / f"observed-{outcome.lower()}.json", campaign),
        )
        assert (result.returncode, result.stdout) == (0, "PASS\n"), outcome

        relabelled = load(PRIVATE)
        leaf = promoted(relabelled)
        leaf["assessments"][0]["comparator"]["outcome"] = outcome
        leaf.update(
            decision="WITHHELD",
            terminal_state=outcome,
            visibility="RAW_DEBUG_ONLY",
            dossier_hash=None,
        )
        rehash_campaign(validator, relabelled)
        falsifier = run(
            "verify-private",
            write(tmp_path / f"relabelled-{outcome.lower()}.json", relabelled),
        )
        assert falsifier.returncode == 1, outcome


def test_numeric_conflict_requires_semantically_distinct_decimal_values(
    tmp_path: pathlib.Path,
) -> None:
    validator = module()
    campaign = observed_terminal_campaign(validator, "CONFLICT")
    conflict_samples = promoted(load(PRIVATE))["assessments"][0]["conflict_samples"]
    assert conflict_samples == []
    assessment = candidate(campaign, "m7-candidate-0018")["assessments"][0]
    first, second = assessment["conflict_samples"]
    first_value = validator.decimal_value(first["value"]["decimal"])
    decimal = second["value"]["decimal"]
    decimal["number"] = int(first_value * 10)
    decimal["scale"] = -1
    second["raw_value"] = copy.deepcopy(second["value"])
    rehash_raw(validator, second)
    rehash_campaign(validator, campaign)
    result = run(
        "verify-private", write(tmp_path / "equal-decimal-conflict.json", campaign)
    )
    assert (result.returncode, result.stdout) == (1, "conflict.invalid\n")


def test_numeric_bounds_are_inclusive_and_out_of_range_is_invalid(
    tmp_path: pathlib.Path,
) -> None:
    validator = module()
    registry = load(REGISTRY)
    expected = registry["candidate_catalog"][-1]
    constraints = expected["eebus_source"]["declared_constraints"]
    campaign = load(PRIVATE)
    leaf = promoted(campaign)
    for assessment, boundary in zip(
        leaf["assessments"],
        (constraints["minimum"], constraints["maximum"]),
        strict=True,
    ):
        typed = {
            "kind": "NUMERIC",
            "decimal": copy.deepcopy(boundary),
            "enum": None,
            "boolean": None,
        }
        for key in ("ebus_sample", "eebus_sample"):
            assessment[key]["raw_value"] = copy.deepcopy(typed)
            assessment[key]["value"] = copy.deepcopy(typed)
            rehash_raw(validator, assessment[key])
        assessment["comparator"]["delta"] = {"number": 0, "scale": 0}
    rehash_campaign(validator, campaign)
    boundary_result = run(
        "verify-private", write(tmp_path / "inclusive-bounds.json", campaign)
    )
    assert (boundary_result.returncode, boundary_result.stdout) == (0, "PASS\n")

    campaign = load(PRIVATE)
    leaf = promoted(campaign)
    assessment = leaf["assessments"][0]
    outside = copy.deepcopy(constraints["maximum"])
    outside["number"] += 1
    typed = {
        "kind": "NUMERIC",
        "decimal": outside,
        "enum": None,
        "boolean": None,
    }
    for key in ("ebus_sample", "eebus_sample"):
        assessment[key]["raw_value"] = copy.deepcopy(typed)
        assessment[key]["value"] = copy.deepcopy(typed)
        rehash_raw(validator, assessment[key])
    assessment["comparator"]["delta"] = {"number": 0, "scale": 0}
    rehash_campaign(validator, campaign)
    rejected = run("verify-private", write(tmp_path / "out-of-range-match.json", campaign))
    assert (rejected.returncode, rejected.stdout) == (1, "comparator.range\n")

    assessment["comparator"]["outcome"] = "INVALID"
    assessment["comparator"]["delta"] = None
    leaf.update(
        decision="WITHHELD",
        terminal_state="INVALID",
        visibility="RAW_DEBUG_ONLY",
        dossier_hash=None,
    )
    rehash_campaign(validator, campaign)
    invalid = run("verify-private", write(tmp_path / "out-of-range-invalid.json", campaign))
    assert (invalid.returncode, invalid.stdout) == (0, "PASS\n")


def test_capture_limits_and_restart_generation_are_bound(tmp_path: pathlib.Path) -> None:
    validator = module()
    campaign = load(PRIVATE)
    promoted(campaign)["assessments"][0]["max_skew_ns"] *= 2
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "widened-limit.json", campaign))
    assert (result.returncode, result.stdout) == (1, "sample.invalid\n")

    campaign = load(PRIVATE)
    promoted(campaign)["assessments"][0]["eebus_sample"]["capture_generation"] = "wrong"
    rehash_campaign(validator, campaign)
    result = run("verify-private", write(tmp_path / "wrong-generation.json", campaign))
    assert (result.returncode, result.stdout) == (1, "sample.invalid\n")


def test_existing_zero_profile_canonical_bytes_are_unchanged() -> None:
    expected = {
        "leaf-promotion-registry-v1.json": "ad33736c00aa2c3ecaac981606d25c064088c80cb72ca5389b83c5d9df40f6a3",
        "../fixtures/leaf-promotion-dossier/v1/positive/dossier.json": "3b12e3b6f625f6efb28fced19d679ab73b974fc4369e0dba9f61f1a2d104ec64",
        "../fixtures/leaf-promotion-dossier/v1/positive/result.json": "a4e5deb1027e337e917304addfa1aebaaf8f04659d7de38b36083c78525d1a04",
    }
    for relative, expected_hash in expected.items():
        assert hashlib.sha256((SCHEMA_ROOT / relative).resolve().read_bytes()).hexdigest() == expected_hash


def mutate(campaign: dict, public: dict, mutation: str) -> tuple[str, dict]:
    leaf = promoted(campaign)
    if mutation == "GRANULARITY_SUBSTITUTION":
        leaf["assessments"][0]["comparator"]["declared_spine_step"] = {"number": 1, "scale": -1}
    elif mutation == "MISSING_GRANULARITY":
        leaf["assessments"][0]["comparator"]["declared_spine_step"] = None
    elif mutation == "IDENTITY_MISMATCH":
        leaf["ebus_identity"]["source_address"] = 126
    elif mutation == "GENERATION_CHANGE":
        leaf["assessments"][0]["eebus_sample"]["connection_generation"] += 1
    elif mutation == "SKEW_EXCEEDED":
        leaf["assessments"][0]["max_skew_ns"] = 1
    elif mutation == "STALE_SAMPLE":
        leaf["assessments"][0]["max_age_ns"] = 1
    elif mutation == "MISSING_SAMPLE":
        leaf["assessments"][0]["ebus_sample"] = None
    elif mutation == "CONFLICT_AS_MATCH":
        leaf["assessments"][0]["comparator"]["outcome"] = "CONFLICT"
    elif mutation == "REPLAY_DRIFT":
        campaign["source_bindings"]["replay_hash"] = "sha256:" + "f" * 64
    elif mutation == "PUBLIC_IDENTITY_LEAK":
        public["device_address"] = "forbidden"
        return "verify-public", public
    elif mutation == "PUBLIC_SECRET_LEAK":
        public["private_key"] = "forbidden"
        return "verify-public", public
    else:
        raise AssertionError(mutation)
    return "verify-private", campaign


def test_negative_vectors_are_closed_and_fail_in_declared_category(tmp_path: pathlib.Path) -> None:
    assert {path.name for path in NEGATIVE.glob("*.json")} == set(EXPECTED_NEGATIVE)
    baseline_private = load(PRIVATE)
    baseline_public = load(PUBLIC)
    for name, (mutation, category) in EXPECTED_NEGATIVE.items():
        assert load(NEGATIVE / name) == {
            "contract": "helianthus.platform.leaf-promotion-captured-multi-leaf-negative.v1",
            "mutation": mutation,
            "expected_category": category,
        }
        command, value = mutate(copy.deepcopy(baseline_private), copy.deepcopy(baseline_public), mutation)
        result = run(command, write(tmp_path / name, value))
        assert (result.returncode, result.stdout, result.stderr) == (1, category + "\n", ""), name


def test_public_redaction_and_private_schema_fail_closed(tmp_path: pathlib.Path) -> None:
    for path in (PRIVATE, PUBLIC):
        serialized = path.read_text(encoding="utf-8").lower()
        for forbidden in ("private_key", "trust_store", "candidate_ref", "ship_id", "ski", "token"):
            assert forbidden not in serialized
    campaign = load(PRIVATE)
    campaign["private_key"] = "forbidden"
    result = run("verify-private", write(tmp_path / "private-secret.json", campaign))
    assert (result.returncode, result.stdout) == (1, "schema.private\n")


def test_secret_material_is_rejected_recursively_in_schema_allowed_strings(
    tmp_path: pathlib.Path,
) -> None:
    payloads = (
        "-----BEGIN PRIVATE KEY-----secret-----END PRIVATE KEY-----",
        "Bearer abcdefghijklmnopqrstuvwxyz0123456789",
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJvcGVyYXRvciJ9.abcdefghijklmnop",
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
        "__________________________________________8=",
        "A" * 180,
        "trust_store=" + "Q" * 32,
    )
    for index, payload in enumerate(payloads):
        campaign = load(PRIVATE)
        identity = candidate(campaign, "m7-candidate-0018")["eebus_identity"]
        identity["service_id"] = payload
        rehash_eebus_identity(module(), identity)
        rehash_campaign(module(), campaign)
        result = run(
            "verify-private", write(tmp_path / f"private-secret-{index}.json", campaign)
        )
        assert (result.returncode, result.stdout) == (1, "secret.material\n")

    public = load(PUBLIC)
    public["provenance"]["binding_hash"] = payloads[0]
    result = run("verify-public", write(tmp_path / "public-secret-value.json", public))
    assert (result.returncode, result.stdout) == (1, "secret.material\n")


def test_canonical_json_emits_unicode_as_utf8() -> None:
    validator = module()
    assert validator.canonical({"text": "é"}) == '{"text":"é"}'.encode("utf-8")


def test_generator_is_deterministic() -> None:
    before = {path: path.read_bytes() for path in (PRIVATE, PUBLIC)}
    result = subprocess.run(
        [sys.executable, str(GENERATOR)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    assert before == {path: path.read_bytes() for path in (PRIVATE, PUBLIC)}
