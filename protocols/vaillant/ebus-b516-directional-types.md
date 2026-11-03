# B516 system-time replies and directional energy types

**Hypothesis:** These five candidate relationships belong to the Vaillant B516
family (`PB=B5`, `SB=16`). Variant labels below are semantic labels; they do not
encode an operation number. Request, read-positive and write-positive are distinct
directions. This supplement does not extend passive energy, float examples or
OP14 local cycles.

## Finite candidate relationships

<!-- relationships:start -->
| Variant | Direction | Field | Declared representation | Grade | Physical reply length |
| --- | --- | --- | --- | --- | --- |
| generic-system-time | positive | system-time | header-only-positive | Hypothesis | Unknown |
| other-system-time | positive | system-time | absent-positive | Hypothesis | Unknown |
| energy-type | request | energy-type | raw-u8-enum | Hypothesis | Unknown |
| energy-type | read-positive | energy-type | low-six-with-independent-flags | Hypothesis | Unknown |
| energy-type | write-positive | energy-type | six-bit-scalar-with-unmodeled-upper-bits | Hypothesis | Unknown |
<!-- relationships:end -->

`other-system-time` groups the other variants with no declared positive; it
does not identify individual products or claim they share a physical behavior.
A header-only declared positive and an absent-positive declaration are different
catalog states. Neither establishes timeout, broadcast or physical reply length.
An absent declaration does not mean a zero-length physical reply. No complete
telegram or physical header length is specified here.

<!-- fields:start -->
| Direction | Value bits | Bit 6 | Bit 7 | Complete enum labels | Positions |
| --- | --- | --- | --- | --- | --- |
| request | raw u8 token | part of enum token | part of enum token | Unknown | Unknown |
| read-positive | low six bits | independent flag | independent flag | Unknown | Unknown |
| write-positive | scalar six bits | unmodeled raw bit | unmodeled raw bit | Unknown | Unknown |
<!-- fields:end -->

**Hypothesis:** The read-positive flags are independent of each other and of the
low-six value. No domain names for those flags are assigned. Write-positive upper
bits are unmodeled, not reserved-zero; neither read-positive flag is assigned to
them. Request tokens retain all eight bits without response bit meanings.

## Synthetic evidence

The [finite synthetic cases](fixtures/ak12_b516_directional_types.json) retain
raw field slices beside candidate interpretations. These are supplied field
slices, not located bytes in a telegram. An empty slice is not used to represent
an absent physical reply.

<!-- cases:start -->
| Case | Variant | Direction | Raw field slice (hex) | Candidate interpretation | Grade | Physical reply length |
| --- | --- | --- | --- | --- | --- | --- |
| request-c1 | energy-type | request | C1 | enum-token=193 | Hypothesis | Unknown |
| read-c1 | energy-type | read-positive | C1 | low-six=1; bit6=true; bit7=true | Hypothesis | Unknown |
| write-c1 | energy-type | write-positive | C1 | low-six=1; unmodeled=C0 | Hypothesis | Unknown |
| read-bit6 | energy-type | read-positive | 40 | low-six=0; bit6=true; bit7=false | Hypothesis | Unknown |
| read-bit7 | energy-type | read-positive | 80 | low-six=0; bit6=false; bit7=true | Hypothesis | Unknown |
| time-header | generic-system-time | positive | not supplied | header-only-positive | Hypothesis | Unknown |
| time-absent | other-system-time | positive | not supplied | absent-positive | Hypothesis | Unknown |
<!-- cases:end -->

**Proven (synthetic representation only):** C1 has low-six value 1 and upper raw
bits C0. Keeping the same raw token across three directions permits distinct
candidate interpretations without erasing any bits. Synthetic consistency
establishes only the declared representation, not native qualification.

## Unknown boundaries

<!-- unknowns:start -->
| Metadata | Status |
| --- | --- |
| Encoded operation numbers | Unknown; absent |
| Complete enum tables | Unknown; absent |
| Missing field positions | Unknown; absent |
| Physical reply length | Unknown |
| Timeout | Unknown |
| Broadcast | Unknown |
| Native support | Unknown |
| Physical effects | Unknown |
| Persistence | Unknown |
| Delivery | Unknown |
<!-- unknowns:end -->

Unknown operation and position metadata is omitted rather than replaced with
zero or an inferred offset. Candidate grade and qualification are separate.
No capture, device observation or complete native enum table is established by
the synthetic cases. The [existing B516 reference](ebus-vaillant-B516-energy.md)
supplies the public family framing; its other layouts do not fill these gaps.
