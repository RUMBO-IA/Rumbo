import base64, hashlib, json, re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
config = json.loads((root / "vercel.json").read_text(encoding="utf-8"))
html = (root / "index.html").read_text(encoding="utf-8")
headers = {h["key"]: h["value"] for h in config["headers"][0]["headers"]}

scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.S)
assert len(scripts) == 1, f"expected one inline script, got {len(scripts)}"
script_hash = base64.b64encode(hashlib.sha256(scripts[0].encode()).digest()).decode()
csp = headers.get("Content-Security-Policy", "")

assert f"'sha256-{script_hash}'" in csp
assert "script-src 'self'" in csp and "'unsafe-inline'" not in csp.split("style-src")[0]
assert "script-src-attr 'none'" in csp

COOKIEYES_SCRIPT = "https://cdn-cookieyes.com/client_data/7b543bb9f5d3733c1f7e966ca7392b40/script.js"
assert COOKIEYES_SCRIPT in html
assert "https://cdn-cookieyes.com" in csp
assert "https://*.cookieyes.com" in csp
for directive in ["object-src 'none'", "frame-ancestors 'none'", "frame-src 'none'", "base-uri 'none'", "form-action 'self'", "connect-src 'self'", "upgrade-insecure-requests"]:
    assert directive in csp, directive
assert headers["X-Content-Type-Options"] == "nosniff"
assert headers["X-Frame-Options"] == "DENY"
assert headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"
assert headers["Cross-Origin-Resource-Policy"] == "same-site"
assert headers["Strict-Transport-Security"] == "max-age=31536000"
print("SECURITY_HEADERS_PASS", script_hash)
