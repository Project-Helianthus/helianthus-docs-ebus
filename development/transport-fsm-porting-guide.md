# Transport-Layer Fixes, FSM Quirks, and Protocol Workarounds

## Source: helianthus-vrc-explorer enhanced_tcp.py (WIP branch)
## Target: helianthus-ebusgo + helianthus-ebus-adapter-proxy

Date: 2026-04-08

---

## Summary Table

| # | Title | Severity | ebusgo | proxy |
|---|-------|----------|--------|-------|
| 1 | RESETTED during arbitration: close+reopen session | HANG | IMPLEMENTED | YES |
| 2 | RESETTED during bus read: close+reopen session | HANG | IMPLEMENTED | N/A |
| 3 | Parser reset after every state transition | DESYNC | YES | N/A |
| 4 | Collision backoff: 50ms floor for PIC16F firmware race | HANG | IMPLEMENTED | PARTIAL |
| 5 | TCP reconnect after timeout retries exhausted | HANG | IMPLEMENTED | N/A |
| 6 | Echo mismatch -> collision (SYN detection) | DESYNC | YES | N/A |
| 7 | Response CRC: 2-attempt inline retry with NACK/re-read | DATA_LOSS | YES | N/A |
| 8 | NACK + CRC unified retry counter | COSMETIC | MISSING | N/A |
| 9 | Initiator-to-initiator: no response expected | HANG | YES | N/A |
| 10 | SYN detection at every bus-read point | DESYNC | YES | N/A |
| 11 | TCP_NODELAY on adapter socket | COSMETIC | IMPLEMENTED | MISSING |
| 12 | Pre-encoded hot-path ENH frames | COSMETIC | N/A | N/A |
| 13 | INIT deadline: tolerate bus flooding | HANG | YES | YES |
| 14 | Adapter reset retry delay (200ms stabilization) | HANG | YES | PARTIAL |

---

## Detailed Analysis

---

### FIX 1: RESETTED during arbitration -- close and reopen full session

**Problem:** If the adapter firmware resets while arbitration is in progress
(START sent, waiting for STARTED/FAILED), the parser holds stale state from
the pre-reset bus. Without a full session teardown and re-INIT, subsequent
reads produce garbage frames.

**Root cause:** The PIC16F adapter firmware can autonomously reset (power
glitch, watchdog, firmware update). The RESETTED response arrives instead of
the expected STARTED/FAILED. The TCP stream carries bytes from both sides of
the reset boundary in a single segment.

**Python fix (enhanced_tcp.py lines 644-650):**
```python
if command == _ENH_RES_RESETTED:
    self._trace(f"START_RESP reset features=0x{data:02X}")
    self.close()           # tear down socket + parser
    self._open_session()   # new TCP connection + INIT handshake
    raise _EnhancedCollision(
        f"Adapter reset during arbitration (features=0x{data:02X})"
    )
```
The collision exception feeds into `_send_with_policy` which retries the
entire send operation from scratch (re-arbitrate on the fresh session).

**Severity:** HANG -- without the close+reopen, the parser is desynchronized
and all subsequent frames are corrupt.

**Go status:**

- **ebusgo (enh_transport.go lines 190-213):** `IMPLEMENTED` -- The
  transport now performs full TCP teardown and re-INIT on RESETTED during
  arbitration, matching the Python close+reopen behavior.

- **proxy (server.go lines 1314-1383):** `YES` -- The proxy's upstream
  reader handles RESETTED comprehensively: aborts pending START, aborts
  pending INFO, releases bus ownership, invalidates info cache, and
  re-INITs upstream with feedback-loop prevention
  (`initSentAtNano` timestamp guard).

**Port status:** Implemented in ebusgo enh_transport.go.

---

### FIX 2: RESETTED during bus symbol read -- close and reopen full session

**Problem:** A RESETTED can arrive at any point while reading bus symbols
(during telegram transmission, while reading response bytes, etc.). The
Python transport treats this as a fatal session event requiring full
teardown.

