from pathlib import Path
import subprocess
import sys

import pytest

from scripts import check_runtime_driver_registration as checker


ROOT = Path(__file__).resolve().parents[1]
TEXT = (ROOT / checker.DOCUMENT).read_text(encoding="utf-8")


def test_runtime_driver_registration_repository_contract() -> None:
    assert checker.validate(TEXT) == []


@pytest.mark.parametrize("name", checker.REQUIREMENTS)
def test_runtime_driver_registration_rejects_missing_obligation(name: str) -> None:
    required = checker.REQUIREMENTS[name]
    assert TEXT.count(required) == 1
    assert name in checker.validate(TEXT.replace(required, ""))


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("at most 128 bytes", "at most 256 bytes"),
        ("^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$", "^[a-z]+$"),
        ("Exactly `southbound`, `northbound` or `both`", "Any direction"),
        ("including disabled entries", "excluding disabled entries"),
        ("freeze\ndetached copies", "retain\ncaller-owned copies"),
        (
            "hub-source collisions\nrefuse registration",
            "hub-source collisions\nallow registration",
        ),
        ("Failure installs no partial registry", "Failure installs a partial registry"),
        (
            "Unknown hook names and unsupported versions fail explicitly",
            "Unknown hook names and unsupported versions are ignored",
        ),
        ("declarations currently fail**", "declarations currently pass**"),
        ("sorted bytewise", "in registration order"),
        ("one coherent read transaction", "separate read transactions"),
        ("`NOT_FOUND`", "an empty entry"),
        ("is the only production registration", "is a production registration"),
        ("Those values are **Unknown**", "Those values are **Proven**"),
        (
            "not executed tests or wire-evidence claims",
            "executed tests and wire-evidence claims",
        ),
    ],
)
def test_runtime_driver_registration_rejects_weakened_clause(
    before: str, after: str
) -> None:
    assert before in TEXT
    assert checker.validate(TEXT.replace(before, after))


def test_runtime_driver_registration_ignores_line_wrapping() -> None:
    rewrapped = "\n\n".join(
        checker.normalize(block) if not block.startswith(("|", "#")) else block
        for block in TEXT.split("\n\n")
    )
    assert checker.validate(rewrapped) == []


@pytest.mark.parametrize("wrapper", ["{}", "<!--\n{}\n-->", "```text\n{}\n```"])
def test_runtime_driver_registration_rejects_decoys(wrapper: str) -> None:
    required = checker.REQUIREMENTS["validation and freeze"]
    changed = TEXT.replace(required, "Validation is optional.")
    # A retained copy elsewhere, in a comment, or in an example cannot satisfy
    # the normative paragraph in S0.
    if wrapper == "{}":
        changed += "\n\n" + required
    else:
        changed = changed.replace("Validation is optional.", wrapper.format(required))
    assert "validation and freeze" in checker.validate(changed)


@pytest.mark.parametrize("name", checker.REQUIREMENTS)
@pytest.mark.parametrize(
    "wrapper",
    [
        "    {}",
        "\t{}",
        "~~~text\n\n{}\n\n~~~",
        "   ~~~~text\n\n{}\n\n   ~~~~",
        "   ````text\n\n{}\n\n   ````",
        "~~~~text\n~~~\n\n{}\n\n~~~~",
        "````text\n```\n\n{}\n\n````",
        "~~~text\n```\n\n{}\n\n~~~",
    ],
)
def test_runtime_driver_registration_rejects_code_blocks(
    name: str, wrapper: str
) -> None:
    required = checker.REQUIREMENTS[name]
    if wrapper in {"    {}", "\t{}"}:
        example = "\n".join(wrapper.format(line) for line in required.splitlines())
    else:
        example = wrapper.format(required)
    changed = TEXT.replace(required, "\n\n" + example + "\n\n")
    assert name in checker.validate(changed)


@pytest.mark.parametrize("fence", ["```", "~~~"])
def test_runtime_driver_registration_ignores_code_block_headings(fence: str) -> None:
    example = f"\n\n{fence}\n{checker.START}\n{checker.END}\n{fence}\n"
    assert checker.validate(TEXT + example) == []


@pytest.mark.parametrize("name", checker.REQUIREMENTS)
@pytest.mark.parametrize("tag", ["pre", "PRE", 'pre class="example"', "script"])
def test_runtime_driver_registration_rejects_raw_html_blocks(
    name: str, tag: str
) -> None:
    required = checker.REQUIREMENTS[name]
    example = f"<{tag}>\n\n{required}\n\n</{tag.split()[0]}>"
    changed = TEXT.replace(required, "\n\n" + example + "\n\n")
    assert name in checker.validate(changed)


def test_runtime_driver_registration_ignores_raw_html_block_headings() -> None:
    example = f"\n\n<pre>\n\n{checker.START}\n\n{checker.END}\n\n</pre>\n"
    assert checker.validate(TEXT + example) == []


@pytest.mark.parametrize(
    "text",
    [
        "",
        TEXT + "\n" + checker.START,
        TEXT + "\n   " + checker.START,
        TEXT.replace(checker.END, "## Other"),
    ],
)
def test_runtime_driver_registration_rejects_missing_or_duplicate_section(
    text: str,
) -> None:
    assert checker.validate(text)


def test_runtime_driver_registration_cli(tmp_path: Path) -> None:
    target = tmp_path / checker.DOCUMENT
    target.parent.mkdir(parents=True)
    command = [
        sys.executable,
        str(ROOT / "scripts/check_runtime_driver_registration.py"),
        "--root",
        str(tmp_path),
    ]
    missing = subprocess.run(command, capture_output=True, text=True)
    assert missing.returncode == 1
    target.write_text(TEXT, encoding="utf-8")
    valid = subprocess.run(command, capture_output=True, text=True)
    assert valid.returncode == 0, valid.stderr
    assert "documentation only" in valid.stdout
    target.write_text(TEXT.replace("sorted bytewise", "unsorted"), encoding="utf-8")
    invalid = subprocess.run(command, capture_output=True, text=True)
    assert invalid.returncode == 1
    assert "coherent cached reads" in invalid.stderr


def test_runtime_driver_registration_registered_in_local_gate() -> None:
    gate = (ROOT / "scripts/ci_local.sh").read_text(encoding="utf-8")
    assert "python3 scripts/check_runtime_driver_registration.py\n" in gate
    assert "python3 -m pytest -q tests/test_runtime_driver_registration.py\n" in gate
