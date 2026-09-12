import pathlib
import unittest

from scripts import verify_brand_contract as brand


class ContentImprintContractTests(unittest.TestCase):
    def test_rumbo_labs_is_admitted_only_as_content_imprint(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        self.assertEqual(("PASS", "authorized_identity_role"), brand.admit_identity("RUMBO Labs", "CONTENT_IMPRINT", root))
        for forbidden_role in ("PARENT_BRAND", "PUBLIC_EXPRESSION", "PRODUCT", "OFFER", "PROFILE", "TECH_NAMESPACE", "SHORT_FORM"):
            self.assertEqual(("SAFE_STOP", "role_not_allowed"), brand.admit_identity("RUMBO Labs", forbidden_role, root))

    def test_existing_brand_contract_still_passes(self):
        root = pathlib.Path(__file__).resolve().parents[1]
        self.assertEqual([], brand.verify(root))


if __name__ == "__main__":
    unittest.main()
