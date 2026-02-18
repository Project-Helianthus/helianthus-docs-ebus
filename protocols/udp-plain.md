# UDP-PLAIN (Raw eBUS bytes over UDP)

Some Ethernet eBUS adapters expose the wire-level eBUS byte stream over UDP datagrams.

This transport is **not** ENH: there is no `<INIT>`, no `<START>` arbitration request, and no ENH command/data framing. The UDP payload is simply a sequence of bytes as observed on / written to the bus.

## Semantics

- **Unit of transfer:** UDP datagrams.
- **Payload:** raw eBUS bytes (including wire-level escape sequences where applicable).
- **Ordering:** datagrams may be dropped or reordered by the network. Consumers must treat this as an *unreliable* byte stream.

Helianthus models this as `UDPPlainTransport`, where:

- each received UDP datagram is buffered as a contiguous byte slice,
- `ReadByte()` returns bytes sequentially across datagrams.

## Arbitration and multi-client behavior

Because UDP-PLAIN does not provide an ENH-style `<START>` / `<STARTED>` handshake, the adapter cannot coordinate bus ownership on behalf of multiple clients.

For UDP-PLAIN setups, **software arbitration and multi-client mediation must be implemented above the adapter**, typically via an eBUS adapter proxy that:

- is the *sole* UDP client of the adapter,
- arbitrates bus ownership and schedules requests,
- multiplexes bus traffic to multiple northbound clients.

## Examples

```text
udp-plain://203.0.113.10:9999
```

