Canonical source: this page.

# Ownership Manifest And Cross-Repository Validation

## Manifest

`manifests/eebus-doc-ownership.yaml` is the authoritative versioned ownership
manifest. Its schema is closed. Every owner/source pair is globally unique,
and a canonical owner path may occur only once. All repository paths are
portable relative paths with no traversal, private path, private identifier,
credential, or network data.

The six required surfaces are `protocol`, `architecture`, `api`, `platform`,
`code_repo`, and `summary_only`. Ownership is exclusive:

| Surface | Owner |
| --- | --- |
| Protocol behavior | `helianthus-docs-eebus/protocols` |
| Runtime, trust, persistence, lifecycle | `helianthus-docs-eebus/architecture` |
| eeBUS Go API schema, reference, examples | `helianthus-docs-eebus/api` |
| Language-neutral contracts | `helianthus-docs-ebus/docs/platform` |
| Substantive code-repository docs | Withdrawn and removed |
| Code README | Minimal summary-only pointer |

## State Contract

| State | Expiry | Output | Terminal invalid state |
| --- | --- | --- | --- |
| `planned` | Exactly 14 days after `created_at` | No candidate or stable output; noncanonical and nonlinkable | Missing source issue/PR, wrong expiry, or any output |
| `candidate` | Exactly 30 days after `created_at` | Candidate output only from a hidden `_candidate` area | Missing source PR/head/hash, digest mismatch, wrong expiry, or stable output |
| `active` | No expiry | Stable outputs after approval and freeze | Missing path, approval, freeze, or any expiry |
| `withdrawn` | No expiry | No output and never consumer-visible | Optional cleanup, remaining artifact, or any output |

Expiry is inclusive: a planned or candidate entry is expired when the
evaluation instant is equal to or later than `expires_at`. Every validation
diagnostic is terminal and fails the workflow. Diagnostics are sorted unique
category identifiers only; they contain no paths, refs, identifiers, or data.

## Combined-Ref Pull Request Validation

PR validation receives an explicit immutable 40-hex docs-ebus ref, docs-eebus
ref, and source-code ref. Each repository is fetched into a separate clean clone
and checked out detached at that exact commit. Validation uses those
roots only: there is no ambient checkout state and no sibling-directory
discovery. A missing, symbolic, moving, mismatched, or dirty ref is terminal.

The toolchain is pinned to Python `3.12.10` and PyYAML `6.0.2`. Workflow action
commits and any installed helper are pinned as well. Paths passed between jobs
are workspace-relative or temporary paths, never operator-specific absolute
paths committed to the repository.

## Main Expiry Validation

Main-branch validation runs separately in `main-expiry` mode. It receives an
RFC 3339 UTC evaluation timestamp and a named timestamp source from the CI
event or scheduler. The validator never reads the local clock implicitly. A
missing or malformed evaluation timestamp, missing timestamp source, or any
entry at or beyond expiry is terminal.

Platform pages may reference only platform pages merged in the same repository
or immutable, active targets already present at the supplied docs-eebus ref.
They do not forward-link to proposed or unmerged pages.
