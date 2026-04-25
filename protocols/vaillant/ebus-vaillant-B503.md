# Vaillant B503 — Diagnostic, Service, and HMU Live-Monitor (normative)

`PB=0xB5`, `SB=0x03`.

This document is the **normative L7 protocol specification** for the Vaillant
`B503` selector family within the Helianthus `vaillant/b503` namespace. It is
the `M0_DOC_GATE` deliverable for execution-plans#19 (plan
`vaillant-b503-namespace-w17-26`, canonical SHA `86495340`). Downstream code
milestones `M1_DECODER` (helianthus-ebusgo), `M2a_GATEWAY_MCP` /
`M2b_GATEWAY_GRAPHQL` / `M5_TRANSPORT_MATRIX` (helianthus-ebusgateway), `M3`
portal and `M4` Home Assistant MUST cite this document as their doc-gate
companion.

Amendment-1 (2026-04-25) extends the v1 surface with the `M0b_DOC_DISPATCHER_BRIDGE`
deliverable (this doc, §12) and the production-dispatch milestone
`M6_DISPATCHER_BRIDGE` (helianthus-ebusgateway). The amendment adds the
production dispatcher contract, the AD18 capability-signal 8-state truth
table, and the AD16 lock-order + epoch-tagged in-flight discipline. All
amendment-1 content is rendered in §12 and cross-referenced from §13 and §14.

## 1. Status

**Normative.** Formerly reverse-engineered selector family. The seven selectors
listed in §3 are locked per plan AD01..AD15 as the v1 delivery surface. The
wire shape is stable; decoder structure, invoke-safety classification, session
model, error model, and public-surface normalization rules are frozen for v1.

Amendment-1 (2026-04-25) keeps the v1 wire/safety surface unchanged and
extends the document with the production dispatcher contract in §12
(plan AD16 + AD18). The amendment is additive: no v1 selector, FSM, or
public enum is altered.

Changes to this document require a new plan revision and a corresponding
doc-gate PR before any downstream code change may land.

Evidence labels used throughout:

- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local bus captures.
- `LOCAL_MCP`: Helianthus MCP runtime observations.
- `PUBLIC_CONFIG`: upstream john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the sources above.

## 2. Wire Shape

`B503` requests **always begin with a two-byte `(family, selector)` prefix**.
The prefix identifies the §3 catalog row; per-selector request lengths MAY
extend beyond 2 bytes (see "History reads" below for the documented
extension case). The request payload is opaque to `protocol.Frame`;
framing, CRC, escaping, and bus-transaction behaviour are unchanged. No new
transport semantics are introduced by this namespace.

```text
Request payload (normative baseline — all selectors start with these 2 bytes):
  family   : byte     # 0x00 current | 0x01 history-lookup | 0x02 clear-command
  selector : byte     # 0x01 error   | 0x02 service        | 0x03 HMU live-monitor
```

The `family` byte classifies the request CLASS; its value is not itself a
history index. `selector` classifies the data plane (error / service / HMU
live-monitor). The two bytes together identify the row in §3.

**The `family` byte is NOT safety-bearing.** Invoke-safety classification
(`READ` / `SERVICE_WRITE` / `INSTALL_WRITE`) is a property of the *complete*
`(family, selector)` tuple as enumerated in §3 / §4, NOT of the family byte
alone. In particular, `family=0x00` includes both `READ` selectors
(`00 01`, `00 02`) and the `SERVICE_WRITE` live-monitor selector
(`00 03`). Implementations MUST derive invoke safety from the §3 catalog
lookup (or equivalent decoder-table entry), never from the family byte in
isolation. A gateway that treats `family=0x00` as passive-by-default would
bypass the session gating required in §6–§7 for `00 03`.

**History reads** (`family = 0x01`, selectors `Errorhistory` / `Servicehistory`)
are indexable. Per `LOCAL_TYPESPEC`, the response carries an echoed `index`
field; the mechanism by which the client SELECTS which history entry to
retrieve is **device-class dependent** and MAY append additional bytes after
the two-byte baseline. Implementers MUST consult the per-target decoder in
`helianthus-ebusgo/protocol/vaillant/b503` and the LOCAL_TYPESPEC / LOCAL_CAPTURE
evidence for the target device class, and MUST run the falsification test in
§3 against multiple history indexes on real hardware before locking the
request encoding for a given target.

Response shape is selector-dependent; see §3 and the `helianthus-ebusgo`
per-selector struct definitions under `protocol/vaillant/b503`.

## 3. Selector Catalog (NORMATIVE)

The table below is the full v1 selector set. The `Invoke-Safety` column is the
authoritative classification applied at the gateway invoke boundary (§7).
`Install-write` selectors (`02 01`, `02 02`) are classified `INSTALL_WRITE` and
MUST NOT be reachable through any public surface in v1 (§9).

