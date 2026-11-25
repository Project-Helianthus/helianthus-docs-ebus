#!/usr/bin/env python3
"""Prior-owner pins Docs Checks resolves from the trusted base workflow.

The resolver is the program embedded in the Docs CI workflow. This module
only asserts that program. A change here does not change the prior manifest
Docs Checks passes on.
"""

from __future__ import annotations

import functools
import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/docs-ci.yml"
CANDIDATE = "a" * 40
RECORDED = "b" * 40
LEGACY = "c" * 40
OTHER = "d" * 40
PROGRAM_NAMES = (
    "recorded_prior_refs",
    "verify_prior_heads",
    "materialize_pre_split",
    "main",
    "OUTPUT_KEYS",
    "SHA",
    "RUNTIME_RELATIVE_PATHS",
    "PIN_RELATIVE_PATHS",
)
PROGRAM_PATTERN = re.compile(
    r"(?m)^(?P<indent>[ ]*)cat > \"\$\{RUNNER_TEMP\}/prior_owner_pins\.py\" "
    r"<<'PRIOR_OWNER_PINS'\n(?P<body>.*?)\n(?P=indent)PRIOR_OWNER_PINS$",
    re.S,
)


def prior_owner_program_source(text: str) -> str:
    """Return the resolver program embedded in a Docs CI workflow."""
    if "tests/test_prior_owner_pins.py" in text:
        raise AssertionError("Docs CI still runs the prior-owner test module")
    match = PROGRAM_PATTERN.search(text)
    if match is None:
        raise AssertionError("Docs CI does not embed the prior-owner program")
    indent = match.group("indent")
    body = []
    for line in match.group("body").splitlines():
        if line == "" or line.startswith(indent):
            body.append(line[len(indent):] if line else "")
        else:
            raise AssertionError("prior-owner program is not in the workflow block")
    return "\n".join(body) + "\n"


@functools.lru_cache(maxsize=1)
def load_prior_owner_program() -> dict[str, object]:
    """Load the workflow program. Missing product entry points fail closed."""
    namespace: dict[str, object] = {"__name__": "prior_owner_pins"}
    source = prior_owner_program_source(WORKFLOW.read_text(encoding="utf-8"))
    exec(compile(source, "docs-ci.yml prior_owner_pins", "exec"), namespace)
    missing = [name for name in PROGRAM_NAMES if name not in namespace]
    if missing:
        raise AssertionError("prior-owner program is missing " + ", ".join(missing))
    return namespace


def test_loader_rejects_a_workflow_that_calls_the_test_module():
    try:
        prior_owner_program_source("python3 tests/test_prior_owner_pins.py\n")
    except AssertionError as error:
        assert "test module" in str(error)
    else:
        raise AssertionError("test-module invocation was accepted")


def test_docs_ci_invokes_the_embedded_program_not_the_test_module():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "tests/test_prior_owner_pins.py" not in text
    assert text.count('python3 "${RUNNER_TEMP}/prior_owner_pins.py"') == 4
    program = load_prior_owner_program()
    assert callable(program["recorded_prior_refs"])
    assert callable(program["verify_prior_heads"])
    assert callable(program["materialize_pre_split"])
    assert callable(program["main"])


def test_test_module_keeps_only_assertions():
    source = Path(__file__).read_text(encoding="utf-8")
    for name in ("recorded_prior_refs", "verify_prior_heads", "materialize_pre_split"):
        assert "def " + name not in source


def test_recorded_checkout_pin_is_not_the_prior_step_or_the_candidate():
    recorded_prior_refs = load_prior_owner_program()["recorded_prior_refs"]
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
    recorded_prior_refs = load_prior_owner_program()["recorded_prior_refs"]
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
    recorded_prior_refs = load_prior_owner_program()["recorded_prior_refs"]
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
    assert "docs_modbus_prior_ref" not in refs
    assert refs["docs_ebus_pin_prior_ref"] == ""


def test_checkout_pin_wins_over_the_legacy_eebus_input():
    recorded_prior_refs = load_prior_owner_program()["recorded_prior_refs"]
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


def test_main_writes_recorded_refs_to_github_output(tmp_path: Path):
    main = load_prior_owner_program()["main"]
    workflow = tmp_path / "docs-ci.yml"
    workflow.write_text(
        f"""
      - name: Checkout helianthus-docs
        uses: actions/checkout@example
        with:
          repository: Project-Helianthus/helianthus-docs
          ref: {RECORDED}
          path: checkouts/docs
""",
        encoding="utf-8",
    )
    output = tmp_path / "github-output.txt"
    status = main(["--base-workflow", str(workflow), "--github-output", str(output)])
    assert status == 0
    written = output.read_text(encoding="utf-8")
    assert f"docs_prior_ref={RECORDED}\n" in written
    assert "docs_modbus_prior_ref" not in written
    assert "docs_eebus_prior_ref=\n" in written
    assert "docs_ebus_pin_prior_ref=\n" in written


