# ENH/ENS Shared Conformance Test Catalog

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` -> `initiator`, `slave` -> `target`. Helianthus documentation uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

This document defines canonical cross-repo (XR) conformance test names for ENH and ENS transport behavior. Each test name is a contract: any implementation claiming ENH/ENS conformance MUST pass these tests or document an explicit deviation.

These tests are the **doc-gate** for aligning proxy PR #101, adaptermux PR #502, ebusgo PRs #131-134, and VRC Explorer PRs #245-250/follow-up.

## Scope: ENH/ENS in This Document

In this document and its referenced invariants, `ENH` and `ENS` refer to the **ebusd transport prefixes** (`enh:` on TCP, `ens:` as a serial-baud alias equivalent to `enh:` on network transports). This is NOT the firmware data-only ENS codec (`codec_ens.c`) described in [ens.md §Disambiguation](ens.md#disambiguation). Conformance tests in this catalog apply to the transport protocol, not to the firmware codec layer.

## Timeout Glossary

The invariants below reference several distinct timeouts. All implementations MUST map their internal clocks to these canonical names:

| Symbol | Definition | Start | Stop | Default |
|--------|-----------|-------|------|---------|
| `T_init` | **INIT timeout** | `INIT` request sent | `RESETTED` received OR timeout | 500 ms |
| `T_read` | **Read timeout** (per-frame) | First byte of a frame received | Frame complete OR timeout | 200 ms |
| `T_request` | **Request timeout** (end-to-end) | Host issues request | Final response OR error OR timeout | 2000 ms |
| `T_reconnect` | **Reconnect deadline** | Reconnect initiated | Connection re-established OR timeout | 5000 ms |
| `T_inactivity` | **Inactivity timeout** (idle lease) | Last SYN observed | Next SYN OR lease expiry | 5000 ms |

XR rows below reference these symbols explicitly. Implementations MAY expose these as configurable, but MUST NOT silently extend them on incidental traffic.

## INIT and Connection Lifecycle

### XR_INIT_TimeoutFailOpen_Bounded

**Invariant:** If RESETTED is not received within the INIT timeout, the connection proceeds with `init_confirmed=false` and `features=unknown`. The host MUST NOT hang or assume optional features. Fail-closed (abort) is permitted only for explicit adapter errors or transport hard failures.

**Falsifiable:** Mock adapter that never sends RESETTED. Host must complete INIT within timeout and report `init_confirmed=false`.

### XR_UpstreamLoss_GracefulShutdown_NoHang

**Invariant:** If the upstream transport (TCP connection to adapter) is lost during an active session, the host shuts down gracefully within a bounded deadline. No goroutine/thread hangs indefinitely.

**Falsifiable:** Close the TCP connection mid-transaction. All pending operations must return errors within 2x the configured timeout.

### XR_START_ReconnectWait_BoundedDeadline

**Invariant:** If a reconnect is triggered during or after START/arbitration, the reconnect attempt is bounded by a configurable deadline. The host does not retry indefinitely.

**Falsifiable:** Mock adapter that accepts TCP but never responds to INIT. Reconnect must fail within the configured deadline.

## ENH Command Handling

### XR_ENH_UnknownCommand_ExplicitError_AdapterToHost

**Invariant:** An encoded ENH response with an undefined command nibble (carried in `byte1` bits 5..2; defined response nibbles are 0x0-0x3, 0xA-0xC) is reported by the host as an explicit protocol error, not as a timeout or collision.

**Falsifiable:** Inject `0xD0 0x80` (byte1=`11_0100_00`, byte2=`10_000000`, command nibble 0x4, data=0x00) into the adapter→host stream. Host MUST emit a transport error (e.g., `ErrUnknownENHCommand`), not a timeout.

### XR_ENH_UnknownCommand_ExplicitError_HostToAdapter

**Invariant:** An encoded ENH request with an undefined command nibble (defined request nibbles are 0x0-0x3) MUST be rejected by the adapter with an explicit error signal, not silently dropped.

**Falsifiable:** Send encoded `0xD0 0x80` to the adapter as a request. Adapter MUST emit `ERROR_HOST` or `FAILED` (see [enh.md §Unknown Command Contract](enh.md#unknown-command-contract) for variant handling); the host MUST NOT see a generic timeout.

### XR_ENH_ParserReset_AfterReadTimeout

**Invariant:** A read timeout that interrupts a partially received ENH frame resets the parser state. The next frame is parsed from a clean state.

**Falsifiable:** Send first byte of a two-byte encoded sequence, then delay beyond read timeout. Send a valid RECEIVED frame. Host must decode the RECEIVED frame correctly, not as a continuation of the interrupted sequence.

### XR_ENH_0xAA_DataNotSYN

**Invariant:** A logical `0xAA` byte in payload data (inside a RECEIVED frame, register value, or protocol response) is treated as data, not as a SYN/boundary marker.

**Falsifiable:** Send a RECEIVED frame containing payload byte `0xAA`. Host must deliver the byte as data. Frame boundary detection must not trigger.

## INFO and Feature Discovery

### XR_INFO_RESETTED_CachePolicy_Explicit

**Invariant:** Cached INFO data is invalidated on every RESETTED event. INFO responses received before RESETTED are not used after RESETTED. This invariant applies only to implementations that cache INFO responses across requests (ebusgo, adaptermux). Stateless implementations that issue single-request INFO without caching (e.g., VRC Explorer) are exempt.

**Falsifiable:** Query INFO ID 0x00, receive response, then receive RESETTED. Query INFO ID 0x00 again. Host must re-query the adapter, not return stale cached data.

### XR_INFO_FrameLength_AndSerialAccess

**Invariant:** The first byte of an INFO response is the payload length `N` (the INFO ID is not echoed — it is known from the request). The host reads exactly `N` data bytes after the length byte. Concurrent INFO requests on the same session MUST use one of the following deterministic policies (no stealing, no undefined behavior):

- **Serialize**: queue the second request until the first completes.
- **Reject**: return an explicit error to the second requester.
- **Evict-old**: cancel the first request with an explicit error to its caller, then start the second. The first requester MUST NOT silently time out — it MUST be notified of the eviction.

**Falsifiable:** (a) Send INFO request for ID 0x00. Verify response starts with length byte, followed by exactly that many data bytes. (b) Issue two INFO requests concurrently. The implementation MUST produce one of the three policies above; the first requester MUST NOT silently receive timeout or corrupted data without an explicit cancellation signal.

## Arbitration

### XR_START_RequestStart_WriteAll_NoDoubleSend

**Invariant:** The START request (source address byte) is sent exactly once per arbitration attempt on the wire. The host MUST NOT send duplicate START frames for the same arbitration attempt (double-send causes the adapter to see two arbitration requests).

**Falsifiable:** Mock transport that captures all bytes written during START. The encoded START command sequence and source address byte must appear exactly once in the captured wire bytes per arbitration attempt.

### XR_START_Cancel_ReleasesOwnership

**Invariant:** If the host cancels an in-progress arbitration (e.g., context cancelled), bus ownership is released cleanly. No pending STARTED response is left unhandled.

**Falsifiable:** Start arbitration, cancel context before STARTED arrives, then start a new arbitration. The new arbitration must succeed without stale STARTED interference.

### XR_Arbitration_Fairness_NoStarvation

**Invariant:** Under contention (multiple pending bus requests), no single request is starved indefinitely. A fairness mechanism (e.g., priority queue, round-robin, or bounded retry) ensures all requests eventually get bus access.

**Falsifiable:** Queue 10 requests with equal priority. Mock adapter grants STARTED to each in turn. All 10 must complete within `10 x single_request_timeout`.

## UDP-PLAIN

### XR_UDP_LeaseTTL_CapRefresh_Bounded

**Invariant:** Bus ownership acquired via UDP-PLAIN is bounded by a maximum TTL. Once the adapter echoes the arbitration byte to indicate the bus win, ownership is released unconditionally if no idle SYN (`0xAA`) is observed within the TTL. Non-SYN raw traffic does not refresh the lease. If a proxy surfaces `STARTED`/`RECEIVED` northbound, those are derived proxy events rather than UDP-PLAIN adapter messages.

**Falsifiable:** Mock UDP-PLAIN adapter echoes the arbitration byte to indicate ownership, then produces only raw bytes other than `0xAA` (no idle SYN). Ownership must be released after TTL expires.

**Scope note:** This invariant ID is strictly for **ownership lease TTL** behavior. Any separate tests that validate UDP client-connection admission caps, concurrent-session limits, or socket accept throttling MUST use a different ID (e.g., `XR_UDP_ClientAdmission_Cap`). Do not overload this ID.

---

## Cross-Reference

**Status legend:**
- `✅` — canonical same-name test exists and passes.
- `⚠️ partial` — test exists but has a documented subcase that deviates (see notes).
- `⚠️ alias` — implementation has an equivalent test under a different (local) name; same-name alias pending.
- `❌ deviation` — implementation behavior deviates from the invariant; documented here.
- `—` — not implemented (no equivalent test).

| Test Name | Primary Spec | ebusgo | VRC Explorer | adaptermux | proxy |
|-----------|-------------|--------|--------------|------------|-------|
| XR_INIT_TimeoutFailOpen_Bounded | [enh.md §INIT](enh.md#init-timeout-invariant) | ✅ | ❌ deviation (TransportTimeout = fail-closed) | ✅ | ✅ |
| XR_UpstreamLoss_GracefulShutdown_NoHang | [enh.md §Errors](enh.md#errors) | ✅ | ⚠️ alias (no same-name test) | — | ✅ |
| XR_START_ReconnectWait_BoundedDeadline | [enh.md §START](enh.md#start--started--failed) | ✅ | ⚠️ alias (no same-name test) | — | ✅ |
| XR_ENH_UnknownCommand_ExplicitError_AdapterToHost | [enh.md §Unknown Command](enh.md#unknown-command-contract) | ⚠️ partial (`transport_recovery` subcase expects silent discard) | ⚠️ alias (no same-name test) | — | — |
| XR_ENH_UnknownCommand_ExplicitError_HostToAdapter | [enh.md §Unknown Command](enh.md#unknown-command-contract) | — | — | — | ✅ |
| XR_INFO_RESETTED_CachePolicy_Explicit | [enh-info-reference.md](enh-info-reference.md) | ✅ | N/A (no INFO cache) | ⚠️ alias (`XR_INFO_CACHE_SNAPSHOT`) | — |
| XR_INFO_FrameLength_AndSerialAccess | [enh.md §INFO](enh.md#info-frame-length-and-interleaving) | ✅ (serialize) | — | ⚠️ alias (serialize) | ⚠️ partial (evict-old policy — see invariant) |
| XR_ENH_ParserReset_AfterReadTimeout | [enh.md §Parser](enh.md#parser-reset-after-read-timeout) | ✅ | ✅ | — | ✅ |
| XR_ENH_0xAA_DataNotSYN | [ebus-overview.md §SYN](../ebus-services/ebus-overview.md#acknack-symbols) | ✅ | ✅ | — | ✅ |
| XR_START_RequestStart_WriteAll_NoDoubleSend | [enh.md §START](enh.md#start--started--failed) | ✅ | ✅ | — | ✅ |
| XR_START_Cancel_ReleasesOwnership | [enh.md §START](enh.md#start--started--failed) | ✅ | — | ⚠️ alias (`XR_BLOCKING_ARB_DEADLINE`) | ✅ |
| XR_Arbitration_Fairness_NoStarvation | [enh.md §START](enh.md#start--started--failed) | ✅ | — | ⚠️ alias | — |
| XR_UDP_LeaseTTL_CapRefresh_Bounded | [udp-plain.md §Ownership](udp-plain.md#ownership-lease-ttl) | — | — | — | ✅ |

**Notes:**
- `XR_ENH_UnknownCommand_ExplicitError_AdapterToHost` was split from a single bidirectional invariant because proxy currently covers only the host→adapter direction. ebusgo's `transport_recovery` subcase expects silent discard on the adapter→host path; this is marked `⚠️ partial` until the live read path returns explicit errors.
- `⚠️ alias` entries indicate that the implementation has an equivalent test (same protocol behavior) under a local ID. Canonical same-name aliases are pending in those repos.
- `N/A` entries are documented exemptions (e.g., VRC Explorer has no INFO cache, so the cache-invalidation invariant does not apply).
