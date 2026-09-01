from pathlib import Path

root = Path(__file__).resolve().parents[1]
html = (root / "index.html").read_text(encoding="utf-8")

TYPEFORM = "https://form.typeform.com/to/Tu3D3tVo"

assert TYPEFORM in html, "canonical Typeform front door missing"
assert "14 días" in html, "canonical pilot duration missing"
assert "USD 149" in html, "canonical pilot price missing"
assert "pago único" in html, "canonical one-time payment wording missing"
assert "/mes" not in html, "stale monthly pricing remains"
assert "mailto:sebastian@rumbo.verso.fans?subject=Quiero%20una%20demo" not in html, "stale mailto primary CTA remains"
assert "No garantiza ROI" in html, "ROI disclaimer missing"
assert "continuidad" in html.lower(), "continuity boundary missing"

print("COMMERCIAL_COHERENCE_PASS")
