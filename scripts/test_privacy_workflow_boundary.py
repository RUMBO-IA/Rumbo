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

    # Conservative structural regression: cover changes outside the named step.
    # This is not a full YAML parser or independent private policy enforcement.
    effective = "\n".join(
        line for line in workflow.splitlines()
        if not line.lstrip().startswith("#")
    )
    event_section = re.search(
        r"(?ms)^on:[ \t]*\n(.*?)(?=^[a-zA-Z_][\w-]*:|\Z)", effective
    )
    events = set(re.findall(r"(?m)^  ([a-zA-Z_][\w-]*):",
                            event_section.group(1))) if event_section else set()
    if events != {"pull_request", "push"}:
        errors.append("UNEXPECTED_WORKFLOW_TRIGGER")
    job_section = re.search(
        r"(?ms)^jobs:[ \t]*\n(.*?)(?=^[a-zA-Z_][\w-]*:|\Z)", effective
    )
    jobs = set(re.findall(r"(?m)^  ([a-zA-Z_][\w-]*):",
                          job_section.group(1))) if job_section else set()
    if jobs != {"privacy"}:
        errors.append("UNEXPECTED_JOB_SET")
    if len(re.findall(r"(?m)^\s*permissions:[ \t]*$", effective)) != 1:
        errors.append("UNEXPECTED_PERMISSIONS")
    if re.search(r"(?m)^ {4,}permissions:[ \t]*$", effective):
        errors.append("UNEXPECTED_PERMISSIONS")
    references = [
        line for line in effective.splitlines()
        if re.search(r"secrets\s*(?:\.|\[)", line, re.IGNORECASE)
    ]
    if len(references) != 1 or not re.fullmatch(
        r" {10}RUMBO_PRIVACY_DENY_HASHES:\s*[$][{][{]\s*"
        r"secrets[.]RUMBO_PRIVACY_DENY_HASHES\s*[}][}]", references[0]
    ):
        errors.append("UNEXPECTED_SECRET_REFERENCE")
    if match:
        actual_ifs = [
            line.strip() for line in step.splitlines()
            if re.match(r"^\s+if\s*:", line)
        ]
        expected = "if: " + "$" + "{{ " + guard + " }}"
        if actual_ifs != [expected] and "MISSING_MAIN_PUSH_GUARD" not in errors:
            errors.append("MISSING_MAIN_PUSH_GUARD")

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



    def test_reject_guard_only_in_comment(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        line = next(line for line in source.splitlines()
                    if line.lstrip().startswith("if:") and "github.event_name" in line)
        changed = source.replace(line, "        # " + line.strip() + "\n        if: " + "$" + "{{ always() }}")
        self.assertIn("MISSING_MAIN_PUSH_GUARD", validate(changed))

    def test_reject_extra_privileged_job(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        changed = source + "\n  extra:\n    permissions:\n      contents: write\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo safe\n"
        self.assertIn("UNEXPECTED_JOB_SET", validate(changed))

    def test_reject_new_event(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        changed = source.replace("  push:\n", "  push:\n  workflow_dispatch:\n")
        self.assertIn("UNEXPECTED_WORKFLOW_TRIGGER", validate(changed))

    def test_reject_other_secret(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        changed = source.replace("      - name: Test commercial coherence verifier",
                                 "      - name: Bad step\n        env:\n          S: " + "$" + "{{ secrets.OTHER_SECRET }}\n"
                                 "      - name: Test commercial coherence verifier")
        self.assertIn("UNEXPECTED_SECRET_REFERENCE", validate(changed))

    def test_reject_nested_write_permissions(self):
        source = WORKFLOW.read_text(encoding="utf-8")
        changed = source.replace("    runs-on: ubuntu-latest",
                                 "    permissions:\n      contents: write\n    runs-on: ubuntu-latest")
        self.assertIn("UNEXPECTED_PERMISSIONS", validate(changed))

if __name__ == "__main__":
    unittest.main()
