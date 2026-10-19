"""Local Google Workspace MCP server for RUMBO Daily Ops.

No credentials are embedded. The server requires an app-owned OAuth access
token in GOOGLE_OAUTH_ACCESS_TOKEN. Writes are disabled unless
RUMBO_ALLOW_WRITES=1. Provider writes use deterministic identities and readback;
they are never blindly retried after an ambiguous result.
"""
from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
from email.message import EmailMessage
from hashlib import sha256
import os
from typing import Any
from urllib.parse import quote

import requests
from mcp.server.mcpserver import MCPServer

GMAIL = "https://gmail.googleapis.com/gmail/v1/users/me"
CALENDAR = "https://www.googleapis.com/calendar/v3"
TIMEOUT_SECONDS = 15
server = MCPServer(
    name="rumbo-google-workspace",
    description="Gmail and Google Calendar tools for RUMBO Daily Ops",
)


def _token() -> str:
    token = os.environ.get("GOOGLE_OAUTH_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("GOOGLE_OAUTH_ACCESS_TOKEN_REQUIRED")
    return token


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {_token()}", "Content-Type": "application/json"}


def _request(method: str, url: str, **kwargs: Any) -> requests.Response:
    return requests.request(method, url, headers=_headers(), timeout=TIMEOUT_SECONDS, **kwargs)


def _json_or_error(response: requests.Response) -> dict[str, Any]:
    if response.status_code >= 400:
        raise RuntimeError(f"PROVIDER_HTTP_{response.status_code}:{response.text[:300]}")
    return response.json()


def _test_mode() -> bool:
    return os.environ.get("RUMBO_MCP_TEST_MODE") == "1"


def _writes_enabled() -> None:
    if _test_mode():
        raise PermissionError("WRITES_DISABLED_IN_TEST_MODE")
    if os.environ.get("RUMBO_ALLOW_WRITES") != "1":
        raise PermissionError("RUMBO_ALLOW_WRITES_NOT_ENABLED")


def _header(headers: list[dict[str, str]], name: str) -> str:
    target = name.lower()
    for item in headers:
        if item.get("name", "").lower() == target:
            return item.get("value", "")
    return ""


def _decode_body(payload: dict[str, Any]) -> str:
    def walk(part: dict[str, Any]) -> list[str]:
        mime = part.get("mimeType", "")
        body = part.get("body", {})
        data = body.get("data")
        if data and mime.startswith("text/plain"):
            padded = data + "=" * (-len(data) % 4)
            return [urlsafe_b64decode(padded).decode("utf-8", errors="replace")]
        out: list[str] = []
        for child in part.get("parts", []) or []:
            out.extend(walk(child))
        return out

    chunks = walk(payload)
    return "\n".join(chunks).strip()


@server.tool(name="gmail_search", description="Search Gmail and return summarized messages. Read-only.")
def gmail_search(query: str, max_results: int = 10) -> list[dict[str, Any]]:
    if _test_mode():
        return [{
            "id": "fixture-message",
            "thread_id": "fixture-thread",
            "from": "fixture-sender",
            "to": "fixture-self",
            "subject": "Fixture operational message",
            "date": "2026-10-02",
            "snippet": "Fixture body preview",
            "labels": ["INBOX"],
        }][:max_results]
    response = _request("GET", f"{GMAIL}/messages", params={"q": query, "maxResults": max_results})
    listing = _json_or_error(response)
    out: list[dict[str, Any]] = []
    for item in listing.get("messages", []) or []:
        message_id = item["id"]
        details = _json_or_error(_request(
            "GET",
            f"{GMAIL}/messages/{message_id}",
            params={"format": "metadata", "metadataHeaders": ["From", "To", "Subject", "Date"]},
        ))
        headers = details.get("payload", {}).get("headers", [])
        out.append({
            "id": message_id,
            "thread_id": details.get("threadId"),
            "from": _header(headers, "From"),
            "to": _header(headers, "To"),
            "subject": _header(headers, "Subject"),
            "date": _header(headers, "Date"),
            "snippet": details.get("snippet", ""),
            "labels": details.get("labelIds", []),
        })
    return out


@server.tool(name="gmail_read", description="Read one Gmail message. Read-only.")
def gmail_read(message_id: str) -> dict[str, Any]:
    if _test_mode():
        return {
            "id": message_id,
            "thread_id": "fixture-thread",
            "from": "fixture-sender",
            "to": "fixture-self",
            "subject": "Fixture operational message",
            "date": "2026-10-02",
            "body": "Fixture body content.",
            "snippet": "Fixture body preview",
            "labels": ["INBOX"],
        }
    details = _json_or_error(_request("GET", f"{GMAIL}/messages/{message_id}", params={"format": "full"}))
    payload = details.get("payload", {})
    headers = payload.get("headers", [])
    return {
        "id": message_id,
        "thread_id": details.get("threadId"),
        "from": _header(headers, "From"),
        "to": _header(headers, "To"),
        "subject": _header(headers, "Subject"),
        "date": _header(headers, "Date"),
        "body": _decode_body(payload),
        "snippet": details.get("snippet", ""),
        "labels": details.get("labelIds", []),
    }


@server.tool(name="calendar_events", description="Read Google Calendar events in an exact RFC3339 window. Read-only.")
def calendar_events(time_min: str, time_max: str, calendar_id: str = "primary", max_results: int = 50) -> list[dict[str, Any]]:
    if _test_mode():
        return [{
            "id": "fixture-event",
            "summary": "Fixture event",
            "status": "confirmed",
            "start": {"dateTime": time_min},
            "end": {"dateTime": time_max},
            "attendees": [],
        }][:max_results]
    response = _request(
        "GET",
        f"{CALENDAR}/calendars/{quote(calendar_id, safe='')}/events",
        params={
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": max_results,
        },
    )
    data = _json_or_error(response)
    return [{
        "id": item.get("id"),
        "summary": item.get("summary"),
        "status": item.get("status"),
        "start": item.get("start"),
        "end": item.get("end"),
        "attendees": item.get("attendees", []),
    } for item in data.get("items", []) or []]


def _draft_message_id(idempotency_key: str) -> str:
    digest = sha256(idempotency_key.encode("utf-8")).hexdigest()[:32]
    return f"<rumbo-{digest}@id.invalid>"


def _find_draft_by_message_id(message_id_header: str) -> dict[str, Any] | None:
    query = f'in:drafts rfc822msgid:{message_id_header}'
    listing = _json_or_error(_request("GET", f"{GMAIL}/messages", params={"q": query, "maxResults": 5}))
    messages = listing.get("messages", []) or []
    if not messages:
        return None
    message_id = messages[0]["id"]
    details = _json_or_error(_request("GET", f"{GMAIL}/messages/{message_id}", params={"format": "metadata"}))
    return {
        "message_id": message_id,
        "thread_id": details.get("threadId"),
        "labels": details.get("labelIds", []),
    }


@server.tool(name="gmail_create_draft", description="Create a Gmail draft. Write tool; caller must require approval.")
def gmail_create_draft(to: str, subject: str, body: str, idempotency_key: str) -> dict[str, Any]:
    _writes_enabled()
    message_id_header = _draft_message_id(idempotency_key)
    existing = _find_draft_by_message_id(message_id_header)
    if existing:
        return {
            "tool_success": True,
            "effect_verified": True,
            "recovered_existing": True,
            **existing,
        }

    message = EmailMessage()
    message["To"] = to
    message["Subject"] = subject
    message["Message-ID"] = message_id_header
    message.set_content(body)
    raw = urlsafe_b64encode(message.as_bytes()).decode("ascii").rstrip("=")

    tool_success = True
    response_data: dict[str, Any] | None = None
    try:
        response_data = _json_or_error(_request(
            "POST",
            f"{GMAIL}/drafts",
            json={"message": {"raw": raw}},
        ))
    except (requests.Timeout, requests.ConnectionError):
        tool_success = False

    if response_data:
        draft_id = response_data.get("id")
        if draft_id:
            verified = _json_or_error(_request("GET", f"{GMAIL}/drafts/{draft_id}", params={"format": "metadata"}))
            return {
                "tool_success": tool_success,
                "effect_verified": True,
                "recovered_existing": False,
                "draft_id": verified.get("id"),
                "message_id": verified.get("message", {}).get("id"),
                "thread_id": verified.get("message", {}).get("threadId"),
                "labels": verified.get("message", {}).get("labelIds", []),
            }

    recovered = _find_draft_by_message_id(message_id_header)
    return {
        "tool_success": tool_success,
        "effect_verified": recovered is not None,
        "recovered_existing": recovered is not None,
        **(recovered or {}),
    }


def _calendar_event_id(idempotency_key: str) -> str:
    return "rumbo" + sha256(idempotency_key.encode("utf-8")).hexdigest()[:32]


def _calendar_event_get(calendar_id: str, event_id: str) -> dict[str, Any] | None:
    response = _request(
        "GET",
        f"{CALENDAR}/calendars/{quote(calendar_id, safe='')}/events/{quote(event_id, safe='')}",
    )
    if response.status_code == 404:
        return None
    return _json_or_error(response)


@server.tool(name="calendar_create_event", description="Create a Google Calendar event. Write tool; caller must require approval.")
def calendar_create_event(
    title: str,
    start_time: str,
    end_time: str,
    attendees: list[str],
    idempotency_key: str,
    calendar_id: str = "primary",
) -> dict[str, Any]:
    _writes_enabled()
    event_id = _calendar_event_id(idempotency_key)
    existing = _calendar_event_get(calendar_id, event_id)
    if existing:
        return {
            "tool_success": True,
            "effect_verified": True,
            "recovered_existing": True,
            "event_id": existing.get("id"),
            "status": existing.get("status"),
        }

    body = {
        "id": event_id,
        "summary": title,
        "start": {"dateTime": start_time},
        "end": {"dateTime": end_time},
        "attendees": [{"email": value} for value in attendees],
    }

    tool_success = True
    try:
        response = _request(
            "POST",
            f"{CALENDAR}/calendars/{quote(calendar_id, safe='')}/events",
            json=body,
        )
        if response.status_code == 409:
            tool_success = False
        else:
            _json_or_error(response)
    except (requests.Timeout, requests.ConnectionError):
        tool_success = False

    verified = _calendar_event_get(calendar_id, event_id)
    return {
        "tool_success": tool_success,
        "effect_verified": verified is not None,
        "recovered_existing": (not tool_success) and verified is not None,
        "event_id": verified.get("id") if verified else None,
        "status": verified.get("status") if verified else None,
    }


def main() -> None:
    transport = os.environ.get("RUMBO_MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        host = os.environ.get("RUMBO_MCP_HOST", "127.0.0.1")
        port = int(os.environ.get("RUMBO_MCP_PORT", "8787"))
        server.run(transport="streamable-http", host=host, port=port, streamable_http_path="/mcp")
        return
    if transport != "stdio":
        raise RuntimeError("RUMBO_MCP_TRANSPORT must be stdio or streamable-http")
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
