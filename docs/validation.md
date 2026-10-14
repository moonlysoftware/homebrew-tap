# Private preview checks — 14 October 2026

Implementation tested: `d9d53b63c1d91f623d59e79cce9b4964eb0ae210`.

- All 25 archive/helper tests passed locally and in [Ubuntu/macOS15 CI](https://github.com/moonlysoftware/homebrew-tap/actions/runs/38628582047).
- Both actual pinned archives passed size, SHA-256, clean build identity, binary
  checksum and license verification.
- The private tap cloned successfully over SSH. Authenticated `gh` retrieval
  of the Linux artifact succeeded after the source repository transfer.
- On the Linux GNU diagnostic, actual Homebrew install, lexical search/formula
  test, license checks, uninstall, fresh install, reinstall, test and uninstall
  passed. The test package was removed afterward.

The complete [receipt](https://github.com/moonlysoftware/deepkit-code/blob/prepare/beta-20261014/bench/results/beta-20261014/private-tap.json)
records identities and individual commands/log hashes. The Linux test used a
custom Homebrew prefix; it does not qualify a portable musl distribution.

The prior Mac archive passed native Homebrew installation in the source
workflow. This new private tap still needs its actual installation checked on
an invited, currently supported Mac. macOS CI above runs helper/formula checks,
not installation. No distinct-version upgrade or model inference is claimed.
The source project's earlier intermittent watcher CI deadline miss is still
open; these packaging checks do not resolve it. No public release is published.
