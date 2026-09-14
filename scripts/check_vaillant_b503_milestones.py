#!/usr/bin/env python3
"""Validate the bounded B503 live-monitor milestone contract."""
from __future__ import annotations

import pathlib
import re
import sys
from html.parser import HTMLParser

from markdown_it import MarkdownIt


DOC = pathlib.Path("protocols/vaillant/ebus-vaillant-B503.md")
STATUS_SECTION_START = "## 1. Status"
STATUS_SECTION_END = "## 2. Wire Shape"
MILESTONE_HEADING = "## 14. Companion Links (downstream code milestones)"
MILESTONE_TABLE_HEADER = ("Milestone", "Repo", "Artefact")
MARKDOWN_TABLE_DELIMITER_CELL = re.compile(r"^:?-{3,}:?$")
HTML_COMMENT = re.compile(r"<!--.*?(?:-->|$)", re.DOTALL)
COMMONMARK_AUTOLINK = re.compile(r"<(?:https?://|mailto:)[^<>\s]+>", re.IGNORECASE)
NON_RENDERING_CONTAINERS = frozenset(
    ("head", "iframe", "pre", "script", "style", "template")
)
HTML_VOID_ELEMENTS = frozenset((
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
))
MARKDOWN = MarkdownIt("commonmark")
SESSION_SECTION_START = "## 6. Live-Monitor Session"
SESSION_SECTION_END = "## 7. Gateway Operational Contract"
SESSION_TRANSITION_TABLE_START = "### 6.3 Transitions (normative)"
SESSION_TRANSITION_TABLE_END = "**Lock lifecycle (single assignment, owner-conditional):**"
SESSION_TRANSITION_TABLE_HEADER = "| From | Event | To | Side effect |"
SESSION_TRANSITION_TABLE_SEPARATOR = "|---|---|---|---|"
REFRESHING_PUBLIC_SECTION_START = "#### 7.1.1 Refreshing session state (public)"
REFRESHING_PUBLIC_SECTION_END = "### 7.2 Quiesce timing bounds (normative)"
REFRESH_SECTION_START = "### 7.3 Retry and refresh"
REFRESH_SECTION_END = "### 7.4 Ownership release"
RELEASE_SECTION_START = "### 7.4 Ownership release"
RELEASE_SECTION_END = "### 7.5 Reconnect and restart handling"
RECONNECT_SECTION_START = "### 7.5 Reconnect and restart handling"
RECONNECT_SECTION_END = "### 7.6 30s idle-timeout semantics"
IDLE_TIMEOUT_SECTION_START = "### 7.6 30s idle-timeout semantics"
IDLE_TIMEOUT_SECTION_END = "### 7.7 Concurrency with B524"
NORMALIZATION_SECTION_START = "## 8. Public Normalization Rules"
NORMALIZATION_SECTION_END = "## 9. Install-Writes Non-Exposure (v1 invariant)"
INSTALL_WRITE_SECTION_START = "## 9. Install-Writes Non-Exposure (v1 invariant)"
INSTALL_WRITE_SECTION_END = "## 10. F.xxx Decimal Caveat (LOCAL_CAPTURE only)"
CAPABILITY_TRUTH_TABLE_SECTION_START = "### 12.5 Capability-signal 8-state truth table (mirror of AD18)"
CAPABILITY_TRUTH_TABLE_SECTION_END = "**Forbidden states** (M6 tests assert absence):"
CAPABILITY_TRUTH_TABLE_HEADER = (
    "#", "State", "Capability output", "Stale-frame discipline",
)
M2B_GRAPHQL = (
    "`M2b_GATEWAY_GRAPHQL`",
    "`helianthus-ebusgateway`",
    "GraphQL diagnostic read-only parity + `vaillantCapabilities.b503` signal and "
    "five-state `vaillantLiveMonitor` session status (`Idle` / `Enabling` / "
    "`Active` / `Refreshing` / `Disabled`); only the bounded session "
    "enable/disable action through the §6 FSM",
)
M3_PORTAL = (
    "`M3_PORTAL`",
    "`helianthus-ebusgateway`",
    "Vaillant pane (errors / service / live-monitor diagnostic reads) plus "
    "Gateway-owned five-state live-monitor session strip (`Idle` / `Enabling` / "
    "`Active` / `Refreshing` / `Disabled`) and only the bounded session "
    "enable/disable action through the §6 FSM",
)
INSTALL_WRITE_NON_EXPOSURE = (
    "> **`02 01` and `02 02` MUST NOT be exposed on any public surface in v1.**"
)
INSTALL_WRITE_SECTION = (
    "## 9. Install-Writes Non-Exposure (v1 invariant)\n\n"
    "`Clearerrorhistory` (selector `02 01`) and `Clearservicehistory` (selector\n"
    "`02 02`) are classified `INSTALL_WRITE` (§4) and are subject to the following\n"
    "normative v1 invariant:\n\n"
    "> **`02 01` and `02 02` MUST NOT be exposed on any public surface in v1.**\n"
    "> This includes, without exception, MCP tools, GraphQL mutations, portal UI\n"
    "> affordances (including hidden / feature-flagged DOM), and Home Assistant\n"
    "> services.\n\n"
    "Enforcement:\n\n"
    "- `M2a_GATEWAY_MCP` acceptance includes a negative test asserting no MCP tool\n"
    "  exists for these selectors.\n"
    "- `M2b_GATEWAY_GRAPHQL` acceptance includes a schema introspection diff\n"
    "  asserting no mutation exists for these selectors.\n"
    "- `M3_PORTAL` acceptance includes a DOM audit scanning for any element\n"
    "  referencing `clear`, `delete`, or `reset` keywords in the B503 pane.\n\n"
    "Any future exposure of these selectors requires a **separate plan** and a new\n"
    "doc-gate PR per `AGENTS.md §8.4`, including installer-mode authentication\n"
    "design and isolated-hardware bench evidence.\n\n"
)
COLD_BOOT_TRUTH_ROW = (
    "1",
    "cold-boot, no successful dispatch yet",
    "`UNKNOWN`",
    "n/a",
)
DISCONNECT_ACTIVE_TRUTH_ROW = (
    "3",
    "disconnect during ACTIVE session",
    "`UNKNOWN` while the cleanup obligation remains",
    "in-flight requests fail `TRANSPORT_DOWN`; retain defensive cleanup; no late mutation",
)
RECONNECT_PRE_DISPATCH_TRUTH_ROW = (
    "4",
    "reconnect, before first post-reconnect dispatch",
    "`UNKNOWN` (NOT sticky `AVAILABLE`)",
    "reset to `UNKNOWN` regardless of pre-disconnect state",
)
STALE_EPOCH_COMPLETION_TRUTH_ROW = (
    "8",
    "stale in-flight completion across epoch rollover",
    "n/a — frame discarded",
    "reply/NAK/timeout from epoch N arriving after reconnect to epoch N+1 MUST be "
    "discarded; MUST NOT mutate capability to `AVAILABLE`; MUST NOT satisfy any "
    "post-reconnect waiter",
)
REFRESHING_CAPABILITY_TRUTH_ROW = ('7', 'held-session epoch refresh; session status `Refreshing`', '`UNKNOWN` (temporary during refresh; remains `UNKNOWN` after any triggering DISABLE)', 'triggering READ or current-owner DISABLE remains pending and is dispatched exactly once only after successful rebind; READ returns to `Active` only if its dispatch completes without transport disconnect, while a disconnect releases ownership into `DISABLED`; DISABLE records and returns its exact native outcome, releases ownership, retains fail-closed cleanup, and admits no Enable; subsequent live-monitor operations are `SESSION_BUSY`; only `vaillantCapabilities` and `vaillantLiveMonitorSession` status queries remain admitted')
STEADY_AVAILABLE_TRUTH_ROW = ('2', 'post-first-success steady state; no cleanup obligation or unproven-session fence', '`AVAILABLE`', 'diagnostic success alone never clears an unproven-session or restart fence')
RECONNECT_AVAILABLE_TRUTH_ROW = ('5', 'reconnect, post-first-success-after-reconnect; no cleanup obligation or unproven-session fence', '`AVAILABLE`', 'diagnostic success alone never clears an unproven-session or restart fence')
DISPATCH_FAILURE_TRUTH_ROW = ('6', 'timeout/NAK/CRC during dispatch', '`UPSTREAM_RPC_FAILED` to caller; capability stays last-known only when the operation creates no cleanup obligation; every post-emission Enable outcome and every disable/refresh failure that leaves settlement unproven publishes `UNKNOWN` per §6–§8', 'cleanup-bearing outcomes retain the Gateway-owned attempt identity, admit no Enable, and never trigger automatic reconnect/restart recovery')
CAPABILITY_TRUTH_ROWS = (
    COLD_BOOT_TRUTH_ROW,
    STEADY_AVAILABLE_TRUTH_ROW,
    DISCONNECT_ACTIVE_TRUTH_ROW,
    RECONNECT_PRE_DISPATCH_TRUTH_ROW,
    RECONNECT_AVAILABLE_TRUTH_ROW,
    DISPATCH_FAILURE_TRUTH_ROW,
    REFRESHING_CAPABILITY_TRUTH_ROW,
    STALE_EPOCH_COMPLETION_TRUTH_ROW,
)
CURRENT_PUBLIC_SESSION_AUTHORITY = (
    "**Current public contract authority.** The five-state public session contract in\n"
    "§6–§8 and the exact eight-row public capability table in §12.5 are governed by\n"
    "this document's current doc-gate revision (docs-ebus#523). They supersede prior\n"
    "public session-presentation and capability-output wording where the archived\n"
    "amendment-1 plan differs. In particular, row 3 returns `TRANSPORT_DOWN` to the\n"
    "in-flight caller while retained cleanup publishes capability `UNKNOWN`. The\n"
    "amendment-1 plan SHA remains traceability evidence for its original dispatcher\n"
    "and stale-epoch design; it is not conflict authority for the current public\n"
    "contract. This revision does not add a compatibility state, route, or fallback.\n\n"
    "Changes to plan-traced selectors, wire shape, or invoke-safety classification\n"
    "require a new plan revision and corresponding doc-gate PR. A correction limited\n"
    "to the current public session contract requires its own doc-gate PR and current\n"
    "source evidence; it does not claim or create execution-plan state."
)
CURRENT_CAPABILITY_TABLE_AUTHORITY = (
    "The `vaillantCapabilities.b503` capability output (§11) follows the exact\n"
    "eight-row table below. This current doc-gate revision is the public contract.\n"
    "The archived plan AD18 entry in\n"
    "`vaillant-b503-namespace-w17-26.implementing/10-scope-decisions.md` is retained\n"
    "as provenance for the initial dispatcher design; rows 2, 3, 5, 6, and 7 include\n"
    "the current cleanup/restart refinement. Each row is a separate\n"
    "`M6_DISPATCHER_BRIDGE` test target; missing coverage on any row is an automatic\n"
    "merge-gate block."
)
FORBIDDEN_PLAN_CONFLICT_AUTHORITY = (
    "On conflict, the plan wins",
    "On disagreement between this doc and the plan, the plan wins",
    "the canonical source; this table mirrors it for doc-gate completeness",
)
SESSION_STATE_CONTRACT = 'five stable states: `Idle`, `Enabling`, `Active`, `Refreshing`, and `Disabled`.\n`Refreshing` means an epoch refresh holds the ownership gate. The already\nadmitted triggering request remains pending; subsequent bus-facing live-monitor\noperations are busy. Refresh success dispatches a triggering read exactly once\nand returns `Active` only when that dispatch completes without a transport\ndisconnect; a disconnect follows the any-transport-disconnect transition below\nand releases the owner. Refresh success may instead dispatch a triggering\ncurrent-owner disable exactly once. Every disable result is recorded and\nreturned exactly, but the result alone never establishes native session\nsettlement. Refresh failure releases the gate, enters internal `DISABLED`,\nretains a Gateway cleanup obligation, and returns the exact Gateway-supplied\nfailure to that request; its public session observation is `Idle` with\n`owned:false` and unavailable capability. `Disabled` is never reported with\n`owned:true`.'
DISABLED_PUBLIC_MAPPING = (
    "**Stable public `Disabled` mapping:** `Disabled` with `owned:false` represents\n"
    "only an out-of-band administrative/configuration-disabled condition supplied\n"
    "by Gateway. It is never the result of a current-owner live-monitor session\n"
    "DISABLE action; every terminal outcome of that action presents public `Idle`\n"
    "with `owned:false`, retains cleanup, and publishes `UNKNOWN`. A still-effective\n"
    "out-of-band disabled condition takes precedence across Gateway restart and\n"
    "continues to present `Disabled` with `owned:false`. Enable failure, the 30s idle\n"
    "timeout, transport disconnect, and every other restart-derived internal cleanup\n"
    "path may traverse `DISABLED`, but their stable public session observation is\n"
    "`Idle` with `owned:false`. While a process-local cleanup obligation remains,\n"
    "capability is `UNKNOWN` and Enable is unavailable; `Idle` does not make the\n"
    "internal slot re-claimable. `Disabled` is never reported with `owned:true`."
)
REFRESHING_CLEANUP_CONTRACT = 'When a locally token-owning consumer leaves a target or navigates away while\nits session is `Refreshing`, it MUST queue that target/token disable without\ninvoking the busy operation. After successful refresh reaches `Active`, it\ndispatches the queued disable; after refresh failure releases ownership and\npresents `Idle`, it clears the browser queued pair without a client disable\nwhile Gateway retains the process-local cleanup obligation. If the triggering request was itself the\ncurrent-owner DISABLE, that single disable is the only client dispatch. Its\nexact ACK, NAK, or failure outcome is returned and recorded, while Gateway\nretains process-local fail-closed cleanup because the outcome alone does not\nprove native settlement. The consumer clears the queued pair without issuing a\nsecond disable.'
ENABLING_CLEANUP_CONTRACT = (
    "When a consumer leaves a target or navigates away while its locally initiated\n"
    "enable is pending, it MUST register cleanup under the exact\n"
    "`(targetAddress, localEnableAttemptID, presentationEpoch)` tuple. The consumer\n"
    "allocates a fresh opaque `localEnableAttemptID` before dispatch and never reuses\n"
    "it. Successful\n"
    "completion of that same attempt supplies the issuer token and dispatches\n"
    "exactly one target/token disable. Any other completion—including `ctx.Done`\n"
    "before bus turnaround, ACK timeout, NAK, CRC mismatch, bus-arbitration timeout,\n"
    "epoch-advance discard, transport disconnect, gateway restart, or any other\n"
    "terminal failure—clears that registration without issuing a client disable\n"
    "before any later enable is admitted. The registration MUST NOT transfer to a\n"
    "later attempt or session. Gateway may separately emit the single defensive\n"
    "native disable required by the §6.3 terminal-failure transition."
)
REFRESHING_UNKNOWN_STRIP_CONTRACT = (
    "During a held `Refreshing` epoch, the\n"
    "session strip remains observable alongside temporarily `UNKNOWN` capability,\n"
    "but it is status-only: only `vaillantCapabilities` and\n"
    "`vaillantLiveMonitorSession` remain admitted so the client can observe\n"
    "completion. No B503 card, general tabs, bus-facing reads, or actions are\n"
    "admitted while Gateway reports `Refreshing`. If the triggering READ succeeds\n"
    "and rebinds the same target and issuer token into `Active` with `owned:true`,\n"
    "the bounded current-owner READ/DISABLE exception above resumes immediately\n"
    "under `UNKNOWN`; it does not wait for `AVAILABLE` and does not extend to a\n"
    "different target, token, or general `UNKNOWN` presentation."
)
ACTIVE_UNKNOWN_OWNER_CONTRACT = (
    "After a successful Enable ACK, session is `Active` with `owned:true` while\n"
    "capability remains `UNKNOWN` because settlement is unproven. The consumer that\n"
    "still holds the exact current issuer token for that target may retain the\n"
    "session strip and dispatch only current-owner READ or DISABLE. It MUST NOT\n"
    "admit a second Enable, general B503 tabs, a new projection entry, or those\n"
    "controls for another `UNKNOWN` target/session. Target switch, navigation away,\n"
    "ownership loss, or departure from `Active` removes this exception and follows\n"
    "the cleanup contract below."
)
REFRESH_SUCCESS_CONTINUATION = "- On refresh success for a surviving authenticated current-owner handle, the\n  old epoch-N key authorizes only that refresh. Gateway atomically installs the\n  returned current `transport_key` for epoch N+1 with the same issuer token and\n  target before returning to `Active`; every epoch-N completion is fenced. This\n  is continuation, not reconstruction or auto-resume. The already-admitted\n  triggering request remains pending during refresh; after successful rebind,\n  Gateway dispatches that request's native operation exactly once using the\n  rebound key and returns its exact outcome. A triggering READ retains the\n  owner in `Active` only when its dispatch completes without transport\n  disconnect; a disconnect releases the owner into `DISABLED`. A triggering\n  current-owner DISABLE emits its disable after quiesce, records and returns the\n  exact native outcome, releases the owner, and remains in internal `DISABLED`.\n  ACK and NAK do not establish settlement: Gateway retains process-local\n  cleanup, publishes `UNKNOWN`, and admits no Enable. ENABLE is never a refresh\n  trigger. This dispatch consumes the request's only retry budget."
REFRESH_FAILURE_CAPABILITY_PRECEDENCE = (
    "- On refresh failure, return the exact Gateway result—including\n"
    "  `TRANSPORT_DOWN` or `UNKNOWN`—to the triggering caller. While the resulting\n"
    "  cleanup obligation remains, public capability is `UNKNOWN`; the exact caller\n"
    "  result MUST NOT be collapsed into `SESSION_BUSY`."
)
REFRESH_OWNER_REBINDING = 'On an `ACTIVE` epoch advance from N to N+1, the old `session_key` authorizes\nonly the one bounded refresh attempt. A successful refresh returns the current\n`transport_key` for epoch N+1. Gateway MUST atomically replace the owner key\nwith `(transport_key[N+1], same issuer_token)` while retaining the same target,\nthen dispatch the admitted triggering operation exactly once. Completions and\ncontrol requests still bound to epoch N are stale and MUST NOT satisfy, disable,\nextend, or mutate the rebound session. If refresh fails, no rebound key is\ninstalled; Gateway releases client ownership, retains a fresh Gateway-owned\nprocess-local cleanup obligation in internal `DISABLED`, presents public\nsession `Idle` with `owned:false`, publishes capability `UNKNOWN`,\nand admits no Enable while native settlement remains unproven.'
NO_AUTO_RESUME_RECONSTRUCTION = '- Gateway MUST NOT reconstruct or auto-resume a session after restart, a lost\n  owner handle, or an absent/invalid current issuer token. The surviving\n  authenticated current-owner refresh path in §7.3 is the only continuation\n  allowed across a non-terminal epoch advance.'
REFRESHING_DISCONNECT_FENCE = '- A terminal transport disconnect follows §7.4: it releases any held owner and\n  does not enter `Refreshing` on reconnect. An `Idle` target with no owner or\n  cleanup obligation stays `Idle` through disconnect/reconnect and requires a\n  new explicit client Enable.\n- If cleanup/session settlement is unproven, the transport layer MUST NOT\n  publish the new epoch as B503-usable or admit Enable. Reconnect emits no\n  automatic B503 enable or disable. Gateway preserves the process-local target,\n  attempt, and prior epoch only as evidence/cleanup state, publishes `UNKNOWN`,\n  and waits for a future accepted settlement contract.'
DISCONNECT_CLEANUP_OBLIGATION = '- On transport disconnect, Gateway transitions the FSM to `DISABLED` and, if an\n  owner was held, releases `liveMonitorMu`. If an Enable may have reached the\n  wire or settlement is otherwise unproven, Gateway retains\n  `(targetAddress, gatewayCleanupAttemptID, priorTransportEpoch)` only as a\n  process-local cleanup obligation across transport reconnect. It carries no\n  issuer token, owner authority, session continuation, or operation eligibility\n  and cannot authorize an automatic reconnect write.'
OWNER_CONDITIONAL_MUTEX_SCOPE = (
    "Only release of `liveMonitorMu` is owner-conditional (§6.3 \"Lock lifecycle\"):\n"
    "it occurs only when an owner is held at the moment the event fires. Cleanup\n"
    "obligations and their native outcomes remain effective after owner release,\n"
    "including defensive cleanup while the FSM is already `DISABLED`; `IDLE` or\n"
    "`DISABLED` makes the event a no-op only with respect to mutex release."
)
DISCONNECT_CLEANUP_MUTEX_INDEPENDENCE = '- If the FSM was already `IDLE` or `DISABLED` at transport-disconnect time,\n  disconnect is a no-op with respect to the mutex; no release is attempted. A\n  pre-existing cleanup obligation remains across that disconnect.\n- If the FSM was already `IDLE` or `DISABLED` at Gateway-restart time, restart\n  is likewise a no-op with respect to the mutex. It still destroys every\n  process-local cleanup attempt identity and enforces the per-target `UNKNOWN`\n  fence; no prior attempt identity survives process restart.'
CONFIRMED_CLEANUP_DEFINITION = 'An ACK or NAK is an exact native outcome, not proof that the device session\nstopped or was never created. After any emitted Enable, Gateway may use one\nbounded defensive disable during the same admitted lifecycle and records its\noutcome, but no current 0.7 outcome makes the session slot re-claimable. Gateway\nretains fail-closed cleanup, publishes capability `UNKNOWN`, and denies Enable\nuntil a separately evidenced native settlement observation exists. Current\npublic evidence defines no such observation; its evidence and recovery contract\nare deferred to [issue #525](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/525).'
UNCONFIRMED_CLEANUP_OBLIGATION = '- Every native disable used for explicit, idle-timeout, refreshed, or defensive\n  cleanup records its exact ACK, NAK, timeout, CRC, arbitration, disconnect, or\n  other outcome. No such outcome alone clears the obligation or proves native\n  session settlement. Gateway retains the target plus a fresh Gateway-owned\n  `gatewayCleanupAttemptID` and attempted transport epoch as process-local,\n  operation-ineligible cleanup state, publishes `UNKNOWN`, admits no Enable,\n  and performs no same-epoch or automatic reconnect/restart recovery.'
GATEWAY_CLEANUP_ATTEMPT_ID = (
    "- Gateway allocates `gatewayCleanupAttemptID` when the cleanup obligation is\n"
    "  created and never reuses it. This opaque ID is internal to Gateway; it is not\n"
    "  the browser-local `localEnableAttemptID`, is not supplied by a caller, and\n"
    "  confers no owner or operation authority."
)
CONFIRMED_CLEANUP_DIAGRAM = 'DISABLED --> DISABLED: native outcome recorded; settlement remains unproven'
EXPLICIT_DISABLE_CONFIRMED_TRANSITION = '| `ACTIVE` | current-owner session DISABLE action; any ACK / NAK / timeout / CRC mismatch / bus-arbitration failure / disconnect / other outcome | `DISABLED` | emit disable exactly once after quiesce, record and return its exact outcome, release the owner, retain `(targetAddress, fresh gatewayCleanupAttemptID, currentTransportEpoch)` as process-local cleanup, present public `Idle` with `owned:false`, publish `UNKNOWN`, and admit no Enable; this session action never produces public `Disabled`, and its outcome does not prove settlement |'
EXPLICIT_DISABLE_UNCONFIRMED_TRANSITION = EXPLICIT_DISABLE_CONFIRMED_TRANSITION
RESTART_TRANSITION = '| any | gateway restart | `DISABLED` | release any owner and destroy every caller handle and process-local attempt identity; reconstruct no session, emit no automatic B503 enable or disable, and publish `UNKNOWN` for each qualified target; a still-effective out-of-band administrative/configuration-disabled condition presents public `Disabled` with `owned:false`, otherwise the restart-derived state presents public `Idle` with `owned:false`; admit no Enable under the current 0.7 contract |'
RESTART_RELEASE_CONTRACT = '- On Gateway restart, Gateway transitions the FSM to `DISABLED` and, if an\n  owner was held, releases `liveMonitorMu`. No session or cleanup tuple persists\n  across restart. Because Gateway can no longer distinguish its pre-restart\n  session from a session owned by another bus client, it emits no automatic\n  B503 enable or disable. Each qualified target starts with live-monitor\n  capability `UNKNOWN`, and Enable remains unavailable under the current 0.7\n  contract.'
RESTART_CLEANUP_FENCE = "- After every Gateway process restart, enumerate the finite registry-qualified\n  B503 targets, set each target's live-monitor capability to `UNKNOWN`, admit no\n  Enable, and emit no automatic B503 enable or disable. The Portal and GraphQL\n  v1 surfaces expose no recovery control. Current 0.7 defines no ACK/NAK-based\n  maintenance action that restores availability; later evidence and any changed\n  recovery contract belong to deferred issue #525."
IDLE_TIMEOUT_ACK_CONTRACT = '- Gateway records the exact disable ACK, NAK, timeout, CRC, arbitration,\n  disconnect, or other outcome, releases the owner, retains process-local\n  cleanup, publishes `UNKNOWN`, and admits no Enable. No outcome alone returns\n  the internal FSM to `IDLE` or preserves public `AVAILABLE` because native\n  session settlement remains unproven. Idle auto-disable MUST NOT be reported as\n  `NOT_SUPPORTED`, which is reserved for "device class does not implement\n  B503" (§11).'
NORMALIZED_REFRESH_DISABLE_CONTRACT = '2. **Refresh once.** On epoch advance with a held session, Gateway transitions\n   to `Refreshing` and makes exactly one refresh attempt. The already-admitted\n   triggering READ or current-owner DISABLE remains pending and is dispatched\n   exactly once only after successful rebind. READ returns Gateway to `Active`\n   only when its dispatch completes without transport disconnect; a disconnect\n   releases the owner under the `any` disconnect transition. DISABLE records and\n   returns its exact native outcome, releases ownership, retains fail-closed\n   cleanup in internal `DISABLED`, publishes `UNKNOWN`, and admits no Enable.\n   Subsequent bus-facing live-monitor operations are `SESSION_BUSY` during\n   refresh. Refresh failure likewise releases client ownership but retains\n   Gateway cleanup, publishes `UNKNOWN`, and admits no Enable.'
REFRESH_FAILURE_DIAGRAM = (
    "REFRESHING --> DISABLED: refresh failure retains cleanup"
)
REFRESH_READ_DIAGRAM = (
    "REFRESHING --> ACTIVE: refresh succeeds; triggering READ completes without disconnect"
)
REFRESH_DISABLE_DIAGRAM = (
    "REFRESHING --> DISABLED: refresh succeeds; triggering DISABLE once"
)
UNCONFIRMED_CLEANUP_DIAGRAM = 'DISABLED --> DISABLED: native outcome recorded; settlement remains unproven'
REFRESH_READ_TRANSITION = (
    "| `REFRESHING` | refresh succeeds for triggering READ; dispatched READ "
    "completes without transport disconnect | `ACTIVE` | atomically rebind the "
    "owner from epoch N to the returned current `transport_key` at N+1, "
    "retaining the same issuer token and target; fence every epoch-N completion; "
    "dispatch READ exactly once using the rebound key, return its outcome, and "
    "retain the owner; any transport disconnect instead follows the `any` disconnect "
    "row and releases the owner into `DISABLED` |"
)
REFRESH_DISABLE_TRANSITION = '| `REFRESHING` | refresh succeeds for triggering current-owner DISABLE; any terminal native outcome | `DISABLED` | atomically rebind to the N+1 key, fence every epoch-N completion, emit disable exactly once after quiesce, record and return its exact outcome, release the owner, retain `(targetAddress, fresh gatewayCleanupAttemptID, transportEpoch[N+1])` as process-local cleanup, publish `UNKNOWN`, and admit no Enable; no outcome alone proves settlement |'
REFRESH_DISABLE_UNCONFIRMED_TRANSITION = '| `REFRESHING` | refresh succeeds for triggering current-owner DISABLE; any terminal native outcome | `DISABLED` | atomically rebind to the N+1 key, fence every epoch-N completion, emit disable exactly once after quiesce, record and return its exact outcome, release the owner, retain `(targetAddress, fresh gatewayCleanupAttemptID, transportEpoch[N+1])` as process-local cleanup, publish `UNKNOWN`, and admit no Enable; no outcome alone proves settlement |'
UNCONFIRMED_CLEANUP_TRANSITION = '| `DISABLED` | defensive-disable ACK / NAK / timeout / CRC mismatch / bus-arbitration failure / disconnect / other outcome | `DISABLED` | retain process-local cleanup, record the exact outcome, publish `UNKNOWN`, admit no Enable, and perform no same-epoch or automatic reconnect/restart recovery; only a future accepted settlement contract may define re-claimability |'
ADMIN_DISABLED_TRANSITION = '| `IDLE` / `DISABLED` with no owner | Gateway reports an out-of-band administrative/configuration-disabled condition | `DISABLED` | emit no native B503 operation; present public `Disabled` with `owned:false`, block Enable, and retain any pre-existing cleanup/fence; this condition is distinct from the current-owner session DISABLE action |'
CONFIRMED_CLEANUP_TRANSITION = '| `DISABLED` | defensive-disable ACK / NAK / timeout / CRC mismatch / bus-arbitration failure / disconnect / other outcome | `DISABLED` | retain process-local cleanup, record the exact outcome, publish `UNKNOWN`, admit no Enable, and perform no same-epoch or automatic reconnect/restart recovery; only a future accepted settlement contract may define re-claimability |'
REFRESH_FAILURE_TRANSITION = '| `REFRESHING` | refresh failure | `DISABLED` | release ownership gate, return the exact Gateway-supplied failure without dispatching the triggering native operation, retain `(targetAddress, fresh gatewayCleanupAttemptID, attemptedTransportEpoch)` as process-local cleanup, present public session `Idle` with `owned:false`, publish `UNKNOWN`, and admit no Enable |'
HELD_OWNER_DISABLED_RELEASE = (
    "on entry to `DISABLED` from `ENABLING`, `ACTIVE`, or\n`REFRESHING`"
)
ENABLING_EPOCH_PRE_DIAGRAM = (
    "ENABLING --> IDLE: epoch advance before enable frame emission"
)
ENABLING_EPOCH_POST_DIAGRAM = (
    "ENABLING --> DISABLED: epoch advance after enable frame emission"
)
ENABLING_EPOCH_PRE_OPERATION = (
    "| Epoch advance while `ENABLING`, before enable-frame emission | — | → "
    "`IDLE`; cancel the queued frame, release the gate, and discard every stale "
    "completion or failure outcome from that enable attempt; explicit new Enable "
    "required |"
)
ENABLING_EPOCH_POST_OPERATION = '| Epoch advance while `ENABLING`, after enable-frame emission | pending attempt identity and target remain Gateway-owned for cleanup only | → `DISABLED`; fence every stale completion, issue at most one defensive disable after quiesce during the admitted lifecycle, and record its exact native outcome; ACK and NAK do not settle the session, so the §7.4 process-local obligation remains fail-closed and no automatic retry or active owner survives |'
ENABLING_EPOCH_PRE_TRANSITION = (
    "| `ENABLING` | epoch advance detected before enable-frame emission | `IDLE` | "
    "cancel the queued frame, release ownership, and discard every stale completion "
    "or failure outcome from that enable attempt; explicit new Enable required |"
)
ENABLING_EPOCH_POST_TRANSITION = '| `ENABLING` | epoch advance detected after enable-frame emission | `DISABLED` | fence every stale completion, issue at most one defensive disable after quiesce during the admitted lifecycle, record its exact native outcome, release ownership, retain fail-closed cleanup, publish `UNKNOWN`, and admit no Enable |'
ENABLING_CANCEL_DIAGRAM = "ENABLING --> IDLE: canceled before enable frame emission"
ENABLING_FAILURE_DIAGRAM = 'ENABLING --> DISABLED: terminal enable outcome after emission'
CODE_REQUIRED_FRAGMENTS = frozenset((
    CONFIRMED_CLEANUP_DIAGRAM,
    UNCONFIRMED_CLEANUP_DIAGRAM,
    REFRESH_FAILURE_DIAGRAM,
    REFRESH_READ_DIAGRAM,
    REFRESH_DISABLE_DIAGRAM,
    ENABLING_EPOCH_PRE_DIAGRAM,
    ENABLING_EPOCH_POST_DIAGRAM,
    ENABLING_CANCEL_DIAGRAM,
    ENABLING_FAILURE_DIAGRAM,
))
ENABLING_CANCEL_TRANSITION = (
    "| `ENABLING` | `ctx.Done` before enable-frame emission | `IDLE` | cancel the "
    "queued frame, release the ownership gate, and clear the pending attempt; no "
    "native disable is emitted |"
)
ENABLE_ADMISSION_OPERATION = '| ENABLE | none (new claim) | succeeds iff FSM is `IDLE`, no cleanup or restart fence exists for the target, capability is `AVAILABLE`, and transport is connected; if any session is already `ENABLING`/`ACTIVE`/`REFRESHING` → `SESSION_BUSY`; an ownerless `IDLE` target under `TRANSPORT_DOWN` returns that exact unavailable result with no state transition or emission |'
IDLE_ENABLE_TRANSITION = '| `IDLE` | enable request, no owner or cleanup/fence, capability `AVAILABLE`, transport connected | `ENABLING` | emit enable frame after poll-quiesce |'
IDLE_ENABLE_REJECT_TRANSITION = '| `IDLE` | enable request while transport disconnected or capability is not `AVAILABLE` | `IDLE` | return the exact Gateway-supplied availability result and emit no enable frame |'
ENABLING_ACK_TRANSITION = '| `ENABLING` | successful enable ACK received after frame emission | `ACTIVE` | record the exact ACK, retain `(targetAddress, fresh gatewayCleanupAttemptID, currentTransportEpoch)` as process-local cleanup, start the 30s idle timer, arm reads for the current owner, publish `UNKNOWN`, and admit no second Enable; the ACK establishes the admitted operation outcome, not session settlement |'
ENABLING_AMBIGUOUS_FAILURE_TRANSITION = '| `ENABLING` | `ctx.Done` / NAK / timeout / CRC mismatch / bus-arbitration failure / any other non-ACK terminal outcome after enable-frame emission | `DISABLED` | record and return the exact native outcome, issue at most one defensive native disable after quiesce during the admitted lifecycle, release the owner on entry, retain `(targetAddress, fresh gatewayCleanupAttemptID, currentTransportEpoch)` as process-local cleanup, publish `UNKNOWN`, and admit no Enable; NAK and any defensive-disable ACK/NAK outcome do not prove settlement |'
ACTIVE_READ_TRANSITION = '| `ACTIVE` | successful read completes | `ACTIVE` | return the exact native result and reset the idle timer |'
ACTIVE_READ_FAILURE_TRANSITION = '| `ACTIVE` | read NAK / timeout / CRC mismatch / bus-arbitration failure / other non-disconnect failure | `ACTIVE` | return the exact native failure and do not reset the idle timer |'
ACTIVE_IDLE_TRANSITION = '| `ACTIVE` | 30s idle | `DISABLED` | emit disable once after quiesce, record the exact outcome, release the owner, retain process-local cleanup, publish `UNKNOWN`, and admit no Enable |'
ACTIVE_REFRESH_TRANSITION = '| `ACTIVE` | admitted request detects epoch advance | `REFRESHING` | ownership gate remains held; triggering request remains pending; subsequent live-monitor operations are busy |'
IDLE_DISCONNECT_TRANSITION = '| `IDLE` | transport disconnect, no owner or cleanup obligation | `IDLE` | change no session state and release no mutex; publish `TRANSPORT_DOWN` while disconnected; after reconnect require a new explicit Enable and perform no automatic B503 write |'
DISCONNECT_TRANSITION = '| `ENABLING` / `ACTIVE` / `REFRESHING` | transport disconnect | `DISABLED` | release the owner; if an Enable may have reached the wire or settlement is otherwise unproven, retain the target and attempt identity only as process-local cleanup, publish `UNKNOWN`, and perform no automatic reconnect write |'
DISABLED_DISCONNECT_TRANSITION = '| `DISABLED` | transport disconnect | `DISABLED` | change no session state and release no mutex; retain any existing cleanup obligation and its `UNKNOWN` fence; perform no automatic reconnect write |'
CLEANUP_SCOPED_TRANSPORT_DOWN_FORBIDDEN = (
    "- silent fallback to `UNKNOWN` from a knowable `TRANSPORT_DOWN` when no cleanup\n"
    "  obligation remains."
)
ENABLING_NAK_TRANSITION = ENABLING_AMBIGUOUS_FAILURE_TRANSITION
SESSION_TRANSITION_ROWS = (
    IDLE_ENABLE_TRANSITION,
    IDLE_ENABLE_REJECT_TRANSITION,
    ENABLING_ACK_TRANSITION,
    ENABLING_CANCEL_TRANSITION,
    ENABLING_AMBIGUOUS_FAILURE_TRANSITION,
    ENABLING_EPOCH_PRE_TRANSITION,
    ENABLING_EPOCH_POST_TRANSITION,
    ACTIVE_READ_TRANSITION,
    ACTIVE_READ_FAILURE_TRANSITION,
    EXPLICIT_DISABLE_CONFIRMED_TRANSITION,
    ACTIVE_IDLE_TRANSITION,
    ACTIVE_REFRESH_TRANSITION,
    REFRESH_READ_TRANSITION,
    REFRESH_DISABLE_TRANSITION,
    REFRESH_FAILURE_TRANSITION,
    UNCONFIRMED_CLEANUP_TRANSITION,
    ADMIN_DISABLED_TRANSITION,
    IDLE_DISCONNECT_TRANSITION,
    DISCONNECT_TRANSITION,
    DISABLED_DISCONNECT_TRANSITION,
    RESTART_TRANSITION,
)
ENABLING_DIRECT_IDLE_LOCK = (
    "on either direct `ENABLING → IDLE` path (cancellation or epoch advance before\n"
    "frame emission)"
)
FORBIDDEN_REFRESH_FAILURE_CONTRADICTIONS = (
    "REFRESHING --> IDLE: refresh failure releases gate",
    "on entry to `DISABLED` from a\nheld-owner state",
)
FORBIDDEN_ENABLING_EPOCH_CONTRADICTIONS = (
    "ENABLING --> REFRESHING: epoch advance",
    "| `ENABLING` | epoch advance detected | `REFRESHING` |",
)
RESTART_AUTOMATIC_WRITE_CONTRADICTION_PATTERNS = (
    re.compile(
        r"(?<!not )(?<!never )\bautomatically\s+"
        r"(?:emit|dispatch|send|issue|perform|enable|disable)\w*\b"
        r"[^.\n]{0,120}\bB503\b[^.\n]{0,80}\brestart\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\brestart\b[^.\n]{0,120}\bGateway\b[^.\n]{0,40}"
        r"(?<!not )(?<!never )\bautomatically\s+"
        r"(?:emit|dispatch|send|issue|perform|enable|disable)\w*\b"
        r"[^.\n]{0,80}\bB503\b",
        re.IGNORECASE,
    ),
)
SETTLEMENT_CONTRADICTION_PATTERNS = (
    re.compile(
        r"\b(?:a\s+)?(?:valid\s+)?disable\s+ACK\b[^.\n]{0,80}"
        r"\b(?:prove|proves|establish|establishes|confirm|confirms)\b"
        r"[^.\n]{0,40}\b(?:native\s+)?session\s+settlement\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\benable\s+NAK\b[^.\n]{0,100}"
        r"\b(?:prove|proves|establish|establishes|confirm|confirms)\b"
        r"[^.\n]{0,100}\b(?:admit|admits|allow|allows|permit|permits|re-admit|re-admits)\b"
        r"[^.\n]{0,20}\bEnable\b",
        re.IGNORECASE,
    ),
)
FORBIDDEN_SESSION_STATE_CLAUSES = (
    "`Refreshing` may accept live-monitor operations.",
    "`Disabled` may be reported with `owned:true`.",
    "After restart, separately operator-authorized target-specific recovery may emit one B503 disable.",
)
SESSION_STATE_CONTRADICTION_PATTERNS = (
    re.compile(
        r"(?:`Refreshing`\s+(?:(?:may|can|must|shall)\s+)?"
        r"(?:accept|allow|permit)s?\s+(?:new\s+|bus-facing\s+)?live-monitor operations?"
        r"|live-monitor operations?\s+(?:are|remain)\s+"
        r"(?:accepted|allowed|permitted)\s+(?:during|while)\s+`Refreshing`)",
        re.IGNORECASE,
    ),
    re.compile(
        r"`Disabled`\s+(?:(?:may|can|must|shall)\s+be\s+|is\s+)?"
        r"(?:reported|rendered|published|returned)\s+with\s+`owned:true`",
        re.IGNORECASE,
    ),
)
FORBIDDEN_ALL_READ_ONLY_MILESTONES = (
    (
        "`M2b_GATEWAY_GRAPHQL`",
        "`helianthus-ebusgateway`",
        "GraphQL read-only parity + `vaillantCapabilities.b503` signal",
    ),
    (
        "`M3_PORTAL`",
        "`helianthus-ebusgateway`",
        "Vaillant pane (errors / service / live-monitor tabs, read-only)",
    ),
)


