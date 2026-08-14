# Modbus Multi-Vendor Ownership And Licensing Boundaries

## Status

This page is the normative pre-implementation boundary contract for the
Helianthus Modbus work. It does not claim that the repositories, APIs, runtime
behavior, profiles, or bindings described below are implemented. An individual
capability becomes implemented only when its owning repository merges code and
tests for that capability.

The first implementation slice is Fronius-oriented, but the public architecture
is not Fronius-specific. It uses one Modbus runtime and one multi-vendor profile
registry so later SunSpec, Growatt, Huawei, and other profiles do not require a
repository per vendor.

## Repository Ownership

| Owner | Responsibility | Explicit exclusions |
| --- | --- | --- |
| `helianthus-modbus` | Modbus protocol data units; Modbus TCP and RTU transports; endpoint ownership; request scheduling; cancellation; timeout, quarantine, and connection recovery | Vendor register meaning, canonical energy semantics, policy for writes |
| `helianthus-modbusreg` | One versioned multi-vendor profile registry; codecs; detection plans; qualification; sanitized fixtures; standard families and vendor overlays | Sockets, serial-port ownership, Modbus framing, canonical publication policy |
| `helianthus-ebusreg` | Protocol-independent canonical identity, value semantics, units, quality, freshness, and observation provenance | Modbus transport mechanics and vendor register addresses |
| `helianthus-ebusgateway/internal/modbusadapter` | Future composition boundary between the public runtime, profile registry, and canonical registry | No implementation is authorized by this page; gateway work starts only in its separately authorized milestone |
| Public consumers | Future MCP-first raw and canonical views, followed by GraphQL and consumer rollout after semantic lock | Direct vendor-register interpretation |
| `helianthus-eebus-binding-private` | Future generic private eeBUS output binding; photovoltaic export is only its first planned slice | Any ingress other than the packaged `PUBLIC_GRAPHQL_M2M_V1` contract; owning public protocol facts; importing private knowledge into public builds |
| `helianthus-matter-binding-private` | Future generic private Matter output binding; photovoltaic export is only its first planned slice | Any ingress other than the packaged `PUBLIC_GRAPHQL_M2M_V1` contract; owning public protocol facts; importing private knowledge into public builds |

The allowed compile-time import direction is:

```text
helianthus-modbusreg ------> helianthus-modbus
          ^                         ^
          |                         |
          +---- future gateway -----+
                      |
                      +-----------> helianthus-ebusreg

public consumer or private output binding
                      |
                      +-----------> public canonical/API contract
```

`helianthus-modbusreg` may depend on public types from `helianthus-modbus`.
Neither public repository may import the gateway or a private binding. The
canonical registry must not import a vendor profile package. Composition owns
the translation between a qualified profile observation and the canonical
registry contract.

Arrows point from importer to imported owner. The future gateway composition
imports all three public owners; those owners do not import the gateway.

## Runtime And Profile Boundary

The runtime operates only on protocol-level requests and responses. Its request
identity includes every field needed to prevent unsafe sharing across endpoint,
transport generation, unit identifier, table/function, authorization context,
and incompatible deadlines. It returns exact raw words and request provenance;
it does not assign vendor meaning to those words.

The profile registry consumes an abstract read interface owned by the runtime.
A profile may:

- declare register ranges and codecs;
- declare an ordered, bounded detection plan;
- qualify a candidate by model, firmware, gateway, and other documented gates;
- normalize raw words into typed profile observations;
- attach the exact profile version and source observation provenance.

A profile may not open a socket, configure a serial port, construct transport
frames, or bypass the runtime operation allowlist. Unsupported detector
operations make that profile ineligible; they are not an excuse to duplicate
protocol framing in the registry.

## Standard Families And Vendor Overlays

A **standard family** represents semantics defined by a public standard, such
as a supported SunSpec model. It must remain free of vendor assumptions.

A **vendor overlay** contains only evidence-backed differences needed for a
specific vendor, product, gateway, or firmware branch. An overlay may refine
detection, applicability, address normalization, or a documented quirk. It may
not duplicate a standard model merely to attach a vendor name.

Fronius support should therefore use the minimal applicable SunSpec standard
family first. A Fronius overlay is added only when admissible evidence proves
that standard behavior is insufficient. Growatt and Huawei later use the same
registry and the same distinction. SmartLogger, EMMA, and S-Dongle are
applicability and detection dimensions inside Huawei profiles, not reasons to
create separate repositories.

[`fronius-sunspec-evidence-v1.md`](./fronius-sunspec-evidence-v1.md) records
the current M3-01 Fronius documentary boundary. Its terminal M3-03 disposition
is `STANDARD_ONLY`; the retained detector claim is a research `HYPOTHESIS`, not
a Fronius overlay, activation, or support claim. The generic
[`SunSpec model-chain contract`](../../protocols/sunspec/sunspec-model-chain-v1.md)
separates ordered model occurrences, capability profiles, and vendor flavors.
Its initial `sunspec.inverter.three_phase.monitoring@1.0.0` profile has no write authority and a future registry-selected outcome is required before any
vendor flavor can be evaluated.

Profiles are versioned and independently disableable. Failure or dispute in one
profile must not change the shared runtime or silently alter another profile.

## Claim Labels

Every protocol or vendor claim is assigned exactly one publication state:

| Label | Meaning | Permitted use |
| --- | --- | --- |
| `PROVEN` | Supported by admissible documentary evidence, a reproducible sanitized capture, or both, with applicability recorded | May drive a versioned profile and support statement within the recorded applicability |
| `HYPOTHESIS` | Plausible interpretation that still lacks sufficient evidence or reproducibility | May guide research and candidate fixtures; must not drive automatic qualification or a support claim |
| `UNKNOWN` | Evidence is absent, conflicting, out of scope, or cannot be published | Must fail closed; no inferred value, fallback profile, or support claim |

