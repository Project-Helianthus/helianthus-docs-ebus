# MSP-085 0.6.38 Live Promotion Lock

This directory publishes the exact `PUBLIC_REDACTED` outputs from the final
VR940/eBUS coexistence and captured multi-leaf promotion run. The source
gateway commit was
`1e9c1d7ce19200a6dff79e32bc8ed6cf3ba6657c`; the deployed binary SHA-256 was
`c71afac7eeeccdbf55ede21a5d14a437eb69492b02e35d10853b5b93cba33310`.

The source-bound M8 verifier returned `PASS` after the restart-separated PRE
and POST captures. The M8 evidence and report are:

- evidence ID `mrcv1:sha256:67b7ded6a64e07e2da8f714c2ef905d9debc615bef6ef35dd515e322e6cf2317`;
- report ID `mrcrv1:sha256:5f44c5e3cfe731d0b8ce7140cb1784098916786bc3eea83e549e50b5dc1e5060`;
- exact evidence bytes SHA-256
  `a14fec7d2f4c268f997ff2940b0bc36aeacddc0fb34c91f31235b4976b7159bf`;
- exact report bytes SHA-256
  `5c4809ab22c1326ee13a689813d977ba8348a2f3084ca42089e674e2310a470c`.

The bound M8.5 verifier returned `PASS`. Its public result has SHA-256
`b80c1a8b7320e9637f6268660d7a67b14399f35b8af63cff3f07b3a5dae2ce03`
and result hash
`sha256:1c2b518dd044c32fb4d3a05b3510e7a747c5b8ebb670d87f911d26024f769219`.
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
