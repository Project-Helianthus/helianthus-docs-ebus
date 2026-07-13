#!/usr/bin/env python3
"""Canonical entry point for exact cross-repository platform validation."""

from __future__ import annotations

import argparse
import pathlib

import validate_platform_contracts as contracts


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    result.add_argument("--docs-ebus-root", type=pathlib.Path, required=True)
    result.add_argument("--docs-eebus-root", type=pathlib.Path, required=True)
    result.add_argument("--eebusreg-root", type=pathlib.Path, required=True)
    result.add_argument("--docs-ebus-ref", required=True)
    result.add_argument("--docs-eebus-ref", required=True)
    result.add_argument("--eebusreg-ref", required=True)
    result.add_argument("--prior-manifest", type=pathlib.Path, required=True)
    result.add_argument("--enforce-through", choices=contracts.MILESTONES, required=True)
    result.add_argument(
        "--docs-ebus-repository",
        default="Project-Helianthus/helianthus-docs-ebus",
    )
    result.add_argument(
        "--toolchain-mode",
        choices=tuple(sorted(contracts.TOOLCHAIN_MODES)),
        default="exact",
    )
    return result


def main() -> int:
    args = parser().parse_args()
    diagnostics = contracts.validate_workspace(
        docs_ebus_root=args.docs_ebus_root,
        docs_eebus_root=args.docs_eebus_root,
        eebusreg_root=args.eebusreg_root,
        mode="combined-ref",
        docs_ebus_ref=args.docs_ebus_ref,
        docs_eebus_ref=args.docs_eebus_ref,
        eebusreg_ref=args.eebusreg_ref,
        docs_ebus_repository=args.docs_ebus_repository,
        enforce_through=args.enforce_through,
        toolchain_mode=args.toolchain_mode,
        prior_manifest=args.prior_manifest,
    )
    for diagnostic in diagnostics:
        print(diagnostic)
    return 1 if diagnostics else 0


if __name__ == "__main__":
    raise SystemExit(main())
