import json
import pathlib
import tempfile
import unittest

from scripts import verify_brand_contract as brand

BASE_STYLE = ":root{--bg:#080c12;--panel:#101722;--panel2:#141e2c;--line:#263246;--text:#f7f9fc;--muted:#9aa8ba;--orange:#ff7a45;--green:#63ddb0;--blue:#7aa7ff;--red:#ff7b88}"
BASE_INDEX = f"<title>RUMBO IA</title><style>{BASE_STYLE}</style><p>IA con control humano</p><span>DATOS SIMULADOS</span>"
BASE_README = "# RUMBO IA\nHuman-controlled AI CRM. main is not production. Production: rumbo.verso.fans application 34c625c65e047fdec06a5bef7064d2de6bed48ba deployment dpl_8KbqvsKuua22xK4EQYZmtF3KXmNK."
SECONDARY = "<title>RUMBO IA</title><p>Human-controlled AI workspace.</p>"
SECONDARY_README = "# RUMBO IA secondary landing\nHuman-controlled candidate surface. Production promotion requires a publication receipt."
LEGAL = "<title>RUMBO IA</title><p>Legal information for RUMBO IA.</p>"
REGISTRY = {
    "schema_version": 1,
    "roles": ["PARENT_BRAND","PUBLIC_EXPRESSION","PRODUCT","OFFER","PROFILE","TECH_NAMESPACE","SHORT_FORM"],
    "identities": {
        "RUMBO": ["PARENT_BRAND","SHORT_FORM"],
        "RUMBO IA": ["PUBLIC_EXPRESSION"],
        "RUMBO-IA": ["TECH_NAMESPACE"],
        "RUMBO Agent Reliability": ["PRODUCT"],
        "RUMBO Guardian": ["PRODUCT"],
        "Revenue Recovery Sprint": ["OFFER"],
    },
    "non_canonical": ["Avanza", "RUMBO Labs"],
    "invariants": ["KNOWN_NAME != ALLOWED_ROLE","UNKNOWN_NAME != NEW_BRAND_AUTHORITY","NON_CANONICAL_NAME = SAFE_STOP"],
}
PRODUCTION_LOCK = {
    "schema_version": 1,
    "registry_issue": "RUMBO-IA/Rumbo#72",
    "owner_authorization_comment_id": 5630078910,
    "application_sha": "34c625c65e047fdec06a5bef7064d2de6bed48ba",
    "deployment_id": "dpl_8KbqvsKuua22xK4EQYZmtF3KXmNK",
    "domain": "rumbo.verso.fans",
    "status": "AUTHORIZED",
    "invariant": "MAIN_ADVANCE != PRODUCTION_AUTHORITY",
}

DISTRIBUTION_LOCK = {
    "schema_version": 1, "registry_issue": "RUMBO-IA/Rumbo#72", "observed_at": "2026-09-11",
    "overall_status": "PARTIAL_PASS", "required_channels": ["website","youtube","x","linkedin"],
    "channels": {
        "website": {"binding":"PASS","profile_alignment":"PASS","readback":"PASS"},
        "youtube": {"binding":"PASS","profile_alignment":"PASS","readback":"PASS"},
        "x": {"binding":"PASS","profile_alignment":"UNRESOLVED_CONFLICT","readback":"PASS"},
        "linkedin": {"binding":"PASS","profile_alignment":"COMPANY_SURFACE_ABSENT","readback":"API_LIMITED"}},
    "optional_channels": {"metricool": {"binding":"CONNECTED_NO_NETWORKS","profile_alignment":"N/A","readback":"PASS"}},
    "invariant": "DISTRIBUTION_PASS_REQUIRES_ALL_REQUIRED_CHANNELS_PASS"}


