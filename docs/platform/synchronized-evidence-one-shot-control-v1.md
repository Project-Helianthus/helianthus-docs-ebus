# Synchronized Evidence One-Shot Control V1

Canonical source: this page and
`schemas/synchronized-evidence-one-shot-control-v1.schema.json`.

Status: closed language-neutral owner-only control contract for
MSP-065-LIVE-R1.

Issue provenance:
`Project-Helianthus/helianthus-docs-ebus#382`.

## Boundary

The private tool name is
`helianthus.v1.synchronized_evidence.capture`. It accepts only the closed
empty argument object. It is served only on the already existing `AF_UNIX` operator socket
and only to a peer with the same effective UID, established
from operating-system peer credentials before request processing. It creates
no listener, TCP endpoint, HTTP route, or LAN surface; the public `tools/list` omits
the tool and no public dispatcher accepts its name.

The response is the closed `ReceiptV1` object. It contains one category and
nothing else. The response and logs contain no raw evidence, normalized
payload, target, pseudonym, timestamp, path, hash, bundle identifier, or
source identifier.

## Fixed Input And Store

The empty tool call activates one request already present at
`/data/synchronized-evidence/one-shot-request-v1.json`. The request must be an
owner-owned regular file with exact mode `0600`. The implementation opens the
verified `/data/synchronized-evidence` directory and uses a
descriptor-relative no-symlink/no-traversal loader. It rejects symlinks,
non-regular files, path substitution, traversal, owner mismatch, mode
mismatch, and a file changed between metadata verification and read.

The only store is `/data/synchronized-evidence/store`. Store lock, staging,
publication, recovery, retention, and immutable-bundle rules are those of
`SynchronizedEvidenceBundleV1`. All store traversal is descriptor-relative
below the already verified store descriptor; symlinks and path escape fail
closed.

The request is closed by the machine schema. It contains the action evidence
reference and the pre-captured `CLOUD_APP` action evidence. The two evidence
references must be byte-identical canonical values. The caller cannot supply targets,
selectors, feature addresses, remote identities, masks, batch parameters,
timestamps, or output paths.

## Deterministic Acquisition

After request validation, the implementation selects all server Measurement, Setpoint, and HVAC features
visible to the established runtime binding. It does not select client or
special-role features and does not infer targets from the cloud/app value.

Selection is sorted by the complete native tuple before pseudonymization:
native service, entity, feature, and every field-path component, followed by
feature type and function as bytewise ASCII tie breakers. No component may be
dropped, shortened, hashed, or replaced by a display label for sorting.
Acquisition preserves that order and the maximum batch size is exactly 16.
The final batch may be smaller. Discovery returning no eligible feature is an
acquisition failure, not an empty successful bundle.

The recorder uses only
`("EEBUS", "helianthus.eebus.m625.public-redacted-evidence.v1", 1)` for this
read. Every selected result is normalized against the pinned source schema,
then independently remasked into the new synchronized-evidence bundle.

## Crash Idempotency

The idempotency key is the canonical action evidence ref plus the M6.25 source tuple.
While holding the store lock, the implementation performs a validated retained-bundle lookup
on that key before any acquisition, source timestamp,
randomness request, or staging-file creation. A retained candidate counts only
after the canonical bundle verifier and replay both succeed and the bundle
contains the exact key.

Exactly one valid retained match returns `EXISTING`. More than one valid match
or any conflicting retained candidate returns `CONFLICT`; neither case reads
the runtime. No mutable side index is authority for this decision.

For a new capture, all source and `CLOUD_APP` input validation completes
before the first read. The completed candidate contract requires that two offline byte-identical replays consume the finalized canonical staging bytes
before atomic publication. Each replay has no runtime, network, clock, randomness,
or mutable-store input. Any byte difference returns `REPLAY_MISMATCH` and
publishes nothing.

Publication follows the synchronized-evidence durable-write order. The
implementation atomically publishes the bundle, then re-opens the final bundle, validates it, and verifies replay
against the prepublication result. It syncs the containing directory and may
publish or return a success receipt only after all of those steps complete. A
crash after bundle publication but before the response is recovered by the
retained-bundle lookup.

A repeated call, including after process restart, may perform the required
request and store reads, retained-bundle validation, and offline replay before
returning `EXISTING`. It performs no runtime, network, or source-acquisition I/O
and creates no new timestamps, bundle, pseudonyms, or staging artifact. The
result does not depend on a process-local cache.

## Failure Surface

Failures are category-only. `INVALID_REQUEST`, `PERMISSION_DENIED`,
`CONFLICT`, `ACQUISITION_FAILED`, `REPLAY_MISMATCH`, `PUBLISH_FAILED`, and
`INTERNAL` publish no receipt claiming success. `PUBLISHED` is returned only
for a newly durable bundle; `EXISTING` is returned only for the validated
retained match described above.
