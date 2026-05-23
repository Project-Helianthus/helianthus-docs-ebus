# First-Byte Arbitration Revalidation (F-NEW-29)

Status: Accepted for M4 live verification of
`fix-p11-midwrite-byte-routing-w21-26.locked`

This page documents the doc-gate contract for the F-NEW-29 adaptermux change:
first-byte arbitration revalidation with forward-not-drop behavior for the
first foreign initiator-class byte observed during a gateway-owned write.

## Locked Direction

Direction C is the only accepted direction for this milestone.

When the gateway is in an active transaction and sees a mid-write byte that does
not match the pending echo, the mux must distinguish the first byte of a
foreign arbitration loss from ordinary echo mismatch handling. If that byte is
an initiator-class address and it is the first post-write mismatch, the mux
forwards it through the active non-SYN delivery path instead of dropping it as
passive foreign traffic.

The implementation must not change `bus.Send` architecture, must not move to a
different arbitration model, and must not reopen `post_grant_ack` as a normal
delivery path.

## F-NEW-29 Predicate

The active Hoare predicate for the fix is:

```text
PRE:
  gatewayTxnActive
  hadPendingEcho
  matchCount == 0
  writeCount == 1
  symbol != preMatchHead
  AddressClassOf(symbol) == initiator-class

ACTION:
  route symbol through mux non-SYN delivery path

POST:
  activeCh receives symbol
  firstByteSuspectArbLoss == true
  bus.go first-byte classifier can raise ErrBusCollision
  sendWithRetries can retry
```

This is intentionally narrow. It only converts the first foreign
initiator-class byte after a one-byte write into active delivery so the bus
layer can classify first-byte arbitration loss and retry. It is not a general
mid-write mismatch relaxation.

## P11 Preservation

For all other mid-write mismatches, P11 remains in force: active delivery is
gated on `symbol == preMatchHead`.

Examples that stay gated:

- mismatches after more than one written byte
- mismatches after any echo match has already occurred
- non-initiator-class symbols
- symbols that are not the first foreign byte in the suspect window
- any path that would require `post_grant_ack` delivery

These cases continue to close through the established active transaction
outcomes such as `ErrEchoMismatch`, `ErrBusCollision`, timeout with diagnostic,
adapter host error, transport error, or context cancellation.

## M4 Live Proof Gates

The M4 proof must establish all of the following on the deployed add-on build:

| Gate | Requirement |
| --- | --- |
| O1 | Within 60 seconds of add-on startup, all 12 MCP semantic planes return non-null data: zones, circuits, dhw, radio_devices, fm5_mode, solar, cylinders, schedules, energy_totals, system, adapter_info, boiler_status. |
| O2 | `semantic_b524_root_discovery address=0x15` appears within 60 seconds of `RequestStart(0x7F)`, with the verification script allowed 90 seconds of polling grace. |
| O3 | Over the 90-minute stress window, `helianthus_round9_absorb_entered_total` has zero delta. |
| O4 | `post_grant_ack` is at most 15 over 90 minutes, equivalent to the 10/hour absolute cap. |
| O5 | Active request collision rate is at most 825/hour. |
| T/PX | T01..T88 and PX01..PX12 have no unexpected fail or xpass, except for owner-recorded `adapter_no_signal` infrastructure blockage. |

The proof must also close the active, passive, and cross-session classification
predicates:

- P-Active: every `bus.Send` active transaction in the window closes into one
  allowed outcome.
- P-Passive: every upstream wire event is classified once, with unexpected
  residual zero and scrape-skew residual explained if present.
- P-Cross: each session has exactly one role for a given upstream symbol,
  concurrent active owners never exceed one, and grant start/terminate counters
  balance with in-flight grants.

If exact counters are missing, P-Cross may be reconstructed from adaptermux
`activeTxn` lifecycle logs. Missing counters do not weaken the invariant.

## Mode B Follow-Up

The Mode B signature, where writes remain at 11 and echo-like events remain at
8, is explicitly out of scope for this fix unless O1-O5 fail. Mode B concerns
upstream source-byte loss in passive observation and is tracked by the passive
reconstructor invariants. F-NEW-29 only proves the first-byte arbitration
revalidation path needed for retryable active collisions.

## Success Rule

Success cannot be declared from a short quiet window. O1/O2 are startup gates,
but the invariant proof requires the full M4 stress evidence, including the
90-minute counter window and fresh proof-target review.