| Request payload | Direction | Name | Invoke-Safety | Response shape | Evidence | Falsification test |
|---|---:|---|---|---|---|---|
| `00 01` | read | `Currenterror` | `READ` | five LE `uint16` error slots (`errors`), `0xFFFF` = empty | `LOCAL_TYPESPEC`, `LOCAL_CAPTURE` | Read `B503 00 01` from BAI00 and disprove that response bytes decode as five little-endian unsigned 16-bit slots with `0xFFFF` sentinel. |
| `01 01` | read | `Errorhistory` | `READ` | index + `errorhistory` payload | `LOCAL_TYPESPEC` | Query multiple history indexes and show response does not change with the index byte or does not carry an error-history record. |
| `02 01` | install write | `Clearerrorhistory` | `INSTALL_WRITE` — **NOT exposed v1** | ACK / side effect | `LOCAL_TYPESPEC` | On isolated hardware, write the clear command and show error history remains unchanged after successful ACK. |
| `00 02` | read | `Currentservice` | `READ` | five LE `uint16` service slots (`errors` shape) | `LOCAL_TYPESPEC` | Read `B503 00 02` from a target with a service message and show no five-slot response exists. |
| `01 02` | read | `Servicehistory` | `READ` | index + `errorhistory`-shaped payload | `LOCAL_TYPESPEC` | Query indexes and show no indexed service-history payload. |
| `02 02` | install write | `Clearservicehistory` | `INSTALL_WRITE` — **NOT exposed v1** | ACK / side effect | `LOCAL_TYPESPEC` | Clear on isolated hardware and verify history is unchanged after ACK. |
| `00 03` | service write/read pair | HMU `LiveMonitorMain` enable + status | `SERVICE_WRITE` | response begins with `status`, `function`; trailing bytes reserved | `LOCAL_TYPESPEC`, `LOCAL_CAPTURE` | Enable live monitor, then read `B503 00 03`; falsify if first two data bytes do not track live-monitor status/function changes. |

## 4. Invoke-Safety Classes

Three classes are defined (plan AD04). The decoder package in
`helianthus-ebusgo/protocol/vaillant/b503` exports this as an enum and the
gateway MUST consult it at the invoke boundary before dispatching a frame.

| Class | Semantics | Gateway behaviour |
|---|---|---|
| `READ` | Passive-safe, idempotent. No session state. | May be invoked directly via `ebus.v1.rpc.invoke` substrate. |
| `SERVICE_WRITE` | Side-effectful, stateful. Gated by live-monitor session (§6). | MUST acquire `liveMonitorMu` and respect the FSM in §6. |
| `INSTALL_WRITE` | Side-effectful, requires installer authority. | MUST NOT be exposed on any public surface in v1. Negative tests in M2a / M2b / M3 assert absence on MCP, GraphQL, and portal respectively. |

Install-write classification for `02 01` (`Clearerrorhistory`) and `02 02`
(`Clearservicehistory`) is **mandatory** and non-overridable in v1. See §9.

## 5. Sentinel Rules and `first_active_error`

### 5.1 Sentinel

In the five-slot composite payloads returned by `00 01` (`Currenterror`) and
`00 02` (`Currentservice`), each slot is a little-endian `uint16`. The value
`0xFFFF` denotes an **empty slot** (no error / no service message occupying
that position). Sentinel detection is per-slot; a `0xFFFF` in slot N does not
truncate scanning of slot N+1.

### 5.2 `first_active_error`

`first_active_error` is defined normatively as:

> The first slot, scanning from slot 0 upward (ascending index), whose decoded
> LE `uint16` value is **not** `0xFFFF`. If all five slots are `0xFFFF`,
> `first_active_error` is absent.

Home Assistant entity `boiler_active_error` (plan M4) publishes this value
directly as a decimal integer when `first_active_error` is present. When
`first_active_error` is absent (all five slots `0xFFFF` — i.e. the device
reports no active fault), the entity state is `None` (rendered as HA
`unknown`), signalling a healthy "no-active-error" state.

**This is distinct from `unavailable`.** `unavailable` is reserved for
capability / transport outages per §11 (`TRANSPORT_DOWN`, `UNKNOWN`,
`NOT_SUPPORTED`). A read that successfully returns five `0xFFFF` slots is a
positive health signal, NOT an outage: the entity MUST NOT be rendered
`unavailable` in that case. Conflating the two states would cause
downstream automations to treat normal operation as device unavailability.

### 5.3 Worked example (LOCAL_CAPTURE)

Captured from BAI00 (`0x08`) during plan R1 evidence gathering:

```text
REQ:  f1 08 b5 03 02 00 01
RESP: 0a 19 01 ff ff ff ff ff ff ff ff
```

Decode:

- Response length byte `0x0a` = 10 payload bytes.
- Slot 0: `19 01` → LE `0x0119` → decimal `281`.
- Slots 1..4: `ff ff` → `0xFFFF` → empty.

`first_active_error` = `281`. See §10 for the F.xxx correlation caveat
governing how this decimal is surfaced to consumers.

## 6. Live-Monitor Session

### 6.1 State machine (plan AD04)

The gateway runs a single-owner FSM per transport incarnation for selector
`00 03` (HMU `LiveMonitorMain`). `EXPIRED` is an **internal** sub-state
emitted only after the transport epoch advances under an in-flight owner
handle; it MUST NOT appear on any public surface (§7.1.1, §8, §11).

