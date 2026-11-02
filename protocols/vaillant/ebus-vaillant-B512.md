# Vaillant B512 Circulation Pump / VR65-Style State Family

`PB=0xB5`, `SB=0x12`.

## Status

The payload has been described as `Modulation/Fan`; public TypeSpec and historical notes provide a stronger, falsifiable hypothesis:
`B512` is at least partly a circulation-pump or VR65-style state family.

Evidence labels:

- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `PUBLIC_CAPTURE`: public Pittnerovi eBUS trace examples.
- `CANDIDATE`: a layout that is not confirmed on the wire. Every
  `CANDIDATE` statement is **Hypothesis**, unconfirmed on the wire.

## Known Shapes

| Request payload | Name/context | Response shape | Evidence | Falsification test |
|---|---|---|---|---|
| `00 <value>` | `StatusCirPump` in `hcmode_inc` | prefix-only candidate; physical acknowledgement Unknown | | Change circulation pump state and show `<value>` does not correlate with off/on values. |
| `02 <value>` | target `0x64`/VR65-style state | ACK/status | `PUBLIC_CAPTURE` | Capture target `0x64` while pump/valve states change and prove `B512 02 xx` is unrelated. |

In `hcmode_inc`, `StatusCirPump` enumerates `off=0` and `on=100`.

## Observation status

No publishable local capture is included in this reference.

### Heat Pump System Shapes (Enrichment Research)

> Hypothesis from public community sources; no publishable capture is included here.

The following B512 shapes are observed on heat pump installations only and are absent from gas-boiler-only systems.

| Request payload | Name/context | Target | Response shape | Evidence | Notes |
|---|---|---|---|---|---|
| `0f 00 01` | `StatusHydraulics` | VWZ/VWZIO (`0x76`) | 7 bytes raw (undecoded) | 4 independent forks — MEDIUM-HIGH confidence | 10-second poll from the controller at `0x15` to VWZ; hydraulic status. HP-system-specific. |
| `13 00` | `StatusHydraulics` (HMU variant) | HMU (`0x08`) | system pressure (UCH/10, bar) + flow (UIN, l/h) — field byte offsets TBD | Hypothesis; native field layout remains Unknown | Wire field offsets and types require correlated native observations. |

**Device scope:** These shapes gate on heat pump device type. ID `0f0001` requires a controller at `0x15` + VWZ/VWZIO at `0x76`. ID `1300` requires HMU at `0x08`.

## Candidate sub-commands (`OP`)

> **Hypothesis**, unconfirmed on the wire: the candidate layouts below cover the
> B512 input/output services selected by the first payload byte (`OP`). No
> exchange of these services is confirmed on the wire. Quoted names are Vaillant
> names, kept as correspondence names only.

| `OP` | Candidate name | Request (candidate) | Reply (candidate) |
|---:|---|---|---|
| `01` | eBUS general accessory | setpoints of 2nd heating pump, circulation pump, solar pump (u8 percent), external error-signal relay, loading pump (u8 percent), open fume flap | feedback of each of the six values |
| `03` | read analogue value | analogue input selection | state of NTC or analogue input, value |
| `06` | APC operation control | operation flags, modulation, DHW water, DHW and tank temperature, further flags | four data bytes: boiler-control flags, DHW setpoint, return temperature, anti-reset-windup state (s8: `-1` at minimum, `0` in range, `1` at maximum, `2` modulation regulator not active) |
| `08` | status info for solar kit | inlet temperature sensor, status, additional infos | DHW setpoint, additional infos |
| `09` | status info for two-zone kit | additional infos | additional infos |
| `0A` | operational data to APC fan module and back | no candidate layout is known | no candidate layout is known |
| `0B` | parameter for HMU to FMU | target fan speeds (2), relay command | actual fan speeds (2), status, three temperature sensors |
| `0C` | FMU parameters | pulses per revolution, P, I, D parameters, minimum PWM to start, maximum PWM saturation, number of fans | feedback |
| `0D` | smart eBUS module A | none | digital input, two temperatures |
| `0E` | smart eBUS module B | none | temperature, humidity, air quality |
| `0F` | set and get IO-expander data | outputs byte (bit 0 MA1, bit 1 MA2), UV1 byte (`0` off, `1` CH, `2` DHW) | SP1 (s16 /16 °C), inputs byte (`0` ME, `1` EVU contact), VF1 (s16 /16 °C), water pressure (u8 /10 bar), backup-heater output (`0` off, `1`..`3` steps, `255` candidate replacement value (no value available)) |
| `10` | terminal board communication | actuator flags, inverse actuator flags | digital inputs, compressor and backup-heater phase feedback, six ADC values, PCB version |
| `11` | operational data exchange between HMU indoor unit and outdoor unit | flow temperature and two refrigerant-circuit temperatures (expansion-valve side and four-way-valve side; each s16 /16 °C), building-circuit water pressure (u8 /10 bar), building-pump flow rate (one byte, 10 l/h per count), building-pump status byte, flags (bit 0 compressor off) | two data bytes: flags (bit 0 compressor off, bit 1 building-pump relay), building-pump set point (u8 percent) |
| `12` | operational data of a heat-pump and ventilation unit | ventilation emergency stop, ventilation switch, two CO2 sensors | ventilation switch LED |
| `14` | control of an input/output module | header only | header only |

