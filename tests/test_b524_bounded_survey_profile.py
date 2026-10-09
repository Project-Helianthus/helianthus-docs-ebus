import json
import subprocess
from copy import deepcopy
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
    text = (ROOT / "protocols/vaillant/ebus-vaillant-b524-survey-methodology.md").read_text()
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
    text = (ROOT / "protocols/vaillant/ebus-vaillant-b524-survey-methodology.md").read_text()
    assert "OP 00 GG II RRlo RRhi" in text
    assert "reserved CRC bytes `A9` and `AA`" in text


def test_basv2_high_group_discovery_accounting_is_reconcilable() -> None:
    profile = json.loads((ROOT / "protocols/vaillant/fixtures/b524-bounded-survey-basv2-v1.json").read_text())
    execution = profile["execution"]
    high_groups = execution["high_group_jobs"]
    op02 = high_groups["OP02"]
    op06 = high_groups["OP06"]

    assert high_groups["phase"] == "discovery"
    assert op02["read_jobs"] == op02["group_count"] * 6
    assert op02["describe_jobs"] == op02["group_count"] * 6
    assert op02["empty_replies"] == op02["read_jobs"] + op02["describe_jobs"]
    assert op06["read_jobs"] == op06["group_count"] * 6 * len(op06["read_instances"])
    assert op06["describe_jobs"] == op06["group_count"] * 6
    assert op06["empty_replies"] == op06["read_jobs"] + op06["describe_jobs"]
    assert high_groups["read_jobs"] == op02["read_jobs"] + op06["read_jobs"] == 606
    assert high_groups["describe_jobs"] == op02["describe_jobs"] + op06["describe_jobs"] == 414
    assert high_groups["empty_replies"] == op02["empty_replies"] + op06["empty_replies"] == 1020
    assert execution["response_categories"]["high_group_empty_reply"] == high_groups["empty_replies"]
    assert high_groups["extension_jobs"] == 0


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


def test_local_ci_validates_every_contributed_bounded_survey_profile() -> None:
    ci = (ROOT / "scripts/ci_local.sh").read_text()
    assert "protocols/vaillant/fixtures/b524-bounded-survey-*-v1.json" in ci
    assert "*-profile-schema-v1.json|*-profile-template-v1.json) continue" in ci
    assert 'jv protocols/vaillant/fixtures/b524-bounded-survey-profile-schema-v1.json "$profile"' in ci
    assert 'python3 scripts/validate_b524_bounded_survey_profile.py "$profile"' in ci


