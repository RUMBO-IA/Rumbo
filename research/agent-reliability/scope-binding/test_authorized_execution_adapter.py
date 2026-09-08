import unittest

import authorized_execution_adapter as adapter


def workspace_receipt():
    return {
        "scope_authority": {"scope_id":"p","source":"owner","resolved_cwd":"/work/p","resolved_workspace_roots":["/work/p"],"required_writable_roots":[]},
        "selected_scope_id":"p","session_meta_cwd":"/work/p","first_turn_cwd":"/work/p","workspace_roots":["/work/p"],"writable_roots":[]
    }


def authority():
    return {"surfaces":{"browser":{"capabilities":["navigate"],"effects":["read"]}}}


class AdapterTests(unittest.TestCase):
    def test_safe_stop_prevents_effect(self):
        calls=[]
        out=adapter.execute_authorized(workspace_receipt(), authority(), {"surface":"browser","capability":"navigate","effect":"write"}, lambda: calls.append("ran"))
        self.assertEqual("SAFE_STOP", out["state"])
        self.assertEqual([], calls)

    def test_authorized_effect_runs_once(self):
        calls=[]
        out=adapter.execute_authorized(workspace_receipt(), authority(), {"surface":"browser","capability":"navigate","effect":"read"}, lambda: calls.append("ran") or {"ok":True})
        self.assertEqual("EXECUTED", out["state"])
        self.assertEqual(["ran"], calls)
        self.assertEqual({"ok":True}, out["result"])

    def test_observed_surface_cannot_grant_authority(self):
        calls=[]
        req={"surface":"browser","capability":"navigate","effect":"read","observed_surfaces":["browser"]}
        out=adapter.execute_authorized(workspace_receipt(), {}, req, lambda: calls.append("ran"))
        self.assertEqual("SAFE_STOP", out["state"])
        self.assertEqual([], calls)

    def test_effect_exception_is_not_reported_as_success(self):
        def boom():
            raise RuntimeError("boom")
        out=adapter.execute_authorized(workspace_receipt(), authority(), {"surface":"browser","capability":"navigate","effect":"read"}, boom)
        self.assertEqual("EFFECT_FAILED", out["state"])
        self.assertIn("RuntimeError", out["error_type"])


if __name__ == "__main__":
    unittest.main()
