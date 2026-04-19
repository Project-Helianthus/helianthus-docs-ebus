# Provider Contract

Status: Normative
Milestone: M3_PROVIDER
Plan reference: ebus-standard-l7-services-w16-26.implementing/00-canonical.md
Canonical SHA-256: 9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305

## Purpose

This chapter freezes the runtime-level contract of the generic
`ebus_standard` provider delivered in `helianthus-ebusreg` under
milestone `M3_PROVIDER`. It is the companion to the M0 policy
documents (`00-namespace.md`, `05-execution-safety.md`,
`07-identity-provenance.md`) and defines what the provider exposes,
how its shape is protected against drift, and how it can be disabled
in production without a rebuild.

The canonical plan states:

> `ebus_standard` is a new L7 provider namespace for Helianthus that
> carries the official eBUS Application Layer standard services. It is
> a cross-vendor, catalog-driven surface applicable to any
> eBUS-conformant device. It runs in parallel with the existing
> Vaillant `0xB5` provider namespace and does not reuse
> Vaillant-specific logic.

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.implementing/00-canonical.md`,
SHA-256 `9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

## Provider Surface

The generic `ebus_standard` provider is:

1. A single provider registered under a stable plan name in the
   Helianthus registry.
2. Catalog-driven. Every method it exposes is generated from the
   `ebus_standard` catalog data file frozen in M2 (see
   [`01-services-catalog.md`](./01-services-catalog.md)) using the
   identity key model in
   [`00-namespace.md`](./00-namespace.md#catalog-identity-key).
3. Cross-vendor. It carries no Vaillant-specific path, alias, quirk,
   or manufacturer heuristic. Enforcement of this property is the
   Cross-Namespace Import Invariant in
   [`00-namespace.md`](./00-namespace.md#cross-namespace-import-invariant).
4. Default-deny at invocation. `provider.Invoke()` is the runtime
   enforcement boundary defined in
   [`05-execution-safety.md`](./05-execution-safety.md#runtime-enforcement);
   the sentinel `ErrSafetyClassDenied` is its denial signal.

The gateway `rpc.invoke` boundary, generated provider methods, and NM
runtime share the same execution-policy module; see
[`05-execution-safety.md#policy-module-single-source`](./05-execution-safety.md#policy-module-single-source).

The provider does NOT:

- Hard-code per-device behaviour.
- Invent service variants not present in the catalog.
- Overwrite `DeviceInfo` fields (see
  [`07-identity-provenance.md`](./07-identity-provenance.md#non-overwrite-rule)).
- Carry or resolve Vaillant `0xB5` semantics.

## ABI Snapshot Stability

The exported symbol set of the generic `ebus_standard` provider is a
public contract. Consumers (gateway MCP surfaces, responder runtime,
namespace-isolation tests, audit tooling) depend on it. Drift in this
surface MUST surface as a CI diff failure, not as a silent consumer
break.

### Golden Fixture

A golden fixture records the exported ABI of the generic provider:

- Fixture path (in `helianthus-ebusreg`):
  `catalog/ebus_standard/testdata/provider_abi.golden.txt`.
- Content: a deterministic rendering of exported symbols relevant to
  the provider surface (exported types, functions, methods, constants,
  and sentinel errors including `ErrSafetyClassDenied`).
- Determinism: the rendering MUST be stable across platforms and Go
  toolchain patch versions. Nondeterministic output is a defect, not
  an expected fixture update.

Cross-repo pointers inside `helianthus-docs-ebus` are documentation
only. The authoritative fixture lives in `helianthus-ebusreg`; this
chapter documents its contract.

### Snapshot Test

A snapshot test under the generic-provider package:

- Test path (in `helianthus-ebusreg`):
  `catalog/ebus_standard/provider_abi_snapshot_test.go`.
- Behaviour: renders the current exported surface, diffs against the
  golden fixture, fails on any mismatch.
- Failure mode: reports the diff in CI output with enough context for
  a reviewer to classify the change as intentional or regression.

### Update Policy

A golden-fixture change is a deliberate ABI change. The following
rules apply:

1. Any change to `provider_abi.golden.txt` MUST be accompanied by a
   PR-body rationale naming which exported symbol changed, why, and
   its downstream consumer impact (registry, gateway MCP, responder,
   portal, HA).
2. A reviewer signoff on the rationale is required before the fixture
   update merges. An unreviewed "regenerate the golden" commit is not
   an acceptable update path.
3. Backwards-incompatible changes (rename, remove, retype of an
   exported symbol) MUST be flagged explicitly and cross-linked to the
   locked-plan decision authorising them, per
   [`05-execution-safety.md`](./05-execution-safety.md#no-runtime-widening).
4. A rationale-free fixture update is grounds for revert.

### Scope

The ABI snapshot protects the generic `ebus_standard` provider surface
exported from `helianthus-ebusreg`. It does NOT replace:

- The `M4B_read_decode_lock` envelope lock in
  `helianthus-ebusgateway`.
- The identity-key collision test on the catalog itself.
- The namespace-isolation tests that prove Vaillant `0xB5` and
  `ebus_standard` do not contaminate each other.

These are separate contracts enforced in their own repos.

## Disable Switch

The generic `ebus_standard` provider ships with a runtime-controlled
disable switch so that operators can revert to pre-provider behaviour
without rebuilding the gateway binary.

### Environment Variable

- Name: `EBUS_STANDARD_PROVIDER_ENABLED`.
- Default value: enabled.
- Effect: when the value resolves to a disabled state, the generic
  `ebus_standard` provider MUST NOT serve catalog-driven invocations.
- Mechanism: runtime flag, consulted at provider entry. Not a build
  tag. Not a compile-time constant. Not a registry record.

### Rationale for Runtime Mechanism

A runtime flag was selected over a build tag for two reasons:

1. Live kill-switch: production operators can disable the provider
   without issuing a new build or coordinating a deployment. This
   matters during incident response, when rebuilding is the wrong
   primitive.
2. Scope containment: the flag must affect only the generic
   `ebus_standard` provider path. Build-tag isolation would risk
   excluding unrelated code whose absence would mask other failures.

### Blast Radius

When the flag resolves to disabled:

1. The generic `ebus_standard` provider returns a documented disabled
   error to any invocation it receives. The concrete error name is an
   implementation detail of `helianthus-ebusreg`; the contract
   documented here is that the disabled condition MUST be a
   distinguishable, structured error, not a generic failure and not a
   silent no-op.
2. The Vaillant `0xB5` provider is unaffected. Vaillant decode, encode,
   and provider state continue regardless of the `ebus_standard`
   disable switch.
3. Gateway MCP surfaces that depend on the `ebus_standard` provider
   (for example `services.list`, `commands.list`, `command.get`,
   `decode` under the `ebus_standard` plan) MUST surface the disabled
   state to callers in a structured way, not by returning stale or
   partial data.
4. The NM runtime's `system_nm_runtime` whitelist behaviour, defined
   in
   [`05-execution-safety.md`](./05-execution-safety.md#system_nm_runtime-whitelist),
   is dependent on the provider path. Disabling the provider therefore
   disables the NM runtime's catalog-driven emit path; this is the
   expected kill-switch behaviour and MUST be visible in audit logs
   per
   [`05-execution-safety.md`](./05-execution-safety.md#audit-requirement).

### Out of Scope

The disable switch MUST NOT:

- Widen any accept set (see
  [`05-execution-safety.md`](./05-execution-safety.md#no-runtime-widening)).
- Alter Vaillant `0xB5` behaviour.
- Re-enable itself from within the provider based on any other
  runtime signal. The flag is one-directional: operator-controlled,
  process-scoped, observable.

## DeviceInfo Contract Preservation

The generic provider MUST NOT overwrite `DeviceInfo` identity fields.
Identification evidence produced by catalog decode of `0x07 0x04`
descriptors is stored with source labels and provenance per
[`07-identity-provenance.md`](./07-identity-provenance.md).

In particular:

1. A valid `0x07 0x04` descriptor results in an
   `ebus_standard.identification` evidence record with catalog
   identity, catalog version, frame metadata, timestamp, and
   validity.
2. Disagreements between `device_info` and
   `ebus_standard.identification` MUST be preserved with both source
   labels and `agreement=false`, per
   [`07-identity-provenance.md`](./07-identity-provenance.md#disagreement-handling).
3. The deterministic precedence rule in
   [`07-identity-provenance.md`](./07-identity-provenance.md#deterministic-precedence)
   applies at projection time, not at write time. The provider does
   not collapse sources.

## Related Documents

- [`00-namespace.md`](./00-namespace.md) — namespace boundary and
  cross-namespace import invariant.
- [`01-services-catalog.md`](./01-services-catalog.md) — catalog used
  to generate provider methods.
- [`05-execution-safety.md`](./05-execution-safety.md) — safety
  classes, default-deny policy, runtime enforcement boundary,
  `ErrSafetyClassDenied` sentinel.
- [`07-identity-provenance.md`](./07-identity-provenance.md) —
  identity provenance and `DeviceInfo` non-overwrite policy.
