# M4b2 Responder Go/No-Go Decision — Capability Signal Contract

Status: Normative (decision artifact)
Milestone: M4b2_responder_go_no_go
Plan reference: `ebus-standard-l7-services-w16-26.implementing/00-canonical.md`
Canonical SHA-256: `9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`
Depends on: [`11-m4b-semantic-lock.md`](./11-m4b-semantic-lock.md) (M4B lock; §6.2 additive policy is load-bearing)
Consult: cruise-consult dual-vendor (Claude + Codex), 2 rounds, joint verdict
`option_go_transport_scoped`.

## §1 — Verdict

**GO** — proceed with **M4c1** (ebusgo responder transport primitives) + **M4c2**
(gateway responder runtime) + **M4D** (doc companion + capability signal freeze)
for **ENH** and **ENS** transports. **ebusd-tcp is explicitly BLOCKED** for the
responder lane with machine-readable reason `command_bridge_no_companion_listen`.

One-sentence summary: *proceed M4c1+M4c2+M4D for ENH/ENS only; expose explicit
per-transport responder capability as an additive `v1.minor` meta key;
ebusd-tcp surfaces as `scope: none` with an explicit blocker reason.*

## §2 — Rationale

The M4b1 spike (helianthus-ebusgo branch `spike/m4b1-responder-feasibility`,
commit `930aedf`) established that:

- **ENH / ENS**: byte-level ingress is already present
  (`ReadByte`/`ENHResReceived` pathways); responder-side send substrate exists;
  the gaps are bounded — a `ResponderTransport` interface that bypasses
  `StartArbitration`, responder-frame decode, local-slave dispatch, and
  ACK/response/final-ACK FSM. Timing budget is the only open PASS/FAIL
  criterion, and it is measurable in M4c1.
- **ebusd-tcp**: the transport wraps the ebusd command socket. Inbound bytes
  are correlated to our own `Write`; there is no goroutine or API surface for
  unsolicited bus ingress addressed to the gateway's local-slave address.
  The only way to emit a responder reply through ebusd is to route through
  ebusd's own `answer` command, which violates the workspace ebusd-isolation
  invariant and surrenders responder identity to a daemon the gateway does not
  own. The plan hypothesis is therefore confirmed: ebusd-tcp is
  architecturally a command bridge, not a real-time eBUS endpoint.

The gateway execution-policy module already carries the four FF 03/04/05/06
responder rows with `RequestOrResponseRole=RoleResponder` and
`transport_capability_requirements=["responder"]`
(`helianthus-ebusgateway/internal/execution_policy/whitelist.go`). Policy
admission for the responder lane therefore requires **no 14-axis whitelist
widening**; `ErrSafetyClassDenied` continues to be the sole policy sentinel.

M4B §6.2 explicitly permits new `meta.*` keys under a `contract.minor` bump
without plan amendment, so the capability signal specified in §4 below is a
clean additive lock rather than a breaking change.

## §3 — Per-transport scope matrix

| Transport | Verdict | `responder_available` (derived) | `scope` | `state` | `reason` |
|---|---|---|---|---|---|
| **ENH** | GO | `true` | `partial` | `supported` | `null` |
| **ENS** | GO | `true` | `partial` | `supported` | `null` |
| **ebusd-tcp** | BLOCKED | `false` | `none` | `blocked` | `command_bridge_no_companion_listen` |

Notes per row:

- **ENH**: substrate complete; M4c1 must add the responder send primitive
  bypassing arbitration, responder decoder, local-slave dispatch, and timing
  harness. Proceed conditional on M4c1 timing PASS (§7).
- **ENS**: constructed through the same `ENHTransport` path with
  `arbitrationSendsSource=true`; inherits ENH responder implementation at zero
  marginal cost. An explicit ENS fixture / bench case MUST be added; this is
  not a free pass by inference.
- **ebusd-tcp**: remains fully supported for its existing roles (readonly +
  initiator where already supported); the responder lane is closed. The
  capability signal row is REQUIRED (not omitted); absence-by-omission is
  forbidden per §5 invariants.

Additional transports (e.g. `tcp_plain`, `udp_plain`, `loopback`) are NOT
enumerated at this minor. Their absence from the `transports[]` array is
`state: unknown` per §5, not `state: blocked`.

