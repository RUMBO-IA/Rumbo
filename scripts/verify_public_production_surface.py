from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "docs" / "brand" / "production_lock_v1.json"
TRUST_HTML_ROUTES = (
    ("/trust-center", "trust-center.html"),
    ("/processing-terms", "processing-terms.html"),
    ("/subprocessors", "subprocessors.html"),
    ("/retention", "retention.html"),
    ("/responsible-ai", "responsible-ai.html"),
    ("/security", "security.html"),
    ("/incident-response", "incident-response.html"),
    ("/continuity", "continuity.html"),
    ("/support-policy", "support-policy.html"),
    ("/status", "status.html"),
    ("/refund", "refund.html"),
    ("/support", "support.html"),
)
HTML_ROUTES = (
    ("/", "index.html"),
    ("/openai-support", "openai-support.html"),
    ("/openai-privacy", "openai-privacy.html"),
    ("/openai-terms", "openai-terms.html"),
    ("/privacy", "privacy.html"),
    ("/terms", "terms.html"),
    *TRUST_HTML_ROUTES,
)


class StylesheetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link":
            return
        values = {key.lower(): value for key, value in attrs if value is not None}
        rel = {token.lower() for token in values.get("rel", "").split()}
        href = values.get("href")
        if "stylesheet" in rel and href:
            self.hrefs.append(href)


def normalize_text(raw: bytes) -> bytes:
    text = raw.decode("utf-8")
    return text.replace("\r\n", "\n").encode("utf-8")


def normalize_html(raw: bytes) -> bytes:
    return normalize_text(raw)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_lock(path: pathlib.Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    for key in ("application_sha", "deployment_id", "domain", "status"):
        if not data.get(key):
            raise ValueError(f"production lock missing {key}")
    if data["status"] != "AUTHORIZED":
        raise ValueError("production lock is not AUTHORIZED")
    return data


def read_authorized_source(root: pathlib.Path, app_sha: str, source_path: str) -> bytes:
    proc = subprocess.run(
        ["git", "show", f"{app_sha}:{source_path}"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"authorized source read failed for {source_path}: {detail}")
    return proc.stdout


def fetch_url(url: str, timeout: float = 15.0) -> tuple[int, bytes]:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "RUMBO-Production-Surface-Watch/2"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            final_url = response.geturl()
            if final_url != url:
                raise RuntimeError(f"redirect detected: {url} -> {final_url}")
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def fetch_live(domain: str, timeout: float = 15.0) -> bytes:
    status, body = fetch_url(f"https://{domain}/", timeout=timeout)
    if status != 200:
        raise RuntimeError(f"live HTTP status is {status}, expected 200")
    return body


def compare_surface(source_raw: bytes, live_raw: bytes) -> dict:
    source = normalize_text(source_raw)
    live = normalize_text(live_raw)
    return {
        "source_bytes": len(source),
        "live_bytes": len(live),
        "source_sha256": sha256(source),
        "live_sha256": sha256(live),
        "match": source == live,
    }


def discover_same_origin_stylesheets(html_raw: bytes, page_url: str, domain: str) -> list[str]:
    parser = StylesheetParser()
    parser.feed(html_raw.decode("utf-8"))
    paths: set[str] = set()
    for href in parser.hrefs:
        absolute = urllib.parse.urljoin(page_url, href)
        parsed = urllib.parse.urlparse(absolute)
        if parsed.scheme not in ("http", "https") or parsed.netloc != domain:
            continue
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"
        paths.add(path)
    return sorted(paths)


def source_path_for_asset(asset_path: str) -> str:
    parsed = urllib.parse.urlparse(asset_path)
    return parsed.path.lstrip("/")


def verify_asset(
    *,
    domain: str,
    route: str,
    source_path: str,
    root: pathlib.Path,
    app_sha: str,
    timeout: float,
) -> tuple[dict, bytes | None]:
    url = urllib.parse.urljoin(f"https://{domain}/", route.lstrip("/"))
    check = {"route": route, "source_path": source_path, "url": url}
    try:
        source_raw = read_authorized_source(root, app_sha, source_path)
    except Exception as exc:
        check.update({"status": "SOURCE_MISSING", "error": str(exc)})
        return check, None

    status, live_raw = fetch_url(url, timeout=timeout)
    check["http_status"] = status
    if status != 200:
        check.update({"status": "HTTP_FAIL", "expected_http_status": 200})
        return check, None

    comparison = compare_surface(source_raw, live_raw)
    check.update(comparison)
    check["status"] = "PASS" if comparison["match"] else "DRIFT"
    return check, live_raw
def verify_surface(root: pathlib.Path, lock: dict, timeout: float) -> dict:
    domain = lock["domain"]
    app_sha = lock["application_sha"]
    checks: list[dict] = []
    stylesheet_routes: set[str] = set()

    for route, source_path in HTML_ROUTES:
        check, live_raw = verify_asset(
            domain=domain,
            route=route,
            source_path=source_path,
            root=root,
            app_sha=app_sha,
            timeout=timeout,
        )
        checks.append(check)
        if live_raw is None or check["status"] != "PASS":
            continue
        page_url = check["url"]
        stylesheet_routes.update(
            discover_same_origin_stylesheets(live_raw, page_url, domain)
        )

    for route in sorted(stylesheet_routes):
        source_path = source_path_for_asset(route)
        check, _ = verify_asset(
            domain=domain,
            route=route,
            source_path=source_path,
            root=root,
            app_sha=app_sha,
            timeout=timeout,
        )
        check["dependency_type"] = "stylesheet"
        checks.append(check)

    failures = [check for check in checks if check["status"] != "PASS"]
    return {
        "schema": "rumbo.brand.public-production-surface-verification/v2",
        "domain": domain,
        "application_sha": app_sha,
        "deployment_id": lock["deployment_id"],
        "checks": checks,
        "failure_count": len(failures),
        "status": "PASS" if not failures else "DRIFT",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", type=pathlib.Path, default=DEFAULT_LOCK)
    parser.add_argument("--repo-root", type=pathlib.Path, default=ROOT)
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args(argv)

    try:
        lock = load_lock(args.lock)
        result = verify_surface(args.repo_root, lock, args.timeout)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["status"] == "PASS" else 1
    except Exception as exc:
        print(json.dumps({
            "schema": "rumbo.brand.public-production-surface-verification/v2",
            "status": "NOT_VERIFIED",
            "error": str(exc),
        }, indent=2, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