**Root cause:** Same as FIX 1 -- adapter firmware reset. The difference is
context: this happens during `_recv_bus_symbol` rather than during
`_start_arbitration`.

**Python fix (enhanced_tcp.py lines 662-665):**
```python
if command == _ENH_RES_RESETTED:
    self.close()
    self._open_session()
    raise TransportTimeout(
        f"Adapter reset during bus read (features=0x{data:02X})"
    )
```
Note: This raises `TransportTimeout` (not `_EnhancedCollision`), which
feeds into the timeout retry counter in `_send_with_policy`.

**Severity:** HANG -- without close+reopen, all subsequent bus reads are
against a stale TCP stream.

**Go status:**

- **ebusgo (enh_transport.go lines 190-213):** `IMPLEMENTED` -- The
  transport now performs full TCP teardown and re-INIT on RESETTED during
  bus reads, matching the Python close+reopen behavior.

- **proxy:** `N/A` -- The proxy does not do bus-level reads in the same
  way; it processes upstream frames in a dedicated reader goroutine.

**Port status:** Implemented in ebusgo enh_transport.go (same as FIX 1).

---

### FIX 3: Parser reset after every state-machine transition

**Problem:** After arbitration completes (STARTED or FAILED), after
collision, after timeout, and before every retry, leftover bytes in the
parser (from TCP segment fragmentation) can produce phantom frames.

**Root cause:** TCP delivers ENH frames in arbitrary chunks. A STARTED
response can arrive in the same TCP segment as subsequent RECEIVED bytes.
If the parser is not reset, a partially-received ENH byte-pair from the
pre-arbitration phase can combine with the first byte of a post-arbitration
RECEIVED frame, producing a wrong decoded value.

**Python fix (enhanced_tcp.py lines 443-445, 629, 765, 809):**
```python
def _reset_parser(self) -> None:
    self._messages.clear()
    self._enh_pending_first = None
```
Called at:
- Line 502: after `_open_session()` (connection setup)
- Line 609: after INIT RESETTED response
- Line 629: after STARTED response in `_start_arbitration`
- Line 633: after FAILED in `_start_arbitration`
- Line 639: after ERROR_EBUS in `_start_arbitration`
- Line 643: after ERROR_HOST in `_start_arbitration`
- Line 765: on timeout retry (`_send_with_policy`)
- Line 809: on NACK/CRC retry (`_send_with_policy`)

**Severity:** DESYNC -- stale parser byte1 causes echo mismatch on the very
next symbol, which cascades into collision retries.

**Go status:**

- **ebusgo (enh_transport.go lines 321-332):** `YES` -- After
  `StartArbitration` completes (both success and failure), the Go code
  calls `t.parser.Reset()` and clears `t.pending`. The comment at line
  322-328 explicitly documents this TCP fragmentation issue.

---

### FIX 4: Collision backoff -- 50ms floor for PIC16F firmware race

**Problem:** After the adapter reports FAILED (arbitration lost), a rapid
re-issue of START can arrive before the PIC16F firmware has finished its
internal state reset. This causes transient eBUS signal loss
(ebus_error=0x00).

**Root cause:** The PIC16F firmware has a race condition in
`protocol_state_dispatch` (decompiled firmware line 9938). After FAILED, it
enforces a 60-tick minimum scan deadline before accepting another START.
But a rapid START from the host bypasses this deadline because the UART
interrupt processes the new START before the main loop applies the
deadline. The firmware then enters an invalid state and reports eBUS error.

**Python fix (enhanced_tcp.py lines 309-316, 783-789):**
```python
# Config:
collision_backoff_min_ms: int = 50
collision_backoff_max_ms: int = 50

# In _send_with_policy, after _EnhancedCollision:
backoff_max = self._config.collision_backoff_max_ms
if backoff_max > 0:
    sleep_s = random.uniform(
        self._config.collision_backoff_min_ms / 1000.0,
        backoff_max / 1000.0,
    )
    time.sleep(sleep_s)
```

