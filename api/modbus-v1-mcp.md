# Modbus V1 MCP

This page defines the first read-only Modbus MCP surface. The implementation
dependency is `Project-Helianthus/helianthus-ebusgateway#802`; this contract is
not a live-device qualification or consumer-support claim.

## Ownership And Phase Boundary

`helianthus-modbus` owns transport requests, responses, scheduling, connection
generation, and wire/logical provenance. `helianthus-modbusreg` owns profile,
detector, activation, normalization, observation, and replay facts. The gateway
only wires those owners into MCP and sanitizes deployment-local endpoint
identities.

M4-02 exposes the raw reader and the retained-profile reader. It does not run a
detector, activate a profile, or poll hardware. Those producer operations remain
in the separately authorized M4-04 live-smoke node. Consequently,
`modbus.v1.profile.observation.get` returns `UNAVAILABLE` until an owning
detector/poller records the exact requested profile/sample pair; it never
fabricates a sample.

The gateway does not derive canonical availability, freshness, stale state, or
source precedence. `source_validity`, source time, and local receipt time remain
source-owned Modbus profile facts.

## Stable Tools

### `modbus.v1.raw.read`

The closed input object requires:

| Field | Limit |
| --- | --- |
| `unit_id` | integer `1..247` |
| `function` | integer `3` (FC03) or `4` (FC04) only |
| `offset` | zero-based PDU offset `0..65535` |
| `quantity` | `1..125` words, with `offset + quantity <= 65536` |

Unknown fields, write functions, fractional numbers, and ranges outside the
address space fail before transport execution. One gateway runtime admits at
most four raw MCP reads in each one-second fixed window. A fifth request returns
`RESOURCE_EXHAUSTED` before wire I/O; the next window restores capacity. The
underlying single endpoint retains its own bounded scheduler, queue, deadline,
and connection limits.

A successful result contains the unit/function/range, words, exact wire bytes,
wire-response ID, logical-view ID, physical-request ID, connection ID,
transport generation, poll generation, and deadline identity. The endpoint is
returned only as `endpoint_ref = sha256:<64 lowercase hex>`.

### `modbus.v1.profile.observation.get`

The closed input object requires non-empty UTF-8 `profile_id` and `sample_id`,
each bounded to 128 bytes. The result preserves:

- immutable profile and codec versions;
- sample and poll-generation identity;
- source validity, source time, and local receipt time;
- ordered detector and activation evidence;
- the complete `helianthus-modbusreg` observation, including normalization
  records and logical-view slice provenance; and
- ordered exact replay views with wire-response IDs, offsets, and raw words.

Every object key named `endpoint`, case-insensitively and at any nesting depth,
is replaced with the deterministic SHA-256 endpoint reference before the MCP
payload is emitted. Userinfo is forbidden by endpoint configuration, but this
redaction still applies defensively to all retained provenance.

## Envelope

Both tools use contract `helianthus-modbus-mcp` version `1.0`. `meta` contains
`data_hash`, `data_timestamp`, `consistency`, and the explicit limits. The raw
reader uses `consistency.mode = LIVE`. The profile reader uses
`consistency.mode = RETAINED_SOURCE_OBSERVATION`, and `data_timestamp` is the
observation's local receipt time rather than the time of the MCP query. This is
an acquisition label, not canonical freshness.

Errors are structured as `INVALID_ARGUMENT` for closed-schema rejection,
`RESOURCE_EXHAUSTED` for quota rejection, or retriable `UNAVAILABLE` for an
owner/provider failure or an absent exact retained sample. Successful and error
envelopes never expose write authority.

Golden envelopes in the gateway lock deterministic key/array ordering and
`data_hash` for both tools. No GraphQL, Portal, Home Assistant, Matter, eeBUS
binding, canonical PV semantic, or Modbus write surface is introduced here.
