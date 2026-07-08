# eeBUS Interop Smoke Gate

Canonical source: this page.

Plan provenance:
`helianthus-execution-plans/multi-runtime-semantic-platform.draft`.

Implementation hook:
`helianthus-eebusreg/internal/eebusinteropsmoke`.

## Scope

MSP-03D proves raw eeBUS runtime feasibility after the internal
`eebus-go v0.7.0` facade and Home Assistant network gates. It does not enable
an eeBUS gateway sidecar, freeze the raw runtime contract, write production
trust, expose MCP tools, create candidate semantic facts, or enrich B509/B524
leaves.

This gate covers `eebus-transport-gate-v0` cases:

| Case | Required proof |
| --- | --- |
| `EEBUS-G01` | A black-box fake peer completes SHIP/TLS/session setup without importing the Helianthus facade under test. |
| `EEBUS-G17` | A live VR940f/myVaillant device completes discovery, pairing/session establishment, feature graph extraction, and reconnect after restart. |

## Fake Peer Boundary

Fake peer success is supporting evidence only. A valid `EEBUS-G01` artifact
must show:

- the exact `github.com/enbility/eebus-go v0.7.0` module evidence;
- disposable, in-memory proof credentials;
- no production trust-store writes;
- no gateway, GraphQL, Portal, Home Assistant, command-routing, raw-write, or
  semantic-registry surface;
- an import-boundary check proving the peer side did not import the
  Helianthus facade under test;
- a redacted PASS/FAIL table for `EEBUS-G01`.

Passing `EEBUS-G01` cannot replace `EEBUS-G17`, cannot close M3 by itself, and
cannot justify a gateway import.

## Live VR940f Boundary

Live VR940f evidence must be collected only from a real LAN-visible SHIP
service. The minimum PASS requires:

- `_ship._tcp` discovery from the relevant LAN/runtime namespace;
- approved pairing/session establishment;
- feature graph extraction as raw SHIP/SPINE evidence;
- reconnect after runtime restart;
- redacted command-log or scripted-harness refs.

If no `_ship._tcp` service is visible, the result is `BLOCKED` with an explicit
`no_visible_ship_service` style state. It is not a PASS and must not be
treated as proof that VR940f lacks eeBUS support.

If a SHIP service is visible but no approved remote SKI or out-of-band pairing
confirmation is available, the result is also `BLOCKED`. The artifact may
record service visibility, but it must not claim pairing/session, feature
graph, reconnect, or semantic facts.

## Public Artifact Requirements

Public MSP-03D artifacts must include:

- repo, branch, commit, issue id, mode, required cases, and generated
  timestamp;
- Go/toolchain and module evidence;
- disposable credential posture;
- per-case PASS/FAIL/BLOCKED rows;
- command-log or scripted-harness references;
- redacted endpoint, service, and interface references.

Public artifacts must not include raw:

- SKIs, certificate fingerprints, peer ids, session ids, pairing history;
- IP addresses, MAC addresses, serials;
- PEM blocks, private keys, tokens, or passwords;
- vendor-restricted protocol details.

Use short redacted digest refs only for continuity inside the same evidence
run. These refs are not semantic facts and must not be copied into eBUS
registries, eeBUS candidate facts, GraphQL, Portal, or Home Assistant.

## Promotion Boundary

MSP-03D is M3 feasibility evidence. M3.5 may freeze raw identity and evidence
shapes only after `EEBUS-G01` and `EEBUS-G17` are both accepted. M4 trust work,
M5 gateway sidecar import, M6 MCP, and later B509/B524/B555 enrichment remain
separate gates.
