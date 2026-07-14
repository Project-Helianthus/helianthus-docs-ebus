Canonical source: this page.

# Ownership Manifest And Cross-Repository Validation

## Manifest

`manifests/eebus-doc-ownership.yaml` is the authoritative versioned ownership
manifest. Version 2 is the current publication contract; version 1 remains a
trusted-prior input during migration. The schema is closed. All six surfaces
must be represented, while the platform surface may contain multiple canonical
documents plus explicit canonical collections. Every owner/source pair is
globally unique, and a canonical owner path may occur only once. All repository
paths are portable relative paths with no traversal, private path, private
identifier, credential, or network data. Every path segment also excludes
Windows-reserved characters, trailing dots or spaces, and reserved device names
(including reserved names followed by an extension).

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

The validator freezes these repository and path-prefix bindings. Canonical
surfaces are canonical exactly while `active`; planned, candidate, withdrawn,
code-repository, and summary-only entries are noncanonical. In particular,
protocol ownership cannot be reassigned to the code README or marked
noncanonical while active.

Version 2 separates eligibility from publication. `channel_registry` is the
closed inventory of controlled publication channels, `eligible_channels`
declares where an entry may appear, and `exact_memberships` records the complete
current membership of every registered channel. An active canonical document
or collection must be present in each declared membership. Candidate entries
cannot appear in a stable membership. Collections contain only active canonical
documents; summary pointers target an active canonical document or collection
without acquiring canonical membership themselves. An absence constraint
covers all and only the registered channels.

Platform governance prose may require an artifact to record or report evidence,
including whether protocol activity was observed. That exemption is local to
the reporting predicate and its single bounded observation complement. The
validator accepts owned behavior inside that complement only when it begins as
a bounded grammatical observation subject; it then masks only the validated
ownership or governance span and checks all remaining predicate content. A
deterministic clause splitter propagates a normative modal across punctuation,
conjunction, relative-clause, and shared-modal predicate boundaries, so
coordinated protocol, architecture, or API behavior cannot inherit an exemption.

## State Contract

| State | Expiry | Publication | Required artifact rule |
| --- | --- | --- | --- |
| `planned` | Exactly 14 days after `created_at` | No eligibility or membership; noncanonical and nonlinkable | Owner/source may be absent or may be pre-existing material that has no publication authority |
| `candidate` | Exactly 30 days after `created_at` | Candidate-channel eligibility only from a hidden `_candidate` area; never in a stable membership | Regular owner and source files plus the direct commit object at the pinned source checkout HEAD and exact content hash |
| `active` | No expiry | Exact registered-channel membership after approval and freeze | Regular owner and source files |
| `withdrawn` | No expiry | No eligibility or membership and never consumer-visible | Owner and every distinct source artifact absent immediately; cleanup mandatory |

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
milestone, its state must equal `enforcement.required_state`. A terminal
`withdrawn` alternative is valid only when `required_state` is `candidate` or
`withdrawn`; an `active` obligation cannot be cancelled through withdrawal.
For a valid withdrawal, cleanup must be required, owner and source artifacts
must be absent immediately, and later stages never resurrect the entry. This
applies to `code_repo` before `MSP-DOCS-CLEAN`; the CLEAN-stage substantive
code-document check remains an independent requirement for both withdrawn and
non-withdrawn entries.

Terminal withdrawal is also checked against history. When a trusted prior
manifest exists, pass it as `--prior-manifest PATH`. Every prior `withdrawn`
entry remains indexed by both `surface` and `id`, remains the sole entry for that
surface, and remains `withdrawn`. For the same surface and ID, the complete
normalized manifest entry is an immutable tombstone: lifecycle and provenance,
enforcement, owner/source metadata, publication fields, and any additional fields must
all remain byte-for-value equivalent after YAML normalization. A new ID cannot
resurrect that surface as `planned`, `candidate`, or `active`, and a duplicate
replacement cannot coexist with the tombstone. Artifact absence remains a
separate current-state rule for every distinct owner and source location. A
missing, unreadable, non-regular, malformed, or internally inconsistent
explicitly supplied prior manifest fails closed. When the trusted base commit
tree truly has no manifest, omitting the option is the valid first-introduction
case.

