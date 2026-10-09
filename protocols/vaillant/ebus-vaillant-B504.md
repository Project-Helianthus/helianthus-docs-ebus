# Vaillant B504 GetOperationalData

`PB=0xB5`, `SB=0x04`.

## Status

`B504` is a selector-based read family. It must not be decoded from the
response bytes alone; the request selector and target class are part of the
schema.

Evidence labels:

- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Wire Shape

The The request shape builds a one-byte request payload:

```text
Request payload:
  op : byte
```

Some ebusd TypeSpec rows inherit `B504` with additional static selector bytes
through `@base(MF, 0x4, ...)`. Therefore, `op` is the simplest common model,
not a guarantee that every configured row has only one selector byte.

## Known Selectors and Shapes

| Selector | Name/context | Response shape | Evidence | Falsification test |
|---:|---|---|---|---|
| `0x00` | Date/time | variant-dependent date/time payload plus outside temperature | existing docs | Query `B504 00` on multiple target classes and show no valid date/time layout is returned. |
| `0x02..0x08` | Timer periods Monday..Sunday | `timer` composite | | Read each weekday from a timer-capable controller and show the selector does not map weekdays in order. |
| `0x09` | Parameters in older/consolidated docs | target-dependent | existing docs, historical docs | Capture `B504 09` against BAI00, BASV, and VR_71 and prove all targets share one fixed layout. |
| `0x0D` | Status in older/consolidated docs | often short status payload | existing docs | Capture state changes and show `0x0D` has no status correlation. |
| `0x16` | Outside temperature in `hcmode_inc` | `temp` | | Query target implementing `hcmode_inc` and show response cannot decode as temperature. |
| `0x19 0xNN` | Daily setpoint temperatures in `tempsetpoints_inc` | three `temp1` values | | Query each day selector and show response does not contain three setpoint temperatures. |

## DateTime Caveat

This reference documents two B504 DateTime variants in
[`ebus-vaillant.md`](ebus-vaillant.md):

- a 10-byte BTI/BDA plus `temp2` layout with weekday byte;
- an 8-byte legacy layout without weekday.

Do not hard-code a single DateTime length without validating the target.

## Observation status

No publishable capture is included in this reference.

## Unknowns

- Complete selector namespace per target class.
- Whether some `B504` selectors require service or installer state.
- Which selectors are safe to probe actively on production systems.

## References

- Public TypeSpec: [timer_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/timer_inc.tsp)
- Public TypeSpec: [hcmode_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/hcmode_inc.tsp)
- Public TypeSpec: [tempsetpoints_inc.tsp](https://github.com/john30/ebusd-configuration/blob/23a460b8fe1cc6e7a7e6d549190573ccfcfc450f/src/vaillant/tempsetpoints_inc.tsp)
- Consolidated local reference: [`ebus-vaillant.md`](ebus-vaillant.md)
