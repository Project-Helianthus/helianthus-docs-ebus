# ENH (Enhanced) Adapter Protocol

ENH is the “enhanced” host↔adapter protocol used by ebusd-style interfaces (commonly on TCP port `9999`).

See also:

- `protocols/ens.md` for ebusd’s `ens:` prefix semantics (serial speed selector; equivalent to `enh:` on network transports). Note: in this document and its conformance tests, `ENH`/`ENS` refer to the ebusd transport prefixes, NOT the firmware data-only ENS codec (`codec_ens.c`) described in [ens.md §Disambiguation](ens.md#disambiguation).
- `protocols/udp-plain.md` for raw eBUS bytes over UDP without ENH framing.

Observe-first caveat: direct adapter-class ENH/ENS listeners on the adapter port
(for example `tcp/:9999`) are not the passive-capable observe-first path. The
current transport contract and troubleshooting signals are documented in
[`deployment/full-stack.md#passive-observe-first-transport-contract`](../deployment/full-stack.md#passive-observe-first-transport-contract)
and
[`architecture/observability.md#troubleshooting-mapping`](../architecture/observability.md#troubleshooting-mapping).

It is a byte-stream protocol where:

- bytes `< 0x80` **may be transferred as-is** (short form),
- bytes `>= 0x80` are transferred as a **2-byte encoded sequence** that also carries a 4-bit command ID.

The specification below follows ebusd’s `docs/enhanced_proto.md`.

## Encoding

### Short form (bytes `< 0x80`)

Any byte with the high bit clear (`0b0xxxxxxx`) can appear unframed on the stream.

- host→adapter: short-form bytes represent “send this data byte”
- adapter→host: short-form bytes represent “received this data byte”

### Encoded form (bytes `>= 0x80`, and all command symbols)

Encoded sequences are 2 bytes:

```text
byte1: 1 1 C C C C D D
byte2: 1 0 D D D D D D
```

- `C` = 4-bit command
- `D` = 8-bit data payload (split across the two bytes)

Reconstruction:

```text
data[7:6] = byte1[1:0]
data[5:0] = byte2[5:0]
```

## Command IDs

The 4-bit command nibble is interpreted by direction:

```text
Requests (host → adapter):
  0x0 = INIT
  0x1 = SEND
  0x2 = START
  0x3 = INFO

Responses (adapter → host):
  0x0 = RESETTED
  0x1 = RECEIVED
  0x2 = STARTED
  0x3 = INFO
  0xA = FAILED
  0xB = ERROR_EBUS
  0xC = ERROR_HOST
```

## INIT / RESETTED

`INIT` requests adapter initialization and feature negotiation:

```text
<INIT> <features>
```

Adapters are expected to reply with:

```text
<RESETTED> <features>
```

Feature bits:

- bit `0`: adapter supports **additional INFO** queries (version / HW ID / voltage / etc.)

Practical note: some adapters may start streaming bus bytes before emitting `RESETTED`. A robust client treats `INIT` as best-effort and proceeds once it sees either a valid `RESETTED` or valid bus traffic within a short timeout window.

### INIT Timeout Invariant

The INIT exchange follows a **fail-open bounded** model:

- If `RESETTED` is received within the timeout: `init_confirmed = true`, `features = <RESETTED.features>`.
- If `RESETTED` is **not** received before timeout: `init_confirmed = false`, `features = unknown` (no optional features may be assumed).
- Implementations MUST NOT claim INFO support solely because they requested INFO. Feature availability is determined exclusively by a confirmed RESETTED response.
- **Fail-closed** (abort connection) is permitted ONLY for explicit adapter errors (`ERROR_HOST`) or transport hard failures (TCP RST, socket EOF).

This invariant ensures that an adapter which does not implement RESETTED (e.g., older firmware) does not cause the host to hang or assume capabilities that do not exist.

## SEND

`SEND` requests transmission of a single byte onto the eBUS:

```text
<SEND> <data>
```

For `data < 0x80`, the short-form (unframed) byte is also allowed.

> **Escape responsibility (SEND / TX path only):** The adapter is responsible for eBUS wire escape **encoding** (`0xA9` substitution) on `SEND` data: the host provides logical frame bytes without escape encoding, and the adapter applies escape substitution before placing bytes on the bus.
>
> **Receive path (RX) is different:** The adapter does NOT decode wire escapes on the receive path. Raw eBUS wire bytes are forwarded to the host as `RECEIVED` events without transformation (verified against PIC firmware `runtime.c:1835-1841`). The host-side escape decoder reassembles `RECEIVED(0xA9) RECEIVED(0x00)` into logical `0xA9` and `RECEIVED(0xA9) RECEIVED(0x01)` into logical `0xAA`. `RECEIVED(0xAA)` is always a raw-wire SYN boundary, not a data byte.

## START / STARTED / FAILED

`START` requests that the adapter begins arbitration after the next bus `SYN` (`0xAA`) and uses the supplied initiator address:

```text
<START> <initiator>
```

If `<initiator>` is `SYN` (`0xAA`), a running arbitration is cancelled.

Outcomes:

- `<STARTED> <initiator>`: arbitration won
- `<FAILED> <winner>`: arbitration lost (the data byte indicates the winning initiator address)

> **Implementation recommendation:** If the adapter sends repeated STARTED frames with an initiator address that does not match the host's arbitration request, the host should abort arbitration after a configurable threshold (typically 3 mismatches). This prevents infinite arbitration loops when the bus is congested with competing initiators. All three Helianthus implementations (ebusgo, VRC Explorer, adaptermux) enforce this pattern.

### Arbitration byte visibility

During arbitration initiated by the host, adapters **must not** emit `RECEIVED` notifications for the arbitration bytes they put on the bus. Clients should not rely on echo notifications for those bytes.

### Post-arbitration byte echo (F-18 contract)

For every byte the host writes **after** the arbitration byte — i.e., every `SEND` byte that traverses `DST PB SB LEN DATA... CRC` and any subsequent response-phase bytes the host writes — the adapter (or proxy) **MUST** emit a corresponding `RECEIVED` notification that reflects the byte observed on the bus.

This follows directly from john30/ebusd's [`docs/enhanced_proto.md`](https://github.com/john30/ebusd/blob/main/docs/enhanced_proto.md), which says ENH_RES_RECEIVED "shall not be sent when the byte received was part of an arbitration request initiated by ebusd." The converse is implied: ENH_RES_RECEIVED MUST be sent for every other host-written byte.

Why this matters: ebusd's [`DirectProtocolHandler` at `protocol_direct.cpp:412-414`](https://github.com/john30/ebusd/blob/main/src/lib/ebus/protocol_direct.cpp) compares `recvSymbol != sentSymbol` after each send and collapses the bus state to `bs_skip` on mismatch or `SEND_TIMEOUT` (~10 ms). Without the echo, ebusd cannot advance `bs_sendCmd` past the arbitration byte — the entire post-arbitration phase abandons silently, no frame ever lands on the bus, and the next retry cycle re-enters arbitration to repeat the failure indefinitely.

Proxy and adapter implementations:

- Adapters that observe the bus directly (e.g., a microcontroller speaking ENH over UART) MUST emit `ENH_RES_RECEIVED(byte)` for every non-arbitration byte they observe on the wire while the host owns the bus.
- Proxies that multiplex multiple ENH client sessions over a single adapter MUST forward each received byte to **every** session, including the session that owns the bus. Suppressing the echo for the owner — a tempting "optimization" because the owner already knows what it sent — violates the contract and breaks any downstream client (ebusd, third-party tooling) that gates `bs_sendCmd` advancement on the round-trip.
- The arbitration byte itself is handled separately: clients receive it via `ENH_RES_STARTED(initiator)` on a successful win, not as `ENH_RES_RECEIVED`. Proxies that emit a synthesized `ENH_RES_RECEIVED(arbitration_byte)` to the winning session violate the "shall not be sent" half of the contract.

Implementations:

- ebusd-adapter-proxy (standalone): a single shared `ownerObserverSeen []byte` is forwarded to whichever session owns the bus. Correct.
- helianthus-ebusgateway adaptermux (embedded mux): every external session — owner and non-owner alike — receives every post-arbitration byte. The arbitration byte is delivered via `deliverWinnerByteToOtherSessions` to non-winners and via `ENH_RES_STARTED` to the winner. See `internal/adaptermux/mux.go` `deliverToSessions` and `_work_adaptermux_audit/EBUSD-VERIFICATION-2026-05-12-batch13.md` (F-18).

Symptoms of a non-conformant proxy that suppresses the owner echo:

- The owner client (e.g., ebusd) issues one `ENH_REQ_SEND(0xFE)` per scan attempt and never advances to `ENH_REQ_SEND(LEN)` or subsequent bytes.
- `passive_reconstructor` logs `abandon reason=corrupted_request phase=1 src=<owner_byte>` at a high rate.
- ebusd's local FSM collapses to `bs_skip` ~10 ms after each `SEND`, retries arbitration, wins again (`STARTED` arrives), and repeats — visible as multiple consecutive `STARTED` frames with no completed transactions in between (`ebusctl info` shows the `messages` counter stuck at a low value).

### Why ebusd sends `DST` first after STARTED

In ebusd “direct” mode, the initiator address byte is emitted as part of arbitration. After a successful `STARTED`, the host continues the telegram by sending `DST`, then `PB SB LEN ...` (i.e., it does not re-send `SRC`).

> **Implementation note — ENS and ENH share arbitration semantics.** Both ENS and ENH adapters transmit the source byte on the wire during START arbitration. Callers must NOT include the source byte in the outgoing telegram payload for either mode. Setting `arbitrationSendsSource=false` for ENS is incorrect and causes a double source byte on the wire. See ebusgo#113. Default: `arbitrationSendsSource` is `false` (adapter does not automatically include source address in arbitration); both ENH and ENS override this to `true`.

### Parser state after arbitration

Implementations that use a stateful parser for ENH framing (e.g., two-byte command decoding) **must reset parser state** after arbitration completes (STARTED or FAILED). TCP fragmentation can deliver extra bytes alongside the arbitration response, leaving the parser with a partially-decoded frame. Without a reset, the stale parser state corrupts subsequent echo matching. See ebusgo#113, adapter-proxy#78.

### Parser Reset After Read Timeout

Any read timeout that interrupts a partially received ENH frame MUST trigger a parser reset before the next frame is processed. Without this reset, the parser may interpret the first byte of the next frame as a continuation of the interrupted frame, causing cascading decode errors.

The reset clears:
- Pending byte1 (the first byte of a two-byte encoded sequence)
- Any accumulated multi-byte response buffer
- The current command context

**Invariant name:** `XR_ENH_ParserReset_AfterReadTimeout`

## INFO

`INFO` requests additional adapter metadata:

```text
<INFO> <info_id>
```

The response is a stream of `<INFO> <data>` bytes where the **first** byte is a length `N` (excluding the length byte itself), followed by `N` data bytes.

### INFO Concurrency

A new INFO request on the same transport/session while a previous INFO response is still streaming MUST be handled deterministically:

1. **Serialize**: Queue the new request until the current INFO response completes, OR
2. **Reject**: Return an explicit error to the caller of the new request.

An implementation MUST NOT allow a new INFO request to "steal" the response channel from an in-progress request. The previous requester would then receive a timeout or corrupted data.

Portable behavior: no overlapping INFO requests on the same transport/session.

### INFO Frame Length and Interleaving

INFO response framing: the first INFO response byte is the payload length `N`, followed by exactly `N` data bytes. The INFO ID is not echoed in the response — it is known from the request. Total response size is `1 + N` bytes (length byte + payload). Expected payload lengths per INFO ID are documented in `enh-info-reference.md`.

**Interleaving rules:**
- Bus traffic (`RECEIVED` frames) MAY arrive between INFO request and response. These MUST be buffered or dispatched separately; they do not terminate the INFO exchange.
- A `RESETTED` frame arriving during an INFO exchange terminates the INFO exchange. The cached INFO data from before the reset is invalidated.
- Stale INFO frames (from a previous session or before a RESETTED) MUST be discarded. The INFO cache MUST be invalidated on every RESETTED event.

There is no explicit cancellation frame for INFO streaming. `RECEIVED` frames are an explicit exception to termination (per the interleaving rules above) — they represent asynchronous bus traffic and are buffered/dispatched separately without affecting the INFO exchange. Any other non-INFO control frame (e.g., `STARTED`, `FAILED`, `ERROR_EBUS`, `ERROR_HOST`) that arrives during INFO delivery implicitly terminates the INFO stream. `RESETTED` always terminates per the rules above.

Common `info_id` values include:

- `0x00`: version + feature bits + checksums + jumper flags (length varies by adapter firmware)
- `0x01`: HW ID
- `0x02`: HW config
- `0x03`: HW temperature
- `0x04`: HW supply voltage
- `0x05`: bus voltage
- `0x06`: reset info
- `0x07`: WiFi RSSI

## Initiator-to-Initiator (i2i) Transactions

When the destination address is an initiator-capable address (both high and low nibbles in the set {0x0, 0x1, 0x3, 0x7, 0xF}), the transaction has **no response phase**. The target ACKs the command telegram and the transaction is complete -- the initiator must not wait for a response payload.

In ENH transport terms, after the target sends ACK (0x00) for an i2i frame, the host should proceed directly to end-of-message (SYN). The wire_phase FSM enters TransactionDone after ACK, not WaitResponseLen. Waiting for a response length byte on an i2i transaction would hang indefinitely.

### Unknown Command Contract

An ENH encoded command nibble (carried in the first encoded byte, `byte1` bits 5..2) that does not match any defined command ID (host: INIT=0x0, SEND=0x1, START=0x2, INFO=0x3; adapter: RESETTED=0x0, RECEIVED=0x1, STARTED=0x2, INFO=0x3, FAILED=0xA, ERROR_EBUS=0xB, ERROR_HOST=0xC) MUST be mapped to an explicit protocol error.

Implementations MUST NOT:
- Report an unknown command as a timeout or collision.
- Silently discard the byte and continue parsing (this corrupts the subsequent frame boundary).

The host SHOULD emit a transport-level error (e.g., `ErrUnknownENHCommand`) and reset the parser state. The adapter SHOULD emit `ERROR_HOST` for unrecognized host commands. Some compatibility paths emit `FAILED` instead of `ERROR_HOST`; this is a documented deviation and implementations MAY accept either as a valid adapter-side rejection signal. Conformance tests MUST accept both and mark the exact variant observed.

## Errors

The adapter can report:

- `<ERROR_EBUS> <error>`: UART/bus-side errors (e.g. `0x00` framing, `0x01` overrun)
- `<ERROR_HOST> <error>`: host-side transport errors

## Example (Hex)

SEND data byte `0x5A` (encoded form):

```text
byte1 = 0xC0 | (0x1 << 2) | (0x5A >> 6) = 0xC5
byte2 = 0x80 | (0x5A & 0x3F)           = 0x9A
```

## See Also

- [`architecture/enh-ens-conformance-tests.md`](../architecture/enh-ens-conformance-tests.md) -- ENH/ENS shared conformance test catalog (canonical XR test names and falsifiable invariants) — Helianthus architecture document, not public-domain protocol spec.