def test_main_requires_github_output_with_a_base_workflow(tmp_path: Path):
    main = load_prior_owner_program()["main"]
    workflow = tmp_path / "docs-ci.yml"
    workflow.write_text("docs_eebus_ref: " + LEGACY + "\n", encoding="utf-8")
    try:
        main(["--base-workflow", str(workflow)])
    except SystemExit as error:
        assert "github-output" in str(error)
    else:
        raise AssertionError("missing github output was accepted")


def test_materialize_pre_split_copies_operands_and_rejects_a_missing_one(tmp_path: Path):
    program = load_prior_owner_program()
    materialize_pre_split = program["materialize_pre_split"]
    source = tmp_path / "base"
    for relative in program["RUNTIME_RELATIVE_PATHS"]:
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
    program = load_prior_owner_program()
    outside = tmp_path / "outside.md"
    outside.write_text("stale", encoding="utf-8")
    link = tmp_path / "base" / program["PIN_RELATIVE_PATHS"][0]
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(outside)
    try:
        program["materialize_pre_split"](tmp_path / "base", tmp_path / "pin-prior", "pin")
    except SystemExit as error:
        assert program["PIN_RELATIVE_PATHS"][0] in str(error)
    else:
        raise AssertionError("symlinked historical operand was accepted")


def test_verify_prior_head_rejects_a_different_revision(tmp_path: Path):
    verify_prior_heads = load_prior_owner_program()["verify_prior_heads"]
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
    load_prior_owner_program()["verify_prior_heads"](tmp_path, {"docs_prior_ref": ""})


def test_public_docs_ci_checks_out_the_pinned_modbus_companion():
    text = WORKFLOW.read_text(encoding="utf-8")
    program = load_prior_owner_program()
    source = prior_owner_program_source(text)
    assert not source.lstrip().startswith("#!")
    steps = {step["name"]: step for step in yaml.safe_load(text)["jobs"]["markdown-checks"]["steps"]}
    run = steps["Run local docs CI"]
    assert run["working-directory"] == "checkouts/docs-ebus"
    assert run["env"]["PLATFORM_DOCS_MODBUS_ROOT"] == ""
    local_gate = (ROOT / "scripts/ci_local.sh").read_text(encoding="utf-8")
    pin = re.search(r"^docs_modbus_ref=(\S+)$", local_gate, re.M)
    assert pin is not None and program["SHA"].fullmatch(pin[1])
    assert 'PLATFORM_DOCS_MODBUS_ROOT="${gate_temp_dir}/checkouts/docs-modbus"' in local_gate
    assert 'env -i "PATH=${PATH}" GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null GIT_TERMINAL_PROMPT=0 git' in local_gate
    assert (
        '"${public_git[@]}" -C "${PLATFORM_DOCS_MODBUS_ROOT}" fetch --depth 1 \\\n'
        '    https://github.com/Project-Helianthus/helianthus-docs-modbus.git "${docs_modbus_ref}"'
    ) in local_gate
    assert '"${public_git[@]}" -C "${PLATFORM_DOCS_MODBUS_ROOT}" checkout --detach FETCH_HEAD' in local_gate
    assert 'rev-parse --verify HEAD)" != "${docs_modbus_ref}"' in local_gate
    for forbidden in (
        "PLATFORM_DOCS_MODBUS_PRIOR_ROOT",
        "docs_modbus_prior_ref",
        "REPO_READ_TOKEN",
        "--modbus-ref",
    ):
        assert forbidden not in text
    assert program["OUTPUT_KEYS"] == (
        "docs_prior_ref",
        "docs_eebus_prior_ref",
        "docs_ebus_pin_prior_ref",
    )
    assert "repository: Project-Helianthus/helianthus-docs\n" in text
    assert "repository: Project-Helianthus/helianthus-docs-eebus\n" in text
    assert "path: checkouts/docs-eebus\n" in text
    assert "path: checkouts/docs-eebus-prior\n" in text
    assert "run: ./scripts/ci_local.sh\n" in text
    assert ".github/workflows/modbus-trusted-revision.yml" in text
    assert ".github/workflows/modbus-trusted-revision-pr.yml" in text
    for workflow_name in (
        ".github/workflows/modbus-trusted-revision.yml",
        ".github/workflows/modbus-trusted-revision-pr.yml",
    ):
        assert "Modbus Trusted Revision" in (ROOT / workflow_name).read_text(encoding="utf-8")


def test_workflow_prior_refs_come_from_the_trusted_base():
    program = load_prior_owner_program()
    text = WORKFLOW.read_text(encoding="utf-8")
    refs = program["recorded_prior_refs"](text)
    for key in program["OUTPUT_KEYS"]:
        pin = refs[key]
        assert program["SHA"].fullmatch(pin)
        assert text.count(pin) == 2
        assert f"ref: ${{{{ steps.prior_owners.outputs.{key} }}}}" in text
    assert 'TRUSTED_BASE_REF="$(git -C "${base_root}" rev-parse HEAD)"' not in text
    assert "PRIOR_EEBUS_REF" in text
    assert "tests/test_prior_owner_pins.py" not in text
