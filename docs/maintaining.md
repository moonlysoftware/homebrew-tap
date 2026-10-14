# Maintaining the private preview

The tap is prepared for private testing only. Publishing a release, creating a
tag, changing repository visibility or replacing the preview artifacts requires
a separate owner decision. Keep credentials out of formulae, metadata, logs and
commits.

## What is pinned

[`preview.json`](../preview.json) is the record of the accepted artifact
identities. The current version is `0.1.0-beta.1`, from
[Actions run 38604704711](https://github.com/moonlysoftware/deepkit-code/actions/runs/38604704711):

- PR source head: `ae9f1bea535c1a92985344fb77ffa47d7776ca57`.
- Artifact build commit: `41efee5b879fb2353a5407516aa90a957fba78ee`.
- Source BLAKE3: `274521317280f0fa3bdcb7d6f7016d62684fbbf1a1527eb205befde4cf2106be`.

| Target | Actions artifact ID | Download expiration (UTC) |
| --- | --- | --- |
| Apple Silicon, `aarch64-apple-darwin` | `11915870390` | 13 November 2026, 17:25:32 |
| GNU Linux diagnostic, `x86_64-unknown-linux-gnu` | `11915354712` | 13 November 2026, 17:28:33 |

The manifest also pins archive names, sizes and SHA-256 values, binary hashes
and license identities. Preserve that connection to the tested artifacts.
Do not substitute a newer run, a similarly named artifact or a different binary
under the existing version.

These are previously tested PR artifacts. They are not a rebuild of the final
reviewed `main` branch. The Mac Homebrew checks used macOS 14, which carries an
older-platform qualification warning; test the private tap on a currently
supported macOS version before making a broader Mac installation claim.
Linux GNU remains diagnostic. Neither platform's installation checks establish
model-inference performance, and this tap offers no Intel Mac or Windows build.

## How private delivery works

Git fetches the private tap over SSH. The preparation helper separately uses
the user's authenticated `gh` session to retrieve the pinned Actions artifact
from `moonlysoftware/deepkit-code`. Access to one repository does not imply
access to the other.

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
