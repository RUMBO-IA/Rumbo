"""Public PR-safe candidate surface scan; never a trusted private attestation."""
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def execute(args=(), updates=None):
    env=dict(os.environ)
    for key in ("RUMBO_PRIVACY_DENY_HASHES","RUMBO_PRIVACY_SCAN_ALL_REFS","RUMBO_PRIVACY_COMMIT_SHA"):
        env.pop(key,None)
    env.update(updates or {})
    return subprocess.run(
        [sys.executable,"scripts/verify_public_privacy.py",*args],
        cwd=ROOT,env=env,capture_output=True,text=True,timeout=45)

class PublicSafePrivacyTests(unittest.TestCase):
    def test_public_mode_without_private_hashes_performs_real_scan(self):
        p=execute(["--public-only"])
        self.assertEqual(p.returncode,0,p.stdout[-2000:]+p.stderr[-800:])
        self.assertIn("PUBLIC_PRIVACY_INVARIANTS_PASS",p.stdout)

    def test_default_private_mode_fails_closed_without_secret(self):
        p=execute()
        self.assertEqual(p.returncode,2,p.stdout+p.stderr)
        self.assertIn("private deny-hash set is missing",p.stdout)

    def test_public_only_ignores_global_ref_flag(self):
        p=execute(["--public-only"],{"RUMBO_PRIVACY_SCAN_ALL_REFS":"1"})
        self.assertEqual(p.returncode,0,p.stdout[-2000:]+p.stderr[-800:])

    def test_unknown_option_rejected(self):
        self.assertNotEqual(execute(["--public-only","--ignore"]).returncode,0)

    def test_workflow_keeps_secret_main_only_and_runs_public_pr_check(self):
        import yaml
        from scripts.test_privacy_workflow_boundary import validate,UniqueLoader
        y=(ROOT/".github/workflows/privacy-gate.yml").read_text(encoding="utf-8")
        self.assertEqual(validate(y),[])
        steps=yaml.load(y,Loader=UniqueLoader)["jobs"]["privacy"]["steps"]
        s=[x for x in steps if x.get("name")=="Verify public PR privacy invariants (no secrets)"]
        self.assertEqual(len(s),1)
        self.assertEqual(s[0].get("if"),"$"+"{{ github.event_name == 'pull_request' }}")
        self.assertEqual(s[0].get("run"),"python scripts/verify_public_privacy.py --public-only")
        self.assertEqual(s[0].get("env"),
          {"RUMBO_PRIVACY_COMMIT_SHA":"$"+"{{ github.event.pull_request.head.sha }}"})
        self.assertNotIn("secrets.",str(s[0]))

    def test_public_mode_rejects_unapproved_address_without_secrets(self):
        import contextlib
        import io
        import tempfile
        from unittest import mock
        from scripts import verify_public_privacy as gate
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            (root/"README.md").write_text("## Founder\nSebastián\n",encoding="utf-8")
            (root/"index.html").write_text("<footer>Fundador: Sebastián</footer>",encoding="utf-8")
            landing=root/"apps"/"landing-publica"
            landing.mkdir(parents=True)
            (landing/"index-en-openai.html").write_text(
                "RUMBO IA is developed by Sebastián<",encoding="utf-8")
            malicious=root/"public.txt"
            malicious.write_text("Contact: unwanted" + "@" + "example.test",encoding="utf-8")
            output=io.StringIO()
            with (mock.patch.object(gate,"ROOT",root),
                  mock.patch.object(gate,"tracked_files",return_value=[malicious]),
                  mock.patch.object(gate,"commit_metadata_violations",return_value=[]),
                  contextlib.redirect_stdout(output)):
                result=gate.main(public_only=True)
            self.assertEqual(result,1)
            self.assertIn("public.txt:unapproved-email",output.getvalue())


if __name__=="__main__":
    unittest.main()
