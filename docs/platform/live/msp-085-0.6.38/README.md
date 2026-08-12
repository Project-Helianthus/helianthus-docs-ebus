# MSP-085 0.6.38 Live Promotion Lock

This directory publishes the exact `PUBLIC_REDACTED` outputs from the final
VR940/eBUS coexistence and captured multi-leaf promotion run. The source
gateway commit was
`1e9c1d7ce19200a6dff79e32bc8ed6cf3ba6657c`; the deployed binary SHA-256 was
`c71afac7eeeccdbf55ede21a5d14a437eb69492b02e35d10853b5b93cba33310`.

The source-bound M8 verifier returned `PASS` after the restart-separated PRE
and POST captures. The M8 evidence and report are:

- evidence ID `mrcv1:sha256:d439ba9dc26e002c84a65c0a480feb904d66e288a971d907f58ca0e83dd3afe9`;
- report ID `mrcrv1:sha256:e71281a70113ff504b918eeb996a5893b651eb5f77a8df606dd1124945ba90b0`;
- exact evidence bytes SHA-256
  `1b898a5d1fa836576190cc83e82ebe01abdd54705f93dd25e95b3e594cfffd14`;
- exact report bytes SHA-256
  `81dcdcffab5a4d7ddb9f784c6bc55a996ab4bf2bb5c3806b936351e96ee8a111`.

The bound M8.5 verifier returned `PASS`. Its public result has SHA-256
`cdfd6522e482ba083a5f3c964f95e953ea94e3d829321904be507952c767f460`
and result hash
`sha256:e60455126413cb8d82e9a640fe118a0ed3f4367c32dea079bb8a1bb4c6a3b204`.
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
