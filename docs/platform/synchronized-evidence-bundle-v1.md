# Synchronized Evidence Bundle V1

Canonical source: this page.

Status: closed language-neutral contract for MSP-065 / M6.5.

Contract identifier: `helianthus.platform.synchronized-evidence-bundle.v1`.

Issue provenance:
`Project-Helianthus/helianthus-docs-ebus#355`.

Immutable eeBUS cross-seed provenance:
`Project-Helianthus/helianthus-docs-eebus@9819762a61c28eeceb11beb775aa2a91c83a68b6`.
The pinned source schema is
`api/_candidate/msp-06/helianthus.eebus.mcp.v1.schema.json`, SHA-256
`7f10fa6860e8ccee1af7f155e03d5ac208b5a6fb30518aa3145122a9a1dc0a1c`.
This immutable ref is provenance text rather than an active navigation link so
candidate-link validation cannot make this platform contract depend on an
unpublished page.

## Purpose And Ownership

`SynchronizedEvidenceBundleV1` records reviewable, synchronized observations
from eeBUS, eBUS, and a bounded cloud/app input seam. It is an evidence and
offline replay contract. It does not assign semantic meaning, compare leaves,
or promote facts.

This page owns only the language-neutral bundle, clock, state, hashing,
privacy, persistence, and replay rules. All eeBUS-native protocol, runtime, and
API facts are canonical in `helianthus-docs-eebus`. This page does not restate
SHIP/SPINE behavior, an `eebus.v1.*` schema, VR940f behavior, or eeBUS
lifecycle rules. A source-owned payload is accepted only through the frozen
`source_contract` and `source_schema_version` named by an artifact.

M6.5 may consume only:

- existing read-only eBUS debug, MCP, or log surfaces;
- existing read-only `eebus.v1.*` snapshots; and
- cloud/app observations supplied through the bounded pre-captured input seam
  defined below.

M6.5 adds no eBUS transport, sniffing, or write path. There is no new eBUS capture path.
It makes no change to `ebus.v1.*`, GraphQL, Portal, Home Assistant,
command routing, the semantic registry, or promoted semantics. An `action`
marker is externally supplied evidence only. The recorder must not initiate a
write or state transition in any runtime, bus, cloud service, application, or
device.

## Conformance Language

The logical model is language-neutral. JSON names below are the stable
interchange names and the RFC 8785 hash representation; an implementation in
another language must enforce the same names, types, closure, nullability,
ordering, and invariants.

Every contract-owned object is closed: additional fields are rejected. Every
listed field is required, including fields whose declared type permits
`null`. Missing fields and unsupported enum values are rejected. The only
source-owned extension value is `normalized_evidence`; it is not permission to
extend a surrounding platform object, and its named source schema must itself
be closed.

The following primitive rules apply everywhere:

- `string` is UTF-8, Unicode NFC, and contains no control character except
  where a source schema explicitly permits escaped JSON whitespace.
- `integer` is a JSON integer in `0..9007199254740991`. Negative values,
  fractions, exponents, and negative zero are rejected for integer fields.
- A general JSON number must be finite and exactly representable as an IEEE
  754 binary64 value. NaN, infinities, and negative zero are rejected. Exact
  decimals and integers outside the portable JSON safe-integer range are
  encoded as strings under the source-owned schema.
- A `digest` is `sha256:` followed by exactly 64 lowercase hexadecimal
  characters.
- A `git_commit` is exactly 40 lowercase hexadecimal characters.
- A timestamp is an RFC 3339 UTC string ending in `Z`, with zero through nine
  fractional digits. A fractional part has no trailing zero. Offsets, leap
  seconds, zero dates, and unrepresentable dates are rejected.
- No value is nullable unless its table says so. A required nullable field is
  serialized explicitly as JSON `null`.

The executable V1 profile accepts only fixed ASCII schema keys, JSON safe
integers, booleans, nulls, arrays, objects, and NFC string values. It rejects
floating-point values. Under that profile, the reference serializer emits
RFC 8785-compatible JCS bytes without implementation-dependent number
rendering. A future profile that admits general JSON numbers must implement
the complete RFC 8785 number algorithm and needs new golden vectors before it
can claim V1 interoperability.

## Closed Root Schema

The root is `SynchronizedEvidenceBundleV1`. Its closed fields are listed in
canonical presentation order. RFC 8785 determines object-key order for hash
bytes; this table determines the stable logical field order for non-JSON
representations and reviews.

