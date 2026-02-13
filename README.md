# Helianthus eBUS Documentation

This repository documents the current, implemented behavior of the Helianthus eBUS ecosystem:

- `helianthus-ebusgo` (transport + protocol + data types)
- `helianthus-ebusreg` (registry + schema + vendor providers)
- `helianthus-ebusgateway` (API surface; currently package stubs only)

Implementation-neutral references for the eBUS wire protocol and data types live under `protocols/` and `types/`. Helianthus-specific architecture, APIs, and deployment notes live elsewhere in the tree.

For Home Assistant onboarding and GraphQL capability expectations, see `development/ha-integration.md`.
For ebusd command-backend usage (gateway transport selection + protocol behavior), see `deployment/full-stack.md` and `protocols/ebusd-tcp.md`.
For cross-repo smoke execution order (gateway → add-on → integration), see `development/end-to-end-smoke.md`.
For target emulation framework and identify-only profile behavior (VR90/VR_71 presets), see `development/target-emulation.md` and `protocols/ebus-overview.md`.

## Documentation Gate

Changes that alter **architecture**, **API surface**, or **runtime behavior** are merge-gated on documentation updates.

- Policy, trigger matrix, and PR checklists: `development/contributing.md#documentation-gate-doc-gate`

## Licensing

This repository contains documentation under two licenses:

- [`protocols/`](protocols/) and [`types/`](types/) – **CC0-1.0** (public domain).
  These describe the eBUS wire protocol and data type formats as reverse-engineered
  from the bus. Anyone can use, modify, or republish this material without restriction.

- Everything else – **AGPL-3.0**.
  This documents the Helianthus implementation specifically.
  See the root [LICENSE](LICENSE) file for terms.
