# Identity Provenance

Status: Normative
Plan reference: ebus-standard-l7-services-w16-26.locked/00-canonical.md
Canonical SHA-256: 9e0a29bb76d99f551904b05749e322aafd3972621858aa6d1acbe49b9ef37305

## Policy

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

`ebus_standard` Identification is an evidence source. It is not a
replacement write into `DeviceInfo`.

## Provenance Sources

Identity records MUST preserve source labels. Required source labels:

| Source label | Meaning |
|---|---|
| `device_info` | Existing registry `DeviceInfo` identity |
| `ebus_standard.identification` | Decoded `0x07 0x04` descriptor |
| `operator_seed` | Operator-provided static identity seed |
| `passive_observation` | Identity evidence observed without Helianthus-originated query |

Implementations MAY add more source labels, but they MUST NOT collapse
multiple sources into an unlabeled merged value.

## Non-Overwrite Rule

When a valid `0x07 0x04` descriptor is decoded:

1. Store it as `ebus_standard.identification` evidence.
2. Attach method provenance: catalog identity, catalog version, source
   frame metadata, timestamp, and decode validity.
3. Do not overwrite `DeviceInfo.manufacturer`, `DeviceInfo.device_id`,
   `DeviceInfo.software_version`, or `DeviceInfo.hardware_version`.
4. If a projection needs a single display value, compute it from the
   deterministic precedence rule below while keeping both source records
   visible.

## Disagreement Handling

A disagreement exists when two valid source records provide different
values for the same identity field.

Required behavior:

1. Preserve both values.
2. Preserve both source labels.
3. Mark the field with `agreement=false`.
4. Do not silently normalize away punctuation, casing, padding, or raw
   byte differences.
5. Expose enough raw data for a client to distinguish display-string
   disagreement from byte-level disagreement.

Malformed `0x07 0x04` data is not a disagreement. It is invalid
evidence and must remain labeled as such.

## Deterministic Precedence

When a consumer requires one preferred identity value, apply this order:

1. Valid `device_info` value.
2. Valid `ebus_standard.identification` value.
3. Valid `operator_seed` value.
4. Valid `passive_observation` value.
5. `unknown`.

This precedence is deterministic display selection only. It does not
delete lower-precedence evidence.

## Projection Shape

A registry or MCP projection SHOULD expose both the preferred value and
the source set:

```json
{
  "manufacturer": {
    "preferred": {
      "value": "Vaillant",
      "source": "device_info"
    },
    "sources": [
      {
        "source": "device_info",
        "value": "Vaillant",
        "valid": true
      },
      {
        "source": "ebus_standard.identification",
        "raw": "b5",
        "value": 181,
        "valid": true
      }
    ],
    "agreement": false
  }
}
```

## HA Compatibility

First delivery is a Home Assistant compatibility checkpoint only. No new
HA entities, no new GraphQL fields, and no consumer rollout are allowed
as a side effect of identity provenance. Existing HA-visible contracts
must remain stable while both identity sources are retained internally.