| Order | Field | Type | Null | Rule |
| ---: | --- | --- | --- | --- |
| 1 | `contract` | string | no | Exact contract identifier from this page. |
| 2 | `schema_version` | integer | no | Exact value `1`. |
| 3 | `bundle_id` | string | no | Content-addressed identity derived as specified below. |
| 4 | `captured_at` | timestamp | no | Bundle finalization observation from the one capture clock. |
| 5 | `capture_window` | `CaptureWindowV1` | no | Exact pre/action/post interval. |
| 6 | `clock` | `CaptureClockV1` | no | The bundle's one capture clock. |
| 7 | `scope` | `CaptureScopeV1` | no | Closed capture purpose, source kinds, and phases. |
| 8 | `mask_tier` | string enum | no | Exact value `redacted` in V1. |
| 9 | `auth_scope` | `AuthScopeV1` | no | Effective authorization after policy evaluation. |
| 10 | `limits` | `CaptureLimitsV1` | no | Effective budgets, each at or below the V1 ceiling. |
| 11 | `evidence_refs` | array of `EvidenceRefV1` | no | Non-empty immutable provenance set. |
| 12 | `sources` | array of `SourceRecordV1` | no | Non-empty; deterministic order defined below. |
| 13 | `artifacts` | array of `SourceArtifactV1` | no | May be empty only when every source has a negative state. |
| 14 | `recorder_version` | string | no | Immutable component version. |
| 15 | `replay_version` | string | no | Immutable replay algorithm version required by this bundle. |
| 16 | `bundle_hash` | digest | no | Redacted JCS hash defined below. |

`recorder_version` and `replay_version` have exact form
`<semver>+git.<git_commit>`; mutable branch names, tags without a commit, and
the words `latest` or `current` are invalid. The root `evidence_refs` array is
the sorted, duplicate-free union of the action marker and source-record refs.

### Capture scope

`CaptureScopeV1` is closed:

| Order | Field | Type | Null | Rule |
| ---: | --- | --- | --- | --- |
| 1 | `purpose` | string enum | no | Exact value `SYNCHRONIZED_EVIDENCE_ONLY`. |
| 2 | `source_kinds` | array of string enum | no | Non-empty subset of `EBUS`, `EEBUS`, `CLOUD_APP`. |
| 3 | `phases` | array of string enum | no | Exact sequence `pre`, `action`, `post`. |

`source_kinds` is ordered `EBUS`, `EEBUS`, `CLOUD_APP`, with no duplicate.
The root has at least one `SourceRecordV1` for every declared source kind.

### Effective authorization scope

`AuthScopeV1` is closed:

| Order | Field | Type | Null | Rule |
| ---: | --- | --- | --- | --- |
| 1 | `authority` | string enum | no | Exact value `effective`; caller-claimed scope is never authoritative. |
| 2 | `permissions` | array of string | no | Non-empty, unique, ascending bytewise UTF-8 order. |

Every permission is a non-empty printable ASCII capability name of at most 128
bytes. Source and artifact authorization scopes are the effective scopes for
their acquisition operations and must be subsets of the root scope. An
artifact repeats its source record's exact `auth_scope`; replay never broadens
or re-masks it.

## One Capture Clock

One bundle has exactly one capture clock. All wall and monotonic observations,
the pre/action/post window, acquisition measurements, artifacts, and
`captured_at` bind to that clock. Mixing process clocks, resetting the
monotonic origin, or substituting a source timestamp for an acquisition
timestamp is a contract violation.

`CaptureClockV1` is closed:

| Order | Field | Type | Null | Rule |
| ---: | --- | --- | --- | --- |
| 1 | `clock_id` | string enum | no | Exact value `capture-clock-1`. |
| 2 | `wall_anchor` | timestamp | no | First wall observation. |
| 3 | `monotonic_anchor_ns` | integer | no | Exact value `0`; all monotonic values are offsets from it. |
| 4 | `captured_offset_ns` | integer | no | Monotonic offset corresponding to root `captured_at`. |
| 5 | `resolution_ns` | integer | no | Positive measured clock resolution. |
| 6 | `maximum_skew_ns` | integer | no | Computed upper bound below. |
| 7 | `observations` | array of `ClockObservationV1` | no | At least two bracketing observations. |

`ClockObservationV1` is closed and contains `observed_at` (timestamp),
`offset_ns` (integer), and `uncertainty_ns` (integer), in that order. The first
observation has `offset_ns=0` and `observed_at=wall_anchor`. Observations sort
by ascending `offset_ns`; duplicate offsets are rejected. The last observation
must be at or after `captured_offset_ns` and every source acquisition end.

For each observation, let `wall_delta_ns` be the exact nanosecond difference
between `observed_at` and `wall_anchor`. The required bound is:

```text
maximum_skew_ns = max(abs(wall_delta_ns - offset_ns) + uncertainty_ns)
```

The stored value must equal that result, not merely exceed it. Each source and
artifact wall timestamp must correspond to its stored monotonic offset within
`maximum_skew_ns`. `captured_at` must correspond to `captured_offset_ns` under
the same rule.

### Capture window and action marker

