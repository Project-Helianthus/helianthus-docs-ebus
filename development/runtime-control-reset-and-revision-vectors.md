# Runtime control: offline reset flags and CTL-19 revision traces

Status: bounded clarification supplement for [#693](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/693),
following [#666](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/666)
and [gateway #1157](https://github.com/Project-Helianthus/helianthus-ebusgateway/issues/1157).
The canonical lifecycle decision procedure, CTL-19 vector and frozen checker
rules now carry the per-driver comparison correction described below. This
supplement does not change the public control API.

## Evidence and scope

**Proven (implementation source):** the supplied public-source view of
[`scripts/reset_runtime_control.py`](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/scripts/reset_runtime_control.py)
defines the flags below in `build_parser`, checks them in `run`, and validates
the replacement in `plan_reset`. The source of
[`internal/runtimestate/runtime_control_test.go`](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/internal/runtimestate/runtime_control_test.go),
`TestControlSerializationPointRereadsTheMark`, asserts the two cross-driver
orderings and the same-driver case described below. Reading those assertions
is not an executed test result. These are implementation claims, not native
eBUS wire facts.

**Hypothesis:** none is needed for the arithmetic traces. **Unknown:** runtime,
transport and physical acceptance in any installation. Source agreement does
not establish qualification, evidence freshness or an executed reset. Nothing
here declares a stable contract before Helianthus 1.0.

## Offline synthetic preview reference

The [lifecycle reset section](../architecture/runtime-driver-lifecycle.md#offline-namespace-only-reset)
still presents a conceptual command. The implemented offline script accepts
this synthetic preview shape; it is reference syntax, not an instruction to
operate equipment:

```text
python3 scripts/reset_runtime_control.py --state-file <synthetic-state-file> --namespace runtime_control --desired STOPPED --driver-id family.a --driver-id family.b
```

`--driver-id` is repeated once for each configured driver ID. There is no driver
configuration-file argument or automatic configuration discovery in this
interface. It therefore cannot prove that supplied IDs match the complete
configured installation set. This reference is limited to synthetic preview:
apply to installation state through this interface is non-conformant with the
canonical reset contract, even with both write flags. A conforming apply path
must resolve the complete ID set from validated read-only installation
configuration and refuse when it cannot validate it; caller-supplied IDs alone
are insufficient. Preview IDs must be canonical and unique, with a nonempty
set within the record bound. Repeating the flag with different IDs supplies multiple drivers;
repeating the same ID is refused. Assignment uses bytewise `DriverID` order,
not argument order. The only namespace is `runtime_control`, and the only
desired value is `STOPPED`.

| `--apply` | `--gateway-stopped` | Result for otherwise valid input |
|---|---|---|
| absent | absent | Preview; no state replacement or quarantine copy |
| absent | present | Preview; the assertion alone does not apply a reset |
| present | absent | `FAILED_PRECONDITION`; no replacement |
| present | present | Implementation write path; non-conformant for installation reset because configuration cannot be validated |

Preview is the default. The implementation requires both flags to write a
replacement; that condition does not establish reset conformance.
`--gateway-stopped` is an operator assertion, not proof that the writer stopped;
the exclusive store lock must also be acquired. Preview also acquires that
lock and may create its sidecar file, although it does not replace state.
Neither mode is an online bypass, gateway startup option or MCP repair tool.
No reset was executed to produce this reference, and no native start is part
of the offline command.

### Implementation bounds, preservation and refusal

The following describes implementation behavior, not approval to use its
non-conformant apply path on installation state.

The validated issued-revision mark `H` bounds earlier desired revisions,
including removed IDs and previous repairs. The durable catalog revision `C`
must also validate. An invalid base or GUID, invalid mark/catalog bound,
unverifiable D5 recovery envelope, or a validated driver/recovery revision
above `H` refuses replacement. Unknown namespace material is not decoded as
empty. Whole-file damage requires a valid GUID-preserving base first.

For `N` supplied IDs, the implementation replacement assigns STOPPED at
`H + 1` through `H + N`, advances the mark to `H + N` and catalog revision to
`C + 1`, and removes active work from the desired-control records. If either
`H + N` or `C + 1` exceeds the unsigned 64-bit maximum, it refuses with
`COUNTER_EXHAUSTED` before replacement; it never wraps or lowers a bound.
Invalid bounds refuse with `FAILED_PRECONDITION`. These refusals replace
nothing. Exit codes are 0 for successful preview/apply, 2 for parser usage
errors, 3 for `FAILED_PRECONDITION`, and 4 for `COUNTER_EXHAUSTED`.
Post-replacement durability/readback uncertainty is separately `AMBIGUOUS`
(exit 5); it must not be described as proof that nothing was replaced.

Before apply, an exclusive, non-overwriting, fsynced quarantine copy preserves
the original bytes; failure to preserve it aborts replacement. Existing copies
remain. The GUID, meta, other namespaces and verified D5 recovery value retain
their original value bytes. Quarantine diagnostics supply no trusted revision
bound. Reset supplies no semantic replay, cleanup or native-close proof.
Ordinary restore retains exact native evidence and pending D5 cleanup/close
obligations, including partial last-known-good state; it does not manufacture
an empty successful snapshot or qualification. Historical START/RESTART work
can resume cleanup and close only, with admission still fail-closed until
recovery permits a new post-reset decision. See the
[D5 preservation requirements](../architecture/runtime-driver-lifecycle.md#offline-namespace-only-reset).

## CTL-19: compare the driver, allocate from the namespace

The [decision procedure](../architecture/runtime-driver-lifecycle.md#validate-decide-and-commit)
uses one namespace-wide serialization point. Under that point, compare
`ExpectedRevision` to the driver's own durable desired revision if a record
exists; only an absent-record driver uses the current namespace mark as its
current revision. Then allocate the accepted changing decision from the
re-read namespace mark plus one and commit record and mark together. A shared
allocator is not a global expected-revision comparison for recorded drivers.

Assume enabled synthetic drivers A (`family.a`) and B (`family.b`), each with
a changing START request carrying `ExpectedRevision=H`. Initially A has a
STOPPED record at `H`, B has no record, and the namespace mark is `H`, where
`H <= 2^64 - 3` leaves room for two increments. Assume validation, deadlines,
capacity, recovery and persistence allow the decisions.
Each ordering begins from that same initial state.

| Serialized order | Comparison and decision | Mark afterward |
|---|---|---|
| A first | A compares `H` to its own `H`; accepts at `H + 1` | `H + 1` |
| then B | B has no record and compares `H` to the re-read mark `H + 1`; `REVISION_CONFLICT`, no mutation | `H + 1` |
| B first | B compares `H` to the mark `H`; accepts at `H + 1` | `H + 1` |
| then A | A still compares `H` to its own record's `H`; accepts at the re-read mark plus one, `H + 2` | `H + 2` |

In the second ordering, B's acceptance does not change A's record. A must not
be rejected merely because the mark advanced. Neither ordering can persist a
previously computed `H + 1` twice. Accepted revisions remain unique; the mark
advances once per accepted changing decision, and never for a conflict.

For the serialized same-driver case, two START requests for absent-record B
both carry `H`. The first compares against mark `H` and creates B's RUNNING
record at `H + 1`. The second then compares against B's own `H + 1`, conflicts
and does not become a same-desired no-op: comparison precedes the no-op check.
Exactly one acceptance applies to this same-driver trace.

### Canonical contract and regression guards

The [decision procedure](../architecture/runtime-driver-lifecycle.md#validate-decide-and-commit)
and [CTL-19 row](../architecture/runtime-driver-lifecycle.md#amended-ctl-acceptance-vectors)
require these two cross-driver orderings and the same-driver conflict. The
frozen rules in `scripts/runtime_control_contract.json` and mutation fixtures
in `tests/test_runtime_control_contract.py` guard the distinction between a
recorded driver's comparison revision and the shared allocation mark. These
checks protect documentation; they do not execute the gateway races.

### Timeout and refusal ordering remain unchanged

The [refusal table and decision procedure](../architecture/runtime-driver-lifecycle.md#validate-decide-and-commit)
still apply: rows 1–5 validate shape, driver existence, control/load state,
configuration eligibility and finite deadline before the wait. Ambiguous
persistence pending readback remains admission-closed (`UNAVAILABLE`). On
acquiring the point, confirm admission and recheck deadline before comparing
revision or testing a same-desired no-op; recheck deadline again before commit.
An expired deadline returns `DEADLINE_EXCEEDED`, even if the expectation would
conflict or the request would otherwise be a no-op.

If the bounded wait expires without acquisition, confirm admission and perform
one read-only load of that driver's current desired revision (the mark for no
record). An expectation below that value is conclusively stale and returns
`REVISION_CONFLICT`; otherwise return `TRANSITION_BUSY`. Busy is not a
revision-comparison outcome. These waiters mutate nothing and do not advance
the mark; the holder may later commit independently. Ordinary acquired-point
mismatches still conflict before no-op handling. No timeout duration, retry,
receipt, authority boundary, or idempotency-key store is introduced. The
existing deterministic eBUS MCP envelope and GraphQL parity remain unchanged.
