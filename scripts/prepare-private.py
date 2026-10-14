#!/usr/bin/env python3
"""Fetch a pinned private preview with gh and seed Homebrew's local archive cache."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    ("Darwin", "arm64"): "aarch64-apple-darwin",
    ("Linux", "x86_64"): "x86_64-unknown-linux-gnu",
}


def manifest() -> dict:
    """Read the reviewed artifact pins; paths and hashes must stay unambiguous."""
    value = json.loads((ROOT / "preview.json").read_text())
    if value["schema"] != 1 or value["repository"] != "moonlysoftware/deepkit-code":
        raise ValueError("unsupported preview manifest")
    for target, entry in value["targets"].items():
        if target not in TARGETS.values():
            raise ValueError(f"unsupported preview target: {target}")
        if entry["archive"] != f"deepkit-code-{target}.tar.gz":
            raise ValueError("invalid archive filename")
        for key in ("sha256", "binary_sha256", "notice_bundle_sha256"):
            digest = entry[key]
            if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError(f"invalid {key}")
        if not 0 < entry["bytes"] <= 50_000_000:
            raise ValueError("archive size must be within the beta download limit")
    return value


def file_hash(path: Path) -> str:
    """Hash the exact archive bytes Homebrew will install."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def verify_archive(path: Path, pins: dict, target: str) -> None:
    """Check reviewed bytes, safe layout, clean build identity and bundled notices."""
    entry = pins["targets"][target]
    if path.is_symlink() or not path.is_file():
        raise ValueError("archive must be a regular file, not a symbolic link")
    if path.stat().st_size != entry["bytes"] or file_hash(path) != entry["sha256"]:
        raise ValueError("archive differs from the reviewed size or SHA-256")
    with tarfile.open(path, "r:gz") as archive:
        members = archive.getmembers()
        names = [PurePosixPath(item.name) for item in members]
        if len(names) != len(set(names)) or any(
            name.is_absolute() or ".." in name.parts
            or not (member.isfile() or member.isdir())
            for name, member in zip(names, members)
        ):
            raise ValueError("unsafe archive layout")
        binaries = [item for item in members if PurePosixPath(item.name).name == "dkc"]
        if len(binaries) != 1 or not binaries[0].isfile() or not binaries[0].mode & 0o111:
            raise ValueError("expected one executable dkc")
        parent = PurePosixPath(binaries[0].name).parent
        if len(parent.parts) > 1 or any(
            parent != PurePosixPath(".") and name != parent and parent not in name.parents
            for name in names
        ):
            raise ValueError("expected a flat archive or one shared directory")

        def member_hash(name: str) -> str:
            member = archive.getmember(str(parent / name))
            if not member.isfile():
                raise ValueError(f"expected regular archive member: {name}")
            with archive.extractfile(member) as stream:
                return hashlib.file_digest(stream, "sha256").hexdigest()

        build_member = archive.getmember(str(parent / "BUILD.json"))
        if not build_member.isfile() or build_member.size > 1_000_000:
            raise ValueError("missing or oversized build metadata")
        with archive.extractfile(build_member) as stream:
            metadata = json.load(stream)
        build = metadata["build"]
        if (
            metadata["version"] != pins["version"] or metadata["diagnostic"] is not False
            or build["commit"] != pins["build_commit"] or build["target"] != target
            or build["source_blake3"] != pins["source_blake3"]
            or str(build["source_dirty"]).lower() != "false"
        ):
            raise ValueError("build provenance differs from the reviewed preview")
        if member_hash("dkc") != entry["binary_sha256"]:
            raise ValueError("binary checksum differs")
        if member_hash("third-party-licenses.tar.gz") != entry["notice_bundle_sha256"]:
            raise ValueError("dependency notice bundle differs")
        for name, digest in entry["license_sha256"].items():
            if member_hash(name) != digest:
                raise ValueError(f"license notice differs: {name}")


def download(pins: dict, target: str, directory: Path) -> Path:
    """Authenticate through gh; no token or temporary signed URL enters the formula."""
    entry = pins["targets"][target]
    endpoint = f"repos/{pins['repository']}/actions/artifacts/{entry['artifact_id']}"
    result = subprocess.run(["gh", "api", endpoint], check=True, capture_output=True, text=True)
    artifact = json.loads(result.stdout)
    run = artifact["workflow_run"]
    if (
        artifact["id"] != entry["artifact_id"] or artifact["name"] != entry["artifact_name"]
        or artifact["expired"] or run["id"] != pins["run_id"]
        or run["head_sha"] != pins["source_head"]
    ):
        raise ValueError("pinned artifact expired or its identity changed; ask a maintainer to refresh the preview")
    subprocess.run([
        "gh", "run", "download", str(pins["run_id"]), "--repo", pins["repository"],
        "--name", entry["artifact_name"], "--dir", str(directory),
    ], check=True)
    candidates = list(directory.rglob(entry["archive"]))
    if len(candidates) != 1:
        raise ValueError("download must contain exactly one selected archive")
    return candidates[0]


def prepare(pins: dict, target: str, cache: Path, source: Path | None = None) -> Path:
    """Seed a content-addressed cache entry without overwriting a different file."""
    entry = pins["targets"][target]
    if source is not None:
        verify_archive(source, pins, target)
    destination = cache / "dkc-private" / entry["sha256"] / entry["archive"]
    for path in (cache / "dkc-private", destination.parent, destination):
        if path.is_symlink():
            raise ValueError(f"refusing symbolic link in preview cache: {path}")
    if destination.exists():
        verify_archive(destination, pins, target)
        return destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".prepare-", dir=destination.parent) as tmp:
        staging = Path(tmp)
        selected = source if source is not None else download(pins, target, staging / "download")
        verify_archive(selected, pins, target)
        staged_archive = staging / entry["archive"]
        shutil.copyfile(selected, staged_archive, follow_symlinks=False)
        verify_archive(staged_archive, pins, target)
        staged_archive.chmod(0o644)
        # Exclusive publication: never replace a concurrent or unexpected entry.
        os.link(staged_archive, destination)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="use an already downloaded, checksum-pinned archive")
    parser.add_argument("--verify-archive", type=Path, help="verify only; no Homebrew changes or downloads")
    parser.add_argument("--target", choices=TARGETS.values(), help="required with --verify-archive only")
    args = parser.parse_args()
    pins = manifest()
    if args.verify_archive:
        if not args.target or args.archive:
            parser.error("--verify-archive requires --target and cannot use --archive")
        verify_archive(args.verify_archive, pins, args.target)
        print("Archive identity, executable and licenses verified.")
        return
    if args.target:
        parser.error("--target is only for verification; installation uses the actual host")
    target = TARGETS.get((platform.system(), platform.machine()))
    if target is None:
        parser.error("preview supports Apple Silicon macOS and x86_64 GNU Linux diagnostic only")
    cache = Path(subprocess.check_output(["brew", "--cache"], text=True).strip()).resolve()
    destination = prepare(pins, target, cache, args.archive)
    print(f"Verified private preview ready: {destination}")
    print("brew install --formula moonlysoftware/tap/dkc")
    print("brew test moonlysoftware/tap/dkc")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, tarfile.TarError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Preview preparation failed: {error}") from None
