# Vaillant Energy Statistics (`0xB5 0x16`, B516)

This document captures the reverse-engineered shape of the Vaillant energy statistics register (`PB=0xB5`, `SB=0x16`).
It is used by Helianthus tooling when querying regulators such as the sensoCOMFORT VRC 720 for cumulative gas, electrical,
and solar energy figures.

## 1. Scope and Framing

- Transport: standard eBUS telegram (`DST PB SB LEN DATA...`) with the payload detailed below.
- CRC/escaping follow normal eBUS rules and are omitted in this document.
- Requests are 8 bytes long and contain embedded selectors for period, source, usage, and time window.
- Responses typically carry ~11 bytes and end with an IEEE 754 float32 little-endian value expressed in watt-hours.

## 2. Register Identification

| Field | Value |
| --- | --- |
| Primary byte (`PB`) | `0xB5` |
| Secondary byte (`SB`) | `0x16` |
| Purpose | Energy statistics selector read (gas/electric/solar, heating/DHW, various periods) |
| Observed targets | Vaillant sensoCOMFORT / VRC 720 regulators (others pending validation) |

## 3. Request Payload Layout

Canonical 8-byte selector payload:

```text
[0x10, 0x0X, 0xFF, 0xFF, 0x0Y, 0x0Z, (W << 4) | V, 0x30 | Q]
```

| Byte | Meaning |
| --- | --- |
| 0 | `0x10` — constant prefix observed on all requests |
| 1 | `0x0X` — period selector (`X` in the low nibble) |
| 2 | `0xFF` — constant |
| 3 | `0xFF` — constant |
| 4 | `0x0Y` — energy source selector (`Y` in the low nibble) |
| 5 | `0x0Z` — usage selector (`Z` in the low nibble) |
| 6 | `(W << 4) | V` — time specifier nibble pair (depends on period) |
| 7 | `0x30 | Q` — qualifier nibble; combines with byte 6 to pinpoint the requested window |

The selector nibble values (`W`, `V`, `Q`) are encoded differently per period and are detailed in Section 4.

## 4. Period Selectors and Time Encoding

### 4.1 Period Map (`X`)

| `X` | Period | Notes |
| --- | --- | --- |
| `0` | System / since installation | All-time totals. No additional window encoding required. |
| `1` | Day | Requires month/day packing as described in §4.4. |
| `2` | Month | Uses regulator-defined nibble packing (not yet fully verified). |
| `3` | Year | Uses qualifier offsets described in §4.3. |

### 4.2 System Totals (`X=0`)

- `W = 0`, `V = 0` ⇒ byte 6 = `0x00`.
- `Q = 0` ⇒ byte 7 = `0x30`.
- Use this form when requesting cumulative totals since installation for a given source/usage pair.

### 4.3 Yearly Windows (`X=3`)

- `W = 0`, `V = 0` (nibbles unused by current firmware).
- `Q` selects the year:
  - `Q = 2` → current year (`byte7 = 0x32`).
  - `Q = 0` → previous year (`byte7 = 0x30`).
- Historic windows beyond `Q=0` have not been observed; regulators tend to expose only current/previous years.

### 4.4 Daily Windows (`X=1`)

Day-level reads require packing the month, half-month, and day within half-month into `W`, `V`, and `Q`:

```text
Month 1–7:   w_base = month × 2,       q_base_current = 2,  q_base_previous = 0
Month 8–12:  w_base = (month − 8) × 2, q_base_current = 3,  q_base_previous = 1
Day 1–15:    v = day,      d_offset = 0
Day 16–31:   v = day − 16, d_offset = 1
W = w_base + d_offset
V = v
Q = q_base_current   (for current-year daily data)
Q = q_base_previous  (for previous-year daily data — see note below)
```

Finally:
- byte 6 = `(W << 4) | V`
- byte 7 = `0x30 | Q`

The `Q` low nibble selects between current and previous year windows within each bank:
- **Bank 1 (months 1–7):** `Q=2` → current year, `Q=0` → previous year
- **Bank 2 (months 8–12):** `Q=3` → current year, `Q=1` → previous year

> **Note:** Helianthus currently queries only current-year daily totals. Previous-year daily queries (Q=0/Q=1) are structurally supported by the protocol but have not yet been validated on real hardware.

Example encodings (gas heating, current year, shown for brevity):

| Date | Byte 6 | Byte 7 | Request tail |
| --- | --- | --- | --- |
| 1 January (current year) | `0x21` | `0x32` | `... 0x21 0x32` |
| 1 January (previous year) | `0x21` | `0x30` | `... 0x21 0x30` |
| 31 December (current year) | `0x9F` | `0x33` | `... 0x9F 0x33` |
| 31 December (previous year) | `0x9F` | `0x31` | `... 0x9F 0x31` |

### 4.5 Monthly Windows (`X=2`)

Regulators encode months using the same `W/Q` banking concept as the daily variant (two banks of seven months). The `Q` nibble toggles between current and previous year within each bank, following the same pattern as §4.4. Detailed month-level validation is pending; Helianthus currently treats month queries as experimental.

## 5. Source and Usage Selectors

| Selector | Value | Description |
| --- | --- | --- |
| `Y` (source) | `1` | Solar contribution |
|  | `2` | Environmental (heat pump ambient) |
|  | `3` | Electrical energy |
|  | `4` | Fuel / gas consumption |
| `Z` (usage) | `0` | Sum/unspecified |
|  | `3` | Heating |
|  | `4` | Domestic hot water |
|  | `5` | Cooling |

Commonly queried combinations:

| Source (`Y`) | Usage (`Z`) | Description |
| --- | --- | --- |
| `4` (Gas) | `3` (Heating) | Gas consumption for space heating |
| `4` (Gas) | `4` (HotWater) | Gas consumption for DHW |
| `3` (Electrical) | `3` (Heating) | Electrical consumption attributed to heating |
| `3` (Electrical) | `4` (HotWater) | Electrical consumption attributed to hot water |
| `1` (Solar) | `3` (Heating) | Solar contribution to heating circuit |
| `1` (Solar) | `4` (HotWater) | Solar contribution to DHW |

## 6. Response Format

Observed responses are typically 11 bytes (some regulators append padding). The final 4 bytes always form a float32 little-endian value representing watt-hours.

```text
[0x0X, ?, ?, 0x0Y, 0x0Z, (W << 4) | V, 0x30 | Q, value_0, value_1, value_2, value_3]
```

- The period/source/usage/time fields echo the request so that callers can correlate responses.
- `value_*` is an IEEE 754 float32 little-endian number. Divide by `1000` to convert Wh to kWh.
- Example: bytes `0x00 0xE8 0x03 0x00` → `100000.0 Wh` → `100 kWh`.

## 7. Example Payloads

| Scenario | Hex payload |
| --- | --- |
| Gas heating, current year | `10 03 FF FF 04 03 00 32` |
| Gas hot water, previous year | `10 03 FF FF 04 04 00 30` |
| Gas heating, 1 January | `10 01 FF FF 04 03 21 32` |
| Gas heating, 31 December | `10 01 FF FF 04 03 9F 33` |

## 8. References

- `john30/ebusd-configuration` issue `#490` (public reverse-engineering notes)
- Operator RE sessions with Vaillant sensoCOMFORT VRC 720
- Helianthus Python reference implementation traces (energy register polling logic)