`CaptureWindowV1` is closed and contains `pre` (`WindowSegmentV1`), `action`
(`ActionWindowV1`), and `post` (`WindowSegmentV1`), in that order.

`WindowSegmentV1` is closed and contains `start_offset_ns` and
`end_offset_ns`, both integers. `ActionWindowV1` is closed:

| Order | Field | Type | Null | Rule |
| ---: | --- | --- | --- | --- |
| 1 | `start_offset_ns` | integer | no | Start of the externally observed action interval. |
| 2 | `marker_offset_ns` | integer | no | Capture-clock position of the action marker. |
| 3 | `marker_captured_at` | timestamp | no | Wall observation stored verbatim. |
| 4 | `marker_id` | string | no | Per-bundle pseudonym, never an external event or device id. |
| 5 | `evidence_ref` | `EvidenceRefV1` | no | Immutable, redacted marker provenance. |
| 6 | `end_offset_ns` | integer | no | End of the externally observed action interval. |

Intervals are non-empty and contiguous:

```text
pre.start_offset_ns < pre.end_offset_ns
pre.end_offset_ns = action.start_offset_ns
action.start_offset_ns <= action.marker_offset_ns <= action.end_offset_ns
action.start_offset_ns < action.end_offset_ns
action.end_offset_ns = post.start_offset_ns
post.start_offset_ns < post.end_offset_ns <= captured_offset_ns
```

The marker is supplied by an external observer or fixture before it is
recorded. It describes that an action was observed; it is not a command. The
recorder must not initiate the marked action, call a mutation API, or cause a
state transition. The bundle contains no requested value, credential, or
write target for the action.

## Immutable Evidence References

`EvidenceRefV1` is closed:

| Order | Field | Type | Null | Rule |
| ---: | --- | --- | --- | --- |
| 1 | `kind` | string enum | no | `CONTENT` or `GIT_BLOB`. |
| 2 | `digest_algorithm` | string enum | no | `SHA256_CONTENT_BYTES` or `SHA256_GIT_BLOB_V1`, matching `kind`. |
| 3 | `digest` | digest | no | Domain-separated digest defined below. |
| 4 | `repository` | string | yes | Required only for `GIT_BLOB`. |
| 5 | `commit` | `git_commit` | yes | Required only for `GIT_BLOB`. |
| 6 | `path` | string | yes | Required only for `GIT_BLOB`; repository-relative normalized path. |

For `CONTENT`, the last three fields are `null`. For `GIT_BLOB`, all three
are non-null, `repository` is an immutable owner/repository name, and `path`
is non-empty. Absolute paths, empty components, `.`, `..`, backslashes, NUL,
and percent-encoded traversal are rejected. Mutable URLs, branch refs, query
parameters, and redirects are not evidence refs.

The two reference algorithms are deliberately separate from artifact and
bundle JCS hashes:

- `SHA256_CONTENT_BYTES` hashes ASCII
  `HELIANTHUS:EVIDENCE-CONTENT:V1`, one NUL byte, then the exact immutable
  redacted content bytes. JSON content bytes must already be RFC 8785 JCS.
- `SHA256_GIT_BLOB_V1` hashes ASCII
  `HELIANTHUS:EVIDENCE-GIT-BLOB:V1`, one NUL byte, the UTF-8 repository, one
  NUL byte, the lowercase commit, one NUL byte, the normalized path, one NUL
  byte, then the exact Git blob bytes at that tuple.

Neither algorithm parses or assumes JSON for arbitrary Git blobs. A kind and
algorithm mismatch is rejected before dereference.

References sort by `kind`, `digest_algorithm`, `digest`, nullable `repository`,
nullable `commit`, then nullable `path`, comparing null before a string and
strings by bytewise UTF-8 order. Exact duplicate references are rejected.

## Immutable Source-Schema Authority

Offline replay accepts only source contracts listed in the closed
`helianthus.platform.source-schema-registry.v1`. Each registry entry binds
`source_kind`, `source_contract`, `source_schema_version`, canonical owner
repository/path/commit, schema SHA-256, and an optional embedded schema path.
The canonical machine-readable registry is
`schemas/synchronized-evidence-source-registry-v1.json`.

The eeBUS entry pins the immutable MSP-06 schema ref and digest stated at the
top of this page. B509, B524, B555, and cloud/app normalized inputs use the
closed schemas next to the registry. Their owner references identify the
canonical protocol or platform source; the embedded schema digest identifies
the exact offline validation bytes. Replay does not fetch a repository,
resolve a branch, or consult a mutable schema catalog. A source binding that
is absent from this registry or differs in any authority field is rejected.

`SourceBindingV1` is the complete comparability object. Its closed fields are:

- runtime kind and per-bundle runtime pseudonym;
- operation/tool id and immutable operation version;
- request scope and snapshot scope;
- the source kind, contract, schema version, owner repository/path/commit, and
  schema SHA-256 from the registry;
