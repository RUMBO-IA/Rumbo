import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_public_privacy as gate


class PrivacyDiagnosticTests(unittest.TestCase):
    def test_denied_line_numbers_reports_location_without_value(self):
        secret_value = "private marker"
        deny = {gate.sha(secret_value)}
        text = "safe line\ncontains private marker here\nsafe again"
        self.assertEqual(gate.denied_line_numbers(text, deny), [2])


if __name__ == "__main__":
    unittest.main()
