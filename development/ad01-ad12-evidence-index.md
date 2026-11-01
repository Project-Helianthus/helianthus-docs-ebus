# AD01–AD12 evidence index (DOC-03)

This is an unfilled evidence-index template for the twelve adapter-direct
acceptance obligations retained by [docs-ebus #250](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/250)
and [gateway #476](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/476).
It does not certify a row or close either parent.

## Source identity and scope

The supplied [M6a transport matrix](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/matrix/M6a-transport-matrix.md)
indexes CM/FC cases, not the twelve AD cases. The actual retained AD names and
assertions are enumerated in the gateway [transport gate's adapter-direct coverage section](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/scripts/transport_gate.sh).
That section states that a formal AD matrix report is pending. Its general unit
coverage statement is not a per-row result artifact. The table below preserves
those twelve names verbatim. The similarly numbered architectural decisions in
[adapter-direct architecture](../architecture/adapter-direct-multiplexer.md)
and B503 plan decisions are different namespaces; do not join them by number.
C08 owns the separate M6a matrix-link repair; this index does not repair it.

Public native [ENH](../protocols/enh.md) and [ENS](../protocols/ens.md)
contracts govern wire claims first. The [shared conformance catalog](../architecture/enh-ens-conformance-tests.md)
defines the XR assertions; architecture links below describe implementation
obligations rather than new wire facts. ENH/ENS here mean transport prefixes,
not the firmware data-only ENS codec. Linked offline tests are candidate partial
observations, not same-name XR aliases or proof of complete AD acceptance.

## Transport-matrix placement

The gateway's transport conformance matrix runs these rows on the
multiplexer's supported southbound transports, ENH and ENS over the adapter's
single TCP connection, next to the PX arbitration cases and one coexistence
case. Other southbound framings (UDP-plain, TCP-plain, UART-direct) are
reserved and planned only: they have no multiplexer path in the architecture
yet, so their cells stay planned or blocked and never count as run. The schema
lives under `matrix/` in the
[gateway repository](https://github.com/Project-Helianthus/helianthus-ebusgateway).
A matrix cell result becomes a live artifact for a row here only when it names
the row, the transport and its evidence as the result discipline below
requires.

## Retained rows

Every result starts unresolved. `Missing` means no row-scoped result artifact
has been supplied to this index, not that the behavior failed or that no evidence
exists elsewhere. Each live requirement below is an obligation for a separately
authorized operator session, not an instruction to perform a live action now.

| ID | Retained assertion | Public contract | Offline test / gap | Live evidence requirement | Unresolved result |
|---|---|---|---|---|---|
| AD01 | Active path sends/receives transactions | [ENH SEND](../protocols/enh.md#send) and [START](../protocols/enh.md#start--started--failed) | [TestActivePath_RealFlow_NoAccumulationAfterTxnSyn](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/internal/adaptermux/pr502_review_test.go) (partial candidate; not run) | Correlate an active request and response with raw wire bytes, direction and decoded outcome. | Unknown; offline artifact: Missing; live artifact: Missing; qualification: unassessed. |
| AD02 | Passive path zero self-echo | [Echo suppression](../architecture/adapter-direct-multiplexer.md#ad07-echo-suppression) | [TestPassive_NoGarbageDuringGatewayTransaction](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/internal/adaptermux/p3_test.go) (partial candidate; not run) | Correlate gateway transmissions with passive output; demonstrate zero self-echo, including aborted traffic. | Unknown; offline artifact: Missing; live artifact: Missing; qualification: unassessed. |
| AD03 | Passive path reconstructs third-party traffic | [Passive delivery](../architecture/adapter-direct-multiplexer.md#ad12-passive-path-delivery) | [TestObserverContinuityDuringArbitration](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/internal/adaptermux/p3_test.go) (partial candidate; not run) | Correlate independent third-party telegrams with reconstructed passive output; retain raw and interpreted evidence. | Unknown; offline artifact: Missing; live artifact: Missing; qualification: unassessed. |
| AD04 | RESETTED propagates to all consumers | [INIT / RESETTED](../protocols/enh.md#init--resetted); [propagation](../architecture/adapter-direct-multiplexer.md#ad09-resetted-propagation) | [TestSession_ResetDeliveryIsLossless](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/internal/adaptermux/session_test.go) (partial candidate; not run) | Observe reset delivery to active, passive and external consumers; prove pending work is cleared and subsequent traffic recovers. | Unknown; offline artifact: Missing; live artifact: Missing; qualification: unassessed. |
| AD05 | ebusd connects, receives broadcasts | [Proxy compatibility](../architecture/adapter-direct-multiplexer.md#ad08-proxy-listener-compatibility) | [TestP3_ExternalSessionReceivesDuringPending](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/internal/adaptermux/p3_test.go) (partial candidate; not run) | Observe an ebusd client connect and receive actual broadcasts through the compatibility listener. | Unknown; offline artifact: Missing; live artifact: Missing; qualification: unassessed. |
| AD06 | ebusd sends START/SEND successfully | [START](../protocols/enh.md#start--started--failed); [XR_START_RequestStart_WriteAll_NoDoubleSend](../architecture/enh-ens-conformance-tests.md#xr_start_requeststart_writeall_nodoublesend) | [TestSession_StartedArrivesBeforeReceivedBytes](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/internal/adaptermux/session_test.go) (partial candidate; not run) | Observe ebusd START/SEND and matching response; show source is sent once per arbitration attempt. | Unknown; offline artifact: Missing; live artifact: Missing; qualification: unassessed. |
| AD07 | Gateway and ebusd compete by initiator-address priority at SYN | [owner arbitration](../architecture/adapter-direct-multiplexer.md#ad06-owner-arbitration-model) | [TestT02_ThreeBiddersAndRebidOrder](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/internal/adaptermux/issue1402_priority_test.go) (partial candidate; not run) | Observe gateway and ebusd bidding at the same SYN: one START is forwarded for the higher-priority address and the other bidder receives FAILED naming it and re-bids; distinguish this local selection from physical address arbitration. | Unknown; offline artifact: Missing; live artifact: Missing; qualification: unassessed. |
| AD08 | Per-session echo suppression | [Arbitration byte visibility](../protocols/enh.md#arbitration-byte-visibility) and [post-arbitration byte echo](../protocols/enh.md#post-arbitration-byte-echo); [echo suppression](../architecture/adapter-direct-multiplexer.md#ad07-echo-suppression) | [TestArbitrationWinnerSynthesis_MultiSessionDeliversToNonWinner](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/internal/adaptermux/session_test.go) (partial candidate; not run) | Observe multiple sessions: suppress only the synthesized arbitration-byte RECEIVED notification to the winning session while delivering it to other observers; preserve required post-arbitration SEND echoes to the sending session. | Unknown; offline artifact: Missing; live artifact: Missing; qualification: unassessed. |
| AD09 | Adapter disconnect triggers reconnection recovery | [XR_UpstreamLoss_GracefulShutdown_NoHang](../architecture/enh-ens-conformance-tests.md#xr_upstreamloss_gracefulshutdown_nohang) and [XR_START_ReconnectWait_BoundedDeadline](../architecture/enh-ens-conformance-tests.md#xr_start_reconnectwait_boundeddeadline) | [TestUnmanagedConnectionLossKeepsLegacyReconnectLoop](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/internal/adaptermux/connection_health_test.go) (partial candidate; not run) | Observe disconnect, bounded failure, reconnect and resumed traffic without stale-session completion. | Unknown; offline artifact: Missing; live artifact: Missing; qualification: unassessed. |
| AD10 | Migration preserves semantics | [Forward migration](../deployment/adapter-direct-migration.md#forward-migration-proxy-based-to-adapter-direct) | Equivalence test plan: [AD10 comparison records](ad10-migration-equivalence.md) (proposed design; not run). | Per southbound transport, pair the configuration the multiplexer replaces (the direct adapter transport, or ebusd-tcp) with the multiplexer on the same bus and family conditions; in the single session that retires the proxy topologies, the proxy route is an additional replaced side. Compare each semantic field and MCP and GraphQL parity as separate decisions. | Unknown; offline artifact: Missing; live artifact: Missing; qualification: unassessed. |
| AD11 | Rollback restores behavior | [Rollback](../deployment/adapter-direct-migration.md#rollback-adapter-direct-to-a-direct-adapter-transport-or-ebusd-tcp) | Narrowed, not retired. The return target, the standalone proxy topology, is deprecated on the operator decision recorded on helianthus-ebusgateway#1378, so that target alone is retired and a return to it is not an accepted rollback. The supported targets, a direct adapter transport and ebusd-tcp, stay in scope: the [AD11 comparison design](ad11-rollback-equivalence.md) applies to them (proposed design; not run). | Per supported target, compare the pre-migration baseline B with the restored observation R after the documented return, including the new session epoch, cleared adapter-direct session state, cache provenance and MCP and GraphQL parity, as separate decisions. Compatibility cells of the gateway transport matrix do not substitute: they test the target configuration, not the transition. | Unknown; offline artifact: Missing; live artifact: Missing; qualification: unassessed. The retired proxy target never counts as PASS. |
| AD12 | No 0xA9/0xAA escape corruption | [ENH receive path](../protocols/enh.md#send); [XR_ENH_0xAA_DataNotSYN](../architecture/enh-ens-conformance-tests.md#xr_enh_0xaa_datanotsyn); [wire-symbol delivery](../architecture/adapter-direct-multiplexer.md#ad12-passive-path-delivery) | [TestActiveTransport_ImplementsEscapeAware](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/internal/adaptermux/pr502_review_test.go) (partial candidate; not run); [TestEchoTracker_EscapeBytePayload](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/internal/adaptermux/echo_tracker_gateway_test.go) (partial candidate; not run) | Correlate raw escape pairs with logical 0xA9/0xAA payload and raw SYN boundaries at the multiplexer boundary: each raw symbol reaches external sessions unchanged, immediately and in order; every `SEND` is one physical wire byte (host-side escaping on both paths); reserved bytes in a CRC position are sent and verified as both raw symbols; the logical view shows no double escaping or loss of provenance. | Unknown; offline artifact: Missing; live artifact: Missing; qualification: unassessed. |

## Result discipline

For each row, retain separate offline and live artifact references and outcomes:
`Missing` (no supplied artifact), `Not run`, `PASS`, `FAIL` (an executed assertion
was violated), or `Unverified` (execution or evidence could not be checked).
A row marked `Retired` carries no obligation any more; its row states why, it
needs no artifact, and it is never counted as PASS.
A missing artifact, timeout, unavailable tool, or environment failure cannot be
converted to PASS or silently reported as a behavioral FAIL. Record the exact
assertion and failure when a real FAIL exists. Keep all other rows unresolved
unless their own evidence is present; no aggregate PASS fills blank rows.

The gateway [B503 bridge status legend](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/matrix/M6a-vaillant-b503.md#9-production-dispatcher-rows-m6_dispatcher_bridge)
distinguishes `bridge-PASS` (mocked transport) from `bridge-LIVE-PASS`
(operator-attested live evidence). These labels belong to that bridge matrix;
its VB-BR rows do not certify AD rows. Never promote offline evidence to live
qualification. A proposed AD qualification needs its own row-scoped evidence
and review under the retained parent acceptance.

Record evidence grade (`Proven`, `Hypothesis`, `Unknown`) separately from
qualification. A test passing against a mock is implementation evidence only.
A live observation is bounded to the documented adapter/transport family,
firmware context when known, conditions and assertion; it grants neither
universal family qualification nor write authority. Use public/synthetic inputs
and family wording. Do not copy private reports, serials, network coordinates,
capture times or contributor identities. Publish only sanitized raw evidence
beside interpretation, retaining direction, relevant service/payload bytes,
units when known and enough non-identifying conditions/provenance to falsify
the claim. If sanitization removes required proof, leave the row unresolved.

## Conflicts and carry-forward

The architecture's AD01/AD04 retain INFO across in-band RESETTED, while
[the native INFO interleaving contract](../protocols/enh.md#info-frame-length-and-interleaving)
and `XR_INFO_RESETTED_CachePolicy_Explicit` require invalidation on every
RESETTED. The catalog's adaptermux alias is not evidence resolving that
conflict. The architecture's AD12 text now states the wire-symbol contract:
raw symbols at the multiplexer boundary, host-side escaping on both paths, and
a logical view with escape provenance for mux-internal tracking and passive consumers. That resolves the
former conflict with the native ENH physical-wire receive contract; logical
bytes remain a host projection. Keep the INFO conflict visible during review,
especially on reset rows; this index changes no implementation.

No last-known-good artifact is erased by a missing or failing newer run: keep
its original identity, scope and result separately, without splicing sessions
or treating stale evidence as current admission. Admission remains fail-closed
when required evidence is absent or contradictory. AD11 is narrowed on the operator decision recorded on helianthus-ebusgateway#1378: only
the deprecated proxy return target is retired; the parent acceptance under #250/#476 must
record that. All twelve obligations stay open for the supported rollback targets. No transport
production change, hardware waiver, release result, namespace change, MCP
behavior change or GraphQL behavior change is provided by this documentation
slice.
