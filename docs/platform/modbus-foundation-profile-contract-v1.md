# Modbus Foundation And Profile Contract V1

## Status And Authority

This page is the normative public companion for `FMV3-M1-00`. It freezes the
minimum contracts required by:

- `FMV3-M1-01` through `FMV3-M1-04` in `helianthus-modbus`; and
- `FMV3-M2-01` through `FMV3-M2-03` in `helianthus-modbusreg`.

Implementation of those issues must conform to this page. This page does not
claim that an implementation exists. It does not authorize gateway work,
vendor-profile admission, canonical photovoltaic semantics, or a write path.

The keywords **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**,
and **MAY** are normative.

This contract refines, but does not replace, the repository and licensing
boundaries in
[`modbus-multivendor-boundaries.md`](./modbus-multivendor-boundaries.md).
If the two pages appear to conflict, the stricter read-only, provenance, or
fail-closed rule applies until a versioned correction resolves the conflict.

The machine-readable companion is
[`manifests/modbus-foundation-profile-contract-v1.json`](./manifests/modbus-foundation-profile-contract-v1.json).
`scripts/validate_modbus_companion.py` validates its closed inventory,
artifact/license lanes, operation set, companion issues, recovery rows, source
policy, and downstream pin requirements.

## Wire Contract And Local Policy

The implementation-neutral, CC0-1.0 wire owner is
[`protocols/modbus/modbus-phase-one-wire-v1.md`](../../protocols/modbus/modbus-phase-one-wire-v1.md).
It records the exact PDU, FC03, FC04, FC2B/MEI0E, MBAP, RTU, CRC, and serial
timing facts plus their authoritative public sources.

The scheduling, abandonment, coalescing, provenance, qualification, and
profile-lifecycle rules below are Helianthus safety and reproducibility policy
under the repository's AGPL documentation lane. Wire facts MUST remain in the
CC0 protocol artifact; Helianthus policy MUST link to that owner instead of
forking or relicensing the facts.

## Layer Boundary

`helianthus-modbus` owns:

- application PDU validation and phase-one codecs;
- Modbus TCP and RTU ADU framing;
- endpoint, connection, and serial-line ownership;
- correlation, cancellation, abandonment, quarantine, and recovery;
- bounded scheduling and compatible read coalescing; and
- exact raw-word and transport provenance.

`helianthus-modbusreg` owns:

- versioned standard-family and vendor-overlay profile declarations;
- deterministic read-only detection and qualification;
- documentary-address normalization;
- versioned codecs and profile-declared coherence;
- source-observation identity; and
- sanitized fixture, replay, and mutation conformance.

The runtime MUST NOT interpret a register as a vendor value, normalize Device
Identification bytes as text, or select a profile. The profile registry MUST
NOT open a socket or serial port, frame a PDU or ADU, allocate transaction
identifiers, or bypass the runtime operation allowlist.

Neither repository may import the gateway, `helianthus-ebusreg`, or a private
binding. Canonical semantic policy remains outside both repositories.

## Phase-One Operation Set

The complete phase-one operation set is:

| Operation | Function and subfunction | Logical table | Direction |
| --- | --- | --- | --- |
| Read Holding Registers | FC03 | holding registers | read-only |
| Read Input Registers | FC04 | input registers | read-only |
| Read Device Identification | FC2B, MEI type `0x0E` | device identification objects | read-only |

All other function codes and all other FC2B MEI types MUST fail locally before
transport write invocation. There is no arbitrary-function escape hatch.

Broadcast and reserved targets, as classified by the CC0 wire reference, are
forbidden for phase-one reads. A profile detector is subject to the same
operation set and cannot weaken it.

FC03 and FC04 are distinct operations and logical tables. Numerically equal
offsets do not permit a request, cache key, coalescing key, observation, or
fixture to alias them.

## PDU Enforcement Policy

