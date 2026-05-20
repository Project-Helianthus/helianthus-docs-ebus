# Prometheus Alert Rules — Helianthus Gateway

This document is the operations-side reference for Prometheus alert rules
that the operator deployment manifest MUST include alongside the
helianthus-ebusgateway image. The gateway itself only exposes counters;
the *alerting decisions* — including any cross-counter or
mode-conditioned predicates — live in the Prometheus rules file shipped
with the deployment.

## Index

| Alert name | Source counter | Reference |
|---|---|---|
| `HelianthusRound9FiredUnderProxy` | `helianthus_round9_absorb_entered_total` | [frame-atomic-visibility-v8 §1.12 / I8](../architecture/adaptermux/frame-atomic-visibility-v8.md) |
| `HelianthusV8ShadowWouldHaveDroppedGrowing` | `helianthus_v8_shadow_would_have_dropped_total` | [frame-atomic-visibility-v8 §4.7 — B3.7 shadow divergence](../architecture/adaptermux/frame-atomic-visibility-v8.md) |

## HelianthusRound9FiredUnderProxy

**Owner:** operations team. The rule MUST be present in the Prometheus
config (`prometheus-rules.yaml`) before the adaptermux classifier is
enabled in `enforce` mode. Step C live-bus validation (v8 §14) verifies
rule presence via the Prometheus API before proxy rollout.

**Counter source:** `helianthus_round9_absorb_entered_total`
— exported by `helianthus-ebusgo`'s `protocol.Bus.Round9AbsorbEntered()`
accessor. The counter is named neutrally on the Go side — it counts
every round-9 AUTO-SYN absorb predicate fire inside `sendRawWithEcho`
(`protocol/bus.go`), gated on the runtime phase predicate
`inSendRawWithEchoActiveEchoWait()` (see [frame-atomic-visibility-v8 §1.8](../architecture/adaptermux/frame-atomic-visibility-v8.md)).
The "fired under proxy" interpretation lives ENTIRELY in this alert
rule's PromQL (which AND-s the counter with `classifier_mode == "enforce"`),
not in the counter's code-side name. This keeps the Go protocol layer
free of cross-repo coupling.

**Why this alert exists:** under v8 I8, round-9 absorb code is RETAINED
as a legacy fallback for direct-adapter mode (no proxy mediating wire
AUTO-SYNs). When the adaptermux classifier is in `enforce` mode, the
proxy is contractually obligated to filter wire AUTO-SYNs before they
reach the gateway's echo position; any round-9 fire under that mode is
a v8 invariant violation — the proxy is not filtering correctly.

**Suggested rule:**

```yaml
groups:
  - name: helianthus.round9
    rules:
      - alert: HelianthusRound9FiredUnderProxy
        expr: |
          rate(helianthus_round9_absorb_entered_total[5m]) > 0
          and on(instance) helianthus_adaptermux_classifier_mode{mode="enforce"} == 1
        for: 1m
        labels:
          severity: warning
          component: helianthus-gateway
          invariant: frame-atomic-v8-I8
        annotations:
          summary: "Round-9 AUTO-SYN absorb fired while adaptermux classifier is in enforce mode"
          description: |
            The gateway's round-9 AUTO-SYN absorb predicate fired on instance
            {{ $labels.instance }} while the adaptermux classifier is in
            `enforce` mode. Per frame-atomic-visibility v8 §1.8 / I8, the
            proxy MUST filter wire AUTO-SYNs before they reach the gateway's
            echo position when classifier mode is `enforce` — round-9 firing
            indicates the proxy is not correctly filtering. Investigate the
            adaptermux classifier path and per-session pacer; this is the
            v8 invariant violation that the round-9 fallback was kept to
            measure, not to mask.
          runbook_url: |
            https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/adaptermux/frame-atomic-visibility-v8.md#18
```

**Gating model:**

- The counter increments unconditionally on every round-9 fire, regardless
  of classifier mode. The Go code does NOT consult the classifier mode
  (no cross-repo coupling).
- The alert rule does the gating via the `helianthus_adaptermux_classifier_mode`
  gauge (exported by `helianthus-ebusgateway/internal/adaptermux` —
  scheduled for Phase 3 of the frame-atomic-visibility rollout). Until
  Phase 3 lands, deploy with the second clause commented out; the alert
  will trip on ANY round-9 fire, which is conservative and
  acceptable for the bootstrap phase.

