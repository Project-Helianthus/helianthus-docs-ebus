# Vaillant Energy Statistics (`0xB5 0x16`, B516)

This document captures the reverse-engineered shape of the Vaillant energy statistics register (`PB=0xB5`, `SB=0x16`).
It is used by observations when querying regulators such as the sensoCOMFORT VRC 720 for cumulative gas, electrical,
and solar energy figures.

## 1. Scope and Framing

- Transport: standard eBUS telegram (`DST PB SB LEN DATA...`) with the payload detailed below.
- CRC/escaping follow normal eBUS rules and are omitted in this document.
- This document covers sub-command `0x10` (energy statistics read) only. For
  sub-command `0x10` requests are 8 bytes long and contain embedded selectors
  for period, source, usage, and time window.
- For sub-command `0x10`, responses typically carry ~11 bytes and end with an
  IEEE 754 float32 little-endian value expressed in watt-hours.
- Other B516 sub-commands exist with different request and reply layouts and
  are not covered by this page.

## 2. Register Identification

| Field | Value |
| --- | --- |
| Primary byte (`PB`) | `0xB5` |
| Secondary byte (`SB`) | `0x16` |
| Purpose | Energy statistics selector read (gas/electric/solar, heating/DHW, various periods) |
| Observed targets | Vaillant sensoCOMFORT / VRC 720 regulators; VWZ/VWZIO at `0x76` on heat pump systems (see Section 8) |

## 3. Request Payload Layout

Canonical 8-byte selector payload:

```text
[0x10, 0x0X, PERIOD_IDX, ENERGY_IDX, 0x0Y, 0x0Z, DATE_LO, DATE_HI]
```

| Byte | Meaning |
| --- | --- |
| 0 | `0x10` — the sub-command byte of the energy-statistics read documented on this page; constant for every request on this page. Other B516 sub-commands use a different one-byte sub-ID and are not covered here. |
| 1 | `0x0X` — period selector (`X` in the low nibble): `0`=total, `1`=daily, `2`=monthly, `3`=yearly |
| 2 | `PERIOD_IDX` — raw one-byte field, sent as `0xFF` in every request observed (`0xFF` = select by date rather than by an explicit period index); hardware confirmation of its semantics pending (see §6.1) |
| 3 | `ENERGY_IDX` — raw one-byte field, sent as `0xFF` in every request observed (`0xFF` = select by energy type and operation mode rather than by an explicit energy index); hardware confirmation of its semantics pending (see §6.1) |
| 4 | `0x0Y` — energy source selector (`Y` in the low nibble) |
| 5 | `0x0Z` — usage selector (`Z` in the low nibble) |
| 6-7 | `DATE_LO, DATE_HI` — one little-endian packed date word |

Bytes 6-7 form a little-endian 16-bit word (`word = DATE_LO | (DATE_HI << 8)`) packing a calendar date:

```text
day   = word & 0x1F
month = (word >> 5) & 0x0F
year  = 2000 + (word >> 9)
```

`day` and `month` are `0` when the requested time base does not use them
(yearly and total requests). The date field is ignored entirely for total
requests. This is the same packing the top-level Vaillant message reference
(`ebus-vaillant.md`) describes one byte at a time as "the number of
half-years since year 2000" for the `QQ` byte alone — see the disambiguation
note in §4.3. See §6.1 for a worked, read-only example decoding this formula
against a live reply.

## 4. Period Selectors and Time Encoding

### 4.1 Period Map (`X`)

| `X` | Period | Notes |
| --- | --- | --- |
| `0` | System / since installation | All-time totals. No additional window encoding required. |
| `1` | Day | Packed date (day, month, year) as described in §4.4. |
| `2` | Month | Packed date with `day=0` as described in §4.5 (experimental beyond the packing itself). |
| `3` | Year | Packed date with `day=month=0` as described in §4.3. |

### 4.2 System Totals (`X=0`)

- Bytes 6-7 (the packed date) are ignored by the regulator for total requests;
  byte 6 = `0x00`, byte 7 = `0x00` is the canonical form observed.
- Use this form when requesting cumulative totals since installation for a given source/usage pair.

### 4.3 Yearly Windows (`X=3`)

Day and month are `0` for a yearly request; only the year component of the
packed date (bits 9-15 of the word, i.e. byte 7) varies:

```text
word  = (year - 2000) << 9
byte6 = word & 0xFF        (always 0x00 for a pure year request)
byte7 = (word >> 8) & 0xFF
```

- Year 2024 → `word = 0x3000` → `byte6 = 0x00`, `byte7 = 0x30`.
- Year 2025 → `word = 0x3200` → `byte6 = 0x00`, `byte7 = 0x32`.
- Year 2026 → `word = 0x3400` → `byte6 = 0x00`, `byte7 = 0x34`.

"Current year" and "previous year" are not wire selectors — they are
descriptions of whichever absolute year the caller encodes relative to
today's date. A caller can request any year this way, not only the two
years adjacent to the current date. Which years a given regulator actually
answers for (versus returning a non-zero return code; see §6) is
device-dependent and has not been exhaustively observed.

