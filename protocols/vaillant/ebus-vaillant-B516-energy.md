# Vaillant Energy Statistics (`0xB5 0x16`, B516)

This document captures the reverse-engineered shape of the Vaillant energy statistics register (`PB=0xB5`, `SB=0x16`).
It is used by observations when querying regulators such as the sensoCOMFORT VRC 720 for cumulative gas, electrical,
and solar energy figures.

## 1. Scope and Framing

- Transport: standard eBUS telegram (`DST PB SB LEN DATA...`) with the payload detailed below.
- CRC/escaping follow normal eBUS rules and are omitted in this document.
- Sections 3 to 7 cover sub-command `0x10` (energy statistics read). For
  sub-command `0x10` requests are 8 bytes long and contain embedded selectors
  for period, source, usage, and time window.
- For sub-command `0x10`, responses typically carry ~11 bytes and end with an
  IEEE 754 float32 little-endian value expressed in watt-hours.
- Other B516 sub-commands have different request and reply layouts: the access
  path of the VWZ/VWZIO at `0x76` is in section 8, sub-ID `0x14` in section 9
  and the further candidate sub-IDs in section 10.

## 2. Register Identification

| Field | Value |
| --- | --- |
| Primary byte (`PB`) | `0xB5` |
| Secondary byte (`SB`) | `0x16` |
| Purpose | Energy statistics selector read (gas/electric/solar, heating/DHW, various periods); further sub-IDs in sections 8 to 10 |
| Observed targets | Vaillant sensoCOMFORT / VRC 720 regulators; VWZ/VWZIO at `0x76` on heat pump systems (see Section 8) |

## 3. Request Payload Layout

Canonical 8-byte selector payload:

```text
[0x10, 0x0X, PERIOD_IDX, ENERGY_IDX, 0x0Y, 0x0Z, DATE_LO, DATE_HI]
```

| Byte | Meaning |
| --- | --- |
| 0 | `0x10` — the sub-command byte of the energy-statistics read documented on this page; constant for every request on this page. Other B516 sub-commands use a different one-byte sub-ID (sections 8 to 10) and are not covered by this layout. |
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
- **Proven arithmetic example (synthetic):** bytes `0x00 0x50 0xC3 0x47` → `100000.0 Wh` → `100 kWh` (IEEE 754 float32 little-endian).
- **Read-only verification step:** a reply to a total request (§4.2) echoes
  the regulator's own current date in bytes 5-6, rather than the all-zero
  date sent in the request. Decoding that echoed date with the §3 formula
  yields the day the read was made — a reproducible, read-only check that
  does not depend on any write or on wall-clock assumptions baked into the
  request. See §6.1 for a worked example.

### 6.1 Worked Evidence (Read-Only)

Three read-only identification-style queries against a VRC720-family
controller at address `0x15`, service `B5 16`, on 2026-04-07.
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

This is a distinct access path from the VRC720 8-byte selector. The `18` sub-ID with `IGN:1` prefix appears to be a simpler, device-specific query form used on the hydraulic station module. It does NOT use the period/source/usage nibble encoding of the VRC720 path described above (see also sections 9 and 10).

**Confidence:** HIGH for observed access path existence; MEDIUM for complete decoder shape (original issue does not show full response bytes in the enrichment corpus).

## 9. Sub-ID `0x14` - current electrical power (candidate)

> **Hypothesis**, unconfirmed on the wire; the unit is a candidate. The
> layout is a request a Vaillant energy-manager requester sends and the reply
> it accepts.

Request: one payload byte, `0x14` (`NN=0x01`):

```text
QQ ZZ B5 16 01 14
```

`QQ` is the requester's address. The request is sent repeatedly (candidate;
the period is unresolved) to targets identified as heat-pump or
backup-heater devices (candidate; see the
[B531 page](ebus-vaillant-B531-hem-power-limit.md), "Targets"); the set of
devices that actually answer is not known.

Reply, payload bytes numbered from 0 (the first byte after the length byte).
The requester rejects a reply whose length is 7 or less:

