# Opaque Runtime Acquisition V1

## Status And Authority

`OPAQUE_RUNTIME_ACQUISITION_V1` is the normative public companion for
`FMV3-M1-05`. It is an additive successor to the M1-04 contract and is a
prerequisite for `FMV3-M1-06` and `FMV3-M2-01`. It defines public,
implementation-neutral behavior; it does not claim that either downstream
implementation exists.

The keywords **MUST**, **MUST NOT**, **REQUIRED**, **SHOULD**, **SHOULD NOT**,
and **MAY** are normative. The closed machine-readable companion is
[`manifests/opaque-runtime-acquisition-v1.json`](./manifests/opaque-runtime-acquisition-v1.json).
`scripts/validate_opaque_runtime_acquisition.py` validates this V1 document,
its closed inventory, and its licensing and boundary declarations.

This contract grants **no** gateway authorization, vendor authorization,
semantic authorization, device authorization, or write authorization. It does
not permit a Modbus write, a gateway change, a vendor/profile admission, a
canonical semantic claim, or access to live hardware or a live system.

This page is Helianthus policy under the repository AGPL-3.0 documentation
lane. It contains no copied restricted source material and introduces no
vendor-specific protocol fact. It refines the read-only, provenance, and
public/private boundaries in
[`modbus-foundation-profile-contract-v1.md`](./modbus-foundation-profile-contract-v1.md);
the stricter fail-closed rule controls until a versioned successor says
otherwise.

## Scope And Terms

An **acquisition** is one source-observation opportunity. A **dependent** is
one logical consumer attached to an acquisition, including a dependent of a
coalesced physical read. An **attempt** is a bounded ledger entry that groups
the dependencies intended for one publication. A **claim** is the one-shot
delivery decision made for exactly one dependent capability. An `AttemptKey`
is a non-empty UTF-8 string compared by exact encoded bytes, without Unicode,
case, or documentary normalization. It is an identifier and never an
authorization token.

`source_kind` is a closed enum with exactly two values:

| Value | Meaning | Trust consequence |
| --- | --- | --- |
| `runtime` | A live runtime source created this acquisition. | Delivery requires a successful capability claim. |
| `offline_fixture` | Offline replay or fixture material created this acquisition. | Untrusted; no capability exists or is claimed. |

No alias, omitted value, future enum value, or inferred source kind is valid
under V1. A source evidence identifier identifies documentary/runtime evidence;
it is not a capability and cannot confer delivery trust.

## Normative Public API Behavior

### Capability Issuance

Only the runtime source MAY issue an `opaque_runtime_acquisition_capability`.
It MUST issue one only when all of the following are true:

1. `source_kind` is exactly `runtime`;
2. the runtime source has produced a deliverable successful dependent; and
3. the capability is assigned to one specific dependent and immutably bound
   by the source to that dependent's exact validated `AttemptKey` and one
   source-issued `AttemptInstance`.

The source MUST validate the key's encoding and bound before capability
allocation or binding. Capability issuance does not admit the M2 attempt; the
ledger independently validates the same exact bindings during attempt admission.

An `AttemptInstance` is an opaque, unforgeable, non-serializable source-owned
identity for one attempt incarnation. It is not an `AttemptKey`, endpoint
generation, counter, UUID, digest, byte sequence, or reconstructible token. A
reused `AttemptKey` always receives a fresh independent instance. Every member
capability MUST register atomically with its exact instance before that
capability becomes caller-visible.

Instance membership begins `open`. Ledger admission atomically performs
`open -> closing`, blocks every later registration, waits for every registration
that linearized before closure, validates the exact ordered member set, and then
performs `closing -> closed`. A registration that loses the close race fails
without making a capability visible or retaining open source state. The closed
membership set is immutable and is the only set that M2 may admit. Caller
convention, a scan by `AttemptKey`, or eventually consistent enumeration cannot
substitute for this source-owned close-and-drain barrier.

The capability is source-issued, opaque, and non-serializable. It MUST NOT be
represented as a string, integer, byte sequence, map, JSON field, wire value,
hash-derived surrogate, or reconstructible token. A caller cannot mint,
deserialize, clone, reset, or replay one. Its only caller-visible operation is
a one-shot atomic claim for the dependent to which it was issued. The separate
source-owned attempt cancellation operation is defined below; it is not a
capability operation and grants no cancellation authority to a caller.

