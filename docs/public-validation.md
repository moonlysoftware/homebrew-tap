# Public beta candidate validation — 22 October 2026

**Prepared, not published.** The Apple Silicon `0.1.0-beta.2` archive is verified
and pinned in [`release.json`](../release.json) and [the formula](../Formula/dkc.rb).
The release asset and tag are not published, and the tap remains private.
Source CI, hosted native install/reinstall and the local preview-to-beta.2
upgrade passed. Anonymous public installation remains pending.
[Private-preview results](validation.md) are separate historical evidence.

## Exact candidate

| Identity | Value |
| --- | --- |
| Upstream version / intended release tag | `0.1.0-beta.2` / `v0.1.0-beta.2` |
| Reviewed source commit | `f9abf48625e012c572b22fdcc13514acea70dfb2` |
| Source BLAKE3 | `5a9b1ff78a29629ec4ab09d428ca260e94015eb447571e7126f50ded42fcd8eb` |
| Public target | `aarch64-apple-darwin` |
| Archive | `deepkit-code-aarch64-apple-darwin.tar.gz` |
| Archive size | 28,129,829 bytes, within the 50,000,000-byte cap |
| Archive SHA-256 | `f0715158b7538c0de56d8f56d8b268f1a6a04d94d5baf061de87b3efff180875` |
| Binary SHA-256 | `0e6cb06ddac3823f955b3c6bde1663e9b064ff5c4d13d5fa458bee03a8072c4e` |
| Dependency notice bundle SHA-256 | `8697564977aeb694b60a1b94f1f64d33306942b3e0044ac17f3067921761c6bc` |
| Native Actions artifact ID | `12422850785` |

The selected archive comes from the
[exact-commit native run 39768490488](https://github.com/moonlysoftware/deepkit-code/actions/runs/39768490488),
not a relabeled PR merge build. Verification covered the archive's safe layout,
required clean `BUILD.json` identity, executable hash, four license-file hashes
and complete dependency notice bundle. The manifest retains those identities.
The formula was generated directly from these bytes with the source repository's
release helper and explicitly selects only Apple Silicon macOS 13 or later.

## Completed checks

| Check | Evidence and scope |
| --- | --- |
| Source quality gates | [Push CI 39768451978](https://github.com/moonlysoftware/deepkit-code/actions/runs/39768451978) and [PR CI 39768457167](https://github.com/moonlysoftware/deepkit-code/actions/runs/39768457167) passed formatting, strict Clippy, 1,416 Rust tests (17 ignored), 39 release-tool tests, 100 benchmark-tool tests and dependency checks at the candidate commit. |
| Exact-commit native packaging and Homebrew lifecycle | [Run 39768490488](https://github.com/moonlysoftware/deepkit-code/actions/runs/39768490488) passed on macOS ARM and the Linux GNU diagnostic. The selected ARM job used macOS 15.7.9 and a macOS 13 deployment target. |
| PR native packaging and Homebrew lifecycle | [Run 39768457278](https://github.com/moonlysoftware/deepkit-code/actions/runs/39768457278) also passed both jobs for the candidate. This is separate supporting evidence; the pinned archive is from the exact-commit run above. |
| Local preview-to-beta.2 upgrade | Upgrade from `0.1.0-beta.1_1` to the pinned `0.1.0-beta.2` archive and the following formula test passed on Apple Silicon; [details and limits](#local-upgrade) below. |
| Tap manifest and generated formula | `python3 scripts/check.py` passed against the real release pins and canonical public URL. |
| Offline tap regression suite | `python3 -m unittest discover -s tests -v`: 41 passed, including 16 public pin cases and 25 historical private-helper cases. |
| Formula syntax and patch formatting | `ruby -c Formula/dkc.rb` and `git diff --check` passed. |

The native jobs installed and tested the package, uninstalled it, installed it
again, reinstalled it and repeated the formula test. They used local archive
URLs before publication. The test exercises initialization, level-1 indexing,
lexical search and status without a model download or API key. These results
do not establish the public HTTPS download path, an upgrade from the old
preview, model-inference performance or a Linux public distribution.

## Local upgrade

On 22 October 2026, from 11:34:24 to 11:34:30 UTC, the installed private
`0.1.0-beta.1_1` preview upgraded to `0.1.0-beta.2` and `brew test` passed.
The test used a local copy of the exact pinned archive; the test and public
formulas differed only in their download URL. The installed executable,
dependency notice bundle and all four license files matched `release.json`.
The binary reported `dkc 0.1.0-beta.2`.

The host ran macOS 26.3.1(a) on ARM64 with Homebrew 7.0.6, Xcode 26.5 and
Command Line Tools 26.0. Homebrew reported outdated toolchain warnings and
classified the configuration as Tier 2. No toolchain changes were made. This
is a successful bounded package upgrade and lexical-search test, without model
downloads, API calls or inference qualification.

The installed tap was restored to its original clean commit
`239918376b2940b755a73c74b505ef9365b04932`, including the original formula's exact
bytes and mode. The earlier `0.1.0-beta.1` and `0.1.0-beta.1_1` keg binary hashes
remained unchanged. The new beta.2 installation is retained. The local receipt
records both command exit statuses, installed hashes and restoration checks.

## Pending checks and publication

- Owner approval for release/tag publication and public tap visibility.
- Anonymous fetch of the published tap and exact release archive, then the
  documented public install path and formula test.

Retain the preparation banner until the public path passes. See
[maintenance](maintaining.md) for the verification and publication sequence.
