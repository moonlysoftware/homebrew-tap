# Private preview: first run scripts/prepare-private.py to verify and cache the archive.
# Public distribution must replace file:// URLs with final reviewed release URLs.
require "json"
require "uri"

class Dkc < Formula
  desc "Local hybrid code and document search for IDE agents"
  homepage "https://github.com/moonlysoftware/deepkit-code"
  version "0.1.0-beta.1"
  revision 1
  license any_of: ["MIT", "Apache-2.0"]

  on_macos do
    depends_on arch: :arm64
    depends_on macos: :ventura
    on_arm do
      archive = HOMEBREW_CACHE/"dkc-private"/
                "9e7459a213a4970a4cd3d528f18224cb37fcafa4d23111a4b0284f74ac941840"/
                "deepkit-code-aarch64-apple-darwin.tar.gz"
      url "file://#{URI::DEFAULT_PARSER.escape(archive.to_s)}"
      sha256 "9e7459a213a4970a4cd3d528f18224cb37fcafa4d23111a4b0284f74ac941840"
    end
  end

  on_linux do
    depends_on arch: :x86_64
    on_intel do
      archive = HOMEBREW_CACHE/"dkc-private"/
                "d354782f5368a9ba2e7215d00a74b6bddaffcaa277b0f6d4c5d6a04952a15dad"/
                "deepkit-code-x86_64-unknown-linux-gnu.tar.gz"
      url "file://#{URI::DEFAULT_PARSER.escape(archive.to_s)}"
      sha256 "d354782f5368a9ba2e7215d00a74b6bddaffcaa277b0f6d4c5d6a04952a15dad"
    end
  end

  def install
    bin.install "dkc"
    pkgshare.install "THIRD_PARTY_NOTICES.md", "third-party-licenses.tar.gz"
  end

  test do
    (testpath/"retry.rs").write "pub fn should_retry(attempt: u32) -> bool { attempt < 3 }\n"
    system "git", "init", "--quiet"
    system "git", "add", "retry.rs"
    system "git", "-c", "user.name=DKC Homebrew Test", "-c",
           "user.email=homebrew@example.invalid", "commit", "--quiet", "-m", "fixture"
    ENV["DKC_MODELS_DIR"] = (testpath/"models").to_s
    system bin/"dkc", "init", "--profile", "local", "--yes", "--json"
    system bin/"dkc", "index", "--level", "1", "--json"
    result = JSON.parse(shell_output("#{bin}/dkc search should_retry --mode lexical --no-rerank --json"))
    assert_equal false, result.fetch("index").fetch("partial")
    assert result.fetch("hits").any? { |hit| hit.fetch("path") == "retry.rs" }
    status = JSON.parse(shell_output("#{bin}/dkc status --json"))
    assert_operator status.fetch("files"), :>=, 1
    assert_operator status.fetch("units"), :>=, 1
    assert_equal 0, status.fetch("queue").fetch("dead")
    assert_path_exists testpath/".deepkit/code.db"
  end
end
