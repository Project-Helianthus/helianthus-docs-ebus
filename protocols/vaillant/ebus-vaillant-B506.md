# Vaillant B506 I/O Test

`PB=0xB5`, `SB=0x06`.

## Status

`B506` is modeled in john30 TypeSpec as an installer-auth write family for I/O
or actuator tests. It is not safe for blind probing on production heating
systems.

Evidence labels:

- `PUBLIC_CONFIG`: public john30 `ebusd-configuration` repository.
- `INFERENCE`: falsifiable interpretation from the evidence above.

## Wire Shape

Known configured rows use:

```text
Start/select test:
  02 value

Stop test:
  01
```

The `value` byte is target/profile-specific.

## Known Selectors

| Request payload | Name | Response shape | Evidence | Falsification test |
|---|---|---|---|---|
| `01` | stop I/O test | ACK/status | | On isolated hardware, start a documented test and show `B506 01` does not stop it after ACK. |
| `02 <value>` | select/start I/O test | ACK/status plus physical side effect | | On isolated hardware, send a documented value and show no actuator/log/test-mode effect. |

## Safety Rule

Only run `B506` against a controlled test fixture or an installation explicitly
prepared for actuator testing. A reasonable safe sequence is:

```text
1. Send stop:        B5 06 01
2. Send one test:    B5 06 02 <documented_value>
3. Observe locally.
4. Send stop again:  B5 06 01
```

Do not use this sequence on production hardware unless the operator has
explicitly accepted the risk.

## Candidate op catalogue

The candidate layouts of B506 cover the ops `B5 06 00` to `B5 06 21` (no
candidate layout is known for `03`), unconfirmed on the wire. They cover remote
control of outputs, input and sensor tests, ROM and EEPROM check requests, an
end-of-line test mode, radio test services and a button test. Candidate
interpretation, unconfirmed on the wire: most of them are installer or factory
test services and many are mutative. The field-level layout of every op is in
[`fixtures/b506-b508-candidate-fields.csv`](fixtures/b506-b508-candidate-fields.csv);
`vaillant_name` in that file is a correspondence column (Vaillant name,
correspondence only), not a canonical name. The column `candidate_variant`
separates the two alternative layouts of the `B5 06 02` request (output bits,
or backlight only on some controllers).

