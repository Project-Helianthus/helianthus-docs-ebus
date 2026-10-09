# ENS (enhanced high-speed serial)

In ebusd-style device naming, `ens:` selects the ENH adapter protocol over a serial connection at `115200` baud. `enh:` selects the same framing at `9600` baud. For network transports, where baud rate has no meaning, the prefixes are equivalent framing selectors.

This `ens:` prefix is distinct from eBUS wire escaping. eBUS escaping is documented in [the wire overview](ebus-services/ebus-overview.md#wire-escape-encoding); ENH framing is documented in [ENH](enh.md).

## Device-prefix forms

```text
enh:/dev/ttyUSB0
ens:/dev/ttyUSB0
enh:tcp:203.0.113.10:9999
ens:203.0.113.10:9999
```

An adapter that forwards raw eBUS bytes over UDP without ENH framing uses a different transport; see [UDP plain](udp-plain.md).

## Escape codec distinction

Some adapter firmware uses a data-only serial escape codec. This is a separate layer from the `ens:` device prefix and from physical eBUS escaping. Its observed substitutions are:

| Logical byte | Encoded bytes |
|---|---|
| `0xA9` | `0xA9 0x00` |
| `0xAA` | `0xA9 0x01` |

The codec carries data bytes only; it does not encode ENH control events such as `RESETTED`, `STARTED`, or `FAILED`. A user of this codec therefore cannot infer those ENH control events from the encoded byte stream.
