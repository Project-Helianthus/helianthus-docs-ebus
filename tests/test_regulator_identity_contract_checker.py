from __future__ import annotations

import importlib.util
import pathlib
import re
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
        "api/graphql.md",
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


@pytest.mark.parametrize(
    ("relative", "required_fragment"),
    (
        (
            "api/graphql.md",
            "A cross-address identity merge is permitted only when the exact normalized\n"
            "  `(Manufacturer, DeviceID, SerialNumber)` triple matches.",
        ),
        (
            "architecture/regulator-identity-enrichment.md",
            "A current-session active scan MAY promote that\n"
            "face to `active_confirmed`/`identity_confirmed` without establishing a\n"
            "cross-address stable identity.",
        ),
        (
            "architecture/atr/04-sn-merge-gate.md",
            "A current-session\n"
            "active scan MAY promote that face to `active_confirmed`/`identity_confirmed`\n"
            "without establishing a cross-address stable identity.",
        ),
    ),
)
def test_qualified_identity_contract_rejects_deleted_new_boundary(
    tmp_path: pathlib.Path, relative: str, required_fragment: str
) -> None:
    checker = load_checker()
    copy_contract_docs(tmp_path)
    path = tmp_path / relative
    path.write_text(path.read_text(encoding="utf-8").replace(required_fragment, "", 1), encoding="utf-8")

    with pytest.raises(checker.CheckError, match="missing required"):
        checker.validate_documents(tmp_path)


@pytest.mark.parametrize(
    ("rule", "relative", "contradiction"),
    (
        (
            "GraphQL legacy manufacturer-plus-serial-or-MAC merge",
            "api/graphql.md",
            "A shared manufacturer + serial number MAY merge faces even when DeviceID values differ.",
        ),
        (
            "GraphQL legacy manufacturer-plus-serial-or-MAC merge",
            "api/graphql.md",
            "A shared manufacturer + MAC address MAY merge faces even when DeviceID values differ.",
        ),
        (
            "active-scan confirmation as cross-address identity",
            "architecture/regulator-identity-enrichment.md",
            "An active scan MAY establish a cross-address stable identity.",
        ),
        (
            "active-scan confirmation blocked by complete-triple gate",
            "architecture/atr/04-sn-merge-gate.md",
            "A static candidate becomes identity_confirmed only after a complete qualified observation.",
        ),
    ),
)
def test_qualified_identity_contract_rejects_new_additive_contradictions(
    tmp_path: pathlib.Path, rule: str, relative: str, contradiction: str
) -> None:
    checker = load_checker()
    copy_contract_docs(tmp_path)
    path = tmp_path / relative
    path.write_text(path.read_text(encoding="utf-8") + f"\n\n{contradiction}\n", encoding="utf-8")

    with pytest.raises(checker.CheckError, match=re.escape(rule)):
        checker.validate_documents(tmp_path)


@pytest.mark.parametrize(
    ("relative", "required_fragment"),
    (
        (
            "architecture/regulator-identity-enrichment.md",
            "## Canonical Qualified-Identity Normalization",
        ),
        (
            "architecture/atr/04-sn-merge-gate.md",
            "Before equality, the decoder removes only terminal NUL (`0x00`) and ASCII-space\n"
            "(`0x20`) padding from a fixed-width native `DeviceID`; the registry does not\n"
            "remove NUL padding.",
        ),
        (
            "api/graphql.md",
            "exported as model/provider metadata for the canonical entry. Before that exact\n"
            "  comparison, fixed-width native `DeviceID` decoding removes only terminal NUL\n"
            "  (`0x00`) and ASCII-space (`0x20`) padding; the registry separately trims outer\n"
            "  Unicode whitespace and folds case for all three members while preserving\n"
            "  internal punctuation. `VR_71` and `VR71` therefore remain distinct; a GraphQL\n"
            "  selector, display label, or product code does not create identity equivalence.",
        ),
    ),
)
def test_qualified_identity_contract_rejects_deleted_normalization_boundary(
    tmp_path: pathlib.Path, relative: str, required_fragment: str
) -> None:
    checker = load_checker()
    copy_contract_docs(tmp_path)
    path = tmp_path / relative
    path.write_text(path.read_text(encoding="utf-8").replace(required_fragment, "", 1), encoding="utf-8")

    with pytest.raises(checker.CheckError, match="missing required"):
        checker.validate_documents(tmp_path)


