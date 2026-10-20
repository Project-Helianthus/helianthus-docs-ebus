# Driver Runtime API V1

## Status And Authority

Superseded: [runtime-driver-lifecycle.md](../architecture/runtime-driver-lifecycle.md)
now owns the runtime lifecycle contract: durable decisions, refusal order,
request members and control semantics; where the pages differ, the lifecycle
page governs.

This page freezes the target MCP-first public contract for the generic gateway
driver lifecycle. It is pending implementation. The process and provider
ownership model is defined in
[`../docs/platform/driver-runtime-manager-v1.md`](../docs/platform/driver-runtime-manager-v1.md).

The V1 MCP namespace contains exactly:

- `drivers.v1.list`
- `drivers.v1.start`
- `drivers.v1.stop`
- `drivers.v1.restart`

Tools stay registered for the process lifetime. Missing, disabled, failed, or
unavailable providers return typed snapshots; a mutation returns either the
desired-state result or a code from the lifecycle refusal table. Tool
disappearance and protocol-specific ad-hoc errors are forbidden.

## Closed Driver Catalog

V1 recognizes exactly these IDs:

- `ebus.primary`
- `modbus.tcp.default`
- `eebus.primary`

The desired-state vocabulary is exactly `RUNNING`, `STOPPED`. The
observed-state vocabulary is exactly `DISABLED`, `STOPPED`, `STARTING`,
`RUNNING`, `DEGRADED`, `BACKOFF`, `STOPPING`, `FAILED`.

Unknown IDs are rejected with `NOT_FOUND`. IDs are ASCII lowercase
catalog tokens, not paths or caller-defined values. V1 never accepts an
endpoint, address, certificate identifier, device identity, or transport name
in place of a catalog ID.

## `DriverSnapshotV1`

Every list/get snapshot uses the following closed shape. Mutation results use
the smaller desired-state result defined under Mutating Tools:

The lifecycle evidence fields are `reason`, `retry`, `generation`,
`desired_revision`, `revision`, `attempt`, `capabilities`, `effective_capabilities`, and
`safety_quarantined`.

```json
{
  "schema_version": 1,
  "driver_id": "eebus.primary",
  "desired_state": "RUNNING",
  "observed_state": "BACKOFF",
  "reason": {
    "code": "DEPENDENCY_UNAVAILABLE",
    "retryable": true
  },
  "retry": {
    "eligible": true,
    "budget_remaining": 3,
    "not_before_utc": "2026-08-21T10:00:05Z"
  },
  "generation": 4,
  "desired_revision": "7",
  "revision": "29",
  "attempt": 2,
  "capabilities": ["DISCOVERY", "READ", "PAIRING", "TOPOLOGY"],
  "effective_capabilities": [],
  "safety_quarantined": false,
  "changed_at_utc": "2026-08-21T10:00:00Z"
}
```

All fields are required. Nullable values are encoded as JSON `null`, not
omitted. Arrays are sorted, duplicate-free, and never null. Unknown fields are
rejected by conformance fixtures until a later version adds them.

### Field Invariants

- desired state is operator intent; observed state is runtime fact. Consumers
  must not infer one from the other.
- `generation` starts at zero before any admitted provider instance and
  monotonically increases. The generation changes only when a new driver
  instance is admitted. It does not change for polling, retry scheduling, or a
  failed construction that never admitted an instance.
- `desired_revision` is the durable desired revision, encoded as a canonical
  decimal string of an unsigned 64-bit value. It is the only value a client
  echoes, unchanged, as `ExpectedRevision`. Observation-only changes do not
  advance it; accepted decisions advance the namespace mark and assign the new
  mark to this driver. A driver without a record returns STOPPED at the
  current mark. Repair assigns revisions above the validated pre-repair mark.
- `revision` is the view revision, equal to the lifecycle catalog revision and
  encoded as a separate canonical decimal string. It starts at one and
  monotonically increases; the revision changes on every externally visible
  snapshot mutation and never changes for a byte-identical replay. Every
  advance is durable before exposure, survives restart and is never reused;
  repair preserves it and advances it once. It is a view counter only and is
  never used as `ExpectedRevision` or for any optimistic control.
