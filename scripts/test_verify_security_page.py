import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SecurityPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.security = (ROOT / "security.html").read_text(encoding="utf-8")
        cls.home = (ROOT / "index.html").read_text(encoding="utf-8")

    def test_security_page_and_home_link_are_present(self):
        self.assertIn("https://rumbo.verso.fans/security", self.security)
        self.assertIn("Security & Agent Reliability", self.security)
        self.assertIn("owned, operated, or explicitly authorized", self.security)
        self.assertIn("not exposed to customers or third parties", self.security)
        self.assertIn("verifiable-agent-control-plane", self.security)
        self.assertIn('href="/security"', self.home)

    def test_security_page_uses_public_founder_identity(self):
        self.assertIn("Founder: Sebastián Federico", self.security)
        self.assertNotIn("mailto:", self.security)

    def test_security_page_does_not_make_positive_unproven_service_claims(self):
        lower = self.security.lower()
        for forbidden in ("we provide managed soc", "we offer commercial pentesting", "we operate a certified red team"):
            self.assertNotIn(forbidden, lower)
