import importlib.util
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import requests

MODULE_PATH = Path(__file__).with_name("google_workspace_mcp.py")
spec = importlib.util.spec_from_file_location("google_workspace_mcp_test", MODULE_PATH)
mcpmod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["google_workspace_mcp_test"] = mcpmod
spec.loader.exec_module(mcpmod)


class FakeResponse:
    def __init__(self, status_code=200, data=None, text=""):
        self.status_code = status_code
        self._data = data or {}
        self.text = text

    def json(self):
        return self._data


class GoogleWorkspaceMcpTests(unittest.TestCase):
    def setUp(self):
        self.old_token = os.environ.get("GOOGLE_OAUTH_ACCESS_TOKEN")
        self.old_writes = os.environ.get("RUMBO_ALLOW_WRITES")
        os.environ["GOOGLE_OAUTH_ACCESS_TOKEN"] = "test-token"
        os.environ["RUMBO_ALLOW_WRITES"] = "1"

    def tearDown(self):
        if self.old_token is None:
            os.environ.pop("GOOGLE_OAUTH_ACCESS_TOKEN", None)
        else:
            os.environ["GOOGLE_OAUTH_ACCESS_TOKEN"] = self.old_token
        if self.old_writes is None:
            os.environ.pop("RUMBO_ALLOW_WRITES", None)
        else:
            os.environ["RUMBO_ALLOW_WRITES"] = self.old_writes

    def test_missing_oauth_token_fails_closed(self):
        os.environ.pop("GOOGLE_OAUTH_ACCESS_TOKEN", None)
        with self.assertRaisesRegex(RuntimeError, "GOOGLE_OAUTH_ACCESS_TOKEN_REQUIRED"):
            mcpmod._headers()

    def test_writes_disabled_fails_closed(self):
        os.environ.pop("RUMBO_ALLOW_WRITES", None)
        with self.assertRaisesRegex(PermissionError, "RUMBO_ALLOW_WRITES_NOT_ENABLED"):
            mcpmod.gmail_create_draft("self", "subject", "body", "key")

    def test_gmail_timeout_after_commit_recovers_by_readback_without_retry(self):
        calls = []
        def fake(method, url, **kwargs):
            calls.append((method, url))
            if len(calls) == 1:
                return FakeResponse(data={"messages": []})
            if len(calls) == 2:
                raise requests.Timeout("lost response")
            if len(calls) == 3:
                return FakeResponse(data={"messages": [{"id": "msg1"}]})
            if len(calls) == 4:
                return FakeResponse(data={"id": "msg1", "threadId": "thr1", "labelIds": ["DRAFT"]})
            raise AssertionError(calls)

        with patch.object(mcpmod, "_request", side_effect=fake):
            result = mcpmod.gmail_create_draft("self", "subject", "body", "stable-key")

        self.assertEqual(sum(1 for method, _ in calls if method == "POST"), 1)
        self.assertFalse(result["tool_success"])
        self.assertTrue(result["effect_verified"])
        self.assertTrue(result["recovered_existing"])
        self.assertEqual(result["message_id"], "msg1")
        self.assertIn("DRAFT", result["labels"])

    def test_calendar_timeout_after_commit_recovers_by_readback_without_retry(self):
        calls = []
        event = {"id": mcpmod._calendar_event_id("stable-key"), "status": "confirmed"}

        def fake(method, url, **kwargs):
            calls.append((method, url))
            if len(calls) == 1:
                return FakeResponse(status_code=404)
            if len(calls) == 2:
                raise requests.Timeout("lost response")
            if len(calls) == 3:
                return FakeResponse(data=event)
            raise AssertionError(calls)

        with patch.object(mcpmod, "_request", side_effect=fake):
            result = mcpmod.calendar_create_event(
                "Lunch",
                "2026-10-02T12:00:00-03:00",
                "2026-10-02T13:00:00-03:00",
                [],
                "stable-key",
            )

        self.assertEqual(sum(1 for method, _ in calls if method == "POST"), 1)
        self.assertFalse(result["tool_success"])
        self.assertTrue(result["effect_verified"])
        self.assertTrue(result["recovered_existing"])
        self.assertEqual(result["event_id"], event["id"])

    def test_calendar_success_without_readback_does_not_claim_verification(self):
        calls = []

        def fake(method, url, **kwargs):
            calls.append((method, url))
            if len(calls) == 1:
                return FakeResponse(status_code=404)
            if len(calls) == 2:
                return FakeResponse(data={"id": "accepted"})
            if len(calls) == 3:
                return FakeResponse(status_code=404)
            raise AssertionError(calls)

        with patch.object(mcpmod, "_request", side_effect=fake):
            result = mcpmod.calendar_create_event(
                "Lunch",
                "2026-10-02T12:00:00-03:00",
                "2026-10-02T13:00:00-03:00",
                [],
                "stable-key",
            )

        self.assertEqual(sum(1 for method, _ in calls if method == "POST"), 1)
        self.assertTrue(result["tool_success"])
        self.assertFalse(result["effect_verified"])
        self.assertFalse(result["recovered_existing"])

    def test_deterministic_provider_ids(self):
        self.assertEqual(mcpmod._draft_message_id("same"), mcpmod._draft_message_id("same"))
        self.assertEqual(mcpmod._calendar_event_id("same"), mcpmod._calendar_event_id("same"))
        self.assertNotEqual(mcpmod._calendar_event_id("same"), mcpmod._calendar_event_id("different"))


if __name__ == "__main__":
    unittest.main()