### Bounded pump, valve and power candidates

The finite companion scope, labelled AE17, is the OP00, OP02, OP04, OP05 and OP07
catalog declarations only. Every declaration here is a candidate of evidence class
**Hypothesis**; provenance is not published, and the fixture is synthetic, not wire
evidence. Broader catalog completion is Unknown. Other variants
remain separate in the preceding overview. All native declarations below are
**Hypothesis**. **Proven** applies only to synthetic representation and arithmetic,
not installed support, delivery, freshness or physical qualification, all **Unknown**.
Logical positions are not wire offsets; extents count bytes only where declared.
No actuator path or stability promise is established.

| Grade | PB/SB | OP | Direction | Field | Logical position | Extent | Raw type/domain | Scale | Sentinel/default/conflict | Timeout seconds | External mode | Unresolved | Qualification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Hypothesis | B5/12 | 00 | request | circulation-setpoint | 3 | 1 | u8; 0..255 | percent | default 0; 0=off; 1..100=on/speed | Unknown | Unknown | 101..255 unresolved; physical acknowledgement Unknown | Unknown |
| Hypothesis | B5/12 | 00 | positive | prefix | Unknown | Unknown | prefix-only | none | no value declared | Unknown | Unknown | physical acknowledgement Unknown | Unknown |
| Hypothesis | B5/12 | 02 | request | valve-setpoint | 3 | 1 | u8; 0..255 | percent | 00=CH; 32=midpoint; 64=DHW; FE=standby; FF=unchanged | Unknown | Unknown | other values unresolved | Unknown |
| Hypothesis | B5/12 | 02 | positive | valve-feedback | 3 | 1 | u8; 0..255 | percent | actual or setpoint-fallback; default Unknown | Unknown | Unknown | actual-versus-fallback selection Unknown | Unknown |
| Hypothesis | B5/12 | 02 | positive | tank-contact | 4 | 1 | u8; 0..255 | none | 0=open; 1=closed; default Unknown | Unknown | Unknown | other values unresolved; no FFFF sentinel | Unknown |
| Hypothesis | B5/12 | 02 | positive | tank-temperature | 5 | 2 | signed LE16; -32768..32767 | raw/16 Celsius | default Unknown; no FFFF no-error sentinel | Unknown | Unknown | replacement values Unknown | Unknown |
| Hypothesis | B5/12 | 02 | positive | virtual-error | 7 | 2 | unsigned LE16; 0..65535 | none | FFFF=no-error; default Unknown | Unknown | Unknown | supplements fault-service information; other meanings Unknown | Unknown |
| Hypothesis | B5/12 | 04 | request | heating-pump | 3 | 1 | u8; 0..255 | percent | 0=off regardless of internal demand; 1..100=on/speed; FF=replacement/no-remote-control; default Unknown | 900; restarts on every received service | Unknown | 101..254 unresolved | Unknown |
| Hypothesis | B5/12 | 04 | positive | acceptance | Unknown | 1 | u8; 0..255 | none | 1=accepted; all other bytes rejected; default Unknown | 900; restarts on every received service | Unknown | logical position Unknown; physical effect Unknown | Unknown |
| Hypothesis | B5/12 | 05 | request | option-relay | 3 | 1 | u8; 0..255 | percent | 0=off; 1..100=on-or-speed; FF=unchanged; default Unknown | none meaningful | 8 for each diagnostic point | 101..254 unresolved | Unknown |
| Hypothesis | B5/12 | 05 | request | accessory-relay-1 | 4 | 1 | u8; 0..255 | percent | 0=off; 1..100=on-or-speed; FF=unchanged; default Unknown | none meaningful | 8 for each diagnostic point | 101..254 unresolved | Unknown |
| Hypothesis | B5/12 | 05 | request | accessory-relay-2 | 5 | 1 | u8; 0..255 | percent | 0=off; 1..100=on-or-speed; FF=unchanged; default Unknown | none meaningful | 8 for each diagnostic point | 101..254 unresolved | Unknown |
| Hypothesis | B5/12 | 07 | request | arguments | none | 0 | none | none | no arguments | Unknown | Unknown | response adaptation Unknown | Unknown |
| Hypothesis | B5/12 | 07 | positive | maximum-power | 3 | 1 | u8; 0..255 | kW | default 0 | Unknown | Unknown | response adaptation, installed support and actual-versus-fallback selection Unknown | Unknown |
| Hypothesis | B5/12 | 07 | positive | minimum-power | 4 | 1 | u8; 0..250 | raw/2 percent; 0..125 percent | default 0; 251..255 outside declared domain | Unknown | Unknown | response adaptation, installed support and actual-versus-fallback selection Unknown | Unknown |

