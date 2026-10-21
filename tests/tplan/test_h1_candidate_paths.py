"""Real temporary-filesystem checks for H1 content confinement, not Host auth."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[2] / "skills" / "tplan" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import tplan_h1_commands as h1


@unittest.skipUnless(h1._FD_CONTENT_SUPPORTED, "Secure POSIX descriptor IO unavailable")
class H1CandidatePathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="h1-content-path-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.mission = self.root / "mission"
        self.store = self.mission / "artifacts" / "h1"
        self.store.mkdir(parents=True)
        self.outside = self.root / "outside"
        (self.outside / "h1").mkdir(parents=True)
        self.content = b"synthetic immutable candidate"
        self.sha = "sha256:" + hashlib.sha256(self.content).hexdigest()
        self.leaf = self.store / self.sha[7:]

    def swap_artifacts(self):
        (self.mission / "artifacts").rename(self.mission / "original-artifacts")
        (self.mission / "artifacts").symlink_to(self.outside, target_is_directory=True)

    def assert_refused(self, callback):
        with self.assertRaises((h1.CommandError, OSError)):
            callback()

    def test_01_stable_roundtrip_and_idempotent_publication(self):
        self.store.rmdir()
        self.store.parent.rmdir()
        h1._store_content(self.mission, self.sha, self.content)
        before = self.leaf.stat()
        h1._store_content(self.mission, self.sha, self.content)
        self.assertEqual(h1._read_content(self.mission, self.sha), self.content)
        self.assertEqual(self.leaf.stat().st_ino, before.st_ino)
        self.assertEqual(self.leaf.stat().st_nlink, 1)
        self.assertEqual(list(self.store.glob(".prepare-*")), [])

    def test_02_checked_ancestor_replaced_before_read_is_refused(self):
        # Same SHA in the outside directory must not make redirection acceptable.
        self.leaf.write_bytes(self.content)
        (self.outside / "h1" / self.sha[7:]).write_bytes(self.content)
        original = h1._content_path
        def swap(directory, sha, **kwargs):
            result = original(directory, sha, **kwargs)
            self.swap_artifacts()
            return result
        with patch.object(h1, "_content_path", side_effect=swap):
            self.assert_refused(lambda: h1._read_content(self.mission, self.sha))

    def test_03_read_keeps_open_parent_when_ancestor_changes_before_leaf_open(self):
        self.leaf.write_bytes(self.content)
        original_inode = self.leaf.stat().st_ino
        outside_leaf = self.outside / "h1" / self.sha[7:]
        outside_leaf.write_bytes(self.content)
        opened_inodes = []
        original_open = os.open
        def swap(path, flags, *args, **kwargs):
            if Path(path).name == self.sha[7:]:
                self.swap_artifacts()
                fd = original_open(path, flags, *args, **kwargs)
                opened_inodes.append(os.fstat(fd).st_ino)
                return fd
            return original_open(path, flags, *args, **kwargs)
        with patch.object(h1.os, "open", side_effect=swap):
            self.assertEqual(h1._read_content(self.mission, self.sha), self.content)
        self.assertEqual(opened_inodes, [original_inode])
        self.assertNotEqual(original_inode, outside_leaf.stat().st_ino)

    def test_04_static_ancestor_symlink_is_refused(self):
        self.swap_artifacts()
        (self.outside / "h1" / self.sha[7:]).write_bytes(self.content)
        self.assert_refused(lambda: h1._read_content(self.mission, self.sha))
        self.assert_refused(lambda: h1._store_content(self.mission, self.sha, self.content))

    def test_05_mission_ancestor_symlink_is_refused(self):
        self.leaf.write_bytes(self.content)
        alias = self.root / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        self.assert_refused(lambda: h1._read_content(alias / "mission", self.sha))

    def test_06_leaf_symlink_is_refused(self):
        target = self.outside / "content"
        target.write_bytes(self.content)
        self.leaf.symlink_to(target)
        self.assert_refused(lambda: h1._read_content(self.mission, self.sha))
        self.assert_refused(lambda: h1._store_content(self.mission, self.sha, self.content))
        self.assertEqual(target.read_bytes(), self.content)

    def test_07_hardlinked_leaf_is_refused(self):
        target = self.outside / "content"
        target.write_bytes(self.content)
        os.link(target, self.leaf)
        self.assert_refused(lambda: h1._read_content(self.mission, self.sha))
        self.assert_refused(lambda: h1._store_content(self.mission, self.sha, self.content))
        self.assertEqual(target.read_bytes(), self.content)
        self.assertEqual(list(self.store.glob(".prepare-*")), [])

    def test_08_nonregular_leaf_is_refused_without_blocking(self):
        os.mkfifo(self.leaf)
        self.assert_refused(lambda: h1._read_content(self.mission, self.sha))
        self.leaf.unlink()
        self.leaf.mkdir()
        self.assert_refused(lambda: h1._read_content(self.mission, self.sha))

    def test_09_oversized_content_is_refused(self):
        content = b"x" * (h1.MAX_CONTENT + 1)
        sha = "sha256:" + hashlib.sha256(content).hexdigest()
        (self.store / sha[7:]).write_bytes(content)
        self.assert_refused(lambda: h1._read_content(self.mission, sha))

    def test_10_growth_after_initial_stat_is_still_bounded(self):
        content = b"x" * (h1.MAX_CONTENT + 1)
        sha = "sha256:" + hashlib.sha256(content).hexdigest()
        leaf = self.store / sha[7:]
        leaf.write_bytes(b"x")
        original_fstat = os.fstat
        grown = False
        def grow(fd):
            nonlocal grown
            info = original_fstat(fd)
            if not grown and info.st_ino == leaf.stat().st_ino:
                grown = True
                leaf.write_bytes(content)
            return info
        with patch.object(h1.os, "fstat", side_effect=grow):
            self.assert_refused(lambda: h1._read_content(self.mission, sha))
        self.assertTrue(grown)

    def test_11_checked_ancestor_replaced_before_staging_never_writes_outside(self):
        original = h1._content_path
        def swap(directory, sha, **kwargs):
            result = original(directory, sha, **kwargs)
            self.swap_artifacts()
            return result
        with patch.object(h1, "_content_path", side_effect=swap):
            self.assert_refused(lambda: h1._store_content(self.mission, self.sha, self.content))
        self.assertEqual(list((self.outside / "h1").iterdir()), [])

    def test_12_publication_and_cleanup_use_pinned_store_after_swap(self):
        original_link = os.link
        outside_temporary = None
        def swap(source, destination, *args, **kwargs):
            nonlocal outside_temporary
            self.swap_artifacts()
            outside_temporary = self.outside / "h1" / Path(source).name
            outside_temporary.write_bytes(b"outside sentinel must survive cleanup")
            return original_link(source, destination, *args, **kwargs)
        with patch.object(h1.os, "link", side_effect=swap):
            h1._store_content(self.mission, self.sha, self.content)
        pinned = self.mission / "original-artifacts" / "h1"
        self.assertEqual((pinned / self.sha[7:]).read_bytes(), self.content)
        self.assertEqual(list(pinned.glob(".prepare-*")), [])
        self.assertEqual(outside_temporary.read_bytes(), b"outside sentinel must survive cleanup")
        self.assertFalse((self.outside / "h1" / self.sha[7:]).exists())

    def test_13_failed_write_cleans_up_temporary_file(self):
        with patch.object(h1.os, "fsync", side_effect=OSError("synthetic fsync failure")):
            self.assert_refused(lambda: h1._store_content(self.mission, self.sha, self.content))
        self.assertEqual(list(self.store.iterdir()), [])

    def test_14_failed_path_operations_do_not_leak_descriptors(self):
        descriptors = Path("/proc/self/fd")
        if not descriptors.is_dir():
            self.skipTest("Linux descriptor inventory unavailable")
        self.swap_artifacts()
        before = len(list(descriptors.iterdir()))
        for _ in range(3):
            self.assert_refused(lambda: h1._read_content(self.mission, self.sha))
            self.assert_refused(lambda: h1._store_content(self.mission, self.sha, self.content))
        self.assertEqual(len(list(descriptors.iterdir())), before)

    def test_15_digest_mismatch_cannot_be_replaced_or_used_as_a_path(self):
        self.leaf.write_bytes(b"changed bytes must not be overwritten")
        self.assert_refused(lambda: h1._read_content(self.mission, self.sha))
        self.assert_refused(lambda: h1._store_content(self.mission, self.sha, self.content))
        self.assertEqual(self.leaf.read_bytes(), b"changed bytes must not be overwritten")
        self.assert_refused(lambda: h1._read_content(self.mission, "sha256:../../outside"))
        self.assertEqual(list(self.store.glob(".prepare-*")), [])

    def test_16_missing_secure_primitives_refuses_before_io(self):
        with patch.object(h1, "_FD_CONTENT_SUPPORTED", False):
            self.assert_refused(lambda: h1._read_content(self.mission, self.sha))
            self.assert_refused(lambda: h1._store_content(self.mission, self.sha, self.content))
        self.assertEqual(list(self.store.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
