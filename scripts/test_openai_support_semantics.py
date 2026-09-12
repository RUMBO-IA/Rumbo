import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class PublisherSupportPageTests(unittest.TestCase):
    def test_openai_support_is_dedicated_rumbo_crm_surface(self):
        html = (ROOT / "openai-support.html").read_text(encoding="utf-8-sig").lower()
        self.assertIn("<title>rumbo crm support</title>", html)
        self.assertIn("support for rumbo crm", html)
        self.assertIn("rumbo ia · rumbo crm support", html)
        self.assertIn("proposal-only", html)
        self.assertIn("mailto:sebastian@rumbo.verso.fans", html)
        self.assertIn("/openai-privacy", html)
        self.assertIn("/openai-terms", html)
        self.assertIn("do not send passwords", html)
        self.assertIn("does not claim openai approval", html)
        self.assertNotIn("rumbo ia crm", html)
        self.assertNotIn("turn customer conversations into", html)

if __name__ == "__main__":
    unittest.main()
