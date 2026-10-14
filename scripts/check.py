#!/usr/bin/env python3
"""Reject stale formula pins and missing documentation links."""

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("prepare_private", ROOT / "scripts/prepare-private.py")
prepare = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prepare)
pins = prepare.manifest()
formula = (ROOT / "Formula/dkc.rb").read_text()
assert f'version "{pins["version"]}"' in formula, "formula version drifted"
assert 'HOMEBREW_CACHE/"dkc-private"/' in formula, "private cache root drifted"
for entry in pins["targets"].values():
    assert f'sha256 "{entry["sha256"]}"' in formula, "formula checksum drifted"
    assert f'"{entry["sha256"]}"/' in formula, "cache identity drifted"
    assert f'"{entry["archive"]}"' in formula, "archive filename drifted"
for path in (ROOT / "README.md", ROOT / "LICENSE.md", ROOT / "docs/maintaining.md"):
    for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
        if not link.startswith(("https://", "http://", "#")):
            assert (path.parent / link.split("#")[0]).exists(), (path, link)
print("Formula pins and local documentation links match the private preview.")
