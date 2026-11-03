# B501 legacy-interface sequencing candidates

## Evidence and scope

The [native B501 and B502 contract](ebus-vaillant.md#b501-and-b502-symbolic-access-and-service-pc-interface)
separates the B501 positive-status form from the independent B502 return-data
service. The [synthetic declarations](fixtures/ak24_b501_legacy_sequence.json)
retain that distinction and add only finite legacy sequencing metadata.

**Hypothesis:** the legacy computer-interface family, identified here as
`legacy-interface`, uses B501 requests, a separate B502 return service,
initiator-to-initiator sequencing, a synchronization wait, and a cooldown of at
least 3500 milliseconds after an explicitly supplied timeout event.
`modern-controller` is neither an alias nor an eligible fallback.
The independent return-service identity is context, not additional sequencing
coverage. No native capture or measured timing is supplied for this candidate.

**Proven (synthetic representation only):** the finite examples distinguish the
declared lower boundary. This does not establish native or physical support.

## Finite candidate relationships

| Property | Candidate value | Grade |
| --- | --- | --- |
| family | legacy-interface | Hypothesis |
| variant | computer-interface | Hypothesis |
| request service | B501 | Hypothesis |
| return service | B502 | Hypothesis |
| sequencing direction | initiator-to-initiator | Hypothesis |
| synchronization required | true | Hypothesis |
| synchronization token | absent; exact bytes Unknown | Unknown |
| post-timeout cooldown minimum | 3500 milliseconds | Hypothesis |
| cooldown trigger | explicit timeout event only | Hypothesis |
| timeout duration | absent; not zero or cooldown-derived | Unknown |
| modern-controller inheritance | none | Hypothesis |

| Service role | Service | Body interpretation | Grade |
| --- | --- | --- | --- |
| request | B501 | opaque request | Hypothesis |
| positive-status | B501 | status form; not B502 return data | Hypothesis |
| return-data | B502 | opaque return data; not B501 status | Hypothesis |

The candidate B501 positive-status notation containing `B5 02` does not make it
a B502 return-data body. Service identity and role remain separate from a byte
prefix; no return codec is inferred.

## Synthetic timing cases

Elapsed values are supplied scalars, not measurements. `minimum-met` states only
that the candidate cooldown inequality is satisfied; it does not establish
synchronization completion, permission to send, or completion of an exchange.
`not-applicable` means this entry contributes no timeout cooldown for that event.
An absent elapsed value remains undetermined after timeout.

| Case | Family | Event | Elapsed milliseconds | Result | Grade |
| --- | --- | --- | --- | --- | --- |
| timeout-below | legacy-interface | timeout | 3499 | below-minimum | Hypothesis |
| timeout-at | legacy-interface | timeout | 3500 | minimum-met | Hypothesis |
| timeout-above | legacy-interface | timeout | 3501 | minimum-met | Hypothesis |
| successful-return | legacy-interface | successful-return | 3499 | not-applicable | Hypothesis |
| no-timeout | legacy-interface | none | 3500 | not-applicable | Hypothesis |
| missing-elapsed | legacy-interface | timeout | absent | elapsed-unknown | Unknown |
| modern-timeout | modern-controller | timeout | 3500 | no-family-entry | Unknown |

## Raw retention and Unknown boundaries

**Unknown:** exact synchronization bytes, state order beyond the synchronization
wait, timeout duration, segmentation, retries, return codec, transport adaptation,
native support, physical effects, persistence and delivery. The synchronization
token and timeout duration are absent, never fabricated as empty bytes or zero.
The cooldown minimum is not a timeout duration. A regular successful return does
not acquire a timeout cooldown solely from this entry.

| Synthetic fragment (hex) | Retention | Interpretation | Qualification |
| --- | --- | --- | --- |
| empty | retain-original-bytes | opaque | Unknown |
| B5 01 | retain-original-bytes | opaque | Unknown |
| B5 02 A6 | retain-original-bytes | opaque | Unknown |

These fabricated fragments are not complete telegrams or synchronization tokens.
Original bytes and partial last-known-good evidence remain available with
uncertain freshness when a new interpretation cannot be admitted. Unknown
metadata fails closed: a candidate relationship supplies no new supported
native claim. Synthetic correctness establishes the declared representation
only. Grade and qualification are independent; every candidate remains
`Hypothesis` with qualification `Unknown`.
