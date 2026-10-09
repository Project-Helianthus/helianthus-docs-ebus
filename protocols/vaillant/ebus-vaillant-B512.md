# Vaillant B512 Circulation Pump / VR65-Style State Family

`PB=0xB5`, `SB=0x12`.

## Status

The payload has been described as `Modulation/Fan`; public TypeSpec and historical notes provide a stronger, falsifiable hypothesis:
`B512` is at least partly a circulation-pump or VR65-style state family.

Evidence labels:

- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `PUBLIC_CAPTURE`: public Pittnerovi eBUS trace examples.

## Known Shapes

| Request payload | Name/context | Response shape | Evidence | Falsification test |
|---|---|---|---|---|
| `00 <value>` | `StatusCirPump` in `hcmode_inc` | ACK/status | | Change circulation pump state and show `<value>` does not correlate with off/on values. |
| `02 <value>` | target `0x64`/VR65-style state | ACK/status | `PUBLIC_CAPTURE` | Capture target `0x64` while pump/valve states change and prove `B512 02 xx` is unrelated. |

In `hcmode_inc`, `StatusCirPump` enumerates `off=0` and `on=100`.

## Observation status

No publishable local capture is included in this reference.

### Heat Pump System Shapes (Enrichment Research)

> Hypothesis from public community sources; no publishable capture is included here.

The following B512 shapes are observed on heat pump installations only and are absent from gas-boiler-only systems.

| Request payload | Name/context | Target | Response shape | Evidence | Notes |
|---|---|---|---|---|---|
| `0f 00 01` | `StatusHydraulics` | VWZ/VWZIO (`0x76`) | 7 bytes raw (undecoded) | 4 independent forks — MEDIUM-HIGH confidence | 10-second poll from CTLV2 (`0x15`) to VWZ; hydraulic status. HP-system-specific. |
| `13 00` | `StatusHydraulics` (HMU variant) | HMU (`0x08`) | system pressure (UCH/10, bar) + flow (UIN, l/h) — field byte offsets TBD | FINAL-corrections-and-devices summary table — MEDIUM confidence | Wire decode (field byte offsets, types) not available in enrichment corpus; requires further research. |

**Device scope:** These shapes gate on heat pump device type. ID `0f0001` requires CTLV2 + VWZ/VWZIO at `0x76`. ID `1300` requires HMU at `0x08`.

## Unknowns

- Whether target `0x64` is a physical VR65-like device, a virtual/internal
  address, or an undiscovered participant on each installation.
- Exact meaning of values `0x00`, `0x64`, and `0xfe` reported in historical
  traces.
- Whether the old "modulation/fan" label has any valid subset for other
  devices.
- VWZ/VWZIO at `0x76` is a confirmed B512 target on heat pump systems
  (4 independent community forks). Full register decode pending.

## References

- Public TypeSpec: [hcmode_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/hcmode_inc.tsp)
- Public TypeSpec: [64.v65.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/64.v65.tsp)
- Public capture/reference: [Pittnerovi eBUS page](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/)
- Historical PDF: [Vaillant_ebus.pdf](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/Vaillant_ebus.pdf)
