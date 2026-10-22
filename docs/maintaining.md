# Maintaining the tap

**Public beta published — 22 October 2026.** The owner approved publication of
`0.1.0-beta.2` for Apple Silicon macOS 13 or later. This tap and the release
downloads are public; the source history repository remains private. See the
[validation record](public-validation.md) for exact package identities and checks.
Future releases and visibility changes still require owner authorization.
Keep credentials out of formulae, metadata, logs and commits.

## Prepare the public formula

1. Require passing source checks and a clean native build at the reviewed
   candidate commit. Inspect the actual archive's safe layout, required
   `BUILD.json`, exact version, target, commit and source hash. Reject diagnostic
   or dirty builds. Verify the executable, project licenses, third-party notices
   and dependency license bundle. The complete archive must fit within
   50,000,000 bytes.
2. Create `release.json` from those verified bytes using the contract below.
   Do not put placeholder identities in the manifest or formula. Preserve the
   original archive and the verification receipt.
3. Use the source repository's `scripts/release/brew-formula.py` to generate
   `Formula/dkc.rb` from that same archive, with only
   `aarch64-apple-darwin` selected. The formula must require macOS Ventura and
   ARM64, use the real release URL and checksum, and omit the private preview's
   old Homebrew revision for the new upstream version.
4. Run the offline tap checks below. Separately record native fresh-install,
   upgrade from `0.1.0-beta.1_1`, formula test and reinstall results against
   these exact bytes. A reinstall is not an upgrade test, and installation
   does not qualify model-inference performance.
5. Present the complete source, archive, formula and validation record for
   owner review. After authorized publication, verify the public tap and exact
   asset download without credentials, then repeat the documented install
   path before advertising it.

Public installation must not depend on private repository access, authenticated
URLs, Actions artifact retention, local `file://` cache entries or
`scripts/prepare-private.py`. Keep the existing preview metadata and helper
unchanged as historical tooling; they are not public-install prerequisites.
Intel Mac and Linux distribution need their own native qualification before
being added to this public formula.

## Public release record

The checker accepts the flat [`release.json`](../release.json) record with these
schema-1 fields:

- `schema` is `1`; `distribution` is `github-release`.
- `version` is the binary's actual release version; `release_tag` is that version
  prefixed with `v`.
- `source_commit` and `source_blake3` identify the reviewed clean source in
  `BUILD.json`.
- `target` is `aarch64-apple-darwin`; `archive` is
  `deepkit-code-aarch64-apple-darwin.tar.gz`.
- `bytes` and `sha256` pin the complete archive.
- `binary_sha256` and `notice_bundle_sha256` pin `dkc` and
  `third-party-licenses.tar.gz`.
- `license_sha256` pins exactly `LICENSE.md`, `LICENSE-MIT`, `LICENSE-APACHE`
  and `THIRD_PARTY_NOTICES.md`.

The sole download URL is derived from
`https://github.com/moonlysoftware/deepkit-code/releases/download/` followed by
the exact release tag and archive name. The manifest does not accept alternate
repositories or download URLs. Its fields describe reviewed bytes; they do not
by themselves prove that those bytes are publicly available or qualified.

## Offline checks

```sh
python3 scripts/check.py
ruby -c Formula/dkc.rb
python3 -m unittest discover -s tests -v
```

The checker selects `release.json` when present and otherwise checks the
existing `preview.json` formula. It checks recorded identities, formula
consistency and local documentation links; it does not download or inspect a
native archive. The unit tests use synthetic fixtures. Neither offline check
establishes a working public download, native installation or upgrade.

Keep the terminal exit status and exact source, archive and tap revisions in
the validation record. A failure remains recorded until understood and the
relevant check rerun; a successful Linux diagnostic does not establish Mac
behavior. Record current results in [public validation](public-validation.md);
[historical validation](validation.md) remains separate from those results.

## Historical private preview

The following record preserves the existing preview's delivery mechanism,
artifact identities, completed checks and earlier transition requirements.
It is not qualification of the public `0.1.0-beta.2` package. Current installation
uses the public formula in [the README](../README.md).

### Pinned private-preview artifacts

