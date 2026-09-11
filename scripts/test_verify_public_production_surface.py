import json
import pathlib
import tempfile
import unittest

from scripts import verify_public_production_surface as surface


class PublicProductionSurfaceTests(unittest.TestCase):
    def test_exact_content_passes(self):
        source = b"<html>\nRUMBO IA\n</html>\n"
        live = b"<html>\r\nRUMBO IA\r\n</html>\r\n"
        result = surface.compare_surface(source, live)
        self.assertTrue(result["match"])
        self.assertEqual(result["source_sha256"], result["live_sha256"])

    def test_material_content_drift_fails(self):
        source = b"<html>RUMBO IA</html>"
        live = b"<html>OTHER</html>"
        self.assertFalse(surface.compare_surface(source, live)["match"])

    def test_normalization_does_not_hide_text_drift(self):
        source = b"A\nB\n"
        live = b"A\r\nC\r\n"
        self.assertFalse(surface.compare_surface(source, live)["match"])

    def test_invalid_utf8_fails_closed(self):
        with self.assertRaises(UnicodeDecodeError):
            surface.normalize_html(b"\xff\xfe")

    def test_lock_requires_authorized_status(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / "lock.json"
            path.write_text(json.dumps({
                "application_sha": "a" * 40,
                "deployment_id": "dpl_test",
                "domain": "example.com",
                "status": "HOLD",
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "not AUTHORIZED"):
                surface.load_lock(path)

    def test_lock_requires_domain(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / "lock.json"
            path.write_text(json.dumps({
                "application_sha": "a" * 40,
                "deployment_id": "dpl_test",
                "status": "AUTHORIZED",
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing domain"):
                surface.load_lock(path)


if __name__ == "__main__":
    unittest.main()
