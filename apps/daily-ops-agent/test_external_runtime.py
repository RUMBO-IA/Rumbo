import importlib.util
import os
from pathlib import Path
import sys
import unittest

from agents import Agent, RunConfig, Runner
from agents.testing import ScriptedModel, assistant_message, function_call

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

MODULE_PATH = HERE / "external_runtime.py"
spec = importlib.util.spec_from_file_location("external_runtime_test", MODULE_PATH)
runtime = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["external_runtime_test"] = runtime
spec.loader.exec_module(runtime)


class ExternalRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_server_discovers_expected_tools_without_provider_credentials(self):
        old_google = os.environ.pop("GOOGLE_OAUTH_ACCESS_TOKEN", None)
        old_write = os.environ.pop("RUMBO_ALLOW_WRITES", None)
        try:
            tools = await runtime.discover_tools()
        finally:
            if old_google is not None:
                os.environ["GOOGLE_OAUTH_ACCESS_TOKEN"] = old_google
            if old_write is not None:
                os.environ["RUMBO_ALLOW_WRITES"] = old_write

        self.assertEqual(
            tools,
            [
                "calendar_create_event",
                "calendar_events",
                "gmail_create_draft",
                "gmail_read",
                "gmail_search",
            ],
        )

    async def test_mcp_read_executes_through_stdio_subprocess(self):
        old_test = os.environ.get("RUMBO_MCP_TEST_MODE")
        os.environ["RUMBO_MCP_TEST_MODE"] = "1"
        server = runtime.build_google_mcp_server()
        await server.connect()
        try:
            model = ScriptedModel([
                [function_call(
                    "gmail_search",
                    {"query": "newer_than:1d", "max_results": 5},
                    call_id="call_mcp_read",
                )],
                [assistant_message("Read path complete.")],
            ])
            agent = Agent(
                name="External MCP read test",
                instructions="Test read boundary.",
                model=model,
                mcp_servers=[server],
            )
            result = await Runner.run(
                agent,
                "Check recent mail.",
                run_config=RunConfig(tracing_disabled=True),
            )
            self.assertEqual(result.final_output, "Read path complete.")
            self.assertEqual(result.interruptions, [])
            self.assertEqual(len(model.calls), 2)
        finally:
            await server.cleanup()
            if old_test is None:
                os.environ.pop("RUMBO_MCP_TEST_MODE", None)
            else:
                os.environ["RUMBO_MCP_TEST_MODE"] = old_test

    async def test_mcp_write_interrupts_before_provider_execution(self):
        old_google = os.environ.pop("GOOGLE_OAUTH_ACCESS_TOKEN", None)
        old_write = os.environ.pop("RUMBO_ALLOW_WRITES", None)
        server = runtime.build_google_mcp_server()
        await server.connect()
        try:
            model = ScriptedModel([
                [function_call(
                    "gmail_create_draft",
                    {
                        "to": "self",
                        "subject": "Test",
                        "body": "Do not send",
                        "idempotency_key": "sdk-mcp-approval-test",
                    },
                    call_id="call_mcp_write",
                )],
                [assistant_message("Rejected write acknowledged.")],
            ])
            agent = Agent(
                name="External MCP approval test",
                instructions="Test approval boundary.",
                model=model,
                mcp_servers=[server],
            )
            result = await Runner.run(
                agent,
                "Create a draft.",
                run_config=RunConfig(tracing_disabled=True),
            )
            self.assertEqual(len(result.interruptions), 1)
            self.assertEqual(result.interruptions[0].tool_name, "gmail_create_draft")
            self.assertEqual(len(model.calls), 1)
        finally:
            await server.cleanup()
            if old_google is not None:
                os.environ["GOOGLE_OAUTH_ACCESS_TOKEN"] = old_google
            if old_write is not None:
                os.environ["RUMBO_ALLOW_WRITES"] = old_write

    def test_live_runtime_requires_explicit_model(self):
        old = os.environ.pop("OPENAI_MODEL", None)
        try:
            server = runtime.build_google_mcp_server()
            with self.assertRaisesRegex(RuntimeError, "OPENAI_MODEL_REQUIRED"):
                runtime.build_external_agent(server)
        finally:
            if old is not None:
                os.environ["OPENAI_MODEL"] = old


if __name__ == "__main__":
    unittest.main()
