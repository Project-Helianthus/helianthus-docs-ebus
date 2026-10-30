# B509 OP59 independent quantity views

> AGPL-3.0. This page is a software contract for one pure helper.
> It does not restate a native family page and it does not qualify a device.

## Contract status

The helper below is the hypothetical signature of the ab09an09 helper.
This page uses that signature only and does not import an implementation.

`view = ab09an09.view_b509_op59_candidate_fields(selection, slices)`

The call is a pure explicit B509 OP59 candidate-field view. `selection` carries family, variant, operation, and direction as independent values. `slices` carries temperature, flow, volume, minimum volume, and maximum volume as independent optional byte slices. The caller draws every boundary. The helper does not parse a packet. The helper does not detect a family from a byte offset or from a slice length.

Nothing in this contract is stable before Helianthus 1.0. This page creates no namespace. This page adds no authorization gate. Roadmap wording remains 0.11. The helper registers no write builder and no registry method. This helper adds no GraphQL field and no MCP tool.

A numeric result of an admitted conversion is a Proven software result and nothing more. Semantic grade remains Hypothesis and native grade remains Unknown on every field, including absent, malformed, raw, and withheld fields. Presence, freshness, and execution are separate from these grades and are not decided here.

## Selection and admission

Admission is fail-closed. The helper copies the supplied selection and returns that copy. Omitted family, variant, operation, and direction stay omitted. The helper does not substitute `B509`, a variant, `59`, or a direction.

The view is admitted only when family is `B509`, variant is a non-empty explicit token, operation is `59`, and direction is `request` or `response`. Any other explicit family, operation, or direction is not admitted. An empty variant or an empty direction is not admitted. Which product variants exist, and which native direction carries these quantities, stay Unknown. Admission of an explicit variant token does not qualify that variant.

When the view is not admitted, temperature, flow, and volume slices of exactly two octets are withheld: their raw bytes remain and they have no numeric value. A malformed slice stays malformed. Opaque slices stay raw.

## Conversion parameters

Temperature, flow, and volume use little-endian byte order. A convertible slice converts only when it is exactly two octets and the view is admitted. Any other width is malformed. Malformed and absent slices have no numeric value.

The arithmetic below is the software reading of the hypothesis. It is not native qualification.

- Selected temperature is a signed little-endian 16-bit quantity divided by 16, in degrees Celsius.
- Selected flow is an unsigned little-endian 16-bit quantity divided by 100, in litres/minute.
- Selected volume is an unsigned little-endian 16-bit quantity divided by 10, in litres.

Minimum volume and maximum volume stay opaque raw slices. The helper infers no scalar width and applies no conversion to either field. Whether a native conversion exists for either field is Unknown.

A unit label is a label. Applying a unit label as a second scale is outside this contract. `unit_scale_passes` is 1 for temperature, flow, and volume, and 0 for the opaque fields.

Dividing temperature by 256 is outside this contract. Signed flow is outside this contract. Signed volume is outside this contract. Converting minimum volume or maximum volume is outside this contract. Assigning a missing sentinel to temperature 00 80 is outside this contract. Dropping every field after one malformed field is outside this contract.

The conversion table is the normative parameter set.

| field | signedness | endian | width_octets | divisor | unit_label | unit_scale_passes | sentinel | numeric_grade | semantic_grade | native_grade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| temperature | signed | little | 2 | 16 | °C | 1 | none | Proven | Hypothesis | Unknown |
| flow | unsigned | little | 2 | 100 | L/min | 1 | none | Proven | Hypothesis | Unknown |
| volume | unsigned | little | 2 | 10 | L | 1 | none | Proven | Hypothesis | Unknown |
| minimum_volume | none | none | none | none | none | 0 | none | none | Hypothesis | Unknown |
| maximum_volume | none | none | none | none | none | 0 | none | none | Hypothesis | Unknown |

Temperature `00 80` remains the candidate numeric value -2048. It is not a missing sentinel. Full-scale flow `FF FF` is 655.35 litres/minute. Full-scale volume `FF FF` is 6553.5 litres. The helper does not clip either value.

## Synthetic examples

An absent or malformed temperature does not erase a valid flow, and the same independence holds for every other slice. Each row varies one declared input except `rejected-family-truncated-temperature`, which combines a rejected family with a truncated temperature. Expected numerics are independent of the other rows. Raw forms are echoed exactly, including a one-octet maximum and a two-octet minimum.

The helper copies each supplied slice before it reads it and returns new raw copies. Mutating an input after the call, or mutating a returned raw slice or selection, does not change a stored result or a later call.