**Severity:** HANG -- without the backoff, rapid START floods cause the
adapter to report eBUS errors, which are then retried, causing more floods.
The bus effectively goes down until the adapter firmware resets.

**Go status:**

- **ebusgo (protocol/bus.go lines 22-27):** `IMPLEMENTED` -- The Go code
  now includes a configurable collision backoff floor (default 50ms)
  applied before re-issuing START after arbitration FAILED.

- **proxy (server.go lines 42-43):** `PARTIAL` -- The proxy has
  `udpPlainBackoffBase = 25ms` and `udpPlainBackoffMax = 400ms` with
  jitter for UDP plain arbitration retries, which serves a similar purpose.
  But the ENH path's pending-start logic relies on the upstream adapter's
  own timing, and there is no explicit post-collision backoff injected
  before re-issuing START to the upstream adapter.

**Port status:** Implemented in ebusgo protocol/bus.go.

---

### FIX 5: TCP reconnect after timeout retries exhausted

**Problem:** When the adapter reboots or a network blip occurs, the TCP
connection becomes stale. Timeout retries on the same dead socket always
fail. The scan aborts after exhausting timeout retries.

**Root cause:** TCP keepalive detection is too slow for interactive use
(default kernel keepalive is 2+ hours). A stale TCP connection does not
produce errors until the application attempts I/O, and even then the first
few reads may timeout rather than error.

**Python fix (enhanced_tcp.py lines 722-729, 740-764):**
```python
def _reconnect(self, seq: int, attempt: int) -> None:
    self.close()
    time.sleep(self._config.reconnect_delay_s)  # default 2.0s
    self._open_session()

# In _send_with_policy, after timeout retries exhausted:
reconnect_retries += 1
if reconnect_retries > self._config.reconnect_max_retries:
    raise TransportTimeout(...)
try:
    self._reconnect(seq, reconnect_retries)
except (TransportError, TransportTimeout, OSError):
    # reconnect itself failed -- count it and try again
    ...
timeout_retries = 0  # reset timeout counter for fresh session
continue
```
The policy is: 2 timeout retries per session, then 3 reconnect attempts
(each with a 2s delay), each getting fresh timeout retry budget.

**Severity:** HANG -- without reconnect, a stale TCP session means the
entire scan/operation fails permanently.

**Go status:**

- **ebusgo (enh_transport.go line 21):** `IMPLEMENTED` -- The
  `ENHTransport` now includes mid-session TCP reconnect logic. When
  timeout retries are exhausted, the transport closes the connection,
  waits, re-dials, and re-INITs before resetting the timeout counter.

- **proxy:** `N/A` -- The proxy's upstream reader detects EOF/closed and
  signals `ErrUpstreamLost`. The caller (gateway) is expected to create a
  new Server instance. The proxy does not auto-reconnect to upstream.

**Port status:** Implemented in ebusgo enh_transport.go.

---

### FIX 6: Echo mismatch detection -- SYN means collision

**Problem:** When waiting for the echo of a transmitted symbol, receiving
SYN instead of the expected echo means another device won arbitration and
the bus has reset.

**Python fix (enhanced_tcp.py lines 677-678):**
```python
def _send_symbol_with_echo(self, symbol: int) -> None:
    self._send_enh_frame(_ENH_REQ_SEND, symbol)
    echo = self._recv_bus_symbol()
    if echo == _EBUS_SYN and symbol != _EBUS_SYN:
        raise _EnhancedCollision("unexpected SYN while waiting for echo")
    if echo != symbol:
        raise _EnhancedCollision(
            f"echo mismatch while waiting for 0x{symbol:02X}: got 0x{echo:02X}"
        )
```

**Severity:** DESYNC -- without SYN-specific detection, the code would
treat SYN as a generic echo mismatch. Both are collisions, but the SYN
case is more definitive (the bus has already been released by the adapter).

**Go status:**

- **ebusgo (protocol/bus.go lines 752-763):** `YES` -- The Go code has
  identical logic: SYN while waiting for non-SYN echo -> `ErrBusCollision`,
  and generic echo mismatch -> `ErrBusCollision` with a different error
  message.

