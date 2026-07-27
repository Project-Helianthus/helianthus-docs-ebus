# M6.25 Public Acquisition Methodology Cross-Seed

Status: candidate methodology only. This page records neither an implementation
nor bounded live validation.

## Ownership And Inputs

This page owns only language-neutral acquisition, reference-binding, and public
evidence methodology. Protocol, API, and architecture material remains owned by
[helianthus-docs-eebus](https://github.com/Project-Helianthus/helianthus-docs-eebus)
and is not restated here.

The cross-seed is bound to these immutable public inputs:

- [locked M6.25 plan](https://github.com/Project-Helianthus/helianthus-execution-plans/blob/fb384ab57d79f0020c54d2c66416e8a7666f0ceb/multi-runtime-semantic-platform.locked/118-w30-26-m625-raw-spine-feature-acquisition.md);
- [canonical provenance policy](https://github.com/Project-Helianthus/helianthus-docs-eebus/blob/cedf238e34f879815ba773e9cd76b2b31c2822a3/development/msp-0625-provenance-policy.md); and
- [candidate command-path ownership record](https://github.com/Project-Helianthus/helianthus-docs-eebus/blob/cedf238e34f879815ba773e9cd76b2b31c2822a3/architecture/_candidate/msp-0625-raw-feature-command-path.md).

Those links establish this page's source boundary; they do not import their
protocol-native content or create a second canonical owner.

## Two Views, One Non-Escalation Rule

An owner-authorized local raw operator view may be necessary to perform or
audit an authorized acquisition. A public redacted export is a different view:
it communicates only publishable evidence. Local visibility is not a
publication license.

A reference is bound to the boundary that created it. Its effective tier,
authorization, runtime, tool, scope, and boundary class are part of the
binding. A reference presented through a mismatched tier, authorization,
runtime, tool, scope, or boundary fails closed before dereference. A public
reference cannot be upgraded to the local raw view, and a local raw reference
cannot be dereferenced through a public redacted export.

## Public Evidence Commitments

Public evidence may state redacted schema and error classifications, aggregate
results, bounded counts, timestamps, deterministic commitments, and pass/fail
outcomes for anti-leak or recovery checks. It must exclude raw values, stable
identities, network coordinates, payload or transport transcripts, household
state, credentials, and secret material.

Every durable public claim needs a stable public source, a redacted publishable
evidence record, or an explicit hypothesis with a falsifier. A test can prove
ordering and negative-path behavior; it cannot establish live support. A
bounded live run, if later authorized and redaction-reviewed, can establish
only its recorded observation and not a general rule.

## Pending State And Falsifier

Implementation and bounded live validation remain pending their separate gates.
This candidate creates no stable API schema, tool name, protocol-native detail,
or consumer surface.

This cross-seed is falsified if it exposes protocol-native material or
restricted material, permits a mismatched bound reference to dereference, or
reports implementation or live support without the corresponding completed
gate and publishable evidence.
