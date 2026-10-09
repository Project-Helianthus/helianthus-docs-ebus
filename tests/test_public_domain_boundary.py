from pathlib import Path

import pytest

from scripts.check_public_domain_boundary import unpublishable_attribution, violations


def document(root: Path, text: str) -> None:
    path = root / "protocols" / "vendor" / "wire.md"
    path.parent.mkdir(parents=True)
    path.write_text(text)


@pytest.mark.parametrize(
    "text",
    [
        "Run scan --preset recommended",
        "The planner chooses slots",
        "Helianthus publishes GraphQL",
        "[Application](../../development/client.md)",
    ],
)
def test_rejects_application_material_in_cc0(tmp_path: Path, text: str) -> None:
    document(tmp_path, text)
    assert violations(tmp_path)


def test_keeps_wire_facts_and_source_attribution(tmp_path: Path) -> None:
    document(
        tmp_path,
        "# Wire\nRequest: 09 GG II ADDRESS CODE\n[Types](../../types/overview.md)\n## Sources\n- VRC Explorer captures (payload only)\n",
    )
    assert violations(tmp_path) == []


def test_source_section_does_not_allow_cli_arguments(tmp_path: Path) -> None:
    document(tmp_path, "## Sources\nRun --execute\n")
    assert violations(tmp_path)


def test_source_section_does_not_allow_application_contracts(tmp_path: Path) -> None:
    document(tmp_path, "## Sources\nThe GraphQL API reports planner rows\n")
    assert violations(tmp_path)


def test_application_schema_cannot_be_placed_in_cc0(tmp_path: Path) -> None:
    path = tmp_path / "protocols" / "b524-operation-reads-artifact-schema-v1.json"
    path.parent.mkdir()
    path.write_text("{}")
    assert violations(tmp_path)


def test_negative_scope_statement_is_not_application_policy(tmp_path: Path) -> None:
    document(
        tmp_path,
        "This wire reference contains no\nHelianthus scheduler, profile, qualification, gateway, or semantic policy.\n",
    )
    assert violations(tmp_path) == []


def test_checks_types_as_well_as_protocols(tmp_path: Path) -> None:
    path = tmp_path / "types" / "wire.md"
    path.parent.mkdir()
    path.write_text("Use the VRC Explorer Browser")
    assert violations(tmp_path)


def test_attribution_guard_covers_agpl_documents_too(tmp_path: Path) -> None:
    path = tmp_path / "architecture" / "contract.md"
    path.parent.mkdir()
    path.write_text("Source: UNPUBLISHED-semantic-notes.md")
    assert unpublishable_attribution(tmp_path)