def _run_profile_validator(profile_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "scripts/validate_b524_bounded_survey_profile.py", str(profile_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_profile_validator_checks_every_profile_and_rejects_second_selector_payload_mismatch(
    tmp_path: Path,
) -> None:
    source = json.loads(
        (ROOT / "protocols/vaillant/fixtures/b524-bounded-survey-basv2-v1.json").read_text()
    )
    first = tmp_path / "b524-bounded-survey-first-v1.json"
    second = tmp_path / "b524-bounded-survey-second-v1.json"
    first.write_text(json.dumps(source))
    mismatched = deepcopy(source)
    mismatched["samples"][1]["selector"]["rr"] = "0002"
    second.write_text(json.dumps(mismatched))

    result = subprocess.run(
        ["python3", "scripts/validate_b524_bounded_survey_profile.py", str(first), str(second)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "request_payload_hex does not match OP/GG/II/RR selector" in result.stderr


@pytest.mark.parametrize("outcome", ["empty_reply", "transport_error"])
def test_profile_validator_rejects_payload_for_empty_or_transport_error(
    tmp_path: Path, outcome: str
) -> None:
    profile = json.loads(
        (ROOT / "protocols/vaillant/fixtures/b524-bounded-survey-basv2-v1.json").read_text()
    )
    profile["samples"][0]["outcome"] = outcome
    candidate = tmp_path / f"{outcome}.json"
    candidate.write_text(json.dumps(profile))

    result = _run_profile_validator(candidate)
    assert result.returncode != 0
    assert f"must be empty for {outcome}" in result.stderr


def test_profile_validator_allows_short_raw_decode_error_without_false_echo_claim(tmp_path: Path) -> None:
    profile = json.loads(
        (ROOT / "protocols/vaillant/fixtures/b524-bounded-survey-basv2-v1.json").read_text()
    )
    profile["samples"][0]["outcome"] = "decode_error"
    profile["samples"][0]["reply_payload_hex"] = "03"
    candidate = tmp_path / "malformed.json"
    candidate.write_text(json.dumps(profile))

    result = _run_profile_validator(candidate)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda profile: profile["tool_identity"]["acquisition"].update({"commit": 1}), "commit"),
        (lambda profile: profile["samples"][0]["selector"].update({"gg": "0a"}), "gg"),
        (lambda profile: profile["samples"][0].update({"request_payload_hex": "0G"}), "request_payload_hex"),
        (lambda profile: profile["samples"][0].update({"reply_payload_hex": "0"}), "reply_payload_hex"),
        (lambda profile: profile["samples"][0]["selector"].update({"op": "06"}), "op"),
        (lambda profile: profile["samples"][0].update({"kind": "op02_reed"}), "kind"),
    ],
)
def test_profile_schema_rejects_invalid_identity_and_payload_fields(
    tmp_path: Path, mutation, expected: str
) -> None:
    fixtures = ROOT / "protocols/vaillant/fixtures"
    profile = json.loads((fixtures / "b524-bounded-survey-basv2-v1.json").read_text())
    mutation(profile)
    candidate = tmp_path / "invalid-profile.json"
    candidate.write_text(json.dumps(profile))

    result = subprocess.run(
        ["jv", str(fixtures / "b524-bounded-survey-profile-schema-v1.json"), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert expected in result.stdout + result.stderr


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (lambda profile: profile["catalog_reference"].update({"path": None}), "path"),
        (lambda profile: profile["catalog_reference"].update({"scope": 7}), "scope"),
        (
            lambda profile: profile["catalog_reference"].update(
                {"qualified_description_limits": "not-an-array"}
            ),
            "qualified_description_limits",
        ),
        (
            lambda profile: profile["catalog_reference"]["qualified_description_limits"][0][
                "selector"
            ].update({"op": "7"}),
            "op",
        ),
    ],
)
def test_catalog_reference_schema_enforces_types_and_limit_selector(
    tmp_path: Path, mutation, expected: str
) -> None:
    fixtures = ROOT / "protocols/vaillant/fixtures"
    profile = json.loads((fixtures / "b524-bounded-survey-basv2-v1.json").read_text())
    mutation(profile)
    candidate = tmp_path / "invalid-catalog-reference.json"
    candidate.write_text(json.dumps(profile))
    result = subprocess.run(
        ["jv", str(fixtures / "b524-bounded-survey-profile-schema-v1.json"), str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert expected in result.stdout + result.stderr


@pytest.mark.parametrize("path", ["missing.csv", "../b524-op02-register-names.csv"])
def test_profile_validator_rejects_missing_or_unsafe_local_catalog_reference(
    tmp_path: Path, path: str
) -> None:
    profile = json.loads(
        (ROOT / "protocols/vaillant/fixtures/b524-bounded-survey-basv2-v1.json").read_text()
    )
    profile["catalog_reference"]["path"] = path
    candidate = tmp_path / "invalid-catalog-path.json"
    candidate.write_text(json.dumps(profile))
    result = _run_profile_validator(candidate)
    assert result.returncode != 0
    assert "catalog_reference.path" in result.stderr


@pytest.mark.parametrize("reference_kind", ["self", "unrelated"])
def test_profile_validator_rejects_non_catalog_reference(
    tmp_path: Path, reference_kind: str
) -> None:
    profile = json.loads(
        (ROOT / "protocols/vaillant/fixtures/b524-bounded-survey-basv2-v1.json").read_text()
    )
    candidate = tmp_path / "candidate.json"
    if reference_kind == "self":
        profile["catalog_reference"]["path"] = candidate.name
    else:
        unrelated = tmp_path / "unrelated.csv"
        unrelated.write_text("message\nirrelevant\n")
        profile["catalog_reference"]["path"] = unrelated.name
    candidate.write_text(json.dumps(profile))

    result = _run_profile_validator(candidate)

    assert result.returncode != 0
    assert "catalog_reference.path" in result.stderr


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        (
            lambda profile: profile["catalog_reference"].update(
                {"scope": "unrelated catalog scope"}
            ),
            "catalog_reference.scope",
        ),
        (
            lambda profile: profile["catalog_reference"]["qualified_description_limits"][0][
                "selector"
            ].update({"rr": "0002"}),
            "qualified_description_limits[0].selector",
        ),
        (
            lambda profile: profile["catalog_reference"]["qualified_description_limits"][0].update(
                {"max": False}
            ),
            "qualified_description_limits[0]",
        ),
    ],
)
def test_profile_validator_correlates_catalog_scope_and_description_limits(
    tmp_path: Path, mutation, expected: str
) -> None:
    profile = json.loads(
        (ROOT / "protocols/vaillant/fixtures/b524-bounded-survey-basv2-v1.json").read_text()
    )
    mutation(profile)
    candidate = tmp_path / "mismatched-catalog-contract.json"
    candidate.write_text(json.dumps(profile))

    result = _run_profile_validator(candidate)

    assert result.returncode != 0
    assert expected in result.stderr


@pytest.mark.parametrize(
    ("sample_index", "flags_class"),
    [(0, "read_only_visible"), (1, "writable_visible")],
)
def test_profile_validator_correlates_read_flags_class_to_reply(
    tmp_path: Path, sample_index: int, flags_class: str
) -> None:
    profile = json.loads(
        (ROOT / "protocols/vaillant/fixtures/b524-bounded-survey-basv2-v1.json").read_text()
    )
    profile["samples"][sample_index]["flags_class"] = flags_class
    candidate = tmp_path / f"mismatched-flags-class-{sample_index}.json"
    candidate.write_text(json.dumps(profile))

    result = _run_profile_validator(candidate)

    assert result.returncode != 0
    assert "flags_class" in result.stderr
