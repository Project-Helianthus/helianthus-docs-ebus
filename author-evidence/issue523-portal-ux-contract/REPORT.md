# Issue 523 Portal UX Contract — Author Evidence

## Scope

This report records the public documentation gate for
[helianthus-docs-ebus#523](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/523)
and PR
[#524](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/524).
It freezes the contribution-driven Portal and target-bound Vaillant B503
contract consumed by Gateway
[#552](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/552)
and PR
[#975](https://github.com/Project-Helianthus/helianthus-ebusgateway/pull/975).

This is documentation and validator work. It does not claim Gateway acceptance,
live eBUS validation, deployment, credential handling, physical qualification,
complete SemReg cutover, or release acceptance.

## Exact source and validation identity

| Item | Exact value |
|---|---|
| Repository | `Project-Helianthus/helianthus-docs-ebus` |
| Branch | `issue/523-portal-ux-contract` |
| Base commit | `6ce5c9f62690e1b9b18cb888f187ba7d89b845f0` |
| Base tree | `2f60febe5760a895b31f10c6f8129f97e7d0b008` |
| Latest functional correction commit | `da22da61cfd194537a9a4837fb9ab49fe19d3ec4` |
| Latest functional correction tree | `188463fcf3fc53725afd0b0aba9aa2caf2781b34` |
| Focused validation | Portal 295 PASS; canonical B503 162 PASS; combined 457 PASS |
| Complete configured CI | Rerun on the final evidence candidate after this report commit; the exact HEAD and immutable log hash are recorded in the PR body and independent review bundle |
| Diff and syntax | `git diff --check` PASS; both Python validators compile |
| Current review state | Fresh review is required after this evidence update is committed and pushed |

The PR review candidate includes this report, so its own commit and tree cannot
be embedded in the same commit without creating a self-reference. The PR body,
lead review bundle, feedback inventory, and independent review report record
that final exact HEAD/tree. The table above names the immediately preceding
functional commit whose exact source was exercised by complete CI. Complete CI
is rerun on the evidence commit before final review.

## Current public contract

Gateway owns the immutable five-domain catalog, Portal rendering boundary,
caller-scoped action admission, B503 lifecycle, and native outcome recording.
The browser consumes accepted contribution/resource/field/action identities and
does not recover semantics from labels, native MCP, or legacy aggregates.

The Portal contract defines:

- the fixed GraphQL transport and no REST/native-MCP fallback;
- deterministic five-domain contribution rendering without a central vendor
  switch;
- selected-target and frontend-epoch fencing for every B503 result;
- all five B503 availability and session states with stable selectors;
- an `Active` same-browser token-owner exception that retains only its session
  strip and READ/DISABLE controls while capability remains `UNKNOWN`, without a
  second Enable or admission for any other `UNKNOWN` presentation;
- contribution-gated projection, bounded history, session strip, target/nav-away
  cleanup, and AD02 installation-write warning;
- no public exposure of the `02 01` or `02 02` installation selectors;
- current lifecycle, freshness, loss, quality, provenance, authorization, and
  action-revalidation inputs without browser-derived native facts.

## Conservative B503 session settlement

The Board approved the conservative 0.7 behavior after the public source review
found no command-specific native session-settlement evidence.

ACK, NAK, timeout, CRC, arbitration, and disconnect remain exact native
outcomes. None proves that the device session stopped or was never created.

The transition guards are disjoint:

- a successful enable ACK received after frame emission enters `ACTIVE`,
  retains the Gateway cleanup obligation, publishes capability `UNKNOWN`,
  permits the current owner to read or disable, and admits no second Enable;
- pre-emission cancellation returns directly to `IDLE` with zero write and no
  cleanup obligation;
- NAK, cancellation after emission, timeout, CRC/arbitration failure, and other
  non-ACK emitted outcomes enter internal `DISABLED`, release the owner, retain
  fail-closed cleanup, publish `UNKNOWN`, and admit no Enable;
- explicit, idle-timeout, refreshed, and defensive disables record their exact
  outcomes but never clear cleanup or establish re-claimability;
- terminal disconnect releases ownership and retains process-local cleanup
  evidence without an automatic reconnect write;
- restart destroys caller handles and process-local attempt identities, fences
  each qualified target at `UNKNOWN`, admits no Enable, and emits no automatic
  B503 write.

Portal and GraphQL expose no maintenance recovery control.
[Deferred docs-eBUS issue #525](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/525)
owns later command-specific observation/readback, the still-unknown `00 03`
semantics, profile/version applicability, regression fixtures, and any
coordinated contract/runtime/consumer revision. It is not a blocker for the
approved conservative behavior and authorizes no physical work.

## Validator boundary

The Portal and B503 validators enforce the declared current fragments, exact
ordered tables, section placement, fixed route, protected selectors, stable
state mappings, and supported rendered CommonMark/HTML forms. They do not claim
to prove arbitrary English.

Reader-hidden material cannot satisfy a required clause when placed in:

- HTML comments;
- fenced or indented code;
- link destinations or titles;
- image labels or destinations;
- non-rendering `head`, `script`, `style`, or `template` elements;
- elements with the standard `hidden` attribute;
- elements with case-insensitive `display:none` or `visibility:hidden`,
  including optional CSS `!important` priority.

Negative mutations also reject overlapping ACK terminal guards,
ACK/NAK-as-settlement, cleanup release, re-Enable under unproven settlement,
automatic or current-contract operator-authorized restart recovery, stale
availability mappings, route/selector fallback, and public installation-write
controls. Positive controls retain visible prose, benign HTML, status-only
observation, and the successful ACK owner path.

## Applicable validation

The final functional commit was validated with:

```sh
python3 -m pytest -q   tests/test_portal_ux_contract_checker.py   tests/test_vaillant_b503_milestone_checker.py
python3 scripts/check_portal_ux_contract.py
python3 scripts/check_vaillant_b503_milestones.py
git diff --check
PLATFORM_M625_DOCS_EEBUS_ROOT='<verified docs-eeBUS root>' PLATFORM_M625_EXECUTION_PLANS_ROOT='<verified execution-plans root>' ./scripts/ci_local.sh
```

Results:

- combined focused suite: 457/457 PASS;
- Portal checker: 295/295 PASS;
- canonical B503 checker: 162/162 PASS;
- both checker CLIs: PASS;
- complete configured repository CI: PASS;
- `git diff --check`: PASS.

The read-only M6.25 inputs were clean and detached:

- docs-eeBUS `cedf238e34f879815ba773e9cd76b2b31c2822a3`, tree
  `7667c4f2675ee627812f048ee164bc30eec331b3`;
- execution plans `fb384ab57d79f0020c54d2c66416e8a7666f0ceb`, tree
  `1f48c5d0cf1aecd2cfa72e0b16f50e41df3ea5af`.

No transport or physical smoke gate applies to this documentation/checker-only
change.

## Review and feedback history retained as evidence

The complete feedback inventory includes every PR general comment, review body,
and inline thread, including resolved and outdated discussions. Earlier
intermediate corrections remain available in Git history and immutable review
reports; this current report does not repeat their superseded behavior.

The latest pre-correction independent review is:

- candidate `9c39a4f989a3aeef88ab3ebd34cffcef6363d511`, tree
  `aa41ef439e63e6c95a8c2c7ed778103cbbf922f6`;
- verdict `BLOCKING_FINDINGS`, three P2s;
- report
  `wave12/review/docs524-9c39a4f-final-independent/REPORT.md`;
- SHA-256
  `6b81ba01e9b49d72c5b70c37c1d1053ed529a96e0e0612f442c261e187198add`.

Those P2s are addressed by functional commit
`6fee72aa8e309b9eea98761ea691f44eb42d4c95` and this evidence update:

1. the successful enable ACK guard is disjoint from the non-ACK emitted failure
   guard, with exact transition and mutation coverage;
2. both hidden-style helpers normalize optional `!important` before comparing
   `display:none` and `visibility:hidden`;
3. this evidence update records the current functional SHA/tree/test counts and
   retains obsolete intermediate semantics only in Git history.

The next independent review of exact
`f6672dce6d24ab20b0250c0b595d9031ff4fe3ea`, tree
`6620be1f0a50d884983521355faa831155ded4a6`, returned one P2: additive
contradictory table rows or settlement clauses could coexist with all required
safe anchors. Its report is
`wave12/review/docs524-f6672dc-final-independent/REPORT.md`, SHA-256
`da5c0131d590ab17d1031fcddf5dfa078a51ac19649abb5a90a5f35dee039ece`.
Functional commit `6fee72aa8e309b9eea98761ea691f44eb42d4c95`
closes that gap with an exact ordered finite §6.3 transition-table check and
bounded contradiction patterns for explicit disable-ACK settlement and
enable-NAK re-admission claims. Insertion mutations for the reported ACK to
`DISABLED` row and both settlement clauses reject. This remains a structured
FSM/settlement check, not an arbitrary-English parser.

The subsequent hosted review at candidate
`5f375889a42334fe92d32fb788ce55ff9b77d624` found one P1 integration defect:
the successful ACK transition kept a current owner in `Active` with capability
`UNKNOWN`, but the Portal's prior `AVAILABLE`-only rendering removed that
owner's controls immediately. The public finding is
[the Active-owner control thread](https://github.com/Project-Helianthus/helianthus-docs-ebus/pull/524#discussion_r4008117718).
Functional commit `da22da61cfd194537a9a4837fb9ab49fe19d3ec4`,
tree `188463fcf3fc53725afd0b0aba9aa2caf2781b34`, retains the already-mounted
same-target session strip plus READ/DISABLE controls only while the browser
holds the exact current token and Gateway reports `Active`/`owned:true`. It
admits no second Enable, general tabs, new projection entry, or any other
`UNKNOWN` target/session. Portal and canonical validators require that bounded
exception and reject its removal or expansion.

The earlier independent evidence opinion that ACK/NAK settlement was unsupported
is preserved at
`wave12/review/docs524-02a9eae-ack-semantics-opinion/REPORT.md`,
SHA-256
`4194fa8b0c5ee8b553e125a2bfd1c786bd0fe2daeaec3dff8805055efff573ee`.
The source reconciliation is preserved at
`wave12/consultations/b503-session-settlement-evidence-gap/REPORT.md`,
SHA-256
`1e57d8a80d8ba30ebeffe81262e711bc719692ca35a70797ff463f670bef260a`.

## Remaining gate

Commit and push this evidence update, rerun complete CI on that exact candidate,
reconcile all current feedback bodies, and obtain a fresh independent exact-HEAD
`NO_BLOCKING_FINDINGS` verdict before merge. After merge, verify remote main,
issue/PR state, branch disposition, and hosted PR/main checks.

No live equipment, credential, deployment, vulnerability, hardware, or physical
action belongs to this change.
