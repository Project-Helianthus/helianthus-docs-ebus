#!/usr/bin/env python3
"""Derive the public M7 status projection from validated private inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
from typing import Any


SCRIPT_ROOT = pathlib.Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))
import validate_candidate_fact_graph as candidate


CONTRACT = "helianthus.platform.draft-candidate-fact-public-status.v1"
PROJECTION_DOMAIN = b"HELIANTHUS:MULTI-RUNTIME-COEXISTENCE-M7-PUBLIC-STATUS:V1"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class Failure(Exception):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def digest(domain: bytes, value: Any) -> str:
    return "sha256:" + hashlib.sha256(domain + b"\x00" + canonical(value)).hexdigest()


def render(value: dict[str, Any]) -> bytes:
    lines = ["{"]
    scalar_keys = [key for key in value if key not in {"facts"}]
    for key in scalar_keys:
        rendered = json.dumps(value[key], ensure_ascii=False)
        lines.append(f'  {json.dumps(key)}: {rendered},')
    lines.append('  "facts": [')
    for index, fact in enumerate(value["facts"]):
        suffix = "," if index + 1 < len(value["facts"]) else ""
        lines.append("    " + json.dumps(fact, ensure_ascii=False) + suffix)
    lines.extend(("  ]", "}"))
    return ("\n".join(lines) + "\n").encode("utf-8")


def project(
    graph: dict[str, Any],
    replay: dict[str, Any],
    source_commit: str,
    docs_source_commit: str,
) -> dict[str, Any]:
    if not SHA_RE.fullmatch(source_commit) or not SHA_RE.fullmatch(docs_source_commit):
        raise Failure("projection.commit")
    if candidate.replay(graph) != replay:
        raise Failure("projection.replay")

    facts = [
        {
            "candidate_id": fact["candidate_id"],
            "status": fact["status"],
            "terminal_negative_state": fact["terminal_negative_state"],
            "fact_hash": fact["fact_hash"],
        }
        for fact in sorted(graph["facts"], key=lambda item: item["candidate_id"])
    ]
    counts = {
        status: sum(fact["status"] == status for fact in facts)
        for status in ("RAW_ONLY", "WITHHELD")
    }
    value = {
        "contract": CONTRACT,
        "schema_version": 1,
        "export_tier": "PUBLIC_REDACTED",
        "projection_id": "dcfpsv1:sha256:" + "0" * 64,
        "projection_hash": "sha256:" + "0" * 64,
        "source_commit": source_commit,
        "docs_source_commit": docs_source_commit,
        "source_graph_id": graph["graph_id"],
        "source_graph_hash": graph["graph_hash"],
        "source_replay_id": replay["replay_id"],
        "source_replay_hash": replay["replay_hash"],
        "fact_count": len(facts),
        "status_counts": counts,
        "facts": facts,
    }
    projection_view = {
        key: item
        for key, item in value.items()
        if key not in {"projection_id", "projection_hash"}
    }
    projection_hash = digest(PROJECTION_DOMAIN, projection_view)
    value["projection_id"] = "dcfpsv1:" + projection_hash
    value["projection_hash"] = projection_hash
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graph", type=pathlib.Path, required=True)
    parser.add_argument("--replay", type=pathlib.Path, required=True)
    parser.add_argument("--registry", type=pathlib.Path, required=True)
    parser.add_argument("--source-bundle", type=pathlib.Path, required=True)
    parser.add_argument("--source-replay", type=pathlib.Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--docs-source-commit", required=True)
    parser.add_argument("--expect", type=pathlib.Path)
    args = parser.parse_args()

    try:
        graph, graph_raw = candidate.load_json(args.graph, input_kind="graph")
        registry, registry_raw = candidate.load_json(
            args.registry, input_kind="registry"
        )
        source_bundle, source_bundle_raw = candidate.load_json(
            args.source_bundle, input_kind="source"
        )
        source_replay, _ = candidate.load_json(
            args.source_replay, input_kind="source"
        )
        verified_source, verified_source_replay = candidate._verify_source_inputs(
            registry,
            args.registry,
            source_bundle,
            source_bundle_raw,
            source_replay,
        )
        candidate.verify(
            graph,
            registry,
            registry_raw,
            len(graph_raw),
            verified_source,
            verified_source_replay,
        )
        replay, _ = candidate.load_json(args.replay, input_kind="source")
        value = project(
            graph,
            replay,
            args.source_commit,
            args.docs_source_commit,
        )
        schema_path = (
            SCRIPT_ROOT.parent
            / "docs/platform/schemas/draft-candidate-fact-public-status-v1.schema.json"
        )
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        if not candidate._schema_validate(value, schema, schema):
            raise Failure("projection.schema")
        output = render(value)
        if args.expect is not None and args.expect.read_bytes() != output:
            raise Failure("projection.binding")
        sys.stdout.buffer.write(output)
        return 0
    except Failure as error:
        sys.stdout.write(str(error) + "\n")
        return 1
    except (candidate.Failure, OSError, KeyError, TypeError, ValueError) as error:
        sys.stdout.write(str(error) + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
