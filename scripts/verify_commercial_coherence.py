#!/usr/bin/env python3
from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
README = ROOT / "README.md"
PUBLIC_VARIANTS = (
    ROOT / "apps" / "landing-publica" / "index.html",
    ROOT / "apps" / "landing-publica" / "index-es.html",
)
TYPEFORM = "https://form.typeform.com/to/Tu3D3tVo"
TYPEFORM_PREFIX = "https://form.typeform.com/to/"
TYPEFORM_URL = re.compile(r"https://form\.typeform\.com/to/[A-Za-z0-9]+")
MONTHLY_PRICE = re.compile(
    r"(?:USD|\$)\s*\d+(?:[.,]\d+)?\s*/\s*(?:mes|month)\b",
    re.I,
)
RECURRING_PUBLIC_PRICE = re.compile(
    r"(?:USD|\$)\s*[0-9][0-9.,]*.{0,80}?"
    r"(?:/\s*(?:mes|month|mo)\b|(?:a|al|per)\s+(?:mes|month)\b)",
    re.I | re.S,
)
RECURRING_CATALOG = re.compile(r"\bmonthly\s*:\s*[0-9]", re.I)
RECURRING_SUBSCRIPTION = re.compile(
    r"\b(?:monthly subscription|suscripci[oó]n mensual)\b",
    re.I,
)

README_INVARIANTS = (
    "Revenue Recovery Sprint",
    "14 calendar days",
    "USD 149 one-time before kickoff",
    TYPEFORM,
)
INDEX_INVARIANTS = (
    "Revenue Recovery Sprint",
    "14 días",
    "USD 149",
    "pago único",
    "No garantiza ROI",
    "Control humano para acciones sensibles",
    "continuidad",
)


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


def check(readme: str, html: str) -> list[str]:
    errors: list[str] = []

    for value in README_INVARIANTS:
        if value not in readme:
            errors.append(f"README_MISSING:{value}")

    for value in INDEX_INVARIANTS:
        if value.casefold() not in html.casefold():
            errors.append(f"INDEX_MISSING:{value}")

    if MONTHLY_PRICE.search(html):
        errors.append("MONTHLY_PRICE")

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


def check_public_variant(path: Path, html: str) -> list[str]:
    errors: list[str] = []
    label = path.relative_to(ROOT).as_posix()
    folded = html.casefold()

    for value in ("Revenue Recovery Sprint", "USD 149"):
        if value.casefold() not in folded:
            errors.append(f"PUBLIC_VARIANT_MISSING:{label}:{value}")

    if "one-time" not in folded and "pago único" not in folded:
        errors.append(f"PUBLIC_VARIANT_ONE_TIME_MISSING:{label}")

    if RECURRING_PUBLIC_PRICE.search(html):
        errors.append(f"PUBLIC_VARIANT_RECURRING_PRICE:{label}")
    if RECURRING_CATALOG.search(html):
        errors.append(f"PUBLIC_VARIANT_RECURRING_CATALOG:{label}")
    if RECURRING_SUBSCRIPTION.search(html):
        errors.append(f"PUBLIC_VARIANT_RECURRING_SUBSCRIPTION:{label}")

    return sorted(set(errors))


def main() -> int:
    required = (README, INDEX, *PUBLIC_VARIANTS)
    if any(not path.is_file() for path in required):
        print("COMMERCIAL_COHERENCE_FAIL: REQUIRED_PUBLIC_SURFACE_MISSING")
        return 1

    errors = check(
        README.read_text(encoding="utf-8"),
        INDEX.read_text(encoding="utf-8"),
    )
    for path in PUBLIC_VARIANTS:
        errors.extend(check_public_variant(path, path.read_text(encoding="utf-8")))
    errors = sorted(set(errors))
    if errors:
        print(f"COMMERCIAL_COHERENCE_FAIL: {len(errors)} violation(s)")
        for error in errors:
            print(f"VIOLATION={error}")
        return 1

    print("COMMERCIAL_COHERENCE_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