## §4 — Capability signal contract

### §4.1 Location

`meta.capabilities.responder` on every MCP envelope emitted by the four
M4B-locked surfaces (`services.list`, `commands.list`, `command.get`,
`decode`). When future runtime-status surfaces (e.g.
`ebus.v1.runtime.status.get`) land, they MUST mirror the same key under the
same minor.

### §4.2 Shape (locked at M4D; sketched here for M4c2 integration)

```json
{
  "meta": {
    "contract": { "name": "helianthus-ebus-mcp", "major": 1, "minor": 1 },
    "capabilities": {
      "responder": {
        "version": "v1",
        "active": {
          "transport": "ENH",
          "scope": "partial",
          "surfaces": ["FF_03", "FF_04", "FF_05", "FF_06"],
          "refusal": null
        },
        "transports": [
          { "transport": "ENH",       "state": "supported", "scope": "partial", "surfaces": ["FF_03","FF_04","FF_05","FF_06"], "reason": null },
          { "transport": "ENS",       "state": "supported", "scope": "partial", "surfaces": ["FF_03","FF_04","FF_05","FF_06"], "reason": null },
          { "transport": "ebusd-tcp", "state": "blocked",   "scope": "none",    "surfaces": [],                                          "reason": "command_bridge_no_companion_listen" }
        ]
      }
    }
  }
}
```

Field semantics:

- `capabilities.responder.version`: string literal `"v1"` at this minor;
  semver bumps when the shape itself changes (orthogonal to
  `meta.contract.minor`).
- `active`: realized capability for the transport serving THIS response.
  Consumers MUST gate current-request responder behavior on `active` only.
  - `active.transport`: enum (union of `transports[].transport`).
  - `active.scope`: enum `{full, partial, none}`; MUST equal
    `transports[x].scope` where `x.transport == active.transport`.
  - `active.surfaces`: array of L7 selector strings (PB+SB or selector-path)
    indicating which responder surfaces the active transport supports at
    this minor. Empty array when `scope == none`.
  - `active.refusal`: `null` on success; when responder attempt was refused
    at capability layer (not policy), `{code, reason}` object.
- `transports[]`: profile / introspection data; MUST include one row per
  known transport at this minor (ENH, ENS, ebusd-tcp — exactly three rows
  at `v1.1`).
  - `transports[].state`: enum
    `{supported, blocked, unknown, not_configured}`.
    - `supported`: transport viable; `scope != none`.
    - `blocked`: transport architecturally incapable of responder
      (ebusd-tcp); `scope == none`; `reason` REQUIRED.
    - `unknown`: transport enumerated by code but no spike / proof exists
      yet; `scope == none`; `reason == null` permitted.
    - `not_configured`: transport exists in code but not wired at this
      deployment; `scope == none`; `reason == null` permitted.
  - `transports[].scope`: enum `{full, partial, none}`.
    `scope == none` ⟺ responder-unavailable on that transport.
  - `transports[].surfaces`: subset of the L7 surfaces the catalog declares
    as responder-emittable; empty when `scope == none`.
  - `transports[].reason`: required when `state == blocked`; enum at v1.1:
    `{command_bridge_no_companion_listen, timing_unavailable}`. MUST be
    `null` when `state == supported`. Enum is locked-open per §6 — new
    reasons MAY be added under a later `contract.minor` bump, but the
    enum is **scoped to transport-capability conditions only**. Per-request
    authorization failures MUST NOT be expressed via this field; they
    flow through `ErrSafetyClassDenied` with audit `outcome=policy_denied`
    per §5. In particular, `policy_denied` is **forbidden** as a
    `transports[].reason` value — conflating the two channels would break
    audit parity and mislead consumers that treat blocked reasons as
    static transport constraints.

### §4.3 Consumer rule (fail-closed)

Consumers MUST gate current-request responder behavior on **`active` only**:

1. Absence of `meta.capabilities.responder` ⇒ treat as `active.scope = none`.
2. Absence of `active` ⇒ treat as `active.scope = none`.
3. Unknown `active.scope` string ⇒ treat as `scope = none` (per M4B §6.2
   open-enum forward-compat rule).