- attempt is scoped to one generation. It counts admission/recovery attempts
  beginning at one and resets only when a new generation is admitted. Zero is
  used before the first attempt.
- reason is a closed categorical value. It never carries an endpoint,
  credential, raw transport error, or protocol payload.
- `retry` is null unless an automatic retry decision exists. When present,
  `eligible`, `budget_remaining`, and `not_before_utc` are mutually coherent;
  a non-eligible retry has no deadline.
- capabilities are immutable for one generation, sorted, and derived from the
  admitted provider. A static capability change requires a new generation.
- effective capabilities are the currently admitted subset of `capabilities`.
  They are sorted, duplicate-free, and empty in `DISABLED`, `STOPPED`,
  `STARTING`, `BACKOFF`, `STOPPING`, and `FAILED`. `RUNNING` exposes the full
  static set; `DEGRADED` exposes a documented non-empty proper subset.
- `safety_quarantined` is true only after the manager cannot prove that an old
  provider instance closed. It is false for ordinary recoverable failures.
- Provider callbacks carry internal lifecycle correlation captured at admission.
  A callback with stale correlation cannot mutate the snapshot; internal
  correlation is not a client operation handle.
- timestamps are UTC RFC3339 values and are evidence, never ordering
  authority. The view `revision` is the view ordering authority.

### Closed Reason Codes

`reason.code` is one of:

| Code | Meaning |
| --- | --- |
| `NONE` | No degraded, retry, stop, or failure reason applies. |
| `CONFIG_DISABLED` | Persistent configuration disabled the driver. |
| `OPERATOR_STOPPED` | Runtime intent stopped the driver. |
| `START_REQUESTED` | An admitted start is in progress. |
| `STOP_REQUESTED` | An admitted stop is in progress. |
| `CONFIG_INVALID` | The driver's isolated configuration is invalid. |
| `PROVIDER_UNAVAILABLE` | The stable catalog entry has no constructible provider. |
| `DEPENDENCY_UNAVAILABLE` | A required adapter, endpoint, bus, or peer is unavailable. |
| `RUNTIME_NOT_READY` | Construction succeeded but required driver readiness did not. |
| `CAPABILITY_DEGRADED` | The provider safely serves only its declared degraded subset. |
| `RETRY_SCHEDULED` | A retryable failure entered bounded backoff. |
| `RETRY_EXHAUSTED` | The process-epoch retry budget ended. |
| `STOP_TIMEOUT` | Bounded drain expired; the adapter-owned close worker then proved that the old provider closed. |
| `CLOSE_UNCONFIRMED` | The adapter-owned close worker did not provide proof that the old provider closed. |
| `INTERNAL_ERROR` | A secret-free manager/provider invariant failed. |

`retryable` is true only for `DEPENDENCY_UNAVAILABLE`, `RUNTIME_NOT_READY`, or
`RETRY_SCHEDULED` while policy budget remains. Consumers do not infer retry
eligibility from the string alone; they use the explicit boolean and `retry`.

### Closed Capability Codes And Admission

V1 capability tokens are `DISCOVERY`, `READ`, `WRITE`, `PAIRING`, `TOPOLOGY`,
`RAW_EVIDENCE`, and `SEMANTIC_PROJECTION`. Capability presence describes what
the admitted generation can support; authorization and observed readiness are
separate. In particular, `WRITE` never grants a consumer permission to issue a
protocol write.

Every gateway path that can invoke a provider admits the invocation through
the manager's same per-driver admission lock. Admission checks the current
generation and requires the requested capability in `effective_capabilities`.
Start publishes effective capabilities only with its atomic transition to
`RUNNING` or `DEGRADED`. Stop or restart withdraws all effective capabilities
before publishing `STOPPING` in that same critical section. A request racing
after the withdrawal is blocked before provider invocation. Work admitted
before withdrawal is tracked as in-flight work and is owned by the bounded
drain. Therefore no provider invocation can be admitted after withdrawal.

This admission rule applies to MCP, GraphQL, Portal, Home Assistant, semantic
pollers, discovery, and protocol-specific diagnostics. No consumer may cache a
previous effective set as invocation authority.

