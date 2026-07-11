Canonical source: this page.

# Ownership Manifest And Cross-Repository Validation

## Manifest

`manifests/eebus-doc-ownership.yaml` is the authoritative versioned ownership
manifest. Its schema is closed. Every owner/source pair is globally unique,
and a canonical owner path may occur only once. All repository paths are
portable relative paths with no traversal, private path, private identifier,
credential, or network data.

The loader retains YAML mapping pairs until duplicate-key validation is
complete. It rejects duplicate keys at any depth, cyclic aliases, more than 16
aliases, nesting beyond 24 nodes, more than 8192 YAML tokens, more than 4096
composed nodes, and UTF-8 input larger than 64 KiB. Parser and resource failures
emit only `manifest.schema`; values, paths, parser text, and tracebacks are never
reported.

The six required surfaces are `protocol`, `architecture`, `api`, `platform`,
`code_repo`, and `summary_only`. Ownership is exclusive:

| Surface | Owner |
| --- | --- |
| Protocol behavior | `helianthus-docs-eebus/protocols` |
| Runtime, trust, persistence, lifecycle | `helianthus-docs-eebus/architecture` |
| eeBUS Go API schema, reference, examples | `helianthus-docs-eebus/api` |
| Language-neutral contracts | `helianthus-docs-ebus/docs/platform` |
| Substantive code-repository docs | Removed by `MSP-DOCS-CLEAN` |
| Code README | Minimal summary-only pointer after `MSP-DOCS-CLEAN` |

## State Contract

| State | Expiry | Output | Required artifact rule |
| --- | --- | --- | --- |
| `planned` | Exactly 14 days after `created_at` | No candidate or stable output; noncanonical and nonlinkable | Owner/source may be absent or may be pre-existing material that has no publication authority |
| `candidate` | Exactly 30 days after `created_at` | Candidate output only from a hidden `_candidate` area | Regular owner and source files plus immutable source head and exact content hash |
| `active` | No expiry | All stable outputs after approval and freeze | Regular owner and source files |
| `withdrawn` | No expiry | No output and never consumer-visible | Owner artifact absent and cleanup mandatory |

Every present lifecycle timestamp (`created_at`, `expires_at`, `approved_at`, or
`frozen_at`) uses the same strict RFC 3339 UTC extended form described below.
Malformed present values fail manifest schema validation before state-specific
presence or absence rules are evaluated.

Every required owner/source file is checked at the repository root named by the
manifest. The root must be the expected GitHub repository top level. The file
must remain inside that root, exist, be a regular file, and have no symlink at
any path component. Absolute and relative symlinks are equally invalid.

## Staged Enforcement

The ordered enforcement stages are `MSP-DOCS-API-SCHEMA`,
`MSP-DOCS-PLATFORM`, `MSP-DOCS-E2`, and `MSP-DOCS-CLEAN`. Before an entry's
owning milestone, its state must be `planned` or `candidate`. At and after that
milestone, its state must equal `enforcement.required_state` exactly.

The current PLATFORM transition is:

- existing protocol ownership and the API representation schema are `active`;
- the platform contracts become `active` at `MSP-DOCS-PLATFORM`;
- the architecture ownership landing remains `planned` with no stable output
  until it transitions to `active` at `MSP-DOCS-E2`;
- current `helianthus-eebusreg/docs` and its README remain `planned` and are not
  failures during PLATFORM or E2;
- at `MSP-DOCS-CLEAN`, code-repository docs must transition
  `planned -> withdrawn`, while the README must transition
  `planned -> active` as a minimal summary-only pointer.

An E2 or CLEAN check cannot reuse PLATFORM enforcement: each successor invokes
the same combined-ref validator with its own required stage. Planned entries
also expire after 14 days, so main expiry CI fails inclusively if a required
successor transition is not completed. Candidate entries transition only to
their declared required state or to `withdrawn` cleanup, while candidate output
remains excluded from every stable channel.

## Combined-Ref Pull Request Validation

`Docs CI / Platform Contracts Combined Ref` is a required pull-request job. It
checks out the current PR head SHA for docs-ebus and these merged dependency
commits:

- docs-eebus: `f23a7c35e6803501f185923de061f935bbac1466`;
- eebusreg: `0e58327dfdb86ef243a19e18d590564813feaa00`.

All three values are explicit immutable 40-hex commits. Each repository is
checked out into a separate clean root and validated without sibling discovery
or ambient checkout state. A missing, symbolic, moving, mismatched, dirty, or
incorrect repository root is terminal. Dependency pins change only in the PR
that owns the corresponding successor transition.

GitHub uses exact Python `3.12.10` and PyYAML `6.0.2`. The validator reads the
actual Python runtime and installed PyYAML distribution/module versions; caller
strings cannot assert them. Local developers use the documented `supported`
mode: Python `>=3.12.0,<3.15.0` and PyYAML `>=6.0.2,<7.0.0`, with distribution
and imported-module versions equal. GitHub always uses `exact` mode.

Workflow validation is gated by actionlint `v1.7.7`; runtime-state schema
validation is gated by `jv v0.7.0`. Both binaries are installed at pinned Go
module versions and their reported versions are verified before use.

## Main Expiry Validation

Main-branch validation runs separately in `main-expiry` mode. It receives a
named timestamp source and a strict RFC 3339 UTC extended timestamp of the form
`YYYY-MM-DDTHH:MM:SSZ`. Fractions are optional and, when present, contain one
through six decimal digits. Basic ISO forms, spaces, lowercase `z`, leap
seconds, commas, more than six fractional digits, and every numeric UTC offset
including `+00:00` are rejected.

The validator never reads the local clock implicitly. Expiry is inclusive: an
entry is expired when the evaluation instant equals or exceeds `expires_at`.
Every diagnostic is terminal and consists only of a sorted unique category id.

Platform pages may reference only platform pages merged in the same repository
or immutable active targets present at the supplied docs-eebus commit. Inline,
reference-style, and HTML links are parsed outside fenced, indented, and inline
code. Moving, candidate, planned, withdrawn, missing, and symlink targets fail.
