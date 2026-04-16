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

**Invariant:** An ENH byte whose high nibble does not match any defined command ID is reported as an explicit protocol error, not as a timeout or collision.

**Falsifiable:** Inject byte `0xB0` (undefined command 0xB) into the ENH stream. Host must emit a transport error, not a timeout.

### XR_ENH_ParserReset_AfterReadTimeout

**Invariant:** A read timeout that interrupts a partially received ENH frame resets the parser state. The next frame is parsed from a clean state.

**Falsifiable:** Send first byte of a two-byte encoded sequence, then delay beyond read timeout. Send a valid RECEIVED frame. Host must decode the RECEIVED frame correctly, not as a continuation of the interrupted sequence.

### XR_ENH_0xAA_DataNotSYN

**Invariant:** A logical `0xAA` byte in payload data (inside a RECEIVED frame, register value, or protocol response) is treated as data, not as a SYN/boundary marker.

**Falsifiable:** Send a RECEIVED frame containing payload byte `0xAA`. Host must deliver the byte as data. Frame boundary detection must not trigger.

## INFO and Feature Discovery

### XR_INFO_RESETTED_CachePolicy_Explicit

**Invariant:** Cached INFO data is invalidated on every RESETTED event. INFO responses received before RESETTED are not used after RESETTED.

**Falsifiable:** Query INFO ID 0x00, receive response, then receive RESETTED. Query INFO ID 0x00 again. Host must re-query the adapter, not return stale cached data.

### XR_INFO_FrameLength_AndSerialAccess

**Invariant:** INFO responses have explicit length (`1 + N` bytes). Concurrent INFO requests on the same session are serialized or rejected; a new request does not steal the response channel.

**Falsifiable:** Issue two INFO requests concurrently. The first requester must receive its complete response; the second must either wait or receive an explicit error.

## Arbitration

### XR_START_RequestStart_WriteAll_NoDoubleSend

**Invariant:** The START request (source address byte) is written exactly once per arbitration attempt. The write is atomic (all bytes in a single write call).

**Falsifiable:** Mock transport that counts write calls during START. Exactly one write call must occur per START attempt.

### XR_START_Cancel_ReleasesOwnership

**Invariant:** If the host cancels an in-progress arbitration (e.g., context cancelled), bus ownership is released cleanly. No pending STARTED response is left unhandled.

**Falsifiable:** Start arbitration, cancel context before STARTED arrives, then start a new arbitration. The new arbitration must succeed without stale STARTED interference.

### XR_Arbitration_Fairness_NoStarvation

**Invariant:** Under contention (multiple pending bus requests), no single request is starved indefinitely. A fairness mechanism (e.g., priority queue, round-robin, or bounded retry) ensures all requests eventually get bus access.

**Falsifiable:** Queue 10 requests with equal priority. Mock adapter grants STARTED to each in turn. All 10 must complete within `10 x single_request_timeout`.

## UDP-PLAIN

### XR_UDP_LeaseTTL_CapRefresh_Bounded

**Invariant:** Bus ownership acquired via UDP-PLAIN is bounded by a maximum TTL. If idle SYN is not observed within the TTL after STARTED, ownership is released unconditionally. Non-SYN traffic does not refresh the lease.

**Falsifiable:** Mock adapter sends STARTED then only RECEIVED frames (no SYN). Ownership must be released after TTL expires.

---

## Cross-Reference

| Test Name | Primary Spec | Implementing Repos |
|-----------|-------------|-------------------|
| XR_INIT_TimeoutFailOpen_Bounded | enh.md INIT | ebusgo, VRC Explorer, proxy, adaptermux |
| XR_UpstreamLoss_GracefulShutdown_NoHang | enh.md Errors | ebusgo, VRC Explorer, proxy |
| XR_START_ReconnectWait_BoundedDeadline | enh.md START | ebusgo, VRC Explorer, proxy |
| XR_ENH_UnknownCommand_ExplicitError | enh.md Errors | ebusgo, VRC Explorer, proxy |
| XR_INFO_RESETTED_CachePolicy_Explicit | enh-info-reference.md | ebusgo, adaptermux |
| XR_INFO_FrameLength_AndSerialAccess | enh.md INFO | ebusgo, adaptermux, proxy |
| XR_ENH_ParserReset_AfterReadTimeout | enh.md Parser | ebusgo, VRC Explorer |
| XR_ENH_0xAA_DataNotSYN | ebus-overview.md SYN | ebusgo, VRC Explorer, proxy |
| XR_START_RequestStart_WriteAll_NoDoubleSend | enh.md START | ebusgo, VRC Explorer |
| XR_START_Cancel_ReleasesOwnership | enh.md START | ebusgo, adaptermux |
| XR_Arbitration_Fairness_NoStarvation | enh.md START | ebusgo, adaptermux |
| XR_UDP_LeaseTTL_CapRefresh_Bounded | udp-plain.md Ownership | proxy |