```mermaid
stateDiagram-v2
    [*] --> IDLE
    IDLE --> ENABLING: enable request (MCP)
    ENABLING --> ACTIVE: enable ACK on bus
    ACTIVE --> ACTIVE: periodic read during session
    ACTIVE --> DISABLED: explicit disable
    ACTIVE --> DISABLED: 30s idle timer
    DISABLED --> IDLE: owner cleanup complete

    ACTIVE --> EXPIRED: reconnect / epoch mismatch
    EXPIRED --> ACTIVE: resolver refresh + retry (success)
    EXPIRED --> DISABLED: refresh reveals TRANSPORT_DOWN
    EXPIRED --> DISABLED: refresh reveals UNKNOWN

    note right of EXPIRED
      Internal-only. Never surfaced publicly.
      Retry budget: exactly 1 per request.
    end note
```

### 6.2 Ownership key

B503 live-monitor ownership has two composition layers:

```text
transport_key = (adapter_instance_id, transport_incarnation_epoch)
session_key   = (transport_key, issuer_token)
```

- `transport_key` is the bus-level identity: at most one live-monitor
  session may be ACTIVE per `transport_key` (physical bus constraint —
  HMU cannot multiplex simultaneous live-monitor streams).
- `issuer_token` is an **opaque, gateway-issued token** returned to the
  client on successful ENABLE. It scopes session control authority (disable,
  idle-extend) to the specific caller that claimed the session.

Rules (normative):

| Operation | Required key match | Outcome on mismatch |
|---|---|---|
| ENABLE | none (new claim) | succeeds iff FSM is `IDLE`; if any session already `ENABLING`/`ACTIVE`/`EXPIRED` under a different `issuer_token` → `SESSION_BUSY` |
| DISABLE | full `session_key` must match the active session | `SESSION_BUSY` (caller does not own the session) — prevents session hijacking between clients on the same transport |
| READ (`00 03`) | `transport_key` match; `issuer_token` ignored | Reads are permitted to any caller while a session is `ACTIVE` — physically there is only one data stream on the bus; denying reads to non-owning clients would serve no safety purpose |
| Epoch advance under any handle | — | handle → `EXPIRED` (internal); resolver refresh per §7.3 |

The `issuer_token` is opaque to clients; it MUST NOT be derived from
user-visible identifiers, and MUST be sufficient entropy that a second
client cannot forge another client's token (e.g., gateway-internal UUID or
cryptographic nonce). Clients obtain their token from the ENABLE response
envelope and return it in subsequent DISABLE calls.

