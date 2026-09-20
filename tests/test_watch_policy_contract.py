from __future__ import annotations

import pathlib

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCUMENTS = (
    ROOT / "api/watch-summary.md",
    ROOT / "architecture/bus-observability-v2.md",
    ROOT / "architecture/observability.md",
)
EXCLUDED_VALUE_BEARING_PATHS = (
    "`catalog_miss`",
    "`never`",
    "`energy_merge_only`",
    "`unknown`",
    "configuration mismatch",
)


def texts() -> tuple[str, ...]:
    return tuple(path.read_text(encoding="utf-8") for path in DOCUMENTS)


def normalized(text: str) -> str:
    return " ".join(text.split())


def require_exclusions(documents: tuple[str, ...]) -> None:
    for document, text in zip(DOCUMENTS, documents, strict=True):
        value = normalized(text)
        for token in EXCLUDED_VALUE_BEARING_PATHS:
            assert token in value, f"{document.name} omits excluded path {token}"


def test_b509_b524_passive_update_policy_is_fail_closed() -> None:
    for text in texts():
        value = normalized(text)
        assert "B509/B524" in value
        assert "active normalized canonical descriptor" in value
        assert "`request_response`" in value
        assert "`state_default`" in value
        assert "observability-only" in value
        assert "passive shadow" in value


def test_policy_excludes_each_non_default_value_bearing_path() -> None:
    require_exclusions(texts())


def test_policy_rejects_an_exclusion_omitted_from_one_document() -> None:
    current = list(texts())
    current[0] = current[0].replace("`energy_merge_only`", "`omitted_path`", 1)
    with pytest.raises(AssertionError, match="watch-summary.md omits excluded path"):
        require_exclusions(tuple(current))


def test_config_opt_in_is_reserved_and_not_applicable_until_accepted() -> None:
    for text in texts():
        value = normalized(text)
        assert "`config_opt_in`" in value
        assert "`not_applicable`" in value
        assert "separately implemented and accepted end-to-end runtime path" in value
    assert "feature-flag normalization" in "\n".join(texts())


def test_gateway_tracking_is_not_status_evidence() -> None:
    for text in texts():
        value = normalized(text)
        assert "helianthus-ebusgateway/issues/982" in value
        assert "helianthus-ebusgateway/pull/992" in value
        assert "documentation alone do not establish merge or runtime qualification" in value
        assert "current GitHub state and merged gateway code establish implementation status" in value
        assert "pending implementation evidence" not in value