- the exact capture window, mask tier, and effective authorization scope; and
- complete `EBusSourceIdentityV1` for eBUS, otherwise explicit `null`.

The exact machine field names and types are normative in
`schemas/synchronized-evidence-bundle-v1.schema.json`. The full binding is
copied into the source and every owned artifact, included in the artifact and
bundle hash views, and emitted in each future-candidate-input row. Missing
binding fields make hashes non-comparable and prevent a `PRESENT` source.

## Source Records

`SourceRecordV1` is closed. A source record represents one source kind in one
phase and ends in exactly one terminal state.

| Order | Field | Type | Null | Rule |
| ---: | --- | --- | --- | --- |
| 1 | `contract` | string | no | Exact root `contract`. |
| 2 | `schema_version` | integer | no | Exact root `schema_version`. |
| 3 | `source_id` | string | no | Per-bundle pseudonym described below. |
| 4 | `source_kind` | string enum | no | `EBUS`, `EEBUS`, or `CLOUD_APP`. |
| 5 | `phase` | string enum | no | `pre`, `action`, or `post`. |
| 6 | `state` | string enum | no | `PRESENT`, `WITHHELD`, `NOT_TESTED`, or `UNAVAILABLE`. |
| 7 | `error_category` | string enum | yes | State-specific category; never free text. |
| 8 | `source_contract` | string | no | Frozen producer contract identifier. |
| 9 | `source_schema_version` | integer | no | Producer schema version used to validate evidence. |
| 10 | `source_binding` | `SourceBindingV1` | no | Complete immutable source/comparability binding. |
| 11 | `capture_window` | `CaptureWindowV1` | no | Exact deep-equal copy of the root window. |
| 12 | `clock` | `CaptureClockV1` | no | Exact deep-equal copy of the root clock. |
| 13 | `scope` | `CaptureScopeV1` | no | Exact deep-equal copy of the root scope. |
| 14 | `mask_tier` | string enum | no | Exact root `mask_tier`. |
| 15 | `auth_scope` | `AuthScopeV1` | no | Effective source-operation scope. |
| 16 | `evidence_refs` | array of `EvidenceRefV1` | no | Non-empty immutable redacted provenance. |
| 17 | `recorder_version` | string | no | Exact root `recorder_version`. |
| 18 | `replay_version` | string | no | Exact root `replay_version`. |
| 19 | `acquisition_started_at` | timestamp | yes | Wall start; null only as allowed by the state matrix. |
| 20 | `acquisition_ended_at` | timestamp | yes | Wall end; null only as allowed by the state matrix. |
| 21 | `acquisition_start_offset_ns` | integer | yes | Monotonic start on the bundle clock. |
| 22 | `acquisition_end_offset_ns` | integer | yes | Monotonic end on the bundle clock. |
| 23 | `measured_latency_ns` | integer | yes | Exact end offset minus start offset. |
| 24 | `maximum_skew_ns` | integer | no | Exact root clock `maximum_skew_ns`. |
| 25 | `ebus_identity` | `EBusSourceIdentityV1` | yes | Exact binding copy for eBUS; otherwise null. |
| 26 | `artifact_ids` | array of string | no | Content-addressed artifacts owned by this record. |

The five acquisition timing fields are either all non-null or all null. When
non-null, start is not after end, both offsets lie in the named phase, wall
values satisfy the clock skew bound, and `measured_latency_ns` equals
`acquisition_end_offset_ns - acquisition_start_offset_ns`. `NOT_TESTED`
requires all five to be null. `PRESENT` and `UNAVAILABLE` require all five.
`WITHHELD` permits either form because policy may prevent acquisition or
redaction may reject an acquired value.

### Closed terminal states

| State | `error_category` | `artifact_ids` | Meaning |
| --- | --- | --- | --- |
| `PRESENT` | `null` | One or more | At least one valid redacted artifact was captured. |
| `WITHHELD` | `POLICY_WITHHELD`, `AUTHORIZATION_DENIED`, `REDACTION_FAILED`, or `EXACT_IDENTITY_MISSING` | Empty | Evidence was not publishable or could not be bound safely. |
| `NOT_TESTED` | `NOT_SELECTED`, `BUDGET_EXHAUSTED`, or `EXACT_IDENTITY_MISSING` | Empty | Acquisition was intentionally not attempted. |
| `UNAVAILABLE` | `BACKEND_UNAVAILABLE`, `TIMEOUT`, or `ACQUISITION_FAILED` | Empty | A permitted acquisition was attempted but yielded no evidence. |

There is no empty success: `PRESENT` with an empty artifact list is invalid,
and every non-`PRESENT` state requires an empty artifact list. A terminal state
describes only this bounded capture and is not a claim about another run or a
device class.

### Error precedence

The recorder applies this deterministic error precedence and stops evaluating
a source at the first applicable step:

