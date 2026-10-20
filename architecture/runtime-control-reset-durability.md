# Offline reset: quarantine durability before replacement

Status: normative clarification supplement for [issue #691](https://github.com/Project-Helianthus/helianthus-docs-ebus/issues/691), **awaiting canonical integration**.
This supplement does not change the canonical
[offline namespace-only reset contract](runtime-driver-lifecycle.md#offline-namespace-only-reset)
or its checker. It specifies the preservation prerequisite that must be carried
into that contract and any manager-page restatement after the lifecycle work
merges. It adds no reset mode, flag or API surface.

## Scope and evidence

The public gateway [reset tool](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/scripts/reset_runtime_control.py)
already calls `fsync_dir` after creating, writing, fsyncing and closing the
quarantine copy, before `replace_atomically` is called. This documents existing
implementation ordering, not a newly fixed implementation. The relevant source
functions are `run`, `write_quarantine`, `replace_atomically` and `fsync_dir`.
The [reset tests](https://github.com/Project-Helianthus/helianthus-ebusgateway/blob/main/scripts/test_reset_runtime_control.py)
provide implementation context; their presence does not establish coverage of
every prerequisite below.

- **Proven (source inspection):** the supplied public implementation orders
  quarantine preservation before temporary replacement creation and treats a
  quarantine `OSError` as a refusal without replacement.
- **Hypothesis:** omitting only the quarantine-directory fsync can leave the
  exact copy's directory entry absent after power loss despite successful file
  fsync. This is the durability counterexample motivating the prerequisite,
  not an observed device or filesystem result.
- **Unknown:** physical power-loss behavior on a particular storage stack.
  Source inspection is separate from runtime qualification, freshness and
  physical acceptance; this supplement establishes none of those.

This is an offline application persistence contract, not an eBUS wire claim.
It preserves the existing D1-D5/O8 obligations, native trust and raw evidence,
partial last-known-good state and fail-closed admission. It changes neither
the deterministic MCP envelopes nor GraphQL parity, and introduces no receipt,
idempotency-key store or authority boundary. Nothing here declares stability
before Helianthus 1.0.

## Required ordering and failure outcomes

Keep the existing offline, exclusive-writer and valid-base prerequisites.
Quarantine must preserve the **exact original whole-file bytes**, including
malformed control material and opaque retained members, rather than a decoded
and reserialized approximation. An unreadable or invalid base is refused under
the existing repair contract; preservation does not authorize repairing it by
guessing. Never overwrite an existing quarantine copy.

All quarantine prerequisites must succeed before live replacement begins,
including before creating the temporary replacement file. File fsync alone
does not establish durability of the newly created quarantine directory entry.
The quarantine parent-directory fsync must succeed; unsupported operations and
other errors are failures, not tolerated durability evidence.

| Order | Required operation / boundary | Failure outcome |
|---|---|---|
| 1 | Under the exclusive store lock, read the original bytes and validate the existing reset plan and preserved base. | Refuse before replacement; live bytes remain unchanged. No fresh base or identity is invented. |
| 2 | Exclusively create a non-overwriting quarantine file and copy all exact original bytes, completing partial writes. A name collision may select another unused name, never truncate a copy. | If no exclusive copy can be completed, refuse; live bytes remain unchanged. An incomplete artifact is not a preserved copy. |
| 3 | Successfully fsync the quarantine file, then successfully close it. | Any write, file-fsync or close failure refuses before replacement; live bytes remain unchanged. |
| 4 | Successfully fsync the quarantine file's parent directory and complete directory-handle cleanup. This is a prerequisite, not deferred work. | Any failure refuses before replacement; live bytes remain unchanged, even if the quarantine file's fsync succeeded. Retain any artifact without claiming it is durable. |
| 5 | Only after orders 1-4 succeed, create the same-directory replacement temporary file, write the planned namespace-only replacement, fsync that file and close it. | Failure before live rename refuses; live bytes remain unchanged and the exact quarantine copy is retained. A temporary file is not a committed replacement. |
| 6 | Atomically rename the temporary replacement over the live file. No cross-filesystem fallback. | A refused rename that did not replace the live file leaves live bytes unchanged. An unconfirmed rename outcome must not be reported as an unchanged refusal. |
| 7 | Successfully fsync the replacement parent directory, then confirm replacement bytes by readback. | Failure after successful live rename is a distinct ambiguous-durability/readback outcome, not a pre-replacement refusal. Retain quarantine, report uncertainty and inspect state before retrying. |

The tool maps quarantine and confirmed pre-replacement failures to
`FAILED_PRECONDITION` (exit 3). After replacement, a failed directory fsync or
failed/disagreeing readback is `AMBIGUOUS` (exit 5). No success may be inferred
from rename alone, a visible file, or readback agreement without established
directory durability. Ambiguity supplies no start, cleanup, native-close or
admission proof; the canonical recovery rules continue to fail admission closed.

Namespace-only replacement retains GUID ownership, meta, eBUS cache, unknown
namespaces and the verified D5 recovery material under the existing contract.
Reset does not erase independent valid state or discharge retained cleanup and
close obligations. It never starts a driver.

## Canonical integration hand-back

The lifecycle-page owner must add the following preservation prerequisite to
the offline reset section and align any manager-page restatement:

> Before any live namespace replacement begins, exclusively copy the exact
> original bytes to a non-overwriting quarantine file, successfully fsync and
> close that file, and successfully fsync its parent directory. Failure of any
> quarantine prerequisite refuses replacement and leaves the live bytes
> unchanged. A failure after live rename is a distinct ambiguous-durability
> outcome and must not be described as an unchanged refusal.

The contract/checker owner must then require that clause in
[`runtime_control_contract.json`](../scripts/runtime_control_contract.json)
and enforce its normative placement with
[`check_runtime_control_contract.py`](../scripts/check_runtime_control_contract.py)
and focused [contract tests](../tests/test_runtime_control_contract.py).
Manager cross-document integration and checker/fixture enforcement remain
outstanding; this supplement does not claim to supply them.

The discriminating counterexample keeps exclusive creation, exact copying,
file fsync and close, but omits **only the quarantine parent-directory fsync**
before replacement. It violates order 4 even when every other step succeeds.
The future checker regression must reject removal, weakening or relocation of
that prerequisite outside the normative reset section. A separate replacement
directory fsync after rename cannot satisfy the earlier prerequisite.

These are reasoned mutation requirements, not executed mutation kills or
runtime tests. Independent checks for creation, copy, file-fsync, close and
quarantine-directory failure must each establish unchanged live bytes and no
replacement call; the positive control must reach replacement only after all
quarantine steps succeed. Post-rename failure must instead establish the
ambiguous outcome and retained quarantine. Those implementation checks belong
to the gateway owner; this document adds no fixtures or implementation changes.
