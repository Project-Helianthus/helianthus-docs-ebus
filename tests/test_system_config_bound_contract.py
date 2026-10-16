"""Pin the documented bound contract without a sibling checkout dependency.

The fixture pins the GraphQL and MCP bound members and examples; the
architecture copy must agree with their policy window and profile narrowing.
"""

from copy import deepcopy
import json
from pathlib import Path
import re

import pytest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "tests/fixtures/system_config_bound_contract.json").read_text()
)


def pages():
    return tuple((ROOT / name).read_text() for name in (
        "api/graphql.md", "api/mcp.md", "architecture/b524-semantic-mapping.md"
    ))


def section(text, heading):
    return text.split(heading + "\n", 1)[1].split("\n## ", 1)[0]


def fields(text, name):
    block = re.search(r"type " + name + r" \{([^}]+)\}", text)
    assert block, name
    return dict(re.findall(r"^  (\w+): (\w+!?)", block[1], re.M))


def validate(graphql, mcp, architecture):
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
        assert {"min_c", "max_c", "source", "narrowed_only"} <= obj.keys()
        assert CONTRACT["mcp_field_types"] == {"narrowed_only": "boolean"}
        assert type(obj["narrowed_only"]) is bool
        assert obj["narrowed_only"] == (obj["source"] == "controller_profile")
        assert ("profile" in obj) == (obj["source"] == "controller_profile")
        assert ("reason" in obj) == (obj["source"] == "unmatched_policy")
    normalized_bound = " ".join(bound.split())
    aliases = list(CONTRACT["graphql_aliases"])
    targets = list(CONTRACT["graphql_aliases"].values())
    aliases[0] = f'{CONTRACT["graphql_type"]}.{aliases[0]}'
    alias_names = [f"`{name}`" for name in aliases]
    target_names = [f"`{name}`" for name in targets]
    assert (
        f"{', '.join(alias_names[:-1])}, and {alias_names[-1]} are aliases of "
        f"{', '.join(target_names[:-1])}, and {target_names[-1]}, "
        "respectively, with identical values."
    ) in normalized_bound
    normalized_payload = " ".join(payload.split())
    policy = CONTRACT["policy_window"]
    assert policy == {"min_c": -20, "max_c": 50}
    policy_min, policy_max = policy["min_c"], policy["max_c"]
    architecture_bound = " ".join(section(
        architecture, "## `ebus.v1.semantic.system.get`"
    ).split())
    for required in (
        f'`unknown_profile`, so every bound is the policy window `{policy_min}..{policy_max}`',
        f'never widen the policy window `{policy_min}..{policy_max}`',
        f'`min = max(profile min, {policy_min})`',
        f'`max = min(profile max, {policy_max})`',
        'An empty intersection falls back to `unmatched_policy` with reason `invalid_bound`;',
        f'The empty-intersection fallback bound is the policy window `{policy_min}..{policy_max}`.',
        'v1 clients see no change; narrowing applies only on a qualified profile match.',
        'The sole seeded BASV0 bound `-20..20` narrows the policy window on a qualified match.',
    ):
        assert required in architecture_bound, required
    for text in (normalized_bound, normalized_payload):
        assert ('The policy window equals the range the gateway accepted before '
                'profiles existed, so v1 clients see no change, and narrowing '
                'applies only on a qualified profile match (none is reachable '
                'until identities are acquired at discovery, gateway '
                '[#1034][gateway-bound-discovery]).') in text
        assert f'policy window `{policy_min}..{policy_max}`' in text
        assert f'`min = max(profile min, {policy_min})`' in text
        assert f'`max = min(profile max, {policy_max})`' in text
        assert (
            'The empty-intersection fallback bound is the policy window '
            f'`{policy_min}..{policy_max}`.'
        ) in text
    assert (
        'The effective bound is the intersection: '
        f'`min = max(profile min, {policy_min})` and '
        f'`max = min(profile max, {policy_max})`.'
    ) in normalized_bound
    assert ('An empty intersection falls back to `unmatched_policy` with '
            'reason `invalid_bound`.') in normalized_bound
    assert (
        'Its bound is a **Hypothesis** for the target installation and can '
        f'only narrow the policy window `{policy_min}..{policy_max}`: '
        f'`min = max(profile min, {policy_min})`, '
        f'`max = min(profile max, {policy_max})`.'
    ) in normalized_payload
    assert ('An empty intersection uses `unmatched_policy` with reason '
            '`invalid_bound`; otherwise the source and profile identity '
            'remain `controller_profile`.') in normalized_payload
    for obj in objects:
        if obj["source"] == "controller_profile":
            assert policy_min <= obj["min_c"] <= obj["max_c"] <= policy_max
            assert obj["narrowed_only"] is True
        else:
            assert obj["source"] == "unmatched_policy"
            assert obj["reason"] in CONTRACT["reasons"]
            assert {key: obj[key] for key in policy} == policy
    for case in CONTRACT["intersection_cases"]:
        profile = case["profile_window"]
        low = max(profile["min_c"], policy_min)
        high = min(profile["max_c"], policy_max)
        if low <= high:
            outcome = {"min_c": low, "max_c": high,
                       "source": "controller_profile", "narrowed_only": True}
        else:
            outcome = {**policy, "source": "unmatched_policy",
                       "reason": "invalid_bound", "narrowed_only": False}
        assert outcome == case["expected"], case
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
    for text in (normalized_bound, " ".join(inventory.split())):
        assert ('controller identity unmatched (<reason>): conservative policy '
                'bound [-20, 50] applies') in text


def test_documented_bound_contract():
    validate(*pages())


