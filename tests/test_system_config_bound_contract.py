"""Pin the documented bound contract without a sibling checkout dependency.

The fixture's MCP data fragments match config bound objects in the gateway's
mcp/testdata/semantic_system_dhw_bivalence_bound.golden.json at 1883d3d3.
The mutation signature and result fields match graphql/mutations.go there.
"""

import json
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "tests/fixtures/system_config_bound_contract.json").read_text()
)


def pages():
    return tuple((ROOT / "api" / name).read_text() for name in (
        "graphql.md", "mcp.md"
    ))


def section(text, heading):
    return text.split(heading + "\n", 1)[1].split("\n## ", 1)[0]


def fields(text, name):
    block = re.search(r"type " + name + r" \{([^}]+)\}", text)
    assert block, name
    return dict(re.findall(r"^  (\w+): (\w+!?)", block[1], re.M))


def validate(graphql, mcp):
    assert fields(graphql, CONTRACT["graphql_type"]) == CONTRACT["graphql_fields"]
    assert fields(graphql, "SystemConfig")["dhwBivalencePointBound"] == (
        CONTRACT["graphql_type"]
    )
    mutation = section(graphql, "## Mutation Surface (Implemented)")
    assert (
        "  setSystemConfig(field: String!, value: String!): ConfigMutationResult\n"
        in mutation
    )
    assert fields(mutation, "ConfigMutationResult") == {
        "success": "Boolean!", "error": "String"
    }
    bound = section(graphql, "### System Config Write Bounds")
    payload = section(mcp, "## System Bound Payload Contract")
    for text in (bound, payload):
        for value in CONTRACT["sources"] + CONTRACT["reasons"]:
            assert f"`{value}`" in text, value
        assert f'`{CONTRACT["mcp_member"]}`' in text
    examples = [json.loads(block) for block in re.findall(
        r"```json\n(.*?)\n```", payload, re.S
    )]
    assert examples == CONTRACT["mcp_examples"]
    objects = [example["config"]["dhw_bivalence_point_bound"]
               for example in examples]
    assert set().union(*(obj.keys() for obj in objects)) == set(
        CONTRACT["mcp_fields"]
    )
    for obj in objects:
        assert {"min_c", "max_c", "source"} <= obj.keys()
        assert ("profile" in obj) == (obj["source"] == "controller_profile")
        assert ("reason" in obj) == (obj["source"] == "unmatched_policy")
    normalized_bound = " ".join(bound.split())
    normalized_payload = " ".join(payload.split())
    assert '(with `profile` naming the matched identity' in normalized_bound
    assert '(with `reason` one of' in normalized_bound
    assert ('Before the first resolution, GraphQL returns `null` for '
            '`dhwBivalencePointBound` and MCP omits '
            '`config.dhw_bivalence_point_bound` entirely.') in normalized_bound
    assert ('Empty optional `reason` and `profile` strings are `null` in '
            'GraphQL and omitted in MCP.') in normalized_bound
    assert ('Before the first resolution, MCP omits '
            '`config.dhw_bivalence_point_bound` entirely. GraphQL returns '
            '`null` for `dhwBivalencePointBound`.') in normalized_payload
    assert ('Empty optional `reason` and `profile` strings are omitted in MCP '
            'and `null` in GraphQL.') in normalized_payload
    inventory = mcp.split("## System Bound Payload Contract", 1)[0]
    for required in (
        '  - `ebus.v1.semantic.system.set_config`',
        '`field` and `value`, both strings',
        '`meta.contract`', '`meta.consistency`', '`meta.data_timestamp`',
        '`meta.data_hash`', '`data.success: false`', '`data.error`',
        'top-level `error: null`', 'MCP `isError: true`',
        'controller profile <identity> allows [min, max]',
        'controller identity unmatched (<reason>): conservative policy bound',
    ):
        assert required in inventory, required


def test_documented_bound_contract():
    validate(*pages())


@pytest.mark.parametrize("old", (
    "minC", "maxC", "SystemConfigBound", "setSystemConfig",
    "unknown_register", "unqualified_bound", "invalid_bound",
    "GraphQL returns `null`", "(with `reason` one of",
))
def test_rejects_graphql_contract_drift(old):
    graphql, mcp = pages()
    with pytest.raises((AssertionError, IndexError)):
        validate(graphql.replace(old, "renamed"), mcp)


@pytest.mark.parametrize("old", (
    "dhw_bivalence_point_bound", "min_c", "max_c", "source", "reason",
    "profile", "controller_profile", "unmatched_policy", "unknown_register",
    "unqualified_bound", "invalid_bound", "MCP omits", "isError: true",
    "ebus.v1.semantic.system.set_config",
))
def test_rejects_mcp_contract_drift(old):
    graphql, mcp = pages()
    with pytest.raises((AssertionError, IndexError)):
        validate(graphql, mcp.replace(old, "renamed"))
