from __future__ import annotations

import importlib.util
import pathlib

import pytest


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "vaillant_b503_milestones", ROOT / "scripts/check_vaillant_b503_milestones.py"
)
assert SPEC is not None and SPEC.loader is not None
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def contract() -> str:
    return (ROOT / "protocols/vaillant/ebus-vaillant-B503.md").read_text(encoding="utf-8")


def table_row(cells: tuple[str, ...]) -> str:
    return f"| {' | '.join(cells)} |"


def test_accepts_current_b503_milestone_contract() -> None:
    CHECKER.validate_text(contract())


def test_rejects_old_all_read_only_milestone_contradiction() -> None:
    text = contract().replace(
        table_row(CHECKER.M2B_GRAPHQL),
        table_row(CHECKER.FORBIDDEN_ALL_READ_ONLY_MILESTONES[0]),
        1,
    ).replace(
        table_row(CHECKER.M3_PORTAL),
        table_row(CHECKER.FORBIDDEN_ALL_READ_ONLY_MILESTONES[1]),
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_missing_install_write_non_exposure() -> None:
    text = contract().replace(CHECKER.INSTALL_WRITE_NON_EXPOSURE, "", 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_install_write_non_exposure_copied_outside_normative_section() -> None:
    text = contract().replace(CHECKER.INSTALL_WRITE_NON_EXPOSURE, "", 1)
    text += f"\n{CHECKER.INSTALL_WRITE_NON_EXPOSURE}\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize(
    "replacement",
    (
        "four stable states: `Idle`, `Enabling`, `Active`, and `Disabled`.",
        "`Disabled` may be reported with `owned:true`.",
    ),
)
def test_rejects_missing_refreshing_or_disabled_ownership_contract(
    replacement: str,
) -> None:
    text = contract().replace(CHECKER.SESSION_STATE_CONTRACT, replacement, 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize("clause", CHECKER.FORBIDDEN_SESSION_STATE_CLAUSES)
def test_rejects_session_state_contradiction_inside_normative_section(
    clause: str,
) -> None:
    text = contract().replace(
        CHECKER.SESSION_SECTION_END,
        f"{clause}\n\n{CHECKER.SESSION_SECTION_END}",
        1,
    )
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


@pytest.mark.parametrize("expected", (CHECKER.M2B_GRAPHQL, CHECKER.M3_PORTAL))
def test_rejects_required_milestone_row_copied_after_milestone_table(
    expected: tuple[str, ...],
) -> None:
    stale_row = (expected[0], expected[1], "stale row")
    text = contract().replace(
        table_row(expected), table_row(stale_row), 1
    ) + f"\n{table_row(expected)}\n"
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)


def test_rejects_required_m3_cells_moved_to_the_wrong_milestone_row() -> None:
    wrong_row = (
        "`M1_DECODER`",
        CHECKER.M3_PORTAL[1],
        CHECKER.M3_PORTAL[2],
    )
    text = contract().replace(table_row(CHECKER.M3_PORTAL), table_row(wrong_row), 1)
    with pytest.raises(CHECKER.CheckError):
        CHECKER.validate_text(text)
