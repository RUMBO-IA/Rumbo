import importlib.util
from pathlib import Path
import sys
import unittest

from agents import RunConfig, Runner
from agents.testing import ScriptedModel, assistant_message, function_call

MODULE_PATH = Path(__file__).with_name("daily_ops.py")
spec = importlib.util.spec_from_file_location("daily_ops_sdk", MODULE_PATH)
daily_ops = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["daily_ops_sdk"] = daily_ops
spec.loader.exec_module(daily_ops)


def agent_with(model):
    daily_ops.os.environ["OPENAI_MODEL"] = "gpt-5-mini"
    agent = daily_ops.build_agent()
    agent.model = model
    return agent


class DailyOpsSdkIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.backend = daily_ops.MockBackend()
        daily_ops.configure_backend(self.backend)

    async def test_read_tool_executes_without_approval(self):
        model = ScriptedModel([
            [function_call("get_calendar_events", {
                "start": "2026-10-02T00:00:00-03:00",
                "end": "2026-10-03T00:00:00-03:00",
            }, call_id="call_read")],
            [assistant_message("Daily brief ready.")],
        ])
        agent = agent_with(model)
        result = await Runner.run(
            agent,
            "Give me the daily brief. Read only.",
            run_config=RunConfig(tracing_disabled=True),
        )
        self.assertEqual(result.final_output, "Daily brief ready.")
        self.assertEqual(result.interruptions, [])
        self.assertEqual(len(self.backend.drafts), 0)
        self.assertEqual(len(self.backend.created_events), 0)
        self.assertEqual(len(model.calls), 2)
        model.assert_complete()

    async def test_write_pauses_until_explicit_approval(self):
        model = ScriptedModel([
            [function_call("create_email_draft", {
                "to": "client@example.com",
                "subject": "Follow-up",
                "body": "Thanks for the call.",
            }, call_id="call_write")],
            [assistant_message("Draft created.")],
        ])
        agent = agent_with(model)
        result = await Runner.run(
            agent,
            "Create that draft.",
            run_config=RunConfig(tracing_disabled=True),
        )
        self.assertEqual(len(result.interruptions), 1)
        self.assertEqual(len(self.backend.drafts), 0)
        state = result.to_state()
        state.approve(result.interruptions[0])
        resumed = await Runner.run(
            agent,
            state,
            run_config=RunConfig(tracing_disabled=True),
        )
        self.assertEqual(resumed.final_output, "Draft created.")
        self.assertEqual(len(self.backend.drafts), 1)
        self.assertEqual(len(model.calls), 2)
        model.assert_complete()


if __name__ == "__main__":
    unittest.main()
