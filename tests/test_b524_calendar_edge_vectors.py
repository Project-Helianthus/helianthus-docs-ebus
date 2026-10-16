"""Synthetic syntax vectors for the published Hypothesis calendar candidates.

Contract: protocols/vaillant/ebus-vaillant-b524-basv0-profile-v1.md,
candidate layouts. Syntactic qualification does not authorize range edits;
calendar STEP remains unknown.
"""

import importlib.util
import json
import re
from copy import deepcopy
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CATALOG = "b524-basv0-description-profile-v1.json"
FIXTURES = ROOT / "protocols/vaillant/fixtures"
DESCRIPTIONS = json.loads((FIXTURES / CATALOG).read_text())
OBSERVATIONS = json.loads(
    (FIXTURES / "b524-basv0-register-observations-v1.json").read_text()
)
SCOPES = json.loads(
    (ROOT / "development/fixtures/b524-basv0-validation-scope-v1.json").read_text()
)
SPEC = importlib.util.spec_from_file_location(
    "calendar_edge_validator",
    ROOT / "scripts/validate_b524_basv0_description_profile.py",
)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def candidate(register: str, field: str, raw: str, text: str) -> tuple:
    document, overlay = deepcopy(DESCRIPTIONS), deepcopy(SCOPES)
    selector = {
        "operation": "02", "group": "00", "instance": "00",
        "register": register,
    }
    index, record = next(
        (i, r) for i, r in enumerate(document["records"])
        if r["selector"] == selector
    )
    # Keep the other endpoint, raw STEP, header and selector/basis intact.
    record["raw_limits"][f"{field}_hex"] = raw
    body = "".join(record["raw_limits"][f"{key}_hex"] for key in ("min", "max", "step"))
    record["raw_description_hex"] = record["raw_description_hex"][:6] + body
    record["description_payload_length"] = len(body) // 2
    record["decoded"][field] = text
    entry = next(e for e in overlay["records"] if e["selector"] == selector)
    return document, overlay, index, record, entry


@pytest.mark.parametrize("register,field,raw,text", [
    pytest.param("002C", "min", "1D0200", "2000-02-29", id="leap-century-2000"),
    pytest.param("002C", "max", "1D0218", "2024-02-29", id="later-leap-2024"),
    pytest.param("0035", "max", "173B3B", "23:59:59", id="last-second"),
])
def test_valid_edges_keep_candidate_display_only(
    register: str, field: str, raw: str, text: str,
) -> None:
    document, overlay, index, record, entry = candidate(register, field, raw, text)
    decoded_before = deepcopy(record["decoded"])
    assert decoded_before["qualification"] == "qualified"  # syntax only, Hypothesis
    assert decoded_before["codec_basis"] == "public_exact_selector_schema"
    assert decoded_before["codec_provenance"] == "selector_qualified"
    assert decoded_before["step"] is None
    assert entry["validation_scope"] == "display_only"
    validator.validate_documents(document, OBSERVATIONS, CATALOG, overlay)
    assert record["decoded"] == decoded_before
    assert entry["validation_scope"] == "display_only"

    entry["validation_scope"] = "format_range_and_step"
    message = (
        f"records[{index}] grants range validation to a plain-byte "
        "DATE_DMY_U8X3/TIME_HMS_U8X3 candidate decoding, which must stay display_only"
    )
    with pytest.raises(validator.ValidationError, match=f"^{re.escape(message)}$"):
        validator.validate_documents(document, OBSERVATIONS, CATALOG, overlay)


def test_valid_leap_day_can_still_fail_range_order() -> None:
    document, overlay, index, _, _ = candidate(
        "002C", "max", "1D0200", "2000-02-29",
    )
    message = (
        f"records[{index}].decoded DATE_DMY_U8X3 "
        "min 2001-01-01 is later than max 2000-02-29"
    )
    with pytest.raises(validator.ValidationError, match=f"^{re.escape(message)}$"):
        validator.validate_documents(document, OBSERVATIONS, CATALOG, overlay)


@pytest.mark.parametrize("register,raw,text,kind", [
    pytest.param("002C", "1D0217", "2023-02-29", "date", id="non-leap-february-29"),
    pytest.param("002C", "1F0418", "2024-04-31", "date", id="april-31"),
    pytest.param("002C", "000118", "2024-01-00", "date", id="day-zero"),
    pytest.param("0035", "173C00", "23:60:00", "time", id="minute-60"),
    pytest.param("0035", "173B3C", "23:59:60", "time", id="second-60"),
])
def test_invalid_edges_reject_syntax_before_range_order(
    register: str, raw: str, text: str, kind: str,
) -> None:
    # These maxima follow the retained minima; ordering is not the rejection.
    document, overlay, index, _, _ = candidate(register, "max", raw, text)
    bounds = (
        "date (day, month, year offset 0-99 from 2000)" if kind == "date"
        else "time (hour 0-23, minute 0-59, second 0-59)"
    )
    message = f"records[{index}].decoded.max is not a valid {bounds}"
    with pytest.raises(validator.ValidationError, match=f"^{re.escape(message)}$"):
        validator.validate_documents(document, OBSERVATIONS, CATALOG, overlay)