| Byte(s) | Candidate meaning | Handling by the requester |
|---:|---|---|
| 0 | status byte, meaning unknown | not interpreted |
| 1..4 | word0: IEEE 754 binary32, little-endian; candidate quantity "current electrical power"; sign and unit unknown | the only value read; whether the device reports watts is not established |
| 5..8 | word1: four further bytes, type, scale and sign unknown | not interpreted; present only when the reply length is 9 or more (a length of 8 supplies bytes 0..7 only) |

This form does not use the period/source/usage encoding of section 3.
Candidate sub-IDs are shown in the table below (within `00`..`1A`, without
`14`); support of other sub-IDs is unresolved.

## 10. Other B516 sub-IDs (candidate)

> **Hypothesis**, unconfirmed on the wire. Besides `0x10` (sections 3 to 7),
> `0x14` (section 9) and the access path of section 8, candidate layouts exist
> for the B516 sub-IDs below. No exchange of these sub-IDs is confirmed on the
> wire, and no sender or responder implementation of them is known either way.

| Sub-ID | Candidate name | Content (candidate) |
|---:|---|---|
| `00` | system time | seconds, minutes, hours, day, month, weekday (`1` Monday .. `7` Sunday, not BCD), year (`0..99`); the six other components are packed BCD; century and time zone are not established; positive reply is the header only |
| `01` | corrected outdoor temperature | s16 LE, raw/256 °C |
| `02` | reserved for a solar-powered RF sensor | state, date/time components, outside temperature, accumulator voltage |
| `03` | RF teach-in | manufacturer byte `B5`, ASCII id; reply NetID (2 bytes) and channel |
| `04` | averaged outside temperature | s16 LE, raw/256 °C |
| `05` | RF room temperature | s16 LE, raw/16 °C, battery-low flag |
| `06`..`08` | RF status data page, RF ping, displayed message | pages, number, display fields |
| `0A`..`0E` | RF set parameter (`0A`, `0B`), RF read parameter (`0C`), RF statistic parameter (`0D`), RF synchronisation pool data (`0E`) | raw `8000` in `0B` and `0C` is a candidate replacement value (no value available) in place of the s16 /256 °C value |
| `0F` | time/date adjustment | the request of `00`; positive reply: feedback byte then seven bytes whose raw `FF` is a candidate replacement value (no value available) |
| `11` | read energy statistics configuration | no arguments; nine u8 fields in order: `Version`, `Build`, `TotalEnergies`, `Days`, `DailyEnergies`, `Months`, `MonthlyEnergies`, `Years`, `YearlyEnergies` |
| `12` | clear energy statistics values | flags (bit 0 total, 1 daily, 2 monthly, 3 yearly), energy type, operation mode; positive: bit 0 request not supported, bit 1 energy type not available, bit 2 operation mode not available. The energy-type field is a scalar u8 on some targets and a complex selector (six bits plus sum flags at bits 6 and 7) on others. |
| `18` | summary yield read / write | yield type (`0` solar, `1` environment, `2` energy, `3` gas/oil); reply LE u32 kWh; the write form carries the same fields |
| `19` | summary yield reset | yield type; feedback (`1` accepted) |
| `1A` | month yield read / write | yield, month, year index (`0` this year, `1` last year), mode (`0` all, `1` heating, `2` DHW); reply LE u32 yield sum |

Candidate interpretation, unconfirmed on the wire: sub-IDs `12` and `19` and
the write forms of `10`, `18` and `1A` change stored values (**Hypothesis**);
no write exchange of them is known.

Notes on the candidate layouts (unconfirmed on the wire):

- Sub-ID `1A` (candidate, unconfirmed on the wire): the unit-type byte
  overlaps the second byte of the yield sum, and the candidate month encoding
  is inconsistent around raw `10` and `11`. These inconsistencies are
  unresolved.
