# Execution Safety Policy

Status: Normative
Plan reference: ebus-standard-l7-services-w16-26.locked/00-canonical.md
Canonical SHA-256: 9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305

## Safety Classes

Every catalog method declares exactly one `safety_class`:

- `read_only_safe`
- `read_only_bus_load`
- `mutating`
- `destructive`
- `broadcast`
- `memory_write`

`read_only_safe` is reserved for non-originating or responder-local
methods that do not cause a user-facing live bus transaction.
`read_only_bus_load` is read-only but originates live bus traffic when
invoked.

## Default-Deny Policy

The locked plan states:

> `rpc.invoke` accepts `read_only_safe` and `read_only_bus_load`.
> `rpc.invoke` default-denies `mutating`, `destructive`, `broadcast`,
> `memory_write`.
> Default-deny applies to any user-facing caller and to every internal
> caller EXCEPT a single named caller context
> `caller_context=system_nm_runtime` that carries a compile-time
> whitelist.

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.locked/00-canonical.md`, SHA-256
`9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

For user-facing `rpc.invoke`, safety-class acceptance is necessary but
not sufficient. The catalog identity must also be a user-requestable
request variant. Response-role and responder-emit variants are not
user-requestable merely because they are read-only.

## Single Policy Function

The locked plan states:

> One shared execution-policy module is consulted by `rpc.invoke`,
> generated provider methods, and the NM runtime.
> All three call the same policy function with the caller context.
> Tests prove denial parity: direct provider invocation and MCP
> `rpc.invoke` deny identical sets by default; the `system_nm_runtime`
> whitelist is honoured only from the NM runtime call site.

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.locked/00-canonical.md`, SHA-256
`9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

## system_nm_runtime Whitelist

The locked plan states:

> The `system_nm_runtime` whitelist is keyed by the full catalog identity
> tuple (see §3). The whitelist in first delivery is exactly:
>
> - `0xFF 00` broadcast (NM reset status on join/reset)
> - `0xFF 02` broadcast (NM failure signal)
> - `0xFF 03` responder (net status)
> - `0xFF 04` responder (monitored participants)
> - `0xFF 05` responder (failed nodes)
> - `0xFF 06` responder (required services)
> - `0x07 FF` broadcast (sign of life, cadence-floor gated)

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.locked/00-canonical.md`, SHA-256
`9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

The whitelist entries below are exact variants. Matching by PB/SB alone
is forbidden.

| namespace | PB | SB | selector_path | telegram_class | direction | request_or_response_role | broadcast_or_addressed | answer_policy | length_prefix_mode | selector_decoder | service_variant | transport_capability_requirements | version |
|---|---:|---:|---|---|---|---|---|---|---|---|---|---|---|
| `ebus_standard` | `0xFF` | `0x00` | `null` | `broadcast` | `request` | `initiator_broadcast_emit` | `broadcast` | `no-answer` | `NN=0x00` | `none` | `nm_reset_status_broadcast` | `initiator+broadcast` | `v1.0-locked` |
| `ebus_standard` | `0xFF` | `0x02` | `null` | `broadcast` | `request` | `initiator_broadcast_emit` | `broadcast` | `no-answer` | `NN=0x00` | `none` | `nm_failure_broadcast` | `initiator+broadcast` | `v1.0-locked` |
| `ebus_standard` | `0xFF` | `0x03` | `null` | `initiator-target` | `response` | `responder_reply` | `addressed` | `answer-required` | `response_NN=0x01` | `none` | `nm_net_status_response` | `responder_companion_required` | `v1.0-locked` |
| `ebus_standard` | `0xFF` | `0x04` | `request.block_number` | `initiator-target` | `response` | `responder_reply` | `addressed` | `answer-required` | `response_NN=0x01..0x0A` | `nm_block_number` | `nm_monitored_participants_response` | `responder_companion_required` | `v1.0-locked` |
| `ebus_standard` | `0xFF` | `0x05` | `request.block_number` | `initiator-target` | `response` | `responder_reply` | `addressed` | `answer-required` | `response_NN=0x01..0x0A` | `nm_block_number` | `nm_failed_nodes_response` | `responder_companion_required` | `v1.0-locked` |
| `ebus_standard` | `0xFF` | `0x06` | `request.block_number` | `initiator-target` | `response` | `responder_reply` | `addressed` | `answer-required` | `response_NN=0x01..0x0A` | `nm_block_number` | `nm_required_services_response` | `responder_companion_required` | `v1.0-locked` |
| `ebus_standard` | `0x07` | `0xFF` | `null` | `broadcast` | `request` | `initiator_broadcast_emit` | `broadcast` | `no-answer` | `NN=0x00` | `none` | `sign_of_life_broadcast` | `initiator+broadcast+cadence_floor_10s` | `v1.0-locked` |

Adjacent variants with the same PB/SB remain denied unless their full
14-axis identity appears in this table. Examples:

1. `0xFF 03` request is not the whitelisted `0xFF 03` responder reply.
2. `0xFF 04` request is not the whitelisted `0xFF 04` responder reply.
3. `0x07 FE` broadcast inquiry is not the whitelisted `0x07 FF`
   sign-of-life broadcast.
4. `0xFF 01` reset target configuration is not whitelisted.

## Audit Requirement

The locked plan states:

> Audit: every allowed invocation in `system_nm_runtime` is logged with
> catalog identity, caller, timestamp, and outcome.

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.locked/00-canonical.md`, SHA-256
`9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

The structured audit log record MUST include at least:

- full catalog identity tuple
- caller context
- concrete runtime caller name
- local address-pair provenance when applicable
- timestamp
- decision (`allowed` or `denied`)
- outcome (`sent`, `responded`, `suppressed`, `transport_error`,
  `policy_denied`, or equivalent structured code)
- error details when outcome is not successful

## No Runtime Widening

The locked plan states:

> Widening the whitelist, adding caller contexts, or exposing
> mutating/destructive/broadcast/memory-write surfaces via GraphQL is a
> new locked-plan decision, not a code change.

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.locked/00-canonical.md`, SHA-256
`9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

The first-delivery whitelist is a compile-time constant. Configuration,
operator commands, feature flags, environment variables, registry
records, and portal state MUST NOT widen it at runtime.
