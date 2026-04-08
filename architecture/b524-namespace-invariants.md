# B524 Operations-First Invariants

> **Provenance:** Originally from `helianthus-vrc-explorer/docs/b524-namespace-invariants.md`.
> Rewritten for v0.2.1 to reflect the operations-first restructure (schema 2.3).
> This is the canonical architecture location; the VRC Explorer copy is the implementation-side mirror.

This document is the implementation-facing contract for B524 artifact structure and scanner behavior in the Helianthus VRC Explorer.

## Scope

- Applies to scanner planning/discovery, artifact schema, browse/report identity, and fixture migration.
- Covers register operations (`0x02`, `0x06`) and the `0x01` constraint probe scope decision.
- Uses `operation` (opcode) as the top-level structural axis; groups are nested within operations.

For the B524 wire protocol (independent of Helianthus implementation), see [`../protocols/ebus-vaillant-B524.md`](../protocols/ebus-vaillant-B524.md).

## Terminology Change (v0.2.1)

The term **namespace** is retired as a structural concept. Previous schema versions used "namespace" (or `dual_namespace`) to describe the relationship between opcodes and groups within a GG-first artifact layout. The operations-first restructure eliminates this indirection:

- **Old (schema <=2.2):** Groups are the top-level container. Each group optionally has `dual_namespace: true` and nested `namespaces` keyed by opcode. Identity path: `B524/<group-name>/<namespace-display>/<instance>/<register-name>`.
- **New (schema 2.3):** Operations (opcodes) are the top-level container. Groups are nested within their owning operation. No `dual_namespace` concept exists. Identity path: `B524/<section>/<operation>/<group-name>/<instance>/<register-name>`.

The word "namespace" may still appear in protocol-level documentation (where it describes wire-level opcode scoping) and in legacy compatibility code paths. In the artifact/scanner/architecture context, it is replaced by "operation."

## Invariants

1. **Operation-first identity is mandatory.**
   - Top-level structural key: `<operation>` (for example `0x02`, `0x06`).
   - Canonical register identity tuple: `(operation, group, instance, register)`.
   - Any GG-first layout that can merge or obscure operation boundaries is invalid.

2. **Discovery is advisory, not semantic authority.**
   - GG directory probe (`opcode 0x00`) results are evidence for discovery flow only.
   - Semantic identity, operation topology, and row identity are not derived from descriptor values.
   - **Ban:** GG discovery MUST NOT be used as semantic authority.

3. **Constraint scope is explicitly `operation_0x02_default`.**
   - Decision: `operation_0x02_default`.
   - Rationale: the bundled static catalog is seeded from `0x01` probe evidence, but it is only trusted for operation `0x02` by default.
   - Outcome: operation `0x06` does not inherit seeded static constraints unless a constraint entry explicitly scopes into that operation or a live probe confirms it.

4. **Artifact identity keys are operation-aware.**
   - Persisted topology authority: per-operation structure under `b524_operations`.
   - UI/report dedupe key contract: `<operation>:<group>:<instance>:<register>`.
   - Path contract: `B524/<section>/<operation>/<group-name>/<instance>/<register-name>`.

5. **Fixture compatibility is migration-based, not semantic rewrite.**
   - Current artifact schema: `2.3` (operations-first layout).
   - Legacy unversioned/`2.0`/`2.1`/`2.2` fixtures are migrated in-memory with register-count preservation.
   - Migration may normalize container shape, but must not drop register entries or collapse operation identity.
   - Legacy mixed-opcode single-group artifacts are rendered split-by-operation in browse/report consumers.

## Schema 2.3 Structure

The artifact JSON uses operations as the top-level axis:

```text
{
  "schema_version": "2.3",
  "b524_operations": {
    "0x02": {
      "groups": {
        "0x00": { ... registers ... },
        "0x01": { ... },
        "0x02": { ... instances ... },
        ...
      }
    },
    "0x06": {
      "groups": {
        "0x00": { ... },
        "0x09": { ... instances ... },
        ...
      }
    }
  },
  "meta": { ... }
}
```

Key structural properties:
- Each operation owns its group set independently.
- `GG=0x09` under operation `0x02` and `GG=0x09` under operation `0x06` are entirely separate entities with different register layouts, instance counts, and semantics.
- No cross-operation inheritance or merging is permitted.

## DT Byte (Reply Kind) Semantics

The DT byte (RK) is an effective 2-bit reply-kind field (`0..3`). The numeric domain is shared across operations, but bit0 semantics are operation-specific:

