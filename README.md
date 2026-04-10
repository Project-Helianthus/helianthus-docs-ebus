# Helianthus eBUS Documentation

This repository documents the current, implemented behavior of the Helianthus eBUS ecosystem:

- `helianthus-ebusgo` (transport + protocol + data types)
- `helianthus-ebusreg` (registry + schema + vendor providers)
- `helianthus-ebusgateway` (runtime + GraphQL/MCP + projection browser/Portal surfaces)

Implementation-neutral references for the eBUS wire protocol and data types live under `protocols/` and `types/`. Helianthus-specific architecture, APIs, and deployment notes live elsewhere in the tree.

Gateway HTTP entrypoints are split by role: `/ui` is the read-only projection browser, while `/portal` is the Portal shell and `/portal/api/v1` is its versioned API surface.

## Start Here by Role

- **Developer path:** [architecture/overview.md](architecture/overview.md) → [api/graphql.md](api/graphql.md) → [api/mcp.md](api/mcp.md) → [api/portal.md](api/portal.md) → [development/contributing.md](development/contributing.md)
- **Operator path:** [deployment/full-stack.md](deployment/full-stack.md) → [development/end-to-end-smoke.md](development/end-to-end-smoke.md) → [development/smoke-test.md](development/smoke-test.md)
- **Researcher path:** [protocols/ebus-overview.md](protocols/ebus-overview.md) → [types/overview.md](types/overview.md) → [architecture/vaillant.md](architecture/vaillant.md)

## Documentation Map

| Area | Start docs |
|---|---|
| Architecture | [architecture/overview.md](architecture/overview.md), [architecture/decisions.md](architecture/decisions.md), [architecture/mcp-first-development.md](architecture/mcp-first-development.md), [architecture/nm-model.md](architecture/nm-model.md), [architecture/nm-discovery.md](architecture/nm-discovery.md) |
| Protocols | [protocols/ebus-overview.md](protocols/ebus-overview.md), [protocols/ebusd-tcp.md](protocols/ebusd-tcp.md), [protocols/ebus-vaillant.md](protocols/ebus-vaillant.md), [protocols/ebus-vaillant-B524.md](protocols/ebus-vaillant-B524.md), [protocols/ebus-vaillant-b524-register-map.md](protocols/ebus-vaillant-B524-register-map.md), [protocols/ebus-vaillant-b524-research.md](protocols/ebus-vaillant-b524-research.md), [protocols/ebus-vaillant-b555-timer-protocol.md](protocols/ebus-vaillant-b555-timer-protocol.md) |
| Types | [types/overview.md](types/overview.md), [types/primitives.md](types/primitives.md), [types/composite.md](types/composite.md) |
| API | [api/graphql.md](api/graphql.md), [api/mcp.md](api/mcp.md), [api/portal.md](api/portal.md) |
| Deployment | [deployment/full-stack.md](deployment/full-stack.md), [deployment/tinygo-esp32.md](deployment/tinygo-esp32.md) |
| Development | [development/contributing.md](development/contributing.md), [development/conventions.md](development/conventions.md), [development/ha-integration.md](development/ha-integration.md) |
| Firmware | [firmware/pic16f15356-overview.md](firmware/pic16f15356-overview.md), [firmware/pic16f15356-pinout.md](firmware/pic16f15356-pinout.md), [firmware/pic16f15356-fsm.md](firmware/pic16f15356-fsm.md), [firmware/pic16f15356-timing.md](firmware/pic16f15356-timing.md), [firmware/pic16f15356-registers.md](firmware/pic16f15356-registers.md) |

## Contribution Workflow (Doc-Gate)

- **Tier 1 (merge-blocking):** changes to architecture, API surface, or runtime behavior must update docs in the same PR; see [Trigger Matrix](development/contributing.md#trigger-matrix).
- **Tier 2 (non-blocking):** internal-only refactors with no external behavior change may skip doc edits, but must include a short rationale in the PR description; see [Trigger Matrix](development/contributing.md#trigger-matrix).
- **Author flow:** classify the change, update required docs, and complete the [PR Author Checklist](development/contributing.md#pr-author-checklist).
- **Reviewer flow:** verify classification and documentation coverage using the [Mandatory Gate Flow](development/contributing.md#mandatory-gate-flow).
- **Canonical policy:** [development/contributing.md#documentation-gate-doc-gate](development/contributing.md#documentation-gate-doc-gate)

## Local CI (no GitHub Actions required)

Run:

```bash
./scripts/ci_local.sh
```

## Licensing

This repository contains documentation under two licenses:

- [`protocols/`](protocols/) and [`types/`](types/) – **CC0-1.0** (public domain).
  These describe the eBUS wire protocol and data type formats as reverse-engineered
  from the bus. Anyone can use, modify, or republish this material without restriction.

- Everything else – **AGPL-3.0**.
  This documents the Helianthus implementation specifically.
  See the root [LICENSE](LICENSE) file for terms.
