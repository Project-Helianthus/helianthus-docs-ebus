# B519: opaque data and independent CRC bytes

## Scope and evidence grades

This partial Vaillant family catalog describes candidate declarations for
`B5 19 <selector>`. **Hypothesis** applies to all native layouts, field meanings
and physical interpretations below. **Proven** applies only to the declared
representation checked by the [synthetic examples](fixtures/ac16_opaque_programming.json);
these are not captures or physical qualification. Physical qualification is
**Unknown**. No runtime capability or write admission follows from this catalog.

The [existing B519 overview](ebus-vaillant.md#b519-test-and-echo-services)
contains older candidate meanings and CRC coordinates. Those alternatives remain
unreconciled; this finite slice does not adopt their coordinates, echo/broadcast
behavior, or AA fill interpretation. It does not replace other qualified variants.
The variant for this slice is Unknown.

## Candidate alternatives

Logical positions include the service prefix: B5 at 0, 19 at 1 and selector at 2;
they are not physical wire offsets. `Unknown` extent means absent information,
not zero length. `none declared` does not establish a physically empty payload.
All rows preserve the raw PDU, including unresolved bytes.

| Family | Variant | Direction | Service | Selector | Alternative | Layout | Fields at logical position | Extent | Grade |
|---|---|---|---|---|---|---|---|---|---|
| Vaillant | Unknown | request | B519 | 00 | request | no-declared-inputs | none declared | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 00 | positive | partial | CRC@Unknown | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 00 | negative | Unknown | none declared | Unknown | Hypothesis |
| Vaillant | Unknown | request | B519 | 01 | request | declared-fields | data@3 | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 01 | positive | partial | CRC@Unknown | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 01 | negative | Unknown | none declared | Unknown | Hypothesis |
| Vaillant | Unknown | request | B519 | 02 | request | no-declared-inputs | none declared | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 02 | positive | partial | CRC@Unknown | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 02 | negative | Unknown | none declared | Unknown | Hypothesis |
| Vaillant | Unknown | request | B519 | 03 | request | declared-fields | data@3 | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 03 | positive | declared-fields | data@3 | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 03 | negative | Unknown | none declared | Unknown | Hypothesis |
| Vaillant | Unknown | request | B519 | 04 | request | declared-fields | data@3 | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 04 | positive | partial | CRC@Unknown | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 04 | negative | Unknown | none declared | Unknown | Hypothesis |
| Vaillant | Unknown | request | B519 | 05 | request | declared-fields | data@3 | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 05 | positive | partial | CRC@Unknown | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 05 | negative | Unknown | none declared | Unknown | Hypothesis |
| Vaillant | Unknown | request | B519 | 06 | request | declared-fields | data@3 | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 06 | positive | prefix-only | none declared | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 06 | negative | Unknown | none declared | Unknown | Hypothesis |
| Vaillant | Unknown | request | B519 | 07 | request | declared-fields | data@3 | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 07 | positive | partial | CRC@Unknown | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 07 | negative | Unknown | none declared | Unknown | Hypothesis |
| Vaillant | Unknown | request | B519 | 08 | request | declared-fields | slave-address@3, data@4 | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 08 | positive | partial | CRC@Unknown | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | 08 | negative | Unknown | none declared | Unknown | Hypothesis |
| Vaillant | Unknown | request | B519 | AA | request | no-declared-inputs | none declared | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | AA | positive | declared-fields | data@3 | Unknown | Hypothesis |
| Vaillant | Unknown | response | B519 | AA | negative | Unknown | none declared | Unknown | Hypothesis |

A prefix-only positive declaration for 06 does not establish no physical response.
Positive CRC coordinates on the partial alternatives are absent, never inferred.
Negative alternatives remain unresolved independently for each selector.

## Candidate field representations

| Field | Representation | Conversion | Extent | Minimum | Maximum | Default | Enum or sentinel | Grade |
|---|---|---|---|---|---|---|---|---|
| data | opaque-bytefield | unchanged | through-end-of-PDU | 0 bytes | Unknown | Unknown | none established | Hypothesis |
| CRC | raw-u8 | unchanged | 1 byte | 0 | 255 | 0 | none established | Hypothesis |
| slave-address | raw-u8 | unchanged | 1 byte | 0 | 255 | 0 | none established | Hypothesis |

Data is an unchanged bytefield through end-of-PDU. It is not scalar, text, a
fixed buffer or a promise of unlimited carrier capacity. No maximum is established.
The declared minimum of zero does not establish physical acceptance of empty data.
CRC and slave-address retain independent raw numbers; zero and FF have no
established sentinel meanings. No CRC calculation or address interpretation follows
from their raw u8 representation. AA is a separate selector, not a fill-byte/count.

Synthetic data `[00, FF, 41]` remains three opaque bytes, including zero and FF;
`[]` illustrates only the declared minimum. Synthetic CRC and slave-address
values `00` and `FF` remain the raw numbers 0 and 255.

## Unresolved properties

| Property | Grade |
|---|---|
| crc_algorithm | Unknown |
| crc_coverage | Unknown |
| crc_initialization | Unknown |
| persistence_reset | Unknown |
| correlation | Unknown |
| transport_crc_relation | Unknown |
| mode_dependent_reply_policy | Unknown |
| full_positive_layouts | Unknown |
| physical_native_effects | Unknown |
| negative_layouts | Unknown |
| variant | Unknown |
| data_maximum | Unknown |
| prefix_only_physical_response | Unknown |
| native_adaptation | Unknown |
| peer_effects | Unknown |

Mode-dependent reply policy, full positive layouts and physical/native effects
remain Unknown and outside this partial catalog. Native adaptation and peer effects
remain Unknown. Unresolved evidence must retain its raw bytes and any independent
useful fields; a failed interpretation does not erase last-known-good information
or qualify another alternative. Physical qualification requires independent native
evidence; these declarations provide none.
