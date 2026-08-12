# MSP-085 0.6.38 Live Promotion Lock

This directory publishes the exact `PUBLIC_REDACTED` outputs from the final
VR940/eBUS coexistence and captured multi-leaf promotion run. The source
gateway commit was
`1e9c1d7ce19200a6dff79e32bc8ed6cf3ba6657c`; the deployed binary SHA-256 was
`c71afac7eeeccdbf55ede21a5d14a437eb69492b02e35d10853b5b93cba33310`.

The source-bound M8 verifier returned `PASS` after the restart-separated PRE
and POST captures. The M8 evidence and report are:

- evidence ID `mrcv1:sha256:ee8c015d0c6ff5702d33d74bac1a96e1d16cceea7000c1b1a6a9d6c23522f3a0`;
- report ID `mrcrv1:sha256:6852c0ecfb389c814323d2780a940f724ae4d1089b768b3416e3a4bfd4e377e4`;
- exact evidence bytes SHA-256
  `a55a17eb24b965debf218dcb8e4d2b49d5bdde284aa642bea729c35d8acac789`;
- exact report bytes SHA-256
  `5266db89e4086e61b88d0242233bdffe7a05422efdacfeca4fb04e3239cc6457`.

The bound M8.5 verifier returned `PASS`. Its public result has SHA-256
`98c5b9a6dc176b64a7e56baeec31ba869ff4c24498804e79cd86678bd74c4f7e`
and result hash
`sha256:58bb1085386420728222362558746b3330aab43cf2c15e05f1e9cf7840535ee3`.
It records `VALID_PROMOTION_LOCK`, `8` promoted candidates, `10` withheld
candidates, and `READY_FOR_M9_PLANNING`.

Promoted candidate IDs are `m7-candidate-0007`, `m7-candidate-0009`,
`m7-candidate-0010`, `m7-candidate-0011`, `m7-candidate-0014`,
`m7-candidate-0015`, `m7-candidate-0016`, and `m7-candidate-0018`. Every one
remains `LOCKED_NOT_EXPOSED`. This completion record does not expose a consumer
API and does not authorize GraphQL, Portal, Home Assistant, command-routing, or
mutable-control work. Those remain separate M9 planning and implementation
steps.

The private campaign, raw operational identities, source addresses, trust
store, and cryptographic material are deliberately not published. The exact
private input bytes remain bound indirectly by the public result's
`private_campaign_bytes_hash`; verifying the live result still requires the
owner-held private inputs defined by the canonical validator contract.
