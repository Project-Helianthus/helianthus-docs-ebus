# B51B local byte budgets and checksums

This page is a pre-1.0 software contract for offline helpers on the B51B family. It is the ordinary companion of AN23 for the same ab23an23 helper surface, and a partial child of issue 736. The parent stays open. The page does not qualify a device, repeat a native family page, or depend on an implementation change.

Nothing here is a Helianthus 1.0 stable surface. The contract adds no major namespace and no experimental namespace. It adds no authorization gate. Roadmap wording for any later gate is 0.11, and this helper does not schedule that work.

Evidence grades stay independent of physical qualification, presence, freshness, and execution. Every row below keeps those axes. Native grade is Unknown on every row. Execution is not run.

## Boundary

The helpers are pure. One call reads its arguments and returns a value. It does not keep a cursor, open a transfer, or decide a later group on its own.

The helper is offline. It does not add or change an MCP tool or a GraphQL field, so those faces gain no new operation.

A call does not yield a device buffer offset. Chunk index and byte progress are not offsets.

| Boundary | Admitted |
| --- | --- |
| authorization_gate | false |
| executor | false |
| framing | false |
| io | false |
| programming_command | false |
| routing | false |
| timeout | false |
| transfer_client | false |

## Signatures

These signatures are hypothetical and are the names used for the whole contract. `procedure` is `grouped_1024` or `single_205`. An omitted `initial` selects the default initial value. Boolean values are not integers for `prior`, `actual`, `start`, or `length`.

| Role | Signature |
| --- | --- |
| plan | PlanLocalBudget(procedure, input) -> (procedure, chunks, consumed, unplanned) |
| progress | AdvanceLocalProgress(prior, accepted, actual) -> (outcome, last_known_good, next) |
| checksum | LocalChecksum(payload, start, length, initial) -> (outcome, value, raw, start, length) |

`PlanLocalBudget` copies input bytes into owned mutable chunk buffers and returns those chunks, the consumed count, and the unplanned count. The procedure identity is returned with them. Empty input returns no chunks. That result is not a peer-empty-packet claim.

`AdvanceLocalProgress` is a pure transition. `accepted` false leaves a valid prior count unchanged. Adding a valid actual count that would exceed the unsigned width is rejected, and the prior count stays the last known good value. A negative prior or actual is rejected. The next count is absent when the transition is rejected.

`LocalChecksum` covers exactly the caller-selected span and returns one numeric value. The raw payload, start, and length are kept when the span is rejected. The numeric value is absent in that case. The returned number is not a byte-swapped pair and not a framed field.

## States

`planned` means the budget call returned owned chunks. `advanced` means a progress call produced a greater next count. `unchanged` means a well-formed progress call kept the prior count, including a rejected chunk whose actual length was not added. `rejected` means the call was not admitted: unknown procedure, a slot role other than chunks, negative count, overflow, malformed span, or a span outside the payload. `checksum` means a numeric value was returned.

Bytes beyond the one grouped plan stay unplanned. The caller plans them by passing that suffix in a new call. Calling again with the same bytes plans the same first group.

The `single_205` alternative returns at most one chunk. It does not inherit the 1024-byte group, the five chunk slots, or the grouped caps.

Local progress is a hypothesis. It advances only by the actual byte count of an accepted chunk. It does not invent a peer counter.

The local checksum is a hypothesis. The polynomial is `0x1021`, the default initial value is `0xFFFF`, the bit order is MSB first, reflection is off, and the final XOR is zero. ASCII `123456789` has check value `0x29B1`. The same digits with explicit initial zero have check value `0x31C3`. Empty input under the default initial value is `0xFFFF`. No peer, block, or transport checksum is identified by these numbers.

## Normative policy

The table is the normative software policy. Planning uses the chunk slots named there. The fifth grouped slot is the last value in `grouped_1024.chunk_caps`. The single-chunk alternative keeps its own cap. `group_limit` `none` means that alternative has no 1024-byte group.

| Key | Value |
| --- | --- |
| alias_chunk_buffers | false |
| auto_plan_later_groups | false |
| copy_slices | true |
| crc.bit_order | msb_first |
| crc.byte_swap | false |
| crc.covers | caller_selected_span_only |
| crc.extra_byte | false |
| crc.final_xor | 0 |
| crc.initial_default | 65535 |
| crc.polynomial | 4129 |
| crc.reflect_input | false |
| crc.reflect_output | false |
| crc.returns | numeric_only |
| grouped_1024.chunk_caps | 206,206,206,206,200 |
| grouped_1024.group_limit | 1024 |
| grouped_1024.groups_per_call | 1 |
| grouped_1024.inherits_grouped_1024 | false |
| grouped_1024.slot_role | chunks |
| peer_empty_packet_claim | false |
| progress.advances_on_rejected | false |
| progress.bool_is_integer | false |
| progress.buffer_offset_from_byte_progress | false |
| progress.buffer_offset_from_chunk_index | false |
| progress.overflow | reject |
| progress.width_bits | 64 |
| raw_rule | (i * 17 + 3) & 255 |
| single_205.chunk_caps | 205 |
| single_205.group_limit | none |
| single_205.groups_per_call | 1 |
| single_205.inherits_grouped_1024 | false |
| single_205.slot_role | chunks |

