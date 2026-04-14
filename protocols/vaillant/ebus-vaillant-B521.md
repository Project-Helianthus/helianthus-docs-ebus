# Vaillant B521 OMU Service Register Family

`PB=0xB5`, `SB=0x21`.

## Status

`B521` appears in john30 OMU TypeSpec files as a service/register family with a
static `0x00` selector after `SB=0x21`. It is used for source input sensor
offsets, deicing parameters, fan/speed parameters, and related OMU values.

Evidence labels:

- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local captures.
- `LOCAL_MCP`: current Helianthus MCP runtime observations.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Wire Shape

The TypeSpec defines a passive write-capable base:

```text
Configured base:
  @write
  @passive
  @base(MF, 0x21, 0)

Request payload:
  00 <selector> 00 <value?>  (inferred from TypeSpec register template)
```

The exact read/write byte order is inherited from shared register templates and
must be verified with captures before implementing a Helianthus writer.

## Known Selector Examples

| Selector | TypeSpec name | Shape | Evidence | Falsification test |
|---|---|---|---|---|
| `4a 00` | `SourceInputSensorOffset` | install register, temperature | `LOCAL_TYPESPEC` | Change the offset on isolated hardware and show no `B521 00 4a 00` correlation. |
| `4b 00` | `SourceInputSensorOffsetBrine` | install register, temperature | `LOCAL_TYPESPEC` | Same test for brine sensor offset. |
| `45 00` | `DeiceTimeMax` | install register, minutes | `LOCAL_TYPESPEC` | Change max deicing time and show no matching B521 selector. |
| `46 00` | `DeicePeriodMin` | install register, minutes | `LOCAL_TYPESPEC` | Change minimum deicing period and show no matching B521 selector. |
| `29 00` | `DeicefinishTemp` | install register, temperature | `LOCAL_TYPESPEC` | Change finish temperature and show no matching B521 selector. |
| `3f 00` | `FanSpeedMax` | install register, percent | `LOCAL_TYPESPEC` | Change max fan speed and show no matching B521 selector. |

## Safety

Many B521 entries are installer/service parameters. Treat writes as dangerous
until proven on a test fixture, because deicing and fan-speed values can affect
heat-pump safety and performance.

## Unknowns

- Which OMU product IDs and software versions implement B521.
- Whether all selectors are valid for both `e0.omu` and `e1.omu.1`.
- Exact ACK/status bytes for writes.

## References

- Public TypeSpec: [e0.omu.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/e0.omu.tsp)
- Public TypeSpec: [e1.omu.1.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/e1.omu.1.tsp)
