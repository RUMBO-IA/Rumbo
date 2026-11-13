import base64, hashlib, json
from html.parser import HTMLParser
from pathlib import Path

root = Path(__file__).resolve().parents[1]
config = json.loads((root / "vercel.json").read_text(encoding="utf-8"))
html = (root / "index.html").read_text(encoding="utf-8")
headers = {h["key"]: h["value"] for h in config["headers"][0]["headers"]}
redirects = {(r.get("source"), r.get("destination"), r.get("permanent")) for r in config.get("redirects", [])}
required_redirects = {
    ("/apps/landing-publica", "/", True),
    ("/apps/landing-publica/index.html", "/", True),
}
assert required_redirects <= redirects, f"missing legacy landing redirects: {sorted(required_redirects - redirects)}"
assert config.get("git", {}).get("deploymentEnabled", {}).get("main") is False


class InlineScripts(HTMLParser):
    """Collects the raw body of attribute-less <script> elements (the ones the CSP hash must cover)."""

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.scripts = []
        self._buffer = None

    def handle_starttag(self, tag, attrs):
        if tag == "script" and not attrs:
            self._buffer = []

    def handle_endtag(self, tag):
        if tag == "script" and self._buffer is not None:
            self.scripts.append("".join(self._buffer))
            self._buffer = None

    def handle_data(self, data):
        if self._buffer is not None:
            self._buffer.append(data)


parser = InlineScripts()
parser.feed(html)
parser.close()
scripts = parser.scripts
assert len(scripts) == 1, f"expected one inline script, got {len(scripts)}"
script_hash = base64.b64encode(hashlib.sha256(scripts[0].encode()).digest()).decode()
csp = headers.get("Content-Security-Policy", "")
csp_directives = {}
for part in csp.split(";"):
    tokens = part.split()
    if tokens:
        csp_directives[tokens[0]] = set(tokens[1:])
csp_sources = set().union(*csp_directives.values()) if csp_directives else set()

assert f"'sha256-{script_hash}'" in csp_directives.get("script-src", set())
assert "script-src 'self'" in csp and "'unsafe-inline'" not in csp.split("style-src")[0]
assert "script-src-attr 'none'" in csp

COOKIEYES_SCRIPT = "https://cdn-cookieyes.com/client_data/7b543bb9f5d3733c1f7e966ca7392b40/script.js"
assert COOKIEYES_SCRIPT in html
assert "https://cdn-cookieyes.com" in csp_sources
assert "https://*.cookieyes.com" in csp_sources
for directive in ["object-src 'none'", "frame-ancestors 'none'", "frame-src 'none'", "base-uri 'none'", "form-action 'self'", "connect-src 'self'", "upgrade-insecure-requests"]:
    assert directive in csp, directive
assert headers["X-Content-Type-Options"] == "nosniff"
assert headers["X-Frame-Options"] == "DENY"
assert headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"
assert headers["Cross-Origin-Resource-Policy"] == "same-site"
assert headers["Strict-Transport-Security"] == "max-age=31536000"
print("SECURITY_HEADERS_PASS", script_hash)
