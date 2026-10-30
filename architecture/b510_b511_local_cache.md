# B510 / B511 local capability and diagnostic caches

This page defines a bounded **Hypothesis** about local software behavior for
controller, communication-module and appliance families. Its only case evidence
is the [synthetic fixture](fixtures/ai28_b510_b511_local_cache.json); there are no
captures or installed-support claims. **Proven** applies only to the declared
representation and predicates checked by the local unittest, not native semantics,
physical qualification, execution authority or admission. Unprovided branches
return **Unknown**. Values, raw bytes, failures, freshness and qualification are
separate dimensions; a retained value is not fresh evidence.

Read the public native contracts first: [B510](../protocols/vaillant/ebus-vaillant-B510.md)
and [B511](../protocols/vaillant/ebus-vaillant-B511.md). They retain candidate wire
layouts and conflicting alternatives. B510's native candidate describes reply
length and a u16 bit; the local count below is not a wire or physical length.
The B511 native candidate failure indication uses index 7; this local hypothesis
uses R[8]. Their correspondence is **Unknown** and neither supersedes the other.
The native OP0E labels (LAN/WLAN/eBUS/PeBUS/backend and others) are raw alternatives,
not proof of this local diagnostic interpretation or physical/cloud health.

## Local rules and boundaries

- B510 success with feedback 1 and count 1 or 2 stores zero; count above 2
  stores bit 6. Count zero has no new candidate rule. Failed query or other
  feedback retains the prior cell with stale/unknown freshness. Initialization
  or reset may overwrite separately; their value is Unknown.
- B511 OP0E is a local getter with a non-null object and nonzero logical length:
  one byte, no request-value or write semantics. Bits 3/5/6/7 remain raw Unknown.
  Router exposure is health == 1, never merely nonzero. Association state 2 for
  connected is a separate domain, not router health 2. Failed signal query
  retains its previous bit 4; a successful result replaces it.
- At injected five-second checks, a counter change means receive-ok and breaks
  the unchanged streak. Five unchanged checks do not reset; the sixth does.
  Post-reset scheduling and counter wrap semantics are Unknown. No real clock,
  polling default or sleep is specified. Six checks span 30 injected seconds.
- Failure-mode OP01 refresh selects registration bit 0, excluding local index 1
  and the local selector independently. A successful parse and nonzero local
  count copies exactly nine bytes, then failure = R[8] & 1. Count is not copy
  size. Short input cannot establish a successful nine-byte parse: Unknown.
  Failed/skipped entries retain their prior failure flag and last-known-good
  bytes; initialization clears the flag separately. Other registration bits
  remain raw; registration value 2 does not select an entry.
- A separate timer consumes retained failure at index 0: nonzero chooses argument
  120; zero selects a capability path whose argument is Unknown. No fresh refresh
  is assumed before this consumer. Refresh/timer ordering remains Unknown.

No runtime, transfer executor, MCP interface or GraphQL contract changes here.
These tuples cannot admit a device or operation; Unknown stays fail-closed.
Serialization below uses JSON scalars and arrays inside table cells. Each row's
grade applies only to that local relation. All byte values are decimal 0..255;
indices and counts are synthetic local coordinates.

## capability

| service | success | feedback | count | prior | value | freshness | grade |
| --- | --- | --- | --- | --- | --- | --- | --- |
| "B510" | 1 | 1 | 1 | 85 | 0 | "Unknown" | "Hypothesis" |
| "B510" | 1 | 1 | 2 | 85 | 0 | "Unknown" | "Hypothesis" |
| "B510" | 1 | 1 | 3 | 85 | 64 | "Unknown" | "Hypothesis" |
| "B510" | 1 | 1 | 0 | 85 | "Unknown" | "Unknown" | "Unknown" |
| "B510" | 0 | 1 | 3 | 85 | 85 | "stale/unknown" | "Hypothesis" |
| "B510" | 1 | 2 | 3 | 85 | 85 | "stale/unknown" | "Hypothesis" |
| "B511" | 1 | 1 | 3 | 85 | "Unknown" | "Unknown" | "Unknown" |

## health

| event | value | exposed | grade |
| --- | --- | --- | --- |
| "initialize" | 0 | false | "Hypothesis" |
| "connected" | 1 | true | "Hypothesis" |
| "leave" | 2 | false | "Hypothesis" |
| "reset" | 2 | false | "Hypothesis" |
| "disconnect" | 2 | false | "Hypothesis" |
| "other" | "Unknown" | "Unknown" | "Unknown" |

## association

| event | value | grade |
| --- | --- | --- |
| "connected" | 2 | "Hypothesis" |
| "connecting" | 1 | "Hypothesis" |
| "other" | "Unknown" | "Unknown" |

## bits

| bit | mask | meaning | grade |
| --- | --- | --- | --- |
| 0 | 1 | "wired diagnostic" | "Hypothesis" |
| 1 | 2 | "wireless diagnostic" | "Hypothesis" |
| 2 | 4 | "cached connection health" | "Hypothesis" |
| 3 | 8 | "raw" | "Unknown" |
| 4 | 16 | "retained successful signal-query result" | "Hypothesis" |
| 5 | 32 | "raw" | "Unknown" |
| 6 | 64 | "raw" | "Unknown" |
| 7 | 128 | "raw" | "Unknown" |

