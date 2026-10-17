#!/usr/bin/env python3
"""Guard the S0 registration documentation; does not execute gateway behavior.

Normative rows/paragraphs are intentionally checked in full so weakening a clause
cannot pass by retaining isolated keywords. Whitespace wrapping is immaterial;
contract edits require a corresponding reviewed validator update.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

from markdown_it import MarkdownIt


DOCUMENT = Path("architecture/runtime-driver-lifecycle.md")
START = "## S0/A1: typed compiled-driver registration"
END = "## S5: deferred managed adapters and DM-HOOKS"
REQUIREMENTS = {
    "descriptor `DriverID`": """| `DriverID` | Canonical, unique, nonempty UTF-8 ID matching `^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$`, at most 128 bytes; stable across restart and gateway rename |""",
    "descriptor Direction": """| Direction | Exactly `southbound`, `northbound` or `both`, explicitly selected per instance |""",
    "descriptor Disposition": """| Disposition | Explicit configured/enabled disposition; configuration eligibility is separate from durable desired state and current observed state |""",
    "descriptor `NativeContractRef`": """| `NativeContractRef` | Nonempty `Owner`, `Contract` and `Version`, naming the public native owner, owner-defined contract and exact supported version/revision; sanitized, with no endpoint, credential, raw payload or handle |""",
    "descriptor Lifecycle adapter": """| Lifecycle adapter | Typed factory plus Runtime binding over DriverManager; registration stores the adapter without invoking it |""",
    "descriptor Owned `SourceID` set": """| Owned `SourceID` set | Stable configured source identities, each exclusively owned by one driver across the entire descriptor set and existing hub ownership |""",
    "descriptor Hook declarations": """| Hook declarations | Optional versioned declarations; an empty set is required by this first host |""",
    "identity and authority": """Direction expresses supported roles. It grants no forwarding, native operation,
publication, write permission, profile qualification or evidence grade.
`DriverID`, `SourceID`, semantic asset/binding identity and lifecycle correlation
remain distinct. A source derives from DriverID plus configured owner identity,
never an endpoint, connection handle, path or discovery result. Reconnecting or
changing an endpoint cannot silently change ownership.""",
    "validation and freeze": """Validate the **complete** descriptor set, including disabled entries, and freeze
detached copies before any factory invocation, semantic declaration or endpoint
call. Validate IDs, directions, dispositions, native references, adapters and
source ownership against both all other descriptors and the hub. Duplicate or
noncanonical driver IDs, duplicate source ownership and hub-source collisions
refuse registration before effects. Failure installs no partial registry and
mutates no hub ownership. Retain unaffected last-known-good state and provenance;
rejected registration never grants admission.""",
    "hook rejection and isolation": """Recognize only hooks implemented by this host at their supported versions.
Unknown hook names and unsupported versions fail explicitly. The reserved
future names are `mcp`, `setup`, `portal`, `semantic` and `evidence`; **all hook
declarations currently fail**, including these names, because none is
implemented. Reserving a name is not accepting a nonfunctional control.
Registration and common lifecycle control contain no protocol, vendor or family
switch and perform no endpoint I/O or semantic declaration.""",
    "coherent cached reads": """List/get read only the frozen registry and cached lifecycle state. List returns
all configured drivers sorted bytewise by `DriverID`, independent of registration
order. Entries and catalog revision come from one coherent read transaction;
get returns the corresponding coherent cached entry and `NOT_FOUND` for an
unknown ID. Neither operation constructs a driver, probes an endpoint, refreshes
native state or performs discovery.""",
    "production registration": """`ebus.primary` is the only production registration in this slice. It is
southbound, configured/enabled and lifecycle-only. It owns one stable configured
source and declares no hooks, semantic assets, bindings, capability instances or
semantic publications. Native invocation capabilities remain separate from
semantic capability instances. The empty barrier and cleanup set are valid;
never fabricate semantic material to satisfy a binding-bearing provider SPI.""",
    "native dispatch blockers": """The native owner is
[`github.com/Project-Helianthus/helianthus-ebusgo`](https://github.com/Project-Helianthus/helianthus-ebusgo),
with the transport API exposed by
[`transport/driver_runtime.go`](https://github.com/Project-Helianthus/helianthus-ebusgo/blob/main/transport/driver_runtime.go).
These branch links identify the public owner and file, not a frozen dependency
version or native eBUS wire proof. The dispatch-pinned source provides
`transport.DriverRuntime`; the supplied material does not establish an
owner-defined contract identifier/version or the exact configured `SourceID`.
Those values are **Unknown** and remain dispatch acceptance blockers. Gateway
descriptor `v1` must not substitute for a native contract version. Do not install
a placeholder reference, derive identity from an endpoint or admit this driver
until the exact supported native contract and configured source are supplied
and validated. This page does not claim that production registration has passed.""",
    "gateway acceptance boundary": """Use synthetic southbound, northbound and both-role descriptors. Require zero
factory calls, semantic declarations, endpoint calls and state mutation for
noncanonical or duplicate DriverID, invalid direction/disposition, missing native
reference fields or adapter, duplicate sources, hub ownership collision, unknown
hook and unsupported hook version. Mutating caller-owned descriptors after freeze
must not alter the registry. Permute registration order and assert sorted,
coherent list/get views, including disabled entries, with no provider calls.
Prove registration/control packages import no protocol package and that the
production composition registers only `ebus.primary`. These are gateway test
obligations, not executed tests or wire-evidence claims in this prose slice.""",
}


def normalize(text: str) -> str:
    return " ".join(text.split())


def validate(text: str) -> list[str]:
    """Return missing/changed obligations in the bounded registration section."""
    # Parse before normalizing whitespace or locating headings: code examples
    # and raw HTML cannot supply normative obligations or section boundaries.
    lines = text.splitlines(keepends=True)
    for token in MarkdownIt().parse(text):
        if token.type in {"fence", "code_block", "html_block"} and token.map is not None:
            start, end = token.map
            lines[start:end] = ["\n"] * (end - start)
    text = "".join(lines)
    headings = list(re.finditer(r"^## .+$", text, re.MULTILINE))
    starts = [i for i, heading in enumerate(headings) if heading.group() == START]
    if len(starts) != 1:
        return ["expected exactly one S0 registration section"]
    index = starts[0]
    if index + 1 >= len(headings) or headings[index + 1].group() != END:
        return ["expected S5 immediately after S0 registration section"]
    section = text[headings[index].end() : headings[index + 1].start()]
    # Rows and paragraphs must stand alone, not survive as substrings in changed
    # prose, comments, examples or other sections.
    section = re.sub(r"<!--.*?-->", "", section, flags=re.DOTALL)
    units = set()
    for block in re.split(r"\n\s*\n", section.strip()):
        if block.lstrip().startswith("|"):
            units.update(normalize(row) for row in block.splitlines())
        else:
            units.add(normalize(block))
    return [
        name
        for name, required in REQUIREMENTS.items()
        if normalize(required) not in units
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    try:
        errors = validate((args.root / DOCUMENT).read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        print(f"registration_contract_invalid: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"registration_contract_invalid: {error}", file=sys.stderr)
        return 1
    print("registration_contract_ok (documentation only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
