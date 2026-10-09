# B524 Operations-First Invariants

> **Provenance:** Originally from `helianthus-vrc-explorer/docs/b524-namespace-invariants.md`.
> Rewritten for v0.2.1 to reflect the operations-first restructure (schema 2.3).
> This is the canonical architecture location; the VRC Explorer copy is the implementation-side mirror.

This document is the implementation-facing contract for B524 artifact structure and scanner behavior in the Helianthus VRC Explorer.

## Scope

- Applies to scanner planning/discovery, artifact schema, browse/report identity, and fixture migration.
- Covers register operations (`0x02`, `0x06`) and the `0x01` constraint probe scope decision.
- Uses `operation` (opcode) as the top-level structural axis; groups are nested within operations.

For the B524 wire protocol (independent of Helianthus implementation), see [`../protocols/vaillant/ebus-vaillant-B524.md`](../protocols/vaillant/ebus-vaillant-B524.md).

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

2. **System information guides qualified instance discovery.**
   - OP=00h uses an information identifier, independent of register GG.
   - Explicit profile mappings may supply bounded candidate guidance for
     non-exhaustive presets; they never invent II identities.
   - OP00/ID00 `circuit_count` and ID01 `zone_count` retain their legacy public
     names but are supported capacities, not configured or present-instance
     counts. Preserve raw float, capacity interpretation, presence results, and
     any unmet planning guidance separately.

3. **Descriptions are operation- and instance-scoped.**
   - OP=01h DescribeParameter describes the OP=02h system family.
   - OP=07h DescribeDeviceParameter describes the OP=06h device family.
   - Match the target/profile and complete `(operation,GG,II,RR16)` identity.
   - The historical short OP01 catalog is unqualified advisory data. It must not
     validate edits or be inherited across operations/instances.

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

## FLAGS Reply Attribute

The leading byte in an OP=02h/06h read response is retained as raw `FLAGS`.
The profile-scoped attribute interpretation uses bit 0 as a visibility/category discriminator and
bit 1 marks writable capability. This is profile-scoped inference, not a
universal wire meaning, live writability proof, or volatile/stable classification.
Scanner artifacts may expose a numeric `reply_kind` for compatibility, but they
must preserve the raw byte and must not derive semantic labels from it alone.

## Register Response State Classification

Register responses are classified into four wire-level states:

| State | Description |
|-------|-------------|
| `active` | ACK + FLAGS+GG+RR+VALUE (4+ bytes). Value-shaped reply pending codec qualification. |
| `empty_reply` | ACK + NN=0. Empty response; a profile may classify it as dormant only with correlated evidence. |
| `nack_or_crc` | Transport-level negative outcome. NACK and CRC failure are indistinguishable via adapter transports and do not prove absence. |
| `timeout` | No response within transport window. |

`error` is reserved for genuine transport/decode failures outside those four states.

## Protocol Notes Implemented In Explorer

These notes are scanner/register-map behaviors implemented in the VRC Explorer repository only. They are observational and do not replace the operation-first identity contract above.

1. **OP `0x06` generic device-header registers** (`RR=0x0001..0x0004`) are mapped experimentally. Group-specific rows (e.g., GG `0x09`/`0x0A` radio fields) remain authoritative when present; wildcard header rows are fallback only. The available public evidence does not qualify `GG=0x00` as a heat-generator route or establish its absence. Treat that namespace as uncharacterized when deciding a device-specific scan profile.

2. **GG=0x09 is dual-use by operation.** OP `0x02`: local control/write-path registers (e.g., quick-mode write target). OP `0x06`: remote radio-device inventory/status registers. GG identity must never be merged across operations.

3. **Sentinel `0x7FFFFFFF`** is annotated when decoded as integer payload. This is scanner-layer annotation only; semantic/runtime policy belongs to gateway/poller repos.

4. **Canonical operation labels** are opcode-first:
   - `0x00`: `ReadSystemInformation`
   - `0x01`: `DescribeParameter`
   - `0x02/0x00`: `GetParameter`
   - `0x02/0x01`: `SetParameter`
   - `0x03`: `ReadTimer`
   - `0x04`: `WriteTimer`
   - `0x06/0x00`: `GetDeviceParameter`
   - `0x06/0x01`: `SetDeviceParameter`
   - `0x07`: `DescribeDeviceParameter`
   - `0x08`: `ReadVR91`
   - `0x09/0x0A`: `GetEvent` / `SetEvent`
   - `0x0B/0x0C`: `GetEventSetPoint` / `SetEventSetPoint`

## Scan Presets (v0.2.1)

The scanner supports 4 presets. The previous 6-preset model (which included `conservative` and `exhaustive`) is retired.
They use one deterministic candidate policy and pure planner for UI and CLI.
This is an implementation-facing scanner contract, not universal B524 wire proof
or a claim that an unprobed selector is absent.