Synthetic input bytes for a `rule` length are `byte[i] = (i * 17 + 3) & 255`.

## Unknowns

These topics are Unknown. The software rows do not promote them.

| Topic | Evidence | Semantic | Native | Qualification | Presence | Freshness | Execution |
| --- | --- | --- | --- | --- | --- | --- | --- |
| peer_append | Unknown | Unknown | Unknown | Unknown | not_claimed | not_applicable | not_run |
| erase_geometry | Unknown | Unknown | Unknown | Unknown | not_claimed | not_applicable | not_run |
| segment_identity | Unknown | Unknown | Unknown | Unknown | not_claimed | not_applicable | not_run |
| physical_capacities | Unknown | Unknown | Unknown | Unknown | not_claimed | not_applicable | not_run |
| native_crc | Unknown | Unknown | Unknown | Unknown | not_claimed | not_applicable | not_run |
| repeated_group_scheduling | Unknown | Unknown | Unknown | Unknown | not_claimed | not_applicable | not_run |
| persistence | Unknown | Unknown | Unknown | Unknown | not_claimed | not_applicable | not_run |
| support | Unknown | Unknown | Unknown | Unknown | not_claimed | not_applicable | not_run |

## Examples

The table is the finite synthetic set. Raw forms, selection, context, and partial outcomes are on each row. Numeric, semantic, and native grades are separate. Qualification, presence, freshness, and execution are separate again.

