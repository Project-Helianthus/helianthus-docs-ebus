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
| Latest functional correction commit | `e80413e2d7096cbe7f0dda919a262113a550321b` |
| Latest functional correction tree | `fcede5610f659103b692ff0fe70a4f659012374b` |
| Focused validation | Portal 313 PASS; canonical B503 190 PASS; combined 503 PASS |
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

- combined focused suite: 503/503 PASS;
- Portal checker: 313/313 PASS;
- canonical B503 checker: 190/190 PASS;
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

The fresh independent review at candidate
`dcf2e45cf49fe6d90428c8787c35a10eac7b3413`, tree
`3481d89df5f2297bb10aa449973e7b528b17f26c`, returned one P2: the
post-emission epoch-advance operation row required exactly one defensive
disable while the normative transition row permitted at most one during the
admitted lifecycle. Its report is
`wave12/review/docs524-dcf2e45-final-independent/REPORT.md`, SHA-256
`039a917ba04f1997dea5a5ce658bd23f6a3a40774c1687ccc99644e1dc182c5a`.
Functional commit `ad13fab39b5bb860abbf89d0948db0a3ccae5108`, tree
`8907f33365b3017b70d27b4296650ea656d3ceb1`, aligns both rows on at most one
defensive disable during the admitted lifecycle. This preserves the
zero-write disconnect/restart rule when no write can be admitted and adds a
regression that rejects reintroduction of the contradictory exactly-one
requirement.

The fresh independent review at candidate
`7fe596f7048818a7f5ad4e1f19f440f1fc48bfee`, tree
`e5134caae0aaa82336ae86b40c57a2dd86d49efd`, returned one P2: a target with a
still-effective explicit operator or configuration disable could present
either `Disabled` or the generic restart-derived `Idle` because no precedence
was defined. Its report is
`wave12/review/docs524-7fe596f-final-independent/REPORT.md`, SHA-256
`4681578a91952f572a3b0a321b516f6c59c6d793021a80f2ac581a42f970473d`.
Functional commit `5dfd5f1087f2a71450f3701bb325caf7c91d6e21`, tree
`4a499a73f6930bd458861e69fe46b473b1941647`, defines the finite precedence:
the still-effective explicit disable remains public `Disabled`/`owned:false`
across restart; every other restart-derived cleanup state presents
`Idle`/`owned:false`. Canonical and Portal mutation tests reject removal of
that precedence.

The fresh independent review at candidate
`af11027151619591fe1cd8b864bc916eab9f9d6c`, tree
`7b5b451830f11c824eeb27e12ae634d643e4de6d`, returned one P1 and one P2. The
exact disconnect row sent an `IDLE` target with no owner or cleanup to
`DISABLED`, contradicting the reconnect-ready `Idle` rule, and raw `<pre>`
could wrap the exact Markdown truth or milestone table while the validator
still treated it as a rendered table. The report is
`wave12/review/docs524-af11027-final-independent/REPORT.md`, SHA-256
`822025996071e445bc549f517b3f094a857f5c65e821be1f44bda21aba4ac6ae`.
Functional commit `edb9a70813231d096b067ac51b3ee8f1d52927c6`, tree
`a841847d2e053df4a431b0c2665bf4135c79401f`, splits disconnect behavior by
state: `IDLE` without owner/cleanup remains `IDLE`, held-owner states enter
`DISABLED` with cleanup, and existing `DISABLED` state retains its cleanup and
fence. It also treats raw `<pre>` as code that cannot satisfy normative table
extraction. Focused mutations cover both required tables and reject a
cleanup-bearing reconnect to `IDLE`.

