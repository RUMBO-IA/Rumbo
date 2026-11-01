# RUMBO public landing — provider-portable static recovery

Source: publicly served content on https://rumbo.verso.fans, captured 2026-11-01 into a protected Vercel preview. This folder includes public HTML for the home page and the seven support/legal pages, plus styles.css.

This is a static recovery copy; not a backup of dynamic apps, databases, private APIs, secrets, live traffic, or application workflows. The external CookieYes script was deliberately omitted from the preview. No production authority is implied. No payment or production domain change was executed.

This branch is isolated from protected main. Do not merge or repoint the public domain without a separate production authorization and platform-compliance review. Owner authorization and deployment lineage: RUMBO-IA/Rumbo#72 and docs/brand/production_lock_v1.json.

To use the flat-file recovery on generic static hosting, serve index.html at /, styles.css at /styles.css and map each route in _redirects to the same-named .html file. Vercel uses vercel.json rewrites. Netlify supports _redirects / _headers. The noindex controls are intentional for an unpublished fallback and must be reviewed before public cutover.

Verified protected preview deployment: dpl_H1LHQH5JkmqKv5x11xiriGyVyc5B.