1. Root shape, schema, scope, limits, and clock validation fail the whole
   capture with no bundle.
2. A source excluded by the valid scope becomes `NOT_TESTED/NOT_SELECTED`.
3. Policy refusal becomes `WITHHELD/POLICY_WITHHELD`.
4. Insufficient effective authorization becomes
   `WITHHELD/AUTHORIZATION_DENIED`.
5. Missing exact eBUS identity becomes `NOT_TESTED/EXACT_IDENTITY_MISSING`
   before acquisition or `WITHHELD/EXACT_IDENTITY_MISSING` after acquisition.
6. An exhausted reserved budget becomes `NOT_TESTED/BUDGET_EXHAUSTED`.
7. A definitely unreachable source becomes
   `UNAVAILABLE/BACKEND_UNAVAILABLE`.
8. A deadline expiration becomes `UNAVAILABLE/TIMEOUT`.
9. Another bounded acquisition failure becomes
   `UNAVAILABLE/ACQUISITION_FAILED`.
10. Failure to produce a public redacted artifact after acquisition becomes
    `WITHHELD/REDACTION_FAILED`.

Errors are category-only and non-reflective. No native error string, user
input, endpoint, identity, path, payload fragment, or credential is copied into
the bundle. Unsupported or internally contradictory states are contract
violations and abort the bundle rather than inventing another state.

### Exact eBUS source-family identity

`EBusSourceIdentityV1` is a closed discriminated union. Every variant carries
`family` and a per-bundle `target_pseudonym`; the remaining mandatory fields
are family-specific:

| Family | Complete required identity |
| --- | --- |
| `B509` | target address, target product class, register family, 16-bit register id, unit/scale source, and evidence role `AUTHORITATIVE`, `MIRROR`, or `FALLBACK` |
| `B524` | source and target address context, full `(opcode, GG, II, RR)`, group meaning, instance gate, register category, and unit/scale source |
| `B555` | device family, schedule/program identity, slot index, day-of-week identity, time identity, operation-mode context, and unit/scale source |

The exact fields, enums, ranges, and closure rules are normative in the three
`schemas/synchronized-evidence-source-ebus-*-v1.schema.json` files. For B524,
`opcode`, `GG`, and `II` are in `0..255`; `RR` is in `0..65535`. OP=0x02 and
OP=0x06 are separate namespaces even when `GG`, `II`, and `RR` match. B509
target product is mandatory because register addresses collide across product
classes. B555 device family and selector context are mandatory because timer
transport and selector namespaces differ across controller families.

Within a bundle, one physical source/target identity maps injectively to one
pseudonym and every repeated occurrence of that identity reuses the same
pseudonym. Two different identities cannot share a pseudonym. The ephemeral
input-to-pseudonym map is not persisted. These rules preserve equality needed
for synchronized comparison without creating a cross-bundle correlator.

A `PRESENT` EBUS record requires this identity before its artifact can be
accepted. There is no inferred tuple, no log-scraping guess, no family or
device inheritance, and no sibling-record fallback. Missing B509/B524/B555
identity produces `WITHHELD` or `NOT_TESTED` under the precedence rule. The
contract never invents source identity from a semantic leaf, device model,
nearby log line, or another capture.

## Source Artifacts

`SourceArtifactV1` is closed:

| Order | Field | Type | Null | Rule |
| ---: | --- | --- | --- | --- |
| 1 | `contract` | string | no | Exact root `contract`. |
| 2 | `schema_version` | integer | no | Exact root `schema_version`. |
| 3 | `artifact_id` | string | no | Content-addressed identity defined below. |
| 4 | `source_id` | string | no | Must resolve to exactly one `PRESENT` source. |
| 5 | `source_kind` | string enum | no | Exact owning source kind. |
| 6 | `phase` | string enum | no | Exact owning source phase. |
| 7 | `source_contract` | string | no | Exact owning source contract. |
| 8 | `source_schema_version` | integer | no | Exact owning source schema version. |
| 9 | `source_binding` | `SourceBindingV1` | no | Exact owning source binding. |
| 10 | `ebus_identity` | `EBusSourceIdentityV1` | yes | Exact binding copy for eBUS; otherwise null. |
| 11 | `source_observed_at` | timestamp | no | Timestamp supplied by the source-owned contract; never replaced by recorder time. |
| 12 | `recorder_ingested_at` | timestamp | no | Recorder wall observation when the validated payload entered the bundle. |
| 13 | `recorder_ingested_offset_ns` | integer | no | Same ingestion event on the one monotonic capture clock. |
| 14 | `capture_window` | `CaptureWindowV1` | no | Exact deep-equal copy of the root window. |
| 15 | `clock` | `CaptureClockV1` | no | Exact deep-equal copy of the root clock. |
| 16 | `scope` | `CaptureScopeV1` | no | Exact deep-equal copy of the root scope. |
| 17 | `mask_tier` | string enum | no | Exact root `mask_tier`. |
| 18 | `auth_scope` | `AuthScopeV1` | no | Exact owning source scope and a subset of root effective permissions. |
| 19 | `evidence_refs` | array of `EvidenceRefV1` | no | Non-empty immutable redacted provenance. |
| 20 | `recorder_version` | string | no | Exact root `recorder_version`. |
| 21 | `replay_version` | string | no | Exact root `replay_version`. |
| 22 | `remasking` | `RemaskingV1` | no | Per-bundle remasking manifest described below. |
| 23 | `item_count` | integer | no | Recomputed source-schema item count, within effective limits. |
| 24 | `byte_count` | integer | no | JCS byte length of `normalized_evidence`. |
| 25 | `normalized_evidence` | source-schema JSON value | no | Redacted raw normalized evidence, validated before persistence. |
| 26 | `redacted_hash` | digest | no | Artifact hash defined below. |

