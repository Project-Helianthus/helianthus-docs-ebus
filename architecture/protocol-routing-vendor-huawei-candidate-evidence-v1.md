# Huawei Gateway Candidate Evidence V1

## Status

FMV3-M7-01 treats SmartLogger, S-Dongle, and EMMA as three independent Huawei
proprietary-Modbus candidates. Each family is `DOCUMENTARY_CANDIDATE` and
ineligible until FMV3-M7-04 reaches either `PROFILE_ADMITTED` or
`NO_ADMISSIBLE_PROFILE` for that family. There is no family fallback, implied
priority, SunSpec claim, or Modbus write authority.

## Evidence Classes

Authoritative inputs, derived R&D, and live observations remain separate:

| Family | Huawei-authored source | R&D lead | Live status |
| --- | --- | --- | --- |
| SmartLogger | SmartLogger V300R024C10 ModBus Interface Definitions, Issue 54, 2026-02-06; converted MD SHA-256 `f00b197c84a581bfcaec95a1b6a959ab8f08c670a31ea3d27414f1f2b33bc794` | `wlcrs/huawei-solar-lib` commit `7927a68d30d86078c1366a4acae7887bc47e62da`, AGPL-3.0, design lead only | historical read-only snapshot proves SmartLogger plus eight addressed children; it does not prove MEI inventory |
| S-Dongle | SDongle V200R025C00SPC120 MODBUS Interface Definitions, Issue 01, 2025-12-23, SHA-256 `2806fac6a6176c3f815e8d8135f306b0bb585bcfed8770bfa822536fcf39ab1b`; TCP Guide Issue 05 SHA-256 `cc5b5c45e90d4607a6d79a4b5069632576731cb1165957bd120970a97ff45d47` | same clean-room research lead | no admitted live detector or child-inventory fixture |
| EMMA | SmartHEMS V100R024C00 MODBUS Interface Definitions, Issue 01, SHA-256 `7a989d2b8d031582ce1fad5766c0168b47b5a4ba2cf96dbd65085590d3308a5e`; SmartHEMS V100R025C00SPC102 MODBUS Interface Definitions, SHA-256 `89bafd5f74ef7516daeb4d5de0d4212245080d1d6d1b03d7482854d0fe5244ce` | same clean-room research lead | historical unit-0 telemetry is confirmed; detector tuple, MEI inventory, and overlap rejection are not |

The EMMA PDFs are Huawei-authored but were recovered from a community mirror,
not an official Huawei download URL. All vendor PDFs and converted tables are
inspection-only and are not redistributed. The closed manifest records stable
capture references, hashes, acquisition treatment, and allowed code mapping.
No AGPL code or register table is copied or translated.

## Address Normalization

Huawei documents these values as zero-based two-byte register addresses in the
holding-register table. For every FC03 candidate read:

```text
pdu_offset = document_register_address
document_base = 0
no +1 conversion
```

The manifest stores table, documentary notation, base, formula, documentary
address, and resolved PDU offset per read. Missing or conflicting normalization
must produce `NO_ADMISSIBLE_PROFILE`; an implementation may not guess a base.
Numeric fields are big-endian, most-significant word first. Strings contain
`quantity * 2` ASCII bytes; retain raw bytes for provenance, validate ASCII, and
strip only terminal NUL/space padding.

## SmartLogger Candidate

The bounded evidence tuple is unit `0`, FC03 offset `65521`, quantity `1`, U16
device-list change counter, plus FC2B/MEI `0x0E` inventory whose self entry
identifies SmartLogger under the matching structured firmware branch. Basic MEI
alone is not unique because SmartLogger and EMMA can expose overlapping Huawei
identity strings.

Register `65524` is a writable device-name alias and is forbidden as identity.
ESN register `40713` is sensitive and cannot be the sole discriminator. Optional
post-classification enrichment at `20674` and `20689` is branch-gated and not a
universal detector.

SmartLogger firmware gates are tuples of model family, release branch, SPC,
document issue, and protocol. `SPC210/Issue 49` and `SPC191/Issue 52` are
parallel branches, not an ordered numeric sequence. Unknown model/branch
combinations fail closed. Runtime comparison first parses `V`, `R`, `C`, and
`SPC` components, then compares only inside an exact admitted branch. Historical
baseline issues without a documented runtime minimum are evidence-only and
cannot match a runtime revision.

Child inventory uses FC2B/MEI `0x0E`, ReadDevId `0x03`, Object `0x87`: object
`0x87` is count and subsequent objects describe children. A snapshot is accepted
only when `65521` is unchanged before and after enumeration.

## S-Dongle Candidate

The bounded evidence tuple uses logical unit `100`: basic MEI, FC03 offset
`30068`, quantity `2`, U32 protocol version, and FC03 offset `37410`, quantity
`3`, for type, search state, and change sequence. Search-state readability alone
or arbitrary unit-100 readability is not identity.

Version branches remain distinct: V100 interface `V100R001C00SPC100+`,
SDongleA-05 TCP `V100R001C00SPC124+`, V200R022 A-05/B-06
`V200R022C10+`, and the V200R025/SPC120 A-05/B-03/B-06 document branch with
its own scope. Protocol baseline `D5.0` is an independent decoded gate, not a
firmware substitute.

