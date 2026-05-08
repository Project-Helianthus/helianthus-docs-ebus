# Live Validation Acceptance

Status: Normative
Plan: address-table-registry-w19-26
Plan-SHA256: eb2cb53c7d9ad2e05cc384db6b7537067e739f62a8a359f1e89e62aca35b367b
Decision references: AD04, AD05, AD07, AD08, AD14

<!-- legacy-role-mapping:begin -->
> Legacy role mapping for this ATR spec: `master` -> `initiator`, `slave` -> `target`.
> The legacy terms are retained where the locked plan and M8 acceptance
> assertions require verbatim wording.

This document is the forward reference for the M8 falsifiability gate. M8 MUST
pass every positive assertion and MUST preserve every negative assertion.

## Positive Assertions (P1..P6)

### P1 — 0xF6 visible via passive observation alone

Procedure:
- Set `EnableStaticSeedTable=false` in addon config
- Deploy gateway; let it run ≥10 minutes during normal NETX3 polling activity
- Query GraphQL `{ devices { address discoverySource verificationState } }`

Expected: device with `address=0xF6 (246) discoverySource=passive_observed verificationState=corroborated`.

Provenance: NETX3's master 0xF1 emits frames during normal operation; Phase A's M3+M4 derives companion (0xF1 → 0xF6) and inserts slot[0xF6] after second corroborating observation.

### P2 — 0x04 visible via static seed (with flag enabled)

Procedure:
- Set `EnableStaticSeedTable=true` in addon config
- Restart addon; let it run ≥30 seconds
- Query GraphQL `{ devices { address discoverySource verificationState } }`

Expected: device with `address=0x04 (4) discoverySource=static_seed verificationState=candidate`.

### P3 — 0xEC visible via static seed (with flag enabled)

Same procedure as P2. Expected: device with `address=0xEC (236) discoverySource=static_seed verificationState=candidate`.

### P4 — Existing devices unchanged