@pytest.mark.parametrize("field", (
    "minC", "min_c", "maxC", "max_c", "narrowedOnly", "narrowed_only",
))
def test_rejects_removing_either_graphql_spelling(field):
    graphql, mcp, architecture = pages()
    graphql, count = re.subn(
        r"^  " + re.escape(field) + r": (?:Float|Boolean)!\n",
        "", graphql, count=1, flags=re.M,
    )
    assert count == 1
    with pytest.raises(AssertionError):
        validate(graphql, mcp, architecture)


@pytest.mark.parametrize("replacement", (
    "",
    "`SystemConfigBound.min_c`, `max_c`, and `narrowed_only` are aliases of\n"
    "`maxC`, `minC`, and `narrowedOnly`, respectively, with identical values.",
    "`SystemConfigBound.min_c`, `max_c`, and `narrowed_only` are aliases of\n"
    "`minC`, `maxC`, and `narrowedOnly`, respectively, with different values.",
))
def test_rejects_graphql_alias_relationship_drift(replacement):
    graphql, mcp, architecture = pages()
    paragraph = (
        "`SystemConfigBound.min_c`, `max_c`, and `narrowed_only` are aliases of\n"
        "`minC`, `maxC`, and `narrowedOnly`, respectively, with identical values."
    )
    assert paragraph in graphql
    with pytest.raises(AssertionError):
        validate(graphql.replace(paragraph, replacement), mcp, architecture)


@pytest.mark.parametrize("old", (
    "minC", "min_c", "maxC", "max_c", "narrowedOnly", "narrowed_only",
    "Boolean!", "SystemConfigBound",
    "setSystemConfig",
    "unknown_register", "unqualified_bound", "invalid_bound",
    "GraphQL returns `null`", "(with `reason` one of",
    "v1 clients see no change", "qualified profile", "[-20, 50] applies",
    "policy window `-20..50`", "max(profile min, -20)",
    "min(profile max, 50)",
    "An empty intersection falls back to\n  `unmatched_policy` with reason `invalid_bound`.",
    "The empty-intersection fallback bound is the policy window `-20..50`.",
))
def test_rejects_graphql_contract_drift(old):
    graphql, mcp, architecture = pages()
    with pytest.raises((AssertionError, IndexError)):
        validate(graphql.replace(old, "renamed"), mcp, architecture)


@pytest.mark.parametrize("old", (
    "dhw_bivalence_point_bound", "narrowed_only", "min_c", "max_c",
    "source", "reason", "profile", "controller_profile", "unmatched_policy", "unknown_register",
    "unqualified_bound", "invalid_bound", "MCP omits", "isError: true",
    "ebus.v1.semantic.system.set_config",
    "v1 clients see no change", "qualified profile", "[-20, 50] applies",
    "policy window `-20..50`", "max(profile min, -20)",
    "min(profile max, 50)",
    "An empty\nintersection uses `unmatched_policy` with reason `invalid_bound`;",
    "The empty-intersection fallback bound is the policy window `-20..50`.",
))
def test_rejects_mcp_contract_drift(old):
    graphql, mcp, architecture = pages()
    with pytest.raises((AssertionError, IndexError)):
        validate(graphql, mcp.replace(old, "renamed"), architecture)


@pytest.mark.parametrize("replacement", (0, 1, "true", None))
def test_rejects_mcp_boolean_type_drift(replacement):
    graphql, mcp, architecture = pages()
    mcp = mcp.replace('"narrowed_only": true',
                      '"narrowed_only": ' + json.dumps(replacement))
    with pytest.raises(AssertionError):
        validate(graphql, mcp, architecture)


@pytest.mark.parametrize("page", (0, 1, 2), ids=("graphql", "mcp", "architecture"))
@pytest.mark.parametrize("old,new", (
    ("-20..50", "-20..20"),
    ("max(profile min, -20)", "max(profile min, -21)"),
    ("min(profile max, 50)", "min(profile max, 20)"),
    ("The empty-intersection fallback bound is the policy window `-20..50`.", ""),
))
def test_rejects_intersection_sentence_drift(page, old, new):
    documents = list(pages())
    assert old in documents[page]
    documents[page] = documents[page].replace(old, new)
    with pytest.raises(AssertionError):
        validate(*documents)


@pytest.mark.parametrize("row", range(len(CONTRACT["intersection_cases"])))
@pytest.mark.parametrize("field", ("min_c", "max_c", "source", "narrowed_only", "reason"))
def test_rejects_intersection_outcome_drift(monkeypatch, row, field):
    cases = deepcopy(CONTRACT["intersection_cases"])
    expected = cases[row]["expected"]
    if field in ("min_c", "max_c"):
        expected[field] += 1
    elif field == "narrowed_only":
        expected[field] = not expected[field]
    elif field == "source":
        expected[field] = ("unmatched_policy" if expected[field] ==
                           "controller_profile" else "controller_profile")
    elif field in expected:
        expected[field] = "unknown_profile"
    else:
        expected[field] = "invalid_bound"
    monkeypatch.setitem(CONTRACT, "intersection_cases", cases)
    with pytest.raises(AssertionError):
        validate(*pages())


@pytest.mark.parametrize("old,new", (
    ("every bound is the policy window `-20..50`", "every bound is the policy window `-20..20`"),
    ("never widen the policy window\n`-20..50`", "never widen the policy window\n`-20..20`"),
    ("reason `invalid_bound`", "reason `unknown_profile`"),
    ("`-20..20` narrows the policy window on a qualified match.",
     "equals the window, so numeric behaviour is unchanged."),
))
def test_rejects_architecture_contract_drift(old, new):
    graphql, mcp, architecture = pages()
    assert old in architecture
    with pytest.raises(AssertionError):
        validate(graphql, mcp, architecture.replace(old, new))
