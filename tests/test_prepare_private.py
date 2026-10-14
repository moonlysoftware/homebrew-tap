"""Private-preview trust-boundary tests; no Homebrew, network or real binaries."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare-private.py"
SPEC = importlib.util.spec_from_file_location("prepare_private", SCRIPT)
prepare_private = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare_private)

TARGET = "aarch64-apple-darwin"
ARCHIVE = f"deepkit-code-{TARGET}.tar.gz"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PreviewFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="dkc-private-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.build = {
            "version": "0.1.0-beta.1",
            "diagnostic": False,
            "build": {
                "commit": "1" * 40,
                "source_blake3": "2" * 64,
                "target": TARGET,
                "source_dirty": "false",
            },
        }
        self.files = {
            "dkc": b"#!/bin/sh\nprintf 'synthetic fixture only\\n'\n",
            "third-party-licenses.tar.gz": b"synthetic notice bundle\n",
            "LICENSE.md": b"MIT OR Apache-2.0\n",
            "LICENSE-MIT": b"synthetic MIT notice\n",
            "LICENSE-APACHE": b"synthetic Apache notice\n",
            "THIRD_PARTY_NOTICES.md": b"synthetic dependency notices\n",
        }
        self.pins = {
            "schema": 1,
            "repository": "moonlysoftware/deepkit-code",
            "version": self.build["version"],
            "build_commit": self.build["build"]["commit"],
            "source_blake3": self.build["build"]["source_blake3"],
            "run_id": 123456,
            "source_head": "3" * 40,
            "targets": {
                TARGET: {
                    "artifact_id": 789,
                    "artifact_name": "beta-homebrew-arm64-123456-1",
                    "archive": ARCHIVE,
                    "binary_sha256": digest(self.files["dkc"]),
                    "notice_bundle_sha256": digest(self.files["third-party-licenses.tar.gz"]),
                    "license_sha256": {
                        name: digest(self.files[name])
                        for name in ("LICENSE.md", "LICENSE-MIT", "LICENSE-APACHE", "THIRD_PARTY_NOTICES.md")
                    },
                }
            },
        }
        self.archive = self.write_archive()
        self.cache = self.root / "cache"
        self.cache.mkdir()

    def write_archive(self, *, build=None, changes=None, prefix="", extras=(), executable=True):
        """Pin outer bytes, keeping the independent reviewed inner-file hashes."""
        path = self.root / ARCHIVE
        files = dict(self.files)
        files["BUILD.json"] = json.dumps(self.build if build is None else build).encode()
        files.update(changes or {})
        with tarfile.open(path, "w:gz") as archive:
            if prefix:
                directory = tarfile.TarInfo(prefix)
                directory.type = tarfile.DIRTYPE
                directory.mode = 0o755
                archive.addfile(directory)
            for name, data in files.items():
                info = tarfile.TarInfo(f"{prefix}/{name}" if prefix else name)
                info.size = len(data)
                info.mode = 0o755 if name == "dkc" and executable else 0o644
                archive.addfile(info, io.BytesIO(data))
            for info, data in extras:
                archive.addfile(info, io.BytesIO(data) if data is not None else None)
        entry = self.pins["targets"][TARGET]
        entry["bytes"] = path.stat().st_size
        entry["sha256"] = digest(path.read_bytes())
        return path

    def destination(self):
        entry = self.pins["targets"][TARGET]
        return self.cache / "dkc-private" / entry["sha256"] / ARCHIVE

    def artifact_metadata(self):
        entry = self.pins["targets"][TARGET]
        return {
            "id": entry["artifact_id"],
            "name": entry["artifact_name"],
            "expired": False,
            "workflow_run": {"id": self.pins["run_id"], "head_sha": self.pins["source_head"]},
        }


class ArchiveVerificationTests(PreviewFixture):
    def test_accepts_reviewed_flat_and_single_directory_archives(self):
        for prefix in ("", "deepkit-code"):
            with self.subTest(prefix=prefix):
                path = self.write_archive(prefix=prefix)
                prepare_private.verify_archive(path, self.pins, TARGET)

    def test_rejects_wrong_archive_hash_even_when_size_matches(self):
        self.pins["targets"][TARGET]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "reviewed size or SHA-256"):
            prepare_private.verify_archive(self.archive, self.pins, TARGET)

    def test_rejects_wrong_archive_size_even_when_hash_matches(self):
        self.pins["targets"][TARGET]["bytes"] += 1
        with self.assertRaisesRegex(ValueError, "reviewed size or SHA-256"):
            prepare_private.verify_archive(self.archive, self.pins, TARGET)

    def test_rejects_unreviewed_version_or_build_provenance(self):
        cases = (
            ("version", "0.2.0"),
            ("diagnostic", True),
            ("commit", "4" * 40),
            ("source_blake3", "5" * 64),
            ("target", "x86_64-unknown-linux-gnu"),
            ("source_dirty", True),
            ("source_dirty", "true"),
        )
        for field, value in cases:
            with self.subTest(field=field, value=value):
                build = copy.deepcopy(self.build)
                section = build if field in ("version", "diagnostic") else build["build"]
                section[field] = value
                path = self.write_archive(build=build)
                with self.assertRaisesRegex(ValueError, "build provenance"):
                    prepare_private.verify_archive(path, self.pins, TARGET)

    def test_accepts_boolean_clean_build_marker(self):
        build = copy.deepcopy(self.build)
        build["build"]["source_dirty"] = False
        path = self.write_archive(build=build)
        prepare_private.verify_archive(path, self.pins, TARGET)

    def test_rejects_changed_binary_even_with_matching_outer_archive_pin(self):
        path = self.write_archive(changes={"dkc": b"different executable\n"})
        with self.assertRaisesRegex(ValueError, "binary checksum"):
            prepare_private.verify_archive(path, self.pins, TARGET)

    def test_rejects_changed_bundled_notices_with_matching_outer_archive_pin(self):
        for name in self.files:
            if name == "dkc":
                continue
            with self.subTest(name=name):
                path = self.write_archive(changes={name: b"unreviewed notice\n"})
                with self.assertRaisesRegex(ValueError, "notice.*differs"):
                    prepare_private.verify_archive(path, self.pins, TARGET)

    def test_rejects_oversized_build_metadata(self):
        path = self.write_archive(changes={"BUILD.json": b" " * 1_000_001})
        with self.assertRaisesRegex(ValueError, "oversized build metadata"):
            prepare_private.verify_archive(path, self.pins, TARGET)

    def test_rejects_non_executable_binary(self):
        path = self.write_archive(executable=False)
        with self.assertRaisesRegex(ValueError, "one executable dkc"):
            prepare_private.verify_archive(path, self.pins, TARGET)

    def test_rejects_hostile_tar_members_without_extracting_them(self):
        cases = (
            ("../escaped", tarfile.REGTYPE, ""),
            (str(self.root / "escaped"), tarfile.REGTYPE, ""),
            ("dkc", tarfile.REGTYPE, ""),
            ("./dkc", tarfile.REGTYPE, ""),
            ("linked", tarfile.SYMTYPE, "../../escaped"),
            ("linked", tarfile.LNKTYPE, "dkc"),
            ("pipe", tarfile.FIFOTYPE, ""),
        )
        for name, kind, link in cases:
            with self.subTest(name=name, kind=kind):
                info = tarfile.TarInfo(name)
                info.type = kind
                info.linkname = link
                path = self.write_archive(extras=((info, b"" if kind == tarfile.REGTYPE else None),))
                with self.assertRaisesRegex(ValueError, "unsafe archive layout"):
                    prepare_private.verify_archive(path, self.pins, TARGET)
                self.assertFalse((self.root / "escaped").exists())

    def test_rejects_deep_or_split_archive_root(self):
        path = self.write_archive(prefix="outer/inner")
        with self.assertRaisesRegex(ValueError, "flat archive or one shared directory"):
            prepare_private.verify_archive(path, self.pins, TARGET)
        other = tarfile.TarInfo("elsewhere/extra")
        path = self.write_archive(prefix="package", extras=((other, b""),))
        with self.assertRaisesRegex(ValueError, "flat archive or one shared directory"):
            prepare_private.verify_archive(path, self.pins, TARGET)

    def test_rejects_two_executable_candidates(self):
        second = tarfile.TarInfo("other/dkc")
        second.mode = 0o755
        path = self.write_archive(extras=((second, b""),))
        with self.assertRaisesRegex(ValueError, "one executable dkc"):
            prepare_private.verify_archive(path, self.pins, TARGET)

    def test_rejects_archive_symlink(self):
        link = self.root / "linked.tar.gz"
        link.symlink_to(self.archive)
        with self.assertRaisesRegex(ValueError, "regular file"):
            prepare_private.verify_archive(link, self.pins, TARGET)


class CachePreparationTests(PreviewFixture):
    def test_prepares_exact_bytes_and_reuses_verified_cache_without_download(self):
        with mock.patch.object(prepare_private, "download", side_effect=AssertionError("unexpected network")):
            result = prepare_private.prepare(self.pins, TARGET, self.cache, self.archive)
            self.assertEqual(result, self.destination())
            self.assertEqual(result.read_bytes(), self.archive.read_bytes())
            self.assertEqual(result.stat().st_mode & 0o777, 0o644)
            repeated = prepare_private.prepare(self.pins, TARGET, self.cache)
            self.assertEqual(repeated, result)
            self.assertEqual(list(result.parent.iterdir()), [result])

    def test_existing_cache_mismatch_is_refused_without_overwrite_or_download(self):
        destination = self.destination()
        destination.parent.mkdir(parents=True)
        destination.write_bytes(b"unexpected previous contents")
        with mock.patch.object(prepare_private, "download", side_effect=AssertionError("unexpected network")):
            with self.assertRaisesRegex(ValueError, "reviewed size or SHA-256"):
                prepare_private.prepare(self.pins, TARGET, self.cache, self.archive)
        self.assertEqual(destination.read_bytes(), b"unexpected previous contents")

    def test_invalid_source_is_not_published(self):
        self.archive.write_bytes(b"not the reviewed archive")
        with self.assertRaisesRegex(ValueError, "reviewed size or SHA-256"):
            prepare_private.prepare(self.pins, TARGET, self.cache, self.archive)
        self.assertFalse(self.destination().exists())
        self.assertFalse(self.destination().parent.exists())

    def test_fifo_source_is_refused_before_copying(self):
        fifo = self.root / "archive.fifo"
        os.mkfifo(fifo)
        with self.assertRaisesRegex(ValueError, "regular file"):
            prepare_private.prepare(self.pins, TARGET, self.cache, fifo)
        self.assertFalse(self.destination().exists())

    def test_explicit_invalid_source_is_refused_even_with_valid_cache(self):
        destination = prepare_private.prepare(self.pins, TARGET, self.cache, self.archive)
        before = destination.read_bytes()
        self.archive.write_bytes(b"not the reviewed archive")
        with self.assertRaisesRegex(ValueError, "reviewed size or SHA-256"):
            prepare_private.prepare(self.pins, TARGET, self.cache, self.archive)
        self.assertEqual(destination.read_bytes(), before)

    def test_source_archive_symlink_is_refused_without_publication(self):
        link = self.root / "source-link.tar.gz"
        link.symlink_to(self.archive)
        with self.assertRaisesRegex(ValueError, "regular file"):
            prepare_private.prepare(self.pins, TARGET, self.cache, link)
        self.assertFalse(self.destination().exists())

    def test_refuses_symlinks_at_each_preview_cache_component(self):
        for component in ("namespace", "digest", "archive"):
            with self.subTest(component=component):
                cache = self.root / f"cache-{component}"
                destination = cache / "dkc-private" / self.pins["targets"][TARGET]["sha256"] / ARCHIVE
                selected = {"namespace": cache / "dkc-private", "digest": destination.parent,
                            "archive": destination}[component]
                selected.parent.mkdir(parents=True)
                outside = self.root / f"outside-{component}"
                if component == "archive":
                    shutil.copyfile(self.archive, outside)
                    before = outside.read_bytes()
                else:
                    outside.mkdir()
                    before = list(outside.iterdir())
                selected.symlink_to(outside, target_is_directory=component != "archive")
                with self.assertRaisesRegex(ValueError, "symbolic link in preview cache"):
                    prepare_private.prepare(self.pins, TARGET, cache, self.archive)
                after = outside.read_bytes() if component == "archive" else list(outside.iterdir())
                self.assertEqual(after, before)

    def test_refuses_dangling_cache_symlink(self):
        destination = self.destination()
        destination.parent.mkdir(parents=True)
        destination.symlink_to(self.root / "absent")
        with self.assertRaisesRegex(ValueError, "symbolic link in preview cache"):
            prepare_private.prepare(self.pins, TARGET, self.cache, self.archive)
        self.assertTrue(destination.is_symlink())
        self.assertFalse((self.root / "absent").exists())


class AuthenticatedDownloadTests(PreviewFixture):
    def test_checks_exact_artifact_then_downloads_only_pinned_run_and_name(self):
        destination = self.root / "download"
        entry = self.pins["targets"][TARGET]
        api_command = ["gh", "api", "repos/moonlysoftware/deepkit-code/actions/artifacts/789"]
        download_command = ["gh", "run", "download", "123456", "--repo", "moonlysoftware/deepkit-code",
                            "--name", entry["artifact_name"], "--dir", str(destination)]

        def gh(command, **kwargs):
            if command == api_command:
                return subprocess.CompletedProcess(command, 0, json.dumps(self.artifact_metadata()))
            self.assertEqual(command, download_command)
            destination.mkdir()
            shutil.copyfile(self.archive, destination / ARCHIVE)
            return subprocess.CompletedProcess(command, 0)

        with mock.patch.object(prepare_private.subprocess, "run", side_effect=gh) as run:
            result = prepare_private.download(self.pins, TARGET, destination)
        self.assertEqual(result, destination / ARCHIVE)
        self.assertEqual(result.read_bytes(), self.archive.read_bytes())
        self.assertEqual(run.call_args_list, [
            mock.call(api_command, check=True, capture_output=True, text=True),
            mock.call(download_command, check=True),
        ])

    def test_refuses_expired_or_changed_artifact_before_download(self):
        cases = (("id", 790), ("name", "unreviewed-artifact"), ("expired", True),
                 ("run_id", 123457), ("head_sha", "6" * 40))
        for field, value in cases:
            with self.subTest(field=field):
                metadata = self.artifact_metadata()
                if field == "run_id":
                    metadata["workflow_run"]["id"] = value
                elif field == "head_sha":
                    metadata["workflow_run"][field] = value
                else:
                    metadata[field] = value
                response = subprocess.CompletedProcess([], 0, json.dumps(metadata))
                with mock.patch.object(prepare_private.subprocess, "run", return_value=response) as run:
                    with self.assertRaisesRegex(ValueError, "expired or its identity changed"):
                        prepare_private.download(self.pins, TARGET, self.root / "download")
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.args[0][:2], ["gh", "api"])

    def test_failed_authentication_does_not_attempt_artifact_download(self):
        error = subprocess.CalledProcessError(1, ["gh", "api"], stderr="authentication required")
        with mock.patch.object(prepare_private.subprocess, "run", side_effect=error) as run:
            with self.assertRaises(subprocess.CalledProcessError):
                prepare_private.download(self.pins, TARGET, self.root / "download")
        self.assertEqual(run.call_count, 1)

    def test_refuses_missing_or_ambiguous_downloaded_archive(self):
        for count in (0, 2):
            with self.subTest(count=count):
                destination = self.root / f"download-{count}"

                def gh(command, **kwargs):
                    if command[:2] == ["gh", "api"]:
                        return subprocess.CompletedProcess(command, 0, json.dumps(self.artifact_metadata()))
                    for number in range(count):
                        folder = destination / str(number)
                        folder.mkdir(parents=True)
                        shutil.copyfile(self.archive, folder / ARCHIVE)
                    return subprocess.CompletedProcess(command, 0)

                with mock.patch.object(prepare_private.subprocess, "run", side_effect=gh):
                    with self.assertRaisesRegex(ValueError, "exactly one selected archive"):
                        prepare_private.download(self.pins, TARGET, destination)


if __name__ == "__main__":
    unittest.main()