## getter

| service | op | object | logical_count | wired | wireless | health | signal | raw | value | grade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| "B511" | 14 | true | 1 | 0 | 0 | 0 | 0 | 0 | 0 | "Hypothesis" |
| "B511" | 14 | true | 2 | 1 | 1 | 1 | 1 | 232 | 255 | "Hypothesis" |
| "B511" | 14 | true | 1 | 0 | 0 | 2 | 0 | 232 | 232 | "Hypothesis" |
| "B510" | 14 | true | 1 | 0 | 0 | 1 | 0 | 0 | "Unknown" | "Unknown" |
| "B511" | 1 | true | 1 | 0 | 0 | 1 | 0 | 0 | "Unknown" | "Unknown" |
| "B511" | 14 | false | 1 | 0 | 0 | 1 | 0 | 0 | "Unknown" | "Unknown" |
| "B511" | 14 | true | 0 | 0 | 0 | 1 | 0 | 0 | "Unknown" | "Unknown" |

## counter

| previous | steps | reset_at | grade |
| --- | --- | --- | --- |
| 7 | [7,7,7,7,7] | [] | "Hypothesis" |
| 7 | [7,7,7,7,7,7] | [6] | "Hypothesis" |
| 7 | [7,7,7,7,7,8,8,8,8,8,8] | [] | "Hypothesis" |
| 7 | [7,7,7,7,7,8,8,8,8,8,8,8] | [12] | "Hypothesis" |

## signal

| success | result | prior | retained | grade |
| --- | --- | --- | --- | --- |
| false | 0 | 1 | 1 | "Hypothesis" |
| false | 1 | 0 | 0 | "Hypothesis" |
| true | 0 | 1 | 0 | "Hypothesis" |
| true | 1 | 0 | 1 | "Hypothesis" |

## refresh

| service | op | registration | index | selector | success | count | reply | prior | failure | copied | grade |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| "B511" | 1 | 1 | 0 | 3 | true | 1 | [10,11,12,13,14,15,16,17,0] | 1 | 0 | [10,11,12,13,14,15,16,17,0] | "Hypothesis" |
| "B511" | 1 | 1 | 0 | 3 | true | 2 | [10,11,12,13,14,15,16,17,1] | 0 | 1 | [10,11,12,13,14,15,16,17,1] | "Hypothesis" |
| "B511" | 1 | 3 | 0 | 3 | true | 1 | [10,11,12,13,14,15,16,17,2,99] | 1 | 0 | [10,11,12,13,14,15,16,17,2] | "Hypothesis" |
| "B511" | 1 | 2 | 0 | 3 | true | 1 | [0,0,0,0,0,0,0,0,0] | 1 | 1 | [] | "Hypothesis" |
| "B511" | 1 | 1 | 1 | 3 | true | 1 | [0,0,0,0,0,0,0,0,0] | 1 | 1 | [] | "Hypothesis" |
| "B511" | 1 | 1 | 0 | 0 | true | 1 | [0,0,0,0,0,0,0,0,0] | 1 | 1 | [] | "Hypothesis" |
| "B511" | 1 | 1 | 0 | 3 | false | 1 | [0,0,0,0,0,0,0,0,0] | 1 | 1 | [] | "Hypothesis" |
| "B511" | 1 | 1 | 0 | 3 | true | 0 | [0,0,0,0,0,0,0,0,0] | 1 | 1 | [] | "Hypothesis" |
| "B511" | 1 | 1 | 0 | 3 | true | 1 | [0,0,0,0,0,0,0,0] | 1 | "Unknown" | "Unknown" | "Unknown" |
| "B510" | 1 | 1 | 0 | 3 | true | 1 | [0,0,0,0,0,0,0,0,0] | 1 | "Unknown" | "Unknown" | "Unknown" |
| "B511" | 14 | 1 | 0 | 3 | true | 1 | [0,0,0,0,0,0,0,0,0] | 1 | "Unknown" | "Unknown" | "Unknown" |

## timer

| index | failure | argument | path | grade |
| --- | --- | --- | --- | --- |
| 0 | 1 | 120 | "failure" | "Hypothesis" |
| 0 | 2 | 120 | "failure" | "Hypothesis" |
| 0 | 0 | "Unknown" | "capability" | "Hypothesis" |
| 1 | 1 | "Unknown" | "Unknown" | "Unknown" |

## constants

| name | value | grade |
| --- | --- | --- |
| "check_interval_seconds" | 5 | "Hypothesis" |
| "unchanged_threshold" | 6 | "Hypothesis" |
| "copy_bytes" | 9 | "Hypothesis" |
| "failure_index" | 8 | "Hypothesis" |
| "failure_mask" | 1 | "Hypothesis" |
| "getter_bytes" | 1 | "Hypothesis" |
| "refresh_before_timer" | "Unknown" | "Unknown" |
| "failure_initial" | 0 | "Hypothesis" |
| "capability_initial" | "Unknown" | "Unknown" |