The fresh independent review at candidate
`98fa69e75469bb959dc3919b6c40cec66e04051e`, tree
`5b65a3f30aa08a127e11158a60874cc57557308a`, returned one P1 and one P2. The
Portal's held-`Refreshing` rule incorrectly kept the same re-bound current
owner's controls blocked until `AVAILABLE`, which never follows the approved
conservative successful-READ path, and the exact transition table reset the
idle timer for any READ request rather than only a successful completion. The
report is `wave12/review/docs524-98fa69e-final-independent/REPORT.md`, SHA-256
`a655fd33cefa8895dc84d6e66756446df7c5f8bc2649bfeac67c4096de6cd179`.
Functional commit `dae38f0c29691b8031f1ae65735492b6972d97bb`, tree
`aff66f1c23ada497a17b3a2e0c9b4c6330d13c05`, limits status-only blocking to
the actual `Refreshing` state and immediately resumes the exact same
target/token `Active` owner exception under `UNKNOWN` after a successful READ
refresh. It also splits successful and failed READ rows so only success resets
the idle timer. Mutations reject an `AVAILABLE` prerequisite, unbound
target/token controls, generic request-time reset, and failed-read reset.

The fresh independent review at candidate
`8ac9df08bf5fb19768a6ba2dddafeb1d206c0da1`, tree
`2efda7e965b341d6bf92ae8c05c61772bb32390e`, returned two P2 Portal-validator
bypasses: a raw `<pre>` wrapper could still satisfy the required availability
table, and an encoded SVG `xlink:href` could name a forbidden REST fallback
without entering the fixed-route URL audit. The report is
`wave12/review/docs524-8ac9df0-final-independent/REPORT.md`, SHA-256
`e6728efa483ea0f31d4ea31a77f855b792fe861af6afb3256d6def361e53ce30`.
Functional commit `ac28f2cba5370c97dd9483f607ed980d6efe90d1`, tree
`2f9dcc163cb0b55ade3287efac159fec38320020`, makes raw `<pre>` inert for the
Portal availability table and includes `xlink:href` in entity/percent-decoded
URL-bearing attributes. Focused mutations reject both exact bypasses while
retaining unrelated visible HTML destinations.

The fresh independent review at candidate
`f7d091e41d0f91f6301cf584ea71e69b7afa33bf`, tree
`f8ae4304e7d25bdc7c6f777e4bef72a1687d74a2`, returned two P2s. The phrase
“explicit operator disable” could conflate a current-owner native session
DISABLE, which presents `Idle` with cleanup, with the out-of-band
administrative/configuration-disabled condition that presents `Disabled`.
Both validators also treated required clauses inside a closed `<dialog>` as
reader-visible. The report is
`wave12/review/docs524-f7d091e-final-independent/REPORT.md`, SHA-256
`e1cfb4591ff3de7f8c2ebc61a2b95806291d41ed63004b4811fc0247bc030338`.
Functional commit `e514194192c8b8e7b6ecb7b96f4c458200ba2405`, tree
`0d8ea7015d10f7d85db1b73d0e4170fba80705fa`, makes the two events disjoint:
the current-owner session action always presents `Idle`/`owned:false` with
retained cleanup and `UNKNOWN`, while only a Gateway-supplied out-of-band
administrative/configuration-disabled condition presents
`Disabled`/`owned:false` and emits no B503 operation. Both visibility parsers
now reject required content in a closed dialog while accepting `<dialog open>`.

The fresh independent review at candidate
`17bd2e08354691f2d98bd055c640f2c5f974a820`, tree
`57b4002d27882191dc2a3128892f5551ef6be173`, returned two P2s. An ownerless
`IDLE` target under `TRANSPORT_DOWN` could still satisfy the generic Enable
row, and a fake target-end heading inside fenced code could truncate later
Portal safety audits. The report is
`wave12/review/docs524-17bd2e0-final-independent/REPORT.md`, SHA-256
`44f68c90dd7f698876f0c4bbbda583dc9cb11bb1a7753ce39d83bb77102de7c1`.
Functional commit `c9748c97ff105f8f7fe1ebd486d05e5baa94d61c`, tree
`12e2f895f2a961fb5a066ae65faf1757315d6d1c`, requires ownerless, cleanup-free,
connected `AVAILABLE` admission before `IDLE → ENABLING`; every unavailable
case returns the exact Gateway result with no transition or emission. The
Portal validator now derives its target bounds from rendered CommonMark H2
tokens and uses those same bounds for inline, raw HTML, and fenced-content
audits, so a fenced fake boundary cannot hide a later rendered control.

