"""External Agents SDK runtime wired to the local Google Workspace MCP server.

This file does not provision credentials. Live execution requires:
- OPENAI_API_KEY
- OPENAI_MODEL
- GOOGLE_OAUTH_ACCESS_TOKEN
- RUMBO_ALLOW_WRITES=1 only when writes are intentionally enabled
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path
import sys

from agents import Agent, Runner
from agents.mcp import MCPServerStdio

from daily_ops import INSTRUCTIONS

HERE = Path(__file__).resolve().parent
SERVER_SCRIPT = HERE / "google_workspace_mcp.py"

READ_TOOLS = {"gmail_search", "gmail_read", "calendar_events"}
WRITE_TOOLS = {"gmail_create_draft", "calendar_create_event"}


def build_google_mcp_server() -> MCPServerStdio:
    child_env = os.environ.copy()
    return MCPServerStdio(
        params={
            "command": sys.executable,
            "args": [str(SERVER_SCRIPT)],
            "env": child_env,
            "cwd": str(HERE),
        },
        name="RUMBO Google Workspace",
        cache_tools_list=True,
        max_retry_attempts=0,
        require_approval={
            "always": {"tool_names": sorted(WRITE_TOOLS)},
            "never": {"tool_names": sorted(READ_TOOLS)},
        },
    )


def build_external_agent(server: MCPServerStdio) -> Agent:
    model = os.environ.get("OPENAI_MODEL", "").strip()
    if not model:
        raise RuntimeError("OPENAI_MODEL_REQUIRED")
    return Agent(
        name="RUMBO Daily Ops External",
        instructions=INSTRUCTIONS,
        model=model,
        mcp_servers=[server],
    )


async def discover_tools() -> list[str]:
    server = build_google_mcp_server()
    await server.connect()
    try:
        tools = await server.list_tools()
        return sorted(tool.name for tool in tools)
    finally:
        await server.cleanup()


async def run_live(prompt: str) -> str:
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY_REQUIRED")
    if not os.environ.get("GOOGLE_OAUTH_ACCESS_TOKEN"):
        raise RuntimeError("GOOGLE_OAUTH_ACCESS_TOKEN_REQUIRED")

    server = build_google_mcp_server()
    await server.connect()
    try:
        agent = build_external_agent(server)
        result = await Runner.run(agent, prompt)
        return str(result.final_output)
    finally:
        await server.cleanup()


if __name__ == "__main__":
    print(asyncio.run(discover_tools()))