Raw normalized evidence means source-owned read-only observations normalized
to their frozen schema. It does not mean a raw packet, wire transcript, native
object dump, or unredacted preimage. Platform validation treats the value as
opaque after the named source validator closes and validates it; the platform
does not rename, interpret, or copy eeBUS-native fields into another surface.

`source_observed_at` and recorder ingestion time are intentionally distinct.
Source time preserves the frozen source contract's observation and may predate
the capture window; freshness is not inferred from it. The recorder clock
binds acquisition and ingestion to the synchronized window. A producer must
not copy recorder time into `source_observed_at` when the source supplied a
different timestamp, and replay emits both values verbatim.

`RemaskingV1` is closed and contains `method` (exactly
`PER_BUNDLE_CSPRNG`), one per-bundle `scope_id`, and ordered unique entries of
JSON Pointer plus a 43-character base64url pseudonym. Every eeBUS identity
`digest` and every cloud subject pseudonym in normalized evidence must appear
in this manifest and equal the value at its pointer. Field names remain those
of the pinned source schema; only their values are remasked. A runtime-scoped
opaque token may never pass through unchanged or become a cross-bundle
correlator.

## Ordering And Duplicate Rejection

The following deterministic ordering is mandatory. All comparisons use
bytewise UTF-8 order unless a numeric or enum rank is stated. Producers must
emit and validators must require:

1. `sources` sorted by phase rank `pre`, `action`, `post`, then source-kind
   rank `EBUS`, `EEBUS`, `CLOUD_APP`, then `source_id`;
2. `artifacts` sorted by phase rank, source-kind rank, `source_id`, then
   `artifact_id`;
3. each `artifact_ids` array sorted ascending;
4. all evidence refs sorted by the key defined above; and
5. authorization permissions sorted ascending; and
6. remasking entries sorted by JSON Pointer, then pseudonym.

Duplicate source key `(phase, source_kind, source_id)`, duplicate
`artifact_id`, duplicate `artifact_ids` entry, duplicate evidence ref, or
duplicate permission is rejected. An artifact referenced by zero sources,
more than one source, or a non-`PRESENT` source is rejected. Reordering is not
performed silently because accepting noncanonical order would hide producer
drift.

## Redacted Hashes And Content Addressing

All hashes use SHA-256 over an explicit ASCII domain separator followed by one
NUL byte and then RFC 8785 JSON Canonicalization Scheme (JCS) bytes. Hashing
occurs only after redaction, schema validation, ordering validation, and limit
validation.

For an artifact, remove `artifact_id` and `redacted_hash` and hash the
remaining closed object with this domain separator:

```text
HELIANTHUS:SYNCHRONIZED-EVIDENCE-ARTIFACT:V1
```

Set `redacted_hash` to `sha256:<hex>` and `artifact_id` to
`seav1:sha256:<hex>` using the same digest.

For a bundle, remove `bundle_id` and `bundle_hash` and hash the remaining
closed root with this domain separator:

```text
HELIANTHUS:SYNCHRONIZED-EVIDENCE-BUNDLE:V1
```

Set `bundle_hash` to `sha256:<hex>` and `bundle_id` to
`sebv1:sha256:<hex>` using the same digest. This makes bundle identity
content-addressed without a self-reference. A validator recomputes every
artifact hash before the bundle hash and rejects any mismatch. Hash comparison
is valid only when contract, schema version, recorder/replay version, scope,
capture window, clock, mask tier, effective auth scope, source contract, and
source schema version all match exactly.

## Offline, Side-Effect-Free Replay

Replay accepts exactly the immutable bundle bytes and an implementation that
supports the recorded `replay_version`. It validates closure and limits before
allocating source-sized structures, validates all source-owned payloads using
the recorded schema, verifies references and hashes, and emits canonical
`ReplayResultV1`.

