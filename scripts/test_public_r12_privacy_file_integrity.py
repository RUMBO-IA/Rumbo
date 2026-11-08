"""PUBLIC R12 privacy-scanner fail-closed reads, isolated adversarial fixtures.

No private deny-list, no external calls, no production mutation.
"""
import pathlib
import tempfile
import unittest
from unittest import mock

from scripts import verify_public_privacy as gate


class PrivacyReadIntegrityTests(unittest.TestCase):
    def assert_scanner_read_rejected(self, filename: str, data: bytes) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / filename
            path.write_bytes(data)
            with self.assertRaisesRegex(gate.PrivacyScanReadError, "tracked"):
                gate.text_of(path)

    def test_unreadable_tracked_html_is_not_silently_skipped(self):
        path = pathlib.Path("tests/privacy-unreadable.html")
        with mock.patch.object(pathlib.Path, "read_bytes", side_effect=PermissionError("read denied")):
            with self.assertRaisesRegex(gate.PrivacyScanReadError, "tracked"):
                gate.text_of(path)

    def test_missing_tracked_file_is_not_silently_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(gate.PrivacyScanReadError, "tracked"):
                gate.text_of(pathlib.Path(tmp) / "tracked.txt")

    def test_html_embedded_nul_is_not_treated_as_safe_binary(self):
        self.assert_scanner_read_rejected("public.html", b"<html>\0private@example.invalid</html>")

    def test_js_embedded_nul_is_not_treated_as_safe_binary(self):
        self.assert_scanner_read_rejected("public.js", b"const a='private@example.invalid';\0")

    def test_markdown_invalid_utf8_is_not_silently_skipped(self):
        self.assert_scanner_read_rejected("readme.md", b"email@example.invalid\xff")

    def test_svg_embedded_nul_is_not_silently_skipped(self):
        self.assert_scanner_read_rejected("logo.svg", b"<svg>\0bad</svg>")

    def test_text_uppercase_suffix_is_also_strict(self):
        self.assert_scanner_read_rejected("PUBLIC.HTML", b"<html>\0content</html>")

    def test_binary_png_still_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "image.png"
            p.write_bytes(b"\x89PNG\0\xff")
            self.assertIsNone(gate.text_of(p))

    def test_valid_utf8_html_scanned_normally(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "index.html"
            p.write_text("Contacto: public@example.invalid", encoding="utf-8")
            self.assertEqual(gate.text_of(p), "Contacto: public@example.invalid")

    def test_no_extension_nonbinary_is_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / "LICENSE"
            p.write_bytes(b"public terms")
            self.assertEqual(gate.text_of(p), "public terms")


if __name__ == "__main__":
    unittest.main()