---

### FIX 7: Response CRC -- 2-attempt inline retry with NACK then re-read

**Problem:** The target's response can have CRC errors due to bus noise.
The eBUS protocol (section 7.4) allows the initiator to NACK the response
and have the target retransmit once.

**Python fix (enhanced_tcp.py lines 856-884):**
```python
for response_attempt in range(2):
    length = self._recv_bus_symbol()
    # ... read response bytes + CRC ...
    if _crc(segment) != crc_value:
        self._send_symbol_with_echo(_EBUS_NACK)
        if response_attempt == 0:
            continue  # target retransmits
        self._send_end_of_message()
        raise _EnhancedCrcMismatch("response crc mismatch")
    self._send_symbol_with_echo(_EBUS_ACK)
    self._send_end_of_message()
    return parsed
```
On first CRC mismatch: send NACK, loop back to read the retransmission.
On second CRC mismatch: send SYN (end of message), raise CRC error.

**Severity:** DATA_LOSS -- without the retry, any CRC error immediately
fails the request, and the outer retry policy re-arbitrates from scratch
(wasting bus time).

**Go status:**

- **ebusgo (protocol/bus.go lines 589-662):** `YES` -- Identical 2-attempt
  loop with NACK on first CRC fail, then CRC error on second fail.

---

### FIX 8: NACK and CRC as a unified retry counter