**Pre-deploy gate (Step C live-validation, v8 §14):**

```bash
# Check the rule is loaded.
curl -s "${PROMETHEUS_URL}/api/v1/rules" \
  | jq '.data.groups[].rules[] | select(.name == "HelianthusRound9FiredUnderProxy")'

# Check the rule was loaded WITHOUT errors.
curl -s "${PROMETHEUS_URL}/api/v1/rules" \
  | jq '.data.groups[].rules[] | select(.name == "HelianthusRound9FiredUnderProxy") | .lastError // empty'
# Empty output = OK; any output here is a load error.
```

If the rule is absent or fails to load, the proxy MUST NOT be promoted
to `enforce` mode — the v8 invariant is unobservable without it.

## HelianthusV8ShadowWouldHaveDroppedGrowing

**Owner:** operations team. The rule MUST be present in the Prometheus
config before the adaptermux classifier is promoted from `shadow` to
`enforce`. This is the **pre-enforce canary signal** for v8 classifier
correctness.

**Counter source:** `helianthus_v8_shadow_would_have_dropped_total`
— exported by
`helianthus-ebusgateway/internal/adaptermux/v8classifier.Classifier.ShadowWouldHaveDroppedTotal()`.
The counter mirrors `fsmDropAaInjectionTotal` ONLY when the runtime
mode is `shadow`; it stays at 0 in `off` and `enforce`. Each
increment is a byte the v8 classifier would have filtered from
session dispatch if it had been the canonical filter — i.e. a
divergence vs the legacy pre-v8 path (which let the byte through).

**Why this alert exists:** during the shadow canary window before
promoting from `shadow` to `enforce`, operators need a clean
no-divergence baseline. The counter staying at 0 (or growing only
during known AA-injection events that operators expect to be
filtered) is the green-light for `enforce` promotion. The counter
growing under normal load means the classifier is flagging
legitimate bytes — a false positive that would change the byte
stream the cross-proxy client (ebusd) sees once enforce is on.
Investigate before promoting.

**Suggested rule:**

```yaml
groups:
  - name: helianthus.v8
    rules:
      - alert: HelianthusV8ShadowWouldHaveDroppedGrowing
        expr: |
          rate(helianthus_v8_shadow_would_have_dropped_total[5m]) > 0
          and on(instance) helianthus_adaptermux_classifier_mode{mode="shadow"} == 1
        for: 5m
        labels:
          severity: info
          component: helianthus-gateway
          invariant: frame-atomic-v8-B3.7
        annotations:
          summary: "v8 classifier flagged bytes for drop during shadow canary"
          description: |
            On instance {{ $labels.instance }} the v8 classifier
            is in `shadow` mode and the
            `helianthus_v8_shadow_would_have_dropped_total` counter
            is growing — the classifier is observing bytes it
            would have filtered if promoted to `enforce`. Under
            sustained, expected AA-injection load this is normal;
            under unexpected growth (no known AA-injection events
            in the bus capture) the classifier may be false-
            positive flagging legitimate bytes. DO NOT promote to
            `enforce` until the growth is explained.
          runbook_url: |
            https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/architecture/adaptermux/frame-atomic-visibility-v8.md#47
```

**Severity rationale (info, not warning):** non-zero growth in shadow
mode is not itself a fault — it's the signal the operator is
specifically looking for during canary validation. Promote to
`warning` (or `critical`) by editing the rule once the operator's
shadow validation runbook is complete and they want failure on
any unexpected growth.

**Pre-promotion gate (Step C live-validation, v8 §14):**

```bash
# 1. Check the rule is loaded.
curl -s "${PROMETHEUS_URL}/api/v1/rules" \
  | jq '.data.groups[].rules[] | select(.name == "HelianthusV8ShadowWouldHaveDroppedGrowing")'

# 2. Check the rule was loaded WITHOUT errors.
curl -s "${PROMETHEUS_URL}/api/v1/rules" \
  | jq '.data.groups[].rules[] | select(.name == "HelianthusV8ShadowWouldHaveDroppedGrowing") | .lastError // empty'

# 3. Query the actual counter value at the time of the
#    promotion decision (must be 0 OR explainable by known
#    AA-injection events).
curl -s -G "${PROMETHEUS_URL}/api/v1/query" \
  --data-urlencode 'query=helianthus_v8_shadow_would_have_dropped_total' \
  | jq '.data.result[] | { instance: .metric.instance, value: .value[1] }'
```
