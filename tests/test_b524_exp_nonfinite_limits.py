"""Exercise semantic finiteness independently of strict JSON admission.

Counterfactual recipe (orchestrator, disposable copy only): remove only the
numeric-range `_require(all(... math.isfinite ...), ...must be finite)` call
in `_validate_record`, retaining number typing, raw agreement, ordering,
positive-step and published-pin guards. Run this file unchanged: all nine
semantic cases must fail because the exact finiteness diagnostic disappears,
even when another guard still rejects the candidate. No production mutation
belongs in this patch.
"""

import importlib.util
import json
import math
import struct
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CATALOG = "b524-basv0-description-profile-v1.json"
FIXTURE = ROOT / "protocols/vaillant/fixtures" / CATALOG
SCHEMA = FIXTURE.with_name("b524-basv0-description-profile-schema-v1.json")
OBSERVATIONS = FIXTURE.with_name("b524-basv0-register-observations-v1.json")
OBSERVATION_SCHEMA = FIXTURE.with_name(
    "b524-basv0-register-observations-schema-v1.json"
)
SCOPES = ROOT / "development/fixtures/b524-basv0-validation-scope-v1.json"
SCOPE_SCHEMA = SCOPES.with_name("b524-basv0-validation-scope-schema-v1.json")
SELECTOR = {"operation": "02", "group": "00", "instance": "00", "register": "0001"}
NONFINITE = [
    pytest.param(float("nan"), id="nan"),
    pytest.param(float("inf"), id="positive-infinity"),
    pytest.param(float("-inf"), id="negative-infinity"),
]

_SPEC = importlib.util.spec_from_file_location(
    "exp_nonfinite_validator",
    ROOT / "scripts/validate_b524_basv0_description_profile.py",
)
validator = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(validator)


@pytest.fixture
def documents():
    paths = (FIXTURE, SCHEMA, OBSERVATIONS, OBSERVATION_SCHEMA, SCOPES, SCOPE_SCHEMA)
    retained = {path: path.read_bytes() for path in paths}
    inputs = tuple(json.loads(retained[path]) for path in (FIXTURE, OBSERVATIONS, SCOPES))
    yield inputs
    for path, original in retained.items():
        assert path.read_bytes() == original, f"published input changed: {path.name}"


def exp_record(document):
    index, record = next(
        (index, record) for index, record in enumerate(document["records"])
        if record["selector"] == SELECTOR
    )
    # Native contract: protocols/vaillant/ebus-vaillant-b524-basv0-profile-v1.md.
    # Qualified is an admission label; the public codec basis stays Hypothesis.
    assert record["decoded"]["codec"] == "EXP"
    assert record["decoded"]["qualification"] == "qualified"
    assert record["decoded"]["codec_basis"] == "public_local_constraint_codec"
    assert validator.register_map_wire()[("02", "00", "0001")] == {"EXP"}
    return index, record


def replace_limit(record, field, value):
    span = struct.pack("<f", value).hex().upper()
    record["raw_limits"][f"{field}_hex"] = span
    record["raw_description_hex"] = record["raw_description_hex"][:6] + "".join(
        record["raw_limits"][f"{name}_hex"] for name in ("min", "max", "step")
    )
    record["decoded"][field] = value
    decoded_span = struct.unpack("<f", bytes.fromhex(span))[0]
    assert (math.isnan(value) and math.isnan(decoded_span)) or decoded_span == value


def validate_preserving_inputs(inputs):
    # A memory-only snapshot also compares NaN reliably (NaN != NaN).
    before = json.dumps(inputs, sort_keys=True)
    document, observations, scopes = inputs
    try:
        validator.validate_documents(document, observations, CATALOG, scopes)
    finally:
        assert json.dumps(inputs, sort_keys=True) == before


def test_unchanged_finite_public_control_passes(documents):
    _, record = exp_record(documents[0])
    assert all(math.isfinite(record["decoded"][field]) for field in ("min", "max", "step"))
    validate_preserving_inputs(documents)


@pytest.mark.parametrize("field", ["min", "max", "step"])
@pytest.mark.parametrize("value", NONFINITE)
def test_nonfinite_exp_limit_has_finiteness_diagnostic(documents, field, value):
    index, record = exp_record(documents[0])
    replace_limit(record, field, value)
    # Call the semantic API directly: strict JSON parsing cannot mask this guard.
    with pytest.raises(validator.ValidationError) as caught:
        validate_preserving_inputs(documents)
    assert str(caught.value) == f"records[{index}].decoded numeric range must be finite"


def schema_result(text):
    # Stream only; never persist a non-JSON numeric token in a fixture file.
    return subprocess.run(
        ["jv", str(SCHEMA), "/dev/stdin"], input=text, cwd=ROOT,
        text=True, capture_output=True, check=False, timeout=20,
    )


def test_strict_json_schema_control_passes(documents):
    result = schema_result(json.dumps(documents[0], allow_nan=False))
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("value", NONFINITE)
def test_strict_json_rejection_is_separate_from_semantics(documents, value):
    _, record = exp_record(documents[0])
    replace_limit(record, "max", value)
    with pytest.raises(ValueError, match="Out of range float values"):
        json.dumps(documents[0], allow_nan=False)
    # Python's permissive encoder emits non-JSON tokens; jv must reject parsing,
    # independently of schema constraints or the in-process semantic validator.
    result = schema_result(json.dumps(documents[0]))
    assert result.returncode != 0
    assert "invalid character" in result.stdout + result.stderr