4. `active.scope == none` OR `active.available` (derived, `scope != none`)
   evaluating false ⇒ MUST NOT attempt responder invocation; MAY surface
   UI hint based on `transports[]`.
5. `transports[]` is **informational / profile only**. It MUST NOT enable
   current-request responder behavior. A `transports[]` entry with
   `scope: partial` on a non-active transport is discovery data for
   transport-switch UX, not an authorization signal.
6. Unknown `active.refusal.code` string ⇒ treat as generic capability
   refusal (fail-closed); MUST NOT attempt responder invocation; MAY log
   the unknown code for diagnostics but MUST NOT surface it as a
   success-path signal. Unknown `transports[].state` and unknown
   `transports[].reason` strings degrade to fail-closed per the same
   rule.

### §4.4 Invariants (normative)

- I1. `transports[]` MUST include exactly one row per transport enumerated
  in code at this minor (v1.1: ENH, ENS, ebusd-tcp — three rows).
- I2. `active.transport` MUST appear in `transports[]`.
- I3. `active.scope` MUST equal `transports[x].scope` where
  `x.transport == active.transport`.
- I4. `scope == none` ⟺ transport does NOT support responder at this minor.
  No separate `responder_available` boolean is emitted — `scope` is the
  single source of truth.
- I5. `state == blocked` REQUIRES `reason != null` and `scope == none`.
- I6. `state == supported` REQUIRES `reason == null` and `scope != none`.
- I7. Duplicate transport rows in `transports[]` are forbidden.
- I8. Unknown `active.refusal.code` values are treated as generic
  capability refusal (fail-closed) per §4.3 rule 6.

### §4.5 `v1.minor` additive justification

This entire signal is a net-new `meta.*` key. Per M4B
[`11-m4b-semantic-lock.md`](./11-m4b-semantic-lock.md) §6.2 bullet 1, new
`meta.*` keys are permitted under a `contract.minor` bump without plan
amendment. `meta` already declares `additionalProperties: true` at M4B §1.2.
No existing key is renamed, no type narrowed, no error code repurposed.
Forward-compat conformance (M4B §7.3) extends to: unknown
`active.transport` value, unknown `active.scope`, unknown
`transports[].state`, unknown `transports[].reason`, and missing
`meta.capabilities.responder` — all MUST parse without error.

## §5 — Policy-module integration

M4c2 runtime MUST consult `execution_policy.Check(cmd, CallerSystemNMRuntime)`
for every inbound responder-role telegram BEFORE composing a reply. The
14-axis whitelist in
`helianthus-ebusgateway/internal/execution_policy/whitelist.go` already
contains FF 03/04/05/06 entries with `RoleResponder` +
`transport_capability_requirements=["responder"]`. A responder-lane inbound
match constructs an `ebusstd.IdentityKey` from the decoded PB/SB + selector
and submits it. **No 14-axis whitelist widening is required.**

`ErrSafetyClassDenied` continues to be the sole **policy-denial** sentinel.
It wraps the provider-level sentinel and carries dynamic audit context
(caller, matched row, tuple). Conflating capability refusal with policy
denial would pollute audit outcome codes (per 05-execution-safety.md
§Audit Requirement) and break denial-parity tests.

**New sentinel introduced at M4c2 construction time**: `ErrResponderTransportUnavailable`,
distinct from `ErrSafetyClassDenied`. Semantics:

- Fires when a catalog identity requires responder transport support but
  the active transport has `responder.scope == none` (ebusd-tcp) OR the
  requested surface is not in the active transport's `surfaces[]`.
- Fires at wiring / capability-probe time (construction of the responder
  goroutine), NOT on every per-call check.
- Populates `transports[].scope == none` entries in the capability signal.
- Populates `active.refusal.code` when the active transport happens to be
  blocked (ebusd-tcp-only deployment).
- MUST NOT appear in audit records with `outcome=policy_denied`.

M4c2 MUST add a transport-capability **pre-gate**: if the active
transport's responder scope is `none`, the responder goroutine MUST NOT be
wired at all. This is fail-closed by construction and mirrors the
`nm_runtime.NewRuntime` fail-fast pattern (`ErrEmitterRequired`).

User-facing `rpc.invoke` remains default-denied for response-role and
responder-emit variants unless policy explicitly allows the caller context.
No user-facing surface is widened by M4c2.

