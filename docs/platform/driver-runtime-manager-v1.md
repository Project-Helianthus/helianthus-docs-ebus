# Driver Runtime Manager V1

## Status And Scope

This page freezes the target protocol-neutral lifecycle architecture for the
first Helianthus `DriverManager`. It is a pre-implementation contract, not a
claim that every API or consumer described here is present in a released
gateway. The public MCP shape is owned by
[`../../api/driver-runtime-v1.md`](../../api/driver-runtime-v1.md).

V1 manages exactly these stable driver instances:

| Driver ID | Protocol family | Initial provider |
| --- | --- | --- |
| `ebus.primary` | eBUS | primary eBUS adapter runtime |
| `modbus.tcp.default` | Modbus TCP | default Modbus TCP endpoint runtime |
| `eebus.primary` | eeBUS | primary SHIP/SPINE runtime |

The IDs identify configured runtime slots, not physical devices. Device
identity, transport endpoints, credentials, and protocol payloads never enter
an ID. Adding another instance or protocol requires a later versioned catalog;
V1 consumers must not invent IDs.

This contract owns process composition, lifecycle, readiness, operations, and
consumer rollout. It does not alter transport framing, protocol semantics,
registry projection, trust ownership, Modbus profile selection, or bus writes.

## Ownership Boundary

`DriverManager` is the sole lifecycle owner inside the gateway process. Each
driver provider owns only its protocol-local construction, connection,
readiness, retryable error classification, drain, and teardown operations. The
manager serializes lifecycle intent, retains the public snapshot, applies
retry policy, owns atomic effective-capability admission, and publishes
categorical audit evidence.

The add-on owns option ingestion and validation. It passes one independently
classified descriptor per driver to the gateway. The add-on does not run three
gateway processes, supervise protocol children, retry a complete gateway, or
interpret driver health. The gateway process owns all providers after launch.

Portal, GraphQL, Home Assistant, and MCP are consumers of the manager. They do
not call transports directly, hold adapter sockets, edit the add-on options
document, or maintain an independent lifecycle FSM.

## Process Readiness Is Not Driver Readiness

Process readiness is not driver readiness. The process is ready after its
mandatory control plane is serving, the driver catalog exists, configuration
classification has completed, and `drivers.v1.list` can return a coherent
snapshot. At least one failed driver does not make process readiness fail.

A protocol-local startup failure never terminates the shared gateway. HTTP,
MCP, GraphQL, and the operator surface remain available, unaffected drivers
continue running, and the failed provider remains represented by a stable
unavailable provider and a categorical `FAILED` or `BACKOFF` snapshot. The
manager must not convert a missing dependency, disconnected bus,
protocol-local admission failure, or exhausted driver retry into process exit.

The global-fatal boundary is deliberately small. A gateway process may fail to
start only when it cannot establish the common control plane or trustworthy
process identity, including:

- an unreadable or syntactically invalid global configuration document for
  which driver fields cannot be isolated;
- invalid global process inputs outside every driver namespace;
- missing or corrupt packaged binary integrity, or an invalid injected build
  identity;
- failure to bind a mandatory process-level HTTP/MCP control endpoint; or
- inability to construct the manager/catalog itself.

All endpoint, adapter, protocol, credential, and driver readiness failures are
driver-local. They are never promoted into that global-fatal boundary.

## Startup And State Transitions

At process startup the manager creates all three catalog entries before it
starts any provider. Each descriptor is then evaluated independently:

- a valid configured-disabled descriptor enters `DISABLED`;
- a valid configured-enabled descriptor enters `STARTING`;
- a driver-local invalid descriptor enters `FAILED` with `CONFIG_INVALID` and
  does not block the other entries;
- a missing or unavailable provider enters `FAILED` with
  `PROVIDER_UNAVAILABLE`, while the provider surface remains stable.

The core transitions are:

