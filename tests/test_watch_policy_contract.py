from __future__ import annotations

import pathlib


ROOT = pathlib.Path(__file__).resolve().parents[1]
DOCUMENTS = (
    ROOT / "api/watch-summary.md",
    ROOT / "architecture/bus-observability-v2.md",
    ROOT / "architecture/observability.md",
)


def texts() -> tuple[str, ...]:
    return tuple(path.read_text(encoding="utf-8") for path in DOCUMENTS)


def normalized(text: str) -> str:
    return " ".join(text.split())


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
    joined = "\n".join(texts())
    for token in (
        "`catalog_miss`",
        "`never`",
        "`energy_merge_only`",
        "`unknown`",
        "configuration mismatch",
    ):
        assert token in joined


def test_config_opt_in_is_reserved_and_not_applicable_until_accepted() -> None:
    for text in texts():
        value = normalized(text)
        assert "`config_opt_in`" in value
        assert "`not_applicable`" in value
        assert "separately implemented and accepted end-to-end runtime path" in value
    assert "feature-flag normalization" in "\n".join(texts())


def test_gateway_work_is_pending_evidence_not_merge_proof() -> None:
    for text in texts():
        value = normalized(text)
        assert "helianthus-ebusgateway/issues/982" in value
        assert "helianthus-ebusgateway/pull/992" in value
        assert "pending implementation evidence" in value