## §6 — Stage gating

### §6.1 M4c1 — ebusgo responder transport primitives

- **RED**: test matrix asserting:
  - `ResponderTransport` interface absence today.
  - ENH/ENS send-without-arbitration missing.
  - Addressed-frame parser missing for responder direction.
  - ACK-response-final-ACK FSM missing.
  - ebusd-tcp non-support (compile-time or runtime refusal).
  - Timing harness absent.
- **IMPL**: two PRs (strict dependency order):
  - PR-A: `transport.ResponderTransport` interface + ENH implementation of
    `SendResponderBytes` bypassing arbitration precondition.
  - PR-B: `protocol/responder` package — inbound frame decoder, local-slave
    dispatch, ACK/response/final-ACK state machine.
  - Both PRs ship with emulation-harness unit tests + one live-bus timing
    assertion (target: responder ACK + reply emission within the eBUS
    target-response window; threshold encoded in test).
- **GREEN**: emulation round-trip + one live bench capture proving ACK-in-window
  on BASV2 (0x15) or equivalent live slave.

### §6.2 M4c2 — gateway responder runtime

- **Hard dependency**: M4c1 merge + go.mod bump to the merged ebusgo
  revision in helianthus-ebusgateway.
- **IMPL adds**:
  - NM runtime responder emit path for FF 03/04/05/06 (catalog-driven; no
    hand-coded FF responder path).
  - Transport-capability pre-gate (`ErrResponderTransportUnavailable`,
    construction-time).
  - Audit-log outcome codes: `responded`, `suppressed_by_capability` (distinct
    from `policy_denied`).
  - Capability signal emission wired into `mcp/ebus_standard/envelope.go`
    under `meta.capabilities.responder`.
- **GREEN**: catalog-integration responder tests + emulator round-trip +
  audit-outcome parity test + envelope golden fixture updates at
  `meta.contract.minor = 1`.

### §6.3 M4D — doc companion + capability signal freeze

- **Parallel with M4c2 IMPL** once §4 shape is agreed (this document).
- **IMPL**:
  - Responder-lane chapter in `05-execution-safety.md` mirroring FF 03-06
    runtime semantics.
  - New chapter `13-responder-capability-signal.md` formally locking the §4
    shape at `meta.contract.minor = 1`.
  - Transport matrix update in `04-capability-discovery.md` pointing at the
    new runtime signal.
- **Merge ordering invariant**: M4D MUST merge **before or with** M4c2
  (doc-gate invariant). M4D MUST NOT merge before M4c1 (dependency on the
  responder substrate being real).

### §6.4 M5 / M5b — consumer unblock

- **M5_PORTAL**: vrc-explorer consumes `meta.capabilities.responder.active`
  for the responder UI gate (fail-closed per §4.3); uses `transports[]` for
  transport-switch affordance rendering.
- **M5b_HA_NOOP_COMPAT**: HA integration remains no-op for responder
  entities; any capability-metadata consumption MUST be fail-closed.

## §7 — No-go fallback

### §7.1 Lane-abort conditions (mid-flight abort; responder lane reverts to readonly)

M4c aborts mid-flight and the responder lane reverts to readonly IF any of:

1. Live-bus bench in M4c1 shows responder ACK emission consistently
   exceeding the eBUS target-response window on ENH → transport degrades
   to `scope: none, reason: timing_unavailable`; no M4c2 for that transport.
   If both ENH and ENS fail → full lane abort.
2. Adapter-proxy fan-out measurement reveals byte serialization or
   reordering breaking timing on the shared RPi4 → open `ISSUE-PROXY-EBS-01`
   and pause M4c2 until resolved. If the proxy architecture cannot
   guarantee timing under any achievable configuration → lane abort.
3. Concurrent initiator + responder ownership on the gateway deadlocks via
   `protocol.Bus.readMu` → abort M4c2, revert to single-role posture,
   re-architect; do NOT ship a deadlock-prone runtime.

Under these aborts, the capability signal collapses to `active.scope =
none` + `transports[].scope = none` across all transports (ENH/ENS rows
carry `state: blocked` + `reason: timing_unavailable` as applicable), and
the v1.minor bump STILL ships to document the capability vocabulary and
lock shape for any future spike.