### eBUS Transport Close Handshake

The eBUS transport seam is a data-only lifecycle handshake. `DriverRuntime` is
the sole sender to `CloseRequest`; the adapter owns the `CloseRequest` receiver
and close worker, which remains adapter-owned. After accepting its one request,
the adapter stops or finishes its own bounded protocol work. The adapter-owned
close worker fulfills this responsibility: the adapter closes `Closed` only
after its resources and adapter-owned closer retire. `Closed` is therefore
closure proof, not permission for the runtime to invoke a closer itself.

The runtime selects only on this request/proof pair. It never invokes an
arbitrary manager callback or starts a manager cleanup goroutine. The adapter
remains responsible for the worker, connections, listeners, and any
protocol-local teardown it needs to retire before proving closure.

The lifecycle handle must have a sendable `CloseRequest` and an open `Closed`
proof channel when admitted. A closed or invalid `CloseRequest` is a lifecycle
ownership violation: it is caught as failed close proof rather than permitted to
panic the process. A request that no adapter worker accepts before its deadline,
or an accepted request without a subsequent `Closed` proof, is likewise an
unproven close and follows the safety-quarantine rule below. The runtime does
not retry a close send in a background goroutine.

## `drivers.v1.list`

`drivers.v1.list` accepts no arguments and returns all three snapshots ordered
by driver ID. It is available whenever the gateway process is ready, including
when every protocol provider failed. The list is one coherent manager revision;
it is not assembled by independently querying transports.

Example result envelope:

```json
{
  "schema_version": 1,
  "manager_revision": "29",
  "drivers": []
}
```

`manager_revision` is the catalog revision, encoded as a canonical decimal
string and equal to each returned snapshot's view `revision`. List/get return
`desired_revision` and `revision` from one coherent cached transaction.

The real V1 result contains exactly three driver entries. The empty array above
illustrates envelope shape only and is not a valid V1 catalog result.

## Mutating Tools

`drivers.v1.start`, `drivers.v1.stop`, and `drivers.v1.restart` accept this
closed two-field request:

```json
{
  "DriverID": "eebus.primary",
  "ExpectedRevision": "7"
}
```

`DriverID` is the canonical registered driver ID. `ExpectedRevision` is a
canonical decimal string of a nonzero unsigned 64-bit value that echoes the
snapshot's `desired_revision`, never the view `revision`. The request
members, their validation, the refusal order and the revision rules are
governed by [`runtime-driver-lifecycle.md`](../architecture/runtime-driver-lifecycle.md),
which supersedes the former `idempotency_key` and `request_id` request members:
neither is accepted, and a request carrying either is refused as
`INVALID_ARGUMENT` like any additional member.

Accepted and same-desired no-op results contain only this closed result inside
the ordinary deterministic MCP envelope:

```json
{
  "desired_state": "RUNNING",
  "desired_revision": "8"
}
```

`desired_revision` is the durable desired revision, with the same encoding as
the snapshot field. No operation ID, request ID, disposition, completion field or
receipt is returned. Superseded: the former `DriverOperationV1` response
(operation and request IDs, kind, disposition, completion, outcome and embedded
snapshot) no longer exists for lifecycle mutations, together with its
concurrency and idempotency rules. Refusals
use the lifecycle contract's ordered codes; REVISION_CONFLICT includes the
current cached view.

### Concurrency And Readback

Expected-revision comparison precedes the same-desired no-op test. START while
desired RUNNING and STOP while desired STOPPED are no-ops without counter, retry
budget or observation changes. RESTART requires desired RUNNING; otherwise it
returns FAILED_PRECONDITION before transition-capacity checks, even in STOPPING.
Changing work uses one current typed slot and at most one reserved successor,
with TRANSITION_BUSY when the decision path is busy (the typed slot is full or the
namespace-wide serialization point was held beyond the bounded wait; it never
reports a revision-comparison outcome). The deadline is rechecked after the
serialization point is acquired, before the comparison and the no-op test. A changing START from stable
STOPPED persists typed START in the current slot; a START during STOPPING takes
the reserved slot as a typed replacement.

