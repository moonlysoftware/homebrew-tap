# Moonly Software Homebrew tap

This private tap lets invited testers install **Deepkit Code (`dkc`)**, a tool
that indexes a repository and searches its code, documents and Git history.
The current preview is `0.1.0-beta.1`.

It provides an Apple Silicon Mac build and an x86-64 GNU Linux build for
diagnostic testing. The Mac artifact passed native Homebrew checks on macOS 14;
installation still needs checking on a currently supported macOS version.
These checks do not qualify model inference. This preview is built from a
tested pull request, not a public release of the final reviewed `main` branch.

## Install

You need Homebrew, Git, Python 3.11 or later, and the GitHub CLI (`gh`). Your
GitHub account must have access to both private repositories:
`moonlysoftware/homebrew-tap` and `moonlysoftware/deepkit-code`.
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
The pinned Actions artifacts expire on **13 November 2026**. This is temporary
private distribution, with no public release date promised.

If you already downloaded the exact archive through authenticated GitHub access:

```sh
python3 "$(brew --repository moonlysoftware/tap)/scripts/prepare-private.py" \
  --archive /path/to/deepkit-code-aarch64-apple-darwin.tar.gz
```

Use the corresponding Linux archive on Linux. The same verification applies.

## Reinstall or remove

Run the preparation step again if Homebrew's cache has been cleared, then:

```sh
brew reinstall --formula moonlysoftware/tap/dkc
brew test moonlysoftware/tap/dkc
```

To remove the installed program:

```sh
brew uninstall moonlysoftware/tap/dkc
```

A future upgrade needs a separately qualified version. This preview does not
establish that an upgrade between versions works. See
[maintaining the tap](docs/maintaining.md) for artifact identities, checks and
the route to a public formula.