> **Disambiguation:** The top-level Vaillant message reference (`ebus-vaillant.md`) describes `QQ` for yearly windows as "the number of half-years since year 2000" (e.g., `QQ=0x34` (52) = first half of 2026). That wording describes the same packed-date byte 7 seen here: with day/month both `0`, byte 7 equals `(year - 2000) << 1`, i.e. twice the year offset — which reads as "half-years since 2000" when the month's top bit (which also lands in byte 7) is zero. This equivalence holds specifically for the **yearly case** (`day = month = 0`), where byte 7 alone carries the year offset doubled; it does not extend to the daily (§4.4) or monthly (§4.5) cases, where day and month occupy bits that the half-year wording does not account for. For the yearly case, the packed-date model in this document and the half-year wording in the parent reference describe the same bytes; they are not two competing encodings.

### 4.4 Daily Windows (`X=1`)

Day-level reads pack the full calendar date (year, month, day) into the
little-endian word described in §3:

```text
word  = ((year - 2000) << 9) | (month << 5) | day
byte6 = word & 0xFF
byte7 = (word >> 8) & 0xFF
```

Example encodings (gas heating, shown for brevity):

| Date | Byte 6 | Byte 7 | Request tail |
| --- | --- | --- | --- |
| 1 January 2025 | `0x21` | `0x32` | `... 0x21 0x32` |
| 1 January 2024 | `0x21` | `0x30` | `... 0x21 0x30` |
| 31 December 2025 | `0x9F` | `0x33` | `... 0x9F 0x33` |
| 31 December 2024 | `0x9F` | `0x31` | `... 0x9F 0x31` |

These four encodings decode cleanly under the packed-date formula in §3:
`21 32` → 2025-01-01, `9F 33` → 2025-12-31, `21 30` → 2024-01-01, `9F 31` →
2024-12-31. As in §4.3, "current year" and "previous year" are descriptive
terms for whichever absolute year the caller encodes relative to today's
date, not separate wire selectors. Daily queries for years other than the
two adjacent to today's date are structurally supported by the packed-date
encoding but have not yet been validated on real hardware.

### 4.5 Monthly Windows (`X=2`)

Monthly reads use the same packed-date word as §4.4 with `day = 0` and the
target month and year set:

```text
word  = ((year - 2000) << 9) | (month << 5)
byte6 = word & 0xFF
byte7 = (word >> 8) & 0xFF
```

For example, March 2025 (`month=3`, `year=2025`) → `word = (25 << 9) | (3 << 5) = 0x3260` → `byte6 = 0x60`, `byte7 = 0x32`. Detailed month-level validation beyond this packing is pending; current observations treat month queries as experimental.

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

For sub-command `0x10`, observed responses are typically 11 bytes (some regulators append padding). In this form the final 4 bytes are a float32 little-endian value representing watt-hours.

```text
[FLAGS, PERIOD_IDX, ENERGY_IDX, 0x0Y, 0x0Z, DATE_LO, DATE_HI, value_0, value_1, value_2, value_3]
```

