# MSP-085 0.6.38 Live Promotion Lock

This directory publishes the exact `PUBLIC_REDACTED` outputs from the final
VR940/eBUS coexistence and captured multi-leaf promotion run. The source
gateway commit was
`1e9c1d7ce19200a6dff79e32bc8ed6cf3ba6657c`; the deployed binary SHA-256 was
`c71afac7eeeccdbf55ede21a5d14a437eb69492b02e35d10853b5b93cba33310`.

The source-bound M8 verifier returned `PASS` after the restart-separated PRE
and POST captures. The M8 evidence and report are:

- evidence ID `mrcv1:sha256:7896e673b08b89f1f065d43f7c3d676dec23003a34ea44008268792727a37e96`;
- report ID `mrcrv1:sha256:7e7a15de9aab34202ce4a02cd1a7b027b189a78990472ca11449e5c8c09d59a7`;
- exact evidence bytes SHA-256
  `87741a9003b24102bda2698654726fe88ad4d0046a12abdf02583eac367c2724`;
- exact report bytes SHA-256
  `948419eeef4bb0c4ee68ee2705ac642bcc02a9f99a4e38589ced9cfe38b2e354`.

The bound M8.5 verifier returned `PASS`. Its public result has SHA-256
`7cbd4b1100066a39100cc31e51bb197e4c3d3ccee3114ddb5ba8517ca44512a2`
and result hash
`sha256:b3ecc450c0a79dc1a9b0df11f3c86131f2f74652a9f2a3ae671f56d756a07797`.
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