def make_surface(root: pathlib.Path, index: str = BASE_INDEX, readme: str = BASE_README, registry=REGISTRY, production_lock=PRODUCTION_LOCK, distribution_lock=DISTRIBUTION_LOCK) -> None:
    (root / "index.html").write_text(index, encoding="utf-8")
    (root / "README.md").write_text(readme, encoding="utf-8")
    d = root / "docs" / "brand"
    d.mkdir(parents=True)
    (d / "identity_registry_v1.json").write_text(json.dumps(registry), encoding="utf-8")
    (d / "production_lock_v1.json").write_text(json.dumps(production_lock), encoding="utf-8")
    (d / "distribution_lock_v1.json").write_text(json.dumps(distribution_lock), encoding="utf-8")
    landing = root / "apps" / "landing-publica"
    landing.mkdir(parents=True)
    for name in ("index.html", "index-es.html", "index-en-openai.html"):
        (landing / name).write_text(SECONDARY, encoding="utf-8")
    (landing / "README.md").write_text(SECONDARY_README, encoding="utf-8")
    (landing / "privacy.html").write_text(LEGAL, encoding="utf-8")
    (landing / "terms.html").write_text(LEGAL, encoding="utf-8")


class BrandContractTests(unittest.TestCase):
    def test_valid_surface_with_legal_pages_passes(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            self.assertEqual([], brand.verify(root))

    def test_legal_pages_are_exempt_only_from_human_control_positioning(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            errors = brand.verify(root)
            self.assertFalse(any("privacy.html" in e and "human-control" in e for e in errors))
            self.assertFalse(any("terms.html" in e and "human-control" in e for e in errors))

    def test_legal_pages_still_reject_unsupported_claims(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            p = root / "apps/landing-publica/privacy.html"
            p.write_text(LEGAL + "<p>fully autonomous</p>", encoding="utf-8")
            self.assertTrue(any("privacy.html" in e and "fully autonomous" in e for e in brand.verify(root)))

    def test_legal_pages_still_reject_noncanonical_aliases(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            p = root / "apps/landing-publica/terms.html"
            p.write_text(LEGAL + "<p>Rumbo AI</p>", encoding="utf-8")
            self.assertTrue(any("terms.html" in e and "non-canonical public alias" in e for e in brand.verify(root)))

    def test_noncanonical_brand_is_rejected_on_primary(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root, BASE_INDEX + "<p>Avanza</p>")
            self.assertTrue(any("non-canonical brand present" in e for e in brand.verify(root)))

    def test_noncanonical_brand_is_rejected_on_secondary(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            (root / "apps/landing-publica/index-es.html").write_text(SECONDARY + "<p>Avanza</p>", encoding="utf-8")
            self.assertTrue(any("non-canonical brand present" in e for e in brand.verify(root)))

    def test_rumbo_labs_collision_is_explicitly_noncanonical(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            self.assertEqual(("SAFE_STOP", "non_canonical"), brand.admit_identity("RUMBO Labs", "PUBLIC_EXPRESSION", root))

    def test_unknown_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            self.assertEqual(("SAFE_STOP", "unknown_identity"), brand.admit_identity("InventedCo", "PARENT_BRAND", root))

    def test_wrong_role_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            self.assertEqual(("SAFE_STOP", "role_not_allowed"), brand.admit_identity("RUMBO-IA", "PARENT_BRAND", root))

    def test_known_parent_passes_case_insensitive(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            self.assertEqual(("PASS", "authorized_identity_role"), brand.admit_identity("rumbo", "PARENT_BRAND", root))

    def test_missing_registry_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            (root / "docs/brand/identity_registry_v1.json").unlink()
            self.assertTrue(any("registry" in e for e in brand.verify(root)))

    def test_registry_overlap_fails_closed_case_insensitive(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); bad = dict(REGISTRY); bad["non_canonical"] = ["rumbo"]
            make_surface(root, registry=bad)
            self.assertTrue(any("overlap" in e for e in brand.verify(root)))

    def test_unknown_role_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            self.assertEqual(("SAFE_STOP", "unknown_role"), brand.admit_identity("RUMBO", "CEO_BRAND", root))

    def test_claim_normalization_catches_case_and_punctuation(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root, BASE_INDEX + "<p>GUARANTEED—ROI</p>")
            self.assertTrue(any("guaranteed roi" in e for e in brand.verify(root)))

    def test_extra_marketing_html_requires_human_control(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            (root / "apps/landing-publica/campaign.html").write_text("<title>RUMBO IA</title><p>Campaign</p>", encoding="utf-8")
            self.assertTrue(any("campaign.html" in e and "human-control" in e for e in brand.verify(root)))

    def test_extra_marketing_html_scans_claims(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            (root / "apps/landing-publica/campaign.html").write_text(SECONDARY + "<p>fully-autonomous</p>", encoding="utf-8")
            self.assertTrue(any("campaign.html" in e and "fully autonomous" in e for e in brand.verify(root)))

    def test_missing_required_secondary_surface_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            (root / "apps/landing-publica/index-es.html").unlink()
            self.assertTrue(any("index-es.html" in e for e in brand.verify(root)))

    def test_secondary_readme_requires_publication_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            (root / "apps/landing-publica/README.md").write_text("# RUMBO IA\nHuman-controlled candidate.", encoding="utf-8")
            errors = brand.verify(root)
            self.assertTrue(any("publication/production authority boundary" in e for e in errors))
            self.assertTrue(any("publication receipt" in e for e in errors))

    def test_primary_readme_requires_main_production_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root, readme="# RUMBO IA\nHuman-controlled AI CRM.")
            self.assertTrue(any("main-vs-production" in e for e in brand.verify(root)))

    def test_missing_production_lock_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            (root / "docs/brand/production_lock_v1.json").unlink()
            self.assertTrue(any("production authority lock invalid" in e for e in brand.verify(root)))

    def test_invalid_production_lock_sha_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); bad = dict(PRODUCTION_LOCK); bad["application_sha"] = "abc"
            make_surface(root, production_lock=bad)
            self.assertTrue(any("application_sha" in e for e in brand.verify(root)))

    def test_production_lock_must_bind_canonical_registry(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); bad = dict(PRODUCTION_LOCK); bad["registry_issue"] = "RUMBO-IA/Rumbo#999"
            make_surface(root, production_lock=bad)
            self.assertTrue(any("canonical registry" in e for e in brand.verify(root)))

    def test_readme_production_binding_must_match_lock(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td)
            readme = BASE_README.replace(PRODUCTION_LOCK["deployment_id"], "dpl_UNAUTHORIZED123")
            make_surface(root, readme=readme)
            self.assertTrue(any("deployment_id" in e and "authorized lock" in e for e in brand.verify(root)))


    def test_missing_distribution_lock_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); make_surface(root)
            (root / "docs/brand/distribution_lock_v1.json").unlink()
            self.assertTrue(any("distribution lock invalid" in e for e in brand.verify(root)))

    def test_distribution_pass_rejects_incomplete_required_channel(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); bad = json.loads(json.dumps(DISTRIBUTION_LOCK)); bad["overall_status"] = "PASS"
            make_surface(root, distribution_lock=bad)
            self.assertTrue(any("distribution PASS forbidden" in e for e in brand.verify(root)))

    def test_distribution_pass_accepts_all_required_channels_complete(self):
        with tempfile.TemporaryDirectory() as td:
            root = pathlib.Path(td); good = json.loads(json.dumps(DISTRIBUTION_LOCK)); good["overall_status"] = "PASS"
            for name in good["required_channels"]:
                good["channels"][name] = {"binding":"PASS","profile_alignment":"PASS","readback":"PASS"}
            make_surface(root, distribution_lock=good)
            self.assertEqual([], brand.verify(root))

    def test_required_palette_contains_primary_and_status_colors(self):
        for color in ("#ff7a45", "#63ddb0", "#7aa7ff", "#ff7b88"):
            self.assertIn(color, brand.REQUIRED_PRIMARY_COLORS)


if __name__ == "__main__":
    unittest.main()