class CheckError(ValueError):
    """The canonical B503 milestone text contradicts the v1 session boundary."""


class _VisibleContractSourceParser(HTMLParser):
    """Retain contract source that is visible, excluding inert HTML content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.parts: list[str] = []
        self._inert_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.casefold()
        hidden = _html_element_is_nonrendering(attrs) or (
            normalized == "dialog"
            and not any(name.casefold() == "open" for name, _ in attrs)
        )
        if self._inert_stack or normalized in NON_RENDERING_CONTAINERS or hidden:
            if normalized not in HTML_VOID_ELEMENTS:
                self._inert_stack.append(normalized)
            return

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        # Opening tags and attribute values are metadata, not rendered prose.
        return

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.casefold()
        if self._inert_stack:
            for index in range(len(self._inert_stack) - 1, -1, -1):
                if self._inert_stack[index] == normalized:
                    del self._inert_stack[index:]
                    return
            return

    def handle_data(self, data: str) -> None:
        if not self._inert_stack:
            self.parts.append(data)

    def handle_entityref(self, name: str) -> None:
        if not self._inert_stack:
            self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if not self._inert_stack:
            self.parts.append(f"&#{name};")


def _visible_contract_source(text: str) -> str:
    parser = _VisibleContractSourceParser()
    parser.feed(COMMONMARK_AUTOLINK.sub("", text))
    parser.close()
    return "".join(parser.parts)


def _html_element_is_nonrendering(attrs: list[tuple[str, str | None]]) -> bool:
    for name, value in attrs:
        if name.casefold() == "hidden":
            return True
        if name.casefold() != "style" or value is None:
            continue
        declarations = {}
        for declaration in value.split(";"):
            property_name, separator, property_value = declaration.partition(":")
            if separator:
                normalized_value = re.sub(
                    r"\s*!important\s*$", "", property_value.casefold()
                ).strip()
                declarations[property_name.strip().casefold()] = normalized_value
        if declarations.get("display") == "none" or declarations.get("visibility") == "hidden":
            return True
    return False


def _visible_prose_source(text: str) -> str:
    """Remove CommonMark fenced and indented code while preserving line boundaries."""
    lines = text.splitlines(keepends=True)
    for token in MARKDOWN.parse(text):
        if token.type not in {"fence", "code_block"} or token.map is None:
            continue
        for index in range(token.map[0], min(token.map[1], len(lines))):
            lines[index] = "\n" if lines[index].endswith("\n") else ""
    return "".join(lines)


def _rendered_contract_source(text: str) -> str:
    """Reconstruct rendered CommonMark text without link/image metadata or code."""
    parts: list[str] = []
    for token in MARKDOWN.parse(text):
        if token.type == "heading_open":
            parts.append("#" * int(token.tag[1:]) + " ")
        elif token.type == "list_item_open":
            parts.append("- ")
        elif token.type == "html_block":
            parts.extend((token.content, "\n"))
        elif token.type == "inline":
            for child in token.children or ():
                if child.type == "text":
                    parts.append(child.content)
                elif child.type == "code_inline":
                    parts.extend(("`", child.content, "`"))
                elif child.type in {"softbreak", "hardbreak"}:
                    parts.append("\n")
                elif child.type == "html_inline":
                    parts.append(child.content)
            parts.append("\n")
    return _visible_contract_source("".join(parts))


def _literal_anchor_values(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, tuple):
        for item in value:
            yield from _literal_anchor_values(item)


def _normalized_rendered(text: str) -> str:
    return " ".join(_rendered_contract_source(text).split())


def _require_declared_literal_anchors_visible(prose_text: str, rendered_text: str) -> None:
    """Require the checker's current literal anchors in reader-visible prose.

    This is bounded to literal contract fragments already declared by this
    checker. It does not attempt to prove arbitrary English semantics.
    """
    normalized_document = " ".join(rendered_text.split())
    for name, value in globals().items():
        if not name.isupper():
            continue
        for anchor in _literal_anchor_values(value):
            if len(anchor) < 32 or anchor not in prose_text:
                continue
            normalized_anchor = _normalized_rendered(anchor)
            if normalized_anchor and normalized_anchor not in normalized_document:
                raise CheckError(
                    f"declared contract anchor is not reader-visible: {name}"
                )


def _parse_table_row(line: str) -> tuple[str, ...] | None:
    if not line.startswith("|") or not line.endswith("|"):
        return None
    return tuple(cell.strip() for cell in line.strip("|").split("|"))


def _is_markdown_table_delimiter(
    row: tuple[str, ...] | None, column_count: int = len(MILESTONE_TABLE_HEADER)
) -> bool:
    return row is not None and len(row) == column_count and all(
        MARKDOWN_TABLE_DELIMITER_CELL.fullmatch(cell) is not None for cell in row
    )


def _section(text: str, start_marker: str, end_marker: str) -> str:
    try:
        start = text.index(start_marker)
        end = text.index(end_marker, start)
    except ValueError as exc:
        raise CheckError(
            f"missing canonical B503 section boundary: {start_marker!r}"
        ) from exc
    return text[start:end]


def _milestone_table(text: str) -> tuple[tuple[str, ...], ...]:
    """Return only the §14 companion milestone table rows, excluding prose."""
    lines = text.splitlines()
    try:
        heading_index = lines.index(MILESTONE_HEADING)
    except ValueError as exc:
        raise CheckError(f"missing B503 milestone heading: {MILESTONE_HEADING!r}") from exc

    header_index = heading_index + 2
    if header_index >= len(lines) or _parse_table_row(lines[header_index]) != MILESTONE_TABLE_HEADER:
        raise CheckError("missing §14 B503 milestone table header")
    separator_index = header_index + 1
    if separator_index >= len(lines) or not _is_markdown_table_delimiter(
        _parse_table_row(lines[separator_index])
    ):
        raise CheckError("missing §14 B503 milestone table separator")

    rows: list[tuple[str, ...]] = []
    for line in lines[separator_index + 1 :]:
        row = _parse_table_row(line)
        if row is None:
            break
        if len(row) != len(MILESTONE_TABLE_HEADER):
            raise CheckError(f"invalid §14 B503 milestone table row: {line!r}")
        rows.append(row)
    if not rows:
        raise CheckError("missing §14 B503 milestone table rows")
    return tuple(rows)


def _capability_truth_table_rows(text: str) -> tuple[tuple[str, ...], ...]:
    section = _section(
        text, CAPABILITY_TRUTH_TABLE_SECTION_START, CAPABILITY_TRUTH_TABLE_SECTION_END
    )
    lines = section.splitlines()
    try:
        header_index = next(
            index
            for index, line in enumerate(lines)
            if _parse_table_row(line) == CAPABILITY_TRUTH_TABLE_HEADER
        )
    except StopIteration as exc:
        raise CheckError("missing §12.5 capability truth-table header") from exc
    separator_index = header_index + 1
    if separator_index >= len(lines) or not _is_markdown_table_delimiter(
        _parse_table_row(lines[separator_index]), len(CAPABILITY_TRUTH_TABLE_HEADER)
    ):
        raise CheckError("missing §12.5 capability truth-table separator")

    rows: list[tuple[str, ...]] = []
    for line in lines[separator_index + 1 :]:
        row = _parse_table_row(line)
        if row is None:
            break
        if len(row) != len(CAPABILITY_TRUTH_TABLE_HEADER):
            raise CheckError(f"invalid §12.5 capability truth-table row: {line!r}")
        rows.append(row)
    if not rows:
        raise CheckError("missing §12.5 capability truth-table rows")
    return tuple(rows)


def _require_exact_row(rows: tuple[tuple[str, ...], ...], expected: tuple[str, ...]) -> None:
    matching_id_rows = [row for row in rows if row[0] == expected[0]]
    if matching_id_rows != [expected]:
        raise CheckError(f"missing exact §14 B503 milestone row: {expected!r}")


def validate_text(text: str) -> None:
    # Exact milestone fragments must be present in rendered documentation.
    # Raw text hidden in a CommonMark HTML comment cannot satisfy the gate.
    text = _visible_contract_source(text)
    prose_text = _visible_prose_source(text)
    _require_declared_literal_anchors_visible(
        prose_text, _rendered_contract_source(text)
    )
    status_section = _section(prose_text, STATUS_SECTION_START, STATUS_SECTION_END)
    if CURRENT_PUBLIC_SESSION_AUTHORITY not in status_section:
        raise CheckError("missing current public session authority in §1")

    session_section = _section(text, SESSION_SECTION_START, SESSION_SECTION_END)
    session_prose_section = _section(
        prose_text, SESSION_SECTION_START, SESSION_SECTION_END
    )
    session_contract_scope = _section(
        text, SESSION_SECTION_START, NORMALIZATION_SECTION_END
    )
    if SESSION_STATE_CONTRACT not in session_prose_section:
        raise CheckError("missing five-state B503 session contract in §6.1")
    if DISABLED_PUBLIC_MAPPING not in session_prose_section:
        raise CheckError("missing stable public Disabled mapping in §6")
    transition_section = _section(
        session_prose_section,
        SESSION_TRANSITION_TABLE_START,
        SESSION_TRANSITION_TABLE_END,
    )
    transition_lines = tuple(
        line for line in transition_section.splitlines() if line.startswith("|")
    )
    expected_transition_lines = (
        SESSION_TRANSITION_TABLE_HEADER,
        SESSION_TRANSITION_TABLE_SEPARATOR,
        *SESSION_TRANSITION_ROWS,
    )
    if transition_lines != expected_transition_lines:
        raise CheckError("§6.3 must contain the exact ordered finite B503 transition table")
    for fragment in (
        CONFIRMED_CLEANUP_DEFINITION,
        CONFIRMED_CLEANUP_DIAGRAM,
        UNCONFIRMED_CLEANUP_DIAGRAM,
        REFRESH_FAILURE_DIAGRAM,
        REFRESH_READ_DIAGRAM,
        REFRESH_DISABLE_DIAGRAM,
        REFRESH_READ_TRANSITION,
        REFRESH_DISABLE_TRANSITION,
        REFRESH_DISABLE_UNCONFIRMED_TRANSITION,
        UNCONFIRMED_CLEANUP_TRANSITION,
        CONFIRMED_CLEANUP_TRANSITION,
        EXPLICIT_DISABLE_CONFIRMED_TRANSITION,
        EXPLICIT_DISABLE_UNCONFIRMED_TRANSITION,
        REFRESH_FAILURE_TRANSITION,
        HELD_OWNER_DISABLED_RELEASE,
        ENABLE_ADMISSION_OPERATION,
        ENABLING_CANCEL_DIAGRAM,
        ENABLING_FAILURE_DIAGRAM,
        ENABLING_ACK_TRANSITION,
        ENABLING_CANCEL_TRANSITION,
        ENABLING_AMBIGUOUS_FAILURE_TRANSITION,
        ENABLING_NAK_TRANSITION,
        ENABLING_DIRECT_IDLE_LOCK,
        DISCONNECT_TRANSITION,
        RESTART_TRANSITION,
    ):
        required_scope = (
            session_section
            if fragment in CODE_REQUIRED_FRAGMENTS
            else session_prose_section
        )
        if fragment not in required_scope:
            raise CheckError(
                f"missing coherent B503 Refreshing failure contract in §6.1: {fragment!r}"
            )
    for fragment in FORBIDDEN_REFRESH_FAILURE_CONTRADICTIONS:
        if fragment in session_section:
            raise CheckError(
                f"forbidden B503 Refreshing failure contradiction in §6.1: {fragment!r}"
            )
    for fragment in FORBIDDEN_SESSION_STATE_CLAUSES:
        if fragment in session_contract_scope:
            raise CheckError(
                f"forbidden §§6-8 B503 session-state contradiction: {fragment!r}"
            )
    for pattern in SESSION_STATE_CONTRADICTION_PATTERNS:
        match = pattern.search(session_contract_scope)
        if match is not None:
            raise CheckError(
                "forbidden declarative §§6-8 B503 session-state contradiction: "
                f"{match.group(0)!r}"
            )
    for pattern in RESTART_AUTOMATIC_WRITE_CONTRADICTION_PATTERNS:
        match = pattern.search(session_contract_scope)
        if match is not None:
            raise CheckError(
                "forbidden automatic B503 restart write contradiction in §§6-8: "
                f"{match.group(0)!r}"
            )
    for pattern in SETTLEMENT_CONTRADICTION_PATTERNS:
        match = pattern.search(session_contract_scope)
        if match is not None:
            raise CheckError(
                "forbidden ACK/NAK session-settlement contradiction in §§6-8: "
                f"{match.group(0)!r}"
            )
    for fragment in (
        ENABLING_EPOCH_PRE_DIAGRAM,
        ENABLING_EPOCH_POST_DIAGRAM,
        ENABLING_EPOCH_PRE_OPERATION,
        ENABLING_EPOCH_POST_OPERATION,
        ENABLING_EPOCH_PRE_TRANSITION,
        ENABLING_EPOCH_POST_TRANSITION,
    ):
        required_scope = (
            session_section
            if fragment in CODE_REQUIRED_FRAGMENTS
            else session_prose_section
        )
        if fragment not in required_scope:
            raise CheckError(
                f"missing coherent ENABLING epoch-advance contract in §6: {fragment!r}"
            )
    for fragment in FORBIDDEN_ENABLING_EPOCH_CONTRADICTIONS:
        if fragment in session_section:
            raise CheckError(
                f"forbidden ENABLING epoch-advance contradiction in §6: {fragment!r}"
            )
    if REFRESH_OWNER_REBINDING not in session_prose_section:
        raise CheckError("missing atomic owner-key epoch rebinding contract in §6.2")

    refreshing_public_section = _section(
        prose_text, REFRESHING_PUBLIC_SECTION_START, REFRESHING_PUBLIC_SECTION_END
    )
    for fragment in (
        ENABLING_CLEANUP_CONTRACT,
        REFRESHING_CLEANUP_CONTRACT,
        REFRESHING_UNKNOWN_STRIP_CONTRACT,
        ACTIVE_UNKNOWN_OWNER_CONTRACT,
    ):
        if fragment not in refreshing_public_section:
            raise CheckError(
                f"missing public Refreshing consumer contract in §7.1.1: {fragment!r}"
            )

    refresh_section = _section(prose_text, REFRESH_SECTION_START, REFRESH_SECTION_END)
    if REFRESH_SUCCESS_CONTINUATION not in refresh_section:
        raise CheckError("missing authenticated Refreshing continuation contract in §7.3")
    if REFRESH_FAILURE_CAPABILITY_PRECEDENCE not in refresh_section:
        raise CheckError("missing cleanup-aware refresh failure capability precedence")
    release_section = _section(prose_text, RELEASE_SECTION_START, RELEASE_SECTION_END)
    for fragment in (
        OWNER_CONDITIONAL_MUTEX_SCOPE,
        UNCONFIRMED_CLEANUP_OBLIGATION,
        GATEWAY_CLEANUP_ATTEMPT_ID,
        DISCONNECT_CLEANUP_OBLIGATION,
        DISCONNECT_CLEANUP_MUTEX_INDEPENDENCE,
        RESTART_RELEASE_CONTRACT,
    ):
        if fragment not in release_section:
            raise CheckError("missing process-local disconnect cleanup obligation in §7.4")
    reconnect_section = _section(prose_text, RECONNECT_SECTION_START, RECONNECT_SECTION_END)
    if NO_AUTO_RESUME_RECONSTRUCTION not in reconnect_section:
        raise CheckError("missing no-reconstruction boundary in §7.5")
    if REFRESHING_DISCONNECT_FENCE not in reconnect_section:
        raise CheckError("missing Refreshing disconnect fence in §7.5")
    if RESTART_CLEANUP_FENCE not in reconnect_section:
        raise CheckError("missing bounded per-target restart cleanup fence in §7.5")
    idle_timeout_section = _section(
        prose_text, IDLE_TIMEOUT_SECTION_START, IDLE_TIMEOUT_SECTION_END
    )
    if IDLE_TIMEOUT_ACK_CONTRACT not in idle_timeout_section:
        raise CheckError("missing valid-ACK idle-timeout cleanup contract in §7.6")
    normalization_section = _section(
        prose_text, NORMALIZATION_SECTION_START, NORMALIZATION_SECTION_END
    )
    if NORMALIZED_REFRESH_DISABLE_CONTRACT not in normalization_section:
        raise CheckError("missing fail-closed refreshed-DISABLE normalization in §8")

    rows = _milestone_table(prose_text)
    for expected in (M2B_GRAPHQL, M3_PORTAL):
        _require_exact_row(rows, expected)
    for fragment in FORBIDDEN_ALL_READ_ONLY_MILESTONES:
        if fragment in rows:
            raise CheckError(f"forbidden all-read-only B503 milestone: {fragment!r}")
    install_write_section = _section(
        prose_text, INSTALL_WRITE_SECTION_START, INSTALL_WRITE_SECTION_END
    )
    if install_write_section != INSTALL_WRITE_SECTION:
        raise CheckError(
            "§9 B503 installation-write classification, prohibition, enforcement, "
            "and future-plan boundary must remain exact"
        )

    truth_rows = _capability_truth_table_rows(prose_text)
    if truth_rows != CAPABILITY_TRUTH_ROWS:
        raise CheckError(
            "§12.5 capability truth table must contain the exact ordered eight-row set; "
            f"got {truth_rows!r}"
        )
    truth_prose = _section(
        prose_text,
        CAPABILITY_TRUTH_TABLE_SECTION_START,
        CAPABILITY_TRUTH_TABLE_SECTION_END,
    )
    if CURRENT_CAPABILITY_TABLE_AUTHORITY not in truth_prose:
        raise CheckError("missing current public authority for all eight §12.5 rows")
    for fragment in FORBIDDEN_PLAN_CONFLICT_AUTHORITY:
        if fragment in text:
            raise CheckError(f"forbidden archived-plan conflict authority: {fragment!r}")
    if CLEANUP_SCOPED_TRANSPORT_DOWN_FORBIDDEN not in prose_text:
        raise CheckError("missing cleanup-scoped TRANSPORT_DOWN/UNKNOWN precedence")


def main() -> int:
    try:
        validate_text(DOC.read_text(encoding="utf-8"))
    except (OSError, CheckError) as exc:
        print(exc, file=sys.stderr)
        return 1
    print("Vaillant B503 milestone contract gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