- Sub-ID `18` and section 8: the community prefix `IGN:1` followed by a value
  is consistent with a one-byte yield type followed by an LE u32 kWh value;
  that the community register `ConsumptionTotal` is the candidate yield type
  `2` (energy) is **Hypothesis**.
- Candidate interpretation, unconfirmed on the wire: sub-ID `10` is the
  energy-statistics read of sections 3 to 7 and also has a write form:
  - request byte 1: bits 0..1 time base (`0` total, `1` daily, `2` monthly,
    `3` yearly), bit 2 access (`0` read, `1` write); the write-positive reply
    carries the access flag in bit 3;
  - byte 2 is the period index and byte 3 the energy index; `FF` in the
    period index selects by date, any other value selects the daily, monthly
    or yearly table row and ignores the date, and a total request ignores
    both; `FF` in the energy index selects by energy type and operation mode,
    any other value ignores them; an indexed write writes value and date;
  - lengths: read request 7 payload bytes after the sub-ID (reply 11), write
    request 11 (reply 7);
  - the value is a binary32 LE energy in Wh (request only for write, reply
    only for read); the return nibble `0` = value contained, `1` = NOK,
    `2..15` no candidate name known;
  - the candidate layout leaves the packing of the two date bytes
    unspecified; the replies of section 6.1 carry the packing of section 3.
- Candidate energy type values (byte 4 of the request of section 3;
  candidate, unconfirmed on the wire): `0` All, `64` SumOfAllEarnedEnergies,
  `65` SolarYield, `66` EarnedEnvironment, `70` RecoveredEnergy, `71`
  GeneratedElectricalPower, `128` SumOfAllConsumedEnergies, `131`
  ConsumedElectricalPower, `132` ConsumedPrimaryEnergy, `192`
  SumOfAllAvailableEnergyTypes. On VRC700-family controllers the candidate
  values are only `00`, `40`, `41`, `42`, `80`, `83` and `C0` hex (candidate,
  unconfirmed on the wire). For solar and expansion-controller targets a
  candidate bit layout applies (low six bits the type, bit 6 "sum of earned",
  bit 7 "sum of consumed") with target-specific tables (candidate, unconfirmed
  on the wire). The unit of the exchange stays Wh; it is not shown to be
  W. The source selectors of section 5 are low-nibble values (for example
  `0x03` for electrical); whether a target also accepts the candidate bit
  forms (for example `0x83`) is unresolved.

Candidate, unconfirmed on the wire: every sub-ID of this family with a
candidate layout (`10`, the access path of section 8 and the sub-IDs of the
table above) is available under both the eBUS and the PeBUS profiles; none is
known to be available only on PeBUS. The profile availability of B516 sub-ID
`0x14` is not established.

## 11. Open questions

- No frame of B5 16 14 has been captured. The framing, the reply length a
  heat pump produces, the acknowledgement and the set of devices that answer
  are unconfirmed on the wire.
- The unit and meaning of word0, the meaning of the status byte, and the type,
  scale and sign of word1 of sub-ID `0x14` are not established; a reply of
  nine or more bytes is needed to see word1.
- Whether a device reports watts in word0; "watts" is the unit the requester
  assumes, not a unit of the exchange.
- The semantics of `PERIOD_IDX` and `ENERGY_IDX` (section 3 and section 6.1),
  month-level reads (section 4.5), and the years a regulator answers for
  (section 4.3) remain open as stated there.
- Whether a target accepts the candidate energy-type bit forms in addition to
  the low-nibble forms of section 5.
- The sub-IDs of section 10 have candidate layouts only; no sender or
  responder implementation is known either way.
- The profile availability (eBUS or PeBUS) of sub-ID `0x14`.
- The worked evidence of section 6.1 comes from one installation of the
  VRC720 family; other installations of the family were not observed.

## 12. References

- `john30/ebusd-configuration` issue `#490` (public reverse-engineering notes)
- §6.1 Worked Evidence: three read-only identification-style queries against
  a VRC720-family regulator, with full request/reply bytes and decode — the
  primary evidence for the packed-date model and the response byte layout
  in this document
