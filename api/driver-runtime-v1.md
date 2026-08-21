# Driver Runtime API V1

## Status And Authority

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
unavailable providers return typed snapshots or a stable `UNAVAILABLE`
operation result; tool disappearance and protocol-specific ad-hoc errors are
forbidden.

## Closed Driver Catalog

V1 recognizes exactly these IDs:

- `ebus.primary`
- `modbus.tcp.default`
- `eebus.primary`

The desired-state vocabulary is exactly `RUNNING`, `STOPPED`. The
observed-state vocabulary is exactly `DISABLED`, `STOPPED`, `STARTING`,
`RUNNING`, `DEGRADED`, `BACKOFF`, `STOPPING`, `FAILED`.

Unknown IDs are rejected with `DRIVER_NOT_FOUND`. IDs are ASCII lowercase
catalog tokens, not paths or caller-defined values. V1 never accepts an
endpoint, address, certificate identifier, device identity, or transport name
in place of a catalog ID.

## `DriverSnapshotV1`

Every list item and mutation response uses the following closed shape:

The lifecycle evidence fields are `reason`, `retry`, `generation`, `revision`,
`attempt`, and `capabilities`.

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
  "revision": 29,
  "attempt": 2,
  "capabilities": ["DISCOVERY", "READ", "PAIRING", "TOPOLOGY"],
  "active_operation_id": null,
  "last_operation": {
    "operation_id": "drvop_01",
    "kind": "RESTART",
    "outcome": "RETRY_SCHEDULED"
  },
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
- `revision` starts at one after catalog construction and monotonically
  increases across the process epoch. The revision changes on every externally
  visible snapshot mutation and never changes for a byte-identical replay.
- attempt is scoped to one generation. It counts admission/recovery attempts
  beginning at one and resets only when a new generation is admitted. Zero is
  used before the first attempt.
- reason is a closed categorical value. It never carries an endpoint,
  credential, raw transport error, or protocol payload.
- `retry` is null unless an automatic retry decision exists. When present,
  `eligible`, `budget_remaining`, and `not_before_utc` are mutually coherent;
  a non-eligible retry has no deadline.
- capabilities are immutable for one generation, sorted, and derived from the
  admitted provider. A capability change requires a new generation.
- `active_operation_id` is non-null only while one operation owns the driver.
- `last_operation` is null before the first terminal operation. It retains
  only categorical correlation for the current process epoch.
- Provider callbacks carry the generation and active operation ID captured at
  admission. A callback with stale correlation cannot mutate the snapshot.
- timestamps are UTC RFC3339 values and are evidence, never ordering
  authority. Revision is the ordering authority.

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
| `STOP_TIMEOUT` | Bounded drain expired and forced local teardown ran. |
| `INTERNAL_ERROR` | A secret-free manager/provider invariant failed. |

`retryable` is true only for `DEPENDENCY_UNAVAILABLE`, `RUNTIME_NOT_READY`, or
`RETRY_SCHEDULED` while policy budget remains. Consumers do not infer retry
eligibility from the string alone; they use the explicit boolean and `retry`.

### Closed Capability Codes

V1 capability tokens are `DISCOVERY`, `READ`, `WRITE`, `PAIRING`, `TOPOLOGY`,
`RAW_EVIDENCE`, and `SEMANTIC_PROJECTION`. Capability presence describes what
the admitted generation can support; authorization and observed readiness are
separate. In particular, `WRITE` never grants a consumer permission to issue a
protocol write.

## `drivers.v1.list`

`drivers.v1.list` accepts no arguments and returns all three snapshots ordered
by driver ID. It is available whenever the gateway process is ready, including
when every protocol provider failed. The list is one coherent manager revision;
it is not assembled by independently querying transports.

Example result envelope:

```json
{
  "schema_version": 1,
  "manager_revision": 29,
  "drivers": []
}
```

The real V1 result contains exactly three driver entries. The empty array above
illustrates envelope shape only and is not a valid V1 catalog result.

