# Finite Prometheus documentation validation scope

## Decision: intended policy

Machine validation has a finite, explicitly structured surface. It checks the
contract data below, not the wording used to explain it. M35 / [companion
#649](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/649)
retains metric-contract, coverage-page, validator and CI ownership. This
scope decision neither copies the metric table nor introduces a second checker.

| Claim | Intended machine check | Human review |
| --- | --- | --- |
| Metric names | Explicitly structured names match the declared contract. | Explanations of purpose and naming rationale. |
| Label domains | Explicitly structured label keys and allowed domains match the declared contract. | Rationale and illustrative label examples. |
| Required table rows | Required structured rows are present with their declared associations. | Surrounding prose, ordering where immaterial, and equivalent descriptions. |
| Exact thermal dispositions | Derive expected fact IDs from `mappings` entries whose `disposition` is `exact`, using their `semreg_fact` values; compare the structured exact claims to that source-derived set. | Explain what an exact candidate mapping means and its evidence limits. |
| Withheld thermal dispositions | Retain each withheld row's `legacy_system_field` and `loss`; compare those structured associations to the source. Never discard a row because `semreg_fact` is null. | Explain the loss and why it prevents substitution. |
| Explanations, rationale and examples | No sentence assertions or verbatim prose matching. | Meaning, clarity, correctness and harmless equivalent rewordings. |

The [thermal mapping fixture](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/fixtures/vaillant-semreg-thermal-map-v1.json)
is the source for thermal dispositions. Exact fact IDs must be derived, not
maintained as a second independent list. Withheld rows cannot be keyed solely
by `semreg_fact`: the rolling-average row has a null fact but retains
`state.outdoor_temperature_avg24h` and
`rolling_average_window_unrepresentable`. Null does not erase that loss.

## Discriminating examples

- Rewording “the rolling-average candidate remains withheld” as “the candidate
  for the rolling average is withheld” preserves meaning. It needs human
  review, not a machine failure.
- Changing a structured exact fact ID from
  `thermal.measurement.air_temperature` to `thermal.measurement.power` while
  the source mapping is unchanged must fail the intended source comparison.
- Removing the withheld rolling-average row because its `semreg_fact` is null,
  or dropping or changing its `loss`, must fail the intended source comparison.

These are manual review examples, not executable tests or evidence of current
validator behavior. New mechanically checked invariants require an explicit
amendment to this scope decision identifying the structured claim and its
source; they must not accumulate as assertions about sentences.

## Implementation and evidence boundary

The supplied issue baseline describes #649 as open and pending, with its
validator and coverage page absent from that main view. The provisioned source
view instead contains the [coverage page](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/deployment/prometheus-semantic-coverage.md)
and [validator](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/scripts/validate_prometheus_semantic_coverage.py),
with registration in the [local gate](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/scripts/ci_local.sh).
That validator includes prose assertions; its presence does not establish
conformance to the intended policy above. The companion PR remains pending
according to the supplied baseline; this decision does not certify its status
or implementation acceptance.

For protocol facts, the public [native B524 contract](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/protocols/vaillant/ebus-vaillant-B524.md)
must precede the [semantic mapping](https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/b524-semantic-mapping.md)
and fixture interpretation. An `exact` disposition is not `Proven` native
behavior, qualification, acquisition, admission or exporter acceptance.
`Proven`, `Hypothesis` and `Unknown` remain evidence conclusions on a separate
axis. This documentation policy changes no native trust or fail-closed
admission, partial last-known-good state, eBUS MCP compatibility or GraphQL
parity. It claims no stability before Helianthus 1.0.
