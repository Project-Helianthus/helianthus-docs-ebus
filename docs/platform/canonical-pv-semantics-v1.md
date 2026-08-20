# Canonical Photovoltaic Semantics V1

## Status And Ownership

This is the pre-implementation contract for `helianthus.canonical-pv/v1`.
It does not claim a runtime implementation, a supported inverter, or consumer
availability. `helianthus-ebusreg` owns the canonical fact identity, value,
unit, quality, availability, freshness, continuity, and provenance rules.

`helianthus-modbusreg` owns source-model decoding and qualification. The
gateway owns acquisition and composition, but it must not redefine canonical
freshness, source precedence, or accumulator continuity. Private bindings may
later consume only the packaged `PUBLIC_GRAPHQL_M2M_V1` surface after its own
promotion gate.

## Separation Of Concerns

The following terms are deliberately distinct:

- a **model** is one source schema occurrence, such as SunSpec model 103;
- a **model chain** is the ordered, terminal-verified source inventory;
- a **source capability profile** states what a qualified source observation
  can provide, independently of vendor flavor;
- a **vendor flavor** records evidence-backed detection or decoding quirks;
- a **canonical capability pack** is a protocol-independent minimum set of
  facts and dimensions.

Historical source IDs `sunspec.phase1@1.0.0` and
`sunspec.inverter.three_phase.monitoring@1.0.0` retain those meanings. They are
not aliases for this canonical contract or its capability pack.

## Fact Envelope

A fact is identified by `(asset_ref, fact_id, dimensions)`. `asset_ref` is an
opaque stable reference; it is not an endpoint, network address, serial number,
or vendor register coordinate. Dimensions are a closed map whose keys and
values are declared by the fact catalog.

Each fact contains:

- a typed value: exact decimal coefficient and base-10 scale, enum, or
  bitfield; decimal coefficients are canonical integer strings and binary JSON
  floating-point values are forbidden;
- one canonical unit from `W`, `VA`, `var`, `V`, `A`, `Hz`, `Wh`, `Cel`, `1`;
- independent `quality`, `availability`, and `freshness` axes;
- per-fact receipt-based temporal data and the policy identifier that evaluated
  it;
- an `origin_ref` into the observation's closed provenance table, never raw
  words or endpoint material;
- continuity metadata when the fact is an accumulator.

The catalog is a rich union rather than a lowest-common-denominator schema.
Facts absent from one protocol remain unavailable; they are not discarded from
the canonical model or synthesized from unrelated source fields.

## State Axes And Freshness

Quality is `GOOD`, `SUSPECT`, or `BAD`. Availability is `AVAILABLE`,
`UNAVAILABLE`, or `UNSUPPORTED`. Freshness is `FRESH`, `STALE`, or `EXPIRED`.
These axes are not aliases and must not be collapsed into a single status.
The only V1 availability/freshness pairs are `AVAILABLE/FRESH`,
`AVAILABLE/STALE`, `UNAVAILABLE/EXPIRED`, and `UNSUPPORTED/EXPIRED`.

Freshness is evaluated from monotonic receipt time against the envelope's
`evaluated_monotonic_ns`; all monotonic values belong to the same runtime clock
domain. Source timestamps are evidence only and never drive expiry. V1 defines
these versioned product-policy profiles in `helianthus-ebusreg`:

| Policy | Fresh through | Retain through |
| --- | ---: | ---: |
| `pv.telemetry.fast.v1` | 30 s | 300 s |
| `pv.status.v1` | 60 s | 600 s |
| `pv.accumulator.v1` | 900 s | 86400 s |
| `pv.rating.v1` | 86400 s | 2592000 s |

A valid observation publishes `AVAILABLE/FRESH`. Passing the fresh threshold
changes only freshness to `STALE`. A new accepted observation refreshes either
`AVAILABLE/FRESH` or `AVAILABLE/STALE` to `AVAILABLE/FRESH`. Passing the retain
threshold publishes `UNAVAILABLE/EXPIRED` while retaining identity and
provenance. A source error must not wholesale-delete the prior observation. A
later accepted observation may return to `AVAILABLE/FRESH` with a new
generation.

V1 binds one selected source observation to one update. If multiple eligible
sources remain ambiguous, publication fails closed. Any future source
precedence policy requires a versioned canonical successor; gateway scheduling
order is never precedence.

## Production Acquisition Lifecycle

The gateway production path is a continuous read-only acquisition owner, not a
startup-only qualification harness. When Modbus and the admitted SunSpec
capability are enabled, it performs one immediate bounded acquisition and then
starts each later acquisition 15 seconds after the previous attempt finishes.
Only one acquisition may be in flight. The complete acquisition cycle,
including its one permitted reconnect and retry, has one shared 10-second
deadline. Every wire attempt receives new positive poll-generation and
deadline identities. Cancellation joins the worker before the Modbus adapter
closes.

The 10-second total cycle bound plus the 15-second post-cycle delay keeps
consecutive successful receipts below the 30-second fresh window of
`pv.telemetry.fast.v1`; a healthy source can therefore keep telemetry fresh
without changing the registry-owned policy. A failed read, reconnect, decode,
qualification, or publication attempt does not create a partial update and
does not rewrite the current semantic slot. The prior accepted observation
remains queryable and advances naturally through `FRESH`, `STALE`, and
`EXPIRED` according to this contract. A later accepted acquisition publishes a
new generation and returns its facts to `FRESH`.