| Byte | Meaning |
| --- | --- |
| 0 | `FLAGS` — low bits 0-1: time base (matches request byte 1's low nibble); bit 2: access (0 = read); bit 3: reserved/unknown; high nibble: return code (`0x0` = value present, non-zero = not OK — no value follows that can be trusted) |
| 1 | `PERIOD_IDX` — raw one-byte field, the same position as request byte 2. Observed as `0x00` or `0xFF`; hardware confirmation of its semantics pending (see §6.1). |
| 2 | `ENERGY_IDX` — raw one-byte field, the same position as request byte 3. Observed as `0x00` or `0xFF`; hardware confirmation of its semantics pending (see §6.1). |
| 3 | `0x0Y` — echoes the energy source selector |
| 4 | `0x0Z` — echoes the usage selector |
| 5-6 | `DATE_LO, DATE_HI` — packed date, decoded with the formula in §3 |
| 7-10 | `value_0..value_3` — IEEE 754 float32 little-endian watt-hours |

- `value_*` is an IEEE 754 float32 little-endian number. Divide by `1000` to convert Wh to kWh.
- Example: bytes `0x00 0xE8 0x03 0x00` → `100000.0 Wh` → `100 kWh`.
- **Read-only verification step:** a reply to a total request (§4.2) echoes
  the regulator's own current date in bytes 5-6, rather than the all-zero
  date sent in the request. Decoding that echoed date with the §3 formula
  yields the day the read was made — a reproducible, read-only check that
  does not depend on any write or on wall-clock assumptions baked into the
  request. See §6.1 for a worked example.

### 6.1 Worked Evidence (Read-Only)

Three read-only identification-style queries against a VRC 720f/2 regulator
(EID `BASV2`, SW `0507`) at address `0x15`, service `B5 16`, on 2026-04-07.
Any reader can reproduce the decode below with only the packed-date formula
in §3 and a standard IEEE 754 float32 little-endian decoder.

**Query 1 — total, electrical heating:**

```text
Request: 10 00 FF FF 03 03 00 30
Reply:   00 00 00 03 03 87 34 00 54 5D 46
```

| Reply byte(s) | Raw | Decoded |
| --- | --- | --- |
| 0 (`FLAGS`) | `0x00` | time base `0` (total); access `0` (read); return code `0` (value present) |
| 1 (`PERIOD_IDX`) | `0x00` | — |
| 2 (`ENERGY_IDX`) | `0x00` | — |
| 3 (`0x0Y`) | `0x03` | energy type `3` (electrical) |
| 4 (`0x0Z`) | `0x03` | operation mode `3` (heating) |
| 5-6 (date) | `87 34` | word `0x3487`; day `7`, month `4`, year `2026` — the day the query was made |
| 7-10 (value) | `00 54 5D 46` | float32 LE = `14165.0` Wh |

**Query 2 — total, electrical DHW (not available):**

```text
Request: 10 00 FF FF 03 04 00 30
Reply:   10 00 FF 03 04 87 34 00 00 00 00
```

| Reply byte(s) | Raw | Decoded |
| --- | --- | --- |
| 0 (`FLAGS`) | `0x10` | time base `0` (total); access `0` (read); return code `1` (**not OK** — no value follows that can be trusted) |
| 1 (`PERIOD_IDX`) | `0x00` | — |
| 2 (`ENERGY_IDX`) | `0xFF` | — |
| 3-4 | `03 04` | energy type `3` (electrical), operation mode `4` (DHW) |
| 5-6 (date) | `87 34` | same echoed date as Query 1: `2026-04-07` |
| 7-10 (value) | `00 00 00 00` | no value — return code is non-zero |

**Query 3 — yearly, electrical heating, year 2025 (not available):**

```text
Request: 10 03 FF FF 03 03 00 32
Reply:   13 FF FF 03 03 00 32 00 00 00 00
```

| Reply byte(s) | Raw | Decoded |
| --- | --- | --- |
| 0 (`FLAGS`) | `0x13` | time base `3` (yearly); access `0` (read); return code `1` (**not OK**) |
| 1 (`PERIOD_IDX`) | `0xFF` | — |
| 2 (`ENERGY_IDX`) | `0xFF` | — |
| 3-4 | `03 03` | energy type `3` (electrical), operation mode `3` (heating) |
| 5-6 (date) | `00 32` | word `0x3200`; day `0`, month `0`, year `2025` — the requested year is echoed back, not today's date, because this is a yearly (not total) request |
| 7-10 (value) | `00 00 00 00` | no value — return code is non-zero |

Queries 2 and 3 show `PERIOD_IDX`/`ENERGY_IDX` (reply bytes 1-2) taking both
`0x00` and `0xFF` across replies from the same regulator, which is why §3
and §6 describe their semantics as pending rather than settled.

## 7. Example Payloads

| Scenario | Hex payload |
| --- | --- |
| Gas heating, year 2025 | `10 03 FF FF 04 03 00 32` |
| Gas hot water, year 2024 | `10 03 FF FF 04 04 00 30` |
| Gas heating, 1 January 2025 | `10 01 FF FF 04 03 21 32` |
| Gas heating, 31 December 2025 | `10 01 FF FF 04 03 9F 33` |

## 8. VWZ/VWZIO Access Path (Heat Pump Systems)

> Hypothesis from a public issue reference; no publishable capture is included here.

On heat pump systems with a VWZ/VWZIO indoor hydraulic station at address `0x76`, B516 supports an alternative, simpler access path distinct from the 8-byte selector described in Sections 3-7:

| Field | Value |
|-------|-------|
| Target device | VWZ/VWZIO at `0x76` |
| Sub-ID | `0x18` |
| Prefix | `IGN:1` (1 ignored byte before the value) |
| Register name | `ConsumptionTotal` |
| Data type | energy (kWh) |
| Offset in response | `0x02` |

**ebusd framing:**
```
Request:   *r,,,,,,\"B516\",\"18\"    (target: VWZ at 0x76)
Prefix:    IGN:1                       (1 ignored byte before value)
```

This is a distinct access path from the VRC720 8-byte selector. The `18` sub-ID with `IGN:1` prefix appears to be a simpler, device-specific query form used on the hydraulic station module. It does NOT use the period/source/usage nibble encoding of the VRC720 path described above.

**Confidence:** HIGH for observed access path existence; MEDIUM for complete decoder shape (original issue does not show full response bytes in the enrichment corpus).

## 9. References

- `john30/ebusd-configuration` issue `#490` (public reverse-engineering notes)
- §6.1 Worked Evidence: three read-only identification-style queries against
  a VRC 720f/2 regulator, with full request/reply bytes and decode — the
  primary evidence for the packed-date model and the response byte layout
  in this document