The current E2 enforcement state is:

- existing protocol ownership and the API representation schema are `active`;
- the five foundational platform documents and their canonical collection are
  `active` from `MSP-DOCS-PLATFORM` onward;
- the architecture ownership landing is `active`, with its canonical membership
  supported at `MSP-DOCS-E2`;
- `helianthus-eebusreg/docs` is `withdrawn` at `MSP-DOCS-CLEAN`;
- the code-repository README is `active` only as the exact minimal
  summary-and-build pointer;
- both CLEAN states are required inputs to successors and are validated against
  the immutable eebusreg cleanup head.

At CLEAN, the validator also scans documentation-like files throughout the
eebusreg checkout, including root architecture files and alternate nested
locations. Normative protocol, architecture, or API authority is rejected
outside the canonical docs repository. The scan is bounded to documentation
names and extensions, skips Git metadata and generated, build, vendor, and cache
trees, and deterministically ignores binary files. Markdown fenced, indented,
and inline code remains non-authoritative. Other documentation formats,
including `.txt`, `.rst`, and `.adoc`, are scanned as raw prose so indentation
cannot suppress normative text. The active minimal README, noncanonical links,
and evidence summaries remain governed by their narrower summary and
predicate-local contracts.

An E2 or CLEAN check cannot reuse PLATFORM enforcement: each successor invokes
the same combined-ref validator with its own required stage. Planned entries
also expire after 14 days, so main expiry CI fails inclusively if a required
successor transition is not completed. Candidate entries transition only to
their declared required state or to `withdrawn` cleanup, while candidate
membership remains excluded from every stable channel.

## Combined-Ref Pull Request Validation

`Docs CI / Platform Contracts Combined Ref` is a required pull-request job. It
checks out the current PR head SHA for docs-ebus and these reviewed dependency
commits:

- docs-eebus: `93097087611b3a7643e4f4a36679ea9742842190`;
  reviewed content from PR #13;
