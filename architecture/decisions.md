# Architectural Decisions

This document records the architectural decisions implemented in the codebase. Each section is an ADR with context, decision, and consequences.

## ADR-001: Three-repo split with a strict dependency chain

**Status:** Accepted

**Context:** The ecosystem spans low-level transport/protocol, registry/vendor logic, and API surfaces with different deployment constraints.

**Decision:** Split into three repositories with a strict dependency chain:
`helianthus-ebusgateway → helianthus-ebusreg → helianthus-ebusgo`.

**Consequences:** Lower layers remain TinyGo-friendly while higher layers can evolve independently. Circular dependencies are avoided by design.

## ADR-002: `RawTransport` abstracts byte-level IO

**Status:** Accepted

**Context:** The bus logic should not depend on a specific framing protocol or socket type.

**Decision:** Define a `RawTransport` interface with `ReadByte()`, `Write([]byte)`, and `Close()` to represent the minimal byte-level contract.

**Consequences:** ENH and ENS can share a common Bus implementation. Future transports can implement the same interface without touching protocol logic.

## ADR-003: ENH framing uses 2-byte command/data sequences

**Status:** Accepted

**Context:** The enhanced protocol wraps each data byte in a 2-byte frame with command bits and a 6-bit data payload.

**Decision:** Encode ENH as two bytes where the first carries the command and the high two data bits, and the second carries the remaining six data bits. Short-form receive notifications for bytes `< 0x80` are normalized into `ENHResReceived` frames by the parser.

**Consequences:** Transport decodes ENH frames and only forwards receive data bytes (`ENHResReceived`, including short-form) to the Bus, suppressing echoed bytes that match the outbound payload. Echo suppression tolerates missing address echoes by allowing a small leading skip when the adapter does not report arbitration bytes.

## ADR-004: ENS uses explicit escaping for control symbols

**Status:** Accepted

**Context:** ENS streams reserve specific control bytes and require escaping.

**Decision:** Use escape byte `0xA9` with `0x00` and `0x01` suffixes to represent `0xA9` and `0xAA` respectively; reject unescaped `0xAA`.

**Consequences:** ENS framing is deterministic and reversible; invalid sequences are detected at decode time.

## ADR-005: Frame type is inferred from target address

**Status:** Accepted

**Context:** eBUS distinguishes broadcast, master-master, and master-slave frames.

**Decision:** Infer `FrameType` from the target address. `0xFE` is broadcast; master/master is detected by valid master-address bit patterns; otherwise master/slave.

**Consequences:** Callers do not set frame type explicitly; it is derived from addressing rules.

## ADR-006: CRC8 is computed over escaped symbols

**Status:** Accepted

**Context:** eBUS CRC8 must account for reserved symbols `0xA9` (escape) and `0xAA` (SYN).

**Decision:** CRC computation treats `0xA9` as `0xA9 0x00` and `0xAA` as `0xA9 0x01` before updating CRC.

**Consequences:** CRC validation matches the wire-level framing used by the transports.

## ADR-007: Bus owns ACK/response state machine and retry policy

**Status:** Accepted

**Context:** Frame retries depend on frame type, and ACK/NACK handling must be consistent.

**Decision:** The Bus enforces the send/ACK/response flow and retry policy per frame type (broadcast has no response; master-master only ACK; master-slave ACK + response).

**Consequences:** Callers use a single `Send` call and receive typed errors after retries are exhausted.

## ADR-008: Priority queue by source address

**Status:** Accepted

**Context:** eBUS arbitration favors lower master addresses.

**Decision:** Outgoing frames are queued in a priority queue keyed by the source address, with FIFO ordering for equal priority.

**Consequences:** Concurrent callers are serialized according to bus arbitration rules without each caller knowing about priorities.

## ADR-009: Sentinel errors with classification helpers

**Status:** Accepted

**Context:** Higher layers must identify transport/protocol errors without depending on concrete types.

**Decision:** Define sentinel errors in `ebusgo/errors` and expose helper functions to classify errors as transient, definitive, or fatal.

**Consequences:** All layers can wrap errors with context and still allow `errors.Is()` checks for policy decisions.

## ADR-010: Value/Valid model and replacement values for data types

**Status:** Accepted

**Context:** eBUS data types often use specific replacement values to represent missing data.

**Decision:** Each data type decodes into a `Value` with a `Valid` flag, and exposes its replacement byte sequence via `ReplacementValue()`.

**Consequences:** Decoders can represent “present but unknown” fields without resorting to sentinel numbers or nullable types.

## ADR-011: Plane/Provider model with IORegistry-inspired matching

**Status:** Accepted

**Context:** A single device can represent multiple semantic roles (heating, DHW, system), and the mapping depends on device identity.

**Decision:** Use `PlaneProvider` matching over `DeviceInfo` to attach one or more `Plane` instances to each `DeviceEntry`. This is conceptually inspired by macOS IOKit:

- **DeviceRegistry ≈ IORegistry** (central device/property registry)
- **PlaneProvider ≈ driver matching/attachment**
- **Plane ≈ IOService instance** (semantic service view)
- **Multiple Planes per device ≈ multiple IORegistry planes**

**Consequences:** The same device can be represented in multiple semantic domains without duplicating the underlying identity or transport bindings.

## ADR-012: Schema and conditional SchemaSelector for payloads

**Status:** Accepted

**Context:** Many eBUS messages reuse the same primary/secondary identifiers but vary structure by target or hardware version.

**Decision:** Model payloads as ordered Schemas with named fields and use a `SchemaSelector` to choose the correct schema based on target address and hardware version.

**Consequences:** The same method identifier can decode into different field layouts without duplicating method definitions.

## ADR-013: Device discovery uses 0x07/0x04 identification frames

**Status:** Accepted

**Context:** Discovery must be deterministic and vendor-agnostic.

**Decision:** Scan by sending primary `0x07` and secondary `0x04` to each target and parse the 8-byte device info payload (manufacturer, device ID, SW, HW).

**Consequences:** Discovery returns a consistent `DeviceInfo` structure for providers to match against.
