# ENS (Enhanced, High-Speed Serial)

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
