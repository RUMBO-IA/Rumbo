import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LISTING = ROOT / "openai-publication" / "agent-reliability" / "submission" / "listing.json"

class AgentReliabilitySupportListingTests(unittest.TestCase):
    def test_support_url_uses_dedicated_semantic_support_surface(self):
        listing = json.loads(LISTING.read_text(encoding="utf-8"))
        urls = listing["publisher_urls"]
        self.assertEqual(urls["support"], "https://rumbo-openai-support.val.run/")
        self.assertEqual(urls["website"], "https://rumbo.verso.fans/")
        self.assertEqual(urls["privacy"], "https://rumbo.verso.fans/openai-privacy")
        self.assertEqual(urls["terms"], "https://rumbo.verso.fans/openai-terms")

if __name__ == "__main__":
    unittest.main()
