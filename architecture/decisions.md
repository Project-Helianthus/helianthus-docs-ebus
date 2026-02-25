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

**Consequences:** ENH (enhanced adapter protocol) and plain eBUS byte streams (with ESC/SYN escaping) can share a common Bus implementation. Future transports can implement the same interface without touching protocol logic.

## ADR-003: ENH framing uses raw bytes and 2-byte command/data sequences

**Status:** Accepted

**Context:** The enhanced adapter protocol uses either short-form bytes (`< 0x80`) or 2-byte encoded command/data sequences (for `>= 0x80` and all command symbols).

**Decision:** Encode ENH command/data sequences as two bytes where the first carries the command and the high two data bits, and the second carries the remaining six data bits. For data bytes `< 0x80`, accept the ENH short form (raw byte without header) and normalize it into a `RECEIVED(data)` notification in the parser.

**Consequences:** Transport decodes ENH frames and only forwards receive data bytes (`ENHResReceived`, including short-form) to the Bus, suppressing echoed bytes that match the outbound payload. Echo suppression tolerates missing address echoes by allowing a small leading skip when the adapter does not report arbitration bytes.

## ADR-004: Plain eBUS streams escape control symbols (ESC/SYN)

**Status:** Accepted

**Context:** Plain eBUS byte streams reserve specific control bytes and require escaping.

**Decision:** Use escape byte `0xA9` with suffixes `0x00` and `0x01` to represent literal `0xA9` and `0xAA` respectively; reject unescaped `0xAA` inside escaped payload streams.

**Consequences:** ESC/SYN escaping is deterministic and reversible; invalid sequences are detected at decode time.

**Naming note:** ebusd uses `ens:` to mean “enhanced protocol at high serial speed” (see `protocols/ens.md`). To avoid confusion, this ADR refers to the plain wire-level escaping as “ESC/SYN escaping”.

## ADR-005: Frame type is inferred from destination address

**Status:** Accepted

**Context:** eBUS distinguishes broadcast, initiator-initiator, and initiator-target frames.

**Decision:** Infer `FrameType` from the destination address. `0xFE` is broadcast; initiator/initiator is detected by valid initiator-address bit patterns; otherwise initiator/target.

**Consequences:** Callers do not set frame type explicitly; it is derived from addressing rules.

## ADR-006: CRC8 is computed over escaped symbols

**Status:** Accepted

**Context:** eBUS CRC8 must account for reserved symbols `0xA9` (escape) and `0xAA` (SYN).

**Decision:** CRC computation treats `0xA9` as `0xA9 0x00` and `0xAA` as `0xA9 0x01` before updating CRC.

**Consequences:** CRC validation matches the wire-level framing used by the transports.

## ADR-007: Bus owns ACK/response state machine and retry policy

**Status:** Accepted

**Context:** Frame retries depend on frame type, and ACK/NACK handling must be consistent.

**Decision:** The Bus enforces the send/ACK/response flow and retry policy per frame type (broadcast has no response; initiator-initiator only ACK; initiator-target ACK + response).

**Consequences:** Callers use a single `Send` call and receive typed errors after retries are exhausted.

## ADR-008: Priority queue by source address

**Status:** Accepted

**Context:** eBUS arbitration favors lower initiator addresses.

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

## ADR-014: Projection graph core with Service-plane canonical paths

**Status:** Accepted

**Context:** We need to represent device semantics as a graph that can be viewed through multiple planes (e.g., observability vs. automation) while preserving stable identity across those views within a registration/snapshot.

**Decision:** Introduce a projection-graph core in `ebusreg` where, in Helianthus:

- A projection is a plane-scoped graph (nodes + edges).
- Each node has a plane-specific path and a canonical path in the `Service` plane.
- Node IDs are derived from the canonical Service-plane path and are stable within a registration/snapshot.
- Path format is `Plane:/segment/...` with `@name` marking location segments; plane and segment names disallow `/` and `:`, and segment names must be non-empty and not start with `@`.
- Edges are validated to reference existing node IDs and have stable IDs (`Plane:from->to`).
- Projections are multi-dimensional views: the **plane** dimension defines the view, while the **canonical** dimension anchors identity; nodes in different planes with the same canonical path represent the same entity and therefore share the same node ID.
- Edges are always plane-local and never connect nodes across planes.