Current semantic publication and immutable diagnostic evidence have separate
bounded ownership. The initial terminal qualification may remain addressable
through the exact profile/sample MCP contract. Later periodic acquisitions
replace only the current semantic slot for the same `asset_ref`; they do not
consume, evict, alias, or overwrite the immutable retained-observation budget.
An immutable-retention capacity limit therefore cannot stop healthy current
publication. The current slot remains detached from callers and must still
carry complete source provenance and projection accounting.

No worker exists when Modbus is disabled. Every acquisition executes only the
immutable bounded read plan admitted by the selected capability and flavor;
the current Fronius phase-one plan is FC03-only. FC04 is unavailable unless a
future versioned profile explicitly admits it. The worker never issues a
Modbus write function or changes inverter configuration.

## Source Admission And Provenance

Canonical publication requires a source observation admitted by its owning
profile registry. Provenance records the source protocol, profile identifier
and version, source-validity state, source observation reference, source shadow
reference, source-registry reference, and evidence reference. Protocol and
profile identifiers are source-registry-owned and extensible without changing
canonical V1 facts; the profile version must match its versioned source ID, and
the registry binding is an opaque digest resolved against a required
source-owned registry entry for the exact `(protocol, profile ID, profile
version, validity)` tuple. References are opaque hashes or handles.
Endpoint addresses, credentials, raw Modbus words, and private fixture paths are
forbidden from the canonical envelope.

The source shadow remains source-owned and lossless enough for deterministic
replay. Canonical projection records whether each requested output was
`MAPPED`, `WITHHELD`, or `UNREPRESENTABLE` against an opaque digest reference;
it never publishes a register path or endpoint. `MAPPED` requires a non-null
fact ID and dimensions matching the complete identity of a fact in the same
observation, while the two loss outcomes require a null fact ID and null
dimensions. Each row is uniquely identified by `(source_ref,
requested_output_ref)` so conflicting outcomes cannot be order-dependent.
For `MAPPED`, `source_ref` equals the mapped fact's `origin_ref`, which must
resolve in `origins[]`. For `WITHHELD` and `UNREPRESENTABLE`, `source_ref` equals
the current acquisition's `source_observation_ref`.
The mandatory `requested_outputs` inventory contains the same complete identity
set as `projection_report`; exactly one outcome is required for every requested
output. Every published fact also has exactly one `MAPPED` row with its complete
fact identity and `origin_ref`; empty, partial, surplus, or duplicate accounting
fails closed. Absence must not be silently converted to zero.

`source_provenance` describes the current acquisition. `origins[]` contains
every exact source provenance record still referenced by a fact. A retained
fact keeps its prior `origin_ref` when a later partial acquisition updates only
other facts; the root current source never rewrites retained provenance.
Opaque dimension identifiers are also redacted identifiers and must not contain
an IP address, URL, or host-and-port endpoint.

## Accumulator Continuity

Accumulator observations have exactly one continuity state:
`BASELINE`, `CONTIGUOUS`, `ROLLOVER`, `RESET`, or `DISCONTINUITY`.

- the first accepted value is `BASELINE` and has no delta;
- a nondecreasing value with coherent identity is `CONTIGUOUS`;
- `ROLLOVER` requires an explicit source modulus and a verifiable boundary;
- `RESET` requires explicit source reset evidence;
- any unexplained decrease, identity change, or observation gap is
  `DISCONTINUITY` with no inferred delta.

The registry must never guess rollover or reset merely because a counter
decreased. Delta and modulus use the same exact decimal representation and
canonical unit as their fact, including an independent base-10 scale.

## Three-Phase Telemetry Capability

`helianthus.pv.inverter.three_phase.telemetry.v1` requires:

- total active AC power and AC frequency;
- AC current for phases `L1`, `L2`, and `L3`;
- line-to-neutral AC voltage for phases `L1`, `L2`, and `L3`;
- lifetime active-export energy;
- inverter operating state.

The pack is independent of wire encoding. An admitted SunSpec `1+103` chain
and an admitted `1+113` chain can satisfy the same pack when all required
canonical facts are present with compatible units and dimensions.
Pack satisfaction is structural, not a freshness claim: a required fact may be
`AVAILABLE` or retained `UNAVAILABLE`, but never `UNSUPPORTED`. Capability IDs
are unique within an observation, and the reported outcome must equal the
derived structural result in both directions. Every capability pack declared
by V1 appears exactly once, including a negative `NOT_SATISFIED` result.

## Compatibility

Within V1, the fact catalog is closed: fact IDs, value kinds, unit meanings,
dimension meanings, enum meanings, and lifecycle transitions are immutable and
no additive facts or canonical enum values are accepted. Unknown source values
remain only in the source shadow until a successor canonical contract defines
them. Removing, adding, or reinterpreting a fact, changing a required
capability member, or changing a unit/dimension meaning requires a new contract
or capability pack identifier.

This contract grants no Modbus write authority and no Fronius support claim.
Consumer rollout remains MCP semantic prototype, GraphQL parity, Portal, Home
Assistant, and only then separately licensed private eeBUS/Matter bindings.

The machine-readable catalog is
[`manifests/canonical-pv-v1.json`](./manifests/canonical-pv-v1.json). The closed
observation envelope is
[`schemas/canonical-pv-observation-v1.schema.json`](./schemas/canonical-pv-observation-v1.schema.json),
with positive and mutation-based negative fixtures under
[`fixtures/canonical-pv/v1/`](./fixtures/canonical-pv/v1/).
The public validator requires a source-owned registry resolver conforming to
[`schemas/canonical-pv-source-registry-bindings-v1.schema.json`](./schemas/canonical-pv-source-registry-bindings-v1.schema.json);
the fixture directory contains only a conformance example, not a canonical
protocol allowlist.