| id | family | variant | operation | direction | temperature | flow | volume | minimum_volume | maximum_volume | admitted | temperature_outcome | flow_outcome | volume_outcome | minimum_volume_outcome | maximum_volume_outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| canonical | B509 | alpha | 59 | response | F0 FF | 64 00 | 0A 00 | FF FF | 01 | yes | converted:F0 FF:-1 | converted:64 00:1 | converted:0A 00:1 | raw:FF FF | raw:01 |
| temperature-low-magnitude | B509 | alpha | 59 | response | 00 80 | 64 00 | 0A 00 | FF FF | 01 | yes | converted:00 80:-2048 | converted:64 00:1 | converted:0A 00:1 | raw:FF FF | raw:01 |
| flow-full-scale | B509 | alpha | 59 | response | F0 FF | FF FF | 0A 00 | FF FF | 01 | yes | converted:F0 FF:-1 | converted:FF FF:655.35 | converted:0A 00:1 | raw:FF FF | raw:01 |
| volume-full-scale | B509 | alpha | 59 | response | F0 FF | 64 00 | FF FF | FF FF | 01 | yes | converted:F0 FF:-1 | converted:64 00:1 | converted:FF FF:6553.5 | raw:FF FF | raw:01 |
| temperature-zero | B509 | alpha | 59 | response | 00 00 | 64 00 | 0A 00 | FF FF | 01 | yes | converted:00 00:0 | converted:64 00:1 | converted:0A 00:1 | raw:FF FF | raw:01 |
| flow-distinct | B509 | alpha | 59 | response | F0 FF | 65 00 | 0A 00 | FF FF | 01 | yes | converted:F0 FF:-1 | converted:65 00:1.01 | converted:0A 00:1 | raw:FF FF | raw:01 |
| volume-distinct | B509 | alpha | 59 | response | F0 FF | 64 00 | 0B 00 | FF FF | 01 | yes | converted:F0 FF:-1 | converted:64 00:1 | converted:0B 00:1.1 | raw:FF FF | raw:01 |
| temperature-as-flow-bytes | B509 | alpha | 59 | response | 64 00 | 64 00 | 0A 00 | FF FF | 01 | yes | converted:64 00:6.25 | converted:64 00:1 | converted:0A 00:1 | raw:FF FF | raw:01 |
| flow-as-volume-bytes | B509 | alpha | 59 | response | F0 FF | 0A 00 | 0A 00 | FF FF | 01 | yes | converted:F0 FF:-1 | converted:0A 00:0.1 | converted:0A 00:1 | raw:FF FF | raw:01 |
| volume-as-flow-bytes | B509 | alpha | 59 | response | F0 FF | 64 00 | 64 00 | FF FF | 01 | yes | converted:F0 FF:-1 | converted:64 00:1 | converted:64 00:10 | raw:FF FF | raw:01 |
| temperature-omitted | B509 | alpha | 59 | response | omitted | 64 00 | 0A 00 | FF FF | 01 | yes | absent | converted:64 00:1 | converted:0A 00:1 | raw:FF FF | raw:01 |
| flow-omitted | B509 | alpha | 59 | response | F0 FF | omitted | 0A 00 | FF FF | 01 | yes | converted:F0 FF:-1 | absent | converted:0A 00:1 | raw:FF FF | raw:01 |
| volume-omitted | B509 | alpha | 59 | response | F0 FF | 64 00 | omitted | FF FF | 01 | yes | converted:F0 FF:-1 | converted:64 00:1 | absent | raw:FF FF | raw:01 |
| minimum-omitted | B509 | alpha | 59 | response | F0 FF | 64 00 | 0A 00 | omitted | 01 | yes | converted:F0 FF:-1 | converted:64 00:1 | converted:0A 00:1 | absent | raw:01 |
| maximum-omitted | B509 | alpha | 59 | response | F0 FF | 64 00 | 0A 00 | FF FF | omitted | yes | converted:F0 FF:-1 | converted:64 00:1 | converted:0A 00:1 | raw:FF FF | absent |
| slices-omitted | B509 | alpha | 59 | response | omitted | omitted | omitted | omitted | omitted | yes | absent | absent | absent | absent | absent |
| temperature-empty | B509 | alpha | 59 | response | empty | 64 00 | 0A 00 | FF FF | 01 | yes | malformed:(empty) | converted:64 00:1 | converted:0A 00:1 | raw:FF FF | raw:01 |
| flow-empty | B509 | alpha | 59 | response | F0 FF | empty | 0A 00 | FF FF | 01 | yes | converted:F0 FF:-1 | malformed:(empty) | converted:0A 00:1 | raw:FF FF | raw:01 |
| volume-empty | B509 | alpha | 59 | response | F0 FF | 64 00 | empty | FF FF | 01 | yes | converted:F0 FF:-1 | converted:64 00:1 | malformed:(empty) | raw:FF FF | raw:01 |
| temperature-truncated | B509 | alpha | 59 | response | F0 | 64 00 | 0A 00 | FF FF | 01 | yes | malformed:F0 | converted:64 00:1 | converted:0A 00:1 | raw:FF FF | raw:01 |
| flow-truncated | B509 | alpha | 59 | response | F0 FF | 64 | 0A 00 | FF FF | 01 | yes | converted:F0 FF:-1 | malformed:64 | converted:0A 00:1 | raw:FF FF | raw:01 |
| volume-truncated | B509 | alpha | 59 | response | F0 FF | 64 00 | 0A | FF FF | 01 | yes | converted:F0 FF:-1 | converted:64 00:1 | malformed:0A | raw:FF FF | raw:01 |
| temperature-wide | B509 | alpha | 59 | response | F0 FF 00 | 64 00 | 0A 00 | FF FF | 01 | yes | malformed:F0 FF 00 | converted:64 00:1 | converted:0A 00:1 | raw:FF FF | raw:01 |
| flow-wide | B509 | alpha | 59 | response | F0 FF | 64 00 00 | 0A 00 | FF FF | 01 | yes | converted:F0 FF:-1 | malformed:64 00 00 | converted:0A 00:1 | raw:FF FF | raw:01 |
| volume-wide | B509 | alpha | 59 | response | F0 FF | 64 00 | 0A 00 00 | FF FF | 01 | yes | converted:F0 FF:-1 | converted:64 00:1 | malformed:0A 00 00 | raw:FF FF | raw:01 |
| minimum-narrow | B509 | alpha | 59 | response | F0 FF | 64 00 | 0A 00 | FF | 01 | yes | converted:F0 FF:-1 | converted:64 00:1 | converted:0A 00:1 | raw:FF | raw:01 |
| minimum-wide | B509 | alpha | 59 | response | F0 FF | 64 00 | 0A 00 | FF FF 00 | 01 | yes | converted:F0 FF:-1 | converted:64 00:1 | converted:0A 00:1 | raw:FF FF 00 | raw:01 |
| maximum-wide | B509 | alpha | 59 | response | F0 FF | 64 00 | 0A 00 | FF FF | 01 02 | yes | converted:F0 FF:-1 | converted:64 00:1 | converted:0A 00:1 | raw:FF FF | raw:01 02 |
| family-b524 | B524 | alpha | 59 | response | F0 FF | 64 00 | 0A 00 | FF FF | 01 | no | withheld:F0 FF | withheld:64 00 | withheld:0A 00 | raw:FF FF | raw:01 |
| family-lowercase | b509 | alpha | 59 | response | F0 FF | 64 00 | 0A 00 | FF FF | 01 | no | withheld:F0 FF | withheld:64 00 | withheld:0A 00 | raw:FF FF | raw:01 |
| family-omitted | omitted | alpha | 59 | response | F0 FF | 64 00 | 0A 00 | FF FF | 01 | no | withheld:F0 FF | withheld:64 00 | withheld:0A 00 | raw:FF FF | raw:01 |
| variant-beta | B509 | beta | 59 | response | F0 FF | 64 00 | 0A 00 | FF FF | 01 | yes | converted:F0 FF:-1 | converted:64 00:1 | converted:0A 00:1 | raw:FF FF | raw:01 |
| variant-empty | B509 | empty | 59 | response | F0 FF | 64 00 | 0A 00 | FF FF | 01 | no | withheld:F0 FF | withheld:64 00 | withheld:0A 00 | raw:FF FF | raw:01 |
| variant-omitted | B509 | omitted | 59 | response | F0 FF | 64 00 | 0A 00 | FF FF | 01 | no | withheld:F0 FF | withheld:64 00 | withheld:0A 00 | raw:FF FF | raw:01 |
| operation-58 | B509 | alpha | 58 | response | F0 FF | 64 00 | 0A 00 | FF FF | 01 | no | withheld:F0 FF | withheld:64 00 | withheld:0A 00 | raw:FF FF | raw:01 |
| operation-omitted | B509 | alpha | omitted | response | F0 FF | 64 00 | 0A 00 | FF FF | 01 | no | withheld:F0 FF | withheld:64 00 | withheld:0A 00 | raw:FF FF | raw:01 |
| direction-request | B509 | alpha | 59 | request | F0 FF | 64 00 | 0A 00 | FF FF | 01 | yes | converted:F0 FF:-1 | converted:64 00:1 | converted:0A 00:1 | raw:FF FF | raw:01 |
| direction-other | B509 | alpha | 59 | other | F0 FF | 64 00 | 0A 00 | FF FF | 01 | no | withheld:F0 FF | withheld:64 00 | withheld:0A 00 | raw:FF FF | raw:01 |
| direction-empty | B509 | alpha | 59 | empty | F0 FF | 64 00 | 0A 00 | FF FF | 01 | no | withheld:F0 FF | withheld:64 00 | withheld:0A 00 | raw:FF FF | raw:01 |
| direction-omitted | B509 | alpha | 59 | omitted | F0 FF | 64 00 | 0A 00 | FF FF | 01 | no | withheld:F0 FF | withheld:64 00 | withheld:0A 00 | raw:FF FF | raw:01 |
| rejected-family-truncated-temperature | B524 | alpha | 59 | response | F0 | 64 00 | 0A 00 | FF FF | 01 | no | malformed:F0 | withheld:64 00 | withheld:0A 00 | raw:FF FF | raw:01 |

The synthetic fixture is [an10_b509_quantity_views.json](fixtures/an10_b509_quantity_views.json).

## Unknown

These items stay Unknown. The software arithmetic above does not close them.

- absolute positions
- omitted family variants
- raw sentinels
- peer bounds
- minimum and maximum conversion
- physical support
- actuation

## Companion

AN10 is the ordinary companion of AN09. Both describe the ab09an09 helper boundary. This page does not depend on an AN09 code change and does not wait for one.
