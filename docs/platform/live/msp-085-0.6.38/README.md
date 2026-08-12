# MSP-085 0.6.38 Live Promotion Lock

This directory publishes the exact `PUBLIC_REDACTED` outputs from the final
VR940/eBUS coexistence and captured multi-leaf promotion run. The source
gateway commit was
`1e9c1d7ce19200a6dff79e32bc8ed6cf3ba6657c`; the deployed binary SHA-256 was
`c71afac7eeeccdbf55ede21a5d14a437eb69492b02e35d10853b5b93cba33310`.

The source-bound M8 verifier returned `PASS` after the restart-separated PRE
and POST captures. The M8 evidence and report are:

- evidence ID `mrcv1:sha256:6451b85ce81dfed4a562180febb2fb3ab5abfe9979937036eb1e247e12e5fd1d`;
- report ID `mrcrv1:sha256:d696ccce9d59625ac60ea3e11b92859f85637fa2a728a99fc171171c30797f76`;
- exact evidence bytes SHA-256
  `861c94987a361707c4b38642322e6fd4d1952c690fc8e49c687da5e85a67a2a2`;
- exact report bytes SHA-256
  `dd6e38b66e1b42f204069acf7f3515b772f77eb4848f8bb62ef3112c4e4deaa1`.

The bound M8.5 verifier returned `PASS`. Its public result has SHA-256
`585ba6c2bf3f7eb9d6833e6b204a8d72a6baf0023a11d1bb863b3d6ad9ed5e91`
and result hash
`sha256:5dd9ace033f8738fecb7a4103ac0bb22d1fe5c72cf5b78faac892ecea13f7670`.
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
