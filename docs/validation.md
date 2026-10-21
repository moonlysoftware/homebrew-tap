# Private preview checks

## Artifact origin — 21 October 2026

The preview now retrieves the same pinned archives from
`moonlysoftware/deepkit-code-history`, which retains the original source
repository's Actions runs. Artifact IDs, build identity, hashes, expiration
dates and Homebrew revision 1 are unchanged. Current source development lives
in the fresh `moonlysoftware/deepkit-code` repository.

All 25 offline helper tests, formula syntax and manifest/formula consistency
checks passed for the origin update. These checks do not repeat native
installation or upgrade qualification.

## Revision 1 — 16 October 2026

This refresh pins the artifacts from
[native run 38807128022](https://github.com/moonlysoftware/deepkit-code-history/actions/runs/38807128022),
which passed build, package, install, formula test, uninstall and reinstall on
macOS ARM and the GNU Linux diagnostic. The build commit `df73b574` and merged
main `b4e7b289` (now preserved in history) have the same Git tree. Full source CI
passed on PR #4's head:
1,416 tests passed and 17 were ignored in each Rust run.

Both downloaded archives passed the private helper's archive, binary, build
provenance and license verification. All 25 offline helper tests, formula syntax
and manifest/formula consistency checks passed. The manifest records the new
archive hashes and expiration dates; the formula uses revision 1 so the earlier
preview remains a distinct Homebrew package.

The exact private revision-0-to-1 upgrade remains untested. The native source
workflow's install/reinstall tests are not evidence of that upgrade or of model
inference. Local validation did not rebuild DKC or replace an installed package.

## Original preview — 14 October 2026

Implementation tested: `d9d53b63c1d91f623d59e79cce9b4964eb0ae210`.

- All 25 archive/helper tests passed locally and in [Ubuntu/macOS15 CI](https://github.com/moonlysoftware/homebrew-tap/actions/runs/38628582047).
- Both actual pinned archives passed size, SHA-256, clean build identity, binary
  checksum and license verification.
- The private tap cloned successfully over SSH. Authenticated `gh` retrieval
  of the Linux artifact succeeded after the source repository transfer.
- On the Linux GNU diagnostic, actual Homebrew install, lexical search/formula
  test, license checks, uninstall, fresh install, reinstall, test and uninstall
  passed. The test package was removed afterward.

The complete [receipt](https://github.com/moonlysoftware/deepkit-code-history/blob/prepare/beta-20261014/bench/results/beta-20261014/private-tap.json)
records identities and individual commands/log hashes. The Linux test used a
custom Homebrew prefix; it does not qualify a portable musl distribution.

The prior Mac archive passed native Homebrew installation in the source
workflow. This new private tap still needs its actual installation checked on
an invited, currently supported Mac. macOS CI above runs helper/formula checks,
not installation. No distinct-version upgrade or model inference is claimed.
The source project's earlier intermittent watcher CI deadline miss is still
open; these packaging checks do not resolve it. No public release is published.
