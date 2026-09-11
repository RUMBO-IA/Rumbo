import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class PublisherSupportPageTests(unittest.TestCase):
    def test_openai_support_is_dedicated_support_surface(self):
        html = (ROOT / "openai-support.html").read_text(encoding="utf-8-sig").lower()
        self.assertIn("<title>rumbo openai support</title>", html)
        self.assertIn("support for rumbo apps and plugins", html)
        self.assertIn("agent reliability", html)
        self.assertIn("guardian", html)
        self.assertIn("rumbo crm", html)
        self.assertIn("mailto:sebastian@rumbo.verso.fans", html)
        self.assertIn("/openai-privacy", html)
        self.assertIn("/openai-terms", html)
        self.assertIn("do not send passwords", html)
        self.assertNotIn("turn customer conversations into", html)

if __name__ == "__main__":
    unittest.main()
