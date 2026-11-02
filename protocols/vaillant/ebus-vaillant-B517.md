# B517 tunnel declarations and partial B518 identity

The [native overview](ebus-vaillant.md#b517-and-b518-sub-ebus-tunnel)
preserves two unresolved readings. The declarations below retain both objects;
B518 is not an alias for the B517 positive form. Other qualified variants in
the overview remain separate. These are family declarations, not observations
of an installed device.

## Candidate fields

Every row is **Hypothesis**. Coordinates are logical positions including
constants, not demonstrated physical packet offsets. An absent body extent is
**Unknown**, not zero. Unset encoding, width and byte order remain absent.

| Family | Direction | Service declaration | Logical fields | Grade |
|---|---|---|---|---|
| B517 | request | B5/17 | B5 at 0; 17 at 1; destination at 2; opaque data at 3 through end-of-PDU | Hypothesis |
| B517 | positive | B5/18 | B5 at 0; 18 at 1; opaque data at 2 through end-of-PDU | Hypothesis |
| B518 | request | Unknown | B5 only at 0; body extent absent | Hypothesis |
| B518 | positive | Unknown | F5 only at 0; body extent absent | Hypothesis |

Each stated constant is eight bits. B518's name adds no encoded subgroup 18,
operation, body, CRC, success predicate or one-byte physical packet. Its two
abstract sides contain only their stated constant. There is no operation byte
in the B517 declaration; the request's logical position 2 is the destination.

| Field | Domain or extent | Default | Interpretation | Grade |
|---|---|---|---|---|
| B517 destination | raw u8 0..255 | 8 | raw destination; installed address Unknown | Hypothesis |
| B517 request data | 0..65535 bytes, through end-of-PDU | absent | opaque; abstract maximum only | Hypothesis |
| B517 positive data | 0..65535 bytes, through end-of-PDU | absent | opaque; abstract maximum only | Hypothesis |

Default 8 is not an installed address. The abstract maximum 65535 is neither a
scalar codec nor a demonstrated transport capacity. Opaque bytes receive no
scalar conversion. Empty opaque data remains empty/partial; it proves no
successful exchange. Raw bytes and independent useful fields remain preserved;
incomplete evidence does not erase partial last-known-good state or turn it
into a fresh result.

## Policy and distinct adaptation alternative

The following **Hypothesis** policy metadata is separate from native field
ranges. No client or transport is implemented by these declarations.

| Policy | Declared value | Grade |
|---|---|---|
| tunnel destination domain | 1..254 | Hypothesis |
| inner destination | original destination | Hypothesis |
| inner opaque data | original PDU | Hypothesis |
| returned data context | original service | Hypothesis |
| local result codes | raw 10, 6, 7; meanings Unknown | Hypothesis |
| remote feedback | separate from local result codes | Hypothesis |

A separate adaptation alternative requires every predicate below. It is not a
universal prefix-removal rule. Missing byte 4 leaves the equation unresolved;
a length match alone establishes only the declared length equation.

| Predicate | Required value | Grade |
|---|---|---|
| ready-state | 3 | Hypothesis |
| final option | nonzero | Hypothesis |
| length equation | input byte 4 + 6 equals available length | Hypothesis |
| request service | B5/17 | Hypothesis |
| input service | B5/18 | Hypothesis |

A synthetic envelope of length 10 with byte4=4 satisfies only that equation.
Changing byte4 to 5 fails the equation and does not establish a valid
alternative. All other qualification requirements remain independent.

## Evidence and limits

The [synthetic examples](fixtures/ac14_tunnel.json) validate the declared
representation only. **Proven** applies only to mechanically checked software
representation; all physical interpretations remain **Hypothesis**.
Qualification is separate from either grade.

| Unresolved property | Grade |
|---|---|
| physical relationship of B517/B518 | Unknown |
| destination roles | Unknown |
| forwarder | Unknown |
| correlation | Unknown |
| timeout | Unknown |
| refusal | Unknown |
| fragmentation | Unknown |
| transport/peer support | Unknown |
| scheduling | Unknown |
| write permission | Unknown |
| native adaptation | Unknown |
| peer effects | Unknown |
| physical qualification | Unknown |

No runtime capability, transmit route, automatic native qualification or write
admission follows. Unsupported or incomplete evidence keeps admission withheld.
