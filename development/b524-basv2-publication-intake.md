# Controller-family publication intake checklist

This application-development checklist is a partial slice of docs issue #574
(Refs #574; issue #591). It admits no native profile or registry bound. Publishing
observations belongs to Explorer #303; shared fixture refresh belongs to Explorer
#299; acquisition and a native profile remain with #574 and registry admission
with ebusreg #176. No observations or new schema are published here.

## Three independent decisions

- [ ] **Implementation observation intake:** sanitized decoded descriptions and
  selector inventories may be published as **Hypothesis**, with their source,
  omissions and nonclaims. They are corroborating implementation evidence, not
  native wire proof. Do not reproduce the existing observation collection here.
- [ ] **Native qualification:** apply the [native evidence rules](../AGENTS.md#ebus-native-evidence-rules)
  and [description format and evidence limits](../protocols/vaillant/ebus-vaillant-b524-basv0-profile-v1.md#native-description-format).
  Missing raw descriptions or request provenance blocks native profile
  qualification. Record retained facts as **Proven** only within their evidence;
  interpretations as **Hypothesis** and omitted context as **Unknown**.
  These evidence labels are distinct from codec `qualification` and `codec_provenance`.
- [ ] **Registry admission:** separately review the qualified native artifact
  under the registry's admission process. Publication, schema validity, profile
  match and decoded values cannot reconstruct missing bytes or justify wider
  write limits. Missing raw descriptions/provenance blocks registry bound
  admission. Retain partial last-known-good evidence without promoting an
  incomplete replacement; fail closed for unsupported identity or selectors.

## Identity and retained evidence

Use the existing [description schema](../protocols/vaillant/fixtures/b524-basv0-description-profile-schema-v1.json)
for exact field vocabulary: `local_profile.eid`, `software_raw`, `hardware_raw`,
`api_version_raw` and `api_revision_raw`. Keep the last two independent, never
collapse them to “API1”: [OP00 identifiers](../protocols/vaillant/fixtures/b524-op00-system-information-ids.csv)
assign version to `0006` and revision to `0007`. This schema pins BASV0 constants;
its field vocabulary is a reference; it does not admit another controller family. Unknown
identity fields must remain Unknown in intake notes, not fabricated schema values.

Retain `selector.operation`, `group`, `instance`, `register` (opcode/GG/II/RR).
OP02 and OP06 remain separate namespaces. Preserve the corresponding OP01/OP07
request bytes and request/reply correlation: response echoes alone do not prove
opcode or instance. See [acquisition provenance](ebus-vaillant-b524-description-acquisition.md#422-targeted-acquisition).
Keep `raw_description_hex`, `description_payload_length`, `raw_limits` and
`decoded` separate; preserve `identity_scope`, `remote_identity`, `access_flags`,
`presence_state`, `response_state` and `observed_read_payload_width` without
upgrading derived state to native proof.

Mark missing native provenance and firmware context as **Unknown**. Retain only
sanitized, nonidentifying context supported by the evidence; never fill missing
native provenance from a UI label. Publish controller families and remove private
or identifying details. This checklist authorizes no acquisition or live write.

## Mechanical publication review

| Review | Required evidence and disposition |
| --- | --- |
| Evidence source | Repository-relative artifact reference, public source and transformation/decoder basis; separate retained bytes from implementation interpretation. |
| Omission markers | Enumerate Unknown context; preserve typed schema states where applicable. Do not insert prose markers into typed fields. |
| Digest | Compute SHA-256 over the exact sanitized artifact; verify packaged/published byte identity under the [shared evidence contract](https://github.com/Project-Helianthus/helianthus-vrc-explorer/blob/main/docs/shared-evidence-contract.md). A digest authenticates that artifact, not missing wire evidence. No fixture digest refresh in this ticket. |
| Native schema and semantics | Record separate schema and [semantic validator](../scripts/validate_b524_basv0_description_profile.py) results; review raw/decoded consistency, widths, selector-to-codec basis and instance invariance. The existing validator is a reference; it does not admit another controller family. New profile support belongs to #574. |
| Privacy | Inspect the sanitized artifact and diff for private data and identifying provenance; withheld details stay Unknown. Retain public native bytes alongside interpretation. |
| License lane | Application intake and overlays stay AGPL in `development/`; neutral native evidence belongs in CC0 `protocols/` only after evidence review. Run the [boundary validator](../scripts/check_public_domain_boundary.py). |

Follow the existing [profile reuse contract](ebus-vaillant-b524-basv0-profile-reuse.md)
for shared schema ownership and coordinated versioning. This checklist changes no
fixtures, hashes, bounds, application APIs, eBUS MCP compatibility or GraphQL
parity, and supplies no write-validation authority.
