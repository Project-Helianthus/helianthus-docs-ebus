"""Guard the proposed operation contract; this does not qualify an executor.

The reviewed fixture freezes visible normative blocks and complete examples.
Intentional contract changes require a reviewed fixture update. Whitespace and
JSON member ordering are immaterial; hidden prose cannot satisfy an obligation.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

from markdown_it import MarkdownIt
import pytest


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = ROOT / "api/semantic-operation-route.md"
CONTRACT = json.loads(Path(__file__).with_name("semantic_operation_route_contract.json").read_text())
TEXT = DOCUMENT.read_text(encoding="utf-8")
TOKENS = MarkdownIt("commonmark").parse(TEXT)
BLOCKS = [token for token in TOKENS if token.type == "inline"]
FENCES = [token for token in TOKENS if token.type == "fence"]


def closed_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        assert key not in result, f"Duplicate JSON member: {key}"
        result[key] = value
    return result


def validate_contract(text: str) -> None:
    blocks = []
    examples = []
    for token in MarkdownIt("commonmark").parse(text):
        assert token.type not in {"html_block", "code_block"}, (
            "Raw HTML blocks and indented code blocks are not allowed in this contract"
        )
        if token.type == "inline":
            assert all(child.type != "html_inline" for child in token.children or []), (
                "Inline HTML is not allowed in this contract"
            )
            # Preserve inline code syntax without discarding rendered markup.
            blocks.append(" ".join(token.content.split()))
        elif token.type == "fence":
            examples.append({
                "language": token.info,
                "body": json.loads(token.content, object_pairs_hook=closed_object)
                if token.info == "json" else " ".join(token.content.split()),
            })
    # Ordered blocks also guard section placement, input/result tables, bounds,
    # every no-send rule, causal readback requirements and the rule trace.
    assert blocks == CONTRACT["visible_blocks"], "Visible contract blocks changed"
    assert examples == CONTRACT["examples"], "Operation examples changed"


def replace_token(token, replacement: str) -> str:
    lines = TEXT.splitlines(keepends=True)
    start, end = token.map
    return "".join(lines[:start]) + replacement + "".join(lines[end:])


def test_semantic_operation_route_contract() -> None:
    validate_contract(TEXT)


@pytest.mark.parametrize("token", BLOCKS, ids=lambda token: token.content[:60])
@pytest.mark.parametrize("wrapper", ("", "<!--\n{}\n-->\n", "```text\n{}\n```\n", "{} weakened\n"))
def test_rejects_missing_hidden_or_weakened_rule(token, wrapper: str) -> None:
    with pytest.raises(AssertionError):
        validate_contract(replace_token(token, wrapper.format(token.content)))


@pytest.mark.parametrize("token", BLOCKS, ids=lambda token: token.content[:60])
@pytest.mark.parametrize("wrapper", (
    '<span hidden>{}</span>',
    '<span style="display:none">{}</span>',
    '<span>{}</span>',
    '{}<!-- hidden rule -->',
))
def test_rejects_inline_html(token, wrapper: str) -> None:
    first_line = token.content.splitlines()[0]
    assert first_line in TEXT
    changed = TEXT.replace(first_line, wrapper.format(first_line), 1)
    with pytest.raises(AssertionError, match="Inline HTML is not allowed"):
        validate_contract(changed)


@pytest.mark.parametrize("token", BLOCKS, ids=lambda token: token.content[:60])
def test_rejects_relocated_rule(token) -> None:
    remaining = replace_token(token, "")
    relocated = (token.content + "\n\n" + remaining if token is BLOCKS[-1]
                 else remaining + "\n\n" + token.content + "\n")
    with pytest.raises(AssertionError):
        validate_contract(relocated)


@pytest.mark.parametrize("index", range(len(CONTRACT["examples"][2]["body"])))
@pytest.mark.parametrize("member", (
    "status", "kernelOutcome", "delivery", "acknowledgement", "readbackRelation", "reason",
))
@pytest.mark.parametrize("mutation", ("remove", "change", "extra"))
def test_rejects_result_mapping_drift(index: int, member: str, mutation: str) -> None:
    responses = copy.deepcopy(CONTRACT["examples"][2]["body"])
    result = responses[index]["data"]["semanticOperation"]
    if mutation == "remove":
        del result[member]
    elif mutation == "change":
        result[member] = "changed" if result[member] is None else None
    else:
        result[member + "Extra"] = None
    with pytest.raises(AssertionError, match="Operation examples changed"):
        validate_contract(replace_token(FENCES[2], "```json\n" + json.dumps(responses) + "\n```\n"))


@pytest.mark.parametrize("member", tuple(CONTRACT["examples"][1]["body"]["input"]))
def test_rejects_request_example_drift(member: str) -> None:
    request = copy.deepcopy(CONTRACT["examples"][1]["body"])
    del request["input"][member]
    with pytest.raises(AssertionError, match="Operation examples changed"):
        validate_contract(replace_token(FENCES[1], "```json\n" + json.dumps(request) + "\n```\n"))


def test_rejects_duplicate_json_members() -> None:
    with pytest.raises(AssertionError, match="Duplicate JSON member"):
        validate_contract(TEXT.replace('"timeoutMs": 1000', '"timeoutMs": 1000, "timeoutMs": 1000'))


@pytest.mark.parametrize("before,after", (
    ("all mean **no-send**", "may use a fallback executor"),
    ("A concurrent retirement or change causes\n   no-send.", "A concurrent retirement permits dispatch."),
    ("A generic route\n   adds no retry, replay, reroute or write/read sequence.", "A generic route retries on timeout."),
    ("`kernelOutcome=acknowledged_unverified`", "`kernelOutcome=applied`"),
    ("`kernelOutcome=indeterminate`", "`kernelOutcome=failed_no_contact`"),
    ("Validated terminal outcomes take precedence over ACK-only classification.",
     "ACK-only classification takes precedence over validated terminal outcomes."),
    ("Validated `no_effect` or `conflict` remains `failed`",
     "Validated `no_effect` or `conflict` becomes `protocol_ack`"),
    ("Only `acknowledged_unverified` with an accepted or",
     "Any kernel outcome with an accepted or"),
    ("strictly after completed\ndispatch", "before completed dispatch"),
    ("1–5000 milliseconds", "1–60000 milliseconds"),
    ("`String!`; exact existing SemReg `AssetID`", "`ID!`; exact existing SemReg `AssetID`"),
    ("numeric inputs are rejected", "numeric inputs are coerced"),
    ("before JSON parsing or GraphQL coercion", "after GraphQL coercion"),
    ("65,536", "131,072"),
    ("`readbackRelation` is `inconclusive` when evidenced, otherwise null",
     "`readbackRelation` is null"),
    ("complete capability collection revision", "optional capability collection revision"),
))
def test_rejects_semantic_weakening(before: str, after: str) -> None:
    assert before in TEXT
    with pytest.raises(AssertionError, match="Visible contract blocks changed"):
        validate_contract(TEXT.replace(before, after, 1))


@pytest.mark.parametrize("token", FENCES, ids=lambda token: token.info)
def test_requires_every_example(token) -> None:
    with pytest.raises(AssertionError, match="Operation examples changed"):
        validate_contract(replace_token(token, ""))


def test_semantic_operation_route_registered_in_local_gate() -> None:
    gate = (ROOT / "scripts/ci_local.sh").read_text(encoding="utf-8")
    assert "python3 -m pytest -q tests/test_semantic_operation_route_contract.py\n" in gate


@pytest.mark.parametrize("addition", (
    '<div>Additional admission rule.</div>\n',
    '<script type="application/json">{"input": {}}</script>\n',
    '    {"input": {}}\n',
))
@pytest.mark.parametrize("position", ("before", "after"))
def test_rejects_untracked_rendered_blocks(addition: str, position: str) -> None:
    changed = addition + "\n" + TEXT if position == "before" else TEXT + "\n" + addition
    with pytest.raises(AssertionError, match="Raw HTML blocks and indented code blocks"):
        validate_contract(changed)
