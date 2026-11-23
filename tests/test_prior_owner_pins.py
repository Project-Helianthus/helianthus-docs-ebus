#!/usr/bin/env python3
"""Prior owner revisions recorded by the trusted base workflow.

Docs CI calls this module. Candidate checkouts keep the pins in the head
workflow. A pull request's prior checkouts use the revisions that workflow
recorded at the trusted base. On the first split that base has no companion
checkout, so the eeBUS prior is its recorded docs_eebus_ref and the other
owners stay empty for the pre-split tree. A nightly or push run reads the
candidate workflow, which is the same-head pair.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/docs-ci.yml"
SHA = re.compile(r"^[0-9a-f]{40}$")
CHECKOUT_REFS = {
    "checkouts/docs": "docs_prior_ref",
    "checkouts/docs-modbus": "docs_modbus_prior_ref",
    "checkouts/docs-eebus": "docs_eebus_prior_ref",
    "checkouts/docs-ebus-pin": "docs_ebus_pin_prior_ref",
}
OUTPUT_KEYS = (
    "docs_prior_ref",
    "docs_modbus_prior_ref",
    "docs_eebus_prior_ref",
    "docs_ebus_pin_prior_ref",
)
PRIOR_CHECKOUTS = {
    "docs_prior_ref": "checkouts/docs-prior",
    "docs_modbus_prior_ref": "checkouts/docs-modbus-prior",
    "docs_eebus_prior_ref": "checkouts/docs-eebus-prior",
    "docs_ebus_pin_prior_ref": "checkouts/docs-ebus-pin-prior",
}
RUNTIME_RELATIVE_PATHS = (
    "api/mcp.md",
    "api/driver-runtime-v1.md",
    "api/portal.md",
    "architecture/runtime-driver-lifecycle.md",
    "architecture/runtime-state.md",
    "architecture/runtime-control-reset-durability.md",
    "docs/platform/driver-runtime-manager-v1.md",
    "scripts/check_runtime_control_contract.py",
    "scripts/runtime_control_contract.json",
    "tests/test_runtime_control_contract.py",
    "scripts/ci_local.sh",
)
PIN_RELATIVE_PATHS = ("api/modbus-v1-addon-runtime.md",)
CANDIDATE = "a" * 40
RECORDED = "b" * 40
LEGACY = "c" * 40
OTHER = "d" * 40


def recorded_prior_refs(workflow_text: str) -> dict[str, str]:
    """Return prior refs from checkout pins, then the pre-split eeBUS input."""
    refs = {key: "" for key in OUTPUT_KEYS}
    pending: dict[str, str] = {}
    in_with = False

    def consume() -> None:
        path = pending.get("path", "")
        ref = pending.get("ref", "")
        output = CHECKOUT_REFS.get(path)
        if output and SHA.fullmatch(ref):
            refs[output] = ref

    for line in workflow_text.splitlines():
        if re.match(r"^\s*- (?:name|uses):", line):
            consume()
            pending = {}
            in_with = False
            continue
        if re.match(r"^\s+with:\s*$", line):
            in_with = True
            continue
        if not in_with:
            continue
        match = re.match(r"^\s+(repository|ref|path):\s+(\S+)\s*$", line)
        if match:
            pending[match.group(1)] = match.group(2)
    consume()
    if not refs["docs_eebus_prior_ref"]:
        legacy = re.search(r"(?m)^\s*docs_eebus_ref:\s+([0-9a-f]{40})\s*$", workflow_text)
        if legacy:
            refs["docs_eebus_prior_ref"] = legacy.group(1)
    return refs


def verify_prior_heads(workspace: Path, refs: dict[str, str]) -> None:
    """Fail unless each recorded prior checkout is that exact revision."""
    for key, relative in PRIOR_CHECKOUTS.items():
        recorded = refs.get(key, "")
        if not recorded:
            continue
        checkout = workspace / relative
        if not checkout.is_dir():
            raise SystemExit(f"{relative} prior checkout is missing")
        head = subprocess.check_output(
            ["git", "-C", str(checkout), "rev-parse", "--verify", "HEAD"],
            text=True,
        ).strip()
        if head != recorded:
            raise SystemExit(f"{relative} prior HEAD does not match the trusted base pin")


def materialize_pre_split(source: Path, dest: Path, kind: str) -> None:
    """Copy pre-split operands. A missing file is a failed prior, not an empty pass."""
    paths = RUNTIME_RELATIVE_PATHS if kind == "runtime" else PIN_RELATIVE_PATHS
    for relative in paths:
        src = source / relative
        if src.is_symlink() or not src.is_file():
            raise SystemExit(f"historical operand missing: {relative}")
        target = dest / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(src.read_bytes())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-workflow", type=Path)
    parser.add_argument("--github-output", type=Path)
    parser.add_argument("--verify-prior-heads", action="store_true")
    parser.add_argument("--workspace", type=Path)
    parser.add_argument("--docs-ref", default="")
    parser.add_argument("--modbus-ref", default="")
    parser.add_argument("--eebus-ref", default="")
    parser.add_argument("--ebus-pin-ref", default="")
    parser.add_argument("--materialize-pre-split", choices=("runtime", "pin"))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--dest", type=Path)
    args = parser.parse_args(argv)
    if args.base_workflow is not None:
        if args.github_output is None:
            raise SystemExit("--github-output is required")
        refs = recorded_prior_refs(args.base_workflow.read_text(encoding="utf-8"))
        with args.github_output.open("a", encoding="utf-8") as handle:
            for key in OUTPUT_KEYS:
                handle.write(f"{key}={refs[key]}\n")
    if args.verify_prior_heads:
        if args.workspace is None:
            raise SystemExit("--workspace is required")
        verify_prior_heads(
            args.workspace,
            {
                "docs_prior_ref": args.docs_ref,
                "docs_modbus_prior_ref": args.modbus_ref,
                "docs_eebus_prior_ref": args.eebus_ref,
                "docs_ebus_pin_prior_ref": args.ebus_pin_ref,
            },
        )
    if args.materialize_pre_split:
        if args.source is None or args.dest is None:
            raise SystemExit("--source and --dest are required")
        materialize_pre_split(args.source, args.dest, args.materialize_pre_split)
    return 0


def test_recorded_checkout_pin_is_not_the_prior_step_or_the_candidate():
    workflow = f"""
      - name: Checkout helianthus-docs
        uses: actions/checkout@example
        with:
          repository: Project-Helianthus/helianthus-docs
          ref: {RECORDED}
          path: checkouts/docs
      - name: Checkout helianthus-docs prior
        uses: actions/checkout@example
        with:
          repository: Project-Helianthus/helianthus-docs
          ref: {CANDIDATE}
          path: checkouts/docs-prior
    """
    refs = recorded_prior_refs(workflow)
    assert refs["docs_prior_ref"] == RECORDED
    assert refs["docs_prior_ref"] != CANDIDATE


def test_expression_ref_is_not_a_recorded_pin():
    workflow = """
      - name: Checkout helianthus-docs
        uses: actions/checkout@example
        with:
          repository: Project-Helianthus/helianthus-docs
          ref: ${{ steps.prior_owners.outputs.docs_prior_ref }}
          path: checkouts/docs
    """
    assert recorded_prior_refs(workflow)["docs_prior_ref"] == ""


def test_first_split_uses_the_base_eebus_input_and_leaves_other_owners_empty():
    workflow = f"""
      - name: Checkout M6.25 provenance sources
        uses: actions/checkout@example
        with:
          repository: Project-Helianthus/helianthus-docs-eebus
          ref: {OTHER}
          path: checkouts/m625-docs-eebus
      docs_eebus_ref: {LEGACY}
    """
    refs = recorded_prior_refs(workflow)
    assert refs["docs_eebus_prior_ref"] == LEGACY
    assert refs["docs_prior_ref"] == ""
    assert refs["docs_modbus_prior_ref"] == ""
    assert refs["docs_ebus_pin_prior_ref"] == ""


def test_checkout_pin_wins_over_the_legacy_eebus_input():
    workflow = f"""
      - name: Checkout helianthus-docs-eebus
        uses: actions/checkout@example
        with:
          repository: Project-Helianthus/helianthus-docs-eebus
          ref: {RECORDED}
          path: checkouts/docs-eebus
      docs_eebus_ref: {LEGACY}
    """
    assert recorded_prior_refs(workflow)["docs_eebus_prior_ref"] == RECORDED


def test_materialize_pre_split_copies_operands_and_rejects_a_missing_one(tmp_path: Path):
    source = tmp_path / "base"
    for relative in RUNTIME_RELATIVE_PATHS:
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative, encoding="utf-8")
    dest = tmp_path / "docs-prior"
    materialize_pre_split(source, dest, "runtime")
    assert (dest / "api/mcp.md").read_text(encoding="utf-8") == "api/mcp.md"
    (source / "api/mcp.md").unlink()
    try:
        materialize_pre_split(source, tmp_path / "again", "runtime")
    except SystemExit as error:
        assert "api/mcp.md" in str(error)
    else:
        raise AssertionError("missing historical operand was accepted")


def test_materialize_pre_split_rejects_a_symlink(tmp_path: Path):
    source = tmp_path / "base"
    outside = tmp_path / "outside.md"
    outside.write_text("stale", encoding="utf-8")
    link = source / PIN_RELATIVE_PATHS[0]
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside)
    try:
        materialize_pre_split(source, tmp_path / "pin-prior", "pin")
    except SystemExit as error:
        assert PIN_RELATIVE_PATHS[0] in str(error)
    else:
        raise AssertionError("symlinked historical operand was accepted")


def test_verify_prior_head_rejects_a_different_revision(tmp_path: Path):
    checkout = tmp_path / "checkouts" / "docs-eebus-prior"
    checkout.mkdir(parents=True)
    subprocess.check_call(["git", "init", checkout], stdout=subprocess.DEVNULL)
    subprocess.check_call(["git", "-C", checkout, "config", "user.email", "prior@example.com"])
    subprocess.check_call(["git", "-C", checkout, "config", "user.name", "prior"])
    subprocess.check_call(["git", "-C", checkout, "config", "commit.gpgsign", "false"])
    (checkout / "manifest").write_text("prior\n", encoding="utf-8")
    subprocess.check_call(["git", "-C", checkout, "add", "manifest"])
    subprocess.check_call(["git", "-C", checkout, "commit", "-m", "prior"], stdout=subprocess.DEVNULL)
    head = subprocess.check_output(["git", "-C", checkout, "rev-parse", "HEAD"], text=True).strip()
    verify_prior_heads(tmp_path, {"docs_eebus_prior_ref": head})
    try:
        verify_prior_heads(tmp_path, {"docs_eebus_prior_ref": OTHER})
    except SystemExit as error:
        assert "does not match" in str(error)
    else:
        raise AssertionError("a different prior revision was accepted")


def test_empty_prior_ref_skips_the_head_check(tmp_path: Path):
    verify_prior_heads(tmp_path, {"docs_prior_ref": ""})


def test_workflow_prior_refs_come_from_the_trusted_base():
    text = WORKFLOW.read_text(encoding="utf-8")
    refs = recorded_prior_refs(text)
    for key in OUTPUT_KEYS:
        pin = refs[key]
        assert SHA.fullmatch(pin)
        assert text.count(pin) == 2
        output = key
        assert f"ref: ${{{{ steps.prior_owners.outputs.{output} }}}}" in text
    assert 'TRUSTED_BASE_REF="$(git -C "${base_root}" rev-parse HEAD)"' not in text
    assert "PRIOR_EEBUS_REF" in text
    assert "test_prior_owner_pins.py" in text


if __name__ == "__main__":
    sys.exit(main())
