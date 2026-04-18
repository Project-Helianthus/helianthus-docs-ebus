# Identification `0x07 0x04`

Status: Normative
Plan reference: ebus-standard-l7-services-w16-26.locked/00-canonical.md
Canonical SHA-256: 9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305

## Catalog Method

The locked plan states:

> `0x07 0x04` produces a canonical `Identification` descriptor with fields
> `manufacturer`, `device_id`, `software_version`, `hardware_version`.
> The descriptor is exposed as a method result with provenance metadata.
> It does NOT overwrite `DeviceInfo`. Disagreements between
> `ebus_standard` Identification and existing `DeviceInfo` values are
> retained with source labels. Consumers apply deterministic precedence
> with both sources visible.

Attribution: canonical plan
`ebus-standard-l7-services-w16-26.locked/00-canonical.md`, SHA-256
`9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305`.

`0x07 0x04` is a normal `ebus_standard` catalog method. It MUST NOT be
implemented as a special scan-only or identity-plumbing path.

## Wire Forms

| Variant | Identity axes |
|---|---|
| Addressed request | `PB=0x07`, `SB=0x04`, request role, addressed, answer-required, request `NN=0x00` |
| Addressed response | `PB=0x07`, `SB=0x04`, response role, addressed, answer-required, response `NN=0x0A` |
| Self-identification broadcast | `PB=0x07`, `SB=0x04`, initiator broadcast, no-answer, payload `NN=0x0A` |

## Response Payload

The addressed response and self-identification broadcast share the same
10-byte payload layout.

| Byte | Field | Type | Descriptor target |
|---:|---|---|---|
| 0 | manufacturer | `BYTE` | `manufacturer` |
| 1-5 | unit_id | `CHAR[5]` text/raw | `device_id` |
| 6 | software_version_major | `BCD` | `software_version.version` |
| 7 | software_version_minor | `BCD` | `software_version.revision` |
| 8 | hardware_version_major | `BCD` | `hardware_version.version` |
| 9 | hardware_version_minor | `BCD` | `hardware_version.revision` |

## Descriptor Schema

The canonical method result schema is:

```json
{
  "manufacturer": {
    "raw": "b5",
    "code": 181,
    "valid": true
  },
  "device_id": {
    "raw": "4241493030",
    "text": "BAI00",
    "valid": true
  },
  "software_version": {
    "version": 1,
    "revision": 23,
    "text": "01.23",
    "valid": true
  },
  "hardware_version": {
    "version": 4,
    "revision": 5,
    "text": "04.05",
    "valid": true
  },
  "provenance": {
    "namespace": "ebus_standard",
    "method": "0x07 0x04",
    "source": "live_bus",
    "catalog_version": "v1.0-locked"
  }
}
```

The four top-level descriptor fields are mandatory. Additional
provenance metadata is mandatory for storage or registry projection.

## Field Rules

`manufacturer`:

1. Decode as `BYTE`.
2. Accept the full byte range `0x00..0xFF`.
3. Do not reject values above decimal `99`; live devices use extended
   manufacturer codes.

`device_id`:

1. Decode bytes 1-5 as fixed-width `CHAR[5]`.
2. Preserve exact raw bytes.
3. Produce display text using the `CHAR` fixed-width text rules in
   [`02-l7-types.md`](./02-l7-types.md).
4. Do not infer vendor or model families from the text inside this
   method. Provider-specific interpretation belongs outside
   `ebus_standard`.

`software_version` and `hardware_version`:

1. Decode each component as independent `BCD`.
2. The high nibble is tens; the low nibble is ones.
3. Invalid BCD nibbles make that version object `valid=false`.
4. `0xFF` is a replacement value for a BCD component. A replacement in
   either component makes the corresponding version object
   `valid=false`, `replacement=true`.

## Length and Error Handling

1. Request payload length MUST be exactly zero bytes.
2. Response and self-broadcast payload length MUST be exactly 10 bytes.
3. Fewer than 10 response bytes is `truncated_payload`.
4. More than 10 response bytes is `overlong_payload`.
5. A malformed descriptor MUST NOT be promoted to `DeviceInfo`.
6. Raw bytes and field diagnostics MUST remain available to decode
   clients when the method identity is known.

