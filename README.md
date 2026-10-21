# Moonly Software Homebrew tap

This private tap lets invited testers install **Deepkit Code (`dkc`)**, a tool
that indexes a repository and searches its code, documents and Git history.
The current Homebrew preview is `0.1.0-beta.1_1` (revision 1). It includes
project Codex setup and the concurrent-client startup fix from
[Deepkit Code PR #4](https://github.com/moonlysoftware/deepkit-code-history/pull/4).
The binary still reports upstream version `0.1.0-beta.1`; Homebrew's revision
and the pinned build commit distinguish this package from the earlier preview.

It provides an Apple Silicon Mac build and an x86-64 GNU Linux build for
diagnostic testing. The Mac artifact passed native Homebrew checks on macOS 14;
installation still needs checking on a currently supported macOS version.
These checks do not qualify model inference. This preview uses the tested PR #4
build and its original merged source, preserved in `deepkit-code-history`.
Current development continues in `deepkit-code`; this remains a private preview.

[Recorded checks](docs/validation.md) include the actual private Linux install
and the Ubuntu/macOS helper tests. The next native check is installation on an
invited Mac.

## Install

You need Homebrew, Git, Python 3.11 or later, and the GitHub CLI (`gh`). Your
GitHub account must have access to both private repositories:
`moonlysoftware/homebrew-tap` and `moonlysoftware/deepkit-code-history`.
The verified Actions archives remain in the history repository after the source
repository rename; access to the new `deepkit-code` alone is not sufficient.
Configure GitHub SSH access for the tap and authenticate `gh` for the download:

```sh
gh auth login
brew tap moonlysoftware/tap git@github.com:moonlysoftware/homebrew-tap.git
python3 "$(brew --repository moonlysoftware/tap)/scripts/prepare-private.py"
brew install --formula moonlysoftware/tap/dkc
brew test moonlysoftware/tap/dkc
dkc --version
```

The preparation step downloads the exact pinned Actions artifact, verifies its
archive, build identity, binary and license files, then places it in Homebrew's
cache. The formula installs from that local file; it contains no credentials.
The pinned Actions artifacts expire on **14 November 2026**. This is temporary
private distribution, with no public release date promised.

If you already downloaded the exact archive through authenticated GitHub access:

```sh
python3 "$(brew --repository moonlysoftware/tap)/scripts/prepare-private.py" \
  --archive /path/to/deepkit-code-aarch64-apple-darwin.tar.gz
```

Use the corresponding Linux archive on Linux. The same verification applies.

## Update, reinstall or remove

To update an installed earlier preview, fetch the new tap and prepare its archive
before asking Homebrew to upgrade:

```sh
brew update
python3 "$(brew --repository moonlysoftware/tap)/scripts/prepare-private.py"
brew upgrade --formula moonlysoftware/tap/dkc
brew test moonlysoftware/tap/dkc
```

Then run `dkc init --codex` inside each project to create its stdio configuration.
If Codex already has a global `deepkit-code` HTTP entry, follow the
[configuration migration instructions](https://github.com/moonlysoftware/deepkit-code/blob/main/docs/usage.md#connect-an-mcp-client)
before using the project entry.

Run the preparation step again if Homebrew's cache has been cleared, then:

```sh
brew reinstall --formula moonlysoftware/tap/dkc
brew test moonlysoftware/tap/dkc
```

To remove the installed program:

```sh
brew uninstall moonlysoftware/tap/dkc
```

Both pinned archives passed native install and reinstall checks. The exact
revision-0-to-1 upgrade has not been exercised; those install checks are not an
upgrade result. See
[maintaining the tap](docs/maintaining.md) for artifact identities, checks and
the route to a public formula.