**Examples (canonical paths across planes):**

- `Service:/ebus/addr@10/device@BASV2/method@get_operational_data`
- `Observability:/ebus/addr@10/device@BASV2/method@get_operational_data` (same canonical node, plane-specific path)
- `Debug:/ebus/addr@10/device@BASV2/register@b524` (canonical path is `Service:/ebus/addr@10/device@BASV2/method@get_ext_register`)

**Portal query expectations:**

- GraphQL consumers (Portal UI) query projection graphs via:
  `devices { projections { plane nodes { id path canonicalPath } edges { id from to } } }`
- `ProjectionNode.id` is derived from the canonical Service path so nodes can be correlated across planes; `path` is used for plane-local display.

**Consequences:** Planes become explicit projections of the canonical Service graph (Helianthus-specific), enabling deterministic identity across planes within a snapshot, consistent path validation, and safe graph composition for higher-level APIs.

## ADR-015: Portal consumes projections as plane-scoped graphs (IORegistry-style semantics)

**Status:** Accepted

**Context:** The portal needs deterministic behavior when switching planes (for example `Service` → `Observability` → `Debug`) without losing canonical node identity. Plane-level rendering and cross-plane correlation must remain explicit for API consumers.

**Decision:**

- Treat projection payloads as a strict mapping of `plane -> {nodes, edges}`.
- Render only the currently selected plane graph; do not merge edges across planes.
- Preserve selected node identity via canonical `Service` path (`canonicalPath`) when switching planes.
- Resolve selection in the target plane by canonical path (or clear selection if no mapped node exists).
- Keep node IDs canonical-path-derived so the same canonical entity can be joined across planes in one snapshot.

**Examples (canonical paths across planes):**

- `Service:/ebus/addr@10/device@BASV2/method@get_operational_data`
- `Observability:/ebus/addr@10/device@BASV2/method@get_operational_data`
- `Debug:/ebus/addr@10/device@BASV2/register@b524` → canonical `Service:/ebus/addr@10/device@BASV2/method@get_ext_register`

**Portal query expectation:**

- `devices { projections { plane nodes { id path canonicalPath } edges { id from to } } }`

**Consequences:** API and UI consumers get a stable, IORegistry-style multi-plane browsing model with canonical identity joins, explicit plane-local edges, and predictable plane-switch behavior.

## ADR-016: Coalesced semantic reads (timer fan-in) for bus efficiency

**Status:** Accepted

**Context:** Multiple consumers (for example GraphQL resolvers/subscriptions, a portal UI, and Home Assistant) need periodic reads of the same semantic registers. A naive model multiplies reads per consumer and can saturate the bus.

**Decision:** Implement a semantic read scheduler that:

- de-duplicates reads by a stable key (target + selector/register),
- coalesces “same tick” requests into one bus request,
- publishes the resulting value to all waiting callers/subscribers, and
- enforces default polling cadences by semantic class:
  - `state`: 1 minute
  - `config`: 5 minutes
  - `discovery`: 10 minutes

For write confirmation (when a write API exists), perform targeted confirm reads:
- start at 5 seconds after the write,
- stop early after two consecutive reads match the expected written value,
- hard-stop at 60 seconds,
- and only poll the registers touched by the write.

**Consequences:** Bus traffic remains bounded under multiple consumers, values become cacheable with explicit staleness, and “UI opened” does not automatically cause high-frequency polling (unless explicitly configured).

## ADR-017: Physical vs Virtual devices and connected-device trees

**Status:** Accepted

**Context:** Helianthus must represent both real devices discovered on the eBUS and derived semantic entities (zones, DHW, energy totals). Some devices may exist physically behind a controller (e.g., RF thermostats behind a regulator) but are not directly addressable or identifiable yet.

**Decision:**

- A **physical device** is a real-world entity for which Helianthus can communicate deterministically (directly or via a controller proxy) and can read identity/capabilities deterministically.
- A **virtual device** is a modeled entity that does not (yet) have deterministic communication and/or identity/capability extraction. This includes projections such as “Zone 1”, “DHW”, or “Energy totals”.
- Communication topology is represented explicitly as a **connected device tree** (e.g., daemon → adapter → bus device → virtual children) using `via_device` relationships, not by “levels”.
- Promotion rule: a behind-controller device becomes **physical** once Helianthus implements a stable, deterministic protocol via the controller to read its identity/capabilities.