Replay is offline and side-effect-free. It has no network, no cloud, no runtime,
no wall clock, no randomness, no locale, no host-path, and no mutable-store
dependency. It reads no environment variable, credential,
configuration file, DNS result, system time, temporary path, installation
registry, or cache. A test harness must fail replay if any such capability is
requested.

`ReplayResultV1` is closed and contains, in order:

| Field | Type | Rule |
| --- | --- | --- |
| `contract` | string | Exact value `helianthus.platform.synchronized-evidence-replay.v1`. |
| `schema_version` | integer | Exact value `1`. |
| `bundle_id` | string | Verified input bundle id. |
| `raw_normalized_evidence` | array | Exact canonical artifact evidence in artifact order. |
| `captured_timestamps` | array of timestamp | Marker, source, and artifact timestamps in contract order. |
| `terminal_states` | array | Exact `(source_id, phase, state, error_category)` rows in source order. |
| `redacted_hashes` | array of digest | Recomputed artifact hashes followed by the bundle hash. |
| `future_candidate_inputs` | array | Artifact ids and provenance only, in artifact order. |

Every array item is itself a closed object. The normative item fields,
nullability, and enums are in
`schemas/synchronized-evidence-replay-v1.schema.json`; the corresponding
bundle envelope is in
`schemas/synchronized-evidence-bundle-v1.schema.json`. Replay output that is
not valid against the replay schema is a hard failure, even if its values
would otherwise compare equal.

Replay reuses captured timestamps verbatim. It does not call a clock, parse and
reformat a timestamp for output, substitute replay time, or derive a new
acquisition time. It regenerates the same raw normalized evidence, terminal
states, redacted hashes, and future candidate inputs for byte-identical valid
input.

`future_candidate_inputs` are inputs that a later M7 process may consume. M6.5
does not create candidate facts, comparators, semantic paths, conflict
decisions, promotion decisions, or consumer output. A replay mismatch is a
hard failure and produces no partial replay result.

## Bounded Cloud/App Input Seam

The recorder and replayer never log in to a cloud service. A `CLOUD_APP`
source enters only as a pre-captured, already redacted input object supplied on
the recorder's bounded local input seam. The seam accepts one declared source
contract/version, the source's original observation timestamp, the recorder's
ingestion timestamp and monotonic offset, one item count, one byte count, and
one immutable evidence ref. It applies the same closure, size, depth,
number, timestamp, ordering, auth, and redaction validation as any artifact.

The seam has no URL fetch, callback, browser session, SDK client, credential
lookup, refresh mechanism, or retry. Credentials are never embedded in a
bundle. Input arriving after its declared action or phase window is rejected,
not moved into a different phase.

## Privacy And Security

Every `source_id`, `runtime_pseudonym`, `target_pseudonym`, and `marker_id` is
a per-bundle pseudonym with the schema-defined kind prefix and 32 lowercase
hexadecimal characters.
They are minted during capture with a CSPRNG, stored verbatim for replay, and
must not be derived from source data. A value cannot be reused across bundles.
Any private mapping is outside the bundle, is never an evidence ref, and is
deleted no later than the bundle's private retention deadline.

Redaction happens before hashing and persistence. Every bundle, source, action
marker, error, reference, and normalized payload excludes:

- passwords, secrets, a private key, certificate material, an access token,
  and a refresh token;
- stable device identifiers, raw or hashed SKIs, SHIP IDs, serial numbers, or
  account identifiers;
- an IP address, MAC address, hostname, interface name, or other network
  endpoint;
- a raw packet, packet capture, wire transcript, protocol payload dump, or
  native object dump;
- a host path, username, environment value, command line, or process detail;
  and
- any `vendor_restricted` preimage, reversible transform, lookup table, or
  cross-bundle correlator.

Digests never make prohibited preimages publishable. Error output remains
category-only and non-reflective. Logging, string formatting, metrics, panic
paths, and validation failures obey the same exclusions. If the recorder
cannot prove that an acquired value is public-safe, the source is `WITHHELD`
and no artifact is persisted.

## Capture Budgets And Parser Limits

The recorder is disabled by default. Enabling it requires an explicit local
configuration naming the scope, destination root, retention, quota, and every
effective limit. Omitted, zero, negative, or above-ceiling values fail closed.

`CaptureLimitsV1` is closed and records these positive integer fields in this
order: `max_sources`, `max_items_per_source`, `max_artifact_bytes`,
`max_bundle_bytes`, `max_depth`, `max_string_bytes`,
`max_capture_duration_ns`, and `max_source_duration_ns`.

V1 hard ceilings are:

| Limit | Ceiling |
| --- | ---: |
| Sources per bundle | 64 |
| Items per source | 4,096 |
| One artifact | 1,048,576 bytes |
| One bundle | 67,108,864 bytes |
| JSON nesting depth | 32 |
| One string | 65,536 UTF-8 bytes |
| Total pre/action/post capture | 900,000,000,000 ns |
| One source acquisition | 60,000,000,000 ns |

