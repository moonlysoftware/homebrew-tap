#!/usr/bin/env python3
"""Check the active formula's reviewed pins and local documentation links offline."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = "aarch64-apple-darwin"
RELEASE_BASE = "https://github.com/moonlysoftware/deepkit-code/releases/download"
LICENSES = {"LICENSE.md", "LICENSE-MIT", "LICENSE-APACHE", "THIRD_PARTY_NOTICES.md"}
RELEASE_FIELDS = {
    "schema", "distribution", "version", "release_tag", "source_commit", "source_blake3",
    "target", "archive", "bytes", "sha256", "binary_sha256", "notice_bundle_sha256",
    "license_sha256",
}


def require(condition: bool, message: str) -> None:
    """Reject inconsistent release inputs, including when Python uses optimization."""
    if not condition:
        raise ValueError(message)


def is_digest(value: object, length: int = 64) -> bool:
    """Accept only a complete lowercase hexadecimal identity."""
    return isinstance(value, str) and re.fullmatch(rf"[0-9a-f]{{{length}}}", value) is not None


def release_manifest(path: Path) -> dict:
    """Read one public Apple Silicon release; URLs are derived, never configurable."""
    pins = json.loads(path.read_text())
    require(isinstance(pins, dict) and set(pins) == RELEASE_FIELDS,
            "release manifest fields differ from schema 1")
    require(type(pins["schema"]) is int and pins["schema"] == 1
            and pins["distribution"] == "github-release", "unsupported release manifest")
    version = pins["version"]
    require(isinstance(version, str) and re.fullmatch(
        r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
        r"(?:-(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
        r"(?:\.(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*))*)?",
        version) is not None, "version must be a release SemVer without a v prefix")
    require(pins["release_tag"] == f"v{version}", "release tag differs from version")
    require(is_digest(pins["source_commit"], 40), "invalid source commit")
    require(pins["target"] == TARGET, "public tap supports Apple Silicon macOS only")
    require(pins["archive"] == f"deepkit-code-{TARGET}.tar.gz", "invalid archive filename")
    require(type(pins["bytes"]) is int and 0 < pins["bytes"] <= 50_000_000,
            "archive size must be within the beta download limit")
    for name in ("source_blake3", "sha256", "binary_sha256", "notice_bundle_sha256"):
        require(is_digest(pins[name]), f"invalid {name}")
    licenses = pins["license_sha256"]
    require(isinstance(licenses, dict) and set(licenses) == LICENSES,
            "release must pin all four license files")
    require(all(is_digest(digest) for digest in licenses.values()), "invalid license checksum")
    return pins


def statements(formula: str, name: str) -> list[str]:
    """Find the generated formula's standalone directives without executing Ruby."""
    return re.findall(rf"^\s*{re.escape(name)}\b([^\n]*)$", formula, re.MULTILINE)


def literal_matches(statement: str, value: str) -> bool:
    """Match one literal Ruby directive, accepting either generated quote style."""
    return statement.strip() in (f'"{value}"', f"'{value}'")


def check_release_formula(formula: str, pins: dict) -> None:
    """Bind the single native formula to the public release and platform contract."""
    expected = {
        "version": pins["version"],
        "url": f'{RELEASE_BASE}/{pins["release_tag"]}/{pins["archive"]}',
        "sha256": pins["sha256"],
    }
    for name, value in expected.items():
        actual = statements(formula, name)
        require(len(actual) == 1 and literal_matches(actual[0], value),
                f"formula {name} differs from the public release")
    require(not statements(formula, "revision"), "new upstream release must not retain a revision")
    require(not statements(formula, "mirror"), "public formula must use the pinned release URL")
    requirements = {value.strip() for value in statements(formula, "depends_on")}
    require("macos: :ventura" in requirements and "arch: :arm64" in requirements,
            "public formula must require macOS Ventura and Apple Silicon")
    require(not statements(formula, "on_linux") and not statements(formula, "on_intel"),
            "public formula must not contain unqualified platforms")
    require(not any(value in formula for value in (
        "file://", "HOMEBREW_CACHE", "dkc-private", "prepare-private", "deepkit-code-history",
    )), "public formula must not depend on private preview delivery")


def check_preview_formula(root: Path, formula: str) -> None:
    """Retain the existing private preview checks until a real release is pinned."""
    spec = importlib.util.spec_from_file_location("prepare_private", root / "scripts/prepare-private.py")
    prepare = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prepare)
    pins = prepare.manifest()
    require(f'version "{pins["version"]}"' in formula, "formula version drifted")
    revision = pins.get("brew_revision", 0)
    require(type(revision) is int and revision >= 0, "invalid Homebrew revision")
    formula_revision = re.search(r"^\s*revision (\d+)\s*$", formula, re.MULTILINE)
    require((int(formula_revision.group(1)) if formula_revision else 0) == revision,
            "formula revision drifted")
    require('HOMEBREW_CACHE/"dkc-private"/' in formula, "private cache root drifted")
    for entry in pins["targets"].values():
        require(f'sha256 "{entry["sha256"]}"' in formula, "formula checksum drifted")
        require(f'"{entry["sha256"]}"/' in formula, "cache identity drifted")
        require(f'"{entry["archive"]}"' in formula, "archive filename drifted")


def check(root: Path = ROOT) -> str:
    """Check the selected manifest without downloading archives or running Homebrew."""
    formula = (root / "Formula/dkc.rb").read_text()
    release = root / "release.json"
    if release.exists():
        check_release_formula(formula, release_manifest(release))
        distribution = "public release"
    else:
        check_preview_formula(root, formula)
        distribution = "private preview"
    for path in (root / "README.md", root / "LICENSE.md", root / "docs/maintaining.md"):
        for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if not link.startswith(("https://", "http://", "#")):
                require((path.parent / link.split("#")[0]).exists(), f"missing link in {path}: {link}")
    return f"Formula pins and local documentation links match the {distribution}."


if __name__ == "__main__":
    try:
        print(check())
    except (ValueError, OSError, KeyError) as error:
        raise SystemExit(f"Tap check failed: {error}") from None
