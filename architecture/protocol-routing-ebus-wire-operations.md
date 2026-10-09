# Protocol routing: eBUS wire operations

This AGPL document contains product policies removed from the CC0
[eBUS wire overview](../protocols/ebus-services/ebus-overview.md).

## Source-address selection

eBUS defines the address byte pattern and arbitration behavior. A product that
chooses a source address needs its own bounded candidate list, target
validation, exclusion policy, and failure state. These controls are not a
protocol membership operation and must not be represented as a universal eBUS
source-address table.

## Same-source collision handling

A shared-client product can retain a bounded timestamped history of its own
transmissions and compare an incoming frame with a recent same-source frame.
Its echo window, source-change grace period, listen-only behavior, and
fail-fast classification are routing policy. They do not alter the native eBUS
per-byte echo or arbitration rules.
