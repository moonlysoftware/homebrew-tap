"""Public tap pin checks using synthetic metadata; no downloads or Homebrew."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/check.py"
SPEC = importlib.util.spec_from_file_location("tap_check", SCRIPT)
tap_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tap_check)


class PublicReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="dkc-public-tap-test-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "Formula").mkdir()
        (self.root / "docs").mkdir()
        for name in ("README.md", "LICENSE.md", "docs/maintaining.md"):
            (self.root / name).write_text("Synthetic offline test fixture.\n")
        self.pins = {
            "schema": 1,
            "distribution": "github-release",
            "version": "0.1.0-beta.2",
            "release_tag": "v0.1.0-beta.2",
            "source_commit": "1" * 40,
            "source_blake3": "2" * 64,
            "target": "aarch64-apple-darwin",
            "archive": "deepkit-code-aarch64-apple-darwin.tar.gz",
            "bytes": 12345,
            "sha256": "3" * 64,
            "binary_sha256": "4" * 64,
            "notice_bundle_sha256": "5" * 64,
            "license_sha256": {name: "6" * 64 for name in tap_check.LICENSES},
        }
        self.url = (f'{tap_check.RELEASE_BASE}/{self.pins["release_tag"]}/'
                    f'{self.pins["archive"]}')
        self.formula = f'''class Dkc < Formula
  version '{self.pins["version"]}'
  depends_on macos: :ventura
  depends_on arch: :arm64
  on_macos do
    on_arm do
      url '{self.url}'
      sha256 "{self.pins["sha256"]}"
    end
  end
end
'''
        (self.root / "Formula/dkc.rb").write_text(self.formula)
        self.write_manifest(self.pins)

    def write_manifest(self, pins):
        path = self.root / "release.json"
        path.write_text(json.dumps(pins))
        return path

    def test_accepts_public_release_without_private_helper_or_manifest(self):
        self.assertIn("match the public release", tap_check.check(self.root))

    def test_accepts_literal_single_or_double_quotes(self):
        tap_check.check_release_formula(self.formula.replace("'", '"'), self.pins)

    def test_rejects_manifest_schema_and_identity_drift(self):
        cases = (
            ("schema", True), ("schema", 2),
            ("distribution", "actions-artifact"),
            ("release_tag", "v0.1.0-beta.1"),
            ("source_commit", "main"), ("source_commit", "a" * 39),
            ("source_blake3", "B" * 64), ("sha256", "3" * 63),
            ("binary_sha256", None), ("notice_bundle_sha256", 123),
            ("target", "x86_64-apple-darwin"),
            ("target", "x86_64-unknown-linux-gnu"),
            ("archive", "../deepkit-code-aarch64-apple-darwin.tar.gz"),
            ("bytes", True), ("bytes", 0), ("bytes", 50_000_001),
            ("bytes", "12345"),
        )
        for key, value in cases:
            with self.subTest(key=key, value=value):
                pins = dict(self.pins, **{key: value})
                with self.assertRaises(ValueError):
                    tap_check.release_manifest(self.write_manifest(pins))

    def test_rejects_missing_or_additional_manifest_fields(self):
        for pins in (None, [], {}, dict(self.pins, url="https://example.invalid/archive"),
                     {key: value for key, value in self.pins.items() if key != "source_commit"}):
            with self.subTest(pins=pins):
                with self.assertRaisesRegex(ValueError, "manifest fields"):
                    tap_check.release_manifest(self.write_manifest(pins))

    def test_rejects_missing_extra_or_invalid_license_pins(self):
        cases = (None, {}, {"LICENSE.md": "6" * 64},
                 dict(self.pins["license_sha256"], **{"extra.txt": "6" * 64}),
                 dict(self.pins["license_sha256"], **{"LICENSE.md": "bad"}))
        for licenses in cases:
            with self.subTest(licenses=licenses):
                pins = dict(self.pins, license_sha256=licenses)
                with self.assertRaisesRegex(ValueError, "license"):
                    tap_check.release_manifest(self.write_manifest(pins))

    def test_accepts_release_and_prerelease_versions(self):
        for version in ("0.1.0-beta.2", "1.2.3", "1.2.3-rc.1"):
            with self.subTest(version=version):
                pins = dict(self.pins, version=version, release_tag=f"v{version}")
                self.assertEqual(tap_check.release_manifest(self.write_manifest(pins)), pins)

    def test_rejects_malformed_or_interpolated_versions(self):
        for version in (None, "v0.1.0", "0.1", "00.1.0", "0.1.0-beta.01",
                        "0.1.0-rc..1", "0.1.0+build", "0.1.0-#{ENV['TOKEN']}"):
            with self.subTest(version=version):
                pins = dict(self.pins, version=version, release_tag=f"v{version}")
                with self.assertRaisesRegex(ValueError, "release SemVer"):
                    tap_check.release_manifest(self.write_manifest(pins))

    def test_rejects_alternate_download_sources_and_version(self):
        urls = (
            self.url.replace("https://", "http://"),
            self.url.replace("deepkit-code/releases", "deepkit-code-history/releases"),
            self.url.replace("github.com/", "github.com.example.invalid/"),
            self.url.replace("v0.1.0-beta.2", "v0.1.0-beta.1"),
            self.url + "?token=synthetic", "file:///tmp/synthetic.tar.gz",
        )
        for url in urls:
            with self.subTest(url=url):
                with self.assertRaisesRegex(ValueError, "formula url"):
                    tap_check.check_release_formula(self.formula.replace(self.url, url), self.pins)

    def test_rejects_formula_version_and_checksum_drift(self):
        for old, new, label in (("version '0.1.0-beta.2'", "version '0.1.0-beta.1'", "version"),
                                (self.pins["sha256"], "7" * 64, "sha256")):
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError, f"formula {label}"):
                    tap_check.check_release_formula(self.formula.replace(old, new), self.pins)

    def test_rejects_duplicate_or_dynamic_formula_pins(self):
        for name, directive in (("url", f"url '{self.url}'"),
                                ("version", "version '0.1.0-beta.2'"),
                                ("sha256", f'sha256 "{self.pins["sha256"]}"')):
            for changed in (self.formula + directive + "\n",
                            self.formula.replace(directive, f"{name} ENV['SYNTHETIC']")):
                with self.subTest(name=name, formula=changed):
                    with self.assertRaisesRegex(ValueError, f"formula {name}"):
                        tap_check.check_release_formula(changed, self.pins)

    def test_rejects_missing_platform_requirements(self):
        for requirement in ("  depends_on macos: :ventura\n", "  depends_on arch: :arm64\n"):
            with self.subTest(requirement=requirement):
                with self.assertRaisesRegex(ValueError, "require macOS Ventura and Apple Silicon"):
                    tap_check.check_release_formula(self.formula.replace(requirement, ""), self.pins)

    def test_rejects_stale_revision_mirrors_and_unqualified_platforms(self):
        for directive in ("revision 1", "mirror 'https://example.invalid/synthetic'",
                          "on_linux do\nend", "on_intel do\nend"):
            with self.subTest(directive=directive):
                with self.assertRaises(ValueError):
                    tap_check.check_release_formula(self.formula + directive + "\n", self.pins)

    def test_rejects_private_delivery_dependencies(self):
        for value in ("file://", "HOMEBREW_CACHE", "dkc-private", "prepare-private",
                      "deepkit-code-history"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "private preview delivery"):
                    tap_check.check_release_formula(self.formula + f"# {value}\n", self.pins)

    def test_invalid_release_does_not_fall_back_to_private_preview(self):
        self.write_manifest({})
        with mock.patch.object(tap_check, "check_preview_formula") as preview:
            with self.assertRaises(ValueError):
                tap_check.check(self.root)
            preview.assert_not_called()

    def test_absent_release_uses_existing_preview_checker(self):
        (self.root / "release.json").unlink()
        with mock.patch.object(tap_check, "check_preview_formula") as preview:
            self.assertIn("match the private preview", tap_check.check(self.root))
            preview.assert_called_once_with(self.root, self.formula)

    def test_rejects_missing_local_documentation_link(self):
        (self.root / "README.md").write_text("[Missing](docs/missing.md)\n")
        with self.assertRaisesRegex(ValueError, "missing link"):
            tap_check.check(self.root)


if __name__ == "__main__":
    unittest.main()
