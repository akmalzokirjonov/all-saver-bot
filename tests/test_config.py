"""Exercise configuration exactly as a fresh bot process reads it."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ConfigurationTests(unittest.TestCase):
    def load_settings(self, admin_ids=None, dotenv=False, **overrides):
        with tempfile.TemporaryDirectory() as scratch:
            env = {
                key: value for key, value in os.environ.items()
                if key not in {"ADMIN_IDS", "MAX_CONCURRENT_PER_USER", "MAX_GLOBAL_CONCURRENT", "MAX_FILE_SIZE_MB"}
            }
            env.update(
                BOT_TOKEN="123456789:TEST_TOKEN_FOR_OFFLINE_CHECKS_ONLY",
                DOWNLOAD_DIR=str(Path(scratch) / "downloads"),
                LOG_FILE=str(Path(scratch) / "logs" / "bot.log"),
                PYTHONPATH=str(ROOT),
            )
            env.update(overrides)
            if admin_ids is not None:
                if dotenv:
                    (Path(scratch) / ".env").write_text(f"ADMIN_IDS={admin_ids}\n", encoding="utf-8")
                else:
                    env["ADMIN_IDS"] = admin_ids
            return subprocess.run(
                [sys.executable, "-c", "from config import settings; import json; print(json.dumps(settings.ADMIN_IDS))"],
                env=env, cwd=scratch, capture_output=True, text=True, timeout=10,
            )

    def test_admin_id_formats_from_environment(self):
        for raw, expected in [(None, []), ("", []), ("123456", [123456]),
                              ("123456, 789012", [123456, 789012]),
                              ("[123456, 789012]", [123456, 789012])]:
            with self.subTest(raw=raw):
                result = self.load_settings(raw)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout), expected)

    def test_comma_separated_ids_from_dotenv(self):
        result = self.load_settings("123456,789012", dotenv=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), [123456, 789012])

    def test_invalid_admin_id_is_rejected(self):
        result = self.load_settings("123456,invalid")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ADMIN_IDS", result.stderr)


if __name__ == "__main__":
    unittest.main()
