# B524 calendar component selectors

## Native contract and evidence

The [public native B524 contract](ebus-vaillant-B524.md) comes first: service
B5/24 retains opcode, group, instance and register as separate selector axes.
OP02 and OP06 are independent namespaces. Its reply classification and matching
group/register requirements apply before isolated component bytes are considered;
requested instance context is retained, not invented from a reply.

**Hypothesis:** the finite declarations below describe ordered plain u8
components, not packed decimal. They are component-group metadata, not a decoder
or calendar/time constraint admission. Family is a qualification axis; matching
bytes do not establish support on another family. Direction is read, OP is 02,
and all numbers in the selector table are hexadecimal. Dynamic II denotes an
unresolved zone instance context, not a concrete instance or a wildcard.

The [synthetic tuples](fixtures/ak22_b524_component_selectors.json) contain only
isolated component bytes. They are not telegram captures. Source, destination,
firmware, complete reply positions and capture conditions are **Unknown**.
No native capture qualifies these candidate relationships.

## Finite candidate table

Every row has grade **Hypothesis**, independently of native qualification.
Date order is day/month/year; time order is hour/minute/second.

| Family | OP | GG | II scope | RR | Candidate field | Order |
| --- | --- | --- | --- | --- | --- | --- |
| controller-700 | 02 | 00 | 00 | 0034 | clock-date | day/month/year |
| controller-700 | 02 | 00 | 00 | 0035 | clock-time | hour/minute/second |
| controller-700 | 02 | 00 | 00 | 0071 | system-holiday-start-date | day/month/year |
| controller-700 | 02 | 00 | 00 | 0072 | system-holiday-end-date | day/month/year |
| controller-700 | 02 | 03 | dynamic | 0003 | zone-holiday-start-date | day/month/year |
| controller-700 | 02 | 03 | dynamic | 0004 | zone-holiday-end-date | day/month/year |
| controller-720 | 02 | 00 | 00 | 0034 | clock-date | day/month/year |
| controller-720 | 02 | 00 | 00 | 0035 | clock-time | hour/minute/second |
| controller-720 | 02 | 00 | 00 | 00DA | system-holiday-start-date | day/month/year |
| controller-720 | 02 | 00 | 00 | 00DB | system-holiday-end-date | day/month/year |
| controller-720 | 02 | 03 | dynamic | 0003 | zone-holiday-start-date | day/month/year |
| controller-720 | 02 | 03 | dynamic | 0004 | zone-holiday-end-date | day/month/year |
| controller-720 | 02 | 03 | dynamic | 001E | zone-time-001e | hour/minute/second |
| controller-720 | 02 | 03 | dynamic | 0020 | zone-time-0020 | hour/minute/second |
| controller-720 | 02 | 03 | dynamic | 0021 | zone-time-0021 | hour/minute/second |

There is no controller-700 counterpart declared for the three zone-time rows.
DA/DB and 71/72 remain family-specific, with no cross-family fallback. Neither
OP06 nor a different group inherits these entries. Zone dates and zone times
are separate component groups; adjacency establishes no date/time pairing.
No cross-selector pair is declared in this supplement.

**Hypothesis (named date domains):** day 1..31, month 1..12, year 0..99.
These independent domains establish neither joint date validity nor a century
or timezone. Time components are plain u8 (representation range 0..255);
no additional native hour/minute/second constraints are established here.

## Synthetic representation checks

**Proven (local unsigned-byte arithmetic only):**

| Shape | Raw isolated bytes | Ordered numeric components |
| --- | --- | --- |
| date | 1F 0C 63 | day=31, month=12, year=99 |
| time | 17 3B 3A | hour=23, minute=59, second=58 |
| time | 12 00 00 | hour=18, minute=0, second=0 |

Hexadecimal 12 is decimal 18, without BCD reinterpretation. Each component's
raw byte and position remain distinct. Arithmetic establishes only the declared
representation; native meaning remains Hypothesis and physical support Unknown.

## Conflicts and Unknown boundaries

The native contract's calendar sections retain profile-dependent BCD and
candidate century-offset interpretations. This plain-byte candidate does not
resolve those codecs for a physical controller. The
[existing calendar selector table](fixtures/b524-op02-calendar-clock-selectors.csv)
and the native contract label the 720 DA/DB dates as manual-cooling dates.
The system-holiday relationship above is a separate Hypothesis; that role
conflict remains **Unknown**, not a relabeling of the older evidence.

**Unknown:** exact zone-name component selectors, string encoding, width and
termination. A name ending in a suffix supplies none of those facts; there is
no string-part entry. Century, timezone, joint calendar validity, installed
zone domain, native qualification, physical effects, persistence and delivery
also remain Unknown. These declarations establish no writable behavior.
