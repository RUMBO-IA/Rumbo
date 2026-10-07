import importlib.util
import json
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ANCHOR = ROOT / "docs" / "control-authority-anchor-v1.json"
VERIFIER = ROOT / "scripts" / "verify_control_authority_anchor.py"
TRUST_ROOT_WORKFLOW = ROOT / ".github" / "workflows" / "qug-protected-trust-root-r1.yml"

spec = importlib.util.spec_from_file_location("verify_control_authority_anchor", VERIFIER)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class ControlAuthorityAnchorTests(unittest.TestCase):
    def load(self):
        return json.loads(ANCHOR.read_text(encoding="utf-8"))

    def test_current_anchor_static_contract(self):
        data = self.load()
        guard.validate_static(data)
        self.assertEqual(
            "dac4b6538481f6cfede0bd989d2ab886a65629f9",
            data["subject"]["authorized_main_sha"],
        )
        self.assertEqual(
            "228ff1198e176e097c40902080d800fd5d64a519",
            data["subject"]["authorized_tree_sha"],
        )

    def test_invalid_authorized_commit_fails_closed(self):
        data = self.load()
        data["subject"]["authorized_main_sha"] = "not-a-sha"
        with self.assertRaisesRegex(guard.AnchorError, "authorized_main_sha"):
            guard.validate_static(data)

    def test_invalid_authorized_tree_fails_closed(self):
        data = self.load()
        data["subject"]["authorized_tree_sha"] = "bad-tree"
        with self.assertRaisesRegex(guard.AnchorError, "authorized_tree_sha"):
            guard.validate_static(data)

    def test_source_tree_mismatch_fails_online(self):
        data = self.load()
        original = guard.gh_json
        def fake(endpoint):
            if endpoint.endswith("/git/commits/" + data["subject"]["authorized_main_sha"]):
                return {"tree": {"sha": "0" * 40}}
            raise AssertionError(endpoint)
        guard.gh_json = fake
        try:
            with self.assertRaisesRegex(guard.AnchorError, "authorized_tree_sha mismatch"):
                guard.validate_online(data)
        finally:
            guard.gh_json = original

    def test_private_main_drift_does_not_change_canon(self):
        data = self.load()
        authorized = data["subject"]["authorized_main_sha"]
        tree = data["subject"]["authorized_tree_sha"]
        original = guard.gh_json

        def fake(endpoint):
            if endpoint.endswith("/git/commits/" + authorized):
                return {"tree": {"sha": tree}}
            if endpoint == "repos/RUMBO-IA/Rumbo/branches/main":
                return {
                    "protected": True,
                    "protection": {
                        "required_status_checks": {
                            "contexts": ["privacy", "Vercel"]
                        }
                    },
                }
            if endpoint == "repos/RUMBO-IA/Rumbo/rulesets/22317339":
                return {
                    "enforcement": "active",
                    "bypass_actors": [],
                    "rules": [{"type": "non_fast_forward"}],
                }
            if endpoint == "repos/RUMBO-IA/rumbo-control-queue/branches/main":
                return {"commit": {"sha": "f" * 40}, "protected": False}
            raise AssertionError(endpoint)

        guard.gh_json = fake
        try:
            observed = guard.validate_online(data)
        finally:
            guard.gh_json = original

        self.assertFalse(observed["source_branch_matches_anchor"])
        self.assertEqual(authorized, observed["canonical_source_commit"])
        self.assertEqual(tree, observed["canonical_source_tree"])

    def test_unprotected_public_authority_fails(self):
        data = self.load()
        authorized = data["subject"]["authorized_main_sha"]
        tree = data["subject"]["authorized_tree_sha"]
        original = guard.gh_json
        def fake(endpoint):
            if endpoint.endswith("/git/commits/" + authorized):
                return {"tree": {"sha": tree}}
            if endpoint == "repos/RUMBO-IA/Rumbo/branches/main":
                return {"protected": False}
            raise AssertionError(endpoint)
        guard.gh_json = fake
        try:
            with self.assertRaisesRegex(guard.AnchorError, "public authority protected=false"):
                guard.validate_online(data)
        finally:
            guard.gh_json = original

    def test_missing_required_check_fails(self):
        data = self.load()
        authorized = data["subject"]["authorized_main_sha"]
        tree = data["subject"]["authorized_tree_sha"]
        original = guard.gh_json
        def fake(endpoint):
            if endpoint.endswith("/git/commits/" + authorized):
                return {"tree": {"sha": tree}}
            if endpoint == "repos/RUMBO-IA/Rumbo/branches/main":
                return {
                    "protected": True,
                    "protection": {
                        "required_status_checks": {"contexts": ["privacy"]}
                    },
                }
            raise AssertionError(endpoint)
        guard.gh_json = fake
        try:
            with self.assertRaisesRegex(guard.AnchorError, "missing required checks:Vercel"):
                guard.validate_online(data)
        finally:
            guard.gh_json = original

    def test_ruleset_bypass_fails(self):
        data = self.load()
        authorized = data["subject"]["authorized_main_sha"]
        tree = data["subject"]["authorized_tree_sha"]
        original = guard.gh_json
        def fake(endpoint):
            if endpoint.endswith("/git/commits/" + authorized):
                return {"tree": {"sha": tree}}
            if endpoint == "repos/RUMBO-IA/Rumbo/branches/main":
                return {
                    "protected": True,
                    "protection": {
                        "required_status_checks": {
                            "contexts": ["privacy", "Vercel"]
                        }
                    },
                }
            if endpoint == "repos/RUMBO-IA/Rumbo/rulesets/22317339":
                return {
                    "enforcement": "active",
                    "bypass_actors": [{"actor_id": 1}],
                    "rules": [{"type": "non_fast_forward"}],
                }
            raise AssertionError(endpoint)
        guard.gh_json = fake
        try:
            with self.assertRaisesRegex(guard.AnchorError, "bypass_actors"):
                guard.validate_online(data)
        finally:
            guard.gh_json = original

    def trust_root_workflow(self):
        return TRUST_ROOT_WORKFLOW.read_text(encoding="utf-8")

    def test_qug_trust_root_binds_exact_check_producers(self):
        workflow = self.trust_root_workflow()
        self.assertIn("EXPECTED_PRIVACY_WORKFLOW_ID = 347174988", workflow)
        self.assertIn('EXPECTED_PRIVACY_WORKFLOW_PATH = ".github/workflows/privacy-gate.yml"', workflow)
        self.assertIn('EXPECTED_PRIVACY_WORKFLOW_BLOB = "1cb3ed7881961516b54fb5ab663890914440463a"', workflow)
        self.assertIn('EXPECTED_PRIVACY_WORKFLOW_SHA256 = "b2f9e4919268b618e6d601c0e9280df8b376a9dec338e71483d3c4a551795bc6"', workflow)
        self.assertIn("EXPECTED_PRIVACY_APP_ID = 15368", workflow)
        self.assertIn("EXPECTED_VERCEL_APP_ID = 8329", workflow)
        self.assertIn("EXPECTED_VERCEL_CREATOR_ID = 35613825", workflow)
        self.assertIn('EXPECTED_VERCEL_CREATOR_LOGIN = "vercel[bot]"', workflow)

    def test_qug_trust_root_enforces_governing_ruleset(self):
        workflow = self.trust_root_workflow()
        self.assertIn("EXPECTED_RULESET_ID = 22317339", workflow)
        self.assertIn("ruleset enforcement!=active", workflow)
        self.assertIn("ruleset bypass_actors present", workflow)
        self.assertIn("ruleset missing non_fast_forward", workflow)

    def test_qug_trust_root_revalidates_public_head_before_carrier(self):
        workflow = self.trust_root_workflow()
        self.assertIn("Revalidate public authority immediately before carrier", workflow)
        self.assertIn("FAIL_PUBLIC_HEAD_SUPERSEDED_BEFORE_CARRIER", workflow)
        self.assertIn("FAIL_ANCHOR_DRIFT_BEFORE_CARRIER", workflow)

    def test_qug_trust_root_allows_private_main_drift(self):
        workflow = self.trust_root_workflow()
        self.assertNotIn("ls-remote origin refs/heads/main", workflow)
        self.assertIn('fetch "$canonical_remote" main --quiet', workflow)
        self.assertIn('cat-file -e "$CANONICAL_SHA^{commit}"', workflow)

    def test_qug_trust_root_disables_git_replace_objects(self):
        workflow = self.trust_root_workflow()
        self.assertIn("GIT_NO_REPLACE_OBJECTS=1", workflow)
        self.assertIn("refs/replace", workflow)
        self.assertIn("FAIL_PRIVATE_REPLACE_REFS_PRESENT", workflow)


    def test_qug_trust_root_precarrier_revalidates_full_ruleset(self):
        workflow = self.trust_root_workflow()
        marker = "Revalidate public authority immediately before carrier"
        self.assertIn(marker, workflow)
        pre_carrier = workflow[workflow.index(marker):]
        self.assertIn('EXPECTED_RULESET_UPDATED_AT = "2026-10-01T00:55:26.160-03:00"', pre_carrier)
        self.assertIn("FAIL_RULESET_UPDATED_AT_DRIFT_BEFORE_CARRIER", pre_carrier)
        self.assertIn('if "~ALL" not in includes:', pre_carrier)
        self.assertIn("FAIL_RULESET_SCOPE_BEFORE_CARRIER", pre_carrier)


    def test_qug_trust_root_rejects_dangerous_local_git_config_and_neutralizes_hooks(self):
        workflow = self.trust_root_workflow()
        self.assertIn("config --local --no-includes --name-only --list", workflow)
        self.assertIn("FAIL_PRIVATE_DANGEROUS_GIT_CONFIG", workflow)
        self.assertIn('hooks="$RUNNER_TEMP/rumbo-public-trust-root-empty-hooks-', workflow)
        self.assertIn('git -c core.hooksPath="$hooks" -C "$repo" worktree add', workflow)
        self.assertIn('git -c core.hooksPath="$hooks" -C "$repo" worktree remove', workflow)




    def test_qug_trust_root_precarrier_revalidates_exact_required_results(self):
        workflow = self.trust_root_workflow()
        marker = "Revalidate public authority immediately before carrier"
        self.assertIn(marker, workflow)
        pre_carrier = workflow[workflow.index(marker):]
        self.assertIn("EXPECTED_PRIVACY_WORKFLOW_ID = 347174988", pre_carrier)
        self.assertIn('EXPECTED_PRIVACY_WORKFLOW_PATH = ".github/workflows/privacy-gate.yml"', pre_carrier)
        self.assertIn("FAIL_PRIVACY_WORKFLOW_PRE_CARRIER", pre_carrier)
        self.assertIn("FAIL_PRIVACY_CHECK_PRE_CARRIER", pre_carrier)
        self.assertIn("FAIL_VERCEL_STATUS_PRE_CARRIER", pre_carrier)
        self.assertIn("FAIL_PRIVACY_REQUIRED_APP_PRE_CARRIER", pre_carrier)
        self.assertIn("FAIL_VERCEL_REQUIRED_APP_PRE_CARRIER", pre_carrier)

    def test_qug_trust_root_serializes_persistent_effect_without_cancellation(self):
        workflow = self.trust_root_workflow()
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertNotIn("cancel-in-progress: true", workflow)



    def test_persistent_qug_carrier_is_inert_until_runner_group_policy_is_proven(self):
        text = (ROOT / ".github" / "workflows" / "qug-protected-trust-root-r1.yml").read_text(encoding="utf-8")
        self.assertIn("apply-desktop-authority:", text)
        self.assertIn("if: ${{ false }}", text)
        self.assertIn("DISABLED_PENDING_RUNNER_POLICY", text)
        self.assertIn("runs-on: [self-hosted, Linux, X64, rumbo-ci-linux]", text)


    def test_ruleset_ref_exclusions_fail_closed_in_both_authority_stages(self):
        workflow = self.trust_root_workflow()
        self.assertGreaterEqual(workflow.count('excludes=set(ref_name.get("exclude") or [])'), 2)
        self.assertIn("FAIL_RULESET_EXCLUSIONS_PRESENT", workflow)
        self.assertIn("FAIL_RULESET_EXCLUSIONS_BEFORE_CARRIER", workflow)

    def test_ruleset_snapshot_normalizes_timestamp_and_rejects_exposed_drift(self):
        workflow = self.trust_root_workflow()
        stamp = 'EXPECTED_RULESET_UPDATED_AT = "2026-10-01T00:55:26.160-03:00"'
        node = 'EXPECTED_RULESET_NODE_ID = "RRS_lACqUmVwb3NpdG9yec5Qpw2wzgFUiRs"'
        self.assertGreaterEqual(workflow.count(stamp), 2)
        self.assertGreaterEqual(workflow.count(node), 2)
        self.assertGreaterEqual(workflow.count('if "updated_at" in ruleset:'), 2)
        self.assertGreaterEqual(workflow.count('if "node_id" in ruleset and'), 2)
        self.assertGreaterEqual(workflow.count("parse_ruleset_time"), 4)
        self.assertIn("FAIL_RULESET_UPDATED_AT_DRIFT", workflow)
        self.assertIn("FAIL_RULESET_NODE_ID_DRIFT", workflow)
        self.assertIn("FAIL_RULESET_UPDATED_AT_DRIFT_BEFORE_CARRIER", workflow)
        self.assertIn("FAIL_RULESET_NODE_ID_DRIFT_BEFORE_CARRIER", workflow)
        self.assertGreaterEqual(workflow.count('if "bypass_actors" in ruleset and ruleset.get("bypass_actors"):'), 2)
        self.assertNotIn('if "bypass_actors" not in ruleset:', workflow)
        self.assertGreaterEqual(workflow.count('if "current_user_can_bypass" in ruleset and ruleset.get("current_user_can_bypass") != "never":'), 2)

    def test_private_fetch_uses_exact_https_origin_and_protocol_lockdown(self):
        workflow = self.trust_root_workflow()
        marker = "Verify anchored private commit and tree before execution"
        self.assertIn(marker, workflow)
        verify = workflow[workflow.index(marker):workflow.index("Execute exact anchored carrier through Windows interop")]
        self.assertIn('canonical_remote="https://github.com/RUMBO-IA/rumbo-control-queue.git"', verify)
        self.assertIn('origin_url="$(git -C "$repo" config --local --no-includes --get remote.origin.url || true)"', verify)
        self.assertIn("FAIL_PRIVATE_ORIGIN_URL", verify)
        self.assertIn("GIT_CONFIG_NOSYSTEM=1", verify)
        self.assertIn("GIT_CONFIG_GLOBAL=/dev/null", verify)
        self.assertIn('protocol\\..*\\.allow', verify)
        self.assertIn("-c protocol.allow=never", verify)
        self.assertIn("-c protocol.https.allow=always", verify)
        self.assertIn("-c protocol.ext.allow=never", verify)
        self.assertIn("-c protocol.file.allow=never", verify)
        self.assertIn('fetch "$canonical_remote" main --quiet', verify)
        self.assertNotIn("fetch origin main --quiet", verify)

    def test_private_verification_shell_block_is_structurally_complete(self):
        workflow = self.trust_root_workflow()
        marker = "Verify anchored private commit and tree before execution"
        verify = workflow[workflow.index(marker):workflow.index("Execute exact anchored carrier through Windows interop")]
        self.assertIn("|| true)\"", verify)
        self.assertEqual(verify.count('dangerous="$(git -C "$repo" config'), 1)
        self.assertEqual(verify.count("FAIL_PRIVATE_DANGEROUS_GIT_CONFIG"), 1)
        self.assertNotIn("Execute exact anchored carrier", verify)


    def test_r13_vercel_status_uses_creator_avatar(self):
        workflow = self.trust_root_workflow()
        self.assertGreaterEqual(workflow.count('(s.get("creator") or {}).get("avatar_url")'), 2)
        self.assertNotIn('s.get("avatar_url") or ""', workflow)
        self.assertNotIn('or s.get("avatar_url")', workflow)

    def test_r13_ruleset_target_is_branch_in_both_authority_stages(self):
        workflow = self.trust_root_workflow()
        self.assertGreaterEqual(workflow.count('ruleset.get("target") != "branch"'), 2)
        self.assertIn("FAIL_RULESET_TARGET_NOT_BRANCH", workflow)
        self.assertIn("FAIL_RULESET_TARGET_NOT_BRANCH_BEFORE_CARRIER", workflow)

    def test_r13_rejects_real_git_include_key_forms(self):
        workflow = self.trust_root_workflow()
        self.assertGreaterEqual(workflow.count(r'include\.path|includeif\..*\.path'), 2)

    def test_r13_materialization_reestablishes_git_config_isolation_and_local_readback(self):
        workflow = self.trust_root_workflow()
        marker = "Execute exact anchored carrier through Windows interop"
        self.assertIn(marker, workflow)
        materialize = workflow[workflow.index(marker):]
        self.assertIn("GIT_CONFIG_NOSYSTEM=1", materialize)
        self.assertIn("GIT_CONFIG_GLOBAL=/dev/null", materialize)
        self.assertIn('canonical_remote="https://github.com/RUMBO-IA/rumbo-control-queue.git"', materialize)
        self.assertIn("FAIL_PRIVATE_ORIGIN_URL_BEFORE_MATERIALIZATION", materialize)
        self.assertIn("FAIL_PRIVATE_DANGEROUS_GIT_CONFIG_BEFORE_MATERIALIZATION", materialize)
        self.assertIn(r'include\.path|includeif\..*\.path', materialize)
        self.assertIn('worktree add --detach "$wt" "$CANONICAL_SHA"', materialize)

if __name__ == "__main__":
    unittest.main()
