# Vaillant B512 Circulation Pump / VR65-Style State Family

`PB=0xB5`, `SB=0x12`.

## Status

Earlier Helianthus notes labeled `B512` as "Modulation/Fan" because it was
observed from BAI00 to target `0x64` and the payload was not decoded. Local
TypeSpec and historical notes provide a stronger, falsifiable hypothesis:
`B512` is at least partly a circulation-pump or VR65-style state family.

Evidence labels:

- `LOCAL_TYPESPEC`: vendored john30 `ebusd-configuration` TypeSpec files.
- `LOCAL_CAPTURE`: operator-provided or repository-local captures.
- `LOCAL_MCP`: current Helianthus MCP runtime observations.
- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `PUBLIC_CAPTURE`: public Pittnerovi eBUS trace examples.

## Known Shapes

| Request payload | Name/context | Response shape | Evidence | Falsification test |
|---|---|---|---|---|
| `00 <value>` | `StatusCirPump` in `hcmode_inc` | ACK/status | `LOCAL_TYPESPEC` | Change circulation pump state and show `<value>` does not correlate with off/on values. |
| `02 <value>` | target `0x64`/VR65-style state | ACK/status | `LOCAL_TYPESPEC`, `LOCAL_MCP`, `PUBLIC_CAPTURE` | Capture target `0x64` while pump/valve states change and prove `B512 02 xx` is unrelated. |

In `hcmode_inc`, `StatusCirPump` enumerates `off=0` and `on=100`.

## Local MCP Evidence

Current Helianthus MCP passive protocol specimens showed:

```text
family:      B512
source:      0x03
target:      0x64
request_hex: 02fe
outcome:     abandoned_partial
```

This proves recent local passive observation of `B512 02 fe` from BAI00 source
`0x03` to target `0x64`. It does not prove the semantic meaning of `0xfe`.

## Unknowns

- Whether target `0x64` is a physical VR65-like device, a virtual/internal
  address, or an undiscovered participant on each installation.
- Exact meaning of values `0x00`, `0x64`, and `0xfe` reported in historical
  traces.
- Whether the old "modulation/fan" label has any valid subset for other
  devices.

## References

- Public TypeSpec: [hcmode_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/hcmode_inc.tsp)
- Public TypeSpec: [64.v65.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/64.v65.tsp)
- Public capture/reference: [Pittnerovi eBUS page](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/)
- Historical PDF: [Vaillant_ebus.pdf](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/Vaillant_ebus.pdf)