Deliverability is owned and decided by the runtime source after correlation.
It is exactly post-correlation successful dependent production under the
predecessor contract's
[successful dependent production](./modbus-foundation-profile-contract-v1.md#physical-and-logical-identity)
boundary: a request-bound response has outcome `successful_data`, the
dependent remains attached, its exact logical slice validates, and production
is coherent. The resulting capability remains non-serializable.

Deliverability MUST NOT be caller-controlled, accepted as a caller flag, or
reconstructed from endpoint identity, response identity, values, provenance,
serialized data, or a prior capability. A detached or cancelled dependent, a
protocol exception, malformed response, transport or dependent failure,
late/abandoned response, uncorrelated frame, torn/incoherent production, or any
other non-success outcome is not deliverable and MUST receive no capability.

A non-deliverable runtime acquisition MUST have no capability. An
`offline_fixture` acquisition MUST have no capability regardless of whether a
fixture resembles a runtime endpoint, identifier, word sequence, or prior
runtime result. Lack of a capability is a normal fail-closed state, not a
recoverable request for the consumer to synthesize one.

### Capability Lifecycle, Claim, And Copy Semantics

Claiming a capability MUST be one-shot compare-and-swap (CAS) against private,
source-issued `source_owned_shared_capability_state`. That state belongs to the
M1 runtime source; it is not an M2 ledger pointer and is not owned by the
consumer. It starts in `open` and follows exactly one legal transition:

| From | To | Source-owned trigger |
| --- | --- | --- |
| `open` | `claimed` | the single successful atomic claim |
| `open` | `cancelled` | source cancellation before a successful claim |
| `open` | `failed` | source-declared terminal production or delivery failure |
| `open` | `expired` | source-owned finite claim deadline expires |

`claimed`, `cancelled`, `failed`, and `expired` are immutable terminal states.
There is no transition between terminal states and no return to `open`.
Every later claim is rejected without state change, including a retry, a
copied value, a reconstructed view, or a stale handle.

Value copies and public views of the same issued capability MUST reference the
same claim state. When copied views race to claim it, exactly one claim wins;
all other concurrent and later claims are rejected. An implementation MUST NOT
create independent claim cells merely because it copied an acquisition value.
After a capability is admitted to an M2 attempt, every conforming claim through
any copied view MUST pass through that attempt's ledger claim-admission
linearization. A direct claim that bypasses the ledger is invalid. An
implementation MUST enforce this by ownership transfer, an unforgeable
ledger-admission permit, or an equivalent private mechanism; caller convention
alone is insufficient.

#### Source-Owned Attempt Cancellation

The runtime source MUST expose the M2 ledger cancellation path to exactly one
attempt-bound operation, `CancelOpen(AttemptInstance)`. The source owns and executes
this operation and all capability CAS state. M2 owns the attempt and decides
when its cancellation protocol invokes the operation. `CancelOpen` is not a
caller-visible capability method, cannot be synthesized from an `AttemptKey`,
and cannot mutate any ledger entry or attempt state.

`CancelOpen` accepts only the exact opaque closed instance handle transferred at
ledger admission and examines exactly that instance's frozen membership. For
each member capability it
atomically performs `open -> cancelled` when the state is still `open`; it
leaves `claimed`, `cancelled`, `failed`, and `expired` unchanged. It returns
only after all pre-close registrations, member capability operations, and
synchronous terminal reclamation have completed and no member remains open.
The operation cannot mint, replace, reconstruct, reopen, or discover a
capability by documentary key. A stale cancellation for instance A MUST NOT
affect instance B even when both have byte-identical `AttemptKey`, endpoint,
generation, and values.

Endpoint recreation that produces a new eligible acquisition MUST create fresh,
independent capability state for each eligible dependent, even when endpoint
coordinates, endpoint generation, endpoint string, unit IDs, function, offsets,
word values, and every other visible identity or datum are identical. Visible
endpoint identity and transport generation are provenance, not capability
security identity.

The new acquisition MUST NOT alias, remint, reset, or merge an earlier
capability. Endpoint recreation and visible-data equality do not change an
existing capability: that capability remains governed only by its own
acquisition and, where applicable, its own attempt lifecycle. In particular,
recreating a matching endpoint cannot reopen or otherwise affect an already
claimed capability. Conversely, recreating a view of the same acquisition MUST
retain that acquisition's private source-owned shared claim state.

### Coalesced Dependents

Coalescing may share transport work and raw response evidence, but it MUST NOT
share a delivery capability. Each deliverable runtime dependent receives one
independent capability with independent shared claim state. For `N`
deliverable runtime dependents there are exactly `N` issued capabilities. A
claim, cancellation, failure, or terminal reclamation of one dependent MUST
NOT authorize, consume, or invalidate another dependent's capability except
through that dependent's own lifecycle.

### Bounded Lifecycle And Reclamation

The runtime source MUST enforce a configured finite hard limit on private
capability state. Invalid, zero, negative, overflowing, or internally
inconsistent source limits fail before admission. Reaching the live-capability
limit rejects new issuance explicitly; it MUST NOT evict or silently reuse
live state. M2 attempt and claim bounds are closed separately below across
every retained lifecycle state.

An issued capability begins open and reaches exactly one real terminal state:
`claimed`, `cancelled`, `failed`, or `expired`. A non-deliverable acquisition
or fixture has no capability; non-issuance is outside the capability lifecycle
and is not a terminal capability state. Terminal state cannot return to open.

The source synchronously removes terminal capability state from its bounded
live tracking set before the terminal operation returns. Reclamation is
storage release after a terminal outcome, not a capability state. The source
MAY retain only a non-reconstructing immutable terminal tombstone under a
configured finite positive `capability_tombstone_limit`. Tombstones are
ordered by a source-reserved terminal sequence; insertion that exceeds the
limit synchronously evicts the lowest terminal sequence first. Wall clock, map
iteration, caller behavior, and randomness MUST NOT affect retention or
eviction.

Before capability admission or allocation, the source MUST reserve one unique
terminal sequence from the unsigned 64-bit range `1..2^64-1`. Reservation is
checked, monotonic, non-wrapping, and never reused during the lifetime of the
source owner instance, including after reclamation. Restored retained state
MUST restore the next unused sequence. Exhaustion rejects new capability
issuance without changing existing state. Every already admitted capability
therefore owns the sequence needed to reach and record a terminal outcome even
after exhaustion.

The capability tombstone schema is closed and has exactly these fields:

| Field | Exact V1 type or value |
| --- | --- |
| `schema_version` | integer `1` |
| `terminal_sequence` | the capability's reserved unsigned 64-bit sequence |
| `terminal_outcome` | exactly `claimed`, `cancelled`, `failed`, or `expired` |

No field is optional and no extension field is allowed. In particular, a
capability tombstone MUST NOT retain a raw `AttemptKey`, `source_evidence_id`,
normalization record, evidence payload, capability representation, or free-form
diagnostic. Its retained encoding MUST fit the configured finite positive
`capability_tombstone_max_encoded_bytes`, validated at source activation against
the largest legal closed-schema encoding.

A caller-retained terminal wrapper is an immutable, non-owning view of its
already determined outcome. It cannot claim, reconstruct, or reopen the
capability and does not keep an entry in the source-owned live tracking or
tombstone sets. Source-owned tracking plus tombstones therefore remains
bounded even if callers retain arbitrarily many terminal wrapper values.

## M2 Ledger And Publication Contract

`helianthus-modbusreg` owns the attempt ledger, while the runtime remains the
sole capability issuer and owner of private capability state. Every attempt
MUST use ledger-owned shared pointer state for attempt and publication state;
copied attempt values and views observe that same attempt/publication state.
The ledger may record a capability claim outcome, but it MUST NOT own, replace,
serialize, reconstruct, or expose the capability's private source-owned CAS
state. A caller-supplied mutable DTO is forbidden as publication input.

An `AttemptKey` documents one ledger attempt, which begins `open`; the exact
opaque `AttemptInstance` is its security and cancellation identity. Before
copying, hashing, interning, or otherwise allocating for a key, the ledger MUST
validate its exact UTF-8 byte length against the finite positive
`attempt_key_max_utf8_bytes`. An empty, invalidly encoded, or over-bound key is
rejected. Insertion of a duplicate `AttemptKey` MUST be rejected before it
changes capability, claim, or publication state. Every runtime capability in
the inserted attempt MUST carry the same exact source-owned key binding; a
mismatch rejects the whole insertion without changing either owner's state.

Before terminal-sequence reservation, ledger allocation, or any capability CAS,
admission MUST validate a non-empty ordered dependency declaration copied from
the predecessor's exact ordered `dependency_set_id`. The dependency count and
complete canonical encoded byte length are finite-positive bounded and checked
before decoding or materializing the collection. Every dependent identity is
non-empty and unique. The ledger computes `dependency_set_digest` as SHA-256 of
the domain-separated canonical encoding of the count followed by each dependent
identity in declared ordinal order. Each capability, claim entry, and
zero-based `claim_ordinal` is bound to that exact digest and ordinal. A
permutation, omission, duplication, extra member, count mismatch, capability
membership mismatch, or digest mismatch rejects the whole attempt before
source or ledger state changes. Claim terminal sequences are reserved in that
same declared ordinal order.

### Claim-Entry Lifecycle

Each runtime claim entry begins `unresolved`. `claim_in_progress` is a counted
nonterminal state. The complete legal claim-entry transition set is:

| From | To | Trigger |
| --- | --- | --- |
| `unresolved` | `claim_in_progress` | the one admitted `Claim()` while the attempt is exactly `open` |
| `claim_in_progress` | `claim_succeeded` | the source claim CAS performs `open -> claimed` |
| `claim_in_progress` | `capability_cancelled` | the source reports immutable `cancelled` |
| `claim_in_progress` | `capability_failed` | the source reports immutable `failed` |
| `claim_in_progress` | `capability_expired` | the source reports immutable `expired` |
| `claim_in_progress` | `claim_rejected_terminal` | the source reports that the capability was already `claimed` |
| `unresolved` | `attempt_cancelled` | attempt cancellation after all admitted claims drain |

The terminal claim outcome enum is exactly:

- `claim_succeeded`
- `capability_cancelled`
- `capability_failed`
- `capability_expired`
- `claim_rejected_terminal`
- `attempt_cancelled`

Every terminal claim outcome is immutable. A terminal claim entry cannot
return to `unresolved`, change outcome, or be retried. Attempt cancellation
synchronously closes only entries that are still `unresolved` as
`attempt_cancelled`. It MUST NOT change `claim_in_progress` or any terminal
entry. Claim admission and finalization use the ledger-owned shared state;
capability consumption remains a source-owned CAS.

Claim admission is the atomic `unresolved -> claim_in_progress` transition
while, in the same linearization decision, the owning attempt is exactly
`open`. It is rejected without source CAS if the attempt is `sealed`,
`cancelling`, `publishing`, or terminal, or if the claim entry is not
`unresolved`. Once admitted, the source claim operation MUST run exactly once.
Its finalization MUST record the corresponding immutable source result in the
claim entry using that entry's reserved terminal sequence before it signals
completion, even when the attempt has meanwhile entered `cancelling`. The
attempt state cannot overwrite or reinterpret that result.

#### Claim-Cancellation Linearization

Attempt cancellation linearizes by atomically performing exactly one of
`open -> cancelling` or `sealed -> cancelling`. That transition immediately
prevents new claim admission, `Seal()`, and `Publish()`. Cancellation then waits
until every already admitted `claim_in_progress` operation has recorded its
immutable terminal result. It next invokes the source-owned
`CancelOpen(AttemptInstance)` operation, waits for it to return, and closes only the
remaining `unresolved` entries as `attempt_cancelled`. Finally it performs
`cancelling -> cancelled`.

Therefore an admitted claim wins the ordering race: its exact source result is
recorded before cancellation can complete. Cancellation wins only against a
still-`unresolved` entry. No execution may record both `attempt_cancelled` and a
source claim result for one entry, cancel a capability after its successful
claim, or expose `cancelled` while an admitted claim or `CancelOpen` is still
running. A concurrent later cancellation call cannot repeat the protocol or
change any outcome.

### Attempt And Publish Lifecycle

The complete legal attempt transition set is:

| From | To | Trigger |
| --- | --- | --- |
| `open` | `sealed` | `Seal()` after every data-bearing runtime claim is `claim_succeeded` |
| `open` | `cancelling` | cancellation before sealing |
| `sealed` | `publishing` | the one admitted `Publish()` invocation |
| `sealed` | `cancelling` | cancellation before `Publish()` is admitted |
| `cancelling` | `cancelled` | the claim drain, `CancelOpen`, and unresolved-entry closure complete |
| `publishing` | `published` | publication succeeds |
| `publishing` | `publish_failed` | publication fails or is cancelled after admission |

`published`, `publish_failed`, and `cancelled` are immutable terminal attempt
states. No other attempt transition is legal. Sealing creates one immutable
attempt set containing the exact ordered dependent and terminal claim
outcomes. `Publish()` MUST consume that sealed immutable ledger state and MUST
NOT accept a mutable DTO or an unsealed attempt.

`Seal()` MUST reject unless the ordered dependency set is non-empty, every
dependent is exactly `runtime` and data-bearing, every dependent has exactly
one claim entry, claim cardinality equals dependency cardinality, and every
entry is exactly `claim_succeeded`. Empty, fixture-only, mixed fixture/runtime,
zero-runtime, duplicated, omitted, or reordered dependency sets permanently
forbid production sealing and publication and may follow only a distinct
non-publishable evidence/audit path. Merely being
terminal is insufficient. Any `capability_cancelled`, `capability_failed`,
`capability_expired`, `claim_rejected_terminal`, or `attempt_cancelled` entry
permanently blocks sealing and publication for that attempt; the attempt may
then follow only the cancellation and bounded audit path. An `unresolved` or
`claim_in_progress` entry also blocks sealing. This condition does not make an
offline fixture trusted and grants no production publication or sample
identity to fixture data.

The success predicate and `open -> sealed` transition MUST linearize as one
atomic decision against cancellation and claim admission. A stale pre-check
cannot authorize sealing after either state has changed.

`Publish()` is one-shot. Exactly one call may perform
`sealed -> publishing`; concurrent or later calls are rejected without state
change. A cancellation that linearizes before admission performs
`sealed -> cancelling` and completes the cancellation protocol above. Once
publication is admitted, successful commit and cancellation arbitrate at one
atomic publication decision that performs exactly one of
`publishing -> published` or `publishing -> publish_failed`. The irreversible
external publication effect and `published` decision MUST be one transactional
commit; an implementation that cannot provide that boundary MUST fail before
external publication. Cancellation wins only before that commit and yields
`publish_failed`. Publication wins at commit; concurrent or later cancellation
returns exactly `already_published` without state or external-effect change.
No execution can expose a committed publication with `publish_failed`, expose
both outcomes, return to `sealed`, or authorize a retry. No post-seal mutation,
addition, deletion, substitution, or reordered dependent is valid.

#### Closed Publication Projection

The sealed normalization records and evidence are internal ledger state.
`Publish()` MUST emit only `published_attempt_v1`, a closed projection with
exactly `schema_version`, `attempt_terminal_sequence`,
`dependency_set_digest`, `runtime_dependency_count`, and
`claim_outcome_digest`. Additional fields are forbidden. The projection MUST
NOT contain or serialize an `AttemptKey`, `AttemptInstance`, dependent identity,
`source_evidence_id`, normalization record, unknown extension key or value,
retained diagnostic, evidence payload, capability representation, endpoint
identity, or raw protocol data. `claim_outcome_digest` is domain-separated and
commits to the ordered successful claim outcomes without exposing their source
records. Downstream domain values require their own public contract and are not
authorized by this receipt. Tests MUST inject distinct secret canaries into
every forbidden source location and prove both field-level and byte-level
absence from the published projection.

### Ledger Bounds And Deterministic Reclamation

The ledger MUST configure finite positive hard limits for:

- all retained attempts across `open`, `sealed`, `cancelling`, `publishing`,
  `published`, `publish_failed`, and `cancelled` pending reclamation;
- claim entries per attempt;
- complete ordered dependency-set encoded bytes before collection decode;
- total retained claim entries across `unresolved`, `claim_in_progress`, and
  every terminal outcome, bounded by the checked product of retained-attempt
  and per-attempt limits;
  and
- immutable attempt/claim audit tombstones.

Invalid, zero, negative, overflowing, or inconsistent bounds fail before
ledger activation. Admission counts every retained state, not only `open`.
Reaching any bound rejects admission without eviction or reuse of live state.

Before an attempt allocates or changes source, claim, attempt, or publication
state, the ledger MUST reserve one unique attempt terminal sequence and one
unique claim terminal sequence for every admitted claim entry. The batch is
reserved all-or-nothing from `1..2^64-1` using checked monotonic unsigned 64-bit
arithmetic. Sequences never wrap or reuse while retained ledger state exists.
They also never reuse after reclamation during the ledger owner instance, and
restored retained state MUST restore the next unused sequence. If the full
batch is unavailable, insertion is rejected without mutation.
Sequence exhaustion blocks new attempts but cannot prevent any existing
attempt or claim entry from reaching its terminal outcome.

On every terminal transition and before every admission result returns, the
ledger synchronously reclaims eligible terminal attempt and claim entries.
Eligibility requires no in-progress ledger operation and no reference from a
retained nonterminal attempt; a terminal claim outcome required by an open,
sealed, cancelling, or publishing attempt remains retained and counted.
Reclamation order is deterministic by the terminal sequence reserved at
admission. Reclamation emits a
non-reconstructing immutable audit tombstone into a configured finite positive
`ledger_audit_tombstone_limit`; insertion beyond the limit synchronously
evicts the lowest terminal sequence first. Wall clock, map iteration, caller
behavior, and randomness cannot alter reclamation or eviction.

The ledger audit tombstone schema has exactly two closed variants:

| Variant | Exact required fields |
| --- | --- |
| attempt | `schema_version=1`, `object_kind=attempt`, reserved unsigned 64-bit `terminal_sequence`, and `terminal_outcome` in `published`, `publish_failed`, or `cancelled` |
| claim | `schema_version=1`, `object_kind=claim`, reserved unsigned 64-bit `terminal_sequence`, the owning attempt's reserved unsigned 64-bit `attempt_terminal_sequence`, zero-based unsigned 64-bit `claim_ordinal`, and `terminal_outcome` in the closed claim terminal enum |

Neither variant permits optional or extension fields. Audit tombstones MUST
NOT retain raw `AttemptKey`, an `AttemptKey` digest, `source_evidence_id`,
normalization records, evidence payloads, capability representations, or
free-form diagnostics. Each retained encoding MUST fit the configured finite
positive `ledger_audit_tombstone_max_encoded_bytes`, validated at ledger
activation against the largest legal encoding of both variants.

A caller-retained terminal attempt or claim wrapper is an immutable, non-owning
outcome view. It cannot mutate or keep alive ledger-owned attempt, claim, or
audit state and does not count as retained ledger state. The
`shared_ledger_owned_pointer` exists only while the bounded ledger owns the
attempt/publication state; it never becomes capability state.

For a runtime acquisition, delivery trust requires the successful one-shot CAS
for that dependent. A failed or absent runtime claim cannot be treated as a
successful delivery. This rule does not authorize any consumer semantics or
publication beyond the downstream contracts.

## Fixture Replay And Sample Identity

Offline fixture replay is untrusted evidence. It MUST perform zero capability
CAS operations, including diagnostic, validation, or simulated CAS operations.
It MUST NOT receive a production `sample_id`. A fixture may retain a
fixture-scoped identity and documentary provenance, but that identity MUST NOT
be promoted, aliased, or transformed into a production sample identity.

Fixture replay cannot become runtime merely because inputs equal a runtime
trace. It cannot receive a capability, be marked deliverable by this contract,
or satisfy runtime delivery trust. A downstream implementation may reject such
replay entirely; accepting it as untrusted evidence does not weaken these
rules.

## Versioned Documentary Normalization Record

Every dependency normalization retains one versioned documentary record with
exactly these required fields:

- `schema_version`
- `source_kind`
- `source_evidence_id`
- `documentary_notation`
- `documentary_address`
- `documentary_address_base`
- `function_code`
- `logical_table`
- `normalized_zero_based_pdu_offset`
- `word_count`

V1 requires the following named finite positive configuration bounds:

| Bound | Measured value |
| --- | --- |
| `attempt_key_max_utf8_bytes` | exact encoded bytes of each non-empty `AttemptKey` |
| `source_evidence_id_max_utf8_bytes` | exact encoded bytes of each non-empty `source_evidence_id` |
| `normalization_record_max_encoded_bytes` | complete received encoded normalization record |
| `normalization_required_string_max_utf8_bytes` | each required string field other than `source_evidence_id` |
| `normalization_extension_count_max` | number of unknown extension fields |
| `normalization_extension_key_max_utf8_bytes` | exact encoded bytes of each non-empty extension key |
| `normalization_extension_value_max_encoded_bytes` | exact received encoding of each extension value |
| `retained_diagnostic_count_per_object_max` | diagnostic strings retained by one live object |
| `retained_diagnostic_max_utf8_bytes` | each optional retained diagnostic string outside tombstones |
| `capability_tombstone_max_encoded_bytes` | complete retained encoding of one capability tombstone |
| `ledger_audit_tombstone_max_encoded_bytes` | complete retained encoding of either ledger tombstone variant |

The maximum normalization field count is the checked sum of the ten required
fields and `normalization_extension_count_max`. Before activation, every bound
MUST be nonzero and finite, every sum or product implied by count and byte
bounds MUST be checked for overflow and fit the implementation's allocation
limit, and source and ledger `attempt_key_max_utf8_bytes` values MUST agree.

The complete encoded-record bound MUST be checked before decoding an encoded
record or allocating its object tree. Field counts and the byte lengths of the
source evidence identifier, required strings, extension keys, and extension
values MUST be checked with a capped or counting decoder before the ledger
copies or retains them. A pre-decoded caller object requires the same checks by
a bounded counting encoder before any ledger-owned copy. Duplicate field names,
empty extension keys, extension keys that collide with required fields,
invalid UTF-8, truncation, and every over-bound input fail closed. Retained
diagnostics, when present, are an ordered list of UTF-8 strings with no nested
payload. Their count and each string's encoded size are checked before copy and
MUST NOT be truncated to fit.

Unknown extension fields MUST be preserved losslessly. Decode followed by
encode, or parse followed by serialize through the V1 normalization boundary,
MUST produce exact record equality: all required fields, scalar values, field
presence, and unknown extension fields are retained without normalization,
dropping, default insertion, renaming, or reinterpretation. Invalid schema
versions or incomplete required fields fail closed. This exact lossless
obligation applies only to a record admitted within every V1 bound; rejection
of an over-bound record MUST NOT produce a truncated or partially normalized
record.

## Implementation Examples (Non-Normative)

The following are examples only; they do not define a language API or permit a
different observable result. A runtime may keep an internal atomically claimed
cell behind an unexported capability object. Separately, an M2 ledger may hold
a shared pointer to an immutable sealed attempt record that records the claim
outcome without owning that cell. Another implementation may use a different
private layout. Both are conforming only if public copying, endpoint
recreation, coalescing, bounds, sealing, replay, and normalization behavior
remains exactly as specified above.

An offline replay test may prove that a fixture has no capability and records
zero CAS calls. That test is not a way to simulate a successful runtime claim
and is not evidence of a production sample.

## Downstream Obligations And Versioning

`FMV3-M1-06` implements the source-issued runtime capability behavior against
this contract. Its CI MUST first pin and verify the full 40-character merged
docs commit plus the exact policy and manifest SHA-256 digests. `FMV3-M2-01`
must verify the same docs lock and consumes M1-06 only after also pinning and
verifying the full 40-character merged producer SHA. Both downstream issues must
keep fixture and runtime trust distinct, preserve lossless normalization, and
fail closed on any violation.

Their executable conformance suites MUST force the following interleavings and
negative cases: registration paused before instance membership while closure
wins; stale instance-A cancellation against same-key instance B; cancellation
before publication commit; simultaneous publish/cancel with exactly one winner;
cancellation after commit returning `already_published`; ordered-set
permutation, omission, duplication, extra-member, and count mismatch before any
CAS; empty, fixture-only, and mixed-source seal rejection; and secret canaries
absent from the closed publication projection. A prose assertion or manifest
match without these behavioral tests is insufficient.

V1 is closed. Any semantic addition or correction requires a new versioned
contract and manifest; no implementation may silently broaden the enums,
issuance conditions, claim operation, ledger ownership, or normalization
record.
