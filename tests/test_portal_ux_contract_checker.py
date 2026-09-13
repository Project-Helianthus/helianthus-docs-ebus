from __future__ import annotations

import importlib.util
import pathlib

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "portal_ux_contract", ROOT / "scripts/check_portal_ux_contract.py"
)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def contract() -> str:
    return (ROOT / "api/portal.md").read_text(encoding="utf-8")


def rejects(old: str, new: str) -> None:
    text = contract()
    assert old in text
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text.replace(old, new, 1))


def test_accepts_current_portal_ux_contract() -> None:
    CHECKER.validate_text(contract())


@pytest.mark.parametrize(
    ("old", "new"),
    (
        ('data-testid="b503-state-unknown"', 'data-testid="b503-state-pending"'),
        ('data-testid="b503-session-strip"', 'data-testid="b503-session"'),
        ('data-testid="b503-install-writes-banner"', 'data-testid="install-writes"'),
        ("no REST compatibility shim", "a REST compatibility shim"),
        ("no direct MCP/native fallback", "a direct MCP/native fallback"),
        ("must not require a vendor switch", "may require a vendor switch"),
        ("an arbitrary-English parser", "a label parser"),
        ("Gateway #552 is open;", "Gateway #552 is implemented;"),
        ("real installation/device write still needs action-time operator confirmation.",
         "real installation/device write is enabled by this banner."),
    ),
)
def test_rejects_contract_regressions(old: str, new: str) -> None:
    rejects(old, new)
