import unittest
from pathlib import Path

from scripts import verify_commercial_coherence as verifier

ROOT = Path(__file__).resolve().parents[1]


class CommercialCoherenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = (ROOT / "README.md").read_text(encoding="utf-8")
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.variant_en = verifier.PUBLIC_VARIANTS[0].read_text(encoding="utf-8")
        cls.variant_es = verifier.PUBLIC_VARIANTS[1].read_text(encoding="utf-8")

    def test_current_public_surface_passes(self):
        self.assertEqual(verifier.check(self.readme, self.html), [])

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

    def test_public_variants_match_current_one_time_offer(self):
        self.assertEqual(
            verifier.check_public_variant(verifier.PUBLIC_VARIANTS[0], self.variant_en),
            [],
        )
        self.assertEqual(
            verifier.check_public_variant(verifier.PUBLIC_VARIANTS[1], self.variant_es),
            [],
        )

    def test_public_variant_recurring_price_is_rejected(self):
        changed = self.variant_en + "\n<div>USD 149/month</div>"
        errors = verifier.check_public_variant(verifier.PUBLIC_VARIANTS[0], changed)
        self.assertTrue(any(e.startswith("PUBLIC_VARIANT_RECURRING_PRICE:") for e in errors))

    def test_public_variant_monthly_catalog_is_rejected(self):
        changed = self.variant_en + "\n<script>const p={monthly:149}</script>"
        errors = verifier.check_public_variant(verifier.PUBLIC_VARIANTS[0], changed)
        self.assertTrue(any(e.startswith("PUBLIC_VARIANT_RECURRING_CATALOG:") for e in errors))

    def test_python_bytecode_is_ignored(self):
        rules = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("__pycache__/", rules)
        self.assertIn("*.py[cod]", rules)


if __name__ == "__main__":
    unittest.main()