The Browser tree is a present-instance projection, not the candidate scan plan.
For the current profile, OP06 candidates use II01..II08; OP02/GG02 uses II01..II08
for heating candidates plus II09 for virtual native water. Do not render an
absent, unknown, or unprobed selector as a tree node. Preserve those outcomes in
the artifact so that the UI does not convert lack of a node into a claim of
physical absence.

### `recommended` (default)

This preset scans characterized OP=02/GG `00..05,08,09` and OP=06/GG
`01,02,03,05,06,07,08,09,0A,0B,0C,0E,0F` consistently. Connected-device enumeration follows the
[profile-qualified II01 policy](../development/ebus-vaillant-b524-explorer-discovery.md#op06-connected-device-discovery).
`recommended` also performs the dedicated OP06/GG0D II01..II08/RR0001
availability-only probe using `device_connected`. This does not admit an automatic
GG0D scalar range: other relay-module registers require an explicit manual RR scope,
and empty, malformed, or failed RR0001 replies remain unknown.
OP02/GG00 System is mandatory at II00, RR0000..00FF. Native DHW (OP02/GG01)
is admitted at II00 after its RR0001 gate succeeds with a nonzero UIN value.
The virtual native-water II09 remains a separate circuit candidate.
OP00 mappings guide candidates only when the profile declares one; every
resulting slot still needs its own presence predicate. ID00 `circuit_count` and
ID01 `zone_count` are supported capacities, never configured-instance counts or
II allocation. They do not make slots contiguous, and II09 remains independent.
Missing, invalid, conflicting, or unmet capacity uses that predicate without
itself making concrete presence qualification incomplete. Other OP00 count
mappings retain count-guided cardinality semantics: a valid zero suppresses
only derived defaults and never erases a positive observation; invalid counts
fall back to their group predicate. ID04 `device_count` compares all confirmed
OP06 slots and is never GG06, group membership, or a cutoff. GG03,
GG05, GG08, GG0A, GG0D, GG0E, and GG0F have no count mapping; neither do ID05
for a generator nor ID17 for a cooling group. Local ventilation uses ID16 only
for OP02/GG09 II00 in `recommended`.

### `full`

Audit every declared II slot in the characterized OP02 groups and OP06/GG
`01,02,03,05,06,07,08,09,0A,0B,0C,0E,0F` using normal profile `rr_max` bounds,
regardless of OP00 counts. OP02/GG00 is mandatory in this preset for II00 and
RR0000..00FF. OP06/GG04 and OP06/GG0D have Unknown RR maxima and receive no automatic
scalar scope. GG0D still receives its dedicated RR0001 presence probe; scanning
other registers requires a manual RR scope. GG04 has no qualified presence predicate. Counts are comparison evidence only; they neither suppress
selector generation nor provide topology identity.

### `research`

Use configured expanded but finite coverage for research; record configured,
skipped, and unknown coverage in the manifest. It uses multiple anchor probes
per family and does not let a failed first II=00/RR=0000 probe veto the rest of that group.
Research uses an explicit finite RR ceiling, default `0xFF`. OP02/GG00 also
uses `0xFF`; no default scan above it is justified by current observations. It
is intended for register discovery and protocol analysis, not
routine scanning.

### `custom`

An exact normalized plan of OP02/OP06 `(GG,II,RR16)` lists or bounded ranges.
The UI and CLI send the same plan to the planner; explicit selectors are never
allowed to widen the current profile II intervals: OP06 is II01..II08 and
OP02/GG02 is II01..II09. RR16 remains an exact scalar selector within the
normal request contract.
Explicit selectors are never presence-pruned. The CLI accepts a `--scan-plan` JSON file with
`schema_version: 1` and `groups: [{opcode, group, instances, registers}]`.
Only read selectors and wire-bounded values are accepted. Plans exceeding
100000 scalar requests fail before queuing.

## Description Scheduler and Send Budget

Descriptions are a second phase after value reads. By default every eligible
writable candidate in the selected scope is scheduled. `--description-budget`
is an optional, explicit caller limit. When supplied, half is initially reserved
for each description/read family (OP01/OP02 and OP07/OP06), borrowing unused share;
each family schedules eligible `(GG,II)` candidates round-robin. Eligibility
comes from profile-scoped writable-format inference and includes unknown codecs,
which are retained raw and reported unqualified. It does not prove a live write
or authorize one. Artifacts count `eligible`, `attempted`, `matched`,
`unavailable`, `unqualified`, and `budget_skipped`.

`--request-budget` optionally caps actual B524 sends, including retries. No
preset supplies a default send budget. Explicit budget exhaustion returns a
partial artifact marked
`incomplete`, never an absence verdict.

## Historical Context

Issues #120 and #125 in the VRC Explorer repository remain useful exploratory context (how we reached the operation-first split from the original GG-first layout), but they are not active semantic authority. The active authority is:

- current code behavior in the VRC Explorer repository,
- tests/fixtures that validate it,
- and this invariants contract.

When historical notes conflict with current contract, follow current contract and open a corrective docs issue/PR.
