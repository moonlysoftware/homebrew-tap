# Maintaining the private preview

The tap is prepared for private testing only. Publishing a release, creating a
tag, changing repository visibility or replacing the preview artifacts requires
a separate owner decision. Keep credentials out of formulae, metadata, logs and
commits.

## What is pinned

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
They are not relabeled as a rebuild at the merge commit. The Mac Homebrew checks used
macOS 14, which carries an older-platform qualification warning; test the private
tap on a currently supported macOS version before making a broader Mac
installation claim.
Linux GNU remains diagnostic. Neither platform's installation checks establish
model-inference performance, and this tap offers no Intel Mac or Windows build.

## How private delivery works

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

## Check a prepared tap

Follow the installation commands in [the README](../README.md) on each claimed
platform. Record the tap revision, `preview.json` identities, operating system,
architecture, Homebrew version and terminal command results.

Check installation, `dkc --version`, `brew test`, uninstall followed by a fresh
install, and `brew reinstall` followed by another `brew test`. Keep the
installation and inference results separate. A failure remains a failure until
it has been understood and the relevant check rerun; a successful Linux run
does not establish Mac behavior.

An upgrade check needs an installed earlier version and a distinct new version.
Reinstalling `0.1.0-beta.1` is not an upgrade test. Do not claim upgrade coverage
until that transition has actually passed.

## Prepare a later preview or public release

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
