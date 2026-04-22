---
name: review-docs-ebus
description: Docs-ebus review orchestrator. Unlike code review skills, this checks documentation correctness, cross-refs, protocol-spec accuracy vs. observed wire behavior, and companion-linkage to code PRs. Dispatches doc-specific sub-agents; no compilation / test gates.
disable-model-invocation: false
allowed-tools:
  - Agent
  - Bash(gh *)
  - Bash(git *)
  - Bash(grep *)
  - Read
  - Grep
---

# Review — docs-ebus

Per-repo orchestrator for `helianthus-docs-ebus`. Documentation is code-for-humans; quality bar is different from executable code but equally strict on accuracy, completeness, and cross-reference integrity.

## When invoked

- Every PR in helianthus-docs-ebus.
- Called from `cruise-preflight` Row 4 when companion docs PR is the subject.

## Sub-agents dispatched (parallel)

1. **`doc-spec-accuracy`** (custom inline):
   - For protocol docs: verify claimed wire formats against recorded fixtures in ebusgo / adapter-proxy test data if available.
   - Verify opcode semantics against firmware RE findings (`firmware/smartConnectKNX/extracted/`).
   - Check byte-by-byte sample frames have correct CRC, correct framing.
   - Flag any unsupported claim ("this register always returns X") without a fixture reference.

2. **`doc-cross-refs`** (custom inline):
   - Every `[link](path)` resolves to an existing file.
   - Every section reference (`see §4.2`) resolves.
   - Every GitHub issue/PR reference uses canonical form `Project-Helianthus/<repo>#<n>`.
   - Anchors in TOC match `##` headings.

3. **`doc-companion-code-link`** — delegates to shared `doc-companion-link` sub-agent in REVERSE mode:
   - This PR IS the docs companion; verify it back-references a code PR (unless it's standalone knowledge capture).
   - If standalone (no code PR), flag: "standalone doc PR — is there an issue tracking the observation?"

4. **`doc-drift-check`** (custom inline):
   - Compare docs PR changes against stated `## Protocol/Semantic impact` section.
   - If body claims "documents newly-decoded register X" and diff has no register table entry → flag.
   - If diff adds a wire-format section but body doesn't mention wire-format → flag.

5. **`doc-style-baseline`** (custom inline):
   - Headings in sentence case (project convention).
   - No trailing whitespace.
   - Code blocks have language tags.
   - Tables render (pipe alignment, header divider).
   - No "TODO" / "FIXME" in main branch additions (they should be tracked as issues).

6. **`doc-re-knowledge-audit`** (custom inline, only when RE trigger):
   - If PR claims new RE finding (firmware, decompilation, new register decoded):
     · at least one citation to `firmware/smartConnectKNX/extracted/` or equivalent artifact
     · version of firmware analyzed
     · method used (decompilation, runtime observation, manual probe)
     · confidence level (HIGH/MEDIUM/LOW) with rationale

## FSM

```
INTAKE → detect touched subdirs (semantic/, transport/, protocol/, re/, architecture/)
DISPATCH → parallel sub-agents relevant to touched subdirs + always run cross-refs + style
CONSOLIDATE → dedupe by file:line
VERDICT → high = BLOCK, medium = REQUEST_CHANGES, low-only = NOFINDINGS
LOOP
```

## Severity rules

- Factual claim without evidence (fixture, firmware ref) → **high**.
- Broken link or anchor → **high**.
- Diff/body mismatch (claims X but does Y) → **high**.
- Missing RE audit fields on an RE PR → **high**.
- Style violation → **low** (reported, non-blocking).
- Companion code reference missing on a doc-gate-triggered PR → **medium** (may be standalone; operator clarifies).

## Outputs

```yaml
review_docs_ebus:
  verdict: NOFINDINGS | block | request_changes
  subdirs_touched: [...]
  findings_by_subagent: {...}
  merged_findings: [...]
```

## Guardrails

- Never block on formatting alone when substance is sound — surface style issues as low-severity.
- Never flag a broken cross-ref if the target exists but is case-sensitive different (case-insensitive file systems exist); do the cross-check correctly.
- Never require a firmware citation for protocol docs that are paraphrased from publicly-known specs (eBUS general layer); only enforce for Vaillant-specific RE.
- Accept both English and occasional Romanian prose in operator-written sections (operator preference); flag only if publicly-facing material uses Romanian.