| ID | Procedure | Raw | Selection | Context | Outcome | Reason | Result | Numeric | Semantic | Native | Qualification | Presence | Freshness | Execution |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| grouped_1024_exact | grouped_1024 | rule:1024 | input:0+1024 | first_group | planned | - | chunks=206+206+206+206+200;consumed=1024;unplanned=0 | Proven | Proven | Unknown | Unknown | not_claimed | not_applicable | not_run |
| grouped_1025_unplanned | grouped_1024 | rule:1025 | input:0+1025 | unplanned_remainder | planned | - | chunks=206+206+206+206+200;consumed=1024;unplanned=1 | Proven | Proven | Unknown | Unknown | not_claimed | not_applicable | not_run |
| grouped_2048_one_group | grouped_1024 | rule:2048 | input:0+2048 | later_group_not_planned | planned | - | chunks=206+206+206+206+200;consumed=1024;unplanned=1024 | Proven | Proven | Unknown | Unknown | not_claimed | not_applicable | not_run |
| grouped_824_four_chunks | grouped_1024 | rule:824 | input:0+824 | four_chunks_no_fifth | planned | - | chunks=206+206+206+206;consumed=824;unplanned=0 | Proven | Proven | Unknown | Unknown | not_claimed | not_applicable | not_run |
| grouped_825_short_fifth | grouped_1024 | rule:825 | input:0+825 | short_fifth_chunk | planned | - | chunks=206+206+206+206+1;consumed=825;unplanned=0 | Proven | Proven | Unknown | Unknown | not_claimed | not_applicable | not_run |
| grouped_207_short_second | grouped_1024 | rule:207 | input:0+207 | short_second_chunk | planned | - | chunks=206+1;consumed=207;unplanned=0 | Proven | Proven | Unknown | Unknown | not_claimed | not_applicable | not_run |
| grouped_three_byte_hex | grouped_1024 | hex:00ff10 | input:0+3 | short_input | planned | - | chunks=3;consumed=3;unplanned=0 | Proven | Proven | Unknown | Unknown | not_claimed | not_applicable | not_run |
| empty_grouped | grouped_1024 | rule:0 | input:0+0 | no_peer_empty_packet | planned | - | chunks=none;consumed=0;unplanned=0 | Proven | Proven | Unknown | Unknown | not_claimed | not_applicable | not_run |
| single_205_over_206 | single_205 | rule:206 | input:0+206 | single_chunk_remainder | planned | - | chunks=205;consumed=205;unplanned=1 | Proven | Proven | Unknown | Unknown | not_claimed | not_applicable | not_run |
| single_205_exact | single_205 | rule:205 | input:0+205 | exact_single_chunk | planned | - | chunks=205;consumed=205;unplanned=0 | Proven | Proven | Unknown | Unknown | not_claimed | not_applicable | not_run |
| single_205_over_1024 | single_205 | rule:1024 | input:0+1024 | group_policy_not_inherited | planned | - | chunks=205;consumed=205;unplanned=819 | Proven | Proven | Unknown | Unknown | not_claimed | not_applicable | not_run |
| empty_single_205 | single_205 | rule:0 | input:0+0 | no_peer_empty_packet | planned | - | chunks=none;consumed=0;unplanned=0 | Proven | Proven | Unknown | Unknown | not_claimed | not_applicable | not_run |
| unknown_procedure | other | hex:00ff10 | input:0+3 | supplied_procedure | rejected | unknown_procedure | chunks=none;consumed=0;unplanned=3;raw=kept | Proven | Proven | Unknown | Unknown | not_claimed | not_applicable | not_run |
| progress_accept_10_17 | - | - | progress:prior=10;accepted=true;actual=17 | accepted_chunk | advanced | - | last_known_good=10;next=27 | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| progress_reject_10_17 | - | - | progress:prior=10;accepted=false;actual=17 | rejected_chunk | unchanged | - | last_known_good=10;next=10 | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| progress_actual_16 | - | - | progress:prior=10;accepted=true;actual=16 | actual_length | advanced | - | last_known_good=10;next=26 | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| progress_actual_0 | - | - | progress:prior=10;accepted=true;actual=0 | zero_actual | unchanged | - | last_known_good=10;next=10 | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| progress_prior_11 | - | - | progress:prior=11;accepted=true;actual=17 | prior_count | advanced | - | last_known_good=11;next=28 | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| progress_overflow | - | - | progress:prior=18446744073709551615;accepted=true;actual=1 | overflow | rejected | overflow | last_known_good=18446744073709551615;next=absent | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| progress_reject_at_limit | - | - | progress:prior=18446744073709551615;accepted=false;actual=1 | rejected_at_limit | unchanged | - | last_known_good=18446744073709551615;next=18446744073709551615 | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| progress_negative_actual | - | - | progress:prior=10;accepted=true;actual=-1 | negative_actual | rejected | negative_count | last_known_good=10;next=absent | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| progress_negative_prior | - | - | progress:prior=-1;accepted=true;actual=17 | negative_prior | rejected | negative_count | last_known_good=absent;next=absent | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| progress_negative_actual_while_rejected | - | - | progress:prior=10;accepted=false;actual=-1 | negative_actual_while_rejected | rejected | negative_count | last_known_good=10;next=absent | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_digits_default | - | ascii:123456789 | span:0+9;initial=default | caller_selected_span | checksum | - | value=29B1;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_empty_default | - | ascii: | span:0+0;initial=default | empty_selection | checksum | - | value=FFFF;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_digits_initial_0 | - | ascii:123456789 | span:0+9;initial=0 | explicit_initial | checksum | - | value=31C3;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_explicit_default_initial | - | ascii:123456789 | span:0+9;initial=65535 | explicit_initial | checksum | - | value=29B1;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_empty_initial_0 | - | ascii: | span:0+0;initial=0 | explicit_initial | checksum | - | value=0000;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_span_length_8 | - | ascii:123456789 | span:0+8;initial=default | caller_selected_span | checksum | - | value=A12B;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_span_start_1 | - | ascii:123456789 | span:1+8;initial=default | caller_selected_span | checksum | - | value=1FDC;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_initial_1 | - | ascii:123456789 | span:0+9;initial=1 | explicit_initial | checksum | - | value=7610;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_negative_length | - | ascii:123456789 | span:0+-1;initial=default | malformed_span | rejected | negative_span | value=absent;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_negative_start | - | ascii:123456789 | span:-1+9;initial=default | malformed_span | rejected | negative_span | value=absent;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_span_past_end | - | ascii:123456789 | span:0+10;initial=default | span_out_of_range | rejected | span_out_of_range | value=absent;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_empty_span_at_end | - | ascii:123456789 | span:9+0;initial=default | empty_selection | checksum | - | value=FFFF;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_flip_byte_0 | - | hex:303233343536373839 | span:0+9;initial=default | mutated_input_byte | checksum | - | value=C292;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_flip_byte_1 | - | hex:313333343536373839 | span:0+9;initial=default | mutated_input_byte | checksum | - | value=6E62;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_flip_byte_2 | - | hex:313232343536373839 | span:0+9;initial=default | mutated_input_byte | checksum | - | value=91D0;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_flip_byte_3 | - | hex:313233353536373839 | span:0+9;initial=default | mutated_input_byte | checksum | - | value=6C11;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_flip_byte_4 | - | hex:313233343436373839 | span:0+9;initial=default | mutated_input_byte | checksum | - | value=83E0;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_flip_byte_5 | - | hex:313233343537373839 | span:0+9;initial=default | mutated_input_byte | checksum | - | value=5F05;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_flip_byte_6 | - | hex:313233343536363839 | span:0+9;initial=default | mutated_input_byte | checksum | - | value=1E81;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_flip_byte_7 | - | hex:313233343536373939 | span:0+9;initial=default | mutated_input_byte | checksum | - | value=1A80;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |
| crc_flip_byte_8 | - | hex:313233343536373838 | span:0+9;initial=default | mutated_input_byte | checksum | - | value=3990;raw=kept | Hypothesis | Hypothesis | Unknown | Unknown | not_claimed | not_applicable | not_run |

## Fixture

The machine-readable copy of this contract is [`an24_b51b_local_budget_crc.json`](fixtures/an24_b51b_local_budget_crc.json).
