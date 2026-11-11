# Standard counter body metadata API contract

This library contract adds no native wire claim. Read the public
[native service and counter-family contract](../../protocols/ebus-services/ebus-service-03h.md#vaillant-variants)
first. Its generic standard response tables and candidate alternatives remain
separate; this page does not correct or replace them. The
[services catalog](01-services-catalog.md) supplies command identities.

**Proven (library contract):** command identity, body metadata and runnable
methods are independent properties. Existing standard commands and identification
scanning remain unchanged. Selecting a body never makes a stub callable.

**Hypothesis:** the following synthetic Vaillant counter-family declarations
preserve raw alternatives. No installed support follows from them. Each row is
individually graded. Order is logical, zero-based within this metadata body;
it is not an absolute native position. `null` is absent knowledge, never zero.
The candidate request-side label is a library variant, not a physical direction.

## Field declarations

| PB | SB | Order | Field | Width bits | Type | Minimum | Maximum | Default | Conversion | Unit | Encoding | Native position | Grade |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 03 | 04 | 0 | decimal_1s | 8 | unsigned8 | 0 | 99 | 0 | identity | raw | null | null | Hypothesis |
| 03 | 04 | 1 | decimal_100s | 8 | unsigned8 | 0 | 99 | 0 | identity | raw | null | null | Hypothesis |
| 03 | 04 | 2 | decimal_10000s | 8 | unsigned8 | 0 | 99 | 0 | identity | raw | null | null | Hypothesis |
| 03 | 05 | 0 | minutes | 8 | unsigned8 | 0 | 59 | null | identity | raw | null | null | Hypothesis |
| 03 | 05 | 1 | hours_100s | 8 | unsigned8 | 0 | 59 | null | identity | raw | null | null | Hypothesis |
| 03 | 05 | 2 | hours_10000s | 8 | unsigned8 | 0 | 59 | null | identity | raw | null | null | Hypothesis |
| 03 | 06 | 0 | minutes | 8 | unsigned8 | 0 | 59 | null | identity | raw | null | null | Hypothesis |
| 03 | 06 | 1 | hours_1s | 8 | unsigned8 | 0 | 99 | null | identity | raw | null | null | Hypothesis |
| 03 | 06 | 2 | hours_100s | 8 | unsigned8 | 0 | 99 | null | identity | raw | null | null | Hypothesis |
| 03 | 06 | 3 | hours_10000s | 8 | unsigned8 | 0 | 99 | null | identity | raw | null | null | Hypothesis |

Encoding `null` means unspecified. An absent encoding property also carries no
encoding declaration; neither is equivalent to explicit `raw` encoding. These
states must survive serialization. The decimal chunks are not packed BCD:
`0x63` is decimal 99. Units remain raw. Only 03/04 declares default zero; other defaults remain Unknown here.
Defaults describe metadata, not bytes to
insert into incomplete bodies. In particular 03/05 has no units-of-hours field.

## Variant declarations

Standard-response rows deliberately leave body metadata Unknown here: the generic
native response contract remains at the link above, independently of this
candidate API slice. They do not reuse the candidate request fields. Missing
03/07, 03/08 and 03/10 bodies have no fields or constructors in either variant;
Unknown does not mean an empty executable body or unsupported command.

| PB | SB | Variant | Body state | Field count | Constructor | Callable | Physical side | Qualification | Grade |
|---|---|---|---|---|---|---|---|---|---|
| 03 | 04 | candidate-request | declared | 3 | false | false | Unknown | Unknown | Hypothesis |
| 03 | 04 | standard-response | Unknown | null | false | false | Unknown | Unknown | Unknown |
| 03 | 05 | candidate-request | declared | 3 | false | false | Unknown | Unknown | Hypothesis |
| 03 | 05 | standard-response | Unknown | null | false | false | Unknown | Unknown | Unknown |
| 03 | 06 | candidate-request | declared | 4 | false | false | Unknown | Unknown | Hypothesis |
| 03 | 06 | standard-response | Unknown | null | false | false | Unknown | Unknown | Unknown |
| 03 | 07 | candidate-request | Unknown | null | false | false | Unknown | Unknown | Unknown |
| 03 | 07 | standard-response | Unknown | null | false | false | Unknown | Unknown | Unknown |
| 03 | 08 | candidate-request | Unknown | null | false | false | Unknown | Unknown | Unknown |
| 03 | 08 | standard-response | Unknown | null | false | false | Unknown | Unknown | Unknown |
| 03 | 10 | candidate-request | Unknown | null | false | false | Unknown | Unknown | Unknown |
| 03 | 10 | standard-response | Unknown | null | false | false | Unknown | Unknown | Unknown |

## Synthetic acceptance examples

These predicates admit complete local representations only. Arithmetic is
**Proven (arithmetic only)**; its applicability to native bodies is **Hypothesis**.
03/04 uses `a + 100*b + 10000*c`, preserving all three chunks. No projection
invents the missing hours byte of 03/05. All unprovided properties are Unknown.

| Case | PB | SB | Raw decimal bytes | Accepted | Illustrative count |
|---|---|---|---|---|---|
| decimal | 03 | 04 | [12, 34, 56] | true | 563412 |
| raw99 | 03 | 04 | [99, 0, 0] | true | 99 |
| middle60 | 03 | 05 | [1, 60, 2] | false | null |
| three | 03 | 05 | [1, 2, 3] | true | null |
| four | 03 | 06 | [59, 99, 99, 99] | true | null |
| incomplete | 03 | 06 | [59, 99, 99] | false | null |
| unknown | 03 | 07 | [] | false | null |

## Positive alternatives and admission

| Alternative | PeBUS relevant | Physical reply |
|---|---|---|
| body-positive | true | Unknown |
| prefix-only-positive | true | Unknown |

Both positive constants can be relevant to PeBUS. A prefix-only representation
never implies an empty physical reply. Absolute native positions and the physical
side carrying candidate bodies remain **Unknown**, independently of logical order.
The fixture's absent-position control and explicit position-zero control must
remain different states; zero is a synthetic control, not an assigned offset.

The [synthetic tuples](fixtures/ai02_03_counter_bodies.json) are metadata examples,
not captures. Admission remains fail-closed on unknown identity, missing body,
invalid domain, extra bytes or incomplete fields. Preserve original raw bytes and
independently valid fields, including partial last-known-good state, without
promoting an incomplete observation to a complete body. Invalid new data cannot
erase a separately retained valid observation or manufacture a default byte.

Keep eBUS MCP compatibility and GraphQL parity: consumers must preserve the same
identity, raw data, variant, missing states and grades; this page adds no endpoint
or executable method. Qualification, freshness, persistence, physical support and
execution permission remain Unknown and independent of Proven/Hypothesis/Unknown
claim grades. Synthetic success grants none of them. No active executor is added.