Offsets count from the first byte of the service prefix (PB, SB and the op
byte): offset 0 = `B5`, 1 = `06`, 2 = op byte. A target response on the bus
carries no such prefix (eBUS framing: `NN`, data, CRC); how the candidate
response offsets map onto the bytes of a bus response is unconfirmed on the
wire. The request length NN counts the op byte plus its data bytes, and "≥"
marks a variable-length field (only `11`: the parameter set of its request, and
its reply, which carries a length byte). **Hypothesis**: response offset 3 is the first
data byte of a bus response (see
[`ebus-vaillant.md`](ebus-vaillant.md#other-b5-services-candidate-layouts)).
The descriptions are plain-language and are not canonical names.

| Op | Candidate description | Request NN | Reply bytes |
|---|---|---:|---:|
| `B5 06 00` | remote control of all outputs | 2 | 0 |
| `B5 06 01` | disable remote control of all outputs | 1 | 0 |
| `B5 06 02` | testing outputs | 2 | 0 |
| `B5 06 04` | testing controller inputs 1 | 1 | 10 |
| `B5 06 05` | testing controller inputs 2 | 1 | 10 |
| `B5 06 06` | testing controller inputs 3 | 1 | 8 |
| `B5 06 07` | testing module inputs | 1 | 9 |
| `B5 06 08` | ROM checksum or CRC request | 2 | 3 |
| `B5 06 09` | ROM check response (carried in the request) | 4 | 0 |
| `B5 06 0A` | testing heat-pump inputs 1 | 1 | 10 |
| `B5 06 0B` | testing heat-pump inputs 2 | 1 | 10 |
| `B5 06 0C` | testing heat-pump inputs 3 | 1 | 10 |
| `B5 06 0D` | testing heat-pump inputs 4 | 1 | 10 |
| `B5 06 0E` | testing heat-pump inputs 5 | 1 | 10 |
| `B5 06 0F` | EEPROM check request; field association unresolved below | 2 (older candidate shape) | Unknown |
| `B5 06 10` | EEPROM check response (older candidate association) | Unknown | 0 (older candidate shape) |
| `B5 06 11` | test mode for hardware validation | ≥2 | ≥1 |
| `B5 06 12` | radio test: send continuous wave | 2 | 0 |
| `B5 06 13` | radio test: configure test telegram | 5 | 0 |
| `B5 06 14` | radio test: start or stop sending test telegrams | 2 | 0 |
| `B5 06 15` | radio test: set operation mode | 2 | 0 |
| `B5 06 16` | radio test: write one transceiver register | 3 | 0 |
| `B5 06 17` | radio test: read one transceiver register | 2 | 1 |
| `B5 06 18` | radio test: transceiver configuration | 2 | 0 |
| `B5 06 19` | radio test: trigger teach-in | 2 | 1 |
| `B5 06 1A` | radio test: check transceiver connection | 1 | 1 |
| `B5 06 1B` | radio test: detection of a radio device | 2 | 2 |
| `B5 06 1C` | read outdoor-unit sensor values 1 | 1 | 10 |
| `B5 06 1D` | read outdoor-unit sensor values 2 | 1 | 10 |
| `B5 06 1E` | read indoor-unit sensor values | 1 | 6 |
| `B5 06 1F` | testing sensor-module inputs 1 | 1 | 10 |
| `B5 06 20` | testing sensor-module inputs 2 | 1 | 4 |
| `B5 06 21` | button testing | 4 | 0 |

The `01` (stop test) and `02 <value>` (select or start test) forms above are
consistent with the candidate ops `01` (disable remote control of all outputs)
and `02` (two distinct output variants; see the scoped declarations below).

## Candidate encodings and enumerations

Every item in this section is a candidate layout, unconfirmed on the wire.

- **Outputs** (`B5 06 02`): the two independent candidate variants are
  declared in the scoped table below. `B5 06 00` sets all outputs (candidate):
  `1` on, any other value off.
- **Inputs and sensors** (`04`..`07`, `0A`..`0E`, `1C`..`20`): candidate,
  unconfirmed on the wire: temperatures are mostly `i16` LE ÷16 °C. Several
  fields in the heat-pump input services may be non-temperature quantities (for
  example a brine pressure, a power or a switch) but are carried as `u16` raw or
  as a temperature value; the unit of these fields is unresolved. The unit of the
  water-pressure field of `1F` is bar (`u16` LE ÷16) and the frequency inputs of
  `20` are in l/min (candidate).
- **ROM check** (`08`): candidate, unconfirmed on the wire: the check-type
  byte in the request is `0` send back the supported types, `2` 16-bit checksum
  for the whole ROM, `4` 16-bit CRC, `8` 8-bit CRC, `16` 8-bit CRC with the eBUS
  polynomial, `255` read the CRC. The candidate reply has check-type and check
  fields; no polynomial, initial value or covered range is established. `09`
  carries the candidate check fields in the request. These ROM declarations do
  not establish EEPROM algorithms, returned widths or operation association;
  the bounded EEPROM declaration is below.
- **Radio details**: candidate, unconfirmed on the wire: `13` wait time between
  two test telegrams at offset 5 is a raw `u8` × 100 ms (1..255); `15` selects
  the transceiver mode `0` sleep, `1` wake and idle, `2` standby, `3` receive, `4`
  calibrate, `5` flush the receive buffer, `6` idle, flush and receive; `1A`
  reports the connection as OK only for the raw value 181 (`B5`), any other value
  is not OK; `1B` returns the detection state at offset 3 (`0` nothing received,
  `1` received) and an RSSI at offset 4 as a raw `u8` (a second candidate reading
  is a signed value in half-dB steps, valid only when the detection state is 1);
  `19` teach-in `0` stop, `1` start, `2` status, with a reply of `0` running or
  `1` not running.
- **Button testing** (`21`): candidate, unconfirmed on the wire: button bits
  1..4, 12, 34, ALL at offset 3, an `i8` increment at offset 4 and buttons 5..8
  at offset 5.

## B5 06 11: end-of-line test (service shape)

Candidate, unconfirmed on the wire: `B5 06 11` is an end-of-line test service
whose request is a one-byte test mode at offset 3 followed by a variable
parameter set, and whose reply carries a length byte. Candidate interpretation,
unconfirmed on the wire: the test-mode values are factory test and programming
controls that change device state; none of them is classified as safe to send,
and a separately established safety procedure is needed before any of them is
sent. Do not run them on a production bus. The candidate test-mode byte values,
unconfirmed on the wire, are: `0` stop active test modes; `1` and `2` transmit
the character `0xAA` or `0x00` continuously on the bus; `3` transmit the request
`07 04` continuously to the configured target address; `4` stop generating the
automatic SYN character; `5` generate no initiator request telegrams; `6`
combine modes 3 and 4; `7`, `8` and `9` product-specific EMC, long-term and
external flash-ROM test modes; `10` enter low-power mode; `32`..`37` radio tests
(unmodulated carrier; pseudo-random sequence with modulation, continuous or not;
with listen-before-talk; listening with a statistical counter). The parameter
representations are declared below by explicit decimal key; their bounds where
absent, reply bodies and framing remain Unknown.

## Scoped parameter and checksum declarations

**Hypothesis**: the following finite declarations concern only the Vaillant
family, PB `B5`, SB `06`. Native wire qualification and physical qualification
are **Unknown**. The public native contract is this table; the independently
merged [AE05 catalog](https://github.com/Project-Helianthus/helianthus-ebusreg/pull/239)
is corroborating implementation evidence for exactly the production-test,
backlight-only, three-output and EEPROM checksum entries, not proof of a
broader completed catalog. The [synthetic cases](fixtures/ae06_b506_candidates.json)
retain raw representations without qualifying device behavior.

Keys in the parameter union are decimal selectors, explicitly associated with
representations; row order has no meaning. All other keys remain unmapped.
Logical position is not a wire offset. Direction and logical position are
Unknown in this bounded declaration, even where older enclosing service shapes
above suggest a request layout. The EEPROM entry does not assign an operation
or inherit the older `0F`/`10` field associations.

| Grade | Identity (PB B5 / SB 06, Vaillant family) | Direction | Logical position / extent | Raw type / domain | Scale | Sentinel / default / conflict | Unresolved properties |
|---|---|---|---|---|---|---|---|
| Hypothesis | OP11 production-test parameter; keys 0,1,2,4,5 | Unknown | Position Unknown; through end-of-data | Opaque bytes | Unknown | Sentinel Unknown; default Unknown; row order is not key association | Minimum/maximum length Unknown; zero length representable; empty-request acceptance Unknown |
| Hypothesis | OP11 production-test parameter; keys 3,6,7,8,9,32,33,34,35,36,37 | Unknown | Position Unknown; one byte | Raw byte 00..FF | Unknown | Sentinel Unknown; default Unknown; row order is not key association | Meaning, unit and additional constraints Unknown |
| Hypothesis | OP11 production-test parameter; key 10 | Unknown | Position Unknown; one byte | Boolean 0=no, 1=yes; 2 unmapped | Unknown | Sentinel Unknown; default Unknown; no meaning invented for other values | Behavior for unmapped values Unknown |
| Hypothesis | OP02 backlight-only outputs | Unknown | Position Unknown; one byte | Bit 0 backlight; mask 01; reserved mask FE | Unknown | Sentinel Unknown; default Unknown; reserved bits retained raw | Bits 1..7 reserved; variant selection Unknown; no automatic choice |
| Hypothesis | OP02 three-output outputs | Unknown | Position Unknown; one byte | Bits 0..2 outputs 1..3; mask 07; reserved mask F8 | Unknown | Sentinel Unknown; default Unknown; reserved bits retained raw | Bits 3..7 reserved; variant selection Unknown; no automatic choice |
| Hypothesis | EEPROM checksum_type; operation Unknown | Unknown | Position Unknown; type one byte; returned width Unknown | 00=query-supported-types; 01..7F=scalar-type; 80 unmapped | Unknown | Sentinel Unknown; default Unknown; scalar, not flags; conflicting EEPROM algorithm assignments withdrawn | Algorithm Unknown; returned checksum width Unknown; completion Unknown; checksum data Unknown |

For the same raw `07`, backlight-only retains active bits `01` and reserved
bits `06`; three-output retains active bits `07` and reserved bits `00`.
Both reconstruct raw `07`. This does not select a variant. Opaque `00 AA FF`
and zero-length representations retain all bytes; neither establishes accepted
request lengths. Checksum `03` is one scalar type, not flags `01` and `02`;
`80` has no new declared type. Algorithm, returned checksum width, completion
and checksum data remain independently Unknown, including for query `00`.
No declaration establishes writable behavior, execution authority or admission.
No stability guarantee is made before 1.0.

## Profiles

No op of this service is known to be available only on PeBUS (candidate);
whether the service is available under the PeBUS profile is not established (see
[EBUS and PeBUS protocol profiles](ebus-vaillant.md#ebus-and-pebus-protocol-profiles)).

## Open questions

- Complete actuator enum per target class.
- Whether non-HMU, solar, or mixer modules share any selector values.
- Whether some devices require a separate service/installer unlock before ACK.
- The candidate ops are known only as candidate layouts; no exchange of them was
  observed beyond the examples on this page, and whether any device implements
  them is not established.
- ROM check algorithms and coverage (`08`, `09`) remain unestablished. EEPROM
  algorithm, returned checksum width, completion, checksum data and operation
  association remain independently Unknown; scalar type declarations do not
  resolve them.
- The units of the heat-pump input fields that may be non-temperature quantities
  but are carried as temperatures (`0B`, `0C`) are unresolved.
- OP11 parameter representations have the explicit keyed Hypothesis declarations
  above. Opaque bounds, empty-request acceptance, reply body lengths and framing
  remain Unknown; the test-mode values are unconfirmed on the wire.
- Several candidate default values lie outside their candidate intervals (see the
  fixture; for example the `13` wait time default 0 against 1..255 and the `18`
  configuration default 0 against 1..6); the intended defaults are unresolved.
- How the candidate response offsets map onto the data bytes of a bus response is
  unconfirmed on the wire.
- OP02 backlight-only and three-output remain independent Hypothesis variants;
  which applies to a device family remains Unknown. Reserved bits stay raw.
- Whether the RSSI of `B5 06 1B` at offset 4 is a raw `u8` or a signed value in
  half-dB steps that is valid only when the detection state is 1 is unresolved.

## References

- Public TypeSpec: [iotesthp_inc.tsp](https://github.com/john30/ebusd-configuration/blob/HEAD/src/vaillant/iotesthp_inc.tsp)
- Public TypeSpec: [iotestbsol_inc.tsp](https://github.com/john30/ebusd-configuration/blob/HEAD/src/vaillant/iotestbsol_inc.tsp)
- Public TypeSpec: [iotestbmc_inc.tsp](https://github.com/john30/ebusd-configuration/blob/HEAD/src/vaillant/iotestbmc_inc.tsp)
