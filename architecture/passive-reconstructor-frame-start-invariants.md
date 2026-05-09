# Passive Reconstructor Frame-Start Invariants (P6)

This page documents the two invariants the passive transaction reconstructor enforces before it accepts a non-`SymbolSyn` byte as a new frame's source byte. Both invariants must hold; together they cover the two failure modes observed live on cruise-control deployments and provide complementary operator canaries for upstream byte-loss diagnosis.

The invariants are implemented in `helianthus-ebusgateway/passive_transaction_reconstructor.go` (Project-Helianthus/helianthus-ebusgateway PR #585) and surface through the Prometheus exporter and the MCP/GraphQL `BusReconstructorAggregate`.

## Invariants

### Layer 1 — Inter-frame SYN gate

A non-`SymbolSyn` byte is only eligible to start a frame if at least one `SymbolSyn` was observed since the previous frame boundary. Frame boundaries include classified commits, abandons, transport discontinuities (connect, reset, decode fault, disconnect), and process startup.

The reconstructor maintains a `synced` flag. Every reset (transport-driven or default-case fallthrough) clears it; every observed `SymbolSyn` re-engages it. While `synced == false` and the parser sits in `passivePhaseIdle`, non-SYN bytes are dropped silently and counted in `ebus_passive_reconstructor_prefix_resync_skipped_total`.

This matches the eBUS bus-idle marker requirement between frames (ref: 12-address-table.md frame structure, Spec_Prot_7 §4 "frame timing"). It catches:

- Process startup before a SYN has been observed.
- Continuation bytes from a previous frame leaking into the new-frame source position via upstream overflow drops or transport ownership-handover races.

### Layer 2 — Source AddressClass validation

After Layer 1 admits a byte as eligible (i.e. `synced == true`), the reconstructor validates that `protocol.AddressClassOf(symbol) == AddressClassMaster` (initiator-class — the 25 canonical initiator addresses per AD05 / Phase C / `sourceAddressTableV1`).

Bytes whose `AddressClass` is `Slave`, `Broadcast`, or `Reserved` indicate either:

- a corrupt-state window the reconstructor cannot recover from blindly, OR
- the upstream loss of the actual SRC byte — the operator-confirmed Mode B signature. Live evidence: 25+ `[SYN] [TGT] [PB=0xB5] [SB] [data]` events per 5000-line log window where the actual source (e.g. `0x10 BASV2 initiator`, `0xF1 NETX3 initiator`) was eaten upstream by the ENH transport's `StreamEventStarted{Data: <src>}` capture-as-control-event drop in the gateway adapter mux (or the analogous proxy drop at `helianthus-ebus-adapter-proxy/internal/adapterproxy/server.go:1841-1847`).

On rejection the reconstructor:

- Increments `ebus_passive_reconstructor_invalid_src_class_skipped_total` once.
- Sets `synced = false` and `awaitingResync = true` to drop the trailing PB/SB/data/CRC bytes silently — `awaitingResync` suppresses Layer 1's cascade counter so `prefix_resync_skipped_total` does NOT inflate by the rest of the corrupt frame body.
- Resumes accepting on the next observed `SymbolSyn`, which clears both flags and re-arms the gate for the next frame.

## Counter semantics — operator interpretation

| Counter | Meaning | Healthy steady-state |
| --- | --- | --- |
| `ebus_passive_reconstructor_prefix_resync_skipped_total` | Bytes dropped because no SYN was observed since the previous frame boundary (Layer 1). | Brief startup spike (~10–100 events), then plateau near zero. |
| `ebus_passive_reconstructor_invalid_src_class_skipped_total` | Bytes rejected as non-initiator-class in source position (Layer 2). Direct measure of upstream byte loss frequency. | Zero on a clean bus where the upstream pipeline preserves the SRC byte. Sustained non-zero rate is operator signal that the upstream transport (or proxy) is dropping the arbitration-grant byte for third-party transactions. |

Both counters together distinguish:

- **"Fix is masking a problem"** — one or both > expected.
- **"Bus is clean"** — both at floor (Layer 1 plateau ≤5/min, Layer 2 at zero).

Sustained `invalid_src_class_skipped_total` ≥10/min after warmup is the trigger to revisit the deferred upstream fixes:

- **P6.1** — replay `StreamEventStarted.Data` as a synthetic `StreamEventByte` in `helianthus-ebusgo/transport/enh_transport.go` so the reconstructor sees the full `[SYN] [SRC] [DST] [PB] [SB] …` sequence on third-party transactions.
- **P6.2** — fan-out `ENHResStarted.Payload[0]` as a synthetic `ENHResReceived` to non-owner sessions in the proxy when no `pendingStart` matches.

Both follow-ups are deferred behind P6 because Layer 1 + Layer 2 normalize observable behavior at the reconstructor regardless of which upstream component dropped the SRC byte; the counters quantify the cost-of-deferral.