- eebusreg: `1121511afaf8583c9aeb698ba6c6d2b0807673db`.
  Reviewed implementation from
  [PR #17](https://github.com/Project-Helianthus/helianthus-eebusreg/pull/17).

All three values are explicit immutable 40-hex commits. Each repository is
checked out into a separate clean root and validated without sibling discovery
or ambient checkout state. A missing, symbolic, moving, mismatched, dirty, or
incorrect repository root is terminal. This caller enforces
`MSP-DOCS-CLEAN`; dependency pins change only in the PR that owns the
corresponding reviewed cross-repository transition.

The G17/G19 cross-seed refresh changes only these Combined Ref inputs. It does
not rewrite the manifest lifecycle source refs that preserve the earlier CLEAN
transition and its immutable withdrawal tombstone.

For pull requests, both Docs Checks and Combined Ref independently check out the
trusted base at `github.event.pull_request.base.sha` into a sibling of the
candidate checkout. Combined Ref executes its validator and dependency lock
only from that official trusted-base checkout; candidate and dependency
checkouts are input data and their scripts are never executed. The one-time
bootstrap from base `114072fe8bdf027cfdd3472d7f2b0896a2496db4`, which predates
the validator, uses reviewed immutable validator commit
`c4d87b2d1fbdc9627a3a2aedaae298547f1908d2`. The workflow verifies the trusted
validator commit and regular script/lock files before execution. It separately
walks every prior-manifest path component with `git ls-tree`, requires tree
objects for parents and a regular blob mode for the final object, and extracts
that inspected blob with `git cat-file` into a private path under
`RUNNER_TEMP`. A missing tree entry is the only valid first-introduction case;
symbolic links, wrong object types, malformed content, and inspection,
extraction, or read failures fail closed. Candidate and dependency refs remain
explicit immutable commits in Combined Ref, including fork pull requests.

Local CI uses the same file contract. A developer with a trusted prior checkout
invokes it deterministically as:

```bash
PLATFORM_PRIOR_MANIFEST=/path/to/trusted-base/docs/platform/manifests/eebus-doc-ownership.yaml \
  ./scripts/ci_local.sh
```

Leave `PLATFORM_PRIOR_MANIFEST` unset only when no prior manifest exists. If it
is set, `ci_local.sh` passes the path unchanged to `--prior-manifest`, so bad or
missing explicit input fails closed. The validator rejects a symbolic link at
the file or any parent path component before reading the manifest.

GitHub uses exact Python `3.12.10`, its bundled pip `25.0.1`, and PyYAML
`6.0.2`. Before the commit-pinned setup action runs, the workflow downloads the
pip `25.0.1` wheel from a fixed URL and verifies its SHA-256 digest. The setup
action receives only that local wheel through `PIP_FIND_LINKS` with index access
disabled, then the workflow explicitly verifies both Python and pip versions.
Every direct and transitive CI dependency is fully pinned in
`requirements-ci.txt`; installation uses `--require-hashes`, `--no-deps`, and
`--no-build-isolation`, so an index may serve only an artifact accepted by the
lock. The lock includes the accepted universal wheels and
source distributions plus PyYAML wheels for GitHub Linux x86_64 and local macOS
x86_64/arm64. The validator reads the actual Python runtime and installed
PyYAML distribution/module versions; caller strings cannot assert them. Local
developers use the documented `supported` mode: Python `>=3.12.0,<3.15.0` and
PyYAML `>=6.0.2,<7.0.0`, with distribution and imported-module versions equal.
GitHub always uses `exact` mode.

Workflow validation is gated by actionlint `v1.7.7`; runtime-state schema
validation is gated by `jv v0.7.0`. Both binaries are installed at pinned Go
module versions and their reported versions are verified before use.

## Post-Merge Completion Token

`scripts/platform_publication_token.py` mints the PLATFORM-B completion token
only from a clean, nonsymlinked checkout whose `HEAD` is the supplied squash
merge. The supplied base, PR head, and merge values must be distinct lowercase
40-hex commit objects. The merge must have the supplied base as its only parent,
the base must be an ancestor of the PR head, and the merge and PR head trees must
match exactly. Repository identity is bound to the expected GitHub origin.

The generator reads the prior and current manifests plus every local publisher
artifact with `git ls-tree` and `git cat-file`. The base manifest must be valid
version 1 and the merged manifest must be valid version 2. Planned or candidate
expiry at the supplied strict UTC evaluation instant blocks token creation. The
evaluation instant cannot precede the immutable merge committer time and carries
an explicit observation source. No network request or moving ref participates
in the proof.

The canonical JSON token binds `producer_id`, `consumer_id`, `repository`, `pr`,
`base_oid`, `head_oid`, `merge_oid`, `tree_oid`, `evidence_core_sha256`,
`prior_token_digest`, and `observation_source`. Its evidence core also records
manifest blob identities, registered channels, eligibility, exact memberships,
collection members, candidate inventory, and local publisher blob identities.
Re-running the command with the same immutable objects and the same explicit
evaluation instant and observation source produces identical bytes.

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

The repository privacy gate and platform validator share the same structured IP
literal parser. They reject private, carrier-grade NAT, and link-local IPv4
addresses, plus IPv6 unique-local, link-local, loopback, scoped private literals,
and IPv4-mapped private addresses. Public and documentation IPv6 literals,
hashes, versions, localhost IPv4 examples, and ordinary colon-bearing prose are
not addresses under this contract.

Platform pages may reference only platform pages merged in the same repository
or immutable active targets present at the supplied docs-eebus commit. Inline,
reference-style, HTML, autolink, and bare GitHub URL forms are parsed outside
fenced, indented, and inline code. GitHub owner and repository names are
compared case-insensitively. Normalized reference identifiers use Markdown's
first-definition-wins behavior, including duplicate identifiers that differ
by case, whitespace, escaped punctuation, or character references. Before
classification, destinations normalize HTML character references and only the
ASCII punctuation escapes defined by CommonMark; unrelated backslashes and
escaped link text are not blanket-unescaped. Moving, candidate, planned,
withdrawn, missing, and symlink targets fail.
