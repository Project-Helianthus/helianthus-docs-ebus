# ENS (Enhanced, High-Speed Serial)

## Disambiguation: ENS Has Two Meanings

The abbreviation "ENS" appears in two different contexts within the Helianthus ecosystem. They refer to different things:

1. **ENS as ebusd transport prefix** (`ens:`): selects the ENH (enhanced adapter) protocol over high-speed serial at `115200` Baud. This is a transport-layer concept -- `ens:` is simply an alias for `enh:` with a different baud rate. Documented in this file and in `protocols/enh.md`.

2. **ENS as firmware codec** (`codec_ens.c`): a distinct escape-based encoding layer implemented in adapter firmware (e.g., PIC-based eBUS adapters). This codec uses `0xA9` as an escape byte to encode control symbols in the byte stream between the firmware and the host. See the "ENS Escape Encoding (Firmware Codec)" section below.

In the Go codebase (`enh_transport.go`), `ENS` is aliased to the ENH transport -- meaning (1) above. Do not confuse this with the firmware codec (2).

---

In ebusd-style device naming, `ens:` selects the **enhanced adapter protocol** (see `protocols/enh.md`) and uses the **high-speed serial** variant (typically `115200` Baud).

This is distinct from the eBUS wire-level escaping of `ESC=0xA9` / `SYN=0xAA`, which is documented in `protocols/ebus-overview.md`.

## Device Prefix Semantics (ebusd)

ebusd recognizes two “enhanced” prefixes:

- `enh:` → enhanced protocol over serial at `9600` Baud
- `ens:` → enhanced protocol over serial at `115200` Baud

Both prefixes enable the same ENH framing; only the serial transfer speed differs.

### Network transports

When the underlying transport is TCP/UDP (for example `host:9999`), there is no serial baud rate. In that case, `enh:` and `ens:` are effectively equivalent and simply indicate “use ENH framing”.

If an adapter exposes raw eBUS bytes over UDP without ENH framing, use UDP-PLAIN instead (`protocols/udp-plain.md`).

Observe-first caveat: direct adapter-class `enh:` / `ens:` listeners on the
adapter port remain `unsupported_or_misconfigured` for passive observe-first.
Proxy-like ENH/ENS endpoints on other ports are the passive-capable path. See
[`deployment/full-stack.md#passive-observe-first-transport-contract`](../deployment/full-stack.md#passive-observe-first-transport-contract)
and
[`architecture/observability.md#troubleshooting-mapping`](../architecture/observability.md#troubleshooting-mapping).

## Examples

Serial:

```text
enh:/dev/ttyUSB0
ens:/dev/ttyUSB0
```

Network:

```text
enh:tcp:203.0.113.10:9999
ens:203.0.113.10:9999
```

## ENS Escape Encoding (Firmware Codec)

The firmware-level ENS codec (`codec_ens.c`) uses `0xA9`-based escape encoding to transport byte values that would otherwise conflict with eBUS control symbols. This encoding operates on the serial link between the adapter firmware and the host, and is distinct from the eBUS wire-level escape encoding (which uses the same byte values but applies at the bus level).

### Escape Sequences

The escape byte is `0xA9`. When a data byte matches a control symbol, it is replaced by a two-byte escape sequence:

| Logical byte | Wire encoding | Description         |
|-------------|---------------|---------------------|
| `0xA9`      | `0xA9 0x00`   | Literal ESC byte    |
| `0xAA`      | `0xA9 0x01`   | Literal SYN byte    |

### Encoding Direction

- **Transmit (host to bus):** the firmware receives escaped bytes from the host, decodes them back to logical bytes, then transmits the logical bytes on the eBUS (with eBUS-level escape encoding applied separately).
- **Receive (bus to host):** the firmware reads logical bytes from the eBUS, applies ENS escape encoding, and sends the escaped stream to the host.

### Relationship to eBUS Wire Escaping

Both the ENS firmware codec and the eBUS wire protocol use `0xA9`/`0xAA` escape sequences with identical substitution rules. However, they operate at different layers:

- **eBUS wire escaping** is applied on the physical bus between eBUS devices. CRC is computed on logical bytes before this encoding (see `protocols/ebus-services/ebus-overview.md#crc8-and-escaping`).
- **ENS firmware escaping** is applied on the serial/USB link between the adapter and the host software. It ensures that `0xA9` and `0xAA` bytes in the data stream do not get misinterpreted as framing symbols by the host.
