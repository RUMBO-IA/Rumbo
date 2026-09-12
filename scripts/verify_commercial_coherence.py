#!/usr/bin/env python3
from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
PUBLIC_HTML = (INDEX, ROOT / "apps/landing-publica/index.html", ROOT / "apps/landing-publica/index-es.html")
README = ROOT / "README.md"
TYPEFORM = "https://form.typeform.com/to/Tu3D3tVo"
TYPEFORM_PREFIX = "https://form.typeform.com/to/"
TYPEFORM_URL = re.compile(r"https://form\.typeform\.com/to/[A-Za-z0-9]+")
MONTHLY_PRICE = re.compile(r"(?:USD|\$)\s*\d+(?:[.,]\d+)?\s*(?:/\s*(?:mes|month|mo)|a\s+month|al\s+mes)\b", re.I)
LEGACY_COMMERCIAL_MARKERS = ("RUMBO Capture", "RUMBO Recovery", "RUMBO Front Desk AI", "RUMBO Growth Engine", "Plan Growth completo")
TOOL_COUNT = re.compile(r"\b(?:(?:more than|más de)\s+)?\d+(?:\s+\w+){0,2}\s+(?:tools|herramientas)\b", re.I)
FAKE_FORM_SUCCESS = re.compile(r"\b(?:mensaje enviado|message sent)\b", re.I)
GENERIC_SOCIAL_DESTINATION = re.compile(r'href=["\']https://www\.(?:linkedin|instagram)\.com/?["\']', re.I)
TYPEFORM_ANCHOR = re.compile(r'<a\b[^>]*href=["\']' + re.escape(TYPEFORM) + r'["\'][^>]*>.*?</a>', re.I | re.S)
DUPLICATE_FOOTER_LINK = re.compile(r'(?:<li>\s*<a href=["\']' + re.escape(TYPEFORM) + r'["\'][^>]*>[^<]+</a>\s*</li>\s*){2,}', re.I)

README_INVARIANTS = (
    "Revenue Recovery Sprint", "14 calendar days", "USD 149 one-time before kickoff", TYPEFORM,
)
ES_SURFACE_INVARIANTS = (
    "Revenue Recovery Sprint", "14 días", "USD 149", "pago único", "No garantiza ROI",
)
EN_SURFACE_INVARIANTS = (
    "Revenue Recovery Sprint", "14 days", "USD 149", "one-time", "No ROI",
)
INDEX_INVARIANTS = ES_SURFACE_INVARIANTS

class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[str] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        element_id = values.get("id")
        if element_id:
            self.ids.add(element_id)
        if tag.lower() == "a":
            href = values.get("href", "").strip()
            if href:
                self.hrefs.append(href)


def check(readme: str, html: str, invariants=INDEX_INVARIANTS) -> list[str]:
    errors: list[str] = []
    plain_html = re.sub(r"<[^>]+>", " ", html)
    plain_html = re.sub(r"\s+", " ", plain_html)
    for value in README_INVARIANTS:
        if value not in readme:
            errors.append(f"README_MISSING:{value}")
    for value in invariants:
        if value.casefold() not in plain_html.casefold():
            errors.append(f"INDEX_MISSING:{value}")
    if MONTHLY_PRICE.search(plain_html):
        errors.append("MONTHLY_PRICE")
    if "@rumbo_ia" in html.casefold():
        errors.append("STALE_SOCIAL_HANDLE")
    if any(marker.casefold() in html.casefold() for marker in LEGACY_COMMERCIAL_MARKERS):
        errors.append("LEGACY_COMMERCIAL_CATALOG")
    if TOOL_COUNT.search(plain_html):
        errors.append("UNVERIFIED_TOOL_COUNT")
    if FAKE_FORM_SUCCESS.search(plain_html):
        errors.append("FAKE_FORM_SUCCESS")
    if GENERIC_SOCIAL_DESTINATION.search(html):
        errors.append("GENERIC_SOCIAL_DESTINATION")
    for anchor in TYPEFORM_ANCHOR.findall(html):
        if re.search(r"\b(?:whatsapp|email|correo)\b", anchor, re.I) or "#25D366" in anchor or re.search(r">\s*wa\s*<", anchor, re.I):
            errors.append("MISLABELED_TYPEFORM_ROUTE")
            break
    if DUPLICATE_FOOTER_LINK.search(html):
        errors.append("DUPLICATE_FOOTER_LINK")
    if "mailto:" in readme.casefold() or "mailto:" in html.casefold():
        errors.append("PUBLIC_MAILTO")

    typeform_urls = TYPEFORM_URL.findall(readme + "\n" + html)
    if TYPEFORM not in typeform_urls:
        errors.append("CANONICAL_TYPEFORM_MISSING")
    if any(url != TYPEFORM for url in typeform_urls):
        errors.append("NONCANONICAL_TYPEFORM")

    parser = AnchorParser()
    parser.feed(html)
    if "contacto" not in parser.ids:
        errors.append("CONTACT_SECTION_MISSING")
    if "#contacto" not in parser.hrefs:
        errors.append("CONTACT_CTA_MISSING")
    typeform_links = [href for href in parser.hrefs if href.startswith(TYPEFORM_PREFIX)]
    if TYPEFORM not in typeform_links:
        errors.append("CANONICAL_TYPEFORM_ANCHOR_MISSING")
    if any(href != TYPEFORM for href in typeform_links):
        errors.append("NONCANONICAL_TYPEFORM_ANCHOR")
    return sorted(set(errors))


def check_surfaces(readme: str, surfaces: dict[str, tuple[str, tuple[str, ...]]]) -> list[str]:
    errors: list[str] = []
    for name, (html, invariants) in surfaces.items():
        errors.extend(f"{name}:{error}" for error in check(readme, html, invariants))
    return sorted(set(errors))


def main() -> int:
    if not README.is_file() or any(not path.is_file() for path in PUBLIC_HTML):
        print("COMMERCIAL_COHERENCE_FAIL: REQUIRED_PUBLIC_SURFACE_MISSING")
        return 1
    readme = README.read_text(encoding="utf-8")
    surfaces = {
        str(INDEX.relative_to(ROOT)): (INDEX.read_text(encoding="utf-8"), ES_SURFACE_INVARIANTS),
        "apps/landing-publica/index.html": ((ROOT / "apps/landing-publica/index.html").read_text(encoding="utf-8"), EN_SURFACE_INVARIANTS),
        "apps/landing-publica/index-es.html": ((ROOT / "apps/landing-publica/index-es.html").read_text(encoding="utf-8"), ES_SURFACE_INVARIANTS),
    }
    errors = check_surfaces(readme, surfaces)
    if errors:
        print(f"COMMERCIAL_COHERENCE_FAIL: {len(errors)} violation(s)")
        for error in errors:
            print(f"VIOLATION={error}")
        return 1
    print("COMMERCIAL_COHERENCE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())