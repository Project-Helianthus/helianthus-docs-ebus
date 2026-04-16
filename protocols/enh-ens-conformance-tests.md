# ENH/ENS Shared Conformance Test Catalog

<!-- legacy-role-mapping:begin -->
> Legacy role mapping (for cross-referencing older materials): `master` -> `initiator`, `slave` -> `target`. Helianthus documentation uses `initiator`/`target`.
<!-- legacy-role-mapping:end -->

This document defines canonical cross-repo (XR) conformance test names for ENH and ENS transport behavior. Each test name is a contract: any implementation claiming ENH/ENS conformance MUST pass these tests or document an explicit deviation.

These tests are the **doc-gate** for aligning proxy PR #101, adaptermux PR #502, ebusgo PRs #131-134, and VRC Explorer PRs #245-250/follow-up.

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

### XR_ENH_UnknownCommand_ExplicitError

**Invariant:** An encoded ENH command sequence whose command nibble (carried in `byte1` bits 5..2) does not match any defined command ID is reported as an explicit protocol error, not as a timeout or collision.

**Falsifiable:** Inject an encoded ENH command sequence with an undefined command nibble into the adapter→host stream. For response nibble 0x4 (undefined — defined response nibbles are 0x0-0x3, 0xA-0xC), the encoded bytes are `0xD0 0x80` (byte1=`11_0100_00`, byte2=`10_000000`, command=0x4, data=0x00). Raw bytes `< 0x80` are short-form data, not commands, and would not exercise this path. Host must emit a transport error, not a timeout. For host→adapter direction, inject encoded request nibble 0x4 (undefined — defined request nibbles are 0x0-0x3): bytes `0xD0 0x80`. Adapter should emit `ERROR_HOST`.

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

**Invariant:** The first byte of an INFO response is the payload length `N` (the INFO ID is not echoed — it is known from the request). The host reads exactly `N` data bytes after the length byte. Concurrent INFO requests on the same session are serialized or rejected; a new request does not steal the response channel.

**Falsifiable:** (a) Send INFO request for ID 0x00. Verify response starts with length byte, followed by exactly that many data bytes. (b) Issue two INFO requests concurrently. The first requester must receive its complete response; the second must either wait or receive an explicit error.

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

---

## Cross-Reference

| Test Name | Primary Spec | Implementing Repos |
|-----------|-------------|-------------------|
| XR_INIT_TimeoutFailOpen_Bounded | [enh.md §INIT](enh.md#init-timeout-invariant) | ebusgo, proxy, adaptermux; VRC Explorer: **deviation** (TransportTimeout = fail-closed on missing RESETTED) |
| XR_UpstreamLoss_GracefulShutdown_NoHang | [enh.md §Errors](enh.md#errors) | ebusgo, VRC Explorer, proxy |
| XR_START_ReconnectWait_BoundedDeadline | [enh.md §START](enh.md#start--started--failed) | ebusgo, VRC Explorer, proxy |
| XR_ENH_UnknownCommand_ExplicitError | [enh.md §Unknown Command](enh.md#unknown-command-contract) | ebusgo, VRC Explorer, proxy |
| XR_INFO_RESETTED_CachePolicy_Explicit | [enh-info-reference.md](enh-info-reference.md) | ebusgo, adaptermux |
| XR_INFO_FrameLength_AndSerialAccess | [enh.md §INFO](enh.md#info-frame-length-and-interleaving) | ebusgo, adaptermux, proxy |
| XR_ENH_ParserReset_AfterReadTimeout | [enh.md §Parser](enh.md#parser-reset-after-read-timeout) | ebusgo, VRC Explorer |
| XR_ENH_0xAA_DataNotSYN | [ebus-overview.md §SYN](../ebus-services/ebus-overview.md#acknack-symbols) | ebusgo, VRC Explorer, proxy |
| XR_START_RequestStart_WriteAll_NoDoubleSend | [enh.md §START](enh.md#start--started--failed) | ebusgo, VRC Explorer |
| XR_START_Cancel_ReleasesOwnership | [enh.md §START](enh.md#start--started--failed) | ebusgo, adaptermux, proxy |
| XR_Arbitration_Fairness_NoStarvation | [enh.md §START](enh.md#start--started--failed) | ebusgo, adaptermux |
| XR_UDP_LeaseTTL_CapRefresh_Bounded | [udp-plain.md §Ownership](udp-plain.md#ownership-lease-ttl) | proxy |
