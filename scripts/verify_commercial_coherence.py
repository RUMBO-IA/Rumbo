#!/usr/bin/env python3
from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
README = ROOT / "README.md"
TYPEFORM = "https://form.typeform.com/to/Tu3D3tVo"
TYPEFORM_PREFIX = "https://form.typeform.com/to/"
TYPEFORM_URL = re.compile(r"https://form\.typeform\.com/to/[A-Za-z0-9]+")
MONTHLY_PRICE = re.compile(
    r"(?:USD|\$)\s*\d+(?:[.,]\d+)?\s*/\s*(?:mes|month)\b",
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


def check_commercial_entrypoints(index_html: str, login_html: str, terms_html: str, refund_html: str, portal_js: str) -> list[str]:
    errors: list[str] = []
    folded = (index_html + "\n" + login_html + "\n" + terms_html).casefold()
    if 'href="/refund"' not in folded and 'href="refund.html"' not in folded:
        errors.append("REFUND_LINK_MISSING")
    if "refund policy" not in refund_html.casefold():
        errors.append("REFUND_POLICY_MISSING")
    if 'id="google-button"' in login_html.casefold() or "continue with google" in login_html.casefold():
        errors.append("UNVERIFIED_GOOGLE_LOGIN_VISIBLE")
    if "subscriptions?select=plan_id,status,current_period_start,current_period_end" not in portal_js:
        errors.append("SUBSCRIPTION_PLAN_QUERY_MISSING")
    if "workspace.plan_id" in portal_js or "select=id,name,slug,plan_id" in portal_js:
        errors.append("WORKSPACE_PLAN_USED_AS_ENTITLEMENT")
    if "No active subscription" not in portal_js:
        errors.append("NO_SUBSCRIPTION_STATE_MISSING")
    return sorted(set(errors))
def main() -> int:
    if not README.is_file() or not INDEX.is_file():
        print("COMMERCIAL_COHERENCE_FAIL: REQUIRED_PUBLIC_SURFACE_MISSING")
        return 1

    index_html = INDEX.read_text(encoding="utf-8")
    errors = check(
        README.read_text(encoding="utf-8"),
        index_html,
    )
    required = {
        "login": ROOT / "login.html",
        "terms": ROOT / "terms.html",
        "refund": ROOT / "refund.html",
        "portal": ROOT / "portal.js",
    }
    if not all(path.is_file() for path in required.values()):
        errors.append("COMMERCIAL_ENTRYPOINT_MISSING")
    else:
        errors.extend(check_commercial_entrypoints(
            index_html,
            required["login"].read_text(encoding="utf-8"),
            required["terms"].read_text(encoding="utf-8"),
            required["refund"].read_text(encoding="utf-8"),
            required["portal"].read_text(encoding="utf-8"),
        ))
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
