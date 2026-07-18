import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PROFILE_ROOT = REPO / "beta" / "2.0-routing-convergence" / "h1-owner-metadata"
BUILD_SCRIPT = REPO / "scripts" / "build-release-pack.py"
OWNERS = ("3l5s", "edsp", "sela", "mpg", "wae", "tvg", "tplan")


def split_skill(path: Path) -> tuple[dict[str, str], bytes]:
    payload = path.read_bytes()
    marker = b"---\n"
    end = payload.find(marker, len(marker))
    metadata: dict[str, str] = {}
    for line in payload[len(marker) : end].decode().splitlines():
        key, value = line.split(":", 1)
        raw = value.strip()
        metadata[key.strip()] = json.loads(raw) if raw.startswith('"') else raw
    return metadata, payload[end + len(marker) :]


class H1OwnerMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temp = tempfile.TemporaryDirectory()
        cls.out = Path(cls._temp.name) / "release"
        result = subprocess.run(
            [
                "python3",
                str(BUILD_SCRIPT),
                "--release-line",
                "2.0-routing-h1-metadata",
                "--package",
                "plugins",
                "--out",
                str(cls.out),
            ],
            text=True,
            capture_output=True,
        )
        if result.returncode:
            raise AssertionError(result.stderr + result.stdout)
        cls.plugin = cls.out / "codex-plugin" / "mindthus-beta"
        cls.profile = json.loads((PROFILE_ROOT / "release-profile.json").read_text())

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temp.cleanup()

    def test_profile_is_distinct_unpublished_codex_only_candidate(self) -> None:
        self.assertEqual(self.profile["release_line"], "2.0-routing-h1-metadata")
        self.assertEqual(self.profile["version"], "2.0.0-next.2")
        self.assertEqual(self.profile["supported_surfaces"], ["codex-plugin"])
        self.assertEqual(self.profile["release_preparation"], "forbidden")
        self.assertNotIn("beta.3", json.dumps(self.profile).lower())

    def test_only_mpg_and_wae_descriptions_change(self) -> None:
        overrides = self.profile["owner_description_overrides"]
        self.assertEqual(set(overrides), {"mpg", "wae"})
        for owner in OWNERS:
            source_metadata, source_body = split_skill(REPO / "skills" / owner / "SKILL.md")
            built_metadata, built_body = split_skill(self.plugin / "skills" / owner / "SKILL.md")
            self.assertEqual(built_metadata["name"], source_metadata["name"])
            expected_description = overrides.get(owner, source_metadata["description"])
            self.assertEqual(built_metadata["description"], expected_description)
            self.assertEqual(
                built_body.replace(b"mindthus-beta:", b"mindthus:"),
                source_body,
                owner,
            )

    def test_thin_entry_and_forbidden_carriers_are_locked(self) -> None:
        entry = self.plugin / "skills" / "using-mindthus" / "SKILL.md"
        self.assertEqual(hashlib.sha256(entry.read_bytes()).hexdigest(), self.profile["thin_entry_sha256"])
        for relative in self.profile["forbidden_active_paths"]:
            self.assertFalse((self.plugin / relative).exists(), relative)

    def test_packaged_diagnostic_passes_but_keeps_semantic_claims_unproven(self) -> None:
        result = subprocess.run(
            [
                "python3",
                str(self.plugin / "scripts" / "check-h1-metadata.py"),
                "--plugin-root",
                str(self.plugin),
                "--stable-state",
                "disabled",
                "--require-isolated",
                "--json",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["integrity"], "ok")
        for word in ("activation", "owner selection", "passive recall", "tokens", "latency"):
            self.assertIn(word, payload["claim_ceiling"])


if __name__ == "__main__":
    unittest.main()