[`preview.json`](../preview.json) is the record of the accepted artifact
identities. The upstream version is `0.1.0-beta.1`, with Homebrew revision 1
(`0.1.0-beta.1_1`), from
[Actions run 38807128022](https://github.com/moonlysoftware/deepkit-code-history/actions/runs/38807128022):

- PR source head: `156a0eccc328c871bfedceafec8e25444ff38439`.
- Artifact build commit: `df73b574bf26fb7befd01a1b1881810b32255d35`.
- Original merged main commit: `b4e7b289f0f94673987bd17d638bcc743071d099`.
- Both commits have Git tree `7ebf819c0818e3fb829c990f662f6c80862c1c9b`.
- Source BLAKE3: `f0f9d5afe4df53ead9f9a71c3481519098aa393b3a4e03b3cd3fe840da65a37e`.

| Target | Actions artifact ID | Download expiration (UTC) |
| --- | --- | --- |
| Apple Silicon, `aarch64-apple-darwin` | `12007981747` | 14 November 2026, 21:24:29 |
| GNU Linux diagnostic, `x86_64-unknown-linux-gnu` | `12008217369` | 14 November 2026, 21:32:50 |

The manifest also pins archive names, sizes and SHA-256 values, binary hashes
and license identities. Preserve that connection to the tested artifacts.
Do not substitute a newer run, a similarly named artifact or a different binary
under an unchanged Homebrew package version and revision. A private refresh at
the same upstream version must increment `brew_revision` in the manifest and
`revision` in the formula together, following
[Homebrew's revision mechanism](https://docs.brew.sh/Formula-Cookbook#formulae-revisions).
The manifest's `version` continues to match the binary's embedded version;
never relabel the artifact's actual build commit or version.

These are tested PR artifacts with the same source tree as the original merge.
They are not relabeled as a rebuild at the merge commit. The source workflow's
Mac Homebrew checks used macOS 14, which carries an older-platform warning.
The private revision-0-to-1 upgrade subsequently passed on macOS 26.3.1(a) with
Homebrew 7.0.6. That host reported Xcode/Command Line Tools Tier 2 warnings, so
the result does not establish full platform qualification.
Linux GNU remains diagnostic. Neither platform's installation checks establish
model-inference performance, and this tap offers no Intel Mac or Windows build.

### Private installation and updates

These archived instructions describe tap commit `2399183` and its private
`0.1.0-beta.1_1` preview. They do not apply to current `main`. The preview
included project Codex setup and concurrent-client startup fixes
from [Deepkit Code PR #4](https://github.com/moonlysoftware/deepkit-code-history/pull/4).
The binary reports upstream version `0.1.0-beta.1`; the Homebrew revision and
build identity distinguish it from the earlier preview.

You need Homebrew, Git, Python 3.11+ and the GitHub CLI, with access to both
`moonlysoftware/homebrew-tap` and `moonlysoftware/deepkit-code-history`.
Access to the public source repository alone is insufficient. With GitHub SSH
access configured for the tap:

```sh
gh auth login
brew tap moonlysoftware/tap git@github.com:moonlysoftware/homebrew-tap.git
python3 "$(brew --repository moonlysoftware/tap)/scripts/prepare-private.py"
brew install --formula moonlysoftware/tap/dkc
brew test moonlysoftware/tap/dkc
dkc --version
```

For an earlier private preview, prepare the updated archive before upgrading:

```sh
brew update
python3 "$(brew --repository moonlysoftware/tap)/scripts/prepare-private.py"
brew upgrade --formula moonlysoftware/tap/dkc
brew test moonlysoftware/tap/dkc
```

If the cache has been cleared, run the helper again before
`brew reinstall --formula moonlysoftware/tap/dkc`, then repeat `brew test`.
An already downloaded exact archive can be verified and prepared with the
helper's `--archive PATH` option; select the archive for the actual host.
The private GNU Linux build is diagnostic only. The pinned downloads expire
on **14 November 2026**. See [recorded checks](validation.md) for completed
private native install/reinstall and Mac upgrade results and their limitations.

### How private delivery works

Git fetches the private tap over SSH. The preparation helper separately uses
the user's authenticated `gh` session to retrieve the pinned Actions artifact
from `moonlysoftware/deepkit-code-history`. Access to one repository does not imply
access to the other. The history repository retains the original commits, PRs,
Actions runs and artifacts; the fresh `moonlysoftware/deepkit-code` repository
contains current development. Do not rely on the old repository-name redirect:
that name now belongs to the fresh repository.

Changing this artifact origin does not change archive bytes, build identity,
checksums, expiration dates or Homebrew revision. The helper accepts only the
reviewed history repository for this preview. A future preview built in the
current source repository needs its own reviewed manifest and helper update.

The helper validates the archive and its build, binary and license identities
before seeding:

```text
$(brew --cache)/dkc-private/<archive-sha256>/<archive-name>
```

`Formula/dkc.rb` derives its `file://` URL from Homebrew's cache location. It
must not contain a maintainer's machine path, token or authenticated download
URL. Run the helper before installation and after clearing the cache.

The helper's `--archive PATH` option accepts an already downloaded archive and
performs the same verification. This supports authenticated manual downloads;
it does not relax the pinned identities. Actions retention is temporary:
prepare and qualify replacement artifacts before expiration if testing must
continue. Retaining a verified archive is useful, but is not a public release.

### Private-preview verification

Follow the private installation commands above on each claimed platform. Record the tap revision, `preview.json` identities, operating system,
architecture, Homebrew version and terminal command results.

Check installation, `dkc --version`, `brew test`, uninstall followed by a fresh
install, and `brew reinstall` followed by another `brew test`. Keep the
installation and inference results separate. A failure remains a failure until
it has been understood and the relevant check rerun; a successful Linux run
does not establish Mac behavior.

An upgrade check needs an installed earlier version and a distinct new version.
Reinstalling `0.1.0-beta.1` is not an upgrade test. Do not claim upgrade coverage
until that transition has actually passed.

### Earlier transition requirements

For another private preview, first qualify the intended source revision and
native artifacts. Review the new version, run and artifact IDs, archive sizes,
checksums, embedded provenance, license files and retention dates together.
Update the manifest and formula consistently, then repeat the native private-tap
checks before inviting testers to use it.

For public distribution, rebuild the reviewed final source and qualify those
exact final archives. Use the source repository's `scripts/release/brew-formula.py`
generator to create a formula bound to their real download URLs and checksums.
Public formulae must not retain these private `file://` URLs or depend on Actions
artifact retention, private repository access or `prepare-private.py`.
Verify the generated formula's actual install and test flow before publication;
the private preview is not evidence that this later public flow has passed.