```text
DISABLED  --start-->    STARTING
STOPPED   --start-->    STARTING
STARTING  --ready-->    RUNNING
STARTING  --usable-->   DEGRADED
STARTING  --retry-->    BACKOFF
STARTING  --terminal--> FAILED
BACKOFF   --due-->      STARTING
RUNNING   --loss-->     DEGRADED | BACKOFF | FAILED
DEGRADED  --recover-->  RUNNING
DEGRADED  --retry-->    BACKOFF
RUNNING   --stop-->     STOPPING
DEGRADED  --stop-->     STOPPING
BACKOFF   --stop-->     STOPPING
STARTING  --stop-->     STOPPING
FAILED    --stop-->     STOPPING
STOPPING  --drained-->  STOPPED
```

The normative textual forms include `STARTING -> RUNNING`,
`STARTING -> BACKOFF`, `BACKOFF -> STARTING`, and `STOPPING -> STOPPED`.
`DEGRADED` means the provider is admitted and offers a documented subset of
its capabilities; it is not a synonym for disconnected or failed. A provider
that cannot safely serve its advertised capability uses `BACKOFF` or `FAILED`.
Static generation capabilities describe the provider contract. Effective
capabilities describe the subset currently admitted for invocation and are
empty outside `RUNNING` and `DEGRADED`.

## Retry And Recovery

Each provider classifies failures as retryable or terminal without exporting a
raw error. The manager applies bounded exponential backoff with jitter from a
closed per-driver retry policy. A finite retry budget, minimum delay, maximum
delay, and next-attempt deadline are visible categorically through the
snapshot. A successful admission advances generation and resets its retry
counter. A failed construction that never admits a provider cannot advance
generation. A terminal failure or exhausted retry budget enters `FAILED`.

`BACKOFF` has no hidden work other than its scheduled attempt. Stop cancels the
timer before teardown. Start from `FAILED` creates a fresh retry budget and, on
successful provider admission, a new generation; it never reuses a half-closed
transport instance. An automatic retry and an operator operation linearize
under the same per-driver operation lock, so neither can resurrect a stopped
driver. Every asynchronous callback carries its captured generation and
operation ID. The manager discards a callback whose generation or operation is
no longer current.

## Stop, Drain, And Restart

Stop first commits desired `STOPPED`, cancels admission and retry work, and
enters `STOPPING`. The provider receives one drain deadline. It must stop new
protocol work, cancel or finish bounded in-flight work, close listeners and
connections, and join owned goroutines. If the drain deadline expires, the
manager performs forced local teardown and publishes `STOP_TIMEOUT`. It enters
`STOPPED` only after teardown completion is confirmed. If the old instance
cannot be proven closed, the driver enters `FAILED`, the generation is
quarantined, and a new start is rejected until process restart; timeout is not
permission to terminate the gateway or another driver or to run two instances.

Stop and restart perform atomic effective-capability withdrawal under the same
lock used by every provider invocation. The manager empties the effective set
before it publishes `STOPPING`; work racing after that point is blocked before
provider invocation, while work admitted earlier belongs to the bounded drain.
Provider callbacks with stale generation or operation correlation cannot
restore an effective capability.

An unproven-close safety quarantine is represented by observed `FAILED`, reason
`CLOSE_UNCONFIRMED`, an empty effective set, the `safety_quarantined` flag, and
operation outcome `SAFETY_QUARANTINED`. It blocks manual start/restart,
automatic retry, provider construction, and generation advance for the rest of
the process epoch. It cannot be cleared by an API operation, configuration
reload, timer, or late callback. Only process restart creates a manager without
that in-memory quarantine.

This is distinct from ordinary recoverable `FAILED`, which does not set
`safety_quarantined` and may admit a later manual start. A drain timeout whose
forced teardown proves closure may reach `STOPPED` with `STOP_TIMEOUT`; it does
not falsely enter quarantine.

restart is one serialized stop-then-start operation. It is not two consumer
requests and cannot be interleaved with another lifecycle command. A successful
restart creates exactly one new generation. If stop cannot complete safely,
the restart ends with a categorical failure and does not start a second
provider instance.

## Configuration And Runtime Overrides

