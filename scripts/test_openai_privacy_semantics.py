import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class PublisherPrivacyPageTests(unittest.TestCase):
    def test_openai_privacy_covers_bounded_mcp_processing(self):
        html = (ROOT / "openai-privacy.html").read_text(encoding="utf-8-sig").lower()
        self.assertIn("rumbo crm privacy", html)
        self.assertIn("remote mcp", html)
        self.assertIn("workspace identifiers", html)
        self.assertIn("subject or lead identifiers", html)
        self.assertIn("a note", html)
        self.assertIn("lead stages", html)
        self.assertIn("outreach channel", html)
        self.assertIn("outreach objective", html)
        self.assertIn("review_required", html)
        self.assertIn("side_effect=false", html)
        self.assertIn("send_authorized=false", html)
        self.assertIn("does not sell", html)
        self.assertIn("does not persist submitted tool arguments", html)
        self.assertIn("does not expose customer-record search", html)
        self.assertIn("mailto:sebastian@rumbo.verso.fans", html)
        self.assertNotIn("used for anything else", html)

if __name__ == "__main__":
    unittest.main()
