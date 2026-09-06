import unittest
from pathlib import Path

from scripts import verify_commercial_coherence as verifier

ROOT = Path(__file__).resolve().parents[1]


class CommercialCoherenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.landing_en = (ROOT / "apps/landing-publica/index.html").read_text(encoding="utf-8")
        cls.landing_es = (ROOT / "apps/landing-publica/index-es.html").read_text(encoding="utf-8")

    def test_current_public_surface_passes(self):
        self.assertEqual(verifier.check(self.readme, self.html), [])

    def test_all_tracked_public_landings_are_commercially_coherent(self):
        combined = self.html + "\n" + self.landing_en + "\n" + self.landing_es
        self.assertEqual(verifier.check(self.readme, combined), [])

    def test_stale_social_handle_is_rejected(self):
        errors = verifier.check(self.readme, self.html + "\n@rumbo_ia")
        self.assertIn("STALE_SOCIAL_HANDLE", errors)

    def test_monthly_pricing_wording_is_rejected(self):
        for wording in ("USD 149 a month", "USD 149 al mes"):
            with self.subTest(wording=wording):
                errors = verifier.check(self.readme, self.html + "\n" + wording)
                self.assertIn("MONTHLY_PRICE", errors)

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


    def test_slash_mo_monthly_pricing_is_rejected(self):
        self.assertIn("MONTHLY_PRICE", verifier.check(self.readme, self.html + "\nUSD 349/mo"))

    def test_legacy_commercial_catalog_is_rejected(self):
        for marker in ("RUMBO Capture", "RUMBO Recovery", "RUMBO Front Desk AI", "RUMBO Growth Engine", "Plan Growth completo"):
            with self.subTest(marker=marker):
                self.assertIn("LEGACY_COMMERCIAL_CATALOG", verifier.check(self.readme, self.html + "\n" + marker))

    def test_unverified_tool_counts_are_rejected(self):
        for wording in ("13 tools", "More than 14 tools", "14 herramientas", "Más de 14 herramientas"):
            with self.subTest(wording=wording):
                self.assertIn("UNVERIFIED_TOOL_COUNT", verifier.check(self.readme, self.html + "\n" + wording))

    def test_fake_form_success_is_rejected(self):
        for wording in ("Mensaje enviado", "Message sent"):
            with self.subTest(wording=wording):
                self.assertIn("FAKE_FORM_SUCCESS", verifier.check(self.readme, self.html + "\n" + wording))

    def test_mislabeled_typeform_route_is_rejected(self):
        sample = self.html + f'\n<a href="{verifier.TYPEFORM}" aria-label="WhatsApp directo">Email directo</a>'
        self.assertIn("MISLABELED_TYPEFORM_ROUTE", verifier.check(self.readme, sample))

    def test_generic_social_destinations_are_rejected(self):
        for url in ("https://www.linkedin.com", "https://www.instagram.com"):
            with self.subTest(url=url):
                self.assertIn("GENERIC_SOCIAL_DESTINATION", verifier.check(self.readme, self.html + f'\n<a href="{url}">Social</a>'))


if __name__ == "__main__":
    unittest.main()
