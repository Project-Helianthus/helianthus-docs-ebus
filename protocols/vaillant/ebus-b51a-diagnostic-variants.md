# B51A diagnostic variants and replication flags

## Evidence and scope

The [existing candidate layouts](ebus-vaillant-B51A.md#candidate-mirror-and-diagnosis-layouts)
provide context for the Vaillant mirror and diagnosis family, PB/SB `B5 1A`.
They are an earlier documentation summary, not an independently traceable source
for the detailed mappings previously listed in this supplement.

No primary capture, vendor specification, TypeSpec declaration or other traceable
artifact is supplied for those detailed mappings. Their native interpretation is
**Unknown**. Exact field coordinates, encodings, domains, defaults, flag meanings,
conditional layouts and replication behavior are withheld until a source can be
cited and independently evaluated. A **Hypothesis** label alone does not establish
provenance. Physical qualification and invocation are **Unknown**.

The [fixture](fixtures/aj08_b51a_diagnostic_variants.json) retains an empty case
collection: constructed examples cannot supply the missing provenance. No native
mapping is admitted by this supplement or its fixture. The earlier summary is
not upgraded by this supplement.

The [native framing contract](../ebus-services/ebus-overview.md) distinguishes
logical data from wire escaping, framing and CRC8; it does not establish the
missing diagnostic or replication mappings.

## Interpretation boundaries

The compatibility names below describe role terminology only; they do not
establish native fields.

<!-- legacy-role-mapping:begin -->
Role terminology follows the native framing contract: initiator corresponds to
legacy master; target corresponds to legacy slave. Thus target-written and
target-version preserve the slave-written/slave-version roles, and
initiator-to-write and initiator-version preserve master-to-write/master-version.
<!-- legacy-role-mapping:end -->
Configured-register forms and previously allocated storage/save forms remain
outside this slice; sharing an operation byte does not merge their variants.