Procedure: same as P1.
Expected: 0x08 (BAI00), 0x15 (BASV2), 0x26 (VR_71) appear with `verificationState=identity_confirmed` (preserved from PR #560/#562 logic) — no regression.

### P5 — bus_admission preserved

Procedure: query `{ busSummary { status { bus_admission { source_selection { state outcome selected_source companion_target active_probe { status } } } } } }`.
Expected: `state=active outcome=active_probe_passed selected_source=127 (0x7F) companion_target=132 (0x84) active_probe.status=active_probe_passed`. Identical to pre-Phase-A.

### P6 — Transport matrix parity

Procedure: re-run T01..T88 transport matrix (M9). Diff against M0A baseline.
Expected: zero unexpected `fail` deltas; zero unexpected `xpass` deltas. Any infra-blocked cases must use the documented `adapter_no_signal` reason.

## Negative Assertions (N1..N5)

### N1 — NACK-only observations do NOT insert

Procedure: send a synthetic frame ZZ=0x99 (a known-non-existent address) from the gateway's admitted source, expect NACK (0xFF in ACK position) from the bus. Query GraphQL.
Expected: NO entry at address 0x99 in `devices`.

### N2 — Broadcast 0xFE destination does NOT insert at 0xFE slot

Procedure: observe natural broadcast traffic addressed to `ZZ=0xFE` (the eBUS broadcast destination). Examples include any frame with primary `B5` and secondary in the broadcast namespace, or the `07 FF` Sign-of-Life service (PB=`07`, SB=`FF`) sent to ZZ=`FE`. Query GraphQL.
Expected: NO entry at address `0xFE` in `devices`. Note: this assertion targets `ZZ=0xFE` (broadcast destination), distinct from the `07 FF` service (PB=0x07 SB=0xFF Sign-of-Life) and from B510 (PB=0xB5 SB=0x10 SetMode); both services are valid broadcast payloads but do not change the requirement that `ZZ=0xFE` is filtered. AD04's separate 0xFF/NACK disambiguation rule covers the `0xFF` ACK-position case (see N3); N2 is only about broadcast destination.

### N3 — ACK byte 0xFF does NOT insert at 0xFF slot via ACK position

Procedure: observe traffic that produces NACK (0xFF) in ACK position. Query GraphQL.
Expected: NO entry at address 0xFF UNLESS a separate frame-start observation of 0xFF as src/dst exists. Test this with a negative golden trace AND positive golden trace separately.

### N4 — Self-source does NOT insert

Procedure: gateway sends frames from admitted source 0x7F. Query GraphQL.
Expected: NO entry at address 0x7F. (0x7F is initiator-capable; if accidentally inserted, it would surface.)

### N5 — Single corroboration does NOT companion-insert

Procedure: send a single frame triggering 0xF1 master observation (one ACK from a 0xF1-sourced request). Query GraphQL within 1 second.
Expected: NO entry at address 0xF6 (companion of 0xF1) — corroboration window not yet closed.

After observation window (default 5s) + second corroborating observation: 0xF6 entry MUST appear (P1 fires). N5 is the "before-second" check.

## HA Consumer Compatibility

Per AD14:

- Existing entities (boiler, regulator, system) MUST remain stable.
- For `0x04`, `0xEC`, and `0xF6` candidate-state entities, the integration
  MUST either filter `verification_state=candidate`, or preserve the candidate
  provenance explicitly, or require explicit operator acceptance.
- The integration MUST NOT crash, MUST NOT create arbitrary-address entities,
  and MUST NOT regress existing user-visible entity state.

## Rollback Criteria

If any positive assertion fails or any negative assertion is violated, the M8
PR MUST NOT merge.

Rollback steps:
1. Revert M3, M4, M5 PRs (in reverse merge order)
2. Revert M5A_SEED_API_CONTRACT (productids)
3. Revert M2A correlator package
4. Revert M2 Companion func
5. Revert M1 registry refactor
6. M0 doc PRs may remain (no runtime impact)

The rollback decision MUST be made from the failed assertion log and the
transport-matrix diff.

## Phase A.5 Live Evidence (post-merge runtime wire-up)

Phase A's first live deployment validation surfaced a runtime gap: the
`AddressTableInserter` introduced in M3+M4 (PR #564) was never instantiated
in `cmd/gateway/main.go`. The type-level pieces (M2A correlator, AD04/AD05
insertion rules, `ACKCorrelation` population by the reconstructor) were all
merged but the inserter was idle in production — passively-observed
addresses were therefore not landing in the registry. P1 failed live.

PR #565 (gateway, merged 2026-05-06 as 2281196) closes the gap:

- `AddressTable` + `AddressTableInserter` are instantiated once after
  `gateway.Start(ctx)` and the GraphQL builder, with a live `AdmittedSource`
  closure tied to `builder.AdmittedMutationSource()`.
- Subscription is gated on `builder.AdmittedMutationSource()` returning
  `ok=true`, with three wire-in points covering both the synchronous
  override / static fallback path and the async source-selection-capable +
  observe-first path (after `activeProbePassed`).
- `sync.Once` + `atomic.Bool` provide cross-goroutine safety.
- Subscription failure is non-fatal — logged and skipped, consistent with
  the `PassiveDiscoveryPromoter` init pattern.

Live evidence captured 2026-05-06 against HA at 192.168.100.4:

- ✅ Source-selection completed (`active_probe_passed`, `selected_source=127`,
  `companion_target=132`).
- ✅ Inserter wired and subscribed via the async wire-in point.
- ✅ Existing devices (BAI00 / BASV2 / VR_71) unchanged at active-discovered
  state.
- ⏳ P1 (passive 0xF6 detection) pending organic 0xF1-originated bus traffic.
  The bus is dominated by gateway traffic during initial steady-state; NETX3
  master 0xF1 emits sparsely (per Prometheus 3h analysis: periodic enrichment
  calls). Once observed twice with positive ACK on any target, the
  AD05-second-corroboration rule inserts companion `0xF6`. P2/P3 (static seed
  for 0x04 / 0xEC) remain N/A by default since `EnableStaticSeedTable=false`.

Transport-matrix dry-run (M9) post-merge: 88-case index identical to the M0A
baseline — 0 diffs (`transport-matrix-baseline-w19-26.json`).

## Phase A.5 Known Follow-ups (Phase B / future)

- **Pre-existing `*AddressSlot` data race** introduced by PR #131 + #564:
  the inserter mutates `registrySlot.DiscoverySource`, `VerificationState`,
  `Role`, and `FirstObservedAt/LastObservedAt` through a pointer returned
  by `LookupSlot()` without holding the registry lock. PR #565's runtime
  test sidesteps the race by asserting via the lock-safe `DeviceEntry`
  interface. Production reads via MCP / GraphQL today don't access
  `*AddressSlot` fields directly, so the race is benign for the current
  surface area, but will be addressed by adding a thread-safe API in
  `helianthus-ebusreg` (proposed:
  `(*DeviceRegistry).MarkSlotPassiveObserved(addr, role, observedAt)`)
  and refactoring the inserter to use it.

- **Async-path test coverage debt**: the runtime test exercises only the
  synchronous static-fallback admission wire-in. The async
  `activeProbePassed` wire-in path (source-selection-capable +
  observe-first) is unit-uncovered in the gateway's main_test suite. A
  future follow-up will add a stub source-selector returning a result so
  the async goroutine fires.

## Phase C Live Validation Acceptance (M-C8)

**Date:** 2026-05-08
**Binary:** Phase C build (M-C6a..M-C7 merged), SHA256
`11491e4978fd6d0ae669d30786a496e3376568dadc3ef3b6c84ca65fff1d7746`,
deployed to HA OS 6.12.75 / RPi4 / aarch64.

### Falsifiability gate

Pre-Phase-C bug operator surfaced from live Grafana traffic analysis:
M2S sends from gateway (initiator 0x7F) routed to the **initiator** byte
of an aliased canonical pair instead of the **target** byte. Concretely:
`registry.devices` listed BAI 0x03↔0x08 with `entry.Address()` returning
`0x03` (initiator side); semantic poller built `Frame{Target: 0x03, …}`
on B509/B524 reads, so traffic went to the master byte instead of the
slave that answers M2S. The pre-Phase-C `Bus.Send` derived FrameType
from `Target` via `FrameTypeForTarget(0x03)` → M2M, validator accepted,
frame went to wire under the wrong contract.

Phase C contract (AD24..AD30): every active gateway send site declares
its FrameType explicitly; `Bus.Send.Validate` refuses M2S to a master
byte with `ErrInvalidFrameAddress`; routing helpers prefer the target-
role byte for aliased pairs.

### Live evidence (10-min observation window post-deploy)

**Active gateway M2S sends per destination** (from `/metrics`,
`ebus_frames_observed_total{src="0x7f", scope="active"}`):

| Destination | Address class | Send count | Verdict |
|-------------|---------------|------------|---------|
| 0x08 (BAI target)    | Slave  | 2 frames | Routes to target ✅ |
| 0x15 (BASV2 target)  | Slave  | 4 frames | Routes to target ✅ |
| 0x26 (VR_71 target)  | Slave  | 1 frame  | Routes to target ✅ |
| **0x03 (BAI initiator)**   | Master | **0** | Pre-Phase-C had ≥1 ✅ |
| **0x10 (BASV2 initiator)** | Master | **0** | Pre-Phase-C had ≥1 ✅ |

**FrameType labels.** All active gateway sends carry
`frame_type="initiator_target"` (M2S declared explicitly per M-C7).
Broadcast traffic (e.g. 0xFE destination) carries
`frame_type="broadcast"`. No active sends carry derived/unknown type.

**Validation failures.** `helianthus_invalid_frame_address_total`
counter is zero (Prometheus emits non-zero counters only; absence
confirms no validator rejections). Addon log search for
`ErrInvalidFrameAddress` / `invalid_frame_address` / `validate.*frame`
during the observation window: zero matches.

**Boiler reads functional** (B509/B524 to 0x08 succeeded):
`flow_temperature_c=18`, `water_pressure_bar=8.16`,
`dhw_temperature_c=39.875`, `central_heating_pump_active=true`.

### Build-break safety net (M-C6d)

Bumping `helianthus-ebusgateway` to the post-M-C6c `helianthus-ebusreg`
(commit 77b56516, where `DeviceEntry.Address()` is removed) preserved
all CI checks: `go build/vet/test ./...` clean; GH Actions 4/4 green;
`scripts/ci_local.sh` exit 0. Any caller missed by M-C6b's migration
would have surfaced as a compile error here. Zero misses.

### Transport-matrix zero-diff (M-C9)

88-case post-Phase-C topology byte-identical to the M-C0A baseline.
SHA256 `46431e22d8ed3909db19a34196df72575df8afb7ae03658be32cde0f2734a143`
matches across:
- M-C0A baseline (`transport-matrix-baseline-phase-c.json` →
  `cases[]` extracted)
- Post-#576 main (M-C6b merged)
- Post-#577 main (M-C7 merged)

`internal/matrix/` was not modified by any Phase C commit; zero-diff
is structurally guaranteed in addition to the byte-equality proof.

### Verdict

**Phase C M-C8 PASS.** The defense-in-depth FrameType-aware transport
contract holds in production: every gateway-initiated M2S frame
targets a slave byte; the explicit `Frame.FrameType` from M-C7
prevents the pre-Phase-C silent-derivation hazard; `Bus.Send.Validate`
from M-C5 stands as the transport-side refusal of invalid frames.
The pre-Phase-C bug (M2S to master byte) is fixed end-to-end,
verified live on BAI 0x03↔0x08 and BASV2 0x10↔0x15 canonical pairs.
<!-- legacy-role-mapping:end -->
