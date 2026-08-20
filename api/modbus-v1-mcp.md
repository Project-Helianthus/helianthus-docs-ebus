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

M4-02 exposes the raw reader and the retained-profile reader. A caller-triggered
raw request performs one bounded FC03 or FC04 transaction against the configured
endpoint, with the single bounded reconnect-and-retry exception defined below.
M4-02 does not run a detector, activate a profile, start a background poller, or
produce retained profile observations. Those producer operations remain in the
separately authorized M4-04 live-smoke node. Consequently,
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

A successful raw `data` object is closed and contains exactly:

| Field | JSON type | Rule |
| --- | --- | --- |
| `endpoint_ref` | string | `sha256:<64 lowercase hex>` |
| `unit_id`, `function`, `offset`, `quantity` | integer | Echo the admitted request |
| `words` | array of integer | Exactly `quantity` unsigned 16-bit words |
| `wire_bytes_hex` | string, omitted only when absent | Lowercase even-length hexadecimal wire-response bytes |
| `wire_response_id`, `logical_view_id`, `physical_request_id` | integer | Positive opaque provenance identities |
| `connection_id`, `transport_generation` | integer | Positive opaque transport identities |
| `poll_generation_id`, `deadline_identity` | integer | Positive opaque request identities |

No other raw-result field is part of V1.

#### Bounded transport recovery

One admitted raw-read operation consumes exactly one raw MCP quota admission.
When its first physical transaction fails with a retryable transport error and
the transport owner reports that reconnect is required, the gateway may perform
exactly one bounded reconnect followed by exactly one retry of the immutable
admitted request. It does not consume a second caller quota admission, widen the
deadline, change the unit/function/range, or perform a third transaction.

On retry success, the returned words and provenance come exclusively from the
successful retry. Its `connection_id` and `transport_generation` are newer than
the failed connection generation; data or identities from the failed attempt
must not be mixed into the result. If reconnect or the one retry fails, the
operation terminates with a bounded `UNAVAILABLE` error. Validation failures,
quota rejection, and provider errors that do not require reconnect are never
retried by this rule.

`modbus.v1.profile.observation.get` reads an immutable retained observation and
does not reconnect to the Modbus endpoint or perform wire I/O.

### `modbus.v1.profile.observation.get`

The closed input object requires non-empty UTF-8 `profile_id` and `sample_id`,
each bounded to 128 bytes. The successful profile `data` object is closed and
contains exactly:

| Field | JSON type | Rule |
| --- | --- | --- |
| `profile_id`, `sample_id` | string | Exact requested immutable identities |
| `profile_version`, `codec_version` | string, omitted only when unavailable | Immutable source-owner versions |
| `poll_generation_id` | integer, omitted only when unavailable | Opaque source poll identity |
| `source_validity` | string | Source-owned validity enum; not canonical availability |
| `source_time` | RFC3339Nano string, omitted when unavailable | Real source time only |
| `local_receipt_time` | RFC3339Nano string, omitted when unavailable | Source observation receipt time |
| `detection_evidence`, `activation_evidence` | array of string | Ordered bounded owner evidence |
| `observation_json_base64` | string | Standard padded Base64 of deterministic sanitized JSON bytes |
| `replay` | array of closed replay objects | Ordered exact raw dependencies |

Each replay object contains exactly `logical_view_id` and `wire_response_id`
(positive integer), `offset` (unsigned 16-bit integer), and `words` (array of
unsigned 16-bit integers). The decoded observation blob preserves the complete
`helianthus-modbusreg` observation, including normalization and slice
provenance, but its internal JSON members are opaque owner data and are not
individually added to the MCP V1 schema. Consumers that need stable fields use
the typed top-level and replay fields.

Every string field whose key is endpoint-bearing, case-insensitively and at any
nesting depth, is replaced with the deterministic SHA-256 endpoint reference
before the MCP payload is emitted. This explicitly includes `endpoint`,
`Endpoint`, and `endpoint_identity`. Userinfo is forbidden by endpoint
configuration, but this redaction still applies defensively to all retained
provenance.

## Envelope

Both tools use contract `helianthus-modbus-mcp` version `1.0`. The closed
top-level envelope contains exactly `meta`, `data`, and `error`. `data` is the
tool-specific object on success and `null` on failure. `meta` contains exactly
`contract`, `consistency`, `data_timestamp`, `data_hash`, and `limits`.
`limits` contains exactly `raw_read_max_words`, `raw_reads_per_window`,
`raw_read_window_milliseconds`, and `identity_max_bytes`, all integers. The raw
reader uses `consistency.mode = LIVE`. The profile reader uses
`consistency.mode = RETAINED_SOURCE_OBSERVATION`, and `data_timestamp` is the
observation's local receipt time rather than the time of the MCP query. This is
an acquisition label, not canonical freshness.

On success, `error` is `null`. On failure, `error` is a closed object containing
exactly string `code`, string `message`, boolean `retriable`, and string
`source_layer` fixed to `modbus`. Codes are `INVALID_ARGUMENT` for closed-schema
rejection, `RESOURCE_EXHAUSTED` for quota rejection, or `UNAVAILABLE` for an
owner/provider failure or an absent exact retained sample. The first is not
retriable; the latter two are retriable. Successful and error envelopes never
expose write authority.

Every emitted error message is endpoint-free. An owner/provider failure uses a
static bounded message and never copies a wrapped operating-system or network
error into the envelope. No error message may contain an endpoint, host name,
IP address, port, URL, userinfo, credential, or deployment-local path. Validation
messages may identify the rejected input field or rule, but remain endpoint-free.

Golden envelopes in the gateway lock deterministic key/array ordering and
`data_hash` for both tools. At the M4-02 publication boundary: No GraphQL,
Portal, Home Assistant, Matter, eeBUS binding, canonical PV semantic, or Modbus
write surface is introduced here. The later M5-06 target below reuses the
already-published raw operation without changing that historical boundary.

## FMV3-M5-06 Portal Reuse Target

The future Portal raw diagnostic route does not define another Modbus reader.
It invokes the same closed `modbus.v1.raw.read` operation core in process, so
MCP and Portal share argument validation, provider/deadline/reconnect behavior,
the four-reads-per-second runtime quota, result envelope, endpoint hashing, and
static error redaction. The fifth combined MCP-or-Portal request in one window
is `RESOURCE_EXHAUSTED` before wire I/O.

Portal supplies only `unit_id`, `function`, `offset`, and `quantity`. It cannot
select an endpoint, MCP tool name, profile, credential, write operation, or
unbounded range. The generic Portal deployment boundary authenticates browser
access; this reuse adds no Modbus-specific credential and is disabled by
default when that boundary is absent. Portal adds a sanitized audit event but
does not copy returned words, wire bytes, request bodies, endpoints, secrets,
certificate bytes, or private paths into logs or retained Portal stores.