This refines plan AD04's baseline `(adapter_instance_id,
transport_incarnation_epoch)` with a client-scoped control token. The
refinement is additive: the plan-level transport identity is preserved, and
the token layer only affects session control (enable/disable), not bus
access.

### 6.3 Transitions (normative)

| From | Event | To | Side effect |
|---|---|---|---|
| `IDLE` | enable request, no owner | `ENABLING` | emit enable frame after poll-quiesce |
| `ENABLING` | enable ACK received | `ACTIVE` | start 30s idle timer; arm reads |
| `ENABLING` | ACK timeout / NAK | `DISABLED` | (see release rule below) |
| `ACTIVE` | read request | `ACTIVE` | reset idle timer |
| `ACTIVE` | explicit disable | `DISABLED` | emit disable frame after quiesce |
| `ACTIVE` | 30s idle | `DISABLED` | emit disable frame after quiesce |
| `ACTIVE` | epoch advance detected | `EXPIRED` | internal; trigger refresh-once |
| `EXPIRED` | refresh succeeds | `ACTIVE` | resume; retry budget consumed |
| `EXPIRED` | refresh → `TRANSPORT_DOWN` | `DISABLED` | surface `TRANSPORT_DOWN` (NOT `SESSION_BUSY`) |
| `EXPIRED` | refresh → `UNKNOWN` | `DISABLED` | surface `UNKNOWN` (NOT `SESSION_BUSY`) |
| `DISABLED` | owner cleanup complete | `IDLE` | session may be re-claimed by any client |
| any | transport disconnect | `DISABLED` | owner cleanup |
| any | gateway restart | `DISABLED` | owner cleanup; session state is NOT recoverable across restart (no EXPIRED refresh path — restart destroys all handles) |

**Lock lifecycle (single assignment, owner-conditional):**
`liveMonitorMu` is acquired exactly once on the `IDLE → ENABLING`
transition. It is released exactly once **on entry to `DISABLED` from a
held-owner state** — i.e., when the source state is `ENABLING`, `ACTIVE`,
or `EXPIRED`. The "any" transitions (transport disconnect, gateway
restart) release the mutex only when FSM was in a held-owner state at the
time the event fired; if the FSM was already `IDLE` or `DISABLED` (no
owner), no release occurs. The `DISABLED → IDLE` transition does NOT
release the mutex; it only marks the session slot as re-claimable after
cleanup completes. Implementations MUST NOT release the mutex at any
other transition, and MUST NOT attempt a release when no owner is held.
This keeps the release single-sourced, owner-conditional, and free of
double-unlock panics on timeout/NAK paths or disconnect-while-idle events.

## 7. Gateway Operational Contract

This section is the primary doc-gate companion for `M2a_GATEWAY_MCP` and
`M5_TRANSPORT_MATRIX`. It is sourced directly from plan §11. All statements
are normative (MUST / MUST NOT / SHOULD).

### 7.1 Public error model

Exactly **two** public outcomes exist for `SERVICE_WRITE` and `READ`
operations that depend on capability state. Both are members of the
public `B503Availability` enum (§11) or map onto it:

| Public value | Meaning | When it surfaces |
|---|---|---|
| `BUSY` (`SESSION_BUSY`) | Live-monitor session already claimed under a different `issuer_token`, OR bounded lifecycle/contention ambiguity. | Another client holds the session (ENABLE/DISABLE mismatch per §6.2); genuine contention that is not transport loss. |
| `UNAVAILABLE` (`TRANSPORT_DOWN` / `UNKNOWN` / `NOT_SUPPORTED`) | Capability is not currently usable; distinguish reason per public enum (§11). | Transport disconnected; gateway has not yet determined availability; device class does not implement B503. |

#### 7.1.1 Internal-only state (NOT public)

`EXPIRED` is a gateway-internal FSM sub-state (§6.1) and MUST NOT appear
in any public MCP / GraphQL / portal / HA surface. It exists only inside
the gateway and is consumed by the resolver refresh-once policy (§7.3):

| Internal value | Where it lives | Public exposure |
|---|---|---|
| `EXPIRED` | gateway FSM only | **forbidden** — surfaces as `AVAILABLE` (after successful refresh), `BUSY`, or `UNAVAILABLE` per §8 normalization |

Downstream contract tests (M2a, M2b) MUST assert that no public response
ever carries `EXPIRED`; any such surface is a gateway bug.

### 7.2 Quiesce timing bounds (normative)

The gateway MUST apply a **poll-quiesce window** around the emission of every
live-monitor enable and disable frame. Bounds:

- **Lower bound: 0.** The quiesce window MAY be zero when no B524 poll frame is
  in flight.
- **Upper bound:** enforced by the transport layer — the gateway MUST NOT emit a
  B503 live-monitor enable or disable frame while a B524 poll frame is in
  flight on the same bus. Observed upper bound on adapter-direct and
  `ebusd_tcp` transports is one B524 transaction window (validated in
  `M5_TRANSPORT_MATRIX`, artefact `matrix/M6a-vaillant-b503.md`).

### 7.3 Retry and refresh

- Maximum **1 auto-retry per request** on `EXPIRED`. No recursive or unbounded
  retries.
- On refresh success → retry once; then surface the retry outcome.
- On refresh revealing `TRANSPORT_DOWN` or `UNKNOWN` → surface that value
  literally (§11). It MUST NOT be collapsed into `SESSION_BUSY`.
- No infinite reconnect loops. Reconnect is driven by the transport layer, not
  by B503 resolvers.

### 7.4 Ownership release

Release is owner-conditional (§6.3 "Lock lifecycle"). The release
obligations below apply **only when an owner is held at the moment the
event fires**; they are no-ops when the FSM is already `IDLE` or
`DISABLED`:

- On transport disconnect, the gateway MUST transition the FSM to
  `DISABLED` and — if an owner was held — release `liveMonitorMu`.
- On gateway restart, the gateway MUST transition the FSM to `DISABLED`
  and — if an owner was held — release `liveMonitorMu`. No state persists
  across restart.
- If the FSM was already `IDLE` or `DISABLED` at disconnect/restart time,
  these events are no-ops with respect to the mutex; no release is
  attempted.
- `liveMonitorMu` is a **distinct** `sync.Mutex` from the B524 `readMu`.
  Acquisition order when both are needed: `liveMonitorMu` → (optional)
  `readMu`. The reverse order is forbidden.

### 7.5 Reconnect handling

- On reconnect, the `transport_incarnation_epoch` advances. Any surviving owner
  handle from the prior incarnation is `EXPIRED` (internal) on next touch.
- The resolver applies the §7.3 refresh-once policy.
- The gateway MUST NOT auto-resume a live-monitor session across transport
  incarnations. A new enable from the client is required.

### 7.6 30s idle-timeout semantics

- In `ACTIVE`, if no read request arrives within 30 seconds, the gateway emits
  a disable frame (with quiesce) and transitions to `DISABLED`.
- The 30s timer resets on every successful read.
- Idle disable transitions the **internal** FSM from `ACTIVE` to `DISABLED`.
  The **public capability signal** (§11) remains `AVAILABLE` throughout: idle
  auto-disable is a session-lifecycle event, not a capability change. A client
  that issues a new live-monitor request simply re-enters `ENABLING`. Idle
  auto-disable MUST NOT be reported to consumers as `NOT_SUPPORTED`, which is
  reserved for "device class does not implement B503" (§11).

### 7.7 Concurrency with B524

- READ selectors (`00 01`, `01 01`, `00 02`, `01 02`) MAY proceed concurrently
  with B524 polling.
- SERVICE_WRITE (`00 03`) enable/disable frames serialize via `liveMonitorMu`
  and the quiesce window (§7.2). `M5_TRANSPORT_MATRIX` MUST include an
  explicit regression scenario (plan AD12) proving B524 baseline throughput is
  unchanged with the new mutex in place.

### 7.8 Stable API error model

The stable API (GraphQL `B503Availability` enum + MCP error code) exposes:

- `AVAILABLE`
- `NOT_SUPPORTED`
- `TRANSPORT_DOWN`
- `SESSION_BUSY`
- `UNKNOWN`

`EXPIRED` is not a member of this enum and never appears in any public
payload. See §8 for the normative normalization rules and §11 for the GraphQL
capability-signal contract.

## 8. Public Normalization Rules

The following rules are normative and binding on every downstream consumer
path (MCP resolvers, GraphQL resolvers, HA integration, portal).

1. **EXPIRED is internal-only.** Internal state `EXPIRED` MUST NOT appear in
   any public-facing enum, error model, or payload exposed to downstream
   consumers (MCP, GraphQL, portal, Home Assistant).
2. **Refresh-once on EXPIRED.** On `EXPIRED` detected inside a resolver, the
   resolver MUST auto-refresh session state and retry the operation
   **exactly once**.
3. **No collapse of transport/unknown outcomes.** After refresh, if the
   capability query reveals `TRANSPORT_DOWN` or `UNKNOWN`, those outcomes MUST
   be surfaced literally. They MUST NOT be collapsed into `SESSION_BUSY`.
4. **SESSION_BUSY is narrow.** `SESSION_BUSY` is reserved **only** for bounded
   lifecycle/contention ambiguity (another claimant, genuine in-flight
   contention). It is not a catch-all for unknown or transport failures.
5. **Bounded retries.** Maximum 1 auto-retry per request. No infinite
   reconnect loops. The transport layer owns reconnect; B503 resolvers do not.

## 9. Install-Writes Non-Exposure (v1 invariant)

`Clearerrorhistory` (selector `02 01`) and `Clearservicehistory` (selector
`02 02`) are classified `INSTALL_WRITE` (§4) and are subject to the following
normative v1 invariant:

> **`02 01` and `02 02` MUST NOT be exposed on any public surface in v1.**
> This includes, without exception, MCP tools, GraphQL mutations, portal UI
> affordances (including hidden / feature-flagged DOM), and Home Assistant
> services.

Enforcement:

- `M2a_GATEWAY_MCP` acceptance includes a negative test asserting no MCP tool
  exists for these selectors.
- `M2b_GATEWAY_GRAPHQL` acceptance includes a schema introspection diff
  asserting no mutation exists for these selectors.
- `M3_PORTAL` acceptance includes a DOM audit scanning for any element
  referencing `clear`, `delete`, or `reset` keywords in the B503 pane.

Any future exposure of these selectors requires a **separate plan** and a new
doc-gate PR per `AGENTS.md §8.4`, including installer-mode authentication
design and isolated-hardware bench evidence.

## 10. F.xxx Decimal Caveat (LOCAL_CAPTURE only)

The normative public contract publishes active-error and service slot values
**as decimal integers, as-is**. There is **no cross-device F.xxx lookup
table** in this specification.

A single local correlation has been observed:

- LOCAL_CAPTURE on BAI00: first slot `0x0119` = decimal `281` (§5.3).
- Unpublished operator UI observation on the same BAI00: `F.281 Flame loss
  during the stabilisation period`.

This proves **only** that on this specific BAI00 device generation, the first
active-error slot was equal to the decimal component of the operator UI code.
It does **not** prove that every Vaillant `F.xxx` code is mirrored as the same
decimal value on every device generation, nor that the mapping is stable
across HMU, EHP, or VRC720-family controllers.

Downstream consumers therefore:

- MUST publish the raw decimal value.
- MUST NOT present a translated F.xxx label in entity state or GraphQL
  resolver output.
- MAY attach a decoder-metadata annotation carrying `provenance=LOCAL_CAPTURE`
  for diagnostic purposes only, with no claim of cross-device validity.

Building a cross-device F.xxx table is deferred to a separate RE plan (see
plan §Scope OUT).

## 11. GraphQL Capability Signal (public contract)

The GraphQL capability signal `vaillantCapabilities.b503` is the authoritative
availability surface for HA and portal. It is defined here for doc-gate
completeness; the authoritative schema lives in
`helianthus-ebusgateway/graphql/schema`.

```graphql
type VaillantCapabilities {
  b503: B503Capability!
}

