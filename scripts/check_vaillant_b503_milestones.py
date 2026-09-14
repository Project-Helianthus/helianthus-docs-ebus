#!/usr/bin/env python3
"""Validate the bounded B503 live-monitor milestone contract."""
from __future__ import annotations

import pathlib
import re
import sys


DOC = pathlib.Path("protocols/vaillant/ebus-vaillant-B503.md")
STATUS_SECTION_START = "## 1. Status"
STATUS_SECTION_END = "## 2. Wire Shape"
MILESTONE_HEADING = "## 14. Companion Links (downstream code milestones)"
MILESTONE_TABLE_HEADER = ("Milestone", "Repo", "Artefact")
MARKDOWN_TABLE_DELIMITER_CELL = re.compile(r"^:?-{3,}:?$")
SESSION_SECTION_START = "## 6. Live-Monitor Session"
SESSION_SECTION_END = "## 7. Gateway Operational Contract"
REFRESHING_PUBLIC_SECTION_START = "#### 7.1.1 Refreshing session state (public)"
REFRESHING_PUBLIC_SECTION_END = "### 7.2 Quiesce timing bounds (normative)"
REFRESH_SECTION_START = "### 7.3 Retry and refresh"
REFRESH_SECTION_END = "### 7.4 Ownership release"
RELEASE_SECTION_START = "### 7.4 Ownership release"
RELEASE_SECTION_END = "### 7.5 Reconnect handling"
RECONNECT_SECTION_START = "### 7.5 Reconnect handling"
RECONNECT_SECTION_END = "### 7.6 30s idle-timeout semantics"
IDLE_TIMEOUT_SECTION_START = "### 7.6 30s idle-timeout semantics"
IDLE_TIMEOUT_SECTION_END = "### 7.7 Concurrency with B524"
NORMALIZATION_SECTION_START = "## 8. Public Normalization Rules"
NORMALIZATION_SECTION_END = "## 9. Install-Writes Non-Exposure (v1 invariant)"
INSTALL_WRITE_SECTION_START = "## 9. Install-Writes Non-Exposure (v1 invariant)"
INSTALL_WRITE_SECTION_END = "## 10. F.xxx Decimal Caveat (LOCAL_CAPTURE only)"
CAPABILITY_TRUTH_TABLE_SECTION_START = "### 12.5 Capability-signal 8-state truth table (mirror of AD18) <a id=\"capability-truth-table\"></a>"
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
REFRESHING_CAPABILITY_TRUTH_ROW = (
    "7",
    "held-session epoch refresh; session status `Refreshing`",
    "`UNKNOWN` (temporary; not sticky `AVAILABLE`)",
    "triggering READ or current-owner DISABLE remains pending and is dispatched "
    "exactly once only after successful rebind; READ returns to `Active`, DISABLE "
    "releases ownership and completes cleanup to `Idle` only after a valid ACK, and subsequent live-monitor operations are "
    "`SESSION_BUSY`; only `vaillantCapabilities` and `vaillantLiveMonitorSession` "
    "status queries remain admitted, with no B503 card, tabs, bus-facing reads, or "
    "actions until capability returns `AVAILABLE`",
)
DISPATCH_FAILURE_TRUTH_ROW = (
    "6",
    "timeout/NAK/CRC during dispatch",
    "`UPSTREAM_RPC_FAILED` to caller; capability stays last-known only when the "
    "operation creates no cleanup obligation; any disable or refresh failure that "
    "retains cleanup publishes `UNKNOWN` per §6–§8",
    "cleanup-bearing outcomes retain the Gateway-owned attempt identity, admit no "
    "Enable, and follow the bounded later-epoch cleanup rule",
)
CURRENT_PUBLIC_SESSION_AUTHORITY = (
    "**Current public session authority.** The five-state public session contract in\n"
    "§6–§8 is governed by this document's current doc-gate revision (docs-ebus#523)\n"
    "and supersedes prior public session-presentation vocabulary here. The\n"
    "amendment-1 plan SHA remains traceability evidence for its original §12 scope;\n"
    "it is not authority to retain a superseded public FSM vocabulary. This current\n"
    "contract does not add a compatibility state, route, or fallback.\n\n"
    "Changes to plan-owned selectors, wire shape, or invoke-safety classification\n"
    "require a new plan revision and corresponding doc-gate PR. A correction limited\n"
    "to the current public session contract requires its own doc-gate PR and current\n"
    "source evidence; it does not claim or create execution-plan state."
)
SESSION_STATE_CONTRACT = (
    "five stable states: `Idle`, `Enabling`, `Active`, `Refreshing`, and `Disabled`.\n"
    "`Refreshing` means an epoch refresh holds the ownership gate. The already\n"
    "admitted triggering request remains pending; subsequent bus-facing live-monitor\n"
    "operations are busy. Refresh success dispatches a triggering read exactly once\n"
    "and returns `Active`, or dispatches a triggering current-owner disable exactly\n"
    "once. Only a valid disable ACK completes owner cleanup to `Idle`; any other\n"
    "disable outcome retains fail-closed cleanup. Refresh failure releases the gate,\n"
    "enters internal `DISABLED`, retains a Gateway cleanup obligation, and returns\n"
    "the exact Gateway-supplied failure to that request; its public session\n"
    "observation is `Idle` with `owned:false` and unavailable capability.\n"
    "`Disabled` is never reported with `owned:true`."
)
DISABLED_PUBLIC_MAPPING = (
    "**Stable public `Disabled` mapping:** `Disabled` with `owned:false` represents\n"
    "only an explicit operator or configuration disable. Enable failure, the 30s\n"
    "idle timeout, transport disconnect, and gateway restart may traverse the\n"
    "internal cleanup path through `DISABLED`, but their stable public session\n"
    "observation is `Idle` with `owned:false`. While a process-local cleanup\n"
    "obligation remains, capability is `UNKNOWN` and Enable is unavailable; `Idle`\n"
    "does not make the internal slot re-claimable. `Disabled` is never reported with\n"
    "`owned:true`."
)
REFRESHING_CLEANUP_CONTRACT = (
    "When a locally token-owning consumer leaves a target or navigates away while\n"
    "its session is `Refreshing`, it MUST queue that target/token disable without\n"
    "invoking the busy operation. After successful refresh reaches `Active`, it\n"
    "dispatches the queued disable; after refresh failure releases ownership and\n"
    "presents `Idle`, it clears the browser queued pair without a client disable\n"
    "while Gateway retains the process-local cleanup obligation. If the triggering request was itself the\n"
    "current-owner DISABLE, that single disable is the only client dispatch. A valid\n"
    "disable ACK completes `Disabled` cleanup to `Idle`; any other outcome returns\n"
    "exactly and leaves the process-local defensive cleanup with Gateway. In both\n"
    "cases the consumer clears the queued pair without issuing a second disable."
)
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
    "completion. No B503 card, tabs, bus-facing reads, or actions are admitted until\n"
    "capability returns `AVAILABLE`."
)
REFRESH_SUCCESS_CONTINUATION = (
    "On refresh success for a surviving authenticated current-owner handle, the\n"
    "  old epoch-N key authorizes only that refresh. Gateway atomically installs the\n"
    "  returned current `transport_key` for epoch N+1 with the same issuer token and\n"
    "  target before returning to `Active`; every epoch-N completion is fenced. This\n"
    "  is continuation, not reconstruction or auto-resume. The already-admitted\n"
    "  triggering request remains pending during refresh; after successful rebind,\n"
    "  Gateway dispatches that request's native operation exactly once using the\n"
    "  rebound key and returns its exact outcome. A triggering READ retains the\n"
    "  owner in `Active`; a triggering current-owner DISABLE emits its disable after\n"
    "  quiesce and enters `Disabled`. A valid disable ACK completes owner cleanup to\n"
    "  `Idle`. Any other disable outcome returns exactly, releases the owner, retains\n"
    "  a process-local defensive-cleanup obligation, publishes capability `UNKNOWN`,\n"
    "  and admits no Enable; it does not enter `Idle`. ENABLE is\n"
    "  never a refresh trigger. This one dispatch consumes the request's only retry\n"
    "  budget. Every subsequent bus-facing live-monitor operation during refresh\n"
    "  returns `SESSION_BUSY`. On refresh failure, no rebound key is installed:\n"
    "  release the ownership gate, retain a fresh Gateway-owned process-local cleanup\n"
    "  obligation in internal `DISABLED`, present public session `Idle` with\n"
    "  `owned:false`, and return the exact Gateway-supplied failure to the triggering\n"
    "  request without dispatching its native operation. Capability remains that\n"
    "  exact unavailable outcome and no Enable is admitted until cleanup succeeds."
)
REFRESH_OWNER_REBINDING = (
    "On an `ACTIVE` epoch advance from N to N+1, the old `session_key` authorizes\n"
    "only the one bounded refresh attempt. A successful refresh returns the current\n"
    "`transport_key` for epoch N+1. Gateway MUST atomically replace the owner key\n"
    "with `(transport_key[N+1], same issuer_token)` while retaining the same target,\n"
    "then dispatch the admitted triggering operation exactly once. Completions and\n"
    "control requests still bound to epoch N are stale and MUST NOT satisfy, disable,\n"
    "extend, or mutate the rebound session. If refresh fails, no rebound key is\n"
    "installed; Gateway releases client ownership, retains a fresh Gateway-owned\n"
    "process-local cleanup obligation in internal `DISABLED`, presents public\n"
    "session `Idle` with `owned:false`, preserves the exact unavailable capability,\n"
    "and admits no Enable until cleanup succeeds."
)
NO_AUTO_RESUME_RECONSTRUCTION = (
    "Gateway MUST NOT reconstruct or auto-resume a session after restart, a lost\n"
    "  owner handle, or an absent/invalid current issuer token; each requires an\n"
    "  explicit new client Enable. After restart that Enable is admitted only after\n"
    "  the bounded per-target startup cleanup succeeds and capability is\n"
    "  `AVAILABLE`. The surviving authenticated current-owner refresh path in §7.3\n"
    "  is the only continuation allowed across an epoch advance."
)
REFRESHING_DISCONNECT_FENCE = (
    "A terminal transport disconnect follows §7.4: it releases the owner and does\n"
    "  not enter `Refreshing` on reconnect. If no defensive cleanup is pending, the\n"
    "  later reconnect reaches `Idle` and requires a new explicit client Enable.\n"
    "- If defensive cleanup is pending, the transport layer MUST NOT publish the new\n"
    "  epoch as B503-usable or admit any Enable. After quiesce on the current\n"
    "  transport epoch, Gateway issues exactly one target-specific defensive disable\n"
    "  for that reconnect attempt and records its exact native outcome. A confirmed\n"
    "  terminal cleanup clears the obligation, publishes the epoch as usable, and\n"
    "  reaches `Idle`; an ambiguous or transport failure retains the obligation,\n"
    "  leaves B503 `TRANSPORT_DOWN` or `UNKNOWN` as applicable, and admits no Enable.\n"
    "  There is no retry within the same transport epoch; a later transport lifecycle\n"
    "  attempt may execute one bounded cleanup again before publication."
)
DISCONNECT_CLEANUP_OBLIGATION = (
    "- On transport disconnect, the gateway MUST transition the FSM to\n"
    "  `DISABLED` and — if an owner was held — release `liveMonitorMu`. If an enable\n"
    "  may have reached the wire and no disable has a confirmed terminal outcome,\n"
    "  Gateway retains `(targetAddress, gatewayCleanupAttemptID, priorTransportEpoch)`\n"
    "  only as a process-local defensive-cleanup obligation across transport\n"
    "  reconnect. It carries no issuer token, owner authority, session continuation,\n"
    "  or operation eligibility and does not survive gateway process restart."
)
DISCONNECT_CLEANUP_MUTEX_INDEPENDENCE = (
    "- If the FSM was already `IDLE` or `DISABLED` at disconnect/restart time,\n"
    "  these events are no-ops with respect to the mutex; no release is\n"
    "  attempted. A pre-existing defensive-cleanup obligation remains independent\n"
    "  of that mutex rule."
)
CONFIRMED_CLEANUP_DEFINITION = (
    "A **confirmed cleanup success** means a valid native disable ACK. A NAK,\n"
    "timeout, CRC mismatch, bus-arbitration failure, disconnect, or any other outcome\n"
    "without that ACK does not prove that a possibly active device session stopped.\n"
    "It therefore retains the applicable process-local defensive-cleanup obligation\n"
    "and never makes the session slot re-claimable."
)
UNCONFIRMED_CLEANUP_OBLIGATION = (
    "- Every native disable used for explicit, idle-timeout, refreshed, or defensive\n"
    "  cleanup clears its obligation only after a valid native\n"
    "  disable ACK. A NAK, timeout, CRC mismatch, bus-arbitration failure,\n"
    "  disconnect, or any other outcome without that ACK retains the target plus a\n"
    "  fresh Gateway-owned `gatewayCleanupAttemptID` and the attempted transport\n"
    "  epoch as process-local,\n"
    "  operation-ineligible cleanup state. Gateway publishes capability `UNKNOWN`,\n"
    "  admits no Enable, and performs no retry in that transport epoch. The internal\n"
    "  FSM remains `DISABLED`; a later transport epoch may attempt one bounded\n"
    "  target-specific cleanup under §7.5."
)
GATEWAY_CLEANUP_ATTEMPT_ID = (
    "- Gateway allocates `gatewayCleanupAttemptID` when the cleanup obligation is\n"
    "  created and never reuses it. This opaque ID is internal to Gateway; it is not\n"
    "  the browser-local `localEnableAttemptID`, is not supplied by a caller, and\n"
    "  confers no owner or operation authority."
)
CONFIRMED_CLEANUP_DIAGRAM = (
    "DISABLED --> IDLE: enable NAK or valid disable ACK"
)
EXPLICIT_DISABLE_CONFIRMED_TRANSITION = (
    "| `ACTIVE` | explicit disable; valid disable ACK | `DISABLED` | emit disable "
    "frame exactly once after quiesce, return success, release the owner, clear "
    "cleanup, and complete to `IDLE` |"
)
EXPLICIT_DISABLE_UNCONFIRMED_TRANSITION = (
    "| `ACTIVE` | explicit disable; NAK / timeout / CRC mismatch / "
    "bus-arbitration failure / disconnect / any other outcome without a valid "
    "disable ACK | `DISABLED` | emit disable frame exactly once after quiesce, "
    "return its exact outcome, release the owner, retain `(targetAddress, fresh "
    "gatewayCleanupAttemptID, currentTransportEpoch)` as the process-local §7.4 "
    "cleanup obligation, and do not enter `IDLE` |"
)
RESTART_TRANSITION = (
    "| any | gateway restart | `DISABLED` | release any owner and destroy every "
    "caller handle; no session state is reconstructed, and §7.5 bounded restart "
    "cleanup must succeed before any qualified B503 target becomes `AVAILABLE` |"
)
RESTART_RELEASE_CONTRACT = (
    "- On gateway restart, the gateway MUST transition the FSM to `DISABLED`\n"
    "  and — if an owner was held — release `liveMonitorMu`. No session or cleanup\n"
    "  tuple persists across restart; the bounded per-target startup cleanup in §7.5\n"
    "  replaces persistence and MUST finish before B503 availability is published."
)
RESTART_CLEANUP_FENCE = (
    "- After every Gateway process restart, enumerate the finite registry-qualified\n"
    "  B503 targets and, before publishing any one of them as `AVAILABLE`, issue\n"
    "  exactly one target-specific defensive disable for that target after quiesce.\n"
    "  Record the native outcome. A valid disable ACK permits that target's normal\n"
    "  availability evaluation; any other outcome leaves it `UNKNOWN`, admits no\n"
    "  Enable, and performs no retry in the same transport epoch. A later transport\n"
    "  epoch may execute one bounded cleanup again. This startup fence reconstructs\n"
    "  no caller handle or session and requires no persisted cleanup tuple."
)
IDLE_TIMEOUT_ACK_CONTRACT = (
    "- Idle disable transitions the **internal** FSM from `ACTIVE` to `DISABLED`.\n"
    "  A valid disable ACK clears cleanup, returns the internal FSM to `IDLE`, and\n"
    "  keeps the **public capability signal** (§11) `AVAILABLE`; a later explicit\n"
    "  request may then re-enter `ENABLING`. A NAK, timeout, CRC mismatch,\n"
    "  bus-arbitration failure, disconnect, or any other outcome without that ACK\n"
    "  follows §7.4: retain the process-local cleanup obligation, publish capability\n"
    "  `UNKNOWN`, admit no Enable, and perform no same-epoch retry. Idle auto-disable\n"
    "  MUST NOT be reported to consumers as `NOT_SUPPORTED`, which is reserved for\n"
    "  \"device class does not implement B503\" (§11)."
)
NORMALIZED_REFRESH_DISABLE_CONTRACT = (
    "2. **Refresh once.** On epoch advance with a held session, Gateway transitions\n"
    "   to `Refreshing` and makes exactly one refresh attempt. The already-admitted\n"
    "   triggering READ or current-owner DISABLE remains pending and is dispatched\n"
    "   exactly once only after successful rebind. READ returns Gateway to `Active`;\n"
    "   DISABLE releases ownership and completes the normal `Disabled` cleanup to\n"
    "   `Idle` only after a valid disable ACK. Any other disable outcome retains the\n"
    "   §7.4 process-local cleanup obligation, publishes capability `UNKNOWN`, admits\n"
    "   no Enable, and returns its exact outcome. Subsequent bus-facing live-monitor\n"
    "   operations are `SESSION_BUSY` during refresh. Refresh failure likewise\n"
    "   releases client ownership but retains Gateway cleanup in internal `DISABLED`,\n"
    "   preserves the exact unavailable capability, and admits no Enable."
)
REFRESH_FAILURE_DIAGRAM = (
    "REFRESHING --> DISABLED: refresh failure retains cleanup"
)
REFRESH_READ_DIAGRAM = "REFRESHING --> ACTIVE: refresh succeeds; triggering READ once"
REFRESH_DISABLE_DIAGRAM = (
    "REFRESHING --> DISABLED: refresh succeeds; triggering DISABLE once"
)
UNCONFIRMED_CLEANUP_DIAGRAM = (
    "DISABLED --> DISABLED: cleanup lacks valid disable ACK; fail closed"
)
REFRESH_READ_TRANSITION = (
    "| `REFRESHING` | refresh succeeds for triggering READ | `ACTIVE` | atomically "
    "rebind the owner from epoch N to the returned current `transport_key` at N+1, "
    "retaining the same issuer token and target; fence every epoch-N completion; "
    "dispatch READ exactly once using the rebound key, return its outcome, and "
    "retain the owner |"
)
REFRESH_DISABLE_TRANSITION = (
    "| `REFRESHING` | refresh succeeds for triggering current-owner DISABLE; valid "
    "disable ACK | `DISABLED` | atomically rebind to the N+1 key, fence every epoch-N "
    "completion, emit disable exactly once after quiesce using the rebound key, "
    "return success, and complete owner cleanup to `IDLE` |"
)
REFRESH_DISABLE_UNCONFIRMED_TRANSITION = (
    "| `REFRESHING` | refresh succeeds for triggering current-owner DISABLE; NAK / "
    "timeout / CRC mismatch / bus-arbitration failure / disconnect / any other "
    "outcome without a valid disable ACK | `DISABLED` | atomically rebind to the N+1 "
    "key, fence every epoch-N completion, emit disable exactly once after quiesce "
    "using the rebound key, return its exact outcome, release the owner, and retain "
    "`(targetAddress, fresh gatewayCleanupAttemptID, transportEpoch[N+1])` only as the "
    "process-local §7.4 defensive-cleanup obligation; do not enter `IDLE` |"
)
UNCONFIRMED_CLEANUP_TRANSITION = (
    "| `DISABLED` | defensive disable has no valid ACK while transport remains "
    "connected | `DISABLED` | retain the process-local §7.4 defensive-cleanup "
    "obligation, publish capability `UNKNOWN`, admit no Enable, and perform no "
    "same-epoch retry; only a later transport epoch may attempt one bounded cleanup "
    "under §7.5 |"
)
CONFIRMED_CLEANUP_TRANSITION = (
    "| `DISABLED` | enable NAK proves no device session, or valid disable ACK "
    "confirms cleanup success | `IDLE` | clear any defensive-cleanup obligation; "
    "session may be re-claimed by any client only when capability is `AVAILABLE` |"
)
REFRESH_FAILURE_TRANSITION = (
    "| `REFRESHING` | refresh failure | `DISABLED` | release ownership gate, return "
    "the exact Gateway-supplied failure outcome to the triggering request without "
    "dispatching its native operation, and retain `(targetAddress, fresh "
    "gatewayCleanupAttemptID, attemptedTransportEpoch)` as the process-local §7.4 "
    "cleanup obligation; public session is `Idle` with `owned:false`, capability "
    "remains the exact unavailable outcome, and no Enable is admitted |"
)
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
ENABLING_EPOCH_POST_OPERATION = (
    "| Epoch advance while `ENABLING`, after enable-frame emission | pending "
    "attempt identity and target remain Gateway-owned for cleanup only | → "
    "`DISABLED`; fence every stale completion, issue exactly one defensive disable "
    "after quiesce on the current transport epoch, and record its exact cleanup "
    "outcome as native evidence; a valid disable ACK completes cleanup to `IDLE`, "
    "while any other outcome retains the §7.4 process-local obligation and remains "
    "fail-closed in `DISABLED`; no automatic retry or active owner survives |"
)
ENABLING_EPOCH_PRE_TRANSITION = (
    "| `ENABLING` | epoch advance detected before enable-frame emission | `IDLE` | "
    "cancel the queued frame, release ownership, and discard every stale completion "
    "or failure outcome from that enable attempt; explicit new Enable required |"
)
ENABLING_EPOCH_POST_TRANSITION = (
    "| `ENABLING` | epoch advance detected after enable-frame emission | "
    "`DISABLED` | fence every stale completion, issue exactly one defensive disable "
    "after quiesce on the current transport epoch, and record its exact cleanup "
    "outcome as native evidence; a valid disable ACK completes cleanup to `IDLE`, "
    "while any other outcome retains the §7.4 process-local obligation and remains "
    "fail-closed in `DISABLED`; no automatic retry or active owner survives |"
)
ENABLING_CANCEL_DIAGRAM = "ENABLING --> IDLE: canceled before enable frame emission"
ENABLING_FAILURE_DIAGRAM = (
    "ENABLING --> DISABLED: terminal enable failure after emission"
)
ENABLING_CANCEL_TRANSITION = (
    "| `ENABLING` | `ctx.Done` before enable-frame emission | `IDLE` | cancel the "
    "queued frame, release the ownership gate, and clear the pending attempt; no "
    "native disable is emitted |"
)
ENABLING_AMBIGUOUS_FAILURE_TRANSITION = (
    "| `ENABLING` | `ctx.Done` after enable-frame emission / ACK timeout / CRC "
    "mismatch / bus-arbitration timeout / any other ambiguous terminal failure | "
    "`DISABLED` | emit exactly one defensive native disable after quiesce, or queue "
    "it under §7.4 if transport disconnects first; release the owner on entry and "
    "complete cleanup to `IDLE` only after a valid disable ACK confirms cleanup "
    "success; return the original exact failure outcome |"
)
DISCONNECT_TRANSITION = (
    "| any | transport disconnect | `DISABLED` | release any owner; if an enable "
    "may have reached the wire and no disable has a confirmed terminal outcome, "
    "retain the target and attempt only as the process-local §7.4 "
    "defensive-cleanup obligation |"
)
ENABLING_NAK_TRANSITION = (
    "| `ENABLING` | NAK | `DISABLED` | release the owner on entry and complete "
    "cleanup to `IDLE` without a defensive disable because NAK proves the enable "
    "was rejected |"
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
FORBIDDEN_SESSION_STATE_CLAUSES = (
    "`Refreshing` may accept live-monitor operations.",
    "`Disabled` may be reported with `owned:true`.",
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
    status_section = _section(text, STATUS_SECTION_START, STATUS_SECTION_END)
    if CURRENT_PUBLIC_SESSION_AUTHORITY not in status_section:
        raise CheckError("missing current public session authority in §1")

    session_section = _section(text, SESSION_SECTION_START, SESSION_SECTION_END)
    if SESSION_STATE_CONTRACT not in session_section:
        raise CheckError("missing five-state B503 session contract in §6.1")
    if DISABLED_PUBLIC_MAPPING not in session_section:
        raise CheckError("missing stable public Disabled mapping in §6")
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
        ENABLING_CANCEL_DIAGRAM,
        ENABLING_FAILURE_DIAGRAM,
        ENABLING_CANCEL_TRANSITION,
        ENABLING_AMBIGUOUS_FAILURE_TRANSITION,
        ENABLING_NAK_TRANSITION,
        ENABLING_DIRECT_IDLE_LOCK,
        DISCONNECT_TRANSITION,
        RESTART_TRANSITION,
    ):
        if fragment not in session_section:
            raise CheckError(
                f"missing coherent B503 Refreshing failure contract in §6.1: {fragment!r}"
            )
    for fragment in FORBIDDEN_REFRESH_FAILURE_CONTRADICTIONS:
        if fragment in session_section:
            raise CheckError(
                f"forbidden B503 Refreshing failure contradiction in §6.1: {fragment!r}"
            )
    for fragment in FORBIDDEN_SESSION_STATE_CLAUSES:
        if fragment in session_section:
            raise CheckError(f"forbidden §6 B503 session-state contradiction: {fragment!r}")
    for pattern in SESSION_STATE_CONTRADICTION_PATTERNS:
        match = pattern.search(session_section)
        if match is not None:
            raise CheckError(
                "forbidden declarative §6 B503 session-state contradiction: "
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
        if fragment not in session_section:
            raise CheckError(
                f"missing coherent ENABLING epoch-advance contract in §6: {fragment!r}"
            )
    for fragment in FORBIDDEN_ENABLING_EPOCH_CONTRADICTIONS:
        if fragment in session_section:
            raise CheckError(
                f"forbidden ENABLING epoch-advance contradiction in §6: {fragment!r}"
            )
    if REFRESH_OWNER_REBINDING not in session_section:
        raise CheckError("missing atomic owner-key epoch rebinding contract in §6.2")

    refreshing_public_section = _section(
        text, REFRESHING_PUBLIC_SECTION_START, REFRESHING_PUBLIC_SECTION_END
    )
    for fragment in (
        ENABLING_CLEANUP_CONTRACT,
        REFRESHING_CLEANUP_CONTRACT,
        REFRESHING_UNKNOWN_STRIP_CONTRACT,
    ):
        if fragment not in refreshing_public_section:
            raise CheckError(
                f"missing public Refreshing consumer contract in §7.1.1: {fragment!r}"
            )

    refresh_section = _section(text, REFRESH_SECTION_START, REFRESH_SECTION_END)
    if REFRESH_SUCCESS_CONTINUATION not in refresh_section:
        raise CheckError("missing authenticated Refreshing continuation contract in §7.3")
    release_section = _section(text, RELEASE_SECTION_START, RELEASE_SECTION_END)
    for fragment in (
        UNCONFIRMED_CLEANUP_OBLIGATION,
        GATEWAY_CLEANUP_ATTEMPT_ID,
        DISCONNECT_CLEANUP_OBLIGATION,
        DISCONNECT_CLEANUP_MUTEX_INDEPENDENCE,
        RESTART_RELEASE_CONTRACT,
    ):
        if fragment not in release_section:
            raise CheckError("missing process-local disconnect cleanup obligation in §7.4")
    reconnect_section = _section(text, RECONNECT_SECTION_START, RECONNECT_SECTION_END)
    if NO_AUTO_RESUME_RECONSTRUCTION not in reconnect_section:
        raise CheckError("missing no-reconstruction boundary in §7.5")
    if REFRESHING_DISCONNECT_FENCE not in reconnect_section:
        raise CheckError("missing Refreshing disconnect fence in §7.5")
    if RESTART_CLEANUP_FENCE not in reconnect_section:
        raise CheckError("missing bounded per-target restart cleanup fence in §7.5")
    idle_timeout_section = _section(
        text, IDLE_TIMEOUT_SECTION_START, IDLE_TIMEOUT_SECTION_END
    )
    if IDLE_TIMEOUT_ACK_CONTRACT not in idle_timeout_section:
        raise CheckError("missing valid-ACK idle-timeout cleanup contract in §7.6")
    normalization_section = _section(
        text, NORMALIZATION_SECTION_START, NORMALIZATION_SECTION_END
    )
    if NORMALIZED_REFRESH_DISABLE_CONTRACT not in normalization_section:
        raise CheckError("missing fail-closed refreshed-DISABLE normalization in §8")

    rows = _milestone_table(text)
    for expected in (M2B_GRAPHQL, M3_PORTAL):
        _require_exact_row(rows, expected)
    for fragment in FORBIDDEN_ALL_READ_ONLY_MILESTONES:
        if fragment in rows:
            raise CheckError(f"forbidden all-read-only B503 milestone: {fragment!r}")
    install_write_section = _section(
        text, INSTALL_WRITE_SECTION_START, INSTALL_WRITE_SECTION_END
    )
    if install_write_section != INSTALL_WRITE_SECTION:
        raise CheckError(
            "§9 B503 installation-write classification, prohibition, enforcement, "
            "and future-plan boundary must remain exact"
        )

    truth_rows = _capability_truth_table_rows(text)
    if [row for row in truth_rows if row[0] == "6"] != [DISPATCH_FAILURE_TRUTH_ROW]:
        raise CheckError("missing exact cleanup-aware dispatch-failure truth-table row")
    if [row for row in truth_rows if row[0] == "7"] != [REFRESHING_CAPABILITY_TRUTH_ROW]:
        raise CheckError("missing exact §12.5 held-session refresh truth-table row")


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
