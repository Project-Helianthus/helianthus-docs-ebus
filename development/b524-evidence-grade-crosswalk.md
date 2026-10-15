# B524 evidence grades for Explorer display consumers

This AGPL consumer crosswalk reads the existing BASV0 contract; it adds no
stored grade, schema/export field, profile, native admission or Explorer UI.
It is a partial follow-up to
[Explorer #302](https://github.com/Project-Helianthus/helianthus-vrc-explorer/issues/302),
which remains open. It is neither a contribution-intake checklist (#601) nor a
name-evidence index (#596).

Evidence grade (`Proven`, `Hypothesis`, `Unknown`), codec qualification, profile
matching and acquisition state are independent. “Unknown/not specified” below
means the cited public contract assigns no grade to that field; it does not
regrade retained metadata. Sources are the [native profile][native], its
[description schema][schema] and [observation schema][observations], with
application policy in [profile reuse][reuse] and [baseline rechecking][baseline].

| Existing field/class | Grade supported by retained evidence; omission/nonclaim | Codec / validation state | Profile matching | Acquisition state |
| --- | --- | --- | --- | --- |
| Local identity: EID, software/hardware raw, API version raw and revision raw | **Unknown/not specified** for identity fields as a class. They identify observation context, not a product article or every controller with that EID; omitted identity detail is **Unknown**. [Native introduction and provenance][native] | Identity is not codec proof or validation authority. [Reuse][reuse] | All five identity components must match; version and revision remain separate. | A match does not establish a current read or recheck. [Baseline][baseline] |
| `remote_identity`, including `observed_remote_header` | **Unknown/not specified** for retained identity metadata. Required group, address and firmware fields and per-slot consistency do not recover omitted native headers or prove a device function. [Retained uncertainty][uncertainty] | Identity-unqualified records never carry a qualified codec; remote descriptions remain raw evidence only when identity is unqualified. [Reuse][reuse] | The selected slot needs its own class and firmware; missing/changed identity cannot qualify a prior baseline. [Baseline][baseline] | An observed-header label is retained metadata, not a new current-target acquisition. |
| `raw_description_hex`: GG/RR echo and MIN/MAX/STEP spans | **Proven** only within retained bytes: echo and equal spans establish structure, not codec, instance, presence or write permission. [Native format][format] | `selector_qualified` plus `qualified` is reuse vocabulary, separate from the codec basis grade. Width alone stays unqualified. | Matching identity remains necessary; raw agreement cannot replace it. | A retained description can coexist with `acquisition_state: unqualified`; it grants no codec/range. [State fields][states] |
| Selector `(OP, GG, II, RR)` | GG/RR are supported within retained description bytes; request opcode/instance association is **Hypothesis**, derived and non-reproducible from the retained artifact. No request bytes are retained and II is not echoed. [Native format][format] | Cross-instance invariance is a qualification check, not proof of missing requests or codec. | Keep OP02 and OP06 separate; never reuse across operations/instances. [Baseline][baseline] | Semantic links do not prove request/reply correlation independently. |
| Absent native headers, request bytes, response payloads and current values | Omitted current values/context are **Unknown**; retained metadata and derived-artifact authentication do not reconstruct them. [Provenance][provenance] | No codec or range authority follows from omitted material. | Profile match cannot supply missing evidence. | `response_state`, `observed_payload_width` and `acquisition_state` are **Hypothesis**, derived; falsification requires new acquisition. [State fields][states] |
| `decoded`, `codec_basis`, decoded limits and read widths | `public_local_constraint_codec` and `public_exact_selector_schema` are **Hypothesis**; `payload_length_inferred` is **Unknown**. Decoded limits do not become Proven through matching. [Codec basis][basis] | Qualified local ranges still rely on the codec hypothesis. Ventilation OP02/GG09/II00..II0A/RR0001 has Proven two-byte description spans, Hypothesis two-byte read width and UIN basis; one-byte UCH is rejected. [Retained uncertainty][uncertainty] | No cross-profile substitution of limits. [Reuse][reuse] | Observed read width is derived, not retained payload proof; absent limits stay null. |
| `presence_state`, including unknown/zero-looking slots | Recorded installation presence is **Hypothesis**, not independently reproducible. Ventilation presence remains **Unknown**; zero-valued empty-looking system metadata establishes neither numeric parameter nor text codec. [State fields][states], [uncertainty][uncertainty] | Recompute validation scope from current presence; unknown/inactive qualified records are display-only. [Reuse scope][scope] | Source-installation presence is not reusable authority for another installation. | Description availability or zero alone does not establish positive presence; use the specific current predicate. [Discovery][discovery] |
| Calendar/clock `DATE_DMY_U8X3`, `TIME_HMS_U8X3` candidates | Layouts and decoded limits are **Hypothesis**; STEP is **Unknown**. They are not packed-BCD codecs. [Codec basis][basis] | Qualified means parsing under a candidate layout; never range-and-step validation from this fixture. [Reuse scope][scope] | A matching profile does not promote the candidates' grade. | Retained spans do not prove a current clock value or recover omitted payloads. |
| `access_flags`, `response_state`: payload versus status | **Unknown/not specified** as a grade for raw access flags; their writable-capability interpretation is family-specific inference. Retained session response state is **Hypothesis**. Status-only `00`, echo payload and transport error remain distinct. [Provenance][provenance], [FLAGS][flags] | FLAGS does not prove write acceptance. Short/status-only replies are not register values; a value-shaped reply still needs a qualified codec. [Response states][responses] | Family-specific FLAGS inference is not universal B524 behavior. | Preserve empty, value and negative/timeout outcomes; failure does not prove global absence. [Response states][responses] |

`validation_scope` is an application overlay, not a native evidence grade.
`format_range_and_step` never admits an edit by itself. No row grants write
authority. Keep partial valid rows and incomplete coverage explicit; on an
unavailable recheck retain the baseline as prior evidence, and on a differing
recheck retain both. A profile mismatch makes that baseline inapplicable as
verification. [Reuse scope][scope], [baseline rechecking][baseline]

This document changes neither MCP compatibility nor GraphQL behavior. It uses
the existing [shared-evidence contract reference][shared] through the published
reuse page; it does not revise that contract or claim implementation parity.

[native]: ../protocols/vaillant/ebus-vaillant-b524-basv0-profile-v1.md
[provenance]: ../protocols/vaillant/ebus-vaillant-b524-basv0-profile-v1.md#provenance-and-evidence-status
[format]: ../protocols/vaillant/ebus-vaillant-b524-basv0-profile-v1.md#native-description-format
[basis]: ../protocols/vaillant/ebus-vaillant-b524-basv0-profile-v1.md#basis-of-the-codec-labels
[states]: ../protocols/vaillant/ebus-vaillant-b524-basv0-profile-v1.md#basis-of-the-other-state-fields
[uncertainty]: ../protocols/vaillant/ebus-vaillant-b524-basv0-profile-v1.md#explicitly-retained-uncertainty
[schema]: ../protocols/vaillant/fixtures/b524-basv0-description-profile-schema-v1.json
[observations]: ../protocols/vaillant/fixtures/b524-basv0-register-observations-schema-v1.json
[reuse]: ebus-vaillant-b524-basv0-profile-reuse.md
[scope]: ebus-vaillant-b524-basv0-profile-reuse.md#validation_scope-and-presence
[baseline]: ebus-vaillant-b524-explorer-discovery.md#bundled-metadata-and-rechecking
[discovery]: ebus-vaillant-b524-explorer-discovery.md#recommended-op00-count-guidance
[flags]: ../protocols/vaillant/ebus-vaillant-B524.md#22-common-read-response-header-0x02--0x06
[responses]: ../protocols/vaillant/ebus-vaillant-B524.md#23-register-response-states
[shared]: https://github.com/Project-Helianthus/helianthus-vrc-explorer/blob/main/docs/shared-evidence-contract.md