### §7.2 PR-local rework conditions (block the PR, NOT the lane)

The following conditions are PR-local quality gates; they block the
offending PR but DO NOT trigger a §7.1 lane abort:

1. `execution_policy.Check` returns `ErrSafetyClassDenied` for a
   whitelisted FF 0x tuple due to `IdentityKey` construction drift in
   M4c2 (catalog-integration test fails) → block the PR, fix key
   construction, re-submit; lane continues.
2. Forward-compat conformance golden (per §4.5) fails on a synthetic
   unknown-value payload → block the PR, fix schema/emission, re-submit.
3. Audit-outcome parity test (`suppressed_by_capability` vs
   `policy_denied` separation) fails → block the PR, fix outcome
   routing, re-submit.

These are distinct from §7.1 because they indicate implementation bugs
within a lane that is otherwise viable. Decisions on §7.1 vs §7.2
classification MUST be made by the merge-gate owner; ambiguous cases
escalate to operator per cruise-run protocol.

## §8 — Residual risks

1. **Bus contention** — concurrent initiator polling + responder reply on
   the same gateway may deadlock on `protocol.Bus.readMu`. Explicitly
   flagged by spike; load-bearing test in M4c2.
2. **Adapter-proxy fan-out timing** — if the RPi4 proxy serializes or
   reorders RECEIVED bytes across attached clients, responder timing
   budget can be blown even with a fast gateway. Requires measurement
   before M4c2 GREEN.
3. **IdentityKey construction drift** — 14-axis key MUST be built with
   `TransportCapabilityRequirements=["responder"]` exactly to match
   whitelist (reflect.DeepEqual in `nmWhitelistContains`). Drift silently
   denies via `ErrSafetyClassDenied`. Regression test required.
4. **Consumer mis-reads `transports[]` as authorization** — fail-closed
   rule §4.3.5 is a contract requirement; enforce via forward-compat
   conformance golden (§4.5) with a synthetic payload where a
   non-active transport reports `scope: partial` and the consumer MUST NOT
   invoke.
5. **Timing threshold leak into telemetry** — if M4c1 encodes the
   target-response window as a magic constant, it diverges across
   repos. Must live in shared config or ebusgo exported constant.
6. **ENS-vs-ENH on-wire divergence** — current code treats them
   identically (`arbitrationSendsSource=true` parity), but if ENS
   responder framing differs, ENS scope needs re-verification.
7. **Audit-outcome pollution** — conflating
   `ErrResponderTransportUnavailable` with `ErrSafetyClassDenied` would
   surface false-positive denials in compliance reporting. Separate
   outcome codes enforced in audit schema.
8. **Reason enum growth** — `reason` enum MUST stay small and stable; new
   values are additive per §6 but require forward-compat tests.

## §9 — Decision process audit

- **Dispatch**: Q2 of cruise-consult dual-vendor pair (Q1 = M4B, merged as
  `91bcb34c` via helianthus-docs-ebus#273).
- **Round 1**: verdict-name divergence — Codex: `option_go_full`, Claude:
  `option_go_partial` — with materially identical executable plan
  (≥4 overlapping evidence refs, ≥4 overlapping residual risks).
- **Round 2**: both vendors declared `can_merge: true`; converged on joint
  verdict `option_go_transport_scoped` with union of:
  - `active` + `transports[]` dual-shape (Codex's profile + Claude's
    fail-closed active-only gating).
  - `state` field (Codex) alongside `scope` field (Claude) — both
    preserved (orthogonal dimensions).
  - `surfaces[]` per-transport (Codex) for introspection.
  - `scope` as single authorization signal (Claude) — no redundant
    `responder_available` boolean.
  - Machine-readable `reason` enum (union of both), scoped to transport-capability conditions only; per-request authorization denials flow exclusively through `ErrSafetyClassDenied` / audit `outcome=policy_denied` (no cross-channel leak).
  - `ErrResponderTransportUnavailable` construction-time sentinel (both).
- **Supersedes**: nothing (first M4b2 artifact).
- **Amendment policy**: changes to §3 / §4.1-4.4 / §5 / §7 require a
  plan-amendment decision. §4 enum additions (new transports, new reasons,
  new scope values) are additive under `contract.minor` bumps per M4B §6.2.
