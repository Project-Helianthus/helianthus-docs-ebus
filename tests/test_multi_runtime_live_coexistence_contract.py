from __future__ import annotations

import json
import pathlib


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
PAGE = REPO_ROOT / "docs/platform/multi-runtime-coexistence-no-drift-v1.md"
EVIDENCE_SCHEMA = (
    REPO_ROOT
    / "docs/platform/schemas/multi-runtime-coexistence-evidence-v1.schema.json"
)
REGISTRY = (
    REPO_ROOT
    / "docs/platform/schemas/multi-runtime-coexistence-registry-v1.json"
)

M7_GATEWAY_MERGE = "8bcba2107d10b149f984ac9546ea6427a9cda8a1"
M7_DOCS_MERGE = "35d2eba256a77b6575a2b45c07e73f054ff74ced"


def load(path: pathlib.Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_msp08_v1_declares_distinct_synthetic_and_live_profiles() -> None:
    registry = load(REGISTRY)

    assert "m7_completion_token" not in registry
    assert registry["m7_live_predecessor"] == {
        "repository": "github.com/Project-Helianthus/helianthus-ebusgateway",
        "source_commit": M7_GATEWAY_MERGE,
        "docs_source_commit": M7_DOCS_MERGE,
        "binding_mode": "VALIDATED_INPUTS_AND_REGENERATED_REPLAY",
    }
    assert registry["scenario_profiles"]["SYNTHETIC_OFFLINE_FIXTURE"] == [
        "EEBUS_DISABLED_BASELINE",
        "EEBUS_DISABLED_CONFIRMED",
        "EEBUS_ENABLED_NO_SERVICES",
        "EEBUS_CONNECTED_CANDIDATE_ONLY",
        "EEBUS_CONFLICTED_WITHHELD",
        "EEBUS_DISABLED_ROLLBACK",
    ]
    assert registry["scenario_profiles"]["CAPTURED_RUNTIME_EVIDENCE"] == [
        "EEBUS_CONNECTED_BASELINE",
        "EEBUS_CONNECTED_RAW_WITHHELD",
        "EEBUS_RESTART_PERSISTED",
        "EEBUS_CONNECTED_ROLLBACK",
    ]


def test_msp08_v1_schema_exposes_real_live_fact_counts_and_m7_source() -> None:
    schema = load(EVIDENCE_SCHEMA)
    m7 = schema["$defs"]["M7Binding"]
    state = schema["$defs"]["StateEvidence"]

    assert "completion_token" not in m7["required"]
    assert "completion_token" not in m7["properties"]
    assert "source_commit" in m7["required"]
    assert "raw_only_count" in state["required"]
    assert "withheld_count" in state["required"]
    assert "RAW_ONLY" in state["properties"]["facts"]["items"]["properties"][
        "status"
    ]["enum"]


def test_msp08_live_contract_is_same_artifact_raw_first_and_non_promoting() -> None:
    page = PAGE.read_text(encoding="utf-8")

    for phrase in (
        "MSP-08-LIVE-R1",
        M7_GATEWAY_MERGE,
        M7_DOCS_MERGE,
        "same exact gateway artifact",
        "RAW_ONLY",
        "WITHHELD",
        "does not fabricate `CANDIDATE` or `CONFLICTED`",
        "restart persistence",
        "public-redacted",
        "does not authorize M8.5 or M9",
    ):
        assert phrase in page