## Mutating Tools

`drivers.v1.start`, `drivers.v1.stop`, and `drivers.v1.restart` accept this
closed request:

```json
{
  "driver_id": "eebus.primary",
  "idempotency_key": "client-generated-opaque-key",
  "request_id": "optional-client-correlation"
}
```

`driver_id` and `idempotency_key` are required. `request_id` is optional and
has no idempotency or authorization meaning. The idempotency key is an opaque
ASCII token of 16 through 128 characters, retained only for the current
process epoch. It must not encode a secret, endpoint, or device identity.

Every tool returns a closed `DriverOperationV1` envelope:

```json
{
  "schema_version": 1,
  "operation_id": "drvop_01",
  "request_id": "optional-client-correlation",
  "driver_id": "eebus.primary",
  "kind": "START",
  "disposition": "ACCEPTED",
  "completed": false,
  "outcome": null,
  "snapshot": {}
}
```

The closed dispositions are `ACCEPTED`, `REPLAYED`, `NOOP`, `CONFLICT`, and
`UNAVAILABLE`. Terminal outcomes are `SUCCEEDED`, `ALREADY_IN_STATE`,
`RETRY_SCHEDULED`, `STOP_TIMEOUT`, `DRIVER_NOT_FOUND`, `DRIVER_BUSY`,
`PROVIDER_UNAVAILABLE`, `INVALID_REQUEST`, and `INTERNAL_ERROR`.

The placeholder snapshot above represents the required `DriverSnapshotV1`
object. An implementation never returns an open or empty snapshot object.

### Concurrency And Idempotency

Exactly one operation is active per driver. Independent drivers may execute in
parallel. A second different operation on a busy driver returns `CONFLICT` /
`DRIVER_BUSY` and is not queued.

The manager binds each idempotency key to the normalized driver ID and kind.
The same idempotency key with the same intent returns the same operation result
and operation ID without a second lifecycle effect. The same key with a
different intent returns `CONFLICT` / `INVALID_REQUEST`. Keys and cached
results expire only with the process epoch.

Start on an already running driver and stop on an already stopped/disabled
driver return `NOOP` / `ALREADY_IN_STATE`; they do not advance generation.
Restart is never reduced to that no-op and creates one new generation when it
succeeds.

The initial response is admission-bounded. Consumers observe progress through
`drivers.v1.list`, correlating `active_operation_id`, `last_operation`, and
revision. Cancellation of the caller's request does not detach an unowned
operation: the manager either rejects before admission or owns the admitted
operation to a terminal categorical result.

### Stable Unavailable Providers

All four tools remain registered even if a driver provider cannot be built or
started. `list` returns its stable catalog snapshot. A mutation against that
entry returns `UNAVAILABLE` / `PROVIDER_UNAVAILABLE`, with the same driver ID
and a current snapshot. It never returns a raw construction or transport error.

## Audit Contract

Exactly one audit record is emitted for every mutation admission or rejection and one
terminal record is emitted for an admitted asynchronous operation. Each record
contains schema version, request ID, operation ID, driver ID, kind,
disposition/outcome, before and after revision, and UTC timestamps. It never
contains an endpoint, credential, raw error, or protocol payload.

Audit publication failure cannot roll back a completed lifecycle transition,
but it makes the operation outcome `INTERNAL_ERROR` and raises a process-level
operator alert. The audit sink is bounded and must not block provider teardown.

## Error And Security Boundary

Input errors use the closed result envelope and never invoke a provider.
Authorization belongs to the host surface; this contract does not create a
credential or make MCP publicly reachable. Portal and Home Assistant use their
normal authenticated gateway boundaries after their rollout gates.

Provider-owned details remain in bounded local diagnostics. Public errors,
snapshots, operations, audits, logs, GraphQL, Portal, and Home Assistant are
categorical and secret-free. The API accepts no endpoint or protocol payload,
and the manager never exposes transport handles.