The effective values may be lower and are hash-bound in `limits`. The recorder
reserves the configured worst-case bytes and source slots before acquisition.
It does not start a capture that cannot fit its time, count, memory, or storage
budget. Parsers enforce maximum source/item/byte/depth limits incrementally
before decoding or allocating the claimed amount.

The capture clock's computed and declared `maximum_skew_ns` are each capped at
1,000,000,000 ns in V1. A higher value is not degraded evidence; it rejects the
bundle because the sources are not synchronized enough for comparison.

## Persistence, Retention, And Recovery

The store root and every created directory use mode `0700`; staging and final
bundle files use mode `0600`. The implementation rejects a symlink in every
path component, path traversal, absolute user-supplied paths, hard-link count
other than one, non-regular files, and a destination that escapes the opened
store root. Path checks operate on directory handles, not on later string
re-resolution.

Exactly one writer holds an exclusive store lock for capture, publication,
retention, drop, and crash recovery. The portable Linux profile uses an
advisory file lock held on an opened regular file below the verified store
root. Startup fails closed when the lock cannot be acquired, when the
filesystem does not provide process-visible locking semantics, or when lock
ownership cannot be verified. There is no lockless fallback. Read-only replay
of an already opened immutable bundle may run concurrently and never mutates
the store.

A successful write follows this order:

1. Reserve quota for the configured maximum and open a same-directory staging
   file with exclusive create and no-follow semantics.
2. Write one validated canonical bundle, flush application buffers, and
   `fsync` the staging file.
3. Re-read and verify its length, closed schemas, artifact hashes, bundle hash,
   and `bundle_id`.
4. Perform an atomic replace of the staging directory entry into the freshly
   reserved final `bundle_id` name using no-replace semantics. An existing
   destination is a hard collision failure and is never overwritten.
5. `fsync` the containing directory before reporting success.

Once visible, a bundle is an immutable capture: it is never appended,
re-masked, repaired in place, or partially trimmed. Quota is checked before
capture and again before publication. Retention removes only complete expired
bundles. An explicit authorized drop removes exactly one complete bundle,
then fsyncs the directory; a missing id returns the idempotent category
`ALREADY_GONE`. Quota or retention pressure never deletes an active staging
file or edits a retained bundle. If no complete bundle can be removed under
policy, the new capture fails with `QUOTA_EXCEEDED` and publishes nothing.

Crash recovery deletes abandoned staging files, verifies every visible final
file, and quarantines a malformed final file without rewriting it. It does not
claim success for a bundle whose directory fsync was not completed. Replay of
a valid retained bundle remains independent of the retention index or any
other mutable store.

Rollback is deterministic: disable the recorder and reject new capture
requests. Disabling opens no source or transport and changes no existing
read-only surface. Retained immutable bundles remain verifiable and droppable
under the same policy; rollback never requires editing them.

## Version And Evolution Rules

V1 is closed. Adding, removing, renaming, reordering, or changing the type or
nullability of a field; changing an enum, state mapping, limit ceiling,
ordering key, domain separator, hash view, pseudonym rule, timestamp rule, or
replay output requires a new platform contract and `schema_version`.

A new source-owned payload schema may be used only with a new immutable
`source_contract` or `source_schema_version`, explicit recorder and replay
support, and new golden replay fixtures. It cannot change this envelope or
smuggle a platform field into `normalized_evidence`. Consumers reject an
unsupported platform or source version before interpreting payload data.

No V1 migration rewrites a bundle. Conversion creates a new content-addressed
bundle with new provenance and preserves the old bundle unchanged. Hashes from
different versions or binding dimensions are not comparable.

## Acceptance Fixture

The canonical executable inventory is the two JSON schemas, the closed source
registry, the positive bundle, golden replay, and named negative fixtures under
`schemas/` and `fixtures/synchronized-evidence/v1/`, validated by
`scripts/validate_synchronized_evidence.py`. The validator is offline,
category-only on failure, and supports only the safe V1 JCS subset.

The MSP-065 smoke fixture is a deterministic redacted replay bundle containing
`PRESENT` eBUS, eeBUS, and cloud/app sources. Its negative corpus contains
terminal negative and malformed cases. Acceptance
requires two isolated replays to produce byte-identical `ReplayResultV1`
output, original captured timestamps, identical redacted hashes, and identical
future candidate inputs while network, cloud, runtime, clock, randomness,
locale, host paths, and mutable storage are unavailable. The fixture must also
prove rejection for unknown fields, duplicate bindings, incomplete
B509/B524/B555 identities, clock skew, prohibited privacy values, missing
per-bundle remasking, over-limit values, terminal-state contradictions,
noncanonical references, and hash mismatch.
