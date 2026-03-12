# ENH (Enhanced) Adapter Protocol

ENH is the “enhanced” host↔adapter protocol used by ebusd-style interfaces (commonly on TCP port `9999`).

See also:

- `protocols/ens.md` for ebusd’s `ens:` prefix semantics (serial speed selector; equivalent to `enh:` on network transports).
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

## SEND

`SEND` requests transmission of a single byte onto the eBUS:

```text
<SEND> <data>
```

For `data < 0x80`, the short-form (unframed) byte is also allowed.

## START / STARTED / FAILED

`START` requests that the adapter begins arbitration after the next bus `SYN` (`0xAA`) and uses the supplied initiator address:

```text
<START> <master>
```

If `<master>` is `SYN` (`0xAA`), a running arbitration is cancelled.

Outcomes:

- `<STARTED> <master>`: arbitration won
- `<FAILED> <winner>`: arbitration lost (the data byte indicates the winning initiator address)

### Arbitration byte visibility

During arbitration initiated by the host, adapters **must not** emit `RECEIVED` notifications for the arbitration bytes they put on the bus. Clients should not rely on echo notifications for those bytes.

### Why ebusd sends `DST` first after STARTED

In ebusd “direct” mode, the initiator address byte is emitted as part of arbitration. After a successful `STARTED`, the host continues the telegram by sending `DST`, then `PB SB LEN ...` (i.e., it does not re-send `SRC`).

> **Implementation note — ENS and ENH share arbitration semantics.** Both ENS and ENH adapters transmit the source byte on the wire during START arbitration. Callers must NOT include the source byte in the outgoing telegram payload for either mode. Setting `arbitrationSendsSource=false` for ENS is incorrect and causes a double source byte on the wire. See ebusgo#113.

### Parser state after arbitration

Implementations that use a stateful parser for ENH framing (e.g., two-byte command decoding) **must reset parser state** after arbitration completes (STARTED or FAILED). TCP fragmentation can deliver extra bytes alongside the arbitration response, leaving the parser with a partially-decoded frame. Without a reset, the stale parser state corrupts subsequent echo matching. See ebusgo#113, adapter-proxy#78.

## INFO

`INFO` requests additional adapter metadata:

```text
<INFO> <info_id>
```

The response is a stream of `<INFO> <data>` bytes where the **first** byte is a length `N` (excluding the length byte itself), followed by `N` data bytes.

Sending a new `INFO` request while a previous response is still streaming immediately terminates the previous transfer.

Common `info_id` values include:

- `0x00`: version + feature bits + checksums + jumper flags (length varies by adapter firmware)
- `0x01`: HW ID
- `0x02`: HW config
- `0x03`: HW temperature
- `0x04`: HW supply voltage
- `0x05`: bus voltage
- `0x06`: reset info
- `0x07`: WiFi RSSI

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
