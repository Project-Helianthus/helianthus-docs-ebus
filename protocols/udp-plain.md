# UDP plain (raw eBUS bytes over UDP)

UDP plain forwards raw bytes between a UDP endpoint and an eBUS adapter. It does not define ENH framing, arbitration, escaping, request correlation, retries, or client ownership. Bytes are forwarded as received.

## Native transport consequences

- A datagram endpoint does not establish exclusive bus ownership.
- Multiple writers can collide on the shared eBUS medium.
- A receiver sees a raw byte stream and cannot derive request ownership from UDP plain alone.
- eBUS frame encoding, including CRC and escape processing, remains the responsibility of the endpoint that constructs or decodes telegrams.

An implementation that needs shared-client arbitration must define that behavior outside this transport specification. Its synthetic events, initiator selection, retry or lease rules are not UDP plain protocol semantics.

## Example endpoint

```text
udp-plain://203.0.113.10:9999
```

## Relationship to ENH

UDP plain is not ENH. A device that exposes ENH framing over TCP or UDP uses the command and response framing documented in [ENH](enh.md). Raw eBUS byte boundaries and escaping are defined in [the eBUS wire overview](ebus-services/ebus-overview.md).