The fresh independent review at candidate
`80dbc7062bb6044033d94e948ecf5795243a0f76`, tree
`9f44dee71e0eee0e2f9abdfbc110d8a487482f91`, returned two bounded P2
validator bypasses. An executable HTML event-handler attribute could name a
forbidden Portal REST destination without entering the fixed-route audit, and
iframe fallback text could satisfy required prose or table anchors even though
supporting browsers render the nested document rather than that fallback text.
The report is `wave12/review/docs524-80dbc70-final-independent/REPORT.md`,
SHA-256
`6e95e30dda3667ef4f31429f12973f8e7b9927127a1e61daf7c232e2255540d4`.
Functional commit `f7254aa660b7bd9c76741f04b835d7e04aeb6c76`, tree
`8933a9491279cb7f4bb2267d4f5a8470ea8a8f07`, subjects `on*` attribute values
to the same entity/percent-decoded fixed-route audit while retaining safe
event-handler names such as `preview()`. Both visibility parsers now treat
iframe fallback content as inert. Exact mutations cover literal and encoded
event-handler destinations, required clauses, the Portal availability table,
and the canonical capability and milestone tables.

The fresh independent review of candidate
`1c632b81b9b56bec3139a3738fa96a73f98cf9f1`, tree
`bbda906750a7442d047f33d032635e8d912e144a`, returned
`NO_BLOCKING_FINDINGS` after reproducing both corrections and the retained
settlement/reconnect/transport-down probes. Its report is
`wave12/review/docs524-1c632b8-final-independent/REPORT.md`, SHA-256
`cd1eaa1001810cd4ef0cb5acb7418f3367df45ffc271b0d5a903f29dd770df9f`.
The mandatory later feedback refresh then found one additional same-class P2:
an `<object>` element could supply fallback prose or tables even though a
successfully loaded resource replaces that content. Functional commit
`e0b3078099d23ea5d8fcc798e6d8a8fe35a1f4c8`, tree
`5f233f2c6aba3fa48c9fb01d1f942f823ec11cc6`, makes object fallback inert in
both bounded visibility parsers. Exact mutations cover required prose plus the
Portal availability and canonical capability/milestone tables. The same
feedback refresh identified stale 305/179/484 counts in this report; they now
record that candidate's 311/185/496 focused run. The final evidence commit remains
self-referential, so its exact SHA/tree and immutable complete-CI log identity
are bound externally in the PR body and fresh independent review bundle.

The fresh independent review of candidate
`811aa8621624e22cbcc262f5dfa5417ed844aa97`, tree
`63658a77ca0eb047bc316eb88f4a21e3787fdc67`, returned
`NO_BLOCKING_FINDINGS` with 496 focused tests. Its report is
`wave12/review/docs524-811aa86-final-independent/REPORT.md`, SHA-256
`16204e89d3c0af5cd1665ef40009dfc3aef4b8af5936aff93ca2df774870dbd1`.
The mandatory later feedback refresh found two further P2s. Canvas fallback
content could still supply hidden prose/tables, and the DISABLE transition
combined a disconnect before frame emission with outcomes after emission while
requiring an exact write. Functional commit
`e80413e2d7096cbe7f0dda919a262113a550321b`, tree
`fcede5610f659103b692ff0fe70a4f659012374b`, makes canvas fallback inert in
both visibility parsers. It also splits current-owner and refreshed DISABLE
paths: a terminal disconnect while waiting for poll-quiesce emits zero frames,
returns exact `TRANSPORT_DOWN`, releases ownership, retains cleanup/`UNKNOWN`,
denies Enable, and is never retried; exactly-once applies only after the frame
reaches emission. The ordered transition table and exact mutations cover both
states, emission and reconnect-retry regressions.

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
