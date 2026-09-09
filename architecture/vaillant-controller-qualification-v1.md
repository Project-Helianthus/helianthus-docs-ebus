# Vaillant controller qualification evidence gap v1

The accepted B524 thermal mapping remains native and read-only, but it has no
publishable direct Identification artifact that can qualify a controller for
runtime use. Its evidence conclusion is `Unknown`; this document is an evidence-gap record, not an
applicability rule and not a documentation gate for registry authority.

## What the public artifact establishes

The exact public artifact named and hashed in
`architecture/fixtures/vaillant-controller-qualification-v1.json` is the B555
timer protocol document at repository revision
`055738bbad31f5cfe7fcd87bffc16bc09e021571`. Its validation-environment
summary records BASV2 at address `0x15`, HW `1704`, and SW `0507`.

The byte-identical snapshot retains four relative B524 references. Their exact
same-revision target is separately materialized beside the snapshot, with its
source path and digest recorded in the fixture. The validator enumerates every
relative snapshot link and verifies that its local target resolves to those
pinned bytes.

It does not contain a directed `0x07/0x04` request and response, the complete
Identification payload, or the raw `0xB5` manufacturer byte for that BASV2
tuple. The generic service documents the Identification layout and the
Vaillant manufacturer byte, but does not connect those facts to this exact
controller observation. No range, family, product, firmware, or hardware
qualification follows from the summary.

## Required evidence before qualification

A future rule needs a public, sanitized, reproducible artifact that shows the
same exact address in directed `0x07/0x04` request and response context and
contains raw manufacturer, device-ID, software, and hardware members. It must
also bind an immutable canonical repository URL, repository revision, path,
and digest. The registry separately needs a current complete
manufacturer/device/serial witness; a direct Identification payload has no
serial field.

Until that artifact exists, `qualified_use_permitted` is false. The B524 map
may not obtain a registry qualification, SemReg source/binding, gateway
publication, consumer state, operation authority, or live qualification from
this record.

## Transition boundary

Malformed or incomplete candidate input is rejected without mutation. A valid,
direct current observation that conflicts with an already-qualified proof must
atomically retire that proof. A matching sparse refresh may retain an existing
direct proof, but cannot construct one from last-known-good fields.
