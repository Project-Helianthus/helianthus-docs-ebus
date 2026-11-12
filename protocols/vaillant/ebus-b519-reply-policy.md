# B519 transaction-mode reply policy

**Hypothesis:** The Vaillant B519 family has separate candidate reply policies
for each transaction mode. This supplement covers only OP01 and OP03 mode-policy
metadata. The [field and CRC catalog](ebus-vaillant-b519.md) retains its separate
selector layouts and unresolved CRC coordinates. Its mode-policy Unknown is
narrowed here to candidate relationships, without establishing native behavior.
The family variant remains **Unknown**.

## Finite candidate relationships

The participants are symbolic: initial sender `sender-A`, receiving target
`receiving-target-B`, and that target's associated initiator
`associated-initiator-C`. They are not installation addresses. In the table,
`none` means the axis is not applicable; **Unknown** means unresolved evidence.
The related participant names a candidate relationship, never a proven route.

| Operation | Mode | Alternative | Reply policy | Related participant | Associated initiator | Later query operation | Grade | Qualification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 03 | initiator-to-target | mode-dependent | target-response | receiving-target-B | none | none | Hypothesis | Unknown |
| 03 | initiator-to-initiator | mode-dependent | service-toward-A | sender-A | associated-initiator-C | none | Hypothesis | Unknown |
| 03 | broadcast | mode-dependent | retained-CRC-for-02 | none | associated-initiator-C | 02 | Hypothesis | Unknown |
| 01 | initiator-to-initiator | ack-only | ACK-only | Unknown | associated-initiator-C | none | Hypothesis | Unknown |
| 01 | initiator-to-initiator | crc-positive | CRC-positive | Unknown | associated-initiator-C | none | Hypothesis | Unknown |
| 01 | broadcast | ack-only | ACK-only | Unknown | associated-initiator-C | none | Hypothesis | Unknown |
| 01 | broadcast | crc-positive | CRC-positive | Unknown | associated-initiator-C | none | Hypothesis | Unknown |

For OP03, changing only the mode selects the target response, service/data toward
the initial sender, or retained CRC for a later OP02 query. The latter two modes
use the initiator associated with the receiving target: C remains C, rather than
becoming A or B. Retention is a candidate relationship; its storage location,
duration and effects are **Unknown**. Actual routing remains **Unknown**.

For OP01, ACK-only and CRC-positive alternatives coexist independently in both
initiator-to-initiator and broadcast modes. ACK-only is a response-policy
candidate, not evidence that an acknowledgement occurred. CRC-positive remains
available as a separate alternative, without choosing its byte layout or proving
a positive reply. Neither alternative establishes a completed physical outcome.
OP01 initiator-to-target policy is outside this finite supplement.

## Data boundary

| Operation | Minimum data bytes | Maximum data bytes | Block number in data | Grade |
| --- | --- | --- | --- | --- |
| 03 | 0 | Unknown | no | Hypothesis |
| 01 | Unknown | Unknown | no | Hypothesis |

**Hypothesis:** OP03 data length ranges from zero to the peer-buffer maximum.
The numeric peer capacity is **Unknown**; neither a numeric maximum nor unlimited
capacity follows. Zero-length data does not prove physical acceptance. Three
fabricated bytes do not establish a capacity bound. Data excludes the block
number. Its separate coordinate and encoding are **Unknown**; no byte offset is
inferred. Raw service prefixes and opaque data remain independent of a symbolic
block token. CRC bytes, algorithm and coverage remain **Unknown** here.

## Evidence and unresolved properties

[Synthetic cases](fixtures/ak14_b519_reply_policy.json) preserve the logical
service prefix `B5 19 03` or `B5 19 01`, data and a fabricated block token
separately. These are incomplete logical representations, not telegrams or wire
captures. Each OP03 mode has both `[]` and `[00, FF, 41]` data, with the same
participants and block token. Each OP01 mode retains both policy alternatives.
No model, firmware, physical offset or native observation is established.

**Proven (synthetic representation only):** The finite declarations distinguish
the three OP03 relationships, preserve C, keep both OP01 alternatives, exclude
the block token from data and preserve Unknown numeric capacity. This grade
describes the representation, independently of each candidate's Hypothesis
grade and Unknown qualification.

**Unknown:** Native support, physical effects, persistence, delivery, routing,
actual acknowledgement and storage effects remain unresolved for every row.
Unresolved interpretation preserves raw evidence and independent partial
last-known-good information. Synthetic consistency does not qualify native
behavior or resolve conflicting alternatives.