**Problem:** The Python implementation uses a single `nack_retries` counter
for both `_EnhancedNack` (target NACK'd the command) and
`_EnhancedCrcMismatch` (response CRC failed after inline retry). This means
a CRC error on one attempt and a NACK on the next share the same retry
budget.

**Python fix (enhanced_tcp.py lines 797-813):**
```python
except (_EnhancedNack, _EnhancedCrcMismatch) as exc:
    nack_retries += 1
    if nack_retries > self._config.nack_max_retries:
        ...
        if isinstance(exc, _EnhancedNack):
            raise TransportNack(message) from exc
        raise TransportError(message) from exc
    self._reset_parser()
```

**Severity:** COSMETIC -- the retry budget is 1 for both in the default
config, and combined vs separate counting only matters if the budget were
higher.

**Go status:**

- **ebusgo (protocol/bus.go lines 372-399):** `MISSING` (different design)
  -- The Go code has separate `NACKRetries` and timeout/CRC retry paths.
  CRC mismatch shares the `timeoutAttempts` counter (line 389:
  `ErrTimeout || ErrCRCMismatch`). NACK has its own counter (line 394:
  `ErrNACK`). This is a deliberate design choice, not a bug. The Python
  approach is simpler but less precise.

**No port needed** -- the Go design is arguably better (separate counters).

---

### FIX 9: Initiator-to-initiator -- no target response expected

**Problem:** When destination is an initiator-capable address, the eBUS
protocol does not define a target response phase. Waiting for one would
hang.

**Python fix (enhanced_tcp.py lines 851-854):**
```python
if _is_initiator_capable_address(dst):
    self._send_end_of_message()
    return b""
```
The `_is_initiator_capable_address` function (lines 392-402) checks the
eBUS address encoding per spec section 6.4.

**Severity:** HANG -- without this check, the code would wait for a
response that never comes from an initiator-class address.

**Go status:**

- **ebusgo (protocol/bus.go lines 575-581):** `YES` -- The Go code
  detects `FrameTypeInitiatorInitiator` and skips the response phase.

---

### FIX 10: SYN detection at every bus-read point

**Problem:** At each point where a bus symbol is expected (response length,
response data bytes, response CRC, command ACK), receiving SYN (0xAA)
means the bus has been released and the telegram is abandoned.

**Python fix (enhanced_tcp.py lines 858-859, 865, 869, 847):**
```python
# Example: waiting for response length
length = self._recv_bus_symbol()
if length == _EBUS_SYN:
    raise TransportTimeout("syn received while waiting for response length")
```
Each read point has its own SYN guard with a descriptive error message.

**Severity:** DESYNC -- without SYN guards, a 0xAA byte would be
interpreted as a data value (length=170, for example), causing the parser
to read 170 bytes of bus traffic as response data.

**Go status:**

- **ebusgo (protocol/bus.go lines 596, 609, 622, 559):** `YES` --
  Identical SYN detection at all four points with descriptive errors.

---

### FIX 11: TCP_NODELAY on adapter socket

**Problem:** Without TCP_NODELAY, Nagle's algorithm can buffer small ENH
frames (2 bytes) for up to 40ms before sending, adding latency to every
bus operation.

**Python fix (enhanced_tcp.py line 485):**
```python
sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
```

**Severity:** COSMETIC -- adds ~40ms latency per operation without the
fix, which accumulates significantly during a multi-thousand-register scan.

**Go status:**

- **ebusgo:** `IMPLEMENTED` -- `SetNoDelay` is called on the adapter-facing
  TCP connection in ebusgo.

- **proxy:** `MISSING` -- The proxy dials upstream via the `dialUpstream`
  helper. Whether TCP_NODELAY is set depends on the dialer implementation,
  but it is not explicitly documented or guaranteed.

**Port status:** Implemented in ebusgo. Proxy still pending.

---

### FIX 12: Pre-encoded hot-path ENH frames (performance only)

**Problem:** Encoding SYN, ACK, and NACK on every call wastes CPU cycles
in a tight bus loop.

**Python fix (enhanced_tcp.py lines 369-371):**
```python
_ENH_SEND_SYN = _encode_enh(_ENH_REQ_SEND, _EBUS_SYN)
_ENH_SEND_ACK = _encode_enh(_ENH_REQ_SEND, _EBUS_ACK)
_ENH_SEND_NACK = _encode_enh(_ENH_REQ_SEND, _EBUS_NACK)
```

**Severity:** COSMETIC -- pure performance optimization.

**Go status:** `N/A` -- The Go `EncodeENH` function is a simple two-byte
computation with no allocation. The overhead is negligible in Go compared
to Python.

---

### FIX 13: INIT deadline -- tolerate bus data flooding

**Problem:** During INIT, the adapter may stream bus data (RECEIVED frames)
before responding with RESETTED. If the code reads indefinitely waiting for
RESETTED, and the bus is flooded, it may never see it (or it may arrive
after an unreasonable delay).

**Python fix (enhanced_tcp.py lines 597-617):**
```python
def _init_transport(self, *, features: int) -> None:
    self._send_enh_frame(_ENH_REQ_INIT, features)
    deadline = time.monotonic() + self._config.timeout_s
    while time.monotonic() < deadline:
        try:
            kind, command, data = self._read_message()
        except TransportTimeout:
            return  # timeout during INIT is acceptable
        if kind != "frame":
            continue
        if command == _ENH_RES_RESETTED:
            self._reset_parser()
            return
        # ... error handling ...
    # Deadline expired without RESETTED -- proceed anyway
```
Key behavior: INIT timeout is NOT fatal. The transport proceeds without
confirmation, because some adapter firmware versions do not respond to INIT
at all (they just start streaming).

**Severity:** HANG -- without a deadline, bus data flooding during INIT
blocks forever.

**Go status:**

- **ebusgo (enh_transport.go lines 93-148):** `YES` -- The Go INIT has a
  deadline-bounded loop with timeout tolerance. Timeout returns nil
  (success), matching the Python behavior.

- **proxy (server.go lines 338-342):** `YES` -- Best-effort INIT with
  comment: "some adapters respond with RESETTED, others start streaming
  immediately."

---

### FIX 14: Adapter reset retry delay (200ms stabilization)

**Problem:** After an adapter reset (RESETTED received), the bus may be
silent for a period while the adapter re-initializes its eBUS transceiver.
Retrying immediately can hit another timeout.

**Python behavior:** The Python code closes and reopens the session
(FIX 1/2), which includes a reconnect delay
(`reconnect_delay_s = 2.0s`). This is much more aggressive than needed
but effectively provides stabilization time.

**Go fix (protocol/bus.go lines 17-20, 286-296):**
```go
const adapterResetRetryDelay = 200 * time.Millisecond

// In sendWithRetries, after ErrAdapterReset:
if errors.Is(err, ebuserrors.ErrAdapterReset) {
    select {
    case <-time.After(adapterResetRetryDelay):
    case <-runCtx.Done():
    case <-request.ctx.Done():
    }
}
```

**Severity:** HANG -- without the delay, rapid retries after adapter reset
produce cascading timeouts.

**Go status:**

- **ebusgo:** `YES` -- 200ms delay is present.
- **proxy:** `PARTIAL` -- The proxy's re-INIT after RESETTED uses a
  `reinitGuard` channel (buffered 1) to serialize re-INIT attempts, but
  there is no explicit delay between the RESETTED and the re-INIT. The
  `initSentAtNano` guard prevents feedback loops but does not add
  stabilization time.

---

## Port Priority Matrix

### Remaining (proxy-side only)

| Fix | Component | What to do |
|-----|-----------|------------|
| 11 | proxy | Set TCP_NODELAY on upstream-facing TCP connection |

### Already implemented (no action needed)

| Fix | Component | Status |
|-----|-----------|--------|
| 1 | ebusgo | TCP teardown + re-INIT on RESETTED in StartArbitration (enh_transport.go) |
| 2 | ebusgo | TCP teardown + re-INIT on RESETTED in bus reads (enh_transport.go) |
| 3 | ebusgo | Parser reset after arbitration |
| 4 | ebusgo | 50ms collision backoff floor (bus.go) |
| 5 | ebusgo | TCP reconnect after timeout retries exhausted (enh_transport.go) |
| 6 | ebusgo | Echo mismatch / SYN collision detection |
| 7 | ebusgo | Response CRC 2-attempt inline retry |
| 9 | ebusgo | Initiator-to-initiator skip response |
| 10 | ebusgo | SYN detection at all bus-read points |
| 11 | ebusgo | TCP_NODELAY on adapter-facing TCP connection |
| 13 | ebusgo, proxy | INIT deadline tolerance |
| 14 | ebusgo | Adapter reset 200ms stabilization delay |

---

## Architecture Note: Python vs Go Transport Layering

The Python `EnhancedTcpTransport` is a monolithic class that owns the full
lifecycle: TCP connection, ENH parsing, eBUS protocol (CRC, arbitration,
telegram framing), and retry policy. It is both the transport AND the
protocol engine.

The Go implementation splits this across layers:
- `transport/ENHTransport` -- TCP + ENH framing only (ReadByte, Write,
  StartArbitration)
- `protocol/Bus` -- eBUS protocol FSM (CRC, ACK/NACK, telegram framing,
  retry policy)
- `protocol/Join` -- reconnection/lifecycle management

The Python "transport" fixes were implemented at these Go layers:
- FIX 1, 2: `ENHTransport` (reconnect on RESETTED)
- FIX 4: `protocol/Bus.sendWithRetries` (post-collision delay)
- FIX 5: `ENHTransport` (mid-session TCP reconnect)
- FIX 11: ebusgo dialer (TCP_NODELAY)

---

## Files Referenced

### Python (source of fixes)
- `/Users/razvan/Desktop/Helianthus Project/helianthus-vrc-explorer/src/helianthus_vrc_explorer/transport/enhanced_tcp.py`
- `/Users/razvan/Desktop/Helianthus Project/helianthus-vrc-explorer/src/helianthus_vrc_explorer/transport/base.py`

### Go ebusgo (port target)
- `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgo/transport/enh_transport.go`
- `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgo/transport/enh.go`
- `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgo/transport/transport.go`
- `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgo/protocol/bus.go`
- `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgo/protocol/join.go`
- `/Users/razvan/Desktop/Helianthus Project/helianthus-ebusgo/determinism/retry.go`

### Go proxy (port target)
- `/Users/razvan/Desktop/Helianthus Project/helianthus-ebus-adapter-proxy/internal/adapterproxy/server.go`