type B503Capability {
  available: Boolean!         # true only when reason == AVAILABLE
  reason: B503Availability!
}

enum B503Availability {
  AVAILABLE
  NOT_SUPPORTED    # device class does not implement B503
  TRANSPORT_DOWN   # transport currently disconnected
  SESSION_BUSY     # bounded contention: session held by another client OR in-flight lifecycle ambiguity (see §7.1, §8)
  UNKNOWN          # gateway has not yet determined availability
}
```

`EXPIRED` is **not** a member of this enum, per §8.

## 12. Production dispatcher contract

This section is the `M0b_DOC_DISPATCHER_BRIDGE` deliverable for execution-plans#19
amendment-1 and is the doc-gate companion for `M6_DISPATCHER_BRIDGE`
(helianthus-ebusgateway). It mirrors plan decisions AD16 (production raw-frame
dispatcher contract) and AD18 (capability-signal 8-state truth table +
stale-epoch discipline) from plan canonical SHA
`86495340799be9340dc191c371a49a958f65c357c76a1e0a2974502c8489b508`. The plan
chunks `13-amendment-1-dispatcher-portal-ux.md` and `10-scope-decisions.md` are
the canonical source; this section MUST NOT diverge. On conflict, the plan
wins and this section is updated by a follow-up doc-gate PR.

### 12.1 Dispatcher path overview

```mermaid
flowchart LR
    Caller[MCP / GraphQL caller]
    MCP[mcp_server resolver]
    Mgr["b503session.Manager<br/>(single-owner FSM, §6)"]
    Disp[RawFrameDispatcher.Invoke]
    Router[router.Invoke<br/>shared adaptermux/router substrate]
    Mux[adaptermux]
    Bus[(eBUS)]

    Caller --> MCP
    MCP --> Mgr
    Mgr --> Disp
    Disp --> Router
    Router --> Mux
    Mux --> Bus