**Consequences:** Device identity remains stable and explainable, UIs can render correct parent/child topology, and derived semantic devices do not pretend to be independently addressable hardware.

## ADR-018: Initiator join uses passive warmup with bounded active inquiry

**Status:** Accepted

**Context:** On live buses, Helianthus may join while other initiators are already active. Joining should minimize additional traffic and avoid known address collisions.

**Decision:**

- Join starts with a passive listen warmup (default 5s) and builds source/target activity statistics.
- Candidate initiator addresses are selected from the valid 25-address set.
- Selection prefers highest addresses by default (lower arbitration priority) unless explicitly configured otherwise.
- Companion target (`initiator + 0x05`) activity heuristics reject risky candidates when the companion target looks active.
- Active `0x07 0xFE` inquiry is optional, rate-limited, and bounded per process session.
- Last-good initiator persistence is best-effort and only reused when still safe.
- If all initiator addresses are occupied, join fails explicitly by default; force mode is opt-in.

**Consequences:** Default join behavior keeps bus chatter low, produces deterministic telemetry for selection rationale, and avoids unsafe address reuse while preserving an explicit operator override path.

## ADR-019: Collision monitor enforces fail-fast writes on foreign same-source traffic

**Status:** Accepted

**Context:** In shared-bus or proxied deployments, another participant can emit frames with the same initiator address Helianthus currently uses. Without explicit detection, request/response ordering and arbitration assumptions become unsafe.

**Decision:**

- Track recently transmitted frames in a bounded history with timestamps.
- For each received frame with `SRC == active initiator`, compare against recent local transmit history inside an echo window (default `200ms`):
  - matching frame: treat as local echo, no collision event,
  - non-matching frame: mark collision as foreign same-source.
- If runtime is in muted/listen-only mode, any `SRC == active initiator` frame is treated as collision.
- After rejoin (initiator change), ignore frames from the previous initiator during a grace window (default `750ms`) to avoid delayed-echo false positives.
- While collision state is active, new writes fail fast with an explicit arbitration-failed error classification.

**Consequences:** Collision state becomes deterministic and observable, upper layers can immediately stop unsafe writes, and rejoin transitions remain stable under delayed bus echoes.

## ADR-020: Read scheduler coalescing with state/config refresh windows

**Status:** Accepted

**Context:** Multiple consumers (GraphQL, HA integration, internal pollers) can request the same read-only register concurrently. Naive forwarding multiplies bus reads, increases contention, and raises the probability of response mismatch under shared-bus traffic.

**Decision:**

- Coalesce read-only invocations by deterministic key: `(plane, method, params)`.
- If the same key is already in-flight, subsequent callers wait for the same result instead of issuing another bus read.
- Cache successful responses per key and apply policy windows:
  - **state** refresh window defaults to `1m`,
  - **config** refresh window defaults to `5m`.
- Policy is tunable in router options (`state`/`config` intervals), and invocation class can be overridden per call via params (`cache_class` / `refresh_class`).
- Write methods (`ReadOnly=false`) bypass cache/coalescing and always go to bus.
- Cached representation stores raw decoded response frame copy, and each caller re-decodes from that frame to avoid shared mutable decoded state.

**Consequences:** Bus load drops under concurrent subscriptions, duplicate register reads are eliminated during active refresh windows, and response ordering risk is reduced because a single bus read serves concurrent callers for the same key.

## ADR-021: MCP-first delivery order and parity gates

**Status:** Accepted

**Context:** Feature development needs a deterministic integration path that avoids drift between internal prototyping and external consumers.

**Decision:** Use MCP as the primary development surface, then implement GraphQL parity, and only then enable consumer-facing integrations.
Graduation requires deterministic MCP contracts, golden snapshots, and MCP <-> GraphQL parity tests.

**Consequences:** New capabilities are stabilized earlier in a tool-oriented interface and cross-surface drift is detected before consumer rollout.

See [MCP-first Development Model](mcp-first-development.md).

## ADR-022: Centralized MCP architecture documentation in docs repository

**Status:** Accepted

