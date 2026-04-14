# Vaillant B522 recoVAIR Ventilation Commands

`PB=0xB5`, `SB=0x22`.

## Status

`B522` appears in the john30 `08.recov` TypeSpec as a write command family for
recoVAIR ventilation modes. The configured base includes a static `0x00`
selector after `SB=0x22`.

Evidence labels:

- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local captures.
- `LOCAL_MCP`: current Helianthus MCP runtime observations.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Wire Shape

The TypeSpec defines:

```text
Write base:
  @base(MF, 0x22, 0)

Configured request payload:
  00 <selector> 00 ff ff
```

The trailing `00 ff ff` bytes are part of the static TypeSpec extension for the
known ventilation commands.

## Known Selectors

| Request suffix | TypeSpec name | Direction | Meaning | Evidence | Falsification test |
|---|---|---|---|---|---|
| `02 00 ff ff` | `VentDay` | write | set ventilation day mode | `LOCAL_TYPESPEC` | Issue the command on isolated recoVAIR hardware and show day mode is not selected. |
| `01 00 ff ff` | `VentNight` | write | set ventilation night mode | `LOCAL_TYPESPEC` | Issue the command on isolated recoVAIR hardware and show night mode is not selected. |
| `03 00 ff ff` | `VentBoost` | write | activate boost ventilation | `LOCAL_TYPESPEC` | Issue the command on isolated recoVAIR hardware and show boost is not activated. |

## Relationship to B509 Registers

The same `08.recov` TypeSpec also exposes many recoVAIR values through B509-like
register templates. `B522` is only the small command family for ventilation mode
writes and should not be used as the general recoVAIR register map.

## Unknowns

- ACK/status response shape for each command.
- Whether command effects are latched, timed, or controller-policy dependent.
- Whether non-recoVAIR ventilation products reuse B522.

## References

- Public TypeSpec: [08.recov.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/08.recov.tsp)
