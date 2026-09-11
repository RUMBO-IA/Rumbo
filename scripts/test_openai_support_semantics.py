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

    def test_publisher_surfaces_follow_canonical_brand_hierarchy(self):
        surfaces = {
            "support": (ROOT / "openai-support.html").read_text(encoding="utf-8-sig").lower(),
            "privacy": (ROOT / "openai-privacy.html").read_text(encoding="utf-8-sig").lower(),
            "terms": (ROOT / "openai-terms.html").read_text(encoding="utf-8-sig").lower(),
        }
        for name, html in surfaces.items():
            with self.subTest(surface=name):
                self.assertNotIn("rumbo ia crm", html)
                self.assertNotIn("rumbo avanza", html)
                self.assertNotIn("avanza", html)
        self.assertIn("rumbo crm", surfaces["support"])
        self.assertIn("rumbo crm", surfaces["privacy"])
        self.assertIn("rumbo crm", surfaces["terms"])
        self.assertIn("rumbo ia", surfaces["privacy"])
        self.assertIn("rumbo ia", surfaces["terms"])

if __name__ == "__main__":
    unittest.main()
