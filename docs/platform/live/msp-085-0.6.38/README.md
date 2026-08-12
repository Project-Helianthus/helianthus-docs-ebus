# MSP-085 0.6.38 Live Promotion Lock

This directory publishes the exact `PUBLIC_REDACTED` outputs from the final
VR940/eBUS coexistence and captured multi-leaf promotion run. The source
gateway commit was
`1e9c1d7ce19200a6dff79e32bc8ed6cf3ba6657c`; the deployed binary SHA-256 was
`c71afac7eeeccdbf55ede21a5d14a437eb69492b02e35d10853b5b93cba33310`.

The source-bound M8 verifier returned `PASS` after the restart-separated PRE
and POST captures. The M8 evidence and report are:

- evidence ID `mrcv1:sha256:341a5b3b83c838174fe4fed3e2bdcf7df5d8a688403e5e66276637960b3543e9`;
- report ID `mrcrv1:sha256:ce81b3ad6cf113aca11ee6cd7a620275dae41ae50e6b50057693176959b58894`;
- exact evidence bytes SHA-256
  `9959206059a091a3805ab87e6dab6db753672c4fe03b453496260be2fb02b7c5`;
- exact report bytes SHA-256
  `f211ab24f3718af21d6f414385f1554dacf654b610fb4f5b7695d57b0743424d`.

The bound M8.5 verifier returned `PASS`. Its public result has SHA-256
`a0b41745f675e234f11729b2730bd640f04b673d4b8c97e3d0b56cc74ddb5b1e`
and result hash
`sha256:3c3c76f6a0541806fe808ea7438b6291736e53a97562f4879dca42612148109b`.
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
