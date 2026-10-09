# Protocol routing: UDP plain shared-adapter policy

This AGPL architecture document holds shared-client policy removed from the CC0 UDP plain transport description. [UDP plain](../protocols/udp-plain.md) defines only raw-byte forwarding.

When a product shares one UDP plain adapter among clients, it may establish one southbound owner, serialize writers, wait for a physical arbitration echo, and retain the resulting ownership until a terminal bus condition. Retry count, backoff, jitter, initiator allocation, synthetic `STARTED` messages, timeout fallback, and lease TTL are product policy. They must be bounded, observable, and kept separate from raw UDP plain semantics.