A lost response is resolved through list/get readback. An old-revision retry
conflicts, and a fresh-revision RESTART after settlement is another restart.
There is no idempotency-key lookup or completed-operation record.

### Unproven-close Safety Quarantine

Stop teardown has two separately bounded phases. The first drains work admitted
before withdrawal. The second phase is permitted only when the first phase
reaches zero active callbacks; it sends `CloseRequest` and waits for
adapter-owned closure proof. An active-callback drain expiry bypasses the
second phase entirely: the runtime emits no `CloseRequest`, must not close
beneath `RawTransport`, and immediately enters `CLOSE_UNCONFIRMED` safety
quarantine.

`STOP_TIMEOUT` is possible only when drain expiry leaves zero active callbacks.
On that path, adapter-proven closure during the second phase may converge to
`STOPPED` with `STOP_TIMEOUT`, `"safety_quarantined": false`, and empty
effective capabilities. If closure cannot be proven, the snapshot instead
contains:

```json
{
  "observed_state": "FAILED",
  "reason": {"code": "CLOSE_UNCONFIRMED", "retryable": false},
  "effective_capabilities": [],
  "safety_quarantined": true
}
```

The complete snapshot retains every other required `DriverSnapshotV1` field;
the fragment shows the quarantine-specific values. While quarantined, observed
state is `FAILED` and effective capabilities are empty. A manual start and
restart cannot clear it: START while desired RUNNING is a no-op, and a START
or RESTART that would change desired state or require admission is refused
with `FAILED_PRECONDITION` at the lifecycle refusal-table quarantine row.
Automatic retry, provider construction, capability admission, and generation
advance are blocked until process restart. No API operation, configuration reload, callback, or elapsed
time clears the flag in the current process epoch.

An ordinary recoverable `FAILED` snapshot has `safety_quarantined=false`.
Recovering it is the reconciler's job under normal configuration and
retry-budget rules; START with the current revision and desired RUNNING is a
no-op and is not a recovery path. With desired STOPPED, a START is an ordinary
changing decision. Consumers must use the flag and categorical reason; they
must not treat every `FAILED` state as a safety quarantine.

An actively executing admitted lease callback is active transport use. Its
immediate `CLOSE_UNCONFIRMED` safety quarantine blocks replacement, so the
runtime cannot construct or admit another transport generation underneath the
callback. An abandoned non-invoking lease is not active transport use; its
zero-callback drain expiry can take the second-phase proof path and yield a
proven `STOP_TIMEOUT` outcome; that outcome is restartable.

The initial response is admission-bounded. Consumers observe progress through
`drivers.v1.list`, using desired state/revision and observed state; readback
does not attribute completion to a particular call. Cancellation of the caller's
request does not detach an unowned operation: the manager either rejects before admission or owns the admitted
operation to a terminal categorical result.

### Stable Unavailable Providers

All four tools remain registered even if a driver provider cannot be built or
started. `list` returns its stable catalog snapshot. A mutation against that
entry follows the ordinary decision rules: an accepted decision returns only
desired state and desired revision, and the snapshot reports the categorical
reason `PROVIDER_UNAVAILABLE`. It never returns a raw construction or transport error.

## Audit Contract

The D3 lifecycle amendment supersedes the former request ID, operation ID and
receipt-based audit requirements. Diagnostics use only the bounded sanitized
in-memory ring defined there; they never provide deduplication or admission
authority. A diagnostic never contains an endpoint, credential, raw error, or
protocol payload. Diagnostic publication cannot roll back durable intent.

## Error And Security Boundary

Input errors use the closed result envelope and never invoke a provider.
Per final D4 the lifecycle tools carry no principal and no authorization
check; this contract does not create a credential or make MCP publicly
reachable. Portal and Home Assistant use their
normal authenticated gateway boundaries after their rollout gates.

Provider-owned details remain in bounded local diagnostics. Public errors,
snapshots, operations, audits, logs, GraphQL, Portal, and Home Assistant are
categorical and secret-free. The API accepts no endpoint or protocol payload,
and the manager never exposes transport handles.
