"""Static regression for the GitHub Actions secret trust boundary."""
import re
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/privacy-gate.yml"


def validate(workflow: str) -> list[str]:
    errors = []
    if "pull_request_target:" in workflow:
        errors.append("PRIVILEGED_PR_EVENT")
    if "workflow_run:" in workflow:
        errors.append("PRIVILEGED_CHAIN_EVENT")
    if not re.search(r"(?m)^  pull_request:\s*$", workflow):
        errors.append("MISSING_PUBLIC_PR_TRIGGER")
    if workflow.count("secrets.RUMBO_PRIVACY_DENY_HASHES") != 1:
        errors.append("PRIVATE_SECRET_REFERENCE_COUNT")
    match = re.search(
        r"(?ms)^      - name: Verify public privacy invariants \(trusted main only\)\n"
        r"(.*?)(?=^      - name:|^  [a-zA-Z_-]+:|\Z)", workflow
    )
    if not match:
        errors.append("MISSING_TRUSTED_MAIN_STEP")
    else:
        step = match.group(1)
        guard = "github.event_name == 'push' && github.ref == 'refs/heads/main'"
        if guard not in step:
            errors.append("MISSING_MAIN_PUSH_GUARD")
        if "secrets.RUMBO_PRIVACY_DENY_HASHES" not in step:
            errors.append("SECRET_OUTSIDE_MAIN_STEP")
        if "python scripts/verify_public_privacy.py" not in step:
            errors.append("MISSING_PRIVATE_VERIFIER")
    if "permissions:\n  contents: read" not in workflow:
        errors.append("MISSING_READONLY_TOKEN")
    return errors


class PrivacyWorkflowBoundaryTest(unittest.TestCase):
    def test_current_workflow(self):
        self.assertEqual(validate(WORKFLOW.read_text(encoding="utf-8")), [])

    def test_reject_privileged_pr_event(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("PRIVILEGED_PR_EVENT", validate(source + "\n  pull_request_target:\n"))

    def test_reject_secret_outside_trusted_step(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        changed = source.replace("      - name: Test commercial coherence verifier", "      - name: Bad step\n        env:\n          X: ${{ secrets.RUMBO_PRIVACY_DENY_HASHES }}\n      - name: Test commercial coherence verifier")
        self.assertIn("PRIVATE_SECRET_REFERENCE_COUNT", validate(changed))

    def test_reject_main_guard_removal(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        changed = source.replace("github.event_name == 'push' && github.ref == 'refs/heads/main'", "github.event_name == 'push'")
        self.assertIn("MISSING_MAIN_PUSH_GUARD", validate(changed))


if __name__ == "__main__":
    unittest.main()
