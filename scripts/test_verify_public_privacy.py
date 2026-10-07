import sys
import unittest
from pathlib import Path
from unittest import mock

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

    def test_github_managed_context_does_not_bypass_private_author_name(self):
        value = "Private Author Name"
        env = {
            "RUMBO_GITHUB_MANAGED_COMMIT": "1",
            "RUMBO_GITHUB_MANAGED_SHA": "abc123",
            "RUMBO_GITHUB_EVENT_NAME": "push",
            "RUMBO_GITHUB_REF": "refs/heads/main",
            "RUMBO_GITHUB_ACTOR": gate.TRUSTED_GITHUB_ACTOR,
            "RUMBO_GITHUB_SENDER": gate.TRUSTED_GITHUB_ACTOR,
            "RUMBO_GITHUB_FORCED": "false",
        }
        with mock.patch.dict(gate.os.environ, env, clear=True):
            self.assertFalse(gate.approved_head_author_name(value, "abc123", set()))

    def test_github_managed_context_does_not_bypass_private_author_email(self):
        value = "private.author" + "@" + "example.test"
        env = {
            "RUMBO_GITHUB_MANAGED_COMMIT": "1",
            "RUMBO_GITHUB_MANAGED_SHA": "abc123",
            "RUMBO_GITHUB_EVENT_NAME": "push",
            "RUMBO_GITHUB_REF": "refs/heads/main",
            "RUMBO_GITHUB_ACTOR": gate.TRUSTED_GITHUB_ACTOR,
            "RUMBO_GITHUB_SENDER": gate.TRUSTED_GITHUB_ACTOR,
            "RUMBO_GITHUB_FORCED": "false",
        }
        with mock.patch.dict(gate.os.environ, env, clear=True):
            self.assertFalse(gate.approved_head_author_email(value, "abc123", set()))

    def test_committer_name_must_be_public(self):
        self.assertNotIn("Private Committer Name", gate.APPROVED_COMMITTER_NAMES)
        self.assertIn("GitHub", gate.APPROVED_COMMITTER_NAMES)

    def test_legacy_metadata_exception_is_exact_sha_and_field_scoped(self):
        legacy = "7734270af5e1928215838fb0f0aee940599d43e4"
        self.assertTrue(gate.is_legacy_metadata_exception(legacy, "committer-name"))
        self.assertTrue(gate.is_legacy_metadata_exception(legacy, "committer-email"))
        self.assertFalse(gate.is_legacy_metadata_exception(legacy, "author-name"))
        self.assertFalse(gate.is_legacy_metadata_exception(legacy, "author-email"))
        self.assertFalse(gate.is_legacy_metadata_exception("a" * 40, "committer-email"))

    def test_brand_rebase_committer_exceptions_are_exact_sha_and_name_only(self):
        for commit_sha in (
            "a276feac777f51320c451a935659ace32db071be",
            "a80215e0fe334b8cec6976da2fc7bf20fe61d4da",
        ):
            self.assertTrue(gate.is_legacy_metadata_exception(commit_sha, "committer-name"))
            self.assertFalse(gate.is_legacy_metadata_exception(commit_sha, "committer-email"))
            self.assertFalse(gate.is_legacy_metadata_exception(commit_sha, "author-name"))
            self.assertFalse(gate.is_legacy_metadata_exception(commit_sha, "author-email"))
        self.assertFalse(gate.is_legacy_metadata_exception("b" * 40, "committer-name"))

    def test_pr199_merge_committer_exception_is_exact_sha_and_name_only(self):
        merge_sha = "5b27fce34ac1884312bfd4c5293bd5fa8fd84b51"
        self.assertTrue(gate.is_legacy_metadata_exception(merge_sha, "committer-name"))
        self.assertFalse(gate.is_legacy_metadata_exception(merge_sha, "committer-email"))
        self.assertFalse(gate.is_legacy_metadata_exception(merge_sha, "author-name"))
        self.assertFalse(gate.is_legacy_metadata_exception(merge_sha, "author-email"))
        self.assertFalse(gate.is_legacy_metadata_exception("c" * 40, "committer-name"))

    def test_pr201_rebase_committer_exception_is_exact_sha_and_name_only(self):
        rebase_sha = "11e7b8302440aa6c4220c7d284f315218c111dd0"
        self.assertTrue(gate.is_legacy_metadata_exception(rebase_sha, "committer-name"))
        self.assertFalse(gate.is_legacy_metadata_exception(rebase_sha, "committer-email"))
        self.assertFalse(gate.is_legacy_metadata_exception(rebase_sha, "author-name"))
        self.assertFalse(gate.is_legacy_metadata_exception(rebase_sha, "author-email"))
        self.assertFalse(gate.is_legacy_metadata_exception("d" * 40, "committer-name"))

    def test_pr303_rebase_committer_exception_is_exact_sha_and_name_only(self):
        rebase_sha = "1c259af1db1153e5bd77ccf35fd6c255fa2c9488"
        self.assertTrue(gate.is_legacy_metadata_exception(rebase_sha, "committer-name"))
        self.assertFalse(gate.is_legacy_metadata_exception(rebase_sha, "committer-email"))
        self.assertFalse(gate.is_legacy_metadata_exception(rebase_sha, "author-name"))
        self.assertFalse(gate.is_legacy_metadata_exception(rebase_sha, "author-email"))
        self.assertFalse(gate.is_legacy_metadata_exception("e" * 40, "committer-name"))

    def test_pr310_rebase_committer_exception_is_exact_sha_and_name_only(self):
        rebase_sha = "2dceea6141e2f542b0c7c6bd8a0ab0535fd289b1"
        self.assertTrue(gate.is_legacy_metadata_exception(rebase_sha, "committer-name"))
        self.assertFalse(gate.is_legacy_metadata_exception(rebase_sha, "committer-email"))
        self.assertFalse(gate.is_legacy_metadata_exception(rebase_sha, "author-name"))
        self.assertFalse(gate.is_legacy_metadata_exception(rebase_sha, "author-email"))
        self.assertFalse(gate.is_legacy_metadata_exception("f" * 40, "committer-name"))

    def test_pr329_rebase_committer_exception_is_exact_sha_and_name_only(self):
        rebase_sha = "fb7de533ededc62fc6744a4c90f2d3cc314d5728"
        self.assertTrue(gate.is_legacy_metadata_exception(rebase_sha, "committer-name"))
        self.assertFalse(gate.is_legacy_metadata_exception(rebase_sha, "committer-email"))
        self.assertFalse(gate.is_legacy_metadata_exception(rebase_sha, "author-name"))
        self.assertFalse(gate.is_legacy_metadata_exception(rebase_sha, "author-email"))
        self.assertFalse(gate.is_legacy_metadata_exception("9" * 40, "committer-name"))

    def test_pr333_rebase_committer_exception_is_exact_sha_and_name_only(self):
        rebase_sha = "552113dae9099835f61b4a44475d858da240146a"
        self.assertTrue(gate.is_legacy_metadata_exception(rebase_sha, "committer-name"))
        self.assertFalse(gate.is_legacy_metadata_exception(rebase_sha, "committer-email"))
        self.assertFalse(gate.is_legacy_metadata_exception(rebase_sha, "author-name"))
        self.assertFalse(gate.is_legacy_metadata_exception(rebase_sha, "author-email"))
        self.assertFalse(gate.is_legacy_metadata_exception("8" * 40, "committer-name"))

    def test_r17_public_ref_residue_exceptions_are_exact_sha_and_name_fields_only(self):
        for commit_sha in (
            "3fa70aa3446acf36f678e42bf348399b563e8370",
            "bedb3089919a623b2ebc21dc4b1c8cbf8810fa92",
            "0e332a336a65c8602808feb23ef91f9a6ffb11ce",
            "a82290c0ac4c2f193bcdf483e18ab57da97a1666",
        ):
            self.assertTrue(gate.is_legacy_metadata_exception(commit_sha, "author-name"))
            self.assertTrue(gate.is_legacy_metadata_exception(commit_sha, "committer-name"))
            self.assertFalse(gate.is_legacy_metadata_exception(commit_sha, "author-email"))
            self.assertFalse(gate.is_legacy_metadata_exception(commit_sha, "committer-email"))
        self.assertFalse(gate.is_legacy_metadata_exception("7" * 40, "author-name"))

    def test_legacy_metadata_exception_does_not_generalize(self):
        legacy = "7734270af5e1928215838fb0f0aee940599d43e4"
        private_email = "private.committer" + "@" + "example.test"

        def fake_check_output(args, **kwargs):
            if args[:2] == ["git", "rev-list"]:
                return legacy + "\n"
            if args[:3] == ["git", "show", "-s"]:
                return (
                    "Sebastián\x00"
                    "293577326+fscfede-beep@users.noreply.github.com\x00"
                    "Private Committer\x00"
                    + private_email
                )
            raise AssertionError(args)

        deny = {gate.sha("Private Committer"), gate.sha(private_email)}
        with mock.patch.object(gate.subprocess, "check_output", side_effect=fake_check_output):
            self.assertEqual(gate.commit_metadata_violations(legacy, deny), [])

        other = "a" * 40

        def fake_other(args, **kwargs):
            if args[:2] == ["git", "rev-list"]:
                return other + "\n"
            if args[:3] == ["git", "show", "-s"]:
                return (
                    "Sebastián\x00"
                    "293577326+fscfede-beep@users.noreply.github.com\x00"
                    "Private Committer\x00"
                    + private_email
                )
            raise AssertionError(args)

        with mock.patch.object(gate.subprocess, "check_output", side_effect=fake_other):
            violations = gate.commit_metadata_violations(other, deny)
        self.assertIn(f"git:commit:{other}:committer-name", violations)
        self.assertIn(f"git:commit:{other}:committer-email", violations)

    def test_full_ancestry_metadata_scan_passes_current_clean_history(self):
        self.assertEqual(gate.commit_metadata_violations("HEAD", set()), [])

    def test_metadata_scan_refs_include_selected_ref_and_all_public_refs(self):
        env = {
            "RUMBO_PRIVACY_COMMIT_SHA": "abc123",
            "RUMBO_PRIVACY_SCAN_ALL_REFS": "1",
        }
        with mock.patch.dict(gate.os.environ, env, clear=True):
            self.assertEqual(gate.metadata_scan_refs(), ["abc123", "--all"])

    def test_metadata_scan_refs_default_to_selected_ref_only(self):
        with mock.patch.dict(gate.os.environ, {"RUMBO_PRIVACY_COMMIT_SHA": "abc123"}, clear=True):
            self.assertEqual(gate.metadata_scan_refs(), ["abc123"])

    def test_ci_enables_repository_wide_metadata_scan(self):
        workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/privacy-gate.yml").read_text(encoding="utf-8")
        self.assertIn("RUMBO_PRIVACY_SCAN_ALL_REFS", workflow)

    def test_public_founder_display_is_first_name_only(self):
        self.assertEqual(gate.PUBLIC_NAME, "Sebasti\u00e1n")

    def test_direct_person_profile_link_is_rejected(self):
        link = "https://www.linkedin.com" + "/in/example"
        self.assertTrue(gate.text_has_direct_person_profile(link))

    def test_rel_me_identity_link_is_rejected(self):
        marker = "rel=" + chr(34) + "me" + chr(34)
        self.assertTrue(gate.text_has_direct_person_profile("<link " + marker + " href=https://example.test/profile>"))

    def test_denied_value_line_numbers_do_not_expose_value(self):
        value = "synthetic private marker"
        deny = {gate.sha(value)}
        text = "safe line\nsynthetic private marker\nother line\n"
        self.assertEqual(gate.denied_value_line_numbers(text, deny), [2])
    def test_word_ngram_deny_behavior_is_preserved(self):
        deny = {gate.sha("private surname")}
        self.assertTrue(gate.text_has_denied_value("hello private surname world", deny))


    def test_openai_landing_founder_uses_public_name(self):
        text = (Path(__file__).resolve().parents[1] / "apps/landing-publica/index-en-openai.html").read_text(encoding="utf-8")
        match = gate.re.search(r"RUMBO IA is developed by\s+([^<\r\n]+)", text)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).strip(), gate.PUBLIC_NAME)


if __name__ == "__main__":
    unittest.main()