Conflicting `PROVEN` candidates are not resolved by priority or guesswork. The
affected claim becomes `UNKNOWN` until a documented disposition resolves the
conflict.

## Clean-Room Evidence Intake

Every evidence packet must record:

1. **Source**: stable document identifier, capture identifier, or reproducible
   acquisition procedure.
2. **Permission and license**: why the material may be inspected and what may
   be republished.
3. **Transformation**: how a source statement or capture became a register,
   codec, detector, or applicability claim.
4. **Applicability**: vendor, product, gateway, hardware, firmware, protocol
   mode, address base, and known exclusions.
5. **Sanitization**: removal of credentials, private addresses, serial numbers,
   customer identifiers, and unrelated payloads.
6. **Disposition**: `PROVEN`, `HYPOTHESIS`, or `UNKNOWN`, including conflicts
   and unresolved questions.
7. **Code mapping**: exact profile version, fixture, detector, or codec that the
   evidence permits.

Documentation may be analyzed again from its authoritative source even when a
prior project produced useful notes. Prior notes are leads, not automatically
admissible facts. Sanitized, reproducible conclusions may be published; source
material whose license forbids redistribution must not be copied into public
fixtures or documentation.

Fixtures must contain the minimum bytes and metadata required to reproduce a
claim. They must not contain secrets or private deployment identifiers.

## Licensing Lanes

`helianthus-modbus` and `helianthus-modbusreg` are public Helianthus
implementation repositories and use `AGPL-3.0`, consistent with the current OSS
core. Their source files, implementation-specific tests, and architecture notes
remain in that lane unless an individual file clearly states another compatible
license.

Implementation-neutral wire formats, register maps, and value semantics
accepted into the public protocol-documentation lane use `CC0-1.0`. A source
document or capture is not relicensed merely because a Helianthus conclusion is
published: only the independently authored, admissible protocol fact or
sanitized fixture enters the declared public lane.

Private bindings use their own separately approved license. That different
license does not change the license of imported Helianthus public components,
remove their notices, or permit public implementation and protocol knowledge to
move into a private-only evidence lane.

## Public And Private Direction

Public repositories are independently buildable and testable without access to
any private repository, package registry, fixture, CI secret, or source tree.
Public contracts are the only permitted dependency surface for private
bindings.

```text
packaged PUBLIC_GRAPHQL_M2M_V1
              |
              v
    private output binding
```

This packaged GraphQL contract is the private bindings' only semantic ingress.
They must reject direct imports or network paths to `helianthus-modbus`,
`helianthus-modbusreg`, gateway internals, and undocumented endpoints. The
contract is consumed through authenticated, bounded query/polling with
compatible-version enforcement, least-privilege noninteractive credentials,
confidential transport, verified server identity, and credential
lifecycle/recovery. Plaintext, untrusted identity, GraphQL subscriptions, and
incompatible contract versions fail closed.

The reverse dependency is forbidden. A finding made while developing a private
binding may affect public behavior only after it is converted into a sanitized,
licensed public evidence packet and accepted through the normal public
doc-gate. A private test result or private-only protocol fact cannot establish
public support.

Creation and implementation of both private binding repositories are deferred
to separately authorized work. Their names describe generic output targets, not
photovoltaic-only products.

## Phase-One Operation Allowlist

The first public runtime slice is read-only. Its complete operation allowlist is:

- FC03, Read Holding Registers;
- FC04, Read Input Registers;
- FC2B/MEI type 0x0E, Read Device Identification.

The detailed framing, bounds, exception, segmentation, recovery, and
coalescing contracts belong to the separately gated Modbus foundation
companion. Until that contract and implementation are merged, this list is a
scope boundary rather than an implementation claim.

Implementation-neutral framing and operation facts are owned in the CC0
[`protocols/modbus/modbus-phase-one-wire-v1.md`](../../protocols/modbus/modbus-phase-one-wire-v1.md)
artifact. Helianthus scheduling, recovery, provenance, profile, and
qualification policy remains in the AGPL platform companion.

There is no generic write escape hatch. FC05, FC06, FC0F, FC10, FC16, FC17,
vendor write operations, and profile-authored arbitrary function codes are
outside phase one.

## Write Deferral

Writes require a separate safety plan and authorization. That plan must define,
at minimum:

- an explicit per-profile write allowlist;
- value bounds, units, scaling, and read-before-write preconditions;
- authorization and operator-intent boundaries;
- idempotency and retry behavior;
- device/gateway/firmware applicability;
- audit evidence and post-write verification;
- cancellation, partial-transmit, timeout, and ambiguous-completion behavior;
- rollback or safe-stop behavior.

Read support does not imply write support. A writable register in vendor
documentation remains non-writable in Helianthus until the separate plan is
implemented and validated.

## Enforcement

Each implementation PR must:

- name the owning repository and remain inside the boundaries above;
- link the admissible evidence for every new profile fact;
- keep `HYPOTHESIS` and `UNKNOWN` out of automatic qualification;
- preserve public-only build and test paths;
- use the MCP-first lifecycle before stable consumer rollout;
- pass the repository CI and all applicable doc, protocol-interoperability,
  licensing, security, and adversarial review gates.

Changes in the Modbus companion surface are additionally checked by the
required `Modbus Trusted Revision` status. That check executes the base-owned
workflow under `pull_request_target`, checks out the proposed head only as
untrusted data, and validates the transition with the immutable external anchor
recorded in the companion manifest. The protected workflow and validators must
not be executed from the proposed head.

Any proposed gateway composition or private binding change is outside this
pre-gateway contract and requires its own execution authorization.
