"""Independent field mutations exercise inventory admission and documentation drift."""

import copy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import check_mcp_inventory as checker


ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC = {
    "schema_version": 1,
    "tools": [
        {"name": "helianthus.runtime.list", "surface": "ordinary",
         "registration_profile": "runtime_disabled",
         "availability_condition": "runtime service absent; eeBUS absent",
         "implementation_source": "mcp/runtime_control.go"},
        {"name": "synthetic.target", "surface": "ordinary",
         "registration_profile": "target_modbus_core",
         "availability_condition": "target/uncomposed structural provider; not a production enablement claim",
         "implementation_source": "mcp/synthetic.go"},
    ],
}
DOCUMENT = """## G5 runtime lifecycle MCP contract (D4)

The five tools are **implemented**.

## Implemented Surface

mcp-profiles:start
| Profile | Surface | Classification |
|---|---|---|
| runtime_disabled | ordinary | implemented |
| target_modbus_core | ordinary | target |
mcp-profiles:end

mcp-inventory:start
| Tool | Surface | Profiles | Availability condition | Implementation source | Classification |
|---|---|---|---|---|---|
| helianthus.runtime.list | ordinary | runtime_disabled | runtime service absent; eeBUS absent | mcp/runtime_control.go | implemented |
| synthetic.target | ordinary | target_modbus_core | target/uncomposed structural provider; not a production enablement claim | mcp/synthetic.go | target |
mcp-inventory:end
"""
CASES = [(SYNTHETIC, DOCUMENT)]
EMITTED = ROOT / ".tmp/reference/mcp-tools.json"
if EMITTED.is_file():
    CASES.append((json.loads(EMITTED.read_text()), (ROOT / "api/mcp.md").read_text()))


@pytest.fixture(params=CASES, ids=["synthetic", "emitted"][:len(CASES)])
def pair(request):
    return copy.deepcopy(request.param)


def test_accept_complete_inventory(pair):
    inventory, document = pair
    assert checker.validate(inventory, document) == len(inventory["tools"])


@pytest.mark.parametrize(("field", "replacement"), [
    ("name", "synthetic.renamed"),
    ("surface", "operator"),
    ("registration_profile", "runtime_enabled"),
    ("availability_condition", "provider always present"),
    ("implementation_source", "mcp/changed.go"),
])
def test_each_emitted_field_mutation_rejected(pair, field, replacement):
    inventory, document = pair
    original = inventory["tools"][0][field]
    if field == "surface" and original == replacement:
        replacement = "ordinary"
    assert original != replacement
    inventory["tools"][0][field] = replacement
    with pytest.raises(ValueError):
        checker.validate(inventory, document)


@pytest.mark.parametrize("mutation", ["remove", "add", "duplicate", "profile", "empty"])
def test_inventory_membership_mutation_rejected(pair, mutation):
    inventory, document = pair
    if mutation == "remove":
        inventory["tools"].pop()
    elif mutation == "add":
        row = dict(inventory["tools"][0], name="synthetic.added")
        inventory["tools"].append(row)
    elif mutation == "duplicate":
        inventory["tools"].append(inventory["tools"][0])
    elif mutation == "profile":
        inventory["tools"][0]["registration_profile"] = "unknown_profile"
    else:
        inventory["tools"] = []
    with pytest.raises(ValueError):
        checker.validate(inventory, document)


@pytest.mark.parametrize(("old", "new"), [
    ("**implemented**", "**pending implementation**"),
    (" | target |", " | implemented |"),
    ("mcp-inventory:start", ""),
    ("mcp-profiles:end", ""),
    ("mcp/runtime_control.go | implemented", "mcp/changed.go | implemented"),
    ("| runtime_disabled | ordinary |", "| runtime_disabled | operator |"),
])
def test_document_mutations_rejected(pair, old, new):
    inventory, document = pair
    assert old in document
    with pytest.raises(ValueError):
        checker.validate(inventory, document.replace(old, new))


@pytest.mark.parametrize("inventory", [None, [], {}, {"schema_version": True, "tools": []},
                                     {"schema_version": 2, "tools": []}])
def test_invalid_root_schema(inventory):
    with pytest.raises(ValueError):
        checker.validate(inventory, DOCUMENT)


@pytest.mark.parametrize("change", ["missing", "extra", "type", "blank"])
def test_invalid_row_schema(change):
    inventory = copy.deepcopy(SYNTHETIC)
    row = inventory["tools"][0]
    if change == "missing":
        del row["name"]
    elif change == "extra":
        row["extra"] = "value"
    elif change == "type":
        row["name"] = 42
    else:
        row["name"] = " "
    with pytest.raises(ValueError):
        checker.validate(inventory, DOCUMENT)


@pytest.mark.parametrize("content", [None, "{", '{"schema_version":1,"schema_version":1,"tools":[]}'])
def test_cli_rejects_missing_or_invalid_input(tmp_path, content):
    path = tmp_path / "inventory.json"
    if content is not None:
        path.write_text(content)
    result = subprocess.run([sys.executable, str(ROOT / "scripts/check_mcp_inventory.py"),
                             "--inventory", str(path)], capture_output=True, text=True,
                            timeout=10)
    assert result.returncode == 1
    assert "MCP inventory:" in result.stderr


def test_cli_requires_inventory():
    result = subprocess.run([sys.executable, str(ROOT / "scripts/check_mcp_inventory.py")],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 2


@pytest.mark.parametrize("mutation", ["remove", "add", "duplicate", "name", "surface",
                                     "registration_profile", "availability_condition",
                                     "implementation_source", "classification"])
def test_document_inventory_row_mutations(pair, mutation):
    inventory, document = pair
    start = document.index("mcp-inventory:start")
    prefix, table = document[:start], document[start:]
    row = next(line for line in table.splitlines()
               if line.startswith("|") and not line.startswith(("| Tool", "|---")))
    cells = row.split("|")
    if mutation == "remove":
        replacement = ""
    elif mutation == "add":
        added = list(cells)
        added[1] = " synthetic.added "
        replacement = row + "\n" + "|".join(added)
    elif mutation == "duplicate":
        replacement = row + "\n" + row
    else:
        index = {"name": 1, "surface": 2, "registration_profile": 3,
                 "availability_condition": 4, "implementation_source": 5,
                 "classification": 6}[mutation]
        cells[index] = " synthetic.changed "
        replacement = "|".join(cells)
    with pytest.raises(ValueError):
        checker.validate(inventory, prefix + table.replace(row, replacement, 1))


def test_fm5_contract_section_defers_availability_to_inventory():
    text = (ROOT / "api" / "mcp.md").read_text(encoding="utf-8")
    section = text.split("### Post-M9 FM5 Contract", 1)[1].split("\n### ", 1)[0].split("\n## ", 1)[0]
    assert "checked\nregistration inventory" in section
    assert not re_search_pending(section)


def re_search_pending(section):
    import re
    return re.search(r"pending|not part of the implemented|until a gateway", section, re.I)