The document describes extended-MEI child objects, but does not conclusively
prove that `unit=100, object=0x87` works through Modbus TCP. FMV3-M7-04 must
provide that live fixture. Until then, child enumeration is ineligible. A valid
snapshot requires search complete at `37411`, stable `37412` before/after, and
count/capacity reconciliation with `37429`.

## EMMA Candidate

EMMA is first-class and must not fall back to SmartLogger. The bounded unit-`0`
tuple is:

- FC03 `30000`, quantity `15`, ASCII offering name;
- FC03 `30222`, quantity `20`, ASCII model;
- FC03 `30035`, quantity `15`, ASCII software version;
- FC2B/MEI basic identity;
- extended-MEI self entry with device ID `0`, EMMA-family model, and HEMS
  product type.

Register `30015` contains a serial number and is forbidden as a detector. Mere
readability of `30222`, a `SmartHEMS` prefix without a fixture, or basic MEI does
not qualify EMMA. R024 is gated at `V100R024C00SPC100+`; R025 is separately
gated at `V100R025C00SPC102+`. The documented `P1.15-D1.0` value is an example,
not a universal protocol minimum.

Historical Tancabesti evidence confirms unit `0` and telemetry blocks
`31639..31690`, `30801..30812`, and `41214..41215`. It does not confirm the
detector tuple, firmware/protocol tuple, MEI inventory, or negative overlap with
SmartLogger.

## Child Inventory Contract

SmartLogger and EMMA document this read-only inventory API:

```text
FC2B / MEI 0x0E / ReadDevId 0x03 / ObjectID 0x87
PDU: 2B 0E 03 87
```

- `0x87` is a U8 device count;
- `0x88..0xFF` describe children 1..120;
- a continued list wraps from `0xFF` to `0x00`;
- response fields `More`, `Next object ID`, and object count drive traversal;
- ASCII attributes include model, software, interface protocol, ESN, device
  address, feature version, and product type.

Traversal must bound total deadline, pages, objects, and bytes; track visited
cursors; reject loops, duplicate objects, duplicate addresses, count mismatch,
and malformed ASCII. Device IDs must be in `0..247`. ESN is never public; a
private digest may participate in stable identity only if identity policy allows
it. Parent-child provenance includes gateway identity, inventory generation,
child routing address, model/product type, source revision, and raw evidence.
Disappearance/reappearance changes lifecycle state without silently reusing a
different child's identity.

The evidence contract fixes a `15000 ms` total deadline. SmartLogger and EMMA
allow at most `248` pages, `248` objects, and `65536` response bytes. The
currently documented S-Dongle path allows at most `121` pages, `121` objects,
and `32768` bytes. Reaching any limit is `INSUFFICIENT_EVIDENCE`, never a
partial successful inventory.

EMMA has no documented change-sequence counter. Its `30801` inverter count,
`30804` charger count, and `30811/30812` presence flags must remain stable around
the inventory, followed by bounded periodic hash/diff refresh. FC03 brute-force
scanning is not equivalent to this API and may only be a separately labeled
degraded fallback after an explicit later gate.

## Collision And Failure Rules

- Two family detectors positive on one endpoint produce
  `INSUFFICIENT_EVIDENCE`; there is no first-match priority.
- A SmartLogger positive at unit `0` plus a response at unit `100` does not
  imply S-Dongle.
- Modbus exceptions `0x02/0x03` reject only the current optional probe.
- Exception `0x04/0x06/0x80/0x90/0x91`, timeout, or disconnect yields
  `INSUFFICIENT_EVIDENCE`, not `NO_MATCH`.
- Serial numbers, writable aliases, credentials, and write-only device-search
  controls are excluded.

FMV3-M7-05 must test SmartLogger, S-Dongle, EMMA, and direct-inverter catalogs
together. Any pairwise detector collision remains fail-closed.

## Transport Prerequisite

The standard `helianthus-modbus` Device Identification traversal remains
strict: it starts at object `0`, requires the basic objects, and does not wrap.
Transport PR [#18](https://github.com/Project-Helianthus/helianthus-modbus/pull/18)
was squash-merged at
`c78030472c24f0f2b849fd30124611157a81f834` and is available as
`v0.0.0-20260820212315-c78030472c24`. It adds separate vendor-neutral,
read-only primitives for response-bearing Modbus TCP `unit_id=0` and a bounded
extended code-03 stream starting at object `0x87`. That extended stream permits
one documented `0xFF -> 0x00` continuation and rejects loops, duplicate objects,
and partial publication. RTU unit `0` remains a rejected response-bearing read.

The prerequisite is `MERGED_AVAILABLE_FOR_REGISTRY_PIN`. FMV3-M7-04 may pin
that exact merge, but transport capability does not make any documentary PDU
executable and does not admit any Huawei profile. `helianthus-modbusreg` must
not build frames or duplicate transport parsing.

## Safety

Every PDU in this packet is non-executable evidence. Only FC03 and FC2B/MEI
`0x0E` appear. FC05, FC06, FC0F, FC10, power-control, start/stop, reset,
registration-key, serial-number, credential, and device-search writes are
excluded. No candidate is a support claim.
