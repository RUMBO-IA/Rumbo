from pathlib import Path
import re
import unittest


class ReleasePostureDocsTests(unittest.TestCase):
    def test_readme_does_not_pin_current_main_sha(self):
        readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
        self.assertIsNone(
            re.search(r"Current `main` is `[0-9a-f]{40}`", readme),
            "README must not hard-code a current main SHA because the commit containing it makes it stale",
        )


if __name__ == "__main__":
    unittest.main()