Requests and responses MUST conform byte-for-byte to the CC0
[common PDU, FC03, FC04, and exception contract](../../protocols/modbus/modbus-phase-one-wire-v1.md#common-pdu).
The implementation applies no permissive alternate decoder.

The decoder MUST receive an exact bounded byte slice and validate all declared
lengths before allocation or indexing. It rejects truncation, arithmetic wrap,
impossible lengths, function or response-shape mismatch, incomplete words, and
trailing bytes.

The response decoder is parameterized by request identity. FC03 and FC04
remain distinct in request identity and returned provenance. Each register is
retained as an uninterpreted 16-bit wire-order word.

Typed protocol failures preserve:

- requested operation;
- received function code when available;
- exception code when available;
- malformed-field category and byte offset when determinable; and
- transport identity without embedding profile semantics.

Unknown exception-code values remain typed unknown protocol exceptions. They
are not silently converted to timeout, no-data, or a profile result. The
protocol layer MUST NOT apply signedness, scale factors, multi-register word
order, string decoding, invalid sentinels, or vendor normalization.

## FC2B/MEI0E Device Identification

### Request Policy

The exact request, access-code, and object-space definitions are owned by the
CC0 [Device Identification wire reference](../../protocols/modbus/modbus-phase-one-wire-v1.md#fc2bmei0e-read-device-identification).

A stream traversal MUST begin with object `0x00`; any other initial cursor is
rejected before transport write. Every continuation cursor MUST come from the
immediately preceding successful segment. An individual request may select its
object directly.

Object values remain exact byte strings in `helianthus-modbus`. Text decoding,
trimming, case folding, Unicode replacement, NUL removal, and model/firmware
interpretation belong to a versioned profile declaration.

### Response And Traversal Policy

Each segment MUST pass every
[Device Identification response constraint](../../protocols/modbus/modbus-phase-one-wire-v1.md#response)
before aggregation.

For stream aggregation:

- object identifiers within a segment are strictly increasing and unique;
- the first returned identifier is greater than or equal to the requested
  cursor, allowing unimplemented optional identifiers to be skipped;
- returned object categories do not exceed either requested access or actual
  conformity;
- a continuation cursor is non-repeating and advances traversal; and
- a restart, cycle, duplicate object, non-progressing cursor, or category
  regression fails the aggregate as malformed.

A stream restart at object zero after the first segment is non-progress and
MUST fail rather than loop indefinitely.

### Aggregation Bounds

The wire-size values come from the CC0 reference. Helianthus fixes these
additional aggregation bounds:

| Constant | Value |
| --- | --- |
| maximum Device Identification segments | 256 |
| maximum distinct object identifiers | 256 |
| maximum aggregate object-value bytes | 62,464 bytes |

The aggregate limit is the wire maximum per-object value multiplied by the
object-identifier space. Lower configured limits MAY be used.

The aggregator MUST account for bytes before allocation, reject addition that
would exceed a limit, reject zero-object nonterminal segments, and terminate on
the first malformed segment. It MUST NOT publish a partial aggregate as a
successful identity result. Segment provenance is retained even when
aggregation succeeds.

A successful basic, regular, or extended stream traversal MUST contain each
mandatory basic object defined by the CC0 wire reference exactly once.
Returned objects and completion checks follow the actual conformity reported
under that reference.

## Modbus TCP Contract

### MBAP Framing

Every ADU MUST conform to the CC0
[Modbus TCP wire reference](../../protocols/modbus/modbus-phase-one-wire-v1.md#modbus-tcp-adu).
The stream parser validates the complete MBAP header and bounded declared
length before allocation. It does not assume that one socket read equals one
ADU. A protocol mismatch, oversized length, truncation, or bytes outside the
selected ADU is malformed.

### Ownership And Correlation

Each live TCP socket has exactly:

- one endpoint owner;
- one transaction-identifier allocator;
- one bounded in-flight correlation map shared by all unit identifiers;
- one socket generation identifier; and
- one socket-lifetime tombstone set.

Candidate association requires:

- active socket generation;
- transaction identifier;
- echoed unit identifier;
- normal expected function or its corresponding exception function as defined
  by the CC0 wire reference.

A normal response is successfully correlated only after its applicable byte
count or Device Identification shape also validates. If a candidate-associated
response has an impossible shape, it becomes that request's
`malformed_response`, fails the waiter, and cannot satisfy another request.

The requested register offset is retained as provenance but MUST NOT be used as
a response-correlation field.

A correlated exception response is delivered to the matching waiter as a typed
protocol exception and is not converted into timeout. A response with no
active matching transaction is dropped. A response from an old generation, a
mismatched unit, unrelated function, or impossible shape MUST NOT be delivered
as a successful response to any waiter.

### Transport Write Linearization

The cancellation-safe linearization boundary is invocation of the underlying
transport write. Before that invocation, cancellation proves that zero bytes
were transmitted. Once invoked, the result is classified exactly as:

| Result | Meaning | Required action |
| --- | --- | --- |
| `provable_zero` | transport proves no byte was transmitted | request may fail without abandoning the socket or identifier |
| `partial_write` | a strict prefix may have reached the peer | tombstone identifier, close socket, recover |
| `indeterminate_error` | transport cannot prove zero bytes | tombstone identifier, close socket, recover |
| `cancellation_race` | cancellation raced with transport completion | tombstone identifier, close socket, recover |
| `ambiguous_completion` | completion cannot be classified as zero or full | tombstone identifier, close socket, recover |
| full transmit success | entire ADU accepted by transport | enter response-wait state |

No implementation may infer `provable_zero` from a generic error or from a
zero byte count unless the transport contract explicitly guarantees that the
peer received no byte.

If the transport can prove that full-transmit completion linearized before
cancellation, the request enters response wait and the cancellation is handled
as response-wait abandonment. If it can prove cancellation linearized before
write invocation, the result is `provable_zero`. Every unresolved ordering
between those points is `cancellation_race`; byte count alone does not resolve
the race.

For every possibly transmitted result, the current connection is unsafe for
stream continuation. The runtime MUST:

1. tombstone the transaction identifier;
2. close the connection before another write;
3. fail or requeue only according to explicit idempotent read policy;
4. create a new connection with an incremented generation; and
5. reject all frames attributed to the old generation.

### Response-Wait Abandonment

After full transmit, timeout or cancellation abandons the waiter but cannot
retract the request. The transaction identifier becomes a tombstone for the
remainder of that socket lifetime. A late matching response is consumed and
dropped; it is never reassigned.

The tombstone retains immutable physical-request identity, expected unit and
operation, expected response shape, physical range or Device Identification
cursor, and transport generation. A late frame matching that tombstone gets a
request-bound `wire_response_id` with outcome `late_after_abandonment` and
retains exact response bytes. It remains dropped, with no `logical_view_id` or
waiter delivery.

Other non-tombstoned identifiers MAY continue on the socket. A tombstoned
identifier MUST NOT be reused on that socket. If the bounded identifier space
cannot provide a safe identifier, the owner performs a controlled close,
increments generation on reconnect, and only then may reuse the numeric value.

Normal socket close discards the allocator, in-flight map, and tombstones as
one generation-scoped unit. Reconnect state MUST NOT leak per-unit or
per-profile eligibility across endpoints.

## Modbus RTU Contract

### Framing

Every ADU MUST conform to the CC0
[Modbus RTU wire reference](../../protocols/modbus/modbus-phase-one-wire-v1.md#modbus-rtu-adu).
Phase-one requests use an individually addressable unit and reject broadcast
or reserved addresses before write. The decoder validates frame boundary,
address, operation shape, and the complete CRC before exposing PDU bytes.

The RTU line has one owner and at most one outstanding request. A frame is
transmitted and delimited according to the CC0 timing baseline. Endpoint
configuration MAY increase either safety interval but MUST NOT reduce it below
that baseline. Actual timing and configured increases are recorded by
qualification evidence.

### Abandonment And Quarantine

The same transport-write classifications apply to RTU. `provable_zero` is the
only abnormal result that does not require abandonment recovery. A partial,
indeterminate, cancellation-race, or ambiguous transmit enters quarantine.
Full transmit enters response wait; timeout or cancellation from response wait
also enters quarantine.

One serialized endpoint owner linearizes write completion, receive parsing,
timeout, cancellation, quarantine, and successor dispatch. On an abandonment
event it changes receive state to `QUARANTINE` atomically before resolving the
waiter or considering a successor. Bytes not already linearized as a valid
response before that transition, including bytes buffered concurrently, belong
to the abandoned exchange and are discarded.

The quarantine time anchor is:

- full-transmit completion for response-wait timeout or cancellation; or
- a conservative transmit horizon for partial, indeterminate,
  cancellation-race, or ambiguous completion, computed from write invocation,
  frame length, declared serial format, and baud when an exact last-byte time
  is unavailable.

During quarantine:

- no successor request may transmit;
- all received frames are discarded, including a valid same-address and
  same-function frame;
- release is no earlier than the quarantine anchor plus the endpoint-declared
  maximum response latency and also requires one complete wire-reference
  bus-idle interval after the last discarded byte;
- the proof and discarded-frame count are observable; and
- only successful resynchronization returns the endpoint to service.

If bounded quiescence cannot be established, the endpoint is disabled and
must pass explicit recovery before reuse. A late same-shape response MUST
never be delivered to a successor request.

### Physical Qualification

RTU ships under `RTU_PHYSICAL_QUALIFICATION_V1` with one exact disposition:

| Disposition | Meaning |
| --- | --- |
| `PHYSICALLY_QUALIFIED` | the named hardware and topology passed physical timing and quarantine evidence |
| `FIXTURE_ONLY_NO_HARDWARE` | deterministic frame fixtures pass, but no qualifying physical evidence exists |

A physical qualification record MUST include:

- record schema version and immutable record identifier;
- runtime implementation commit and configuration version;
- adapter and transceiver identity;
- serial mode, baud, parity, stop bits, and topology;
- measured physical 1.5-character and 3.5-character timing behavior;
- measured endpoint response-latency bound;
- timeout and cancellation quarantine traces;
- quiescence and successor-request proof;
- test timestamp, evidence hashes, and disposition; and
- revocation or supersession state.

`FIXTURE_ONLY_NO_HARDWARE` is default-disabled and experimental. It MUST NOT
produce an enabled, supported, or hardware-qualified claim. Explicit
experimental opt-in cannot rename that disposition or bypass profile gates.

Lack of RTU hardware does not block Modbus TCP, the Fronius TCP slice, or other
TCP-sufficient M1 work.

## Endpoint Scheduling And Recovery

Every endpoint configuration declares finite positive limits for:

- connections;
- in-flight requests per connection;
- total queued requests per endpoint;
- maximum active admission keys;
- protected queued slots per admission key;
- shared burst slots;
- queued requests per authorization scope and unit;
- transaction tombstones;
- coalesced dependents per `(endpoint, authorization_scope, unit_id)`;
- request and response deadlines;
- Device Identification aggregation;
- retry attempts; and
- reconnect backoff floor, ceiling, and jitter source.

Invalid, zero, negative, overflowing, or internally inconsistent limits fail
configuration before endpoint activation. Queue admission fails explicitly
when a bound is reached.

An admission key is `(authorization_scope, unit_id)`. Configuration declares
`max_active_admission_keys = K`, `protected_slots_per_key = R`, and
`shared_burst_slots = B`. Total endpoint queue capacity MUST be at least
`K * R + B`, using checked arithmetic. A key becomes active on admission of its
first queued request and releases its protected capacity only after its queue,
in-flight physical requests, and attached dependents are all empty. At most
`K` keys may be active.

Each active key owns `R` protected slots. It may additionally consume available
shared burst slots, but it MUST NOT consume capacity protected for another
active key or capacity needed to activate any of the remaining `K` keys.
Consequently, one key cannot fill the endpoint queue in a way that rejects the
first request for another key while an admission-key position remains. Limits
for an authorization scope, unit, or coalesced dependent MUST be at least the
protected capacity promised to that key and MUST NOT exceed the checked
endpoint total. Any inconsistent relationship fails before activation.

The scheduler maintains bounded queues by admission key.
Across non-empty authorization scopes it uses deterministic round-robin
service; within each scope it uses deterministic round-robin across non-empty
unit queues; within one scope/unit queue requests are FIFO by monotonic enqueue
sequence. A continuously busy unit therefore cannot consume another unit's
admission budget or starve its service. Retries re-enter through the same
bounded admission and fairness rules; they do not jump the queue. An expired
request is removed without transport write.

Reconnect backoff is bounded and cancellation-aware. Success resets backoff
only after a valid correlated response, not merely after socket connection.
Endpoint failure and profile qualification state are isolated by endpoint and
unit identifier.

The jitter source is injected. Its algorithm identifier, version, and seed or
the exact emitted jitter schedule are captured in traces. Production MAY seed
from entropy, but deterministic replay injects the recorded algorithm and seed
or schedule; wall clock, process identity, and fresh entropy cannot alter
replayed retry ordering or deadline outcomes.

The monotonic clock is also injected. Endpoint traces record clock-contract
version plus monotonic offsets and owner-assigned event sequence for enqueue,
admission, write invocation, transmit result, cancellation, response receive,
timer arm/fire, quarantine transition, queue service, and jitter/backoff.
Replay drives a virtual monotonic clock from that timeline. Events with equal
offset are ordered by recorded event sequence, so deadline, response, and
cancellation ties have one reproducible outcome.

## Read Coalescing And Provenance

### Compatibility

Two or more reads may coalesce only when all of these fields are equal:

- endpoint identity;
- transport family and active transport generation;
- unit identifier;
- function code and logical table;
- authorization scope;
- poll generation identifier; and
- operation deadline identity.

Their requested ranges must overlap, and their union must fit the FC03/FC04
operation limit owned by the CC0 wire reference. Adjacent but non-overlapping
reads are not coalesced by V1. Any mismatch refuses coalescing without changing
either logical request.

The physical request range is the minimal union of compatible ranges.
Coalescing MUST NOT change per-request admission, cancellation, or visibility.
Each dependent moves through `queued`, `attached`, and exactly one terminal
state: `delivered`, `cancelled`, or `failed`.

- Cancellation while queued removes that dependent. If it was the final
  dependent, no physical request is transmitted.
- Cancellation after transport write detaches that dependent. It receives no
  logical view or observation, even if the physical response later succeeds.
- The physical request continues while any attached dependent remains.
- Cancellation of the last attached dependent after write invokes the
  transport-specific abandonment path: TCP response-wait tombstone after full
  transmit, or RTU quarantine for possibly transmitted/full-transmit cases.
- Endpoint-owner event sequence resolves cancellation/response races.

### Physical And Logical Identity

Each physical request has an immutable `physical_request_id`. Every complete
response correlated to that request has one `wire_response_id`, including a
normal response, protocol exception, or correlated malformed response. The
identity is bound to:

- `physical_request_id`;
- endpoint;
- unit identifier;
- requested operation, including function and any applicable MEI/access code;
- received function code;
- logical table or Device Identification object space;
- physical zero-based PDU offset and word count for FC03/FC04, or requested
  object cursor and segment identity for FC2B/MEI0E; and
- transport generation identifier.

It also retains exact response bytes and one outcome:
`successful_data`, `protocol_exception`, `malformed_response`, or
`late_after_abandonment`. An uncorrelated frame has diagnostic frame identity
but cannot claim a request-bound `wire_response_id`.

Only `successful_data` can produce dependent observations. Every still-attached
successful dependent has its own `logical_view_id` linked to that
`wire_response_id`, plus:

- logical zero-based PDU offset;
- logical word count;
- slice offset within the physical response; and
- slice word count.

The slice is validated with checked arithmetic and MUST reproduce exactly the
words requested by that dependent. Unequal overlapping reads are the required
positive case: each logical view replays its own exact words and provenance
from the shared response.

`wire_response_id` and `logical_view_id` are opaque stable identities, not
hashes inferred from values. A correlated malformed or exceptional response
or a late response after abandonment retains its wire response and outcome but
yields no logical view. A transport failure with no received response or a
torn sample yields no successful logical view.

## M2 Profile Registry Contract

### Registry And Profile Identity

One registry contains multiple standard families and vendor overlays. A
versioned profile descriptor contains at least:

- stable `profile_id` and immutable `profile_version`;
- `profile_kind`: `standard_family` or `vendor_overlay`;
- standard/model/vendor applicability and known exclusions;
- required runtime contract version;
- detector, codec, normalization, coherence, and qualification versions;
- exact dependency set;
- evidence record identifiers and publication dispositions;
- maturity and default-enabled state; and
- revocation or supersession state.

A standard-family profile MUST contain no vendor assumptions. A vendor overlay
MUST declare the qualified standard-family version it refines and only the
evidence-backed delta. It cannot copy a standard model to attach a vendor
name.

Profiles are independently disableable. Removing or disputing one profile
cannot modify runtime behavior or another profile version.

The catalog rejects duplicate profile IDs or duplicate `(profile_id,
profile_version)` entries, returns a deterministic order independent of
registration or map iteration, and never mutates a published version in place.
A behavioral change requires a new immutable version and explicit
supersession. Serialized records carry their schema version and reject an
unknown incompatible version.

### Register Dependencies And Address Normalization

Each dependency declaration contains:

- stable dependency identifier;
- FC03 or FC04 logical table;
- documentary source locator and notation;
- documentary address base and address-space label;
- explicit transformation to zero-based PDU offset;
- resolved zero-based PDU offset and word count;
- codec identifier and version;
- coherence group; and
- evidence and applicability references.

The normalization record is retained with every observation. Human reference
numbers such as `4xxxx`, one-based register numbers, and zero-based PDU offsets
MUST NOT be accepted interchangeably. A transformation that is absent,
ambiguous, overflowing, or inconsistent with its resolved offset makes the
profile invalid.

### Codec Declaration

A codec is immutable and versioned. It declares every applicable dimension:

- raw word count;
- word permutation for multi-register values;
- intra-word byte order when the source defines an exception to Modbus byte
  order;
- signedness and integer or floating representation;
- scale source and scale application order;
- invalid, not-implemented, and reserved raw sentinels;
- string word packing, byte order, padding byte, termination, retained raw
  length, and documentary character repertoire; and
- output profile type and validity behavior.

No global "vendor byte order" exists. An undeclared dimension is valid only
when it is provably inapplicable to that codec. The codec MUST preserve raw
words and MUST NOT silently clamp, guess, trim, replace, or reinterpret an
invalid value.

Transport Device Identification values remain bytes. A profile may define a
versioned documentary comparison normalization for detection, but must retain
both exact bytes and the normalized comparison value with the normalization
version.

### Source Observation Envelope

Every successful profile observation contains:

- profile, codec, detector, normalization, coherence, and qualification
  versions;
- `sample_id`;
- `poll_generation_id`;
- `dependency_set_id`;
- source validity;
- source observation time or an explicit source-time-unavailable state;
- local receipt time;
- endpoint and unit identity; and
- every dependency's raw words, normalization record, `logical_view_id`,
  `wire_response_id`, logical offset/count, and slice offset/count.

`sample_id` identifies one coherent profile sample. It MUST NOT be reused for a
retry, a changed dependency set, or a different poll generation.
`dependency_set_id` identifies the exact ordered dependency declarations and
versions used by that sample.

Source validity and source time are not canonical availability, freshness, or
receipt time. `helianthus-modbusreg` records source facts; canonical policy is
owned later by the canonical registry/composition layer.

### Coherence And Torn Reads

Every profile declares a coherence policy for each dependency set:

- `single_wire_response`, requiring all words from one physical response; or
- `bounded_multi_response`, declaring ordering, maximum source/receipt skew,
  generation equality, retry-set behavior, and any documentary consistency
  marker.

All dependencies in a sample MUST use one poll generation and the exact
declared dependency set. On failure, retry occurs for the declared retry set;
new and retained-old dependencies MUST NOT be merged into a successful sample.

An unrecoverable torn, mixed-generation, missing, exceptional, malformed, or
provenance-incomplete read invalidates the sample. Partial raw evidence may be
retained as failed diagnostic evidence, but no successful profile observation
is emitted.

### Detector And Probe Plan

A detector is immutable and versioned. Its probe plan is:

- finite and statically bounded by operation count, total words, total Device
  Identification bytes, and deadline;
- ordered deterministically;
- composed only of FC03, FC04, and FC2B/MEI0E;
- read-only and free of arbitrary-function callbacks;
- explicit about required versus optional evidence; and
- explicit about model, firmware, gateway, and version gates.

Probe results retain raw responses and full transport provenance. Evaluation
is a pure deterministic function of the ordered results and declared
versions.

The terminal detector results are:

- `no_match`;
- `insufficient_evidence`;
- `ambiguous`;
- `experimental_candidate`; or
- `qualified_candidate`.

Missing required evidence cannot become a partial match. More than one
eligible profile is `ambiguous`; priority, registration order, or vendor name
does not break the tie. A failed model, firmware, gateway, or version gate is
not bypassed by explicit selection.

### Activation And Hardware Qualification

`experimental_candidate` is default-disabled and requires explicit opt-in. It
is never automatically eligible. Opt-in permits bounded use for research; it
does not create a support or qualification claim and cannot bypass detector or
applicability gates.

Automatic eligibility requires a `qualified_candidate` and a matching
versioned hardware qualification record. That record binds at least:

- qualification schema and record version;
- profile and detector versions;
- vendor, model, gateway, hardware, firmware, and protocol-mode applicability;
- implementation commit and fixture/evidence hashes;
- test outcome and timestamp;
- exclusions;
- status: active, revoked, superseded, or demoted; and
- reason and replacement record when status is not active.

A missing, mismatched, expired-by-policy, revoked, superseded, or demoted
record fails closed. Revocation disables new activation. An active instance
detecting a mismatch is disabled and must re-enter detection; it is not
silently retained under an old qualification.

The activation evaluator returns `auto_eligible` only for that exact
qualified-candidate plus active matching-record conjunction. Its other
terminal results are `experimental_opt_in_required`, `disabled`,
`insufficient_evidence`, `ambiguous`, `qualification_mismatch`, `revoked`, and
`demoted`. None is silently upgraded by explicit profile selection.

## Fixture, Replay, And Mutation Contract

### Manifest

Every admitted fixture has a machine-readable manifest containing:

- fixture schema version and immutable identifier;
- exact profile, codec, detector, normalization, coherence, and qualification
  versions;
- runtime scheduler/backoff/jitter algorithm versions plus the recorded jitter
  seed or exact schedule;
- virtual-clock contract version and complete monotonic event timeline;
- source type and stable evidence locator;
- permission basis and redistribution disposition;
- transformation from source to fixture;
- vendor/model/gateway/hardware/firmware/protocol applicability;
- sanitization checklist and confirmation that no secret or private deployment
  identifier remains;
- claim disposition `PROVEN`, `HYPOTHESIS`, or `UNKNOWN`;
- file paths and SHA-256 hashes; and
- expected result or expected fail-closed disposition.

Only `PROVEN` evidence may admit an automatic profile behavior.
`HYPOTHESIS` and `UNKNOWN` fixtures remain research or negative-test material.
Restricted source material is not copied into a public fixture.

### Deterministic Replay

Replay is offline and transport-neutral. Given the same fixture and exact
implementation versions, it MUST reproduce:

- request and response codec outcome;
- detector result and ordered evidence;
- qualification result;
- documentary normalization;
- each physical request and `wire_response_id`;
- each logical view and exact words/provenance;
- generation and dependency-set identity;
- retry, admission, unit-service, and jitter ordering;
- coherence or torn-read outcome; and
- the exact profile observation or fail-closed result.

Wall-clock time, map iteration, process identity, network availability, and
registration order MUST NOT change the result.

### Required Mutations

The conformance harness includes, at minimum:

| Mutation | Required result |
| --- | --- |
| malformed PDU/ADU length and trailing bytes | reject |
| FC03/FC04 alias attempt | reject |
| exception for unrelated request function or response-shape mismatch | reject |
| correlated protocol exception | deliver typed exception with wire response identity; do not time out |
| correlated malformed response | retain malformed wire response identity; emit no logical view |
| Device Identification stream starts from nonzero object | reject before transport write |
| completed stream omits a mandatory basic object | reject aggregate |
| Device Identification cursor cycle, duplicate, non-progress, or overflow | reject aggregate |
| unequal overlapping compatible reads | coalesce; every logical view replays exact words and provenance |
| cross-unit reads | refuse coalescing |
| cross-table or cross-function reads | refuse coalescing |
| cross-authorization reads | refuse coalescing |
| cross-generation reads | refuse coalescing |
| deadline-incompatible reads | refuse coalescing |
| TCP tombstoned identifier reuse | reject until controlled generation rollover |
| late response matching a TCP tombstone | retain `late_after_abandonment` wire identity and bytes; never deliver |
| old-generation or unmatched TCP response | drop |
| one admission key exhausts its protected and shared capacity | another key still activates, admits its protected request, and receives round-robin service |
| one authorization scope saturates a unit's dependents | another scope retains its own bounded capacity |
| replay runs in fresh processes | identical jitter, retry, admission, and output sequence |
| response, cancellation, and deadline share a clock offset | recorded event sequence yields one identical outcome |
| one coalesced dependent cancels after write | detach it; emit no logical view while active dependents may complete |
| final coalesced dependent cancels after write | enter the transport-specific abandonment path |
| RTU late same-shape frame during quarantine | discard |
| RTU response races quarantine transition | serialized event order either completes the old request or discards under quarantine, never reaches a successor |
| RTU quiescence failure | disable and recover endpoint |
| word-order, byte-order, signedness, scale, string-padding mutation | match only the declared codec |
| address-base off-by-one mutation | reject or produce the declared negative result |
| mixed poll generation or dependency set | torn/invalid sample |
| partial detector evidence | insufficient, never activate |
| multiple eligible profiles | ambiguous, never priority-select |
| fixture-only profile without opt-in | disabled |
| fixture-only profile with opt-in | experimental only; all gates still apply |
| qualification mismatch, revocation, or demotion | disable/fail closed |

The harness MUST report unexpected pass, unexpected fail, and skipped required
rows as failures. A transport or profile may remain disabled while its required
rows fail; passing transports and unrelated profiles remain independently
available.

### Required Transport Recovery Matrix

`FMV3-M1-04` owns the following stable row identifiers. Every row is required;
an absent, skipped, unexpected-fail, or unexpected-pass row fails the matrix.

| Row | Required proof |
| --- | --- |
| `tcp_provable_zero_no_abandonment` | zero transmission does not abandon the connection or identifier |
| `tcp_partial_write_close_reconnect` | partial transmit tombstones, closes, reconnects, and increments generation |
| `tcp_indeterminate_error_close_reconnect` | indeterminate transmit follows the same unsafe-stream recovery |
| `tcp_cancellation_race_close_reconnect` | cancellation race cannot preserve the old stream |
| `tcp_ambiguous_completion_close_reconnect` | ambiguous completion cannot preserve the old stream |
| `tcp_full_transmit_timeout_tombstone` | timeout tombstones the identifier; a late match retains request-bound provenance without delivery |
| `tcp_full_transmit_cancellation_tombstone` | cancellation tombstones the identifier; a late match retains request-bound provenance without delivery |
| `tcp_same_socket_tombstone_reuse_rejected` | a tombstoned numeric ID is unavailable for that socket lifetime |
| `tcp_tombstone_exhaustion_controlled_rollover` | exhaustion closes cleanly and increments generation before reuse |
| `tcp_old_generation_late_frame_rejected` | an old-generation frame cannot satisfy a current waiter |
| `rtu_provable_zero_no_abandonment` | proven zero transmit does not enter quarantine |
| `rtu_partial_write_quarantine` | partial transmit enters quarantine before any successor |
| `rtu_indeterminate_error_quarantine` | indeterminate transmit enters quarantine |
| `rtu_cancellation_race_quarantine` | cancellation race enters quarantine |
| `rtu_ambiguous_completion_quarantine` | ambiguous completion enters quarantine |
| `rtu_full_transmit_timeout_quarantine` | timeout after full transmit enters quarantine |
| `rtu_full_transmit_cancellation_quarantine` | cancellation after full transmit enters quarantine |
| `rtu_late_same_shape_discarded` | a late valid-looking frame is discarded during quarantine |
| `rtu_quiescence_failure_endpoint_recovery` | failure to prove idle disables and recovers the endpoint |

The same matrix includes bounded FC2B/MEI0E framing, segmentation, exception,
and malformed-response cases over both TCP and RTU. Stress cases MUST reach
each configured queue, correlation, tombstone, aggregation, and dependent-view
bound without unbounded memory, starvation, identity reuse, or cross-request
delivery.

## Security And Resource Invariants

- Every parser allocates only after validating declared lengths against fixed
  and configured bounds.
- Arithmetic on offsets, counts, byte lengths, and slices is checked before
  conversion or allocation.
- Authorization scope is part of admission and coalescing identity.
- Raw diagnostic errors MUST NOT include credentials or private endpoint
  configuration.
- Profile fixtures and evidence MUST pass sanitization and license validation.
- No network response alone changes executable configuration or loads code.
- No phase-one API can construct or transmit a write PDU.

## Implementation And Review Gates

`FMV3-M1-01` through `FMV3-M2-03` MUST:

1. link this companion and its merged commit;
2. begin with a CI-observed test-only RED commit, except documentation-only
   corrections;
3. map tests to the relevant rows in this contract;
4. keep runtime and profile packages independently testable;
5. pass all applicable local CI, protocol, transport, recovery, security,
   licensing, and adversarial review gates; and
6. retain explicit disabled dispositions for unavailable hardware.

Each dependent repository commits a machine-readable companion lock containing
the exact repository, full 40-character merged docs commit, companion contract
ID/version/content revision, and SHA-256 of the canonical manifest bytes. The
closed schema is
[`schemas/modbus-companion-consumer-lock-v1.schema.json`](./schemas/modbus-companion-consumer-lock-v1.schema.json).
Its local and hosted CI check out the public docs repository at the exact locked
commit and invoke `scripts/validate_modbus_companion.py --root <docs-root>
--consumer-lock <consumer-lock> --docs-commit-sha <locked-sha>` before
implementation tests run.
The lock MUST reside outside the docs checkout. The validator independently
requires the canonical GitHub `origin`, requires the docs checkout's full
`HEAD` to equal the lock, and rejects tracked or untracked modifications. It
also fetches canonical GitHub `main` by fixed HTTPS URL into a fresh bare
repository and protected validation ref, with global/system Git configuration
disabled, then proves that the locked SHA is its ancestor. Local remote-tracking
refs and URL rewrite configuration are not ancestry authorities.
The first implementation PR in each of
`helianthus-modbus` and `helianthus-modbusreg` MUST add this gate; later M1/M2
PRs MUST retain it and update the lock only for an accepted contract revision.
CI rejects a missing or additional field, short or moving ref, unknown version,
wrong repository or contract identity, stale content revision, or manifest
digest mismatch. Branch names, tags, and "latest" cannot satisfy the lock.

The documentation licensing gate classifies every changed Modbus artifact:

- implementation-neutral wire facts MUST be under `protocols/modbus/` and are
  covered by `protocols/LICENSE` (CC0-1.0);
- Helianthus scheduling, recovery, provenance, profile, and qualification
  policy MUST be under `docs/platform/` (AGPL-3.0); and
- copied upstream specifications, restricted vendor material, or neutral wire
  facts placed in the AGPL platform file fail the gate.

`scripts/validate_modbus_companion.py` enforces the current artifact locations,
license declarations, source-link lane, operation/issue/recovery inventory,
and downstream pin schema. `scripts/ci_local.sh` runs its positive and mutation
tests. Review still classifies new facts that no marker-based validator can
understand, and cannot weaken the machine gate.

For contract version 1, the manifest and validator also pin the exact SHA-256
of the normative policy and CC0 wire artifacts. Pull-request CI supplies the
trusted base checkout to the validator. If a prior manifest exists and the
contract version is unchanged, changed normative artifact hashes require
exactly the next `content_revision`; an unchanged artifact set requires the
same revision. A revision cannot decrease or skip. A new contract without a
prior manifest starts at revision 1. A contract-version change requires an
explicit validator/schema update and is rejected by this V1 validator until
that update exists.

The prior-state comparison is independent of editable in-tree expected-hash
constants. A coordinated edit to policy, manifest, and validator that leaves
the revision unchanged therefore fails against the trusted base. The trusted
revision workflow is canonical JSON and pins the full commit recorded at
`trust_anchor.commit_sha` in the companion manifest from
`Project-Helianthus/helianthus-execution-plans`. It executes
`scripts/validate_modbus_docs_trust.py` from that immutable checkout, not code
from this repository. The local transition validator is a byte-identical
mirror. The external anchor treats the head checkout only as bounded untrusted
data, validates the workflow object exactly, pins the semantic validator and
the normalized V1 contract, and makes all three protected files immutable
after bootstrap. A head change cannot remove, repin, or replace that
invocation. Changing V1 requires a new independently reviewed trust anchor;
every accepted normative byte change also requires matching
mutation-test and downstream-lock updates. Rewording a safety rule without the
required revision transition fails CI.

This first-publication PR has no prior Modbus manifest, so its bootstrap is
certified by local/hosted CI and fresh adversarial review. Immediately after
that PR merges, `Modbus Trusted Revision` MUST be configured as a required
`main` status check and a verification PR MUST prove that exact context green.
The external gate
`runtime-gates/fronius-modbus-m1-admission.json` in
`helianthus-execution-plans/main` remains `BLOCKED_PENDING_DOCS_TRUST` until
GitHub live evidence proves this docs PR merge, the required-check setting, its
successful verification check run, and the pinned anchor workflow. The plan
validator rejects `FMV3-M1-01` through M3 while that gate is not `OPEN`.
`FMV3-M1-00` is not complete and `FMV3-M1-01` MUST NOT start before the
evidence-bearing gate-opening PR merges.

The transport matrix for M1 is not the eBUS T01..T88 matrix. M1 must create a
Modbus-neutral matrix covering every TCP and RTU recovery row named by
`FMV3-M1-04`, including FC2B/MEI0E on both transports. It must have no
unexpected failure or unexpected pass.

## Traceability

| Contract area | First implementation issue |
| --- | --- |
| strict PDU types, FC03/FC04, exceptions, FC2B/MEI0E | `FMV3-M1-01` |
| TCP ownership, scheduler, correlation, coalescing, recovery | `FMV3-M1-02` |
| RTU framing, timing, quarantine, qualification disposition | `FMV3-M1-03` |
| transport conformance and recovery matrix | `FMV3-M1-04` |
| profile, codec, observation, provenance, and coherence | `FMV3-M2-01` |
| detector, probe, activation, and qualification lifecycle | `FMV3-M2-02` |
| fixture, replay, mutation, and licensing harness | `FMV3-M2-03` |

This contract belongs to cruise run
[`helianthus-execution-plans#71`](https://github.com/Project-Helianthus/helianthus-execution-plans/issues/71)
and documentation issue
[`helianthus-docs-ebus#373`](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/373).
The execution authorization hard-stops before `FMV3-M4-01`; nothing on this
page authorizes gateway implementation.
