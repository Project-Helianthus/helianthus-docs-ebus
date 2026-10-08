import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

def test_basv2_profile_keeps_coverage_and_nonclaim_boundaries() -> None:
    profile = json.loads((ROOT / "protocols/vaillant/fixtures/b524-bounded-survey-basv2-v1.json").read_text())
    assert profile["schema_version"] == "b524-bounded-survey-profile/v1"
    assert profile["tool_identity"]["acquisition"]["commit"] == "c1c87294989ff15b52c3a629146e56b9871e5b1f"
    assert profile["tool_identity"]["catalog"]["commit"] == "f15ac183b9f345afce72852ec1fbbb8291fbdd14"
    assert profile["execution"]["planned_jobs"] == profile["execution"]["completed_jobs"] == 3274
    assert profile["execution"]["final_transport_failures"] == 0
    windows = {(item["operation"], group): item for item in profile["group_windows"] for group in item["groups"]}
    assert windows[("OP02", "0A")]["rr_window"] == "0000..0050"
    assert windows[("OP06", "0D")]["status"] == "known_family_no_positive_in_this_survey"
    assert windows[("OP06", "10")]["status"] == "unknown_group_empty_reply_only"
    assert any(sample["selector"]["ii"] == "FF" for sample in profile["samples"])
    for sample in profile["samples"]:
        if sample["kind"] in {"op02_read", "op06_read"}:
            assert sample["reply_payload_hex"][2:4].upper() == sample["selector"]["gg"]
            rr = sample["selector"]["rr"]
            assert sample["reply_payload_hex"][4:8].upper() == rr[2:4] + rr[0:2]
    assert "terminal RR maxima" in " ".join(profile["nonclaims"])

def test_methodology_preserves_read_only_boundary() -> None:
    text = (ROOT / "protocols/vaillant/b524-survey-methodology.md").read_text()
    assert "not evidence that a group" in text
    assert "does not write" in text
    assert "BASV0, BASV3, or CTLv3" in text


def test_effective_windows_are_separate_from_survey_coverage_and_partial_describe() -> None:
    profile = json.loads((ROOT / "protocols/vaillant/fixtures/b524-bounded-survey-basv2-v1.json").read_text())
    windows = profile["effective_scan_windows"]
    assert windows["OP02"]["00"]["rr_max"] == "00FF"
    assert windows["OP02"]["04"]["rr_max"] == "000B"
    assert windows["OP06"]["0E"]["rr_max"] == "0033"
    assert windows["OP06"]["0D"]["rr_max"] is None
    assert all(not window["terminal_max_established"] for op in ("OP02", "OP06") for window in windows[op].values())
    counts = profile["execution"]
    assert sum(counts["response_categories"][k] for k in ("value_reply", "empty_reply", "description_correlated_raw")) == counts["completed_jobs"]
    assert sum(phase["actual_attempts"] for phase in counts["phases"].values()) == counts["actual_attempts"]
    assert sum(phase["planned_jobs"] for phase in counts["phases"].values()) == counts["planned_jobs"]
    assert sum(phase["completed_jobs"] for phase in counts["phases"].values()) == counts["completed_jobs"]
    assert "unqualified" in profile["description_high_water_qualification"]
    text = (ROOT / "protocols/vaillant/b524-survey-methodology.md").read_text()
    assert "OP 00 GG II RRlo RRhi" in text
    assert "reserved CRC bytes `A9` and `AA`" in text


@pytest.mark.parametrize("field", ["actual_attempts", "reused_completed_exchanges", "phases"])
def test_profile_schema_rejects_missing_execution_accounting(tmp_path: Path, field: str) -> None:
    fixtures = ROOT / "protocols/vaillant/fixtures"
    profile = json.loads((fixtures / "b524-bounded-survey-basv2-v1.json").read_text())
    del profile["execution"][field]
    candidate = tmp_path / "missing-accounting.json"
    candidate.write_text(json.dumps(profile))
    result = subprocess.run(
        ["jv", str(fixtures / "b524-bounded-survey-profile-schema-v1.json"), str(candidate)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert field in result.stdout + result.stderr


@pytest.mark.parametrize(
    "profile_path",
    sorted(path for path in (ROOT / "protocols/vaillant/fixtures").glob("b524-bounded-survey-*-v1.json")
           if not path.name.startswith("b524-bounded-survey-profile-")),
    ids=lambda path: path.stem,
)
def test_all_contributed_profiles_have_consistent_phase_totals(profile_path: Path) -> None:
    counts = json.loads(profile_path.read_text())["execution"]
    for key in ("planned_jobs", "completed_jobs", "actual_attempts"):
        assert sum(phase[key] for phase in counts["phases"].values()) == counts[key]
    assert counts["completed_jobs"] <= counts["planned_jobs"]
    assert counts["actual_attempts"] >= counts["completed_jobs"]