**Context:** ADR content duplicated across runtime repositories creates drift and weakens doc-gate enforcement.

**Decision:** Keep MCP architecture decisions centralized in `helianthus-docs-ebus` and remove duplicated local ADR files from runtime repos.

**Consequences:** Documentation has a single canonical source and repository-level doc-gates remain auditable.

## ADR-023: Gateway-hosted Portal API for evidence-first reverse engineering

**Status:** Accepted

**Context:** `helianthus-vrc-explorer` (Python) provided useful reverse-engineering workflows, but Helianthus runtime is Go-first. We need a dynamic portal that exposes multiple runtime views (functional planes, projections, semantic contract, and raw traces) without moving semantic logic into Home Assistant.

**Decision:**

- Add a dedicated gateway-hosted portal surface under `/portal`, with versioned read APIs under `/portal/api/v1/*`.
- Keep portal API **read-only by default**. Any future mutating controls must be explicit, separately flagged, rate-limited, and audited.
- Treat the gateway as the sole semantic authority; Home Assistant remains a consumer of GraphQL semantic contract only.
- Use evidence-first workflow in the portal: investigation context, provenance, and exportable issue bundles are first-class outcomes.
- Keep runtime Node-free: frontend assets are built at build-time and embedded in gateway binaries via Go `embed`.

**Consequences:** Helianthus gains a native, production-aligned portal that can replace VRC-Explorer incrementally, while preserving architectural layering and minimizing operational complexity.

## ADR-024: Shared deterministic primitives for MCP invoke and hashing workflows

**Status:** Accepted

**Context:** MCP-first rollout requires deterministic invoke semantics and stable `data_hash` behavior. Previously, idempotency and canonicalization logic risked diverging when implemented ad-hoc at gateway level.

**Decision:** Standardize these capabilities as shared low-level primitives in `helianthus-ebusgo/determinism`:

- idempotency cache primitives with TTL eviction, payload fingerprint conflict detection, and immutable cached payload copies;
- deterministic retry schedule primitives (fixed/custom/exponential) paired with normalized retriable-error classification;
- canonicalization primitives (`CanonicalClone`, `CanonicalJSON`, `CanonicalHash`) for stable hash input generation.

These primitives are part of MCP-first foundation work and are consumed before GraphQL parity rollout.

**Consequences:** Determinism behavior is reusable and testable across layers, invoke safety logic is less error-prone, and parity checks rely on a single canonical normalization path. No eBUS wire/protocol semantics are changed by this decision.

## ADR-025: BAI heat-source modeling boundary and VWZ-equivalent design contract

**Status:** Accepted

**Context:** Helianthus needs deterministic heat-source modeling for Vaillant BAI while preventing domain leakage from controller/regulator semantics. The same design must be reusable for future heat-source classes (for example VWZ heat pumps) without re-inventing contracts each time.

**Decision:**

- BAI modeling is **BAI-only** and excludes EMM/controller semantics.
- `scan` is a **cross-device discovery layer**, not a BAI plane. BAI planes are:
  - `registers` (with groups such as `dia1`, `dia2`, `maintenance`, `expert`)
  - `hcmode`
  - `errors`
  - `service`
- Runtime enforcement must deny cross-domain lookups (`HEAT_SOURCE` cannot read `REGULATOR` registers, and vice versa).
- Snapshot reads across multiple planes use explicit timeout policy:
  - total timeout is caller-configurable (default `10s`)
  - per-plane budget derives from total timeout and selected plane count
  - default behavior is atomic (`allow_partial=false`)
  - partial mode is opt-in (`allow_partial=true`) and must return `error_planes`.
- Poll/read scheduling must include starvation prevention:
  - queue depth limit (`100`)
  - aging-based promotion (`15s`)
  - emergency promotion (`30s`)
  - FIFO preserved within the same effective priority band.
- `common_core` must be versioned (`common_core_vN`) and must not regress in-place for stable API contracts.
- Architecture docs are part of the runtime contract: every heat-source design change must be documented here in a way that enables an equivalent implementation for another heat-source class (VWZ).

**Consequences:** BAI behavior stays deterministic and isolated from regulator behavior, multi-plane reads get explicit and testable timeout semantics, queue starvation is bounded under load, and future VWZ support can reuse the same contract surface with class-specific register catalogs.