@pytest.mark.parametrize(
    ("rule", "relative", "contradiction"),
    (
        (
            "selector punctuation identity collapse",
            "architecture/regulator-identity-enrichment.md",
            "VR_71 and VR71 MAY compare equal for a cross-address merge.",
        ),
        (
            "registry NUL-padding removal",
            "architecture/atr/04-sn-merge-gate.md",
            "The registry identity normalizer MAY remove NUL padding.",
        ),
    ),
)
def test_qualified_identity_contract_rejects_normalization_overreach(
    tmp_path: pathlib.Path, rule: str, relative: str, contradiction: str
) -> None:
    checker = load_checker()
    copy_contract_docs(tmp_path)
    path = tmp_path / relative
    path.write_text(path.read_text(encoding="utf-8") + f"\n\n{contradiction}\n", encoding="utf-8")

    with pytest.raises(checker.CheckError, match=re.escape(rule)):
        checker.validate_documents(tmp_path)


@pytest.mark.parametrize(
    ("relative", "compatible_prohibition"),
    (
        (
            "architecture/regulator-identity-enrichment.md",
            "Serial alone MUST never merge independent addresses.",
        ),
        (
            "architecture/atr/04-sn-merge-gate.md",
            "Identity confirmation MUST never rewrite static_seed provenance.",
        ),
    ),
)
def test_qualified_identity_contract_accepts_must_never_prohibitions(
    tmp_path: pathlib.Path, relative: str, compatible_prohibition: str
) -> None:
    checker = load_checker()
    copy_contract_docs(tmp_path)
    path = tmp_path / relative
    path.write_text(path.read_text(encoding="utf-8") + f"\n\n{compatible_prohibition}\n", encoding="utf-8")

    checker.validate_documents(tmp_path)


@pytest.mark.parametrize(
    "permission",
    (
        "MAY",
        "can",
        "is permitted to",
        "MUST",
    ),
)
def test_qualified_identity_contract_rejects_affirmative_permission_tokens(
    tmp_path: pathlib.Path, permission: str
) -> None:
    checker = load_checker()
    copy_contract_docs(tmp_path)
    path = tmp_path / "architecture/regulator-identity-enrichment.md"
    path.write_text(
        path.read_text(encoding="utf-8") + f"\n\nSerial alone {permission} merge independent addresses.\n",
        encoding="utf-8",
    )

    with pytest.raises(checker.CheckError, match="serial-only"):
        checker.validate_documents(tmp_path)


@pytest.mark.parametrize(
    ("relative", "compatible_prohibition"),
    (
        (
            "architecture/regulator-identity-enrichment.md",
            "Serial alone MAY NOT merge independent addresses.",
        ),
        (
            "architecture/atr/04-sn-merge-gate.md",
            "A sentinel serial MAY never serve as identity proof.",
        ),
        (
            "architecture/regulator-identity-enrichment.md",
            "Serial alone can\tNEVER merge independent addresses.",
        ),
        (
            "architecture/regulator-identity-enrichment.md",
            "Serial alone is permitted to NOT merge independent addresses.",
        ),
        (
            "architecture/regulator-identity-enrichment.md",
            "Serial alone MUST not merge independent addresses.",
        ),
    ),
)
def test_qualified_identity_contract_accepts_negated_permission_tokens(
    tmp_path: pathlib.Path, relative: str, compatible_prohibition: str
) -> None:
    checker = load_checker()
    copy_contract_docs(tmp_path)
    path = tmp_path / relative
    path.write_text(
        path.read_text(encoding="utf-8") + f"\n\n{compatible_prohibition}\n", encoding="utf-8"
    )

    checker.validate_documents(tmp_path)