OP02 feedback preserves independent actual and setpoint-fallback alternatives;
equality to a setpoint cannot establish an actual value. The wire selection
criterion remains Unknown. OP04's proposed fifteen-minute duration is 900 seconds;
it does not apply to OP05. OP05 declares no meaningful timeout and requires
external-mode 8 separately for each diagnostic point. Absent metadata remains
Unknown, rather than zero or an inherited value. Raw values and partial
last-known-good fields must remain distinguishable from unresolved meanings;
unresolved declarations do not admit physical support.

[Synthetic candidate examples](fixtures/ae18_b512_candidates.json) are isolated
logical field examples, not complete telegrams or native observations.

Codec notes (candidate): in `OP=01`, pump fields are percent while relay and
fume-flap fields use `0F` for true and `F0` for false. In `OP=0F`, raw `8000`
in SP1 or VF1 is a candidate replacement value (no value available) in place
of the s16 /16 °C value, and candidate value 255.0 for the pressure when no value is set
(unconfirmed on the wire) lies outside the candidate range 0..25.5 bar.
`OP=03` and `OP=06` carry unit °C on selector and modulation fields.
`OP=08` status: `0` valid, `55` short circuit, `AA` interrupted or not
connected. `OP=0B` reports `0` idle, `1` running, `FF` fault.

Overlap with the shapes above (all **Hypothesis**):

- `00 <value>` with `0` and `100` corresponds in number and width to candidate
  `OP=00` (circulation pump setpoint, percent).
- The community shape `0f 00 01` has the `OP` byte `0F` and a two-byte
  request, and the community reply length of seven bytes equals the sum of the
  candidate `OP=0F` reply fields (2 + 1 + 2 + 1 + 1). With the candidate
  request fields it reads outputs `00` and UV1 `01` (CH). Whether the
  community name `StatusHydraulics` and the candidate names describe the same
  exchange is unresolved.
- The community shape `02 <value>` has the `OP` byte `02` and a one-byte
  value, and the candidate `OP=02` request is one byte too: the 3-way-valve
  setpoint in percent (`0x00` CH position, `0x64` DHW position, `0xFE`
  actuator standby, `0xFF` no change). The values `0x00`, `0x64` and `0xFE` of
  the community shape coincide with these candidate values. Whether the
  community shape is the candidate `OP=02` exchange is unresolved.
- The quantities of the HMU shape `13 00` (system pressure, flow) are request
  fields of candidate `OP=11` (building-circuit water pressure and
  building-pump flow rate), not fields of its two-byte reply. No candidate
  `OP=13` is known, so the relation of `13 00` to the candidate `OP` services
  is unresolved.

Candidate, unconfirmed on the wire: every sub-command of this family with a
candidate layout (`OP` `00` to `12`, except `0A`) is available under both the
eBUS and the PeBUS profiles; none is known to be available only on PeBUS. The
profile availability of the header-only entry (B512 `14`) is not established.

## Unknowns

- Whether target `0x64` is a physical VR65-like device, a virtual/internal
  address, or an undiscovered participant on each installation.
- Exact meaning of values `0x00`, `0x64`, and `0xfe` reported in historical
  traces (the candidate 3-way-valve setpoint reading of the overlap list above
  is **Hypothesis**, unconfirmed on the wire).
- Whether the old "modulation/fan" label has any valid subset for other
  devices.
- VWZ/VWZIO at `0x76` is a confirmed B512 target on heat pump systems
  (4 independent community forks). Full register decode pending.

## Open questions

- No B512 exchange of the candidate `OP` services has been captured; the
  physical acknowledgement, complete reply lengths and the targets that implement
  each `OP` remain Unknown; the scoped table declares candidate extents only.
- Which targets, if any, answer the `OP` services, and whether a Vaillant
  requester sends any of them; no sender or responder implementation is
  known either way.
- Whether the community shapes `0f 00 01` and `02 <value>` are the candidate
  `OP=0F` and `OP=02` exchanges, and which candidate `OP`, if any, the community
  shape `13 00` corresponds to (system pressure and flow are request fields of
  candidate `OP=11`, and no candidate `OP=13` is known).
- The meaning of candidate value 255.0 for the pressure when no value is set,
  which falls outside the candidate range 0..25.5 bar.
- The profile availability (eBUS or PeBUS) of the header-only entry `14`.

## References

- Public TypeSpec: [hcmode_inc.tsp](https://github.com/john30/ebusd-configuration/blob/master/src/vaillant/hcmode_inc.tsp)
- Public TypeSpec: [64.v65.tsp](https://github.com/john30/ebusd-configuration/blob/master/src/vaillant/64.v65.tsp)
- Public capture/reference: [Pittnerovi eBUS page](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/)
- Historical PDF: [Vaillant_ebus.pdf](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/Vaillant_ebus.pdf)
