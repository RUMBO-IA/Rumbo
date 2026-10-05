import unittest
from pathlib import Path

from scripts import verify_commercial_coherence as verifier

ROOT = Path(__file__).resolve().parents[1]


class CommercialCoherenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")

    def test_current_public_surface_passes(self):
        self.assertEqual(verifier.check(self.readme, self.html), [])

    def test_current_commercial_entrypoints_pass(self):
        self.assertEqual(
            verifier.check_commercial_entrypoints(
                self.html,
                (ROOT / "login.html").read_text(encoding="utf-8"),
                (ROOT / "terms.html").read_text(encoding="utf-8"),
                (ROOT / "refund.html").read_text(encoding="utf-8"),
                (ROOT / "portal.js").read_text(encoding="utf-8"),
            ),
            [],
        )

    def test_workspace_plan_cannot_be_entitlement_authority(self):
        portal = (ROOT / "portal.js").read_text(encoding="utf-8") + "\nworkspace.plan_id"
        errors = verifier.check_commercial_entrypoints(
            self.html, "email login", '<a href="/refund">Refund</a>',
            '<h1>Refund Policy</h1>', portal,
        )
        self.assertIn("WORKSPACE_PLAN_USED_AS_ENTITLEMENT", errors)

    def test_subscription_plan_query_is_required(self):
        portal = (ROOT / "portal.js").read_text(encoding="utf-8").replace(
            "subscriptions?select=plan_id,status,current_period_start,current_period_end",
            "subscriptions?select=status",
        )
        errors = verifier.check_commercial_entrypoints(
            self.html, "email login", '<a href="/refund">Refund</a>',
            '<h1>Refund Policy</h1>', portal,
        )
        self.assertIn("SUBSCRIPTION_PLAN_QUERY_MISSING", errors)

    def test_unverified_google_login_is_rejected(self):
        errors = verifier.check_commercial_entrypoints(
            self.html, '<button id="google-button">Continue with Google</button>',
            '<a href="/refund">Refund</a>', '<h1>Refund Policy</h1>',
            (ROOT / "portal.js").read_text(encoding="utf-8"),
        )
        self.assertIn("UNVERIFIED_GOOGLE_LOGIN_VISIBLE", errors)

    def test_monthly_pricing_is_rejected(self):
        errors = verifier.check(self.readme, self.html + "\n<div>USD 149/mes</div>")
        self.assertIn("MONTHLY_PRICE", errors)

    def test_any_public_mailto_is_rejected(self):
        errors = verifier.check(
            self.readme,
            self.html + '\n<a href="mailto:' + "test" + "@" + 'example.com">Contacto</a>',
        )
        self.assertIn("PUBLIC_MAILTO", errors)

    def test_noncanonical_typeform_is_rejected(self):
        changed = self.html.replace(
            verifier.TYPEFORM,
            "https://form.typeform.com/to/WRONG123",
        )
        errors = verifier.check(self.readme, changed)
        self.assertIn("NONCANONICAL_TYPEFORM", errors)
        self.assertIn("CANONICAL_TYPEFORM_ANCHOR_MISSING", errors)

    def test_internal_contact_cta_is_required(self):
        changed = self.html.replace('href="#contacto"', 'href="#producto"', 1)
        errors = verifier.check(self.readme, changed)
        self.assertIn("CONTACT_CTA_MISSING", errors)


if __name__ == "__main__":
    unittest.main()
