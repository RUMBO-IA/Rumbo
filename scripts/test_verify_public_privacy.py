import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_public_privacy as gate


class PrivacyGateRegressionTests(unittest.TestCase):
    def test_email_candidates_preserve_punctuation(self):
        value = "private.person+tag" + "@" + "example.test"
        self.assertEqual(list(gate.email_candidates(f"contact={value}")), [value])

    def test_denied_email_is_detected_as_exact_value(self):
        value = "private.person" + "@" + "example.test"
        deny = {gate.sha(value)}
        self.assertTrue(gate.text_has_denied_value(f"owner: {value}", deny))

    def test_unapproved_email_is_rejected_without_secret_hash(self):
        value = "private.person" + "@" + "example.test"
        self.assertTrue(gate.text_has_unapproved_email(f"owner: {value}"))

    def test_approved_business_email_is_allowed(self):
        value = "sebastian@rumbo.verso.fans"
        self.assertFalse(gate.text_has_unapproved_email(f"contact: {value}"))

    def test_github_noreply_email_is_allowed(self):
        value = "293577326+fscfede-beep@users.noreply.github.com"
        self.assertFalse(gate.text_has_unapproved_email(f"commit: {value}"))

    def test_word_ngram_deny_behavior_is_preserved(self):
        deny = {gate.sha("private surname")}
        self.assertTrue(gate.text_has_denied_value("hello private surname world", deny))


if __name__ == "__main__":
    unittest.main()
