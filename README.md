# Moonly Software Homebrew tap

Install **[Deepkit Code (`dkc`)](https://github.com/moonlysoftware/deepkit-code)**
to search a repository's code, documents and Git history from the CLI or an MCP
client. The public beta supports **Apple Silicon Macs running
macOS 13 Ventura or later**. Intel Mac, Linux and Windows packages are outside
this public tap.

## Install

With Homebrew installed:

```sh
brew install moonlysoftware/tap/dkc
brew test moonlysoftware/tap/dkc
dkc --version
```

The formula downloads a checksum-pinned GitHub release archive. No GitHub
authentication or preparation helper is needed. Models are downloaded separately; the formula test uses
local lexical search without a model download or API key.

## Upgrade, reinstall or remove

Upgrade an earlier installation, including the private
`0.1.0-beta.1_1` preview, with:

```sh
brew update
brew upgrade moonlysoftware/tap/dkc
brew test moonlysoftware/tap/dkc
```

To reinstall the same package, run:

```sh
brew reinstall moonlysoftware/tap/dkc
brew test moonlysoftware/tap/dkc
```

Remove it with `brew uninstall moonlysoftware/tap/dkc`.

## Connect your project

Inside each Git repository, run:

```sh
dkc init --profile local --yes --codex
dkc index --level 1
dkc search "retry policy" --mode lexical --no-rerank
```

Use `--cursor` or `--claude` instead of `--codex` for those clients, or omit the
flag for CLI use. Generated MCP configurations use stdio, so projects do not
compete for a port. If you already configured a global HTTP entry, follow the
[configuration migration instructions](https://github.com/moonlysoftware/deepkit-code/blob/main/docs/usage.md#connect-an-mcp-client).

See [setup and usage](https://github.com/moonlysoftware/deepkit-code/blob/main/docs/usage.md)
for models and configuration, [maintenance](docs/maintaining.md) for release
verification, and the [validation record](docs/public-validation.md) for
package identities and installation checks. [Private-preview checks](docs/validation.md)
remain separate historical evidence.

The tap is licensed under [MIT OR Apache-2.0](LICENSE.md). Deepkit Code archives
include the project's licenses and bundled dependency notices.
