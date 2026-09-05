from __future__ import annotations

import importlib.util
import pathlib
import shutil

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
CHECKER_PATH = REPO_ROOT / "scripts/check_regulator_identity_contract.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("regulator_identity_checker", CHECKER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_contract_docs(destination: pathlib.Path) -> None:
    for relative in (
        "architecture/regulator-identity-enrichment.md",
        "architecture/atr/04-sn-merge-gate.md",
        "architecture/overview.md",
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, target)


def test_qualified_identity_contract_accepts_current_docs(tmp_path: pathlib.Path) -> None:
    checker = load_checker()
    copy_contract_docs(tmp_path)

    checker.validate_documents(tmp_path)


def test_qualified_identity_contract_rejects_serial_only_merge_wording(tmp_path: pathlib.Path) -> None:
    checker = load_checker()
    copy_contract_docs(tmp_path)
    path = tmp_path / "architecture/regulator-identity-enrichment.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace(
            "a serial-only match, a\nMAC-only match, or a matching model signature alone MUST NOT merge independent\naddresses.",
            "a serial-only match may merge independent addresses.",
            1,
        ),
        encoding="utf-8",
    )

    with pytest.raises(checker.CheckError, match="serial-only"):
        checker.validate_documents(tmp_path)


@pytest.mark.parametrize(
    ("rule", "relative", "contradiction"),
    (
        ("serial-only", "architecture/regulator-identity-enrichment.md", "A serial-only match MAY merge independent addresses."),
        ("partial-triple", "architecture/regulator-identity-enrichment.md", "A partial triple MAY merge independent addresses."),
        ("sentinel", "architecture/regulator-identity-enrichment.md", "A sentinel SerialNumber MAY serve as identity proof for a cross-address merge."),
        ("topology-alias", "architecture/regulator-identity-enrichment.md", "A topology alias MAY become a stable identity for independent addresses."),
        ("same-address-enrichment", "architecture/regulator-identity-enrichment.md", "Same-address partial enrichment MAY merge independent addresses."),
        ("provenance", "architecture/regulator-identity-enrichment.md", "Identity confirmation MAY rewrite static_seed provenance."),
        ("serial-only", "architecture/atr/04-sn-merge-gate.md", "Serial alone MAY merge independent addresses."),
        ("partial-triple", "architecture/atr/04-sn-merge-gate.md", "A partial triple MAY merge independent addresses."),
        ("sentinel", "architecture/atr/04-sn-merge-gate.md", "A sentinel SerialNumber MAY serve as identity proof for a cross-address merge."),
        ("topology-alias", "architecture/atr/04-sn-merge-gate.md", "A topology alias MAY become a stable identity for independent addresses."),
        ("same-address-enrichment", "architecture/atr/04-sn-merge-gate.md", "Same-address partial enrichment MAY merge independent addresses."),
        ("provenance", "architecture/atr/04-sn-merge-gate.md", "Identity confirmation MAY rewrite passive_observed provenance."),
        ("partial-triple", "architecture/overview.md", "A partial triple MAY merge independent addresses."),
        ("topology-alias", "architecture/overview.md", "A topology alias MAY become a stable identity for independent addresses."),
    ),
)
def test_qualified_identity_contract_rejects_additive_permissions(
    tmp_path: pathlib.Path, rule: str, relative: str, contradiction: str
) -> None:
    checker = load_checker()
    copy_contract_docs(tmp_path)
    path = tmp_path / relative
    path.write_text(path.read_text(encoding="utf-8") + f"\n\n{contradiction}\n", encoding="utf-8")

    expected_rule = {
        "same-address-enrichment": r"same-address.*enrichment",
    }.get(rule, rule.replace("-", "[- ]"))
    with pytest.raises(checker.CheckError, match=expected_rule):
        checker.validate_documents(tmp_path)
