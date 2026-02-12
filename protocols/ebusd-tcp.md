# ebusd TCP Command Protocol (Observed)

This document describes the ASCII command protocol exposed by the `ebusd` daemon over TCP (often on port `8888`). It is intended for tooling that drives eBUS transactions through ebusd rather than talking to an adapter directly.

For gateway transport selection examples using this backend, see `deployment/full-stack.md`.

## Transport

- Connection: plain TCP.
- Encoding: ASCII text commands terminated by `\\n` (newline).
- Responses: one or more newline-terminated text lines. Many versions terminate a response with a blank line.
- Errors: response lines starting with `ERR:` indicate failures (timeouts, signal issues, parse errors, etc.).

## `hex` Command

`hex` sends a raw eBUS telegram (without CRC) and prints the response as hex.

### Request

```text
hex <TELEGRAM_HEX>
hex -s <SRC_HEX> <TELEGRAM_HEX>
```

Where `<TELEGRAM_HEX>` encodes:

```text
DST PB SB LEN DATA...
```

Notes:
- The CRC byte is not included; ebusd computes it.
- `LEN` is the number of bytes in `DATA...` (0..255) and must be included.
- `<SRC_HEX>` overrides the source address for the command (optional; depends on ebusd configuration and permissions).

Example (Vaillant B524 register read payload `02 00 03 00 16 00` to `DST=0x15`):

```text
hex 15B52406 020003001600
```

(Whitespace is optional; ebusd accepts plain hex.)

### Response

On success, ebusd typically returns a single hex line representing the **target response bytes** as:

```text
LEN DATA...
```

Where the leading `LEN` is the eBUS response data length (not a B524 field). ebusd does not include the target CRC byte in this output.

Note on streaming vs request/response:

- `hex` is **not** a live bus capture; it returns only the response associated with the command you sent.
- The output does **not** include the initiator telegram, per-byte echo, addresses, or CRC.
- Unrelated bus traffic is **not** streamed through `hex`; monitoring/sniffing is a separate mode.

Broadcast notes:
- For broadcast telegrams (`DST=0xFE`), there is no target response. ebusd commonly returns a textual status line (e.g. “done broadcast”) instead of a hex payload.

Many B524 responses are easiest to parse by stripping this length prefix:

- If the response bytes are `b0 b1 ... bn` and `b0 == n`, treat `b0` as a length prefix and strip it.
- Example: response line `09030316004574616a00` parses to bytes:
  - `0x09` length prefix (9 bytes of remaining data)
  - B524 payload: `03 03 16 00 45 74 61 6a 00`

Notes:
- Some replies contain only a 1-byte payload (e.g. `01TT`), which becomes a single `TT` byte after stripping.
- A response of `00` indicates an empty payload (length 0).

### Errors and Multiline Responses

If the first non-empty response line starts with `ERR:`, the command failed.

Some ebusd versions may emit extra trailing lines after a valid hex payload line (including spurious `ERR:` lines). Tooling should treat the **first hex payload line** as authoritative and ignore any later lines once a valid payload has been parsed.

## `info` Command

`info` is a lightweight health/status command used by tooling to check daemon connectivity. Like `hex`, it may return `ERR:` lines on failure.

Many ebusd builds include an address summary in the `info` output, for example:

```text
address 08: scanned ...
address 15: scanned ...
address 31: self ...
```

Tooling can enumerate discovered target addresses by:
- matching lines starting with `address XX:` (hex), and
- excluding the `self` entry.

## Backend Integration Checklist

For deterministic request/response behavior when integrating ebusd TCP:

- Send `hex` requests with `DST PB SB LEN DATA...` (CRC omitted; ebusd computes it).
- Treat the first valid hex payload line as authoritative if trailing lines are present.
- Strip the leading eBUS response length byte (`LEN`) before higher-layer payload parsing when applicable.
- Treat `done...` responses as successful no-payload outcomes (commonly broadcast sends).
- Treat timeout/no-answer `ERR:` responses as timeout conditions; map other `ERR:` responses to invalid payload or command failure.

## Timing Caveat for Target Emulation

`ebusd` TCP is a host-side command relay and is useful for functional request/response validation. For strict response-timing emulation, it is usually insufficient because host scheduling and network jitter can shift response timing outside tight target windows.

For cycle-accurate target emulation behavior, place emulation logic near the adapter/firmware side where timing control is deterministic.
