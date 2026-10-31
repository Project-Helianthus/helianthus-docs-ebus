# B50C circuit-name application state

This application contract accompanies the candidate native declarations in the
[B50A to B50D reference](../protocols/vaillant/ebus-vaillant.md#b50a-to-b50d-room-and-remote-control-families).
It is separate from the eBUS wire contract.

For B50C OP02, keep raw name bytes and partial last-known-good values independently
per circuit. Neither a failed read nor an unresolved alternative erases a
successful value. Valid circuits 1 and 3 survive a failed circuit 2; circuit 2
keeps its prior raw value. A bounded 1..15 aggregate is not installed cardinality.

The [synthetic state fixture](fixtures/ac06_room_actions_state.json) illustrates
that retention contract, including trailing spaces in raw name bytes.
**Proven:** the fixture represents the stated independent outcomes.
**Unknown:** runtime implementation and physical qualification. The fixture is
not a device observation and establishes no native wire semantics.
