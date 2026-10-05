import json
import pathlib
import tempfile
import unittest
from unittest import mock

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

    def test_discovers_relative_same_origin_stylesheet(self):
        html = b'<html><head><link rel="stylesheet" href="styles.css"></head></html>'
        result = surface.discover_same_origin_stylesheets(
            html,
            "https://rumbo.verso.fans/openai-support",
            "rumbo.verso.fans",
        )
        self.assertEqual(["/styles.css"], result)

    def test_ignores_external_stylesheet(self):
        html = (
            b'<link rel="stylesheet" href="https://cdn.example.com/x.css">'
            b'<link rel="stylesheet" href="/styles.css">'
        )
        result = surface.discover_same_origin_stylesheets(
            html,
            "https://rumbo.verso.fans/openai-support",
            "rumbo.verso.fans",
        )
        self.assertEqual(["/styles.css"], result)

    def test_source_path_for_asset_strips_query(self):
        self.assertEqual(
            "styles.css",
            surface.source_path_for_asset("/styles.css?v=1"),
        )

    @mock.patch.object(surface, "fetch_url")
    @mock.patch.object(surface, "read_authorized_source")
    def test_verify_asset_reports_http_failure(self, read_source, fetch_url):
        read_source.return_value = b"body"
        fetch_url.return_value = (404, b"missing")
        check, body = surface.verify_asset(
            domain="rumbo.verso.fans",
            route="/styles.css",
            source_path="styles.css",
            root=pathlib.Path("."),
            app_sha="a" * 40,
            timeout=1.0,
        )
        self.assertEqual("HTTP_FAIL", check["status"])
        self.assertIsNone(body)

    @mock.patch.object(surface, "read_authorized_source")
    def test_verify_asset_reports_missing_authorized_source(self, read_source):
        read_source.side_effect = RuntimeError("missing")
        check, body = surface.verify_asset(
            domain="rumbo.verso.fans",
            route="/privacy",
            source_path="privacy.html",
            root=pathlib.Path("."),
            app_sha="a" * 40,
            timeout=1.0,
        )
        self.assertEqual("SOURCE_MISSING", check["status"])
        self.assertIsNone(body)

    def test_trust_center_routes_are_required_by_production_watch(self):
        expected = {
            "/trust-center",
            "/processing-terms",
            "/subprocessors",
            "/retention",
            "/responsible-ai",
            "/security",
            "/incident-response",
            "/continuity",
            "/support-policy",
            "/status",
            "/refund",
            "/support",
        }
        actual = {route for route, _ in surface.TRUST_HTML_ROUTES}
        self.assertEqual(expected, actual)
        self.assertTrue(expected.issubset({route for route, _ in surface.HTML_ROUTES}))

    @mock.patch.object(surface, "verify_asset")
    def test_verify_surface_discovers_stylesheet_from_each_html_route(self, verify_asset):
        def fake_verify_asset(**kwargs):
            route = kwargs["route"]
            if route == "/styles.css":
                return ({
                    "route": route,
                    "source_path": "styles.css",
                    "url": "https://rumbo.verso.fans/styles.css",
                    "status": "PASS",
                }, b"body{}")
            return ({
                "route": route,
                "source_path": kwargs["source_path"],
                "url": "https://rumbo.verso.fans" + route,
                "status": "PASS",
            }, b'<link rel="stylesheet" href="/styles.css">')

        verify_asset.side_effect = fake_verify_asset
        result = surface.verify_surface(
            pathlib.Path("."),
            {
                "domain": "rumbo.verso.fans",
                "application_sha": "a" * 40,
                "deployment_id": "dpl_test",
            },
            1.0,
        )
        stylesheet_checks = [
            check for check in result["checks"]
            if check.get("dependency_type") == "stylesheet"
        ]
        self.assertEqual(1, len(stylesheet_checks))
        self.assertEqual("/styles.css", stylesheet_checks[0]["route"])
        self.assertEqual("PASS", result["status"])

    @mock.patch.object(surface.urllib.request, "urlopen")
    def test_fetch_url_rejects_redirected_final_url(self, urlopen):
        response = mock.MagicMock()
        response.status = 200
        response.read.return_value = b"same-body"
        response.geturl.return_value = "https://rumbo.verso.fans/openai-privacy"
        urlopen.return_value.__enter__.return_value = response

        with self.assertRaisesRegex(RuntimeError, "redirect"):
            surface.fetch_url("https://rumbo.verso.fans/privacy", timeout=1.0)

    @mock.patch.object(surface, "verify_asset")
    def test_verify_surface_does_not_discover_dependencies_from_drift(self, verify_asset):
        def fake_verify_asset(**kwargs):
            route = kwargs["route"]
            if route.startswith("/evil.css"):
                self.fail("dependency discovery must not use drifted HTML")
            return ({
                "route": route,
                "source_path": kwargs["source_path"],
                "url": "https://rumbo.verso.fans" + route,
                "status": "DRIFT",
            }, b'<link rel="stylesheet" href="/evil.css?v=1">')

        verify_asset.side_effect = fake_verify_asset
        result = surface.verify_surface(
            pathlib.Path("."),
            {
                "domain": "rumbo.verso.fans",
                "application_sha": "a" * 40,
                "deployment_id": "dpl_test",
            },
            1.0,
        )
        self.assertEqual(len(surface.HTML_ROUTES), verify_asset.call_count)
        self.assertEqual("DRIFT", result["status"])


if __name__ == "__main__":
    unittest.main()