- **OP 0x02:** bit1=config, bit0=volatile/stable.
  - `0`: `simple_volatile`, `1`: `simple_stable`, `2`: `config_volatile`, `3`: `config_stable`
- **OP 0x06:** bit1=config, bit0=invalid/valid data.
  - `0`: `simple_invalid`, `1`: `simple_valid`, `2`: `config_invalid`, `3`: `config_valid`

Scanner artifacts expose `reply_kind` while preserving legacy `flags_access` labels for compatibility.

## Register Response State Classification

Register responses are classified into four wire-level states:

| State | Description |
|-------|-------------|
| `active` | ACK + FLAGS+GG+RR+VALUE (4+ bytes). Register is functional. |
| `empty_reply` | ACK + NN=0. Feature dormant. Rendered as "empty reply / dormant". |
| `nack_or_crc` | Transport-level negative outcome. NACK and CRC failure are indistinguishable via adapter transports. |
| `timeout` | No response within transport window. |

`error` is reserved for genuine transport/decode failures outside those four states.

## Protocol Notes Implemented In Explorer

These notes are scanner/register-map behaviors implemented in the VRC Explorer repository only. They are observational and do not replace the operation-first identity contract above.

1. **OP `0x06` generic device-header registers** (`RR=0x0001..0x0004`) are mapped experimentally. Group-specific rows (e.g., GG `0x09`/`0x0A` radio fields) remain authoritative when present; wildcard header rows are fallback only. On BASV2, the remote heat-source groups are 1-indexed (`GG=0x01` = primary, `GG=0x02` = secondary). `GG=0x00` remains local-only on BASV2 and should not be scanned as a remote operation.

2. **GG=0x09 is dual-use by operation.** OP `0x02`: local control/write-path registers (e.g., quick-mode write target). OP `0x06`: remote radio-device inventory/status registers. GG identity must never be merged across operations.

3. **Sentinel `0x7FFFFFFF`** is annotated when decoded as integer payload. This is scanner-layer annotation only; semantic/runtime policy belongs to gateway/poller repos.

4. **Canonical operation labels** are opcode-first:
   - `0x00`: `QueryGroupDirectory`
   - `0x01`: `QueryRegisterConstraints`
   - `0x02/0x00`: `ReadControllerRegister`
   - `0x02/0x01`: `WriteControllerRegister`
   - `0x03`: `ReadTimerProgram`
   - `0x04`: `WriteTimerProgram`
   - `0x06/0x00`: `ReadDeviceSlotRegister`
   - `0x06/0x01`: `WriteDeviceSlotRegister`
   - `0x0B`: `ReadRegisterTable`

## Scan Presets (v0.2.1)

The scanner supports 4 presets. The previous 6-preset model (which included `conservative` and `exhaustive`) is retired.

### `recommended` (default)

Per-(OP, GG) rules determine scanning behavior:

- **always_on:** Groups `0x00`-`0x01` (system, DHW) in OP=0x02; groups `0x04`-`0x05` (solar, cylinders) in OP=0x02. These are always scanned regardless of directory probe results.
- **present_gated:** Groups where directory probe or static topology indicates presence. Scanned at profile-defined register ranges and instance limits.
- **OFF:** Unknown or uncharacterized groups. Not scanned in recommended mode.

Known characterized groups per operation:
- **OP=0x02:** GG=0x00 through 0x05, 0x08, 0x09 (all characterized).
- **OP=0x06:** GG=0x00, 0x01, 0x08, 0x09, 0x0A, 0x0C (device slot registers).

### `full`

All groups from both operations. Normal `rr_max` bounds from the discovery profile. Full instance enumeration (II=0x00 through II=0x0A for instanced groups).

### `research`

All groups from both operations. Expanded `rr_max` bounds:
- Default: `0xFF` (256 registers per group).
- OP=0x02, GG=0x00: `0x1FF` (512 registers) -- this group is known to extend beyond 0xFF on BASV2.

Research mode is intended for register discovery and protocol analysis, not routine scanning.

### `custom`

Operator-defined group/operation/register selections. No preset rules applied.

## Historical Context

Issues #120 and #125 in the VRC Explorer repository remain useful exploratory context (how we reached the operation-first split from the original GG-first layout), but they are not active semantic authority. The active authority is:

- current code behavior in the VRC Explorer repository,
- tests/fixtures that validate it,
- and this invariants contract.

When historical notes conflict with current contract, follow current contract and open a corrective docs issue/PR.