Persistent add-on configuration supplies the process-start baseline. A runtime
start or stop changes the manager's desired state through a
process-epoch-local override. The override does not rewrite add-on options,
does not persist credentials or endpoints, and does not survive a gateway
process restart. On the next process epoch, desired state is derived again
from the admitted add-on configuration.

Consequently, an operator can temporarily start a configured-disabled driver
or stop a configured-enabled driver without silently changing Supervisor
configuration. Persistent changes remain an explicit add-on configuration
operation outside DriverManager V1.

## Add-on Validation Boundary

The add-on validates each enabled driver's own configuration independently.
An invalid driver-local configuration disables only that driver descriptor and
passes a secret-free categorical failure to the manager; it must not prevent
the gateway process from starting. Disabled drivers do not validate retained
endpoint or credential text, preserving a safe recovery path.

Only global process inputs, packaged binary integrity, an unreadable global
configuration document, and other conditions enumerated in the global-fatal
boundary may stop the add-on before gateway launch. Secret material remains in
the existing owner-specific protected-file boundary and never enters a
snapshot, audit record, command response, or log.

## Operation And Audit Model

Mutating requests are asynchronous, bounded at admission, and serialized per
driver. Drivers may progress in parallel with each other. Exactly one operation
is active per driver; commands are not silently queued. Idempotency binds the
caller-supplied key to the normalized driver ID and intent for the process
epoch. Replaying the same binding returns the same operation result without a
second lifecycle effect. Reusing the key for different intent returns
`CONFLICT`.

Every admitted, replayed, rejected, completed, or failed command emits one
categorical audit record with request ID, operation ID, driver ID, kind,
disposition, before and after revision, and timestamps. Audit data never
contains an endpoint, credential, raw transport error, protocol payload,
certificate identity, or device identity.

## Delivery Order

The implementation follows the platform delivery pipeline:

1. **MCP prototype**: implement and stabilize `drivers.v1.list`,
   `drivers.v1.start`, `drivers.v1.stop`, and `drivers.v1.restart`.
2. **GraphQL parity**: freeze the equivalent snapshot and mutations without
   replacing MCP ownership.
3. **Portal rollout**: render driver cards and lifecycle controls from the
   gateway APIs; Portal remains a consumer.
4. **Home Assistant rollout**: expose native entities/actions after GraphQL is
   stable; Home Assistant remains a consumer.

No consumer may shape protocol-specific exceptions into this V1 contract.
Protocol-specific status remains reachable through its existing diagnostics
surface and correlates by the stable driver ID.

## One-release Acceptance

Repository work may proceed in parallel only through disjoint file ownership
and normal dependency order. Public runtime acceptance is bundled into one
consolidated add-on release, one multi-architecture build, and one CI/CD
publication. Intermediate dependency merges are not separate live releases.

The release gate must demonstrate, from the exact packaged gateway/add-on
pair:

- all three driver IDs are always listed with the closed V1 shape;
- all configured healthy drivers reach `RUNNING` without duplicate instances;
- startup failure injection for each driver is protocol-local while the
  process remains ready and the other drivers remain operable;
- stop, start, and restart work for each driver without gateway restart;
- restart increments generation exactly once and command replay has no second
  effect;
- retry budget, drain timeout, stable unavailable-provider, and stale callback
  races behave as specified;
- a deterministic stop/restart withdrawal race proves that post-withdrawal
  work is blocked before provider invocation and no stale callback restores
  admission;
- an unproven-close fixture enters process-epoch quarantine, invokes no new
  constructor through start, restart, or retry, and remains distinct from
  ordinary recoverable failure;
- a process restart discards runtime overrides and restores configuration
  intent;
- MCP, GraphQL, Portal, and Home Assistant expose parity at their respective
  rollout gates; and
- logs, snapshots, responses, and audits remain secret-free and
  endpoint-free.

Real-device absence or a physically disconnected bus may produce an expected
driver-local unavailable/degraded result. It does not waive API, isolation,
redaction, concurrency, or rollback evidence.
