# M4D Responder Capability Signal — Normative Lock

Status: Normative (lock artifact)
Milestone: M4D_responder_capability_lock
Plan reference: `ebus-standard-l7-services-w16-26.implementing/00-canonical.md`
Canonical SHA-256: `9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`
Gateway anchor commit: `547fd4ed` (helianthus-ebusgateway#509, merged 2026-04-19)
Depends on: M4B semantic lock — [`11-m4b-semantic-lock.md`](./11-m4b-semantic-lock.md)
            (§6.2 additive `meta.*` policy, §7.3 forward-compat conformance)
Depends on: M4c2 producer — `helianthus-ebusgateway/mcp/ebus_standard/responder_capability.go`
Supersedes (shape + invariants only): `helianthus-execution-plans/ebus-standard-l7-services-w16-26.implementing/decisions/m4b2-responder-go-no-go.md`
§4.2 + §4.3 + §4.4 (execution-plans#17 @ `567a6798`). The M4b2 decision
doc remains authoritative for rationale, stage gating (§6), residual risks
(§8), and no-go fallback (§7). This chapter is the authoritative **wire
contract** from merge of gateway `547fd4ed` onward.

## Purpose

This chapter freezes the exact shape, invariants, and consumer rule of the
`meta.capabilities.responder` key emitted on every MCP envelope by the
four M4B-locked surfaces (`services.list`, `commands.list`, `command.get`,
`decode`) at `meta.contract.minor = 1`.

The M4b2 decision doc §4 framed this signal as **forward specification**
— a producer target that would become a wire contract "once the gateway
actually emits it on the wire." That condition is now satisfied:
helianthus-ebusgateway#509 (squash `547fd4ed`) bumped
`EnvelopeContractMinor` from `0` to `1` and wired the capability signal
into `mcp/ebus_standard/envelope.go::NewEnvelope`. This chapter ratifies
the emitted shape as normative.

Every clause marked **MUST** below is a hard lock against breaking change.
Additive extension under `contract.minor` remains permitted per §6.

## Scope

This lock covers, exactly and exhaustively:

1. The location of the capability signal within the M4B envelope.
2. The JSON shape of `meta.capabilities.responder` (fields, types,
   defaults, null-semantics).
3. The invariants I1 through I8 that relate `active` to `transports[]`.
4. The fail-closed consumer rule (six normative MUST clauses).
5. The enum surfaces at `v1.1`: `surfaces`, `reason`, `state`, `scope`.
6. The subtree-version policy (`responder.version`) and its orthogonality
   to `meta.contract.minor`.
7. The relationship to the M4B lock (this is an additive v1.minor
   extension under §6.2 bullet 1).
8. Audit-outcome separation (capability-suppression vs policy-denial
   channels).

Out of scope (unchanged by this lock):

- The M4B envelope shape (`meta` / `data` / `error` structure and all of
  [`11-m4b-semantic-lock.md`](./11-m4b-semantic-lock.md) §§1–5).
- The 14-axis execution-policy whitelist (`05-execution-safety.md`).
- The `rpc.invoke` source byte invariant (`10-rpc-source-113.md`).
- Responder transport primitives themselves (helianthus-ebusgo, M4c1).

## §1 — Location

`meta.capabilities.responder` is emitted on every MCP envelope returned by
the four M4B-locked surfaces:

- `ebus.v1.ebus_standard.services.list`
- `ebus.v1.ebus_standard.commands.list`
- `ebus.v1.ebus_standard.command.get`
- `ebus.v1.ebus_standard.decode`

Lock clauses:

- The key MUST appear whenever the gateway has a canonical transport
  (`ENH`, `ENS`, `ebusd-tcp`) wired at bootstrap.
- When the active transport is not one of the three canonical enumerated
  transports — or when no transport has been wired at all (pre-bootstrap,
  unit-test Config-only callers) — the producer MUST omit
  `meta.capabilities.responder` entirely. Absence is authoritatively
  equivalent to `active.scope = none` per §4 rule 1 (fail-closed).
  Emitting an empty or placeholder object is **forbidden** because it
  would falsely promise a shape consumers are entitled to interpret.
- Future runtime-status surfaces (e.g. `ebus.v1.runtime.status.get`) that
  land under a later `contract.minor` MUST mirror this same key under
  the same shape; divergence is a v2 breaking change.

## §2 — Shape

The canonical shape at `contract.minor = 1` is:

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
          { "transport": "ebusd-tcp", "state": "blocked",   "scope": "none",    "surfaces": [],                                 "reason": "command_bridge_no_companion_listen" }
        ]
      }
    }
  }
}
```

Field semantics (all locked):

| Field | Type | Lock |
|---|---|---|
| `responder.version` | string | Semver of the **subtree shape**, literal `"v1"` at this minor. Orthogonal to `meta.contract.minor`; see §6. |
| `responder.active` | object | Realised capability for the transport serving THIS response. Consumers MUST gate current-request behaviour on `active` only (§4). |
| `active.transport` | string | Enum; value MUST appear verbatim in `transports[].transport`. |
| `active.scope` | string | Enum `{full, partial, none}`; MUST equal `transports[x].scope` where `x.transport == active.transport` (I3). |
| `active.surfaces` | array<string> | L7 selector strings supported by the active transport. Empty `[]` when `active.scope == none`. |
| `active.refusal` | object or null | `null` on success; when the capability layer refuses, a `{code, reason}` object. Never omitted. |
| `active.refusal.code` | string | Machine-readable enum (see §5.2 for v1.1 values). |
| `active.refusal.reason` | string | Human-readable explanation; free-form. |
| `responder.transports` | array<object> | Per-transport profile. Exactly three rows at `v1.1` (I1). Discovery/introspection only — never an authorisation signal (§4 rule 5). |
| `transports[].transport` | string | Enum member. Duplicates forbidden (I7). |
| `transports[].state` | string | Enum `{supported, blocked, unknown, not_configured}` (§5.3). |
| `transports[].scope` | string | Enum `{full, partial, none}` (§5.4). |
| `transports[].surfaces` | array<string> | L7 surfaces the row supports; empty `[]` when `scope == none`. |
| `transports[].reason` | string or null | Required when `state == blocked` (I5); `null` when `state == supported` (I6). |

The canonical byte-exact reference for a synthetic forward-compat payload
is:

```
helianthus-ebusgateway/mcp/ebus_standard/testdata/forward_compat_synthetic_v1_1.golden.json
```

## §3 — Invariants (normative)

The following invariants are **MUST** clauses. A producer violating any of
them emits a non-conformant envelope; a consumer may reject such an
envelope or treat it as degraded (fail-closed per §4 rule 3).

| ID | Invariant | Enforcement |
|---|---|---|
| **I1** | `transports[]` MUST contain **exactly one row per transport enumerated in code at this minor**. At `v1.1` this means exactly three rows, one each for `ENH`, `ENS`, and `ebusd-tcp`, in a fixed order. | Producer: static-array construction in `buildResponderCapabilityProvider`. Consumer: length check. |
| **I2** | `active.transport` MUST appear verbatim as one of `transports[].transport`. | Producer: `active.transport` derived from the same canonical enum literals as the rows. Consumer: membership check. |
| **I3** | `active.scope` MUST equal `transports[x].scope` where `x.transport == active.transport`. | Producer: shared-runtime-downgrade logic rewrites both `active` and the matching row when the runtime transport cannot satisfy `ResponderTransport` (see §9 producer note). |
| **I4** | `scope == none` if and only if the transport does NOT support responder emission at this minor. There MUST NOT be a separate `responder_available` boolean; `scope` is the single source of truth. | Producer: no boolean emitted. Consumer: `scope != "none"` is the only authorisation signal. |
| **I5** | `state == "blocked"` REQUIRES `reason != null` AND `scope == "none"`. | Producer: `ebusd-tcp` row hard-coded; mux-bypass rewrite sets all three fields atomically. |
| **I6** | `state == "supported"` REQUIRES `reason == null` AND `scope != "none"`. | Producer: supported rows carry empty `Reason` which the marshaller emits as JSON `null`. |
| **I7** | Duplicate transport rows in `transports[]` are forbidden. | Producer: static array; tests assert uniqueness. |
| **I8** | Unknown `active.refusal.code` values MUST be treated by consumers as generic capability refusal (fail-closed). Producers MAY emit new codes under a later `contract.minor` bump. | Consumer: §4 rule 6. |

Producer-side proof: the M4c2 producer enforces I1/I7 by constructing
`transports[]` as a fixed three-element slice, enforces I2/I3 by deriving
`active.transport` from the same canonical enum literals the rows use, and
enforces I5/I6 by null-routing the empty-string `Reason` field in
`capabilityToMap` (`responder_capability.go`).

## §4 — Consumer rule (fail-closed, normative)

Consumers MUST gate current-request responder behaviour on the `active`
sub-object only. `transports[]` is profile data and MUST NOT be used to
authorise responder emission on the current request.

The six fail-closed MUST clauses:

1. **Absence of `meta.capabilities.responder`** ⇒ treat as
   `active.scope = none`. No responder invocation attempted.
2. **Absence of `active`** within the key ⇒ treat as `active.scope = none`.
3. **Unknown `active.scope` string** ⇒ treat as `scope = none` (per M4B
   §6.2 open-enum forward-compat rule). No responder invocation
   attempted.
4. `active.scope == "none"` (or a derived `active.available` equivalent
   evaluating false) ⇒ MUST NOT attempt responder invocation. MAY surface
   a UI hint drawn from `transports[]` (transport-switch affordance), but
   this hint is **informational only**.
5. `transports[]` is **informational / profile only**. It MUST NOT enable
   current-request responder behaviour. A `transports[]` entry with
   `scope: "partial"` on a non-active transport is discovery data, not an
   authorisation signal.
6. **Unknown `active.refusal.code` string** ⇒ treat as generic capability
   refusal (fail-closed). The consumer MUST NOT attempt responder
   invocation, MAY log the unknown code for diagnostics, and MUST NOT
   surface it as a success-path signal. Unknown `transports[].state` and
   unknown `transports[].reason` strings degrade to fail-closed per the
   same rule.

These clauses are the load-bearing consumer contract for M5_PORTAL
(vrc-explorer) and M5b_HA_NOOP_COMPAT (ha-integration). Consumer
regression tests MUST cover all six clauses.

## §5 — Enum catalogue at v1.1

Each enum below is **locked-open**: new values MAY be added under a
subsequent `contract.minor` bump per M4B §6.2; existing values MUST NOT be
removed, renamed, or have their semantics changed.

### §5.1 `surfaces`

At `v1.1`, `active.surfaces` and `transports[].surfaces` draw values from
the set:

```
FF_03  FF_04  FF_05  FF_06
```

These are the four FF-prefixed L7 responder-role entries already present
in `helianthus-ebusgateway/internal/execution_policy/whitelist.go` with
`RequestOrResponseRole = RoleResponder` and
`transport_capability_requirements = ["responder"]`. Surface `07_04`
(Identification) is **excluded** from this enum at `v1.1`; adding it
would be an additive minor bump.

### §5.2 `active.refusal.code` / `transports[].reason`

At `v1.1`, the refusal / reason enum contains exactly:

```
command_bridge_no_companion_listen
timing_unavailable
transport_mux_bypass
```

Locked semantics:

- `command_bridge_no_companion_listen` — the transport is architecturally
  a command bridge (ebusd-tcp); no unsolicited responder ingress goroutine
  exists and none can be added without surrendering responder identity to
  a daemon the gateway does not own. Applied to the `ebusd-tcp` row
  permanently.
- `timing_unavailable` — reserved for a future runtime determination that
  a viable transport cannot meet the eBUS target-response window under
  live-bus conditions (M4c1 no-go fallback per M4b2 §7.1.1). No active
  production emission at v1.1.
- `transport_mux_bypass` — emitted at runtime when the canonical protocol
  is `ENH` or `ENS` but the live transport instance does NOT satisfy
  `ebusgoTransport.ResponderTransport` (the adapter-direct mux case
  today). The producer rewrites BOTH the ENH and ENS rows to
  `state=blocked, scope=none, reason=transport_mux_bypass` to preserve
  I3 under the shared-runtime downgrade.

`policy_denied` is **forbidden** as a value of this enum. The reason enum
is scoped to **transport-capability conditions only**; per-request
authorisation failures flow exclusively through `ErrSafetyClassDenied`
with audit `outcome = policy_denied` (see §8). Conflating the two
channels would break audit parity and mislead consumers that treat
blocked reasons as static transport constraints.

Consumers MUST treat unknown code/reason strings as generic capability
refusal (fail-closed, §4 rule 6).

### §5.3 `transports[].state`

At `v1.1`, the `state` enum is locked to exactly four values:

```
supported        # transport viable; scope != none; reason == null (I6)
blocked          # transport architecturally incapable; scope == none; reason REQUIRED (I5)
unknown          # transport enumerated in code but no spike / proof exists; scope == none; reason MAY be null
not_configured   # transport exists in code but not wired at this deployment; scope == none; reason MAY be null
```

No active production emission of `unknown` or `not_configured` at v1.1 —
both are reserved for future transports that enter the enum without a
validated responder spike.

### §5.4 `scope`

At `v1.1`, the `scope` enum is locked to exactly three values:

```
full       # all four FF_03..FF_06 surfaces emissible
partial    # strict subset emissible
none       # no surface emissible (responder unavailable)
```

No active production emission of `full` at v1.1 — M4c1 / M4c2 landed with
`partial` on ENH and ENS. Promotion to `full` is an additive minor event
requiring a fresh golden fixture per M4B §6.2.

## §6 — Version policy

### §6.1 Subtree version orthogonal to envelope minor

`meta.capabilities.responder.version` is a semver string that versions the
**subtree shape** (`{version, active, transports[]}` and all invariants
I1-I8). It is orthogonal to `meta.contract.minor`, which versions the
entire envelope.

At `v1.1` of the envelope the subtree value is the string literal `"v1"`.

### §6.2 v1 additive minor events (subtree stays at `"v1"`)

The following additions ship under a `contract.minor` bump of the
envelope while `responder.version` remains `"v1"`:

- A new transport member (e.g. future `tcp-plain`) — requires a fourth
  `transports[]` row **and** a matching `surfaces[]` population or an
  explicit `blocked`/`unknown` state. Omission-as-unknown is NOT a
  permitted encoding; consumers that encounter a non-enumerated
  `active.transport` fail closed per §4 rule 6.
- A new `reason` or `refusal.code` value (new transport-capability
  condition).
- A new `state` value (e.g. a future `degraded`).
- A new `scope` value (e.g. a hypothetical `deep` beyond `full`).
- A new surface enum member (e.g. `07_04`).

All such additions MUST preserve I1-I8 and the §4 consumer rule. All such
additions MUST ship with updated golden fixtures per §10.

### §6.3 v2 subtree-breaking events (bump `responder.version` to `"v2"`)

The subtree version bumps to `"v2"` only under shape-restructuring
changes, such as:

- Removing or renaming any of `active` / `transports[]` / `version`.
- Narrowing `active.refusal` from nullable object to non-nullable.
- Splitting `scope` across multiple fields.
- Changing any I1-I8 invariant.

A subtree v2 bump is independent of whether the envelope also bumps to
`contract.major = 2`; the two are orthogonal. A subtree v2 on a v1
envelope is permitted provided the envelope-level M4B §6.2 additive
rules hold for the carrying `meta.*` key.

### §6.4 Forward-compat conformance (pointer to M4B §7.3)

The capability-signal forward-compat invariants mandated by M4B
[`11-m4b-semantic-lock.md`](./11-m4b-semantic-lock.md) §7.3 extend to:

- Unknown `active.transport` value.
- Unknown `active.scope` value.
- Unknown `active.refusal.code` value.
- Unknown `transports[].state` value.
- Unknown `transports[].reason` value.
- Missing `meta.capabilities.responder` key entirely.

All of the above MUST parse without error under the canonical consumer
decoder and MUST degrade to fail-closed per §4.

## §7 — Relationship to M4B lock

This chapter is a pure additive v1.minor extension per M4B §6.2 bullet 1
("new `meta.*` keys are permitted under a `contract.minor` bump"). The
M4B envelope shape at §§1.1–1.2 is unchanged:

- `meta.additionalProperties: true` permits the new `capabilities.*`
  subtree (no narrowing of `meta`).
- Top-level `{meta, data, error}` lock (§1.1) is untouched; no new
  top-level key.
- `meta.contract.minor` moves from `0` to `1`; the major remains `1`.
- `meta.data_hash` determinism (§1.4) holds unchanged — the canonical-JSON
  hash covers only `data`, not `meta`; adding a `meta.*` key has no
  effect on the hash contract.
- No `safety_class` enum change (§2), no `error` schema change (§3), no
  `decode` scaffold change (§4), no catalog-version semantics change
  (§5).

Emission of this key was confirmed by gateway merge `547fd4ed`
(helianthus-ebusgateway#509). M4D is therefore a zero-risk doc-gate
follow-up: the wire producer shipped first, and this chapter freezes the
shape it emits.

## §8 — Audit outcome separation

The capability signal participates in a three-channel audit taxonomy that
MUST remain mutually exclusive. Conflation across channels would pollute
compliance reporting and break denial-parity tests.

| Outcome code | Channel | Trigger |
|---|---|---|
| `responded` | Successful emission | A responder-role inbound telegram was matched by policy AND the active transport satisfied `ResponderTransport` AND the eBUS ACK/response/final-ACK FSM completed in window. |
| `suppressed_by_capability` | Capability refusal | The capability layer refused emission because `active.scope == none` or the surface was not in `active.surfaces[]`. Maps 1:1 to the `active.refusal` object surfaced to consumers. |
| `policy_denied` | Policy denial | `execution_policy.Check` returned `ErrSafetyClassDenied` for the inbound tuple. Carries dynamic audit context (caller, matched row, tuple). |

Enforcement clauses:

- `ErrResponderTransportUnavailable` (construction-time sentinel) and its
  derived audit outcome `suppressed_by_capability` MUST NOT appear in
  audit records with `outcome = policy_denied`.
- `ErrSafetyClassDenied` MUST NOT be routed to
  `active.refusal` or to `transports[].reason`. Per-request authorisation
  failures never surface through the capability signal.
- `policy_denied` is **forbidden** as a `transports[].reason` value per
  §5.2.

## §9 — Producer reference (authoritative)

The authoritative producer implementation as of gateway `547fd4ed` is:

- `helianthus-ebusgateway/mcp/ebus_standard/responder_capability.go` —
  types (`ResponderCapability`, `ActiveResponder`, `ActiveRefusal`,
  `TransportRow`), provider pattern (`SetResponderCapabilityProvider`,
  package-level `atomic.Pointer`), and JSON-shape marshaller
  (`capabilityToMap`, including the empty-string-to-`null` convention for
  `reason` on supported rows).
- `helianthus-ebusgateway/mcp/ebus_standard/envelope.go` — envelope
  composer, `EnvelopeContractMinor = 1`, and emission site (nil-provider
  key omission).
- `helianthus-ebusgateway/cmd/gateway/main.go::buildResponderCapabilityProvider`
  — bootstrap-time provider factory. Maps canonical transport
  (`TransportENH` / `TransportENS` / `TransportEbusdTCP`) to the
  `active` object; performs the runtime-transport type assertion against
  `ebusgoTransport.ResponderTransport` and applies the shared-runtime
  mux-bypass downgrade (rewriting both ENH and ENS rows to
  `state=blocked, scope=none, reason=transport_mux_bypass`) when the
  live transport instance does not satisfy the interface. Returns `nil`
  for non-enumerated transports so the envelope omits the key entirely
  (§4 rule 1 fall-through).

The code is truth. Any drift between this chapter and the producer at a
later gateway commit MUST be reconciled by amending this chapter under
the §6 version policy; the producer implementation MUST NOT be mutated
to match stale prose without a corresponding plan-amendment decision.

## §10 — Conformance tests (pointer)

The following gateway-side tests are normative for this chapter and MUST
exist continuously:

1. **Unit coverage of provider semantics** —
   `helianthus-ebusgateway/mcp/ebus_standard/responder_capability_test.go`
   (type marshalling, nil-provider absence, empty-string-to-`null` for
   supported-row reason).
2. **Bootstrap wiring & mux-bypass behaviour** —
   `helianthus-ebusgateway/cmd/gateway/wiring_test.go` (canonical enum
   mapping, adapter-direct mux downgrade, ebusd alias canonicalisation,
   nil-return on non-enumerated transport).
3. **Forward-compat synthetic payload** —
   `helianthus-ebusgateway/mcp/ebus_standard/forward_compat_test.go`
   using
   `helianthus-ebusgateway/mcp/ebus_standard/testdata/forward_compat_synthetic_v1_1.golden.json`.
   This fixture carries an unknown `active.transport`, unknown
   `active.scope`, unknown `state`, and unknown `reason` simultaneously
   and MUST parse under the canonical consumer decoder with every
   unknown preserved.
4. **Envelope golden fixtures** — the four M4B surface goldens
   (`testdata/services_list.golden.json`,
   `testdata/commands_list_pb03.golden.json`,
   `testdata/command_get_alpha.golden.json`,
   `testdata/decode_alpha.golden.json`) MUST include
   `meta.capabilities.responder` at their minor-1 generation.

M4B §7.3 (forward-compat conformance golden) is the parent obligation;
this chapter adds the responder-subtree-specific coverage.

## §11 — Supersedes

This chapter supersedes, for wire-contract purposes only, the
forward-specification framing of:

- `helianthus-execution-plans/ebus-standard-l7-services-w16-26.implementing/decisions/m4b2-responder-go-no-go.md`
  §4.1 (Location), §4.2 (Shape), §4.3 (Consumer rule), §4.4 (Invariants).

The M4b2 decision doc remains authoritative for:

- §1 (Verdict) and §2 (Rationale).
- §3 (Per-transport scope matrix).
- §5 (Policy-module integration and sentinel separation).
- §6 (Stage gating: M4c1, M4c2, M4D, M5, M5b).
- §7 (No-go fallback conditions).
- §8 (Residual risks).
- §9 (Decision process audit).
- §4.5 (v1.minor additive justification — informative since this
  chapter ratifies the claim).

## §12 — Sign-off

- Decision process: ratification of M4c2 wire emission shipped by
  helianthus-ebusgateway#509 (squash `547fd4ed`), landing the shape that
  the M4b2 cruise-consult dual-vendor pair (Claude + Codex, 2 rounds,
  joint verdict `option_go_transport_scoped`) specified as forward
  target.
- Evidence: gateway commit `547fd4ed` + producer test suite + M4B
  semantic-lock predecessor (commit `91bcb34c`, helianthus-docs-ebus#273).
- Supersedes: M4b2 decision doc §4 forward-spec framing (shape +
  invariants only — see §11).
- Amendment policy: any change violating §§1–5 or §8 invariants, or
  narrowing any of the locked-open enums, requires a new locked-plan
  amendment per the Helianthus execution-plan protocol. Additive enum
  expansions ship under `contract.minor` bumps per §6.2.
