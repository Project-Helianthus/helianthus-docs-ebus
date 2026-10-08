# B524 bounded survey methodology

This method records a bounded, read-only B524 survey. It makes coverage and limits reproducible without turning a scan result into a device inventory, writable contract, or terminal register map. Selector identity is always `(OP, GG, II, RR)`; OP02 and OP06 are separate namespaces.

## Evidence states

Record each request as `value_reply`, `empty_reply`, `transport_error`, `decode_error`, or `unknown`. An empty reply is a valid observed outcome, not evidence that a group, instance, register, or physical device does not exist. An error remains unknown. A responsive RR is an observed survey ceiling, never a terminal `RR_max`.

## Bounded read recipe

1. Declare exact OP/GG candidates, read instances, Describe instance, and inclusive RR ranges before transport I/O.
2. Issue only read operations: OP02 for local values and OP06 for remote values. Their public payload layout is `OP 00 GG II RRlo RRhi`; descriptions use `OP01/OP07 GG FF RRlo RRhi`. A public transport client may implement these normal B524 reads; current VRC Explorer CLI does not provide this whole survey recipe as a single command.
3. Extend a positive group's RR window only to the declared ceiling. Unknown groups retain their smaller declared window. These are coverage choices, not protocol bounds.
4. Use OP01 for eligible writable OP02 values and OP07 for eligible writable OP06 values. Correlate replies by GG/RR, never II: response II is not echoed. Decode a value only with a qualified current-read or static matching codec, never from reply length. A description is metadata acquisition only: it does not write, prove current writability, prove a concrete installed device, or establish the highest valid RR.
5. Insert positive control requests between batches. Preserve retry accounting and ensure transport escaping for reserved CRC bytes `A9` and `AA` before classifying an outcome as empty. Persist planned/completed jobs, actual attempts, response categories, and terminal transport failures independently. Retries increase attempts, not planned-job coverage.

Record FLAGS classes as `0=read_only_hidden`, `1=read_only_visible`, `2=writable_hidden`, and `3=writable_visible` when the response permits that interpretation. A writable FLAGS class selects a description candidate; it never authorizes a write.

## BASV2 sample profile

The published BASV2 profile is a sanitized observation for VRC720f/2, software `0507`, hardware `1704`. It schedules OP02 GG `00..2F` and OP06 GG `01..2F`; unknown groups use `RR=0000..0005`, and positive groups use `RR=0000..0050`. Reads use a concrete representative `II`; descriptions use `II=FF`.

The fixture separates `effective_scan_windows` (the integrated scheduling limits)
from `group_windows` (the survey coverage). A null limit stays unknown. A correlated
Describe high-water mark may contain an unqualified body and is not automatically
a decoded parameter limit. Read-only tails can exceed decoded Describe coverage.

Its completed execution comprised 3,274 planned jobs (1,054 discovery and 2,220 extension), with zero final transport failures. It sampled higher OP02 GG `0B..2F` and OP06 GG `10..2F`; it found no new positive GG there. That negative observation is not nonexistence. The 69 high groups produced 1,020 valid empty replies.

The profile and reusable [template](fixtures/b524-bounded-survey-profile-template-v1.json) are versioned data. Add BASV0, BASV3, or CTLv3 only from their own sanitized observations; do not copy BASV2 results into another model family.

## Publishable artifacts

Publish the schema, a sanitized profile, and payload-only samples sufficient to check operation/selector handling. Exclude serials, endpoints, addresses, network coordinates, and raw captures. A profile states its coverage, model scope, response totals, and nonclaims.

The [BASV2 profile](fixtures/b524-bounded-survey-basv2-v1.json) includes representative OP02/OP06 read and description entries. Its generic `II=FF` description is explicitly not concrete-instance evidence.

## Adding a profile

Copy the template, assign a new profile filename, and replace every placeholder with sanitized observations from one model and software-version scope. Include the acquisition and catalog revisions, actual read-instance scope, separately declared discovery intervals, each operation/group scheduling window, response tallies, and nonclaims. Do not combine results across model families.

Validate the public artifact before proposing it:

```sh
jv protocols/vaillant/fixtures/b524-bounded-survey-profile-schema-v1.json \
  protocols/vaillant/fixtures/b524-bounded-survey-<profile>-v1.json
pytest -q tests/test_b524_bounded_survey_profile.py
```

The tests automatically check phase totals for every contributed
`b524-bounded-survey-<profile>-v1.json` fixture. Discovery and extension retain
separate planned, completed and attempt counts; reused exchanges are recorded
separately and are not added to this execution's completed-job total.