```

The dispatcher path is single-substrate. There is **no** parallel transport
path for B503 (AD16). B524 and B525 already traverse the same `router.Invoke`
substrate; B503 production dispatch reuses that substrate verbatim. A gateway
configuration that injects any other transport path for B503 is
non-conforming.

### 12.2 `RawFrameDispatcher.Invoke` contract <a id="rawframedispatcher-invoke-contract"></a>

The dispatcher exposes a single method whose Go signature is fixed:

```go
Invoke(ctx context.Context, target byte, payload []byte) ([]byte, error)
```

Normative obligations:

- **Request shape.** `target` is the bus address of the destination slave
  (e.g. `0x08` for BAI00). `payload` is the complete L7 request body
  starting with the family/selector prefix defined in §2 (e.g.
  `b5 03 00 01` for `Currenterror`). The dispatcher MUST NOT prepend or
  rewrite the family/selector bytes; payload framing is the caller's
  responsibility.
- **Response shape.** On success the returned `[]byte` is the decoded L7
  response payload exactly as delivered by the underlying `router.Invoke`
  substrate, with no B503-specific stripping or padding.
- **Cancellation discipline.** The dispatcher MUST honour `ctx.Done()`.
  Cancellation before bus turnaround MUST surface as an
  `UPSTREAM_TIMEOUT` per §12.4 with `structured.detail.phase="ctx_canceled"`.
  In-flight bus traffic that is already on the wire MAY complete and be
  discarded; the dispatcher MUST NOT block on bus-quiesce after `ctx.Done()`.
- **Error mapping.** Transport and protocol errors are translated to the
  caller-visible enum in §12.4. Legitimate B503 protocol errors (NAK from
  the device) MUST NOT be collapsed into transport-level errors
  (`TRANSPORT_DOWN`).
- **Stub forbidden post-M6.** Once `M6_DISPATCHER_BRIDGE` lands, the
  `b503StubDispatcher{}` injection in `cmd/gateway/vaillant_b503_wiring.go`
  MUST be removed. The only acceptable post-deploy state is the production
  dispatcher live; reintroducing a stub fallback is a defect class (AD16).

### 12.3 Shared adaptermux/router routing semantics <a id="shared-router-substrate"></a>

The dispatcher routes through the **same** `router.Invoke` substrate used
by B524 and B525 (AD16). Implementation rules:

- The B503 dispatcher MUST NOT open its own adaptermux subscription, its
  own bus session, or any auxiliary transport channel.
- READ selectors (`00 01`, `01 01`, `00 02`, `01 02`) MAY proceed
  concurrently with B524 / B525 traffic on the same router (consistent
  with §7.7).
- `SERVICE_WRITE` (`00 03`) enable / disable frames serialise via
  `liveMonitorMu` and the §7.2 quiesce window, but the actual bus
  transaction is still issued through `router.Invoke`. The router is the
  one and only bus-access primitive.
- Transport disconnect MUST be propagated to
  `b503session.Manager.OnTransportDisconnect()` so the AD04 quiesce-release
  fires; the dispatcher acts as the propagation site.

### 12.4 Error-mapping table (NORMATIVE) <a id="error-mapping-table"></a>

The dispatcher translates transport and protocol errors to caller-visible
public surfaces as follows. The `structured.detail` discriminator keys are
the assertion targets for `M6_DISPATCHER_BRIDGE` tests; M6 tests fail if
any row collapses to a different public surface or omits the detail keys.

| Transport / protocol error | Caller-visible error | `structured.detail` keys |
|---|---|---|
| transport_down (adaptermux disconnected) | `TRANSPORT_DOWN` | `transport_state="down"`, `last_seen_ts=<unix>` |
| `ctx.Done` before bus turnaround | `UPSTREAM_TIMEOUT` | `timeout_ms=<int>`, `phase="ctx_canceled"` |
| bus NAK | `UPSTREAM_RPC_FAILED` | `nak_byte=<hex>`, `target=<hex>` |
| CRC mismatch | `UPSTREAM_RPC_FAILED` | `crc_expected=<hex>`, `crc_got=<hex>` |
| stale-epoch reply (AD18 row 8) | (frame discarded; caller still pending) | n/a — see §12.6 stale-epoch discipline |

Discriminator rules:

- `TRANSPORT_DOWN` is reserved for transport-level loss. A device NAK is a
  legitimate B503 protocol response and MUST NOT be reported as
  `TRANSPORT_DOWN`. A CRC mismatch is a protocol-layer failure and MUST
  NOT be reported as `TRANSPORT_DOWN` either.
- `UPSTREAM_TIMEOUT` is reserved for caller-driven cancellation
  (`ctx.Done`) before the bus has produced a reply. Bus arbitration
  timeouts that occur after the request reaches the wire are reported as
  `UPSTREAM_RPC_FAILED` with a `phase="bus_timeout"` detail key (added by
  M6 if observed; not pre-declared here).
- `UPSTREAM_RPC_FAILED` is the catch-all for protocol-level failure with
  a populated discriminator. The discriminator MUST be present; an
  `UPSTREAM_RPC_FAILED` without `structured.detail` is non-conforming.

### 12.5 Capability-signal 8-state truth table (mirror of AD18) <a id="capability-truth-table"></a>

The `vaillantCapabilities.b503` capability output (§11) follows the 8-state
truth table below. The plan AD18 entry in
`vaillant-b503-namespace-w17-26.implementing/10-scope-decisions.md` is the
canonical source; this table mirrors it for doc-gate completeness. Each
row is a separate `M6_DISPATCHER_BRIDGE` test target; missing-coverage on
any row is an automatic merge-gate block.

| # | State | Capability output | Stale-frame discipline |
|---|---|---|---|
| 1 | cold-boot, no successful dispatch yet | `UNKNOWN` | n/a |
| 2 | post-first-success steady state | `AVAILABLE` | n/a |
| 3 | disconnect during ACTIVE session | `TRANSPORT_DOWN` (literal) | in-flight requests fail `TRANSPORT_DOWN`; no late mutation |
| 4 | reconnect, before first post-reconnect dispatch | `UNKNOWN` (NOT sticky `AVAILABLE`) | reset to `UNKNOWN` regardless of pre-disconnect state |
| 5 | reconnect, post-first-success-after-reconnect | `AVAILABLE` | n/a |
| 6 | timeout/NAK/CRC during dispatch | `UPSTREAM_RPC_FAILED` to caller; capability stays last-known | n/a |
| 7 | session-expiry detected | `EXPIRED` internal → AD14 1-retry → `AVAILABLE` OR `TRANSPORT_DOWN` literal | n/a |
| 8 | stale in-flight completion across epoch rollover | n/a — frame discarded | reply/NAK/timeout from epoch N arriving after reconnect to epoch N+1 MUST be discarded; MUST NOT mutate capability to `AVAILABLE`; MUST NOT satisfy any post-reconnect waiter |

**Forbidden states** (M6 tests assert absence):

- sticky `AVAILABLE` after transport loss;
- premature `AVAILABLE` before the first real dispatch;
- silent fallback to `UNKNOWN` once `TRANSPORT_DOWN` is knowable.

`EXPIRED` remains gateway-internal per §7.1.1 and §8; row 7 above describes
the internal sub-state, not a public capability value.

### 12.6 Lock acquisition order invariant <a id="lock-order"></a>

The gateway uses two B503-related mutexes:

- `liveMonitorMu` — write-class mutex acquired by `b503session.Manager.Enable`,
  `Read` on the `00 03` selector, and `Disable`. It is **distinct** from
  the B524 `readMu` (§7.4).
- `readMu` — the B524 family poll mutex.

**Acquisition order is INVARIANT: `liveMonitorMu → readMu`.** Reversal is a
defect class (AD16). Implementations MUST NOT enter `readMu` while holding
`liveMonitorMu` in the forbidden order, AND MUST NOT enter `liveMonitorMu`
while waiting on `readMu`.

`M6_DISPATCHER_BRIDGE` acceptance verifies this mechanically: the test
harness installs a build-tagged lock tracer/hook on `liveMonitorMu` and
`readMu` that records every `Lock()` / `Unlock()` with goroutine ID and
timestamp. Each `M6-CONC-*` concurrency test asserts via the tracer that no
goroutine ever crossed the forbidden order. `-race` and a 30 s deadlock
timeout are SECONDARY trip-wires, not the primary proof (AD16 + R3 A1 fix
in plan §13).

### 12.7 Epoch-tagged in-flight requests <a id="epoch-tagged-inflight"></a>

Per AD18 row 8 (stale-epoch discipline), every B503 dispatch request MUST
capture the current `b503session.Manager.epoch` value into an in-flight
request record at issue-time. Reply, NAK, and timeout completion paths
MUST compare against the **stored** epoch BEFORE waking waiters or
mutating capability state.

Normative rules:

- Epoch comparison is **request-side metadata**, populated when the
  request leaves `RawFrameDispatcher.Invoke`. It MUST NOT be re-derived
  from `Manager` at receive time.
- A reply / NAK / timeout from epoch N that arrives after the transport
  has rolled over to epoch N+1 MUST be:
  1. discarded silently;
  2. NOT used to mutate the capability signal to `AVAILABLE`;
  3. NOT used to satisfy any post-reconnect waiter.
- The discard path MUST NOT inspect the new (epoch N+1) `Manager` state to
  decide; the request's stored epoch is sufficient on its own.

This is the only correct closure for the AD18 row 8 stale-frame race. A
completion path that compares against `Manager.epoch` at receive time is
non-conforming because the epoch may have advanced between request issue
and reply arrival, allowing a stale frame to satisfy a fresh waiter.

### 12.8 Companion test surface

`M6_DISPATCHER_BRIDGE` acceptance lives in the plan
(`13-amendment-1-dispatcher-portal-ux.md §M6`); §12.4–§12.7 are the
assertion targets (error-mapping rows, 8 truth-table tests, 4 `M6-CONC-*`
lock-tracer tests, stale-epoch in-flight completion test). On disagreement
between this doc and the plan, the plan wins and a follow-up doc-gate PR
realigns §12.

## 13. Evidence Labels (preserved)

The evidence labels defined in §1 are used throughout. In particular:

- The §3 selector catalog is `LOCAL_TYPESPEC` + `LOCAL_CAPTURE` grounded.
- The §5.3 worked example is `LOCAL_CAPTURE`.
- The §10 F.xxx correlation is `LOCAL_CAPTURE`-only; no `PUBLIC_CONFIG` or
  cross-device evidence has been admitted into this spec.
- Future device-class coverage additions MUST cite the evidence label that
  supports them before entering the normative catalog.

## 14. Companion Links (downstream code milestones)

| Milestone | Repo | Artefact |
|---|---|---|
| `M1_DECODER` | `helianthus-ebusgo` | `protocol/vaillant/b503` decoder package + invoke-safety enum |
| `M2a_GATEWAY_MCP` | `helianthus-ebusgateway` | MCP tools `ebus.v1.vaillant.errors.get`, `.errors.history.get`, `.service.current.get`, `.service.history.get`, `.live_monitor.get` |
| `M5_TRANSPORT_MATRIX` | `helianthus-ebusgateway` | `matrix/M6a-vaillant-b503.md` — adapter-direct + `ebusd_tcp` (+ `ebusd_serial` if lab-available) |
| `M2b_GATEWAY_GRAPHQL` | `helianthus-ebusgateway` | GraphQL read-only parity + `vaillantCapabilities.b503` signal |
| `M3_PORTAL` | `helianthus-ebusgateway` | Vaillant pane (errors / service / live-monitor tabs, read-only) |
| `M4_HA` | `helianthus-ha-integration` | diagnostic sensor `boiler_active_error` + `error_history` attribute, capability-signal-gated |
| `M6_DISPATCHER_BRIDGE` (amendment-1) | `helianthus-ebusgateway` | production `RawFrameDispatcher` replacing `b503StubDispatcher{}` injection in `cmd/gateway/vaillant_b503_wiring.go`; contract per §12 (PR ref: TBD) |

Dependency DAG (plan AD09 + amendment-1):
`M0 → M1 → M2a → M5 → M2b → {M3, M4} → M6 → {M7, M8}` with
`M0b` parallel to `M6` and merge-blocking it.

All downstream PRs MUST include a companion-link reference to this document in
their PR body.

## 15. References

- Plan: `helianthus-execution-plans/vaillant-b503-namespace-w17-26.implementing/`
  (canonical SHA `86495340799be9340dc191c371a49a958f65c357c76a1e0a2974502c8489b508`,
  amendment-1 locked 2026-04-25). Prior v1.0 baseline canonical SHA was
  `896a82e720b33eefb449ea532570e0a962bfa76504519996825f13d92ec9bb28`; amendment-1
  supersedes it.
- Amendment-1 chunk: [`13-amendment-1-dispatcher-portal-ux.md`](https://github.com/Project-Helianthus/helianthus-execution-plans/blob/main/vaillant-b503-namespace-w17-26.implementing/13-amendment-1-dispatcher-portal-ux.md)
  — canonical source for §12 (M0b / M6 / M7 / M8).
- Decision matrix: [`10-scope-decisions.md`](https://github.com/Project-Helianthus/helianthus-execution-plans/blob/main/vaillant-b503-namespace-w17-26.implementing/10-scope-decisions.md)
  — canonical source for AD16 (production dispatcher contract) and AD18
  (capability-signal 8-state truth table + stale-epoch discipline).
- Meta-issue: [execution-plans#19](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/19).
- Doc-gate issue (v1.0): [docs-ebus#282](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/282).
- Doc-gate issue (amendment-1 / M0b): [docs-ebus#288](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/288).
- Public TypeSpec: [errors_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/errors_inc.tsp)
- Public TypeSpec: [service_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/service_inc.tsp)
- Public TypeSpec: [08.hmu.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/08.hmu.tsp)
- Data type reference: [`../../types/ebusd-csv.md`](../../types/ebusd-csv.md)
- Consolidated local reference: [`ebus-vaillant.md`](ebus-vaillant.md)
- Sibling normative doc (structure precedent): [`ebus-vaillant-B505.md`](ebus-vaillant-B505.md)
