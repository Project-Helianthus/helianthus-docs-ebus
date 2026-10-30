# Vaillant B509 Register Access

`PB=0xB5`, `SB=0x09`.

## Status

`B509` is a flat-register access primitive with an operation byte and a 16-bit
address in the common boiler-style form. Register semantics and codecs are
target-specific.

The same `PB`/`SB` header also carries candidate subcommand families
(unconfirmed on the wire) that are not register reads: serial-number windows (`24` to `27`), a product-number read
(`28`), a configuration or data-point read (`54`) and others. They are covered in
the [subcommand catalogue](#subcommand-catalogue). The register form documented
under Wire Shape uses the operation bytes `0D` and `0E`; the falsification tests
below concern the bytes after those two operation bytes.

Evidence labels:

- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.

Confidence markers follow the repository vocabulary: **Proven**,
**Hypothesis** and **Unknown**. A statement described as unconfirmed on the wire
has not been captured on an eBUS exchange.

## Wire Shape

```text
Read request:
  0d a1 a2

Write request:
  0e a1 a2 data...
```

evidence accepts either of these response forms for reads:

```text
0d a1 a2 data...
a1 a2 data...
```

The first form echoes the read opcode; the second echoes only the address.

### Address byte order

The sketch above names the two address bytes `a1 a2` (first and second wire
byte). In this page and
in the register maps a register id such as `0x1800` is written as the two
address bytes in wire order, first byte first.

**Hypothesis** (unconfirmed on the wire): the two address bytes form a 16-bit
little-endian symbolic address, so the first byte is the low byte. Under this
reading `0x1800` is the number 24 (`0x0018`), `0x0E04` is 1038 (`0x040E`) and
the heat-pump id `0xCE01` is 462 (`0x01CE`). No exchange is included here
that distinguishes the two byte orders; the opposite reading (first byte is the
high byte) is not excluded.

## Observation status

No publishable capture is included here; register semantics remain target-specific.

## Device-Type Gate (Register Address Collision)

B509 register addresses are **not globally unique**. The same register ID at the
same eBUS bus address (`0x08`) returns completely different data depending on
whether a BAI00 (boiler) or an EHP00 (heat pump) is installed; the meaning of
these ids on an HMU (heat-pump interface unit) identity is unresolved (see the
[heat pump register map](ebus-vaillant-B509-heatpump-register-map.md#open-questions),
item 5).

Known collisions at address `0x08`:

| Register ID | BAI00 (boiler) | EHP00 (heat pump) |
|------------:|----------------|------------------------|
| `0x3F00` | `externalPumpActive` (on/off) | `ICLOut` — inrush current limiter (on/off) |
| `0xBB00` | `gasValveActive` (UCH 0x0F/0xF0) | `ActualEnvPowerPercentage` (percent0, %) |
| `0x1400` | `pumpHours` (Hoursum2, hours) | `CompPressHigh` — high-side compressor pressure (sensor, bar) |
| `0xE400` | `externGasvalve` (on/off) | `compressorState` (UCH enum) |

**Any B509 implementation that does not gate on product ID will silently return
semantically wrong data.** The product ID can be established from:

- B509 register `0x9A00` (DSN — device-specific number: a device-type or
  configuration code, not a serial number (candidate interpretation,
  unconfirmed on the wire); canonical name `device_specific_number`)
- Candidate, unconfirmed on the wire: B509 subcommand `28` (product number and
  version read, see [Product-number read](#product-number-read-28)); which
  target classes answer it is not established
- B514 device identity frame

The BAI00 boiler register map is in
[`ebus-vaillant-B509-boiler-register-map.md`](ebus-vaillant-B509-boiler-register-map.md).
The EHP00/HMU heat pump register map is in
[`ebus-vaillant-B509-heatpump-register-map.md`](ebus-vaillant-B509-heatpump-register-map.md).

## Known Boiler Registers

Known BAI00 register candidates:

| Register | Name | Semantic use | Codec |
|---:|---|---|---|
| `0x1800` | `flow_temperature` | boiler flow temperature | `DATA2c` |
| `0x4400` | `central_heating_pump_active` | central heating pump active | on/off |
| `0x0200` | `water_pressure` | water pressure | `DATA2b` |
| `0x0500` | `flame_active` | flame active | on/off |
| `0xBB00` | `gas_valve_active` | gas valve active | on/off |
| `0x8300` | `fan_speed` | fan speed | `UIN` |
| `0x2E00` | `modulation_setpoint` | modulation (legacy reading: percent; see the Open questions of the boiler map) | `SIN / 10` |

The `Name` column is the canonical name used by the
[register name correspondence fixture](#register-name-correspondence-fixture);
the boiler and heat-pump maps give the full register lists.

## Subcommand catalogue

`B509` selects its function with the first payload byte (`DB1`). The table
lists the subcommands covered by this page, with the Vaillant name of each.
Presence on a given target is target-specific and unconfirmed on the wire for
every row, and a byte pattern needs the target product before it can be decoded.
Every documented subcommand is available on both the eBUS and the PeBUS profile
(candidate availability, unconfirmed on the wire; PeBUS denotes the second
Vaillant protocol profile). No subcommand of this family is known to be available
only on PeBUS (candidate).

| `DB1` | Vaillant name | Purpose | Candidate availability |
|---|---|---|---|
| `0D` | `DS_B5090DReadSymboAddre` | read a symbolic address | eBUS and PeBUS |
| `0E` | `DS_B5090EWriteSymboAddre` | write a symbolic address | eBUS and PeBUS |
| `0F` | `DS_B5090FWriteSymboAddreAndEnablRemotContrOfThisValue` | write a symbolic address and enable remote control of the value | eBUS and PeBUS |
| `10` | `DS_B50910EnablDisabRemotContr` | enable or disable remote control | eBUS and PeBUS |
| `29` | `DS_B50929ReadSymboAddreAnsweIncluAddre` | read a symbolic address; the reply includes the address | eBUS and PeBUS |
| `03` | `DS_B50903WriteSeriaNumbe` | write a 22-character field | eBUS and PeBUS |
| `04` | `DS_B50904ReadSeriaNumbe` | read a 22-character field | eBUS and PeBUS |
| `20` to `23` | `DS_B50920WriteNewSeriaNumbeFirstPart` to `DS_B50923WriteNewSeriaNumbeFourtPart` | write four nine-byte structures | eBUS and PeBUS |
| `24` | `DS_B50924ReadSeriaNumbePart1` | serial number window 1 | eBUS and PeBUS |
| `25` | `DS_B50925ReadSeriaNumbePart2` | serial number window 2 | eBUS and PeBUS |
| `26` | `DS_B50926ReadSeriaNumbePart3` | serial number window 3 | eBUS and PeBUS |
| `27` | `DS_B50927ReadSeriaNumbePart4` | serial number window 4 | eBUS and PeBUS |
| `28` | `DS_B50928ReadVersiOfAIAndBMU` | read product number and version | eBUS and PeBUS |
| `54` | `DS_B50954ReadDatap`, `DS_B50954WriteDatap` | read or write a data point | eBUS and PeBUS |
| `38` | `DS_B50938MarkECUAsSparePart` | header only | eBUS and PeBUS |
| `5A` | `DS_B5095ARequeRemotReset` | header only | eBUS and PeBUS |
| `5B` | `DS_B5095BResetRequeValid` | header only | eBUS and PeBUS |
| `5C` | `DS_B5095CResetTimeWindo` | header only | eBUS and PeBUS |
| `18` | `DS_B50918ReadErrorBlockOfSlave` | diagnostic read of an error block | eBUS and PeBUS |

### Symbolic-address reads and writes: 0D, 0E, 0F, 10 and 29

Candidate request shapes and behaviour, unconfirmed on the wire; a
`PUBLIC_CONFIG` mark denotes public community configuration evidence. `a1 a2` is the symbolic address in wire order (see
[Address byte order](#address-byte-order)). `NN` is the payload length byte.

```text
0D a1 a2                 read (NN=3)
0E a1 a2 data...         write
0F a1 a2 data...         write and enable remote control of the value
10 a1 a2 flag            enable or disable remote control for the address
29 a1 a2                 read; the reply starts with the address
```

- `0D`: the reply carries the register data. Its width and codec depend on the
  target product; no universal decoder is known (**Unknown**).
- `29`: the reply is an address followed by data selected by that address.
  `PUBLIC_CONFIG`: the community heat-pump configuration decodes `29`
  replies as two ignored address bytes followed by the register value, with the
  same ids as `0D`.
- `0E`: the value follows the address; its codec comes from the target
  product. The reply carries no data.
- `0F`: as `0E`, and it also enables remote control of the value. Candidate
  interpretation, unconfirmed on the wire: the remote-control state lasts 15
  minutes after the last retrigger.
- `10`: candidate interpretation, unconfirmed on the wire: flag `00` disables
  remote control for the address and flag `01` retriggers the remote-control
  timer. Which flag value enables remote control is unresolved.
- The positive replies of `0E`, `0F` and `10` carry only the service prefix. They
  do not certify that a value was written; confirm with a read-back. These
  subcommands change device state. None of them is documented as safe to send:
  a write needs a separately established safety procedure, target
  qualification and explicit confirmation before it is sent, and an ACK plus a
  matching read-back only checks its outcome (see Falsification Tests).
- `FFFF` is a candidate address value for some targets; whether it addresses
  all registers, a broadcast, a clear or an enumeration is **Unknown**.

### Serial-number windows: 24 to 27

Candidate request and reply, unconfirmed on the wire: Request: `24`, `25`,
`26` or `27` with no further request byte (NN=1). Each reply
is nine bytes. **Hypothesis** (unconfirmed on the wire): the four replies are
contiguous windows over one 28-character serial string.

| `DB1` | Serial characters (0-based) | Reply bytes |
|---|---|---|
| `24` | 0 to 7 (8 characters) | byte 0 is a leading byte (`00` in the candidate layout); bytes 1 to 8 carry the characters |
| `25` | 8 to 16 (9 characters) | bytes 0 to 8 |
| `26` | 17 to 25 (9 characters) | bytes 0 to 8 |
| `27` | 26 to 27 (2 characters) | bytes 0 to 1; bytes 2 to 8 are filler `FF` in the candidate layout |

The four replies assemble to the 28-character serial from 8, 9, 9 and 2
characters at serial offsets 0, 8, 17 and 26 (candidate). The requests are
addressed to the heat generator (address `0x08`; candidate).

The [overview page](ebus-vaillant.md) describes these requests as one-byte
selectors that return a status byte and eight ASCII characters per reply. That
description matches window `24`; for `25` to `27` the nine-character windows
above differ from it. The discrepancy is unresolved.

Candidate interpretation, unconfirmed on the wire: the 10-digit article number
is characters 6 to 15 (0-based), that is reply bytes 7 and 8 of `24` and reply
bytes 0 to 7 of `25`.

**Hypothesis** (unconfirmed on the wire): the assembled serial has exactly 28
characters; characters 0 to 25 are digits, character 26 is the letter `N` and
character 27 is a digit.

Further serial subcommands exist (candidate, unconfirmed on the wire): `04` reads
and `03` writes one 22-character ASCII field (the read reply is 25 bytes counted
from the service prefix: three prefix bytes and the 22-character field;
candidate), and `20` to `23` write four nine-byte structures. They are separate
subcommands from the windows `24` to `27`. The 22-character field is not shown
to equal the concatenation of the four windows, and the commit order, the
concatenation and the check of the four writes are not established (**Unknown**).
The write subcommands change device state and no write frame is documented here.

### Product-number read: 28

Request: `28 02` (NN=2), addressed to the heat generator (address `0x08`;
candidate).
Candidate: the second byte is a PeBUS address byte; candidate values include `02`.
Which target classes answer this read is not established (see
[Open questions](#open-questions)). All of this is unconfirmed on the wire.

Candidate reply layout (reply byte 0 is the first byte after NN):

| Reply byte | Width | Encoding | Meaning | Present when NN is |
|---|---|---|---|---|
| 0 | 1 | BCD | meaning not established | 4 or more |
| 1 | 1 | u8 | one-byte software product number (SPN) | 4 or more |
| 2 to 3 | 2 | raw bytes | version pair (major, minor), raw bytes, not BCD-coded | 4 or more |
| 4 to 5 | 2 | u16 little-endian | SPN (16-bit form; its relation to byte 1 is not established) | 6 or more |
| 6 | 1 | raw | candidate: build number | 7 or more |
| 7 to 11 | 5 | ASCII | five-character identity string | 12 or more |

Four reply forms that match the NN steps 4, 6, 7 and 12 (up to the version pair;
plus the 16-bit SPN; plus the build byte; plus the identity string) are the
candidate set; a reply with NN of
3 or less carries none of the fields. The `07 04` identity chain and the SPN
derivation are described in
[ebus-vaillant-regulators.md](ebus-vaillant-regulators.md).

### Configuration and data-point read: 54

Candidate request and reply, unconfirmed on the wire:

```text
request: 54 pp cc lo hi        (NN=5)
reply:   pp fb lo hi data...
```

- `pp`: PeBUS address byte. Candidate values include `0A` and `02`; the meaning
  of the byte is unresolved.
- `cc`: configuration byte. Bit 0 is read/write (`0` read, `1` write). Bits 1 to 2 select remote control (`0` unchanged, `1` disable, `2`
  enable, value `3` has no candidate meaning). Bits 3 to 7 are reserved and zero.
- `lo hi`: data-point address, u16 little-endian.
- `fb`: feedback flags. The reply echoes `pp` and the address.

Candidate feedback bits (a flag set, not an enumeration):

| Bit | Mask | Meaning |
|---|---|---|
| 0 | `01` | success |
| 1 | `02` | data section of the telegram too short |
| 2 | `04` | data section of the telegram too long |
| 3 | `08` | invalid data-point address |
| 4 | `10` | data-point address is under remote control |
| 5 | `20` | data-point value out of range |
| 6 | `40` | value is read-only |
| 7 | `80` | reserved |

The write form (`DS_B50954WriteDatap`) has the same envelope followed by the
data; a write sets bit 0 (candidate). This page documents no write frame. Which targets implement `54`,
and for which addresses, is not established.

**Hypothesis** (unconfirmed on the wire): the five-byte selector
`54 02 00 REG TYPE` of the heat pump interface unit section in the
[heat pump register map](ebus-vaillant-B509-heatpump-register-map.md) is this
read with `pp` = `02`, `cc` = `00` (read) and the data-point address bytes
`REG` (first byte) and `TYPE` (second byte).

### Header-only subcommands: 38, 5A, 5B and 5C

Four further subcommands exist as candidates (`38`, `5A`, `5B`, `5C`; names in
the catalogue). Candidate interpretation, unconfirmed on the wire: for each,
only a request service byte `B5` and a positive reply byte `F5` are candidates;
whether the subcommand byte follows `PB SB` in the request, and any further
request or reply bytes, are **Unknown**.

### Diagnostic subcommand 18

`18` is, as a candidate (unconfirmed on the wire), a diagnostic read of an
error block that carries no register address; it belongs with the diagnostic
services of [ebus-vaillant-B503.md](ebus-vaillant-B503.md). Candidate layout,
unconfirmed on the wire: the request is the operation byte `18` with no
argument; the reply is 10 bytes counted from the service prefix: offsets 3 to 6
are four sensor error blocks (raw bytes), offset 7 bit 0 is a temperature-error
flag (bits 1 to 7 reserved) and offsets 8 and 9 are two temperature error
blocks (raw bytes). The bit maps of the blocks are not established.

### Bounded width and feedback alternatives: 06, 07, 32, 33, 39, 41, 44 and 59

These **Hypothesis** declarations concern the Vaillant family under
`PB=0xB5`, `SB=0x09`. They are candidate native declarations, not wire-qualified
behavior. **Unknown**: wire adaptation and installed support. Logical positions
are Unknown throughout this finite slice; a logical position is not a wire
offset, and a field extent does not establish a complete payload width.
Unprovided defaults, sentinels, units and domains remain Unknown. The five OP33
quantities are separate fields, not an established contiguous wire layout.

| Grade | Operation | Variant | Field | Direction | Logical position / extent | Raw type/domain | Scale | Default/sentinel/conflict | Unresolved |
|---|---|---|---|---|---|---|---|---|---|
| Hypothesis | 07 | selector | selector | request | Unknown / 8 bits | unsigned byte | raw | Unknown | Request selector cannot select reply width; wire adaptation and installed support Unknown |
| Hypothesis | 07 | positive-u16 | value | response | Unknown / 16 bits | unsigned LE16 | raw | default 0; sentinel Unknown | Alternative width remains incomplete/raw; selection, wire adaptation and installed support Unknown |
| Hypothesis | 07 | positive-u32 | value | response | Unknown / 32 bits | unsigned LE32 | raw | default 0; sentinel Unknown | Alternative width remains incomplete/raw; selection, wire adaptation and installed support Unknown |
| Hypothesis | 32 | status-query | address | request | Unknown / Unknown | Unknown | Unknown | Unknown | Queries status; does not toggle an address; address width Unknown |
| Hypothesis | 33 | raw-quantities | address | Unknown | Unknown / Unknown | Unknown | Unknown | Unknown | Address width, byte order and conversion Unknown |
| Hypothesis | 33 | raw-quantities | minimum | Unknown | Unknown / 16 bits | signed LE16 | raw | Unknown | Five separate raw quantities; factor is not a converter; conversion and minimum<=maximum enforcement Unknown |
| Hypothesis | 33 | raw-quantities | maximum | Unknown | Unknown / 16 bits | signed LE16 | raw | Unknown | Five separate raw quantities; factor is not a converter; conversion and minimum<=maximum enforcement Unknown |
| Hypothesis | 33 | raw-quantities | default | Unknown | Unknown / 16 bits | signed LE16 | raw | Unknown | Five separate raw quantities; factor is not a converter; conversion and minimum<=maximum enforcement Unknown |
| Hypothesis | 33 | raw-quantities | step | Unknown | Unknown / 16 bits | signed LE16 | raw | Unknown | Five separate raw quantities; factor is not a converter; conversion and minimum<=maximum enforcement Unknown |
| Hypothesis | 33 | raw-quantities | factor | Unknown | Unknown / 16 bits | signed LE16 | raw | Unknown | Five separate raw quantities; factor is not a converter; conversion and minimum<=maximum enforcement Unknown |
| Hypothesis | 39 | raw-u16 | value | Unknown | Unknown / 16 bits | unsigned 16-bit; byte order Unknown | raw | Unknown | Complement algorithm Unknown |
| Hypothesis | 41 | raw-0f-f0 | value | Unknown | Unknown / 8 bits | unsigned byte; raw 0F/F0 | raw | Unknown | Other values have no established labels |
| Hypothesis | 44 | default-domain-conflict | value | Unknown | Unknown / 8 bits | unsigned byte; domain 1..255 | Unknown; minute interpretation Hypothesis | default 0 conflicts with domain 1..255; sentinel Unknown | Conflict unresolved; conversion Unknown |
| Hypothesis | 59 | quantities | temperature | Unknown | Unknown / 16 bits | signed LE16 | /16 degrees Celsius | Unknown | Wire adaptation and installed support Unknown |
| Hypothesis | 59 | quantities | flow | Unknown | Unknown / 16 bits | unsigned LE16 | /100 litres per minute | Unknown | Wire adaptation and installed support Unknown |
| Hypothesis | 59 | quantities | volume | Unknown | Unknown / 16 bits | unsigned LE16 | /10 litres | Unknown | Wire adaptation and installed support Unknown |
| Hypothesis | 59 | quantities | minimum_volume | Unknown | Unknown / Unknown | width, signedness and byte order Unknown | raw; no division | Unknown | Unit and interpretation Unknown; preserve raw bytes |
| Hypothesis | 59 | quantities | maximum_volume | Unknown | Unknown / Unknown | width, signedness and byte order Unknown | raw; no division | Unknown | Unit and interpretation Unknown; preserve raw bytes |
| Hypothesis | 06 | prefix-only-positive | prefix | response | Unknown / Unknown | Unknown | Unknown | Unknown | Shared apparent prefix cannot select alternative or establish successful reset; wire adaptation and installed support Unknown |
| Hypothesis | 06 | positive-with-feedback | feedback | response | Unknown / 8 bits | unsigned byte | 01 accepted; every other byte rejected | Unknown | Only explicit feedback form; accepted feedback does not establish successful reset; wire adaptation and installed support Unknown |
| Hypothesis | 06 | negative-without-extra-discriminator | prefix | response | Unknown / Unknown | Unknown | Unknown | Unknown | Ambiguous negative; no extra discriminator; prefix does not establish physical NACK or successful reset; wire adaptation and installed support Unknown |

The [synthetic examples](fixtures/ae08_b509_candidates.json) retain raw carriers
beside candidate interpretations. In OP07, two-byte `34 12` is 4660 only in the
16-bit alternative; four-byte `78 56 34 12` is 305419896 only in the 32-bit
alternative. Cross-variant widths remain incomplete/raw. OP33 retains
`-1, 2, 0, 1, -2` as minimum, maximum, default, step and factor independently;
even minimum exceeding maximum does not establish a rejection rule. OP39
`FF FF` remains raw 65535 without a complement (this symmetric example does
not resolve byte order). OP59 `F0 FF` is -1 degree Celsius, `64 00` is 1 litre
per minute and `0A 00` is 1 litre under the respective candidate scales;
minimum/maximum volume bytes remain raw without division.

For OP06, `00`, `01`, `02`, `FF` mean rejected, accepted, rejected, rejected
only in the explicit feedback alternative. Prefix-only-positive and
ambiguous-negative remain separate states; an apparent shared prefix supplies
no alternative discriminator, physical NACK or successful-reset evidence.

The independently merged [AE07 finite catalog](https://github.com/Project-Helianthus/helianthus-ebusreg/pull/245)
is corroborating implementation evidence for exactly these 21 entries, not
proof of the native wire contract or a broader completed catalog. Generic
OP0D/0E access and identity scanning are outside these entries. Synthetic
correctness provides no physical qualification, freshness or execution authority.

### Request and reply widths

Candidate payload widths (NN counts the payload bytes that follow it):

| Subcommand | Request payload | Reply payload |
|---|---|---|
| `0D` | 3 bytes: `0D a1 a2` | register data; width depends on the target product and register |
| `0E` | 3 bytes plus the value | no data |
| `10` | 4 bytes | no data |
| `24` to `27` | 1 byte | 9 bytes |
| `28` | 2 bytes | 4 to 12 bytes (steps at NN 4, 6, 7 and 12) |
| `29` | 3 bytes | 2 address bytes plus data |
| `54` read | 5 bytes | 4 header bytes plus data selected by the address |

## Register name correspondence fixture

[`fixtures/b509-register-name-correspondence.csv`](fixtures/b509-register-name-correspondence.csv)
maps every entry of the [boiler](ebus-vaillant-B509-boiler-register-map.md) and
[heat pump](ebus-vaillant-B509-heatpump-register-map.md) register maps to a
canonical name and, where known, correspondence names. An entry is identified by
`(device_class, operation, selector)`; equal names never merge entries of
different identity.

| Column | Meaning |
| --- | --- |
| `device_class` | Target class: `boiler`, `heat_pump` or `heat_pump_interface_unit`; `any` (class-neutral) for the two operation rows; which targets implement `0D` or `0E` is target-specific and not established. Examples of `07 04` identity strings of these classes: strings starting `BAI`, `EHP00` and strings starting `HMU`. |
| `operation` | Operation byte as a hex pair: `0D` (read), `0E` (write) or `54` (data-point read). |
| `selector` | Complete selector: the two-byte register id in map notation, or the five-byte selector of the heat pump interface unit section. Empty for the two operation rows. |
| `name` | Canonical name: `snake_case`, describing the quantity. Unit, codec, scaling and access are separate fields; names carry no API prefix. A name is provisional when its `open_question` says so; it stays provisional until the conflict recorded there is resolved. |
| `unit` | Unit of the value after the map's scaling. Empty when there is none or when it is unresolved. |
| `vaillant_friendly_name` | For boiler entries, the diagnostic menu code with its label (for example `d.40 Supply temperature`); the label text follows the community ebusd comments. For the two operation rows, a descriptive expansion of the service name. |
| `vaillant_name` | Vaillant symbolic name for the register, or the service name for the operation rows. Empty where no Vaillant name is known. Vaillant names can differ between devices of one class for the same id; the cell then holds one of them (for example `0x4904`). |
| `ebusd_name` | Name in the community ebusd configurations. For the heat pump interface unit selectors the second name is the one used in the heat pump map. |
| `legacy_api_path` | Earlier API path (`state.*`, `config.*`, `diagnostics.*`, `identity.*`, `energy.*`), kept as correspondence only. It is not a name and not a Vaillant name. |
| `open_question` | Open item for the entry. |

Several observed values in one cell are separated by `` | ``, and the only
multi-value separator is that one. An empty correspondence cell means that no
name is known; it does not mean that the register or a name does not exist.

## Falsification Tests

- Disprove flat addressing by capturing a valid `B509` exchange where bytes
  after `0x0D` or `0x0E` are not a 16-bit address.
- Disprove write semantics with a captured exchange in which a write ACK is not
  followed by a matching read-back value. An ACK plus a matching read-back is
  required before a write is treated as applied, and no write is sent without
  the safety procedure, target qualification and explicit confirmation stated
  for `0E`, `0F` and `10`.
- Disprove a register mapping by changing the physical state and showing the
  documented register value does not change while an alternate register does.

## Unknowns

- Complete register map per product ID and firmware generation.
- Meaning of invalid/unavailable response markers across device classes.
- Whether every target accepts both echoed-op and address-only response forms.
- Whether B509/`0x9A00` (DSN) is available on EHP00/HMU devices for product-type
  gating, or if B514 must be used exclusively for heat pump identification.
- Heat pump interface unit `540200xx` sub-addressing: single-source candidate;
  live validation priority items: CompressorSpeed, Fan1Speed,
  ElectricPowerConsumption, AirInletTemp.
- EHP `01`-suffix register semantics: page/bank selector vs instance selector.
  Live scan comparing `XX00` vs `XX01` needed.

## Open questions

- For the bounded alternatives above, reply-width selection for `07`, the
  address width and conversion of `33`, its minimum<=maximum enforcement,
  the complement algorithm of `39`, and the default/domain conflict of `44`
  remain unresolved. `32` queries status rather than toggling an address.
  `06` still lacks wire adaptation, installed-support and alternative-selection
  evidence; neither a shared prefix nor accepted feedback proves a reset.

- No exchange of the subcommands in the catalogue is included here. Every
  request shape, reply layout and reply width above is a candidate, and the
  behaviour of a target that receives a request it does not implement (reply,
  source address, timing) is not established.
- Whether the two symbolic-address bytes are a 16-bit little-endian number (the
  first byte being the low byte) is unconfirmed on the wire.
- The per-character meaning of the 28-character serial is not established beyond
  the candidate article-number position: which characters carry the year, the
  week and the production site is unknown. The leading `00` byte of window `24`
  and the `FF` filler of window `27` are candidates, and the difference to the
  status-plus-eight-characters description in the overview page is unresolved.
- The `28` request and reply layout is unconfirmed on the wire, and which target
  classes answer it is not established.
- The meaning of the PeBUS address byte of `54` (candidate values `0A` and `02`), the use of
  the feedback bits by a given target, and the equivalence of the heat
  pump interface unit `54 02 00 REG TYPE` selectors with this read are unconfirmed on the wire.
- The `0D`, `0E`, `0F`, `10` and `29` subcommands have no per-product decoder
  here. Whether a given target answers `0D` with the operation echoed, the
  address echoed or the data alone is not established, and no reply layout is
  established for `38`, `5A`, `5B` and `5C`.
- For `38`, `5A`, `5B` and `5C` only a request service byte `B5` and a
  positive reply byte `F5` are candidates; whether a subcommand byte follows
  `PB SB` is not established.
- The bit maps of the `18` sensor and temperature error blocks are not
  established.
- A single Vaillant name for the whole class is not established for every id:
  for some ids (for example `0x4904`) the meaning differs between devices, and
  for `0x0E04` and `0xA500` it is unresolved which devices of the class use
  which id.
- Which flag value of subcommand `10` enables remote control is unresolved.
- The 15-minute remote-control timer of `0F` is a candidate, unconfirmed on the
  wire.
- The meaning of the address `FFFF` is not established.
- Whether the 22-character field of `04` and `03` equals the concatenation of
  the four serial-number windows, the commit order of the four `20` to `23`
  writes and the 25-byte `04` reply are not established.
- The meaning of reply byte 0 of `28`, the relation of the product-number byte 1
  to bytes 4 and 5, and the build-number byte are not established.

## References

- Public TypeSpec: [_templates.tsp](https://github.com/john30/ebusd-configuration/blob/HEAD/src/vaillant/_templates.tsp)
- Public config corpus: [john30/ebusd-configuration](https://github.com/john30/ebusd-configuration/tree/HEAD/src/vaillant)
- Boiler register map: [`ebus-vaillant-B509-boiler-register-map.md`](ebus-vaillant-B509-boiler-register-map.md)
- Heat pump register map: [`ebus-vaillant-B509-heatpump-register-map.md`](ebus-vaillant-B509-heatpump-register-map.md)
- Register name correspondence fixture: [`fixtures/b509-register-name-correspondence.csv`](fixtures/b509-register-name-correspondence.csv)
- Diagnostic selector family: [`ebus-vaillant-B503.md`](ebus-vaillant-B503.md)
- Consolidated local reference: [`ebus-vaillant.md`](ebus-vaillant.md)
- Historical Vaillant reference: [Pittnerovi eBUS page](https://www.pittnerovi.com/jiri/hobby/electronics/ebus/)
